from __future__ import annotations

from collections import Counter
from dataclasses import replace
import hashlib
import importlib.util
import json
import math
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
DESIGN_SPEC = ROOT / "design-specs/0006-stable-norm2-numerical-kernel.md"
EXEC_PLAN = ROOT / "docs/exec-plans/active/0011-stable-norm2-numerical-kernel.md"
MANIFEST = ROOT / "registry/stable-norm2/manifest.json"
SOURCE = ROOT / "specs/stable-norm2.pspec"
MODULE_READY = importlib.util.find_spec("semantic_packages.numerical_kernel") is not None

CASES = (
    ("zero", "0x0.0p+0", "0x0.0p+0"),
    ("x-unit", "0x1.0000000000000p+0", "0x0.0p+0"),
    ("y-unit", "0x0.0p+0", "0x1.0000000000000p+0"),
    ("three-four", "0x1.8000000000000p+1", "0x1.0000000000000p+2"),
    ("sign-invariance", "-0x1.8000000000000p+1", "0x1.0000000000000p+2"),
    ("swapped", "0x1.0000000000000p+2", "0x1.8000000000000p+1"),
    ("unit-diagonal", "0x1.0000000000000p+0", "0x1.0000000000000p+0"),
    ("adjacent", "0x1.0000000000001p+0", "0x1.0000000000000p+0"),
    ("large-equal", "0x1.1ccf385ebc8a0p+1023", "0x1.1ccf385ebc8a0p+1023"),
    ("unbalanced", "0x1.1ccf385ebc8a0p+1023", "0x0.730d67819e8d2p-1022"),
    ("small-equal", "0x1.87e92154ef7acp-665", "0x1.87e92154ef7acp-665"),
    ("subnormal-boundary", "0x0.0000000000001p-1022", "0x1.0000000000000p-1022"),
)
CANDIDATES = (
    "stable-norm2-hypot",
    "stable-norm2-scaled",
    "stable-norm2-naive-breaker",
)
ENTRYPOINTS = (
    "implementations/stable-norm2/hypot/adapter.py",
    "implementations/stable-norm2/scaled/adapter.py",
    "fixtures/candidates/stable-norm2/naive_breaker.py",
)
PREDECESSOR_SHA256 = {
    "registry/lease-session/manifest.json": "ef6b53219e8c404521ade83b446fae006c2daaaa217c032dfb219569f7b0c2a4",
    "specs/lease-session.pspec": "ba7e831e855da11e72495e061f74dd70e6062dd7e354c0b904a25410bdd7d938",
    "scripts/record_check.py": "721c590057f568495a20b58adf39c08d25dddeaa896c4f3f825e5a5719a46edd",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StableNorm2RedBaselineTest(unittest.TestCase):
    def test_design_precedes_code_and_freezes_fourteen_falsifiers(self) -> None:
        contract = DESIGN_SPEC.read_text(encoding="utf-8")
        plan = EXEC_PLAN.read_text(encoding="utf-8")
        self.assertIn("revision 1 (user need and falsifiers frozen)", contract)
        self.assertIn("## User need", contract)
        self.assertIn("## Observable numerical contract", contract)
        self.assertIn("at most **2 ULPs**", contract)
        self.assertEqual(14, sum(f"\n{index}. " in contract for index in range(1, 15)))
        self.assertIn("No\nnumerical implementation or PR exists at this revision", plan)

    def test_campaign_and_predecessor_oracles_are_frozen(self) -> None:
        self.assertEqual(12, len(CASES))
        self.assertEqual(36, len(CASES) * len(CANDIDATES))
        self.assertEqual("large-equal", CASES[8][0])
        self.assertEqual(PREDECESSOR_SHA256, {path: _sha256(ROOT / path) for path in PREDECESSOR_SHA256})

    def test_red_predecessor_names_only_absent_numerical_surface(self) -> None:
        if MODULE_READY:
            self.skipTest("stable-norm2 package is implemented")
        self.fail("N1 stable-norm2 numerical package is absent; successor remains red")


@unittest.skipUnless(MODULE_READY, "stable-norm2 package is not implemented")
class StableNorm2JourneyTest(unittest.TestCase):
    maxDiff = None

    def _run(self, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "semantic_packages", "numerical", "inspect", str(MANIFEST), "--output", str(output)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _report(self) -> dict:
        with tempfile.TemporaryDirectory(prefix="stable-norm2-") as directory:
            output = Path(directory) / "report.json"
            result = self._run(output)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                "inspected stable-norm2 0.1.0: 2 registered realizations accepted, "
                "1 overflow breaker challenged across 36 cases; tolerance=2-ulp; "
                f"satisfaction=policy-relative -> {output}\n",
                result.stdout,
            )
            return json.loads(output.read_text(encoding="utf-8"))

    def _mutated_graph(self, address: tuple[str, str, str], mutate):
        from semantic_packages import graph
        authority = graph.inspect_manifest_authority(MANIFEST)
        observation = graph.inspect_manifest_graph(authority)
        self.assertTrue(observation.ok, observation.diagnostics)
        records = []
        for record in observation.records:
            if record.address == address:
                document = record.document
                mutate(document)
                record = replace(record, _document_text=json.dumps(document, sort_keys=True, separators=(",", ":")))
            records.append(record)
        return replace(observation, records=tuple(records))

    def test_felt_journey_and_closed_report(self) -> None:
        report = self._report()
        self.assertEqual(
            {"kind", "specification", "authority", "campaign", "candidates", "decisions", "theory", "boundaries", "assumptions", "exclusions", "conclusion"},
            set(report),
        )
        self.assertEqual("numerical-package-inspection-v1", report["kind"])
        self.assertEqual("bounded-approximate-kernel-observed", report["conclusion"])
        self.assertEqual(36, report["campaign"]["caseCount"])
        self.assertEqual(2, report["campaign"]["maxUlps"])
        self.assertEqual(100, report["campaign"]["oracleDecimalDigits"])

    def test_pspec_authors_exact_specification_and_omission_remains_valid(self) -> None:
        from semantic_packages.authoring import AuthoringDependency, PSPEC_TOML_V1, author_specification
        profile = ROOT / "registry/stable-norm2/theory/stable-norm2-profile.json"
        dependencies = (AuthoringDependency(str(profile), json.loads(profile.read_text())),)
        observation = author_specification(SOURCE.read_bytes(), PSPEC_TOML_V1, str(SOURCE), dependencies)
        self.assertTrue(observation.ok, observation.diagnostics)
        expected = json.loads((ROOT / "registry/stable-norm2/theory/stable-norm2-spec.json").read_text())
        self.assertEqual(expected, observation.document)
        stack = ROOT / "registry/stack/theory/records/stack-spec.json"
        self.assertNotIn("numericalKernels", json.loads(stack.read_text()))

    def test_every_case_exposes_complete_approximation_observation(self) -> None:
        report = self._report()
        self.assertEqual(list(CANDIDATES), [item["id"] for item in report["candidates"]])
        for candidate in report["candidates"]:
            self.assertEqual([item[0] for item in CASES], [item["id"] for item in candidate["cases"]])
            for expected, observed in zip(CASES, candidate["cases"], strict=True):
                self.assertEqual({"id", "input", "output", "oracle", "ulpDistance", "maxUlps", "result"}, set(observed))
                self.assertEqual({"x": expected[1], "y": expected[2]}, observed["input"])
                self.assertEqual(2, observed["maxUlps"])
                self.assertTrue(observed["oracle"].startswith("0x"))

    def test_two_realizations_pass_and_naive_breaker_has_exact_first_counterexample(self) -> None:
        report = self._report()
        for candidate in report["candidates"][:2]:
            self.assertTrue(candidate["registered"])
            self.assertEqual("supports", candidate["result"])
            self.assertTrue(all(case["result"] == "supports" for case in candidate["cases"]))
        breaker = report["candidates"][2]
        self.assertFalse(breaker["registered"])
        self.assertEqual("challenges", breaker["result"])
        self.assertEqual("large-equal", breaker["counterexample"]["case"])
        self.assertEqual(8, breaker["counterexample"]["index"])
        self.assertEqual("nonfinite-output", breaker["counterexample"]["reason"])
        self.assertTrue(all(item["result"] == "supports" for item in breaker["cases"][:8]))

    def test_symmetry_sign_and_range_observations_are_semantic(self) -> None:
        report = self._report()
        for candidate in report["candidates"][:2]:
            cases = {item["id"]: item for item in candidate["cases"]}
            self.assertEqual(cases["three-four"]["output"], cases["sign-invariance"]["output"])
            self.assertEqual(cases["three-four"]["output"], cases["swapped"]["output"])
            for name in ("large-equal", "unbalanced", "small-equal", "subnormal-boundary"):
                self.assertEqual("supports", cases[name]["result"])
                self.assertLessEqual(cases[name]["ulpDistance"], 2)

    def test_evidence_policy_and_boundaries_remain_separate(self) -> None:
        report = self._report()
        self.assertFalse(report["theory"]["packageEvidenceIncluded"])
        self.assertEqual(["approximate-norm2"], report["theory"]["declarations"])
        self.assertEqual(["acceptable", "acceptable"], [item["semanticStatus"] for item in report["decisions"]])
        for decision in report["decisions"]:
            self.assertEqual("bounded-numerical-campaign", decision["evidence"]["mechanism"])
            self.assertEqual("accepted", decision["evidence"]["reviewState"])
        self.assertEqual(
            [
                {"realization": "stable-norm2-hypot", "direction": "consumer->stable-norm2-hypot", "mechanism": "hex-float-child-process", "direct": False},
                {"realization": "stable-norm2-scaled", "direction": "consumer->stable-norm2-scaled", "mechanism": "hex-float-child-process", "direct": False},
            ],
            report["boundaries"],
        )

    def test_valid_negative_evidence_axes_fail_closed(self) -> None:
        from semantic_packages.numerical_kernel import inspect_numerical_package
        evidence = ("evidence", "stable-norm2-hypot-campaign", "0.1.0")
        policy = ("consumerPolicy", "stable-norm2-policy", "0.1.0")
        attacks = (
            (evidence, lambda value: value.__setitem__("result", "challenges")),
            (evidence, lambda value: value.__setitem__("result", "error")),
            (evidence, lambda value: value.__setitem__("result", "inconclusive")),
            (evidence, lambda value: value.__setitem__("reviewState", "pending")),
            (evidence, lambda value: value.__setitem__("mechanism", "assertion")),
            (policy, lambda value: value["concerns"][0].__setitem__("acceptedMechanisms", [])),
        )
        for address, mutation in attacks:
            observation = self._mutated_graph(address, mutation)
            with mock.patch("semantic_packages.numerical_kernel.graph.inspect_manifest_graph", return_value=observation):
                report, diagnostics, _ = inspect_numerical_package(MANIFEST)
            self.assertFalse(diagnostics)
            self.assertEqual("rejected", report["decisions"][0]["semanticStatus"])

    def test_execution_and_acquisition_are_exact(self) -> None:
        from semantic_packages import numerical_kernel
        calls = []
        original = numerical_kernel.subprocess.run
        def tracked(command, *args, **kwargs):
            calls.append(tuple(command))
            return original(command, *args, **kwargs)
        with (
            mock.patch("semantic_packages.numerical_kernel.subprocess.run", side_effect=tracked),
            mock.patch.object(Path, "glob", side_effect=AssertionError("discovery forbidden")),
            mock.patch.object(Path, "rglob", side_effect=AssertionError("discovery forbidden")),
            mock.patch.object(Path, "iterdir", side_effect=AssertionError("discovery forbidden")),
            mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")),
        ):
            report, diagnostics, _ = numerical_kernel.inspect_numerical_package(MANIFEST)
        self.assertFalse(diagnostics)
        self.assertIsNotNone(report)
        expected = Counter((sys.executable, os.fspath((ROOT / path).resolve())) for path in ENTRYPOINTS for _ in CASES)
        self.assertEqual(expected, Counter(calls))
        self.assertTrue(all(len(item) == 2 for item in calls))

    def test_output_alias_and_failure_preserve_inputs_and_prior_output(self) -> None:
        from semantic_packages.numerical_kernel import inspect_numerical_package, run_numerical_inspection
        before = MANIFEST.read_bytes()
        result = self._run(MANIFEST)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("NUMERICAL_OUTPUT_ALIAS", result.stderr)
        self.assertEqual(before, MANIFEST.read_bytes())
        report, diagnostics, governed = inspect_numerical_package(MANIFEST)
        self.assertFalse(diagnostics)
        with tempfile.TemporaryDirectory(prefix="norm-preserve-") as directory:
            output = Path(directory) / "report.json"
            self.assertEqual(0, self._run(output).returncode)
            accepted = output.read_bytes()
            fake = type("D", (), {"code": "NUMERICAL_TEST_FAILURE", "path": "<test>", "pointer": "#", "message": "forced"})()
            with mock.patch("semantic_packages.numerical_kernel.inspect_numerical_package", return_value=(None, (fake,), ())):
                self.assertEqual(1, run_numerical_inspection(MANIFEST, output))
            self.assertEqual(accepted, output.read_bytes())
        for path in governed:
            with mock.patch("semantic_packages.numerical_kernel.inspect_numerical_package", return_value=(report, (), governed)):
                self.assertEqual(1, run_numerical_inspection(MANIFEST, path))

    def test_nonauthority_language_and_exclusions(self) -> None:
        report = self._report()
        language = json.dumps(report, sort_keys=True).casefold()
        for forbidden in ("correct rounding established", "covers all binary64 inputs", "real-arithmetic proof established", "arbitrary numerical generality established"):
            self.assertNotIn(forbidden, language)
        self.assertEqual(5, len(report["exclusions"]))
        self.assertIn("twelve exact finite input pairs", report["exclusions"][0])
        self.assertEqual(PREDECESSOR_SHA256, {path: _sha256(ROOT / path) for path in PREDECESSOR_SHA256})


if __name__ == "__main__":
    unittest.main()
