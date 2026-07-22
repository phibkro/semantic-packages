from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STACK_SURFACE = ROOT / "specs" / "stack.pspec"
ORDERED_MAP_SURFACE = ROOT / "specs" / "ordered-map.pspec"
STACK_SPEC = ROOT / "registry" / "stack" / "theory" / "records" / "stack-spec.json"
ORDERED_MAP_SPEC = (
    ROOT / "registry" / "ordered-map" / "theory" / "records" / "ordered-map-spec.json"
)
SPEC_SCHEMA = ROOT / "schemas" / "spec.schema.json"

EXPECTED_SHA256 = {
    STACK_SURFACE: "86f60cc9415353b951b21d1993430b0bd4369a6e560359aaeb67af7cc682596a",
    STACK_SPEC: "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1",
    ORDERED_MAP_SPEC: "6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f",
    SPEC_SCHEMA: "c77c1089e61f4b4c88b5e9a93429ea121753ab5753c76c11889a285c0265cd84",
}
DECLARATION_FIELDS = (
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
SHARED_FIELDS = {
    "carriers",
    "operations",
    "observations",
    "equivalences",
    "laws",
    "effects",
    "resources",
    "performancePropositions",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _declaration_ids(specification: dict) -> tuple[str, ...]:
    ids: list[str] = []
    for field in DECLARATION_FIELDS:
        value = specification.get(field)
        if isinstance(value, dict):
            ids.append(value["id"])
        elif isinstance(value, list):
            ids.extend(item["id"] for item in value)
    return tuple(ids)


class SharedHumanAuthoringSurfaceProbeTest(unittest.TestCase):
    def test_exact_probe_inputs_are_frozen(self) -> None:
        self.assertEqual(
            EXPECTED_SHA256,
            {path: _digest(path) for path in EXPECTED_SHA256},
        )

    def test_two_domains_share_mechanics_but_not_identical_shapes(self) -> None:
        stack = _load(STACK_SPEC)
        ordered_map = _load(ORDERED_MAP_SPEC)
        stack_fields = set(stack) & set(DECLARATION_FIELDS)
        ordered_map_fields = set(ordered_map) & set(DECLARATION_FIELDS)
        self.assertEqual(SHARED_FIELDS | {"derivedObservations"}, stack_fields)
        self.assertEqual(SHARED_FIELDS, ordered_map_fields)
        self.assertEqual(11, len(_declaration_ids(stack)))
        self.assertEqual(18, len(_declaration_ids(ordered_map)))

    def test_every_canonical_declaration_id_is_explicit_and_flat(self) -> None:
        for path in (STACK_SPEC, ORDERED_MAP_SPEC):
            with self.subTest(path=path):
                identifiers = _declaration_ids(_load(path))
                self.assertTrue(all(identifiers))
                self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_current_surface_cannot_round_trip_without_hidden_defaults(self) -> None:
        surface = STACK_SURFACE.read_text(encoding="utf-8")
        self.assertFalse(ORDERED_MAP_SURFACE.exists())
        for canonical_id in (
            "stack-equivalence",
            "stack-effects",
            "push-amortized-constant",
        ):
            with self.subTest(canonical_id=canonical_id):
                self.assertNotIn(canonical_id, surface)

    def test_schema_hosts_semantic_payloads_as_uninterpreted_text(self) -> None:
        definitions = _load(SPEC_SCHEMA)["$defs"]
        hosted_fields = {
            "operationDeclaration": "signature",
            "derivedObservationDeclaration": "definition",
            "equivalenceDeclaration": "definition",
            "lawDeclaration": "statement",
            "resourceDeclaration": "rule",
            "performancePropositionDeclaration": "predicate",
        }
        for definition, field in hosted_fields.items():
            with self.subTest(definition=definition, field=field):
                self.assertEqual(
                    "common.schema.json#/$defs/nonEmptyString",
                    definitions[definition]["properties"][field]["$ref"],
                )


if __name__ == "__main__":
    unittest.main()
