"""Read-only theory-consumer projection over a captured product graph.

The projection exposes authored meaning, exact imports, specification-scoped Claims,
Evidence qualifications, contradictions, and unknowns.  It does not resolve consumer
policy, acquire imports, merge namespaces, execute proofs, or infer compatibility.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from scripts import record_check
from semantic_packages.graph import Address, GraphObservation


@dataclass(frozen=True)
class EvidenceView:
    address: Address
    mechanism: str
    result: str
    review_state: str
    assumptions: tuple[str, ...]
    exclusions: tuple[str, ...]


@dataclass(frozen=True)
class ClaimView:
    address: Address
    concern: str
    state: str
    assumptions: tuple[str, ...]
    exclusions: tuple[str, ...]
    evidence: tuple[EvidenceView, ...]


@dataclass(frozen=True)
class DeclarationView:
    kind: str
    declaration_id: str
    observation: str
    claims: tuple[ClaimView, ...]
    _content_text: str

    @property
    def content(self) -> dict[str, Any]:
        """Return an isolated copy of the exact declaration content."""

        return json.loads(self._content_text)


@dataclass(frozen=True)
class ImportView:
    specification: Address
    available: bool


@dataclass(frozen=True)
class TheoryView:
    specification: Address
    imports: tuple[ImportView, ...]
    declarations: tuple[DeclarationView, ...]
    contradictions: tuple[Address, ...]
    unknowns: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ProjectionResult:
    view: TheoryView | None
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


_DECLARATION_FIELDS = (
    ("carriers", "carrier"),
    ("operations", "operation"),
    ("observations", "observation"),
    ("derivedObservations", "derivedObservation"),
    ("equivalences", "equivalence"),
    ("laws", "law"),
    ("effects", "effect"),
    ("resources", "resource"),
    ("performancePropositions", "performance"),
)


def _diagnostic(code: str, message: str | None = None) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, "<graph>", "#", message)


def _address(value: Any) -> Address | None:
    if not isinstance(value, dict):
        return None
    parts = (value.get("kind"), value.get("id"), value.get("version"))
    if not all(isinstance(part, str) for part in parts):
        return None
    return parts  # type: ignore[return-value]


def _texts(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _declarations(document: dict[str, Any]) -> tuple[tuple[str, str, dict[str, Any]], ...]:
    declarations: list[tuple[str, str, dict[str, Any]]] = []
    for field, kind in _DECLARATION_FIELDS:
        value = document.get(field)
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                declarations.append((kind, item["id"], item))
    return tuple(sorted(declarations, key=lambda item: (item[0], item[1])))


def _claim_targets(
    document: dict[str, Any], specification: Address, declaration_id: str
) -> bool:
    proposition = document.get("proposition")
    return (
        document.get("kind") == "claim"
        and _address(document.get("subject")) == specification
        and _address(document.get("governingSpecification")) == specification
        and isinstance(proposition, dict)
        and _address(proposition.get("specification")) == specification
        and proposition.get("declarationId") == declaration_id
    )


def _evidence_view(
    claim: Address,
    documents: tuple[tuple[Address, dict[str, Any]], ...],
) -> tuple[EvidenceView, ...]:
    views = [
        EvidenceView(
            address=address,
            mechanism=document.get("mechanism", "<invalid>"),
            result=document.get("result", "<invalid>"),
            review_state=document.get("reviewState", "<invalid>"),
            assumptions=_texts(document.get("assumptions")),
            exclusions=_texts(document.get("exclusions")),
        )
        for address, document in documents
        if document.get("kind") == "evidence"
        and _address(document.get("claim")) == claim
    ]
    return tuple(sorted(views, key=lambda item: item.address))


def _claim_views(
    specification: Address,
    declaration_id: str,
    documents: tuple[tuple[Address, dict[str, Any]], ...],
) -> tuple[ClaimView, ...]:
    views = [
        ClaimView(
            address=address,
            concern=document.get("concern", "<invalid>"),
            state=document.get("state", "<invalid>"),
            assumptions=_texts(document.get("assumptions")),
            exclusions=_texts(document.get("exclusions")),
            evidence=_evidence_view(address, documents),
        )
        for address, document in documents
        if _claim_targets(document, specification, declaration_id)
    ]
    return tuple(sorted(views, key=lambda item: item.address))


def _observation(claims: tuple[ClaimView, ...]) -> str:
    active = tuple(claim for claim in claims if claim.state == "active")
    if not active:
        return "unclaimed"
    evidence = tuple(item for claim in active for item in claim.evidence)
    accepted = tuple(item for item in evidence if item.review_state == "accepted")
    if any(item.result == "challenges" for item in accepted):
        return "contested-observation"
    if any(item.result == "supports" for item in accepted):
        return "supported-observation"
    return "undetermined"


def project_theory(
    graph: GraphObservation, *, specification: Address
) -> ProjectionResult:
    """Project one exact Specification and its specification-scoped observations."""

    if not graph.ok:
        return ProjectionResult(None, graph.diagnostics)

    documents = tuple((record.address, record.document) for record in graph.records)
    by_address = {address: document for address, document in documents}
    specification_document = by_address.get(specification)
    if specification_document is None:
        return ProjectionResult(
            None,
            (_diagnostic("PROJECTION_SELECTOR_NOT_FOUND", repr(specification)),),
        )
    if specification[0] != "specification" or specification_document.get("kind") != "specification":
        return ProjectionResult(
            None,
            (_diagnostic("PROJECTION_SELECTOR_KIND", repr(specification)),),
        )

    imports = tuple(
        sorted(
            (
                ImportView(address, address in by_address)
                for raw in specification_document.get("imports", [])
                if (address := _address(raw)) is not None
            ),
            key=lambda item: item.specification,
        )
    )
    declaration_views: list[DeclarationView] = []
    contradictions: set[Address] = set()
    unknowns: list[tuple[str, str]] = []
    for kind, declaration_id, content in _declarations(specification_document):
        claims = _claim_views(specification, declaration_id, documents)
        observation = _observation(claims)
        for claim in claims:
            contradictions.update(
                item.address
                for item in claim.evidence
                if item.review_state == "accepted" and item.result == "challenges"
            )
        if observation in {"unclaimed", "undetermined"}:
            unknowns.append((kind, declaration_id))
        declaration_views.append(
            DeclarationView(
                kind=kind,
                declaration_id=declaration_id,
                observation=observation,
                claims=claims,
                _content_text=json.dumps(content, sort_keys=True),
            )
        )

    return ProjectionResult(
        TheoryView(
            specification=specification,
            imports=imports,
            declarations=tuple(declaration_views),
            contradictions=tuple(sorted(contradictions)),
            unknowns=tuple(sorted(unknowns)),
        ),
        (),
    )
