"""Per-node summaries, positions, pairwise precedence and the arm comparison.

Three quantities are kept apart and never collapsed into one statistic:

- **first switch** -- when a node first leaves its starting state, whatever
  happens next (``first_switch_time``);
- **net response** -- whether it ends the phase in a different state
  (``p_net_change``), with reversals (``p_transient_return``) and net changes
  that need at least three switches (``p_net_change_n_switches_min_gt_1``)
  counted separately;
- **perturbation-associated response** -- the difference from the matched
  unperturbed control, computed in ``compare_arms`` on pairs that share their
  starting state and seed.

A node that does not switch before the horizon is reported in two parts: at a
fixed point of its rule at the horizon, or still called to change by its rule
(``p_no_switch_rule_disagrees``): the latter is censored, not a non-response.

Uncertainty intervals here are percentile bootstraps over trajectories. They
treat trajectories as exchangeable draws: initial states are drawn i.i.d., and
event streams come from distinct spread seeds, which is not a proof of
independence. Empirical quantiles of positions (``q025`` .. ``q975``) describe
the spread across trajectories and are not confidence intervals.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from dt_adoc.cascade.events import NET_CHANGE_N_MIN_GT_1, TRANSIENT_RETURN

POSITIONS = ("normalized_rank", "normalized_time", "absolute_time")
#: Positions are computed from reconstructed first-switch times and are for
#: display; order claims come from ``pairwise_precedence``, which counts an
#: order only when it is identifiable from the occupancies.
POSITION_DEFINITIONS = {
    "absolute_time": "reconstructed MaBoSS relative time of the node's first switch (exact when its window held one switch, otherwise an upper bound within that window) after the perturbation boundary (t = 0); dimensionless continuous MaBoSS time with every transition rate 1, not hours and not a count of Boolean updates",
    "normalized_rank": "(r - 1) / (m - 1): r = rank of the node's first switch among the m nodes that switched in that trajectory (average rank on ties); undefined when m < 2",
    "normalized_time": "(t - t_first) / (t_last - t_first) over the first-switch times of the nodes that switched in that trajectory; undefined when t_last == t_first",
}
#: A direction's row is drawn in the figure when at least this share of
#: trajectories switch that way first (or when it holds every switch); every
#: direction with a switch has a row in ``node_summary`` regardless.
DIRECTION_ROW_MIN_FRACTION = 0.05
BOOTSTRAP_REPLICATES = 1000


def first_switch_matrix(events: pd.DataFrame) -> pd.DataFrame:
    """trajectory x node first-switch times (NaN = no switch)."""
    return events.pivot(index="trajectory", columns="node", values="first_switch_time")


def positions(
    events: pd.DataFrame, nodes: list[str] | None = None
) -> dict[str, pd.DataFrame]:
    times = first_switch_matrix(events)
    if nodes is not None:
        times = times[[n for n in nodes if n in times.columns]]
    m = times.notna().sum(axis=1)
    rank = times.rank(axis=1, method="average").sub(1).div((m - 1).where(m > 1), axis=0)
    t0, t1 = times.min(axis=1), times.max(axis=1)
    ntime = times.sub(t0, axis=0).div((t1 - t0).where(t1 > t0), axis=0)
    return {"absolute_time": times, "normalized_rank": rank, "normalized_time": ntime}


def _bootstrap_median_ci(
    x: np.ndarray, rng: np.random.Generator
) -> tuple[float, float]:
    if len(x) < 2:
        return (np.nan, np.nan)
    draws = np.median(
        x[rng.integers(0, len(x), (BOOTSTRAP_REPLICATES, len(x)))], axis=1
    )
    return tuple(np.percentile(draws, [2.5, 97.5]))


class UnknownInitialStateError(ValueError):
    """A node's starting state is unknown in some trajectory."""


