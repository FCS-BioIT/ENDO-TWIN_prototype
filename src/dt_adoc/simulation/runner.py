"""Simulation-runner helpers."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
from dataclasses import dataclass, field, replace
from importlib import metadata
from math import isclose, isfinite
from pathlib import Path
from typing import Any, Self

import maboss
import yaml

from dt_adoc.calibration.adhesion_likelihood import (
    STRUCTURALLY_CONTRADICTED,
    binomial_log_likelihood,
    is_rankable,
    structural_verdict,
)
from dt_adoc.calibration.objectives import (
    AdhesionReadout,
    readout_log_likelihood,
)
from dt_adoc.maboss_adapter import (
    apply_joint_distribution,
    apply_node_marginals_independent,
    project_joint_distribution,
    render_network_with_logic_overrides,
)
from dt_adoc.model.catalog import (
    load_parameter_scenarios,
    load_phenotypes,
    load_tsv,
)
from dt_adoc.model.provenance import describe_file, repo_root
from dt_adoc.model.runtime import (
    resolve_memory_policy,
    resolve_model,
    resolve_rule_variants,
    validate_manifest_model_version,
)
from dt_adoc.perturbations.adjudication import (
    ADJUDICATIONS_PATH,
    TARGET_POLICY_PATH,
    admission_record,
)
from dt_adoc.perturbations.engine import (
    ACTIVITY_VETO,
    DIRECT_BASIS,
    EVIDENCE_REGISTER_PATH,
    LEGACY_BASIS,
    LIBRARY_PATH,
    InterventionError,
    legacy_route_overrides,
    library_for_version,
    load_intervention_library,
    named_effect_records,
)
from dt_adoc.protocols.conditions import get_protocol, protocol_file
from dt_adoc.protocols.runner import protocol_sequence
from dt_adoc.reporting.report import write_markdown_report
from dt_adoc.reporting.tables import write_tsv
from dt_adoc.scoring.candidates import CandidateScore, pareto_front
from dt_adoc.simulation.manifests import (
    SimulationSettings as ManifestSimulationSettings,
)
from dt_adoc.simulation.manifests import build_run_manifest, write_run_manifest
from dt_adoc.simulation.stability import effect_mean, effect_span

JOINT_CONTINUATION_METHOD = "projected_joint_memory"
MARGINAL_CONTINUATION_METHOD = "node_marginals_independent"
CONTINUATION_MODE_CHOICES = {"joint", "marginal"}
MEMORY_NODE_POLICY_CHOICES = {"all_non_inputs", "relay_only", "explicit"}
CONTINUATION_STATE_PREFIXES = ("X_INTERFACE_",)
PROBABILITY_TOLERANCE = 1e-9
#: How library-covered interventions are executed. ``"engine"`` renders their
#: effect through ``perturbations.engine`` and leaves the legacy ``IN_*`` inputs
#: unread (Stage 2 of ``docs/intervention_layer_refactor_plan.md``);
#: ``"legacy"`` runs the model's own ``and not IN_X`` rules. Both give
#: bit-identical results; the legacy route exists so that tests can show it.
INTERVENTION_ROUTING = "engine"


@dataclass(frozen=True)
class SimulationSettings:
    seeds: list[int]
    trajectory_count: int
    max_time: float
    time_tick: float


@dataclass(frozen=True)
class ContinuationState:
    mode: str
    continuation_method: str
    node_ids: tuple[str, ...] = ()
    distribution: dict[tuple[int, ...], float] = field(default_factory=dict)
    forced_nodes: dict[str, bool] = field(default_factory=dict)
    source_protocol: str | None = None
    probability_cutoff: float = 0.0
    source_state_count: int = 0
    retained_state_count: int = 0
    dropped_probability_mass: float = 0.0
    memory_node_policy: str | None = None
    previous_result: Any | None = None


@dataclass(frozen=True)
class ConditionRunResult:
    merged_cfg: Path
    raw_result: Any
    last_nodes_probtraj: Any
    last_states_probtraj: Any
    last: dict[str, float]
    nodes_probtraj: Any = None
    """Full time-indexed node marginal trajectory, or None when unavailable.

    Rows are MaBoSS relative times, columns are tracked node ids, values are
    P(node = ON) across simulated trajectories. Input (``IN_*``) nodes stay
    internal to the merged cfg and are therefore absent here; their values are
    deterministic protocol settings, not simulated quantities.
    """
    executed_network: dict[str, Any] = field(default_factory=dict)
    """What MaBoSS actually loaded. Rendered networks are temporary and are
    deleted after the run, so this record is what reconstructs them: the source
    network, the logic overrides applied to it (``intervention_overrides`` names
    the nodes the engine rewrote, the rest are rule variants), the intervention
    routing, the
    intervention library consulted (path and sha256, or None), and the sha256 of
    the exact network text executed. ``named_intervention_effects`` lists each
    named intervention's library rows with their mapping basis and evidence, and
    ``evidence_register`` pins the register a direct row's evidence resolved in.
    ``legacy_input_values`` is the value each routed legacy marker started at, so
    a marker-timed run and a name-timed one stay distinguishable even when their
    networks are identical. A step run by ``run_protocol`` also carries
    ``intervention_timing``: the protocol, the step, and which of the active
    names the step declared and which the caller supplied.
    """

    def release(self) -> None:
        """Remove this run's merged-cfg directory. Idempotent.

        The directory belongs to whoever holds the result, which is why the
        runner does not remove it on success: ``merged_cfg`` stays readable
        until the holder says otherwise. Read it first if it is needed.
        """
        shutil.rmtree(self.merged_cfg.parent, ignore_errors=True)


@dataclass(frozen=True)
class ProtocolRunResult:
    protocol_id: str
    step_results: tuple[ConditionRunResult, ...]
    step_initializations: tuple[ContinuationState | None, ...]
    continuation_from: str | None
    continuation_applied: bool

    @property
    def final_result(self) -> ConditionRunResult:
        return self.step_results[-1]

    def release(self) -> None:
        """Remove every step's merged-cfg directory (``ConditionRunResult.release``)."""
        for step_result in self.step_results:
            step_result.release()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


def ensure_positive_settings(settings: SimulationSettings) -> None:
    if not settings.seeds or any(seed < 0 for seed in settings.seeds):
        raise ValueError("seeds must be a non-empty list of non-negative integers")
    if (
        settings.trajectory_count <= 0
        or settings.max_time <= 0
        or settings.time_tick <= 0
    ):
        raise ValueError("trajectory_count, max_time, and time_tick must be positive")


def _parse_cfg_lines(text: str) -> tuple[list[str], dict[str, str]]:
    passthrough: list[str] = []
    assignments: dict[str, str] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("//") or "=" not in raw_line:
            passthrough.append(raw_line)
            continue
        key = raw_line.split("=", 1)[0].strip()
        assignments[key] = raw_line
    return passthrough, assignments


def merge_cfg_texts(base_text: str, override_texts: list[str]) -> str:
    passthrough, assignments = _parse_cfg_lines(base_text)
    order = []
    for raw_line in base_text.splitlines():
        if "=" in raw_line:
            order.append(raw_line.split("=", 1)[0].strip())
    for override in override_texts:
        for raw_line in override.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("//") or "=" not in raw_line:
                continue
            key = raw_line.split("=", 1)[0].strip()
            assignments[key] = raw_line
            if key not in order:
                order.append(key)
    rendered: list[str] = [line for line in passthrough if line.strip()]
    if rendered:
        rendered.append("")
    rendered.extend(assignments[key] for key in order)
    return "\n".join(rendered).rstrip() + "\n"


def _input_override_text(input_states: dict[str, bool]) -> str:
    return (
        "\n".join(
            f"{node_id}.istate = {'TRUE' if state else 'FALSE'};"
            for node_id, state in input_states.items()
        )
        + "\n"
    )


def _default_time_tick(root: Path | None = None) -> float:
    scenario = load_parameter_scenarios(root)["scenarios"][0]
    return float(scenario["simulation_defaults"]["time_tick"])


