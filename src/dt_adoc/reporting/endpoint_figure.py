"""Functional adhesion endpoint: ADOC observation versus MaBoSS simulation.

Reads only tracked artifacts -- ``docs/endpoint/endpoint_replicates.tsv`` and
``docs/endpoint/endpoint_run_settings.json`` written by
``endpoint_replicates.build_endpoint_replicates`` -- and never runs MaBoSS, so a
render is cheap and deterministic and every plotted number traces to a row.

Two uncertainties appear, and they are never drawn as if they meant the same
thing:

* **Observed** -- attached / challenged blastocysts, with a Wilson 95% score
  interval on the per-embryo proportion. That is correct for counting embryos
  (``docs/maboss_estimator_semantics.md`` §3d). It is *not* a donor- or
  chip-level interval: embryos share chips, chips can share donors, and the
  embryo-to-chip/donor mapping is not recoverable (``config/adoc_chip_donor_provenance.tsv``).
* **Simulated** -- the mean of R complete MaBoSS lineages on disjoint seed
  blocks, with +/- 1 SD across those runs. That SD is the run-to-run
  reproducibility of the simulator's occupancy estimator, nothing more: not
  experimental, biological or structural uncertainty, not an i.i.d. Monte Carlo
  SE, and not MaBoSS's node error column. At figure scale it is invisible, which
  is itself the finding, so panel B magnifies it.

The derived summary is written to ``docs/endpoint/endpoint_figure_source_data.tsv``
so captions and the README can cite numbers that a test recomputes from the
replicate rows.
"""

from __future__ import annotations

import csv
import hashlib
import json
import textwrap
from pathlib import Path
from statistics import mean, stdev
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from dt_adoc.concordance.figure import wilson_interval
from dt_adoc.reporting.endpoint_replicates import (
    ENDPOINT_ARMS,
    ENDPOINT_NODE,
    HORIZON_CLASSES,
    REPLICATES_TSV,
    RUN_SETTINGS_JSON,
)

SOURCE_DATA_TSV = Path("docs/endpoint/endpoint_figure_source_data.tsv")
FIGURE_PATH = Path("docs/assets/adoc_functional_endpoint_v0.5.0.png")

SURFACE = "#FCFCFB"
INK = "#0B0B0B"
INK_2 = "#52514E"
INK_3 = "#8A8984"
GRID = "#E6E5E0"
OBSERVED = "#0B0B0B"
CONVERGED = "#2A78D6"
DECLARED = "#EB6834"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


SOURCE_COLUMNS = (
    "arm_id",
    "series",
    "value",
    "interval_low",
    "interval_high",
    "interval_kind",
    "n",
    "evidence_role",
    "note",
)


def load_replicates(root: Path) -> dict[tuple[str, str], list[float]]:
    """Endpoint value per (arm, horizon), in replicate order."""
    values: dict[tuple[str, str], list[tuple[int, float]]] = {}
    with (root / REPLICATES_TSV).open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["node_id"] != ENDPOINT_NODE:
                continue
            values.setdefault((row["arm_id"], row["horizon_class"]), []).append(
                (int(row["replicate"]), float(row["value"]))
            )
    return {k: [v for _r, v in sorted(rows)] for k, rows in values.items()}


def _role_label(observed: dict[str, Any]) -> str:
    if observed["role"] == "calibration":
        return "designated calibration\n(magnitude NOT fitted)"
    return "held out"


