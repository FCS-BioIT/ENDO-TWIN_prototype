"""Model-data contract: which readout observes which node, and how agreement is judged.

MaBoSS probabilities are never compared with concentrations. A prediction is a
direction of change of a node's fixed-point state between a perturbed and a
matched control condition; an observation is a donor-level effect (log2 ratio of
perturbed over control within the same donor) of a readout mapped to that node.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from endotwin.model import Model, read_tsv
from endotwin.paths import CONFIG

MAPPING_STATUSES = {
    "active",
    "active_with_caveat",
    "planned",
    "candidate",
    "quality_gate",
}
OUTCOMES = ("concordant", "discordant", "inconclusive")


class ObservationError(ValueError):
    pass


def load_observation_map(
    model: Model, path: Path | None = None
) -> dict[str, dict[str, str]]:
    path = path or CONFIG / "observation_map.tsv"
    out: dict[str, dict[str, str]] = {}
    for row in read_tsv(path):
        if row["mapping_status"] not in MAPPING_STATUSES:
            raise ObservationError(
                f"{row['readout_id']}: unknown status {row['mapping_status']}"
            )
        node = row["model_node"]
        if node and node not in model.rules:
            raise ObservationError(f"{row['readout_id']} maps to unknown node {node}")
        if row["mapping_status"] != "quality_gate" and not node:
            raise ObservationError(f"{row['readout_id']} has no model node")
        if "concentration" in row["observation_rule"].lower():
            raise ObservationError(
                f"{row['readout_id']}: observation rules compare directions, never concentrations"
            )
        out[row["readout_id"]] = row
    return out


@dataclass(frozen=True)
class AgreementCriteria:
    """Pre-declared rule turning donor-level effects into one verdict.

    ``min_effect_log2``: smallest |log2 ratio| counted as a change.
    ``min_evaluable_donors``: below this, the verdict is inconclusive.
    ``min_consistent_donors``: donors that must move in one direction (beyond
    ``min_effect_log2``) for a concordant or discordant call.
    ``equivalence_margin_log2``: for a predicted no-change, every evaluable donor
    must lie within this margin; a non-significant difference alone never
    confirms a no-change prediction.
    """

    min_effect_log2: float
    min_evaluable_donors: int
    min_consistent_donors: int
    equivalence_margin_log2: float

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> AgreementCriteria:
        criteria = cls(
            min_effect_log2=float(payload["min_effect_log2"]),
            min_evaluable_donors=int(payload["min_evaluable_donors"]),
            min_consistent_donors=int(payload["min_consistent_donors"]),
            equivalence_margin_log2=float(payload["equivalence_margin_log2"]),
        )
        if criteria.min_consistent_donors > criteria.min_evaluable_donors:
            raise ObservationError(
                "min_consistent_donors cannot exceed min_evaluable_donors"
            )
        if criteria.min_effect_log2 < 0 or criteria.equivalence_margin_log2 < 0:
            raise ObservationError("thresholds must be non-negative")
        return criteria


def donor_effect(perturbed: float, control: float) -> float:
    if perturbed <= 0 or control <= 0:
        raise ObservationError(
            "log2 ratios need positive values; below-detection values must be "
            "handled by a pre-declared rule before evaluation, not imputed here"
        )
    return math.log2(perturbed / control)


def classify(
    predicted: str, effects: Sequence[float], criteria: AgreementCriteria
) -> tuple[str, str]:
    """Return (verdict, reason) for one prediction against donor-level effects."""
    if predicted not in {"up", "down", "no_change"}:
        raise ObservationError(f"unknown predicted direction {predicted!r}")
    n = len(effects)
    if n < criteria.min_evaluable_donors:
        return "inconclusive", f"{n} evaluable donors < {criteria.min_evaluable_donors}"
    up = sum(1 for e in effects if e >= criteria.min_effect_log2 and e > 0)
    down = sum(1 for e in effects if e <= -criteria.min_effect_log2 and e < 0)
    k = criteria.min_consistent_donors
    if predicted == "no_change":
        if all(abs(e) <= criteria.equivalence_margin_log2 for e in effects):
            return (
                "concordant",
                f"all {n} donors within +/-{criteria.equivalence_margin_log2} log2",
            )
        if up >= k or down >= k:
            return (
                "discordant",
                f"{max(up, down)} donors changed beyond {criteria.min_effect_log2} log2",
            )
        return "inconclusive", "neither equivalence nor a consistent change"
    agreeing, opposing = (up, down) if predicted == "up" else (down, up)
    if agreeing >= k:
        return "concordant", f"{agreeing}/{n} donors in the predicted direction"
    if opposing >= k:
        return "discordant", f"{opposing}/{n} donors opposite to the prediction"
    return "inconclusive", f"{agreeing} agreeing, {opposing} opposing of {n}"
