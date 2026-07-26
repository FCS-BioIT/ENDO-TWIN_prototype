"""Phenotype effect helpers."""

from __future__ import annotations


def directional_effect(*, baseline: float, perturbed: float, direction: str) -> float:
    if direction == "decrease":
        return baseline - perturbed
    if direction == "increase":
        return perturbed - baseline
    if direction == "preserve_high":
        return perturbed
    raise ValueError("unsupported direction")
