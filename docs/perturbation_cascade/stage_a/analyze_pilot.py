import pickle
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy import stats

P = str(Path(__file__).resolve().parent)
sys.path.insert(0, P)
import cascade_proto as cp  # noqa: E402

R = pickle.load(open(Path(__file__).resolve().parents[3] / "output" / "perturbations" / "stage_a_pilot.pkl", "rb"))
pd.set_option("display.width", 220)
pd.set_option("display.max_rows", 200)


def per_node(ev):
    g = ev.groupby("node")
    return pd.DataFrame({
        "p_init_on": g.initial.mean(),
        "p_switch": g.n_min.apply(lambda s: (s > 0).mean()),
        "p_multi": g.n_min.apply(lambda s: (s > 1).mean()),
        "p_transient": g.category.apply(lambda s: (s == "transient_return").mean()),
        "p_net_change": g.apply(lambda d: ((d.final.notna()) & (d.final != d.initial)).mean(), include_groups=False),
        "p_unresolved_first": g.first_resolved.apply(lambda s: (s == False).mean()),  # noqa: E712
        "p_at_risk_end": g.at_risk_at_horizon.apply(lambda s: np.mean([bool(v) for v in s if v is not None])),
        "med_first": g.first_time.median(),
    })


print("=== 0. lineage", R["meta"]["lineage"])
for tag in ("B_all_h25", "A_canon_h25"):
    c = R[tag]["cont"]
    print(tag, "memory nodes", len(c["node_ids"]), "states", len(c["distribution"]))

print("\n=== 1. control arm: switching without perturbation")
for tag in ("B_all_h25", "A_canon_h25", "B_all_h50", "B_all_declared"):
    pn = per_node(R[tag]["control"])
    sw = pn[pn.p_switch > 0]
    print(f"{tag}: nodes switching in control: {len(sw)}; max p_switch {pn.p_switch.max():.3f}; any at-risk at horizon {pn.p_at_risk_end.max():.3f}")
    if len(sw):
        print(sw[["p_init_on", "p_switch", "p_net_change", "p_multi"]].round(3).to_string())

print("\n=== 2. withdrawal vs mifepristone (policy B, h25, same states+seeds)")
for tag in ("B_all_h25", "A_canon_h25"):
    w, m = R[tag]["withdrawal"], R[tag]["mifepristone"]
    print(tag, "network sha distinct:", R[tag]["withdrawal_sha"] != R[tag]["mifepristone_sha"],
          "| overrides wd:", R[tag]["withdrawal_overrides"], "| mife:", R[tag]["mifepristone_overrides"])
    j = w.merge(m, on=["traj", "node"], suffixes=("_w", "_m"))
    same_t = np.isclose(j.first_time_w.fillna(-1), j.first_time_m.fillna(-1), atol=1e-12, rtol=0)
    print(f"  pathwise identical first_time: {same_t.mean():.4f}; identical n_min {np.mean(j.n_min_w == j.n_min_m):.4f}; identical final {np.mean(j.final_w.fillna(-1) == j.final_m.fillna(-1)):.4f}")
    pw, pm = per_node(w), per_node(m)
    print(f"  max |p_switch diff| {np.abs(pw.p_switch - pm.p_switch).max():.4f}; max |median diff| {np.nanmax(np.abs(pw.med_first - pm.med_first)):.2e}")

print("\n=== 3. policy A (canonical extended_maternal_joint) vs B (all non-inputs), withdrawal arm")
A, B = R["A_canon_h25"], R["B_all_h25"]
print("memory nodes in B but not A:", sorted(set(B["cont"]["node_ids"]) - set(A["cont"]["node_ids"])))
pa, pb = per_node(A["withdrawal"]), per_node(B["withdrawal"])
d = pd.DataFrame({"init_A": pa.p_init_on, "init_B": pb.p_init_on, "sw_A": pa.p_switch, "sw_B": pb.p_switch,
                  "med_A": pa.med_first, "med_B": pb.med_first})
print(d[(np.abs(d.init_A - d.init_B) > 0.01) | (np.abs(d.sw_A - d.sw_B) > 0.02) | (np.abs(d.med_A - d.med_B) > 0.15)].round(3).to_string())

print("\n=== 4. initialisation horizon: starting distributions and withdrawal medians")


def dist_tv(c1, c2):
    keys = set(c1["distribution"]) | set(c2["distribution"])
    assert c1["node_ids"] == c2["node_ids"]
    return 0.5 * sum(abs(c1["distribution"].get(k, 0) - c2["distribution"].get(k, 0)) for k in keys)


for tag in ("B_all_h50", "B_all_declared"):
    print(f"TV(start h25, {tag}) = {dist_tv(B['cont'], R[tag]['cont']):.4f}")
    p2 = per_node(R[tag]["withdrawal"])
    dd = (p2.med_first - pb.med_first).abs()
    print(f"   max |median first-time diff| vs h25: {dd.max():.3f} at {dd.idxmax()}; max |p_switch diff| {np.abs(p2.p_switch - pb.p_switch).max():.3f}")

print("\n=== 5. tick / horizon invariance on v0.6.0 (first 200 trajectories, same states and seeds)")
base = B["withdrawal"][B["withdrawal"].traj < 200]
for tag in ("B_tick005", "B_tick0001", "B_h40"):
    assert all(np.array_equal(a, b) for a, b in zip(R[tag]["states"], B["states"][:200]))
    o = R[tag]["withdrawal"].merge(base, on=["traj", "node"], suffixes=("", "_b"))
    both = o.first_time.notna() & o.first_time_b.notna()
    print(f"{tag}: max |first_time diff| {np.abs(o.first_time - o.first_time_b)[both].max():.2e}; "
          f"switch presence agree {np.mean(o.first_time.isna() == o.first_time_b.isna()):.4f}; "
          f"n_min agree {np.mean(o.n_min == o.n_min_b):.4f}; unresolved first {np.mean(o.first_resolved == False):.4f}")  # noqa: E712

