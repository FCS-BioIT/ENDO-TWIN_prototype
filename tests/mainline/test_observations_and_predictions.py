"""Observation mappings, agreement rules and the prediction-freezing workflow."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from endotwin.model import load_model
from endotwin.observations import (
    AgreementCriteria,
    ObservationError,
    classify,
    donor_effect,
    load_observation_map,
)
from endotwin.predictions import (
    FreezeError,
    evaluate,
    freeze,
    load_spec,
    verify,
)

MODEL = load_model()
CRITERIA = AgreementCriteria(
    min_effect_log2=0.5,
    min_evaluable_donors=4,
    min_consistent_donors=4,
    equivalence_margin_log2=0.3,
)

SPEC = textwrap.dedent(
    """
    prediction_id: TEST-Q1-BMPRI
    purpose: WP2_prospective_G1
    model_version: endotwin-v0.1.0
    comparison: Q1_bmpr_inhibition
    primary_readout: RO-PRL
    secondary_readouts: [RO-PSMAD158, RO-KI67]
    rule_variants: {Q1: Q1_bmp_required}
    agreement_criteria:
      min_effect_log2: 0.5
      min_evaluable_donors: 4
      min_consistent_donors: 4
      equivalence_margin_log2: 0.3
    simulation: {sample_count: 200, seed: 1, replicates: 2}
    sensitivity:
      vary_rule_families: [Q2, INF]
      rate_samples: 2
      rate_sample_count: 200
      require_stable: true
    donor_policy:
      development_donors: [D01, D02, D03, D04]
      evaluation_groups: [G1]
    """
)


class ObservationMap(unittest.TestCase):
    obs = load_observation_map(MODEL)

    def test_grant_readouts_map_to_the_right_nodes(self):
        expected = {
            "RO-PRL": "OUT_STROMAL_DECIDUALIZATION",
            "RO-IGFBP1": "OUT_STROMAL_DECIDUALIZATION",
            "RO-PAEP": "OUT_EPITHELIAL_SECRETORY",
            "RO-KI67": "OUT_EPITHELIAL_PROLIFERATION",
            "RO-EDU": "OUT_EPITHELIAL_PROLIFERATION",
            "RO-PSMAD158": "S_BMP_SMAD",
        }
        for readout, node in expected.items():
            self.assertEqual(self.obs[readout]["model_node"], node)

    def test_paep_assay_is_stated_as_its_source_does(self):
        assay = self.obs["RO-PAEP"]["assay"]
        self.assertIn("per manuscript Methods", assay)
        self.assertIn("does not name the assay", assay)

    def test_planned_readouts_are_not_presented_as_data(self):
        for readout in (
            "RO-KI67",
            "RO-EDU",
            "RO-PSMAD158",
            "RO-BULK-DECID",
            "RO-BULK-SECR",
        ):
            self.assertEqual(self.obs[readout]["mapping_status"], "planned")
            self.assertRegex(
                self.obs[readout]["data_status"], "planned|not yet measured"
            )

    def test_deconvolution_readouts_are_relative_contributions(self):
        for readout in ("RO-BULK-DECID", "RO-BULK-SECR"):
            self.assertIn(
                "relative contribution", self.obs[readout]["measured_quantity"]
            )


class AgreementRules(unittest.TestCase):
    def test_direction_predictions(self):
        self.assertEqual(
            classify("down", [-1.0, -0.8, -0.7, -1.2, 0.1], CRITERIA)[0], "concordant"
        )
        self.assertEqual(
            classify("down", [1.0, 0.8, 0.7, 1.2, 0.0], CRITERIA)[0], "discordant"
        )
        self.assertEqual(
            classify("down", [-1.0, 0.8, -0.1, 0.2, 0.0], CRITERIA)[0], "inconclusive"
        )

    def test_no_change_needs_equivalence_not_just_non_significance(self):
        self.assertEqual(
            classify("no_change", [0.1, -0.2, 0.05, 0.0], CRITERIA)[0], "concordant"
        )
        # Noisy data without a consistent change are inconclusive, never concordant.
        self.assertEqual(
            classify("no_change", [0.4, -0.45, 0.6, -0.1], CRITERIA)[0], "inconclusive"
        )

    def test_too_few_evaluable_donors_is_inconclusive(self):
        self.assertEqual(classify("up", [1.0, 1.0, 1.0], CRITERIA)[0], "inconclusive")

    def test_non_positive_values_are_refused(self):
        with self.assertRaises(ObservationError):
            donor_effect(0.0, 1.0)


class FreezingWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="endotwin_freeze_test_"))
        cls.spec = cls.tmp / "spec.yaml"
        cls.spec.write_text(SPEC)
        cls.record = freeze(
            cls.spec, out_root=cls.tmp / "frozen", allow_dirty=True, model=MODEL
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _copy(self, name):
        target = self.tmp / name
        shutil.copytree(self.record, target)
        return target

    def test_record_holds_predictions_snapshot_and_manifest(self):
        payload = json.loads((self.record / "predictions.json").read_text())
        self.assertEqual(payload["predictions"]["RO-PRL"]["direction"], "down")
        self.assertEqual(payload["predictions"]["RO-PSMAD158"]["direction"], "down")
        self.assertEqual(payload["predictions"]["RO-KI67"]["direction"], "no_change")
        self.assertTrue(payload["sensitivity"]["eligible"])
        self.assertTrue((self.record / "model" / "network.bnd").is_file())
        self.assertTrue(verify(self.record)["intact"])

    def test_frozen_records_are_never_overwritten(self):
        with self.assertRaises(FreezeError):
            freeze(
                self.spec, out_root=self.tmp / "frozen", allow_dirty=True, model=MODEL
            )

    def test_tampering_is_detected_and_blocks_evaluation(self):
        copy = self._copy("tampered")
        (copy / "model" / "network.bnd").write_text("Node X { logic = X; }\n")
        self.assertFalse(verify(copy)["intact"])
        obs = self.tmp / "obs_tampered.tsv"
        obs.write_text(
            "donor_id\tgroup\treadout_id\tperturbed_value\tcontrol_value\tevaluable\n"
        )
        with self.assertRaises(FreezeError):
            evaluate(copy, obs)

    def test_evaluation_uses_frozen_criteria_and_is_written_once(self):
        copy = self._copy("evaluated")
        obs = self.tmp / "obs_ok.tsv"
        lines = [
            "donor_id\tgroup\treadout_id\tperturbed_value\tcontrol_value\tevaluable"
        ]
        for donor, ratio in zip(
            ("E01", "E02", "E03", "E04", "E05"), (0.3, 0.4, 0.2, 0.35, 0.5), strict=True
        ):
            lines.append(f"{donor}\tG1\tRO-PRL\t{100 * ratio}\t100\ttrue")
        obs.write_text("\n".join(lines) + "\n")
        out = evaluate(copy, obs)
        result = json.loads(out.read_text())
        self.assertEqual(result["results"]["RO-PRL"]["verdict"], "concordant")
        self.assertEqual(result["results"]["RO-PSMAD158"]["verdict"], "inconclusive")
        self.assertTrue(verify(copy)["intact"])  # evaluation does not modify the record
        with self.assertRaises(FreezeError):
            evaluate(copy, obs)

    def test_development_donors_cannot_be_used_for_evaluation(self):
        copy = self._copy("leaky")
        obs = self.tmp / "obs_leak.tsv"
        obs.write_text(
            "donor_id\tgroup\treadout_id\tperturbed_value\tcontrol_value\tevaluable\n"
            "D01\tG1\tRO-PRL\t10\t100\ttrue\n"
        )
        with self.assertRaises(FreezeError):
            evaluate(copy, obs)

    def test_g3_data_cannot_select_the_wp4_intervention(self):
        bad = self.tmp / "wp4_bad.yaml"
        bad.write_text(
            SPEC.replace("WP2_prospective_G1", "WP4_selection_G2")
            + "selection_dataset_groups: [G2, G3]\n"
        )
        with self.assertRaises(FreezeError):
            load_spec(bad)
        missing = self.tmp / "wp4_g3.yaml"
        missing.write_text(SPEC.replace("WP2_prospective_G1", "WP4_evaluation_G3"))
        with self.assertRaises(FreezeError):
            load_spec(missing)

    def test_unstable_primary_predictions_are_not_eligible(self):
        spec = self.tmp / "unstable.yaml"
        spec.write_text(
            SPEC.replace("TEST-Q1-BMPRI", "TEST-UNSTABLE").replace(
                "vary_rule_families: [Q2, INF]", "vary_rule_families: [Q1, Q2, INF]"
            )
        )
        with self.assertRaises(FreezeError):
            freeze(spec, out_root=self.tmp / "frozen", allow_dirty=True, model=MODEL)


class Template(unittest.TestCase):
    def test_committed_template_is_a_valid_spec(self):
        spec = load_spec(
            ROOT / "endotwin/predictions/templates/wp2_prediction_spec.template.yaml"
        )
        self.assertEqual(spec["purpose"], "WP2_prospective_G1")


if __name__ == "__main__":
    unittest.main()
