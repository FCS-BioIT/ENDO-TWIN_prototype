"""The structural-contradiction state, and that it keeps clipped scores out of ranking.

Added with the 2026-09-16 demotion of `adhesion_objective` from magnitude-fitted
objective to ordinal/diagnostic readout. The point of the state is that clipping
is sound for a *small* probability and unsound for a *structurally zero* one, so
these tests fix the boundary between those two cases.
"""

from __future__ import annotations

import math
import unittest

import yaml

from dt_adoc.calibration.adhesion_likelihood import (
    CLIP_EPSILON,
    CONSISTENT,
    STRUCTURALLY_CONTRADICTED,
    STRUCTURALLY_SATURATED,
    binomial_log_likelihood,
    is_rankable,
    structural_verdict,
)
from dt_adoc.calibration.objectives import (
    AdhesionReadout,
    rankable_readouts,
    summarize_adhesion_log_likelihoods,
)
from dt_adoc.reporting.identifiability import repo_root


class StructuralVerdictTest(unittest.TestCase):
    def test_zero_probability_with_a_success_is_contradicted(self) -> None:
        self.assertEqual(
            structural_verdict(probability=0.0, successes=1, trials=8),
            STRUCTURALLY_CONTRADICTED,
        )

    def test_zero_probability_with_no_successes_is_consistent(self) -> None:
        """The basal arm: the model says impossible and nothing happened."""
        self.assertEqual(
            structural_verdict(probability=0.0, successes=0, trials=12), CONSISTENT
        )

    def test_one_probability_with_a_failure_is_saturated(self) -> None:
        self.assertEqual(
            structural_verdict(probability=1.0, successes=7, trials=8),
            STRUCTURALLY_SATURATED,
        )

    def test_a_merely_small_probability_is_not_contradicted(self) -> None:
        """The distinction the whole state exists to draw."""
        self.assertEqual(
            structural_verdict(probability=1e-12, successes=1, trials=8), CONSISTENT
        )
        self.assertTrue(is_rankable(probability=1e-12, successes=1, trials=8))

    def test_contradicted_arms_are_not_rankable(self) -> None:
        self.assertFalse(is_rankable(probability=0.0, successes=1, trials=8))

    def test_invalid_counts_still_raise(self) -> None:
        with self.assertRaises(ValueError):
            structural_verdict(probability=0.5, successes=9, trials=8)


class WhyContradictedScoresCannotRankTest(unittest.TestCase):
    """The score is a function of the clip constant, not of the model."""

    def test_the_score_of_a_contradicted_arm_is_successes_times_log_epsilon(
        self,
    ) -> None:
        value = binomial_log_likelihood(probability=0.0, successes=1, trials=8)
        self.assertAlmostEqual(value, math.log(CLIP_EPSILON), places=6)

    def test_every_candidate_gets_the_identical_score(self) -> None:
        """Two different models, both structurally zero, score the same."""
        scores = {
            binomial_log_likelihood(probability=0.0, successes=1, trials=8)
            for _ in range(2)
        }
        self.assertEqual(len(scores), 1)


class SummaryReportsContradictionTest(unittest.TestCase):
    ARMS = (
        AdhesionReadout(probability=0.0, successes=0, trials=12, role="calibration"),
        AdhesionReadout(probability=0.82, successes=9, trials=19, role="calibration"),
        AdhesionReadout(
            probability=0.0, successes=1, trials=8, role="validation_if_held_out"
        ),
    )

    def test_the_mifepristone_arm_is_counted(self) -> None:
        summary = summarize_adhesion_log_likelihoods(self.ARMS)
        self.assertEqual(summary.structurally_contradicted_count, 1)
        self.assertTrue(summary.contains_unrankable_readouts)

    def test_rankable_readouts_drops_exactly_that_arm(self) -> None:
        kept = rankable_readouts(self.ARMS)
        self.assertEqual(len(kept), 2)
        self.assertNotIn(self.ARMS[2], kept)

    def test_a_fully_consistent_set_is_not_flagged(self) -> None:
        summary = summarize_adhesion_log_likelihoods(self.ARMS[:2])
        self.assertEqual(summary.structurally_contradicted_count, 0)
        self.assertFalse(summary.contains_unrankable_readouts)


class DemotionIsDeclaredTest(unittest.TestCase):
    """`config/calibration.yaml` must keep saying adhesion is not fitted.

    If someone re-promotes it, this fails rather than the change passing
    silently -- which is the whole reason the demotion was recorded as a
    SEMANTIC_OR_PROTOCOL repair.
    """

    @classmethod
    def setUpClass(cls) -> None:
        payload = yaml.safe_load(
            (repo_root() / "config" / "calibration.yaml").read_text()
        )
        cls.objective = payload["adhesion_objective"]

    def test_the_objective_is_declared_diagnostic_and_not_fitted(self) -> None:
        self.assertEqual(self.objective["role"], "diagnostic_ordinal")
        self.assertIs(self.objective["magnitude_fitted"], False)

    def test_no_replacement_scalar_objective_was_manufactured(self) -> None:
        self.assertIn("no_replacement_objective", self.objective)
        self.assertIn("NO quantitative", self.objective["no_replacement_objective"])

    def test_the_ordinal_claim_is_retained(self) -> None:
        claim = self.objective["retained_ordinal_claim"]
        self.assertEqual(
            claim["statement"],
            "untreated < hormone_treated > hormone_treated_mifepristone",
        )

    def test_the_structural_contradiction_policy_is_recorded(self) -> None:
        policy = self.objective["structural_contradiction_policy"]
        self.assertIn("UNCLIPPED", policy)
        self.assertIn("NO MATERNAL RULE IS ALTERED", policy)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class NoFittingLoopEverConsumedThisTest(unittest.TestCase):
    """The demotion removed an aspiration, not a working fitting loop.

    Asserted rather than claimed, because `docs/gate3_scope_adjudication.md`
    §3a says so and that is exactly the kind of statement that rots. If someone
    later wires a real ranking loop, this fails and the document must be
    revised instead of quietly becoming false.
    """

    def test_no_source_module_ranks_scenarios(self) -> None:
        offenders = []
        for path in (repo_root() / "src").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            ranks = "rank_scenarios" in text or "retain_acceptable_scenarios" in text
            if ranks and path.name != "search.py":
                offenders.append(str(path))
        self.assertEqual(
            offenders,
            [],
            "something in src/ now ranks scenarios; §3a says nothing does, and "
            "a ranking loop would need a declared objective that no longer exists",
        )

    def test_the_runner_takes_the_first_scenario_unconditionally(self) -> None:
        text = (repo_root() / "src/dt_adoc/simulation/runner.py").read_text()
        self.assertIn('load_parameter_scenarios(root)["scenarios"][0]', text)

    def test_relay_initial_states_is_still_read_by_nothing(self) -> None:
        """The dead-configuration finding in §3a, pinned so it cannot silently change.

        If a future change starts consuming it, this fails -- which is the
        right outcome, because the document records it as inert and the
        istates that actually run come from baseline.cfg.
        """
        readers = [
            str(path)
            for path in (repo_root() / "src").rglob("*.py")
            if "relay_initial_states" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(readers, [])
