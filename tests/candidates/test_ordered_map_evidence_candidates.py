from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

from scripts import record_check


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/ordered_map_evidence_check.py"
SPECIFICATION_PATH = Path("registry/ordered-map/theory/records/ordered-map-spec.json")
PROFILE_PATH = Path(
    "registry/ordered-map/theory/dependencies/ordered-map-profile.json"
)
SPECIFICATION = {"kind": "specification", "id": "ordered-map", "version": "0.1.0"}
PROFILE = {
    "kind": "realizationProfile",
    "id": "ordered-map-ascii-fold",
    "version": "0.1.0",
}
DECLARATIONS = {
    "lookup-empty": "law.conformance",
    "lookup-put-same": "law.conformance",
    "lookup-put-other": "law.conformance",
    "put-existing-position": "law.conformance",
    "put-new-appends": "law.conformance",
    "persistence": "resource.persistence",
    "ordered-map-effects": "effect.conformance",
}
CANDIDATES = {
    "rust": {
        "id": "ordered-map-rust",
        "adapter": "ordered-map-rust-json-adapter",
        "entrypoint": "implementations/ordered-map/rust/src/main.rs",
        "report": Path("reports/ordered-map/rust-campaign-report.json"),
        "recordRoot": Path("registry/ordered-map/packages/rust/records"),
        "implementation": {
            "language": "Rust",
            "languageVersion": "1.96.1",
            "target": "local native child process",
            "runtime": "native executable",
            "interfaceMechanism": "NDJSON messages over stdin and stdout",
            "buildSystem": "direct rustc, edition 2024",
            "buildInstructions": (
                "Use RUSTC with the explicit GCC linker as documented in "
                "implementations/ordered-map/rust/README.md."
            ),
            "executionInstructions": "Run the built adapter as a lockstep child process.",
        },
    },
    "typescript": {
        "id": "ordered-map-typescript",
        "adapter": "ordered-map-typescript-json-adapter",
        "entrypoint": "implementations/ordered-map/typescript/adapter.ts",
        "report": Path("reports/ordered-map/typescript-campaign-report.json"),
        "recordRoot": Path("registry/ordered-map/packages/typescript/records"),
        "implementation": {
            "language": "TypeScript",
            "languageVersion": "6.0.3",
            "target": "local Deno child process",
            "runtime": "Deno 2.9.2",
            "interfaceMechanism": "NDJSON messages over stdin and stdout",
            "buildSystem": "dependency-free Deno check",
            "buildInstructions": (
                "Run the offline Deno check documented in "
                "implementations/ordered-map/typescript/README.md."
            ),
            "executionInstructions": (
                "Run adapter.ts with Deno's no-config, no-lock, no-npm, no-remote, "
                "and no-prompt flags."
            ),
        },
    },
}
CAPABILITIES = [
    "ordered-map.empty",
    "ordered-map.put",
    "ordered-map.lookup",
    "ordered-map.entries",
]
LIMITATIONS = [
    "Evidence is bounded to ordered-map-ascii-fold/0.1.0 and its exact campaign.",
    "Reported events cover only the adapter-observed invocation boundary.",
    "No performance, concurrency, remote transport, registry discovery, or interoperation claim.",
]
REVIEW_LINEAGE = (
    "O-R6d6 PASS; retained report fact independently reproduced three consecutive times."
)
PRODUCED_AT = "2026-07-19T21:11:33Z"
ENVIRONMENTS = {
    "rust": {
        "runnerProtocol": "ordered-map-runner-json-v1",
        "python": "3.14.6",
        "jsonschema": "4.26.0",
        "referencing": "0.37.0",
        "rustc": "1.96.1 (31fca3adb)",
        "gcc": "15.2.0",
    },
    "typescript": {
        "runnerProtocol": "ordered-map-runner-json-v1",
        "python": "3.14.6",
        "jsonschema": "4.26.0",
        "referencing": "0.37.0",
        "deno": "2.9.2",
        "v8": "14.9.207.2-rusty",
        "typescript": "6.0.3",
    },
}
APPLICABILITY_PARAMETERS = {
    "keyDomain": ["A", "a", "B", "b", "C", "c"],
    "valueMinimum": -2,
    "valueMaximum": 2,
    "maximumHistory": 3,
    "maximumLiveClasses": 3,
    "observationLimit": 3,
    "responseTimeoutSeconds": 0.2,
    "exitTimeoutSeconds": 0.2,
}


