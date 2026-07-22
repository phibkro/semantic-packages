"""Red-first O6d controls for reproducible OrderedMap report facts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import builtins
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest import mock

from semantic_packages import ordered_map_contract, ordered_map_runner
from semantic_packages.ordered_map_runner import EventOutcome


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "ordered_map_report_check.py"
REPORTS = {
    "ordered-map-rust": ROOT / "reports" / "ordered-map" / "rust-campaign-report.json",
    "ordered-map-typescript": ROOT
    / "reports"
    / "ordered-map"
    / "typescript-campaign-report.json",
    "ordered-map-reorder-breaker": ROOT
    / "fixtures"
    / "candidates"
    / "ordered-map"
    / "reorder_breaker"
    / "reorder-breaker-report.json",
}
BREAKER = REPORTS["ordered-map-reorder-breaker"].parent
REPORT_BOUNDARY_EXISTS = CHECKER.is_file() and all(path.is_file() for path in REPORTS.values())
DECLARATION_COUNTS = {
    "lookup-empty": 1,
    "ordered-map-effects": 30,
    "lookup-put-same": 2,
    "lookup-put-other": 1,
    "put-existing-position": 1,
    "put-new-appends": 1,
    "persistence": 2,
}
CASE_REQUESTS = {
    "lookup-empty": 2,
    "same-class-replacement": 5,
    "other-class-preservation": 4,
    "nonlast-overwrite-order": 5,
    "new-class-append-three": 5,
    "retained-new-class-source": 4,
    "retained-existing-class-source": 5,
}
CASE_DECLARATIONS = {
    "lookup-empty": {"lookup-empty": 1, "ordered-map-effects": 2},
    "same-class-replacement": {"lookup-put-same": 2, "ordered-map-effects": 5},
    "other-class-preservation": {"lookup-put-other": 1, "ordered-map-effects": 4},
    "nonlast-overwrite-order": {"put-existing-position": 1, "ordered-map-effects": 5},
    "new-class-append-three": {"put-new-appends": 1, "ordered-map-effects": 5},
    "retained-new-class-source": {"persistence": 1, "ordered-map-effects": 4},
    "retained-existing-class-source": {"persistence": 1, "ordered-map-effects": 5},
}
COMMON_INPUTS = {
    "plan": {
        "path": "contracts/ordered-map/conformance-plan.json",
        "rawSha256": "bfffbe98114c78c04865bccadc143a02cd46beff71c0f04c0b7f5b522d15c1d3",
        "canonicalSha256": "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a",
    },
    "runner": {
        "path": "semantic_packages/ordered_map_runner.py",
        "sha256": "9b4729ef5b879821e19926e85c0e4a9db18c81a94e2c28e9215ea28d8b24f28b",
    },
    "specification": {
        "path": "registry/ordered-map/theory/records/ordered-map-spec.json",
        "sha256": "6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f",
    },
    "profile": {
        "path": "registry/ordered-map/theory/dependencies/ordered-map-profile.json",
        "sha256": "6d1297892c355a569e244c2b94448a5f5edaf9b1bf2ae54f940d7c4494fe225f",
    },
    "harness": [
        {
            "path": "semantic_packages/__init__.py",
            "sha256": "ae06adf5d023d88f6380400bd771f3f849934b945c19aff9eb5c5baae7dfd48f",
        },
        {
            "path": "semantic_packages/ordered_map_contract.py",
            "sha256": "60f6c0d01faa544516dddaa7b91e1277a87b7b3aa92d8d5491792164547c7766",
        },
        {
            "path": "semantic_packages/canonical_artifact.py",
            "sha256": "de90cf40f0070b360cf7c149cf6880b29a0d1c32b3f0767e610c68787d2c4144",
        },
        {
            "path": "scripts/record_check.py",
            "sha256": "721c590057f568495a20b58adf39c08d25dddeaa896c4f3f825e5a5719a46edd",
        },
        {
            "path": "schemas/ordered-map-conformance-plan.schema.json",
            "sha256": "d9e61cad21524a13312b86782967e5f14c46bed0c5a0b0888aaa3ea4174289d1",
        },
    ],
}
SOURCE_PATHS = {
    "ordered-map-rust": {
        "implementations/ordered-map/rust/src/main.rs":
            "80c4d154ba753bf4cc2580aedc91a6eb9bded2da28318d1c63c2b76bf8eb1fc1",
        "implementations/ordered-map/rust/src/ordered_map.rs":
            "5d81fde8a1695c1b1ce38b0dbef81da36376e5caffad20f7175b9469e8727012",
    },
    "ordered-map-typescript": {
        "implementations/ordered-map/typescript/adapter.ts":
            "c4a6d37151962df24ce362dd6a3e84cbb1e53045eca780f9d4c37d650579d670",
        "implementations/ordered-map/typescript/ordered_map.ts":
            "b2b034ffb23dab1f68eb41c7b42a60a28cbb1b00cb2e96f4c4f4bb9b9efb0697",
    },
    "ordered-map-reorder-breaker": {
        "fixtures/candidates/ordered-map/reorder_breaker/src/main.rs": None,
        "fixtures/candidates/ordered-map/reorder_breaker/src/ordered_map.rs": None,
    },
}
RUSTC_OUTPUT = [
    "rustc 1.96.1 (31fca3adb 2026-06-26) (built from a source tarball)",
    "binary: rustc",
    "commit-hash: 31fca3adb283cc9dfd56b49cdee9a96eb9c96ffd",
    "commit-date: 2026-06-26",
    "host: x86_64-unknown-linux-gnu",
    "release: 1.96.1",
    "LLVM version: 21.1.8",
]
HARNESS_TOOLCHAIN = {
    "python": {"command": "$PYTHON --version", "output": ["Python 3.14.6"]},
    "pythonLibraries": {
        "command": "$PYTHON -c <locked-harness-library-version-probe>",
        "output": ["jsonschema 4.26.0", "referencing 0.37.0"],
    },
}
TOOLCHAINS = {
    "ordered-map-rust": {
        **HARNESS_TOOLCHAIN,
        "gcc": {
            "command": "$GCC --version",
            "output": [
                "gcc (GCC) 15.2.0",
                "Copyright (C) 2025 Free Software Foundation, Inc.",
                "This is free software; see the source for copying conditions.  There is NO",
                "warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.",
                "",
            ],
        },
        "rustc": {"command": "$RUSTC --version --verbose", "output": RUSTC_OUTPUT},
    },
    "ordered-map-typescript": {
        **HARNESS_TOOLCHAIN,
        "deno": {
            "command": "$DENO --version",
            "output": [
                "deno 2.9.2 (stable, release, x86_64-unknown-linux-gnu)",
                "v8 14.9.207.2-rusty",
                "typescript 6.0.3",
            ],
        }
    },
    "ordered-map-reorder-breaker": {
        **HARNESS_TOOLCHAIN,
        "gcc": {
            "command": "$GCC --version",
            "output": [
                "gcc (GCC) 15.2.0",
                "Copyright (C) 2025 Free Software Foundation, Inc.",
                "This is free software; see the source for copying conditions.  There is NO",
                "warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.",
                "",
            ],
        },
        "rustc": {"command": "$RUSTC --version --verbose", "output": RUSTC_OUTPUT},
    },
}
COMMANDS = {
    "ordered-map-rust": {
        "build": [
            "$RUSTC", "--edition=2024", "-C", "opt-level=2", "-C", "linker=$GCC",
            "-o", "$RUST_BINARY", "implementations/ordered-map/rust/src/main.rs",
        ],
        "campaign": ["$RUST_BINARY"],
    },
    "ordered-map-typescript": {
        "check": [
            "$DENO", "check", "--no-config", "--no-lock", "--no-npm", "--no-remote",
            "implementations/ordered-map/typescript/adapter.ts",
            "implementations/ordered-map/typescript/ordered_map.ts",
        ],
        "campaign": [
            "$DENO", "run", "--no-config", "--no-lock", "--no-npm", "--no-remote",
            "--no-prompt", "implementations/ordered-map/typescript/adapter.ts",
        ],
    },
    "ordered-map-reorder-breaker": {
        "build": [
            "$RUSTC", "--edition=2024", "-C", "opt-level=2", "-C", "linker=$GCC",
            "-o", "$BREAKER_BINARY",
            "fixtures/candidates/ordered-map/reorder_breaker/src/main.rs",
        ],
        "campaign": ["$BREAKER_BINARY"],
    },
}
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def _load_checker(path: Path = CHECKER):
    module_name = f"ordered_map_report_check_{hashlib.sha256(os.fspath(path).encode()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load OrderedMap report checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _walk(value):
    yield value
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _expected_declarations(*, breaker: bool = False) -> list[dict]:
    return [
        {
            "id": declaration,
            "observationCount": count,
            "result": (
                "challenges" if breaker and declaration == "put-existing-position" else "supports"
            ),
            "causes": (
                ["OBSERVATION_MISMATCH"]
                if breaker and declaration == "put-existing-position"
                else []
            ),
        }
        for declaration, count in DECLARATION_COUNTS.items()
    ]


def _expected_cases(*, breaker: bool = False) -> list[dict]:
    cases = []
    for case, request_count in CASE_REQUESTS.items():
        declarations = []
        for declaration, observation_count in CASE_DECLARATIONS[case].items():
            challenged = breaker and case == "nonlast-overwrite-order" and declaration == "put-existing-position"
            declarations.append(
                {
                    "id": declaration,
                    "observationCount": observation_count,
                    "result": "challenges" if challenged else "supports",
                    "causes": ["OBSERVATION_MISMATCH"] if challenged else [],
                }
            )
        cases.append({"id": case, "requestCount": request_count, "declarations": declarations})
    return cases


def _assert_raw_binding(test: unittest.TestCase, binding: dict) -> None:
    test.assertEqual({"path", "sha256"}, set(binding))
    test.assertFalse(Path(binding["path"]).is_absolute())
    test.assertEqual(
        hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest(),
        binding["sha256"],
    )


def _compact_rust(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return re.sub(r"\s+", "", text)


def _perturb_report(report, key: str):
    cause = f"TEST_EXECUTION_{key}"
    declarations = tuple(
        replace(
            item,
            declaration_id=f"test-{key}-{item.declaration_id}",
            observation_count=item.observation_count + 100,
            result=f"test-{key}",
            causes=(cause,),
        )
        for item in reversed(report.declarations)
    )
    declarations += (
        replace(
            report.declarations[0],
            declaration_id=f"test-{key}-extra-declaration",
            observation_count=999,
            result=f"test-{key}",
            causes=(cause,),
        ),
    )
    cases = tuple(
        replace(
            case,
            case_id=f"test-{key}-{case.case_id}",
            request_count=case.request_count + 100,
            declarations=tuple(
                replace(
                    item,
                    declaration_id=f"test-{key}-{item.declaration_id}",
                    observation_count=item.observation_count + 100,
                    result=f"test-{key}",
                    causes=(cause,),
                )
                for item in reversed(case.declarations)
            ),
        )
        for case in reversed(report.cases)
    )
    cases += (
        replace(
            report.cases[0],
            case_id=f"test-{key}-extra-case",
            request_count=999,
            declarations=(declarations[-1],),
        ),
    )
    return replace(
        report,
        result=f"test-{key}",
        causes=(cause,),
        plan_sha256=hashlib.sha256(key.encode()).hexdigest(),
        declarations=declarations,
        cases=cases,
        events=(EventOutcome(900, f"case-{key}", "empty", f"event-{key}", "unspecified"),),
        assumptions=(f"assumption-{key}",),
        exclusions=(f"exclusion-{key}",),
        stderr=f"stderr-{key}".encode(),
    )


def _expected_perturbed_outcome(report, key: str) -> dict:
    cause = f"TEST_EXECUTION_{key}"
    declaration_rows = [
        {
            "id": f"test-{key}-{item.declaration_id}",
            "observationCount": item.observation_count + 100,
            "result": f"test-{key}",
            "causes": [cause],
        }
        for item in reversed(report.declarations)
    ]
    declaration_rows.append(
        {
            "id": f"test-{key}-extra-declaration",
            "observationCount": 999,
            "result": f"test-{key}",
            "causes": [cause],
        }
    )
    case_rows = [
        {
            "id": f"test-{key}-{case.case_id}",
            "requestCount": case.request_count + 100,
            "declarations": [
                {
                    "id": f"test-{key}-{item.declaration_id}",
                    "observationCount": item.observation_count + 100,
                    "result": f"test-{key}",
                    "causes": [cause],
                }
                for item in reversed(case.declarations)
            ],
        }
        for case in reversed(report.cases)
    ]
    case_rows.append(
        {
            "id": f"test-{key}-extra-case",
            "requestCount": 999,
            "declarations": [declaration_rows[-1]],
        }
    )
    return {
        "result": f"test-{key}",
        "causes": [cause],
        "planCanonicalSha256": hashlib.sha256(key.encode()).hexdigest(),
        "requestCount": sum(case.request_count + 100 for case in report.cases) + 999,
        "declarations": declaration_rows,
        "cases": case_rows,
        "events": [
            {
                "seq": 900,
                "case": f"case-{key}",
                "operation": "empty",
                "event": f"event-{key}",
                "disposition": "unspecified",
            }
        ],
        "assumptions": [f"assumption-{key}"],
        "exclusions": [f"exclusion-{key}"],
        "stderrSha256": hashlib.sha256(f"stderr-{key}".encode()).hexdigest(),
    }


class OrderedMapReportPreconditionTest(unittest.TestCase):
    def test_accepted_plan_and_independent_candidates_precede_reports(self) -> None:
        plan = ordered_map_contract.inspect_conformance_plan()
        self.assertTrue(plan.ok, plan.diagnostics)
        self.assertEqual(
            "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a",
            plan.canonical_sha256,
        )
        for path in (
            ROOT / "implementations/ordered-map/rust/src/main.rs",
            ROOT / "implementations/ordered-map/rust/src/ordered_map.rs",
            ROOT / "implementations/ordered-map/typescript/adapter.ts",
            ROOT / "implementations/ordered-map/typescript/ordered_map.ts",
        ):
            self.assertTrue(path.is_file(), path)

    def test_checker_candidate_reports_and_breaker_are_the_only_red_predecessor(self) -> None:
        self.assertTrue(
            REPORT_BOUNDARY_EXISTS,
            "O6d-P intentionally precedes the report checker, two report facts, and selective breaker",
        )


@unittest.skipUnless(REPORT_BOUNDARY_EXISTS, "O6d-P freezes report controls before reproduction")
class OrderedMapReportContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = _load_checker()
        cls.payloads = {
            candidate: json.loads(path.read_text(encoding="utf-8"))
            for candidate, path in REPORTS.items()
        }

    def test_reproduction_is_fresh_byte_exact_and_repository_relative(self) -> None:
        first = self.checker.reproduce_ordered_map_reports(ROOT)
        second = self.checker.reproduce_ordered_map_reports(ROOT)
        self.assertEqual(first, second)
        self.assertEqual({path.relative_to(ROOT) for path in REPORTS.values()}, set(first))
        for relative, fresh in first.items():
            self.assertEqual((ROOT / relative).read_bytes(), fresh, relative)
            self.assertTrue(fresh.endswith(b"\n"))
            self.assertEqual(fresh, self.checker.canonical_json(json.loads(fresh)))

        errors, summary = self.checker.run_ordered_map_report_checks(ROOT)
        self.assertEqual([], errors)
        self.assertEqual(
            "OrderedMap report checks passed: 2 fresh candidate reports and 1 selective breaker.",
            summary,
        )

    def test_reports_bind_exact_plan_runner_inputs_sources_commands_and_toolchains(self) -> None:
        for candidate, payload in self.payloads.items():
            with self.subTest(candidate=candidate):
                self.assertEqual(
                    {
                        "formatVersion",
                        "kind",
                        "candidate",
                        "packetRole",
                        "protocol",
                        "inputs",
                        "toolchain",
                        "commands",
                        "binarySha256",
                        "outcome",
                    },
                    set(payload),
                )
                self.assertEqual(1, payload["formatVersion"])
                self.assertEqual("ordered-map-campaign-report", payload["kind"])
                self.assertEqual(candidate, payload["candidate"])
                self.assertEqual("ordered-map-runner-json-v1", payload["protocol"])
                inputs = payload["inputs"]
                self.assertEqual(
                    {"harness", "plan", "profile", "runner", "sources", "specification"},
                    set(inputs),
                )
                self.assertEqual(COMMON_INPUTS["plan"], inputs["plan"])
                self.assertEqual(
                    COMMON_INPUTS["plan"]["rawSha256"],
                    hashlib.sha256((ROOT / COMMON_INPUTS["plan"]["path"]).read_bytes()).hexdigest(),
                )
                self.assertEqual(
                    COMMON_INPUTS["plan"]["canonicalSha256"],
                    ordered_map_contract.inspect_conformance_plan().canonical_sha256,
                )
                for name in ("profile", "runner", "specification"):
                    self.assertEqual(COMMON_INPUTS[name], inputs[name])
                    _assert_raw_binding(self, inputs[name])
                self.assertEqual(COMMON_INPUTS["harness"], inputs["harness"])
                for binding in inputs["harness"]:
                    _assert_raw_binding(self, binding)
                sources = {item["path"]: item["sha256"] for item in inputs["sources"]}
                expected_sources = [
                    {
                        "path": path,
                        "sha256": digest
                        or hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                    }
                    for path, digest in SOURCE_PATHS[candidate].items()
                ]
                self.assertEqual(expected_sources, inputs["sources"])
                self.assertEqual(len(sources), len(inputs["sources"]))
                for item in inputs["sources"]:
                    _assert_raw_binding(self, item)
                for path, digest in SOURCE_PATHS[candidate].items():
                    if digest is not None:
                        self.assertEqual(digest, sources[path])
                self.assertEqual(COMMANDS[candidate], payload["commands"])
                self.assertNotIn(str(ROOT), json.dumps(payload["commands"]))
                self.assertEqual(TOOLCHAINS[candidate], payload["toolchain"])
                if candidate == "ordered-map-typescript":
                    self.assertIsNone(payload["binarySha256"])
                else:
                    self.assertRegex(payload["binarySha256"], r"^[0-9a-f]{64}$")
                if candidate == "ordered-map-rust":
                    self.assertEqual(
                        "ae457dde79c86091ff79b4603cf436f8d1c06b67affe4511ed089ecc86cb8a2a",
                        payload["binarySha256"],
                    )

    def test_report_facts_expose_no_claim_evidence_review_or_acceptance_axis(self) -> None:
        forbidden_vocabulary = {
            "claim",
            "claims",
            "evidence",
            "review",
            "reviewed",
            "accepted",
            "acceptance",
            "authority",
            "manifest",
            "membership",
            "semanticCompatibility",
            "verified",
            "signature",
            "attestation",
            "productContract",
            "registration",
            "reviewState",
            "acceptedEvidence",
        }
        for candidate, payload in self.payloads.items():
            observed = {item.casefold() for item in _walk(payload) if isinstance(item, str)}
            with self.subTest(candidate=candidate):
                self.assertTrue(
                    {item.casefold() for item in forbidden_vocabulary}.isdisjoint(observed)
                )

    def test_reproduction_cannot_read_retained_reports_and_consumes_each_execution(self) -> None:
        expected = {
            path.relative_to(ROOT): path.read_bytes() for path in REPORTS.values()
        }
        with tempfile.TemporaryDirectory(prefix="ordered-map-fresh-execution-") as raw:
            copied = Path(raw) / "repository"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", ".direnv"))
            for path in REPORTS.values():
                (copied / path.relative_to(ROOT)).unlink()
            guarded_reports = {
                path.resolve() for path in REPORTS.values()
            } | {
                (copied / path.relative_to(ROOT)).resolve() for path in REPORTS.values()
            }
            original_open = Path.open
            original_builtin_open = builtins.open
            original_os_open = os.open

            def is_guarded(path) -> bool:
                try:
                    return Path(path).resolve() in guarded_reports
                except TypeError:
                    return False

            def guarded_open(path, *args, **kwargs):
                if is_guarded(path):
                    raise AssertionError(f"reproduction read retained report: {path}")
                return original_open(path, *args, **kwargs)

            def guarded_builtin_open(path, *args, **kwargs):
                if is_guarded(path):
                    raise AssertionError(f"reproduction read retained report: {path}")
                return original_builtin_open(path, *args, **kwargs)

            def guarded_os_open(path, *args, **kwargs):
                if is_guarded(path):
                    raise AssertionError(f"reproduction read retained report: {path}")
                return original_os_open(path, *args, **kwargs)

            with ExitStack() as stack:
                stack.enter_context(mock.patch.object(Path, "open", guarded_open))
                stack.enter_context(mock.patch.object(builtins, "open", guarded_builtin_open))
                stack.enter_context(mock.patch.object(os, "open", guarded_os_open))
                fresh_checker = _load_checker(copied / CHECKER.relative_to(ROOT))
                self.assertIs(
                    ordered_map_runner.run_ordered_map_conformance,
                    fresh_checker.run_ordered_map_conformance,
                )
                self.assertEqual(expected, fresh_checker.reproduce_ordered_map_reports(copied))

            original_runner = fresh_checker.run_ordered_map_conformance
            commands: dict[str, tuple[str, ...]] = {}
            binary_digests: dict[str, str] = {}
            original_reports: dict[str, object] = {}

            def observed_runner(command):
                command = tuple(os.fspath(item) for item in command)
                report = original_runner(command)
                if len(command) > 1:
                    key = "typescript"
                elif report.result == "challenges":
                    key = "breaker"
                else:
                    key = "rust"
                self.assertNotIn(key, commands)
                commands[key] = command
                original_reports[key] = report
                if len(command) == 1:
                    binary_digests[key] = hashlib.sha256(Path(command[0]).read_bytes()).hexdigest()
                return _perturb_report(report, key)

            with mock.patch.object(
                fresh_checker, "run_ordered_map_conformance", side_effect=observed_runner
            ):
                with ExitStack() as stack:
                    stack.enter_context(mock.patch.object(Path, "open", guarded_open))
                    stack.enter_context(mock.patch.object(builtins, "open", guarded_builtin_open))
                    stack.enter_context(mock.patch.object(os, "open", guarded_os_open))
                    perturbed = fresh_checker.reproduce_ordered_map_reports(copied)

        self.assertEqual({"rust", "typescript", "breaker"}, set(commands))
        self.assertEqual(1, len(commands["rust"]))
        self.assertEqual(1, len(commands["breaker"]))
        self.assertEqual(
            Path(shutil.which(os.environ.get("DENO", "deno"))).resolve(),
            Path(commands["typescript"][0]).resolve(),
        )
        self.assertEqual(
            (
                "run", "--no-config", "--no-lock", "--no-npm", "--no-remote",
                "--no-prompt",
                os.fspath(copied / "implementations/ordered-map/typescript/adapter.ts"),
            ),
            commands["typescript"][1:],
        )
        report_keys = {
            "ordered-map-rust": "rust",
            "ordered-map-typescript": "typescript",
            "ordered-map-reorder-breaker": "breaker",
        }
        for candidate, key in report_keys.items():
            payload = json.loads(perturbed[REPORTS[candidate].relative_to(ROOT)])
            self.assertEqual(
                _expected_perturbed_outcome(original_reports[key], key),
                payload["outcome"],
            )
        self.assertEqual(
            binary_digests["rust"],
            json.loads(perturbed[REPORTS["ordered-map-rust"].relative_to(ROOT)])["binarySha256"],
        )
        self.assertEqual(
            binary_digests["breaker"],
            json.loads(perturbed[REPORTS["ordered-map-reorder-breaker"].relative_to(ROOT)])["binarySha256"],
        )

    def test_recorded_build_check_and_tool_probes_reproduce_independently(self) -> None:
        tools = {
            "PYTHON": sys.executable,
            "RUSTC": shutil.which(os.environ.get("RUSTC", "rustc")),
            "GCC": shutil.which(os.environ.get("GCC", "gcc")),
            "DENO": shutil.which(os.environ.get("DENO", "deno")),
        }
        self.assertTrue(all(tools.values()), tools)
        probes = {
            "python": (
                [tools["PYTHON"], "--version"],
                HARNESS_TOOLCHAIN["python"]["output"],
            ),
            "pythonLibraries": (
                [
                    tools["PYTHON"],
                    "-c",
                    "import importlib.metadata as m;"
                    "print('jsonschema '+m.version('jsonschema'));"
                    "print('referencing '+m.version('referencing'))",
                ],
                HARNESS_TOOLCHAIN["pythonLibraries"]["output"],
            ),
            "rustc": ([tools["RUSTC"], "--version", "--verbose"], RUSTC_OUTPUT),
            "gcc": ([tools["GCC"], "--version"], TOOLCHAINS["ordered-map-rust"]["gcc"]["output"]),
            "deno": ([tools["DENO"], "--version"], TOOLCHAINS["ordered-map-typescript"]["deno"]["output"]),
        }
        for name, (argv, expected) in probes.items():
            with self.subTest(tool=name):
                observed = subprocess.run(
                    argv, check=True, capture_output=True, text=True, timeout=10
                ).stdout.splitlines()
                self.assertEqual(expected, observed)

        with tempfile.TemporaryDirectory(prefix="ordered-map-independent-build-") as raw:
            for candidate, source, variable in (
                (
                    "ordered-map-rust",
                    ROOT / "implementations/ordered-map/rust/src/main.rs",
                    "RUST_BINARY",
                ),
                (
                    "ordered-map-reorder-breaker",
                    BREAKER / "src/main.rs",
                    "BREAKER_BINARY",
                ),
            ):
                output = Path(raw) / candidate
                argv = [
                    tools["RUSTC"], "--edition=2024", "-C", "opt-level=2", "-C",
                    f"linker={tools['GCC']}", "-o", os.fspath(output),
                    os.fspath(source.relative_to(ROOT)),
                ]
                subprocess.run(
                    argv, cwd=ROOT, check=True, capture_output=True, timeout=20
                )
                self.assertEqual(
                    self.payloads[candidate]["binarySha256"],
                    hashlib.sha256(output.read_bytes()).hexdigest(),
                    variable,
                )

        subprocess.run(
            (
                tools["DENO"], "check", "--no-config", "--no-lock", "--no-npm",
                "--no-remote",
                "implementations/ordered-map/typescript/adapter.ts",
                "implementations/ordered-map/typescript/ordered_map.ts",
            ),
            cwd=ROOT,
            check=True,
            capture_output=True,
            timeout=20,
        )

    def test_candidate_reports_support_every_exact_declaration_case_and_invocation(self) -> None:
        for candidate in ("ordered-map-rust", "ordered-map-typescript"):
            outcome = self.payloads[candidate]["outcome"]
            with self.subTest(candidate=candidate):
                self.assertEqual("candidate", self.payloads[candidate]["packetRole"])
                self.assertEqual(("supports", [], 30), (
                    outcome["result"], outcome["causes"], outcome["requestCount"]
                ))
                self.assertEqual(
                    {
                        "result", "causes", "requestCount", "declarations", "cases",
                        "events", "assumptions", "exclusions", "stderrSha256",
                        "planCanonicalSha256",
                    },
                    set(outcome),
                )
                self.assertEqual(
                    COMMON_INPUTS["plan"]["canonicalSha256"], outcome["planCanonicalSha256"]
                )
                self.assertEqual(["adapter-faithfulness", "adapter-event-completeness"], outcome["assumptions"])
                self.assertEqual(["adapter-external-effects", "realization-steps"], outcome["exclusions"])
                self.assertEqual(EMPTY_SHA256, outcome["stderrSha256"])
                self.assertEqual([], outcome["events"])
                self.assertEqual(_expected_declarations(), outcome["declarations"])
                self.assertEqual(_expected_cases(), outcome["cases"])

    def test_breaker_is_isolated_and_challenges_only_existing_position(self) -> None:
        self.assertEqual(
            {"README.md", "src/main.rs", "src/ordered_map.rs", "reorder-breaker-report.json"},
            {path.relative_to(BREAKER).as_posix() for path in BREAKER.rglob("*") if path.is_file()},
        )
        for path in BREAKER.rglob("*"):
            self.assertFalse(path.is_symlink(), path)
        packet_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (BREAKER / "README.md", BREAKER / "src/main.rs", BREAKER / "src/ordered_map.rs")
        )
        for forbidden in (
            "implementations/ordered-map",
            "semantic_packages",
            "ordered_map_runner",
            "ordered_map_contract",
            "contracts/ordered-map",
            *DECLARATION_COUNTS,
            *CASE_REQUESTS,
        ):
            self.assertNotIn(forbidden, packet_text)
        main = (BREAKER / "src/main.rs").read_text(encoding="utf-8")
        map_source = (BREAKER / "src/ordered_map.rs").read_text(encoding="utf-8")
        compact = _compact_rust(main + "\n" + map_source)
        identifiers = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", compact))
        self.assertEqual(1, compact.count("modordered_map;"))
        self.assertNotIn("mod", _compact_rust(map_source))
        for forbidden in (
            "include!",
            "include_str!",
            "include_bytes!",
            "#[path=",
            "cfg_attr",
            "path=",
            "std::fs",
            "File::open",
            "OpenOptions",
            "Command",
            "env!",
            "option_env!",
            "std::net",
            "TcpStream",
            "UdpSocket",
        ):
            self.assertNotIn(forbidden, compact)
        self.assertTrue(
            {
                "fs", "File", "OpenOptions", "Command", "env", "current_dir",
                "net", "os", "UnixStream", "UnixDatagram", "TcpStream", "UdpSocket",
                "include", "include_str", "include_bytes", "cfg_attr",
            }.isdisjoint(identifiers),
            identifiers,
        )
        self.assertNotEqual(
            hashlib.sha256((ROOT / "implementations/ordered-map/rust/src/ordered_map.rs").read_bytes()).digest(),
            hashlib.sha256((BREAKER / "src/ordered_map.rs").read_bytes()).digest(),
        )
        for path in BREAKER.rglob("*"):
            if path.is_dir():
                self.assertEqual("src", path.relative_to(BREAKER).as_posix())

        payload = self.payloads["ordered-map-reorder-breaker"]
        self.assertEqual("targeted-breaker", payload["packetRole"])
        outcome = payload["outcome"]
        self.assertEqual("challenges", outcome["result"])
        self.assertEqual(["OBSERVATION_MISMATCH"], outcome["causes"])
        self.assertEqual(30, outcome["requestCount"])
        self.assertEqual(
            {
                "result", "causes", "requestCount", "declarations", "cases",
                "events", "assumptions", "exclusions", "stderrSha256",
                "planCanonicalSha256",
            },
            set(outcome),
        )
        self.assertEqual(
            COMMON_INPUTS["plan"]["canonicalSha256"], outcome["planCanonicalSha256"]
        )
        self.assertEqual(_expected_declarations(breaker=True), outcome["declarations"])
        self.assertEqual(_expected_cases(breaker=True), outcome["cases"])
        self.assertEqual(["adapter-faithfulness", "adapter-event-completeness"], outcome["assumptions"])
        self.assertEqual(["adapter-external-effects", "realization-steps"], outcome["exclusions"])
        self.assertEqual(EMPTY_SHA256, outcome["stderrSha256"])
        self.assertEqual([], outcome["events"])

    def test_cross_root_replay_has_no_checkout_build_or_temporary_path_leak(self) -> None:
        expected = self.checker.reproduce_ordered_map_reports(ROOT)
        with tempfile.TemporaryDirectory(prefix="ordered-map-report-attacks-") as raw:
            copied_a = Path(raw) / "repository-a"
            copied_b = Path(raw) / "repository-b"
            for copied in (copied_a, copied_b):
                shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", ".direnv"))
            self.assertEqual(
                expected,
                self.checker.reproduce_ordered_map_reports(copied_a),
            )
            self.assertEqual(
                expected,
                self.checker.reproduce_ordered_map_reports(copied_b),
            )
            for report in expected.values():
                text = report.decode("utf-8")
                self.assertNotIn(str(ROOT), text)
                self.assertNotIn(str(copied_a), text)
                self.assertNotIn(str(copied_b), text)
                self.assertNotRegex(text, r"/tmp/|/nix/store/")

    def test_stale_bound_inputs_and_forged_report_axes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ordered-map-report-attacks-") as raw:
            copied = Path(raw) / "repository"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", ".direnv"))
            source = copied / "implementations/ordered-map/rust/src/ordered_map.rs"
            source.write_text(source.read_text(encoding="utf-8") + "\n// stale source\n", encoding="utf-8")
            errors, _summary = self.checker.run_ordered_map_report_checks(copied)
        self.assertTrue(any("rust-campaign-report.json" in error for error in errors), errors)

        with tempfile.TemporaryDirectory(prefix="ordered-map-input-drift-") as raw:
            copied = Path(raw) / "repository"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", ".direnv"))
            bound_paths = [
                COMMON_INPUTS["plan"]["path"],
                COMMON_INPUTS["runner"]["path"],
                COMMON_INPUTS["specification"]["path"],
                COMMON_INPUTS["profile"]["path"],
                *(item["path"] for item in COMMON_INPUTS["harness"]),
                *SOURCE_PATHS["ordered-map-rust"],
                *SOURCE_PATHS["ordered-map-typescript"],
                *SOURCE_PATHS["ordered-map-reorder-breaker"],
            ]
            for relative in bound_paths:
                with self.subTest(bound_input=relative):
                    path = copied / relative
                    original_bytes = path.read_bytes()
                    path.write_bytes(original_bytes + b"\n")
                    errors = self.checker.input_binding_errors(copied)
                    self.assertTrue(any(relative in error for error in errors), errors)
                    path.write_bytes(original_bytes)

        fresh = self.checker.reproduce_ordered_map_reports(ROOT)
        mutations = {
            "identity": lambda value: value.update(candidate="forged"),
            "role": lambda value: value.update(packetRole="accepted"),
            "protocol": lambda value: value.update(protocol="forged"),
            "plan": lambda value: value["inputs"]["plan"].update(rawSha256="0" * 64),
            "runner": lambda value: value["inputs"]["runner"].update(sha256="0" * 64),
            "specification": lambda value: value["inputs"]["specification"].update(sha256="0" * 64),
            "profile": lambda value: value["inputs"]["profile"].update(sha256="0" * 64),
            "sources": lambda value: value["inputs"]["sources"].clear(),
            "toolchain": lambda value: value["toolchain"].clear(),
            "commands": lambda value: value["commands"].update(campaign=["$OTHER"]),
            "binary": lambda value: value.update(binarySha256="0" * 64),
            "assumptions": lambda value: value["outcome"]["assumptions"].clear(),
            "exclusions": lambda value: value["outcome"]["exclusions"].clear(),
            "top-result": lambda value: value["outcome"].update(result="forged"),
            "top-causes": lambda value: value["outcome"].update(causes=["FORGED"]),
            "request-count": lambda value: value["outcome"].update(requestCount=29),
            "declaration": lambda value: value["outcome"]["declarations"][0].update(result="challenges"),
            "case": lambda value: value["outcome"]["cases"][0].update(requestCount=99),
            "events": lambda value: value["outcome"]["events"].append({"event": "io.read"}),
            "plan-result": lambda value: value["outcome"].update(planCanonicalSha256="0" * 64),
            "stderr": lambda value: value["outcome"].update(stderrSha256="0" * 64),
            "promotion": lambda value: value.update(reviewState="accepted"),
        }
        with tempfile.TemporaryDirectory(prefix="ordered-map-report-forgeries-") as raw:
            copied = Path(raw) / "repository"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", ".direnv"))
            for report in fresh:
                original = json.loads(fresh[report])
                for name, mutate in mutations.items():
                    with self.subTest(report=report, axis=name):
                        document = json.loads(json.dumps(original))
                        mutate(document)
                        (copied / report).write_bytes(self.checker.canonical_json(document))
                        errors = self.checker.compare_committed_reports(copied, fresh)
                        self.assertTrue(any(report.as_posix() in error for error in errors), errors)
                (copied / report).write_bytes(fresh[report])

    def test_bound_runner_bytes_must_be_the_runner_that_executes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ordered-map-runner-substitution-") as raw:
            copied = Path(raw) / "repository"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", ".direnv"))
            runner = copied / COMMON_INPUTS["runner"]["path"]
            runner.write_bytes(b"THIS IS NOT VALID PYTHON\n" + runner.read_bytes())
            substituted_sha256 = hashlib.sha256(runner.read_bytes()).hexdigest()
            for report in REPORTS.values():
                path = copied / report.relative_to(ROOT)
                document = json.loads(path.read_text(encoding="utf-8"))
                document["inputs"]["runner"]["sha256"] = substituted_sha256
                path.write_bytes(self.checker.canonical_json(document))
            errors, _summary = self.checker.run_ordered_map_report_checks(copied)
        self.assertTrue(
            any("loaded runner bytes differ" in error for error in errors),
            errors,
        )

    def test_runner_identity_survives_post_import_source_mutation(self) -> None:
        program = r'''
import json
from pathlib import Path
from scripts import ordered_map_report_check as checker

root = Path.cwd()
runner = root / checker.RUNNER
runner.write_bytes(b"THIS IS NOT VALID PYTHON\n" + runner.read_bytes())
try:
    fresh = checker.reproduce_ordered_map_reports(root)
except RuntimeError as error:
    errors = [str(error)]
else:
    for path, payload in fresh.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    errors, _summary = checker.run_ordered_map_report_checks(root)
print(json.dumps(errors))
'''
        with tempfile.TemporaryDirectory(prefix="ordered-map-runner-toctou-") as raw:
            copied = Path(raw) / "repository"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", ".direnv"))
            process = subprocess.run(
                (os.fspath(Path(sys.executable)), "-c", program),
                cwd=copied,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
        errors = json.loads(process.stdout)
        self.assertTrue(
            any("loaded runner bytes differ" in error for error in errors),
            errors,
        )

    def test_bound_harness_dependency_bytes_must_match_loaded_closure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ordered-map-harness-substitution-") as raw:
            copied = Path(raw) / "repository"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", ".direnv"))
            relative = "semantic_packages/ordered_map_contract.py"
            dependency = copied / relative
            dependency.write_bytes(b"THIS IS NOT VALID PYTHON\n" + dependency.read_bytes())
            substituted_sha256 = hashlib.sha256(dependency.read_bytes()).hexdigest()
            harness = [dict(item) for item in COMMON_INPUTS["harness"]]
            next(item for item in harness if item["path"] == relative)["sha256"] = (
                substituted_sha256
            )
            for report in REPORTS.values():
                path = copied / report.relative_to(ROOT)
                document = json.loads(path.read_text(encoding="utf-8"))
                document["inputs"]["harness"] = harness
                path.write_bytes(self.checker.canonical_json(document))
            errors, _summary = self.checker.run_ordered_map_report_checks(copied)
        self.assertTrue(
            any("loaded executable closure bytes differ" in error for error in errors),
            errors,
        )

    def test_harness_identity_survives_post_import_dependency_mutation(self) -> None:
        program = r'''
import json
from pathlib import Path
from scripts import ordered_map_report_check as checker

root = Path.cwd()
dependency = root / "semantic_packages/ordered_map_contract.py"
dependency.write_bytes(b"THIS IS NOT VALID PYTHON\n" + dependency.read_bytes())
try:
    fresh = checker.reproduce_ordered_map_reports(root)
except RuntimeError as error:
    errors = [str(error)]
else:
    for path, payload in fresh.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    errors, _summary = checker.run_ordered_map_report_checks(root)
print(json.dumps(errors))
'''
        with tempfile.TemporaryDirectory(prefix="ordered-map-harness-toctou-") as raw:
            copied = Path(raw) / "repository"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", ".direnv"))
            process = subprocess.run(
                (os.fspath(Path(sys.executable)), "-c", program),
                cwd=copied,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
        errors = json.loads(process.stdout)
        self.assertTrue(
            any("loaded executable closure bytes differ" in error for error in errors),
            errors,
        )

    def test_python_closure_rejects_same_size_timestamp_stale_bytecode(self) -> None:
        program = r'''
import json
import os
import sys
from pathlib import Path

root = Path.cwd()
source = root / sys.argv[1]
stat = source.stat()
original = source.read_bytes()
source.write_bytes(b"!" + original[1:])
os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns))
from scripts import ordered_map_report_check as checker
try:
    fresh = checker.reproduce_ordered_map_reports(root)
except RuntimeError as error:
    errors = [str(error)]
else:
    for path, payload in fresh.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    errors, _summary = checker.run_ordered_map_report_checks(root)
print(json.dumps(errors))
'''
        python_closure = (
            "semantic_packages/__init__.py",
            "semantic_packages/ordered_map_runner.py",
            "semantic_packages/ordered_map_contract.py",
            "semantic_packages/canonical_artifact.py",
            "scripts/record_check.py",
        )
        for relative in python_closure:
            with self.subTest(source=relative):
                with tempfile.TemporaryDirectory(
                    prefix="ordered-map-stale-bytecode-"
                ) as raw:
                    copied = Path(raw) / "repository"
                    shutil.copytree(
                        ROOT,
                        copied,
                        ignore=shutil.ignore_patterns(".git", ".direnv"),
                    )
                    process = subprocess.run(
                        (sys.executable, "-c", program, relative),
                        cwd=copied,
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                errors = json.loads(process.stdout)
                self.assertTrue(
                    any(
                        "loaded executable closure bytes differ" in error
                        or "loaded runner bytes differ" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_breaker_report_is_outside_candidate_report_and_registry_membership(self) -> None:
        self.assertTrue(REPORTS["ordered-map-reorder-breaker"].is_relative_to(ROOT / "fixtures"))
        self.assertFalse(REPORTS["ordered-map-reorder-breaker"].is_relative_to(ROOT / "reports"))
        self.assertEqual(
            {"rust-campaign-report.json", "typescript-campaign-report.json"},
            {path.name for path in (ROOT / "reports/ordered-map").glob("*.json")},
        )
        forbidden = (
            "ordered-map-reorder-breaker",
            "fixtures/candidates/ordered-map/reorder_breaker",
            "reorder-breaker-report.json",
        )
        for path in (ROOT / "registry/ordered-map").rglob("*.json"):
            text = path.read_text(encoding="utf-8")
            self.assertFalse([token for token in forbidden if token in text], path)


if __name__ == "__main__":
    unittest.main()
