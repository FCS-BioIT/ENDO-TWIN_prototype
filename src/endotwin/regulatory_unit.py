"""A steppable regulatory unit: the interface a multiscale driver would call.

This is not a multiscale model. It wraps one MaBoSS network (the integrated
model, or one compartment from :func:`endotwin.model.split_compartments`) behind
the five operations a per-cell coupling such as PhysiBoSS needs:

1. initialise the regulatory state from a cell state;
2. supply extracellular inputs;
3. execute regulatory dynamics for a duration;
4. read node probabilities, or draw one Boolean state for an agent;
5. pass selected outputs (exported signals, functional outputs) outward.

Durations are MaBoSS time. Mapping them to physical time is a modelling
decision of the external driver and is deliberately not made here
(docs/architecture/future_multiscale_extension.md).
"""

from __future__ import annotations

import random
from collections.abc import Mapping

from endotwin.model import Model, split_compartments
from endotwin.simulate import SimulationSettings, run_phase
from endotwin.structure import free_variables


class RegulatoryUnit:
    def __init__(
        self,
        model: Model,
        *,
        compartment: str | None = None,
        selection: Mapping[str, str] | None = None,
        sample_count: int = 1000,
        seed: int = 1,
        rates: Mapping[str, tuple[float, float]] | None = None,
    ) -> None:
        if compartment is None:
            self.rules = model.rules_for(selection)
            self.exported = tuple(model.outputs)
        else:
            network = split_compartments(model, selection)[compartment]
            self.rules = network.rules
            self.exported = network.exported_signals + tuple(
                n for n in model.outputs if n in network.rules
            )
        self.compartment = compartment
        self.input_nodes = free_variables(self.rules)
        self.state_nodes = tuple(n for n in self.rules if n not in self.input_nodes)
        self._inputs = {n: 0 for n in self.input_nodes}
        self._joint: dict[tuple[int, ...], float] | None = None
        self._probabilities: dict[str, float] = {n: 0.0 for n in self.rules}
        self._settings = SimulationSettings(
            sample_count=sample_count, seed=seed, rates=rates
        )
        self._steps = 0
        self._clock = 0.0

    # 1. initialise ---------------------------------------------------------
    def initialize(self, state: Mapping[str, int]) -> None:
        """Start from one Boolean state (unnamed state nodes are OFF)."""
        unknown = set(state) - set(self.state_nodes)
        if unknown:
            raise KeyError(f"not state nodes of this unit: {sorted(unknown)}")
        key = tuple(int(bool(state.get(n, 0))) for n in self.state_nodes)
        self._joint = {key: 1.0}
        for node, value in zip(self.state_nodes, key, strict=True):
            self._probabilities[node] = float(value)

    # 2. inputs ---------------------------------------------------------------
    def set_inputs(self, values: Mapping[str, int]) -> None:
        unknown = set(values) - set(self.input_nodes)
        if unknown:
            raise KeyError(f"not inputs of this unit: {sorted(unknown)}")
        for node, value in values.items():
            self._inputs[node] = int(bool(value))

    # 3. execute ------------------------------------------------------------
    def step(self, duration: float) -> dict[str, float]:
        if duration <= 0:
            raise ValueError("duration must be positive")
        settings = SimulationSettings(
            sample_count=self._settings.sample_count,
            seed=self._settings.seed + self._steps,
            rates=self._settings.rates,
        )
        result = run_phase(
            self.rules,
            inputs=self._inputs,
            forced={},
            duration=duration,
            # Steps are spaced by the sample count so they never share
            # per-trajectory seeds.
            seed=1
            + (self._settings.seed * 100_000 + self._steps) * settings.sample_count,
            settings=settings,
            carried=self._joint,
            carried_nodes=self.state_nodes,
            start_time=self._clock,
            phase_id=f"step_{self._steps}",
        )
        self._steps += 1
        self._clock += duration
        self._joint = result.joint_final
        self._probabilities = result.final
        return dict(result.final)

    # 4. read -----------------------------------------------------------------
    def probabilities(self) -> dict[str, float]:
        return dict(self._probabilities)

    def sample_state(self, rng: random.Random) -> dict[str, int]:
        """Draw one Boolean state from the current joint distribution."""
        if self._joint is None:
            return {n: 0 for n in self.state_nodes}
        keys = list(self._joint)
        key = rng.choices(keys, weights=[self._joint[k] for k in keys], k=1)[0]
        return dict(zip(self.state_nodes, key, strict=True))

    # 5. pass outward -------------------------------------------------------
    def outputs(self) -> dict[str, float]:
        return {n: self._probabilities[n] for n in self.exported}
