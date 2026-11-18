"""Structural facts behind `docs/prl_igfbp1_temporal_axis.md`.

The document's conclusion is negative -- no rule or rate variant is adopted --
so these tests pin the facts that make it negative. Each fails if the situation
it records changes, at which point the document must be revised rather than the
test loosened. The judgements in its sections 5 and 6 are arguments from these
facts and are deliberately not asserted here.
"""

from __future__ import annotations

import csv
import unittest
from collections import defaultdict

from dt_adoc.reporting.identifiability import (
    parse_bnd_rules,
    repo_root,
    resolve_model,
)

MODEL = "adoc-literature-superset-v0.4.0"
ROOT = repo_root()
#: Detection limits, from SOFIA-STR-001 via the observation map notes.
LOD = {"IGFBP-1": 5.0, "PRL": 10.0}


class ExchangeableByConstructionTest(unittest.TestCase):
    """Identical rule, identical istate, no declared rate."""

    @classmethod
    def setUpClass(cls) -> None:
        spec = resolve_model(MODEL, ROOT)
        cls.rules = parse_bnd_rules(spec.network_bnd)
        cls.baseline = spec.baseline_cfg.read_text(encoding="utf-8")
        cls.model_dir = spec.network_bnd.parent

    def test_the_two_nodes_share_one_boolean_function(self) -> None:
        self.assertEqual(self.rules["S_PRL"].strip(), self.rules["S_IGFBP1"].strip())
        self.assertEqual(self.rules["S_PRL"].strip(), "S_DECIDUALIZED")

    def test_both_start_from_the_same_initial_state(self) -> None:
        self.assertIn("S_PRL.istate = FALSE;", self.baseline)
        self.assertIn("S_IGFBP1.istate = FALSE;", self.baseline)

    def test_no_transition_rate_is_declared_anywhere(self) -> None:
        """A rate is the only remaining way the two could differ."""
        texts = [self.baseline]
        conditions = self.model_dir / "conditions"
        texts.extend(p.read_text(encoding="utf-8") for p in conditions.glob("*.cfg"))
        for text in texts:
            self.assertNotIn("rate_up", text)
            self.assertNotIn("rate_down", text)


class Day3IsTheSameConditionAsDay6Test(unittest.TestCase):
    """So no arm can express the difference; it is purely a horizon."""

    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / "config/adoc_outlet_conditions.tsv"
        with path.open(encoding="utf-8") as fh:
            cls.rows = {
                r["condition_id"]: r for r in csv.DictReader(fh, delimiter="\t")
            }

    def test_the_agents_and_concentrations_are_identical(self) -> None:
        day3 = self.rows["COND-DAY3-SAMPLE"]
        day6 = self.rows["COND-DAY6-SAMPLE"]
        self.assertEqual(day3["agents"], day6["agents"])
        self.assertEqual(day3["agent_concentrations"], day6["agent_concentrations"])
        self.assertEqual(day3["condition_normalized"], day6["condition_normalized"])

    def test_only_elapsed_time_differs(self) -> None:
        self.assertNotEqual(
            self.rows["COND-DAY3-SAMPLE"]["hours_after_cocktail_start"],
            self.rows["COND-DAY6-SAMPLE"]["hours_after_cocktail_start"],
        )

    def test_no_day3_protocol_arm_was_created(self) -> None:
        """The document says one is deliberately not created."""
        conditions = ROOT / "models/superset" / MODEL / "conditions"
        self.assertEqual([p for p in conditions.glob("*day3*")], [])
        self.assertEqual([p for p in conditions.glob("*day_3*")], [])


class TheOrderingIsConfoundedTest(unittest.TestCase):
    """Magnitude and detection limit, on the like-for-like stromal outlet."""

    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / "input_tables/adoc_secreted_proteins.tsv"
        with path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        cls.by = defaultdict(list)
        for row in rows:
            if row["protein"] in LOD and row["outlet"] == "bottom":
                raw = row["reported_concentration_pg_ml"]
                cls.by[(row["protein"], row["resolved_protocol_day"])].append(
                    float(raw) if raw else 0.0
                )

    def _detected(self, protein: str, day: str) -> list[float]:
        return [v for v in self.by[(protein, day)] if v > LOD[protein]]

    def test_igfbp1_is_detected_before_any_hormone(self) -> None:
        """Section 4: constitutive, not merely earlier."""
        detected = self._detected("IGFBP-1", "0")
        self.assertEqual(len(detected), 4)
        self.assertEqual(len(self.by[("IGFBP-1", "0")]), 5)
        self.assertEqual(self._detected("PRL", "0"), [])

    def test_the_magnitude_gap_is_large_at_both_treated_timepoints(self) -> None:
        for day, minimum in (("3", 20.0), ("6", 5.0)):
            igf = sorted(self._detected("IGFBP-1", day))
            prl = sorted(self._detected("PRL", day))
            self.assertTrue(igf and prl, day)
            ratio = igf[len(igf) // 2] / prl[len(prl) // 2]
            self.assertGreater(ratio, minimum, f"day {day} magnitude ratio")

    def test_the_detection_limits_also_favour_igfbp1(self) -> None:
        self.assertLess(LOD["IGFBP-1"], LOD["PRL"])

    def test_igfbp1_detection_is_non_monotonic(self) -> None:
        """5/5 at day 3 falling to 3/5 at day 6 weakens any ordering argument."""
        self.assertEqual(len(self._detected("IGFBP-1", "3")), 5)
        self.assertEqual(len(self._detected("IGFBP-1", "6")), 3)


class NoThresholdIsPreRegisteredTest(unittest.TestCase):
    """Section 5: the actual blocker, and the rule that governs it."""

    def test_the_repository_records_the_no_self_chosen_threshold_rule(self) -> None:
        path = ROOT / "config/observation_model_map.tsv"
        text = path.read_text(encoding="utf-8")
        self.assertIn(
            "must never be chosen from these same observations while they also "
            "serve as the feasibility gate",
            text,
        )

    def test_the_igfbp1_row_is_still_an_active_diagnostic(self) -> None:
        """Which is why choosing a threshold from it would be leakage."""
        path = ROOT / "config/observation_model_map.tsv"
        with path.open(encoding="utf-8") as fh:
            rows = {r["mapping_id"]: r for r in csv.DictReader(fh, delimiter="\t")}
        self.assertEqual(rows["OM-002"]["model_nodes"], "S_IGFBP1")
        self.assertEqual(rows["OM-002"]["activation_status"], "active_diagnostic")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
