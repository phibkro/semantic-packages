from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "contracts" / "ordered-map" / "conformance-plan.json"
SCHEMA = ROOT / "schemas" / "ordered-map-conformance-plan.schema.json"
EXPECTED_SHA256 = "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a"

try:
    artifact = importlib.import_module("semantic_packages.canonical_artifact")
    ARTIFACT_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.canonical_artifact":
        raise
    artifact = None
    ARTIFACT_IMPORT_ERROR = error

try:
    ordered_map = importlib.import_module("semantic_packages.ordered_map_contract")
    ORDERED_MAP_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.ordered_map_contract":
        raise
    ordered_map = None
    ORDERED_MAP_IMPORT_ERROR = error


def _canonical_sha256(document: dict) -> str:
    content = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class OrderedMapPlanBoundaryPreconditionTest(unittest.TestCase):
    def test_exact_artifacts_are_green_before_the_shared_loader(self) -> None:
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        self.assertEqual(EXPECTED_SHA256, _canonical_sha256(plan))
        self.assertTrue(SCHEMA.is_file())

    def test_canonical_artifact_loader_is_the_intentional_red_predecessor(self) -> None:
        self.assertIsNotNone(
            artifact,
            "O3b intentionally precedes semantic_packages/canonical_artifact.py; "
            f"observed {ARTIFACT_IMPORT_ERROR!r}",
        )
        self.assertIsNotNone(
            ordered_map,
            "O3b intentionally precedes semantic_packages/ordered_map_contract.py; "
            f"observed {ORDERED_MAP_IMPORT_ERROR!r}",
        )


