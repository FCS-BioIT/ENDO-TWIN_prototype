from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.calibration.adhesion_likelihood import (
    binomial_deviance,
    binomial_log_likelihood,
)
from dt_adoc.personalization.soft_nv import (
    SoftMappingConfig,
    score_to_initial_probability,
    score_to_rate_modifiers,
)
from dt_adoc.personalization.strict_nv import decide_strict_variant
from dt_adoc.perturbations.combinations import pair_scenarios
from dt_adoc.perturbations.single import single_scenarios
from dt_adoc.perturbations.synergy import (
    bliss_independence,
    highest_single_agent,
)
from dt_adoc.perturbations.target_engagement import build_target_engagement_grid
from dt_adoc.scoring.candidates import CandidateScore, pareto_front
from dt_adoc.simulation.sensitivity import sensitivity_matrix
from dt_adoc.simulation.stability import effect_mean, stable_within


class StrictVariantTest(unittest.TestCase):
    def test_missing_value_cannot_clamp(self) -> None:
        decision = decide_strict_variant(
            has_constitutive_evidence=True,
            measurement_state="missing",
            desired_state=1,
        )
        self.assertIsNone(decision.clamp)

    def test_constitutive_evidence_allows_clamp(self) -> None:
        decision = decide_strict_variant(
            has_constitutive_evidence=True,
            measurement_state="observed",
            desired_state=0,
        )
        self.assertEqual(decision.clamp, 0)


class SoftVariantTest(unittest.TestCase):
    def test_initial_probability_clips(self) -> None:
        self.assertEqual(score_to_initial_probability(-1.0), 0.0)
        self.assertEqual(score_to_initial_probability(2.0), 1.0)

    def test_rate_modifiers_are_monotonic(self) -> None:
        config = SoftMappingConfig(alpha=1.5)
        low = score_to_rate_modifiers(0.2, config)
        high = score_to_rate_modifiers(0.8, config)
        self.assertLess(low[0], high[0])
        self.assertGreater(low[1], high[1])


class PerturbationTest(unittest.TestCase):
    def test_target_grid_validates(self) -> None:
        self.assertEqual(build_target_engagement_grid([1.0, 0.0, 0.4]), [0.0, 0.4, 1.0])

    def test_single_and_pair_counts(self) -> None:
        levels = [0.0, 0.5, 1.0]
        self.assertEqual(len(single_scenarios("A", levels, mode="inhibit")), 3)
        self.assertEqual(len(pair_scenarios("A", "B", levels, mode="inhibit")), 9)

    def test_synergy_helpers(self) -> None:
        bliss = bliss_independence(
            baseline=0.9,
            single_a=0.7,
            single_b=0.6,
            double_ab=0.3,
            direction="decrease",
        )
        hsa = highest_single_agent(
            baseline=0.9,
            single_a=0.7,
            single_b=0.6,
            double_ab=0.3,
            direction="decrease",
        )
        self.assertTrue(math.isfinite(bliss))
        self.assertGreater(hsa, 0.0)


class CalibrationTest(unittest.TestCase):
    def test_binomial_likelihood(self) -> None:
        value = binomial_log_likelihood(probability=0.5, successes=1, trials=2)
        self.assertAlmostEqual(value, math.log(0.5) * 2)

    def test_binomial_deviance_nonnegative(self) -> None:
        self.assertGreaterEqual(
            binomial_deviance(probability=0.5, successes=1, trials=2),
            0.0,
        )


class CandidateScoreTest(unittest.TestCase):
    def test_pareto_front(self) -> None:
        scores = [
            CandidateScore("a", reward=0.9, penalty=0.1, instability=0.1),
            CandidateScore("b", reward=0.8, penalty=0.2, instability=0.2),
            CandidateScore("c", reward=0.7, penalty=0.1, instability=0.1),
        ]
        front_ids = {score.candidate_id for score in pareto_front(scores)}
        self.assertIn("a", front_ids)
        self.assertNotIn("b", front_ids)


class SimulationHelpersTest(unittest.TestCase):
    def test_stability_helpers(self) -> None:
        values = [0.1, 0.12, 0.11]
        self.assertTrue(stable_within(values, tolerance=0.05))
        self.assertAlmostEqual(effect_mean(values), 0.11)

    def test_sensitivity_matrix(self) -> None:
        matrix = sensitivity_matrix({"a": [1, 2], "b": ["x", "y"]})
        self.assertEqual(len(matrix), 4)


if __name__ == "__main__":
    unittest.main()
