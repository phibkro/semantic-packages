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
SUCCESSOR_MANIFEST = REGISTRY / "successor-manifest.json"
PROFILE = ("realizationProfile", "stack-default", "0.1.0")
OLD_SPEC = ("specification", "stack", "0.1.0")
NEW_SPEC = ("specification", "stack", "0.2.0")
OLD_POLICY = ("consumerPolicy", "stack-bounded-policy", "0.1.0")
NEW_POLICY = ("consumerPolicy", "stack-bounded-policy", "0.2.0")
NEW_REALIZATION = ("realization", "stack-rust", "0.2.0")
NEW_CLAIMS = {
    ("claim", "stack-rust-pop-empty", "0.2.0"),
    ("claim", "stack-rust-pop-push", "0.2.0"),
    ("claim", "stack-rust-persistence", "0.2.0"),
    ("claim", "stack-rust-stack-effects", "0.2.0"),
}

try:
    maintenance = importlib.import_module("semantic_packages.maintenance")
    MAINTENANCE_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.maintenance":
        raise
    maintenance = None
    MAINTENANCE_IMPORT_ERROR = error


def _write_json(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


class SuccessorRecoveryPreconditionTest(unittest.TestCase):
    def test_predecessor_graph_and_default_remain_exact(self) -> None:
        observation = graph.inspect_stack_graph(MANIFEST)
        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(24, len(observation.records))
        self.assertEqual(MANIFEST.resolve(), graph.DEFAULT_STACK_MANIFEST.resolve())

    def test_successor_manifest_is_an_intentional_red_predecessor(self) -> None:
        self.assertTrue(
            SUCCESSOR_MANIFEST.is_file(),
            "J5-F1 precedes registry/stack/successor-manifest.json",
        )

    def test_maintenance_module_is_an_intentional_red_predecessor(self) -> None:
        self.assertIsNotNone(
            maintenance,
            "J5-F1 precedes semantic_packages/maintenance.py; "
            f"observed {MAINTENANCE_IMPORT_ERROR!r}",
        )


@unittest.skipIf(
    maintenance is None or not SUCCESSOR_MANIFEST.is_file(),
    "J5-F1 freezes recovery before successor records and maintenance exist",
)
class SuccessorRecoveryContractTest(unittest.TestCase):
    def _observe(self, successor=None):
        predecessor = graph.inspect_stack_graph(MANIFEST)
        successor = successor or graph.inspect_stack_graph(SUCCESSOR_MANIFEST)
        return maintenance.inspect_stack_successor(
            predecessor,
            successor,
            predecessor_policy=OLD_POLICY,
            successor_policy=NEW_POLICY,
            profile=PROFILE,
            predecessor_specification=OLD_SPEC,
            successor_specification=NEW_SPEC,
        )

    def test_successor_manifest_is_a_field_identical_append_only_revision(self) -> None:
        diagnostics = maintenance.compare_manifest_revisions(
            MANIFEST, SUCCESSOR_MANIFEST
        )
        self.assertEqual((), diagnostics)

        with tempfile.TemporaryDirectory(prefix="j5-manifest-") as raw:
            attacked = Path(raw) / "successor-manifest.json"
            document = json.loads(SUCCESSOR_MANIFEST.read_text(encoding="utf-8"))
            document["members"][0]["sha256"] = "0" * 64
            _write_json(attacked, document)
            attacked_diagnostics = maintenance.compare_manifest_revisions(
                MANIFEST, attacked
            )
        self.assertIn(
            "SUCCESSOR_PREDECESSOR_MEMBER_DRIFT",
            [item.code for item in attacked_diagnostics],
        )

    def test_successor_graph_adds_exactly_seven_actor_owned_records(self) -> None:
        successor = graph.inspect_stack_graph(SUCCESSOR_MANIFEST)
        self.assertTrue(successor.ok, successor.diagnostics)
        self.assertEqual(31, len(successor.records))
        observation = self._observe(successor)
        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertTrue(observation.predecessor_preserved)
        self.assertEqual(
            {NEW_SPEC, NEW_POLICY, NEW_REALIZATION} | NEW_CLAIMS,
            set(observation.added_addresses),
        )

    def test_failed_successor_recovers_to_acceptable_predecessor_in_same_graph(self) -> None:
        observation = self._observe()
        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(
            {
                ("realization", "stack-rust", "0.1.0"),
                ("realization", "stack-typescript", "0.1.0"),
            },
            set(observation.recovery_candidates),
        )
        self.assertTrue(
            all(
                candidate.semantic_status == "acceptable"
                for candidate in observation.predecessor_resolution.candidates
            )
        )
        self.assertEqual(
            (NEW_REALIZATION,),
            tuple(
                candidate.realization
                for candidate in observation.successor_resolution.candidates
            ),
        )
        successor = observation.successor_resolution.candidates[0]
        self.assertEqual("unacceptable", successor.semantic_status)
        self.assertTrue(
            all(
                concern.status == "unsupported"
                for concern in successor.concerns
                if concern.priority == "required"
            )
        )

    def test_predecessor_evidence_is_history_not_successor_support(self) -> None:
        observation = self._observe()
        self.assertEqual(9, len(observation.stale_evidence))
        selected = set()
        for candidate in observation.successor_resolution.candidates:
            for concern in candidate.concerns:
                selected.update(concern.supporting_evidence)
                selected.update(concern.challenging_evidence)
                selected.update(concern.inconclusive_evidence)
                selected.update(concern.error_evidence)
                selected.update(concern.inapplicable_evidence)
                selected.update(concern.unselected_evidence)
            for prohibition in candidate.prohibitions:
                selected.update(prohibition.supporting_evidence)
                selected.update(prohibition.challenging_evidence)
                selected.update(prohibition.inconclusive_evidence)
                selected.update(prohibition.error_evidence)
                selected.update(prohibition.inapplicable_evidence)
                selected.update(prohibition.unselected_evidence)
        self.assertEqual(set(), selected)
        self.assertTrue(
            all(item.reason == "exact-specification-version" for item in observation.stale_evidence)
        )

    def test_successor_projection_has_no_inherited_proof_or_lineage(self) -> None:
        observation = self._observe()
        view = observation.successor_theory.view
        self.assertEqual(NEW_SPEC, view.specification)
        self.assertEqual((), view.contradictions)
        self.assertTrue(view.unknowns)
        self.assertTrue(all(not declaration.claims for declaration in view.declarations))

    def test_no_implicit_latest_or_cross_version_policy_binding(self) -> None:
        successor = graph.inspect_stack_graph(SUCCESSOR_MANIFEST)
        mismatched = maintenance.resolve_exact(
            successor,
            policy=NEW_POLICY,
            profile=PROFILE,
            specification=OLD_SPEC,
        )
        self.assertFalse(mismatched.ok)
        self.assertEqual((), mismatched.candidates)
        self.assertIn(
            "RESOLUTION_POLICY_SELECTOR_MISMATCH",
            [item.code for item in mismatched.diagnostics],
        )
        for path in (
            ROOT / "semantic_packages/graph.py",
            ROOT / "semantic_packages/resolver.py",
            ROOT / "semantic_packages/theory_projection.py",
            ROOT / "semantic_packages/maintenance.py",
        ):
            self.assertNotIn("successor-manifest", path.read_text(encoding="utf-8"))

    def test_retired_and_withdrawn_claims_stay_lifecycle_not_evidence_axes(self) -> None:
        for state in ("retired", "withdrawn"):
            with self.subTest(state=state), tempfile.TemporaryDirectory(
                prefix="j5-lifecycle-"
            ) as raw:
                registry = Path(raw) / "registry" / "stack"
                shutil.copytree(REGISTRY, registry)
                manifest_path = registry / "successor-manifest.json"
                claim_path = (
                    registry
                    / "successors/j5/packages/rust/stack-rust-pop-push-claim.json"
                )
                claim = json.loads(claim_path.read_text(encoding="utf-8"))
                claim["state"] = state
                _write_json(claim_path, claim)
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                member = next(
                    item
                    for item in manifest["members"]
                    if item["address"]
                    == {"kind": "claim", "id": "stack-rust-pop-push", "version": "0.2.0"}
                )
                member["sha256"] = hashlib.sha256(claim_path.read_bytes()).hexdigest()
                _write_json(manifest_path, manifest)
                changed = graph.inspect_stack_graph(manifest_path)
                self.assertTrue(changed.ok, changed.diagnostics)
                observation = self._observe(changed)
                self.assertIn(
                    (("claim", "stack-rust-pop-push", "0.2.0"), state),
                    observation.successor_claim_states,
                )
                law = next(
                    concern
                    for concern in observation.successor_resolution.candidates[0].concerns
                    if concern.concern == "law.conformance"
                )
                self.assertIn("inapplicable-claim", law.reasons)
                self.assertEqual((), law.supporting_evidence)

    def test_maintenance_observation_uses_no_io_or_execution_after_graph_load(self) -> None:
        predecessor = graph.inspect_stack_graph(MANIFEST)
        successor = graph.inspect_stack_graph(SUCCESSOR_MANIFEST)
        touched = []

        def reject(name):
            def fail(*_args, **_kwargs):
                touched.append(name)
                raise AssertionError(f"maintenance attempted {name}")
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
            observation = maintenance.inspect_stack_successor(
                predecessor,
                successor,
                predecessor_policy=OLD_POLICY,
                successor_policy=NEW_POLICY,
                profile=PROFILE,
                predecessor_specification=OLD_SPEC,
                successor_specification=NEW_SPEC,
            )
        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual([], touched)


if __name__ == "__main__":
    unittest.main()
