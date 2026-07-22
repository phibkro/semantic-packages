from __future__ import annotations

import json
import inspect
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from semantic_packages import graph, publication, registration


ROOT = Path(__file__).resolve().parents[2]
STACK_MANIFEST = ROOT / "registry" / "stack" / "manifest.json"
STACK_THEORY = ROOT / "registry" / "stack" / "theory"
STACK_PACKAGES = ROOT / "registry" / "stack" / "packages"
ORDERED_MAP_PROBE = ROOT / "fixtures" / "research" / "ordered-map"
ORDERED_MAP_RECORDS = ORDERED_MAP_PROBE / "records"
ORDERED_MAP_MANIFEST = ORDERED_MAP_PROBE / "manifest.json"


class ManifestAuthorityExtractionContractTest(unittest.TestCase):
    def test_supplied_authority_is_immutable_and_replays_the_same_graph(self) -> None:
        authority = graph.inspect_manifest_authority(STACK_MANIFEST)

        self.assertTrue(authority.ok, authority.diagnostics)
        self.assertIsInstance(authority.sources, tuple)
        self.assertIsInstance(authority.members, tuple)
        self.assertIsInstance(authority.sources[0].roles, frozenset)
        with self.assertRaises((AttributeError, TypeError)):
            authority.sources[0].root = "attacker-root"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            authority.members[0].sha256 = "0" * 64  # type: ignore[misc]

        shared = graph.inspect_manifest_graph(authority)
        compatible = graph.inspect_stack_graph(STACK_MANIFEST)
        self.assertEqual(compatible, shared)

        with tempfile.TemporaryDirectory(prefix="o4b-authority-snapshot-") as raw:
            copied = Path(raw) / "ordered-map"
            shutil.copytree(ORDERED_MAP_PROBE, copied)
            manifest_path = copied / "manifest.json"
            captured = graph.inspect_manifest_authority(manifest_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["members"][0]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with mock.patch.object(
                graph,
                "_load_manifest",
                side_effect=AssertionError("captured authority reread its manifest"),
            ):
                replay = graph.inspect_manifest_graph(captured)

        self.assertTrue(replay.ok, replay.diagnostics)
        self.assertEqual(
            [("specification", "ordered-map", "0.1.0")],
            [record.address for record in replay.records],
        )

    def test_generic_publication_observes_the_supplied_ordered_map_authority(self) -> None:
        authority = graph.inspect_manifest_authority(ORDERED_MAP_MANIFEST)

        observation = publication.inspect_theory_publication(
            ORDERED_MAP_RECORDS,
            authority=authority,
            source="ordered-map-theory",
            product="OrderedMap probe",
        )

        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(
            [("specification", "ordered-map", "0.1.0")],
            [record.address for record in observation.records],
        )
        self.assertEqual(["authored"], [record.role for record in observation.records])
        for authority_conclusion in (
            "accepted",
            "assurance",
            "product_contract",
            "product_contract_id",
        ):
            self.assertFalse(hasattr(observation, authority_conclusion))

        actor = publication.inspect_stack_theory(ORDERED_MAP_RECORDS)
        self.assertFalse(actor.ok)
        self.assertEqual(
            Counter(
                {
                    "PUBLICATION_MISSING_ADDRESS": 4,
                    "PUBLICATION_UNEXPECTED_ADDRESS": 1,
                }
            ),
            Counter(diagnostic.code for diagnostic in actor.diagnostics),
        )

    def test_stack_wrappers_pin_their_actor_surface_without_authority_arguments(self) -> None:
        positional = inspect.Parameter.POSITIONAL_OR_KEYWORD
        self.assertEqual(
            inspect.Signature(
                [inspect.Parameter("root", positional, annotation="Path")],
                return_annotation="PublicationObservation",
            ),
            inspect.signature(publication.inspect_stack_theory),
        )
        self.assertEqual(
            inspect.Signature(
                [
                    inspect.Parameter("theory_root", positional, annotation="Path"),
                    inspect.Parameter("package_root", positional, annotation="Path"),
                    inspect.Parameter("package", positional, annotation="str"),
                ],
                return_annotation="RegistrationObservation",
            ),
            inspect.signature(registration.inspect_stack_package),
        )
        self.assertEqual(
            inspect.Signature(
                [
                    inspect.Parameter(
                        "manifest_path", positional, annotation="Path"
                    )
                ],
                return_annotation="GraphObservation",
            ),
            inspect.signature(graph.inspect_stack_graph),
        )

        authority = graph.inspect_manifest_authority(STACK_MANIFEST)
        shared_theory = publication.inspect_theory_publication(
            STACK_THEORY,
            authority=authority,
            source="theory",
            product="Stack",
        )
        self.assertEqual(publication.inspect_stack_theory(STACK_THEORY), shared_theory)

        for package in ("rust", "typescript"):
            with self.subTest(package=package):
                shared_package = registration.inspect_package_registration(
                    STACK_THEORY,
                    STACK_PACKAGES / package,
                    package,
                    authority=authority,
                    theory_source="theory",
                    product="Stack",
                )
                self.assertEqual(
                    registration.inspect_stack_package(
                        STACK_THEORY, STACK_PACKAGES / package, package
                    ),
                    shared_package,
                )

        override_attacks = (
            lambda: publication.inspect_stack_theory(
                STACK_THEORY, authority=authority
            ),
            lambda: publication.inspect_stack_theory(STACK_THEORY, source="rust"),
            lambda: publication.inspect_stack_theory(STACK_THEORY, product="Other"),
            lambda: publication.inspect_stack_theory(
                STACK_THEORY, manifest_path=ORDERED_MAP_MANIFEST
            ),
            lambda: registration.inspect_stack_package(
                STACK_THEORY,
                STACK_PACKAGES / "rust",
                "rust",
                authority=authority,
            ),
            lambda: registration.inspect_stack_package(
                STACK_THEORY,
                STACK_PACKAGES / "rust",
                "rust",
                theory_source="rust",
            ),
            lambda: registration.inspect_stack_package(
                STACK_THEORY,
                STACK_PACKAGES / "rust",
                "rust",
                product="Other",
            ),
            lambda: registration.inspect_stack_package(
                STACK_THEORY,
                STACK_PACKAGES / "rust",
                "rust",
                manifest_path=ORDERED_MAP_MANIFEST,
            ),
        )
        for attack in override_attacks:
            with self.assertRaises(TypeError):
                attack()

    def test_unknown_and_wrong_role_selectors_fail_before_source_observation(self) -> None:
        authority = graph.inspect_manifest_authority(STACK_MANIFEST)
        attacks = (
            (
                "publication-unknown",
                lambda: publication.inspect_theory_publication(
                    Path("/must-not-observe"),
                    authority=authority,
                    source="missing",
                    product="Example",
                ),
                "PUBLICATION_UNKNOWN_SOURCE .#: no Example theory publication "
                "source selector for 'missing'",
            ),
            (
                "publication-wrong-role",
                lambda: publication.inspect_theory_publication(
                    Path("/must-not-observe"),
                    authority=authority,
                    source="rust",
                    product="Example",
                ),
                "PUBLICATION_SOURCE_ROLE_MISMATCH .#: Example theory publication "
                "source 'rust' does not permit only theory-authored/dependency roles",
            ),
            (
                "registration-unknown-theory",
                lambda: registration.inspect_package_registration(
                    Path("/must-not-observe-theory"),
                    Path("/must-not-observe-package"),
                    "rust",
                    authority=authority,
                    theory_source="missing",
                    product="Example",
                ),
                "REGISTRATION_UNKNOWN_THEORY_SOURCE .#: no Example theory source "
                "selector for 'missing'",
            ),
            (
                "registration-wrong-theory-role",
                lambda: registration.inspect_package_registration(
                    Path("/must-not-observe-theory"),
                    Path("/must-not-observe-package"),
                    "rust",
                    authority=authority,
                    theory_source="rust",
                    product="Example",
                ),
                "REGISTRATION_THEORY_SOURCE_ROLE_MISMATCH .#: Example theory source "
                "'rust' does not permit only theory-authored/dependency roles",
            ),
            (
                "registration-wrong-package-role",
                lambda: registration.inspect_package_registration(
                    Path("/must-not-observe-theory"),
                    Path("/must-not-observe-package"),
                    "theory",
                    authority=authority,
                    theory_source="theory",
                    product="Example",
                ),
                "REGISTRATION_PACKAGE_SOURCE_ROLE_MISMATCH .#: Example package "
                "source 'theory' does not permit only package-authored roles",
            ),
            (
                "registration-unknown-package",
                lambda: registration.inspect_package_registration(
                    Path("/must-not-observe-theory"),
                    Path("/must-not-observe-package"),
                    "missing",
                    authority=authority,
                    theory_source="theory",
                    product="Example",
                ),
                "REGISTRATION_UNKNOWN_PACKAGE_SOURCE .#: no Example package source "
                "selector for 'missing'",
            ),
        )

        with mock.patch.object(
            graph._finite_source,
            "_observe_finite_source",
            side_effect=AssertionError("selector attack observed roots"),
        ):
            for name, attack, expected in attacks:
                with self.subTest(name=name):
                    observation = attack()
                    self.assertFalse(observation.ok)
                    self.assertEqual((), observation.records)
                    self.assertEqual(
                        [expected],
                        [diagnostic.format() for diagnostic in observation.diagnostics],
                    )

    def test_invalid_authority_fails_before_any_source_observation(self) -> None:
        authority = graph.inspect_manifest_authority(
            ROOT / "fixtures" / "missing-o4b-manifest.json"
        )
        self.assertFalse(authority.ok)

        with mock.patch.object(
            graph._finite_source,
            "_observe_finite_source",
            side_effect=AssertionError("invalid authority observed roots"),
        ):
            graph_observation = graph.inspect_manifest_graph(authority)
            theory = publication.inspect_theory_publication(
                Path("/must-not-observe-theory"),
                authority=authority,
                source="theory",
                product="Example",
            )
            package = registration.inspect_package_registration(
                Path("/must-not-observe-theory"),
                Path("/must-not-observe-package"),
                "package",
                authority=authority,
                theory_source="theory",
                product="Example",
            )

        for observation in (graph_observation, theory, package):
            self.assertFalse(observation.ok)
            self.assertEqual((), observation.records)
            self.assertEqual(
                ["MANIFEST_INPUT_NOT_FOUND"],
                [diagnostic.code for diagnostic in observation.diagnostics],
            )


if __name__ == "__main__":
    unittest.main()
