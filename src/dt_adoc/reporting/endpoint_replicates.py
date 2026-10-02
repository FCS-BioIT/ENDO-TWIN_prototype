"""Independent complete-run replicates of the functional adhesion endpoint.

This module produces the simulated side of the functional-endpoint figure. It
exists because the only committed across-run spread of the adhesion endpoint --
``simulated_sd_across_seeds`` in ``docs/concordance/`` -- turned out not to be
a spread across complete runs at all, and a figure with error bars built
on it would plot a number that measures almost nothing.

What was measured (2026-09-23, installed ``cmaboss``; ``seed_structure_probe``
below, recorded in every run-settings file, re-run by an integration test):

1. **A run with seed ``s`` and ``N`` trajectories is the union of ``N``
   single-trajectory runs with seeds ``s, ..., s+N-1``** -- equal on the full
   time-resolved node table and the full joint state distribution of a dynamic
   protocol. So the committed seeds 1-5 at ``N = 20000`` share 19,996 of their
   20,000 per-trajectory seeds, and their spread reflects swapping at most four
   trajectories -- not complete-run variability.
2. **The per-trajectory initial-state draw over consecutive seeds is
   stratified, not i.i.d.**: across disjoint blocks a Bernoulli(0.70) relay's
   occupancy spread is far below the binomial reference (values recorded).

What is therefore done here, and why it is the defensible estimator:

* Each replicate is a **complete lineage** (every protocol phase, with the
  projected continuation between phases) run under one seed.
* Replicate ``r`` uses seed ``1 + r * trajectory_count``, so the per-trajectory
  seed ranges ``[seed, seed + N)`` of different replicates are **disjoint**:
  replicates share no per-trajectory seed. This is the complete-run variability
  across seeds that ``docs/maboss_estimator_semantics.md`` §3c prefers, with the
  overlap defect removed. Disjoint seeds are not a proof that the streams are
  statistically independent, and nothing here relies on that.
* The reported spread is the sample SD across replicates. It is the run-to-run
  reproducibility of *this* estimator on disjoint seed blocks. It is **not**
  an i.i.d. Monte Carlo standard error (the stratified draw makes it smaller),
  not a trajectory-level pseudo-replicate, not MaBoSS's node error column
  (§3b of that document: a sum of state SEs, not the marginal's SE), and not a
  binomial/Wilson interval (§3d: wrong variance family for a dwell-time
  occupancy). It carries no biological or experimental uncertainty at all.

At the converged horizon this network is a DAG over its free variables, so the
endpoint's exact expectation under the ``baseline.cfg`` priors is computable by
enumeration; ``exact_converged_endpoint`` does that, and the replicates are
checked against it rather than trusted.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dt_adoc.model.provenance import repo_root

MODEL_VERSION = "adoc-literature-superset-v0.5.0"
#: The executable parent v0.5.0 was copied from. Recorded so the provenance can
#: state, from hashes, whether the simulated network differs from it.
PARENT_MODEL_VERSION = "adoc-literature-superset-v0.4.0"

#: The three adhesion arms the manuscript compares, in display order. Protocol
#: ids are the ones ``dt_adoc.concordance.build.ARMS`` uses, so the two
#: artifacts simulate the same thing.
ENDPOINT_ARMS: tuple[tuple[str, str, str], ...] = (
    ("untreated", "adhesion_challenge_basal", "Untreated"),
    ("hormone_treated", "adhesion_challenge_hormone_treated", "Hormone-treated"),
    (
        "mifepristone",
        "adhesion_challenge_hormone_treated_mifepristone",
        "Hormone-treated + mifepristone",
    ),
)

ENDPOINT_NODE = "OUT_STABLE_ADHESION"
#: Recorded beside the endpoint because at convergence the endpoint is their
#: disjunction (``identifiability.adhesion_endpoint_decomposition``): a reader
#: can see that the replicate spread of the endpoint is the spread of two
#: hand-set initial-state draws.
CARRIER_NODES = ("X_INTERFACE_SPP1_RELAY", "X_INTERFACE_REDUNDANT_RELAY")
RECORDED_NODES = (ENDPOINT_NODE, "OUT_MATERNAL_ADHESION_COMPETENCE", *CARRIER_NODES)

HORIZON_CLASSES = ("converged", "declared")
DEFAULT_TRAJECTORIES = 20_000

#: Fifty replicates. The choice is computational, not conventional: for a
#: roughly normal spread the relative standard error of a sample SD is about
#: ``1 / sqrt(2 (R - 1))``, i.e. ~35% at R = 5, ~24% at 10, ~16% at 20 and ~10%
#: at 50. Five seeds can show gross stability; they cannot estimate a spread.
#: At ~2 CPU-minutes per replicate (three arms, both horizons) fifty replicates
#: are ~100 CPU-minutes. Run with few workers: each can reach 11-14 GB resident
#: at the declared horizon (see ``build_endpoint_replicates``). Beyond ~50 the
#: precision gain per CPU-minute is small, and the spread is in any case
#: invisible at figure scale -- the figure prints it rather than relying on the
#: bar.
DEFAULT_REPLICATES = 50

OUTPUT_DIR = Path("docs/endpoint")
REPLICATES_TSV = OUTPUT_DIR / "endpoint_replicates.tsv"
RUN_SETTINGS_JSON = OUTPUT_DIR / "endpoint_run_settings.json"

GENERATOR_FILES = (
    "src/dt_adoc/reporting/endpoint_replicates.py",
    "src/dt_adoc/concordance/simulate.py",
    "src/dt_adoc/simulation/runner.py",
    "src/dt_adoc/protocols/conditions.py",
)

TSV_COLUMNS = (
    "arm_id",
    "protocol_id",
    "horizon_class",
    "phase_horizon",
    "replicate",
    "seed",
    "trajectory_seed_range",
    "trajectory_count",
    "node_id",
    "value",
)


def replicate_seed(replicate: int, trajectory_count: int) -> int:
    """Seed whose per-trajectory seed range is disjoint from every other replicate."""
    return 1 + replicate * trajectory_count


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class _Task:
    arm_id: str
    protocol_id: str
    horizon_class: str
    replicate: int
    seed: int
    trajectory_count: int
    model_version: str
    root: str


def _run_task(task: _Task) -> list[dict[str, Any]]:
    from dt_adoc.concordance.simulate import run_arm

    run = run_arm(
        task.arm_id,
        task.protocol_id,
        horizon_class=task.horizon_class,
        model_version=task.model_version,
        root=Path(task.root),
        trajectory_count=task.trajectory_count,
        seeds=(task.seed,),
    )
    return [
        {
            "arm_id": task.arm_id,
            "protocol_id": task.protocol_id,
            "horizon_class": task.horizon_class,
            "phase_horizon": ""
            if run.phase_horizon is None
            else repr(run.phase_horizon),
            "replicate": task.replicate,
            "seed": task.seed,
            "trajectory_seed_range": (
                f"{task.seed}..{task.seed + task.trajectory_count - 1}"
            ),
            "trajectory_count": task.trajectory_count,
            "node_id": node_id,
            "value": repr(float(run.node_by_seed[node_id][0])),
        }
        for node_id in RECORDED_NODES
    ]


#: A single-step protocol run from ``baseline.cfg`` at its DECLARED horizon, so
#: nodes are caught in transit: the union test below is then a test on dynamic
#: trajectories, not on saturated free variables that never transition.
PROBE_PROTOCOL = "hormone_treated_maternal"


def _probe_run(
    seed: int, count: int, model_version: str, root: Path
) -> tuple[Any, Any]:
    from dt_adoc.simulation.runner import run_protocol

    final = run_protocol(
        PROBE_PROTOCOL,
        model_version=model_version,
        root=root,
        seed=seed,
        sample_count=count,
    ).final_result
    return final.nodes_probtraj, final.last_states_probtraj.iloc[-1]


def _union_test(
    start: int,
    count: int,
    singles: list[tuple[Any, Any]],
    model_version: str,
    root: Path,
) -> dict[str, Any]:
    """Pooled run (seed ``start``, ``count`` trajectories) vs mean of single runs.

    Compares the FULL time-resolved per-node occupancy table (every recorded
    node at every tick) and the FULL joint state distribution at the last tick.
    Agreement to rounding on both, for a run with many transient cells, is what
    an identical trajectory multiset produces; a merely equal pair of means is
    not.
    """
    import pandas as pd

    pooled_nodes, pooled_states = _probe_run(start, count, model_version, root)
    chosen = singles[start - 1 : start - 1 + count]
    mean_nodes = sum(nodes for nodes, _ in chosen) / count
    mean_states = (
        pd.concat([states for _, states in chosen], axis=1).fillna(0.0).sum(axis=1)
        / count
    )
    index = mean_states.index.union(pooled_states.index)
    values = pooled_nodes.to_numpy()
    return {
        "seed": start,
        "trajectories": count,
        "single_run_seeds": f"{start}..{start + count - 1}",
        "node_table_shape": list(pooled_nodes.shape),
        "transient_node_tick_cells": int(((values > 1e-9) & (values < 1 - 1e-9)).sum()),
        "max_abs_diff_node_table": float((pooled_nodes - mean_nodes).abs().max().max()),
        "joint_states_at_last_tick": len(index),
        "max_abs_diff_joint_states": float(
            (
                pooled_states.reindex(index).fillna(0.0)
                - mean_states.reindex(index).fillna(0.0)
            )
            .abs()
            .max()
        ),
    }


def seed_structure_probe(
    *,
    model_version: str = MODEL_VERSION,
    root: Path | None = None,
    block: int = 40,
) -> dict[str, Any]:
    """Measure, on the installed binary, how MaBoSS seeds its trajectories.

    Three measurements, all recorded so the addendum in
    ``docs/maboss_estimator_semantics.md`` quotes numbers a reader can find:

    * **union** -- for seeds 1 and 2, a run of ``block`` trajectories against the
      mean of ``block`` single-trajectory runs with consecutive seeds, on the full
      node table and the full joint state distribution of a dynamic protocol;
    * **disjoint control** -- the same comparison between two runs whose seed
      ranges do not overlap, which must differ, so the union test can fail;
    * **relay draws** -- the per-seed Bernoulli(0.70) relay draws over seeds
      ``1..block`` and the relay occupancy of ten disjoint blocks at two sizes,
      beside the i.i.d. binomial SD those sizes would give, as a *reference* for
      how stratified the initial-state draw is. No scaling law is claimed.
    """
    from statistics import stdev

    from dt_adoc.concordance.simulate import CONVERGED_PHASE_HORIZON
    from dt_adoc.simulation.runner import run_protocol

    active_root = root or repo_root()
    singles = [
        _probe_run(seed, 1, model_version, active_root) for seed in range(1, block + 2)
    ]
    union = [
        _union_test(1, block, singles, model_version, active_root),
        _union_test(2, block, singles, model_version, active_root),
    ]
    control_a, _ = _probe_run(1, block, model_version, active_root)
    control_b, _ = _probe_run(1 + block, block, model_version, active_root)
    tolerance = 1e-12

    def relay(seed: int, count: int) -> float:
        return float(
            run_protocol(
                "basal_maternal",
                model_version=model_version,
                root=active_root,
                seed=seed,
                sample_count=count,
                phase_horizon=CONVERGED_PHASE_HORIZON,
            ).final_result.last[CARRIER_NODES[0]]
        )

    draws = "".join(str(round(relay(seed, 1))) for seed in range(1, block + 1))
    blocks = {}
    for size in (100, DEFAULT_TRAJECTORIES):
        values = [relay(1 + i * size, size) for i in range(10)]
        blocks[str(size)] = {
            "block_seeds": [1 + i * size for i in range(10)],
            "relay_occupancy": values,
            "observed_sd": stdev(values),
            "iid_binomial_sd_reference": (0.7 * 0.3 / size) ** 0.5,
        }
    return {
        "probe_protocol": PROBE_PROTOCOL,
        "horizon": "declared",
        "union_tests": union,
        "disjoint_control": {
            "seeds": [1, 1 + block],
            "trajectories": block,
            "max_abs_diff_node_table": float((control_a - control_b).abs().max().max()),
        },
        "run_equals_union_of_consecutive_single_seed_runs": all(
            u["max_abs_diff_node_table"] < tolerance
            and u["max_abs_diff_joint_states"] < tolerance
            and u["transient_node_tick_cells"] > 0
            for u in union
        ),
        "tolerance": tolerance,
        "relay_node": CARRIER_NODES[0],
        "relay_prior": 0.7,
        "relay_single_trajectory_draws_seeds_1_to_block": draws,
        "relay_disjoint_blocks": blocks,
    }


def exact_converged_endpoint(
    model_version: str = MODEL_VERSION, root: Path | None = None
) -> dict[str, dict[str, Any]]:
    """Exact fixed-point expectation of the endpoint per arm, by enumeration.

    At convergence each trajectory sits at the unique fixed point of its
    free-variable assignment, so the expected endpoint is the prior-weighted sum
    over the latent free variables. Probabilistic latents take their
    ``baseline.cfg`` Bernoulli prior; deterministic ones their cfg value. The arm
    inputs are the recorded-design overlay ``identifiability.load_design`` uses.
    This is a proof over the model, not an estimate; the replicate means are
    compared against it.
    """
    from dt_adoc.model.runtime import resolve_model
    from dt_adoc.model.topology import parse_bnd_rules
    from dt_adoc.reporting.identifiability import (
        _evaluate,
        _latent_seeds,
        _parse_cfg_inputs,
        load_design,
        parse_cfg_probabilities,
    )
    from dt_adoc.reporting.structure import _topological_order

    active_root = root or repo_root()
    spec = resolve_model(model_version, active_root)
    rules = parse_bnd_rules(spec.network_bnd)
    free = {n for n in rules if rules[n].strip() == n}
    order = _topological_order(rules, free)
    arms, _controlled, _held_off, latent = load_design(model_version, active_root)
    by_id = {arm.arm_id: arm for arm in arms}
    priors = parse_cfg_probabilities(spec.baseline_cfg)
    fixed = _parse_cfg_inputs(spec.baseline_cfg)
    seeds, states, mask = _latent_seeds(latent)

    weights = []
    for index in range(states):
        weight = 1.0
        for node_id in latent:
            bit = (seeds[node_id] >> index) & 1
            if node_id in priors:
                weight *= priors[node_id] if bit else 1.0 - priors[node_id]
            elif bit != int(fixed.get(node_id, False)):
                weight = 0.0
                break
        weights.append(weight)

    result: dict[str, dict[str, Any]] = {}
    for arm_id, protocol_id, _label in ENDPOINT_ARMS:
        column = _evaluate(rules, order, seeds, mask, by_id[protocol_id].inputs)[
            ENDPOINT_NODE
        ]
        value = sum(w for i, w in enumerate(weights) if (column >> i) & 1)
        result[arm_id] = {
            "protocol_id": protocol_id,
            "exact_converged_value": value,
            "latent_free_variables": list(latent),
            "latent_priors": {n: priors[n] for n in latent if n in priors},
        }
    return result


def _observed(root: Path) -> dict[str, dict[str, Any]]:
    """Embryo counts and evidence roles, read from ``config/calibration.yaml``."""
    document = yaml.safe_load(
        (root / "config" / "calibration.yaml").read_text(encoding="utf-8")
    )
    objective = document["adhesion_objective"]
    by_protocol = {row["protocol_id"]: row for row in objective["readouts"]}
    return {
        arm_id: {
            "protocol_id": protocol_id,
            "successes": int(by_protocol[protocol_id]["successes"]),
            "trials": int(by_protocol[protocol_id]["trials"]),
            "role": by_protocol[protocol_id]["role"],
            "objective_role": objective["role"],
            "magnitude_fitted": bool(objective["magnitude_fitted"]),
        }
        for arm_id, protocol_id, _label in ENDPOINT_ARMS
    }


def build_endpoint_replicates(
    *,
    root: Path | None = None,
    model_version: str = MODEL_VERSION,
    replicates: int = DEFAULT_REPLICATES,
    trajectory_count: int = DEFAULT_TRAJECTORIES,
    workers: int = 4,
) -> dict[str, Any]:
    """Run every replicate, write the tracked TSV and run settings, return settings."""
    from dt_adoc.concordance.simulate import (
        CONVERGED_PHASE_HORIZON,
        protocol_lineage,
        run_provenance,
    )
    from dt_adoc.model.runtime import resolve_model

    active_root = root or repo_root()
    tasks = [
        _Task(
            arm_id=arm_id,
            protocol_id=protocol_id,
            horizon_class=horizon,
            replicate=replicate,
            seed=replicate_seed(replicate, trajectory_count),
            trajectory_count=trajectory_count,
            model_version=model_version,
            root=str(active_root),
        )
        for horizon in HORIZON_CLASSES
        for arm_id, protocol_id, _label in ENDPOINT_ARMS
        for replicate in range(replicates)
    ]
    # One task per worker process: a declared-horizon lineage carries a large
    # projected continuation and a worker reached 11-14 GB resident. Reusing
    # workers let that accumulate, and 14 of them exhausted a 125 GB host and
    # OOM-killed unrelated processes. Recycle every worker after one task.
    with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as pool:
        rows = [row for batch in pool.map(_run_task, tasks) for row in batch]
    rows.sort(
        key=lambda r: (
            HORIZON_CLASSES.index(r["horizon_class"]),
            [a[0] for a in ENDPOINT_ARMS].index(r["arm_id"]),
            r["replicate"],
            RECORDED_NODES.index(r["node_id"]),
        )
    )
    destination = active_root / REPLICATES_TSV
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    spec = resolve_model(model_version, active_root)
    parent = resolve_model(PARENT_MODEL_VERSION, active_root)
    provenance = run_provenance(
        model_version=model_version,
        root=active_root,
        trajectory_count=trajectory_count,
        seeds=tuple(replicate_seed(r, trajectory_count) for r in range(replicates)),
    )
    executable_identity = {
        name: {
            model_version: _sha256(getattr(spec, attr)),
            PARENT_MODEL_VERSION: _sha256(getattr(parent, attr)),
        }
        for name, attr in (
            ("network_bnd", "network_bnd"),
            ("baseline_cfg", "baseline_cfg"),
        )
    }
    for path in sorted(Path(spec.condition_dir).glob("*.cfg")):
        executable_identity[f"conditions/{path.name}"] = {
            model_version: _sha256(path),
            PARENT_MODEL_VERSION: _sha256(Path(parent.condition_dir) / path.name)
            if (Path(parent.condition_dir) / path.name).is_file()
            else "absent",
        }
    settings = {
        "schema_version": "1.0",
        "artifact": "adoc_functional_endpoint_replicates",
        "claim_boundary": (
            "Simulated values are MaBoSS time-averaged node occupancies "
            "(docs/maboss_estimator_semantics.md), not clinical or experimental "
            "adhesion probabilities. The across-replicate SD is run-to-run "
            "reproducibility of the estimator on disjoint seed blocks: not "
            "an experimental, biological or model-structure uncertainty, and not "
            "an i.i.d. Monte Carlo SE."
        ),
        "model_version": model_version,
        "parent_model_version": PARENT_MODEL_VERSION,
        "executable_identity": executable_identity,
        "executable_identical_to_parent": all(
            v[model_version] == v[PARENT_MODEL_VERSION]
            for v in executable_identity.values()
        ),
        "replicates": replicates,
        "trajectory_count": trajectory_count,
        "seed_rule": "seed_r = 1 + r * trajectory_count; trajectory k of replicate r "
        "is seeded seed_r + k, so replicate seed ranges are disjoint",
        "seeds": [replicate_seed(r, trajectory_count) for r in range(replicates)],
        "converged_phase_horizon": CONVERGED_PHASE_HORIZON,
        "declared_horizon": "config/protocols.yaml relative_duration per phase "
        "(dimensionless MaBoSS time; ~4000x short of the endpoint fixed point, "
        "docs/endpoint_convergence_finding.md)",
        "lineages": {
            arm_id: list(
                protocol_lineage(
                    protocol_id, model_version=model_version, root=active_root
                )
            )
            for arm_id, protocol_id, _label in ENDPOINT_ARMS
        },
        "recorded_nodes": list(RECORDED_NODES),
        "observed": _observed(active_root),
        "exact_converged": exact_converged_endpoint(model_version, active_root),
        "seed_structure_probe": seed_structure_probe(
            model_version=model_version, root=active_root
        ),
        "replicates_tsv": str(REPLICATES_TSV),
        "replicates_tsv_sha256": _sha256(destination),
        "generator_files": {
            relative: _sha256(active_root / relative) for relative in GENERATOR_FILES
        },
        "python_version": platform.python_version(),
        "provenance": {
            "git_commit": provenance.git_commit,
            "git_tree_dirty": provenance.git_tree_dirty,
            "implementation_digest": provenance.implementation_digest,
            "maboss_python_version": provenance.maboss_python_version,
            "time_tick": provenance.time_tick,
            "protocols_yaml_sha256": provenance.protocols_yaml_sha256,
        },
    }
    (active_root / RUN_SETTINGS_JSON).write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return settings


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--trajectories", type=int, default=DEFAULT_TRAJECTORIES)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    settings = build_endpoint_replicates(
        replicates=args.replicates,
        trajectory_count=args.trajectories,
        workers=args.workers,
    )
    print(
        json.dumps(
            {
                "replicates": settings["replicates"],
                "executable_identical_to_parent": settings[
                    "executable_identical_to_parent"
                ],
                "seed_probe_union": settings["seed_structure_probe"][
                    "run_equals_union_of_consecutive_single_seed_runs"
                ],
                "exact_converged": {
                    k: v["exact_converged_value"]
                    for k, v in settings["exact_converged"].items()
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
