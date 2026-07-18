"""Exact successor and recovery observations for the bounded Stack tracer.

This module compares already captured graph snapshots and composes the existing
resolver and theory projection.  It does not discover successors, infer lineage or
compatibility, execute artifacts, or implement a time/freshness engine.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts import record_check
from semantic_packages import resolver, theory_projection
from semantic_packages.graph import Address, GraphObservation


@dataclass(frozen=True)
class StaleEvidence:
    address: Address
    reason: str


@dataclass(frozen=True)
class SuccessorInspection:
    predecessor_preserved: bool
    added_addresses: tuple[Address, ...]
    stale_evidence: tuple[StaleEvidence, ...]
    predecessor_resolution: resolver.ResolutionResult
    successor_resolution: resolver.ResolutionResult
    predecessor_theory: theory_projection.ProjectionResult
    successor_theory: theory_projection.ProjectionResult
    recovery_candidates: tuple[Address, ...]
    successor_claim_states: tuple[tuple[Address, str], ...]
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def _diagnostic(code: str, path: str, message: str | None = None) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, path, "#", message)


def _address(value: Any) -> Address | None:
    if not isinstance(value, dict):
        return None
    parts = value.get("kind"), value.get("id"), value.get("version")
    if not all(isinstance(part, str) for part in parts):
        return None
    return parts  # type: ignore[return-value]


def compare_manifest_revisions(
    predecessor_path: Path, successor_path: Path
) -> tuple[record_check.Diagnostic, ...]:
    """Check that a successor repeats predecessor sources and members exactly."""

    predecessor_path = Path(predecessor_path)
    successor_path = Path(successor_path)
    try:
        predecessor = json.loads(predecessor_path.read_text(encoding="utf-8"))
        successor = json.loads(successor_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return (_diagnostic("SUCCESSOR_MANIFEST_READ_ERROR", str(successor_path), str(error)),)
    if not isinstance(predecessor, dict) or not isinstance(successor, dict):
        return (_diagnostic("SUCCESSOR_MANIFEST_SHAPE", str(successor_path)),)

    diagnostics: list[record_check.Diagnostic] = []
    successor_sources = {
        item.get("id"): item
        for item in successor.get("sources", [])
        if isinstance(item, dict)
    }
    for source in predecessor.get("sources", []):
        if not isinstance(source, dict) or successor_sources.get(source.get("id")) != source:
            diagnostics.append(
                _diagnostic(
                    "SUCCESSOR_PREDECESSOR_SOURCE_DRIFT",
                    str(successor_path),
                    repr(source.get("id") if isinstance(source, dict) else None),
                )
            )

    def member_key(item: Any) -> Address | None:
        return _address(item.get("address")) if isinstance(item, dict) else None

    successor_members = {
        key: item
        for item in successor.get("members", [])
        if (key := member_key(item)) is not None
    }
    for member in predecessor.get("members", []):
        key = member_key(member)
        if key is None or successor_members.get(key) != member:
            diagnostics.append(
                _diagnostic(
                    "SUCCESSOR_PREDECESSOR_MEMBER_DRIFT",
                    str(successor_path),
                    repr(key),
                )
            )
    return tuple(diagnostics)


def resolve_exact(
    graph: GraphObservation,
    *,
    policy: Address,
    profile: Address,
    specification: Address,
) -> resolver.ResolutionResult:
    """Expose the existing exact resolver without adding successor selection."""

    return resolver.resolve_stack(
        graph,
        policy=policy,
        profile=profile,
        specification=specification,
    )


def inspect_stack_successor(
    predecessor: GraphObservation,
    successor: GraphObservation,
    *,
    predecessor_policy: Address,
    successor_policy: Address,
    profile: Address,
    predecessor_specification: Address,
    successor_specification: Address,
) -> SuccessorInspection:
    """Compare exact snapshots and compose their consumer-visible observations."""

    predecessor_resolution = resolve_exact(
        successor,
        policy=predecessor_policy,
        profile=profile,
        specification=predecessor_specification,
    )
    successor_resolution = resolve_exact(
        successor,
        policy=successor_policy,
        profile=profile,
        specification=successor_specification,
    )
    predecessor_theory = theory_projection.project_theory(
        successor, specification=predecessor_specification
    )
    successor_theory = theory_projection.project_theory(
        successor, specification=successor_specification
    )
    if not predecessor.ok or not successor.ok:
        diagnostics = predecessor.diagnostics + successor.diagnostics
    else:
        diagnostics = (
            predecessor_resolution.diagnostics
            + successor_resolution.diagnostics
            + predecessor_theory.diagnostics
            + successor_theory.diagnostics
        )

    predecessor_by_address = {record.address: record for record in predecessor.records}
    successor_by_address = {record.address: record for record in successor.records}
    predecessor_preserved = all(
        successor_by_address.get(address) == record
        for address, record in predecessor_by_address.items()
    )
    if not predecessor_preserved:
        diagnostics += (_diagnostic("SUCCESSOR_PREDECESSOR_RECORD_DRIFT", "<graphs>"),)

    added = tuple(sorted(set(successor_by_address) - set(predecessor_by_address)))
    stale: list[StaleEvidence] = []
    claim_states: list[tuple[Address, str]] = []
    for record in successor.records:
        document = record.document
        if (
            document.get("kind") == "evidence"
            and _address(document.get("specification")) == predecessor_specification
        ):
            stale.append(StaleEvidence(record.address, "exact-specification-version"))
        if (
            document.get("kind") == "claim"
            and _address(document.get("governingSpecification"))
            == successor_specification
        ):
            claim_states.append((record.address, document.get("state", "<invalid>")))

    old_acceptable = tuple(
        candidate.realization
        for candidate in predecessor_resolution.candidates
        if candidate.semantic_status == "acceptable"
    )
    new_acceptable = tuple(
        candidate.realization
        for candidate in successor_resolution.candidates
        if candidate.semantic_status == "acceptable"
    )
    recovery = tuple(sorted(old_acceptable)) if old_acceptable and not new_acceptable else ()
    return SuccessorInspection(
        predecessor_preserved=predecessor_preserved,
        added_addresses=added,
        stale_evidence=tuple(sorted(stale, key=lambda item: item.address)),
        predecessor_resolution=predecessor_resolution,
        successor_resolution=successor_resolution,
        predecessor_theory=predecessor_theory,
        successor_theory=successor_theory,
        recovery_candidates=recovery,
        successor_claim_states=tuple(sorted(claim_states)),
        diagnostics=diagnostics,
    )
