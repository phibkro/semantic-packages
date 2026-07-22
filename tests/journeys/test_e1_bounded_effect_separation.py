"""Refute-first contract for design-spec 0003's bounded effect observation."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from semantic_packages.ordered_map_runner import run_ordered_map_conformance
from semantic_packages.stack_runner import (
    _classify_event as classify_stack_event,
    default_stack_conformance_plan,
    run_stack_conformance,
)


ROOT = Path(__file__).resolve().parents[2]
DESIGN_SPEC = ROOT / "design-specs/0003-bounded-effect-separation-observation.md"
EXEC_PLAN = ROOT / "docs/exec-plans/active/0008-bounded-effect-separation.md"
SCRIPT = ROOT / "scripts/effect_separation_probe.py"
STACK_FIXTURE = ROOT / "fixtures/adapters/v1/fake_stack_adapter.py"
ORDERED_MAP_FIXTURE = (
    ROOT / "fixtures/adapters/ordered-map-v1/fake_ordered_map_adapter.py"
)
EFFECT_READY = (
    importlib.util.find_spec("semantic_packages.effect_separation") is not None
    and SCRIPT.is_file()
)
ROLES = ("quiet", "optional", "forbidden", "unspecified", "adapter-error")
STACK_MODES = (
    "reference",
    "optional-event",
    "forbidden-event",
    "unspecified-event",
    "status-error",
)
ORDERED_MAP_MODES = (
    "reference",
    "optional-event",
    "forbidden-event",
    "unspecified-event",
    "adapter-error-forbidden",
)


def _run_probe(output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _run_stack(mode: str):
    return run_stack_conformance(
        (sys.executable, str(STACK_FIXTURE), mode),
        plan=default_stack_conformance_plan(),
    )


def _run_ordered_map(mode: str):
    return run_ordered_map_conformance(
        (sys.executable, str(ORDERED_MAP_FIXTURE), mode)
    )


def _tree_snapshot(root: Path) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        (path.relative_to(root).as_posix(), path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


class BoundedEffectRedBaselineTest(unittest.TestCase):
    def test_contract_plan_and_exact_substrate_are_present(self) -> None:
        self.assertTrue(DESIGN_SPEC.is_file())
        self.assertTrue(EXEC_PLAN.is_file())
        self.assertTrue(STACK_FIXTURE.is_file())
        self.assertTrue(ORDERED_MAP_FIXTURE.is_file())
        self.assertEqual(
            "e055eab406683a01a32e8b563ef2e299169ddb2745685b5ad3ffae3297d93f6c",
            default_stack_conformance_plan().sha256,
        )
        self.assertEqual("unspecified", classify_stack_event("io"))
        self.assertEqual("unspecified", classify_stack_event("io."))
        self.assertEqual("forbidden", classify_stack_event("io.read"))
        self.assertEqual("forbidden", classify_stack_event("io.read.deep"))

    def test_exact_runner_census_freezes_error_asymmetry_and_concern_locality(self) -> None:
        stack = tuple(_run_stack(mode) for mode in STACK_MODES)
        ordered_map = tuple(_run_ordered_map(mode) for mode in ORDERED_MAP_MODES)

        self.assertEqual(
            ("supports", "supports", "challenges", "supports", "error"),
            tuple(report.result for report in stack),
        )
        self.assertEqual(
            ("supports", "supports", "challenges", "supports", "error"),
            tuple(report.result for report in ordered_map),
        )
        self.assertEqual((177, 177, 177), tuple(len(stack[index].events) for index in (1, 2, 3)))
        self.assertTrue(all(event == ("debug.emit", "optional") for event in stack[1].events))
        self.assertTrue(all(event == ("io.read", "forbidden") for event in stack[2].events))
        self.assertTrue(all(event == ("custom.audit", "unspecified") for event in stack[3].events))
        self.assertEqual((), stack[4].events)
        self.assertEqual((30, 30, 30), tuple(len(ordered_map[index].events) for index in (1, 2, 3)))
        self.assertEqual(
            ("io.read", "forbidden"),
            (ordered_map[4].events[0].event, ordered_map[4].events[0].disposition),
        )
        self.assertEqual(1, len(ordered_map[4].events))

        self.assertEqual(
            {"stack-effects"},
            {
                item.declaration_id
                for item in stack[2].declaration_outcomes
                if item.result == "challenges"
            },
        )
        self.assertEqual(
            {"ordered-map-effects"},
            {
                item.declaration_id
                for item in ordered_map[2].declarations
                if item.result == "challenges"
            },
        )
        self.assertFalse(
            any(item.result == "challenges" for item in stack[4].declaration_outcomes)
        )
        self.assertFalse(
            any(item.result == "challenges" for item in ordered_map[4].declarations)
        )

    def test_red_predecessor_names_only_the_absent_probe(self) -> None:
        if EFFECT_READY:
            self.skipTest("bounded effect-separation probe is implemented")
        with tempfile.TemporaryDirectory(prefix="semantic-effect-red-") as raw:
            result = _run_probe(Path(raw) / "report.json")
        self.assertEqual(2, result.returncode)
        self.assertIn("can't open file", result.stderr)
        self.fail("E1 bounded effect-separation probe is absent; successor remains red")


@unittest.skipUnless(EFFECT_READY, "bounded effect-separation probe not implemented")
class BoundedEffectJourneyTest(unittest.TestCase):
    maxDiff = None

    def _exact_reports(self):
        return (
            tuple(_run_stack(mode) for mode in STACK_MODES),
            tuple(_run_ordered_map(mode) for mode in ORDERED_MAP_MODES),
        )

    def _build_with_reports(self, stack, ordered_map):
        from semantic_packages import effect_separation

        with (
            mock.patch.object(effect_separation, "run_stack_conformance", side_effect=stack),
            mock.patch.object(
                effect_separation,
                "run_ordered_map_conformance",
                side_effect=ordered_map,
            ),
        ):
            return effect_separation.build_observation(ROOT)

    def _assert_rejected(self, stack, ordered_map, expected: str) -> None:
        from semantic_packages import effect_separation

        with (
            tempfile.TemporaryDirectory(prefix="semantic-effect-failure-") as raw,
            mock.patch.object(effect_separation, "run_stack_conformance", side_effect=stack),
            mock.patch.object(
                effect_separation,
                "run_ordered_map_conformance",
                side_effect=ordered_map,
            ),
        ):
            output = Path(raw) / "report.json"
            sentinel = b"operator-owned prior observation\n"
            output.write_bytes(sentinel)
            stderr = []
            result = effect_separation.run(output, root=ROOT, diagnostics=stderr.append)
            self.assertEqual(1, result)
            self.assertEqual(sentinel, output.read_bytes())
            self.assertTrue(stderr)
            self.assertTrue(all(": " in line for line in stderr), stderr)
            self.assertIn(expected, "\n".join(stderr))

    def test_felt_command_writes_exact_bounded_report_without_mutating_inputs(self) -> None:
        governed = tuple(
            _tree_snapshot(ROOT / relative)
            for relative in ("fixtures", "contracts", "specs", "registry", "reports")
        )
        with tempfile.TemporaryDirectory(prefix="semantic-effect-success-") as raw:
            output = Path(raw) / "effect-separation.json"
            result = _run_probe(output)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("", result.stderr)
            self.assertEqual(
                "observed bounded effect separation: 2 domains, 10 observations, "
                f"0 semantic drifts, 2 effect challenges, 2 execution errors -> {output}\n",
                result.stdout,
            )
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(
            (
                "kind",
                "boundary",
                "domains",
                "summary",
                "assumptions",
                "exclusions",
                "conclusion",
            ),
            tuple(report),
        )
        self.assertEqual("effect-separation-observation-v1", report["kind"])
        self.assertEqual("adapter-reported-invocation-events", report["boundary"])
        self.assertEqual("bounded-separation-observed", report["conclusion"])
        self.assertEqual(
            {
                "domains": 2,
                "observations": 10,
                "semanticDrifts": 0,
                "effectChallenges": 2,
                "executionErrors": 2,
            },
            report["summary"],
        )
        self.assertIn("adapter-event-completeness", report["assumptions"])
        self.assertIn("adapter-external-effects", report["exclusions"])
        self.assertEqual(governed, tuple(
            _tree_snapshot(ROOT / relative)
            for relative in ("fixtures", "contracts", "specs", "registry", "reports")
        ))

    def test_domains_retain_exact_modes_ledgers_and_projection_relations(self) -> None:
        stack, ordered_map = self._exact_reports()
        report = self._build_with_reports(stack, ordered_map)
        self.assertEqual(("stack", "ordered-map"), tuple(item["domain"] for item in report["domains"]))

        for domain, modes, effect_id in (
            (report["domains"][0], STACK_MODES, "stack-effects"),
            (report["domains"][1], ORDERED_MAP_MODES, "ordered-map-effects"),
        ):
            observations = domain["observations"]
            self.assertEqual(ROLES, tuple(item["role"] for item in observations))
            self.assertEqual(modes, tuple(item["adapterMode"] for item in observations))
            self.assertEqual(effect_id, domain["effectDeclaration"])
            self.assertEqual(
                ("baseline", "equal", "equal", "equal", "not-compared"),
                tuple(item["projectionComparison"] for item in observations),
            )
            baseline = observations[0]["semanticProjection"]
            self.assertTrue(all(item["semanticProjection"] == baseline for item in observations[1:4]))
            self.assertNotEqual(baseline, observations[4]["semanticProjection"])
            self.assertEqual("non-authoritative", observations[4]["effectAuthority"])

        stack_observations = report["domains"][0]["observations"]
        ordered_observations = report["domains"][1]["observations"]
        self.assertEqual([], stack_observations[0]["eventLedger"])
        self.assertEqual([], stack_observations[4]["eventLedger"])
        self.assertEqual(177, len(stack_observations[1]["eventLedger"]))
        self.assertEqual(30, len(ordered_observations[1]["eventLedger"]))
        self.assertEqual(
            [{"seq": 0, "caseId": "lookup-empty", "operation": "empty", "event": "io.read", "disposition": "forbidden"}],
            ordered_observations[4]["eventLedger"],
        )

    def test_semantic_drift_and_forbidden_concern_spillover_fail_closed(self) -> None:
        stack, ordered_map = self._exact_reports()
        changed_outcomes = list(stack[1].declaration_outcomes)
        changed_outcomes[0] = replace(changed_outcomes[0], result="challenges", causes=("TEST_DRIFT",))
        drifted_stack = list(stack)
        drifted_stack[1] = replace(stack[1], declaration_outcomes=tuple(changed_outcomes))
        self._assert_rejected(tuple(drifted_stack), ordered_map, "semantic projection drift")

        spill_outcomes = list(stack[2].declaration_outcomes)
        spill_outcomes[0] = replace(spill_outcomes[0], result="challenges", causes=("TEST_SPILL",))
        spilled_stack = list(stack)
        spilled_stack[2] = replace(stack[2], declaration_outcomes=tuple(spill_outcomes))
        self._assert_rejected(tuple(spilled_stack), ordered_map, "concern spillover")

    def test_event_classification_and_error_asymmetry_fail_closed(self) -> None:
        stack, ordered_map = self._exact_reports()
        wrong_optional = list(stack)
        wrong_optional[1] = replace(
            stack[1],
            events=tuple((name, "unspecified") for name, _ in stack[1].events),
        )
        self._assert_rejected(tuple(wrong_optional), ordered_map, "event ledger")

        lost_error_event = list(ordered_map)
        lost_error_event[4] = replace(ordered_map[4], events=())
        self._assert_rejected(stack, tuple(lost_error_event), "adapter-error event ledger")

        reclassified_error = list(stack)
        reclassified_error[4] = replace(stack[4], result="supports", causes=())
        self._assert_rejected(tuple(reclassified_error), ordered_map, "adapter-error result")

    def test_exact_execution_authority_and_domain_ownership_are_visible(self) -> None:
        stack, ordered_map = self._exact_reports()
        report = self._build_with_reports(stack, ordered_map)
        stack_domain, ordered_domain = report["domains"]
        self.assertEqual("fixtures/adapters/v1/fake_stack_adapter.py", stack_domain["fixture"])
        self.assertEqual(
            "fixtures/adapters/ordered-map-v1/fake_ordered_map_adapter.py",
            ordered_domain["fixture"],
        )
        self.assertEqual(default_stack_conformance_plan().sha256, stack_domain["planSha256"])
        self.assertEqual(
            "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a",
            ordered_domain["planSha256"],
        )
        self.assertIn("observations", stack_domain["observations"][0]["semanticProjection"])
        self.assertNotIn("cases", stack_domain["observations"][0]["semanticProjection"])
        self.assertIn("cases", ordered_domain["observations"][0]["semanticProjection"])
        self.assertNotIn("observations", ordered_domain["observations"][0]["semanticProjection"])

    def test_output_alias_required_argument_and_determinism_controls(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-effect-alias-") as raw:
            alias = Path(raw) / "fixture-alias.py"
            os.link(STACK_FIXTURE, alias)
            before = STACK_FIXTURE.read_bytes()
            result = _run_probe(alias)
            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertIn("OUTPUT_INPUT_ALIAS", result.stderr)
            self.assertEqual(before, STACK_FIXTURE.read_bytes())

            missing = subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(2, missing.returncode)

            first = Path(raw) / "first.json"
            second = Path(raw) / "second.json"
            self.assertEqual(0, _run_probe(first).returncode)
            self.assertEqual(0, _run_probe(second).returncode)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_report_language_preserves_bounded_nonauthority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-effect-language-") as raw:
            output = Path(raw) / "report.json"
            self.assertEqual(0, _run_probe(output).returncode)
            text = output.read_text(encoding="utf-8").lower()
        for forbidden_claim in (
            "whole-process purity",
            "contextual noninterference",
            "semantic equivalence",
            "accepted evidence",
            "arbitrary-domain generality",
        ):
            self.assertNotIn(forbidden_claim, text)


if __name__ == "__main__":
    unittest.main()
