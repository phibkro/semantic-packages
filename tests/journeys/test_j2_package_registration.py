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


ROOT = Path(__file__).resolve().parents[2]
THEORY_ROOT = ROOT / "registry" / "stack" / "theory"
PACKAGE_ROOTS = {
    "rust": ROOT / "registry" / "stack" / "packages" / "rust",
    "typescript": ROOT / "registry" / "stack" / "packages" / "typescript",
}
VALID_FIXTURES = ROOT / "fixtures" / "records" / "valid"
HISTORICAL_FIXTURES = (
    VALID_FIXTURES / "link" / "historical-fixture-only-support" / "records"
)

try:
    registration = importlib.import_module("semantic_packages.registration")
    REGISTRATION_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.registration":
        raise
    registration = None
    REGISTRATION_IMPORT_ERROR = error

finite_source = importlib.import_module("semantic_packages._finite_source")


THEORY_INVENTORY = [
    (
        ("claim", "stack-pop-empty-law", "0.1.0"),
        "theory/records/pop-empty-spec-claim.json",
        "f3de2c39a1ecf85865aaff3dead75d55b76807e02d8a9b61d358a8f5688c3b6a",
        "theory-authored",
    ),
    (
        ("evidence", "stack-pop-empty-model-proof", "0.1.0"),
        "theory/records/stack-pop-empty-model-proof-evidence.json",
        "7813247dad2d138295eb8e868eca2f81168d08654d4dd6ce253542470e11ef90",
        "theory-authored",
    ),
    (
        ("realizationProfile", "stack-default", "0.1.0"),
        "theory/dependencies/stack-profile.json",
        "2a51ed7d2e1266376cd4a58ef3f20d30244655d25cb884816576be989014eddb",
        "dependency",
    ),
    (
        ("specification", "stack", "0.1.0"),
        "theory/records/stack-spec.json",
        "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1",
        "theory-authored",
    ),
]

PACKAGE_INVENTORIES = {
    "rust": [
        (("claim", "stack-rust-persistence", "0.1.0"), "stack-rust-persistence-claim.json", "60cbdcaee70ec4d843e6f0992fb80ede012e54d297bd69fdafc5d6c0decbae0e"),
        (("claim", "stack-rust-pop-empty", "0.1.0"), "stack-rust-pop-empty-claim.json", "7754b304be1de34ac7381813cca804e2b2c49f10b29bded9067b1fb8744aa8e0"),
        (("claim", "stack-rust-pop-push", "0.1.0"), "stack-rust-pop-push-claim.json", "db0ca3571e426abf3b053f143b30354f70db0afbf323661af558873de66f3ab6"),
        (("claim", "stack-rust-stack-effects", "0.1.0"), "stack-rust-stack-effects-claim.json", "452d0120451aa4f1bf68c3460ac0369eb1f47fb5e3326364ffb56330877154f3"),
        (("evidence", "stack-rust-persistence-conformance", "0.1.0"), "stack-rust-persistence-evidence.json", "951f88f7f9ea163a1ecd740bdea41dce0caa61b0f52fd3cae1beb6b5269420a3"),
        (("evidence", "stack-rust-pop-empty-conformance", "0.1.0"), "stack-rust-pop-empty-evidence.json", "1b12750f890e00e91786bab41cbbe2eda59455783d86592672de4f53430efec5"),
        (("evidence", "stack-rust-pop-push-conformance", "0.1.0"), "stack-rust-pop-push-evidence.json", "9a3696f24b27c27d84ff372de0abb6333f3c4c443729fa0bbf9373bad89f28d1"),
        (("evidence", "stack-rust-stack-effects-conformance", "0.1.0"), "stack-rust-stack-effects-evidence.json", "827e069bda46bea5876d5d3ce345e41694d80f431c327c76bf706c7d20efa4e9"),
        (("realization", "stack-rust", "0.1.0"), "stack-rust-realization.json", "7cdf2c9cec54557a57d6f1545f81f95cb52998ec013e808d79b4467dca3c655d"),
    ],
    "typescript": [
        (("claim", "stack-typescript-persistence", "0.1.0"), "stack-typescript-persistence-claim.json", "1d75002ea7b20af860067b48016fb11b3d285a6463b5bcd37142bd586ff837ff"),
        (("claim", "stack-typescript-pop-empty", "0.1.0"), "stack-typescript-pop-empty-claim.json", "282eeeedaa5c7a3b54f033c0cce13fb16e92bdae3e183372296b52444b9d20fc"),
        (("claim", "stack-typescript-pop-push", "0.1.0"), "stack-typescript-pop-push-claim.json", "4be51efdef4d90d3e553e75d27ce36cc94e751c6dad047e37e064ab44a310091"),
        (("claim", "stack-typescript-stack-effects", "0.1.0"), "stack-typescript-stack-effects-claim.json", "0bb2ae29c70a12c3921cdea874f34d0574b4cda1550f14636cf273e0b1a82877"),
        (("evidence", "stack-typescript-persistence-conformance", "0.1.0"), "stack-typescript-persistence-evidence.json", "133bd7de9e4900609377bcaf4da66a239d184a18a41412d5a2654903afc987a5"),
        (("evidence", "stack-typescript-pop-empty-conformance", "0.1.0"), "stack-typescript-pop-empty-evidence.json", "75dacc500799a3383d7299d998ef9518314a7de029dc24eacef97138da280a26"),
        (("evidence", "stack-typescript-pop-push-conformance", "0.1.0"), "stack-typescript-pop-push-evidence.json", "c50d5c13485c7e4eae92871fe8e29fba4be14607c35f1b8e4a3017803b812a0e"),
        (("evidence", "stack-typescript-stack-effects-conformance", "0.1.0"), "stack-typescript-stack-effects-evidence.json", "6ca311ba6ec60ebc8cc47c50b58fb3e34f80b64032e467cbb9f27edb834baa65"),
        (("realization", "stack-typescript", "0.1.0"), "stack-typescript-realization.json", "97ce905cee0d196d34e7a017637ca75fc7ef4c9a438d20168b02d05fd8664adf"),
    ],
}