def require_known_initial_states(events: pd.DataFrame) -> None:
    """Refuse events in which any node's t = 0 state is unknown.

    Direction, eligibility and switching fractions are all conditioned on the
    starting state, so a node with an unknown one would fall into neither
    direction and be summarised as if it never switched. The default start
    carries every tracked node, so this cannot happen there; a start that does
    not carry a node whose first window is fractional must be refused, not
    guessed.
    """
    unknown = events[events.initial.isna()]
    if len(unknown):
        counts = (
            unknown.groupby("node").trajectory.nunique().sort_values(ascending=False)
        )
        detail = ", ".join(f"{n} ({k} trajectories)" for n, k in counts.head(5).items())
        raise UnknownInitialStateError(
            f"starting state unknown for {len(counts)} node(s): {detail}; carry them in "
            "the starting state (memory_policy all_non_inputs) rather than infer them"
        )


def node_summary(events: pd.DataFrame, *, seed: int = 0) -> pd.DataFrame:
    """One row per (node, first-switch direction with enough trajectories) of one arm.

    Every node gets at least one row, including nodes that never switch
    (``direction = none``).
    """
    require_known_initial_states(events)
    rng = np.random.default_rng(seed)
    pos = positions(events)
    rows = []
    n_traj = events.trajectory.nunique()
    for node, g in events.groupby("node", sort=True):
        g = g.set_index("trajectory").sort_index()
        switched = g.n_switches_min > 0
        init = g.initial
        base = {
            "node": node,
            "n_trajectories": n_traj,
            "p_initial_on": float((init == 1).mean()),
            "p_initial_unknown": float(init.isna().mean()),
            "p_switch": float(switched.mean()),
            "p_switch_given_initial_on": float(switched[init == 1].mean())
            if (init == 1).any()
            else np.nan,
            "p_switch_given_initial_off": float(switched[init == 0].mean())
            if (init == 0).any()
            else np.nan,
            "p_first_on_to_off": float((switched & (init == 1)).mean()),
            "p_first_off_to_on": float((switched & (init == 0)).mean()),
            # Over trajectories whose final state is known; an unknown final
            # is missing, not "unchanged" (``p_final_unknown`` counts them).
            "n_final_known": int(g.final.notna().sum()),
            "p_net_change": (
                float((g.final[g.final.notna()] != init[g.final.notna()]).mean())
                if g.final.notna().any()
                else np.nan
            ),
            "p_n_switches_min_gt_1": float((g.n_switches_min > 1).mean()),
            "p_transient_return": float((g.category == TRANSIENT_RETURN).mean()),
            "p_net_change_n_switches_min_gt_1": float(
                (g.category == NET_CHANGE_N_MIN_GT_1).mean()
            ),
            "p_never_switches": float((~switched).mean()),
            "p_no_switch_rule_agrees": float(
                ((~switched) & (g.rule_disagrees_at_horizon == False)).mean()
            ),
            "p_no_switch_rule_disagrees": float(
                ((~switched) & (g.rule_disagrees_at_horizon == True)).mean()
            ),
            "p_final_unknown": float(g.final.isna().mean()),
            "p_first_switch_unresolved": float(
                (g.first_switch_resolved == False).mean()
            ),
        }
        # Every direction with at least one switch gets a row, so ``none`` means
        # exactly that the node never switched. Whether a row is drawn is a
        # display choice (``shown_in_figure``), never a reason to drop it.
        directions = []
        for label, mask in (
            ("on_to_off", switched & (init == 1)),
            ("off_to_on", switched & (init == 0)),
        ):
            if mask.any():
                shown = bool(
                    mask.mean() >= DIRECTION_ROW_MIN_FRACTION
                    or switched[mask].sum() == switched.sum()
                )
                directions.append((label, mask, shown))
        share = {d: float(m.sum() / max(switched.sum(), 1)) for d, m, _ in directions}
        if not directions:
            rows.append(
                {
                    **base,
                    "direction": "none",
                    "direction_share": np.nan,
                    "n_contributing": 0,
                    "shown_in_figure": False,
                }
            )
            continue
        for label, mask, shown in directions:
            idx = mask[mask].index
            row = {
                **base,
                "direction": label,
                "direction_share": share[label],
                "n_contributing": len(idx),
                "mixed_direction": len(directions) > 1,
                "shown_in_figure": shown,
            }
            for name in POSITIONS:
                x = (
                    pos[name].loc[idx, node].dropna().to_numpy()
                    if node in pos[name]
                    else np.array([])
                )
                row[f"{name}_n"] = len(x)
                if len(x):
                    q = np.quantile(x, [0.025, 0.25, 0.5, 0.75, 0.975])
                    lo, hi = _bootstrap_median_ci(x, rng)
                else:
                    q, lo, hi = [np.nan] * 5, np.nan, np.nan
                for qn, v in zip(("q025", "q25", "median", "q75", "q975"), q):
                    row[f"{name}_{qn}"] = float(v)
                row[f"{name}_median_ci_low"] = float(lo)
                row[f"{name}_median_ci_high"] = float(hi)
            rows.append(row)
    out = pd.DataFrame(rows)
    # When nothing switched no row carries the position columns; add them
    # empty (NaN, as on every ``direction = none`` row) so an inert
    # perturbation yields the same schema as any other.
    for name in POSITIONS:
        for suffix in POSITION_SUFFIXES:
            col = f"{name}_{suffix}"
            if col not in out.columns:
                out[col] = np.nan
    out["mixed_direction"] = out.get("mixed_direction", False)
    out["mixed_direction"] = out["mixed_direction"].fillna(False).astype(bool)
    return out


