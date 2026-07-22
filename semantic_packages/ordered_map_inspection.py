"""Consumer inspection over one accepted OrderedMap product replay.

The actor accepts no overrides. It authenticates and captures through the O6-G product
wrapper once, then resolves and renders only that detached observation. Rendering does
not discover, read, execute, reproduce, or silently promote realization-scoped
Evidence into Specification assurance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

from scripts import record_check
from semantic_packages import ordered_map_product
from semantic_packages.graph import Address
from semantic_packages.ordered_map_resolution import resolve_ordered_map
from semantic_packages.resolver import (
    ConcernDisposition,
    ProhibitionDisposition,
    ResolutionCandidate,
    ResolutionResult,
)


@dataclass(frozen=True)
class OrderedMapInspectionObservation:
    """Fail-closed structured decision plus its deterministic presentation."""

    source: ordered_map_product.ProductCandidateObservation
    resolution: ResolutionResult | None
    output: str | None
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


class InspectionError(ValueError):
    """The supplied captured product observation cannot be rendered."""


def _address(value: Address) -> str:
    return "/".join(value)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _items(values: Iterable[str]) -> str:
    items = tuple(values)
    return ", ".join(items) if items else "none"


def _evidence_lines(
    label: str,
    addresses: tuple[Address, ...],
    documents: dict[Address, dict],
    *,
    disposition: str,
) -> list[str]:
    if not addresses:
        return [f"    {label} Evidence: none"]
    lines: list[str] = []
    for address in addresses:
        document = documents.get(address, {})
        lines.append(
            f"    {label} Evidence: {_address(address)} "
            f"mechanism={document.get('mechanism', '<missing>')} "
            f"result={document.get('result', '<missing>')} "
            f"review={document.get('reviewState', '<missing>')} "
            f"disposition={disposition}"
        )
    return lines


def _disposition_lines(
    item: ConcernDisposition | ProhibitionDisposition,
    documents: dict[Address, dict],
) -> list[str]:
    if isinstance(item, ConcernDisposition):
        lines = [
            f"  {item.concern}: status={item.status} priority={item.priority} "
            f"blocks={_yes_no(item.blocks)}",
            f"    declarations: {_items(item.declarations)}",
            f"    missing declarations: {_items(item.missing_declarations)}",
        ]
    else:
        lines = [
            f"  prohibition {item.declaration} event={item.event_pattern}: "
            f"status={item.status} blocks={_yes_no(item.blocks)}"
        ]
    lines.append(f"    reasons: {_items(item.reasons)}")
    for label, addresses, disposition in (
        ("supporting", item.supporting_evidence, "selected-applicable"),
        ("challenging", item.challenging_evidence, "selected-applicable"),
        ("inconclusive", item.inconclusive_evidence, "selected-applicable"),
        ("error", item.error_evidence, "selected-applicable"),
        ("inapplicable", item.inapplicable_evidence, "inapplicable"),
        ("unselected", item.unselected_evidence, "unselected"),
    ):
        lines.extend(
            _evidence_lines(
                label,
                addresses,
                documents,
                disposition=disposition,
            )
        )
    lines.extend(
        [f"    assumption: {value}" for value in item.assumptions]
        or ["    assumptions: none"]
    )
    lines.extend(
        [f"    exclusion: {value}" for value in item.exclusions]
        or ["    exclusions: none"]
    )
    return lines


def _candidate_lines(
    candidate: ResolutionCandidate, documents: dict[Address, dict]
) -> list[str]:
    lines = [
        f"{_address(candidate.realization)}: semantic={candidate.semantic_status}"
    ]
    for concern in candidate.concerns:
        lines.extend(_disposition_lines(concern, documents))
    for prohibition in candidate.prohibitions:
        lines.extend(_disposition_lines(prohibition, documents))
    lines.extend(
        (
            "  Directional realization boundary (not semantic acceptance)",
            "    "
            f"direction={candidate.boundary.direction} "
            f"mechanism={candidate.boundary.mechanism} "
            f"direct={_yes_no(candidate.boundary.direct)}",
        )
    )
    return lines


def render_ordered_map_inspection(
    source: ordered_map_product.ProductCandidateObservation,
    resolution: ResolutionResult,
) -> str:
    """Render only already captured and decided values, without I/O."""

    if not source.ok:
        raise InspectionError("product replay is invalid")
    if not resolution.ok:
        raise InspectionError("consumer resolution is invalid")
    if (
        source.authority is None
        or source.graph is None
        or source.theory is None
        or source.publication is None
        or not source.registrations
    ):
        raise InspectionError("product replay omitted a required accepted view")

    authority = source.authority
    theory = source.theory
    documents = {item.address: item.document for item in source.graph.records}
    unclaimed = sum(
        item.observation == "unclaimed" for item in theory.declarations
    )
    lines = [
        "Accepted OrderedMap product authority (no discovery or execution)",
        f"contract: {authority.contract_id}/{authority.contract_version}",
        f"contract canonical SHA-256: {authority.contract_canonical_sha256}",
        f"manifest raw SHA-256: {authority.manifest_raw_sha256}",
        f"graph records: {len(source.graph.records)}",
        f"theory publication records: {len(source.publication.records)}",
    ]
    lines.extend(
        f"package {item.package}: records={len(item.records)}"
        for item in source.registrations
    )
    lines.extend(
        (
            "",
            f"Theory consumer: {_address(theory.specification)}",
            f"theory declarations: {len(theory.declarations)}, unclaimed: {unclaimed}",
        )
    )
    for declaration in theory.declarations:
        content = json.dumps(
            declaration.content, sort_keys=True, separators=(",", ":")
        )
        lines.append(
            f"{declaration.kind} {declaration.declaration_id}: "
            f"observation={declaration.observation} content={content}"
        )
    lines.append(
        "unknown/unclaimed: "
        + _items(f"{kind}/{identifier}" for kind, identifier in theory.unknowns)
    )
    lines.append(
        "contradictions: "
        + _items(_address(address) for address in theory.contradictions)
    )
    lines.extend(("", "Package consumer semantic decisions"))
    for candidate in resolution.candidates:
        lines.extend(_candidate_lines(candidate, documents))
    return "\n".join(lines) + "\n"


def _diagnostic(code: str, message: str | None = None) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, "<ordered-map-inspection>", "#", message)


def inspect_ordered_map() -> OrderedMapInspectionObservation:
    """Inspect and decide the one pinned accepted OrderedMap product candidate."""

    source = ordered_map_product.inspect_product_candidate()
    if not source.ok:
        return OrderedMapInspectionObservation(
            source, None, None, source.diagnostics
        )
    if source.graph is None:
        diagnostic = _diagnostic("ORDERED_MAP_INSPECTION_GRAPH_MISSING")
        return OrderedMapInspectionObservation(source, None, None, (diagnostic,))

    resolution = resolve_ordered_map(source.graph)
    if not resolution.ok:
        return OrderedMapInspectionObservation(
            source, None, None, resolution.diagnostics
        )
    try:
        output = render_ordered_map_inspection(source, resolution)
    except InspectionError as error:
        diagnostic = _diagnostic(
            "ORDERED_MAP_INSPECTION_INVALID_SOURCE", str(error)
        )
        return OrderedMapInspectionObservation(source, None, None, (diagnostic,))
    return OrderedMapInspectionObservation(source, resolution, output, ())
