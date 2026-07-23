"""Representation-neutral authoring of one canonical Specification document.

The strict JSON conformance control and explicit PSpec surface perform no filesystem,
manifest, registry, network, version, profile, or identity discovery. External
references are checked only against the finite dependency records supplied by the
caller.
"""

from __future__ import annotations

import json
import math
import re
import tomllib
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from typing import Any, Mapping

from scripts import record_check


CANONICAL_SPEC_JSON_V1 = "canonical-spec-json-v1"
PSPEC_TOML_V1 = "pspec-toml-v1"


@dataclass(frozen=True)
class AuthoringDependency:
    """One caller-supplied canonical context record and diagnostic label."""

    source_label: str
    document: Mapping[str, Any]


@dataclass(frozen=True)
class AuthoringObservation:
    """All-or-none authoring result with a detached document snapshot."""

    _document_text: str | None
    diagnostics: tuple[record_check.Diagnostic, ...]

    def __post_init__(self) -> None:
        if self._document_text is None and not self.diagnostics:
            raise ValueError("failed authoring observation requires diagnostics")
        if self._document_text is not None and self.diagnostics:
            raise ValueError("successful authoring observation cannot carry diagnostics")

    @property
    def ok(self) -> bool:
        return self._document_text is not None

    @property
    def document(self) -> dict[str, Any] | None:
        if self._document_text is None:
            return None
        return json.loads(self._document_text)


class _DuplicateMember(ValueError):
    def __init__(self, member: str) -> None:
        super().__init__(member)
        self.member = member


class _NonStandardConstant(ValueError):
    def __init__(self, token: str) -> None:
        super().__init__(token)
        self.token = token


class _InvalidDependencyValue(ValueError):
    pass


def _diagnostic(
    code: str,
    path: str,
    pointer: str = "#",
    message: str | None = None,
) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, path, pointer, message)


def _failure(
    diagnostics: list[record_check.Diagnostic] | tuple[record_check.Diagnostic, ...],
) -> AuthoringObservation:
    return AuthoringObservation(None, tuple(diagnostics))


def _success(document: dict[str, Any]) -> AuthoringObservation:
    snapshot = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
    return AuthoringObservation(snapshot, ())


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateMember(key)
        result[key] = value
    return result


def _reject_nonstandard_constant(token: str) -> None:
    raise _NonStandardConstant(token)


def _decode_json_source(
    source: bytes,
    source_label: str,
) -> tuple[Any | None, list[record_check.Diagnostic]]:
    if not isinstance(source, bytes):
        return None, [
            _diagnostic(
                "AUTHOR_SOURCE_TYPE",
                source_label,
                message="source must be bytes",
            )
        ]
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as error:
        return None, [
            _diagnostic(
                "AUTHOR_INVALID_UTF8",
                source_label,
                message=f"invalid UTF-8 at byte {error.start}",
            )
        ]

    try:
        document = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_nonstandard_constant,
        )
    except _DuplicateMember as error:
        return None, [
            _diagnostic(
                "AUTHOR_DUPLICATE_MEMBER",
                source_label,
                message=f"duplicate object member: {error.member}",
            )
        ]
    except _NonStandardConstant as error:
        return None, [
            _diagnostic(
                "AUTHOR_INVALID_JSON",
                source_label,
                message=f"non-standard JSON constant: {error.token}",
            )
        ]
    except json.JSONDecodeError as error:
        return None, [
            _diagnostic(
                "AUTHOR_INVALID_JSON",
                source_label,
                message=(
                    f"invalid JSON at line {error.lineno} column {error.colno} "
                    f"(character {error.pos})"
                ),
            )
        ]
    except RecursionError:
        return None, [
            _diagnostic(
                "AUTHOR_INVALID_JSON",
                source_label,
                message="JSON nesting exceeds parser limit",
            )
        ]
    return document, []


def _toml_error_location(text: str, error: tomllib.TOMLDecodeError) -> tuple[int, int]:
    line = getattr(error, "lineno", None)
    column = getattr(error, "colno", None)
    if isinstance(line, int) and isinstance(column, int):
        return line, column

    match = re.search(r"\(at line (\d+), column (\d+)\)$", str(error))
    if match is not None:
        return int(match.group(1)), int(match.group(2))

    lines = text.split("\n")
    return len(lines), len(lines[-1]) + 1


