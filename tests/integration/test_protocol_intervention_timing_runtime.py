"""Protocol-native intervention timing reproduces marker timing exactly.

Gate G11 of ``docs/protocol_intervention_timing.md``. Every run here goes through
the production ``run_protocol`` and ``protocol_continuation``, unpatched, against
a sandbox repository built by ``tests/fixtures/protocol_timing/sandbox.py``. The
committed ``config/protocols.yaml`` and ``config/protocols_markerless.yaml`` are
not edited.

The marker-timed schedules run on v0.5.2, the last version with legacy markers.
Every protocol that names the synthetic direct compound runs on v0.6.0, because
since Stage 4b a direct row needs an entity map and an expressivity artefact for
its version (``docs/stage4b_direct_admission.md`` §6.6); there its partners are
the migrated rows. Each protocol runs on the version whose file declares it.

Each historical schedule is re-expressed with its legacy marker ``OFF`` and the
equivalent named intervention declared only in the step(s) the marker was ``ON``.
It is then compared, phase by phase, with the canonical marker-driven lineage.
Identity is required on everything except the marker itself: the executed
network, the trajectories, the last-node marginals, the last-state distribution,
the continuation handed to the next phase, and the phase durations and cfgs.

The negative controls put the intervention in the wrong phase, or omit the
washout, and require the same comparison to fail.

No result is interpreted. A comparison shows that two encodings of one schedule
are one mechanism, or that a mistimed one is not.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.concordance.simulate import protocol_lineage
from dt_adoc.maboss_adapter import NODE_BLOCK_RE
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.engine import DIRECT_BASIS, InterventionError
from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.protocols.runner import expanded_protocol_sequence
from dt_adoc.simulation import runner

_spec = importlib.util.spec_from_file_location(
    "protocol_timing_sandbox", ROOT / "tests/fixtures/protocol_timing/sandbox.py"
)
sandbox = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sandbox)

MODEL_VERSION = sandbox.MODEL_VERSION
MARKERLESS = sandbox.MARKERLESS_VERSION
SEEDS = (1, 2, 3)
SAMPLE_COUNT = 500
VETO_SUFFIX = "and not 1"

#: Each historical schedule: the canonical terminal protocol, the marker that
#: times it today, and, for every phase from the first one the marker touches,
#: the named interventions that phase declares instead.
SCHEDULES: dict[str, tuple[str, str, dict[str, list[str]]]] = {
    "mifepristone": (
        "adhesion_challenge_hormone_treated_mifepristone",
        "IN_MIFEPRISTONE",
        {
            "hormone_treated_mifepristone": ["mifepristone"],
            "adhesion_challenge_hormone_treated_mifepristone": ["mifepristone"],
        },
    ),
    "anti_spp1": (
        "adhesion_challenge_hormone_treated_anti_spp1",
        "IN_ANTI_SPP1",
        {
            "hormone_treated_anti_spp1": ["anti_spp1"],
            "adhesion_challenge_hormone_treated_anti_spp1": ["anti_spp1"],
        },
    ),
    "hand2_loss": (
        "adhesion_challenge_hormone_treated_hand2_loss",
        "IN_HAND2_LOSS",
        {
            "hormone_treated_hand2_loss": ["hand2_loss"],
            "adhesion_challenge_hormone_treated_hand2_loss": ["hand2_loss"],
        },
    ),
    "washout": (
        "adhesion_challenge_washout",
        "IN_ANTI_SPP1",
        {
            "hormone_treated_anti_spp1": ["anti_spp1"],
            "washout": [],
            "adhesion_challenge_washout": [],
        },
    ),
}

#: Mistimed versions of the schedules above, which the comparison must reject.
NEGATIVE_CONTROLS: dict[str, tuple[str, str, dict[str, list[str]]]] = {
    # Mifepristone moved from the maternal exposure into the challenge only.
    "mifepristone_wrong_phase": (
        "adhesion_challenge_hormone_treated_mifepristone",
        "IN_MIFEPRISTONE",
        {
            "hormone_treated_mifepristone": [],
            "adhesion_challenge_hormone_treated_mifepristone": ["mifepristone"],
        },
    ),
    # The washout phase keeps anti-SPP1 active.
    "washout_omitted": (
        "adhesion_challenge_washout",
        "IN_ANTI_SPP1",
        {
            "hormone_treated_anti_spp1": ["anti_spp1"],
            "washout": ["anti_spp1"],
            "adhesion_challenge_washout": [],
        },
    ),
}


def _named(schedule: str, protocol_id: str) -> str:
    return f"{schedule}__{protocol_id}"


def _schedule_rows(
    schedules: dict[str, tuple[str, str, dict[str, list[str]]]],
) -> list[dict[str, Any]]:
    """One variant per phase of each schedule, marker OFF, names declared."""
    canonical = sandbox.canonical_rows()
    variants: list[dict[str, Any]] = []
    for name, (terminal, marker, declared) in schedules.items():
        for protocol_id in protocol_lineage(
            terminal, model_version=MODEL_VERSION, root=ROOT
        ):
            if protocol_id not in declared:
                continue
            base = canonical[protocol_id]
            parent = base.get("continuation_from")
            variants.append(
                sandbox.renamed(
                    base,
                    _named(name, protocol_id),
                    continuation_from=(
                        _named(name, parent) if parent in declared else parent
                    ),
                    steps=[
                        sandbox.step(
                            step,
                            step["step_id"],
                            step["relative_order"],
                            inputs={marker: False},
                            interventions=declared[protocol_id],
                        )
                        for step in base["steps"]
                    ],
                )
            )
    return variants


#: Interventions whose marker ``hormone_treated_anti_spp1.cfg`` sets ON. XAV939
#: is absent on purpose: its row has no executable effect, and Stage 4a accepts
#: naming it while its marker is on (``test_an_inert_member_leaves_a_combination
#: _unchanged``), so the runtime has nothing to apply twice. The parser still
#: refuses it when the step's own ``input_states`` sets the marker.
CFG_MARKERS = {"anti_spp1": "IN_ANTI_SPP1"}


def _three_step_rows() -> list[dict[str, Any]]:
    """One protocol per schedule, three steps on one cfg, timed inside the protocol.

    Built from ``hormone_treated_anti_spp1`` (its cfg and its parent), so the
    marker-timed version is a protocol the repository could have declared.
    """
    base = sandbox.canonical_rows()["hormone_treated_anti_spp1"]
    (template,) = base["steps"]

    def protocol(protocol_id: str, phases: list[tuple[bool, list[str] | None]]):
        return sandbox.renamed(
            base,
            protocol_id,
            steps=[
                sandbox.step(
                    template,
                    f"phase_{index + 1}",
                    index + 1,
                    inputs={"IN_ANTI_SPP1": marker},
                    interventions=names,
                )
                for index, (marker, names) in enumerate(phases)
            ],
        )

    return [
        protocol("three_step_marker", [(False, None), (True, None), (False, None)]),
        protocol(
            "three_step_named", [(False, []), (False, ["anti_spp1"]), (False, [])]
        ),
        protocol(
            "three_step_named_no_washout",
            [(False, []), (False, ["anti_spp1"]), (False, ["anti_spp1"])],
        ),
        # The marker is not set in input_states, so the cfg's istate = TRUE holds
        # and the parser cannot see it: the step must refuse at run time.
        *(
            sandbox.renamed(
                base,
                f"marker_from_cfg_and_named__{name}",
                steps=[
                    {
                        **sandbox.step(template, "phase_1", 1, interventions=[name]),
                        "input_states": {
                            k: v
                            for k, v in template["input_states"].items()
                            if k != marker
                        },
                    }
                ],
            )
            for name, marker in CFG_MARKERS.items()
        ),
    ]


def _markerless_three_step_rows() -> list[dict[str, Any]]:
    """The three-step protocols that name the synthetic direct compound.

    v0.6.0 rows, built from its own ``hormone_treated_anti_spp1`` (same cfg and
    parent), with no marker to set: the protocol alone times every compound.
    ``markerless_three_step_named`` is ``three_step_named`` on v0.6.0, for the
    caller-composition tests, which add the direct compound on top.
    """
    base = sandbox.markerless_rows()["hormone_treated_anti_spp1"]
    (template,) = base["steps"]

    def protocol(protocol_id: str, phases: list[list[str]]):
        return sandbox.renamed(
            base,
            protocol_id,
            steps=[
                sandbox.step(
                    template, f"phase_{index + 1}", index + 1, interventions=names
                )
                for index, names in enumerate(phases)
            ],
        )

    x = "synthetic_compound_x"
    return [
        protocol("markerless_three_step_named", [[], ["anti_spp1"], []]),
        protocol("three_step_markerless", [[], [x], []]),
        protocol("three_step_markerless_off", [[]] * 3),
        protocol("three_step_markerless_kept", [[], [x], [x]]),
        protocol("three_step_combination", [[], ["anti_spp1", x], ["mifepristone"]]),
        protocol(
            "three_step_combination_reordered",
            [[], [x, "anti_spp1"], ["mifepristone"]],
        ),
    ]


#: The protocols declared for v0.6.0, which therefore run there.
MARKERLESS_PROTOCOLS = frozenset(
    {row["protocol_id"] for row in _markerless_three_step_rows()}
)


def _without(result: runner.ConditionRunResult, marker: str) -> dict[str, Any]:
    """Everything a step reports, with only ``marker`` projected out."""
    traj = result.nodes_probtraj
    keep = [c for c in traj.columns if c != marker]
    last_states = result.last_states_probtraj.iloc[-1]
    projected: dict[frozenset[str], float] = {}
    for label in sorted(last_states.index):
        active = frozenset(
            token.strip()
            for token in str(label).split(" -- ")
            if token.strip() and token.strip() not in {"<nil>", marker}
        )
        projected[active] = projected.get(active, 0.0) + float(last_states[label])
    last_nodes = result.last_nodes_probtraj
    return {
        "times": list(traj.index),
        "columns": keep,
        "trajectory": traj[keep].to_numpy().tolist(),
        "last_nodes": last_nodes[[c for c in last_nodes.columns if c != marker]]
        .to_numpy()
        .tolist(),
        "last": {k: v for k, v in result.last.items() if k != marker},
        "last_states": {k: v for k, v in projected.items() if v != 0.0},
        "network_sha256": result.executed_network["network_sha256"],
        "logic_overrides": result.executed_network["logic_overrides"],
        "legacy_input_values": {
            k: v
            for k, v in result.executed_network["legacy_input_values"].items()
            if k != marker
        },
    }


def _initialisation(state: runner.ContinuationState | None, marker: str):
    """The continuation a step started from, with the marker's forced value out."""
    if state is None:
        return None
    return {
        "mode": state.mode,
        "method": state.continuation_method,
        "node_ids": state.node_ids,
        "distribution": state.distribution,
        "forced": {k: v for k, v in state.forced_nodes.items() if k != marker},
        "cutoff": state.probability_cutoff,
        "counts": (state.source_state_count, state.retained_state_count),
        "dropped": state.dropped_probability_mass,
        "policy": state.memory_node_policy,
    }


