"""The calibration-candidate report is derived, and its derivations are right.

The report's value is that structural claims come from the model rather than
from a curator, so these tests check the derivations themselves -- not the
prose, which is an output.
"""

from __future__ import annotations

import csv
import unittest

from dt_adoc.experiments.calibration_candidates import (
    CURATED,
    OUT_MD,
    OUT_TSV,
    Sources,
    build,
    derive,
    diagnostics,
    uncovered_couplings,
)
from dt_adoc.reporting.identifiability import repo_root
from tests.unit.checkout_isolation import regenerate_in_shadow

ROOT = repo_root()


def _curated() -> list[dict[str, str]]:
    with (ROOT / CURATED).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


class SourcesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = Sources.load(ROOT)

    def test_zero_degree_detection_finds_the_known_unread_inputs(self) -> None:
        """Derived, not curated: these inputs are declared and read by no rule."""
        for node in ("IN_XAV939", "IN_HCG", "IN_EMBRYO_CONDITIONED_SIGNAL"):
            self.assertTrue(
                self.sources.is_zero_degree(node), f"{node} should be zero-degree"
            )

    def test_a_read_input_is_not_zero_degree(self) -> None:
        for node in ("IN_E2", "IN_PROGESTIN", "IN_MIFEPRISTONE", "IN_ANTI_SPP1"):
            self.assertFalse(self.sources.is_zero_degree(node), node)

    def test_downstream_propagation_reaches_the_endpoint_from_a_hormone_input(
        self,
    ) -> None:
        reach = self.sources.downstream("IN_PROGESTIN")
        self.assertIn("OUT_STABLE_ADHESION", reach)
        self.assertIn("S_DECIDUALIZED", reach)

    def test_downstream_of_a_zero_degree_input_is_empty(self) -> None:
        self.assertEqual(self.sources.downstream("IN_XAV939"), set())

    def test_alias_classes_were_loaded(self) -> None:
        self.assertGreater(len(self.sources.alias_class), 10)
        self.assertIn("E_LIF", self.sources.alias_class)


class DerivationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = Sources.load(ROOT)
        cls.rows = {r["candidate_id"]: r for r in _curated()}

    def _derive(self, candidate_id: str) -> dict:
        return derive(self.sources, self.rows[candidate_id])

    def test_a_missing_node_is_reported_rather_than_silently_dropped(self) -> None:
        """The check that catches a candidate naming a node the model lost."""
        row = dict(self.rows["CAND-02"])
        row["interrogates_nodes"] = "E_LIF;S_STAT3"
        derived = derive(self.sources, row)
        self.assertEqual(derived["nodes_missing"], ["S_STAT3"])
        self.assertIn("E_LIF", derived["nodes_present"])

    def test_the_lif_candidate_reports_the_artificial_coupling(self) -> None:
        derived = self._derive("CAND-02")
        self.assertEqual(derived["couplings"]["E_LIF"], "ARTIFICIALLY_COUPLED")
        self.assertEqual(derived["couplings"]["E_GP130_STAT3"], "ARTIFICIALLY_COUPLED")
        self.assertIn("E_CD98_CD9", derived["aliases"]["E_LIF"])

    def test_the_hcg_candidate_is_flagged_zero_degree(self) -> None:
        derived = self._derive("CAND-10")
        self.assertIn("IN_HCG", derived["zero_degree_nodes"])

    def test_the_xav939_candidate_has_no_model_image(self) -> None:
        """Its only node is zero-degree, so the model predicts nothing."""
        derived = self._derive("CAND-12")
        self.assertIn("IN_XAV939", derived["zero_degree_nodes"])

    def test_anti_spp1_reaches_a_maternal_node_but_cannot_move_it(self) -> None:
        """Structural reach is not experimental information.

        `X_SPP1_LUMEN_FREE` is one disjunct of eight in `E_RECEPTIVE_SURFACE`,
        and the other seven are saturated under hormone treatment, so the
        topological path exists and carries nothing. Asserting reach alone
        would overstate this experiment's maternal value, which is the exact
        error the report is built to avoid.
        """
        derived = self._derive("CAND-11")
        self.assertEqual(derived["maternal_nodes_reached"], 1)
        self.assertIn("OUT_STABLE_ADHESION", derived["terminal_nodes_reached"])
        self.assertFalse(derived["moves_maternal_in_a_recorded_arm"])

    def test_a_hormone_input_does_move_maternal_nodes(self) -> None:
        """The contrast that makes the previous assertion meaningful."""
        derived = self._derive("CAND-05")
        self.assertTrue(derived["moves_maternal_in_a_recorded_arm"])

    def test_the_camp_candidate_reaches_the_maternal_network(self) -> None:
        derived = self._derive("CAND-05")
        self.assertGreater(derived["maternal_nodes_reached"], 5)
        self.assertTrue(derived["scope"].startswith("maternal"))

    def test_evidence_species_is_derived_from_the_reference_table(self) -> None:
        self.assertEqual(self._derive("CAND-05")["evidence_level"], "direct_human")
        self.assertEqual(self._derive("CAND-04")["evidence_level"], "transferred_only")

    def test_an_unknown_reference_is_caught(self) -> None:
        row = dict(self.rows["CAND-05"])
        row["ref_ids"] = "REF-99999"
        derived = derive(self.sources, row)
        self.assertIn("NOT IN references.tsv", derived["reference_details"][0])

    def test_analyte_names_match_across_punctuation(self) -> None:
        """IGFBP1 must match the observation map's IGFBP-1."""
        derived = self._derive("CAND-05")
        self.assertEqual(derived["readout_status"]["IGFBP1"], "in_observation_map")
        self.assertEqual(derived["readout_status"]["PRL"], "in_observation_map")

    def test_an_unmeasurable_readout_is_named(self) -> None:
        derived = self._derive("CAND-01")
        self.assertEqual(
            derived["readout_status"]["surface CD98/CD9"],
            "NOT_IN_OBSERVATION_LAYER",
        )


class DiagnosticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = Sources.load(ROOT)
        cls.pairs = [(r, derive(cls.sources, r)) for r in _curated()]

    def test_diagnostics_report_the_zero_degree_candidates(self) -> None:
        text = "\n".join(diagnostics(self.pairs))
        self.assertIn("CAND-10", text)
        self.assertIn("CAND-12", text)
        self.assertIn("zero-degree", text)

    def test_uncovered_couplings_are_reported(self) -> None:
        """Check 6: coupled nodes with no discriminating experiment."""
        uncovered = uncovered_couplings(self.sources, self.pairs)
        self.assertIsInstance(uncovered, list)
        for node in uncovered:
            self.assertEqual(
                self.sources.coupling[node]["adjudication"], "ARTIFICIALLY_COUPLED"
            )

    def test_every_active_candidate_names_at_least_one_readout_or_is_a_gap(
        self,
    ) -> None:
        for row, _ in self.pairs:
            if row["status"] == "active":
                self.assertTrue(
                    row["proximal_readouts"].strip(),
                    f"{row['candidate_id']} is active with no proximal readout",
                )


class GeneratedOutputIsCurrentTest(unittest.TestCase):
    """The committed Markdown must be what the generator produces now."""

    def test_regenerating_reproduces_the_committed_files(self) -> None:
        # Nothing here is volatile: the report carries no generation date, and
        # `test_generated_date_determinism` pins that across wall-clock dates.
        produced = regenerate_in_shadow(build, (OUT_MD, OUT_TSV))
        for relative, content in produced.items():
            self.assertEqual((ROOT / relative).read_bytes(), content, str(relative))

    def test_the_markdown_says_it_is_generated(self) -> None:
        text = (ROOT / OUT_MD).read_text(encoding="utf-8")
        self.assertIn("Generated file — do not edit", text)
        self.assertIn("build-calibration-candidates", text)

    def test_no_single_overall_score_column_exists(self) -> None:
        """The axes stay separate; a combined score was explicitly refused."""
        with (ROOT / OUT_TSV).open(encoding="utf-8") as fh:
            header = next(csv.reader(fh, delimiter="\t"))
        self.assertIn("curator_maternal_value", header)
        self.assertIn("curator_interface_value", header)
        for name in header:
            self.assertNotIn("overall", name.lower())
            self.assertNotIn("total_score", name.lower())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
