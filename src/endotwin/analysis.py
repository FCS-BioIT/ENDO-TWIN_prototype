"""Mechanistic analyses of the ENDO-TWIN mainline.

* :func:`exact_predictions` and :func:`discrimination_table` -- exact fixed-point
  predictions of every protocol condition under every combination of rule
  variants, and which perturbation/readout pairs separate competing hypotheses.
  Exhaustive; independent of transition rates.
* :func:`maboss_confirmation` -- the same conditions simulated stochastically,
  checking that every phase converges to the exact fixed point.
* :func:`relay_transient` -- the HAND2 stromal-relay example: two
  representations with an identical composed Boolean function compared through
  the progestin-onset transient, on disjoint seed blocks.
* :func:`rate_sensitivity` -- random per-node transition rates: which predicted
  directions survive (steady state) and how transient readouts move.

Every result is a conditional model prediction, not a biological observation.
"""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Mapping
from dataclasses import dataclass

from endotwin.model import Model, scenario_label
from endotwin.protocols import ProtocolSet, forced_nodes
from endotwin.simulate import SimulationSettings, simulate_condition
from endotwin.structure import NotAcyclicError, fixed_point, topological_order

DIRECTION_TOLERANCE = 1e-9


def direction(delta: float, tolerance: float = DIRECTION_TOLERANCE) -> str:
    if delta > tolerance:
        return "up"
    if delta < -tolerance:
        return "down"
    return "no_change"


def readout_nodes(model: Model) -> tuple[str, ...]:
    return tuple(dict.fromkeys(model.outputs + model.readout_nodes))


# -- exact fixed points -------------------------------------------------------


def exact_predictions(model: Model, protocols: ProtocolSet) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for selection in model.scenarios():
        rules = model.rules_for(selection)
        for condition in protocols.conditions.values():
            for phase in condition.phases:
                state = fixed_point(
                    rules, phase.inputs, forced_nodes(phase, protocols.interventions)
                )
                rows.append(
                    {
                        "scenario": scenario_label(selection),
                        **{f"variant_{f}": v for f, v in sorted(selection.items())},
                        "condition": condition.condition_id,
                        "phase": phase.phase_id,
                        **{n: state[n] for n in readout_nodes(model)},
                    }
                )
    return rows


def _lookup(rows, scenario: str, condition: str, phase: str) -> Mapping[str, object]:
    for row in rows:
        if (row["scenario"], row["condition"], row["phase"]) == (
            scenario,
            condition,
            phase,
        ):
            return row
    raise KeyError((scenario, condition, phase))


def comparison_directions(
    model: Model, protocols: ProtocolSet, rows: list[dict[str, object]] | None = None
) -> list[dict[str, object]]:
    rows = rows or exact_predictions(model, protocols)
    out = []
    for selection in model.scenarios():
        label = scenario_label(selection)
        for comp in protocols.comparisons.values():
            pert = _lookup(rows, label, comp.perturbed, comp.phase_perturbed)
            ctrl = _lookup(rows, label, comp.control, comp.phase)
            for node in readout_nodes(model):
                out.append(
                    {
                        "comparison": comp.comparison_id,
                        "question": comp.question,
                        "scenario": label,
                        **{f"variant_{f}": v for f, v in sorted(selection.items())},
                        "readout_node": node,
                        "control": int(ctrl[node]),
                        "perturbed": int(pert[node]),
                        "direction": direction(float(pert[node]) - float(ctrl[node])),
                    }
                )
    return out


