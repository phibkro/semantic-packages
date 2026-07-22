from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from semantic_packages import graph


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs" / "operations" / "cold-human-inspection.md"
README = ROOT / "README.md"
REGISTRY = ROOT / "registry" / "stack"
PREDECESSOR = REGISTRY / "manifest.json"
SUCCESSOR = REGISTRY / "successor-manifest.json"
PROFILE = ("realizationProfile", "stack-default", "0.1.0")
OLD_SPEC = ("specification", "stack", "0.1.0")
NEW_SPEC = ("specification", "stack", "0.2.0")
OLD_POLICY = ("consumerPolicy", "stack-bounded-policy", "0.1.0")
NEW_POLICY = ("consumerPolicy", "stack-bounded-policy", "0.2.0")
OPTIONS = (
    ("--predecessor-manifest", "registry/stack/manifest.json"),
    ("--successor-manifest", "registry/stack/successor-manifest.json"),
    ("--profile", "realizationProfile/stack-default/0.1.0"),
    ("--predecessor-specification", "specification/stack/0.1.0"),
    ("--successor-specification", "specification/stack/0.2.0"),
    ("--predecessor-policy", "consumerPolicy/stack-bounded-policy/0.1.0"),
    ("--successor-policy", "consumerPolicy/stack-bounded-policy/0.2.0"),
)
README_COMMAND = " \\\n  ".join(
    ("python3 -m semantic_packages.inspection",)
    + tuple(f"{option} {value}" for option, value in OPTIONS)
)
COMMAND = (
    sys.executable,
    "-m",
    "semantic_packages.inspection",
    *(part for pair in OPTIONS for part in pair),
)

try:
    inspection = importlib.import_module("semantic_packages.inspection")
    INSPECTION_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.inspection":
        raise
    inspection = None
    INSPECTION_IMPORT_ERROR = error


class ColdHumanProtocolPreconditionTest(unittest.TestCase):
    def test_protocol_freezes_participant_observation_before_surface(self) -> None:
        text = PROTOCOL.read_text(encoding="utf-8")
        for required in (
            "eligible participant",
            "five questions",
            "30 minutes",
            "source/test/record archaeology",
            "participant reviews the retained text",
            "A preflight PASS does not substitute for H2",
        ):
            self.assertIn(required, text)

    def test_inspection_module_is_the_intentional_red_predecessor(self) -> None:
        self.assertIsNotNone(
            inspection,
            "H1 proves the documented inspection surface is absent before H-S1; "
            f"observed {INSPECTION_IMPORT_ERROR!r}",
        )


