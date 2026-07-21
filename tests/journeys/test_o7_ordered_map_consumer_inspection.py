from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import subprocess
import unittest
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest import mock

from scripts import record_check
from semantic_packages import canonical_artifact, graph, ordered_map_product, resolver


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "registry/ordered-map/consumers/package/records/ordered-map-bounded-policy.json"
MANIFEST = ROOT / "registry/ordered-map/manifest.json"
CONTRACT = ROOT / "contracts/ordered-map/product-contract.json"
CONTRACT_SCHEMA = ROOT / "schemas/ordered-map-product-contract.schema.json"
WRAPPER = ROOT / "semantic_packages/ordered_map_product.py"
REGISTRATION = ROOT / "semantic_packages/registration.py"
POLICY_ADDRESS = ("consumerPolicy", "ordered-map-bounded-policy", "0.1.0")
SPECIFICATION = ("specification", "ordered-map", "0.1.0")
PROFILE = ("realizationProfile", "ordered-map-ascii-fold", "0.1.0")
RUST = ("realization", "ordered-map-rust", "0.1.0")
TYPESCRIPT = ("realization", "ordered-map-typescript", "0.1.0")
REALIZATIONS = (RUST, TYPESCRIPT)

EXPECTED_RAW_SHA256 = {
    POLICY: "6d0d215df3407660fd381e097dba70f8f80196d5f246eacb933358095817291c",
    MANIFEST: "0dae972b40c850f691df0856577cf8a9d66449a4655dcbb0c328b20c6993455d",
    WRAPPER: "1ea1f5d9cd0bd4768a72c6188560f641f2f78399e68cffc842398b5f4f4cbbc8",
    REGISTRATION: "dbe700f613a37b3c25188952f368ef824431e0eca081fa3803e56e4e1d4882a4",
    CONTRACT_SCHEMA: "1e14d61de6f30eee5fe16f121450d21d5d342bf99d0468bfc7c08e1c26a2ab36",
}
EXPECTED_CONTRACT_CANONICAL_SHA256 = (
    "4bfbc89ed7e061fa9f2c38f02a99331af1e9a05f5d111bea391b2034ac14eb17"
)

try:
    ordered_map_resolution = importlib.import_module(
        "semantic_packages.ordered_map_resolution"
    )
    ordered_map_inspection = importlib.import_module(
        "semantic_packages.ordered_map_inspection"
    )
    CONSUMER_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as error:
    if error.name not in {
        "semantic_packages.ordered_map_resolution",
        "semantic_packages.ordered_map_inspection",
    }:
        raise
    ordered_map_resolution = None
    ordered_map_inspection = None
    CONSUMER_IMPORT_ERROR = error


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate(result, realization):
    return next(item for item in result.candidates if item.realization == realization)


def _concern(candidate, concern):
    return next(item for item in candidate.concerns if item.concern == concern)


def _derived_graph(observation, address, mutate):
    """Create a detached breaker control; never an accepted manifest candidate."""

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
    if len(records) != len(observation.records):
        raise AssertionError("derived graph changed the record census")
    return graph.GraphObservation(tuple(records), ())


def _without(observation, *addresses):
    removed = frozenset(addresses)
    return graph.GraphObservation(
        tuple(item for item in observation.records if item.address not in removed),
        (),
    )


class OrderedMapConsumerPreconditionTest(unittest.TestCase):
    def test_o6g_accepted_bytes_and_graph_are_the_only_predecessor(self) -> None:
        self.assertEqual(
            EXPECTED_RAW_SHA256,
            {path: _raw_sha256(path) for path in EXPECTED_RAW_SHA256},
        )
        contract = canonical_artifact.inspect_json_artifact(
            CONTRACT,
            schema_path=CONTRACT_SCHEMA,
            expected_canonical_sha256=EXPECTED_CONTRACT_CANONICAL_SHA256,
            label="O6-G accepted OrderedMap ProductContract",
        )
        self.assertTrue(contract.ok, contract.diagnostics)
        source = ordered_map_product.inspect_product_candidate()
        self.assertTrue(source.ok, source.diagnostics)
        self.assertEqual(33, len(source.graph.records))
        self.assertEqual(18, len(source.theory.declarations))
        self.assertEqual(
            frozenset(REALIZATIONS),
            frozenset(
                item.address
                for item in source.graph.records
                if item.address in REALIZATIONS
            ),
        )

    def test_ordered_map_consumer_boundary_is_the_only_red_predecessor(self) -> None:
        self.assertIsNotNone(
            ordered_map_resolution,
            "O7-P intentionally precedes ordered_map_resolution.py and "
            f"ordered_map_inspection.py; observed {CONSUMER_IMPORT_ERROR!r}",
        )
        self.assertIsNotNone(ordered_map_inspection)


