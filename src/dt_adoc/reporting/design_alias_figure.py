"""Where the experimentally indistinguishable nodes sit in the biological network.

Two figures over the analysis in ``design_alias.py``.

**A -- current experimental resolution.** The compartment layout the animation
already uses -- inputs, luminal epithelium, ECM/interface, stroma, phenotype
outputs -- recoloured so that one fill colour is one *design-equivalence class*:
nodes the declared plan's arms cannot tell apart. Nodes are not collapsed into
supernodes, because the question the figure answers is *where in the tissue* the
indistinguishable nodes sit, and a supernode destroys exactly that.

Fill and border carry different things on purpose, and the caption says so:

* **fill colour** = design class. Same colour, same behaviour under this plan.
* **border** = whether that merge is the *rules'* fault or the *design's*.
  A heavy dark border means the node shares a Boolean function with another node
  (``P_global``); no arm separates it and only a rule change would. A thin border
  means the merge is design-induced and a further arm can break it.
* **dashed border with hatching** = a latent placeholder. Not resolved, not
  aliased: unknown in every arm.

The third encoding is a badge letter naming the structural class, so a reader can
see which sub-groups inside one fill colour are locked together by the rules.
That matters most for the 22-member class: it is not one Boolean function, it is
four of them that the plan's arms happen to move in lockstep.

**B -- which couplings are experimentally breakable.** Every candidate fifth arm
scored against the plan itself, with the classes each one splits. Candidates that
correspond to a committed condition cfg are marked; the rest would need a new cfg
written before they could be run, and the figure says which.

WHAT THE COLOURS DO NOT MEAN. Same colour is not same biology, not same pathway,
not same cell type, and not evidence that two molecules are interchangeable. It
is a statement about *this design*: under these arms, these nodes take the same
value in every condition, so no measurement taken in them can tell the nodes
apart. ``docs/design_alias_note.md`` states this at length, and the legend states
it on the figure itself.

Nothing here simulates and nothing is painted by hand. Every class comes from
``design_alias.py``, every position from ``config/visualization.yaml`` through
``dynamics.build_network_view``, and every edge from ``network.bnd``.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

#: Fixes the salt for SVG element ids so repeated runs are byte-identical.
matplotlib.rcParams["svg.hashsalt"] = "dt-adoc-design-alias"

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from dt_adoc.model.provenance import repo_root, source_commit
from dt_adoc.model.runtime import resolve_model
from dt_adoc.reporting.design_alias import (
    DesignAliasFacts,
    FifthArm,
    _Enumerator,
    candidate_fifth_arms,
    design_alias_summary,
    load_design_alias,
    load_plan,
)
from dt_adoc.reporting.dynamics import (
    VIEW_FULL,
    build_edge_views,
    build_network_view,
    load_visualization_config,
)
from dt_adoc.reporting.identifiability import load_identifiability

#: Okabe-Ito, the standard colour-vision-deficiency-safe scientific sequence,
#: in a fixed order, taken unmodified from its published definition. The
#: accessibility claim rests on that provenance, which a reader can check
#: against the hex values below, and NOT on a computation this repository
#: performs. An earlier revision of this comment and of
#: docs/design_alias_note.md quoted specific colour-difference figures --
#: "worst pair 15.8 under deuteranopia, 16.4 at normal vision, both clear of a
#: deltaE 8 floor" -- which named neither the difference metric nor the
#: deficiency simulation and which nothing in src/, tests/ or scripts/ computes.
#: They were withdrawn rather than reverse-engineered: picking a formula until
#: it reproduced 15.8 would have manufactured provenance instead of supplying
#: it. Restoring numbers here means committing the computation that yields them.
#:
#: The sub-3:1 surface contrast of the lighter hues is relieved, as it must be,
#: by a visible label on every node and by
#: docs/design_alias/node_design_classes.tsv as a table view.
#:
#: Assigned in fixed order to design classes sorted by descending size, so a
#: class keeps its colour when a re-run changes nothing about it. Colour follows
#: the class, never its rank in some filtered subset.
CLASS_HUES = (
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#8C6D1F",  # dark ochre
)

#: Singletons and any class beyond the palette. Neutral on purpose: "this design
#: already separates it" is the absence of a finding, and it must not compete
#: visually with the classes that are the finding.
NEUTRAL_FILL = "#EEF0F2"
NEUTRAL_EDGE = "#98A2AC"

#: Latent placeholders. Grey-violet with hatching, never one of the class hues:
#: they are not an equivalence class, they are unknown.
PLACEHOLDER_FILL = "#E4E0EC"
PLACEHOLDER_EDGE = "#6B5B8A"

INK = "#1F2933"
MUTED = "#6B7684"

#: Border weight for a node the *rules* alias to another node. Heavier than the
#: design-only border because it is the finding a reader can act on least
#: cheaply: no arm fixes it.
STRUCTURAL_LINEWIDTH = 2.3
DESIGN_LINEWIDTH = 0.9


def _compact(node_id: str) -> str:
    """Drop the compartment prefix for a label that has to fit in a panel."""
    for prefix in ("E_", "S_", "X_", "IN_", "OUT_"):
        if node_id.startswith(prefix):
            return node_id[len(prefix) :]
    return node_id


def _tint(hex_color: str, weight: float) -> str:
    """Mix ``hex_color`` toward white so a label stays legible on top of it."""
    text = hex_color.lstrip("#")
    channels = (int(text[i : i + 2], 16) for i in (0, 2, 4))
    mixed = (round(c + (255 - c) * weight) for c in channels)
    return "#" + "".join(f"{value:02X}" for value in mixed)


def _text_color(hex_color: str) -> str:
    text = hex_color.lstrip("#")
    red, green, blue = (int(text[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return INK if 0.299 * red + 0.587 * green + 0.114 * blue > 0.55 else "#FFFFFF"


def assign_class_colors(
    facts: DesignAliasFacts,
) -> tuple[dict[tuple[str, ...], str], dict[tuple[str, ...], str]]:
    """Design class -> (fill, border), deterministic from the partition.

    Only classes with more than one member earn a hue: a singleton is not a
    finding. Ordering is by descending size then by the class's first node, so
    the assignment is a function of the model and the plan alone -- never of
    iteration order, and never hand-set.
    """
    ranked = sorted(
        (c for c in facts.design_classes if len(c) > 1),
        key=lambda c: (-len(c), min(c)),
    )
    fills: dict[tuple[str, ...], str] = {}
    borders: dict[tuple[str, ...], str] = {}
    for index, members in enumerate(ranked):
        if index < len(CLASS_HUES):
            hue = CLASS_HUES[index]
            fills[members] = _tint(hue, 0.68)
            borders[members] = hue
        else:  # pragma: no cover - the palette covers the current partition
            fills[members] = NEUTRAL_FILL
            borders[members] = NEUTRAL_EDGE
    return fills, borders


def _global_badges(facts: DesignAliasFacts) -> dict[str, str]:
    """A short letter per multi-member structural class, for the node badge.

    Only classes the *rules* merge get one. A badge on a singleton would say
    nothing, and the figure has 59 nodes to keep legible.
    """
    ranked = sorted(
        (c for c in facts.global_classes if len(c) > 1),
        key=lambda c: (-len(c), min(c)),
    )
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return {
        node_id: letters[index]
        for index, members in enumerate(ranked)
        for node_id in members
    }


def _style_for(
    node_id: str,
    facts: DesignAliasFacts,
    fills: dict[tuple[str, ...], str],
    borders: dict[tuple[str, ...], str],
) -> tuple[str, str, float, str | None]:
    """(fill, border, linewidth, hatch) for one node, from its category."""
    category = facts.category[node_id]
    if category == "interface_placeholder":
        return PLACEHOLDER_FILL, PLACEHOLDER_EDGE, 1.5, "////"
    if category == "latent_biological":
        return PLACEHOLDER_FILL, PLACEHOLDER_EDGE, 1.5, "...."
    members = facts.design_class_of[node_id]
    fill = fills.get(members, NEUTRAL_FILL)
    border = borders.get(members, NEUTRAL_EDGE)
    structural = len(facts.global_class_of[node_id]) > 1
    return (
        fill,
        border if not structural else _darken(border),
        STRUCTURAL_LINEWIDTH if structural else DESIGN_LINEWIDTH,
        None,
    )


def _darken(hex_color: str) -> str:
    text = hex_color.lstrip("#")
    channels = (int(text[i : i + 2], 16) for i in (0, 2, 4))
    return "#" + "".join(f"{round(c * 0.62):02X}" for c in channels)


# --------------------------------------------------------------------------
# Figure A
# --------------------------------------------------------------------------


def _draw_network(
    axis: Any,
    facts: DesignAliasFacts,
    view: Any,
    edges: tuple[Any, ...],
    fills: dict[tuple[str, ...], str],
    borders: dict[tuple[str, ...], str],
    badges: dict[str, str],
    short_labels: dict[str, str],
) -> None:
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(0.0, 1.0)
    axis.axis("off")

    for class_name, compartment in view.compartments.items():
        if not any(n.compartment_class == class_name for n in view.nodes):
            continue
        x0, y0, x1, y1 = view.regions[str(compartment["region"])]
        pad = 0.012
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
        axis.text(
            (x0 + x1) / 2.0,
            y1 + pad + 0.014,
            "\n".join(textwrap.wrap(str(compartment["label"]), width=36)),
            ha="center",
            va="bottom",
            fontsize=7.6,
            fontweight="semibold",
            color=compartment["color"],
            linespacing=1.25,
            zorder=1,
        )

    positions = view.positions
    # Edges are drawn thin and pale. Topology is context here, not the message:
    # the message is which nodes share a fill, and a dense edge set competes
    # with it. Sign is kept because an inhibition drawn as an activation would
    # be wrong, not merely busy.
    for edge in edges:
        if edge.source not in positions or edge.target not in positions:
            continue
        x0, y0 = positions[edge.source]
        x1, y1 = positions[edge.target]
        axis.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops={
                "arrowstyle": "-|>,head_width=0.11,head_length=0.24",
                "color": edge.color,
                "alpha": 0.20,
                "linewidth": 0.55,
                "linestyle": edge.style,
                "shrinkA": 12.0,
                "shrinkB": 12.0,
                "connectionstyle": "arc3,rad=0.10",
            },
            zorder=1,
        )

    for node in view.nodes:
        fill, border, width, hatch = _style_for(node.node_id, facts, fills, borders)
        x, y = node.position
        label = short_labels.get(node.node_id, node.short_label)
        axis.add_patch(
            mpatches.FancyBboxPatch(
                (x - 0.052, y - 0.0155),
                0.104,
                0.031,
                boxstyle="round,pad=0.0035",
                linewidth=width,
                edgecolor=border,
                facecolor=fill,
                hatch=hatch,
                zorder=3,
            )
        )
        # A hatch drawn under a label makes the label unreadable, and these are
        # the nodes a reader most needs to identify by name. The plate is only
        # on hatched nodes: adding it everywhere would put a second border
        # around all 59 and compete with the class borders.
        axis.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=4.9,
            color=_text_color(fill),
            zorder=4,
            bbox=None
            if hatch is None
            else {
                "boxstyle": "round,pad=0.16",
                "facecolor": fill,
                "edgecolor": "none",
            },
        )
        badge = badges.get(node.node_id)
        if badge:
            axis.text(
                x + 0.0505,
                y + 0.0145,
                badge,
                ha="center",
                va="center",
                fontsize=4.4,
                fontweight="bold",
                color=_darken(border),
                zorder=5,
                bbox={
                    "boxstyle": "circle,pad=0.14",
                    "facecolor": "#FFFFFF",
                    "edgecolor": _darken(border),
                    "linewidth": 0.5,
                },
            )


def _annotate_measured(axis: Any, facts: DesignAliasFacts, view: Any) -> None:
    """Ring the measured nodes and say which of them this design cannot separate.

    The reader is told to look at the class containing PAEP and IGFBP-1, and it
    is the one class where the aliasing has an immediate experimental cost: two
    of the three quantities the repository records an observation for sit inside
    it, so no contrast between them is informative under this plan. Which nodes
    get the ring is read from the observation tables, not from this function.
    """
    positions = view.positions
    measured = [n for n in facts.measured_nodes if n in positions]
    for node_id in measured:
        x, y = positions[node_id]
        axis.add_patch(
            mpatches.FancyBboxPatch(
                (x - 0.058, y - 0.0205),
                0.116,
                0.041,
                boxstyle="round,pad=0.0035",
                linewidth=1.3,
                edgecolor="#111111",
                facecolor="none",
                linestyle=(0, (2.4, 1.6)),
                zorder=6,
            )
        )
    # Grouped by class rather than flattened: if the measured nodes ever spanned
    # two aliased classes, naming one class's size for all of them would be
    # wrong. One clause per class keeps the caption true in that case too.
    grouped: dict[tuple[str, ...], list[str]] = {}
    for node_id in measured:
        members = facts.design_class_of[node_id]
        if len(set(members) & set(facts.measured_nodes)) > 1:
            grouped.setdefault(members, []).append(node_id)
    if not grouped:  # pragma: no cover - the current plan always aliases two
        return
    clauses = [
        " and ".join(_compact(n) for n in sorted(nodes))
        + f" share one design class of {len(members)} nodes"
        for members, nodes in sorted(grouped.items(), key=lambda kv: -len(kv[0]))
    ]
    axis.text(
        0.5,
        0.017,
        "Black dashed ring: a node the repository records an observation for.  "
        + "; ".join(clauses)
        + ", so under this plan no contrast between them is informative.",
        ha="center",
        va="bottom",
        fontsize=6.4,
        color="#111111",
        zorder=7,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "#FFFFFF",
            "edgecolor": "#111111",
            "linewidth": 0.7,
        },
    )


def _legend_handles(
    facts: DesignAliasFacts,
    fills: dict[tuple[str, ...], str],
    borders: dict[tuple[str, ...], str],
) -> list[Any]:
    ranked = sorted(
        (c for c in facts.design_classes if len(c) > 1),
        key=lambda c: (-len(c), min(c)),
    )
    handles: list[Any] = []
    for members in ranked:
        structural = sorted(
            {facts.global_class_of[n] for n in members}, key=lambda c: (-len(c), min(c))
        )
        detail = f"{len(members)} nodes, {len(structural)} Boolean function"
        detail += "s" if len(structural) > 1 else ""
        handles.append(
            mpatches.Patch(
                facecolor=fills[members],
                edgecolor=borders[members],
                linewidth=1.4,
                label=f"{min(members)} + {len(members) - 1} more  ({detail})",
            )
        )
    handles.append(
        mpatches.Patch(
            facecolor=NEUTRAL_FILL,
            edgecolor=NEUTRAL_EDGE,
            label="This plan already separates it (singleton)",
        )
    )
    handles.append(
        mpatches.Patch(
            facecolor=PLACEHOLDER_FILL,
            edgecolor=PLACEHOLDER_EDGE,
            hatch="////",
            label="Interface placeholder: unknown in every arm, no assay target",
        )
    )
    handles.append(
        mpatches.Patch(
            facecolor=PLACEHOLDER_FILL,
            edgecolor=PLACEHOLDER_EDGE,
            hatch="....",
            label="Latent biological state: unknown in every arm, assayable",
        )
    )
    handles.append(
        mpatches.Patch(
            facecolor="#FFFFFF",
            edgecolor=_darken(CLASS_HUES[0]),
            linewidth=STRUCTURAL_LINEWIDTH,
            label="Heavy border: merged by the RULES; no arm separates it",
        )
    )
    handles.append(
        mpatches.Patch(
            facecolor="#FFFFFF",
            edgecolor=NEUTRAL_EDGE,
            linewidth=DESIGN_LINEWIDTH,
            label="Thin border: merged by the DESIGN; another arm can split it",
        )
    )
    handles.append(
        Line2D(
            [],
            [],
            linestyle="none",
            marker="o",
            markerfacecolor="#FFFFFF",
            markeredgecolor=INK,
            markersize=5,
            label="Badge letter: which Boolean function the node implements",
        )
    )
    return handles


def _draw_structural_breakdown(
    axis: Any, facts: DesignAliasFacts, fills: dict[tuple[str, ...], str]
) -> None:
    """The companion panel: each design class opened into its Boolean functions.

    Figure A can show *that* a fill colour spans several structural classes via
    the badge letters, but not cleanly *which*. This panel is the answer, and it
    is where the structural-versus-design distinction becomes actionable: a bar
    of one segment is a class no arm will ever split; a bar of several segments
    is a class an arm can split, and the segments are the pieces it splits into.
    """
    axis.axis("off")
    ranked = sorted(
        (c for c in facts.design_classes if len(c) > 1),
        key=lambda c: (-len(c), min(c)),
    )
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(-0.6, len(ranked) - 0.4)
    axis.invert_yaxis()
    widest = max(len(c) for c in ranked)

    for row, members in enumerate(ranked):
        groups = sorted(
            {facts.global_class_of[n] for n in members},
            key=lambda c: (-len(c), min(c)),
        )
        left = 0.0
        for group in groups:
            width = len(group) / widest * 0.74
            axis.add_patch(
                mpatches.Rectangle(
                    (left + 0.005, row - 0.26),
                    max(width - 0.010, 0.004),
                    0.52,
                    facecolor=fills[members],
                    edgecolor=_darken(fills[members]),
                    linewidth=1.5 if len(group) > 1 else 0.6,
                    zorder=2,
                )
            )
            if len(group) > 1:
                axis.text(
                    left + width / 2.0,
                    row,
                    str(len(group)),
                    ha="center",
                    va="center",
                    fontsize=5.4,
                    color=INK,
                    zorder=3,
                )
            left += width
        # Truncated rather than wrapped: the panel is a shape comparison and the
        # exact membership is one column away in node_design_classes.tsv.
        name = _compact(min(members))
        if len(name) > 15:
            name = name[:14] + "\u2026"
        axis.text(
            0.77,
            row,
            f"{name} +{len(members) - 1}  "
            f"({len(groups)} fn{'s' if len(groups) > 1 else ''})",
            ha="left",
            va="center",
            fontsize=5.2,
            color=INK,
        )


# --------------------------------------------------------------------------
# Figure B
# --------------------------------------------------------------------------


def _shortlist(
    candidates: tuple[FifthArm, ...], limit: int = 12
) -> tuple[FifthArm, ...]:
    """The distinct experiments worth drawing, best first.

    Candidates are de-duplicated by the *refinement they produce* -- the full
    set of resulting parts -- not by name and not by which classes they touch.
    Four HAND2-loss arms on four backgrounds produce the identical refinement,
    and drawing four identical bars would read as four options where there is
    one.

    Keying on the set of classes *touched* was tried and is wrong: six of the
    eight such keys collapse candidates that refine those classes differently,
    and the measured-analyte verdict is not even constant within such a key. A
    bar could then carry the "separates two measured analytes" marker from its
    representative while a sibling folded into it separates nothing, or the
    reverse. The refinement is the experiment's identity.

    Among candidates producing the same refinement the representative kept is
    the first in sort order -- highest gain, then a committed cfg ahead of one
    that would need writing. Since equal refinement implies equal gain, the
    committed-cfg preference is decisive within each group.
    """
    chosen: list[FifthArm] = []
    seen: set[tuple[tuple[str, ...], ...]] = set()
    for candidate in sorted(
        candidates,
        key=lambda c: (-c.gain, c.committed_cfg == "", c.candidate_id),
    ):
        if candidate.gain <= 0:
            continue
        key = tuple(
            sorted(
                tuple(sorted(p)) for _before, parts in candidate.splits for p in parts
            )
        )
        if key in seen:
            continue
        seen.add(key)
        chosen.append(candidate)
        if len(chosen) == limit:
            break
    return tuple(chosen)


def _arm_label(candidate: FifthArm) -> str:
    """Bar label: the experiment, then whether the model can already express it."""
    return candidate.label + ("" if candidate.committed_cfg else "  [needs a new cfg]")


def _draw_gain(
    axis: Any,
    facts: DesignAliasFacts,
    shortlist: tuple[FifthArm, ...],
    fills: dict[tuple[str, ...], str],
) -> None:
    baseline = len(facts.design_classes)
    axis.set_xlim(0, max((c.classes_after for c in shortlist), default=baseline) + 3.4)
    axis.set_ylim(-0.7, len(shortlist) - 0.3)
    axis.invert_yaxis()
    axis.axvline(baseline, color=MUTED, linewidth=0.9, linestyle=(0, (4, 3)), zorder=1)
    axis.text(
        baseline - 0.25,
        -0.62,
        f"plan as it stands: {baseline}",
        ha="right",
        va="center",
        fontsize=5.6,
        color=MUTED,
    )

    for row, candidate in enumerate(shortlist):
        axis.barh(
            row,
            baseline,
            height=0.52,
            color="#DDE2E7",
            edgecolor="none",
            zorder=2,
        )
        axis.barh(
            row,
            candidate.gain,
            left=baseline,
            height=0.52,
            color="#0072B2",
            edgecolor="none",
            zorder=3,
        )
        note = f"+{candidate.gain} -> {candidate.classes_after}"
        if candidate.separated_measured_pairs:
            note += "  * measured pair"
        axis.text(
            baseline + candidate.gain + 0.28,
            row,
            note,
            ha="left",
            va="center",
            fontsize=5.8,
            fontweight="bold" if candidate.separated_measured_pairs else "normal",
            color=INK,
        )
        # Which of the current classes this arm splits, in their own colours.
        for index, (before, _parts) in enumerate(
            sorted(candidate.splits, key=lambda s: (-len(s[0]), min(s[0])))
        ):
            axis.add_patch(
                mpatches.Rectangle(
                    (0.35 + index * 0.62, row - 0.12),
                    0.5,
                    0.24,
                    facecolor=fills.get(before, NEUTRAL_FILL),
                    edgecolor=_darken(fills.get(before, NEUTRAL_EDGE)),
                    linewidth=0.7,
                    zorder=4,
                )
            )

    axis.set_yticks(range(len(shortlist)))
    axis.set_yticklabels(
        ["\n".join(textwrap.wrap(_arm_label(c), width=34)) for c in shortlist],
        fontsize=5.7,
    )
    axis.set_xlabel(
        "Design-equivalence classes the arms can separate  "
        "(swatches: which current classes this arm splits)",
        fontsize=6.2,
        color=INK,
    )
    axis.tick_params(axis="x", labelsize=5.8)
    for spine in ("top", "right", "left"):
        axis.spines[spine].set_visible(False)
    axis.spines["bottom"].set_color(MUTED)


def _draw_split_detail(
    axis: Any, facts: DesignAliasFacts, shortlist: tuple[FifthArm, ...]
) -> None:
    """Which biological nodes each leading arm actually pulls apart."""
    axis.axis("off")
    axis.set_xlim(0.0, 1.0)
    lines: list[str] = []
    for candidate in shortlist[:5]:
        lines.append(
            "\n".join(
                textwrap.wrap(
                    f"{_arm_label(candidate)}  (+{candidate.gain})",
                    width=62,
                    subsequent_indent="  ",
                )
            )
        )
        if candidate.separated_measured_pairs:
            for left, right in candidate.separated_measured_pairs:
                lines.append(
                    f"  * SEPARATES MEASURED {_compact(left)} from {_compact(right)}"
                )
        else:
            lines.append("    separates no two measured analytes")
        for before, parts in sorted(
            candidate.splits, key=lambda s: (-len(s[0]), min(s[0]))
        ):
            moved = [p for p in parts if len(p) < len(before)]
            pulled = sorted(_compact(n) for p in moved for n in p)
            shown = ", ".join(pulled[:4]) + (
                f" (+{len(pulled) - 4})" if len(pulled) > 4 else ""
            )
            lines.append(f"    class[{len(before)}] -> {len(parts)}: {shown}")
        lines.append("")
    axis.text(
        0.0,
        1.0,
        "\n".join(lines).rstrip(),
        ha="left",
        va="top",
        fontsize=5.1,
        color=INK,
        family="monospace",
        linespacing=1.5,
    )


# --------------------------------------------------------------------------
# Artifact
# --------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(args: list[str], root: Path) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        return ""


IMPLEMENTATION_FILES = (
    "src/dt_adoc/reporting/design_alias.py",
    "src/dt_adoc/reporting/design_alias_figure.py",
    "src/dt_adoc/reporting/identifiability.py",
    "src/dt_adoc/reporting/structure.py",
    "src/dt_adoc/reporting/dynamics.py",
)


def _provenance(model_version: str, root: Path) -> dict[str, Any]:
    """Everything a reader needs to recompute these figures, or to detect drift.

    The condition-cfg map is the whole set, not only the plan's: an arm added to
    the model after this render changes what a candidate ranking means, and the
    staleness guard in ``tests/unit/test_design_alias.py`` compares the recorded
    set against the directory. This is the failure mode
    ``tests/unit/test_concordance.py`` was written for.
    """
    spec = resolve_model(model_version, root)
    digest = hashlib.sha256()
    for relative in IMPLEMENTATION_FILES:
        digest.update(relative.encode("utf-8"))
        path = root / relative
        digest.update(_sha256(path).encode("ascii") if path.is_file() else b"absent")
    return {
        "model_version": model_version,
        "git_commit": _git(["rev-parse", "HEAD"], root),
        "git_tree_dirty": bool(_git(["status", "--porcelain"], root)),
        "source_commit": source_commit(root),
        "python_version": platform.python_version(),
        "matplotlib_version": matplotlib.__version__,
        "implementation_files": list(IMPLEMENTATION_FILES),
        "implementation_digest": digest.hexdigest(),
        "network_bnd_sha256": _sha256(spec.network_bnd),
        "baseline_cfg_sha256": _sha256(spec.baseline_cfg),
        "node_dictionary_sha256": _sha256(spec.node_dictionary),
        "planned_design_yaml_sha256": _sha256(root / "config" / "planned_design.yaml"),
        "visualization_yaml_sha256": _sha256(root / "config" / "visualization.yaml"),
        "condition_cfg_sha256": {
            path.name: _sha256(path)
            for path in sorted(Path(spec.condition_dir).glob("*.cfg"))
        },
    }


CLAIM_BOUNDARIES = (
    (
        "Same colour means experimentally indistinguishable under the declared "
        "plan, never biologically equivalent."
    ),
    (
        "A design-equivalence class is a property of the arms, not of the "
        "biology; a measured divergence inside a class falsifies the aliasing."
    ),
    (
        "No simulation, horizon, rate or fitted parameter enters any class: "
        "every partition is exhaustive enumeration over the model's free "
        "variables."
    ),
    (
        "The plan is declared in config/planned_design.yaml, not recorded "
        "evidence; arms with no recorded observation are listed as "
        "planned_not_recorded."
    ),
    (
        "Latent placeholders are unknown in every arm. They are not resolved "
        "and they are not aliased."
    ),
)


def render_design_alias_artifact(
    output: Path | None = None,
    root: Path | None = None,
    *,
    variant: str | None = None,
) -> dict[str, Any]:
    """Render both figures, write every table behind them, and stamp provenance."""
    active_root = root or repo_root()
    document, _arms = load_plan(active_root, variant)
    model_version = document["model_version"]
    recorded = load_identifiability(model_version, active_root)
    facts = load_design_alias(active_root, variant, facts=recorded)
    enumerator = _Enumerator(model_version, active_root)
    candidates = candidate_fifth_arms(facts, active_root, enumerator=enumerator)
    summary = design_alias_summary(facts, candidates)
    shortlist = _shortlist(candidates)

    suffix = f"_{variant}" if variant else ""
    target = output or (
        active_root / "docs" / "assets" / f"adoc_design_alias_{model_version}{suffix}"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    tables = active_root / "docs" / "design_alias"
    tables.mkdir(parents=True, exist_ok=True)

    settings = load_visualization_config(active_root)
    view = build_network_view(
        model_version=model_version,
        view=VIEW_FULL,
        root=active_root,
        config=settings,
    )
    spec = resolve_model(model_version, active_root)
    edges = build_edge_views(nodes=list(view.nodes), model_spec=spec, config=settings)
    fills, borders = assign_class_colors(facts)
    badges = _global_badges(facts)
    short_labels = {n.node_id: n.short_label for n in view.nodes}

    written: list[Path] = []

    # ---- Figure A ----------------------------------------------------------
    figure_a = plt.figure(figsize=(13.6, 11.4))
    grid = figure_a.add_gridspec(
        2,
        2,
        height_ratios=[3.05, 1.0],
        width_ratios=[1.72, 1.0],
        hspace=0.17,
        wspace=0.06,
        left=0.022,
        right=0.985,
        top=0.915,
        bottom=0.058,
    )
    ax_network = figure_a.add_subplot(grid[0, :])
    ax_legend = figure_a.add_subplot(grid[1, 0])
    ax_breakdown = figure_a.add_subplot(grid[1, 1])

    _draw_network(ax_network, facts, view, edges, fills, borders, badges, short_labels)
    ax_legend.axis("off")
    ax_legend.legend(
        handles=_legend_handles(facts, fills, borders),
        loc="upper left",
        fontsize=6.0,
        frameon=False,
        ncol=2,
        handlelength=1.5,
        handleheight=1.0,
        labelspacing=0.55,
        columnspacing=1.2,
        title=(
            "Same colour = experimentally indistinguishable under the current design; "
            "NOT biologically equivalent."
        ),
        title_fontproperties={"weight": "bold", "size": 6.8},
    )
    _annotate_measured(ax_network, facts, view)
    ax_breakdown.set_title(
        "Each class opened into its Boolean functions",
        fontsize=6.6,
        fontweight="bold",
        loc="left",
        pad=6,
    )
    _draw_structural_breakdown(ax_breakdown, facts, fills)

    figure_a.suptitle(
        f"What the {summary['planned_conditions']}-arm ADOC plan can and cannot tell apart, "
        f"on the network it is measured in",
        fontsize=12.4,
        fontweight="bold",
        y=0.985,
    )
    figure_a.text(
        0.022,
        0.947,
        f"{model_version} - {summary['named_nodes']} nodes implement "
        f"{summary['global_effective_states']} distinct Boolean functions, of which the "
        f"{summary['planned_conditions']} planned arms "
        f"({summary['planned_cfgs']} condition cfgs) separate "
        f"{summary['design_effective_states']}. Largest indistinguishable class: "
        f"{summary['largest_design_class']} nodes, spanning epithelium, stroma and interface.",
        fontsize=7.0,
        color=MUTED,
        va="top",
    )
    figure_a.text(
        0.022,
        0.012,
        "Colour is computed from network.bnd and the condition cfgs by exhaustive "
        "enumeration over the model's free variables; no simulation, horizon, rate or "
        "fitted parameter enters it. Nodes are NOT collapsed: the question is where the\n"
        "indistinguishable nodes sit in the tissue. Same colour means this design cannot "
        "separate these nodes -- never that they are the same molecule, pathway or cell "
        "state. Method and the full list of what the colours do not mean: "
        "docs/design_alias_note.md.",
        fontsize=5.4,
        color=MUTED,
        va="bottom",
        linespacing=1.6,
    )

    for extension, options in (
        (".svg", {"metadata": {"Date": None}}),
        (".pdf", {"metadata": {"CreationDate": None}}),
        (".png", {"dpi": 220}),
    ):
        path = target.with_name(target.name + "_A" + extension)
        figure_a.savefig(path, format=extension[1:], **options)
        written.append(path)
    plt.close(figure_a)

    # ---- Figure B ----------------------------------------------------------
    figure_b = plt.figure(figsize=(13.6, 7.4))
    grid_b = figure_b.add_gridspec(
        1,
        2,
        width_ratios=[1.42, 1.0],
        wspace=0.14,
        left=0.175,
        right=0.985,
        top=0.855,
        bottom=0.095,
    )
    ax_bars = figure_b.add_subplot(grid_b[0, 0])
    ax_detail = figure_b.add_subplot(grid_b[0, 1])
    _draw_gain(ax_bars, facts, shortlist, fills)
    ax_detail.set_title(
        "What the leading arms actually pull apart",
        fontsize=7.2,
        fontweight="bold",
        loc="left",
        pad=8,
    )
    _draw_split_detail(ax_detail, facts, shortlist)

    best = summary["best_fifth_arms"]
    figure_b.suptitle(
        "Which of those couplings a fifth arm could break",
        fontsize=12.4,
        fontweight="bold",
        x=0.022,
        ha="left",
        y=0.975,
    )
    figure_b.text(
        0.022,
        0.925,
        f"{summary['candidates_evaluated']} candidate arms scored against the "
        f"{summary['planned_conditions']}-arm plan itself, not against the recorded "
        f"design. Candidates de-duplicated by the refinement they produce, so one bar "
        f"is one distinct experiment.\n"
        f"Largest marginal gain: +{summary['best_fifth_arm_gain']} classes "
        f"({len(best)} tied arms, every one of them HAND2 loss on some background). But "
        f"gain in classes is not the same currency as gain in what the experiment reads: "
        f"only {summary['candidates_separating_two_measured_nodes']} of "
        f"{summary['candidates_evaluated']} candidates\nseparate two nodes the "
        f"repository actually measures "
        f"({', '.join(_compact(n) for n in summary['measured_nodes'])}), "
        f"the best of them at +{summary['best_gain_among_arms_separating_measured_nodes']}, "
        f"and no HAND2-loss arm is among them.",
        fontsize=7.0,
        color=MUTED,
        va="top",
    )
    figure_b.text(
        0.022,
        0.012,
        "Gain is in design-equivalence classes: how many more of the model's Boolean "
        "functions the arms could tell apart. It is not a power calculation, an effect "
        "size, or a probability of detecting anything, and it says nothing about\n"
        "whether the perturbation is biologically achievable or ethically available. "
        "'Needs a new cfg' means no committed condition file has those input "
        "assignments; writing one is a model change and is not done here.",
        fontsize=5.4,
        color=MUTED,
        va="bottom",
        linespacing=1.6,
    )

    for extension, options in (
        (".svg", {"metadata": {"Date": None}}),
        (".pdf", {"metadata": {"CreationDate": None}}),
        (".png", {"dpi": 220}),
    ):
        path = target.with_name(target.name + "_B" + extension)
        figure_b.savefig(path, format=extension[1:], **options)
        written.append(path)
    plt.close(figure_b)

    artifacts = _write_tables(
        facts, candidates, badges, fills, tables, active_root, suffix
    )
    metadata = {
        "schema_version": "1.0",
        "plan_id": facts.plan_id,
        "plan_label": facts.plan_label,
        "variant": variant or "as_declared",
        "summary": summary,
        "claim_boundaries": list(CLAIM_BOUNDARIES),
        "class_colors": {
            min(members): {
                "fill": fills[members],
                "border": borders[members],
                "size": len(members),
                "members": sorted(members),
            }
            for members in fills
        },
        "figures": [
            {
                "path": str(path.relative_to(active_root)),
                "sha256": _sha256(path),
            }
            for path in written
        ],
        "tables": artifacts,
        "provenance": _provenance(model_version, active_root),
    }
    metadata_path = tables / f"design_alias_metadata{suffix}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    metadata["metadata_path"] = str(metadata_path.relative_to(active_root))
    return metadata


def _write_tables(
    facts: DesignAliasFacts,
    candidates: tuple[FifthArm, ...],
    badges: dict[str, str],
    fills: dict[tuple[str, ...], str],
    directory: Path,
    root: Path,
    suffix: str = "",
) -> list[dict[str, str]]:
    """The machine-readable figure: one row per node, per candidate, per arm.

    ``suffix`` is the variant marker, and it must reach every filename. Without
    it a ``--variant`` run rewrote the three as-declared tables with
    maternal-phase-only content while leaving the as-declared figures and the
    metadata that records those tables' sha256 untouched -- a figure and its own
    source data disagreeing, which is precisely what the staleness guard in
    ``tests/unit/test_design_alias.py`` exists to catch and could not have
    caught here, because the guard would have been comparing the variant's table
    against the default's recorded hash only on the next run.
    """
    written: list[dict[str, str]] = []

    def emit(stem: str, header: list[str], rows: list[list[Any]]) -> None:
        name = f"{stem}{suffix}.tsv"
        path = directory / name
        body = "\t".join(header) + "\n"
        body += "".join("\t".join(str(cell) for cell in row) + "\n" for row in rows)
        path.write_text(body, encoding="utf-8")
        written.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": _sha256(path),
                "rows": str(len(rows)),
            }
        )

    global_of = facts.global_class_of
    design_of = facts.design_class_of

    emit(
        "node_design_classes",
        [
            "node_id",
            "label",
            "compartment",
            "global_boolean_class",
            "global_class_size",
            "global_class_members",
            "design_class",
            "design_class_size",
            "design_class_members",
            "structurally_aliased",
            "design_aliased",
            "latent_interface_placeholder",
            "category",
            "structural_badge",
            "fill_color",
        ],
        [
            [
                node_id,
                facts.label_of.get(node_id, node_id),
                facts.compartment_of.get(node_id, ""),
                min(global_of[node_id]),
                len(global_of[node_id]),
                ";".join(sorted(global_of[node_id])),
                min(design_of[node_id]),
                len(design_of[node_id]),
                ";".join(sorted(design_of[node_id])),
                "true" if len(global_of[node_id]) > 1 else "false",
                # Design-aliased means merged by the design *beyond* whatever the
                # rules already merged. A node whose design class is exactly its
                # global class is not design-aliased, however large that class is.
                "true"
                if len(design_of[node_id]) > len(global_of[node_id])
                else "false",
                "true"
                if facts.category[node_id] == "interface_placeholder"
                else "false",
                facts.category[node_id],
                badges.get(node_id, ""),
                fills.get(design_of[node_id], NEUTRAL_FILL),
            ]
            for node_id in facts.node_ids
        ],
    )

    emit(
        "planned_arms",
        [
            "arm_id",
            "label",
            "condition_cfgs",
            "has_recorded_observation",
            "observation_sources",
            "interpretation",
        ],
        [
            [
                arm.arm_id,
                arm.label,
                ";".join(f"{phase}:{stem}" for phase, stem in arm.cfgs),
                "true" if arm.has_recorded_observation else "false",
                ";".join(arm.recorded_sources) or "(none)",
                arm.interpretation,
            ]
            for arm in facts.arms
        ],
    )

    emit(
        "candidate_fifth_arms",
        [
            "candidate_id",
            "label",
            "family",
            "committed_condition_cfg",
            "inputs_on",
            "baseline_design_classes",
            "design_classes_after",
            "gain",
            "classes_split",
            "classes_split_detail",
            "nodes_newly_distinguishable",
            "separates_measured_nodes",
            "measured_pairs_separated",
            "rationale",
        ],
        [
            [
                candidate.candidate_id,
                candidate.label,
                candidate.family,
                candidate.committed_cfg or "(none: would need a new cfg)",
                ";".join(sorted(k for k, v in candidate.inputs.items() if v))
                or "(none)",
                candidate.baseline_classes,
                candidate.classes_after,
                candidate.gain,
                len(candidate.splits),
                " | ".join(
                    f"{min(before)}[{len(before)}]->"
                    + "/".join(str(len(p)) for p in parts)
                    for before, parts in sorted(
                        candidate.splits, key=lambda s: (-len(s[0]), min(s[0]))
                    )
                )
                or "(none)",
                ";".join(candidate.newly_separable) or "(none)",
                "true" if candidate.separated_measured_pairs else "false",
                ";".join(
                    f"{left}|{right}"
                    for left, right in candidate.separated_measured_pairs
                )
                or "(none)",
                candidate.rationale,
            ]
            for candidate in candidates
        ],
    )

    return written
