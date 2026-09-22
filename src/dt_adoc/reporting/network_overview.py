"""Principal static overview of the executable MaBoSS network.

Every node and every dependency is read from ``network.bnd`` through
``structure.load_structure``; nothing on the figure is hand-placed biology. The
figure answers five questions at a glance, each with its own visual channel so
none depends on colour alone:

* **where a node lives** -- a horizontal band per compartment (epithelium,
  interface / extracellular, stroma), plus a protocol-input column on the left
  and a phenotype-output column on the right, each band named in the margin;
* **what a dependency does** -- activation ends in an arrowhead, inhibition in a
  bar, and a dependency that is *absorbed* (the target never depends on it) or
  an inhibition that *never binds* is drawn dotted, without a head;
* **what ADOC actually measures** -- a marker before the label, in three tiers
  derived from ``config/observation_model_map.tsv`` and ``config/calibration.yaml``
  (see ``measurement_tiers``), never from a hand list;
* **what is not computed** -- free variables have a heavy border, declared inputs
  no rule reads say so, and nodes that cannot change any phenotype output are
  hatched;
* **what is not distinct** -- nodes computing the identical Boolean function
  share a letter, and the classes are spelled out beside the network.

Layout is deterministic: x is dependency depth, and within each band nodes are
ordered by a fixed number of barycentre sweeps with node-id tie-breaks. No
probability, time course, rate, initial condition or evidence grade is drawn, and
no ``.cfg`` is read -- so the figure is horizon- and seed-independent.
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

from dt_adoc.reporting.structure import (
    StructuralFacts,
    load_structure,
    structural_summary,
)
from dt_adoc.reporting.structure_figure import _short

#: Surface and ink (reference palette, light mode).
SURFACE = "#FCFCFB"
INK = "#0B0B0B"
INK_2 = "#52514E"
INK_3 = "#8A8984"

#: Compartment identity: the first three reference categorical slots, which pass
#: the all-pairs CVD and normal-vision checks. Band position and band labels
#: carry the same information, so colour is never the only channel.
BANDS: tuple[tuple[str, str, str], ...] = (
    ("epithelial", "Luminal epithelium", "#2A78D6"),
    ("extracellular", "Interface / extracellular", "#EB6834"),
    ("stromal", "Stroma", "#1BAF7A"),
)
BAND_TINT_ALPHA = 0.07
IO_COLOR = "#52514E"

ACTIVATION = "#52514E"
INHIBITION = "#E34948"
DEAD_EDGE = "#B8B7B1"
INERT_FILL = "#EFEEEA"
HATCH = "#CFCEC8"

#: Measurement tiers, strongest first. The glyph precedes the node label.
TIER_ACTIVE = "active_observation_mapping"
TIER_ENDPOINT = "functional_endpoint_ordinal_only"
TIER_ASSAYED = "assayed_mapping_not_activated"
TIER_COMPOSITE = "reported_composite_no_source_rows"
TIER_GLYPH = {
    TIER_ACTIVE: "●",
    TIER_ENDPOINT: "◆",
    TIER_ASSAYED: "○",
    TIER_COMPOSITE: "◇",
}
TIER_LABEL = {
    TIER_ACTIVE: "ADOC readout with an ACTIVE observation mapping",
    TIER_ENDPOINT: "ADOC functional endpoint (embryo counts; ordinal only, magnitude not fitted)",
    TIER_ASSAYED: "ADOC-assayed analyte, mapping NOT activated (provisional)",
    TIER_COMPOSITE: "reported composite mapping, zero ADOC source rows (not assayed)",
}

DEFAULT_OUTPUT_DIR = Path("docs/assets")


@dataclass(frozen=True)
class OverviewSettings:
    figsize: tuple[float, float] = (24.0, 14.0)
    dpi: int = 110
    node_fontsize: float = 6.4
    caption_fontsize: float = 8.6
    sweeps: int = 8


def measurement_tiers(
    facts: StructuralFacts, root: Path | None = None
) -> dict[str, str]:
    """Each model node's strongest ADOC measurement tier, derived, not declared.

    ``active`` -- a row of ``observation_model_map.tsv`` whose activation status
    is evaluable names the node (the same rule ``structure.py`` uses).
    ``endpoint`` -- ``config/calibration.yaml``'s adhesion objective records
    embryo-attachment counts, which ``identifiability._observed_arms`` maps to
    ``OUT_STABLE_ADHESION``; that objective is ``diagnostic_ordinal``.
    ``assayed`` -- a ``provisional`` or ``reported_only`` row with source rows
    names the node: the analyte is measured, but no mapping to the node is
    licensed. ``composite`` -- such a row with **zero** source rows, i.e. a
    reported multi-analyte composite that ADOC does not assay as such. The two
    must not share a marker: one has data behind it and the other has none.
    ``rejected`` rows confer nothing.
    """
    import yaml

    from dt_adoc.calibration.observation_map import (
        EVALUABLE_ACTIVATION_STATUSES,
        load_observation_map,
    )
    from dt_adoc.model.provenance import repo_root

    active_root = root or repo_root()
    rank = {TIER_ACTIVE: 0, TIER_ENDPOINT: 1, TIER_ASSAYED: 2, TIER_COMPOSITE: 3}
    tiers: dict[str, str] = {}

    def assign(node_id: str, tier: str) -> None:
        if node_id in facts.rules and (
            node_id not in tiers or rank[tier] < rank[tiers[node_id]]
        ):
            tiers[node_id] = tier

    for row in load_observation_map(active_root):
        nodes = [n for n in row["model_nodes"].split(";") if n]
        if row["activation_status"] in EVALUABLE_ACTIVATION_STATUSES:
            for node_id in nodes:
                assign(node_id, TIER_ACTIVE)
        elif row["activation_status"] in {"provisional", "reported_only"}:
            rows = int(row.get("source_rows_n") or 0)
            for node_id in nodes:
                assign(node_id, TIER_ASSAYED if rows > 0 else TIER_COMPOSITE)
    calibration = yaml.safe_load(
        (active_root / "config" / "calibration.yaml").read_text(encoding="utf-8")
    )
    if calibration["adhesion_objective"]["readouts"]:
        assign("OUT_STABLE_ADHESION", TIER_ENDPOINT)
    return tiers


def _group(facts: StructuralFacts, node_id: str) -> str:
    if node_id.startswith("IN_"):
        return "input"
    if node_id.startswith("OUT_"):
        return "output"
    return facts.compartment_of.get(node_id, "extracellular")


def overview_positions(
    facts: StructuralFacts, sweeps: int = 8
) -> tuple[dict[str, tuple[float, float]], dict[str, tuple[float, float]]]:
    """Deterministic coordinates, and each band's (y_low, y_high) extent.

    x: inputs at -1.3, outputs one column past the deepest node, everything else
    at its dependency depth. y: bands stacked epithelium (top), interface, stroma,
    each as tall as its fullest depth column; inputs and outputs span the whole
    height. Order inside a column comes from alternating parent/child barycentre
    sweeps, ties broken by node id, so the render is reproducible byte-for-byte.
    """
    max_depth = max(facts.depth[n] for n in facts.node_ids if not n.startswith("OUT_"))
    x_of = {}
    for node_id in facts.node_ids:
        group = _group(facts, node_id)
        if group == "input":
            x_of[node_id] = -1.3
        elif group == "output":
            x_of[node_id] = max_depth + 1.3
        else:
            x_of[node_id] = float(facts.depth[node_id])

    columns: dict[tuple[str, float], list[str]] = {}
    for node_id in facts.node_ids:
        group = _group(facts, node_id)
        key = ("io" if group in {"input", "output"} else group, x_of[node_id])
        columns.setdefault(key, []).append(node_id)
    for members in columns.values():
        members.sort()

    band_rows = {
        band: max((len(m) for (g, _x), m in columns.items() if g == band), default=1)
        for band, _label, _color in BANDS
    }
    gap = 0.8
    total = sum(band_rows.values()) + gap * (len(BANDS) - 1)
    extents: dict[str, tuple[float, float]] = {}
    top = total
    for band, _label, _color in BANDS:
        extents[band] = (top - band_rows[band], top)
        top -= band_rows[band] + gap
    extents["io"] = (0.0, total)

    parents: dict[str, list[str]] = {n: [] for n in facts.node_ids}
    children: dict[str, list[str]] = {n: [] for n in facts.node_ids}
    for source, target, _sign in facts.edges:
        parents[target].append(source)
        children[source].append(target)

    y_of: dict[str, float] = {}

    def place() -> None:
        for (group, _x), members in columns.items():
            low, high = extents[group]
            span = high - low
            count = len(members)
            for index, node_id in enumerate(members):
                y_of[node_id] = high - (index + 0.5) * span / count

    place()
    ordered_keys = sorted(columns, key=lambda k: (k[1], k[0]))
    for sweep in range(sweeps):
        neighbours = parents if sweep % 2 == 0 else children
        keys = ordered_keys if sweep % 2 == 0 else list(reversed(ordered_keys))
        for key in keys:
            members = columns[key]
            members.sort(
                key=lambda n: (
                    -(
                        sum(y_of[p] for p in neighbours[n]) / len(neighbours[n])
                        if neighbours[n]
                        else y_of[n]
                    ),
                    n,
                )
            )
        place()
    return {n: (x_of[n], y_of[n]) for n in facts.node_ids}, extents


def _alias_letters(facts: StructuralFacts) -> dict[str, str]:
    ordered = sorted(facts.alias_classes, key=lambda m: (-len(m), sorted(m)))
    return {
        node_id: chr(ord("A") + index)
        for index, members in enumerate(ordered)
        for node_id in members
    }


def render_network_overview(
    facts: StructuralFacts,
    tiers: dict[str, str],
    output_path: Path,
    *,
    title: str,
    subtitle: str,
    settings: OverviewSettings | None = None,
) -> dict[str, Any]:
    """Draw the overview and return the counts it asserts."""
    settings = settings or OverviewSettings()
    positions, extents = overview_positions(facts, settings.sweeps)
    inert = set(facts.phenotype_inert)
    unread = set(facts.unread_inputs)
    free = set(facts.free)
    absorbed = set(facts.absorbed_edges)
    never_binding = set(facts.never_binding_inhibitions)
    dead_edges = absorbed | never_binding
    letters = _alias_letters(facts)
    band_color = {band: color for band, _label, color in BANDS}

    xs = [p[0] for p in positions.values()]
    figure = plt.figure(figsize=settings.figsize, dpi=settings.dpi, facecolor=SURFACE)
    axis = figure.add_axes((0.035, 0.12, 0.74, 0.80))
    side = figure.add_axes((0.785, 0.12, 0.205, 0.80))
    side.axis("off")
    axis.set_facecolor(SURFACE)
    axis.axis("off")
    axis.set_xlim(min(xs) - 0.75, max(xs) + 0.75)
    axis.set_ylim(extents["io"][0] - 0.3, extents["io"][1] + 0.9)

    half_w, half_h = 0.43, 0.36
    for band, label, color in BANDS:
        low, high = extents[band]
        axis.add_patch(
            mpatches.FancyBboxPatch(
                (-0.6, low - 0.05),
                max(xs) - 1.3 + 0.2 + 0.6 - 0.0,
                high - low + 0.1,
                boxstyle="round,pad=0.02,rounding_size=0.15",
                facecolor=color,
                alpha=BAND_TINT_ALPHA,
                edgecolor="none",
                zorder=0,
            )
        )
        axis.text(
            -0.72,
            (low + high) / 2,
            label.upper(),
            rotation=90,
            fontsize=settings.caption_fontsize,
            fontweight="bold",
            color=color,
            ha="center",
            va="center",
            zorder=4,
        )
    for x, label in ((min(xs), "PROTOCOL INPUTS"), (max(xs), "PHENOTYPE OUTPUTS")):
        axis.text(
            x,
            extents["io"][1] + 0.55,
            label,
            fontsize=settings.caption_fontsize,
            fontweight="bold",
            color=IO_COLOR,
            ha="center",
            va="bottom",
        )
    max_depth = int(
        max(facts.depth[n] for n in facts.node_ids if not n.startswith("OUT_"))
    )
    for depth in range(max_depth + 1):
        axis.text(
            depth,
            extents["io"][1] + 0.55,
            f"depth {depth}",
            fontsize=settings.caption_fontsize - 1.8,
            color=INK_3,
            ha="center",
            va="bottom",
        )

    for source, target, sign in facts.edges:
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        dead = (source, target) in dead_edges
        inhibition = sign == "inhibition"
        axis.annotate(
            "",
            xy=(x1 - half_w, y1),
            xytext=(x0 + half_w, y0),
            zorder=1,
            arrowprops={
                "arrowstyle": "-"
                if dead
                else (
                    "-[,widthB=0.35,lengthB=0.0"
                    if inhibition
                    else "-|>,head_length=0.5,head_width=0.22"
                ),
                "color": DEAD_EDGE
                if dead
                else (INHIBITION if inhibition else ACTIVATION),
                "linewidth": 0.7 if dead else (1.0 if inhibition else 0.8),
                "linestyle": (0, (1.2, 1.8)) if dead else "solid",
                "alpha": 0.95 if dead else (0.75 if inhibition else 0.45),
                "shrinkA": 0,
                "shrinkB": 0,
                "connectionstyle": "arc3,rad=0.06",
            },
        )

    for node_id in facts.node_ids:
        x, y = positions[node_id]
        group = _group(facts, node_id)
        is_inert = node_id in inert
        edge_color = band_color.get(group, IO_COLOR)
        axis.add_patch(
            mpatches.FancyBboxPatch(
                (x - half_w, y - half_h),
                2 * half_w,
                2 * half_h,
                boxstyle="round,pad=0.0,rounding_size=0.08",
                linewidth=2.6 if node_id in free else 1.0,
                edgecolor=edge_color,
                facecolor=INERT_FILL if is_inert else "#FFFFFF",
                hatch="////" if is_inert else None,
                zorder=2,
            )
        )
        if is_inert:
            axis.patches[-1].set_hatchcolor(HATCH)
        label = _short(node_id)
        if node_id in tiers:
            label = f"{TIER_GLYPH[tiers[node_id]]} {label}"
        if node_id in unread:
            label = f"{label}\n(read by no rule)"
        axis.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=settings.node_fontsize
            * min(1.0, 20.0 / max(len(line) for line in label.split("\n"))),
            fontweight="bold" if node_id in tiers else "normal",
            color=INK_2 if is_inert else INK,
            zorder=3,
        )
        if node_id in letters:
            axis.text(
                x + half_w - 0.03,
                y + half_h - 0.02,
                letters[node_id],
                ha="right",
                va="top",
                fontsize=settings.node_fontsize - 0.4,
                fontweight="bold",
                color=INK_2,
                zorder=3,
            )

    summary = structural_summary(facts)
    summary["absorbed_or_never_binding_dependencies"] = len(dead_edges)
    summary["measurement_tiers"] = {
        tier: sorted(n for n, t in tiers.items() if t == tier) for tier in TIER_GLYPH
    }
    figure.text(
        0.035,
        0.975,
        title,
        fontsize=settings.caption_fontsize + 7,
        fontweight="bold",
        color=INK,
        va="top",
    )
    figure.text(
        0.035,
        0.945,
        subtitle,
        fontsize=settings.caption_fontsize + 1.5,
        color=INK_2,
        va="top",
    )

    # Side panel: the alias classes, spelled out, then the tiers.
    lines: list[tuple[str, dict[str, Any]]] = [
        ("Exact Boolean aliases (identical function over", {"fontweight": "bold"}),
        (
            f"all {summary['enumerated_states']:,} free-variable assignments)",
            {"fontweight": "bold"},
        ),
    ]
    ordered = sorted(facts.alias_classes, key=lambda m: (-len(m), sorted(m)))
    for index, members in enumerate(ordered):
        names = sorted(members, key=lambda n: (not n.startswith(("IN_", "S_PKA")), n))
        text = " = ".join(names)
        wrapped: list[str] = []
        current = f"{chr(ord('A') + index)} ({len(members)}): "
        for part in text.split(" = "):
            piece = part if current.endswith(": ") else f" = {part}"
            if len(current) + len(piece) > 46:
                wrapped.append(current)
                current = "      " + part
            else:
                current += piece
        wrapped.append(current)
        lines.extend(
            (w, {"family": "monospace", "fontsize": settings.caption_fontsize - 1.6})
            for w in wrapped
        )
    lines.append(("", {}))
    lines.append(("ADOC measurements", {"fontweight": "bold"}))
    for tier, glyph in TIER_GLYPH.items():
        members = summary["measurement_tiers"][tier]
        lines.append(
            (
                f"{glyph} {', '.join(members) or 'none'}",
                {"family": "monospace", "fontsize": settings.caption_fontsize - 1.6},
            )
        )
    y = 1.0
    for text, style in lines:
        side.text(
            0.0,
            y,
            text,
            transform=side.transAxes,
            va="top",
            ha="left",
            color=INK,
            **({"fontsize": settings.caption_fontsize - 0.6} | style),
        )
        y -= 0.021

    handles = [
        Line2D(
            [],
            [],
            color=ACTIVATION,
            linewidth=1.4,
            marker=">",
            markersize=6,
            label="activation (arrowhead)",
        ),
        Line2D(
            [],
            [],
            color=INHIBITION,
            linewidth=1.4,
            marker="|",
            markersize=9,
            markeredgewidth=2,
            label="inhibition (bar)",
        ),
        Line2D(
            [],
            [],
            color=DEAD_EDGE,
            linewidth=1.4,
            linestyle=(0, (1.2, 1.8)),
            label=f"absorbed or never-binding, no head ({summary['absorbed_or_never_binding_dependencies']})",
        ),
        Line2D(
            [],
            [],
            marker="s",
            color="none",
            markerfacecolor="#FFFFFF",
            markeredgecolor=INK_2,
            markeredgewidth=2.6,
            markersize=10,
            label=f"free variable: set, not computed ({summary['free_variables']})",
        ),
        mpatches.Patch(
            facecolor=INERT_FILL,
            edgecolor=INK_3,
            hatch="////",
            label=f"cannot change any phenotype output ({summary['phenotype_inert_nodes']})",
        ),
        Line2D(
            [],
            [],
            marker="$A$",
            color=INK_2,
            linestyle="none",
            markersize=8,
            label=f"alias-class letter ({summary['alias_classes']} classes)",
        ),
        *(
            Line2D(
                [],
                [],
                marker="none",
                linestyle="none",
                label=f"{TIER_GLYPH[t]}  {TIER_LABEL[t]}",
            )
            for t in TIER_GLYPH
        ),
    ]
    figure.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.035, 0.015),
        ncol=3,
        frameon=False,
        fontsize=settings.caption_fontsize - 0.2,
        handlelength=2.6,
    )
    figure.text(
        0.035,
        0.105,
        f"{summary['nodes']} nodes, {summary['dependencies']} dependencies, "
        f"{summary['distinct_functions']} distinct Boolean functions, "
        f"{len(facts.unread_inputs)} declared inputs read by no rule. Every node and "
        "edge is derived from network.bnd; exhaustive enumeration, no simulation. "
        "No probability, rate, initial condition, time course or evidence grade is "
        "drawn.",
        fontsize=settings.caption_fontsize - 0.4,
        color=INK_2,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_path, dpi=settings.dpi, facecolor=SURFACE, metadata={"Software": None}
    )
    plt.close(figure)
    return {
        "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "summary": summary,
    }


def _display(path: Path, root: Path) -> str:
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def render_network_overview_artifact(
    model_version: str = "adoc-literature-superset-v0.5.0",
    parent_version: str | None = "adoc-literature-superset-v0.4.0",
    root: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Render the overview and its provenance sidecar.

    When ``parent_version`` is given, the sidecar records whether this model's
    ``network.bnd`` is byte-identical to the parent's, and the subtitle says so --
    so a v0.5-labelled figure of an unchanged network cannot pass for a new one.
    """
    from dt_adoc.model.provenance import describe_file, repo_root, source_commit
    from dt_adoc.model.runtime import resolve_model

    active_root = root or repo_root()
    spec = resolve_model(model_version, active_root)
    facts = load_structure(model_version, active_root)
    tiers = measurement_tiers(facts, active_root)
    identity: dict[str, Any] | None = None
    subtitle = f"network.bnd sha256 {hashlib.sha256(spec.network_bnd.read_bytes()).hexdigest()[:12]}"
    if parent_version:
        parent = resolve_model(parent_version, active_root)
        same = spec.network_bnd.read_bytes() == parent.network_bnd.read_bytes()
        identity = {
            "parent_model_version": parent_version,
            "network_bnd_byte_identical_to_parent": same,
            "parent_network_bnd_sha256": hashlib.sha256(
                parent.network_bnd.read_bytes()
            ).hexdigest(),
        }
        subtitle = (
            f"Current development line (v0.5 scaffold). Executable network is "
            f"{'BYTE-IDENTICAL to' if same else 'DIFFERENT from'} {parent_version}: "
            + ("no node, rule or edge differs. " if same else "")
            + subtitle
        )
    target = active_root / (
        output_path
        or DEFAULT_OUTPUT_DIR
        / f"adoc_network_overview_{model_version.rsplit('-', 1)[-1]}.png"
    )
    result = render_network_overview(
        facts,
        tiers,
        target,
        title=f"{model_version}: executable MaBoSS network",
        subtitle=subtitle,
    )
    metadata = {
        "schema_version": "1.0",
        "artifact": "adoc_network_overview",
        "claim_boundary": (
            "Structural view of an executable Boolean network. No probability, "
            "time course, transition rate, initial condition or evidence grade. "
            "Measurement tiers state what ADOC assays and which mappings are "
            "licensed, not that any node's activity is measured."
        ),
        "model_version": model_version,
        "executable_identity": identity,
        "source_commit": source_commit(active_root),
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
            "calibration": describe_file(
                active_root / "config" / "calibration.yaml", root=active_root
            ).__dict__,
        },
        "generator_files": {
            relative: hashlib.sha256((active_root / relative).read_bytes()).hexdigest()
            for relative in (
                "src/dt_adoc/reporting/network_overview.py",
                "src/dt_adoc/reporting/structure.py",
                "src/dt_adoc/reporting/structure_figure.py",
            )
        },
        "summary": result["summary"],
        "alias_classes": sorted(sorted(m) for m in facts.alias_classes),
        "phenotype_inert_nodes": sorted(facts.phenotype_inert),
        "unread_inputs": sorted(facts.unread_inputs),
        "free_variables": sorted(facts.free),
        "absorbed_dependencies": sorted(list(p) for p in facts.absorbed_edges),
        "never_binding_inhibitions": sorted(
            list(p) for p in facts.never_binding_inhibitions
        ),
        "figure": {
            "path": _display(target, active_root),
            "sha256": result["sha256"],
            "deterministic": True,
        },
    }
    sidecar = target.with_name(target.stem + "_metadata.json")
    sidecar.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    metadata["metadata_path"] = _display(sidecar, active_root)
    return metadata


def main() -> int:
    metadata = render_network_overview_artifact()
    print(f"figure   {metadata['figure']['path']}  {metadata['figure']['sha256'][:12]}")
    print(f"metadata {metadata['metadata_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
