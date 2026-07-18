from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from semantic_packages import graph


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry" / "stack"


def _write_json(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def _address(document: dict) -> tuple[str, str, str]:
    return document["kind"], document["id"], document["version"]


class SuccessorEvidenceMigrationPreflightTest(unittest.TestCase):
    def test_old_evidence_repointed_at_successor_claim_is_link_invalid(self) -> None:
        with tempfile.TemporaryDirectory(prefix="j5-migration-") as raw:
            registry = Path(raw) / "registry" / "stack"
            shutil.copytree(REGISTRY, registry)
            manifest_path = registry / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            additions = (
                (
                    "theory/records/stack-spec-0.2.0.json",
                    "theory/records/stack-spec.json",
                    "theory",
                    "theory-authored",
                    lambda document: document.update(version="0.2.0"),
                ),
                (
                    "packages/rust/records/stack-rust-realization-0.2.0.json",
                    "packages/rust/records/stack-rust-realization.json",
                    "rust",
                    "package-authored",
                    lambda document: (
                        document.update(version="0.2.0"),
                        document["specification"].update(version="0.2.0"),
                    ),
                ),
                (
                    "packages/rust/records/stack-rust-pop-empty-claim-0.2.0.json",
                    "packages/rust/records/stack-rust-pop-empty-claim.json",
                    "rust",
                    "package-authored",
                    lambda document: (
                        document.update(version="0.2.0"),
                        document["subject"].update(version="0.2.0"),
                        document["governingSpecification"].update(version="0.2.0"),
                        document["proposition"]["specification"].update(
                            version="0.2.0"
                        ),
                    ),
                ),
            )
            for target, source, source_id, role, mutate in additions:
                document = json.loads((registry / source).read_text(encoding="utf-8"))
                mutate(document)
                path = registry / target
                _write_json(path, document)
                kind, record_id, version = _address(document)
                manifest["members"].append(
                    {
                        "source": source_id,
                        "address": {
                            "kind": kind,
                            "id": record_id,
                            "version": version,
                        },
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "role": role,
                    }
                )

            evidence_path = (
                registry
                / "packages/rust/records/stack-rust-pop-empty-evidence.json"
            )
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["claim"].update(version="0.2.0")
            _write_json(evidence_path, evidence)
            evidence_address = _address(evidence)
            evidence_member = next(
                member
                for member in manifest["members"]
                if (
                    member["address"]["kind"],
                    member["address"]["id"],
                    member["address"]["version"],
                )
                == evidence_address
            )
            evidence_member["sha256"] = hashlib.sha256(
                evidence_path.read_bytes()
            ).hexdigest()
            _write_json(manifest_path, manifest)

            observation = graph.inspect_stack_graph(manifest_path)

        self.assertFalse(observation.ok)
        codes = {diagnostic.code for diagnostic in observation.diagnostics}
        self.assertIn("LINK_EVIDENCE_SPECIFICATION_MISMATCH", codes)
        self.assertIn("LINK_EVIDENCE_REALIZATION_MISMATCH", codes)
        self.assertFalse(any(code.startswith("GRAPH_MEMBERSHIP") for code in codes))


if __name__ == "__main__":
    unittest.main()
