"""Render the concordance figure from the tracked figure source data.

Reads `docs/concordance/figure_source_data.tsv` rather than recomputing, so the
figure and the table cannot disagree: a mark that is not in the table cannot be
drawn, and the reader can check every mark against a tracked file.

Panel C draws the **quotient** of the model's dependency graph under Boolean
function equivalence, restricted to the nodes that carry the panel A and B
contrasts. Drawing the 35 raw carrying-path nodes would be unreadable and, worse,
would imply 35 independent mechanisms where the rule set implements far fewer:
nine epithelial nodes compute one function, six stromal nodes compute another,
and five progesterone-arm nodes compute a third. Collapsing them is not a
simplification for legibility, it is the finding.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from dt_adoc.concordance.figure import (
    ARM_LABELS,
    COVERAGE_COLORS,
    GRID,
    SERIES_CONVERGED,
    SERIES_DECLARED,
    SERIES_OBSERVED,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    scorecard_entries,
)

ARM_ORDER = ("untreated", "hormone_treated", "mifepristone")

#: Segment order for panel D. ``structural_falsification`` is listed although it
#: is empty: a class that can never appear would be a promise, and one that is
#: empty *in this analysis* is a result worth being able to see.
COVERAGE_ORDER = (
    "not_expressible_by_model_class",
    "not_assessable_with_current_data",
    "calibration_circular_agreement",
    "directional_agreement",
    "partial_agreement",
    "disagreement",
    "structural_falsification",
)

COVERAGE_LABELS = {
    "not_expressible_by_model_class": "Not expressible by model class\n(Boolean: no geometry, flux, populations)",
    "not_assessable_with_current_data": "Not assessable with current data\n(no node, no mapping, or data missing)",
    "calibration_circular_agreement": "Calibration / circular agreement\n(agrees with what built or filtered it)",
    "directional_agreement": "Directional agreement\n(ordering only; no magnitude)",
    "partial_agreement": "Partial agreement\n(direction agrees, magnitude fails)",
    "disagreement": "Disagreement",
    "structural_falsification": "Structural falsification\n(none found: see the analysis)",
}

#: Panel C node boxes. ``members`` names the real model nodes each box stands
#: for, so the drawing is checkable against ``network.bnd``: a box that claims to
#: be an alias class must actually be one, its ``n`` must equal its membership,
#: and every drawn edge must be a dependency the model computes between the two
#: boxes' members. ``tests/unit/test_concordance.py`` asserts all three, so the
#: panel cannot drift away from the model it depicts.
#:
#: ``kind`` separates the two reasons a box can hold several nodes, because the
#: figure's ``xN`` badge means one of them and not the other:
#:
#: * ``"alias"`` -- the members compute the IDENTICAL Boolean function. This is a
#:   claim about the model, it earns the ``xN`` badge, and it is asserted against
#:   ``facts.alias_classes``.
#: * ``"grouping"`` -- several DISTINCT nodes drawn in one box to save space.
#:   This claims nothing and carries no badge. ``IN_EMBRYO`` is the only one:
#:   the three embryo inputs are separate variables, and an earlier revision gave
#:   that box an ``x3`` badge, which asserted a degeneracy the model does not
#:   have, in the panel whose whole purpose is showing which readouts are not
#:   independent.
#:
#: Each entry is
#: ``key: (x, y, display label, member count, members, evidence class)``.
#: Coordinates are hand-set because an automatic layout of a 7-layer signalling
#: cascade is unreadable, and the layering is itself information.
_EPI = "epithelial"
_STR = "stromal"
_INT = "interface"
_IN = "input"
_OUT = "output"

PANEL_C_NODES: dict[str, dict] = {
    "IN_E2": {
        "x": 0.0,
        "y": 4.4,
        "label": "E2",
        "n": 1,
        "members": ["IN_E2"],
        "kind": "alias",
        "cls": "protocol_input",
        "comp": _IN,
    },
    "IN_PROGESTIN": {
        "x": 0.0,
        "y": 3.3,
        "label": "Progestin\n(MPA)",
        "n": 1,
        "members": ["IN_PROGESTIN"],
        "kind": "alias",
        "cls": "protocol_input",
        "comp": _IN,
    },
    "IN_cAMP": {
        "x": 0.0,
        "y": 2.2,
        "label": "cAMP\n= S_PKA",
        "n": 2,
        "members": ["IN_cAMP", "S_PKA"],
        "kind": "alias",
        "cls": "protocol_input",
        "comp": _IN,
    },
    "IN_MIFEPRISTONE": {
        "x": 0.0,
        "y": 1.1,
        "label": "Mifepristone",
        "n": 1,
        "members": ["IN_MIFEPRISTONE"],
        "kind": "alias",
        "cls": "protocol_input",
        "comp": _IN,
    },
    "IN_EMBRYO": {
        "x": 0.0,
        "y": -0.3,
        "label": "Embryo present /\ncompetent / contact",
        "n": 3,
        "members": [
            "IN_EMBRYO_PRESENT",
            "IN_TROPHECTODERM_COMPETENT",
            "IN_EMBRYO_CONTACT",
        ],
        "kind": "grouping",
        "cls": "protocol_input",
        "comp": _IN,
    },
    "PGR_CLASS": {
        "x": 1.6,
        "y": 2.7,
        "label": "PGR arm\nE_PGR = E_IHH = S_PGR\n= S_NR2F2 = S_BMP2",
        "n": 5,
        "members": ["E_PGR", "E_IHH", "S_PGR", "S_NR2F2", "S_BMP2"],
        "kind": "alias",
        "cls": "literature_derived",
        "comp": _STR,
    },
    "SECRETORY_CLASS": {
        "x": 3.2,
        "y": 4.4,
        "label": "Epithelial secretory program\nE_SECRETORY_STATE = E_PAEP\n= PC6 = HBEGF = SPP1 = ITGAVB3/5 ...",
        "n": 9,
        "members": [
            "E_SECRETORY_STATE",
            "E_PAEP",
            "E_PC6",
            "E_DAG1_CLEAVED",
            "E_MUC1_SLEX",
            "E_HBEGF",
            "E_SPP1_EXPR",
            "E_ITGAVB3_5",
            "E_ANXA2_ACTIN",
        ],
        "kind": "alias",
        "cls": "adoc_measured",
        "comp": _EPI,
    },
    "DECIDUAL_CLASS": {
        "x": 3.2,
        "y": 1.5,
        "label": "Stromal decidual program\nS_DECIDUALIZED = S_PRL\n= S_IGFBP1 = S_SPP1 = S_TAZ_ECM",
        "n": 6,
        "members": [
            "S_DECIDUALIZED",
            "S_PRL",
            "S_IGFBP1",
            "S_SPP1",
            "S_TAZ_ECM",
            "OUT_STROMAL_DECIDUALIZED",
        ],
        "kind": "alias",
        "cls": "adoc_measured",
        "comp": _STR,
    },
    "S_HAND2": {
        "x": 3.2,
        "y": 0.3,
        "label": "S_HAND2",
        "n": 1,
        "members": ["S_HAND2"],
        "kind": "alias",
        "cls": "literature_derived",
        "comp": _STR,
    },
    "LIF_CLASS": {
        "x": 4.9,
        "y": 5.4,
        "label": "LIF axis\nE_LIF = E_GP130_STAT3\n= E_CD98_CD9",
        "n": 3,
        "members": ["E_LIF", "E_GP130_STAT3", "E_CD98_CD9"],
        "kind": "alias",
        "cls": "literature_derived",
        "comp": _EPI,
    },
    "ANTIADH_CLASS": {
        "x": 4.9,
        "y": 3.6,
        "label": "Anti-adhesive surface\nE_PODXL = E_DAG1_FULL\n= E_MUC1_BARRIER",
        "n": 3,
        "members": ["E_PODXL", "E_DAG1_FULL", "E_MUC1_BARRIER"],
        "kind": "alias",
        "cls": "literature_derived",
        "comp": _EPI,
    },
    "RELAY_SPP1": {
        "x": 4.9,
        "y": 2.4,
        "label": "SPP1 relay\nistate 0.70",
        "n": 1,
        "members": ["X_INTERFACE_SPP1_RELAY"],
        "kind": "alias",
        "cls": "hand_set_free",
        "comp": _INT,
    },
    "X_SPP1_LUMEN_FREE": {
        "x": 4.9,
        "y": 1.3,
        "label": "X_SPP1_\nLUMEN_FREE",
        "n": 1,
        "members": ["X_SPP1_LUMEN_FREE"],
        "kind": "alias",
        "cls": "literature_derived",
        "comp": _INT,
    },
    "RELAY_REDUNDANT": {
        "x": 4.9,
        "y": 0.2,
        "label": "Redundant relay\nistate 0.40",
        "n": 1,
        "members": ["X_INTERFACE_REDUNDANT_RELAY"],
        "kind": "alias",
        "cls": "hand_set_free",
        "comp": _INT,
    },
    "X_MECH_ECM": {
        "x": 4.9,
        "y": -0.9,
        "label": "X_MECHANICAL_\nPERMISSIVE_ECM",
        "n": 1,
        "members": ["X_MECHANICAL_PERMISSIVE_ECM"],
        "kind": "alias",
        "cls": "literature_derived",
        "comp": _INT,
    },
    "RECEPTIVE_CLASS": {
        "x": 6.6,
        "y": 4.8,
        "label": "E_RECEPTIVE_SURFACE\n= OUT_EPITHELIAL_RECEPTIVE",
        "n": 2,
        "members": ["E_RECEPTIVE_SURFACE", "OUT_EPITHELIAL_RECEPTIVE"],
        "kind": "alias",
        "cls": "composite_output",
        "comp": _OUT,
    },
    "X_ANTIADH_ROUTE": {
        "x": 6.6,
        "y": 3.6,
        "label": "X_ANTIADHESIVE_\nROUTE",
        "n": 1,
        "members": ["X_ANTIADHESIVE_ROUTE"],
        "kind": "alias",
        "cls": "literature_derived",
        "comp": _INT,
    },
    "X_ROUTE_SPP1": {
        "x": 6.6,
        "y": 2.2,
        "label": "X_ADHESION_\nROUTE_SPP1",
        "n": 1,
        "members": ["X_ADHESION_ROUTE_SPP1"],
        "kind": "alias",
        "cls": "literature_derived",
        "comp": _INT,
    },
    "X_ROUTE_REDUNDANT": {
        "x": 6.6,
        "y": 0.8,
        "label": "X_ADHESION_ROUTE_\nREDUNDANT",
        "n": 1,
        "members": ["X_ADHESION_ROUTE_REDUNDANT"],
        "kind": "alias",
        "cls": "literature_derived",
        "comp": _INT,
    },
    "OUT_COMPETENCE": {
        "x": 8.3,
        "y": 3.0,
        "label": "OUT_MATERNAL_\nADHESION_COMPETENCE",
        "n": 1,
        "members": ["OUT_MATERNAL_ADHESION_COMPETENCE"],
        "kind": "alias",
        "cls": "composite_output",
        "comp": _OUT,
    },
    "OUT_ADHESION": {
        "x": 8.3,
        "y": 1.0,
        "label": "OUT_STABLE_\nADHESION",
        "n": 1,
        "members": ["OUT_STABLE_ADHESION"],
        "kind": "alias",
        "cls": "composite_output",
        "comp": _OUT,
    },
}

#: ``(source, target, kind)``. ``kind`` is ``activation``, ``inhibition`` or
#: ``never_binding`` -- the last is an inhibition the exhaustive enumeration
#: shows can never suppress its target in any state.
#:
#: ``EDGE_CURVE`` routes specific long edges around unrelated boxes. Only
#: geometry: a curved edge asserts nothing a straight one does not.
EDGE_CURVE: dict[tuple[str, str], float] = {
    ("IN_EMBRYO", "OUT_ADHESION"): -0.16,
    # A true right-to-left dependency: E_LIF feeds E_ITGAVB3_5, which sits in the
    # secretory class one column upstream. Curved so it reads as a feedback edge
    # rather than a layout error.
    ("LIF_CLASS", "SECRETORY_CLASS"): 0.16,
}

PANEL_C_EDGES: tuple[tuple[str, str, str], ...] = (
    ("IN_PROGESTIN", "PGR_CLASS", "activation"),
    ("IN_MIFEPRISTONE", "PGR_CLASS", "inhibition"),
    ("IN_E2", "SECRETORY_CLASS", "activation"),
    ("PGR_CLASS", "SECRETORY_CLASS", "activation"),
    ("PGR_CLASS", "DECIDUAL_CLASS", "activation"),
    ("IN_cAMP", "DECIDUAL_CLASS", "activation"),
    ("PGR_CLASS", "S_HAND2", "activation"),
    ("SECRETORY_CLASS", "LIF_CLASS", "activation"),
    ("SECRETORY_CLASS", "ANTIADH_CLASS", "inhibition"),
    ("SECRETORY_CLASS", "X_SPP1_LUMEN_FREE", "activation"),
    ("DECIDUAL_CLASS", "X_SPP1_LUMEN_FREE", "activation"),
    ("DECIDUAL_CLASS", "X_MECH_ECM", "activation"),
    ("LIF_CLASS", "RECEPTIVE_CLASS", "activation"),
    ("SECRETORY_CLASS", "RECEPTIVE_CLASS", "activation"),
    ("ANTIADH_CLASS", "X_ANTIADH_ROUTE", "activation"),
    ("RECEPTIVE_CLASS", "X_ROUTE_SPP1", "activation"),
    ("X_SPP1_LUMEN_FREE", "X_ROUTE_SPP1", "activation"),
    ("RELAY_SPP1", "X_ROUTE_SPP1", "activation"),
    ("RECEPTIVE_CLASS", "X_ROUTE_REDUNDANT", "activation"),
    ("RELAY_REDUNDANT", "X_ROUTE_REDUNDANT", "activation"),
    ("X_ROUTE_SPP1", "OUT_COMPETENCE", "activation"),
    ("X_ROUTE_REDUNDANT", "OUT_COMPETENCE", "activation"),
    ("RECEPTIVE_CLASS", "OUT_COMPETENCE", "activation"),
    ("DECIDUAL_CLASS", "OUT_COMPETENCE", "activation"),
    ("X_MECH_ECM", "OUT_COMPETENCE", "activation"),
    ("X_ANTIADH_ROUTE", "OUT_COMPETENCE", "never_binding"),
    ("OUT_COMPETENCE", "OUT_ADHESION", "activation"),
    ("IN_EMBRYO", "OUT_ADHESION", "activation"),
    # Completeness. These seven were omitted from an earlier revision of this
    # layout and were found by the test that compares the drawing against every
    # dependency the model computes between the nodes drawn here. A mechanism
    # panel that silently drops a route into the endpoint overstates how well the
    # displayed structure explains the prediction.
    ("IN_cAMP", "PGR_CLASS", "activation"),
    ("LIF_CLASS", "SECRETORY_CLASS", "activation"),
    ("X_SPP1_LUMEN_FREE", "RECEPTIVE_CLASS", "activation"),
    ("SECRETORY_CLASS", "X_ROUTE_SPP1", "activation"),
    ("SECRETORY_CLASS", "X_ROUTE_REDUNDANT", "activation"),
    ("LIF_CLASS", "X_ROUTE_REDUNDANT", "activation"),
    # The anti-adhesive arm's veto on the receptive surface is never binding
    # too, exactly like its veto on adhesion competence: pinning these three off
    # changes no output in any enumerated state. Drawing it struck through is the
    # point -- the arm is inert on both of its routes, not just one.
    ("ANTIADH_CLASS", "RECEPTIVE_CLASS", "never_binding"),
)

NODE_FACE = {
    "adoc_measured": "#cfe0f7",
    "hand_set_free": "#fbdccd",
    "literature_derived": "#f2f1ed",
    "composite_output": "#ffffff",
    "protocol_input": "#e6e5e0",
}
NODE_EDGE = {
    "adoc_measured": SERIES_OBSERVED,
    "hand_set_free": SERIES_CONVERGED,
    "literature_derived": "#9a9992",
    "composite_output": TEXT_PRIMARY,
    "protocol_input": "#7d7c76",
}


def _read_source_data(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _panel_a(ax, records: list[dict[str, str]]) -> None:
    """Observed adhesion against simulation, at both horizons."""
    by_arm: dict[str, dict[str, dict[str, str]]] = {}
    for row in records:
        if row["panel"] != "A":
            continue
        by_arm.setdefault(row["arm"], {})[row["quantity"]] = row

    positions = range(len(ARM_ORDER))
    for index, arm in zip(positions, ARM_ORDER):
        entries = by_arm.get(arm, {})
        observed = entries.get("observed_proportion")
        if observed is not None:
            value = float(observed["value"])
            low = float(observed["ci_low"])
            high = float(observed["ci_high"])
            ax.errorbar(
                index - 0.17,
                value,
                yerr=[[value - low], [high - value]],
                fmt="o",
                markersize=9,
                color=SERIES_OBSERVED,
                ecolor=SERIES_OBSERVED,
                elinewidth=2,
                capsize=5,
                zorder=3,
            )
            ax.annotate(
                f"{observed['n']}\n{value:.2f}",
                (index - 0.17, high),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=8.2,
                color=TEXT_PRIMARY,
            )
        for offset, quantity, color, marker in (
            (0.17, "simulated_converged", SERIES_CONVERGED, "s"),
            (0.42, "simulated_declared", SERIES_DECLARED, "^"),
        ):
            entry = entries.get(quantity)
            if entry is None:
                continue
            value = float(entry["value"])
            ax.plot(
                index + offset,
                value,
                marker,
                markersize=9,
                color=color,
                zorder=3,
            )
            label = f"{value:.6f}" if 0.0 < value < 0.001 else f"{value:.3f}"
            ax.annotate(
                label,
                (index + offset, value),
                textcoords="offset points",
                xytext=(0, 9 if value < 0.9 else -15),
                ha="center",
                fontsize=8.2,
                color=TEXT_PRIMARY,
            )

    ax.set_xticks(list(positions))
    ax.set_xticklabels(
        [
            f"{ARM_LABELS[a]}\n({by_arm.get(a, {}).get('observed_proportion', {}).get('evidence_role', '')})"
            for a in ARM_ORDER
        ],
        fontsize=9,
    )
    ax.set_ylim(-0.08, 1.12)
    ax.set_ylabel("Stable adhesion\n(proportion / trajectory frequency)", fontsize=9.5)
    ax.set_title(
        "A  Functional endpoint: observed vs simulated",
        loc="left",
        fontsize=11.5,
        fontweight="bold",
        color=TEXT_PRIMARY,
    )
    ax.grid(axis="y", color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    ax.legend(
        handles=[
            Line2D(
                [],
                [],
                marker="o",
                linestyle="",
                color=SERIES_OBSERVED,
                markersize=8,
                label="Observed (Wilson 95% CI, per embryo)",
            ),
            Line2D(
                [],
                [],
                marker="s",
                linestyle="",
                color=SERIES_CONVERGED,
                markersize=8,
                label="Simulated, converged horizon",
            ),
            Line2D(
                [],
                [],
                marker="^",
                linestyle="",
                color=SERIES_DECLARED,
                markersize=8,
                label="Simulated, declared horizon",
            ),
        ],
        fontsize=8,
        loc="upper left",
        frameon=False,
    )
    ax.annotate(
        "0.82 = 1-(1-0.70)(1-0.40): two hand-set relay istates, not a fit; the "
        "observed 9/19 CI excludes it.\n"
        "The declared horizon reads ~4000x early and produces no reduction at all.\n"
        "HT+mifepristone declared is NOT ASSESSABLE: the simulated regimen omits "
        "the recorded 24 h maternal phase.",
        xy=(0.5, -0.38),
        xycoords="axes fraction",
        ha="center",
        fontsize=7.8,
        color=TEXT_SECONDARY,
    )


def _panel_b(ax, entries) -> None:
    """Direction-only molecular scorecard. Deliberately not a value heatmap.

    The status string comes from each row's concordance class, so a readout the
    matrix records as unassessable cannot appear here as an agreement.
    """
    ax.axis("off")
    ax.set_title(
        "B  Molecular readouts: direction only",
        loc="left",
        fontsize=11.5,
        fontweight="bold",
        color=TEXT_PRIMARY,
    )
    y = 0.95
    for entry in entries:
        assessable = "NOT ASSESSABLE" not in entry.status
        status_color = SERIES_CONVERGED if assessable else "#8a1f1d"
        ax.text(
            0.0,
            y,
            entry.label,
            fontsize=9.4,
            fontweight="bold",
            color=TEXT_PRIMARY,
            transform=ax.transAxes,
        )
        ax.text(
            1.0,
            y,
            entry.status,
            fontsize=8.6,
            fontweight="bold",
            ha="right",
            color=status_color,
            transform=ax.transAxes,
        )
        ax.text(
            0.0,
            y - 0.045,
            f"observed: {entry.observed_direction}",
            fontsize=7.6,
            color=TEXT_SECONDARY,
            transform=ax.transAxes,
        )
        ax.text(
            0.0,
            y - 0.085,
            f"magnitude: {entry.magnitude_comparable}",
            fontsize=7.6,
            color=TEXT_SECONDARY,
            transform=ax.transAxes,
        )
        ax.text(
            0.0,
            y - 0.125,
            f"role: {entry.evidence_role}",
            fontsize=7.6,
            color=TEXT_SECONDARY,
            transform=ax.transAxes,
        )
        ax.text(
            0.0,
            y - 0.165,
            entry.footnote,
            fontsize=7.6,
            style="italic",
            color=TEXT_SECONDARY,
            transform=ax.transAxes,
        )
        y -= 0.225
    ax.text(
        0.0,
        -0.09,
        "No concentration is compared numerically to a Boolean probability:\n"
        "no validated observation model exists to relate them. Two of the three\n"
        "secreted readouts are one Boolean function, so they are not independent.",
        fontsize=7.8,
        color=TEXT_SECONDARY,
        transform=ax.transAxes,
    )


def _panel_c(ax, records: list[dict[str, str]]) -> None:
    """The reduced mechanism, as the quotient under Boolean equivalence.

    Every label, member roster, collapse count, evidence class and edge polarity
    is read from ``figure_source_data.tsv``. Only the box coordinates come from
    ``PANEL_C_NODES``, because a layout is a drawing decision and carries no
    scientific claim. So the panel cannot assert a mechanism the tracked data
    does not contain, and a rebuild that changes the model changes the drawing.
    """
    boxes = {
        row["arm"]: {
            "label": row["value"].replace("\\n", "\n"),
            "n": int(row["n"]),
            # The source data packs the evidence class and the box kind into
            # one column; split them back out rather than letting the combined
            # string reach the palette lookup.
            "cls": row["unit"].split(";")[0].strip(),
            "kind": row["unit"].split("box_kind=")[-1].strip(),
            "members": row["evidence_role"].split(";"),
        }
        for row in records
        if row["panel"] == "C" and row["quantity"] == "mechanism_node"
    }
    edges = [
        (*row["arm"].split("->"), row["value"])
        for row in records
        if row["panel"] == "C" and row["quantity"] == "mechanism_edge"
    ]
    missing = set(boxes) ^ set(PANEL_C_NODES)
    if missing:
        raise ValueError(
            f"panel C source data and layout disagree on boxes: {sorted(missing)}"
        )
    ax.axis("off")
    ax.set_xlim(-0.95, 9.35)
    ax.set_ylim(-1.95, 6.3)
    ax.set_title(
        "C  Mechanism behind the predictions, with identical Boolean functions collapsed",
        loc="left",
        fontsize=11.5,
        fontweight="bold",
        color=TEXT_PRIMARY,
    )

    half_w, half_h = 0.62, 0.34
    for edge_from, edge_to, kind in edges:
        source = PANEL_C_NODES[edge_from]
        target = PANEL_C_NODES[edge_to]
        x0, y0 = source["x"] + half_w, source["y"]
        x1, y1 = target["x"] - half_w, target["y"]
        if kind == "never_binding":
            ax.annotate(
                "",
                xy=(x1, y1),
                xytext=(x0, y0),
                arrowprops={
                    "arrowstyle": "-",
                    "color": "#c0403f",
                    "linewidth": 1.4,
                    "linestyle": (0, (3, 3)),
                    "shrinkA": 2,
                    "shrinkB": 2,
                },
            )
            ax.plot(
                [(x0 + x1) / 2 - 0.12, (x0 + x1) / 2 + 0.12],
                [(y0 + y1) / 2 + 0.12, (y0 + y1) / 2 - 0.12],
                color="#c0403f",
                linewidth=1.8,
            )
        else:
            ax.annotate(
                "",
                xy=(x1, y1),
                xytext=(x0, y0),
                arrowprops={
                    "arrowstyle": "-|>" if kind == "activation" else "-[",
                    "color": "#6f6e68" if kind == "activation" else "#c0403f",
                    "linewidth": 1.1,
                    "shrinkA": 2,
                    "shrinkB": 2,
                    "connectionstyle": (
                        f"arc3,rad={EDGE_CURVE[(edge_from, edge_to)]}"
                        if (edge_from, edge_to) in EDGE_CURVE
                        else "arc3,rad=0"
                    ),
                },
            )

    for key, layout in PANEL_C_NODES.items():
        spec = dict(layout)
        spec.update(boxes[key])
        face = NODE_FACE[spec["cls"]]
        edge = NODE_EDGE[spec["cls"]]
        box = mpatches.FancyBboxPatch(
            (spec["x"] - half_w, spec["y"] - half_h),
            2 * half_w,
            2 * half_h,
            boxstyle="round,pad=0.03,rounding_size=0.07",
            facecolor=face,
            edgecolor=edge,
            linewidth=2.0 if spec["cls"] in {"adoc_measured", "hand_set_free"} else 1.1,
            linestyle="--" if spec["cls"] == "hand_set_free" else "-",
            zorder=2,
        )
        ax.add_patch(box)
        ax.text(
            spec["x"],
            spec["y"],
            spec["label"],
            ha="center",
            va="center",
            fontsize=6.0,
            color=TEXT_PRIMARY,
            zorder=3,
            linespacing=1.25,
        )
        if spec["n"] > 1 and spec["kind"] == "alias":
            ax.text(
                spec["x"] + half_w - 0.04,
                spec["y"] + half_h - 0.03,
                f"x{spec['n']}",
                ha="right",
                va="top",
                fontsize=6.2,
                fontweight="bold",
                color=SERIES_CONVERGED,
                zorder=4,
            )

    ax.legend(
        handles=[
            mpatches.Patch(
                facecolor=NODE_FACE["adoc_measured"],
                edgecolor=NODE_EDGE["adoc_measured"],
                linewidth=2,
                label="Contains an ADOC-measured node (E_PAEP, S_IGFBP1)",
            ),
            mpatches.Patch(
                facecolor=NODE_FACE["hand_set_free"],
                edgecolor=NODE_EDGE["hand_set_free"],
                linewidth=2,
                linestyle="--",
                label="Hand-set free assumption (relay istate)",
            ),
            mpatches.Patch(
                facecolor=NODE_FACE["literature_derived"],
                edgecolor=NODE_EDGE["literature_derived"],
                label="Literature-curated rule",
            ),
            mpatches.Patch(
                facecolor=NODE_FACE["composite_output"],
                edgecolor=NODE_EDGE["composite_output"],
                label="Composite / latent output (never measured)",
            ),
            mpatches.Patch(
                facecolor=NODE_FACE["protocol_input"],
                edgecolor=NODE_EDGE["protocol_input"],
                label="Protocol input (set by the schedule)",
            ),
            Line2D(
                [],
                [],
                color="#c0403f",
                linestyle=(0, (3, 3)),
                linewidth=1.6,
                label="Inhibition that can never bind (verified over all 524,288 states)",
            ),
        ],
        fontsize=7.6,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.015),
        frameon=False,
        ncol=3,
    )
    ax.text(
        -0.9,
        6.15,
        "xN marks nodes collapsed because they compute the IDENTICAL Boolean function "
        "(35 distinct functions across 59 nodes).\n"
        "A box without a badge groups distinct nodes for layout only and claims no "
        "degeneracy.\n"
        "No scRNA-supported state appears: the repository holds no annotated object to support one.",
        fontsize=7.6,
        color=TEXT_SECONDARY,
        va="top",
    )


def _panel_d(ax, records: list[dict[str, str]]) -> None:
    """Coverage of all curated rows, so the other panels get a denominator."""
    counts = {row["arm"]: int(row["value"]) for row in records if row["panel"] == "D"}
    total = sum(counts.values())
    left = 0.0
    for key in COVERAGE_ORDER:
        value = counts.get(key, 0)
        if not value:
            continue
        ax.barh(
            0,
            value,
            left=left,
            height=0.5,
            color=COVERAGE_COLORS[key],
            edgecolor=SURFACE,
            linewidth=2,
        )
        ax.annotate(
            str(value),
            (left + value / 2, 0),
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#ffffff" if value > 3 else TEXT_PRIMARY,
        )
        left += value

    ax.set_xlim(0, total)
    ax.set_ylim(-0.6, 0.6)
    ax.set_yticks([])
    ax.set_xlabel(f"curated matrix rows (n = {total})", fontsize=9)
    ax.set_title(
        "D  What fraction of the ADOC evidence the model can touch at all",
        loc="left",
        fontsize=11.5,
        fontweight="bold",
        color=TEXT_PRIMARY,
    )
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.legend(
        handles=[
            mpatches.Patch(color=COVERAGE_COLORS[k], label=COVERAGE_LABELS[k])
            for k in COVERAGE_ORDER
            if counts.get(k, 0)
        ],
        fontsize=7.6,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.95),
        ncol=3,
        frameon=False,
    )


def render(
    *,
    source_data: Path,
    destination: Path,
    provenance: dict,
    rows: list | None = None,
) -> Path:
    """Draw the figure and write its metadata sidecar."""
    records = _read_source_data(source_data)

    fig = plt.figure(figsize=(15.5, 13.2), facecolor=SURFACE)
    grid = fig.add_gridspec(
        3,
        2,
        height_ratios=[0.95, 1.55, 0.20],
        hspace=0.50,
        wspace=0.20,
        left=0.065,
        right=0.978,
        top=0.940,
        bottom=0.135,
    )
    _panel_a(fig.add_subplot(grid[0, 0]), records)
    if rows is None:
        from dt_adoc.concordance.table import build_rows_from_table

        rows = build_rows_from_table()
    _panel_b(fig.add_subplot(grid[0, 1]), scorecard_entries(rows))
    _panel_c(fig.add_subplot(grid[1, :]), records)
    _panel_d(fig.add_subplot(grid[2, :]), records)

    fig.suptitle(
        "ADOC digital twin: model-data concordance and the mechanism behind each prediction",
        fontsize=14,
        fontweight="bold",
        color=TEXT_PRIMARY,
        x=0.065,
        ha="left",
        y=0.985,
    )
    fig.text(
        0.065,
        0.962,
        f"{provenance['model_version']} - exploratory - "
        f"{provenance['trajectory_count']} trajectories x {len(provenance['seeds'])} seeds - "
        "MaBoSS time is dimensionless - calibration agreement is not validation",
        fontsize=9,
        color=TEXT_SECONDARY,
        ha="left",
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=200, facecolor=SURFACE)
    plt.close(fig)

    # Repository-relative, never the author's absolute path: an artifact that
    # records where a file happened to live on one machine is not a pointer a
    # reader can follow.
    from dt_adoc.model.provenance import repo_root

    root = repo_root()
    try:
        source_label = str(source_data.resolve().relative_to(root.resolve()))
    except ValueError:  # pragma: no cover - source outside the repository
        source_label = source_data.name

    # The sidecar pins the DIGEST of the data drawn, not only its path. A path
    # cannot go stale and so cannot report staleness: the figure and its source
    # data are separate tracked files, one is rendered and the other rebuilt, and
    # a rebuild that is not followed by a re-render leaves a committed figure
    # drawing numbers no tracked artifact holds any more. That happened -- the
    # protocol-lineage repair moved the mifepristone declared-horizon value from
    # 0.000050 to 0.000020 in `figure_source_data.tsv`, and the committed PNG
    # went on drawing 0.000050, the withdrawn pre-repair artifact, through a
    # merge and a full green suite. `tests/unit/test_concordance.py` compares
    # this digest against the tracked file so the next one fails loudly.
    sidecar = destination.with_name(destination.stem + "_metadata.json")
    sidecar.write_text(
        json.dumps(
            {
                "schema_version": "1.1",
                "figure": destination.name,
                "source_data": source_label,
                "source_data_sha256": hashlib.sha256(
                    source_data.read_bytes()
                ).hexdigest(),
                "provenance": provenance,
                "claim_boundaries": [
                    "Calibration agreement is not validation.",
                    "MaBoSS relative time is dimensionless; never a day count.",
                    "No concentration is compared numerically to a Boolean probability.",
                    "Three donors; no generalisation claim.",
                    "Panel C collapses nodes computing identical Boolean functions.",
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return destination
