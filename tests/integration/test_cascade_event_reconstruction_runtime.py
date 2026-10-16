"""The tick-occupancy event reconstruction, checked against the installed cmaboss.

This is the implementation gate of ``docs/perturbation_cascade/README.md``: the
cascade tool reads switching events off single-trajectory tick occupancies, and
that is only valid if (1) the event stream of a seed does not depend on the tick,
so a reconstructed time can be checked against a much finer tick, and (2) the
switch-count lower bound agrees with a fine-tick count at the default tick on
fast dynamics. A synthetic network with known kinetics is used for both.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import cmaboss

from dt_adoc.cascade.events import node_events

NETWORK = """
Node A { logic = !A; }
Node D { logic = 0; }
"""
SEEDS = [
    int(s)
    for s in np.random.SeedSequence(20261008).generate_state(40) % (2**31 - 2) + 1
]


class ReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.bnd = Path(cls.tmp.name) / "net.bnd"
        cls.bnd.write_text(NETWORK)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_one(self, seed: int, tick: float, horizon: float):
        cfg = Path(self.tmp.name) / "net.cfg"
        cfg.write_text(
            "A.istate = 0;\nD.istate = 1;\nsample_count = 1;\n"
            f"max_time = {horizon};\ntime_tick = {tick};\ndiscrete_time = 0;\n"
            f"use_physrandgen = 0;\nseed_pseudorandom = {seed};\nthread_count = 1;\n"
        )
        result = cmaboss.MaBoSSSim(network=str(self.bnd), config=str(cfg)).run()
        values, times, nodes = result.get_nodes_probtraj()[:3]
        table = np.asarray(values, dtype=float)
        return {n: table[:, i] for i, n in enumerate(nodes)}, np.asarray(
            times, dtype=float
        )

    def test_single_switch_time_does_not_depend_on_the_tick(self):
        for seed in SEEDS[:20]:
            got = []
            for tick in (1.0, 0.1, 0.001):
                cols, starts = self.run_one(seed, tick, 10.0)
                got.append(node_events(cols["D"], starts, tick, 1).first_time)
            with self.subTest(seed=seed):
                self.assertTrue(np.isfinite(got[-1]))
                self.assertLess(max(abs(g - got[-1]) for g in got), 1e-9)

    def test_switch_count_lower_bound_matches_a_fine_tick_at_the_default_tick(self):
        agree = 0
        for seed in SEEDS:
            fine_cols, fine_starts = self.run_one(seed, 1e-4, 5.0)
            cols, starts = self.run_one(seed, 0.01, 5.0)
            fine = node_events(fine_cols["A"], fine_starts, 1e-4, 0).n_min
            coarse = node_events(cols["A"], starts, 0.01, 0).n_min
            self.assertLessEqual(coarse, fine)
            agree += coarse == fine
        # Rate-1 toggle: a hidden pair needs two switches inside one 0.01 window.
        self.assertGreaterEqual(agree, len(SEEDS) - 1)


if __name__ == "__main__":
    unittest.main()