def _record_paths(candidate: dict) -> list[Path]:
    root = candidate["recordRoot"]
    prefix = candidate["id"]
    return [
        root / f"{prefix}-realization.json",
        *[
            root / f"{prefix}-{declaration}-claim.json"
            for declaration in DECLARATIONS
        ],
        *[
            root / f"{prefix}-{declaration}-evidence.json"
            for declaration in DECLARATIONS
        ],
    ]


def _claim_scope(candidate: dict, declaration: str) -> str:
    if declaration == "ordered-map-effects":
        return (
            f"adapter-reported invocation events for {candidate['id']} through "
            f"{candidate['adapter']} under ordered-map-ascii-fold."
        )
    return (
        f"{candidate['id']} through {candidate['adapter']} under "
        "ordered-map-ascii-fold."
    )


def _claim_assumptions(declaration: str) -> list[str]:
    if declaration == "ordered-map-effects":
        return ["Reported events are complete for the adapter-observed boundary."]
    return ["The adapter faithfully exposes the named Realization."]


def _claim_exclusions(declaration: str) -> list[str]:
    if declaration == "ordered-map-effects":
        return ["Effects outside the adapter-reported invocation boundary are not observed."]
    return ["No behavior outside the exact bounded campaign is asserted."]


def _evidence_method(declaration: str) -> str:
    if declaration == "ordered-map-effects":
        subject = "adapter-reported invocation-event campaign"
    elif declaration == "persistence":
        subject = "retained-source observation campaign"
    else:
        subject = "OrderedMap campaign report"
    return f"O-R6d6-reviewed {subject} for one declaration under the exact plan."


def _evidence_assumptions(declaration: str) -> list[str]:
    first = (
        "Reported events are complete for the adapter-observed boundary."
        if declaration == "ordered-map-effects"
        else "The adapter faithfully exposes the named Realization."
    )
    return [first, "The runner and O-R6d6 review correctly enforce the recorded checks."]


def _evidence_exclusions(declaration: str) -> list[str]:
    if declaration == "ordered-map-effects":
        return [
            "Effects outside the adapter-reported invocation boundary are not observed.",
            "No general external-effect, performance, concurrency, remote, or interoperation conclusion.",
        ]
    if declaration == "persistence":
        return [
            "Support is bounded to the exact plan, profile, report, and process session.",
            "No post-termination, performance, concurrency, remote, or interoperation conclusion.",
        ]
    return [
        "Support is bounded to the exact plan, profile, report, and process session.",
        "No performance, malformed-client, concurrency, remote, or interoperation conclusion.",
    ]


RECORD_PATHS = [path for candidate in CANDIDATES.values() for path in _record_paths(candidate)]
BOUNDARY_EXISTS = CHECKER.is_file() and all((ROOT / path).is_file() for path in RECORD_PATHS)


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_json(relative: Path) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _package_entries() -> set[Path]:
    return {
        path.relative_to(ROOT)
        for candidate in CANDIDATES.values()
        for path in (ROOT / candidate["recordRoot"]).rglob("*")
        if path.is_file() or path.is_symlink()
    }


def _package_json_documents() -> list[dict]:
    return [
        _load_json(path)
        for path in sorted(_package_entries())
        if path.suffix == ".json"
    ]


