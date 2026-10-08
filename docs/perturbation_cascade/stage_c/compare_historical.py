"""Stage C: decompose the differences between the historical figure and the new tool.

Lineage: ``run_stage_c.sh`` regenerates the four bundles below under the
gitignored ``output/perturbations/``; the bundle tables are byte-deterministic,
and this script refuses to run unless every table it reads matches
``bundle_manifest.json`` and the archived historical files match
``../historical_v051/ORIGINAL_SHA256SUMS.tsv``. From a fresh checkout,
``--regenerate`` runs ``run_stage_c.sh`` first (about 6 minutes) and then
verifies, so the comparison runs from the committed state alone.
``--write-manifest`` records the current bundles' hashes (only after
regenerating them).

Reads the archived historical events and the four bundles, and writes
``historical_comparison.tsv`` and ``historical_comparison_summary.json`` next to
this script, and the figure to ``output/perturbations/stage_c/``. Each comparison holds everything but one factor fixed:

- stochastic: v0.6.0 seed block A vs block B (same everything else);
- initialisation and seed scheme: historical v0.5.1 vs the tool on v0.5.1
  (same model, lineage, event definition and statistic; the tool draws i.i.d.
  starting states and spread seeds, the historical run used consecutive seeds);
- normalisation: rank vs normalised time on the same tool events;
- model version: the tool on v0.5.1 vs v0.6.0 (same tool, settings and seeds).
"""

from __future__ import annotations

import hashlib
import subprocess
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from dt_adoc.cascade.summary import positions  # noqa: E402

BUNDLES = ROOT / "output" / "perturbations"
RUNS = {
    "v060_A": "progestin_withdrawal__v060__n2000__seedA",
    "v060_B": "progestin_withdrawal__v060__n2000__seedB",
    "v051_tool": "progestin_withdrawal__v051__n2000__seedA",
    "mife_v060_A": "mifepristone_after_ht__v060__n2000__seedA",
}
STATS = ("normalized_rank", "normalized_time", "absolute_time")
MANIFEST = HERE / "bundle_manifest.json"
#: Written to the gitignored output tree, not committed; its hash is recorded in
#: the summary JSON so a regeneration can be checked against it.
FIGURE = BUNDLES / "stage_c" / "historical_comparison.png"
HISTORICAL = ROOT / "docs/perturbation_cascade/historical_v051"
BUNDLE_TABLES = ("events.tsv", "node_summary.tsv", "control_comparison.tsv", "pairwise_precedence.tsv")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bundle_hashes() -> dict[str, dict[str, object]]:
    out = {}
    for key, run in RUNS.items():
        d = BUNDLES / run
        meta = json.loads((d / "metadata.json").read_text())
        out[run] = {
            "key": key,
            "spec": meta["perturbation"]["spec"],
            "n_trajectories_per_arm": meta["simulation"]["n_trajectories_per_arm"],
            "master_seed": meta["simulation"]["master_seed"],
            "tables": {name: _sha((d / name).read_bytes()) for name in BUNDLE_TABLES},
        }
    return out


def verify_inputs() -> None:
    """Refuse to compute from anything but the recorded parent artifacts."""
    sums = pd.read_csv(HISTORICAL / "ORIGINAL_SHA256SUMS.tsv", sep="\t").set_index("file").sha256
    for name in ("per_trajectory_events.tsv", "pairwise_precedence.tsv"):
        if _sha((HISTORICAL / name).read_bytes()) != sums[name]:
            raise SystemExit(f"archived {name} does not match ORIGINAL_SHA256SUMS.tsv")
    recorded = json.loads(MANIFEST.read_text())
    for run, entry in recorded.items():
        for name, digest in entry["tables"].items():
            path = BUNDLES / run / name
            if not path.is_file() or _sha(path.read_bytes()) != digest:
                raise SystemExit(
                    f"{path} is missing or differs from bundle_manifest.json; "
                    "regenerate with docs/perturbation_cascade/stage_c/run_stage_c.sh"
                )