def discrimination_table(
    model: Model,
    protocols: ProtocolSet,
    directions: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    """For each comparison x readout x hypothesis family: does it separate the variants?

    ``robust``: the variants predict different directions for every setting of
    the other families. ``conditional``: only for some settings. ``none``: never.
    """
    directions = directions or comparison_directions(model, protocols)
    index = {
        (d["comparison"], d["readout_node"], d["scenario"]): d["direction"]
        for d in directions
    }
    families = model.families()
    out = []
    for comp in protocols.comparisons.values():
        for node in readout_nodes(model):
            for family, variants in sorted(families.items()):
                others = {f: v for f, v in families.items() if f != family}
                contexts: list[dict[str, str]] = [{}]
                for f in sorted(others):
                    contexts = [{**c, f: v} for c in contexts for v in others[f]]
                for i, a in enumerate(variants):
                    for b in variants[i + 1 :]:
                        differs = []
                        per_variant: dict[str, set[str]] = {a: set(), b: set()}
                        for ctx in contexts:
                            da = index[
                                (
                                    comp.comparison_id,
                                    node,
                                    scenario_label({**ctx, family: a}),
                                )
                            ]
                            db = index[
                                (
                                    comp.comparison_id,
                                    node,
                                    scenario_label({**ctx, family: b}),
                                )
                            ]
                            per_variant[a].add(da)
                            per_variant[b].add(db)
                            differs.append(da != db)
                        verdict = (
                            "robust"
                            if all(differs)
                            else "conditional"
                            if any(differs)
                            else "none"
                        )
                        out.append(
                            {
                                "comparison": comp.comparison_id,
                                "question": comp.question,
                                "readout_node": node,
                                "family": family,
                                "variant_a": a,
                                "variant_b": b,
                                "directions_a": ";".join(sorted(per_variant[a])),
                                "directions_b": ";".join(sorted(per_variant[b])),
                                "discrimination": verdict,
                            }
                        )
    return out


# -- stochastic confirmation --------------------------------------------------


def maboss_confirmation(
    model: Model,
    protocols: ProtocolSet,
    settings: SimulationSettings,
    exact_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    out = []
    for selection in model.scenarios():
        label = scenario_label(selection)
        for condition in protocols.conditions.values():
            result = simulate_condition(
                model, condition, protocols.interventions, selection, settings
            )
            for phase in result.phases:
                exact = _lookup(
                    exact_rows, label, condition.condition_id, phase.phase_id
                )
                worst = max(
                    abs(phase.final[n] - float(exact[n])) for n in readout_nodes(model)
                )
                out.append(
                    {
                        "scenario": label,
                        "condition": condition.condition_id,
                        "phase": phase.phase_id,
                        "converged": phase.converged,
                        "max_abs_deviation_from_exact": round(worst, 6),
                        **{n: round(phase.final[n], 6) for n in readout_nodes(model)},
                    }
                )
    return out


# -- HAND2 relay transient ----------------------------------------------------


@dataclass(frozen=True)
class RelayTransient:
    time: list[float]
    mean_relay: list[float]
    sd_relay: list[float]
    mean_direct: list[float]
    sd_direct: list[float]
    summary: dict[str, object]


def relay_transient(
    model: Model,
    protocols: ProtocolSet,
    *,
    replicates: int = 10,
    sample_count: int = 5000,
    seed: int = 101,
    readout: str = "OUT_EPITHELIAL_PROLIFERATION",
    relay_variant: str = "Q2_stromal_relay",
    direct_variant: str = "Q2_relay_plus_direct_v051",
    condition_id: str = "reference",
    phase_id: str = "differentiation_supplemented",
) -> RelayTransient:
    condition = protocols.conditions[condition_id]
    curves: dict[str, list[list[float]]] = {relay_variant: [], direct_variant: []}
    finals: dict[str, list[float]] = {relay_variant: [], direct_variant: []}
    times: list[float] = []
    for r in range(replicates):
        # The same seed block is used for both variants (paired design), and
        # replicate blocks are disjoint.
        settings = SimulationSettings(sample_count=sample_count, seed=seed + r)
        for variant in (relay_variant, direct_variant):
            result = simulate_condition(
                model,
                condition,
                protocols.interventions,
                model.selection_from_ids([variant]),
                settings,
            )
            phase = next(p for p in result.phases if p.phase_id == phase_id)
            frame = phase.trajectory
            times = [round(t - phase.start_time, 6) for t in frame["time"]]
            curves[variant].append([float(v) for v in frame[readout]])
            finals[variant].append(phase.final[readout])

    def mean_sd(series: list[list[float]]) -> tuple[list[float], list[float]]:
        cols = list(zip(*series, strict=True))
        return (
            [statistics.fmean(c) for c in cols],
            [statistics.stdev(c) if len(c) > 1 else 0.0 for c in cols],
        )

    m_relay, s_relay = mean_sd(curves[relay_variant])
    m_direct, s_direct = mean_sd(curves[direct_variant])
    tick = times[1] - times[0] if len(times) > 1 else 0.0
    paired_area = [
        sum(a - b for a, b in zip(ra, rb, strict=True)) * tick
        for ra, rb in zip(curves[relay_variant], curves[direct_variant], strict=True)
    ]
    diff = [a - b for a, b in zip(m_relay, m_direct, strict=True)]
    peak_index = max(range(len(diff)), key=lambda i: diff[i])

    def half_time(curve: list[float]) -> float | None:
        for t, v in zip(times, curve, strict=True):
            if v < 0.5:
                return t
        return None

    summary = {
        "model_version": model.version,
        "condition": condition_id,
        "phase": phase_id,
        "readout": readout,
        "variants": {"relay": relay_variant, "relay_plus_direct": direct_variant},
        "replicates": replicates,
        "sample_count": sample_count,
        "seeds": [seed + r for r in range(replicates)],
        "rates": "MaBoSS defaults (1 for every node)",
        "composed_function_identical": True,
        "final_mean_relay": statistics.fmean(finals[relay_variant]),
        "final_mean_relay_plus_direct": statistics.fmean(finals[direct_variant]),
        "peak_mean_difference": diff[peak_index],
        "peak_time": times[peak_index],
        "area_between_curves_mean": statistics.fmean(paired_area),
        "area_between_curves_sd": statistics.stdev(paired_area)
        if replicates > 1
        else 0.0,
        "replicates_with_positive_area": sum(1 for a in paired_area if a > 0),
        "half_time_relay": half_time(m_relay),
        "half_time_relay_plus_direct": half_time(m_direct),
        "interpretation": (
            "Both representations compute the same Boolean function, so their "
            "fixed points are identical; the explicit relay delays the fall of "
            "epithelial proliferation after progestin onset. The difference is a "
            "transient under unit rates in dimensionless time, not a calibrated "
            "temporal prediction."
        ),
    }
    return RelayTransient(times, m_relay, s_relay, m_direct, s_direct, summary)


# -- transition-rate sensitivity ----------------------------------------------


def _random_rates(model: Model, rng: random.Random, low: float, high: float):
    rates = {}
    for node in model.nodes:
        if node in model.inputs:
            continue
        up = math.exp(rng.uniform(math.log(low), math.log(high)))
        down = math.exp(rng.uniform(math.log(low), math.log(high)))
        rates[node] = (up, down)
    return rates


def rate_sensitivity(
    model: Model,
    protocols: ProtocolSet,
    exact_directions: list[dict[str, object]],
    *,
    samples: int = 30,
    sample_count: int = 2000,
    seed: int = 7,
    low: float = 0.1,
    high: float = 10.0,
    duration_scale: float = 5.0,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Per-node rates drawn log-uniformly in [low, high]; default variants only.

    Phases are lengthened by ``duration_scale`` so slow-rate samples can reach
    their fixed point; each record says whether it converged.
    """
    rng = random.Random(seed)
    default = scenario_label(model.default_selection())
    expected = {
        (d["comparison"], d["readout_node"]): d["direction"]
        for d in exact_directions
        if d["scenario"] == default
    }
    rows: list[dict[str, object]] = []
    for s in range(samples):
        rates = _random_rates(model, rng, low, high)
        settings = SimulationSettings(
            sample_count=sample_count,
            seed=1000 + s,
            rates=rates,
            duration_scale=duration_scale,
        )
        cache = {}
        for comp in protocols.comparisons.values():
            for cid in (comp.perturbed, comp.control):
                if cid not in cache:
                    cache[cid] = simulate_condition(
                        model,
                        protocols.conditions[cid],
                        protocols.interventions,
                        None,
                        settings,
                    )
            pert = next(
                p
                for p in cache[comp.perturbed].phases
                if p.phase_id == comp.phase_perturbed
            )
            ctrl = next(
                p for p in cache[comp.control].phases if p.phase_id == comp.phase
            )
            for node in readout_nodes(model):
                delta = pert.final[node] - ctrl.final[node]
                observed = direction(delta, tolerance=0.05)
                rows.append(
                    {
                        "sample": s,
                        "comparison": comp.comparison_id,
                        "readout_node": node,
                        "delta": round(delta, 6),
                        "direction": observed,
                        "exact_direction": expected[(comp.comparison_id, node)],
                        "agrees": observed == expected[(comp.comparison_id, node)],
                        "both_converged": pert.converged and ctrl.converged,
                    }
                )
    converged_rows = [r for r in rows if r["both_converged"]]
    summary = {
        "model_version": model.version,
        "scenario": default,
        "samples": samples,
        "rate_range": [low, high],
        "rate_distribution": "independent log-uniform per node, activation and inactivation",
        "duration_scale": duration_scale,
        "sample_count": sample_count,
        "direction_threshold": 0.05,
        "records": len(rows),
        "records_converged": len(converged_rows),
        "converged_agreement_fraction": (
            sum(r["agrees"] for r in converged_rows) / len(converged_rows)
            if converged_rows
            else None
        ),
        "all_agreement_fraction": sum(r["agrees"] for r in rows) / len(rows)
        if rows
        else None,
    }
    return rows, summary


def relay_rate_robustness(
    model: Model,
    protocols: ProtocolSet,
    *,
    samples: int = 20,
    sample_count: int = 2000,
    seed: int = 11,
    low: float = 0.1,
    high: float = 10.0,
    readout: str = "OUT_EPITHELIAL_PROLIFERATION",
    condition_id: str = "reference",
    phase_id: str = "differentiation_supplemented",
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Does the relay delay survive random transition rates?

    For each rate sample, the relay and relay-plus-direct representations are
    run with the same rates and seed block, and the area between their
    proliferation curves over the progestin-onset phase is recorded.
    """
    rng = random.Random(seed)
    condition = protocols.conditions[condition_id]
    rows = []
    for s in range(samples):
        rates = _random_rates(model, rng, low, high)
        settings = SimulationSettings(
            sample_count=sample_count, seed=2000 + s, rates=rates, duration_scale=5.0
        )
        curves = {}
        finals = {}
        for variant in ("Q2_stromal_relay", "Q2_relay_plus_direct_v051"):
            result = simulate_condition(
                model,
                condition,
                protocols.interventions,
                model.selection_from_ids([variant]),
                settings,
            )
            phase = next(p for p in result.phases if p.phase_id == phase_id)
            curves[variant] = [float(v) for v in phase.trajectory[readout]]
            finals[variant] = phase.final[readout]
        area = (
            sum(
                a - b
                for a, b in zip(
                    curves["Q2_stromal_relay"],
                    curves["Q2_relay_plus_direct_v051"],
                    strict=True,
                )
            )
            * settings.time_tick
        )
        rows.append(
            {
                "sample": s,
                "area_between_curves": round(area, 6),
                "final_relay": round(finals["Q2_stromal_relay"], 6),
                "final_relay_plus_direct": round(
                    finals["Q2_relay_plus_direct_v051"], 6
                ),
            }
        )
    areas = [r["area_between_curves"] for r in rows]
    summary = {
        "samples": samples,
        "rate_range": [low, high],
        "positive_area_samples": sum(1 for a in areas if a > 0),
        "median_area": statistics.median(areas),
        "min_area": min(areas),
        "max_area": max(areas),
        "max_final_difference": max(
            abs(r["final_relay"] - r["final_relay_plus_direct"]) for r in rows
        ),
    }
    return rows, summary


def initial_condition_sensitivity(
    model: Model,
    protocols: ProtocolSet,
    comparison_id: str,
    selection: Mapping[str, str],
    node: str,
    expected: str,
    *,
    samples: int = 5,
    sample_count: int = 1000,
    seed: int = 11,
    duration_scale: float = 2.0,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Does a comparison's direction on ``node`` survive random initial states?

    Two parts. Structurally, an acyclic network has exactly one fixed point for
    given inputs, so steady-state directions cannot depend on the initial
    state. Empirically, every non-input node starts ON with an independent
    uniform random probability, both matched conditions are simulated (phases
    lengthened by ``duration_scale``), and the end-of-phase direction is
    compared with the exact one (threshold 0.05, as for rates).
    """
    rules = model.rules_for(selection)
    try:
        topological_order(rules)
        acyclic = True
    except NotAcyclicError:
        acyclic = False
    comp = protocols.comparisons[comparison_id]
    rng = random.Random(seed)
    free = set(model.inputs)
    rows: list[dict[str, object]] = []
    for s in range(samples):
        initial = {n: round(rng.random(), 6) for n in rules if n not in free}
        settings = SimulationSettings(
            sample_count=sample_count,
            seed=3000 + s,
            initial_probabilities=initial,
            duration_scale=duration_scale,
        )
        pert = simulate_condition(
            model,
            protocols.conditions[comp.perturbed],
            protocols.interventions,
            selection,
            settings,
        )
        ctrl = simulate_condition(
            model,
            protocols.conditions[comp.control],
            protocols.interventions,
            selection,
            settings,
        )
        p_phase = next(p for p in pert.phases if p.phase_id == comp.phase_perturbed)
        c_phase = next(p for p in ctrl.phases if p.phase_id == comp.phase)
        delta = p_phase.final[node] - c_phase.final[node]
        observed = direction(delta, tolerance=0.05)
        rows.append(
            {
                "sample": s,
                "delta": round(delta, 6),
                "direction": observed,
                "agrees": observed == expected,
                "both_converged": p_phase.converged and c_phase.converged,
            }
        )
    summary = {
        "acyclic_network": acyclic,
        "samples": samples,
        "sample_count": sample_count,
        "initial_distribution": "every non-input node ON with an independent uniform(0, 1) probability",
        "duration_scale": duration_scale,
        "agreeing_samples": sum(r["agrees"] for r in rows),
        "stable": acyclic and all(r["agrees"] for r in rows),
    }
    return rows, summary
