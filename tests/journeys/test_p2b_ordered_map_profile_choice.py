from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
import os
import subprocess
import unittest
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest import mock

from scripts import record_check
from semantic_packages import (
    canonical_artifact,
    graph,
    ordered_map_inspection,
    ordered_map_maintenance,
    resolver,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "registry" / "ordered-map" / "profile-choice-manifest.json"
O8_MANIFEST = ROOT / "registry" / "ordered-map" / "successor-manifest.json"
OLD_MANIFEST = ROOT / "registry" / "ordered-map" / "manifest.json"
NATIVE_PLAN = ROOT / "contracts" / "ordered-map" / "profile-choice" / "native-conformance-plan.json"
DENO_PLAN = ROOT / "contracts" / "ordered-map" / "profile-choice" / "deno-conformance-plan.json"
NATIVE_PROFILE_PATH = ROOT / "registry" / "ordered-map" / "profile-choice" / "profiles" / "records" / "ordered-map-native-process.json"
DENO_PROFILE_PATH = ROOT / "registry" / "ordered-map" / "profile-choice" / "profiles" / "records" / "ordered-map-deno-sandbox.json"
NATIVE_POLICY_PATH = ROOT / "registry" / "ordered-map" / "profile-choice" / "consumers" / "records" / "ordered-map-native-process-policy.json"
DENO_POLICY_PATH = ROOT / "registry" / "ordered-map" / "profile-choice" / "consumers" / "records" / "ordered-map-deno-sandbox-policy.json"
NATIVE_REPORT = ROOT / "reports" / "ordered-map" / "profile-choice" / "rust-native-campaign-report.json"
DENO_REPORT = ROOT / "reports" / "ordered-map" / "profile-choice" / "typescript-deno-campaign-report.json"

SPECIFICATION = ("specification", "ordered-map", "0.1.0")
NATIVE_PROFILE = ("realizationProfile", "ordered-map-native-process", "0.1.0")
DENO_PROFILE = ("realizationProfile", "ordered-map-deno-sandbox", "0.1.0")
NATIVE_POLICY = ("consumerPolicy", "ordered-map-native-process-policy", "0.1.0")
DENO_POLICY = ("consumerPolicy", "ordered-map-deno-sandbox-policy", "0.1.0")
RUST = ("realization", "ordered-map-rust", "0.2.0")
TYPESCRIPT = ("realization", "ordered-map-typescript", "0.2.0")
DECISIONS = (
    (NATIVE_POLICY, NATIVE_PROFILE, RUST),
    (DENO_POLICY, DENO_PROFILE, TYPESCRIPT),
)
DECLARATIONS = (
    "lookup-empty",
    "lookup-put-other",
    "lookup-put-same",
    "ordered-map-effects",
    "persistence",
    "put-existing-position",
    "put-new-appends",
)
PACKAGE_PROFILES = {
    "ordered-map-rust": NATIVE_PROFILE,
    "ordered-map-typescript": DENO_PROFILE,
}
PACKAGE_REALIZATIONS = {
    "ordered-map-rust": RUST,
    "ordered-map-typescript": TYPESCRIPT,
}
PROFILE_PATHS = {
    NATIVE_PROFILE: NATIVE_PROFILE_PATH,
    DENO_PROFILE: DENO_PROFILE_PATH,
}
POLICY_PATHS = {
    NATIVE_POLICY: NATIVE_POLICY_PATH,
    DENO_POLICY: DENO_POLICY_PATH,
}
REPORT_INPUTS = {
    NATIVE_REPORT: (
        NATIVE_PLAN,
        "8cd414cf900f571994e081788cebf5f5c7c73964efd43f7384c2089b1fb0b472",
        NATIVE_PROFILE_PATH,
        "ordered-map-rust",
    ),
    DENO_REPORT: (
        DENO_PLAN,
        "57cdeb9d881a272e9c591920cc6bf43d426cbd6310951a99c90797aa91cdb5b4",
        DENO_PROFILE_PATH,
        "ordered-map-typescript",
    ),
}
EXPECTED_ADDED_SOURCES = (
    graph.ManifestSource(
        "ordered-map-profile-choice-profiles",
        "profile-choice/profiles/records",
        frozenset(("dependency",)),
    ),
    graph.ManifestSource(
        "ordered-map-profile-choice-rust",
        "profile-choice/packages/rust/records",
        frozenset(("package-authored",)),
    ),
    graph.ManifestSource(
        "ordered-map-profile-choice-typescript",
        "profile-choice/packages/typescript/records",
        frozenset(("package-authored",)),
    ),
    graph.ManifestSource(
        "ordered-map-profile-choice-consumer",
        "profile-choice/consumers/records",
        frozenset(("package-consumer-authored",)),
    ),
)
EXPECTED_RAW_SHA256 = {
    OLD_MANIFEST: "0dae972b40c850f691df0856577cf8a9d66449a4655dcbb0c328b20c6993455d",
    O8_MANIFEST: "f5e87e65c4765865203158cdd6cbfbf46774dd7d068ddadeaa37c41a5f6ffaf3",
    ROOT / "semantic_packages" / "resolver.py": "afd6d93378c3361da8a56a5114507b704c675a44c978efa2b54543d89684c8ea",
    ROOT / "semantic_packages" / "ordered_map_resolution.py": "eed151deda93c00ba665ca7270cb115666d808cdc1f473d2fccc202e52307a5e",
    ROOT / "semantic_packages" / "ordered_map_inspection.py": "ebabecee1c93ca4b498901226336fbc4c660761abcc9eef418d28ba9475a477c",
    ROOT / "semantic_packages" / "ordered_map_maintenance.py": "e217e7538745c3053d62f24c3cea574077c0ab88052e8436ae5b2cf990699091",
    NATIVE_PLAN: "4ad983583dc4558c9321d3c2b7a8089f7f41aa25e391b5ffeac5875a9a28d932",
    DENO_PLAN: "bedd5199c9958ea127c77f4f8646a71a282305b88487854cd2ce4338d76ad0d9",
    NATIVE_PROFILE_PATH: "788481758572ec2d94d3e97b009b9ca30e0322d07b93dcb37b6417243fffc450",
    DENO_PROFILE_PATH: "4629a98d62ae9ab59bebefcab5eab2306eeef8df0b19f80b6cc594f1f5adb1bf",
    NATIVE_POLICY_PATH: "1370368902b920743bdf3a24f6eab637fbee27d4e1d99e864104feeafc0b03fc",
    DENO_POLICY_PATH: "4266acfe9a658420805f0ce16ed0e49454e0ecb557f49bcb9c094960947b9df1",
}


def _import(name: str):
    try:
        return importlib.import_module(name), None
    except ModuleNotFoundError as error:
        if error.name != name:
            raise
        return None, error


profile_choice, PROFILE_CHOICE_IMPORT_ERROR = _import(
    "semantic_packages.ordered_map_profile_choice"
)
report_check, REPORT_CHECK_IMPORT_ERROR = _import(
    "scripts.ordered_map_profile_choice_report_check"
)
evidence_check, EVIDENCE_CHECK_IMPORT_ERROR = _import(
    "scripts.ordered_map_profile_choice_evidence_check"
)


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate(decision):
    return decision.candidate


def _concern(candidate, concern: str):
    return next(item for item in candidate.concerns if item.concern == concern)


def _address_document(address):
    return {"kind": address[0], "id": address[1], "version": address[2]}


def _package_addresses(package: str, version: str, kind: str) -> tuple:
    suffix = "" if kind == "claim" else "-conformance"
    return tuple(
        (kind, f"{package}-{declaration}{suffix}", version)
        for declaration in DECLARATIONS
    )


def _package_record_addresses(package: str) -> tuple:
    interleaved = tuple(
        address
        for declaration in DECLARATIONS
        for address in (
            ("claim", f"{package}-{declaration}", "0.2.0"),
            ("evidence", f"{package}-{declaration}-conformance", "0.2.0"),
        )
    )
    return (*interleaved, PACKAGE_REALIZATIONS[package])


EXPECTED_ADDED_ADDRESSES = (
    DENO_PROFILE,
    NATIVE_PROFILE,
    *_package_record_addresses("ordered-map-rust"),
    *_package_record_addresses("ordered-map-typescript"),
    DENO_POLICY,
    NATIVE_POLICY,
)


def _candidate_record_map() -> dict[Path, tuple]:
    records = {}
    for package in PACKAGE_PROFILES:
        root = Path("registry/ordered-map/profile-choice/packages") / package.removeprefix(
            "ordered-map-"
        ) / "records"
        for declaration in DECLARATIONS:
            records[root / f"{package}-{declaration}-claim.json"] = (
                "claim",
                f"{package}-{declaration}",
                "0.2.0",
            )
            records[root / f"{package}-{declaration}-evidence.json"] = (
                "evidence",
                f"{package}-{declaration}-conformance",
                "0.2.0",
            )
        records[root / f"{package}-realization.json"] = PACKAGE_REALIZATIONS[package]
    return records


def _expected_ledgers(package: str) -> tuple[set, set, set, set]:
    selected_claims = set(_package_addresses(package, "0.2.0", "claim"))
    selected_evidence = set(_package_addresses(package, "0.2.0", "evidence"))
    predecessor_claims = {
        *_package_addresses("ordered-map-rust", "0.1.0", "claim"),
        *_package_addresses("ordered-map-typescript", "0.1.0", "claim"),
    }
    predecessor_evidence = {
        *_package_addresses("ordered-map-rust", "0.1.0", "evidence"),
        *_package_addresses("ordered-map-typescript", "0.1.0", "evidence"),
    }
    other = next(candidate for candidate in PACKAGE_PROFILES if candidate != package)
    return (
        selected_claims,
        predecessor_claims | set(_package_addresses(other, "0.2.0", "claim")),
        selected_evidence,
        predecessor_evidence | set(_package_addresses(other, "0.2.0", "evidence")),
    )


def _derived_graph(observation, address, mutate):
    records = []
    for item in observation.records:
        if item.address != address:
            records.append(item)
            continue
        document = item.document
        mutate(document)
        records.append(
            replace(
                item,
                _document_text=json.dumps(
                    document, sort_keys=True, separators=(",", ":")
                ),
            )
        )
    return graph.GraphObservation(tuple(records), ())


def _without(observation, address):
    return graph.GraphObservation(
        tuple(item for item in observation.records if item.address != address),
        (),
    )


def _assert_structurally_rejected(test, observation) -> None:
    result = profile_choice.resolve_ordered_map_profile_choices(observation)
    test.assertFalse(result.ok)
    test.assertEqual((), result.decisions)


def _literal_assignment(module, name: str) -> str | None:
    tree = ast.parse(inspect.getsource(module))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Name)
            and target.id == name
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    return None


