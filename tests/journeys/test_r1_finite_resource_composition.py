"""Refute-first contract for design-spec 0004's resource journey."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
DESIGN_SPEC = ROOT / "design-specs/0004-finite-resource-composition-inspection.md"
EXEC_PLAN = ROOT / "docs/exec-plans/active/0009-finite-resource-composition.md"
SOURCE = ROOT / "specs/persistence-composition.pspec"
STACK_PSPEC = ROOT / "specs/stack.pspec"
ORDERED_MAP_PSPEC = ROOT / "specs/ordered-map.pspec"
STACK = ROOT / "registry/stack/theory/records/stack-spec.json"
ORDERED_MAP = ROOT / "registry/ordered-map/theory/records/ordered-map-spec.json"
STACK_PROFILE = ROOT / "registry/stack/theory/dependencies/stack-profile.json"
ORDERED_MAP_PROFILE = ROOT / "registry/ordered-map/theory/dependencies/ordered-map-profile.json"
RESOURCE_READY = importlib.util.find_spec("semantic_packages.resource_algebra") is not None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _record_address(path: Path) -> dict:
    document = _read_json(path)
    return {key: document[key] for key in ("kind", "id", "version")}


def _run_resource(
    source: Path,
    stack: Path,
    ordered_map: Path,
    output: Path,
    *,
    resource: str = "retained-persistence",
    dependencies: tuple[Path, ...] | None = None,
) -> subprocess.CompletedProcess[str]:
    explicit = (
        dependencies
        if dependencies is not None
        else (stack, STACK_PROFILE, ordered_map, ORDERED_MAP_PROFILE)
    )
    arguments = [
        sys.executable,
        "-m",
        "semantic_packages",
        "resource",
        "inspect",
        str(source),
    ]
    for dependency in explicit:
        arguments.extend(("--dependency", str(dependency)))
    arguments.extend(("--resource", resource, "--output", str(output)))
    return subprocess.run(
        arguments,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _copy_inputs(directory: Path) -> tuple[Path, Path, Path]:
    source = directory / "candidate.pspec"
    stack = directory / "stack.json"
    ordered_map = directory / "ordered-map.json"
    shutil.copyfile(SOURCE, source)
    shutil.copyfile(STACK, stack)
    shutil.copyfile(ORDERED_MAP, ordered_map)
    return source, stack, ordered_map


def _replace(path: Path, old: str, new: str, *, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) < count:
        raise AssertionError(f"missing mutation token: {old!r}")
    path.write_text(text.replace(old, new, count), encoding="utf-8")


class FiniteResourceRedBaselineTest(unittest.TestCase):
    maxDiff = None

    def test_contract_plan_and_retained_source_are_present(self) -> None:
        self.assertTrue(DESIGN_SPEC.is_file())
        self.assertTrue(EXEC_PLAN.is_file())
        self.assertTrue(SOURCE.is_file())
        source = tomllib.loads(SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(
            {"kind": "specification", "id": "persistence-composition", "version": "0.1.0"},
            {key: source[key] for key in ("kind", "id", "version")},
        )
        self.assertEqual(
            [
                {"kind": "specification", "id": "stack", "version": "0.1.0"},
                {"kind": "specification", "id": "ordered-map", "version": "0.1.0"},
            ],
            source["imports"],
        )
        self.assertEqual(1, len(source["resources"]))

    def test_exact_table_bindings_and_independent_oracle_are_frozen(self) -> None:
        algebra = tomllib.loads(SOURCE.read_text(encoding="utf-8"))["resources"][0]["algebra"]
        carrier = ("none", "stack-retained", "ordered-map-retained", "both-retained")
        self.assertEqual("finite-commutative-monoid-v1", algebra["kind"])
        self.assertEqual(list(carrier), algebra["carrier"])
        self.assertEqual("none", algebra["unit"])
        table = {(row["left"], row["right"]): row["result"] for row in algebra["composition"]}
        self.assertEqual(16, len(algebra["composition"]))
        self.assertEqual({(left, right) for left in carrier for right in carrier}, set(table))
        self.assertTrue(all(table["none", item] == item == table[item, "none"] for item in carrier))
        self.assertTrue(all(table[left, right] == table[right, left] for left in carrier for right in carrier))
        self.assertTrue(
            all(
                table[table[left, middle], right] == table[left, table[middle, right]]
                for left in carrier
                for middle in carrier
                for right in carrier
            )
        )
        self.assertEqual(
            [
                ({"kind": "specification", "id": "stack", "version": "0.1.0"}, "persistence", "stack-retained"),
                ({"kind": "specification", "id": "ordered-map", "version": "0.1.0"}, "persistence", "ordered-map-retained"),
            ],
            [
                (
                    binding["declarationReference"]["specification"],
                    binding["declarationReference"]["declarationId"],
                    binding["element"],
                )
                for binding in algebra["bindings"]
            ],
        )

    def test_all_predecessor_bytes_and_resource_meanings_are_unchanged(self) -> None:
        self.assertEqual("4c77a9fe9c4ff3495a9ae2255baea8b0e3d11c13e47ff66fd46bdf76a93b0f78", _sha256(STACK_PSPEC))
        self.assertEqual("e8ed6a4e9ab1b00769856be34f62fdc56fccaac65c49311671993c71b8072177", _sha256(ORDERED_MAP_PSPEC))
        self.assertEqual("dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1", _sha256(STACK))
        self.assertEqual("6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f", _sha256(ORDERED_MAP))
        self.assertEqual("persistence", _read_json(STACK)["resources"][0]["id"])
        self.assertEqual("persistence", _read_json(ORDERED_MAP)["resources"][0]["id"])
        self.assertNotEqual(_read_json(STACK)["resources"][0]["rule"], _read_json(ORDERED_MAP)["resources"][0]["rule"])

    def test_red_predecessor_names_only_the_absent_resource_command(self) -> None:
        if RESOURCE_READY:
            self.skipTest("resource inspection command is implemented")
        with tempfile.TemporaryDirectory(prefix="semantic-resource-red-") as raw:
            directory = Path(raw)
            result = _run_resource(SOURCE, STACK, ORDERED_MAP, directory / "report.json")
        self.assertEqual(2, result.returncode)
        self.assertIn("invalid choice: 'resource'", result.stderr)
        self.fail("R1 resource inspect journey is absent; successor remains red")


@unittest.skipUnless(RESOURCE_READY, "finite resource inspection is not implemented")
class FiniteResourceJourneyTest(unittest.TestCase):
    maxDiff = None

    def _assert_failed_preserving_output(
        self,
        source: Path,
        stack: Path,
        ordered_map: Path,
        expected: tuple[str, ...],
        *,
        dependencies: tuple[Path, ...] | None = None,
        resource: str = "retained-persistence",
    ) -> subprocess.CompletedProcess[str]:
        output = source.parent / "report.json"
        sentinel = b'{"retained":"prior"}\n'
        output.write_bytes(sentinel)
        snapshots = (source.read_bytes(), stack.read_bytes(), ordered_map.read_bytes())
        result = _run_resource(
            source,
            stack,
            ordered_map,
            output,
            dependencies=dependencies,
            resource=resource,
        )
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)
        self.assertTrue(all(token in result.stderr for token in expected), result.stderr)
        self.assertEqual(sentinel, output.read_bytes())
        self.assertEqual(snapshots, (source.read_bytes(), stack.read_bytes(), ordered_map.read_bytes()))
        return result

    def test_required_arguments_exit_two_without_output(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "semantic_packages", "resource", "inspect"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("the following arguments are required", result.stderr)

    def test_exact_felt_journey_and_complete_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-happy-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            inputs = (source.read_bytes(), stack.read_bytes(), ordered_map.read_bytes())
            output = directory / "report.json"
            result = _run_resource(source, stack, ordered_map, output)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                "inspected resource algebra retained-persistence: 4 elements, 16 compositions, "
                "2 bindings, fold=both-retained; satisfaction unestablished -> "
                f"{output}\n",
                result.stdout,
            )
            self.assertEqual(inputs, (source.read_bytes(), stack.read_bytes(), ordered_map.read_bytes()))
            report = _read_json(output)
            authored = tomllib.loads(source.read_text(encoding="utf-8"))
            algebra = authored["resources"][0]["algebra"]
            imports = authored["imports"]
            self.assertEqual(
                {
                    "kind",
                    "source",
                    "imports",
                    "dependencies",
                    "resource",
                    "algebra",
                    "observations",
                    "folds",
                    "assumptions",
                    "exclusions",
                    "algebraConclusion",
                    "satisfaction",
                },
                set(report),
            )
            self.assertEqual("resource-algebra-inspection-v1", report["kind"])
            self.assertEqual(
                {"format": "pspec-toml-v1", "sha256": _sha256(source), "specification": {"kind": "specification", "id": "persistence-composition", "version": "0.1.0"}},
                report["source"],
            )
            self.assertEqual(imports, report["imports"])
            self.assertEqual(
                [
                    {"record": imports[0], "sha256": _sha256(stack)},
                    {"record": _record_address(STACK_PROFILE), "sha256": _sha256(STACK_PROFILE)},
                    {"record": imports[1], "sha256": _sha256(ordered_map)},
                    {"record": _record_address(ORDERED_MAP_PROFILE), "sha256": _sha256(ORDERED_MAP_PROFILE)},
                ],
                report["dependencies"],
            )
            self.assertEqual(
                {
                    "id": "retained-persistence",
                    "rule": "Stack-retained and OrderedMap-retained persistence obligations compose independently into both-retained.",
                },
                report["resource"],
            )
            self.assertEqual(algebra, report["algebra"])
            self.assertEqual(
                {
                    "structure": {
                        "carrierCount": 4,
                        "compositionCount": 16,
                        "expectedPairCount": 16,
                        "closed": True,
                        "total": True,
                        "duplicatePairs": 0,
                    },
                    "laws": {
                        "unit": {"holds": True, "observationCount": 8},
                        "commutativity": {"holds": True, "observationCount": 16},
                        "associativity": {"holds": True, "observationCount": 64},
                    },
                },
                report["observations"],
            )
            self.assertEqual(
                {
                    "authored": {
                        "start": "none",
                        "elements": ["stack-retained", "ordered-map-retained"],
                        "trace": [
                            {"left": "none", "right": "stack-retained", "result": "stack-retained"},
                            {"left": "stack-retained", "right": "ordered-map-retained", "result": "both-retained"},
                        ],
                        "result": "both-retained",
                    },
                    "reverse": {
                        "start": "none",
                        "elements": ["ordered-map-retained", "stack-retained"],
                        "trace": [
                            {"left": "none", "right": "ordered-map-retained", "result": "ordered-map-retained"},
                            {"left": "ordered-map-retained", "right": "stack-retained", "result": "both-retained"},
                        ],
                        "result": "both-retained",
                    },
                },
                report["folds"],
            )
            self.assertEqual(
                [
                    "Imported declaration meanings remain those of their exact authored Specifications.",
                    "Finite enumeration is sufficient for this exact authored carrier and table.",
                ],
                report["assumptions"],
            )
            self.assertEqual(
                [
                    "Realization satisfaction",
                    "Claim or Evidence transfer",
                    "Semantic compatibility or refinement",
                    "Runtime resource, ownership, quantity, or separation reasoning",
                    "Resolver or consumer-decision authority",
                    "Arbitrary-domain resource composition",
                ],
                report["exclusions"],
            )
            self.assertEqual("finite-algebra-well-formed", report["algebraConclusion"])
            self.assertEqual("unestablished", report["satisfaction"])

    def test_exact_dependencies_and_resource_kind_bindings_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-binding-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            self._assert_failed_preserving_output(
                source,
                stack,
                ordered_map,
                ("LINK_DANGLING_REFERENCE", "#/imports/1"),
                dependencies=(stack,),
            )

            shutil.copyfile(SOURCE, source)
            _replace(
                source,
                '  { kind = "specification", id = "stack", version = "0.1.0" },\n',
                "",
            )
            self._assert_failed_preserving_output(
                source,
                stack,
                ordered_map,
                (
                    "LINK_RESOURCE_BINDING_NOT_IMPORTED",
                    "#/resources/0/algebra/bindings/0/declarationReference/specification",
                ),
            )

            shutil.copyfile(SOURCE, source)
            _replace(source, 'declarationId = "persistence"', 'declarationId = "missing"')
            self._assert_failed_preserving_output(source, stack, ordered_map, ("LINK_DANGLING_DECLARATION", "#/resources/0/algebra/bindings/0/declarationReference/declarationId"))

            shutil.copyfile(SOURCE, source)
            _replace(source, 'declarationId = "persistence"', 'declarationId = "push"')
            self._assert_failed_preserving_output(source, stack, ordered_map, ("LINK_DECLARATION_KIND_MISMATCH", "found operation"))

            shutil.copyfile(SOURCE, source)
            _replace(
                source,
                'specification = { kind = "specification", id = "stack", version = "0.1.0" }, declarationId = "persistence"',
                'specification = { kind = "specification", id = "stack", version = "9.9.9" }, declarationId = "persistence"',
            )
            self._assert_failed_preserving_output(source, stack, ordered_map, ("LINK_VERSION_MISMATCH", "loaded version is 0.1.0"))

    def test_equal_local_ids_do_not_bind_implicitly_or_collapse(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-no-inference-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            output = directory / "report.json"
            result = _run_resource(source, stack, ordered_map, output)
            self.assertEqual(0, result.returncode, result.stderr)
            bindings = _read_json(output)["algebra"]["bindings"]
            self.assertEqual(["persistence", "persistence"], [item["declarationReference"]["declarationId"] for item in bindings])
            self.assertEqual(["stack", "ordered-map"], [item["declarationReference"]["specification"]["id"] for item in bindings])
            self.assertEqual(["stack-retained", "ordered-map-retained"], [item["element"] for item in bindings])

            _replace(
                source,
                'specification = { kind = "specification", id = "ordered-map", version = "0.1.0" }, declarationId = "persistence"',
                'specification = { kind = "specification", id = "stack", version = "0.1.0" }, declarationId = "persistence"',
            )
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_BINDING_DUPLICATE", "#/resources/0/algebra/bindings/1/declarationReference"))

    def test_raw_schema_and_link_phases_precede_algebra_inspection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-phases-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            _replace(source, 'id = "persistence-composition"', 'id = "persistence-composition"\nid = "duplicate"')
            _replace(source, 'unit = "none"', 'unit = "outside"')
            raw_failure = self._assert_failed_preserving_output(source, stack, ordered_map, ("AUTHOR_INVALID_TOML", "duplicate"))
            self.assertNotIn("SCHEMA_", raw_failure.stderr)
            self.assertNotIn("LINK_", raw_failure.stderr)
            self.assertNotIn("RESOURCE_ALGEBRA_", raw_failure.stderr)

            shutil.copyfile(SOURCE, source)
            _replace(source, 'kind = "finite-commutative-monoid-v1"', 'kind = "invented-algebra"')
            _replace(source, 'unit = "none"', 'unit = "outside"')
            schema = self._assert_failed_preserving_output(source, stack, ordered_map, ("SCHEMA_RESOURCE_ALGEBRA_KIND", "#/resources/0/algebra/kind"))
            self.assertNotIn("RESOURCE_ALGEBRA_UNIT_ELEMENT", schema.stderr)

            shutil.copyfile(SOURCE, source)
            _replace(source, 'id = "ordered-map", version = "0.1.0"', 'id = "missing-map", version = "0.1.0"', count=2)
            _replace(source, 'unit = "none"', 'unit = "outside"')
            link = self._assert_failed_preserving_output(source, stack, ordered_map, ("LINK_DANGLING_REFERENCE", "#/imports/1"))
            self.assertNotIn("RESOURCE_ALGEBRA_", link.stderr)

    def test_candidate_carrier_unit_and_required_algebra_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-shape-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            _replace(
                source,
                'carrier = ["none", "stack-retained", "ordered-map-retained", "both-retained"]',
                'carrier = ["none", "stack-retained", "ordered-map-retained", "stack-retained"]',
            )
            self._assert_failed_preserving_output(source, stack, ordered_map, ("SCHEMA_UNIQUE_ITEMS", "#/resources/0/algebra/carrier"))

            shutil.copyfile(SOURCE, source)
            _replace(source, 'unit = "none"', 'unit = "outside"')
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_ALGEBRA_UNIT_ELEMENT", "#/resources/0/algebra/unit"))

            shutil.copyfile(SOURCE, source)
            text = source.read_text(encoding="utf-8")
            source.write_text(text[: text.index("\n[resources.algebra]")] + "\n", encoding="utf-8")
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_ALGEBRA_REQUIRED", "#/resources/0/algebra"))

    def test_missing_duplicate_and_out_of_carrier_compositions_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-coverage-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            block = '[[resources.algebra.composition]]\nleft = "none"\nright = "none"\nresult = "none"\n\n'
            _replace(source, block, "")
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_ALGEBRA_COVERAGE", "missing pair (none, none)"))

            shutil.copyfile(SOURCE, source)
            source.write_text(source.read_text(encoding="utf-8") + "\n" + block, encoding="utf-8")
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_ALGEBRA_DUPLICATE_PAIR", "#/resources/0/algebra/composition/16"))

            shutil.copyfile(SOURCE, source)
            _replace(source, 'left = "none"\nright = "none"\nresult = "none"', 'left = "outside"\nright = "none"\nresult = "none"')
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_ALGEBRA_CLOSURE", "#/resources/0/algebra/composition/0/left", "outside"))

            shutil.copyfile(SOURCE, source)
            _replace(source, 'left = "none"\nright = "none"\nresult = "none"', 'left = "none"\nright = "none"\nresult = "outside"')
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_ALGEBRA_CLOSURE", "#/resources/0/algebra/composition/0/result", "outside"))

    def test_unit_commutativity_and_associativity_have_stable_counterexamples(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-laws-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            _replace(source, 'left = "none"\nright = "stack-retained"\nresult = "stack-retained"', 'left = "none"\nright = "stack-retained"\nresult = "both-retained"')
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_ALGEBRA_UNIT", "#/resources/0/algebra/composition", "left unit none with stack-retained produced both-retained"))

            shutil.copyfile(SOURCE, source)
            _replace(source, 'left = "stack-retained"\nright = "ordered-map-retained"\nresult = "both-retained"', 'left = "stack-retained"\nright = "ordered-map-retained"\nresult = "stack-retained"')
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_ALGEBRA_COMMUTATIVITY", "#/resources/0/algebra/composition", "(stack-retained, ordered-map-retained)"))

            shutil.copyfile(SOURCE, source)
            _replace(source, 'left = "stack-retained"\nright = "stack-retained"\nresult = "stack-retained"', 'left = "stack-retained"\nright = "stack-retained"\nresult = "ordered-map-retained"')
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_ALGEBRA_ASSOCIATIVITY", "#/resources/0/algebra/composition", "(stack-retained, stack-retained, ordered-map-retained)", "ordered-map-retained != both-retained"))

    def test_binding_elements_and_complete_forward_reverse_folds_are_exact(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-fold-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            output = directory / "report.json"
            result = _run_resource(source, stack, ordered_map, output)
            self.assertEqual(0, result.returncode, result.stderr)
            folds = _read_json(output)["folds"]
            self.assertEqual("none", folds["authored"]["start"])
            self.assertEqual(["stack-retained", "ordered-map-retained"], folds["authored"]["elements"])
            self.assertEqual(["ordered-map-retained", "stack-retained"], folds["reverse"]["elements"])
            self.assertEqual("both-retained", folds["authored"]["result"])
            self.assertEqual("both-retained", folds["reverse"]["result"])
            self.assertEqual(
                [
                    {"left": "none", "right": "stack-retained", "result": "stack-retained"},
                    {"left": "stack-retained", "right": "ordered-map-retained", "result": "both-retained"},
                ],
                folds["authored"]["trace"],
            )
            self.assertEqual(
                [
                    {"left": "none", "right": "ordered-map-retained", "result": "ordered-map-retained"},
                    {"left": "ordered-map-retained", "right": "stack-retained", "result": "both-retained"},
                ],
                folds["reverse"]["trace"],
            )

            _replace(source, 'element = "stack-retained"', 'element = "none"')
            changed = _run_resource(source, stack, ordered_map, output)
            self.assertEqual(0, changed.returncode, changed.stderr)
            changed_folds = _read_json(output)["folds"]
            self.assertEqual("ordered-map-retained", changed_folds["authored"]["result"])
            self.assertEqual("ordered-map-retained", changed_folds["reverse"]["result"])
            self.assertEqual(["none", "ordered-map-retained"], changed_folds["authored"]["elements"])
            self.assertEqual(["ordered-map-retained", "none"], changed_folds["reverse"]["elements"])
            self.assertEqual(
                [
                    {"left": "none", "right": "none", "result": "none"},
                    {"left": "none", "right": "ordered-map-retained", "result": "ordered-map-retained"},
                ],
                changed_folds["authored"]["trace"],
            )
            self.assertEqual(
                [
                    {"left": "none", "right": "ordered-map-retained", "result": "ordered-map-retained"},
                    {"left": "ordered-map-retained", "right": "none", "result": "ordered-map-retained"},
                ],
                changed_folds["reverse"]["trace"],
            )
            self.assertIn("fold=ordered-map-retained", changed.stdout)

            shutil.copyfile(SOURCE, source)
            _replace(source, 'element = "stack-retained"', 'element = "outside"')
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_BINDING_ELEMENT", "#/resources/0/algebra/bindings/0/element"))

    def test_missing_or_ambiguous_resource_selection_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-selection-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            self._assert_failed_preserving_output(source, stack, ordered_map, ("RESOURCE_NOT_FOUND", "#/resources"), resource="missing")

            text = source.read_text(encoding="utf-8")
            duplicate = text[text.index("[[resources]]") :]
            source.write_text(text + "\n" + duplicate, encoding="utf-8")
            self._assert_failed_preserving_output(source, stack, ordered_map, ("LINK_DUPLICATE_DECLARATION_ID", "#/resources/1/id"))

    def test_output_aliases_and_publication_failure_preserve_inputs_and_prior_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-output-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            for aliased in (source, stack, STACK_PROFILE, ordered_map, ORDERED_MAP_PROFILE):
                with self.subTest(aliased=aliased.name):
                    before = aliased.read_bytes()
                    result = _run_resource(source, stack, ordered_map, aliased)
                    self.assertEqual(1, result.returncode)
                    self.assertIn("RESOURCE_OUTPUT_WRITE", result.stderr)
                    self.assertIn("output aliases input", result.stderr)
                    self.assertEqual(before, aliased.read_bytes())

            symlink = directory / "source-alias.json"
            symlink.symlink_to(source)
            result = _run_resource(source, stack, ordered_map, symlink)
            self.assertEqual(1, result.returncode)
            self.assertIn("RESOURCE_OUTPUT_WRITE", result.stderr)
            self.assertEqual(SOURCE.read_bytes(), source.read_bytes())
            symlink.unlink()

            nested = directory / "nested"
            nested.mkdir()
            normalized_alias = nested / ".." / source.name
            result = _run_resource(source, stack, ordered_map, normalized_alias)
            self.assertEqual(1, result.returncode)
            self.assertIn("output aliases input", result.stderr)
            self.assertEqual(SOURCE.read_bytes(), source.read_bytes())

            from semantic_packages.resource_algebra import run_resource_inspection

            output = directory / "report.json"
            output.write_bytes(b"prior\n")
            with mock.patch("semantic_packages.resource_algebra.os.replace", side_effect=OSError("publication interrupted")):
                code = run_resource_inspection(
                    source,
                    (stack, STACK_PROFILE, ordered_map, ORDERED_MAP_PROFILE),
                    "retained-persistence",
                    output,
                )
            self.assertEqual(1, code)
            self.assertEqual(b"prior\n", output.read_bytes())

    def test_explicit_inputs_are_the_only_acquisition_and_no_execution_occurs(self) -> None:
        from semantic_packages.resource_algebra import run_resource_inspection

        with tempfile.TemporaryDirectory(prefix="semantic-resource-authority-") as raw:
            directory = Path(raw)
            source, stack, ordered_map = _copy_inputs(directory)
            output = directory / "report.json"
            with (
                mock.patch("pathlib.Path.glob", side_effect=AssertionError("glob authority")),
                mock.patch("pathlib.Path.rglob", side_effect=AssertionError("rglob authority")),
                mock.patch("pathlib.Path.iterdir", side_effect=AssertionError("directory authority")),
                mock.patch("os.walk", side_effect=AssertionError("walk authority")),
                mock.patch("os.listdir", side_effect=AssertionError("list authority")),
                mock.patch("os.scandir", side_effect=AssertionError("scan authority")),
                mock.patch("subprocess.Popen", side_effect=AssertionError("child execution")),
                mock.patch("socket.socket", side_effect=AssertionError("network authority")),
            ):
                code = run_resource_inspection(
                    source,
                    (stack, STACK_PROFILE, ordered_map, ORDERED_MAP_PROFILE),
                    "retained-persistence",
                    output,
                )
            self.assertEqual(0, code)
            self.assertTrue(output.is_file())

    def test_paths_do_not_change_report_and_nonauthority_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-resource-determinism-") as raw:
            directory = Path(raw)
            reports = []
            for name in ("first", "renamed"):
                child = directory / name
                child.mkdir()
                source, stack, ordered_map = _copy_inputs(child)
                output = child / "report.json"
                result = _run_resource(source, stack, ordered_map, output)
                self.assertEqual(0, result.returncode, result.stderr)
                reports.append(_read_json(output))
            self.assertEqual(reports[0], reports[1])
            report = reports[0]
            self.assertEqual("unestablished", report["satisfaction"])
            self.assertIn("Realization satisfaction", report["exclusions"])
            self.assertIn("Claim or Evidence transfer", report["exclusions"])
            rendered = json.dumps(report).casefold()
            self.assertNotIn("universally", rendered)
            self.assertNotIn("consumer accepted", rendered)
            self.assertNotIn("proven persistence", rendered)


if __name__ == "__main__":
    unittest.main()
