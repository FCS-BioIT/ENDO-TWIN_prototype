"""View model for the MaBoSS pathway-dynamics animation.

This module turns a sequential timeline plus the selected model's own metadata
tables into an ordered, fully positioned description of what each frame should
show. It deliberately imports no plotting library, so every rule below is unit
testable without a display and without a MaBoSS runtime.

Semantics, restated because they constrain every function here:

* A node value is ``P(node = ON)`` across simulated MaBoSS trajectories. It is
  not a concentration, expression level, secretion amount or flux.
* Input values are deterministic protocol settings, not simulated quantities.
* Edge opacity tracks the regulator node's P(ON). It is a visual
  regulator-activity cue only -- never causal flux, reaction rate, edge
  probability, regulatory strength or pathway flow. Marginal node
  probabilities cannot establish joint edge activity.
* Time is MaBoSS relative time; no mapping to hours exists.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

import yaml

from dt_adoc.model.catalog import load_tsv
from dt_adoc.model.runtime import ModelRuntimeSpec, resolve_model
from dt_adoc.model.topology import derive_dependencies, parse_bnd_rules

CONFIG_RELATIVE_PATH = Path("config") / "visualization.yaml"

#: Fields owned by the model's own tables. The visualization config may not
#: define them, so a presentation change can never silently restate biology.
BIOLOGICAL_FIELDS = frozenset(
    {
        "nodes",
        "node_dictionary",
        "edges",
        "edge_evidence",
        "phenotypes",
        "phenotype_contract",
        "compartment",
        "model_role",
        "confidence",
        "logic",
        "sign",
    }
)

VIEW_OVERVIEW = "overview"
VIEW_FULL = "full"
VIEWS = (VIEW_OVERVIEW, VIEW_FULL)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_visualization_config(root: Path | None = None) -> dict[str, Any]:
    """Load and structurally validate the visualization configuration."""
    active_root = root or repo_root()
    path = active_root / CONFIG_RELATIVE_PATH
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{CONFIG_RELATIVE_PATH} must contain a mapping.")
    # `edges` here is edge *styling*, not an edge list; everything else named
    # in BIOLOGICAL_FIELDS would be a second, undocumented biology source.
    intruders = (set(payload) & BIOLOGICAL_FIELDS) - {"edges"}
    if intruders:
        raise ValueError(
            "config/visualization.yaml carries visual metadata only; "
            f"remove biological key(s): {sorted(intruders)}"
        )
    for required in ("compartments", "regions", "panels", "compartment_classes"):
        if required not in payload:
            raise ValueError(f"{CONFIG_RELATIVE_PATH} is missing '{required}'.")
    for name, compartment in payload["compartments"].items():
        region = compartment.get("region")
        if region not in payload["regions"]:
            raise ValueError(f"Compartment '{name}' names unknown region '{region}'.")
    return payload


# --- Colour ---------------------------------------------------------------


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    text = value.lstrip("#")
    if len(text) != 6:
        raise ValueError(f"Expected a 6-digit hex colour, got {value!r}.")
    return tuple(int(text[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(
        f"{round(max(0.0, min(1.0, channel)) * 255):02X}" for channel in rgb
    )


def probability_to_color(probability: float, *, pale: str, saturated: str) -> str:
    """Map P(node = ON) onto a compartment colour ramp.

    Deterministic and monotonic: a linear interpolation in RGB from ``pale`` at
    P=0 to ``saturated`` at P=1. Intermediate probabilities stay visibly
    intermediate; they are never rounded to an ON/OFF colour.
    """
    if not math.isfinite(probability):
        raise ValueError("Cannot colour a non-finite probability.")
    clamped = max(0.0, min(1.0, float(probability)))
    low = _hex_to_rgb(pale)
    high = _hex_to_rgb(saturated)
    return _rgb_to_hex(
        tuple(
            start + (end - start) * clamped
            for start, end in zip(low, high, strict=True)
        )
    )


# --- Node and edge view models -------------------------------------------


@dataclass(frozen=True)
class NodeView:
    """A model node with its resolved presentation metadata and position."""

    node_id: str
    label: str
    short_label: str
    compartment_class: str
    source_compartment: str
    model_role: str
    confidence: str
    region: str
    position: tuple[float, float]
    uncertain: bool
    is_input: bool
    is_output: bool


@dataclass(frozen=True)
class EdgeView:
    """A model edge with static sign-derived styling."""

    source: str
    target: str
    sign: str
    confidence: str
    color: str
    style: str
    cross_compartment: bool


@dataclass(frozen=True)
class PanelView:
    """One synchronized time-series panel."""

    key: str
    title: str
    axis_label: str
    members: tuple[str, ...]


@dataclass(frozen=True)
class NetworkView:
    """Everything needed to draw a frame, fixed for the whole animation."""

    model_id: str
    model_version: str
    view: str
    nodes: tuple[NodeView, ...]
    edges: tuple[EdgeView, ...]
    panels: tuple[PanelView, ...]
    compartments: dict[str, dict[str, Any]]
    regions: dict[str, list[float]]
    edge_style: dict[str, Any]

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(node.node_id for node in self.nodes)

    def node(self, node_id: str) -> NodeView:
        for candidate in self.nodes:
            if candidate.node_id == node_id:
                return candidate
        raise KeyError(node_id)

    @property
    def positions(self) -> dict[str, tuple[float, float]]:
        return {node.node_id: node.position for node in self.nodes}


def classify_node(
    node_id: str,
    compartment: str,
    config: dict[str, Any],
) -> str:
    """Resolve a node's visual compartment class.

    Prefix wins for protocol inputs and phenotype outputs; the model's own
    ``compartment`` column decides the rest. This is what keeps ECM and lumen
    nodes in the extracellular band rather than inside the stromal cell.
    """
    for prefix, class_name in config.get("prefix_classes", {}).items():
        if node_id.startswith(prefix):
            return str(class_name)
    mapped = config.get("compartment_classes", {}).get(compartment)
    if mapped is None:
        raise ValueError(
            f"Node {node_id} has compartment '{compartment}', which "
            "config/visualization.yaml does not map to a visual class."
        )
    return str(mapped)


def _grid_positions(
    count: int,
    box: list[float],
    *,
    horizontal: bool,
) -> list[tuple[float, float]]:
    """Evenly place ``count`` slots inside a region box.

    Placement depends only on the count and the box, so a node keeps the same
    coordinates in every frame of the animation.
    """
    if count == 0:
        return []
    x0, y0, x1, y1 = box
    if horizontal:
        columns = count
        rows = 1
        if count > 7:
            rows = 2
            columns = (count + 1) // 2
    else:
        columns = 1 if count <= 8 else 2
        rows = (count + columns - 1) // columns

    positions: list[tuple[float, float]] = []
    for index in range(count):
        if horizontal:
            column = index % columns
            row = index // columns
        else:
            column = index // rows
            row = index % rows
        x = x0 + (x1 - x0) * ((column + 0.5) / columns)
        # Top-to-bottom within a column reads in the same order as the config.
        y = y1 - (y1 - y0) * ((row + 0.5) / rows)
        positions.append((round(x, 6), round(y, 6)))
    return positions


def _select_node_ids(
    *,
    view: str,
    model_version: str,
    dictionary_rows: list[dict[str, str]],
    config: dict[str, Any],
) -> list[str]:
    available = [row["node_id"] for row in dictionary_rows]
    if view == VIEW_FULL:
        return available
    overview = config.get("overview_nodes", {})
    requested = overview.get(model_version) or overview.get("default") or []
    known = set(available)
    unknown = [node_id for node_id in requested if node_id not in known]
    if unknown:
        raise ValueError(
            f"config/visualization.yaml lists node(s) absent from "
            f"{model_version}: {unknown}"
        )
    return list(requested) if requested else available


def build_network_view(
    *,
    model_version: str,
    view: str = VIEW_OVERVIEW,
    root: Path | None = None,
    config: dict[str, Any] | None = None,
    model_spec: ModelRuntimeSpec | None = None,
) -> NetworkView:
    """Assemble the fixed frame geometry for one model and view."""
    if view not in VIEWS:
        raise ValueError(f"Unknown view '{view}'; expected one of {VIEWS}.")
    active_root = root or repo_root()
    settings = config or load_visualization_config(active_root)
    spec = model_spec or resolve_model(model_version, active_root)

    dictionary_rows = load_tsv(spec.node_dictionary)
    by_id = {row["node_id"]: row for row in dictionary_rows}
    selected = _select_node_ids(
        view=view,
        model_version=spec.model_version,
        dictionary_rows=dictionary_rows,
        config=settings,
    )

    uncertain_roles = set(settings.get("uncertainty", {}).get("roles", []))
    uncertain_confidences = set(settings.get("uncertainty", {}).get("confidences", []))
    short_labels = settings.get("short_labels", {})
    overrides = settings.get("positions", {}) or {}

    grouped: dict[str, list[str]] = {}
    for node_id in selected:
        row = by_id[node_id]
        class_name = classify_node(node_id, row["compartment"], settings)
        grouped.setdefault(class_name, []).append(node_id)

    nodes: list[NodeView] = []
    for class_name, node_ids in grouped.items():
        compartment = settings["compartments"][class_name]
        region = str(compartment["region"])
        box = settings["regions"][region]
        horizontal = region in {"top", "bottom"}
        coordinates = _grid_positions(len(node_ids), box, horizontal=horizontal)
        for node_id, position in zip(node_ids, coordinates, strict=True):
            row = by_id[node_id]
            role = row.get("model_role", "")
            confidence = row.get("confidence", "")
            override = overrides.get(node_id)
            nodes.append(
                NodeView(
                    node_id=node_id,
                    label=row.get("label", node_id),
                    short_label=str(short_labels.get(node_id, node_id)),
                    compartment_class=class_name,
                    source_compartment=row["compartment"],
                    model_role=role,
                    confidence=confidence,
                    region=region,
                    position=tuple(override) if override else position,
                    uncertain=(
                        role in uncertain_roles or confidence in uncertain_confidences
                    ),
                    is_input=node_id.startswith("IN_"),
                    is_output=node_id.startswith("OUT_"),
                )
            )

    order = {node_id: index for index, node_id in enumerate(selected)}
    nodes.sort(key=lambda node: order[node.node_id])
    edges = build_edge_views(
        nodes=nodes,
        model_spec=spec,
        config=settings,
    )
    panels = build_panels(
        node_ids=[node.node_id for node in nodes],
        model_spec=spec,
        config=settings,
    )
    return NetworkView(
        model_id=spec.model_id,
        model_version=spec.model_version,
        view=view,
        nodes=tuple(nodes),
        edges=edges,
        panels=panels,
        compartments=settings["compartments"],
        regions=settings["regions"],
        edge_style=settings.get("edges", {}),
    )


def build_edge_views(
    *,
    nodes: list[NodeView],
    model_spec: ModelRuntimeSpec,
    config: dict[str, Any],
) -> tuple[EdgeView, ...]:
    """Derive edges from what the network computes, styled by its evidence.

    **Existence and sign come from ``network.bnd``, not from the evidence
    table.** They used to come from ``edge_evidence.tsv``, which is a record of
    what has been *cited*, not of what the model *computes*. The two are not the
    same set and are not even nested: for the superset the network computes 96
    non-self dependencies against 93 evidence rows, so the figure drew the
    retired ``LE081`` relation the model does not compute and omitted four real
    dependencies. Evidence availability must not define topology.

    Polarity is derived by the same recursive-descent parse the parity
    reconciler uses, so a rule that negates a parenthesised group is signed
    correctly. Evidence is joined in only to style confidence; an edge with no
    evidence row is still drawn, with empty confidence, because the network
    computes it either way.

    Edges touching a node outside the current view are dropped rather than
    drawn to nowhere.
    """
    style = config.get("edges", {})
    class_by_id = {node.node_id: node.compartment_class for node in nodes}
    uncertain = set(style.get("uncertain_confidences", []))
    confidence_by_pair = {
        (row["source"], row["target"]): row.get("confidence", "")
        for row in load_tsv(model_spec.edge_evidence)
    }
    dependencies = derive_dependencies(parse_bnd_rules(model_spec.network_bnd))
    views: list[EdgeView] = []
    for (source, target), derived_sign in sorted(dependencies.items()):
        if source not in class_by_id or target not in class_by_id:
            continue
        sign = "activation" if derived_sign == "ambiguous" else derived_sign
        confidence = confidence_by_pair.get((source, target), "")
        views.append(
            EdgeView(
                source=source,
                target=target,
                sign=sign,
                confidence=confidence,
                color=(
                    style.get("inhibition_color", "#BC4749")
                    if sign == "inhibition"
                    else style.get("activation_color", "#2D6A4F")
                ),
                style="dashed" if confidence in uncertain else "solid",
                cross_compartment=class_by_id[source] != class_by_id[target],
            )
        )
    return tuple(views)


def build_panels(
    *,
    node_ids: list[str],
    model_spec: ModelRuntimeSpec,
    config: dict[str, Any],
) -> tuple[PanelView, ...]:
    """Resolve the time-series panels against what the model actually has.

    Members are a preferred ordering; anything the selected model lacks is
    skipped silently so a single configuration serves every model. Nothing is
    substituted or invented to fill an empty panel.
    """
    available = set(node_ids)
    panels: list[PanelView] = []
    for spec in config.get("panels", []):
        if spec.get("source") == "phenotype_contract":
            members = tuple(
                row["phenotype_id"]
                for row in load_tsv(model_spec.phenotype_contract)
                if str(row.get("executable", "")).lower() == "true"
                and row.get("category") == "primary"
                and row["phenotype_id"] in available
            )
        else:
            members = tuple(
                node_id for node_id in spec.get("members", []) if node_id in available
            )
        if not members:
            continue
        panels.append(
            PanelView(
                key=str(spec["key"]),
                title=str(spec["title"]),
                axis_label=str(spec.get("axis_label", "P(node = ON)")),
                members=members,
            )
        )
    return tuple(panels)


# --- Frame sampling -------------------------------------------------------


def sample_frame_indices(row_count: int, stride: int) -> list[int]:
    """Sample row indices for animation frames.

    The final row is always included so the last frame shows the same values
    the smoke reports as final.
    """
    if row_count <= 0:
        return []
    step = max(int(stride), 1)
    indices = list(range(0, row_count, step))
    if indices[-1] != row_count - 1:
        indices.append(row_count - 1)
    return indices


def frame_values(
    frame: Any,
    row_index: int,
    node_ids: tuple[str, ...] | list[str],
) -> dict[str, float]:
    """Read one frame's node values straight out of the timeline table."""
    row = frame.iloc[row_index]
    return {node_id: float(row[node_id]) for node_id in node_ids if node_id in row}
