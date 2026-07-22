from __future__ import annotations

import hashlib
import json
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts import record_check


ROOT = Path(__file__).resolve().parents[2]
SPECIFICATION = ROOT / "registry" / "ordered-map" / "theory" / "records" / "ordered-map-spec.json"
OLD_PROFILE = ROOT / "registry" / "ordered-map" / "theory" / "dependencies" / "ordered-map-profile.json"
OLD_POLICY = ROOT / "registry" / "ordered-map" / "consumers" / "package" / "records" / "ordered-map-bounded-policy.json"
OLD_MANIFEST = ROOT / "registry" / "ordered-map" / "manifest.json"
O8_MANIFEST = ROOT / "registry" / "ordered-map" / "successor-manifest.json"
PROFILE_CHOICE_MANIFEST = ROOT / "registry" / "ordered-map" / "profile-choice-manifest.json"
PROBE = ROOT / "fixtures" / "research" / "ordered-map-profile-choice"
PROFILES = ROOT / "registry" / "ordered-map" / "profile-choice" / "profiles" / "records"
POLICIES = ROOT / "registry" / "ordered-map" / "profile-choice" / "consumers" / "records"
PLANS = ROOT / "contracts" / "ordered-map" / "profile-choice"
BASE_PLAN = ROOT / "contracts" / "ordered-map" / "conformance-plan.json"
PLAN_SCHEMA = ROOT / "schemas" / "ordered-map-conformance-plan.schema.json"

NATIVE_PROFILE = PROFILES / "ordered-map-native-process.json"
DENO_PROFILE = PROFILES / "ordered-map-deno-sandbox.json"
NATIVE_POLICY = POLICIES / "ordered-map-native-process-policy.json"
DENO_POLICY = POLICIES / "ordered-map-deno-sandbox-policy.json"
NATIVE_PLAN = PLANS / "native-conformance-plan.json"
DENO_PLAN = PLANS / "deno-conformance-plan.json"

EXPECTED_RAW_SHA256 = {
    NATIVE_PROFILE: "788481758572ec2d94d3e97b009b9ca30e0322d07b93dcb37b6417243fffc450",
    DENO_PROFILE: "4629a98d62ae9ab59bebefcab5eab2306eeef8df0b19f80b6cc594f1f5adb1bf",
    NATIVE_POLICY: "1370368902b920743bdf3a24f6eab637fbee27d4e1d99e864104feeafc0b03fc",
    DENO_POLICY: "4266acfe9a658420805f0ce16ed0e49454e0ecb557f49bcb9c094960947b9df1",
    NATIVE_PLAN: "4ad983583dc4558c9321d3c2b7a8089f7f41aa25e391b5ffeac5875a9a28d932",
    DENO_PLAN: "bedd5199c9958ea127c77f4f8646a71a282305b88487854cd2ce4338d76ad0d9",
}
EXPECTED_CANONICAL_PLAN_SHA256 = {
    NATIVE_PLAN: "8cd414cf900f571994e081788cebf5f5c7c73964efd43f7384c2089b1fb0b472",
    DENO_PLAN: "57cdeb9d881a272e9c591920cc6bf43d426cbd6310951a99c90797aa91cdb5b4",
}
EXPECTED_PREDECESSOR_SHA256 = {
    OLD_MANIFEST: "0dae972b40c850f691df0856577cf8a9d66449a4655dcbb0c328b20c6993455d",
    O8_MANIFEST: "f5e87e65c4765865203158cdd6cbfbf46774dd7d068ddadeaa37c41a5f6ffaf3",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(document: dict) -> str:
    content = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _address(document: dict) -> tuple[str, str, str]:
    return tuple(document[key] for key in ("kind", "id", "version"))


class OrderedMapProfileChoiceArtifactTest(unittest.TestCase):
    def test_exact_artifact_bytes_are_frozen(self) -> None:
        self.assertEqual(
            EXPECTED_RAW_SHA256,
            {path: _raw_sha256(path) for path in EXPECTED_RAW_SHA256},
        )

    def test_profiles_promote_reviewed_probe_bytes_without_hidden_defaults(self) -> None:
        schemas = record_check.SchemaRegistry()
        validator = schemas.validator_for("realizationProfile")
        for final, candidate in (
            (NATIVE_PROFILE, PROBE / "native-profile.json"),
            (DENO_PROFILE, PROBE / "deno-profile.json"),
        ):
            with self.subTest(final=final):
                document = _load(final)
                self.assertEqual(_load(candidate), document)
                self.assertEqual([], list(validator.iter_errors(document)))

    def test_policies_preserve_every_predecessor_concern_and_prohibition(self) -> None:
        errors = record_check.validate_graph_paths(
            [
                str(SPECIFICATION),
                str(OLD_PROFILE),
                str(PROFILES),
                str(POLICIES),
            ]
        )
        self.assertEqual([], errors)
        predecessor = _load(OLD_POLICY)
        expected = {
            NATIVE_POLICY: (
                "ordered-map-native-process-policy",
                "ordered-map-native-process",
            ),
            DENO_POLICY: (
                "ordered-map-deno-sandbox-policy",
                "ordered-map-deno-sandbox",
            ),
        }
        for path, (policy_id, profile_id) in expected.items():
            with self.subTest(path=path):
                candidate = _load(path)
                projected = deepcopy(predecessor)
                projected["id"] = policy_id
                projected["profile"]["id"] = profile_id
                self.assertEqual(projected, candidate)
                self.assertEqual(
                    ("consumerPolicy", policy_id, "0.1.0"),
                    _address(candidate),
                )

    def test_plans_are_schema_valid_and_change_only_the_profile_binding(self) -> None:
        schema = _load(PLAN_SCHEMA)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        base = _load(BASE_PLAN)
        expected = {
            NATIVE_PLAN: NATIVE_PROFILE,
            DENO_PLAN: DENO_PROFILE,
        }
        for plan_path, profile_path in expected.items():
            with self.subTest(plan=plan_path):
                plan = _load(plan_path)
                self.assertEqual([], list(validator.iter_errors(plan)))
                projected = deepcopy(base)
                profile = _load(profile_path)
                projected["profile"] = {
                    "path": profile_path.relative_to(ROOT).as_posix(),
                    "address": {
                        "kind": profile["kind"],
                        "id": profile["id"],
                        "version": profile["version"],
                    },
                    "sha256": _raw_sha256(profile_path),
                }
                self.assertEqual(projected, plan)
                self.assertEqual(
                    EXPECTED_CANONICAL_PLAN_SHA256[plan_path],
                    _canonical_sha256(plan),
                )

    def test_artifacts_are_inputs_not_a_premature_product_authority(self) -> None:
        self.assertEqual(
            EXPECTED_PREDECESSOR_SHA256,
            {path: _raw_sha256(path) for path in EXPECTED_PREDECESSOR_SHA256},
        )
        self.assertFalse(PROFILE_CHOICE_MANIFEST.exists())


if __name__ == "__main__":
    unittest.main()
