"""Proposal-local structural inspection for two exact Specifications.

The functions in this module compare only explicitly mapped declaration documents.
They do not infer lineage, resolve packages, interpret hosted semantics, or establish
semantic refinement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


FAMILIES = (
    "carriers",
    "operations",
    "observations",
    "derivedObservations",
    "equivalences",
    "laws",
    "effects",
    "resources",
    "performancePropositions",
)


@dataclass(frozen=True)
class ProposalProblem:
    code: str
    pointer: str
    message: str


def declaration_index(document: Mapping[str, Any]) -> dict[tuple[str, str], Any]:
    """Index schema-valid declarations by their specification-local address."""

    result: dict[tuple[str, str], Any] = {}
    for family in FAMILIES:
        values = document.get(family, [])
        if isinstance(values, dict):
            values = [values]
        for value in values:
            result[(family, value["id"])] = value
    return result


def _reference(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, dict) or set(value) != {"family", "localId"}:
        return None
    family = value.get("family")
    local_id = value.get("localId")
    if not isinstance(family, str) or not family:
        return None
    if not isinstance(local_id, str) or not local_id:
        return None
    return family, local_id


def validate_proposal_shape(proposal: Any) -> ProposalProblem | None:
    """Validate the deliberately small reversible `.prefine` surface."""

    if not isinstance(proposal, dict):
        return ProposalProblem("REFINEMENT_PROPOSAL_SHAPE", "#", "proposal must be a table")
    allowed = {
        "kind",
        "id",
        "version",
        "predecessor",
        "successor",
        "mappings",
        "additions",
        "removals",
    }
    unknown = sorted(set(proposal) - allowed)
    if unknown:
        return ProposalProblem(
            "REFINEMENT_PROPOSAL_SHAPE",
            "#",
            f"unknown proposal field {unknown[0]}",
        )
    for key, expected in (("kind", "refinement-proposal"),):
        if proposal.get(key) != expected:
            return ProposalProblem(
                "REFINEMENT_PROPOSAL_SHAPE", f"#/{key}", f"must equal {expected}"
            )
    for key in ("id", "version"):
        if not isinstance(proposal.get(key), str) or not proposal[key]:
            return ProposalProblem(
                "REFINEMENT_PROPOSAL_SHAPE", f"#/{key}", "must be a nonempty string"
            )
    for side in ("predecessor", "successor"):
        value = proposal.get(side)
        if not isinstance(value, dict) or set(value) != {
            "kind",
            "id",
            "version",
            "rawSha256",
        }:
            return ProposalProblem(
                "REFINEMENT_PROPOSAL_SHAPE",
                f"#/{side}",
                "must contain exactly kind, id, version, and rawSha256",
            )
        for field in ("kind", "id", "version", "rawSha256"):
            if not isinstance(value.get(field), str) or not value[field]:
                return ProposalProblem(
                    "REFINEMENT_PROPOSAL_SHAPE",
                    f"#/{side}/{field}",
                    "must be a nonempty string",
                )
    for collection, member in (
        ("mappings", None),
        ("additions", "successor"),
        ("removals", "predecessor"),
    ):
        values = proposal.get(collection, [])
        if not isinstance(values, list):
            return ProposalProblem(
                "REFINEMENT_PROPOSAL_SHAPE", f"#/{collection}", "must be an array"
            )
        for index, value in enumerate(values):
            required = {"predecessor", "successor"} if member is None else {member}
            if not isinstance(value, dict) or set(value) != required:
                return ProposalProblem(
                    "REFINEMENT_PROPOSAL_SHAPE",
                    f"#/{collection}/{index}",
                    f"must contain exactly {', '.join(sorted(required))}",
                )
            for reference_name in required:
                if _reference(value[reference_name]) is None:
                    return ProposalProblem(
                        "REFINEMENT_PROPOSAL_SHAPE",
                        f"#/{collection}/{index}/{reference_name}",
                        "must contain exactly nonempty family and localId strings",
                    )
    return None


def inspect_proposal(
    proposal: Mapping[str, Any],
    predecessor: Mapping[str, Any],
    successor: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, ProposalProblem | None]:
    """Inspect one already shape-validated proposal against exact documents."""

    predecessor_declarations = declaration_index(predecessor)
    successor_declarations = declaration_index(successor)
    mapped_predecessors: list[tuple[str, str]] = []
    mapped_successors: list[tuple[str, str]] = []
    additions: list[tuple[str, str]] = []
    removals: list[tuple[str, str]] = []

    mappings = proposal.get("mappings", [])
    for index, mapping in enumerate(mappings):
        left = _reference(mapping["predecessor"])
        right = _reference(mapping["successor"])
        assert left is not None and right is not None
        if left not in predecessor_declarations:
            return None, ProposalProblem(
                "REFINEMENT_REFERENCE",
                f"#/mappings/{index}/predecessor",
                f"predecessor declaration {left[0]}/{left[1]} does not exist",
            )
        if right not in successor_declarations:
            return None, ProposalProblem(
                "REFINEMENT_REFERENCE",
                f"#/mappings/{index}/successor",
                f"successor declaration {right[0]}/{right[1]} does not exist",
            )
        if left[0] != right[0]:
            return None, ProposalProblem(
                "REFINEMENT_FAMILY",
                f"#/mappings/{index}",
                f"mapping crosses declaration families {left[0]} and {right[0]}",
            )
        mapped_predecessors.append(left)
        mapped_successors.append(right)

    for collection, side, declarations, target in (
        ("additions", "successor", successor_declarations, additions),
        ("removals", "predecessor", predecessor_declarations, removals),
    ):
        for index, item in enumerate(proposal.get(collection, [])):
            reference = _reference(item[side])
            assert reference is not None
            if reference not in declarations:
                return None, ProposalProblem(
                    "REFINEMENT_REFERENCE",
                    f"#/{collection}/{index}/{side}",
                    f"{side} declaration {reference[0]}/{reference[1]} does not exist",
                )
            target.append(reference)

    duplicate_groups = (
        ("mapped predecessor", mapped_predecessors),
        ("mapped successor", mapped_successors),
        ("addition", additions),
        ("removal", removals),
    )
    for label, values in duplicate_groups:
        if len(values) != len(set(values)):
            return None, ProposalProblem(
                "REFINEMENT_DUPLICATE", "#", f"duplicate {label} disposition"
            )
    if set(mapped_predecessors) & set(removals):
        return None, ProposalProblem(
            "REFINEMENT_OVERLAP", "#", "a predecessor is both mapped and removed"
        )
    if set(mapped_successors) & set(additions):
        return None, ProposalProblem(
            "REFINEMENT_OVERLAP", "#", "a successor is both mapped and added"
        )
    if set(mapped_predecessors) | set(removals) != set(predecessor_declarations):
        return None, ProposalProblem(
            "REFINEMENT_COVERAGE", "#/predecessor", "predecessor disposition is incomplete"
        )
    if set(mapped_successors) | set(additions) != set(successor_declarations):
        return None, ProposalProblem(
            "REFINEMENT_COVERAGE", "#/successor", "successor disposition is incomplete"
        )

    report_mappings: list[dict[str, Any]] = []
    for mapping, left, right in zip(mappings, mapped_predecessors, mapped_successors):
        report_mappings.append(
            {
                "predecessor": dict(mapping["predecessor"]),
                "successor": dict(mapping["successor"]),
                "documentRelation": (
                    "document-unchanged"
                    if predecessor_declarations[left] == successor_declarations[right]
                    else "document-changed"
                ),
            }
        )
    report = {
        "kind": "refinement-inspection-v1",
        "proposal": {"id": proposal["id"], "version": proposal["version"]},
        "predecessor": dict(proposal["predecessor"]),
        "successor": dict(proposal["successor"]),
        "mappings": report_mappings,
        "additions": [dict(item["successor"]) for item in proposal.get("additions", [])],
        "removals": [dict(item["predecessor"]) for item in proposal.get("removals", [])],
        "semanticRefinement": "unestablished",
    }
    return report, None
