"""Exact deployment-profile choice over one authenticated OrderedMap graph.

This actor replays one pinned 69-member authority and makes two closed decisions. It
does not discover versions, infer profile refinement, execute candidates, migrate
Evidence, or call Stack resolution. Runtime direction is rendered separately from
semantic acceptance.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from scripts import record_check
from semantic_packages import canonical_artifact, graph
from semantic_packages.graph import Address, GraphObservation, ManifestAuthority
from semantic_packages.resolver import (
    ProhibitionDisposition,
    ResolutionCandidate,
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


_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = Path("registry/ordered-map/profile-choice-manifest.json")
_MANIFEST_SCHEMA = Path("schemas/registry-manifest.schema.json")
_MANIFEST_RAW_SHA256 = "d6be0eec8439e02434a4f39a021a3c0abcc20f98ff10a02c3749359c1b78f8c7"
_SPECIFICATION = ("specification", "ordered-map", "0.1.0")
_NATIVE_PROFILE = ("realizationProfile", "ordered-map-native-process", "0.1.0")
_DENO_PROFILE = ("realizationProfile", "ordered-map-deno-sandbox", "0.1.0")
_NATIVE_POLICY = (
    "consumerPolicy",
    "ordered-map-native-process-policy",
    "0.1.0",
)
_DENO_POLICY = (
    "consumerPolicy",
    "ordered-map-deno-sandbox-policy",
    "0.1.0",
)
_DECLARATIONS = {
    "lookup-empty": "law.conformance",
    "lookup-put-other": "law.conformance",
    "lookup-put-same": "law.conformance",
    "ordered-map-effects": "effect.conformance",
    "persistence": "resource.persistence",
    "put-existing-position": "law.conformance",
    "put-new-appends": "law.conformance",
}
_PACKAGES = {
    "ordered-map-rust": {
        "realization": ("realization", "ordered-map-rust", "0.2.0"),
        "profile": _NATIVE_PROFILE,
        "policy": _NATIVE_POLICY,
        "plan": {
            "path": "contracts/ordered-map/profile-choice/native-conformance-plan.json",
            "rawSha256": "4ad983583dc4558c9321d3c2b7a8089f7f41aa25e391b5ffeac5875a9a28d932",
            "canonicalSha256": "8cd414cf900f571994e081788cebf5f5c7c73964efd43f7384c2089b1fb0b472",
        },
        "profileBinding": {
            "path": "registry/ordered-map/profile-choice/profiles/records/ordered-map-native-process.json",
            "sha256": "788481758572ec2d94d3e97b009b9ca30e0322d07b93dcb37b6417243fffc450",
        },
        "report": {
            "path": "reports/ordered-map/profile-choice/rust-native-campaign-report.json",
            "sha256": "4cc41ec214054bb0d6174e821fb80678ee8ad8fe72cac362fd01c0e91497bb5c",
        },
        "adapter": {"id": "ordered-map-rust-json-adapter", "version": "0.1.0"},
    },
    "ordered-map-typescript": {
        "realization": ("realization", "ordered-map-typescript", "0.2.0"),
        "profile": _DENO_PROFILE,
        "policy": _DENO_POLICY,
        "plan": {
            "path": "contracts/ordered-map/profile-choice/deno-conformance-plan.json",
            "rawSha256": "bedd5199c9958ea127c77f4f8646a71a282305b88487854cd2ce4338d76ad0d9",
            "canonicalSha256": "57cdeb9d881a272e9c591920cc6bf43d426cbd6310951a99c90797aa91cdb5b4",
        },
        "profileBinding": {
            "path": "registry/ordered-map/profile-choice/profiles/records/ordered-map-deno-sandbox.json",
            "sha256": "4629a98d62ae9ab59bebefcab5eab2306eeef8df0b19f80b6cc594f1f5adb1bf",
        },
        "report": {
            "path": "reports/ordered-map/profile-choice/typescript-deno-campaign-report.json",
            "sha256": "ef597eadb9349223d25533b97e490b6ea1463eabf59116924a470ac76ddfe29c",
        },
        "adapter": {
            "id": "ordered-map-typescript-json-adapter",
            "version": "0.1.0",
        },
    },
}
_DECISION_ORDER = ("ordered-map-rust", "ordered-map-typescript")
_CAMPAIGN = "bounded-conformance-campaign"
_EFFECT_SCOPE = "adapter-invocation-trace"
_ASSURANCE = "per-declaration-one-accepted-applicable-support-no-selected-challenge"
_EXPECTED_CONCERNS = [
    {
        "concern": "law.conformance",
        "priority": "required",
        "acceptedMechanisms": [_CAMPAIGN],
        "minimumAssurance": _ASSURANCE,
    },
    {
        "concern": "resource.persistence",
        "priority": "required",
        "acceptedMechanisms": [_CAMPAIGN],
        "minimumAssurance": _ASSURANCE,
    },
    {
        "concern": "effect.conformance",
        "priority": "required",
        "acceptedMechanisms": [_CAMPAIGN],
        "minimumAssurance": _ASSURANCE,
    },
    {
        "concern": "performance",
        "priority": "optional",
        "acceptedMechanisms": ["proof", "proof-audit"],
        "minimumAssurance": _ASSURANCE,
    },
]
_EXPECTED_PROHIBITIONS = [
    {
        "proposition": {
            "specification": {
                "kind": "specification",
                "id": "ordered-map",
                "version": "0.1.0",
            },
            "declarationId": "ordered-map-effects",
        },
        "description": "No io.* events inside the adapter-observed invocation trace.",
        "eventPattern": "io.*",
        "acceptedEvidenceScope": [_EFFECT_SCOPE],
    }
]


def _address_document(address: Address) -> dict[str, str]:
    return {"kind": address[0], "id": address[1], "version": address[2]}


def _package_addresses(package: str, version: str, kind: str) -> tuple[Address, ...]:
    suffix = "" if kind == "claim" else "-conformance"
    return tuple(
        (kind, f"{package}-{declaration}{suffix}", version)
        for declaration in _DECLARATIONS
    )


_EXPECTED_ADDRESSES = frozenset(
    {
        ("realizationProfile", "ordered-map-ascii-fold", "0.1.0"),
        _NATIVE_PROFILE,
        _DENO_PROFILE,
        _SPECIFICATION,
        ("specification", "ordered-map", "0.2.0"),
        ("consumerPolicy", "ordered-map-bounded-policy", "0.1.0"),
        ("consumerPolicy", "ordered-map-bounded-policy", "0.2.0"),
        _NATIVE_POLICY,
        _DENO_POLICY,
        ("realization", "ordered-map-rust", "0.1.0"),
        ("realization", "ordered-map-typescript", "0.1.0"),
        *(_package_addresses("ordered-map-rust", "0.1.0", "claim")),
        *(_package_addresses("ordered-map-rust", "0.1.0", "evidence")),
        *(_package_addresses("ordered-map-typescript", "0.1.0", "claim")),
        *(_package_addresses("ordered-map-typescript", "0.1.0", "evidence")),
        *(_package_addresses("ordered-map-rust", "0.2.0", "claim")),
        *(_package_addresses("ordered-map-rust", "0.2.0", "evidence")),
        *(_package_addresses("ordered-map-typescript", "0.2.0", "claim")),
        *(_package_addresses("ordered-map-typescript", "0.2.0", "evidence")),
        _PACKAGES["ordered-map-rust"]["realization"],
        _PACKAGES["ordered-map-typescript"]["realization"],
    }
)


@dataclass(frozen=True)
class ApplicabilityLedger:
    selected_applicable: tuple[Address, ...]
    inapplicable: tuple[Address, ...]


@dataclass(frozen=True)
class ProfileChoiceDecision:
    policy: Address
    profile: Address
    candidate: ResolutionCandidate
    claims: ApplicabilityLedger
    evidence: ApplicabilityLedger


@dataclass(frozen=True)
class ProfileChoiceResolution:
    decisions: tuple[ProfileChoiceDecision, ...]
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


@dataclass(frozen=True)
class ProfileChoiceObservation:
    authority: ManifestAuthority
    graph: GraphObservation
    resolution: ProfileChoiceResolution
    output: str | None
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def _diagnostic(code: str, message: str | None = None) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, "<ordered-map-profile-choice>", "#", message)


def _expected_new_record(address: Address):
    for package, contract in _PACKAGES.items():
        realization = contract["realization"]
        if address == realization:
            return package, "realization", None
        for declaration in _DECLARATIONS:
            if address == ("claim", f"{package}-{declaration}", "0.2.0"):
                return package, "claim", declaration
            if address == (
                "evidence",
                f"{package}-{declaration}-conformance",
                "0.2.0",
            ):
                return package, "evidence", declaration
    return None


def _structural_diagnostics(observation: GraphObservation) -> tuple[record_check.Diagnostic, ...]:
    if not observation.ok:
        return (_diagnostic("PROFILE_CHOICE_INVALID_GRAPH"),)
    documents = {record.address: record.document for record in observation.records}
    if len(documents) != len(observation.records):
        return (_diagnostic("PROFILE_CHOICE_DUPLICATE_ADDRESS"),)
    unexpected = sorted(set(documents) - _EXPECTED_ADDRESSES)
    if unexpected:
        return (_diagnostic("PROFILE_CHOICE_UNEXPECTED_ADDRESS", repr(unexpected[0])),)
    missing = sorted(_EXPECTED_ADDRESSES - set(documents))
    if missing:
        return (_diagnostic("PROFILE_CHOICE_MISSING_ADDRESS", repr(missing[0])),)

    for selector in (_SPECIFICATION, _NATIVE_PROFILE, _DENO_PROFILE, _NATIVE_POLICY, _DENO_POLICY):
        document = documents.get(selector)
        if document is None:
            return (_diagnostic("PROFILE_CHOICE_SELECTOR_NOT_FOUND", repr(selector)),)
        if record_check.address_of(document) != selector:
            return (_diagnostic("PROFILE_CHOICE_SELECTOR_IDENTITY", repr(selector)),)

    for policy, profile in ((_NATIVE_POLICY, _NATIVE_PROFILE), (_DENO_POLICY, _DENO_PROFILE)):
        document = documents[policy]
        if (
            document.get("specification") != _address_document(_SPECIFICATION)
            or document.get("profile") != _address_document(profile)
            or document.get("concerns") != _EXPECTED_CONCERNS
            or document.get("prohibitions") != _EXPECTED_PROHIBITIONS
        ):
            return (_diagnostic("PROFILE_CHOICE_POLICY_SELECTOR_MISMATCH", repr(policy)),)

    for address, document in documents.items():
        expected = _expected_new_record(address)
        if expected is None:
            continue
        package, kind, declaration = expected
        contract = _PACKAGES[package]
        profile = contract["profile"]
        realization = contract["realization"]
        if record_check.address_of(document) != address:
            return (_diagnostic("PROFILE_CHOICE_RECORD_IDENTITY", repr(address)),)
        if kind == "realization":
            if (
                document.get("specification") != _address_document(_SPECIFICATION)
                or document.get("supportedProfiles") != [_address_document(profile)]
            ):
                return (_diagnostic("PROFILE_CHOICE_REALIZATION_SCOPE", repr(address)),)
            continue
        assert declaration is not None
        claim = ("claim", f"{package}-{declaration}", "0.2.0")
        if kind == "claim":
            if (
                document.get("subject") != _address_document(realization)
                or document.get("governingSpecification") != _address_document(_SPECIFICATION)
                or document.get("proposition")
                != {
                    "specification": _address_document(_SPECIFICATION),
                    "declarationId": declaration,
                }
                or document.get("concern") != _DECLARATIONS[declaration]
                or document.get("applicableProfiles") != [_address_document(profile)]
                or document.get("state") != "active"
            ):
                return (_diagnostic("PROFILE_CHOICE_CLAIM_SCOPE", repr(address)),)
            continue
        applicability = document.get("applicability")
        provenance = document.get("provenance")
        if (
            document.get("claim") != _address_document(claim)
            or document.get("specification") != _address_document(_SPECIFICATION)
            or document.get("realization") != _address_document(realization)
            or document.get("adapter") != contract["adapter"]
            or not isinstance(applicability, dict)
            or applicability.get("profiles") != [_address_document(profile)]
            or not isinstance(provenance, dict)
            or provenance.get("declaration") != declaration
            or provenance.get("report") != contract["report"]
            or provenance.get("reportCandidate") != package
            or provenance.get("reportPacketRole") != "profile-choice-candidate"
            or provenance.get("plan") != contract["plan"]
            or provenance.get("profile") != contract["profileBinding"]
        ):
            return (_diagnostic("PROFILE_CHOICE_EVIDENCE_SCOPE", repr(address)),)
    return ()


def _effect_scope_match(
    evidence: dict[str, Any],
    claim: dict[str, Any],
    realization_document: dict[str, Any],
    *,
    contract: dict[str, Any],
    declaration: str,
) -> bool:
    applicability = evidence.get("applicability")
    provenance = evidence.get("provenance")
    realization_adapter = realization_document.get("adapter")
    evidence_adapter = evidence.get("adapter")
    return (
        claim.get("concern") == "effect.conformance"
        and claim.get("applicableProfiles") == [_address_document(contract["profile"])]
        and evidence.get("scope") == "realization"
        and evidence.get("mechanism") == _CAMPAIGN
        and isinstance(applicability, dict)
        and applicability.get("profiles") == [_address_document(contract["profile"])]
        and isinstance(realization_adapter, dict)
        and isinstance(evidence_adapter, dict)
        and evidence_adapter.get("id") == realization_adapter.get("id")
        and evidence_adapter.get("version") == realization_adapter.get("version")
        and isinstance(provenance, dict)
        and provenance.get("declaration") == declaration
        and provenance.get("plan") == contract["plan"]
    )


def _prohibition_disposition(
    policy_entry: dict[str, Any],
    *,
    specification_document: dict[str, Any],
    realization_document: dict[str, Any],
    contract: dict[str, Any],
    documents: tuple[tuple[Address, dict[str, Any]], ...],
) -> ProhibitionDisposition:
    proposition = policy_entry.get("proposition")
    declaration = proposition.get("declarationId", "<invalid>") if isinstance(proposition, dict) else "<invalid>"
    event_pattern = policy_entry.get("eventPattern", "<invalid>")
    effect = specification_document.get("effects")
    accepted_scopes = policy_entry.get("acceptedEvidenceScope")
    complete = (
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
    realization = contract["realization"]
    profile = contract["profile"]
    if complete:
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
            item
            for item in target_claims
            if item[1].get("state") == "active"
            and profile in _addresses(item[1].get("applicableProfiles"))
        )
        if not target_claims:
            reasons.append("missing-claim")
        for claim_address, claim_document in target_claims:
            selected = (claim_address, claim_document) in claims
            linked = _evidence_for_claim(documents, claim_address)
            if selected and not linked:
                reasons.append("absent-evidence")
            for evidence_address, evidence_document in linked:
                if not selected or not _evidence_is_applicable(evidence_document, profile=profile):
                    inapplicable.append(evidence_address)
                    continue
                if evidence_document.get("reviewState") != "accepted":
                    unselected.append(evidence_address)
                    reasons.append("unaccepted-review-state")
                    continue
                if _EFFECT_SCOPE not in accepted_scopes or not _effect_scope_match(
                    evidence_document,
                    claim_document,
                    realization_document,
                    contract=contract,
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
    if not complete:
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


def _ledger(
    documents: tuple[tuple[Address, dict[str, Any]], ...],
    *,
    package: str,
    kind: str,
) -> ApplicabilityLedger:
    selected_set = set(_package_addresses(package, "0.2.0", kind))
    present = {address for address, document in documents if document.get("kind") == kind}
    return ApplicabilityLedger(
        tuple(sorted(present & selected_set)),
        tuple(sorted(present - selected_set)),
    )


def _inapplicable_for_concern(
    evidence: ApplicabilityLedger,
    by_address: dict[Address, dict[str, Any]],
    concern: str,
) -> tuple[Address, ...]:
    selected: list[Address] = []
    for address in evidence.inapplicable:
        document = by_address.get(address, {})
        claim = _address(document.get("claim"))
        claim_document = by_address.get(claim, {}) if claim is not None else {}
        if claim_document.get("concern") == concern:
            selected.append(address)
    return tuple(sorted(selected))


def resolve_ordered_map_profile_choices(
    observation: GraphObservation,
) -> ProfileChoiceResolution:
    """Resolve the two exact decisions from one already captured detached graph."""

    diagnostics = _structural_diagnostics(observation)
    if diagnostics:
        return ProfileChoiceResolution((), diagnostics)
    documents = tuple((record.address, record.document) for record in observation.records)
    by_address = dict(documents)
    specification_document = by_address[_SPECIFICATION]
    decisions: list[ProfileChoiceDecision] = []
    for package in _DECISION_ORDER:
        contract = _PACKAGES[package]
        policy = contract["policy"]
        profile = contract["profile"]
        realization = contract["realization"]
        policy_document = by_address[policy]
        realization_document = by_address.get(realization)
        if realization_document is None:
            return ProfileChoiceResolution(
                (), (_diagnostic("PROFILE_CHOICE_REALIZATION_NOT_FOUND", repr(realization)),)
            )
        claim_ledger = _ledger(documents, package=package, kind="claim")
        evidence_ledger = _ledger(documents, package=package, kind="evidence")
        concerns = []
        for entry in policy_document.get("concerns", []):
            if not isinstance(entry, dict):
                continue
            disposition = _concern_disposition(
                entry,
                specification_document=specification_document,
                specification=_SPECIFICATION,
                profile=profile,
                realization=realization,
                documents=documents,
            )
            disposition = replace(
                disposition,
                inapplicable_evidence=_unique_sorted(
                    (*disposition.inapplicable_evidence, *_inapplicable_for_concern(
                        evidence_ledger, by_address, disposition.concern
                    ))
                ),
            )
            concerns.append(disposition)
        prohibitions = tuple(
            _prohibition_disposition(
                entry,
                specification_document=specification_document,
                realization_document=realization_document,
                contract=contract,
                documents=documents,
            )
            for entry in policy_document.get("prohibitions", [])
            if isinstance(entry, dict)
        )
        blocked = any(item.blocks for item in concerns) or any(
            item.blocks for item in prohibitions
        )
        candidate = ResolutionCandidate(
            realization,
            "unacceptable" if blocked else "acceptable",
            tuple(concerns),
            prohibitions,
            _boundary(realization_document),
        )
        decisions.append(
            ProfileChoiceDecision(
                policy,
                profile,
                candidate,
                claim_ledger,
                evidence_ledger,
            )
        )
    return ProfileChoiceResolution(tuple(decisions), ())


def _address_text(address: Address) -> str:
    return "/".join(address)


def render_ordered_map_profile_choices(
    authority: ManifestAuthority,
    observation: GraphObservation,
    resolution: ProfileChoiceResolution,
) -> str:
    """Render the exact decisions without further discovery, I/O, or execution."""

    lines = [
        "OrderedMap exact deployment-profile choices (no discovery or execution)",
        f"graph records: {len(observation.records)}, sources: {len(authority.sources)}",
    ]
    for decision in resolution.decisions:
        candidate = decision.candidate
        lines.extend(
            (
                f"policy: {_address_text(decision.policy)}",
                f"profile: {_address_text(decision.profile)}",
                f"{_address_text(candidate.realization)}: semantic={candidate.semantic_status}",
                f"Claims: selected-applicable={len(decision.claims.selected_applicable)} "
                f"inapplicable={len(decision.claims.inapplicable)}",
                f"Evidence: selected-applicable={len(decision.evidence.selected_applicable)} "
                f"inapplicable={len(decision.evidence.inapplicable)}",
            )
        )
        lines.extend(
            f"{item.concern}: status={item.status} priority={item.priority} "
            f"blocks={'yes' if item.blocks else 'no'}"
            for item in candidate.concerns
        )
        lines.extend(
            (
                "Directional realization boundary (not semantic acceptance)",
                f"direction={candidate.boundary.direction} "
                f"mechanism={candidate.boundary.mechanism} "
                f"direct={'yes' if candidate.boundary.direct else 'no'}",
            )
        )
    return "\n".join(lines) + "\n"


def _failure(
    authority: ManifestAuthority,
    diagnostics: tuple[record_check.Diagnostic, ...],
    *,
    observation: GraphObservation | None = None,
) -> ProfileChoiceObservation:
    empty = GraphObservation((), ()) if observation is None else observation
    resolution = ProfileChoiceResolution((), diagnostics)
    return ProfileChoiceObservation(authority, empty, resolution, None, diagnostics)


def _expected_authority(
    manifest_path: Path, document: Mapping[str, Any]
) -> tuple[tuple[graph.ManifestSource, ...], tuple[graph.ManifestMember, ...]]:
    sources = tuple(
        graph.ManifestSource(item["id"], item["root"], frozenset(item["roles"]))
        for item in document["sources"]
    )
    members = tuple(
        graph.ManifestMember(
            item["source"],
            record_check.address_of(item["address"]),
            item["sha256"],
            item["role"],
        )
        for item in document["members"]
    )
    return sources, members


def inspect_ordered_map_profile_choices() -> ProfileChoiceObservation:
    """Authenticate and replay the one exact profile-choice product snapshot."""

    manifest_path = _ROOT / _MANIFEST
    captured = canonical_artifact.inspect_json_artifact(
        manifest_path,
        schema_path=_ROOT / _MANIFEST_SCHEMA,
        expected_raw_sha256=_MANIFEST_RAW_SHA256,
        label="OrderedMap exact deployment-profile manifest",
    )
    empty_authority = ManifestAuthority(manifest_path, (), (), captured.diagnostics)
    if not captured.ok:
        return _failure(empty_authority, captured.diagnostics)
    assert isinstance(captured.document, Mapping)
    expected_sources, expected_members = _expected_authority(
        manifest_path, captured.document
    )
    authority = graph.inspect_manifest_document(manifest_path, captured.document)
    if (
        not authority.ok
        or authority.manifest_path != manifest_path
        or authority.sources != expected_sources
        or authority.members != expected_members
    ):
        diagnostics = authority.diagnostics or (
            _diagnostic("PROFILE_CHOICE_AUTHORITY_MISMATCH"),
        )
        return _failure(authority, diagnostics)
    observation = graph.inspect_manifest_graph(authority)
    if not observation.ok:
        return _failure(authority, observation.diagnostics, observation=observation)
    resolution = resolve_ordered_map_profile_choices(observation)
    if not resolution.ok:
        return _failure(authority, resolution.diagnostics, observation=observation)
    output = render_ordered_map_profile_choices(authority, observation, resolution)
    return ProfileChoiceObservation(authority, observation, resolution, output, ())
