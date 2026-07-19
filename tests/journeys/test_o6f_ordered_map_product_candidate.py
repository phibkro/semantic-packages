from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from collections.abc import Mapping
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

import jsonschema

from scripts import ordered_map_evidence_check
from semantic_packages import _finite_source, canonical_artifact, graph, resolver


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "registry" / "ordered-map" / "manifest.json"
CONTRACT = ROOT / "contracts" / "ordered-map" / "product-contract.json"
CONTRACT_SCHEMA = ROOT / "schemas" / "ordered-map-product-contract.schema.json"
THEORY_ROOT = ROOT / "registry" / "ordered-map" / "theory"
RUST_ROOT = ROOT / "registry" / "ordered-map" / "packages" / "rust" / "records"
TYPESCRIPT_ROOT = (
    ROOT / "registry" / "ordered-map" / "packages" / "typescript" / "records"
)
POLICY_ROOT = ROOT / "registry" / "ordered-map" / "consumers" / "package" / "records"
POLICY = POLICY_ROOT / "ordered-map-bounded-policy.json"
SPECIFICATION = ("specification", "ordered-map", "0.1.0")
PROFILE = ("realizationProfile", "ordered-map-ascii-fold", "0.1.0")
PLAN_RAW_SHA256 = "bfffbe98114c78c04865bccadc143a02cd46beff71c0f04c0b7f5b522d15c1d3"
PLAN_CANONICAL_SHA256 = (
    "2cf7b481946ce1c0130e70b0d0ffcc1ec5a58bb10e7963b3f5058253bb63447a"
)
ASSURANCE = "per-declaration-one-accepted-applicable-support-no-selected-challenge"

try:
    product = importlib.import_module("semantic_packages.ordered_map_product")
    PRODUCT_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.ordered_map_product":
        raise
    product = None
    PRODUCT_IMPORT_ERROR = error

BOUNDARY_FILES = (POLICY, MANIFEST, CONTRACT, CONTRACT_SCHEMA)
BOUNDARY_READY = product is not None and all(path.is_file() for path in BOUNDARY_FILES)

