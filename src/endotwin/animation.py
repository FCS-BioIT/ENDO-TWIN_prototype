"""Animated network view of an ENDO-TWIN protocol run (README GIF).

Renders committed dynamics tables only (no simulation here). The network panel
colours every node by its simulated P(ON) under the IL-1beta exposure protocol
(default rules); the side panels compare the reference regimen with the two
competing IL-1beta hypotheses. A provenance sidecar binds the input digests.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from PIL import Image

from endotwin.figures import (
    AQUA,
    ASSETS,
    BASELINE,
    BLUE,
    COMPS,
    GRID,
    INK,
    INK_2,
    LAYOUT,
    ORANGE,
    SURFACE,
    TINT,
    _sha,
)
from endotwin.model import dependencies, load_model
from endotwin.paths import ROOT, relative

STRONG = {"epithelium": BLUE, "stroma": ORANGE, "medium": "#3d3c38"}
FRIENDLY = {
    "IN_E2": "E2",
    "IN_PROGESTIN": "Progestin\n(MPA)",
    "IN_cAMP": "cAMP",
    "IN_XAV939": "XAV939",
    "IN_BMPR_INHIBITOR": "BMPR\ninhibitor",
    "IN_IL1B": "IL-1β",
    "E_PGR": "PGR",
    "E_IHH": "IHH",
    "OUT_EPITHELIAL_SECRETORY": "Secretory\n(PAEP)",
    "OUT_EPITHELIAL_PROLIFERATION": "Proliferation\n(Ki67, EdU)",
    "S_PGR": "PGR",
    "S_PKA": "PKA",
    "S_IL1_SIGNALING": "IL-1\nsignalling",
    "S_NR2F2": "NR2F2",
    "S_BMP2": "BMP2\nexpression",
    "S_BMP_SMAD": "BMP/SMAD\n(pSMAD1/5/8)",
    "S_HAND2": "HAND2",
    "S_PARACRINE_MITOGEN": "Paracrine\nmitogen",
    "OUT_STROMAL_DECIDUALIZATION": "Decidualisation\n(PRL, IGFBP-1)",
}
PHASE_LABEL = {
    "basal": "Basal culture",
    "e2_priming": "E2 priming",
    "differentiation_supplemented": "Differentiation (E2 + MPA + cAMP + XAV939) + IL-1β",
}
PANELS = [
    ("OUT_STROMAL_DECIDUALIZATION", "Stromal decidualisation (PRL, IGFBP-1)"),
    (
        "S_BMP_SMAD",
        "BMP/SMAD activity (pSMAD1/5/8): separates the two IL-1β rules",
    ),
    ("OUT_EPITHELIAL_PROLIFERATION", "Epithelial proliferation (Ki67, EdU)"),
    ("OUT_EPITHELIAL_SECRETORY", "Epithelial secretory differentiation (PAEP)"),
]
TRACES = [
    ("reference__default", "Reference regimen", BLUE, "-", 3.0),
    (
        "il1b_exposure__default",
        "IL-1β, acts on decidualisation only (default rule)",
        ORANGE,
        "-",
        2.0,
    ),
    (
        "il1b_exposure__INF_pgr_depletion",
        "IL-1β, also depletes stromal PGR (alternative rule)",
        AQUA,
        (0, (4, 2)),
        2.0,
    ),
]
NETWORK_RUN = "il1b_exposure__default"
SAMPLES_NOTE = "10,000 trajectories, seed 1, unit rates"


def _rgb(hex_colour: str) -> np.ndarray:
    h = hex_colour.lstrip("#")
    return np.array([int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)])


def _mix(c0: str, c1: str, p: float) -> tuple[float, float, float]:
    out = (1 - p) * _rgb(c0) + p * _rgb(c1)
    return tuple(float(v) for v in out)


def _frame_times(bounds: list[tuple[str, float, float]]) -> list[float]:
    """Dense sampling where the network switches, sparse once it has settled."""
    times: list[float] = []
    for _, lo, hi in bounds:
        times += [round(lo + 0.3 * i, 2) for i in range(20)]
        times += [round(t, 2) for t in np.arange(lo + 6.0, hi + 0.05, 2.3)]
    return times


def _on_intervals(frame: pd.DataFrame, column: str) -> list[tuple[float, float]]:
    on = frame[column].to_numpy() > 0.5
    t = frame["time"].to_numpy()
    spans, start = [], None
    for i, flag in enumerate(on):
        if flag and start is None:
            start = t[i]
        if not flag and start is not None:
            spans.append((start, t[i]))
            start = None
    if start is not None:
        spans.append((start, t[-1] + 0.1))
    return spans


def render_animation(version: str) -> Path:
    model = load_model(version)
    res = ROOT / "endotwin" / "results" / version
    inputs = {tag: res / f"dynamics_{tag}.tsv" for tag, *_ in TRACES}
    data = {tag: pd.read_csv(path, sep="\t") for tag, path in inputs.items()}
    net = data[NETWORK_RUN]
    times_all = net["time"].to_numpy()
    bounds = [
        (pid, float(g["time"].min()), float(g["time"].max()))
        for pid, g in net.groupby("phase_id", sort=False)
    ]
    order = [pid for pid, _, _ in bounds]
    t_end = float(times_all[-1]) + 0.1

    fig = plt.figure(figsize=(16, 9), dpi=90)
    fig.patch.set_facecolor(SURFACE)
    title = fig.text(0.012, 0.955, "", fontsize=15, weight="bold", color=INK)
    fig.text(
        0.012,
        0.922,
        f"model {version}  ·  protocol il1b_exposure  ·  {SAMPLES_NOTE}  ·  "
        "network panel: default rules, IL-1β run",
        fontsize=9.5,
        color=INK_2,
    )

    # -- network panel --------------------------------------------------------
    ax = fig.add_axes((0.008, 0.115, 0.585, 0.78))
    ax.set_facecolor(SURFACE)
    ax.axis("off")
    ax.set_xlim(-0.4, 13.4)
    ax.set_ylim(-0.75, 6.75)
    for x0, w, fc, ec, text in (
        (-0.2, 5.0, "#f4f8fd", BLUE, "Epithelium (organoid-derived)"),
        (5.0, 8.2, "#fdf6f2", ORANGE, "Stroma (primary stromal cells)"),
    ):
        ax.add_patch(
            FancyBboxPatch(
                (x0, -0.45),
                w,
                5.6,
                boxstyle="round,pad=0.02",
                fc=fc,
                ec=ec,
                lw=0.9,
            )
        )
        ax.text(x0 + 0.2, -0.3, text, color=ec, fontsize=10, weight="bold")
    ax.text(
        -0.2,
        6.55,
        "Culture medium: protocol inputs and perturbations",
        color=INK_2,
        fontsize=10,
        weight="bold",
    )
    edges = []
    px_per_unit = ax.transData.transform((1, 1)) - ax.transData.transform((0, 0))
    half_w, half_h = 0.83 * px_per_unit[0], 0.40 * px_per_unit[1]

    def _clearance(dx: float, dy: float) -> float:
        # Points from a box centre to its border along (dx, dy), plus a small gap.
        ux, uy = abs(dx) * px_per_unit[0], abs(dy) * px_per_unit[1]
        norm = float(np.hypot(ux, uy)) or 1.0
        ux, uy = ux / norm, uy / norm
        reach = min(half_w / ux if ux else np.inf, half_h / uy if uy else np.inf)
        return (reach + 3.0) * 72.0 / fig.dpi

    for (src, tgt), sign in dependencies(model.rules).items():
        x0, y0 = LAYOUT[src]
        x1, y1 = LAYOUT[tgt]
        clearance = _clearance(x1 - x0, y1 - y0)
        crossing = (
            model.compartment(src) in COMPS
            and model.compartment(tgt) in COMPS
            and model.compartment(src) != model.compartment(tgt)
        )
        ann = ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops={
                "arrowstyle": "-|>" if sign == "activation" else "-[",
                "color": INK if crossing else INK_2,
                "lw": 2.0 if crossing else 1.1,
                "shrinkA": clearance,
                "shrinkB": clearance,
                "mutation_scale": 11,
                "connectionstyle": "arc3,rad=0.06",
            },
            zorder=1,
        )
        edges.append((src, ann))
    boxes = {}
    for node, (x, y) in LAYOUT.items():
        comp = model.compartment(node)
        is_out = model.node_info[node]["layer"] == "functional_output"
        patch = FancyBboxPatch(
            (x - 0.8, y - 0.37),
            1.6,
            0.74,
            boxstyle="round,pad=0.03",
            fc=TINT[comp],
            ec=STRONG[comp],
            lw=2.6 if is_out else 1.1,
            linestyle="--" if node == "IN_XAV939" else "-",
            zorder=2,
        )
        ax.add_patch(patch)
        label = ax.text(
            x, y, "", ha="center", va="center", fontsize=8, color=INK, zorder=3
        )
        boxes[node] = (comp, patch, label)
    ax.text(
        -0.2,
        -0.72,
        "Node fill = fraction of simulated trajectories with the node ON (pale 0, saturated 1). Arrow = activation, "
        "bar = inhibition;\nheavy arrows cross compartments; edge opacity follows the regulator's P(ON). Heavy box = "
        "functional output with its readout. Dashed = XAV939, read by no rule.",
        fontsize=7.6,
        color=INK_2,
        va="top",
    )

    # -- side panels ----------------------------------------------------------
    left, width, top, gap = 0.635, 0.35, 0.895, 0.022
    timeline_h, panel_h = 0.085, 0.13
    tl = fig.add_axes((left, top - timeline_h, width, timeline_h))
    rows = [
        ("E2", "IN_E2", INK_2),
        ("MPA + cAMP + XAV939", "IN_PROGESTIN", INK_2),
        ("IL-1β (perturbation)", "IN_IL1B", ORANGE),
    ]
    for i, (name, column, colour) in enumerate(rows):
        y = len(rows) - 1 - i
        for a, b in _on_intervals(net, column):
            tl.add_patch(plt.Rectangle((a, y - 0.32), b - a, 0.64, color=colour, lw=0))
        tl.text(0.6, y, name, ha="left", va="center", fontsize=8, color=INK_2)
    tl.set_xlim(0, t_end)
    tl.set_ylim(-0.6, len(rows) - 0.4)
    tl.set_yticks([])
    tl.set_xticks([])
    for side in tl.spines.values():
        side.set_visible(False)
    clock = tl.set_title("", fontsize=9, color=INK, loc="left", pad=3)
    cursors = [tl.axvline(0, color=INK, lw=1.2)]
    revealed = []
    y0 = top - timeline_h - gap - 0.012
    axes = []
    for k, (node, heading) in enumerate(PANELS):
        pax = fig.add_axes((left, y0 - (k + 1) * panel_h - k * gap, width, panel_h))
        axes.append(pax)
        pax.set_facecolor(SURFACE)
        for side in ("top", "right"):
            pax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            pax.spines[side].set_color(BASELINE)
        pax.tick_params(colors=INK_2, labelsize=7.5)
        pax.yaxis.grid(True, color=GRID, linewidth=0.6)
        pax.set_axisbelow(True)
        pax.set_xlim(0, t_end)
        pax.set_ylim(-0.05, 1.08)
        pax.set_yticks([0, 0.5, 1])
        pax.set_ylabel("P(ON)", fontsize=7.5, color=INK_2)
        for _, lo, _ in bounds[1:]:
            pax.axvline(lo, color=BASELINE, lw=0.8, ls=":")
        pax.set_title(heading, fontsize=9, color=INK, loc="left", pad=3)
        if k < len(PANELS) - 1:
            pax.set_xticklabels([])
        for tag, name, colour, style, lw in TRACES:
            frame = data[tag]
            pax.plot(
                frame["time"], frame[node], color=colour, lw=lw, ls=style, alpha=0.13
            )
            (line,) = pax.plot([], [], color=colour, lw=lw, ls=style, label=name)
            revealed.append((line, frame, node))
        cursors.append(pax.axvline(0, color=INK, lw=1.0))
    axes[-1].set_xlabel(
        "MaBoSS time (dimensionless; not mapped to hours or days)",
        fontsize=8,
        color=INK_2,
    )
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower left",
        bbox_to_anchor=(left - 0.005, 0.008),
        ncol=1,
        frameon=False,
        fontsize=8.3,
    )
    fig.text(
        0.012,
        0.012,
        "Model predictions, not observations. IL-1β wiring is provisional (two competing rules). "
        "Probabilities are trajectory frequencies, not concentrations.",
        fontsize=7.6,
        color=INK_2,
    )

    # -- frames ---------------------------------------------------------------
    frames: list[Image.Image] = []
    durations: list[int] = []
    times = _frame_times(bounds)
    phase_starts = {round(lo, 2) for _, lo, _ in bounds}
    for t in times:
        idx = int(np.searchsorted(times_all, t + 1e-9, side="right") - 1)
        row = net.iloc[max(idx, 0)]
        phase = row["phase_id"]
        k = order.index(phase) + 1
        title.set_text(f"Phase {k}/{len(order)}   {PHASE_LABEL.get(phase, phase)}")
        clock.set_text(
            f"Protocol (inputs are set, not simulated)     MaBoSS time {t:4.1f}"
        )
        for node, (comp, patch, label) in boxes.items():
            p = float(row[node])
            patch.set_facecolor(_mix(TINT[comp], STRONG[comp], p))
            if node.startswith("IN_"):
                text = f"{FRIENDLY[node]}\n{'ON' if p > 0.5 else 'off'}"
            else:
                text = f"{FRIENDLY[node]}\n{p:.2f}"
            label.set_text(text)
            label.set_color("white" if p > 0.55 else INK)
            label.set_weight("bold" if p > 0.55 else "normal")
        for src, ann in edges:
            ann.arrow_patch.set_alpha(0.18 + 0.82 * float(row[src]))
        for line, frame, node in revealed:
            shown = frame[frame["time"] <= t + 1e-9]
            line.set_data(shown["time"], shown[node])
        for c in cursors:
            c.set_xdata([t, t])
        fig.canvas.draw()
        rgba = np.asarray(fig.canvas.buffer_rgba())
        frames.append(Image.fromarray(rgba[..., :3].copy()))
        durations.append(110)
    for i, t in enumerate(times[1:], start=0):
        if round(t, 2) in phase_starts:
            durations[i] = 1000  # pause on the settled state before the next phase
    durations[-1] = 2600
    plt.close(fig)

    sample = [frames[i] for i in np.linspace(0, len(frames) - 1, 8).astype(int)]
    montage = Image.new("RGB", (sample[0].width, sample[0].height * len(sample)))
    for i, im in enumerate(sample):
        montage.paste(im, (0, i * im.height))
    palette = montage.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    quantized = [
        im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames
    ]
    ASSETS.mkdir(parents=True, exist_ok=True)
    tag = version.split("-")[-1]
    out = ASSETS / f"endotwin_pathway_dynamics_{tag}.gif"
    quantized[0].save(
        out,
        save_all=True,
        append_images=quantized[1:],
        duration=durations,
        loop=0,
        disposal=1,
        optimize=False,
    )
    sources = [
        *inputs.values(),
        model.root / "network.bnd",
        model.root / "node_dictionary.tsv",
    ]
    sidecar = {
        "figure": relative(out),
        "inputs_sha256": {relative(p): _sha(p) for p in sources},
        "regenerate": "pixi run endotwin-figures",
        "model_version": version,
        "content": (
            "Network panel: P(ON) of every node through basal, E2 priming and "
            "differentiation with IL-1beta (default rules). Side panels: reference regimen "
            "and the two competing IL-1beta rules."
        ),
        "simulation": f"{SAMPLES_NOTE}, joint state carried across phases",
        "frames": len(frames),
        "main_result": (
            "Both IL-1beta rules abolish decidualisation; only the PGR-depletion rule also "
            "abolishes pSMAD1/5/8 (and, under the default Q2 relay, restores epithelial "
            "proliferation)."
        ),
        "limitations": (
            "Model predictions, not observations. IL-1beta wiring is provisional. Time is "
            "dimensionless; node fill is a trajectory frequency, not a concentration."
        ),
    }
    (ASSETS / f"endotwin_pathway_dynamics_{tag}_provenance.json").write_text(
        json.dumps(sidecar, indent=2, sort_keys=True) + "\n"
    )
    return out


if __name__ == "__main__":
    import sys

    print(
        relative(
            render_animation(sys.argv[1] if len(sys.argv) > 1 else "endotwin-v0.1.0")
        )
    )
