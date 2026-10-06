"""Stage 4b §5: what a full veto of each eligible v0.6.0 target expresses.

``docs/stage4b_direct_admission.md`` classifies the 19 O8b-eligible targets by
what a veto changes on the observed readouts. The classification is generated
by ``dt_adoc.reporting.veto_expressivity`` and pinned here, so a rule, cfg,
policy or observation-map change that moves it is a visible diff rather than a
silent change to what the pre-registration says.
"""

from __future__ import annotations

import contextlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import resolve_model
from dt_adoc.reporting import veto_expressivity
from dt_adoc.reporting.veto_expressivity import (
    NULL_CLASS,
    OUTPUT_PATH,
    ExpressivityError,
    _contexts,
    _scenarios,
    baseline_marginal,
    expressivity,
    fixed_point,
    free_distributions,
    parse_network,
    render,
)


def _bnd(**rules: str) -> str:
    return "".join(f"Node {n} {{\n  logic = {r};\n}}\n" for n, r in rules.items())


V060 = "adoc-literature-superset-v0.6.0"

STRUCTURAL_NULLS = {
    "E_IHH",
    "E_PODXL",
    "E_HBEGF",
    "E_SPP1_EXPR",
    "E_CD98_CD9",
    "E_ANXA2_ACTIN",
    "E_CDH1_APICAL",
    "S_NR2F2",
    "S_SPP1",
}
OBSERVED_CLASSES = {
    frozenset({"E_PGR"}),
    frozenset(
        {"E_LIF", "E_GP130_STAT3", "E_PC6", "S_HAND2", "S_TAZ_ECM", "hand2_loss"}
    ),
    frozenset({"E_ITGAVB3_5", "X_SPP1_LUMEN_FREE", "anti_spp1"}),
    frozenset({"S_PGR", "S_PKA"}),
    frozenset({"mifepristone"}),
}


class VetoExpressivityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = expressivity(root=ROOT)
        cls.by_arm = {r["arm"]: r for r in cls.rows}

    @staticmethod
    def scenario_count():
        """The scenarios the generator builds for v0.6.0, for the cap test."""
        from dt_adoc.model.runtime import resolve_model

        spec = resolve_model("adoc-literature-superset-v0.6.0", ROOT)
        network = veto_expressivity.parse_network(
            spec.network_bnd.read_text(encoding="utf-8")
        )
        import csv as _csv

        with spec.node_dictionary.open(encoding="utf-8", newline="") as handle:
            roles = {
                r["node_id"]: r["model_role"]
                for r in _csv.DictReader(handle, delimiter="\t")
            }
        inputs = {
            n
            for n in network.free
            if roles.get(n) in veto_expressivity.PROTOCOL_INPUT_ROLES
        }
        distribution = veto_expressivity.free_distributions(
            spec.baseline_cfg.read_text(encoding="utf-8"), network.free
        )
        return _scenarios(distribution, inputs)

    def test_the_committed_output_is_current(self) -> None:
        self.assertEqual(
            (ROOT / OUTPUT_PATH).read_text(encoding="utf-8"), render(self.rows)
        )

    def test_every_eligible_target_is_classified(self) -> None:
        eligible = {r["arm"] for r in self.rows if r["arm_kind"] == "eligible_node"}
        self.assertEqual(len(eligible), 19)

    def test_the_structural_nulls(self) -> None:
        nulls = {
            r["arm"] for r in self.rows if r["structurally_null_on_observed"] == "yes"
        }
        self.assertEqual(nulls, STRUCTURAL_NULLS)
        # Eight change nothing but themselves; E_IHH changes only S_NR2F2.
        self.assertEqual(
            {
                a
                for a in nulls
                if self.by_arm[a]["changes_any_non_target_node"] == "yes"
            },
            {"E_IHH"},
        )

    def test_the_observed_classes(self) -> None:
        classes = {
            frozenset(r["observed_class_members"].split(";"))
            for r in self.rows
            if r["observed_class"] != NULL_CLASS
        }
        self.assertEqual(classes, OBSERVED_CLASSES)

    def test_reported_only_phenotypes_split_two_classes(self) -> None:
        self.assertNotEqual(
            self.by_arm["S_TAZ_ECM"]["extended_class"],
            self.by_arm["E_LIF"]["extended_class"],
        )
        self.assertNotEqual(
            self.by_arm["S_PKA"]["extended_class"],
            self.by_arm["S_PGR"]["extended_class"],
        )

    def test_the_integrin_veto_is_not_inert(self) -> None:
        """Corrects O8b §7.3/§11: the veto equals anti-SPP1, it is not near-null."""
        self.assertEqual(
            self.by_arm["E_ITGAVB3_5"]["observed_class"],
            self.by_arm["anti_spp1"]["observed_class"],
        )
        self.assertIn(
            "OUT_STABLE_ADHESION:-0.4200",
            self.by_arm["E_ITGAVB3_5"]["observed_effect_reference_context"],
        )

    def test_baselines_are_relay_priors(self) -> None:
        """0.82 = 1 - 0.30 * 0.60; the stress contexts multiply by 0.70."""
        self.assertAlmostEqual(
            baseline_marginal(
                "OUT_STABLE_ADHESION", "adhesion_challenge_hormone_treated", root=ROOT
            ),
            1 - 0.30 * 0.60,
        )
        for context in (
            "adhesion_challenge_excess_er_stress",
            "adhesion_challenge_high_ecm_stiffness",
        ):
            with self.subTest(context=context):
                self.assertAlmostEqual(
                    baseline_marginal("OUT_STABLE_ADHESION", context, root=ROOT),
                    (1 - 0.30 * 0.60) * 0.70,
                )

    def test_self_loops_are_free_variables(self) -> None:
        network = parse_network(_bnd(C="C", A="not C"))
        self.assertEqual(network.free, ("C",))
        self.assertEqual(network.order, ("A",))


