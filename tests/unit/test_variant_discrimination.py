"""Gate 3a: the separating-observation computation, and the trap it exists to catch.

With no fitted score left, "an observation distinguishes it" is the only
admissible reason to prefer a candidate rule. These tests pin the computation
that decides that, and in particular the case where structural gain and
experimental information come apart.
"""

from __future__ import annotations

import csv
import unittest

from dt_adoc.experiments.variant_discrimination import (
    EXCLUDED,
    INPUT_DEFAULTS,
    MAPPED_COMPOSITE,
    MATERNAL_OUT_NODES,
    NO_ASSAY,
    OUT_MD,
    OUT_TSV,
    PAIRS,
    USABLE_ASSAY,
    VARIANTS,
    build,
    discriminate,
)
from dt_adoc.reporting.identifiability import repo_root
from tests.unit.checkout_isolation import regenerate_in_shadow

ROOT = repo_root()


class DiscriminationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = discriminate(ROOT)
        cls.by_pair = {r["pair"]: r for r in cls.report["results"]}

    def test_structural_gain_does_not_imply_experimental_separation(self) -> None:
        """CD98-b adds a distinct Boolean function and is still unseparable.

        The candidate table records CD98-b as taking the partition 35 -> 36. It
        reads `IN_HCG`, which is false in every recorded arm, so it predicts
        exactly what v0.4 predicts everywhere this project can observe. This is
        the single most important assertion in the module: if it ever passes
        trivially because the pair stopped being computed, the report's central
        warning has quietly stopped being tested.
        """
        result = self.by_pair["CD98-a vs CD98-b"]
        current = next(s for s in result["per_setting"] if s["is_current_design"])
        self.assertEqual(
            current["hits"], [], "CD98-b must match v0.4 in the current design"
        )
        # But it is NOT impossible to separate: IN_HCG exists and is off in
        # every arm, so an hCG-on arm distinguishes them. Calling this
        # unseparable confused "no current arm does it" with "nothing can".
        self.assertEqual(result["verdict"], "REQUIRES_A_NEW_CONTROLLED_INPUT")
        self.assertIn("IN_HCG", result["controlled_inputs_varied"])
        self.assertEqual(result["separating_nodes"], ["E_CD98_CD9"])

    def test_the_e2_disjunct_is_what_is_actually_separable(self) -> None:
        """CD98-c differs from both others, embryo-free, with opposite values."""
        for pair in ("CD98-a vs CD98-c", "CD98-b vs CD98-c"):
            result = self.by_pair[pair]
            self.assertEqual(
                result["verdict"], "DISCRIMINABLE_IN_CURRENT_ARMS_EMBRYO_FREE_OPPOSITE"
            )
            hits = [h for s in result["per_setting"] for h in s["hits"]]
            opposite = [h for h in hits if h["embryo_free"] and h["opposite"]]
            self.assertTrue(opposite)
            self.assertTrue(all(h["node"] == "E_CD98_CD9" for h in opposite))
            self.assertIn("e2_primed_maternal", {h["arm"] for h in opposite})

    def test_both_cdh1_pairs_need_embryos_in_the_current_design(self) -> None:
        for pair in ("CDH1-a vs CDH1-b", "CDH1-b vs CDH1-c"):
            result = self.by_pair[pair]
            self.assertEqual(
                result["verdict"], "DISCRIMINABLE_IN_CURRENT_ARMS_ONLY_WITH_EMBRYOS"
            )
            current = next(s for s in result["per_setting"] if s["is_current_design"])
            self.assertTrue(current["hits"])
            self.assertFalse(any(h["embryo_free"] for h in current["hits"]))

    def test_an_hcg_arm_opens_an_embryo_free_route_for_cdh1_a_vs_b(self) -> None:
        """Varying an unexercised input can CREATE a discrimination."""
        other = [
            s
            for s in self.by_pair["CDH1-a vs CDH1-b"]["per_setting"]
            if not s["is_current_design"]
        ]
        self.assertTrue(any(h["embryo_free"] for s in other for h in s["hits"]))

    def test_the_same_input_DESTROYS_the_cdh1_b_vs_c_discrimination(self) -> None:
        """And it can also remove one, which is why per-setting is reported.

        `CDH1-b` is `IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL`; `CDH1-c` adds
        `IN_EMBRYO_CONTACT`. With either of the first two on, both rules are
        satisfied everywhere and the readings become identical. So that pair is
        separable ONLY where contact occurs without an embryo cue -- which needs
        an embryo. Reporting a single pooled verdict would hide this.
        """
        other = [
            s
            for s in self.by_pair["CDH1-b vs CDH1-c"]["per_setting"]
            if not s["is_current_design"]
        ]
        self.assertTrue(other)
        for setting in other:
            self.assertEqual(setting["hits"], [])

    def test_a_supplied_input_is_conditioned_on_not_marginalised(self) -> None:
        """The repair. Averaging over "IL-11 supplied" and "IL-11 absent"
        reported 0.75 for GP130-b -- a number no experiment can produce. Under
        conditioning the two settings are two experiments, and they say
        different things: with IL-11 absent the variant is indistinguishable
        from v0.4, with IL-11 supplied it gives opposite predictions.
        """
        result = self.by_pair["GP130-a vs GP130-b"]
        self.assertEqual(result["verdict"], "REQUIRES_A_NEW_CONTROLLED_INPUT")
        self.assertEqual(result["controlled_inputs_varied"], ["X_IL11"])
        settings = {s["is_current_design"]: s for s in result["per_setting"]}
        self.assertEqual(settings[True]["hits"], [], "IL-11 absent must be a no-op")
        self.assertTrue(settings[False]["hits"])
        self.assertTrue(
            any(h["opposite"] and h["embryo_free"] for h in settings[False]["hits"])
        )
        # 0.5 is legitimate: E_KLF12_HIGH is a genuine latent and is still
        # marginalised. 0.75 is the signature of the withdrawn code, which
        # averaged over the SUPPLIED INPUT as though it were uncertain.
        values = {
            v
            for s in result["per_setting"]
            for h in s["hits"]
            for v in (h["left"], h["right"])
        }
        self.assertNotIn(0.75, values)
        self.assertNotIn(0.25, values)

    def test_the_current_design_is_not_assumed_to_be_all_inputs_off(self) -> None:
        """Endogenous DAG1 IS cleavable; the experiment is the resistant mutant.

        Treating all-off as the current design made the wild-type condition
        look like the intervention, and reported PC6-b as discriminable today.
        """
        self.assertIs(INPUT_DEFAULTS["E_DAG1_CLEAVABLE"], True)
        self.assertIs(INPUT_DEFAULTS["X_IL11"], False)
        result = self.by_pair["PC6-a vs PC6-b"]
        self.assertEqual(result["verdict"], "REQUIRES_A_NEW_CONTROLLED_INPUT")
        current = next(s for s in result["per_setting"] if s["is_current_design"])
        self.assertEqual(current["setting"], {"E_DAG1_CLEAVABLE": True})

    def test_readout_tiers_use_the_same_node_universe_as_the_comparison(
        self,
    ) -> None:
        """One universe, or the header claims a readout that cannot appear."""
        for node in self.report["readout_tiers"]:
            self.assertTrue(
                node.startswith(("E_", "S_")) or node in MATERNAL_OUT_NODES, node
            )

    def test_a_mapped_composite_is_not_counted_as_a_usable_assay(self) -> None:
        """The repair. OM-009 maps OUT_EPITHELIAL_RECEPTIVE and says in its own
        claim_ceiling "Not usable to validate OUT_EPITHELIAL_RECEPTIVE
        behavior": reported_only, confidence low, source_rows_n 0,
        objective_treatment not_used. Calling that "measurable today" overstated
        what the observation layer can do.
        """
        tier, note = self.report["readout_tiers"]["OUT_EPITHELIAL_RECEPTIVE"]
        self.assertEqual(tier, MAPPED_COMPOSITE)
        self.assertIn("reported_only", note)
        self.assertIn("source_rows_n=0", note)
        for pair in ("GP130-a vs GP130-b", "PC6-a vs PC6-b"):
            result = self.by_pair[pair]
            self.assertIn("OUT_EPITHELIAL_RECEPTIVE", result["mapped_composite_nodes"])
            self.assertNotIn("OUT_EPITHELIAL_RECEPTIVE", result["usable_assay_nodes"])

    def test_an_actively_used_row_does_earn_the_usable_tier(self) -> None:
        """The tier is not vacuous: PAEP and IGFBP-1 clear it."""
        for node in ("E_PAEP", "S_IGFBP1"):
            self.assertEqual(self.report["readout_tiers"][node][0], USABLE_ASSAY)
        # PRL is mapped but provisional/not_used, so it must NOT clear it.
        self.assertEqual(self.report["readout_tiers"]["S_PRL"][0], MAPPED_COMPOSITE)

    def test_no_gate3a_pair_separates_on_a_usable_assay(self) -> None:
        """Stark, and now on a defensible basis rather than a flat label."""
        for result in self.report["results"]:
            self.assertEqual(
                result["usable_assay_nodes"],
                [],
                f"{result['pair']} now separates on a usable assay",
            )

    def test_unmapped_nodes_report_no_assay(self) -> None:
        hits = [
            h
            for r in self.report["results"]
            for s in r["per_setting"]
            for h in s["hits"]
        ]
        self.assertTrue(any(h["readout_tier"] == NO_ASSAY for h in hits))

    def test_every_declared_pair_is_computed(self) -> None:
        self.assertEqual(len(self.report["results"]), len(PAIRS))
        known = {v.variant_id for v in VARIANTS}
        for left, right in PAIRS:
            self.assertIn(left, known)
            self.assertIn(right, known)

    def test_the_inert_and_cyclic_variants_are_excluded_explicitly(self) -> None:
        """Dropped silently they would look like variants nobody proposed."""
        for variant_id in ("IGFBP1-fb", "EPAC", "HH-reception"):
            self.assertIn(variant_id, EXCLUDED)
            self.assertGreater(len(EXCLUDED[variant_id]), 40)

    def test_baselines_are_not_paired_against_each_other(self) -> None:
        """Guards the probe itself: an edit-free variant must be a no-op."""
        for left, right in (("CD98-a", "CDH1-a"), ("CD98-a", "GP130-a")):
            pair = next(
                (
                    r
                    for r in self.report["results"]
                    if {r["left"], r["right"]} == {left, right}
                ),
                None,
            )
            self.assertIsNone(pair, "baselines are not paired against each other")
        baselines = [v for v in VARIANTS if v.is_baseline]
        self.assertGreaterEqual(len(baselines), 4)


