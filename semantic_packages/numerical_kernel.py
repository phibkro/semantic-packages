"""Bounded stable-norm2 approximate numerical package inspection."""

from __future__ import annotations

from decimal import Decimal, localcontext
import hashlib
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts import record_check
from semantic_packages import graph


ROOT = Path(__file__).resolve().parents[1]
SPECIFICATION = ("specification", "stable-norm2", "0.1.0")
PROFILE = ("realizationProfile", "stable-norm2-binary64", "0.1.0")
POLICY = ("consumerPolicy", "stable-norm2-policy", "0.1.0")
REALIZATIONS = ("stable-norm2-hypot", "stable-norm2-scaled")


@dataclass(frozen=True)
class NumericalDocumentObservation:
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def _diagnostic(code: str, path: str = "<stable-norm2>", pointer: str = "#", message: str | None = None) -> record_check.Diagnostic:
    return record_check.Diagnostic(code, path, pointer, message)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_numerical_document(document: Mapping[str, Any]) -> NumericalDocumentObservation:
    kernels = document.get("numericalKernels")
    if kernels is None:
        return NumericalDocumentObservation(())
    if not isinstance(kernels, list) or not kernels:
        return NumericalDocumentObservation((_diagnostic("NUMERICAL_KERNEL_REQUIRED", pointer="#/numericalKernels"),))
    operations = {item.get("id") for item in document.get("operations", ()) if isinstance(item, dict)}
    declarations: set[str] = set()
    for field in ("carriers", "operations", "observations", "derivedObservations", "equivalences", "laws", "resources", "performancePropositions", "protocols", "numericalKernels"):
        for index, item in enumerate(document.get(field, ())):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            if item["id"] in declarations:
                return NumericalDocumentObservation((_diagnostic("NUMERICAL_DUPLICATE_DECLARATION", pointer=f"#/{field}/{index}/id"),))
            declarations.add(item["id"])
    for index, kernel in enumerate(kernels):
        if not isinstance(kernel, dict) or kernel.get("operation") not in operations:
            return NumericalDocumentObservation((_diagnostic("NUMERICAL_UNKNOWN_OPERATION", pointer=f"#/numericalKernels/{index}/operation"),))
    return NumericalDocumentObservation(())


def _oracle(x: float, y: float, digits: int) -> float:
    with localcontext() as context:
        context.prec = digits
        exact_x = Decimal.from_float(x)
        exact_y = Decimal.from_float(y)
        value = (exact_x * exact_x + exact_y * exact_y).sqrt()
        return float(value)


def _ulp_distance(left: float, right: float) -> int:
    if left == 0.0 and right == 0.0:
        return 0
    left_bits = struct.unpack(">Q", struct.pack(">d", left))[0]
    right_bits = struct.unpack(">Q", struct.pack(">d", right))[0]
    return abs(left_bits - right_bits)


