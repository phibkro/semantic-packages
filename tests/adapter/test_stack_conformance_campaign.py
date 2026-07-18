"""Red-first contract for the Wave 4 shared Stack campaign boundary.

These tests freeze harness-owned campaign data and report classification only.  They
do not run a child, reproduce the Stack oracle, or inspect any realization.
"""

from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
