from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import unittest
from copy import deepcopy
from pathlib import Path

from scripts import record_check


ROOT = Path(__file__).resolve().parents[2]
STACK_SPEC = ROOT / "registry/stack/theory/records/stack-spec.json"
STACK_PROFILE = ROOT / "registry/stack/theory/dependencies/stack-profile.json"
ORDERED_MAP_SPEC = (
    ROOT / "registry/ordered-map/theory/records/ordered-map-spec.json"
)
ORDERED_MAP_PROFILE = (
    ROOT / "registry/ordered-map/theory/dependencies/ordered-map-profile.json"
)
FORMAT = "canonical-spec-json-v1"

EXPECTED_SHA256 = {
    STACK_SPEC: "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1",
    STACK_PROFILE: "2a51ed7d2e1266376cd4a58ef3f20d30244655d25cb884816576be989014eddb",
    ORDERED_MAP_SPEC: "6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f",
    ORDERED_MAP_PROFILE: "6d1297892c355a569e244c2b94448a5f5edaf9b1bf2ae54f940d7c4494fe225f",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_bytes(document: dict) -> bytes:
    return json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _import_authoring():
    try:
        return importlib.import_module("semantic_packages.authoring"), None
    except ModuleNotFoundError as error:
        if error.name != "semantic_packages.authoring":
            raise
        return None, error


authoring, AUTHORING_IMPORT_ERROR = _import_authoring()
AUTHORING_READY = authoring is not None


def _dependency(path: Path, label: str):
    assert authoring is not None
    return authoring.AuthoringDependency(
        source_label=label,
        document=_load(path),
    )


def _author(
    document: dict,
    *,
    label: str = "author/specification.json",
    profile: Path | None = STACK_PROFILE,
):
    assert authoring is not None
    dependencies = (
        ()
        if profile is None
        else (_dependency(profile, "dependency/profile.json"),)
    )
    return authoring.author_specification(
        _canonical_bytes(document),
        format_token=FORMAT,
        source_label=label,
        dependencies=dependencies,
    )


def _shape(diagnostic: record_check.Diagnostic) -> tuple[str, str, str]:
    return diagnostic.code, diagnostic.path, diagnostic.pointer


@unittest.skipUnless(AUTHORING_READY, "A4 authoring module not implemented")
class SharedHumanAuthoringSuccessorContractTest(unittest.TestCase):
    def test_public_boundary_has_no_format_or_dependency_default(self) -> None:
        signature = inspect.signature(authoring.author_specification)
        self.assertEqual(
            ("source", "format_token", "source_label", "dependencies"),
            tuple(signature.parameters),
        )
        self.assertEqual(
            inspect.Parameter.empty,
            signature.parameters["format_token"].default,
        )
        self.assertEqual(
            inspect.Parameter.empty,
            signature.parameters["source_label"].default,
        )
        self.assertEqual(
            inspect.Parameter.empty,
            signature.parameters["dependencies"].default,
        )
        self.assertEqual(FORMAT, authoring.CANONICAL_SPEC_JSON_V1)

    def test_stack_and_ordered_map_round_trip_as_exact_documents(self) -> None:
        for spec_path, profile_path in (
            (STACK_SPEC, STACK_PROFILE),
            (ORDERED_MAP_SPEC, ORDERED_MAP_PROFILE),
        ):
            with self.subTest(specification=spec_path):
                expected = _load(spec_path)
                observation = _author(expected, profile=profile_path)
                self.assertTrue(observation.ok)
                self.assertEqual(expected, observation.document)
                self.assertEqual((), observation.diagnostics)

    def test_external_references_require_explicit_finite_context(self) -> None:
        observation = _author(_load(STACK_SPEC), profile=None)
        self.assertFalse(observation.ok)
        self.assertIsNone(observation.document)
        self.assertEqual(
            (
                (
                    "LINK_DANGLING_REFERENCE",
                    "author/specification.json",
                    "#/performancePropositions/0/costMeasure/profile",
                ),
                (
                    "LINK_DANGLING_REFERENCE",
                    "author/specification.json",
                    "#/performancePropositions/0/workload/profile",
                ),
            ),
            tuple(_shape(item) for item in observation.diagnostics),
        )

    def test_dependency_context_is_validated_ordered_and_nonauthoritative(self) -> None:
        source = _load(STACK_SPEC)
        correct = _dependency(STACK_PROFILE, "z/stack-profile.json")
        irrelevant = _dependency(ORDERED_MAP_PROFILE, "a/ordered-map-profile.json")

        for dependencies in ((correct, irrelevant), (irrelevant, correct)):
            with self.subTest(order=tuple(item.source_label for item in dependencies)):
                observation = authoring.author_specification(
                    _canonical_bytes(source),
                    format_token=FORMAT,
                    source_label="author/source.json",
                    dependencies=dependencies,
                )
                self.assertTrue(observation.ok)
                self.assertEqual(source, observation.document)

        renamed = authoring.AuthoringDependency(
            source_label="renamed/context.json",
            document=_load(STACK_PROFILE),
        )
        observation = authoring.author_specification(
            _canonical_bytes(source),
            format_token=FORMAT,
            source_label="author/source.json",
            dependencies=(renamed,),
        )
        self.assertTrue(observation.ok)
        self.assertEqual(source, observation.document)

        wrong_context = authoring.author_specification(
            _canonical_bytes(source),
            format_token=FORMAT,
            source_label="author/source.json",
            dependencies=(irrelevant,),
        )
        self.assertFalse(wrong_context.ok)
        self.assertIsNone(wrong_context.document)
        self.assertEqual(
            (
                (
                    "LINK_DANGLING_REFERENCE",
                    "author/source.json",
                    "#/performancePropositions/0/costMeasure/profile",
                ),
                (
                    "LINK_DANGLING_REFERENCE",
                    "author/source.json",
                    "#/performancePropositions/0/workload/profile",
                ),
            ),
            tuple(_shape(item) for item in wrong_context.diagnostics),
        )

        missing_version = _load(STACK_PROFILE)
        del missing_version["version"]
        missing_id = _load(ORDERED_MAP_PROFILE)
        del missing_id["id"]
        first = authoring.AuthoringDependency("z/first.json", missing_version)
        second = authoring.AuthoringDependency("a/second.json", missing_id)
        for dependencies, expected_diagnostics in (
            (
                (first, second),
                (
                    ("SCHEMA_MISSING_FIELD", "z/first.json", "#/version"),
                    ("SCHEMA_MISSING_FIELD", "a/second.json", "#/id"),
                ),
            ),
            (
                (second, first),
                (
                    ("SCHEMA_MISSING_FIELD", "a/second.json", "#/id"),
                    ("SCHEMA_MISSING_FIELD", "z/first.json", "#/version"),
                ),
            ),
        ):
            with self.subTest(invalid_order=expected_diagnostics):
                invalid = authoring.author_specification(
                    _canonical_bytes(source),
                    format_token=FORMAT,
                    source_label="author/source.json",
                    dependencies=dependencies,
                )
                self.assertFalse(invalid.ok)
                self.assertIsNone(invalid.document)
                self.assertEqual(
                    expected_diagnostics,
                    tuple(_shape(item) for item in invalid.diagnostics),
                )
                self.assertNotIn(
                    "LINK_DANGLING_REFERENCE",
                    {item.code for item in invalid.diagnostics},
                )

        duplicate = authoring.author_specification(
            _canonical_bytes(source),
            format_token=FORMAT,
            source_label="author/source.json",
            dependencies=(
                correct,
                authoring.AuthoringDependency(
                    "duplicate/stack-profile.json", _load(STACK_PROFILE)
                ),
            ),
        )
        self.assertFalse(duplicate.ok)
        self.assertIsNone(duplicate.document)
        self.assertEqual(
            (
                (
                    "LINK_DUPLICATE_ADDRESS",
                    "duplicate/stack-profile.json",
                    "#",
                ),
            ),
            tuple(_shape(item) for item in duplicate.diagnostics),
        )

    def test_schema_valid_non_specification_source_is_rejected(self) -> None:
        observation = authoring.author_specification(
            _canonical_bytes(_load(STACK_PROFILE)),
            format_token=FORMAT,
            source_label="author/source.json",
            dependencies=(),
        )
        self.assertIsNone(observation.document)
        self.assertEqual(
            (("AUTHOR_EXPECTED_SPECIFICATION", "author/source.json", "#/kind"),),
            tuple(_shape(item) for item in observation.diagnostics),
        )

    def test_source_label_is_provenance_only_on_success(self) -> None:
        source = _load(STACK_SPEC)
        left = _author(source, label="left/source.json")
        right = _author(source, label="right/renamed.json")
        self.assertEqual(left.document, right.document)
        self.assertEqual((), left.diagnostics)
        self.assertEqual((), right.diagnostics)

    def test_source_label_changes_only_diagnostic_path_on_failure(self) -> None:
        source = _load(STACK_SPEC)
        del source["id"]
        left = _author(source, label="left/source.json")
        right = _author(source, label="right/renamed.json")
        self.assertIsNone(left.document)
        self.assertIsNone(right.document)
        self.assertEqual(
            (("SCHEMA_MISSING_FIELD", "#/id"),),
            tuple((item.code, item.pointer) for item in left.diagnostics),
        )
        self.assertEqual(
            tuple((item.code, item.pointer) for item in left.diagnostics),
            tuple((item.code, item.pointer) for item in right.diagnostics),
        )
        self.assertEqual(("left/source.json",), tuple(d.path for d in left.diagnostics))
        self.assertEqual(
            ("right/renamed.json",), tuple(d.path for d in right.diagnostics)
        )

    def test_unknown_format_fails_before_source_decoding(self) -> None:
        observation = authoring.author_specification(
            b"\xff",
            format_token="unknown",
            source_label="author/source",
            dependencies=(),
        )
        self.assertIsNone(observation.document)
        self.assertEqual(
            (("AUTHOR_FORMAT_UNSUPPORTED", "author/source", "#"),),
            tuple(_shape(item) for item in observation.diagnostics),
        )

    def test_invalid_utf8_fails_before_json_and_record_validation(self) -> None:
        observation = authoring.author_specification(
            b"\xff{",
            format_token=FORMAT,
            source_label="author/source",
            dependencies=(),
        )
        self.assertIsNone(observation.document)
        self.assertEqual(
            (("AUTHOR_INVALID_UTF8", "author/source", "#"),),
            tuple(_shape(item) for item in observation.diagnostics),
        )
        self.assertEqual("invalid UTF-8 at byte 0", observation.diagnostics[0].message)

    def test_malformed_json_fails_before_record_validation(self) -> None:
        observation = authoring.author_specification(
            b'{"kind":"specification"',
            format_token=FORMAT,
            source_label="author/source",
            dependencies=(),
        )
        self.assertIsNone(observation.document)
        self.assertEqual(
            (("AUTHOR_INVALID_JSON", "author/source", "#"),),
            tuple(_shape(item) for item in observation.diagnostics),
        )
        self.assertEqual(
            "invalid JSON at line 1 column 24 (character 23)",
            observation.diagnostics[0].message,
        )

    def test_duplicate_object_member_fails_before_schema_validation(self) -> None:
        observation = authoring.author_specification(
            b'{"kind":"specification","id":"stack","id":"shadow"}',
            format_token=FORMAT,
            source_label="author/source",
            dependencies=(),
        )
        self.assertIsNone(observation.document)
        self.assertEqual(
            (("AUTHOR_DUPLICATE_MEMBER", "author/source", "#"),),
            tuple(_shape(item) for item in observation.diagnostics),
        )
        self.assertEqual(
            "duplicate object member: id", observation.diagnostics[0].message
        )

    def test_missing_and_unknown_root_identity_are_exact(self) -> None:
        missing = _load(STACK_SPEC)
        del missing["id"]
        unknown = _load(STACK_SPEC)
        unknown["kind"] = "unknown"
        self.assertEqual(
            (("SCHEMA_MISSING_FIELD", "#/id"),),
            tuple((d.code, d.pointer) for d in _author(missing).diagnostics),
        )
        self.assertEqual(
            (("SCHEMA_UNKNOWN_KIND", "#"),),
            tuple((d.code, d.pointer) for d in _author(unknown).diagnostics),
        )

        missing_local_id = _load(STACK_SPEC)
        del missing_local_id["operations"][0]["id"]
        self.assertEqual(
            (("SCHEMA_MISSING_FIELD", "#/operations/0/id"),),
            tuple((d.code, d.pointer) for d in _author(missing_local_id).diagnostics),
        )

        missing_local_reference = _load(STACK_SPEC)
        del missing_local_reference["equivalences"][0]["carrier"]
        self.assertEqual(
            (("SCHEMA_MISSING_FIELD", "#/equivalences/0/carrier"),),
            tuple(
                (d.code, d.pointer)
                for d in _author(missing_local_reference).diagnostics
            ),
        )

    def test_duplicate_dangling_and_wrong_kind_local_references_are_exact(self) -> None:
        duplicate = _load(STACK_SPEC)
        duplicate["operations"][1]["id"] = duplicate["operations"][0]["id"]
        self.assertEqual(
            (
                ("LINK_DUPLICATE_DECLARATION_ID", "#/operations/1/id"),
                (
                    "LINK_DANGLING_DECLARATION",
                    "#/performancePropositions/0/operationFamily/0",
                ),
            ),
            tuple((d.code, d.pointer) for d in _author(duplicate).diagnostics),
        )

        dangling = _load(STACK_SPEC)
        dangling["equivalences"][0]["carrier"] = "MissingCarrier"
        self.assertEqual(
            (("LINK_DANGLING_DECLARATION", "#/equivalences/0/carrier"),),
            tuple((d.code, d.pointer) for d in _author(dangling).diagnostics),
        )

        wrong_kind = _load(STACK_SPEC)
        wrong_kind["equivalences"][0]["carrier"] = "empty"
        self.assertEqual(
            (("LINK_DECLARATION_KIND_MISMATCH", "#/equivalences/0/carrier"),),
            tuple((d.code, d.pointer) for d in _author(wrong_kind).diagnostics),
        )

    def test_blank_hosted_payload_is_actionable_without_claiming_meaning(self) -> None:
        source = _load(STACK_SPEC)
        source["laws"][0]["statement"] = ""
        observation = _author(source)
        self.assertIsNone(observation.document)
        self.assertEqual(
            (("SCHEMA_NONEMPTY_STRING", "#/laws/0/statement"),),
            tuple((d.code, d.pointer) for d in observation.diagnostics),
        )

        opaque = _load(STACK_SPEC)
        opaque_text = "forall x: hosted tokens remain opaque {{not interpreted}}"
        opaque["laws"][0]["statement"] = opaque_text
        preserved = _author(opaque)
        self.assertTrue(preserved.ok)
        self.assertEqual(opaque_text, preserved.document["laws"][0]["statement"])

    def test_explicit_declaration_order_is_preserved_but_not_addressing(self) -> None:
        source = _load(ORDERED_MAP_SPEC)
        reordered = deepcopy(source)
        reordered["laws"] = list(reversed(reordered["laws"]))
        observation = _author(reordered, profile=ORDERED_MAP_PROFILE)
        self.assertTrue(observation.ok)
        self.assertEqual(reordered, observation.document)
        self.assertNotEqual(source, observation.document)
        self.assertEqual(
            {item["id"] for item in source["laws"]},
            {item["id"] for item in observation.document["laws"]},
        )

    def test_failure_diagnostics_replay_in_one_exact_order(self) -> None:
        source = _load(STACK_SPEC)
        source["operations"][1]["id"] = source["operations"][0]["id"]
        observed = [
            tuple(_shape(item) for item in _author(deepcopy(source)).diagnostics)
            for _ in range(3)
        ]
        self.assertEqual((observed[0], observed[0], observed[0]), tuple(observed))

    def test_observation_does_not_expose_mutable_input_or_output_authority(self) -> None:
        source = _load(STACK_SPEC)
        dependency_document = _load(STACK_PROFILE)
        dependency = authoring.AuthoringDependency(
            source_label="dependency/profile.json",
            document=dependency_document,
        )
        observation = authoring.author_specification(
            _canonical_bytes(source),
            format_token=FORMAT,
            source_label="author/source.json",
            dependencies=(dependency,),
        )
        source["id"] = "mutated-input"
        dependency_document["id"] = "mutated-dependency"
        first = observation.document
        first["id"] = "mutated-output"
        self.assertEqual("stack", observation.document["id"])


class SharedHumanAuthoringRedTopologyTest(unittest.TestCase):
    def test_exact_accepted_inputs_and_dependency_gap_are_frozen(self) -> None:
        for path, expected in EXPECTED_SHA256.items():
            with self.subTest(path=path):
                self.assertEqual(expected, hashlib.sha256(path.read_bytes()).hexdigest())

        stack = _load(STACK_SPEC)
        diagnostics = record_check.check_graph({"author/stack.json": stack})
        self.assertEqual(
            (
                (
                    "LINK_DANGLING_REFERENCE",
                    "#/performancePropositions/0/costMeasure/profile",
                ),
                (
                    "LINK_DANGLING_REFERENCE",
                    "#/performancePropositions/0/workload/profile",
                ),
            ),
            tuple((item.code, item.pointer) for item in diagnostics),
        )

    def test_a4_module_is_the_only_intentional_red_predecessor(self) -> None:
        self.assertIsNone(
            AUTHORING_IMPORT_ERROR,
            "A4 must provide semantic_packages.authoring before successor controls run",
        )


if __name__ == "__main__":
    unittest.main()
