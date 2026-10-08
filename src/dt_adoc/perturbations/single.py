"""Single-perturbation scenario generation."""

from __future__ import annotations

from dataclasses import dataclass

from dt_adoc.perturbations.target_engagement import build_target_engagement_grid


@dataclass(frozen=True)
class SinglePerturbationScenario:
    target: str
    engagement: float
    mode: str


def single_scenarios(
    target: str, levels: list[float], *, mode: str
) -> list[SinglePerturbationScenario]:
    return [
        SinglePerturbationScenario(target=target, engagement=level, mode=mode)
        for level in build_target_engagement_grid(levels)
    ]
