#!/usr/bin/env python3
"""Reproduce and bind Wave 4 campaign reports and Evidence provenance."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_packages.stack_runner import (  # noqa: E402
    ConformanceReport,
    default_stack_conformance_plan,
    run_stack_conformance,
)
from scripts import record_check  # noqa: E402

PLAN_SHA256 = "e055eab406683a01a32e8b563ef2e299169ddb2745685b5ad3ffae3297d93f6c"
RUNNER = Path("semantic_packages/stack_runner.py")
SPECIFICATION = Path("fixtures/records/valid/stack-spec.json")
PROFILE = Path("fixtures/records/valid/stack-profile.json")
MATRIX = Path("tests/candidates/test_cross_language_candidates.py")
DECLARATIONS = ("pop-empty", "pop-push", "persistence", "stack-effects")
EXPECTED_REVIEWS = {
    ("rust", "pop-empty"): "W4-RR1 PASS followed by W4-RR2 PASS on the arbitrary-sequence successor",
    ("rust", "pop-push"): "W4-RR2 PASS; law-breaker challenged only pop-push",
    ("rust", "persistence"): "W4-RR2 PASS; retained ancestor probes passed",
    ("rust", "stack-effects"): "W4-RR2 PASS; empty event trace retained with completeness assumption",
    ("typescript", "pop-empty"): "W4-TR1 BLOCK then W4-TR2 PASS after arbitrary sequence correction",
    ("typescript", "pop-push"): "W4-TR2 PASS; exact campaign and protocol probes passed",
    ("typescript", "persistence"): "W4-TR2 PASS; persistence breaker challenged only persistence",
    ("typescript", "stack-effects"): "W4-TR2 PASS; empty event trace retained with completeness assumption",
}
PROVENANCE_KEYS = {
    "rust": frozenset(
        {
            "declaration",
            "planSha256",
            "buildArgv",
            "campaignArgv",
            "inputs",
            "report",
            "runner",
            "sources",
            "binarySha256",
            "review",
        }
    ),
    "typescript": frozenset(
        {
            "declaration",
            "planSha256",
            "checkArgv",
            "campaignArgv",
            "inputs",
            "report",
            "runner",
            "sources",
            "review",
        }
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def _tool(environment: str, fallback: str) -> str:
    selected = os.environ.get(environment, fallback)
    resolved = shutil.which(selected)
    if resolved is None:
        raise RuntimeError(f"required tool {environment}/{fallback} is unavailable")
    return resolved


def _run(argv: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    process = subprocess.run(
        tuple(argv),
        cwd=ROOT,
        shell=False,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10.0,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"command failed ({process.returncode}): {list(argv)!r}; "
            f"stdout={process.stdout!r}; stderr={process.stderr!r}"
        )
    return process


def _report_payload(candidate: str, report: ConformanceReport) -> dict[str, Any]:
    return {
        "assumptions": list(report.assumptions),
        "candidate": candidate,
        "causes": list(report.causes),
        "declarations": [
            {
                "causes": list(outcome.causes),
                "id": outcome.declaration_id,
                "observationCount": sum(
                    observation.declaration_id == outcome.declaration_id
                    for observation in report.observations
                ),
                "result": outcome.result,
            }
            for outcome in report.declaration_outcomes
        ],
        "events": [list(event) for event in report.events],
        "exclusions": list(report.exclusions),
        "observationCount": len(report.observations),
        "planSha256": report.plan_sha256,
        "result": report.result,
        "stderrSha256": hashlib.sha256(report.stderr).hexdigest(),
    }


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _input_map(items: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {"path": path.as_posix(), "sha256": _sha256(path)}
        for name, path in items.items()
    }


def _binding_errors(
    candidate: str,
    declaration: str,
    evidence: dict[str, Any],
    claim: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    realization_id = "stack-rust" if candidate == "rust" else "stack-typescript"
    adapter_id = (
        "stack-rust-json-adapter"
        if candidate == "rust"
        else "stack-typescript-json-adapter"
    )
    claim_id = f"{realization_id}-{declaration}"
    spec_ref = {"kind": "specification", "id": "stack", "version": "0.1.0"}
    realization_ref = {
        "kind": "realization",
        "id": realization_id,
        "version": "0.1.0",
    }
    claim_ref = {"kind": "claim", "id": claim_id, "version": "0.1.0"}
    profile_ref = {
        "kind": "realizationProfile",
        "id": "stack-default",
        "version": "0.1.0",
    }
    expected_concern = {
        "pop-empty": "law.conformance",
        "pop-push": "law.conformance",
        "persistence": "resource.persistence",
        "stack-effects": "effect.conformance",
    }[declaration]
    claim_assumptions = (
        ["Reported events are complete for the adapter-observed boundary."]
        if declaration == "stack-effects"
        else ["The adapter faithfully exposes the named Realization."]
    )
    claim_exclusions = {
        "pop-empty": ["No behavior outside the bounded campaign is asserted."],
        "pop-push": ["No behavior outside the bounded campaign is asserted."],
        "persistence": ["Handle behavior after process termination is not asserted."],
        "stack-effects": ["Effects outside the adapter event boundary are not observed."],
    }[declaration]
    evidence_assumptions = [
        (
            "Reported events are complete for the adapter-observed boundary."
            if declaration == "stack-effects"
            else "The adapter faithfully exposes the named Realization."
        ),
        "The runner and independent review correctly enforce the recorded checks.",
    ]
    evidence_exclusions = {
        "pop-empty": [
            "Support is bounded to the exact plan and profile.",
            "No performance, external-effect, malformed-client, concurrency, remote, or interoperation conclusion.",
        ],
        "pop-push": [
            "Support is bounded to the exact plan and profile.",
            "No performance, external-effect, malformed-client, concurrency, remote, or interoperation conclusion.",
        ],
        "persistence": [
            "Support is bounded to the exact plan and one process session.",
            "No post-termination, performance, concurrency, remote, or interoperation conclusion.",
        ],
        "stack-effects": [
            "Effects outside the adapter event boundary are not observed.",
            "No general security or external-effect conclusion.",
        ],
    }[declaration]
    expected_environment = (
        {"runner": "stack-runner-json-v1", "python": "3.14.6", "rustc": "1.96.1 (31fca3adb)", "linker": "GCC 15.2.0"}
        if candidate == "rust"
        else {"runner": "stack-runner-json-v1", "python": "3.14.6", "deno": "2.9.2", "typescript": "6.0.3", "mode": "offline"}
    )
    expected_claim = {
        "kind": "claim",
        "id": claim_id,
        "version": "0.1.0",
        "subject": realization_ref,
        "governingSpecification": spec_ref,
        "proposition": {"specification": spec_ref, "declarationId": declaration},
        "concern": expected_concern,
        "scope": (
            f"adapter-reported events for {realization_id} under stack-default."
            if declaration == "stack-effects"
            else f"{realization_id} through {adapter_id} under stack-default."
        ),
        "assumptions": claim_assumptions,
        "exclusions": claim_exclusions,
        "applicableProfiles": [profile_ref],
        "state": "active",
    }
    for key, value in expected_claim.items():
        if claim.get(key) != value:
            errors.append(f"claim field {key} does not bind {candidate}/{declaration}")

    expected_method = {
        ("rust", "pop-empty"): "Independent Stack campaign plus protocol, negative-control, reproducibility, and source review.",
        ("rust", "pop-push"): "Independent Stack campaign plus protocol, law-breaker, reproducibility, and source review.",
        ("rust", "persistence"): "Retained-handle and ancestor campaign plus novel persistence review.",
        ("rust", "stack-effects"): "Campaign review of adapter-reported event traces.",
        ("typescript", "pop-empty"): "Independent Stack campaign plus protocol, negative-control, arbitrary-sequence, and source review.",
        ("typescript", "pop-push"): "Independent Stack campaign plus protocol, arbitrary-sequence, and source review.",
        ("typescript", "persistence"): "Retained-handle and ancestor campaign plus persistence-breaker and novel persistence review.",
        ("typescript", "stack-effects"): "Campaign review of adapter-reported event traces.",
    }[(candidate, declaration)]
    expected_evidence = {
        "kind": "evidence",
        "id": f"{claim_id}-conformance",
        "version": "0.1.0",
        "claim": claim_ref,
        "specification": spec_ref,
        "scope": "realization",
        "realization": realization_ref,
        "adapter": {"id": adapter_id, "version": "0.1.0"},
        "mechanism": "bounded-conformance-campaign",
        "method": expected_method,
        "environment": expected_environment,
        "freshness": {"producedAt": "2026-07-18T13:00:00Z"},
        "assumptions": evidence_assumptions,
        "exclusions": evidence_exclusions,
        "applicability": {
            "profiles": [profile_ref],
            "parameters": {"maximumDepth": 8, "maximumHistory": 32, "observationLimit": 9},
        },
    }
    for key, value in expected_evidence.items():
        if evidence.get(key) != value:
            errors.append(f"Evidence field {key} does not bind {candidate}/{declaration}")
    return errors


def _realization_binding_errors(
    candidate: str, realization: dict[str, Any]
) -> list[str]:
    profile_ref = {
        "kind": "realizationProfile",
        "id": "stack-default",
        "version": "0.1.0",
    }
    spec_ref = {"kind": "specification", "id": "stack", "version": "0.1.0"}
    if candidate == "rust":
        expected = {
            "kind": "realization",
            "id": "stack-rust",
            "version": "0.1.0",
            "specification": spec_ref,
            "adapter": {
                "id": "stack-rust-json-adapter",
                "version": "0.1.0",
                "protocol": "stack-runner-json-v1",
                "entrypoint": "implementations/rust/src/main.rs",
                "assumptions": [
                    "The adapter faithfully exposes the Rust Realization.",
                    "Reported events are complete for the adapter-observed boundary.",
                ],
            },
            "implementation": {
                "language": "Rust",
                "languageVersion": "1.96.1",
                "target": "local native child process",
                "runtime": "native executable",
                "interfaceMechanism": "NDJSON messages over stdin and stdout",
                "buildSystem": "direct rustc, edition 2024",
                "buildInstructions": "Use RUSTC with an explicit CC linker as documented in implementations/rust/README.md.",
                "executionInstructions": "Run the built adapter as a lockstep child process.",
            },
            "capabilities": ["stack.empty", "stack.push", "stack.pop"],
            "limitations": [
                "Tracer profile only; element values are integers from -2 through 2.",
                "The std-only codec is bounded protocol infrastructure, not a general JSON implementation.",
                "Sequence integers use canonical nonnegative decimal spelling; alternate integral JSON spellings reopen the protocol boundary.",
                "No performance, concurrency, remote transport, registry discovery, or cross-language interoperation claim.",
            ],
            "supportedProfiles": [profile_ref],
        }
    else:
        expected = {
            "kind": "realization",
            "id": "stack-typescript",
            "version": "0.1.0",
            "specification": spec_ref,
            "adapter": {
                "id": "stack-typescript-json-adapter",
                "version": "0.1.0",
                "protocol": "stack-runner-json-v1",
                "entrypoint": "implementations/typescript/adapter.ts",
                "assumptions": [
                    "The adapter faithfully exposes the TypeScript Realization.",
                    "Reported events are complete for the adapter-observed boundary.",
                ],
            },
            "implementation": {
                "language": "TypeScript",
                "languageVersion": "6.0.3",
                "target": "local Deno child process",
                "runtime": "Deno 2.9.2",
                "interfaceMechanism": "NDJSON messages over stdin and stdout",
                "buildSystem": "dependency-free Deno check",
                "buildInstructions": "Run the offline Deno check documented in implementations/typescript/README.md.",
                "executionInstructions": "Run adapter.ts with Deno's no-config, no-lock, no-npm, no-remote, and no-prompt flags.",
            },
            "capabilities": ["stack.empty", "stack.push", "stack.pop"],
            "limitations": [
                "Tracer profile only; element values are integers from -2 through 2.",
                "Sequence integers use canonical nonnegative decimal spelling; alternate integral JSON spellings reopen the protocol boundary.",
                "No performance, concurrency, remote transport, registry discovery, or cross-language interoperation claim.",
            ],
            "supportedProfiles": [profile_ref],
        }
    return [
        f"Realization field {key} does not bind {candidate}"
        for key, value in expected.items()
        if realization.get(key) != value
    ]


def _review_binding_errors(
    candidate: str, declaration: str, provenance: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if set(provenance) != PROVENANCE_KEYS[candidate]:
        errors.append("provenance members changed")
    if provenance.get("review") != EXPECTED_REVIEWS[(candidate, declaration)]:
        errors.append("review provenance changed")
    return errors


def _check_records(
    candidate: str,
    report_path: Path,
    report_sha256: str,
    source_digests: dict[str, str],
    input_digests: dict[str, dict[str, str]],
    build_or_check_key: str,
    build_or_check_argv: list[str],
    campaign_argv: list[str],
    binary_sha256: str | None,
) -> list[str]:
    errors: list[str] = []
    prefix = "stack-rust" if candidate == "rust" else "stack-typescript"
    realization_path = ROOT / "fixtures/records/valid" / f"{prefix}-realization.json"
    realization = json.loads(realization_path.read_text(encoding="utf-8"))
    errors.extend(
        f"{realization_path.relative_to(ROOT)}: {error}"
        for error in _realization_binding_errors(candidate, realization)
    )
    for declaration in DECLARATIONS:
        path = ROOT / "fixtures/records/valid" / f"{prefix}-{declaration}-evidence.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        claim_path = ROOT / "fixtures/records/valid" / f"{prefix}-{declaration}-claim.json"
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
        errors.extend(
            f"{path.relative_to(ROOT)}: {error}"
            for error in _binding_errors(candidate, declaration, record, claim)
        )
        provenance = record.get("provenance", {})
        expected = {
            "declaration": declaration,
            "planSha256": PLAN_SHA256,
            build_or_check_key: build_or_check_argv,
            "campaignArgv": campaign_argv,
            "inputs": input_digests,
            "report": {"path": report_path.as_posix(), "sha256": report_sha256},
            "runner": {"path": RUNNER.as_posix(), "sha256": _sha256(RUNNER)},
            "sources": source_digests,
        }
        for key, value in expected.items():
            if provenance.get(key) != value:
                errors.append(f"{path.relative_to(ROOT)}: stale provenance field {key}")
        if binary_sha256 is not None and provenance.get("binarySha256") != binary_sha256:
            errors.append(f"{path.relative_to(ROOT)}: stale binarySha256")
        errors.extend(
            f"{path.relative_to(ROOT)}: {error}"
            for error in _review_binding_errors(
                candidate, declaration, provenance
            )
        )
        if record.get("result") != "supports" or record.get("reviewState") != "accepted":
            errors.append(f"{path.relative_to(ROOT)}: accepted support disposition changed")
    return errors


def run_wave4_evidence_checks() -> tuple[list[str], str]:
    errors: list[str] = []
    graph_errors, _ = record_check.check_flat_valid_records(record_check.SchemaRegistry())
    errors.extend(f"flat canonical graph: {error}" for error in graph_errors)
    rustc = _tool("RUSTC", "rustc")
    cc = _tool("CC", "cc")
    deno = _tool("DENO", "deno")
    version_probes = (
        ([rustc, "--version", "--verbose"], ("rustc 1.96.1", "commit-hash: 31fca3adb")),
        ([cc, "--version"], ("gcc (GCC) 15.2.0",)),
        ([deno, "--version"], ("deno 2.9.2", "typescript 6.0.3")),
    )
    for argv, expected_fragments in version_probes:
        observed = _run(argv).stdout.decode("utf-8", "replace")
        for fragment in expected_fragments:
            if fragment not in observed:
                errors.append(f"tool provenance mismatch: {argv[0]} lacks {fragment!r}")
    if sys.version_info[:3] != (3, 14, 6):
        errors.append(
            "tool provenance mismatch: Python is "
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}, expected 3.14.6"
        )

    rust_sources = {
        "main": Path("implementations/rust/src/main.rs"),
        "stack": Path("implementations/rust/src/stack.rs"),
    }
    ts_sources = {
        "adapter": Path("implementations/typescript/adapter.ts"),
        "stack": Path("implementations/typescript/stack.ts"),
    }
    common_inputs = {
        "specification": SPECIFICATION,
        "profile": PROFILE,
        "candidateMatrix": MATRIX,
    }
    rust_inputs = _input_map(
        common_inputs
        | {
            "breakerMain": Path("fixtures/candidates/wave4/rust_law_breaker/src/main.rs"),
            "breakerStack": Path("fixtures/candidates/wave4/rust_law_breaker/src/stack.rs"),
        }
    )
    ts_inputs = _input_map(
        common_inputs
        | {
            "breakerAdapter": Path(
                "fixtures/candidates/wave4/typescript_persistence_breaker/adapter.ts"
            ),
            "breakerStack": Path(
                "fixtures/candidates/wave4/typescript_persistence_breaker/stack.ts"
            ),
        }
    )

    with tempfile.TemporaryDirectory(prefix="wave4-evidence-") as directory:
        binary = Path(directory) / "stack-rust-adapter"
        rust_build = [
            rustc,
            "--edition",
            "2024",
            "-C",
            f"linker={cc}",
            rust_sources["main"].as_posix(),
            "-o",
            str(binary),
        ]
        _run(rust_build)
        binary_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()

        ts_check = [
            deno,
            "check",
            "--no-config",
            "--no-lock",
            "--no-npm",
            "--no-remote",
            ts_sources["adapter"].as_posix(),
            ts_sources["stack"].as_posix(),
        ]
        _run(ts_check)
        ts_child = [
            deno,
            "run",
            "--no-config",
            "--no-lock",
            "--no-npm",
            "--no-remote",
            "--no-prompt",
            ts_sources["adapter"].as_posix(),
        ]

        candidates = (
            (
                "rust",
                [str(binary)],
                Path("evidence/wave4/rust-campaign-report.json"),
                {name: _sha256(path) for name, path in rust_sources.items()},
                rust_inputs,
                "buildArgv",
                [
                    "$RUSTC", "--edition", "2024", "-C", "linker=$CC",
                    rust_sources["main"].as_posix(), "-o", "$RUST_BINARY",
                ],
                ["$RUST_BINARY"],
                binary_sha256,
            ),
            (
                "typescript",
                ts_child,
                Path("evidence/wave4/typescript-campaign-report.json"),
                {name: _sha256(path) for name, path in ts_sources.items()},
                ts_inputs,
                "checkArgv",
                [
                    "$DENO", "check", "--no-config", "--no-lock", "--no-npm",
                    "--no-remote", ts_sources["adapter"].as_posix(),
                    ts_sources["stack"].as_posix(),
                ],
                [
                    "$DENO", "run", "--no-config", "--no-lock", "--no-npm",
                    "--no-remote", "--no-prompt", ts_sources["adapter"].as_posix(),
                ],
                None,
            ),
        )

        for (
            candidate,
            command,
            report_path,
            sources,
            inputs,
            setup_key,
            setup_argv,
            campaign_argv,
            observed_binary_sha256,
        ) in candidates:
            report = run_stack_conformance(command, plan=default_stack_conformance_plan())
            fresh = _canonical_json(_report_payload(candidate, report))
            committed = (ROOT / report_path).read_bytes()
            if fresh != committed:
                errors.append(f"{report_path}: committed report differs from fresh execution")
            report_sha256 = hashlib.sha256(committed).hexdigest()
            errors.extend(
                _check_records(
                    candidate,
                    report_path,
                    report_sha256,
                    sources,
                    inputs,
                    setup_key,
                    setup_argv,
                    campaign_argv,
                    observed_binary_sha256,
                )
            )

    return errors, "Wave 4 Evidence checks passed: 2 fresh reports and 8 records."


if __name__ == "__main__":
    problems, summary = run_wave4_evidence_checks()
    if problems:
        print("Wave 4 Evidence checks failed:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print(summary)
