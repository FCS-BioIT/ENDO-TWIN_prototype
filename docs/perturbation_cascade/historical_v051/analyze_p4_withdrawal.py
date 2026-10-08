"""Statistics and figures for the progesterone-withdrawal run (reads run outputs only)."""

from __future__ import annotations

import itertools
import json
import re
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def structural_depth(bnd: Path, source: str = "IN_PROGESTIN") -> dict[str, int]:
    text = bnd.read_text()
    logic = dict(re.findall(r"Node\s+(\w+)\s*\{\s*logic\s*=\s*([^;]+);", text))
    targets: dict[str, set[str]] = {}
    for node, expr in logic.items():
        for reg in set(re.findall(r"[A-Za-z_]\w*", expr)) - {"and", "or", "not", node}:
            targets.setdefault(reg, set()).add(node)
    depth, frontier = {source: 0}, [source]
    while frontier:
        nxt = []
        for n in frontier:
            for t in targets.get(n, ()):
                if t not in depth:
                    depth[t] = depth[n] + 1
                    nxt.append(t)
        frontier = nxt
    return depth
RNG = np.random.default_rng(20260928)
BOOT = 4000

BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})

MILESTONES = {
    "E_PGR": "Epithelial PGR off",
    "S_PGR": "Stromal PGR off",
    "E_SECRETORY_STATE": "Secretory program off",
    "S_DECIDUALIZED": "Decidual core off",
    "OUT_STROMAL_DECIDUALIZED": "OUT stromal decidualized off",
    "OUT_EPITHELIAL_RECEPTIVE": "OUT epithelial receptive off",
    "OUT_MATERNAL_ADHESION_COMPETENCE": "OUT adhesion competence off",
    "S_HAND2": "HAND2 off",
    "E_ESTROGENIC_PROLIFERATION": "Estrogenic proliferation ON",
}


def trigger_delays(ev: pd.DataFrame, bnd: Path, inputs: dict[str, bool]) -> pd.DataFrame:
    """Replay each trajectory against the Boolean rules.

    For every switch, the enabling time is the last moment the node's rule
    started to disagree with its current value, and the trigger is the event
    that caused that. The delay is switch time minus enabling time. A switch
    that happens while its rule does not call for it raises: that would be a
    causal violation.
    """
    logic = dict(re.findall(r"Node\s+(\w+)\s*\{\s*logic\s*=\s*([^;]+);", bnd.read_text()))
    code = {n: compile(e, n, "eval") for n, e in logic.items() if n not in inputs}
    rows = []
    for k, g in ev.groupby("traj"):
        state = {**inputs, **{r.node: bool(r.initial) for r in g.itertuples()}}
        enabled_at, trig = {}, {}
        for n, c in code.items():
            if eval(c, {}, state) != state[n]:
                enabled_at[n], trig[n] = 0.0, "IN_PROGESTIN"
        for r in g[g.switch_time.notna()].sort_values("switch_time").itertuples():
            if r.node not in enabled_at:
                raise AssertionError(f"traj {k}: {r.node} switched while its rule did not call for it")
            rows.append({"traj": k, "node": r.node, "switch_time": r.switch_time,
                         "enabled_at": enabled_at[r.node], "trigger": trig[r.node],
                         "delay": r.switch_time - enabled_at[r.node]})
            state[r.node] = not state[r.node]
            for n, c in code.items():
                wants = eval(c, {}, state) != state[n]
                if wants and n not in enabled_at:
                    enabled_at[n], trig[n] = r.switch_time, r.node
                elif not wants:
                    enabled_at.pop(n, None)
                    trig.pop(n, None)
    return pd.DataFrame(rows)


def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else stats.beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(1 - a / 2, k + 1, n - k)
    return lo, hi


def boot_median_ci(x):
    idx = RNG.integers(0, len(x), size=(BOOT, len(x)))
    meds = np.median(x[idx], axis=1)
    return np.percentile(meds, [2.5, 97.5])


