"""U2b -- a checkpoint observes a phase; it never becomes one.

The unit these tests belong to added within-phase observation checkpoints so the
day-3 IGFBP-1 and PRL measurements can be positioned on the full-cocktail
trajectory the model already runs. Four things must stay true, and each is a
thing the repository has been told not to do:

1. no checkpoint creates or implies a protocol arm;
2. no checkpoint resets, restarts or re-runs a trajectory;
3. no checkpoint converts an experimental hour into a simulation time --
   ``config/calibration.yaml`` records ``calibrated_physical_time: false``;
4. the placement of a checkpoint is fixed by experimental timing and its order,
   never by a molecular value read afterwards.

TWO PLACEMENT RULES WERE TRIED AND BOTH ARE REJECTED, and the tests below hold
each rejection in place. *Proportional* placement asserts a fixed
hours-per-relative-time factor. *Ordinal rank* -- the k-th of n at ``k/n`` of
the phase -- avoids the hours but is unstable under extension: declaring 48 h
and 72 h would move the day-3 reading from ``1/2`` of the trajectory to ``1/4``,
changing an unchanged observation because a different one was declared. So an
interior checkpoint has NO simulation time and NO value, and
``test_declaring_future_checkpoints_cannot_move_an_existing_one`` is the
regression that keeps it that way.

The one readable position is the phase end, and even that is read under an
explicitly declared horizon: this repository executes the same phase at its
declared duration and at the converged fixed point, and the two end in
different states.
"""

from __future__ import annotations

import csv
import dataclasses
import inspect
import re
import sys
import unittest
from dataclasses import replace
from itertools import pairwise
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.observations.checkpoints import (
    CHECKPOINT_COLUMNS,
    COMPARISON_ENDPOINT_VALUE,
    COMPARISON_PHASE_WIDE_CHANGE,
    COMPARISON_PHASE_WIDE_SIGN,
    ENDPOINT_COMPARISONS,
    HORIZON_CONVERGED,
    HORIZON_DECLARED,
    HORIZON_NOT_APPLICABLE,
    INDISTINGUISHABLE,
    INVARIANT_GREATER,
    INVARIANT_LESS,
    NO_RESOLVED_DECREASE,
    NO_RESOLVED_INCREASE,
    PLACEMENT_DEPENDENT,
    PLACEMENT_ORDINAL_RANK,
    PLACEMENT_PHASE_END,
    PLACEMENT_PROPORTIONAL,
    PLACEMENT_UNPLACED,
    RESOLVED_BOTH_DIRECTIONS,
    Checkpoint,
    ExecutedPhase,
    checkpoints_for_phase,
    load_checkpoints,
    monotonicity_verdict,
    ordering_verdict,
    paired_difference_tolerance,
    read_checkpoints,
    validate_checkpoints,
)

CHECKPOINT_TSV = ROOT / "config" / "observation_checkpoints.tsv"
PROTOCOLS = ROOT / "config" / "protocols.yaml"
CALIBRATION = ROOT / "config" / "calibration.yaml"

PHASE = "hormone_treated_maternal"
MODEL_VERSION = "adoc-literature-superset-v0.5.0"
#: The phase's declared relative duration and the converged horizon. A
#: synthetic frame has to state which of the two it represents, because
#: `executed_phase` measures that rather than believing a caller.
DECLARED_EXTENT = 4.0
CONVERGED_EXTENT = 25.0
#: Trajectory count the synthetic verdict tests reason about.
TRAJECTORY_COUNT = 2000


def _protocol_steps() -> set[tuple[str, str]]:
    payload = yaml.safe_load(PROTOCOLS.read_text(encoding="utf-8"))
    return {
        (protocol["protocol_id"], step["step_id"])
        for protocol in payload["protocols"]
        for step in protocol["steps"]
    }


def _frame(
    times: list[float],
    columns: dict[str, list[float]],
    *,
    executed: float = CONVERGED_EXTENT,
) -> object:
    """A minimal executed-phase frame, in the shape the timeline emits."""
    import pandas as pd

    data = {
        "phase_local_time": times,
        "protocol_id": [PHASE] * len(times),
        "step_id": [PHASE] * len(times),
        "phase_index": [2] * len(times),
        "phase_start": [3.0] * len(times),
        "phase_end": [3.0 + executed] * len(times),
    }
    data.update(columns)
    return pd.DataFrame(data)


def _phase(
    times: list[float],
    columns: dict[str, list[float]],
    *,
    executed: float = CONVERGED_EXTENT,
    trajectory_count: int = TRAJECTORY_COUNT,
    model_version: str = MODEL_VERSION,
    horizon: str = HORIZON_CONVERGED,
) -> ExecutedPhase:
    """A synthetic ``ExecutedPhase``.

    Constructing one directly is legitimate HERE and nowhere else: a test has
    to be able to state the execution it is reasoning about. Production callers
    build one with :func:`executed_phase` from a real timeline, which is what
    stops them asserting a trajectory count or a model version the data does
    not have.
    """
    return ExecutedPhase(
        protocol_id=PHASE,
        step_id=PHASE,
        model_version=model_version,
        trajectory_count=trajectory_count,
        seed=1,
        horizon=horizon,
        declared_duration=DECLARED_EXTENT,
        executed_duration=executed,
        rows=_frame(times, columns, executed=executed),
    )


