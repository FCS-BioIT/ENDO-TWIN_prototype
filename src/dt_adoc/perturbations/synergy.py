"""Synergy summary functions."""

from __future__ import annotations


def _beneficial_effect(baseline: float, perturbed: float, *, direction: str) -> float:
    if direction == "decrease":
        return baseline - perturbed
    if direction == "increase":
        return perturbed - baseline
    raise ValueError("direction must be 'increase' or 'decrease'")


def bliss_independence(
    *,
    baseline: float,
    single_a: float,
    single_b: float,
    double_ab: float,
    direction: str,
) -> float:
    effect_a = _beneficial_effect(baseline, single_a, direction=direction)
    effect_b = _beneficial_effect(baseline, single_b, direction=direction)
    effect_ab = _beneficial_effect(baseline, double_ab, direction=direction)
    expected = effect_a + effect_b - (effect_a * effect_b)
    return effect_ab - expected


def highest_single_agent(
    *,
    baseline: float,
    single_a: float,
    single_b: float,
    double_ab: float,
    direction: str,
) -> float:
    effect_a = _beneficial_effect(baseline, single_a, direction=direction)
    effect_b = _beneficial_effect(baseline, single_b, direction=direction)
    effect_ab = _beneficial_effect(baseline, double_ab, direction=direction)
    return effect_ab - max(effect_a, effect_b)