class ProfileChoiceRedPreconditionTest(unittest.TestCase):
    def test_p2a_and_predecessor_bytes_are_the_only_inputs(self) -> None:
        self.assertEqual(
            EXPECTED_RAW_SHA256,
            {path: _raw_sha256(path) for path in EXPECTED_RAW_SHA256},
        )
        self.assertEqual(PROFILE_CHOICE_IMPORT_ERROR is None, MANIFEST.exists())
        self.assertEqual(REPORT_CHECK_IMPORT_ERROR is None, NATIVE_REPORT.exists())
        self.assertEqual(REPORT_CHECK_IMPORT_ERROR is None, DENO_REPORT.exists())

    def test_p3_p4_surface_is_the_only_red_predecessor(self) -> None:
        missing = tuple(
            error
            for error in (
                PROFILE_CHOICE_IMPORT_ERROR,
                REPORT_CHECK_IMPORT_ERROR,
                EVIDENCE_CHECK_IMPORT_ERROR,
            )
            if error is not None
        )
        self.assertEqual((), missing, f"P2b intentionally precedes P3/P4: {missing!r}")


@unittest.skipUnless(
    profile_choice is not None
    and report_check is not None
    and evidence_check is not None,
    "P2b freezes P3/P4 before implementation",
)
class ProfileChoiceContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.observation = profile_choice.inspect_ordered_map_profile_choices()

    def test_fresh_reports_bind_exact_plan_profile_and_execution(self) -> None:
        errors, summary = report_check.run_profile_choice_report_checks(ROOT)
        self.assertEqual([], errors)
        self.assertEqual(
            "OrderedMap profile-choice report checks passed: 2 fresh profile-bound reports.",
            summary,
        )
        fresh = report_check.reproduce_profile_choice_reports(ROOT)
        self.assertEqual(
            {NATIVE_REPORT.relative_to(ROOT), DENO_REPORT.relative_to(ROOT)},
            set(fresh),
        )
        for path, (plan, canonical, profile, candidate) in REPORT_INPUTS.items():
            with self.subTest(path=path):
                relative = path.relative_to(ROOT)
                self.assertEqual(path.read_bytes(), fresh[relative])
                document = json.loads(fresh[relative])
                self.assertEqual(candidate, document["candidate"])
                self.assertEqual(
                    {
                        "path": plan.relative_to(ROOT).as_posix(),
                        "rawSha256": _raw_sha256(plan),
                        "canonicalSha256": canonical,
                    },
                    document["inputs"]["plan"],
                )
                self.assertEqual(
                    {
                        "path": profile.relative_to(ROOT).as_posix(),
                        "sha256": _raw_sha256(profile),
                    },
                    document["inputs"]["profile"],
                )
                self.assertEqual(canonical, document["outcome"]["planCanonicalSha256"])
                self.assertEqual("supports", document["outcome"]["result"])
                self.assertIn("realization-steps", document["outcome"]["exclusions"])

    def test_candidate_records_are_exact_link_valid_and_profile_singletons(self) -> None:
        errors, summary = evidence_check.run_profile_choice_evidence_checks(ROOT)
        self.assertEqual([], errors)
        self.assertEqual(
            "OrderedMap profile-choice Evidence checks passed: 2 Realizations, 14 Claims, 14 Evidence records.",
            summary,
        )
        records = evidence_check.load_profile_choice_candidate_records(ROOT)
        self.assertEqual(30, len(records))
        expected_records = _candidate_record_map()
        self.assertEqual(set(expected_records), set(records))
        self.assertEqual(
            expected_records,
            {path: record_check.address_of(item) for path, item in records.items()},
        )
        documents = tuple(records.values())
        self.assertEqual(2, sum(item["kind"] == "realization" for item in documents))
        self.assertEqual(14, sum(item["kind"] == "claim" for item in documents))
        self.assertEqual(14, sum(item["kind"] == "evidence" for item in documents))
        for path, item in records.items():
            package = next(name for name in PACKAGE_PROFILES if name in path.name)
            profile = PACKAGE_PROFILES[package]
            if item["kind"] == "realization":
                profiles = item["supportedProfiles"]
            elif item["kind"] == "claim":
                profiles = item["applicableProfiles"]
                self.assertNotEqual("performance", item["concern"])
            else:
                profiles = item["applicability"]["profiles"]
                report = NATIVE_REPORT if package == "ordered-map-rust" else DENO_REPORT
                plan, canonical, profile_path, candidate = REPORT_INPUTS[report]
                provenance = item["provenance"]
                self.assertEqual(
                    {
                        "path": report.relative_to(ROOT).as_posix(),
                        "sha256": _raw_sha256(report),
                    },
                    provenance["report"],
                )
                self.assertEqual(
                    {
                        "path": plan.relative_to(ROOT).as_posix(),
                        "rawSha256": _raw_sha256(plan),
                        "canonicalSha256": canonical,
                    },
                    provenance["plan"],
                )
                self.assertEqual(
                    {
                        "path": profile_path.relative_to(ROOT).as_posix(),
                        "sha256": _raw_sha256(profile_path),
                    },
                    provenance["profile"],
                )
                self.assertEqual(candidate, provenance["reportCandidate"])
            self.assertEqual(1, len(profiles))
            self.assertEqual([_address_document(profile)], profiles)

    def test_actor_is_zero_argument_one_capture_and_rejects_overrides(self) -> None:
        self.assertEqual(
            (),
            tuple(inspect.signature(profile_choice.inspect_ordered_map_profile_choices).parameters),
        )
        original_artifact = canonical_artifact.inspect_json_artifact
        original_graph = graph.inspect_manifest_graph
        with mock.patch.object(
            canonical_artifact, "inspect_json_artifact", wraps=original_artifact
        ) as manifest_capture, mock.patch.object(
            graph, "inspect_manifest_graph", wraps=original_graph
        ) as graph_capture, mock.patch.object(
            resolver,
            "resolve_stack",
            side_effect=AssertionError("profile-choice actor called Stack resolution"),
        ):
            result = profile_choice.inspect_ordered_map_profile_choices()
        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual(1, manifest_capture.call_count)
        call = manifest_capture.call_args
        self.assertEqual((MANIFEST,), call.args)
        pinned_digest = _literal_assignment(profile_choice, "_MANIFEST_RAW_SHA256")
        self.assertIsNotNone(pinned_digest)
        self.assertRegex(pinned_digest, r"^[0-9a-f]{64}$")
        self.assertEqual(pinned_digest, profile_choice._MANIFEST_RAW_SHA256)
        self.assertEqual(pinned_digest, _raw_sha256(MANIFEST))
        self.assertEqual(pinned_digest, call.kwargs["expected_raw_sha256"])
        graph_capture.assert_called_once_with(result.authority)
        for keyword, value in (
            ("manifest", MANIFEST),
            ("manifest_path", MANIFEST),
            ("contract", MANIFEST),
            ("policy", NATIVE_POLICY),
            ("profile", NATIVE_PROFILE),
            ("latest", True),
            ("version_range", ">=0.1.0"),
        ):
            with self.subTest(keyword=keyword), self.assertRaises(TypeError):
                profile_choice.inspect_ordered_map_profile_choices(**{keyword: value})

    def test_authority_is_exactly_o8_plus_34_and_immutable(self) -> None:
        result = self.observation
        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual(MANIFEST.resolve(), result.authority.manifest_path)
        self.assertEqual(69, len(result.graph.records))
        self.assertEqual(10, len(result.authority.sources))
        o8_authority = graph.inspect_manifest_authority(O8_MANIFEST)
        o8 = graph.inspect_manifest_graph(o8_authority)
        self.assertTrue(o8.ok, o8.diagnostics)
        self.assertEqual(o8_authority.sources, result.authority.sources[:6])
        self.assertEqual(o8_authority.members, result.authority.members[:35])
        self.assertEqual(EXPECTED_ADDED_SOURCES, result.authority.sources[6:])
        self.assertEqual(35, len(o8.records))
        self.assertEqual(
            EXPECTED_ADDED_ADDRESSES,
            tuple(member.address for member in result.authority.members[35:]),
        )
        self.assertEqual(
            {(item.address, item.sha256) for item in o8.records},
            {
                (item.address, item.sha256)
                for item in result.graph.records
                if item.address not in EXPECTED_ADDED_ADDRESSES
            },
        )
        self.assertEqual(
            set(EXPECTED_ADDED_ADDRESSES),
            {
                item.address
                for item in result.graph.records
                if item.address in EXPECTED_ADDED_ADDRESSES
            },
        )
        self.assertEqual(
            {
                (item.source, item.address, item.sha256, item.role)
                for item in result.authority.members
            },
            {
                (item.source, item.address, item.sha256, item.role)
                for item in result.graph.records
            },
        )
        with self.assertRaises((AttributeError, TypeError)):
            result.authority.sources[0].root = "changed"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            result.graph.records[0].address = ("x", "y", "z")  # type: ignore[misc]

    def test_two_exact_decisions_select_one_package_each(self) -> None:
        resolution = self.observation.resolution
        self.assertTrue(resolution.ok, resolution.diagnostics)
        self.assertEqual(DECISIONS, tuple((item.policy, item.profile, item.candidate.realization) for item in resolution.decisions))
        for decision in resolution.decisions:
            candidate = _candidate(decision)
            self.assertEqual("acceptable", candidate.semantic_status)
            for concern in ("law.conformance", "resource.persistence", "effect.conformance"):
                disposition = _concern(candidate, concern)
                self.assertEqual("satisfied", disposition.status)
                self.assertFalse(disposition.blocks)
            performance = _concern(candidate, "performance")
            self.assertEqual("optional", performance.priority)
            self.assertEqual("unsupported", performance.status)
            self.assertFalse(performance.blocks)
            self.assertEqual("satisfied", candidate.prohibitions[0].status)
            self.assertEqual("consumer-to-realization", candidate.boundary.direction)
            self.assertEqual("child-process-ndjson", candidate.boundary.mechanism)
            self.assertFalse(candidate.boundary.direct)

    def test_complete_claim_and_evidence_ledgers_are_7_selected_21_inapplicable(self) -> None:
        for decision in self.observation.resolution.decisions:
            with self.subTest(profile=decision.profile):
                package = next(
                    name
                    for name, realization in PACKAGE_REALIZATIONS.items()
                    if realization == decision.candidate.realization
                )
                selected_claims, inapplicable_claims, selected_evidence, inapplicable_evidence = (
                    _expected_ledgers(package)
                )
                self.assertEqual(7, len(decision.claims.selected_applicable))
                self.assertEqual(21, len(decision.claims.inapplicable))
                self.assertEqual(7, len(decision.evidence.selected_applicable))
                self.assertEqual(21, len(decision.evidence.inapplicable))
                self.assertEqual(selected_claims, set(decision.claims.selected_applicable))
                self.assertEqual(inapplicable_claims, set(decision.claims.inapplicable))
                self.assertEqual(selected_evidence, set(decision.evidence.selected_applicable))
                self.assertEqual(inapplicable_evidence, set(decision.evidence.inapplicable))
                self.assertTrue(
                    selected_claims.isdisjoint(inapplicable_claims)
                    and selected_evidence.isdisjoint(inapplicable_evidence)
                )

    def test_non_supporting_evidence_axes_fail_closed_and_remain_visible(self) -> None:
        evidence = ("evidence", "ordered-map-rust-lookup-empty-conformance", "0.2.0")
        result_attacks = (
            (lambda item: item.update(result="challenges"), "contested", "challenging_evidence"),
            (lambda item: item.update(result="inconclusive"), "unsupported", "inconclusive_evidence"),
            (lambda item: item.update(result="error"), "unsupported", "error_evidence"),
            (lambda item: item.update(mechanism="assertion"), "unsupported", "unselected_evidence"),
        )
        for mutate, status, field in result_attacks:
            with self.subTest(field=field):
                attacked = _derived_graph(self.observation.graph, evidence, mutate)
                result = profile_choice.resolve_ordered_map_profile_choices(attacked)
                decision = result.decisions[0]
                law = _concern(decision.candidate, "law.conformance")
                self.assertEqual("unacceptable", decision.candidate.semantic_status)
                self.assertEqual(status, law.status)
                self.assertEqual((evidence,), getattr(law, field))

        for review_state in ("unverified", "pending", "rejected", "superseded", "revoked"):
            with self.subTest(reviewState=review_state):
                attacked = _derived_graph(
                    self.observation.graph,
                    evidence,
                    lambda item, state=review_state: item.update(reviewState=state),
                )
                decision = profile_choice.resolve_ordered_map_profile_choices(attacked).decisions[0]
                law = _concern(decision.candidate, "law.conformance")
                self.assertEqual("unacceptable", decision.candidate.semantic_status)
                self.assertEqual("unsupported", law.status)
                self.assertEqual((evidence,), law.unselected_evidence)

    def test_missing_swapped_and_invalid_inputs_never_vacuously_satisfy(self) -> None:
        claim = ("claim", "ordered-map-rust-lookup-empty", "0.2.0")
        missing = profile_choice.resolve_ordered_map_profile_choices(_without(self.observation.graph, claim))
        self.assertFalse(missing.ok)
        self.assertEqual((), missing.decisions)

        old_evidence = (
            "evidence",
            "ordered-map-rust-lookup-empty-conformance",
            "0.1.0",
        )
        missing_inapplicable = profile_choice.resolve_ordered_map_profile_choices(
            _without(self.observation.graph, old_evidence)
        )
        self.assertFalse(missing_inapplicable.ok)
        self.assertEqual((), missing_inapplicable.decisions)

        invalid = profile_choice.resolve_ordered_map_profile_choices(
            graph.GraphObservation(
                self.observation.graph.records,
                (record_check.Diagnostic("P2B_INVALID", "<graph>", "#"),),
            )
        )
        self.assertFalse(invalid.ok)
        self.assertEqual((), invalid.decisions)

        rust_evidence = ("evidence", "ordered-map-rust-persistence-conformance", "0.2.0")
        typescript_evidence = (
            "evidence",
            "ordered-map-typescript-persistence-conformance",
            "0.2.0",
        )
        result = profile_choice.resolve_ordered_map_profile_choices(self.observation.graph)
        native, deno = result.decisions
        native_persistence = _concern(native.candidate, "resource.persistence")
        deno_persistence = _concern(deno.candidate, "resource.persistence")
        self.assertEqual("acceptable", native.candidate.semantic_status)
        self.assertIn(rust_evidence, native_persistence.supporting_evidence)
        self.assertIn(typescript_evidence, native_persistence.inapplicable_evidence)
        self.assertEqual("acceptable", deno.candidate.semantic_status)
        self.assertIn(typescript_evidence, deno_persistence.supporting_evidence)

    def test_exact_selectors_and_profile_sets_reject_generalization(self) -> None:
        selector_attacks = (
            lambda item: item["profile"].update(version="0.2.0"),
            lambda item: item["profile"].pop("version"),
            lambda item: item["profile"].update(version=">=0.1.0"),
            lambda item: item["profile"].update(latest=True),
        )
        for mutate in selector_attacks:
            with self.subTest(mutate=mutate):
                _assert_structurally_rejected(
                    self,
                    _derived_graph(self.observation.graph, NATIVE_POLICY, mutate),
                )

        rust_claim = ("claim", "ordered-map-rust-lookup-empty", "0.2.0")
        broadened = _derived_graph(
            self.observation.graph,
            rust_claim,
            lambda item: item["applicableProfiles"].append(_address_document(DENO_PROFILE)),
        )
        _assert_structurally_rejected(self, broadened)

        cross_selected = _derived_graph(
            self.observation.graph,
            TYPESCRIPT,
            lambda item: item["supportedProfiles"].append(_address_document(NATIVE_PROFILE)),
        )
        _assert_structurally_rejected(self, cross_selected)

        for field in ("concerns", "prohibitions"):
            with self.subTest(empty_policy_field=field):
                empty_policy = _derived_graph(
                    self.observation.graph,
                    NATIVE_POLICY,
                    lambda item, name=field: item.update({name: []}),
                )
                _assert_structurally_rejected(self, empty_policy)

    def test_false_performance_promotion_and_extra_records_fail_closed(self) -> None:
        claim = ("claim", "ordered-map-rust-lookup-empty", "0.2.0")
        promoted = _derived_graph(
            self.observation.graph,
            claim,
            lambda item: (
                item.update(concern="performance"),
                item["proposition"].update(declarationId="put-amortized-constant"),
            ),
        )
        _assert_structurally_rejected(self, promoted)

        extra = replace(
            self.observation.graph.records[-1],
            address=("claim", "ordered-map-extra", "0.2.0"),
        )
        _assert_structurally_rejected(
            self,
            graph.GraphObservation((*self.observation.graph.records, extra), ()),
        )

    def test_replaced_or_extra_authority_fails_before_record_loading(self) -> None:
        authority = self.observation.authority
        extra_member = replace(
            authority.members[-1],
            address=("claim", "ordered-map-extra", "0.2.0"),
        )
        extra_source = graph.ManifestSource(
            "ordered-map-profile-choice-extra",
            "profile-choice/extra/records",
            frozenset(("package-authored",)),
        )
        attacks = (
            replace(authority, members=authority.members[:-1]),
            replace(authority, members=(*authority.members, extra_member)),
            replace(
                authority,
                members=(replace(authority.members[0], sha256="0" * 64), *authority.members[1:]),
            ),
            replace(authority, sources=authority.sources[:-1]),
            replace(authority, sources=(*authority.sources, extra_source)),
            replace(
                authority,
                sources=(replace(authority.sources[0], root="changed"), *authority.sources[1:]),
            ),
        )
        for attacked in attacks:
            with self.subTest(sources=len(attacked.sources), members=len(attacked.members)), mock.patch.object(
                graph, "inspect_manifest_document", return_value=attacked
            ), mock.patch.object(
                graph,
                "inspect_manifest_graph",
                side_effect=AssertionError("records loaded after invalid exact authority"),
            ):
                result = profile_choice.inspect_ordered_map_profile_choices()
            self.assertFalse(result.ok)
            self.assertEqual((), result.resolution.decisions)

    def test_directional_boundary_neither_grants_nor_revokes_semantics(self) -> None:
        attacked = _derived_graph(
            self.observation.graph,
            RUST,
            lambda item: item["implementation"].update(interfaceMechanism="in-process FFI"),
        )
        decision = profile_choice.resolve_ordered_map_profile_choices(attacked).decisions[0]
        self.assertEqual("acceptable", decision.candidate.semantic_status)
        self.assertEqual("unsupported-interface", decision.candidate.boundary.mechanism)
        self.assertFalse(decision.candidate.boundary.direct)

    def test_inspection_explains_authority_evidence_ledgers_and_boundaries(self) -> None:
        output = self.observation.output
        for required in (
            "OrderedMap exact deployment-profile choices (no discovery or execution)",
            "graph records: 69, sources: 10",
            "consumerPolicy/ordered-map-native-process-policy/0.1.0",
            "realizationProfile/ordered-map-native-process/0.1.0",
            "realization/ordered-map-rust/0.2.0: semantic=acceptable",
            "consumerPolicy/ordered-map-deno-sandbox-policy/0.1.0",
            "realizationProfile/ordered-map-deno-sandbox/0.1.0",
            "realization/ordered-map-typescript/0.2.0: semantic=acceptable",
            "Claims: selected-applicable=7 inapplicable=21",
            "Evidence: selected-applicable=7 inapplicable=21",
            "performance: status=unsupported priority=optional blocks=no",
            "Directional realization boundary (not semantic acceptance)",
            "direction=consumer-to-realization mechanism=child-process-ndjson direct=no",
        ):
            self.assertIn(required, output)

    def test_capture_failure_purity_determinism_and_public_shape(self) -> None:
        touched: list[str] = []

        def reject(name):
            def fail(*_args, **_kwargs):
                touched.append(name)
                raise AssertionError(f"post-capture decision attempted {name}")

            return fail

        with ExitStack() as stack:
            for owner, name in (
                (subprocess, "run"),
                (subprocess, "Popen"),
                (os, "system"),
                (os, "scandir"),
                (Path, "open"),
            ):
                stack.enter_context(mock.patch.object(owner, name, side_effect=reject(name)))
            resolution = profile_choice.resolve_ordered_map_profile_choices(self.observation.graph)
            output = profile_choice.render_ordered_map_profile_choices(
                self.observation.authority,
                self.observation.graph,
                resolution,
            )
        self.assertTrue(resolution.ok, resolution.diagnostics)
        self.assertIn("semantic=acceptable", output)
        self.assertEqual([], touched)

        first = profile_choice.inspect_ordered_map_profile_choices()
        second = profile_choice.inspect_ordered_map_profile_choices()
        self.assertEqual(first, second)
        self.assertEqual(
            {"authority", "graph", "resolution", "output", "diagnostics"},
            set(vars(first)),
        )

    def test_stack_o6_o7_o8_regressions_remain_unchanged(self) -> None:
        accepted = ordered_map_inspection.inspect_ordered_map()
        successor = ordered_map_maintenance.inspect_ordered_map_maintenance()
        self.assertTrue(accepted.ok, accepted.diagnostics)
        self.assertTrue(successor.ok, successor.diagnostics)
        self.assertEqual(2, len(accepted.resolution.candidates))
        self.assertEqual(0, len(successor.successor_resolution.candidates))
        self.assertEqual(2, len(successor.recovery_candidates))


if __name__ == "__main__":
    unittest.main()
