"""The collaborator-facing observability figure, and the tables behind it.

Three panels over one shared layout, so the reader learns the map once:

**A -- what the model represents.** Every node placed by compartment and
dependency depth, drawn as *effective-state* supernodes: nodes realising the
identical Boolean function everywhere share one box, with their biological names
listed inside. Nine epithelial labels that are one function are drawn as one
box, because drawing nine boxes would assert nine independently estimable
variables that do not exist.

**B -- what the current experiment determines.** Same layout, recoloured by the
information status each effective state has under the arms the repository
records observations for. Boxes that merge further under the design -- distinct
functions the arms cannot tell apart -- are joined by a bundling hull.

**C -- what the proposed panel would recover.** Same layout again, marking the
states the computed panel separates.

Every colour is read from ``identifiability.py``. Nothing is painted by hand,
and no colour encodes evidence grade: the model's edge assertions are almost all
``not_yet_curated``, so an evidence-graded edge palette would assert curation
that does not exist. This follows ``structure_figure.py``, which made the same
choice for the same reason.
"""

from __future__ import annotations

import hashlib
import json
import textwrap
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

#: Fixes the salt for SVG element ids so repeated runs are byte-identical.
matplotlib.rcParams["svg.hashsalt"] = "dt-adoc-identifiability"

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import derive_dependencies, parse_bnd_rules
from dt_adoc.reporting.coupling import adjudication_for, perturbation_separability
from dt_adoc.reporting.identifiability import (
    IdentifiabilityFacts,
    adhesion_endpoint_decomposition,
    candidate_arms,
    compute_gain,
    identifiability_summary,
    load_identifiability,
)
from dt_adoc.reporting.structure import load_structure

#: Column bands, left to right. Inputs first, phenotypes last: the figure reads
#: as intervention -> tissue -> interface -> readout.
BANDS = (
    ("input", "Experimental\ninputs"),
    ("epithelium", "Epithelium"),
    ("stroma", "Stroma"),
    ("interface", "ECM / interface"),
    ("phenotype", "Phenotype\nreadouts"),
)

#: Information status -> (fill, edge, legend text). Grey means the current design
#: cannot tell this state apart or does not observe it. It never means the
#: biology does not matter.
STATUS_STYLE = {
    "directly_measured": ("#1b5e20", "#0d3010", "Directly measured"),
    "design_aliased_to_measured": (
        "#81c784",
        "#2e7d32",
        "Indistinguishable from a measured state",
    ),
    "indirectly_constrained": (
        "#4fc3f7",
        "#01579b",
        "Inferred from a measured readout",
    ),
    "model_asserted_untested": (
        "#cfd8dc",
        "#78909c",
        "Asserted by the model, untested",
    ),
    "latent_unresolved": ("#9e9e9e", "#424242", "Unknown: latent and unresolved"),
}

#: B2: the module writes six perturbation statuses and this table held two, so
#: `set_alone_no_shared_readout` -- the one status the analysis text spends a
#: paragraph defending, and which `IN_E2` alone carries -- was drawn as if the
#: input were never perturbed at all. The figure must not erase a distinction
#: the tables make. Pinned by
#: `test_identifiability.PerturbationMarkerCoverageTest`.
PERTURBATION_MARKER = {
    "independently_perturbed": ("o", "#d84315", "Independently perturbed"),
    "set_alone_no_shared_readout": (
        "D",
        "#8e24aa",
        "Set alone, but no shared readout",
    ),
    "bundled_perturbed": ("s", "#ef9a9a", "Perturbed only inside a bundle"),
}


def _band_of(node_id: str, compartment: str) -> str:
    if node_id.startswith("OUT_"):
        return "phenotype"
    if node_id.startswith("IN_"):
        return "input"
    if compartment in {"epithelium", "stroma", "interface"}:
        return compartment
    if compartment in {"extracellular", "stroma_external", "shared"}:
        return "interface"
    if node_id.startswith("E_"):
        return "epithelium"
    if node_id.startswith("S_"):
        return "stroma"
    return "interface"


#: Vertical pitch between boxes in a column, in axis units.
ROW_PITCH = 1.0
BOX_HALF_WIDTH = 0.40


