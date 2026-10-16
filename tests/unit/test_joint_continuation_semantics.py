"""Joint continuation semantics, checked against hand-computed distributions.

The joint continuation carries a phase's final state forward: it projects the
last-state distribution onto the memory nodes, drops the states at or below the
probability cutoff, renormalises, and installs the result as the next phase's
initial joint state (`maboss_adapter.project_joint_distribution` and
`apply_joint_distribution`). Every multi-phase lineage of the adopted model
passes through it.

The existing runtime checks (tests/integration/test_maboss_continuation_modes.py)
use one symmetric 50/50 distribution with Monte Carlo tolerances of 0.05. A
mutation that moved 1 % of the modal state's mass to the others passed them, and
it passed every other test of the adopted model (audit mutation M6c,
2026-10-15). So the cases here are small, explicit and asymmetric, with a
low-probability state in each. Every expected value is worked out by hand in
the test from the stated input: none comes from the function under test.
Probabilities are dyadic, so sums of the inputs are exact in binary floating
point, and comparisons are exact except after a renormalising division.
"""

from __future__ import annotations

import math
import unittest

import pandas as pd

from dt_adoc.maboss_adapter import (
    apply_joint_distribution,
    project_joint_distribution,
)


def _last_states(row: dict[str, float]) -> pd.DataFrame:
    """A last-state table in MaBoSS's layout: one row, one column per state label.

    The first row is a decoy, so a projection that read anything but the last
    row would be visibly wrong.
    """
    decoy = {label: 0.0 for label in row}
    decoy[next(iter(row))] = 1.0
    return pd.DataFrame([decoy, row])


#: Three nodes, A, B and C; memory is (A, B), so C must be marginalised out.
#: The (A, B) = (1, 0) state carries 1/16 of the mass: a low-probability state.
THREE_NODE = {
    "A -- B -- C": 0.25,
    "A -- B": 0.125,
    "A": 0.0625,
    "C": 0.0625,
    "<nil>": 0.5,
}


class ProjectionIsTheExactMarginal(unittest.TestCase):
    def test_states_project_onto_the_memory_nodes_exactly(self) -> None:
        # By hand: (1,1) = 0.25 + 0.125; (1,0) = 0.0625; (0,0) = 0.0625 + 0.5.
        # (0,1) has no support. Nothing is dropped, so nothing is rescaled.
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(THREE_NODE),
            memory_nodes=("A", "B"),
            probability_cutoff=0.0,
        )
        self.assertEqual(
            projected["distribution"],
            {(1, 1): 0.375, (1, 0): 0.0625, (0, 0): 0.5625},
        )
        self.assertEqual(projected["source_state_count"], 5)
        self.assertEqual(projected["retained_state_count"], 3)
        self.assertEqual(projected["dropped_probability_mass"], 0.0)
        self.assertFalse(projected["renormalized"])

    def test_the_tuple_follows_the_memory_node_order(self) -> None:
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(THREE_NODE),
            memory_nodes=("B", "A"),
            probability_cutoff=0.0,
        )
        self.assertEqual(
            projected["distribution"],
            {(1, 1): 0.375, (0, 1): 0.0625, (0, 0): 0.5625},
        )

    def test_a_single_memory_node_gives_its_marginal(self) -> None:
        # P(C) = 0.25 + 0.0625 = 0.3125.
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(THREE_NODE),
            memory_nodes=("C",),
            probability_cutoff=0.0,
        )
        self.assertEqual(projected["distribution"], {(1,): 0.3125, (0,): 0.6875})

    def test_zero_probability_states_are_not_counted(self) -> None:
        row = {"A": 0.0, "A -- B": 0.75, "<nil>": 0.25}
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(row),
            memory_nodes=("A", "B"),
            probability_cutoff=0.0,
        )
        self.assertEqual(projected["distribution"], {(1, 1): 0.75, (0, 0): 0.25})
        self.assertEqual(projected["source_state_count"], 2)

    def test_state_labels_tolerate_surrounding_whitespace(self) -> None:
        row = {" A -- B ": 0.5, "<nil>": 0.5}
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(row),
            memory_nodes=("A", "B"),
            probability_cutoff=0.0,
        )
        self.assertEqual(projected["distribution"], {(1, 1): 0.5, (0, 0): 0.5})


