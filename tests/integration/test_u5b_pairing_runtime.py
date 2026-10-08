"""U5b's common-random-number pairing, re-run on the installed MaBoSS.

`docs/u5b_readout_repair/transient_preregistration.md` rests the paired design on
common random numbers: the same seed drives both model versions trajectory by
trajectory. This checks two consequences on one replicate block of 2,000
trajectories (the pre-registered check count):

- where the two rules never disagree (the three pre-declared control cells), the
  two versions' runs are exactly identical, node by node and tick by tick;
- in `hormone_treated_maternal`, where they do disagree, the readout differs and
  v0.5.1's phase average is the higher one.

It does not attribute any paired difference exactly to the rule. Once a
trajectory reaches a state where the rules disagree, the two versions consume the
stream differently, so later differences mix the rule's effect with Monte Carlo
variation; the size is estimated in the committed run, not here. The unit guards
read committed artifacts; this re-runs the pairing on the installed MaBoSS, so an
upgrade that changed how seeds or streams are consumed would fail here rather than
silently turn the committed paired bands into unpaired ones.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting import u5b_readout_transient as transient
from dt_adoc.reporting.u5b_increment import (
    MODEL_VERSION,
    PARENT_VERSION,
    REPAIRED_NODE,
)


class PairingRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runs = {
            version: transient._run_task(
                transient._Task(version, transient.CHECK_TRAJECTORIES, 0, str(ROOT))
            )
            for version in (PARENT_VERSION, MODEL_VERSION)
        }

    def test_the_pair_is_exactly_identical_where_the_rules_never_disagree(self) -> None:
        for cell in transient.EXACT_IDENTITY_CELLS:
            a = self.runs[MODEL_VERSION]["cells"][cell]["nodes"]
            b = self.runs[PARENT_VERSION]["cells"][cell]["nodes"]
            with self.subTest(cell=cell):
                self.assertEqual(a, b)

    def test_the_repaired_readout_differs_where_the_rules_do(self) -> None:
        a = self.runs[MODEL_VERSION]["cells"]["hormone_treated_maternal"]["nodes"]
        b = self.runs[PARENT_VERSION]["cells"]["hormone_treated_maternal"]["nodes"]
        self.assertNotEqual(a[REPAIRED_NODE], b[REPAIRED_NODE])
        # Direction only, on the phase average. Once the two versions reach a
        # state where the rules disagree they consume the stream differently, so
        # they are no longer the same trajectories and no per-tick ordering is
        # guaranteed -- only that v0.5.1, which need not wait for the markers,
        # reads higher on average. The committed run measures the size.
        self.assertGreater(
            sum(a[REPAIRED_NODE]) / len(a[REPAIRED_NODE]),
            sum(b[REPAIRED_NODE]) / len(b[REPAIRED_NODE]),
        )


if __name__ == "__main__":
    unittest.main()