def _layout(
    facts: IdentifiabilityFacts, depth: dict[str, int]
) -> dict[tuple[str, ...], tuple[float, float]]:
    """One position per global effective state, deterministic from the model.

    Band from the node dictionary's compartment, vertical order from dependency
    depth then name, on a fixed row pitch rather than a normalised interval: a
    column of five boxes and a column of fourteen must use the same box size, or
    the sparse column's labels grow until they collide with the arrows.

    A class spanning compartments -- the stromal class ends in an ``OUT_`` node
    -- is placed in the band of its deepest member, so an edge into a phenotype
    still points rightwards.
    """
    placed: dict[str, list[tuple[str, ...]]] = {band: [] for band, _ in BANDS}
    for members in facts.global_classes:
        anchor = max(members, key=lambda n: (depth[n], n))
        band = _band_of(anchor, facts.compartment_of.get(anchor, ""))
        placed[band].append(members)

    tallest = max(len(classes) for classes in placed.values())
    positions: dict[tuple[str, ...], tuple[float, float]] = {}
    for column, (band, _label) in enumerate(BANDS):
        classes = sorted(
            placed[band],
            key=lambda m: (min(depth[n] for n in m), min(m)),
        )
        offset = (tallest - len(classes)) / 2.0
        for row, members in enumerate(classes):
            positions[members] = (float(column), (offset + row) * ROW_PITCH)
    return positions


def _class_label(members: tuple[str, ...], label_of: dict[str, str]) -> str:
    """What goes inside a supernode box: the biological names, never one name.

    A nine-member class prints its members, because printing only the first
    would show the reader one variable where the model has one variable and nine
    names, which is the confusion the whole figure exists to remove.
    """

    def strip(node_id: str) -> str:
        for prefix in ("IN_", "E_", "S_", "X_", "OUT_"):
            if node_id.startswith(prefix):
                return node_id[len(prefix) :]
        return node_id

    names = [strip(n) for n in sorted(members)]
    if len(names) <= 3:
        return "\n".join(names)
    return "\n".join(names[:3]) + f"\n+{len(names) - 3} more"


def _class_status(members: tuple[str, ...], facts: IdentifiabilityFacts) -> str:
    """The strongest information status any member of the class holds.

    A class is a set of labels the rules make identical, so if one member is
    measured the whole class is observed -- and equally, the measurement cannot
    distinguish the members. Taking the strongest status states what the design
    determines about the class, which is exactly what it determines about any
    member.
    """
    order = [
        "directly_measured",
        "indirectly_constrained",
        "design_aliased_to_measured",
        "model_asserted_untested",
        "latent_unresolved",
    ]
    statuses = {facts.information_status[n] for n in members}
    for status in order:
        if status in statuses:
            return status
    return "latent_unresolved"


#: Precedence when one design class mixes statuses: attributable beats
#: set-alone-but-unreadable beats bundled. Keyed to PERTURBATION_MARKER so a
#: status can never be added to the legend and left undrawn.
_PERTURBATION_PRECEDENCE = (
    "independently_perturbed",
    "set_alone_no_shared_readout",
    "bundled_perturbed",
)


def _class_perturbation(members: tuple[str, ...], facts: IdentifiabilityFacts) -> str:
    statuses = {facts.perturbation_status[n] for n in members}
    for status in _PERTURBATION_PRECEDENCE:
        if status in statuses:
            return status
    return "none"


