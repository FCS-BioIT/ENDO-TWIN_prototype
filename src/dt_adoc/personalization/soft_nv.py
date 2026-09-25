"""Soft node-variant mappings."""

from __future__ import annotations

import math
from dataclasses import dataclass


def clip01(value: float) -> float:
    return min(1.0, max(0.0, value))


@dataclass(frozen=True)
class SoftMappingConfig:
    alpha: float = 1.0
    min_rate: float = 0.25
    max_rate: float = 4.0


def score_to_initial_probability(score: float) -> float:
    """Treat the normalized score itself as the provisional initial probability."""
    return clip01(score)


def _bounded_rate(value: float, *, min_rate: float, max_rate: float) -> float:
    return min(max_rate, max(min_rate, value))


def score_to_rate_modifiers(
    score: float, config: SoftMappingConfig
) -> tuple[float, float]:
    """
    Map a normalized score to relative up/down modifiers around 0.5.

    This is a documented model assumption, not a biological calibration.
    """
    centered = clip01(score) - 0.5
    rate_up = math.exp(config.alpha * centered)
    rate_down = math.exp(-config.alpha * centered)
    return (
        _bounded_rate(rate_up, min_rate=config.min_rate, max_rate=config.max_rate),
        _bounded_rate(rate_down, min_rate=config.min_rate, max_rate=config.max_rate),
    )
