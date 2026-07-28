"""Load conservative DT_ADOC model specifications from repository-local files."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dt_adoc.model.provenance import repo_root


@dataclass(frozen=True)
class ModelCatalogPaths:
    nodes_tsv: Path
    edges_tsv: Path
    rules_yaml: Path
    uncertain_rules_yaml: Path
    phenotypes_yaml: Path
    parameter_scenarios_yaml: Path
    baseline_dir: Path
    extended_dir: Path
    protocols_yaml: Path
    perturbations_yaml: Path
    phenotype_definitions_yaml: Path


def default_paths(root: Path | None = None) -> ModelCatalogPaths:
    active_root = root or repo_root()
    return ModelCatalogPaths(
        nodes_tsv=active_root / "models/specs/nodes.tsv",
        edges_tsv=active_root / "models/specs/edges.tsv",
        rules_yaml=active_root / "models/specs/rules.yaml",
        uncertain_rules_yaml=active_root / "models/specs/uncertain_rule_variants.yaml",
        phenotypes_yaml=active_root / "models/specs/phenotypes.yaml",
        parameter_scenarios_yaml=active_root / "models/specs/parameter_scenarios.yaml",
        baseline_dir=active_root / "models/baseline/adoc-core-v0.1.0",
        extended_dir=active_root / "models/extended/adoc-literature-v0.2.0",
        protocols_yaml=active_root / "config/protocols.yaml",
        perturbations_yaml=active_root / "config/perturbations.yaml",
        phenotype_definitions_yaml=active_root / "config/phenotype_definitions.yaml",
    )


def load_jsonish(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_nodes(root: Path | None = None) -> list[dict[str, str]]:
    return load_tsv(default_paths(root).nodes_tsv)


def load_edges(root: Path | None = None) -> list[dict[str, str]]:
    return load_tsv(default_paths(root).edges_tsv)


def load_rules(root: Path | None = None) -> dict[str, Any]:
    return load_jsonish(default_paths(root).rules_yaml)


def load_phenotypes(root: Path | None = None) -> dict[str, Any]:
    return load_jsonish(default_paths(root).phenotypes_yaml)


def load_parameter_scenarios(root: Path | None = None) -> dict[str, Any]:
    return load_jsonish(default_paths(root).parameter_scenarios_yaml)


def load_protocols(root: Path | None = None) -> dict[str, Any]:
    return load_jsonish(default_paths(root).protocols_yaml)


def load_perturbations(root: Path | None = None) -> dict[str, Any]:
    return load_jsonish(default_paths(root).perturbations_yaml)


def load_phenotype_definitions(root: Path | None = None) -> dict[str, Any]:
    return load_jsonish(default_paths(root).phenotype_definitions_yaml)
