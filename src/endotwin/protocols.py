"""Experimental protocols: sequential hormonal phases, perturbations and timing.

Protocols live in ``endotwin/config/protocols.yaml`` and interventions in
``endotwin/config/interventions.tsv``. A condition is an ordered list of phases;
each phase fixes every experimental input (unlisted inputs are OFF) and may
apply interventions. The timing of a perturbation is therefore explicit: it is
the phase in which an input or intervention appears.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from endotwin.model import Model, read_tsv
from endotwin.paths import CONFIG


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Intervention:
    intervention_id: str
    node: str
    forced_state: int
    compartment: str
    kind: str


@dataclass(frozen=True)
class Phase:
    phase_id: str
    inputs: dict[str, int]
    interventions: tuple[str, ...]
    relative_duration: float
    physical_duration: str


@dataclass(frozen=True)
class Condition:
    condition_id: str
    description: str
    phases: tuple[Phase, ...]

    def phase(self, phase_id: str) -> Phase:
        for phase in self.phases:
            if phase.phase_id == phase_id:
                return phase
        raise KeyError(f"{self.condition_id} has no phase {phase_id}")


@dataclass(frozen=True)
class Comparison:
    comparison_id: str
    question: str
    perturbed: str
    control: str
    phase: str
    phase_perturbed: str


@dataclass(frozen=True)
class ProtocolSet:
    model_version: str
    conditions: dict[str, Condition]
    comparisons: dict[str, Comparison]
    interventions: dict[str, Intervention]
    source: Path


def load_interventions(
    model: Model, path: Path | None = None
) -> dict[str, Intervention]:
    path = path or CONFIG / "interventions.tsv"
    out: dict[str, Intervention] = {}
    for row in read_tsv(path):
        if row["node"] not in model.rules:
            raise ProtocolError(
                f"intervention {row['intervention_id']} targets unknown node"
            )
        out[row["intervention_id"]] = Intervention(
            intervention_id=row["intervention_id"],
            node=row["node"],
            forced_state=int(row["forced_state"]),
            compartment=row["compartment"],
            kind=row["kind"],
        )
    return out


def _phase(
    model: Model,
    phase_id: str,
    spec: Mapping[str, object],
    overlay: Mapping[str, object] | None,
    default_duration: float,
    interventions: Mapping[str, Intervention],
) -> Phase:
    inputs = {n: 0 for n in model.inputs}
    for source in (spec.get("inputs") or {}, (overlay or {}).get("inputs") or {}):
        for node, value in dict(source).items():
            if node not in inputs:
                raise ProtocolError(
                    f"phase {phase_id}: {node} is not an experimental input"
                )
            inputs[node] = int(value)
    applied = tuple((overlay or {}).get("interventions") or ())
    for intervention_id in applied:
        if intervention_id not in interventions:
            raise ProtocolError(
                f"phase {phase_id}: unknown intervention {intervention_id}"
            )
    duration = float(
        (overlay or {}).get("relative_duration")
        or spec.get("relative_duration", default_duration)
    )
    if duration <= 0:
        raise ProtocolError(f"phase {phase_id}: duration must be positive")
    return Phase(
        phase_id=phase_id,
        inputs=inputs,
        interventions=applied,
        relative_duration=duration,
        physical_duration=str(spec.get("physical_duration", "")),
    )


def load_protocols(model: Model, path: Path | None = None) -> ProtocolSet:
    path = path or CONFIG / "protocols.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload.get("model_version") != model.version:
        raise ProtocolError(
            f"{path} is written for {payload.get('model_version')}, not {model.version}"
        )
    interventions = load_interventions(model)
    default_duration = float(payload.get("default_relative_duration", 20.0))
    base_phases = payload["phases"]
    conditions: dict[str, Condition] = {}
    for condition_id, spec in payload["conditions"].items():
        available = dict(base_phases)
        available.update(spec.get("extra_phases") or {})
        overlays = spec.get("overlays") or {}
        unknown = set(overlays) - set(spec["phases"])
        if unknown:
            raise ProtocolError(
                f"{condition_id}: overlay on absent phases {sorted(unknown)}"
            )
        phases = tuple(
            _phase(
                model,
                phase_id,
                available[phase_id],
                overlays.get(phase_id),
                default_duration,
                interventions,
            )
            for phase_id in spec["phases"]
        )
        conditions[condition_id] = Condition(
            condition_id=condition_id,
            description=str(spec.get("description", "")),
            phases=phases,
        )
    comparisons: dict[str, Comparison] = {}
    for row in payload.get("comparisons") or []:
        for key in ("perturbed", "control"):
            if row[key] not in conditions:
                raise ProtocolError(
                    f"comparison {row['id']}: unknown condition {row[key]}"
                )
        comparison = Comparison(
            comparison_id=row["id"],
            question=str(row.get("question", "")),
            perturbed=row["perturbed"],
            control=row["control"],
            phase=row["phase"],
            phase_perturbed=row.get("phase_perturbed", row["phase"]),
        )
        conditions[comparison.control].phase(comparison.phase)
        conditions[comparison.perturbed].phase(comparison.phase_perturbed)
        comparisons[comparison.comparison_id] = comparison
    return ProtocolSet(
        model_version=model.version,
        conditions=conditions,
        comparisons=comparisons,
        interventions=interventions,
        source=path,
    )


def forced_nodes(
    phase: Phase, interventions: Mapping[str, Intervention]
) -> dict[str, int]:
    forced: dict[str, int] = {}
    for intervention_id in phase.interventions:
        intervention = interventions[intervention_id]
        if (
            forced.get(intervention.node, intervention.forced_state)
            != intervention.forced_state
        ):
            raise ProtocolError(f"conflicting interventions on {intervention.node}")
        forced[intervention.node] = intervention.forced_state
    return forced