def _phase(run: runner.ProtocolRunResult, marker: str) -> list[dict[str, Any]]:
    return [
        {
            "outputs": _without(result, marker),
            "initialisation": _initialisation(state, marker),
        }
        for result, state in zip(run.step_results, run.step_initializations)
    ]


def _merged_cfg_difference(a: runner.ConditionRunResult, b: runner.ConditionRunResult):
    left = a.merged_cfg.read_text(encoding="utf-8").splitlines()
    right = b.merged_cfg.read_text(encoding="utf-8").splitlines()
    return sorted(set(left) - set(right)), sorted(set(right) - set(left))


def _vetoed(result: runner.ConditionRunResult) -> set[str]:
    return {
        node
        for node, logic in result.executed_network["logic_overrides"].items()
        if logic.endswith(VETO_SUFFIX)
    }


class _TimingSandbox(unittest.TestCase):
    """One sandbox per class, with every protocol run memoised per seed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = sandbox.build_sandbox(
            Path(cls._tmp.name),
            [
                *_schedule_rows(SCHEDULES),
                *_schedule_rows(NEGATIVE_CONTROLS),
                *_three_step_rows(),
            ],
            compounds=("synthetic_compound_x",),
            markerless_variants=_markerless_three_step_rows(),
        )
        cls._runs: dict[tuple[str, int], runner.ProtocolRunResult] = {}

    @classmethod
    def tearDownClass(cls) -> None:
        for run in cls._runs.values():
            run.release()
        cls._tmp.cleanup()

    @classmethod
    def run_protocol(
        cls, protocol_id: str, seed: int, model_version: str | None = None
    ) -> runner.ProtocolRunResult:
        """``protocol_id`` after its whole lineage, as ``run_arm`` chains it.

        On the version that declares it unless ``model_version`` says otherwise;
        its parents run on the same version.
        """
        version = model_version or (
            MARKERLESS if protocol_id in MARKERLESS_PROTOCOLS else MODEL_VERSION
        )
        key = (protocol_id, seed, version)
        if key not in cls._runs:
            protocol = get_protocol(protocol_id, cls.root, model_version=version)
            continuation = None
            if protocol.continuation_from is not None:
                continuation = runner.protocol_continuation(
                    protocol_id,
                    cls.run_protocol(protocol.continuation_from, seed, version),
                    model_version=version,
                    root=cls.root,
                )
            cls._runs[key] = runner.run_protocol(
                protocol_id,
                model_version=version,
                root=cls.root,
                continuation=continuation,
                seed=seed,
                sample_count=SAMPLE_COUNT,
            )
        return cls._runs[key]

    def lineage(self, terminal: str) -> list[str]:
        return protocol_lineage(terminal, model_version=MODEL_VERSION, root=self.root)

    def phases(
        self, schedule: str, table: dict[str, tuple[str, str, dict[str, list[str]]]]
    ) -> list[tuple[str, str]]:
        """``(canonical id, named id)`` for each phase of a schedule's lineage."""
        terminal, _, declared = table[schedule]
        return [
            (
                protocol_id,
                _named(schedule, protocol_id)
                if protocol_id in declared
                else protocol_id,
            )
            for protocol_id in self.lineage(terminal)
        ]

    def same_schedule(self, canonical: str, named: str, marker: str, seed: int) -> bool:
        a = self.run_protocol(canonical, seed)
        b = self.run_protocol(named, seed)
        return _phase(a, marker) == _phase(b, marker)