class MassIsConserved(unittest.TestCase):
    def test_retained_and_dropped_mass_sum_to_one(self) -> None:
        for cutoff in (0.0, 0.0625, 0.4):
            with self.subTest(cutoff=cutoff):
                projected = project_joint_distribution(
                    last_states_probtraj=_last_states(THREE_NODE),
                    memory_nodes=("A", "B"),
                    probability_cutoff=cutoff,
                )
                self.assertTrue(
                    math.isclose(
                        math.fsum(projected["distribution"].values()),
                        1.0,
                        rel_tol=0.0,
                        abs_tol=1e-15,
                    )
                )
                self.assertTrue(
                    all(p > 0.0 for p in projected["distribution"].values())
                )


class CutoffAndRenormalisation(unittest.TestCase):
    """The cutoff is strict, applies to projected states, and is renormalised."""

    def test_a_state_exactly_at_the_cutoff_is_dropped(self) -> None:
        # (1,0) projects to exactly 1/16 and the cutoff is 1/16: `>` drops it.
        # Retained mass 15/16, so (1,1) = 0.375 / (15/16) = 2/5 and
        # (0,0) = 0.5625 / (15/16) = 3/5.
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(THREE_NODE),
            memory_nodes=("A", "B"),
            probability_cutoff=0.0625,
        )
        self.assertEqual(set(projected["distribution"]), {(1, 1), (0, 0)})
        self.assertAlmostEqual(projected["distribution"][(1, 1)], 2 / 5, places=15)
        self.assertAlmostEqual(projected["distribution"][(0, 0)], 3 / 5, places=15)
        self.assertEqual(projected["dropped_probability_mass"], 0.0625)
        self.assertEqual(projected["retained_state_count"], 2)
        self.assertTrue(projected["renormalized"])

    def test_a_state_just_above_the_cutoff_is_kept_unscaled(self) -> None:
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(THREE_NODE),
            memory_nodes=("A", "B"),
            probability_cutoff=0.0625 - 2**-20,
        )
        self.assertEqual(
            projected["distribution"],
            {(1, 1): 0.375, (1, 0): 0.0625, (0, 0): 0.5625},
        )
        self.assertFalse(projected["renormalized"])

    def test_the_cutoff_applies_to_projected_not_source_states(self) -> None:
        # "A -- B -- C" and "A -- B" are each below 0.3 but project together to
        # (1,1) = 0.375, which is above it. (1,0) = 0.0625 is dropped. Retained
        # 0.9375: (1,1) = 0.375 / 0.9375 = 2/5, (0,0) = 0.5625 / 0.9375 = 3/5.
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(THREE_NODE),
            memory_nodes=("A", "B"),
            probability_cutoff=0.3,
        )
        self.assertEqual(set(projected["distribution"]), {(1, 1), (0, 0)})
        self.assertAlmostEqual(projected["distribution"][(1, 1)], 2 / 5, places=15)
        self.assertAlmostEqual(projected["distribution"][(0, 0)], 3 / 5, places=15)

    def test_a_rare_state_survives_the_production_cutoff_unscaled(self) -> None:
        # The v0.6.0 protocols continue with probability_cutoff 1e-6
        # (config/protocols_markerless.yaml). A state carrying 2**-8 (about
        # 0.4 %) is far above it and must be kept as it is, with no rescaling
        # of anything else: the rare-state tail is part of the carried tissue.
        row = {"A": 2**-8, "A -- B": 0.5, "<nil>": 0.5 - 2**-8}
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(row),
            memory_nodes=("A", "B"),
            probability_cutoff=1e-6,
        )
        self.assertEqual(
            projected["distribution"],
            {(1, 0): 2**-8, (1, 1): 0.5, (0, 0): 0.5 - 2**-8},
        )
        self.assertEqual(projected["dropped_probability_mass"], 0.0)
        self.assertFalse(projected["renormalized"])

    def test_a_cutoff_that_keeps_nothing_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "retained no probability mass"):
            project_joint_distribution(
                last_states_probtraj=_last_states(THREE_NODE),
                memory_nodes=("A", "B"),
                probability_cutoff=0.6,
            )


