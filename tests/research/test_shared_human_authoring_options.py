from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from scripts import record_check


ROOT = Path(__file__).resolve().parents[2]
STACK_SPEC = ROOT / "registry" / "stack" / "theory" / "records" / "stack-spec.json"
STACK_PROFILE = (
    ROOT / "registry" / "stack" / "theory" / "dependencies" / "stack-profile.json"
)
ORDERED_MAP_SPEC = (
    ROOT / "registry" / "ordered-map" / "theory" / "records" / "ordered-map-spec.json"
)
ORDERED_MAP_PROFILE = (
    ROOT
    / "registry"
    / "ordered-map"
    / "theory"
    / "dependencies"
    / "ordered-map-profile.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _diagnostic_shape(diagnostic: record_check.Diagnostic) -> tuple[str, str, str]:
    return diagnostic.code, diagnostic.path, diagnostic.pointer


def _graph_diagnostics(specification: dict, profile: dict) -> list[record_check.Diagnostic]:
    return record_check.check_graph(
        {
            "author/specification.json": specification,
            "author/profile.json": profile,
        }
    )


class SharedHumanAuthoringOptionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = record_check.SchemaRegistry()

    def test_canonical_control_accepts_both_exact_domains(self) -> None:
        for spec_path, profile_path in (
            (STACK_SPEC, STACK_PROFILE),
            (ORDERED_MAP_SPEC, ORDERED_MAP_PROFILE),
        ):
            with self.subTest(specification=spec_path):
                specification = _load(spec_path)
                profile = _load(profile_path)
                self.assertIsNone(
                    record_check.validate_record(
                        self.schemas,
                        "author/specification.json",
                        specification,
                    )
                )
                self.assertIsNone(
                    record_check.validate_record(
                        self.schemas,
                        "author/profile.json",
                        profile,
                    )
                )
                self.assertEqual([], _graph_diagnostics(specification, profile))

    def test_missing_root_identity_has_an_exact_diagnostic(self) -> None:
        specification = _load(STACK_SPEC)
        del specification["id"]
        diagnostic = record_check.validate_record(
            self.schemas,
            "author/specification.json",
            specification,
        )
        self.assertIsNotNone(diagnostic)
        self.assertEqual(
            ("SCHEMA_MISSING_FIELD", "author/specification.json", "#/id"),
            _diagnostic_shape(diagnostic),
        )

    def test_unknown_record_kind_and_wrong_local_kind_have_exact_diagnostics(self) -> None:
        unknown = _load(STACK_SPEC)
        unknown["kind"] = "unknown"
        diagnostic = record_check.validate_record(
            self.schemas,
            "author/specification.json",
            unknown,
        )
        self.assertIsNotNone(diagnostic)
        self.assertEqual(
            ("SCHEMA_UNKNOWN_KIND", "author/specification.json", "#"),
            _diagnostic_shape(diagnostic),
        )

        wrong_local_kind = _load(STACK_SPEC)
        wrong_local_kind["equivalences"][0]["carrier"] = "empty"
        self.assertEqual(
            [("LINK_DECLARATION_KIND_MISMATCH", "#/equivalences/0/carrier")],
            [
                (item.code, item.pointer)
                for item in _graph_diagnostics(
                    wrong_local_kind,
                    _load(STACK_PROFILE),
                )
            ],
        )

    def test_duplicate_and_dangling_local_identity_fail_at_exact_paths(self) -> None:
        profile = _load(STACK_PROFILE)

        duplicate = _load(STACK_SPEC)
        duplicate["operations"][1]["id"] = duplicate["operations"][0]["id"]
        self.assertEqual(
            [
                ("LINK_DUPLICATE_DECLARATION_ID", "#/operations/1/id"),
                (
                    "LINK_DANGLING_DECLARATION",
                    "#/performancePropositions/0/operationFamily/0",
                ),
            ],
            [
                (diagnostic.code, diagnostic.pointer)
                for diagnostic in _graph_diagnostics(duplicate, profile)
            ],
        )

        dangling = _load(STACK_SPEC)
        dangling["equivalences"][0]["carrier"] = "MissingCarrier"
        self.assertEqual(
            [("LINK_DANGLING_DECLARATION", "#/equivalences/0/carrier")],
            [
                (diagnostic.code, diagnostic.pointer)
                for diagnostic in _graph_diagnostics(dangling, profile)
            ],
        )

    def test_dangling_profile_member_fails_at_the_exact_nested_path(self) -> None:
        specification = _load(STACK_SPEC)
        specification["performancePropositions"][0]["workload"]["localId"] = (
            "missing-workload"
        )
        self.assertEqual(
            [
                (
                    "LINK_DANGLING_PROFILE_MEMBER",
                    "#/performancePropositions/0/workload/localId",
                )
            ],
            [
                (diagnostic.code, diagnostic.pointer)
                for diagnostic in _graph_diagnostics(
                    specification,
                    _load(STACK_PROFILE),
                )
            ],
        )

    def test_blank_hosted_payload_exposes_the_coarse_diagnostic_deficit(self) -> None:
        specification = _load(STACK_SPEC)
        specification["laws"][0]["statement"] = ""
        diagnostic = record_check.validate_record(
            self.schemas,
            "author/specification.json",
            specification,
        )
        self.assertIsNotNone(diagnostic)
        self.assertEqual(
            ("SCHEMA_INVALID", "author/specification.json", "#"),
            _diagnostic_shape(diagnostic),
        )

    def test_ordinary_json_control_silently_collapses_duplicate_members(self) -> None:
        duplicate_id = (
            '{"kind":"specification","id":"stack","id":"shadow",'
            '"version":"0.1.0","laws":[{"id":"x","statement":"x"}]}'
        )
        decoded = json.loads(duplicate_id)
        self.assertEqual("shadow", decoded["id"])
        self.assertNotEqual("stack", decoded["id"])

    def test_raw_decode_failures_are_exceptions_not_author_diagnostics(self) -> None:
        with self.assertRaises(UnicodeDecodeError):
            b"\xff".decode("utf-8")
        with self.assertRaises(json.JSONDecodeError):
            json.loads("{")

    def test_existing_diagnostics_replay_deterministically(self) -> None:
        specification = _load(STACK_SPEC)
        specification["equivalences"][0]["carrier"] = "MissingCarrier"
        observed = [
            tuple(
                _diagnostic_shape(item)
                for item in _graph_diagnostics(
                    deepcopy(specification),
                    _load(STACK_PROFILE),
                )
            )
            for _ in range(3)
        ]
        self.assertEqual([observed[0], observed[0], observed[0]], observed)

    def test_declaration_order_changes_documents_not_local_addresses(self) -> None:
        specification = _load(ORDERED_MAP_SPEC)
        reordered = deepcopy(specification)
        reordered["laws"] = list(reversed(reordered["laws"]))
        self.assertNotEqual(specification, reordered)
        self.assertEqual(
            {law["id"] for law in specification["laws"]},
            {law["id"] for law in reordered["laws"]},
        )
        self.assertEqual(
            [],
            _graph_diagnostics(reordered, _load(ORDERED_MAP_PROFILE)),
        )


if __name__ == "__main__":
    unittest.main()
