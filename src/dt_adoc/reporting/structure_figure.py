"""Static structural figures for an executable MaBoSS network.

Two artifacts, deliberately different rather than one downscaled twice.

The **network figure** lays every node out by dependency depth and marks the
structural caveats: which nodes cannot affect a phenotype, which declared inputs
no rule reads, which nodes are exact aliases of one another, and which
dependencies are absorbed. It needs ~1900px to stay legible; a downscale to
README width turns the grey inert labels into smudges and erases the dotted
absorbed edges, which are precisely the marks that stop the figure being
misread.

The **summary card** is what the README embeds. It is not a shrunk network -- it
is a small set of counts, large enough to read, linking to the network figure.
That avoids publishing an illegible hairball as the current-model figure.

Neither draws a probability, a time course, a transition rate, an initial
condition, or an evidence-confidence colour. ``probability_to_color`` is never
imported. No ``.cfg`` is read, so the relay istates cannot reach either figure.
Edge-level evidence confidence is deliberately not drawn: every one of the
model's assertions is ``not_yet_curated`` and none has claim-level verified
support, so colouring edges by grade would assert curation that does not exist.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from dt_adoc.reporting.dynamics import load_visualization_config
from dt_adoc.reporting.structure import (
    StructuralFacts,
    load_structure,
    structural_summary,
)

INERT_FILL = "#E2E8F0"
INERT_EDGE = "#94A3B8"
INERT_TEXT = "#64748B"
LIVE_FILL = "#FFFFFF"
LIVE_TEXT = "#1F2933"
ACTIVATION = "#2D6A4F"
INHIBITION = "#BC4749"
DEAD_EDGE = "#CBD5E0"

ALIAS_BADGE_COLORS = (
    "#B7791F",
    "#6B46C1",
    "#2C7A7B",
    "#B83280",
    "#2B6CB0",
    "#9C4221",
    "#4C51BF",
)


@dataclass(frozen=True)
class StructureSettings:
    figsize: tuple[float, float] = (22.0, 11.5)
    dpi: int = 100
    node_fontsize: float = 5.8
    caption_fontsize: float = 8.0


def _short(node_id: str) -> str:
    """Strip the compartment prefix, keeping it where it disambiguates.

    ``E_PGR`` and ``S_PGR`` are the only pair that collides after stripping, and
    they are in the same alias class, so losing the distinction would hide the
    single most consequential aliasing in the model.
    """
    stem = node_id
    for prefix in ("IN_", "OUT_", "E_", "S_", "X_", "T_"):
        if node_id.startswith(prefix):
            stem = node_id[len(prefix) :]
            if stem == "PGR":
                return f"{prefix[0]}·{stem}"
            stem = stem.replace("_", " ")
            break
    # Wrap rather than let text overflow the box: an overflowing label collides
    # with its neighbours and, at the output end of the graph, made four
    # phenotype nodes unreadable.
    if len(stem) > 15:
        words = stem.split(" ")
        if len(words) > 1:
            midpoint = len(words) // 2 + len(words) % 2
            return "\n".join((" ".join(words[:midpoint]), " ".join(words[midpoint:])))
    return stem


def _layered_positions(facts: StructuralFacts) -> dict[str, tuple[float, float]]:
    """Place nodes in columns by dependency depth, ordered by parent median.

    Depth layering rather than compartment bands: 5 of the 7 alias classes span
    compartments, so bands would imply a separation the logic does not have, and
    96 arcs across three vertical bands is an untraceable hairball.
    """
    by_depth: dict[int, list[str]] = {}
    for node_id in facts.node_ids:
        by_depth.setdefault(facts.depth[node_id], []).append(node_id)

    parents: dict[str, list[str]] = {n: [] for n in facts.node_ids}
    for source, target, _sign in facts.edges:
        parents[target].append(source)

    positions: dict[str, tuple[float, float]] = {}
    for depth in sorted(by_depth):
        column = by_depth[depth]
        if depth > 0:
            column.sort(
                key=lambda n: (
                    sum(positions[p][1] for p in parents[n] if p in positions)
                    / max(len([p for p in parents[n] if p in positions]), 1),
                    n,
                )
            )
        else:
            column.sort()
        count = len(column)
        for index, node_id in enumerate(column):
            y = 1.0 - (index + 0.5) / count
            positions[node_id] = (float(depth), y)
    return positions


def render_structure(
    facts: StructuralFacts,
    output_path: Path,
    settings: StructureSettings | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Draw the layered structural network and return its metadata."""
    settings = settings or StructureSettings()
    config = load_visualization_config(root)
    compartments = config.get("compartments", {})
    positions = _layered_positions(facts)

    inert = set(facts.phenotype_inert)
    unread = set(facts.unread_inputs)
    free = set(facts.free)
    measured = set(facts.measured)
    absorbed = set(facts.absorbed_edges)
    never_binding = set(facts.never_binding_inhibitions)
    alias_of = {
        node_id: index
        for index, members in enumerate(
            sorted(facts.alias_classes, key=lambda m: (-len(m), sorted(m)))
        )
        for node_id in members
    }

    max_depth = max(facts.depth.values())
    figure, axis = plt.subplots(figsize=settings.figsize, dpi=settings.dpi)
    axis.set_xlim(-0.7, max_depth + 0.7)
    axis.set_ylim(-0.20, 1.06)
    axis.axis("off")

    for depth in range(max_depth + 1):
        if depth % 2 == 0:
            axis.axvspan(depth - 0.45, depth + 0.45, color="#F7FAFC", zorder=0)
        axis.text(
            depth,
            1.035,
            f"depth {depth}",
            ha="center",
            va="center",
            fontsize=settings.caption_fontsize - 1.6,
            color="#A0AEC0",
        )

    for source, target, sign in facts.edges:
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        dead = (source, target) in absorbed or (source, target) in never_binding
        axis.annotate(
            "",
            xy=(x1 - 0.1, y1),
            xytext=(x0 + 0.1, y0),
            zorder=1,
            arrowprops={
                "arrowstyle": "-"
                if dead
                else ("|-|,widthB=0.22" if sign == "inhibition" else "-|>"),
                "color": DEAD_EDGE
                if dead
                else (INHIBITION if sign == "inhibition" else ACTIVATION),
                "linewidth": 0.5 if dead else 0.8,
                "linestyle": (0, (1.4, 1.8)) if dead else "solid",
                "alpha": 0.9 if dead else 0.55,
                "shrinkA": 0,
                "shrinkB": 0,
                "connectionstyle": "arc3,rad=0.08",
            },
        )

    for node_id in facts.node_ids:
        x, y = positions[node_id]
        is_inert = node_id in inert
        compartment = compartments.get(
            facts.compartment_of.get(node_id, "interface"), {}
        )
        border = INERT_EDGE if is_inert else compartment.get("edge", "#4A5568")
        box = mpatches.FancyBboxPatch(
            (x - 0.44, y - 0.024),
            0.88,
            0.048,
            boxstyle="round,pad=0.004,rounding_size=0.008",
            linewidth=2.4 if node_id in free else 0.9,
            edgecolor=border,
            facecolor=INERT_FILL if is_inert else LIVE_FILL,
            hatch="///" if is_inert else None,
            zorder=2,
        )
        axis.add_patch(box)
        label = _short(node_id)
        if node_id in measured:
            label = f"● {label}"
        if node_id in unread:
            label = f"{label}\n(no reader)"
        badge = ""
        if node_id in alias_of:
            badge = chr(ord("A") + alias_of[node_id])
        axis.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=settings.node_fontsize,
            color=INERT_TEXT if is_inert else LIVE_TEXT,
            zorder=3,
        )
        if badge:
            axis.text(
                x + 0.44,
                y,
                badge,
                ha="left",
                va="center",
                fontsize=settings.node_fontsize + 0.4,
                fontweight="bold",
                color=ALIAS_BADGE_COLORS[alias_of[node_id] % len(ALIAS_BADGE_COLORS)],
                zorder=3,
            )

    summary = structural_summary(facts)
    axis.set_title(
        f"{facts.model_version} — structural topology "
        f"({summary['nodes']} nodes, {summary['dependencies']} dependencies "
        f"derived from network.bnd)",
        fontsize=settings.caption_fontsize + 3.5,
        pad=16,
    )

    handles = [
        Line2D(
            [],
            [],
            marker="s",
            color="none",
            markerfacecolor=LIVE_FILL,
            markeredgecolor="#4A5568",
            markeredgewidth=2.4,
            markersize=9,
            label=f"free variable, set not computed ({summary['free_variables']})",
        ),
        Line2D(
            [],
            [],
            marker="s",
            color="none",
            markerfacecolor=INERT_FILL,
            markeredgecolor=INERT_EDGE,
            markersize=9,
            label=f"cannot change any phenotype output ({summary['phenotype_inert_nodes']})",
        ),
        Line2D(
            [],
            [],
            marker="$\\bullet$",
            color="#1F2933",
            linestyle="none",
            markersize=8,
            label=f"has an activated ADOC observation mapping ({summary['measured_nodes']})",
        ),
        Line2D([], [], color=ACTIVATION, linewidth=1.4, label="activation"),
        Line2D([], [], color=INHIBITION, linewidth=1.4, label="inhibition"),
        Line2D(
            [],
            [],
            color=DEAD_EDGE,
            linewidth=1.4,
            linestyle=(0, (1.4, 1.8)),
            label=f"absorbed or never-binding, no arrowhead "
            f"({summary['absorbed_dependencies'] + summary['never_binding_inhibitions']})",
        ),
        Line2D(
            [],
            [],
            marker="$A$",
            color=ALIAS_BADGE_COLORS[0],
            linestyle="none",
            markersize=8,
            label=f"alias class: identical Boolean function ({summary['alias_classes']} classes)",
        ),
    ]
    axis.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.0, -0.185),
        ncol=4,
        frameon=False,
        fontsize=settings.caption_fontsize - 0.6,
    )
    axis.text(
        0.0,
        -0.085,
        f"{summary['nodes']} named nodes implement {summary['distinct_functions']} "
        f"distinct Boolean functions. Exhaustive over "
        f"{summary['enumerated_states']:,} assignments of "
        f"{summary['free_variables']} free variables.\n"
        "No probability, time course, transition rate or initial condition is "
        "shown. Evidence grade is deliberately not drawn: no relation has "
        "claim-level verified support.",
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=settings.caption_fontsize - 1.2,
        color="#4A5568",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_path, dpi=settings.dpi, bbox_inches="tight", facecolor="#FFFFFF"
    )
    plt.close(figure)
    return {
        "artifact": output_path.name,
        "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "summary": summary,
    }


