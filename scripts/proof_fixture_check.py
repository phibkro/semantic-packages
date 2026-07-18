#!/usr/bin/env python3
"""Red-first oracle for ADR 0009's bounded `pop-empty` proof boundary.

The harness contains no proof checker fallback.  It validates its committed JSON and
Lean test data, then invokes the future standalone `scripts/proof_check.py` in
disposable repository-shaped trees.  Stable product output is exit status plus
diagnostic code, source label, JSON pointer, and ordering; prose after `: ` is not
frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "proof_check.py"
ACTUAL_PROOF = ROOT / "proofs" / "stack-pop-empty" / "StackPopEmpty.lean"
ACTUAL_MANIFEST = ROOT / "proofs" / "stack-pop-empty" / "manifest.json"
FIXTURES = ROOT / "fixtures" / "proofs" / "v1"
TEMPLATE = FIXTURES / "manifest.template.json"
SPECIFICATION = ROOT / "fixtures" / "records" / "valid" / "stack-spec.json"
CLAIM = ROOT / "fixtures" / "records" / "valid" / "pop-empty-spec-claim.json"
PLACEHOLDER_EVIDENCE = (
    ROOT / "fixtures" / "records" / "valid" / "pop-empty-proof-evidence.json"
)
MANIFEST_LABEL = "proofs/stack-pop-empty/manifest.json"
SOURCE_LABEL = "proofs/stack-pop-empty/StackPopEmpty.lean"
EVIDENCE_LABEL = "fixtures/records/valid/pop-empty-proof-evidence.json"
SUCCESS = "Proof is valid: 0 diagnostics."
LEAN_VERSION = "4.30.0"
LEAN_COMMIT = "d024af099ca4bf2c86f649261ebf59565dc8c622"
DIAGNOSTIC_HEAD = re.compile(r"^[A-Z][A-Z0-9_]+ [^#]+#(?:/.*)?$")


@dataclass(frozen=True)
class Observation:
    exit_status: int
    signatures: list[str]
    stdout: str
    stderr: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _parse_signatures(stdout: str) -> tuple[list[str], list[str]]:
    if stdout.strip() == SUCCESS:
        return [], []
    signatures: list[str] = []
    errors: list[str] = []
    for line in stdout.splitlines():
        if not line:
            continue
        head = line.split(": ", 1)[0]
        if not DIAGNOSTIC_HEAD.fullmatch(head):
            errors.append(f"unrecognized output line {line!r}")
        else:
            signatures.append(head)
    return signatures, errors


def _invoke(
    checker: Path,
    cwd: Path,
    manifest: Path,
    lean: Path,
    *,
    evidence: Path | None = None,
    environment: dict[str, str] | None = None,
) -> tuple[Observation, list[str]]:
    command = [
        sys.executable,
        str(checker),
        "--manifest",
        str(manifest),
        "--lean",
        str(lean),
    ]
    if evidence is not None:
        command.extend(["--evidence", str(evidence)])
    process_environment = os.environ.copy()
    if environment:
        process_environment.update(environment)
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=process_environment,
    )
    signatures, parse_errors = _parse_signatures(completed.stdout)
    return (
        Observation(
            exit_status=completed.returncode,
            signatures=signatures,
            stdout=completed.stdout,
            stderr=completed.stderr,
        ),
        parse_errors,
    )


def _expect(
    name: str,
    checker: Path,
    cwd: Path,
    manifest: Path,
    lean: Path,
    exit_status: int,
    signatures: list[str],
    *,
    evidence: Path | None = None,
    environment: dict[str, str] | None = None,
) -> list[str]:
    observation, parse_errors = _invoke(
        checker,
        cwd,
        manifest,
        lean,
        evidence=evidence,
        environment=environment,
    )
    failures = [f"{name}: {error}" for error in parse_errors]
    if observation.exit_status != exit_status:
        failures.append(
            f"{name}: expected exit {exit_status}, got {observation.exit_status}; "
            f"stdout={observation.stdout!r}, stderr={observation.stderr!r}"
        )
    if observation.signatures != signatures:
        failures.append(
            f"{name}: expected diagnostics {signatures!r}, got "
            f"{observation.signatures!r}; stdout={observation.stdout!r}"
        )
    if observation.stderr:
        failures.append(f"{name}: expected empty stderr, got {observation.stderr!r}")
    return failures


def _materialize(
    raw: str,
    source_name: str = "positive.lean",
) -> tuple[Path, Path, Path, Path, Path, dict[str, Any]]:
    repository = Path(raw)
    checker = repository / "scripts" / "proof_check.py"
    source = repository / SOURCE_LABEL
    manifest_path = repository / MANIFEST_LABEL
    specification = repository / SPECIFICATION.relative_to(ROOT)
    claim = repository / CLAIM.relative_to(ROOT)
    evidence = repository / PLACEHOLDER_EVIDENCE.relative_to(ROOT)
    fake_lean = repository / FIXTURES.relative_to(ROOT) / "fake_lean.py"

    _copy(CHECKER, checker)
    _copy(FIXTURES / source_name, source)
    _copy(SPECIFICATION, specification)
    _copy(CLAIM, claim)
    _copy(PLACEHOLDER_EVIDENCE, evidence)
    _copy(FIXTURES / "fake_lean.py", fake_lean)
    fake_lean.write_text(
        fake_lean.read_text(encoding="utf-8").replace(
            "#!/usr/bin/env python3", f"#!{sys.executable}", 1
        ),
        encoding="utf-8",
    )
    fake_lean.chmod(0o755)

    substitutions = {
        "$SPECIFICATION_SHA256": _sha256(specification),
        "$CLAIM_SHA256": _sha256(claim),
        "$SOURCE_SHA256": _sha256(source),
        "$RUNNER_SHA256": _sha256(checker),
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    for token, value in substitutions.items():
        template = template.replace(token, value)
    manifest = json.loads(template)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return repository, checker, manifest_path, evidence, fake_lean, manifest


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _case(
    name: str,
    lean: Path,
    *,
    source_name: str = "positive.lean",
    mutate: Callable[[dict[str, Any]], None] | None = None,
    expected: str | None = None,
    evidence: bool = False,
    fake_mode: str | None = None,
    malformed_manifest: bool = False,
) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-proof-fixture-") as raw:
        (
            repository,
            checker,
            manifest_path,
            _evidence_path,
            fake_lean,
            manifest,
        ) = _materialize(raw, source_name)
        if mutate:
            mutate(manifest)
        if malformed_manifest:
            manifest_path.write_text("{ not json\n", encoding="utf-8")
        else:
            _write_manifest(manifest_path, manifest)
        selected_lean = fake_lean if fake_mode else lean
        environment = {"FAKE_LEAN_MODE": fake_mode} if fake_mode else None
        signatures = [expected] if expected else []
        return _expect(
            name,
            checker,
            repository,
            Path(MANIFEST_LABEL),
            selected_lean,
            1 if expected else 0,
            signatures,
            evidence=Path(EVIDENCE_LABEL) if evidence else None,
            environment=environment,
        )


def _run_lean(lean: Path, source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(lean), "--trust=0", "--json", str(source)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def check_fixture_inputs(lean: Path | None) -> list[str]:
    failures: list[str] = []
    try:
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        failures.append(f"fixture manifest template is valid JSON: {error}")
        template = {}
    if template.get("expectedStatement") != (
        "∀ (A : Type u), pop (empty : ObservedStack A) = Option.none"
    ):
        failures.append("fixture manifest pins the exact universal expected statement")
    for source in sorted(FIXTURES.glob("*.lean")):
        try:
            source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            failures.append(f"{source.name} is readable UTF-8: {error}")
    positive = (FIXTURES / "positive.lean").read_text(encoding="utf-8")
    if "import " in positive or "Realization" in positive or "adapter" in positive:
        failures.append("positive proof model imports no Realization or adapter code")
    if "(A : Type u)" not in positive or "ObservedStack" not in positive:
        failures.append("positive proof model is universal over the observed Stack model")

    if lean is None:
        return failures
    version = subprocess.run(
        [str(lean), "--version"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if (
        version.returncode != 0
        or LEAN_VERSION not in version.stdout
        or LEAN_COMMIT not in version.stdout
    ):
        failures.append(
            "fixture syntax checker is exact Lean 4.30.0: "
            f"exit={version.returncode}, stdout={version.stdout!r}, stderr={version.stderr!r}"
        )
        return failures

    expected_exit = {
        "positive.lean": 0,
        "false-theorem.lean": 1,
        "sorry.lean": 1,
        "injected-axiom.lean": 0,
        "classical-choice.lean": 0,
        "wrong-true-statement.lean": 0,
        "finite-specialization.lean": 0,
        "warning-policy-too-late.lean": 0,
    }
    for name, status in expected_exit.items():
        completed = _run_lean(lean, FIXTURES / name)
        if completed.returncode != status:
            failures.append(
                f"{name} direct Lean control: expected exit {status}, got "
                f"{completed.returncode}; stdout={completed.stdout!r}, "
                f"stderr={completed.stderr!r}"
            )

    axiom_expectations = {
        "positive.lean": "does not depend on any axioms",
        "injected-axiom.lean": "depends on axioms",
        "classical-choice.lean": "depends on axioms",
    }
    with tempfile.TemporaryDirectory(prefix="semantic-proof-axioms-") as raw:
        directory = Path(raw)
        for name, expected in axiom_expectations.items():
            augmented = directory / name
            augmented.write_text(
                (FIXTURES / name).read_text(encoding="utf-8")
                + "\n#print axioms stack_pop_empty\n",
                encoding="utf-8",
            )
            completed = _run_lean(lean, augmented)
            if completed.returncode != 0 or expected not in completed.stdout:
                failures.append(
                    f"{name} axiom audit: expected {expected!r}; exit="
                    f"{completed.returncode}, stdout={completed.stdout!r}, "
                    f"stderr={completed.stderr!r}"
                )
    return failures


def check_product_contract(lean: Path) -> tuple[list[str], int]:
    failures: list[str] = []
    groups = 0

    def run(*args: Any, **kwargs: Any) -> None:
        nonlocal groups
        groups += 1
        failures.extend(_case(*args, lean=lean, **kwargs))

    run("clean universal model satisfies the proof boundary")
    run(
        "a false theorem is a proof error, not a semantic challenge",
        source_name="false-theorem.lean",
        expected=f"PROOF_LEAN_CHECK_FAILED {SOURCE_LABEL}#",
    )
    run(
        "sorry is rejected even though default Lean may exit zero",
        source_name="sorry.lean",
        expected=f"PROOF_SORRY {SOURCE_LABEL}#",
    )
    run(
        "a declared axiom is rejected",
        source_name="injected-axiom.lean",
        expected=f"PROOF_AXIOM_DEPENDENCY {SOURCE_LABEL}#",
    )
    run(
        "an axiom-producing classical control is rejected",
        source_name="classical-choice.lean",
        expected=f"PROOF_AXIOM_DEPENDENCY {SOURCE_LABEL}#",
    )
    run(
        "the theorem name cannot hide a wrong but true statement",
        source_name="wrong-true-statement.lean",
        expected=f"PROOF_STATEMENT_MISMATCH {MANIFEST_LABEL}#/expectedStatement",
    )
    run(
        "a finite specialization is not universal proof",
        source_name="finite-specialization.lean",
        expected=f"PROOF_STATEMENT_MISMATCH {MANIFEST_LABEL}#/expectedStatement",
    )
    run(
        "warning policy must precede every declaration",
        source_name="warning-policy-too-late.lean",
        expected=f"PROOF_WARNING_POLICY_ORDER {SOURCE_LABEL}#",
    )
    run(
        "the declaration link is exact",
        mutate=lambda manifest: manifest.__setitem__("declarationId", "pop-push"),
        expected=f"PROOF_LINK_MISMATCH {MANIFEST_LABEL}#/declarationId",
    )
    run(
        "the Claim link is exact",
        mutate=lambda manifest: manifest["claim"]["reference"].__setitem__(
            "id", "another-claim"
        ),
        expected=f"PROOF_LINK_MISMATCH {MANIFEST_LABEL}#/claim/reference",
    )
    run(
        "a stale Specification digest is rejected",
        mutate=lambda manifest: manifest["specification"].__setitem__(
            "sha256", "0" * 64
        ),
        expected=(
            f"PROOF_INPUT_DIGEST_MISMATCH "
            f"{MANIFEST_LABEL}#/specification/sha256"
        ),
    )
    run(
        "a stale Claim digest is rejected",
        mutate=lambda manifest: manifest["claim"].__setitem__("sha256", "0" * 64),
        expected=f"PROOF_INPUT_DIGEST_MISMATCH {MANIFEST_LABEL}#/claim/sha256",
    )
    run(
        "a stale proof-source digest is rejected",
        mutate=lambda manifest: manifest["source"].__setitem__("sha256", "0" * 64),
        expected=f"PROOF_SOURCE_DIGEST_MISMATCH {MANIFEST_LABEL}#/source/sha256",
    )
    run(
        "a stale checker digest is rejected",
        mutate=lambda manifest: manifest["runner"].__setitem__("sha256", "0" * 64),
        expected=f"PROOF_RUNNER_DIGEST_MISMATCH {MANIFEST_LABEL}#/runner/sha256",
    )
    run(
        "the exact Lean version is checked",
        mutate=lambda manifest: manifest["tool"].__setitem__("version", "4.29.0"),
        expected=f"PROOF_TOOL_VERSION_MISMATCH {MANIFEST_LABEL}#/tool/version",
    )
    run(
        "the exact Lean commit is checked",
        mutate=lambda manifest: manifest["tool"].__setitem__("commit", "0" * 40),
        expected=f"PROOF_TOOL_VERSION_MISMATCH {MANIFEST_LABEL}#/tool/commit",
    )
    run(
        "missing no-axioms output is rejected despite exit zero",
        fake_mode="missing-axiom-audit",
        expected=f"PROOF_AXIOM_AUDIT_MISSING {SOURCE_LABEL}#",
    )
    run(
        "invalid no-axioms output is rejected despite exit zero",
        fake_mode="invalid-axiom-audit",
        expected=f"PROOF_AXIOM_AUDIT_INVALID {SOURCE_LABEL}#",
    )
    run(
        "the accepted fixture-only Evidence cannot be reused",
        evidence=True,
        expected=(
            f"PROOF_FIXTURE_EVIDENCE_FORBIDDEN "
            f"{EVIDENCE_LABEL}#/environment/checker"
        ),
    )
    run(
        "malformed manifest JSON is stable input failure",
        malformed_manifest=True,
        expected=f"PROOF_MANIFEST_JSON {MANIFEST_LABEL}#",
    )

    def remove_statement(manifest: dict[str, Any]) -> None:
        del manifest["expectedStatement"]

    run(
        "a missing manifest field is rejected",
        mutate=remove_statement,
        expected=f"PROOF_MANIFEST_SHAPE {MANIFEST_LABEL}#/expectedStatement",
    )
    run(
        "an absolute proof path is rejected",
        mutate=lambda manifest: manifest["source"].__setitem__(
            "path", "/tmp/StackPopEmpty.lean"
        ),
        expected=f"PROOF_PATH_INVALID {MANIFEST_LABEL}#/source/path",
    )
    run(
        "a parent-traversal proof path is rejected",
        mutate=lambda manifest: manifest["source"].__setitem__(
            "path", "proofs/stack-pop-empty/../../../outside.lean"
        ),
        expected=f"PROOF_PATH_INVALID {MANIFEST_LABEL}#/source/path",
    )
    run(
        "a missing proof path is rejected",
        mutate=lambda manifest: manifest["source"].__setitem__(
            "path", "proofs/stack-pop-empty/Missing.lean"
        ),
        expected=f"PROOF_PATH_NOT_FOUND {MANIFEST_LABEL}#/source/path",
    )

    groups += 1
    failures.extend(
        _expect(
            "the actual product proof boundary exists and passes",
            CHECKER,
            ROOT,
            ACTUAL_MANIFEST.relative_to(ROOT),
            lean,
            0,
            [],
        )
    )
    return failures, groups


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lean",
        type=Path,
        help="explicit Lean executable; defaults to LEAN or PATH lookup",
    )
    arguments = parser.parse_args()
    configured = arguments.lean or (
        Path(os.environ["LEAN"]) if os.environ.get("LEAN") else None
    )
    if configured is None:
        discovered = shutil.which("lean")
        configured = Path(discovered) if discovered else None

    failures = check_fixture_inputs(configured)
    missing = []
    if not CHECKER.is_file():
        missing.append("future checker scripts/proof_check.py is absent")
    if not ACTUAL_PROOF.is_file():
        missing.append("future proof proofs/stack-pop-empty/StackPopEmpty.lean is absent")
    if not ACTUAL_MANIFEST.is_file():
        missing.append("future proof manifest proofs/stack-pop-empty/manifest.json is absent")
    if missing:
        failures.extend(missing)
        print("Proof fixture checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    if configured is None:
        failures.append(
            "future proof checker exists but no explicit Lean executable is available"
        )
        groups = 0
    else:
        product_failures, groups = check_product_contract(configured)
        failures.extend(product_failures)
    if failures:
        print("Proof fixture checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Proof fixture checks passed: {groups} contract groups.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