def build_source_data(root: Path) -> list[dict[str, str]]:
    """Every plotted quantity, one row each."""
    settings = json.loads((root / RUN_SETTINGS_JSON).read_text(encoding="utf-8"))
    replicates = load_replicates(root)
    rows: list[dict[str, str]] = []
    for arm_id, _protocol, _label in ENDPOINT_ARMS:
        observed = settings["observed"][arm_id]
        k, n = observed["successes"], observed["trials"]
        low, high = wilson_interval(k, n)
        rows.append(
            {
                "arm_id": arm_id,
                "series": "observed",
                "value": f"{k / n:.6f}",
                "interval_low": f"{low:.6f}",
                "interval_high": f"{high:.6f}",
                "interval_kind": "Wilson 95% score interval, per-embryo proportion",
                "n": f"{k}/{n} embryos",
                "evidence_role": observed["role"],
                "note": "embryos are not independent donors or chips; embryo-to-chip/donor mapping not recoverable",
            }
        )
        for horizon in HORIZON_CLASSES:
            values = replicates[(arm_id, horizon)]
            centre = mean(values)
            spread = stdev(values) if len(values) > 1 else 0.0
            rows.append(
                {
                    "arm_id": arm_id,
                    "series": f"simulated_{horizon}",
                    "value": f"{centre:.8f}",
                    "interval_low": f"{centre - spread:.8f}",
                    "interval_high": f"{centre + spread:.8f}",
                    "interval_kind": "mean +/- 1 SD across complete runs on seed blocks disjoint between replicate indices, reused across arms and horizons (simulator reproducibility only)",
                    "n": f"{len(values)} runs x {settings['trajectory_count']} trajectories",
                    "evidence_role": observed["role"],
                    "note": f"sd={spread:.3g}; min={min(values):.8f}; max={max(values):.8f}",
                }
            )
        rows.append(
            {
                "arm_id": arm_id,
                "series": "exact_converged",
                "value": f"{settings['exact_converged'][arm_id]['exact_converged_value']:.8f}",
                "interval_low": "",
                "interval_high": "",
                "interval_kind": "exact: prior-weighted enumeration of the fixed point over the latent free variables",
                "n": f"{2 ** len(settings['exact_converged'][arm_id]['latent_free_variables'])} latent assignments",
                "evidence_role": observed["role"],
                "note": "a property of the model and baseline.cfg priors, not an estimate",
            }
        )
    return rows


def write_source_data(root: Path, rows: list[dict[str, str]]) -> Path:
    destination = root / SOURCE_DATA_TSV
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=SOURCE_COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    return destination


