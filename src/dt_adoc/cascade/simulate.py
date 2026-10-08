"""Paired single-trajectory runs from an established protocol state.

Everything executes through ``dt_adoc.simulation.runner``: the starting lineage
with ``run_protocol`` and ``protocol_continuation``, each perturbed-phase
trajectory with ``run_cmaboss_condition``. Interventions and rule variants
therefore go through the intervention engine and its licences, exactly as in
every other result of the repository.

Three choices here are not the runner's defaults, and each is recorded:

- **Initial states are drawn here, not by MaBoSS.** Each trajectory's starting
  state is drawn i.i.d. from the projected terminal distribution of the starting
  protocol with a NumPy generator, and the run is given that one state with
  probability 1. Both arms of pair ``k`` therefore start in *exactly* the same
  state. MaBoSS's own initial draw over consecutive per-trajectory seeds is
  stratified, not i.i.d. (``docs/maboss_estimator_semantics.md``, addendum).
- **Per-trajectory seeds are spread, not consecutive.** They come from
  ``numpy.random.SeedSequence(master_seed)``, are checked to be distinct, and
  are recorded per trajectory. Under the default Rand48 generator consecutive
  seeds give lag-correlated event streams (Stage A, ``docs/perturbation_cascade``).
  Distinct seeds are not a proof of independence; the record says so.
- **The two arms share seed ``k``** (common random numbers). That does not pair
  the event streams: a different network consumes the stream differently, so a
  shared seed is not an individual counterfactual. Comparisons between arms are
  distributional.
"""

from __future__ import annotations

import hashlib
import math
import re
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dt_adoc.cascade.events import trajectory_events
from dt_adoc.concordance.simulate import protocol_lineage
from dt_adoc.maboss_adapter import render_network_with_logic_overrides
from dt_adoc.model.provenance import describe_file, repo_root
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.engine import _evaluable, _value
from dt_adoc.perturbations.spec import PerturbationSpec, start_step
from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.simulation.runner import (
    ContinuationState,
    _input_override_text,
    joint_continuation_from_last_states,
    protocol_continuation,
    run_cmaboss_condition,
    run_protocol,
)

#: Largest seed handed to MaBoSS (``seed_pseudorandom`` is a signed int).
MAX_SEED = 2**31 - 2
SEED_SCHEME = (
    "per-trajectory seed k = SeedSequence(master_seed).generate_state(n, uint32)[k]"
    " mod (2**31 - 2) + 1, distinct by check; initial state k drawn by"
    " numpy.random.default_rng(SeedSequence([master_seed, 1])).choice over the"
    " projected start distribution; arms share seed k and initial state k"
)


@dataclass(frozen=True)
class StartSettings:
    """How the starting ensemble is built from the start protocol's lineage."""

    init_horizon: float | None = 25.0
    """Horizon of every lineage phase (``run_protocol(phase_horizon=)``); None
    uses each phase's declared duration. Dimensionless MaBoSS time, not days."""
    lineage_seed: int = 1
    lineage_trajectories: int = 5000
    memory_policy: str = "all_non_inputs"
    probability_cutoff: float = 0.0


@dataclass(frozen=True)
class PhaseSettings:
    """The perturbed phase: MaBoSS ``max_time`` and ``time_tick``.

    MaBoSS reports ``floor(max_time / time_tick)`` whole windows, the ratio
    taken in floating point: 1.05 / 0.1 gives 10 windows ending at 1.0, and
    0.3 / 0.1 (= 2.9999999999999996) gives 2 ending at 0.2. A horizon is
    accepted only when that ratio is exactly an integer, so the windows end at
    the recorded horizon; ``_one_trajectory`` also checks the window count.
    """

    horizon: float = 25.0
    tick: float = 0.01

    def __post_init__(self) -> None:
        if not (math.isfinite(self.horizon) and math.isfinite(self.tick)):
            raise ValueError("horizon and tick must be finite")
        if self.horizon <= 0 or self.tick <= 0:
            raise ValueError(
                f"horizon and tick must be positive, got {self.horizon}, {self.tick}"
            )
        if not (self.horizon / self.tick).is_integer():
            raise ValueError(
                f"horizon {self.horizon} is not a whole number of ticks of "
                f"{self.tick} in floating point ({self.horizon / self.tick!r}); "
                "MaBoSS would stop at the last whole tick"
            )

    @property
    def n_windows(self) -> int:
        return round(self.horizon / self.tick)