@unittest.skipIf(
    inspection is None,
    "H1 freezes the human-facing contract before H-S1 implements it",
)
class ColdHumanInspectionContractTest(unittest.TestCase):
    maxDiff = None

    def _run(self, command: tuple[str, ...] = COMMAND) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )

    def test_readme_contains_one_exact_copyable_command(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn(f"```sh\n{README_COMMAND}\n```", text)
        self.assertEqual(1, text.count("python3 -m semantic_packages.inspection"))

    def test_theory_output_exposes_substantive_meaning_and_qualified_evidence(self) -> None:
        result = self._run()
        self.assertEqual(0, result.returncode, result.stderr)
        output = result.stdout
        for required in (
            "Exact inputs (no discovery, latest selection, or artifact execution)",
            "predecessor graph records: 24",
            "successor graph records: 31",
            "Theory meaning: specification/stack/0.1.0",
            'carrier Stack: observation=unclaimed content={"description":"An abstract finite last-in-first-out collection.","id":"Stack"}',
            'operation empty: observation=unclaimed content={"id":"empty","signature":"Stack[A]"}',
            'operation push: observation=unclaimed content={"id":"push","signature":"Stack[A] * A -> Stack[A]"}',
            'observation pop: observation=unclaimed content={"id":"pop","signature":"Stack[A] -> Option[A * Stack[A]]"}',
            'derivedObservation elements: observation=unclaimed content={"definition":"Repeatedly pop a reachable finite stack until None, yielding a top-first sequence.","id":"elements"}',
            'law pop-empty: observation=supported-observation content={"id":"pop-empty","statement":"pop(empty) == None"}',
            'law pop-push: observation=unclaimed content={"id":"pop-push","statement":"pop(push(s, x)) == Some((x, s)) under Stack observational equivalence"}',
            'effect stack-effects: observation=unclaimed content={"default":"unspecified","forbidden":["io.*"],"id":"stack-effects","optional":["debug.emit"]}',
            'resource persistence: observation=unclaimed content={"id":"persistence","rule":"Retained stack handles remain usable and observationally unchanged after operations on them or derived handles."}',
            'performance push-amortized-constant: observation=unclaimed content={"costMeasure":{"localId":"realization-steps","profile":{"id":"stack-default","kind":"realizationProfile","version":"0.1.0"}},"id":"push-amortized-constant","operationFamily":["push"],"permittedEvidenceMethods":["proof","proof-audit"],"predicate":"There exist constants a,b >= 0 such that total realization-steps for n pushes is at most a*n+b for every n >= 0.","workload":{"localId":"push-sequence","profile":{"id":"stack-default","kind":"realizationProfile","version":"0.1.0"}}}',
            'equivalence stack-equivalence: observation=unclaimed content={"carrier":"Stack","definition":"Pointwise equality of top-first elements sequences under the declared element equivalence.","id":"stack-equivalence"}',
            "claim claim/stack-pop-empty-law/0.1.0 concern=law.conformance state=active",
            "Evidence evidence/stack-pop-empty-model-proof/0.1.0 mechanism=proof result=supports review=accepted",
            "assumption: Classical equality for Option values.",
            "exclusion: No realization behavior is asserted by this claim.",
            "Evidence assumption: The hand-reviewed translation from the Stack law to the Lean observation model is faithful.",
            "Evidence exclusion: This Evidence does not establish conformance of any Realization or adapter.",
            "unknown/unclaimed: carrier/Stack",
            "performance/push-amortized-constant",
            "contradictions: none",
        ):
            self.assertIn(required, output)

    def test_resolution_output_preserves_every_axis_and_candidate_boundary(self) -> None:
        output = self._run().stdout
        for realization, evidence in (
            (
                "realization/stack-rust/0.1.0",
                "evidence/stack-rust-pop-empty-conformance/0.1.0",
            ),
            (
                "realization/stack-typescript/0.1.0",
                "evidence/stack-typescript-pop-empty-conformance/0.1.0",
            ),
        ):
            start = output.index(f"{realization}: semantic=acceptable")
            end = output.find("\nrealization/", start + 1)
            block = output[start:] if end == -1 else output[start:end]
            for required in (
                "law.conformance: status=satisfied priority=required blocks=no",
                "resource.persistence: status=satisfied priority=required blocks=no",
                "effect.conformance: status=satisfied priority=required blocks=no",
                "performance: status=unsupported priority=optional blocks=no",
                f"supporting Evidence: {evidence} mechanism=bounded-conformance-campaign result=supports review=accepted disposition=selected-applicable",
                "challenging Evidence: none",
                "inconclusive Evidence: none",
                "error Evidence: none",
                "inapplicable Evidence: none",
                "unselected Evidence: none",
                "assumption: The adapter faithfully exposes the named Realization.",
                "exclusion: No behavior outside the bounded campaign is asserted.",
                "boundary: direction=consumer-to-realization mechanism=child-process-ndjson direct=no",
            ):
                self.assertIn(required, block)

    def test_successor_failure_and_exact_recovery_are_explained(self) -> None:
        output = self._run().stdout
        start = output.index("Failed successor")
        block = output[start:]
        for required in (
            "realization/stack-rust/0.2.0: semantic=unacceptable",
            "law.conformance: status=unsupported priority=required blocks=yes",
            "missing declarations: pop-empty, pop-push",
            "resource.persistence: status=unsupported priority=required blocks=yes",
            "missing declarations: persistence",
            "effect.conformance: status=unsupported priority=required blocks=yes",
            "missing declarations: stack-effects",
            "reasons: absent-evidence",
            "supporting Evidence: none",
            "stale Evidence: 9 (reason=exact-specification-version)",
            "evidence/stack-pop-empty-model-proof/0.1.0",
            "recovery candidates (not automatically selected):",
            "realization/stack-rust/0.1.0",
            "realization/stack-typescript/0.1.0",
        ):
            self.assertIn(required, block)

    def test_output_is_deterministic_and_every_input_is_required(self) -> None:
        first = self._run()
        second = self._run()
        self.assertEqual(first.stdout, second.stdout)
        self.assertNotIn("latest", first.stdout.lower().replace("no discovery, latest", ""))

        for option, value in OPTIONS:
            with self.subTest(option=option):
                attacked = list(COMMAND)
                position = attacked.index(option)
                del attacked[position : position + 2]
                missing = self._run(tuple(attacked))
                self.assertEqual(2, missing.returncode)
                self.assertIn(option, missing.stderr)
                self.assertNotIn(value, missing.stdout)

    def test_malformed_and_valid_but_wrong_addresses_fail_closed(self) -> None:
        malformed = list(COMMAND)
        malformed[malformed.index("realizationProfile/stack-default/0.1.0")] = "stack-default"
        result = self._run(tuple(malformed))
        self.assertEqual(2, result.returncode)
        self.assertIn("exact address KIND/ID/VERSION", result.stderr)

        wrong = list(COMMAND)
        wrong[wrong.index("specification/stack/0.2.0")] = "specification/stack/9.9.9"
        result = self._run(tuple(wrong))
        self.assertEqual(1, result.returncode)
        self.assertIn("RESOLUTION_SELECTOR_NOT_FOUND", result.stderr)
        self.assertNotIn("Failed successor", result.stdout)

    def test_changed_graph_is_rejected_instead_of_printing_canonical_answers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h1-attacked-") as raw:
            attacked_registry = Path(raw) / "stack"
            shutil.copytree(REGISTRY, attacked_registry)
            manifest_path = attacked_registry / "successor-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["members"][0]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            attacked = list(COMMAND)
            attacked[attacked.index("registry/stack/successor-manifest.json")] = str(manifest_path)
            result = self._run(tuple(attacked))
        self.assertEqual(1, result.returncode)
        self.assertIn("GRAPH_DIGEST_MISMATCH", result.stderr)
        self.assertNotIn("realization/stack-rust/0.1.0: semantic=acceptable", result.stdout)

    def test_renderer_performs_no_io_or_artifact_execution_after_graph_capture(self) -> None:
        predecessor = graph.inspect_stack_graph(PREDECESSOR)
        successor = graph.inspect_stack_graph(SUCCESSOR)
        touched: list[str] = []

        def reject(name: str):
            def fail(*_args, **_kwargs):
                touched.append(name)
                raise AssertionError(f"inspection renderer attempted {name}")

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
            output = inspection.render_stack_inspection(
                predecessor,
                successor,
                profile=PROFILE,
                predecessor_specification=OLD_SPEC,
                successor_specification=NEW_SPEC,
                predecessor_policy=OLD_POLICY,
                successor_policy=NEW_POLICY,
            )
            with self.assertRaises(inspection.InspectionError) as caught:
                inspection.render_stack_inspection(
                    predecessor,
                    predecessor,
                    profile=PROFILE,
                    predecessor_specification=OLD_SPEC,
                    successor_specification=NEW_SPEC,
                    predecessor_policy=OLD_POLICY,
                    successor_policy=NEW_POLICY,
                )
        self.assertIn("Theory meaning: specification/stack/0.1.0", output)
        self.assertIn("RESOLUTION_SELECTOR_NOT_FOUND", str(caught.exception))
        self.assertEqual([], touched)


if __name__ == "__main__":
    unittest.main()
