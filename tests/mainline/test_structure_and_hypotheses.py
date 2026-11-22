"""Exact structure and the predictions that separate competing hypotheses."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from dt_adoc.model.topology import parse_bnd_rules
from endotwin.analysis import (
    comparison_directions,
    discrimination_table,
    exact_predictions,
)
from endotwin.model import load_model, scenario_label
from endotwin.protocols import load_protocols
from endotwin.structure import (
    _input_columns,
    columns,
    fixed_point,
    summarize,
)

MODEL = load_model()
PROTOCOLS = load_protocols(MODEL)
RESULTS = ROOT / "endotwin/results/endotwin-v0.1.0"
HT = {"IN_E2": 1, "IN_PROGESTIN": 1, "IN_cAMP": 1, "IN_XAV939": 1}


def _fp(variants=(), inputs=None, forced=None):
    rules = MODEL.rules_for(MODEL.selection_from_ids(list(variants)))
    return fixed_point(rules, inputs or HT, forced)


class ExactEnumeration(unittest.TestCase):
    def test_closed_form_columns_equal_the_definition(self):
        for k in range(1, 8):
            count = 1 << k
            for i, col in enumerate(_input_columns(k)):
                self.assertEqual(col, sum(1 << j for j in range(count) if (j >> i) & 1))

    def test_reproduces_the_recorded_v060_structure(self):
        # An independent implementation must agree with the prototype record.
        rules = parse_bnd_rules(
            ROOT / "models/superset/adoc-literature-superset-v0.6.0/network.bnd"
        )
        summary = summarize(rules, tuple(n for n in rules if n.startswith("OUT_")))
        recorded = json.loads(
            (ROOT / "docs/intervention_layer_stage3/structure_counts.json").read_text()
        )
        v060 = recorded["versions"]["adoc-literature-superset-v0.6.0"]
        self.assertEqual(summary.nodes, v060["nodes"])
        self.assertEqual(summary.dependencies, v060["dependencies"])
        self.assertEqual(
            summary.distinct_functions, v060["distinct_composed_functions"]
        )
        self.assertEqual(len(summary.alias_classes), v060["alias_class_count"])
        self.assertEqual(len(summary.phenotype_inert_nodes), 17)
        self.assertEqual(len(summary.absorbed_dependencies), 15)
        self.assertEqual(len(summary.never_binding_inhibitions), 5)


class MainlineStructure(unittest.TestCase):
    summary = summarize(MODEL.rules, MODEL.outputs, MODEL.readout_nodes)

    def test_receptor_inhibition_separates_smad_activity_from_the_progesterone_class(
        self,
    ):
        progesterone_class = next(
            c for c in self.summary.alias_classes if "IN_PROGESTIN" in c
        )
        self.assertIn("S_BMP2", progesterone_class)
        self.assertNotIn("S_BMP_SMAD", progesterone_class)
        cols = columns(MODEL.rules)
        self.assertNotEqual(cols.values["S_BMP2"], cols.values["S_BMP_SMAD"])

    def test_xav939_is_declared_but_read_by_no_rule(self):
        self.assertEqual(self.summary.unread_inputs, ("IN_XAV939",))
        self.assertEqual(self.summary.readout_inert_nodes, ("IN_XAV939",))

    def test_committed_structure_is_current(self):
        committed = json.loads((RESULTS / "structure.json").read_text())
        self.assertEqual(committed["default"], self.summary.as_dict())


class Q1BmpHypotheses(unittest.TestCase):
    def test_bmp_required_predicts_loss_of_decidualisation_under_inhibition(self):
        ctrl = _fp(["Q1_bmp_required"])
        pert = _fp(["Q1_bmp_required"], {**HT, "IN_BMPR_INHIBITOR": 1})
        self.assertEqual(
            (ctrl["OUT_STROMAL_DECIDUALIZATION"], pert["OUT_STROMAL_DECIDUALIZATION"]),
            (1, 0),
        )

    def test_pgr_sufficient_predicts_maintained_decidualisation(self):
        pert = _fp(["Q1_pgr_sufficient"], {**HT, "IN_BMPR_INHIBITOR": 1})
        self.assertEqual(pert["OUT_STROMAL_DECIDUALIZATION"], 1)

    def test_target_engagement_is_the_same_under_both_hypotheses(self):
        for variant in ("Q1_bmp_required", "Q1_pgr_sufficient"):
            pert = _fp([variant], {**HT, "IN_BMPR_INHIBITOR": 1})
            self.assertEqual((pert["S_BMP2"], pert["S_BMP_SMAD"]), (1, 0), variant)
            self.assertEqual(pert["OUT_EPITHELIAL_PROLIFERATION"], 0, variant)

    def test_cyclic_amp_is_required_in_both(self):
        hormone_only = {"IN_E2": 1, "IN_PROGESTIN": 1}
        for variant in ("Q1_bmp_required", "Q1_pgr_sufficient"):
            self.assertEqual(
                _fp([variant], hormone_only)["OUT_STROMAL_DECIDUALIZATION"], 0
            )


class Q2ParacrineHypotheses(unittest.TestCase):
    knockdown: ClassVar[dict[str, int]] = {"S_HAND2": 0}
    block: ClassVar[dict[str, int]] = {"S_PARACRINE_MITOGEN": 0}
    e2_only: ClassVar[dict[str, int]] = {"IN_E2": 1}

    def test_hand2_knockdown_separates_stromal_from_autonomous(self):
        self.assertEqual(
            _fp(["Q2_stromal_relay"], forced=self.knockdown)[
                "OUT_EPITHELIAL_PROLIFERATION"
            ],
            1,
        )
        self.assertEqual(
            _fp(["Q2_epithelial_autonomous"], forced=self.knockdown)[
                "OUT_EPITHELIAL_PROLIFERATION"
            ],
            0,
        )

    def test_paracrine_block_discriminates_only_during_e2_priming(self):
        self.assertEqual(
            _fp(["Q2_stromal_relay"], self.e2_only, self.block)[
                "OUT_EPITHELIAL_PROLIFERATION"
            ],
            0,
        )
        self.assertEqual(
            _fp(["Q2_epithelial_autonomous"], self.e2_only, self.block)[
                "OUT_EPITHELIAL_PROLIFERATION"
            ],
            1,
        )
        for variant in ("Q2_stromal_relay", "Q2_epithelial_autonomous"):
            self.assertEqual(
                _fp([variant], HT, self.block)["OUT_EPITHELIAL_PROLIFERATION"], 0
            )

    def test_relay_and_relay_plus_direct_compute_the_same_function(self):
        a = columns(MODEL.rules_for(MODEL.selection_from_ids(["Q2_stromal_relay"])))
        b = columns(
            MODEL.rules_for(MODEL.selection_from_ids(["Q2_relay_plus_direct_v051"]))
        )
        self.assertEqual(a.values, b.values)


class InflammationHypotheses(unittest.TestCase):
    il1b: ClassVar[dict[str, int]] = {**HT, "IN_IL1B": 1}

    def test_il1b_impairs_decidualisation_in_every_scenario(self):
        for selection in MODEL.scenarios():
            state = fixed_point(MODEL.rules_for(selection), self.il1b)
            self.assertEqual(
                state["OUT_STROMAL_DECIDUALIZATION"], 0, scenario_label(selection)
            )

    def test_psmad_separates_the_two_routes(self):
        self.assertEqual(_fp(["INF_decidual_only"], self.il1b)["S_BMP_SMAD"], 1)
        self.assertEqual(_fp(["INF_pgr_depletion"], self.il1b)["S_BMP_SMAD"], 0)

    def test_il1b_inputs_are_inert_without_exposure(self):
        for selection in MODEL.scenarios():
            rules = MODEL.rules_for(selection)
            self.assertEqual(
                fixed_point(rules, HT)["OUT_STROMAL_DECIDUALIZATION"],
                fixed_point(
                    MODEL.rules_for({**selection, "INF": "INF_decidual_only"}), HT
                )["OUT_STROMAL_DECIDUALIZATION"],
            )


class CommittedPredictionTables(unittest.TestCase):
    def _read(self, name):
        with (RESULTS / name).open(newline="") as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    def test_committed_tables_regenerate(self):
        rows = exact_predictions(MODEL, PROTOCOLS)
        directions = comparison_directions(MODEL, PROTOCOLS, rows)
        table = discrimination_table(MODEL, PROTOCOLS, directions)
        self.assertEqual(
            self._read("fixed_point_predictions.tsv"),
            [{k: str(v) for k, v in r.items()} for r in rows],
        )
        self.assertEqual(
            self._read("discrimination.tsv"),
            [{k: str(v) for k, v in r.items()} for r in table],
        )

    def test_every_variant_family_has_a_robust_discriminating_comparison(self):
        table = self._read("discrimination.tsv")
        for family in MODEL.families():
            robust = [
                r
                for r in table
                if r["family"] == family and r["discrimination"] == "robust"
            ]
            self.assertTrue(robust, family)


if __name__ == "__main__":
    unittest.main()