def _draw_map(
    axis,
    facts: IdentifiabilityFacts,
    positions: dict[tuple[str, ...], tuple[float, float]],
    edges: set[tuple[tuple[str, ...], tuple[str, ...]]],
    *,
    mode: str,
    resolved: set[tuple[str, ...]],
    title: str,
    subtitle: str,
) -> None:
    design_of = {n: c for c in facts.design_classes for n in c}
    bundled = {
        members for members in positions if len(design_of[members[0]]) > len(members)
    }

    for source, target in sorted(edges):
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        axis.annotate(
            "",
            xy=(x1 - BOX_HALF_WIDTH - 0.01, y1),
            xytext=(x0 + BOX_HALF_WIDTH + 0.01, y0),
            arrowprops={
                "arrowstyle": "-|>,head_length=0.25,head_width=0.12",
                "color": "#b0bec5",
                "linewidth": 0.35,
                "alpha": 0.55,
                "shrinkA": 0,
                "shrinkB": 0,
                "connectionstyle": "arc3,rad=0.10",
            },
            zorder=1,
        )

    for members, (x, y) in sorted(positions.items()):
        status = _class_status(members, facts)
        if mode == "proposed":
            if members in resolved:
                fill, edge = "#ffb300", "#e65100"
            else:
                fill, edge = "#eceff1", "#b0bec5"
        else:
            fill, edge, _ = STATUS_STYLE[status]
        rows = min(len(members), 4)
        half_height = 0.16 + 0.085 * rows
        # A red dashed outline marks a state the run arms cannot separate from
        # some other state. Drawing hulls around those groups instead produced
        # blobs spanning the whole panel, because the merged states sit in every
        # compartment -- which is the finding, but not a readable mark for it.
        in_bundle = members in bundled and mode != "proposed"
        axis.add_patch(
            mpatches.FancyBboxPatch(
                (x - BOX_HALF_WIDTH, y - half_height),
                2 * BOX_HALF_WIDTH,
                2 * half_height,
                boxstyle="round,pad=0.02",
                linewidth=1.6 if in_bundle else 1.0,
                linestyle=(0, (2.5, 1.8)) if in_bundle else "solid",
                edgecolor="#c62828" if in_bundle else edge,
                facecolor=fill,
                zorder=2,
            )
        )
        axis.text(
            x,
            y,
            _class_label(members, facts.label_of),
            ha="center",
            va="center",
            fontsize=3.9,
            color="white"
            if status == "directly_measured" and mode != "proposed"
            else "#102027",
            zorder=3,
            linespacing=1.22,
        )
        if len(members) > 1:
            axis.text(
                x + BOX_HALF_WIDTH,
                y + half_height,
                str(len(members)),
                ha="center",
                va="center",
                fontsize=4.2,
                color="#37474f",
                zorder=4,
                bbox={
                    "boxstyle": "circle,pad=0.18",
                    "facecolor": "white",
                    "edgecolor": "#90a4ae",
                    "linewidth": 0.6,
                },
            )
        if mode == "current":
            perturbation = _class_perturbation(members, facts)
            if perturbation in PERTURBATION_MARKER:
                marker, colour, _ = PERTURBATION_MARKER[perturbation]
                axis.plot(
                    [x - BOX_HALF_WIDTH],
                    [y + half_height],
                    marker=marker,
                    markersize=3.6,
                    color=colour,
                    markeredgecolor="white",
                    markeredgewidth=0.5,
                    zorder=4,
                )

    top = max(y for _x, y in positions.values())
    for column, (_band, label) in enumerate(BANDS):
        axis.text(
            column,
            top + 1.15,
            label,
            ha="center",
            va="bottom",
            fontsize=6.4,
            color="#37474f",
            fontweight="bold",
            linespacing=1.1,
        )
    # Wrapped to a fixed column count rather than trusted to fit: matplotlib does
    # not clip or reflow axes text, so an over-long caption silently runs off the
    # page edge in the PDF and the SVG alike.
    wrapped = "\n".join(
        line
        for paragraph in subtitle.split("\n")
        for line in textwrap.wrap(paragraph, width=168) or [""]
    )
    # The subtitle is anchored to the top of the axes and grows UPWARD, so the
    # title's pad has to clear it. A constant pad was fine at four wrapped lines
    # and silently drew the title straight through the caption at six, which is
    # how B1's repair first came out. Deriving it from the wrapped line count is
    # what makes the layout a function of the text rather than of the author
    # having remembered.
    _SUBTITLE_LINE_PT = 8.7  # fontsize 5.8 at linespacing 1.5
    axis.set_title(
        title,
        fontsize=8.2,
        fontweight="bold",
        loc="left",
        pad=13.2 + _SUBTITLE_LINE_PT * (wrapped.count("\n") + 1),
    )
    axis.text(
        0.0,
        1.004,
        wrapped,
        transform=axis.transAxes,
        fontsize=5.8,
        color="#455a64",
        va="bottom",
        linespacing=1.5,
    )
    axis.set_xlim(-0.62, len(BANDS) - 0.38)
    axis.set_ylim(-0.9, top + 2.0)
    axis.axis("off")


def _draw_collapse(axis, facts: IdentifiabilityFacts, summary: dict[str, Any]) -> None:
    """The headline: two independent collapses, drawn as two bars each.

    Left pair is the *state space the model distinguishes*; right pair is the
    *internal configuration the observation distinguishes*. They are different
    quantities in different units and are drawn apart, because a single
    "% identifiable" would divide one by the other and mean nothing.
    """
    stages = [
        (0, summary["named_nodes"], "#37474f", "biological\nlabels", ""),
        (
            1,
            summary["global_effective_states"],
            "#607d8b",
            "distinct Boolean\nfunctions",
            f"-{summary['states_lost_to_rule_encoding']} merged by the v0.4 rules\n(a model-encoding limit)",
        ),
        (
            2,
            summary["design_effective_states"],
            "#c62828",
            "separable by the\ncurrent arms",
            f"-{summary['states_lost_to_design_bundling']} merged by bundled dosing\n(an experimental-design limit)",
        ),
    ]
    for x, value, colour, label, note in stages:
        axis.bar(x, value, width=0.56, color=colour, zorder=2)
        axis.text(
            x,
            value + 1.2,
            str(value),
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color=colour,
        )
        axis.text(
            x,
            -4.2,
            label,
            ha="center",
            va="top",
            fontsize=5.7,
            color="#37474f",
            linespacing=1.25,
        )
        if note:
            axis.annotate(
                note,
                xy=(x - 0.3, value),
                xytext=(x - 0.02, value + 13.5),
                fontsize=5.2,
                color="#b71c1c" if "design" in note else "#455a64",
                ha="center",
                va="bottom",
                linespacing=1.3,
                arrowprops={"arrowstyle": "-", "color": "#cfd8dc", "linewidth": 0.6},
            )

    for x, value, colour, label in (
        (
            3.9,
            summary["latent_assignments"],
            "#546e7a",
            "internal configurations\nthe design allows",
        ),
        (
            4.9,
            summary["observation_classes"],
            "#b71c1c",
            "distinguishable by\nevery measurement taken",
        ),
    ):
        axis.bar(x, value, width=0.56, color=colour, zorder=2)
        axis.text(
            x,
            value + 1.2,
            str(value),
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color=colour,
        )
        axis.text(
            x,
            -4.2,
            label,
            ha="center",
            va="top",
            fontsize=5.7,
            color="#37474f",
            linespacing=1.25,
        )

    axis.axvline(3.15, color="#cfd8dc", linewidth=0.8)
    axis.text(
        1.0,
        62,
        "Mechanism the model can tell apart",
        ha="center",
        fontsize=6.3,
        fontweight="bold",
        color="#37474f",
    )
    axis.text(
        4.4,
        62,
        "Internal state the data can tell apart",
        ha="center",
        fontsize=6.3,
        fontweight="bold",
        color="#37474f",
    )
    axis.set_xlim(-0.65, 5.45)
    axis.set_ylim(-17, 70)
    axis.axis("off")


