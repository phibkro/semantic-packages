"""Refute-first contract for design-spec 0003's bounded effect observation."""

from __future__ import annotations

import importlib.util
import builtins
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


def _stack_projection(report) -> dict:
    return {
        "observations": [
            {
                "caseId": item.case_id,
                "declarationId": item.declaration_id,
                "result": item.result,
                "expectedTopFirst": list(item.expected_top_first),
                "observedTopFirst": list(item.observed_top_first),
                "causes": list(item.causes),
            }
            for item in report.observations
        ],
        "declarations": [
            {
                "declarationId": item.declaration_id,
                "result": item.result,
                "causes": list(item.causes),
            }
            for item in report.declaration_outcomes
            if item.declaration_id != "stack-effects"
        ],
    }


def _ordered_map_declaration(item) -> dict:
    return {
        "declarationId": item.declaration_id,
        "observationCount": item.observation_count,
        "result": item.result,
        "causes": list(item.causes),
    }


def _ordered_map_projection(report) -> dict:
    return {
        "cases": [
            {
                "caseId": case.case_id,
                "requestCount": case.request_count,
                "declarations": [
                    _ordered_map_declaration(item)
                    for item in case.declarations
                    if item.declaration_id != "ordered-map-effects"
                ],
            }
            for case in report.cases
        ],
        "declarations": [
            _ordered_map_declaration(item)
            for item in report.declarations
            if item.declaration_id != "ordered-map-effects"
        ],
    }


def _stack_ledger(report) -> list[dict]:
    return [
        {"event": event, "disposition": disposition}
        for event, disposition in report.events
    ]


