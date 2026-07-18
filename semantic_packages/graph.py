"""Manifest-governed inspection of the finite Stack product graph.

The supplied manifest owns curated membership, source assignment, raw-byte
digest, and explanatory role.  Canonical record bytes retain semantic identity
and content.  Inspection validates and snapshots those records without running
proofs, adapters, campaigns, build instructions, or policy resolution.
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import jsonschema

from scripts import record_check
from semantic_packages import _finite_source


Address = tuple[str, str, str]
_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "registry-manifest.schema.json"
)
_MANIFEST_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
_MANIFEST_VALIDATOR = jsonschema.Draft202012Validator(_MANIFEST_SCHEMA)
DEFAULT_STACK_MANIFEST = (
    Path(__file__).resolve().parents[1] / "registry" / "stack" / "manifest.json"
)


@dataclass(frozen=True)
class GraphRecord:
    """One canonical record captured from a successful manifest source."""

    address: Address
    path: str
    sha256: str
    role: str | None
    source: str
    _document_text: str

    @property
    def document(self) -> dict[str, Any]:
        """Return an isolated view of the captured document snapshot."""

        return json.loads(self._document_text)


@dataclass(frozen=True)
class GraphObservation:
    """Deterministic records and diagnostics from one uncached inspection."""

    records: tuple[GraphRecord, ...]
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


@dataclass(frozen=True)
class _Source:
    source_id: str
    root: str
    roles: frozenset[str]


@dataclass(frozen=True)
class _Member:
    source: str
    address: Address
    sha256: str
    role: str


@dataclass(frozen=True)
class _ManifestProjection:
    """Manifest-only snapshot used by legacy Stack actor views."""

    sources: tuple[_Source, ...]
    members: tuple[_Member, ...]
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def _diagnostic(
    code: str,
    path: str,
    pointer: str = "#",
    message: str | None = None,
) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, path, pointer, message)


def _normalized_absolute(path: Path) -> str:
    normalized = os.path.abspath(os.fspath(path))
    if normalized.startswith("/"):
        normalized = "/" + normalized.lstrip("/")
    return normalized


def _load_manifest(
    manifest_path: Path,
) -> tuple[dict[str, Any] | None, list[record_check.Diagnostic]]:
    """Load a regular manifest after lstat-checking every path component."""

    label = os.fspath(manifest_path)
    absolute = _normalized_absolute(manifest_path)
    parts = Path(absolute).parts
    current = parts[0]
    for part in parts[1:]:
        current = os.path.join(current, part)
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return None, [
                _diagnostic(
                    "MANIFEST_INPUT_NOT_FOUND",
                    label,
                    message=f"no such file: {absolute}",
                )
            ]
        except OSError as error:
            return None, [
                _diagnostic("MANIFEST_INPUT_READ_ERROR", label, message=str(error))
            ]
        if stat.S_ISLNK(info.st_mode):
            return None, [_diagnostic("MANIFEST_INPUT_SYMLINK", label)]

    try:
        info = os.lstat(absolute)
    except FileNotFoundError:
        return None, [_diagnostic("MANIFEST_INPUT_NOT_FOUND", label)]
    except OSError as error:
        return None, [
            _diagnostic("MANIFEST_INPUT_READ_ERROR", label, message=str(error))
        ]
    if not stat.S_ISREG(info.st_mode):
        return None, [_diagnostic("MANIFEST_INPUT_UNSUPPORTED_TYPE", label)]

    try:
        raw = Path(absolute).read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as error:
        return None, [
            _diagnostic("MANIFEST_INPUT_READ_ERROR", label, message=str(error))
        ]
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        return None, [
            _diagnostic("MANIFEST_INVALID_JSON", label, message=str(error))
        ]
    if not isinstance(document, dict):
        return None, [_diagnostic("MANIFEST_SCHEMA_INVALID", label)]

    errors = sorted(
        _MANIFEST_VALIDATOR.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        pointer = (
            "#/" + "/".join(str(part) for part in error.absolute_path)
            if error.absolute_path
            else "#"
        )
        code = (
            "MANIFEST_FORMAT_VERSION"
            if list(error.absolute_path) == ["formatVersion"]
            else "MANIFEST_SCHEMA_INVALID"
        )
        return None, [_diagnostic(code, label, pointer)]
    return document, []


def _safe_root(root: str) -> bool:
    if not root or root == "." or "\\" in root or root.startswith("/"):
        return False
    path = PurePosixPath(root)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        return False
    return path.as_posix() == root


def _parse_manifest(
    document: dict[str, Any], manifest_label: str
) -> tuple[
    tuple[_Source, ...],
    tuple[_Member, ...],
    list[record_check.Diagnostic],
]:
    diagnostics: list[record_check.Diagnostic] = []
    sources: list[_Source] = []
    source_ids: set[str] = set()
    source_roots: set[str] = set()

    for index, raw_source in enumerate(document["sources"]):
        source_id = raw_source["id"]
        root = raw_source["root"]
        pointer = f"#/sources/{index}"
        if source_id in source_ids:
            diagnostics.append(
                _diagnostic(
                    "MANIFEST_DUPLICATE_SOURCE_ID",
                    manifest_label,
                    f"{pointer}/id",
                )
            )
        source_ids.add(source_id)
        if root in source_roots:
            diagnostics.append(
                _diagnostic(
                    "MANIFEST_DUPLICATE_SOURCE_ROOT",
                    manifest_label,
                    f"{pointer}/root",
                )
            )
        source_roots.add(root)
        if not _safe_root(root):
            diagnostics.append(
                _diagnostic(
                    "MANIFEST_UNSAFE_ROOT",
                    manifest_label,
                    f"{pointer}/root",
                )
            )
        sources.append(_Source(source_id, root, frozenset(raw_source["roles"])))

    for left_index, left in enumerate(sources):
        left_path = PurePosixPath(left.root)
        for right_index, right in enumerate(sources[left_index + 1 :], left_index + 1):
            right_path = PurePosixPath(right.root)
            if left.root == right.root:
                continue
            if left_path in right_path.parents or right_path in left_path.parents:
                diagnostics.append(
                    _diagnostic(
                        "MANIFEST_OVERLAPPING_ROOT",
                        manifest_label,
                        f"#/sources/{right_index}/root",
                    )
                )

    by_source = {source.source_id: source for source in sources}
    members: list[_Member] = []
    member_addresses: set[Address] = set()
    for index, raw_member in enumerate(document["members"]):
        address_document = raw_member["address"]
        address = record_check.address_of(address_document)
        pointer = f"#/members/{index}"
        if address in member_addresses:
            diagnostics.append(
                _diagnostic(
                    "MANIFEST_DUPLICATE_MEMBER_ADDRESS",
                    manifest_label,
                    f"{pointer}/address",
                )
            )
        member_addresses.add(address)
        source = by_source.get(raw_member["source"])
        if source is None:
            diagnostics.append(
                _diagnostic(
                    "MANIFEST_UNKNOWN_SOURCE",
                    manifest_label,
                    f"{pointer}/source",
                )
            )
        elif raw_member["role"] not in source.roles:
            diagnostics.append(
                _diagnostic(
                    "MANIFEST_ROLE_NOT_ALLOWED",
                    manifest_label,
                    f"{pointer}/role",
                )
            )
        members.append(
            _Member(
                raw_member["source"],
                address,
                raw_member["sha256"],
                raw_member["role"],
            )
        )

    diagnostics.sort(key=record_check.Diagnostic.sort_key)
    return tuple(sources), tuple(members), diagnostics


def _inspect_manifest_projection(
    manifest_path: Path = DEFAULT_STACK_MANIFEST,
) -> _ManifestProjection:
    """Snapshot manifest authority without observing any declared record root."""

    manifest, diagnostics = _load_manifest(Path(manifest_path))
    if manifest is None:
        return _ManifestProjection((), (), tuple(diagnostics))
    sources, members, diagnostics = _parse_manifest(
        manifest, os.fspath(manifest_path)
    )
    return _ManifestProjection(sources, members, tuple(diagnostics))


def _inventory(
    source_records: tuple[_finite_source._SourceRecord, ...],
    members: tuple[_Member, ...],
    sources: tuple[_Source, ...],
) -> tuple[GraphRecord, ...]:
    by_address = {member.address: member for member in members}
    source_roles = {source.source_id: source.roles for source in sources}
    records: list[GraphRecord] = []
    for record in source_records:
        source = record.path.split("/", 1)[0]
        member = by_address.get(record.address)
        role: str | None = member.role if member is not None else None
        if role is None and len(source_roles.get(source, ())) == 1:
            role = next(iter(source_roles[source]))
        records.append(
            GraphRecord(
                address=record.address,
                path=record.path,
                sha256=record.sha256,
                role=role,
                source=source,
                _document_text=json.dumps(
                    record.document,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            )
        )
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.address,
                record.sha256,
                record.role or "",
                record.source,
                record.path,
            ),
        )
    )


def _membership_diagnostics(
    records: tuple[GraphRecord, ...], members: tuple[_Member, ...]
) -> list[record_check.Diagnostic]:
    diagnostics: list[record_check.Diagnostic] = []
    expected = {(member.source, member.address): member for member in members}
    observed = {(record.source, record.address): record for record in records}

    for key, member in sorted(expected.items()):
        if key not in observed:
            diagnostics.append(
                _diagnostic(
                    "GRAPH_MISSING_MEMBER",
                    member.source,
                    message=f"manifest requires {record_check.fmt_tuple(dict(zip(('kind', 'id', 'version'), member.address)))}",
                )
            )

    for key, record in sorted(observed.items()):
        member = expected.get(key)
        if member is None:
            diagnostics.append(
                _diagnostic(
                    "GRAPH_UNEXPECTED_MEMBER",
                    record.path,
                    message=f"manifest does not include {record_check.fmt_tuple(dict(zip(('kind', 'id', 'version'), record.address)))} in source {record.source!r}",
                )
            )
        elif record.sha256 != member.sha256:
            diagnostics.append(
                _diagnostic(
                    "GRAPH_DIGEST_MISMATCH",
                    record.path,
                    message=f"record has SHA-256 {record.sha256}, expected {member.sha256}",
                )
            )
    diagnostics.sort(key=record_check.Diagnostic.sort_key)
    return diagnostics


def inspect_stack_graph(manifest_path: Path) -> GraphObservation:
    """Inspect one supplied Stack manifest without defaults or execution."""

    manifest_path = Path(manifest_path)
    manifest, diagnostics = _load_manifest(manifest_path)
    if manifest is None:
        return GraphObservation((), tuple(diagnostics))

    sources, members, manifest_diagnostics = _parse_manifest(
        manifest, os.fspath(manifest_path)
    )
    if manifest_diagnostics:
        return GraphObservation((), tuple(manifest_diagnostics))

    source = _finite_source._observe_finite_source(
        tuple(
            _finite_source._SourceRoot(
                declared.source_id,
                manifest_path.parent / PurePosixPath(declared.root),
            )
            for declared in sources
        )
    )
    records = _inventory(source.records, members, sources)
    diagnostics = list(source.diagnostics)

    # Preserve the record input/schema and link phases.  Membership conclusions
    # are made only from one complete, schema-valid, link-valid record graph.
    if not diagnostics:
        graph_diagnostics = record_check.check_graph(
            {record.path: record.document for record in records}
        )
        diagnostics.extend(graph_diagnostics)
        if not graph_diagnostics:
            diagnostics.extend(_membership_diagnostics(records, members))

    diagnostics.sort(key=record_check.Diagnostic.sort_key)
    return GraphObservation(records, tuple(diagnostics))
