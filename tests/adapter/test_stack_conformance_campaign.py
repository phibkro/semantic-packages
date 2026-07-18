"""Red-first contract for the Wave 4 shared Stack campaign boundary.

These tests freeze harness-owned campaign data and report classification only.  They
do not run a child, reproduce the Stack oracle, or inspect any realization.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any

from semantic_packages.stack_runner import (
    CaseObservation,
    default_stack_conformance_plan,
    run_stack_conformance,
    summarize_stack_conformance,
    validate_stack_conformance_plan,
)


DECLARATIONS = ("pop-empty", "pop-push", "persistence", "stack-effects")
ROOT = Path(__file__).resolve().parents[2]
FAKE_ADAPTER = ROOT / "fixtures" / "adapters" / "v1" / "fake_stack_adapter.py"


class StackConformanceCampaignContractTests(unittest.TestCase):
    def run_mode(self, mode: str):
        return run_stack_conformance(
            (sys.executable, str(FAKE_ADAPTER), mode),
            plan=default_stack_conformance_plan(),
        )

    def test_default_plan_pins_profile_sized_inputs_and_controls(self) -> None:
        plan = default_stack_conformance_plan()

        self.assertEqual(
            ("specification", "stack", "0.1.0"), plan.specification.reference
        )
        self.assertEqual(
            "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1",
            plan.specification.sha256,
        )
        self.assertEqual(
            ("realizationProfile", "stack-default", "0.1.0"),
            plan.profile.reference,
        )
        self.assertEqual(
            "2a51ed7d2e1266376cd4a58ef3f20d30244655d25cb884816576be989014eddb",
            plan.profile.sha256,
        )
        self.assertEqual(tuple(range(-2, 3)), plan.element_domain)
        self.assertEqual((8, 32, 9), (
            plan.max_depth,
            plan.max_history,
            plan.observation_limit,
        ))
        self.assertEqual(
            ("stack-conformance-campaign", "1", 20260718),
            (plan.algorithm, plan.algorithm_version, plan.seed),
        )
        self.assertEqual(0.20, plan.timeout_seconds)
        self.assertEqual(("io.*",), plan.event_contract.forbidden)
        self.assertEqual(("debug.emit",), plan.event_contract.optional)
        self.assertEqual("unspecified", plan.event_contract.default)

    def test_cases_reach_depth_eight_and_include_a_mixed_length_32_history(self) -> None:
        plan = default_stack_conformance_plan()

        observed_depths = [
            len(observation.top_first)
            for case in plan.cases
            for observation in case.observations
        ]
        self.assertIn(8, observed_depths)

        mixed_histories = [
            case
            for case in plan.cases
            if len(case.steps) == 32
            and {step.op for step in case.steps}.issuperset({"push", "pop"})
        ]
        self.assertTrue(mixed_histories)
        self.assertEqual({"curated", "generated"}, {case.origin for case in plan.cases})

    def test_cases_expose_only_logical_bindings(self) -> None:
        plan = default_stack_conformance_plan()
        payload = json.loads(plan.canonical_json())

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                self.assertNotIn("handle", value)
                self.assertNotIn("representation", value)
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(payload)
        for case in plan.cases:
            for step in case.steps:
                for binding in (step.source, step.bind):
                    if binding is not None:
                        self.assertRegex(binding, r"^[a-z][a-z0-9_]*$")

    def test_default_plan_is_canonical_and_reproducible(self) -> None:
        first = default_stack_conformance_plan()
        second = default_stack_conformance_plan()

        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertRegex(first.sha256, r"^[0-9a-f]{64}$")
        self.assertEqual(first.sha256, second.sha256)
        first_ids = tuple(case.case_id for case in first.cases)
        self.assertEqual(first_ids, tuple(case.case_id for case in second.cases))
        self.assertEqual(len(first_ids), len(set(first_ids)))

    def test_plan_validation_rejects_unsafe_bounds_and_unknown_bindings(self) -> None:
        plan = default_stack_conformance_plan()
        with self.assertRaisesRegex(ValueError, "observation"):
            validate_stack_conformance_plan(replace(plan, observation_limit=8))

        case = next(case for case in plan.cases if any(s.source for s in case.steps))
        step_index = next(i for i, step in enumerate(case.steps) if step.source)
        bad_steps = list(case.steps)
        bad_steps[step_index] = replace(bad_steps[step_index], source="never_bound")
        bad_case = replace(case, steps=tuple(bad_steps))
        with self.assertRaisesRegex(ValueError, "binding"):
            validate_stack_conformance_plan(replace(plan, cases=(bad_case,)))

        case = next(
            case for case in plan.cases if sum(s.bind is not None for s in case.steps) > 1
        )
        first_binding = next(step.bind for step in case.steps if step.bind is not None)
        duplicate_index = next(
            index
            for index, step in enumerate(case.steps)
            if step.bind is not None and step.bind != first_binding
        )
        duplicate_steps = list(case.steps)
        duplicate_steps[duplicate_index] = replace(
            duplicate_steps[duplicate_index], bind=first_binding
        )
        with self.assertRaisesRegex(ValueError, "binding"):
            validate_stack_conformance_plan(
                replace(plan, cases=(replace(case, steps=tuple(duplicate_steps)),))
            )

    def test_report_retains_granular_semantics_while_execution_stays_distinct(self) -> None:
        supports = tuple(
            CaseObservation(
                case_id=f"case-{declaration}",
                declaration_id=declaration,
                result="supports",
                expected_top_first=(),
                observed_top_first=(),
            )
            for declaration in DECLARATIONS
        )
        forbidden = summarize_stack_conformance(
            supports,
            events=(("io.read", "forbidden"),),
        )
        outcomes = {item.declaration_id: item for item in forbidden.declaration_outcomes}
        self.assertEqual(set(DECLARATIONS), set(outcomes))
        self.assertEqual("challenges", forbidden.result)
        self.assertEqual("challenges", outcomes["stack-effects"].result)
        self.assertIn("FORBIDDEN_EVENT", outcomes["stack-effects"].causes)
        for declaration in DECLARATIONS[:-1]:
            self.assertEqual("supports", outcomes[declaration].result)
            self.assertNotIn("FORBIDDEN_EVENT", outcomes[declaration].causes)

        semantic_observation = CaseObservation(
            case_id="pop-push-value",
            declaration_id="pop-push",
            result="challenges",
            causes=("POP_PUSH_VALUE",),
            expected_top_first=(2, 1),
            observed_top_first=(-2, 1),
        )
        errored = summarize_stack_conformance(
            (semantic_observation,),
            execution_causes=("TIMEOUT",),
        )
        self.assertEqual("error", errored.result)
        self.assertIn("TIMEOUT", errored.causes)
        self.assertEqual((semantic_observation,), errored.observations)
        pop_push = {
            item.declaration_id: item for item in errored.declaration_outcomes
        }["pop-push"]
        self.assertEqual("challenges", pop_push.result)
        self.assertIn("POP_PUSH_VALUE", pop_push.causes)

        plan = default_stack_conformance_plan()
        actual = run_stack_conformance(
            (sys.executable, str(FAKE_ADAPTER), "reference"),
            plan=plan,
        )
        self.assertEqual("supports", actual.result, actual)
        self.assertEqual(
            {case.case_id for case in plan.cases},
            {observation.case_id for observation in actual.observations},
        )
        self.assertEqual(
            set(DECLARATIONS),
            {outcome.declaration_id for outcome in actual.declaration_outcomes},
        )

    def test_retained_ancestor_change_challenges_only_persistence(self) -> None:
        report = self.run_mode("retained-ancestor-change")
        outcomes = {item.declaration_id: item for item in report.declaration_outcomes}

        self.assertEqual("challenges", report.result, report)
        self.assertEqual(("RETAINED_HANDLE_CHANGED",), report.causes, report)
        self.assertEqual(
            {"persistence"},
            {
                declaration
                for declaration, outcome in outcomes.items()
                if outcome.result == "challenges"
            },
            report,
        )
        self.assertEqual("challenges", outcomes["persistence"].result, report)
        self.assertIn("RETAINED_HANDLE_CHANGED", outcomes["persistence"].causes)
        for declaration in ("pop-empty", "pop-push", "stack-effects"):
            self.assertEqual("supports", outcomes[declaration].result, report)

    def test_wrong_empty_is_declaration_local(self) -> None:
        plan = default_stack_conformance_plan()
        report = run_stack_conformance(
            (sys.executable, str(FAKE_ADAPTER), "wrong-empty"),
            plan=plan,
        )
        outcomes = {item.declaration_id: item for item in report.declaration_outcomes}

        self.assertEqual("challenges", outcomes["pop-empty"].result, report)
        self.assertIn("POP_EMPTY", outcomes["pop-empty"].causes, report)
        self.assertEqual("inconclusive", outcomes["pop-push"].result, report)
        self.assertEqual("inconclusive", outcomes["persistence"].result, report)
        self.assertEqual("supports", outcomes["stack-effects"].result, report)
        for declaration in ("pop-push", "persistence", "stack-effects"):
            self.assertNotIn("OBSERVATION_LIMIT", outcomes[declaration].causes, report)

    def test_wrong_empty_does_not_replace_plan_owned_persistence_expectations(self) -> None:
        plan = default_stack_conformance_plan()
        report = run_stack_conformance(
            (sys.executable, str(FAKE_ADAPTER), "wrong-empty"),
            plan=plan,
        )
        expected_by_case = {
            case.case_id: sorted(
                observation.top_first
                for observation in case.observations
                if observation.declaration_id == "persistence"
            )
            for case in plan.cases
            if any(
                observation.declaration_id == "persistence"
                for observation in case.observations
            )
        }
        reported_by_case = {
            case_id: sorted(
                observation.expected_top_first
                for observation in report.observations
                if observation.declaration_id == "persistence"
                and observation.case_id == case_id
            )
            for case_id in expected_by_case
        }
        self.assertEqual(expected_by_case, reported_by_case)

    def test_semantic_causes_remain_case_local(self) -> None:
        with self.subTest(mode="bottom-first"):
            bottom_first = self.run_mode("bottom-first")
            bottom_causes = {
                cause
                for observation in bottom_first.observations
                if observation.declaration_id == "pop-push"
                for cause in observation.causes
            }
            self.assertIn("OBSERVATION_ORDER", bottom_causes, bottom_first)

        with self.subTest(mode="wrong-value"):
            wrong_value = self.run_mode("wrong-value")
            wrong_value_causes = {
                cause
                for observation in wrong_value.observations
                if observation.declaration_id == "pop-push"
                for cause in observation.causes
            }
            self.assertIn("POP_PUSH_VALUE", wrong_value_causes, wrong_value)

        with self.subTest(mode="case-local-causes"):
            combined = self.run_mode("case-local-causes")
            by_case = {
                observation.case_id: observation
                for observation in combined.observations
                if observation.declaration_id == "pop-push"
                and observation.result == "challenges"
            }
            first = by_case["curated-pop-push-v1"]
            later = by_case["curated-depth-eight-repeated-v1"]
            self.assertIn("POP_PUSH_VALUE", first.causes, combined)
            self.assertNotIn("OBSERVATION_ORDER", first.causes, combined)
            self.assertIn("OBSERVATION_ORDER", later.causes, combined)
            self.assertNotIn("POP_PUSH_VALUE", later.causes, combined)

    def test_validation_binds_generation_metadata_and_canonical_inputs(self) -> None:
        plan = default_stack_conformance_plan()
        inputs = (
            (ROOT / "fixtures" / "records" / "valid" / "stack-spec.json", plan.specification),
            (
                ROOT / "fixtures" / "records" / "valid" / "stack-profile.json",
                plan.profile,
            ),
        )
        for path, record_input in inputs:
            with self.subTest(path=path.name):
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(actual, record_input.sha256)

        first_case = plan.cases[0]
        mutations = {
            "case ID type": replace(
                plan, cases=(replace(first_case, case_id=7), *plan.cases[1:])
            ),
            "seed/cases": replace(plan, seed=plan.seed + 1),
            "algorithm/cases": replace(plan, algorithm="other-algorithm"),
            "algorithm version/cases": replace(plan, algorithm_version="2"),
            "specification digest": replace(
                plan,
                specification=replace(plan.specification, sha256="0" * 64),
            ),
            "profile digest": replace(
                plan,
                profile=replace(plan.profile, sha256="0" * 64),
            ),
        }
        for mechanism, changed in mutations.items():
            with self.subTest(mechanism=mechanism):
                with self.assertRaises(ValueError):
                    validate_stack_conformance_plan(changed)

    def test_generated_length_32_history_reaches_profile_depth(self) -> None:
        generated = [
            case
            for case in default_stack_conformance_plan().cases
            if case.origin == "generated"
            and len(case.steps) == 32
            and {step.op for step in case.steps}.issuperset({"push", "pop"})
        ]
        self.assertTrue(generated)
        self.assertTrue(
            any(
                len(observation.top_first) == 8
                for case in generated
                for observation in case.observations
            )
        )

    def test_persistence_cases_plan_sources_and_retained_ancestors(self) -> None:
        plan = default_stack_conformance_plan()
        cases = {case.case_id: case for case in plan.cases}

        def expected(case_id: str) -> set[tuple[str, tuple[int, ...]]]:
            return {
                (observation.binding, observation.top_first)
                for observation in cases[case_id].observations
                if observation.declaration_id == "persistence"
            }

        controls = {
            "curated-retained-source-push-v1": {
                ("root", ()),
                ("source", (1,)),
            },
            "curated-retained-source-pop-v1": {
                ("root", ()),
                ("one", (1,)),
                ("source", (2, 1)),
            },
        }
        for case_id, planned in controls.items():
            with self.subTest(case_id=case_id):
                self.assertEqual(planned, expected(case_id))


if __name__ == "__main__":
    unittest.main()
