"""U5b: paired transient comparison of v0.5.0 against v0.5.1.

Implements ``docs/u5b_readout_repair/transient_preregistration.md`` exactly; that
file was committed before v0.5.1 existed, and every constant below is read from
it rather than chosen here. If the two ever disagree, the pre-registration is
right and this module is the defect.

Design, in one paragraph. Four adhesion lineages are run phase by phase with the
projected continuation between phases, as the concordance and endpoint builds
run them, on both model versions. Replicate ``r`` uses the SAME seed in both
versions -- common random numbers, because a run with seed ``s`` and ``N``
trajectories is the union of single-trajectory runs on seeds ``s .. s+N-1``
(``docs/maboss_estimator_semantics.md``, addendum 2026-09-23) -- and seed blocks
are disjoint between replicate indices and between the two trajectory counts.
For every phase cell and every reported node the per-block paired difference of
the phase-averaged occupancy and of the final-tick occupancy is summarised by a
Bonferroni-adjusted across-block t-interval and classified against the declared
tolerance.

**Pairing is variance reduction and nothing more.** Where the two rules disagree
the total transition rate differs, and from there the two versions consume the
same stream differently, so the paired mean is an estimate with Monte Carlo
error. The interval is the run-to-run reproducibility of that estimator on
disjoint seed blocks; it is not an i.i.d. Monte Carlo SE (the initial-state
draw over consecutive seeds is stratified), and it carries no biological or
experimental uncertainty.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from dt_adoc.model.provenance import repo_root
from dt_adoc.reporting.u5b_increment import (
    MODEL_VERSION as REPAIRED_VERSION,
)
from dt_adoc.reporting.u5b_increment import (
    PARENT_VERSION,
    REPAIRED_NODE,
    structural_identity,
)

#: The four lineages of the pre-registration, section 2.
ARMS = (
    "adhesion_challenge_basal",
    "adhesion_challenge_hormone_treated",
    "adhesion_challenge_hormone_treated_mifepristone",
    "adhesion_challenge_washout",
)
#: Pre-registration section 5, expectation 1: the rules never disagree here.
EXACT_IDENTITY_CELLS = (
    "basal_maternal",
    "e2_primed_maternal",
    "adhesion_challenge_basal",
)
REPLICATES = 20
#: Verdicts are read at the larger count; the smaller is the stability check.
GOVERNING_TRAJECTORIES = 20_000
CHECK_TRAJECTORIES = 2_000
TRAJECTORY_COUNTS = (GOVERNING_TRAJECTORIES, CHECK_TRAJECTORIES)
TOLERANCE = 0.005
FAMILY_ALPHA = 0.05
ESTIMANDS = ("time_averaged", "final_tick")

OUTPUT_DIR = Path("docs/u5b_readout_repair")
COMPARISON_TSV = OUTPUT_DIR / "transient_comparison.tsv"
BLOCKS_TSV = OUTPUT_DIR / "transient_blocks.tsv"
TRACE_TSV = OUTPUT_DIR / "transient_trace.tsv"
SETTINGS_JSON = OUTPUT_DIR / "transient_run_settings.json"
PREREGISTRATION = OUTPUT_DIR / "transient_preregistration.md"

GENERATOR_FILES = (
    "src/dt_adoc/reporting/u5b_readout_transient.py",
    "src/dt_adoc/reporting/u5b_increment.py",
    "src/dt_adoc/concordance/simulate.py",
    "src/dt_adoc/simulation/runner.py",
    "src/dt_adoc/protocols/conditions.py",
)


def replicate_seed(replicate: int, trajectory_count: int) -> int:
    """Seed blocks disjoint between replicates AND between trajectory counts.

    The governing count occupies seeds ``1 .. REPLICATES * 20,000``; the check
    count starts after that whole range (pre-registration section 2).
    """
    if trajectory_count == GOVERNING_TRAJECTORIES:
        return 1 + replicate * trajectory_count
    if trajectory_count == CHECK_TRAJECTORIES:
        return 1 + REPLICATES * GOVERNING_TRAJECTORIES + replicate * trajectory_count
    raise ValueError(f"trajectory count {trajectory_count} is not pre-registered")


@dataclass(frozen=True)
class _Task:
    model_version: str
    trajectory_count: int
    replicate: int
    root: str


def _cells(root: Path, model_version: str) -> dict[tuple[str, ...], str]:
    """Lineage prefix -> the phase it ends in, deduplicated across the arms."""
    from dt_adoc.concordance.simulate import protocol_lineage

    cells: dict[tuple[str, ...], str] = {}
    for arm in ARMS:
        lineage = protocol_lineage(arm, model_version=model_version, root=root)
        for end in range(1, len(lineage) + 1):
            cells[tuple(lineage[:end])] = lineage[end - 1]
    phases = list(cells.values())
    if len(set(phases)) != len(phases):
        raise ValueError(
            "two lineage prefixes end in the same phase; cells are ambiguous"
        )
    return cells


def _run_task(task: _Task) -> dict[str, Any]:
    """One replicate of every cell on one model version: per-tick node marginals."""
    from dt_adoc.concordance.simulate import protocol_continuation
    from dt_adoc.simulation.runner import run_protocol

    root = Path(task.root)
    seed = replicate_seed(task.replicate, task.trajectory_count)
    cache: dict[tuple[str, ...], Any] = {}
    out: dict[str, dict[str, Any]] = {}
    for prefix, phase in sorted(
        _cells(root, task.model_version).items(), key=lambda kv: len(kv[0])
    ):
        continuation = None
        if len(prefix) > 1:
            continuation = protocol_continuation(
                phase, cache[prefix[:-1]], model_version=task.model_version, root=root
            )
        result = run_protocol(
            phase,
            model_version=task.model_version,
            root=root,
            continuation=continuation,
            seed=seed,
            sample_count=task.trajectory_count,
        )
        cache[prefix] = result
        table = result.final_result.nodes_probtraj
        out[phase] = {
            "times": [float(t) for t in table.index],
            "nodes": {str(c): [float(v) for v in table[c]] for c in table.columns},
        }
    return {
        "model_version": task.model_version,
        "trajectory_count": task.trajectory_count,
        "replicate": task.replicate,
        "seed": seed,
        "cells": out,
    }


def _t_quantile(alpha_per_interval: float, df: int) -> float:
    from scipy.stats import t

    return float(t.ppf(1 - alpha_per_interval / 2, df))


def _normal_quantile(alpha_per_interval: float) -> float:
    from scipy.stats import norm

    return float(norm.ppf(1 - alpha_per_interval / 2))


def classify(differences: list[float], quantile: float) -> dict[str, Any]:
    """Pre-registration section 5's verdict table, for one interval."""
    centre = mean(differences)
    spread = stdev(differences)
    se = spread / math.sqrt(len(differences))
    low, high = centre - quantile * se, centre + quantile * se
    if all(d == 0.0 for d in differences):
        verdict = "EXACTLY_IDENTICAL"
    elif -TOLERANCE <= low and high <= TOLERANCE:
        verdict = "WITHIN_TOLERANCE"
    elif high < -TOLERANCE or low > TOLERANCE:
        verdict = "BEYOND_TOLERANCE"
    else:
        verdict = "INDETERMINATE"
    return {
        "mean": centre,
        "sd": spread,
        "se": se,
        "low": low,
        "high": high,
        "verdict": verdict,
    }


