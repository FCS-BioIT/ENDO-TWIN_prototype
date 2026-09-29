"""Within-phase observation checkpoints, and how far a verdict depends on them.

An experiment samples a treatment phase more than once -- ADOC samples the 96 h
full-cocktail phase at 24 h and at 96 h, and future runs are expected to sample
it every 24 h. The model runs that phase as ONE continuous MaBoSS trajectory
with a relative duration, initialised by continuation from the preceding phase.
This module lets the repository read that existing trajectory at declared
positions. It creates no protocol, runs no simulation, resets no state, and
never converts an experimental hour into a simulation time.

Three quantities are kept apart, and conflating them is the failure this module
exists to prevent:

* **Experimental elapsed time** -- 24 h, 48 h, 96 h. A fact about the bench,
  recorded in ``config/observation_checkpoints.tsv`` and in the protocol's
  ``experimental_day_anchors``.
* **Experimental phase fraction** -- 24/96 = 0.25. Still a fact about the bench:
  it is the position of the sample within the *experimental* phase, and says
  nothing about the simulation.
* **MaBoSS relative time** -- the ``phase_local_time`` axis of the trajectory.
  ``config/calibration.yaml`` records ``calibrated_physical_time: false``, so no
  validated map exists between this axis and hours, in either direction.

WHY AN INTERIOR CHECKPOINT GETS NO SIMULATION TIME AT ALL. Two conventions were
tried and both are rejected.

*Proportional* placement -- read 24 h of a 96 h phase at 0.25 of the relative
duration -- is a physical-time calibration written as a ratio: it asserts
hours = k x relative time with k fixed by the phase, which is what
``calibrated_physical_time: false`` denies. It is also under-determined, because
this repository deliberately executes the same phase at two horizons (the
declared ``relative_duration`` and the converged fixed point of
``docs/endpoint_convergence_finding.md``), and "0.25 of the phase" names a
different part of the curve under each.

*Ordinal rank* placement -- the k-th of n checkpoints at ``k/n`` of the phase --
avoids the hours but is **not stable under dataset extension**, which is worse.
Declaring the future 48 h and 72 h checkpoints would move the day-3 reading from
``1/2`` of the trajectory to ``1/4``, so an unchanged historical observation
would acquire a different simulated value merely because new declarations
arrived. A placement rule whose output depends on what else is declared cannot
carry an observation.

So an interior checkpoint is an **ordered observation with no assigned MaBoSS
time and no read value**. Its experimental hours, fraction and order are kept as
metadata, and that is all a checkpoint asserts. Only the terminal checkpoint is
read for a value, because the end of an executed phase is the one position no
placement rule has to choose -- and even that is read under an explicitly
declared horizon policy rather than from whatever row the supplied frame happens
to end on.

WHAT IS STILL COMPARABLE, AND ON WHAT CONDITION. Nothing here needs an interior
position, because the useful comparisons are phase-wide:

* two nodes compared at one position agree with the phase-wide answer only where
  the SIGN of their difference is constant across the phase. If the trajectories
  cross, the answer depends on where one looks, and no reparameterisation
  argument rescues it;
* one node compared across positions in experimental order agrees with the
  phase-wide answer only where the trajectory is MONOTONE over the phase.

``ordering_verdict`` and ``monotonicity_verdict`` examine exactly those two
conditions over every sampled time. They are the safeguard; the conditions are
not assumed anywhere.

ONLY THE FIRST IS EVER CERTIFIED. The band bounds the error of the ESTIMATE, so
``ordering_verdict`` can certify a true sign -- every estimate outside the band
in one direction -- while the monotonicity check cannot: "every ordered estimate
is at least ``-t``" establishes only that the truth is at least ``-2t``. Its
verdicts are therefore named for the diagnostic they support, not for
monotonicity, and NO across-checkpoint ordering is licensed by this module at
all. None is needed: the interior checkpoint is unplaced, so there is nothing to
order it against.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import pairwise
from math import log, sqrt
from pathlib import Path
from typing import Any

from dt_adoc.model.provenance import repo_root

DEFAULT_CHECKPOINT_PATH = "config/observation_checkpoints.tsv"

CHECKPOINT_COLUMNS: tuple[str, ...] = (
    "checkpoint_id",
    "phase_protocol_id",
    "phase_step_id",
    "applies_to_model_versions",
    "experimental_label",
    "source_condition_id",
    "hours_after_phase_start",
    "phase_duration_h",
    "experimental_phase_fraction",
    "ordinal_index",
    "ordinal_count",
    "placement_semantics",
    "endpoint_horizon_policy",
    "observed_series",
    "model_nodes",
    "observation_rows",
    "licensed_comparisons",
    "forbidden_uses",
    "predeclared_on",
    "predeclaration_basis",
    "evidence_ids",
    "note",
)

#: Placement rules. ``unplaced_ordinal`` carries order and no simulation time;
#: ``phase_end`` is the terminal position of an executed phase. ``proportional``
#: and ``ordinal_rank`` are named so a row attempting either is rejected WITH
#: the reason rather than being silently unrecognised -- ``proportional``
#: calibrates hours to relative time, and ``ordinal_rank`` moves an existing
#: reading when a later checkpoint is declared.
PLACEMENT_UNPLACED = "unplaced_ordinal"
PLACEMENT_PHASE_END = "phase_end"
PLACEMENT_PROPORTIONAL = "proportional"
PLACEMENT_ORDINAL_RANK = "ordinal_rank"
PLACEMENT_SEMANTICS: frozenset[str] = frozenset(
    {
        PLACEMENT_UNPLACED,
        PLACEMENT_PHASE_END,
        PLACEMENT_PROPORTIONAL,
        PLACEMENT_ORDINAL_RANK,
    }
)
ADMISSIBLE_PLACEMENTS: frozenset[str] = frozenset(
    {PLACEMENT_UNPLACED, PLACEMENT_PHASE_END}
)

#: Horizons this repository executes a phase at. A terminal checkpoint declares
#: which one its endpoint reading belongs to, and a frame run at the other one
#: may not be read for it -- see ``read_checkpoints``.
HORIZON_DECLARED = "declared_duration"
HORIZON_CONVERGED = "converged_fixed_point"
HORIZONS: frozenset[str] = frozenset({HORIZON_DECLARED, HORIZON_CONVERGED})
HORIZON_NOT_APPLICABLE = "not_applicable"

#: What a checkpoint may license, split by whether it needs a model VALUE at
#: the checkpoint. The phase-wide diagnostics are properties of the executed
#: phase: they are evaluated over every sampled time and need no position, so
#: an unplaced checkpoint may declare them. The endpoint comparisons read a
#: value, so only a ``phase_end`` checkpoint may declare them.
#:
#: The field used to read ``within_phase_ordering;cross_analyte_same_checkpoint``
#: on both checkpoints. Both of those name a comparison AT a checkpoint, which
#: an unplaced one cannot support -- the contract was licensing a reading
#: ``read_checkpoints`` returns as ``None``. It was parsed and never validated,
#: so nothing caught the contradiction.
COMPARISON_PHASE_WIDE_SIGN = "phase_wide_sign_invariance"
COMPARISON_PHASE_WIDE_CHANGE = "phase_wide_resolved_change"
COMPARISON_ENDPOINT_VALUE = "endpoint_node_value"
COMPARISON_ENDPOINT_CROSS_ANALYTE = "endpoint_cross_analyte"
PHASE_WIDE_COMPARISONS: frozenset[str] = frozenset(
    {COMPARISON_PHASE_WIDE_SIGN, COMPARISON_PHASE_WIDE_CHANGE}
)
ENDPOINT_COMPARISONS: frozenset[str] = frozenset(
    {COMPARISON_ENDPOINT_VALUE, COMPARISON_ENDPOINT_CROSS_ANALYTE}
)
LICENSED_COMPARISONS: frozenset[str] = PHASE_WIDE_COMPARISONS | ENDPOINT_COMPARISONS

#: Verdicts. ``INDISTINGUISHABLE`` is bounded by the Monte Carlo tolerance and
#: is never evidence of equality -- see ``monte_carlo_tolerance``.
INVARIANT_GREATER = "invariant_greater"
INVARIANT_LESS = "invariant_less"
INDISTINGUISHABLE = "indistinguishable_within_monte_carlo_tolerance"
PLACEMENT_DEPENDENT = "placement_dependent"
#: Monotonicity verdicts, named for what they CERTIFY rather than for what one
#: would like them to mean. The band is a simultaneous error bound on the
#: estimate, so "every sampled later-minus-earlier difference is at least -t"
#: establishes only that the true difference is at least -2t. It is therefore a
#: diagnostic -- no decrease was resolved above Monte Carlo error -- and never a
#: proof of monotonicity or a licence for an across-checkpoint ordering.
NO_RESOLVED_DECREASE = "no_resolved_decrease_within_mc_error"
NO_RESOLVED_INCREASE = "no_resolved_increase_within_mc_error"
RESOLVED_BOTH_DIRECTIONS = "resolved_change_in_both_directions"


@dataclass(frozen=True)
class Checkpoint:
    """One declared observation position inside one protocol phase."""

    checkpoint_id: str
    phase_protocol_id: str
    phase_step_id: str
    applies_to_model_versions: tuple[str, ...]
    experimental_label: str
    source_condition_id: str
    hours_after_phase_start: float
    phase_duration_h: float
    experimental_phase_fraction: float
    ordinal_index: int
    ordinal_count: int
    placement_semantics: str
    endpoint_horizon_policy: str
    model_nodes: tuple[str, ...]
    observation_rows: tuple[str, ...]
    licensed_comparisons: tuple[str, ...]
    forbidden_uses: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    raw: dict[str, str]

    @property
    def is_phase_end(self) -> bool:
        """Declared as the phase terminus -- the only readable position.

        Read from ``placement_semantics`` rather than inferred from
        ``ordinal_index == ordinal_count``: being last among today's
        declarations is not the same claim as being the end of the phase, and
        conflating them is how a future interior checkpoint would silently
        become readable.
        """
        return self.placement_semantics == PLACEMENT_PHASE_END


@dataclass(frozen=True)
class CheckpointReading:
    """One node at one checkpoint, read where that is defined and not otherwise.

    ``value`` and ``phase_local_time`` are ``None`` for an interior checkpoint.
    That is the result, not a gap to be filled later: the observation is real
    and ordered, and the simulation has no position corresponding to it while
    physical time is uncalibrated. ``phase_min``/``phase_max`` are populated
    either way, because the phase-wide behaviour of the node needs no position.
    """

    checkpoint_id: str
    node_id: str
    placement: str
    phase_local_time: float | None
    value: float | None
    #: Extremes of this node over the WHOLE sampled phase.
    phase_min: float
    phase_max: float
    #: The horizon the frame was executed at, carried so a reading cannot be
    #: compared with one taken from the other horizon by accident.
    horizon: str

    @property
    def phase_range(self) -> float:
        return self.phase_max - self.phase_min

    @property
    def is_placed(self) -> bool:
        return self.value is not None


@dataclass(frozen=True)
class ExecutedPhase:
    """One executed phase, with the metadata that describes it attached.

    WHY THIS EXISTS. The reading and verdict functions used to take a bare
    frame plus a caller-supplied ``trajectory_count`` and ``model_version``.
    Nothing tied those to the data: evaluating a 2000-trajectory frame while
    claiming ``trajectory_count=1e9`` shrank the confidence band by two orders
    of magnitude and flipped a verdict from ``INDISTINGUISHABLE`` to
    ``INVARIANT_GREATER``. That is the same shape as the horizon label this
    module removed earlier -- a fact about the execution, asserted beside the
    execution instead of taken from it.

    So the execution metadata travel WITH the rows. :func:`executed_phase`
    builds this from a :class:`SequentialTimeline`, which already carries all of
    it, and nothing downstream accepts the parts separately. A synthetic test
    may construct one directly; a production caller has nothing left to assert.
    """

    protocol_id: str
    step_id: str
    model_version: str
    trajectory_count: int
    seed: int
    #: Measured, never declared: which of the repository's two horizons this
    #: run actually executed at.
    horizon: str
    declared_duration: float
    executed_duration: float
    #: The phase's rows, time-ordered.
    rows: Any

    @property
    def sampled_points(self) -> int:
        return len(self.rows)


@dataclass(frozen=True)
class ValidationReport:
    errors: list[str]
    checks: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _split(value: str) -> tuple[str, ...]:
    return tuple(token.strip() for token in value.split(";") if token.strip())


def _checkpoint_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_CHECKPOINT_PATH


def load_checkpoints(root: Path | None = None) -> list[Checkpoint]:
    """Load ``config/observation_checkpoints.tsv``.

    Structural loading only: schema conformance is asserted here because a
    malformed row must not reach an evaluator, while the policy questions --
    whether a placement rule is admissible, whether an order matches the
    experiment -- belong to :func:`validate_checkpoints`.
    """
    path = _checkpoint_path(root)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = tuple(reader.fieldnames or ())
        if fieldnames != CHECKPOINT_COLUMNS:
            raise ValueError(
                f"{DEFAULT_CHECKPOINT_PATH} columns are {fieldnames}, expected "
                f"{CHECKPOINT_COLUMNS}"
            )
        checkpoints: list[Checkpoint] = []
        for row in reader:
            checkpoints.append(
                Checkpoint(
                    checkpoint_id=row["checkpoint_id"],
                    phase_protocol_id=row["phase_protocol_id"],
                    phase_step_id=row["phase_step_id"],
                    applies_to_model_versions=_split(row["applies_to_model_versions"]),
                    experimental_label=row["experimental_label"],
                    source_condition_id=row["source_condition_id"],
                    hours_after_phase_start=float(row["hours_after_phase_start"]),
                    phase_duration_h=float(row["phase_duration_h"]),
                    experimental_phase_fraction=float(
                        row["experimental_phase_fraction"]
                    ),
                    ordinal_index=int(row["ordinal_index"]),
                    ordinal_count=int(row["ordinal_count"]),
                    placement_semantics=row["placement_semantics"],
                    endpoint_horizon_policy=row["endpoint_horizon_policy"],
                    model_nodes=_split(row["model_nodes"]),
                    observation_rows=_split(row["observation_rows"]),
                    licensed_comparisons=_split(row["licensed_comparisons"]),
                    forbidden_uses=_split(row["forbidden_uses"]),
                    evidence_ids=_split(row["evidence_ids"]),
                    raw=dict(row),
                )
            )
    return checkpoints


def checkpoints_for_phase(
    checkpoints: list[Checkpoint], phase_protocol_id: str
) -> list[Checkpoint]:
    """Checkpoints of one phase, in declared experimental order."""
    selected = [
        checkpoint
        for checkpoint in checkpoints
        if checkpoint.phase_protocol_id == phase_protocol_id
    ]
    return sorted(selected, key=lambda checkpoint: checkpoint.ordinal_index)


def validate_checkpoints(
    checkpoints: list[Checkpoint],
    *,
    known_protocol_steps: set[tuple[str, str]] | None = None,
    calibrated_physical_time: bool = False,
) -> ValidationReport:
    """Policy checks a malformed or over-claiming declaration must fail.

    ``calibrated_physical_time`` is passed in rather than read here so a caller
    cannot be surprised by which file supplied it; the repository's value lives
    in ``config/calibration.yaml`` and is ``false``.
    """
    errors: list[str] = []
    checks: list[str] = []

    seen: set[str] = set()
    for checkpoint in checkpoints:
        if checkpoint.checkpoint_id in seen:
            errors.append(f"duplicate checkpoint_id {checkpoint.checkpoint_id!r}")
        seen.add(checkpoint.checkpoint_id)
    checks.append("checkpoint_ids_unique")

    for checkpoint in checkpoints:
        placement = checkpoint.placement_semantics
        if placement not in PLACEMENT_SEMANTICS:
            errors.append(
                f"{checkpoint.checkpoint_id}: unknown placement_semantics {placement!r}"
            )
        elif placement == PLACEMENT_PROPORTIONAL and not calibrated_physical_time:
            errors.append(
                f"{checkpoint.checkpoint_id}: placement_semantics="
                f"{PLACEMENT_PROPORTIONAL!r} places a reading at "
                "hours/phase_hours of the simulated duration, which asserts a "
                "fixed hours-per-relative-time factor. That is a physical-time "
                "calibration and config/calibration.yaml records "
                "calibrated_physical_time: false"
            )
        elif placement == PLACEMENT_ORDINAL_RANK:
            errors.append(
                f"{checkpoint.checkpoint_id}: placement_semantics="
                f"{PLACEMENT_ORDINAL_RANK!r} places the k-th of n checkpoints at "
                "k/n of the phase, so declaring a later checkpoint MOVES this "
                "one -- the day-3 reading would slide from 1/2 of the phase to "
                "1/4 when 48 h and 72 h are declared. An observation may not "
                "change because another observation was declared"
            )
    checks.append("placement_semantics_admissible")

    for checkpoint in checkpoints:
        policy = checkpoint.endpoint_horizon_policy
        if checkpoint.is_phase_end:
            if policy not in HORIZONS:
                errors.append(
                    f"{checkpoint.checkpoint_id}: a {PLACEMENT_PHASE_END!r} "
                    f"checkpoint must declare endpoint_horizon_policy in "
                    f"{sorted(HORIZONS)}, got {policy!r}. The frame supplied at "
                    "read time must not be what decides which horizon an "
                    "endpoint belongs to"
                )
            if checkpoint.hours_after_phase_start != checkpoint.phase_duration_h:
                errors.append(
                    f"{checkpoint.checkpoint_id}: declared as the phase end but "
                    f"sampled at {checkpoint.hours_after_phase_start} h of a "
                    f"{checkpoint.phase_duration_h} h phase"
                )
        elif policy != HORIZON_NOT_APPLICABLE:
            errors.append(
                f"{checkpoint.checkpoint_id}: only a {PLACEMENT_PHASE_END!r} "
                f"checkpoint may declare an endpoint_horizon_policy, got "
                f"{policy!r}. An interior checkpoint is read at no horizon "
                "because it is read at no position"
            )
    checks.append("endpoint_horizon_policy_declared")

    for checkpoint in checkpoints:
        declared = set(checkpoint.licensed_comparisons)
        if not declared:
            errors.append(
                f"{checkpoint.checkpoint_id}: licensed_comparisons is empty; a "
                "checkpoint that licenses nothing is a row with no consumer"
            )
        unknown = sorted(declared - LICENSED_COMPARISONS)
        if unknown:
            errors.append(
                f"{checkpoint.checkpoint_id}: unknown licensed_comparisons "
                f"{unknown}; known values are {sorted(LICENSED_COMPARISONS)}"
            )
        needs_value = sorted(declared & ENDPOINT_COMPARISONS)
        if needs_value and not checkpoint.is_phase_end:
            errors.append(
                f"{checkpoint.checkpoint_id}: licenses {needs_value}, which "
                "reads a model value AT the checkpoint, but its placement is "
                f"{checkpoint.placement_semantics!r} and it has no value. A "
                "machine-readable contract may not license what the reader "
                "returns as None"
            )
    checks.append("licensed_comparisons_match_placement")

    for checkpoint in checkpoints:
        if not 0.0 < checkpoint.hours_after_phase_start <= checkpoint.phase_duration_h:
            errors.append(
                f"{checkpoint.checkpoint_id}: hours_after_phase_start "
                f"{checkpoint.hours_after_phase_start} is outside "
                f"(0, {checkpoint.phase_duration_h}]"
            )
        expected = checkpoint.hours_after_phase_start / checkpoint.phase_duration_h
        if abs(checkpoint.experimental_phase_fraction - expected) > 1e-9:
            errors.append(
                f"{checkpoint.checkpoint_id}: experimental_phase_fraction "
                f"{checkpoint.experimental_phase_fraction} does not equal "
                f"hours_after_phase_start/phase_duration_h ({expected})"
            )
    checks.append("experimental_timing_self_consistent")

    by_phase: dict[str, list[Checkpoint]] = {}
    for checkpoint in checkpoints:
        by_phase.setdefault(checkpoint.phase_protocol_id, []).append(checkpoint)
    for phase_protocol_id, phase_checkpoints in by_phase.items():
        ordered = sorted(phase_checkpoints, key=lambda c: c.ordinal_index)
        indices = [checkpoint.ordinal_index for checkpoint in ordered]
        if indices != list(range(1, len(ordered) + 1)):
            errors.append(
                f"{phase_protocol_id}: ordinal_index must be 1..n with no gaps, "
                f"got {indices}"
            )
        for checkpoint in ordered:
            if checkpoint.ordinal_count != len(ordered):
                errors.append(
                    f"{checkpoint.checkpoint_id}: ordinal_count "
                    f"{checkpoint.ordinal_count} but the phase declares "
                    f"{len(ordered)} checkpoints"
                )
        hours = [checkpoint.hours_after_phase_start for checkpoint in ordered]
        if any(later <= earlier for earlier, later in pairwise(hours)):
            errors.append(
                f"{phase_protocol_id}: ordinal order does not follow experimental "
                f"time (hours {hours}). The order IS the claim; a checkpoint may "
                "never be reordered to change a reading"
            )
        durations = {checkpoint.phase_duration_h for checkpoint in ordered}
        if len(durations) > 1:
            errors.append(
                f"{phase_protocol_id}: checkpoints disagree on phase_duration_h "
                f"({sorted(durations)})"
            )
        terminal = [c for c in ordered if c.is_phase_end]
        if len(terminal) > 1:
            errors.append(
                f"{phase_protocol_id}: {len(terminal)} checkpoints declare "
                f"{PLACEMENT_PHASE_END!r}; a phase has one end"
            )
        if terminal and terminal[0] is not ordered[-1]:
            errors.append(
                f"{phase_protocol_id}: {terminal[0].checkpoint_id} declares "
                f"{PLACEMENT_PHASE_END!r} but is not the last checkpoint in "
                "experimental order"
            )
    checks.append("phase_ordinals_follow_experimental_time")

    if known_protocol_steps is not None:
        for checkpoint in checkpoints:
            key = (checkpoint.phase_protocol_id, checkpoint.phase_step_id)
            if key not in known_protocol_steps:
                errors.append(
                    f"{checkpoint.checkpoint_id}: {key} is not a declared protocol "
                    "step. A checkpoint observes an EXISTING phase and must never "
                    "imply a new protocol arm"
                )
        checks.append("checkpoints_observe_existing_phases")

    return ValidationReport(errors=errors, checks=checks)


def phase_frame(frame: Any, *, protocol_id: str, step_id: str) -> Any:
    """The rows of one executed phase, in time order.

    One phase is one continuous trajectory. Selecting rows from it is the whole
    of "reading a checkpoint": nothing is re-run, re-initialised or resampled,
    which is why this module cannot reset a state even by accident.
    """
    selected = frame[
        (frame["protocol_id"] == protocol_id) & (frame["step_id"] == step_id)
    ]
    if len(selected) == 0:
        raise ValueError(f"timeline has no rows for phase {protocol_id}/{step_id}")
    return selected.sort_values("phase_local_time")


def executed_phase(
    timeline: Any,
    *,
    protocol_id: str,
    step_id: str | None = None,
    root: Path | None = None,
) -> ExecutedPhase:
    """Bind one phase's rows to the metadata of the run that produced them.

    ``timeline`` is a :class:`dt_adoc.simulation.timeline.SequentialTimeline`,
    which already records ``model_version``, ``trajectory_count``, ``seed`` and
    each phase's declared and executed durations. Taking them from there rather
    than from arguments is the point: none of them can then disagree with the
    frame, because none of them is supplied twice.

    The horizon is MEASURED from the executed duration against the declared one
    and ``CONVERGED_PHASE_HORIZON``, and an extent matching neither is refused
    rather than guessed at.
    """
    from dt_adoc.concordance.simulate import CONVERGED_PHASE_HORIZON

    phases = [phase for phase in timeline.phases if phase.protocol_id == protocol_id]
    if step_id is not None:
        phases = [phase for phase in phases if phase.step_id == step_id]
    if len(phases) != 1:
        raise ValueError(
            f"timeline has {len(phases)} phase(s) for {protocol_id}"
            + (f"/{step_id}" if step_id else "")
            + "; expected exactly one"
        )
    phase = phases[0]

    declared = float(phase.declared_duration)
    executed = float(phase.relative_duration)
    if abs(executed - declared) < 1e-9:
        horizon = HORIZON_DECLARED
    elif abs(executed - float(CONVERGED_PHASE_HORIZON)) < 1e-9:
        horizon = HORIZON_CONVERGED
    else:
        raise ValueError(
            f"phase {protocol_id}/{phase.step_id} ran for {executed} relative "
            f"units, which is neither its declared duration ({declared}) nor "
            f"the converged horizon ({CONVERGED_PHASE_HORIZON}); this "
            "repository has no other horizon and an endpoint may not be read "
            "against an unrecognised one"
        )

    return ExecutedPhase(
        protocol_id=protocol_id,
        step_id=phase.step_id,
        model_version=timeline.model_version,
        trajectory_count=int(timeline.trajectory_count),
        seed=int(timeline.seed),
        horizon=horizon,
        declared_duration=declared,
        executed_duration=executed,
        rows=phase_frame(
            timeline.frame, protocol_id=protocol_id, step_id=phase.step_id
        ),
    )


def read_checkpoints(
    phase: ExecutedPhase,
    checkpoints: list[Checkpoint],
    *,
    node_ids: tuple[str, ...] | None = None,
) -> list[CheckpointReading]:
    """Read declared checkpoints against an executed phase.

    Everything about the run -- which model, how many trajectories, which
    horizon -- comes from ``phase`` and is therefore the run's own account of
    itself. A terminal checkpoint whose ``endpoint_horizon_policy`` disagrees
    with the measured horizon is refused, as is a checkpoint that does not
    declare this model version.

    An interior checkpoint yields a reading with no time and no value. It is not
    a failure and not a placeholder: while physical time is uncalibrated the
    simulation has no position that corresponds to "24 h into the phase", and
    inventing one is the defect this signature exists to prevent. The
    phase-wide extremes are still reported, because they need no position.
    """
    if not checkpoints:
        return []
    declared_phases = {
        (checkpoint.phase_protocol_id, checkpoint.phase_step_id)
        for checkpoint in checkpoints
    }
    if len(declared_phases) != 1:
        raise ValueError(f"checkpoints span several phases: {sorted(declared_phases)}")
    if (phase.protocol_id, phase.step_id) not in declared_phases:
        raise ValueError(
            f"checkpoints describe {min(declared_phases)} but the "
            f"executed phase is {(phase.protocol_id, phase.step_id)}"
        )

    rows = phase.rows
    times = [float(value) for value in rows["phase_local_time"]]

    readings: list[CheckpointReading] = []
    for checkpoint in sorted(checkpoints, key=lambda c: c.ordinal_index):
        if (
            checkpoint.applies_to_model_versions
            and phase.model_version not in checkpoint.applies_to_model_versions
        ):
            raise ValueError(
                f"{checkpoint.checkpoint_id} declares "
                f"applies_to_model_versions={list(checkpoint.applies_to_model_versions)} "
                f"and this phase ran {phase.model_version!r}; a checkpoint is "
                "declared against the models whose trajectory it describes, and "
                "reading it against another is not a judgement call"
            )
        if (
            checkpoint.is_phase_end
            and checkpoint.endpoint_horizon_policy != phase.horizon
        ):
            raise ValueError(
                f"{checkpoint.checkpoint_id} declares "
                f"endpoint_horizon_policy={checkpoint.endpoint_horizon_policy!r} "
                f"but this phase was MEASURED to have executed at "
                f"{phase.horizon!r}; the two runs end in different states and "
                "must not be conflated"
            )
        for node_id in node_ids or checkpoint.model_nodes:
            column = rows[node_id]
            placed = checkpoint.is_phase_end
            readings.append(
                CheckpointReading(
                    checkpoint_id=checkpoint.checkpoint_id,
                    node_id=node_id,
                    placement=checkpoint.placement_semantics,
                    phase_local_time=times[-1] if placed else None,
                    value=float(column.iloc[-1]) if placed else None,
                    phase_min=float(column.min()),
                    phase_max=float(column.max()),
                    horizon=phase.horizon,
                )
            )
    return readings


def paired_difference_tolerance(
    trajectory_count: int,
    *,
    comparisons: int,
    family_error: float = 0.0027,
) -> float:
    """Family-wise band for a PAIRED difference of two node probabilities.

    WHAT THE ESTIMATOR ACTUALLY IS. ``P(node = ON)`` is the mean of an indicator
    over ``trajectory_count`` trajectories, so the difference of two such means
    computed from the SAME run is the mean of the per-trajectory difference
    ``D = A - B``, with ``D`` in ``[-1, 1]``. The quantity is already paired; it
    was only ever written as a difference of two marginals. The same holds for
    one node at two times, which is what the monotonicity verdict compares.

    WHY THE PREVIOUS BOUND WAS WRONG. It used ``z * sqrt(2) * 0.5 / sqrt(N)``,
    the normal-approximation band for the difference of two INDEPENDENT
    estimates. Two nodes driven by one network and estimated from one set of
    trajectories are not independent, and their covariance is **not
    identifiable from marginal ``nodes_probtraj`` curves** -- those give
    ``P(A)`` and ``P(B)`` and never ``P(A, B)`` -- so the correlation can be
    neither assumed nor measured from what this module is given.

    WHAT REPLACES IT. Hoeffding's inequality on the i.i.d. bounded variables
    ``D_i``: for a mean of ``N`` variables in a range of width ``R = 2``,
    ``P(|D_bar - E D| >= t) <= 2 exp(-2 N t^2 / R^2)``. Setting the
    right-hand side to ``family_error / comparisons`` and solving gives
    ``t = sqrt(2 ln(2 * comparisons / family_error) / N)``. The within-trajectory
    dependence between ``A`` and ``B`` never enters, because the bound is taken
    on ``D`` directly. It is wider than the independent-sample band, which is
    the conservative direction for asserting a difference.

    WHAT IT IS A BOUND ON, which decides what a verdict may say. It bounds the
    error of the ESTIMATE simultaneously over ``comparisons`` comparisons:
    under that event every ``|d_hat - d_true| <= t``. So ``d_hat > t`` certifies
    ``d_true > 0``, while ``d_hat >= -t`` certifies only ``d_true >= -2t``. The
    verdicts below are named for which of those they have.

    ASSUMPTIONS, stated because they are what makes it valid: the trajectories
    are independent of one another (MaBoSS runs them so); the two quantities are
    read from the SAME run, so the pairing is real -- comparing marginals from
    two different runs breaks it and this bound would not apply; and
    ``comparisons`` counts every comparison the verdict makes, which is why the
    verdict functions compute it themselves rather than accepting a band.
    """
    if trajectory_count <= 0:
        raise ValueError("trajectory_count must be positive")
    if comparisons <= 0:
        raise ValueError("comparisons must be positive")
    if not 0.0 < family_error < 1.0:
        raise ValueError("family_error must lie in (0, 1)")
    return sqrt(2.0 * log(2.0 * comparisons / family_error) / float(trajectory_count))


def ordering_verdict(
    phase: ExecutedPhase,
    *,
    node_a: str,
    node_b: str,
    family_error: float = 0.0027,
) -> str:
    """Whether ``node_a > node_b`` holds everywhere in the phase, or nowhere.

    Evaluated at every sampled time, not at a placed checkpoint, so the answer
    cannot be an artefact of where a checkpoint was put. ``PLACEMENT_DEPENDENT``
    is the honest verdict when the sign changes: the comparison is real but its
    answer depends on where one looks, and under
    ``calibrated_physical_time: false`` the repository cannot say where that is.

    WHAT EACH VERDICT CERTIFIES under the simultaneous event:

    * ``INVARIANT_GREATER`` / ``INVARIANT_LESS`` -- every estimate is outside
      the band in one direction, so the TRUE difference has that sign at every
      sampled time. A real claim.
    * ``INDISTINGUISHABLE`` -- every estimate is inside the band, so the true
      difference is within ``2t``. **Not** equality, and never evidence of it.
    * ``PLACEMENT_DEPENDENT`` -- neither holds.

    The band comes from ``phase``: the trajectory count is the run's, and the
    comparison count is the number of sampled times this call actually
    compares. Neither is a caller's to state.
    """
    rows = phase.rows
    differences = [
        float(a) - float(b) for a, b in zip(rows[node_a], rows[node_b], strict=True)
    ]
    tolerance = paired_difference_tolerance(
        phase.trajectory_count,
        comparisons=len(differences),
        family_error=family_error,
    )
    if all(difference > tolerance for difference in differences):
        return INVARIANT_GREATER
    if all(difference < -tolerance for difference in differences):
        return INVARIANT_LESS
    if all(abs(difference) <= tolerance for difference in differences):
        return INDISTINGUISHABLE
    return PLACEMENT_DEPENDENT


def monotonicity_verdict(
    phase: ExecutedPhase,
    *,
    node_id: str,
    family_error: float = 0.0027,
) -> str:
    """Whether any decrease -- or any increase -- is resolved above MC error.

    THE RELATION IS EVERY ORDERED PAIR. An earlier version compared adjacent
    steps only, which is not transitive under a band: decreases each smaller
    than the band accumulate, and a series falling from 1.0 to 0.002 came back
    as "non-decreasing". Every ordered pair is what is tested now, computed in
    one pass against the running extremes rather than in O(n^2), and the band is
    recomputed for the ``n(n-1)/2`` pairs that implies rather than the ``n-1``
    adjacent steps it replaced.

    WHAT IT DOES NOT SAY, and why the verdicts are named as they are. The band
    bounds the error of the estimate, so "every later-minus-earlier estimate is
    at least ``-t``" establishes only that the true difference is at least
    ``-2t``. It does **not** establish that the series is non-decreasing, and
    this function no longer says that it does. Certifying ``d_true >= 0`` would
    require every ordered estimate to exceed ``+t``, which a saturating
    trajectory cannot meet and which nothing here needs: the interior checkpoint
    is unplaced, so no across-checkpoint model comparison is licensed at all.
    What is left is a diagnostic -- no decrease (or no increase) was resolved
    above Monte Carlo error -- and it must not be read as more.
    """
    values = [float(value) for value in phase.rows[node_id]]
    count = len(values)
    if count < 2:
        raise ValueError(
            f"phase {phase.protocol_id}/{phase.step_id} has {count} sampled "
            "time(s); a monotonicity diagnostic needs at least two"
        )
    tolerance = paired_difference_tolerance(
        phase.trajectory_count,
        comparisons=count * (count - 1) // 2,
        family_error=family_error,
    )

    resolved_decrease = False
    resolved_increase = False
    running_max = values[0]
    running_min = values[0]
    for value in values[1:]:
        # The largest earlier value is the binding one for a decrease and the
        # smallest for an increase, so the running extremes decide every
        # ordered pair ending here in constant time.
        if value < running_max - tolerance:
            resolved_decrease = True
        if value > running_min + tolerance:
            resolved_increase = True
        running_max = max(running_max, value)
        running_min = min(running_min, value)

    if resolved_decrease and resolved_increase:
        return RESOLVED_BOTH_DIRECTIONS
    if resolved_decrease:
        return NO_RESOLVED_INCREASE
    return NO_RESOLVED_DECREASE