class CorrelationIsPreserved(unittest.TestCase):
    """Joint continuation keeps the joint, not the product of the marginals."""

    def test_perfectly_correlated_support_stays_correlated(self) -> None:
        # P(A) = P(B) = 0.75 and P(A, B) = 0.75: the covariance is
        # 0.75 - 0.75 * 0.75 = 0.1875. A product of marginals would put
        # 0.1875 on each discordant state and 0.5625 on (1,1).
        row = {"A -- B": 0.75, "<nil>": 0.25}
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(row),
            memory_nodes=("A", "B"),
            probability_cutoff=0.0,
        )
        distribution = projected["distribution"]
        self.assertEqual(distribution, {(1, 1): 0.75, (0, 0): 0.25})
        p_a = sum(p for s, p in distribution.items() if s[0] == 1)
        p_b = sum(p for s, p in distribution.items() if s[1] == 1)
        self.assertEqual(distribution[(1, 1)] - p_a * p_b, 0.1875)

    def test_anticorrelated_support_stays_anticorrelated(self) -> None:
        row = {"A": 0.625, "B": 0.375}
        projected = project_joint_distribution(
            last_states_probtraj=_last_states(row),
            memory_nodes=("A", "B"),
            probability_cutoff=0.0,
        )
        self.assertEqual(projected["distribution"], {(1, 0): 0.625, (0, 1): 0.375})


class InvalidInputIsRefused(unittest.TestCase):
    def test_no_memory_nodes(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one memory node"):
            project_joint_distribution(
                last_states_probtraj=_last_states(THREE_NODE),
                memory_nodes=(),
                probability_cutoff=0.0,
            )

    def test_negative_cutoff(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-negative"):
            project_joint_distribution(
                last_states_probtraj=_last_states(THREE_NODE),
                memory_nodes=("A",),
                probability_cutoff=-1e-9,
            )

    def test_negative_or_non_finite_probability(self) -> None:
        for bad in (-0.125, float("nan"), float("inf")):
            with (
                self.subTest(bad=bad),
                self.assertRaisesRegex(ValueError, "invalid state probability"),
            ):
                project_joint_distribution(
                    last_states_probtraj=_last_states({"A": bad, "<nil>": 0.5}),
                    memory_nodes=("A",),
                    probability_cutoff=0.0,
                )


class _RecordingNetwork:
    """Stands in for a cMaBoSS network: records every istate assignment in order."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, object]] = []

    def set_istate(self, nodes, probability, warnings=False):
        self.calls.append((nodes, probability))


class InstallationOrder(unittest.TestCase):
    def test_the_distribution_is_installed_unchanged_on_the_memory_nodes(self) -> None:
        network = _RecordingNetwork()
        distribution = {(1, 1): 0.375, (1, 0): 0.0625, (0, 0): 0.5625}
        apply_joint_distribution(
            network=network, memory_nodes=("A", "B"), distribution=distribution
        )
        self.assertEqual(network.calls, [(["A", "B"], distribution)])

    def test_forced_nodes_are_applied_after_the_joint_state(self) -> None:
        # The runner pins a phase's declared inputs through `forced_nodes`, and
        # they must win over anything the carried distribution says.
        network = _RecordingNetwork()
        distribution = {(1,): 0.25, (0,): 0.75}
        apply_joint_distribution(
            network=network,
            memory_nodes=("A",),
            distribution=distribution,
            forced_nodes={"IN_X": True, "IN_Y": False},
        )
        self.assertEqual(
            network.calls,
            [(["A"], distribution), ("IN_X", [0.0, 1.0]), ("IN_Y", [1.0, 0.0])],
        )

    def test_an_empty_distribution_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty distribution"):
            apply_joint_distribution(
                network=_RecordingNetwork(), memory_nodes=("A",), distribution={}
            )


if __name__ == "__main__":
    unittest.main()
