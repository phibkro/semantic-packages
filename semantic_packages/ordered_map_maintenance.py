"""Exact successor and recovery observation for the OrderedMap tracer.

The actor authenticates one pinned append-only maintenance manifest, captures it once,
and compares it with the already accepted product replay. It neither discovers a
successor nor infers latest-version, lineage, refinement, Evidence migration, or
semantic-version compatibility.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from scripts import record_check
from semantic_packages import (
    canonical_artifact,
    graph,
    ordered_map_product,
    theory_projection,
)
from semantic_packages.graph import Address, GraphObservation
from semantic_packages.ordered_map_resolution import resolve_ordered_map
from semantic_packages.resolver import (
    ProhibitionDisposition,
    ResolutionCandidate,
    ResolutionResult,
    _address,
    _addresses,
    _boundary,
    _claim_targets,
    _concern_disposition,
)
from semantic_packages.theory_projection import TheoryView


_ROOT = Path(__file__).resolve().parents[1]
_SUCCESSOR_MANIFEST = Path("registry/ordered-map/successor-manifest.json")
_MANIFEST_SCHEMA = Path("schemas/registry-manifest.schema.json")
_SUCCESSOR_MANIFEST_RAW_SHA256 = (
    "f5e87e65c4765865203158cdd6cbfbf46774dd7d068ddadeaa37c41a5f6ffaf3"
)
_PREDECESSOR_SPECIFICATION = ("specification", "ordered-map", "0.1.0")
_SUCCESSOR_SPECIFICATION = ("specification", "ordered-map", "0.2.0")
_PREDECESSOR_POLICY = (
    "consumerPolicy",
    "ordered-map-bounded-policy",
    "0.1.0",
)
_SUCCESSOR_POLICY = (
    "consumerPolicy",
    "ordered-map-bounded-policy",
    "0.2.0",
)
_PROFILE = ("realizationProfile", "ordered-map-ascii-fold", "0.1.0")
_SUCCESSOR_RECORDS = {
    _SUCCESSOR_SPECIFICATION: (
        "ordered-map-successor-theory",
        "theory-authored",
        "05bd1dee68216834a81e9095425905a3fb5a5c93530bbe2479c07ef1a6a3afd0",
    ),
    _SUCCESSOR_POLICY: (
        "ordered-map-successor-consumer",
        "package-consumer-authored",
        "db788f7fb1adab5f8f9baea65add07269e39e7fdc8d1f84aef9df18b34ece00d",
    ),
}


@dataclass(frozen=True)
class StaleEvidence:
    address: Address
    reason: str


@dataclass(frozen=True)
class OrderedMapMaintenanceObservation:
    source: ordered_map_product.ProductCandidateObservation
    successor_graph: GraphObservation | None
    successor_manifest_raw_sha256: str | None
    predecessor_preserved: bool
    added_addresses: tuple[Address, ...]
    stale_evidence: tuple[StaleEvidence, ...]
    predecessor_resolution: ResolutionResult | None
    successor_resolution: ResolutionResult | None
    successor_theory: TheoryView | None
    recovery_candidates: tuple[Address, ...]
    output: str | None
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def _diagnostic(code: str, message: str | None = None) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, "<ordered-map-successor>", "#", message)


def _failure(
    source: ordered_map_product.ProductCandidateObservation,
    diagnostics: tuple[record_check.Diagnostic, ...],
    *,
    successor_graph: GraphObservation | None = None,
    successor_manifest_raw_sha256: str | None = None,
) -> OrderedMapMaintenanceObservation:
    return OrderedMapMaintenanceObservation(
        source,
        successor_graph,
        successor_manifest_raw_sha256,
        False,
        (),
        (),
        None,
        None,
        None,
        (),
        None,
        diagnostics,
    )


def _successor_prohibition(
    policy_entry: dict[str, Any],
    *,
    specification_document: dict[str, Any],
    realization: Address,
    documents: tuple[tuple[Address, dict[str, Any]], ...],
) -> ProhibitionDisposition:
    proposition = policy_entry.get("proposition")
    declaration = (
        proposition.get("declarationId", "<invalid>")
        if isinstance(proposition, dict)
        else "<invalid>"
    )
    event_pattern = policy_entry.get("eventPattern", "<invalid>")
    effect = specification_document.get("effects")
    accepted_scopes = policy_entry.get("acceptedEvidenceScope")
    complete = (
        isinstance(proposition, dict)
        and _address(proposition.get("specification")) == _SUCCESSOR_SPECIFICATION
        and isinstance(effect, dict)
        and effect.get("id") == declaration
        and event_pattern in effect.get("forbidden", [])
        and isinstance(accepted_scopes, list)
        and all(isinstance(item, str) for item in accepted_scopes)
    )
    target_claims = tuple(
        (address, document)
        for address, document in documents
        if _claim_targets(
            document,
            realization=realization,
            specification=_SUCCESSOR_SPECIFICATION,
            concern="effect.conformance",
            declaration=declaration,
        )
    )
    reasons: tuple[str, ...]
    if not complete:
        status = "policy-incomplete"
        reasons = ("policy-scope-incomplete",)
    elif not target_claims:
        status = "unsupported"
        reasons = ("missing-claim",)
    else:
        # O8 authorizes no successor Claim or Evidence. A detached control that adds
        # either remains visible but cannot become selected assurance.
        status = "unsupported"
        reasons = ("successor-evidence-not-authorized",)
    return ProhibitionDisposition(
        declaration,
        event_pattern,
        status,
        True,
        (),
        (),
        (),
        (),
        (),
        (),
        reasons,
        (),
        (),
    )


def _resolve_ordered_map_successor(
    observation: GraphObservation,
) -> ResolutionResult:
    """Resolve only the exact OrderedMap successor selectors from a detached graph."""

    if not observation.ok:
        return ResolutionResult(
            (), (_diagnostic("ORDERED_MAP_SUCCESSOR_INVALID_GRAPH"),)
        )
    documents = tuple(
        (record.address, record.document) for record in observation.records
    )
    by_address = {address: document for address, document in documents}
    for selector, expected_kind in (
        (_SUCCESSOR_POLICY, "consumerPolicy"),
        (_PROFILE, "realizationProfile"),
        (_SUCCESSOR_SPECIFICATION, "specification"),
    ):
        document = by_address.get(selector)
        if document is None:
            return ResolutionResult(
                (),
                (
                    _diagnostic(
                        "ORDERED_MAP_SUCCESSOR_SELECTOR_NOT_FOUND", repr(selector)
                    ),
                ),
            )
        if selector[0] != expected_kind or document.get("kind") != expected_kind:
            return ResolutionResult(
                (),
                (
                    _diagnostic(
                        "ORDERED_MAP_SUCCESSOR_SELECTOR_KIND", repr(selector)
                    ),
                ),
            )

    policy_document = by_address[_SUCCESSOR_POLICY]
    if (
        _address(policy_document.get("specification")) != _SUCCESSOR_SPECIFICATION
        or _address(policy_document.get("profile")) != _PROFILE
    ):
        return ResolutionResult(
            (),
            (_diagnostic("ORDERED_MAP_SUCCESSOR_POLICY_SELECTOR_MISMATCH"),),
        )

    specification_document = by_address[_SUCCESSOR_SPECIFICATION]
    candidates: list[ResolutionCandidate] = []
    for realization, realization_document in documents:
        if (
            realization_document.get("kind") != "realization"
            or _address(realization_document.get("specification"))
            != _SUCCESSOR_SPECIFICATION
            or _PROFILE
            not in _addresses(realization_document.get("supportedProfiles"))
        ):
            continue
        concerns = tuple(
            _concern_disposition(
                entry,
                specification_document=specification_document,
                specification=_SUCCESSOR_SPECIFICATION,
                profile=_PROFILE,
                realization=realization,
                documents=documents,
            )
            for entry in policy_document.get("concerns", [])
            if isinstance(entry, dict)
        )
        prohibitions = tuple(
            _successor_prohibition(
                entry,
                specification_document=specification_document,
                realization=realization,
                documents=documents,
            )
            for entry in policy_document.get("prohibitions", [])
            if isinstance(entry, dict)
        )
        blocked = any(item.blocks for item in concerns) or any(
            item.blocks for item in prohibitions
        )
        candidates.append(
            ResolutionCandidate(
                realization,
                "unacceptable" if blocked else "acceptable",
                concerns,
                prohibitions,
                _boundary(realization_document),
            )
        )
    return ResolutionResult(
        tuple(sorted(candidates, key=lambda item: item.realization)), ()
    )


def _successor_record_is_exact(record: graph.GraphRecord) -> bool:
    expected = _SUCCESSOR_RECORDS.get(record.address)
    if expected is None:
        return False
    source, role, digest = expected
    observed = hashlib.sha256(
        (record._document_text + "\n").encode("utf-8")
    ).hexdigest()
    return (
        record.source == source
        and record.role == role
        and record.sha256 == digest
        and observed == digest
    )


def _observe_ordered_map_maintenance(
    source: ordered_map_product.ProductCandidateObservation,
    successor: GraphObservation,
    *,
    successor_manifest_raw_sha256: str,
) -> OrderedMapMaintenanceObservation:
    """Compare two captured snapshots and derive exact maintenance observations."""

    if (
        not source.ok
        or source.graph is None
        or source.theory is None
        or not successor.ok
    ):
        diagnostics = source.diagnostics + (
            ()
            if successor.ok
            else (_diagnostic("ORDERED_MAP_SUCCESSOR_INVALID_GRAPH"),)
        )
        return _failure(
            source,
            diagnostics,
            successor_graph=successor,
            successor_manifest_raw_sha256=successor_manifest_raw_sha256,
        )

    predecessor_by_address = {
        record.address: record for record in source.graph.records
    }
    successor_by_address = {record.address: record for record in successor.records}
    if any(
        successor_by_address.get(address) != record
        for address, record in predecessor_by_address.items()
    ):
        return _failure(
            source,
            (_diagnostic("ORDERED_MAP_SUCCESSOR_PREDECESSOR_DRIFT"),),
            successor_graph=successor,
            successor_manifest_raw_sha256=successor_manifest_raw_sha256,
        )

    expected_addresses = set(predecessor_by_address) | set(_SUCCESSOR_RECORDS)
    actual_addresses = set(successor_by_address)
    unexpected = actual_addresses - expected_addresses
    if unexpected:
        return _failure(
            source,
            (
                _diagnostic(
                    "ORDERED_MAP_SUCCESSOR_UNEXPECTED_MEMBERSHIP",
                    repr(tuple(sorted(unexpected))),
                ),
            ),
            successor_graph=successor,
            successor_manifest_raw_sha256=successor_manifest_raw_sha256,
        )
    if any(
        address not in successor_by_address
        or not _successor_record_is_exact(successor_by_address[address])
        for address in _SUCCESSOR_RECORDS
    ):
        return _failure(
            source,
            (_diagnostic("ORDERED_MAP_SUCCESSOR_CONTRACT_DRIFT"),),
            successor_graph=successor,
            successor_manifest_raw_sha256=successor_manifest_raw_sha256,
        )

    predecessor_resolution = resolve_ordered_map(source.graph)
    successor_resolution = _resolve_ordered_map_successor(successor)
    projected = theory_projection.project_theory(
        successor, specification=_SUCCESSOR_SPECIFICATION
    )
    diagnostics = (
        predecessor_resolution.diagnostics
        + successor_resolution.diagnostics
        + projected.diagnostics
    )
    if diagnostics or projected.view is None:
        return _failure(
            source,
            diagnostics
            or (_diagnostic("ORDERED_MAP_SUCCESSOR_THEORY_MISSING"),),
            successor_graph=successor,
            successor_manifest_raw_sha256=successor_manifest_raw_sha256,
        )

    stale = tuple(
        StaleEvidence(record.address, "exact-specification-version")
        for record in source.graph.records
        if record.address[0] == "evidence"
    )
    predecessor_acceptable = tuple(
        candidate.realization
        for candidate in predecessor_resolution.candidates
        if candidate.semantic_status == "acceptable"
    )
    successor_acceptable = tuple(
        candidate.realization
        for candidate in successor_resolution.candidates
        if candidate.semantic_status == "acceptable"
    )
    recovery = (
        tuple(sorted(predecessor_acceptable))
        if predecessor_acceptable and not successor_acceptable
        else ()
    )
    observation = OrderedMapMaintenanceObservation(
        source,
        successor,
        successor_manifest_raw_sha256,
        True,
        tuple(sorted(set(_SUCCESSOR_RECORDS))),
        tuple(sorted(stale, key=lambda item: item.address)),
        predecessor_resolution,
        successor_resolution,
        projected.view,
        recovery,
        None,
        (),
    )
    return replace(observation, output=render_ordered_map_maintenance(observation))


def _address_text(address: Address) -> str:
    return "/".join(address)


def render_ordered_map_maintenance(
    observation: OrderedMapMaintenanceObservation,
) -> str:
    """Render one already derived maintenance observation without I/O."""

    if (
        not observation.ok
        or observation.source.graph is None
        or observation.successor_graph is None
        or observation.predecessor_resolution is None
        or observation.successor_resolution is None
        or observation.successor_theory is None
    ):
        raise ValueError("cannot render an incomplete maintenance observation")
    theory = observation.successor_theory
    unclaimed = sum(
        declaration.observation == "unclaimed"
        for declaration in theory.declarations
    )
    lines = [
        "OrderedMap maintenance successor (exact versions; no discovery or execution)",
        f"predecessor graph records: {len(observation.source.graph.records)}",
        f"successor graph records: {len(observation.successor_graph.records)}",
        "added records: "
        + ", ".join(_address_text(item) for item in observation.added_addresses),
        "",
        f"Successor theory: {_address_text(theory.specification)}",
        f"declarations: {len(theory.declarations)}, unclaimed: {unclaimed}",
    ]
    for declaration in theory.declarations:
        content = json.dumps(
            declaration.content, sort_keys=True, separators=(",", ":")
        )
        lines.append(
            f"{declaration.kind} {declaration.declaration_id}: "
            f"observation={declaration.observation} content={content}"
        )
    if observation.successor_resolution.candidates:
        lines.append("Successor semantic resolution:")
        lines.extend(
            f"  {_address_text(candidate.realization)}: "
            f"semantic={candidate.semantic_status}"
            for candidate in observation.successor_resolution.candidates
        )
    else:
        lines.append(
            "Successor semantic resolution: zero exact-version candidates"
        )
    lines.append(
        f"historical predecessor Evidence: {len(observation.stale_evidence)} "
        "(reason=exact-specification-version)"
    )
    lines.append("Recovery candidates (not automatically selected)")
    lines.extend(
        f"  {_address_text(candidate)}"
        for candidate in observation.recovery_candidates
    )
    lines.append(
        "No Evidence migration, latest selection, lineage, refinement, or "
        "compatibility inference."
    )
    return "\n".join(lines) + "\n"


def inspect_ordered_map_maintenance() -> OrderedMapMaintenanceObservation:
    """Inspect the one pinned append-only OrderedMap successor snapshot."""

    source = ordered_map_product.inspect_product_candidate()
    if not source.ok:
        return _failure(source, source.diagnostics)

    manifest_path = _ROOT / _SUCCESSOR_MANIFEST
    manifest = canonical_artifact.inspect_json_artifact(
        manifest_path,
        schema_path=_ROOT / _MANIFEST_SCHEMA,
        expected_raw_sha256=_SUCCESSOR_MANIFEST_RAW_SHA256,
        label="OrderedMap maintenance successor manifest",
    )
    if not manifest.ok:
        return _failure(source, manifest.diagnostics)
    assert manifest.document is not None
    assert manifest.raw_sha256 is not None
    authority = graph.inspect_manifest_document(manifest_path, manifest.document)
    if not authority.ok:
        return _failure(source, authority.diagnostics)
    successor = graph.inspect_manifest_graph(authority)
    if not successor.ok:
        return _failure(
            source,
            successor.diagnostics,
            successor_graph=successor,
            successor_manifest_raw_sha256=manifest.raw_sha256,
        )
    return _observe_ordered_map_maintenance(
        source,
        successor,
        successor_manifest_raw_sha256=manifest.raw_sha256,
    )
