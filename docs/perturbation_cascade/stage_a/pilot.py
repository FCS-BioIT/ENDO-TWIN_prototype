import pickle
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cascade_proto as cp  # noqa: E402

OUT = str(Path(__file__).resolve().parents[3] / "output" / "perturbations" / "stage_a_pilot.pkl")
START = "hormone_treated_maternal"
N = 1000
t0 = time.time()
prot = cp.get_protocol(START, model_version=cp.MV)
cfg = cp.ROOT / prot.condition_cfg
base_inputs = dict(prot.steps[0].input_states)
wd_inputs = {**base_inputs, "IN_PROGESTIN": False}
results = {"meta": {"base_inputs": base_inputs, "wd_inputs": wd_inputs}}


def seeds_for(entropy, n):
    s = np.random.SeedSequence(entropy).generate_state(n, dtype=np.uint32) % (2**31 - 2) + 1
    assert len(set(s.tolist())) == n
    return s


def arms(tag, term, policy, cutoff, horizon=25.0, tick=0.01, n=N, entropy=1, with_mife=False):
    cont = cp.perturbation_continuation(term, START, policy, cutoff, base_inputs)
    rng = np.random.default_rng(np.random.SeedSequence([entropy, 7]))
    states = cp.sample_states(cont, n, rng)
    seeds = seeds_for(entropy, n)
    out = {"cont": cont, "states": states, "seeds": seeds}
    plan = [("control", base_inputs, ()), ("withdrawal", wd_inputs, ())]
    if with_mife:
        plan.append(("mifepristone", base_inputs, ("mifepristone",)))
    for arm, inputs, iv in plan:
        cw = cp.replace(cont, forced_nodes=inputs)
        runs = cp.run_arm(cw, states, seeds, inputs, cfg, horizon, tick, iv)
        ev = cp.extract(runs, cont, states, tick)
        logic = cp.logic_table(runs[0][3])
        ev["at_risk_at_horizon"] = cp.at_risk(ev, logic, inputs)
        out[arm] = ev
        out[arm + "_sha"] = sorted({r[2] for r in runs})
        out[arm + "_overrides"] = runs[0][3]
        print(f"{tag} {arm} done {time.time() - t0:.0f}s", flush=True)
    results[tag] = out


lin, term25 = cp.lineage_terminal(START, seed=1, n=5000, horizon=25.0)
results["meta"]["lineage"] = lin
arms("B_all_h25", term25.final_result, "all_non_inputs", 0.0, with_mife=True)
arms("A_canon_h25", term25.final_result, "extended_maternal_joint", 1e-6, with_mife=True)
_, term50 = cp.lineage_terminal(START, seed=1, n=5000, horizon=50.0)
arms("B_all_h50", term50.final_result, "all_non_inputs", 0.0)
_, term4 = cp.lineage_terminal(START, seed=1, n=5000, horizon=None)
arms("B_all_declared", term4.final_result, "all_non_inputs", 0.0)
arms("B_all_h25_block2", term25.final_result, "all_non_inputs", 0.0, entropy=2)
# Same seeds and states, different tick / horizon (first 200).
for tag, hz, tk in (("B_tick005", 25.0, 0.05), ("B_tick0001", 25.0, 0.001), ("B_h40", 40.0, 0.01)):
    arms(tag, term25.final_result, "all_non_inputs", 0.0, horizon=hz, tick=tk, n=200)
for tag in list(results):
    if tag != "meta":
        results[tag]["cont"] = {"node_ids": results[tag]["cont"].node_ids,
                                "distribution": results[tag]["cont"].distribution}
pickle.dump(results, open(OUT, "wb"))
print("total", time.time() - t0)