def _draw_gain(axis, facts: IdentifiabilityFacts, gain) -> None:
    """Marginal gain of each candidate, the two currencies side by side."""
    arms = sorted(gain.arm_structural, key=lambda row: (-row[1], row[0]))[:9]
    labels = [
        arm_id.replace("hormone_treated_maternal__", "HT + ")
        .replace("adhesion_challenge_hormone_treated__", "challenge + ")
        .replace("solo_", "alone: ")
        .replace("dropout_", "cocktail minus ")
        .replace("IN_", "")
        for arm_id, _v, _r in arms
    ]
    values = [value - gain.baseline_design_classes for _a, value, _r in arms]
    y = list(range(len(arms)))[::-1]
    axis.barh(y, values, color="#c62828", height=0.62, zorder=2)
    for position, (value, label) in enumerate(zip(values, labels)):
        axis.text(
            -0.12,
            y[position],
            label,
            ha="right",
            va="center",
            fontsize=4.8,
            color="#37474f",
        )
        axis.text(
            value + 0.12,
            y[position],
            f"+{value}",
            va="center",
            fontsize=5.2,
            color="#b71c1c",
        )
    # The category labels live in negative x so they stay inside the axes; a
    # tight_layout-style reservation is not available on an axis with axis("off").
    axis.set_xlim(-max(values) * 2.45, max(values) + 1.1)
    axis.set_ylim(-0.8, len(arms) - 0.2)
    axis.set_title(
        "Added perturbations, ranked by mechanism separated",
        fontsize=6.6,
        fontweight="bold",
        loc="left",
        pad=13,
    )
    axis.text(
        0.0,
        1.005,
        "extra distinct Boolean functions the arms can tell apart",
        transform=axis.transAxes,
        fontsize=5.3,
        color="#607d8b",
        va="bottom",
    )
    axis.axis("off")


def _draw_readout_gain(axis, facts: IdentifiabilityFacts, gain) -> None:
    """Why most candidate assays add nothing, as a count rather than a claim."""
    assayable = [(n, v) for n, v, ok in gain.readout_current if ok]
    zero = [n for n, v in assayable if v <= gain.baseline_fibers]
    some = sorted(
        ((n, v) for n, v in assayable if v > gain.baseline_fibers),
        key=lambda row: (-row[1], row[0]),
    )
    axis.bar([0], [len(zero)], width=0.5, color="#9e9e9e", zorder=2)
    axis.bar([1.6], [len(some)], width=0.5, color="#2e7d32", zorder=2)
    axis.text(
        0,
        len(zero) + 0.7,
        str(len(zero)),
        ha="center",
        fontsize=8.0,
        fontweight="bold",
        color="#616161",
    )
    axis.text(
        1.6,
        len(some) + 0.7,
        str(len(some)),
        ha="center",
        fontsize=8.0,
        fontweight="bold",
        color="#2e7d32",
    )
    axis.text(
        0,
        -1.2,
        "add\nnothing",
        ha="center",
        va="top",
        fontsize=5.0,
        color="#37474f",
        linespacing=1.35,
    )
    axis.text(
        1.6,
        -1.2,
        "add\nresolution",
        ha="center",
        va="top",
        fontsize=5.0,
        color="#37474f",
        linespacing=1.35,
    )
    axis.text(
        2.55,
        len(zero) * 1.02,
        f"of {len(assayable)} assayable states not yet\nmeasured. The {len(some)} that help:\n\n"
        + "\n".join(f"+{v - gain.baseline_fibers}   {n}" for n, v in some[:6]),
        fontsize=4.7,
        va="top",
        color="#37474f",
        linespacing=1.5,
    )
    axis.set_xlim(-0.9, 6.4)
    axis.set_ylim(-9.5, len(zero) + 6)
    axis.set_title(
        "Added readouts, under the arms as they are run",
        fontsize=6.6,
        fontweight="bold",
        loc="left",
        pad=13,
    )
    axis.text(
        0.0,
        1.005,
        "a readout only informs if the design already makes its state vary",
        transform=axis.transAxes,
        fontsize=5.3,
        color="#607d8b",
        va="bottom",
    )
    axis.axis("off")


