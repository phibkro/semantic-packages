"""Pinned read-only contract inputs for the OrderedMap tracer."""

from __future__ import annotations

from pathlib import Path

from semantic_packages import canonical_artifact


_ROOT = Path(__file__).resolve().parents[1]
_PLAN = _ROOT / "contracts" / "ordered-map" / "conformance-plan.json"
_SCHEMA = _ROOT / "schemas" / "ordered-map-conformance-plan.schema.json"
_PLAN_SHA256 = "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a"


def inspect_conformance_plan() -> canonical_artifact.ArtifactObservation:
    """Inspect the one O-R3a-reviewed plan; callers cannot override its authority."""

    return canonical_artifact.inspect_json_artifact(
        _PLAN,
        schema_path=_SCHEMA,
        expected_canonical_sha256=_PLAN_SHA256,
        label="ordered-map-conformance-plan",
    )
