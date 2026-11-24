"""Measure what ENDO-TWIN workloads actually cost, and extrapolate explicitly.

Two things are kept apart here on purpose, because conflating them is how
compute budgets stop being checkable:

* **Measured** — wall time and CPU time for units that this repository really
  runs, at stated trajectory counts, scenario counts and model version, on the
  machine the benchmark ran on. Reproducible with
  ``pixi run endotwin-benchmark``.
* **Extrapolated** — what a larger campaign would cost, computed from those
  measurements by multiplying out factors that are each named and defended
  separately. Every factor is a planning assumption, not a measurement, and is
  printed as such.

The point is that a reader can change any factor and recompute, rather than
having to trust a single aggregate number.

MaBoSS here runs single-threaded (``thread_count = 1`` in
:mod:`endotwin.simulate`), so CPU time and wall time per run are close and the
ensemble is embarrassingly parallel across scenarios, rate sets and conditions.
"""

from __future__ import annotations

import json
import platform
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from endotwin import DEFAULT_MODEL_VERSION
from endotwin.model import load_model
from endotwin.protocols import load_protocols
from endotwin.simulate import SimulationSettings, simulate_condition

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "endotwin" / "results" / "benchmarks"

#: Trajectory counts to time. 2000 is what the rate-sensitivity ensemble uses,
#: 10000 what the reference dynamics use; 50000 probes the large-batch regime.
SAMPLE_COUNTS = (2000, 10000, 50000)
REPEATS = 3


@dataclass
class Measurement:
    label: str
    sample_count: int
    phases: int
    repeats: int
    wall_seconds: list[float] = field(default_factory=list)
    cpu_seconds: list[float] = field(default_factory=list)

    @property
    def median_wall(self) -> float:
        return statistics.median(self.wall_seconds)

    @property
    def median_cpu(self) -> float:
        return statistics.median(self.cpu_seconds)

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "sample_count": self.sample_count,
            "phases": self.phases,
            "repeats": self.repeats,
            "median_wall_seconds": round(self.median_wall, 4),
            "median_cpu_seconds": round(self.median_cpu, 4),
            "cpu_seconds_per_trajectory": round(self.median_cpu / self.sample_count, 9),
            "wall_seconds_all": [round(x, 4) for x in self.wall_seconds],
        }


def measure(version: str = DEFAULT_MODEL_VERSION) -> list[Measurement]:
    model = load_model(version)
    protocols = load_protocols(model)
    condition = protocols.conditions["reference"]
    out: list[Measurement] = []
    for n in SAMPLE_COUNTS:
        m = Measurement(
            label="simulate_condition(reference)",
            sample_count=n,
            phases=len(condition.phases),
            repeats=REPEATS,
        )
        for rep in range(REPEATS):
            settings = SimulationSettings(sample_count=n, seed=rep + 1)
            w0, c0 = time.perf_counter(), time.process_time()
            simulate_condition(
                model, condition, protocols.interventions, None, settings
            )
            m.wall_seconds.append(time.perf_counter() - w0)
            m.cpu_seconds.append(time.process_time() - c0)
        out.append(m)
    return out


def environment(version: str) -> dict[str, Any]:
    model = load_model(version)
    try:
        from endotwin.simulate import engine_report

        engine = engine_report()
    except (ImportError, RuntimeError):  # pragma: no cover - MaBoSS absent
        engine = {}
    return {
        "model_version": version,
        "nodes": len(model.nodes),
        "free_variables": len(model.inputs),
        "conditions": len(load_protocols(model).conditions),
        "families": len(model.families()),
        "scenarios": len(model.scenarios()),
        "engine": engine,
        "thread_count": 1,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
    }


def _product(factors: dict[str, dict[str, Any]]) -> int:
    runs = 1
    for f in factors.values():
        runs *= int(f["value"])
    return runs