def _ordered_map_ledger(report) -> list[dict]:
    return [
        {
            "seq": item.seq,
            "caseId": item.case_id,
            "operation": item.operation,
            "event": item.event,
            "disposition": item.disposition,
        }
        for item in report.events
    ]


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

        ordered_map_boundary = _run_ordered_map("nonmatching-io-boundary")
        self.assertEqual("supports", ordered_map_boundary.result)
        self.assertEqual(
            (("io", "unspecified"), ("io.", "unspecified")),
            tuple(
                (item.event, item.disposition)
                for item in ordered_map_boundary.events[:2]
            ),
        )
        ordered_map_descendant = _run_ordered_map("long-forbidden-event")
        self.assertEqual("challenges", ordered_map_descendant.result)
        self.assertTrue(
            all(
                item.event == "io.read.deep" and item.disposition == "forbidden"
                for item in ordered_map_descendant.events
            )
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
            mock.patch.object(
                effect_separation,
                "run_stack_conformance",
                side_effect=stack,
            ) as stack_runner,
            mock.patch.object(
                effect_separation,
                "run_ordered_map_conformance",
                side_effect=ordered_map,
            ) as ordered_map_runner,
            mock.patch(
                "socket.create_connection",
                side_effect=AssertionError("network authority is forbidden"),
            ),
            mock.patch(
                "urllib.request.urlopen",
                side_effect=AssertionError("network authority is forbidden"),
            ),
            mock.patch(
                "subprocess.Popen",
                side_effect=AssertionError("only the two exact runners may execute"),
            ),
            mock.patch(
                "subprocess.run",
                side_effect=AssertionError("only the two exact runners may execute"),
            ),
            mock.patch(
                "subprocess.call",
                side_effect=AssertionError("only the two exact runners may execute"),
            ),
            mock.patch(
                "subprocess.check_call",
                side_effect=AssertionError("only the two exact runners may execute"),
            ),
            mock.patch(
                "subprocess.check_output",
                side_effect=AssertionError("only the two exact runners may execute"),
            ),
            mock.patch.object(
                os,
                "system",
                side_effect=AssertionError("only the two exact runners may execute"),
            ),
            mock.patch.object(
                os,
                "open",
                side_effect=AssertionError("evaluation may not discover registry inputs"),
            ),
            mock.patch.object(
                os,
                "popen",
                side_effect=AssertionError("only the two exact runners may execute"),
            ),
            mock.patch(
                "socket.socket",
                side_effect=AssertionError("network authority is forbidden"),
            ),
            mock.patch.object(
                builtins,
                "open",
                side_effect=AssertionError("evaluation may not discover registry inputs"),
            ),
            mock.patch.object(
                Path,
                "read_bytes",
                side_effect=AssertionError("evaluation may not discover registry inputs"),
            ),
            mock.patch.object(
                Path,
                "read_text",
                side_effect=AssertionError("evaluation may not discover registry inputs"),
            ),
            mock.patch.object(
                Path,
                "glob",
                side_effect=AssertionError("evaluation may not discover registry inputs"),
            ),
            mock.patch.object(
                Path,
                "rglob",
                side_effect=AssertionError("evaluation may not discover registry inputs"),
            ),
            mock.patch.object(
                Path,
                "iterdir",
                side_effect=AssertionError("evaluation may not discover registry inputs"),
            ),
        ):
            report = effect_separation.build_observation(ROOT)

        self.assertEqual(5, stack_runner.call_count)
        self.assertEqual(5, ordered_map_runner.call_count)
        self.assertEqual(
            [
                mock.call(
                    (sys.executable, str(STACK_FIXTURE), mode),
                    plan=default_stack_conformance_plan(),
                )
                for mode in STACK_MODES
            ],
            stack_runner.call_args_list,
        )
        self.assertEqual(
            [
                mock.call((sys.executable, str(ORDERED_MAP_FIXTURE), mode))
                for mode in ORDERED_MAP_MODES
            ],
            ordered_map_runner.call_args_list,
        )
        return report

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
        self.assertEqual(
            ["adapter-faithfulness", "adapter-event-completeness"],
            report["assumptions"],
        )
        self.assertEqual(
            ["adapter-external-effects", "realization-steps"],
            report["exclusions"],
        )
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
            self.assertEqual(
                (
                    "domain",
                    "effectDeclaration",
                    "fixture",
                    "planSha256",
                    "observations",
                ),
                tuple(domain),
            )
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
            for observation in observations:
                self.assertEqual(
                    (
                        "role",
                        "adapterMode",
                        "campaignResult",
                        "campaignCauses",
                        "effectResult",
                        "effectCauses",
                        "effectAuthority",
                        "eventLedger",
                        "semanticProjection",
                        "projectionComparison",
                    ),
                    tuple(observation),
                )

        stack_observations = report["domains"][0]["observations"]
        ordered_observations = report["domains"][1]["observations"]
        self.assertEqual(
            [_stack_ledger(item) for item in stack],
            [item["eventLedger"] for item in stack_observations],
        )
        self.assertEqual(
            [_ordered_map_ledger(item) for item in ordered_map],
            [item["eventLedger"] for item in ordered_observations],
        )
        self.assertEqual(
            [_stack_projection(item) for item in stack],
            [item["semanticProjection"] for item in stack_observations],
        )
        self.assertEqual(
            [_ordered_map_projection(item) for item in ordered_map],
            [item["semanticProjection"] for item in ordered_observations],
        )

        for observations, native, effect_id in (
            (stack_observations, stack, "stack-effects"),
            (ordered_observations, ordered_map, "ordered-map-effects"),
        ):
            for observed, source in zip(observations, native):
                declarations = (
                    source.declaration_outcomes
                    if hasattr(source, "declaration_outcomes")
                    else source.declarations
                )
                effect = next(
                    item for item in declarations if item.declaration_id == effect_id
                )
                self.assertEqual(source.result, observed["campaignResult"])
                self.assertEqual(list(source.causes), observed["campaignCauses"])
                self.assertEqual(effect.result, observed["effectResult"])
                self.assertEqual(list(effect.causes), observed["effectCauses"])

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

        invented_stack_event = list(stack)
        invented_stack_event[4] = replace(
            stack[4], events=(("io.read", "forbidden"),)
        )
        self._assert_rejected(
            tuple(invented_stack_event), ordered_map, "adapter-error event ledger"
        )

        reclassified_ordered_error = list(ordered_map)
        reclassified_ordered_error[4] = replace(
            ordered_map[4], result="supports", causes=()
        )
        self._assert_rejected(
            stack, tuple(reclassified_ordered_error), "adapter-error result"
        )

    def test_ordered_map_drift_spillover_and_permitted_challenges_fail_closed(self) -> None:
        stack, ordered_map = self._exact_reports()
        changed_declarations = list(ordered_map[1].declarations)
        changed_declarations[0] = replace(
            changed_declarations[0], result="challenges", causes=("TEST_DRIFT",)
        )
        drifted = list(ordered_map)
        drifted[1] = replace(
            ordered_map[1], declarations=tuple(changed_declarations)
        )
        self._assert_rejected(stack, tuple(drifted), "semantic projection drift")

        spill_declarations = list(ordered_map[2].declarations)
        spill_declarations[0] = replace(
            spill_declarations[0], result="challenges", causes=("TEST_SPILL",)
        )
        spilled = list(ordered_map)
        spilled[2] = replace(
            ordered_map[2], declarations=tuple(spill_declarations)
        )
        self._assert_rejected(stack, tuple(spilled), "concern spillover")

        optional_declarations = list(ordered_map[1].declarations)
        effect_index = next(
            index
            for index, item in enumerate(optional_declarations)
            if item.declaration_id == "ordered-map-effects"
        )
        optional_declarations[effect_index] = replace(
            optional_declarations[effect_index],
            result="challenges",
            causes=("TEST_OPTIONAL",),
        )
        challenged_optional = list(ordered_map)
        challenged_optional[1] = replace(
            ordered_map[1],
            result="challenges",
            causes=("TEST_OPTIONAL",),
            declarations=tuple(optional_declarations),
        )
        self._assert_rejected(
            stack, tuple(challenged_optional), "optional effect result"
        )

        nested_cases = list(ordered_map[4].cases)
        nested_declarations = list(nested_cases[0].declarations)
        nested_effect = next(
            index
            for index, item in enumerate(nested_declarations)
            if item.declaration_id == "ordered-map-effects"
        )
        nested_declarations[nested_effect] = replace(
            nested_declarations[nested_effect],
            result="challenges",
            causes=("TEST_NESTED_AUTHORITY",),
        )
        nested_cases[0] = replace(
            nested_cases[0], declarations=tuple(nested_declarations)
        )
        nested_authority = list(ordered_map)
        nested_authority[4] = replace(
            ordered_map[4], cases=tuple(nested_cases)
        )
        self._assert_rejected(
            stack, tuple(nested_authority), "effect surface changed"
        )

        forbidden_cases = list(ordered_map[2].cases)
        forbidden_declarations = list(forbidden_cases[0].declarations)
        forbidden_effect = next(
            index
            for index, item in enumerate(forbidden_declarations)
            if item.declaration_id == "ordered-map-effects"
        )
        forbidden_declarations[forbidden_effect] = replace(
            forbidden_declarations[forbidden_effect], result="supports", causes=()
        )
        forbidden_cases[0] = replace(
            forbidden_cases[0], declarations=tuple(forbidden_declarations)
        )
        hidden_forbidden = list(ordered_map)
        hidden_forbidden[2] = replace(
            ordered_map[2], cases=tuple(forbidden_cases)
        )
        self._assert_rejected(
            stack, tuple(hidden_forbidden), "effect surface changed"
        )

    def test_exact_projection_census_and_event_attribution_fail_closed(self) -> None:
        stack, ordered_map = self._exact_reports()
        stripped_stack = tuple(
            replace(
                report,
                observations=(),
                declaration_outcomes=tuple(
                    item
                    for item in report.declaration_outcomes
                    if item.declaration_id == "stack-effects"
                ),
            )
            for report in stack
        )
        self._assert_rejected(
            stripped_stack, ordered_map, "semantic projection binding changed"
        )

        moved_events = list(ordered_map[1].events)
        moved_events[0] = replace(
            moved_events[0], case_id="invented-case", operation="invented-operation"
        )
        moved_ordered_map = list(ordered_map)
        moved_ordered_map[1] = replace(
            ordered_map[1], events=tuple(moved_events)
        )
        self._assert_rejected(
            stack, tuple(moved_ordered_map), "event ledger changed exact attribution"
        )

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
            directory = Path(raw)
            governed_inputs = (
                STACK_FIXTURE,
                ORDERED_MAP_FIXTURE,
                ROOT / "contracts/ordered-map/conformance-plan.json",
                ROOT / "specs/stack.pspec",
                ROOT / "registry/stack/theory/records/stack-spec.json",
                ROOT / "reports/ordered-map/rust-campaign-report.json",
                ROOT / "docs/exec-plans/completed/0004-ordered-map-generality.md",
            )
            for index, governed in enumerate(governed_inputs):
                with self.subTest(governed=governed.relative_to(ROOT)):
                    alias = directory / f"governed-alias-{index}"
                    os.link(governed, alias)
                    before = governed.read_bytes()
                    result = _run_probe(alias)
                    self.assertEqual(1, result.returncode)
                    self.assertEqual("", result.stdout)
                    self.assertIn("OUTPUT_INPUT_ALIAS", result.stderr)
                    self.assertEqual(before, governed.read_bytes())
                    alias.unlink()

            missing = subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(2, missing.returncode)

            first = directory / "first.json"
            second = directory / "second.json"
            self.assertEqual(0, _run_probe(first).returncode)
            self.assertEqual(0, _run_probe(second).returncode)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_atomic_publication_failure_preserves_prior_output(self) -> None:
        from semantic_packages import effect_separation

        with tempfile.TemporaryDirectory(prefix="semantic-effect-atomic-") as raw:
            output = Path(raw) / "report.json"
            sentinel = b"operator-owned prior observation\n"
            output.write_bytes(sentinel)
            diagnostics = []
            with mock.patch.object(
                effect_separation.os,
                "replace",
                side_effect=OSError("injected publication interruption"),
            ):
                result = effect_separation.run(
                    output, root=ROOT, diagnostics=diagnostics.append
                )
            self.assertEqual(1, result)
            self.assertEqual(sentinel, output.read_bytes())
            self.assertTrue(any("OUTPUT_WRITE" in item for item in diagnostics))

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
