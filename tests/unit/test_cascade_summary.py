"""Positions, node summaries, precedence and the arm comparison on hand-built events."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.cascade.summary import (
    compare_arms,
    node_summary,
    pairwise_precedence,
    positions,
)


def events(spec: dict[int, dict[str, tuple[int, float | None]]], seed0: int = 100):
    """``{trajectory: {node: (initial, first_time or None)}}`` -> an events table.

    A node with a time switches once and ends flipped; without one it stays.
    """
    rows = []
    for k, nodes in spec.items():
        for node, (initial, t) in nodes.items():
            switched = t is not None
            rows.append(
                {
                    "arm": "x",
                    "trajectory": k,
                    "seed": seed0 + k,
                    "node": node,
                    "initial": initial,
                    "final": (1 - initial) if switched else initial,
                    "n_switches_min": int(switched),
                    "first_switch_time": t if switched else np.nan,
                    "first_switch_resolved": True if switched else None,
                    "last_switch_time": t if switched else np.nan,
                    "last_switch_resolved": True if switched else None,
                    "category": "net_change_n_switches_min_1"
                    if switched
                    else "no_switch",
                    "rule_disagrees_at_horizon": False,
                }
            )
    return pd.DataFrame(rows)


class PositionTests(unittest.TestCase):
    def test_endpoints_and_definitions(self):
        ev = events({0: {"A": (1, 1.0), "B": (1, 2.0), "C": (1, 5.0)}})
        p = positions(ev)
        self.assertEqual(p["normalized_time"].loc[0].tolist(), [0.0, 0.25, 1.0])
        self.assertEqual(p["normalized_rank"].loc[0].tolist(), [0.0, 0.5, 1.0])
        self.assertEqual(p["absolute_time"].loc[0].tolist(), [1.0, 2.0, 5.0])

    def test_rank_and_time_normalisations_differ(self):
        ev = events({0: {"A": (1, 1.0), "B": (1, 1.1), "C": (1, 9.0)}})
        p = positions(ev)
        self.assertAlmostEqual(p["normalized_rank"].loc[0, "B"], 0.5)
        self.assertAlmostEqual(p["normalized_time"].loc[0, "B"], 0.1 / 8.0)

    def test_uniform_stretching_leaves_both_normalisations_unchanged(self):
        base = {0: {"A": (1, 0.3), "B": (0, 1.7), "C": (1, 2.2), "D": (1, 4.0)}}
        stretched = {0: {n: (i, t * 3.7) for n, (i, t) in base[0].items()}}
        a, b = positions(events(base)), positions(events(stretched))
        for name in ("normalized_time", "normalized_rank"):
            np.testing.assert_allclose(a[name].to_numpy(), b[name].to_numpy())

    def test_single_switch_trajectory_has_no_normalised_position(self):
        p = positions(events({0: {"A": (1, 0.5), "B": (1, None)}}))
        self.assertTrue(math.isnan(p["normalized_time"].loc[0, "A"]))
        self.assertTrue(math.isnan(p["normalized_rank"].loc[0, "A"]))
        self.assertEqual(p["absolute_time"].loc[0, "A"], 0.5)

    def test_simultaneous_switches_share_the_average_rank_and_undefined_time(self):
        p = positions(events({0: {"A": (1, 1.0), "B": (1, 1.0), "C": (1, 1.0)}}))
        self.assertEqual(set(p["normalized_rank"].loc[0]), {0.5})
        self.assertTrue(p["normalized_time"].loc[0].isna().all())

    def test_node_exclusion_changes_normalised_not_absolute(self):
        ev = events({0: {"A": (1, 1.0), "B": (1, 2.0), "C": (1, 5.0)}})
        full, sub = positions(ev), positions(ev, nodes=["A", "B"])
        self.assertEqual(sub["normalized_time"].loc[0, "B"], 1.0)
        self.assertNotEqual(full["normalized_time"].loc[0, "B"], 1.0)
        self.assertEqual(
            full["absolute_time"].loc[0, "B"], sub["absolute_time"].loc[0, "B"]
        )


class SummaryTests(unittest.TestCase):
    def test_every_node_has_a_row_and_conditioning_is_visible(self):
        spec = {
            k: {"A": (1, 1.0 + k), "B": (1, 2.0 + k if k < 2 else None), "C": (1, None)}
            for k in range(4)
        }
        s = node_summary(events(spec))
        self.assertEqual(set(s.node), {"A", "B", "C"})
        b = s[s.node == "B"].iloc[0]
        self.assertEqual(b.p_switch, 0.5)
        self.assertEqual(b.n_contributing, 2)
        self.assertEqual(b.normalized_time_n, 2)
        c = s[s.node == "C"].iloc[0]
        self.assertEqual(c.direction, "none")
        self.assertEqual(c.p_never_switches, 1.0)

    def test_already_in_state_is_distinguished_from_at_risk(self):
        spec = {0: {"A": (0, None), "Z": (1, 1.0)}, 1: {"A": (1, 2.0), "Z": (1, 1.0)}}
        a = node_summary(events(spec)).query("node == 'A'").iloc[0]
        self.assertEqual(a.p_initial_on, 0.5)
        self.assertEqual(a.p_switch_given_initial_on, 1.0)
        self.assertEqual(a.p_switch_given_initial_off, 0.0)

    def test_mixed_direction_gets_one_row_per_direction(self):
        spec = {k: {"A": (k % 2, 1.0), "Z": (1, 2.0)} for k in range(10)}
        s = node_summary(events(spec)).query("node == 'A'")
        self.assertEqual(sorted(s.direction), ["off_to_on", "on_to_off"])
        self.assertTrue(s.mixed_direction.all())
        self.assertAlmostEqual(s.direction_share.sum(), 1.0)


class PrecedenceTests(unittest.TestCase):
    def test_conditional_on_both_switching(self):
        spec = {
            0: {"A": (1, 1.0), "B": (1, 2.0)},
            1: {"A": (1, 3.0), "B": (1, 2.0)},
            2: {"A": (1, 1.0), "B": (1, None)},
        }
        pr = pairwise_precedence(events(spec)).set_index(["node_a", "node_b"])
        r = pr.loc[("A", "B")]
        self.assertEqual((r.n_both_switch, r.n_a_first, r.p_a_first), (2, 1, 0.5))
        self.assertAlmostEqual(r.frac_comparable, 2 / 3)
        self.assertEqual(r.n_only_a_switches, 1)


class CompareTests(unittest.TestCase):
    def test_paired_counts(self):
        p = events({0: {"A": (1, 1.0)}, 1: {"A": (1, 1.0)}, 2: {"A": (1, None)}})
        c = events({0: {"A": (1, None)}, 1: {"A": (1, 2.0)}, 2: {"A": (1, None)}})
        r = compare_arms(p, c).iloc[0]
        self.assertEqual(
            (
                r.n_switch_both,
                r.n_switch_perturbed_only,
                r.n_switch_control_only,
                r.n_switch_neither,
            ),
            (1, 1, 0, 1),
        )
        self.assertAlmostEqual(r.delta_p_switch, 1 / 3)

    def test_unpaired_arms_are_refused(self):
        p = events({0: {"A": (1, 1.0)}})
        with self.assertRaises(ValueError):
            compare_arms(p, events({0: {"A": (1, 1.0)}}, seed0=7))
        with self.assertRaises(ValueError):
            compare_arms(p, events({0: {"A": (0, 1.0)}}))


if __name__ == "__main__":
    unittest.main()


class ControlComparatorIsDirectionSpecific(unittest.TestCase):
    """B (figure.py): each direction row's control tick is the control's frequency
    of that same direction, on the bar's scale, not its total switch fraction."""

    def setUp(self):
        # 100 control trajectories: node A first switches ON->OFF in 50 and
        # OFF->ON in the other 50; B never switches.
        spec = {
            k: {
                "A": (1, 1.0 + k * 0.01) if k < 50 else (0, 1.0 + k * 0.01),
                "B": (1, None),
            }
            for k in range(100)
        }
        self.control = node_summary(events(spec))

    def test_each_direction_gets_its_own_frequency(self):
        from dt_adoc.cascade.figure import control_direction_frequency

        self.assertAlmostEqual(
            control_direction_frequency(self.control, "A", "on_to_off"), 0.5
        )
        self.assertAlmostEqual(
            control_direction_frequency(self.control, "A", "off_to_on"), 0.5
        )

    def test_an_unswitched_or_unreported_node(self):
        from dt_adoc.cascade.figure import control_direction_frequency

        self.assertEqual(
            control_direction_frequency(self.control, "B", "on_to_off"), 0.0
        )
        self.assertTrue(
            math.isnan(control_direction_frequency(self.control, "Z", "on_to_off"))
        )

    def test_the_figure_draws_each_row_against_its_own_direction(self):
        import tempfile
        from unittest import mock

        from dt_adoc.cascade import figure

        summary = self.control.assign(arm="perturbed")
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(
                figure,
                "control_direction_frequency",
                wraps=figure.control_direction_frequency,
            ) as spy,
        ):
            figure.render_cascade(
                summary,
                self.control,
                pairwise_precedence(events({0: {"A": (1, 1.0)}})),
                {},
                position="absolute_time",
                title="t",
                subtitle="s",
                footer="f",
                paths=[Path(tmp) / "c.png"],
            )
        directions = {c.args[1:] for c in spy.call_args_list}
        self.assertEqual(directions, {("A", "on_to_off"), ("A", "off_to_on")})
