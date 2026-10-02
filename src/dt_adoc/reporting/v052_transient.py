"""v0.5.2: paired transient comparison against v0.5.1, with attribution arms.

Implements ``docs/v052_paep_hand2/transient_preregistration.md``, as extended for
run 2 by ``transient_preregistration_addendum_01.md``. The addendum was committed
after run 1, which is preserved INVALID in ``run1_invalid/``, and before run 2.
Every constant below is read from one of those two files, or is U5b's constant,
which they adopt verbatim. If a constant here and the files ever disagree, the
files are right and this module is the defect.

Run 2 differs from run 1 in exactly the addendum's three respects:

* **A1.** Expectation 1 is exact final-tick per-state identity, plus node
  differences ``<= SNAP``.
* **A2.** Per-tick paired differences with ``|d| <= SNAP`` are set to 0 before
  the estimands are computed.
* **A3.** Fresh seed blocks are used.

The run machinery is U5b's, imported rather than copied:

* the arms, the dedup into ten cells, and the seed rule;
* one replicate of every cell on one model version (``_run_task``);
* the verdict table (``classify``).

What is new here is the comparison layout:

* the primary comparison, v0.5.2 against v0.5.1, at both trajectory counts;
* two attribution comparisons at the governing count, C1-only and C5-only
  against v0.5.1, on the same seeds as the primary comparison.

Each comparison has three families, derived from that comparison's own rules by
``v052_increment.affected_nodes``:

* **primary:** the changed node(s);
* **downstream:** their transitive readers;
* **unaffected:** every other node.

For the primary comparison this is exactly the pre-registered 2 + 5 + 52 split.
Section 3 says the attribution families are "defined the same way", and this
module reads that as the same derivation applied to each variant. Under that
reading, C1-only's primary node is ``OUT_EPITHELIAL_RECEPTIVE`` and C5-only's is
``E_ESTROGENIC_PROLIFERATION``. ``INTERPRETATION`` records the reading in the
artifact.

The attribution variants are emitted by ``v052_increment.build_increment`` into
a scratch repository root, which is never committed. That root symlinks every
top-level entry of the real one except ``models/`` and ``output/``. It has its
own ``models/superset/`` holding the variant directories beside symlinks to the
committed versions, and its own real ``output/``, so the runner's own run
records never land in the repository.
"""

from __future__ import annotations

import json
import math
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting import u5b_readout_transient as u5b
from dt_adoc.reporting.u5b_readout_transient import (
    ARMS,
    CHECK_TRAJECTORIES,
    ESTIMANDS,
    EXACT_IDENTITY_CELLS,
    FAMILY_ALPHA,
    GOVERNING_TRAJECTORIES,
    REPLICATES,
    TOLERANCE,
    TRAJECTORY_COUNTS,
    _counts,
    _normal_quantile,
    _sha256,
    _t_quantile,
    _Task,
    _write_tsv,
    classify,
)
from dt_adoc.reporting.v052_increment import (
    MODEL_VERSION,
    PARENT_VERSION,
    SUPERSET_DIR,
    affected_nodes,
    structural_identity,
    write_increment,
)

C1_ONLY = f"{MODEL_VERSION}-c1only"
C5_ONLY = f"{MODEL_VERSION}-c5only"
#: comparison id -> (new version, change ids, trajectory counts run)
COMPARISONS: dict[str, tuple[str, tuple[str, ...], tuple[int, ...]]] = {
    "v052_vs_v051": (MODEL_VERSION, ("C1", "C5"), TRAJECTORY_COUNTS),
    "c1only_vs_v051": (C1_ONLY, ("C1",), (GOVERNING_TRAJECTORIES,)),
    "c5only_vs_v051": (C5_ONLY, ("C5",), (GOVERNING_TRAJECTORIES,)),
}
PRIMARY_COMPARISON = "v052_vs_v051"
ATTRIBUTION_VERSIONS = (C1_ONLY, C5_ONLY)
#: Pre-registration section 5, expectation 3: comparison -> node whose
#: phase-averaged difference must not lie wholly below zero.
DIRECTION_EXPECTATIONS = {
    "c1only_vs_v051": "OUT_EPITHELIAL_RECEPTIVE",
    "c5only_vs_v051": "E_ESTROGENIC_PROLIFERATION",
}
INTERPRETATION = (
    "Families per comparison are derived from that comparison's own rules: "
    "primary = the changed node(s), downstream = their transitive readers, "
    "unaffected = every other node. For v052_vs_v051 this is exactly the "
    "pre-registered 2 + 5 + 52 split; for the attribution arms it is the reading "
    "of section 3's 'defined the same way' as the same derivation."
)

