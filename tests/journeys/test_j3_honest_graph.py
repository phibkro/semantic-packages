from __future__ import annotations

import builtins
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from scripts import record_check


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_ROOT = ROOT / "registry" / "stack"
MANIFEST = REGISTRY_ROOT / "manifest.json"

try:
    graph = importlib.import_module("semantic_packages.graph")
    GRAPH_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.graph":
        raise
    graph = None
    GRAPH_IMPORT_ERROR = error

publication = importlib.import_module("semantic_packages.publication")
registration = importlib.import_module("semantic_packages.registration")


EXPECTED_SOURCES = {
    "theory": ("theory", ("dependency", "theory-authored")),
    "rust": ("packages/rust", ("package-authored",)),
    "typescript": ("packages/typescript", ("package-authored",)),
    "package-consumer": (
        "consumers/package",
        ("package-consumer-authored",),
    ),
    "composition-theory": (
        "compositions/theory",
        ("theory-authored",),
    ),
}

# This literal is deliberately independent of product code and of the future
# manifest.  Paths are not members: byte-preserving rename remains provenance only.
EXPECTED_MEMBERS = sorted(
    [
        (("claim", "stack-pop-empty-law", "0.1.0"), "f3de2c39a1ecf85865aaff3dead75d55b76807e02d8a9b61d358a8f5688c3b6a", "theory-authored", "theory"),
        (("evidence", "stack-pop-empty-model-proof", "0.1.0"), "7813247dad2d138295eb8e868eca2f81168d08654d4dd6ce253542470e11ef90", "theory-authored", "theory"),
        (("realizationProfile", "stack-default", "0.1.0"), "2a51ed7d2e1266376cd4a58ef3f20d30244655d25cb884816576be989014eddb", "dependency", "theory"),
        (("specification", "stack", "0.1.0"), "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1", "theory-authored", "theory"),
        (("claim", "stack-rust-persistence", "0.1.0"), "60cbdcaee70ec4d843e6f0992fb80ede012e54d297bd69fdafc5d6c0decbae0e", "package-authored", "rust"),
        (("claim", "stack-rust-pop-empty", "0.1.0"), "7754b304be1de34ac7381813cca804e2b2c49f10b29bded9067b1fb8744aa8e0", "package-authored", "rust"),
        (("claim", "stack-rust-pop-push", "0.1.0"), "db0ca3571e426abf3b053f143b30354f70db0afbf323661af558873de66f3ab6", "package-authored", "rust"),
        (("claim", "stack-rust-stack-effects", "0.1.0"), "452d0120451aa4f1bf68c3460ac0369eb1f47fb5e3326364ffb56330877154f3", "package-authored", "rust"),
        (("evidence", "stack-rust-persistence-conformance", "0.1.0"), "951f88f7f9ea163a1ecd740bdea41dce0caa61b0f52fd3cae1beb6b5269420a3", "package-authored", "rust"),
        (("evidence", "stack-rust-pop-empty-conformance", "0.1.0"), "1b12750f890e00e91786bab41cbbe2eda59455783d86592672de4f53430efec5", "package-authored", "rust"),
        (("evidence", "stack-rust-pop-push-conformance", "0.1.0"), "9a3696f24b27c27d84ff372de0abb6333f3c4c443729fa0bbf9373bad89f28d1", "package-authored", "rust"),
        (("evidence", "stack-rust-stack-effects-conformance", "0.1.0"), "827e069bda46bea5876d5d3ce345e41694d80f431c327c76bf706c7d20efa4e9", "package-authored", "rust"),
        (("realization", "stack-rust", "0.1.0"), "7cdf2c9cec54557a57d6f1545f81f95cb52998ec013e808d79b4467dca3c655d", "package-authored", "rust"),
        (("claim", "stack-typescript-persistence", "0.1.0"), "1d75002ea7b20af860067b48016fb11b3d285a6463b5bcd37142bd586ff837ff", "package-authored", "typescript"),
        (("claim", "stack-typescript-pop-empty", "0.1.0"), "282eeeedaa5c7a3b54f033c0cce13fb16e92bdae3e183372296b52444b9d20fc", "package-authored", "typescript"),
        (("claim", "stack-typescript-pop-push", "0.1.0"), "4be51efdef4d90d3e553e75d27ce36cc94e751c6dad047e37e064ab44a310091", "package-authored", "typescript"),
        (("claim", "stack-typescript-stack-effects", "0.1.0"), "0bb2ae29c70a12c3921cdea874f34d0574b4cda1550f14636cf273e0b1a82877", "package-authored", "typescript"),
        (("evidence", "stack-typescript-persistence-conformance", "0.1.0"), "133bd7de9e4900609377bcaf4da66a239d184a18a41412d5a2654903afc987a5", "package-authored", "typescript"),
        (("evidence", "stack-typescript-pop-empty-conformance", "0.1.0"), "75dacc500799a3383d7299d998ef9518314a7de029dc24eacef97138da280a26", "package-authored", "typescript"),
        (("evidence", "stack-typescript-pop-push-conformance", "0.1.0"), "c50d5c13485c7e4eae92871fe8e29fba4be14607c35f1b8e4a3017803b812a0e", "package-authored", "typescript"),
        (("evidence", "stack-typescript-stack-effects-conformance", "0.1.0"), "6ca311ba6ec60ebc8cc47c50b58fb3e34f80b64032e467cbb9f27edb834baa65", "package-authored", "typescript"),
        (("realization", "stack-typescript", "0.1.0"), "97ce905cee0d196d34e7a017637ca75fc7ef4c9a438d20168b02d05fd8664adf", "package-authored", "typescript"),
        (("consumerPolicy", "stack-bounded-policy", "0.1.0"), "f814cf62fb956030ee51ac378c340a3eb149123b7192b827c1a1084b54890acb", "package-consumer-authored", "package-consumer"),
        (("specification", "undo-history", "0.1.0"), "2f05e331562d2e1dacc06af8bbb14ff47e7d3155599f8f6d5997c0506fcb6866", "theory-authored", "composition-theory"),
    ]
)


