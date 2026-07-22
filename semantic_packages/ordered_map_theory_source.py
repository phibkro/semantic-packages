"""Pinned provisional theory-source inspection for the OrderedMap tracer.

The actor authenticates its fixed contract and manifest, observes the finite source
once, and derives publication, graph, and theory views from that captured graph.  It
does not create final product authority, execute artifacts, or resolve compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts import record_check
from semantic_packages import canonical_artifact, graph, publication, theory_projection


_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT_PATH = Path("contracts/ordered-map/theory-source-contract.json")
_CONTRACT_SCHEMA = Path("schemas/ordered-map-theory-source-contract.schema.json")
_MANIFEST_SCHEMA = Path("schemas/registry-manifest.schema.json")
_CONTRACT_CANONICAL_SHA256 = (
    "1ec7d9f0ec74af8afff2823b89e7039a910fbde28fd86b9dd60f499948b25a6b"
)


@dataclass(frozen=True)
class TheorySourceAuthority:
    """Authenticated provisional authority surfaced to the theory-source actor."""

    contract_id: str
    contract_version: str
    authority_class: str
    final_product_authority: bool
    contract_canonical_sha256: str
    manifest_raw_sha256: str
    source: str


@dataclass(frozen=True)
class TheorySourceObservation:
    """One fail-closed inspection of the pinned OrderedMap theory source."""

    authority: TheorySourceAuthority | None
    publication: publication.PublicationObservation | None
    graph: graph.GraphObservation | None
    theory: theory_projection.TheoryView | None
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def _failure(
    diagnostics: tuple[record_check.Diagnostic, ...],
    *,
    authority: TheorySourceAuthority | None = None,
    graph_observation: graph.GraphObservation | None = None,
) -> TheorySourceObservation:
    return TheorySourceObservation(
        authority,
        None,
        graph_observation,
        None,
        diagnostics,
    )


def inspect_theory_source() -> TheorySourceObservation:
    """Inspect the pinned OrderedMap theory source without actor overrides."""

    contract = canonical_artifact.inspect_json_artifact(
        _ROOT / _CONTRACT_PATH,
        schema_path=_ROOT / _CONTRACT_SCHEMA,
        expected_canonical_sha256=_CONTRACT_CANONICAL_SHA256,
        label="OrderedMap theory-source contract",
    )
    if not contract.ok:
        return _failure(contract.diagnostics)
    assert contract.document is not None
    assert contract.canonical_sha256 is not None
    document = contract.document

    manifest_path = _ROOT / document["manifest"]["path"]
    manifest = canonical_artifact.inspect_json_artifact(
        manifest_path,
        schema_path=_ROOT / _MANIFEST_SCHEMA,
        expected_raw_sha256=document["manifest"]["rawSha256"],
        label="OrderedMap theory-source manifest",
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

    source = document["source"]["selector"]
    actor_authority = TheorySourceAuthority(
        document["id"],
        document["version"],
        document["authorityClass"],
        document["finalProductAuthority"],
        contract.canonical_sha256,
        manifest.raw_sha256,
        source,
    )
    graph_observation = graph.inspect_manifest_graph(manifest_authority)
    if not graph_observation.ok:
        return _failure(
            graph_observation.diagnostics,
            authority=actor_authority,
            graph_observation=graph_observation,
        )

    publication_observation = publication._project_theory_publication(
        graph_observation,
        authority=manifest_authority,
        source=source,
        product="OrderedMap",
    )
    if not publication_observation.ok:
        return _failure(
            publication_observation.diagnostics,
            authority=actor_authority,
            graph_observation=graph_observation,
        )

    specification_document = document["specification"]["address"]
    specification = (
        specification_document["kind"],
        specification_document["id"],
        specification_document["version"],
    )
    projected = theory_projection.project_theory(
        graph_observation, specification=specification
    )
    if not projected.ok:
        return TheorySourceObservation(
            actor_authority,
            publication_observation,
            graph_observation,
            None,
            projected.diagnostics,
        )
    assert projected.view is not None
    return TheorySourceObservation(
        actor_authority,
        publication_observation,
        graph_observation,
        projected.view,
        (),
    )
