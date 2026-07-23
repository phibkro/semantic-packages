#!/usr/bin/env python3
"""Minimal repository quality gate.

Checks required project-memory files, local Markdown links, JSON syntax, the canonical
record schemas (including offline metaschema validation), the registry manifest
schema, and every record fixture (valid, schema-invalid, link-invalid, link-valid) against their exact
diagnostic oracles. It also exercises the deterministic local loader's discovery,
normalization, phase, and import-edge fixtures, the tracer-scoped Stack adapter suite,
the independent Rust/TypeScript candidates and their bound Evidence reports, the
accepted actor-journey and repository-governance contracts, and ADR 0009's bounded
Lean proof boundary. Retained executable research probes freeze the observed boundary
between domain-shaped substrate and Stack-specific product authority.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record_check  # noqa: E402
import loader_fixture_check  # noqa: E402
import ordered_map_evidence_check  # noqa: E402
import ordered_map_profile_choice_evidence_check  # noqa: E402
import ordered_map_profile_choice_report_check  # noqa: E402
import ordered_map_report_check  # noqa: E402
import proof_fixture_check  # noqa: E402
import wave4_evidence_check  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "design-specs/0001-explicit-pspec-author-journey.md",
    "design-specs/0002-explicit-refinement-inspection-journey.md",
    "design-specs/0003-bounded-effect-separation-observation.md",
    "design-specs/0004-finite-resource-composition-inspection.md",
    "design-specs/0005-retry-safe-lease-session-package.md",
    "design-specs/0006-stable-norm2-numerical-kernel.md",
    "docs/vision/constitution.md",
    "docs/research/synthesis.md",
    "docs/research/ordered-map-probe.md",
    "docs/research/shared-human-authoring-surface.md",
    "docs/research/shared-human-authoring-options.md",
    "docs/design/core-model.md",
    "docs/design/ordered-map-tracer.md",
    "docs/design/ordered-map-profile-choice.md",
    "docs/design/system-map.md",
    "docs/design/user-journeys.md",
    "docs/design/spec-language.md",
    "docs/design/adapter-protocol.md",
    "docs/design/evidence-model.md",
    "docs/design/compatibility.md",
    "docs/design/lifecycle.md",
    "docs/design/tracer-bullet.md",
    "docs/operations/multi-provider-workflow.md",
    "docs/operations/explicit-pspec-author-observation.md",
    ".agent/PLANS.md",
    "docs/exec-plans/active/0003-cold-human-inspection.md",
    "docs/exec-plans/active/0006-shared-human-authoring-surface.md",
    "docs/exec-plans/completed/0007-explicit-refinement-inspection.md",
    "docs/exec-plans/completed/0008-bounded-effect-separation.md",
    "docs/exec-plans/completed/0009-finite-resource-composition.md",
    "docs/exec-plans/completed/0010-retry-safe-lease-session.md",
    "docs/exec-plans/completed/0011-stable-norm2-numerical-kernel.md",
    "docs/exec-plans/completed/0005-deployment-profile-choice.md",
    "docs/exec-plans/completed/0004-ordered-map-generality.md",
    "docs/exec-plans/completed/0001-tracer-bullet.md",
    "docs/exec-plans/completed/0002-actor-journeys.md",
    "semantic_packages/__init__.py",
    "semantic_packages/__main__.py",
    "semantic_packages/authoring.py",
    "semantic_packages/author_command.py",
    "semantic_packages/refinement.py",
    "semantic_packages/refinement_command.py",
    "semantic_packages/effect_separation.py",
    "semantic_packages/resource_algebra.py",
    "semantic_packages/lease_session.py",
    "semantic_packages/numerical_kernel.py",
    "semantic_packages/graph.py",
    "semantic_packages/maintenance.py",
    "semantic_packages/publication.py",
    "semantic_packages/resolver.py",
    "semantic_packages/stack_realization.py",
    "semantic_packages/stack_adapter.py",
    "semantic_packages/stack_runner.py",
    "semantic_packages/theory_projection.py",
    "scripts/proof_check.py",
    "scripts/effect_separation_probe.py",
    "scripts/check_change_metadata.py",
    "scripts/wave4_evidence_check.py",
    "scripts/ordered_map_evidence_check.py",
    "scripts/ordered_map_profile_choice_evidence_check.py",
    "scripts/ordered_map_profile_choice_report_check.py",
    "scripts/ordered_map_report_check.py",
    ".github/pull_request_template.md",
    "proofs/stack-pop-empty/StackPopEmpty.lean",
    "proofs/stack-pop-empty/manifest.json",
    "registry/stack/manifest.json",
    "registry/stack/successor-manifest.json",
    "docs/decisions/0014-revisioned-successor-source-set.md",
    "docs/decisions/0016-representation-neutral-authoring-boundary.md",
    "docs/decisions/0017-explicit-authoring-dependency-context.md",
    "schemas/registry-manifest.schema.json",
    "schemas/ordered-map-conformance-plan.schema.json",
    "registry/ordered-map/theory/records/ordered-map-spec.json",
    "registry/ordered-map/theory/dependencies/ordered-map-profile.json",
    "specs/stack.pspec",
    "specs/ordered-map.pspec",
    "specs/persistence-composition.pspec",
    "specs/lease-session.pspec",
    "registry/lease-session/manifest.json",
    "contracts/lease-session/campaign-plan.json",
    "specs/stable-norm2.pspec",
    "registry/stable-norm2/manifest.json",
    "contracts/stable-norm2/campaign-plan.json",
    "refinements/stack-0.1.0-to-0.2.0.prefine",
    "refinements/ordered-map-0.1.0-to-0.2.0.prefine",
    "fixtures/authoring/a1/stack-illustrative.pspec",
    "registry/ordered-map/profile-choice-manifest.json",
    "contracts/ordered-map/conformance-plan.json",
    "reports/ordered-map/rust-campaign-report.json",
    "reports/ordered-map/typescript-campaign-report.json",
    "fixtures/candidates/ordered-map/reorder_breaker/README.md",
    "fixtures/candidates/ordered-map/reorder_breaker/src/main.rs",
    "fixtures/candidates/ordered-map/reorder_breaker/src/ordered_map.rs",
    "fixtures/candidates/ordered-map/reorder_breaker/reorder-breaker-report.json",
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


def run_candidate_checks() -> tuple[list[str], str]:
    sys.path.insert(0, str(ROOT))
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests" / "candidates"))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful():
        return [f"cross-language candidate suite failed:\n{stream.getvalue()}"], ""
    return [], f"Cross-language candidate checks passed: {result.testsRun} tests."


def run_contract_checks(directory: str, label: str) -> tuple[list[str], str]:
    sys.path.insert(0, str(ROOT))
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests" / directory))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful():
        return [f"{label} suite failed:\n{stream.getvalue()}"], ""
    return [], f"{label} checks passed: {result.testsRun} tests."


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
    candidate_errors, candidate_summary = run_candidate_checks()
    errors += candidate_errors
    journey_errors, journey_summary = run_contract_checks(
        "journeys", "Actor journey"
    )
    errors += journey_errors
    research_errors, research_summary = run_contract_checks(
        "research", "Research probe"
    )
    errors += research_errors
    governance_errors, governance_summary = run_contract_checks(
        "governance", "Change governance"
    )
    errors += governance_errors
    try:
        wave4_errors, wave4_summary = wave4_evidence_check.run_wave4_evidence_checks()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        wave4_errors, wave4_summary = [f"Wave 4 Evidence check failed: {error}"], ""
    errors += wave4_errors
    ordered_map_errors, ordered_map_summary = (
        ordered_map_report_check.run_ordered_map_report_checks()
    )
    errors += ordered_map_errors
    ordered_map_evidence_errors, ordered_map_evidence_summary = (
        ordered_map_evidence_check.run_ordered_map_evidence_candidate_checks()
    )
    errors += ordered_map_evidence_errors
    profile_choice_report_errors, profile_choice_report_summary = (
        ordered_map_profile_choice_report_check.run_profile_choice_report_checks()
    )
    errors += profile_choice_report_errors
    profile_choice_evidence_errors, profile_choice_evidence_summary = (
        ordered_map_profile_choice_evidence_check.run_profile_choice_evidence_checks()
    )
    errors += profile_choice_evidence_errors
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
    print(candidate_summary)
    print(journey_summary)
    print(research_summary)
    print(governance_summary)
    print(wave4_summary)
    print(ordered_map_summary)
    print(ordered_map_evidence_summary)
    print(profile_choice_report_summary)
    print(profile_choice_evidence_summary)
    print(proof_summary)
    print("Repository checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
