"""Freeze the v0.6.0 golden-lineage reference used by
tests/integration/test_golden_lineage_v060.py.

The result is a computational regression reference. It is not biological
validation. It records what the committed implementation produced for a few
seeded multi-phase lineages of the adopted model, so that a later change to the
continuation or execution path that moves any of those numbers fails a test
instead of passing silently. Audit mutation M6c (2026-10-15) did exactly that:
it moved 1 % of the carried joint mass and passed every test of this model.

Re-freezing replaces the expected values. Do it only when a change to the
simulation is intended and reviewed. Never do it to make a failing test pass.
The script refuses to run while tracked files under src/, models/ or config/
differ from HEAD, because a reference frozen from uncommitted code could not be
reconstructed.

    PYTHONPATH=src python -B scripts/freeze_golden_lineage.py
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests/fixtures/golden_lineage/v060_continuation_reference.json"
MODEL_VERSION = "adoc-literature-superset-v0.6.0"

#: Each case is one declared lineage, run from basal through every
#: `continuation_from` to the named protocol. Every phase boundary is a joint
#: continuation. The declared horizon stops each phase before its fixed point, so
#: most nodes sit at intermediate probabilities that any change to the carried
#: state moves. The converged mifepristone case covers the horizon the
#: concordance build reads.
CASES = (
    {
        "protocol_id": "adhesion_challenge_hormone_treated_mifepristone",
        "horizon_class": "declared",
    },
    {"protocol_id": "washout", "horizon_class": "declared"},
    {"protocol_id": "adhesion_challenge_hormone_treated", "horizon_class": "declared"},
    {
        "protocol_id": "adhesion_challenge_hormone_treated_mifepristone",
        "horizon_class": "converged",
    },
)
SEEDS = (1,)
TRAJECTORY_COUNT = 2000

#: The inputs that decide these numbers apart from the code. A change here is
#: a model change, so the test reports it as one instead of as a numerical
#: mismatch.
INPUT_PATHS = (
    "config/protocols_markerless.yaml",
    "config/intervention_library.tsv",
    "config/direct_effect_adjudications.tsv",
    "config/direct_effect_target_policy.tsv",
    "config/direct_effect_target_declarations.tsv",
    "config/node_entity_map.tsv",
)
MODEL_DIR = f"models/superset/{MODEL_VERSION}"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def input_digests(root: Path = ROOT) -> dict[str, str]:
    """sha256 of every recorded input file: the model directory and INPUT_PATHS."""
    tracked = _git("ls-files", "-z", "--", MODEL_DIR).split("\0")
    paths = sorted({p for p in tracked if p} | set(INPUT_PATHS))
    return {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths
    }


def environment() -> dict[str, str]:
    return {
        "maboss": metadata.version("maboss"),
        "python": platform.python_version(),
        "machine": platform.machine(),
    }


def run_case(case: dict, root: Path = ROOT) -> dict:
    from dt_adoc.concordance.simulate import run_arm

    run = run_arm(
        case["protocol_id"],
        case["protocol_id"],
        horizon_class=case["horizon_class"],
        model_version=MODEL_VERSION,
        root=root,
        trajectory_count=TRAJECTORY_COUNT,
        seeds=SEEDS,
    )
    return {
        "lineage": list(run.lineage),
        "phase_horizon": run.phase_horizon,
        "node_mean": dict(sorted(run.node_mean.items())),
    }


def main() -> int:
    dirty = _git("status", "--porcelain", "--", "src", "models", "config")
    if dirty:
        print("refusing to freeze from uncommitted src/, models/ or config/:\n" + dirty)
        return 1
    reference = {
        "description": (
            "Computational regression reference for the adopted "
            f"{MODEL_VERSION}: exact node probabilities at the end of seeded, "
            "multi-phase joint-continuation lineages, as the committed "
            "implementation produced them. Not biological validation."
        ),
        "frozen_from_commit": _git("rev-parse", "HEAD"),
        "frozen_from_trees": {
            part: _git("rev-parse", f"HEAD:{part}")
            for part in ("src", "models", "config")
        },
        "model_version": MODEL_VERSION,
        "seeds": list(SEEDS),
        "trajectory_count": TRAJECTORY_COUNT,
        "environment": environment(),
        "inputs_sha256": input_digests(),
        "cases": [],
    }
    for case in CASES:
        result = run_case(case)
        reference["cases"].append({**case, **result})
        print(
            case["protocol_id"], case["horizon_class"], len(result["lineage"]), "phases"
        )
    REFERENCE.parent.mkdir(parents=True, exist_ok=True)
    REFERENCE.write_text(
        json.dumps(reference, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {REFERENCE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    raise SystemExit(main())
