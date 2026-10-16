"""Stage 1 of the intervention-layer refactor: same-seed MaBoSS equivalence.

Gates G5 and G6 of ``docs/intervention_layer_refactor_plan.md``.

Two routes run each declared intervention lineage of v0.5.2 end to end:

- **legacy**: the protocols exactly as declared, with the ``IN_*`` input set in
  the phases where it is active;
- **engine**: the legacy input held at 0 in every phase, and the library's
  rendering applied in exactly the phases where the legacy input was 1.

Both go through the production ``run_cmaboss_condition``; the engine's overrides
reach the network through its own ``render_network_with_logic_overrides`` call.
The runner is pinned to ``INTERVENTION_ROUTING = "legacy"`` here, because these
gates compare the Stage 1 primitive with the model's own rules; Stage 2's
routing has its own gate in ``test_intervention_routing_runtime.py``.
Comparisons drop the ``IN_*`` nodes, because the engine route changes their
value by construction and ``IN_HAND2_LOSS`` is visible in state labels.
"""

from __future__ import annotations

import sys
import unittest
from collections.abc import Callable
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.concordance.simulate import protocol_lineage
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.engine import (
    intervention_logic_overrides,
    load_intervention_library,
)
from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.simulation import runner

MODEL_VERSION = "adoc-literature-superset-v0.5.2"
SEEDS = (1, 2)
SAMPLE_COUNT = 500
#: Final protocol of each lineage, and the intervention it exercises. The washout
#: lineage lifts the anti-SPP1 veto again, so the "veto ends" transition is
#: covered as well as the "veto starts" one.
LINEAGES = {
    "adhesion_challenge_hormone_treated_mifepristone": "mifepristone",
    "adhesion_challenge_hormone_treated_anti_spp1": "anti_spp1",
    "adhesion_challenge_hormone_treated_hand2_loss": "hand2_loss",
    "adhesion_challenge_washout": "anti_spp1",
}

Route = Callable[[dict[str, bool]], tuple[dict[str, bool], dict[str, str]]]


def _legacy(input_states: dict[str, bool]) -> tuple[dict[str, bool], dict[str, str]]:
    return dict(input_states), {}


def _run_lineage(
    final_protocol: str, *, seed: int, route: Route
) -> list[runner.ConditionRunResult]:
    """Every step of the lineage, chained exactly as ``run_protocol`` and
    ``protocol_continuation`` chain them, with ``route`` choosing inputs and
    logic overrides per step."""
    steps = []
    for protocol_id in protocol_lineage(
        final_protocol, model_version=MODEL_VERSION, root=ROOT
    ):
        protocol = get_protocol(protocol_id, ROOT, model_version=MODEL_VERSION)
        steps.extend(
            (protocol_id, protocol.condition_cfg, step) for step in protocol.steps
        )
    results: list[runner.ConditionRunResult] = []
    continuation = None
    for index, (protocol_id, condition_cfg, step) in enumerate(steps):
        inputs, overrides = route(step.input_states)
        with mock.patch.object(
            runner, "resolve_rule_variants", return_value=({}, overrides)
        ):
            result = runner.run_cmaboss_condition(
                model_version=MODEL_VERSION,
                condition_cfg=ROOT / condition_cfg,
                root=ROOT,
                override_texts=[
                    runner._input_override_text(inputs),
                    runner._timing_override_text(
                        relative_duration=step.relative_duration, root=ROOT
                    ),
                ],
                continuation=continuation,
                seed=seed,
                sample_count=SAMPLE_COUNT,
            )
        results.append(result)
        if index + 1 < len(steps):
            next_protocol, _, next_step = steps[index + 1]
            continuation = runner.build_continuation(
                previous_condition=result,
                target_protocol_id=next_protocol,
                model_version=MODEL_VERSION,
                forced_nodes=route(next_step.input_states)[0],
                source_protocol=protocol_id,
                root=ROOT,
                mode=None,
            )
    return results


def _input_off_route(legacy_input: str, overrides: dict[str, str]) -> Route:
    """Hold ``legacy_input`` at 0, and apply ``overrides`` where it was declared 1."""

    def route(input_states: dict[str, bool]) -> tuple[dict[str, bool], dict[str, str]]:
        # An input a step does not declare keeps its cfg value and stays out of
        # ``forced_nodes``; adding the key would change what the continuation
        # carries, so only a declared input is switched off.
        if not input_states.get(legacy_input, False):
            return dict(input_states), {}
        return {**input_states, legacy_input: False}, dict(overrides)

    return route


def _biological(result: runner.ConditionRunResult) -> dict[str, object]:
    """Everything the run reports, with ``IN_*`` nodes projected out."""
    trajectory = result.nodes_probtraj
    keep = [c for c in trajectory.columns if not str(c).startswith("IN_")]
    projected: dict[frozenset[str], float] = {}
    last_states = result.last_states_probtraj.iloc[-1]
    for label in sorted(last_states.index):
        active = frozenset(
            token.strip()
            for token in str(label).split(" -- ")
            if token.strip()
            and token.strip() != "<nil>"
            and not token.strip().startswith("IN_")
        )
        projected[active] = projected.get(active, 0.0) + float(last_states[label])
    return {
        "times": list(trajectory.index),
        "columns": keep,
        "trajectory": trajectory[keep].to_numpy().tolist(),
        "last": {k: v for k, v in result.last.items() if not k.startswith("IN_")},
        "last_states": {k: v for k, v in projected.items() if v != 0.0},
    }


class InterventionEngineRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.object(runner, "INTERVENTION_ROUTING", "legacy")
        patcher.start()
        self.addCleanup(patcher.stop)

    @classmethod
    def setUpClass(cls) -> None:
        cls.library = load_intervention_library(ROOT)
        cls.network_text = resolve_model(MODEL_VERSION, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )

    def engine_route(self, intervention_id: str) -> Route:
        overrides = intervention_logic_overrides(
            self.network_text,
            [intervention_id],
            model_version=MODEL_VERSION,
            library=self.library,
        )
        self.assertTrue(overrides)
        return _input_off_route(
            self.library[intervention_id][0].legacy_input_node, overrides
        )

    def fast_clamp_route(self, intervention_id: str) -> Route:
        """The deliberately wrong implementation: pyMaBoSS ``mutate(OFF)`` kinetics."""
        targets = [e.target_node for e in self.library[intervention_id]]
        # pyMaBoSS divides 1E308 by the number of mutated nodes so that the summed
        # rate stays finite; two clamped nodes at 1E308 each overflow to inf.
        rate = f"{1e308 / len(targets):.0E}"
        clamp = {node: f"0;\n  rate_up = 0;\n  rate_down = {rate}" for node in targets}
        return _input_off_route(
            self.library[intervention_id][0].legacy_input_node, clamp
        )

    def test_the_lineage_helper_reproduces_production_chaining(self) -> None:
        """The helper's legacy route is the production ``run_protocol`` chain, bit for bit,
        so equivalence measured through it is equivalence of the real runs."""
        final = "adhesion_challenge_hormone_treated_mifepristone"
        lineage = protocol_lineage(final, model_version=MODEL_VERSION, root=ROOT)
        production: list[runner.ConditionRunResult] = []
        continuation = None
        for index, protocol_id in enumerate(lineage):
            run = runner.run_protocol(
                protocol_id,
                model_version=MODEL_VERSION,
                root=ROOT,
                continuation=continuation,
                seed=SEEDS[0],
                sample_count=SAMPLE_COUNT,
            )
            production.extend(run.step_results)
            if index + 1 < len(lineage):
                continuation = runner.protocol_continuation(
                    lineage[index + 1], run, model_version=MODEL_VERSION, root=ROOT
                )
        helper = _run_lineage(final, seed=SEEDS[0], route=_legacy)
        self.assertEqual(len(helper), len(production))
        for ours, theirs in zip(helper, production):
            self.assertEqual(
                ours.nodes_probtraj.to_dict(), theirs.nodes_probtraj.to_dict()
            )
            self.assertEqual(
                ours.last_states_probtraj.to_dict(),
                theirs.last_states_probtraj.to_dict(),
            )

    def test_engine_route_is_bit_identical_on_every_intervention_lineage(self) -> None:
        for final, intervention_id in LINEAGES.items():
            for seed in SEEDS:
                with self.subTest(lineage=final, seed=seed):
                    legacy = _run_lineage(final, seed=seed, route=_legacy)
                    engine = _run_lineage(
                        final, seed=seed, route=self.engine_route(intervention_id)
                    )
                    self.assertEqual(len(legacy), len(engine))
                    for step, (a, b) in enumerate(zip(legacy, engine)):
                        self.assertEqual(_biological(a), _biological(b), f"step {step}")

    def test_omitting_the_veto_is_detected_on_every_lineage(self) -> None:
        """The comparison has power, and the patched overrides really reach MaBoSS:
        switching the legacy input off without rendering the veto must differ."""
        for final, intervention_id in LINEAGES.items():
            input_off_only = _input_off_route(
                self.library[intervention_id][0].legacy_input_node, {}
            )
            with self.subTest(lineage=final):
                legacy = _run_lineage(final, seed=SEEDS[0], route=_legacy)
                missing = _run_lineage(final, seed=SEEDS[0], route=input_off_only)
                self.assertNotEqual(
                    [_biological(r) for r in legacy], [_biological(r) for r in missing]
                )

    def test_the_mifepristone_lineage_exercises_decay_of_active_targets(self) -> None:
        """Without targets that are ON when the veto starts, G6 would prove nothing."""
        results = _run_lineage(
            "adhesion_challenge_hormone_treated_mifepristone",
            seed=SEEDS[0],
            route=_legacy,
        )
        before_veto = results[2].last  # hormone_treated_maternal, the phase before
        self.assertGreater(before_veto["E_PGR"], 0.5)
        self.assertGreater(before_veto["S_PGR"], 0.5)
        first_tick = results[3].nodes_probtraj.iloc[0]
        self.assertGreater(first_tick["E_PGR"], 0.5)  # decaying, not yet gone
        self.assertGreater(first_tick["S_PGR"], 0.5)

    def test_a_fast_clamp_is_not_equivalent(self) -> None:
        """G6, the negative control: an instantaneous clamp must fail the G5 comparison."""
        final = "adhesion_challenge_hormone_treated_mifepristone"
        legacy = _run_lineage(final, seed=SEEDS[0], route=_legacy)
        clamped = _run_lineage(
            final, seed=SEEDS[0], route=self.fast_clamp_route("mifepristone")
        )
        # Identical until the intervention starts ...
        for step in range(3):
            self.assertEqual(_biological(legacy[step]), _biological(clamped[step]))
        # ... and different from its first tick on.
        self.assertNotEqual(_biological(legacy[3]), _biological(clamped[3]))
        self.assertGreater(legacy[3].nodes_probtraj.iloc[0]["E_PGR"], 0.5)
        self.assertLess(clamped[3].nodes_probtraj.iloc[0]["E_PGR"], 0.01)


if __name__ == "__main__":
    unittest.main()