def _synthetic_checkpoints(hours: list[float], *, phase_h: float = 96.0):
    """The shape the committed table has: interior positions plus one end."""
    return [
        Checkpoint(
            checkpoint_id=f"CHK-T{int(hour)}",
            phase_protocol_id=PHASE,
            phase_step_id=PHASE,
            applies_to_model_versions=("adoc-literature-superset-v0.5.0",),
            experimental_label=f"{hour} h",
            source_condition_id="COND-FULL-COCKTAIL",
            hours_after_phase_start=hour,
            phase_duration_h=phase_h,
            experimental_phase_fraction=hour / phase_h,
            ordinal_index=index,
            ordinal_count=len(hours),
            placement_semantics=(
                PLACEMENT_PHASE_END if hour == phase_h else PLACEMENT_UNPLACED
            ),
            endpoint_horizon_policy=(
                HORIZON_CONVERGED if hour == phase_h else HORIZON_NOT_APPLICABLE
            ),
            model_nodes=("S_IGFBP1", "S_PRL"),
            observation_rows=("OM-016",),
            licensed_comparisons=(
                (COMPARISON_ENDPOINT_VALUE,) if hour == phase_h else ()
            )
            + (COMPARISON_PHASE_WIDE_SIGN,),
            forbidden_uses=("physical_time_calibration",),
            evidence_ids=("SOFIA-COMM-004",),
            raw={},
        )
        for index, hour in enumerate(hours, start=1)
    ]


