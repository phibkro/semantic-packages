from __future__ import annotations

import copy
import hashlib
import importlib
import inspect
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest import mock

from scripts import record_check
from semantic_packages import (
    graph,
    maintenance,
    ordered_map_product,
    resolver,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry/ordered-map"
MANIFEST = REGISTRY / "manifest.json"
SUCCESSOR_MANIFEST = REGISTRY / "successor-manifest.json"
SPECIFICATION_RECORD = REGISTRY / "theory/records/ordered-map-spec.json"
POLICY_RECORD = REGISTRY / "consumers/package/records/ordered-map-bounded-policy.json"
SUCCESSOR_SPECIFICATION_RECORD = (
    REGISTRY / "successors/o8/theory/ordered-map-spec.json"
)
SUCCESSOR_POLICY_RECORD = (
    REGISTRY
    / "successors/o8/consumers/package/ordered-map-bounded-policy.json"
)
OLD_SPECIFICATION = ("specification", "ordered-map", "0.1.0")
NEW_SPECIFICATION = ("specification", "ordered-map", "0.2.0")
OLD_POLICY = ("consumerPolicy", "ordered-map-bounded-policy", "0.1.0")
NEW_POLICY = ("consumerPolicy", "ordered-map-bounded-policy", "0.2.0")
PROFILE = ("realizationProfile", "ordered-map-ascii-fold", "0.1.0")
REALIZATIONS = (
    ("realization", "ordered-map-rust", "0.1.0"),
    ("realization", "ordered-map-typescript", "0.1.0"),
)
EXPECTED_SPECIFICATION_SHA256 = (
    "05bd1dee68216834a81e9095425905a3fb5a5c93530bbe2479c07ef1a6a3afd0"
)
EXPECTED_POLICY_SHA256 = (
    "db788f7fb1adab5f8f9baea65add07269e39e7fdc8d1f84aef9df18b34ece00d"
)
EXPECTED_SUCCESSOR_MANIFEST_SHA256 = (
    "f5e87e65c4765865203158cdd6cbfbf46774dd7d068ddadeaa37c41a5f6ffaf3"
)
PROTECTED_RAW_SHA256 = {
    ROOT / "semantic_packages/resolver.py": "afd6d93378c3361da8a56a5114507b704c675a44c978efa2b54543d89684c8ea",
    ROOT / "semantic_packages/ordered_map_resolution.py": "eed151deda93c00ba665ca7270cb115666d808cdc1f473d2fccc202e52307a5e",
    ROOT / "semantic_packages/ordered_map_inspection.py": "ebabecee1c93ca4b498901226336fbc4c660761abcc9eef418d28ba9475a477c",
    ROOT / "semantic_packages/ordered_map_product.py": "1ea1f5d9cd0bd4768a72c6188560f641f2f78399e68cffc842398b5f4f4cbbc8",
    ROOT / "semantic_packages/registration.py": "dbe700f613a37b3c25188952f368ef824431e0eca081fa3803e56e4e1d4882a4",
    MANIFEST: "0dae972b40c850f691df0856577cf8a9d66449a4655dcbb0c328b20c6993455d",
    POLICY_RECORD: "6d0d215df3407660fd381e097dba70f8f80196d5f246eacb933358095817291c",
    ROOT / "schemas/ordered-map-product-contract.schema.json": "1e14d61de6f30eee5fe16f121450d21d5d342bf99d0468bfc7c08e1c26a2ab36",
}

try:
    ordered_map_maintenance = importlib.import_module(
        "semantic_packages.ordered_map_maintenance"
    )
    MAINTENANCE_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name != "semantic_packages.ordered_map_maintenance":
        raise
    ordered_map_maintenance = None
    MAINTENANCE_IMPORT_ERROR = error


def _load(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _canonical_bytes(document: dict) -> bytes:
    return (
        json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode()


def _expected_specification() -> dict:
    document = copy.deepcopy(_load(SPECIFICATION_RECORD))
    document["version"] = "0.2.0"
    document["observations"].append(
        {"id": "size", "signature": "OrderedMap[Key,Value] -> Natural"}
    )
    document["laws"].append(
        {
            "id": "size-put",
            "statement": (
                "size(put(m, k, v)) == size(m) when k is key-equivalent to a "
                "live class, and size(put(m, k, v)) == size(m) + 1 otherwise"
            ),
        }
    )
    return document


def _expected_policy() -> dict:
    document = copy.deepcopy(_load(POLICY_RECORD))
    document["version"] = "0.2.0"
    document["specification"]["version"] = "0.2.0"
    document["prohibitions"][0]["proposition"]["specification"][
        "version"
    ] = "0.2.0"
    return document


def _expected_manifest() -> dict:
    document = copy.deepcopy(_load(MANIFEST))
    document["sources"].extend(
        (
            {
                "id": "ordered-map-successor-theory",
                "root": "successors/o8/theory",
                "roles": ["theory-authored"],
            },
            {
                "id": "ordered-map-successor-consumer",
                "root": "successors/o8/consumers/package",
                "roles": ["package-consumer-authored"],
            },
        )
    )
    document["members"].extend(
        (
            {
                "source": "ordered-map-successor-theory",
                "address": {
                    "kind": "specification",
                    "id": "ordered-map",
                    "version": "0.2.0",
                },
                "sha256": EXPECTED_SPECIFICATION_SHA256,
                "role": "theory-authored",
            },
            {
                "source": "ordered-map-successor-consumer",
                "address": {
                    "kind": "consumerPolicy",
                    "id": "ordered-map-bounded-policy",
                    "version": "0.2.0",
                },
                "sha256": EXPECTED_POLICY_SHA256,
                "role": "package-consumer-authored",
            },
        )
    )
    return document


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _derived_graph(observation, address, mutate):
    records = []
    for item in observation.records:
        if item.address != address:
            records.append(item)
            continue
        document = item.document
        mutate(document)
        records.append(
            replace(
                item,
                _document_text=json.dumps(
                    document, sort_keys=True, separators=(",", ":")
                ),
            )
        )
    return graph.GraphObservation(tuple(records), ())


def _without(observation, address):
    return graph.GraphObservation(
        tuple(item for item in observation.records if item.address != address), ()
    )


def _with_synthetic_successor_realization(observation):
    predecessor = next(
        item
        for item in observation.records
        if item.address == ("realization", "ordered-map-rust", "0.1.0")
    )
    document = predecessor.document
    document["version"] = "0.2.0"
    document["specification"]["version"] = "0.2.0"
    synthetic = replace(
        predecessor,
        address=("realization", "ordered-map-rust", "0.2.0"),
        path="successors/o8/synthetic/ordered-map-rust-realization.json",
        sha256="0" * 64,
        source="o8-detached-control",
        _document_text=json.dumps(document, sort_keys=True, separators=(",", ":")),
    )
    return graph.GraphObservation(observation.records + (synthetic,), ())


class OrderedMapMaintenancePreconditionTest(unittest.TestCase):
    def test_o7_and_the_accepted_predecessor_remain_exact(self) -> None:
        self.assertEqual(
            PROTECTED_RAW_SHA256,
            {path: _raw_sha256(path) for path in PROTECTED_RAW_SHA256},
        )
        source = ordered_map_product.inspect_product_candidate()
        self.assertTrue(source.ok, source.diagnostics)
        self.assertEqual(33, len(source.graph.records))
        self.assertEqual(18, len(source.theory.declarations))

    def test_successor_boundary_is_the_only_red_predecessor(self) -> None:
        self.assertTrue(
            SUCCESSOR_MANIFEST.is_file(),
            "O8-P intentionally precedes the pinned OrderedMap successor manifest",
        )
        self.assertTrue(SUCCESSOR_SPECIFICATION_RECORD.is_file())
        self.assertTrue(SUCCESSOR_POLICY_RECORD.is_file())
        self.assertIsNotNone(
            ordered_map_maintenance,
            "O8-P intentionally precedes ordered_map_maintenance.py; "
            f"observed {MAINTENANCE_IMPORT_ERROR!r}",
        )


@unittest.skipUnless(
    ordered_map_maintenance is not None
    and SUCCESSOR_MANIFEST.is_file()
    and SUCCESSOR_SPECIFICATION_RECORD.is_file()
    and SUCCESSOR_POLICY_RECORD.is_file(),
    "O8-P freezes successor/recovery before implementation",
)
class OrderedMapMaintenanceContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = ordered_map_product.inspect_product_candidate()
        self.assertTrue(self.source.ok, self.source.diagnostics)
        authority = graph.inspect_manifest_authority(SUCCESSOR_MANIFEST)
        self.successor = graph.inspect_manifest_graph(authority)
        self.assertTrue(self.successor.ok, self.successor.diagnostics)

    def _observe(self, successor=None):
        return ordered_map_maintenance._observe_ordered_map_maintenance(
            self.source,
            self.successor if successor is None else successor,
            successor_manifest_raw_sha256=EXPECTED_SUCCESSOR_MANIFEST_SHA256,
        )

    def test_successor_artifacts_are_exact_and_append_only(self) -> None:
        predecessor_manifest = _load(MANIFEST)
        successor_manifest = _load(SUCCESSOR_MANIFEST)
        self.assertEqual(_expected_specification(), _load(SUCCESSOR_SPECIFICATION_RECORD))
        self.assertEqual(_expected_policy(), _load(SUCCESSOR_POLICY_RECORD))
        self.assertEqual(_expected_manifest(), successor_manifest)
        self.assertEqual(
            EXPECTED_SPECIFICATION_SHA256,
            _raw_sha256(SUCCESSOR_SPECIFICATION_RECORD),
        )
        self.assertEqual(EXPECTED_POLICY_SHA256, _raw_sha256(SUCCESSOR_POLICY_RECORD))
        self.assertEqual(
            EXPECTED_SUCCESSOR_MANIFEST_SHA256,
            _raw_sha256(SUCCESSOR_MANIFEST),
        )
        self.assertEqual(
            predecessor_manifest["sources"], successor_manifest["sources"][:4]
        )
        self.assertEqual(
            predecessor_manifest["members"], successor_manifest["members"][:33]
        )
        self.assertEqual(35, len(successor_manifest["members"]))
        self.assertEqual(6, len(successor_manifest["sources"]))
        self.assertEqual(
            EXPECTED_SUCCESSOR_MANIFEST_SHA256,
            ordered_map_maintenance._SUCCESSOR_MANIFEST_RAW_SHA256,
        )

    def test_actor_is_zero_argument_one_replay_and_never_uses_stack_maintenance(self) -> None:
        original = ordered_map_product.inspect_product_candidate
        with mock.patch.object(
            ordered_map_product, "inspect_product_candidate", wraps=original
        ) as replay, mock.patch.object(
            maintenance,
            "inspect_stack_successor",
            side_effect=AssertionError("OrderedMap actor used Stack maintenance"),
        ), mock.patch.object(
            resolver,
            "resolve_stack",
            side_effect=AssertionError("OrderedMap actor used Stack resolution"),
        ):
            result = ordered_map_maintenance.inspect_ordered_map_maintenance()
        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual(1, replay.call_count)
        self.assertEqual(
            0,
            len(
                inspect.signature(
                    ordered_map_maintenance.inspect_ordered_map_maintenance
                ).parameters
            ),
        )
        for call in (
            lambda: ordered_map_maintenance.inspect_ordered_map_maintenance(
                SUCCESSOR_MANIFEST
            ),
            lambda: ordered_map_maintenance.inspect_ordered_map_maintenance(
                manifest=SUCCESSOR_MANIFEST
            ),
            lambda: ordered_map_maintenance.inspect_ordered_map_maintenance(
                predecessor=self.source
            ),
        ):
            with self.assertRaises(TypeError):
                call()

    def test_successor_query_has_zero_candidates_and_exact_predecessor_recovery(self) -> None:
        result = self._observe()
        self.assertTrue(result.ok, result.diagnostics)
        self.assertTrue(result.predecessor_preserved)
        self.assertEqual((NEW_POLICY, NEW_SPECIFICATION), result.added_addresses)
        self.assertEqual(
            REALIZATIONS,
            tuple(
                item.realization for item in result.predecessor_resolution.candidates
            ),
        )
        self.assertTrue(
            all(
                item.semantic_status == "acceptable"
                for item in result.predecessor_resolution.candidates
            )
        )
        self.assertTrue(result.successor_resolution.ok)
        self.assertEqual((), result.successor_resolution.candidates)
        self.assertEqual(REALIZATIONS, result.recovery_candidates)

        selector_attacks = (
            (
                _without(self.successor, NEW_POLICY),
                "ORDERED_MAP_SUCCESSOR_SELECTOR_NOT_FOUND",
            ),
            (
                _without(self.successor, NEW_SPECIFICATION),
                "ORDERED_MAP_SUCCESSOR_SELECTOR_NOT_FOUND",
            ),
            (
                _without(self.successor, PROFILE),
                "ORDERED_MAP_SUCCESSOR_SELECTOR_NOT_FOUND",
            ),
            (
                _derived_graph(
                    self.successor,
                    PROFILE,
                    lambda item: item.update(kind="consumerPolicy"),
                ),
                "ORDERED_MAP_SUCCESSOR_SELECTOR_KIND",
            ),
            (
                _derived_graph(
                    self.successor,
                    NEW_POLICY,
                    lambda item: item["specification"].update(version="0.1.0"),
                ),
                "ORDERED_MAP_SUCCESSOR_POLICY_SELECTOR_MISMATCH",
            ),
            (
                _derived_graph(
                    self.successor,
                    NEW_POLICY,
                    lambda item: item["profile"].update(id="other"),
                ),
                "ORDERED_MAP_SUCCESSOR_POLICY_SELECTOR_MISMATCH",
            ),
        )
        for attacked, code in selector_attacks:
            with self.subTest(selector_failure=code):
                resolution = ordered_map_maintenance._resolve_ordered_map_successor(
                    attacked
                )
                self.assertFalse(resolution.ok)
                self.assertEqual((), resolution.candidates)
                self.assertIn(code, [item.code for item in resolution.diagnostics])

        synthetic_graph = _with_synthetic_successor_realization(self.successor)
        synthetic = ordered_map_maintenance._resolve_ordered_map_successor(
            synthetic_graph
        )
        self.assertTrue(synthetic.ok, synthetic.diagnostics)
        self.assertEqual(1, len(synthetic.candidates))
        candidate = synthetic.candidates[0]
        self.assertEqual(
            ("realization", "ordered-map-rust", "0.2.0"),
            candidate.realization,
        )
        self.assertEqual("unacceptable", candidate.semantic_status)
        self.assertTrue(
            all(item.status == "unsupported" for item in candidate.concerns[:3])
        )
        self.assertTrue(all(not item.supporting_evidence for item in candidate.concerns))
        self.assertTrue(candidate.prohibitions[0].blocks)
        self.assertEqual((), result.successor_resolution.candidates)

    def test_successor_theory_adds_size_and_size_put_but_promotes_no_assurance(self) -> None:
        result = self._observe()
        theory = result.successor_theory
        self.assertEqual(NEW_SPECIFICATION, theory.specification)
        self.assertEqual(20, len(theory.declarations))
        self.assertEqual(20, len(theory.unknowns))
        self.assertEqual((), theory.contradictions)
        self.assertTrue(
            all(item.observation == "unclaimed" and not item.claims for item in theory.declarations)
        )
        self.assertIn(
            ("observation", "size"),
            {(item.kind, item.declaration_id) for item in theory.declarations},
        )
        self.assertIn(
            ("law", "size-put"),
            {(item.kind, item.declaration_id) for item in theory.declarations},
        )
        performance = next(item for item in theory.declarations if item.kind == "performance")
        self.assertEqual("put-amortized-constant", performance.declaration_id)
        self.assertEqual("unclaimed", performance.observation)

    def test_predecessor_evidence_is_visible_history_not_successor_support(self) -> None:
        result = self._observe()
        expected = tuple(
            sorted(
                item.address
                for item in self.source.graph.records
                if item.address[0] == "evidence"
            )
        )
        self.assertEqual(14, len(expected))
        self.assertEqual(expected, tuple(item.address for item in result.stale_evidence))
        self.assertTrue(
            all(item.reason == "exact-specification-version" for item in result.stale_evidence)
        )
        self.assertFalse(
            any(
                item.address[2] == "0.2.0"
                and item.address[0] in {"realization", "claim", "evidence"}
                for item in self.successor.records
            )
        )

    def test_inspection_explains_zero_candidate_failure_and_nonautomatic_recovery(self) -> None:
        result = ordered_map_maintenance.inspect_ordered_map_maintenance()
        self.assertTrue(result.ok, result.diagnostics)
        for required in (
            "OrderedMap maintenance successor (exact versions; no discovery or execution)",
            "predecessor graph records: 33",
            "successor graph records: 35",
            "added records: consumerPolicy/ordered-map-bounded-policy/0.2.0, specification/ordered-map/0.2.0",
            "Successor theory: specification/ordered-map/0.2.0",
            "declarations: 20, unclaimed: 20",
            "observation size: observation=unclaimed",
            "law size-put: observation=unclaimed",
            "Successor semantic resolution: zero exact-version candidates",
            "historical predecessor Evidence: 14 (reason=exact-specification-version)",
            "Recovery candidates (not automatically selected)",
            "realization/ordered-map-rust/0.1.0",
            "realization/ordered-map-typescript/0.1.0",
            "No Evidence migration, latest selection, lineage, refinement, or compatibility inference.",
        ):
            self.assertIn(required, result.output)

    def test_predecessor_drift_and_invalid_graph_fail_before_any_decision(self) -> None:
        attacks = (
            (
                _derived_graph(
                    self.successor,
                    OLD_SPECIFICATION,
                    lambda item: item.update(version="changed"),
                ),
                "ORDERED_MAP_SUCCESSOR_PREDECESSOR_DRIFT",
            ),
            (
                _derived_graph(
                    self.successor,
                    OLD_POLICY,
                    lambda item: item.update(version="changed"),
                ),
                "ORDERED_MAP_SUCCESSOR_PREDECESSOR_DRIFT",
            ),
            (
                _derived_graph(
                    self.successor,
                    NEW_SPECIFICATION,
                    lambda item: item.update(version="changed"),
                ),
                "ORDERED_MAP_SUCCESSOR_CONTRACT_DRIFT",
            ),
            (
                _derived_graph(
                    self.successor,
                    NEW_POLICY,
                    lambda item: item.update(version="changed"),
                ),
                "ORDERED_MAP_SUCCESSOR_CONTRACT_DRIFT",
            ),
            (
                _without(self.successor, OLD_SPECIFICATION),
                "ORDERED_MAP_SUCCESSOR_PREDECESSOR_DRIFT",
            ),
            (
                _without(self.successor, OLD_POLICY),
                "ORDERED_MAP_SUCCESSOR_PREDECESSOR_DRIFT",
            ),
            (
                _without(self.successor, NEW_SPECIFICATION),
                "ORDERED_MAP_SUCCESSOR_CONTRACT_DRIFT",
            ),
            (
                _without(self.successor, NEW_POLICY),
                "ORDERED_MAP_SUCCESSOR_CONTRACT_DRIFT",
            ),
            (
                _with_synthetic_successor_realization(self.successor),
                "ORDERED_MAP_SUCCESSOR_UNEXPECTED_MEMBERSHIP",
            ),
        )
        for attacked, code in attacks:
            with self.subTest(drift=code):
                result = self._observe(attacked)
                self.assertFalse(result.ok)
                self.assertIsNone(result.predecessor_resolution)
                self.assertIsNone(result.successor_resolution)
                self.assertIsNone(result.successor_theory)
                self.assertIsNone(result.output)
                self.assertIn(code, [item.code for item in result.diagnostics])

        invalid = graph.GraphObservation(
            self.successor.records,
            (record_check.Diagnostic("O8_TEST_INVALID", "<graph>", "#"),),
        )
        result = self._observe(invalid)
        self.assertFalse(result.ok)
        self.assertIn(
            "ORDERED_MAP_SUCCESSOR_INVALID_GRAPH",
            [item.code for item in result.diagnostics],
        )

    def test_pinned_manifest_mutation_fails_before_graph_or_partial_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="o8-successor-") as raw:
            root = Path(raw) / "repository"
            shutil.copytree(REGISTRY, root / "registry/ordered-map")
            schema = ROOT / "schemas/registry-manifest.schema.json"
            (root / "schemas").mkdir(parents=True)
            shutil.copy2(schema, root / "schemas/registry-manifest.schema.json")
            manifest_path = root / SUCCESSOR_MANIFEST.relative_to(ROOT)
            manifest = _load(manifest_path)
            manifest["members"] = manifest["members"][:-1]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            observed = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            with mock.patch.object(
                ordered_map_maintenance, "_ROOT", root
            ), mock.patch.object(
                graph,
                "inspect_manifest_graph",
                side_effect=AssertionError("invalid authority reached graph capture"),
            ):
                result = ordered_map_maintenance.inspect_ordered_map_maintenance()
        self.assertFalse(result.ok)
        self.assertIsNone(result.successor_graph)
        self.assertIsNone(result.predecessor_resolution)
        self.assertIsNone(result.successor_resolution)
        self.assertIsNone(result.successor_theory)
        self.assertIsNone(result.output)
        self.assertEqual(1, len(result.diagnostics))
        diagnostic = result.diagnostics[0]
        self.assertEqual("ARTIFACT_RAW_DIGEST_MISMATCH", diagnostic.code)
        self.assertEqual(os.fspath(manifest_path), diagnostic.path)
        self.assertEqual("#", diagnostic.pointer)
        self.assertEqual(
            f"raw SHA-256 {observed}, expected {EXPECTED_SUCCESSOR_MANIFEST_SHA256}",
            diagnostic.message,
        )

    def test_observation_and_rendering_use_no_io_or_execution_after_capture(self) -> None:
        touched: list[str] = []

        def reject(name):
            def fail(*_args, **_kwargs):
                touched.append(name)
                raise AssertionError(f"maintenance observation attempted {name}")

            return fail

        with ExitStack() as stack:
            for owner, name in (
                (subprocess, "run"),
                (subprocess, "Popen"),
                (os, "system"),
                (os, "scandir"),
                (Path, "open"),
            ):
                stack.enter_context(mock.patch.object(owner, name, side_effect=reject(name)))
            result = self._observe()
            output = ordered_map_maintenance.render_ordered_map_maintenance(result)
        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual(result.output, output)
        self.assertEqual([], touched)

    def test_result_is_deterministic_immutable_and_has_one_public_shape(self) -> None:
        first = ordered_map_maintenance.inspect_ordered_map_maintenance()
        second = ordered_map_maintenance.inspect_ordered_map_maintenance()
        self.assertEqual(first, second)
        self.assertEqual(first.output, second.output)
        self.assertEqual(
            {
                "source",
                "successor_graph",
                "successor_manifest_raw_sha256",
                "predecessor_preserved",
                "added_addresses",
                "stale_evidence",
                "predecessor_resolution",
                "successor_resolution",
                "successor_theory",
                "recovery_candidates",
                "output",
                "diagnostics",
            },
            set(vars(first)),
        )
        self.assertEqual(
            {
                "source",
                "successor_graph",
                "successor_manifest_raw_sha256",
                "predecessor_preserved",
                "added_addresses",
                "stale_evidence",
                "predecessor_resolution",
                "successor_resolution",
                "successor_theory",
                "recovery_candidates",
                "output",
                "diagnostics",
                "ok",
            },
            {name for name in dir(first) if not name.startswith("_")},
        )
        self.assertIsInstance(first.added_addresses, tuple)
        self.assertIsInstance(first.stale_evidence, tuple)
        self.assertIsInstance(first.recovery_candidates, tuple)
        self.assertEqual(
            {"address", "reason"}, set(vars(first.stale_evidence[0]))
        )
        self.assertEqual(
            {"address", "reason"},
            {
                name
                for name in dir(first.stale_evidence[0])
                if not name.startswith("_")
            },
        )
        with self.assertRaises((AttributeError, TypeError)):
            first.output = "changed"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            first.stale_evidence[0].reason = "changed"  # type: ignore[misc]
        with self.assertRaises((AttributeError, TypeError)):
            first.recovery_candidates[0] = ("realization", "latest", "latest")  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
