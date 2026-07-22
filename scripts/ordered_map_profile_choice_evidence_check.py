#!/usr/bin/env python3
"""Derive and validate exact profile-choice package records from P-R3a reports."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import ordered_map_evidence_check as base  # noqa: E402
from scripts import record_check  # noqa: E402


SPECIFICATION_PATH = Path("registry/ordered-map/theory/records/ordered-map-spec.json")
PREDECESSOR_PROFILE_PATH = Path(
    "registry/ordered-map/theory/dependencies/ordered-map-profile.json"
)
SPECIFICATION = {"kind": "specification", "id": "ordered-map", "version": "0.1.0"}
VERSION = "0.2.0"
REVIEW_STATE = "accepted"
REVIEW_LINEAGE = (
    "P-R3a and P-R3b PASS; acceptance is bounded to the exact "
    "profile-specific report derivation."
)
PRODUCED_AT = "2026-07-22T00:00:00Z"
CANDIDATES = {
    "rust": {
        **base.CANDIDATES["rust"],
        "profile": {
            "kind": "realizationProfile",
            "id": "ordered-map-native-process",
            "version": "0.1.0",
        },
        "profilePath": Path(
            "registry/ordered-map/profile-choice/profiles/records/ordered-map-native-process.json"
        ),
        "report": Path(
            "reports/ordered-map/profile-choice/rust-native-campaign-report.json"
        ),
        "recordRoot": Path(
            "registry/ordered-map/profile-choice/packages/rust/records"
        ),
    },
    "typescript": {
        **base.CANDIDATES["typescript"],
        "profile": {
            "kind": "realizationProfile",
            "id": "ordered-map-deno-sandbox",
            "version": "0.1.0",
        },
        "profilePath": Path(
            "registry/ordered-map/profile-choice/profiles/records/ordered-map-deno-sandbox.json"
        ),
        "report": Path(
            "reports/ordered-map/profile-choice/typescript-deno-campaign-report.json"
        ),
        "recordRoot": Path(
            "registry/ordered-map/profile-choice/packages/typescript/records"
        ),
    },
}


def _record_paths(candidate: dict[str, Any]) -> list[Path]:
    root = candidate["recordRoot"]
    prefix = candidate["id"]
    return [
        root / f"{prefix}-realization.json",
        *[root / f"{prefix}-{item}-claim.json" for item in base.DECLARATIONS],
        *[root / f"{prefix}-{item}-evidence.json" for item in base.DECLARATIONS],
    ]


def _profile_name(candidate: dict[str, Any]) -> str:
    return candidate["profile"]["id"]


def _claim_scope(candidate: dict[str, Any], declaration: str) -> str:
    profile = _profile_name(candidate)
    if declaration == "ordered-map-effects":
        return (
            f"adapter-reported invocation events for {candidate['id']} through "
            f"{candidate['adapter']} under {profile}."
        )
    return f"{candidate['id']} through {candidate['adapter']} under {profile}."


def _realization(candidate: dict[str, Any]) -> dict[str, Any]:
    profile = _profile_name(candidate)
    return {
        "kind": "realization",
        "id": candidate["id"],
        "version": VERSION,
        "specification": SPECIFICATION,
        "adapter": {
            "id": candidate["adapter"],
            "version": "0.1.0",
            "protocol": "ordered-map-runner-json-v1",
            "entrypoint": candidate["entrypoint"],
            "assumptions": [
                "The adapter faithfully exposes the named Realization.",
                "Reported events are complete for the adapter-observed boundary.",
            ],
        },
        "implementation": candidate["implementation"],
        "capabilities": base.CAPABILITIES,
        "limitations": [
            f"Evidence is bounded to {profile}/0.1.0 and its exact campaign.",
            "Reported events cover only the adapter-observed invocation boundary.",
            "No performance, concurrency, remote transport, registry discovery, or interoperation claim.",
        ],
        "supportedProfiles": [candidate["profile"]],
    }


def _claim(candidate: dict[str, Any], declaration: str) -> dict[str, Any]:
    return {
        "kind": "claim",
        "id": f"{candidate['id']}-{declaration}",
        "version": VERSION,
        "subject": {
            "kind": "realization",
            "id": candidate["id"],
            "version": VERSION,
        },
        "governingSpecification": SPECIFICATION,
        "proposition": {"specification": SPECIFICATION, "declarationId": declaration},
        "concern": base.DECLARATIONS[declaration],
        "scope": _claim_scope(candidate, declaration),
        "assumptions": base._claim_assumptions(declaration),
        "exclusions": base._claim_exclusions(declaration),
        "applicableProfiles": [candidate["profile"]],
        "state": "active",
    }


def _provenance(
    root: Path,
    candidate: dict[str, Any],
    declaration: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    outcome = next(
        item for item in report["outcome"]["declarations"] if item["id"] == declaration
    )
    return {
        "declaration": declaration,
        "report": {
            "path": candidate["report"].as_posix(),
            "sha256": hashlib.sha256((root / candidate["report"]).read_bytes()).hexdigest(),
        },
        "reportCandidate": candidate["id"],
        "reportPacketRole": "profile-choice-candidate",
        "declarationOutcome": outcome,
        "plan": report["inputs"]["plan"],
        "specification": report["inputs"]["specification"],
        "profile": report["inputs"]["profile"],
        "runner": report["inputs"]["runner"],
        "harness": report["inputs"]["harness"],
        "sources": report["inputs"]["sources"],
        "commandsCanonicalSha256": base._canonical_sha256(report["commands"]),
        "toolchainCanonicalSha256": base._canonical_sha256(report["toolchain"]),
        "outcomeCanonicalSha256": base._canonical_sha256(report["outcome"]),
        "binarySha256": report["binarySha256"],
        "review": REVIEW_LINEAGE,
    }


def _evidence(
    root: Path,
    candidate: dict[str, Any],
    declaration: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    provenance = _provenance(root, candidate, declaration, report)
    outcome = provenance["declarationOutcome"]
    return {
        "kind": "evidence",
        "id": f"{candidate['id']}-{declaration}-conformance",
        "version": VERSION,
        "claim": {
            "kind": "claim",
            "id": f"{candidate['id']}-{declaration}",
            "version": VERSION,
        },
        "specification": SPECIFICATION,
        "scope": "realization",
        "realization": {
            "kind": "realization",
            "id": candidate["id"],
            "version": VERSION,
        },
        "adapter": {"id": candidate["adapter"], "version": "0.1.0"},
        "mechanism": "bounded-conformance-campaign",
        "result": outcome["result"],
        "reviewState": REVIEW_STATE,
        "method": base._evidence_method(declaration).replace("O-R6d6", "P-R3a"),
        "environment": candidate["environment"],
        "freshness": {"producedAt": PRODUCED_AT},
        "assumptions": [
            item.replace("O-R6d6", "P-R3a")
            for item in base._evidence_assumptions(declaration)
        ],
        "exclusions": base._evidence_exclusions(declaration),
        "applicability": {
            "profiles": [candidate["profile"]],
            "parameters": base.APPLICABILITY_PARAMETERS,
        },
        "provenance": provenance,
    }


def load_profile_choice_reports(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    return {
        candidate["id"]: json.loads(
            (root / candidate["report"]).read_text(encoding="utf-8")
        )
        for candidate in CANDIDATES.values()
    }


def load_profile_choice_candidate_records(
    root: Path = ROOT,
) -> dict[Path, dict[str, Any]]:
    documents: dict[Path, dict[str, Any]] = {}
    for candidate in CANDIDATES.values():
        package = root / candidate["recordRoot"]
        if not package.is_dir():
            continue
        for path in sorted(package.rglob("*.json")):
            documents[path.relative_to(root)] = json.loads(path.read_text(encoding="utf-8"))
    return documents


def expected_profile_choice_candidate_records(
    root: Path,
    reports: dict[str, dict[str, Any]],
) -> dict[Path, dict[str, Any]]:
    expected: dict[Path, dict[str, Any]] = {}
    for candidate in CANDIDATES.values():
        paths = _record_paths(candidate)
        expected[paths[0]] = _realization(candidate)
        report = reports[candidate["id"]]
        for index, declaration in enumerate(base.DECLARATIONS, start=1):
            expected[paths[index]] = _claim(candidate, declaration)
        offset = 1 + len(base.DECLARATIONS)
        for index, declaration in enumerate(base.DECLARATIONS):
            expected[paths[offset + index]] = _evidence(
                root, candidate, declaration, report
            )
    return expected


def run_profile_choice_evidence_checks(
    root: Path = ROOT,
) -> tuple[list[str], str]:
    root = Path(root).resolve()
    try:
        reports = load_profile_choice_reports(root)
        documents = load_profile_choice_candidate_records(root)
        expected = expected_profile_choice_candidate_records(root, reports)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, StopIteration) as error:
        return [f"OrderedMap profile-choice Evidence input failed: {error}"], ""

    errors: list[str] = []
    for path in sorted(set(expected) - set(documents)):
        errors.append(f"missing OrderedMap profile-choice record: {path}")
    for path in sorted(set(documents) - set(expected)):
        errors.append(f"unexpected OrderedMap profile-choice record: {path}")
    for path in sorted(set(expected) & set(documents)):
        if documents[path] != expected[path]:
            errors.append(f"OrderedMap profile-choice record differs: {path}")

    diagnostics = record_check.validate_graph_paths(
        [
            (root / SPECIFICATION_PATH).as_posix(),
            (root / PREDECESSOR_PROFILE_PATH).as_posix(),
            *[(root / candidate["profilePath"]).as_posix() for candidate in CANDIDATES.values()],
            *[(root / candidate["recordRoot"]).as_posix() for candidate in CANDIDATES.values()],
        ]
    )
    errors.extend(item.format() for item in diagnostics)
    if errors:
        return errors, ""
    return (
        [],
        "OrderedMap profile-choice Evidence checks passed: "
        "2 Realizations, 14 Claims, 14 Evidence records.",
    )


if __name__ == "__main__":
    problems, summary = run_profile_choice_evidence_checks(ROOT)
    if problems:
        print("OrderedMap profile-choice Evidence checks failed:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print(summary)
