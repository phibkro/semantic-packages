from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import record_check  # noqa: E402
from semantic_packages import graph, publication, theory_projection  # noqa: E402


FIXTURE = ROOT / "fixtures" / "research" / "ordered-map"
RECORDS = FIXTURE / "records"
MANIFEST = FIXTURE / "manifest.json"
SPECIFICATION = ("specification", "ordered-map", "0.1.0")

EXPECTED_DECLARATIONS = {
    ("carrier", "Key"),
    ("carrier", "Value"),
    ("carrier", "OrderedMap"),
    ("operation", "empty"),
    ("operation", "put"),
    ("observation", "lookup"),
    ("observation", "entries"),
    ("equivalence", "key-equivalence"),
    ("equivalence", "value-equivalence"),
    ("equivalence", "ordered-map-equivalence"),
    ("law", "lookup-empty"),
    ("law", "lookup-put-same"),
    ("law", "lookup-put-other"),
    ("law", "put-existing-position"),
    ("law", "put-new-appends"),
    ("effect", "ordered-map-effects"),
    ("resource", "persistence"),
}


class OrderedMapPaperProbeTest(unittest.TestCase):
    def test_record_graph_is_valid_without_domain_specific_schema_changes(self) -> None:
        diagnostics = record_check.validate_graph_paths(
            [str(RECORDS / "spec.json")]
        )
        self.assertEqual([], diagnostics)

    def test_supplied_manifest_and_projection_retain_all_unknowns(self) -> None:
        observation = graph.inspect_stack_graph(MANIFEST)
        self.assertTrue(observation.ok, observation.diagnostics)
        self.assertEqual(
            [SPECIFICATION], [record.address for record in observation.records]
        )

        result = theory_projection.project_theory(
            observation, specification=SPECIFICATION
        )
        self.assertTrue(result.ok, result.diagnostics)
        declarations = {
            (item.kind, item.declaration_id) for item in result.view.declarations
        }
        self.assertEqual(EXPECTED_DECLARATIONS, declarations)
        self.assertEqual(EXPECTED_DECLARATIONS, set(result.view.unknowns))

    def test_stack_publication_authority_is_the_first_observed_blocker(self) -> None:
        observation = publication.inspect_stack_theory(RECORDS)
        self.assertFalse(observation.ok)
        self.assertEqual(1, len(observation.records))
        self.assertEqual(
            Counter(
                {
                    "PUBLICATION_MISSING_ADDRESS": 4,
                    "PUBLICATION_UNEXPECTED_ADDRESS": 1,
                }
            ),
            Counter(item.code for item in observation.diagnostics),
        )


if __name__ == "__main__":
    unittest.main()
