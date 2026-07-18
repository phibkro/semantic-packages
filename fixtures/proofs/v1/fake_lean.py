#!/usr/bin/env python3
"""Narrow fake Lean process for missing/invalid audit-output controls.

The real positive and semantic falsifier fixtures run against an explicitly supplied
Lean binary.  This fake exists only to prove that `proof_check.py` requires structured
statement and no-axioms observations instead of trusting exit zero.
"""

from __future__ import annotations

import json
import os
import sys


VERSION = "4.30.0"
COMMIT = "d024af099ca4bf2c86f649261ebf59565dc8c622"
STATEMENT = "stack_pop_empty : ∀ (A : Type u), pop empty = none"


def message(data: str) -> None:
    print(
        json.dumps(
            {
                "caption": "",
                "data": data,
                "endPos": {"column": 0, "line": 1},
                "fileName": "generated.lean",
                "isSilent": False,
                "keepFullRange": False,
                "kind": "[anonymous]",
                "pos": {"column": 0, "line": 1},
                "severity": "information",
            },
            separators=(",", ":"),
        )
    )


def main() -> int:
    mode = os.environ.get("FAKE_LEAN_MODE", "missing-axiom-audit")
    if "--version" in sys.argv:
        print(
            f"Lean (version {VERSION}, x86_64-unknown-linux-gnu, "
            f"commit {COMMIT}, Release)"
        )
        return 0
    if "--githash" in sys.argv or "-g" in sys.argv:
        print(COMMIT)
        return 0

    message(STATEMENT)
    if mode == "invalid-axiom-audit":
        message("'stack_pop_empty' axiom audit is unavailable")
    elif mode != "missing-axiom-audit":
        print(f"unknown fake Lean mode: {mode}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