def _default_simulation_settings(root: Path | None = None) -> dict[str, float | int]:
    scenario = load_parameter_scenarios(root)["scenarios"][0]
    defaults = scenario["simulation_defaults"]
    return {
        "sample_count": int(defaults["sample_count"]),
        "max_time": float(defaults["max_time"]),
        "time_tick": float(defaults["time_tick"]),
        "thread_count": int(defaults["thread_count"]),
    }


def _timing_override_text(*, relative_duration: float, root: Path | None = None) -> str:
    return (
        "\n".join(
            [
                f"max_time = {float(relative_duration)};",
                f"time_tick = {_default_time_tick(root)};",
            ]
        )
        + "\n"
    )


def _state_tracking_override_text(root: Path | None = None) -> str:
    return _state_tracking_override_text_for_model(
        model_version="adoc-core-v0.1.0",
        root=root,
    )


def _state_tracking_override_text_for_model(
    *,
    model_version: str,
    root: Path | None = None,
) -> str:
    model_spec = resolve_model(model_version, root)
    lines = []
    for row in load_tsv(model_spec.node_dictionary):
        node_id = row["node_id"]
        if node_id.startswith("IN_"):
            continue
        lines.append(f"{node_id}.is_internal = FALSE;")
    return "\n".join(lines) + "\n"


def _load_calibration_payload(root: Path | None = None) -> dict[str, Any]:
    active_root = root or repo_root()
    return yaml.safe_load((active_root / "config" / "calibration.yaml").read_text())


def _adhesion_objective_rows(
    *,
    condition_results: dict[str, dict[str, float]],
    root: Path | None = None,
) -> tuple[list[dict[str, object]], float, float, float, list[str]]:
    payload = _load_calibration_payload(root)
    readouts = payload["adhesion_objective"]["readouts"]
    rows: list[dict[str, object]] = []
    objective_readouts: list[AdhesionReadout] = []
    held_out_readouts: list[AdhesionReadout] = []
    included_units: list[str] = []
    for readout in readouts:
        protocol_id = str(readout["protocol_id"])
        successes = int(readout["successes"])
        trials = int(readout["trials"])
        role = str(readout["role"])
        model_probability = condition_results[protocol_id]["OUT_STABLE_ADHESION"]
        rows.append(
            {
                "protocol_id": protocol_id,
                "role": role,
                "successes": successes,
                "trials": trials,
                "model_probability": model_probability,
                "used_for_fitting": role == "calibration",
                "log_likelihood": binomial_log_likelihood(
                    probability=model_probability,
                    successes=successes,
                    trials=trials,
                ),
                # From the UNCLIPPED probability, so an exact 0 or 1 is visible
                # rather than absorbed into log(CLIP_EPSILON).
                "structural_verdict": structural_verdict(
                    probability=model_probability,
                    successes=successes,
                    trials=trials,
                ),
                "rankable": is_rankable(
                    probability=model_probability,
                    successes=successes,
                    trials=trials,
                ),
            }
        )
        if role == "calibration":
            objective_readouts.append(
                AdhesionReadout(
                    probability=model_probability,
                    successes=successes,
                    trials=trials,
                    role=role,
                )
            )
            included_units.append(f"{protocol_id}:{successes}/{trials}:{role}")
        else:
            held_out_readouts.append(
                AdhesionReadout(
                    probability=model_probability,
                    successes=successes,
                    trials=trials,
                    role=role,
                )
            )
    calibration_log_likelihood = sum(
        readout_log_likelihood(readout) for readout in objective_readouts
    )
    held_out_validation_log_likelihood = sum(
        readout_log_likelihood(readout) for readout in held_out_readouts
    )
    total_descriptive_log_likelihood = calibration_log_likelihood + (
        held_out_validation_log_likelihood
    )
    # Reported, never ranked on. Since the 2026-09-16 demotion adhesion is an
    # ordinal/diagnostic readout: the sums above are descriptive, and any arm
    # flagged structurally_contradicted scores log(CLIP_EPSILON) identically for
    # every candidate. See docs/gate3_scope_adjudication.md.
    contradicted = [
        row["protocol_id"]
        for row in rows
        if row["structural_verdict"] == STRUCTURALLY_CONTRADICTED
    ]
    return (
        rows,
        calibration_log_likelihood,
        held_out_validation_log_likelihood,
        total_descriptive_log_likelihood,
        included_units,
        contradicted,
    )


def _maboss_python_package_version() -> str:
    try:
        return metadata.version("maboss")
    except metadata.PackageNotFoundError:
        return "unknown"


def build_condition_cfg(
    *,
    model_version: str = "adoc-core-v0.1.0",
    condition_cfg: Path,
    root: Path | None = None,
    override_texts: list[str] | None = None,
    seed: int | None = None,
    sample_count: int | None = None,
) -> Path:
    active_root = root or repo_root()
    model_spec = resolve_model(model_version, active_root)
    baseline_cfg = model_spec.baseline_cfg
    merged = merge_cfg_texts(
        baseline_cfg.read_text(encoding="utf-8"),
        [
            condition_cfg.read_text(encoding="utf-8"),
            _state_tracking_override_text_for_model(
                model_version=model_version,
                root=active_root,
            ),
            *(override_texts or []),
        ],
    )
    extra_lines: list[str] = []
    if seed is not None:
        extra_lines.append(f"seed_pseudorandom = {seed};")
    if sample_count is not None:
        extra_lines.append(f"sample_count = {sample_count};")
    if extra_lines:
        merged = merged.rstrip() + "\n" + "\n".join(extra_lines) + "\n"
    tempdir = Path(tempfile.mkdtemp(prefix="dt_adoc_cfg_"))
    merged_cfg = tempdir / condition_cfg.name
    merged_cfg.write_text(merged, encoding="utf-8")
    return merged_cfg


def _set_istate(network: Any, nodes: Any, probability: Any) -> None:
    try:
        network.set_istate(nodes, probability, warnings=False)
    except TypeError:
        network.set_istate(nodes, probability)


def _validate_binary_distribution(
    probability: list[float] | tuple[float, float],
) -> None:
    if len(probability) != 2:
        raise ValueError("single-node initial states require exactly two probabilities")
    if any((not isfinite(value)) or value < 0.0 for value in probability):
        raise ValueError("single-node initial states must be finite and non-negative")
    if not isclose(sum(probability), 1.0, rel_tol=0.0, abs_tol=PROBABILITY_TOLERANCE):
        raise ValueError("single-node initial states must sum to one")


def _validate_joint_distribution(
    distribution: dict[tuple[int, ...], float],
    *,
    node_count: int,
) -> None:
    if not distribution:
        raise ValueError("joint continuation distribution is empty")
    total = 0.0
    for state, probability in distribution.items():
        if len(state) != node_count:
            raise ValueError(
                "joint continuation state length does not match node count"
            )
        if any(bit not in {0, 1} for bit in state):
            raise ValueError("joint continuation states must be binary tuples")
        if (not isfinite(probability)) or probability < 0.0:
            raise ValueError(
                "joint continuation probabilities must be finite and non-negative"
            )
        total += probability
    if not isclose(total, 1.0, rel_tol=0.0, abs_tol=PROBABILITY_TOLERANCE):
        raise ValueError("joint continuation probabilities must sum to one")


def _normalize_joint_distribution(
    distribution: dict[tuple[int, ...], float],
) -> dict[tuple[int, ...], float]:
    total = sum(distribution.values())
    if (not isfinite(total)) or total <= 0.0:
        raise ValueError("joint continuation distribution must have positive mass")
    normalized = {
        state: probability / total for state, probability in distribution.items()
    }
    _validate_joint_distribution(normalized, node_count=len(next(iter(normalized))))
    return normalized


