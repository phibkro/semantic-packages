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


def _invoke(
    cwd: Path,
    arguments: list[str],
    environment: dict[str, str] | None = None,
) -> tuple[Observation, list[str]]:
    process_environment = os.environ.copy()
    if environment:
        process_environment.update(environment)
    completed = subprocess.run(
        [sys.executable, str(CHECKER), *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=process_environment,
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
    environment: dict[str, str] | None = None,
) -> list[str]:
    observation, errors = _invoke(cwd, arguments, environment)
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


def check_unreadable_explicit_directory() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-unreadable-") as raw:
        source = Path(raw)
        directory = source / "unreadable"
        _copy(FIXTURES / "templates" / "minimal-spec.json", directory / "record.json")
        original_mode = directory.stat().st_mode & 0o7777
        failures: list[str] = []
        try:
            directory.chmod(0)
        except OSError as error:
            return [f"an unreadable explicit directory is rejected: chmod failed: {error}"]
        try:
            if os.access(directory, os.R_OK | os.X_OK):
                failures.append(
                    "an unreadable explicit directory is rejected: "
                    "platform did not enforce removed read/search permissions"
                )
            else:
                failures.extend(
                    _expect(
                        "an unreadable explicit directory becomes one stable input diagnostic",
                        source,
                        ["unreadable"],
                        1,
                        ["INPUT_READ_ERROR unreadable#"],
                    )
                )
        finally:
            directory.chmod(original_mode)
        return failures


def check_failing_source_alias_deduplication() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-failing-alias-") as raw:
        source = Path(raw)
        (source / "nested").mkdir()
        _copy(FIXTURES / "templates" / "valid-record.txt", source / "record.txt")
        try:
            os.symlink("absent-target.json", source / "broken.json")
        except (OSError, NotImplementedError) as error:
            return [f"failing source aliases are deduplicated: could not create test symlink: {error}"]

        failures = _expect(
            "lexical aliases of one missing JSON source produce one diagnostic",
            source,
            [
                "missing.json",
                "./missing.json",
                "nested/../missing.json",
                "missing.json",
            ],
            1,
            ["INPUT_NOT_FOUND missing.json#"],
        )
        failures.extend(
            _expect(
                "lexical aliases of one explicit non-JSON source produce one diagnostic",
                source,
                ["record.txt", "./record.txt", "nested/../record.txt", "record.txt"],
                1,
                ["INPUT_NON_JSON record.txt#"],
            )
        )
        failures.extend(
            _expect(
                "lexical aliases of one broken symbolic link produce one diagnostic",
                source,
                ["broken.json", "./broken.json", "nested/../broken.json", "broken.json"],
                1,
                ["INPUT_SYMLINK broken.json#"],
            )
        )
        return failures


def check_intermediate_directory_symlinks() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-intermediate-link-") as raw:
        source = Path(raw)
        _copy(
            FIXTURES / "templates" / "minimal-spec.json",
            source / "real-directory" / "item.json",
        )
        try:
            os.symlink("real-directory", source / "link-directory")
            os.symlink("absent-directory", source / "broken-directory")
        except (OSError, NotImplementedError) as error:
            return [f"intermediate directory symlinks are rejected: could not create links: {error}"]

        failures = _expect(
            "an explicit file reached through an intermediate directory symlink is rejected",
            source,
            ["link-directory/item.json"],
            1,
            ["INPUT_SYMLINK link-directory/item.json#"],
        )
        failures.extend(
            _expect(
                "an explicit file below a broken intermediate directory symlink is rejected",
                source,
                ["broken-directory/item.json"],
                1,
                ["INPUT_SYMLINK broken-directory/item.json#"],
            )
        )
        return failures


def check_discovered_symlink_overlap_deduplication() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-discovered-link-overlap-") as raw:
        source = Path(raw)
        _copy(
            FIXTURES / "templates" / "minimal-spec.json",
            source / "registry" / "nested" / "record.json",
        )
        try:
            os.symlink("record.json", source / "registry" / "nested" / "record-link.json")
        except (OSError, NotImplementedError) as error:
            return [f"overlapping symlink discovery is deduplicated: could not create link: {error}"]
        return _expect(
            "file/directory overlap emits one discovered symlink diagnostic",
            source,
            ["registry", "registry/nested"],
            1,
            ["INPUT_SYMLINK registry/nested/record-link.json#"],
        )


def check_multiple_empty_directory_order() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-empty-order-") as raw:
        source = Path(raw)
        for name in ("a-empty", "z-empty"):
            directory = source / name
            directory.mkdir()
            (directory / "README.txt").write_text("ignored\n", encoding="utf-8")
        expected = ["INPUT_EMPTY_SOURCE_SET a-empty#"]
        failures = _expect(
            "multiple empty directories select the smallest label (reverse argv)",
            source,
            ["z-empty", "a-empty"],
            1,
            expected,
        )
        failures.extend(
            _expect(
                "multiple empty directories select the smallest label (forward argv)",
                source,
                ["a-empty", "z-empty"],
                1,
                expected,
            )
        )
        return failures


def check_root_base_source_label() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-root-label-", dir="/tmp") as raw:
        source = Path(raw)
        invalid = source / "invalid.json"
        _copy(FIXTURES / "schema-invalid" / "kind-array.json", invalid)
        relative_label = invalid.as_posix().lstrip("/")
        return _expect(
            "an absolute source under root receives a relative POSIX label",
            Path("/"),
            [invalid.as_posix()],
            1,
            [f"SCHEMA_KIND_TYPE {relative_label}#/kind"],
        )


def check_double_leading_slash_alias() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-double-slash-", dir="/tmp") as raw:
        source = Path(raw)
        record = source / "record.json"
        _copy(FIXTURES / "templates" / "minimal-spec.json", record)
        ordinary = record.as_posix()
        double_slash = "//" + ordinary.lstrip("/")
        try:
            same_namespace = os.path.samefile(ordinary, double_slash)
        except OSError as error:
            return [f"double-leading-slash alias predicate failed: {error}"]
        if not same_namespace:
            # POSIX permits exactly two leading slashes to select a distinct
            # implementation-defined namespace. Such a platform has no alias
            # to deduplicate, so this Linux-tracer control is inapplicable.
            return []
        return _valid(
            "ordinary and exactly-double-leading-slash spellings are idempotent",
            source,
            [ordinary, double_slash],
        )


def check_directory_entry_classification_error() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-direntry-") as raw:
        source = Path(raw)
        registry = source / "registry"
        _copy(FIXTURES / "templates" / "minimal-spec.json", registry / "blocked.json")
        seam = source / "seam"
        seam.mkdir()
        (seam / "sitecustomize.py").write_text(
            """import os

_real_scandir = os.scandir
_target_directory = os.environ["SEMANTIC_LOADER_FAIL_DIRENTRY"]


class _FailingEntry:
    def __init__(self, entry):
        self._entry = entry
        self.name = entry.name
        self.path = entry.path

    def _raise(self):
        if self.name == "blocked.json":
            raise PermissionError("injected directory-entry classification failure")

    def is_symlink(self):
        self._raise()
        return self._entry.is_symlink()

    def is_dir(self, *, follow_symlinks=True):
        self._raise()
        return self._entry.is_dir(follow_symlinks=follow_symlinks)

    def is_file(self, *, follow_symlinks=True):
        self._raise()
        return self._entry.is_file(follow_symlinks=follow_symlinks)

    def stat(self, *, follow_symlinks=True):
        self._raise()
        return self._entry.stat(follow_symlinks=follow_symlinks)

    def __getattr__(self, name):
        return getattr(self._entry, name)


class _ScandirContext:
    def __init__(self, inner):
        self._inner = inner

    def __enter__(self):
        entries = self._inner.__enter__()
        return iter(_FailingEntry(entry) for entry in entries)

    def __exit__(self, exc_type, exc_value, traceback):
        return self._inner.__exit__(exc_type, exc_value, traceback)


def _scandir(path):
    inner = _real_scandir(path)
    if os.path.normpath(os.fspath(path)) == _target_directory:
        return _ScandirContext(inner)
    return inner


os.scandir = _scandir
""",
            encoding="utf-8",
        )
        inherited_pythonpath = os.environ.get("PYTHONPATH")
        pythonpath = str(seam)
        if inherited_pythonpath:
            pythonpath += os.pathsep + inherited_pythonpath
        return _expect(
            "a directory-entry classification error becomes one stable input diagnostic",
            source,
            ["registry"],
            1,
            ["INPUT_READ_ERROR registry/blocked.json#"],
            {
                "PYTHONPATH": pythonpath,
                "SEMANTIC_LOADER_FAIL_DIRENTRY": str(registry),
            },
        )


def check_explicit_special_file() -> list[str]:
    with tempfile.TemporaryDirectory(prefix="semantic-loader-special-") as raw:
        source = Path(raw)
        fifo = source / "pipe.json"
        if not hasattr(os, "mkfifo"):
            return ["an explicit special JSON path is rejected: os.mkfifo is unavailable"]
        try:
            os.mkfifo(fifo)
        except OSError as error:
            return [f"an explicit special JSON path is rejected: could not create FIFO: {error}"]
        return _expect(
            "an explicit FIFO receives an actionable unsupported-type diagnostic",
            source,
            ["pipe.json"],
            1,
            ["INPUT_UNSUPPORTED_TYPE pipe.json#"],
        )


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


def run_loader_fixture_checks() -> tuple[list[str], str]:
    checks = [
        check_alias_and_overlap,
        check_recursive_discovery_and_ignored_files,
        check_explicit_non_json,
        check_empty_source_set,
        check_symlink_rejection,
        check_unreadable_explicit_directory,
        check_failing_source_alias_deduplication,
        check_intermediate_directory_symlinks,
        check_discovered_symlink_overlap_deduplication,
        check_multiple_empty_directory_order,
        check_root_base_source_label,
        check_double_leading_slash_alias,
        check_directory_entry_classification_error,
        check_explicit_special_file,
        check_stable_source_order,
        check_distinct_file_duplicate_address,
        check_input_schema_phase_barrier,
        check_visible_import_edges,
    ]
    failures: list[str] = []
    for check in checks:
        failures.extend(check())
    return failures, "Loader fixture checks passed: 18 contract groups."


def main() -> int:
    failures, summary = run_loader_fixture_checks()
    if failures:
        print("Loader fixture checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
