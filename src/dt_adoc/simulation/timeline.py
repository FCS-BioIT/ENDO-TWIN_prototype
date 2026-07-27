"""Concatenate sequential MaBoSS protocol phases into a single timeline.

The timeline exists so downstream consumers (reports, animations) can read one
ordered table instead of re-deriving the continuation chain. It executes the
real protocol lineage with the real transferred continuation state; nothing is
recomputed, interpolated, or synthesised.

Semantics that must not be restated loosely elsewhere:

* Node values are ``P(node = ON)`` across simulated MaBoSS trajectories. They
  are not concentrations, expression levels, secretion amounts, or fluxes.
* Time is MaBoSS relative time. No validated mapping to hours exists, so no
  conversion is offered here.
* ``IN_*`` values are deterministic protocol settings resolved from the
  condition cfg and the protocol step, not simulated quantities. MaBoSS keeps
  input nodes internal, so they never appear in a node trajectory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from dt_adoc.model.runtime import resolve_model
from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.protocols.runner import expanded_protocol_sequence
from dt_adoc.protocols.schema import ProtocolDefinition, ProtocolStep

DEFAULT_TERMINAL_PROTOCOL = "adhesion_challenge_washout"
PROBABILITY_TOLERANCE = 1e-9

_ISTATE_PATTERN = re.compile(
    r"^\s*(?P<node>[A-Za-z_][A-Za-z0-9_]*)\.istate\s*=\s*(?P<value>TRUE|FALSE)\s*;",
    re.MULTILINE,
)

_PHASE_LABEL_OVERRIDES = {
    "basal": "Basal maternal state",
    "basal_maternal": "Basal maternal state",
    "e2_priming": "E2 priming",
    "e2_primed_maternal": "E2 priming",
    "hormone_treated": "Hormone conditioning",
    "hormone_treated_maternal": "Hormone conditioning",
    "hormone_treated_mifepristone": "Mifepristone challenge",
    "hormone_treated_anti_spp1": "Anti-SPP1 challenge",
    "washout": "Washout",
    "adhesion_challenge_basal": "Embryo adhesion challenge (basal)",
    "adhesion_challenge_hormone_treated": "Embryo adhesion challenge",
    "adhesion_challenge_hormone_treated_mifepristone": (
        "Embryo adhesion challenge + mifepristone"
    ),
    "adhesion_challenge_hormone_treated_anti_spp1": (
        "Embryo adhesion challenge + anti-SPP1"
    ),
    "adhesion_challenge_excess_er_stress": "Embryo adhesion challenge + ER stress",
    "adhesion_challenge_high_ecm_stiffness": "Embryo adhesion challenge + stiff ECM",
    "adhesion_challenge_washout": "Washout after adhesion challenge",
}


def phase_label(protocol_id: str) -> str:
    """Human-readable label for a protocol phase."""
    override = _PHASE_LABEL_OVERRIDES.get(protocol_id)
    if override is not None:
        return override
    return protocol_id.replace("_", " ").capitalize()


def resolved_input_states(
    protocol: ProtocolDefinition,
    step: ProtocolStep,
    *,
    root: Path | None = None,
) -> dict[str, bool]:
    """Effective deterministic input states for one protocol step.

    The condition cfg declares a baseline istate for every input node; the
    protocol step overrides a subset. Both are read from the repository's own
    source files so the reported inputs cannot drift from what was simulated.
    """
    active_root = root or Path(__file__).resolve().parents[3]
    cfg_path = active_root / protocol.condition_cfg
    states: dict[str, bool] = {}
    for match in _ISTATE_PATTERN.finditer(cfg_path.read_text(encoding="utf-8")):
        node_id = match.group("node")
        if node_id.startswith("IN_"):
            states[node_id] = match.group("value") == "TRUE"
    states.update({key: bool(value) for key, value in step.input_states.items()})
    return states


@dataclass(frozen=True)
class TimelinePhase:
    """One executed protocol step positioned on the global timeline."""

    phase_index: int
    protocol_id: str
    step_id: str
    label: str
    relative_duration: float
    #: The value declared in config/protocols.yaml, retained even when
    #: ``relative_duration`` is a converged-horizon override, so a figure can
    #: mark where the committed policy would have read the endpoint.
    declared_duration: float
    phase_start: float
    phase_end: float
    continuation_from: str | None
    continuation_applied: bool
    input_states: dict[str, bool] = field(default_factory=dict)
    #: Library interventions the step declares (``ProtocolStep.interventions``).
    #: Kept apart from ``input_states``: an intervention is not an input node,
    #: and from v0.6.0 on it has no ``IN_*`` node at all, so a figure or table
    #: that read only ``input_states`` would lose it.
    interventions: tuple[str, ...] = ()
    #: Repo-relative condition cfg the step was built from.
    condition_cfg: str = ""
    #: The exact merged cfg MaBoSS executed for this step, read before its
    #: temporary directory can be released, so a figure can publish it.
    executed_cfg_text: str = ""
    #: ``ConditionRunResult.executed_network``: what MaBoSS actually loaded.
    executed_network: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SequentialTimeline:
    """Concatenated node trajectories across a real protocol lineage."""

    model_id: str
    model_version: str
    seed: int
    trajectory_count: int
    terminal_protocol: str
    protocol_ids: tuple[str, ...]
    phases: tuple[TimelinePhase, ...]
    node_ids: tuple[str, ...]
    input_ids: tuple[str, ...]
    frame: Any

    @property
    def total_duration(self) -> float:
        return self.phases[-1].phase_end if self.phases else 0.0

    def phase_at(self, global_time: float) -> TimelinePhase:
        """Phase active at ``global_time`` (later phase wins on a boundary)."""
        for phase in reversed(self.phases):
            if global_time >= phase.phase_start:
                return phase
        return self.phases[0]


def reference_sequence(
    *,
    model_version: str,
    terminal_protocol: str = DEFAULT_TERMINAL_PROTOCOL,
    root: Path | None = None,
) -> tuple[str, ...]:
    """Ordered protocol lineage terminating at ``terminal_protocol``.

    The order is the model's declared ``continuation_from`` chain, not a
    narrative ordering chosen for the figure.
    """
    lineage = expanded_protocol_sequence(
        terminal_protocol,
        root,
        model_version=model_version,
    )
    ordered: list[str] = []
    for row in lineage:
        protocol_id = str(row["protocol_id"])
        if protocol_id not in ordered:
            ordered.append(protocol_id)
    return tuple(ordered)


def build_sequential_timeline(
    *,
    model_version: str,
    terminal_protocol: str = DEFAULT_TERMINAL_PROTOCOL,
    root: Path | None = None,
    seed: int = 1,
    trajectory_count: int = 2000,
    rule_variant_selection: dict[str, str] | None = None,
    phase_horizon: float | None = None,
) -> SequentialTimeline:
    """Execute the protocol lineage and concatenate its node trajectories.

    Each phase after the first is initialised from the preceding phase's actual
    transferred continuation state, using the same ``protocol_continuation``
    machinery the structural smoke uses.
    """
    # Imported lazily: this module is importable without a MaBoSS runtime, and
    # the CLI relies on that for its non-simulation subcommands.
    import pandas as pd

    from dt_adoc.simulation.runner import (
        ProtocolRunResult,
        nodes_probtraj_table,
        protocol_continuation,
        run_protocol,
    )

    active_root = root or Path(__file__).resolve().parents[3]
    model_spec = resolve_model(model_version, active_root)
    protocol_ids = reference_sequence(
        model_version=model_version,
        terminal_protocol=terminal_protocol,
        root=active_root,
    )

    phases: list[TimelinePhase] = []
    tables: list[Any] = []
    protocol_results: dict[str, ProtocolRunResult] = {}
    phase_index = 0
    elapsed = 0.0

    for protocol_id in protocol_ids:
        protocol = get_protocol(protocol_id, active_root, model_version=model_version)
        continuation = None
        if protocol.continuation_from is not None:
            if protocol.continuation_from not in protocol_results:
                raise ValueError(
                    f"Protocol {protocol_id} continues from "
                    f"{protocol.continuation_from}, which is not part of the "
                    f"lineage for {terminal_protocol}."
                )
            continuation = protocol_continuation(
                protocol_id,
                protocol_results[protocol.continuation_from],
                model_version=model_version,
                root=active_root,
            )
        run = run_protocol(
            protocol_id,
            model_version=model_version,
            root=active_root,
            continuation=continuation,
            rule_variant_selection=rule_variant_selection,
            seed=seed,
            sample_count=trajectory_count,
            phase_horizon=phase_horizon,
        )
        protocol_results[protocol_id] = run

        for step_index, step in enumerate(protocol.steps):
            step_result = run.step_results[step_index]
            declared_duration = float(step.relative_duration)
            executed_duration = (
                declared_duration if phase_horizon is None else float(phase_horizon)
            )
            phase_start = elapsed
            phase_end = phase_start + executed_duration
            inputs = resolved_input_states(protocol, step, root=active_root)
            phases.append(
                TimelinePhase(
                    phase_index=phase_index,
                    protocol_id=protocol_id,
                    step_id=step.step_id,
                    label=phase_label(protocol_id),
                    relative_duration=executed_duration,
                    declared_duration=declared_duration,
                    phase_start=phase_start,
                    phase_end=phase_end,
                    continuation_from=protocol.continuation_from,
                    continuation_applied=run.step_initializations[step_index]
                    is not None,
                    input_states=inputs,
                    interventions=tuple(step.interventions),
                    condition_cfg=str(protocol.condition_cfg),
                    executed_cfg_text=step_result.merged_cfg.read_text(
                        encoding="utf-8"
                    ),
                    executed_network=dict(step_result.executed_network),
                )
            )
            table = nodes_probtraj_table(
                step_result.nodes_probtraj,
                protocol_id=protocol_id,
                step_id=step.step_id,
                phase_index=phase_index,
            )
            table.insert(1, "phase_local_time", table["time"])
            table.insert(1, "global_time", table["time"] + phase_start)
            table.insert(2, "phase_label", phase_label(protocol_id))
            table["phase_start"] = phase_start
            table["phase_end"] = phase_end
            for node_id, state in inputs.items():
                table[node_id] = 1.0 if state else 0.0
            tables.append(table.drop(columns=["time"]))
            phase_index += 1
            elapsed = phase_end

    frame = pd.concat(tables, ignore_index=True, sort=False)
    node_ids = tuple(
        column
        for column in frame.columns
        if column not in _METADATA_COLUMNS and not column.startswith("IN_")
    )
    input_ids = tuple(column for column in frame.columns if column.startswith("IN_"))
    _validate_timeline_frame(frame, node_ids=node_ids)
    return SequentialTimeline(
        model_id=model_spec.model_id,
        model_version=model_spec.model_version,
        seed=seed,
        trajectory_count=trajectory_count,
        terminal_protocol=terminal_protocol,
        protocol_ids=protocol_ids,
        phases=tuple(phases),
        node_ids=node_ids,
        input_ids=input_ids,
        frame=frame,
    )


_METADATA_COLUMNS = frozenset(
    {
        "global_time",
        "phase_local_time",
        "phase_label",
        "protocol_id",
        "step_id",
        "phase_index",
        "phase_start",
        "phase_end",
    }
)


def _validate_timeline_frame(frame: Any, *, node_ids: tuple[str, ...]) -> None:
    """Fail loudly rather than animate a malformed trajectory."""
    if frame.empty:
        raise ValueError("Sequential timeline produced no rows.")
    times = frame["global_time"].tolist()
    if any(later < earlier for earlier, later in pairwise(times)):
        raise ValueError("Sequential timeline global_time is not monotonic.")
    for node_id in node_ids:
        values = frame[node_id]
        if not values.notna().all():
            raise ValueError(f"Node {node_id} has non-finite probabilities.")
        low = float(values.min())
        high = float(values.max())
        if low < -PROBABILITY_TOLERANCE or high > 1.0 + PROBABILITY_TOLERANCE:
            raise ValueError(
                f"Node {node_id} has probabilities outside [0, 1]: [{low}, {high}]."
            )
