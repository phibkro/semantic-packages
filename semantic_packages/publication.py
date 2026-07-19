"""Read-only inspection of a manifest-governed theory publication.

Shared mechanics inventory one exact theory source selected by supplied
manifest authority. The Stack actor wrapper pins its product authority and
accepts no override. Neither path executes proof tooling, registry metadata,
or Realizations.
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


_MANIFEST = graph.inspect_manifest_authority(graph.DEFAULT_STACK_MANIFEST)
_THEORY_ROLES = frozenset({"theory-authored", "dependency"})


def _publication_role(role: str) -> str:
    return "authored" if role == "theory-authored" else role


def _mismatch_code(address: Address) -> str:
    if address[0] in {"claim", "specification"}:
        return "PUBLICATION_PROOF_INPUT_DIGEST_MISMATCH"
    return "PUBLICATION_SOURCE_DIGEST_MISMATCH"


def _inventory(
    records: tuple[_finite_source._SourceRecord, ...],
    approved_records: dict[Address, _ApprovedRecord],
) -> tuple[PublicationRecord, ...]:
    inventory: list[PublicationRecord] = []
    for record in records:
        approved = approved_records.get(record.address)
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
    approved_records: dict[Address, _ApprovedRecord],
    product: str,
) -> list[record_check.Diagnostic]:
    diagnostics: list[record_check.Diagnostic] = []
    records_by_path = records
    observed_addresses = {item.address for item in inventory}

    # Suppress a redundant missing-address diagnostic only when a graph
    # diagnostic already names that exact requested tuple at an actionable
    # reference.  An unrelated graph failure must not hide a missing leaf.
    approved_kind_ids = {
        (kind, record_id) for kind, record_id, _ in approved_records
    }
    for address in sorted(set(approved_records) - observed_addresses):
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
                f"the {product} theory publication requires {address_text}",
            )
        )

    for item in inventory:
        approved = approved_records.get(item.address)
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
        if item.address[:2] in approved_kind_ids:
            accepted = next(
                address
                for address in approved_records
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
                f"the {product} theory publication does not include "
                f"{record_check.fmt_tuple(records_by_path[item.path])}",
            )
        )
    return diagnostics


def _selector_diagnostic(code: str, message: str) -> PublicationObservation:
    return PublicationObservation(
        (), (record_check.Diagnostic(code, ".", "#", message),)
    )


def inspect_theory_publication(
    root: Path,
    *,
    authority: graph.ManifestAuthority,
    source: str,
    product: str,
) -> PublicationObservation:
    """Observe one exact theory source under supplied, non-product authority."""

    if not authority.ok:
        return PublicationObservation((), authority.diagnostics)

    declared_source = next(
        (item for item in authority.sources if item.source_id == source), None
    )
    if declared_source is None:
        return _selector_diagnostic(
            "PUBLICATION_UNKNOWN_SOURCE",
            f"no {product} theory publication source selector for {source!r}",
        )
    if not declared_source.roles.issubset(_THEORY_ROLES):
        return _selector_diagnostic(
            "PUBLICATION_SOURCE_ROLE_MISMATCH",
            f"{product} theory publication source {source!r} does not permit only "
            "theory-authored/dependency roles",
        )

    approved_records = {
        member.address: _ApprovedRecord(
            member.sha256,
            _publication_role(member.role),
            _mismatch_code(member.address),
        )
        for member in authority.members
        if member.source == source
    }

    source = _finite_source._observe_finite_source(
        (_finite_source._SourceRoot("", root),)
    )
    diagnostics = list(source.diagnostics)
    inventory = _inventory(source.records, approved_records)
    records = {record.path: record.document for record in source.records}

    # Preserve the loader's input/schema phase barrier.  Graph and publication
    # conclusions are not manufactured from a partial record set.
    if not diagnostics:
        graph_diagnostics = record_check.check_graph(records)
        diagnostics.extend(graph_diagnostics)
        diagnostics.extend(
            _publication_diagnostics(
                inventory,
                records,
                graph_diagnostics,
                approved_records,
                product,
            )
        )

    diagnostics.sort(key=record_check.Diagnostic.sort_key)
    return PublicationObservation(inventory, tuple(diagnostics))


def _project_theory_publication(
    observation: graph.GraphObservation,
    *,
    authority: graph.ManifestAuthority,
    source: str,
    product: str,
) -> PublicationObservation:
    """Internally project publication from an actor-owned captured graph.

    GraphObservation construction is deliberately not an authentication boundary. Actor
    wrappers must obtain the observation through their pinned graph inspection before
    using this non-accepting projection seam.
    """

    if not authority.ok:
        return PublicationObservation((), authority.diagnostics)
    declared_source = next(
        (item for item in authority.sources if item.source_id == source), None
    )
    if declared_source is None:
        return _selector_diagnostic(
            "PUBLICATION_UNKNOWN_SOURCE",
            f"no {product} theory publication source selector for {source!r}",
        )
    if not declared_source.roles.issubset(_THEORY_ROLES):
        return _selector_diagnostic(
            "PUBLICATION_SOURCE_ROLE_MISMATCH",
            f"{product} theory publication source {source!r} does not permit only "
            "theory-authored/dependency roles",
        )
    if not observation.ok:
        return PublicationObservation((), observation.diagnostics)

    prefix = f"{source}/"
    records = tuple(
        sorted(
            (
                PublicationRecord(
                    record.address,
                    record.path[len(prefix) :]
                    if record.path.startswith(prefix)
                    else record.path,
                    record.sha256,
                    _publication_role(record.role or "theory-authored"),
                )
                for record in observation.records
                if record.source == source
            ),
            key=lambda item: (item.address, item.path),
        )
    )
    return PublicationObservation(records, ())


def inspect_stack_theory(root: Path) -> PublicationObservation:
    """Inspect the pinned Stack theory surface without actor overrides."""

    return inspect_theory_publication(
        root,
        authority=_MANIFEST,
        source="theory",
        product="Stack",
    )
