#!/usr/bin/env python3
"""Validate the pre-authority OrderedMap Realization, Claim, and Evidence candidates."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import record_check  # noqa: E402


SPECIFICATION_PATH = Path("registry/ordered-map/theory/records/ordered-map-spec.json")
PROFILE_PATH = Path("registry/ordered-map/theory/dependencies/ordered-map-profile.json")
SPECIFICATION = {"kind": "specification", "id": "ordered-map", "version": "0.1.0"}
PROFILE = {
    "kind": "realizationProfile",
    "id": "ordered-map-ascii-fold",
    "version": "0.1.0",
}
DECLARATIONS = {
    "lookup-empty": "law.conformance",
    "lookup-put-same": "law.conformance",
    "lookup-put-other": "law.conformance",
    "put-existing-position": "law.conformance",
    "put-new-appends": "law.conformance",
    "persistence": "resource.persistence",
    "ordered-map-effects": "effect.conformance",
}
CANDIDATES = {
    "rust": {
        "id": "ordered-map-rust",
        "adapter": "ordered-map-rust-json-adapter",
        "entrypoint": "implementations/ordered-map/rust/src/main.rs",
        "report": Path("reports/ordered-map/rust-campaign-report.json"),
        "recordRoot": Path("registry/ordered-map/packages/rust/records"),
        "implementation": {
            "language": "Rust",
            "languageVersion": "1.96.1",
            "target": "local native child process",
            "runtime": "native executable",
            "interfaceMechanism": "NDJSON messages over stdin and stdout",
            "buildSystem": "direct rustc, edition 2024",
            "buildInstructions": (
                "Use RUSTC with the explicit GCC linker as documented in "
                "implementations/ordered-map/rust/README.md."
            ),
            "executionInstructions": "Run the built adapter as a lockstep child process.",
        },
        "environment": {
            "runnerProtocol": "ordered-map-runner-json-v1",
            "python": "3.14.6",
            "jsonschema": "4.26.0",
            "referencing": "0.37.0",
            "rustc": "1.96.1 (31fca3adb)",
            "gcc": "15.2.0",
        },
    },
    "typescript": {
        "id": "ordered-map-typescript",
        "adapter": "ordered-map-typescript-json-adapter",
        "entrypoint": "implementations/ordered-map/typescript/adapter.ts",
        "report": Path("reports/ordered-map/typescript-campaign-report.json"),
        "recordRoot": Path("registry/ordered-map/packages/typescript/records"),
        "implementation": {
            "language": "TypeScript",
            "languageVersion": "6.0.3",
            "target": "local Deno child process",
            "runtime": "Deno 2.9.2",
            "interfaceMechanism": "NDJSON messages over stdin and stdout",
            "buildSystem": "dependency-free Deno check",
            "buildInstructions": (
                "Run the offline Deno check documented in "
                "implementations/ordered-map/typescript/README.md."
            ),
            "executionInstructions": (
                "Run adapter.ts with Deno's no-config, no-lock, no-npm, no-remote, "
                "and no-prompt flags."
            ),
        },
        "environment": {
            "runnerProtocol": "ordered-map-runner-json-v1",
            "python": "3.14.6",
            "jsonschema": "4.26.0",
            "referencing": "0.37.0",
            "deno": "2.9.2",
            "v8": "14.9.207.2-rusty",
            "typescript": "6.0.3",
        },
    },
}
CAPABILITIES = [
    "ordered-map.empty",
    "ordered-map.put",
    "ordered-map.lookup",
    "ordered-map.entries",
]
LIMITATIONS = [
    "Evidence is bounded to ordered-map-ascii-fold/0.1.0 and its exact campaign.",
    "Reported events cover only the adapter-observed invocation boundary.",
    "No performance, concurrency, remote transport, registry discovery, or interoperation claim.",
]
REVIEW_LINEAGE = (
    "O-R6d6 PASS; retained report fact independently reproduced three consecutive times."
)
PRODUCED_AT = "2026-07-19T21:11:33Z"
APPLICABILITY_PARAMETERS = {
    "keyDomain": ["A", "a", "B", "b", "C", "c"],
    "valueMinimum": -2,
    "valueMaximum": 2,
    "maximumHistory": 3,
    "maximumLiveClasses": 3,
    "observationLimit": 3,
    "responseTimeoutSeconds": 0.2,
    "exitTimeoutSeconds": 0.2,
}


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _record_paths(candidate: dict[str, Any]) -> list[Path]:
    root = candidate["recordRoot"]
    prefix = candidate["id"]
    return [
        root / f"{prefix}-realization.json",
        *[root / f"{prefix}-{item}-claim.json" for item in DECLARATIONS],
        *[root / f"{prefix}-{item}-evidence.json" for item in DECLARATIONS],
    ]


def _claim_scope(candidate: dict[str, Any], declaration: str) -> str:
    if declaration == "ordered-map-effects":
        return (
            f"adapter-reported invocation events for {candidate['id']} through "
            f"{candidate['adapter']} under ordered-map-ascii-fold."
        )
    return (
        f"{candidate['id']} through {candidate['adapter']} under "
        "ordered-map-ascii-fold."
    )


def _claim_assumptions(declaration: str) -> list[str]:
    if declaration == "ordered-map-effects":
        return ["Reported events are complete for the adapter-observed boundary."]
    return ["The adapter faithfully exposes the named Realization."]


def _claim_exclusions(declaration: str) -> list[str]:
    if declaration == "ordered-map-effects":
        return ["Effects outside the adapter-reported invocation boundary are not observed."]
    return ["No behavior outside the exact bounded campaign is asserted."]


def _evidence_method(declaration: str) -> str:
    if declaration == "ordered-map-effects":
        subject = "adapter-reported invocation-event campaign"
    elif declaration == "persistence":
        subject = "retained-source observation campaign"
    else:
        subject = "OrderedMap campaign report"
    return f"O-R6d6-reviewed {subject} for one declaration under the exact plan."


def _evidence_assumptions(declaration: str) -> list[str]:
    first = (
        "Reported events are complete for the adapter-observed boundary."
        if declaration == "ordered-map-effects"
        else "The adapter faithfully exposes the named Realization."
    )
    return [first, "The runner and O-R6d6 review correctly enforce the recorded checks."]


def _evidence_exclusions(declaration: str) -> list[str]:
    if declaration == "ordered-map-effects":
        return [
            "Effects outside the adapter-reported invocation boundary are not observed.",
            "No general external-effect, performance, concurrency, remote, or interoperation conclusion.",
        ]
    if declaration == "persistence":
        return [
            "Support is bounded to the exact plan, profile, report, and process session.",
            "No post-termination, performance, concurrency, remote, or interoperation conclusion.",
        ]
    return [
        "Support is bounded to the exact plan, profile, report, and process session.",
        "No performance, malformed-client, concurrency, remote, or interoperation conclusion.",
    ]


def load_ordered_map_reports(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    return {
        candidate["id"]: json.loads((root / candidate["report"]).read_text(encoding="utf-8"))
        for candidate in CANDIDATES.values()
    }


def load_ordered_map_candidate_records(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for candidate in CANDIDATES.values():
        package = root / candidate["recordRoot"]
        if not package.is_dir():
            continue
        for path in sorted(package.rglob("*.json")):
            relative = path.relative_to(root).as_posix()
            documents[relative] = json.loads(path.read_text(encoding="utf-8"))
    return documents


def _realization(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "realization",
        "id": candidate["id"],
        "version": "0.1.0",
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
        "capabilities": CAPABILITIES,
        "limitations": LIMITATIONS,
        "supportedProfiles": [PROFILE],
    }


def _claim(candidate: dict[str, Any], declaration: str) -> dict[str, Any]:
    return {
        "kind": "claim",
        "id": f"{candidate['id']}-{declaration}",
        "version": "0.1.0",
        "subject": {
            "kind": "realization",
            "id": candidate["id"],
            "version": "0.1.0",
        },
        "governingSpecification": SPECIFICATION,
        "proposition": {"specification": SPECIFICATION, "declarationId": declaration},
        "concern": DECLARATIONS[declaration],
        "scope": _claim_scope(candidate, declaration),
        "assumptions": _claim_assumptions(declaration),
        "exclusions": _claim_exclusions(declaration),
        "applicableProfiles": [PROFILE],
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
        "reportPacketRole": "candidate",
        "declarationOutcome": outcome,
        "plan": report["inputs"]["plan"],
        "specification": report["inputs"]["specification"],
        "profile": report["inputs"]["profile"],
        "runner": report["inputs"]["runner"],
        "harness": report["inputs"]["harness"],
        "sources": report["inputs"]["sources"],
        "commandsCanonicalSha256": _canonical_sha256(report["commands"]),
        "toolchainCanonicalSha256": _canonical_sha256(report["toolchain"]),
        "outcomeCanonicalSha256": _canonical_sha256(report["outcome"]),
        "binarySha256": report["binarySha256"],
        "review": REVIEW_LINEAGE,
    }


def _evidence(
    root: Path,
    candidate: dict[str, Any],
    declaration: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "evidence",
        "id": f"{candidate['id']}-{declaration}-conformance",
        "version": "0.1.0",
        "claim": {
            "kind": "claim",
            "id": f"{candidate['id']}-{declaration}",
            "version": "0.1.0",
        },
        "specification": SPECIFICATION,
        "scope": "realization",
        "realization": {
            "kind": "realization",
            "id": candidate["id"],
            "version": "0.1.0",
        },
        "adapter": {"id": candidate["adapter"], "version": "0.1.0"},
        "mechanism": "bounded-conformance-campaign",
        "result": "supports",
        "reviewState": "accepted",
        "method": _evidence_method(declaration),
        "environment": candidate["environment"],
        "freshness": {"producedAt": PRODUCED_AT},
        "assumptions": _evidence_assumptions(declaration),
        "exclusions": _evidence_exclusions(declaration),
        "applicability": {
            "profiles": [PROFILE],
            "parameters": APPLICABILITY_PARAMETERS,
        },
        "provenance": _provenance(root, candidate, declaration, report),
    }


def expected_ordered_map_candidate_records(
    root: Path,
    reports: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    expected: dict[str, dict[str, Any]] = {}
    for candidate in CANDIDATES.values():
        paths = _record_paths(candidate)
        expected[paths[0].as_posix()] = _realization(candidate)
        report = reports[candidate["id"]]
        for index, declaration in enumerate(DECLARATIONS, start=1):
            expected[paths[index].as_posix()] = _claim(candidate, declaration)
        offset = 1 + len(DECLARATIONS)
        for index, declaration in enumerate(DECLARATIONS):
            expected[paths[offset + index].as_posix()] = _evidence(
                root, candidate, declaration, report
            )
    return expected


def candidate_record_errors(
    documents: dict[str, dict[str, Any]],
    reports: dict[str, dict[str, Any]],
    root: Path = ROOT,
) -> list[str]:
    expected = expected_ordered_map_candidate_records(root, reports)
    errors: list[str] = []
    missing = sorted(set(expected) - set(documents))
    unexpected = sorted(set(documents) - set(expected))
    errors.extend(f"missing OrderedMap candidate record: {path}" for path in missing)
    errors.extend(f"unexpected OrderedMap candidate record: {path}" for path in unexpected)
    for path in sorted(set(expected) & set(documents)):
        if documents[path] != expected[path]:
            errors.append(f"OrderedMap candidate record differs from reviewed contract: {path}")
    return errors


def run_ordered_map_evidence_candidate_checks(
    root: Path = ROOT,
) -> tuple[list[str], str]:
    root = Path(root).resolve()
    errors: list[str] = []
    try:
        reports = load_ordered_map_reports(root)
        documents = load_ordered_map_candidate_records(root)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, StopIteration) as error:
        return [f"OrderedMap Evidence candidate input failed: {error}"], ""
    errors.extend(candidate_record_errors(documents, reports, root))

    expected_entries = {
        path.as_posix()
        for candidate in CANDIDATES.values()
        for path in _record_paths(candidate)
    }
    actual_entries = {
        path.relative_to(root).as_posix()
        for candidate in CANDIDATES.values()
        for path in (root / candidate["recordRoot"]).rglob("*")
        if path.is_file() or path.is_symlink()
    }
    for path in sorted(actual_entries - expected_entries):
        errors.append(f"unexpected OrderedMap package entry: {path}")

    diagnostics = record_check.validate_graph_paths(
        [
            (root / SPECIFICATION_PATH).as_posix(),
            (root / PROFILE_PATH).as_posix(),
            *[
                (root / candidate["recordRoot"]).as_posix()
                for candidate in CANDIDATES.values()
            ],
        ]
    )
    errors.extend(item.format() for item in diagnostics)
    if errors:
        return errors, ""
    return (
        [],
        "OrderedMap Evidence candidate checks passed: "
        "2 Realizations, 14 Claims, 14 Evidence records.",
    )


def main() -> int:
    errors, summary = run_ordered_map_evidence_candidate_checks(ROOT)
    if errors:
        for error in errors:
            print(error)
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