def render_endpoint_figure(root: Path | None = None) -> dict[str, Any]:
    from dt_adoc.model.provenance import repo_root

    active_root = root or repo_root()
    settings = json.loads((active_root / RUN_SETTINGS_JSON).read_text(encoding="utf-8"))
    rows = build_source_data(active_root)
    source_path = write_source_data(active_root, rows)
    by = {(r["arm_id"], r["series"]): r for r in rows}
    replicates = load_replicates(active_root)
    R = settings["replicates"]

    plt.rcParams.update({"font.size": 10})
    figure = plt.figure(figsize=(13.5, 7.6), dpi=150, facecolor=SURFACE)
    axis = figure.add_axes((0.065, 0.30, 0.52, 0.54))
    zoom = figure.add_axes((0.67, 0.30, 0.31, 0.54))
    for ax in (axis, zoom):
        ax.set_facecolor(SURFACE)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(INK_3)
        ax.tick_params(colors=INK_2)

    offsets = {
        "observed": -0.22,
        "simulated_converged": 0.0,
        "simulated_declared": 0.22,
    }
    styles = {
        "observed": {"marker": "o", "color": OBSERVED, "mfc": OBSERVED},
        "simulated_converged": {"marker": "s", "color": CONVERGED, "mfc": CONVERGED},
        "simulated_declared": {"marker": "^", "color": DECLARED, "mfc": SURFACE},
    }
    for index, (arm_id, _protocol, label) in enumerate(ENDPOINT_ARMS):
        for series, dx in offsets.items():
            row = by[(arm_id, series)]
            value = float(row["value"])
            low, high = float(row["interval_low"]), float(row["interval_high"])
            style = styles[series]
            axis.errorbar(
                index + dx,
                value,
                yerr=[[value - low], [high - value]],
                fmt=style["marker"],
                color=style["color"],
                mfc=style["mfc"],
                mec=style["color"],
                ms=8,
                mew=1.6,
                elinewidth=1.6,
                capsize=4,
                zorder=3,
            )
            text = (
                f"{row['n'].split(' ')[0]}\n{value:.2f}"
                if series == "observed"
                else f"{value:.4f}"
            )
            axis.annotate(
                text,
                (index + dx, high if series == "observed" else value),
                xytext=(0, 7),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color=INK_2,
            )
        exact = float(by[(arm_id, "exact_converged")]["value"])
        axis.plot(
            [index - 0.08, index + 0.08],
            [exact, exact],
            color=CONVERGED,
            lw=1.0,
            ls=":",
            zorder=2,
        )
    axis.set_xticks(
        range(len(ENDPOINT_ARMS)),
        [
            f"{label}\n{_role_label(settings['observed'][arm_id])}"
            for arm_id, _p, label in ENDPOINT_ARMS
        ],
        fontsize=9,
    )
    axis.set_ylim(-0.04, 1.08)
    axis.set_xlim(-0.55, len(ENDPOINT_ARMS) - 0.45)
    axis.set_ylabel(
        "Stable adhesion\n(observed proportion  |  simulated P(node = ON))", color=INK_2
    )
    axis.yaxis.grid(True, color=GRID, lw=0.8)
    axis.set_axisbelow(True)
    axis.set_title(
        "A   Functional endpoint", loc="left", fontsize=12, fontweight="bold", color=INK
    )

    # Panel B: the run-to-run spread, magnified. Converged runs as deviation
    # from the exact enumerated value; declared runs as raw values.
    scale = 1e4
    positions: list[float] = []
    labels: list[str] = []
    for index, (arm_id, _protocol, label) in enumerate(ENDPOINT_ARMS):
        exact = float(by[(arm_id, "exact_converged")]["value"])
        for j, horizon in enumerate(HORIZON_CLASSES):
            values = replicates[(arm_id, horizon)]
            reference = exact if horizon == "converged" else 0.0
            deltas = [(v - reference) * scale for v in values]
            x = index * 2.6 + j
            positions.append(x)
            labels.append(
                f"{label.split(' +')[0].replace('Hormone-treated', 'HT')}{' + mife' if '+' in label else ''}\n{horizon}"
            )
            jitter = [((k * 37) % 17 - 8) / 40 for k in range(len(deltas))]
            color = CONVERGED if horizon == "converged" else DECLARED
            zoom.scatter(
                [x + d for d in jitter],
                deltas,
                s=10,
                color=color,
                alpha=0.55,
                edgecolors="none",
                zorder=2,
            )
            centre = mean(deltas)
            spread = stdev(deltas) if len(deltas) > 1 else 0.0
            zoom.errorbar(
                x + 0.42,
                centre,
                yerr=spread,
                fmt="_",
                color=INK,
                ms=10,
                capsize=3,
                lw=1.2,
                zorder=3,
            )
    zoom.axhline(0, color=INK_3, lw=0.8, zorder=1)
    zoom.set_xticks(positions, labels, fontsize=7.2)
    zoom.set_ylabel(
        "converged: run − exact value  |  declared: run value\n(× 10⁻⁴ absolute probability)",
        color=INK_2,
        fontsize=8.5,
    )
    zoom.yaxis.grid(True, color=GRID, lw=0.8)
    zoom.set_axisbelow(True)
    zoom.set_title(
        f"B   Run-to-run spread, {R} runs",
        loc="left",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )

    handles = [
        Line2D(
            [],
            [],
            marker="o",
            color=OBSERVED,
            ls="none",
            ms=8,
            label="ADOC observed: attached / challenged embryos; bar = Wilson 95% CI on the per-embryo proportion",
        ),
        Line2D(
            [],
            [],
            marker="s",
            color=CONVERGED,
            ls="none",
            ms=8,
            label=f"MaBoSS, converged horizon (phases run to fixed point): mean of {R} runs; bar = ±1 SD across runs",
        ),
        Line2D(
            [],
            [],
            marker="^",
            color=DECLARED,
            mfc=SURFACE,
            ls="none",
            ms=8,
            mew=1.6,
            label=f"MaBoSS, declared horizon (config/protocols.yaml durations, ~4000× shorter than the time to the fixed point): mean of {R} runs; ±1 SD",
        ),
        Line2D(
            [],
            [],
            color=CONVERGED,
            ls=":",
            lw=1.2,
            label="exact converged value by enumeration over the model's latent free variables",
        ),
    ]
    figure.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.055, 0.105),
        frameon=False,
        fontsize=8.6,
    )
    ht_exact = float(by[("hormone_treated", "exact_converged")]["value"])
    notes = (
        f"The two uncertainties are different kinds and are not comparable. The simulated SD is run-to-run reproducibility of the MaBoSS occupancy estimator on seed blocks disjoint between replicate indices and reused across arms and horizons (a paired design) "
        f"(seed_r = 1 + r·{settings['trajectory_count']}, {settings['trajectory_count']} trajectories each): not biological, experimental or model-structure uncertainty,\n"
        "not an i.i.d. Monte Carlo SE (MaBoSS's per-trajectory seeding makes the initial-state draw stratified), and not MaBoSS's node error column. "
        f"The converged hormone-treated value {ht_exact:.2f} = 1 − (1 − 0.70)(1 − 0.40) is set by two hand-typed relay priors in baseline.cfg;\n"
        "adhesion magnitude is not fitted (config/calibration.yaml: diagnostic_ordinal). Only the ordering untreated < hormone-treated > mifepristone is claimed. "
        "Observed intervals ignore chip/donor clustering, which cannot be reconstructed. MaBoSS time is dimensionless."
    )
    figure.text(
        0.055,
        0.012,
        "\n".join(textwrap.wrap(" ".join(notes.split()), 205)),
        fontsize=7.4,
        color=INK_2,
        va="bottom",
    )
    identity = (
        "byte-identical to " + settings["parent_model_version"]
        if settings["executable_identical_to_parent"]
        else "DIFFERS from " + settings["parent_model_version"]
    )
    figure.text(
        0.055,
        0.955,
        "Stable embryo adhesion: ADOC observation vs MaBoSS simulation",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    figure.text(
        0.055,
        0.940,
        f"{settings['model_version']} (v0.5 scaffold; executable model {identity})\n"
        f"{R} complete runs × {settings['trajectory_count']:,} trajectories per arm and "
        "horizon · exploratory, not validation",
        fontsize=9.5,
        color=INK_2,
        va="top",
        linespacing=1.4,
    )
    target = active_root / FIGURE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target, dpi=150, facecolor=SURFACE, metadata={"Software": None})
    plt.close(figure)

    metadata = {
        "schema_version": "1.0",
        "artifact": "adoc_functional_endpoint",
        "model_version": settings["model_version"],
        "executable_identical_to_parent": settings["executable_identical_to_parent"],
        "parent_model_version": settings["parent_model_version"],
        "replicates": R,
        "trajectory_count": settings["trajectory_count"],
        "seeds": settings["seeds"],
        "converged_phase_horizon": settings["converged_phase_horizon"],
        "run_settings": str(RUN_SETTINGS_JSON),
        "run_settings_sha256": sha(active_root / RUN_SETTINGS_JSON),
        "replicates_tsv": str(REPLICATES_TSV),
        "replicates_tsv_sha256": sha(active_root / REPLICATES_TSV),
        "source_data": str(SOURCE_DATA_TSV),
        "source_data_sha256": sha(source_path),
        "renderer_sha256": sha(
            active_root / "src/dt_adoc/reporting/endpoint_figure.py"
        ),
        "run_provenance": settings["provenance"],
        "figure": {"path": str(FIGURE_PATH), "sha256": sha(target)},
    }
    sidecar = target.with_name(target.stem + "_metadata.json")
    sidecar.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    metadata = render_endpoint_figure()
    print(f"figure   {metadata['figure']['path']}  {metadata['figure']['sha256'][:12]}")
    print(f"source   {metadata['source_data']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