def _memory_node_ids(
    *,
    model_version: str,
    root: Path | None = None,
    excluded_nodes: set[str] | None = None,
    memory_node_policy: str = "all_non_inputs",
    explicit_memory_nodes: tuple[str, ...] = (),
) -> tuple[str, ...]:
    active_root = root or repo_root()
    excluded = excluded_nodes or set()
    model_spec = resolve_model(model_version, active_root)
    if memory_node_policy == "explicit":
        node_ids = tuple(
            node_id for node_id in explicit_memory_nodes if node_id not in excluded
        )
        if not node_ids:
            raise ValueError(
                "explicit joint continuation memory_nodes resolved to empty"
            )
        return node_ids
    if memory_node_policy in model_spec.memory_policies:
        policy = resolve_memory_policy(
            model_version=model_version,
            policy_id=memory_node_policy,
            root=active_root,
        )
        return tuple(node_id for node_id in policy.node_ids if node_id not in excluded)
    return tuple(
        sorted(
            row["node_id"]
            for row in load_tsv(model_spec.node_dictionary)
            if row["node_id"] not in excluded
            and (
                memory_node_policy == "all_non_inputs"
                or row["node_id"].startswith(CONTINUATION_STATE_PREFIXES)
            )
        )
    )


def joint_continuation_from_last_states(
    *,
    last_states_probtraj: Any,
    model_version: str,
    root: Path | None = None,
    excluded_nodes: set[str] | None = None,
    forced_nodes: dict[str, bool] | None = None,
    source_protocol: str | None = None,
    probability_cutoff: float = 0.0,
    memory_node_policy: str = "all_non_inputs",
    explicit_memory_nodes: tuple[str, ...] = (),
) -> ContinuationState:
    node_ids = _memory_node_ids(
        model_version=model_version,
        root=root,
        excluded_nodes=excluded_nodes,
        memory_node_policy=memory_node_policy,
        explicit_memory_nodes=explicit_memory_nodes,
    )
    projected = project_joint_distribution(
        last_states_probtraj=last_states_probtraj,
        memory_nodes=node_ids,
        probability_cutoff=probability_cutoff,
    )
    return ContinuationState(
        mode="joint",
        continuation_method=JOINT_CONTINUATION_METHOD,
        node_ids=node_ids,
        distribution=projected["distribution"],
        forced_nodes=dict(forced_nodes or {}),
        source_protocol=source_protocol,
        probability_cutoff=probability_cutoff,
        source_state_count=int(projected["source_state_count"]),
        retained_state_count=int(projected["retained_state_count"]),
        dropped_probability_mass=float(projected["dropped_probability_mass"]),
        memory_node_policy=memory_node_policy,
    )


def continuation_from_last_states(
    *,
    last_states_probtraj: Any,
    model_version: str,
    root: Path | None = None,
    excluded_nodes: set[str] | None = None,
    forced_nodes: dict[str, bool] | None = None,
    source_protocol: str | None = None,
    carry_mode: str = "all_non_inputs",
) -> ContinuationState:
    return joint_continuation_from_last_states(
        last_states_probtraj=last_states_probtraj,
        model_version=model_version,
        root=root,
        excluded_nodes=excluded_nodes,
        forced_nodes=forced_nodes,
        source_protocol=source_protocol,
        probability_cutoff=0.0,
        memory_node_policy=carry_mode,
    )


def marginal_continuation_from_result(
    *,
    previous_result: Any,
    forced_nodes: dict[str, bool] | None = None,
    source_protocol: str | None = None,
) -> ContinuationState:
    if previous_result is None:
        raise ValueError("marginal continuation requires a previous runtime result")
    return ContinuationState(
        mode="marginal",
        continuation_method=MARGINAL_CONTINUATION_METHOD,
        node_ids=tuple(
            node_id
            for node_id in previous_result.get_last_nodes_probtraj().columns
            if node_id != "<nil>"
        ),
        forced_nodes=dict(forced_nodes or {}),
        source_protocol=source_protocol,
        previous_result=previous_result,
    )


def build_continuation(
    *,
    previous_condition: ConditionRunResult,
    target_protocol_id: str,
    model_version: str = "adoc-core-v0.1.0",
    forced_nodes: dict[str, bool],
    source_protocol: str | None,
    root: Path | None = None,
    mode: str | None = None,
) -> ContinuationState:
    target_protocol = get_protocol(
        target_protocol_id, root, model_version=model_version
    )
    continuation = target_protocol.continuation
    selected_mode = mode or (continuation.mode if continuation is not None else "joint")
    if selected_mode not in CONTINUATION_MODE_CHOICES:
        raise ValueError(f"unsupported continuation mode: {selected_mode}")
    if selected_mode == "marginal":
        return marginal_continuation_from_result(
            previous_result=previous_condition.raw_result,
            forced_nodes=forced_nodes,
            source_protocol=source_protocol,
        )
    if continuation is None:
        memory_node_policy = "all_non_inputs"
        probability_cutoff = 0.0
        explicit_memory_nodes: tuple[str, ...] = ()
    else:
        memory_node_policy = continuation.memory_policy
        model_spec = resolve_model(model_version, root)
        if (
            memory_node_policy not in MEMORY_NODE_POLICY_CHOICES
            and memory_node_policy not in model_spec.memory_policies
        ):
            raise ValueError(f"unsupported memory-node policy: {memory_node_policy}")
        probability_cutoff = continuation.probability_cutoff
        explicit_memory_nodes = continuation.memory_nodes
    return joint_continuation_from_last_states(
        last_states_probtraj=previous_condition.last_states_probtraj,
        model_version=model_version,
        root=root,
        excluded_nodes=set(forced_nodes),
        forced_nodes=forced_nodes,
        source_protocol=source_protocol,
        probability_cutoff=probability_cutoff,
        memory_node_policy=memory_node_policy,
        explicit_memory_nodes=explicit_memory_nodes,
    )


def protocol_continuation(
    protocol_id: str,
    run: ProtocolRunResult,
    *,
    model_version: str = "adoc-core-v0.1.0",
    root: Path | None = None,
    mode: str | None = None,
) -> ContinuationState:
    protocol = get_protocol(protocol_id, root, model_version=model_version)
    first_step = protocol.steps[0]
    return build_continuation(
        previous_condition=run.final_result,
        target_protocol_id=protocol_id,
        model_version=model_version,
        forced_nodes=first_step.input_states,
        source_protocol=run.protocol_id,
        root=root,
        mode=mode,
    )


def _cfg_input_value(assignments: dict[str, str], node_id: str) -> bool:
    line = assignments.get(f"{node_id}.istate")
    if line is None:
        raise InterventionError(f"the merged cfg sets no istate for {node_id}")
    value = line.split("=", 1)[1].strip().rstrip(";").strip()
    if value in {"TRUE", "1"}:
        return True
    if value in {"FALSE", "0"}:
        return False
    raise InterventionError(f"{node_id}.istate is {value!r}, not a fixed value")


def _deterministic(probability: float, node_id: str, source: str) -> bool:
    for value in (0.0, 1.0):
        if isclose(probability, value, abs_tol=PROBABILITY_TOLERANCE):
            return bool(value)
    raise InterventionError(
        f"{node_id} starts at P(ON) = {probability} from {source}; an intervention "
        "input must be fixed"
    )


def _legacy_input_value(
    node_id: str,
    assignments: dict[str, str],
    continuation: ContinuationState | None,
) -> bool:
    """The value MaBoSS starts ``node_id`` at, in ``run_cmaboss_condition``'s order.

    The merged cfg sets it first. A marginal continuation then overwrites every
    node the previous result tracked, and a joint one overwrites its memory nodes.
    ``forced_nodes`` are applied last.
    """
    if continuation is not None:
        if node_id in continuation.forced_nodes:
            return bool(continuation.forced_nodes[node_id])
        if continuation.mode == "marginal":
            marginals = continuation.previous_result.get_nodes_probtraj().iloc[-1]
            if node_id in marginals.index:
                return _deterministic(
                    float(marginals[node_id]), node_id, "the marginal continuation"
                )
        elif node_id in continuation.node_ids:
            index = continuation.node_ids.index(node_id)
            probability = sum(
                p for state, p in continuation.distribution.items() if state[index] == 1
            )
            return _deterministic(float(probability), node_id, "the joint continuation")
    return _cfg_input_value(assignments, node_id)


