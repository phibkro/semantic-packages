from __future__ import annotations

import ast
from collections import Counter
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import socket
import shutil
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
DESIGN_SPEC = ROOT / "design-specs/0005-retry-safe-lease-session-package.md"
EXEC_PLAN = ROOT / "docs/exec-plans/completed/0010-retry-safe-lease-session.md"
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
AVAILABLE = {"state": "available"}
HELD = {"state": "held", "holder": "A", "request": "r1", "token": "t1"}
COMPLETED = {"state": "completed"}
EXPIRED = {"state": "expired"}


def _step(index: int, input_value: dict, before: dict, output: dict, after: dict) -> dict:
    return {"index": index, "input": input_value, "before": before, "output": output, "after": after}


ACQUIRE_A = {"op": "acquire", "client": "A", "request": "r1"}
ACQUIRE_B = {"op": "acquire", "client": "B", "request": "r2"}
COMPLETE_T1 = {"op": "complete", "token": "t1"}
EXPECTED_TRACES = {
    "acquire": [
        _step(0, ACQUIRE_A, AVAILABLE, {"status": "granted", "token": "t1"}, HELD),
    ],
    "retry-stability": [
        _step(0, ACQUIRE_A, AVAILABLE, {"status": "granted", "token": "t1"}, HELD),
        _step(1, ACQUIRE_A, HELD, {"status": "granted", "token": "t1"}, HELD),
    ],
    "exclusive-holder": [
        _step(0, ACQUIRE_A, AVAILABLE, {"status": "granted", "token": "t1"}, HELD),
        _step(1, ACQUIRE_B, HELD, {"status": "busy"}, HELD),
    ],
    "wrong-holder-rejection": [
        _step(0, ACQUIRE_A, AVAILABLE, {"status": "granted", "token": "t1"}, HELD),
        _step(1, {"op": "complete", "token": "wrong"}, HELD, {"status": "denied"}, HELD),
    ],
    "completion-closure": [
        _step(0, ACQUIRE_A, AVAILABLE, {"status": "granted", "token": "t1"}, HELD),
        _step(1, COMPLETE_T1, HELD, {"status": "completed"}, COMPLETED),
        _step(2, ACQUIRE_B, COMPLETED, {"status": "terminal", "state": "completed"}, COMPLETED),
        _step(3, {"op": "renew", "token": "t1"}, COMPLETED, {"status": "terminal", "state": "completed"}, COMPLETED),
        _step(4, {"op": "expire"}, COMPLETED, {"status": "terminal", "state": "completed"}, COMPLETED),
        _step(5, COMPLETE_T1, COMPLETED, {"status": "terminal", "state": "completed"}, COMPLETED),
    ],
    "expiry-closure": [
        _step(0, ACQUIRE_A, AVAILABLE, {"status": "granted", "token": "t1"}, HELD),
        _step(1, {"op": "expire"}, HELD, {"status": "expired"}, EXPIRED),
        _step(2, COMPLETE_T1, EXPIRED, {"status": "terminal", "state": "expired"}, EXPIRED),
        _step(3, ACQUIRE_B, EXPIRED, {"status": "terminal", "state": "expired"}, EXPIRED),
        _step(4, {"op": "renew", "token": "t1"}, EXPIRED, {"status": "terminal", "state": "expired"}, EXPIRED),
        _step(5, {"op": "expire"}, EXPIRED, {"status": "terminal", "state": "expired"}, EXPIRED),
    ],
}
PREDECESSOR_SHA256 = {
    "registry/stack/theory/records/stack-spec.json": "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1",
    "registry/ordered-map/theory/records/ordered-map-spec.json": "6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f",
    "specs/persistence-composition.pspec": "9bd4bc52b7c2fb9fe4b7ac8aaa12049e7e94250abb68828bfeef2a6620fba4a1",
    "scripts/record_check.py": "721c590057f568495a20b58adf39c08d25dddeaa896c4f3f825e5a5719a46edd",
}
CANDIDATE_SHA256 = {
    "implementations/lease-session/table/adapter.py": "e467000d68fbb8981107612ba0de98eb555dc21cd233559ac6f42abd91e39138",
    "implementations/lease-session/object/adapter.py": "9877efd1c25eed2a9024e26bb9c23c7aecef46e69df48dca1488253419895635",
    "fixtures/candidates/lease-session/resurrection_breaker.py": "8d278df9c6208d8ea394affff884c23a12322b316a976396ad87c9e2ffbf43ca",
}
GOVERNED_RECORDS = (
    "registry/lease-session/theory/lease-session-profile.json",
    "registry/lease-session/theory/lease-session-spec.json",
    "registry/lease-session/packages/table/lease-session-table-realization.json",
    "registry/lease-session/packages/table/lease-session-table-claim.json",
    "registry/lease-session/packages/table/lease-session-table-evidence.json",
    "registry/lease-session/packages/object/lease-session-object-realization.json",
    "registry/lease-session/packages/object/lease-session-object-claim.json",
    "registry/lease-session/packages/object/lease-session-object-evidence.json",
    "registry/lease-session/consumer/lease-session-policy.json",
)
EXPECTED_ASSUMPTIONS = [
    "Each child adapter faithfully exposes its named realization.",
    "The runner observes every response inside the NDJSON child-process boundary.",
]
EXPECTED_EXCLUSIONS = [
    "No wall-clock timers, scheduling fairness, progress, or liveness claim.",
    "No concurrency, network partition, process crash, durable recovery, or lease-transfer claim.",
    "No token entropy, authenticity, authorization, or other security claim.",
    "No exhaustive-trace or adapter-faithfulness conclusion from the finite campaign.",
    "No protocol refinement, composition, session-type, or arbitrary-domain generality claim.",
    "Opaque identities are observed only by equality in the retained scenarios.",
]
MANIFEST_SHA256 = "ef6b53219e8c404521ade83b446fae006c2daaaa217c032dfb219569f7b0c2a4"
PLAN_SHA256 = "2d1f47896b329c599f11097dbdf4989e724df8a8859864af3b706d8953a4228a"


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
        self.assertEqual([1, 2, 2, 2, 6, 6], [len(EXPECTED_TRACES[item]) for item in SCENARIOS])
        self.assertEqual(19, sum(len(EXPECTED_TRACES[item]) for item in SCENARIOS))

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

    def _mutated_graph(self, address: tuple[str, str, str], mutate) -> object:
        return self._mutated_graph_many({address: mutate})

    def _mutated_graph_many(self, mutations: dict[tuple[str, str, str], object]) -> object:
        from semantic_packages import graph

        authority = graph.inspect_manifest_authority(MANIFEST)
        observation = graph.inspect_manifest_graph(authority)
        self.assertTrue(observation.ok, observation.diagnostics)
        records = []
        for record in observation.records:
            if record.address in mutations:
                document = record.document
                mutations[record.address](document)
                record = replace(
                    record,
                    _document_text=json.dumps(document, sort_keys=True, separators=(",", ":")),
                )
            records.append(record)
        return replace(observation, records=tuple(records))

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
        self.assertEqual(
            {"kind": "specification", "id": "lease-session", "version": "0.1.0"},
            report["specification"],
        )
        self.assertEqual(
            {"manifestRawSha256": MANIFEST_SHA256, "memberCount": 9},
            report["authority"],
        )
        self.assertEqual(PLAN_SHA256, report["campaign"]["planRawSha256"])
        self.assertEqual(18, report["campaign"]["traceCaseCount"])
        self.assertEqual(list(SCENARIOS), report["campaign"]["scenarioOrder"])

    def test_pspec_authors_the_exact_manifest_specification(self) -> None:
        from semantic_packages.authoring import PSPEC_TOML_V1, author_specification

        observation = author_specification(
            SOURCE.read_bytes(),
            PSPEC_TOML_V1,
            "specs/lease-session.pspec",
            (),
        )
        self.assertTrue(observation.ok, observation.diagnostics)
        expected = json.loads(
            (ROOT / "registry/lease-session/theory/lease-session-spec.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(expected, observation.document)

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

    def test_passing_candidates_match_every_exact_frozen_trace_step(self) -> None:
        report = self._report()
        for candidate in report["candidates"][:2]:
            observed = {item["id"]: item["trace"] for item in candidate["scenarios"]}
            self.assertEqual(EXPECTED_TRACES, observed)
        breaker_expiry = report["candidates"][2]["scenarios"][-1]["trace"]
        self.assertEqual(EXPECTED_TRACES["expiry-closure"][:2], breaker_expiry[:2])
        self.assertEqual(COMPLETE_T1, breaker_expiry[2]["input"])
        self.assertEqual(EXPIRED, breaker_expiry[2]["before"])

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
        observed_by_scenario = {item["id"]: item["trace"] for item in breaker["scenarios"]}
        for scenario in SCENARIOS[:5]:
            self.assertEqual(EXPECTED_TRACES[scenario], observed_by_scenario[scenario])
        first_mismatch = next(
            (scenario, index, wanted, actual)
            for scenario in SCENARIOS
            for index, (wanted, actual) in enumerate(
                zip(EXPECTED_TRACES[scenario], observed_by_scenario[scenario], strict=True)
            )
            if wanted != actual
        )
        scenario, mismatch, wanted, actual = first_mismatch
        self.assertEqual(scenario, breaker["counterexample"]["scenario"])
        self.assertEqual(mismatch, breaker["counterexample"]["step"])
        self.assertEqual(wanted["after"]["state"], breaker["counterexample"]["expectedState"])
        self.assertEqual(actual["after"]["state"], breaker["counterexample"]["actualState"])

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
        self.assertEqual(CANDIDATE_SHA256, {path: _sha256(ROOT / path) for path in CANDIDATE_SHA256})
        for relative in tuple(CANDIDATE_SHA256)[:2]:
            tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.add(node.module or "")
            self.assertEqual({"__future__", "json", "sys"}, imports)

    def test_evidence_theory_projection_and_boundaries_remain_separate(self) -> None:
        report = self._report()
        self.assertEqual({"declarations", "packageEvidenceIncluded"}, set(report["theory"]))
        self.assertFalse(report["theory"]["packageEvidenceIncluded"])
        self.assertEqual(["protocol-conformance"], report["theory"]["declarations"])
        for decision in report["decisions"]:
            self.assertEqual("bounded-protocol-campaign", decision["evidence"]["mechanism"])
            self.assertEqual("accepted", decision["evidence"]["reviewState"])
            self.assertEqual("supports", decision["evidence"]["result"])
        self.assertEqual(2, len(report["boundaries"]))
        self.assertEqual(
            [
                {"realization": "lease-session-table", "direction": "consumer->lease-session-table", "mechanism": "ndjson-child-process", "direct": False},
                {"realization": "lease-session-object", "direction": "consumer->lease-session-object", "mechanism": "ndjson-child-process", "direct": False},
            ],
            report["boundaries"],
        )

    def test_evidence_and_policy_negative_axes_fail_closed(self) -> None:
        from semantic_packages.lease_session import inspect_protocol_package

        evidence = ("evidence", "lease-session-table-protocol-campaign", "0.1.0")
        claim = ("claim", "lease-session-table-protocol-conformance", "0.1.0")
        policy = ("consumerPolicy", "lease-session-bounded-policy", "0.1.0")
        valid_attacks = (
            (evidence, lambda value: value.__setitem__("result", "challenges")),
            (evidence, lambda value: value.__setitem__("reviewState", "pending")),
            (evidence, lambda value: value.__setitem__("result", "error")),
            (evidence, lambda value: value.__setitem__("result", "inconclusive")),
            (evidence, lambda value: value.__setitem__("mechanism", "assertion")),
            (evidence, lambda value: value["provenance"]["source"].__setitem__("rawSha256", "0" * 64)),
            (claim, lambda value: value.__setitem__("state", "withdrawn")),
            (policy, lambda value: value["concerns"][0].__setitem__("acceptedMechanisms", [])),
        )
        for address, mutate in valid_attacks:
            observation = self._mutated_graph(address, mutate)
            with mock.patch(
                "semantic_packages.lease_session.graph.inspect_manifest_graph",
                return_value=observation,
            ):
                report, diagnostics, _ = inspect_protocol_package(MANIFEST)
            self.assertFalse(diagnostics)
            self.assertIsNotNone(report)
            self.assertEqual("rejected", report["decisions"][0]["semanticStatus"])

        missing_evidence = self._mutated_graph_many({})
        missing_evidence = replace(
            missing_evidence,
            records=tuple(
                record for record in missing_evidence.records if record.address != evidence
            ),
        )
        with mock.patch(
            "semantic_packages.lease_session.graph.inspect_manifest_graph",
            return_value=missing_evidence,
        ):
            report, diagnostics, _ = inspect_protocol_package(MANIFEST)
        self.assertIsNone(report)
        self.assertEqual(["PROTOCOL_EVIDENCE_COUNT"], [item.code for item in diagnostics])
        inapplicable = self._mutated_graph_many(
            {
                claim: lambda value: value.__setitem__("applicableProfiles", []),
                evidence: lambda value: value["applicability"].__setitem__("profiles", []),
            }
        )
        with mock.patch(
            "semantic_packages.lease_session.graph.inspect_manifest_graph",
            return_value=inapplicable,
        ):
            report, diagnostics, _ = inspect_protocol_package(MANIFEST)
        self.assertFalse(diagnostics)
        self.assertEqual("rejected", report["decisions"][0]["semanticStatus"])

        invalid_attacks = (
            ("schema", evidence, lambda value: value.__setitem__("reviewState", "draft")),
            ("link", evidence, lambda value: value["adapter"].__setitem__("id", "wrong")),
            ("link", evidence, lambda value: value["applicability"].__setitem__("profiles", [])),
        )
        from scripts import record_check
        schemas = record_check.SchemaRegistry()
        for phase, address, mutate in invalid_attacks:
            observation = self._mutated_graph(address, mutate)
            documents = {record.path: record.document for record in observation.records}
            schema_problems = tuple(
                problem
                for path, document in documents.items()
                if (problem := record_check.validate_record(schemas, path, document)) is not None
            )
            if phase == "schema":
                self.assertTrue(schema_problems, address)
                self.assertTrue(all(problem.code.startswith("SCHEMA_") for problem in schema_problems))
            else:
                self.assertFalse(schema_problems)
                link_problems = record_check.check_graph(documents)
                self.assertTrue(link_problems, address)
                self.assertTrue(all(problem.code.startswith("LINK_") for problem in link_problems))

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
        unknown_input = json.loads(json.dumps(document))
        unknown_input["protocols"][0]["transitions"][0]["input"] = "missing"
        mutations.append((unknown_input, "PROTOCOL_UNKNOWN_INPUT"))
        unknown_output = json.loads(json.dumps(document))
        unknown_output["protocols"][0]["transitions"][0]["output"] = "missing"
        mutations.append((unknown_output, "PROTOCOL_UNKNOWN_OUTPUT"))
        duplicate_transition = json.loads(json.dumps(document))
        duplicate_transition["protocols"][0]["transitions"].append(
            dict(duplicate_transition["protocols"][0]["transitions"][0])
        )
        mutations.append((duplicate_transition, "PROTOCOL_DUPLICATE_TRANSITION"))
        duplicate_input = json.loads(json.dumps(document))
        duplicate_input["protocols"][0]["inputs"].append("acquire-new")
        mutations.append((duplicate_input, "PROTOCOL_DUPLICATE_INPUT"))
        duplicate_output = json.loads(json.dumps(document))
        duplicate_output["protocols"][0]["outputs"].append("granted")
        mutations.append((duplicate_output, "PROTOCOL_DUPLICATE_OUTPUT"))
        duplicate_declaration = json.loads(json.dumps(document))
        duplicate_declaration["protocols"][0]["id"] = "acquire"
        mutations.append((duplicate_declaration, "PROTOCOL_DUPLICATE_DECLARATION"))
        for attacked, code in mutations:
            observation = inspect_protocol_document(attacked)
            self.assertFalse(observation.ok)
            self.assertEqual(code, observation.diagnostics[0].code)
            self.assertTrue(observation.diagnostics[0].pointer.startswith("#/"))

    def test_protocol_less_predecessor_and_authoring_phase_order_remain_valid(self) -> None:
        from semantic_packages.authoring import AuthoringDependency, CANONICAL_SPEC_JSON_V1, PSPEC_TOML_V1, author_specification

        stack = ROOT / "registry/stack/theory/records/stack-spec.json"
        profile = ROOT / "registry/stack/theory/dependencies/stack-profile.json"
        accepted = author_specification(
            stack.read_bytes(),
            CANONICAL_SPEC_JSON_V1,
            str(stack),
            (AuthoringDependency(str(profile), json.loads(profile.read_text(encoding="utf-8"))),),
        )
        self.assertTrue(accepted.ok, accepted.diagnostics)
        raw = author_specification(b"kind = \"specification\"\nkind = \"again\"\n", PSPEC_TOML_V1, "duplicate.pspec", ())
        self.assertFalse(raw.ok)
        self.assertEqual("AUTHOR_INVALID_TOML", raw.diagnostics[0].code)
        schema = author_specification(b"kind = \"specification\"\nid = \"x\"\nversion = \"1\"\nprotocols = \"bad\"\n", PSPEC_TOML_V1, "schema.pspec", ())
        self.assertFalse(schema.ok)
        self.assertTrue(schema.diagnostics[0].code.startswith("SCHEMA_"))

        link_document = json.loads(
            (ROOT / "registry/lease-session/theory/lease-session-spec.json").read_text(
                encoding="utf-8"
            )
        )
        link_document["imports"] = [
            {"kind": "specification", "id": "missing", "version": "0.1.0"}
        ]
        link = author_specification(
            json.dumps(link_document).encode(),
            CANONICAL_SPEC_JSON_V1,
            "link.json",
            (),
        )
        self.assertFalse(link.ok)
        self.assertTrue(link.diagnostics[0].code.startswith("LINK_"))

        malformed_protocol = SOURCE.read_text(encoding="utf-8").replace(
            'initialState = "available"', 'initialState = "completed"', 1
        )
        protocol = author_specification(
            malformed_protocol.encode(),
            PSPEC_TOML_V1,
            "malformed-protocol.pspec",
            (),
        )
        self.assertFalse(protocol.ok)
        self.assertEqual("PROTOCOL_INITIAL_TERMINAL", protocol.diagnostics[0].code)
        self.assertEqual("malformed-protocol.pspec", protocol.diagnostics[0].path)
        self.assertEqual("#/protocols/0/initialState", protocol.diagnostics[0].pointer)

    def test_output_alias_and_failure_preserve_governed_inputs(self) -> None:
        from semantic_packages.lease_session import inspect_protocol_package, run_protocol_inspection

        before = MANIFEST.read_bytes()
        result = self._run(MANIFEST)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("PROTOCOL_OUTPUT_ALIAS", result.stderr)
        self.assertEqual(before, MANIFEST.read_bytes())
        plan = ROOT / "contracts/lease-session/campaign-plan.json"
        plan_before = plan.read_bytes()
        plan_result = self._run(plan)
        self.assertNotEqual(0, plan_result.returncode)
        self.assertIn("PROTOCOL_OUTPUT_ALIAS", plan_result.stderr)
        self.assertEqual(plan_before, plan.read_bytes())
        report, diagnostics, governed = inspect_protocol_package(MANIFEST)
        self.assertFalse(diagnostics)
        accepted_report = report
        expected_governed = {
            MANIFEST,
            *(ROOT / path for path in GOVERNED_RECORDS),
            ROOT / "contracts/lease-session/campaign-plan.json",
            *(ROOT / path for path in CANDIDATE_SHA256),
        }
        self.assertEqual({path.resolve() for path in expected_governed}, {path.resolve() for path in governed})
        snapshots = {path.resolve(): path.read_bytes() for path in governed}
        with tempfile.TemporaryDirectory(prefix="lease-session-snapshot-") as directory:
            self.assertEqual(0, self._run(Path(directory) / "report.json").returncode)
        self.assertEqual(snapshots, {path.resolve(): path.read_bytes() for path in governed})
        for governed_path in governed:
            with mock.patch(
                "semantic_packages.lease_session.inspect_protocol_package",
                return_value=(report, (), governed),
            ):
                self.assertEqual(1, run_protocol_inspection(MANIFEST, governed_path))
        with tempfile.TemporaryDirectory(prefix="lease-session-preserve-") as directory:
            output = Path(directory) / "report.json"
            self.assertEqual(0, self._run(output).returncode)
            accepted = output.read_bytes()
            with mock.patch(
                "semantic_packages.lease_session.inspect_protocol_package",
                return_value=(None, (type("D", (), {"code": "PROTOCOL_TEST_FAILURE", "path": "<test>", "pointer": "#", "message": "forced"})(),), ()),
            ):
                self.assertEqual(1, run_protocol_inspection(MANIFEST, output))
            self.assertEqual(accepted, output.read_bytes())

        with tempfile.TemporaryDirectory(prefix="lease-session-unexpected-") as directory:
            copied_registry = Path(directory) / "lease-session"
            shutil.copytree(ROOT / "registry/lease-session", copied_registry)
            rogue = copied_registry / "theory/rogue.json"
            rogue.write_text(
                json.dumps(
                    {
                        "kind": "specification",
                        "id": "rogue",
                        "version": "0.1.0",
                        "laws": [{"id": "rogue", "statement": "not governed"}],
                    }
                ),
                encoding="utf-8",
            )
            report, diagnostics, _ = inspect_protocol_package(
                copied_registry / "manifest.json"
            )
            self.assertIsNone(report)
            self.assertIn("GRAPH_UNEXPECTED_MEMBER", [item.code for item in diagnostics])

        with tempfile.TemporaryDirectory(prefix="lease-session-alias-") as directory:
            alias_root = Path(directory)
            target = ROOT / GOVERNED_RECORDS[0]
            (alias_root / "nested").mkdir()
            normalized = alias_root / "nested" / ".." / "normalized.json"
            normalized_target = alias_root / "normalized.json"
            os.link(target, normalized_target)
            symlink = alias_root / "symlink.json"
            symlink.symlink_to(target)
            hardlink = alias_root / "hardlink.json"
            os.link(target, hardlink)
            target_before = target.read_bytes()
            for alias in (normalized, symlink, hardlink):
                with mock.patch(
                    "semantic_packages.lease_session.inspect_protocol_package",
                    return_value=(accepted_report, (), governed),
                ):
                    self.assertEqual(1, run_protocol_inspection(MANIFEST, alias))
            self.assertEqual(target_before, target.read_bytes())

    def test_acquisition_and_execution_are_exactly_allowlisted(self) -> None:
        from semantic_packages import lease_session

        calls = []
        original = lease_session.subprocess.run

        def tracked(command, *args, **kwargs):
            calls.append(tuple(command))
            return original(command, *args, **kwargs)

        with (
            mock.patch("semantic_packages.lease_session.subprocess.run", side_effect=tracked),
            mock.patch.object(Path, "glob", side_effect=AssertionError("glob discovery forbidden")),
            mock.patch.object(Path, "rglob", side_effect=AssertionError("rglob discovery forbidden")),
            mock.patch.object(Path, "iterdir", side_effect=AssertionError("directory discovery forbidden")),
            mock.patch.object(socket, "socket", side_effect=AssertionError("network access forbidden")),
        ):
            report, diagnostics, _ = lease_session.inspect_protocol_package(MANIFEST)
        self.assertFalse(diagnostics)
        self.assertIsNotNone(report)
        expected_commands = Counter(
            (sys.executable, os.fspath((ROOT / path).resolve()))
            for path in CANDIDATE_SHA256
            for _ in SCENARIOS
        )
        self.assertEqual(expected_commands, Counter(calls))
        self.assertTrue(all(len(command) == 2 for command in calls))

    def test_nonauthority_language_and_predecessor_regressions(self) -> None:
        report = self._report()
        language = json.dumps(report, sort_keys=True).casefold()
        for forbidden in (
            "real-time guarantee",
            "liveness proved",
            "universal session type",
            "arbitrary-domain generality established",
        ):
            self.assertNotIn(forbidden, language)
        self.assertEqual(EXPECTED_ASSUMPTIONS, report["assumptions"])
        self.assertEqual(EXPECTED_EXCLUSIONS, report["exclusions"])
        self.assertEqual({"manifestRawSha256", "memberCount"}, set(report["authority"]))
        self.assertEqual({"planRawSha256", "scenarioOrder", "traceCaseCount"}, set(report["campaign"]))
        for candidate in report["candidates"]:
            expected_keys = {"id", "registered", "representation", "sources", "result", "scenarios"}
            if candidate["result"] == "challenges":
                expected_keys.add("counterexample")
            self.assertEqual(expected_keys, set(candidate))
            expected_candidate = {
                "lease-session-table": (
                    True,
                    "table-oriented mutable record",
                    ["implementations/lease-session/table/adapter.py"],
                    "supports",
                ),
                "lease-session-object": (
                    True,
                    "object-oriented branch state",
                    ["implementations/lease-session/object/adapter.py"],
                    "supports",
                ),
                "lease-session-resurrection-breaker": (
                    False,
                    "negative branch-state fixture",
                    ["fixtures/candidates/lease-session/resurrection_breaker.py"],
                    "challenges",
                ),
            }[candidate["id"]]
            self.assertEqual(
                expected_candidate,
                (
                    candidate["registered"],
                    candidate["representation"],
                    candidate["sources"],
                    candidate["result"],
                ),
            )
            for scenario in candidate["scenarios"]:
                self.assertEqual({"id", "result", "trace"}, set(scenario))
            expected_results = ["supports"] * 6
            if candidate["id"] == "lease-session-resurrection-breaker":
                expected_results[-1] = "challenges"
            self.assertEqual(
                expected_results,
                [scenario["result"] for scenario in candidate["scenarios"]],
            )
        for decision in report["decisions"]:
            self.assertEqual({"realization", "semanticStatus", "evidence"}, set(decision))
            self.assertEqual({"id", "mechanism", "result", "reviewState"}, set(decision["evidence"]))
            realization_id = decision["realization"]["id"]
            self.assertEqual(
                f"{realization_id}-protocol-campaign", decision["evidence"]["id"]
            )
        self.assertEqual(
            PREDECESSOR_SHA256,
            {relative: _sha256(ROOT / relative) for relative in PREDECESSOR_SHA256},
        )


if __name__ == "__main__":
    unittest.main()
