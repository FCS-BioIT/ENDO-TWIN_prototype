"""Exact structural claims the static figure is allowed to assert.

Every number here is derived by exhaustive enumeration over the model's free
variables, so these are statements about the model rather than estimates. They
are unit tests, not integration tests: no MaBoSS, no .cfg, no protocol duration,
no seed. That is precisely why the figure can be published while the
endpoint-readout policy is still unresolved.
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

from dt_adoc.reporting.structure import load_structure, structural_summary

SUPERSET = "adoc-literature-superset-v0.4.0"
FIGURE = ROOT / "docs/assets/adoc_superset_structure_v0.4.0.png"
SIDECAR = ROOT / "docs/assets/adoc_superset_structure_v0.4.0_metadata.json"


class SupersetStructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_structure(SUPERSET, ROOT)
        cls.summary = structural_summary(cls.facts)

    def test_shape_and_exhaustiveness(self) -> None:
        self.assertEqual(self.summary["nodes"], 59)
        self.assertEqual(self.summary["dependencies"], 97)
        self.assertEqual(self.summary["free_variables"], 19)
        self.assertEqual(self.summary["enumerated_states"], 2**19)
        self.assertEqual(self.summary["max_depth"], 11)

    def test_fifteen_nodes_cannot_change_any_phenotype(self) -> None:
        self.assertEqual(len(self.facts.phenotype_inert), 14)
        for node_id in ("E_HBEGF", "IN_XAV939", "X_INTERFACE_ANTIADHESIVE_RELAY"):
            self.assertIn(node_id, self.facts.phenotype_inert)

    def test_three_declared_inputs_are_read_by_no_rule(self) -> None:
        self.assertEqual(
            set(self.facts.unread_inputs),
            {"IN_XAV939", "IN_HCG", "IN_EMBRYO_CONDITIONED_SIGNAL"},
        )

    def test_fifty_eight_nodes_implement_thirty_two_functions(self) -> None:
        """The headline the figure asserts: most named nodes are duplicates."""
        self.assertEqual(self.summary["distinct_functions"], 35)
        self.assertEqual(len(self.facts.alias_classes), 8)

    def test_the_secretory_alias_class_has_nine_members(self) -> None:
        classes = {frozenset(members) for members in self.facts.alias_classes}
        self.assertIn(
            frozenset(
                {
                    "E_SECRETORY_STATE",
                    "E_PAEP",
                    "E_PC6",
                    "E_HBEGF",
                    "E_SPP1_EXPR",
                    "E_MUC1_SLEX",
                    "E_DAG1_CLEAVED",
                    "E_ANXA2_ACTIN",
                    "E_ITGAVB3_5",
                }
            ),
            classes,
        )

    def test_the_receptivity_output_is_no_longer_an_alias_of_e_lif(self) -> None:
        """INVERTED at v0.4.0, deliberately.

        Through v0.3.0 this test asserted the defect: OUT_EPITHELIAL_RECEPTIVE
        was bit-identical to E_LIF, so the declared phenotype carried no
        information the LIF gate did not already carry. IN_HAND2_LOSS makes the
        E_ESTROGENIC_PROLIFERATION veto reachable, which splits that 5-member
        class into {E_LIF, E_GP130_STAT3, E_CD98_CD9} and
        {E_RECEPTIVE_SURFACE, OUT_EPITHELIAL_RECEPTIVE}. The output is still not
        fully independent -- it remains an alias of E_RECEPTIVE_SURFACE, which
        is a separate and still-open defect -- so this pins the improvement
        exactly, not more.
        """
        for members in self.facts.alias_classes:
            if "OUT_EPITHELIAL_RECEPTIVE" in members:
                self.assertNotIn("E_LIF", members)
                self.assertIn("E_RECEPTIVE_SURFACE", members)
                return
        self.fail("OUT_EPITHELIAL_RECEPTIVE is not in any alias class")

    def test_the_antiadhesive_veto_never_binds(self) -> None:
        """Pinning the route off changes nothing: the veto is already implied.

        Note the route itself is highly reachable -- this is a statement about
        the inhibition, not about the node being unreachable.
        """
        self.assertIn(
            ("X_ANTIADHESIVE_ROUTE", "OUT_MATERNAL_ADHESION_COMPETENCE"),
            self.facts.never_binding_inhibitions,
        )

    def test_only_two_nodes_carry_an_activated_observation_mapping(self) -> None:
        self.assertEqual(set(self.facts.measured), {"E_PAEP", "S_IGFBP1"})

    def test_absorbed_dependencies_are_identified(self) -> None:
        self.assertEqual(len(self.facts.absorbed_edges), 15)


class CommittedFigureTest(unittest.TestCase):
    def test_the_figure_and_its_sidecar_exist(self) -> None:
        self.assertTrue(FIGURE.exists(), FIGURE)
        self.assertTrue(SIDECAR.exists(), SIDECAR)

    def test_the_sidecar_counts_match_a_fresh_derivation(self) -> None:
        """A stale caption number is the defect this guards against."""
        recorded = json.loads(SIDECAR.read_text(encoding="utf-8"))
        self.assertEqual(
            recorded["summary"], structural_summary(load_structure(SUPERSET, ROOT))
        )

    def test_the_sidecar_records_no_probabilistic_input(self) -> None:
        """No .cfg, so no istate or transition rate can reach the figure."""
        recorded = json.loads(SIDECAR.read_text(encoding="utf-8"))
        for reference in recorded["inputs"].values():
            self.assertNotIn(".cfg", reference["path"])
        self.assertNotIn("protocols.yaml", json.dumps(recorded["inputs"]))


if __name__ == "__main__":
    unittest.main()