def _json_pointer(parts: tuple[str | int, ...]) -> str:
    if not parts:
        return "#"
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "#/" + "/".join(encoded)


def _first_non_json_pointer(
    value: Any,
    parts: tuple[str | int, ...] = (),
) -> str | None:
    if value is None or isinstance(value, (str, bool, int)):
        return None
    if isinstance(value, float):
        return None if math.isfinite(value) else _json_pointer(parts)
    if isinstance(value, dict):
        for key, item in value.items():
            pointer = _first_non_json_pointer(item, (*parts, key))
            if pointer is not None:
                return pointer
        return None
    if isinstance(value, list):
        for index, item in enumerate(value):
            pointer = _first_non_json_pointer(item, (*parts, index))
            if pointer is not None:
                return pointer
        return None
    return _json_pointer(parts)


def _decode_pspec_source(
    source: bytes,
    source_label: str,
) -> tuple[Any | None, list[record_check.Diagnostic]]:
    if not isinstance(source, bytes):
        return None, [
            _diagnostic(
                "AUTHOR_SOURCE_TYPE",
                source_label,
                message="source must be bytes",
            )
        ]
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as error:
        return None, [
            _diagnostic(
                "AUTHOR_INVALID_UTF8",
                source_label,
                message=f"invalid UTF-8 at byte {error.start}",
            )
        ]

    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        line, column = _toml_error_location(text, error)
        detail = str(error).split(" (at", 1)[0]
        if "overwrite" in detail.casefold():
            message = f"duplicate TOML key at line {line} column {column}"
        else:
            message = f"invalid TOML at line {line} column {column}: {detail}"
        return None, [
            _diagnostic("AUTHOR_INVALID_TOML", source_label, message=message)
        ]
    except ValueError:
        return None, [
            _diagnostic(
                "AUTHOR_INVALID_TOML",
                source_label,
                message="numeric conversion exceeds parser limit",
            )
        ]
    except RecursionError:
        return None, [
            _diagnostic(
                "AUTHOR_INVALID_TOML",
                source_label,
                message="TOML nesting exceeds parser limit",
            )
        ]

    pointer = _first_non_json_pointer(document)
    if pointer is not None:
        return None, [
            _diagnostic(
                "AUTHOR_TOML_NON_JSON",
                source_label,
                pointer,
                "PSpec values must belong to the JSON data model",
            )
        ]
    return document, []


def _remap_diagnostics(
    diagnostics: list[record_check.Diagnostic],
    labels: dict[str, str],
) -> list[record_check.Diagnostic]:
    remapped = [
        record_check.Diagnostic(
            diagnostic.code,
            labels[diagnostic.path],
            diagnostic.pointer,
            diagnostic.message,
        )
        for diagnostic in diagnostics
    ]
    remapped.sort(key=record_check.Diagnostic.sort_key)
    return remapped


def _validate_authored_source(
    schemas: record_check.SchemaRegistry,
    source_label: str,
    document: Any,
) -> record_check.Diagnostic | None:
    diagnostic = record_check.validate_record(schemas, source_label, document)
    if (
        diagnostic is not None
        and diagnostic.code == "SCHEMA_INVALID"
        and isinstance(document, dict)
        and isinstance(document.get("laws"), list)
    ):
        for index, law in enumerate(document["laws"]):
            if isinstance(law, dict) and law.get("statement") == "":
                return _diagnostic(
                    "SCHEMA_NONEMPTY_STRING",
                    source_label,
                    f"#/laws/{index}/statement",
                )
    return diagnostic


