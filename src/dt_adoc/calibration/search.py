"""Bounded search helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    payload: dict[str, object]


@dataclass(frozen=True)
class RetainedScenarioEnsemble:
    retained: tuple[Scenario, ...]
    total_scenarios: int
    acceptable_scenarios: int
    minimum_retained: int
    maximum_retained: int | None
    used_minimum_fallback: bool
    truncated_to_maximum: bool


def _tie_break_value(value: object) -> str:
    return repr(value)


def rank_scenarios(
    scenarios: Iterable[Scenario],
    *,
    score_key: str,
    tie_break_keys: Sequence[str] = (),
) -> tuple[Scenario, ...]:
    return tuple(
        sorted(
            scenarios,
            key=lambda scenario: (
                -float(scenario.payload[score_key]),
                *(
                    _tie_break_value(scenario.payload.get(key))
                    for key in tie_break_keys
                ),
                scenario.scenario_id,
            ),
        )
    )


def retain_acceptable_scenarios(
    scenarios: Iterable[Scenario],
    *,
    score_key: str,
    minimum_score: float,
    min_scenarios: int = 1,
    max_scenarios: int | None = None,
    tie_break_keys: Sequence[str] = (),
) -> RetainedScenarioEnsemble:
    if min_scenarios < 0:
        raise ValueError("min_scenarios must be non-negative")
    if max_scenarios is not None and max_scenarios <= 0:
        raise ValueError("max_scenarios must be positive when provided")
    if max_scenarios is not None and max_scenarios < min_scenarios:
        raise ValueError("max_scenarios cannot be smaller than min_scenarios")

    ranked = rank_scenarios(
        scenarios,
        score_key=score_key,
        tie_break_keys=tie_break_keys,
    )
    acceptable = tuple(
        scenario
        for scenario in ranked
        if float(scenario.payload[score_key]) >= minimum_score
    )
    retained = acceptable[:max_scenarios] if max_scenarios is not None else acceptable
    used_minimum_fallback = len(retained) < min_scenarios
    if used_minimum_fallback:
        floor_count = min(len(ranked), min_scenarios)
        if max_scenarios is not None:
            floor_count = min(floor_count, max_scenarios)
        retained = ranked[:floor_count]
    return RetainedScenarioEnsemble(
        retained=tuple(retained),
        total_scenarios=len(ranked),
        acceptable_scenarios=len(acceptable),
        minimum_retained=min_scenarios,
        maximum_retained=max_scenarios,
        used_minimum_fallback=used_minimum_fallback,
        truncated_to_maximum=max_scenarios is not None
        and len(acceptable) > max_scenarios,
    )
