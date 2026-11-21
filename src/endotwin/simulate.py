"""Stochastic simulation of ENDO-TWIN protocols with MaBoSS (cmaboss backend).

Phase semantics. Each phase is one MaBoSS run. At a phase boundary the joint
distribution over every non-input node at the end of the previous phase is
carried forward unchanged, and the new phase's inputs are imposed
deterministically. Nothing is re-initialised, so a jump at a boundary can only
come from an input or intervention change, never from a restart.

Estimator semantics. A reported probability is the fraction of simulated
trajectories with the node ON (MaBoSS time-window means on the time grid). With
a fixed seed the run is exactly reproducible; that is reproducibility, not
Monte Carlo precision. Use :func:`replicate` with disjoint seed blocks to see
run-to-run spread.
"""

from __future__ import annotations

import math
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path

import pandas as pd

from endotwin.model import Model, render_bnd, sha256_file, sha256_text
from endotwin.protocols import Condition, Intervention, forced_nodes

DEFAULT_SAMPLE_COUNT = 5000
DEFAULT_TIME_TICK = 0.1
#: Convergence is declared when no node's probability moves by more than this
#: over the last CONVERGENCE_WINDOW time units of a phase.
CONVERGENCE_TOLERANCE = 0.01
CONVERGENCE_WINDOW = 2.0
#: A MaBoSS run of N trajectories uses N consecutive per-trajectory seeds
#: (docs/maboss_estimator_semantics.md, 2026-09-23 addendum), so two runs share
#: trajectories unless their seeds are at least N apart. Phase seeds are spaced
#: by the sample count and replicate blocks by MAX_PHASES phase blocks.
MAX_PHASES = 16


def phase_seed(settings: SimulationSettings, phase_index: int) -> int:
    if not 0 <= phase_index < MAX_PHASES:
        raise ValueError(f"at most {MAX_PHASES} phases per condition")
    block = settings.sample_count * MAX_PHASES
    return 1 + settings.seed * block + phase_index * settings.sample_count


@dataclass(frozen=True)
class SimulationSettings:
    sample_count: int = DEFAULT_SAMPLE_COUNT
    time_tick: float = DEFAULT_TIME_TICK
    seed: int = 1
    rates: Mapping[str, tuple[float, float]] | None = None
    #: Initial distribution of non-input nodes at the start of the first phase,
    #: as ``{node: P(ON)}`` (independent). Default: every node OFF.
    initial_probabilities: Mapping[str, float] | None = None
    duration_scale: float = 1.0

    def as_dict(self) -> dict[str, object]:
        return {
            "sample_count": self.sample_count,
            "time_tick": self.time_tick,
            "seed": self.seed,
            "rates": {k: list(v) for k, v in sorted((self.rates or {}).items())},
            "initial_probabilities": dict(
                sorted((self.initial_probabilities or {}).items())
            ),
            "duration_scale": self.duration_scale,
        }


@dataclass
class PhaseResult:
    phase_id: str
    start_time: float
    duration: float
    seed: int
    network_sha256: str
    forced: dict[str, int]
    inputs: dict[str, int]
    trajectory: pd.DataFrame
    final: dict[str, float]
    joint_final: dict[tuple[int, ...], float]
    converged: bool
    max_late_change: float


@dataclass
class ConditionResult:
    condition_id: str
    model_version: str
    selection: dict[str, str]
    settings: SimulationSettings
    phases: list[PhaseResult] = field(default_factory=list)

    def final(self, phase_id: str) -> dict[str, float]:
        for phase in self.phases:
            if phase.phase_id == phase_id:
                return phase.final
        raise KeyError(phase_id)

    def trajectory(self) -> pd.DataFrame:
        frames = []
        for index, phase in enumerate(self.phases):
            frame = phase.trajectory.copy()
            frame.insert(0, "phase_index", index)
            frame.insert(1, "phase_id", phase.phase_id)
            frames.append(frame)
        return pd.concat(frames, ignore_index=True)

    def provenance(self) -> dict[str, object]:
        return {
            "condition_id": self.condition_id,
            "model_version": self.model_version,
            "rule_variants": dict(sorted(self.selection.items())),
            "settings": self.settings.as_dict(),
            "engine": engine_report(),
            "phases": [
                {
                    "phase_id": p.phase_id,
                    "start_time": p.start_time,
                    "relative_duration": p.duration,
                    "seed": p.seed,
                    "inputs": p.inputs,
                    "forced": p.forced,
                    "network_sha256": p.network_sha256,
                    "converged": p.converged,
                    "max_change_over_last_window": round(p.max_late_change, 6),
                }
                for p in self.phases
            ],
        }


def engine_report() -> dict[str, str]:
    try:
        version = metadata.version("maboss")
    except metadata.PackageNotFoundError:  # pragma: no cover - environment
        version = "unavailable"
    return {"package": "maboss", "version": version, "backend": "cmaboss"}


def _cfg_text(
    nodes: tuple[str, ...], settings: SimulationSettings, max_time: float, seed: int
) -> str:
    lines = [
        "discrete_time = 0;",
        "use_physrandgen = FALSE;",
        f"seed_pseudorandom = {seed};",
        f"sample_count = {settings.sample_count};",
        f"max_time = {max_time!r};",
        f"time_tick = {settings.time_tick!r};",
        "thread_count = 1;",
        "display_traj = FALSE;",
    ]
    lines += [f"{n}.istate = FALSE;" for n in nodes]
    lines += [f"{n}.is_internal = FALSE;" for n in nodes]
    return "\n".join(lines) + "\n"