@dataclass(frozen=True)
class StartingEnsemble:
    model_version: str
    start: str
    lineage: tuple[str, ...]
    settings: StartSettings
    continuation: ContinuationState
    condition_cfg: Path
    step_inputs: dict[str, bool]
    step_interventions: tuple[str, ...]
    lineage_records: tuple[dict[str, Any], ...] = ()

    def record(self, root: Path | None = None) -> dict[str, Any]:
        c = self.continuation
        return {
            "start_protocol": self.start,
            "lineage": list(self.lineage),
            "init_horizon": self.settings.init_horizon,
            "init_horizon_semantics": "dimensionless MaBoSS relative time; not calibrated to hours or days",
            "lineage_seed": self.settings.lineage_seed,
            "lineage_trajectories": self.settings.lineage_trajectories,
            "lineage_continuations": "each lineage phase continues from its parent by the protocol's own registered continuation (protocol_continuation)",
            "perturbation_memory_policy": self.settings.memory_policy,
            "probability_cutoff": self.settings.probability_cutoff,
            "memory_nodes": list(c.node_ids),
            "start_state_count": c.retained_state_count,
            "source_state_count": c.source_state_count,
            "dropped_probability_mass": c.dropped_probability_mass,
            "start_distribution": [
                {"state": "".join(map(str, s)), "probability": p}
                for s, p in sorted(c.distribution.items(), key=lambda kv: -kv[1])
            ],
            "condition_cfg": describe_file(self.condition_cfg, root=root).__dict__,
            "start_step_inputs": dict(sorted(self.step_inputs.items())),
            "start_step_interventions": list(self.step_interventions),
            "lineage_phases": list(self.lineage_records),
        }


#: Policies the runner's projection supports without further arguments; the
#: model's own registered policies are accepted too. ``explicit`` is refused
#: because it needs a node list this analysis does not take.
GENERIC_MEMORY_POLICIES = ("all_non_inputs", "relay_only")


def validate_memory_policy(
    model_version: str, policy: str, root: Path | None = None
) -> None:
    """Refuse a continuation policy the runner would not apply as named.

    The runner's node selection treats an unrecognised policy string like a
    relay-only carry-over, so a typo would silently change the starting
    ensemble; it is refused here instead, before anything is simulated.
    """
    allowed = set(GENERIC_MEMORY_POLICIES) | set(
        resolve_model(model_version, root).memory_policies
    )
    if policy not in allowed:
        raise ValueError(
            f"unknown continuation policy {policy!r} for {model_version}; "
            f"choose one of {sorted(allowed)}"
        )


