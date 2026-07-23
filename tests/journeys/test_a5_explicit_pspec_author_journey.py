"""Contract tests for design-spec 0001's complete human author journey."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DESIGN_SPEC = ROOT / "design-specs/0001-explicit-pspec-author-journey.md"
STACK_SOURCE = ROOT / "specs/stack.pspec"
STACK_RECORD = ROOT / "registry/stack/theory/records/stack-spec.json"
STACK_PROFILE = ROOT / "registry/stack/theory/dependencies/stack-profile.json"
ORDERED_SOURCE = ROOT / "specs/ordered-map.pspec"
ORDERED_RECORD = ROOT / "registry/ordered-map/theory/records/ordered-map-spec.json"
ORDERED_PROFILE = (
    ROOT / "registry/ordered-map/theory/dependencies/ordered-map-profile.json"
)
HUMAN_OBSERVATION = ROOT / "reports/authoring/uninvolved-author-observation.json"
HUMAN_OBSERVATION_PROTOCOL = (
    ROOT / "docs/operations/explicit-pspec-author-observation.md"
)
HUMAN_OBSERVATION_AUTHORITY = (
    ROOT / "docs/operations/explicit-pspec-author-observation-authority.json"
)
ASSISTANCE_CATEGORIES = {
    "orientation",
    "command-clarification",
    "terminology",
    "environment",
    "recovery",
    "other",
}
CLI_READY = importlib.util.find_spec("semantic_packages.__main__") is not None


def _run_author(
    source: Path,
    output: Path,
    dependencies: tuple[Path, ...] = (),
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "-m",
        "semantic_packages",
        "author",
        str(source),
    ]
    for dependency in dependencies:
        command.extend(("--dependency", str(dependency)))
    command.extend(("--output", str(output)))
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _observation_problems(authority_revision: str, observation: Any) -> set[str]:
    problems: set[str] = set()
    if type(observation) is not dict:
        return {"observation-type"}
    if set(observation) != {
        "kind",
        "revision",
        "participant",
        "tasks",
        "blockingAmbiguities",
    }:
        problems.add("observation-keys")
    if observation.get("kind") != "human-author-observation-v1":
        problems.add("kind")
    if observation.get("revision") != authority_revision:
        problems.add("revision")

    participant = observation.get("participant")
    if type(participant) is not dict:
        problems.add("participant-type")
    else:
        if set(participant) != {
            "eligible",
            "priorProjectInvolvement",
            "reviewedObservation",
        }:
            problems.add("participant-keys")
        if participant.get("eligible") is not True:
            problems.add("participant-eligibility")
        if participant.get("priorProjectInvolvement") != "none":
            problems.add("participant-involvement")
        if participant.get("reviewedObservation") is not True:
            problems.add("participant-review")

    tasks = observation.get("tasks")
    if type(tasks) is not list:
        problems.add("tasks-type")
    else:
        if len(tasks) != 2:
            problems.add("tasks-length")
        for index, expected_domain in enumerate(("stack", "ordered-map")):
            if index >= len(tasks) or type(tasks[index]) is not dict:
                problems.add(f"task-{index}-type")
                continue
            task = tasks[index]
            if set(task) != {"domain", "result", "durationSeconds", "assistance"}:
                problems.add(f"task-{index}-keys")
            if task.get("domain") != expected_domain:
                problems.add(f"task-{index}-domain")
            if task.get("result") != "pass":
                problems.add(f"task-{index}-result")
            duration = task.get("durationSeconds")
            if type(duration) is not int or duration <= 0:
                problems.add(f"task-{index}-duration")
            assistance = task.get("assistance")
            if type(assistance) is not list:
                problems.add(f"task-{index}-assistance-type")
            else:
                if any(
                    type(item) is not str or item not in ASSISTANCE_CATEGORIES
                    for item in assistance
                ):
                    problems.add(f"task-{index}-assistance-item")
                if all(type(item) is str for item in assistance) and len(
                    assistance
                ) != len(set(assistance)):
                    problems.add(f"task-{index}-assistance-duplicate")

    ambiguities = observation.get("blockingAmbiguities")
    if type(ambiguities) is not list:
        problems.add("ambiguities-type")
    else:
        if any(type(item) is not str or not item.strip() for item in ambiguities):
            problems.add("ambiguity-item")
        if all(type(item) is str for item in ambiguities) and len(ambiguities) != len(
            set(ambiguities)
        ):
            problems.add("ambiguity-duplicate")
        if ambiguities:
            problems.add("blocking-ambiguity")
    return problems


class ExplicitPSpecRedBaselineTest(unittest.TestCase):
    def test_design_spec_and_two_explicit_inputs_exist(self) -> None:
        self.assertTrue(DESIGN_SPEC.is_file())
        self.assertTrue(STACK_SOURCE.is_file())
        self.assertTrue(ORDERED_SOURCE.is_file())
        for source in (STACK_SOURCE, ORDERED_SOURCE):
            text = source.read_text(encoding="utf-8")
            self.assertIn('kind = "specification"', text)
            self.assertIn('version = "0.1.0"', text)
            self.assertNotIn("TODO", text)

    def test_red_predecessor_names_only_the_absent_command(self) -> None:
        if CLI_READY:
            self.skipTest("A5 author command is implemented")
        with tempfile.TemporaryDirectory(prefix="semantic-pspec-red-") as raw:
            result = _run_author(STACK_SOURCE, Path(raw) / "stack.json", (STACK_PROFILE,))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("No module named semantic_packages.__main__", result.stderr)
        self.fail("A5 author command is absent; successor journey remains red")


@unittest.skipUnless(CLI_READY, "A5 author command not implemented")
class ExplicitPSpecAuthorJourneyTest(unittest.TestCase):
    def _mutated_stack(self, directory: Path, old: str, new: str) -> Path:
        source = directory / "mutated.pspec"
        original = STACK_SOURCE.read_text(encoding="utf-8")
        self.assertIn(old, original)
        source.write_text(original.replace(old, new, 1), encoding="utf-8")
        return source

    def _assert_failed_without_output_change(
        self,
        source: Path,
        expected: tuple[str, ...],
        dependencies: tuple[Path, ...] = (STACK_PROFILE,),
    ) -> str:
        with tempfile.TemporaryDirectory(prefix="semantic-pspec-sentinel-") as raw:
            output = Path(raw) / "out.json"
            sentinel = "operator-owned prior output\n"
            output.write_text(sentinel, encoding="utf-8")
            result = _run_author(source, output, dependencies)
            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertNotIn("Traceback", result.stderr)
            self.assertTrue(
                all(": " in line for line in result.stderr.splitlines()),
                result.stderr,
            )
            for fragment in expected:
                self.assertIn(fragment, result.stderr)
            self.assertEqual(sentinel, output.read_text(encoding="utf-8"))
            return result.stderr

    def test_complete_stack_and_ordered_map_examples_author_exact_records(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-pspec-exact-") as raw:
            directory = Path(raw)
            for source, dependency, accepted in (
                (STACK_SOURCE, STACK_PROFILE, STACK_RECORD),
                (ORDERED_SOURCE, ORDERED_PROFILE, ORDERED_RECORD),
            ):
                with self.subTest(source=source.name):
                    output = directory / f"{source.stem}.json"
                    result = _run_author(source, output, (dependency,))
                    expected = _read_json(accepted)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual("", result.stderr)
                    self.assertEqual(
                        f"authored specification {expected['id']}@{expected['version']} -> {output}\n",
                        result.stdout,
                    )
                    self.assertEqual(expected, _read_json(output))
                    rendered = output.read_text(encoding="utf-8")
                    self.assertTrue(rendered.endswith("\n"))
                    self.assertIn('\n  "kind": "specification"', rendered)

    def test_source_and_dependency_paths_are_provenance_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-pspec-label-") as raw:
            directory = Path(raw)
            renamed_source = directory / "meaning-does-not-come-from-this-name.txt"
            renamed_dependency = directory / "nor-this-name.data"
            shutil.copyfile(STACK_SOURCE, renamed_source)
            shutil.copyfile(STACK_PROFILE, renamed_dependency)
            output = directory / "renamed.json"
            result = _run_author(renamed_source, output, (renamed_dependency,))
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(_read_json(STACK_RECORD), _read_json(output))

    def test_dependency_context_is_explicit_finite_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-pspec-context-") as raw:
            directory = Path(raw)
            source = directory / "stack.pspec"
            nearby = directory / "stack-profile.json"
            shutil.copyfile(STACK_SOURCE, source)
            shutil.copyfile(STACK_PROFILE, nearby)

            first = self._assert_failed_without_output_change(
                source,
                (
                    "LINK_DANGLING_REFERENCE",
                    "#/performancePropositions/0/costMeasure/profile",
                    "#/performancePropositions/0/workload/profile",
                ),
                (),
            )
            second = self._assert_failed_without_output_change(
                source,
                ("LINK_DANGLING_REFERENCE",),
                (),
            )
            self.assertEqual(first, second)

            wrong = self._assert_failed_without_output_change(
                source,
                ("LINK_DANGLING_REFERENCE",),
                (ORDERED_PROFILE,),
            )
            self.assertNotIn(str(nearby), wrong)

            duplicate = self._assert_failed_without_output_change(
                source,
                ("LINK_DUPLICATE_ADDRESS", str(STACK_PROFILE)),
                (STACK_PROFILE, STACK_PROFILE),
            )
            self.assertEqual(1, duplicate.count("LINK_DUPLICATE_ADDRESS"))

            corrupt = directory / "corrupt.json"
            corrupt.write_text('{"kind":', encoding="utf-8")
            self._assert_failed_without_output_change(
                source,
                ("AUTHOR_DEPENDENCY_JSON", str(corrupt), "invalid JSON"),
                (corrupt,),
            )

    def test_raw_schema_and_link_failures_are_actionable_and_atomic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-pspec-errors-") as raw:
            directory = Path(raw)
            cases = (
                (
                    'id = "stack"\n',
                    "",
                    ("SCHEMA_MISSING_FIELD", "#/id"),
                ),
                (
                    'id = "stack"\n',
                    'id = "stack"\nid = "shadow"\n',
                    ("AUTHOR_INVALID_TOML", "duplicate"),
                ),
                (
                    '[[operations]]\nid = "empty"\n',
                    "[[operations]]\n",
                    ("SCHEMA_MISSING_FIELD", "#/operations/0/id"),
                ),
                (
                    'id = "push"',
                    'id = "empty"',
                    (
                        "LINK_DUPLICATE_DECLARATION_ID",
                        "#/operations/1/id",
                        "LINK_DANGLING_DECLARATION",
                        "#/performancePropositions/0/operationFamily/0",
                    ),
                ),
                (
                    'carrier = "Stack"',
                    'carrier = "MissingCarrier"',
                    ("LINK_DANGLING_DECLARATION", "#/equivalences/0/carrier"),
                ),
                (
                    'carrier = "Stack"',
                    'carrier = "empty"',
                    ("LINK_DECLARATION_KIND_MISMATCH", "#/equivalences/0/carrier"),
                ),
                (
                    'statement = "pop(empty) == None"',
                    'statement = ""',
                    ("SCHEMA_NONEMPTY_STRING", "#/laws/0/statement"),
                ),
            )
            for index, (old, new, expected) in enumerate(cases):
                with self.subTest(case=index):
                    source = self._mutated_stack(directory, old, new)
                    self._assert_failed_without_output_change(source, expected)

            invalid_toml = directory / "invalid.pspec"
            invalid_toml.write_text('kind = "specification"\nid = ', encoding="utf-8")
            self._assert_failed_without_output_change(
                invalid_toml,
                ("AUTHOR_INVALID_TOML", "line 2", "column"),
                (),
            )

            invalid_utf8 = directory / "invalid-utf8.pspec"
            invalid_utf8.write_bytes(b'kind = "specification"\n\xff')
            self._assert_failed_without_output_change(
                invalid_utf8,
                ("AUTHOR_INVALID_UTF8", "byte 23"),
                (),
            )

    def test_non_json_toml_values_fail_before_record_validation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-pspec-non-json-") as raw:
            directory = Path(raw)
            source = self._mutated_stack(
                directory,
                'version = "0.1.0"',
                'version = "0.1.0"\ncreated = 1979-05-27T07:32:00Z',
            )
            stderr = self._assert_failed_without_output_change(
                source,
                ("AUTHOR_TOML_NON_JSON", "#/created", "JSON data model"),
                (),
            )
            self.assertNotIn("SCHEMA_", stderr)

    def test_parser_numeric_conversion_limits_are_contained(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-pspec-numeric-limit-") as raw:
            directory = Path(raw)
            huge_integer = "9" * 5000
            source = self._mutated_stack(
                directory,
                'version = "0.1.0"',
                f'version = "0.1.0"\nhuge = {huge_integer}',
            )
            self._assert_failed_without_output_change(
                source,
                ("AUTHOR_INVALID_TOML", "numeric conversion exceeds parser limit"),
                (),
            )

            dependency = directory / "huge.json"
            dependency.write_text(f'{{"huge":{huge_integer}}}', encoding="utf-8")
            self._assert_failed_without_output_change(
                STACK_SOURCE,
                (
                    "AUTHOR_DEPENDENCY_JSON",
                    str(dependency),
                    "numeric conversion exceeds parser limit",
                ),
                (dependency,),
            )

    def test_declaration_order_and_hosted_text_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-pspec-opaque-") as raw:
            directory = Path(raw)
            original = STACK_SOURCE.read_text(encoding="utf-8")
            first = (
                '[[laws]]\nid = "pop-empty"\nstatement = "pop(empty) == None"\n'
            )
            second = (
                '[[laws]]\nid = "pop-push"\n'
                'statement = "pop(push(s, x)) == Some((x, s)) under Stack observational equivalence"\n'
            )
            self.assertIn(first + "\n" + second, original)
            reordered = directory / "reordered.pspec"
            reordered.write_text(
                original.replace(first + "\n" + second, second + "\n" + first, 1),
                encoding="utf-8",
            )
            output = directory / "reordered.json"
            result = _run_author(reordered, output, (STACK_PROFILE,))
            self.assertEqual(0, result.returncode, result.stderr)
            document = _read_json(output)
            self.assertEqual(["pop-push", "pop-empty"], [law["id"] for law in document["laws"]])

            hosted = directory / "hosted.pspec"
            opaque = "forall x:\n  hosted tokens remain opaque {{not interpreted}}\n"
            hosted.write_text(
                original.replace(
                    'statement = "pop(empty) == None"',
                    'statement = """\n' + opaque + '"""',
                    1,
                ),
                encoding="utf-8",
            )
            hosted_output = directory / "hosted.json"
            hosted_result = _run_author(hosted, hosted_output, (STACK_PROFILE,))
            self.assertEqual(0, hosted_result.returncode, hosted_result.stderr)
            self.assertEqual(opaque, _read_json(hosted_output)["laws"][0]["statement"])

    def test_required_arguments_and_output_write_failures_are_contained(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "semantic_packages", "author", str(STACK_SOURCE)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("--output", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

        with tempfile.TemporaryDirectory(prefix="semantic-pspec-output-") as raw:
            directory = Path(raw)
            result = _run_author(STACK_SOURCE, directory, (STACK_PROFILE,))
            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertIn("AUTHOR_OUTPUT_WRITE", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_uninvolved_author_protocol_and_any_observation_are_truthful(self) -> None:
        protocol = HUMAN_OBSERVATION_PROTOCOL.read_text(encoding="utf-8")
        self.assertIn("## Task 1 — Stack success, failure, and recovery", protocol)
        self.assertIn("## Task 2 — OrderedMap through the same contract", protocol)
        self.assertIn("The implementing agent must not impersonate", protocol)
        authority = _read_json(HUMAN_OBSERVATION_AUTHORITY)
        self.assertEqual(
            {"kind", "revision", "protocol", "domains"}, set(authority)
        )
        self.assertEqual(
            "human-author-observation-authority-v1", authority["kind"]
        )
        self.assertRegex(authority["revision"], r"^[0-9a-f]{40}$")
        self.assertNotEqual("0" * 40, authority["revision"])
        self.assertEqual(
            "docs/operations/explicit-pspec-author-observation.md",
            authority["protocol"],
        )
        self.assertEqual(["stack", "ordered-map"], authority["domains"])
        if not HUMAN_OBSERVATION.is_file():
            return

        observation = _read_json(HUMAN_OBSERVATION)
        self.assertEqual(set(), _observation_problems(authority["revision"], observation))

    def test_observation_validation_rejects_permissive_counterexample(self) -> None:
        authority = _read_json(HUMAN_OBSERVATION_AUTHORITY)
        valid = {
            "kind": "human-author-observation-v1",
            "revision": authority["revision"],
            "participant": {
                "eligible": True,
                "priorProjectInvolvement": "none",
                "reviewedObservation": True,
            },
            "tasks": [
                {
                    "domain": "stack",
                    "result": "pass",
                    "durationSeconds": 1,
                    "assistance": [],
                },
                {
                    "domain": "ordered-map",
                    "result": "pass",
                    "durationSeconds": 1,
                    "assistance": ["orientation"],
                },
            ],
            "blockingAmbiguities": [],
        }
        self.assertEqual(set(), _observation_problems(authority["revision"], valid))

        counterexample = {
            "kind": "human-author-observation-v1",
            "revision": "0" * 40,
            "participant": {
                "eligible": True,
                "priorProjectInvolvement": "none",
                "reviewedObservation": True,
                "extra": "ungoverned",
            },
            "tasks": [
                {
                    "domain": "stack",
                    "result": "pass",
                    "durationSeconds": True,
                    "assistance": [{"answer": "arbitrary"}],
                },
                {
                    "domain": "ordered-map",
                    "result": "fail",
                    "durationSeconds": 1,
                    "assistance": ["unknown-category"],
                },
            ],
            "blockingAmbiguities": ["", {"extra": "channel"}],
            "extra": "ungoverned",
        }
        problems = _observation_problems(authority["revision"], counterexample)
        self.assertTrue(
            {
                "observation-keys",
                "revision",
                "participant-keys",
                "task-0-duration",
                "task-0-assistance-item",
                "task-1-result",
                "task-1-assistance-item",
                "ambiguity-item",
                "blocking-ambiguity",
            }
            <= problems
        )


if __name__ == "__main__":
    unittest.main()