def _write_json(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _address(document: dict) -> tuple[str, str, str]:
    return document["kind"], document["id"], document["version"]


def _predecessor_record_paths():
    """Yield only roots governed by the immutable predecessor source set."""

    for source, (root, _roles) in EXPECTED_SOURCES.items():
        for path in sorted((REGISTRY_ROOT / root).rglob("*.json")):
            yield root, source, path


class GraphFixtureCheckpointTest(unittest.TestCase):
    def test_curated_record_packets_are_exact_and_graph_valid(self) -> None:
        records: dict[str, dict] = {}
        actual = []
        role_by_address = {
            address: (role, source)
            for address, _digest, role, source in EXPECTED_MEMBERS
        }
        for _root, source, path in _predecessor_record_paths():
            relative = path.relative_to(REGISTRY_ROOT).as_posix()
            raw = path.read_bytes()
            document = json.loads(raw)
            address = _address(document)
            role, expected_source = role_by_address[address]
            self.assertEqual(source, expected_source)
            actual.append((address, hashlib.sha256(raw).hexdigest(), role, expected_source))
            records[relative] = document

        self.assertEqual(EXPECTED_MEMBERS, sorted(actual))
        self.assertEqual([], record_check.check_graph(records))

    def test_graph_module_is_the_only_red_predecessor(self) -> None:
        self.assertIsNotNone(
            graph,
            "J3-F1 intentionally precedes semantic_packages/graph.py; "
            f"observed {GRAPH_IMPORT_ERROR!r}",
        )


@unittest.skipIf(
    graph is None,
    "J3-F1 freezes the contract before semantic_packages.graph exists",
)
class HonestStackGraphContractTest(unittest.TestCase):
    def _copy_registry(self, raw: str) -> tuple[Path, Path]:
        registry = Path(raw) / "registry" / "stack"
        shutil.copytree(REGISTRY_ROOT, registry)
        return registry, registry / "manifest.json"

    def _inspect(self, manifest: Path):
        return graph.inspect_stack_graph(manifest)

    def _codes(self, observation) -> list[str]:
        return [diagnostic.code for diagnostic in observation.diagnostics]

    def _formatted(self, observation) -> str:
        return "\n".join(diagnostic.format() for diagnostic in observation.diagnostics)

    def _load_manifest(self, manifest: Path) -> dict:
        return json.loads(manifest.read_text(encoding="utf-8"))

    def _member(self, manifest: dict, address: tuple[str, str, str]) -> dict:
        return next(
            member
            for member in manifest["members"]
            if (
                member["address"]["kind"],
                member["address"]["id"],
                member["address"]["version"],
            )
            == address
        )

    def _signature(self, observation):
        return [
            (record.address, record.sha256, record.role, record.source, record.document)
            for record in observation.records
        ]

    def test_manifest_is_the_minimal_single_authority(self) -> None:
        manifest = self._load_manifest(MANIFEST)
        self.assertEqual({"formatVersion", "sources", "members"}, set(manifest))
        self.assertEqual(1, manifest["formatVersion"])
        self.assertEqual(
            EXPECTED_SOURCES,
            {
                source["id"]: (source["root"], tuple(sorted(source["roles"])))
                for source in manifest["sources"]
            },
        )
        self.assertTrue(
            all(set(source) == {"id", "root", "roles"} for source in manifest["sources"])
        )
        self.assertTrue(
            all(
                set(member) == {"source", "address", "sha256", "role"}
                and set(member["address"]) == {"kind", "id", "version"}
                for member in manifest["members"]
            )
        )
        actual = sorted(
            (
                (
                    member["address"]["kind"],
                    member["address"]["id"],
                    member["address"]["version"],
                ),
                member["sha256"],
                member["role"],
                member["source"],
            )
            for member in manifest["members"]
        )
        self.assertEqual(EXPECTED_MEMBERS, actual)

    def test_exact_24_member_inventory_and_canonical_documents(self) -> None:
        observation = self._inspect(MANIFEST)
        self.assertTrue(observation.ok, self._formatted(observation))
        actual = [
            (record.address, record.sha256, record.role, record.source)
            for record in observation.records
        ]
        self.assertEqual(EXPECTED_MEMBERS, actual)
        self.assertEqual(set(EXPECTED_SOURCES), {record.source for record in observation.records})

        expected_documents = {}
        for _root, _source, path in _predecessor_record_paths():
            document = json.loads(path.read_bytes())
            expected_documents[_address(document)] = document
        self.assertEqual(
            expected_documents,
            {record.address: record.document for record in observation.records},
        )

    def test_manifest_input_failures_are_manifest_only_and_do_not_observe_roots(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j3-manifest-phase-") as raw:
            registry = Path(raw) / "registry"
            registry.mkdir()
            source_root = registry / "must-not-be-observed"
            source_root.mkdir()
            attacks = {
                "missing": registry / "missing.json",
                "invalid-json": registry / "invalid.json",
                "invalid-shape": registry / "shape.json",
            }
            attacks["invalid-json"].write_text("{ invalid\n", encoding="utf-8")
            _write_json(
                attacks["invalid-shape"],
                {
                    "formatVersion": 1,
                    "sources": [
                        {
                            "id": "sentinel",
                            "root": "must-not-be-observed",
                            "roles": ["theory-authored"],
                        }
                    ],
                },
            )

            original_open = Path.open
            original_scandir = os.scandir

            def guarded_open(path, *args, **kwargs):
                if Path(path).is_relative_to(source_root):
                    raise AssertionError("source record opened after manifest failure")
                return original_open(path, *args, **kwargs)

            def guarded_scandir(path):
                if Path(path).is_relative_to(source_root):
                    raise AssertionError("source root scanned after manifest failure")
                return original_scandir(path)

            for name, manifest in attacks.items():
                with self.subTest(name=name), mock.patch.object(
                    Path, "open", guarded_open
                ), mock.patch.object(os, "scandir", guarded_scandir):
                    observation = self._inspect(manifest)
                self.assertFalse(observation.ok)
                self.assertTrue(self._codes(observation))
                self.assertTrue(all(code.startswith("MANIFEST_") for code in self._codes(observation)))
                self.assertEqual((), observation.records)

    def test_manifest_and_ancestor_symlinks_are_rejected_without_target_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j3-manifest-symlink-") as raw:
            base = Path(raw)
            real = base / "real"
            real.mkdir()
            target = real / "manifest.json"
            target.write_bytes(b"{}")
            leaf = base / "manifest.json"
            leaf.symlink_to(target)
            linked_parent = base / "linked"
            linked_parent.symlink_to(real, target_is_directory=True)

            for name, manifest in (("leaf", leaf), ("ancestor", linked_parent / "manifest.json")):
                with self.subTest(name=name), ExitStack() as stack:
                    stack.enter_context(
                        mock.patch.object(
                            Path,
                            "open",
                            side_effect=AssertionError("symlink target opened"),
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(
                            builtins,
                            "open",
                            side_effect=AssertionError("symlink target opened"),
                        )
                    )
                    observation = self._inspect(manifest)
                self.assertEqual(["MANIFEST_INPUT_SYMLINK"], self._codes(observation))
                self.assertEqual((), observation.records)

    def test_manifest_shape_and_relations_fail_before_source_observation(self) -> None:
        base = self._load_manifest(MANIFEST)
        attacks = []

        def candidate(name, mutate):
            value = json.loads(json.dumps(base))
            mutate(value)
            attacks.append((name, value))

        def slash_source_id(value):
            old_id = value["sources"][0]["id"]
            value["sources"][0]["id"] = "theory/aux"
            for member in value["members"]:
                if member["source"] == old_id:
                    member["source"] = "theory/aux"

        candidate("unknown-field", lambda value: value.update(unexpected=True))
        candidate("format-version", lambda value: value.update(formatVersion=2))
        candidate("empty-source-id", lambda value: value["sources"][0].update(id=""))
        candidate(
            "slash-source-id",
            slash_source_id,
        )
        candidate(
            "duplicate-source-id",
            lambda value: value["sources"][1].update(id=value["sources"][0]["id"]),
        )
        candidate(
            "duplicate-source-root",
            lambda value: value["sources"][1].update(root=value["sources"][0]["root"]),
        )
        candidate(
            "unknown-member-source",
            lambda value: value["members"][0].update(source="absent"),
        )
        candidate(
            "bad-digest-shape",
            lambda value: value["members"][0].update(sha256="ABC"),
        )
        candidate(
            "member-filename",
            lambda value: value["members"][0].update(path="records/forbidden.json"),
        )
        candidate(
            "duplicate-member-address",
            lambda value: value["members"].append(
                json.loads(json.dumps(value["members"][0]))
            ),
        )

        for name, manifest_document in attacks:
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="j3-manifest-shape-"
            ) as raw:
                _registry, manifest = self._copy_registry(raw)
                _write_json(manifest, manifest_document)
                observation = self._inspect(manifest)
            self.assertFalse(observation.ok)
            self.assertTrue(self._codes(observation))
            self.assertTrue(
                all(code.startswith("MANIFEST_") for code in self._codes(observation))
            )
            self.assertEqual((), observation.records)

    def test_source_roots_are_relative_directory_nonoverlapping_and_role_constrained(self) -> None:
        attacks = []
        base = self._load_manifest(MANIFEST)
        for name, mutate in (
            ("empty", lambda value: value["sources"][0].update(root="")),
            ("dot", lambda value: value["sources"][0].update(root=".")),
            ("absolute", lambda value: value["sources"][0].update(root="/tmp/outside")),
            ("double-slash", lambda value: value["sources"][0].update(root="//tmp/outside")),
            ("traversal", lambda value: value["sources"][0].update(root="../outside")),
            ("backslash", lambda value: value["sources"][0].update(root="theory\\records")),
            ("overlap", lambda value: value["sources"][1].update(root="theory/records")),
            ("bad-role", lambda value: value["sources"][0]["roles"].append("unknown-role")),
        ):
            candidate = json.loads(json.dumps(base))
            mutate(candidate)
            attacks.append((name, candidate))

        for name, candidate in attacks:
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix="j3-root-safe-") as raw:
                _registry, manifest = self._copy_registry(raw)
                _write_json(manifest, candidate)
                observation = self._inspect(manifest)
                self.assertFalse(observation.ok)
                self.assertTrue(self._codes(observation))
                self.assertTrue(all(code.startswith("MANIFEST_") for code in self._codes(observation)))

        with tempfile.TemporaryDirectory(prefix="j3-root-file-") as raw:
            registry, manifest = self._copy_registry(raw)
            regular_file = registry / "not-a-directory"
            regular_file.write_text("not a source root\n", encoding="utf-8")
            candidate = self._load_manifest(manifest)
            candidate["sources"][0]["root"] = "not-a-directory"
            _write_json(manifest, candidate)
            observation = self._inspect(manifest)
        self.assertFalse(observation.ok)
        self.assertTrue(
            any(code.startswith(("MANIFEST_", "INPUT_")) for code in self._codes(observation))
        )

    def test_source_symlink_is_rejected_without_following(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j3-source-symlink-") as raw:
            registry, manifest = self._copy_registry(raw)
            theory = registry / "theory"
            outside = Path(raw) / "outside-theory"
            theory.rename(outside)
            theory.symlink_to(outside, target_is_directory=True)

            observation = self._inspect(manifest)

        self.assertFalse(observation.ok)
        self.assertEqual(["INPUT_SYMLINK"], self._codes(observation))

    def test_internal_directory_and_record_symlinks_are_rejected_without_following(self) -> None:
        for name, target_relative in (
            ("directory", "theory/records"),
            ("record", "theory/records/stack-spec.json"),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="j3-internal-symlink-"
            ) as raw:
                registry, manifest = self._copy_registry(raw)
                target = registry / target_relative
                outside = Path(raw) / f"outside-{name}"
                target.rename(outside)
                target.symlink_to(outside, target_is_directory=outside.is_dir())
                observation = self._inspect(manifest)
            self.assertFalse(observation.ok)
            self.assertIn("INPUT_SYMLINK", self._codes(observation))

    def test_record_input_and_schema_failures_stop_before_links_and_membership(self) -> None:
        for name, mutate, expected_prefix in (
            (
                "input",
                lambda path: path.write_text("{ invalid\n", encoding="utf-8"),
                "INPUT_",
            ),
            (
                "schema",
                lambda path: _write_json(
                    path,
                    {
                        **json.loads(path.read_text(encoding="utf-8")),
                        "kind": ["specification"],
                    },
                ),
                "SCHEMA_",
            ),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix="j3-record-phase-"
            ) as raw:
                registry, manifest = self._copy_registry(raw)
                path = registry / "theory" / "records" / "stack-spec.json"
                mutate(path)
                observation = self._inspect(manifest)

            self.assertFalse(observation.ok)
            self.assertTrue(any(code.startswith(expected_prefix) for code in self._codes(observation)))
            self.assertFalse(
                any(code.startswith(("LINK_", "GRAPH_")) for code in self._codes(observation))
            )

    def test_link_failures_remain_link_diagnostics_not_membership_failures(self) -> None:
        address = ("consumerPolicy", "stack-bounded-policy", "0.1.0")
        with tempfile.TemporaryDirectory(prefix="j3-link-phase-") as raw:
            registry, manifest = self._copy_registry(raw)
            policy_path = (
                registry
                / "consumers"
                / "package"
                / "records"
                / "stack-bounded-policy.json"
            )
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["specification"]["version"] = "absent"
            _write_json(policy_path, policy)
            manifest_document = self._load_manifest(manifest)
            self._member(manifest_document, address)["sha256"] = hashlib.sha256(
                policy_path.read_bytes()
            ).hexdigest()
            _write_json(manifest, manifest_document)
            observation = self._inspect(manifest)

        self.assertFalse(observation.ok)
        self.assertIn("LINK_VERSION_MISMATCH", self._codes(observation))
        self.assertFalse(any(code.startswith("GRAPH_") for code in self._codes(observation)))

    def test_manifest_duplicate_source_and_member_selectors_are_rejected(self) -> None:
        base = self._load_manifest(MANIFEST)
        attacks = []
        duplicate_source = json.loads(json.dumps(base))
        duplicate_source["sources"].append(duplicate_source["sources"][0])
        attacks.append(("MANIFEST_DUPLICATE_SOURCE_ID", duplicate_source))
        duplicate_member = json.loads(json.dumps(base))
        duplicate_member["members"].append(duplicate_member["members"][0])
        attacks.append(("MANIFEST_DUPLICATE_MEMBER_ADDRESS", duplicate_member))

        for expected_code, candidate in attacks:
            with self.subTest(code=expected_code), tempfile.TemporaryDirectory(prefix="j3-duplicate-") as raw:
                _registry, manifest = self._copy_registry(raw)
                _write_json(manifest, candidate)
                observation = self._inspect(manifest)
                self.assertIn(expected_code, self._codes(observation))
                self.assertEqual((), observation.records)

    def test_member_omission_addition_digest_and_source_attacks_fail(self) -> None:
        base = self._load_manifest(MANIFEST)
        stack_address = ("specification", "stack", "0.1.0")
        attacks = []

        omitted = json.loads(json.dumps(base))
        omitted["members"].remove(self._member(omitted, stack_address))
        attacks.append(("omitted", "GRAPH_UNEXPECTED_MEMBER", omitted))

        added = json.loads(json.dumps(base))
        extra = json.loads(json.dumps(added["members"][0]))
        extra["address"] = {"kind": "specification", "id": "absent", "version": "0.1.0"}
        added["members"].append(extra)
        attacks.append(("added", "GRAPH_MISSING_MEMBER", added))

        digest = json.loads(json.dumps(base))
        self._member(digest, stack_address)["sha256"] = "0" * 64
        attacks.append(("digest", "GRAPH_DIGEST_MISMATCH", digest))

        source = json.loads(json.dumps(base))
        self._member(source, stack_address).update(
            source="rust", role="package-authored"
        )
        attacks.append(("source", "GRAPH_MISSING_MEMBER", source))

        for name, expected_code, candidate in attacks:
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix="j3-member-") as raw:
                _registry, manifest = self._copy_registry(raw)
                _write_json(manifest, candidate)
                observation = self._inspect(manifest)
                self.assertFalse(observation.ok)
                self.assertIn(expected_code, self._codes(observation))
                if name == "source":
                    self.assertIn("GRAPH_UNEXPECTED_MEMBER", self._codes(observation))

    def test_allowed_manifest_role_change_is_live_without_a_hidden_role_map(self) -> None:
        address = ("specification", "stack", "0.1.0")
        with tempfile.TemporaryDirectory(prefix="j3-role-live-") as raw:
            _registry, manifest = self._copy_registry(raw)
            candidate = self._load_manifest(manifest)
            self._member(candidate, address)["role"] = "dependency"
            _write_json(manifest, candidate)
            observation = self._inspect(manifest)

        self.assertTrue(observation.ok, self._formatted(observation))
        record = next(record for record in observation.records if record.address == address)
        self.assertEqual("dependency", record.role)

    def test_obsolete_history_and_unlisted_valid_records_are_exposed(self) -> None:
        sources = [
            ROOT / "fixtures" / "records" / "valid" / "stack-reference-realization-0.2.0.json",
            ROOT / "fixtures" / "records" / "valid" / "link" / "historical-fixture-only-support" / "records" / "realization.json",
            ROOT / "fixtures" / "records" / "valid" / "link" / "historical-fixture-only-support" / "records" / "claim.json",
            ROOT / "fixtures" / "records" / "valid" / "link" / "historical-fixture-only-support" / "records" / "evidence.json",
        ]
        with tempfile.TemporaryDirectory(prefix="j3-obsolete-") as raw:
            registry, manifest = self._copy_registry(raw)
            for index, source in enumerate(sources):
                shutil.copyfile(source, registry / "packages" / "rust" / "records" / f"obsolete-{index}.json")
            observation = self._inspect(manifest)

        self.assertFalse(observation.ok)
        self.assertIn("GRAPH_UNEXPECTED_MEMBER", self._codes(observation))
        rendered = self._formatted(observation)
        self.assertIn("(realization, stack-reference, 0.2.0)", rendered)
        self.assertIn("(claim, stack-reference-persistence, 0.1.0)", rendered)

    def test_cross_root_move_retains_role_but_is_missing_and_unexpected(self) -> None:
        address = ("specification", "stack", "0.1.0")
        with tempfile.TemporaryDirectory(prefix="j3-cross-root-") as raw:
            registry, manifest = self._copy_registry(raw)
            source = registry / "theory" / "records" / "stack-spec.json"
            destination = registry / "packages" / "rust" / "records" / "moved-stack-spec.json"
            source.rename(destination)
            observation = self._inspect(manifest)

        self.assertFalse(observation.ok)
        self.assertIn("GRAPH_MISSING_MEMBER", self._codes(observation))
        self.assertIn("GRAPH_UNEXPECTED_MEMBER", self._codes(observation))
        moved = next(record for record in observation.records if record.address == address)
        self.assertEqual("theory-authored", moved.role)

    def test_byte_preserving_rename_in_each_source_changes_only_provenance(self) -> None:
        representatives = {
            "theory": "theory/records/stack-spec.json",
            "rust": "packages/rust/records/stack-rust-realization.json",
            "typescript": "packages/typescript/records/stack-typescript-realization.json",
            "package-consumer": "consumers/package/records/stack-bounded-policy.json",
            "composition-theory": "compositions/theory/records/undo-history-spec.json",
        }
        for source_id, relative in representatives.items():
            with self.subTest(source=source_id), tempfile.TemporaryDirectory(prefix="j3-rename-") as raw:
                registry, manifest = self._copy_registry(raw)
                original = registry / relative
                renamed = original.with_name("renamed.json")
                original.rename(renamed)
                observation = self._inspect(manifest)
                self.assertTrue(observation.ok, self._formatted(observation))
                self.assertEqual(EXPECTED_MEMBERS, [
                    (record.address, record.sha256, record.role, record.source)
                    for record in observation.records
                ])
                self.assertTrue(any(record.path.endswith("renamed.json") for record in observation.records))

    def test_whole_source_relocation_requires_and_accepts_manifest_root_change(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j3-relocate-") as raw:
            registry, manifest = self._copy_registry(raw)
            original = registry / "packages" / "rust"
            relocated = registry / "vendors" / "rust"
            relocated.parent.mkdir()
            original.rename(relocated)
            stale = self._inspect(manifest)
            candidate = self._load_manifest(manifest)
            next(source for source in candidate["sources"] if source["id"] == "rust")["root"] = "vendors/rust"
            _write_json(manifest, candidate)
            updated = self._inspect(manifest)

        self.assertFalse(stale.ok)
        self.assertTrue(updated.ok, self._formatted(updated))
        self.assertEqual(EXPECTED_MEMBERS, [
            (record.address, record.sha256, record.role, record.source)
            for record in updated.records
        ])

    def test_source_and_member_order_are_semantically_irrelevant(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j3-permutation-") as raw:
            _registry, manifest = self._copy_registry(raw)
            original = self._inspect(manifest)
            candidate = self._load_manifest(manifest)
            candidate["sources"].reverse()
            candidate["members"].reverse()
            for source in candidate["sources"]:
                source["roles"].reverse()
            _write_json(manifest, candidate)
            permuted = self._inspect(manifest)

        self.assertTrue(original.ok, self._formatted(original))
        self.assertTrue(permuted.ok, self._formatted(permuted))
        self.assertEqual(self._signature(original), self._signature(permuted))

    def test_each_call_is_an_immutable_deep_snapshot_and_reloads_manifest_and_records(self) -> None:
        address = ("specification", "stack", "0.1.0")
        with tempfile.TemporaryDirectory(prefix="j3-snapshot-") as raw:
            registry, manifest = self._copy_registry(raw)
            first = self._inspect(manifest)
            first_record = next(record for record in first.records if record.address == address)
            returned_document = first_record.document
            try:
                returned_document["carriers"][0]["description"] = "caller mutation"
            except (AttributeError, TypeError):
                pass
            else:
                self.assertNotEqual("caller mutation", first_record.document["carriers"][0]["description"])
            with self.assertRaises((AttributeError, TypeError)):
                first_record.role = "changed"

            path = registry / "theory" / "records" / "stack-spec.json"
            changed = json.loads(path.read_text(encoding="utf-8"))
            changed["carriers"][0]["description"] += " Snapshot successor."
            _write_json(path, changed)
            candidate = self._load_manifest(manifest)
            self._member(candidate, address)["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            _write_json(manifest, candidate)
            second = self._inspect(manifest)

        self.assertTrue(first.ok, self._formatted(first))
        self.assertTrue(second.ok, self._formatted(second))
        self.assertNotEqual(first_record.sha256, next(record for record in second.records if record.address == address).sha256)
        self.assertNotIn("Snapshot successor.", first_record.document["carriers"][0]["description"])

    def test_graph_inspection_never_executes_records_or_metadata(self) -> None:
        touched = []

        def reject(name):
            def fail(*_args, **_kwargs):
                touched.append(name)
                raise AssertionError(f"graph inspection attempted {name}")

            return fail

        boundaries = [
            (subprocess, "Popen"),
            (subprocess, "run"),
            (subprocess, "call"),
            (subprocess, "check_call"),
            (subprocess, "check_output"),
            (os, "system"),
        ]
        with ExitStack() as stack:
            for owner, name in boundaries:
                stack.enter_context(mock.patch.object(owner, name, side_effect=reject(name)))
            observation = self._inspect(MANIFEST)

        self.assertEqual([], touched)
        self.assertTrue(observation.ok, self._formatted(observation))

    def test_legacy_views_fail_closed_on_invalid_manifest_projection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j3-invalid-projection-") as raw:
            _registry, manifest = self._copy_registry(raw)
            candidate = self._load_manifest(manifest)
            candidate["members"].append(
                json.loads(json.dumps(candidate["members"][0]))
            )
            _write_json(manifest, candidate)
            projection = graph._inspect_manifest_projection(manifest)

            self.assertFalse(projection.ok)
            self.assertIn(
                "MANIFEST_DUPLICATE_MEMBER_ADDRESS",
                [diagnostic.code for diagnostic in projection.diagnostics],
            )
            with mock.patch.object(publication, "_MANIFEST", projection):
                theory = publication.inspect_stack_theory(
                    Path(raw) / "theory-must-not-be-observed"
                )
            with mock.patch.object(registration, "_MANIFEST", projection):
                package = registration.inspect_stack_package(
                    Path(raw) / "theory-must-not-be-observed",
                    Path(raw) / "package-must-not-be-observed",
                    "rust",
                )

        for observation in (theory, package):
            self.assertFalse(observation.ok)
            self.assertEqual((), observation.records)
            self.assertEqual(
                ["MANIFEST_DUPLICATE_MEMBER_ADDRESS"],
                [diagnostic.code for diagnostic in observation.diagnostics],
            )


if __name__ == "__main__":
    unittest.main()
