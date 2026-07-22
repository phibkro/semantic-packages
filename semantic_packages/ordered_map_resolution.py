"""Pure policy resolution for the exact accepted OrderedMap product graph.

The public boundary accepts one already captured graph and closes over the O6-G
accepted selectors and resolver tokens. It does not discover records, execute
implementations, reproduce Evidence, or generalize these bounded mechanics into a
universal policy language. The Stack ``resolve_stack`` entrypoint remains untouched.
"""

from __future__ import annotations

from typing import Any

from scripts import record_check
from semantic_packages.graph import Address, GraphObservation
from semantic_packages.resolver import (
    ProhibitionDisposition,
    ResolutionCandidate,
    ResolutionResult,
    _address,
    _addresses,
    _boundary,
    _claim_targets,
    _concern_disposition,
    _evidence_for_claim,
    _evidence_is_applicable,
    _text_tuple,
    _unique_sorted,
)


_POLICY = ("consumerPolicy", "ordered-map-bounded-policy", "0.1.0")
_PROFILE = ("realizationProfile", "ordered-map-ascii-fold", "0.1.0")
_SPECIFICATION = ("specification", "ordered-map", "0.1.0")
_CAMPAIGN = "bounded-conformance-campaign"
_EFFECT_SCOPE = "adapter-invocation-trace"
_PLAN_CANONICAL_SHA256 = (
    "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a"
)


def _diagnostic(code: str, message: str | None = None) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, "<graph>", "#", message)


def _effect_scope_match(
    evidence: dict[str, Any],
    claim: dict[str, Any],
    realization_document: dict[str, Any],
    *,
    realization: Address,
    declaration: str,
) -> bool:
    proposition = claim.get("proposition")
    provenance = evidence.get("provenance")
    plan = provenance.get("plan") if isinstance(provenance, dict) else None
    adapter = realization_document.get("adapter")
    evidence_adapter = evidence.get("adapter")
    claim_profiles = frozenset(_addresses(claim.get("applicableProfiles")))
    applicability = evidence.get("applicability")
    evidence_profiles = frozenset(
        _addresses(applicability.get("profiles"))
        if isinstance(applicability, dict)
        else ()
    )
    return (
        claim.get("concern") == "effect.conformance"
        and _address(claim.get("subject")) == realization
        and _address(claim.get("governingSpecification")) == _SPECIFICATION
        and claim.get("state") == "active"
        and isinstance(proposition, dict)
        and _address(proposition.get("specification")) == _SPECIFICATION
        and proposition.get("declarationId") == declaration
        and claim_profiles == {_PROFILE}
        and evidence.get("scope") == "realization"
        and _address(evidence.get("specification")) == _SPECIFICATION
        and _address(evidence.get("realization")) == realization
        and evidence.get("mechanism") == _CAMPAIGN
        and evidence_profiles == claim_profiles
        and isinstance(adapter, dict)
        and isinstance(evidence_adapter, dict)
        and evidence_adapter.get("id") == adapter.get("id")
        and evidence_adapter.get("version") == adapter.get("version")
        and isinstance(provenance, dict)
        and provenance.get("declaration") == declaration
        and isinstance(plan, dict)
        and plan.get("canonicalSha256") == _PLAN_CANONICAL_SHA256
    )