class MaterialisationTest(_TimingSandbox):
    def test_the_sandbox_protocols_are_the_canonical_ones(self) -> None:
        """Making the cloned protocols explicit changes no canonical definition."""
        from dt_adoc.protocols.conditions import protocol_definitions

        for version in (MODEL_VERSION, MARKERLESS):
            repository = protocol_definitions(ROOT, model_version=version)
            materialised = protocol_definitions(self.root, model_version=version)
            for protocol_id, definition in repository.items():
                with self.subTest(version=version, protocol=protocol_id):
                    self.assertEqual(materialised[protocol_id], definition)

    def test_the_sandbox_runs_the_repository_bit_for_bit(self) -> None:
        """A canonical lineage run in the sandbox is the repository's, byte for byte."""
        terminal = "adhesion_challenge_washout"
        lineage = protocol_lineage(terminal, model_version=MODEL_VERSION, root=ROOT)
        continuation = None
        for index, protocol_id in enumerate(lineage):
            with runner.run_protocol(
                protocol_id,
                model_version=MODEL_VERSION,
                root=ROOT,
                continuation=continuation,
                seed=SEEDS[0],
                sample_count=SAMPLE_COUNT,
            ) as repository:
                sandboxed = self.run_protocol(protocol_id, SEEDS[0])
                for a, b in zip(repository.step_results, sandboxed.step_results):
                    self.assertTrue(a.nodes_probtraj.equals(b.nodes_probtraj))
                    self.assertTrue(
                        a.last_states_probtraj.equals(b.last_states_probtraj)
                    )
                    self.assertEqual(
                        a.merged_cfg.read_text(encoding="utf-8"),
                        b.merged_cfg.read_text(encoding="utf-8"),
                    )
                    self.assertEqual(
                        a.executed_network["network_sha256"],
                        b.executed_network["network_sha256"],
                    )
                if index + 1 < len(lineage):
                    continuation = runner.protocol_continuation(
                        lineage[index + 1],
                        repository,
                        model_version=MODEL_VERSION,
                        root=ROOT,
                    )


