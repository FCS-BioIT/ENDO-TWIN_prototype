"""Strict node-variant logic."""

from __future__ import annotations

from dataclasses import dataclass

NON_EVIDENCE_STATES = {"missing", "blank", "below_detection", "dropout", "excluded"}


@dataclass(frozen=True)
class StrictNodeDecision:
    clamp: int | None
    reason: str


def decide_strict_variant(
    *,
    has_constitutive_evidence: bool,
    measurement_state: str,
    desired_state: int | None,
) -> StrictNodeDecision:
    """Return a conservative clamp decision."""
    if desired_state not in {None, 0, 1}:
        raise ValueError("desired_state must be None, 0, or 1")
    if measurement_state in NON_EVIDENCE_STATES:
        return StrictNodeDecision(
            clamp=None,
            reason="non-evidence measurement state cannot justify a clamp",
        )
    if not has_constitutive_evidence or desired_state is None:
        return StrictNodeDecision(
            clamp=None,
            reason="strong constitutive evidence is required for strict variants",
        )
    return StrictNodeDecision(clamp=desired_state, reason="constitutive evidence")
