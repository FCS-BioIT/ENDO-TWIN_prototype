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
        "families": len(model.families()),
        "scenarios": len(model.scenarios()),
        "engine": engine,
        "thread_count": 1,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
    }


def scaling(measurements: list[Measurement], env: dict[str, Any]) -> dict[str, Any]:
    """Extrapolate a campaign cost. Every factor below is an ASSUMPTION."""
    per_run = {m.sample_count: m.median_cpu for m in measurements}
    unit = per_run.get(10000) or next(iter(per_run.values()))
    internal = env["nodes"] - env["free_variables"]
    singles = 2 * internal  # each internal node forced ON or OFF
    pairs = singles * (singles - 1) // 2
    factors = {
        "pairwise_perturbations": {
            "value": pairs,
            "basis": f"DERIVED from the model: {internal} internal (non-input) "
            f"nodes, each forcible ON or OFF, give {singles} single perturbations "
            f"and {singles}*{singles - 1}/2 = {pairs} unordered pairs. It remains "
            "a PLANNING ASSUMPTION that pairs are screened at all; nothing in the "
            "funded work plan commits to it.",
        },
        "scenarios": {
            "value": env["scenarios"],
            "basis": "MEASURED from the model: one variant per hypothesis family.",
        },
        "rate_sets": {
            "value": 1000,
            "basis": "PLANNING ASSUMPTION. The committed ensemble uses 30; 1000 is "
            "a uncertainty-quantification target, not a current practice.",
        },
        "donors": {
            "value": 30,
            "basis": "PLANNING ASSUMPTION for per-donor parameterisation. The "
            "funded plan names 5 G1 donors for WP2 and 21 chips for RNA-seq.",
        },
        "campaigns_per_project": {
            "value": 4,
            "basis": "PLANNING ASSUMPTION: one full recomputation per major model "
            "revision over four years.",
        },
    }
    runs = 1
    for f in factors.values():
        runs *= int(f["value"])
    cpu_hours = runs * unit / 3600.0
    return {
        "unit_cpu_seconds_per_condition_run": round(unit, 6),
        "unit_basis": "MEASURED: median CPU seconds for one 3-phase condition at "
        "10,000 trajectories.",
        "factors": factors,
        "total_condition_runs": runs,
        "extrapolated_cpu_hours": round(cpu_hours, 1),
        "caveats": [
            (
                "Single-condition timing on an otherwise idle machine. Real "
                "campaigns additionally pay model loading, protocol resolution, "
                "result assembly and I/O per batch, and spot-instance retries."
            ),
            (
                "The product of five planning factors is not a measurement. "
                "Changing any one changes the total proportionally."
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
        "per condition run at 10,000 trajectories (measured).\n\n"
    )
    lines.append("| Factor | Value | Basis |\n|---|---|---|\n")
    for name, f in extrapolation["factors"].items():
        lines.append(f"| `{name}` | {f['value']:,} | {f['basis']} |\n")
    lines.append(
        f"\n**Product: {extrapolation['total_condition_runs']:,} condition runs ≈ "
        f"{extrapolation['extrapolated_cpu_hours']:,.0f} CPU-hours.**\n\n"
    )
    for c in extrapolation["caveats"]:
        lines.append(f"- {c}\n")
    md_path = OUT / "benchmark.md"
    md_path.write_text("".join(lines), encoding="utf-8")
    return json_path, md_path