def tool_events(run: str) -> pd.DataFrame:
    ev = pd.read_csv(BUNDLES / RUNS[run] / "events.tsv", sep="\t", low_memory=False)
    return ev[ev.arm == "perturbed"]


def historical_events() -> pd.DataFrame:
    h = pd.read_csv(HISTORICAL / "per_trajectory_events.tsv", sep="\t")
    return h.rename(columns={"traj": "trajectory", "switch_time": "first_switch_time"})


def medians(ev: pd.DataFrame) -> pd.DataFrame:
    pos = positions(ev)
    return pd.DataFrame({s: pos[s].median() for s in STATS})


def p_switch(ev: pd.DataFrame) -> pd.Series:
    return ev.groupby("node").first_switch_time.apply(lambda s: s.notna().mean())


def logic(version: str) -> dict[str, str]:
    text = (ROOT / "models/superset" / f"adoc-literature-superset-{version}" / "network.bnd").read_text()
    return {n: " ".join(e.split()) for n, e in re.findall(r"Node\s+(\w+)\s*\{\s*logic\s*=\s*([^;]+);", text)}


def delta(a: pd.DataFrame, b: pd.DataFrame, stat: str) -> dict[str, float]:
    common = a.index.intersection(b.index)
    common = common[np.isfinite(a.loc[common, stat].to_numpy()) & np.isfinite(b.loc[common, stat].to_numpy())]
    d = (a.loc[common, stat] - b.loc[common, stat]).abs()
    return {
        "n_nodes": len(common),
        "max_abs_delta": float(d.max()),
        "median_abs_delta": float(d.median()),
        "spearman": float(stats.spearmanr(a.loc[common, stat], b.loc[common, stat])[0]),
    }


CLAIMS = (
    ("OUT_STROMAL_DECIDUALIZED", "OUT_EPITHELIAL_RECEPTIVE"),
    ("OUT_MATERNAL_ADHESION_COMPETENCE", "OUT_EPITHELIAL_RECEPTIVE"),
    ("OUT_MATERNAL_ADHESION_COMPETENCE", "OUT_STROMAL_DECIDUALIZED"),
    ("E_PGR", "S_PGR"),
    ("S_HAND2", "E_ESTROGENIC_PROLIFERATION"),
    ("S_HAND2", "S_FGF_MITOGENIC"),
)


def ordering_claims() -> list[dict[str, object]]:
    """P(A before B | both switch) for the historical report's claims, per source."""
    hist = pd.read_csv(ROOT / "docs/perturbation_cascade/historical_v051/pairwise_precedence.tsv", sep="\t")
    hist = hist.set_index(["first", "second"])
    tool = {
        k: pd.read_csv(BUNDLES / RUNS[k] / "pairwise_precedence.tsv", sep="\t").set_index(["node_a", "node_b"])
        for k in ("v051_tool", "v060_A", "v060_B")
    }
    out = []
    for a, b in CLAIMS:
        row: dict[str, object] = {"a": a, "b": b}
        if (a, b) in hist.index:
            h = hist.loc[(a, b)]
            row["historical"] = {"p": float(h.p_first_before), "n_both": int(h.n_both)}
        for k, t in tool.items():
            r = t.loc[(a, b)]
            resolved = int(r.n_a_first + r.n_b_first)
            ci = stats.binomtest(int(r.n_a_first), resolved).proportion_ci()
            row[k] = {
                "p": float(r.p_a_first),
                "n_both": int(r.n_both_switch),
                "n_identifiable": resolved,
                "n_order_unresolved": int(r.n_order_unresolved),
                "ci95": [ci.low, ci.high],
            }
        out.append(row)
    return out