class HistoricalScheduleEquivalenceTest(_TimingSandbox):
    """Mifepristone, anti-SPP1, HAND2 loss and the anti-SPP1 washout."""

    def test_each_schedule_is_reproduced_phase_by_phase(self) -> None:
        for schedule, (_, marker, declared) in SCHEDULES.items():
            phases = self.phases(schedule, SCHEDULES)
            for seed in SEEDS:
                for canonical, named in phases:
                    with self.subTest(schedule=schedule, seed=seed, phase=canonical):
                        self.assertTrue(
                            self.same_schedule(canonical, named, marker, seed)
                        )

    def test_the_two_encodings_differ_only_in_how_the_marker_is_set(self) -> None:
        """Byte-level account of what does differ: the marker's istate line, its
        recorded value, and the declared names. Nothing else."""
        for schedule, (_, marker, declared) in SCHEDULES.items():
            for canonical, named in self.phases(schedule, SCHEDULES):
                a = self.run_protocol(canonical, SEEDS[0])
                b = self.run_protocol(named, SEEDS[0])
                for left, right in zip(a.step_results, b.step_results):
                    with self.subTest(schedule=schedule, phase=canonical):
                        marker_on = left.executed_network["legacy_input_values"][marker]
                        self.assertFalse(
                            right.executed_network["legacy_input_values"][marker]
                        )
                        self.assertEqual(
                            _merged_cfg_difference(left, right),
                            (
                                (
                                    [f"{marker}.istate = TRUE;"],
                                    [f"{marker}.istate = FALSE;"],
                                )
                                if marker_on
                                else ([], [])
                            ),
                        )
                        # A step the marker drives is exactly a step that names it.
                        self.assertEqual(
                            bool(right.executed_network["named_interventions"]),
                            marker_on,
                        )
                        self.assertEqual(
                            left.executed_network["named_interventions"], []
                        )
                        self.assertEqual(
                            right.executed_network["network_sha256"],
                            left.executed_network["network_sha256"],
                        )

    def test_phase_boundaries_and_continuations_are_the_canonical_ones(self) -> None:
        keys = (
            "relative_order",
            "relative_duration",
            "condition_cfg",
            "continuation_mode",
            "continuation_memory_policy",
            "continuation_probability_cutoff",
        )
        for schedule, (terminal, _, declared) in SCHEDULES.items():
            with self.subTest(schedule=schedule):
                named_terminal = _named(schedule, terminal)
                canonical = expanded_protocol_sequence(
                    terminal, self.root, model_version=MODEL_VERSION
                )
                named = expanded_protocol_sequence(
                    named_terminal, self.root, model_version=MODEL_VERSION
                )
                self.assertEqual(
                    [{k: row[k] for k in keys} for row in canonical],
                    [{k: row[k] for k in keys} for row in named],
                )
                self.assertEqual(
                    [row.get("interventions", []) for row in named],
                    [
                        declared.get(row["protocol_id"].split("__")[-1], [])
                        for row in canonical
                    ],
                )

    def test_washout_removes_the_veto(self) -> None:
        """After washout the named schedule renders no veto, as the canonical one."""
        for seed in SEEDS:
            washout = self.run_protocol(_named("washout", "washout"), seed).final_result
            exposure = self.run_protocol(
                _named("washout", "hormone_treated_anti_spp1"), seed
            ).final_result
            self.assertIn("X_SPP1_LUMEN_FREE", _vetoed(exposure))
            self.assertEqual(_vetoed(washout), set())
            self.assertEqual(washout.executed_network["named_interventions"], [])


