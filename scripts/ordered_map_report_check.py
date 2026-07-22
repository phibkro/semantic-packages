#!/usr/bin/env python3
"""Rebuild and replay deterministic OrderedMap campaign report facts."""

from __future__ import annotations

import hashlib
import inspect
import json
import marshal
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

import semantic_packages  # noqa: E402
from scripts import record_check  # noqa: E402
from semantic_packages import canonical_artifact, ordered_map_contract  # noqa: E402
from semantic_packages.ordered_map_runner import run_ordered_map_conformance  # noqa: E402


PLAN = Path("contracts/ordered-map/conformance-plan.json")
RUNNER = Path("semantic_packages/ordered_map_runner.py")
HARNESS = (
    Path("semantic_packages/__init__.py"),
    Path("semantic_packages/ordered_map_contract.py"),
    Path("semantic_packages/canonical_artifact.py"),
    Path("scripts/record_check.py"),
    Path("schemas/ordered-map-conformance-plan.schema.json"),
)
SPECIFICATION = Path("registry/ordered-map/theory/records/ordered-map-spec.json")
PROFILE = Path("registry/ordered-map/theory/dependencies/ordered-map-profile.json")
REPORTS = {
    "ordered-map-rust": Path("reports/ordered-map/rust-campaign-report.json"),
    "ordered-map-typescript": Path("reports/ordered-map/typescript-campaign-report.json"),
    "ordered-map-reorder-breaker": Path(
        "fixtures/candidates/ordered-map/reorder_breaker/reorder-breaker-report.json"
    ),
}
SOURCES = {
    "ordered-map-rust": (
        Path("implementations/ordered-map/rust/src/main.rs"),
        Path("implementations/ordered-map/rust/src/ordered_map.rs"),
    ),
    "ordered-map-typescript": (
        Path("implementations/ordered-map/typescript/adapter.ts"),
        Path("implementations/ordered-map/typescript/ordered_map.ts"),
    ),
    "ordered-map-reorder-breaker": (
        Path("fixtures/candidates/ordered-map/reorder_breaker/src/main.rs"),
        Path("fixtures/candidates/ordered-map/reorder_breaker/src/ordered_map.rs"),
    ),
}
LIBRARY_VERSION_PROBE = (
    "import importlib.metadata as m;"
    "print('jsonschema '+m.version('jsonschema'));"
    "print('referencing '+m.version('referencing'))"
)


def _loaded_digest(path: str | os.PathLike[str] | None) -> bytes | None:
    return hashlib.sha256(Path(path).read_bytes()).digest() if path is not None else None


def _loaded_python_digest(module_or_object: Any) -> bytes | None:
    """Bind an imported Python module to the exact source that produced its cache."""
    module = (
        module_or_object
        if inspect.ismodule(module_or_object)
        else inspect.getmodule(module_or_object)
    )
    source_path = inspect.getsourcefile(module_or_object)
    if module is None or source_path is None:
        return None
    try:
        source = Path(source_path).read_bytes()
        cached_path = getattr(module, "__cached__", None)
        if cached_path is None or not Path(cached_path).is_file():
            compile(source, os.fspath(source_path), "exec", dont_inherit=True)
        else:
            cached = Path(cached_path).read_bytes()
            if len(cached) < 16:
                return None
            cached_code = marshal.loads(cached[16:])
            cached_filename = cached_code.co_filename
            fresh_code = compile(
                source,
                cached_filename,
                "exec",
                dont_inherit=True,
            )
            if fresh_code != cached_code:
                return None
    except (AttributeError, EOFError, OSError, SyntaxError, TypeError, ValueError):
        return None
    return hashlib.sha256(source).digest()


_LOADED_EXECUTABLE_SHA256 = {
    RUNNER: _loaded_python_digest(run_ordered_map_conformance),
    PLAN: _loaded_digest(ordered_map_contract._PLAN),
    HARNESS[0]: _loaded_python_digest(semantic_packages),
    HARNESS[1]: _loaded_python_digest(ordered_map_contract),
    HARNESS[2]: _loaded_python_digest(canonical_artifact),
    HARNESS[3]: _loaded_python_digest(record_check),
    HARNESS[4]: _loaded_digest(ordered_map_contract._SCHEMA),
}


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _sha256(root: Path, path: Path) -> str:
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def _canonical_sha256(root: Path, path: Path) -> str:
    document = json.loads((root / path).read_text(encoding="utf-8"))
    encoded = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _tool(environment: str, fallback: str) -> str:
    requested = os.environ.get(environment, fallback)
    resolved = shutil.which(requested)
    if resolved is None:
        raise RuntimeError(f"required tool {environment}/{requested} is unavailable")
    return resolved


def _require_bound_loaded_closure(root: Path) -> None:
    for relative, loaded_sha256 in _LOADED_EXECUTABLE_SHA256.items():
        requested = root / relative
        label = (
            "loaded runner bytes differ"
            if relative == RUNNER
            else "loaded executable closure bytes differ"
        )
        if (
            loaded_sha256 is None
            or requested.is_symlink()
            or not requested.is_file()
            or hashlib.sha256(requested.read_bytes()).digest() != loaded_sha256
        ):
            raise RuntimeError(f"{label} from requested input {requested}")


