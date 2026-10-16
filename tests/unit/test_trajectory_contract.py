"""Unit contracts for the full node-probability trajectory output layer.

These tests use synthetic trajectories so they run without a MaBoSS runtime.
The matching runtime assertions live in
``tests/integration/test_trajectory_runtime.py``.
"""

from __future__ import annotations

import sys
import unittest
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd

from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.simulation.runner import nodes_probtraj_table
from dt_adoc.simulation.timeline import (
    DEFAULT_TERMINAL_PROTOCOL,
    _validate_timeline_frame,
    phase_label,
    reference_sequence,
    resolved_input_states,
)


def synthetic_probtraj() -> pd.DataFrame:
    return pd.DataFrame(
        {"E_PGR": [0.0, 0.4, 0.9], "OUT_STABLE_ADHESION": [0.0, 0.1, 0.25]},
        index=[0.0, 0.1, 0.2],
    )


class NodesProbtrajTableTest(unittest.TestCase):
    def test_table_carries_time_and_phase_context(self) -> None:
        table = nodes_probtraj_table(
            synthetic_probtraj(),
            protocol_id="hormone_treated_maternal",
            step_id="hormone_treated_maternal",
            phase_index=2,
        )
        self.assertEqual(
            list(table.columns[:4]),
            ["time", "protocol_id", "step_id", "phase_index"],
        )
        self.assertEqual(table["time"].tolist(), [0.0, 0.1, 0.2])
        self.assertEqual(set(table["protocol_id"]), {"hormone_treated_maternal"})
        self.assertEqual(set(table["phase_index"]), {2})

    def test_table_has_more_than_one_time_row(self) -> None:
        table = nodes_probtraj_table(
            synthetic_probtraj(),
            protocol_id="basal_maternal",
            step_id="basal_maternal",
            phase_index=0,
        )
        self.assertGreater(len(table), 1)

    def test_table_preserves_node_values_exactly(self) -> None:
        source = synthetic_probtraj()
        table = nodes_probtraj_table(
            source,
            protocol_id="basal_maternal",
            step_id="basal_maternal",
            phase_index=0,
        )
        self.assertEqual(table["E_PGR"].tolist(), source["E_PGR"].tolist())

    def test_missing_trajectory_raises(self) -> None:
        with self.assertRaises(ValueError):
            nodes_probtraj_table(
                None,
                protocol_id="basal_maternal",
                step_id="basal_maternal",
                phase_index=0,
            )

    def test_shaping_does_not_mutate_the_source(self) -> None:
        source = synthetic_probtraj()
        before = list(source.columns)
        nodes_probtraj_table(
            source,
            protocol_id="basal_maternal",
            step_id="basal_maternal",
            phase_index=0,
        )
        self.assertEqual(list(source.columns), before)


class TimelineFrameValidationTest(unittest.TestCase):
    def frame(self, times: list[float], values: list[float]) -> pd.DataFrame:
        return pd.DataFrame({"global_time": times, "E_PGR": values})

    def test_monotonic_frame_passes(self) -> None:
        _validate_timeline_frame(
            self.frame([0.0, 0.1, 0.2], [0.0, 0.5, 1.0]),
            node_ids=("E_PGR",),
        )

    def test_non_monotonic_global_time_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _validate_timeline_frame(
                self.frame([0.0, 0.3, 0.2], [0.0, 0.5, 1.0]),
                node_ids=("E_PGR",),
            )

    def test_probability_above_one_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _validate_timeline_frame(
                self.frame([0.0, 0.1, 0.2], [0.0, 0.5, 1.4]),
                node_ids=("E_PGR",),
            )

    def test_negative_probability_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _validate_timeline_frame(
                self.frame([0.0, 0.1, 0.2], [-0.2, 0.5, 1.0]),
                node_ids=("E_PGR",),
            )

    def test_non_finite_probability_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _validate_timeline_frame(
                self.frame([0.0, 0.1, 0.2], [0.0, float("nan"), 1.0]),
                node_ids=("E_PGR",),
            )

    def test_empty_frame_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _validate_timeline_frame(
                pd.DataFrame({"global_time": [], "E_PGR": []}),
                node_ids=("E_PGR",),
            )


class ReferenceSequenceTest(unittest.TestCase):
    def test_literature_lineage_is_the_declared_continuation_chain(self) -> None:
        sequence = reference_sequence(
            model_version="adoc-literature-v0.2.0",
            root=ROOT,
        )
        self.assertEqual(
            sequence,
            (
                "basal_maternal",
                "e2_primed_maternal",
                "hormone_treated_maternal",
                "adhesion_challenge_hormone_treated_anti_spp1",
                "adhesion_challenge_washout",
            ),
        )

    def test_core_lineage_is_the_declared_continuation_chain(self) -> None:
        sequence = reference_sequence(
            model_version="adoc-core-v0.1.0",
            root=ROOT,
        )
        self.assertEqual(
            sequence,
            (
                "basal",
                "e2_priming",
                "hormone_treated",
                "hormone_treated_anti_spp1",
                "washout",
                "adhesion_challenge_washout",
            ),
        )

    def test_every_link_matches_the_declared_continuation_from(self) -> None:
        for model_version in ("adoc-core-v0.1.0", "adoc-literature-v0.2.0"):
            sequence = reference_sequence(model_version=model_version, root=ROOT)
            for previous, current in pairwise(sequence):
                protocol = get_protocol(current, ROOT, model_version=model_version)
                self.assertEqual(
                    protocol.continuation_from,
                    previous,
                    f"{model_version}: {current} does not continue from {previous}",
                )

    def test_default_terminal_protocol_exists_in_both_models(self) -> None:
        for model_version in ("adoc-core-v0.1.0", "adoc-literature-v0.2.0"):
            protocol = get_protocol(
                DEFAULT_TERMINAL_PROTOCOL, ROOT, model_version=model_version
            )
            self.assertEqual(protocol.protocol_id, DEFAULT_TERMINAL_PROTOCOL)