EXPECTED_POLICY_SHA256 = (
    "6d0d215df3407660fd381e097dba70f8f80196d5f246eacb933358095817291c"
)
EXPECTED_POLICY = {
    "kind": "consumerPolicy",
    "id": "ordered-map-bounded-policy",
    "version": "0.1.0",
    "specification": {
        "kind": "specification",
        "id": "ordered-map",
        "version": "0.1.0",
    },
    "profile": {
        "kind": "realizationProfile",
        "id": "ordered-map-ascii-fold",
        "version": "0.1.0",
    },
    "concerns": [
        {
            "concern": "law.conformance",
            "priority": "required",
            "acceptedMechanisms": ["bounded-conformance-campaign"],
            "minimumAssurance": ASSURANCE,
        },
        {
            "concern": "resource.persistence",
            "priority": "required",
            "acceptedMechanisms": ["bounded-conformance-campaign"],
            "minimumAssurance": ASSURANCE,
        },
        {
            "concern": "effect.conformance",
            "priority": "required",
            "acceptedMechanisms": ["bounded-conformance-campaign"],
            "minimumAssurance": ASSURANCE,
        },
        {
            "concern": "performance",
            "priority": "optional",
            "acceptedMechanisms": ["proof", "proof-audit"],
            "minimumAssurance": ASSURANCE,
        },
    ],
    "prohibitions": [
        {
            "proposition": {
                "specification": {
                    "kind": "specification",
                    "id": "ordered-map",
                    "version": "0.1.0",
                },
                "declarationId": "ordered-map-effects",
            },
            "description": (
                "No io.* events inside the adapter-observed invocation trace."
            ),
            "eventPattern": "io.*",
            "acceptedEvidenceScope": ["adapter-invocation-trace"],
        }
    ],
}
EXPECTED_MEMBER_ROWS = (
    ("ordered-map-theory", PROFILE, "6d1297892c355a569e244c2b94448a5f5edaf9b1bf2ae54f940d7c4494fe225f", "dependency"),
    ("ordered-map-theory", SPECIFICATION, "6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f", "theory-authored"),
    ("ordered-map-rust", ("claim", "ordered-map-rust-lookup-empty", "0.1.0"), "5d4643cd384a5538d024c20f4b32e23ffec55de343ad642cd5ce7fe7ba63c66e", "package-authored"),
    ("ordered-map-rust", ("evidence", "ordered-map-rust-lookup-empty-conformance", "0.1.0"), "8dc702cbc8c0126013f76e3475d87ed78410031bd2bb5335de297a9e4494bd7f", "package-authored"),
    ("ordered-map-rust", ("claim", "ordered-map-rust-lookup-put-other", "0.1.0"), "a49866a34722e2040e7cbcf51b7eaaa08e3ca2216f3b6d32d98bc90cd3c1a061", "package-authored"),
    ("ordered-map-rust", ("evidence", "ordered-map-rust-lookup-put-other-conformance", "0.1.0"), "ccb6c447985d45956c6522166c2e59b021fd19d5122bc2f69e0bb5d1fbe316e0", "package-authored"),
    ("ordered-map-rust", ("claim", "ordered-map-rust-lookup-put-same", "0.1.0"), "c3198e3f4297d5a4850d3746b29f159af131ddb9a88843b36ac39f2e31028b61", "package-authored"),
    ("ordered-map-rust", ("evidence", "ordered-map-rust-lookup-put-same-conformance", "0.1.0"), "3542194fb3d59d93fdd79614d603ca5ec63ce71ee58007b3210111ea3ff78215", "package-authored"),
    ("ordered-map-rust", ("claim", "ordered-map-rust-ordered-map-effects", "0.1.0"), "1eb9aeb4d3f29bd34efd5e0ad2294927e8e7e647ee07fca4b430b0cb955397ae", "package-authored"),
    ("ordered-map-rust", ("evidence", "ordered-map-rust-ordered-map-effects-conformance", "0.1.0"), "3add20e4ca94aae743cc8634e6154a32e09c8209c423cc3644c8d0b074ef26f7", "package-authored"),
    ("ordered-map-rust", ("claim", "ordered-map-rust-persistence", "0.1.0"), "b5e5c5fbc707350064d9a7849947a5f9ad95c6994fd1b2ff80ad530262215223", "package-authored"),
    ("ordered-map-rust", ("evidence", "ordered-map-rust-persistence-conformance", "0.1.0"), "9ae9b1c7a72c17fecb090c2991a86830e0d4cbddcbbd795dd999a55e767f4e4d", "package-authored"),
    ("ordered-map-rust", ("claim", "ordered-map-rust-put-existing-position", "0.1.0"), "e62077b46923fb2f4c2ed6a9b7b683a515b7fe64c4e5e0a164a83ba8afca0e5f", "package-authored"),
    ("ordered-map-rust", ("evidence", "ordered-map-rust-put-existing-position-conformance", "0.1.0"), "7d7ac27e9acdb29ce141fa5cbd10c7548999450854363246f1c2b4ea0a8831da", "package-authored"),
    ("ordered-map-rust", ("claim", "ordered-map-rust-put-new-appends", "0.1.0"), "267b24d54fb4db0aeed64811332dcb9911c55fafe5d4f681409cada0da751089", "package-authored"),
    ("ordered-map-rust", ("evidence", "ordered-map-rust-put-new-appends-conformance", "0.1.0"), "39018810f56894b251b3fa030157aebfd7192d0e8f3930f3ab0a2df011735d3b", "package-authored"),
    ("ordered-map-rust", ("realization", "ordered-map-rust", "0.1.0"), "6f66ea9b5cfb8b7804271f3f266d01c68085b6bcdc943d046b82ca71ca9aed90", "package-authored"),
    ("ordered-map-typescript", ("claim", "ordered-map-typescript-lookup-empty", "0.1.0"), "a408b368ea0bae3dba52b590d0bf3fcfc12bd8b82e0d4d7dece1e8238a79880b", "package-authored"),
    ("ordered-map-typescript", ("evidence", "ordered-map-typescript-lookup-empty-conformance", "0.1.0"), "063be5de4695bddf333199646721653bb0332fafe46625c3b096522524164165", "package-authored"),
    ("ordered-map-typescript", ("claim", "ordered-map-typescript-lookup-put-other", "0.1.0"), "0d920caefc665655178302d0545c89145e33dae60f3fcf374909736fdf0b0b30", "package-authored"),
    ("ordered-map-typescript", ("evidence", "ordered-map-typescript-lookup-put-other-conformance", "0.1.0"), "1094aa260a9884ec90908ca7ed46d3a3ca67aa725fceac46e28b0b2a38305645", "package-authored"),
    ("ordered-map-typescript", ("claim", "ordered-map-typescript-lookup-put-same", "0.1.0"), "d42abd0e5d54b0f470e13f07eeeb2ccd2e1dfd8d8a96bec7bb0f82acaf195e9a", "package-authored"),
    ("ordered-map-typescript", ("evidence", "ordered-map-typescript-lookup-put-same-conformance", "0.1.0"), "abd7d25dd6f9216957b00428a2ccbf003968b6fd06714b684535e383e6838963", "package-authored"),
    ("ordered-map-typescript", ("claim", "ordered-map-typescript-ordered-map-effects", "0.1.0"), "8756ac71870d5684128a9bc49b47bbb9165e5cca1685477821e5410c5ad64225", "package-authored"),
    ("ordered-map-typescript", ("evidence", "ordered-map-typescript-ordered-map-effects-conformance", "0.1.0"), "c352bd7b89a9fece485482f818448ced560bfa4189e162c05322f08b2cf95b36", "package-authored"),
    ("ordered-map-typescript", ("claim", "ordered-map-typescript-persistence", "0.1.0"), "ae81ab746d25be7d38a7f8d59aadfc1c6f4dba3e60d2915956b3b144447216f3", "package-authored"),
    ("ordered-map-typescript", ("evidence", "ordered-map-typescript-persistence-conformance", "0.1.0"), "07936f56032b3239e0e035ff20adc514324ec013375d618d51fc24d892273104", "package-authored"),
    ("ordered-map-typescript", ("claim", "ordered-map-typescript-put-existing-position", "0.1.0"), "cb6752d1f20a4d46fad97107c88430c6c054b6afd1b235b1a3b1bc3c438e347d", "package-authored"),
    ("ordered-map-typescript", ("evidence", "ordered-map-typescript-put-existing-position-conformance", "0.1.0"), "6b440385f2f946e6e927a39f70166a1238371047487efc3fe94be12c114c20d4", "package-authored"),
    ("ordered-map-typescript", ("claim", "ordered-map-typescript-put-new-appends", "0.1.0"), "b8ed82d4a6a1fce907c6203cca84d2194ffc07ed5ab480540e24485988e9df2d", "package-authored"),
    ("ordered-map-typescript", ("evidence", "ordered-map-typescript-put-new-appends-conformance", "0.1.0"), "eaea076986c538d13abf82883d8e4bcdbc016115760c4b7fb8475f92d5d648a6", "package-authored"),
    ("ordered-map-typescript", ("realization", "ordered-map-typescript", "0.1.0"), "38984d1c1607d5c23e15e7b94764837bcc93e3a50a0a6229eb21f888f2669e74", "package-authored"),
    ("ordered-map-consumer", ("consumerPolicy", "ordered-map-bounded-policy", "0.1.0"), EXPECTED_POLICY_SHA256, "package-consumer-authored"),
)
EXPECTED_MANIFEST = {
    "formatVersion": 1,
    "sources": [
        {
            "id": "ordered-map-theory",
            "root": "theory",
            "roles": ["theory-authored", "dependency"],
        },
        {
            "id": "ordered-map-rust",
            "root": "packages/rust/records",
            "roles": ["package-authored"],
        },
        {
            "id": "ordered-map-typescript",
            "root": "packages/typescript/records",
            "roles": ["package-authored"],
        },
        {
            "id": "ordered-map-consumer",
            "root": "consumers/package/records",
            "roles": ["package-consumer-authored"],
        },
    ],
    "members": [
        {
            "source": source,
            "address": {"kind": kind, "id": record_id, "version": version},
            "sha256": sha256,
            "role": role,
        }
        for source, (kind, record_id, version), sha256, role in EXPECTED_MEMBER_ROWS
    ],
}
EXPECTED_MANIFEST_RAW_SHA256 = (
    "0dae972b40c850f691df0856577cf8a9d66449a4655dcbb0c328b20c6993455d"
)
EXPECTED_CONTRACT = {
    "formatVersion": 1,
    "id": "ordered-map-product-contract",
    "version": "0.1.0",
    "authorityClass": "final-product",
    "finalProductAuthority": True,
    "manifest": {
        "path": "registry/ordered-map/manifest.json",
        "rawSha256": EXPECTED_MANIFEST_RAW_SHA256,
    },
    "sources": [
        {
            "selector": "ordered-map-theory",
            "roles": ["theory-authored", "dependency"],
        },
        {"selector": "ordered-map-rust", "roles": ["package-authored"]},
        {
            "selector": "ordered-map-typescript",
            "roles": ["package-authored"],
        },
        {
            "selector": "ordered-map-consumer",
            "roles": ["package-consumer-authored"],
        },
    ],
    "specification": {
        "address": {
            "kind": "specification",
            "id": "ordered-map",
            "version": "0.1.0",
        },
        "rawSha256": (
            "6049d371603cbdac0e722685f1fd25c7369872f7d963ae2e4f4bae90cce7fd7f"
        ),
    },
    "profile": {
        "address": {
            "kind": "realizationProfile",
            "id": "ordered-map-ascii-fold",
            "version": "0.1.0",
        },
        "rawSha256": (
            "6d1297892c355a569e244c2b94448a5f5edaf9b1bf2ae54f940d7c4494fe225f"
        ),
    },
    "conformancePlan": {
        "path": "contracts/ordered-map/conformance-plan.json",
        "rawSha256": PLAN_RAW_SHA256,
        "canonicalSha256": PLAN_CANONICAL_SHA256,
        "observationScope": "adapter-invocation-trace",
    },
    "resolver": {
        "concernCategories": [
            {"concern": "law.conformance", "declarationField": "laws"},
            {
                "concern": "resource.persistence",
                "declarationField": "resources",
            },
            {"concern": "effect.conformance", "declarationField": "effects"},
            {
                "concern": "performance",
                "declarationField": "performancePropositions",
            },
        ],
        "assurance": ASSURANCE,
        "acceptedCampaignMechanism": "bounded-conformance-campaign",
        "effectScope": "adapter-invocation-trace",
    },
    "deploymentBoundary": {
        "interfaceMechanism": "NDJSON messages over stdin and stdout",
        "direction": "consumer-to-realization",
        "mechanism": "child-process-ndjson",
        "direct": False,
    },
}
EXPECTED_CONTRACT_CANONICAL_SHA256 = (
    "4bfbc89ed7e061fa9f2c38f02a99331af1e9a05f5d111bea391b2034ac14eb17"
)


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _plain(value: object):
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _address(document: dict) -> tuple[str, str, str]:
    return document["kind"], document["id"], document["version"]