def _draw_endpoint(axis, endpoint: dict[str, Any], summary: dict[str, Any]) -> None:
    """The adhesion endpoint, and why it cannot localise a mechanism."""
    priors = endpoint["carrier_priors"]
    names = [n.replace("X_INTERFACE_", "").replace("_RELAY", "") for n in priors]
    first, second = priors.values()
    axis.text(
        0.0,
        1.0,
        "The stable-adhesion endpoint",
        fontsize=6.6,
        fontweight="bold",
        color="#37474f",
        va="top",
        transform=axis.transAxes,
    )
    # The reduction is DERIVED under a pinned latent value and holds only there.
    # Saying "every internal configuration" without it claimed the mechanism
    # across the assignments the derivation excludes -- the ones where
    # E_KLF12_HIGH is on -- in a figure collaborators read on its own.
    pinned = ", ".join(
        f"{node} {'on' if state else 'off'}"
        for node, state in endpoint["pinned_latent"].items()
    )
    lines = (
        f"In the hormone-treated challenge arm, with {pinned},\n"
        f"every condition for attachment holds for every\n"
        f"internal configuration, except the two positive\n"
        f"interface routes. So the converged endpoint is\n"
        f"exactly\n\n"
        f"   1 - (1-{first:g})(1-{second:g})  =  "
        f"{endpoint['analytic_value']}\n\n"
        f"Both numbers are initial probabilities typed into\n"
        f"baseline.cfg for the {names[0]} and {names[1]}\n"
        f"relays -- placeholders for interface biology the\n"
        f"model does not represent. Attachment is a real and\n"
        f"important phenotype, but its graded value here is\n"
        f"arithmetic on two assumptions, and the count cannot\n"
        f"say which route carried it. Endpoint-only validation\n"
        f"cannot identify mechanism."
    )
    axis.text(
        0.0,
        0.88,
        lines,
        fontsize=4.9,
        color="#37474f",
        va="top",
        linespacing=1.55,
        transform=axis.transAxes,
    )
    axis.axis("off")