def _run(argv: Sequence[str], *, root: Path) -> subprocess.CompletedProcess[bytes]:
    process = subprocess.run(
        tuple(argv),
        cwd=root,
        shell=False,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"command failed ({process.returncode}): {list(argv)!r}; "
            f"stdout={process.stdout!r}; stderr={process.stderr!r}"
        )
    return process


def _tool_output(argv: Sequence[str], *, root: Path) -> list[str]:
    return _run(argv, root=root).stdout.decode("utf-8").splitlines()


def _raw_binding(root: Path, path: Path) -> dict[str, str]:
    return {"path": path.as_posix(), "sha256": _sha256(root, path)}


def _inputs(root: Path, candidate: str) -> dict[str, Any]:
    return {
        "harness": [_raw_binding(root, path) for path in HARNESS],
        "plan": {
            "path": PLAN.as_posix(),
            "rawSha256": _sha256(root, PLAN),
            "canonicalSha256": _canonical_sha256(root, PLAN),
        },
        "profile": _raw_binding(root, PROFILE),
        "runner": _raw_binding(root, RUNNER),
        "sources": [_raw_binding(root, path) for path in SOURCES[candidate]],
        "specification": _raw_binding(root, SPECIFICATION),
    }


def _outcome(report) -> dict[str, Any]:
    return {
        "result": report.result,
        "causes": list(report.causes),
        "planCanonicalSha256": report.plan_sha256,
        "requestCount": sum(case.request_count for case in report.cases),
        "declarations": [
            {
                "id": item.declaration_id,
                "observationCount": item.observation_count,
                "result": item.result,
                "causes": list(item.causes),
            }
            for item in report.declarations
        ],
        "cases": [
            {
                "id": case.case_id,
                "requestCount": case.request_count,
                "declarations": [
                    {
                        "id": item.declaration_id,
                        "observationCount": item.observation_count,
                        "result": item.result,
                        "causes": list(item.causes),
                    }
                    for item in case.declarations
                ],
            }
            for case in report.cases
        ],
        "events": [
            {
                "seq": item.seq,
                "case": item.case_id,
                "operation": item.operation,
                "event": item.event,
                "disposition": item.disposition,
            }
            for item in report.events
        ],
        "assumptions": list(report.assumptions),
        "exclusions": list(report.exclusions),
        "stderrSha256": hashlib.sha256(report.stderr).hexdigest(),
    }


def _packet(
    *,
    root: Path,
    candidate: str,
    role: str,
    commands: dict[str, list[str]],
    toolchain: dict[str, dict[str, Any]],
    binary_sha256: str | None,
    report,
) -> bytes:
    return canonical_json(
        {
            "formatVersion": 1,
            "kind": "ordered-map-campaign-report",
            "candidate": candidate,
            "packetRole": role,
            "protocol": "ordered-map-runner-json-v1",
            "inputs": _inputs(root, candidate),
            "toolchain": toolchain,
            "commands": commands,
            "binarySha256": binary_sha256,
            "outcome": _outcome(report),
        }
    )


