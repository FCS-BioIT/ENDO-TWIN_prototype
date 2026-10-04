"""Trajectory-attributing test of how MaBoSS seeds its trajectories.

``endpoint_replicates.seed_structure_probe`` shows that a pooled run equals the
mean of single-trajectory runs on consecutive seeds, on the whole node table and
the final joint state distribution. An external review (2026-09-23) correctly
noted that equal aggregates do not by themselves identify a trajectory
collection. This probe adds the test that does attribute a difference to named
trajectories.

**The shift test.** If trajectory ``k`` of a run with seed ``s`` is seeded
``s + k``, then the pooled runs with seeds ``s`` and ``s + d`` (``N``
trajectories each) share every trajectory except ``d`` at each end, so

    N * (pooled(s + d) - pooled(s)) == sum_{j < d} (single(s + N + j) - single(s + j))

must hold **exactly**, at every tick, for every recorded node -- the whole
difference between two pooled runs is carried by the ``2d`` named single
trajectories that the rule says enter and leave. Any other seeding rule (a
global stream, a seed hash, a per-thread offset) breaks it. It is checked for
several offsets ``d`` on a dynamic protocol at its declared horizon, and a
negative control applies the identity with the wrong trajectories, which must
fail.

Writes ``docs/endpoint/seed_structure_probe.json``. Cheap (seconds), single
process, no model change.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from dt_adoc.model.provenance import repo_root

MODEL_VERSION = "adoc-literature-superset-v0.5.0"
PROBE_PROTOCOL = "hormone_treated_maternal"
OUTPUT = Path("docs/endpoint/seed_structure_probe.json")
TOLERANCE = 1e-12


def _nodes(seed: int, count: int, root: Path) -> Any:
    from dt_adoc.simulation.runner import run_protocol

    return run_protocol(
        PROBE_PROTOCOL,
        model_version=MODEL_VERSION,
        root=root,
        seed=seed,
        sample_count=count,
    ).final_result.nodes_probtraj


def shift_probe(
    root: Path | None = None,
    *,
    start: int = 1,
    trajectories: int = 30,
    offsets: tuple[int, ...] = (1, 3, 7),
) -> dict[str, Any]:
    active_root = root or repo_root()
    # One extra seed so the wrong-attribution control can shift by one.
    top = start + trajectories + max(offsets) + 1
    single = {seed: _nodes(seed, 1, active_root) for seed in range(start, top)}
    base = _nodes(start, trajectories, active_root)
    values = base.to_numpy()
    tests = []
    for d in offsets:
        shifted = _nodes(start + d, trajectories, active_root)
        lhs = (shifted - base) * trajectories
        entering = sum(single[start + trajectories + j] for j in range(d))
        leaving = sum(single[start + j] for j in range(d))
        rhs = entering - leaving
        # Wrong attribution, a near miss: the entering trajectories shifted by
        # one seed. It must NOT explain the difference.
        wrong_entering = sum(single[start + trajectories + 1 + j] for j in range(d))
        tests.append(
            {
                "offset": d,
                "pooled_seeds": [start, start + d],
                "entering_single_seeds": [start + trajectories + j for j in range(d)],
                "leaving_single_seeds": [start + j for j in range(d)],
                "max_abs_residual": float((lhs - rhs).abs().max().max()),
                "max_abs_difference_being_explained": float(lhs.abs().max().max()),
                "wrong_attribution_max_abs_residual": float(
                    (lhs - (wrong_entering - leaving)).abs().max().max()
                ),
            }
        )
    return {
        "model_version": MODEL_VERSION,
        "probe_protocol": PROBE_PROTOCOL,
        "horizon": "declared",
        "trajectories": trajectories,
        "node_table_shape": list(base.shape),
        "transient_node_tick_cells": int(((values > 1e-9) & (values < 1 - 1e-9)).sum()),
        "tolerance": TOLERANCE,
        "shift_tests": tests,
        "consistent_with_per_trajectory_seed_s_plus_k": all(
            t["max_abs_residual"] < TOLERANCE
            and t["max_abs_difference_being_explained"] > 0.01
            and t["wrong_attribution_max_abs_residual"] > 0.01
            for t in tests
        ),
    }


def write_probe(root: Path | None = None) -> dict[str, Any]:
    from dt_adoc.simulation.runner import _maboss_python_package_version

    active_root = root or repo_root()
    payload = {
        "schema_version": "1.0",
        "claim_boundary": (
            "A measured behaviour of the installed MaBoSS binary, not a property "
            "read from its source. It identifies which single-seed trajectories "
            "account for the difference between two pooled runs; it is not a "
            "statement about statistical independence of streams."
        ),
        "maboss_python_version": _maboss_python_package_version(),
        "generator_sha256": hashlib.sha256(
            (active_root / "src/dt_adoc/reporting/seed_structure.py").read_bytes()
        ).hexdigest(),
        **shift_probe(active_root),
    }
    (active_root / OUTPUT).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload


if __name__ == "__main__":
    result = write_probe()
    print(
        json.dumps(
            {
                "consistent": result["consistent_with_per_trajectory_seed_s_plus_k"],
                "tests": result["shift_tests"],
            },
            indent=2,
        )
    )
