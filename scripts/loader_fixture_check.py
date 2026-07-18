#!/usr/bin/env python3
"""Red-first oracle packet for the Wave 3 deterministic local loader.

The harness intentionally uses only the Python standard library.  It invokes the
public ``record_check.py`` command in disposable source trees and freezes only the
portable diagnostic contract: exit status, code, normalized source label, JSON
pointer, and ordering.  Message prose after ``:`` is deliberately ignored.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "record_check.py"
FIXTURES = ROOT / "fixtures" / "loader" / "v1"
DIAGNOSTIC_HEAD = re.compile(r"^[A-Z][A-Z0-9_]+ [^#]+#(?:/.*)?$")


@dataclass(frozen=True)
class Observation:
    exit_status: int
    signatures: list[str]
    stdout: str
    stderr: str


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _copy_tree(source: Path, target: Path) -> None:
    shutil.copytree(source, target)


def _diagnostic_signatures(stdout: str) -> tuple[list[str], list[str]]:
    signatures: list[str] = []
    errors: list[str] = []
    for line in stdout.splitlines():
        if not line:
            continue
        head = line.split(": ", 1)[0]
        if not DIAGNOSTIC_HEAD.fullmatch(head):
            errors.append(f"unrecognized output line {line!r}")
            continue
        signatures.append(head)
    return signatures, errors


def _invoke(cwd: Path, arguments: list[str]) -> tuple[Observation, list[str]]:
    completed = subprocess.run(
        [sys.executable, str(CHECKER), *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.stdout.strip() == "Graph is valid: 0 diagnostics.":
        signatures: list[str] = []
        parse_errors: list[str] = []
    else:
        signatures, parse_errors = _diagnostic_signatures(completed.stdout)
    return (
        Observation(
            exit_status=completed.returncode,
            signatures=signatures,
            stdout=completed.stdout,
            stderr=completed.stderr,
        ),
        parse_errors,
    )


def _expect(
    name: str,
    cwd: Path,
    arguments: list[str],
    exit_status: int,
    signatures: list[str],
) -> list[str]:
    observation, errors = _invoke(cwd, arguments)
    failures = [f"{name}: {error}" for error in errors]
    if observation.exit_status != exit_status:
        failures.append(
            f"{name}: expected exit {exit_status}, got {observation.exit_status}; "
            f"stdout={observation.stdout!r}, stderr={observation.stderr!r}"
        )
    if observation.signatures != signatures:
        failures.append(
            f"{name}: expected diagnostics {signatures!r}, got "
            f"{observation.signatures!r}; stdout={observation.stdout!r}"
        )
    if observation.stderr:
        failures.append(f"{name}: expected empty stderr, got {observation.stderr!r}")
    return failures


def _valid(name: str, cwd: Path, arguments: list[str]) -> list[str]:
    return _expect(name, cwd, arguments, 0, [])


def check_alias_and_overlap() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-alias-") as raw:
        source = Path(raw)
        _copy(FIXTURES / "templates" / "minimal-spec.json", source / "records" / "item.json")
        (source / "records" / "nested").mkdir()
        return _valid(
            "lexical aliases, repeated argv, and file/directory overlap are idempotent",
            source,
            [
                "records/item.json",
                "./records/item.json",
                "records/nested/../item.json",
                "records/item.json",
                "records",
            ],
        )


def check_recursive_discovery_and_ignored_files() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-discovery-") as raw:
        source = Path(raw)
        _copy_tree(FIXTURES / "discovery", source / "registry")
        (source / "registry" / "README.txt").write_text("not a record\n", encoding="utf-8")
        (source / "registry" / "IGNORED.JSON").write_text("not json\n", encoding="utf-8")
        return _valid(
            "directories recursively discover lowercase JSON and ignore other files",
            source,
            ["registry"],
        )


def check_explicit_non_json() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-extension-") as raw:
        source = Path(raw)
        _copy(FIXTURES / "templates" / "valid-record.txt", source / "record.txt")
        return _expect(
            "an explicit non-JSON file is rejected before content validation",
            source,
            ["record.txt"],
            1,
            ["INPUT_NON_JSON record.txt#"],
        )


def check_empty_source_set() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-empty-") as raw:
        source = Path(raw)
        (source / "empty").mkdir()
        (source / "empty" / "README.txt").write_text("ignored\n", encoding="utf-8")
        return _expect(
            "a source list discovering no records is an input failure",
            source,
            ["empty"],
            1,
            ["INPUT_EMPTY_SOURCE_SET empty#"],
        )


def check_symlink_rejection() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-symlink-") as raw:
        source = Path(raw)
        _copy(FIXTURES / "templates" / "minimal-spec.json", source / "record.json")
        try:
            os.symlink("record.json", source / "record-link.json")
        except (OSError, NotImplementedError) as error:
            return [f"explicit symbolic-link input is rejected: could not create test symlink: {error}"]
        failures = _expect(
            "an explicit symbolic-link input is rejected",
            source,
            ["record-link.json"],
            1,
            ["INPUT_SYMLINK record-link.json#"],
        )
        _copy(FIXTURES / "templates" / "minimal-spec.json", source / "registry" / "record.json")
        try:
            os.symlink("record.json", source / "registry" / "record-link.json")
        except (OSError, NotImplementedError) as error:
            failures.append(
                "a recursively discovered symbolic link is rejected: "
                f"could not create test symlink: {error}"
            )
            return failures
        failures.extend(
            _expect(
                "a lowercase JSON symbolic link found during recursive discovery is rejected",
                source,
                ["registry"],
                1,
                ["INPUT_SYMLINK registry/record-link.json#"],
            )
        )
        return failures


def check_stable_source_order() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-order-") as raw:
        source = Path(raw)
        _copy(FIXTURES / "schema-invalid" / "kind-array.json", source / "left" / "a.json")
        _copy(
            FIXTURES / "schema-invalid" / "unknown-field.json",
            source / "right" / "nested" / "z.json",
        )
        expected = [
            "SCHEMA_KIND_TYPE left/a.json#/kind",
            "SCHEMA_UNKNOWN_FIELD right/nested/z.json#/surprise",
        ]
        failures = _expect(
            "diagnostics are stable when directory arguments are reversed (forward)",
            source,
            ["right", "left"],
            1,
            expected,
        )
        failures.extend(
            _expect(
                "diagnostics are stable when directory arguments are reversed (reverse)",
                source,
                ["left", "right"],
                1,
                expected,
            )
        )
        return failures


def check_distinct_file_duplicate_address() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-duplicate-") as raw:
        source = Path(raw)
        template = FIXTURES / "templates" / "minimal-spec.json"
        _copy(template, source / "duplicates" / "a.json")
        _copy(template, source / "duplicates" / "b.json")
        return _expect(
            "distinct sources with one canonical address remain a graph error",
            source,
            ["duplicates"],
            1,
            ["LINK_DUPLICATE_ADDRESS duplicates/b.json#"],
        )


def check_input_schema_phase_barrier() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-barrier-") as raw:
        source = Path(raw)
        _copy(
            FIXTURES / "imports" / "dangling" / "loaded" / "importer.json",
            source / "source" / "dangling.json",
        )
        _copy(
            FIXTURES / "templates" / "malformed-json.txt",
            source / "source" / "malformed.json",
        )
        _copy(
            FIXTURES / "schema-invalid" / "kind-array.json",
            source / "source" / "schema-invalid.json",
        )
        return _expect(
            "input/schema failures suppress link cascades from the partial graph",
            source,
            ["source"],
            1,
            [
                "INPUT_INVALID_JSON source/malformed.json#",
                "SCHEMA_KIND_TYPE source/schema-invalid.json#/kind",
            ],
        )


def check_visible_import_edges() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="semantic-loader-imports-") as raw:
        source = Path(raw)
        _copy_tree(FIXTURES / "imports", source / "imports")
        for case in ("self", "cycle", "diamond", "repeated"):
            failures.extend(
                _valid(
                    f"{case} imports remain valid visible edges",
                    source,
                    [f"imports/{case}"],
                )
            )
        failures.extend(
            _expect(
                "an import outside the supplied source set remains dangling",
                source,
                ["imports/dangling/loaded"],
                1,
                [
                    "LINK_DANGLING_REFERENCE "
                    "imports/dangling/loaded/importer.json#/imports/0"
                ],
            )
        )
    return failures


def main() -> int:
    checks = [
        check_alias_and_overlap,
        check_recursive_discovery_and_ignored_files,
        check_explicit_non_json,
        check_empty_source_set,
        check_symlink_rejection,
        check_stable_source_order,
        check_distinct_file_duplicate_address,
        check_input_schema_phase_barrier,
        check_visible_import_edges,
    ]
    failures: list[str] = []
    for check in checks:
        failures.extend(check())
    if failures:
        print("Loader fixture checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Loader fixture checks passed: 9 contract groups.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