OUTPUT_DIR = Path("docs/v052_paep_hand2")
COMPARISON_TSV = OUTPUT_DIR / "transient_comparison.tsv"
BLOCKS_TSV = OUTPUT_DIR / "transient_blocks.tsv"
TRACE_TSV = OUTPUT_DIR / "transient_trace.tsv"
SETTINGS_JSON = OUTPUT_DIR / "transient_run_settings.json"
PREREGISTRATION = OUTPUT_DIR / "transient_preregistration.md"
ADDENDUM = OUTPUT_DIR / "transient_preregistration_addendum_01.md"
RUN_ID = "run2"
#: Addendum A1/A2: node-marginal differences at or below this are rounding.
SNAP = 1e-12

GENERATOR_FILES = (
    "src/dt_adoc/reporting/v052_transient.py",
    "src/dt_adoc/reporting/v052_increment.py",
    "src/dt_adoc/reporting/u5b_readout_transient.py",
    "src/dt_adoc/concordance/simulate.py",
    "src/dt_adoc/simulation/runner.py",
    "src/dt_adoc/protocols/conditions.py",
)


def replicate_seed(replicate: int, trajectory_count: int) -> int:
    """Addendum A3: fresh blocks, disjoint from run 1, the pilot and each other."""
    if not 0 <= replicate < REPLICATES:
        raise ValueError(f"replicate {replicate} is not pre-registered")
    if trajectory_count == GOVERNING_TRAJECTORIES:
        return 1_000_001 + replicate * GOVERNING_TRAJECTORIES
    if trajectory_count == CHECK_TRAJECTORIES:
        return 1_400_001 + replicate * CHECK_TRAJECTORIES
    raise ValueError(f"trajectory count {trajectory_count} is not pre-registered")


