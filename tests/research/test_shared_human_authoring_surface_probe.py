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
EXPECTED_IDENTITIES = {
    STACK_SPEC: ("specification", "stack", "0.1.0"),
    ORDERED_MAP_SPEC: ("specification", "ordered-map", "0.1.0"),
}
EXPECTED_DECLARATIONS = {
    STACK_SPEC: {
        "carriers": {"Stack"},
        "operations": {"empty", "push"},
        "observations": {"pop"},
        "derivedObservations": {"elements"},
        "equivalences": {"stack-equivalence"},
        "laws": {"pop-empty", "pop-push"},
        "effects": {"stack-effects"},
        "resources": {"persistence"},
        "performancePropositions": {"push-amortized-constant"},
    },
    ORDERED_MAP_SPEC: {
        "carriers": {"Key", "Value", "OrderedMap"},
        "operations": {"empty", "put"},
        "observations": {"lookup", "entries"},
        "equivalences": {
            "key-equivalence",
            "value-equivalence",
            "ordered-map-equivalence",
        },
        "laws": {
            "lookup-empty",
            "lookup-put-same",
            "lookup-put-other",
            "put-existing-position",
            "put-new-appends",
        },
        "effects": {"ordered-map-effects"},
        "resources": {"persistence"},
        "performancePropositions": {"put-amortized-constant"},
    },
}
EXPECTED_LOCAL_REFERENCES = {
    STACK_SPEC: {
        "equivalenceCarriers": {"stack-equivalence": "Stack"},
        "operationFamily": ("push",),
        "profile": ("realizationProfile", "stack-default", "0.1.0"),
        "workload": "push-sequence",
        "costMeasure": "realization-steps",
    },
    ORDERED_MAP_SPEC: {
        "equivalenceCarriers": {
            "key-equivalence": "Key",
            "value-equivalence": "Value",
            "ordered-map-equivalence": "OrderedMap",
        },
        "operationFamily": ("put",),
        "profile": ("realizationProfile", "ordered-map-ascii-fold", "0.1.0"),
        "workload": "put-sequence",
        "costMeasure": "realization-steps",
    },
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


def _declarations_by_field(specification: dict) -> dict[str, set[str]]:
    declarations: dict[str, set[str]] = {}
    for field in DECLARATION_FIELDS:
        value = specification.get(field)
        if isinstance(value, dict):
            declarations[field] = {value["id"]}
        elif isinstance(value, list):
            declarations[field] = {item["id"] for item in value}
    return declarations


def _reference_census(specification: dict) -> dict:
    performance = specification["performancePropositions"][0]
    workload = performance["workload"]
    cost_measure = performance["costMeasure"]
    profile = workload["profile"]
    assert profile == cost_measure["profile"]
    return {
        "equivalenceCarriers": {
            item["id"]: item["carrier"] for item in specification["equivalences"]
        },
        "operationFamily": tuple(performance["operationFamily"]),
        "profile": tuple(profile[key] for key in ("kind", "id", "version")),
        "workload": workload["localId"],
        "costMeasure": cost_measure["localId"],
    }


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

    def test_exact_identity_declarations_and_references_are_explicit(self) -> None:
        for path, expected_identity in EXPECTED_IDENTITIES.items():
            with self.subTest(path=path):
                specification = _load(path)
                self.assertEqual(
                    expected_identity,
                    tuple(specification[key] for key in ("kind", "id", "version")),
                )
                self.assertNotIn("imports", specification)
                self.assertEqual(
                    EXPECTED_DECLARATIONS[path],
                    _declarations_by_field(specification),
                )
                identifiers = _declaration_ids(specification)
                self.assertTrue(all(identifiers))
                self.assertEqual(len(identifiers), len(set(identifiers)))
                self.assertEqual(
                    EXPECTED_LOCAL_REFERENCES[path],
                    _reference_census(specification),
                )

    def test_current_surface_cannot_round_trip_without_hidden_defaults(self) -> None:
        surface = STACK_SURFACE.read_text(encoding="utf-8")
        self.assertFalse(ORDERED_MAP_SURFACE.exists())
        for canonical_id in (
            "stack-equivalence",
            "pop-empty",
            "pop-push",
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