class ExhaustiveInvarianceTest(unittest.TestCase):
    """§5.4.1: the classification holds under EVERY free-variable assignment.

    The pre-registration claims the v0.6.0 classes are a property of the rules
    rather than of the declared arms. That claim is canonical - §11.1 rests on
    it - so it is computed here rather than asserted in prose.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = veto_expressivity.invariance(root=ROOT)
        cls.by_arm = {r["arm"]: r for r in cls.rows}

    def test_the_committed_output_is_current(self) -> None:
        self.assertEqual(
            (ROOT / veto_expressivity.INVARIANCE_PATH).read_text(encoding="utf-8"),
            veto_expressivity.render_invariance(self.rows),
        )

    def test_it_enumerates_every_assignment_of_every_free_variable(self) -> None:
        """v0.6.0 has 16 free variables, so 65536 assignments, none sampled."""
        spec = resolve_model(V060, ROOT)
        network = veto_expressivity.parse_network(
            spec.network_bnd.read_text(encoding="utf-8")
        )
        self.assertEqual(len(network.free), 16)
        observed, _ = veto_expressivity._observed_sets(ROOT, set(network.nodes))
        arms = veto_expressivity._arms(V060, ROOT)
        _, _, width = veto_expressivity.exhaustive_signatures(network, observed, arms)
        self.assertEqual(width, 1 << 16)
        self.assertEqual(width, 65536)

    def test_the_nulls_are_null_under_every_assignment(self) -> None:
        nulls = {
            r["arm"] for r in self.rows if r["null_under_every_assignment"] == "yes"
        }
        self.assertEqual(nulls, STRUCTURAL_NULLS)

    def test_no_assignment_splits_any_declared_class(self) -> None:
        """The claim §11.1 rests on: condition-relativity is vacuous for v0.6.0."""
        for row in self.rows:
            with self.subTest(arm=row["arm"]):
                self.assertEqual(row["agrees_with_declared_condition_class"], "yes")

    def test_S_PGR_and_S_PKA_are_not_separable_by_any_arm(self) -> None:
        """Review proposed this pair as a condition-relative example; it is not."""
        self.assertEqual(
            self.by_arm["S_PGR"]["class_under_every_assignment"],
            self.by_arm["S_PKA"]["class_under_every_assignment"],
        )

    def test_it_agrees_with_the_independent_per_condition_implementation(self) -> None:
        """Two implementations, one exact: bit vectors against fixed-point marginals.

        `expressivity` evaluates one assignment at a time through `fixed_point`;
        this evaluates all of them at once with bitwise operators. Agreement on
        the declared contexts is what rules out a translation bug in either.
        """
        declared = {r["arm"]: r for r in veto_expressivity.expressivity(V060, ROOT)}
        for arm, row in self.by_arm.items():
            with self.subTest(arm=arm):
                exhaustive_null = row["null_under_every_assignment"] == "yes"
                declared_null = declared[arm]["structurally_null_on_observed"] == "yes"
                self.assertEqual(exhaustive_null, declared_null)

    def test_too_many_free_variables_are_refused(self) -> None:
        network = veto_expressivity.parse_network(
            _bnd(**{f"F{i}": f"F{i}" for i in range(30)})
        )
        with self.assertRaisesRegex(ExpressivityError, "above the cap"):
            veto_expressivity.exhaustive_signatures(network, (), [])


class RefusalTest(unittest.TestCase):
    """Every case the exactness argument of §5.2 does not cover is refused.

    A silent acceptance here would commit a wrong classification for a later
    model version, and §5.6 reads that classification as a screening bound.
    """

    def test_a_cycle_other_than_a_self_loop_is_refused(self) -> None:
        with self.assertRaisesRegex(ExpressivityError, "cycle"):
            parse_network(_bnd(A="B", B="A and C", C="C"))

    def test_a_declared_transition_rate_is_refused(self) -> None:
        """The fixed point is the limit only under default rates, for every node."""
        text = _bnd(C="C", A="not C").replace(
            "  logic = not C;\n", "  logic = not C;\n  rate_up = 2.0;\n"
        )
        with self.assertRaisesRegex(ExpressivityError, "transition rate"):
            parse_network(text)

    def test_a_cfg_that_sets_a_free_variable_is_refused(self) -> None:
        with self._sandbox() as (condition_dir, inputs, free, baseline):
            (condition_dir / "bad.cfg").write_text(
                "IN_E2.istate = TRUE;\nE_KLF12_HIGH.istate = TRUE;\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ExpressivityError, "free variables"):
                _contexts(condition_dir, inputs, free, baseline)

    def test_a_mixed_istate_on_a_protocol_input_is_refused(self) -> None:
        with self._sandbox() as (condition_dir, inputs, free, baseline):
            (condition_dir / "bad.cfg").write_text(
                "[IN_E2].istate = 0.40[0], 0.60[1];\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ExpressivityError, "mixed istate"):
                _contexts(condition_dir, inputs, free, baseline)

    def test_a_veto_of_a_free_node_is_refused(self) -> None:
        """Silently ignoring it would report the most damaging wrong answer: a null."""
        network = parse_network(_bnd(C="C", A="not C"))
        with self.assertRaisesRegex(ExpressivityError, "free .self-loop. node"):
            fixed_point(network, {"C": True}, frozenset({"C"}))

    def test_a_veto_of_an_unknown_node_is_refused(self) -> None:
        network = parse_network(_bnd(C="C", A="not C"))
        with self.assertRaisesRegex(ExpressivityError, "not nodes of this network"):
            fixed_point(network, {"C": True}, frozenset({"Z"}))

    def test_a_multi_node_istate_is_refused_in_a_condition_cfg(self) -> None:
        """`[A,B].istate` is a joint distribution the single-node form misses."""
        with self._sandbox() as (condition_dir, inputs, free, baseline):
            (condition_dir / "bad.cfg").write_text(
                "[IN_E2,E_KLF12_HIGH].istate = 0.5[0,0], 0.5[1,1];\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ExpressivityError, "multi-node istate"):
                _contexts(condition_dir, inputs, free, baseline)

    def test_a_multi_node_istate_is_refused_in_the_baseline(self) -> None:
        with self.assertRaisesRegex(ExpressivityError, "multi-node istate"):
            free_distributions("[A,B].istate = 0.5[0,0], 0.5[1,1];\n", ("A", "B"))

    def test_a_missing_reference_context_is_refused(self) -> None:
        """An empty reported column would otherwise be the only symptom."""
        with (
            mock.patch.object(veto_expressivity, "REFERENCE_CONTEXT", "no_such_cfg"),
            self.assertRaisesRegex(ExpressivityError, "reference context"),
        ):
            expressivity(root=ROOT)

    def test_an_unknown_activation_status_is_refused(self) -> None:
        original = veto_expressivity.KNOWN_STATUSES
        with (
            mock.patch.object(
                veto_expressivity, "KNOWN_STATUSES", original - {"rejected"}
            ),
            self.assertRaisesRegex(ExpressivityError, "unknown activation_status"),
        ):
            expressivity(root=ROOT)

    def test_an_uninterpreted_istate_value_is_refused(self) -> None:
        """`1.0` would otherwise be ignored and the input kept at its baseline."""
        with self._sandbox() as (condition_dir, inputs, free, baseline):
            (condition_dir / "bad.cfg").write_text(
                "IN_E2.istate = 1.0;\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ExpressivityError, "not interpreted"):
                _contexts(condition_dir, inputs, free, baseline)

    def test_scenarios_enumerate_combinations_not_one_at_a_time(self) -> None:
        """Flipping one at a time would miss a class only two together can split."""
        scenarios = _scenarios({"A": 0.0, "B": 0.0, "R": 0.3}, set())
        self.assertEqual(len(scenarios), 4)
        self.assertIn({"A": 1.0, "B": 1.0, "R": 0.3}, scenarios)
        self.assertTrue(all(s["R"] == 0.3 for s in scenarios))

    def test_too_many_hand_set_free_variables_are_refused(self) -> None:
        many = {
            f"N{i}": 0.0 for i in range(veto_expressivity.MAX_HAND_SET_FREE_NODES + 1)
        }
        with self.assertRaisesRegex(ExpressivityError, "hand-set free variables"):
            _scenarios(many, set())

    def test_v060_has_exactly_one_hand_set_free_variable(self) -> None:
        """So the committed classification covers both KLF12 values and no more."""
        self.assertEqual(len(VetoExpressivityTest.scenario_count()), 2)

    def test_a_mixed_baseline_istate_on_a_protocol_input_is_refused(self) -> None:
        with (
            self._sandbox() as (condition_dir, inputs, free, baseline),
            self.assertRaisesRegex(ExpressivityError, "mixed istate"),
        ):
            _contexts(condition_dir, inputs, free, {**baseline, "IN_E2": 0.5})

    def test_an_input_a_cfg_omits_keeps_its_baseline_value(self) -> None:
        """The runner merges the cfg onto the baseline; off is not the default."""
        with self._sandbox() as (condition_dir, inputs, free, baseline):
            (condition_dir / "a.cfg").write_text(
                "IN_E2.istate = TRUE;\n", encoding="utf-8"
            )
            on = _contexts(
                condition_dir, inputs, free, {**baseline, "IN_PROGESTIN": 1.0}
            )
            self.assertEqual(on["a"], {"IN_E2": True, "IN_PROGESTIN": True})
            off = _contexts(condition_dir, inputs, free, baseline)
            self.assertEqual(off["a"], {"IN_E2": True, "IN_PROGESTIN": False})

    @contextlib.contextmanager
    def _sandbox(self):
        inputs = ("IN_E2", "IN_PROGESTIN")
        free = inputs + ("E_KLF12_HIGH",)
        baseline = {"IN_E2": 0.0, "IN_PROGESTIN": 0.0, "E_KLF12_HIGH": 0.0}
        with tempfile.TemporaryDirectory() as directory:
            yield Path(directory), inputs, free, baseline


if __name__ == "__main__":
    unittest.main()
