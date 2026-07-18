"""Deterministic observation of a finite set of labeled local record roots.

This module is intentionally an internal, policy-free boundary.  It discovers
and schema-validates local JSON records without following symlinks, executing
artifacts, checking graph links, or assigning publication/registration roles.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from scripts import record_check


Address = tuple[str, str, str]


@dataclass(frozen=True)
class _SourceRoot:
    """A physical source root and its logical provenance prefix."""

    label: str
    path: Path


@dataclass(frozen=True)
class _SourceRecord:
    """One schema-valid record captured from the finite source set."""

    address: Address
    path: str
    sha256: str
    _document_text: str

    @property
    def document(self) -> dict:
        """Return an isolated view of the captured document snapshot."""

        return json.loads(self._document_text)


@dataclass(frozen=True)
class _SourceObservation:
    """Stable records and input/schema diagnostics from one observation."""

    records: tuple[_SourceRecord, ...]
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


@dataclass(frozen=True)
class _Candidate:
    physical_path: str
    logical_path: str


def _normalize_physical_path(path: Path) -> str:
    """Apply ADR 0007's lexical absolute-path normalization."""

    normalized = os.path.abspath(os.fspath(path))
    if normalized.startswith("/"):
        normalized = "/" + normalized.lstrip("/")
    return normalized


def _logical_path(label: str, relative: str = "") -> str:
    parts = [part for part in (label, relative) if part and part != "."]
    return PurePosixPath(*parts).as_posix() if parts else "."


def _diagnostic(
    code: str, path: str, message: str | None = None
) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, path, "#", message)


def _ancestor_diagnostic(
    base: str, root_label: str
) -> record_check.Diagnostic | None:
    """Classify strict ancestors without touching the requested root."""

    parts = PurePosixPath(base).parts
    current = "/"
    for part in parts[1:-1]:
        current = os.path.join(current, part)
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return _diagnostic(
                "INPUT_NOT_FOUND", root_label, f"no such file: {base}"
            )
        except OSError as error:
            return _diagnostic("INPUT_READ_ERROR", root_label, str(error))
        if stat.S_ISLNK(info.st_mode):
            return _diagnostic("INPUT_SYMLINK", root_label)
    return None


def _discover_root(
    root: _SourceRoot,
) -> tuple[list[_Candidate], list[record_check.Diagnostic], bool]:
    base = _normalize_physical_path(root.path)
    root_label = _logical_path(root.label)
    diagnostics: list[record_check.Diagnostic] = []
    candidates: list[_Candidate] = []

    ancestor_diagnostic = _ancestor_diagnostic(base, root_label)
    if ancestor_diagnostic is not None:
        return [], [ancestor_diagnostic], False

    try:
        root_info = os.lstat(base)
    except FileNotFoundError:
        return (
            [],
            [_diagnostic("INPUT_NOT_FOUND", root_label, f"no such file: {base}")],
            False,
        )
    except OSError as error:
        return [], [_diagnostic("INPUT_READ_ERROR", root_label, str(error))], False

    if stat.S_ISLNK(root_info.st_mode):
        return [], [_diagnostic("INPUT_SYMLINK", root_label)], False
    if stat.S_ISREG(root_info.st_mode):
        if base.endswith(".json"):
            return [_Candidate(base, root_label)], [], False
        return [], [_diagnostic("INPUT_NON_JSON", root_label)], False
    if not stat.S_ISDIR(root_info.st_mode):
        return (
            [],
            [
                _diagnostic(
                    "INPUT_UNSUPPORTED_TYPE",
                    root_label,
                    f"not a regular file or directory: {base}",
                )
            ],
            False,
        )

    def walk(directory: str, relative_directory: str) -> None:
        try:
            with os.scandir(directory) as entries:
                ordered = sorted(entries, key=lambda entry: entry.name)
        except OSError as error:
            diagnostics.append(
                _diagnostic(
                    "INPUT_READ_ERROR",
                    _logical_path(root.label, relative_directory),
                    str(error),
                )
            )
            return

        for entry in ordered:
            relative = PurePosixPath(relative_directory, entry.name).as_posix()
            physical = os.path.join(directory, entry.name)
            logical = _logical_path(root.label, relative)
            try:
                is_symlink = entry.is_symlink()
                is_directory = not is_symlink and entry.is_dir(follow_symlinks=False)
                is_file = (
                    not is_symlink
                    and not is_directory
                    and entry.is_file(follow_symlinks=False)
                )
            except OSError as error:
                diagnostics.append(
                    _diagnostic("INPUT_READ_ERROR", logical, str(error))
                )
                continue

            if is_symlink:
                diagnostics.append(_diagnostic("INPUT_SYMLINK", logical))
            elif is_directory:
                walk(physical, relative)
            elif is_file and entry.name.endswith(".json"):
                candidates.append(_Candidate(physical, logical))

    walk(base, "")
    return candidates, diagnostics, True


