"""Safety penalty helpers."""

from __future__ import annotations


def loss_penalty(*, observed: float, minimum_allowed: float) -> float:
    return max(0.0, minimum_allowed - observed)


def gain_penalty(*, observed: float, maximum_allowed: float) -> float:
    return max(0.0, observed - maximum_allowed)
