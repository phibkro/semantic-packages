from __future__ import annotations

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
THEORY_SOURCE_SET = ROOT / "registry" / "stack" / "theory"
MIXED_FIXTURE_TREE = ROOT / "fixtures" / "records" / "valid"

try:
    publication = importlib.import_module("semantic_packages.publication")
    PUBLICATION_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.publication":
        raise
    publication = None
    PUBLICATION_IMPORT_ERROR = error


EXPECTED_INVENTORY = [
    (
        ("claim", "stack-pop-empty-law", "0.1.0"),
        "records/pop-empty-spec-claim.json",
        "f3de2c39a1ecf85865aaff3dead75d55b76807e02d8a9b61d358a8f5688c3b6a",
        "authored",
    ),
    (
        ("evidence", "stack-pop-empty-model-proof", "0.1.0"),
        "records/stack-pop-empty-model-proof-evidence.json",
        "7813247dad2d138295eb8e868eca2f81168d08654d4dd6ce253542470e11ef90",
        "authored",
    ),
    (
        ("realizationProfile", "stack-default", "0.1.0"),
        "dependencies/stack-profile.json",
        "2a51ed7d2e1266376cd4a58ef3f20d30244655d25cb884816576be989014eddb",
        "dependency",
    ),
    (
        ("specification", "stack", "0.1.0"),
        "records/stack-spec.json",
        "dd083a71a4631cc44be051a16b8e20ff0cee7199e46d3823322665d1fdeec6c1",
        "authored",
    ),
]


def _write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class PublicationAvailabilityTest(unittest.TestCase):
    def test_publication_module_is_the_only_red_predecessor(self) -> None:
        self.assertIsNotNone(
            publication,
            "J1-F1 intentionally precedes semantic_packages/publication.py; "
            f"observed {PUBLICATION_IMPORT_ERROR!r}",
        )