def comparison_figure(table: pd.DataFrame) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = table.dropna(subset=["v060_A__normalized_time"]).sort_values("v060_A__normalized_time", ascending=False)
    y = np.arange(len(t))
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 0.24 * len(t) + 1.8), sharey=True)
    a.scatter(t["historical__normalized_rank"], y, s=22, facecolors="none", edgecolors="#52514e", label="historical run (v0.5.1)")
    a.scatter(t["v051_tool__normalized_rank"], y, s=10, color="#2a78d6", label="new tool, v0.5.1")
    a.set_title("initialisation and seed scheme\n(same model, same rank axis)", fontsize=9, loc="left")
    a.set_xlabel("median normalised rank position")
    b.scatter(t["v051_tool__normalized_time"], y, s=22, facecolors="none", edgecolors="#2a78d6", label="new tool, v0.5.1")
    b.scatter(t["v060_A__normalized_time"], y, s=10, color="#eb6834", label="new tool, v0.6.0 block A")
    b.scatter(t["v060_B__normalized_time"], y, s=10, marker="x", color="#eb6834", alpha=0.6, label="new tool, v0.6.0 block B")
    b.set_title("model version against stochastic spread\n(same tool, normalised-time axis)", fontsize=9, loc="left")
    b.set_xlabel("median normalised time position")
    a.set_yticks(y)
    a.set_yticklabels([n + ("  *" if c else "") for n, c in zip(t.node, t.rule_changed_v051_to_v060)], fontsize=6.5)
    for ax in (a, b):
        ax.grid(axis="x", color="#e4e3df", lw=0.6)
        ax.legend(frameon=False, fontsize=7, loc="upper right")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.text(0.01, 0.005, "Progestin input withdrawal, 2,000 trajectories per run; * = rule differs between v0.5.1 and v0.6.0. Medians of empirical positions, not confidence intervals.", fontsize=7, color="#52514e")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=150)
    plt.close(fig)


def bundles_match() -> bool:
    try:
        verify_inputs()
    except SystemExit:
        return False
    return True