class ResolvedInputStateTest(unittest.TestCase):
    def resolve(self, protocol_id: str) -> dict[str, bool]:
        protocol = get_protocol(
            protocol_id, ROOT, model_version="adoc-literature-v0.2.0"
        )
        return resolved_input_states(protocol, protocol.steps[0], root=ROOT)

    def test_basal_has_every_input_off(self) -> None:
        states = self.resolve("basal_maternal")
        self.assertTrue(states)
        self.assertFalse(any(states.values()))

    def test_e2_priming_turns_on_only_e2(self) -> None:
        states = self.resolve("e2_primed_maternal")
        self.assertTrue(states["IN_E2"])
        self.assertEqual({node for node, value in states.items() if value}, {"IN_E2"})

    def test_hormone_conditioning_matches_the_published_protocol(self) -> None:
        states = self.resolve("hormone_treated_maternal")
        self.assertEqual(
            {node for node, value in states.items() if value},
            {"IN_E2", "IN_PROGESTIN", "IN_cAMP", "IN_XAV939"},
        )

    def test_anti_spp1_challenge_adds_the_antibody_and_embryo_inputs(self) -> None:
        states = self.resolve("adhesion_challenge_hormone_treated_anti_spp1")
        self.assertTrue(states["IN_ANTI_SPP1"])
        self.assertTrue(states["IN_EMBRYO_PRESENT"])
        self.assertTrue(states["IN_EMBRYO_CONTACT"])

    def test_step_overrides_win_over_the_condition_cfg(self) -> None:
        protocol = get_protocol(
            "adhesion_challenge_hormone_treated_anti_spp1",
            ROOT,
            model_version="adoc-literature-v0.2.0",
        )
        states = resolved_input_states(protocol, protocol.steps[0], root=ROOT)
        for node_id, value in protocol.steps[0].input_states.items():
            self.assertEqual(states[node_id], bool(value))

    def test_only_input_nodes_are_reported(self) -> None:
        states = self.resolve("hormone_treated_maternal")
        self.assertTrue(all(node.startswith("IN_") for node in states))


class PhaseLabelTest(unittest.TestCase):
    def test_known_protocols_get_curated_labels(self) -> None:
        self.assertEqual(phase_label("basal_maternal"), "Basal maternal state")
        self.assertEqual(phase_label("e2_primed_maternal"), "E2 priming")
        self.assertEqual(
            phase_label("hormone_treated_maternal"), "Hormone conditioning"
        )

    def test_unknown_protocol_falls_back_without_raising(self) -> None:
        self.assertEqual(phase_label("some_new_protocol"), "Some new protocol")

    def test_labels_never_mention_hours_or_concentration(self) -> None:
        from dt_adoc.simulation.timeline import _PHASE_LABEL_OVERRIDES

        banned = ("hour", "hr", "concentration", "µm", "ng/ml", "nm ")
        for label in _PHASE_LABEL_OVERRIDES.values():
            lowered = label.lower()
            for term in banned:
                self.assertNotIn(term, lowered, f"{label} leaks {term!r}")


if __name__ == "__main__":
    unittest.main()


class ContinuationInputPrecedenceTest(unittest.TestCase):
    """A joint continuation re-pins protocol inputs after the merged cfg.

    Discovered while perturbing IN_XAV939 during curation increment 1: a cfg
    input override was silently reverted by the continuation's forced_nodes,
    making the perturbation look inert. Production code is unaffected because
    run_protocol derives both from the same step.input_states, but perturbation
    studies must go through continuation_with_input_overrides.
    """

    def continuation(self) -> object:
        from dt_adoc.simulation.runner import ContinuationState

        return ContinuationState(
            mode="joint",
            continuation_method="projected_joint_memory",
            node_ids=("A", "B"),
            distribution={(0, 1): 1.0},
            forced_nodes={"IN_XAV939": True, "IN_E2": True},
        )

    def test_override_replaces_only_the_named_input(self) -> None:
        from dt_adoc.simulation.runner import continuation_with_input_overrides

        updated = continuation_with_input_overrides(
            self.continuation(), {"IN_XAV939": False}
        )
        self.assertFalse(updated.forced_nodes["IN_XAV939"])
        self.assertTrue(updated.forced_nodes["IN_E2"], "unrelated inputs must survive")

    def test_original_continuation_is_not_mutated(self) -> None:
        from dt_adoc.simulation.runner import continuation_with_input_overrides

        original = self.continuation()
        continuation_with_input_overrides(original, {"IN_XAV939": False})
        self.assertTrue(
            original.forced_nodes["IN_XAV939"],
            "the helper must not mutate the continuation it was given",
        )

    def test_distribution_and_memory_nodes_are_preserved(self) -> None:
        from dt_adoc.simulation.runner import continuation_with_input_overrides

        original = self.continuation()
        updated = continuation_with_input_overrides(original, {"IN_XAV939": False})
        self.assertEqual(updated.node_ids, original.node_ids)
        self.assertEqual(updated.distribution, original.distribution)
        self.assertEqual(updated.mode, original.mode)