def _intervention_overrides(
    *,
    model_version: str,
    network_text: str,
    merged_cfg: Path,
    continuation: ContinuationState | None,
    root: Path,
    interventions: tuple[str, ...] = (),
) -> tuple[dict[str, str], dict[str, Any] | None, dict[str, bool]]:
    """The engine's overrides, the library file they came from, and the input values.

    No overrides, and no library, when routing is legacy; no overrides when the
    library does not cover the model version. Each legacy input takes the value
    MaBoSS will start it at (``_legacy_input_value``).
    """
    if INTERVENTION_ROUTING == "legacy":
        if interventions:
            # Silently dropping them would run an unperturbed model under a
            # perturbed name, which is the one outcome worth refusing outright.
            raise InterventionError(
                "named interventions need the engine route, not legacy routing"
            )
        return {}, None, {}
    if INTERVENTION_ROUTING != "engine":
        raise ValueError(f"unknown INTERVENTION_ROUTING {INTERVENTION_ROUTING!r}")
    if not (root / LIBRARY_PATH).is_file():
        # A root without the library (a synthetic test root, say) has no
        # interventions to route; its models run as their own rules say.
        if interventions:
            raise InterventionError(f"no intervention library at {LIBRARY_PATH}")
        return {}, None, {}
    library = load_intervention_library(root)
    library_ref = describe_file(root / LIBRARY_PATH, root=root).__dict__
    view = library_for_version(library, model_version)
    legacy_inputs = sorted(
        {
            effects[0].legacy_input_node
            for effects in view.values()
            if effects[0].mode == ACTIVITY_VETO
            and effects[0].mapping_basis == LEGACY_BASIS
        }
    )
    if not legacy_inputs:
        if not interventions:
            return {}, library_ref, {}
        if not view:
            raise InterventionError(
                f"the library covers no intervention for {model_version}"
            )
    _, assignments = _parse_cfg_lines(merged_cfg.read_text(encoding="utf-8"))
    for key in assignments:
        # A joint istate such as ``[A, IN_X].istate`` is a second, separate key
        # for the same input; which one MaBoSS honours is not something to guess.
        if key.startswith("[") and any(
            re.search(rf"\b{re.escape(node_id)}\b", key) for node_id in legacy_inputs
        ):
            raise InterventionError(
                f"the merged cfg sets a legacy input jointly: {key}"
            )
    values = {
        node_id: _legacy_input_value(node_id, assignments, continuation)
        for node_id in legacy_inputs
    }
    overrides = legacy_route_overrides(
        network_text,
        values,
        model_version=model_version,
        library=library,
        also_active=interventions,
    )
    return overrides, library_ref, values


def run_cmaboss_condition(
    *,
    model_version: str,
    condition_cfg: Path,
    root: Path | None = None,
    override_texts: list[str] | None = None,
    continuation: ContinuationState | None = None,
    rule_variant_selection: dict[str, str] | None = None,
    interventions: tuple[str, ...] = (),
    seed: int = 1,
    sample_count: int = 2000,
) -> ConditionRunResult:
    """Run one condition.

    ``interventions`` names library interventions to apply on top of whatever the
    protocol itself declares, which is how a combination or a multi-target
    compound is executed without adding a node. It is a conditional
    model-internal prediction, never evidence that the compounds interact.
    """
    if isinstance(interventions, str):
        raise InterventionError("interventions is a sequence of ids, not one id")
    # Materialised once: consuming it twice recorded a perturbed run as
    # unperturbed, which is the one outcome this path refuses outright.
    interventions = tuple(interventions)
    active_root = root or repo_root()
    model_spec = resolve_model(model_version, active_root)
    merged_cfg = build_condition_cfg(
        model_version=model_version,
        condition_cfg=condition_cfg,
        root=active_root,
        override_texts=override_texts,
        seed=seed,
        sample_count=sample_count,
    )
    try:
        _, logic_overrides = resolve_rule_variants(
            model_version=model_version,
            variant_selection=rule_variant_selection,
            root=active_root,
        )
        model_network_text = model_spec.network_bnd.read_text(encoding="utf-8")
        intervention_overrides, library_ref, legacy_values = _intervention_overrides(
            model_version=model_version,
            network_text=model_network_text,
            merged_cfg=merged_cfg,
            continuation=continuation,
            root=active_root,
            interventions=interventions,
        )
        named_effects: list[dict[str, object]] = []
        evidence_register = None
        direct_adjudications = None
        direct_target_policy = None
        direct_admission = None
        if interventions:
            # Reached only once the engine route accepted them, so the library
            # exists and every name resolves in it.
            library = load_intervention_library(active_root)
            named_effects = named_effect_records(
                interventions,
                library,
                model_version=model_version,
            )
            if any(e["mapping_basis"] == DIRECT_BASIS for e in named_effects):
                evidence_register = describe_file(
                    active_root / EVIDENCE_REGISTER_PATH, root=active_root
                ).__dict__
                # Why a direct effect was licensed: the approvals and the target
                # policy, alongside the evidence they rest on (O8b).
                direct_adjudications = describe_file(
                    active_root / ADJUDICATIONS_PATH, root=active_root
                ).__dict__
                direct_target_policy = describe_file(
                    active_root / TARGET_POLICY_PATH, root=active_root
                ).__dict__
                # What the admission established and what the result may be
                # reported as: declarations, expressivity classes, and the
                # phenotype_claim_blocked / compound_claim_blocked flags
                # (docs/stage4b_direct_admission.md §6.5).
                direct_admission = admission_record(
                    interventions, library, model_version, active_root
                )
        clash = sorted(set(logic_overrides) & set(intervention_overrides))
        if clash:
            raise InterventionError(
                f"a rule variant and an intervention both rewrite {', '.join(clash)}"
            )
        logic_overrides = {**logic_overrides, **intervention_overrides}
        network_text = model_network_text
        rendered_path: Path | None = None
        if logic_overrides:
            network_text = render_network_with_logic_overrides(
                model_network_text,
                logic_overrides=logic_overrides,
            )
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".bnd",
                delete=False,
            ) as handle:
                handle.write(network_text)
                rendered_path = Path(handle.name)
        network_path = rendered_path or model_spec.network_bnd
        executed_network = {
            "source_network": describe_file(
                model_spec.network_bnd, root=active_root
            ).__dict__,
            "rendered": rendered_path is not None,
            "network_sha256": hashlib.sha256(network_text.encode("utf-8")).hexdigest(),
            "logic_overrides": dict(sorted(logic_overrides.items())),
            "intervention_overrides": sorted(intervention_overrides),
            "named_interventions": list(interventions),
            "named_intervention_effects": named_effects,
            "legacy_input_values": dict(sorted(legacy_values.items())),
            "evidence_register": evidence_register,
            "direct_effect_adjudications": direct_adjudications,
            "direct_effect_target_policy": direct_target_policy,
            "direct_admission": direct_admission,
            "intervention_routing": INTERVENTION_ROUTING,
            "intervention_library": library_ref,
        }
        try:
            simulation = maboss.load(str(network_path), str(merged_cfg), cmaboss=True)
            if continuation is not None:
                if continuation.mode == "marginal":
                    apply_node_marginals_independent(
                        network=simulation.network,
                        result=continuation.previous_result,
                        forced_nodes=continuation.forced_nodes,
                    )
                elif continuation.node_ids:
                    _validate_joint_distribution(
                        continuation.distribution,
                        node_count=len(continuation.node_ids),
                    )
                    apply_joint_distribution(
                        network=simulation.network,
                        memory_nodes=continuation.node_ids,
                        distribution=continuation.distribution,
                        forced_nodes=continuation.forced_nodes,
                    )
            result = simulation.run()
        finally:
            # The rendered file is reconstructable from ``executed_network``, so it is
            # not kept: a screen runs many phases and would otherwise leave one per run.
            if rendered_path is not None:
                rendered_path.unlink(missing_ok=True)
        last_nodes_probtraj = result.get_last_nodes_probtraj().copy()
        last_states_probtraj = result.get_last_states_probtraj().copy()
        # Read the full node trajectory off the already-completed result. This is an
        # accessor on the same run, never a second simulation. The cmaboss backend
        # returns None when the simulation was executed with only_final_state=True,
        # and it accepts no ``nodes=`` argument, so any column subsetting happens
        # after the call.
        nodes_probtraj = result.get_nodes_probtraj()
        if nodes_probtraj is not None:
            nodes_probtraj = nodes_probtraj.copy()
        last = {
            key: float(value)
            for key, value in last_nodes_probtraj.iloc[-1].to_dict().items()
        }
        return ConditionRunResult(
            merged_cfg=merged_cfg,
            raw_result=result,
            last_nodes_probtraj=last_nodes_probtraj,
            last_states_probtraj=last_states_probtraj,
            last=last,
            nodes_probtraj=nodes_probtraj,
            executed_network=executed_network,
        )
    except BaseException:
        # The merged cfg is a temporary directory that a successful run
        # hands back in its result, so it is kept on the way out and removed
        # only when there is no result to hand back. A refused intervention
        # is an ordinary outcome for a screen, and would otherwise leave one
        # directory behind per rejected combination.
        shutil.rmtree(merged_cfg.parent, ignore_errors=True)
        raise