def _deduplicate_candidates(
    candidates: list[_Candidate],
) -> tuple[list[_Candidate], list[record_check.Diagnostic]]:
    """Collapse physical aliases, then diagnose logical-path collisions."""

    diagnostics: list[record_check.Diagnostic] = []
    by_physical: dict[str, set[str]] = {}
    for candidate in candidates:
        by_physical.setdefault(candidate.physical_path, set()).add(
            candidate.logical_path
        )

    physical_winners: list[_Candidate] = []
    for physical_path in sorted(by_physical):
        logical_paths = sorted(by_physical[physical_path])
        physical_winners.append(_Candidate(physical_path, logical_paths[0]))
        diagnostics.extend(
            _diagnostic("INPUT_SOURCE_ALIAS", logical_path)
            for logical_path in logical_paths[1:]
        )

    by_logical: dict[str, list[_Candidate]] = {}
    for candidate in physical_winners:
        by_logical.setdefault(candidate.logical_path, []).append(candidate)

    winners: list[_Candidate] = []
    for logical_path in sorted(by_logical):
        colliding = sorted(
            by_logical[logical_path], key=lambda candidate: candidate.physical_path
        )
        winners.append(colliding[0])
        if len(colliding) > 1:
            diagnostics.append(
                _diagnostic("INPUT_LOGICAL_PATH_COLLISION", logical_path)
            )
    return winners, diagnostics


def _observe_finite_source(
    roots: tuple[_SourceRoot, ...],
) -> _SourceObservation:
    """Capture schema-valid JSON records from labeled, no-follow roots."""

    if not roots:
        return _SourceObservation((), (_diagnostic("INPUT_EMPTY_SOURCE_SET", "."),))

    schemas = record_check.SchemaRegistry()
    diagnostics: list[record_check.Diagnostic] = [
        record_check.Diagnostic("SCHEMA_METASCHEMA_ERROR", "#", "#", error)
        for error in schemas.metaschema_errors
    ]
    candidates: list[_Candidate] = []
    directory_labels: list[str] = []

    unique_roots = {
        (root.label, _normalize_physical_path(root.path)): _SourceRoot(
            root.label, Path(_normalize_physical_path(root.path))
        )
        for root in roots
    }
    for root in sorted(
        unique_roots.values(),
        key=lambda item: (_normalize_physical_path(item.path), item.label),
    ):
        discovered, root_diagnostics, is_directory = _discover_root(root)
        candidates.extend(discovered)
        diagnostics.extend(root_diagnostics)
        if is_directory:
            directory_labels.append(_logical_path(root.label))

    candidates, alias_diagnostics = _deduplicate_candidates(candidates)
    diagnostics.extend(alias_diagnostics)
    if not candidates and not diagnostics:
        diagnostics.append(
            _diagnostic("INPUT_EMPTY_SOURCE_SET", min(directory_labels))
        )

    records: list[_SourceRecord] = []
    for candidate in candidates:
        path = Path(candidate.physical_path)
        try:
            with path.open("rb") as stream:
                raw = stream.read()
            text = raw.decode("utf-8")
        except (OSError, UnicodeError) as error:
            diagnostics.append(
                _diagnostic("INPUT_READ_ERROR", candidate.logical_path, str(error))
            )
            continue
        try:
            document = json.loads(text)
        except json.JSONDecodeError as error:
            diagnostics.append(
                _diagnostic("INPUT_INVALID_JSON", candidate.logical_path, str(error))
            )
            continue

        schema_diagnostic = record_check.validate_record(
            schemas, candidate.logical_path, document
        )
        if schema_diagnostic is not None:
            diagnostics.append(schema_diagnostic)
            continue
        records.append(
            _SourceRecord(
                address=record_check.address_of(document),
                path=candidate.logical_path,
                sha256=hashlib.sha256(raw).hexdigest(),
                _document_text=text,
            )
        )

    records.sort(key=lambda record: (record.path, record.address))
    diagnostics.sort(key=record_check.Diagnostic.sort_key)
    return _SourceObservation(tuple(records), tuple(diagnostics))
