"""Static validation for the provisional DT_ADOC Phase 1 model contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from dt_adoc.model.catalog import (
    default_paths,
    load_edges,
    load_nodes,
    load_phenotype_definitions,
    load_protocols,
    load_rules,
    load_tsv,
)
from dt_adoc.model.compile import render_bnd, render_condition_cfg
from dt_adoc.model.runtime import available_models, resolve_model
from dt_adoc.model.superset_family import (
    MODEL_VERSION as SUPERSET_VERSION,
)
from dt_adoc.model.superset_family import (
    validate_family as verify_superset_family,
)

TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
IGNORE_TOKENS = {"and", "or", "not", "TRUE", "FALSE", "Node", "logic"}


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)

    def payload(self) -> dict[str, object]:
        return {
            "status": "valid" if not self.errors else "invalid",
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks,
        }


def _extract_nodes_from_bnd(path: Path) -> list[str]:
    names: list[str] = []
    pattern = re.compile(r"^\s*Node\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            names.append(match.group(1))
    return names


def _extract_logic_from_bnd(path: Path) -> dict[str, str]:
    logic_by_node: dict[str, str] = {}
    current_node: str | None = None
    node_pattern = re.compile(r"^\s*Node\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{")
    logic_pattern = re.compile(r"^\s*logic\s*=\s*(.+?)\s*;\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        node_match = node_pattern.match(line)
        if node_match:
            current_node = node_match.group(1)
            continue
        logic_match = logic_pattern.match(line)
        if logic_match and current_node is not None:
            logic_by_node[current_node] = logic_match.group(1)
    return logic_by_node


def _extract_cfg_assignments(path: Path) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("//", 1)[0].strip()
        if not line or "=" not in line:
            continue
        left, right = line.split("=", 1)
        left = left.strip()
        right = right.strip().rstrip(";")
        assignments[left] = right
    return assignments


def _tokens(expression: str) -> set[str]:
    return {
        token
        for token in TOKEN_RE.findall(expression)
        if token not in IGNORE_TOKENS and not token.isupper()
    } | {
        token
        for token in TOKEN_RE.findall(expression)
        if token.startswith(("IN_", "E_", "S_", "X_", "OUT_"))
    }


def _duration_fallbacks(root: Path | None = None) -> dict[str, float]:
    active_root = root or Path(__file__).resolve().parents[3]
    payload: dict[str, Any] = yaml.safe_load(
        (active_root / "config" / "calibration.yaml").read_text()
    )
    durations = payload.get("sequential_execution", {}).get(
        "relative_phase_durations", {}
    )
    return {str(key): float(value) for key, value in durations.items()}


def _validate_runtime_model(
    report: ValidationReport,
    *,
    model_version: str,
    root: Path | None = None,
) -> None:
    spec = resolve_model(model_version, root)
    model_nodes = _extract_nodes_from_bnd(spec.network_bnd)
    node_catalog = {row["node_id"] for row in load_tsv(spec.node_dictionary)}
    if set(model_nodes) != node_catalog:
        report.errors.append(
            f"{model_version} network.bnd nodes do not match {spec.node_dictionary}"
        )
    else:
        report.checks.append(
            f"{model_version} network.bnd nodes match its node dictionary"
        )
    if (
        model_version == "adoc-literature-v0.2.0"
        and spec.node_dictionary.parent != spec.model_root
    ):
        report.errors.append(
            "silent baseline-node-catalog reuse for literature model is not allowed"
        )
    known_nodes = set(model_nodes)
    for protocol_id in spec.default_smoke_protocols:
        condition_cfg = spec.condition_dir / f"{protocol_id}.cfg"
        if not condition_cfg.exists():
            report.errors.append(
                f"{model_version} missing expected condition cfg {condition_cfg}"
            )
            continue
        cfg_nodes = {
            key.rsplit(".", 1)[0]
            for key in _extract_cfg_assignments(condition_cfg)
            if key.endswith((".istate", ".is_internal"))
        }
        unknown = sorted(cfg_nodes - known_nodes)
        if unknown:
            report.errors.append(
                f"{model_version} condition {protocol_id} references unknown nodes: {', '.join(unknown)}"
            )
    if model_version == SUPERSET_VERSION:
        try:
            verify_superset_family(spec.model_root)
        except (
            OSError,
            ValueError,
        ) as exc:  # pragma: no cover - exercised in integration tests
            report.errors.append(
                f"{SUPERSET_VERSION} family verification failed: {exc}"
            )
        else:
            report.checks.append(f"{SUPERSET_VERSION} family deliverables verified")
    report.checks.append(f"{model_version} runtime artifacts resolved successfully")


def validate(
    root: Path | None = None,
    *,
    model_version: str | None = None,
) -> ValidationReport:
    report = ValidationReport()
    paths = default_paths(root)
    nodes = load_nodes(root)
    edges = load_edges(root)
    rules = load_rules(root)["rules"]
    phenotype_defs = load_phenotype_definitions(root)["phenotypes"]
    protocols = load_protocols(root)["protocols"]
    duration_fallbacks = _duration_fallbacks(root)

    node_ids = [row["node_id"] for row in nodes]
    node_id_set = set(node_ids)
    if len(node_ids) != len(node_id_set):
        report.errors.append("models/specs/nodes.tsv contains duplicate node_id values")
    else:
        report.checks.append("node ids are unique")

    edge_ids = [row["edge_id"] for row in edges]
    if len(edge_ids) != len(set(edge_ids)):
        report.errors.append("models/specs/edges.tsv contains duplicate edge_id values")
    else:
        report.checks.append("edge ids are unique")

    for edge in edges:
        for key in ("source", "target"):
            if edge[key] not in node_id_set:
                report.errors.append(
                    f"edge {edge['edge_id']} references unknown {key} node {edge[key]}"
                )
    report.checks.append("edge sources and targets resolve against node ids")

    rule_map = {row["node_id"]: row for row in rules}
    missing_rules = sorted(node_id_set - set(rule_map))
    if missing_rules:
        report.errors.append(f"missing rules for nodes: {', '.join(missing_rules)}")
    else:
        report.checks.append("every node has a rule entry")

    for node_id, row in rule_map.items():
        expression = row.get("expression")
        if expression is None:
            report.warnings.append(f"node {node_id} has no executable expression")
            continue
        unknown = sorted(_tokens(str(expression)) - node_id_set)
        if unknown:
            report.errors.append(
                f"rule for {node_id} references unknown nodes: {', '.join(unknown)}"
            )
    report.checks.append("rule expressions resolve against node ids")

    baseline_bnd = paths.baseline_dir / "network.bnd"
    rendered_bnd = render_bnd(root)
    committed_bnd = baseline_bnd.read_text(encoding="utf-8")
    if rendered_bnd != committed_bnd:
        report.errors.append(
            "rendered models/specs artifacts do not match models/baseline/adoc-core-v0.1.0/network.bnd"
        )
    else:
        report.checks.append("compiled BND matches the committed baseline network")

    bnd_nodes = _extract_nodes_from_bnd(baseline_bnd)
    if bnd_nodes != node_ids:
        report.errors.append(
            "network.bnd node order does not match models/specs/nodes.tsv"
        )
    else:
        report.checks.append("network.bnd node order matches models/specs/nodes.tsv")

    executable_phenotypes = {
        row["phenotype_id"] for row in phenotype_defs if row.get("executable")
    }
    missing_exec_nodes = sorted(executable_phenotypes - node_id_set)
    if missing_exec_nodes:
        report.errors.append(
            "executable phenotypes missing from node catalog: "
            + ", ".join(missing_exec_nodes)
        )
    else:
        report.checks.append("executable phenotypes exist in the node catalog")

    for protocol in protocols:
        protocol_id = protocol["protocol_id"]
        protocol_class = str(
            protocol.get(
                "protocol_class",
                "embryo_challenge"
                if protocol_id.startswith("adhesion_challenge_")
                else "maternal_state",
            )
        )
        if protocol_class not in {"maternal_state", "embryo_challenge"}:
            report.errors.append(
                f"protocol {protocol_id} has unsupported protocol_class {protocol_class!r}"
            )
        for step in protocol["steps"]:
            relative_duration = float(
                step.get(
                    "relative_duration",
                    duration_fallbacks.get(step["step_id"], 1.0),
                )
            )
            if relative_duration <= 0:
                report.errors.append(
                    f"protocol {protocol_id} step {step['step_id']} must have positive relative_duration"
                )
        final_inputs = protocol["steps"][-1]["input_states"]
        if protocol_class == "maternal_state" and (
            final_inputs.get("IN_EMBRYO_PRESENT")
            or final_inputs.get("IN_TROPHECTODERM_COMPETENT")
        ):
            report.errors.append(
                f"maternal_state protocol {protocol_id} must keep embryo challenge inputs OFF in its final step"
            )
        if protocol_class == "embryo_challenge" and (
            not final_inputs.get("IN_EMBRYO_PRESENT")
            or not final_inputs.get("IN_TROPHECTODERM_COMPETENT")
        ):
            report.errors.append(
                f"embryo_challenge protocol {protocol_id} must set both embryo challenge inputs ON in its final step"
            )
        protocol_model_version = str(protocol["model_version"])
        if protocol_model_version == "adoc-core-v0.1.0":
            condition_path = Path(
                paths.baseline_dir / "conditions" / f"{protocol_id}.cfg"
            )
            rendered_cfg = {
                key.strip(): value.strip().rstrip(";")
                for key, value in (
                    line.split("=", 1)
                    for line in render_condition_cfg(
                        protocol_id,
                        root,
                        model_version=protocol_model_version,
                    ).splitlines()
                    if line.strip()
                )
            }
            committed_cfg = _extract_cfg_assignments(condition_path)
            if rendered_cfg != committed_cfg:
                report.errors.append(
                    f"compiled condition cfg for {protocol_id} does not match {condition_path}"
                )
        else:
            condition_path = (root or Path(__file__).resolve().parents[3]) / protocol[
                "condition_cfg"
            ]
        protocol_spec = resolve_model(protocol_model_version, root)
        protocol_node_ids = set(_extract_nodes_from_bnd(protocol_spec.network_bnd))
        assignments = _extract_cfg_assignments(condition_path)
        for key in assignments:
            if not key.endswith(".istate"):
                report.warnings.append(
                    f"{condition_path} contains a non-istate assignment {key}; static validation only checks input-state overrides"
                )
                continue
            node_id = key.removesuffix(".istate")
            if node_id not in protocol_node_ids:
                report.errors.append(
                    f"{condition_path} references unknown node {node_id}"
                )
        report.checks.append(
            f"condition cfg {protocol_id} references known nodes for {protocol_model_version}"
        )
        report.checks.append(
            f"protocol {protocol_id} satisfies the maternal-versus-challenge input contract"
        )

    model_versions = (
        [model_version] if model_version is not None else sorted(available_models(root))
    )
    for candidate in model_versions:
        spec = resolve_model(candidate, root)
        cfg_assignments = _extract_cfg_assignments(spec.baseline_cfg)
        for required_key in ("sample_count", "max_time", "time_tick"):
            if required_key not in cfg_assignments:
                report.errors.append(f"{spec.baseline_cfg} is missing {required_key}")
        report.checks.append(
            f"{candidate} baseline.cfg contains structural simulation defaults"
        )
        _validate_runtime_model(report, model_version=candidate, root=root)

    for protocol in protocols:
        protocol_model_version = str(protocol["model_version"])
        spec = resolve_model(protocol_model_version, root)
        condition_path = (root or Path(__file__).resolve().parents[3]) / protocol[
            "condition_cfg"
        ]
        if not condition_path.is_file():
            report.errors.append(
                f"protocol {protocol['protocol_id']} model_version {protocol_model_version} is missing condition cfg {condition_path}"
            )
            continue
        if condition_path.parent != spec.condition_dir:
            report.errors.append(
                f"protocol {protocol['protocol_id']} condition cfg is outside the selected model condition directory"
            )
        assignments = _extract_cfg_assignments(condition_path)
        model_node_ids = set(_extract_nodes_from_bnd(spec.network_bnd))
        for key in assignments:
            if not key.endswith(".istate"):
                continue
            node_id = key.removesuffix(".istate")
            if node_id not in model_node_ids:
                report.errors.append(
                    f"{condition_path} references unknown node {node_id} for model_version {protocol_model_version}"
                )
        report.checks.append(
            f"protocol {protocol['protocol_id']} condition cfg resolves against {protocol_model_version}"
        )

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--model-version", default=None)
    args = parser.parse_args(argv)
    report = validate(args.root, model_version=args.model_version)
    payload = report.payload()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload))
    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
