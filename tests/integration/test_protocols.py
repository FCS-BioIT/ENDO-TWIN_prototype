from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.protocols.runner import protocol_sequence
from dt_adoc.simulation.runner import (
    build_condition_cfg,
    protocol_continuation,
    run_protocol,
)


class ProtocolIntegrationTest(unittest.TestCase):
    MODEL_VERSION = "adoc-core-v0.1.0"

    def test_protocol_sequence_order(self) -> None:
        sequence = protocol_sequence(
            "hormone_treated", ROOT, model_version=self.MODEL_VERSION
        )
        self.assertEqual([row["relative_order"] for row in sequence], [1])

    def test_maternal_protocols_keep_embryo_inputs_off(self) -> None:
        for protocol_id in [
            "basal",
            "e2_priming",
            "hormone_treated",
            "hormone_treated_mifepristone",
            "hormone_treated_anti_spp1",
            "washout",
        ]:
            step = get_protocol(
                protocol_id, ROOT, model_version=self.MODEL_VERSION
            ).steps[0]
            self.assertFalse(step.input_states["IN_EMBRYO_PRESENT"], protocol_id)
            self.assertFalse(
                step.input_states["IN_TROPHECTODERM_COMPETENT"], protocol_id
            )

    def test_adhesion_challenge_protocols_keep_embryo_inputs_on(self) -> None:
        for protocol_id in [
            "adhesion_challenge_basal",
            "adhesion_challenge_hormone_treated",
            "adhesion_challenge_hormone_treated_mifepristone",
            "adhesion_challenge_hormone_treated_anti_spp1",
            "adhesion_challenge_washout",
        ]:
            step = get_protocol(
                protocol_id, ROOT, model_version=self.MODEL_VERSION
            ).steps[0]
            self.assertTrue(step.input_states["IN_EMBRYO_PRESENT"], protocol_id)
            self.assertTrue(
                step.input_states["IN_TROPHECTODERM_COMPETENT"], protocol_id
            )

    def test_phase1b_declares_joint_continuation(self) -> None:
        for protocol_id in [
            "e2_priming",
            "hormone_treated",
            "hormone_treated_mifepristone",
            "hormone_treated_anti_spp1",
            "washout",
            "adhesion_challenge_basal",
            "adhesion_challenge_hormone_treated",
            "adhesion_challenge_hormone_treated_mifepristone",
            "adhesion_challenge_hormone_treated_anti_spp1",
            "adhesion_challenge_washout",
        ]:
            continuation = get_protocol(
                protocol_id,
                ROOT,
                model_version=self.MODEL_VERSION,
            ).continuation
            self.assertIsNotNone(continuation, protocol_id)
            self.assertEqual(continuation.mode, "joint", protocol_id)
            self.assertEqual(continuation.memory_policy, "all_non_inputs", protocol_id)

    def test_build_condition_cfg_overrides_baseline(self) -> None:
        protocol = get_protocol(
            "hormone_treated", ROOT, model_version=self.MODEL_VERSION
        )
        merged_cfg = build_condition_cfg(
            model_version=self.MODEL_VERSION,
            condition_cfg=ROOT / protocol.condition_cfg,
            root=ROOT,
            seed=7,
            sample_count=50,
        )
        text = merged_cfg.read_text(encoding="utf-8")
        self.assertIn("IN_PROGESTIN.istate = TRUE;", text)
        self.assertIn("seed_pseudorandom = 7;", text)
        self.assertIn("sample_count = 50;", text)

    def test_continuation_payload_changes_next_protocol_initialization(self) -> None:
        maternal_ht = run_protocol(
            "hormone_treated",
            model_version=self.MODEL_VERSION,
            root=ROOT,
            sample_count=200,
        )
        continuation = protocol_continuation(
            "adhesion_challenge_hormone_treated",
            maternal_ht,
            model_version=self.MODEL_VERSION,
            root=ROOT,
        )
        without_continuation = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=self.MODEL_VERSION,
            root=ROOT,
            sample_count=200,
        )
        with_continuation = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=self.MODEL_VERSION,
            root=ROOT,
            continuation=continuation,
            sample_count=200,
        )
        all_off_state = tuple(0 for _ in continuation.node_ids)
        self.assertNotEqual(
            continuation.distribution,
            {all_off_state: 1.0},
        )
        self.assertEqual(continuation.mode, "joint")
        self.assertEqual(continuation.continuation_method, "projected_joint_memory")
        self.assertGreater(len(continuation.node_ids), 3)
        self.assertTrue(continuation.forced_nodes["IN_EMBRYO_PRESENT"])
        self.assertGreater(
            with_continuation.final_result.last["OUT_STABLE_ADHESION"],
            without_continuation.final_result.last["OUT_STABLE_ADHESION"],
        )


if __name__ == "__main__":
    unittest.main()