def _parse_state(label: str) -> frozenset[str]:
    label = label.strip()
    if not label or label == "<nil>":
        return frozenset()
    return frozenset(t.strip() for t in label.split(" -- ") if t.strip())


def run_phase(
    rules: Mapping[str, str],
    *,
    inputs: Mapping[str, int],
    forced: Mapping[str, int],
    duration: float,
    seed: int,
    settings: SimulationSettings,
    carried: Mapping[tuple[int, ...], float] | None,
    carried_nodes: tuple[str, ...],
    start_time: float,
    phase_id: str,
) -> PhaseResult:
    import maboss  # local: keep the model layer importable without MaBoSS

    text = render_bnd(rules, rates=settings.rates, forced=forced)
    workdir = Path(tempfile.mkdtemp(prefix="endotwin_"))
    try:
        bnd = workdir / "network.bnd"
        cfg = workdir / "run.cfg"
        bnd.write_text(text, encoding="utf-8")
        nodes_order = tuple(rules)
        cfg.write_text(
            _cfg_text(nodes_order, settings, duration, seed), encoding="utf-8"
        )
        sim = maboss.load(str(bnd), str(cfg), cmaboss=True)
        net = sim.network
        if carried is not None:
            net.set_istate(list(carried_nodes), dict(carried))
        elif settings.initial_probabilities:
            for node, p in settings.initial_probabilities.items():
                net.set_istate(node, [1.0 - float(p), float(p)])
        for node, value in inputs.items():
            net.set_istate(node, [1.0 - value, float(value)])
        result = sim.run()
        nodes = result.get_nodes_probtraj()
        states = result.get_last_states_probtraj()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    node_list = list(rules)
    trajectory = nodes.reindex(columns=node_list, fill_value=0.0).copy()
    trajectory.insert(0, "time", trajectory.index.astype(float) + start_time)
    trajectory = trajectory.reset_index(drop=True)
    # MaBoSS sums trajectory weights in floating point (1.0000000000000089 is
    # common); 12 decimals is far below any Monte Carlo resolution used here.
    final = {n: round(float(trajectory[n].iloc[-1]), 12) for n in node_list}

    joint: dict[tuple[int, ...], float] = {}
    for label, prob in states.iloc[-1].items():
        p = float(prob)
        if p <= 0.0 or not math.isfinite(p):
            continue
        on = _parse_state(str(label))
        key = tuple(1 if n in on else 0 for n in carried_nodes)
        joint[key] = joint.get(key, 0.0) + p
    total = sum(joint.values())
    joint = {k: v / total for k, v in joint.items()}

    window = trajectory[
        trajectory["time"] >= trajectory["time"].iloc[-1] - CONVERGENCE_WINDOW
    ]
    late_change = float((window[node_list].max() - window[node_list].min()).max())
    return PhaseResult(
        phase_id=phase_id,
        start_time=start_time,
        duration=duration,
        seed=seed,
        network_sha256=sha256_text(text),
        forced=dict(forced),
        inputs=dict(inputs),
        trajectory=trajectory,
        final=final,
        joint_final=joint,
        converged=late_change <= CONVERGENCE_TOLERANCE,
        max_late_change=late_change,
    )


def simulate_condition(
    model: Model,
    condition: Condition,
    interventions: Mapping[str, Intervention],
    selection: Mapping[str, str] | None = None,
    settings: SimulationSettings | None = None,
) -> ConditionResult:
    settings = settings or SimulationSettings()
    resolved = model.resolve_selection(selection)
    rules = model.rules_for(resolved)
    carried_nodes = tuple(n for n in model.nodes if n not in model.inputs)
    out = ConditionResult(
        condition_id=condition.condition_id,
        model_version=model.version,
        selection=resolved,
        settings=settings,
    )
    carried: dict[tuple[int, ...], float] | None = None
    clock = 0.0
    for index, phase in enumerate(condition.phases):
        duration = phase.relative_duration * settings.duration_scale
        seed = phase_seed(settings, index)
        result = run_phase(
            rules,
            inputs=phase.inputs,
            forced=forced_nodes(phase, interventions),
            duration=duration,
            seed=seed,
            settings=settings,
            carried=carried,
            carried_nodes=carried_nodes,
            start_time=clock,
            phase_id=phase.phase_id,
        )
        out.phases.append(result)
        carried = result.joint_final
        clock += duration
    return out


def replicate(
    model: Model,
    condition: Condition,
    interventions: Mapping[str, Intervention],
    *,
    replicates: int,
    selection: Mapping[str, str] | None = None,
    base: SimulationSettings | None = None,
) -> list[ConditionResult]:
    """Independent runs on disjoint seed blocks (seed = base.seed + r)."""
    base = base or SimulationSettings()
    results = []
    for r in range(replicates):
        settings = SimulationSettings(
            sample_count=base.sample_count,
            time_tick=base.time_tick,
            seed=base.seed + 1 + r,
            rates=base.rates,
            initial_probabilities=base.initial_probabilities,
            duration_scale=base.duration_scale,
        )
        results.append(
            simulate_condition(model, condition, interventions, selection, settings)
        )
    return results


def model_file_digests(model: Model) -> dict[str, str]:
    return {p.name: sha256_file(p) for p in sorted(model.root.iterdir()) if p.is_file()}