def _estimands(repaired: list[float], parent: list[float]) -> dict[str, float]:
    diffs = [a - b for a, b in zip(repaired, parent, strict=True)]
    return {"time_averaged": mean(diffs), "final_tick": diffs[-1]}


def compare(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Pair the runs, classify every interval, and evaluate the expectations."""
    by_key = {
        (r["model_version"], r["trajectory_count"], r["replicate"]): r for r in results
    }
    cells = sorted(results[0]["cells"])
    nodes_by_cell = {cell: sorted(results[0]["cells"][cell]["nodes"]) for cell in cells}

    blocks: list[dict[str, Any]] = []
    per_interval: dict[tuple[int, str, str, str], list[float]] = {}
    exact_identity: dict[str, bool] = {}
    traces: dict[tuple[str, int], list[list[float]]] = {}
    for count in TRAJECTORY_COUNTS:
        for replicate in range(REPLICATES):
            repaired = by_key[(REPAIRED_VERSION, count, replicate)]
            parent = by_key[(PARENT_VERSION, count, replicate)]
            if repaired["seed"] != parent["seed"]:
                raise ValueError("the two arms of a pair must share a seed")
            for cell in cells:
                a, b = repaired["cells"][cell], parent["cells"][cell]
                if a["times"] != b["times"] or sorted(a["nodes"]) != sorted(b["nodes"]):
                    raise ValueError(f"{cell}: the two versions report different grids")
                if count == GOVERNING_TRAJECTORIES and cell in EXACT_IDENTITY_CELLS:
                    same = all(a["nodes"][n] == b["nodes"][n] for n in a["nodes"])
                    exact_identity[cell] = exact_identity.get(cell, True) and same
                for node in nodes_by_cell[cell]:
                    values = _estimands(a["nodes"][node], b["nodes"][node])
                    for estimand, value in values.items():
                        per_interval.setdefault(
                            (count, cell, node, estimand), []
                        ).append(value)
                    if node == REPAIRED_NODE:
                        blocks.append(
                            {
                                "trajectory_count": count,
                                "replicate": replicate,
                                "seed": repaired["seed"],
                                "trajectory_seed_range": (
                                    f"{repaired['seed']}..{repaired['seed'] + count - 1}"
                                ),
                                "cell": cell,
                                "node_id": node,
                                "parent_time_averaged": mean(b["nodes"][node]),
                                "repaired_time_averaged": mean(a["nodes"][node]),
                                "paired_time_averaged": values["time_averaged"],
                                "parent_final_tick": b["nodes"][node][-1],
                                "repaired_final_tick": a["nodes"][node][-1],
                                "paired_final_tick": values["final_tick"],
                            }
                        )
                        if count == GOVERNING_TRAJECTORIES:
                            traces.setdefault((cell, count), []).append(
                                [
                                    x - y
                                    for x, y in zip(
                                        a["nodes"][node], b["nodes"][node], strict=True
                                    )
                                ]
                            )

    primary_n = len(cells) * len(ESTIMANDS)
    blast_n = sum(len(nodes_by_cell[c]) - 1 for c in cells) * len(ESTIMANDS)
    alpha = {
        "primary": FAMILY_ALPHA / primary_n,
        "blast_radius": FAMILY_ALPHA / blast_n,
    }
    t_q = {family: _t_quantile(a, REPLICATES - 1) for family, a in alpha.items()}
    z_q = {family: _normal_quantile(a) for family, a in alpha.items()}

    rows: list[dict[str, Any]] = []
    classified: dict[tuple[int, str, str, str], dict[str, Any]] = {}
    for (count, cell, node, estimand), diffs in sorted(per_interval.items()):
        family = "primary" if node == REPAIRED_NODE else "blast_radius"
        summary = classify(diffs, t_q[family])
        classified[(count, cell, node, estimand)] = summary
        rows.append(
            {
                "trajectory_count": count,
                "cell": cell,
                "node_id": node,
                "estimand": estimand,
                "family": family,
                "replicates": len(diffs),
                "t_quantile": t_q[family],
                **summary,
            }
        )

    stability: list[dict[str, Any]] = []
    for cell in cells:
        for estimand in ESTIMANDS:
            big = classified[(GOVERNING_TRAJECTORIES, cell, REPAIRED_NODE, estimand)]
            small = classified[(CHECK_TRAJECTORIES, cell, REPAIRED_NODE, estimand)]
            bound = z_q["primary"] * math.sqrt(big["se"] ** 2 + small["se"] ** 2)
            agree = abs(big["mean"] - small["mean"]) <= bound
            stability.append(
                {
                    "cell": cell,
                    "estimand": estimand,
                    "mean_governing": big["mean"],
                    "mean_check": small["mean"],
                    "absolute_gap": abs(big["mean"] - small["mean"]),
                    "bound": bound,
                    "se_ratio_check_over_governing": (
                        small["se"] / big["se"] if big["se"] > 0 else None
                    ),
                    "verdict_governing": big["verdict"],
                    "verdict_check": small["verdict"],
                    "stable": bool(agree and big["verdict"] == small["verdict"]),
                    "reported_verdict": (
                        big["verdict"]
                        if agree and big["verdict"] == small["verdict"]
                        else "UNSTABLE"
                    ),
                }
            )

    governing_blast = [
        r
        for r in rows
        if r["family"] == "blast_radius"
        and r["trajectory_count"] == GOVERNING_TRAJECTORIES
    ]
    expectations = {
        "1_exact_identity_where_rules_never_disagree": {
            "cells": list(EXACT_IDENTITY_CELLS),
            "held": all(exact_identity.get(c, False) for c in EXACT_IDENTITY_CELLS),
            "per_cell": {c: exact_identity.get(c, False) for c in EXACT_IDENTITY_CELLS},
        },
        "2_blast_radius_within_tolerance": {
            "intervals": len(governing_blast),
            "held": all(
                r["verdict"] in {"EXACTLY_IDENTICAL", "WITHIN_TOLERANCE"}
                for r in governing_blast
            ),
            "verdict_counts": _counts(r["verdict"] for r in governing_blast),
            "max_abs_mean": max(abs(r["mean"]) for r in governing_blast),
            "max_abs_interval_end": max(
                max(abs(r["low"]), abs(r["high"])) for r in governing_blast
            ),
        },
    }

    trace_rows: list[dict[str, Any]] = []
    pointwise_q = _t_quantile(FAMILY_ALPHA, REPLICATES - 1)
    for (cell, _count), per_block in sorted(traces.items()):
        times = results[0]["cells"][cell]["times"]
        for index, time in enumerate(times):
            column = [block[index] for block in per_block]
            centre = mean(column)
            se = stdev(column) / math.sqrt(len(column))
            trace_rows.append(
                {
                    "cell": cell,
                    "time": time,
                    "mean_paired_difference": centre,
                    "pointwise_low": centre - pointwise_q * se,
                    "pointwise_high": centre + pointwise_q * se,
                }
            )

    return {
        "rows": rows,
        "blocks": blocks,
        "trace": trace_rows,
        "stability": stability,
        "expectations": expectations,
        "families": {
            "primary_intervals": primary_n,
            "blast_radius_intervals": blast_n,
            "alpha_per_interval": alpha,
            "t_quantile": t_q,
            "normal_quantile_for_stability": z_q["primary"],
            "pointwise_trace_t_quantile": pointwise_q,
        },
        "cells": cells,
    }


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {k: (repr(v) if isinstance(v, float) else v) for k, v in row.items()}
            )


def _provenance(root: Path) -> dict[str, Any]:
    import subprocess

    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()

    models = {}
    for version in (PARENT_VERSION, REPAIRED_VERSION):
        model_dir = root / "models" / "superset" / version
        models[version] = {
            "network_bnd_sha256": _sha256(model_dir / "network.bnd"),
            "baseline_cfg_sha256": _sha256(model_dir / "baseline.cfg"),
            "provenance_toml_sha256": _sha256(model_dir / "provenance.toml"),
            "conditions_sha256": {
                p.name: _sha256(p)
                for p in sorted((model_dir / "conditions").glob("*.cfg"))
            },
        }
    try:
        import maboss

        maboss_version = getattr(maboss, "__version__", "unknown")
    except ImportError:  # pragma: no cover
        maboss_version = "unavailable"
    return {
        "git_commit": _git("rev-parse", "HEAD"),
        "python": platform.python_version(),
        "maboss_python_package": maboss_version,
        "platform": platform.platform(),
        "models": models,
        "generator_files": {f: _sha256(root / f) for f in GENERATOR_FILES},
        "preregistration_sha256": _sha256(root / PREREGISTRATION),
        "protocols_yaml_sha256": _sha256(root / "config/protocols.yaml"),
    }


def build(root: Path | None = None, workers: int = 3) -> dict[str, Any]:
    """Run every pre-registered pair and write the four artifacts."""
    active = root or repo_root()
    tasks = [
        _Task(model, count, replicate, str(active))
        for count in TRAJECTORY_COUNTS
        for replicate in range(REPLICATES)
        for model in (PARENT_VERSION, REPAIRED_VERSION)
    ]
    with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as pool:
        results = list(pool.map(_run_task, tasks))
    comparison = compare(results)

    _write_tsv(active / COMPARISON_TSV, comparison["rows"])
    _write_tsv(active / BLOCKS_TSV, comparison["blocks"])
    _write_tsv(active / TRACE_TSV, comparison["trace"])

    primary = {f"{s['cell']}:{s['estimand']}": s for s in comparison["stability"]}
    settings = {
        "artifact": "u5b_readout_transient_comparison",
        "claim_boundary": (
            "Paired differences of MaBoSS phase-averaged and final-tick node "
            "occupancies between two model versions on common random numbers, at "
            "each phase's declared dimensionless horizon. The interval is the "
            "run-to-run reproducibility of the paired estimator on disjoint seed "
            "blocks: not an i.i.d. Monte Carlo SE, not a biological, experimental "
            "or kinetic uncertainty, and no statement about days. WITHIN_TOLERANCE "
            "means no detected transient change at this precision, never no change."
        ),
        "preregistration": str(PREREGISTRATION),
        "parent_model_version": PARENT_VERSION,
        "model_version": REPAIRED_VERSION,
        "repaired_node": REPAIRED_NODE,
        "arms": list(ARMS),
        "cells": comparison["cells"],
        "horizon": "declared relative_duration per phase (dimensionless MaBoSS time)",
        "replicates": REPLICATES,
        "trajectory_counts": list(TRAJECTORY_COUNTS),
        "governing_trajectory_count": GOVERNING_TRAJECTORIES,
        "seed_rule": {
            str(GOVERNING_TRAJECTORIES): "1 + r * 20000",
            str(CHECK_TRAJECTORIES): "400001 + r * 2000",
        },
        "tolerance": TOLERANCE,
        "family_alpha": FAMILY_ALPHA,
        "families": comparison["families"],
        "expectations": comparison["expectations"],
        "stability": comparison["stability"],
        "primary_reported_verdicts": {
            k: v["reported_verdict"] for k, v in primary.items()
        },
        "structural_identity": structural_identity(active),
        "provenance": _provenance(active),
    }
    (active / SETTINGS_JSON).write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return settings


if __name__ == "__main__":  # pragma: no cover
    import sys

    print(
        json.dumps(
            build(workers=int(sys.argv[1]) if len(sys.argv) > 1 else 3)[
                "primary_reported_verdicts"
            ],
            indent=2,
        )
    )
