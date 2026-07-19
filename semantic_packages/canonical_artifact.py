"""Read-only inspection of one exact canonical JSON artifact.

This module authenticates bytes and structure only. It never executes an artifact,
discovers defaults, or decides which digest is authoritative for a product. Actor-facing
wrappers own those exact inputs.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry
from referencing.exceptions import NoSuchResource, Unresolvable

from scripts import record_check


_MAX_INPUT_BYTES = 4 * 1024 * 1024
_MAX_NESTING_DEPTH = 128


class _DuplicateMember(ValueError):
    def __init__(self, member: str) -> None:
        super().__init__(member)
        self.member = member


class _NonstandardConstant(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactObservation:
    """One detached authenticated document or fail-closed diagnostics."""

    label: str
    document: Any | None
    canonical_sha256: str | None
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def _diagnostic(
    code: str, path: Path, message: str | None = None, *, pointer: str = "#"
) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, os.fspath(path), pointer, message)


def _lexical_source_error(path: Path) -> record_check.Diagnostic | None:
    raw_parts = path.parts
    if ".." in raw_parts:
        return _diagnostic(
            "INPUT_UNSUPPORTED_TYPE", path, "parent-directory traversal is not supported"
        )

    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    try:
        mode = os.lstat(current).st_mode
    except (OSError, ValueError) as error:
        return _diagnostic("INPUT_READ_ERROR", path, str(error))
    for part in absolute.parts[1:]:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            return _diagnostic("INPUT_NOT_FOUND", path)
        except (OSError, ValueError) as error:
            return _diagnostic("INPUT_READ_ERROR", path, str(error))
        if stat.S_ISLNK(mode):
            return _diagnostic("INPUT_SYMLINK", path)

    if not stat.S_ISREG(mode):
        return _diagnostic("INPUT_UNSUPPORTED_TYPE", path)
    return None


def _read_regular_file(path: Path) -> tuple[str | None, record_check.Diagnostic | None]:
    if diagnostic := _lexical_source_error(path):
        return None, diagnostic

    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return None, _diagnostic("INPUT_NOT_FOUND", path)
    except OSError as error:
        return None, _diagnostic("INPUT_READ_ERROR", path, str(error))

    try:
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            return None, _diagnostic("INPUT_UNSUPPORTED_TYPE", path)
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65536, _MAX_INPUT_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > _MAX_INPUT_BYTES:
                return None, _diagnostic(
                    "INPUT_TOO_LARGE", path, f"input exceeds {_MAX_INPUT_BYTES} bytes"
                )
        try:
            return b"".join(chunks).decode("utf-8"), None
        except UnicodeDecodeError as error:
            return None, _diagnostic("INPUT_INVALID_UTF8", path, str(error))
    except OSError as error:
        return None, _diagnostic("INPUT_READ_ERROR", path, str(error))
    finally:
        os.close(descriptor)


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise _DuplicateMember(key)
        document[key] = value
    return document


def _parse_json(
    text: str, path: Path
) -> tuple[Any | None, record_check.Diagnostic | None]:
    def reject_constant(token: str) -> None:
        raise _NonstandardConstant(token)

    try:
        document = json.loads(
            text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=reject_constant,
        )
    except _DuplicateMember as error:
        return None, _diagnostic(
            "ARTIFACT_DUPLICATE_MEMBER",
            path,
            f"duplicate JSON object member {error.member!r}",
        )
    except _NonstandardConstant:
        return None, _diagnostic(
            "INPUT_INVALID_JSON", path, "nonstandard numeric constant"
        )
    except RecursionError:
        return None, _diagnostic(
            "ARTIFACT_NESTING_LIMIT",
            path,
            f"JSON nesting exceeds {_MAX_NESTING_DEPTH}",
        )
    except (json.JSONDecodeError, ValueError) as error:
        return None, _diagnostic("INPUT_INVALID_JSON", path, str(error))

    stack: list[tuple[Any, int]] = [(document, 0)]
    while stack:
        value, depth = stack.pop()
        if depth > _MAX_NESTING_DEPTH:
            return None, _diagnostic(
                "ARTIFACT_NESTING_LIMIT",
                path,
                f"JSON nesting exceeds {_MAX_NESTING_DEPTH}",
            )
        if isinstance(value, dict):
            stack.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            stack.extend((item, depth + 1) for item in value)
    return document, None


def _pointer(parts: Any) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "#" if not encoded else "/" + "/".join(encoded)


def _offline_registry() -> Registry:
    def deny(uri: str):
        raise NoSuchResource(ref=uri)

    return Registry(retrieve=deny)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _failure(label: str, diagnostic: record_check.Diagnostic) -> ArtifactObservation:
    return ArtifactObservation(label, None, None, (diagnostic,))


def inspect_json_artifact(
    path: Path,
    *,
    schema_path: Path,
    expected_canonical_sha256: str,
    label: str,
) -> ArtifactObservation:
    """Inspect one explicitly authorized artifact without defaults or execution."""

    path = Path(path)
    schema_path = Path(schema_path)
    if not isinstance(label, str) or not label:
        raise ValueError("label must be a nonempty string")
    if (
        not isinstance(expected_canonical_sha256, str)
        or len(expected_canonical_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_canonical_sha256)
    ):
        raise ValueError("expected canonical SHA-256 must be 64 lowercase hexadecimal characters")

    artifact_text, diagnostic = _read_regular_file(path)
    if diagnostic is not None:
        return _failure(label, diagnostic)
    assert artifact_text is not None

    schema_text, diagnostic = _read_regular_file(schema_path)
    if diagnostic is not None:
        return _failure(label, diagnostic)
    assert schema_text is not None

    document, diagnostic = _parse_json(artifact_text, path)
    if diagnostic is not None:
        return _failure(label, diagnostic)
    schema, diagnostic = _parse_json(schema_text, schema_path)
    if diagnostic is not None:
        return _failure(label, diagnostic)

    try:
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, registry=_offline_registry())
        errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    except (SchemaError, TypeError, Unresolvable) as error:
        message = error.message if isinstance(error, SchemaError) else str(error)
        return _failure(
            label,
            _diagnostic("ARTIFACT_SCHEMA_CONTRACT_ERROR", schema_path, message),
        )

    if errors:
        error = errors[0]
        return _failure(
            label,
            _diagnostic(
                "ARTIFACT_SCHEMA_INVALID",
                path,
                f"schema rule {error.validator!r} failed",
                pointer=_pointer(error.absolute_path),
            ),
        )

    canonical = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    observed_sha256 = hashlib.sha256(canonical).hexdigest()
    if observed_sha256 != expected_canonical_sha256:
        return _failure(
            label,
            _diagnostic(
                "ARTIFACT_CANONICAL_DIGEST_MISMATCH",
                path,
                f"canonical SHA-256 {observed_sha256}, expected {expected_canonical_sha256}",
            ),
        )

    return ArtifactObservation(label, _freeze(document), observed_sha256, ())