class NegativeControlTest(_TimingSandbox):
    """The comparison above is not vacuous: a mistimed schedule fails it."""

    def test_mifepristone_in_the_wrong_phase_is_detected(self) -> None:
        _, marker, _ = NEGATIVE_CONTROLS["mifepristone_wrong_phase"]
        phases = dict(self.phases("mifepristone_wrong_phase", NEGATIVE_CONTROLS))
        canonical = "hormone_treated_mifepristone"
        self.assertFalse(
            self.same_schedule(canonical, phases[canonical], marker, SEEDS[0])
        )

    def test_an_omitted_washout_is_detected(self) -> None:
        _, marker, _ = NEGATIVE_CONTROLS["washout_omitted"]
        phases = dict(self.phases("washout_omitted", NEGATIVE_CONTROLS))
        for protocol_id in ("washout", "adhesion_challenge_washout"):
            with self.subTest(phase=protocol_id):
                self.assertFalse(
                    self.same_schedule(
                        protocol_id, phases[protocol_id], marker, SEEDS[0]
                    )
                )
        # The exposure phase itself is correct in this control, so it still agrees.
        exposure = "hormone_treated_anti_spp1"
        self.assertTrue(
            self.same_schedule(exposure, phases[exposure], marker, SEEDS[0])
        )

    def test_a_washout_omitted_inside_one_protocol_is_detected(self) -> None:
        a = self.run_protocol("three_step_marker", SEEDS[0])
        b = self.run_protocol("three_step_named_no_washout", SEEDS[0])
        self.assertEqual(_phase(a, "IN_ANTI_SPP1")[:2], _phase(b, "IN_ANTI_SPP1")[:2])
        self.assertNotEqual(_phase(a, "IN_ANTI_SPP1")[2], _phase(b, "IN_ANTI_SPP1")[2])