def _prohibition_disposition(
    policy_entry: dict[str, Any],
    *,
    specification_document: dict[str, Any],
    realization: Address,
    realization_document: dict[str, Any],
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
    policy_complete = (
        isinstance(proposition, dict)
        and _address(proposition.get("specification")) == _SPECIFICATION
        and isinstance(effect, dict)
        and effect.get("id") == declaration
        and event_pattern in effect.get("forbidden", [])
        and isinstance(accepted_scopes, list)
        and all(isinstance(item, str) for item in accepted_scopes)
    )

    supporting: list[Address] = []
    challenging: list[Address] = []
    inconclusive: list[Address] = []
    errored: list[Address] = []
    inapplicable: list[Address] = []
    unselected: list[Address] = []
    reasons: list[str] = []
    assumptions: list[str] = []
    exclusions: list[str] = []
    if policy_complete:
        target_claims = tuple(
            (address, document)
            for address, document in documents
            if _claim_targets(
                document,
                realization=realization,
                specification=_SPECIFICATION,
                concern="effect.conformance",
                declaration=declaration,
            )
        )
        claims = tuple(
            (address, document)
            for address, document in target_claims
            if document.get("state") == "active"
            and _PROFILE in _addresses(document.get("applicableProfiles"))
        )
        if not target_claims:
            reasons.append("missing-claim")
        elif not claims:
            reasons.append("inapplicable-claim")
        for claim_address, claim_document in target_claims:
            claim_selected = (claim_address, claim_document) in claims
            linked = _evidence_for_claim(documents, claim_address)
            if claim_selected and not linked:
                reasons.append("absent-evidence")
            for evidence_address, evidence_document in linked:
                if not claim_selected or not _evidence_is_applicable(
                    evidence_document, profile=_PROFILE
                ):
                    inapplicable.append(evidence_address)
                    reasons.append("inapplicable-evidence")
                    continue
                if evidence_document.get("reviewState") != "accepted":
                    unselected.append(evidence_address)
                    reasons.append("unaccepted-review-state")
                    continue
                if _EFFECT_SCOPE not in accepted_scopes:
                    unselected.append(evidence_address)
                    reasons.append(
                        "accept-none-scope"
                        if not accepted_scopes
                        else "unaccepted-scope-token"
                    )
                    continue
                if not _effect_scope_match(
                    evidence_document,
                    claim_document,
                    realization_document,
                    realization=realization,
                    declaration=declaration,
                ):
                    unselected.append(evidence_address)
                    reasons.append(
                        "unacceptable-mechanism"
                        if evidence_document.get("mechanism") != _CAMPAIGN
                        else "unaccepted-scope"
                    )
                    continue
                result = evidence_document.get("result")
                if result == "supports":
                    supporting.append(evidence_address)
                elif result == "challenges":
                    challenging.append(evidence_address)
                elif result == "inconclusive":
                    inconclusive.append(evidence_address)
                    reasons.append("inconclusive-evidence")
                elif result == "error":
                    errored.append(evidence_address)
                    reasons.append("error-evidence")
                assumptions.extend(_text_tuple(claim_document.get("assumptions")))
                assumptions.extend(_text_tuple(evidence_document.get("assumptions")))
                exclusions.extend(_text_tuple(claim_document.get("exclusions")))
                exclusions.extend(_text_tuple(evidence_document.get("exclusions")))

    if not policy_complete:
        status = "policy-incomplete"
        reasons.append("policy-scope-incomplete")
    elif challenging:
        status = "contested"
    elif not supporting:
        status = "unsupported"
    else:
        status = "satisfied"
    return ProhibitionDisposition(
        declaration,
        event_pattern,
        status,
        status != "satisfied",
        _unique_sorted(supporting),
        _unique_sorted(challenging),
        _unique_sorted(inconclusive),
        _unique_sorted(errored),
        _unique_sorted(inapplicable),
        _unique_sorted(unselected),
        _unique_sorted(reasons),
        _unique_sorted(assumptions),
        _unique_sorted(exclusions),
    )


def resolve_ordered_map(observation: GraphObservation) -> ResolutionResult:
    """Resolve the exact accepted OrderedMap selectors from a detached graph."""

    if not observation.ok:
        return ResolutionResult(
            (), (_diagnostic("ORDERED_MAP_RESOLUTION_INVALID_GRAPH"),)
        )

    documents = tuple(
        (record.address, record.document) for record in observation.records
    )
    by_address = {address: document for address, document in documents}
    for selector, expected_kind in (
        (_POLICY, "consumerPolicy"),
        (_PROFILE, "realizationProfile"),
        (_SPECIFICATION, "specification"),
    ):
        document = by_address.get(selector)
        if document is None:
            return ResolutionResult(
                (),
                (
                    _diagnostic(
                        "ORDERED_MAP_RESOLUTION_SELECTOR_NOT_FOUND", repr(selector)
                    ),
                ),
            )
        if selector[0] != expected_kind or document.get("kind") != expected_kind:
            return ResolutionResult(
                (),
                (
                    _diagnostic(
                        "ORDERED_MAP_RESOLUTION_SELECTOR_KIND", repr(selector)
                    ),
                ),
            )

    policy_document = by_address[_POLICY]
    specification_document = by_address[_SPECIFICATION]
    if (
        _address(policy_document.get("specification")) != _SPECIFICATION
        or _address(policy_document.get("profile")) != _PROFILE
    ):
        return ResolutionResult(
            (),
            (
                _diagnostic(
                    "ORDERED_MAP_RESOLUTION_POLICY_SELECTOR_MISMATCH"
                ),
            ),
        )

    candidates: list[ResolutionCandidate] = []
    for realization, realization_document in documents:
        if (
            realization_document.get("kind") != "realization"
            or _address(realization_document.get("specification")) != _SPECIFICATION
            or _PROFILE
            not in _addresses(realization_document.get("supportedProfiles"))
        ):
            continue
        concerns = tuple(
            _concern_disposition(
                entry,
                specification_document=specification_document,
                specification=_SPECIFICATION,
                profile=_PROFILE,
                realization=realization,
                documents=documents,
            )
            for entry in policy_document.get("concerns", [])
            if isinstance(entry, dict)
        )
        prohibitions = tuple(
            _prohibition_disposition(
                entry,
                specification_document=specification_document,
                realization=realization,
                realization_document=realization_document,
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
