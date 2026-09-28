"""Tests for the RNA <-> MaBoSS endpoint-concordance layer.

The layer derives nothing new: every call must be the node-support audit's, every
prediction the adopted model's, and the figure must be drawn from the table
alone. The dangerous failures are a table that silently stops matching its
committed inputs, and an abundance proxy or KLF12 acquiring a verdict.
"""

from __future__ import annotations

import filecmp
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.scrna import node_support_contract as C
from dt_adoc.scrna import node_support_expectations as X
from dt_adoc.scrna import observation_corrections as O
from dt_adoc.scrna import rna_endpoint_concordance as R

REPO = ROOT


def _map_rows():
    return X.rna_assessable_rows()


V040_BND = ROOT / "models/superset/adoc-literature-superset-v0.4.0/network.bnd"


class Regeneration(unittest.TestCase):
    def test_the_committed_table_regenerates_byte_identically(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "concordance.tsv"
            R.write_table(R.build(), out)
            self.assertTrue(filecmp.cmp(out, R.TABLE, shallow=False))

    def test_the_committed_figure_is_drawn_from_the_committed_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = R.render(R.TABLE, Path(tmp) / "concordance.png")
            self.assertTrue(filecmp.cmp(out, R.FIGURE, shallow=False))

    def test_the_figure_reads_only_the_table(self):
        rows = R.read_table()
        rows[0]["verdict"] = "concordant"
        with tempfile.TemporaryDirectory() as tmp:
            edited = Path(tmp) / "edited.tsv"
            R.write_table(rows, edited)
            out = R.render(edited, Path(tmp) / "edited.png")
            self.assertFalse(filecmp.cmp(out, R.FIGURE, shallow=False))


class CommittedInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r["model_node"]: r for r in R.read_table()}

    def test_every_rna_observable_node_has_one_row(self):
        expected = {r["model_node"] for r in X.rna_assessable_rows()}
        self.assertEqual(set(self.rows), expected)
        self.assertEqual(len(expected), 27)

    def test_per_donor_calls_are_the_node_support_audits(self):
        # A node whose map row was corrected after closure reads different genes
        # from the frozen audit, so its frozen calls are history: its calls must
        # instead be the frozen RULE over the corrected program on live evidence.
        corrected = O.superseded(REPO)
        self.assertTrue(corrected)
        stats = R.live_stats()
        corrected_rows = C.assessable_nodes(O.corrected_map_path(REPO))
        findings = json.loads(R.FINDINGS.read_text(encoding="utf-8"))
        checked = 0
        for klass in findings["alias_classes"].values():
            for node, member in klass["members"].items():
                calls = member.get("per_donor", {})
                if node in corrected:
                    compartment = C.COMPARTMENT_OF_NODE[
                        corrected_rows[node]["compartment"]
                    ]
                    calls = O.live_member_verdict(node, compartment, stats, root=REPO)[
                        "per_donor"
                    ]
                for donor, call in calls.items():
                    self.assertEqual(self.rows[node][f"call_{donor}"], call, node)
                    checked += 1
        self.assertGreaterEqual(checked, 60)

    def test_v051_differs_from_v040_only_at_an_unread_output(self):
        old, new = X.load_rules(V040_BND), X.load_rules(R.BND)
        self.assertEqual(set(old), set(new))
        changed = {n for n in old if old[n] != new[n]}
        self.assertEqual(changed, {"OUT_STROMAL_DECIDUALIZED"})
        for node, rule in new.items():
            if node != "OUT_STROMAL_DECIDUALIZED":
                self.assertIsNone(re.search(r"\bOUT_STROMAL_DECIDUALIZED\b", rule))

    def test_predictions_match_the_committed_maboss_converged_endpoint(self):
        for node, row in self.rows.items():
            ht = float(row["maboss_v040_converged_p_on_ht"])
            for encoding in ("untreated", "e2_only"):
                cnt = float(row[f"maboss_v040_converged_p_on_cnt_{encoding}"])
                self.assertIn(cnt, (0.0, 1.0), node)
                self.assertIn(ht, (0.0, 1.0), node)
                self.assertEqual(
                    row[f"predicted_if_cnt_{encoding}"],
                    X.direction(bool(cnt), bool(ht)),
                    node,
                )


class Scoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r["model_node"]: r for r in R.read_table()}

    def test_abundance_proxies_are_reported_not_scored(self):
        proxies = {
            n for n, r in self.rows.items() if r["observation_type"] == R.NOT_SCORED
        }
        self.assertEqual(len(proxies), 6)
        for node in proxies:
            self.assertEqual(self.rows[node]["verdict"], "reported_not_scored")

    def test_klf12_is_descriptive_with_no_call(self):
        row = self.rows["E_KLF12_HIGH"]
        self.assertEqual(row["verdict"], "descriptive_only")
        self.assertEqual({row[f"call_{d}"] for d in R.DONORS}, {""})
        self.assertTrue(row["rna_log2_fold_by_gene"].startswith("KLF12["))

    def test_the_encoding_dependent_node_is_uninformative(self):
        row = self.rows["E_ESTROGENIC_PROLIFERATION"]
        self.assertNotEqual(
            row["predicted_if_cnt_untreated"], row["predicted_if_cnt_e2_only"]
        )
        self.assertEqual(row["predicted_cnt_to_ht"], "")
        self.assertEqual(row["verdict"], "uninformative")

    def test_verdict_rule_is_the_conservative_three_of_three(self):
        v = R._verdict
        up, down = "moves_up", "moves_down"
        flat, indet = "flat_within_two_fold", "indeterminate"

        def states(*values):
            return dict(zip(R.DONORS, values, strict=True))

        self.assertEqual(v(states(up, up, up), up), "concordant")
        self.assertEqual(v(states(down, down, down), up), "discordant_opposite")
        self.assertEqual(v(states(flat, flat, flat), up), "no_response_within_two_fold")
        self.assertEqual(v(states(up, up, flat), up), "mixed_or_inconclusive")
        # An imprecise non-move is not evidence of no response.
        self.assertEqual(v(states(flat, flat, indet), up), "mixed_or_inconclusive")

    def test_construction_agreement_is_circular_not_concordant(self):
        v = R._verdict
        up = "moves_up"
        three = dict.fromkeys(R.DONORS, up)
        self.assertEqual(v(three, up, construction=True), "circular_agreement")
        row = self.rows["E_PAEP"]
        self.assertEqual(row["evidence_role"], "construction")
        self.assertEqual(row["verdict"], "circular_agreement")
        for node, r in self.rows.items():
            if r["evidence_role"] == R.CONSTRUCTION:
                self.assertNotEqual(r["verdict"], "concordant", node)

    def test_flat_requires_the_fold_interval_inside_two_fold(self):
        for r in self.rows.values():
            if r["verdict"] != "no_response_within_two_fold":
                continue
            self.assertEqual(
                {r[f"rna_state_{d}"] for d in R.DONORS}, {"flat_within_two_fold"}
            )
        # HBEGF SZ10: separated, +0.72, but the interval reaches past two-fold.
        self.assertEqual(self.rows["E_HBEGF"]["call_SZ10"], "no_material_move")
        self.assertEqual(self.rows["E_HBEGF"]["rna_state_SZ10"], "indeterminate")

    def test_undetected_in_an_arm_is_indeterminate_not_flat(self):
        # IHH is exactly zero in both SZ09 arms; the pseudocount fold is a floor.
        self.assertEqual(self.rows["E_IHH"]["call_SZ09"], "no_material_move")
        self.assertEqual(self.rows["E_IHH"]["rna_state_SZ09"], "indeterminate")

    def test_states_the_map_says_are_unresolved_are_not_scored(self):
        R.verify_not_resolved_grounds({r["model_node"]: r for r in _map_rows()})
        for node in R.STATE_NOT_RESOLVED:
            self.assertEqual(self.rows[node]["verdict"], "reported_not_scored")

    def test_only_paep_and_hbegf_escape_the_layer_caveat(self):
        verified = {
            n for n, r in self.rows.items() if r["layer_status"] == "raw_umi_verified"
        }
        self.assertEqual(verified, {"E_PAEP", "E_HBEGF"})

    def test_no_response_is_never_called_discordance(self):
        self.assertEqual(
            R.class_verdict(["circular_agreement", "no_response_within_two_fold"]),
            "members_diverge_one_within_two_fold",
        )
        for r in self.rows.values():
            self.assertFalse(r["verdict"].startswith("discordant_no"))
            self.assertNotIn("discordant", r["alias_class_verdict"])

    def test_class_verdicts_ignore_unscored_members(self):
        self.assertEqual(
            R.class_verdict(["circular_agreement", "discordant_opposite"]),
            "alias_challenged",
        )
        self.assertEqual(
            self.rows["E_LIF"]["alias_class_verdict"],
            "jointly_no_response_within_two_fold",
        )
        self.assertEqual(
            self.rows["E_PODXL"]["alias_class_verdict"], "no_scored_members"
        )

    def test_classification_inconsistencies_are_flagged_not_fixed(self):
        self.assertEqual(self.rows["S_HAND2"]["observation_type"], "direct_transcript")
        self.assertEqual(self.rows["S_NR2F2"]["observation_type"], "regulon_activity")
        for node in ("S_HAND2", "S_NR2F2"):
            self.assertTrue(self.rows[node]["classification_flag"])


if __name__ == "__main__":
    unittest.main()
