"""Pinned final-authority candidate replay for the OrderedMap tracer.

The actor authenticates one immutable ProductContract and its complete manifest,
captures the finite graph once, and derives publication, registration, graph, and
theory views from that snapshot. It neither executes records nor resolves policy or
accepts the candidate as final product authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts import record_check
from semantic_packages import (
    canonical_artifact,
    graph,
    publication,
    registration,
    theory_projection,
)


_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT_PATH = Path("contracts/ordered-map/product-contract.json")
_CONTRACT_SCHEMA = Path("schemas/ordered-map-product-contract.schema.json")
_MANIFEST_SCHEMA = Path("schemas/registry-manifest.schema.json")
_CONTRACT_CANONICAL_SHA256 = (
    "4bfbc89ed7e061fa9f2c38f02a99331af1e9a05f5d111bea391b2034ac14eb17"
)


@dataclass(frozen=True)
class ProductCandidateAuthority:
    """Authenticated candidate bytes surfaced without a convergence decision."""

    contract_id: str
    contract_version: str
    authority_class: str
    final_product_authority: bool
    contract_canonical_sha256: str
    manifest_raw_sha256: str


@dataclass(frozen=True)
class ProductCandidateObservation:
    """One fail-closed replay of the pinned OrderedMap product candidate."""

    authority: ProductCandidateAuthority | None
    publication: publication.PublicationObservation | None
    registrations: tuple[registration.RegistrationObservation, ...]
    graph: graph.GraphObservation | None
    theory: theory_projection.TheoryView | None
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def _failure(
    diagnostics: tuple[record_check.Diagnostic, ...],
    *,
    authority: ProductCandidateAuthority | None = None,
    graph_observation: graph.GraphObservation | None = None,
) -> ProductCandidateObservation:
    return ProductCandidateObservation(
        authority,
        None,
        (),
        graph_observation,
        None,
        diagnostics,
    )


def inspect_product_candidate() -> ProductCandidateObservation:
    """Replay the pinned candidate without caller overrides or acceptance."""

    contract = canonical_artifact.inspect_json_artifact(
        _ROOT / _CONTRACT_PATH,
        schema_path=_ROOT / _CONTRACT_SCHEMA,
        expected_canonical_sha256=_CONTRACT_CANONICAL_SHA256,
        label="OrderedMap ProductContract candidate",
    )
    if not contract.ok:
        return _failure(contract.diagnostics)
    assert contract.document is not None
    assert contract.canonical_sha256 is not None
    contract_document = contract.document

    manifest_path = _ROOT / contract_document["manifest"]["path"]
    manifest = canonical_artifact.inspect_json_artifact(
        manifest_path,
        schema_path=_ROOT / _MANIFEST_SCHEMA,
        expected_raw_sha256=contract_document["manifest"]["rawSha256"],
        label="OrderedMap complete manifest candidate",
    )
    if not manifest.ok:
        return _failure(manifest.diagnostics)
    assert manifest.document is not None
    assert manifest.raw_sha256 is not None

    manifest_authority = graph.inspect_manifest_document(
        manifest_path, manifest.document
    )
    if not manifest_authority.ok:
        return _failure(manifest_authority.diagnostics)

    actor_authority = ProductCandidateAuthority(
        contract_document["id"],
        contract_document["version"],
        contract_document["authorityClass"],
        contract_document["finalProductAuthority"],
        contract.canonical_sha256,
        manifest.raw_sha256,
    )
    graph_observation = graph.inspect_manifest_graph(manifest_authority)
    if not graph_observation.ok:
        return _failure(
            graph_observation.diagnostics,
            authority=actor_authority,
            graph_observation=graph_observation,
        )

    sources = tuple(item["selector"] for item in contract_document["sources"])
    theory_source, rust_source, typescript_source, _consumer_source = sources
    publication_observation = publication._project_theory_publication(
        graph_observation,
        authority=manifest_authority,
        source=theory_source,
        product="OrderedMap",
    )
    if not publication_observation.ok:
        return _failure(
            publication_observation.diagnostics,
            authority=actor_authority,
            graph_observation=graph_observation,
        )

    registrations = tuple(
        registration._project_package_registration(
            graph_observation,
            authority=manifest_authority,
            theory_source=theory_source,
            package=package,
            product="OrderedMap",
        )
        for package in (rust_source, typescript_source)
    )
    registration_diagnostics = tuple(
        diagnostic
        for observation in registrations
        for diagnostic in observation.diagnostics
    )
    if registration_diagnostics:
        return _failure(
            tuple(sorted(registration_diagnostics, key=record_check.Diagnostic.sort_key)),
            authority=actor_authority,
            graph_observation=graph_observation,
        )

    specification_document = contract_document["specification"]["address"]
    specification = tuple(
        specification_document[key] for key in ("kind", "id", "version")
    )
    projected = theory_projection.project_theory(
        graph_observation,
        specification=specification,
    )
    if not projected.ok:
        return _failure(
            projected.diagnostics,
            authority=actor_authority,
            graph_observation=graph_observation,
        )
    assert projected.view is not None
    return ProductCandidateObservation(
        actor_authority,
        publication_observation,
        registrations,
        graph_observation,
        projected.view,
        (),
    )
