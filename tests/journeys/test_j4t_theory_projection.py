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
STACK = ("specification", "stack", "0.1.0")
UNDO = ("specification", "undo-history", "0.1.0")
PROOF_CLAIM = ("claim", "stack-pop-empty-law", "0.1.0")
PROOF_EVIDENCE = ("evidence", "stack-pop-empty-model-proof", "0.1.0")

try:
    projection = importlib.import_module("semantic_packages.theory_projection")
    PROJECTION_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.theory_projection":
        raise
    projection = None
    PROJECTION_IMPORT_ERROR = error


def _write_json(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


class TheoryProjectionPreconditionTest(unittest.TestCase):
    def test_canonical_graph_contains_both_exact_theories(self) -> None:
        observation = graph.inspect_stack_graph(MANIFEST)
        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(
            {STACK, UNDO},
            {
                record.address
                for record in observation.records
                if record.address in {STACK, UNDO}
            },
        )

    def test_projection_module_is_the_only_red_predecessor(self) -> None:
        self.assertIsNotNone(
            projection,
            "J4T-F1 intentionally precedes theory_projection.py; "
            f"observed {PROJECTION_IMPORT_ERROR!r}",
        )


@unittest.skipIf(projection is None, "J4T-F1 freezes projection before implementation")
class TheoryProjectionContractTest(unittest.TestCase):
    def _project(self, observation, specification=STACK):
        return projection.project_theory(observation, specification=specification)

    def _mutated_graph(self, relative, mutate):
        with tempfile.TemporaryDirectory(prefix="j4t-graph-") as raw:
            registry = Path(raw) / "registry" / "stack"
            shutil.copytree(REGISTRY, registry)
            manifest_path = registry / "manifest.json"
            record_path = registry / relative
            document = json.loads(record_path.read_text(encoding="utf-8"))
            mutate(document)
            _write_json(record_path, document)
            address = (document["kind"], document["id"], document["version"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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
        return observation

    @staticmethod
    def _declaration(view, kind, declaration_id):
        return next(
            item
            for item in view.declarations
            if (item.kind, item.declaration_id) == (kind, declaration_id)
        )

    def test_stack_projection_exposes_exact_meaning_proof_and_unknowns(self) -> None:
        result = self._project(graph.inspect_stack_graph(MANIFEST))
        self.assertTrue(result.ok, result.diagnostics)
        view = result.view
        self.assertEqual(STACK, view.specification)
        self.assertEqual((), view.imports)
        self.assertEqual(
            {
                ("law", "pop-empty"),
                ("law", "pop-push"),
                ("resource", "persistence"),
                ("effect", "stack-effects"),
                ("performance", "push-amortized-constant"),
            },
            {
                (item.kind, item.declaration_id)
                for item in view.declarations
                if item.kind in {"law", "resource", "effect", "performance"}
            },
        )
        pop_empty = self._declaration(view, "law", "pop-empty")
        self.assertEqual("pop(empty) == None", pop_empty.content["statement"])
        self.assertEqual("supported-observation", pop_empty.observation)
        self.assertEqual((PROOF_CLAIM,), tuple(item.address for item in pop_empty.claims))
        self.assertEqual(
            (PROOF_EVIDENCE,),
            tuple(item.address for item in pop_empty.claims[0].evidence),
        )
        performance = self._declaration(
            view, "performance", "push-amortized-constant"
        )
        self.assertEqual("unclaimed", performance.observation)
        self.assertIn(
            ("performance", "push-amortized-constant"), view.unknowns
        )

    def test_exact_import_is_an_edge_and_never_a_namespace_merge(self) -> None:
        view = self._project(graph.inspect_stack_graph(MANIFEST), UNDO).view
        self.assertEqual(UNDO, view.specification)
        self.assertEqual((STACK,), tuple(item.specification for item in view.imports))
        self.assertTrue(view.imports[0].available)
        self.assertEqual(
            {("carrier", "UndoHistory")},
            {(item.kind, item.declaration_id) for item in view.declarations},
        )
        self.assertNotIn(("law", "pop-empty"), view.unknowns)

    def test_declaration_reordering_cannot_change_stable_references(self) -> None:
        canonical = self._project(graph.inspect_stack_graph(MANIFEST)).view

        def reverse(document):
            for field in ("operations", "laws"):
                document[field].reverse()

        reordered = self._mutated_graph("theory/records/stack-spec.json", reverse)
        self.assertTrue(reordered.ok, reordered.diagnostics)
        changed = self._project(reordered).view
        self.assertEqual(
            [(item.kind, item.declaration_id) for item in canonical.declarations],
            [(item.kind, item.declaration_id) for item in changed.declarations],
        )

    def test_proof_qualifications_and_axes_remain_visible(self) -> None:
        proof = self._declaration(
            self._project(graph.inspect_stack_graph(MANIFEST)).view,
            "law",
            "pop-empty",
        ).claims[0].evidence[0]
        self.assertEqual("proof", proof.mechanism)
        self.assertEqual("supports", proof.result)
        self.assertEqual("accepted", proof.review_state)
        self.assertTrue(proof.assumptions)
        self.assertTrue(proof.exclusions)
        self.assertIn("does not establish conformance", " ".join(proof.exclusions))

    def test_challenge_is_a_contradiction_not_a_claim_lifecycle_rewrite(self) -> None:
        observation = self._mutated_graph(
            "theory/records/stack-pop-empty-model-proof-evidence.json",
            lambda document: document.update(result="challenges"),
        )
        self.assertTrue(observation.ok, observation.diagnostics)
        view = self._project(observation).view
        law = self._declaration(view, "law", "pop-empty")
        self.assertEqual("contested-observation", law.observation)
        self.assertEqual("active", law.claims[0].state)
        self.assertEqual((PROOF_EVIDENCE,), view.contradictions)

    def test_inconclusive_evidence_remains_visible_and_unknown(self) -> None:
        observation = self._mutated_graph(
            "theory/records/stack-pop-empty-model-proof-evidence.json",
            lambda document: document.update(result="inconclusive"),
        )
        self.assertTrue(observation.ok, observation.diagnostics)
        view = self._project(observation).view
        law = self._declaration(view, "law", "pop-empty")
        self.assertEqual("undetermined", law.observation)
        self.assertEqual("inconclusive", law.claims[0].evidence[0].result)
        self.assertIn(("law", "pop-empty"), view.unknowns)

    def test_missing_exact_import_fails_before_projection(self) -> None:
        observation = self._mutated_graph(
            "compositions/theory/records/undo-history-spec.json",
            lambda document: document["imports"][0].update(id="absent-stack"),
        )
        self.assertFalse(observation.ok)
        result = self._project(observation, UNDO)
        self.assertFalse(result.ok)
        self.assertIsNone(result.view)
        self.assertIn(
            ("LINK_DANGLING_REFERENCE", "#/imports/0"),
            {(item.code, item.pointer) for item in result.diagnostics},
        )

    def test_exact_selector_and_successful_graph_are_required(self) -> None:
        missing = self._project(
            graph.inspect_stack_graph(MANIFEST),
            ("specification", "absent", "0.1.0"),
        )
        self.assertFalse(missing.ok)
        self.assertEqual("PROJECTION_SELECTOR_NOT_FOUND", missing.diagnostics[0].code)
        self.assertIsNone(missing.view)

    def test_projection_uses_no_filesystem_process_or_policy_resolution(self) -> None:
        canonical = graph.inspect_stack_graph(MANIFEST)
        touched = []

        def reject(name):
            def fail(*_args, **_kwargs):
                touched.append(name)
                raise AssertionError(f"projection attempted {name}")

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
            result = self._project(canonical)
        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual([], touched)
        self.assertFalse(hasattr(result.view, "semantic_status"))


if __name__ == "__main__":
    unittest.main()
