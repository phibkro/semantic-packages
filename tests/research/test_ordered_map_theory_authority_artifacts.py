from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import jsonschema

from semantic_packages import canonical_artifact, graph


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts" / "ordered-map" / "theory-source-contract.json"
CONTRACT_SCHEMA = (
    ROOT / "schemas" / "ordered-map-theory-source-contract.schema.json"
)
MANIFEST = ROOT / "registry" / "ordered-map" / "theory-manifest.json"
SPECIFICATION = (
    ROOT / "registry" / "ordered-map" / "theory" / "records" / "ordered-map-spec.json"
)
PROFILE = (
    ROOT
    / "registry"
    / "ordered-map"
    / "theory"
    / "dependencies"
    / "ordered-map-profile.json"
)

CONTRACT_SHA256 = "1ec7d9f0ec74af8afff2823b89e7039a910fbde28fd86b9dd60f499948b25a6b"
MANIFEST_SHA256 = "06157079396b8712e31eaf459949c0503eb8d68ac7b6c97ac0b1308cc7f523c7"
SPECIFICATION_SHA256 = "6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f"
PROFILE_SHA256 = "6d1297892c355a569e244c2b94448a5f5edaf9b1bf2ae54f940d7c4494fe225f"


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OrderedMapTheoryAuthorityArtifactTest(unittest.TestCase):
    def test_contract_is_closed_schema_valid_and_canonically_pinned(self) -> None:
        observation = canonical_artifact.inspect_json_artifact(
            CONTRACT,
            schema_path=CONTRACT_SCHEMA,
            expected_canonical_sha256=CONTRACT_SHA256,
            label="ordered-map-theory-source-contract",
        )

        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(CONTRACT_SHA256, observation.canonical_sha256)
        self.assertEqual(
            "ordered-map-theory-source-contract", observation.document["id"]
        )
        self.assertEqual("0.1.0", observation.document["version"])
        self.assertEqual(
            "provisional-theory-source", observation.document["authorityClass"]
        )
        self.assertIs(False, observation.document["finalProductAuthority"])

    def test_schema_rejects_authority_expansion(self) -> None:
        schema = json.loads(CONTRACT_SCHEMA.read_text(encoding="utf-8"))
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        contract["acceptedPackages"] = ["ordered-map-rust"]

        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(contract))

        self.assertTrue(errors)
        self.assertIn("Additional properties", errors[0].message)

    def test_schema_rejects_swapped_and_arbitrary_binding_addresses(self) -> None:
        schema = json.loads(CONTRACT_SCHEMA.read_text(encoding="utf-8"))
        base = json.loads(CONTRACT.read_text(encoding="utf-8"))
        swapped = json.loads(json.dumps(base))
        swapped["specification"], swapped["profile"] = (
            swapped["profile"],
            swapped["specification"],
        )
        arbitrary = json.loads(json.dumps(base))
        arbitrary["specification"]["address"]["id"] = "other-map"

        validator = jsonschema.Draft202012Validator(schema)

        self.assertTrue(list(validator.iter_errors(swapped)))
        self.assertTrue(list(validator.iter_errors(arbitrary)))

    def test_manifest_authority_is_exactly_two_members_and_manifest_only(self) -> None:
        authority = graph.inspect_manifest_authority(MANIFEST)

        self.assertTrue(authority.ok, authority.diagnostics)
        self.assertEqual(MANIFEST.resolve(), authority.manifest_path)
        self.assertEqual(
            [("ordered-map-theory", "theory", {"theory-authored", "dependency"})],
            [
                (source.source_id, source.root, set(source.roles))
                for source in authority.sources
            ],
        )
        self.assertEqual(
            {
                (
                    "ordered-map-theory",
                    ("specification", "ordered-map", "0.1.0"),
                    SPECIFICATION_SHA256,
                    "theory-authored",
                ),
                (
                    "ordered-map-theory",
                    (
                        "realizationProfile",
                        "ordered-map-ascii-fold",
                        "0.1.0",
                    ),
                    PROFILE_SHA256,
                    "dependency",
                ),
            },
            {
                (member.source, member.address, member.sha256, member.role)
                for member in authority.members
            },
        )

    def test_contract_manifest_and_member_digests_reproduce(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        authority = graph.inspect_manifest_authority(MANIFEST)

        self.assertEqual(MANIFEST_SHA256, _raw_sha256(MANIFEST))
        self.assertEqual(MANIFEST_SHA256, contract["manifest"]["rawSha256"])
        self.assertEqual(SPECIFICATION_SHA256, _raw_sha256(SPECIFICATION))
        self.assertEqual(
            SPECIFICATION_SHA256, contract["specification"]["rawSha256"]
        )
        self.assertEqual(PROFILE_SHA256, _raw_sha256(PROFILE))
        self.assertEqual(PROFILE_SHA256, contract["profile"]["rawSha256"])
        self.assertEqual(contract["source"]["selector"], authority.sources[0].source_id)
        self.assertEqual(set(contract["source"]["roles"]), set(authority.sources[0].roles))
        contract_bindings = {
            (
                tuple(binding["address"][key] for key in ("kind", "id", "version")),
                binding["rawSha256"],
            )
            for binding in (contract["specification"], contract["profile"])
        }
        self.assertEqual(
            {(member.address, member.sha256) for member in authority.members},
            contract_bindings,
        )

    def test_provisional_authority_remains_separate_from_later_product_candidate(
        self,
    ) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        product_contract = json.loads(
            (
                ROOT / "contracts" / "ordered-map" / "product-contract.json"
            ).read_text(encoding="utf-8")
        )

        self.assertFalse(contract["finalProductAuthority"])
        self.assertTrue(product_contract["finalProductAuthority"])
        self.assertEqual("provisional-theory-source", contract["authorityClass"])
        self.assertEqual("final-product", product_contract["authorityClass"])
        self.assertNotEqual(contract["id"], product_contract["id"])
        self.assertNotEqual(contract["manifest"], product_contract["manifest"])
        self.assertNotIn("packages", contract)
        self.assertNotIn("evidence", contract)
        self.assertNotIn("resolver", contract)


if __name__ == "__main__":
    unittest.main()