DEFAULT_STRUCTURE_DIR = Path("docs/assets")

#: Version-pinned stems, distinct from the ``adoc_maboss_pathway_dynamics*`` set
#: that ``adoc-literature-v0.2.0`` owns, so a structural render can never land on
#: the committed animation's files.
STRUCTURE_STEMS = {
    "adoc-literature-superset-v0.4.0": "adoc_superset_structure_v0.4.0",
    "adoc-literature-superset-v0.3.0": "adoc_superset_structure_v0.3.0",
    "adoc-literature-v0.2.0": "adoc_literature_structure_v0.2.0",
    "adoc-core-v0.1.0": "adoc_core_structure_v0.1.0",
}


def render_structure_artifact(
    model_version: str,
    output_path: Path | None = None,
    root: Path | None = None,
    settings: StructureSettings | None = None,
) -> dict[str, Any]:
    """Render the figure and write its provenance sidecar.

    The metadata records the model version, the sha256 of every input the figure
    depends on, and the counts the caption asserts, so any number on the image
    can be checked without re-rendering. The sidecar path is derived from the
    figure path, so the two cannot drift apart or land on another model's files.
    """
    from dt_adoc.model.provenance import describe_file
    from dt_adoc.model.runtime import resolve_model

    active_root = root or Path(__file__).resolve().parents[3]
    spec = resolve_model(model_version, active_root)
    target = active_root / (
        output_path
        or DEFAULT_STRUCTURE_DIR
        / f"{STRUCTURE_STEMS.get(model_version, model_version)}.png"
    )
    facts = load_structure(model_version, active_root)
    result = render_structure(facts, target, settings, active_root)

    metadata = {
        "schema_version": "1.0",
        "artifact": "adoc_structural_topology",
        "claim_boundary": (
            "Structural topology of an executable Boolean network. Shows no "
            "probability, no time course, no transition rate, no initial "
            "condition and no evidence grade. Horizon-independent and "
            "seed-independent: it cannot be invalidated by the unresolved "
            "endpoint-readout policy."
        ),
        "model_version": spec.model_version,
        "inputs": {
            "network_bnd": describe_file(spec.network_bnd, root=active_root).__dict__,
            "node_dictionary": describe_file(
                spec.node_dictionary, root=active_root
            ).__dict__,
            "visualization_config": describe_file(
                active_root / "config" / "visualization.yaml", root=active_root
            ).__dict__,
            "observation_model_map": describe_file(
                active_root / "config" / "observation_model_map.tsv", root=active_root
            ).__dict__,
        },
        "summary": result["summary"],
        "phenotype_inert_nodes": list(facts.phenotype_inert),
        "unread_inputs": list(facts.unread_inputs),
        "measured_nodes": list(facts.measured),
        "alias_classes": [sorted(members) for members in facts.alias_classes],
        "never_binding_inhibitions": [
            list(pair) for pair in facts.never_binding_inhibitions
        ],
        "figure": {
            "path": str(target.relative_to(active_root)),
            "sha256": result["sha256"],
            "deterministic": True,
        },
    }
    sidecar = target.with_name(target.stem + "_metadata.json")
    sidecar.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    metadata["metadata_path"] = str(sidecar.relative_to(active_root))
    return metadata