print("\n=== 6. withdrawal arm event categories (policy B, h25)")
evB = B["withdrawal"]
print(evB.category.value_counts().to_string())
print("unresolved first windows:", int((evB.first_resolved == False).sum()))  # noqa: E712
pbn = pb.copy()
print(pbn[pbn.p_switch > 0].sort_values("med_first")[["p_init_on", "p_switch", "p_multi", "p_transient", "p_net_change", "p_at_risk_end", "med_first"]].round(3).to_string())
print("never switching nodes:", sorted(pbn.index[pbn.p_switch == 0]))

print("\n=== 7. position statistics: robustness")


def medians(ev, nodes=None):
    w, rank, nt = cp.positions(ev, nodes)
    return pd.DataFrame({"abs": w.median(), "rank": rank.median(), "ntime": nt.median()}), w, rank, nt


m1, w1, r1, n1 = medians(B["withdrawal"])
m2, *_ = medians(R["B_all_h25_block2"]["withdrawal"])
print("block1 vs block2 (independent states+seeds, n=1000 each):")
for c in m1:
    print(f"  {c:6s} spearman {stats.spearmanr(m1[c], m2[c])[0]:.3f}  max|diff| {np.abs(m1[c] - m2[c]).max():.3f}  scale(IQR of medians) {m1[c].quantile(.75) - m1[c].quantile(.25):.3f}")
nodes = list(m1.index)
last = m1["abs"].idxmax()
first2 = list(m1["abs"].nsmallest(2).index)
outs = [n for n in nodes if n.startswith("OUT_")]
for label, keep in (("drop last node " + last, [n for n in nodes if n != last]),
                    ("drop OUT_*", [n for n in nodes if n not in outs]),
                    ("drop first two " + ",".join(first2), [n for n in nodes if n not in first2])):
    mk, *_ = medians(B["withdrawal"], keep)
    common = mk.index
    print(f"  {label}:")
    for c in ("rank", "ntime"):
        dd = (mk[c] - m1.loc[common, c]).abs()
        print(f"     {c:6s} max|shift| {dd.max():.3f}  median|shift| {dd.median():.3f}  spearman {stats.spearmanr(mk[c], m1.loc[common, c])[0]:.3f}")

# relay strata
st = pd.DataFrame(B["states"], columns=B["cont"]["node_ids"])
for relay in [n for n in st.columns if n.endswith("_RELAY")]:
    on = st[relay].to_numpy() == 1
    if on.all() or (~on).all():
        continue
    for c, tab in (("abs", w1), ("rank", r1), ("ntime", n1)):
        diff = (tab[on].median() - tab[~on].median()).abs()
        diff = diff.drop([n for n in diff.index if n.startswith("X_")], errors="ignore")
        print(f"  relay {relay} (P on {on.mean():.2f}) {c:6s}: max|median shift| among non-X nodes {diff.max():.3f} at {diff.idxmax()}")

# within-wave resolution: adjacent rows in median order
pr = cp.precedence(w1)
order = m1["ntime"].sort_values().index.tolist()
adj = [pr[(pr.a == a) & (pr.b == b)].p_a_first.iloc[0] for a, b in zip(order[:-1], order[1:])]
adj = np.array(adj)
print(f"  adjacent pairs in ntime-median order: {len(adj)}; P(a first) in [0.4,0.6]: {np.mean((adj > .4) & (adj < .6)):.2f}; >0.9: {np.mean(adj > .9):.2f}")
und = pr[pr.a < pr.b]
print(f"  all pairs: {len(und)}; unresolved [0.4,0.6]: {np.mean((und.p_a_first > .4) & (und.p_a_first < .6)):.2f}; strict (0 or 1): {np.mean((und.p_a_first == 0) | (und.p_a_first == 1)):.2f}")
pr2 = cp.precedence(cp.positions(R["B_all_h25_block2"]["withdrawal"])[0])
j = pr.merge(pr2, on=["a", "b"])
print(f"  pairwise precedence block1 vs block2: max|diff| {np.abs(j.p_a_first_x - j.p_a_first_y).max():.3f}, median {np.abs(j.p_a_first_x - j.p_a_first_y).median():.3f}")

print("\n=== 8. n adequacy: bootstrap 95% CI half-width of per-node median at n=1000")
rng = np.random.default_rng(0)
for c, tab in (("abs", w1), ("rank", r1), ("ntime", n1)):
    hw = []
    for n in tab.columns:
        x = tab[n].dropna().to_numpy()
        if len(x) < 20:
            continue
        b = np.median(x[rng.integers(0, len(x), (1000, len(x)))], axis=1)
        hw.append((np.percentile(b, 97.5) - np.percentile(b, 2.5)) / 2)
    hw = np.array(hw)
    q = []
    for n in tab.columns:
        x = tab[n].dropna().to_numpy()
        if len(x) < 50:
            continue
        b = np.quantile(x[rng.integers(0, len(x), (500, len(x)))], 0.975, axis=1)
        q.append((np.percentile(b, 97.5) - np.percentile(b, 2.5)) / 2)
    print(f"  {c:6s} median CI half-width: median {np.median(hw):.4f} max {hw.max():.4f} | q97.5 CI half-width median {np.median(q):.4f} max {np.max(q):.4f}")
counts = B["withdrawal"].groupby("node").n_min.apply(lambda s: (s > 0).sum())
print("  switching counts (n contributing) min over switching nodes:", counts[counts > 0].min(), counts[counts > 0].idxmin())
