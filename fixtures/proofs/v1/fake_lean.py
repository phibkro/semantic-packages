#!/usr/bin/env python3
"""Narrow table-driven fake Lean process for proof-boundary controls.

The real positive and semantic falsifier fixtures run against an explicitly supplied
Lean binary. This fake exercises bounded tool lifecycle and proves that
`proof_check.py` requires valid structured statement/no-axioms observations and
warning-free output instead of trusting exit zero.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path


VERSION = "4.30.0"
COMMIT = "d024af099ca4bf2c86f649261ebf59565dc8c622"
STATEMENT = (
    "stack_pop_empty : ∀ (A : Type u), "
    "pop (empty : ObservedStack A) = Option.none"
)
NO_AXIOMS = "'stack_pop_empty' does not depend on any axioms"


def message(
    data: str,
    *,
    severity: str = "information",
    kind: str = "[anonymous]",
) -> None:
    print(
        json.dumps(
            {
                "caption": "",
                "data": data,
                "endPos": {"column": 0, "line": 1},
                "fileName": "generated.lean",
                "isSilent": False,
                "keepFullRange": False,
                "kind": kind,
                "pos": {"column": 0, "line": 1},
                "severity": severity,
            },
            separators=(",", ":"),
        )
    )


def hang() -> None:
    marker = os.environ.get("FAKE_LEAN_PID_MARKER")
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    if marker:
        Path(marker).write_text(str(os.getpid()) + "\n", encoding="ascii")
    while True:
        time.sleep(10)


def main() -> int:
    mode = os.environ.get("FAKE_LEAN_MODE", "missing-axiom-audit")
    if "--version" in sys.argv:
        if mode == "timeout-version":
            hang()
        print(
            f"Lean (version {VERSION}, x86_64-unknown-linux-gnu, "
            f"commit {COMMIT}, Release)"
        )
        return 0
    if "--githash" in sys.argv or "-g" in sys.argv:
        print(COMMIT)
        return 0

    if mode == "timeout-execution":
        hang()
    if mode == "malformed-output-forged-positive":
        print("not-json")
        message(STATEMENT)
        message(NO_AXIOMS)
        return 0
    if mode == "unexpected-output-forged-positive":
        print(json.dumps({"unexpected": True}, separators=(",", ":")))
        message(STATEMENT)
        message(NO_AXIOMS)
        return 0
    if mode == "warning-with-forged-positive":
        message("injected warning", severity="warning", kind="warning")
        message(STATEMENT)
        message(NO_AXIOMS)
        return 0
    if mode == "axiom-only-positive":
        message(NO_AXIOMS)
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
