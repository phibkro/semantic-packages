"""Explicit file boundary for proposal-local refinement inspection."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Sequence

from scripts import record_check

from .author_command import run_author
from .refinement import ProposalProblem, inspect_proposal, validate_proposal_shape
from .resource_algebra import run_resource_inspection


class _DuplicateMember(ValueError):
    def __init__(self, member: str) -> None:
        super().__init__(member)
        self.member = member


class _NonstandardConstant(ValueError):
    pass


def _diagnostic(code: str, path: Path, pointer: str, message: str) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, os.fspath(path), pointer, message)


def _print(diagnostic: record_check.Diagnostic) -> None:
    message = diagnostic.message or "value does not satisfy the canonical record schema"
    print(f"{diagnostic.code} {diagnostic.path}{diagnostic.pointer}: {message}", file=os.sys.stderr)


def _read_proposal(path: Path) -> tuple[dict[str, Any] | None, record_check.Diagnostic | None]:
    try:
        raw = path.read_bytes()
    except (OSError, ValueError) as error:
        detail = getattr(error, "strerror", None) or str(error)
        return None, _diagnostic("REFINEMENT_PROPOSAL_READ", path, "#", f"cannot read proposal: {detail}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        return None, _diagnostic("REFINEMENT_PROPOSAL_UTF8", path, "#", f"invalid UTF-8 at byte {error.start}")
    try:
        proposal = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        detail = str(error)
        if "overwrite" in detail.casefold() or "already" in detail.casefold():
            detail = "duplicate TOML key"
        return None, _diagnostic("REFINEMENT_PROPOSAL_TOML", path, "#", f"invalid TOML: {detail}")
    except (RecursionError, ValueError) as error:
        detail = "nesting exceeds parser limit" if isinstance(error, RecursionError) else "numeric conversion exceeds parser limit"
        return None, _diagnostic("REFINEMENT_PROPOSAL_TOML", path, "#", f"invalid TOML: {detail}")
    problem = validate_proposal_shape(proposal)
    if problem is not None:
        return None, _problem_diagnostic(path, problem)
    return proposal, None


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateMember(key)
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise _NonstandardConstant(token)


def _read_specification(path: Path) -> tuple[dict[str, Any] | None, bytes | None, record_check.Diagnostic | None]:
    try:
        raw = path.read_bytes()
    except (OSError, ValueError) as error:
        detail = getattr(error, "strerror", None) or str(error)
        return None, None, _diagnostic("REFINEMENT_SPEC_READ", path, "#", f"cannot read Specification: {detail}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        return None, None, _diagnostic("REFINEMENT_SPEC_UTF8", path, "#", f"invalid UTF-8 at byte {error.start}")
    try:
        document = json.loads(text, object_pairs_hook=_pairs_without_duplicates, parse_constant=_reject_constant)
    except _DuplicateMember as error:
        return None, None, _diagnostic("REFINEMENT_SPEC_JSON", path, "#", f"invalid JSON: duplicate object member {error.member}")
    except _NonstandardConstant as error:
        return None, None, _diagnostic("REFINEMENT_SPEC_JSON", path, "#", f"invalid JSON: non-standard constant {error}")
    except json.JSONDecodeError as error:
        detail = f"line {error.lineno} column {error.colno} (character {error.pos})"
        return None, None, _diagnostic("REFINEMENT_SPEC_JSON", path, "#", f"invalid JSON: {detail}")
    except RecursionError:
        return None, None, _diagnostic("REFINEMENT_SPEC_JSON", path, "#", "invalid JSON: nesting exceeds parser limit")
    except ValueError:
        return None, None, _diagnostic("REFINEMENT_SPEC_JSON", path, "#", "invalid JSON: numeric conversion exceeds parser limit")
    if isinstance(document, float) and not math.isfinite(document):
        return None, None, _diagnostic("REFINEMENT_SPEC_JSON", path, "#", "invalid JSON: non-finite number")
    schema_diagnostic = record_check.validate_record(record_check.SchemaRegistry(), os.fspath(path), document)
    if schema_diagnostic is not None:
        return None, None, schema_diagnostic
    return document, raw, None


def _problem_diagnostic(path: Path, problem: ProposalProblem) -> record_check.Diagnostic:
    return _diagnostic(problem.code, path, problem.pointer, problem.message)


def _check_binding(
    proposal_path: Path,
    specification_path: Path,
    side: str,
    expected: dict[str, Any],
    document: dict[str, Any],
    raw: bytes,
) -> record_check.Diagnostic | None:
    observed_address = {key: document.get(key) for key in ("kind", "id", "version")}
    expected_address = {key: expected[key] for key in ("kind", "id", "version")}
    if observed_address != expected_address:
        return _diagnostic(
            "REFINEMENT_SPEC_ADDRESS",
            specification_path,
            f"#/{side}",
            f"supplied address does not match proposal {proposal_path}",
        )
    observed_digest = hashlib.sha256(raw).hexdigest()
    if observed_digest != expected["rawSha256"]:
        return _diagnostic(
            "REFINEMENT_SPEC_DIGEST",
            specification_path,
            f"#/{side}/rawSha256",
            f"observed {observed_digest}",
        )
    return None


def _write_atomically(path: Path, document: dict[str, Any]) -> record_check.Diagnostic | None:
    rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except (OSError, ValueError) as error:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        detail = getattr(error, "strerror", None) or str(error)
        return _diagnostic("REFINEMENT_OUTPUT_WRITE", path, "#", f"cannot write output: {detail}")
    return None


def _aliases_input(output: Path, input_path: Path) -> bool:
    try:
        return os.path.samefile(output, input_path)
    except (OSError, ValueError):
        try:
            return output.resolve(strict=False) == input_path.resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            return os.path.abspath(output) == os.path.abspath(input_path)


def run_inspection(
    proposal_path: Path,
    predecessor_path: Path,
    successor_path: Path,
    output_path: Path,
) -> int:
    for input_path in (proposal_path, predecessor_path, successor_path):
        if _aliases_input(output_path, input_path):
            _print(
                _diagnostic(
                    "REFINEMENT_OUTPUT_WRITE",
                    output_path,
                    "#",
                    f"output aliases input {input_path}",
                )
            )
            return 1
    proposal, diagnostic = _read_proposal(proposal_path)
    if diagnostic is not None:
        _print(diagnostic)
        return 1
    assert proposal is not None

    predecessor, predecessor_raw, diagnostic = _read_specification(predecessor_path)
    if diagnostic is not None:
        _print(diagnostic)
        return 1
    successor, successor_raw, diagnostic = _read_specification(successor_path)
    if diagnostic is not None:
        _print(diagnostic)
        return 1
    assert predecessor is not None and predecessor_raw is not None
    assert successor is not None and successor_raw is not None

    for side, path, document, raw in (
        ("predecessor", predecessor_path, predecessor, predecessor_raw),
        ("successor", successor_path, successor, successor_raw),
    ):
        diagnostic = _check_binding(proposal_path, path, side, proposal[side], document, raw)
        if diagnostic is not None:
            _print(diagnostic)
            return 1

    report, problem = inspect_proposal(proposal, predecessor, successor)
    if problem is not None:
        _print(_problem_diagnostic(proposal_path, problem))
        return 1
    assert report is not None
    diagnostic = _write_atomically(output_path, report)
    if diagnostic is not None:
        _print(diagnostic)
        return 1
    relations = [item["documentRelation"] for item in report["mappings"]]
    unchanged = relations.count("document-unchanged")
    changed = relations.count("document-changed")
    print(
        f"inspected refinement {proposal['id']}: {unchanged} unchanged, {changed} changed, "
        f"{len(report['additions'])} additions, {len(report['removals'])} removals; "
        f"semantic refinement unestablished -> {output_path}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m semantic_packages")
    commands = parser.add_subparsers(dest="command", required=True)
    author = commands.add_parser("author", help="author one exact canonical Specification from explicit PSpec input")
    author.add_argument("source", type=Path, help="explicit PSpec source path")
    author.add_argument("--dependency", action="append", default=[], type=Path, help="explicit canonical JSON dependency path; repeat to preserve input order")
    author.add_argument("--output", required=True, type=Path, help="exact canonical JSON output path")

    refinement = commands.add_parser("refinement", help="inspect one explicit exact cross-version proposal")
    refinement_commands = refinement.add_subparsers(dest="refinement_command", required=True)
    inspect = refinement_commands.add_parser("inspect", help="inspect explicit declaration dispositions without a semantic verdict")
    inspect.add_argument("proposal", type=Path, help="explicit UTF-8 TOML proposal path")
    inspect.add_argument("--predecessor", required=True, type=Path, help="exact predecessor Specification path")
    inspect.add_argument("--successor", required=True, type=Path, help="exact successor Specification path")
    inspect.add_argument("--output", required=True, type=Path, help="inspection report output path")

    resource = commands.add_parser("resource", help="inspect one bounded authored resource algebra")
    resource_commands = resource.add_subparsers(dest="resource_command", required=True)
    resource_inspect = resource_commands.add_parser(
        "inspect", help="inspect one finite resource composition without a satisfaction verdict"
    )
    resource_inspect.add_argument("source", type=Path, help="explicit UTF-8 PSpec source path")
    resource_inspect.add_argument(
        "--dependency",
        action="append",
        default=[],
        type=Path,
        help="explicit canonical JSON dependency path; repeat to preserve input order",
    )
    resource_inspect.add_argument("--resource", required=True, help="exact local resource declaration ID")
    resource_inspect.add_argument("--output", required=True, type=Path, help="inspection report output path")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parser = build_parser()
    options = parser.parse_args(arguments)
    if options.command == "author":
        return run_author(options.source, options.dependency, options.output)
    if options.command == "refinement" and options.refinement_command == "inspect":
        return run_inspection(options.proposal, options.predecessor, options.successor, options.output)
    if options.command == "resource" and options.resource_command == "inspect":
        return run_resource_inspection(
            options.source,
            tuple(options.dependency),
            options.resource,
            options.output,
        )
    parser.error("unsupported command")
    return 2