def build_starting_ensemble(
    spec: PerturbationSpec,
    settings: StartSettings | None = None,
    root: Path | None = None,
) -> StartingEnsemble:
    """Run the start protocol's lineage and project its terminal distribution."""
    settings = settings or StartSettings()
    validate_memory_policy(spec.model_version, settings.memory_policy, root)
    active_root = root or repo_root()
    protocol, step = start_step(spec, active_root)
    lineage = protocol_lineage(
        spec.start, model_version=spec.model_version, root=active_root
    )
    continuation = None
    records = []
    final = None
    for index, protocol_id in enumerate(lineage):
        result = run_protocol(
            protocol_id,
            model_version=spec.model_version,
            root=active_root,
            continuation=continuation,
            seed=settings.lineage_seed,
            sample_count=settings.lineage_trajectories,
            phase_horizon=settings.init_horizon,
        )
        try:
            records.append(
                {
                    "protocol_id": protocol_id,
                    "steps": [
                        {
                            "network_sha256": s.executed_network["network_sha256"],
                            "named_interventions": s.executed_network[
                                "named_interventions"
                            ],
                        }
                        for s in result.step_results
                    ],
                    "condition_cfg": describe_file(
                        active_root
                        / get_protocol(
                            protocol_id, active_root, model_version=spec.model_version
                        ).condition_cfg,
                        root=active_root,
                    ).__dict__,
                    "continued_from": None
                    if continuation is None
                    else continuation.source_protocol,
                    "continuation_policy": None
                    if continuation is None
                    else continuation.memory_node_policy,
                }
            )
            if index + 1 < len(lineage):
                continuation = protocol_continuation(
                    lineage[index + 1],
                    result,
                    model_version=spec.model_version,
                    root=active_root,
                )
            else:
                final = result.final_result.last_states_probtraj.copy()
        finally:
            result.release()
    projected = joint_continuation_from_last_states(
        last_states_probtraj=final,
        model_version=spec.model_version,
        root=active_root,
        excluded_nodes=set(step.input_states),
        forced_nodes=dict(step.input_states),
        source_protocol=spec.start,
        probability_cutoff=settings.probability_cutoff,
        memory_node_policy=settings.memory_policy,
    )
    return StartingEnsemble(
        model_version=spec.model_version,
        start=spec.start,
        lineage=lineage,
        settings=settings,
        continuation=projected,
        condition_cfg=active_root / protocol.condition_cfg,
        step_inputs=dict(step.input_states),
        step_interventions=tuple(step.interventions),
        lineage_records=tuple(records),
    )


def trajectory_seeds(master_seed: int, n: int) -> np.ndarray:
    raw = np.random.SeedSequence(master_seed).generate_state(n, dtype=np.uint32)
    seeds = (raw.astype(np.int64) % MAX_SEED) + 1
    if len(np.unique(seeds)) != n:
        raise ValueError("per-trajectory seeds collide; choose another master seed")
    return seeds


def sample_initial_states(
    ensemble: StartingEnsemble, n: int, master_seed: int
) -> np.ndarray:
    states = sorted(ensemble.continuation.distribution)
    p = np.array([ensemble.continuation.distribution[s] for s in states], dtype=float)
    rng = np.random.default_rng(np.random.SeedSequence([master_seed, 1]))
    index = rng.choice(len(states), size=n, p=p / p.sum())
    return np.array([states[i] for i in index], dtype=np.int8)


@dataclass(frozen=True)
class Arm:
    name: str
    input_states: dict[str, bool]
    interventions: tuple[str, ...]
    rule_variants: dict[str, str] = field(default_factory=dict)


def arms_for(spec: PerturbationSpec, ensemble: StartingEnsemble) -> tuple[Arm, Arm]:
    """The perturbed arm and its matched control: identical but for the spec's effects.

    Both keep every input and every intervention active at the end of the start
    protocol, so a start that already carries an intervention keeps it.
    """
    control = Arm("control", dict(ensemble.step_inputs), ensemble.step_interventions)
    perturbed = Arm(
        "perturbed",
        {**ensemble.step_inputs, **spec.input_changes},
        ensemble.step_interventions + spec.interventions,
        dict(spec.rule_variants),
    )
    return perturbed, control


_LOGIC_CACHE: dict[tuple, dict] = {}


def _logic(model_version: str, overrides: dict[str, str], root: Path) -> dict:
    """The executed rules, keyed by the exact network text they come from.

    The key is the SHA-256 of the rendered network, so two roots, two model
    files or two override sets never share an entry unless the network
    MaBoSS executes is byte-identical.
    """
    text = resolve_model(model_version, root).network_bnd.read_text(encoding="utf-8")
    text = render_network_with_logic_overrides(text, logic_overrides=overrides)
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if key not in _LOGIC_CACHE:
        logic = dict(re.findall(r"Node\s+(\w+)\s*\{\s*logic\s*=\s*([^;]+);", text))
        _LOGIC_CACHE[key] = {n: _evaluable(e) for n, e in logic.items()}
    return _LOGIC_CACHE[key]