def reproduce_ordered_map_reports(root: Path = ROOT) -> dict[Path, bytes]:
    """Build every packet and return fresh canonical report bytes without writing."""

    root = Path(root).resolve()
    _require_bound_loaded_closure(root)
    rustc = _tool("RUSTC", "rustc")
    gcc = _tool("GCC", "gcc")
    deno = _tool("DENO", "deno")
    harness_toolchain = {
        "python": {
            "command": "$PYTHON --version",
            "output": _tool_output((sys.executable, "--version"), root=root),
        },
        "pythonLibraries": {
            "command": "$PYTHON -c <locked-harness-library-version-probe>",
            "output": _tool_output(
                (sys.executable, "-c", LIBRARY_VERSION_PROBE), root=root
            ),
        },
    }
    rust_toolchain = {
        **harness_toolchain,
        "gcc": {
            "command": "$GCC --version",
            "output": _tool_output((gcc, "--version"), root=root),
        },
        "rustc": {
            "command": "$RUSTC --version --verbose",
            "output": _tool_output((rustc, "--version", "--verbose"), root=root),
        },
    }
    deno_toolchain = {
        **harness_toolchain,
        "deno": {
            "command": "$DENO --version",
            "output": _tool_output((deno, "--version"), root=root),
        }
    }

    rust_main = SOURCES["ordered-map-rust"][0]
    typescript_adapter, typescript_map = SOURCES["ordered-map-typescript"]
    breaker_main = SOURCES["ordered-map-reorder-breaker"][0]
    with tempfile.TemporaryDirectory(prefix="ordered-map-reports-") as raw:
        temporary = Path(raw)
        rust_binary = temporary / "ordered-map-rust"
        breaker_binary = temporary / "ordered-map-reorder-breaker"
        rust_build = (
            rustc,
            "--edition=2024",
            "-C",
            "opt-level=2",
            "-C",
            f"linker={gcc}",
            "-o",
            os.fspath(rust_binary),
            rust_main.as_posix(),
        )
        breaker_build = (
            rustc,
            "--edition=2024",
            "-C",
            "opt-level=2",
            "-C",
            f"linker={gcc}",
            "-o",
            os.fspath(breaker_binary),
            breaker_main.as_posix(),
        )
        deno_check = (
            deno,
            "check",
            "--no-config",
            "--no-lock",
            "--no-npm",
            "--no-remote",
            typescript_adapter.as_posix(),
            typescript_map.as_posix(),
        )
        _run(rust_build, root=root)
        _run(breaker_build, root=root)
        _run(deno_check, root=root)

        rust_report = run_ordered_map_conformance((os.fspath(rust_binary),))
        typescript_command = (
            deno,
            "run",
            "--no-config",
            "--no-lock",
            "--no-npm",
            "--no-remote",
            "--no-prompt",
            os.fspath(root / typescript_adapter),
        )
        typescript_report = run_ordered_map_conformance(typescript_command)
        breaker_report = run_ordered_map_conformance((os.fspath(breaker_binary),))

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
                rust_main.as_posix(),
            ],
            "campaign": ["$RUST_BINARY"],
        }
        typescript_commands = {
            "check": [
                "$DENO",
                "check",
                "--no-config",
                "--no-lock",
                "--no-npm",
                "--no-remote",
                typescript_adapter.as_posix(),
                typescript_map.as_posix(),
            ],
            "campaign": [
                "$DENO",
                "run",
                "--no-config",
                "--no-lock",
                "--no-npm",
                "--no-remote",
                "--no-prompt",
                typescript_adapter.as_posix(),
            ],
        }
        breaker_commands = {
            "build": [
                "$RUSTC",
                "--edition=2024",
                "-C",
                "opt-level=2",
                "-C",
                "linker=$GCC",
                "-o",
                "$BREAKER_BINARY",
                breaker_main.as_posix(),
            ],
            "campaign": ["$BREAKER_BINARY"],
        }
        return {
            REPORTS["ordered-map-rust"]: _packet(
                root=root,
                candidate="ordered-map-rust",
                role="candidate",
                commands=rust_commands,
                toolchain=rust_toolchain,
                binary_sha256=hashlib.sha256(rust_binary.read_bytes()).hexdigest(),
                report=rust_report,
            ),
            REPORTS["ordered-map-typescript"]: _packet(
                root=root,
                candidate="ordered-map-typescript",
                role="candidate",
                commands=typescript_commands,
                toolchain=deno_toolchain,
                binary_sha256=None,
                report=typescript_report,
            ),
            REPORTS["ordered-map-reorder-breaker"]: _packet(
                root=root,
                candidate="ordered-map-reorder-breaker",
                role="targeted-breaker",
                commands=breaker_commands,
                toolchain=rust_toolchain,
                binary_sha256=hashlib.sha256(breaker_binary.read_bytes()).hexdigest(),
                report=breaker_report,
            ),
        }


def compare_committed_reports(root: Path, fresh: dict[Path, bytes]) -> list[str]:
    errors: list[str] = []
    for path, expected in fresh.items():
        try:
            observed = (Path(root) / path).read_bytes()
        except OSError as error:
            errors.append(f"{path}: unable to read committed report: {error}")
            continue
        if observed != expected:
            errors.append(f"{path}: committed report differs from fresh execution")
    return errors


def input_binding_errors(root: Path = ROOT) -> list[str]:
    root = Path(root)
    errors: list[str] = []
    for candidate, report_path in REPORTS.items():
        try:
            report = json.loads((root / report_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{report_path}: unable to inspect bindings: {error}")
            continue
        try:
            expected = _inputs(root, candidate)
        except OSError as error:
            errors.append(f"{report_path}: unable to inspect bound input bytes: {error}")
            continue
        observed = report.get("inputs")
        if not isinstance(observed, dict):
            errors.append(f"{report_path}: inputs binding is absent or malformed")
            continue
        for name in ("harness", "plan", "profile", "runner", "sources", "specification"):
            if observed.get(name) != expected[name]:
                paths: list[str]
                if name == "sources":
                    paths = [path.as_posix() for path in SOURCES[candidate]]
                elif name == "harness":
                    paths = [path.as_posix() for path in HARNESS]
                else:
                    value = expected[name]
                    paths = [value["path"]]
                errors.append(
                    f"{report_path}: {name} binding differs from " + ", ".join(paths)
                )
    return errors


def run_ordered_map_report_checks(root: Path = ROOT) -> tuple[list[str], str]:
    errors = input_binding_errors(root)
    try:
        fresh = reproduce_ordered_map_reports(root)
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        errors.append(f"OrderedMap report reproduction failed: {error}")
    else:
        errors.extend(compare_committed_reports(root, fresh))
    return (
        errors,
        "OrderedMap report checks passed: 2 fresh candidate reports and 1 selective breaker.",
    )


if __name__ == "__main__":
    problems, summary = run_ordered_map_report_checks(ROOT)
    if problems:
        print("OrderedMap report checks failed:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print(summary)