class GeneratedOutputTest(unittest.TestCase):
    def test_regenerating_reproduces_the_committed_outputs(self) -> None:
        produced = regenerate_in_shadow(build, (OUT_MD, OUT_TSV))
        for relative, content in produced.items():
            self.assertEqual((ROOT / relative).read_bytes(), content, str(relative))

    def test_the_markdown_warns_about_structural_versus_experimental(self) -> None:
        text = (ROOT / OUT_MD).read_text(encoding="utf-8")
        self.assertIn("Generated file — do not edit", text)
        self.assertIn("Structural vs experimental", text)
        self.assertIn("conditioned on, never marginalised", text)

    def test_the_tsv_records_the_unseparable_pair(self) -> None:
        with (ROOT / OUT_TSV).open(encoding="utf-8") as fh:
            rows = {r["pair"]: r for r in csv.DictReader(fh, delimiter="\t")}
        self.assertEqual(
            rows["CD98-a vs CD98-b"]["verdict"],
            "REQUIRES_A_NEW_CONTROLLED_INPUT",
        )
        self.assertEqual(
            rows["CD98-a vs CD98-b"]["discriminable_in_current_arms"], "False"
        )

    def test_the_report_keeps_the_prl_igfbp1_task_open(self) -> None:
        """Excluding the IGFBP1-fb repair must not read as closing the axis."""
        text = (ROOT / OUT_MD).read_text(encoding="utf-8")
        self.assertIn("does NOT close the PRL/IGFBP1 Gate-3a task", text)
        self.assertIn("identical by", text)
        self.assertIn("IGFBP-1-before-PRL onset order", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
