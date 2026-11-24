"""The verification report says what it must, and derives what it can.

The report's whole purpose is to keep an external reader from mistaking a
verified implementation for a validated biology. These tests pin the statements
that do that work, so they cannot be dropped in an edit, and check that the
funded-versus-candidate split is computed from the node dictionary rather than
hard-coded.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from endotwin.model import load_model
from endotwin.verification import (
    _candidate_only_comparisons,
    _unfunded_inputs,
    build_report,
)

MODEL = load_model()
REPORT_PATH = ROOT / "endotwin/results" / MODEL.version / "verification_report.md"


class ReportContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = build_report(MODEL.version)

    def test_it_names_the_model_version(self) -> None:
        self.assertIn(MODEL.version, self.text)

    def test_it_refuses_the_validation_claim(self) -> None:
        """The single most important sentence in the document."""
        self.assertIn(
            "Computational verification is not biological validation", self.text
        )
        self.assertIn("has **not** been calibrated", self.text)

    def test_it_separates_scenarios_from_replicates(self) -> None:
        self.assertIn("model scenarios, not biological replicates", self.text)
        self.assertIn("must never", self.text)

    def test_it_bounds_the_robustness_claim(self) -> None:
        """Robustness is reported only inside the range that was sampled."""
        self.assertIn("rate sets that were sampled, within the stated range", self.text)
        self.assertIn("Scope: one scenario", self.text)

    def test_it_records_the_unread_input(self) -> None:
        self.assertIn("IN_XAV939", self.text)
        self.assertIn("silence is not a prediction", self.text)

    def test_the_committed_report_is_current(self) -> None:
        self.assertTrue(REPORT_PATH.is_file(), REPORT_PATH)
        self.assertEqual(
            REPORT_PATH.read_text(encoding="utf-8"),
            self.text,
            "the committed verification report is stale; run "
            "`pixi run endotwin-verification-report`",
        )


class FundedSplitIsDerived(unittest.TestCase):
    def test_unfunded_inputs_come_from_the_node_dictionary(self) -> None:
        """Not a hard-coded list: the marker lives with the node description."""
        unfunded = _unfunded_inputs(MODEL)
        self.assertIn("IN_SMO_INHIBITOR", unfunded)
        self.assertIn("IN_FOXO1_INHIBITOR", unfunded)
        # The BMP receptor inhibitor IS funded (WP1 Task 1.4) and must not be
        # swept in by a loose match.
        self.assertNotIn("IN_BMPR_INHIBITOR", unfunded)

    def test_candidate_comparisons_are_identified(self) -> None:
        candidate = _candidate_only_comparisons(MODEL)
        self.assertIn("FOX_foxo1_inhibition", candidate)
        self.assertIn("HH_smo_inhibition_hormone_only", candidate)
        self.assertNotIn("Q1_bmpr_inhibition", candidate)

    def test_the_report_marks_a_family_the_plan_cannot_decide(self) -> None:
        """FOX is separated only by a perturbation outside the funded protocol.

        If this ever becomes "no family", either the plan gained an arm or the
        marker was lost; both deserve a look rather than a silent pass.
        """
        self.assertIn("not in the funded protocol", build_report(MODEL.version))


if __name__ == "__main__":
    unittest.main()
