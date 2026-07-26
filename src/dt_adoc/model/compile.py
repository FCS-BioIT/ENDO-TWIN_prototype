"""Render conservative MaBoSS artifacts from the Phase 1 specification files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from dt_adoc.model.catalog import default_paths, load_nodes, load_rules
from dt_adoc.protocols.conditions import default_model_version


def _ordered_rules(
    rule_payload: dict[str, Any], rule_overrides: dict[str, str] | None = None
) -> dict[str, str]:
    overrides = rule_overrides or {}
    return {
        row["node_id"]: str(overrides.get(row["node_id"], row["expression"]))
        for row in rule_payload["rules"]
        if row.get("expression") is not None
    }


def render_bnd(
    root: Path | None = None, *, rule_overrides: dict[str, str] | None = None
) -> str:
    nodes = load_nodes(root)
    rules = _ordered_rules(load_rules(root), rule_overrides)
    lines = [
        "// Provisional Phase 1 ADOC baseline model.",
        "// Topology shared across maternal-state and embryo adhesion-challenge protocols.",
        "// Node-specific rates are intentionally omitted; MaBoSS implicit logic-driven defaults apply.",
        "",
    ]
    for node in nodes:
        node_id = node["node_id"]
        expression = rules.get(node_id)
        if expression is None:
            raise ValueError(f"missing rule for node {node_id}")
        lines.append(f"Node {node_id} {{")
        lines.append(f"  logic = {expression};")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_input_state_cfg(input_states: dict[str, bool]) -> str:
    return (
        "\n".join(
            f"{node_id}.istate = {'TRUE' if state else 'FALSE'};"
            for node_id, state in input_states.items()
        )
        + "\n"
    )


def render_condition_cfg(
    protocol_id: str,
    root: Path | None = None,
    *,
    model_version: str | None = None,
) -> str:
    paths = default_paths(root)
    payload = json.loads(paths.protocols_yaml.read_text(encoding="utf-8"))
    selected_model_version = model_version or default_model_version(root)
    match = next(
        (
            protocol
            for protocol in payload["protocols"]
            if protocol["protocol_id"] == protocol_id
            and protocol["model_version"] == selected_model_version
        ),
        None,
    )
    if match is None:
        raise ValueError(
            f"unknown protocol_id {protocol_id} for model_version {selected_model_version}"
        )
    step = match["steps"][-1]
    return render_input_state_cfg(step["input_states"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--emit-bnd", action="store_true")
    parser.add_argument("--emit-condition", metavar="PROTOCOL_ID")
    args = parser.parse_args(argv)
    if args.emit_bnd:
        print(render_bnd(args.root), end="")
    elif args.emit_condition:
        print(render_condition_cfg(args.emit_condition, args.root), end="")
    else:
        parser.error("one of --emit-bnd or --emit-condition is required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