@unittest.skipIf(
    artifact is None or ordered_map is None,
    "O3b freezes the artifact boundary before its O4 implementation",
)
class CanonicalPlanBoundaryContractTest(unittest.TestCase):
    def _inspect(self, plan: Path, schema: Path = SCHEMA, expected: str = EXPECTED_SHA256):
        return artifact.inspect_json_artifact(
            plan,
            schema_path=schema,
            expected_canonical_sha256=expected,
            label="ordered-map-conformance-plan",
        )

    @staticmethod
    def _codes(observation) -> list[str]:
        return [item.code for item in observation.diagnostics]

    def test_no_argument_product_wrapper_pins_reviewed_plan(self) -> None:
        self.assertEqual((), tuple(inspect.signature(ordered_map.inspect_conformance_plan).parameters))
        observation = ordered_map.inspect_conformance_plan()
        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(EXPECTED_SHA256, observation.canonical_sha256)
        self.assertEqual("ordered-map-conformance-campaign", observation.document["algorithm"])
        with self.assertRaises(TypeError):
            ordered_map.inspect_conformance_plan(PLAN)
        for keyword, value in (
            ("plan", PLAN),
            ("plan_path", PLAN),
            ("schema_path", SCHEMA),
            ("expected_canonical_sha256", EXPECTED_SHA256),
            ("contract", object()),
            ("configuration", object()),
        ):
            with self.subTest(keyword=keyword), self.assertRaises(TypeError):
                ordered_map.inspect_conformance_plan(**{keyword: value})

    def test_schema_valid_alternate_plan_is_non_authoritative(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o3b-alternate-") as raw:
            path = Path(raw) / "plan.json"
            document = json.loads(PLAN.read_text(encoding="utf-8"))
            document["cases"] = list(reversed(document["cases"]))
            path.write_text(json.dumps(document), encoding="utf-8")
            observation = self._inspect(path)
        self.assertFalse(observation.ok)
        self.assertEqual(["ARTIFACT_CANONICAL_DIGEST_MISMATCH"], self._codes(observation))
        self.assertIsNone(observation.document)
        self.assertIsNone(observation.canonical_sha256)
        diagnostic = observation.diagnostics[0]
        self.assertEqual(os.fspath(path), diagnostic.path)
        self.assertEqual("#", diagnostic.pointer)
        observed = _canonical_sha256(document)
        self.assertEqual(
            f"canonical SHA-256 {observed}, expected {EXPECTED_SHA256}",
            diagnostic.message,
        )

    def test_duplicate_member_fails_before_digest_or_schema_conclusions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o3b-duplicate-") as raw:
            path = Path(raw) / "plan.json"
            text = PLAN.read_text(encoding="utf-8")
            text = text.replace(
                '"maximumHistory": 3,',
                '"maximumHistory": 3,\n    "maximumHistory": 3,',
                1,
            )
            path.write_text(text, encoding="utf-8")
            observation = self._inspect(path)
        self.assertFalse(observation.ok)
        self.assertEqual(["ARTIFACT_DUPLICATE_MEMBER"], self._codes(observation))
        self.assertIsNone(observation.document)
        self.assertIsNone(observation.canonical_sha256)
        self.assertEqual(os.fspath(path), observation.diagnostics[0].path)
        self.assertEqual("#", observation.diagnostics[0].pointer)
        self.assertIn("maximumHistory", observation.diagnostics[0].message)

    def test_invalid_json_and_schema_are_distinct_phase_failures(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o3b-invalid-") as raw:
            malformed = Path(raw) / "malformed.json"
            malformed.write_text("{ malformed\n", encoding="utf-8")
            malformed_result = self._inspect(malformed)

            invalid = Path(raw) / "invalid.json"
            document = json.loads(PLAN.read_text(encoding="utf-8"))
            document["protocol"] = "stack-runner-json-v1"
            invalid.write_text(json.dumps(document), encoding="utf-8")
            invalid_result = self._inspect(invalid)

        self.assertEqual(["INPUT_INVALID_JSON"], self._codes(malformed_result))
        self.assertEqual(["ARTIFACT_SCHEMA_INVALID"], self._codes(invalid_result))
        for result in (malformed_result, invalid_result):
            self.assertIsNone(result.document)
            self.assertIsNone(result.canonical_sha256)
        self.assertEqual(os.fspath(malformed), malformed_result.diagnostics[0].path)
        self.assertEqual("#", malformed_result.diagnostics[0].pointer)
        self.assertEqual(os.fspath(invalid), invalid_result.diagnostics[0].path)
        self.assertEqual("/protocol", invalid_result.diagnostics[0].pointer)

    def test_invalid_schema_fails_closed_without_artifact_conclusions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o3b-schema-") as raw:
            schema = Path(raw) / "schema.json"
            schema.write_text('{"type": 7}\n', encoding="utf-8")
            observation = self._inspect(PLAN, schema=schema)
        self.assertEqual(["ARTIFACT_SCHEMA_CONTRACT_ERROR"], self._codes(observation))
        self.assertIsNone(observation.document)
        self.assertIsNone(observation.canonical_sha256)
        self.assertEqual(os.fspath(schema), observation.diagnostics[0].path)
        self.assertEqual("#", observation.diagnostics[0].pointer)
        self.assertTrue(observation.diagnostics[0].message)

    def test_symlink_directory_and_absent_inputs_fail_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o3b-source-") as raw:
            root = Path(raw)
            link = root / "plan-link.json"
            link.symlink_to(PLAN)
            ancestor = root / "ancestor"
            ancestor.symlink_to(PLAN.parent, target_is_directory=True)
            cases = {
                "symlink": self._inspect(link),
                "ancestor-symlink": self._inspect(ancestor / PLAN.name),
                "directory": self._inspect(root),
                "absent": self._inspect(root / "absent.json"),
            }
        self.assertEqual(["INPUT_SYMLINK"], self._codes(cases["symlink"]))
        self.assertEqual(["INPUT_SYMLINK"], self._codes(cases["ancestor-symlink"]))
        self.assertEqual(["INPUT_UNSUPPORTED_TYPE"], self._codes(cases["directory"]))
        self.assertEqual(["INPUT_NOT_FOUND"], self._codes(cases["absent"]))
        expected_paths = {
            "symlink": link,
            "ancestor-symlink": ancestor / PLAN.name,
            "directory": root,
            "absent": root / "absent.json",
        }
        for name, expected_path in expected_paths.items():
            diagnostic = cases[name].diagnostics[0]
            self.assertEqual(os.fspath(expected_path), diagnostic.path)
            self.assertEqual("#", diagnostic.pointer)
        for observation in cases.values():
            self.assertIsNone(observation.document)
            self.assertIsNone(observation.canonical_sha256)

    def test_schema_source_rejects_absent_directory_and_symlink_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o3b-schema-source-") as raw:
            root = Path(raw)
            leaf = root / "schema-link.json"
            leaf.symlink_to(SCHEMA)
            ancestor = root / "ancestor"
            ancestor.symlink_to(SCHEMA.parent, target_is_directory=True)
            cases = {
                "leaf": self._inspect(PLAN, schema=leaf),
                "ancestor": self._inspect(PLAN, schema=ancestor / SCHEMA.name),
                "directory": self._inspect(PLAN, schema=root),
                "absent": self._inspect(PLAN, schema=root / "absent.json"),
            }
        self.assertEqual(["INPUT_SYMLINK"], self._codes(cases["leaf"]))
        self.assertEqual(["INPUT_SYMLINK"], self._codes(cases["ancestor"]))
        self.assertEqual(["INPUT_UNSUPPORTED_TYPE"], self._codes(cases["directory"]))
        self.assertEqual(["INPUT_NOT_FOUND"], self._codes(cases["absent"]))
        expected_paths = {
            "leaf": leaf,
            "ancestor": ancestor / SCHEMA.name,
            "directory": root,
            "absent": root / "absent.json",
        }
        for name, expected_path in expected_paths.items():
            diagnostic = cases[name].diagnostics[0]
            self.assertEqual(os.fspath(expected_path), diagnostic.path)
            self.assertEqual("#", diagnostic.pointer)
        for observation in cases.values():
            self.assertIsNone(observation.document)
            self.assertIsNone(observation.canonical_sha256)

    def test_capture_is_detached_from_later_file_changes_and_never_executes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o3b-capture-") as raw:
            path = Path(raw) / "plan.json"
            shutil.copyfile(PLAN, path)
            with ExitStack() as stack:
                for target in (
                    "subprocess.Popen",
                    "subprocess.run",
                    "os.system",
                    "os.execv",
                    "os.execve",
                ):
                    stack.enter_context(mock.patch(target, side_effect=AssertionError("execution")))
                observation = self._inspect(path)
            self.assertTrue(observation.ok, observation.diagnostics)
            with self.assertRaises(TypeError):
                observation.document["algorithm"] = "mutated"
            with self.assertRaises((AttributeError, TypeError)):
                observation.document["cases"].append({})
            with self.assertRaises(TypeError):
                observation.document["specification"]["address"]["id"] = "mutated"
            with self.assertRaises(TypeError):
                observation.document["cases"][0]["steps"][0]["bind"] = "mutated"
            path.write_text("{}\n", encoding="utf-8")
            replay = self._inspect(PLAN)
        self.assertEqual(
            "ordered-map-conformance-campaign", observation.document["algorithm"]
        )
        self.assertTrue(replay.ok, replay.diagnostics)
        self.assertEqual((), replay.diagnostics)
        self.assertEqual(observation.document, replay.document)
        self.assertEqual(EXPECTED_SHA256, observation.canonical_sha256)
        self.assertEqual(EXPECTED_SHA256, replay.canonical_sha256)

    def test_diagnostics_are_stable_and_do_not_leak_file_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o3b-secret-") as raw:
            path = Path(raw) / "plan.json"
            secret = "operator-secret-do-not-render"
            path.write_text('{"secret":"' + secret + '"}\n', encoding="utf-8")
            observation = self._inspect(path)
        self.assertFalse(observation.ok)
        self.assertIsNone(observation.document)
        self.assertIsNone(observation.canonical_sha256)
        rendered = "\n".join(item.format() for item in observation.diagnostics)
        self.assertNotIn(secret, rendered)
        self.assertIn(os.fspath(path), rendered)

    def test_root_and_embedded_nul_sources_fail_as_observations(self) -> None:
        nul = Path("embedded\0member.json")
        cases = {
            "artifact-root": self._inspect(Path("/")),
            "artifact-nul": self._inspect(nul),
            "schema-root": self._inspect(PLAN, schema=Path("/")),
            "schema-nul": self._inspect(PLAN, schema=nul),
        }
        self.assertEqual(["INPUT_UNSUPPORTED_TYPE"], self._codes(cases["artifact-root"]))
        self.assertEqual(["INPUT_READ_ERROR"], self._codes(cases["artifact-nul"]))
        self.assertEqual(["INPUT_UNSUPPORTED_TYPE"], self._codes(cases["schema-root"]))
        self.assertEqual(["INPUT_READ_ERROR"], self._codes(cases["schema-nul"]))
        for observation in cases.values():
            self.assertFalse(observation.ok)
            self.assertIsNone(observation.document)
            self.assertIsNone(observation.canonical_sha256)

    def test_nonstandard_json_constants_are_rejected_before_schema_or_digest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o4a-nonfinite-") as raw:
            root = Path(raw)
            schema = root / "permissive.schema.json"
            schema.write_text(
                '{"$schema":"https://json-schema.org/draft/2020-12/schema"}\n',
                encoding="utf-8",
            )
            observations = []
            for index, content in enumerate(
                ('{"value":NaN}', '{"value":[Infinity,-Infinity]}')
            ):
                path = root / f"nonfinite-{index}.json"
                path.write_text(content + "\n", encoding="utf-8")
                observations.append(self._inspect(path, schema=schema, expected="0" * 64))
        for observation in observations:
            self.assertEqual(["INPUT_INVALID_JSON"], self._codes(observation))
            self.assertIsNone(observation.document)
            self.assertIsNone(observation.canonical_sha256)

    def test_nesting_is_bounded_before_schema_hash_and_freeze(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o4a-depth-") as raw:
            root = Path(raw)
            schema = root / "permissive.schema.json"
            schema.write_text(
                '{"$schema":"https://json-schema.org/draft/2020-12/schema"}\n',
                encoding="utf-8",
            )
            observations = []
            for index, depth in enumerate((129, 2000)):
                path = root / f"depth-{index}.json"
                path.write_text("[" * depth + "0" + "]" * depth, encoding="utf-8")
                observations.append(self._inspect(path, schema=schema, expected="0" * 64))
        for observation in observations:
            self.assertEqual(["ARTIFACT_NESTING_LIMIT"], self._codes(observation))
            self.assertIsNone(observation.document)
            self.assertIsNone(observation.canonical_sha256)


if __name__ == "__main__":
    unittest.main()
