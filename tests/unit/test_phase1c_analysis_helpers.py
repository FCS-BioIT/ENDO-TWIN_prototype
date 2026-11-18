from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.calibration.objectives import (
    AdhesionReadout,
    summarize_adhesion_log_likelihoods,
    summed_adhesion_log_likelihood,
)
from dt_adoc.calibration.search import Scenario, retain_acceptable_scenarios
from dt_adoc.simulation.sensitivity import (
    build_baseline_vs_literature_comparison_rows,
)
from dt_adoc.simulation.stability import (
    FullSequenceStabilityRecord,
    summarize_full_sequence_stability,
)


class CalibrationLeakagePreventionTest(unittest.TestCase):
    def test_validation_role_is_excluded_from_calibration_objective(self) -> None:
        readouts = [
            AdhesionReadout(
                probability=0.1,
                successes=0,
                trials=12,
                role="calibration",
            ),
            AdhesionReadout(
                probability=0.45,
                successes=9,
                trials=19,
                role="calibration",
            ),
            AdhesionReadout(
                probability=0.3,
                successes=1,
                trials=8,
                role="validation_if_held_out",
            ),
        ]

        summary = summarize_adhesion_log_likelihoods(readouts)

        expected_validation = math.log(0.3) + 7 * math.log(0.7)
        self.assertEqual(summary.calibration_readout_count, 2)
        self.assertEqual(summary.validation_readout_count, 1)
        self.assertEqual(summary.descriptive_readout_count, 3)
        self.assertAlmostEqual(
            summary.total_log_likelihood,
            summary.calibration_log_likelihood + expected_validation,
        )
        self.assertAlmostEqual(
            summed_adhesion_log_likelihood(readouts),
            summary.calibration_log_likelihood,
        )
        self.assertAlmostEqual(
            summary.validation_log_likelihood,
            expected_validation,
        )


class BoundedRetentionTest(unittest.TestCase):
    def test_retention_uses_deterministic_ties_and_maximum_bound(self) -> None:
        scenarios = [
            Scenario("beta", {"score": 0.9, "tie_rank": 2}),
            Scenario("alpha", {"score": 0.9, "tie_rank": 1}),
            Scenario("gamma", {"score": 0.8, "tie_rank": 3}),
        ]

        retained = retain_acceptable_scenarios(
            scenarios,
            score_key="score",
            minimum_score=0.8,
            min_scenarios=1,
            max_scenarios=2,
            tie_break_keys=("tie_rank",),
        )

        self.assertEqual(
            [scenario.scenario_id for scenario in retained.retained],
            ["alpha", "beta"],
        )
        self.assertEqual(retained.acceptable_scenarios, 3)
        self.assertTrue(retained.truncated_to_maximum)
        self.assertFalse(retained.used_minimum_fallback)

    def test_retention_falls_back_to_minimum_when_no_scenario_is_acceptable(
        self,
    ) -> None:
        scenarios = [
            Scenario("b", {"score": 0.3}),
            Scenario("a", {"score": 0.4}),
        ]

        retained = retain_acceptable_scenarios(
            scenarios,
            score_key="score",
            minimum_score=0.9,
            min_scenarios=1,
            max_scenarios=1,
        )

        self.assertEqual(
            [scenario.scenario_id for scenario in retained.retained], ["a"]
        )
        self.assertEqual(retained.acceptable_scenarios, 0)
        self.assertTrue(retained.used_minimum_fallback)


