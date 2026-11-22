"""Planned experimental data interfaces (synthetic rows only; no ENDO-TWIN data exist)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from endotwin.data_interfaces import validate
from endotwin.model import load_model
from endotwin.observations import load_observation_map

READOUTS = load_observation_map(load_model())


def sample(**overrides):
    row = {
        "library_id": "L1",
        "chip_id": "C1",
        "donor_id": "D01",
        "group": "G1",
        "work_package": "WP1",
        "compartment": "stromal",
        "condition_id": "reference",
        "collection_phase": "differentiation_supplemented",
        "analysis_role": "development",
        "sequencing_batch": "B1",
        "qc_pass": "true",
    }
    row.update(overrides)
    return row


def measurement(**overrides):
    row = {
        "measurement_id": "M1",
        "donor_id": "D01",
        "chip_id": "C1",
        "group": "G1",
        "readout_id": "RO-PRL",
        "outlet_or_site": "basal_outlet",
        "condition_id": "reference",
        "collection_time_h": "96",
        "value": "120.5",
        "unit": "pg/mL",
        "measurement_state": "observed",
        "lod": "10",
        "analysis_role": "development",
    }
    row.update(overrides)
    return row


class SampleSheets(unittest.TestCase):
    def test_valid_sheet_passes(self):
        report = validate(
            "bulk_rnaseq_samples",
            [sample(), sample(library_id="L2", compartment="epithelial")],
        )
        self.assertTrue(report.ok, report.errors)

    def test_identifiers_must_be_pseudonymised_codes(self):
        report = validate("bulk_rnaseq_samples", [sample(donor_id="Donor One")])
        self.assertFalse(report.ok)

    def test_wp2_donors_never_appear_in_development(self):
        rows = [sample(), sample(library_id="L2", analysis_role="wp2_evaluation")]
        self.assertTrue(
            any("WP2" in e for e in validate("bulk_rnaseq_samples", rows).errors)
        )

    def test_g3_data_never_select_the_intervention(self):
        rows = [sample(group="G3", analysis_role="wp4_selection")]
        self.assertTrue(
            any("G3" in e for e in validate("bulk_rnaseq_samples", rows).errors)
        )

    def test_duplicate_libraries_are_refused(self):
        self.assertFalse(validate("bulk_rnaseq_samples", [sample(), sample()]).ok)


class Measurements(unittest.TestCase):
    def test_valid_measurement_passes(self):
        self.assertTrue(
            validate("functional_measurements", [measurement()], READOUTS).ok
        )

    def test_states_stay_distinct_from_values(self):
        cases = [
            measurement(value=""),
            measurement(measurement_state="missing"),
            measurement(measurement_state="below_lod", lod=""),
            measurement(value="4.2"),  # observed but below the lod
        ]
        for row in cases:
            self.assertFalse(
                validate("functional_measurements", [row], READOUTS).ok, row
            )
        self.assertTrue(
            validate(
                "functional_measurements",
                [measurement(measurement_state="below_lod", value="")],
                READOUTS,
            ).ok
        )

    def test_readout_must_be_mapped(self):
        self.assertFalse(
            validate(
                "functional_measurements", [measurement(readout_id="RO-XYZ")], READOUTS
            ).ok
        )


class Deconvolution(unittest.TestCase):
    def row(self, **overrides):
        row = {
            "library_id": "L1",
            "reference_id": "E-MTAB-15842-v1",
            "reference_state": "HT stroma",
            "estimate": "0.6",
            "estimate_type": "relative_state_contribution",
            "method": "CIBERSORTx",
            "fit_p_value": "",
        }
        row.update(overrides)
        return row

    def test_relative_contributions_pass(self):
        rows = [self.row(), self.row(reference_state="Stroma", estimate="0.3")]
        self.assertTrue(validate("deconvolution_estimates", rows).ok)

    def test_absolute_fractions_are_refused(self):
        self.assertFalse(
            validate(
                "deconvolution_estimates",
                [self.row(estimate_type="absolute_cell_fraction")],
            ).ok
        )

    def test_contributions_cannot_exceed_one(self):
        rows = [self.row(), self.row(reference_state="Stroma", estimate="0.6")]
        self.assertFalse(validate("deconvolution_estimates", rows).ok)


if __name__ == "__main__":
    unittest.main()
