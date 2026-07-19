from __future__ import annotations

import builtins
import importlib
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from semantic_packages import _finite_source, graph


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts" / "ordered-map" / "theory-source-contract.json"
MANIFEST = ROOT / "registry" / "ordered-map" / "theory-manifest.json"
SPECIFICATION = ("specification", "ordered-map", "0.1.0")
PROFILE = ("realizationProfile", "ordered-map-ascii-fold", "0.1.0")
CONTRACT_SHA256 = "1ec7d9f0ec74af8afff2823b89e7039a910fbde28fd86b9dd60f499948b25a6b"
MANIFEST_SHA256 = "06157079396b8712e31eaf459949c0503eb8d68ac7b6c97ac0b1308cc7f523c7"
SPECIFICATION_SHA256 = "6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f"
PROFILE_SHA256 = "6d1297892c355a569e244c2b94448a5f5edaf9b1bf2ae54f940d7c4494fe225f"

EXPECTED_DECLARATIONS = {
    ("carrier", "Key"),
    ("carrier", "Value"),
    ("carrier", "OrderedMap"),
    ("operation", "empty"),
    ("operation", "put"),
    ("observation", "lookup"),
    ("observation", "entries"),
    ("equivalence", "key-equivalence"),
    ("equivalence", "value-equivalence"),
    ("equivalence", "ordered-map-equivalence"),
    ("law", "lookup-empty"),
    ("law", "lookup-put-same"),
    ("law", "lookup-put-other"),
    ("law", "put-existing-position"),
    ("law", "put-new-appends"),
    ("effect", "ordered-map-effects"),
    ("resource", "persistence"),
    ("performance", "put-amortized-constant"),
}

try:
    theory_source = importlib.import_module(
        "semantic_packages.ordered_map_theory_source"
    )
    THEORY_SOURCE_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.ordered_map_theory_source":
        raise
    theory_source = None
    THEORY_SOURCE_IMPORT_ERROR = error