def scaling(measurements: list[Measurement], env: dict[str, Any]) -> dict[str, Any]:
    """Two extrapolations, kept apart because they answer different questions.

    **funded** costs the analyses the proposal actually describes. **illustrative**
    costs a larger campaign nobody has committed to, and exists only to show what
    reaching a much bigger number would take. Mixing them is how a compute budget
    stops being checkable, so they never share a total.

    One factor is deliberately absent from both: per-donor model fitting. v10 is
    explicit that the inferred activities "inform a common G1 model
    initialisation ... without fitting donor-specific models", so a donor
    multiplier would contradict the proposal rather than extrapolate it.
    """
    per_run = {m.sample_count: m.median_cpu for m in measurements}
    unit = per_run.get(10000) or next(iter(per_run.values()))
    internal = env["nodes"] - env["free_variables"]
    singles = 2 * internal  # each internal node forced ON or OFF
    pairs = singles * (singles - 1) // 2

    scenarios = {
        "value": env["scenarios"],
        "basis": "MEASURED from the model: one variant per hypothesis family.",
    }
    conditions = {
        "value": env["conditions"],
        "basis": "MEASURED from endotwin/config/protocols.yaml.",
    }
    revisions = {
        "value": 10,
        "basis": "PLANNING ASSUMPTION: WP1 versions the model repeatedly before the "
        "WP2 freeze, and WP3/WP4 revise it again.",
    }

    funded = {
        "single_perturbations": {
            "value": singles,
            "basis": f"DERIVED: {internal} internal (non-input) nodes, each forcible "
            "ON or OFF. v10 funds perturbation screening for intervention selection "
            "(WP4) and targeted perturbations testing selected dependencies before "
            "the WP2 freeze. It describes single perturbations, not combinations.",
        },
        "scenarios": scenarios,
        "conditions": conditions,
        "rate_sets": {
            "value": 100,
            "basis": "PLANNING ASSUMPTION, and the weakest number here. v10 funds "
            "'systematic sensitivity analyses' of rules, rates and initial "
            "conditions but states no ensemble size; current practice is 30.",
        },
        "model_revisions": revisions,
    }
    illustrative = {
        "pairwise_perturbations": {
            "value": pairs,
            "basis": f"NOT FUNDED. {singles}*{singles - 1}/2 = {pairs} unordered "
            "pairs. Combinatorial screening is a plausible future direction, "
            "especially for WP4 synergy, but no work package commits to it and no "
            "code here performs it.",
        },
        "scenarios": scenarios,
        "conditions": conditions,
        "rate_sets": {
            "value": 1000,
            "basis": "NOT FUNDED at this size: a full uncertainty-quantification "
            "target, against 30 in current practice.",
        },
        "model_revisions": revisions,
    }

    def cost(factors: dict[str, dict[str, Any]]) -> dict[str, Any]:
        runs = _product(factors)
        return {
            "factors": factors,
            "condition_runs": runs,
            "cpu_hours": round(runs * unit / 3600.0, 1),
        }

    return {
        "unit_cpu_seconds_per_condition_run": round(unit, 6),
        "unit_basis": "MEASURED: median CPU seconds for one 3-phase condition at "
        "10,000 trajectories.",
        "funded": cost(funded),
        "illustrative": cost(illustrative),
        "excluded_factors": {
            "per_donor_models": "v10 states the plan informs a COMMON G1 model "
            "initialisation 'without fitting donor-specific models', so a donor "
            "multiplier is excluded from both columns."
        },
        "caveats": [
            (
                "Single-condition timing on an otherwise idle machine. Real "
                "campaigns additionally pay model loading, protocol resolution, "
                "result assembly and I/O per batch, and spot-instance retries."
            ),
            (
                "A product of planning factors is not a measurement. Changing any "
                "one changes its total proportionally."
            ),
            (
                "These are CPU-hours consumed: not vCPU-hours provisioned, not "
                "elapsed time, not money. See docs/computational_resources.md."
            ),
        ],
    }


