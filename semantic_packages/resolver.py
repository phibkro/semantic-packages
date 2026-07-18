"""Pure, bounded policy resolution over a captured Stack product graph.

This module intentionally resolves only the exact Stack tracer semantics frozen by
ADR 0013.  It does not discover records, execute implementations, reproduce evidence,
or generalize the tracer's assurance and observation-scope tokens into a universal
policy language.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from scripts import record_check
from semantic_packages.graph import Address, GraphObservation


_ASSURANCE = (
    "per-declaration-one-accepted-applicable-support-no-selected-challenge"
)
_CAMPAIGN = "bounded-conformance-campaign"
_EFFECT_SCOPE = "adapter-invocation-trace"
_WAVE4_PLAN_SHA256 = (
    "e055eab406683a01a32e8b563ef2e299169ddb2745685b5ad3ffae3297d93f6c"
)
_NDJSON_INTERFACE = "NDJSON messages over stdin and stdout"


@dataclass(frozen=True)
class ConcernDisposition:
    concern: str
    priority: str
    status: str
    blocks: bool
    declarations: tuple[str, ...]
    missing_declarations: tuple[str, ...]
    supporting_evidence: tuple[Address, ...]
    challenging_evidence: tuple[Address, ...]
    inconclusive_evidence: tuple[Address, ...]
    error_evidence: tuple[Address, ...]
    inapplicable_evidence: tuple[Address, ...]
    unselected_evidence: tuple[Address, ...]
    reasons: tuple[str, ...]
    assumptions: tuple[str, ...]
    exclusions: tuple[str, ...]


@dataclass(frozen=True)
class ProhibitionDisposition:
    declaration: str
    event_pattern: str
    status: str
    blocks: bool
    supporting_evidence: tuple[Address, ...]
    challenging_evidence: tuple[Address, ...]
    inconclusive_evidence: tuple[Address, ...]
    error_evidence: tuple[Address, ...]
    inapplicable_evidence: tuple[Address, ...]
    unselected_evidence: tuple[Address, ...]
    reasons: tuple[str, ...]
    assumptions: tuple[str, ...]
    exclusions: tuple[str, ...]


@dataclass(frozen=True)
class RealizationBoundary:
    direction: str
    mechanism: str
    direct: bool


@dataclass(frozen=True)
class ResolutionCandidate:
    realization: Address
    semantic_status: str
    concerns: tuple[ConcernDisposition, ...]
    prohibitions: tuple[ProhibitionDisposition, ...]
    boundary: RealizationBoundary


@dataclass(frozen=True)
class ResolutionResult:
    candidates: tuple[ResolutionCandidate, ...]
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        """Whether resolution inputs were usable; candidates may still be rejected."""

        return not self.diagnostics


def _diagnostic(code: str, message: str | None = None) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, "<graph>", "#", message)


def _address(value: Any) -> Address | None:
    if not isinstance(value, dict):
        return None
    parts = (value.get("kind"), value.get("id"), value.get("version"))
    if not all(isinstance(part, str) for part in parts):
        return None
    return parts  # type: ignore[return-value]


def _addresses(values: Any) -> tuple[Address, ...]:
    if not isinstance(values, list):
        return ()
    return tuple(
        address
        for value in values
        if (address := _address(value)) is not None
    )


def _text_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _unique_sorted(values: Iterable[Any]) -> tuple[Any, ...]:
    return tuple(sorted(set(values)))


def _covered_declarations(specification: dict[str, Any], concern: str) -> tuple[str, ...] | None:
    if concern == "law.conformance":
        declarations = specification.get("laws", [])
    elif concern == "resource.persistence":
        declarations = specification.get("resources", [])
    elif concern == "effect.conformance":
        effect = specification.get("effects")
        declarations = [effect] if isinstance(effect, dict) else []
    elif concern == "performance":
        declarations = specification.get("performancePropositions", [])
    else:
        return None
    if not isinstance(declarations, list):
        return ()
    return tuple(
        item["id"]
        for item in declarations
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    )


def _claim_targets(
    document: dict[str, Any],
    *,
    realization: Address,
    specification: Address,
    concern: str,
    declaration: str,
) -> bool:
    proposition = document.get("proposition")
    return (
        document.get("kind") == "claim"
        and _address(document.get("subject")) == realization
        and _address(document.get("governingSpecification")) == specification
        and document.get("concern") == concern
        and isinstance(proposition, dict)
        and _address(proposition.get("specification")) == specification
        and proposition.get("declarationId") == declaration
    )


def _evidence_is_applicable(
    document: dict[str, Any], *, profile: Address
) -> bool:
    applicability = document.get("applicability")
    return (
        isinstance(applicability, dict)
        and profile in _addresses(applicability.get("profiles"))
    )


def _evidence_for_claim(
    documents: Iterable[tuple[Address, dict[str, Any]]],
    claim: Address,
) -> tuple[tuple[Address, dict[str, Any]], ...]:
    return tuple(
        (address, document)
        for address, document in documents
        if document.get("kind") == "evidence"
        and _address(document.get("claim")) == claim
    )


def _concern_disposition(
    policy_entry: dict[str, Any],
    *,
    specification_document: dict[str, Any],
    specification: Address,
    profile: Address,
    realization: Address,
    documents: tuple[tuple[Address, dict[str, Any]], ...],
) -> ConcernDisposition:
    concern = policy_entry.get("concern", "<invalid>")
    priority = policy_entry.get("priority", "required")
    declarations = _covered_declarations(specification_document, concern)
    mechanisms = policy_entry.get("acceptedMechanisms")
    policy_complete = (
        declarations is not None
        and isinstance(mechanisms, list)
        and all(isinstance(item, str) for item in mechanisms)
        and policy_entry.get("minimumAssurance") == _ASSURANCE
    )
    blocks = priority == "required"
    if not policy_complete:
        incomplete_reason = (
            "mechanism-unspecified"
            if not isinstance(mechanisms, list)
            else "assurance-unspecified"
        )
        return ConcernDisposition(
            concern=concern,
            priority=priority,
            status="policy-incomplete",
            blocks=blocks,
            declarations=declarations or (),
            missing_declarations=declarations or (),
            supporting_evidence=(),
            challenging_evidence=(),
            inconclusive_evidence=(),
            error_evidence=(),
            inapplicable_evidence=(),
            unselected_evidence=(),
            reasons=(incomplete_reason,),
            assumptions=(),
            exclusions=(),
        )

    accepted_mechanisms = frozenset(mechanisms)
    if not declarations:
        return ConcernDisposition(
            concern=concern,
            priority=priority,
            status="no-coverage",
            blocks=blocks,
            declarations=(),
            missing_declarations=(),
            supporting_evidence=(),
            challenging_evidence=(),
            inconclusive_evidence=(),
            error_evidence=(),
            inapplicable_evidence=(),
            unselected_evidence=(),
            reasons=("no-declarations",),
            assumptions=(),
            exclusions=(),
        )

    missing: list[str] = []
    supporting: list[Address] = []
    challenging: list[Address] = []
    inconclusive: list[Address] = []
    errored: list[Address] = []
    inapplicable: list[Address] = []
    unselected: list[Address] = []
    reasons: list[str] = []
    assumptions: list[str] = []
    exclusions: list[str] = []
    if not accepted_mechanisms:
        reasons.append("accept-none")

    for declaration in declarations:
        target_claims = tuple(
            (address, document)
            for address, document in documents
            if _claim_targets(
                document,
                realization=realization,
                specification=specification,
                concern=concern,
                declaration=declaration,
            )
        )
        claims = tuple(
            (address, document)
            for address, document in target_claims
            if document.get("state") == "active"
            and profile in _addresses(document.get("applicableProfiles"))
        )
        declaration_supports: list[Address] = []
        declaration_challenges: list[Address] = []
        for claim_address, claim_document in target_claims:
            claim_selected = (claim_address, claim_document) in claims
            linked = _evidence_for_claim(documents, claim_address)
            if claim_selected and not linked:
                reasons.append("absent-evidence")
            for evidence_address, evidence_document in linked:
                if not claim_selected or not _evidence_is_applicable(
                    evidence_document, profile=profile
                ):
                    inapplicable.append(evidence_address)
                    reasons.append("inapplicable-evidence")
                    continue
                if evidence_document.get("reviewState") != "accepted":
                    unselected.append(evidence_address)
                    reasons.append("unaccepted-review-state")
                    continue
                if evidence_document.get("mechanism") not in accepted_mechanisms:
                    unselected.append(evidence_address)
                    reasons.append("unacceptable-mechanism")
                    continue
                result = evidence_document.get("result")
                if result == "supports":
                    declaration_supports.append(evidence_address)
                elif result == "challenges":
                    declaration_challenges.append(evidence_address)
                elif result == "inconclusive":
                    inconclusive.append(evidence_address)
                    reasons.append("inconclusive-evidence")
                elif result == "error":
                    errored.append(evidence_address)
                    reasons.append("error-evidence")
                assumptions.extend(_text_tuple(evidence_document.get("assumptions")))
                exclusions.extend(_text_tuple(evidence_document.get("exclusions")))
            if claim_selected:
                assumptions.extend(_text_tuple(claim_document.get("assumptions")))
                exclusions.extend(_text_tuple(claim_document.get("exclusions")))
        supporting.extend(declaration_supports)
        challenging.extend(declaration_challenges)
        if not claims or not declaration_supports:
            missing.append(declaration)
        if not target_claims:
            reasons.append("missing-claim")
        elif not claims:
            reasons.append("inapplicable-claim")

    if challenging:
        status = "contested"
    elif missing:
        status = "unsupported"
    else:
        status = "satisfied"
    return ConcernDisposition(
        concern,
        priority,
        status,
        blocks and status != "satisfied",
        declarations,
        _unique_sorted(missing),
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


def _effect_scope_match(
    evidence: dict[str, Any],
    claim: dict[str, Any],
    realization_document: dict[str, Any],
    *,
    specification: Address,
    realization: Address,
    profile: Address,
    declaration: str,
) -> bool:
    proposition = claim.get("proposition")
    provenance = evidence.get("provenance")
    adapter = realization_document.get("adapter")
    evidence_adapter = evidence.get("adapter")
    claim_profiles = frozenset(_addresses(claim.get("applicableProfiles")))
    evidence_applicability = evidence.get("applicability")
    evidence_profiles = frozenset(
        _addresses(evidence_applicability.get("profiles"))
        if isinstance(evidence_applicability, dict)
        else ()
    )
    return (
        claim.get("concern") == "effect.conformance"
        and _address(claim.get("subject")) == realization
        and _address(claim.get("governingSpecification")) == specification
        and claim.get("state") == "active"
        and isinstance(proposition, dict)
        and _address(proposition.get("specification")) == specification
        and proposition.get("declarationId") == declaration
        and claim_profiles == {profile}
        and evidence.get("scope") == "realization"
        and _address(evidence.get("specification")) == specification
        and _address(evidence.get("realization")) == realization
        and evidence.get("mechanism") == _CAMPAIGN
        and evidence_profiles == claim_profiles
        and isinstance(adapter, dict)
        and isinstance(evidence_adapter, dict)
        and evidence_adapter.get("id") == adapter.get("id")
        and evidence_adapter.get("version") == adapter.get("version")
        and isinstance(provenance, dict)
        and provenance.get("declaration") == declaration
        and provenance.get("planSha256") == _WAVE4_PLAN_SHA256
    )


def _prohibition_disposition(
    policy_entry: dict[str, Any],
    *,
    specification_document: dict[str, Any],
    specification: Address,
    profile: Address,
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
        and _address(proposition.get("specification")) == specification
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
                specification=specification,
                concern="effect.conformance",
                declaration=declaration,
            )
        )
        claims = tuple(
            (address, document)
            for address, document in target_claims
            if document.get("state") == "active"
            and profile in _addresses(document.get("applicableProfiles"))
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
                if (
                    not claim_selected
                    or not _evidence_is_applicable(evidence_document, profile=profile)
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
                        specification=specification,
                        realization=realization,
                        profile=profile,
                        declaration=declaration,
                    ):
                    unselected.append(evidence_address)
                    if evidence_document.get("mechanism") != _CAMPAIGN:
                        reasons.append("unacceptable-mechanism")
                    else:
                        reasons.append("unaccepted-scope")
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


def _boundary(realization: dict[str, Any]) -> RealizationBoundary:
    implementation = realization.get("implementation")
    mechanism = (
        implementation.get("interfaceMechanism")
        if isinstance(implementation, dict)
        else None
    )
    if mechanism == _NDJSON_INTERFACE:
        return RealizationBoundary(
            direction="consumer-to-realization",
            mechanism="child-process-ndjson",
            direct=False,
        )
    return RealizationBoundary(
        direction="consumer-to-realization",
        mechanism="unsupported-interface",
        direct=False,
    )


def resolve_stack(
    graph: GraphObservation,
    *,
    policy: Address,
    profile: Address,
    specification: Address,
) -> ResolutionResult:
    """Resolve exact Stack candidates from one already captured graph snapshot."""

    if not graph.ok:
        return ResolutionResult((), (_diagnostic("RESOLUTION_INVALID_GRAPH"),))

    documents = tuple((record.address, record.document) for record in graph.records)
    by_address = {address: document for address, document in documents}
    selectors = (
        (policy, "consumerPolicy"),
        (profile, "realizationProfile"),
        (specification, "specification"),
    )
    for selector, expected_kind in selectors:
        document = by_address.get(selector)
        if document is None:
            return ResolutionResult(
                (),
                (_diagnostic("RESOLUTION_SELECTOR_NOT_FOUND", repr(selector)),),
            )
        if selector[0] != expected_kind or document.get("kind") != expected_kind:
            return ResolutionResult(
                (),
                (_diagnostic("RESOLUTION_SELECTOR_KIND", repr(selector)),),
            )

    policy_document = by_address[policy]
    specification_document = by_address[specification]
    if (
        _address(policy_document.get("specification")) != specification
        or _address(policy_document.get("profile")) != profile
    ):
        return ResolutionResult(
            (),
            (_diagnostic("RESOLUTION_POLICY_SELECTOR_MISMATCH"),),
        )

    candidates: list[ResolutionCandidate] = []
    for realization, realization_document in documents:
        if (
            realization_document.get("kind") != "realization"
            or _address(realization_document.get("specification")) != specification
            or profile not in _addresses(realization_document.get("supportedProfiles"))
        ):
            continue
        raw_concerns = policy_document.get("concerns", [])
        concerns = tuple(
            _concern_disposition(
                entry,
                specification_document=specification_document,
                specification=specification,
                profile=profile,
                realization=realization,
                documents=documents,
            )
            for entry in raw_concerns
            if isinstance(entry, dict)
        )
        raw_prohibitions = policy_document.get("prohibitions", [])
        prohibitions = tuple(
            _prohibition_disposition(
                entry,
                specification_document=specification_document,
                specification=specification,
                profile=profile,
                realization=realization,
                realization_document=realization_document,
                documents=documents,
            )
            for entry in raw_prohibitions
            if isinstance(entry, dict)
        )
        unacceptable = any(item.blocks for item in concerns) or any(
            item.blocks for item in prohibitions
        )
        candidates.append(
            ResolutionCandidate(
                realization=realization,
                semantic_status="unacceptable" if unacceptable else "acceptable",
                concerns=concerns,
                prohibitions=prohibitions,
                boundary=_boundary(realization_document),
            )
        )

    return ResolutionResult(tuple(sorted(candidates, key=lambda item: item.realization)), ())
