"""Switching events read off single-trajectory tick occupancies.

The occupancy tables are built by hand from known event sequences, so each
expected value is derived from the sequence, not from the code under test.
"""

from __future__ import annotations

import itertools
import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.cascade.events import (
    NET_CHANGE_N_MIN_1,
    NET_CHANGE_N_MIN_GT_1,
    NO_SWITCH,
    TRANSIENT_RETURN,
    UNRESOLVED_END,
    node_events,
    trajectory_events,
)


def occupancy(initial: int, switch_times: list[float], tick: float, horizon: float):
    """ON-occupancy per window of a path that starts at ``initial`` and flips at each time."""
    n = round(horizon / tick)
    starts = np.arange(n) * tick
    out = np.zeros(n)
    edges = [0.0, *sorted(switch_times), horizon]
    state = initial
    for a, b in itertools.pairwise(edges):
        if state == 1:
            for j in range(n):
                lo, hi = starts[j], starts[j] + tick
                out[j] += max(0.0, min(hi, b) - max(lo, a)) / tick
        state = 1 - state
    return out, starts


class NodeEventTests(unittest.TestCase):
    tick = 0.1
    horizon = 2.0

    def run_path(self, initial, times, known_initial=True):
        x, starts = occupancy(initial, times, self.tick, self.horizon)
        return node_events(x, starts, self.tick, initial if known_initial else None)

    def test_single_known_switch_is_exact(self):
        e = self.run_path(1, [0.537])
        self.assertEqual((e.initial, e.final, e.n_min), (1, 0, 1))
        self.assertAlmostEqual(e.first_time, 0.537, places=12)
        self.assertAlmostEqual(e.last_time, 0.537, places=12)
        self.assertTrue(e.first_resolved)
        self.assertEqual(e.category, NET_CHANGE_N_MIN_1)

    def test_off_to_on(self):
        e = self.run_path(0, [1.234])
        self.assertEqual((e.initial, e.final), (0, 1))
        self.assertAlmostEqual(e.first_time, 1.234, places=12)

    def test_no_switch(self):
        e = self.run_path(1, [])
        self.assertEqual(e.n_min, 0)
        self.assertTrue(math.isnan(e.first_time))
        self.assertEqual(e.category, NO_SWITCH)

    def test_switches_in_separate_windows_are_counted_and_timed(self):
        e = self.run_path(1, [0.33, 0.81, 1.47])
        self.assertEqual(e.n_min, 3)
        self.assertAlmostEqual(e.first_time, 0.33, places=12)
        self.assertAlmostEqual(e.last_time, 1.47, places=12)
        self.assertEqual(e.category, NET_CHANGE_N_MIN_GT_1)

    def test_transient_switch_that_reverses(self):
        e = self.run_path(1, [0.42, 1.05])
        self.assertEqual((e.final, e.n_min), (1, 2))
        self.assertEqual(e.category, TRANSIENT_RETURN)
        self.assertAlmostEqual(e.first_time, 0.42, places=12)

    def test_out_and_back_inside_one_window_is_a_lower_bound(self):
        e = self.run_path(1, [0.51, 0.56])
        self.assertEqual(e.n_min, 2)
        self.assertFalse(e.first_resolved)
        # The first departure is no later than the reported time.
        self.assertGreaterEqual(e.first_time + 1e-12, 0.51)
        self.assertEqual(e.category, TRANSIENT_RETURN)

    def test_three_switches_in_one_window_are_undercounted_not_overcounted(self):
        e = self.run_path(1, [0.51, 0.53, 0.56])
        self.assertEqual(e.n_min, 1)  # the hidden pair is invisible
        self.assertLessEqual(e.n_min, 3)
        # So the category may not say "one switch": three happened here.
        self.assertEqual(e.category, NET_CHANGE_N_MIN_1)
        self.assertNotIn("single", e.category)

    def test_adjacent_fractional_windows(self):
        e = self.run_path(0, [0.55, 0.62])  # ON in window 5, OFF in window 6
        self.assertEqual(e.n_min, 2)
        self.assertFalse(e.first_resolved)

    def test_switch_in_last_window_leaves_final_unknown(self):
        e = self.run_path(1, [1.95])
        self.assertIsNone(e.final)
        self.assertEqual(e.category, UNRESOLVED_END)
        self.assertEqual(e.n_min, 1)

    def test_switch_in_first_window_needs_the_known_initial_state(self):
        known = self.run_path(1, [0.04])
        self.assertAlmostEqual(known.first_time, 0.04, places=12)
        unknown = self.run_path(1, [0.04], known_initial=False)
        self.assertIsNone(unknown.initial)
        self.assertTrue(math.isnan(unknown.first_time))
        self.assertEqual(unknown.category, UNRESOLVED_END)

    def test_float_dust_is_not_a_switch(self):
        x, starts = occupancy(1, [], self.tick, self.horizon)
        x[7] = 1.0 - 1e-12
        self.assertEqual(node_events(x, starts, self.tick, 1).n_min, 0)

    def test_contradictory_initial_state_is_refused(self):
        x, starts = occupancy(1, [], self.tick, self.horizon)
        with self.assertRaises(ValueError):
            node_events(x, starts, self.tick, 0)

    def test_time_is_invariant_to_the_tick(self):
        for tick in (0.5, 0.1, 0.01):
            x, starts = occupancy(1, [0.737], tick, 2.0)
            self.assertAlmostEqual(
                node_events(x, starts, tick, 1).first_time, 0.737, 10
            )


class TrajectoryEventTests(unittest.TestCase):
    def test_all_nodes_switch_simultaneously(self):
        x, starts = occupancy(1, [0.3], 0.1, 1.0)
        table = np.column_stack([x, x, x])
        ev = trajectory_events(
            table, starts, ["A", "B", "C"], 0.1, {"A": 1, "B": 1, "C": 1}
        )
        times = {e.first_time for e in ev.values()}
        self.assertEqual(len(times), 1)

    def test_shape_mismatch_is_refused(self):
        with self.assertRaises(ValueError):
            trajectory_events(np.zeros((3, 2)), np.arange(3), ["A"], 0.1, {})


if __name__ == "__main__":
    unittest.main()