@unittest.skipUnless(
    ordered_map_resolution is not None and ordered_map_inspection is not None,
    "O7-P freezes the consumer contract before its implementation",
)
class OrderedMapConsumerContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = ordered_map_product.inspect_product_candidate()
        self.assertTrue(self.source.ok, self.source.diagnostics)

    def _resolve(self, observation=None):
        return ordered_map_resolution.resolve_ordered_map(
            self.source.graph if observation is None else observation
        )

    def test_actor_is_zero_argument_one_replay_and_never_calls_stack_resolution(self) -> None:
        original = ordered_map_product.inspect_product_candidate
        with mock.patch.object(
            ordered_map_product, "inspect_product_candidate", wraps=original
        ) as capture, mock.patch.object(
            resolver,
            "resolve_stack",
            side_effect=AssertionError("OrderedMap actor called Stack resolution"),
        ):
            result = ordered_map_inspection.inspect_ordered_map()

        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual(1, capture.call_count)
        self.assertEqual(0, len(inspect.signature(ordered_map_inspection.inspect_ordered_map).parameters))
        self.assertEqual(
            ["observation"],
            list(inspect.signature(ordered_map_resolution.resolve_ordered_map).parameters),
        )
        for call in (
            lambda: ordered_map_inspection.inspect_ordered_map(CONTRACT),
            lambda: ordered_map_inspection.inspect_ordered_map(graph=self.source.graph),
            lambda: ordered_map_inspection.inspect_ordered_map(policy=POLICY_ADDRESS),
        ):
            with self.assertRaises(TypeError):
                call()
        for call in (
            lambda: ordered_map_resolution.resolve_ordered_map(
                self.source.graph, policy=POLICY_ADDRESS
            ),
            lambda: ordered_map_resolution.resolve_ordered_map(
                self.source.graph, profile=PROFILE
            ),
            lambda: ordered_map_resolution.resolve_ordered_map(
                self.source.graph, specification=SPECIFICATION
            ),
            lambda: ordered_map_resolution.resolve_ordered_map(
                self.source.graph, contract=CONTRACT
            ),
        ):
            with self.assertRaises(TypeError):
                call()

    def test_accepted_graph_yields_two_explainable_semantic_decisions(self) -> None:
        result = self._resolve()
        self.assertTrue(result.ok, result.diagnostics)
        self.assertEqual(REALIZATIONS, tuple(item.realization for item in result.candidates))
        for candidate in result.candidates:
            with self.subTest(candidate=candidate.realization):
                prefix = candidate.realization[1]
                expected_law = tuple(
                    (
                        "evidence",
                        f"{prefix}-{declaration}-conformance",
                        "0.1.0",
                    )
                    for declaration in (
                        "lookup-empty",
                        "lookup-put-other",
                        "lookup-put-same",
                        "put-existing-position",
                        "put-new-appends",
                    )
                )
                expected_resource = (
                    ("evidence", f"{prefix}-persistence-conformance", "0.1.0"),
                )
                expected_effect = (
                    (
                        "evidence",
                        f"{prefix}-ordered-map-effects-conformance",
                        "0.1.0",
                    ),
                )
                self.assertEqual("acceptable", candidate.semantic_status)
                for concern in (
                    "law.conformance",
                    "resource.persistence",
                    "effect.conformance",
                ):
                    disposition = _concern(candidate, concern)
                    self.assertEqual("satisfied", disposition.status)
                    self.assertFalse(disposition.blocks)
                self.assertEqual(
                    expected_law,
                    _concern(candidate, "law.conformance").supporting_evidence,
                )
                self.assertEqual(
                    expected_resource,
                    _concern(candidate, "resource.persistence").supporting_evidence,
                )
                self.assertEqual(
                    expected_effect,
                    _concern(candidate, "effect.conformance").supporting_evidence,
                )
                performance = _concern(candidate, "performance")
                self.assertEqual("optional", performance.priority)
                self.assertEqual("unsupported", performance.status)
                self.assertFalse(performance.blocks)
                self.assertEqual("satisfied", candidate.prohibitions[0].status)
                self.assertEqual(
                    expected_effect,
                    candidate.prohibitions[0].supporting_evidence,
                )

    def test_theory_consumer_keeps_all_eighteen_declarations_unclaimed(self) -> None:
        result = ordered_map_inspection.inspect_ordered_map()
        theory = result.source.theory
        self.assertEqual(18, len(theory.declarations))
        self.assertEqual(18, len(theory.unknowns))
        self.assertEqual((), theory.contradictions)
        self.assertTrue(
            all(item.observation == "unclaimed" and not item.claims for item in theory.declarations)
        )
        performance = next(
            item
            for item in theory.declarations
            if item.kind == "performance" and item.declaration_id == "put-amortized-constant"
        )
        self.assertEqual("unclaimed", performance.observation)
        self.assertNotIn("supported-observation", result.output)

    def test_inspection_surfaces_every_evidence_axis_and_separate_boundary(self) -> None:
        result = ordered_map_inspection.inspect_ordered_map()
        self.assertTrue(result.ok, result.diagnostics)
        output = result.output
        for required in (
            "Accepted OrderedMap product authority (no discovery or execution)",
            "graph records: 33",
            "theory declarations: 18, unclaimed: 18",
            "package ordered-map-rust: records=17",
            "package ordered-map-typescript: records=17",
            "realization/ordered-map-rust/0.1.0: semantic=acceptable",
            "realization/ordered-map-typescript/0.1.0: semantic=acceptable",
            "law.conformance: status=satisfied priority=required blocks=no",
            "resource.persistence: status=satisfied priority=required blocks=no",
            "effect.conformance: status=satisfied priority=required blocks=no",
            "performance: status=unsupported priority=optional blocks=no",
            "supporting Evidence:",
            "supporting Evidence: evidence/ordered-map-rust-lookup-empty-conformance/0.1.0 mechanism=bounded-conformance-campaign result=supports review=accepted disposition=selected-applicable",
            "supporting Evidence: evidence/ordered-map-typescript-ordered-map-effects-conformance/0.1.0 mechanism=bounded-conformance-campaign result=supports review=accepted disposition=selected-applicable",
            "challenging Evidence: none",
            "inconclusive Evidence: none",
            "error Evidence: none",
            "inapplicable Evidence: none",
            "unselected Evidence: none",
            "Directional realization boundary (not semantic acceptance)",
            "direction=consumer-to-realization mechanism=child-process-ndjson direct=no",
        ):
            self.assertIn(required, output)
        for implementation in ("rust", "typescript"):
            for declaration in (
                "lookup-empty",
                "lookup-put-other",
                "lookup-put-same",
                "ordered-map-effects",
                "persistence",
                "put-existing-position",
                "put-new-appends",
            ):
                self.assertIn(
                    "supporting Evidence: "
                    f"evidence/ordered-map-{implementation}-{declaration}-conformance/0.1.0 "
                    "mechanism=bounded-conformance-campaign result=supports "
                    "review=accepted disposition=selected-applicable",
                    output,
                )

    def test_selected_breaker_challenge_rejects_only_its_candidate(self) -> None:
        evidence = (
            "evidence",
            "ordered-map-rust-put-existing-position-conformance",
            "0.1.0",
        )
        attacked = _derived_graph(
            self.source.graph,
            evidence,
            lambda document: document.update(result="challenges"),
        )
        result = self._resolve(attacked)
        rust = _candidate(result, RUST)
        typescript = _candidate(result, TYPESCRIPT)
        self.assertEqual("unacceptable", rust.semantic_status)
        self.assertEqual("contested", _concern(rust, "law.conformance").status)
        self.assertEqual((evidence,), _concern(rust, "law.conformance").challenging_evidence)
        self.assertEqual("child-process-ndjson", rust.boundary.mechanism)
        self.assertEqual("acceptable", typescript.semantic_status)
        self.assertEqual(33, len(self.source.graph.records))
        canonical = _candidate(self._resolve(), RUST)
        self.assertEqual("acceptable", canonical.semantic_status)

        derived_source = replace(self.source, graph=attacked)
        with mock.patch.object(
            ordered_map_product,
            "inspect_product_candidate",
            return_value=derived_source,
        ):
            actor_result = ordered_map_inspection.inspect_ordered_map()
        actor_rust = _candidate(actor_result.resolution, RUST)
        self.assertEqual("unacceptable", actor_rust.semantic_status)
        self.assertIn(
            "realization/ordered-map-rust/0.1.0: semantic=unacceptable",
            actor_result.output,
        )
        self.assertIn(
            "challenging Evidence: "
            "evidence/ordered-map-rust-put-existing-position-conformance/0.1.0 "
            "mechanism=bounded-conformance-campaign result=challenges "
            "review=accepted disposition=selected-applicable",
            actor_result.output,
        )

    def test_non_supporting_evidence_axes_remain_visible_and_cannot_satisfy(self) -> None:
        evidence = (
            "evidence",
            "ordered-map-rust-lookup-empty-conformance",
            "0.1.0",
        )
        attacks = (
            (lambda item: item.update(result="inconclusive"), "inconclusive_evidence"),
            (lambda item: item.update(result="error"), "error_evidence"),
            (lambda item: item.update(reviewState="rejected"), "unselected_evidence"),
            (lambda item: item["applicability"].update(profiles=[]), "inapplicable_evidence"),
            (lambda item: item.update(mechanism="assertion"), "unselected_evidence"),
        )
        for mutate, field in attacks:
            with self.subTest(field=field):
                attacked = _derived_graph(self.source.graph, evidence, mutate)
                rust = _candidate(self._resolve(attacked), RUST)
                law = _concern(rust, "law.conformance")
                self.assertEqual("unacceptable", rust.semantic_status)
                self.assertEqual("unsupported", law.status)
                self.assertEqual((evidence,), getattr(law, field))
                self.assertIn("lookup-empty", law.missing_declarations)

    def test_missing_claim_and_evidence_fail_closed_without_vacuous_support(self) -> None:
        attacked = _without(
            self.source.graph,
            ("claim", "ordered-map-rust-lookup-empty", "0.1.0"),
            ("evidence", "ordered-map-rust-lookup-empty-conformance", "0.1.0"),
        )
        rust = _candidate(self._resolve(attacked), RUST)
        law = _concern(rust, "law.conformance")
        self.assertEqual("unacceptable", rust.semantic_status)
        self.assertEqual("unsupported", law.status)
        self.assertIn("lookup-empty", law.missing_declarations)
        self.assertIn("missing-claim", law.reasons)

        invalid = self._resolve(
            graph.GraphObservation(
                self.source.graph.records,
                (record_check.Diagnostic("O7_TEST_INVALID", "<graph>", "#"),),
            )
        )
        self.assertFalse(invalid.ok)
        self.assertEqual((), invalid.candidates)
        self.assertIn(
            "ORDERED_MAP_RESOLUTION_INVALID_GRAPH",
            [item.code for item in invalid.diagnostics],
        )

        for selector in (POLICY_ADDRESS, PROFILE, SPECIFICATION):
            with self.subTest(missing=selector):
                missing = self._resolve(_without(self.source.graph, selector))
                self.assertFalse(missing.ok)
                self.assertEqual((), missing.candidates)
                self.assertIn(
                    "ORDERED_MAP_RESOLUTION_SELECTOR_NOT_FOUND",
                    [item.code for item in missing.diagnostics],
                )

    def test_effect_provenance_and_policy_tokens_fail_closed(self) -> None:
        effect = (
            "evidence",
            "ordered-map-rust-ordered-map-effects-conformance",
            "0.1.0",
        )
        attacked = _derived_graph(
            self.source.graph,
            effect,
            lambda item: item["provenance"]["plan"].update(
                canonicalSha256="0" * 64
            ),
        )
        rust = _candidate(self._resolve(attacked), RUST)
        self.assertEqual("unacceptable", rust.semantic_status)
        self.assertEqual("unsupported", rust.prohibitions[0].status)
        self.assertEqual("child-process-ndjson", rust.boundary.mechanism)

        effect_attacks = (
            (lambda item: item.update(result="challenges"), "contested", "challenging_evidence"),
            (lambda item: item.update(result="inconclusive"), "unsupported", "inconclusive_evidence"),
            (lambda item: item.update(result="error"), "unsupported", "error_evidence"),
            (lambda item: item.update(reviewState="rejected"), "unsupported", "unselected_evidence"),
            (lambda item: item["applicability"].update(profiles=[]), "unsupported", "inapplicable_evidence"),
        )
        for mutate, status, field in effect_attacks:
            with self.subTest(effect_axis=field):
                attacked = _derived_graph(self.source.graph, effect, mutate)
                prohibition = _candidate(self._resolve(attacked), RUST).prohibitions[0]
                self.assertEqual(status, prohibition.status)
                self.assertEqual((effect,), getattr(prohibition, field))
                self.assertTrue(prohibition.blocks)

        blocking_policy_attacks = (
            lambda item: item["concerns"][0].update(minimumAssurance="unknown"),
            lambda item: item["concerns"][0].update(acceptedMechanisms=[]),
            lambda item: item["prohibitions"][0].update(acceptedEvidenceScope=[]),
        )
        for mutate in blocking_policy_attacks:
            with self.subTest(policy_attack=mutate):
                attacked = _derived_graph(self.source.graph, POLICY_ADDRESS, mutate)
                result = self._resolve(attacked)
                self.assertTrue(result.ok, result.diagnostics)
                self.assertEqual(2, len(result.candidates))
                self.assertTrue(
                    all(item.semantic_status == "unacceptable" for item in result.candidates)
                )

        binding_attacks = (
            lambda item: item.update(
                specification={
                    "kind": "specification",
                    "id": "other",
                    "version": "0.1.0",
                }
            ),
            lambda item: item.update(
                profile={
                    "kind": "realizationProfile",
                    "id": "other",
                    "version": "0.1.0",
                }
            ),
        )
        for mutate in binding_attacks:
            with self.subTest(policy_binding=mutate):
                attacked = _derived_graph(self.source.graph, POLICY_ADDRESS, mutate)
                result = self._resolve(attacked)
                self.assertFalse(result.ok)
                self.assertEqual((), result.candidates)
                self.assertIn(
                    "ORDERED_MAP_RESOLUTION_POLICY_SELECTOR_MISMATCH",
                    [item.code for item in result.diagnostics],
                )

        mismatch = _derived_graph(
            self.source.graph,
            PROFILE,
            lambda item: item.update(kind="consumerPolicy"),
        )
        result = self._resolve(mismatch)
        self.assertFalse(result.ok)
        self.assertEqual((), result.candidates)
        self.assertIn(
            "ORDERED_MAP_RESOLUTION_SELECTOR_KIND",
            [item.code for item in result.diagnostics],
        )

    def test_directional_boundary_neither_grants_nor_revokes_semantic_status(self) -> None:
        attacked = _derived_graph(
            self.source.graph,
            RUST,
            lambda item: item["implementation"].update(interfaceMechanism="in-process FFI"),
        )
        rust = _candidate(self._resolve(attacked), RUST)
        self.assertEqual("acceptable", rust.semantic_status)
        self.assertEqual("unsupported-interface", rust.boundary.mechanism)
        self.assertFalse(rust.boundary.direct)

    def test_product_failure_returns_no_decision_or_partial_inspection(self) -> None:
        failure = ordered_map_product.ProductCandidateObservation(
            None,
            None,
            (),
            None,
            None,
            (record_check.Diagnostic("O7_TEST_FAILURE", "<product>", "#"),),
        )
        with mock.patch.object(
            ordered_map_product, "inspect_product_candidate", return_value=failure
        ):
            result = ordered_map_inspection.inspect_ordered_map()
        self.assertFalse(result.ok)
        self.assertIs(result.source, failure)
        self.assertIsNone(result.resolution)
        self.assertIsNone(result.output)
        self.assertEqual(["O7_TEST_FAILURE"], [item.code for item in result.diagnostics])

    def test_resolution_and_rendering_are_pure_after_accepted_capture(self) -> None:
        touched: list[str] = []

        def reject(name):
            def fail(*_args, **_kwargs):
                touched.append(name)
                raise AssertionError(f"post-capture consumer attempted {name}")

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
            decision = self._resolve()
            output = ordered_map_inspection.render_ordered_map_inspection(
                self.source, decision
            )
        self.assertTrue(decision.ok, decision.diagnostics)
        self.assertIn("semantic=acceptable", output)
        self.assertEqual([], touched)

    def test_inspection_is_deterministic_and_uses_only_frozen_public_fields(self) -> None:
        first = ordered_map_inspection.inspect_ordered_map()
        second = ordered_map_inspection.inspect_ordered_map()
        self.assertEqual(first.output, second.output)
        self.assertEqual(
            {"source", "resolution", "output", "diagnostics"},
            set(vars(first)),
        )
        self.assertEqual(
            {"ok", "source", "resolution", "output", "diagnostics"},
            {name for name in dir(first) if not name.startswith("_")},
        )


if __name__ == "__main__":
    unittest.main()
