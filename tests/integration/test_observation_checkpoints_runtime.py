"""U2b -- checkpoints read on a real trajectory, and what that run establishes.

The unit tests next to this one use synthetic frames, which is right for the
rules but cannot show that the abstraction fits the trajectory the repository
actually produces. This module runs the real maternal lineage
(``basal_maternal -> e2_primed_maternal -> hormone_treated_maternal``) on the
live v0.5 superset and reads the two declared checkpoints off it.

TWO RESULTS, AND THE DIFFERENCE BETWEEN THEM MATTERS.

``S_IGFBP1`` and ``S_PRL`` come back INDISTINGUISHABLE at every sampled time in
the phase. That is not a discovery: ``docs/prl_igfbp1_temporal_axis.md`` section
1 proves the two nodes are exchangeable by construction -- one Boolean function,
one initial state, one default rate -- so their onset distributions are
identical at every horizon and under every seed, and any gap in a run is node
ordering noise. The run corroborates the proof; it could never replace it.

What the run does establish, which the proof does not, is that this layer WOULD
SEE a difference if there were one. ``S_PGR`` against ``S_PRL`` -- a genuine
upstream/downstream pair on the same trajectory, same run, same band --
comes back PLACEMENT_DEPENDENT, meaning some sampled time shows a gap outside
the band. The aliased pair shows a gap outside the band at NO sampled time at
all. So ``INDISTINGUISHABLE`` is a statement about the model, not the
sensitivity floor of the method.

That the real pair is PLACEMENT_DEPENDENT rather than INVARIANT_GREATER is worth
stating rather than tuning away: this phase begins before the decidualization
cascade fires, so every upstream/downstream pair in it starts equal at zero and
separates later. A strict everywhere-ordering is therefore unattainable inside
this phase for ANY such pair -- which is the abstraction's own point, since it
means the answer to "does PGR lead PRL here?" depends on where one looks, and
without a calibrated time axis the repository cannot say where that is.

WHAT IT DOES NOT ESTABLISH. Nothing about whether the alias should be retired.
That question is blocked on measurement, not on observation machinery --
sections 3 to 5 of the same document -- and this unit deliberately leaves it
blocked. See ``docs/observation_checkpoints.md``.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.observations.checkpoints import (
    HORIZON_CONVERGED,
    HORIZON_DECLARED,
    INDISTINGUISHABLE,
    NO_RESOLVED_DECREASE,
    PLACEMENT_DEPENDENT,
    checkpoints_for_phase,
    executed_phase,
    load_checkpoints,
    monotonicity_verdict,
    ordering_verdict,
    paired_difference_tolerance,
    read_checkpoints,
)
from dt_adoc.simulation.timeline import build_sequential_timeline

MODEL_VERSION = "adoc-literature-superset-v0.5.0"
PHASE = "hormone_treated_maternal"
TRAJECTORIES = 2000
SEED = 1
#: The horizon the active constraints and diagnostics are read at
#: (`config/calibration.yaml` horizon_note, `CONVERGED_PHASE_HORIZON`), and the
#: one CHK-HTM-D6 declares. The declared-duration run below exists to show that
#: an endpoint reading off it is REFUSED, not to be read.
CONVERGED_HORIZON = 25.0


class CheckpointRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.timeline = build_sequential_timeline(
            model_version=MODEL_VERSION,
            terminal_protocol=PHASE,
            seed=SEED,
            trajectory_count=TRAJECTORIES,
            phase_horizon=CONVERGED_HORIZON,
        )
        cls.declared_timeline = build_sequential_timeline(
            model_version=MODEL_VERSION,
            terminal_protocol=PHASE,
            seed=SEED,
            trajectory_count=TRAJECTORIES,
        )
        cls.checkpoints = checkpoints_for_phase(load_checkpoints(ROOT), PHASE)
        cls.phase = executed_phase(cls.timeline, protocol_id=PHASE)
        cls.declared_phase = executed_phase(cls.declared_timeline, protocol_id=PHASE)
        cls.sampled_points = cls.phase.sampled_points
        # The verdict functions derive their own band from the multiplicity
        # each one actually tests, so nothing here chooses a tolerance. This
        # one is kept only to state the margin in a test below.
        cls.pointwise_band = paired_difference_tolerance(
            TRAJECTORIES, comparisons=cls.sampled_points
        )

    def test_the_lineage_executed_is_the_declared_one_with_no_extra_arm(self) -> None:
        """A checkpoint must not smuggle in a protocol. Count the arms that ran."""
        self.assertEqual(
            self.timeline.protocol_ids,
            ("basal_maternal", "e2_primed_maternal", "hormone_treated_maternal"),
        )
        self.assertEqual(len(self.timeline.phases), 3)

    def test_the_observed_phase_is_one_continuous_trajectory(self) -> None:
        """No reset: one phase index, one run from zero, monotone throughout."""
        frame = self.timeline.frame
        phase_rows = frame[frame["protocol_id"] == PHASE]
        self.assertEqual(sorted(phase_rows["phase_index"].unique()), [2])
        times = [float(value) for value in phase_rows["phase_local_time"]]
        self.assertEqual(times, sorted(times))
        self.assertAlmostEqual(times[0], 0.0)
        self.assertGreater(len(times), 10)

    def test_the_hours_are_never_converted_into_a_horizon(self) -> None:
        """The experiment is 96 h; the simulation is 4.0 declared or 25.0 run.

        If a physical-time calibration had crept in, an executed duration would
        track the hours, or the ratio 24 would appear as a factor. Neither
        number has anything to do with 96, and the two runs below differ from
        each other -- which is exactly why an endpoint must say which one it
        means.
        """
        converged = next(p for p in self.timeline.phases if p.protocol_id == PHASE)
        declared = next(
            p for p in self.declared_timeline.phases if p.protocol_id == PHASE
        )
        self.assertEqual(declared.declared_duration, 4.0)
        self.assertEqual(declared.relative_duration, 4.0)
        self.assertEqual(converged.declared_duration, 4.0)
        self.assertEqual(converged.relative_duration, CONVERGED_HORIZON)
        self.assertEqual({c.phase_duration_h for c in self.checkpoints}, {96.0})

    def test_the_two_horizons_really_do_end_in_different_states(self) -> None:
        """Why the endpoint policy is not bureaucracy.

        The declared duration is known not to reach the fixed point
        (`docs/endpoint_convergence_finding.md`), so reading `CHK-HTM-D6` off
        the wrong run would silently substitute a mid-transient value for a
        converged one.
        """
        ends = {}
        for label, timeline in (
            ("converged", self.timeline),
            ("declared", self.declared_timeline),
        ):
            rows = timeline.frame[timeline.frame["protocol_id"] == PHASE]
            rows = rows.sort_values("phase_local_time")
            ends[label] = float(rows["S_IGFBP1"].iloc[-1])
        self.assertAlmostEqual(ends["converged"], 1.0, places=3)
        self.assertLess(ends["declared"], 0.6)

    def test_the_execution_describes_itself(self) -> None:
        """Every number a verdict depends on is taken from the run, not given.

        The horizon is classified from what each run executed, and the model
        version, trajectory count and seed come from the timeline that produced
        the rows -- so no caller can narrow a band or relabel a horizon by
        saying something different beside the data.
        """
        for expected, phase in (
            (HORIZON_CONVERGED, self.phase),
            (HORIZON_DECLARED, self.declared_phase),
        ):
            with self.subTest(expected=expected):
                self.assertEqual(phase.horizon, expected)
                self.assertEqual(phase.model_version, MODEL_VERSION)
                self.assertEqual(phase.trajectory_count, TRAJECTORIES)
                self.assertEqual(phase.seed, SEED)
                self.assertEqual(phase.declared_duration, 4.0)

    def test_reading_the_endpoint_off_the_declared_run_is_refused(self) -> None:
        """A real declared-duration run cannot satisfy the converged endpoint.

        This is the regression for a defect the earlier design had: the caller
        used to supply the horizon as a string, so passing this very frame with
        `horizon=converged_fixed_point` was accepted and the endpoint policy
        protected nothing. There is no such argument now.
        """
        with self.assertRaises(ValueError) as caught:
            read_checkpoints(self.declared_phase, self.checkpoints)
        message = str(caught.exception)
        self.assertIn("CHK-HTM-D6", message)
        self.assertIn("MEASURED", message)

    def test_day_three_gets_no_simulated_value_from_the_real_run_either(
        self,
    ) -> None:
        """Not a gap to be filled: there is no position that means 24 h."""
        readings = read_checkpoints(self.phase, self.checkpoints)
        day3 = [r for r in readings if r.checkpoint_id == "CHK-HTM-D3"]
        self.assertEqual(len(day3), 2)
        for reading in day3:
            self.assertFalse(reading.is_placed)
            self.assertIsNone(reading.value)
            self.assertIsNone(reading.phase_local_time)
            # The phase-wide behaviour is still available, and needs no position.
            self.assertGreater(reading.phase_range, 0.0)

    def test_the_final_checkpoint_reads_the_end_of_the_converged_phase(self) -> None:
        """The one position no placement rule has to choose."""
        readings = read_checkpoints(self.phase, self.checkpoints)
        final = [r for r in readings if r.checkpoint_id == "CHK-HTM-D6"]
        self.assertEqual(len(final), 2)
        for reading in final:
            self.assertTrue(reading.is_placed)
            self.assertAlmostEqual(reading.value, reading.phase_max, places=6)
            self.assertEqual(reading.horizon, HORIZON_CONVERGED)

    def test_the_aliased_pair_is_indistinguishable_at_every_sampled_time(
        self,
    ) -> None:
        """Corroborates the structural proof; it does not stand in for it."""
        self.assertEqual(
            ordering_verdict(
                self.phase,
                node_a="S_IGFBP1",
                node_b="S_PRL",
            ),
            INDISTINGUISHABLE,
        )

    def test_the_verdict_is_not_living_on_the_edge_of_its_tolerance(self) -> None:
        """Margin, measured rather than assumed.

        A verdict that only just fits inside its band would flip between seeds
        and mean nothing. The observed gap is well under it: the two estimates
        share their trajectories and their driver, so the paired difference is
        far better behaved than any worst-case bound allows for. Seeds 1-5 were
        checked by hand at 2000 trajectories. The band is the
        correlation-agnostic paired Hoeffding bound, wider than the retired
        independent-sample one, so the margin is larger still -- about 0.015
        against 0.11 at the converged horizon.
        """
        frame = self.timeline.frame
        phase_rows = frame[frame["protocol_id"] == PHASE]
        gap = (phase_rows["S_IGFBP1"] - phase_rows["S_PRL"]).abs().max()
        self.assertLess(float(gap), self.pointwise_band / 2.0)

    def test_the_layer_does_see_a_real_difference_on_the_same_run(self) -> None:
        """The control that makes the verdict above worth reading.

        ``S_PGR`` drives ``S_DECIDUALIZED``, which drives ``S_PRL``, so the two
        genuinely differ inside this phase. Same trajectory, same tolerance, a
        different verdict: PLACEMENT_DEPENDENT says a gap outside the band
        exists somewhere, which is exactly what INDISTINGUISHABLE denies. If
        this ever returned INDISTINGUISHABLE the method would be blind and the
        alias result would mean nothing.
        """
        self.assertEqual(
            ordering_verdict(
                self.phase,
                node_a="S_PGR",
                node_b="S_PRL",
            ),
            PLACEMENT_DEPENDENT,
        )

    def test_no_pair_can_be_ordered_everywhere_inside_this_phase(self) -> None:
        """Why no verdict here is INVARIANT_GREATER, stated as a measurement.

        The phase starts from the E2-primed state, before the decidualization
        cascade fires, so the stromal outputs and their drivers are all at or
        near zero at phase-local time 0. Two series that coincide at the start
        cannot be separated at every sampled time by any tolerance, whatever
        happens later.
        """
        frame = self.timeline.frame
        phase_rows = frame[frame["protocol_id"] == PHASE].sort_values(
            "phase_local_time"
        )
        first = phase_rows.iloc[0]
        for node_id in ("S_DECIDUALIZED", "S_PRL", "S_IGFBP1"):
            self.assertAlmostEqual(float(first[node_id]), 0.0, places=6)
        for node_id in ("S_PGR", "S_PKA"):
            self.assertLess(float(first[node_id]), self.pointwise_band)

    def test_no_decrease_is_resolved_for_the_stromal_outputs(self) -> None:
        """A diagnostic, deliberately not a monotonicity proof.

        The band bounds the error of the estimate, so this says no decrease was
        resolved above Monte Carlo error -- not that the series never falls, and
        not a licence for an across-checkpoint ordering. None is needed: the
        interior checkpoint is unplaced.
        """
        for node_id in ("S_IGFBP1", "S_PRL", "S_DECIDUALIZED"):
            with self.subTest(node=node_id):
                self.assertEqual(
                    monotonicity_verdict(self.phase, node_id=node_id),
                    NO_RESOLVED_DECREASE,
                )


if __name__ == "__main__":
    unittest.main()