class FullSequenceStabilitySummaryTest(unittest.TestCase):
    def test_summary_requires_matched_upstream_seed_and_two_trajectory_counts(
        self,
    ) -> None:
        records = [
            FullSequenceStabilityRecord(
                sequence_id="adhesion_challenge_hormone_treated",
                trajectory_count=200,
                seed=1,
                maternal_seed=1,
                phenotype_values={"OUT_STABLE_ADHESION": 0.40},
            ),
            FullSequenceStabilityRecord(
                sequence_id="adhesion_challenge_hormone_treated",
                trajectory_count=200,
                seed=2,
                maternal_seed=2,
                phenotype_values={"OUT_STABLE_ADHESION": 0.44},
            ),
            FullSequenceStabilityRecord(
                sequence_id="adhesion_challenge_hormone_treated",
                trajectory_count=500,
                seed=1,
                maternal_seed=1,
                phenotype_values={"OUT_STABLE_ADHESION": 0.41},
            ),
            FullSequenceStabilityRecord(
                sequence_id="adhesion_challenge_hormone_treated",
                trajectory_count=500,
                seed=2,
                maternal_seed=2,
                phenotype_values={"OUT_STABLE_ADHESION": 0.43},
            ),
        ]

        rows = summarize_full_sequence_stability(records)

        self.assertEqual(len(rows), 2)
        row_200 = rows[0]
        row_500 = rows[1]
        self.assertEqual(row_200["trajectory_count"], 200)
        self.assertEqual(row_200["seed_count"], 2)
        self.assertEqual(row_200["seeds"], "1,2")
        self.assertAlmostEqual(row_200["mean_probability"], 0.42)
        self.assertAlmostEqual(row_200["span"], 0.04)
        self.assertEqual(row_500["trajectory_count"], 500)
        self.assertAlmostEqual(row_500["mean_probability"], 0.42)
        self.assertAlmostEqual(row_500["span"], 0.02)

    def test_summary_rejects_reused_upstream_maternal_state(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "maternal_seed must match seed",
        ):
            summarize_full_sequence_stability(
                [
                    FullSequenceStabilityRecord(
                        sequence_id="adhesion_challenge_hormone_treated",
                        trajectory_count=200,
                        seed=1,
                        maternal_seed=1,
                        phenotype_values={"OUT_STABLE_ADHESION": 0.40},
                    ),
                    FullSequenceStabilityRecord(
                        sequence_id="adhesion_challenge_hormone_treated",
                        trajectory_count=200,
                        seed=2,
                        maternal_seed=1,
                        phenotype_values={"OUT_STABLE_ADHESION": 0.42},
                    ),
                    FullSequenceStabilityRecord(
                        sequence_id="adhesion_challenge_hormone_treated",
                        trajectory_count=500,
                        seed=1,
                        maternal_seed=1,
                        phenotype_values={"OUT_STABLE_ADHESION": 0.41},
                    ),
                    FullSequenceStabilityRecord(
                        sequence_id="adhesion_challenge_hormone_treated",
                        trajectory_count=500,
                        seed=2,
                        maternal_seed=2,
                        phenotype_values={"OUT_STABLE_ADHESION": 0.43},
                    ),
                ]
            )


class ComparisonSchemaTest(unittest.TestCase):
    def test_baseline_vs_literature_rows_include_required_fields(self) -> None:
        rows = build_baseline_vs_literature_comparison_rows(
            baseline_results={
                "adhesion_challenge_hormone_treated": {
                    "OUT_STABLE_ADHESION": 0.41,
                }
            },
            literature_results={
                "adhesion_challenge_hormone_treated": {
                    "OUT_STABLE_ADHESION": 0.52,
                }
            },
            protocol_pairs={
                "ht_challenge": (
                    "adhesion_challenge_hormone_treated",
                    "adhesion_challenge_hormone_treated",
                )
            },
            phenotype_ids=("OUT_STABLE_ADHESION",),
            protocol_roles={"ht_challenge": "calibration"},
            root=ROOT,
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["comparison_id"], "ht_challenge")
        self.assertEqual(row["role"], "calibration")
        self.assertEqual(row["comparison_kind"], "baseline_vs_literature")
        self.assertAlmostEqual(row["baseline_probability"], 0.41)
        self.assertAlmostEqual(row["literature_probability"], 0.52)
        self.assertAlmostEqual(row["literature_minus_baseline"], 0.11)
        self.assertAlmostEqual(row["absolute_delta"], 0.11)


if __name__ == "__main__":
    unittest.main()
