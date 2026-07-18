#!/usr/bin/env python3
"""Minimal repository quality gate.

Checks required project-memory files, local Markdown links, JSON syntax, the seven
canonical record schemas (including offline metaschema validation), and every record
fixture (valid, schema-invalid, link-invalid, link-valid) against their exact
diagnostic oracles. It also exercises the deterministic local loader's discovery,
normalization, phase, and import-edge fixtures, the tracer-scoped Stack adapter suite,
and ADR 0009's bounded Lean proof boundary. This is intentionally small so the tracer
bullet has an executable governance gate without locking in a larger toolchain.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record_check  # noqa: E402
import loader_fixture_check  # noqa: E402
import proof_fixture_check  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "docs/vision/constitution.md",
    "docs/research/synthesis.md",
    "docs/design/core-model.md",
    "docs/design/spec-language.md",
    "docs/design/adapter-protocol.md",
    "docs/design/evidence-model.md",
    "docs/design/compatibility.md",
    "docs/design/lifecycle.md",
    "docs/design/tracer-bullet.md",
    "docs/operations/multi-provider-workflow.md",
    ".agent/PLANS.md",
    "docs/exec-plans/active/0001-tracer-bullet.md",
    "semantic_packages/__init__.py",
    "semantic_packages/stack_realization.py",
    "semantic_packages/stack_adapter.py",
    "semantic_packages/stack_runner.py",
    "scripts/proof_check.py",
    "proofs/stack-pop-empty/StackPopEmpty.lean",
    "proofs/stack-pop-empty/manifest.json",
]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
JSON_EXCLUDED_DIRS = {".git", ".direnv", "node_modules"}


def check_required() -> list[str]:
    return [f"missing required file: {path}" for path in REQUIRED if not (ROOT / path).is_file()]


def check_markdown_links() -> list[str]:
    errors: list[str] = []
    for md in ROOT.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (md.parent / unquote(target)).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"{md.relative_to(ROOT)}: link escapes repository: {raw_target}")
                continue
            if not resolved.exists():
                errors.append(f"{md.relative_to(ROOT)}: broken link: {raw_target}")
    return errors


def check_json_syntax() -> list[str]:
    errors: list[str] = []
    for path in ROOT.rglob("*.json"):
        relative = path.relative_to(ROOT)
        if JSON_EXCLUDED_DIRS.intersection(relative.parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append(f"{relative}: invalid JSON: {error}")
    return errors


def run_adapter_checks() -> tuple[list[str], str]:
    sys.path.insert(0, str(ROOT))
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests" / "adapter"))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful():
        return [f"adapter conformance suite failed:\n{stream.getvalue()}"], ""
    return [], f"Adapter fixture checks passed: {result.testsRun} tests."


def run_proof_checks() -> tuple[list[str], str]:
    configured = Path(os.environ["LEAN"]) if os.environ.get("LEAN") else None
    if configured is None:
        discovered = shutil.which("lean")
        configured = Path(discovered) if discovered else None
    if configured is None:
        return ["proof gate requires Lean via LEAN or PATH"], ""
    errors = proof_fixture_check.check_fixture_inputs(configured)
    product_errors, groups = proof_fixture_check.check_product_contract(configured)
    errors.extend(product_errors)
    return errors, f"Proof fixture checks passed: {groups} contract groups."


def main() -> int:
    errors = check_required() + check_markdown_links() + check_json_syntax()
    record_errors, record_summary = record_check.run_fixture_checks()
    errors += record_errors
    loader_errors, loader_summary = loader_fixture_check.run_loader_fixture_checks()
    errors += loader_errors
    adapter_errors, adapter_summary = run_adapter_checks()
    errors += adapter_errors
    proof_errors, proof_summary = run_proof_checks()
    errors += proof_errors
    if errors:
        print("Repository checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(record_summary)
    print(loader_summary)
    print(adapter_summary)
    print(proof_summary)
    print("Repository checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
