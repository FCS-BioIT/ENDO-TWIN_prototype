from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import resolve_model
from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.simulation.runner import (
    protocol_continuation,
    run_cmaboss_condition,
    run_protocol,
)

MODEL_VERSION = "adoc-literature-superset-v0.3.0"


class SupersetModelRuntimeTest(unittest.TestCase):
    def test_superset_protocol_registry_separates_maternal_and_challenge_paths(
        self,
    ) -> None:
        for protocol_id in (
            "hormone_treated_mifepristone",
            "hormone_treated_anti_spp1",
        ):
            protocol = get_protocol(protocol_id, ROOT, model_version=MODEL_VERSION)
            step_inputs = protocol.steps[0].input_states
            self.assertFalse(step_inputs["IN_EMBRYO_PRESENT"])
            self.assertFalse(step_inputs["IN_TROPHECTODERM_COMPETENT"])
            self.assertFalse(step_inputs["IN_EMBRYO_CONTACT"])
        # v0.3.0 is an ARCHIVED superset and deliberately keeps the wiring it
        # was published with, bypass included. The maternal-perturbation repair
        # applies from v0.4.0 onward only -- see
        # `protocols.conditions.REPAIRED_FROM_SUPERSET_VERSION`. Applying it
        # here would not merely reinterpret an archived model, it would break
        # one: this family ships no `washout.cfg`, so seeding
        # `adhesion_challenge_washout` from `washout` would make a currently
        # runnable arm fail on a missing condition file.
        self.assertEqual(
            get_protocol(
                "adhesion_challenge_hormone_treated_mifepristone",
                ROOT,
                model_version=MODEL_VERSION,
            ).continuation_from,
            "hormone_treated_maternal",
        )
        self.assertEqual(
            get_protocol(
                "adhesion_challenge_hormone_treated_anti_spp1",
                ROOT,
                model_version=MODEL_VERSION,
            ).continuation_from,
            "hormone_treated_maternal",
        )
        self.assertEqual(
            get_protocol(
                "adhesion_challenge_washout", ROOT, model_version=MODEL_VERSION
            ).continuation_from,
            "adhesion_challenge_hormone_treated_anti_spp1",
        )

    def test_superset_protocols_run_through_main_runtime(self) -> None:
        maternal = run_protocol(
            "hormone_treated_maternal",
            model_version=MODEL_VERSION,
            root=ROOT,
            sample_count=1000,
        )
        challenge = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_hormone_treated",
                maternal,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=3000,
        )
        self.assertGreater(maternal.final_result.last["S_DECIDUALIZED"], 0.0)
        self.assertGreater(
            challenge.final_result.last["OUT_MATERNAL_ADHESION_COMPETENCE"], 0.0
        )
        self.assertIn("OUT_STABLE_ADHESION", challenge.final_result.last)

    def test_superset_continuation_changes_challenge_initialization(self) -> None:
        basal = run_protocol(
            "basal_maternal",
            model_version=MODEL_VERSION,
            root=ROOT,
            sample_count=300,
        )
        e2 = run_protocol(
            "e2_primed_maternal",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "e2_primed_maternal",
                basal,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=300,
        )
        ht_seq = run_protocol(
            "hormone_treated_maternal",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "hormone_treated_maternal",
                e2,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=300,
        )
        direct = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=MODEL_VERSION,
            root=ROOT,
            sample_count=1000,
        )
        continued = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_hormone_treated",
                ht_seq,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=1000,
        )
        self.assertIsNone(direct.step_initializations[0])
        self.assertIsNotNone(continued.step_initializations[0])
        self.assertGreater(len(continued.step_initializations[0].node_ids), 0)
        self.assertNotAlmostEqual(
            direct.final_result.last["OUT_EPITHELIAL_RECEPTIVE"],
            continued.final_result.last["OUT_EPITHELIAL_RECEPTIVE"],
            delta=1e-6,
        )

    def test_superset_expected_qualitative_directions_hold(self) -> None:
        maternal = run_protocol(
            "hormone_treated_maternal",
            model_version=MODEL_VERSION,
            root=ROOT,
            sample_count=3000,
        )
        ht = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_hormone_treated",
                maternal,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=3000,
        )
        maternal_mife = run_protocol(
            "hormone_treated_mifepristone",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "hormone_treated_mifepristone",
                maternal,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=3000,
        )
        mife = run_protocol(
            "adhesion_challenge_hormone_treated_mifepristone",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_hormone_treated_mifepristone",
                maternal,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=3000,
        )
        maternal_anti = run_protocol(
            "hormone_treated_anti_spp1",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "hormone_treated_anti_spp1",
                maternal,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=3000,
        )
        anti = run_protocol(
            "adhesion_challenge_hormone_treated_anti_spp1",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_hormone_treated_anti_spp1",
                maternal,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=3000,
        )
        embryo_absent = run_cmaboss_condition(
            model_version=MODEL_VERSION,
            condition_cfg=resolve_model(MODEL_VERSION, ROOT).condition_dir
            / "adhesion_challenge_hormone_treated.cfg",
            root=ROOT,
            override_texts=["IN_EMBRYO_PRESENT.istate = FALSE;"],
            sample_count=1000,
        )
        embryo_incompetent = run_cmaboss_condition(
            model_version=MODEL_VERSION,
            condition_cfg=resolve_model(MODEL_VERSION, ROOT).condition_dir
            / "adhesion_challenge_hormone_treated.cfg",
            root=ROOT,
            override_texts=["IN_TROPHECTODERM_COMPETENT.istate = FALSE;"],
            sample_count=1000,
        )
        stress = run_protocol(
            "adhesion_challenge_excess_er_stress",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_excess_er_stress",
                maternal,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=3000,
        )
        stiff = run_protocol(
            "adhesion_challenge_high_ecm_stiffness",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_high_ecm_stiffness",
                maternal,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=3000,
        )
        self.assertLess(
            maternal_mife.final_result.last["E_PGR"],
            maternal.final_result.last["E_PGR"],
        )
        self.assertLess(
            maternal_mife.final_result.last["S_PGR"],
            maternal.final_result.last["S_PGR"],
        )
        self.assertLess(
            maternal_anti.final_result.last["X_SPP1_LUMEN_FREE"],
            maternal.final_result.last["X_SPP1_LUMEN_FREE"],
        )
        self.assertLess(
            mife.final_result.last["E_PGR"],
            ht.final_result.last["E_PGR"],
        )
        self.assertLess(
            mife.final_result.last["S_PGR"],
            ht.final_result.last["S_PGR"],
        )
        self.assertLess(
            anti.final_result.last["X_ADHESION_ROUTE_SPP1"],
            ht.final_result.last["X_ADHESION_ROUTE_SPP1"],
        )
        self.assertGreater(
            anti.final_result.last["OUT_MATERNAL_ADHESION_COMPETENCE"], 0.0
        )
        self.assertEqual(embryo_absent.last["OUT_STABLE_ADHESION"], 0.0)
        self.assertEqual(embryo_incompetent.last["OUT_STABLE_ADHESION"], 0.0)
        self.assertLess(
            stress.final_result.last["X_MECHANICAL_PERMISSIVE_ECM"],
            ht.final_result.last["X_MECHANICAL_PERMISSIVE_ECM"],
        )
        self.assertLess(
            stiff.final_result.last["X_MECHANICAL_PERMISSIVE_ECM"],
            ht.final_result.last["X_MECHANICAL_PERMISSIVE_ECM"],
        )

    def test_bounded_extensions_are_executable(self) -> None:
        model = resolve_model(MODEL_VERSION, ROOT)
        default = run_cmaboss_condition(
            model_version=MODEL_VERSION,
            condition_cfg=model.condition_dir / "hormone_treated_maternal.cfg",
            root=ROOT,
            sample_count=500,
        )
        klf12 = run_cmaboss_condition(
            model_version=MODEL_VERSION,
            condition_cfg=model.condition_dir / "hormone_treated_maternal.cfg",
            root=ROOT,
            override_texts=["E_KLF12_HIGH.istate = TRUE;"],
            sample_count=500,
        )
        e2_primed = run_cmaboss_condition(
            model_version=MODEL_VERSION,
            condition_cfg=model.condition_dir / "e2_primed_maternal.cfg",
            root=ROOT,
            sample_count=500,
        )
        hormone_treated = run_cmaboss_condition(
            model_version=MODEL_VERSION,
            condition_cfg=model.condition_dir / "hormone_treated_maternal.cfg",
            root=ROOT,
            sample_count=500,
        )
        self.assertLess(klf12.last["E_LIF"], default.last["E_LIF"])
        self.assertGreater(
            e2_primed.last["S_FGF_MITOGENIC"],
            hormone_treated.last["S_FGF_MITOGENIC"],
        )
        self.assertGreaterEqual(
            e2_primed.last["E_ESTROGENIC_PROLIFERATION"],
            hormone_treated.last["E_ESTROGENIC_PROLIFERATION"],
        )


if __name__ == "__main__":
    unittest.main()
