"""Intentional-red O6a contract for the OrderedMap campaign runner."""

from __future__ import annotations

import builtins
import importlib
import inspect
import json
import os
import runpy
import sys
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path
from collections.abc import Mapping, Sequence
from unittest import mock

from scripts import record_check
from semantic_packages import ordered_map_contract


ROOT = Path(__file__).resolve().parents[2]
FAKE_ADAPTER = (
    ROOT / "fixtures" / "adapters" / "ordered-map-v1" / "fake_ordered_map_adapter.py"
)
PLAN_SHA256 = "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a"
DECLARATIONS = {
    "lookup-empty",
    "lookup-put-same",
    "lookup-put-other",
    "put-existing-position",
    "put-new-appends",
    "persistence",
    "ordered-map-effects",
}
DECLARATION_COUNTS = {
    "lookup-empty": 1,
    "lookup-put-same": 2,
    "lookup-put-other": 1,
    "put-existing-position": 1,
    "put-new-appends": 1,
    "persistence": 2,
    "ordered-map-effects": 30,
}
CASE_LEDGER = (
    ("lookup-empty", 2, (("lookup-empty", 1, "supports"), ("ordered-map-effects", 2, "supports"))),
    ("same-class-replacement", 5, (("lookup-put-same", 2, "supports"), ("ordered-map-effects", 5, "supports"))),
    ("other-class-preservation", 4, (("lookup-put-other", 1, "supports"), ("ordered-map-effects", 4, "supports"))),
    ("nonlast-overwrite-order", 5, (("put-existing-position", 1, "supports"), ("ordered-map-effects", 5, "supports"))),
    ("new-class-append-three", 5, (("put-new-appends", 1, "supports"), ("ordered-map-effects", 5, "supports"))),
    ("retained-new-class-source", 4, (("persistence", 1, "supports"), ("ordered-map-effects", 4, "supports"))),
    ("retained-existing-class-source", 5, (("persistence", 1, "supports"), ("ordered-map-effects", 5, "supports"))),
)


class _TrackedMapping(Mapping):
    def __init__(self, value, path: str, accesses: list[str]) -> None:
        self._value = value
        self._path = path
        self._accesses = accesses

    def __getitem__(self, key):
        path = f"{self._path}/{key}"
        self._accesses.append(path)
        return _track(self._value[key], path, self._accesses)

    def __iter__(self):
        return iter(self._value)

    def __len__(self):
        return len(self._value)


class _TrackedSequence(Sequence):
    def __init__(self, value, path: str, accesses: list[str]) -> None:
        self._value = value
        self._path = path
        self._accesses = accesses

    def __getitem__(self, index):
        path = f"{self._path}/{index}"
        self._accesses.append(path)
        return _track(self._value[index], path, self._accesses)

    def __len__(self):
        return len(self._value)


def _track(value, path: str, accesses: list[str]):
    if isinstance(value, Mapping):
        return _TrackedMapping(value, path, accesses)
    if isinstance(value, tuple):
        return _TrackedSequence(value, path, accesses)
    return value


def _expected_requests(document) -> list[dict]:
    requests = []
    next_handle = 0
    seq = 0
    for case in document["cases"]:
        bindings = {}
        for step in case["steps"]:
            op = step["op"]
            if op == "empty":
                args = {}
            elif op == "put":
                args = {
                    "map": bindings[step["source"]],
                    "key": step["key"],
                    "value": step["value"],
                }
            elif op == "lookup":
                args = {"map": bindings[step["source"]], "key": step["key"]}
            else:
                args = {"map": bindings[step["source"]]}
            requests.append({"seq": seq, "op": op, "args": args})
            if "bind" in step:
                bindings[step["bind"]] = f"opaque-{next_handle * 17 + 3}"
                next_handle += 1
            seq += 1
    return requests


def _event_ledger(report) -> tuple[tuple[int, str, str, str, str], ...]:
    return tuple(
        (item.seq, item.case_id, item.operation, item.event, item.disposition)
        for item in report.events
    )


