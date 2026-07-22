"""Human-readable inspection for the exact bounded Stack tracer.

This module composes already captured graph, resolution, theory, and maintenance
observations. It does not discover records, select latest versions, execute artifacts,
reproduce Evidence, or infer semantics beyond those observations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from semantic_packages import maintenance
from semantic_packages.graph import Address, GraphObservation, inspect_stack_graph
from semantic_packages.resolver import (
    ConcernDisposition,
    ProhibitionDisposition,
    ResolutionCandidate,
)


class InspectionError(ValueError):
    """The exact captured inputs cannot produce the requested inspection."""


def _address(address: Address) -> str:
    return "/".join(address)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _items(values: Iterable[str]) -> str:
    items = tuple(values)
    return ", ".join(items) if items else "none"


def _diagnostics(observation: maintenance.SuccessorInspection) -> str:
    return "\n".join(item.format() for item in observation.diagnostics)


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


def _qualification_lines(
    assumptions: tuple[str, ...], exclusions: tuple[str, ...]
) -> list[str]:
    lines = (
        [f"    assumption: {item}" for item in assumptions]
        or ["    assumptions: none"]
    )
    lines.extend(
        [f"    exclusion: {item}" for item in exclusions]
        or ["    exclusions: none"]
    )
    return lines


def _disposition_lines(
    item: ConcernDisposition | ProhibitionDisposition,
    documents: dict[Address, dict],
) -> list[str]:
    lines: list[str] = []
    if isinstance(item, ConcernDisposition):
        lines.append(
            f"  {item.concern}: status={item.status} priority={item.priority} "
            f"blocks={_yes_no(item.blocks)}"
        )
        lines.append(f"    declarations: {_items(item.declarations)}")
        lines.append(
            f"    missing declarations: {_items(item.missing_declarations)}"
        )
    else:
        lines.append(
            f"  prohibition {item.declaration} event={item.event_pattern}: "
            f"status={item.status} blocks={_yes_no(item.blocks)}"
        )
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
                label, addresses, documents, disposition=disposition
            )
        )
    lines.extend(_qualification_lines(item.assumptions, item.exclusions))
    return lines


def _candidate_lines(
    candidate: ResolutionCandidate, documents: dict[Address, dict]
) -> list[str]:
    lines = [f"{_address(candidate.realization)}: semantic={candidate.semantic_status}"]
    for concern in candidate.concerns:
        lines.extend(_disposition_lines(concern, documents))
    for prohibition in candidate.prohibitions:
        lines.extend(_disposition_lines(prohibition, documents))
    lines.append(
        "  boundary: "
        f"direction={candidate.boundary.direction} "
        f"mechanism={candidate.boundary.mechanism} "
        f"direct={_yes_no(candidate.boundary.direct)}"
    )
    return lines


def render_stack_inspection(
    predecessor: GraphObservation,
    successor: GraphObservation,
    *,
    profile: Address,
    predecessor_specification: Address,
    successor_specification: Address,
    predecessor_policy: Address,
    successor_policy: Address,
) -> str:
    """Render exact Stack observations without performing I/O or execution."""

    observation = maintenance.inspect_stack_successor(
        predecessor,
        successor,
        predecessor_policy=predecessor_policy,
        successor_policy=successor_policy,
        profile=profile,
        predecessor_specification=predecessor_specification,
        successor_specification=successor_specification,
    )
    if not observation.ok:
        raise InspectionError(_diagnostics(observation))

    theory = observation.predecessor_theory.view
    if theory is None:
        raise InspectionError("predecessor theory projection has no view")
    documents = {record.address: record.document for record in successor.records}
    lines = [
        "Exact inputs (no discovery, latest selection, or artifact execution)",
        f"predecessor graph records: {len(predecessor.records)}",
        f"successor graph records: {len(successor.records)}",
        f"profile: {_address(profile)}",
        f"predecessor specification: {_address(predecessor_specification)}",
        f"successor specification: {_address(successor_specification)}",
        f"predecessor policy: {_address(predecessor_policy)}",
        f"successor policy: {_address(successor_policy)}",
        "",
        f"Theory meaning: {_address(theory.specification)}",
        f"imports: {_items(_address(item.specification) for item in theory.imports)}",
    ]
    for declaration in theory.declarations:
        content = json.dumps(
            declaration.content, sort_keys=True, separators=(",", ":")
        )
        lines.append(
            f"{declaration.kind} {declaration.declaration_id}: "
            f"observation={declaration.observation} content={content}"
        )
        for claim in declaration.claims:
            lines.append(
                f"  claim {_address(claim.address)} concern={claim.concern} "
                f"state={claim.state}"
            )
            lines.extend(
                f"    assumption: {assumption}" for assumption in claim.assumptions
            )
            lines.extend(
                f"    exclusion: {exclusion}" for exclusion in claim.exclusions
            )
            for evidence in claim.evidence:
                lines.append(
                    f"    Evidence {_address(evidence.address)} "
                    f"mechanism={evidence.mechanism} result={evidence.result} "
                    f"review={evidence.review_state}"
                )
                lines.extend(
                    f"      Evidence assumption: {assumption}"
                    for assumption in evidence.assumptions
                )
                lines.extend(
                    f"      Evidence exclusion: {exclusion}"
                    for exclusion in evidence.exclusions
                )
    lines.append(
        "unknown/unclaimed: "
        + _items(f"{kind}/{identifier}" for kind, identifier in theory.unknowns)
    )
    lines.append(
        "contradictions: " + _items(_address(item) for item in theory.contradictions)
    )
    lines.extend(("", "Predecessor semantic resolution"))
    for candidate in observation.predecessor_resolution.candidates:
        lines.extend(_candidate_lines(candidate, documents))
    lines.extend(("", "Failed successor"))
    for candidate in observation.successor_resolution.candidates:
        lines.extend(_candidate_lines(candidate, documents))

    reasons = sorted({item.reason for item in observation.stale_evidence})
    reason = reasons[0] if len(reasons) == 1 else _items(reasons)
    lines.append(
        f"stale Evidence: {len(observation.stale_evidence)} (reason={reason})"
    )
    for item in observation.stale_evidence:
        lines.append(f"  {_address(item.address)} reason={item.reason}")
    lines.append("recovery candidates (not automatically selected):")
    if observation.recovery_candidates:
        lines.extend(
            f"  {_address(candidate)}"
            for candidate in observation.recovery_candidates
        )
    else:
        lines.append("  none")
    return "\n".join(lines) + "\n"


def _exact_address(value: str) -> Address:
    parts = value.split("/")
    if len(parts) != 3 or not all(parts):
        raise argparse.ArgumentTypeError(
            f"expected exact address KIND/ID/VERSION, got {value!r}"
        )
    return parts[0], parts[1], parts[2]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect two exact bounded Stack graph snapshots."
    )
    parser.add_argument("--predecessor-manifest", required=True, type=Path)
    parser.add_argument("--successor-manifest", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=_exact_address)
    parser.add_argument(
        "--predecessor-specification", required=True, type=_exact_address
    )
    parser.add_argument(
        "--successor-specification", required=True, type=_exact_address
    )
    parser.add_argument("--predecessor-policy", required=True, type=_exact_address)
    parser.add_argument("--successor-policy", required=True, type=_exact_address)
    return parser


def main(arguments: list[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    predecessor = inspect_stack_graph(args.predecessor_manifest)
    successor = inspect_stack_graph(args.successor_manifest)
    try:
        output = render_stack_inspection(
            predecessor,
            successor,
            profile=args.profile,
            predecessor_specification=args.predecessor_specification,
            successor_specification=args.successor_specification,
            predecessor_policy=args.predecessor_policy,
            successor_policy=args.successor_policy,
        )
    except InspectionError as error:
        print(error, file=sys.stderr)
        return 1
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