POSITION_SUFFIXES = (
    "n",
    "q025",
    "q25",
    "median",
    "q75",
    "q975",
    "median_ci_low",
    "median_ci_high",
)

PRECEDENCE_COLUMNS = [
    "node_a",
    "node_b",
    "n_trajectories",
    "n_both_switch",
    "frac_comparable",
    "n_a_first",
    "n_b_first",
    "n_order_unresolved",
    "p_a_first",
    "n_only_a_switches",
    "n_only_b_switches",
]


def pairwise_precedence(
    events: pd.DataFrame, nodes: list[str] | None = None
) -> pd.DataFrame:
    """P(A first | both switch, order identifiable) for every ordered pair.

    The first switch of a node is only known to lie in
    ``[first_switch_lower, first_switch_upper]`` (``dt_adoc.cascade.events``):
    a window can hide an earlier out-and-back pair. A is counted first only
    when its interval ends before B's begins, B first in the mirror case, and
    the pair is ``n_order_unresolved`` otherwise (their first switches share a
    window). ``p_a_first`` is over the identifiable pairs only, and
    ``frac_comparable`` is the share of trajectories where both switched.
    Events without interval columns are treated as exact points. With fewer
    than two switching nodes the table is empty but keeps its columns.
    """
    times = first_switch_matrix(events)
    if "first_switch_lower" in events.columns:
        lower = events.pivot(
            index="trajectory", columns="node", values="first_switch_lower"
        )
        upper = events.pivot(
            index="trajectory", columns="node", values="first_switch_upper"
        )
    else:
        lower = upper = times
    if nodes is not None:
        keep = [n for n in nodes if n in times.columns]
        times, lower, upper = times[keep], lower[keep], upper[keep]
    keep = times.columns[times.notna().any()]
    times, lower, upper = times[keep], lower[keep], upper[keep]
    cols = list(keep)
    lo, up = lower.to_numpy(), upper.to_numpy()
    present = ~np.isnan(times.to_numpy())
    n = len(lo)
    rows = []
    for i, x in enumerate(cols):
        for j, y in enumerate(cols):
            if i == j:
                continue
            both = present[:, i] & present[:, j]
            nb = int(both.sum())
            a_first = int((up[both, i] < lo[both, j]).sum())
            b_first = int((up[both, j] < lo[both, i]).sum())
            resolved = a_first + b_first
            rows.append(
                {
                    "node_a": x,
                    "node_b": y,
                    "n_trajectories": n,
                    "n_both_switch": nb,
                    "frac_comparable": nb / n if n else np.nan,
                    "n_a_first": a_first,
                    "n_b_first": b_first,
                    "n_order_unresolved": nb - resolved,
                    "p_a_first": a_first / resolved if resolved else np.nan,
                    "n_only_a_switches": int((present[:, i] & ~present[:, j]).sum()),
                    "n_only_b_switches": int((~present[:, i] & present[:, j]).sum()),
                }
            )
    return pd.DataFrame(rows, columns=PRECEDENCE_COLUMNS)


