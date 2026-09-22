"""Render MaBoSS pathway dynamics as a fixed-layout animated figure.

Every frame reuses the same node coordinates, the same compartment boxes and
the same axis limits, so nothing moves between frames except node fill, edge
opacity, the time cursor and the phase header.

What the figure does and does not assert is fixed here and repeated in the
legend, because a figure travels further than its documentation:

* Node fill encodes ``P(node = ON)`` across simulated MaBoSS trajectories --
  not concentration, expression level, secretion amount or flux.
* Edge sign and style are static and evidence-derived. Edge opacity follows
  the regulator's P(ON) as a visual activity cue only. It is not causal flux,
  reaction rate, edge probability, regulatory strength or pathway flow, and
  marginal node probabilities cannot establish joint edge activity.
* Input rows are deterministic protocol settings, not measurements.
* The x axis is MaBoSS relative time. There is no validated mapping to hours.
* The layout is a compartment schematic. It is not spatial, not cellularly
  resolved, and not a PhysiBoSS or agent-based output.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.lines import Line2D
from PIL import Image

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from dt_adoc.reporting.dynamics import (
    NetworkView,
    probability_to_color,
    sample_frame_indices,
)

# Explicit line breaks, not wrap=True: the footer must stay inside the network
# column and never run under the legend on the right.
_FOOTER_LINES = (
    (
        "Node fill = P(node = ON) across simulated MaBoSS trajectories "
        "(pale = 0, saturated = 1); not a concentration, expression level, "
        "secretion amount or flux."
    ),
    (
        "Edge sign and style are static and evidence-derived. Edge opacity "
        "follows the regulator's P(ON) as a visual activity cue only -- not "
        "causal flux, reaction rate, edge probability,"
    ),
    (
        "regulatory strength or pathway flow. Input rows are deterministic "
        "protocol settings, not measurements. Time is MaBoSS relative time "
        "(no validated mapping to hours)."
    ),
    (
        "Compartments are a schematic; the figure is not spatial, not "
        "cellularly resolved, and not a PhysiBoSS or agent-based output."
    ),
    (
        "Horizon is a dimensionless MaBoSS relative-time parameter, never a day "
        "or hour count. Orange dashes mark the DECLARED phase duration in the "
        "model's protocol file (see metadata), at which"
    ),
    (
        "the adhesion endpoints are still ~4000x short of their fixed point "
        "(docs/endpoint_convergence_finding.md). A converged adhesion value near "
        "0.82 is NOT a calibrated frequency: it equals"
    ),
    (
        "1 - (1 - 0.70)(1 - 0.40) from two hand-set relay istates in "
        "baseline.cfg; observed hormone-treated adhesion is 9/19 = 0.47. "
        "No magnitude is fitted: calibration.yaml keeps adhesion as an ordinal "
        "diagnostic only."
    ),
    (
        "EXPLORATORY: the endpoint-readout policy is decided but not implemented "
        "in the protocol files. S_IGFBP1 and S_PRL share one Boolean rule with "
        "no declared rates, so their curves"
    ),
    (
        "coincide by construction -- the observed IGFBP-1-before-PRL onset order "
        "is NOT represented. Only nodes marked with a filled dot carry an "
        "activated ADOC observation mapping."
    ),
)
CLAIM_FOOTER = "\n".join(_FOOTER_LINES)

PHASE_BAND_COLORS = ("#FFFFFF", "#F1F3F5")
CURSOR_COLOR = "#111111"
#: Marks the declared phase duration from the protocol file inside a
#: converged-horizon render. Deliberately a warm colour so it reads as a caveat
#: rather than as data.
DECLARED_HORIZON_COLOR = "#C2410C"
GHOST_ALPHA = 0.18

SERIES_COLORS = (
    "#1B7F5C",
    "#2A6F97",
    "#B03A2E",
    "#8C4C9E",
    "#A6761D",
    "#4A5568",
)


@dataclass(frozen=True)
class RenderSettings:
    """Presentation knobs that do not affect any simulated value."""

    figsize: tuple[float, float] = (16.0, 9.0)
    dpi: int = 76
    frame_stride: int = 2
    frame_duration_ms: int = 260
    max_width: int | None = None
    node_fontsize: float = 6.6
    #: Multiplies every text size in the figure. Raising dpi alone increases
    #: pixel density but keeps text the same fraction of the frame, which is
    #: what makes a dense network unreadable once GitHub scales the image down
    #: to README width. Scaling the fonts is what actually buys legibility.
    font_scale: float = 1.0
    show_numeric: bool = True
    #: Short git sha of the tree the figure was rendered from, with a ``-dirty``
    #: suffix when the tree is not clean. Printed on every frame so a published
    #: animation can be traced to a source state.
    source_commit: str = "unavailable"


def _text_color(hex_color: str) -> str:
    """Pick a readable label colour for a given node fill."""
    text = hex_color.lstrip("#")
    red, green, blue = (int(text[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    luminance = 0.299 * red + 0.587 * green + 0.114 * blue
    return "#1F2933" if luminance > 0.55 else "#FFFFFF"


def _draw_compartment_boxes(axis: Any, view: NetworkView, scale: float = 1.0) -> None:
    for class_name, compartment in view.compartments.items():
        if not any(node.compartment_class == class_name for node in view.nodes):
            continue
        region = str(compartment["region"])
        x0, y0, x1, y1 = view.regions[region]
        pad = 0.012
        box_pad = 0.004
        axis.add_patch(
            mpatches.FancyBboxPatch(
                (x0 - pad, y0 - pad),
                (x1 - x0) + 2 * pad,
                (y1 - y0) + 2 * pad,
                boxstyle="round,pad=0.004",
                linewidth=1.1,
                edgecolor=compartment["color"],
                facecolor=compartment["pale"],
                alpha=0.45,
                zorder=0,
            )
        )
        # Wrapped to the box width so neighbouring compartment titles cannot
        # run into one another.
        axis.text(
            (x0 + x1) / 2.0,
            y1 + pad + box_pad + 0.010,
            "\n".join(textwrap.wrap(str(compartment["label"]), width=34)),
            ha="center",
            va="bottom",
            fontsize=7.8 * scale,
            fontweight="semibold",
            color=compartment["color"],
            linespacing=1.25,
            zorder=1,
        )


def _draw_edges(
    axis: Any,
    view: NetworkView,
    values: dict[str, float],
    graph: nx.DiGraph,
) -> None:
    positions = view.positions
    style = view.edge_style
    min_alpha = float(style.get("min_alpha", 0.10))
    max_alpha = float(style.get("max_alpha", 0.85))
    for edge in view.edges:
        # Opacity tracks the REGULATOR's marginal probability. Inputs are not
        # in the trajectory, so their deterministic state is used instead.
        activity = float(values.get(edge.source, 0.0))
        alpha = min_alpha + (max_alpha - min_alpha) * max(0.0, min(1.0, activity))
        nx.draw_networkx_edges(
            graph,
            pos=positions,
            edgelist=[(edge.source, edge.target)],
            ax=axis,
            arrows=True,
            # A blunt bar reads as inhibition; a filled head reads as activation.
            arrowstyle="-[" if edge.sign == "inhibition" else "-|>",
            arrowsize=9 if edge.sign == "inhibition" else 8,
            edge_color=edge.color,
            width=1.35 if edge.cross_compartment else 0.9,
            alpha=alpha,
            style=edge.style,
            min_source_margin=13,
            min_target_margin=13,
            connectionstyle="arc3,rad=0.06",
            node_size=300,
        )


def _draw_nodes(
    axis: Any,
    view: NetworkView,
    values: dict[str, float],
    settings: RenderSettings,
) -> None:
    for node in view.nodes:
        compartment = view.compartments[node.compartment_class]
        probability = float(values.get(node.node_id, 0.0))
        fill = probability_to_color(
            probability,
            pale=str(compartment["pale"]),
            saturated=str(compartment["color"]),
        )
        if node.is_input:
            # Deterministic protocol settings read as exact 0 or 1.
            caption = f"{node.short_label}\n{probability:.0f}"
        elif settings.show_numeric:
            caption = f"{node.short_label}\n{probability:.2f}"
        else:
            caption = node.short_label
        axis.text(
            node.position[0],
            node.position[1],
            caption,
            ha="center",
            va="center",
            fontsize=settings.node_fontsize * settings.font_scale,
            fontweight="semibold" if node.is_output else "normal",
            color=_text_color(fill),
            linespacing=1.18,
            zorder=3,
            bbox={
                # Outputs get a distinct squared-off shape.
                "boxstyle": "square,pad=0.34" if node.is_output else "round,pad=0.30",
                "facecolor": fill,
                "edgecolor": compartment["color"],
                "linewidth": 2.0 if node.is_output else 1.0,
                "linestyle": "--" if node.uncertain else "-",
            },
        )


def _draw_legend(axis: Any, view: NetworkView, scale: float = 1.0) -> None:
    axis.axis("off")
    handles = [
        Line2D(
            [],
            [],
            color=view.edge_style.get("activation_color", "#2D6A4F"),
            lw=2.0,
            label="activation",
        ),
        Line2D(
            [],
            [],
            color=view.edge_style.get("inhibition_color", "#BC4749"),
            lw=2.0,
            label="inhibition",
        ),
        Line2D(
            [], [], color="#4A5568", lw=1.6, ls="--", label="uncertain / assumed edge"
        ),
        Line2D([], [], color="#4A5568", lw=2.4, label="cross-compartment (thicker)"),
        Line2D(
            [],
            [],
            color="none",
            marker="s",
            markersize=8,
            markerfacecolor="#FFFFFF",
            markeredgecolor="#4A5568",
            markeredgewidth=1.4,
            ls="--",
            label="uncertain relay node (dashed)",
        ),
        Line2D(
            [],
            [],
            color="none",
            marker="s",
            markersize=8,
            markerfacecolor="#F9EEEC",
            markeredgecolor="#B03A2E",
            markeredgewidth=2.2,
            label="phenotype output (heavy square)",
        ),
    ]
    axis.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(-0.02, 1.18),
        ncol=2,
        frameon=True,
        fontsize=7.0 * scale,
        handlelength=2.2,
        columnspacing=1.1,
        borderpad=0.6,
        title="Edge and node styling (static, evidence-derived)",
        title_fontsize=7.2 * scale,
    )


def _draw_panels(
    axes: list[Any],
    view: NetworkView,
    timeline: Any,
    row_index: int,
    labels: dict[str, str],
    scale: float = 1.0,
) -> None:
    frame = timeline.frame
    times = frame["global_time"].to_numpy(dtype=float)
    cursor = float(times[row_index])
    total = float(timeline.total_duration)

    for axis, panel in zip(axes, view.panels, strict=True):
        for index, phase in enumerate(timeline.phases):
            axis.axvspan(
                phase.phase_start,
                phase.phase_end,
                color=PHASE_BAND_COLORS[index % len(PHASE_BAND_COLORS)],
                zorder=0,
            )
            if index:
                axis.axvline(
                    phase.phase_start, color="#ADB5BD", lw=0.8, ls=":", zorder=1
                )
            # Where the COMMITTED policy in config/protocols.yaml would have read
            # this phase. Drawn only when the executed horizon is longer, i.e.
            # when a converged override is in force -- at which point the marker
            # is the only in-frame evidence that the declared readout is still
            # in transit. See docs/endpoint_convergence_finding.md.
            declared = getattr(phase, "declared_duration", phase.relative_duration)
            if declared < phase.relative_duration:
                axis.axvline(
                    phase.phase_start + declared,
                    color=DECLARED_HORIZON_COLOR,
                    lw=1.0,
                    ls=(0, (4, 2)),
                    alpha=0.9,
                    zorder=1,
                )
        for series_index, node_id in enumerate(panel.members):
            color = SERIES_COLORS[series_index % len(SERIES_COLORS)]
            series = frame[node_id].to_numpy(dtype=float)
            axis.plot(times, series, color=color, lw=0.9, alpha=GHOST_ALPHA, zorder=2)
            axis.plot(
                times[: row_index + 1],
                series[: row_index + 1],
                color=color,
                lw=1.7,
                label=labels.get(node_id, node_id),
                zorder=3,
            )
        axis.axvline(cursor, color=CURSOR_COLOR, lw=1.1, alpha=0.8, zorder=4)
        axis.set_title(panel.title, fontsize=8.0 * scale, pad=3.0, loc="left")
        axis.set_ylabel(panel.axis_label, fontsize=7.0 * scale)
        axis.set_xlim(0.0, total)
        axis.set_ylim(-0.04, 1.06)
        axis.tick_params(axis="both", labelsize=6.5 * scale)
        axis.grid(alpha=0.16, lw=0.5)
        axis.legend(
            frameon=False,
            fontsize=5.8 * scale,
            loc="upper left",
            ncol=3,
            handlelength=1.2,
            columnspacing=0.8,
        )
    for axis in axes[:-1]:
        axis.set_xticklabels([])
    axes[-1].set_xlabel(
        "MaBoSS relative time (no validated hour mapping)", fontsize=7.2 * scale
    )
    axes[-1].set_xticks([phase.phase_start for phase in timeline.phases] + [total])


def render_frame(
    *,
    view: NetworkView,
    timeline: Any,
    row_index: int,
    settings: RenderSettings,
    graph: nx.DiGraph,
) -> Image.Image:
    """Render a single animation frame to a PIL image."""
    row = timeline.frame.iloc[row_index]
    values = {
        node.node_id: float(row[node.node_id])
        for node in view.nodes
        if node.node_id in row
    }
    phase = timeline.phase_at(float(row["global_time"]))

    figure = plt.figure(figsize=settings.figsize, dpi=settings.dpi)
    # The panel column is sized from the view, not hardcoded: the superset adds a
    # secreted-analyte panel and a fixed nrows=5 silently raised
    # `zip() argument 2 is longer than argument 1` in _draw_panels.
    panel_count = max(1, len(view.panels))
    grid = figure.add_gridspec(
        nrows=panel_count + 1,
        ncols=2,
        width_ratios=[2.05, 1.0],
        height_ratios=[*([1.0] * panel_count), 0.62],
        left=0.030,
        right=0.972,
        top=min(0.880, 0.900 - 0.018 * settings.font_scale),
        # The claim footer grew to nine lines when the horizon caveats were
        # added; at font_scale 1.75 it needs ~0.12 of the figure height, so the
        # grid must not extend below it or the phenotype band is overprinted.
        bottom=0.138,
        wspace=0.10,
        hspace=0.52,
    )
    network_axis = figure.add_subplot(grid[:, 0])
    panel_axes = [figure.add_subplot(grid[index, 1]) for index in range(panel_count)]
    legend_axis = figure.add_subplot(grid[panel_count, 1])

    network_axis.set_xlim(0.0, 1.0)
    network_axis.set_ylim(0.0, 1.0)
    network_axis.axis("off")
    _draw_compartment_boxes(network_axis, view, settings.font_scale)
    _draw_edges(network_axis, view, values, graph)
    _draw_nodes(network_axis, view, values, settings)

    labels = {node.node_id: node.short_label for node in view.nodes}
    _draw_panels(
        panel_axes[: len(view.panels)],
        view,
        timeline,
        row_index,
        labels,
        settings.font_scale,
    )
    for axis in panel_axes[len(view.panels) :]:
        axis.axis("off")
    _draw_legend(legend_axis, view, settings.font_scale)

    phase_ordinal = f"Phase {phase.phase_index + 1}/{len(timeline.phases)}"
    figure.suptitle(
        f"{phase_ordinal}  {phase.label}   |   simulation time "
        f"{float(row['global_time']):.1f} (phase "
        f"{float(row['phase_local_time']):.1f} / "
        f"{phase.relative_duration:.1f}, dimensionless)",
        fontsize=14.5 * settings.font_scale,
        fontweight="semibold",
        x=0.012,
        ha="left",
        y=0.985 - 0.008 * settings.font_scale,
    )
    figure.text(
        0.012,
        0.952 - 0.020 * settings.font_scale,
        f"model {view.model_version}  ·  commit {settings.source_commit}"
        f"  ·  protocol {phase.protocol_id}"
        f"  ·  phase {phase.phase_index + 1}/{len(timeline.phases)}"
        f"  ·  seed {timeline.seed}  ·  {timeline.trajectory_count} trajectories"
        f"  ·  horizon {phase.relative_duration:.1f} dimensionless"
        f" (declared {phase.declared_duration:.1f})",
        fontsize=8.6 * settings.font_scale,
        color="#4A5568",
        ha="left",
    )
    figure.text(
        0.012,
        0.012,
        CLAIM_FOOTER,
        fontsize=6.0 * settings.font_scale,
        color="#4A5568",
        ha="left",
        va="bottom",
        wrap=True,
    )

    figure.canvas.draw()
    image = Image.fromarray(np.asarray(figure.canvas.buffer_rgba())).convert("RGB")
    plt.close(figure)
    if settings.max_width and image.width > settings.max_width:
        height = round(image.height * settings.max_width / image.width)
        image = image.resize((settings.max_width, height), Image.LANCZOS)
    return image


def _quantize_with_shared_palette(images: list[Image.Image]) -> list[Image.Image]:
    """Quantize every frame against one palette derived from all of them.

    Quantizing frames independently is wrong twice over: each frame gets its own
    palette, so flat regions shimmer between frames, and a per-frame median cut
    on a mostly-white figure spends its palette on near-white gradients and
    collapses the saturated compartment colours toward grey. Both destroy the
    compartment colour coding the figure depends on.

    Sampling every frame into one strip and taking a single adaptive palette
    keeps the compartment hues distinct and stable for the whole animation.
    """
    width, height = images[0].size
    # A vertical strip of downscaled frames is enough to capture every colour
    # that appears anywhere in the animation without allocating full frames.
    sample_height = max(1, height // 4)
    strip = Image.new("RGB", (max(1, width // 4), sample_height * len(images)))
    for index, image in enumerate(images):
        strip.paste(
            image.resize((max(1, width // 4), sample_height), Image.NEAREST),
            (0, index * sample_height),
        )
    palette = strip.quantize(colors=256, method=Image.MAXCOVERAGE)
    return [
        image.quantize(palette=palette, dither=Image.Dither.NONE) for image in images
    ]


def build_graph(view: NetworkView) -> nx.DiGraph:
    """Graph object shared by every frame so geometry cannot drift."""
    graph = nx.DiGraph()
    for node in view.nodes:
        graph.add_node(node.node_id)
    for edge in view.edges:
        graph.add_edge(edge.source, edge.target)
    return graph


def render_animation(
    *,
    view: NetworkView,
    timeline: Any,
    output_path: Path,
    settings: RenderSettings | None = None,
    preview_path: Path | None = None,
) -> dict[str, Any]:
    """Render the animation and return its reproducibility metadata."""
    active = settings or RenderSettings()
    graph = build_graph(view)
    indices = sample_frame_indices(len(timeline.frame), active.frame_stride)
    if len(indices) < 2:
        raise ValueError(
            "An animation needs at least two frames; reduce --frame-stride."
        )
    images = [
        render_frame(
            view=view,
            timeline=timeline,
            row_index=index,
            settings=active,
            graph=graph,
        )
        for index in indices
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    quantized = _quantize_with_shared_palette(images)
    quantized[0].save(
        output_path,
        save_all=True,
        append_images=quantized[1:],
        duration=active.frame_duration_ms,
        loop=0,
        optimize=True,
    )

    preview_index = indices[len(indices) * 2 // 3]
    if preview_path is not None:
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        images[len(indices) * 2 // 3].save(preview_path, format="PNG", optimize=True)

    return {
        "frame_count": len(images),
        "frame_duration_ms": active.frame_duration_ms,
        "frame_stride": active.frame_stride,
        "frame_row_indices": indices,
        "preview_row_index": preview_index,
        "image_width": images[0].width,
        "image_height": images[0].height,
        "gif_bytes": output_path.stat().st_size,
    }
