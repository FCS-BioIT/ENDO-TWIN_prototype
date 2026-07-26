"""MaBoSS runtime detection and continuation helpers."""

from __future__ import annotations

import math
import re
from importlib import metadata
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def _parse_state_label(state_label: str) -> set[str]:
    stripped = state_label.strip()
    if not stripped or stripped == "<nil>":
        return set()
    return {token.strip() for token in stripped.split(" -- ") if token.strip()}


NODE_BLOCK_RE = re.compile(
    r"(?ms)^(\s*Node\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{\n)(.*?)(^\s*\}\s*$)"
)
LOGIC_LINE_RE = re.compile(r"(?m)^(\s*logic\s*=\s*)(.+?)(\s*;\s*)$")


def set_istate(network: Any, nodes: Any, probability: Any) -> None:
    """Set an initial state while tolerating optional warnings kwarg support."""
    try:
        network.set_istate(nodes, probability, warnings=False)
    except TypeError:
        network.set_istate(nodes, probability)


def render_network_with_logic_overrides(
    network_text: str,
    *,
    logic_overrides: dict[str, str],
) -> str:
    """Return a .bnd payload with selected node logic expressions replaced."""
    if not logic_overrides:
        return network_text
    applied: set[str] = set()

    def _replace(match: re.Match[str]) -> str:
        header = match.group(1)
        node_id = match.group(2)
        body = match.group(3)
        closing = match.group(4)
        replacement = logic_overrides.get(node_id)
        if replacement is None:
            return match.group(0)

        def _logic_sub(logic_match: re.Match[str]) -> str:
            applied.add(node_id)
            return f"{logic_match.group(1)}{replacement}{logic_match.group(3)}"

        updated_body, count = LOGIC_LINE_RE.subn(_logic_sub, body, count=1)
        if count != 1:
            raise ValueError(f"node {node_id} does not contain exactly one logic line")
        return f"{header}{updated_body}{closing}"

    rendered = NODE_BLOCK_RE.sub(_replace, network_text)
    missing = sorted(set(logic_overrides) - applied)
    if missing:
        raise ValueError(
            "logic overrides referenced unknown or non-replaced nodes: "
            + ", ".join(missing)
        )
    return rendered


def apply_deterministic_overrides(
    network: Any,
    forced_nodes: dict[str, bool] | None,
) -> None:
    for node_id, state in (forced_nodes or {}).items():
        set_istate(network, node_id, [1.0 - float(state), float(state)])


def apply_node_marginals_independent(
    *,
    network: Any,
    result: Any,
    forced_nodes: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Apply the exact pinned-package marginal continuation semantics."""
    from maboss.simulation import (
        Simulation as ClassicalSimulation,  # pylint: disable=import-outside-toplevel
    )

    proxy = SimpleNamespace(network=network)
    ClassicalSimulation.continue_from_result(proxy, result)
    apply_deterministic_overrides(network, forced_nodes)
    node_count = 0
    for node_id in result.get_nodes_probtraj().iloc[-1].index:
        if node_id != "<nil>":
            node_count += 1
    return {
        "continuation_mode": "node_marginals_independent",
        "implementation": "maboss.simulation.Simulation.continue_from_result",
        "memory_node_count": node_count,
        "retained_state_count": 0,
        "dropped_probability_mass": 0.0,
        "probability_cutoff": None,
    }


def project_joint_distribution(
    *,
    last_states_probtraj: Any,
    memory_nodes: tuple[str, ...],
    probability_cutoff: float,
) -> dict[str, Any]:
    if not memory_nodes:
        raise ValueError("joint continuation requires at least one memory node")
    if probability_cutoff < 0.0:
        raise ValueError("probability_cutoff must be non-negative")
    last_row = last_states_probtraj.iloc[-1]
    projected: dict[tuple[int, ...], float] = {}
    source_state_count = 0
    for state_label, probability in last_row.items():
        value = float(probability)
        if not math.isfinite(value) or value < 0.0:
            raise ValueError("joint continuation encountered invalid state probability")
        if value == 0.0:
            continue
        source_state_count += 1
        active_nodes = _parse_state_label(str(state_label))
        state_tuple = tuple(
            1 if node_id in active_nodes else 0 for node_id in memory_nodes
        )
        projected[state_tuple] = projected.get(state_tuple, 0.0) + value
    filtered = {
        state: probability
        for state, probability in projected.items()
        if probability > probability_cutoff
    }
    retained_mass = sum(filtered.values())
    if retained_mass <= 0.0:
        raise ValueError("joint continuation retained no probability mass after cutoff")
    renormalized = {
        state: probability / retained_mass for state, probability in filtered.items()
    }
    return {
        "distribution": renormalized,
        "source_state_count": source_state_count,
        "retained_state_count": len(renormalized),
        "dropped_probability_mass": 1.0 - retained_mass,
        "renormalized": not math.isclose(retained_mass, 1.0),
    }


def apply_joint_distribution(
    *,
    network: Any,
    memory_nodes: tuple[str, ...],
    distribution: dict[tuple[int, ...], float],
    forced_nodes: dict[str, bool] | None = None,
) -> None:
    if not distribution:
        raise ValueError("joint continuation requires a non-empty distribution")
    set_istate(network, list(memory_nodes), distribution)
    apply_deterministic_overrides(network, forced_nodes)


def runtime_report() -> dict[str, str]:
    """Return a small runtime capability report without importing the engine."""
    payload = {
        "python_package": "maboss",
        "installed": "false",
        "version": "unavailable",
        "binary_path": "unavailable",
        "binary_present": "false",
        "cmaboss_available": "false",
        "classic_continue_from_result_available": "false",
        "cmaboss_continue_from_result_available": "false",
        "note": "Real simulation requires the official MaBoSS/PyMaBoSS runtime.",
    }
    try:
        import maboss  # pylint: disable=import-outside-toplevel

        payload["version"] = metadata.version("maboss")
    except metadata.PackageNotFoundError:
        return payload
    payload["installed"] = "true"
    bin_path = Path(maboss.bin_path) / maboss.bin_name
    payload["binary_path"] = str(bin_path)
    payload["binary_present"] = "true" if bin_path.is_file() else "false"
    try:
        import cmaboss  # noqa: F401  # pylint: disable=import-outside-toplevel,unused-import
    except ModuleNotFoundError:
        payload["cmaboss_available"] = "false"
    else:
        payload["cmaboss_available"] = "true"
    try:
        from maboss.simulation import (
            Simulation as ClassicalSimulation,  # pylint: disable=import-outside-toplevel
        )
    except ModuleNotFoundError:
        payload["classic_continue_from_result_available"] = "false"
    else:
        payload["classic_continue_from_result_available"] = (
            "true" if hasattr(ClassicalSimulation, "continue_from_result") else "false"
        )
    try:
        from maboss.cmabosssimulation import (
            CMaBoSSSimulation,  # pylint: disable=import-outside-toplevel
        )
    except ModuleNotFoundError:
        payload["cmaboss_continue_from_result_available"] = "false"
    else:
        payload["cmaboss_continue_from_result_available"] = (
            "true" if hasattr(CMaBoSSSimulation, "continue_from_result") else "false"
        )
    return payload
