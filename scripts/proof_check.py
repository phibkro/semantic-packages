#!/usr/bin/env python3
"""Check ADR 0009's bounded, specification-only ``pop-empty`` Lean proof.

The checker is deliberately a closed acceptance boundary, not a general proof
framework.  It validates the pinned manifest and canonical records, invokes the
exact Lean toolchain with bounded process-group cleanup, and requires structured
observations of both the theorem's exact type and its empty axiom dependency set.
All failures are stable stdout diagnostics; stderr and Python tracebacks are never
part of the interface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import signal
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import record_check


SUCCESS = "Proof is valid: 0 diagnostics."
PROCESS_TIMEOUT_SECONDS = 1.0

FORMAT_VERSION = 1
SPECIFICATION_REFERENCE = {
    "kind": "specification",
    "id": "stack",
    "version": "0.1.0",
}
CLAIM_REFERENCE = {
    "kind": "claim",
    "id": "stack-pop-empty-law",
    "version": "0.1.0",
}
DECLARATION_ID = "pop-empty"
THEOREM_NAME = "stack_pop_empty"
EXPECTED_STATEMENT = (
    "∀ (A : Type u), pop (empty : ObservedStack A) = Option.none"
)
EXPECTED_AXIOMS: list[str] = []
LEAN_NAME = "Lean"
LEAN_VERSION = "4.30.0"
LEAN_COMMIT = "d024af099ca4bf2c86f649261ebf59565dc8c622"
LEAN_INVOCATION = ["$LEAN", "--trust=0", "--json", "$GENERATED_SOURCE"]

SPECIFICATION_PATH = "fixtures/records/valid/stack-spec.json"
CLAIM_PATH = "fixtures/records/valid/pop-empty-spec-claim.json"
SOURCE_PATH = "proofs/stack-pop-empty/StackPopEmpty.lean"
RUNNER_PATH = "scripts/proof_check.py"

EVIDENCE_IDENTITY = {
    "kind": "evidence",
    "id": "stack-pop-empty-model-proof",
    "version": "0.1.0",
}
EVIDENCE_METHOD = "Lean model-satisfaction and proof-pipeline check for Stack pop-empty"
EVIDENCE_ENVIRONMENT = {"execution": "local", "kernel": "Lean 4.30.0"}
EVIDENCE_ASSUMPTIONS = [
    "The hand-reviewed translation from the Stack law to the Lean observation model is faithful.",
    "Finite Lean lists faithfully model the Specification's finite top-first Stack observation space.",
    "Lean 4.30.0 and its trusted kernel correctly check the generated proof audit.",
]
EVIDENCE_EXCLUSIONS = [
    "This Evidence does not establish conformance of any Realization or adapter.",
    "This Evidence does not prove every Stack law or the complete Specification.",
    "This Evidence grants no global authority to Lean or to this proof pipeline.",
]
SUCCESS_SHA256 = hashlib.sha256(f"{SUCCESS}\n".encode("utf-8")).hexdigest()

_STRING = ("string",)
_INT = ("int",)
_STRING_LIST = ("string_list",)


def _object(**fields: tuple[Any, ...]) -> tuple[str, dict[str, tuple[Any, ...]]]:
    return ("object", fields)


_REFERENCE_SCHEMA = _object(kind=_STRING, id=_STRING, version=_STRING)
_INPUT_SCHEMA = _object(reference=_REFERENCE_SCHEMA, path=_STRING, sha256=_STRING)
_FILE_SCHEMA = _object(path=_STRING, sha256=_STRING)
_TOOL_SCHEMA = _object(
    name=_STRING, version=_STRING, commit=_STRING, invocation=_STRING_LIST
)
MANIFEST_SCHEMA = _object(
    formatVersion=_INT,
    specification=_INPUT_SCHEMA,
    declarationId=_STRING,
    claim=_INPUT_SCHEMA,
    source=_FILE_SCHEMA,
    runner=_FILE_SCHEMA,
    tool=_TOOL_SCHEMA,
    theoremName=_STRING,
    expectedStatement=_STRING,
    expectedAxioms=_STRING_LIST,
)

_VERSION_OUTPUT = re.compile(
    r"\ALean \(version ([^,\n]+), [^,\n]+, commit ([0-9a-f]{40}), [^)\n]+\)\n?\Z"
)
_NO_AXIOMS = re.compile(r"^'([^']+)' does not depend on any axioms$")
_HAS_AXIOMS = re.compile(r"^'([^']+)' depends on axioms: \[(.*)\]$")
_DECLARATION = re.compile(
    r"(?m)^\s*(?:universe|variable|def|theorem|abbrev|axiom|instance|"
    r"structure|inductive|class|example)\b"
)
_LEADING_WARNING_OPTION = re.compile(
    r"\A[ \t\r\n]*set_option[ \t]+warningAsError[ \t]+true[ \t]*(?:\r?\n|\Z)"
)
_SOURCE_AXIOM = re.compile(r"\baxiom\b")
_SOURCE_UNSAFE = re.compile(r"\bunsafe\b")
_SOURCE_EXECUTING_COMMAND = re.compile(r"(?m)^\s*#\s*(?:eval|print)\b")

_LEAN_MESSAGE_KEYS = {
    "caption",
    "data",
    "endPos",
    "fileName",
    "isSilent",
    "keepFullRange",
    "kind",
    "pos",
    "severity",
}
_POSITION_KEYS = {"column", "line"}


class Diagnostic(Exception):
    def __init__(self, code: str, source: str, pointer: str = "", detail: str = ""):
        self.code = code
        self.source = source
        self.pointer = pointer
        self.detail = " ".join(detail.split())

    def signature(self) -> str:
        head = f"{self.code} {self.source}#{self.pointer}"
        return f"{head}: {self.detail}" if self.detail else head

    def key(self) -> str:
        return f"{self.code} {self.source}#{self.pointer}"


class _ArgumentError(Exception):
    pass


class _QuietParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _ArgumentError(message)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_shape(
    data: Any, schema: tuple[Any, ...], pointer: str, manifest_arg: str
) -> list[Diagnostic]:
    kind = schema[0]
    if kind == "object":
        fields: dict[str, tuple[Any, ...]] = schema[1]
        if not isinstance(data, dict):
            return [
                Diagnostic(
                    "PROOF_MANIFEST_SHAPE",
                    manifest_arg,
                    pointer,
                    "expected a JSON object",
                )
            ]
        violations: list[Diagnostic] = []
        for key in sorted(set(fields) | set(data)):
            child = f"{pointer}/{key}"
            if key not in fields:
                violations.append(
                    Diagnostic(
                        "PROOF_MANIFEST_SHAPE", manifest_arg, child, "unexpected field"
                    )
                )
            elif key not in data:
                violations.append(
                    Diagnostic(
                        "PROOF_MANIFEST_SHAPE",
                        manifest_arg,
                        child,
                        "missing required field",
                    )
                )
            else:
                violations.extend(
                    _validate_shape(data[key], fields[key], child, manifest_arg)
                )
        return violations
    if kind == "string":
        valid = isinstance(data, str)
    elif kind == "int":
        valid = isinstance(data, int) and not isinstance(data, bool)
    elif kind == "string_list":
        valid = isinstance(data, list) and all(isinstance(item, str) for item in data)
    else:
        raise AssertionError(f"unknown manifest schema kind {kind!r}")
    if valid:
        return []
    expected = {
        "string": "a string",
        "int": "an integer",
        "string_list": "a list of strings",
    }[kind]
    return [
        Diagnostic("PROOF_MANIFEST_SHAPE", manifest_arg, pointer, f"expected {expected}")
    ]


def _canonical_relative(raw: str) -> bool:
    if not raw or "\\" in raw or PurePosixPath(raw).is_absolute():
        return False
    return posixpath.normpath(raw) == raw and raw not in (".", "..")


def _contained_regular_path(
    raw: str,
    repo_root: Path,
    source: str,
    pointer: str,
    *,
    missing_code: str,
    type_code: str,
    read_code: str,
) -> Path:
    if not _canonical_relative(raw):
        raise Diagnostic(
            "PROOF_PATH_INVALID", source, pointer, "expected a canonical relative path"
        )

    current = repo_root
    parts = PurePosixPath(raw).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError as error:
            raise Diagnostic(missing_code, source, pointer, str(error)) from error
        except OSError as error:
            raise Diagnostic(read_code, source, pointer, str(error)) from error
        if stat.S_ISLNK(info.st_mode):
            raise Diagnostic(
                "PROOF_PATH_INVALID", source, pointer, "symbolic links are rejected"
            )
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise Diagnostic(missing_code, source, pointer, "path ancestor is not a directory")

    if not stat.S_ISREG(info.st_mode):
        raise Diagnostic(type_code, source, pointer, "expected a regular file")
    if info.st_mode & (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH) == 0:
        raise Diagnostic(read_code, source, pointer, "file has no read permission bit")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(repo_root)
    except (OSError, ValueError) as error:
        raise Diagnostic(
            "PROOF_PATH_INVALID", source, pointer, "path is outside the repository"
        ) from error
    return current


def _argument_path(raw: str, repo_root: Path) -> Path:
    if not _canonical_relative(raw):
        raise Diagnostic(
            "PROOF_ARGUMENT_PATH_INVALID",
            raw,
            detail="expected a canonical relative repository path",
        )
    # CLI arguments reject symlinks and escape before their content/type is inspected.
    try:
        return _contained_regular_path(
            raw,
            repo_root,
            raw,
            "",
            missing_code="PROOF_ARGUMENT_NOT_FOUND",
            type_code="PROOF_ARGUMENT_TYPE",
            read_code="PROOF_ARGUMENT_READ",
        )
    except Diagnostic as diagnostic:
        if diagnostic.code == "PROOF_PATH_INVALID":
            raise Diagnostic(
                "PROOF_ARGUMENT_PATH_INVALID", raw, detail=diagnostic.detail
            ) from diagnostic
        raise


def _evidence_argument_path(raw: str, repo_root: Path) -> Path:
    if not _canonical_relative(raw):
        raise Diagnostic(
            "PROOF_ARGUMENT_PATH_INVALID",
            raw,
            detail="expected a canonical relative repository path",
        )
    try:
        return _contained_regular_path(
            raw,
            repo_root,
            raw,
            "",
            missing_code="PROOF_EVIDENCE_NOT_FOUND",
            type_code="PROOF_EVIDENCE_TYPE",
            read_code="PROOF_EVIDENCE_READ",
        )
    except Diagnostic as diagnostic:
        if diagnostic.code == "PROOF_PATH_INVALID":
            raise Diagnostic(
                "PROOF_ARGUMENT_PATH_INVALID", raw, detail=diagnostic.detail
            ) from diagnostic
        raise


def _load_json(path: Path, source: str, code: str) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise Diagnostic(code.replace("_JSON", "_READ"), source, detail=str(error)) from error
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise Diagnostic(code, source, detail=str(error)) from error


def _manifest_owned_path(
    manifest: dict[str, Any], field: str, repo_root: Path, manifest_arg: str
) -> Path:
    return _contained_regular_path(
        manifest[field]["path"],
        repo_root,
        manifest_arg,
        f"/{field}/path",
        missing_code="PROOF_PATH_NOT_FOUND",
        type_code="PROOF_PATH_NOT_FOUND",
        read_code="PROOF_PATH_NOT_FOUND",
    )


def _check_manifest_constants(
    manifest: dict[str, Any], manifest_arg: str
) -> list[Diagnostic]:
    if manifest["formatVersion"] != FORMAT_VERSION:
        return [
            Diagnostic("PROOF_MANIFEST_VERSION", manifest_arg, "/formatVersion")
        ]
    acceptance_fields = (
        (manifest["specification"]["reference"], SPECIFICATION_REFERENCE, "/specification/reference"),
        (manifest["theoremName"], THEOREM_NAME, "/theoremName"),
        (manifest["expectedStatement"], EXPECTED_STATEMENT, "/expectedStatement"),
    )
    for observed, expected, pointer in acceptance_fields:
        if observed != expected:
            return [Diagnostic("PROOF_ACCEPTANCE_SCOPE", manifest_arg, pointer)]
    if manifest["tool"]["name"] != LEAN_NAME:
        return [Diagnostic("PROOF_TOOL_IDENTITY", manifest_arg, "/tool/name")]
    if manifest["tool"]["invocation"] != LEAN_INVOCATION:
        return [Diagnostic("PROOF_TOOL_INVOCATION", manifest_arg, "/tool/invocation")]
    if manifest["expectedAxioms"] != EXPECTED_AXIOMS:
        return [Diagnostic("PROOF_EXPECTED_AXIOMS", manifest_arg, "/expectedAxioms")]
    return []


def _read_record(path: Path, label: str) -> dict[str, Any]:
    data = _load_json(path, label, "PROOF_INPUT_JSON")
    schemas = record_check.SchemaRegistry()
    if schemas.metaschema_errors:
        raise Diagnostic(
            "PROOF_INPUT_SCHEMA", label, detail=schemas.metaschema_errors[0]
        )
    diagnostic = record_check.validate_record(schemas, label, data)
    if diagnostic is not None:
        pointer = diagnostic.pointer[1:] if diagnostic.pointer.startswith("#") else diagnostic.pointer
        raise Diagnostic(
            "PROOF_INPUT_SCHEMA",
            label,
            pointer,
            f"{diagnostic.code} {diagnostic.pointer}",
        )
    return data


def _identity(record: dict[str, Any]) -> dict[str, Any]:
    return {key: record.get(key) for key in ("kind", "id", "version")}


def _check_linkage(
    manifest: dict[str, Any], specification: dict[str, Any], claim: dict[str, Any], manifest_arg: str
) -> list[Diagnostic]:
    specification_ref = manifest["specification"]["reference"]
    if _identity(specification) != specification_ref:
        return [
            Diagnostic("PROOF_LINK_MISMATCH", manifest_arg, "/specification/reference")
        ]
    claim_ref = manifest["claim"]["reference"]
    if _identity(claim) != claim_ref:
        return [Diagnostic("PROOF_LINK_MISMATCH", manifest_arg, "/claim/reference")]

    proposition = claim.get("proposition", {})
    if proposition.get("declarationId") != manifest["declarationId"]:
        return [Diagnostic("PROOF_LINK_MISMATCH", manifest_arg, "/declarationId")]
    if (
        claim.get("subject") != specification_ref
        or claim.get("governingSpecification") != specification_ref
        or proposition.get("specification") != specification_ref
    ):
        return [Diagnostic("PROOF_LINK_MISMATCH", manifest_arg, "/claim/reference")]
    declaration_ids: list[str | None] = []
    for field in (
        "carriers",
        "operations",
        "observations",
        "derivedObservations",
        "equivalences",
        "laws",
        "resources",
        "performancePropositions",
    ):
        declaration_ids.extend(item.get("id") for item in specification.get(field, []))
    effects = specification.get("effects")
    if isinstance(effects, dict):
        declaration_ids.append(effects.get("id"))
    law_ids = [law.get("id") for law in specification.get("laws", [])]
    if (
        law_ids.count(manifest["declarationId"]) != 1
        or declaration_ids.count(manifest["declarationId"]) != 1
    ):
        return [Diagnostic("PROOF_LINK_MISMATCH", manifest_arg, "/declarationId")]

    # These constants are checked after canonical linkage so PF1's deliberately
    # incoherent mutations retain their more informative LINK_MISMATCH diagnostics.
    if claim_ref != CLAIM_REFERENCE:
        return [Diagnostic("PROOF_ACCEPTANCE_SCOPE", manifest_arg, "/claim/reference")]
    if manifest["declarationId"] != DECLARATION_ID:
        return [Diagnostic("PROOF_ACCEPTANCE_SCOPE", manifest_arg, "/declarationId")]
    return []


def _run_process(command: list[str], timeout: float) -> tuple[int, str, str, bool]:
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            start_new_session=True,
        )
    except OSError as error:
        return 127, "", str(error), False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr, False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        return 124, stdout, stderr, True


def _check_tool(lean: str, manifest: dict[str, Any], manifest_arg: str) -> list[Diagnostic]:
    tool = manifest["tool"]
    # A manifest cannot redefine the accepted binary identity.
    if tool["version"] != LEAN_VERSION:
        return [
            Diagnostic("PROOF_TOOL_VERSION_MISMATCH", manifest_arg, "/tool/version")
        ]
    if tool["commit"] != LEAN_COMMIT:
        return [
            Diagnostic("PROOF_TOOL_VERSION_MISMATCH", manifest_arg, "/tool/commit")
        ]

    status, stdout, stderr, timed_out = _run_process(
        [lean, "--version"], PROCESS_TIMEOUT_SECONDS
    )
    if timed_out:
        return [Diagnostic("PROOF_TOOL_TIMEOUT", manifest_arg, "/tool/version")]
    match = _VERSION_OUTPUT.fullmatch(stdout)
    if status != 0 or stderr or match is None:
        return [
            Diagnostic(
                "PROOF_TOOL_VERSION_MISMATCH",
                manifest_arg,
                "/tool/version",
                f"exit={status}, stdout={stdout!r}, stderr={stderr!r}",
            )
        ]
    violations: list[Diagnostic] = []
    if match.group(1) != LEAN_VERSION:
        violations.append(
            Diagnostic("PROOF_TOOL_VERSION_MISMATCH", manifest_arg, "/tool/version")
        )
    if match.group(2) != LEAN_COMMIT:
        violations.append(
            Diagnostic("PROOF_TOOL_VERSION_MISMATCH", manifest_arg, "/tool/commit")
        )
    return violations


def _strip_lean_comments_and_strings(text: str) -> str:
    """Blank comments and string literals while preserving positions and lines."""
    output: list[str] = []
    index = 0
    depth = 0
    in_string = False
    escaped = False
    while index < len(text):
        pair = text[index : index + 2]
        char = text[index]
        if depth:
            if pair == "/-":
                depth += 1
                output.extend("  ")
                index += 2
            elif pair == "-/":
                depth -= 1
                output.extend("  ")
                index += 2
            else:
                output.append("\n" if char == "\n" else " ")
                index += 1
            continue
        if not in_string and pair == "--":
            while index < len(text) and text[index] != "\n":
                output.append(" ")
                index += 1
            continue
        if not in_string and pair == "/-":
            depth = 1
            output.extend("  ")
            index += 2
            continue
        if in_string:
            output.append("\n" if char == "\n" else " ")
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            output.append(" ")
            in_string = True
            index += 1
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _check_source_boundary(source_text: str, source_arg: str) -> bool:
    uncommented = _strip_lean_comments_and_strings(source_text)
    option = _LEADING_WARNING_OPTION.match(uncommented)
    declaration = _DECLARATION.search(uncommented)
    if option is None or (declaration is not None and declaration.start() < option.end()):
        raise Diagnostic(
            "PROOF_WARNING_POLICY_ORDER",
            source_arg,
            detail="a real leading `set_option warningAsError true` is required",
        )
    if re.search(r"(?m)^\s*import\b", uncommented):
        raise Diagnostic(
            "PROOF_SOURCE_BOUNDARY", source_arg, detail="the bounded proof imports no modules"
        )
    has_source_axiom = _SOURCE_AXIOM.search(uncommented) is not None
    if _SOURCE_UNSAFE.search(uncommented) or _SOURCE_EXECUTING_COMMAND.search(uncommented):
        raise Diagnostic(
            "PROOF_SOURCE_BOUNDARY",
            source_arg,
            detail="unsafe, #eval, and #print are outside the bounded source language",
        )
    return has_source_axiom


def _generated_source(source_text: str, manifest: dict[str, Any]) -> tuple[str, int]:
    stripped = source_text.rstrip("\n")
    original_lines = len(stripped.splitlines())
    theorem = manifest["theoremName"]
    statement = manifest["expectedStatement"]
    audit = (
        f"theorem __semantic_packages_expected_type : {statement} := {theorem}\n"
        f"#check @{theorem}\n"
        "#check @__semantic_packages_expected_type\n"
        f"#print axioms {theorem}\n"
    )
    return f"{stripped}\n\n{audit}", original_lines


def _valid_position(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _POSITION_KEYS
        and all(isinstance(value[key], int) and not isinstance(value[key], bool) for key in _POSITION_KEYS)
    )


def _valid_lean_message(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _LEAN_MESSAGE_KEYS
        and isinstance(value["caption"], str)
        and isinstance(value["data"], str)
        and _valid_position(value["endPos"])
        and isinstance(value["fileName"], str)
        and isinstance(value["isSilent"], bool)
        and isinstance(value["keepFullRange"], bool)
        and isinstance(value["kind"], str)
        and _valid_position(value["pos"])
        and value["severity"] in {"information", "warning", "error"}
    )


def _parse_lean_output(stdout: str, source_arg: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise Diagnostic(
                "PROOF_LEAN_OUTPUT_INVALID", source_arg, detail=str(error)
            ) from error
        if not _valid_lean_message(value):
            raise Diagnostic(
                "PROOF_LEAN_OUTPUT_INVALID",
                source_arg,
                detail="Lean emitted an unexpected JSON message shape",
            )
        messages.append(value)
    return messages


def _type_suffix(data: str, theorem_name: str) -> str | None:
    for prefix in (f"{theorem_name} : ", f"@{theorem_name} : "):
        if data.startswith(prefix):
            return data[len(prefix) :]
    return None


def _run_lean_checks(
    lean: str,
    source_path: Path,
    manifest: dict[str, Any],
    manifest_arg: str,
    source_arg: str,
) -> None:
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise Diagnostic("PROOF_PATH_NOT_FOUND", manifest_arg, "/source/path", str(error)) from error
    generated_text, original_lines = _generated_source(source_text, manifest)
    with tempfile.TemporaryDirectory(prefix="proof-check-audit-") as scratch:
        generated_path = Path(scratch) / "GeneratedAudit.lean"
        generated_path.write_text(generated_text, encoding="utf-8")
        status, stdout, stderr, timed_out = _run_process(
            [lean, "--trust=0", "--json", str(generated_path)],
            PROCESS_TIMEOUT_SECONDS,
        )
    if timed_out:
        raise Diagnostic("PROOF_EXECUTION_TIMEOUT", source_arg)
    if stderr:
        raise Diagnostic(
            "PROOF_LEAN_OUTPUT_INVALID", source_arg, detail=f"unexpected stderr: {stderr!r}"
        )
    messages = _parse_lean_output(stdout, source_arg)

    if any(message["kind"] == "hasSorry" for message in messages):
        raise Diagnostic("PROOF_SORRY", source_arg, detail="the proof uses `sorry`")
    if any(message["severity"] == "warning" for message in messages):
        raise Diagnostic("PROOF_LEAN_WARNING", source_arg, detail="Lean emitted a warning")

    errors = [message for message in messages if message["severity"] == "error"]
    source_errors = [
        message for message in errors if message["pos"]["line"] <= original_lines
    ]
    if source_errors:
        raise Diagnostic(
            "PROOF_LEAN_CHECK_FAILED", source_arg, detail=source_errors[0]["data"]
        )
    if errors:
        raise Diagnostic(
            "PROOF_STATEMENT_MISMATCH",
            manifest_arg,
            "/expectedStatement",
            "the theorem is not assignable to the pinned statement",
        )
    if status != 0:
        raise Diagnostic(
            "PROOF_LEAN_CHECK_FAILED", source_arg, detail=f"Lean exited {status}"
        )

    theorem = manifest["theoremName"]
    actual_types = [
        suffix
        for message in messages
        if message["severity"] == "information"
        if (suffix := _type_suffix(message["data"], theorem)) is not None
    ]
    expected_types = [
        suffix
        for message in messages
        if message["severity"] == "information"
        if (
            suffix := _type_suffix(
                message["data"], "__semantic_packages_expected_type"
            )
        )
        is not None
    ]
    if len(actual_types) != 1 or len(expected_types) != 1:
        raise Diagnostic(
            "PROOF_THEOREM_AUDIT_MISSING", manifest_arg, "/expectedStatement"
        )
    if actual_types[0] != expected_types[0]:
        raise Diagnostic(
            "PROOF_THEOREM_TYPE_MISMATCH", manifest_arg, "/expectedStatement"
        )

    axiom_observations: list[list[str]] = []
    mentions_theorem = False
    for message in messages:
        if message["severity"] != "information":
            continue
        data = message["data"]
        if f"'{theorem}'" in data:
            mentions_theorem = True
        no_axioms = _NO_AXIOMS.fullmatch(data)
        if no_axioms is not None and no_axioms.group(1) == theorem:
            axiom_observations.append([])
            continue
        has_axioms = _HAS_AXIOMS.fullmatch(data)
        if has_axioms is not None and has_axioms.group(1) == theorem:
            axiom_observations.append(
                [item.strip() for item in has_axioms.group(2).split(",") if item.strip()]
            )
    if not axiom_observations:
        code = "PROOF_AXIOM_AUDIT_INVALID" if mentions_theorem else "PROOF_AXIOM_AUDIT_MISSING"
        raise Diagnostic(code, source_arg)
    if len(axiom_observations) != 1:
        raise Diagnostic("PROOF_AXIOM_AUDIT_INVALID", source_arg)
    observed_axioms = axiom_observations[0]
    if observed_axioms != EXPECTED_AXIOMS:
        raise Diagnostic(
            "PROOF_AXIOM_DEPENDENCY",
            source_arg,
            detail=f"observed axioms {observed_axioms!r}",
        )


def _first_json_difference(
    expected: Any, observed: Any, path: tuple[str, ...] = ()
) -> tuple[str, ...] | None:
    if isinstance(expected, dict) and isinstance(observed, dict):
        for key in sorted(set(expected) | set(observed)):
            if key not in expected or key not in observed:
                return (*path, key)
            difference = _first_json_difference(expected[key], observed[key], (*path, key))
            if difference is not None:
                return difference
        return None
    if expected != observed:
        return path
    return None


def _check_evidence(
    path: Path,
    label: str,
    manifest_path: Path,
    manifest_arg: str,
    manifest: dict[str, Any],
) -> None:
    data = _load_json(path, label, "PROOF_EVIDENCE_JSON")
    schemas = record_check.SchemaRegistry()
    if schemas.metaschema_errors:
        raise Diagnostic("PROOF_EVIDENCE_SCHEMA", label, detail=schemas.metaschema_errors[0])
    schema_diagnostic = record_check.validate_record(schemas, label, data)
    if schema_diagnostic is not None:
        raise Diagnostic(
            "PROOF_EVIDENCE_SCHEMA", label, detail=schema_diagnostic.format()
        )
    if isinstance(data, dict) and data.get("environment", {}).get("checker") == "fixture-only":
        raise Diagnostic(
            "PROOF_FIXTURE_EVIDENCE_FORBIDDEN",
            label,
            "/environment/checker",
            "the Wave 2 fixture-only placeholder cannot back this proof",
        )

    assert isinstance(data, dict), "schema-valid Evidence is an object"
    for field, expected in EVIDENCE_IDENTITY.items():
        if data[field] != expected:
            raise Diagnostic("PROOF_EVIDENCE_IDENTITY", label, f"/{field}")
    if data["scope"] != "specification":
        raise Diagnostic("PROOF_EVIDENCE_SCOPE", label, "/scope")
    if data["claim"] != manifest["claim"]["reference"]:
        raise Diagnostic("PROOF_EVIDENCE_LINK", label, "/claim")
    if data["specification"] != manifest["specification"]["reference"]:
        raise Diagnostic("PROOF_EVIDENCE_LINK", label, "/specification")
    if data["mechanism"] != "proof":
        raise Diagnostic("PROOF_EVIDENCE_MECHANISM", label, "/mechanism")
    if data["result"] != "supports":
        raise Diagnostic("PROOF_EVIDENCE_RESULT", label, "/result")
    if data["applicability"] != {"profiles": []}:
        raise Diagnostic("PROOF_EVIDENCE_SCOPE", label, "/applicability/profiles")

    semantic_fields = {
        "reviewState": "accepted",
        "method": EVIDENCE_METHOD,
        "environment": EVIDENCE_ENVIRONMENT,
        "assumptions": EVIDENCE_ASSUMPTIONS,
        "exclusions": EVIDENCE_EXCLUSIONS,
    }
    for field, expected in semantic_fields.items():
        if data[field] != expected:
            raise Diagnostic("PROOF_EVIDENCE_SEMANTICS", label, f"/{field}")

    expected_provenance = {
        "manifest": {
            "path": manifest_arg,
            "sha256": _sha256_file(manifest_path),
        },
        "runner": {
            "path": manifest["runner"]["path"],
            "sha256": manifest["runner"]["sha256"],
        },
        "inputs": {
            "specification": {
                "path": manifest["specification"]["path"],
                "sha256": manifest["specification"]["sha256"],
            },
            "claim": {
                "path": manifest["claim"]["path"],
                "sha256": manifest["claim"]["sha256"],
            },
            "source": {
                "path": manifest["source"]["path"],
                "sha256": manifest["source"]["sha256"],
            },
        },
        "tool": dict(manifest["tool"]),
        "result": {"completed": True, "outputSha256": SUCCESS_SHA256},
    }
    difference = _first_json_difference(expected_provenance, data["provenance"])
    if difference is not None:
        pointer = "/provenance"
        if difference:
            pointer += "/" + "/".join(difference)
        raise Diagnostic("PROOF_EVIDENCE_PROVENANCE", label, pointer)


def _run_checks(args: argparse.Namespace) -> list[Diagnostic]:
    repo_root = Path.cwd().resolve()
    manifest_arg = args.manifest
    manifest_path = _argument_path(manifest_arg, repo_root)
    manifest = _load_json(manifest_path, manifest_arg, "PROOF_MANIFEST_JSON")

    shape = _validate_shape(manifest, MANIFEST_SCHEMA, "", manifest_arg)
    if shape:
        return shape
    constants = _check_manifest_constants(manifest, manifest_arg)
    if constants:
        return constants

    paths = {
        field: _manifest_owned_path(manifest, field, repo_root, manifest_arg)
        for field in ("specification", "claim", "source", "runner")
    }
    if Path(__file__).resolve(strict=True) != paths["runner"].resolve(strict=True):
        raise Diagnostic("PROOF_RUNNER_IDENTITY", manifest_arg, "/runner/path")
    digest_codes = {
        "specification": "PROOF_INPUT_DIGEST_MISMATCH",
        "claim": "PROOF_INPUT_DIGEST_MISMATCH",
        "source": "PROOF_SOURCE_DIGEST_MISMATCH",
        "runner": "PROOF_RUNNER_DIGEST_MISMATCH",
    }
    for field in ("specification", "claim", "source", "runner"):
        if _sha256_file(paths[field]) != manifest[field]["sha256"]:
            raise Diagnostic(digest_codes[field], manifest_arg, f"/{field}/sha256")

    specification = _read_record(paths["specification"], manifest["specification"]["path"])
    claim = _read_record(paths["claim"], manifest["claim"]["path"])
    linkage = _check_linkage(manifest, specification, claim, manifest_arg)
    if linkage:
        return linkage

    accepted_paths = {
        "specification": SPECIFICATION_PATH,
        "claim": CLAIM_PATH,
        "source": SOURCE_PATH,
        "runner": RUNNER_PATH,
    }
    for field, expected in accepted_paths.items():
        if manifest[field]["path"] != expected:
            return [Diagnostic("PROOF_ACCEPTANCE_SCOPE", manifest_arg, f"/{field}/path")]

    if args.evidence is not None:
        evidence_path = _evidence_argument_path(args.evidence, repo_root)
        _check_evidence(
            evidence_path, args.evidence, manifest_path, manifest_arg, manifest
        )

    source_text = paths["source"].read_text(encoding="utf-8")
    has_source_axiom = _check_source_boundary(
        source_text, manifest["source"]["path"]
    )

    tool = _check_tool(args.lean, manifest, manifest_arg)
    if tool:
        return tool

    _run_lean_checks(
        args.lean,
        paths["source"],
        manifest,
        manifest_arg,
        manifest["source"]["path"],
    )
    if has_source_axiom:
        raise Diagnostic(
            "PROOF_SOURCE_BOUNDARY",
            manifest["source"]["path"],
            detail="declared axioms are outside the bounded source language",
        )
    return []


def main() -> int:
    parser = _QuietParser(description=__doc__, add_help=False)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--lean", required=True)
    parser.add_argument("--evidence")
    parser.add_argument("-h", "--help", action="help")
    try:
        args = parser.parse_args()
    except _ArgumentError as error:
        print(Diagnostic("PROOF_ARGUMENT", "<command-line>", detail=str(error)).signature())
        return 1

    try:
        diagnostics = _run_checks(args)
    except Diagnostic as diagnostic:
        diagnostics = [diagnostic]
    except Exception as error:  # The CLI contract never exposes a traceback/stderr.
        diagnostics = [Diagnostic("PROOF_INTERNAL_ERROR", args.manifest, detail=str(error))]

    if diagnostics:
        for diagnostic in sorted(diagnostics, key=lambda item: item.key()):
            print(diagnostic.signature())
        return 1
    print(SUCCESS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
