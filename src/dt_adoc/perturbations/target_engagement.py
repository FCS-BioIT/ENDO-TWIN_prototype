"""Target-engagement helpers."""

from __future__ import annotations


def build_target_engagement_grid(levels: list[float]) -> list[float]:
    cleaned = sorted({round(level, 10) for level in levels})
    if not cleaned:
        raise ValueError("at least one level is required")
    for level in cleaned:
        if level < 0.0 or level > 1.0:
            raise ValueError("engagement levels must be in [0, 1]")
    return cleaned
