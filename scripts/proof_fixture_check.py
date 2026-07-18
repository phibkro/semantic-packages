#!/usr/bin/env python3
"""Red-first oracle for ADR 0009's bounded `pop-empty` proof boundary.

The harness contains no proof checker fallback.  It validates its committed JSON and
Lean test data, then invokes the future standalone `scripts/proof_check.py` in
disposable repository-shaped trees.  Stable product output is exit status plus
diagnostic code, source label, JSON pointer, and ordering; prose after `: ` is not
frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import record_check


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "proof_check.py"
ACTUAL_PROOF = ROOT / "proofs" / "stack-pop-empty" / "StackPopEmpty.lean"
ACTUAL_MANIFEST = ROOT / "proofs" / "stack-pop-empty" / "manifest.json"
FIXTURES = ROOT / "fixtures" / "proofs" / "v1"
TEMPLATE = FIXTURES / "manifest.template.json"
SPECIFICATION = ROOT / "fixtures" / "records" / "valid" / "stack-spec.json"
CLAIM = ROOT / "fixtures" / "records" / "valid" / "pop-empty-spec-claim.json"
PLACEHOLDER_EVIDENCE = (
    ROOT / "fixtures" / "records" / "valid" / "pop-empty-proof-evidence.json"
)
PROOF_EVIDENCE_TEMPLATE = FIXTURES / "proof-evidence.template.json"
MANIFEST_LABEL = "proofs/stack-pop-empty/manifest.json"
SOURCE_LABEL = "proofs/stack-pop-empty/StackPopEmpty.lean"
EVIDENCE_LABEL = "fixtures/records/valid/pop-empty-proof-evidence.json"
PROOF_EVIDENCE_LABEL = "fixtures/proofs/v1/stack-pop-empty-model-proof.json"
SUCCESS = "Proof is valid: 0 diagnostics."
FALSE_SOURCE_AXIOM_MESSAGE = "'stack_pop_empty' does not depend on any axioms"
LEAN_VERSION = "4.30.0"
LEAN_COMMIT = "d024af099ca4bf2c86f649261ebf59565dc8c622"
DIAGNOSTIC_HEAD = re.compile(r"^[A-Z][A-Z0-9_]+ [^#]+#(?:/.*)?$")
HARNESS_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class Observation:
    exit_status: int
    signatures: list[str]
    stdout: str
    stderr: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _parse_signatures(stdout: str) -> tuple[list[str], list[str]]:
    if stdout.strip() == SUCCESS:
        return [], []
    signatures: list[str] = []
    errors: list[str] = []
    for line in stdout.splitlines():
        if not line:
            continue
        head = line.split(": ", 1)[0]
        if not DIAGNOSTIC_HEAD.fullmatch(head):
            errors.append(f"unrecognized output line {line!r}")
        else:
            signatures.append(head)
    return signatures, errors


def _invoke(
    checker: Path,
    cwd: Path,
    manifest: Path,
    lean: Path,
    *,
    evidence: Path | None = None,
    environment: dict[str, str] | None = None,
) -> tuple[Observation, list[str]]:
    command = [
        sys.executable,
        str(checker),
        "--manifest",
        str(manifest),
        "--lean",
        str(lean),
    ]
    if evidence is not None:
        command.extend(["--evidence", str(evidence)])
    process_environment = os.environ.copy()
    if environment:
        process_environment.update(environment)
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=process_environment,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=HARNESS_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    signatures, parse_errors = _parse_signatures(stdout)
    if timed_out:
        parse_errors.append(
            f"checker exceeded the {HARNESS_TIMEOUT_SECONDS:.1f}s harness deadline"
        )
    return (
        Observation(
            exit_status=124 if timed_out else process.returncode,
            signatures=signatures,
            stdout=stdout,
            stderr=stderr,
        ),
        parse_errors,
    )


def _expect(
    name: str,
    checker: Path,
    cwd: Path,
    manifest: Path,
    lean: Path,
    exit_status: int,
    signatures: list[str],
    *,
    evidence: Path | None = None,
    environment: dict[str, str] | None = None,
) -> list[str]:
    observation, parse_errors = _invoke(
        checker,
        cwd,
        manifest,
        lean,
        evidence=evidence,
        environment=environment,
    )
    failures = [f"{name}: {error}" for error in parse_errors]
    if observation.exit_status != exit_status:
        failures.append(
            f"{name}: expected exit {exit_status}, got {observation.exit_status}; "
            f"stdout={observation.stdout!r}, stderr={observation.stderr!r}"
        )
    if observation.signatures != signatures:
        failures.append(
            f"{name}: expected diagnostics {signatures!r}, got "
            f"{observation.signatures!r}; stdout={observation.stdout!r}"
        )
    if observation.stderr:
        failures.append(f"{name}: expected empty stderr, got {observation.stderr!r}")
    return failures


def _materialize(
    raw: str,
    source_name: str = "positive.lean",
) -> tuple[Path, Path, Path, Path, Path, dict[str, Any]]:
    repository = Path(raw)
    checker = repository / "scripts" / "proof_check.py"
    source = repository / SOURCE_LABEL
    manifest_path = repository / MANIFEST_LABEL
    specification = repository / SPECIFICATION.relative_to(ROOT)
    claim = repository / CLAIM.relative_to(ROOT)
    evidence = repository / PLACEHOLDER_EVIDENCE.relative_to(ROOT)
    fake_lean = repository / FIXTURES.relative_to(ROOT) / "fake_lean.py"

    _copy(CHECKER, checker)
    _copy(ROOT / "scripts" / "record_check.py", repository / "scripts" / "record_check.py")
    shutil.copytree(ROOT / "schemas", repository / "schemas")
    _copy(FIXTURES / source_name, source)
    _copy(SPECIFICATION, specification)
    _copy(CLAIM, claim)
    _copy(PLACEHOLDER_EVIDENCE, evidence)
    _copy(FIXTURES / "fake_lean.py", fake_lean)
    fake_lean.write_text(
        fake_lean.read_text(encoding="utf-8").replace(
            "#!/usr/bin/env python3", f"#!{sys.executable}", 1
        ),
        encoding="utf-8",
    )
    fake_lean.chmod(0o755)

    substitutions = {
        "$SPECIFICATION_SHA256": _sha256(specification),
        "$CLAIM_SHA256": _sha256(claim),
        "$SOURCE_SHA256": _sha256(source),
        "$RUNNER_SHA256": _sha256(checker),
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    for token, value in substitutions.items():
        template = template.replace(token, value)
    manifest = json.loads(template)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return repository, checker, manifest_path, evidence, fake_lean, manifest


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _materialize_proof_evidence(
    repository: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    substitutions = {
        "$MANIFEST_SHA256": _sha256(manifest_path),
        "$RUNNER_SHA256": manifest["runner"]["sha256"],
        "$SPECIFICATION_SHA256": manifest["specification"]["sha256"],
        "$CLAIM_SHA256": manifest["claim"]["sha256"],
        "$SOURCE_SHA256": manifest["source"]["sha256"],
        "$SUCCESS_SHA256": hashlib.sha256(
            f"{SUCCESS}\n".encode("utf-8")
        ).hexdigest(),
    }
    rendered = PROOF_EVIDENCE_TEMPLATE.read_text(encoding="utf-8")
    for token, value in substitutions.items():
        rendered = rendered.replace(token, value)
    data = json.loads(rendered)
    path = repository / PROOF_EVIDENCE_LABEL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path, data


def _case(
    name: str,
    lean: Path,
    *,
    source_name: str = "positive.lean",
    mutate: Callable[[dict[str, Any]], None] | None = None,
    expected: str | None = None,
    evidence: bool = False,
    fake_mode: str | None = None,
    malformed_manifest: bool = False,
    prepare: Callable[[Path, dict[str, Any]], None] | None = None,
) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-proof-fixture-") as raw:
        (
            repository,
            checker,
            manifest_path,
            _evidence_path,
            fake_lean,
            manifest,
        ) = _materialize(raw, source_name)
        if mutate:
            mutate(manifest)
        if prepare:
            prepare(repository, manifest)
        if malformed_manifest:
            manifest_path.write_text("{ not json\n", encoding="utf-8")
        else:
            _write_manifest(manifest_path, manifest)
        selected_lean = fake_lean if fake_mode else lean
        environment = {"FAKE_LEAN_MODE": fake_mode} if fake_mode else None
        signatures = [expected] if expected else []
        return _expect(
            name,
            checker,
            repository,
            Path(MANIFEST_LABEL),
            selected_lean,
            1 if expected else 0,
            signatures,
            evidence=Path(EVIDENCE_LABEL) if evidence else None,
            environment=environment,
        )


def _run_lean(lean: Path, source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(lean), "--trust=0", "--json", str(source)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def check_fixture_inputs(lean: Path | None) -> list[str]:
    failures: list[str] = []
    try:
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        failures.append(f"fixture manifest template is valid JSON: {error}")
        template = {}
    if template.get("expectedStatement") != (
        "∀ (A : Type u), pop (empty : ObservedStack A) = Option.none"
    ):
        failures.append("fixture manifest pins the exact universal expected statement")
    try:
        evidence_template = json.loads(
            PROOF_EVIDENCE_TEMPLATE.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        failures.append(f"proof Evidence template is valid JSON: {error}")
        evidence_template = None
    if evidence_template is not None:
        schemas = record_check.SchemaRegistry()
        if schemas.metaschema_errors:
            failures.append(
                "proof Evidence template schema registry is valid: "
                f"{schemas.metaschema_errors[0]}"
            )
        else:
            diagnostic = record_check.validate_record(
                schemas,
                PROOF_EVIDENCE_TEMPLATE.relative_to(ROOT).as_posix(),
                evidence_template,
            )
            if diagnostic is not None:
                failures.append(
                    "proof Evidence template is schema-valid: "
                    f"{diagnostic.format()}"
                )
    for source in sorted(FIXTURES.glob("*.lean")):
        try:
            source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            failures.append(f"{source.name} is readable UTF-8: {error}")
    positive = (FIXTURES / "positive.lean").read_text(encoding="utf-8")
    if "import " in positive or "Realization" in positive or "adapter" in positive:
        failures.append("positive proof model imports no Realization or adapter code")
    if "(A : Type u)" not in positive or "ObservedStack" not in positive:
        failures.append("positive proof model is universal over the observed Stack model")

    if lean is None:
        return failures
    version = subprocess.run(
        [str(lean), "--version"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if (
        version.returncode != 0
        or LEAN_VERSION not in version.stdout
        or LEAN_COMMIT not in version.stdout
    ):
        failures.append(
            "fixture syntax checker is exact Lean 4.30.0: "
            f"exit={version.returncode}, stdout={version.stdout!r}, stderr={version.stderr!r}"
        )
        return failures

    expected_exit = {
        "positive.lean": 0,
        "false-theorem.lean": 1,
        "sorry.lean": 1,
        "injected-axiom.lean": 0,
        "classical-choice.lean": 0,
        "wrong-true-statement.lean": 0,
        "finite-specialization.lean": 0,
        "warning-policy-too-late.lean": 0,
        "defaulted-extra-binder.lean": 0,
        "autoparam-extra-binder.lean": 0,
        "warning-policy-comment.lean": 0,
        "unused-axiom.lean": 0,
        "modifier-unsafe.lean": 0,
        "source-eval.lean": 0,
        "source-print.lean": 0,
        "wrapped-source-eval.lean": 0,
        "wrapped-source-print.lean": 0,
    }
    for name, status in expected_exit.items():
        completed = _run_lean(lean, FIXTURES / name)
        if completed.returncode != status:
            failures.append(
                f"{name} direct Lean control: expected exit {status}, got "
                f"{completed.returncode}; stdout={completed.stdout!r}, "
                f"stderr={completed.stderr!r}"
            )
        if (
            name in {"source-eval.lean", "wrapped-source-eval.lean"}
            and FALSE_SOURCE_AXIOM_MESSAGE not in completed.stdout
        ):
            failures.append(
                f"{name} emits the benign false no-axioms message: "
                f"stdout={completed.stdout!r}, stderr={completed.stderr!r}"
            )

    axiom_expectations = {
        "positive.lean": "does not depend on any axioms",
        "unused-axiom.lean": "does not depend on any axioms",
        "injected-axiom.lean": "depends on axioms",
        "classical-choice.lean": "depends on axioms",
    }
    with tempfile.TemporaryDirectory(prefix="semantic-proof-axioms-") as raw:
        directory = Path(raw)
        for name, expected in axiom_expectations.items():
            augmented = directory / name
            augmented.write_text(
                (FIXTURES / name).read_text(encoding="utf-8")
                + "\n#print axioms stack_pop_empty\n",
                encoding="utf-8",
            )
            completed = _run_lean(lean, augmented)
            if completed.returncode != 0 or expected not in completed.stdout:
                failures.append(
                    f"{name} axiom audit: expected {expected!r}; exit="
                    f"{completed.returncode}, stdout={completed.stdout!r}, "
                    f"stderr={completed.stderr!r}"
                )
    return failures


def check_product_contract(lean: Path) -> tuple[list[str], int]:
    failures: list[str] = []
    groups = 0

    def run(*args: Any, **kwargs: Any) -> None:
        nonlocal groups
        groups += 1
        failures.extend(_case(*args, lean=lean, **kwargs))

    def run_group(cases: list[tuple[tuple[Any, ...], dict[str, Any]]]) -> None:
        nonlocal groups
        groups += 1
        for positional, keyword in cases:
            failures.extend(_case(*positional, lean=lean, **keyword))

    run("clean universal model satisfies the proof boundary")
    run(
        "a false theorem is a proof error, not a semantic challenge",
        source_name="false-theorem.lean",
        expected=f"PROOF_LEAN_CHECK_FAILED {SOURCE_LABEL}#",
    )
    run(
        "sorry is rejected even though default Lean may exit zero",
        source_name="sorry.lean",
        expected=f"PROOF_SORRY {SOURCE_LABEL}#",
    )
    run(
        "a declared axiom is rejected",
        source_name="injected-axiom.lean",
        expected=f"PROOF_AXIOM_DEPENDENCY {SOURCE_LABEL}#",
    )
    run(
        "an axiom-producing classical control is rejected",
        source_name="classical-choice.lean",
        expected=f"PROOF_AXIOM_DEPENDENCY {SOURCE_LABEL}#",
    )
    run(
        "the theorem name cannot hide a wrong but true statement",
        source_name="wrong-true-statement.lean",
        expected=f"PROOF_STATEMENT_MISMATCH {MANIFEST_LABEL}#/expectedStatement",
    )
    run(
        "a finite specialization is not universal proof",
        source_name="finite-specialization.lean",
        expected=f"PROOF_STATEMENT_MISMATCH {MANIFEST_LABEL}#/expectedStatement",
    )
    run(
        "warning policy must precede every declaration",
        source_name="warning-policy-too-late.lean",
        expected=f"PROOF_WARNING_POLICY_ORDER {SOURCE_LABEL}#",
    )
    run(
        "the declaration link is exact",
        mutate=lambda manifest: manifest.__setitem__("declarationId", "pop-push"),
        expected=f"PROOF_LINK_MISMATCH {MANIFEST_LABEL}#/declarationId",
    )
    run(
        "the Claim link is exact",
        mutate=lambda manifest: manifest["claim"]["reference"].__setitem__(
            "id", "another-claim"
        ),
        expected=f"PROOF_LINK_MISMATCH {MANIFEST_LABEL}#/claim/reference",
    )
    run(
        "a stale Specification digest is rejected",
        mutate=lambda manifest: manifest["specification"].__setitem__(
            "sha256", "0" * 64
        ),
        expected=(
            f"PROOF_INPUT_DIGEST_MISMATCH "
            f"{MANIFEST_LABEL}#/specification/sha256"
        ),
    )
    run(
        "a stale Claim digest is rejected",
        mutate=lambda manifest: manifest["claim"].__setitem__("sha256", "0" * 64),
        expected=f"PROOF_INPUT_DIGEST_MISMATCH {MANIFEST_LABEL}#/claim/sha256",
    )
    run(
        "a stale proof-source digest is rejected",
        mutate=lambda manifest: manifest["source"].__setitem__("sha256", "0" * 64),
        expected=f"PROOF_SOURCE_DIGEST_MISMATCH {MANIFEST_LABEL}#/source/sha256",
    )
    run(
        "a stale checker digest is rejected",
        mutate=lambda manifest: manifest["runner"].__setitem__("sha256", "0" * 64),
        expected=f"PROOF_RUNNER_DIGEST_MISMATCH {MANIFEST_LABEL}#/runner/sha256",
    )
    run(
        "the exact Lean version is checked",
        mutate=lambda manifest: manifest["tool"].__setitem__("version", "4.29.0"),
        expected=f"PROOF_TOOL_VERSION_MISMATCH {MANIFEST_LABEL}#/tool/version",
    )
    run(
        "the exact Lean commit is checked",
        mutate=lambda manifest: manifest["tool"].__setitem__("commit", "0" * 40),
        expected=f"PROOF_TOOL_VERSION_MISMATCH {MANIFEST_LABEL}#/tool/commit",
    )
    run(
        "missing no-axioms output is rejected despite exit zero",
        fake_mode="missing-axiom-audit",
        expected=f"PROOF_AXIOM_AUDIT_MISSING {SOURCE_LABEL}#",
    )
    run(
        "invalid no-axioms output is rejected despite exit zero",
        fake_mode="invalid-axiom-audit",
        expected=f"PROOF_AXIOM_AUDIT_INVALID {SOURCE_LABEL}#",
    )
    run(
        "the accepted fixture-only Evidence cannot be reused",
        evidence=True,
        expected=(
            f"PROOF_FIXTURE_EVIDENCE_FORBIDDEN "
            f"{EVIDENCE_LABEL}#/environment/checker"
        ),
    )
    run(
        "malformed manifest JSON is stable input failure",
        malformed_manifest=True,
        expected=f"PROOF_MANIFEST_JSON {MANIFEST_LABEL}#",
    )

    def remove_statement(manifest: dict[str, Any]) -> None:
        del manifest["expectedStatement"]

    run(
        "a missing manifest field is rejected",
        mutate=remove_statement,
        expected=f"PROOF_MANIFEST_SHAPE {MANIFEST_LABEL}#/expectedStatement",
    )
    run(
        "an absolute proof path is rejected",
        mutate=lambda manifest: manifest["source"].__setitem__(
            "path", "/tmp/StackPopEmpty.lean"
        ),
        expected=f"PROOF_PATH_INVALID {MANIFEST_LABEL}#/source/path",
    )
    run(
        "a parent-traversal proof path is rejected",
        mutate=lambda manifest: manifest["source"].__setitem__(
            "path", "proofs/stack-pop-empty/../../../outside.lean"
        ),
        expected=f"PROOF_PATH_INVALID {MANIFEST_LABEL}#/source/path",
    )
    run(
        "a missing proof path is rejected",
        mutate=lambda manifest: manifest["source"].__setitem__(
            "path", "proofs/stack-pop-empty/Missing.lean"
        ),
        expected=f"PROOF_PATH_NOT_FOUND {MANIFEST_LABEL}#/source/path",
    )

    groups += 1
    failures.extend(
        _expect(
            "the actual product proof boundary exists and passes",
            CHECKER,
            ROOT,
            ACTUAL_MANIFEST.relative_to(ROOT),
            lean,
            0,
            [],
        )
    )

    # PF2 acceptance-boundary successor groups. Each group may contain multiple
    # isolated witnesses, but every witness retains one exact diagnostic oracle.
    run_group(
        [
            (
                ("only proof-manifest format version 1 is accepted",),
                {
                    "mutate": lambda manifest: manifest.__setitem__("formatVersion", 2),
                    "expected": f"PROOF_MANIFEST_VERSION {MANIFEST_LABEL}#/formatVersion",
                },
            )
        ]
    )

    def prepare_alias_theorem(repository: Path, manifest: dict[str, Any]) -> None:
        source = repository / manifest["source"]["path"]
        source.write_text(
            source.read_text(encoding="utf-8")
            + "\ntheorem alternate_pop_empty (A : Type u) :\n"
            + "    pop (empty : ObservedStack A) = Option.none := stack_pop_empty A\n",
            encoding="utf-8",
        )
        manifest["source"]["sha256"] = _sha256(source)

    run_group(
        [
            (
                ("the accepted Specification address is constant",),
                {
                    "mutate": lambda manifest: manifest["specification"]["reference"].__setitem__(
                        "id", "another-specification"
                    ),
                    "expected": f"PROOF_ACCEPTANCE_SCOPE {MANIFEST_LABEL}#/specification/reference",
                },
            ),
            (
                ("the accepted theorem name is constant",),
                {
                    "mutate": lambda manifest: manifest.__setitem__(
                        "theoremName", "alternate_pop_empty"
                    ),
                    "prepare": prepare_alias_theorem,
                    "expected": f"PROOF_ACCEPTANCE_SCOPE {MANIFEST_LABEL}#/theoremName",
                },
            ),
            (
                ("the accepted statement spelling is constant",),
                {
                    "mutate": lambda manifest: manifest.__setitem__(
                        "expectedStatement",
                        "∀ (A : Type u), pop (empty : ObservedStack A) = none",
                    ),
                    "expected": f"PROOF_ACCEPTANCE_SCOPE {MANIFEST_LABEL}#/expectedStatement",
                },
            ),
        ]
    )

    run_group(
        [
            (
                ("the proof tool name is exactly Lean",),
                {
                    "mutate": lambda manifest: manifest["tool"].__setitem__(
                        "name", "CompatibleLean"
                    ),
                    "expected": f"PROOF_TOOL_IDENTITY {MANIFEST_LABEL}#/tool/name",
                },
            ),
            (
                ("the generated-source invocation is exact",),
                {
                    "mutate": lambda manifest: manifest["tool"].__setitem__(
                        "invocation", ["$LEAN", "--json", "$GENERATED_SOURCE"]
                    ),
                    "expected": f"PROOF_TOOL_INVOCATION {MANIFEST_LABEL}#/tool/invocation",
                },
            ),
        ]
    )

    run_group(
        [
            (
                ("the accepted manifest cannot pre-authorize axioms",),
                {
                    "mutate": lambda manifest: manifest.__setitem__(
                        "expectedAxioms", ["Classical.choice"]
                    ),
                    "expected": f"PROOF_EXPECTED_AXIOMS {MANIFEST_LABEL}#/expectedAxioms",
                },
            )
        ]
    )

    def prepare_record_input(
        field: str, *, malformed: bool
    ) -> Callable[[Path, dict[str, Any]], None]:
        def prepare(repository: Path, manifest: dict[str, Any]) -> None:
            path = repository / manifest[field]["path"]
            if malformed:
                path.write_text("{ not json\n", encoding="utf-8")
            else:
                record = json.loads(path.read_text(encoding="utf-8"))
                record["unexpected"] = True
                path.write_text(
                    json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            manifest[field]["sha256"] = _sha256(path)

        return prepare

    run_group(
        [
            (
                ("malformed Specification input is diagnosed after digest verification",),
                {
                    "prepare": prepare_record_input("specification", malformed=True),
                    "expected": (
                        "PROOF_INPUT_JSON "
                        "fixtures/records/valid/stack-spec.json#"
                    ),
                },
            ),
            (
                ("schema-invalid Specification input is rejected",),
                {
                    "prepare": prepare_record_input("specification", malformed=False),
                    "expected": (
                        "PROOF_INPUT_SCHEMA "
                        "fixtures/records/valid/stack-spec.json#/unexpected"
                    ),
                },
            ),
            (
                ("malformed Claim input is diagnosed after digest verification",),
                {
                    "prepare": prepare_record_input("claim", malformed=True),
                    "expected": (
                        "PROOF_INPUT_JSON "
                        "fixtures/records/valid/pop-empty-spec-claim.json#"
                    ),
                },
            ),
            (
                ("schema-invalid Claim input is rejected",),
                {
                    "prepare": prepare_record_input("claim", malformed=False),
                    "expected": (
                        "PROOF_INPUT_SCHEMA "
                        "fixtures/records/valid/pop-empty-spec-claim.json#/unexpected"
                    ),
                },
            ),
        ]
    )

    def prepare_alternate_graph(repository: Path, manifest: dict[str, Any]) -> None:
        spec_path = repository / manifest["specification"]["path"]
        claim_path = repository / manifest["claim"]["path"]
        specification = json.loads(spec_path.read_text(encoding="utf-8"))
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
        specification["id"] = "alternate-stack"
        specification["laws"][0]["id"] = "alternate-pop-empty"
        alternate_spec = {
            "kind": "specification",
            "id": "alternate-stack",
            "version": "0.1.0",
        }
        claim["id"] = "alternate-pop-empty-claim"
        claim["subject"] = dict(alternate_spec)
        claim["governingSpecification"] = dict(alternate_spec)
        claim["proposition"]["specification"] = dict(alternate_spec)
        claim["proposition"]["declarationId"] = "alternate-pop-empty"
        spec_path.write_text(json.dumps(specification, indent=2) + "\n", encoding="utf-8")
        claim_path.write_text(json.dumps(claim, indent=2) + "\n", encoding="utf-8")
        manifest["specification"]["reference"] = dict(alternate_spec)
        manifest["claim"]["reference"]["id"] = "alternate-pop-empty-claim"
        manifest["declarationId"] = "alternate-pop-empty"
        manifest["specification"]["sha256"] = _sha256(spec_path)
        manifest["claim"]["sha256"] = _sha256(claim_path)

    run_group(
        [
            (
                ("a coherent alternate record and declaration graph is outside acceptance",),
                {
                    "prepare": prepare_alternate_graph,
                    "expected": f"PROOF_ACCEPTANCE_SCOPE {MANIFEST_LABEL}#/specification/reference",
                },
            )
        ]
    )

    run_group(
        [
            (
                ("a manifest cannot authorize a declared proof axiom",),
                {
                    "source_name": "injected-axiom.lean",
                    "mutate": lambda manifest: manifest.__setitem__(
                        "expectedAxioms", ["assumed_pop_empty"]
                    ),
                    "expected": (
                        f"PROOF_EXPECTED_AXIOMS "
                        f"{MANIFEST_LABEL}#/expectedAxioms"
                    ),
                },
            ),
            (
                ("a manifest cannot authorize Classical.choice",),
                {
                    "source_name": "classical-choice.lean",
                    "mutate": lambda manifest: manifest.__setitem__(
                        "expectedAxioms", ["Classical.choice"]
                    ),
                    "expected": (
                        f"PROOF_EXPECTED_AXIOMS "
                        f"{MANIFEST_LABEL}#/expectedAxioms"
                    ),
                },
            ),
        ]
    )

    run_group(
        [
            (
                ("a defaulted extra theorem binder is not exact type equality",),
                {
                    "source_name": "defaulted-extra-binder.lean",
                    "expected": (
                        f"PROOF_THEOREM_TYPE_MISMATCH "
                        f"{MANIFEST_LABEL}#/expectedStatement"
                    ),
                },
            ),
            (
                ("an autoParam extra theorem binder is not exact type equality",),
                {
                    "source_name": "autoparam-extra-binder.lean",
                    "expected": (
                        f"PROOF_THEOREM_TYPE_MISMATCH "
                        f"{MANIFEST_LABEL}#/expectedStatement"
                    ),
                },
            ),
        ]
    )

    run_group(
        [
            (
                ("a warning-policy phrase inside a comment is not a command",),
                {
                    "source_name": "warning-policy-comment.lean",
                    "expected": f"PROOF_WARNING_POLICY_ORDER {SOURCE_LABEL}#",
                },
            ),
            (
                ("every structured Lean warning is rejected",),
                {
                    "fake_mode": "warning-with-forged-positive",
                    "expected": f"PROOF_LEAN_WARNING {SOURCE_LABEL}#",
                },
            ),
        ]
    )

    def run_argument_case(mode: str) -> list[str]:
        with tempfile.TemporaryDirectory(prefix="semantic-proof-argument-") as raw:
            repository, checker, manifest_path, _evidence, _fake, manifest = _materialize(raw)
            _write_manifest(manifest_path, manifest)
            benign_evidence = repository / "evidence" / "clean.json"
            benign_evidence.parent.mkdir(parents=True, exist_ok=True)
            benign_evidence.write_text("{}\n", encoding="utf-8")
            manifest_arg: Path = Path(MANIFEST_LABEL)
            evidence_arg: Path | None = None
            if mode == "manifest-absolute":
                manifest_arg = manifest_path
            elif mode == "manifest-traversal":
                manifest_arg = Path(
                    "proofs/stack-pop-empty/../../proofs/stack-pop-empty/manifest.json"
                )
            elif mode == "manifest-symlink":
                external = repository.parent / f"{repository.name}-manifest.json"
                external.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
                (repository / "manifest-link.json").symlink_to(external)
                manifest_arg = Path("manifest-link.json")
            elif mode == "evidence-absolute":
                evidence_arg = benign_evidence
            elif mode == "evidence-traversal":
                evidence_arg = Path("evidence/../evidence/clean.json")
            elif mode == "evidence-symlink":
                external = repository.parent / f"{repository.name}-evidence.json"
                external.write_text("{}\n", encoding="utf-8")
                (repository / "evidence-link.json").symlink_to(external)
                evidence_arg = Path("evidence-link.json")
            else:
                raise AssertionError(mode)
            selected = manifest_arg if mode.startswith("manifest") else evidence_arg
            assert selected is not None
            try:
                return _expect(
                    f"{mode} is rejected at the CLI boundary",
                    checker,
                    repository,
                    manifest_arg,
                    lean,
                    1,
                    [f"PROOF_ARGUMENT_PATH_INVALID {selected}#"],
                    evidence=evidence_arg,
                )
            finally:
                for suffix in ("manifest.json", "evidence.json"):
                    external = repository.parent / f"{repository.name}-{suffix}"
                    if external.exists():
                        external.unlink()

    groups += 1
    for argument_mode in (
        "manifest-absolute",
        "manifest-traversal",
        "manifest-symlink",
        "evidence-absolute",
        "evidence-traversal",
        "evidence-symlink",
    ):
        failures.extend(run_argument_case(argument_mode))

    external_owned_paths = {
        "specification": SPECIFICATION,
        "claim": CLAIM,
        "source": FIXTURES / "positive.lean",
        "runner": CHECKER,
    }

    def prepare_owned_symlink(
        field: str,
    ) -> Callable[[Path, dict[str, Any]], None]:
        def prepare(repository: Path, manifest: dict[str, Any]) -> None:
            path = repository / manifest[field]["path"]
            path.unlink()
            path.symlink_to(external_owned_paths[field])

        return prepare

    run_group(
        [
            (
                (f"manifest-owned {field} paths cannot escape through symlinks",),
                {
                    "prepare": prepare_owned_symlink(field),
                    "expected": f"PROOF_PATH_INVALID {MANIFEST_LABEL}#/{field}/path",
                },
            )
            for field in ("specification", "claim", "source", "runner")
        ]
    )

    def run_evidence_case(mode: str) -> list[str]:
        with tempfile.TemporaryDirectory(prefix="semantic-proof-evidence-") as raw:
            repository, checker, manifest_path, _evidence, _fake, manifest = _materialize(raw)
            _write_manifest(manifest_path, manifest)
            relative = Path("evidence") / f"{mode}.json"
            path = repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            expected_code = {
                "missing": "PROOF_EVIDENCE_NOT_FOUND",
                "directory": "PROOF_EVIDENCE_TYPE",
                "unreadable": "PROOF_EVIDENCE_READ",
                "malformed": "PROOF_EVIDENCE_JSON",
            }[mode]
            original_mode: int | None = None
            if mode == "directory":
                path.mkdir()
            elif mode == "unreadable":
                path.write_text("{}\n", encoding="utf-8")
                original_mode = path.stat().st_mode & 0o7777
                path.chmod(0)
                if os.access(path, os.R_OK):
                    path.chmod(original_mode)
                    return ["unreadable Evidence control: permissions were not enforced"]
            elif mode == "malformed":
                path.write_text("{ not json\n", encoding="utf-8")
            try:
                return _expect(
                    f"{mode} Evidence is diagnosed",
                    checker,
                    repository,
                    Path(MANIFEST_LABEL),
                    lean,
                    1,
                    [f"{expected_code} {relative.as_posix()}#"],
                    evidence=relative,
                )
            finally:
                if original_mode is not None:
                    path.chmod(original_mode)

    groups += 1
    for evidence_mode in ("missing", "directory", "unreadable", "malformed"):
        failures.extend(run_evidence_case(evidence_mode))

    def process_is_gone(pid: int) -> bool:
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            time.sleep(0.01)
        return False

    def run_timeout_case(mode: str, expected: str) -> list[str]:
        with tempfile.TemporaryDirectory(prefix="semantic-proof-timeout-") as raw:
            repository, checker, manifest_path, _evidence, fake_lean, manifest = _materialize(raw)
            _write_manifest(manifest_path, manifest)
            marker = repository / "fake-lean.pid"
            started = time.monotonic()
            case_failures = _expect(
                f"{mode} is bounded and diagnosed",
                checker,
                repository,
                Path(MANIFEST_LABEL),
                fake_lean,
                1,
                [expected],
                environment={
                    "FAKE_LEAN_MODE": mode,
                    "FAKE_LEAN_PID_MARKER": str(marker),
                },
            )
            elapsed = time.monotonic() - started
            if elapsed > HARNESS_TIMEOUT_SECONDS + 1.0:
                case_failures.append(f"{mode}: unbounded harness return after {elapsed:.3f}s")
            if not marker.is_file():
                case_failures.append(f"{mode}: fake Lean did not publish its PID")
            else:
                pid = int(marker.read_text(encoding="ascii"))
                if not process_is_gone(pid):
                    case_failures.append(f"{mode}: fake Lean PID {pid} remained alive")
            return case_failures

    groups += 1
    failures.extend(
        run_timeout_case(
            "timeout-version",
            f"PROOF_TOOL_TIMEOUT {MANIFEST_LABEL}#/tool/version",
        )
    )
    failures.extend(
        run_timeout_case(
            "timeout-execution",
            f"PROOF_EXECUTION_TIMEOUT {SOURCE_LABEL}#",
        )
    )

    run_group(
        [
            (
                ("non-JSON Lean output cannot precede a forged positive audit",),
                {
                    "fake_mode": "malformed-output-forged-positive",
                    "expected": f"PROOF_LEAN_OUTPUT_INVALID {SOURCE_LABEL}#",
                },
            ),
            (
                ("unexpected structured Lean output cannot precede a forged positive audit",),
                {
                    "fake_mode": "unexpected-output-forged-positive",
                    "expected": f"PROOF_LEAN_OUTPUT_INVALID {SOURCE_LABEL}#",
                },
            ),
        ]
    )

    run_group(
        [
            (
                ("an empty-axiom message cannot replace exact theorem-type observation",),
                {
                    "fake_mode": "axiom-only-positive",
                    "expected": (
                        f"PROOF_THEOREM_AUDIT_MISSING "
                        f"{MANIFEST_LABEL}#/expectedStatement"
                    ),
                },
            )
        ]
    )

    # PF3 review-successor controls. These freeze the original-source command and
    # declaration boundary, cardinality of independent Lean audits, the exact
    # proof-support Evidence packet, and executing-runner identity.
    run_group(
        [
            (
                ("an unused source axiom is outside the bounded proof language",),
                {
                    "source_name": "unused-axiom.lean",
                    "expected": f"PROOF_SOURCE_BOUNDARY {SOURCE_LABEL}#",
                },
            ),
            (
                ("declaration modifiers cannot hide an unsafe definition",),
                {
                    "source_name": "modifier-unsafe.lean",
                    "expected": f"PROOF_SOURCE_BOUNDARY {SOURCE_LABEL}#",
                },
            ),
        ]
    )

    def run_source_command_case(source_name: str) -> list[str]:
        with tempfile.TemporaryDirectory(prefix="semantic-proof-command-") as raw:
            repository, checker, manifest_path, _evidence, fake_lean, manifest = (
                _materialize(raw, source_name)
            )
            _write_manifest(manifest_path, manifest)
            marker = repository / "proof-phase-executed"
            case_failures = _expect(
                f"{source_name} is rejected before proof execution",
                checker,
                repository,
                Path(MANIFEST_LABEL),
                fake_lean,
                1,
                [f"PROOF_SOURCE_BOUNDARY {SOURCE_LABEL}#"],
                environment={
                    "FAKE_LEAN_MODE": "source-command-forged-positive",
                    "FAKE_LEAN_EXECUTION_MARKER": str(marker),
                },
            )
            if marker.exists():
                case_failures.append(
                    f"{source_name}: source containing a command reached proof execution"
                )
            return case_failures

    groups += 1
    failures.extend(run_source_command_case("source-eval.lean"))
    failures.extend(run_source_command_case("source-print.lean"))

    groups += 1
    failures.extend(run_source_command_case("wrapped-source-eval.lean"))
    failures.extend(run_source_command_case("wrapped-source-print.lean"))

    run_group(
        [
            (
                ("a later axiom dependency contradicts an earlier empty audit",),
                {
                    "fake_mode": "axiom-positive-then-negative",
                    "expected": f"PROOF_AXIOM_AUDIT_INVALID {SOURCE_LABEL}#",
                },
            ),
            (
                ("duplicate empty-axiom audits are not one independent observation",),
                {
                    "fake_mode": "axiom-duplicate-positive",
                    "expected": f"PROOF_AXIOM_AUDIT_INVALID {SOURCE_LABEL}#",
                },
            ),
        ]
    )

    run_group(
        [
            (
                ("the fake positive path emits both independently named type audits",),
                {"fake_mode": "complete-positive"},
            ),
            (
                ("an actual-type-only fake cannot use a synthetic expected observation",),
                {
                    "fake_mode": "actual-type-only",
                    "expected": (
                        f"PROOF_THEOREM_AUDIT_MISSING "
                        f"{MANIFEST_LABEL}#/expectedStatement"
                    ),
                },
            ),
        ]
    )

    def run_proof_evidence_case(
        name: str,
        *,
        expected: str | None = None,
        mutate_evidence: Callable[[Any], Any] | None = None,
    ) -> list[str]:
        with tempfile.TemporaryDirectory(prefix="semantic-proof-support-") as raw:
            repository, checker, manifest_path, _placeholder, _fake, manifest = (
                _materialize(raw)
            )
            _write_manifest(manifest_path, manifest)
            evidence_path, evidence = _materialize_proof_evidence(
                repository, manifest_path, manifest
            )
            if mutate_evidence is not None:
                replacement = mutate_evidence(evidence)
                if replacement is not None:
                    evidence = replacement
                evidence_path.write_text(
                    json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            return _expect(
                name,
                checker,
                repository,
                Path(MANIFEST_LABEL),
                lean,
                1 if expected else 0,
                [expected] if expected else [],
                evidence=Path(PROOF_EVIDENCE_LABEL),
            )

    def replace_with(value: Any) -> Callable[[Any], Any]:
        return lambda _evidence: value

    groups += 1
    failures.extend(
        run_proof_evidence_case(
            "the materialized proof-local Evidence template is accepted"
        )
    )
    for name, replacement in (
        ("an empty object is not proof Evidence", {}),
        ("a scalar is not proof Evidence", "proof"),
    ):
        failures.extend(
            run_proof_evidence_case(
                name,
                expected=f"PROOF_EVIDENCE_SCHEMA {PROOF_EVIDENCE_LABEL}#",
                mutate_evidence=replace_with(replacement),
            )
        )

    def mutate_field(key: str, value: Any) -> Callable[[Any], None]:
        def mutate(evidence: dict[str, Any]) -> None:
            evidence[key] = value

        return mutate

    def realization_scope(evidence: dict[str, Any]) -> None:
        evidence["scope"] = "realization"
        evidence["realization"] = {
            "kind": "realization",
            "id": "stack-reference",
            "version": "0.2.0",
        }
        evidence["adapter"] = {"id": "stack-json-adapter", "version": "0.2.0"}

    def add_realization(evidence: dict[str, Any]) -> None:
        evidence["realization"] = {
            "kind": "realization",
            "id": "stack-reference",
            "version": "0.2.0",
        }

    def add_adapter(evidence: dict[str, Any]) -> None:
        evidence["adapter"] = {"id": "stack-json-adapter", "version": "0.2.0"}

    def wrong_claim(evidence: dict[str, Any]) -> None:
        evidence["claim"]["id"] = "another-claim"

    def wrong_specification(evidence: dict[str, Any]) -> None:
        evidence["specification"]["id"] = "another-specification"

    def add_profile(evidence: dict[str, Any]) -> None:
        evidence["applicability"]["profiles"] = [
            {
                "kind": "realizationProfile",
                "id": "stack-default",
                "version": "0.1.0",
            }
        ]

    semantic_evidence_cases = [
        (
            "proof Evidence identity is exact",
            mutate_field("id", "another-proof"),
            f"PROOF_EVIDENCE_IDENTITY {PROOF_EVIDENCE_LABEL}#/id",
        ),
        (
            "proof Evidence is specification-scoped",
            realization_scope,
            f"PROOF_EVIDENCE_SCOPE {PROOF_EVIDENCE_LABEL}#/scope",
        ),
        (
            "specification proof Evidence cannot carry a Realization",
            add_realization,
            f"PROOF_EVIDENCE_SCHEMA {PROOF_EVIDENCE_LABEL}#",
        ),
        (
            "specification proof Evidence cannot carry an adapter",
            add_adapter,
            f"PROOF_EVIDENCE_SCHEMA {PROOF_EVIDENCE_LABEL}#",
        ),
        (
            "proof Evidence links the pinned Claim",
            wrong_claim,
            f"PROOF_EVIDENCE_LINK {PROOF_EVIDENCE_LABEL}#/claim",
        ),
        (
            "proof Evidence links the pinned Specification",
            wrong_specification,
            f"PROOF_EVIDENCE_LINK {PROOF_EVIDENCE_LABEL}#/specification",
        ),
        (
            "proof Evidence has mechanism proof",
            mutate_field("mechanism", "assertion"),
            f"PROOF_EVIDENCE_MECHANISM {PROOF_EVIDENCE_LABEL}#/mechanism",
        ),
        (
            "proof Evidence records supporting completion",
            mutate_field("result", "challenges"),
            f"PROOF_EVIDENCE_RESULT {PROOF_EVIDENCE_LABEL}#/result",
        ),
        (
            "proof Evidence has no profile scope",
            add_profile,
            f"PROOF_EVIDENCE_SCOPE {PROOF_EVIDENCE_LABEL}#/applicability/profiles",
        ),
        (
            "proof Evidence review state is the accepted gate decision",
            mutate_field("reviewState", "pending"),
            f"PROOF_EVIDENCE_SEMANTICS {PROOF_EVIDENCE_LABEL}#/reviewState",
        ),
        (
            "proof Evidence method retains the bounded model wording",
            mutate_field("method", "the Stack Specification is proved"),
            f"PROOF_EVIDENCE_SEMANTICS {PROOF_EVIDENCE_LABEL}#/method",
        ),
        (
            "proof Evidence retains the exact local Lean kernel environment",
            mutate_field(
                "environment",
                {"execution": "remote", "kernel": "CompatibleLean 4.30.0"},
            ),
            f"PROOF_EVIDENCE_SEMANTICS {PROOF_EVIDENCE_LABEL}#/environment",
        ),
        (
            "proof Evidence assumptions cannot broaden model satisfaction",
            mutate_field(
                "assumptions",
                ["The Lean theorem proves every law of the Stack Specification."],
            ),
            f"PROOF_EVIDENCE_SEMANTICS {PROOF_EVIDENCE_LABEL}#/assumptions",
        ),
        (
            "proof Evidence exclusions retain no-realization and no-global-authority",
            mutate_field(
                "exclusions",
                ["This Evidence establishes conformance of every Stack Realization."],
            ),
            f"PROOF_EVIDENCE_SEMANTICS {PROOF_EVIDENCE_LABEL}#/exclusions",
        ),
    ]
    groups += 1
    for name, mutation, expected in semantic_evidence_cases:
        failures.extend(
            run_proof_evidence_case(
                name,
                expected=expected,
                mutate_evidence=mutation,
            )
        )

    def mutate_nested(path: tuple[str, ...], value: Any) -> Callable[[Any], None]:
        def mutate(evidence: dict[str, Any]) -> None:
            current = evidence
            for part in path[:-1]:
                current = current[part]
            current[path[-1]] = value

        return mutate

    provenance_mutations: list[tuple[tuple[str, ...], Any]] = [
        (("manifest", "path"), "proofs/stack-pop-empty/other-manifest.json"),
        (("manifest", "sha256"), "0" * 64),
        (("runner", "path"), "scripts/other-proof-check.py"),
        (("runner", "sha256"), "0" * 64),
        (("inputs", "specification", "path"), "fixtures/records/other-spec.json"),
        (("inputs", "specification", "sha256"), "0" * 64),
        (("inputs", "claim", "path"), "fixtures/records/other-claim.json"),
        (("inputs", "claim", "sha256"), "0" * 64),
        (("inputs", "source", "path"), "proofs/stack-pop-empty/Other.lean"),
        (("inputs", "source", "sha256"), "0" * 64),
        (("tool", "name"), "CompatibleLean"),
        (("tool", "version"), "4.29.0"),
        (("tool", "commit"), "0" * 40),
        (("tool", "invocation"), ["$LEAN", "--json", "$GENERATED_SOURCE"]),
        (("result", "completed"), False),
        (("result", "outputSha256"), "0" * 64),
    ]
    groups += 1
    for path, value in provenance_mutations:
        pointer = "/provenance/" + "/".join(path)
        failures.extend(
            run_proof_evidence_case(
                f"proof Evidence provenance pins {pointer}",
                expected=(
                    f"PROOF_EVIDENCE_PROVENANCE "
                    f"{PROOF_EVIDENCE_LABEL}#{pointer}"
                ),
                mutate_evidence=mutate_nested(("provenance", *path), value),
            )
        )

    groups += 1
    with tempfile.TemporaryDirectory(prefix="semantic-proof-runner-") as raw:
        repository, checker, manifest_path, _evidence, _fake, manifest = _materialize(raw)
        _write_manifest(manifest_path, manifest)
        copied_checker = repository / "tools" / "copied-proof-check.py"
        _copy(checker, copied_checker)
        _copy(
            repository / "scripts" / "record_check.py",
            repository / "tools" / "record_check.py",
        )
        failures.extend(
            _expect(
                "a copied checker cannot attest the manifest's repository runner",
                copied_checker,
                repository,
                Path(MANIFEST_LABEL),
                lean,
                1,
                [f"PROOF_RUNNER_IDENTITY {MANIFEST_LABEL}#/runner/path"],
            )
        )
    return failures, groups


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lean",
        type=Path,
        help="explicit Lean executable; defaults to LEAN or PATH lookup",
    )
    arguments = parser.parse_args()
    configured = arguments.lean or (
        Path(os.environ["LEAN"]) if os.environ.get("LEAN") else None
    )
    if configured is None:
        discovered = shutil.which("lean")
        configured = Path(discovered) if discovered else None

    failures = check_fixture_inputs(configured)
    missing = []
    if not CHECKER.is_file():
        missing.append("future checker scripts/proof_check.py is absent")
    if not ACTUAL_PROOF.is_file():
        missing.append("future proof proofs/stack-pop-empty/StackPopEmpty.lean is absent")
    if not ACTUAL_MANIFEST.is_file():
        missing.append("future proof manifest proofs/stack-pop-empty/manifest.json is absent")
    if missing:
        failures.extend(missing)
        print("Proof fixture checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    if configured is None:
        failures.append(
            "future proof checker exists but no explicit Lean executable is available"
        )
        groups = 0
    else:
        product_failures, groups = check_product_contract(configured)
        failures.extend(product_failures)
    if failures:
        print("Proof fixture checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Proof fixture checks passed: {groups} contract groups.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
