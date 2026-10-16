"""The conditioning overlay must move the node it names, and only that node.

Every number in `docs/scrna/klf12_conditioning_response.tsv` rests on two
claims that a green artifact cannot establish on its own: that the chain this
module runs is the chain `run_protocol` runs, and that the prior reaches
`E_KLF12_HIGH`. Both are executed here, small and fast, against the real engine.

The second is the one that catches the interesting failure. A prior that landed
on a derived node, or that was silently dropped when the merged configuration
kept `baseline.cfg`'s `FALSE`, would still produce a table -- a table whose
endpoints happened to look plausible. The analytic law is what distinguishes
them: `E_KLF12_HIGH` never moves once set, and it gates `E_LIF` and therefore
every output that passes through `E_RECEPTIVE_SURFACE`. For the outputs the
high sub-ensemble drives to zero -- and ONLY those -- the converged endpoint is
the unconditioned value scaled by ``1 - prior``. That special case is not the
general law: it is false for `E_KLF12_HIGH` itself, for `E_ITGAVB3_5`, whose
`E_SECRETORY_STATE` disjunct survives the gate closing, and for
`OUT_STROMAL_DECIDUALIZED`, which `test_the_stromal_arm_is_untouched` below
pins at 1.000. The general law is the two-extreme mixture in
`mixture_prediction`; the three assertions here are deliberately restricted to
the nodes where the scaled form holds.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.concordance.simulate import CONVERGED_PHASE_HORIZON, run_arm
from dt_adoc.scrna.klf12_conditioning import ARMS, MODEL_VERSION, _run_chain

#: Small on purpose. These assertions are structural -- an exact reproduction
#: and an exact scaling law -- so they do not need the sweep's trajectory count.
TRAJECTORIES = 2000
SEED = 1
GRADED = ARMS["hormone_treated"]


def _chain(prior: float, *, apply_prior: bool = True) -> dict[str, float]:
    return _run_chain(
        GRADED,
        prior=prior,
        seed=SEED,
        trajectory_count=TRAJECTORIES,
        phase_horizon=CONVERGED_PHASE_HORIZON,
        root=ROOT,
        apply_prior=apply_prior,
    )


class TheOverlayDoesNotDriftFromTheRunnerItCopies(unittest.TestCase):
    def test_no_prior_reproduces_run_protocol_exactly(self) -> None:
        """Not "close to": the same seed and chain must give the same numbers."""
        reference = run_arm(
            "hormone_treated",
            GRADED,
            horizon_class="converged",
            model_version=MODEL_VERSION,
            root=ROOT,
            trajectory_count=TRAJECTORIES,
            seeds=(SEED,),
        )
        mine = _chain(0.0, apply_prior=False)
        self.assertEqual(set(mine), set(reference.node_mean))
        for node_id, value in reference.node_mean.items():
            with self.subTest(node=node_id):
                self.assertEqual(mine[node_id], value)


class ThePriorReachesTheNodeItNames(unittest.TestCase):
    def test_the_conditioned_node_reads_back_at_the_requested_value(self) -> None:
        for prior in (0.0, 0.3, 1.0):
            with self.subTest(prior=prior):
                self.assertAlmostEqual(_chain(prior)["E_KLF12_HIGH"], prior, places=2)

    def test_the_endpoint_follows_the_analytic_scaling(self) -> None:
        unconditioned = _chain(0.0)
        for prior in (0.3, 1.0):
            conditioned = _chain(prior)
            for node_id in (
                "OUT_EPITHELIAL_RECEPTIVE",
                "OUT_MATERNAL_ADHESION_COMPETENCE",
                "OUT_STABLE_ADHESION",
            ):
                with self.subTest(prior=prior, node=node_id):
                    self.assertAlmostEqual(
                        conditioned[node_id],
                        unconditioned[node_id] * (1.0 - prior),
                        places=2,
                    )

    def test_the_stromal_arm_is_untouched(self) -> None:
        """`OUT_STROMAL_DECIDUALIZED` has no path from the conditioned node."""
        unconditioned = _chain(0.0)
        for prior in (0.3, 1.0):
            with self.subTest(prior=prior):
                self.assertAlmostEqual(
                    _chain(prior)["OUT_STROMAL_DECIDUALIZED"],
                    unconditioned["OUT_STROMAL_DECIDUALIZED"],
                    places=6,
                )


if __name__ == "__main__":
    unittest.main()