def _snapshot_json_value(value: Any, active: set[int] | None = None) -> Any:
    """Detach a finite JSON value without relying on object pickle protocols."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise _InvalidDependencyValue
        return value

    if active is None:
        active = set()
    if isinstance(value, MappingABC):
        identity = id(value)
        if identity in active:
            raise _InvalidDependencyValue
        active.add(identity)
        try:
            result: dict[str, Any] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise _InvalidDependencyValue
                result[key] = _snapshot_json_value(item, active)
            return result
        finally:
            active.remove(identity)
    if isinstance(value, (list, tuple)):
        identity = id(value)
        if identity in active:
            raise _InvalidDependencyValue
        active.add(identity)
        try:
            return [_snapshot_json_value(item, active) for item in value]
        finally:
            active.remove(identity)
    raise _InvalidDependencyValue


def author_specification(
    source: bytes,
    format_token: str,
    source_label: str,
    dependencies: tuple[AuthoringDependency, ...],
) -> AuthoringObservation:
    """Decode and validate one Specification relative to explicit dependencies.

    Phases are strict: format dispatch, raw decode, source/dependency schema checks,
    then isolated graph links.  Any failure returns diagnostics and no document.
    """

    if not isinstance(source_label, str):
        return _failure(
            [
                _diagnostic(
                    "AUTHOR_SOURCE_LABEL_TYPE",
                    "<source>",
                    "#/sourceLabel",
                    "source label must be a string",
                )
            ]
        )

    if format_token == CANONICAL_SPEC_JSON_V1:
        decoder = _decode_json_source
    elif format_token == PSPEC_TOML_V1:
        decoder = _decode_pspec_source
    else:
        return _failure(
            [_diagnostic("AUTHOR_FORMAT_UNSUPPORTED", source_label)]
        )

    document, raw_diagnostics = decoder(source, source_label)
    if raw_diagnostics:
        return _failure(raw_diagnostics)

    schemas = record_check.SchemaRegistry()
    source_diagnostic = _validate_authored_source(schemas, source_label, document)
    if source_diagnostic is not None:
        return _failure([source_diagnostic])
    assert isinstance(document, dict), "schema-valid record is an object"
    if document["kind"] != "specification":
        return _failure(
            [_diagnostic("AUTHOR_EXPECTED_SPECIFICATION", source_label, "#/kind")]
        )

    if not isinstance(dependencies, tuple):
        return _failure(
            [
                _diagnostic(
                    "AUTHOR_DEPENDENCIES_TYPE",
                    source_label,
                    "#/dependencies",
                    "dependencies must be a tuple",
                )
            ]
        )

    dependency_snapshots: list[tuple[str, dict[str, Any]]] = []
    dependency_schema_diagnostics: list[record_check.Diagnostic] = []
    for index, dependency in enumerate(dependencies):
        if not isinstance(dependency, AuthoringDependency):
            return _failure(
                [
                    _diagnostic(
                        "AUTHOR_DEPENDENCY_TYPE",
                        source_label,
                        f"#/dependencies/{index}",
                        "dependency must be AuthoringDependency",
                    )
                ]
            )
        if not isinstance(dependency.source_label, str):
            return _failure(
                [
                    _diagnostic(
                        "AUTHOR_DEPENDENCY_LABEL_TYPE",
                        source_label,
                        f"#/dependencies/{index}/sourceLabel",
                        "dependency source label must be a string",
                    )
                ]
            )
        if not isinstance(dependency.document, MappingABC):
            return _failure(
                [
                    _diagnostic(
                        "AUTHOR_DEPENDENCY_DOCUMENT_TYPE",
                        dependency.source_label,
                        message="dependency document must be a mapping",
                    )
                ]
            )
        try:
            dependency_document = _snapshot_json_value(dependency.document)
        except Exception:
            return _failure(
                [
                    _diagnostic(
                        "AUTHOR_DEPENDENCY_SNAPSHOT",
                        dependency.source_label,
                        message="dependency document must be a finite JSON value",
                    )
                ]
            )
        assert isinstance(dependency_document, dict)
        diagnostic = record_check.validate_record(
            schemas,
            dependency.source_label,
            dependency_document,
        )
        if diagnostic is not None:
            dependency_schema_diagnostics.append(diagnostic)
            continue
        assert isinstance(
            dependency_document, dict
        ), "schema-valid dependency is an object"
        dependency_snapshots.append(
            (dependency.source_label, dependency_document)
        )
    if dependency_schema_diagnostics:
        return _failure(dependency_schema_diagnostics)

    records: dict[str, dict[str, Any]] = {"@source/000000": document}
    labels = {"@source/000000": source_label}
    for index, (label, dependency_document) in enumerate(dependency_snapshots):
        internal_path = f"@dependency/{index:06d}"
        records[internal_path] = dependency_document
        labels[internal_path] = label

    link_diagnostics = record_check.check_graph(records)
    if link_diagnostics:
        return _failure(_remap_diagnostics(link_diagnostics, labels))
    return _success(document)