class StepTimingInsideOneProtocolTest(_TimingSandbox):
    """Per-step resolution inside a single ``run_protocol`` call."""

    def test_named_steps_reproduce_marker_steps(self) -> None:
        for seed in SEEDS:
            with self.subTest(seed=seed):
                self.assertTrue(
                    self.same_schedule(
                        "three_step_marker", "three_step_named", "IN_ANTI_SPP1", seed
                    )
                )
        named = self.run_protocol("three_step_named", SEEDS[0])
        self.assertEqual(
            [r.executed_network["named_interventions"] for r in named.step_results],
            [[], ["anti_spp1"], []],
        )

    def test_a_markerless_intervention_switches_off_on_off(self) -> None:
        """No ``IN_*`` node for the compound exists, and the protocol alone times it."""
        canonical_text = resolve_model(MARKERLESS, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )
        nodes = [m.group(2) for m in NODE_BLOCK_RE.finditer(canonical_text)]
        self.assertFalse([n for n in nodes if "COMPOUND" in n or "SYNTHETIC" in n])
        for seed in SEEDS:
            with self.subTest(seed=seed):
                timed = self.run_protocol("three_step_markerless", seed).step_results
                off = self.run_protocol("three_step_markerless_off", seed).step_results
                kept = self.run_protocol(
                    "three_step_markerless_kept", seed
                ).step_results
                self.assertEqual(
                    [r.executed_network["named_interventions"] for r in timed],
                    [[], ["synthetic_compound_x"], []],
                )
                self.assertEqual(
                    [_vetoed(r) for r in timed], [set(), {"E_GP130_STAT3"}, set()]
                )
                # OFF: the first step is the never-treated protocol's, exactly.
                self.assertEqual(_without(timed[0], ""), _without(off[0], ""))
                # ON: the second step departs from it, and is the kept protocol's.
                self.assertNotEqual(_without(timed[1], ""), _without(off[1], ""))
                self.assertEqual(_without(timed[1], ""), _without(kept[1], ""))
                # OFF again: the third step renders the canonical network, and
                # differs from keeping the compound on.
                self.assertEqual(
                    timed[2].executed_network["network_sha256"],
                    off[2].executed_network["network_sha256"],
                )
                self.assertNotEqual(_without(timed[2], ""), _without(kept[2], ""))
                for result in timed:
                    self.assertEqual(
                        result.executed_network["source_network"]["sha256"],
                        sandbox.o8_sandbox.hashlib.sha256(
                            canonical_text.encode("utf-8")
                        ).hexdigest(),
                    )
                (effect,) = timed[1].executed_network["named_intervention_effects"]
                self.assertEqual(effect["mapping_basis"], DIRECT_BASIS)
                self.assertEqual(effect["legacy_input_node"], "")

    def test_combinations_compose_per_step_and_order_is_not_semantic(self) -> None:
        a = self.run_protocol("three_step_combination", SEEDS[0]).step_results
        b = self.run_protocol("three_step_combination_reordered", SEEDS[0]).step_results
        self.assertEqual(
            [_vetoed(r) for r in a],
            [set(), {"X_SPP1_LUMEN_FREE", "E_GP130_STAT3"}, {"E_PGR", "S_PGR"}],
        )
        self.assertEqual(
            [r.executed_network["named_interventions"] for r in a],
            [[], ["anti_spp1", "synthetic_compound_x"], ["mifepristone"]],
        )
        self.assertEqual(
            _phase(self.run_protocol("three_step_combination", SEEDS[0]), ""),
            _phase(self.run_protocol("three_step_combination_reordered", SEEDS[0]), ""),
        )
        self.assertEqual(
            [r.executed_network["named_interventions"] for r in a],
            [r.executed_network["named_interventions"] for r in b],
        )

    def test_a_marker_on_through_the_cfg_and_a_name_is_refused(self) -> None:
        """The parser sees only ``input_states``; the step itself refuses the rest."""
        parent = self.run_protocol("hormone_treated_maternal", SEEDS[0])
        for name, marker in CFG_MARKERS.items():
            protocol_id = f"marker_from_cfg_and_named__{name}"
            continuation = runner.protocol_continuation(
                protocol_id, parent, model_version=MODEL_VERSION, root=self.root
            )
            with (
                self.subTest(intervention=name),
                self.assertRaisesRegex(InterventionError, f"through {marker}"),
            ):
                runner.run_protocol(
                    protocol_id,
                    model_version=MODEL_VERSION,
                    root=self.root,
                    continuation=continuation,
                    seed=SEEDS[0],
                    sample_count=50,
                )


