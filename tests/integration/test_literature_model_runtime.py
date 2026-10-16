from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.maboss_adapter import render_network_with_logic_overrides
from dt_adoc.model.runtime import resolve_model, resolve_rule_variants
from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.simulation.runner import (
    build_condition_cfg,
    protocol_continuation,
    run_cmaboss_condition,
    run_protocol,
    run_structural_smoke,
)
from tests.unit.checkout_isolation import working_tree_copy

MODEL_VERSION = "adoc-literature-v0.2.0"


class LiteratureModelRuntimeTest(unittest.TestCase):
    def test_literature_perturbation_challenges_continue_from_maternal_ht(self) -> None:
        for protocol_id in (
            "adhesion_challenge_hormone_treated_mifepristone",
            "adhesion_challenge_hormone_treated_anti_spp1",
            "adhesion_challenge_excess_er_stress",
            "adhesion_challenge_high_ecm_stiffness",
        ):
            protocol = get_protocol(protocol_id, ROOT, model_version=MODEL_VERSION)
            self.assertEqual(protocol.continuation_from, "hormone_treated_maternal")

    def test_literature_protocols_run_through_main_runtime(self) -> None:
        maternal = run_protocol(
            "hormone_treated_maternal",
            model_version=MODEL_VERSION,
            root=ROOT,
            sample_count=200,
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
            sample_count=200,
        )
        self.assertGreater(maternal.final_result.last["OUT_EPITHELIAL_RECEPTIVE"], 0.0)
        self.assertGreater(challenge.final_result.last["E_CDH1_APICAL"], 0.0)
        self.assertIn("OUT_STABLE_ADHESION", challenge.final_result.last)

    def test_literature_sequential_phases_are_not_vacuous(self) -> None:
        ht_direct = run_protocol(
            "hormone_treated_maternal",
            model_version=MODEL_VERSION,
            root=ROOT,
            sample_count=200,
        )
        e2 = run_protocol(
            "e2_primed_maternal",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "e2_primed_maternal",
                run_protocol(
                    "basal_maternal",
                    model_version=MODEL_VERSION,
                    root=ROOT,
                    sample_count=200,
                ),
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=200,
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
            sample_count=200,
        )
        challenge_direct = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=MODEL_VERSION,
            root=ROOT,
            sample_count=200,
        )
        challenge_seq = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_hormone_treated",
                ht_seq,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=2000,
        )
        mife_seq = run_protocol(
            "adhesion_challenge_hormone_treated_mifepristone",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_hormone_treated_mifepristone",
                ht_seq,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=2000,
        )
        anti_seq = run_protocol(
            "adhesion_challenge_hormone_treated_anti_spp1",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_hormone_treated_anti_spp1",
                ht_seq,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=2000,
        )
        washout_seq = run_protocol(
            "adhesion_challenge_washout",
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_washout",
                anti_seq,
                model_version=MODEL_VERSION,
                root=ROOT,
            ),
            sample_count=200,
        )
        washout_direct = run_protocol(
            "adhesion_challenge_washout",
            model_version=MODEL_VERSION,
            root=ROOT,
            sample_count=200,
        )
        self.assertNotAlmostEqual(
            ht_seq.final_result.last["E_RECEPTIVE_SURFACE"],
            ht_direct.final_result.last["E_RECEPTIVE_SURFACE"],
            delta=1e-6,
        )
        self.assertGreater(
            challenge_seq.final_result.last["OUT_EPITHELIAL_RECEPTIVE"],
            challenge_direct.final_result.last["OUT_EPITHELIAL_RECEPTIVE"],
        )
        self.assertGreater(
            challenge_seq.final_result.last["OUT_MATERNAL_ADHESION_COMPETENCE"],
            0.0,
        )
        self.assertLess(
            mife_seq.final_result.last["OUT_MATERNAL_ADHESION_COMPETENCE"],
            challenge_seq.final_result.last["OUT_MATERNAL_ADHESION_COMPETENCE"],
        )
        self.assertLess(
            anti_seq.final_result.last["OUT_MATERNAL_ADHESION_COMPETENCE"],
            challenge_seq.final_result.last["OUT_MATERNAL_ADHESION_COMPETENCE"],
        )
        self.assertGreater(
            anti_seq.final_result.last["OUT_MATERNAL_ADHESION_COMPETENCE"],
            0.0,
        )
        self.assertGreater(
            washout_seq.final_result.last["OUT_EPITHELIAL_RECEPTIVE"],
            washout_direct.final_result.last["OUT_EPITHELIAL_RECEPTIVE"],
        )

    def test_literature_rule_variants_are_executable(self) -> None:
        challenge_default = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=MODEL_VERSION,
            root=ROOT,
            sample_count=200,
        )
        challenge_cdh1 = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=MODEL_VERSION,
            root=ROOT,
            rule_variant_selection={"cdh1": "maternal_receptive_state_dependent"},
            sample_count=200,
        )
        challenge_ihh = run_protocol(
            "adhesion_challenge_hormone_treated",
            model_version=MODEL_VERSION,
            root=ROOT,
            rule_variant_selection={"ihh": "strict_nr2f2_bmp2_hand2"},
            sample_count=200,
        )
        self.assertLessEqual(
            challenge_cdh1.final_result.last["OUT_STABLE_ADHESION"],
            challenge_default.final_result.last["OUT_STABLE_ADHESION"],
        )
        self.assertLessEqual(
            challenge_ihh.final_result.last["OUT_STROMAL_DECIDUALIZED"],
            challenge_default.final_result.last["OUT_STROMAL_DECIDUALIZED"],
        )

    def test_xav939_required_variant_changes_runtime_when_input_is_removed(
        self,
    ) -> None:
        model = resolve_model(MODEL_VERSION, ROOT)
        permissive = run_cmaboss_condition(
            model_version=MODEL_VERSION,
            condition_cfg=model.condition_dir / "hormone_treated_maternal.cfg",
            root=ROOT,
            override_texts=["IN_XAV939.istate = FALSE;"],
            sample_count=200,
        )
        required = run_cmaboss_condition(
            model_version=MODEL_VERSION,
            condition_cfg=model.condition_dir / "hormone_treated_maternal.cfg",
            root=ROOT,
            override_texts=["IN_XAV939.istate = FALSE;"],
            rule_variant_selection={"xav939": "required"},
            sample_count=200,
        )
        self.assertGreater(
            permissive.last["E_SECRETORY_STATE"],
            required.last["E_SECRETORY_STATE"],
        )

    def test_model_specific_cfg_selection_uses_extended_baseline(self) -> None:
        model = resolve_model(MODEL_VERSION, ROOT)
        merged_cfg = build_condition_cfg(
            model_version=MODEL_VERSION,
            condition_cfg=model.condition_dir / "hormone_treated_maternal.cfg",
            root=ROOT,
            seed=7,
            sample_count=50,
        )
        text = merged_cfg.read_text(encoding="utf-8")
        self.assertIn("IN_EMBRYO_CONTACT.istate = FALSE;", text)
        self.assertEqual(
            merged_cfg.read_text(encoding="utf-8").count("sample_count = 50;"), 1
        )

    def test_literature_smoke_records_model_version_and_calibration_roles(self) -> None:
        # The smoke writes under its root; run it on a copy, not the checkout.
        work = working_tree_copy(Path(self.enterContext(tempfile.TemporaryDirectory())))
        output_root = run_structural_smoke(
            run_id="phase1c-lit-smoke-fixture",
            model_version=MODEL_VERSION,
            root=work,
        )
        manifest = json.loads((output_root / "run_manifest.json").read_text())
        self.assertEqual(manifest["model"]["model_version"], MODEL_VERSION)
        # One executed-network record per phase. The intervention library does
        # not cover this model, so the only overrides are its default rule
        # variants, and each record rebuilds the network that was executed.
        model_text = resolve_model(MODEL_VERSION, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )
        _, variant_overrides = resolve_rule_variants(
            model_version=MODEL_VERSION, root=ROOT
        )
        executed = manifest["model"]["executed_networks"]
        phases = manifest["simulation"]["continuation"]["protocol_initializations"]
        self.assertEqual(len(executed), len(phases))
        for row in executed:
            self.assertEqual(
                row["logic_overrides"], dict(sorted(variant_overrides.items()))
            )
            rebuilt = render_network_with_logic_overrides(
                model_text, logic_overrides=row["logic_overrides"]
            )
            self.assertEqual(
                row["network_sha256"],
                hashlib.sha256(rebuilt.encode("utf-8")).hexdigest(),
            )
            self.assertEqual(
                row["intervention_library"]["path"], "config/intervention_library.tsv"
            )
        summary_lines = (
            (output_root / "tables" / "adhesion_calibration_summary.tsv")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        self.assertEqual(len(summary_lines), 2)
        calibration_lines = (
            (output_root / "tables" / "adhesion_calibration.tsv")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        self.assertGreaterEqual(len(calibration_lines), 2)
        self.assertIn("used_for_fitting", calibration_lines[0])


if __name__ == "__main__":
    unittest.main()