def _expected_inventory(package: str):
    package_records = [
        (address, f"package/records/{filename}", sha256, "package-authored")
        for address, filename, sha256 in PACKAGE_INVENTORIES[package]
    ]
    return sorted(THEORY_INVENTORY + package_records)


def _write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class RegistrationFixtureCheckpointTest(unittest.TestCase):
    def test_curated_package_records_are_exact_wave4_bytes(self) -> None:
        for package, inventory in PACKAGE_INVENTORIES.items():
            for _address, filename, expected_sha256 in inventory:
                with self.subTest(package=package, filename=filename):
                    curated = PACKAGE_ROOTS[package] / "records" / filename
                    accepted = VALID_FIXTURES / filename
                    self.assertEqual(accepted.read_bytes(), curated.read_bytes())
                    self.assertEqual(
                        expected_sha256,
                        hashlib.sha256(curated.read_bytes()).hexdigest(),
                    )

    def test_registration_module_is_the_only_red_predecessor(self) -> None:
        self.assertIsNotNone(
            registration,
            "J2-F1 intentionally precedes semantic_packages/registration.py; "
            f"observed {REGISTRATION_IMPORT_ERROR!r}",
        )


@unittest.skipIf(
    registration is None,
    "J2-F1 freezes the contract before semantic_packages.registration exists",
)
class StackPackageRegistrationContractTest(unittest.TestCase):
    def _copy_roots(self, raw: str, package: str) -> tuple[Path, Path]:
        base = Path(raw)
        theory = base / "theory"
        package_root = base / package
        shutil.copytree(THEORY_ROOT, theory)
        shutil.copytree(PACKAGE_ROOTS[package], package_root)
        return theory, package_root

    def _inspect(self, theory: Path, package_root: Path, package: str):
        return registration.inspect_stack_package(theory, package_root, package)

    @staticmethod
    def _codes(observation) -> list[str]:
        return [diagnostic.code for diagnostic in observation.diagnostics]

    @staticmethod
    def _formatted(observation) -> str:
        return "\n".join(
            diagnostic.format() for diagnostic in observation.diagnostics
        )

    @staticmethod
    def _signatures(observation) -> list[str]:
        return [
            diagnostic.format().split(": ", 1)[0]
            for diagnostic in observation.diagnostics
        ]

    def test_exact_immutable_inventories_digests_roles_and_shape(self) -> None:
        for package in ("rust", "typescript"):
            with self.subTest(package=package):
                observation = self._inspect(
                    THEORY_ROOT, PACKAGE_ROOTS[package], package
                )
                self.assertTrue(observation.ok, self._formatted(observation))
                self.assertEqual(package, observation.package)
                self.assertIsInstance(observation.records, tuple)
                self.assertIsInstance(observation.diagnostics, tuple)
                self.assertEqual(
                    {"package", "records", "diagnostics"},
                    set(vars(observation)),
                )
                self.assertFalse(hasattr(observation, "assurance"))
                self.assertFalse(hasattr(observation, "campaign_reproduced"))
                actual = [
                    (record.address, record.path, record.sha256, record.role)
                    for record in observation.records
                ]
                self.assertEqual(_expected_inventory(package), actual)
                for record in observation.records:
                    self.assertEqual(
                        {"address", "path", "sha256", "role"},
                        set(vars(record)),
                    )
                with self.assertRaises((AttributeError, TypeError)):
                    observation.package = "changed"
                with self.assertRaises((AttributeError, TypeError)):
                    observation.records[0].role = "changed"

    def test_each_package_is_an_independent_union_with_theory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-independent-") as raw:
            theory = Path(raw) / "theory"
            rust = Path(raw) / "rust"
            typescript = Path(raw) / "typescript"
            shutil.copytree(THEORY_ROOT, theory)
            shutil.copytree(PACKAGE_ROOTS["rust"], rust)
            shutil.copytree(PACKAGE_ROOTS["typescript"], typescript)
            (typescript / "records" / "stack-typescript-realization.json").write_text(
                "{ malformed\n", encoding="utf-8"
            )

            rust_observation = self._inspect(theory, rust, "rust")

            shutil.rmtree(rust)
            shutil.copytree(PACKAGE_ROOTS["typescript"], typescript, dirs_exist_ok=True)
            typescript_observation = self._inspect(theory, typescript, "typescript")

        self.assertTrue(rust_observation.ok, self._formatted(rust_observation))
        self.assertTrue(
            typescript_observation.ok,
            self._formatted(typescript_observation),
        )

    def test_explicit_package_selector_governs_instead_of_root_basename(self) -> None:
        attacks = (
            (
                "typescript",
                PACKAGE_ROOTS["rust"],
                "(realization, stack-typescript, 0.1.0)",
                "(realization, stack-rust, 0.1.0)",
            ),
            (
                "rust",
                PACKAGE_ROOTS["typescript"],
                "(realization, stack-rust, 0.1.0)",
                "(realization, stack-typescript, 0.1.0)",
            ),
        )
        for package, package_root, missing, unexpected in attacks:
            with self.subTest(package=package, root=package_root.name):
                observation = self._inspect(THEORY_ROOT, package_root, package)

                self.assertEqual(package, observation.package)
                self.assertFalse(observation.ok)
                self.assertIn("REGISTRATION_MISSING_ADDRESS", self._codes(observation))
                self.assertIn("REGISTRATION_UNEXPECTED_ADDRESS", self._codes(observation))
                rendered = self._formatted(observation)
                self.assertIn(missing, rendered)
                self.assertIn(unexpected, rendered)

    def test_unknown_selector_is_total_without_observing_supplied_roots(self) -> None:
        selector = "unknown-package"
        theory = Path("/j2-unknown-selector-theory-must-not-be-observed")
        package_root = Path("/j2-unknown-selector-package-must-not-be-observed")
        touched: list[str] = []

        def reject(name: str):
            def fail(*_args, **_kwargs):
                touched.append(name)
                raise AssertionError(
                    f"unknown selector attempted finite-source/root I/O via {name}"
                )

            return fail

        boundaries = [
            (builtins, "open"),
            (os, "open"),
            (os, "lstat"),
            (os, "stat"),
            (os, "scandir"),
            (os, "listdir"),
            (os, "readlink"),
            (Path, "open"),
            (Path, "read_bytes"),
            (Path, "read_text"),
        ]
        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.object(
                    finite_source,
                    "_observe_finite_source",
                    side_effect=reject("finite-source observation"),
                )
            )
            for owner, name in boundaries:
                stack.enter_context(
                    mock.patch.object(owner, name, side_effect=reject(name))
                )

            observation = self._inspect(theory, package_root, selector)

        self.assertEqual([], touched)
        self.assertEqual(selector, observation.package)
        self.assertEqual((), observation.records)
        self.assertEqual(
            [
                "REGISTRATION_UNKNOWN_SELECTOR .#: "
                "no Stack package registration selector for 'unknown-package'"
            ],
            [diagnostic.format() for diagnostic in observation.diagnostics],
        )

    def test_mixed_obsolete_historical_and_other_package_records_are_exposed(self) -> None:
        attacks = [
            (
                "other-package",
                [VALID_FIXTURES / "stack-typescript-realization.json"],
                ["(realization, stack-typescript, 0.1.0)"],
            ),
            (
                "obsolete-reference",
                [VALID_FIXTURES / "stack-reference-realization-0.2.0.json"],
                ["(realization, stack-reference, 0.2.0)"],
            ),
            (
                "historical-fixture-only",
                [
                    HISTORICAL_FIXTURES / "realization.json",
                    HISTORICAL_FIXTURES / "claim.json",
                    HISTORICAL_FIXTURES / "evidence.json",
                ],
                [
                    "(realization, stack-reference, 0.1.0)",
                    "(claim, stack-reference-persistence, 0.1.0)",
                    "(evidence, stack-reference-persistence-test, 0.1.0)",
                ],
            ),
        ]
        for name, sources, addresses in attacks:
            with self.subTest(name=name), tempfile.TemporaryDirectory(
                prefix=f"j2-mixed-{name}-"
            ) as raw:
                theory, package_root = self._copy_roots(raw, "rust")
                for index, source in enumerate(sources):
                    shutil.copyfile(
                        source,
                        package_root / "records" / f"unexpected-{index}.json",
                    )
                observation = self._inspect(theory, package_root, "rust")

                self.assertFalse(observation.ok)
                self.assertIn("REGISTRATION_UNEXPECTED_ADDRESS", self._codes(observation))
                rendered = self._formatted(observation)
                for address in addresses:
                    self.assertIn(address, rendered)

    def test_missing_realization_claim_and_evidence_survive_unrelated_graph_errors(self) -> None:
        attacks = [
            ("stack-rust-realization.json", "(realization, stack-rust, 0.1.0)"),
            ("stack-rust-pop-empty-claim.json", "(claim, stack-rust-pop-empty, 0.1.0)"),
            ("stack-rust-pop-empty-evidence.json", "(evidence, stack-rust-pop-empty-conformance, 0.1.0)"),
        ]
        for filename, address in attacks:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory(
                prefix="j2-missing-"
            ) as raw:
                theory, package_root = self._copy_roots(raw, "rust")
                (package_root / "records" / filename).unlink()
                shutil.copyfile(
                    package_root / "records" / "stack-rust-pop-push-claim.json",
                    package_root / "records" / "duplicate-pop-push-claim.json",
                )
                observation = self._inspect(theory, package_root, "rust")

                self.assertFalse(observation.ok)
                self.assertIn("REGISTRATION_MISSING_ADDRESS", self._codes(observation))
                self.assertIn("LINK_DUPLICATE_ADDRESS", self._codes(observation))
                self.assertIn(address, self._formatted(observation))

    def test_theory_dependencies_cannot_be_missing_or_digest_drifted(self) -> None:
        attacks = [
            (
                "records/stack-spec.json",
                "(specification, stack, 0.1.0)",
            ),
            (
                "records/pop-empty-spec-claim.json",
                "(claim, stack-pop-empty-law, 0.1.0)",
            ),
            (
                "records/stack-pop-empty-model-proof-evidence.json",
                "(evidence, stack-pop-empty-model-proof, 0.1.0)",
            ),
            (
                "dependencies/stack-profile.json",
                "(realizationProfile, stack-default, 0.1.0)",
            ),
        ]
        for relative, address in attacks:
            with self.subTest(case="missing", relative=relative), tempfile.TemporaryDirectory(
                prefix="j2-theory-missing-"
            ) as raw:
                theory, package_root = self._copy_roots(raw, "rust")
                (theory / relative).unlink()
                observation = self._inspect(theory, package_root, "rust")

                self.assertFalse(observation.ok)
                self.assertIn("REGISTRATION_MISSING_ADDRESS", self._codes(observation))
                self.assertIn(address, self._formatted(observation))
                self.assertNotIn(
                    address,
                    [
                        f"({', '.join(record.address)})"
                        for record in observation.records
                    ],
                )

            with self.subTest(case="drift", relative=relative), tempfile.TemporaryDirectory(
                prefix="j2-theory-drift-"
            ) as raw:
                theory, package_root = self._copy_roots(raw, "rust")
                path = theory / relative
                record = json.loads(path.read_text(encoding="utf-8"))
                if record["kind"] == "specification":
                    record["laws"][0]["statement"] += " Schema-valid drift."
                elif record["kind"] == "claim":
                    record["scope"] += " Schema-valid drift."
                elif record["kind"] == "evidence":
                    record["exclusions"].append("Schema-valid drift.")
                else:
                    record["scale"] += " with schema-valid drift"
                _write_json(path, record)
                observation = self._inspect(theory, package_root, "rust")

                self.assertFalse(observation.ok)
                self.assertIn(
                    "REGISTRATION_SOURCE_DIGEST_MISMATCH",
                    self._codes(observation),
                )
                self.assertIn(f"theory/{relative}", self._formatted(observation))

    def test_duplicate_and_wrong_exact_version_fail_stably(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-duplicate-") as raw:
            theory, package_root = self._copy_roots(raw, "rust")
            shutil.copyfile(
                package_root / "records" / "stack-rust-realization.json",
                package_root / "records" / "duplicate-realization.json",
            )
            duplicate = self._inspect(theory, package_root, "rust")

        self.assertFalse(duplicate.ok)
        self.assertIn("LINK_DUPLICATE_ADDRESS", self._codes(duplicate))

        with tempfile.TemporaryDirectory(prefix="j2-version-") as raw:
            theory, package_root = self._copy_roots(raw, "rust")
            path = package_root / "records" / "stack-rust-realization.json"
            realization = json.loads(path.read_text(encoding="utf-8"))
            realization["version"] = "0.1.1"
            _write_json(path, realization)
            wrong_version = self._inspect(theory, package_root, "rust")

        self.assertFalse(wrong_version.ok)
        self.assertIn("LINK_VERSION_MISMATCH", self._codes(wrong_version))
        self.assertIn("REGISTRATION_MISSING_ADDRESS", self._codes(wrong_version))
        self.assertIn(
            "(realization, stack-rust, 0.1.0)",
            self._formatted(wrong_version),
        )

    def test_schema_valid_mutation_of_every_package_record_fails_digest_binding(self) -> None:
        for package, inventory in PACKAGE_INVENTORIES.items():
            for address, filename, _sha256 in inventory:
                with self.subTest(package=package, address=address), tempfile.TemporaryDirectory(
                    prefix="j2-drift-"
                ) as raw:
                    theory, package_root = self._copy_roots(raw, package)
                    path = package_root / "records" / filename
                    record = json.loads(path.read_text(encoding="utf-8"))
                    if record["kind"] == "realization":
                        record["limitations"].append(
                            "Schema-valid mutation outside the accepted W4 packet."
                        )
                    elif record["kind"] == "claim":
                        record["scope"] += " Schema-valid mutation."
                    else:
                        record["exclusions"].append(
                            "Schema-valid mutation outside the accepted W4 packet."
                        )
                    _write_json(path, record)

                    observation = self._inspect(theory, package_root, package)

                    self.assertFalse(observation.ok)
                    self.assertIn(
                        "REGISTRATION_SOURCE_DIGEST_MISMATCH",
                        self._codes(observation),
                    )
                    self.assertIn(
                        f"package/records/{filename}",
                        self._formatted(observation),
                    )

    def test_report_only_and_added_performance_claim_do_not_manufacture_evidence(self) -> None:
        for package in ("rust", "typescript"):
            with self.subTest(package=package), tempfile.TemporaryDirectory(
                prefix="j2-report-only-"
            ) as raw:
                theory, package_root = self._copy_roots(raw, package)
                for path in (package_root / "records").glob("*-evidence.json"):
                    path.unlink()
                shutil.copyfile(
                    ROOT / "evidence" / "wave4" / f"{package}-campaign-report.json",
                    package_root / "campaign-report.txt",
                )
                report_only = self._inspect(theory, package_root, package)

                self.assertFalse(report_only.ok)
                missing = [
                    diagnostic
                    for diagnostic in report_only.diagnostics
                    if diagnostic.code == "REGISTRATION_MISSING_ADDRESS"
                ]
                self.assertEqual(4, len(missing))
                self.assertFalse(
                    any(
                        record.path == "package/campaign-report.txt"
                        for record in report_only.records
                    )
                )

            with self.subTest(package=f"{package}-performance"), tempfile.TemporaryDirectory(
                prefix="j2-performance-"
            ) as raw:
                theory, package_root = self._copy_roots(raw, package)
                prefix = "stack-rust" if package == "rust" else "stack-typescript"
                source = package_root / "records" / f"{prefix}-pop-empty-claim.json"
                performance = json.loads(source.read_text(encoding="utf-8"))
                performance["id"] = f"{prefix}-amortized-o1"
                performance["proposition"]["declarationId"] = "amortized-o1"
                performance["concern"] = "performance"
                performance["scope"] = "No performance Evidence is registered by J2."
                _write_json(
                    package_root / "records" / "unexpected-performance-claim.json",
                    performance,
                )
                added_performance = self._inspect(theory, package_root, package)

                self.assertFalse(added_performance.ok)
                self.assertIn(
                    "REGISTRATION_UNEXPECTED_ADDRESS",
                    self._codes(added_performance),
                )
                self.assertIn(
                    f"(claim, {prefix}-amortized-o1, 0.1.0)",
                    self._formatted(added_performance),
                )
                self.assertFalse(hasattr(added_performance, "performance_unknown"))

    def test_byte_preserving_rename_changes_only_logical_provenance_path(self) -> None:
        for package in ("rust", "typescript"):
            prefix = "stack-rust" if package == "rust" else "stack-typescript"
            attacks = [
                (
                    f"{prefix}-realization.json",
                    ("realization", prefix, "0.1.0"),
                    "implementation-record.json",
                ),
                (
                    f"{prefix}-pop-empty-claim.json",
                    ("claim", f"{prefix}-pop-empty", "0.1.0"),
                    "claim-record.json",
                ),
                (
                    f"{prefix}-pop-empty-evidence.json",
                    ("evidence", f"{prefix}-pop-empty-conformance", "0.1.0"),
                    "evidence-record.json",
                ),
            ]
            for filename, address, renamed_filename in attacks:
                with self.subTest(package=package, address=address), tempfile.TemporaryDirectory(
                    prefix="j2-rename-"
                ) as raw:
                    theory, package_root = self._copy_roots(raw, package)
                    original = package_root / "records" / filename
                    renamed = package_root / "records" / renamed_filename
                    original.rename(renamed)

                    observation = self._inspect(theory, package_root, package)

                    self.assertTrue(observation.ok, self._formatted(observation))
                    observed = next(
                        record
                        for record in observation.records
                        if record.address == address
                    )
                    self.assertEqual(
                        f"package/records/{renamed_filename}",
                        observed.path,
                    )

    def test_every_theory_record_accepts_a_byte_preserving_rename(self) -> None:
        attacks = [
            (
                "records/stack-spec.json",
                ("specification", "stack", "0.1.0"),
                "records/renamed-specification.json",
            ),
            (
                "records/pop-empty-spec-claim.json",
                ("claim", "stack-pop-empty-law", "0.1.0"),
                "records/renamed-claim.json",
            ),
            (
                "records/stack-pop-empty-model-proof-evidence.json",
                ("evidence", "stack-pop-empty-model-proof", "0.1.0"),
                "records/renamed-evidence.json",
            ),
            (
                "dependencies/stack-profile.json",
                ("realizationProfile", "stack-default", "0.1.0"),
                "dependencies/renamed-profile.json",
            ),
        ]
        for original_relative, address, renamed_relative in attacks:
            with self.subTest(address=address), tempfile.TemporaryDirectory(
                prefix="j2-theory-rename-"
            ) as raw:
                theory, package_root = self._copy_roots(raw, "rust")
                (theory / original_relative).rename(theory / renamed_relative)

                observation = self._inspect(theory, package_root, "rust")

                self.assertTrue(observation.ok, self._formatted(observation))
                observed = next(
                    record for record in observation.records if record.address == address
                )
                self.assertEqual(f"theory/{renamed_relative}", observed.path)

    def test_theory_roles_remain_address_owned_across_directory_renames(self) -> None:
        renames = {
            ("realizationProfile", "stack-default", "0.1.0"): (
                "dependencies/stack-profile.json",
                "records/renamed-profile.json",
            ),
            ("specification", "stack", "0.1.0"): (
                "records/stack-spec.json",
                "dependencies/renamed-specification.json",
            ),
        }
        expected_roles = {
            address: role
            for address, _path, _sha256, role in THEORY_INVENTORY
        }
        with tempfile.TemporaryDirectory(
            prefix="j2-theory-cross-directory-rename-"
        ) as raw:
            theory, package_root = self._copy_roots(raw, "rust")
            for original_relative, renamed_relative in renames.values():
                (theory / original_relative).rename(theory / renamed_relative)

            observation = self._inspect(theory, package_root, "rust")

        self.assertTrue(observation.ok, self._formatted(observation))
        self.assertEqual(13, len(observation.records))
        observed_theory = {
            record.address: record
            for record in observation.records
            if record.address in expected_roles
        }
        self.assertEqual(
            expected_roles,
            {address: record.role for address, record in observed_theory.items()},
        )
        for address, (_original_relative, renamed_relative) in renames.items():
            self.assertEqual(
                f"theory/{renamed_relative}",
                observed_theory[address].path,
            )

    def test_exact_records_cannot_cross_theory_and_package_root_ownership(self) -> None:
        issues: list[str] = []

        def exercise(
            package: str,
            address: tuple[str, str, str],
            sha256: str,
            expected_role: str,
            source_owner: str,
            source_relative: str,
            destination_relative: str,
        ) -> None:
            with tempfile.TemporaryDirectory(
                prefix=f"j2-cross-root-{package}-"
            ) as raw:
                theory, package_root = self._copy_roots(raw, package)
                roots = {"theory": theory, "package": package_root}
                destination_owner = (
                    "package" if source_owner == "theory" else "theory"
                )
                source = roots[source_owner] / source_relative
                destination = roots[destination_owner] / destination_relative
                exact_bytes = source.read_bytes()
                source.rename(destination)
                moved_bytes = destination.read_bytes()

                observation = self._inspect(theory, package_root, package)

            case = f"{package}:{source_owner}->{destination_owner}:{address}"
            moved_path = f"{destination_owner}/{destination_relative}"
            if exact_bytes != moved_bytes:
                issues.append(f"{case}: move changed exact bytes")
            if hashlib.sha256(moved_bytes).hexdigest() != sha256:
                issues.append(f"{case}: move changed the frozen SHA-256")

            expected_addresses = {
                item_address
                for item_address, _path, _sha256, _role in _expected_inventory(package)
            }
            observed_addresses = {record.address for record in observation.records}
            if observed_addresses != expected_addresses:
                issues.append(
                    f"{case}: explanatory inventory addresses changed: "
                    f"{sorted(observed_addresses)}"
                )
            if len(observation.records) != 13:
                issues.append(
                    f"{case}: explanatory inventory has {len(observation.records)} "
                    "records instead of 13"
                )

            moved_records = [
                record for record in observation.records if record.address == address
            ]
            if len(moved_records) != 1:
                issues.append(
                    f"{case}: expected one explanatory record, got {len(moved_records)}"
                )
            elif (
                moved_records[0].path != moved_path
                or moved_records[0].sha256 != sha256
            ):
                issues.append(
                    f"{case}: moved record provenance is "
                    f"{(moved_records[0].path, moved_records[0].sha256)!r}"
                )
            if len(moved_records) == 1 and moved_records[0].role != expected_role:
                issues.append(
                    f"{case}: exact address-owned role changed from "
                    f"{expected_role!r} to {moved_records[0].role!r}"
                )

            address_text = f"({', '.join(address)})"
            expected_diagnostics = [
                "REGISTRATION_MISSING_ADDRESS .#: Stack package registration "
                f"requires {address_text}",
                f"REGISTRATION_UNEXPECTED_ADDRESS {moved_path}#: Stack package "
                f"registration does not include {address_text}",
            ]
            actual_diagnostics = [
                diagnostic.format() for diagnostic in observation.diagnostics
            ]
            if observation.ok or actual_diagnostics != expected_diagnostics:
                issues.append(
                    f"{case}: expected root rejection {expected_diagnostics!r}, "
                    f"got ok={observation.ok}, diagnostics={actual_diagnostics!r}"
                )

        for package in ("rust", "typescript"):
            for address, path, sha256, role in THEORY_INVENTORY:
                source_relative = path.removeprefix("theory/")
                destination_relative = (
                    f"records/moved-theory-{address[0]}-{address[1]}.json"
                )
                exercise(
                    package,
                    address,
                    sha256,
                    role,
                    "theory",
                    source_relative,
                    destination_relative,
                )

            for address, filename, sha256 in PACKAGE_INVENTORIES[package]:
                exercise(
                    package,
                    address,
                    sha256,
                    "package-authored",
                    "package",
                    f"records/{filename}",
                    f"records/moved-package-{filename}",
                )

        self.assertEqual([], issues, "\n".join(issues))

    def test_leaf_known_nested_and_unknown_symlinks_reject_without_following(self) -> None:
        attacks = ("leaf", "known-directory", "nested-directory", "unknown-directory")
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory(
                prefix=f"j2-symlink-{attack}-"
            ) as raw:
                theory, package_root = self._copy_roots(raw, "rust")
                outside = Path(raw) / f"outside-{attack}"
                if attack == "leaf":
                    target = package_root / "records" / "stack-rust-realization.json"
                    target.unlink()
                    target.symlink_to(VALID_FIXTURES / "stack-rust-realization.json")
                    expected = "INPUT_SYMLINK package/records/stack-rust-realization.json#"
                elif attack == "known-directory":
                    records = package_root / "records"
                    records.rename(outside)
                    records.symlink_to(outside, target_is_directory=True)
                    expected = "INPUT_SYMLINK package/records#"
                else:
                    outside.mkdir()
                    shutil.copyfile(
                        VALID_FIXTURES / "stack-typescript-realization.json",
                        outside / "hidden.json",
                    )
                    if attack == "nested-directory":
                        target = package_root / "records" / "hidden"
                        expected = "INPUT_SYMLINK package/records/hidden#"
                    else:
                        target = package_root / "unknown"
                        expected = "INPUT_SYMLINK package/unknown#"
                    target.symlink_to(outside, target_is_directory=True)

                observation = self._inspect(theory, package_root, "rust")

                self.assertFalse(observation.ok)
                self.assertEqual([expected], self._signatures(observation))

    def test_malformed_input_preserves_the_input_schema_phase_barrier(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-malformed-") as raw:
            theory, package_root = self._copy_roots(raw, "rust")
            malformed = package_root / "records" / "stack-rust-realization.json"
            malformed.write_text("{ malformed\n", encoding="utf-8")
            shutil.copyfile(
                VALID_FIXTURES / "stack-typescript-realization.json",
                package_root / "records" / "unexpected-typescript.json",
            )

            observation = self._inspect(theory, package_root, "rust")

        self.assertFalse(observation.ok)
        self.assertEqual(
            ["INPUT_INVALID_JSON package/records/stack-rust-realization.json#"],
            self._signatures(observation),
        )
        self.assertNotIn("REGISTRATION_MISSING_ADDRESS", self._codes(observation))
        self.assertNotIn("REGISTRATION_UNEXPECTED_ADDRESS", self._codes(observation))

    def test_inspection_executes_no_entrypoint_campaign_or_process_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j2-no-exec-") as raw:
            theory, package_root = self._copy_roots(raw, "rust")
            marker = Path(raw) / "execution-marker"
            executable = Path(raw) / "entrypoint"
            executable.write_text(
                f"#!/bin/sh\ntouch {marker}\nexit 1\n", encoding="utf-8"
            )
            executable.chmod(0o755)
            realization_path = package_root / "records" / "stack-rust-realization.json"
            realization = json.loads(realization_path.read_text(encoding="utf-8"))
            realization["adapter"]["entrypoint"] = str(executable)
            realization["implementation"]["executionInstructions"] = str(executable)
            _write_json(realization_path, realization)

            launches: list[str] = []

            def reject_launch(name: str):
                def reject(*_args, **_kwargs):
                    launches.append(name)
                    raise AssertionError(f"inspection attempted process launch via {name}")

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
                    if hasattr(registration, name):
                        stack.enter_context(
                            mock.patch.object(
                                registration,
                                name,
                                side_effect=reject_launch(f"registration.{name}"),
                            )
                        )
                observation = self._inspect(theory, package_root, "rust")

            self.assertFalse(marker.exists())
            self.assertEqual([], launches)

        self.assertFalse(observation.ok)
        self.assertIn(
            "REGISTRATION_SOURCE_DIGEST_MISMATCH",
            self._codes(observation),
        )

    def test_unchanged_accepted_packages_execute_no_canonical_entrypoint(self) -> None:
        launches: list[str] = []

        def reject_launch(name: str):
            def reject(*_args, **_kwargs):
                launches.append(name)
                raise AssertionError(
                    f"inspection attempted canonical process launch via {name}"
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
                if hasattr(registration, name):
                    stack.enter_context(
                        mock.patch.object(
                            registration,
                            name,
                            side_effect=reject_launch(f"registration.{name}"),
                        )
                    )
            observations = [
                self._inspect(THEORY_ROOT, PACKAGE_ROOTS[package], package)
                for package in ("rust", "typescript")
            ]

        self.assertEqual([], launches)
        for observation in observations:
            self.assertTrue(observation.ok, self._formatted(observation))


if __name__ == "__main__":
    unittest.main()
