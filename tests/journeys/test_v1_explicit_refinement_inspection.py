"""Contract tests for design-spec 0002's explicit refinement inspection."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
DESIGN_SPEC = ROOT / "design-specs/0002-explicit-refinement-inspection-journey.md"
EXEC_PLAN = ROOT / "docs/exec-plans/active/0007-explicit-refinement-inspection.md"
STACK_PROPOSAL = ROOT / "refinements/stack-0.1.0-to-0.2.0.prefine"
STACK_PREDECESSOR = ROOT / "registry/stack/theory/records/stack-spec.json"
STACK_SUCCESSOR = ROOT / "registry/stack/successors/j5/theory/stack-spec.json"
ORDERED_PROPOSAL = ROOT / "refinements/ordered-map-0.1.0-to-0.2.0.prefine"
ORDERED_PREDECESSOR = ROOT / "registry/ordered-map/theory/records/ordered-map-spec.json"
ORDERED_SUCCESSOR = (
    ROOT / "registry/ordered-map/successors/o8/theory/ordered-map-spec.json"
)
REFINEMENT_READY = (
    importlib.util.find_spec("semantic_packages.refinement_command") is not None
)
FAMILIES = (
    "carriers",
    "operations",
    "observations",
    "derivedObservations",
    "equivalences",
    "laws",
    "effects",
    "resources",
    "performancePropositions",
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _declarations(document: dict) -> dict[tuple[str, str], dict]:
    declarations: dict[tuple[str, str], dict] = {}
    for family in FAMILIES:
        values = document.get(family, [])
        if isinstance(values, dict):
            values = [values]
        for value in values:
            declarations[(family, value["id"])] = value
    return declarations


def _proposal_ref(value: dict) -> tuple[str, str]:
    return value["family"], value["localId"]


def _tree_snapshot(root: Path) -> tuple[tuple[str, str], ...]:
    return tuple(
        (path.relative_to(root).as_posix(), _raw_sha256(path))
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


def _run_refinement(
    proposal: Path,
    predecessor: Path,
    successor: Path,
    output: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "semantic_packages",
            "refinement",
            "inspect",
            str(proposal),
            "--predecessor",
            str(predecessor),
            "--successor",
            str(successor),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class ExplicitRefinementRedBaselineTest(unittest.TestCase):
    def test_contract_plan_and_complete_proposals_freeze_exact_census(self) -> None:
        self.assertTrue(DESIGN_SPEC.is_file())
        self.assertTrue(EXEC_PLAN.is_file())
        for proposal_path, predecessor_path, successor_path, expected in (
            (STACK_PROPOSAL, STACK_PREDECESSOR, STACK_SUCCESSOR, (10, 1, 0, 0)),
            (
                ORDERED_PROPOSAL,
                ORDERED_PREDECESSOR,
                ORDERED_SUCCESSOR,
                (18, 0, 2, 0),
            ),
        ):
            proposal = tomllib.loads(proposal_path.read_text(encoding="utf-8"))
            predecessor = _declarations(_read_json(predecessor_path))
            successor = _declarations(_read_json(successor_path))
            self.assertEqual(_raw_sha256(predecessor_path), proposal["predecessor"]["rawSha256"])
            self.assertEqual(_raw_sha256(successor_path), proposal["successor"]["rawSha256"])

            mappings = proposal.get("mappings", [])
            additions = proposal.get("additions", [])
            removals = proposal.get("removals", [])
            mapped_predecessors = [_proposal_ref(item["predecessor"]) for item in mappings]
            mapped_successors = [_proposal_ref(item["successor"]) for item in mappings]
            added = [_proposal_ref(item["successor"]) for item in additions]
            removed = [_proposal_ref(item["predecessor"]) for item in removals]
            self.assertEqual(set(predecessor), set(mapped_predecessors) | set(removed))
            self.assertEqual(set(successor), set(mapped_successors) | set(added))
            self.assertEqual(len(mapped_predecessors), len(set(mapped_predecessors)))
            self.assertEqual(len(mapped_successors), len(set(mapped_successors)))
            self.assertEqual(
                expected,
                (
                    sum(
                        predecessor[left] == successor[right]
                        for left, right in zip(mapped_predecessors, mapped_successors)
                    ),
                    sum(
                        predecessor[left] != successor[right]
                        for left, right in zip(mapped_predecessors, mapped_successors)
                    ),
                    len(added),
                    len(removed),
                ),
            )

    def test_red_predecessor_names_only_the_absent_refinement_command(self) -> None:
        if REFINEMENT_READY:
            self.skipTest("refinement inspection command is implemented")
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-red-") as raw:
            result = _run_refinement(
                STACK_PROPOSAL,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                Path(raw) / "report.json",
            )
        self.assertEqual(2, result.returncode)
        self.assertIn("invalid choice: 'refinement'", result.stderr)
        self.fail("V1 refinement inspection command is absent; successor remains red")


@unittest.skipUnless(REFINEMENT_READY, "refinement inspection command not implemented")
class ExplicitRefinementJourneyTest(unittest.TestCase):
    def _proposal_copy(self, directory: Path, source: Path = STACK_PROPOSAL) -> Path:
        proposal = directory / source.name
        shutil.copyfile(source, proposal)
        return proposal

    def _replace(self, path: Path, old: str, new: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def _assert_failed_without_output_change(
        self,
        proposal: Path,
        predecessor: Path,
        successor: Path,
        expected: tuple[str, ...],
    ) -> str:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-output-") as raw:
            output = Path(raw) / "report.json"
            sentinel = "operator-owned prior report\n"
            output.write_text(sentinel, encoding="utf-8")
            result = _run_refinement(proposal, predecessor, successor, output)
            self.assertEqual(1, result.returncode, result.stderr)
            self.assertEqual("", result.stdout)
            self.assertNotIn("Traceback", result.stderr)
            self.assertTrue(
                all(": " in line for line in result.stderr.splitlines()), result.stderr
            )
            for fragment in expected:
                self.assertIn(fragment, result.stderr)
            self.assertEqual(sentinel, output.read_text(encoding="utf-8"))
            return result.stderr

    def test_exact_stack_and_ordered_map_reports_preserve_distinct_changes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-exact-") as raw:
            directory = Path(raw)
            cases = (
                (
                    STACK_PROPOSAL,
                    STACK_PREDECESSOR,
                    STACK_SUCCESSOR,
                    "stack-0.1.0-to-0.2.0",
                    "stack",
                    (10, 1, 0, 0),
                    [],
                ),
                (
                    ORDERED_PROPOSAL,
                    ORDERED_PREDECESSOR,
                    ORDERED_SUCCESSOR,
                    "ordered-map-0.1.0-to-0.2.0",
                    "ordered-map",
                    (18, 0, 2, 0),
                    [
                        {"family": "observations", "localId": "size"},
                        {"family": "laws", "localId": "size-put"},
                    ],
                ),
            )
            for (
                proposal,
                predecessor,
                successor,
                proposal_id,
                specification_id,
                counts,
                additions,
            ) in cases:
                with self.subTest(proposal=proposal.name):
                    output = directory / f"{proposal.stem}.json"
                    result = _run_refinement(proposal, predecessor, successor, output)
                    self.assertEqual(0, result.returncode, result.stderr)
                    report = _read_json(output)
                    unchanged, changed, added, removed = counts
                    self.assertEqual("refinement-inspection-v1", report["kind"])
                    self.assertEqual(
                        {"id": proposal_id, "version": "0.1.0"}, report["proposal"]
                    )
                    self.assertEqual(
                        {
                            "kind": "specification",
                            "id": specification_id,
                            "version": "0.1.0",
                            "rawSha256": _raw_sha256(predecessor),
                        },
                        report["predecessor"],
                    )
                    self.assertEqual(
                        {
                            "kind": "specification",
                            "id": specification_id,
                            "version": "0.2.0",
                            "rawSha256": _raw_sha256(successor),
                        },
                        report["successor"],
                    )
                    authored = tomllib.loads(proposal.read_text(encoding="utf-8"))
                    self.assertEqual(
                        [item["predecessor"] for item in authored["mappings"]],
                        [item["predecessor"] for item in report["mappings"]],
                    )
                    self.assertEqual(
                        [item["successor"] for item in authored["mappings"]],
                        [item["successor"] for item in report["mappings"]],
                    )
                    relations = [item["documentRelation"] for item in report["mappings"]]
                    self.assertEqual(unchanged, relations.count("document-unchanged"))
                    self.assertEqual(changed, relations.count("document-changed"))
                    self.assertEqual(additions, report["additions"])
                    self.assertEqual(removed, len(report["removals"]))
                    self.assertEqual("unestablished", report["semanticRefinement"])
                    self.assertNotIn("compatible", json.dumps(report).casefold())
                    self.assertNotIn("evidence", json.dumps(report).casefold())
                    self.assertEqual(
                        f"inspected refinement {proposal_id}: {unchanged} unchanged, "
                        f"{changed} changed, {added} additions, {removed} removals; "
                        f"semantic refinement unestablished -> {output}\n",
                        result.stdout,
                    )

    def test_paths_and_version_spelling_have_no_relation_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-authority-") as raw:
            directory = Path(raw)
            proposal = directory / "names-do-not-govern.prefine"
            predecessor = directory / "not-an-old-version.data"
            successor = directory / "not-a-new-version.data"
            shutil.copyfile(STACK_PROPOSAL, proposal)
            shutil.copyfile(STACK_PREDECESSOR, predecessor)
            shutil.copyfile(STACK_SUCCESSOR, successor)
            output = directory / "report.json"
            result = _run_refinement(proposal, predecessor, successor, output)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(10, sum(
                item["documentRelation"] == "document-unchanged"
                for item in _read_json(output)["mappings"]
            ))

            wrong_version = self._proposal_copy(directory)
            self._replace(wrong_version, 'version = "0.2.0"', 'version = "999.0.0"')
            self._assert_failed_without_output_change(
                wrong_version,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                ("REFINEMENT_SPEC_ADDRESS", "#/successor"),
            )

    def test_complete_same_family_swap_governs_instead_of_matching_ids(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-explicit-map-") as raw:
            directory = Path(raw)
            proposal = self._proposal_copy(directory)
            empty_mapping = (
                '[[mappings]]\npredecessor = { family = "operations", localId = "empty" }\n'
                'successor = { family = "operations", localId = "empty" }'
            )
            push_mapping = (
                '[[mappings]]\npredecessor = { family = "operations", localId = "push" }\n'
                'successor = { family = "operations", localId = "push" }'
            )
            swapped = (
                '[[mappings]]\npredecessor = { family = "operations", localId = "empty" }\n'
                'successor = { family = "operations", localId = "push" }'
            )
            swapped_push = (
                '[[mappings]]\npredecessor = { family = "operations", localId = "push" }\n'
                'successor = { family = "operations", localId = "empty" }'
            )
            text = proposal.read_text(encoding="utf-8")
            self.assertIn(empty_mapping, text)
            self.assertIn(push_mapping, text)
            proposal.write_text(
                text.replace(empty_mapping, swapped, 1).replace(
                    push_mapping, swapped_push, 1
                ),
                encoding="utf-8",
            )
            output = directory / "report.json"
            result = _run_refinement(
                proposal, STACK_PREDECESSOR, STACK_SUCCESSOR, output
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report = _read_json(output)
            relations = [item["documentRelation"] for item in report["mappings"]]
            self.assertEqual(8, relations.count("document-unchanged"))
            self.assertEqual(3, relations.count("document-changed"))
            self.assertEqual(
                [
                    {"family": "operations", "localId": "push"},
                    {"family": "operations", "localId": "empty"},
                ],
                [report["mappings"][1]["successor"], report["mappings"][2]["successor"]],
            )

    def test_opaque_reverse_looking_versions_succeed_when_explicit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-opaque-version-") as raw:
            directory = Path(raw)
            predecessor_document = _read_json(STACK_PREDECESSOR)
            successor_document = _read_json(STACK_SUCCESSOR)
            predecessor_document["version"] = "later-looking-999"
            successor_document["version"] = "earlier-looking-001"
            predecessor = directory / "predecessor.json"
            successor = directory / "successor.json"
            predecessor.write_text(
                json.dumps(predecessor_document, ensure_ascii=False, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            successor.write_text(
                json.dumps(successor_document, ensure_ascii=False, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            proposal = self._proposal_copy(directory)
            text = proposal.read_text(encoding="utf-8")
            text = text.replace(
                '[predecessor]\nkind = "specification"\nid = "stack"\nversion = "0.1.0"\n'
                f'rawSha256 = "{_raw_sha256(STACK_PREDECESSOR)}"',
                '[predecessor]\nkind = "specification"\nid = "stack"\n'
                f'version = "later-looking-999"\nrawSha256 = "{_raw_sha256(predecessor)}"',
                1,
            )
            text = text.replace(
                '[successor]\nkind = "specification"\nid = "stack"\nversion = "0.2.0"\n'
                f'rawSha256 = "{_raw_sha256(STACK_SUCCESSOR)}"',
                '[successor]\nkind = "specification"\nid = "stack"\n'
                f'version = "earlier-looking-001"\nrawSha256 = "{_raw_sha256(successor)}"',
                1,
            )
            proposal.write_text(text, encoding="utf-8")
            output = directory / "report.json"
            result = _run_refinement(proposal, predecessor, successor, output)
            self.assertEqual(0, result.returncode, result.stderr)
            report = _read_json(output)
            self.assertEqual("later-looking-999", report["predecessor"]["version"])
            self.assertEqual("earlier-looking-001", report["successor"]["version"])
            self.assertEqual("unestablished", report["semanticRefinement"])

    def test_incomplete_duplicate_dangling_and_wrong_family_dispositions_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-coverage-") as raw:
            directory = Path(raw)
            original = STACK_PROPOSAL.read_text(encoding="utf-8")
            first = (
                '[[mappings]]\npredecessor = { family = "carriers", localId = "Stack" }\n'
                'successor = { family = "carriers", localId = "Stack" }\n\n'
            )
            cases = (
                ("missing.prefine", original.replace(first, "", 1), "REFINEMENT_COVERAGE"),
                ("duplicate.prefine", original + "\n" + first, "REFINEMENT_DUPLICATE"),
                (
                    "dangling.prefine",
                    original.replace('localId = "Stack"', 'localId = "Missing"', 1),
                    "REFINEMENT_REFERENCE",
                ),
                (
                    "family.prefine",
                    original.replace('family = "carriers"', 'family = "laws"', 1),
                    "REFINEMENT_REFERENCE",
                ),
            )
            for name, text, code in cases:
                with self.subTest(name=name):
                    proposal = directory / name
                    proposal.write_text(text, encoding="utf-8")
                    self._assert_failed_without_output_change(
                        proposal,
                        STACK_PREDECESSOR,
                        STACK_SUCCESSOR,
                        (code, str(proposal)),
                    )

    def test_existing_cross_family_swap_and_disposition_overlaps_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-overlap-") as raw:
            directory = Path(raw)
            stack = STACK_PROPOSAL.read_text(encoding="utf-8")
            operation = (
                '[[mappings]]\npredecessor = { family = "operations", localId = "empty" }\n'
                'successor = { family = "operations", localId = "empty" }'
            )
            law = (
                '[[mappings]]\npredecessor = { family = "laws", localId = "pop-empty" }\n'
                'successor = { family = "laws", localId = "pop-empty" }'
            )
            cross_operation = (
                '[[mappings]]\npredecessor = { family = "operations", localId = "empty" }\n'
                'successor = { family = "laws", localId = "pop-empty" }'
            )
            cross_law = (
                '[[mappings]]\npredecessor = { family = "laws", localId = "pop-empty" }\n'
                'successor = { family = "operations", localId = "empty" }'
            )
            cross_family = directory / "cross-family.prefine"
            cross_family.write_text(
                stack.replace(operation, cross_operation, 1).replace(law, cross_law, 1),
                encoding="utf-8",
            )
            self._assert_failed_without_output_change(
                cross_family,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                ("REFINEMENT_FAMILY", str(cross_family)),
            )

            valid_removed = stack.replace(operation + "\n\n", "", 1)
            valid_removed += (
                '\n[[removals]]\npredecessor = { family = "operations", localId = "empty" }\n'
                '\n[[additions]]\nsuccessor = { family = "operations", localId = "empty" }\n'
            )

            cases = (
                (
                    "mapped-and-removed.prefine",
                    stack
                    + '\n[[removals]]\npredecessor = { family = "carriers", localId = "Stack" }\n',
                    "REFINEMENT_OVERLAP",
                ),
                (
                    "mapped-and-added.prefine",
                    stack
                    + '\n[[additions]]\nsuccessor = { family = "carriers", localId = "Stack" }\n',
                    "REFINEMENT_OVERLAP",
                ),
                (
                    "duplicate-addition.prefine",
                    ORDERED_PROPOSAL.read_text(encoding="utf-8")
                    + '\n[[additions]]\nsuccessor = { family = "observations", localId = "size" }\n',
                    "REFINEMENT_DUPLICATE",
                ),
                (
                    "duplicate-removal.prefine",
                    valid_removed
                    + '\n[[removals]]\npredecessor = { family = "operations", localId = "empty" }\n',
                    "REFINEMENT_DUPLICATE",
                ),
            )
            for name, text, code in cases:
                with self.subTest(name=name):
                    proposal = directory / name
                    proposal.write_text(text, encoding="utf-8")
                    predecessor = (
                        ORDERED_PREDECESSOR
                        if name == "duplicate-addition.prefine"
                        else STACK_PREDECESSOR
                    )
                    successor = (
                        ORDERED_SUCCESSOR
                        if name == "duplicate-addition.prefine"
                        else STACK_SUCCESSOR
                    )
                    self._assert_failed_without_output_change(
                        proposal, predecessor, successor, (code, str(proposal))
                    )

    def test_explicit_removal_and_addition_override_matching_id_inference(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-removal-") as raw:
            directory = Path(raw)
            proposal = self._proposal_copy(directory)
            mapping = (
                '[[mappings]]\npredecessor = { family = "operations", localId = "empty" }\n'
                'successor = { family = "operations", localId = "empty" }\n\n'
            )
            text = proposal.read_text(encoding="utf-8")
            self.assertIn(mapping, text)
            proposal.write_text(
                text.replace(mapping, "", 1)
                + '\n[[removals]]\npredecessor = { family = "operations", localId = "empty" }\n'
                + '\n[[additions]]\nsuccessor = { family = "operations", localId = "empty" }\n',
                encoding="utf-8",
            )
            output = directory / "report.json"
            result = _run_refinement(
                proposal, STACK_PREDECESSOR, STACK_SUCCESSOR, output
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report = _read_json(output)
            relations = [item["documentRelation"] for item in report["mappings"]]
            self.assertEqual(9, relations.count("document-unchanged"))
            self.assertEqual(1, relations.count("document-changed"))
            self.assertEqual(
                [{"family": "operations", "localId": "empty"}],
                report["removals"],
            )
            self.assertEqual(
                [{"family": "operations", "localId": "empty"}],
                report["additions"],
            )

    def test_exact_addresses_digests_and_campaign_bytes_are_bound(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-binding-") as raw:
            directory = Path(raw)
            predecessor_drift = directory / "stack-predecessor.json"
            predecessor_drift.write_bytes(STACK_PREDECESSOR.read_bytes() + b"\n")
            self._assert_failed_without_output_change(
                STACK_PROPOSAL,
                predecessor_drift,
                STACK_SUCCESSOR,
                (
                    "REFINEMENT_SPEC_DIGEST",
                    str(predecessor_drift),
                    "#/predecessor/rawSha256",
                ),
            )

            drifted = directory / "stack-successor.json"
            drifted.write_bytes(STACK_SUCCESSOR.read_bytes() + b"\n")
            self._assert_failed_without_output_change(
                STACK_PROPOSAL,
                STACK_PREDECESSOR,
                drifted,
                ("REFINEMENT_SPEC_DIGEST", str(drifted), "#/successor/rawSha256"),
            )

            proposal = self._proposal_copy(directory)
            self._replace(proposal, "070a9c7a", "170a9c7a")
            self._assert_failed_without_output_change(
                proposal,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                ("REFINEMENT_SPEC_DIGEST", "#/successor/rawSha256"),
            )

            predecessor_digest = directory / "predecessor-digest.prefine"
            shutil.copyfile(STACK_PROPOSAL, predecessor_digest)
            self._replace(predecessor_digest, "dd083a71", "ed083a71")
            self._assert_failed_without_output_change(
                predecessor_digest,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                ("REFINEMENT_SPEC_DIGEST", "#/predecessor/rawSha256"),
            )

            address_mutations = (
                (
                    '[predecessor]\nkind = "specification"',
                    '[predecessor]\nkind = "claim"',
                ),
                (
                    '[predecessor]\nkind = "specification"\nid = "stack"',
                    '[predecessor]\nkind = "specification"\nid = "other"',
                ),
                (
                    '[predecessor]\nkind = "specification"\nid = "stack"\nversion = "0.1.0"',
                    '[predecessor]\nkind = "specification"\nid = "stack"\nversion = "opaque"',
                ),
            )
            for index, (old, new) in enumerate(address_mutations):
                with self.subTest(address=index):
                    mutated = directory / f"predecessor-address-{index}.prefine"
                    shutil.copyfile(STACK_PROPOSAL, mutated)
                    self._replace(mutated, old, new)
                    self._assert_failed_without_output_change(
                        mutated,
                        STACK_PREDECESSOR,
                        STACK_SUCCESSOR,
                        ("REFINEMENT_SPEC_ADDRESS", "#/predecessor"),
                    )

    def test_raw_parse_schema_and_numeric_limits_are_contained_by_phase(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-raw-") as raw:
            directory = Path(raw)
            invalid_utf8 = directory / "invalid.prefine"
            invalid_utf8.write_bytes(b"\xff")
            stderr = self._assert_failed_without_output_change(
                invalid_utf8,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                ("REFINEMENT_PROPOSAL_UTF8", str(invalid_utf8)),
            )
            self.assertNotIn("REFINEMENT_SPEC_", stderr)
            self.assertNotIn("REFINEMENT_COVERAGE", stderr)

            huge = directory / "huge.prefine"
            huge.write_text(f"huge = {'9' * 5000}\n", encoding="utf-8")
            stderr = self._assert_failed_without_output_change(
                huge,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                ("REFINEMENT_PROPOSAL_TOML", "numeric conversion exceeds parser limit"),
            )
            self.assertNotIn("REFINEMENT_SPEC_", stderr)
            self.assertNotIn("REFINEMENT_COVERAGE", stderr)

            duplicate_toml = directory / "duplicate.prefine"
            duplicate_toml.write_text('kind = "x"\nkind = "y"\n', encoding="utf-8")
            stderr = self._assert_failed_without_output_change(
                duplicate_toml,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                ("REFINEMENT_PROPOSAL_TOML", "duplicate TOML key"),
            )
            self.assertNotIn("REFINEMENT_SPEC_", stderr)
            self.assertNotIn("REFINEMENT_COVERAGE", stderr)

            invalid_spec_utf8 = directory / "invalid-spec.json"
            invalid_spec_utf8.write_bytes(b"\xff")
            stderr = self._assert_failed_without_output_change(
                STACK_PROPOSAL,
                invalid_spec_utf8,
                STACK_SUCCESSOR,
                ("REFINEMENT_SPEC_UTF8", str(invalid_spec_utf8)),
            )
            self.assertNotIn("SCHEMA_", stderr)
            self.assertNotIn("REFINEMENT_SPEC_DIGEST", stderr)
            self.assertNotIn("REFINEMENT_COVERAGE", stderr)

            huge_json = directory / "huge.json"
            huge_json.write_text(
                '{"kind":"specification","id":"stack","version":'
                + "9" * 5000
                + ',"laws":[{"id":"x","statement":"x"}]}',
                encoding="utf-8",
            )
            stderr = self._assert_failed_without_output_change(
                STACK_PROPOSAL,
                huge_json,
                STACK_SUCCESSOR,
                ("REFINEMENT_SPEC_JSON", "numeric conversion exceeds parser limit"),
            )
            self.assertNotIn("SCHEMA_", stderr)
            self.assertNotIn("REFINEMENT_SPEC_DIGEST", stderr)
            self.assertNotIn("REFINEMENT_COVERAGE", stderr)

            duplicate_json = directory / "duplicate.json"
            duplicate_json.write_text(
                '{"kind":"specification","kind":"specification","id":"stack","version":"0.1.0","laws":[{"id":"x","statement":"x"}]}',
                encoding="utf-8",
            )
            stderr = self._assert_failed_without_output_change(
                STACK_PROPOSAL,
                duplicate_json,
                STACK_SUCCESSOR,
                ("REFINEMENT_SPEC_JSON", "duplicate object member kind"),
            )
            self.assertNotIn("SCHEMA_", stderr)
            self.assertNotIn("REFINEMENT_SPEC_DIGEST", stderr)
            self.assertNotIn("REFINEMENT_COVERAGE", stderr)

            invalid_schema = directory / "invalid-schema.json"
            invalid_schema.write_text(
                '{"kind":"specification","id":"stack","version":"0.1.0"}',
                encoding="utf-8",
            )
            stderr = self._assert_failed_without_output_change(
                STACK_PROPOSAL,
                invalid_schema,
                STACK_SUCCESSOR,
                ("SCHEMA_", str(invalid_schema)),
            )
            self.assertNotIn("REFINEMENT_SPEC_ADDRESS", stderr)
            self.assertNotIn("REFINEMENT_SPEC_DIGEST", stderr)
            self.assertNotIn("REFINEMENT_COVERAGE", stderr)

    def test_reordering_documents_does_not_reorder_or_create_mappings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-order-") as raw:
            directory = Path(raw)
            baseline_output = directory / "baseline.json"
            baseline_result = _run_refinement(
                STACK_PROPOSAL,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                baseline_output,
            )
            self.assertEqual(0, baseline_result.returncode, baseline_result.stderr)
            baseline = _read_json(baseline_output)
            predecessor_document = _read_json(STACK_PREDECESSOR)
            predecessor_document["laws"].reverse()
            predecessor = directory / "reordered.json"
            predecessor.write_text(
                json.dumps(predecessor_document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            proposal = self._proposal_copy(directory)
            self._replace(
                proposal,
                _raw_sha256(STACK_PREDECESSOR),
                _raw_sha256(predecessor),
            )
            output = directory / "report.json"
            result = _run_refinement(proposal, predecessor, STACK_SUCCESSOR, output)
            self.assertEqual(0, result.returncode, result.stderr)
            report = _read_json(output)
            self.assertEqual(baseline["mappings"], report["mappings"])
            self.assertEqual(baseline["additions"], report["additions"])
            self.assertEqual(baseline["removals"], report["removals"])
            self.assertEqual(
                baseline["semanticRefinement"], report["semanticRefinement"]
            )

    def test_hosted_changes_are_structural_not_semantic_verdicts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-hosted-") as raw:
            directory = Path(raw)
            successor_document = _read_json(ORDERED_SUCCESSOR)
            successor_document["laws"][0]["statement"] = "opaque changed tokens"
            successor = directory / "hosted.json"
            successor.write_text(
                json.dumps(successor_document, ensure_ascii=False, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            proposal = self._proposal_copy(directory, ORDERED_PROPOSAL)
            self._replace(
                proposal,
                _raw_sha256(ORDERED_SUCCESSOR),
                _raw_sha256(successor),
            )
            output = directory / "report.json"
            result = _run_refinement(proposal, ORDERED_PREDECESSOR, successor, output)
            self.assertEqual(0, result.returncode, result.stderr)
            report = _read_json(output)
            changed = [
                item for item in report["mappings"]
                if item["documentRelation"] == "document-changed"
            ]
            self.assertEqual(
                [{"family": "laws", "localId": "lookup-empty"}],
                [item["successor"] for item in changed],
            )
            self.assertEqual("unestablished", report["semanticRefinement"])

    def test_required_paths_no_discovery_and_output_failures_are_contained(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "semantic_packages", "refinement", "inspect", str(STACK_PROPOSAL)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("--predecessor", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

        with tempfile.TemporaryDirectory(prefix="semantic-refinement-no-discovery-") as raw:
            directory = Path(raw)
            proposal = self._proposal_copy(directory)
            shutil.copyfile(STACK_PREDECESSOR, directory / "nearby-predecessor.json")
            shutil.copyfile(STACK_SUCCESSOR, directory / "nearby-successor.json")
            missing = directory / "missing.json"
            self._assert_failed_without_output_change(
                proposal,
                missing,
                STACK_SUCCESSOR,
                ("REFINEMENT_SPEC_READ", str(missing)),
            )
            result = _run_refinement(
                proposal, STACK_PREDECESSOR, STACK_SUCCESSOR, directory
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("REFINEMENT_OUTPUT_WRITE", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_report_contains_no_resolution_or_evidence_migration_surface(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-boundary-") as raw:
            before = _tree_snapshot(ROOT / "registry")
            output = Path(raw) / "report.json"
            result = _run_refinement(
                ORDERED_PROPOSAL, ORDERED_PREDECESSOR, ORDERED_SUCCESSOR, output
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(before, _tree_snapshot(ROOT / "registry"))
            report = _read_json(output)
            self.assertEqual(
                {
                    "kind",
                    "proposal",
                    "predecessor",
                    "successor",
                    "mappings",
                    "additions",
                    "removals",
                    "semanticRefinement",
                },
                set(report),
            )
            serialized = json.dumps(report).casefold()
            for forbidden in (
                "claim",
                "evidence",
                "realization",
                "selected",
                "latest",
                "compatible",
                "migration",
            ):
                self.assertNotIn(forbidden, serialized)

    def test_in_process_inspection_never_calls_resolver_or_process_boundary(self) -> None:
        from semantic_packages import refinement_command, resolver

        with tempfile.TemporaryDirectory(prefix="semantic-refinement-pure-") as raw:
            output = Path(raw) / "report.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            arguments = [
                "refinement",
                "inspect",
                str(STACK_PROPOSAL),
                "--predecessor",
                str(STACK_PREDECESSOR),
                "--successor",
                str(STACK_SUCCESSOR),
                "--output",
                str(output),
            ]
            forbidden = AssertionError("refinement inspection crossed a forbidden boundary")
            with (
                mock.patch.object(resolver, "resolve_exact", side_effect=forbidden),
                mock.patch.object(
                    refinement_command,
                    "resolve_exact",
                    create=True,
                    side_effect=forbidden,
                ),
                mock.patch("subprocess.Popen", side_effect=forbidden),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                status = refinement_command.main(arguments)
            self.assertEqual(0, status, stderr.getvalue())
            self.assertEqual("", stderr.getvalue())
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