def _manifest_members(document: dict) -> set[tuple[str, tuple[str, str, str], str, str]]:
    return {
        (
            member["source"],
            tuple(member["address"][key] for key in ("kind", "id", "version")),
            member["sha256"],
            member["role"],
        )
        for member in document["members"]
    }


def _public_attributes(value: object) -> set[str]:
    return {name for name in dir(value) if not name.startswith("_")}


def _object_schema_nodes(value: object):
    if isinstance(value, dict):
        if value.get("type") == "object":
            yield value
        for item in value.values():
            yield from _object_schema_nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from _object_schema_nodes(item)


class OrderedMapProductCandidatePreconditionTest(unittest.TestCase):
    def test_reviewed_records_and_macro_convergence_precede_final_candidate(self) -> None:
        errors, summary = (
            ordered_map_evidence_check.run_ordered_map_evidence_candidate_checks(ROOT)
        )
        self.assertEqual([], errors)
        self.assertEqual(
            "OrderedMap Evidence candidate checks passed: 2 Realizations, "
            "14 Claims, 14 Evidence records.",
            summary,
        )
        predecessor_files = tuple(THEORY_ROOT.rglob("*.json")) + tuple(
            RUST_ROOT.rglob("*.json")
        ) + tuple(TYPESCRIPT_ROOT.rglob("*.json"))
        self.assertEqual(32, len(predecessor_files))
        self.assertEqual(33, len(EXPECTED_MEMBER_ROWS))

    def test_final_authority_candidate_boundary_exists(self) -> None:
        self.assertTrue(
            BOUNDARY_READY,
            "O6f-P intentionally precedes the consumer policy, complete manifest, "
            "ProductContract schema/document, and ordered_map_product actor; observed "
            f"import={PRODUCT_IMPORT_ERROR!r}, files="
            f"{[(path.relative_to(ROOT).as_posix(), path.is_file()) for path in BOUNDARY_FILES]}",
        )