def _run_task(task: _Task) -> dict[str, Any]:
    """One replicate of every cell on one version: node marginals and final states.

    U5b's ``_run_task``, with two differences. It uses the addendum's seeds, and
    it also keeps each phase's final-tick per-state distribution, on which
    addendum A1 tests exact identity.
    """
    from dt_adoc.concordance.simulate import protocol_continuation
    from dt_adoc.simulation.runner import run_protocol

    root = Path(task.root)
    seed = replicate_seed(task.replicate, task.trajectory_count)
    cache: dict[tuple[str, ...], Any] = {}
    out: dict[str, dict[str, Any]] = {}
    for prefix, phase in sorted(
        u5b._cells(root, task.model_version).items(), key=lambda kv: len(kv[0])
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
        states = result.final_result.last_states_probtraj
        out[phase] = {
            "times": [float(t) for t in table.index],
            "nodes": {str(c): [float(v) for v in table[c]] for c in table.columns},
            "final_states": {str(c): float(states[c].iloc[-1]) for c in states.columns},
        }
    return {
        "model_version": task.model_version,
        "trajectory_count": task.trajectory_count,
        "replicate": task.replicate,
        "seed": seed,
        "cells": out,
    }


def _snap(d: float) -> float:
    return 0.0 if abs(d) <= SNAP else d


def _estimands(new: list[float], parent: list[float]) -> dict[str, float]:
    """Addendum A2: rounding-level per-tick differences are exactly 0."""
    diffs = [_snap(a - b) for a, b in zip(new, parent, strict=True)]
    return {"time_averaged": mean(diffs), "final_tick": diffs[-1]}


def families(root: Path, comparison: str) -> dict[str, set[str]]:
    """Primary, downstream and unaffected node sets for one comparison."""
    new_version = COMPARISONS[comparison][0]
    parent = parse_bnd_rules(root / SUPERSET_DIR / PARENT_VERSION / "network.bnd")
    rules = parse_bnd_rules(root / SUPERSET_DIR / new_version / "network.bnd")
    changed = {n for n in rules if rules[n] != parent.get(n)}
    affected = affected_nodes(rules, changed)
    return {
        "primary": changed,
        "downstream": affected - changed,
        "unaffected": set(rules) - affected,
    }


def attribution_root(active: Path, scratch: Path) -> Path:
    """A scratch repository root carrying the two single-change variants."""
    for entry in sorted(active.iterdir()):
        if entry.name in {"models", "output", ".git", ".pixi"}:
            continue
        (scratch / entry.name).symlink_to(entry)
    (scratch / "output").mkdir()
    models = scratch / "models"
    models.mkdir()
    for entry in sorted((active / "models").iterdir()):
        if entry.name != "superset":
            (models / entry.name).symlink_to(entry)
    superset = models / "superset"
    superset.mkdir()
    for entry in sorted((active / SUPERSET_DIR).iterdir()):
        (superset / entry.name).symlink_to(entry)
    for version, change_ids, _ in (COMPARISONS[c] for c in COMPARISONS):
        if version in ATTRIBUTION_VERSIONS:
            write_increment(scratch, change_ids, version)
    return scratch


def compare(
    results: list[dict[str, Any]], node_families: dict[str, dict[str, set[str]]]
) -> dict[str, Any]:
    """Pair the runs, classify every interval, and evaluate the expectations."""
    by_key = {
        (r["model_version"], r["trajectory_count"], r["replicate"]): r for r in results
    }
    cells = sorted(results[0]["cells"])
    nodes_by_cell = {cell: sorted(results[0]["cells"][cell]["nodes"]) for cell in cells}

    def family_of(comparison: str, node: str) -> str:
        for name, members in node_families[comparison].items():
            if node in members:
                return name
        raise ValueError(f"{node} is in no family of {comparison}")

    per_interval: dict[tuple[str, int, str, str, str], list[float]] = {}
    blocks: list[dict[str, Any]] = []
    exact_identity: dict[tuple[str, str], bool] = {}
    state_identity: dict[tuple[str, str], bool] = {}
    max_node_gap: dict[tuple[str, str], float] = {}
    traces: dict[tuple[str, str], list[list[float]]] = {}
    for comparison, (new_version, _, counts) in COMPARISONS.items():
        for count in counts:
            for replicate in range(REPLICATES):
                new = by_key[(new_version, count, replicate)]
                parent = by_key[(PARENT_VERSION, count, replicate)]
                if new["seed"] != parent["seed"]:
                    raise ValueError("the two arms of a pair must share a seed")
                for cell in cells:
                    a, b = new["cells"][cell], parent["cells"][cell]
                    if a["times"] != b["times"] or sorted(a["nodes"]) != sorted(
                        b["nodes"]
                    ):
                        raise ValueError(
                            f"{comparison} {cell}: the versions report different grids"
                        )
                    if cell in EXACT_IDENTITY_CELLS:
                        # Addendum A1, at both counts and in every replicate.
                        key = (comparison, cell)
                        states_equal = a["final_states"] == b["final_states"]
                        node_gap = max(
                            abs(x - y)
                            for n in a["nodes"]
                            for x, y in zip(a["nodes"][n], b["nodes"][n], strict=True)
                        )
                        same = states_equal and node_gap <= SNAP
                        exact_identity[key] = exact_identity.get(key, True) and same
                        state_identity[key] = (
                            state_identity.get(key, True) and states_equal
                        )
                        max_node_gap[key] = max(max_node_gap.get(key, 0.0), node_gap)
                    for node in nodes_by_cell[cell]:
                        values = _estimands(a["nodes"][node], b["nodes"][node])
                        for estimand, value in values.items():
                            per_interval.setdefault(
                                (comparison, count, cell, node, estimand), []
                            ).append(value)
                        if family_of(comparison, node) != "primary":
                            continue
                        blocks.append(
                            {
                                "comparison": comparison,
                                "trajectory_count": count,
                                "replicate": replicate,
                                "seed": new["seed"],
                                "trajectory_seed_range": (
                                    f"{new['seed']}..{new['seed'] + count - 1}"
                                ),
                                "cell": cell,
                                "node_id": node,
                                "parent_time_averaged": mean(b["nodes"][node]),
                                "new_time_averaged": mean(a["nodes"][node]),
                                "paired_time_averaged": values["time_averaged"],
                                "parent_final_tick": b["nodes"][node][-1],
                                "new_final_tick": a["nodes"][node][-1],
                                "paired_final_tick": values["final_tick"],
                            }
                        )
                        if (
                            comparison == PRIMARY_COMPARISON
                            and count == GOVERNING_TRAJECTORIES
                        ):
                            traces.setdefault((cell, node), []).append(
                                [
                                    x - y
                                    for x, y in zip(
                                        a["nodes"][node], b["nodes"][node], strict=True
                                    )
                                ]
                            )

    # Bonferroni within each family of each comparison, counted at one
    # trajectory count (every count of a comparison has the same intervals).
    family_sizes: dict[tuple[str, str], int] = {}
    for comparison in COMPARISONS:
        for cell in cells:
            for node in nodes_by_cell[cell]:
                key = (comparison, family_of(comparison, node))
                family_sizes[key] = family_sizes.get(key, 0) + len(ESTIMANDS)
    alpha = {key: FAMILY_ALPHA / n for key, n in family_sizes.items()}
    t_q = {key: _t_quantile(a, REPLICATES - 1) for key, a in alpha.items()}
    z_q = {key: _normal_quantile(a) for key, a in alpha.items()}

    rows: list[dict[str, Any]] = []
    classified: dict[tuple[str, int, str, str, str], dict[str, Any]] = {}
    for key, diffs in sorted(per_interval.items()):
        comparison, count, cell, node, estimand = key
        family = family_of(comparison, node)
        summary = classify(diffs, t_q[(comparison, family)])
        classified[key] = summary
        rows.append(
            {
                "comparison": comparison,
                "trajectory_count": count,
                "cell": cell,
                "node_id": node,
                "estimand": estimand,
                "family": family,
                "replicates": len(diffs),
                "t_quantile": t_q[(comparison, family)],
                **summary,
            }
        )

    stability: list[dict[str, Any]] = []
    primary_nodes = sorted(node_families[PRIMARY_COMPARISON]["primary"])
    for cell in cells:
        for node in primary_nodes:
            for estimand in ESTIMANDS:
                big = classified[
                    (PRIMARY_COMPARISON, GOVERNING_TRAJECTORIES, cell, node, estimand)
                ]
                small = classified[
                    (PRIMARY_COMPARISON, CHECK_TRAJECTORIES, cell, node, estimand)
                ]
                bound = z_q[(PRIMARY_COMPARISON, "primary")] * math.sqrt(
                    big["se"] ** 2 + small["se"] ** 2
                )
                agree = abs(big["mean"] - small["mean"]) <= bound
                stable = bool(agree and big["verdict"] == small["verdict"])
                stability.append(
                    {
                        "cell": cell,
                        "node_id": node,
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
                        "stable": stable,
                        "reported_verdict": big["verdict"] if stable else "UNSTABLE",
                    }
                )

    expectations: dict[str, Any] = {
        "1_exact_identity_where_rules_never_disagree": {
            comparison: {
                "held": all(
                    exact_identity.get((comparison, c), False)
                    for c in EXACT_IDENTITY_CELLS
                ),
                "per_cell": {
                    c: {
                        "held": exact_identity.get((comparison, c), False),
                        "final_state_distributions_bitwise_equal": state_identity.get(
                            (comparison, c), False
                        ),
                        "max_abs_node_difference": max_node_gap.get(
                            (comparison, c), float("nan")
                        ),
                    }
                    for c in EXACT_IDENTITY_CELLS
                },
                "rule": (
                    "addendum 01 A1: final-tick per-state distributions bitwise "
                    f"equal AND every per-tick node difference <= {SNAP}, in every "
                    "replicate at every trajectory count run"
                ),
            }
            for comparison in COMPARISONS
        },
        "2_unaffected_family_same_law": {},
        "3_attribution_directions": {},
    }
    for comparison in COMPARISONS:
        governing = [
            r
            for r in rows
            if r["comparison"] == comparison
            and r["family"] == "unaffected"
            and r["trajectory_count"] == GOVERNING_TRAJECTORIES
        ]
        verdicts = _counts(r["verdict"] for r in governing)
        beyond = verdicts.get("BEYOND_TOLERANCE", 0)
        indeterminate = verdicts.get("INDETERMINATE", 0)
        expectations["2_unaffected_family_same_law"][comparison] = {
            "intervals": len(governing),
            "verdict_counts": verdicts,
            "defect_beyond_tolerance": beyond,
            "not_certified_indeterminate": indeterminate,
            "status": (
                "DEFECT"
                if beyond
                else "NOT_MET_AT_THIS_PRECISION"
                if indeterminate
                else "HELD"
            ),
            "max_abs_mean": max(abs(r["mean"]) for r in governing),
            "max_abs_interval_end": max(
                max(abs(r["low"]), abs(r["high"])) for r in governing
            ),
        }
    for comparison, node in DIRECTION_EXPECTATIONS.items():
        per_cell = {
            r["cell"]: {"mean": r["mean"], "low": r["low"], "high": r["high"]}
            for r in rows
            if r["comparison"] == comparison
            and r["node_id"] == node
            and r["estimand"] == "time_averaged"
            and r["trajectory_count"] == GOVERNING_TRAJECTORIES
        }
        falsified = sorted(c for c, v in per_cell.items() if v["high"] < 0)
        expectations["3_attribution_directions"][comparison] = {
            "node_id": node,
            "statement": "phase-averaged difference >= 0 in every cell",
            "falsified_in_cells": falsified,
            "held": not falsified,
            "per_cell": per_cell,
        }

    trace_rows: list[dict[str, Any]] = []
    pointwise_q = _t_quantile(FAMILY_ALPHA, REPLICATES - 1)
    for (cell, node), per_block in sorted(traces.items()):
        times = results[0]["cells"][cell]["times"]
        for index, time in enumerate(times):
            column = [block[index] for block in per_block]
            centre = mean(column)
            se = stdev(column) / math.sqrt(len(column))
            trace_rows.append(
                {
                    "cell": cell,
                    "node_id": node,
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
            "members": {
                c: {f: sorted(m) for f, m in fams.items()}
                for c, fams in node_families.items()
            },
            "intervals_per_count": {
                f"{c}:{f}": n for (c, f), n in sorted(family_sizes.items())
            },
            "alpha_per_interval": {
                f"{c}:{f}": a for (c, f), a in sorted(alpha.items())
            },
            "t_quantile": {f"{c}:{f}": q for (c, f), q in sorted(t_q.items())},
            "normal_quantile_for_stability": z_q[(PRIMARY_COMPARISON, "primary")],
            "pointwise_trace_t_quantile": pointwise_q,
            "interpretation": INTERPRETATION,
        },
        "cells": cells,
    }


def _model_hashes(root: Path, version: str) -> dict[str, Any]:
    model_dir = root / SUPERSET_DIR / version
    return {
        "network_bnd_sha256": _sha256(model_dir / "network.bnd"),
        "baseline_cfg_sha256": _sha256(model_dir / "baseline.cfg"),
        "provenance_toml_sha256": _sha256(model_dir / "provenance.toml"),
        "conditions_sha256": {
            p.name: _sha256(p) for p in sorted((model_dir / "conditions").glob("*.cfg"))
        },
    }


def _provenance(root: Path, scratch: Path) -> dict[str, Any]:
    import platform
    import subprocess

    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()

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
        "models": {v: _model_hashes(root, v) for v in (PARENT_VERSION, MODEL_VERSION)},
        "attribution_models_not_committed": {
            v: _model_hashes(scratch, v) for v in ATTRIBUTION_VERSIONS
        },
        "generator_files": {f: _sha256(root / f) for f in GENERATOR_FILES},
        "preregistration_sha256": _sha256(root / PREREGISTRATION),
        "addendum_sha256": _sha256(root / ADDENDUM),
        "protocols_yaml_sha256": _sha256(root / "config/protocols.yaml"),
    }


