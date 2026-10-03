"""U5 guards: the structural audit is recomputed, and its result is identity.

`docs/v05_mechanistic_integration_plan.md` §17 U5 asks for Δ, the alias classes
that broke, and a rerun of identifiability and design-alias with the matched-unit
caveat on every number. The committed audit must regenerate byte-for-byte, and
its headline -- v0.5.0 is executable-identical to v0.4.0, Δ = 0, no class broken
-- must follow from the recomputation rather than be asserted by it.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting.u5_structural_audit import (
    MATCHED_UNIT_CAVEAT,
    NODE_TSV,
    SCAFFOLD_METADATA_FILES,
    SUMMARY_JSON,
    build_audit,
)

RECORD = ROOT / "docs/v05_u5_structural_audit.md"


class U5AuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload, cls.summary_text, cls.node_text = build_audit(ROOT)

    def test_committed_outputs_regenerate_byte_for_byte(self) -> None:
        self.assertEqual(
            (ROOT / SUMMARY_JSON).read_text(encoding="utf-8"), self.summary_text
        )
        self.assertEqual((ROOT / NODE_TSV).read_text(encoding="utf-8"), self.node_text)

    def test_only_scaffold_metadata_differs_between_the_model_directories(self) -> None:
        identity = self.payload["file_identity"]
        self.assertEqual(identity["unexpected_differences"], [])
        self.assertEqual(identity["present_in_one_only"], [])
        self.assertTrue(set(identity["differing"]) <= SCAFFOLD_METADATA_FILES)
        self.assertTrue(identity["executable_byte_identical"])

    def test_delta_is_zero_and_no_alias_class_broke(self) -> None:
        comparison = self.payload["comparison"]
        self.assertEqual(comparison["delta_distinct_boolean_functions"], 0)
        self.assertEqual(comparison["baseline_distinct_boolean_functions"], 35)
        self.assertEqual(comparison["alias_classes_broken"], [])
        self.assertEqual(comparison["alias_classes_new"], [])
        self.assertTrue(all(comparison["recomputed_blocks_identical"].values()))

    def test_the_audited_numbers(self) -> None:
        structural = self.payload["audited"]["structural"]["summary"]
        self.assertEqual(
            (
                structural["nodes"],
                structural["dependencies"],
                structural["free_variables"],
                structural["distinct_functions"],
                structural["alias_classes"],
                structural["phenotype_inert_nodes"],
                structural["unread_inputs"],
                structural["absorbed_dependencies"],
                structural["never_binding_inhibitions"],
            ),
            (59, 97, 19, 35, 8, 14, 3, 15, 4),
        )
        ceilings = self.payload["audited"]["identifiability"]["ceilings"]
        self.assertEqual(ceilings["design_states_now"], 19)
        self.assertEqual(ceilings["observation_classes_now"], 2)
        self.assertEqual(ceilings["observation_classes_assayable_ceiling"], 8)
        self.assertEqual(ceilings["observation_classes_ceiling"], 32)

    def test_every_design_dependent_block_carries_the_matched_unit_caveat(self) -> None:
        audited = self.payload["audited"]
        self.assertEqual(
            audited["identifiability"]["matched_unit_caveat"], MATCHED_UNIT_CAVEAT
        )
        for variant, block in audited["design_alias"].items():
            self.assertEqual(block["matched_unit_caveat"], MATCHED_UNIT_CAVEAT, variant)
        header = self.node_text.splitlines()[0].split("\t")
        self.assertIn("matched_unit_conditional", header)
        for row in self.payload["measured_node_implications"]:
            self.assertIn("information_status", row["matched_unit_conditional_fields"])

    def test_paep_and_igfbp1_are_one_design_class_under_the_declared_plan(self) -> None:
        # The measured-node implication the record relies on: under the declared
        # four-arm plan the two active readouts cannot be told apart.
        rows = {r["node_id"]: r for r in self.payload["measured_node_implications"]}
        self.assertIn("S_IGFBP1", rows["E_PAEP"]["design_class_as_declared_plan"])

    def test_the_record_quotes_the_computed_numbers(self) -> None:
        text = RECORD.read_text(encoding="utf-8")
        for needle in ("Δ = 0", "35", "19", "8 of 32", "matched-unit"):
            self.assertIn(needle, text)
        self.assertEqual(
            json.loads((ROOT / SUMMARY_JSON).read_text(encoding="utf-8"))[
                "audited_model"
            ],
            "adoc-literature-superset-v0.5.0",
        )


if __name__ == "__main__":
    unittest.main()
