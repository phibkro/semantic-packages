"""Red-first contract for the tracer-scoped Stack conformance runner.

The intended initial failure is import of ``semantic_packages.stack_runner``.  These
tests deliberately do not provide a fallback runner or import any Realization's Stack
operations: expected behavior stays in this harness and the child is opaque.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from semantic_packages.stack_runner import run_stack_conformance


ROOT = Path(__file__).resolve().parents[2]
FAKE_ADAPTER = ROOT / "fixtures" / "adapters" / "v1" / "fake_stack_adapter.py"


class StackRunnerContractTests(unittest.TestCase):
    """Freeze the smallest useful Python call and result surface for W3-A1."""

    def command(self, mode: str, *arguments: str) -> tuple[str, ...]:
        return (sys.executable, str(FAKE_ADAPTER), mode, *arguments)

    def run_command(self, command: tuple[str, ...]):
        return run_stack_conformance(
            command,
            values=(-2, -1, 0, 1, 2),
            max_depth=2,
            max_history=8,
            observation_limit=8,
            timeout_seconds=0.20,
        )

    def run_mode(self, mode: str, *arguments: str):
        return self.run_command(self.command(mode, *arguments))

    def assert_result(self, mode: str, expected: str, cause: str | None = None):
        report = self.run_mode(mode)
        self.assertEqual(expected, report.result, report)
        if cause is not None:
            self.assertIn(cause, report.causes, report)
        return report

    def test_reference_behavior_and_eof_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "closed.txt"
            report = self.run_mode("eof-marker", str(marker))
            self.assertEqual("supports", report.result, report)
            self.assertEqual("stdin-closed\n", marker.read_text(encoding="utf-8"))

    def test_empty_pop_push_pop_and_depth_two_are_top_first(self) -> None:
        # The request-auditing reference child returns an adapter error if request
        # keys, args, sequence, value domain, or a live opaque handle are wrong.
        self.assert_result("reference", "supports")

    def test_actual_reference_realization_and_adapter_support_the_contract(self) -> None:
        report = self.run_command(
            (sys.executable, "-m", "semantic_packages.stack_adapter")
        )
        self.assertEqual("supports", report.result, report)

    def test_handle_spelling_and_freshness_are_not_semantic(self) -> None:
        for mode in ("fresh", "interned"):
            with self.subTest(mode=mode):
                self.assert_result(mode, "supports")

    def test_retained_source_and_ancestors_are_reobserved(self) -> None:
        controls = {
            "destructive-push": "RETAINED_HANDLE_CHANGED",
            "destructive-pop": "RETAINED_HANDLE_CHANGED",
        }
        for mode, cause in controls.items():
            with self.subTest(mode=mode):
                self.assert_result(mode, "challenges", cause)

    def test_well_formed_semantic_counterexamples_challenge(self) -> None:
        controls = {
            "wrong-empty": "POP_EMPTY",
            "wrong-value": "POP_PUSH_VALUE",
            "wrong-remainder": "POP_PUSH_REMAINDER",
            "bottom-first": "OBSERVATION_ORDER",
            "shallow-liar": "OBSERVATION_ORDER",
            "nonterminating-observation": "OBSERVATION_LIMIT",
        }
        for mode, cause in controls.items():
            with self.subTest(mode=mode):
                self.assert_result(mode, "challenges", cause)

    def test_reported_events_are_retained_and_classified(self) -> None:
        optional = self.assert_result("optional-event", "supports")
        self.assertIn(("debug.emit", "optional"), optional.events)

        forbidden = self.assert_result("forbidden-event", "challenges", "FORBIDDEN_EVENT")
        self.assertIn(("io.read", "forbidden"), forbidden.events)

        unspecified = self.run_mode("unspecified-event")
        self.assertIn(("custom.audit", "unspecified"), unspecified.events)
        self.assertNotEqual("error", unspecified.result)

        ordered = self.run_mode("ordered-events")
        self.assertEqual(
            (("debug.emit", "optional"), ("custom.audit", "unspecified")),
            ordered.events[:2],
        )

    def test_transport_and_adapter_failures_are_errors_not_challenges(self) -> None:
        controls = {
            "malformed-json": "RESPONSE_JSON",
            "malformed-utf8": "RESPONSE_ENCODING",
            "malformed-shape": "RESPONSE_SHAPE",
            "extra-stdout": "EXTRA_STDOUT",
            "wrong-seq": "SEQUENCE_MISMATCH",
            "early-eof": "UNEXPECTED_EOF",
            "timeout": "TIMEOUT",
            "nonzero-exit": "PROCESS_EXIT",
            "status-error": "ADAPTER_ERROR",
        }
        for mode, cause in controls.items():
            with self.subTest(mode=mode):
                self.assert_result(mode, "error", cause)

    def test_perfect_shadow_passes_but_trust_limits_remain_explicit(self) -> None:
        report = self.assert_result("perfect-shadow", "supports")
        self.assertIn("adapter-faithfulness", report.assumptions)
        self.assertIn("adapter-event-completeness", report.assumptions)
        self.assertIn("adapter-external-effects", report.exclusions)
        self.assertIn("realization-steps", report.exclusions)


if __name__ == "__main__":
    unittest.main()
