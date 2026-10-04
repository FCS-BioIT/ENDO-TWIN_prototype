"""Guards on `docs/gate3a_closure_audit.md`'s countable claims.

The audit's conclusion -- do not close Gate 3a, do not open Gate 3b -- rests on
counts that will change as work lands. These pin them so the recommendation
cannot quietly outlive its evidence: when one of these fails, the audit is due
for revision, which is the intended signal.
"""

from __future__ import annotations

import unittest
from collections import Counter

from dt_adoc.experiments.variant_discrimination import discriminate
from dt_adoc.reporting.coupling import load_coupling_adjudication
from dt_adoc.reporting.identifiability import load_identifiability, repo_root

MODEL = "adoc-literature-superset-v0.4.0"
ROOT = repo_root()


class TheModelIsUnchangedByGate3aTest(unittest.TestCase):
    """No candidate variant was adopted."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_identifiability(MODEL, ROOT)

    def test_the_partition_is_still_the_baseline_one(self) -> None:
        self.assertEqual(len(self.facts.node_ids), 59)
        self.assertEqual(len(self.facts.global_classes), 35)
        self.assertEqual(len(self.facts.latent), 5)


class UnidentifiedCountsTest(unittest.TestCase):
    """Section 2. If these fall, the gate has actually moved."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_coupling_adjudication(ROOT)
        cls.counts = Counter(r["adjudication"] for r in cls.rows.values())

    def test_the_adjudication_counts_are_as_audited(self) -> None:
        self.assertEqual(self.counts["ARTIFICIALLY_COUPLED"], 22)
        self.assertEqual(self.counts["UNIDENTIFIED"], 6)
        self.assertEqual(self.counts["BIOLOGICALLY_COLLAPSED"], 4)
        self.assertEqual(self.counts["NOT_RULE_COLLAPSED"], 27)

    def test_the_total_is_every_node(self) -> None:
        self.assertEqual(sum(self.counts.values()), 59)


class TheBindingConstraintIsTheObservationLayerTest(unittest.TestCase):
    """Section 3 -- the audit's central claim, and its whole basis."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = discriminate(ROOT)

    def test_no_axis_separates_on_a_node_with_a_usable_assay(self) -> None:
        for result in self.report["results"]:
            self.assertEqual(
                result["usable_assay_nodes"],
                [],
                f"{result['pair']} now separates on a usable assay -- the audit's "
                "recommendation to stay in Gate 3a may no longer hold",
            )

    def test_exactly_two_nodes_carry_a_usable_assay(self) -> None:
        from dt_adoc.experiments.variant_discrimination import USABLE_ASSAY

        usable = sorted(
            node
            for node, (tier, _) in self.report["readout_tiers"].items()
            if tier == USABLE_ASSAY
        )
        self.assertEqual(usable, ["E_PAEP", "S_IGFBP1"])

    def test_receptive_surface_is_a_separating_node_without_an_assay(self) -> None:
        """Reason 2 for not opening Gate 3b."""
        separating = {
            node
            for result in self.report["results"]
            for node in result["separating_nodes"]
        }
        self.assertIn("E_RECEPTIVE_SURFACE", separating)
        self.assertNotIn("E_RECEPTIVE_SURFACE", self.report["readout_tiers"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
