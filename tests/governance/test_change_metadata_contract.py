from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "check_change_metadata.py"
FIXTURES = ROOT / "fixtures" / "governance"
CHECKER_EXISTS = CHECKER.is_file()
ALLOWED_TYPES = {
    "feat",
    "fix",
    "refactor",
    "perf",
    "docs",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
    "style",
}
VALID_PR_EVENTS = (
    "pull-requests/valid-event.json",
    "pull-requests/valid-breaking-event.json",
    "pull-requests/valid-72-event.json",
)


def _read_json(relative: str) -> object:
    return json.loads((FIXTURES / relative).read_text(encoding="utf-8"))


def _load_checker():
    spec = importlib.util.spec_from_file_location("change_metadata_contract_target", CHECKER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load governance checker from {CHECKER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_body() -> str:
    return _read_json("pull-requests/valid-event.json")["pull_request"]["body"]


def _replace_heading_content(body: str, heading: str, replacement: str) -> str:
    marker = f"{heading}\n"
    start = body.index(marker) + len(marker)
    boundary_tokens = ("\n## ",) if heading.startswith("## ") else ("\n## ", "\n### ")
    candidates = [
        position
        for token in boundary_tokens
        if (position := body.find(token, start)) >= 0
    ]
    end = min(candidates) if candidates else len(body)
    return body[:start] + replacement + body[end:]


def _event_with_body(body: str, title: str = "ci(governance): enforce change metadata contracts") -> dict[str, object]:
    return {"pull_request": {"title": title, "body": body}}


class RedCheckpoint(unittest.TestCase):
    def test_checker_is_absent_at_the_deliberate_red_checkpoint(self) -> None:
        self.assertTrue(
            CHECKER_EXISTS,
            "red checkpoint: scripts/check_change_metadata.py does not exist",
        )


@unittest.skipUnless(CHECKER_EXISTS, "blocked only by the missing governance checker")
class PublicApiContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checker = _load_checker()

    def test_valid_commit_subjects(self) -> None:
        cases = _read_json("commits/valid.json")
        self.assertEqual(
            {case["subject"].split("(", 1)[0].split(":", 1)[0] for case in cases},
            ALLOWED_TYPES,
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                self.assertEqual(
                    self.checker.validate_commit_subject(
                        case["subject"], parent_count=case["parentCount"]
                    ),
                    [],
                )

    def test_invalid_commit_subjects_have_stable_diagnostics(self) -> None:
        for case in _read_json("commits/invalid.json"):
            with self.subTest(case=case["name"]):
                self.assertEqual(
                    self.checker.validate_commit_subject(
                        case["subject"], parent_count=case["parentCount"]
                    ),
                    case["expected"],
                )

    def test_valid_pull_request_event(self) -> None:
        for fixture in VALID_PR_EVENTS:
            with self.subTest(fixture=fixture):
                self.assertEqual(
                    self.checker.validate_pull_request_event(_read_json(fixture)),
                    [],
                )
        titles = _read_json("pull-requests/valid-titles.json")
        self.assertEqual(
            {title.split("(", 1)[0].split(":", 1)[0] for title in titles},
            ALLOWED_TYPES,
        )
        for title in titles:
            with self.subTest(title=title):
                self.assertEqual(
                    self.checker.validate_pull_request_event(
                        _event_with_body(_valid_body(), title=title)
                    ),
                    [],
                )

    def test_invalid_pull_request_events_have_stable_diagnostics(self) -> None:
        for case in _read_json("pull-requests/invalid-events.json"):
            with self.subTest(case=case["name"]):
                self.assertEqual(
                    self.checker.validate_pull_request_event(case["event"]),
                    case["expected"],
                )

    def test_malformed_pull_request_envelopes_have_stable_diagnostics(self) -> None:
        for case in _read_json("pull-requests/malformed-events.json"):
            with self.subTest(case=case["name"]):
                self.assertEqual(
                    self.checker.validate_pull_request_event(case["event"]),
                    case["expected"],
                )

    def test_every_required_section_rejects_noncontent_and_duplicates(self) -> None:
        controls = _read_json("pull-requests/markdown-controls.json")
        body = _valid_body()
        for heading in controls["requiredSections"]:
            for replacement in controls["nonSubstantiveContent"]:
                with self.subTest(heading=heading, replacement=replacement):
                    mutated = _replace_heading_content(body, heading, replacement)
                    self.assertEqual(
                        self.checker.validate_pull_request_event(_event_with_body(mutated)),
                        [f"pull request section '{heading}' must contain substantive content"],
                    )
            with self.subTest(heading=heading, mutation="duplicate"):
                mutated = f"{body}\n\n{heading}\nA later duplicate must not be accepted."
                self.assertEqual(
                    self.checker.validate_pull_request_event(_event_with_body(mutated)),
                    [f"pull request body repeats required section '{heading}'"],
                )

    def test_markdown_headings_must_be_real_and_ordered(self) -> None:
        controls = _read_json("pull-requests/markdown-controls.json")
        body = _valid_body()
        for control in controls["hiddenHeadingControls"]:
            with self.subTest(control=control["name"]):
                mutated = body.replace("## Governing scope", control["replacement"], 1)
                self.assertEqual(
                    self.checker.validate_pull_request_event(_event_with_body(mutated)),
                    ["pull request body missing required section '## Governing scope'"],
                )

        risks = "## Risks, assumptions, and exclusions\nHosted rules and application installation remain operator-owned."
        recovery = "## Recovery, maintenance, and reopen triggers\nRevert the governance commit if valid low-risk work is rejected."
        reordered = body.replace(f"{risks}\n\n{recovery}", f"{recovery}\n\n{risks}")
        self.assertEqual(
            self.checker.validate_pull_request_event(_event_with_body(reordered)),
            ["pull request body sections must appear in the documented order"],
        )

        comment_prefixed = body.replace(
            "## Outcome", "<!-- -->## Outcome", 1
        )
        self.assertEqual(
            self.checker.validate_pull_request_event(
                _event_with_body(comment_prefixed)
            ),
            ["pull request body missing required section '## Outcome'"],
        )

        invalid_fence_duplicate = (
            f"{body}\n\n`````bad`info\n## Outcome\n"
            "Invalid fence syntax cannot hide this duplicate.\n`````"
        )
        self.assertEqual(
            self.checker.validate_pull_request_event(
                _event_with_body(invalid_fence_duplicate)
            ),
            ["pull request body repeats required section '## Outcome'"],
        )

    def test_fenced_comment_syntax_cannot_hide_later_headings(self) -> None:
        body = _valid_body().replace(
            "## Outcome\n",
            "## Outcome\n```text\n<!-- literal code, not a comment\n```\n",
            1,
        )

        self.assertEqual(
            self.checker.validate_pull_request_event(_event_with_body(body)),
            [],
        )

    def test_placeholder_only_lines_and_headings_are_not_substantive(self) -> None:
        body = _valid_body()
        for replacement in (
            "TBD\nTODO",
            "### TODO",
            "### Details",
            "~~~text\n~~~",
            "<span>TBD</span>",
            "&nbsp;",
            "<br>",
            "[TBD](https://example.invalid)",
            "[ref]: https://example.invalid",
            "Details\n-------",
            "[ref]: https://example.invalid\n  \"descriptive title\"",
            "`TBD`",
            "`` TODO ``",
        ):
            with self.subTest(replacement=replacement):
                mutated = _replace_heading_content(
                    body, "## Outcome", replacement
                )
                self.assertEqual(
                    self.checker.validate_pull_request_event(
                        _event_with_body(mutated)
                    ),
                    [
                        "pull request section '## Outcome' must contain "
                        "substantive content"
                    ],
                )

    def test_unicode_prose_and_literal_inline_code_are_substantive(self) -> None:
        body = _valid_body()
        for replacement in (
            "実装結果を確認しました。",
            "`<!-- literal -->`",
        ):
            with self.subTest(replacement=replacement):
                mutated = _replace_heading_content(
                    body, "## Outcome", replacement
                )
                self.assertEqual(
                    self.checker.validate_pull_request_event(
                        _event_with_body(mutated)
                    ),
                    [],
                )

    def test_evidence_subsections_enforce_content_location_order_and_uniqueness(self) -> None:
        controls = _read_json("pull-requests/markdown-controls.json")
        body = _valid_body()
        for heading in controls["requiredEvidenceSubsections"]:
            for replacement in controls["nonSubstantiveContent"]:
                with self.subTest(heading=heading, replacement=replacement):
                    mutated = _replace_heading_content(body, heading, replacement)
                    self.assertEqual(
                        self.checker.validate_pull_request_event(_event_with_body(mutated)),
                        [f"pull request Evidence subsection '{heading}' must contain substantive content"],
                    )

            with self.subTest(heading=heading, mutation="duplicate"):
                duplicate = f"\n\n{heading}\nDuplicate evidence metadata must fail."
                mutated = body.replace(
                    "\n\n## Risks, assumptions, and exclusions",
                    f"{duplicate}\n\n## Risks, assumptions, and exclusions",
                    1,
                )
                self.assertEqual(
                    self.checker.validate_pull_request_event(_event_with_body(mutated)),
                    [f"pull request Evidence section repeats required subsection '{heading}'"],
                )

            with self.subTest(heading=heading, mutation="outside-evidence"):
                content_removed = body.replace(f"{heading}\n", "", 1)
                mutated = f"{content_removed}\n\n{heading}\nOutside Evidence does not satisfy the contract."
                self.assertEqual(
                    self.checker.validate_pull_request_event(_event_with_body(mutated)),
                    [f"pull request Evidence section missing required subsection '{heading}'"],
                )

        baseline = "### Baseline / falsifier\nA legacy subject and incomplete body must be rejected."
        verification = "### Verification\nRun `python3 -m unittest discover -s tests/governance -v`."
        reordered = body.replace(
            f"{baseline}\n\n{verification}",
            f"{verification}\n\n{baseline}",
        )
        self.assertEqual(
            self.checker.validate_pull_request_event(_event_with_body(reordered)),
            ["pull request Evidence subsections must appear in the documented order"],
        )


@unittest.skipUnless(CHECKER_EXISTS, "blocked only by the missing governance checker")
class DocumentationContract(unittest.TestCase):
    def test_guidance_anchor_and_template_headings_match_the_checker_contract(self) -> None:
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("\n## Conventional commits\n", contributing)

        template = ROOT / ".github" / "pull_request_template.md"
        self.assertTrue(template.is_file(), "missing .github/pull_request_template.md")
        actual = [
            line
            for line in template.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ") or line.startswith("### ")
        ]
        controls = _read_json("pull-requests/markdown-controls.json")
        expected: list[str] = []
        for heading in controls["requiredSections"]:
            expected.append(heading)
            if heading == "## Evidence":
                expected.extend(controls["requiredEvidenceSubsections"])
        self.assertEqual(actual, expected)


@unittest.skipUnless(CHECKER_EXISTS, "blocked only by the missing governance checker")
class CliContract(unittest.TestCase):
    def test_pr_event_mode_accepts_complete_and_rejects_incomplete_metadata(self) -> None:
        valid = subprocess.run(
            [sys.executable, str(CHECKER), "pr-event", "--event", str(FIXTURES / "pull-requests" / "valid-event.json")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(valid.stderr, "")

        invalid_case = _read_json("pull-requests/invalid-events.json")[0]
        with tempfile.TemporaryDirectory() as directory:
            event_path = Path(directory) / "event.json"
            event_path.write_text(json.dumps(invalid_case["event"]), encoding="utf-8")
            invalid = subprocess.run(
                [sys.executable, str(CHECKER), "pr-event", "--event", str(event_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(invalid.returncode, 1)
        self.assertEqual(invalid.stdout, "")
        self.assertEqual(invalid.stderr, "\n".join(invalid_case["expected"]) + "\n")
        self.assertNotIn("Traceback", invalid.stderr)

    def test_pr_event_mode_has_exact_clean_malformed_diagnostics(self) -> None:
        malformed = _read_json("pull-requests/malformed-events.json")
        invalid = _read_json("pull-requests/invalid-events.json")
        cases = (
            malformed[0],
            invalid[0],
            next(case for case in malformed if case["name"] == "null-body"),
        )
        for case in cases:
            with self.subTest(case=case["name"]), tempfile.TemporaryDirectory() as directory:
                event_path = Path(directory) / "event.json"
                event_path.write_text(json.dumps(case["event"]), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(CHECKER), "pr-event", "--event", str(event_path)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "\n".join(case["expected"]) + "\n")
                self.assertNotIn("Traceback", result.stderr)

    def test_pr_event_mode_rejects_non_utf8_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event_path = Path(directory) / "event.json"
            event_path.write_bytes(b"\xff")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER),
                    "pr-event",
                    "--event",
                    str(event_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            f"pull request event JSON '{event_path}' must be UTF-8 encoded\n",
        )
        self.assertNotIn("Traceback", result.stderr)

    def test_commit_range_mode_checks_only_the_requested_successor_range(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(["git", "init", "--quiet"], cwd=repository, check=True)
            subprocess.run(["git", "config", "user.name", "Governance Fixture"], cwd=repository, check=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repository, check=True)

            tracked = repository / "state.txt"
            tracked.write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "state.txt"], cwd=repository, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "Bootstrap legacy fixture repository"], cwd=repository, check=True)
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=True
            ).stdout.strip()

            tracked.write_text("valid successor\n", encoding="utf-8")
            subprocess.run(["git", "add", "state.txt"], cwd=repository, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "fix(governance): validate successor range"], cwd=repository, check=True)
            valid_head = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=True
            ).stdout.strip()
            valid = subprocess.run(
                [sys.executable, str(CHECKER), "commit-range", "--base", base, "--head", valid_head],
                cwd=repository,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertEqual(valid.stderr, "")

            tracked.write_text("first legacy successor\n", encoding="utf-8")
            subprocess.run(["git", "add", "state.txt"], cwd=repository, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "Add legacy successor"], cwd=repository, check=True)
            first_invalid = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=True
            ).stdout.strip()

            tracked.write_text("second legacy successor\n", encoding="utf-8")
            subprocess.run(["git", "add", "state.txt"], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "--quiet", "-m", "squash! fix(governance): validate successor range"],
                cwd=repository,
                check=True,
            )
            second_invalid = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=True
            ).stdout.strip()

            tracked.write_text("valid head after failures\n", encoding="utf-8")
            subprocess.run(["git", "add", "state.txt"], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "--quiet", "-m", "test(governance): retain non-head failures"],
                cwd=repository,
                check=True,
            )
            final_head = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=True
            ).stdout.strip()
            invalid = subprocess.run(
                [sys.executable, str(CHECKER), "commit-range", "--base", base, "--head", final_head],
                cwd=repository,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(invalid.returncode, 1)
            self.assertEqual(invalid.stdout, "")
            self.assertEqual(
                invalid.stderr,
                f"{first_invalid}: commit subject must match '<type>[optional scope][!]: <description>'; see CONTRIBUTING.md#conventional-commits\n"
                f"{second_invalid}: commit subject must not use fixup! or squash! prefixes\n",
            )
            self.assertNotIn("Traceback", invalid.stderr)

    def test_commit_range_uses_two_dot_and_excludes_base_only_legacy_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(["git", "init", "--quiet", "--initial-branch=main"], cwd=repository, check=True)
            subprocess.run(["git", "config", "user.name", "Governance Fixture"], cwd=repository, check=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repository, check=True)

            (repository / "root.txt").write_text("common ancestor\n", encoding="utf-8")
            subprocess.run(["git", "add", "root.txt"], cwd=repository, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "chore: establish divergent fixture"], cwd=repository, check=True)

            subprocess.run(["git", "checkout", "--quiet", "-b", "head-branch"], cwd=repository, check=True)
            (repository / "head.txt").write_text("head only\n", encoding="utf-8")
            subprocess.run(["git", "add", "head.txt"], cwd=repository, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "test(governance): add head-only change"], cwd=repository, check=True)
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=True
            ).stdout.strip()

            subprocess.run(["git", "checkout", "--quiet", "main"], cwd=repository, check=True)
            (repository / "base.txt").write_text("base only legacy\n", encoding="utf-8")
            subprocess.run(["git", "add", "base.txt"], cwd=repository, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "Add base-only legacy change"], cwd=repository, check=True)
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=True
            ).stdout.strip()

            two_dot = subprocess.run(
                ["git", "rev-list", f"{base}..{head}"],
                cwd=repository,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.splitlines()
            symmetric = subprocess.run(
                ["git", "rev-list", f"{base}...{head}"],
                cwd=repository,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.splitlines()
            self.assertNotIn(base, two_dot)
            self.assertIn(base, symmetric)

            result = subprocess.run(
                [sys.executable, str(CHECKER), "commit-range", "--base", base, "--head", head],
                cwd=repository,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")

    def test_commit_range_mode_rejects_a_real_two_parent_merge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(["git", "init", "--quiet", "--initial-branch=main"], cwd=repository, check=True)
            subprocess.run(["git", "config", "user.name", "Governance Fixture"], cwd=repository, check=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repository, check=True)

            (repository / "base.txt").write_text("legacy base\n", encoding="utf-8")
            subprocess.run(["git", "add", "base.txt"], cwd=repository, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "Bootstrap legacy merge fixture"], cwd=repository, check=True)
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=True
            ).stdout.strip()

            subprocess.run(["git", "checkout", "--quiet", "-b", "side"], cwd=repository, check=True)
            (repository / "side.txt").write_text("side\n", encoding="utf-8")
            subprocess.run(["git", "add", "side.txt"], cwd=repository, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "test(governance): add side branch"], cwd=repository, check=True)

            subprocess.run(["git", "checkout", "--quiet", "main"], cwd=repository, check=True)
            (repository / "main.txt").write_text("main\n", encoding="utf-8")
            subprocess.run(["git", "add", "main.txt"], cwd=repository, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "test(governance): add main branch"], cwd=repository, check=True)
            subprocess.run(
                ["git", "merge", "--quiet", "--no-ff", "side", "-m", "chore: reconcile fixture branches"],
                cwd=repository,
                check=True,
            )
            merge_head = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True, capture_output=True, check=True
            ).stdout.strip()
            parent_line = subprocess.run(
                ["git", "rev-list", "--parents", "-n", "1", merge_head],
                cwd=repository,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.split()
            self.assertEqual(len(parent_line), 3, parent_line)

            result = subprocess.run(
                [sys.executable, str(CHECKER), "commit-range", "--base", base, "--head", merge_head],
                cwd=repository,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertEqual(
                result.stderr,
                f"{merge_head}: pull request history must not contain merge commits\n",
            )
            self.assertNotIn("Traceback", result.stderr)

    def test_commit_range_rejects_non_utf8_subject_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(
                ["git", "init", "--quiet"], cwd=repository, check=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Governance Fixture"],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "fixture@example.invalid"],
                cwd=repository,
                check=True,
            )
            tracked = repository / "state.txt"
            tracked.write_text("base\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "state.txt"], cwd=repository, check=True
            )
            subprocess.run(
                ["git", "commit", "--quiet", "-m", "chore: establish base"],
                cwd=repository,
                check=True,
            )
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repository,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            tree = subprocess.run(
                ["git", "write-tree"],
                cwd=repository,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            raw_commit = (
                f"tree {tree}\nparent {base}\n"
                "author Governance Fixture <fixture@example.invalid> 1 +0000\n"
                "committer Governance Fixture <fixture@example.invalid> 1 +0000\n\n"
            ).encode("ascii") + b"\xff\n"
            head = subprocess.run(
                ["git", "hash-object", "-t", "commit", "-w", "--stdin"],
                cwd=repository,
                input=raw_commit,
                capture_output=True,
                check=True,
            ).stdout.decode("ascii").strip()

            result = subprocess.run(
                [
                    sys.executable,
                    str(CHECKER),
                    "commit-range",
                    "--base",
                    base,
                    "--head",
                    head,
                ],
                cwd=repository,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            f"{head}: commit subject must be UTF-8 encoded\n",
        )
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
