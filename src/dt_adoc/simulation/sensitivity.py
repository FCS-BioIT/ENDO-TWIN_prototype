"""Assumption-sensitivity helpers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from pathlib import Path

from dt_adoc.model.runtime import (
    resolve_memory_policy,
    resolve_model,
    resolve_rule_variants,
)

CONTINUATION_MODE_CHOICES = ("joint", "marginal")


def sensitivity_matrix(space: dict[str, list[object]]) -> list[dict[str, object]]:
    keys = list(space)
    return [
        dict(zip(keys, values, strict=True))
        for values in product(*(space[key] for key in keys))
    ]


@dataclass(frozen=True)
class SensitivityScenario:
    scenario_id: str
    model_version: str
    continuation_mode: str
    memory_policy_id: str
    rule_variant_selection: tuple[tuple[str, str], ...]

    def as_row(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "model_version": self.model_version,
            "continuation_mode": self.continuation_mode,
            "memory_policy_id": self.memory_policy_id,
            "rule_variant_selection": dict(self.rule_variant_selection),
            "rule_variant_signature": _rule_variant_signature(
                dict(self.rule_variant_selection)
            ),
        }


def _rule_variant_signature(selection: Mapping[str, str]) -> str:
    if not selection:
        return "none"
    return "|".join(
        f"{family}={variant_id}" for family, variant_id in sorted(selection.items())
    )


def _normalize_memory_policies(
    *,
    model_version: str,
    requested: Sequence[str] | None,
    root: Path | None = None,
) -> tuple[str, ...]:
    spec = resolve_model(model_version, root)
    if requested is None:
        return (spec.default_memory_policy,)
    normalized: list[str] = []
    for policy_id in requested:
        if policy_id == spec.default_memory_policy:
            normalized.append(policy_id)
            continue
        resolve_memory_policy(
            model_version=model_version,
            policy_id=policy_id,
            root=root,
        )
        normalized.append(policy_id)
    if not normalized:
        raise ValueError(
            f"no memory policies requested for model_version {model_version!r}"
        )
    return tuple(normalized)


def _normalize_rule_variant_selections(
    *,
    model_version: str,
    requested: Mapping[str, Sequence[str]] | None,
    root: Path | None = None,
) -> tuple[dict[str, str], ...]:
    spec = resolve_model(model_version, root)
    if not spec.rule_variants:
        return ({},)
    if not requested:
        selected, _ = resolve_rule_variants(model_version=model_version, root=root)
        return (selected,)

    families = sorted(requested)
    variant_lists: list[tuple[str, ...]] = []
    for family in families:
        variant_ids = tuple(requested[family])
        if not variant_ids:
            raise ValueError(
                f"rule-variant family {family!r} must include at least one variant"
            )
        variant_lists.append(variant_ids)

    selections: list[dict[str, str]] = []
    for variant_ids in product(*variant_lists):
        selected, _ = resolve_rule_variants(
            model_version=model_version,
            variant_selection=dict(zip(families, variant_ids, strict=True)),
            root=root,
        )
        selections.append(selected)
    return tuple(selections)


def build_bounded_sensitivity_matrix(
    *,
    model_versions: Sequence[str],
    continuation_modes: Sequence[str],
    memory_policies_by_model: Mapping[str, Sequence[str]] | None = None,
    rule_variants_by_model: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
    root: Path | None = None,
) -> list[SensitivityScenario]:
    if not model_versions:
        raise ValueError("model_versions cannot be empty")
    if not continuation_modes:
        raise ValueError("continuation_modes cannot be empty")

    memory_policies_by_model = memory_policies_by_model or {}
    rule_variants_by_model = rule_variants_by_model or {}
    rows: list[SensitivityScenario] = []
    for model_version in model_versions:
        resolve_model(model_version, root)
        memory_policy_ids = _normalize_memory_policies(
            model_version=model_version,
            requested=memory_policies_by_model.get(model_version),
            root=root,
        )
        rule_variant_selections = _normalize_rule_variant_selections(
            model_version=model_version,
            requested=rule_variants_by_model.get(model_version),
            root=root,
        )
        for continuation_mode in continuation_modes:
            if continuation_mode not in CONTINUATION_MODE_CHOICES:
                raise ValueError(
                    f"unsupported continuation_mode {continuation_mode!r}; expected one of: {', '.join(CONTINUATION_MODE_CHOICES)}"
                )
            for memory_policy_id, selection in product(
                memory_policy_ids,
                rule_variant_selections,
            ):
                signature = _rule_variant_signature(selection)
                rows.append(
                    SensitivityScenario(
                        scenario_id=(
                            f"{model_version}__{continuation_mode}"
                            f"__{memory_policy_id}__{signature}"
                        ),
                        model_version=model_version,
                        continuation_mode=continuation_mode,
                        memory_policy_id=memory_policy_id,
                        rule_variant_selection=tuple(sorted(selection.items())),
                    )
                )
    return sorted(
        rows,
        key=lambda row: (
            row.model_version,
            row.continuation_mode,
            row.memory_policy_id,
            row.rule_variant_selection,
        ),
    )


def validate_sensitivity_matrix_completeness(
    scenarios: Iterable[SensitivityScenario],
    *,
    model_versions: Sequence[str],
    continuation_modes: Sequence[str],
    memory_policies_by_model: Mapping[str, Sequence[str]] | None = None,
    rule_variants_by_model: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
    root: Path | None = None,
) -> None:
    scenario_tuple = tuple(scenarios)
    counts = Counter(scenario.scenario_id for scenario in scenario_tuple)
    duplicates = sorted(
        scenario_id for scenario_id, count in counts.items() if count > 1
    )
    if duplicates:
        raise ValueError(
            f"sensitivity matrix contains duplicate scenario_id values: {', '.join(duplicates)}"
        )

    expected = build_bounded_sensitivity_matrix(
        model_versions=model_versions,
        continuation_modes=continuation_modes,
        memory_policies_by_model=memory_policies_by_model,
        rule_variants_by_model=rule_variants_by_model,
        root=root,
    )
    expected_ids = {scenario.scenario_id for scenario in expected}
    observed_ids = set(counts)
    missing = sorted(expected_ids - observed_ids)
    unexpected = sorted(observed_ids - expected_ids)
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if unexpected:
            details.append(f"unexpected={','.join(unexpected)}")
        raise ValueError(
            "sensitivity matrix completeness failure: " + "; ".join(details)
        )


def build_baseline_vs_literature_comparison_rows(
    *,
    baseline_results: Mapping[str, Mapping[str, float]],
    literature_results: Mapping[str, Mapping[str, float]],
    protocol_pairs: Mapping[str, tuple[str, str]],
    phenotype_ids: Sequence[str],
    protocol_roles: Mapping[str, str] | None = None,
    baseline_model_version: str = "adoc-core-v0.1.0",
    literature_model_version: str = "adoc-literature-v0.2.0",
    root: Path | None = None,
) -> list[dict[str, object]]:
    resolve_model(baseline_model_version, root)
    resolve_model(literature_model_version, root)
    protocol_roles = protocol_roles or {}

    rows: list[dict[str, object]] = []
    for comparison_id in sorted(protocol_pairs):
        baseline_protocol_id, literature_protocol_id = protocol_pairs[comparison_id]
        baseline_protocol = baseline_results[baseline_protocol_id]
        literature_protocol = literature_results[literature_protocol_id]
        role = protocol_roles.get(comparison_id, "descriptive")
        for phenotype_id in phenotype_ids:
            baseline_probability = float(baseline_protocol[phenotype_id])
            literature_probability = float(literature_protocol[phenotype_id])
            rows.append(
                {
                    "comparison_id": comparison_id,
                    "baseline_protocol_id": baseline_protocol_id,
                    "literature_protocol_id": literature_protocol_id,
                    "phenotype_id": phenotype_id,
                    "baseline_model_version": baseline_model_version,
                    "literature_model_version": literature_model_version,
                    "role": role,
                    "baseline_probability": baseline_probability,
                    "literature_probability": literature_probability,
                    "literature_minus_baseline": literature_probability
                    - baseline_probability,
                    "absolute_delta": abs(
                        literature_probability - baseline_probability
                    ),
                    "comparison_kind": "baseline_vs_literature",
                }
            )
    return rows
