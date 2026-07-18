"""Read-only inspection of independent Stack package registration.

This is deliberately a Stack-specific product boundary.  It inventories one
finite local union of a theory source set and one explicitly selected package
source set using the governed finite-source helper and record/link checker;
it does not execute adapters, campaigns, proof tooling, or resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from semantic_packages import _finite_source, graph
from scripts import record_check


Address = tuple[str, str, str]


@dataclass(frozen=True)
class RegistrationRecord:
    """One schema-valid record observed in the theory/package union."""

    address: Address
    path: str
    sha256: str
    role: str


@dataclass(frozen=True)
class RegistrationObservation:
    """Deterministic inventory and diagnostics for a registration attempt."""

    package: str
    records: tuple[RegistrationRecord, ...]
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


_MANIFEST = graph._inspect_manifest_projection()
_SOURCE_ROOTS = {source.source_id: source.root for source in _MANIFEST.sources}
_THEORY_APPROVED: dict[Address, str] = {
    member.address: member.sha256
    for member in _MANIFEST.members
    if member.source == "theory"
}
_PACKAGE_APPROVED: dict[str, dict[Address, str]] = {
    source_id: {
        member.address: member.sha256
        for member in _MANIFEST.members
        if member.source == source_id
    }
    for source_id, root in _SOURCE_ROOTS.items()
    if Path(root).parts[:1] == ("packages",)
}
_ROLE_BY_ADDRESS: dict[Address, str] = {
    member.address: member.role for member in _MANIFEST.members
}


def _root_label(path: str) -> str:
    return path.split("/", 1)[0]


def _role_for_record(path: str, address: Address) -> str:
    # Ownership role is decided by accepted address identity, not by the
    # physical root a record happens to be observed under: an exact theory
    # or package address keeps its authored role even when moved to the
    # other root, since the physical root only governs registration validity
    # (see _registration_diagnostics), never who authored the content.
    governed_role = _ROLE_BY_ADDRESS.get(address)
    if governed_role is not None:
        return governed_role
    # Wholly unexpected address: no accepted identity exists to attribute
    # authorship to, so fall back to a deterministic root-derived label.
    # This observation is invalid regardless (REGISTRATION_UNEXPECTED_ADDRESS).
    return "package-authored" if _root_label(path) == "package" else "theory-authored"


def _address_text(address: Address) -> str:
    return record_check.fmt_tuple(dict(zip(("kind", "id", "version"), address)))


def _inventory(
    records: tuple[_finite_source._SourceRecord, ...],
) -> tuple[RegistrationRecord, ...]:
    inventory = [
        RegistrationRecord(
            address=record.address,
            path=record.path,
            sha256=record.sha256,
            role=_role_for_record(record.path, record.address),
        )
        for record in records
    ]
    return tuple(
        sorted(inventory, key=lambda item: (item.address, item.path, item.sha256, item.role))
    )


def _root_approved(
    root: str,
    theory_approved: dict[Address, str],
    package_approved: dict[Address, str],
) -> dict[Address, str]:
    if root == "theory":
        return theory_approved
    if root == "package":
        return package_approved
    return {}


def _registration_diagnostics(
    inventory: tuple[RegistrationRecord, ...],
    theory_approved: dict[Address, str],
    package_approved: dict[Address, str],
) -> list[record_check.Diagnostic]:
    diagnostics: list[record_check.Diagnostic] = []

    # Missing addresses are decided per-root: a theory address is only
    # satisfied by a record actually observed under the theory root, and a
    # package address only by a record observed under the package root.  An
    # address moved across roots is missing from its owning root even though
    # its bytes survive elsewhere.
    for root, approved in (("theory", theory_approved), ("package", package_approved)):
        observed_in_root = {
            item.address for item in inventory if _root_label(item.path) == root
        }
        for address in sorted(set(approved) - observed_in_root):
            diagnostics.append(
                record_check.Diagnostic(
                    "REGISTRATION_MISSING_ADDRESS",
                    ".",
                    "#",
                    f"Stack package registration requires {_address_text(address)}",
                )
            )

    for item in inventory:
        approved = _root_approved(_root_label(item.path), theory_approved, package_approved)
        expected_sha256 = approved.get(item.address)
        if expected_sha256 is None:
            diagnostics.append(
                record_check.Diagnostic(
                    "REGISTRATION_UNEXPECTED_ADDRESS",
                    item.path,
                    "#",
                    "Stack package registration does not include "
                    f"{_address_text(item.address)}",
                )
            )
        elif item.sha256 != expected_sha256:
            diagnostics.append(
                record_check.Diagnostic(
                    "REGISTRATION_SOURCE_DIGEST_MISMATCH",
                    item.path,
                    "#",
                    f"record {_address_text(item.address)} has SHA-256 {item.sha256}, "
                    f"expected {expected_sha256}",
                )
            )
    return diagnostics


def inspect_stack_package(
    theory_root: Path, package_root: Path, package: str
) -> RegistrationObservation:
    """Inspect the theory/package union without executing or mutating anything."""

    if not _MANIFEST.ok:
        return RegistrationObservation(package, (), _MANIFEST.diagnostics)

    package_approved = _PACKAGE_APPROVED.get(package)
    if package_approved is None:
        diagnostic = record_check.Diagnostic(
            "REGISTRATION_UNKNOWN_SELECTOR",
            ".",
            "#",
            f"no Stack package registration selector for {package!r}",
        )
        return RegistrationObservation(package, (), (diagnostic,))

    source = _finite_source._observe_finite_source(
        (
            _finite_source._SourceRoot("theory", theory_root),
            _finite_source._SourceRoot("package", package_root),
        )
    )
    diagnostics = list(source.diagnostics)
    inventory = _inventory(source.records)

    # Preserve the loader's input/schema phase barrier.  Graph and registration
    # conclusions are not manufactured from a partial record set.
    if not diagnostics:
        records = {record.path: record.document for record in source.records}
        graph_diagnostics = record_check.check_graph(records)
        diagnostics.extend(graph_diagnostics)
        diagnostics.extend(
            _registration_diagnostics(inventory, _THEORY_APPROVED, package_approved)
        )

    diagnostics.sort(key=record_check.Diagnostic.sort_key)
    return RegistrationObservation(package, inventory, tuple(diagnostics))
