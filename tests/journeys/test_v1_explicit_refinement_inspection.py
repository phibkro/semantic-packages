"""Contract tests for design-spec 0002's explicit refinement inspection."""

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
                    (10, 1, 0, 0),
                    [],
                ),
                (
                    ORDERED_PROPOSAL,
                    ORDERED_PREDECESSOR,
                    ORDERED_SUCCESSOR,
                    "ordered-map-0.1.0-to-0.2.0",
                    (18, 0, 2, 0),
                    [
                        {"family": "observations", "localId": "size"},
                        {"family": "laws", "localId": "size-put"},
                    ],
                ),
            )
            for proposal, predecessor, successor, proposal_id, counts, additions in cases:
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

    def test_exact_addresses_digests_and_campaign_bytes_are_bound(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-binding-") as raw:
            directory = Path(raw)
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

    def test_raw_parse_schema_and_numeric_limits_are_contained_by_phase(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-raw-") as raw:
            directory = Path(raw)
            invalid_utf8 = directory / "invalid.prefine"
            invalid_utf8.write_bytes(b"\xff")
            self._assert_failed_without_output_change(
                invalid_utf8,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                ("REFINEMENT_PROPOSAL_UTF8", str(invalid_utf8)),
            )

            huge = directory / "huge.prefine"
            huge.write_text(f"huge = {'9' * 5000}\n", encoding="utf-8")
            self._assert_failed_without_output_change(
                huge,
                STACK_PREDECESSOR,
                STACK_SUCCESSOR,
                ("REFINEMENT_PROPOSAL_TOML", "numeric conversion exceeds parser limit"),
            )

            duplicate_json = directory / "duplicate.json"
            duplicate_json.write_text(
                '{"kind":"specification","kind":"specification","id":"stack","version":"0.1.0","laws":[{"id":"x","statement":"x"}]}',
                encoding="utf-8",
            )
            self._assert_failed_without_output_change(
                STACK_PROPOSAL,
                duplicate_json,
                STACK_SUCCESSOR,
                ("REFINEMENT_SPEC_JSON", "duplicate object member kind"),
            )

            invalid_schema = directory / "invalid-schema.json"
            invalid_schema.write_text(
                '{"kind":"specification","id":"stack","version":"0.1.0"}',
                encoding="utf-8",
            )
            self._assert_failed_without_output_change(
                STACK_PROPOSAL,
                invalid_schema,
                STACK_SUCCESSOR,
                ("SCHEMA_", str(invalid_schema)),
            )

    def test_reordering_documents_does_not_reorder_or_create_mappings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-refinement-order-") as raw:
            directory = Path(raw)
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
            authored = tomllib.loads(proposal.read_text(encoding="utf-8"))["mappings"]
            self.assertEqual(
                [item["predecessor"] for item in authored],
                [item["predecessor"] for item in report["mappings"]],
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
            output = Path(raw) / "report.json"
            result = _run_refinement(
                ORDERED_PROPOSAL, ORDERED_PREDECESSOR, ORDERED_SUCCESSOR, output
            )
            self.assertEqual(0, result.returncode, result.stderr)
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


if __name__ == "__main__":
    unittest.main()
