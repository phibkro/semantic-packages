"""Explicit file boundary for the PSpec author journey."""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

from scripts import record_check

from .authoring import (
    PSPEC_TOML_V1,
    AuthoringDependency,
    author_specification,
)


_DIAGNOSTIC_FALLBACKS = {
    "AUTHOR_EXPECTED_SPECIFICATION": "source record kind must be specification",
    "SCHEMA_INVALID": "value does not satisfy the canonical record schema",
    "SCHEMA_MISSING_FIELD": "required field is missing",
    "SCHEMA_NONEMPTY_STRING": "value must be a nonempty string",
    "SCHEMA_UNKNOWN_FIELD": "field or value is not permitted by the canonical schema",
    "SCHEMA_UNKNOWN_KIND": "record kind is not supported",
}


class _DuplicateMember(ValueError):
    def __init__(self, member: str) -> None:
        super().__init__(member)
        self.member = member


class _NonstandardConstant(ValueError):
    pass


def _diagnostic(
    code: str,
    path: Path,
    message: str,
) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, os.fspath(path), "#", message)


def _print_diagnostics(diagnostics: Sequence[record_check.Diagnostic]) -> None:
    for diagnostic in diagnostics:
        message = diagnostic.message or _DIAGNOSTIC_FALLBACKS.get(
            diagnostic.code,
            "authoring failed at this value",
        )
        print(
            f"{diagnostic.code} {diagnostic.path}{diagnostic.pointer}: {message}",
            file=os.sys.stderr,
        )


def _read_source(path: Path) -> tuple[bytes | None, record_check.Diagnostic | None]:
    try:
        return path.read_bytes(), None
    except (OSError, ValueError) as error:
        detail = getattr(error, "strerror", None) or str(error)
        return None, _diagnostic(
            "AUTHOR_SOURCE_READ",
            path,
            f"cannot read source: {detail}",
        )


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateMember(key)
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise _NonstandardConstant(token)


def _load_dependency(
    path: Path,
) -> tuple[AuthoringDependency | None, record_check.Diagnostic | None]:
    try:
        raw = path.read_bytes()
    except (OSError, ValueError) as error:
        detail = getattr(error, "strerror", None) or str(error)
        return None, _diagnostic(
            "AUTHOR_DEPENDENCY_READ",
            path,
            f"cannot read dependency: {detail}",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        return None, _diagnostic(
            "AUTHOR_DEPENDENCY_UTF8",
            path,
            f"invalid UTF-8 at byte {error.start}",
        )
    try:
        document = json.loads(
            text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
        )
    except _DuplicateMember as error:
        return None, _diagnostic(
            "AUTHOR_DEPENDENCY_JSON",
            path,
            f"invalid JSON: duplicate object member {error.member}",
        )
    except _NonstandardConstant as error:
        return None, _diagnostic(
            "AUTHOR_DEPENDENCY_JSON",
            path,
            f"invalid JSON: non-standard constant {error}",
        )
    except (json.JSONDecodeError, RecursionError) as error:
        if isinstance(error, json.JSONDecodeError):
            detail = f"line {error.lineno} column {error.colno} (character {error.pos})"
        else:
            detail = "nesting exceeds parser limit"
        return None, _diagnostic(
            "AUTHOR_DEPENDENCY_JSON",
            path,
            f"invalid JSON: {detail}",
        )
    if isinstance(document, float) and not math.isfinite(document):
        return None, _diagnostic(
            "AUTHOR_DEPENDENCY_JSON",
            path,
            "invalid JSON: non-finite number",
        )
    return AuthoringDependency(os.fspath(path), document), None


def _write_atomically(
    path: Path,
    document: dict[str, Any],
) -> record_check.Diagnostic | None:
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
        return _diagnostic(
            "AUTHOR_OUTPUT_WRITE",
            path,
            f"cannot write output: {detail}",
        )
    return None


def run_author(source: Path, dependencies: Sequence[Path], output: Path) -> int:
    source_bytes, source_diagnostic = _read_source(source)
    if source_diagnostic is not None:
        _print_diagnostics((source_diagnostic,))
        return 1
    assert source_bytes is not None

    loaded_dependencies: list[AuthoringDependency] = []
    for dependency_path in dependencies:
        dependency, diagnostic = _load_dependency(dependency_path)
        if diagnostic is not None:
            _print_diagnostics((diagnostic,))
            return 1
        assert dependency is not None
        loaded_dependencies.append(dependency)

    observation = author_specification(
        source_bytes,
        format_token=PSPEC_TOML_V1,
        source_label=os.fspath(source),
        dependencies=tuple(loaded_dependencies),
    )
    if not observation.ok:
        _print_diagnostics(observation.diagnostics)
        return 1
    document = observation.document
    assert document is not None

    output_diagnostic = _write_atomically(output, document)
    if output_diagnostic is not None:
        _print_diagnostics((output_diagnostic,))
        return 1
    print(f"authored specification {document['id']}@{document['version']} -> {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m semantic_packages")
    commands = parser.add_subparsers(dest="command", required=True)
    author = commands.add_parser(
        "author",
        help="author one exact canonical Specification from explicit PSpec input",
    )
    author.add_argument("source", type=Path, help="explicit PSpec source path")
    author.add_argument(
        "--dependency",
        action="append",
        default=[],
        type=Path,
        help="explicit canonical JSON dependency path; repeat to preserve input order",
    )
    author.add_argument(
        "--output",
        required=True,
        type=Path,
        help="exact canonical JSON output path",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parser = build_parser()
    options = parser.parse_args(arguments)
    if options.command == "author":
        return run_author(options.source, options.dependency, options.output)
    parser.error(f"unsupported command: {options.command}")
    return 2
