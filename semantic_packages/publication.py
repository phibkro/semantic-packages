"""Read-only inspection of the frozen Stack theory publication.

This is deliberately a Stack-specific product boundary.  It inventories one
finite local source set using the governed Wave 3 loader and record/link
checker; it does not execute proof tooling, registry metadata, or Realizations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from semantic_packages import _finite_source, graph
from scripts import record_check


Address = tuple[str, str, str]


@dataclass(frozen=True)
class PublicationRecord:
    """One schema-valid record observed in the supplied source set."""

    address: Address
    path: str
    sha256: str
    role: str


@dataclass(frozen=True)
class PublicationObservation:
    """Deterministic inventory and diagnostics for a publication attempt."""

    records: tuple[PublicationRecord, ...]
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


@dataclass(frozen=True)
class _ApprovedRecord:
    sha256: str
    role: str
    mismatch_code: str


_MANIFEST = graph._inspect_manifest_projection()


def _publication_role(role: str) -> str:
    return "authored" if role == "theory-authored" else role


def _mismatch_code(address: Address) -> str:
    if address[0] in {"claim", "specification"}:
        return "PUBLICATION_PROOF_INPUT_DIGEST_MISMATCH"
    return "PUBLICATION_SOURCE_DIGEST_MISMATCH"


_APPROVED: dict[Address, _ApprovedRecord] = {
    member.address: _ApprovedRecord(
        member.sha256,
        _publication_role(member.role),
        _mismatch_code(member.address),
    )
    for member in _MANIFEST.members
    if member.source == "theory"
}

_APPROVED_KIND_IDS = {(kind, record_id) for kind, record_id, _ in _APPROVED}


def _inventory(
    records: tuple[_finite_source._SourceRecord, ...],
) -> tuple[PublicationRecord, ...]:
    inventory: list[PublicationRecord] = []
    for record in records:
        approved = _APPROVED.get(record.address)
        inventory.append(
            PublicationRecord(
                address=record.address,
                path=record.path,
                sha256=record.sha256,
                role=approved.role if approved is not None else "authored",
            )
        )
    return tuple(sorted(inventory, key=lambda item: (item.address, item.path)))


def _publication_diagnostics(
    inventory: tuple[PublicationRecord, ...],
    records: dict[str, dict],
    graph_diagnostics: list[record_check.Diagnostic],
) -> list[record_check.Diagnostic]:
    diagnostics: list[record_check.Diagnostic] = []
    records_by_path = records
    observed_addresses = {item.address for item in inventory}

    # Suppress a redundant missing-address diagnostic only when a graph
    # diagnostic already names that exact requested tuple at an actionable
    # reference.  An unrelated graph failure must not hide a missing leaf.
    for address in sorted(set(_APPROVED) - observed_addresses):
        address_text = record_check.fmt_tuple(
            dict(zip(("kind", "id", "version"), address))
        )
        if any(
            diagnostic.message is not None
            and f"requested {address_text}" in diagnostic.message
            for diagnostic in graph_diagnostics
        ):
            continue
        diagnostics.append(
            record_check.Diagnostic(
                "PUBLICATION_MISSING_ADDRESS",
                ".",
                "#",
                f"the Stack theory publication requires {address_text}",
            )
        )

    for item in inventory:
        approved = _APPROVED.get(item.address)
        if approved is not None:
            if item.sha256 != approved.sha256:
                diagnostics.append(
                    record_check.Diagnostic(
                        approved.mismatch_code,
                        item.path,
                        "#",
                        f"record {record_check.fmt_tuple(records_by_path[item.path])} "
                        f"has SHA-256 {item.sha256}, expected {approved.sha256}",
                    )
                )
            continue

        # A version near-miss of one frozen identity is not duplicated when the
        # governed exact-reference linker already diagnosed that exact request
        # at its actionable pointer.  An otherwise unreferenced extra version
        # remains an unexpected publication address.
        if item.address[:2] in _APPROVED_KIND_IDS:
            accepted = next(
                address
                for address in _APPROVED
                if address[:2] == item.address[:2]
            )
            accepted_text = record_check.fmt_tuple(
                dict(zip(("kind", "id", "version"), accepted))
            )
            if any(
                diagnostic.code == "LINK_VERSION_MISMATCH"
                and diagnostic.message is not None
                and f"requested {accepted_text}" in diagnostic.message
                for diagnostic in graph_diagnostics
            ):
                continue
        diagnostics.append(
            record_check.Diagnostic(
                "PUBLICATION_UNEXPECTED_ADDRESS",
                item.path,
                "#",
                f"the Stack theory publication does not include "
                f"{record_check.fmt_tuple(records_by_path[item.path])}",
            )
        )
    return diagnostics


def inspect_stack_theory(root: Path) -> PublicationObservation:
    """Inspect ``root`` without executing or mutating any supplied artifact."""

    if not _MANIFEST.ok:
        return PublicationObservation((), _MANIFEST.diagnostics)

    source = _finite_source._observe_finite_source(
        (_finite_source._SourceRoot("", root),)
    )
    diagnostics = list(source.diagnostics)
    inventory = _inventory(source.records)
    records = {record.path: record.document for record in source.records}

    # Preserve the loader's input/schema phase barrier.  Graph and publication
    # conclusions are not manufactured from a partial record set.
    if not diagnostics:
        graph_diagnostics = record_check.check_graph(records)
        diagnostics.extend(graph_diagnostics)
        diagnostics.extend(
            _publication_diagnostics(inventory, records, graph_diagnostics)
        )

    diagnostics.sort(key=record_check.Diagnostic.sort_key)
    return PublicationObservation(inventory, tuple(diagnostics))