def main() -> None:
    if "--regenerate" in sys.argv and not bundles_match():
        subprocess.run(["bash", str(HERE / "run_stage_c.sh")], check=True)
    if "--write-manifest" in sys.argv:
        MANIFEST.write_text(json.dumps(bundle_hashes(), indent=2, sort_keys=True) + "\n")
    verify_inputs()
    hist = historical_events()
    ev = {k: tool_events(k) for k in RUNS}
    med = {"historical": medians(hist), **{k: medians(v) for k, v in ev.items()}}
    ps = {"historical": p_switch(hist), **{k: p_switch(v) for k, v in ev.items()}}
    summary: dict[str, object] = {}
    summary["stochastic_v060_A_vs_B"] = {s: delta(med["v060_A"], med["v060_B"], s) for s in STATS}
    summary["initialisation_and_seeds_historical_vs_tool_v051"] = {
        s: delta(med["historical"], med["v051_tool"], s) for s in STATS
    }
    summary["normalisation_rank_vs_time_order_v060_A"] = {
        "spearman_of_medians": float(
            stats.spearmanr(med["v060_A"].normalized_rank, med["v060_A"].normalized_time, nan_policy="omit")[0]
        ),
        "max_row_displacement": int(
            (med["v060_A"].normalized_rank.rank() - med["v060_A"].normalized_time.rank()).abs().max()
        ),
    }
    summary["model_version_tool_v051_vs_v060_A"] = {s: delta(med["v051_tool"], med["v060_A"], s) for s in STATS}
    summary["model_version_note"] = (
        "the v0.5.1 and v0.6.0 runs share master seed and lineage seed, so they start from the same "
        "drawn states (equal switching fractions follow); their event streams differ because the "
        "networks differ. Version shifts are therefore partly paired and are read against the "
        "independent-block stochastic shift as a conservative reference"
    )
    summary["event_definition"] = {
        "historical_max_reversals": int(hist.reversals.max()),
        "tool_max_switch_count": {k: int(v.n_switches_min.max()) for k, v in ev.items()},
        "note": "first-switch definition and tick are the same in both; no node needs more than one switch (n_switches_min <= 1, a lower bound: an out-and-back pair hidden inside one tick window is not excluded, and is invisible to both alike), so the event definition contributes no detected difference for this perturbation",
    }
    summary["p_switch_max_abs_delta"] = {
        "historical_vs_v051_tool": float((ps["historical"] - ps["v051_tool"]).abs().max()),
        "v060_A_vs_B": float((ps["v060_A"] - ps["v060_B"]).abs().max()),
        "v051_tool_vs_v060_A": float((ps["v051_tool"] - ps["v060_A"]).abs().max()),
    }
    mife = ev["mife_v060_A"].set_index(["trajectory", "node"]).sort_index()
    wd = ev["v060_A"].set_index(["trajectory", "node"]).sort_index()
    same = np.isclose(mife.first_switch_time.fillna(-1), wd.first_switch_time.fillna(-1), rtol=0, atol=1e-12)
    summary["withdrawal_vs_mifepristone_v060"] = {
        "same_starting_states_and_seeds": bool((mife.seed == wd.seed).all() and (mife.initial == wd.initial).all()),
        "fraction_node_trajectory_cells_identical_first_switch": float(same.mean()),
        "max_abs_p_switch_delta": float((p_switch(ev["mife_v060_A"]) - ps["v060_A"]).abs().max()),
    }
    summary["ordering_claims"] = ordering_claims()
    pr = pd.read_csv(BUNDLES / RUNS["v060_A"] / "pairwise_precedence.tsv", sep="\t")
    und = pr[pr.node_a < pr.node_b]
    summary["order_identifiability_v060_A"] = {
        "comparisons_both_switch": int(und.n_both_switch.sum()),
        "comparisons_unresolved_same_window": int(und.n_order_unresolved.sum()),
        "max_unresolved_for_one_pair": int(und.n_order_unresolved.max()),
    }
    l51, l60 = logic("v0.5.1"), logic("v0.6.0")
    changed = sorted(n for n in set(l51) & set(l60) if l51[n] != l60[n])
    summary["rules_changed_v051_to_v060"] = {n: {"v0.5.1": l51[n], "v0.6.0": l60[n]} for n in changed}
    summary["nodes_only_in_v051"] = sorted(set(l51) - set(l60))
    summary["nodes_only_in_v060"] = sorted(set(l60) - set(l51))

    # Per node: medians under each source, and whether the model-version shift
    # exceeds the block-to-block shift of the same node.
    nodes = sorted(set().union(*(m.index for m in med.values())))
    rows = []
    for n in nodes:
        r = {"node": n, "rule_changed_v051_to_v060": n in changed}
        for k, m in med.items():
            for s in STATS:
                r[f"{k}__{s}"] = float(m[s].get(n, np.nan))
            r[f"{k}__p_switch"] = float(ps[k].get(n, np.nan))
        stoch = abs(r["v060_A__normalized_time"] - r["v060_B__normalized_time"])
        version = abs(r["v051_tool__normalized_time"] - r["v060_A__normalized_time"])
        r["version_shift_ntime"] = version
        r["stochastic_shift_ntime"] = stoch
        rows.append(r)
    table = pd.DataFrame(rows)
    comparison_figure(table)
    summary["figure_sha256"] = {"historical_comparison.png": _sha(FIGURE.read_bytes())}
    table.to_csv(HERE / "historical_comparison.tsv", sep="\t", index=False, float_format="%.6g")
    (HERE / "historical_comparison_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "rules_changed_v051_to_v060"}, indent=2))
    print("rules changed:", changed)
    print(table.sort_values("version_shift_ntime", ascending=False)
          [["node", "rule_changed_v051_to_v060", "v051_tool__normalized_time", "v060_A__normalized_time",
            "version_shift_ntime", "stochastic_shift_ntime", "v051_tool__p_switch", "v060_A__p_switch"]]
          .head(15).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
