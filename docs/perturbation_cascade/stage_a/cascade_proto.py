"""Stage A prototype: paired single-trajectory perturbation runs and event extraction.

Scratch code. Everything executes through dt_adoc.simulation.runner.
"""

from __future__ import annotations

import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from dt_adoc.concordance.simulate import protocol_lineage  # noqa: E402
from dt_adoc.maboss_adapter import render_network_with_logic_overrides  # noqa: E402
from dt_adoc.model.runtime import resolve_model  # noqa: E402
from dt_adoc.perturbations.engine import _evaluable, _value  # noqa: E402
from dt_adoc.protocols.conditions import get_protocol  # noqa: E402
from dt_adoc.simulation.runner import (  # noqa: E402
    _input_override_text,
    joint_continuation_from_last_states,
    protocol_continuation,
    run_cmaboss_condition,
    run_protocol,
)

MV = "adoc-literature-superset-v0.6.0"
SNAP = 1e-9


def snap(x):
    return np.where(x < SNAP, 0.0, np.where(x > 1 - SNAP, 1.0, x))


def node_events(x, tick, s0):
    """Events of one node in one trajectory from tick occupancies.

    x: occupancy of ON per window (window j = [j*tick, (j+1)*tick)).
    s0: known start state (0/1) or None.
    Returns dict with initial, final (None if last window fractional), n_min
    (minimum switch count consistent with the occupancies), first/last switch
    times, and whether each is resolved (window consistent with one switch).
    """
    x = snap(np.asarray(x, float))
    whole = (x == 0.0) | (x == 1.0)
    if s0 is None:
        s0 = int(x[0]) if whole[0] else None
    # DP over boundary states: minimum switches.
    INF = 10**9
    cost = [0, 0] if s0 is None else ([0, INF] if s0 == 0 else [INF, 0])
    for v, w in zip(x, whole):
        new = [INF, INF]
        for s in (0, 1):
            if cost[s] >= INF:
                continue
            if w:
                if s == v:
                    new[s] = min(new[s], cost[s])
            else:
                for e in (0, 1):
                    new[e] = min(new[e], cost[s] + (1 if s != e else 2))
        cost = new
    final = int(x[-1]) if whole[-1] else None
    n_min = cost[final] if final is not None else min(cost)
    frac = np.nonzero(~whole)[0]
    out = {"initial": s0, "final": final, "n_min": int(n_min),
           "first_time": np.nan, "first_resolved": None,
           "last_time": np.nan, "last_resolved": None}
    if frac.size == 0:
        return out
    j = frac[0]
    # State entering window j: known if j == 0 (s0) or window j-1 whole.
    s_in = s0 if j == 0 else int(x[j - 1])
    if s_in is not None:
        occ_in = x[j] if s_in == 1 else 1 - x[j]
        out["first_time"] = j * tick + occ_in * tick
        s_out = None if j + 1 >= len(x) or not whole[j + 1] else int(x[j + 1])
        out["first_resolved"] = bool(s_out is not None and s_out != s_in)
    k = frac[-1]
    s_in_k = s0 if k == 0 else (int(x[k - 1]) if whole[k - 1] else None)
    if s_in_k is not None:
        occ_in = x[k] if s_in_k == 1 else 1 - x[k]
        out["last_time"] = k * tick + occ_in * tick
        s_out = final if k == len(x) - 1 else (int(x[k + 1]) if whole[k + 1] else None)
        out["last_resolved"] = bool(s_out is not None and s_out != s_in_k)
    return out


def classify(e):
    n = e["n_min"]
    if n == 0:
        return "no_switch"
    if e["final"] is None:
        return "unresolved_end"
    if e["final"] == e["initial"]:
        return "transient_return"
    return "single_switch" if n == 1 else "multiple_net_change"


def lineage_terminal(start, seed, n, horizon):
    lin = protocol_lineage(start, model_version=MV)
    cont = None
    for i, pid in enumerate(lin):
        res = run_protocol(pid, model_version=MV, continuation=cont, seed=seed,
                           sample_count=n, phase_horizon=horizon)
        if i + 1 < len(lin):
            cont = protocol_continuation(lin[i + 1], res, model_version=MV)
    return lin, res


