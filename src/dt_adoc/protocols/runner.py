"""Protocol sequencing helpers for parent-owned MaBoSS execution code."""

from __future__ import annotations

from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from dt_adoc.protocols.conditions import get_protocol


def protocol_sequence(
    protocol_id: str,
    root: Path | None = None,
    *,
    model_version: str | None = None,
) -> list[dict[str, object]]:
    protocol = get_protocol(protocol_id, root, model_version=model_version)
    return [
        {
            "protocol_id": protocol.protocol_id,
            "model_version": protocol.model_version,
            "protocol_class": protocol.protocol_class,
            "continuation_mode": protocol.continuation.mode
            if protocol.continuation is not None
            else "",
            "continuation_memory_policy": protocol.continuation.memory_policy
            if protocol.continuation is not None
            else "",
            "continuation_probability_cutoff": protocol.continuation.probability_cutoff
            if protocol.continuation is not None
            else "",
            "step_id": step.step_id,
            "relative_order": step.relative_order,
            "relative_duration": step.relative_duration,
            "duration_note": step.duration_note,
            "condition_cfg": protocol.condition_cfg,
            "continuation_from": protocol.continuation_from,
            "input_states": dict(step.input_states),
            # Only when declared, so a sequence that names none is the record it
            # was before step-level timing existed.
            **(
                {"interventions": list(step.interventions)}
                if step.interventions
                else {}
            ),
        }
        for step in protocol.steps
    ]


def expanded_protocol_sequence(
    protocol_id: str,
    root: Path | None = None,
    *,
    model_version: str | None = None,
) -> list[dict[str, object]]:
    protocol = get_protocol(protocol_id, root, model_version=model_version)
    lineage: list[dict[str, object]] = []
    if protocol.continuation_from is not None:
        lineage.extend(
            expanded_protocol_sequence(
                protocol.continuation_from,
                root,
                model_version=model_version,
            )
        )
    lineage.extend(protocol_sequence(protocol_id, root, model_version=model_version))
    return lineage