def write_report(version: str = DEFAULT_MODEL_VERSION) -> tuple[Path, Path]:
    env = environment(version)
    measurements = measure(version)
    extrapolation = scaling(measurements, env)
    OUT.mkdir(parents=True, exist_ok=True)

    payload = {
        "environment": env,
        "measured": [m.as_dict() for m in measurements],
        "extrapolated": extrapolation,
    }
    json_path = OUT / "benchmark.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")

    lines = [
        f"# Computational benchmark — `{version}`\n",
        "\nGenerated by `pixi run endotwin-benchmark`. Do not edit by hand.\n",
        (
            "\nTiming is machine-specific and will differ on other hardware. These\n"
            "figures exist so that the repository's compute planning can be checked,\n"
            "and they are deliberately kept out of the grant text.\n"
        ),
        "\n## Environment\n\n",
        (
            f"- Model `{env['model_version']}`: {env['nodes']} nodes, "
            f"{env['families']} hypothesis families, {env['scenarios']} scenarios\n"
        ),
        (
            f"- Engine: {env['engine'].get('package', 'maboss')} "
            f"{env['engine'].get('version', '')}, `thread_count = 1`\n"
        ),
        f"- Python {env['python']} on {env['platform']}\n",
        "\n## Measured\n\n",
        (
            "One `simulate_condition` call on the 3-phase `reference` condition,\n"
            f"median of {REPEATS} repeats.\n\n"
        ),
        "| Trajectories | Wall (s) | CPU (s) | CPU s per trajectory |\n",
        "|---|---|---|---|\n",
    ]
    for m in measurements:
        lines.append(
            f"| {m.sample_count:,} | {m.median_wall:.3f} | {m.median_cpu:.3f} | "
            f"{m.median_cpu / m.sample_count:.2e} |\n"
        )
    lines.append(
        "\nPer-trajectory cost falls as the batch grows, because fixed setup is\n"
        "amortised. The ensemble is embarrassingly parallel across scenarios, rate\n"
        "sets, conditions and donors, while each individual run is single-threaded:\n"
        "the binding resource is concurrency, not per-run speed.\n"
    )
    lines.append("\n## Extrapolated — planning assumptions, not measurements\n\n")
    lines.append(
        f"Unit: **{extrapolation['unit_cpu_seconds_per_condition_run']} CPU-seconds** "
        "per condition run at 10,000 trajectories (measured).\n"
    )
    for key, heading, intro in (
        (
            "funded",
            "Funded analyses",
            (
                "The analyses v10 actually describes: rule comparison across every "
                "scenario, systematic sensitivity analysis, and single-perturbation "
                "screening for intervention selection."
            ),
        ),
        (
            "illustrative",
            "Illustrative only — NOT the funded workload",
            (
                "A larger campaign no work package commits to, shown so that the gap "
                "between the funded plan and a much bigger number is visible."
            ),
        ),
    ):
        block = extrapolation[key]
        lines.append(f"\n### {heading}\n\n{intro}\n\n")
        lines.append("| Factor | Value | Basis |\n|---|---|---|\n")
        for name, f in block["factors"].items():
            lines.append(f"| `{name}` | {f['value']:,} | {f['basis']} |\n")
        lines.append(
            f"\n**{block['condition_runs']:,} condition runs ≈ "
            f"{block['cpu_hours']:,.0f} CPU-hours.**\n"
        )
    lines.append("\n### Excluded on purpose\n\n")
    for name, why in extrapolation["excluded_factors"].items():
        lines.append(f"- `{name}`: {why}\n")
    lines.append("\n### Caveats\n\n")
    for c in extrapolation["caveats"]:
        lines.append(f"- {c}\n")
    md_path = OUT / "benchmark.md"
    md_path.write_text("".join(lines), encoding="utf-8")
    return json_path, md_path
