#!/usr/bin/env python3
"""Minimal repository quality gate.

Checks required project-memory files and local Markdown links. This is intentionally
small so the first tracer bullet has an executable governance gate without locking
in a larger toolchain.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "docs/vision/constitution.md",
    "docs/research/synthesis.md",
    "docs/design/core-model.md",
    "docs/design/spec-language.md",
    "docs/design/tracer-bullet.md",
    "docs/exec-plans/active/0001-tracer-bullet.md",
]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def check_required() -> list[str]:
    return [f"missing required file: {path}" for path in REQUIRED if not (ROOT / path).is_file()]


def check_markdown_links() -> list[str]:
    errors: list[str] = []
    for md in ROOT.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (md.parent / unquote(target)).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"{md.relative_to(ROOT)}: link escapes repository: {raw_target}")
                continue
            if not resolved.exists():
                errors.append(f"{md.relative_to(ROOT)}: broken link: {raw_target}")
    return errors


def main() -> int:
    errors = check_required() + check_markdown_links()
    if errors:
        print("Repository checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