class CallerCompositionTest(_TimingSandbox):
    """Caller-supplied names are a union with the step's, never an override."""

    def test_caller_names_apply_to_every_step_on_top_of_the_declared_ones(self) -> None:
        protocol_id = "markerless_three_step_named"
        parent = self.run_protocol("hormone_treated_maternal", SEEDS[0], MARKERLESS)
        continuation = runner.protocol_continuation(
            protocol_id, parent, model_version=MARKERLESS, root=self.root
        )
        with runner.run_protocol(
            protocol_id,
            model_version=MARKERLESS,
            root=self.root,
            continuation=continuation,
            interventions=("synthetic_compound_x",),
            seed=SEEDS[0],
            sample_count=SAMPLE_COUNT,
        ) as run:
            self.assertEqual(
                [r.executed_network["named_interventions"] for r in run.step_results],
                [
                    ["synthetic_compound_x"],
                    ["anti_spp1", "synthetic_compound_x"],
                    ["synthetic_compound_x"],
                ],
            )
            self.assertEqual(
                [r.executed_network["intervention_timing"] for r in run.step_results],
                [
                    {
                        "protocol_id": protocol_id,
                        "step_id": f"phase_{i + 1}",
                        "step_index": i,
                        "protocol_declared": declared,
                        "caller_supplied": ["synthetic_compound_x"],
                    }
                    for i, declared in enumerate([[], ["anti_spp1"], []])
                ],
            )

    def test_a_name_both_declared_and_supplied_is_refused_before_any_step(self) -> None:
        with (
            mock.patch.object(
                runner, "run_cmaboss_condition", side_effect=AssertionError("ran")
            ),
            self.assertRaisesRegex(InterventionError, "already declares anti_spp1"),
        ):
            runner.run_protocol(
                "markerless_three_step_named",
                model_version=MARKERLESS,
                root=self.root,
                interventions=("anti_spp1",),
            )

    def test_a_caller_name_repeated_is_refused_before_any_step(self) -> None:
        with (
            mock.patch.object(
                runner, "run_cmaboss_condition", side_effect=AssertionError("ran")
            ),
            self.assertRaisesRegex(InterventionError, "named twice"),
        ):
            runner.run_protocol(
                "markerless_three_step_named",
                model_version=MARKERLESS,
                root=self.root,
                interventions=("synthetic_compound_x", "synthetic_compound_x"),
            )


