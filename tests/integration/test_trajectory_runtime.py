"""Runtime contracts for full node-probability trajectory capture.

Bounded on purpose: a small trajectory count over the shortest protocols. The
point is the shape and consistency of the trajectory contract, not calibrated
biology.
"""

from __future__ import annotations

import math
import sys
import unittest
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.simulation.runner import run_protocol
from dt_adoc.simulation.timeline import build_sequential_timeline

MODEL_VERSION = "adoc-literature-v0.2.0"
TRAJECTORY_COUNT = 200
SEED = 1


class ConditionTrajectoryCaptureTest(unittest.TestCase):
    """The full trajectory must be captured without disturbing the final row."""

    @classmethod
    def setUpClass(cls) -> None:
        protocol_run = run_protocol(
            "basal_maternal",
            model_version=MODEL_VERSION,
            root=ROOT,
            seed=SEED,
            sample_count=TRAJECTORY_COUNT,
        )
        cls.result = protocol_run.final_result

    def test_trajectory_is_captured(self) -> None:
        self.assertIsNotNone(self.result.nodes_probtraj)

    def test_trajectory_has_more_than_one_time_row(self) -> None:
        self.assertGreater(len(self.result.nodes_probtraj), 1)

    def test_last_trajectory_row_agrees_with_last_nodes_probtraj(self) -> None:
        last_row = self.result.nodes_probtraj.iloc[-1]
        reference = self.result.last_nodes_probtraj.iloc[-1]
        for node_id, value in reference.to_dict().items():
            self.assertAlmostEqual(
                float(last_row[node_id]),
                float(value),
                places=12,
                msg=f"{node_id} diverges between full and final trajectory",
            )

    def test_last_trajectory_row_agrees_with_scalar_last(self) -> None:
        last_row = self.result.nodes_probtraj.iloc[-1]
        for node_id, value in self.result.last.items():
            self.assertAlmostEqual(float(last_row[node_id]), float(value), places=12)

    def test_all_probabilities_are_finite_and_bounded(self) -> None:
        for node_id in self.result.nodes_probtraj.columns:
            for value in self.result.nodes_probtraj[node_id]:
                numeric = float(value)
                self.assertTrue(math.isfinite(numeric), f"{node_id} is not finite")
                self.assertGreaterEqual(numeric, 0.0)
                self.assertLessEqual(numeric, 1.0)

    def test_input_nodes_are_absent_from_the_trajectory(self) -> None:
        """Inputs stay internal; their values are protocol settings, not output."""
        leaked = [
            node_id
            for node_id in self.result.nodes_probtraj.columns
            if str(node_id).startswith("IN_")
        ]
        self.assertEqual(leaked, [])

    def test_continuation_inputs_remain_available(self) -> None:
        """Joint continuation still depends on the final state distribution."""
        self.assertIsNotNone(self.result.last_states_probtraj)
        self.assertGreaterEqual(len(self.result.last_states_probtraj), 1)


class SequentialTimelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.timeline = build_sequential_timeline(
            model_version=MODEL_VERSION,
            root=ROOT,
            seed=SEED,
            trajectory_count=TRAJECTORY_COUNT,
        )

    def test_phases_follow_the_declared_lineage(self) -> None:
        self.assertEqual(
            [phase.protocol_id for phase in self.timeline.phases],
            list(self.timeline.protocol_ids),
        )

    def test_global_time_is_monotonic(self) -> None:
        times = self.timeline.frame["global_time"].tolist()
        for earlier, later in pairwise(times):
            self.assertLessEqual(earlier, later)

    def test_phase_boundaries_are_contiguous_and_recorded(self) -> None:
        previous_end = 0.0
        for phase in self.timeline.phases:
            self.assertAlmostEqual(phase.phase_start, previous_end, places=9)
            self.assertAlmostEqual(
                phase.phase_end,
                phase.phase_start + phase.relative_duration,
                places=9,
            )
            previous_end = phase.phase_end

    def test_phase_durations_match_the_protocol_definitions(self) -> None:
        for phase in self.timeline.phases:
            protocol = get_protocol(
                phase.protocol_id, ROOT, model_version=MODEL_VERSION
            )
            step = next(
                candidate
                for candidate in protocol.steps
                if candidate.step_id == phase.step_id
            )
            self.assertAlmostEqual(
                phase.relative_duration, float(step.relative_duration), places=9
            )

    def test_every_phase_after_the_first_receives_a_continuation(self) -> None:
        self.assertFalse(self.timeline.phases[0].continuation_applied)
        for phase in self.timeline.phases[1:]:
            self.assertTrue(
                phase.continuation_applied,
                f"{phase.protocol_id} did not receive a transferred state",
            )
            self.assertIsNotNone(phase.continuation_from)

    def test_frame_rows_cover_every_phase(self) -> None:
        seen = set(self.timeline.frame["phase_index"].tolist())
        self.assertEqual(seen, {phase.phase_index for phase in self.timeline.phases})

    def test_local_time_never_exceeds_the_phase_duration(self) -> None:
        for phase in self.timeline.phases:
            rows = self.timeline.frame[
                self.timeline.frame["phase_index"] == phase.phase_index
            ]
            self.assertLess(float(rows["phase_local_time"].max()), phase.phase_end)
            self.assertGreaterEqual(float(rows["phase_local_time"].min()), 0.0)

    def test_global_time_equals_phase_start_plus_local_time(self) -> None:
        frame = self.timeline.frame
        for _, row in frame.iterrows():
            self.assertAlmostEqual(
                float(row["global_time"]),
                float(row["phase_start"]) + float(row["phase_local_time"]),
                places=9,
            )

    def test_input_traces_are_deterministic_zero_or_one(self) -> None:
        for input_id in self.timeline.input_ids:
            values = set(self.timeline.frame[input_id].tolist())
            self.assertTrue(
                values <= {0.0, 1.0},
                f"{input_id} carries non-deterministic values {values}",
            )

    def test_input_traces_match_the_protocol_definitions(self) -> None:
        for phase in self.timeline.phases:
            rows = self.timeline.frame[
                self.timeline.frame["phase_index"] == phase.phase_index
            ]
            for input_id, state in phase.input_states.items():
                expected = 1.0 if state else 0.0
                self.assertEqual(
                    set(rows[input_id].tolist()),
                    {expected},
                    f"{input_id} in {phase.protocol_id} should be {expected}",
                )

    def test_e2_switches_on_at_priming_and_stays_on(self) -> None:
        frame = self.timeline.frame
        basal = frame[frame["phase_index"] == 0]["IN_E2"]
        later = frame[frame["phase_index"] > 0]["IN_E2"]
        self.assertEqual(set(basal.tolist()), {0.0})
        self.assertEqual(set(later.tolist()), {1.0})

    def test_metadata_records_model_seed_and_trajectory_count(self) -> None:
        self.assertEqual(self.timeline.model_version, MODEL_VERSION)
        self.assertEqual(self.timeline.seed, SEED)
        self.assertEqual(self.timeline.trajectory_count, TRAJECTORY_COUNT)
        self.assertTrue(self.timeline.model_id)

    def test_node_and_input_columns_are_disjoint(self) -> None:
        self.assertEqual(
            set(self.timeline.node_ids) & set(self.timeline.input_ids), set()
        )
        self.assertTrue(self.timeline.node_ids)
        self.assertTrue(self.timeline.input_ids)

    def test_phase_at_resolves_the_active_phase(self) -> None:
        for phase in self.timeline.phases:
            midpoint = (phase.phase_start + phase.phase_end) / 2.0
            self.assertEqual(
                self.timeline.phase_at(midpoint).phase_index, phase.phase_index
            )

    def test_building_the_timeline_is_reproducible_under_a_fixed_seed(self) -> None:
        repeat = build_sequential_timeline(
            model_version=MODEL_VERSION,
            root=ROOT,
            seed=SEED,
            trajectory_count=TRAJECTORY_COUNT,
        )
        for node_id in self.timeline.node_ids:
            self.assertEqual(
                self.timeline.frame[node_id].tolist(),
                repeat.frame[node_id].tolist(),
                f"{node_id} is not reproducible under seed {SEED}",
            )


class CoreModelTimelineTest(unittest.TestCase):
    """The baseline model must build a timeline too, not just the literature one."""

    def test_core_model_builds_a_six_phase_timeline(self) -> None:
        timeline = build_sequential_timeline(
            model_version="adoc-core-v0.1.0",
            root=ROOT,
            seed=SEED,
            trajectory_count=TRAJECTORY_COUNT,
        )
        self.assertEqual(len(timeline.phases), 6)
        self.assertGreater(len(timeline.frame), len(timeline.phases))
        self.assertTrue(timeline.node_ids)


if __name__ == "__main__":
    unittest.main()