def nodes_probtraj_table(
    nodes_probtraj: Any,
    *,
    protocol_id: str,
    step_id: str,
    phase_index: int,
) -> Any:
    """Shape a raw node trajectory into a tidy, self-describing table.

    Columns are ``time`` (MaBoSS relative time, never hours), ``protocol_id``,
    ``step_id``, ``phase_index``, then one column per tracked node holding
    P(node = ON) across simulated trajectories.
    """
    if nodes_probtraj is None:
        raise ValueError(
            f"No node trajectory available for {protocol_id}__{step_id}; "
            "the simulation was run without trajectory output."
        )
    table = nodes_probtraj.copy()
    table.insert(0, "phase_index", int(phase_index))
    table.insert(0, "step_id", step_id)
    table.insert(0, "protocol_id", protocol_id)
    table.insert(0, "time", [float(value) for value in nodes_probtraj.index])
    table.reset_index(drop=True, inplace=True)
    return table


def run_protocol(
    protocol_id: str,
    *,
    model_version: str = "adoc-core-v0.1.0",
    root: Path | None = None,
    continuation: ContinuationState | None = None,
    continuation_mode: str | None = None,
    rule_variant_selection: dict[str, str] | None = None,
    interventions: tuple[str, ...] = (),
    seed: int = 1,
    sample_count: int = 2000,
    phase_horizon: float | None = None,
) -> ProtocolRunResult:
    """Execute a protocol's steps, optionally overriding every step's horizon.

    ``phase_horizon`` replaces each step's declared ``relative_duration`` for the
    simulation only. It exists because the declared durations read the adhesion
    endpoints roughly 4000x before their logical fixed point (see
    ``docs/endpoint_convergence_finding.md``), so a converged readout needs a
    longer horizon than the committed policy declares. The declared value is NOT
    mutated -- callers that need it for labelling read it from the protocol.
    Every horizon is a dimensionless MaBoSS relative-time parameter.

    Each step runs the interventions its own ``interventions`` field declares,
    so the protocol says when an intervention is active
    (``docs/protocol_intervention_timing.md``). ``interventions`` names library
    interventions active for every step of this call *in addition*: a step's
    active set is the union of the two, the step's declared names first. A name
    in both is refused before any step runs, as is a name the caller repeats. A
    step that would apply an intervention twice through its legacy marker is
    refused by that step, so on a multi-step protocol that refusal can arrive
    after earlier steps have been simulated.

    The merged-cfg directory of every step belongs to the caller once this
    returns; ``ProtocolRunResult.release`` (or ``with``) removes them.
    """
    if isinstance(interventions, str):
        raise InterventionError("interventions is a sequence of ids, not one id")
    interventions = tuple(interventions)
    if len(set(interventions)) != len(interventions):
        raise InterventionError(
            f"an intervention is named twice: {sorted(interventions)}"
        )
    active_root = root or repo_root()
    protocol = get_protocol(protocol_id, active_root, model_version=model_version)
    for step in protocol.steps:
        both = sorted(set(step.interventions) & set(interventions))
        if both:
            raise InterventionError(
                f"protocol {protocol_id} step {step.step_id} already declares "
                f"{', '.join(both)}; naming it again would apply it twice"
            )
    condition_cfg = active_root / protocol.condition_cfg
    current_continuation = continuation
    step_results: list[ConditionRunResult] = []
    step_initializations: list[ContinuationState | None] = []
    try:
        for step_index, step in enumerate(protocol.steps):
            step_initializations.append(current_continuation)
            condition_run = run_cmaboss_condition(
                model_version=model_version,
                condition_cfg=condition_cfg,
                root=active_root,
                override_texts=[
                    _input_override_text(step.input_states),
                    _timing_override_text(
                        relative_duration=(
                            step.relative_duration
                            if phase_horizon is None
                            else float(phase_horizon)
                        ),
                        root=active_root,
                    ),
                ],
                continuation=current_continuation,
                rule_variant_selection=rule_variant_selection,
                interventions=step.interventions + interventions,
                seed=seed,
                sample_count=sample_count,
            )
            condition_run = replace(
                condition_run,
                executed_network={
                    **condition_run.executed_network,
                    "intervention_timing": {
                        "protocol_id": protocol_id,
                        "step_id": step.step_id,
                        "step_index": step_index,
                        "protocol_declared": list(step.interventions),
                        "caller_supplied": list(interventions),
                    },
                },
            )
            step_results.append(condition_run)
            if step_index + 1 < len(protocol.steps):
                next_step = protocol.steps[step_index + 1]
                current_continuation = build_continuation(
                    previous_condition=condition_run,
                    target_protocol_id=protocol_id,
                    model_version=model_version,
                    forced_nodes=next_step.input_states,
                    source_protocol=protocol_id,
                    root=active_root,
                    mode=continuation_mode,
                )
    except BaseException:
        # A step's merged cfg is handed back in the result, so only the caller
        # can remove it. When a later step fails there is no result to hand
        # back, and the earlier steps' directories would be orphaned, one set
        # per refused protocol run in a screen.
        for step_result in step_results:
            shutil.rmtree(step_result.merged_cfg.parent, ignore_errors=True)
        raise
    return ProtocolRunResult(
        protocol_id=protocol_id,
        step_results=tuple(step_results),
        step_initializations=tuple(step_initializations),
        continuation_from=protocol.continuation_from,
        continuation_applied=continuation is not None,
    )


def _candidate_score(
    *, candidate_id: str, baseline: dict[str, float], perturbed: dict[str, float]
) -> CandidateScore:
    reward = baseline["OUT_STABLE_ADHESION"] - perturbed["OUT_STABLE_ADHESION"]
    return CandidateScore(
        candidate_id=candidate_id,
        reward=reward,
        penalty=0.0,
        instability=0.0,
    )