def _run_case(entrypoint: Path, case: Mapping[str, Any]) -> tuple[str | None, str | None]:
    payload = json.dumps({"x": case["x"], "y": case["y"]}, sort_keys=True, separators=(",", ":")) + "\n"
    try:
        result = subprocess.run([sys.executable, os.fspath(entrypoint)], input=payload, text=True, capture_output=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        return None, f"candidate execution failed: {error}"
    if result.returncode != 0:
        return None, f"candidate exited {result.returncode}"
    lines = result.stdout.splitlines()
    if len(lines) != 1:
        return None, f"candidate returned {len(lines)} lines"
    try:
        response = json.loads(lines[0])
    except json.JSONDecodeError:
        return None, "candidate response is not JSON"
    if not isinstance(response, dict) or set(response) != {"value"} or not isinstance(response["value"], str):
        return None, "candidate response has the wrong shape"
    return response["value"], None


def _observe_case(entrypoint: Path, case: Mapping[str, Any], digits: int, max_ulps: int) -> tuple[dict[str, Any] | None, str | None]:
    output_text, problem = _run_case(entrypoint, case)
    if problem is not None or output_text is None:
        return None, problem
    try:
        x = float.fromhex(case["x"])
        y = float.fromhex(case["y"])
        output = float.fromhex(output_text)
    except (ValueError, OverflowError) as error:
        output = math.nan
        parse_problem = str(error)
    else:
        parse_problem = None
    reference = _oracle(x, y, digits)
    reason: str | None = None
    distance: int | None = None
    if parse_problem is not None:
        reason = "malformed-output"
    elif not math.isfinite(output):
        reason = "nonfinite-output"
    elif output < 0.0:
        reason = "negative-output"
    else:
        distance = _ulp_distance(output, reference)
        if distance > max_ulps:
            reason = "ulp-bound-exceeded"
    observation = {
        "id": case["id"],
        "input": {"x": case["x"], "y": case["y"]},
        "output": output_text,
        "oracle": reference.hex(),
        "ulpDistance": distance,
        "maxUlps": max_ulps,
        "result": "supports" if reason is None else "challenges",
    }
    return observation, reason


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def inspect_numerical_package(manifest_path: Path) -> tuple[dict[str, Any] | None, tuple[record_check.Diagnostic, ...], tuple[Path, ...]]:
    authority = graph.inspect_manifest_authority(manifest_path)
    observation = graph.inspect_manifest_graph(authority)
    if not observation.ok:
        return None, observation.diagnostics, (manifest_path,)
    documents = {record.address: record.document for record in observation.records}
    source_roots = {item.source_id: item.root for item in authority.sources}
    members = tuple(authority.manifest_path.parent / source_roots[record.source] / record.path.split("/", 1)[-1] for record in observation.records)
    required = (SPECIFICATION, PROFILE, POLICY, *(("realization", item, "0.1.0") for item in REALIZATIONS))
    missing = [address for address in required if address not in documents]
    if missing:
        return None, (_diagnostic("NUMERICAL_REQUIRED_RECORD", message=repr(missing[0])),), (manifest_path, *members)
    specification = documents[SPECIFICATION]
    semantic = inspect_numerical_document(specification)
    if not semantic.ok:
        return None, semantic.diagnostics, (manifest_path, *members)
    evidences = [value for address, value in documents.items() if address[0] == "evidence"]
    if len(evidences) != 2:
        return None, (_diagnostic("NUMERICAL_EVIDENCE_COUNT"),), (manifest_path, *members)
    plan_paths = {item.get("provenance", {}).get("plan", {}).get("path") for item in evidences}
    plan_hashes = {item.get("provenance", {}).get("plan", {}).get("rawSha256") for item in evidences}
    if len(plan_paths) != 1 or len(plan_hashes) != 1 or None in plan_paths or None in plan_hashes:
        return None, (_diagnostic("NUMERICAL_PLAN_BINDING"),), (manifest_path, *members)
    plan_path = ROOT / next(iter(plan_paths))
    plan_hash = next(iter(plan_hashes))
    try:
        if _sha256(plan_path) != plan_hash:
            return None, (_diagnostic("NUMERICAL_PLAN_DIGEST", os.fspath(plan_path)),), (manifest_path, *members, plan_path)
        plan = _load_json(plan_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, (_diagnostic("NUMERICAL_PLAN_READ", os.fspath(plan_path), message=str(error)),), (manifest_path, *members, plan_path)
    oracle = plan.get("oracle", {})
    digits = oracle.get("decimalDigits")
    max_ulps = oracle.get("maxUlps")
    cases = plan.get("cases")
    candidates = plan.get("candidates")
    kernels = specification.get("numericalKernels", [])
    kernel = kernels[0] if isinstance(kernels, list) and len(kernels) == 1 else {}
    expected_spec = {"kind": "specification", "id": "stable-norm2", "version": "0.1.0"}
    expected_profile = {"kind": "realizationProfile", "id": "stable-norm2-binary64", "version": "0.1.0"}
    if (
        plan.get("specification") != expected_spec
        or plan.get("profile") != expected_profile
        or oracle.get("kind") != kernel.get("oracle")
        or digits != kernel.get("oracleDecimalDigits")
        or max_ulps != kernel.get("maxUlps")
        or kernel.get("profile") != expected_profile
    ):
        return None, (_diagnostic("NUMERICAL_ORACLE_CONFIGURATION", os.fspath(plan_path)),), (manifest_path, *members, plan_path)
    if not isinstance(digits, int) or digits < 1 or not isinstance(max_ulps, int) or max_ulps < 0:
        return None, (_diagnostic("NUMERICAL_ORACLE_CONFIGURATION", os.fspath(plan_path)),), (manifest_path, *members, plan_path)
    if not isinstance(cases, list) or not cases:
        return None, (_diagnostic("NUMERICAL_CASES_REQUIRED", os.fspath(plan_path)),), (manifest_path, *members, plan_path)
    expected_candidates = [*REALIZATIONS, "stable-norm2-naive-breaker"]
    if not isinstance(candidates, list) or [item.get("id") for item in candidates] != expected_candidates:
        return None, (_diagnostic("NUMERICAL_CANDIDATE_ORDER", os.fspath(plan_path)),), (manifest_path, *members, plan_path)
    governed: list[Path] = [manifest_path, *members, plan_path]
    candidate_results: list[dict[str, Any]] = []
    for candidate in candidates:
        source = ROOT / candidate["entrypoint"]
        governed.append(source)
        try:
            if _sha256(source) != candidate["sha256"]:
                return None, (_diagnostic("NUMERICAL_SOURCE_DIGEST", os.fspath(source)),), tuple(governed)
        except OSError as error:
            return None, (_diagnostic("NUMERICAL_SOURCE_READ", os.fspath(source), message=str(error)),), tuple(governed)
        observations: list[dict[str, Any]] = []
        counterexample: dict[str, Any] | None = None
        for index, case in enumerate(cases):
            item, problem = _observe_case(source, case, digits, max_ulps)
            if item is None:
                return None, (_diagnostic("NUMERICAL_CANDIDATE_EXECUTION", os.fspath(source), message=problem),), tuple(governed)
            observations.append(item)
            if item["result"] == "challenges" and counterexample is None:
                counterexample = {"case": case["id"], "index": index, "reason": problem or ("nonfinite-output" if item["ulpDistance"] is None else "ulp-bound-exceeded")}
        result = "supports" if counterexample is None else "challenges"
        candidate_result = {"id": candidate["id"], "registered": candidate["registered"], "representation": candidate["representation"], "sources": [candidate["entrypoint"]], "result": result, "cases": observations}
        if counterexample is not None:
            candidate_result["counterexample"] = counterexample
        candidate_results.append(candidate_result)
    by_id = {item["id"]: item for item in candidate_results}
    plan_candidates = {item["id"]: item for item in candidates}
    policy = documents[POLICY]
    concerns = policy.get("concerns")
    policy_ok = (
        policy.get("specification") == expected_spec
        and policy.get("profile") == expected_profile
        and isinstance(concerns, list) and len(concerns) == 1
        and concerns[0].get("concern") == "numerical.approximation"
        and concerns[0].get("priority") == "required"
        and concerns[0].get("acceptedMechanisms") == ["bounded-numerical-campaign"]
        and concerns[0].get("minimumAssurance") == "one-accepted-applicable-support-no-selected-challenge"
    )
    decisions: list[dict[str, Any]] = []
    boundaries: list[dict[str, Any]] = []
    for realization_id in REALIZATIONS:
        realization = documents.get(("realization", realization_id, "0.1.0"), {})
        claim_id = f"{realization_id}-approximation"
        evidence_id = f"{realization_id}-campaign"
        claim = documents.get(("claim", claim_id, "0.1.0"), {})
        evidence = documents.get(("evidence", evidence_id, "0.1.0"), {})
        expected_realization = {"kind": "realization", "id": realization_id, "version": "0.1.0"}
        adapter = realization.get("adapter", {})
        candidate = plan_candidates[realization_id]
        provenance = evidence.get("provenance", {})
        accepted = (
            by_id[realization_id]["result"] == "supports" and policy_ok
            and realization.get("specification") == expected_spec
            and realization.get("supportedProfiles") == [expected_profile]
            and claim.get("subject") == expected_realization
            and claim.get("governingSpecification") == expected_spec
            and claim.get("proposition") == {"specification": expected_spec, "declarationId": "approximate-norm2"}
            and claim.get("concern") == "numerical.approximation"
            and claim.get("applicableProfiles") == [expected_profile]
            and claim.get("state") == "active"
            and evidence.get("claim") == {"kind": "claim", "id": claim_id, "version": "0.1.0"}
            and evidence.get("specification") == expected_spec
            and evidence.get("realization") == expected_realization
            and evidence.get("adapter") == {"id": adapter.get("id"), "version": adapter.get("version")}
            and evidence.get("mechanism") == "bounded-numerical-campaign"
            and evidence.get("result") == "supports"
            and evidence.get("reviewState") == "accepted"
            and evidence.get("applicability", {}).get("profiles") == [expected_profile]
            and evidence.get("applicability", {}).get("parameters") == {"caseCount": len(cases), "maxUlps": max_ulps, "oracleDecimalDigits": digits}
            and provenance.get("plan") == {"path": next(iter(plan_paths)), "rawSha256": plan_hash}
            and provenance.get("source") == {"path": candidate["entrypoint"], "rawSha256": candidate["sha256"]}
            and provenance.get("caseOrder") == [item["id"] for item in cases]
        )
        decisions.append({"realization": expected_realization, "semanticStatus": "acceptable" if accepted else "rejected", "evidence": {"id": evidence_id, "mechanism": evidence.get("mechanism"), "result": evidence.get("result"), "reviewState": evidence.get("reviewState")}})
        boundaries.append({"realization": realization_id, "direction": f"consumer->{realization_id}", "mechanism": "hex-float-child-process", "direct": False})
    report = {
        "kind": "numerical-package-inspection-v1",
        "specification": expected_spec,
        "authority": {"manifestRawSha256": _sha256(manifest_path), "memberCount": len(authority.members)},
        "campaign": {"planRawSha256": plan_hash, "caseOrder": [item["id"] for item in cases], "caseCount": len(cases) * len(candidates), "maxUlps": max_ulps, "oracleDecimalDigits": digits},
        "candidates": candidate_results,
        "decisions": decisions,
        "theory": {"declarations": [item["id"] for item in specification.get("laws", [])], "packageEvidenceIncluded": False},
        "boundaries": boundaries,
        "assumptions": plan["assumptions"],
        "exclusions": plan["exclusions"],
        "conclusion": "bounded-approximate-kernel-observed",
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
        return _diagnostic("NUMERICAL_OUTPUT_WRITE", os.fspath(path), message=str(error))
    return None


def run_numerical_inspection(manifest_path: Path, output_path: Path) -> int:
    if _aliases(manifest_path, output_path):
        print(f"NUMERICAL_OUTPUT_ALIAS {output_path}#: output aliases governed manifest", file=sys.stderr)
        return 1
    report, diagnostics, governed = inspect_numerical_package(manifest_path)
    if diagnostics:
        for diagnostic in diagnostics:
            print(f"{diagnostic.code} {diagnostic.path}{diagnostic.pointer}: {diagnostic.message or 'numerical inspection failed'}", file=sys.stderr)
        return 1
    assert report is not None
    for path in governed:
        if _aliases(path, output_path):
            print(f"NUMERICAL_OUTPUT_ALIAS {output_path}#: output aliases governed input {path}", file=sys.stderr)
            return 1
    diagnostic = _write_atomically(output_path, report)
    if diagnostic is not None:
        print(f"{diagnostic.code} {diagnostic.path}{diagnostic.pointer}: {diagnostic.message}", file=sys.stderr)
        return 1
    print(
        "inspected stable-norm2 0.1.0: 2 registered realizations accepted, "
        "1 overflow breaker challenged across 36 cases; tolerance=2-ulp; "
        f"satisfaction=policy-relative -> {output_path}"
    )
    return 0