def build(root: Path | None = None, workers: int = 3) -> dict[str, Any]:
    """Run every pre-registered pair and write the four artifacts."""
    active = (root or repo_root()).resolve()
    with tempfile.TemporaryDirectory(prefix="v052-attribution-") as tmp:
        scratch = attribution_root(active, Path(tmp))
        node_families = {
            c: families(
                scratch if COMPARISONS[c][0] in ATTRIBUTION_VERSIONS else active, c
            )
            for c in COMPARISONS
        }
        runs = {(PARENT_VERSION, count) for count in TRAJECTORY_COUNTS}
        for version, _, counts in COMPARISONS.values():
            runs |= {(version, count) for count in counts}
        tasks = [
            _Task(
                version,
                count,
                replicate,
                str(scratch if version in ATTRIBUTION_VERSIONS else active),
            )
            for version, count in sorted(runs)
            for replicate in range(REPLICATES)
        ]
        with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as pool:
            results = list(pool.map(_run_task, tasks))
        comparison = compare(results, node_families)
        provenance = _provenance(active, scratch)

    _write_tsv(active / COMPARISON_TSV, comparison["rows"])
    _write_tsv(active / BLOCKS_TSV, comparison["blocks"])
    _write_tsv(active / TRACE_TSV, comparison["trace"])
    settings = {
        "artifact": "v052_transient_comparison",
        "run_id": RUN_ID,
        "addendum": str(ADDENDUM),
        "snap_threshold": SNAP,
        "claim_boundary": (
            "Paired differences of MaBoSS phase-averaged and final-tick node "
            "occupancies between model versions on common random numbers, at each "
            "phase's declared dimensionless horizon. The interval is the run-to-run "
            "reproducibility of the paired estimator on disjoint seed blocks: not an "
            "i.i.d. Monte Carlo SE, not a biological, experimental or kinetic "
            "uncertainty, and no statement about days. WITHIN_TOLERANCE means no "
            "detected transient change at this precision, never no change."
        ),
        "preregistration": str(PREREGISTRATION),
        "parent_model_version": PARENT_VERSION,
        "model_version": MODEL_VERSION,
        "comparisons": {
            c: {"new_version": v, "changes": list(ch), "trajectory_counts": list(n)}
            for c, (v, ch, n) in COMPARISONS.items()
        },
        "arms": list(ARMS),
        "cells": comparison["cells"],
        "horizon": "declared relative_duration per phase (dimensionless MaBoSS time)",
        "replicates": REPLICATES,
        "trajectory_counts": list(TRAJECTORY_COUNTS),
        "governing_trajectory_count": GOVERNING_TRAJECTORIES,
        "seed_rule": {
            str(GOVERNING_TRAJECTORIES): "1000001 + r * 20000",
            str(CHECK_TRAJECTORIES): "1400001 + r * 2000",
        },
        "tolerance": TOLERANCE,
        "family_alpha": FAMILY_ALPHA,
        "families": comparison["families"],
        "expectations": comparison["expectations"],
        "stability": comparison["stability"],
        "primary_reported_verdicts": {
            f"{s['cell']}:{s['node_id']}:{s['estimand']}": s["reported_verdict"]
            for s in comparison["stability"]
        },
        "structural_identity": structural_identity(active),
        "provenance": provenance,
    }
    (active / SETTINGS_JSON).write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return settings


if __name__ == "__main__":  # pragma: no cover
    import sys

    print(
        json.dumps(
            build(workers=int(sys.argv[1]) if len(sys.argv) > 1 else 3)["expectations"],
            indent=2,
            default=str,
        )
    )