class ObservationMapReReadTest(unittest.TestCase):
    """``simulate_constraint_protocols`` re-runs its terminal step outside
    ``run_protocol``; that re-read must run the step's declared names too."""

    def test_the_terminal_re_read_runs_the_declared_names(self) -> None:
        import json

        from dt_adoc.calibration.observation_map import simulate_constraint_protocols

        with tempfile.TemporaryDirectory() as tmp:
            root = sandbox.build_sandbox(
                Path(tmp), [], compounds=("synthetic_compound_x",)
            )
            # A direct compound runs on v0.6.0, whose rows are their own file.
            path = root / sandbox.MARKERLESS_PROTOCOLS
            payload = json.loads(path.read_text(encoding="utf-8"))
            (row,) = [
                r
                for r in payload["protocols"]
                if r["model_version"] == MARKERLESS
                and r["protocol_id"] == "hormone_treated_maternal"
            ]
            row["steps"][0]["interventions"] = ["synthetic_compound_x"]
            path.write_text(json.dumps(payload), encoding="utf-8")

            calls: list[tuple[str, ...]] = []
            real = runner.run_cmaboss_condition

            def recording(**kwargs):
                calls.append(tuple(kwargs.get("interventions", ())))
                return real(**kwargs)

            with mock.patch.object(runner, "run_cmaboss_condition", recording):
                simulate_constraint_protocols(
                    model_version=MARKERLESS, root=root, trajectory_count=100
                )
        # basal, e2-primed, hormone-treated through run_protocol, then the re-read.
        named = ("synthetic_compound_x",)
        self.assertEqual(calls, [(), (), named, named])


class TimingProvenanceTest(_TimingSandbox):
    def test_every_step_records_its_own_active_set(self) -> None:
        run = self.run_protocol("three_step_combination", SEEDS[0])
        for index, result in enumerate(run.step_results):
            record = result.executed_network
            with self.subTest(step=index):
                timing = record["intervention_timing"]
                self.assertEqual(timing["protocol_id"], "three_step_combination")
                self.assertEqual(timing["step_id"], f"phase_{index + 1}")
                self.assertEqual(timing["step_index"], index)
                self.assertEqual(
                    timing["protocol_declared"], record["named_interventions"]
                )
                self.assertEqual(timing["caller_supplied"], [])
                self.assertEqual(
                    sorted(
                        {
                            e["intervention_id"]
                            for e in record["named_intervention_effects"]
                        }
                    ),
                    record["named_interventions"],
                )
                for effect in record["named_intervention_effects"]:
                    for key in ("mapping_basis", "target_node", "mode", "evidence_ids"):
                        self.assertIn(key, effect)
                self.assertEqual(len(record["network_sha256"]), 64)

    def test_different_timing_gives_different_provenance(self) -> None:
        """Runs whose timing differs are distinguishable from their records alone,
        including the two encodings of one schedule, whose networks agree."""

        def records(protocol_id: str) -> list[dict[str, Any]]:
            return [
                {
                    k: r.executed_network.get(k)
                    for k in (
                        "intervention_timing",
                        "named_interventions",
                        "legacy_input_values",
                        "network_sha256",
                    )
                }
                for r in self.run_protocol(protocol_id, SEEDS[0]).step_results
            ]

        protocols = (
            "three_step_marker",
            "three_step_named",
            "three_step_named_no_washout",
            "three_step_markerless",
            "three_step_markerless_off",
            "three_step_markerless_kept",
        )
        seen = [
            [
                {
                    **row,
                    "intervention_timing": {
                        **row["intervention_timing"],
                        "protocol_id": "",
                    },
                }
                for row in records(protocol_id)
            ]
            for protocol_id in protocols
        ]
        for i in range(len(protocols)):
            for j in range(i + 1, len(protocols)):
                with self.subTest(a=protocols[i], b=protocols[j]):
                    self.assertNotEqual(seen[i], seen[j])


if __name__ == "__main__":
    unittest.main()
