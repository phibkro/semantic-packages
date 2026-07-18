from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from semantic_packages import graph


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry" / "stack"
MANIFEST = REGISTRY / "manifest.json"

POLICY = ("consumerPolicy", "stack-bounded-policy", "0.1.0")
PROFILE = ("realizationProfile", "stack-default", "0.1.0")
SPECIFICATION = ("specification", "stack", "0.1.0")
REALIZATIONS = {
    ("realization", "stack-rust", "0.1.0"),
    ("realization", "stack-typescript", "0.1.0"),
}

try:
    resolver = importlib.import_module("semantic_packages.resolver")
    RESOLVER_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.resolver":
        raise
    resolver = None
    RESOLVER_IMPORT_ERROR = error


def _write_json(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class PackageResolutionPreconditionTest(unittest.TestCase):
    def test_canonical_graph_is_the_only_product_input(self) -> None:
        observation = graph.inspect_stack_graph(MANIFEST)
        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(24, len(observation.records))
        self.assertEqual(
            {POLICY, PROFILE, SPECIFICATION} | REALIZATIONS,
            {
                record.address
                for record in observation.records
                if record.address in {POLICY, PROFILE, SPECIFICATION} | REALIZATIONS
            },
        )

    def test_resolver_module_is_the_only_red_predecessor(self) -> None:
        self.assertIsNotNone(
            resolver,
            "J4P-F1 intentionally precedes semantic_packages/resolver.py; "
            f"observed {RESOLVER_IMPORT_ERROR!r}",
        )


@unittest.skipIf(
    resolver is None,
    "J4P-F1 freezes the package-consumer contract before resolver.py exists",
)
class PackageResolutionContractTest(unittest.TestCase):
    def _resolve(self, observation):
        return resolver.resolve_stack(
            observation,
            policy=POLICY,
            profile=PROFILE,
            specification=SPECIFICATION,
        )

    def _copy_registry(self, raw: str) -> tuple[Path, Path]:
        registry = Path(raw) / "registry" / "stack"
        shutil.copytree(REGISTRY, registry)
        return registry, registry / "manifest.json"

    def _mutated_graph(self, relative: str, mutate):
        return self._changed_graph(((relative, mutate),))

    def _changed_graph(self, mutations=(), removals=()):
        with tempfile.TemporaryDirectory(prefix="j4p-graph-") as raw:
            registry, manifest_path = self._copy_registry(raw)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            removed = set()
            for relative in removals:
                record_path = registry / relative
                document = json.loads(record_path.read_text(encoding="utf-8"))
                removed.add((document["kind"], document["id"], document["version"]))
                record_path.unlink()
            manifest["members"] = [
                member
                for member in manifest["members"]
                if (
                    member["address"]["kind"],
                    member["address"]["id"],
                    member["address"]["version"],
                )
                not in removed
            ]
            for relative, mutate in mutations:
                record_path = registry / relative
                document = json.loads(record_path.read_text(encoding="utf-8"))
                mutate(document)
                _write_json(record_path, document)
                address = (document["kind"], document["id"], document["version"])
                member = next(
                    item
                    for item in manifest["members"]
                    if (
                        item["address"]["kind"],
                        item["address"]["id"],
                        item["address"]["version"],
                    )
                    == address
                )
                member["sha256"] = hashlib.sha256(record_path.read_bytes()).hexdigest()
            _write_json(manifest_path, manifest)
            observation = graph.inspect_stack_graph(manifest_path)
        self.assertTrue(observation.ok, observation.diagnostics)
        return observation

    def _without_records(self, relatives: tuple[str, ...]):
        with tempfile.TemporaryDirectory(prefix="j4p-remove-") as raw:
            registry, manifest_path = self._copy_registry(raw)
            removed = set()
            for relative in relatives:
                path = registry / relative
                document = json.loads(path.read_text(encoding="utf-8"))
                removed.add((document["kind"], document["id"], document["version"]))
                path.unlink()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["members"] = [
                member
                for member in manifest["members"]
                if (
                    member["address"]["kind"],
                    member["address"]["id"],
                    member["address"]["version"],
                )
                not in removed
            ]
            _write_json(manifest_path, manifest)
            observation = graph.inspect_stack_graph(manifest_path)
        self.assertTrue(observation.ok, observation.diagnostics)
        return observation

    @staticmethod
    def _candidate(result, realization):
        return next(item for item in result.candidates if item.realization == realization)

    @staticmethod
    def _concern(candidate, concern):
        return next(item for item in candidate.concerns if item.concern == concern)

    def test_canonical_candidates_are_semantically_acceptable_and_explainable(self) -> None:
        result = self._resolve(graph.inspect_stack_graph(MANIFEST))
        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual(REALIZATIONS, {item.realization for item in result.candidates})
        for candidate in result.candidates:
            with self.subTest(realization=candidate.realization):
                self.assertEqual("acceptable", candidate.semantic_status)
                self.assertEqual("satisfied", self._concern(candidate, "law.conformance").status)
                self.assertEqual("satisfied", self._concern(candidate, "resource.persistence").status)
                self.assertEqual("satisfied", self._concern(candidate, "effect.conformance").status)
                performance = self._concern(candidate, "performance")
                self.assertEqual("unsupported", performance.status)
                self.assertEqual("optional", performance.priority)
                self.assertFalse(performance.blocks)
                self.assertEqual("satisfied", candidate.prohibitions[0].status)
                self.assertIn("adapter-observed", " ".join(candidate.prohibitions[0].assumptions).lower())
                self.assertIn("outside", " ".join(candidate.prohibitions[0].exclusions).lower())

    def test_semantic_acceptance_stays_separate_from_directional_boundary(self) -> None:
        result = self._resolve(graph.inspect_stack_graph(MANIFEST))
        for candidate in result.candidates:
            self.assertEqual("acceptable", candidate.semantic_status)
            self.assertFalse(candidate.boundary.direct)
            self.assertEqual("consumer-to-realization", candidate.boundary.direction)
            self.assertEqual("child-process-ndjson", candidate.boundary.mechanism)
            self.assertNotEqual(candidate.semantic_status, candidate.boundary.mechanism)

    def test_selected_challenge_makes_composable_candidate_semantically_unacceptable(self) -> None:
        observation = self._mutated_graph(
            "packages/rust/records/stack-rust-pop-push-evidence.json",
            lambda document: document.update(result="challenges"),
        )
        result = self._resolve(observation)
        rust = self._candidate(result, ("realization", "stack-rust", "0.1.0"))
        self.assertEqual("unacceptable", rust.semantic_status)
        law = self._concern(rust, "law.conformance")
        self.assertEqual("contested", law.status)
        self.assertTrue(law.challenging_evidence)
        self.assertEqual("child-process-ndjson", rust.boundary.mechanism)

    def test_missing_claim_cannot_satisfy_assurance_vacuously(self) -> None:
        observation = self._without_records(
            (
                "packages/rust/records/stack-rust-pop-push-claim.json",
                "packages/rust/records/stack-rust-pop-push-evidence.json",
            )
        )
        rust = self._candidate(
            self._resolve(observation),
            ("realization", "stack-rust", "0.1.0"),
        )
        self.assertEqual("unacceptable", rust.semantic_status)
        law = self._concern(rust, "law.conformance")
        self.assertEqual("unsupported", law.status)
        self.assertIn("pop-push", law.missing_declarations)

    def test_omitted_mechanisms_and_unknown_assurance_fail_closed(self) -> None:
        attacks = (
            lambda policy: policy["concerns"][0].pop("acceptedMechanisms"),
            lambda policy: policy["concerns"][0].update(minimumAssurance="unknown-token"),
        )
        for mutate in attacks:
            with self.subTest(mutate=mutate):
                observation = self._mutated_graph(
                    "consumers/package/records/stack-bounded-policy.json", mutate
                )
                result = self._resolve(observation)
                for candidate in result.candidates:
                    law = self._concern(candidate, "law.conformance")
                    self.assertEqual("policy-incomplete", law.status)
                    self.assertTrue(law.blocks)
                    self.assertEqual("unacceptable", candidate.semantic_status)

    def test_unaccepted_assertion_does_not_substitute_for_campaign_evidence(self) -> None:
        observation = self._mutated_graph(
            "packages/rust/records/stack-rust-persistence-evidence.json",
            lambda document: document.update(mechanism="assertion"),
        )
        rust = self._candidate(
            self._resolve(observation),
            ("realization", "stack-rust", "0.1.0"),
        )
        persistence = self._concern(rust, "resource.persistence")
        self.assertEqual("unsupported", persistence.status)
        self.assertEqual((), persistence.supporting_evidence)
        self.assertIn("unacceptable-mechanism", persistence.reasons)
        self.assertTrue(persistence.unselected_evidence)
        self.assertEqual("unacceptable", rust.semantic_status)

    def test_accepted_inconclusive_and_error_attempts_remain_visible(self) -> None:
        for outcome, field in (
            ("inconclusive", "inconclusive_evidence"),
            ("error", "error_evidence"),
        ):
            with self.subTest(outcome=outcome):
                observation = self._mutated_graph(
                    "packages/rust/records/stack-rust-pop-push-evidence.json",
                    lambda document, outcome=outcome: document.update(result=outcome),
                )
                rust = self._candidate(
                    self._resolve(observation),
                    ("realization", "stack-rust", "0.1.0"),
                )
                law = self._concern(rust, "law.conformance")
                self.assertEqual("unsupported", law.status)
                self.assertTrue(getattr(law, field))
                self.assertIn(f"{outcome}-evidence", law.reasons)
                self.assertIn("pop-push", law.missing_declarations)

    def test_inapplicable_claim_and_evidence_remain_visible(self) -> None:
        observation = self._changed_graph(
            (
                (
                    "packages/rust/records/stack-rust-pop-push-claim.json",
                    lambda document: document.update(applicableProfiles=[]),
                ),
                (
                    "packages/rust/records/stack-rust-pop-push-evidence.json",
                    lambda document: document["applicability"].update(profiles=[]),
                ),
            )
        )
        rust = self._candidate(
            self._resolve(observation),
            ("realization", "stack-rust", "0.1.0"),
        )
        law = self._concern(rust, "law.conformance")
        self.assertEqual("unsupported", law.status)
        self.assertTrue(law.inapplicable_evidence)
        self.assertIn("inapplicable-evidence", law.reasons)
        self.assertIn("pop-push", law.missing_declarations)

    def test_explicit_accept_none_is_distinct_from_incomplete_or_absent_evidence(self) -> None:
        observation = self._mutated_graph(
            "consumers/package/records/stack-bounded-policy.json",
            lambda document: document["concerns"][0].update(acceptedMechanisms=[]),
        )
        for candidate in self._resolve(observation).candidates:
            law = self._concern(candidate, "law.conformance")
            self.assertEqual("unsupported", law.status)
            self.assertIn("accept-none", law.reasons)
            self.assertTrue(law.unselected_evidence)
            self.assertNotEqual("policy-incomplete", law.status)

        absent = self._without_records(
            ("packages/rust/records/stack-rust-pop-push-evidence.json",)
        )
        rust = self._candidate(
            self._resolve(absent),
            ("realization", "stack-rust", "0.1.0"),
        )
        law = self._concern(rust, "law.conformance")
        self.assertIn("absent-evidence", law.reasons)
        self.assertNotIn("accept-none", law.reasons)
        self.assertEqual((), law.unselected_evidence)

    def test_explicit_accept_no_observation_scope_is_not_policy_omission(self) -> None:
        observation = self._mutated_graph(
            "consumers/package/records/stack-bounded-policy.json",
            lambda document: document["prohibitions"][0].update(
                acceptedEvidenceScope=[]
            ),
        )
        for candidate in self._resolve(observation).candidates:
            prohibition = candidate.prohibitions[0]
            self.assertEqual("unsupported", prohibition.status)
            self.assertIn("accept-none-scope", prohibition.reasons)
            self.assertTrue(prohibition.unselected_evidence)
            self.assertNotEqual("policy-incomplete", prohibition.status)

    def test_unaccepted_review_state_remains_visible_but_cannot_support(self) -> None:
        observation = self._mutated_graph(
            "packages/rust/records/stack-rust-persistence-evidence.json",
            lambda document: document.update(reviewState="rejected"),
        )
        rust = self._candidate(
            self._resolve(observation),
            ("realization", "stack-rust", "0.1.0"),
        )
        persistence = self._concern(rust, "resource.persistence")
        self.assertEqual("unsupported", persistence.status)
        self.assertTrue(persistence.unselected_evidence)
        self.assertIn("unaccepted-review-state", persistence.reasons)

    def test_inconclusive_effect_observation_does_not_disappear_or_prove_absence(self) -> None:
        observation = self._mutated_graph(
            "packages/rust/records/stack-rust-stack-effects-evidence.json",
            lambda document: document.update(result="inconclusive"),
        )
        rust = self._candidate(
            self._resolve(observation),
            ("realization", "stack-rust", "0.1.0"),
        )
        prohibition = rust.prohibitions[0]
        self.assertEqual("unsupported", prohibition.status)
        self.assertTrue(prohibition.inconclusive_evidence)
        self.assertIn("inconclusive-evidence", prohibition.reasons)
        self.assertEqual("unacceptable", rust.semantic_status)

    def test_zero_specification_coverage_never_satisfies_a_policy_concern(self) -> None:
        performance_absent = self._mutated_graph(
            "theory/records/stack-spec.json",
            lambda document: document.pop("performancePropositions"),
        )
        for candidate in self._resolve(performance_absent).candidates:
            performance = self._concern(candidate, "performance")
            self.assertEqual("no-coverage", performance.status)
            self.assertFalse(performance.blocks)
            self.assertIn("no-declarations", performance.reasons)

        law_relatives = tuple(
            relative
            for relative in (
                "theory/records/pop-empty-spec-claim.json",
                "theory/records/stack-pop-empty-model-proof-evidence.json",
                "packages/rust/records/stack-rust-pop-empty-claim.json",
                "packages/rust/records/stack-rust-pop-empty-evidence.json",
                "packages/rust/records/stack-rust-pop-push-claim.json",
                "packages/rust/records/stack-rust-pop-push-evidence.json",
                "packages/typescript/records/stack-typescript-pop-empty-claim.json",
                "packages/typescript/records/stack-typescript-pop-empty-evidence.json",
                "packages/typescript/records/stack-typescript-pop-push-claim.json",
                "packages/typescript/records/stack-typescript-pop-push-evidence.json",
            )
        )
        laws_absent = self._changed_graph(
            (("theory/records/stack-spec.json", lambda document: document.pop("laws")),),
            law_relatives,
        )
        for candidate in self._resolve(laws_absent).candidates:
            law = self._concern(candidate, "law.conformance")
            self.assertEqual("no-coverage", law.status)
            self.assertTrue(law.blocks)
            self.assertIn("no-declarations", law.reasons)
            self.assertEqual("unacceptable", candidate.semantic_status)

    def test_effect_scope_requires_exact_governed_plan_provenance(self) -> None:
        observation = self._mutated_graph(
            "packages/rust/records/stack-rust-stack-effects-evidence.json",
            lambda document: document["provenance"].update(planSha256="0" * 64),
        )
        rust = self._candidate(
            self._resolve(observation),
            ("realization", "stack-rust", "0.1.0"),
        )
        self.assertEqual("unacceptable", rust.semantic_status)
        self.assertEqual("unsupported", rust.prohibitions[0].status)

    def test_exact_selectors_and_successful_graph_are_required(self) -> None:
        canonical = graph.inspect_stack_graph(MANIFEST)
        missing = resolver.resolve_stack(
            canonical,
            policy=("consumerPolicy", "absent", "0.1.0"),
            profile=PROFILE,
            specification=SPECIFICATION,
        )
        self.assertFalse(missing.ok)
        self.assertEqual((), missing.candidates)
        self.assertIn("RESOLUTION_SELECTOR_NOT_FOUND", [d.code for d in missing.diagnostics])

        invalid_graph = graph.GraphObservation(
            canonical.records,
            (graph._diagnostic("GRAPH_TEST_INVALID", "."),),
        )
        invalid = self._resolve(invalid_graph)
        self.assertFalse(invalid.ok)
        self.assertEqual((), invalid.candidates)
        self.assertIn("RESOLUTION_INVALID_GRAPH", [d.code for d in invalid.diagnostics])

    def test_resolution_uses_no_filesystem_or_execution_boundary(self) -> None:
        canonical = graph.inspect_stack_graph(MANIFEST)
        touched = []

        def reject(name):
            def fail(*_args, **_kwargs):
                touched.append(name)
                raise AssertionError(f"resolver attempted {name}")

            return fail

        with ExitStack() as stack:
            for owner, name in (
                (subprocess, "run"),
                (subprocess, "Popen"),
                (os, "system"),
                (Path, "open"),
                (os, "scandir"),
            ):
                stack.enter_context(mock.patch.object(owner, name, side_effect=reject(name)))
            result = self._resolve(canonical)

        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual([], touched)


if __name__ == "__main__":
    unittest.main()