def boot_quantile_ci(x, q):
    idx = RNG.integers(0, len(x), size=(BOOT, len(x)))
    return np.percentile(np.quantile(x[idx], q, axis=1), [2.5, 97.5])


def main():
    meta = json.loads((OUT / "run_metadata.json").read_text())
    ev = pd.read_csv(OUT / "per_trajectory_events.tsv", sep="\t")
    K = ev.traj.nunique()
    assert int(ev.reversals.max()) == 0, "a node switched more than once; the one-switch summary would be wrong"

    # ---- 1. switch-time table ---------------------------------------------------
    rows = []
    for node, g in ev.groupby("node"):
        sw = g[g.switch_time.notna()]
        if sw.empty:
            continue
        direction = "ON->OFF" if sw.initial.iloc[0] == 1 else "OFF->ON"
        assert (sw.initial == sw.initial.iloc[0]).all()
        eligible = g[g.initial == sw.initial.iloc[0]]
        t = sw.switch_time.to_numpy()
        mlo, mhi = boot_median_ci(t)
        plo, phi = cp(len(sw), len(eligible))
        rows.append({"node": node, "direction": direction, "n_eligible": len(eligible), "n_switched": len(sw),
                     "frac_switched": len(sw) / len(eligible), "frac_ci_low": plo, "frac_ci_high": phi,
                     "median": np.median(t), "median_ci_low": mlo, "median_ci_high": mhi,
                     "mean": t.mean(), "p2.5": np.quantile(t, .025), "p25": np.quantile(t, .25),
                     "p75": np.quantile(t, .75), "p97.5": np.quantile(t, .975), "max": t.max()})
    sw_tab = pd.DataFrame(rows)

    # ---- 2. pairwise precedence ---------------------------------------------------
    wide = ev.pivot(index="traj", columns="node", values="switch_time")
    switching = sw_tab.node.tolist()
    prec_rows = []
    for a, b in itertools.permutations(switching, 2):
        both = wide[[a, b]].dropna()
        n = len(both)
        if n == 0:
            continue
        k = int((both[a] < both[b]).sum())
        lo, hi = cp(k, n)
        p = stats.binomtest(k, n, 0.5).pvalue if n else np.nan
        prec_rows.append({"first": a, "second": b, "n_both": n, "k_first_before": k, "p_first_before": k / n,
                          "ci_low": lo, "ci_high": hi, "p_binom_vs_half": p})
    prec = pd.DataFrame(prec_rows)
    # Holm over unordered pairs (one test per pair: use the a<b orientation).
    und = prec[prec["first"] < prec["second"]].copy()
    m = len(und)
    order = np.argsort(und.p_binom_vs_half.to_numpy())
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * und.p_binom_vs_half.to_numpy()[i]))
        adj[i] = running
    und["p_holm"] = adj
    prec = prec.merge(und[["first", "second", "p_holm"]], how="left", on=["first", "second"])
    swapped = und.rename(columns={"first": "second", "second": "first"})[["first", "second", "p_holm"]]
    prec = prec.set_index(["first", "second"])
    prec["p_holm"] = prec["p_holm"].fillna(swapped.set_index(["first", "second"])["p_holm"])
    prec = prec.reset_index()
    prec.to_csv(OUT / "pairwise_precedence.tsv", sep="\t", index=False)

    # Obligate predecessors: nodes that switched first in EVERY trajectory where
    # both switched. Disjunctive (OR) dependencies have none, so this is not a depth.
    obligate = prec[(prec.k_first_before == prec.n_both) & (prec.n_both > 0)]
    preds = {n: set(obligate[obligate.second == n]["first"]) for n in switching}
    # Structural depth: shortest regulatory path from IN_PROGESTIN in network.bnd
    # = the minimum number of asynchronous update events before the node can move.
    tier = structural_depth(ROOT / "models/superset" / meta["model_version"] / "network.bnd")
    sw_tab["tier"] = sw_tab.node.map(tier)
    sw_tab["obligate_predecessors"] = sw_tab.node.map(lambda n: ";".join(sorted(preds[n])))
    # Empirical event rank: position of this switch in the trajectory's event sequence (1 = first).
    ranks = wide[switching].rank(axis=1, method="first")
    for col, fn in (("rank_median", np.nanmedian), ("rank_p2.5", lambda a: np.nanpercentile(a, 2.5)),
                    ("rank_p97.5", lambda a: np.nanpercentile(a, 97.5))):
        sw_tab[col] = sw_tab.node.map(lambda n: fn(ranks[n].to_numpy()))
    sw_tab = sw_tab.sort_values(["median"]).reset_index(drop=True)
    sw_tab.to_csv(OUT / "switch_times.tsv", sep="\t", index=False)

    # ---- 3. milestone orderings ----------------------------------------------------
    ms = [n for n in MILESTONES if n in wide.columns]
    order_counts = Counter()
    for _, r in wide[ms].iterrows():
        present = r.dropna().sort_values()
        order_counts[" < ".join(present.index)] += 1
    ms_pairs = prec[prec["first"].isin(ms) & prec["second"].isin(ms)].copy()

    # ---- 4. final phenotype & absorption ---------------------------------------------
    last = ev.pivot(index="traj", columns="node", values="final")
    pheno_nodes = ["OUT_EPITHELIAL_RECEPTIVE", "OUT_STROMAL_DECIDUALIZED", "OUT_MATERNAL_ADHESION_COMPETENCE",
                   "OUT_STABLE_ADHESION", "E_ESTROGENIC_PROLIFERATION", "X_ANTIADHESIVE_ROUTE"]
    ph_rows = []
    for n in pheno_nodes:
        k = int(last[n].sum())
        lo, hi = cp(k, K)
        ph_rows.append({"node": n, "k_on": k, "n": K, "p_on": k / K, "cp_low": lo, "cp_high": hi})
    pheno = pd.DataFrame(ph_rows)
    pheno.to_csv(OUT / "final_phenotype_per_trajectory.tsv", sep="\t", index=False)
    classes = last[pheno_nodes].astype(int).astype(str).agg("".join, axis=1).value_counts()
    absorb = wide.max(axis=1).to_numpy()
    absorb_q = {q: (np.quantile(absorb, q), *boot_quantile_ci(absorb, q)) for q in (0.5, 0.95, 0.99)}
    abs_lo, abs_hi = cp(int((absorb <= meta["phase_horizon"]).sum()), K)

    agg_final = pd.read_csv(OUT / "aggregate_final_state.tsv", sep="\t")
    delta = pd.read_csv(OUT / "withdrawal_vs_control_delta.tsv", sep="\t")
    tc = pd.read_csv(OUT / "aggregate_timecourse.tsv", sep="\t")

    # ---- figures -----------------------------------------------------------------------
    # Fig 1: aggregate P(ON) heatmap, all dynamic nodes, ordered by tier then median.
    w = tc[tc.arm == "withdrawal"]
    order_nodes = sw_tab.node.tolist()
    mat = w.pivot(index="node", columns="time", values="mean").loc[order_nodes]
    tmax = 12.0
    mat = mat.loc[:, mat.columns <= tmax]
    fig, ax = plt.subplots(figsize=(9, 8.5))
    im = ax.imshow(mat.to_numpy(), aspect="auto", cmap="Blues", vmin=0, vmax=1, interpolation="nearest",
                   extent=[0, tmax, len(order_nodes), 0])
    ax.set_yticks(np.arange(len(order_nodes)) + 0.5)
    ax.set_yticklabels([f"D{tier[n]}  {n}" + ("  (ON)" if sw_tab.set_index('node').loc[n, 'direction'] == 'OFF->ON' else "")
                        for n in order_nodes], fontsize=7)
    ax.set_xlabel("MaBoSS relative time after progesterone removal (not hours)")
    ax.set_title("P(node ON) after progesterone withdrawal\nrows ordered by median switch time · D = shortest regulatory path from IN_PROGESTIN",
                 fontsize=9, loc="left", color=INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("P(ON), mean of 10 replicates × 5,000 trajectories")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_cascade_heatmap.png", dpi=170)
    plt.close(fig)

    # Fig 2: milestone curves, withdrawal vs control, with across-replicate 95% CI band.
    panels = [("Receptor loss", ["E_PGR", "S_PGR"]),
              ("Programs", ["E_SECRETORY_STATE", "S_DECIDUALIZED", "S_HAND2"]),
              ("Readout phenotypes", ["OUT_EPITHELIAL_RECEPTIVE", "OUT_STROMAL_DECIDUALIZED", "OUT_MATERNAL_ADHESION_COMPETENCE"]),
              ("Anti-receptive gains", ["E_MUC1_BARRIER", "E_PODXL", "E_ESTROGENIC_PROLIFERATION"])]
    colors = [BLUE, ORANGE, AQUA]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6), sharey=True)
    for pi, (ax, (title, nds)) in enumerate(zip(axes, panels)):
        for c, n in zip(colors, nds):
            d = w[(w.node == n) & (w.time <= tmax)]
            ax.fill_between(d.time, d.ci_low, d.ci_high, color=c, alpha=0.25, linewidth=0)
            ax.plot(d.time, d["mean"], color=c, lw=2, label=n.replace("MATERNAL_ADHESION_", "ADHESION_"))
            ctl = tc[(tc.arm == "control") & (tc.node == n) & (tc.time <= tmax)]
            ax.plot(ctl.time, ctl["mean"], color=c, lw=1, ls=(0, (3, 2)), alpha=0.8)
        ax.set_title(title, loc="left", fontsize=9, color=INK)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_xlabel("relative time (not hours)")
        ax.legend(fontsize=6.5, frameon=False, loc="center right", bbox_to_anchor=(1.0, 0.3 if pi == 3 else 0.5))
    axes[0].set_ylabel("P(ON)")
    fig.suptitle("Solid: progesterone removed (band = 95% CI across 10 replicates)   ·   dashed: cocktail kept (matched control)",
                 fontsize=8.5, color=INK2, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "fig2_milestone_timecourses.png", dpi=170)
    plt.close(fig)

    # Fig 3: switch-time intervals, labelled with the model's own node_dictionary labels.
    nd = pd.read_csv(ROOT / "models/superset" / meta["model_version"] / "node_dictionary.tsv", sep="\t")
    label = dict(zip(nd.node_id, nd.label))
    # Marker genes the repo reads each node through (support features of the
    # committed observation map, current HGNC symbol where renamed). A readout
    # node whose logic is exactly one other node inherits that node's markers.
    cm = pd.read_csv(ROOT / "docs/u6_semantics/component_map.tsv", sep="\t", dtype=str).fillna("")
    cm = cm[cm.role == "support_feature"]
    genes: dict[str, list[str]] = {}
    for _, r in cm.iterrows():
        sym = r.current_hgnc_symbol or r.symbol_as_committed
        genes.setdefault(r.model_node, [])
        if sym not in genes[r.model_node]:
            genes[r.model_node].append(sym)
    # Nodes the repo marks not RNA-assessable (node_semantics.tsv) have no marker
    # genes: they are combinations of other nodes. Show what their v0.5.1 rule
    # combines instead ("= ..."), never as a gene list.
    composition = {
        "OUT_STROMAL_DECIDUALIZED": "= decidual state [PRL, IGFBP1, FOXO1, WNT4, LEFTY2]",
        "OUT_EPITHELIAL_RECEPTIVE": "= receptive surface + PAEP",
        "OUT_MATERNAL_ADHESION_COMPETENCE": "= receptive epithelium + decidual state + permissive ECM\n+ SPP1 or redundant route, no anti-adhesive route",
        "E_RECEPTIVE_SURFACE": "= STAT3 signal, no PODXL/DAG1/MUC1 barrier, no proliferation,\n+ at least one adhesion support (integrin, SPP1, HB-EGF, ...)",
        "X_ADHESION_ROUTE_SPP1": "= receptive surface + free SPP1 + integrin",
        "X_ADHESION_ROUTE_REDUNDANT": "= receptive surface + CD98/CD9, HB-EGF, ANXA2,\ncleaved DAG1 or sLeX-MUC1",
        "X_ANTIADHESIVE_ROUTE": "= PODXL, full-length DAG1 or barrier MUC1",
        "X_MECHANICAL_PERMISSIVE_ECM": "= decidual state + TAZ ECM remodeling, no stiffness/ER stress",
        "X_SPP1_LUMEN_FREE": "= epithelial or stromal SPP1, not neutralized",
    }

    def friendly(n):
        base = label.get(n, n)
        if n in composition:
            return f"{base}\n{composition[n]}"
        g = genes.get(n, [])
        if not g or (len(g) == 1 and g[0] in base.replace("-", "")):
            return base
        shown = ", ".join(g[:5]) + (f", +{len(g) - 5}" if len(g) > 5 else "")
        full = f"{base} [{shown}]"
        return full if len(full) <= 42 else f"{base}\n[{shown}]"
    inputs = {k: bool(v) for k, v in meta["arm_inputs"]["withdrawal"].items()}
    dl = trigger_delays(ev, ROOT / "models/superset" / meta["model_version"] / "network.bnd", inputs)
    dl.to_csv(OUT / "switch_delays_after_trigger.tsv", sep="\t", index=False)
    def interval_figure(stats_tab, xlabel, subtitle, path, xlim=None):
        s = stats_tab.iloc[::-1].reset_index(drop=True)
        fig, ax = plt.subplots(figsize=(10.5, 15))
        for i, r in s.iterrows():
            c = BLUE if r.direction == "ON->OFF" else ORANGE
            ax.plot([r["p2.5"], r["p97.5"]], [i, i], color=c, lw=1, alpha=0.6)
            ax.plot([r.p25, r.p75], [i, i], color=c, lw=4, solid_capstyle="round")
            ax.plot(r["median"], i, "o", color=SURF, ms=5, mec=c, mew=1.5)
        ax.set_yticks(range(len(s)))
        ax.set_yticklabels([friendly(n) for n in s.node], fontsize=7.5)
        for tick, n in zip(ax.get_yticklabels(), s.node):
            if n.startswith("OUT_"):
                tick.set_fontweight("bold")
                tick.set_color(INK)
        ax.set_ylim(-0.7, len(s) - 0.3)
        if xlim:
            ax.set_xlim(*xlim)
        ax.set_xlabel(xlabel)
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.plot([], [], color=BLUE, lw=4, label="turns off")
        ax.plot([], [], color=ORANGE, lw=4, label="turns on")
        ax.legend(frameon=False, loc="upper right", fontsize=9)
        fig.subplots_adjust(left=0.42, right=0.98, top=0.925, bottom=0.04)
        fig.text(0.01, 0.99, "When each part of the network switches after progesterone is removed",
                 fontsize=10.5, color=INK, va="top")
        fig.text(0.01, 0.975, f"{K} simulated trajectories · dot = median · thick bar = middle 50% · thin line = middle 95% · bold = phenotype readouts\n"
                 + subtitle + "\n[ ] = marker genes the repo reads the node through (not its molecular definition)\n"
                 "= ... = node defined by its rule as a combination of other nodes; the repo marks these not RNA-measurable",
                 fontsize=8.5, color=INK2, va="top")
        fig.savefig(path, dpi=170)
        plt.close(fig)

    interval_figure(sw_tab, "time after progesterone removal (MaBoSS relative time, not hours)",
                    "x = absolute simulated time; bars mix fast and slow trajectories",
                    OUT / "fig3_switch_time_intervals.png")

    # Per-trajectory normalisation: position of each switch in its own
    # trajectory's cascade, 0 = first switch, 1 = last. Order within every
    # trajectory is preserved exactly; between-trajectory speed differences are
    # removed. Absolute durations are dropped, and with uniform rates they carry
    # no information anyway.
    cols = sw_tab.node.tolist()
    rk = wide[cols].rank(axis=1, method="first")
    npos = rk.sub(1).div(wide[cols].notna().sum(axis=1) - 1, axis=0)
    norm_rows = []
    for n in cols:
        x = npos[n].dropna().to_numpy()
        norm_rows.append({"node": n, "direction": sw_tab.set_index("node").loc[n, "direction"],
                          "median": np.median(x), "p2.5": np.quantile(x, .025), "p25": np.quantile(x, .25),
                          "p75": np.quantile(x, .75), "p97.5": np.quantile(x, .975)})
    norm_tab = pd.DataFrame(norm_rows).sort_values("median").reset_index(drop=True)
    norm_tab.to_csv(OUT / "switch_positions_normalized.tsv", sep="\t", index=False)
    interval_figure(norm_tab, "position in the trajectory's own cascade (0 = first switch, 1 = last switch)",
                    "x = per-trajectory normalised position: every trajectory rescaled to the same cascade length",
                    OUT / "fig3b_switch_positions_normalized.png", xlim=(-0.03, 1.03))

    # Fig 4: milestone precedence matrix.
    mp = prec[prec["first"].isin(ms) & prec["second"].isin(ms)].pivot(index="first", columns="second",
                                                                        values="p_first_before").reindex(index=ms, columns=ms)
    fig, ax = plt.subplots(figsize=(7.5, 6.2))
    im = ax.imshow(mp.to_numpy(dtype=float), cmap="RdBu_r", vmin=0, vmax=1)
    for i in range(len(ms)):
        for j in range(len(ms)):
            v = mp.iloc[i, j]
            if pd.notna(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                        color="white" if abs(v - 0.5) > 0.35 else INK)
    ax.set_xticks(range(len(ms)))
    ax.set_xticklabels([MILESTONES[n] for n in ms], rotation=40, ha="right", fontsize=7)
    ax.set_yticks(range(len(ms)))
    ax.set_yticklabels([MILESTONES[n] for n in ms], fontsize=7)
    ax.set_title("P(row event happens before column event), per trajectory", loc="left", fontsize=9, color=INK)
    fig.colorbar(im, ax=ax, fraction=0.04)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_milestone_precedence.png", dpi=170)
    plt.close(fig)

    summary = {
        "K": K, "order_counts_top": order_counts.most_common(8), "n_distinct_milestone_orders": len(order_counts),
        "phenotype_classes": classes.to_dict(), "phenotype_class_nodes": pheno_nodes,
        "absorption_quantiles": {str(k): v for k, v in absorb_q.items()},
        "absorbed_by_horizon_cp": [abs_lo, abs_hi], "absorption_max": float(absorb.max()),
        "n_obligate_pairs": len(obligate), "n_unordered_pairs": m,
        "n_pairs_holm_sig": int((und.p_holm < 0.05).sum()),
    }
    (OUT / "analysis_summary.json").write_text(json.dumps(summary, indent=2, default=float) + "\n")
    pd.set_option("display.width", 250)
    print(sw_tab.round(3).to_string())
    print(ms_pairs.round(4).to_string())
    print(pheno.to_string())
    print(json.dumps(summary, indent=2, default=float))
    print(delta.round(4).to_string())
    print(agg_final[agg_final.arm != "mifepristone"].round(4).to_string())


if __name__ == "__main__":
    main()