def _load_checker():
    spec = importlib.util.spec_from_file_location("ordered_map_evidence_check", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expected_provenance(candidate: dict, declaration: str, report: dict) -> dict:
    outcome = next(
        item for item in report["outcome"]["declarations"] if item["id"] == declaration
    )
    return {
        "declaration": declaration,
        "report": {
            "path": candidate["report"].as_posix(),
            "sha256": hashlib.sha256((ROOT / candidate["report"]).read_bytes()).hexdigest(),
        },
        "reportCandidate": candidate["id"],
        "reportPacketRole": "candidate",
        "declarationOutcome": outcome,
        "plan": report["inputs"]["plan"],
        "specification": report["inputs"]["specification"],
        "profile": report["inputs"]["profile"],
        "runner": report["inputs"]["runner"],
        "harness": report["inputs"]["harness"],
        "sources": report["inputs"]["sources"],
        "commandsCanonicalSha256": _canonical_sha256(report["commands"]),
        "toolchainCanonicalSha256": _canonical_sha256(report["toolchain"]),
        "outcomeCanonicalSha256": _canonical_sha256(report["outcome"]),
        "binarySha256": report["binarySha256"],
        "review": REVIEW_LINEAGE,
    }


class OrderedMapEvidencePreconditionTest(unittest.TestCase):
    def test_retained_reports_are_candidate_facts_only(self) -> None:
        self.assertEqual(
            {"rust-campaign-report.json", "typescript-campaign-report.json"},
            {candidate["report"].name for candidate in CANDIDATES.values()},
        )
        for package, candidate in CANDIDATES.items():
            path = ROOT / candidate["report"]
            self.assertTrue(path.is_file(), path)
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(candidate["id"], report["candidate"])
            self.assertEqual("candidate", report["packetRole"])
            self.assertEqual("supports", report["outcome"]["result"])
            self.assertEqual(
                set(DECLARATIONS),
                {item["id"] for item in report["outcome"]["declarations"]},
            )
            self.assertTrue(
                all(
                    item["result"] == "supports" and not item["causes"]
                    for item in report["outcome"]["declarations"]
                )
            )
            self.assertFalse(
                {"claim", "evidence", "reviewState", "authority", "manifest"}
                & set(report)
            )


class OrderedMapEvidenceCandidateContractTest(unittest.TestCase):
    def test_candidate_record_boundary_exists(self) -> None:
        missing = [
            path.as_posix()
            for path in [Path("scripts/ordered_map_evidence_check.py"), *RECORD_PATHS]
            if not (ROOT / path).is_file()
        ]
        self.assertEqual([], missing)

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_exact_inventory_graph_and_candidate_checker_pass(self) -> None:
        expected = set(RECORD_PATHS)
        actual = _package_entries()
        self.assertEqual(expected, actual)
        diagnostics = record_check.validate_graph_paths(
            [
                (ROOT / SPECIFICATION_PATH).as_posix(),
                (ROOT / PROFILE_PATH).as_posix(),
                *[
                    (ROOT / candidate["recordRoot"]).as_posix()
                    for candidate in CANDIDATES.values()
                ],
            ]
        )
        self.assertEqual([], [item.format() for item in diagnostics])
        checker = _load_checker()
        errors, summary = checker.run_ordered_map_evidence_candidate_checks(ROOT)
        self.assertEqual([], errors)
        self.assertEqual(
            "OrderedMap Evidence candidate checks passed: 2 Realizations, 14 Claims, 14 Evidence records.",
            summary,
        )

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_realizations_have_exact_package_local_execution_envelopes(self) -> None:
        for candidate in CANDIDATES.values():
            realization = _load_json(_record_paths(candidate)[0])
            self.assertEqual(
                {
                    "kind",
                    "id",
                    "version",
                    "specification",
                    "adapter",
                    "implementation",
                    "capabilities",
                    "limitations",
                    "supportedProfiles",
                },
                set(realization),
            )
            self.assertEqual("realization", realization["kind"])
            self.assertEqual(candidate["id"], realization["id"])
            self.assertEqual("0.1.0", realization["version"])
            self.assertEqual(SPECIFICATION, realization["specification"])
            self.assertEqual(
                {
                    "id": candidate["adapter"],
                    "version": "0.1.0",
                    "protocol": "ordered-map-runner-json-v1",
                    "entrypoint": candidate["entrypoint"],
                    "assumptions": [
                        "The adapter faithfully exposes the named Realization.",
                        "Reported events are complete for the adapter-observed boundary.",
                    ],
                },
                realization["adapter"],
            )
            self.assertEqual(candidate["implementation"], realization["implementation"])
            self.assertEqual(CAPABILITIES, realization["capabilities"])
            self.assertEqual(LIMITATIONS, realization["limitations"])
            self.assertEqual([PROFILE], realization["supportedProfiles"])

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_claims_are_exact_active_declaration_scopes(self) -> None:
        for candidate in CANDIDATES.values():
            records = [_load_json(path) for path in _record_paths(candidate)]
            claims = {record["proposition"]["declarationId"]: record for record in records if record["kind"] == "claim"}
            self.assertEqual(set(DECLARATIONS), set(claims))
            for declaration, concern in DECLARATIONS.items():
                claim = claims[declaration]
                claim_id = f"{candidate['id']}-{declaration}"
                self.assertEqual(claim_id, claim["id"])
                self.assertEqual("0.1.0", claim["version"])
                self.assertEqual(
                    {"kind": "realization", "id": candidate["id"], "version": "0.1.0"},
                    claim["subject"],
                )
                self.assertEqual(SPECIFICATION, claim["governingSpecification"])
                self.assertEqual(
                    {"specification": SPECIFICATION, "declarationId": declaration},
                    claim["proposition"],
                )
                self.assertEqual(concern, claim["concern"])
                self.assertEqual(_claim_scope(candidate, declaration), claim["scope"])
                self.assertEqual(_claim_assumptions(declaration), claim["assumptions"])
                self.assertEqual(_claim_exclusions(declaration), claim["exclusions"])
                self.assertEqual([PROFILE], claim["applicableProfiles"])
                self.assertEqual("active", claim["state"])

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_evidence_axes_and_review_lineage_are_independent_and_exact(self) -> None:
        for package, candidate in CANDIDATES.items():
            records = [_load_json(path) for path in _record_paths(candidate)]
            evidence_records = {
                record["provenance"]["declaration"]: record
                for record in records
                if record["kind"] == "evidence"
            }
            self.assertEqual(set(DECLARATIONS), set(evidence_records))
            for declaration, evidence in evidence_records.items():
                self.assertEqual(
                    f"{candidate['id']}-{declaration}-conformance", evidence["id"]
                )
                self.assertEqual(
                    {"kind": "claim", "id": f"{candidate['id']}-{declaration}", "version": "0.1.0"},
                    evidence["claim"],
                )
                self.assertEqual(SPECIFICATION, evidence["specification"])
                self.assertEqual("realization", evidence["scope"])
                self.assertEqual(
                    {"kind": "realization", "id": candidate["id"], "version": "0.1.0"},
                    evidence["realization"],
                )
                self.assertEqual(
                    {"id": candidate["adapter"], "version": "0.1.0"},
                    evidence["adapter"],
                )
                self.assertEqual("bounded-conformance-campaign", evidence["mechanism"])
                self.assertEqual("supports", evidence["result"])
                self.assertEqual("accepted", evidence["reviewState"])
                self.assertEqual(_evidence_method(declaration), evidence["method"])
                self.assertEqual(ENVIRONMENTS[package], evidence["environment"])
                self.assertEqual({"producedAt": PRODUCED_AT}, evidence["freshness"])
                self.assertEqual(
                    _evidence_assumptions(declaration), evidence["assumptions"]
                )
                self.assertEqual(_evidence_exclusions(declaration), evidence["exclusions"])
                self.assertEqual(
                    {"profiles": [PROFILE], "parameters": APPLICABILITY_PARAMETERS},
                    evidence["applicability"],
                )

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_every_evidence_provenance_equals_its_retained_report_fact(self) -> None:
        for candidate in CANDIDATES.values():
            report = _load_json(candidate["report"])
            records = [_load_json(path) for path in _record_paths(candidate)]
            evidence_records = [record for record in records if record["kind"] == "evidence"]
            for evidence in evidence_records:
                declaration = evidence["provenance"]["declaration"]
                self.assertEqual(
                    _expected_provenance(candidate, declaration, report),
                    evidence["provenance"],
                )

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_candidate_checker_rejects_each_scope_axis_and_provenance_drift(self) -> None:
        checker = _load_checker()
        documents = checker.load_ordered_map_candidate_records(ROOT)
        reports = checker.load_ordered_map_reports(ROOT)
        for package, candidate in CANDIDATES.items():
            other = CANDIDATES["typescript" if package == "rust" else "rust"]
            evidence_path = next(
                path
                for path, document in documents.items()
                if document.get("id") == f"{candidate['id']}-lookup-empty-conformance"
            )
            claim_path = next(
                path
                for path, document in documents.items()
                if document.get("id") == f"{candidate['id']}-lookup-empty"
            )
            mutations = {
                "cross-realization": lambda d: d["realization"].update(id=other["id"]),
                "adapter": lambda d: d["adapter"].update(id=other["adapter"]),
                "specification-version": lambda d: d["specification"].update(version="0.2.0"),
                "profile": lambda d: d["applicability"]["profiles"][0].update(version="0.2.0"),
                "result": lambda d: d.update(result="inconclusive"),
                "review": lambda d: d.update(reviewState="pending"),
                "declaration": lambda d: d["provenance"].update(declaration="lookup-put-same"),
                "report": lambda d: d["provenance"]["report"].update(sha256="0" * 64),
                "candidate": lambda d: d["provenance"].update(reportCandidate=other["id"]),
                "plan": lambda d: d["provenance"]["plan"].update(canonicalSha256="0" * 64),
                "runner": lambda d: d["provenance"]["runner"].update(sha256="0" * 64),
                "harness": lambda d: d["provenance"]["harness"][0].update(sha256="0" * 64),
                "sources": lambda d: d["provenance"]["sources"][0].update(sha256="0" * 64),
                "commands": lambda d: d["provenance"].update(commandsCanonicalSha256="0" * 64),
                "toolchain": lambda d: d["provenance"].update(toolchainCanonicalSha256="0" * 64),
                "outcome": lambda d: d["provenance"].update(outcomeCanonicalSha256="0" * 64),
                "binary": lambda d: d["provenance"].update(binarySha256="0" * 64),
                "future-review": lambda d: d["provenance"].update(review="O-R6e PASS"),
                "environment": lambda d: d["environment"].update(python="0.0.0"),
                "freshness": lambda d: d["freshness"].update(producedAt="2026-07-19T00:00:00Z"),
            }
            for label, mutate in mutations.items():
                with self.subTest(package=package, axis=label):
                    changed = copy.deepcopy(documents)
                    mutate(changed[evidence_path])
                    errors = checker.candidate_record_errors(changed, reports)
                    self.assertTrue(errors, label)
                    if label in {"result", "review"}:
                        self.assertEqual("active", changed[claim_path]["state"])

            claim_mutations = {
                "claim-declaration": lambda d: d["proposition"].update(
                    declarationId="put-amortized-constant"
                ),
                "claim-profile": lambda d: d["applicableProfiles"][0].update(
                    version="0.2.0"
                ),
                "claim-concern": lambda d: d.update(concern="performance"),
            }
            for label, mutate in claim_mutations.items():
                with self.subTest(package=package, axis=label):
                    changed = copy.deepcopy(documents)
                    mutate(changed[claim_path])
                    self.assertTrue(checker.candidate_record_errors(changed, reports), label)

            with self.subTest(package=package, axis="eighth-performance-claim"):
                changed = copy.deepcopy(documents)
                extra = copy.deepcopy(changed[claim_path])
                extra["id"] = f"{candidate['id']}-put-amortized-constant"
                extra["proposition"]["declarationId"] = "put-amortized-constant"
                extra["concern"] = "performance"
                changed[
                    f"{candidate['recordRoot'].as_posix()}/"
                    f"{candidate['id']}-put-amortized-constant-claim.json"
                ] = extra
                self.assertTrue(checker.candidate_record_errors(changed, reports))

            with self.subTest(package=package, axis="missing-evidence"):
                changed = copy.deepcopy(documents)
                del changed[evidence_path]
                self.assertTrue(checker.candidate_record_errors(changed, reports))

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_claim_lifecycle_and_evidence_result_review_axes_do_not_move_together(self) -> None:
        checker = _load_checker()
        documents = checker.load_ordered_map_candidate_records(ROOT)
        reports = checker.load_ordered_map_reports(ROOT)
        rust_claim = next(
            path
            for path, document in documents.items()
            if document.get("id") == "ordered-map-rust-lookup-empty"
        )
        for field, value in (("state", "retired"),):
            changed = copy.deepcopy(documents)
            changed[rust_claim][field] = value
            errors = checker.candidate_record_errors(changed, reports)
            self.assertTrue(errors)
            evidence = next(
                document
                for document in changed.values()
                if document.get("id") == "ordered-map-rust-lookup-empty-conformance"
            )
            self.assertEqual("supports", evidence["result"])
            self.assertEqual("accepted", evidence["reviewState"])

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_unsupported_performance_and_final_authority_remain_absent(self) -> None:
        documents = _package_json_documents()
        declaration_ids = {
            document["proposition"]["declarationId"]
            for document in documents
            if document["kind"] == "claim"
        }
        self.assertEqual(set(DECLARATIONS), declaration_ids)
        self.assertNotIn("put-amortized-constant", declaration_ids)
        forbidden_keys = {
            "assurance",
            "verified",
            "authority",
            "manifest",
            "productContract",
            "registration",
            "semanticAcceptance",
        }

        def keys(value: object) -> set[str]:
            if isinstance(value, dict):
                return set(value) | set().union(*(keys(item) for item in value.values()))
            if isinstance(value, list):
                return set().union(*(keys(item) for item in value))
            return set()

        self.assertFalse(forbidden_keys & keys(documents))
        package_root = ROOT / "registry/ordered-map/packages"
        self.assertEqual([], list(package_root.rglob("*manifest*.json")))
        self.assertEqual([], list(package_root.rglob("*contract*.json")))

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_reports_are_inputs_not_records_or_membership(self) -> None:
        record_addresses = {
            (document["kind"], document["id"], document["version"])
            for document in _package_json_documents()
        }
        self.assertFalse(any(kind == "ordered-map-campaign-report" for kind, _, _ in record_addresses))
        self.assertFalse(any(path.is_relative_to(ROOT / "registry") for path in [ROOT / candidate["report"] for candidate in CANDIDATES.values()]))
        manifest = _load_json(Path("registry/ordered-map/theory-manifest.json"))
        serialized = json.dumps(manifest, sort_keys=True)
        for candidate in CANDIDATES.values():
            self.assertNotIn(candidate["id"], serialized)
            self.assertNotIn(candidate["report"].as_posix(), serialized)

    @unittest.skipUnless(BOUNDARY_EXISTS, "O6e candidate record boundary is absent")
    def test_repository_gate_runs_the_candidate_checker(self) -> None:
        source = (ROOT / "scripts/check_repo.py").read_text(encoding="utf-8")
        self.assertIn("import ordered_map_evidence_check", source)
        self.assertIn("run_ordered_map_evidence_candidate_checks", source)


if __name__ == "__main__":
    unittest.main()