@unittest.skipUnless(
    BOUNDARY_READY,
    "O6f-P freezes the candidate boundary before O6f implementation",
)
class OrderedMapProductCandidateContractTest(unittest.TestCase):
    @staticmethod
    def _copy_repository_slice(raw: str) -> Path:
        root = Path(raw) / "repository"
        shutil.copytree(ROOT / "contracts", root / "contracts")
        shutil.copytree(ROOT / "schemas", root / "schemas")
        shutil.copytree(
            ROOT / "registry" / "ordered-map", root / "registry" / "ordered-map"
        )
        return root

    @staticmethod
    def _inspect_at(root: Path):
        with mock.patch.object(product, "_ROOT", root):
            return product.inspect_product_candidate()

    def test_manifest_is_the_exact_four_source_thirty_three_member_graph(self) -> None:
        document = _load(MANIFEST)
        authority = graph.inspect_manifest_authority(MANIFEST)

        self.assertTrue(authority.ok, authority.diagnostics)
        self.assertEqual(EXPECTED_MANIFEST, document)
        self.assertEqual(EXPECTED_MANIFEST_RAW_SHA256, _raw_sha256(MANIFEST))
        self.assertEqual(
            [
                {
                    "id": "ordered-map-theory",
                    "root": "theory",
                    "roles": ["theory-authored", "dependency"],
                },
                {
                    "id": "ordered-map-rust",
                    "root": "packages/rust/records",
                    "roles": ["package-authored"],
                },
                {
                    "id": "ordered-map-typescript",
                    "root": "packages/typescript/records",
                    "roles": ["package-authored"],
                },
                {
                    "id": "ordered-map-consumer",
                    "root": "consumers/package/records",
                    "roles": ["package-consumer-authored"],
                },
            ],
            document["sources"],
        )
        self.assertEqual(33, len(document["members"]))
        self.assertEqual(set(EXPECTED_MEMBER_ROWS), _manifest_members(document))
        self.assertEqual(EXPECTED_POLICY, _load(POLICY))
        self.assertEqual(EXPECTED_POLICY_SHA256, _raw_sha256(POLICY))
        self.assertTrue(graph.inspect_manifest_graph(authority).ok)
        self.assertFalse(
            any(
                "report" in member["source"]
                or member["address"]["id"] == "put-amortized-constant"
                for member in document["members"]
            )
        )

    def test_contract_is_closed_canonical_and_binds_manifest_and_inputs(self) -> None:
        observation = canonical_artifact.inspect_json_artifact(
            CONTRACT,
            schema_path=CONTRACT_SCHEMA,
            expected_canonical_sha256=EXPECTED_CONTRACT_CANONICAL_SHA256,
            label="OrderedMap ProductContract candidate",
        )
        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(
            EXPECTED_CONTRACT_CANONICAL_SHA256,
            product._CONTRACT_CANONICAL_SHA256,
        )
        document = observation.document
        self.assertEqual(EXPECTED_CONTRACT, _plain(document))
        self.assertEqual(
            EXPECTED_CONTRACT_CANONICAL_SHA256,
            observation.canonical_sha256,
        )
        self.assertEqual("ordered-map-product-contract", document["id"])
        self.assertEqual("0.1.0", document["version"])
        self.assertEqual("final-product", document["authorityClass"])
        self.assertIs(True, document["finalProductAuthority"])
        self.assertEqual("registry/ordered-map/manifest.json", document["manifest"]["path"])
        self.assertEqual(
            EXPECTED_MANIFEST_RAW_SHA256, document["manifest"]["rawSha256"]
        )
        self.assertEqual(SPECIFICATION, _address(document["specification"]["address"]))
        self.assertEqual(PROFILE, _address(document["profile"]["address"]))
        self.assertEqual(
            _raw_sha256(THEORY_ROOT / "records" / "ordered-map-spec.json"),
            document["specification"]["rawSha256"],
        )
        self.assertEqual(
            _raw_sha256(THEORY_ROOT / "dependencies" / "ordered-map-profile.json"),
            document["profile"]["rawSha256"],
        )

        schema = _load(CONTRACT_SCHEMA)
        changed = _plain(document)
        assert isinstance(changed, dict)
        changed["accepted"] = True
        self.assertTrue(
            list(jsonschema.Draft202012Validator(schema).iter_errors(changed))
        )
        object_nodes = tuple(_object_schema_nodes(schema))
        self.assertGreaterEqual(len(object_nodes), 10)
        self.assertTrue(
            all(node.get("additionalProperties") is False for node in object_nodes)
        )

    def test_contract_pins_exact_sources_plan_policy_effect_and_boundary_tokens(self) -> None:
        document = _load(CONTRACT)
        self.assertEqual(
            [
                {
                    "selector": "ordered-map-theory",
                    "roles": ["theory-authored", "dependency"],
                },
                {"selector": "ordered-map-rust", "roles": ["package-authored"]},
                {
                    "selector": "ordered-map-typescript",
                    "roles": ["package-authored"],
                },
                {
                    "selector": "ordered-map-consumer",
                    "roles": ["package-consumer-authored"],
                },
            ],
            document["sources"],
        )
        self.assertEqual(
            {
                "path": "contracts/ordered-map/conformance-plan.json",
                "rawSha256": PLAN_RAW_SHA256,
                "canonicalSha256": PLAN_CANONICAL_SHA256,
                "observationScope": "adapter-invocation-trace",
            },
            document["conformancePlan"],
        )
        self.assertEqual(
            {
                "concernCategories": [
                    {"concern": "law.conformance", "declarationField": "laws"},
                    {
                        "concern": "resource.persistence",
                        "declarationField": "resources",
                    },
                    {
                        "concern": "effect.conformance",
                        "declarationField": "effects",
                    },
                    {"concern": "performance", "declarationField": "performancePropositions"},
                ],
                "assurance": ASSURANCE,
                "acceptedCampaignMechanism": "bounded-conformance-campaign",
                "effectScope": "adapter-invocation-trace",
            },
            document["resolver"],
        )
        self.assertEqual(
            {
                "interfaceMechanism": "NDJSON messages over stdin and stdout",
                "direction": "consumer-to-realization",
                "mechanism": "child-process-ndjson",
                "direct": False,
            },
            document["deploymentBoundary"],
        )

    def test_zero_argument_actor_surfaces_candidate_bytes_without_acceptance(self) -> None:
        self.assertEqual(
            (), tuple(inspect.signature(product.inspect_product_candidate).parameters)
        )
        result = product.inspect_product_candidate()
        self.assertTrue(result.ok, result.diagnostics)
        authority = result.authority
        self.assertEqual("ordered-map-product-contract", authority.contract_id)
        self.assertEqual("0.1.0", authority.contract_version)
        self.assertEqual("final-product", authority.authority_class)
        self.assertTrue(authority.final_product_authority)
        self.assertEqual(
            EXPECTED_CONTRACT_CANONICAL_SHA256,
            authority.contract_canonical_sha256,
        )
        self.assertEqual(
            EXPECTED_MANIFEST_RAW_SHA256, authority.manifest_raw_sha256
        )
        self.assertEqual(
            {
                "authority",
                "publication",
                "registrations",
                "graph",
                "theory",
                "diagnostics",
            },
            set(vars(result)),
        )
        self.assertEqual(set(vars(result)) | {"ok"}, _public_attributes(result))
        self.assertEqual(
            {
                "contract_id",
                "contract_version",
                "authority_class",
                "final_product_authority",
                "contract_canonical_sha256",
                "manifest_raw_sha256",
            },
            set(vars(authority)),
        )
        self.assertEqual(set(vars(authority)), _public_attributes(authority))
        for call in (
            lambda: product.inspect_product_candidate(CONTRACT),
            lambda: product.inspect_product_candidate(contract=object()),
            lambda: product.inspect_product_candidate(manifest=MANIFEST),
            lambda: product.inspect_product_candidate(root=ROOT),
        ):
            with self.assertRaises(TypeError):
                call()

    def test_one_graph_snapshot_drives_publication_registrations_and_theory(self) -> None:
        original_graph = graph.inspect_manifest_graph
        original_source = _finite_source._observe_finite_source
        original_artifact = canonical_artifact.inspect_json_artifact
        with mock.patch.object(
            graph, "inspect_manifest_graph", wraps=original_graph
        ) as capture, mock.patch.object(
            graph,
            "inspect_manifest_authority",
            side_effect=AssertionError("actor reread manifest authority"),
        ), mock.patch.object(
            _finite_source, "_observe_finite_source", wraps=original_source
        ) as source_capture, mock.patch.object(
            canonical_artifact,
            "inspect_json_artifact",
            wraps=original_artifact,
        ) as artifact_capture:
            result = product.inspect_product_candidate()

        self.assertEqual(
            [CONTRACT, MANIFEST],
            [call.args[0] for call in artifact_capture.call_args_list],
        )
        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual(1, capture.call_count)
        self.assertEqual(1, source_capture.call_count)
        self.assertEqual(33, len(result.graph.records))
        self.assertEqual(2, len(result.publication.records))
        self.assertEqual(
            {"ordered-map-rust": 17, "ordered-map-typescript": 17},
            {item.package: len(item.records) for item in result.registrations},
        )
        self.assertEqual(SPECIFICATION, result.theory.specification)
        self.assertEqual(18, len(result.theory.declarations))
        self.assertTrue(
            all(
                item.observation == "unclaimed" and not item.claims
                for item in result.theory.declarations
            )
        )

    def test_actor_replay_neither_executes_records_nor_resolves_policy(self) -> None:
        def reject(name: str):
            return AssertionError(f"product replay crossed execution path {name}")

        with ExitStack() as stack:
            for owner, name in (
                (subprocess, "Popen"),
                (subprocess, "run"),
                (os, "system"),
                (os, "posix_spawn"),
                (os, "posix_spawnp"),
                (os, "spawnv"),
                (os, "spawnve"),
                (os, "spawnvp"),
                (os, "spawnvpe"),
            ):
                if hasattr(owner, name):
                    stack.enter_context(
                        mock.patch.object(owner, name, side_effect=reject(name))
                    )
            stack.enter_context(
                mock.patch.object(
                    resolver,
                    "resolve_stack",
                    side_effect=AssertionError("product replay resolved policy"),
                )
            )
            result = product.inspect_product_candidate()
        self.assertTrue(result.ok, result.diagnostics)
        self.assertFalse(hasattr(result, "candidates"))
        self.assertFalse(hasattr(result, "boundary"))

    def test_contract_or_manifest_mutation_fails_before_graph_or_views(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o6f-candidate-mutations-") as raw:
            root = self._copy_repository_slice(raw)
            contract_path = root / CONTRACT.relative_to(ROOT)
            contract = _load(contract_path)
            contract["resolver"]["effectScope"] = "whole-process"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            with mock.patch.object(
                graph,
                "inspect_manifest_graph",
                side_effect=AssertionError("contract failure reached graph capture"),
            ):
                result = self._inspect_at(root)
            self.assertFalse(result.ok)
            self.assertIsNone(result.authority)
            self.assertIsNone(result.graph)
            self.assertIsNone(result.publication)
            self.assertEqual((), result.registrations)
            self.assertIsNone(result.theory)

        with tempfile.TemporaryDirectory(prefix="o6f-manifest-mutations-") as raw:
            root = self._copy_repository_slice(raw)
            manifest_path = root / MANIFEST.relative_to(ROOT)
            manifest = _load(manifest_path)
            manifest["members"] = manifest["members"][:-1]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with mock.patch.object(
                graph,
                "inspect_manifest_graph",
                side_effect=AssertionError("manifest failure reached graph capture"),
            ):
                result = self._inspect_at(root)
            self.assertFalse(result.ok)
            self.assertIsNone(result.authority)
            self.assertIsNone(result.graph)
            self.assertIsNone(result.publication)
            self.assertEqual((), result.registrations)
            self.assertIsNone(result.theory)

    def test_member_failure_retains_authority_but_returns_no_partial_views(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o6f-member-failure-") as raw:
            root = self._copy_repository_slice(raw)
            member = root / RUST_ROOT.relative_to(ROOT) / "ordered-map-rust-realization.json"
            member.unlink()
            result = self._inspect_at(root)

        self.assertFalse(result.ok)
        self.assertIsNotNone(result.authority)
        self.assertIsNotNone(result.graph)
        self.assertFalse(result.graph.ok)
        self.assertIsNone(result.publication)
        self.assertEqual((), result.registrations)
        self.assertIsNone(result.theory)

    def test_candidate_graph_is_detached_from_returned_document_mutation(self) -> None:
        result = product.inspect_product_candidate()
        self.assertTrue(result.ok, result.diagnostics)
        record = result.graph.records[0]
        first = record.document
        first["id"] = "changed"
        self.assertNotEqual("changed", record.document["id"])
        with self.assertRaises((AttributeError, TypeError)):
            result.authority.contract_id = "changed"  # type: ignore[misc]

    def test_stack_and_provisional_theory_source_regressions_remain_separate(self) -> None:
        from semantic_packages import ordered_map_theory_source, publication, registration

        provisional = ordered_map_theory_source.inspect_theory_source()
        candidate = product.inspect_product_candidate()
        self.assertTrue(provisional.ok, provisional.diagnostics)
        self.assertTrue(candidate.ok, candidate.diagnostics)
        self.assertFalse(provisional.authority.final_product_authority)
        self.assertEqual("provisional-theory-source", provisional.authority.authority_class)
        self.assertNotEqual(
            provisional.authority.contract_canonical_sha256,
            candidate.authority.contract_canonical_sha256,
        )
        self.assertEqual(1, len(inspect.signature(publication.inspect_stack_theory).parameters))
        self.assertEqual(3, len(inspect.signature(registration.inspect_stack_package).parameters))


if __name__ == "__main__":
    unittest.main()