def _one_trajectory(job: tuple) -> dict[str, Any]:
    (model_version, root, cfg, base_continuation, arm, state, seed, phase) = job
    continuation = replace(
        base_continuation,
        distribution={tuple(int(v) for v in state): 1.0},
        forced_nodes=dict(arm.input_states),
    )
    result = run_cmaboss_condition(
        model_version=model_version,
        condition_cfg=cfg,
        root=root,
        override_texts=[
            _input_override_text(arm.input_states),
            f"max_time = {phase.horizon};\ntime_tick = {phase.tick};\n",
        ],
        continuation=continuation,
        rule_variant_selection=arm.rule_variants or None,
        interventions=arm.interventions,
        seed=int(seed),
        sample_count=1,
    )
    try:
        table = result.nodes_probtraj
        nodes = [str(c) for c in table.columns]
        starts = np.asarray(table.index, dtype=float)
        if len(starts) != phase.n_windows:
            raise RuntimeError(
                f"MaBoSS returned {len(starts)} windows for horizon {phase.horizon} "
                f"and tick {phase.tick}, expected {phase.n_windows}"
            )
        known = dict(zip(base_continuation.node_ids, (int(v) for v in state)))
        events = trajectory_events(
            table.to_numpy(dtype=float), starts, nodes, phase.tick, known
        )
        executed = result.executed_network
        logic = _logic(model_version, executed["logic_overrides"], root)
        final_state = {
            n: bool(e.final) for n, e in events.items() if e.final is not None
        }
        values = {**{k: bool(v) for k, v in arm.input_states.items()}, **final_state}
        rows = []
        for node, e in events.items():
            at_risk = None
            if e.final is not None and node in logic:
                expr, names = logic[node]
                if names <= set(values):
                    at_risk = bool(_value(expr, values) != values[node])
            rows.append(
                (
                    node,
                    e.initial,
                    e.final,
                    e.n_min,
                    e.first_time,
                    e.first_lower,
                    e.first_upper,
                    e.first_resolved,
                    e.last_time,
                    e.last_resolved,
                    e.category,
                    at_risk,
                )
            )
        return {
            "rows": rows,
            "network_sha256": executed["network_sha256"],
            "executed_network": executed,
            "window_count": len(starts),
            "first_window_start": float(starts[0]),
        }
    finally:
        result.release()


EVENT_COLUMNS = (
    "node",
    "initial",
    "final",
    "n_switches_min",
    "first_switch_time",
    "first_switch_lower",
    "first_switch_upper",
    "first_switch_resolved",
    "last_switch_time",
    "last_switch_resolved",
    "category",
    "rule_disagrees_at_horizon",
)


@dataclass(frozen=True)
class ArmResult:
    arm: Arm
    events: pd.DataFrame
    executed_network: dict[str, Any]


def run_arm(
    ensemble: StartingEnsemble,
    arm: Arm,
    states: np.ndarray,
    seeds: np.ndarray,
    phase: PhaseSettings,
    *,
    workers: int = 4,
    root: Path | None = None,
) -> ArmResult:
    active_root = root or repo_root()
    jobs = [
        (
            ensemble.model_version,
            active_root,
            ensemble.condition_cfg,
            ensemble.continuation,
            arm,
            states[k],
            int(seeds[k]),
            phase,
        )
        for k in range(len(seeds))
    ]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            outputs = list(pool.map(_one_trajectory, jobs, chunksize=16))
    else:
        outputs = [_one_trajectory(job) for job in jobs]
    shas = {o["network_sha256"] for o in outputs}
    if len(shas) != 1:
        raise RuntimeError(f"arm {arm.name} executed {len(shas)} different networks")
    if {o["first_window_start"] for o in outputs} != {0.0}:
        raise RuntimeError(
            "a trajectory table does not start at the perturbation boundary"
        )
    frames = []
    for k, o in enumerate(outputs):
        f = pd.DataFrame(o["rows"], columns=EVENT_COLUMNS)
        f.insert(0, "trajectory", k)
        frames.append(f)
    events = pd.concat(frames, ignore_index=True)
    # Fail here, before anything is written, rather than in the summary.
    from dt_adoc.cascade.summary import require_known_initial_states

    require_known_initial_states(events)
    events.insert(0, "arm", arm.name)
    events.insert(2, "seed", np.repeat(seeds, len(outputs[0]["rows"])))
    return ArmResult(arm, events, outputs[0]["executed_network"])