def _write_json(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _canonical_sha256(document: dict) -> str:
    encoded = json.dumps(
        document, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OrderedMapTheorySourcePreconditionTest(unittest.TestCase):
    def test_reviewed_authority_artifacts_precede_the_actor_wrapper(self) -> None:
        self.assertTrue(CONTRACT.is_file())
        self.assertTrue(MANIFEST.is_file())
        self.assertEqual(
            {SPECIFICATION, PROFILE},
            {member.address for member in graph.inspect_manifest_authority(MANIFEST).members},
        )

    def test_theory_source_module_is_the_only_red_predecessor(self) -> None:
        self.assertIsNotNone(
            theory_source,
            "O5b intentionally precedes ordered_map_theory_source.py; "
            f"observed {THEORY_SOURCE_IMPORT_ERROR!r}",
        )


@unittest.skipIf(
    theory_source is None,
    "O5b freezes the provisional actor boundary before O5c implementation",
)
class OrderedMapTheorySourceContractTest(unittest.TestCase):
    @staticmethod
    def _copy_repository_slice(raw: str) -> Path:
        root = Path(raw) / "repository"
        shutil.copytree(ROOT / "contracts", root / "contracts")
        shutil.copytree(ROOT / "schemas", root / "schemas")
        shutil.copytree(ROOT / "registry" / "ordered-map", root / "registry" / "ordered-map")
        return root

    @staticmethod
    def _inspect_at(root: Path):
        with mock.patch.object(theory_source, "_ROOT", root):
            return theory_source.inspect_theory_source()

    def test_zero_argument_wrapper_surfaces_exact_provisional_authority(self) -> None:
        self.assertEqual(
            (), tuple(inspect.signature(theory_source.inspect_theory_source).parameters)
        )
        result = theory_source.inspect_theory_source()

        self.assertTrue(result.ok, result.diagnostics)
        authority = result.authority
        self.assertEqual("ordered-map-theory-source-contract", authority.contract_id)
        self.assertEqual("0.1.0", authority.contract_version)
        self.assertEqual("provisional-theory-source", authority.authority_class)
        self.assertFalse(authority.final_product_authority)
        self.assertEqual(CONTRACT_SHA256, authority.contract_canonical_sha256)
        self.assertEqual(MANIFEST_SHA256, authority.manifest_raw_sha256)
        self.assertEqual("ordered-map-theory", authority.source)
        for name in ("product_contract", "accepted", "assurance", "semantic_status"):
            self.assertFalse(hasattr(result, name))
            self.assertFalse(hasattr(authority, name))

        attacks = (
            lambda: theory_source.inspect_theory_source(CONTRACT),
            lambda: theory_source.inspect_theory_source(contract=object()),
            lambda: theory_source.inspect_theory_source(manifest=MANIFEST),
            lambda: theory_source.inspect_theory_source(root=ROOT),
            lambda: theory_source.inspect_theory_source(configuration=object()),
        )
        for attack in attacks:
            with self.assertRaises(TypeError):
                attack()

    def test_publication_and_graph_are_exact_views_of_one_snapshot(self) -> None:
        result = theory_source.inspect_theory_source()
        self.assertTrue(result.ok, result.diagnostics)

        self.assertEqual(
            [
                (
                    PROFILE,
                    "dependencies/ordered-map-profile.json",
                    PROFILE_SHA256,
                    "dependency",
                ),
                (
                    SPECIFICATION,
                    "records/ordered-map-spec.json",
                    SPECIFICATION_SHA256,
                    "authored",
                ),
            ],
            [
                (record.address, record.path, record.sha256, record.role)
                for record in result.publication.records
            ],
        )
        self.assertEqual(
            [
                (
                    PROFILE,
                    "ordered-map-theory/dependencies/ordered-map-profile.json",
                    PROFILE_SHA256,
                    "dependency",
                    "ordered-map-theory",
                ),
                (
                    SPECIFICATION,
                    "ordered-map-theory/records/ordered-map-spec.json",
                    SPECIFICATION_SHA256,
                    "theory-authored",
                    "ordered-map-theory",
                ),
            ],
            [
                (
                    record.address,
                    record.path,
                    record.sha256,
                    record.role,
                    record.source,
                )
                for record in result.graph.records
            ],
        )
        self.assertEqual(
            [(record.address, record.sha256) for record in result.publication.records],
            [(record.address, record.sha256) for record in result.graph.records],
        )

    def test_theory_projection_exposes_all_meaning_as_unclaimed(self) -> None:
        result = theory_source.inspect_theory_source()
        self.assertTrue(result.ok, result.diagnostics)
        view = result.theory

        self.assertEqual(SPECIFICATION, view.specification)
        self.assertEqual((), view.imports)
        self.assertEqual((), view.contradictions)
        self.assertEqual(
            EXPECTED_DECLARATIONS,
            {(item.kind, item.declaration_id) for item in view.declarations},
        )
        self.assertEqual(EXPECTED_DECLARATIONS, set(view.unknowns))
        self.assertTrue(
            all(item.observation == "unclaimed" and not item.claims for item in view.declarations)
        )
        performance = next(
            item
            for item in view.declarations
            if (item.kind, item.declaration_id)
            == ("performance", "put-amortized-constant")
        )
        self.assertEqual("unclaimed", performance.observation)

    def test_success_uses_one_source_capture_without_manifest_reread_or_execution(self) -> None:
        original = _finite_source._observe_finite_source
        original_open = os.open
        original_close = os.close
        original_builtin_open = builtins.open
        original_path_open = Path.open
        original_read_text = Path.read_text
        original_read_bytes = Path.read_bytes
        captures = []
        manifest_reads = []
        manifest_descriptors = set()
        launches = []

        def observe(*args, **kwargs):
            captures.append(args[0])
            return original(*args, **kwargs)

        def reject(name):
            def fail(*_args, **_kwargs):
                launches.append(name)
                raise AssertionError(f"theory source attempted {name}")

            return fail

        with tempfile.TemporaryDirectory(prefix="o5-detached-manifest-") as raw:
            root = self._copy_repository_slice(raw)
            manifest_path = root / "registry" / "ordered-map" / MANIFEST.name
            manifest_absolute = manifest_path.resolve()

            def is_manifest_path(path) -> bool:
                return not isinstance(path, int) and Path(path).resolve() == manifest_absolute

            def reject_manifest_builtin_open(path, *args, **kwargs):
                if is_manifest_path(path):
                    raise AssertionError("manifest bypassed authenticated descriptor capture")
                return original_builtin_open(path, *args, **kwargs)

            def reject_manifest_path_open(path, *args, **kwargs):
                if is_manifest_path(path):
                    raise AssertionError("manifest bypassed authenticated descriptor capture")
                return original_path_open(path, *args, **kwargs)

            def reject_manifest_read_text(path, *args, **kwargs):
                if is_manifest_path(path):
                    raise AssertionError("manifest bypassed authenticated descriptor capture")
                return original_read_text(path, *args, **kwargs)

            def reject_manifest_read_bytes(path, *args, **kwargs):
                if is_manifest_path(path):
                    raise AssertionError("manifest bypassed authenticated descriptor capture")
                return original_read_bytes(path, *args, **kwargs)

            def tracked_open(path, flags, *args, **kwargs):
                descriptor = original_open(path, flags, *args, **kwargs)
                if Path(path).resolve() == manifest_absolute:
                    manifest_reads.append(manifest_absolute)
                    manifest_descriptors.add(descriptor)
                return descriptor

            def tracked_close(descriptor):
                original_close(descriptor)
                if descriptor in manifest_descriptors:
                    manifest_descriptors.remove(descriptor)
                    with original_path_open(manifest_path, "w", encoding="utf-8") as stream:
                        stream.write("{}\n")

            with ExitStack() as stack:
                stack.enter_context(mock.patch.object(theory_source, "_ROOT", root))
                stack.enter_context(
                    mock.patch.object(
                        _finite_source, "_observe_finite_source", side_effect=observe
                    )
                )
                stack.enter_context(mock.patch.object(os, "open", side_effect=tracked_open))
                stack.enter_context(mock.patch.object(os, "close", side_effect=tracked_close))
                stack.enter_context(
                    mock.patch.object(
                        builtins, "open", side_effect=reject_manifest_builtin_open
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        Path,
                        "open",
                        autospec=True,
                        side_effect=reject_manifest_path_open,
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        Path,
                        "read_text",
                        autospec=True,
                        side_effect=reject_manifest_read_text,
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        Path,
                        "read_bytes",
                        autospec=True,
                        side_effect=reject_manifest_read_bytes,
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        graph,
                        "_load_manifest",
                        side_effect=AssertionError("authenticated manifest was reread"),
                    )
                )
                for owner, name in (
                    (subprocess, "run"),
                    (subprocess, "Popen"),
                    (os, "system"),
                    (os, "posix_spawn"),
                    (os, "posix_spawnp"),
                ):
                    stack.enter_context(
                        mock.patch.object(owner, name, side_effect=reject(name))
                    )
                result = theory_source.inspect_theory_source()

        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual([manifest_absolute], manifest_reads)
        self.assertEqual(1, len(captures))
        self.assertEqual(1, len(captures[0]))
        self.assertEqual("ordered-map-theory", captures[0][0].label)
        self.assertEqual(
            (root / "registry" / "ordered-map" / "theory").resolve(),
            captures[0][0].path.resolve(),
        )
        self.assertEqual([], launches)

    def test_contract_and_manifest_failures_stop_before_source_observation(self) -> None:
        failures = {}
        locations = {}
        with tempfile.TemporaryDirectory(prefix="o5-authority-phase-") as raw:
            root = self._copy_repository_slice(raw)
            contract_path = root / "contracts" / "ordered-map" / CONTRACT.name
            locations["contract-digest"] = os.fspath(contract_path)
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["manifest"]["rawSha256"] = "0" * 64
            _write_json(contract_path, contract)
            observed_contract_sha256 = _canonical_sha256(contract)
            with mock.patch.object(
                _finite_source,
                "_observe_finite_source",
                side_effect=AssertionError("contract failure observed source roots"),
            ):
                failures["contract-digest"] = self._inspect_at(root)

        with tempfile.TemporaryDirectory(prefix="o5-contract-schema-") as raw:
            root = self._copy_repository_slice(raw)
            contract_path = root / "contracts" / "ordered-map" / CONTRACT.name
            locations["contract-schema"] = os.fspath(contract_path)
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["finalProductAuthority"] = True
            _write_json(contract_path, contract)
            with mock.patch.object(
                _finite_source,
                "_observe_finite_source",
                side_effect=AssertionError("contract schema failure observed roots"),
            ):
                failures["contract-schema"] = self._inspect_at(root)

        with tempfile.TemporaryDirectory(prefix="o5-manifest-phase-") as raw:
            root = self._copy_repository_slice(raw)
            manifest_path = root / "registry" / "ordered-map" / MANIFEST.name
            locations["manifest-digest"] = os.fspath(manifest_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["members"] = list(reversed(manifest["members"]))
            _write_json(manifest_path, manifest)
            observed_manifest_sha256 = _raw_sha256(manifest_path)
            with mock.patch.object(
                _finite_source,
                "_observe_finite_source",
                side_effect=AssertionError("manifest failure observed source roots"),
            ):
                failures["manifest-digest"] = self._inspect_at(root)

        with tempfile.TemporaryDirectory(prefix="o5-manifest-schema-") as raw:
            root = self._copy_repository_slice(raw)
            manifest_path = root / "registry" / "ordered-map" / MANIFEST.name
            locations["manifest-schema"] = os.fspath(manifest_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["formatVersion"] = 2
            _write_json(manifest_path, manifest)
            with mock.patch.object(
                _finite_source,
                "_observe_finite_source",
                side_effect=AssertionError("manifest schema failure observed roots"),
            ):
                failures["manifest-schema"] = self._inspect_at(root)

        symlink_cases = (
            (
                "contract-schema-leaf",
                Path("schemas/ordered-map-theory-source-contract.schema.json"),
                False,
            ),
            ("contract-schema-ancestor", Path("schemas"), True),
            ("manifest-leaf", Path("registry/ordered-map/theory-manifest.json"), False),
            ("manifest-ancestor", Path("registry/ordered-map"), True),
            ("manifest-schema-leaf", Path("schemas/registry-manifest.schema.json"), False),
        )
        for name, relative, directory in symlink_cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix=f"o5-{name}-"
            ) as raw:
                root = self._copy_repository_slice(raw)
                target = root / relative
                outside = Path(raw) / f"outside-{name}"
                target.rename(outside)
                target.symlink_to(outside, target_is_directory=directory)
                locations[name] = os.fspath(target)
                with mock.patch.object(
                    _finite_source,
                    "_observe_finite_source",
                    side_effect=AssertionError(f"{name} observed roots"),
                ):
                    failures[name] = self._inspect_at(root)

        self.assertEqual(
            ["ARTIFACT_CANONICAL_DIGEST_MISMATCH"],
            [item.code for item in failures["contract-digest"].diagnostics],
        )
        self.assertEqual(
            ["ARTIFACT_RAW_DIGEST_MISMATCH"],
            [item.code for item in failures["manifest-digest"].diagnostics],
        )
        self.assertEqual(
            [
                (
                    "ARTIFACT_SCHEMA_INVALID",
                    locations["contract-schema"],
                    "/finalProductAuthority",
                )
            ],
            [
                (item.code, item.path, item.pointer)
                for item in failures["contract-schema"].diagnostics
            ],
        )
        self.assertEqual(
            [
                (
                    "ARTIFACT_SCHEMA_INVALID",
                    locations["manifest-schema"],
                    "/formatVersion",
                )
            ],
            [
                (item.code, item.path, item.pointer)
                for item in failures["manifest-schema"].diagnostics
            ],
        )
        self.assertEqual(locations["contract-digest"], failures["contract-digest"].diagnostics[0].path)
        self.assertEqual("#", failures["contract-digest"].diagnostics[0].pointer)
        self.assertEqual(
            f"canonical SHA-256 {observed_contract_sha256}, expected {CONTRACT_SHA256}",
            failures["contract-digest"].diagnostics[0].message,
        )
        self.assertEqual(locations["manifest-digest"], failures["manifest-digest"].diagnostics[0].path)
        self.assertEqual("#", failures["manifest-digest"].diagnostics[0].pointer)
        self.assertEqual(
            f"raw SHA-256 {observed_manifest_sha256}, expected {MANIFEST_SHA256}",
            failures["manifest-digest"].diagnostics[0].message,
        )
        for name, _relative, _directory in symlink_cases:
            self.assertEqual(
                [("INPUT_SYMLINK", locations[name], "#")],
                [
                    (item.code, item.path, item.pointer)
                    for item in failures[name].diagnostics
                ],
            )
        for result in failures.values():
            self.assertFalse(result.ok)
            self.assertIsNone(result.authority)
            self.assertIsNone(result.publication)
            self.assertIsNone(result.graph)
            self.assertIsNone(result.theory)

    def test_record_membership_digest_and_version_attacks_fail_before_projection(self) -> None:
        observations = {}
        expected_messages = {
            "missing": "manifest requires (specification, ordered-map, 0.1.0)",
            "unexpected": "manifest does not include (realizationProfile, ordered-map-extra, 0.1.0) in source 'ordered-map-theory'",
        }
        for attack in ("missing", "unexpected", "digest", "version", "schema", "link"):
            with self.subTest(attack=attack), tempfile.TemporaryDirectory(
                prefix=f"o5-record-{attack}-"
            ) as raw:
                root = self._copy_repository_slice(raw)
                theory = root / "registry" / "ordered-map" / "theory"
                spec = theory / "records" / "ordered-map-spec.json"
                if attack == "missing":
                    spec.unlink()
                elif attack == "unexpected":
                    profile = json.loads(
                        (theory / "dependencies" / "ordered-map-profile.json").read_text(
                            encoding="utf-8"
                        )
                    )
                    profile["id"] = "ordered-map-extra"
                    _write_json(theory / "dependencies" / "extra-profile.json", profile)
                else:
                    document = json.loads(spec.read_text(encoding="utf-8"))
                    if attack == "digest":
                        document["carriers"][0]["description"] += " Drift."
                    elif attack == "version":
                        document["version"] = "0.1.1"
                    elif attack == "schema":
                        document["laws"][0].pop("id")
                    else:
                        document["performancePropositions"][0]["workload"][
                            "localId"
                        ] = "absent-workload"
                    _write_json(spec, document)
                    if attack == "digest":
                        expected_messages["digest"] = (
                            f"record has SHA-256 {_raw_sha256(spec)}, expected "
                            f"{SPECIFICATION_SHA256}"
                        )
                observations[attack] = self._inspect_at(root)

        self.assertEqual(
            [("GRAPH_MISSING_MEMBER", "ordered-map-theory", "#")],
            [
                (item.code, item.path, item.pointer)
                for item in observations["missing"].diagnostics
            ],
        )
        self.assertEqual(
            [
                (
                    "GRAPH_UNEXPECTED_MEMBER",
                    "ordered-map-theory/dependencies/extra-profile.json",
                    "#",
                )
            ],
            [
                (item.code, item.path, item.pointer)
                for item in observations["unexpected"].diagnostics
            ],
        )
        self.assertEqual(
            [
                (
                    "GRAPH_DIGEST_MISMATCH",
                    "ordered-map-theory/records/ordered-map-spec.json",
                    "#",
                )
            ],
            [
                (item.code, item.path, item.pointer)
                for item in observations["digest"].diagnostics
            ],
        )
        self.assertEqual(
            {
                ("GRAPH_MISSING_MEMBER", "ordered-map-theory", "#"),
                (
                    "GRAPH_UNEXPECTED_MEMBER",
                    "ordered-map-theory/records/ordered-map-spec.json",
                    "#",
                ),
            },
            {
                (item.code, item.path, item.pointer)
                for item in observations["version"].diagnostics
            },
        )
        self.assertEqual(
            [
                (
                    "SCHEMA_MISSING_FIELD",
                    "ordered-map-theory/records/ordered-map-spec.json",
                    "#/laws/0/id",
                )
            ],
            [
                (item.code, item.path, item.pointer)
                for item in observations["schema"].diagnostics
            ],
        )
        self.assertEqual(
            expected_messages["missing"],
            observations["missing"].diagnostics[0].message,
        )
        self.assertEqual(
            expected_messages["unexpected"],
            observations["unexpected"].diagnostics[0].message,
        )
        self.assertEqual(
            expected_messages["digest"],
            observations["digest"].diagnostics[0].message,
        )
        version_messages = {item.code: item.message for item in observations["version"].diagnostics}
        self.assertEqual(
            "manifest requires (specification, ordered-map, 0.1.0)",
            version_messages["GRAPH_MISSING_MEMBER"],
        )
        self.assertEqual(
            "manifest does not include (specification, ordered-map, 0.1.1) in source 'ordered-map-theory'",
            version_messages["GRAPH_UNEXPECTED_MEMBER"],
        )
        self.assertIsNone(observations["schema"].diagnostics[0].message)
        self.assertEqual(
            "requested local ID absent-workload in (realizationProfile, ordered-map-ascii-fold, 0.1.0)",
            observations["link"].diagnostics[0].message,
        )
        self.assertEqual(
            [
                (
                    "LINK_DANGLING_PROFILE_MEMBER",
                    "ordered-map-theory/records/ordered-map-spec.json",
                    "#/performancePropositions/0/workload/localId",
                )
            ],
            [
                (item.code, item.path, item.pointer)
                for item in observations["link"].diagnostics
            ],
        )
        for result in observations.values():
            self.assertFalse(result.ok)
            self.assertIsNotNone(result.authority)
            self.assertIsNotNone(result.graph)
            self.assertIsNone(result.publication)
            self.assertIsNone(result.theory)

    def test_invalid_and_symlinked_records_fail_without_partial_views(self) -> None:
        observations = {}
        for attack in ("invalid", "symlink"):
            with self.subTest(attack=attack), tempfile.TemporaryDirectory(
                prefix=f"o5-input-{attack}-"
            ) as raw:
                root = self._copy_repository_slice(raw)
                spec = (
                    root
                    / "registry"
                    / "ordered-map"
                    / "theory"
                    / "records"
                    / "ordered-map-spec.json"
                )
                if attack == "invalid":
                    spec.write_text("{ malformed\n", encoding="utf-8")
                else:
                    outside = Path(raw) / "outside-spec.json"
                    shutil.copyfile(spec, outside)
                    spec.unlink()
                    spec.symlink_to(outside)
                observations[attack] = self._inspect_at(root)

        self.assertEqual(
            [
                (
                    "INPUT_INVALID_JSON",
                    "ordered-map-theory/records/ordered-map-spec.json",
                    "#",
                )
            ],
            [
                (item.code, item.path, item.pointer)
                for item in observations["invalid"].diagnostics
            ],
        )
        self.assertEqual(
            [
                (
                    "INPUT_SYMLINK",
                    "ordered-map-theory/records/ordered-map-spec.json",
                    "#",
                )
            ],
            [
                (item.code, item.path, item.pointer)
                for item in observations["symlink"].diagnostics
            ],
        )
        for result in observations.values():
            self.assertFalse(result.ok)
            self.assertIsNotNone(result.authority)
            self.assertIsNotNone(result.graph)
            self.assertIsNone(result.publication)
            self.assertIsNone(result.theory)

    def test_success_is_detached_and_recursively_safe_to_reinspect(self) -> None:
        first = theory_source.inspect_theory_source()
        self.assertTrue(first.ok, first.diagnostics)

        with self.assertRaises((AttributeError, TypeError)):
            first.authority.source = "attacker"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            first.publication.records.append(object())  # type: ignore[attr-defined]
        document = first.graph.records[1].document
        document["id"] = "attacker"
        declaration = first.theory.declarations[0].content
        declaration["id"] = "attacker"

        second = theory_source.inspect_theory_source()
        self.assertTrue(second.ok, second.diagnostics)
        self.assertEqual(SPECIFICATION, second.theory.specification)
        self.assertEqual("ordered-map", first.graph.records[1].document["id"])
        self.assertNotEqual("attacker", first.theory.declarations[0].content["id"])


if __name__ == "__main__":
    unittest.main()