def compare_arms(
    perturbed: pd.DataFrame, control: pd.DataFrame, *, seed: int = 0
) -> pd.DataFrame:
    """Per node, perturbed vs matched control on pairs sharing state and seed.

    Pair counts are descriptive. A shared seed does not pair the event streams,
    so ``n_switch_perturbed_only`` is not an individual counterfactual effect.
    The differences are paired-bootstrap estimates over pairs; net change is
    compared only on the ``n_pairs_final_known`` pairs whose final states are
    both known.
    """
    rng = np.random.default_rng(seed)
    p = perturbed.set_index(["trajectory", "node"]).sort_index()
    c = control.set_index(["trajectory", "node"]).sort_index()
    if not p.index.equals(c.index):
        raise ValueError("arms do not cover the same trajectories and nodes")
    if (
        not (p.seed == c.seed).all()
        or not (p.initial.fillna(-1) == c.initial.fillna(-1)).all()
    ):
        raise ValueError("arms are not paired on seed and starting state")
    rows = []
    for node in sorted(p.index.get_level_values("node").unique()):
        pn, cn = p.xs(node, level="node"), c.xs(node, level="node")
        sp, sc = (pn.n_switches_min > 0).to_numpy(), (cn.n_switches_min > 0).to_numpy()
        # Net change is compared only on pairs whose final states are both
        # known: an unknown final is missing, never "unchanged".
        known = (pn.final.notna() & cn.final.notna()).to_numpy()
        netp = (pn.final != pn.initial).to_numpy()[known]
        netc = (cn.final != cn.initial).to_numpy()[known]
        diff_switch = sp.astype(float) - sc
        diff_net = netp.astype(float) - netc
        idx = rng.integers(0, len(sp), (BOOTSTRAP_REPLICATES, len(sp)))
        ci_s = np.percentile(diff_switch[idx].mean(axis=1), [2.5, 97.5])
        if known.all():
            # Same resample as the switch difference: with no unknown final the
            # interval is exactly the one computed before unknowns were excluded.
            ci_n = np.percentile(diff_net[idx].mean(axis=1), [2.5, 97.5])
        elif len(diff_net):
            idx_n = rng.integers(
                0, len(diff_net), (BOOTSTRAP_REPLICATES, len(diff_net))
            )
            ci_n = np.percentile(diff_net[idx_n].mean(axis=1), [2.5, 97.5])
        else:
            ci_n = (np.nan, np.nan)
        rows.append(
            {
                "node": node,
                "n_pairs": len(sp),
                "p_switch_perturbed": sp.mean(),
                "p_switch_control": sc.mean(),
                "delta_p_switch": diff_switch.mean(),
                "delta_p_switch_ci_low": ci_s[0],
                "delta_p_switch_ci_high": ci_s[1],
                "n_pairs_final_known": int(known.sum()),
                "p_net_change_perturbed": netp.mean() if len(netp) else np.nan,
                "p_net_change_control": netc.mean() if len(netc) else np.nan,
                "delta_p_net_change": diff_net.mean() if len(diff_net) else np.nan,
                "delta_p_net_change_ci_low": ci_n[0],
                "delta_p_net_change_ci_high": ci_n[1],
                "n_switch_both": int((sp & sc).sum()),
                "n_switch_perturbed_only": int((sp & ~sc).sum()),
                "n_switch_control_only": int((~sp & sc).sum()),
                "n_switch_neither": int((~sp & ~sc).sum()),
                "median_first_time_perturbed": float(np.nanmedian(pn.first_switch_time))
                if sp.any()
                else np.nan,
                "median_first_time_control": float(np.nanmedian(cn.first_switch_time))
                if sc.any()
                else np.nan,
                "p_on_to_off_perturbed": float(
                    (sp & (pn.initial == 1).to_numpy()).mean()
                ),
                "p_on_to_off_control": float(
                    (sc & (cn.initial == 1).to_numpy()).mean()
                ),
                "p_off_to_on_perturbed": float(
                    (sp & (pn.initial == 0).to_numpy()).mean()
                ),
                "p_off_to_on_control": float(
                    (sc & (cn.initial == 0).to_numpy()).mean()
                ),
            }
        )
    return pd.DataFrame(rows)
