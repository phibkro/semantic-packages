from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESIGN_SPEC = ROOT / "design-specs/0005-retry-safe-lease-session-package.md"
EXEC_PLAN = ROOT / "docs/exec-plans/active/0010-retry-safe-lease-session.md"
MANIFEST = ROOT / "registry/lease-session/manifest.json"
SOURCE = ROOT / "specs/lease-session.pspec"
MODULE_READY = importlib.util.find_spec("semantic_packages.lease_session") is not None

SCENARIOS = (
    "acquire",
    "retry-stability",
    "exclusive-holder",
    "wrong-holder-rejection",
    "completion-closure",
    "expiry-closure",
)
CANDIDATES = (
    "lease-session-table",
    "lease-session-object",
    "lease-session-resurrection-breaker",
)
PREDECESSOR_SHA256 = {
    "registry/stack/theory/records/stack-spec.json": "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1",
    "registry/ordered-map/theory/records/ordered-map-spec.json": "6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f",
    "specs/persistence-composition.pspec": "9bd4bc52b7c2fb9fe4b7ac8aaa12049e7e94250abb68828bfeef2a6620fba4a1",
    "scripts/record_check.py": "721c590057f568495a20b58adf39c08d25dddeaa896c4f3f825e5a5719a46edd",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LeaseSessionRedBaselineTest(unittest.TestCase):
    def test_contract_freezes_need_scenarios_falsifiers_and_separate_pr(self) -> None:
        contract = DESIGN_SPEC.read_text(encoding="utf-8")
        plan = EXEC_PLAN.read_text(encoding="utf-8")
        self.assertIn("revision 1 (user need and falsifiers frozen)", contract)
        self.assertIn("## User need", contract)
        self.assertIn("## Frozen falsifiers", contract)
        self.assertEqual(14, sum(f"\n{index}. " in contract for index in range(1, 15)))
        normalized_contract = contract.casefold().replace("-", " ")
        for scenario in SCENARIOS:
            self.assertIn(scenario.replace("-", " ").casefold(), normalized_contract)
        self.assertIn("Do not begin numerical-kernel files", plan)
        self.assertIn("one experienceable stacked PR", plan)

    def test_selected_predecessor_bytes_are_frozen(self) -> None:
        observed = {
            relative: _sha256(ROOT / relative) for relative in PREDECESSOR_SHA256
        }
        self.assertEqual(PREDECESSOR_SHA256, observed)

    def test_independent_trace_oracle_is_frozen_before_implementation(self) -> None:
        self.assertEqual(6, len(SCENARIOS))
        self.assertEqual(3, len(CANDIDATES))
        self.assertEqual(18, len(SCENARIOS) * len(CANDIDATES))
        self.assertEqual("expiry-closure", SCENARIOS[-1])
        self.assertEqual("lease-session-resurrection-breaker", CANDIDATES[-1])

    def test_red_predecessor_names_only_the_absent_protocol_surface(self) -> None:
        if MODULE_READY:
            self.skipTest("lease-session protocol package is implemented")
        self.fail("I1 protocol package journey is absent; successor remains red")


@unittest.skipUnless(MODULE_READY, "lease-session protocol package is not implemented")
class LeaseSessionJourneyTest(unittest.TestCase):
    maxDiff = None

    def _run(self, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "semantic_packages",
                "protocol",
                "inspect",
                str(MANIFEST),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _report(self) -> dict:
        with tempfile.TemporaryDirectory(prefix="lease-session-journey-") as directory:
            output = Path(directory) / "report.json"
            result = self._run(output)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                "inspected lease-session 0.1.0: 2 registered realizations accepted, "
                "1 breaker challenged across 18 trace cases; boundary=directional; "
                f"satisfaction=policy-relative -> {output}\n",
                result.stdout,
            )
            return json.loads(output.read_text(encoding="utf-8"))

    def test_exact_felt_journey_and_closed_report(self) -> None:
        report = self._report()
        self.assertEqual(
            {
                "kind",
                "specification",
                "authority",
                "campaign",
                "candidates",
                "decisions",
                "theory",
                "boundaries",
                "assumptions",
                "exclusions",
                "conclusion",
            },
            set(report),
        )
        self.assertEqual("protocol-package-inspection-v1", report["kind"])
        self.assertEqual("bounded-protocol-package-observed", report["conclusion"])
        self.assertEqual(18, report["campaign"]["traceCaseCount"])
        self.assertEqual(list(SCENARIOS), report["campaign"]["scenarioOrder"])

    def test_every_candidate_retains_six_complete_ordered_traces(self) -> None:
        report = self._report()
        self.assertEqual(list(CANDIDATES), [item["id"] for item in report["candidates"]])
        for candidate in report["candidates"]:
            self.assertEqual(list(SCENARIOS), [item["id"] for item in candidate["scenarios"]])
            for scenario in candidate["scenarios"]:
                self.assertTrue(scenario["trace"])
                self.assertEqual(
                    list(range(len(scenario["trace"]))),
                    [step["index"] for step in scenario["trace"]],
                )
                self.assertEqual(
                    {"index", "input", "before", "output", "after"},
                    set(scenario["trace"][0]),
                )

    def test_retry_conflict_wrong_holder_and_terminality_are_observable(self) -> None:
        report = self._report()
        passing = report["candidates"][:2]
        for candidate in passing:
            by_id = {item["id"]: item for item in candidate["scenarios"]}
            retry = by_id["retry-stability"]["trace"][-1]
            self.assertEqual("t1", retry["output"]["token"])
            self.assertEqual(retry["before"], retry["after"])
            conflict = by_id["exclusive-holder"]["trace"][-1]
            self.assertEqual("busy", conflict["output"]["status"])
            self.assertEqual(conflict["before"], conflict["after"])
            wrong = by_id["wrong-holder-rejection"]["trace"][-1]
            self.assertEqual("denied", wrong["output"]["status"])
            self.assertEqual(wrong["before"], wrong["after"])
            self.assertEqual(
                "completed", by_id["completion-closure"]["trace"][-1]["after"]["state"]
            )
            self.assertEqual(
                "expired", by_id["expiry-closure"]["trace"][-1]["after"]["state"]
            )

    def test_exact_resurrection_breaker_is_challenged(self) -> None:
        report = self._report()
        breaker = report["candidates"][2]
        self.assertFalse(breaker["registered"])
        self.assertEqual("challenges", breaker["result"])
        self.assertEqual("expiry-closure", breaker["counterexample"]["scenario"])
        self.assertEqual(2, breaker["counterexample"]["step"])
        self.assertEqual("expired", breaker["counterexample"]["expectedState"])
        self.assertEqual("completed", breaker["counterexample"]["actualState"])

    def test_two_registered_realizations_are_independent_and_policy_accepted(self) -> None:
        report = self._report()
        registered = [item for item in report["candidates"] if item["registered"]]
        self.assertEqual(2, len(registered))
        self.assertEqual(2, len({item["representation"] for item in registered}))
        self.assertEqual(2, len({tuple(item["sources"]) for item in registered}))
        self.assertTrue(all(item["result"] == "supports" for item in registered))
        self.assertEqual(
            ["lease-session-table", "lease-session-object"],
            [item["realization"]["id"] for item in report["decisions"]],
        )
        self.assertTrue(all(item["semanticStatus"] == "acceptable" for item in report["decisions"]))

    def test_evidence_theory_projection_and_boundaries_remain_separate(self) -> None:
        report = self._report()
        self.assertFalse(report["theory"]["packageEvidenceIncluded"])
        self.assertIn("protocol-conformance", report["theory"]["declarations"])
        for decision in report["decisions"]:
            self.assertEqual("bounded-protocol-campaign", decision["evidence"]["mechanism"])
            self.assertEqual("accepted", decision["evidence"]["reviewState"])
            self.assertEqual("supports", decision["evidence"]["result"])
        self.assertEqual(2, len(report["boundaries"]))
        self.assertTrue(all(item["direction"] for item in report["boundaries"]))
        self.assertTrue(all(item["mechanism"] for item in report["boundaries"]))

    def test_structural_and_authority_mutations_fail_closed(self) -> None:
        from semantic_packages.lease_session import inspect_protocol_document

        document = json.loads((ROOT / "registry/lease-session/theory/lease-session-spec.json").read_text())
        mutations = []
        duplicate = json.loads(json.dumps(document))
        duplicate["protocols"][0]["states"].append("held")
        mutations.append((duplicate, "PROTOCOL_DUPLICATE_STATE"))
        initial_terminal = json.loads(json.dumps(document))
        initial_terminal["protocols"][0]["initialState"] = "completed"
        mutations.append((initial_terminal, "PROTOCOL_INITIAL_TERMINAL"))
        dangling = json.loads(json.dumps(document))
        dangling["protocols"][0]["transitions"][0]["to"] = "missing"
        mutations.append((dangling, "PROTOCOL_UNKNOWN_STATE"))
        unreachable = json.loads(json.dumps(document))
        unreachable["protocols"][0]["transitions"] = []
        mutations.append((unreachable, "PROTOCOL_UNREACHABLE_STATE"))
        for attacked, code in mutations:
            observation = inspect_protocol_document(attacked)
            self.assertFalse(observation.ok)
            self.assertEqual(code, observation.diagnostics[0].code)

    def test_output_alias_and_failure_preserve_governed_inputs(self) -> None:
        before = MANIFEST.read_bytes()
        result = self._run(MANIFEST)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("PROTOCOL_OUTPUT_ALIAS", result.stderr)
        self.assertEqual(before, MANIFEST.read_bytes())

    def test_nonauthority_language_and_predecessor_regressions(self) -> None:
        report = self._report()
        language = json.dumps(report, sort_keys=True).casefold()
        for forbidden in (
            "real-time guarantee",
            "liveness proved",
            "universal session type",
            "arbitrary-domain generality",
        ):
            self.assertNotIn(forbidden, language)
        self.assertEqual(
            PREDECESSOR_SHA256,
            {relative: _sha256(ROOT / relative) for relative in PREDECESSOR_SHA256},
        )


if __name__ == "__main__":
    unittest.main()
