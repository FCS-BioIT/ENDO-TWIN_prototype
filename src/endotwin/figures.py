"""Figures for the README and docs, each with a provenance sidecar.

Every figure is rendered from committed result tables (no simulation here) and
writes ``<name>_provenance.json`` beside it with the SHA-256 of its inputs and
the command that regenerates it.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from endotwin.model import dependencies, load_model
from endotwin.paths import ASSETS, ROOT, relative

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"  # categorical slot 1
ORANGE = "#eb6834"  # categorical slot 2
AQUA = "#1baf7a"  # categorical slot 3
YELLOW = "#eda100"  # categorical slot 4
TINT = {"epithelium": "#e3eefb", "stroma": "#fbe7de", "medium": "#efeeea"}
EDGE = {"epithelium": BLUE, "stroma": ORANGE, "medium": MUTED}


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASELINE)
    ax.tick_params(colors=INK_2, labelsize=8)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(fig, name: str, inputs: list[Path], meta: dict[str, object]) -> Path:
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / f"{name}.png"
    fig.savefig(
        out,
        dpi=160,
        facecolor=SURFACE,
        metadata={"Software": None},
        bbox_inches="tight",
        pad_inches=0.15,
    )
    plt.close(fig)
    sidecar = {
        "figure": relative(out),
        "inputs_sha256": {relative(p): _sha(p) for p in inputs},
        "regenerate": "pixi run endotwin-figures",
        **meta,
    }
    (ASSETS / f"{name}_provenance.json").write_text(
        json.dumps(sidecar, indent=2, sort_keys=True) + "\n"
    )
    return out


def _tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


# -- 1. network ---------------------------------------------------------------

LAYOUT = {
    "IN_E2": (0.9, 6.0),
    "IN_PROGESTIN": (3.2, 6.0),
    "IN_cAMP": (5.5, 6.0),
    "IN_XAV939": (7.6, 6.0),
    "IN_BMPR_INHIBITOR": (9.8, 6.0),
    "IN_IL1B": (12.0, 6.0),
    "E_PGR": (1.6, 4.5),
    "E_IHH": (3.4, 3.2),
    "OUT_EPITHELIAL_SECRETORY": (1.3, 1.6),
    "OUT_EPITHELIAL_PROLIFERATION": (3.7, 0.4),
    "S_PGR": (6.4, 4.5),
    "S_PKA": (8.6, 4.5),
    "S_IL1_SIGNALING": (12.0, 4.5),
    "S_NR2F2": (6.2, 3.2),
    "S_BMP2": (8.4, 3.2),
    "S_BMP_SMAD": (10.4, 3.2),
    "S_HAND2": (8.2, 1.9),
    "S_PARACRINE_MITOGEN": (6.4, 0.9),
    "OUT_STROMAL_DECIDUALIZATION": (11.2, 1.6),
}
LABEL = {
    "IN_BMPR_INHIBITOR": "IN_BMPR_\nINHIBITOR",
    "OUT_EPITHELIAL_SECRETORY": "OUT_EPITHELIAL_\nSECRETORY",
    "OUT_EPITHELIAL_PROLIFERATION": "OUT_EPITHELIAL_\nPROLIFERATION",
    "S_PARACRINE_MITOGEN": "S_PARACRINE_\nMITOGEN",
    "OUT_STROMAL_DECIDUALIZATION": "OUT_STROMAL_\nDECIDUALIZATION",
    "S_IL1_SIGNALING": "S_IL1_\nSIGNALING",
}


def network_figure(version: str) -> Path:
    model = load_model(version)
    deps = dependencies(model.rules)
    fig, ax = plt.subplots(figsize=(11.5, 6.6))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.axis("off")
    ax.set_xlim(-0.4, 13.4)
    ax.set_ylim(-0.95, 6.9)
    ax.add_patch(
        FancyBboxPatch(
            (-0.2, -0.4),
            5.0,
            5.55,
            boxstyle="round,pad=0.02",
            fc="#f4f8fd",
            ec=BLUE,
            lw=0.8,
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (5.0, -0.4),
            8.2,
            5.55,
            boxstyle="round,pad=0.02",
            fc="#fdf6f2",
            ec=ORANGE,
            lw=0.8,
        )
    )
    ax.text(
        0.0, 5.0, "Epithelium (organoid-derived)", color=BLUE, fontsize=9, weight="bold"
    )
    ax.text(
        5.2,
        5.0,
        "Stroma (primary stromal cells)",
        color=ORANGE,
        fontsize=9,
        weight="bold",
    )
    ax.text(
        0.0,
        6.65,
        "Experimental inputs (culture medium)",
        color=INK_2,
        fontsize=9,
        weight="bold",
    )
    new = {
        n
        for n, info in model.node_info.items()
        if info["lineage_change"]
        in {"new", "renamed", "merged_and_renamed", "modified"}
    }
    for (src, tgt), sign in deps.items():
        x0, y0 = LAYOUT[src]
        x1, y1 = LAYOUT[tgt]
        crossing = (
            model.compartment(src) in COMPS
            and model.compartment(tgt) in COMPS
            and model.compartment(src) != model.compartment(tgt)
        )
        style = "-|>" if sign == "activation" else "-["
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops={
                "arrowstyle": style,
                "color": INK if crossing else INK_2,
                "lw": 1.6 if crossing else 0.9,
                "shrinkA": 17,
                "shrinkB": 19,
                "mutation_scale": 9,
                "connectionstyle": "arc3,rad=0.06",
                "linestyle": "-",
            },
        )
    for node, (x, y) in LAYOUT.items():
        comp = model.compartment(node)
        is_out = model.node_info[node]["layer"] == "functional_output"
        ax.add_patch(
            FancyBboxPatch(
                (x - 0.78, y - 0.3),
                1.56,
                0.6,
                boxstyle="round,pad=0.03",
                fc=TINT[comp],
                ec=EDGE[comp],
                lw=2.2 if is_out else 1.0,
                linestyle="--" if node == "IN_XAV939" else "-",
            )
        )
        ax.text(
            x,
            y,
            LABEL.get(node, node),
            ha="center",
            va="center",
            fontsize=6.4,
            color=INK,
            weight="bold" if node in new else "normal",
        )
        readouts = model.node_info[node]["readouts"]
        if readouts:
            ax.text(
                x,
                y - 0.43,
                readouts.replace(";", ", "),
                ha="center",
                va="top",
                fontsize=6.4,
                color=INK_2,
                style="italic",
            )
    ax.text(
        -0.2,
        -0.88,
        "Arrowhead = activation, bar = inhibition; bold arrows cross compartments. Heavy border = functional output (readouts in italics).\n"
        "Bold label = new or changed vs prototype v0.6.0. Dashed box = IN_XAV939, declared but read by no rule.",
        fontsize=6.6,
        color=INK_2,
    )
    return _save(
        fig,
        f"endotwin_network_{version.split('-')[-1]}",
        [model.root / "network.bnd", model.root / "node_dictionary.tsv"],
        {
            "model_version": version,
            "content": "default rules of the executable network (no simulation)",
            "limitations": "Default variant of each hypothesis family only; alternatives are in rule_variants.tsv.",
        },
    )


COMPS = {"epithelium", "stroma"}


# -- 2. dynamics --------------------------------------------------------------


def _phase_bounds(rows: list[dict[str, str]]) -> list[tuple[str, float, float]]:
    bounds: dict[str, list[float]] = {}
    for r in rows:
        bounds.setdefault(r["phase_id"], []).append(float(r["time"]))
    return [(p, min(v), max(v)) for p, v in bounds.items()]


def dynamics_figure(version: str) -> Path:
    res = ROOT / "endotwin" / "results" / version
    ref = _tsv(res / "dynamics_reference__default.tsv")
    bmp = _tsv(res / "dynamics_bmpr_inhibition__default.tsv")
    bmp_alt = _tsv(res / "dynamics_bmpr_inhibition__Q1_pgr_sufficient.tsv")
    panels = [
        ("OUT_EPITHELIAL_PROLIFERATION", "Epithelial proliferation (Ki67/EdU)"),
        ("OUT_EPITHELIAL_SECRETORY", "Epithelial secretory differentiation (PAEP)"),
        ("OUT_STROMAL_DECIDUALIZATION", "Stromal decidualisation (PRL, IGFBP-1)"),
        ("S_BMP_SMAD", "BMP/SMAD1/5/8 activity (pSMAD1/5/8)"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.2), sharex=True)
    fig.patch.set_facecolor(SURFACE)
    t_ref = [float(r["time"]) for r in ref]
    for ax, (node, title) in zip(axes.flat, panels, strict=True):
        _style(ax)
        for phase, lo, hi in _phase_bounds(ref)[1:]:
            ax.axvline(lo, color=BASELINE, lw=0.8, ls=":")
        ax.plot(
            t_ref,
            [float(r[node]) for r in ref],
            color=BLUE,
            lw=2,
            label="reference regimen",
        )
        ax.plot(
            t_ref,
            [float(r[node]) for r in bmp],
            color=ORANGE,
            lw=2,
            label="BMPR inhibition, H1 BMP-required",
        )
        if node == "OUT_STROMAL_DECIDUALIZATION":
            ax.plot(
                t_ref,
                [float(r[node]) for r in bmp_alt],
                color=AQUA,
                lw=2,
                ls="--",
                label="BMPR inhibition, H1 PGR-sufficient (equals its own reference)",
            )
        ax.set_title(title, fontsize=9, color=INK, loc="left")
        ax.set_ylim(-0.04, 1.06)
        ax.set_ylabel("P(node ON)", fontsize=8, color=INK_2)
    for ax in axes[1]:
        ax.set_xlabel(
            "MaBoSS time (dimensionless; not mapped to days)", fontsize=8, color=INK_2
        )
    phases = ", ".join(
        f"{p.replace('_', ' ')} ({lo:.0f}-{hi:.0f})" for p, lo, hi in _phase_bounds(ref)
    )
    fig.suptitle(
        f"endotwin-v0.1.0 protocol phases: {phases}",
        fontsize=8.5,
        color=INK_2,
        x=0.01,
        ha="left",
    )
    for ax in (axes[0][0], axes[0][1]):
        ax.text(
            0.02,
            0.5,
            "BMPR inhibition: no predicted effect\n(lines overlap)",
            transform=ax.transAxes,
            fontsize=7.5,
            color=INK_2,
        )
    handles, labels = axes[1][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0.06, 1, 0.97))
    return _save(
        fig,
        f"endotwin_dynamics_{version.split('-')[-1]}",
        [
            res / "dynamics_reference__default.tsv",
            res / "dynamics_bmpr_inhibition__default.tsv",
            res / "dynamics_bmpr_inhibition__Q1_pgr_sufficient.tsv",
        ],
        {
            "model_version": version,
            "simulation": "10,000 trajectories, seed 1, unit rates, joint state carried across phases",
            "main_result": "Under BMP receptor inhibition the two Q1 hypotheses predict opposite decidualisation outcomes with identical pSMAD1/5/8 loss.",
            "limitations": "Model predictions, not observations. Time is dimensionless; magnitudes are trajectory frequencies, not concentrations.",
        },
    )


# -- 3. HAND2 relay transient -------------------------------------------------


def relay_figure(version: str) -> Path:
    res = ROOT / "endotwin" / "results" / version
    rows = _tsv(res / "relay_transient.tsv")
    summary = json.loads((res / "relay_transient_summary.json").read_text())
    legacy = [
        r
        for r in _tsv(ROOT / "docs/v052_paep_hand2/transient_trace.tsv")
        if r["cell"] == "hormone_treated_maternal"
        and r["node_id"] == "E_ESTROGENIC_PROLIFERATION"
    ]
    t = [float(r["time_in_phase"]) for r in rows]
    fig, (a, b) = plt.subplots(
        1, 2, figsize=(11, 3.9), gridspec_kw={"width_ratios": [1.25, 1]}
    )
    fig.patch.set_facecolor(SURFACE)
    _style(a)
    for key, color, label in (
        ("relay", BLUE, "stromal relay only (default, v0.5.2 form)"),
        ("relay_plus_direct", ORANGE, "relay + direct HAND2 term (v0.5.1 form)"),
    ):
        mean = [float(r[f"{key}_mean"]) for r in rows]
        sd = [float(r[f"{key}_sd"]) for r in rows]
        a.plot(t, mean, color=color, lw=2, label=label)
        a.fill_between(
            t,
            [m - s for m, s in zip(mean, sd, strict=True)],
            [m + s for m, s in zip(mean, sd, strict=True)],
            color=color,
            alpha=0.18,
            lw=0,
        )
    a.set_xlim(0, 8)
    a.set_title(
        f"ENDO-TWIN {version}: proliferation after progestin onset",
        fontsize=9,
        loc="left",
        color=INK,
    )
    a.set_xlabel(
        "MaBoSS time since onset of the differentiation phase", fontsize=8, color=INK_2
    )
    a.set_ylabel("P(OUT_EPITHELIAL_PROLIFERATION)", fontsize=8, color=INK_2)
    a.legend(frameon=False, fontsize=7.5, loc="upper right")
    a.text(
        0.98,
        0.55,
        f"area between curves {summary['area_between_curves_mean']:.3f} ± {summary['area_between_curves_sd']:.3f}\n"
        f"identical end-of-phase values ({summary['final_mean_relay']:.3f} vs {summary['final_mean_relay_plus_direct']:.3f})",
        transform=a.transAxes,
        ha="right",
        fontsize=7.5,
        color=INK_2,
    )
    _style(b)
    lt = [float(r["time"]) for r in legacy]
    b.plot(
        lt,
        [float(r["mean_paired_difference"]) for r in legacy],
        color=INK_2,
        lw=2,
        label="mean paired difference",
    )
    b.fill_between(
        lt,
        [float(r["pointwise_low"]) for r in legacy],
        [float(r["pointwise_high"]) for r in legacy],
        color=MUTED,
        alpha=0.3,
        lw=0,
        label="pointwise band (20 replicates)",
    )
    b.axhline(0, color=BASELINE, lw=0.8)
    b.set_title(
        "LEGACY record: prototype v0.5.2 minus v0.5.1", fontsize=9, loc="left", color=INK
    )
    b.set_xlabel(
        "MaBoSS time in hormone-treated cell (declared duration)",
        fontsize=8,
        color=INK_2,
    )
    b.set_ylabel("difference in P(E_ESTROGENIC_PROLIFERATION)", fontsize=8, color=INK_2)
    b.legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.tight_layout()
    return _save(
        fig,
        f"endotwin_relay_transient_{version.split('-')[-1]}",
        [
            res / "relay_transient.tsv",
            res / "relay_transient_summary.json",
            ROOT / "docs/v052_paep_hand2/transient_trace.tsv",
        ],
        {
            "model_version": version,
            "legacy_panel_model_versions": [
                "adoc-literature-superset-v0.5.1",
                "adoc-literature-superset-v0.5.2",
            ],
            "main_result": "Two representations with the same composed Boolean function differ only in the transient fall of epithelial proliferation.",
            "limitations": "Unit rates and dimensionless time; the legacy panel is a recorded result of the prototype adhesion model (restart-at-boundary semantics), not regenerated here.",
        },
    )


def render_all(version: str) -> list[Path]:
    from endotwin.animation import render_animation

    out = [
        network_figure(version),
        dynamics_figure(version),
        relay_figure(version),
        render_animation(version),
    ]
    for path in out:
        print(f"wrote {relative(path)}")
    return out
