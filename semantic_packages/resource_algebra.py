"""Bounded inspection of one authored finite resource-composition algebra."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts import record_check

from .author_command import (
    _print_diagnostics,
    _read_source,
    load_authoring_dependency,
)
from .authoring import PSPEC_TOML_V1, AuthoringDependency, author_specification


@dataclass(frozen=True)
class ResourceProblem:
    code: str
    pointer: str
    message: str


def _address(document: Mapping[str, Any]) -> dict[str, Any]:
    return {key: document[key] for key in ("kind", "id", "version")}


def _problem(code: str, pointer: str, message: str) -> ResourceProblem:
    return ResourceProblem(code, pointer, message)


def _binding_key(binding: Mapping[str, Any]) -> tuple[str, str, str, str]:
    reference = binding["declarationReference"]
    specification = reference["specification"]
    return (
        specification["kind"],
        specification["id"],
        specification["version"],
        reference["declarationId"],
    )


def inspect_resource_algebra(
    document: Mapping[str, Any],
    dependency_documents: Sequence[Mapping[str, Any]],
    dependency_hashes: Sequence[str],
    source_hash: str,
    resource_id: str,
) -> tuple[dict[str, Any] | None, ResourceProblem | None]:
    """Inspect one already-authored candidate without granting satisfaction authority."""
    resources = [item for item in document.get("resources", []) if item.get("id") == resource_id]
    if not resources:
        return None, _problem(
            "RESOURCE_NOT_FOUND",
            "#/resources",
            f"resource {resource_id} is not declared by {_address(document)}",
        )
    if len(resources) != 1:
        return None, _problem(
            "RESOURCE_AMBIGUOUS",
            "#/resources",
            f"resource {resource_id} occurs {len(resources)} times",
        )
    resource = resources[0]
    resource_index = document.get("resources", []).index(resource)
    base = f"#/resources/{resource_index}/algebra"
    algebra = resource.get("algebra")
    if not isinstance(algebra, dict):
        return None, _problem(
            "RESOURCE_ALGEBRA_REQUIRED",
            base,
            f"resource {resource_id} has no finite-commutative-monoid-v1 algebra",
        )

    carrier = list(algebra["carrier"])
    carrier_set = set(carrier)
    unit = algebra["unit"]
    if unit not in carrier_set:
        return None, _problem(
            "RESOURCE_ALGEBRA_UNIT_ELEMENT",
            f"{base}/unit",
            f"unit {unit} is outside the authored carrier",
        )

    rows = list(algebra["composition"])
    table: dict[tuple[str, str], str] = {}
    row_indexes: dict[tuple[str, str], int] = {}
    for index, row in enumerate(rows):
        for field in ("left", "right", "result"):
            token = row[field]
            if token not in carrier_set:
                return None, _problem(
                    "RESOURCE_ALGEBRA_CLOSURE",
                    f"{base}/composition/{index}/{field}",
                    f"{field} element {token} is outside the authored carrier",
                )
        pair = (row["left"], row["right"])
        if pair in table:
            return None, _problem(
                "RESOURCE_ALGEBRA_DUPLICATE_PAIR",
                f"{base}/composition/{index}",
                f"duplicate ordered pair ({pair[0]}, {pair[1]}); first authored at row {row_indexes[pair]}",
            )
        table[pair] = row["result"]
        row_indexes[pair] = index

    for left in carrier:
        for right in carrier:
            if (left, right) not in table:
                return None, _problem(
                    "RESOURCE_ALGEBRA_COVERAGE",
                    f"{base}/composition",
                    f"missing pair ({left}, {right})",
                )

    for element in carrier:
        left_result = table[unit, element]
        if left_result != element:
            return None, _problem(
                "RESOURCE_ALGEBRA_UNIT",
                f"{base}/composition",
                f"left unit {unit} with {element} produced {left_result}",
            )
        right_result = table[element, unit]
        if right_result != element:
            return None, _problem(
                "RESOURCE_ALGEBRA_UNIT",
                f"{base}/composition",
                f"right unit {unit} with {element} produced {right_result}",
            )

    for left in carrier:
        for right in carrier:
            direct = table[left, right]
            reverse = table[right, left]
            if direct != reverse:
                return None, _problem(
                    "RESOURCE_ALGEBRA_COMMUTATIVITY",
                    f"{base}/composition",
                    f"commutativity failed at ({left}, {right}): {direct} != {reverse}",
                )

    for left in carrier:
        for middle in carrier:
            for right in carrier:
                left_grouped = table[table[left, middle], right]
                right_grouped = table[left, table[middle, right]]
                if left_grouped != right_grouped:
                    return None, _problem(
                        "RESOURCE_ALGEBRA_ASSOCIATIVITY",
                        f"{base}/composition",
                        f"associativity failed at ({left}, {middle}, {right}): "
                        f"{left_grouped} != {right_grouped}",
                    )

    bindings = list(algebra["bindings"])
    seen_bindings: set[tuple[str, str, str, str]] = set()
    for index, binding in enumerate(bindings):
        element = binding["element"]
        if element not in carrier_set:
            return None, _problem(
                "RESOURCE_BINDING_ELEMENT",
                f"{base}/bindings/{index}/element",
                f"binding element {element} is outside the authored carrier",
            )
        key = _binding_key(binding)
        if key in seen_bindings:
            return None, _problem(
                "RESOURCE_BINDING_DUPLICATE",
                f"{base}/bindings/{index}/declarationReference",
                f"duplicate exact declaration binding {key}",
            )
        seen_bindings.add(key)

    def fold(elements: list[str]) -> dict[str, Any]:
        current = unit
        trace: list[dict[str, str]] = []
        for element in elements:
            result = table[current, element]
            trace.append({"left": current, "right": element, "result": result})
            current = result
        return {
            "start": unit,
            "elements": elements,
            "trace": trace,
            "result": current,
        }

    elements = [binding["element"] for binding in bindings]
    imports = list(document.get("imports", []))
    dependencies = [
        {"record": _address(dependency), "sha256": digest}
        for dependency, digest in zip(dependency_documents, dependency_hashes, strict=True)
    ]
    report = {
        "kind": "resource-algebra-inspection-v1",
        "source": {
            "format": PSPEC_TOML_V1,
            "sha256": source_hash,
            "specification": _address(document),
        },
        "imports": imports,
        "dependencies": dependencies,
        "resource": {"id": resource["id"], "rule": resource["rule"]},
        "algebra": algebra,
        "observations": {
            "structure": {
                "carrierCount": len(carrier),
                "compositionCount": len(rows),
                "expectedPairCount": len(carrier) ** 2,
                "closed": True,
                "total": True,
                "duplicatePairs": 0,
            },
            "laws": {
                "unit": {"holds": True, "observationCount": len(carrier) * 2},
                "commutativity": {"holds": True, "observationCount": len(carrier) ** 2},
                "associativity": {"holds": True, "observationCount": len(carrier) ** 3},
            },
        },
        "folds": {
            "authored": fold(elements),
            "reverse": fold(list(reversed(elements))),
        },
        "assumptions": [
            "Imported declaration meanings remain those of their exact authored Specifications.",
            "Finite enumeration is sufficient for this exact authored carrier and table.",
        ],
        "exclusions": [
            "Realization satisfaction",
            "Claim or Evidence transfer",
            "Semantic compatibility or refinement",
            "Runtime resource, ownership, quantity, or separation reasoning",
            "Resolver or consumer-decision authority",
            "Arbitrary-domain resource composition",
        ],
        "algebraConclusion": "finite-algebra-well-formed",
        "satisfaction": "unestablished",
    }
    return report, None


def _aliases_input(output: Path, input_path: Path) -> bool:
    try:
        return os.path.samefile(output, input_path)
    except (OSError, ValueError):
        try:
            return output.resolve(strict=False) == input_path.resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            return os.path.abspath(output) == os.path.abspath(input_path)


def _write_atomically(path: Path, document: Mapping[str, Any]) -> record_check.Diagnostic | None:
    rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except (OSError, ValueError) as error:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        detail = getattr(error, "strerror", None) or str(error)
        return record_check.Diagnostic(
            "RESOURCE_OUTPUT_WRITE", os.fspath(path), "#", f"cannot write output: {detail}"
        )
    return None


def _print_problem(path: Path, problem: ResourceProblem) -> None:
    print(
        f"{problem.code} {path}{problem.pointer}: {problem.message}",
        file=os.sys.stderr,
    )


def run_resource_inspection(
    source_path: Path,
    dependency_paths: Sequence[Path],
    resource_id: str,
    output_path: Path,
) -> int:
    inputs = (source_path, *dependency_paths)
    for input_path in inputs:
        if _aliases_input(output_path, input_path):
            _print_diagnostics(
                (
                    record_check.Diagnostic(
                        "RESOURCE_OUTPUT_WRITE",
                        os.fspath(output_path),
                        "#",
                        f"output aliases input {input_path}",
                    ),
                )
            )
            return 1

    source_bytes, source_diagnostic = _read_source(source_path)
    if source_diagnostic is not None:
        _print_diagnostics((source_diagnostic,))
        return 1
    assert source_bytes is not None

    dependencies: list[AuthoringDependency] = []
    dependency_documents: list[Mapping[str, Any]] = []
    dependency_hashes: list[str] = []
    for dependency_path in dependency_paths:
        dependency, raw, diagnostic = load_authoring_dependency(dependency_path)
        if diagnostic is not None:
            _print_diagnostics((diagnostic,))
            return 1
        assert dependency is not None and raw is not None
        dependencies.append(dependency)
        dependency_documents.append(dependency.document)
        dependency_hashes.append(hashlib.sha256(raw).hexdigest())

    observation = author_specification(
        source_bytes,
        format_token=PSPEC_TOML_V1,
        source_label=os.fspath(source_path),
        dependencies=tuple(dependencies),
    )
    if not observation.ok:
        _print_diagnostics(observation.diagnostics)
        return 1
    document = observation.document
    assert document is not None

    report, problem = inspect_resource_algebra(
        document,
        dependency_documents,
        dependency_hashes,
        hashlib.sha256(source_bytes).hexdigest(),
        resource_id,
    )
    if problem is not None:
        _print_problem(source_path, problem)
        return 1
    assert report is not None
    output_diagnostic = _write_atomically(output_path, report)
    if output_diagnostic is not None:
        _print_diagnostics((output_diagnostic,))
        return 1
    algebra = report["algebra"]
    folded = report["folds"]["authored"]["result"]
    print(
        f"inspected resource algebra {resource_id}: {len(algebra['carrier'])} elements, "
        f"{len(algebra['composition'])} compositions, {len(algebra['bindings'])} bindings, "
        f"fold={folded}; satisfaction unestablished -> {output_path}"
    )
    return 0