def _expected_events(
    event_dispositions: tuple[tuple[str, str], ...]
) -> tuple[tuple[int, str, str, str, str], ...]:
    document = ordered_map_contract.inspect_conformance_plan().document
    expected = []
    seq = 0
    for case in document["cases"]:
        for step in case["steps"]:
            expected.extend(
                (seq, case["id"], step["op"], event, disposition)
                for event, disposition in event_dispositions
            )
            seq += 1
    return tuple(expected)


def _repository_bytes() -> dict[Path, bytes]:
    excluded = {".git", ".direnv", "__pycache__"}
    return {
        path.relative_to(ROOT): path.read_bytes()
        for path in ROOT.rglob("*")
        if path.is_file()
        and not excluded.intersection(path.relative_to(ROOT).parts)
        and path.suffix != ".pyc"
    }

try:
    runner = importlib.import_module("semantic_packages.ordered_map_runner")
    RUNNER_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.ordered_map_runner":
        raise
    runner = None
    RUNNER_IMPORT_ERROR = error


class OrderedMapRunnerPreconditionTest(unittest.TestCase):
    def test_reviewed_plan_and_hostile_adapter_precede_runner(self) -> None:
        plan = ordered_map_contract.inspect_conformance_plan()
        self.assertTrue(plan.ok, plan.diagnostics)
        self.assertEqual(PLAN_SHA256, plan.canonical_sha256)
        self.assertTrue(FAKE_ADAPTER.is_file())
        validate = runpy.run_path(os.fspath(FAKE_ADAPTER))["validate_request"]
        invalid_requests = (
            {"seq": False, "op": "empty", "args": {}},
            {"seq": 0, "op": "put", "args": {"map": "", "key": "A", "value": 1}},
            {"seq": 0, "op": "lookup", "args": {"map": "h", "key": "D"}},
            {"seq": 0, "op": "put", "args": {"map": "h", "key": "A", "value": True}},
        )
        self.assertTrue(all(validate(request, 0) for request in invalid_requests))

    def test_runner_module_is_the_only_red_predecessor(self) -> None:
        self.assertIsNotNone(
            runner,
            "O6a intentionally precedes ordered_map_runner.py; "
            f"observed {RUNNER_IMPORT_ERROR!r}",
        )


