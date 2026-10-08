"""Progesterone withdrawal after the full hormone cocktail, model v0.5.1.

Protocol (MaBoSS relative time throughout; never hours):
  basal_maternal -> e2_primed_maternal -> hormone_treated_maternal
  (repo lineage, every phase at the converged horizon 25), then a fourth phase
  continued from the exact terminal joint state of the cocktail phase:
    * withdrawal : E2 + cAMP + XAV939 kept ON, IN_PROGESTIN -> OFF
    * control    : full cocktail kept ON (matched unperturbed twin)
    * mifepristone: cocktail + IN_MIFEPRISTONE (logical-equivalence check)

Two estimators, kept separate:
  A. Aggregate: R independent replicate runs (distinct seeds, each re-running
     the whole lineage) x N trajectories. The replicate is the independent unit;
     intervals are t-intervals across replicates (MaBoSS node values are dwell
     fractions, not Bernoulli counts, so no binomial SE is used on them).
  B. Per-trajectory: K single-trajectory MaBoSS runs (sample_count = 1, one
     seed each) from the same continuation, read at tick 0.01. Each run is one
     independent Bernoulli / event-time draw, so exact binomial (Clopper-Pearson)
     and bootstrap intervals apply to these.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from dt_adoc.concordance.simulate import CONVERGED_PHASE_HORIZON, protocol_lineage  # noqa: E402
from dt_adoc.model.provenance import describe_file  # noqa: E402
from dt_adoc.protocols.conditions import get_protocol  # noqa: E402
from dt_adoc.simulation.runner import (  # noqa: E402
    _input_override_text,
    joint_continuation_from_last_states,
    protocol_continuation,
    run_cmaboss_condition,
    run_protocol,
)

MV = "adoc-literature-superset-v0.5.1"
OUT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models/superset" / MV
COND_CFG = MODEL_DIR / "conditions/hormone_treated_maternal.cfg"

REPLICATES = 10          # estimator A
TRAJ_PER_REP = 5000
AGG_TICK = 0.05
SINGLE_RUNS = 2000       # estimator B
SINGLE_TICK = 0.01
HORIZON = CONVERGED_PHASE_HORIZON  # 25.0, same regime as the repo's converged readouts


def cocktail_terminal(seed: int):
    lineage = protocol_lineage("hormone_treated_maternal", model_version=MV)
    cont = None
    for i, pid in enumerate(lineage):
        res = run_protocol(pid, model_version=MV, continuation=cont, seed=seed,
                           sample_count=TRAJ_PER_REP, phase_horizon=HORIZON)
        if i + 1 < len(lineage):
            cont = protocol_continuation(lineage[i + 1], res, model_version=MV)
    return lineage, res.final_result


def arm_inputs(arm: str) -> dict[str, bool]:
    inputs = dict(get_protocol("hormone_treated_maternal", model_version=MV).steps[0].input_states)
    if arm == "withdrawal":
        inputs["IN_PROGESTIN"] = False
    elif arm == "mifepristone":
        inputs["IN_MIFEPRISTONE"] = True
    return inputs


def continuation_for(terminal, inputs):
    # Carry EVERY non-input node, so the fourth phase starts exactly in the
    # cocktail terminal state (readouts included) and any change is caused by
    # the input switch, not by a readout re-initialised to FALSE.
    return joint_continuation_from_last_states(
        last_states_probtraj=terminal.last_states_probtraj, model_version=MV,
        excluded_nodes=set(inputs), forced_nodes=inputs,
        memory_node_policy="all_non_inputs")


def run_phase(cont, inputs, *, seed, n, tick):
    return run_cmaboss_condition(
        model_version=MV, condition_cfg=COND_CFG,
        override_texts=[_input_override_text(inputs), f"max_time = {HORIZON};\ntime_tick = {tick};\n"],
        continuation=cont, seed=seed, sample_count=n)


def t_ci(values: np.ndarray, axis=0):
    m = values.mean(axis=axis)
    sd = values.std(axis=axis, ddof=1)
    half = stats.t.ppf(0.975, values.shape[axis] - 1) * sd / np.sqrt(values.shape[axis])
    return m, m - half, m + half, sd


def clopper_pearson(k, n, alpha=0.05):
    lo = 0.0 if k == 0 else stats.beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return lo, hi


def switch_events(traj: pd.DataFrame, tick: float):
    """Per node: (initial, final, first switch time or NaN, n_reversals)."""
    t = traj.index.to_numpy(dtype=float)
    out = {}
    for node in traj.columns:
        # Tick occupancies carry float dust (0.9999999999); snap within 1e-9.
        x = traj[node].to_numpy(dtype=float)
        x = np.where(np.abs(x) < 1e-9, 0.0, np.where(np.abs(x - 1) < 1e-9, 1.0, x))
        # A switch inside the first tick leaves x[0] fractional; the old state is
        # then the complement of the next whole-tick state.
        x0 = round(x[0]) if x[0] in (0.0, 1.0) else 1 - round(x[1])
        diff = np.nonzero(x != x0)[0]
        if diff.size == 0:
            out[node] = (x0, x0, np.nan, 0)
            continue
        k = diff[0]
        occ_old = x[k] if x0 == 1 else 1.0 - x[k]   # fraction of tick k still in old state
        ts = t[k] + occ_old * tick
        # State changes between whole-tick states, plus fractional ticks that
        # return to the same state (an out-and-back inside one tick).
        clean = x[(x == 0) | (x == 1)]
        n_changes = int(np.sum(clean[1:] != clean[:-1]))
        frac = (x > 0) & (x < 1)
        prev_next_same = frac[1:-1] & (x[:-2] == x[2:]) & ((x[:-2] == 0) | (x[:-2] == 1))
        n_changes += 2 * int(np.sum(prev_next_same))
        out[node] = (x0, round(x[-1]), ts, max(n_changes - 1, 0))
    return out


def main():
    t0 = time.time()
    arms = ["withdrawal", "control", "mifepristone"]
    agg = {a: [] for a in arms}
    finals = {a: [] for a in arms}
    terminals = {}
    lineage = None
    for r in range(REPLICATES):
        seed = 1 + r
        lineage, term = cocktail_terminal(seed)
        terminals[seed] = term
        for a in arms:
            inp = arm_inputs(a)
            res = run_phase(continuation_for(term, inp), inp, seed=seed, n=TRAJ_PER_REP, tick=AGG_TICK)
            agg[a].append(res.nodes_probtraj)
            finals[a].append(res.last)
        print(f"replicate {r + 1}/{REPLICATES} done {time.time() - t0:.0f}s", flush=True)

    nodes = sorted(agg["withdrawal"][0].columns)
    times = agg["withdrawal"][0].index.to_numpy(dtype=float)
    rows = []
    for a in arms:
        cube = np.stack([df[nodes].to_numpy() for df in agg[a]])  # rep x time x node
        m, lo, hi, _ = t_ci(cube)
        for j, n in enumerate(nodes):
            rows.append(pd.DataFrame({"arm": a, "node": n, "time": times,
                                      "mean": m[:, j], "ci_low": lo[:, j], "ci_high": hi[:, j]}))
    pd.concat(rows).to_csv(OUT / "aggregate_timecourse.tsv", sep="\t", index=False)

    # Initial (t=0 of phase 4, i.e. end of cocktail) and final aggregate values.
    fin_rows = []
    for a in arms:
        start = np.array([[df[n].iloc[0] for n in nodes] for df in agg[a]])
        end = np.array([[f.get(n, np.nan) for n in nodes] for f in finals[a]])
        ms, los, his, _ = t_ci(start)
        me, loe, hie, sde = t_ci(end)
        for j, n in enumerate(nodes):
            fin_rows.append({"arm": a, "node": n, "start_mean": ms[j], "final_mean": me[j],
                             "final_ci_low": loe[j], "final_ci_high": hie[j], "final_sd_across_reps": sde[j],
                             "final_min": end[:, j].min(), "final_max": end[:, j].max()})
    fin = pd.DataFrame(fin_rows)
    fin.to_csv(OUT / "aggregate_final_state.tsv", sep="\t", index=False)
    wd = fin[fin.arm == "withdrawal"].set_index("node")
    mf = fin[fin.arm == "mifepristone"].set_index("node")
    mife_max_abs_diff = float((wd.final_mean - mf.final_mean).abs().max())
    # Paired withdrawal-vs-control absolute change per replicate (same seed, same start).
    paired = []
    for j, n in enumerate(nodes):
        d = np.array([finals["withdrawal"][r].get(n, np.nan) - finals["control"][r].get(n, np.nan)
                      for r in range(REPLICATES)])
        m, lo, hi, sd = t_ci(d)
        p = stats.ttest_1samp(d, 0).pvalue if sd > 0 else (0.0 if abs(m) > 0 else 1.0)
        paired.append({"node": n, "delta_mean": m, "delta_ci_low": lo, "delta_ci_high": hi,
                       "delta_sd": sd, "p_paired_t": p})
    pd.DataFrame(paired).to_csv(OUT / "withdrawal_vs_control_delta.tsv", sep="\t", index=False)

    # ---- Estimator B: single trajectories --------------------------------------
    inp = arm_inputs("withdrawal")
    cont = continuation_for(terminals[1], inp)
    ev_rows = []
    for k in range(SINGLE_RUNS):
        res = run_phase(cont, inp, seed=100_001 + k, n=1, tick=SINGLE_TICK)
        for node, (x0, x1, ts, nrev) in switch_events(res.nodes_probtraj[nodes], SINGLE_TICK).items():
            ev_rows.append({"traj": k, "node": node, "initial": x0, "final": x1,
                            "switch_time": ts, "reversals": nrev})
        if (k + 1) % 500 == 0:
            print(f"single trajectories {k + 1}/{SINGLE_RUNS} {time.time() - t0:.0f}s", flush=True)
    ev = pd.DataFrame(ev_rows)
    ev.to_csv(OUT / "per_trajectory_events.tsv", sep="\t", index=False)

    meta = {
        "model_version": MV, "lineage": list(lineage) + ["<phase 4 arm>"],
        "network_bnd": describe_file(MODEL_DIR / "network.bnd"),
        "baseline_cfg": describe_file(MODEL_DIR / "baseline.cfg"),
        "condition_cfg": describe_file(COND_CFG),
        "phase_horizon": HORIZON, "replicates": REPLICATES, "replicate_seeds": list(range(1, REPLICATES + 1)),
        "trajectories_per_replicate": TRAJ_PER_REP, "aggregate_tick": AGG_TICK,
        "single_runs": SINGLE_RUNS, "single_seeds": [100_001, 100_000 + SINGLE_RUNS], "single_tick": SINGLE_TICK,
        "single_runs_continuation_from_replicate_seed": 1,
        "cocktail_terminal_joint_states_retained": cont.retained_state_count,
        "arm_inputs": {a: arm_inputs(a) for a in arms},
        "withdrawal_vs_mifepristone_max_abs_final_diff": mife_max_abs_diff,
        "maboss_python": __import__("importlib.metadata").metadata.version("maboss"),
        "runtime_s": round(time.time() - t0, 1),
    }
    (OUT / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")
    print(json.dumps(meta, indent=2, default=str))


if __name__ == "__main__":
    main()
