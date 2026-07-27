"""Monte Carlo stability helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from statistics import mean


def effect_span(values: list[float]) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    return max(values) - min(values)


def stable_within(values: list[float], tolerance: float) -> bool:
    return effect_span(values) <= tolerance


def effect_mean(values: list[float]) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    return mean(values)


@dataclass(frozen=True)
class FullSequenceStabilityRecord:
    sequence_id: str
    trajectory_count: int
    seed: int
    maternal_seed: int
    phenotype_values: Mapping[str, float]


def validate_full_sequence_stability_records(
    records: Iterable[FullSequenceStabilityRecord],
    *,
    minimum_trajectory_counts: int = 2,
) -> tuple[FullSequenceStabilityRecord, ...]:
    if minimum_trajectory_counts < 2:
        raise ValueError("minimum_trajectory_counts must be at least 2")
    record_tuple = tuple(records)
    if not record_tuple:
        raise ValueError("records cannot be empty")

    seen_keys: set[tuple[str, int, int]] = set()
    by_sequence: dict[str, list[FullSequenceStabilityRecord]] = defaultdict(list)
    for record in record_tuple:
        if record.trajectory_count <= 0:
            raise ValueError("trajectory_count must be positive")
        if record.seed < 0 or record.maternal_seed < 0:
            raise ValueError("seed and maternal_seed must be non-negative")
        if record.seed != record.maternal_seed:
            raise ValueError(
                "maternal_seed must match seed so each stability rerun uses its own upstream maternal state"
            )
        key = (record.sequence_id, record.trajectory_count, record.seed)
        if key in seen_keys:
            raise ValueError(
                f"duplicate full-sequence stability record for sequence_id={record.sequence_id!r}, trajectory_count={record.trajectory_count}, seed={record.seed}"
            )
        seen_keys.add(key)
        by_sequence[record.sequence_id].append(record)

    for sequence_id, sequence_records in by_sequence.items():
        trajectory_counts = {record.trajectory_count for record in sequence_records}
        if len(trajectory_counts) < minimum_trajectory_counts:
            raise ValueError(
                f"sequence {sequence_id!r} must include at least {minimum_trajectory_counts} trajectory counts"
            )
        seeds = {record.seed for record in sequence_records}
        if len(seeds) < 2:
            raise ValueError(
                f"sequence {sequence_id!r} must include at least two seeds"
            )
    return record_tuple


def summarize_full_sequence_stability(
    records: Iterable[FullSequenceStabilityRecord],
    *,
    minimum_trajectory_counts: int = 2,
) -> list[dict[str, object]]:
    record_tuple = validate_full_sequence_stability_records(
        records,
        minimum_trajectory_counts=minimum_trajectory_counts,
    )
    grouped: dict[tuple[str, int, str], list[tuple[int, float]]] = defaultdict(list)
    for record in record_tuple:
        for phenotype_id, value in record.phenotype_values.items():
            grouped[(record.sequence_id, record.trajectory_count, phenotype_id)].append(
                (record.seed, float(value))
            )

    rows: list[dict[str, object]] = []
    for sequence_id, trajectory_count, phenotype_id in sorted(grouped):
        seed_values = sorted(grouped[(sequence_id, trajectory_count, phenotype_id)])
        values = [value for _, value in seed_values]
        rows.append(
            {
                "sequence_id": sequence_id,
                "trajectory_count": trajectory_count,
                "phenotype_id": phenotype_id,
                "seed_count": len(seed_values),
                "seeds": ",".join(str(seed) for seed, _ in seed_values),
                "mean_probability": effect_mean(values),
                "min_probability": min(values),
                "max_probability": max(values),
                "span": effect_span(values),
            }
        )
    return rows
