"""Bounded cross-domain observation of semantic/effect separation.

The observation composes two exact repository-owned conformance runners.  It does not
discover packages, execute registry metadata, construct Evidence, or infer effects
outside adapter-reported invocation events.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from .ordered_map_runner import run_ordered_map_conformance
from .stack_runner import default_stack_conformance_plan, run_stack_conformance


_ROLES = ("quiet", "optional", "forbidden", "unspecified", "adapter-error")
_STACK_MODES = (
    "reference",
    "optional-event",
    "forbidden-event",
    "unspecified-event",
    "status-error",
)
_ORDERED_MAP_MODES = (
    "reference",
    "optional-event",
    "forbidden-event",
    "unspecified-event",
    "adapter-error-forbidden",
)
_STACK_PLAN_SHA256 = (
    "e055eab406683a01a32e8b563ef2e299169ddb2745685b5ad3ffae3297d93f6c"
)
_ORDERED_MAP_PLAN_SHA256 = (
    "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a"
)
_ASSUMPTIONS = ("adapter-faithfulness", "adapter-event-completeness")
_EXCLUSIONS = ("adapter-external-effects", "realization-steps")
_PROJECTION_SHA256 = {
    "stack": (
        "fe57b959a04840767112f9963c9587c74e4a7bf8ad5fcb923ce5b2d85bf6af8a",
        "74ba5130525995263889ec3e3c8f59bccb6cc21f4164aee452e1a7878528fa4b",
    ),
    "ordered-map": (
        "33c51b19a11fda2086a72d465b3ff7cd1df62bfecb3d6664aecbf2fbcf6b3b48",
        "498363d24c4a81834238d5a9efae18f0faafeca394ccc7859ecac4b9ec042d12",
    ),
}
_LEDGER_SHA256 = {
    "stack": (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
        "53941bd7a53b09d60ab142e43e2244de00fe6d6ed0da044242297d7fc7a38abe",
        "2a589fc440ac72c225ea0b6b7793a0919d88b51f0d921099f4c6321022e32675",
        "8736efed677dbef68c3e89770c63c1b811aec11ff0aaf89a3e273edab23b0d9e",
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    ),
    "ordered-map": (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
        "3808991f4e71676006a8585c86d8d0ea462749dab0e7f1ce4befe2ecb0ffbd3e",
        "be76489a71aef9e60da5a1261dc0a6f14a003f9ef180f784b9eae34441ed5148",
        "e586200bc51149b0c915c1cfa1358e35f98330125f1a630516cd2905d70d0f8e",
        "22b965b4d6a3436e0b42a460b3cdc14ab9b886a0b1a8fee167beb9921f2b9730",
    ),
}
_ORDERED_MAP_EFFECT_SURFACE_SHA256 = (
    "c1c1a60f0456218aae8d6ad0c4dd032caf24ff4d4a6f22479d9ac447b3b007e3",
    "c1c1a60f0456218aae8d6ad0c4dd032caf24ff4d4a6f22479d9ac447b3b007e3",
    "57a7f669667c9803af5534349ebda6860c667e9b648c92b1ace5c0326159f401",
    "c1c1a60f0456218aae8d6ad0c4dd032caf24ff4d4a6f22479d9ac447b3b007e3",
    "cd33da8df12f16b207f95dd25045963925d1f3f61d07169877d202ae3bdb42e2",
)


@dataclass(frozen=True)
class ObservationProblem(Exception):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def _problem(code: str, message: str) -> None:
    raise ObservationProblem(code, message)


def _canonical_sha256(value: Any) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _stack_projection(report: Any) -> dict[str, Any]:
    return {
        "observations": [
            {
                "caseId": item.case_id,
                "declarationId": item.declaration_id,
                "result": item.result,
                "expectedTopFirst": list(item.expected_top_first),
                "observedTopFirst": list(item.observed_top_first),
                "causes": list(item.causes),
            }
            for item in report.observations
        ],
        "declarations": [
            {
                "declarationId": item.declaration_id,
                "result": item.result,
                "causes": list(item.causes),
            }
            for item in report.declaration_outcomes
            if item.declaration_id != "stack-effects"
        ],
    }


def _ordered_map_declaration(item: Any) -> dict[str, Any]:
    return {
        "declarationId": item.declaration_id,
        "observationCount": item.observation_count,
        "result": item.result,
        "causes": list(item.causes),
    }


def _ordered_map_projection(report: Any) -> dict[str, Any]:
    return {
        "cases": [
            {
                "caseId": case.case_id,
                "requestCount": case.request_count,
                "declarations": [
                    _ordered_map_declaration(item)
                    for item in case.declarations
                    if item.declaration_id != "ordered-map-effects"
                ],
            }
            for case in report.cases
        ],
        "declarations": [
            _ordered_map_declaration(item)
            for item in report.declarations
            if item.declaration_id != "ordered-map-effects"
        ],
    }


def _stack_ledger(report: Any) -> list[dict[str, Any]]:
    return [
        {"event": event, "disposition": disposition}
        for event, disposition in report.events
    ]


def _ordered_map_ledger(report: Any) -> list[dict[str, Any]]:
    return [
        {
            "seq": item.seq,
            "caseId": item.case_id,
            "operation": item.operation,
            "event": item.event,
            "disposition": item.disposition,
        }
        for item in report.events
    ]


def _effect_outcome(report: Any, attribute: str, effect_id: str) -> Any:
    outcomes = getattr(report, attribute)
    matches = [item for item in outcomes if item.declaration_id == effect_id]
    if len(matches) != 1:
        _problem(
            "EFFECT_DECLARATION_CENSUS",
            f"{effect_id} must occur exactly once in the domain report",
        )
    return matches[0]


def _validate_common(report: Any, domain: str, expected_plan: str) -> None:
    if report.plan_sha256 != expected_plan:
        _problem("PLAN_BINDING", f"{domain} report does not bind the exact campaign")
    if tuple(report.assumptions) != _ASSUMPTIONS:
        _problem("ASSUMPTION_DRIFT", f"{domain} assumptions changed")
    if tuple(report.exclusions) != _EXCLUSIONS:
        _problem("EXCLUSION_DRIFT", f"{domain} exclusions changed")


def _validate_ledger(
    domain: str,
    role: str,
    ledger: list[dict[str, Any]],
    role_index: int,
) -> None:
    if role == "quiet":
        expected_count = 0
        expected_event = None
        expected_disposition = None
    elif role == "optional":
        expected_count = 177 if domain == "stack" else 30
        expected_event = "debug.emit"
        expected_disposition = "optional"
    elif role == "forbidden":
        expected_count = 177 if domain == "stack" else 30
        expected_event = "io.read"
        expected_disposition = "forbidden"
    elif role == "unspecified":
        expected_count = 177 if domain == "stack" else 30
        expected_event = "custom.audit" if domain == "stack" else "network.send"
        expected_disposition = "unspecified"
    else:
        expected_count = 0 if domain == "stack" else 1
        expected_event = None if domain == "stack" else "io.read"
        expected_disposition = None if domain == "stack" else "forbidden"

    label = "adapter-error event ledger" if role == "adapter-error" else "event ledger"
    if len(ledger) != expected_count:
        _problem("EVENT_LEDGER", f"{domain} {label} has unexpected length")
    if any(
        item["event"] != expected_event
        or item["disposition"] != expected_disposition
        for item in ledger
    ):
        _problem("EVENT_LEDGER", f"{domain} {label} has unexpected classification")
    if domain == "ordered-map" and ledger:
        if [item["seq"] for item in ledger] != list(range(len(ledger))):
            _problem("EVENT_LEDGER", f"{domain} {label} is not in invocation order")
    if domain == "ordered-map" and role == "adapter-error" and ledger:
        if (ledger[0]["caseId"], ledger[0]["operation"]) != (
            "lookup-empty",
            "empty",
        ):
            _problem("EVENT_LEDGER", "ordered-map adapter-error event ledger moved")
    if _canonical_sha256(ledger) != _LEDGER_SHA256[domain][role_index]:
        _problem("EVENT_LEDGER", f"{domain} {label} changed exact attribution")


def _ordered_map_effect_surface(report: Any) -> dict[str, Any]:
    return {
        "global": [
            _ordered_map_declaration(item)
            for item in report.declarations
            if item.declaration_id == "ordered-map-effects"
        ],
        "cases": [
            {
                "case": case.case_id,
                "effects": [
                    _ordered_map_declaration(item)
                    for item in case.declarations
                    if item.declaration_id == "ordered-map-effects"
                ],
            }
            for case in report.cases
        ],
    }


def _challenged_non_effect(report: Any, domain: str) -> bool:
    effect_id = "stack-effects" if domain == "stack" else "ordered-map-effects"
    outcomes = (
        report.declaration_outcomes if domain == "stack" else report.declarations
    )
    if any(
        item.result == "challenges" and item.declaration_id != effect_id
        for item in outcomes
    ):
        return True
    if domain == "ordered-map":
        return any(
            item.result == "challenges" and item.declaration_id != effect_id
            for case in report.cases
            for item in case.declarations
        )
    return False


def _any_challenge(report: Any, domain: str) -> bool:
    outcomes = (
        report.declaration_outcomes if domain == "stack" else report.declarations
    )
    return any(item.result == "challenges" for item in outcomes)


def _domain_observation(
    *,
    domain: str,
    fixture: str,
    effect_id: str,
    modes: Sequence[str],
    reports: Sequence[Any],
    expected_plan: str,
) -> dict[str, Any]:
    if len(reports) != 5:
        _problem("VARIANT_CENSUS", f"{domain} must have exactly five observations")

    declaration_attribute = (
        "declaration_outcomes" if domain == "stack" else "declarations"
    )
    project = _stack_projection if domain == "stack" else _ordered_map_projection
    ledger_for = _stack_ledger if domain == "stack" else _ordered_map_ledger
    projections = [project(report) for report in reports]
    expected_campaign_results = (
        "supports",
        "supports",
        "challenges",
        "supports",
        "error",
    )
    expected_effect_results = (
        "supports",
        "supports",
        "challenges",
        "supports",
        "inconclusive",
    )
    observations: list[dict[str, Any]] = []

    for index, (role, mode, report) in enumerate(zip(_ROLES, modes, reports)):
        _validate_common(report, domain, expected_plan)
        ledger = ledger_for(report)
        _validate_ledger(domain, role, ledger, index)
        effect = _effect_outcome(report, declaration_attribute, effect_id)

        if role == "forbidden" and _challenged_non_effect(report, domain):
            _problem("CONCERN_SPILLOVER", f"{domain} forbidden concern spillover")
        if role != "adapter-error" and index > 0 and projections[index] != projections[0]:
            _problem("SEMANTIC_DRIFT", f"{domain} semantic projection drift in {role}")
        expected_projection = _PROJECTION_SHA256[domain][
            1 if role == "adapter-error" else 0
        ]
        if _canonical_sha256(projections[index]) != expected_projection:
            _problem(
                "PROJECTION_BINDING",
                f"{domain} semantic projection binding changed in {role}",
            )
        if role != "adapter-error" and effect.result != expected_effect_results[index]:
            _problem(
                "EFFECT_RESULT",
                f"{domain} {role} effect result is {effect.result}",
            )
        if report.result != expected_campaign_results[index]:
            label = (
                "adapter-error result"
                if role == "adapter-error"
                else f"{role} campaign result"
            )
            _problem("CAMPAIGN_RESULT", f"{domain} {label} is {report.result}")
        if role == "adapter-error" and effect.result != expected_effect_results[index]:
            _problem(
                "EFFECT_RESULT",
                f"{domain} adapter-error effect result is {effect.result}",
            )
        if role == "forbidden":
            if list(report.causes) != ["FORBIDDEN_EVENT"] or list(effect.causes) != [
                "FORBIDDEN_EVENT"
            ]:
                _problem("CONCERN_CAUSE", f"{domain} forbidden cause changed")
        elif role == "adapter-error":
            if list(report.causes) != ["ADAPTER_ERROR"] or _any_challenge(
                report, domain
            ):
                _problem("ERROR_AUTHORITY", f"{domain} adapter-error became authoritative")
        elif report.causes or effect.causes:
            _problem("UNEXPECTED_CAUSE", f"{domain} {role} carries a challenge cause")
        if domain == "ordered-map" and _canonical_sha256(
            _ordered_map_effect_surface(report)
        ) != _ORDERED_MAP_EFFECT_SURFACE_SHA256[index]:
            _problem(
                "EFFECT_SURFACE",
                f"ordered-map {role} effect surface changed",
            )

        observations.append(
            {
                "role": role,
                "adapterMode": mode,
                "campaignResult": report.result,
                "campaignCauses": list(report.causes),
                "effectResult": effect.result,
                "effectCauses": list(effect.causes),
                "effectAuthority": (
                    "non-authoritative"
                    if role == "adapter-error"
                    else "authoritative-within-complete-campaign"
                ),
                "eventLedger": ledger,
                "semanticProjection": projections[index],
                "projectionComparison": (
                    "baseline"
                    if role == "quiet"
                    else "not-compared"
                    if role == "adapter-error"
                    else "equal"
                ),
            }
        )

    return {
        "domain": domain,
        "effectDeclaration": effect_id,
        "fixture": fixture,
        "planSha256": expected_plan,
        "observations": observations,
    }


def build_observation(root: Path) -> dict[str, Any]:
    """Run the two exact campaigns and return one validated bounded observation."""

    stack_fixture = root / "fixtures/adapters/v1/fake_stack_adapter.py"
    ordered_map_fixture = (
        root / "fixtures/adapters/ordered-map-v1/fake_ordered_map_adapter.py"
    )
    stack_plan = default_stack_conformance_plan()
    stack_reports = tuple(
        run_stack_conformance(
            (sys.executable, str(stack_fixture), mode),
            plan=stack_plan,
        )
        for mode in _STACK_MODES
    )
    ordered_map_reports = tuple(
        run_ordered_map_conformance(
            (sys.executable, str(ordered_map_fixture), mode)
        )
        for mode in _ORDERED_MAP_MODES
    )

    domains = [
        _domain_observation(
            domain="stack",
            fixture="fixtures/adapters/v1/fake_stack_adapter.py",
            effect_id="stack-effects",
            modes=_STACK_MODES,
            reports=stack_reports,
            expected_plan=_STACK_PLAN_SHA256,
        ),
        _domain_observation(
            domain="ordered-map",
            fixture="fixtures/adapters/ordered-map-v1/fake_ordered_map_adapter.py",
            effect_id="ordered-map-effects",
            modes=_ORDERED_MAP_MODES,
            reports=ordered_map_reports,
            expected_plan=_ORDERED_MAP_PLAN_SHA256,
        ),
    ]
    return {
        "kind": "effect-separation-observation-v1",
        "boundary": "adapter-reported-invocation-events",
        "domains": domains,
        "summary": {
            "domains": 2,
            "observations": 10,
            "semanticDrifts": 0,
            "effectChallenges": 2,
            "executionErrors": 2,
        },
        "assumptions": list(_ASSUMPTIONS),
        "exclusions": list(_EXCLUSIONS),
        "conclusion": "bounded-separation-observed",
    }


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(directory.resolve(strict=False))
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _same_file(left: Path, right: Path) -> bool:
    try:
        return os.path.samefile(left, right)
    except (OSError, ValueError):
        return False


def _aliases_governed_input(output: Path, root: Path) -> bool:
    protected_roots = tuple(
        root / item for item in ("fixtures", "contracts", "specs", "registry", "reports")
    )
    if any(_is_within(output, protected) for protected in protected_roots):
        return True
    return any(
        _same_file(output, candidate)
        for candidate in root.rglob("*")
        if candidate.is_file()
    )


def _write_atomically(output: Path, document: dict[str, Any]) -> None:
    temporary: str | None = None
    rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    except (OSError, ValueError) as error:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        detail = getattr(error, "strerror", None) or str(error)
        raise ObservationProblem("OUTPUT_WRITE", f"cannot write observation: {detail}") from error


def run(
    output: Path,
    *,
    root: Path,
    diagnostics: Callable[[str], None] | None = None,
) -> int:
    """Validate, then atomically publish one observation; preserve prior output on failure."""

    emit = diagnostics if diagnostics is not None else lambda message: print(message, file=sys.stderr)
    try:
        if _aliases_governed_input(output, root):
            _problem(
                "OUTPUT_INPUT_ALIAS",
                "output aliases or occupies a governed repository input boundary",
            )
        document = build_observation(root)
        _write_atomically(output, document)
    except ObservationProblem as problem:
        emit(str(problem))
        return 1
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        emit(
            "OBSERVATION_FAILURE: bounded observation could not be completed "
            f"({type(error).__name__})"
        )
        return 1

    print(
        "observed bounded effect separation: 2 domains, 10 observations, "
        f"0 semantic drifts, 2 effect challenges, 2 execution errors -> {output}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 scripts/effect_separation_probe.py",
        description="Observe bounded semantic/effect separation in two exact campaigns.",
    )
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(arguments: Sequence[str] | None = None, *, root: Path | None = None) -> int:
    options = build_parser().parse_args(arguments)
    repository_root = root if root is not None else Path(__file__).resolve().parents[1]
    return run(options.output, root=repository_root)
