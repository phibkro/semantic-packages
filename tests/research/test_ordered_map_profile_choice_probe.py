from __future__ import annotations

import json
import unittest
from copy import deepcopy
from collections import Counter
from pathlib import Path

from scripts import record_check


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "fixtures" / "research" / "ordered-map-profile-choice"
NATIVE = PROBE / "native-profile.json"
DENO = PROBE / "deno-profile.json"
OLD_PROFILE = ROOT / "registry" / "ordered-map" / "theory" / "dependencies" / "ordered-map-profile.json"
RUST_REALIZATION = ROOT / "registry" / "ordered-map" / "packages" / "rust" / "records" / "ordered-map-rust-realization.json"
TYPESCRIPT_REALIZATION = ROOT / "registry" / "ordered-map" / "packages" / "typescript" / "records" / "ordered-map-typescript-realization.json"
PACKAGE_RECORDS = (
    ROOT / "registry" / "ordered-map" / "packages" / "rust" / "records",
    ROOT / "registry" / "ordered-map" / "packages" / "typescript" / "records",
)
RUST_REPORT = ROOT / "reports" / "ordered-map" / "rust-campaign-report.json"
TYPESCRIPT_REPORT = ROOT / "reports" / "ordered-map" / "typescript-campaign-report.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _address(document: dict) -> tuple[str, str, str]:
    return document["kind"], document["id"], document["version"]


def _applicable_profiles(document: dict) -> set[tuple[str, str, str]]:
    if document["kind"] == "claim":
        values = document["applicableProfiles"]
    elif document["kind"] == "evidence":
        values = document["applicability"]["profiles"]
    else:
        raise AssertionError(f"unsupported profile-bearing kind: {document['kind']}")
    return {
        (item["kind"], item["id"], item["version"])
        for item in values
    }


def _package_records() -> tuple[dict, ...]:
    return tuple(
        _load(path)
        for directory in PACKAGE_RECORDS
        for path in sorted(directory.glob("*.json"))
    )


class OrderedMapProfileChoiceProbeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.native = _load(NATIVE)
        self.deno = _load(DENO)
        self.old_profile = _load(OLD_PROFILE)

    def test_candidate_profiles_are_schema_valid_exact_records(self) -> None:
        schemas = record_check.SchemaRegistry()
        self.assertEqual([], schemas.metaschema_errors)
        validator = schemas.validator_for("realizationProfile")

        for path, document in ((NATIVE, self.native), (DENO, self.deno)):
            with self.subTest(path=path):
                self.assertEqual([], list(validator.iter_errors(document)))
                self.assertEqual("realizationProfile", document["kind"])
                self.assertEqual("0.1.0", document["version"])

        self.assertEqual(
            {
                ("realizationProfile", "ordered-map-native-process", "0.1.0"),
                ("realizationProfile", "ordered-map-deno-sandbox", "0.1.0"),
            },
            {_address(self.native), _address(self.deno)},
        )

    def test_profiles_hold_meaning_constant_and_differentiate_deployment(self) -> None:
        for field in (
            "scale",
            "concurrency",
            "portability",
            "workloads",
            "costMeasures",
        ):
            with self.subTest(field=field):
                self.assertEqual(self.native[field], self.deno[field])

        self.assertNotEqual(self.native["platform"], self.deno["platform"])
        self.assertNotEqual(
            set(self.native["hostCapabilities"]),
            set(self.deno["hostCapabilities"]),
        )
        self.assertNotEqual(self.native["trust"], self.deno["trust"])
        self.assertNotIn("network.denied", self.native["hostCapabilities"])
        self.assertIn("network.denied", self.deno["hostCapabilities"])

    def test_accepted_realizations_do_not_claim_the_candidate_profiles(self) -> None:
        old_address = _address(self.old_profile)
        candidate_addresses = {_address(self.native), _address(self.deno)}
        for path in (RUST_REALIZATION, TYPESCRIPT_REALIZATION):
            with self.subTest(path=path):
                realization = _load(path)
                supported = {
                    (item["kind"], item["id"], item["version"])
                    for item in realization["supportedProfiles"]
                }
                self.assertEqual({old_address}, supported)
                self.assertTrue(supported.isdisjoint(candidate_addresses))

    def test_every_accepted_claim_and_evidence_is_exactly_inapplicable(self) -> None:
        old_address = _address(self.old_profile)
        candidate_addresses = {_address(self.native), _address(self.deno)}
        records = _package_records()
        claims = tuple(item for item in records if item["kind"] == "claim")
        evidence = tuple(item for item in records if item["kind"] == "evidence")

        self.assertEqual(14, len(claims))
        self.assertEqual(14, len(evidence))
        self.assertEqual(
            Counter(
                {
                    "law.conformance": 10,
                    "resource.persistence": 2,
                    "effect.conformance": 2,
                }
            ),
            Counter(item["concern"] for item in claims),
        )
        claim_addresses = {_address(item) for item in claims}
        self.assertEqual(
            claim_addresses,
            {
                (
                    item["claim"]["kind"],
                    item["claim"]["id"],
                    item["claim"]["version"],
                )
                for item in evidence
            },
        )
        for document in (*claims, *evidence):
            with self.subTest(address=_address(document)):
                profiles = _applicable_profiles(document)
                self.assertEqual({old_address}, profiles)
                self.assertTrue(profiles.isdisjoint(candidate_addresses))

    def test_relabel_and_addition_controls_break_exact_applicability(self) -> None:
        old_address = _address(self.old_profile)
        native_reference = {
            "kind": self.native["kind"],
            "id": self.native["id"],
            "version": self.native["version"],
        }
        records = _package_records()
        claim = deepcopy(next(item for item in records if item["kind"] == "claim"))
        evidence = deepcopy(next(item for item in records if item["kind"] == "evidence"))

        claim["applicableProfiles"] = [native_reference]
        evidence["applicability"]["profiles"].append(native_reference)

        self.assertNotEqual({old_address}, _applicable_profiles(claim))
        self.assertNotEqual({old_address}, _applicable_profiles(evidence))

    def test_retained_reports_bind_the_old_profile_not_a_relabelled_one(self) -> None:
        old_binding = {
            "path": OLD_PROFILE.relative_to(ROOT).as_posix(),
            "sha256": "6d1297892c355a569e244c2b94448a5f5edaf9b1bf2ae54f940d7c4494fe225f",
        }
        candidate_paths = {
            NATIVE.relative_to(ROOT).as_posix(),
            DENO.relative_to(ROOT).as_posix(),
        }
        for path in (RUST_REPORT, TYPESCRIPT_REPORT):
            with self.subTest(path=path):
                binding = _load(path)["inputs"]["profile"]
                self.assertEqual(old_binding, binding)
                self.assertNotIn(binding["path"], candidate_paths)


if __name__ == "__main__":
    unittest.main()