class CommittedTableTest(unittest.TestCase):
    """The shipped declaration, read as the loader reads it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.checkpoints = load_checkpoints(ROOT)

    def test_the_committed_table_matches_the_declared_schema(self) -> None:
        with CHECKPOINT_TSV.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            self.assertEqual(tuple(reader.fieldnames or ()), CHECKPOINT_COLUMNS)
            rows = list(reader)
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            [row["checkpoint_id"] for row in rows], ["CHK-HTM-D3", "CHK-HTM-D6"]
        )

    def test_the_committed_table_validates(self) -> None:
        report = validate_checkpoints(
            self.checkpoints,
            known_protocol_steps=_protocol_steps(),
            calibrated_physical_time=False,
        )
        self.assertEqual(report.errors, [], report.errors)
        self.assertIn("checkpoints_observe_existing_phases", report.checks)

    def test_day_three_and_day_six_map_to_one_existing_phase(self) -> None:
        """The mapping this unit exists to make: both days sit in ONE phase.

        Day 3 is not a new arm and not a new protocol. It is 24 h into the same
        96 h full-cocktail phase whose end is day 6, and the two share every
        input the model has.
        """
        phase = checkpoints_for_phase(self.checkpoints, PHASE)
        self.assertEqual([c.checkpoint_id for c in phase], ["CHK-HTM-D3", "CHK-HTM-D6"])
        for checkpoint in phase:
            self.assertEqual(checkpoint.phase_protocol_id, PHASE)
            self.assertEqual(checkpoint.phase_step_id, PHASE)
            self.assertEqual(checkpoint.phase_duration_h, 96.0)
        self.assertEqual(phase[0].hours_after_phase_start, 24.0)
        self.assertEqual(phase[1].hours_after_phase_start, 96.0)

    def test_day_three_is_unplaced_and_day_six_is_the_declared_end(self) -> None:
        """Only the phase end is readable, and it says which horizon it means."""
        day3, day6 = checkpoints_for_phase(self.checkpoints, PHASE)
        self.assertEqual(day3.placement_semantics, PLACEMENT_UNPLACED)
        self.assertEqual(day3.endpoint_horizon_policy, HORIZON_NOT_APPLICABLE)
        self.assertFalse(day3.is_phase_end)
        self.assertEqual(day6.placement_semantics, PLACEMENT_PHASE_END)
        self.assertEqual(day6.endpoint_horizon_policy, HORIZON_CONVERGED)
        self.assertTrue(day6.is_phase_end)

    def test_the_committed_rows_license_only_what_they_can_support(self) -> None:
        """D3 licenses the placement-independent diagnostics and nothing else."""
        day3, day6 = checkpoints_for_phase(self.checkpoints, PHASE)
        self.assertEqual(
            set(day3.licensed_comparisons),
            {COMPARISON_PHASE_WIDE_SIGN, COMPARISON_PHASE_WIDE_CHANGE},
        )
        self.assertEqual(set(day3.licensed_comparisons) & ENDPOINT_COMPARISONS, set())
        self.assertTrue(set(day6.licensed_comparisons) & ENDPOINT_COMPARISONS)

    def test_the_endpoint_horizon_is_the_one_om_002_is_read_at(self) -> None:
        """The ambiguity this replaces: two runs of one phase end differently.

        `config/calibration.yaml` evaluates the active constraints and
        diagnostics at the converged fixed point, so an endpoint checkpoint that
        did not say so could be read off a declared-duration run and silently
        mean something else.
        """
        calibration = yaml.safe_load(CALIBRATION.read_text(encoding="utf-8"))
        horizon_note = calibration["directional_constraints"]["horizon_note"]
        self.assertIn("converged", horizon_note)
        day6 = checkpoints_for_phase(self.checkpoints, PHASE)[1]
        self.assertEqual(day6.endpoint_horizon_policy, HORIZON_CONVERGED)

    def test_no_checkpoint_names_a_protocol_the_repository_does_not_have(
        self,
    ) -> None:
        """A checkpoint that named an absent protocol would BE a new arm."""
        steps = _protocol_steps()
        for checkpoint in self.checkpoints:
            self.assertIn(
                (checkpoint.phase_protocol_id, checkpoint.phase_step_id), steps
            )

    def test_the_checkpoint_layer_adds_no_condition_cfg(self) -> None:
        """The day-3 arm the guards forbid would arrive as a condition file.

        `tests/unit/test_v05_gate3a_guards.py::NoDayThreeArmTest` already fails
        on a day-3 cfg; this asserts the complement from the checkpoint side --
        every checkpoint reuses the cfg of the phase it observes, so there is
        nothing for that guard to find.
        """
        payload = yaml.safe_load(PROTOCOLS.read_text(encoding="utf-8"))
        cfgs = {
            protocol["protocol_id"]: protocol["condition_cfg"]
            for protocol in payload["protocols"]
        }
        for checkpoint in self.checkpoints:
            cfg = cfgs[checkpoint.phase_protocol_id]
            self.assertTrue((ROOT / cfg).exists(), cfg)
            for token in ("day3", "day_3", "24h"):
                self.assertNotIn(token, Path(cfg).name)

    def test_physical_time_is_still_uncalibrated_in_the_repository(self) -> None:
        """The premise the ordinal rule rests on, asserted rather than assumed."""
        calibration = yaml.safe_load(CALIBRATION.read_text(encoding="utf-8"))
        self.assertIs(calibration["time_units"]["calibrated_physical_time"], False)
        self.assertEqual(
            calibration["sequential_execution"]["duration_units"], "relative_only"
        )


class PlacementVocabularyHasOneHomeTest(unittest.TestCase):
    """Placement semantics are described in one place, and cited elsewhere.

    THE DEFECT THIS CLOSES, which appeared three times on this change and twice
    before it on another. A fact gets written into several prose homes; one of
    them is updated when the fact changes; the rest keep asserting the old one
    and nothing fails. Here the placement rule changed from ordinal rank to
    "interior checkpoints are unplaced", and `config/observation_model_map.tsv`
    went on telling readers that day 3 is "read off the trajectory at an ORDINAL
    position" -- a reading `read_checkpoints` now refuses to produce and
    `validate_checkpoints` rejects by name.

    The durable fix is not a third correction. It is that the observation map
    may say WHICH checkpoint represents an observation and WHETHER it has a
    simulated counterpart, and may not describe HOW a checkpoint is placed. That
    description belongs to the checkpoint table and this module, and everything
    else cites them. The same move -- one machine-readable home plus a check --
    is what stopped `externally_asserted_fields` drifting.
    """

    #: Terms that describe a placement RULE. A file needing one of these is
    #: restating something it should be citing. ``phase_end`` is matched as a
    #: whole word so `config/protocols.yaml`'s `e2_phase_end_day` -- an
    #: experimental day anchor with nothing to do with placement -- is not a
    #: false positive.
    PLACEMENT_VOCABULARY = (
        "ordinal position",
        "ordinal-rank",
        "ordinal rank",
        PLACEMENT_ORDINAL_RANK,
        PLACEMENT_UNPLACED,
        PLACEMENT_PROPORTIONAL,
    )
    PLACEMENT_WORDS = (PLACEMENT_PHASE_END,)

    def _placement_terms(self, text: str) -> list[str]:
        lowered = text.lower()
        found = [term for term in self.PLACEMENT_VOCABULARY if term in lowered]
        found += [
            word
            for word in self.PLACEMENT_WORDS
            if re.search(rf"(?<![a-z_]){re.escape(word)}(?![a-z_])", lowered)
        ]
        return found

    def _non_authoritative_homes(self) -> list[tuple[str, str]]:
        """Current-state files that must CITE the placement rule, not state it.

        The authoritative homes are deliberately absent:
        `config/observation_checkpoints.tsv`,
        `docs/observation_checkpoints.md` and
        `src/dt_adoc/observations/checkpoints.py` are where placement is
        defined, and a guard that forbade the vocabulary there would forbid
        saying the thing at all.
        """
        return [
            (rel, (ROOT / rel).read_text(encoding="utf-8"))
            for rel in (
                "config/protocols.yaml",
                "config/secreted_protein_contract.yaml",
                "config/observation_model_map.tsv",
                "config/adoc_outlet_conditions.tsv",
            )
        ]

    def test_no_non_authoritative_home_states_a_placement_rule(self) -> None:
        """The exact evasion the previous round left open.

        The first version of this guard checked `config/observation_model_map.tsv`
        and nothing else, so restoring `config/protocols.yaml`'s retired note --
        "read off this phase's existing continuous trajectory at an ordinal
        position" -- would have passed it. That wording is mutation-tested in
        `test_the_retired_protocols_note_would_be_caught`.
        """
        offenders = [
            f"{label}: {term}"
            for label, text in self._non_authoritative_homes()
            for term in self._placement_terms(text)
        ]
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_the_retired_protocols_note_would_be_caught(self) -> None:
        """Mutation test on the exact sentence that caused the last round."""
        retired = (
            "Since 2026-09-18 day 3 is represented instead as an OBSERVATION "
            "CHECKPOINT (CHK-HTM-D3 in config/observation_checkpoints.tsv) read "
            "off this phase's existing continuous trajectory at an ordinal "
            "position -- no arm, no reset."
        )
        self.assertEqual(self._placement_terms(retired), ["ordinal position"])

    def test_the_day_anchor_fields_are_not_false_positives(self) -> None:
        """`e2_phase_end_day` is experimental timing, not a placement rule."""
        self.assertEqual(
            self._placement_terms('"e2_phase_end_day": 2, "cocktail_end_day": 6'),
            [],
        )
        self.assertEqual(
            self._placement_terms("placement_semantics=phase_end"), ["phase_end"]
        )

    #: A statement of current state that unit U2b made false. It may still
    #: appear where it is explicitly marked as the superseded record -- OM-011
    #: exists to hold exactly that history -- but not as a live claim.
    RETIRED_CURRENT_STATE = (
        "no protocol counterpart",
        "no protocol represents the day-3",
        "no protocol represents day 3",
    )
    #: Words that mark a sentence as history rather than current state.
    HISTORY_MARKERS = (
        "superseded",
        "as recorded",
        "previously",
        "former",
        "closed",
        "withdrawn",
        "used to",
        "no longer",
    )

    def _live_claims(self, text: str) -> list[str]:
        """Retired claims stated as current, sentence by sentence.

        Split per sentence rather than per line: `config/protocols.yaml` holds
        a whole note on one line, so a line-wide search for a history marker
        elsewhere in that note would excuse a live claim sitting next to it.
        """
        found: list[str] = []
        for sentence in re.split(r"(?<=[.;])\s+|\\n", text):
            lowered = sentence.lower()
            if any(marker in lowered for marker in self.HISTORY_MARKERS):
                continue
            for phrase in self.RETIRED_CURRENT_STATE:
                if phrase in lowered:
                    found.append(f"{phrase!r} in: {sentence.strip()[:110]}")
        return found

    def _semantic_homes(self) -> list[tuple[str, str]]:
        """The files that state the CURRENT day-3 semantics, not its history.

        Named explicitly rather than globbed: a sweep over all of docs/ would
        catch the analysis findings whose whole job is to record what was
        believed on the day they were written, and rewriting those would
        destroy the record instead of maintaining it.
        """
        return [
            (
                "config/protocols.yaml",
                (ROOT / "config" / "protocols.yaml").read_text(encoding="utf-8"),
            ),
            (
                "config/observation_checkpoints.tsv",
                (ROOT / "config" / "observation_checkpoints.tsv").read_text(
                    encoding="utf-8"
                ),
            ),
            (
                "config/secreted_protein_contract.yaml",
                (ROOT / "config" / "secreted_protein_contract.yaml").read_text(
                    encoding="utf-8"
                ),
            ),
        ]

    def test_no_current_state_home_still_says_day_three_has_no_protocol(
        self,
    ) -> None:
        """The drift this closes, in the homes that state current behaviour.

        `config/protocols.yaml` kept describing CHK-HTM-D3 as read at an ordinal
        position after that reading was withdrawn, and two observation-map rows
        kept saying day 3 has "no protocol counterpart" after the phase was
        shown to be the counterpart. The canonical current state is: the
        protocol phase exists, the experimental checkpoint exists, the
        experimental-to-MaBoSS alignment is unresolved, and there is no day-3
        simulated value.
        """
        offenders: list[str] = []
        for label, text in self._semantic_homes():
            offenders.extend(
                f"{label}: {sentence}" for sentence in self._live_claims(text)
            )
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_the_observation_map_states_the_current_day_three_semantics(
        self,
    ) -> None:
        """Same check for the map, where a row may hold marked history."""
        with (ROOT / "config" / "observation_model_map.tsv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        offenders = [
            f"{row['mapping_id']}.{column}: {claim}"
            for row in rows
            for column, value in row.items()
            for claim in self._live_claims(value or "")
        ]
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_the_observation_map_describes_no_placement_rule(self) -> None:
        with (ROOT / "config" / "observation_model_map.tsv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        # Case-insensitive on purpose: the text this closes wrote "ORDINAL
        # position" in capitals, and a guard that a shout gets past is no guard.
        offenders = [
            (row["mapping_id"], column, term)
            for row in rows
            for column, value in row.items()
            for term in self.PLACEMENT_VOCABULARY
            if term.lower() in (value or "").lower()
        ]
        self.assertEqual(
            offenders,
            [],
            "an observation-map row describes how a checkpoint is placed. That "
            "belongs to config/observation_checkpoints.tsv and "
            "src/dt_adoc/observations/checkpoints.py; cite them instead, or the "
            "next placement change leaves this row asserting the old rule:\n"
            + "\n".join(map(str, offenders)),
        )

    def test_the_map_still_cites_the_checkpoint_it_depends_on(self) -> None:
        """Citing, not restating -- a row that says nothing is not the fix."""
        with (ROOT / "config" / "observation_model_map.tsv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = {
                row["mapping_id"]: row for row in csv.DictReader(handle, delimiter="\t")
            }
        for mapping_id in ("OM-004", "OM-005", "OM-006", "OM-011"):
            with self.subTest(mapping_id=mapping_id):
                text = " ".join(rows[mapping_id].values())
                self.assertIn("CHK-HTM-D3", text)
                self.assertIn("observation_checkpoints", text)

    def test_the_committed_checkpoint_table_is_where_placement_lives(self) -> None:
        for checkpoint in load_checkpoints(ROOT):
            self.assertIn(
                checkpoint.placement_semantics,
                {PLACEMENT_UNPLACED, PLACEMENT_PHASE_END},
            )


class PlacementTest(unittest.TestCase):
    """What a placement rule may and may not do."""

    def test_an_interior_checkpoint_is_read_at_no_time_and_no_value(self) -> None:
        """The core of the redesign, stated as the reading it produces."""
        times = [round(0.1 * step, 1) for step in range(40)]
        phase = _phase(times, {"S_IGFBP1": [step / 39 for step in range(40)]})
        readings = read_checkpoints(
            phase,
            _synthetic_checkpoints([24.0, 96.0]),
            node_ids=("S_IGFBP1",),
        )
        interior, terminal = readings
        self.assertEqual(interior.placement, PLACEMENT_UNPLACED)
        self.assertIsNone(interior.phase_local_time)
        self.assertIsNone(interior.value)
        self.assertFalse(interior.is_placed)
        self.assertEqual(terminal.placement, PLACEMENT_PHASE_END)
        self.assertTrue(terminal.is_placed)

    def test_declaring_future_checkpoints_cannot_move_an_existing_one(self) -> None:
        """The regression the external review asked for, and the defect it names.

        Under ordinal-rank placement the day-3 reading sat at 1/2 of the phase
        with two checkpoints declared and would have slid to 1/4 with four --
        an unchanged observation acquiring a different simulated value because
        a different observation was declared. With interior checkpoints
        unplaced, the 24 h reading is identical in both worlds, and so is the
        phase-end reading and every phase-wide quantity.
        """
        times = [round(0.1 * step, 1) for step in range(40)]
        values = [step / 39 for step in range(40)]
        phase = _phase(times, {"S_IGFBP1": values, "S_PRL": values})

        today = read_checkpoints(
            phase,
            _synthetic_checkpoints([24.0, 96.0]),
            node_ids=("S_IGFBP1",),
        )
        extended = read_checkpoints(
            phase,
            _synthetic_checkpoints([24.0, 48.0, 72.0, 96.0]),
            node_ids=("S_IGFBP1",),
        )

        def by_hour(readings: list, checkpoint_id: str) -> tuple:
            reading = next(r for r in readings if r.checkpoint_id == checkpoint_id)
            return (
                reading.placement,
                reading.phase_local_time,
                reading.value,
                reading.phase_min,
                reading.phase_max,
            )

        self.assertEqual(by_hour(today, "CHK-T24"), by_hour(extended, "CHK-T24"))
        self.assertEqual(by_hour(today, "CHK-T96"), by_hour(extended, "CHK-T96"))
        self.assertEqual(len(extended), 4)

    def test_the_verdicts_are_unchanged_by_declaring_more_checkpoints(self) -> None:
        """Extension must not move an interpretation either, not just a number.

        The verdicts are phase-wide, so they cannot depend on the declarations
        at all -- which is why they remained useful once placement was dropped.
        """
        times = [round(0.1 * step, 1) for step in range(40)]
        rising = [step / 39 for step in range(40)]
        phase = _phase(times, {"A": rising, "B": [value * 0.5 for value in rising]})
        verdict = ordering_verdict(phase, node_a="A", node_b="B")
        for hours in ([24.0, 96.0], [24.0, 48.0, 72.0, 96.0]):
            read_checkpoints(phase, _synthetic_checkpoints(hours), node_ids=("A",))
            self.assertEqual(ordering_verdict(phase, node_a="A", node_b="B"), verdict)

    def test_reading_the_endpoint_off_the_declared_run_is_refused(self) -> None:
        """A declared-duration execution cannot satisfy a converged endpoint."""
        times = [round(0.1 * step, 1) for step in range(40)]
        phase = _phase(
            times,
            {"S_IGFBP1": [step / 39 for step in range(40)]},
            executed=DECLARED_EXTENT,
            horizon=HORIZON_DECLARED,
        )
        with self.assertRaises(ValueError) as caught:
            read_checkpoints(
                phase,
                _synthetic_checkpoints([24.0, 96.0]),
                node_ids=("S_IGFBP1",),
            )
        self.assertIn("MEASURED", str(caught.exception))

    def test_the_execution_cannot_be_asserted_by_the_caller_at_all(self) -> None:
        """The regression for two defects of one shape.

        `read_checkpoints` once took a `horizon` string on trust, so a
        declared-duration frame labelled `converged_fixed_point` was read as
        converged. The verdict functions then took `trajectory_count` on trust,
        so the SAME frame evaluated at N=1e9 returned `invariant_greater` where
        at its real N=2000 it returned `indistinguishable` -- the band shrank by
        two orders of magnitude because a caller said so.

        Neither argument exists now. Everything about the run is read off the
        `ExecutedPhase` the run itself produced.
        """
        for function in (read_checkpoints, ordering_verdict, monotonicity_verdict):
            parameters = inspect.signature(function).parameters
            with self.subTest(function=function.__name__):
                self.assertNotIn("horizon", parameters)
                self.assertNotIn("trajectory_count", parameters)
                self.assertNotIn("model_version", parameters)
                self.assertNotIn("tolerance", parameters)

    def test_the_band_follows_the_execution_not_a_caller(self) -> None:
        """The reproduced defect: the same data, two different N, two verdicts.

        Both phases below hold identical rows. The only difference is the
        trajectory count each execution reports, which is now a property of the
        execution, so producing the narrow-band verdict requires producing a run
        that actually had 10^9 trajectories.
        """
        times = [0.0, 0.1, 0.2]
        a = [0.50, 0.52, 0.54]
        b = [0.44, 0.46, 0.48]
        honest = _phase(times, {"A": a, "B": b}, trajectory_count=2000)
        inflated = _phase(times, {"A": a, "B": b}, trajectory_count=1_000_000_000)
        self.assertEqual(
            ordering_verdict(honest, node_a="A", node_b="B"), INDISTINGUISHABLE
        )
        self.assertEqual(
            ordering_verdict(inflated, node_a="A", node_b="B"), INVARIANT_GREATER
        )
        for phase in (honest, inflated):
            self.assertEqual(
                [float(value) for value in phase.rows["A"]],
                a,
                "the rows must be identical; only the reported execution differs",
            )

    def test_executed_phase_binds_the_metadata_to_the_rows(self) -> None:
        """What `executed_phase` is for: one object, one account of the run."""
        phase = _phase([0.0, 0.1], {"A": [0.1, 0.2]})
        self.assertEqual(phase.protocol_id, PHASE)
        self.assertEqual(phase.model_version, MODEL_VERSION)
        self.assertEqual(phase.trajectory_count, TRAJECTORY_COUNT)
        self.assertEqual(phase.declared_duration, DECLARED_EXTENT)
        self.assertEqual(phase.executed_duration, CONVERGED_EXTENT)
        self.assertEqual(phase.sampled_points, 2)
        # Frozen: the run's account of itself is not editable after the fact.
        with self.assertRaises(dataclasses.FrozenInstanceError):
            phase.trajectory_count = 10  # type: ignore[misc]

    def test_a_checkpoint_is_refused_against_a_model_it_does_not_declare(
        self,
    ) -> None:
        """`applies_to_model_versions` was parsed and never enforced.

        A checkpoint is declared against the models whose trajectory it
        describes. Reading it against another model is not a judgement call to
        be made silently at read time.
        """
        phase = _phase(
            [0.0, 0.1], {"S_IGFBP1": [0.1, 0.2]}, model_version="adoc-core-v0.1.0"
        )
        with self.assertRaises(ValueError) as caught:
            read_checkpoints(
                phase, _synthetic_checkpoints([24.0, 96.0]), node_ids=("S_IGFBP1",)
            )
        self.assertIn("applies_to_model_versions", str(caught.exception))

    def test_every_committed_checkpoint_declares_the_live_superset(self) -> None:
        for checkpoint in load_checkpoints(ROOT):
            self.assertIn(MODEL_VERSION, checkpoint.applies_to_model_versions)


class ValidationTest(unittest.TestCase):
    """Negative controls: each rule, broken on purpose."""

    def test_a_proportional_row_is_rejected_while_time_is_uncalibrated(self) -> None:
        checkpoints = [
            replace(
                checkpoint,
                placement_semantics=PLACEMENT_PROPORTIONAL,
                endpoint_horizon_policy=HORIZON_NOT_APPLICABLE,
            )
            for checkpoint in _synthetic_checkpoints([24.0, 96.0])
        ]
        report = validate_checkpoints(checkpoints, calibrated_physical_time=False)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("physical-time calibration" in error for error in report.errors),
            report.errors,
        )

    def test_the_proportional_row_is_admissible_only_if_time_were_calibrated(
        self,
    ) -> None:
        """States the condition rather than hard-coding the prohibition.

        The repository is not going to calibrate physical time, but a rule that
        cannot say WHEN it would stop applying is a slogan, not a check. Note
        that ordinal-rank placement below has NO such condition: it is wrong
        whatever the time axis does, because its defect is instability under
        extension rather than an unwarranted calibration.
        """
        checkpoints = [
            replace(
                checkpoint,
                placement_semantics=PLACEMENT_PROPORTIONAL,
                endpoint_horizon_policy=HORIZON_NOT_APPLICABLE,
                # Only phase-wide comparisons: a non-`phase_end` checkpoint may
                # not license an endpoint reading, which is a separate rule and
                # would otherwise mask the one under test.
                licensed_comparisons=(COMPARISON_PHASE_WIDE_SIGN,),
            )
            for checkpoint in _synthetic_checkpoints([24.0, 96.0])
        ]
        report = validate_checkpoints(checkpoints, calibrated_physical_time=True)
        self.assertEqual(report.errors, [])

    def test_ordinal_rank_placement_is_rejected_at_any_time_semantics(self) -> None:
        """The rule this unit shipped first, kept named so it cannot return."""
        for calibrated in (False, True):
            checkpoints = [
                replace(
                    checkpoint,
                    placement_semantics=PLACEMENT_ORDINAL_RANK,
                    endpoint_horizon_policy=HORIZON_NOT_APPLICABLE,
                )
                for checkpoint in _synthetic_checkpoints([24.0, 96.0])
            ]
            report = validate_checkpoints(
                checkpoints, calibrated_physical_time=calibrated
            )
            with self.subTest(calibrated_physical_time=calibrated):
                self.assertFalse(report.ok)
                self.assertTrue(
                    any("1/2 of the phase to" in error for error in report.errors),
                    report.errors,
                )

    def test_an_interior_checkpoint_may_not_declare_an_endpoint_horizon(self) -> None:
        checkpoints = _synthetic_checkpoints([24.0, 96.0])
        checkpoints[0] = replace(
            checkpoints[0], endpoint_horizon_policy=HORIZON_CONVERGED
        )
        report = validate_checkpoints(checkpoints)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("read at no position" in error for error in report.errors),
            report.errors,
        )

    def test_a_phase_end_must_declare_a_horizon_and_sit_at_the_end(self) -> None:
        checkpoints = _synthetic_checkpoints([24.0, 96.0])
        checkpoints[1] = replace(
            checkpoints[1], endpoint_horizon_policy=HORIZON_NOT_APPLICABLE
        )
        report = validate_checkpoints(checkpoints)
        self.assertTrue(
            any("must declare endpoint_horizon_policy" in e for e in report.errors),
            report.errors,
        )

        mislabelled = _synthetic_checkpoints([24.0, 96.0])
        mislabelled[0] = replace(
            mislabelled[0],
            placement_semantics=PLACEMENT_PHASE_END,
            endpoint_horizon_policy=HORIZON_CONVERGED,
        )
        report = validate_checkpoints(mislabelled)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("a phase has one end" in e for e in report.errors), report.errors
        )

    def test_ordinal_order_must_follow_experimental_time(self) -> None:
        """Placement is fixed by the experiment, so the order may not be edited.

        Swapping two checkpoints' hours while keeping their ordinal indices is
        exactly how a placement could be chosen after seeing the values.
        """
        checkpoints = _synthetic_checkpoints([96.0, 24.0])
        report = validate_checkpoints(checkpoints)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("does not follow experimental time" in e for e in report.errors),
            report.errors,
        )

    def test_a_checkpoint_outside_its_phase_is_rejected(self) -> None:
        checkpoints = _synthetic_checkpoints([24.0, 120.0])
        report = validate_checkpoints(checkpoints)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("outside (0, 96.0]" in error for error in report.errors), report.errors
        )

    def test_a_fraction_that_contradicts_its_hours_is_rejected(self) -> None:
        checkpoints = _synthetic_checkpoints([24.0, 96.0])
        checkpoints[0] = replace(checkpoints[0], experimental_phase_fraction=0.5)
        report = validate_checkpoints(checkpoints)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("experimental_phase_fraction" in error for error in report.errors),
            report.errors,
        )

    def test_an_unplaced_checkpoint_may_not_license_an_endpoint_reading(
        self,
    ) -> None:
        """The contract must not license what the reader returns as None.

        Both checkpoints used to declare `within_phase_ordering` and
        `cross_analyte_same_checkpoint`, each of which names a comparison AT a
        checkpoint. CHK-HTM-D3 is unplaced and has no value, so the
        machine-readable contract asserted something `read_checkpoints` refuses
        to produce -- and the field was parsed and never validated, so nothing
        caught it.
        """
        checkpoints = _synthetic_checkpoints([24.0, 96.0])
        checkpoints[0] = replace(
            checkpoints[0],
            licensed_comparisons=(COMPARISON_ENDPOINT_VALUE,),
        )
        report = validate_checkpoints(checkpoints)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("returns as None" in error for error in report.errors), report.errors
        )

    def test_an_unknown_licensed_comparison_is_rejected(self) -> None:
        checkpoints = _synthetic_checkpoints([24.0, 96.0])
        checkpoints[0] = replace(
            checkpoints[0], licensed_comparisons=("within_phase_ordering",)
        )
        report = validate_checkpoints(checkpoints)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("unknown licensed_comparisons" in e for e in report.errors),
            report.errors,
        )

    def test_a_checkpoint_licensing_nothing_is_rejected(self) -> None:
        checkpoints = _synthetic_checkpoints([24.0, 96.0])
        checkpoints[0] = replace(checkpoints[0], licensed_comparisons=())
        report = validate_checkpoints(checkpoints)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("licenses nothing" in error for error in report.errors), report.errors
        )

    def test_a_checkpoint_on_an_undeclared_phase_is_rejected(self) -> None:
        checkpoints = [
            replace(checkpoint, phase_protocol_id="hormone_treated_day3")
            for checkpoint in _synthetic_checkpoints([24.0, 96.0])
        ]
        report = validate_checkpoints(
            checkpoints, known_protocol_steps=_protocol_steps()
        )
        self.assertFalse(report.ok)
        self.assertTrue(
            any("never imply a new protocol arm" in error for error in report.errors),
            report.errors,
        )


class ReadingTest(unittest.TestCase):
    """Reading declared checkpoints off an already-executed phase trajectory."""

    def setUp(self) -> None:
        self.times = [round(0.1 * step, 1) for step in range(40)]
        self.rising = [step / 39 for step in range(40)]
        self.phase = _phase(
            self.times,
            {
                "S_IGFBP1": list(self.rising),
                "S_PRL": list(self.rising),
                "S_DECIDUALIZED": [min(1.0, value * 1.5) for value in self.rising],
            },
        )
        self.frame = self.phase.rows

    def _read(self, hours: list[float], **kwargs):
        return read_checkpoints(self.phase, _synthetic_checkpoints(hours), **kwargs)

    def test_the_endpoint_reading_is_a_sampled_row_never_an_interpolation(
        self,
    ) -> None:
        for reading in self._read([24.0, 96.0]):
            if reading.is_placed:
                self.assertIn(reading.phase_local_time, self.times)
                self.assertIn(reading.value, self.rising)

    def test_reading_does_not_reset_or_re_run_anything(self) -> None:
        """The reader is a pure function of one phase's rows.

        Both checkpoints refer to the SAME continuous trajectory: one
        phase_index, one monotone time axis, and the frame is unchanged
        afterwards. A design that restarted the phase per checkpoint would show
        two phase indices or a time axis that returns to zero.
        """
        import pandas as pd

        before = self.frame.copy()
        self._read([24.0, 96.0])
        pd.testing.assert_frame_equal(before, self.frame)
        self.assertEqual(sorted(self.frame["phase_index"].unique()), [2])
        self.assertEqual(self.frame["phase_local_time"].tolist(), self.times)

    def test_every_reading_carries_the_phase_range_placed_or_not(self) -> None:
        """Phase-wide behaviour needs no position, so an unplaced reading has it."""
        for reading in self._read([24.0, 96.0]):
            self.assertEqual(reading.phase_min, min(self.rising))
            self.assertEqual(reading.phase_max, max(self.rising))
            self.assertGreater(reading.phase_range, 0.0)
            self.assertEqual(reading.horizon, HORIZON_CONVERGED)

    def test_four_future_checkpoints_need_no_code_change(self) -> None:
        """The design constraint: 24/48/72/96 h must work as data, not code.

        Nothing below constructs a protocol, a cfg or a branch -- only four
        declarations against the same single trajectory. Three are unplaced and
        one is the phase end, which is what stops the extension from disturbing
        what was already declared.
        """
        readings = self._read([24.0, 48.0, 72.0, 96.0], node_ids=("S_IGFBP1",))
        self.assertEqual(len(readings), 4)
        self.assertEqual(
            [reading.checkpoint_id for reading in readings],
            ["CHK-T24", "CHK-T48", "CHK-T72", "CHK-T96"],
        )
        self.assertEqual(
            [reading.is_placed for reading in readings],
            [False, False, False, True],
        )


class InvarianceVerdictTest(unittest.TestCase):
    """Verdicts are computed over the phase, not at the placed positions."""

    def _verdict(
        self, a: list[float], b: list[float], *, trajectory_count: int = 1_000_000
    ) -> str:
        """A large N so the band is small enough for the SHAPE to decide.

        These cases are about what the relation says, not about sampling: at
        N = 1e6 the band is ~0.006, so a gap of 0.4 is a verdict and a crossing
        is a crossing. Sampling power is exercised separately below.
        """
        times = [round(0.1 * step, 1) for step in range(len(a))]
        phase = _phase(times, {"A": a, "B": b}, trajectory_count=trajectory_count)
        return ordering_verdict(phase, node_a="A", node_b="B")

    def test_a_constant_gap_is_invariant(self) -> None:
        self.assertEqual(
            self._verdict([0.5, 0.6, 0.7], [0.1, 0.2, 0.3]), INVARIANT_GREATER
        )
        self.assertEqual(
            self._verdict([0.1, 0.2, 0.3], [0.5, 0.6, 0.7]), INVARIANT_LESS
        )

    def test_a_crossing_is_placement_dependent_not_a_verdict(self) -> None:
        """The case the whole abstraction exists for.

        If A leads early and B leads late, then "A > B" is true at one placement
        and false at another. With no calibrated time axis the repository cannot
        say which placement is right, so the honest answer is neither verdict.
        """
        self.assertEqual(
            self._verdict([0.9, 0.5, 0.1], [0.1, 0.5, 0.9]), PLACEMENT_DEPENDENT
        )

    def test_equal_trajectories_are_indistinguishable_not_equal(self) -> None:
        self.assertEqual(
            self._verdict([0.2, 0.4, 0.6], [0.2, 0.4, 0.6]), INDISTINGUISHABLE
        )

    def test_the_band_shrinks_with_the_trajectory_count(self) -> None:
        self.assertGreater(
            paired_difference_tolerance(500, comparisons=40),
            paired_difference_tolerance(2000, comparisons=40),
        )

    def test_the_band_widens_with_the_number_of_comparisons(self) -> None:
        """A verdict tests every sampled time, so the rate is family-wise."""
        self.assertGreater(
            paired_difference_tolerance(2000, comparisons=780),
            paired_difference_tolerance(2000, comparisons=40),
        )

    def test_the_band_is_the_hoeffding_paired_bound_not_the_independent_one(
        self,
    ) -> None:
        """The construction, pinned against its own formula and its predecessor.

        The retired band was `z * sqrt(2) * 0.5 / sqrt(N)`, valid only for
        INDEPENDENT estimates -- which two nodes read from one set of
        trajectories are not, and whose covariance marginal `nodes_probtraj`
        curves cannot identify. The replacement bounds the paired mean of
        `D = A - B in [-1, 1]` directly, so within-trajectory dependence never
        enters. It is wider, which is the conservative direction for asserting
        a difference.
        """
        from math import log, sqrt

        band = paired_difference_tolerance(2000, comparisons=40)
        self.assertAlmostEqual(band, sqrt(2 * log(2 * 40 / 0.0027) / 2000), places=12)
        retired_independent_band = 3.0 * sqrt(2.0) * 0.5 / sqrt(2000)
        self.assertGreater(band, retired_independent_band)

    def test_the_band_rejects_impossible_arguments(self) -> None:
        for kwargs in (
            {"comparisons": 0},
            {"family_error": 0.0},
            {"family_error": 1.0},
        ):
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                paired_difference_tolerance(2000, **{"comparisons": 40, **kwargs})
        with self.assertRaises(ValueError):
            paired_difference_tolerance(0, comparisons=40)

    def test_a_gap_inside_the_band_is_not_a_verdict(self) -> None:
        """Power, stated as a test: this run cannot resolve a gap this small."""
        self.assertEqual(
            self._verdict([0.50, 0.60], [0.495, 0.595], trajectory_count=2000),
            INDISTINGUISHABLE,
        )
        self.assertEqual(
            self._verdict([0.50, 0.60], [0.20, 0.30], trajectory_count=2000),
            INVARIANT_GREATER,
        )

    def test_a_decline_through_sub_band_steps_is_not_non_decreasing(self) -> None:
        """The reproduced defect, kept as the regression.

        `monotonicity_verdict` compared ADJACENT steps against the band, which
        is not transitive: seventeen decreases each just inside the band summed
        to a fall from 1.0 to 0.002, and the verdict was
        `invariant_non_decreasing`. The relation the verdict licenses is "every
        later value is at least every earlier one", so every ordered pair is
        what it tests, and this series is now correctly the opposite verdict.
        """
        band = paired_difference_tolerance(TRAJECTORY_COUNT, comparisons=17 * 16 // 2)
        values = [1.0 - step * band * 0.99 for step in range(17)]
        self.assertGreater(values[0] - values[-1], 0.9)
        for earlier, later in pairwise(values):
            self.assertLess(earlier - later, band)
        phase = _phase([round(0.1 * step, 1) for step in range(17)], {"A": values})
        verdict = monotonicity_verdict(phase, node_id="A")
        self.assertNotEqual(verdict, NO_RESOLVED_DECREASE)
        self.assertEqual(verdict, NO_RESOLVED_INCREASE)

    def test_a_real_decrease_inside_the_band_is_not_called_non_decreasing(
        self,
    ) -> None:
        """The reproduced overstatement, and the rename that answers it.

        A fall from 0.50 to 0.45 with a band of ~0.081 was returned as
        `INVARIANT_NON_DECREASING`. It decreases. The band bounds the error of
        the ESTIMATE, so "every estimate is at least -t" certifies only that the
        truth is at least -2t -- it cannot certify that nothing fell. The
        verdict now says what it has: no decrease was RESOLVED above Monte
        Carlo error. Certifying a true non-decrease would need every ordered
        estimate above +t, which this series is nowhere near.
        """
        band = paired_difference_tolerance(TRAJECTORY_COUNT, comparisons=1)
        self.assertGreater(band, 0.05)
        phase = _phase([0.0, 0.1], {"A": [0.50, 0.45]})
        verdict = monotonicity_verdict(phase, node_id="A")
        self.assertEqual(verdict, NO_RESOLVED_DECREASE)
        self.assertNotIn("non_decreasing", verdict)
        self.assertIn("no_resolved_decrease", verdict)
        # What the verdict would have had to clear to certify a true increase.
        self.assertLess(0.45 - 0.50, band)

    def test_the_verdict_names_say_resolved_not_proven(self) -> None:
        """The vocabulary is the claim; a reader should not have to infer it."""
        for verdict in (NO_RESOLVED_DECREASE, NO_RESOLVED_INCREASE):
            self.assertIn("no_resolved", verdict)
            self.assertIn("mc_error", verdict)
        self.assertEqual(RESOLVED_BOTH_DIRECTIONS, "resolved_change_in_both_directions")

    def test_the_relation_is_every_ordered_pair_not_just_neighbours(self) -> None:
        """A dip that recovers: adjacent steps alone would miss the pair."""
        band = paired_difference_tolerance(TRAJECTORY_COUNT, comparisons=3)
        values = [0.9, 0.9 - band * 0.9, 0.9 - band * 1.8]
        phase = _phase([0.0, 0.1, 0.2], {"A": values})
        self.assertEqual(monotonicity_verdict(phase, node_id="A"), NO_RESOLVED_INCREASE)

    def test_a_single_sampled_time_cannot_carry_a_monotonicity_verdict(
        self,
    ) -> None:
        phase = _phase([0.0], {"A": [0.5]})
        with self.assertRaises(ValueError):
            monotonicity_verdict(phase, node_id="A")

    def test_the_diagnostic_separates_a_rise_from_a_change_in_both_directions(
        self,
    ) -> None:
        """Renamed: this unit licenses NO across-checkpoint ordering.

        The old name said the diagnostic licensed an across-checkpoint
        comparison. It does not, and the interior checkpoint has no value to
        compare anyway. What it distinguishes is whether a change was
        resolved above Monte Carlo error, and in which direction.
        """
        times = [0.0, 0.1, 0.2, 0.3]
        rising = _phase(times, {"A": [0.1, 0.2, 0.3, 0.4]}, trajectory_count=10**7)
        self.assertEqual(
            monotonicity_verdict(rising, node_id="A"), NO_RESOLVED_DECREASE
        )
        humped = _phase(times, {"A": [0.1, 0.9, 0.2, 0.8]}, trajectory_count=10**7)
        self.assertEqual(
            monotonicity_verdict(humped, node_id="A"), RESOLVED_BOTH_DIRECTIONS
        )


if __name__ == "__main__":
    unittest.main()