def perturbation_continuation(term_result, start, policy, cutoff, input_states):
    return joint_continuation_from_last_states(
        last_states_probtraj=term_result.last_states_probtraj, model_version=MV,
        excluded_nodes=set(input_states), forced_nodes=input_states,
        memory_node_policy=policy, probability_cutoff=cutoff, source_protocol=start)


def sample_states(cont, n, rng):
    states = list(cont.distribution)
    p = np.array([cont.distribution[s] for s in states], float)
    idx = rng.choice(len(states), size=n, p=p / p.sum())
    return [states[i] for i in idx]


def _one(args):
    (cont, state, input_states, cfg, seed, horizon, tick, interventions) = args
    c = replace(cont, distribution={tuple(state): 1.0})
    r = run_cmaboss_condition(
        model_version=MV, condition_cfg=cfg,
        override_texts=[_input_override_text(input_states),
                        f"max_time = {horizon};\ntime_tick = {tick};\n"],
        continuation=c, seed=seed, sample_count=1, interventions=tuple(interventions))
    tab = r.nodes_probtraj
    network_sha = r.executed_network["network_sha256"]
    overrides = r.executed_network["logic_overrides"]
    r.release() if hasattr(r, "release") else None
    return tab.to_numpy(dtype=float), list(tab.columns), network_sha, overrides


def run_arm(cont, states, seeds, input_states, cfg, horizon, tick, interventions=(), workers=8):
    jobs = [(cont, s, input_states, cfg, int(sd), horizon, tick, tuple(interventions))
            for s, sd in zip(states, seeds)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, jobs, chunksize=8))


def extract(runs, cont, states, tick):
    rows = []
    for k, (arr, cols, sha, _ov) in enumerate(runs):
        known = dict(zip(cont.node_ids, states[k]))
        for j, node in enumerate(cols):
            e = node_events(arr[:, j], tick, known.get(node))
            e["traj"] = k
            e["node"] = node
            e["category"] = classify(e)
            rows.append(e)
    return pd.DataFrame(rows)


def logic_table(overrides):
    spec = resolve_model(MV)
    text = render_network_with_logic_overrides(spec.network_bnd.read_text(), logic_overrides=overrides)
    logic = dict(re.findall(r"Node\s+(\w+)\s*\{\s*logic\s*=\s*([^;]+);", text))
    return {n: _evaluable(e) for n, e in logic.items()}


def at_risk(ev, logic, input_states):
    """Per trajectory: for each node, does its rule disagree with its final value?"""
    out = []
    for k, g in ev.groupby("traj"):
        st = {**{n: bool(v) for n, v in input_states.items()},
              **{r.node: bool(r.final) for r in g.itertuples() if r.final is not None}}
        for r in g.itertuples():
            if r.final is None or r.node not in logic:
                out.append(None)
                continue
            expr, names = logic[r.node]
            if not names <= set(st):
                out.append(None)
                continue
            out.append(bool(_value(expr, st) != st[r.node]))
    return out


def positions(ev, nodes=None):
    """Per-trajectory rank and normalised-time position of first switches."""
    w = ev.pivot(index="traj", columns="node", values="first_time")
    if nodes is not None:
        w = w[[n for n in nodes if n in w.columns]]
    w = w.loc[:, w.notna().any()]
    m = w.notna().sum(axis=1)
    rank = w.rank(axis=1, method="average").sub(1).div((m - 1).where(m > 1), axis=0)
    t0, t1 = w.min(axis=1), w.max(axis=1)
    ntime = w.sub(t0, axis=0).div((t1 - t0).where(t1 > t0), axis=0)
    return w, rank, ntime


def precedence(w):
    cols = list(w.columns)
    a = w.to_numpy()
    rows = []
    for i, x in enumerate(cols):
        for j, y in enumerate(cols):
            if i == j:
                continue
            both = ~np.isnan(a[:, i]) & ~np.isnan(a[:, j])
            nb = int(both.sum())
            k = int((a[both, i] < a[both, j]).sum())
            rows.append({"a": x, "b": y, "n_both": nb, "frac_comparable": nb / len(a),
                         "p_a_first": k / nb if nb else np.nan})
    return pd.DataFrame(rows)


if os.environ.get("CASCADE_PROTO_SELFTEST"):
    print(node_events([1, 1, 0.3, 0, 0], 0.1, 1))
    print(node_events([1, 0.5, 1, 1], 0.1, 1))
