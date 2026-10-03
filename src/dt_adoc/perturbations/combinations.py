"""Pairwise perturbation scenarios."""

from __future__ import annotations

from dataclasses import dataclass

from dt_adoc.perturbations.target_engagement import build_target_engagement_grid


@dataclass(frozen=True)
class PairPerturbationScenario:
    target_a: str
    target_b: str
    engagement_a: float
    engagement_b: float
    mode: str


def pair_scenarios(
    target_a: str,
    target_b: str,
    levels: list[float],
    *,
    mode: str,
) -> list[PairPerturbationScenario]:
    grid = build_target_engagement_grid(levels)
    return [
        PairPerturbationScenario(
            target_a=target_a,
            target_b=target_b,
            engagement_a=level_a,
            engagement_b=level_b,
            mode=mode,
        )
        for level_a in grid
        for level_b in grid
    ]
