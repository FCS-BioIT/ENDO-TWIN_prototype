"""What each node is, and how the repository observes it, for figure labels.

Read from the committed contracts, never hand-maintained:

- ``label``: the model's ``node_dictionary.tsv``;
- ``defining_entity``: ``config/node_entity_map.tsv`` (entity and level). A
  ``derived`` row has no defining gene: the node is a combination of other
  nodes, and its composition is read off its executed rule (``composed_of``);
- ``marker_genes``: ``support_feature`` rows of ``docs/u6_semantics/component_map.tsv``
  -- genes the repository *reads the node through*, not its molecular definition;
- ``measurement_type``: ``docs/u6_semantics/node_semantics.tsv``;
- ``is_phenotype``: listed in the model's ``phenotype_contract.tsv``.

The two U6 tables were generated from the scRNA observation map, which is
pinned to an earlier model version; ``annotation_sources`` records the files
and their hashes so a reader can see what the labels rest on.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from dt_adoc.model.provenance import describe_file, repo_root
from dt_adoc.model.runtime import resolve_model

ENTITY_MAP = Path("config/node_entity_map.tsv")
COMPONENT_MAP = Path("docs/u6_semantics/component_map.tsv")
NODE_SEMANTICS = Path("docs/u6_semantics/node_semantics.tsv")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def node_annotations(
    model_version: str, root: Path | None = None
) -> dict[str, dict[str, Any]]:
    active_root = root or repo_root()
    spec = resolve_model(model_version, active_root)
    labels = {r["node_id"]: r for r in _rows(spec.node_dictionary)}
    phenotypes = {r["phenotype_id"] for r in _rows(spec.phenotype_contract)}
    entities = {
        r["node_id"]: r
        for r in _rows(active_root / ENTITY_MAP)
        if r["model_version"] == model_version
    }
    markers: dict[str, list[str]] = {}
    for r in _rows(active_root / COMPONENT_MAP):
        if r.get("role") != "support_feature":
            continue
        symbol = r.get("current_hgnc_symbol") or r.get("symbol_as_committed")
        if symbol and symbol not in markers.setdefault(r["model_node"], []):
            markers[r["model_node"]].append(symbol)
    semantics = {r["model_node"]: r for r in _rows(active_root / NODE_SEMANTICS)}
    text = spec.network_bnd.read_text(encoding="utf-8")
    logic = dict(re.findall(r"Node\s+(\w+)\s*\{\s*logic\s*=\s*([^;]+);", text))
    out = {}
    for node, row in labels.items():
        entity = entities.get(node, {})
        derived = entity.get("aggregation") == "derived"
        regulators = sorted(
            set(re.findall(r"[A-Za-z_]\w*", logic.get(node, "")))
            - {"and", "or", "not", node}
        )
        out[node] = {
            "node": node,
            "label": row.get("label") or node,
            "compartment": row.get("compartment", ""),
            "defining_entity": "" if derived else entity.get("entity", ""),
            "entity_level": "" if derived else entity.get("level", ""),
            "is_composite": derived,
            "composed_of": regulators if derived else [],
            "marker_genes": markers.get(node, []),
            "measurement_type": semantics.get(node, {}).get(
                "measurement_type", "unknown"
            ),
            "is_phenotype": node in phenotypes,
        }
    return out


def annotation_sources(
    model_version: str, root: Path | None = None
) -> list[dict[str, Any]]:
    active_root = root or repo_root()
    spec = resolve_model(model_version, active_root)
    return [
        describe_file(p, root=active_root).__dict__
        for p in (
            spec.node_dictionary,
            spec.phenotype_contract,
            active_root / ENTITY_MAP,
            active_root / COMPONENT_MAP,
            active_root / NODE_SEMANTICS,
        )
    ]


def display_label(a: dict[str, Any], max_markers: int = 5) -> str:
    """``Label [marker, ...]`` when the repo observes the node through marker
    genes; ``Label = f(A, B)`` for a composite with no markers; else the label."""
    base = a["label"]
    genes = a["marker_genes"]
    if not genes:
        if a["is_composite"] and a["composed_of"]:
            parts = a["composed_of"]
            shown = ", ".join(parts[:3]) + (
                f", +{len(parts) - 3}" if len(parts) > 3 else ""
            )
            return f"{base}\n= f({shown})"
        return base
    shown = ", ".join(genes[:max_markers]) + (
        f", +{len(genes) - max_markers}" if len(genes) > max_markers else ""
    )
    return f"{base} [{shown}]"