@unittest.skipIf(runner is None, "O6a freezes the runner boundary before O6b")
class OrderedMapRunnerContractTest(unittest.TestCase):
    @staticmethod
    def command(mode: str, *arguments: str) -> tuple[str, ...]:
        return (sys.executable, str(FAKE_ADAPTER), mode, *arguments)

    def run_mode(self, mode: str, *arguments: str):
        return runner.run_ordered_map_conformance(self.command(mode, *arguments))

    def assert_result(self, mode: str, result: str, cause: str | None = None):
        report = self.run_mode(mode)
        self.assertEqual(result, report.result, report)
        if cause is not None:
            self.assertIn(cause, report.causes, report)
        return report

    def test_actor_surface_accepts_only_one_explicit_child_command(self) -> None:
        self.assertEqual(
            ("command",),
            tuple(inspect.signature(runner.run_ordered_map_conformance).parameters),
        )
        for attack in (
            lambda: runner.run_ordered_map_conformance(),
            lambda: runner.run_ordered_map_conformance(self.command("reference"), plan={}),
            lambda: runner.run_ordered_map_conformance(self.command("reference"), timeout=9),
            lambda: runner.run_ordered_map_conformance(command=self.command("reference"), root=ROOT),
        ):
            with self.assertRaises(TypeError):
                attack()

    def test_reference_protocol_consumes_exact_plan_and_supports_seven_declarations(self) -> None:
        for mode in ("reference", "interned", "arbitrary-handles"):
            with self.subTest(mode=mode):
                report = self.assert_result(mode, "supports")
                self.assertEqual(PLAN_SHA256, report.plan_sha256)
                self.assertEqual(DECLARATIONS, {item.declaration_id for item in report.declarations})
                self.assertTrue(all(item.result == "supports" for item in report.declarations))
                counts = {
                    item.declaration_id: item.observation_count
                    for item in report.declarations
                }
                self.assertEqual(DECLARATION_COUNTS, counts)
                self.assertEqual(
                    CASE_LEDGER,
                    tuple(
                        (
                            item.case_id,
                            item.request_count,
                            tuple(
                                (
                                    outcome.declaration_id,
                                    outcome.observation_count,
                                    outcome.result,
                                )
                                for outcome in item.declarations
                            ),
                        )
                        for item in report.cases
                    ),
                )

    def test_one_authenticated_plan_snapshot_drives_the_run_without_reread(self) -> None:
        captured = ordered_map_contract.inspect_conformance_plan()
        accesses: list[str] = []
        tracked = replace(
            captured,
            document=_track(captured.document, "", accesses),
        )
        original_os_open = os.open
        original_builtin_open = builtins.open
        original_path_open = Path.open
        original_read_text = Path.read_text
        original_read_bytes = Path.read_bytes
        protected = {
            Path(ordered_map_contract._PLAN).resolve(),
            Path(ordered_map_contract._SCHEMA).resolve(),
        }

        def is_protected(path) -> bool:
            return not isinstance(path, int) and Path(path).resolve() in protected

        def guarded_os_open(path, *args, **kwargs):
            if is_protected(path):
                raise AssertionError("runner directly reread pinned plan authority")
            return original_os_open(path, *args, **kwargs)

        def guarded_builtin_open(path, *args, **kwargs):
            if is_protected(path):
                raise AssertionError("runner bypassed captured plan through builtins.open")
            return original_builtin_open(path, *args, **kwargs)

        def guarded_path_open(path, *args, **kwargs):
            if is_protected(path):
                raise AssertionError("runner bypassed captured plan through Path.open")
            return original_path_open(path, *args, **kwargs)

        def guarded_read_text(path, *args, **kwargs):
            if is_protected(path):
                raise AssertionError("runner bypassed captured plan through read_text")
            return original_read_text(path, *args, **kwargs)

        def guarded_read_bytes(path, *args, **kwargs):
            if is_protected(path):
                raise AssertionError("runner bypassed captured plan through read_bytes")
            return original_read_bytes(path, *args, **kwargs)

        with tempfile.TemporaryDirectory(prefix="o6a-plan-snapshot-") as raw:
            journal = Path(raw) / "requests.ndjson"
            with mock.patch.object(
                ordered_map_contract,
                "inspect_conformance_plan",
                return_value=tracked,
            ) as inspect_plan, mock.patch.object(
                os, "open", side_effect=guarded_os_open
            ), mock.patch.object(
                builtins, "open", side_effect=guarded_builtin_open
            ), mock.patch.object(
                Path, "open", autospec=True, side_effect=guarded_path_open
            ), mock.patch.object(
                Path, "read_text", autospec=True, side_effect=guarded_read_text
            ), mock.patch.object(
                Path, "read_bytes", autospec=True, side_effect=guarded_read_bytes
            ):
                report = self.run_mode("request-journal", str(journal))
                self.assertEqual("supports", report.result, report)
            inspect_plan.assert_called_once_with()
            requests = [json.loads(line) for line in journal.read_text().splitlines()]
        self.assertEqual(PLAN_SHA256, report.plan_sha256)
        self.assertEqual(_expected_requests(captured.document), requests)
        required_accesses = {
            f"/cases/{case_index}/steps/{step_index}/{field}"
            for case_index, case in enumerate(captured.document["cases"])
            for step_index, step in enumerate(case["steps"])
            for field in step
        }
        required_accesses.add("/cases")
        required_accesses.update(
            {
                path
                for case_index, _case in enumerate(captured.document["cases"])
                for path in (
                    f"/cases/{case_index}",
                    f"/cases/{case_index}/id",
                    f"/cases/{case_index}/steps",
                )
            }
        )
        self.assertLessEqual(required_accesses, set(accesses))

    def test_plan_authority_failure_stops_before_process_start(self) -> None:
        valid = ordered_map_contract.inspect_conformance_plan()
        failed = replace(
            valid,
            document=None,
            canonical_sha256=None,
            raw_sha256=None,
            diagnostics=(
                record_check.Diagnostic(
                    "ARTIFACT_CANONICAL_DIGEST_MISMATCH",
                    "<controlled-plan>",
                    "#",
                ),
            ),
        )
        with tempfile.TemporaryDirectory(prefix="o6a-plan-failure-") as raw:
            marker = Path(raw) / "started.txt"
            with mock.patch.object(
                ordered_map_contract, "inspect_conformance_plan", return_value=failed
            ):
                report = runner.run_ordered_map_conformance(
                    self.command("start-marker", str(marker))
                )
            self.assertFalse(marker.exists())
        self.assertEqual("error", report.result)
        self.assertEqual(("PLAN_AUTHORITY",), report.causes)
        self.assertEqual((), report.declarations)

    def test_semantic_counterexamples_are_declaration_local(self) -> None:
        controls = {
            "wrong-empty": {"lookup-empty"},
            "wrong-same": {"lookup-put-same"},
            "wrong-other": {"lookup-put-other"},
            "wrong-append": {"put-new-appends"},
            "destructive-new": {"persistence"},
            "destructive-existing": {"persistence"},
            "reorder-existing": {"put-existing-position"},
        }
        challenged_cases = {
            "wrong-empty": {("lookup-empty", "lookup-empty")},
            "wrong-same": {("same-class-replacement", "lookup-put-same")},
            "wrong-other": {("other-class-preservation", "lookup-put-other")},
            "wrong-append": {("new-class-append-three", "put-new-appends")},
            "destructive-new": {("retained-new-class-source", "persistence")},
            "destructive-existing": {
                ("retained-existing-class-source", "persistence")
            },
            "reorder-existing": {
                ("nonlast-overwrite-order", "put-existing-position")
            },
        }
        for mode, challenged in controls.items():
            with self.subTest(mode=mode):
                report = self.assert_result(mode, "challenges")
                self.assertEqual(
                    challenged,
                    {
                        item.declaration_id
                        for item in report.declarations
                        if item.result == "challenges"
                    },
                )
                self.assertTrue(
                    all(
                        item.result == "supports"
                        for item in report.declarations
                        if item.declaration_id not in challenged
                    )
                )
                self.assertEqual(
                    challenged_cases[mode],
                    {
                        (case.case_id, outcome.declaration_id)
                        for case in report.cases
                        for outcome in case.declarations
                        if outcome.result == "challenges"
                    },
                )

    def test_events_are_ordered_retained_and_scoped_to_effect_conformance(self) -> None:
        optional = self.assert_result("optional-event", "supports")
        self.assertEqual(
            _expected_events((("debug.emit", "optional"),)),
            _event_ledger(optional),
        )

        forbidden = self.assert_result("forbidden-event", "challenges")
        self.assertEqual(
            _expected_events((("io.read", "forbidden"),)),
            _event_ledger(forbidden),
        )
        self.assertEqual(
            {"ordered-map-effects"},
            {
                item.declaration_id
                for item in forbidden.declarations
                if item.result == "challenges"
            },
        )

        unspecified = self.assert_result("unspecified-event", "supports")
        self.assertEqual(
            _expected_events((("network.send", "unspecified"),)),
            _event_ledger(unspecified),
        )
        ordered = self.assert_result("ordered-events", "supports")
        self.assertEqual(
            _expected_events(
                (("debug.emit", "optional"), ("network.send", "unspecified"))
            ),
            _event_ledger(ordered),
        )

        boundary = self.assert_result("nonmatching-io-boundary", "supports")
        self.assertEqual(
            _expected_events((("io", "unspecified"), ("io.", "unspecified"))),
            _event_ledger(boundary),
        )
        long_match = self.assert_result("long-forbidden-event", "challenges")
        self.assertEqual(
            _expected_events((("io.read.deep", "forbidden"),)),
            _event_ledger(long_match),
        )

        adapter_error = self.assert_result(
            "adapter-error-forbidden", "error", "ADAPTER_ERROR"
        )
        self.assertEqual(
            ((0, "lookup-empty", "empty", "io.read", "forbidden"),),
            _event_ledger(adapter_error),
        )
        self.assertFalse(
            any(item.result == "challenges" for item in adapter_error.declarations)
        )

    def test_transport_adapter_and_process_failures_are_errors_not_challenges(self) -> None:
        controls = {
            "malformed-json": "RESPONSE_JSON",
            "malformed-utf8": "RESPONSE_ENCODING",
            "malformed-shape": "RESPONSE_SHAPE",
            "duplicate-member": "RESPONSE_DUPLICATE_MEMBER",
            "nonstandard-number": "RESPONSE_JSON",
            "bool-seq": "RESPONSE_SHAPE",
            "top-level-extra": "RESPONSE_SHAPE",
            "both-result-error": "RESPONSE_SHAPE",
            "empty-handle": "RESPONSE_SHAPE",
            "numeric-handle": "RESPONSE_SHAPE",
            "put-empty-handle": "RESPONSE_SHAPE",
            "extra-result-member": "RESPONSE_SHAPE",
            "put-extra-result": "RESPONSE_SHAPE",
            "lookup-extra-result": "RESPONSE_SHAPE",
            "invalid-lookup-tag": "RESPONSE_SHAPE",
            "lookup-bool-value": "RESPONSE_SHAPE",
            "lookup-some-missing-value": "RESPONSE_SHAPE",
            "lookup-none-extra-value": "RESPONSE_SHAPE",
            "invalid-entry-class": "RESPONSE_SHAPE",
            "entry-extra-member": "RESPONSE_SHAPE",
            "invalid-entry-value": "RESPONSE_SHAPE",
            "entries-not-list": "RESPONSE_SHAPE",
            "entries-result-extra": "RESPONSE_SHAPE",
            "invalid-event-container": "RESPONSE_SHAPE",
            "empty-event": "RESPONSE_SHAPE",
            "nonstring-event": "RESPONSE_SHAPE",
            "unknown-status": "RESPONSE_SHAPE",
            "empty-error-code": "RESPONSE_SHAPE",
            "empty-error-message": "RESPONSE_SHAPE",
            "numeric-error-code": "RESPONSE_SHAPE",
            "numeric-error-message": "RESPONSE_SHAPE",
            "extra-error-member": "RESPONSE_SHAPE",
            "error-top-level-extra": "RESPONSE_SHAPE",
            "output-before-request": "UNEXPECTED_OUTPUT",
            "extra-stdout": "EXTRA_STDOUT",
            "wrong-seq": "SEQUENCE_MISMATCH",
            "early-eof": "UNEXPECTED_EOF",
            "nonzero-exit": "PROCESS_EXIT",
            "status-error": "ADAPTER_ERROR",
        }
        for mode, cause in controls.items():
            with self.subTest(mode=mode):
                report = self.assert_result(mode, "error", cause)
                self.assertFalse(
                    any(item.result == "challenges" for item in report.declarations)
                )

        with tempfile.TemporaryDirectory(prefix="o6a-response-timeout-") as raw:
            marker = Path(raw) / "pid.txt"
            started = time.monotonic()
            report = runner.run_ordered_map_conformance(
                self.command("timeout", str(marker))
            )
            elapsed = time.monotonic() - started
            pid = int(marker.read_text(encoding="ascii"))
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)
            self.assertLess(elapsed, 0.60, report)
            self.assertEqual("error", report.result)
            self.assertIn("TIMEOUT", report.causes)

    def test_stdin_close_and_post_eof_lifecycle_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o6a-eof-") as raw:
            marker = Path(raw) / "closed.txt"
            report = runner.run_ordered_map_conformance(
                self.command("eof-marker", str(marker))
            )
            self.assertEqual("supports", report.result, report)
            self.assertEqual("stdin-closed\n", marker.read_text(encoding="utf-8"))

        self.assert_result("eof-nonzero", "error", "PROCESS_EXIT")
        self.assert_result("eof-extra-stdout", "error", "EXTRA_STDOUT")

        with tempfile.TemporaryDirectory(prefix="o6a-timeout-") as raw:
            marker = Path(raw) / "pid.txt"
            started = time.monotonic()
            report = runner.run_ordered_map_conformance(
                self.command("eof-timeout", str(marker))
            )
            elapsed = time.monotonic() - started
            pid = int(marker.read_text(encoding="ascii"))
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)
            self.assertLess(elapsed, 0.60, report)
            self.assertEqual("error", report.result)
            self.assertIn("TIMEOUT", report.causes)

    def test_process_start_failures_are_returned_as_reports(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o6a-missing-") as raw:
            report = runner.run_ordered_map_conformance((str(Path(raw) / "absent"),))
        self.assertEqual("error", report.result)
        self.assertIn("PROCESS_START", report.causes)
        empty = runner.run_ordered_map_conformance(())
        self.assertEqual("error", empty.result)
        self.assertIn("PROCESS_START", empty.causes)

    def test_support_retains_trust_limits_and_raw_stderr(self) -> None:
        before = _repository_bytes()
        report = self.assert_result("reference", "supports")
        after = _repository_bytes()
        self.assertEqual(before, after)
        self.assertIn("adapter-faithfulness", report.assumptions)
        self.assertIn("adapter-event-completeness", report.assumptions)
        self.assertIn("adapter-external-effects", report.exclusions)
        self.assertIn("realization-steps", report.exclusions)
        stderr = self.assert_result("stderr-bytes", "supports")
        self.assertEqual(b"ordered-map diagnostic: \xff\x00\n", stderr.stderr)
        for name in (
            "claim",
            "evidence",
            "review_state",
            "review",
            "accepted",
            "acceptance",
            "claim_state",
            "evidence_result",
            "authority",
            "manifest",
            "semantic_status",
        ):
            self.assertFalse(hasattr(report, name))

    def test_reports_are_immutable_and_replay_is_fresh(self) -> None:
        first = self.assert_result("reference", "supports")
        with self.assertRaises((AttributeError, TypeError)):
            first.result = "attacker"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            first.declarations.append(object())  # type: ignore[attr-defined]
        with self.assertRaises((AttributeError, TypeError)):
            first.declarations[0].result = "attacker"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            first.declarations[0].causes.append("attacker")  # type: ignore[attr-defined]
        with self.assertRaises((AttributeError, TypeError)):
            first.cases[0].declarations.append("attacker")  # type: ignore[attr-defined]
        with self.assertRaises((AttributeError, TypeError)):
            first.cases[0].declarations[0].result = "attacker"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            first.cases.append(object())  # type: ignore[attr-defined]
        with self.assertRaises((AttributeError, TypeError)):
            first.cases[0].case_id = "attacker"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            first.cases[0].request_count = 99  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            first.causes.append("attacker")  # type: ignore[attr-defined]
        with self.assertRaises((AttributeError, TypeError)):
            first.assumptions.append("attacker")  # type: ignore[attr-defined]
        with self.assertRaises((AttributeError, TypeError)):
            first.exclusions.append("attacker")  # type: ignore[attr-defined]
        event_report = self.assert_result("ordered-events", "supports")
        with self.assertRaises((AttributeError, TypeError)):
            event_report.events[0].event = "attacker"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            event_report.events.append(object())  # type: ignore[attr-defined]
        second = self.assert_result("reference", "supports")
        self.assertIsNot(first, second)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
