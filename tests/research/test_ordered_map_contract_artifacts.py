from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import record_check  # noqa: E402


THEORY = ROOT / "registry" / "ordered-map" / "theory"
SPECIFICATION = THEORY / "records" / "ordered-map-spec.json"
PROFILE = THEORY / "dependencies" / "ordered-map-profile.json"
PLAN = ROOT / "contracts" / "ordered-map" / "conformance-plan.json"
PLAN_SCHEMA = ROOT / "schemas" / "ordered-map-conformance-plan.schema.json"

EXPECTED_CANONICAL_PLAN_SHA256 = (
    "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a"
)
EXPECTED_CASES = (
    "lookup-empty",
    "same-class-replacement",
    "other-class-preservation",
    "nonlast-overwrite-order",
    "new-class-append-three",
    "retained-new-class-source",
    "retained-existing-class-source",
)
EXPECTED_COVERAGE = {
    "lookup-empty",
    "lookup-put-same",
    "lookup-put-other",
    "put-existing-position",
    "put-new-appends",
    "persistence",
    "ordered-map-effects",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OrderedMapContractArtifactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specification = _load(SPECIFICATION)
        cls.profile = _load(PROFILE)
        cls.plan = _load(PLAN)
        cls.schema = _load(PLAN_SCHEMA)

    def test_exact_theory_records_are_link_valid(self) -> None:
        self.assertEqual([], record_check.validate_graph_paths([str(THEORY)]))
        self.assertEqual(
            ("specification", "ordered-map", "0.1.0"),
            tuple(self.specification[key] for key in ("kind", "id", "version")),
        )
        self.assertEqual(
            ("realizationProfile", "ordered-map-ascii-fold", "0.1.0"),
            tuple(self.profile[key] for key in ("kind", "id", "version")),
        )

    def test_performance_proposition_is_exact_but_uninstrumented(self) -> None:
        proposition = self.specification["performancePropositions"]
        self.assertEqual(1, len(proposition))
        proposition = proposition[0]
        self.assertEqual("put-amortized-constant", proposition["id"])
        self.assertEqual(["put"], proposition["operationFamily"])
        self.assertEqual("put-sequence", proposition["workload"]["localId"])
        self.assertEqual(
            "realization-steps", proposition["costMeasure"]["localId"]
        )
        self.assertEqual(["proof", "proof-audit"], proposition["permittedEvidenceMethods"])
        measure = self.profile["costMeasures"][0]
        self.assertIn("does not report", measure["instrumentation"])

    def test_plan_schema_and_canonical_digest_are_frozen(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        errors = sorted(
            Draft202012Validator(self.schema).iter_errors(self.plan),
            key=lambda item: list(item.path),
        )
        self.assertEqual([], errors)
        canonical = json.dumps(
            self.plan,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        self.assertEqual(
            EXPECTED_CANONICAL_PLAN_SHA256,
            hashlib.sha256(canonical).hexdigest(),
        )

    def test_plan_pins_exact_record_bytes_and_addresses(self) -> None:
        for key, path, address in (
            (
                "specification",
                SPECIFICATION,
                ("specification", "ordered-map", "0.1.0"),
            ),
            (
                "profile",
                PROFILE,
                ("realizationProfile", "ordered-map-ascii-fold", "0.1.0"),
            ),
        ):
            item = self.plan[key]
            self.assertEqual(path.relative_to(ROOT).as_posix(), item["path"])
            self.assertEqual(_sha256(path), item["sha256"])
            self.assertEqual(
                address,
                tuple(item["address"][part] for part in ("kind", "id", "version")),
            )

    def test_cases_have_valid_logical_bindings_and_exact_coverage(self) -> None:
        self.assertEqual(EXPECTED_CASES, tuple(item["id"] for item in self.plan["cases"]))
        coverage: set[str] = set()
        for case in self.plan["cases"]:
            bindings: set[str] = set()
            put_count = 0
            for step in case["steps"]:
                self.assertEqual("ordered-map-effects", step["effectDeclaration"])
                coverage.add(step["effectDeclaration"])
                if "source" in step:
                    self.assertIn(step["source"], bindings)
                if "bind" in step:
                    self.assertNotIn(step["bind"], bindings)
                    bindings.add(step["bind"])
                if step["op"] == "put":
                    put_count += 1
                coverage.update(step.get("declarations", ()))
            self.assertLessEqual(put_count, self.plan["bounds"]["maximumHistory"])
        self.assertEqual(EXPECTED_COVERAGE, coverage)

    def test_persistence_attribution_observes_only_retained_sources(self) -> None:
        cases = {item["id"]: item for item in self.plan["cases"]}
        for case_id, retained, derived in (
            ("retained-new-class-source", "h1", "h2"),
            ("retained-existing-class-source", "h2", "h3"),
        ):
            observations = [
                step
                for step in cases[case_id]["steps"]
                if "persistence" in step.get("declarations", ())
            ]
            self.assertEqual(1, len(observations))
            self.assertEqual(retained, observations[0]["source"])
            self.assertNotEqual(derived, observations[0]["source"])

    def test_reorder_oracle_targets_only_existing_position(self) -> None:
        cases = {item["id"]: item for item in self.plan["cases"]}
        target = [
            step
            for step in cases["nonlast-overwrite-order"]["steps"]
            if step.get("declarations") == ["put-existing-position"]
        ]
        self.assertEqual(1, len(target))
        self.assertEqual("entries", target[0]["op"])
        self.assertEqual(
            [
                {"class": "a", "value": -1},
                {"class": "b", "value": 2},
            ],
            target[0]["expected"],
        )


if __name__ == "__main__":
    unittest.main()
