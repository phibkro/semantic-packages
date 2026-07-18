from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
VALID_RECORDS = ROOT / "fixtures" / "records" / "valid"

try:
    finite_source = importlib.import_module("semantic_packages._finite_source")
    FINITE_SOURCE_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages._finite_source":
        raise
    finite_source = None
    FINITE_SOURCE_IMPORT_ERROR = error


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class FiniteSourceAvailabilityTest(unittest.TestCase):
    def test_internal_finite_source_module_is_the_only_red_predecessor(self) -> None:
        self.assertIsNotNone(
            finite_source,
            "J2-SF0 intentionally precedes semantic_packages/_finite_source.py; "
            f"observed {FINITE_SOURCE_IMPORT_ERROR!r}",
        )


@unittest.skipIf(
    finite_source is None,
    "J2-SF0 freezes the helper contract before _finite_source exists",
)
class FiniteSourceContractTest(unittest.TestCase):
    def _root(self, label: str, path: Path):
        return finite_source._SourceRoot(label, path)

    def _observe(self, *roots):
        return finite_source._observe_finite_source(tuple(roots))

    @staticmethod
    def _codes(observation) -> list[str]:
        return [diagnostic.code for diagnostic in observation.diagnostics]

    @staticmethod
    def _signatures(observation) -> list[str]:
        return [
            diagnostic.format().split(": ", 1)[0]
            for diagnostic in observation.diagnostics
        ]

    def test_labeled_roots_produce_exact_deterministic_immutable_records(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-roots-") as raw:
            base = Path(raw)
            theory = base / "theory"
            package = base / "package"
            theory.mkdir()
            package.mkdir()
            theory_path = theory / "z-spec.json"
            package_path = package / "a-profile.json"
            shutil.copyfile(VALID_RECORDS / "stack-spec.json", theory_path)
            shutil.copyfile(VALID_RECORDS / "stack-profile.json", package_path)

            observation = self._observe(
                self._root("theory", theory),
                self._root("package", package),
            )
            reversed_observation = self._observe(
                self._root("package", package),
                self._root("theory", theory),
            )

        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(observation, reversed_observation)
        self.assertIsInstance(observation.records, tuple)
        self.assertIsInstance(observation.diagnostics, tuple)
        self.assertEqual(
            ["package/a-profile.json", "theory/z-spec.json"],
            [record.path for record in observation.records],
        )
        expected = {
            "package/a-profile.json": (
                ("realizationProfile", "stack-default", "0.1.0"),
                "2a51ed7d2e1266376cd4a58ef3f20d30244655d25cb884816576be989014eddb",
            ),
            "theory/z-spec.json": (
                ("specification", "stack", "0.1.0"),
                "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1",
            ),
        }
        for record in observation.records:
            self.assertEqual(expected[record.path][0], record.address)
            self.assertEqual(expected[record.path][1], record.sha256)
            self.assertEqual(record.address[1], record.document["id"])
            self.assertFalse(hasattr(record, "role"))
            with self.assertRaises((AttributeError, TypeError)):
                record.path = "changed"

    def test_duplicate_and_overlapping_physical_sources_never_duplicate_records(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-alias-") as raw:
            base = Path(raw)
            nested = base / "nested"
            nested.mkdir()
            shutil.copyfile(VALID_RECORDS / "stack-spec.json", nested / "spec.json")

            repeated = self._observe(
                self._root("theory", base),
                self._root("theory", base / "."),
            )
            overlapping = self._observe(
                self._root("all", base),
                self._root("nested", nested),
            )
            reversed_overlapping = self._observe(
                self._root("nested", nested),
                self._root("all", base),
            )

        self.assertTrue(repeated.ok, repeated.diagnostics)
        self.assertEqual(1, len(repeated.records))
        self.assertEqual("theory/nested/spec.json", repeated.records[0].path)
        self.assertFalse(overlapping.ok)
        self.assertEqual(overlapping, reversed_overlapping)
        self.assertEqual(1, len(overlapping.records))
        self.assertEqual("all/nested/spec.json", overlapping.records[0].path)
        self.assertEqual(
            ["INPUT_SOURCE_ALIAS nested/spec.json#"],
            self._signatures(overlapping),
        )

    @unittest.skipUnless(
        sys.platform.startswith("linux"),
        "ADR 0007 collapses Linux double-leading-slash aliases",
    )
    def test_linux_double_leading_slash_is_an_idempotent_lexical_alias(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-double-slash-") as raw:
            source = Path(raw) / "theory"
            source.mkdir()
            shutil.copyfile(VALID_RECORDS / "stack-spec.json", source / "spec.json")
            ordinary = source.absolute()
            double_slash = Path("/" + ordinary.as_posix())
            self.assertTrue(str(double_slash).startswith("//"))

            observation = self._observe(
                self._root("theory", ordinary),
                self._root("theory", double_slash),
            )

        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(1, len(observation.records))
        self.assertEqual("theory/spec.json", observation.records[0].path)

    def test_distinct_files_with_one_canonical_address_are_both_observed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-address-duplicate-") as raw:
            source = Path(raw) / "theory"
            source.mkdir()
            shutil.copyfile(VALID_RECORDS / "stack-spec.json", source / "a.json")
            shutil.copyfile(VALID_RECORDS / "stack-spec.json", source / "b.json")

            observation = self._observe(self._root("theory", source))

        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(["theory/a.json", "theory/b.json"], [r.path for r in observation.records])
        self.assertEqual(
            [("specification", "stack", "0.1.0")] * 2,
            [record.address for record in observation.records],
        )

    def test_same_logical_path_from_distinct_roots_is_a_stable_collision(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-logical-collision-") as raw:
            base = Path(raw)
            left = base / "a-left"
            right = base / "b-right"
            left.mkdir()
            right.mkdir()
            left_record = json.loads(
                (VALID_RECORDS / "stack-spec.json").read_text(encoding="utf-8")
            )
            left_record["id"] = "stack-left"
            right_record = json.loads(
                (VALID_RECORDS / "stack-spec.json").read_text(encoding="utf-8")
            )
            right_record["id"] = "stack-right"
            _write_json(left / "spec.json", left_record)
            _write_json(right / "spec.json", right_record)

            observation = self._observe(
                self._root("theory", right),
                self._root("theory", left),
            )
            reversed_observation = self._observe(
                self._root("theory", left),
                self._root("theory", right),
            )

        self.assertEqual(observation, reversed_observation)
        self.assertFalse(observation.ok)
        self.assertEqual(1, len(observation.records))
        self.assertEqual(
            ("specification", "stack-left", "0.1.0"),
            observation.records[0].address,
        )
        self.assertEqual(
            ["INPUT_LOGICAL_PATH_COLLISION theory/spec.json#"],
            self._signatures(observation),
        )

    def test_no_roots_and_empty_labeled_roots_fail_deterministically(self) -> None:
        no_roots = self._observe()
        self.assertFalse(no_roots.ok)
        self.assertEqual(
            ["INPUT_EMPTY_SOURCE_SET .#"],
            self._signatures(no_roots),
        )

        with tempfile.TemporaryDirectory(prefix="j2-empty-root-") as raw:
            empty = Path(raw) / "empty"
            empty.mkdir()
            observation = self._observe(self._root("theory", empty))

        self.assertFalse(observation.ok)
        self.assertEqual(
            ["INPUT_EMPTY_SOURCE_SET theory#"],
            self._signatures(observation),
        )

    def test_input_and_schema_failures_form_a_downstream_phase_barrier(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-phase-") as raw:
            source = Path(raw) / "theory"
            source.mkdir()
            (source / "a-malformed.json").write_text(
                "{ malformed\n", encoding="utf-8"
            )
            invalid = json.loads(
                (VALID_RECORDS / "stack-spec.json").read_text(encoding="utf-8")
            )
            invalid["kind"] = ["specification"]
            _write_json(source / "b-schema-invalid.json", invalid)
            shutil.copyfile(
                VALID_RECORDS / "stack-rust-realization.json",
                source / "c-dangling-but-schema-valid.json",
            )

            observation = self._observe(self._root("theory", source))

        self.assertFalse(observation.ok)
        self.assertEqual(
            [
                "INPUT_INVALID_JSON theory/a-malformed.json#",
                "SCHEMA_KIND_TYPE theory/b-schema-invalid.json#/kind",
            ],
            self._signatures(observation),
        )
        self.assertFalse(any(code.startswith("LINK_") for code in self._codes(observation)))
        self.assertFalse(any(code.startswith("PUBLICATION_") for code in self._codes(observation)))
        self.assertFalse(any(code.startswith("REGISTRATION_") for code in self._codes(observation)))

    def test_root_leaf_known_nested_and_unknown_symlinks_are_never_followed(self) -> None:
        attacks = ("root", "leaf", "known-directory", "nested-directory", "unknown-directory")
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory(
                prefix=f"j2-source-symlink-{attack}-"
            ) as raw:
                base = Path(raw)
                source = base / "source"
                source.mkdir()
                records = source / "records"
                records.mkdir()
                shutil.copyfile(VALID_RECORDS / "stack-spec.json", records / "spec.json")
                outside = base / f"outside-{attack}"

                if attack == "root":
                    alias = base / "alias"
                    alias.symlink_to(source, target_is_directory=True)
                    observed_root = alias
                    expected = "INPUT_SYMLINK theory#"
                elif attack == "leaf":
                    leaf = records / "spec.json"
                    leaf.unlink()
                    leaf.symlink_to(VALID_RECORDS / "stack-spec.json")
                    observed_root = source
                    expected = "INPUT_SYMLINK theory/records/spec.json#"
                elif attack == "known-directory":
                    records.rename(outside)
                    records.symlink_to(outside, target_is_directory=True)
                    observed_root = source
                    expected = "INPUT_SYMLINK theory/records#"
                else:
                    outside.mkdir()
                    shutil.copyfile(
                        VALID_RECORDS / "stack-profile.json",
                        outside / "hidden.json",
                    )
                    if attack == "nested-directory":
                        target = records / "hidden"
                        expected = "INPUT_SYMLINK theory/records/hidden#"
                    else:
                        target = source / "unknown"
                        expected = "INPUT_SYMLINK theory/unknown#"
                    target.symlink_to(outside, target_is_directory=True)
                    observed_root = source

                observation = self._observe(self._root("theory", observed_root))

                self.assertFalse(observation.ok)
                self.assertEqual([expected], self._signatures(observation))
                self.assertFalse(
                    any(record.path.endswith("hidden.json") for record in observation.records)
                )

    def test_symlinked_ancestor_is_rejected_before_requested_or_target_io(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-ancestor-symlink-") as raw:
            base = Path(raw)
            outside = base / "outside"
            target_root = outside / "records"
            target_root.mkdir(parents=True)
            target_record = target_root / "spec.json"
            shutil.copyfile(VALID_RECORDS / "stack-spec.json", target_record)
            ancestor_link = base / "ancestor-link"
            ancestor_link.symlink_to(outside, target_is_directory=True)
            requested_root = ancestor_link / "records"
            linked_record = requested_root / "spec.json"

            real_lstat = os.lstat
            real_stat = os.stat
            real_scandir = os.scandir
            real_path_open = Path.open
            forbidden = {
                requested_root,
                linked_record,
                target_root,
                target_record,
            }
            touched: list[tuple[str, Path]] = []

            def reject_forbidden(operation: str, path):
                candidate = Path(path)
                if candidate in forbidden:
                    touched.append((operation, candidate))
                    raise AssertionError(
                        f"{operation} touched requested or resolved symlink target {candidate}"
                    )
                return candidate

            def guarded_lstat(path, *args, **kwargs):
                reject_forbidden("lstat", path)
                return real_lstat(path, *args, **kwargs)

            def guarded_stat(path, *args, **kwargs):
                reject_forbidden("stat", path)
                return real_stat(path, *args, **kwargs)

            def guarded_scandir(path):
                reject_forbidden("scandir", path)
                return real_scandir(path)

            def guarded_open(path, *args, **kwargs):
                reject_forbidden("open", path)
                return real_path_open(path, *args, **kwargs)

            with mock.patch.object(os, "lstat", side_effect=guarded_lstat), mock.patch.object(
                os, "stat", side_effect=guarded_stat
            ), mock.patch.object(
                os, "scandir", side_effect=guarded_scandir
            ), mock.patch.object(
                Path, "open", autospec=True, side_effect=guarded_open
            ):
                observation = self._observe(
                    self._root("theory", requested_root)
                )

        self.assertEqual([], touched)
        self.assertFalse(observation.ok)
        self.assertEqual(
            ["INPUT_SYMLINK theory#"],
            self._signatures(observation),
        )
        self.assertEqual((), observation.records)

    def test_symlink_entries_are_classified_without_target_scandir_or_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-symlink-instrument-") as raw:
            base = Path(raw)
            source = base / "source"
            source.mkdir()
            outside_directory = base / "outside-directory"
            outside_directory.mkdir()
            shutil.copyfile(
                VALID_RECORDS / "stack-profile.json",
                outside_directory / "hidden.json",
            )
            directory_link = source / "hidden-directory"
            directory_link.symlink_to(outside_directory, target_is_directory=True)
            leaf_link = source / "hidden-leaf.json"
            leaf_link.symlink_to(VALID_RECORDS / "stack-spec.json")
            real_scandir = os.scandir
            real_path_open = Path.open
            scanned: list[Path] = []
            opened: list[Path] = []

            def guarded_scandir(path):
                candidate = Path(path)
                scanned.append(candidate)
                if candidate in (directory_link, outside_directory):
                    raise AssertionError(
                        f"symlinked directory or resolved target was traversed: {candidate}"
                    )
                return real_scandir(path)

            def guarded_open(path, *args, **kwargs):
                candidate = Path(path)
                opened.append(candidate)
                if candidate in (leaf_link, VALID_RECORDS / "stack-spec.json"):
                    raise AssertionError(
                        f"symlinked record or resolved target was read: {candidate}"
                    )
                return real_path_open(path, *args, **kwargs)

            with mock.patch.object(os, "scandir", side_effect=guarded_scandir), mock.patch.object(
                Path, "open", autospec=True, side_effect=guarded_open
            ):
                observation = self._observe(self._root("theory", source))

        self.assertFalse(observation.ok)
        self.assertEqual(
            [
                "INPUT_SYMLINK theory/hidden-directory#",
                "INPUT_SYMLINK theory/hidden-leaf.json#",
            ],
            self._signatures(observation),
        )
        self.assertNotIn(directory_link, scanned)
        self.assertNotIn(outside_directory, scanned)
        self.assertNotIn(leaf_link, opened)
        self.assertNotIn(VALID_RECORDS / "stack-spec.json", opened)

    def test_read_and_scandir_errors_are_total_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-errors-") as raw:
            source = Path(raw) / "theory"
            source.mkdir()
            blocked = source / "blocked"
            blocked.mkdir()
            (source / "invalid-utf8.json").write_bytes(b"\xff\xfe")
            real_scandir = os.scandir

            def guarded_scandir(path):
                if Path(path) == blocked:
                    raise PermissionError("bounded scandir denial")
                return real_scandir(path)

            with mock.patch.object(os, "scandir", side_effect=guarded_scandir):
                observation = self._observe(self._root("theory", source))

        self.assertFalse(observation.ok)
        self.assertEqual(
            [
                "INPUT_READ_ERROR theory/blocked#",
                "INPUT_READ_ERROR theory/invalid-utf8.json#",
            ],
            self._signatures(observation),
        )

    @unittest.skipUnless(
        sys.platform.startswith("linux") and Path("/dev/null").exists(),
        "predecessor special-root diagnostic is frozen on the Linux boundary",
    )
    def test_special_root_retains_predecessor_unsupported_type_diagnostic(self) -> None:
        observation = self._observe(
            self._root("", Path("/dev/null"))
        )

        self.assertFalse(observation.ok)
        self.assertEqual((), observation.records)
        self.assertEqual(
            [
                "INPUT_UNSUPPORTED_TYPE .#: "
                "not a regular file or directory: /dev/null"
            ],
            [diagnostic.format() for diagnostic in observation.diagnostics],
        )

    def test_ordinary_rename_changes_only_logical_path_and_preserves_exact_hash(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-rename-") as raw:
            source = Path(raw) / "theory"
            source.mkdir()
            original = source / "stack-spec.json"
            renamed = source / "meaning.json"
            shutil.copyfile(VALID_RECORDS / "stack-spec.json", original)
            before = self._observe(self._root("theory", source))
            original.rename(renamed)
            after = self._observe(self._root("theory", source))

        self.assertTrue(before.ok)
        self.assertTrue(after.ok)
        self.assertEqual(before.records[0].address, after.records[0].address)
        self.assertEqual(before.records[0].sha256, after.records[0].sha256)
        self.assertEqual("theory/stack-spec.json", before.records[0].path)
        self.assertEqual("theory/meaning.json", after.records[0].path)

    def test_hash_is_over_exact_raw_bytes_not_a_normalized_json_document(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-raw-hash-") as raw:
            source = Path(raw) / "theory"
            source.mkdir()
            document = json.loads(
                (VALID_RECORDS / "stack-spec.json").read_text(encoding="utf-8")
            )
            reformatted = (
                " \n" + json.dumps(document, separators=(",", ":")) + "\n\n"
            ).encode("utf-8")
            path = source / "reformatted.json"
            path.write_bytes(reformatted)

            observation = self._observe(self._root("theory", source))

        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(1, len(observation.records))
        self.assertEqual(
            hashlib.sha256(reformatted).hexdigest(),
            observation.records[0].sha256,
        )
        self.assertNotEqual(
            hashlib.sha256(
                (VALID_RECORDS / "stack-spec.json").read_bytes()
            ).hexdigest(),
            observation.records[0].sha256,
        )

    def test_observed_document_is_a_snapshot_and_inspection_does_not_mutate_sources(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-snapshot-") as raw:
            source = Path(raw) / "theory"
            source.mkdir()
            path = source / "spec.json"
            shutil.copyfile(VALID_RECORDS / "stack-spec.json", path)
            source_bytes = path.read_bytes()

            observation = self._observe(self._root("theory", source))
            record = observation.records[0]
            self.assertEqual(source_bytes, path.read_bytes())
            document_snapshot = record.document
            exposed = record.document
            try:
                exposed["id"] = "mutated-view"
            except (AttributeError, TypeError):
                pass
            self.assertEqual("stack", record.document["id"])
            nested_statement = record.document["laws"][0]["statement"]
            nested_exposed = record.document
            try:
                nested_exposed["laws"][0]["statement"] = "mutated nested view"
            except (AttributeError, TypeError):
                pass
            self.assertEqual(
                nested_statement,
                record.document["laws"][0]["statement"],
            )
            path.write_text("{ later mutation\n", encoding="utf-8")

            self.assertEqual(document_snapshot, record.document)
            self.assertEqual("stack", record.document["id"])
            with self.assertRaises((AttributeError, TypeError)):
                record.document = {"id": "replacement"}
            self.assertEqual(
                hashlib.sha256(source_bytes).hexdigest(),
                record.sha256,
            )
            self.assertEqual(("specification", "stack", "0.1.0"), record.address)

            path.write_bytes(source_bytes)
            self.assertEqual(source_bytes, path.read_bytes())

    def test_helper_applies_no_stack_allowlist_role_graph_or_assurance_policy(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-policy-") as raw:
            source = Path(raw) / "candidate"
            source.mkdir()
            shutil.copyfile(
                VALID_RECORDS / "stack-rust-realization.json",
                source / "unresolved-realization.json",
            )

            observation = self._observe(self._root("candidate", source))

        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(1, len(observation.records))
        record = observation.records[0]
        self.assertEqual(("realization", "stack-rust", "0.1.0"), record.address)
        self.assertFalse(hasattr(record, "role"))
        for policy_field in (
            "package",
            "publication",
            "assurance",
            "accepted",
            "unexpected_addresses",
        ):
            self.assertFalse(hasattr(observation, policy_field))

    def test_observation_executes_no_document_entrypoint_or_process_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-no-exec-") as raw:
            source = Path(raw) / "candidate"
            source.mkdir()
            marker = Path(raw) / "execution-marker"
            executable = Path(raw) / "entrypoint"
            executable.write_text(
                f"#!/bin/sh\ntouch {marker}\nexit 1\n", encoding="utf-8"
            )
            executable.chmod(0o755)
            realization = json.loads(
                (VALID_RECORDS / "stack-rust-realization.json").read_text(
                    encoding="utf-8"
                )
            )
            realization["adapter"]["entrypoint"] = str(executable)
            realization["implementation"]["executionInstructions"] = str(executable)
            _write_json(source / "realization.json", realization)
            before = (source / "realization.json").read_bytes()
            launches: list[str] = []

            def reject_launch(name: str):
                def reject(*_args, **_kwargs):
                    launches.append(name)
                    raise AssertionError(f"finite-source observation launched {name}")

                return reject

            boundaries = [
                (subprocess, "run"),
                (subprocess, "Popen"),
                (os, "system"),
                (os, "posix_spawn"),
                (os, "posix_spawnp"),
                (os, "spawnv"),
                (os, "spawnve"),
                (os, "spawnvp"),
                (os, "spawnvpe"),
            ]
            with ExitStack() as stack:
                for owner, name in boundaries:
                    if hasattr(owner, name):
                        stack.enter_context(
                            mock.patch.object(owner, name, side_effect=reject_launch(name))
                        )
                for name in ("run", "Popen", "system"):
                    if hasattr(finite_source, name):
                        stack.enter_context(
                            mock.patch.object(
                                finite_source,
                                name,
                                side_effect=reject_launch(f"finite_source.{name}"),
                            )
                        )
                observation = self._observe(self._root("candidate", source))

            self.assertFalse(marker.exists())
            self.assertEqual([], launches)
            self.assertEqual(before, (source / "realization.json").read_bytes())

        self.assertTrue(observation.ok, observation.diagnostics)

    def test_unchanged_canonical_realization_executes_no_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-source-canonical-no-exec-") as raw:
            source = Path(raw) / "candidate"
            source.mkdir()
            shutil.copyfile(
                VALID_RECORDS / "stack-rust-realization.json",
                source / "realization.json",
            )
            launches: list[str] = []

            def reject_launch(name: str):
                def reject(*_args, **_kwargs):
                    launches.append(name)
                    raise AssertionError(
                        f"finite-source observation launched canonical {name}"
                    )

                return reject

            boundaries = [
                (subprocess, "run"),
                (subprocess, "Popen"),
                (os, "system"),
                (os, "posix_spawn"),
                (os, "posix_spawnp"),
                (os, "spawnv"),
                (os, "spawnve"),
                (os, "spawnvp"),
                (os, "spawnvpe"),
            ]
            with ExitStack() as stack:
                for owner, name in boundaries:
                    if hasattr(owner, name):
                        stack.enter_context(
                            mock.patch.object(owner, name, side_effect=reject_launch(name))
                        )
                for name in ("run", "Popen", "system"):
                    if hasattr(finite_source, name):
                        stack.enter_context(
                            mock.patch.object(
                                finite_source,
                                name,
                                side_effect=reject_launch(f"finite_source.{name}"),
                            )
                        )
                observation = self._observe(self._root("candidate", source))

        self.assertEqual([], launches)
        self.assertTrue(observation.ok, observation.diagnostics)


if __name__ == "__main__":
    unittest.main()
