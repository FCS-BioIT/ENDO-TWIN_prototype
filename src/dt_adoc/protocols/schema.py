"""Typed protocol metadata for the conservative Phase 1 DT_ADOC workflow."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContinuationDefinition:
    mode: str
    memory_policy: str
    memory_nodes: tuple[str, ...]
    probability_cutoff: float


@dataclass(frozen=True)
class ProtocolStep:
    step_id: str
    relative_order: int
    relative_duration: float
    duration_note: str
    input_states: dict[str, bool]
    #: Library interventions active in this step, as intervention ids in
    #: canonical (sorted) order. Empty when the step declares none, whether the
    #: field is absent or an empty list. The library says what each one does;
    #: this says only when it is active. See
    #: ``docs/protocol_intervention_timing.md``.
    interventions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProtocolDefinition:
    protocol_id: str
    protocol_class: str
    model_version: str
    condition_cfg: str
    comparator_role: str
    steps: tuple[ProtocolStep, ...]
    evidence_ids: tuple[str, ...]
    notes: str
    continuation_from: str | None = None
    continuation: ContinuationDefinition | None = None
