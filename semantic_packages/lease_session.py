"""Bounded third-domain lease-session package inspection."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts import record_check
from semantic_packages import graph


ROOT = Path(__file__).resolve().parents[1]
SPECIFICATION = ("specification", "lease-session", "0.1.0")
PROFILE = ("realizationProfile", "lease-session-local-process", "0.1.0")
POLICY = ("consumerPolicy", "lease-session-bounded-policy", "0.1.0")
SCENARIOS = (
    "acquire",
    "retry-stability",
    "exclusive-holder",
    "wrong-holder-rejection",
    "completion-closure",
    "expiry-closure",
)


@dataclass(frozen=True)
class ProtocolDocumentObservation:
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def _diagnostic(code: str, path: str = "<lease-session>", pointer: str = "#", message: str | None = None) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, path, pointer, message)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_protocol_document(document: Mapping[str, Any]) -> ProtocolDocumentObservation:
    protocols = document.get("protocols")
    if not isinstance(protocols, list) or len(protocols) != 1 or not isinstance(protocols[0], dict):
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_REQUIRED", pointer="#/protocols"),))
    protocol = protocols[0]
    declarations: dict[str, str] = {}
    for field in ("carriers", "operations", "observations", "derivedObservations", "equivalences", "laws", "resources", "performancePropositions", "protocols"):
        values = document.get(field, ())
        if not isinstance(values, list):
            continue
        for index, value in enumerate(values):
            if not isinstance(value, dict) or not isinstance(value.get("id"), str):
                continue
            identifier = value["id"]
            if identifier in declarations:
                return ProtocolDocumentObservation((_diagnostic("PROTOCOL_DUPLICATE_DECLARATION", pointer=f"#/{field}/{index}/id"),))
            declarations[identifier] = f"#/{field}/{index}/id"
    effect = document.get("effects")
    if isinstance(effect, dict) and isinstance(effect.get("id"), str):
        if effect["id"] in declarations:
            return ProtocolDocumentObservation((_diagnostic("PROTOCOL_DUPLICATE_DECLARATION", pointer="#/effects/id"),))
    states = protocol.get("states")
    if not isinstance(states, list) or not all(isinstance(item, str) for item in states):
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_STATES", pointer="#/protocols/0/states"),))
    if len(states) != len(set(states)):
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_DUPLICATE_STATE", pointer="#/protocols/0/states"),))
    state_set = set(states)
    initial = protocol.get("initialState")
    terminals = protocol.get("terminalStates")
    if initial not in state_set:
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_UNKNOWN_STATE", pointer="#/protocols/0/initialState"),))
    if not isinstance(terminals, list) or any(item not in state_set for item in terminals):
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_UNKNOWN_STATE", pointer="#/protocols/0/terminalStates"),))
    if initial in terminals:
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_INITIAL_TERMINAL", pointer="#/protocols/0/initialState"),))
    input_values = protocol.get("inputs", ())
    output_values = protocol.get("outputs", ())
    if not isinstance(input_values, list) or len(input_values) != len(set(input_values)):
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_DUPLICATE_INPUT", pointer="#/protocols/0/inputs"),))
    if not isinstance(output_values, list) or len(output_values) != len(set(output_values)):
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_DUPLICATE_OUTPUT", pointer="#/protocols/0/outputs"),))
    inputs = set(input_values)
    outputs = set(output_values)
    transitions = protocol.get("transitions")
    if not isinstance(transitions, list):
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_TRANSITIONS", pointer="#/protocols/0/transitions"),))
    keys: set[tuple[str, str]] = set()
    reachable = {initial}
    changed = True
    for index, transition in enumerate(transitions):
        pointer = f"#/protocols/0/transitions/{index}"
        if not isinstance(transition, dict):
            return ProtocolDocumentObservation((_diagnostic("PROTOCOL_TRANSITION", pointer=pointer),))
        source, target = transition.get("from"), transition.get("to")
        if source not in state_set or target not in state_set:
            return ProtocolDocumentObservation((_diagnostic("PROTOCOL_UNKNOWN_STATE", pointer=pointer),))
        if transition.get("input") not in inputs:
            return ProtocolDocumentObservation((_diagnostic("PROTOCOL_UNKNOWN_INPUT", pointer=pointer),))
        if transition.get("output") not in outputs:
            return ProtocolDocumentObservation((_diagnostic("PROTOCOL_UNKNOWN_OUTPUT", pointer=pointer),))
        key = (source, transition["input"])
        if key in keys:
            return ProtocolDocumentObservation((_diagnostic("PROTOCOL_DUPLICATE_TRANSITION", pointer=pointer),))
        keys.add(key)
    while changed:
        changed = False
        for transition in transitions:
            if transition["from"] in reachable and transition["to"] not in reachable:
                reachable.add(transition["to"])
                changed = True
    if reachable != state_set:
        return ProtocolDocumentObservation((_diagnostic("PROTOCOL_UNREACHABLE_STATE", pointer="#/protocols/0/states"),))
    return ProtocolDocumentObservation(())


def _expected_step(state: dict[str, Any], message: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    phase = state["state"]
    operation = message["op"]
    if phase in {"completed", "expired"}:
        return {"status": "terminal", "state": phase}, dict(state)
    if phase == "available":
        if operation != "acquire":
            return {"status": "denied"}, dict(state)
        next_state = {"state": "held", "holder": message["client"], "request": message["request"], "token": "t1"}
        return {"status": "granted", "token": "t1"}, next_state
    if operation == "acquire":
        if message.get("client") == state["holder"] and message.get("request") == state["request"]:
            return {"status": "granted", "token": state["token"]}, dict(state)
        return {"status": "busy"}, dict(state)
    if operation == "renew":
        return ({"status": "renewed"} if message.get("token") == state["token"] else {"status": "denied"}), dict(state)
    if operation == "complete":
        if message.get("token") != state["token"]:
            return {"status": "denied"}, dict(state)
        return {"status": "completed"}, {"state": "completed"}
    if operation == "expire":
        return {"status": "expired"}, {"state": "expired"}
    return {"status": "denied"}, dict(state)


def _run_scenario(entrypoint: Path, inputs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]] | None, str | None]:
    payload = "".join(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n" for item in inputs)
    try:
        result = subprocess.run([sys.executable, os.fspath(entrypoint)], input=payload, text=True, capture_output=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        return None, f"candidate execution failed: {error}"
    if result.returncode != 0:
        return None, f"candidate exited {result.returncode}"
    lines = result.stdout.splitlines()
    if len(lines) != len(inputs):
        return None, f"candidate returned {len(lines)} responses for {len(inputs)} inputs"
    state: dict[str, Any] = {"state": "available"}
    trace: list[dict[str, Any]] = []
    for index, (message, raw) in enumerate(zip(inputs, lines, strict=True)):
        try:
            response = json.loads(raw)
        except json.JSONDecodeError:
            return None, f"candidate response {index} is not JSON"
        if not isinstance(response, dict) or set(response) != {"output", "state"}:
            return None, f"candidate response {index} has the wrong shape"
        trace.append({"index": index, "input": message, "before": state, "output": response["output"], "after": response["state"]})
        state = response["state"]
    return trace, None


def _evaluate_trace(inputs: list[dict[str, Any]], trace: list[dict[str, Any]]) -> dict[str, Any] | None:
    state: dict[str, Any] = {"state": "available"}
    for index, (message, step) in enumerate(zip(inputs, trace, strict=True)):
        expected_output, expected_state = _expected_step(state, message)
        if step["before"] != state or step["input"] != message or step["output"] != expected_output or step["after"] != expected_state:
            return {"step": index, "expectedOutput": expected_output, "actualOutput": step["output"], "expectedState": expected_state["state"], "actualState": step["after"].get("state")}
        state = expected_state
    return None


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def inspect_protocol_package(manifest_path: Path) -> tuple[dict[str, Any] | None, tuple[record_check.Diagnostic, ...], tuple[Path, ...]]:
    authority = graph.inspect_manifest_authority(manifest_path)
    observation = graph.inspect_manifest_graph(authority)
    if not observation.ok:
        return None, observation.diagnostics, (manifest_path,)
    documents = {record.address: record.document for record in observation.records}
    source_roots = {item.source_id: item.root for item in authority.sources}
    member_paths = tuple(
        authority.manifest_path.parent
        / source_roots[record.source]
        / record.path.split("/", 1)[-1]
        for record in observation.records
    )
    required = (SPECIFICATION, PROFILE, POLICY, ("realization", "lease-session-table", "0.1.0"), ("realization", "lease-session-object", "0.1.0"))
    missing = [address for address in required if address not in documents]
    if missing:
        return None, (_diagnostic("PROTOCOL_REQUIRED_RECORD", message=repr(missing[0])),), (manifest_path, *member_paths)
    specification = documents[SPECIFICATION]
    structural = inspect_protocol_document(specification)
    if not structural.ok:
        return None, structural.diagnostics, (manifest_path, *member_paths)
    evidences = [document for address, document in documents.items() if address[0] == "evidence"]
    if len(evidences) != 2:
        return None, (_diagnostic("PROTOCOL_EVIDENCE_COUNT"),), (manifest_path, *member_paths)
    plan_values = {item.get("provenance", {}).get("plan", {}).get("path") for item in evidences}
    plan_hashes = {item.get("provenance", {}).get("plan", {}).get("rawSha256") for item in evidences}
    if len(plan_values) != 1 or len(plan_hashes) != 1 or None in plan_values or None in plan_hashes:
        return None, (_diagnostic("PROTOCOL_PLAN_BINDING"),), (manifest_path, *member_paths)
    plan_path = ROOT / next(iter(plan_values))
    expected_plan_hash = next(iter(plan_hashes))
    try:
        if _sha256(plan_path) != expected_plan_hash:
            return None, (_diagnostic("PROTOCOL_PLAN_DIGEST", os.fspath(plan_path)),), (manifest_path, *member_paths, plan_path)
        plan = _load_json(plan_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, (_diagnostic("PROTOCOL_PLAN_READ", os.fspath(plan_path), message=str(error)),), (manifest_path, *member_paths, plan_path)
    if [item.get("id") for item in plan.get("scenarios", [])] != list(SCENARIOS):
        return None, (_diagnostic("PROTOCOL_SCENARIO_ORDER", os.fspath(plan_path)),), (manifest_path, *member_paths, plan_path)
    if [item.get("id") for item in plan.get("candidates", [])] != ["lease-session-table", "lease-session-object", "lease-session-resurrection-breaker"]:
        return None, (_diagnostic("PROTOCOL_CANDIDATE_ORDER", os.fspath(plan_path)),), (manifest_path, *member_paths, plan_path)
    candidate_results: list[dict[str, Any]] = []
    governed: list[Path] = [manifest_path, *member_paths, plan_path]
    for candidate in plan.get("candidates", []):
        source = ROOT / candidate["entrypoint"]
        governed.append(source)
        try:
            if _sha256(source) != candidate["sha256"]:
                return None, (_diagnostic("PROTOCOL_SOURCE_DIGEST", os.fspath(source)),), tuple(governed)
        except OSError as error:
            return None, (_diagnostic("PROTOCOL_SOURCE_READ", os.fspath(source), message=str(error)),), tuple(governed)
        scenario_results: list[dict[str, Any]] = []
        first_counterexample: dict[str, Any] | None = None
        for scenario in plan["scenarios"]:
            trace, problem = _run_scenario(source, scenario["inputs"])
            if problem is not None or trace is None:
                return None, (_diagnostic("PROTOCOL_CANDIDATE_EXECUTION", os.fspath(source), message=problem),), tuple(governed)
            mismatch = _evaluate_trace(scenario["inputs"], trace)
            scenario_results.append({"id": scenario["id"], "result": "supports" if mismatch is None else "challenges", "trace": trace})
            if mismatch is not None and first_counterexample is None:
                first_counterexample = {"scenario": scenario["id"], **mismatch}
        result = "supports" if first_counterexample is None else "challenges"
        item = {"id": candidate["id"], "registered": candidate["registered"], "representation": candidate["representation"], "sources": [candidate["entrypoint"]], "result": result, "scenarios": scenario_results}
        if first_counterexample is not None:
            item["counterexample"] = first_counterexample
        candidate_results.append(item)
    by_id = {item["id"]: item for item in candidate_results}
    plan_candidates = {item["id"]: item for item in plan["candidates"]}
    policy = documents[POLICY]
    policy_concerns = policy.get("concerns")
    policy_complete = (
        policy.get("specification") == {"kind": "specification", "id": "lease-session", "version": "0.1.0"}
        and policy.get("profile") == {"kind": "realizationProfile", "id": "lease-session-local-process", "version": "0.1.0"}
        and isinstance(policy_concerns, list)
        and len(policy_concerns) == 1
        and policy_concerns[0].get("concern") == "protocol.conformance"
        and policy_concerns[0].get("priority") == "required"
        and policy_concerns[0].get("acceptedMechanisms") == ["bounded-protocol-campaign"]
        and policy_concerns[0].get("minimumAssurance") == "one-accepted-applicable-support-no-selected-challenge"
    )
    decisions: list[dict[str, Any]] = []
    boundaries: list[dict[str, Any]] = []
    for realization_id in ("lease-session-table", "lease-session-object"):
        realization_address = ("realization", realization_id, "0.1.0")
        claim_id = f"{realization_id}-protocol-conformance"
        evidence_id = f"{realization_id}-protocol-campaign"
        claim = documents.get(("claim", claim_id, "0.1.0"), {})
        evidence = documents.get(("evidence", evidence_id, "0.1.0"), {})
        realization = documents.get(realization_address, {})
        candidate_plan = plan_candidates[realization_id]
        expected_profile = {"kind": "realizationProfile", "id": "lease-session-local-process", "version": "0.1.0"}
        expected_specification = {"kind": "specification", "id": "lease-session", "version": "0.1.0"}
        expected_realization = {"kind": "realization", "id": realization_id, "version": "0.1.0"}
        expected_claim = {"kind": "claim", "id": claim_id, "version": "0.1.0"}
        expected_adapter = realization.get("adapter", {})
        provenance = evidence.get("provenance", {})
        accepted = (
            by_id[realization_id]["result"] == "supports"
            and policy_complete
            and realization.get("specification") == expected_specification
            and realization.get("supportedProfiles") == [expected_profile]
            and claim.get("concern") == "protocol.conformance"
            and claim.get("subject") == expected_realization
            and claim.get("governingSpecification") == expected_specification
            and claim.get("proposition") == {"specification": expected_specification, "declarationId": "protocol-conformance"}
            and claim.get("applicableProfiles") == [expected_profile]
            and claim.get("state") == "active"
            and evidence.get("claim") == expected_claim
            and evidence.get("specification") == expected_specification
            and evidence.get("scope") == "realization"
            and evidence.get("realization") == expected_realization
            and evidence.get("adapter") == {"id": expected_adapter.get("id"), "version": expected_adapter.get("version")}
            and evidence.get("mechanism") == "bounded-protocol-campaign"
            and evidence.get("result") == "supports"
            and evidence.get("reviewState") == "accepted"
            and evidence.get("applicability", {}).get("profiles") == [expected_profile]
            and isinstance(evidence.get("freshness", {}).get("producedAt"), str)
            and provenance.get("plan") == {"path": next(iter(plan_values)), "rawSha256": expected_plan_hash}
            and provenance.get("source") == {"path": candidate_plan["entrypoint"], "rawSha256": candidate_plan["sha256"]}
            and provenance.get("scenarioOrder") == list(SCENARIOS)
        )
        decisions.append({"realization": {"kind": "realization", "id": realization_id, "version": "0.1.0"}, "semanticStatus": "acceptable" if accepted else "rejected", "evidence": {"id": evidence_id, "mechanism": evidence.get("mechanism"), "result": evidence.get("result"), "reviewState": evidence.get("reviewState")}})
        boundaries.append({"realization": realization_id, "direction": f"consumer->{realization_id}", "mechanism": "ndjson-child-process", "direct": False})
    report = {
        "kind": "protocol-package-inspection-v1",
        "specification": {"kind": "specification", "id": "lease-session", "version": "0.1.0"},
        "authority": {"manifestRawSha256": _sha256(manifest_path), "memberCount": len(authority.members)},
        "campaign": {"planRawSha256": expected_plan_hash, "scenarioOrder": list(SCENARIOS), "traceCaseCount": len(SCENARIOS) * len(candidate_results)},
        "candidates": candidate_results,
        "decisions": decisions,
        "theory": {"declarations": [item["id"] for item in specification.get("laws", [])], "packageEvidenceIncluded": False},
        "boundaries": boundaries,
        "assumptions": plan["assumptions"],
        "exclusions": plan["exclusions"],
        "conclusion": "bounded-protocol-package-observed",
    }
    return report, (), tuple(governed)


def _aliases(left: Path, right: Path) -> bool:
    if left.resolve(strict=False) == right.resolve(strict=False):
        return True
    try:
        return left.exists() and right.exists() and os.path.samefile(left, right)
    except OSError:
        return False


def _write_atomically(path: Path, report: dict[str, Any]) -> record_check.Diagnostic | None:
    temporary: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            temporary = stream.name
            json.dump(report, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as error:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        return _diagnostic("PROTOCOL_OUTPUT_WRITE", os.fspath(path), message=str(error))
    return None


def run_protocol_inspection(manifest_path: Path, output_path: Path) -> int:
    if _aliases(manifest_path, output_path):
        print(f"PROTOCOL_OUTPUT_ALIAS {output_path}#: output aliases governed manifest", file=sys.stderr)
        return 1
    report, diagnostics, governed = inspect_protocol_package(manifest_path)
    if diagnostics:
        for diagnostic in diagnostics:
            print(f"{diagnostic.code} {diagnostic.path}{diagnostic.pointer}: {diagnostic.message or 'protocol inspection failed'}", file=sys.stderr)
        return 1
    assert report is not None
    for path in governed:
        if _aliases(path, output_path):
            print(f"PROTOCOL_OUTPUT_ALIAS {output_path}#: output aliases governed input {path}", file=sys.stderr)
            return 1
    diagnostic = _write_atomically(output_path, report)
    if diagnostic is not None:
        print(f"{diagnostic.code} {diagnostic.path}{diagnostic.pointer}: {diagnostic.message}", file=sys.stderr)
        return 1
    print(
        "inspected lease-session 0.1.0: 2 registered realizations accepted, "
        "1 breaker challenged across 18 trace cases; boundary=directional; "
        f"satisfaction=policy-relative -> {output_path}"
    )
    return 0