def run_structural_smoke(
    *,
    run_id: str = "phase1-structural-smoke",
    model_version: str = "adoc-core-v0.1.0",
    rule_variant_selection: dict[str, str] | None = None,
    root: Path | None = None,
) -> Path:
    active_root = root or repo_root()
    model_spec = resolve_model(model_version, active_root)
    selected_rule_variants, _ = resolve_rule_variants(
        model_version=model_version,
        variant_selection=rule_variant_selection,
        root=active_root,
    )
    output_root = model_spec.output_root / run_id
    raw_dir = output_root / "raw"
    tables_dir = output_root / "tables"
    figures_dir = output_root / "figures"
    logs_dir = output_root / "logs"
    validation_dir = output_root / "validation"
    report_dir = output_root / "report"
    for directory in (
        raw_dir,
        tables_dir,
        figures_dir,
        logs_dir,
        validation_dir,
        report_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    phenotype_payload = load_phenotypes(active_root)
    phenotype_contract_rows = load_tsv(model_spec.phenotype_contract)
    executable_phenotype_ids = [
        row["phenotype_id"]
        for row in phenotype_contract_rows
        if str(row.get("executable", "")).lower() == "true"
    ]
    primary_outputs = [
        row["phenotype_id"]
        for row in phenotype_contract_rows
        if str(row.get("executable", "")).lower() == "true"
        and row.get("category") == "primary"
    ]
    safety_outputs = [
        row["phenotype_id"]
        for row in phenotype_contract_rows
        if str(row.get("executable", "")).lower() == "true"
        and row.get("category") == "safety"
    ]
    protocols = list(model_spec.default_smoke_protocols)

    protocol_rows: list[dict[str, object]] = []
    trajectory_row_counts: list[int] = []
    initialization_rows: list[dict[str, object]] = []
    manifest_continuation_rows: list[dict[str, object]] = []
    executed_network_rows: list[dict[str, object]] = []
    phenotype_rows: list[dict[str, object]] = []
    output_refs: list[dict[str, object]] = []
    protocol_results: dict[str, ProtocolRunResult] = {}
    condition_results: dict[str, dict[str, float]] = {}

    for protocol_id in protocols:
        protocol_rows.extend(
            protocol_sequence(protocol_id, active_root, model_version=model_version)
        )
        protocol = get_protocol(protocol_id, active_root, model_version=model_version)
        continuation = None
        if protocol.continuation_from is not None:
            continuation = protocol_continuation(
                protocol_id,
                protocol_results[protocol.continuation_from],
                model_version=model_version,
                root=active_root,
            )
        run = run_protocol(
            protocol_id,
            model_version=model_version,
            root=active_root,
            continuation=continuation,
            rule_variant_selection=selected_rule_variants,
        )
        protocol_results[protocol_id] = run
        condition_results[protocol_id] = run.final_result.last
        for index, step in enumerate(protocol.steps):
            step_result = run.step_results[index]
            step_initialization = run.step_initializations[index]
            executed_network_rows.append(
                {
                    "protocol_id": protocol_id,
                    "step_id": step.step_id,
                    **step_result.executed_network,
                }
            )
            stem = f"{protocol_id}__{step.step_id}"
            raw_nodes_path = raw_dir / f"{stem}_last_nodes_probtraj.tsv"
            raw_states_path = raw_dir / f"{stem}_last_states_probtraj.tsv"
            raw_traj_path = raw_dir / f"{stem}_nodes_probtraj.tsv"
            merged_cfg_path = raw_dir / f"{stem}_merged.cfg"
            step_result.last_nodes_probtraj.to_csv(raw_nodes_path, sep="\t")
            step_result.last_states_probtraj.to_csv(raw_states_path, sep="\t")
            nodes_probtraj_table(
                step_result.nodes_probtraj,
                protocol_id=protocol_id,
                step_id=step.step_id,
                phase_index=index,
            ).to_csv(raw_traj_path, sep="\t", index=False)
            trajectory_row_counts.append(len(step_result.nodes_probtraj))
            merged_cfg_path.write_text(
                step_result.merged_cfg.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            output_refs.append(
                {
                    **describe_file(raw_nodes_path, root=active_root).__dict__,
                    "kind": "raw_last_nodes_probtraj",
                }
            )
            output_refs.append(
                {
                    **describe_file(raw_traj_path, root=active_root).__dict__,
                    "kind": "raw_nodes_probtraj",
                }
            )
            output_refs.append(
                {
                    **describe_file(raw_states_path, root=active_root).__dict__,
                    "kind": "raw_last_states_probtraj",
                }
            )
            output_refs.append(
                {
                    **describe_file(merged_cfg_path, root=active_root).__dict__,
                    "kind": "merged_condition_cfg",
                }
            )
            initialization_rows.append(
                {
                    "protocol_id": protocol_id,
                    "step_id": step.step_id,
                    "continuation_from": protocol.continuation_from or "",
                    "continuation_applied": "true"
                    if step_initialization is not None
                    else "false",
                    "continuation_mode": step_initialization.mode
                    if step_initialization is not None
                    else "",
                    "continuation_method": step_initialization.continuation_method
                    if step_initialization is not None
                    else "",
                    "forced_input_nodes": ",".join(step.input_states.keys()),
                    # Interventions are not input nodes. A name-timed one has no
                    # IN_* node, so it is recorded here or not at all.
                    "step_interventions": ",".join(step.interventions),
                    "memory_node_count": len(step_initialization.node_ids)
                    if step_initialization is not None
                    else 0,
                    "memory_nodes": ",".join(step_initialization.node_ids)
                    if step_initialization is not None
                    else "",
                    "memory_node_policy": step_initialization.memory_node_policy
                    if step_initialization is not None
                    else "",
                    "joint_probability_cutoff": step_initialization.probability_cutoff
                    if step_initialization is not None
                    else 0.0,
                    "source_state_count": step_initialization.source_state_count
                    if step_initialization is not None
                    else 0,
                    "retained_state_count": step_initialization.retained_state_count
                    if step_initialization is not None
                    else 0,
                    "dropped_probability_mass": step_initialization.dropped_probability_mass
                    if step_initialization is not None
                    else 0.0,
                    "transferred_state_count": len(step_initialization.distribution)
                    if step_initialization is not None
                    else 0,
                }
            )
            manifest_continuation_rows.append(
                {
                    "protocol_id": protocol_id,
                    "step_id": step.step_id,
                    "continuation_from": protocol.continuation_from,
                    "continuation_applied": step_initialization is not None,
                    "step_interventions": list(step.interventions),
                    "continuation_mode": step_initialization.mode
                    if step_initialization is not None
                    else None,
                    "continuation_method": step_initialization.continuation_method
                    if step_initialization is not None
                    else None,
                    "memory_nodes": list(step_initialization.node_ids)
                    if step_initialization is not None
                    else [],
                    "memory_node_policy": step_initialization.memory_node_policy
                    if step_initialization is not None
                    else None,
                    "joint_probability_cutoff": step_initialization.probability_cutoff
                    if step_initialization is not None
                    else 0.0,
                    "source_state_count": step_initialization.source_state_count
                    if step_initialization is not None
                    else 0,
                    "retained_state_count": step_initialization.retained_state_count
                    if step_initialization is not None
                    else 0,
                    "dropped_probability_mass": step_initialization.dropped_probability_mass
                    if step_initialization is not None
                    else 0.0,
                    "transferred_state_count": len(step_initialization.distribution)
                    if step_initialization is not None
                    else 0,
                }
            )
        row: dict[str, object] = {"protocol_id": protocol_id}
        row.update(
            {
                name: run.final_result.last.get(name)
                for name in primary_outputs + safety_outputs
            }
        )
        phenotype_rows.append(row)

    if any("interventions" in row for row in protocol_rows):
        # protocol_sequence lists a step's interventions only when it declares
        # some; a table needs the column on every row once any row has it.
        for row in protocol_rows:
            row.setdefault("interventions", [])
    write_tsv(tables_dir / "protocol_phases.tsv", protocol_rows)
    write_tsv(tables_dir / "protocol_initializations.tsv", initialization_rows)
    write_tsv(tables_dir / "phenotype_probabilities.tsv", phenotype_rows)
    for relative_path, kind in (
        ("protocol_phases.tsv", "protocol_phase_table"),
        ("protocol_initializations.tsv", "protocol_initialization_table"),
        ("phenotype_probabilities.tsv", "phenotype_probabilities"),
    ):
        output_refs.append(
            {
                **describe_file(tables_dir / relative_path, root=active_root).__dict__,
                "kind": kind,
            }
        )

    perturbation_rows = []
    if model_version == "adoc-core-v0.1.0":
        maternal_base_id = "hormone_treated"
        challenge_base_id = "adhesion_challenge_hormone_treated"
        perturbation_pairs = [
            (
                "hormone_treated_mifepristone",
                "adhesion_challenge_hormone_treated_mifepristone",
            ),
            (
                "hormone_treated_anti_spp1",
                "adhesion_challenge_hormone_treated_anti_spp1",
            ),
            ("washout", "adhesion_challenge_washout"),
        ]
    else:
        maternal_base_id = "hormone_treated_maternal"
        challenge_base_id = "adhesion_challenge_hormone_treated"
        perturbation_pairs = [
            (
                "hormone_treated_maternal",
                "adhesion_challenge_hormone_treated_mifepristone",
            ),
            (
                "hormone_treated_maternal",
                "adhesion_challenge_hormone_treated_anti_spp1",
            ),
            (
                "hormone_treated_maternal",
                "adhesion_challenge_excess_er_stress",
            ),
            (
                "hormone_treated_maternal",
                "adhesion_challenge_high_ecm_stiffness",
            ),
            (
                "adhesion_challenge_hormone_treated_anti_spp1",
                "adhesion_challenge_washout",
            ),
        ]
    maternal_base = condition_results[maternal_base_id]
    challenge_base = condition_results[challenge_base_id]
    for maternal_protocol, challenge_protocol in perturbation_pairs:
        perturbation_rows.append(
            {
                "maternal_protocol": maternal_protocol,
                "challenge_protocol": challenge_protocol,
                "delta_maternal_competence": maternal_base[
                    "OUT_MATERNAL_ADHESION_COMPETENCE"
                ]
                - condition_results[maternal_protocol][
                    "OUT_MATERNAL_ADHESION_COMPETENCE"
                ],
                "delta_stable_adhesion": challenge_base["OUT_STABLE_ADHESION"]
                - condition_results[challenge_protocol]["OUT_STABLE_ADHESION"],
            }
        )
    write_tsv(tables_dir / "perturbation_effects.tsv", perturbation_rows)
    output_refs.append(
        {
            **describe_file(
                tables_dir / "perturbation_effects.tsv", root=active_root
            ).__dict__,
            "kind": "perturbation_effects",
        }
    )

    (
        calibration_rows,
        calibration_log_likelihood,
        held_out_validation_log_likelihood,
        total_log_likelihood,
        included_units,
        structurally_contradicted,
    ) = _adhesion_objective_rows(
        condition_results=condition_results,
        root=active_root,
    )
    write_tsv(tables_dir / "adhesion_calibration.tsv", calibration_rows)
    output_refs.append(
        {
            **describe_file(
                tables_dir / "adhesion_calibration.tsv", root=active_root
            ).__dict__,
            "kind": "adhesion_calibration",
        }
    )
    write_tsv(
        tables_dir / "adhesion_calibration_summary.tsv",
        [
            {
                "model_version": model_version,
                "calibration_log_likelihood": calibration_log_likelihood,
                "held_out_validation_log_likelihood": held_out_validation_log_likelihood,
                "total_descriptive_log_likelihood": total_log_likelihood,
                "calibration_observation_count": sum(
                    1 for row in calibration_rows if row["used_for_fitting"]
                ),
                "held_out_observation_count": sum(
                    1 for row in calibration_rows if not row["used_for_fitting"]
                ),
                # Adhesion is ordinal/diagnostic, not magnitude-fitted. These
                # two columns say so in the artifact itself, so a reader cannot
                # take the sums above for a model-selection score.
                "objective_role": "diagnostic_ordinal",
                "magnitude_fitted": False,
                "structurally_contradicted_arms": ";".join(structurally_contradicted)
                or "none",
                "log_likelihood_usable_for_ranking": not structurally_contradicted,
            }
        ],
    )
    output_refs.append(
        {
            **describe_file(
                tables_dir / "adhesion_calibration_summary.tsv",
                root=active_root,
            ).__dict__,
            "kind": "adhesion_calibration_summary",
        }
    )

    stability_rows = []
    seed_values = [1, 2, 3]
    per_seed = []
    for seed in seed_values:
        run = run_protocol(
            challenge_base_id,
            model_version=model_version,
            root=active_root,
            continuation=protocol_continuation(
                challenge_base_id,
                protocol_results[
                    get_protocol(
                        challenge_base_id,
                        active_root,
                        model_version=model_version,
                    ).continuation_from
                    or challenge_base_id
                ],
                model_version=model_version,
                root=active_root,
            ),
            rule_variant_selection=selected_rule_variants,
            seed=seed,
            sample_count=500,
        )
        per_seed.append(run.final_result.last)
    for phenotype in primary_outputs:
        values = [row[phenotype] for row in per_seed]
        stability_rows.append(
            {
                "phenotype_id": phenotype,
                "mean_probability": effect_mean(values),
                "span": effect_span(values),
                "seeds": ",".join(str(seed) for seed in seed_values),
            }
        )
    write_tsv(tables_dir / "stability.tsv", stability_rows)
    output_refs.append(
        {
            **describe_file(tables_dir / "stability.tsv", root=active_root).__dict__,
            "kind": "stability_table",
        }
    )

    sensitivity_rows = [
        {
            "variant_id": "phase1_candidate_ihh",
            "status": "declared_not_screened",
            "notes": "Topology retained but not varied in the bounded Phase 1B smoke.",
        },
        {
            "variant_id": "phase1_candidate_spp1",
            "status": "embedded_in_interface",
            "notes": "SPP1 acts through one modular route and no longer gates total maternal competence.",
        },
        {
            "variant_id": "phase1_candidate_xav939_gate",
            "status": "declared_not_screened",
            "notes": "Stricter XAV939-gated secretory-state variant recorded for sensitivity but not used in the bounded smoke.",
        },
        {
            "variant_id": "phase1_candidate_adhesion_interface",
            "status": "active_default",
            "notes": "Bounded stochastic relay states drive the modular adhesion interface in the bounded smoke.",
        },
    ]
    write_tsv(tables_dir / "assumption_sensitivity.tsv", sensitivity_rows)
    output_refs.append(
        {
            **describe_file(
                tables_dir / "assumption_sensitivity.tsv", root=active_root
            ).__dict__,
            "kind": "assumption_sensitivity",
        }
    )

    candidate_scores = [
        _candidate_score(
            candidate_id="mifepristone_after_ht",
            baseline=challenge_base,
            perturbed=condition_results[
                "adhesion_challenge_hormone_treated_mifepristone"
            ],
        ),
        _candidate_score(
            candidate_id="anti_spp1_after_ht",
            baseline=challenge_base,
            perturbed=condition_results["adhesion_challenge_hormone_treated_anti_spp1"],
        ),
    ]
    candidate_rows = [
        {
            "candidate_id": score.candidate_id,
            "ranking_mode": "structural_only",
            "reward": score.reward,
            "penalty": score.penalty,
            "instability": score.instability,
            "scalar": score.scalar,
        }
        for score in candidate_scores
    ]
    pareto_rows = [
        {
            "candidate_id": score.candidate_id,
            "ranking_mode": "structural_only",
            "reward": score.reward,
            "penalty": score.penalty,
            "instability": score.instability,
            "scalar": score.scalar,
        }
        for score in pareto_front(candidate_scores)
    ]
    write_tsv(tables_dir / "candidate_scores.tsv", candidate_rows)
    write_tsv(tables_dir / "pareto_front.tsv", pareto_rows)
    output_refs.append(
        {
            **describe_file(
                tables_dir / "candidate_scores.tsv", root=active_root
            ).__dict__,
            "kind": "candidate_scores",
        }
    )
    output_refs.append(
        {
            **describe_file(tables_dir / "pareto_front.tsv", root=active_root).__dict__,
            "kind": "pareto_front",
        }
    )

    simulation_defaults = _default_simulation_settings(active_root)
    runtime_payload = {
        "engine": "cmaboss",
        "maboss_python_package": _maboss_python_package_version(),
        "primary_protocol_sample_count": int(simulation_defaults["sample_count"]),
        "primary_protocol_seed": 1,
        "primary_protocol_time_tick": float(simulation_defaults["time_tick"]),
        "primary_protocol_max_time": float(simulation_defaults["max_time"]),
        "stability_sample_count": 500,
        "stability_seeds": seed_values,
        "adhesion_objective_calibration_log_likelihood": calibration_log_likelihood,
        "adhesion_objective_held_out_validation_log_likelihood": held_out_validation_log_likelihood,
        "adhesion_objective_total_descriptive_log_likelihood": total_log_likelihood,
        "adhesion_objective_role": "diagnostic_ordinal",
        "adhesion_objective_magnitude_fitted": False,
        "adhesion_objective_structurally_contradicted_arms": structurally_contradicted,
        "note": "The Python package runtime was available even though the standalone MaBoSS binary was absent on PATH.",
    }
    runtime_path = logs_dir / "runtime_report.json"
    runtime_path.write_text(
        json.dumps(runtime_payload, indent=2) + "\n", encoding="utf-8"
    )
    output_refs.append(
        {
            **describe_file(runtime_path, root=active_root).__dict__,
            "kind": "runtime_report",
        }
    )

    figure_payloads = {
        "protocol_state_changes.json": phenotype_rows,
        "target_engagement_curves.json": perturbation_rows,
        "efficacy_vs_safety.json": candidate_rows,
        "uncertainty.json": stability_rows,
    }
    for filename, payload in figure_payloads.items():
        path = figures_dir / filename
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        output_refs.append(
            {**describe_file(path, root=active_root).__dict__, "kind": "figure_payload"}
        )

    report_path = report_dir / "smoke_report.md"
    write_markdown_report(
        report_path,
        title="DT_ADOC Phase 1B Sequential Structural Smoke",
        sections=[
            (
                "Status",
                "Provisional sequential smoke only. Results are executable runtime artifacts, not calibrated or biologically validated claims.",
            ),
            (
                "Summary",
                "Protocols run: "
                + ", ".join(protocols)
                + ". The bounded adhesion-interface relay states produce comparator outputs under the selected model and rule-variant configuration.",
            ),
            (
                "Calibration",
                "Basal challenge probability = "
                + f"{condition_results['adhesion_challenge_basal']['OUT_STABLE_ADHESION']:.3f}; "
                + "HT challenge probability = "
                + f"{condition_results['adhesion_challenge_hormone_treated']['OUT_STABLE_ADHESION']:.3f}; "
                + "HT+mifepristone challenge probability = "
                + f"{condition_results['adhesion_challenge_hormone_treated_mifepristone']['OUT_STABLE_ADHESION']:.3f}; "
                + "calibration log-likelihood = "
                + f"{calibration_log_likelihood:.3f}; "
                + "held-out validation log-likelihood = "
                + f"{held_out_validation_log_likelihood:.3f}; "
                + "total descriptive log-likelihood = "
                + f"{total_log_likelihood:.3f}. "
                + "Adhesion is an ordinal/diagnostic readout, NOT a magnitude-fitted objective "
                + "(demoted 2026-09-16; see docs/gate3_scope_adjudication.md), so these sums "
                + "are descriptive and rank nothing. "
                + (
                    "Structurally contradicted arms (unclipped P=0 with observed successes, "
                    "so the score is log(CLIP_EPSILON) and identical for every candidate): "
                    + ", ".join(structurally_contradicted)
                    + ". "
                    if structurally_contradicted
                    else "No arm is structurally contradicted. "
                ),
            ),
        ],
    )
    output_refs.append(
        {
            **describe_file(report_path, root=active_root).__dict__,
            "kind": "markdown_report",
        }
    )

    mapping_path = active_root / "config" / "evidence_roles.yaml"
    manifest = build_run_manifest(
        run_id=run_id,
        command=(
            f"PYTHONPATH=src python -B -m dt_adoc.cli smoke --run-id {run_id}"
            f" --model-version {model_version}"
        ),
        baseline_bnd=model_spec.network_bnd,
        baseline_cfg=model_spec.baseline_cfg,
        source_manifest=active_root / "config" / "data_manifest.tsv",
        mapping=mapping_path,
        outputs=output_refs,
        phenotypes={
            key: value
            for key, value in phenotype_payload["definitions"].items()
            if key in executable_phenotype_ids
        },
        included_units=included_units,
        exclusions=[],
        leakage_controls="Construction, calibration, and validation evidence roles frozen in config/evidence_roles.yaml.",
        software={
            "maboss_python_package": _maboss_python_package_version(),
            "engine_backend": "cmaboss",
            "model_runtime_version": model_version,
        },
        protocols=protocols,
        simulation=ManifestSimulationSettings(
            seeds=[1],
            trajectory_count=int(simulation_defaults["sample_count"]),
            max_time=float(simulation_defaults["max_time"]),
            time_tick=float(simulation_defaults["time_tick"]),
            thread_count=int(simulation_defaults["thread_count"]),
            perturbation="phase1b_sequential_smoke_suite",
        ),
        simulation_extras={
            "stability": {
                "seeds": seed_values,
                "trajectory_count": 500,
            },
            "trajectory_capture": {
                "source": "cmaboss get_nodes_probtraj()",
                "semantics": "P(node = ON) across simulated MaBoSS trajectories",
                "time_units": "maboss_relative_only",
                "artifact_kind": "raw_nodes_probtraj",
                "step_count": len(trajectory_row_counts),
                "rows_per_step": trajectory_row_counts,
                "input_nodes_excluded": True,
                "input_nodes_note": (
                    "IN_* input nodes are deterministic protocol settings "
                    "(input_states), not simulated quantities, and are "
                    "excluded from the trajectory unless the model tracks "
                    "them. Named interventions are not nodes: each step's "
                    "are listed in step_interventions and rendered into the "
                    "executed network recorded under model.executed_networks."
                ),
            },
        },
        validation_levels=["structural", "synthetic_model"],
        warnings=[
            "Standalone MaBoSS binary is not installed on PATH; smoke used cmaboss.",
            "Primary protocol tables used seed 1 and sample_count from models/specs/parameter_scenarios.yaml; stability.tsv used seeds 1,2,3 with sample_count=500.",
            "Barrier, viability, inflammation, senescence, and washout-recovery outputs remain structural or deferred in Phase 1C.",
            "Candidate ranking remains structural-only until mechanistic safety and washout outputs exist.",
        ],
        root=active_root,
    )
    manifest["model"].update(
        {
            "model_id": model_spec.model_id,
            "model_version": model_spec.model_version,
            "network_bnd": describe_file(
                model_spec.network_bnd, root=active_root
            ).__dict__,
            "baseline_cfg": describe_file(
                model_spec.baseline_cfg, root=active_root
            ).__dict__,
            "node_dictionary": describe_file(
                model_spec.node_dictionary, root=active_root
            ).__dict__,
            "edge_evidence": describe_file(
                model_spec.edge_evidence, root=active_root
            ).__dict__,
            "phenotype_contract": describe_file(
                model_spec.phenotype_contract, root=active_root
            ).__dict__,
            "provenance": describe_file(
                model_spec.provenance, root=active_root
            ).__dict__,
            "selected_rule_variants": selected_rule_variants,
            # Per phase, the network MaBoSS executed; rendered ones are deleted
            # after the run and are reconstructed from these records.
            "executed_networks": executed_network_rows,
        }
    )
    validate_manifest_model_version(
        manifest,
        expected_model_version=model_spec.model_version,
    )
    manifest["simulation"]["continuation"] = {
        "declared_in": protocol_file(model_version, active_root).as_posix(),
        "protocol_initializations": manifest_continuation_rows,
    }
    manifest_path = write_run_manifest(
        output_root / "run_manifest.json", manifest, root=active_root
    )
    output_refs.append(
        {
            **describe_file(manifest_path, root=active_root).__dict__,
            "kind": "run_manifest",
        }
    )
    return output_root


def continuation_with_input_overrides(
    continuation: ContinuationState,
    input_overrides: dict[str, bool],
) -> ContinuationState:
    """Return a continuation whose forced inputs reflect a perturbation.

    A joint continuation pins the target protocol's declared inputs through
    ``forced_nodes``, and those are applied to the network *after* the merged
    cfg. So a caller that perturbs an input only via cfg overrides has it
    silently restored, and the perturbation appears to have no effect.

    ``run_protocol`` never hits this, because it derives both the cfg override
    text and ``forced_nodes`` from the same ``step.input_states``. It bites
    perturbation studies that vary one input while continuing from an
    unperturbed ancestor. Use this helper for those rather than editing
    ``forced_nodes`` by hand.
    """
    forced = dict(continuation.forced_nodes)
    forced.update({node: bool(state) for node, state in input_overrides.items()})
    return replace(continuation, forced_nodes=forced)
