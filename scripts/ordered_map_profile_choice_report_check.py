#!/usr/bin/env python3
"""Reproduce the two exact deployment-profile OrderedMap campaign reports.

The accepted runner remains unchanged. This wrapper authenticates one exact P2a plan,
temporarily supplies its detached observation at the runner's existing plan boundary,
and records that wrapper plus the complete executable closure in each report. It does
not create Claims, Evidence, authority, or an acceptance decision.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

import semantic_packages  # noqa: E402
from scripts import ordered_map_report_check as base  # noqa: E402
from scripts import record_check  # noqa: E402
from semantic_packages import canonical_artifact, ordered_map_contract  # noqa: E402
from semantic_packages.ordered_map_runner import run_ordered_map_conformance  # noqa: E402


RUNNER = Path("semantic_packages/ordered_map_runner.py")
SCHEMA = Path("schemas/ordered-map-conformance-plan.schema.json")
SPECIFICATION = Path("registry/ordered-map/theory/records/ordered-map-spec.json")
HARNESS = (
    Path("semantic_packages/__init__.py"),
    Path("semantic_packages/ordered_map_contract.py"),
    Path("semantic_packages/canonical_artifact.py"),
    Path("scripts/record_check.py"),
    Path("scripts/ordered_map_report_check.py"),
    Path("scripts/ordered_map_profile_choice_report_check.py"),
    SCHEMA,
)
CAMPAIGNS = {
    "ordered-map-rust": {
        "plan": Path("contracts/ordered-map/profile-choice/native-conformance-plan.json"),
        "planRawSha256": "4ad983583dc4558c9321d3c2b7a8089f7f41aa25e391b5ffeac5875a9a28d932",
        "planCanonicalSha256": "8cd414cf900f571994e081788cebf5f5c7c73964efd43f7384c2089b1fb0b472",
        "profile": Path("registry/ordered-map/profile-choice/profiles/records/ordered-map-native-process.json"),
        "profileSha256": "788481758572ec2d94d3e97b009b9ca30e0322d07b93dcb37b6417243fffc450",
        "report": Path("reports/ordered-map/profile-choice/rust-native-campaign-report.json"),
        "sources": (
            Path("implementations/ordered-map/rust/src/main.rs"),
            Path("implementations/ordered-map/rust/src/ordered_map.rs"),
        ),
    },
    "ordered-map-typescript": {
        "plan": Path("contracts/ordered-map/profile-choice/deno-conformance-plan.json"),
        "planRawSha256": "bedd5199c9958ea127c77f4f8646a71a282305b88487854cd2ce4338d76ad0d9",
        "planCanonicalSha256": "57cdeb9d881a272e9c591920cc6bf43d426cbd6310951a99c90797aa91cdb5b4",
        "profile": Path("registry/ordered-map/profile-choice/profiles/records/ordered-map-deno-sandbox.json"),
        "profileSha256": "4629a98d62ae9ab59bebefcab5eab2306eeef8df0b19f80b6cc594f1f5adb1bf",
        "report": Path("reports/ordered-map/profile-choice/typescript-deno-campaign-report.json"),
        "sources": (
            Path("implementations/ordered-map/typescript/adapter.ts"),
            Path("implementations/ordered-map/typescript/ordered_map.ts"),
        ),
    },
}


def _sha256(root: Path, path: Path) -> str:
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def _raw_binding(root: Path, path: Path) -> dict[str, str]:
    return {"path": path.as_posix(), "sha256": _sha256(root, path)}


def _require_bound_loaded_closure(root: Path) -> None:
    loaded = {
        RUNNER: base._loaded_python_digest(run_ordered_map_conformance),
        HARNESS[0]: base._loaded_python_digest(semantic_packages),
        HARNESS[1]: base._loaded_python_digest(ordered_map_contract),
        HARNESS[2]: base._loaded_python_digest(canonical_artifact),
        HARNESS[3]: base._loaded_python_digest(record_check),
        HARNESS[4]: base._loaded_python_digest(base),
        HARNESS[5]: base._loaded_python_digest(sys.modules[__name__]),
        HARNESS[6]: base._loaded_digest(ROOT / SCHEMA),
    }
    for relative, loaded_sha256 in loaded.items():
        requested = root / relative
        if (
            loaded_sha256 is None
            or requested.is_symlink()
            or not requested.is_file()
            or hashlib.sha256(requested.read_bytes()).digest() != loaded_sha256
        ):
            raise RuntimeError(
                f"loaded executable closure bytes differ from requested input {requested}"
            )


def _capture_plan(root: Path, campaign: dict[str, Any]):
    observation = canonical_artifact.inspect_json_artifact(
        root / campaign["plan"],
        schema_path=root / SCHEMA,
        expected_raw_sha256=campaign["planRawSha256"],
        expected_canonical_sha256=campaign["planCanonicalSha256"],
        label="OrderedMap exact deployment-profile conformance plan",
    )
    if not observation.ok:
        raise RuntimeError(
            "profile-bound plan capture failed: "
            + "; ".join(item.code for item in observation.diagnostics)
        )
    return observation


def _campaign_worker(candidate: str, command: tuple[str, ...]) -> dict[str, Any]:
    """Run one substituted plan inside this short-lived worker interpreter."""

    campaign = CAMPAIGNS[candidate]
    plan = _capture_plan(ROOT, campaign)
    original = ordered_map_contract.inspect_conformance_plan
    ordered_map_contract.inspect_conformance_plan = lambda: plan
    try:
        report = run_ordered_map_conformance(command)
        return base._outcome(report)
    finally:
        ordered_map_contract.inspect_conformance_plan = original


def _run_isolated_campaign(
    root: Path,
    candidate: str,
    command: tuple[str, ...],
) -> dict[str, Any]:
    """Run the plan substitution in a child interpreter, never in this process."""

    worker = root / "scripts/ordered_map_profile_choice_report_check.py"
    process = base._run(
        (
            sys.executable,
            os.fspath(worker),
            "--campaign-worker",
            candidate,
            "--",
            *command,
        ),
        root=root,
    )
    try:
        outcome = json.loads(process.stdout)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"profile campaign worker returned invalid JSON: {error}") from error
    if not isinstance(outcome, dict):
        raise RuntimeError("profile campaign worker returned a non-object outcome")
    return outcome


def _inputs(root: Path, candidate: str) -> dict[str, Any]:
    campaign = CAMPAIGNS[candidate]
    return {
        "harness": [_raw_binding(root, path) for path in HARNESS],
        "plan": {
            "path": campaign["plan"].as_posix(),
            "rawSha256": campaign["planRawSha256"],
            "canonicalSha256": campaign["planCanonicalSha256"],
        },
        "profile": {
            "path": campaign["profile"].as_posix(),
            "sha256": campaign["profileSha256"],
        },
        "runner": _raw_binding(root, RUNNER),
        "sources": [_raw_binding(root, path) for path in campaign["sources"]],
        "specification": _raw_binding(root, SPECIFICATION),
    }


def _packet(
    *,
    root: Path,
    candidate: str,
    commands: dict[str, list[str]],
    toolchain: dict[str, dict[str, Any]],
    binary_sha256: str | None,
    outcome: dict[str, Any],
) -> bytes:
    return base.canonical_json(
        {
            "formatVersion": 1,
            "kind": "ordered-map-campaign-report",
            "candidate": candidate,
            "packetRole": "profile-choice-candidate",
            "protocol": "ordered-map-runner-json-v1",
            "inputs": _inputs(root, candidate),
            "toolchain": toolchain,
            "commands": commands,
            "binarySha256": binary_sha256,
            "outcome": outcome,
        }
    )


def reproduce_profile_choice_reports(root: Path = ROOT) -> dict[Path, bytes]:
    """Execute both exact profile-bound campaigns without writing reports."""

    root = Path(root).resolve()
    _require_bound_loaded_closure(root)
    for campaign in CAMPAIGNS.values():
        if _sha256(root, campaign["plan"]) != campaign["planRawSha256"]:
            raise RuntimeError(f"plan bytes differ: {campaign['plan']}")
        if _sha256(root, campaign["profile"]) != campaign["profileSha256"]:
            raise RuntimeError(f"profile bytes differ: {campaign['profile']}")

    rustc = base._tool("RUSTC", "rustc")
    gcc = base._tool("GCC", "gcc")
    deno = base._tool("DENO", "deno")
    harness_toolchain = {
        "python": {
            "command": "$PYTHON --version",
            "output": base._tool_output((sys.executable, "--version"), root=root),
        },
        "pythonLibraries": {
            "command": "$PYTHON -c <locked-harness-library-version-probe>",
            "output": base._tool_output(
                (sys.executable, "-c", base.LIBRARY_VERSION_PROBE), root=root
            ),
        },
    }
    rust_toolchain = {
        **harness_toolchain,
        "gcc": {
            "command": "$GCC --version",
            "output": base._tool_output((gcc, "--version"), root=root),
        },
        "rustc": {
            "command": "$RUSTC --version --verbose",
            "output": base._tool_output((rustc, "--version", "--verbose"), root=root),
        },
    }
    deno_toolchain = {
        **harness_toolchain,
        "deno": {
            "command": "$DENO --version",
            "output": base._tool_output((deno, "--version"), root=root),
        },
    }

    rust_sources = CAMPAIGNS["ordered-map-rust"]["sources"]
    typescript_sources = CAMPAIGNS["ordered-map-typescript"]["sources"]
    with tempfile.TemporaryDirectory(prefix="ordered-map-profile-choice-") as raw:
        rust_binary = Path(raw) / "ordered-map-rust"
        rust_build = (
            rustc,
            "--edition=2024",
            "-C",
            "opt-level=2",
            "-C",
            f"linker={gcc}",
            "-o",
            os.fspath(rust_binary),
            rust_sources[0].as_posix(),
        )
        deno_check = (
            deno,
            "check",
            "--no-config",
            "--no-lock",
            "--no-npm",
            "--no-remote",
            *(path.as_posix() for path in typescript_sources),
        )
        base._run(rust_build, root=root)
        base._run(deno_check, root=root)

        rust_outcome = _run_isolated_campaign(
            root,
            "ordered-map-rust",
            (os.fspath(rust_binary),),
        )
        typescript_command = (
            deno,
            "run",
            "--no-config",
            "--no-lock",
            "--no-npm",
            "--no-remote",
            "--no-prompt",
            os.fspath(root / typescript_sources[0]),
        )
        typescript_outcome = _run_isolated_campaign(
            root,
            "ordered-map-typescript",
            typescript_command,
        )
        rust_commands = {
            "build": [
                "$RUSTC",
                "--edition=2024",
                "-C",
                "opt-level=2",
                "-C",
                "linker=$GCC",
                "-o",
                "$RUST_BINARY",
                rust_sources[0].as_posix(),
            ],
            "campaign": [
                "$PYTHON",
                "scripts/ordered_map_profile_choice_report_check.py",
                "--campaign-worker",
                "ordered-map-rust",
                "--",
                "$RUST_BINARY",
            ],
        }
        typescript_commands = {
            "check": [
                "$DENO",
                "check",
                "--no-config",
                "--no-lock",
                "--no-npm",
                "--no-remote",
                *(path.as_posix() for path in typescript_sources),
            ],
            "campaign": [
                "$PYTHON",
                "scripts/ordered_map_profile_choice_report_check.py",
                "--campaign-worker",
                "ordered-map-typescript",
                "--",
                "$DENO",
                "run",
                "--no-config",
                "--no-lock",
                "--no-npm",
                "--no-remote",
                "--no-prompt",
                typescript_sources[0].as_posix(),
            ],
        }
        return {
            CAMPAIGNS["ordered-map-rust"]["report"]: _packet(
                root=root,
                candidate="ordered-map-rust",
                commands=rust_commands,
                toolchain=rust_toolchain,
                binary_sha256=hashlib.sha256(rust_binary.read_bytes()).hexdigest(),
                outcome=rust_outcome,
            ),
            CAMPAIGNS["ordered-map-typescript"]["report"]: _packet(
                root=root,
                candidate="ordered-map-typescript",
                commands=typescript_commands,
                toolchain=deno_toolchain,
                binary_sha256=None,
                outcome=typescript_outcome,
            ),
        }


def input_binding_errors(root: Path = ROOT) -> list[str]:
    root = Path(root).resolve()
    errors: list[str] = []
    for candidate, campaign in CAMPAIGNS.items():
        report_path = campaign["report"]
        try:
            report = json.loads((root / report_path).read_text(encoding="utf-8"))
            expected = _inputs(root, candidate)
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{report_path}: unable to inspect bindings: {error}")
            continue
        if report.get("inputs") != expected:
            errors.append(f"{report_path}: exact input binding differs")
        if report.get("packetRole") != "profile-choice-candidate":
            errors.append(f"{report_path}: packet role differs")
        outcome = report.get("outcome")
        if not isinstance(outcome, dict) or outcome.get("planCanonicalSha256") != campaign["planCanonicalSha256"]:
            errors.append(f"{report_path}: executed plan digest differs")
    return errors


def run_profile_choice_report_checks(root: Path = ROOT) -> tuple[list[str], str]:
    errors = input_binding_errors(root)
    try:
        fresh = reproduce_profile_choice_reports(root)
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        errors.append(f"OrderedMap profile-choice report reproduction failed: {error}")
    else:
        errors.extend(base.compare_committed_reports(root, fresh))
    return (
        errors,
        "OrderedMap profile-choice report checks passed: 2 fresh profile-bound reports.",
    )


if __name__ == "__main__" and len(sys.argv) >= 5 and sys.argv[1] == "--campaign-worker":
    if sys.argv[3] != "--" or sys.argv[2] not in CAMPAIGNS:
        raise SystemExit("invalid profile campaign worker invocation")
    sys.stdout.buffer.write(
        base.canonical_json(_campaign_worker(sys.argv[2], tuple(sys.argv[4:])))
    )
elif __name__ == "__main__":
    problems, summary = run_profile_choice_report_checks(ROOT)
    if problems:
        print("OrderedMap profile-choice report checks failed:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print(summary)