@unittest.skipIf(
    publication is None,
    "J1-F1 freezes the contract before semantic_packages.publication exists",
)
class StackTheoryPublicationContractTest(unittest.TestCase):
    def _copy_source_set(self, raw: str) -> Path:
        destination = Path(raw) / "theory"
        shutil.copytree(THEORY_SOURCE_SET, destination)
        return destination

    def _inspect(self, root: Path):
        return publication.inspect_stack_theory(root)

    def _codes(self, observation) -> list[str]:
        return [diagnostic.code for diagnostic in observation.diagnostics]

    def _formatted(self, observation) -> str:
        return "\n".join(diagnostic.format() for diagnostic in observation.diagnostics)

    def _signatures(self, observation) -> list[str]:
        return [
            diagnostic.format().split(": ", 1)[0]
            for diagnostic in observation.diagnostics
        ]

    def test_exact_inventory_digests_and_roles(self) -> None:
        observation = self._inspect(THEORY_SOURCE_SET)

        self.assertTrue(observation.ok, self._formatted(observation))
        actual = [
            (record.address, record.path, record.sha256, record.role)
            for record in observation.records
        ]
        self.assertEqual(actual, EXPECTED_INVENTORY)

    def test_mixed_fixture_tree_exposes_obsolete_support(self) -> None:
        observation = self._inspect(MIXED_FIXTURE_TREE)

        self.assertFalse(observation.ok)
        self.assertIn("PUBLICATION_UNEXPECTED_ADDRESS", self._codes(observation))
        rendered = self._formatted(observation)
        for address in (
            "(realization, stack-reference, 0.1.0)",
            "(claim, stack-reference-persistence, 0.1.0)",
            "(evidence, stack-reference-persistence-test, 0.1.0)",
        ):
            self.assertIn(address, rendered)

    def test_malformed_json_is_rejected_stably(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-malformed-") as raw:
            source_set = self._copy_source_set(raw)
            (source_set / "records" / "stack-spec.json").write_text(
                "{ malformed\n", encoding="utf-8"
            )

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            ["INPUT_INVALID_JSON records/stack-spec.json#"],
        )

    def test_duplicate_exact_address_is_rejected_stably(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-duplicate-") as raw:
            source_set = self._copy_source_set(raw)
            shutil.copyfile(
                source_set / "records" / "stack-spec.json",
                source_set / "records" / "duplicate-stack-spec.json",
            )

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            ["LINK_DUPLICATE_ADDRESS records/stack-spec.json#"],
        )

    def test_dangling_claim_is_rejected_stably(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-dangling-claim-") as raw:
            source_set = self._copy_source_set(raw)
            (source_set / "records" / "pop-empty-spec-claim.json").unlink()

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "LINK_DANGLING_REFERENCE "
                "records/stack-pop-empty-model-proof-evidence.json#/claim"
            ],
        )

    def test_dangling_profile_is_rejected_stably(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-dangling-profile-") as raw:
            source_set = self._copy_source_set(raw)
            (source_set / "dependencies" / "stack-profile.json").unlink()

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "LINK_DANGLING_REFERENCE "
                "records/stack-spec.json#/performancePropositions/0/"
                "costMeasure/profile",
                "LINK_DANGLING_REFERENCE "
                "records/stack-spec.json#/performancePropositions/0/"
                "workload/profile",
            ],
        )

    def test_wrong_exact_version_is_rejected_stably(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-version-") as raw:
            source_set = self._copy_source_set(raw)
            profile_path = source_set / "dependencies" / "stack-profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["version"] = "0.1.1"
            _write_json(profile_path, profile)

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "LINK_VERSION_MISMATCH "
                "records/stack-spec.json#/performancePropositions/0/"
                "costMeasure/profile",
                "LINK_VERSION_MISMATCH "
                "records/stack-spec.json#/performancePropositions/0/"
                "workload/profile",
            ],
        )

    def test_semantic_drift_is_rejected_against_proof_input_digest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-proof-drift-") as raw:
            source_set = self._copy_source_set(raw)
            specification_path = source_set / "records" / "stack-spec.json"
            specification = json.loads(
                specification_path.read_text(encoding="utf-8")
            )
            specification["laws"][0]["statement"] = "pop(empty) != None"
            _write_json(specification_path, specification)

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "PUBLICATION_PROOF_INPUT_DIGEST_MISMATCH "
                "records/stack-spec.json#"
            ],
        )
        self.assertIn(
            "(specification, stack, 0.1.0)", self._formatted(observation)
        )

    def test_claim_drift_is_rejected_against_proof_input_digest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-claim-drift-") as raw:
            source_set = self._copy_source_set(raw)
            claim_path = source_set / "records" / "pop-empty-spec-claim.json"
            claim = json.loads(claim_path.read_text(encoding="utf-8"))
            claim["scope"] = "A changed but schema-valid scope for the named law."
            _write_json(claim_path, claim)

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "PUBLICATION_PROOF_INPUT_DIGEST_MISMATCH "
                "records/pop-empty-spec-claim.json#"
            ],
        )
        self.assertIn(
            "(claim, stack-pop-empty-law, 0.1.0)", self._formatted(observation)
        )

    def test_proof_evidence_drift_is_rejected_against_curated_source_digest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-evidence-drift-") as raw:
            source_set = self._copy_source_set(raw)
            evidence_path = (
                source_set
                / "records"
                / "stack-pop-empty-model-proof-evidence.json"
            )
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["exclusions"].append(
                "A schema-valid mutation that was not part of the accepted record."
            )
            _write_json(evidence_path, evidence)

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "PUBLICATION_SOURCE_DIGEST_MISMATCH "
                "records/stack-pop-empty-model-proof-evidence.json#"
            ],
        )
        self.assertIn(
            "(evidence, stack-pop-empty-model-proof, 0.1.0)",
            self._formatted(observation),
        )

    def test_supplied_profile_drift_is_rejected_against_curated_source_digest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-profile-drift-") as raw:
            source_set = self._copy_source_set(raw)
            profile_path = source_set / "dependencies" / "stack-profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["scale"] = "A changed but schema-valid execution scale."
            _write_json(profile_path, profile)

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "PUBLICATION_SOURCE_DIGEST_MISMATCH "
                "dependencies/stack-profile.json#"
            ],
        )
        self.assertIn(
            "(realizationProfile, stack-default, 0.1.0)",
            self._formatted(observation),
        )

    def test_consumer_policy_is_not_theory_author_owned(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-policy-") as raw:
            source_set = self._copy_source_set(raw)
            shutil.copyfile(
                MIXED_FIXTURE_TREE / "stack-policy.json",
                source_set / "records" / "stack-policy.json",
            )

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertIn("PUBLICATION_UNEXPECTED_ADDRESS", self._codes(observation))
        self.assertIn(
            "(consumerPolicy, stack-default-policy, 0.1.0)",
            self._formatted(observation),
        )

    def test_consumer_policy_cannot_hide_at_source_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-root-policy-") as raw:
            source_set = self._copy_source_set(raw)
            shutil.copyfile(
                MIXED_FIXTURE_TREE / "stack-policy.json",
                source_set / "stack-policy.json",
            )

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            ["PUBLICATION_UNEXPECTED_ADDRESS stack-policy.json#"],
        )
        self.assertIn(
            "(consumerPolicy, stack-default-policy, 0.1.0)",
            self._formatted(observation),
        )

    def test_consumer_policy_cannot_hide_in_sibling_subtree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-sibling-policy-") as raw:
            source_set = self._copy_source_set(raw)
            sibling = source_set / "consumer-inputs" / "stack-policy.json"
            sibling.parent.mkdir()
            shutil.copyfile(MIXED_FIXTURE_TREE / "stack-policy.json", sibling)

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "PUBLICATION_UNEXPECTED_ADDRESS "
                "consumer-inputs/stack-policy.json#"
            ],
        )
        self.assertIn(
            "(consumerPolicy, stack-default-policy, 0.1.0)",
            self._formatted(observation),
        )

    def test_unrelated_graph_error_does_not_hide_missing_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-missing-and-duplicate-") as raw:
            source_set = self._copy_source_set(raw)
            (
                source_set
                / "records"
                / "stack-pop-empty-model-proof-evidence.json"
            ).unlink()
            shutil.copyfile(
                source_set / "records" / "stack-spec.json",
                source_set / "records" / "duplicate-stack-spec.json",
            )

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "PUBLICATION_MISSING_ADDRESS .#",
                "LINK_DUPLICATE_ADDRESS records/stack-spec.json#",
            ],
        )
        self.assertIn(
            "(evidence, stack-pop-empty-model-proof, 0.1.0)",
            self._formatted(observation),
        )

    def test_schema_valid_unexpected_specification_cannot_escape_allowlist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-unexpected-spec-") as raw:
            source_set = self._copy_source_set(raw)
            unexpected_path = source_set / "records" / "unexpected-spec.json"
            unexpected = json.loads(
                (source_set / "records" / "stack-spec.json").read_text(
                    encoding="utf-8"
                )
            )
            unexpected["id"] = "stack-shadow"
            _write_json(unexpected_path, unexpected)

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            ["PUBLICATION_UNEXPECTED_ADDRESS records/unexpected-spec.json#"],
        )
        self.assertIn(
            "(specification, stack-shadow, 0.1.0)", self._formatted(observation)
        )

    def test_schema_valid_unexpected_profile_cannot_escape_allowlist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-unexpected-profile-") as raw:
            source_set = self._copy_source_set(raw)
            unexpected_path = (
                source_set / "dependencies" / "unexpected-profile.json"
            )
            unexpected = json.loads(
                (source_set / "dependencies" / "stack-profile.json").read_text(
                    encoding="utf-8"
                )
            )
            unexpected["id"] = "stack-shadow-profile"
            _write_json(unexpected_path, unexpected)

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            [
                "PUBLICATION_UNEXPECTED_ADDRESS "
                "dependencies/unexpected-profile.json#"
            ],
        )
        self.assertIn(
            "(realizationProfile, stack-shadow-profile, 0.1.0)",
            self._formatted(observation),
        )

    def test_source_filename_is_provenance_not_record_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-rename-") as raw:
            source_set = self._copy_source_set(raw)
            original = source_set / "records" / "stack-spec.json"
            renamed = source_set / "records" / "theory-source.json"
            original.rename(renamed)

            observation = self._inspect(source_set)

        self.assertTrue(observation.ok, self._formatted(observation))
        specification = next(
            record
            for record in observation.records
            if record.address == ("specification", "stack", "0.1.0")
        )
        self.assertEqual(specification.path, "records/theory-source.json")

    def test_symlinked_curated_source_is_rejected_at_filesystem_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-symlink-") as raw:
            source_set = self._copy_source_set(raw)
            specification_path = source_set / "records" / "stack-spec.json"
            specification_path.unlink()
            specification_path.symlink_to(
                MIXED_FIXTURE_TREE / "stack-spec.json"
            )

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            ["INPUT_SYMLINK records/stack-spec.json#"],
        )

    def test_symlinked_records_component_is_rejected_before_traversal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-directory-symlink-") as raw:
            source_set = self._copy_source_set(raw)
            records = source_set / "records"
            outside_records = Path(raw) / "outside-records"
            records.rename(outside_records)
            records.symlink_to(outside_records, target_is_directory=True)

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            ["INPUT_SYMLINK records#"],
        )

    def test_symlinked_unknown_sibling_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-sibling-directory-symlink-") as raw:
            source_set = self._copy_source_set(raw)
            outside = Path(raw) / "outside-consumer-inputs"
            outside.mkdir()
            shutil.copyfile(
                MIXED_FIXTURE_TREE / "stack-policy.json",
                outside / "stack-policy.json",
            )
            (source_set / "consumer-inputs").symlink_to(
                outside, target_is_directory=True
            )

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            ["INPUT_SYMLINK consumer-inputs#"],
        )

    def test_symlinked_nested_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-nested-directory-symlink-") as raw:
            source_set = self._copy_source_set(raw)
            outside = Path(raw) / "outside-consumer-inputs"
            outside.mkdir()
            shutil.copyfile(
                MIXED_FIXTURE_TREE / "stack-policy.json",
                outside / "stack-policy.json",
            )
            (source_set / "records" / "hidden").symlink_to(
                outside, target_is_directory=True
            )

            observation = self._inspect(source_set)

        self.assertFalse(observation.ok)
        self.assertEqual(
            self._signatures(observation),
            ["INPUT_SYMLINK records/hidden#"],
        )

    def test_inspection_executes_neither_proof_tool_nor_realization(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j1-no-exec-") as raw:
            source_set = self._copy_source_set(raw)
            marker = Path(raw) / "execution-marker"
            fake_lean = Path(raw) / "fake-lean"
            fake_lean.write_text(
                f"#!/bin/sh\ntouch {marker}\nexit 1\n", encoding="utf-8"
            )
            fake_lean.chmod(0o755)

            realization_path = source_set / "records" / "unexpected-realization.json"
            realization = json.loads(
                (MIXED_FIXTURE_TREE / "stack-reference-realization-0.2.0.json").read_text(
                    encoding="utf-8"
                )
            )
            realization["implementation"]["executionInstructions"] = str(fake_lean)
            realization["adapter"]["entrypoint"] = str(fake_lean)
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
                stack.enter_context(mock.patch.dict(os.environ, {"LEAN": str(fake_lean)}))
                for owner, name in boundaries:
                    if hasattr(owner, name):
                        stack.enter_context(
                            mock.patch.object(owner, name, side_effect=reject_launch(name))
                        )
                for name in ("run", "Popen", "system"):
                    if hasattr(publication, name):
                        stack.enter_context(
                            mock.patch.object(
                                publication,
                                name,
                                side_effect=reject_launch(f"publication.{name}"),
                            )
                        )
                observation = self._inspect(source_set)

            self.assertFalse(marker.exists())
            self.assertEqual(launches, [])

        self.assertFalse(observation.ok)
        self.assertIn("PUBLICATION_UNEXPECTED_ADDRESS", self._codes(observation))


if __name__ == "__main__":
    unittest.main()
