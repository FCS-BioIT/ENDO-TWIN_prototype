from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.calibration.objectives import (
    AdhesionReadout,
    summarize_adhesion_log_likelihoods,
)
from dt_adoc.simulation.sensitivity import (
    build_bounded_sensitivity_matrix,
    validate_sensitivity_matrix_completeness,
)


class Phase1CAnalysisRuntimeIntegrationTest(unittest.TestCase):
    def test_live_calibration_config_preserves_calibration_validation_split(
        self,
    ) -> None:
        payload = yaml.safe_load((ROOT / "config" / "calibration.yaml").read_text())
        probabilities = {
            "adhesion_challenge_basal": 0.05,
            "adhesion_challenge_hormone_treated": 0.45,
            "adhesion_challenge_hormone_treated_mifepristone": 0.10,
        }
        readouts = [
            AdhesionReadout(
                probability=probabilities[row["protocol_id"]],
                successes=int(row["successes"]),
                trials=int(row["trials"]),
                role=str(row["role"]),
            )
            for row in payload["adhesion_objective"]["readouts"]
        ]

        summary = summarize_adhesion_log_likelihoods(readouts)

        self.assertEqual(summary.calibration_readout_count, 2)
        self.assertEqual(summary.validation_readout_count, 1)
        self.assertLess(summary.total_log_likelihood, 0.0)

    def test_live_runtime_bounded_sensitivity_matrix_is_complete(self) -> None:
        model_versions = ("adoc-core-v0.1.0", "adoc-literature-v0.2.0")
        continuation_modes = ("joint", "marginal")
        memory_policies_by_model = {
            "adoc-core-v0.1.0": ("all_non_inputs",),
            "adoc-literature-v0.2.0": (
                "minimal_stable_joint",
                "marginal_comparator",
            ),
        }
        rule_variants_by_model = {
            "adoc-literature-v0.2.0": {
                "mifepristone": (
                    "pgr_only_inhibition",
                    "pgr_plus_direct_interface_inhibition",
                ),
            }
        }

        matrix = build_bounded_sensitivity_matrix(
            model_versions=model_versions,
            continuation_modes=continuation_modes,
            memory_policies_by_model=memory_policies_by_model,
            rule_variants_by_model=rule_variants_by_model,
            root=ROOT,
        )
        validate_sensitivity_matrix_completeness(
            matrix,
            model_versions=model_versions,
            continuation_modes=continuation_modes,
            memory_policies_by_model=memory_policies_by_model,
            rule_variants_by_model=rule_variants_by_model,
            root=ROOT,
        )

        self.assertEqual(len(matrix), 10)
        self.assertEqual(len({row.scenario_id for row in matrix}), len(matrix))
        self.assertEqual(matrix[0].model_version, "adoc-core-v0.1.0")
        self.assertEqual(matrix[-1].model_version, "adoc-literature-v0.2.0")

    def test_completeness_check_detects_missing_live_runtime_row(self) -> None:
        model_versions = ("adoc-literature-v0.2.0",)
        continuation_modes = ("joint",)
        memory_policies_by_model = {
            "adoc-literature-v0.2.0": ("minimal_stable_joint",),
        }
        rule_variants_by_model = {
            "adoc-literature-v0.2.0": {
                "mifepristone": (
                    "pgr_only_inhibition",
                    "pgr_plus_direct_interface_inhibition",
                ),
            }
        }

        matrix = build_bounded_sensitivity_matrix(
            model_versions=model_versions,
            continuation_modes=continuation_modes,
            memory_policies_by_model=memory_policies_by_model,
            rule_variants_by_model=rule_variants_by_model,
            root=ROOT,
        )

        with self.assertRaisesRegex(ValueError, "missing="):
            validate_sensitivity_matrix_completeness(
                matrix[:-1],
                model_versions=model_versions,
                continuation_modes=continuation_modes,
                memory_policies_by_model=memory_policies_by_model,
                rule_variants_by_model=rule_variants_by_model,
                root=ROOT,
            )


if __name__ == "__main__":
    unittest.main()
