"""The response-order figure: one row per node and first-switch direction.

Left panel: the empirical distribution, across the trajectories in which the
node switched that way, of the chosen position statistic (dot = median, thick
bar = middle 50 %, thin line = middle 95 %). Right panel: in how many
trajectories that happened, under the perturbation (bar) and in the matched
control (tick), so a node that switches in 20 % of trajectories never looks like
one that switches in all of them.

Adjacent rows whose order is unresolved, ``|P(upper first) - 0.5| < 0.1`` on at
least 50 trajectories where both switch in an identifiable order, are joined by a bracket in the gutter:
their vertical order is an artefact of sorting. This is a stated criterion on
``pairwise_precedence``, not a wave grouping.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dt_adoc.cascade.annotations import display_label

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"
DIRECTION_COLOR = {"on_to_off": BLUE, "off_to_on": ORANGE}
DIRECTION_TEXT = {"on_to_off": "turns OFF", "off_to_on": "turns ON"}
UNRESOLVED_HALF_WIDTH = 0.1
UNRESOLVED_MIN_BOTH = 50
AXIS_LABEL = {
    "normalized_time": "position in the trajectory's own response cascade, by time\n(0 = first switching node, 1 = last switching node)",
    "normalized_rank": "position in the trajectory's own response cascade, by rank\n(0 = first switching node, 1 = last switching node)",
    "absolute_time": "time of first switch after the perturbation (MaBoSS relative time, every rate 1; not hours)",
}


def unresolved_adjacent(rows: pd.DataFrame, precedence: pd.DataFrame) -> list[bool]:
    """For each adjacent pair of plotted rows: is their order unresolved?"""
    lookup = precedence.set_index(["node_a", "node_b"])
    out = []
    for upper, lower in zip(rows.node.iloc[:-1], rows.node.iloc[1:]):
        if upper == lower or (upper, lower) not in lookup.index:
            out.append(False)
            continue
        r = lookup.loc[(upper, lower)]
        out.append(
            bool(
                (r.n_a_first + r.n_b_first) >= UNRESOLVED_MIN_BOTH
                and abs(r.p_a_first - 0.5) < UNRESOLVED_HALF_WIDTH
            )
        )
    return out


def figure_rows(
    summary: pd.DataFrame, position: str
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """The rows to draw, the nodes that never switched, and the switching nodes not drawn.

    "Never switched" is read from ``p_switch == 0`` and nothing else. A node that
    switched but has no drawn row (its direction is below the display threshold,
    or the chosen position is undefined in every contributing trajectory) is
    reported as such, never as a non-switcher.
    """
    col = f"{position}_median"
    drawn = summary[
        (summary.direction != "none")
        & summary.shown_in_figure.astype(bool)
        & (summary[f"{position}_n"].fillna(0) > 0)
    ]
    rows = drawn.sort_values([col, "node"]).reset_index(drop=True)
    per_node = summary.drop_duplicates("node").set_index("node").p_switch
    never = sorted(per_node.index[per_node == 0])
    not_drawn = sorted(set(per_node.index[per_node > 0]) - set(rows.node))
    return rows, never, not_drawn


def control_direction_frequency(
    control_summary: pd.DataFrame, node: str, direction: str
) -> float:
    """Share of control trajectories in which ``node`` first switched in ``direction``.

    The comparator for one direction-specific perturbed row, on the same scale
    as its bar (``direction_share * p_switch``). A node the control reports but
    never switched that way is 0; a node the control does not report is NaN, and
    no tick is drawn.
    """
    rows = control_summary[control_summary.node == node]
    if rows.empty:
        return np.nan
    match = rows[rows.direction == direction]
    if match.empty:
        return 0.0
    row = match.iloc[0]
    return float(row.direction_share * row.p_switch)


def render_cascade(
    summary: pd.DataFrame,
    control_summary: pd.DataFrame,
    precedence: pd.DataFrame,
    annotations: dict,
    *,
    position: str,
    title: str,
    subtitle: str,
    footer: str,
    paths: list[Path],
) -> None:
    rows, never, not_drawn = figure_rows(summary, position)
    col = f"{position}_median"
    n = len(rows)
    height = max(4.0, 0.34 * n + 2.6)
    fig, (ax, bx) = plt.subplots(
        1,
        2,
        figsize=(12.5, height),
        sharey=True,
        gridspec_kw={"width_ratios": [4.2, 1.0], "wspace": 0.04},
    )
    for a in (ax, bx):
        a.set_facecolor(SURF)
        for side in ("top", "right"):
            a.spines[side].set_visible(False)
        a.spines["left"].set_color(INK2)
        a.spines["bottom"].set_color(INK2)
        a.tick_params(colors=INK2, labelsize=8)
        a.grid(axis="x", color=GRID, lw=0.6)
        a.set_axisbelow(True)
    y = np.arange(n)[::-1]
    for yi, r in zip(y, rows.itertuples()):
        c = DIRECTION_COLOR[r.direction]
        ax.plot(
            [getattr(r, f"{position}_q025"), getattr(r, f"{position}_q975")],
            [yi, yi],
            color=c,
            lw=1.2,
            alpha=0.75,
            solid_capstyle="round",
        )
        ax.plot(
            [getattr(r, f"{position}_q25"), getattr(r, f"{position}_q75")],
            [yi, yi],
            color=c,
            lw=5,
            solid_capstyle="round",
        )
        ax.plot(getattr(r, col), yi, "o", ms=6, color=SURF, mec=c, mew=1.8, zorder=3)
        bx.barh(yi, r.direction_share * r.p_switch, height=0.56, color=c, alpha=0.9)
        cp = control_direction_frequency(control_summary, r.node, r.direction)
        if np.isfinite(cp):
            bx.plot(
                [cp, cp],
                [yi - 0.36, yi + 0.36],
                color=INK,
                lw=1.6,
                clip_on=False,
                zorder=4,
            )
        bx.text(1.03, yi, f"{r.n_contributing}", va="center", fontsize=7, color=INK2)
    flags = unresolved_adjacent(rows, precedence)
    x0 = -0.06 if position != "absolute_time" else ax.get_xlim()[0]
    for i, flag in enumerate(flags):
        if flag:
            ax.plot(
                [x0, x0],
                [y[i] - 0.1, y[i + 1] + 0.1],
                color=MUTED,
                lw=2.2,
                clip_on=False,
                solid_capstyle="butt",
            )
    labels = []
    for r in rows.itertuples():
        text = display_label(
            annotations.get(
                r.node,
                {
                    "label": r.node,
                    "marker_genes": [],
                    "is_composite": False,
                    "composed_of": [],
                },
            )
        )
        if r.mixed_direction:
            text += f"  ({DIRECTION_TEXT[r.direction]}, {r.direction_share:.0%} of switches)"
        labels.append(text)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.4)
    for tick, r in zip(ax.get_yticklabels(), rows.itertuples()):
        tick.set_color(INK)
        if annotations.get(r.node, {}).get("is_phenotype"):
            tick.set_fontweight("bold")
    if position != "absolute_time":
        ax.set_xlim(-0.08, 1.04)
    ax.set_ylim(-0.7, n - 0.3)
    ax.set_xlabel(AXIS_LABEL[position], fontsize=8.5, color=INK)
    bx.set_xlim(-0.04, 1.0)
    bx.set_xticks([0, 0.5, 1.0])
    bx.set_xlabel(
        "share of trajectories\nbar = perturbed · tick = control\n(number = n contributing)",
        fontsize=7.5,
        color=INK,
    )
    handles = [
        plt.Line2D([], [], color=BLUE, lw=5, label="turns OFF"),
        plt.Line2D([], [], color=ORANGE, lw=5, label="turns ON"),
        plt.Line2D([], [], color=MUTED, lw=2.2, label="order with next row unresolved"),
    ]
    ax.legend(
        handles=handles,
        frameon=False,
        fontsize=8,
        loc="lower left",
        bbox_to_anchor=(0.0, 1.0),
        ncol=3,
        borderaxespad=0.2,
    )
    top = 1 - 2.0 / height
    fig.subplots_adjust(
        left=0.42, right=0.965, top=top, bottom=max(0.07, 1.25 / height)
    )
    fig.text(
        0.01, 1 - 0.18 / height, title, fontsize=11, color=INK, va="top", weight="bold"
    )
    fig.text(0.01, 1 - 0.46 / height, subtitle, fontsize=7.8, color=INK2, va="top")
    tail = footer
    if not_drawn:
        tail = (
            f"Switched but not drawn ({len(not_drawn)}; below the display threshold or "
            "no defined position, see node_summary.tsv): "
            + ", ".join(not_drawn)
            + "\n"
            + tail
        )
    if never:
        tail = (
            f"Never switched in the perturbed arm ({len(never)}): "
            + ", ".join(never)
            + "\n"
            + tail
        )
    fig.text(0.01, 0.012, tail, fontsize=7, color=INK2, va="bottom", wrap=True)
    fig.patch.set_facecolor(SURF)
    for path in paths:
        fig.savefig(
            path,
            dpi=170,
            facecolor=SURF,
            metadata={"Date": None} if path.suffix == ".svg" else None,
        )
    plt.close(fig)
