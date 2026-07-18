#!/usr/bin/env python3
"""Validate prospective commit and pull-request metadata.

The checker is deliberately local and deterministic.  It does not inspect GitHub or
apply the policy to commits outside the explicitly supplied ``base..head`` range.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any


ALLOWED_TYPES = (
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
)
ALLOWED_TYPES_TEXT = ", ".join(ALLOWED_TYPES)
REQUIRED_SECTIONS = (
    "## Outcome",
    "## Change class and lifecycle",
    "## Governing scope",
    "## Design and changes",
    "## Evidence",
    "## Risks, assumptions, and exclusions",
    "## Recovery, maintenance, and reopen triggers",
    "## Review plan and dispositions",
)
REQUIRED_EVIDENCE_SUBSECTIONS = (
    "### Baseline / falsifier",
    "### Verification",
)
NON_SUBSTANTIVE_CONTENT = {"", "tbd", "n/a", "n-a", "todo"}
_NON_SUBSTANTIVE_TOKEN_SEQUENCES = {
    tuple(re.findall(r"[a-z0-9]+", value.casefold()))
    for value in NON_SUBSTANTIVE_CONTENT
    if value
}
_AUTOSQUASH_PREFIXES = ("fixup! ", "squash! ")
_CONVENTIONAL_PATTERN = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)\r\n]*)\))?(?P<breaking>!)?: "
    r"(?P<description>[^\r\n]*)$"
)
_FENCE_OPEN = re.compile(
    r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$"
)
_ATX_HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+|$)")
_SETEXT_HEADING_UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
_LINK_REFERENCE_DEFINITION = re.compile(r"^ {0,3}\[[^]]+\]:")
_LINK_REFERENCE_TITLE_CONTINUATION = re.compile(
    r'''^ {1,3}(?:"[^"\r\n]*"|'[^'\r\n]*'|\([^()\r\n]*\))[ \t]*$'''
)
_INLINE_LINK = re.compile(r"!?\[([^]]*)\]\([^\r\n)]*\)")
_REFERENCE_LINK = re.compile(r"!?\[([^]]*)\]\[[^]]*\]")
_HTML_WRAPPER = re.compile(
    r"</?[A-Za-z][A-Za-z0-9-]*(?:[ \t][^<>]*)?/?>"
)
_INLINE_CODE_MARKER = "\ue000"


def _validate_conventional_text(value: str, *, kind: str) -> list[str]:
    if value.startswith(_AUTOSQUASH_PREFIXES):
        return [f"{kind} must not use fixup! or squash! prefixes"]

    match = _CONVENTIONAL_PATTERN.fullmatch(value)
    if match is None or (
        match.group("scope") is not None and not match.group("scope").strip()
    ):
        return [
            f"{kind} must match '<type>[optional scope][!]: <description>'; "
            "see CONTRIBUTING.md#conventional-commits"
        ]

    change_type = match.group("type")
    if change_type not in ALLOWED_TYPES:
        noun = "commit type" if kind == "commit subject" else "pull request type"
        return [
            f"unsupported {noun} '{change_type}'; allowed types: {ALLOWED_TYPES_TEXT}"
        ]

    if not match.group("description").strip():
        noun = "commit description" if kind == "commit subject" else "pull request description"
        return [f"{noun} must contain non-whitespace text"]

    if len(value) > 72:
        noun = "commit subject" if kind == "commit subject" else "pull request title"
        return [f"{noun} exceeds 72 characters ({len(value)})"]

    return []


def validate_commit_subject(subject: str, parent_count: int = 1) -> list[str]:
    """Return stable diagnostics for one commit subject and its parent count."""

    if parent_count >= 2:
        return ["pull request history must not contain merge commits"]
    return _validate_conventional_text(subject, kind="commit subject")


def _remove_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    visible: list[str] = []
    cursor = 0
    while cursor < len(line):
        if in_comment:
            end = line.find("-->", cursor)
            if end < 0:
                visible.append(" " * (len(line) - cursor))
                return "".join(visible), True
            visible.append(" " * (end + 3 - cursor))
            cursor = end + 3
            in_comment = False
            continue

        start = line.find("<!--", cursor)
        if start < 0:
            visible.append(line[cursor:])
            break
        visible.append(line[cursor:start])
        visible.append(" " * 4)
        cursor = start + 4
        in_comment = True
    return "".join(visible), in_comment


def _fence_opening(line: str) -> tuple[str, int] | None:
    opening = _FENCE_OPEN.match(line)
    if opening is None:
        return None
    fence = opening.group("fence")
    if fence[0] == "`" and "`" in opening.group("info"):
        return None
    return fence[0], len(fence)


def _is_fence_closing(line: str, character: str, length: int) -> bool:
    return (
        re.match(
            rf"^ {{0,3}}{re.escape(character)}{{{length},}}[ \t]*$",
            line,
        )
        is not None
    )


def _mask_inline_code_spans(line: str) -> tuple[str, tuple[tuple[int, str], ...]]:
    """Mask bounded single-line code spans before interpreting HTML comments.

    Each marker retains its literal text only when it remains visible after comment
    removal. Positions are recorded so an unrelated private-use character in input
    cannot manufacture substance.
    """

    masked = list(line)
    marked_literals: list[tuple[int, str]] = []
    cursor = 0
    while cursor < len(line):
        opening = line.find("`", cursor)
        if opening < 0:
            break
        opening_end = opening
        while opening_end < len(line) and line[opening_end] == "`":
            opening_end += 1
        run_length = opening_end - opening

        closing = opening_end
        while True:
            closing = line.find("`" * run_length, closing)
            if closing < 0:
                cursor = opening_end
                break
            before_is_tick = closing > 0 and line[closing - 1] == "`"
            after = closing + run_length
            after_is_tick = after < len(line) and line[after] == "`"
            if not before_is_tick and not after_is_tick:
                content = line[opening_end:closing]
                for index in range(opening, after):
                    masked[index] = " "
                masked[opening] = _INLINE_CODE_MARKER
                marked_literals.append((opening, content))
                cursor = after
                break
            closing = after

    return "".join(masked), tuple(marked_literals)


def _unicode_word_tokens(content: str) -> list[str]:
    """Return Unicode letter/number words for prose and placeholder checks."""

    tokens: list[str] = []
    current: list[str] = []
    normalized = unicodedata.normalize("NFKC", content).casefold()
    for character in normalized:
        category = unicodedata.category(character)
        if category[0] in {"L", "N"} or (current and category[0] == "M"):
            current.append(character)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tokens


def _markdown_headings(lines: list[str]) -> list[tuple[int, str]]:
    """Find real column-zero level-two/three headings needed by the contract."""

    headings: list[tuple[int, str]] = []
    in_comment = False
    fence_character: str | None = None
    fence_length = 0

    for index, original in enumerate(lines):
        if fence_character is not None:
            if _is_fence_closing(original, fence_character, fence_length):
                fence_character = None
                fence_length = 0
            continue

        masked, _marked_literals = _mask_inline_code_spans(original)
        visible, in_comment = _remove_html_comments(masked, in_comment)

        opening = _fence_opening(visible)
        if opening is not None:
            fence_character, fence_length = opening
            continue

        if visible.startswith("## ") and not visible.startswith("### "):
            headings.append((index, visible))
        elif visible.startswith("### ") and not visible.startswith("#### "):
            headings.append((index, visible))

    return headings


def _rendered_substance(lines: list[str]) -> tuple[bool, str]:
    rendered_lines: list[tuple[str, bool]] = []
    has_fenced_code = False
    in_comment = False
    fence_character: str | None = None
    fence_length = 0
    reference_title_may_follow = False

    for original in lines:
        if fence_character is not None:
            if _is_fence_closing(original, fence_character, fence_length):
                fence_character = None
                fence_length = 0
            elif original.strip():
                has_fenced_code = True
            rendered_lines.append(("", False))
            continue

        masked, marked_literals = _mask_inline_code_spans(original)
        visible, in_comment = _remove_html_comments(masked, in_comment)
        inline_literals = [
            literal
            for position, literal in marked_literals
            if position < len(visible) and visible[position] == _INLINE_CODE_MARKER
        ]
        visible = visible.replace(_INLINE_CODE_MARKER, " ")
        opening = _fence_opening(visible)
        if opening is not None:
            fence_character, fence_length = opening
            reference_title_may_follow = False
            rendered_lines.append(("", False))
            continue
        if _ATX_HEADING.match(visible) is not None:
            reference_title_may_follow = False
            rendered_lines.append(("", False))
            continue
        if _SETEXT_HEADING_UNDERLINE.match(visible) is not None:
            if rendered_lines and rendered_lines[-1][0].strip():
                rendered_lines[-1] = ("", False)
            reference_title_may_follow = False
            rendered_lines.append(("", False))
            continue
        if (
            reference_title_may_follow
            and _LINK_REFERENCE_TITLE_CONTINUATION.match(visible) is not None
        ):
            reference_title_may_follow = False
            rendered_lines.append(("", False))
            continue
        reference_title_may_follow = False
        if _LINK_REFERENCE_DEFINITION.match(visible) is not None:
            reference_title_may_follow = True
            rendered_lines.append(("", False))
            continue

        visible = _INLINE_LINK.sub(r"\1", visible)
        visible = _REFERENCE_LINK.sub(r"\1", visible)
        visible = _HTML_WRAPPER.sub("", visible)
        visible = html.unescape(visible)
        visible = "".join(
            character
            for character in visible
            if unicodedata.category(character) != "Cf"
        )
        rendered = "\n".join((visible, *inline_literals))
        rendered_lines.append((rendered, False))

    has_code = has_fenced_code or any(
        line_has_code for _line, line_has_code in rendered_lines
    )
    return has_code, "\n".join(line for line, _line_has_code in rendered_lines)


def _is_substantive(lines: list[str]) -> bool:
    has_code, content = _rendered_substance(lines)
    if has_code:
        return True
    tokens = _unicode_word_tokens(content)
    if not tokens:
        return False

    reachable = {0}
    for start in range(len(tokens)):
        if start not in reachable:
            continue
        for placeholder in _NON_SUBSTANTIVE_TOKEN_SEQUENCES:
            end = start + len(placeholder)
            if tuple(tokens[start:end]) == placeholder:
                reachable.add(end)
    return len(tokens) not in reachable


def _validate_pull_request_body(body: str) -> list[str]:
    lines = body.splitlines()
    headings = _markdown_headings(lines)
    level_two = [(line, heading) for line, heading in headings if heading.startswith("## ")]

    locations: dict[str, list[int]] = {
        required: [line for line, heading in level_two if heading == required]
        for required in REQUIRED_SECTIONS
    }
    for required in REQUIRED_SECTIONS:
        if not locations[required]:
            return [f"pull request body missing required section '{required}'"]
    for required in REQUIRED_SECTIONS:
        if len(locations[required]) > 1:
            return [f"pull request body repeats required section '{required}'"]

    ordered_lines = [locations[required][0] for required in REQUIRED_SECTIONS]
    if ordered_lines != sorted(ordered_lines):
        return ["pull request body sections must appear in the documented order"]

    level_two_lines = [line for line, _heading in level_two]
    for required in REQUIRED_SECTIONS:
        start = locations[required][0]
        following = [line for line in level_two_lines if line > start]
        end = min(following) if following else len(lines)
        if not _is_substantive(lines[start + 1 : end]):
            return [f"pull request section '{required}' must contain substantive content"]

    evidence_start = locations["## Evidence"][0]
    following_sections = [line for line in level_two_lines if line > evidence_start]
    evidence_end = min(following_sections) if following_sections else len(lines)
    evidence_headings = [
        (line, heading)
        for line, heading in headings
        if evidence_start < line < evidence_end and heading.startswith("### ")
    ]
    evidence_locations: dict[str, list[int]] = {
        required: [
            line for line, heading in evidence_headings if heading == required
        ]
        for required in REQUIRED_EVIDENCE_SUBSECTIONS
    }
    for required in REQUIRED_EVIDENCE_SUBSECTIONS:
        if not evidence_locations[required]:
            return [
                f"pull request Evidence section missing required subsection '{required}'"
            ]
    for required in REQUIRED_EVIDENCE_SUBSECTIONS:
        if len(evidence_locations[required]) > 1:
            return [
                f"pull request Evidence section repeats required subsection '{required}'"
            ]

    ordered_evidence = [
        evidence_locations[required][0] for required in REQUIRED_EVIDENCE_SUBSECTIONS
    ]
    if ordered_evidence != sorted(ordered_evidence):
        return ["pull request Evidence subsections must appear in the documented order"]

    evidence_heading_lines = [line for line, _heading in evidence_headings]
    for required in REQUIRED_EVIDENCE_SUBSECTIONS:
        start = evidence_locations[required][0]
        following = [line for line in evidence_heading_lines if line > start]
        end = min(following) if following else evidence_end
        if not _is_substantive(lines[start + 1 : end]):
            return [
                f"pull request Evidence subsection '{required}' must contain substantive content"
            ]

    return []


def validate_pull_request_event(event: Any) -> list[str]:
    """Return stable diagnostics for any JSON-shaped pull-request event value."""

    if not isinstance(event, dict):
        return ["pull request event must be an object"]
    if "pull_request" not in event:
        return ["pull request event missing object 'pull_request'"]

    pull_request = event["pull_request"]
    if not isinstance(pull_request, dict):
        return ["pull request event field 'pull_request' must be an object"]
    if "title" not in pull_request:
        return ["pull request event missing string 'pull_request.title'"]
    title = pull_request["title"]
    if not isinstance(title, str):
        return ["pull request event field 'pull_request.title' must be a string"]
    if "body" not in pull_request:
        return ["pull request event missing 'pull_request.body'"]
    body = pull_request["body"]
    if body is None:
        return ["pull request body is required"]
    if not isinstance(body, str):
        return ["pull request event field 'pull_request.body' must be a string or null"]

    title_errors = _validate_conventional_text(title, kind="pull request title")
    if title_errors:
        return title_errors
    return _validate_pull_request_body(body)


def _run_git(arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        capture_output=True,
        check=False,
    )


def _git_error_detail(stderr: bytes, fallback: str) -> str:
    return stderr.decode("utf-8", errors="replace").strip() or fallback


def _validate_commit_range(base: str, head: str) -> list[str]:
    revision_range = _run_git(
        ["rev-list", "--reverse", "--topo-order", f"{base}..{head}"]
    )
    if revision_range.returncode != 0:
        detail = _git_error_detail(revision_range.stderr, "git rev-list failed")
        return [f"cannot inspect commit range {base}..{head}: {detail}"]
    try:
        revision_output = revision_range.stdout.decode("ascii")
    except UnicodeDecodeError:
        return [f"cannot inspect commit range {base}..{head}: malformed git output"]

    diagnostics: list[str] = []
    for sha in revision_output.splitlines():
        metadata = _run_git(
            ["show", "-s", "--encoding=none", "--format=%s%x00%P", sha]
        )
        if metadata.returncode != 0:
            detail = _git_error_detail(metadata.stderr, "git show failed")
            diagnostics.append(f"{sha}: cannot inspect commit metadata: {detail}")
            continue
        subject_bytes, separator, parents_bytes = metadata.stdout.rstrip(b"\n").partition(
            b"\x00"
        )
        if not separator:
            diagnostics.append(f"{sha}: cannot inspect commit metadata: malformed git output")
            continue
        try:
            subject = subject_bytes.decode("utf-8")
        except UnicodeDecodeError:
            diagnostics.append(f"{sha}: commit subject must be UTF-8 encoded")
            continue
        try:
            parents = parents_bytes.decode("ascii")
        except UnicodeDecodeError:
            diagnostics.append(f"{sha}: cannot inspect commit metadata: malformed git output")
            continue
        parent_count = len(parents.split())
        for diagnostic in validate_commit_subject(subject, parent_count=parent_count):
            diagnostics.append(f"{sha}: {diagnostic}")
    return diagnostics


def _write_diagnostics(diagnostics: list[str]) -> int:
    if not diagnostics:
        return 0
    sys.stderr.write("\n".join(diagnostics) + "\n")
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    commit_range = commands.add_parser(
        "commit-range", help="validate every commit in the exact base..head range"
    )
    commit_range.add_argument("--base", required=True)
    commit_range.add_argument("--head", required=True)

    pull_request = commands.add_parser(
        "pr-event", help="validate a local pull-request event JSON file"
    )
    pull_request.add_argument("--event", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    if arguments.command == "commit-range":
        try:
            return _write_diagnostics(_validate_commit_range(arguments.base, arguments.head))
        except OSError as error:
            return _write_diagnostics([f"cannot execute git: {error}"])

    try:
        with arguments.event.open(encoding="utf-8") as event_file:
            event = json.load(event_file)
    except OSError as error:
        return _write_diagnostics(
            [f"cannot read pull request event JSON '{arguments.event}': {error}"]
        )
    except UnicodeDecodeError:
        return _write_diagnostics(
            [f"pull request event JSON '{arguments.event}' must be UTF-8 encoded"]
        )
    except json.JSONDecodeError as error:
        return _write_diagnostics(
            [f"pull request event JSON '{arguments.event}' is invalid: {error}"]
        )
    return _write_diagnostics(validate_pull_request_event(event))


if __name__ == "__main__":
    raise SystemExit(main())
