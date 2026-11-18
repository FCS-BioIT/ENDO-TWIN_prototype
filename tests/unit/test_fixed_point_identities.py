"""The seven fixed-point identities of the 2026-11-18 audit, as regression tests.

These lock two different things, and the distinction matters.

The identities themselves are facts about ``network.bnd`` at v0.6.0. A test that
asserts them will fail the day someone edits a rule -- which is the point: the
identities are the reason the baseline terminal readouts cannot discriminate
these mechanisms, so a change that breaks one changes what the model can be
calibrated against, and that should never happen silently.

The verifier is separately tested against hand-built networks whose answers can
be read off by eye, because an "all seven hold" result from a broken decision
procedure looks exactly like a correct one.
"""

from __future__ import annotations

import unittest

from dt_adoc.reporting.fixed_point_identities import (
    IDENTITIES,
    IdentityError,
    verify_identities,
)
from dt_adoc.reporting.structure import load_structure

MODEL = "adoc-literature-superset-v0.6.0"


class TheAuditedIdentities(unittest.TestCase):
    """The seven claims, checked against the executable network."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = verify_identities(MODEL)

    def test_all_seven_hold(self) -> None:
        failed = [r.node for r in self.report.results if not r.holds]
        self.assertEqual(failed, [], f"identities no longer hold: {failed}")

    def test_every_identity_is_decided_with_zero_counterexamples(self) -> None:
        # `holds` is derived from the count, so this asserts the count itself
        # rather than trusting the flag computed from it.
        for result in self.report.results:
            with self.subTest(node=result.node):
                self.assertEqual(result.counterexamples, 0)
                self.assertIsNone(result.witness)

    def test_the_seven_are_the_seven(self) -> None:
        self.assertEqual(len(IDENTITIES), 7)
        self.assertEqual(
            [r.node for r in self.report.results],
            [
                "S_DECIDUALIZED",
                "S_TAZ_ECM",
                "E_RECEPTIVE_SURFACE",
                "X_MECHANICAL_PERMISSIVE_ECM",
                "X_ADHESION_ROUTE_SPP1",
                "X_ADHESION_ROUTE_REDUNDANT",
                "OUT_STABLE_ADHESION",
            ],
        )

    def test_enumeration_is_exhaustive_not_sampled(self) -> None:
        """Asserting `enumerated_states == 2 ** len(free)` only restates the
        line that computed it and cannot fail. This predicts a count
        arithmetically instead, which a truncated bit mask would break.

        `S_DECIDUALIZED` is identically `IN_PROGESTIN and IN_cAMP`, and the
        other 14 free variables are unconstrained, so exactly 2**14 of the
        2**16 assignments satisfy it. The earlier mask bug -- `states - 1`
        rather than `(1 << states) - 1` -- left only the low 16 bits of every
        column and would give at most 16 here.
        """
        from dt_adoc.model.topology import parse_bnd_rules
        from dt_adoc.reporting.fixed_point_identities import (
            _columns,
            _network_path,
            _topological_order,
        )

        rules = parse_bnd_rules(_network_path(MODEL, None))
        free = tuple(n for n in rules if rules[n].strip() == n)
        self.assertEqual(len(free), 16)
        states = 2 ** len(free)
        mask = (1 << states) - 1
        seeds = {}
        for index, node in enumerate(free):
            block = 1 << index
            column = 0
            for start in range(block, states, block * 2):
                column |= ((1 << block) - 1) << start
            seeds[node] = column
        columns = _columns(rules, _topological_order(rules, set(free)), seeds, mask)

        self.assertEqual(self.report.enumerated_states, states)
        self.assertEqual(columns["S_DECIDUALIZED"].bit_count(), 2**14)
        # And every free variable is true in exactly half of them.
        for node in free:
            with self.subTest(free=node):
                self.assertEqual(seeds[node].bit_count(), states // 2)

    def test_the_free_variables_match_the_structural_analysis(self) -> None:
        """Both analyses must hold the same things free, or they describe
        different models and agreement between them means nothing."""
        self.assertEqual(sorted(self.report.free), sorted(load_structure(MODEL).free))

    def test_the_network_verified_is_the_one_on_disk(self) -> None:
        import hashlib

        from dt_adoc.model.runtime import resolve_model

        path = resolve_model(MODEL, None).network_bnd
        self.assertEqual(
            self.report.network_sha256,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )


class ClampingTheAuditedTargets(unittest.TestCase):
    """The five nodes section 7 of the 2026-11-18 brief asks about.

    These assertions are about the model as it stands. If one fails, either a
    rule changed or an intervention became observable that was not -- both are
    things the next review has to be told about, which is why they are pinned.
    """

    TARGETS = (
        "S_BMP2",
        "S_TAZ_ECM",
        "E_GP130_STAT3",
        "E_CDH1_APICAL",
        "E_HBEGF",
    )

    @classmethod
    def setUpClass(cls) -> None:
        from dt_adoc.reporting.fixed_point_identities import clamp_discrimination

        cls.results = {
            (r.node, r.mode): r for r in clamp_discrimination(cls.TARGETS, MODEL)
        }

    def test_cdh1_and_hbegf_cannot_be_seen_in_any_output(self) -> None:
        """Neither direction of clamping moves a single OUT_ node, in any of
        the 65536 states. No steady-state experiment can detect them."""
        for node in ("E_CDH1_APICAL", "E_HBEGF"):
            for mode in ("loss_of_function", "gain_of_function"):
                with self.subTest(node=node, mode=mode):
                    self.assertTrue(self.results[node, mode].observationally_silent)

    def test_gp130_stat3_is_the_only_bidirectionally_visible_target(self) -> None:
        visible = {
            node
            for node in self.TARGETS
            if not self.results[node, "loss_of_function"].observationally_silent
            and not self.results[node, "gain_of_function"].observationally_silent
        }
        self.assertEqual(visible, {"E_GP130_STAT3"})

    def test_bmp2_and_taz_are_visible_only_when_removed(self) -> None:
        """They sit inside conjunctions, so removing one is decisive and
        forcing one on is not. An experiment designed around overexpression
        would read as a null for a reason that is not biological."""
        for node in ("S_BMP2", "S_TAZ_ECM"):
            with self.subTest(node=node):
                self.assertFalse(
                    self.results[node, "loss_of_function"].observationally_silent
                )
                self.assertTrue(
                    self.results[node, "gain_of_function"].observationally_silent
                )

    def test_every_target_shares_its_function_with_other_nodes(self) -> None:
        """No target computes anything its own; each is an exact alias of at
        least one other node, which is the identifiability problem itself."""
        for node in self.TARGETS:
            with self.subTest(node=node):
                self.assertTrue(self.results[node, "loss_of_function"].aliases)

    def test_prl_and_igfbp1_are_the_same_function(self) -> None:
        """Section 8E asks whether PRL and IGFBP1 report equivalent states.
        In this model they are not merely correlated, they are identical, so
        the model cannot express a difference between them at all."""
        aliases = self.results["S_TAZ_ECM", "loss_of_function"].aliases
        self.assertIn("S_PRL", aliases)
        self.assertIn("S_IGFBP1", aliases)

    def test_clamping_an_absent_node_is_an_error(self) -> None:
        from dt_adoc.reporting.fixed_point_identities import clamp_discrimination

        with self.assertRaises(IdentityError):
            clamp_discrimination(("NOT_A_NODE",), MODEL)


class TheVerifierItself(unittest.TestCase):
    """Hand-built cases whose answers are obvious by inspection."""

    def _report(self, rules: dict[str, str], identities, tmp) -> object:
        body = "".join(
            f"Node {name} {{\n  logic = {logic};\n  rate_up = @logic ? 1 : 0;\n"
            f"  rate_down = @logic ? 0 : 1;\n}}\n\n"
            for name, logic in rules.items()
        )
        (tmp / "network.bnd").write_text(body, encoding="utf-8")
        from dt_adoc.reporting import fixed_point_identities as mod

        original = mod._network_path
        mod._network_path = lambda *a, **k: tmp / "network.bnd"
        try:
            return mod.verify_identities("test", None, identities)
        finally:
            mod._network_path = original

    def setUp(self) -> None:
        import tempfile
        from pathlib import Path

        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def test_a_true_identity_holds(self) -> None:
        report = self._report(
            {"IN_A": "IN_A", "IN_B": "IN_B", "MID": "IN_A and IN_B", "OUT": "MID"},
            (("OUT", "IN_A and IN_B"),),
            self.tmp,
        )
        self.assertTrue(report.all_hold)
        self.assertEqual(report.results[0].counterexamples, 0)

    def test_a_false_identity_fails_and_is_quantified(self) -> None:
        """The verifier must find the disagreement, not merely fail to confirm."""
        report = self._report(
            {"IN_A": "IN_A", "IN_B": "IN_B", "OUT": "IN_A and IN_B"},
            (("OUT", "IN_A or IN_B"),),
            self.tmp,
        )
        self.assertFalse(report.all_hold)
        result = report.results[0]
        # and/or differ on exactly the two assignments where one input is set.
        self.assertEqual(result.counterexamples, 2)
        self.assertIsNotNone(result.witness)
        self.assertNotEqual(
            result.witness["IN_A"] and result.witness["IN_B"],
            result.witness["IN_A"] or result.witness["IN_B"],
        )

    def test_a_near_miss_is_not_waved_through(self) -> None:
        """One disagreeing assignment out of eight must still fail: a check
        that only caught gross differences would pass every plausible typo."""
        report = self._report(
            {
                "IN_A": "IN_A",
                "IN_B": "IN_B",
                "IN_C": "IN_C",
                "OUT": "IN_A and IN_B and IN_C",
            },
            (("OUT", "IN_A and IN_B"),),
            self.tmp,
        )
        self.assertFalse(report.all_hold)
        self.assertEqual(report.results[0].counterexamples, 1)
        self.assertEqual(
            report.results[0].witness, {"IN_A": True, "IN_B": True, "IN_C": False}
        )

    def test_substitution_sees_through_intermediate_nodes(self) -> None:
        """The whole point is that detail cancels; a verifier that compared
        rules textually would call this one false."""
        report = self._report(
            {
                "IN_A": "IN_A",
                "L1": "IN_A",
                "L2": "L1",
                "L3": "L2 and L1",
                "OUT": "L3 or L2",
            },
            (("OUT", "IN_A"),),
            self.tmp,
        )
        self.assertTrue(report.all_hold)

    def test_an_identity_naming_an_absent_node_is_an_error(self) -> None:
        with self.assertRaises(IdentityError):
            self._report(
                {"IN_A": "IN_A", "OUT": "IN_A"},
                (("NOT_A_NODE", "IN_A"),),
                self.tmp,
            )

    def test_an_identity_naming_an_unknown_variable_is_an_error(self) -> None:
        with self.assertRaises(IdentityError):
            self._report(
                {"IN_A": "IN_A", "OUT": "IN_A"},
                (("OUT", "IN_A and IN_NOWHERE"),),
                self.tmp,
            )


if __name__ == "__main__":
    unittest.main()