def _proposed_resolution(
    facts: IdentifiabilityFacts, gain, root: Path | None
) -> set[tuple[str, ...]]:
    """Effective states the proposed arms pull out of a bundle.

    Re-partitioned under the extended arm set rather than asserted: a state
    counts as recovered only if it shares a design class with another state now
    and stops doing so once the proposed arms are added.
    """
    from dt_adoc.reporting.identifiability import (
        _classes,
        _evaluate,
        _latent_seeds,
        _topological_order,
    )

    spec = resolve_model(facts.model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    order = _topological_order(rules, {n for n in rules if rules[n].strip() == n})
    seeds, _states, mask = _latent_seeds(facts.latent)
    proposals = {c.arm_id: c for c in candidate_arms(facts, root)}
    selected = [a.inputs for a in facts.arms] + [
        proposals[arm_id].inputs for arm_id, _c, _f in gain.greedy_arms
    ]
    columns = [_evaluate(rules, order, seeds, mask, inputs) for inputs in selected]
    extended_of = {
        n: members
        for members in _classes({n: tuple(c[n] for c in columns) for n in rules})
        for n in members
    }
    design_of = {n: members for members in facts.design_classes for n in members}
    return {
        members
        for members in facts.global_classes
        if len(design_of[members[0]]) > len(extended_of[members[0]])
    }


def render_identifiability_artifact(
    model_version: str,
    output: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Render the figure and write every table behind it."""
    active_root = root or repo_root()
    facts = load_identifiability(model_version, root)
    structure = load_structure(model_version, root)
    gain = compute_gain(facts, root)
    endpoint = adhesion_endpoint_decomposition(facts, root)
    summary = identifiability_summary(facts)

    target = output or (
        active_root / "docs" / "assets" / f"adoc_identifiability_{model_version}.svg"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    tables = active_root / "docs" / "identifiability"
    tables.mkdir(parents=True, exist_ok=True)

    positions = _layout(facts, structure.depth)
    class_of = {n: members for members in positions for n in members}
    dependencies = derive_dependencies(
        parse_bnd_rules(resolve_model(model_version, root).network_bnd)
    )
    edges = {
        (class_of[source], class_of[target])
        for source, target in dependencies
        if class_of[source] != class_of[target]
    }
    resolved = _proposed_resolution(facts, gain, root)

    # Height and hspace carry panel B's four-paragraph subtitle: `_draw_map`
    # pads the title clear of its own caption, so the caption's length is paid
    # for in the gap above the panel, not inside it. Tightened together, and
    # checked against panel A's bar labels, which is what the previous values
    # collided with.
    figure = plt.figure(figsize=(10.0, 16.2))
    grid = figure.add_gridspec(
        4,
        6,
        height_ratios=[1.25, 3.45, 3.45, 1.5],
        hspace=0.42,
        wspace=0.55,
        left=0.035,
        right=0.975,
        top=0.945,
        bottom=0.05,
    )
    ax_collapse = figure.add_subplot(grid[0, :])
    ax_current = figure.add_subplot(grid[1, :])
    ax_proposed = figure.add_subplot(grid[2, :])
    ax_arms = figure.add_subplot(grid[3, 0:2])
    ax_readouts = figure.add_subplot(grid[3, 2:4])
    ax_endpoint = figure.add_subplot(grid[3, 4:6])

    _draw_collapse(ax_collapse, facts, summary)
    ax_collapse.set_title(
        "A  What the twin represents, and how much of it the data separate",
        fontsize=8.2,
        fontweight="bold",
        loc="left",
        pad=10,
    )

    _draw_map(
        ax_current,
        facts,
        positions,
        edges,
        mode="current",
        resolved=resolved,
        # B1: this panel titled itself "What the current experiment can
        # determine" while docs/identifiability_analysis.md opens by
        # withdrawing exactly that reading -- every information status here
        # assumes one biological unit carries a single latent assignment
        # through every arm and assay, which the current data do not provide.
        # The title and the first subtitle line now carry that scope, so the
        # figure cannot be read apart from the document that explains it.
        # Pinned by `test_identifiability.PanelScopeTest`.
        title=(
            "B  What a matched-unit design of this shape could determine "
            "-- NOT what the current data determine"
        ),
        subtitle=(
            f"MATCHED-UNIT ASSUMPTION: every colour below assumes one biological unit "
            f"carries one latent assignment through every arm and assay. The current data "
            f"do not provide that -- adhesion is an aggregate per-embryo count and the "
            f"secretion mappings are unpaired.\n"
            f"One box is one distinct Boolean function; the badge counts the biological labels "
            f"the v0.4 rules make identical to it.\n"
            f"Colour is what the {summary['run_arms']} recorded arms and "
            f"{summary['measured_nodes']} measured quantities would determine about that state "
            f"under that assumption. Red "
            f"dashed outline: the arms cannot separate it from another state, because the "
            f"hormone cocktail and the embryo challenge each move three inputs at once.\n"
            f"Grey means this design could not infer the state -- never that the biology is "
            f"unimportant."
        ),
    )
    _draw_map(
        ax_proposed,
        facts,
        positions,
        edges,
        mode="proposed",
        resolved=resolved,
        title="C  What a small set of added perturbations would separate",
        subtitle=(
            f"Amber: states the {len(gain.greedy_arms)} proposed arms pull out of a bundle, "
            f"raising separable mechanism from {summary['design_effective_states']} to "
            f"{gain.greedy_arms[-1][1]} of {gain.global_ceiling}.\nEach proposed arm moves one "
            f"input that currently never moves alone. Measurements alone cannot do this: they "
            f"raise internal-state resolution only from {gain.baseline_fibers} to "
            f"{gain.assayable_latent_ceiling} of {gain.latent_ceiling}, because the rest of the "
            f"uncertainty sits in four interface placeholders no assay can measure."
        ),
    )
    _draw_gain(ax_arms, facts, gain)
    _draw_readout_gain(ax_readouts, facts, gain)

    handles = [
        mpatches.Patch(facecolor=fill, edgecolor=edge, label=text)
        for fill, edge, text in STATUS_STYLE.values()
    ]
    handles.append(
        mpatches.Patch(
            facecolor="white",
            edgecolor="#c62828",
            linestyle="--",
            label="Not separable from another state",
        )
    )
    handles.append(
        mpatches.Patch(
            facecolor="#ffb300", edgecolor="#e65100", label="Separated by panel C"
        )
    )
    handles += [
        Line2D(
            [],
            [],
            marker=marker,
            color=colour,
            linestyle="none",
            markersize=4.4,
            label=text,
        )
        for marker, colour, text in PERTURBATION_MARKER.values()
    ]
    figure.legend(
        handles=handles,
        loc="upper center",
        ncol=5,
        fontsize=5.9,
        frameon=False,
        bbox_to_anchor=(0.5, 0.988),
    )
    figure.suptitle(
        "The ADOC digital twin represents more mechanism than a matched-unit "
        "design of this shape could identify",
        fontsize=11.0,
        fontweight="bold",
        y=0.995,
    )

    _draw_endpoint(ax_endpoint, endpoint, summary)

    figure.text(
        0.035,
        0.008,
        f"{facts.model_version}  |  structural analysis of network.bnd with the recorded "
        f"condition cfgs, config/observation_model_map.tsv and config/calibration.yaml. No "
        f"simulation, no horizon, no fitted parameter;\nevery class is computed, none assigned "
        f"by hand.\nMATCHED-UNIT ASSUMPTION: every class assumes one unit carries one "
        f"latent assignment through every arm and assay. The current data do not provide "
        f"that -- adhesion is an aggregate\ncount and the secretion mappings are unpaired -- "
        f"so these are NOT claims about what the current data identify. "
        f"Tables: docs/identifiability/. Method: docs/identifiability_analysis.md.",
        fontsize=5.0,
        color="#78909c",
        va="bottom",
        linespacing=1.5,
    )

    # SVG and PDF both embed a creation timestamp, and SVG salts its internal
    # element ids from the process hash seed. Left alone, re-running the command
    # produces a byte-different file with identical content, so the recorded
    # sha256 would change on every run and could never certify anything. Pinning
    # both makes the artifact a function of the model, which is what the hash in
    # the metadata is for.
    written = []
    for suffix, options in (
        (".svg", {"metadata": {"Date": None}}),
        (".pdf", {"metadata": {"CreationDate": None}}),
        (".png", {"dpi": 220}),
    ):
        path = target.with_suffix(suffix)
        figure.savefig(path, format=suffix[1:], **options)
        written.append(path)
    plt.close(figure)

    artifacts = _write_tables(facts, gain, structure, tables, active_root)
    metadata = {
        "model_version": model_version,
        "summary": summary,
        "adhesion_endpoint": endpoint,
        "ceilings": {
            "design_states_now": gain.baseline_design_classes,
            "design_states_with_proposed_arms": gain.greedy_arms[-1][1],
            "design_states_ceiling": gain.global_ceiling,
            "observation_classes_now": gain.baseline_fibers,
            "observation_classes_assayable_ceiling": gain.assayable_latent_ceiling,
            "observation_classes_ceiling": gain.latent_ceiling,
        },
        "figures": [
            {
                "path": str(path.relative_to(active_root)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in written
        ],
        "tables": artifacts,
    }
    metadata_path = tables / "identifiability_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    metadata["metadata_path"] = str(metadata_path.relative_to(active_root))
    return metadata


def _write_tables(
    facts: IdentifiabilityFacts,
    gain,
    structure,
    directory: Path,
    root: Path,
) -> list[dict[str, str]]:
    """The machine-readable analysis: one row per node, arm, and candidate."""
    written: list[dict[str, str]] = []

    def emit(name: str, header: list[str], rows: list[list[Any]]) -> None:
        path = directory / name
        body = "\t".join(header) + "\n"
        body += "".join("\t".join(str(cell) for cell in row) + "\n" for row in rows)
        path.write_text(body, encoding="utf-8")
        written.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "rows": str(len(rows)),
            }
        )

    global_of = {n: members for members in facts.global_classes for n in members}
    design_of = {n: members for members in facts.design_classes for n in members}
    # Gate 2: the one thing the three partitions do not say -- whether a
    # rule-induced merge is biologically defensible. Curated in
    # config/coupling_adjudication.tsv and joined here rather than typed into
    # this generated table, and pinned to the rule class it was written
    # against, so a rule edit invalidates the verdict loudly.
    adjudication = adjudication_for(
        facts.node_ids,
        {n: min(global_of[n]) for n in facts.node_ids},
        root,
        rule_class_members=global_of,
        model_version=facts.model_version,
    )
    separability = perturbation_separability(
        facts.node_ids, global_of, facts.model_version, root
    )
    inert = set(facts.phenotype_inert)
    assayable = set(facts.assayable)
    measured = set(facts.measured_nodes)
    gain_current = {n: v for n, v, _ok in gain.readout_current}
    gain_extended = {n: v for n, v, _ok in gain.readout_extended}
    proposals = {c.arm_id: c for c in candidate_arms(facts)}

    emit(
        "node_classification.tsv",
        [
            "node_id",
            "label",
            "compartment",
            "figure_band",
            "dependency_depth",
            "effective_function_id",
            "effective_function_size",
            "effective_function_members",
            "design_state_id",
            "design_state_size",
            "information_status",
            "perturbation_status",
            "phenotype_inert",
            "assayable",
            "currently_measured",
            "observation_classes_if_measured_now",
            "observation_classes_if_measured_with_proposed_arms",
            "coupling_adjudication",
            "coupling_evidence_ids",
            "perturbation_separability",
            "merged_with_catalogued_targets",
        ],
        [
            [
                node_id,
                facts.label_of.get(node_id, node_id),
                facts.compartment_of.get(node_id, ""),
                _band_of(node_id, facts.compartment_of.get(node_id, "")),
                structure.depth[node_id],
                min(global_of[node_id]),
                len(global_of[node_id]),
                ";".join(sorted(global_of[node_id])),
                min(design_of[node_id]),
                len(design_of[node_id]),
                facts.information_status[node_id],
                facts.perturbation_status[node_id],
                "true" if node_id in inert else "false",
                "true" if node_id in assayable else "false",
                "true" if node_id in measured else "false",
                gain_current.get(node_id, ""),
                gain_extended.get(node_id, ""),
                adjudication[node_id]["adjudication"],
                adjudication[node_id]["evidence_ids"],
                separability[node_id][0],
                ";".join(separability[node_id][1]),
            ]
            for node_id in facts.node_ids
        ],
    )

    emit(
        "design_arms.tsv",
        [
            "arm_id",
            "condition_cfg",
            "inputs_on",
            "measured_nodes",
            "observation_sources",
        ],
        [
            [
                arm.arm_id,
                arm.cfg,
                ";".join(arm.on) or "(none)",
                ";".join(sorted({n for n, _ in arm.measured})),
                ";".join(sorted({s for _, s in arm.measured})),
            ]
            for arm in facts.arms
        ],
    )

    emit(
        "candidate_arms.tsv",
        [
            "arm_id",
            "inputs_on",
            "design_states_separable",
            "marginal_states_gained",
            "in_proposed_panel",
            "rationale",
        ],
        sorted(
            (
                [
                    arm_id,
                    ";".join(
                        sorted(k for k, v in proposals[arm_id].inputs.items() if v)
                    )
                    or "(none)",
                    classes,
                    classes - gain.baseline_design_classes,
                    "true"
                    if arm_id in {a for a, _c, _f in gain.greedy_arms}
                    else "false",
                    rationale,
                ]
                for arm_id, classes, rationale in gain.arm_structural
            ),
            key=lambda row: (-int(row[3]), row[0]),
        ),
    )

    emit(
        "candidate_readouts.tsv",
        [
            "node_id",
            "label",
            "assayable",
            "why_not_assayable",
            "observation_classes_if_added_now",
            "marginal_gain_now",
            "observation_classes_with_proposed_arms",
            "marginal_gain_with_proposed_arms",
            "shares_design_state_with_a_measured_node",
        ],
        sorted(
            (
                [
                    node_id,
                    facts.label_of.get(node_id, node_id),
                    "true" if is_assayable else "false",
                    ""
                    if is_assayable
                    else "modelling placeholder or protocol schedule; no assay target",
                    value,
                    value - gain.baseline_fibers,
                    gain_extended.get(node_id, ""),
                    gain_extended.get(node_id, 0) - gain.baseline_fibers,
                    "true" if measured.intersection(design_of[node_id]) else "false",
                ]
                for node_id, value, is_assayable in gain.readout_current
            ),
            key=lambda row: (-int(row[7]), -int(row[5]), row[0]),
        ),
    )

    emit(
        "proposed_panel.tsv",
        ["step", "kind", "item", "design_states_separable", "observation_classes"],
        [
            [index + 1, "perturbation_arm", arm_id, classes, fibers]
            for index, (arm_id, classes, fibers) in enumerate(gain.greedy_arms)
        ]
        + [
            [len(gain.greedy_arms) + index + 1, "readout", node_id, "", fibers]
            for index, (node_id, fibers) in enumerate(gain.greedy_readouts)
        ],
    )

    emit(
        "observation_classes.tsv",
        [
            "observation_class",
            "observation_vector",
            "latent_assignments_in_class",
            "latent_variables_resolved",
            "latent_variables_unresolved",
        ],
        [
            [
                index + 1,
                ";".join(str(bit) for bit in key),
                len(members),
                ";".join(
                    n
                    for position, n in enumerate(facts.latent)
                    if len({(m >> position) & 1 for m in members}) == 1
                )
                or "(none)",
                ";".join(
                    n
                    for position, n in enumerate(facts.latent)
                    if len({(m >> position) & 1 for m in members}) > 1
                )
                or "(none)",
            ]
            for index, (key, members) in enumerate(facts.fibers)
        ],
    )
    return written
