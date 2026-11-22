"""MaBoSS execution: protocol phases, intervention timing, carry-over and seeds."""

from __future__ import annotations

import csv
import itertools
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from endotwin.model import load_model, sha256_file
from endotwin.protocols import ProtocolError, forced_nodes, load_protocols
from endotwin.simulate import (
    SimulationSettings,
    phase_seed,
    simulate_condition,
)
from endotwin.structure import fixed_point

MODEL = load_model()
PROTOCOLS = load_protocols(MODEL)
FAST = SimulationSettings(sample_count=500, seed=3)
RESULTS = ROOT / "endotwin/results/endotwin-v0.2.0"


def run(condition_id, settings=FAST, variants=()):
    selection = MODEL.selection_from_ids(list(variants)) if variants else None
    return simulate_condition(
        MODEL,
        PROTOCOLS.conditions[condition_id],
        PROTOCOLS.interventions,
        selection,
        settings,
    )


class ProtocolDefinitions(unittest.TestCase):
    def test_unlisted_inputs_are_off_and_regimen_is_encoded(self):
        ref = PROTOCOLS.conditions["reference"]
        self.assertEqual(
            [p.phase_id for p in ref.phases],
            ["basal", "e2_priming", "differentiation_supplemented"],
        )
        self.assertEqual(ref.phases[0].inputs, {n: 0 for n in MODEL.inputs})
        self.assertEqual(
            ref.phase("differentiation_supplemented").inputs,
            {
                "IN_E2": 1,
                "IN_PROGESTIN": 1,
                "IN_cAMP": 1,
                "IN_XAV939": 1,
                "IN_BMPR_INHIBITOR": 0,
                "IN_SMO_INHIBITOR": 0,
                "IN_FOXO1_INHIBITOR": 0,
                "IN_IL1B": 0,
            },
        )

    def test_perturbations_appear_only_in_their_declared_phase(self):
        bmp = PROTOCOLS.conditions["bmpr_inhibition"]
        self.assertEqual([p.inputs["IN_BMPR_INHIBITOR"] for p in bmp.phases], [0, 0, 1])
        block = PROTOCOLS.conditions["paracrine_block_e2"]
        self.assertEqual(
            [p.interventions for p in block.phases], [(), ("paracrine_mitogen_block",)]
        )

    def test_unknown_input_is_refused(self):
        from endotwin.protocols import _phase

        with self.assertRaises(ProtocolError):
            _phase(
                MODEL,
                "x",
                {"inputs": {"IN_NOT_A_NODE": 1}},
                None,
                20.0,
                PROTOCOLS.interventions,
            )

    def test_comparisons_reference_existing_phases(self):
        for comp in PROTOCOLS.comparisons.values():
            PROTOCOLS.conditions[comp.control].phase(comp.phase)
            PROTOCOLS.conditions[comp.perturbed].phase(comp.phase_perturbed)


class InterventionTiming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = run("reference")
        cls.bmp = run("bmpr_inhibition")
        cls.kd = run("stromal_hand2_knockdown")

    def test_phases_before_the_perturbation_are_identical_to_control(self):
        for i in (0, 1):
            self.assertTrue(
                self.ref.phases[i].trajectory.equals(self.bmp.phases[i].trajectory)
            )
            self.assertTrue(
                self.ref.phases[i].trajectory.equals(self.kd.phases[i].trajectory)
            )

    def test_bmpr_inhibition_acts_only_after_its_onset(self):
        self.assertEqual(self.bmp.final("e2_priming")["S_BMP_SMAD"], 0.0)
        self.assertEqual(
            self.bmp.final("differentiation_supplemented")["S_BMP_SMAD"], 0.0
        )
        self.assertEqual(
            self.ref.final("differentiation_supplemented")["S_BMP_SMAD"], 1.0
        )

    def test_knockdown_has_a_dynamic_onset_and_raises_proliferation(self):
        traj = self.kd.phases[2].trajectory
        self.assertGreater(traj["OUT_EPITHELIAL_PROLIFERATION"].iloc[0], 0.9)
        self.assertEqual(self.kd.final("differentiation_supplemented")["S_HAND2"], 0.0)
        self.assertGreater(
            self.kd.final("differentiation_supplemented")[
                "OUT_EPITHELIAL_PROLIFERATION"
            ],
            0.95,
        )

    def test_state_is_carried_across_phase_boundaries(self):
        # Proliferation is ON at the end of E2 priming and must not restart from
        # OFF when the differentiation phase begins.
        end_e2 = self.ref.final("e2_priming")["OUT_EPITHELIAL_PROLIFERATION"]
        start_diff = (
            self.ref.phases[2].trajectory["OUT_EPITHELIAL_PROLIFERATION"].iloc[0]
        )
        self.assertGreater(end_e2, 0.99)
        self.assertGreater(start_diff, 0.95)

    def test_every_phase_converges(self):
        for result in (self.ref, self.bmp, self.kd):
            for phase in result.phases:
                self.assertTrue(phase.converged, (result.condition_id, phase.phase_id))


class Reproducibility(unittest.TestCase):
    def test_same_seed_gives_identical_trajectories(self):
        a = run("il1b_exposure")
        b = run("il1b_exposure")
        self.assertTrue(a.trajectory().equals(b.trajectory()))

    def test_phase_seeds_never_share_trajectories(self):
        s = SimulationSettings(sample_count=5000, seed=1)
        t = SimulationSettings(sample_count=5000, seed=2)
        seeds = [phase_seed(s, i) for i in range(3)] + [
            phase_seed(t, i) for i in range(3)
        ]
        gaps = sorted(seeds)
        self.assertTrue(all(b - a >= 5000 for a, b in itertools.pairwise(gaps)))

    def test_different_seeds_agree_at_the_fixed_point(self):
        a = run("reference", SimulationSettings(sample_count=500, seed=4))
        b = run("reference", SimulationSettings(sample_count=500, seed=5))
        self.assertFalse(a.trajectory().equals(b.trajectory()))
        self.assertEqual(
            a.final("differentiation_supplemented"),
            b.final("differentiation_supplemented"),
        )

    def test_provenance_records_settings_and_networks(self):
        prov = run("reference").provenance()
        self.assertEqual(prov["settings"]["sample_count"], 500)
        self.assertEqual(len(prov["phases"]), 3)
        self.assertTrue(all(len(p["network_sha256"]) == 64 for p in prov["phases"]))


class CommittedResults(unittest.TestCase):
    def test_run_manifest_matches_current_inputs(self):
        from endotwin.cli import input_digests

        manifest = json.loads((RESULTS / "run_manifest.json").read_text())
        self.assertEqual(manifest["inputs_sha256"], input_digests(MODEL))
        for name in manifest["outputs"]:
            self.assertTrue((RESULTS / name).is_file(), name)

    def test_committed_dynamics_end_at_the_exact_fixed_point_of_their_rules(self):
        tables = sorted(RESULTS.glob("dynamics_*.tsv"))
        self.assertGreaterEqual(len(tables), 6)
        for table in tables:
            condition_id, variant = table.stem.removeprefix("dynamics_").split("__")
            selection = MODEL.selection_from_ids(
                [] if variant == "default" else [variant]
            )
            last = PROTOCOLS.conditions[condition_id].phases[-1]
            exact = fixed_point(
                MODEL.rules_for(selection),
                last.inputs,
                forced_nodes(last, PROTOCOLS.interventions),
            )
            with table.open(newline="") as handle:
                final = list(csv.DictReader(handle, delimiter="\t"))[-1]
            self.assertEqual(final["phase_id"], last.phase_id, table.name)
            for node, value in exact.items():
                self.assertAlmostEqual(
                    float(final[node]), value, delta=0.02, msg=f"{table.name}: {node}"
                )

    def test_animation_matches_its_provenance_record(self):
        from PIL import Image

        gif = ROOT / "docs/assets/endotwin/endotwin_pathway_dynamics_v0.2.0.gif"
        sidecar = json.loads(
            gif.with_name(gif.stem + "_provenance.json").read_text(encoding="utf-8")
        )
        with Image.open(gif) as image:
            self.assertEqual(image.n_frames, sidecar["frames"])
        self.assertLess(gif.stat().st_size, 5_000_000)
        for tag in (
            "reference__default",
            "il1b_exposure__default",
            "il1b_exposure__INF_pgr_depletion",
        ):
            self.assertIn(
                f"endotwin/results/endotwin-v0.2.0/dynamics_{tag}.tsv",
                sidecar["inputs_sha256"],
            )

    def test_figure_sidecars_bind_current_inputs(self):
        for sidecar in sorted(
            (ROOT / "docs/assets/endotwin").glob("*_provenance.json")
        ):
            payload = json.loads(sidecar.read_text())
            self.assertTrue((ROOT / payload["figure"]).is_file())
            for path, digest in payload["inputs_sha256"].items():
                self.assertEqual(
                    sha256_file(ROOT / path), digest, f"{sidecar.name}: {path}"
                )

    def test_stochastic_confirmation_reached_the_exact_fixed_points(self):
        summary = json.loads((RESULTS / "maboss_confirmation_summary.json").read_text())
        self.assertEqual(summary["unconverged_phases"], 0)
        self.assertLessEqual(summary["max_abs_deviation_from_exact_fixed_point"], 0.02)

    def test_relay_example_is_a_transient_difference_only(self):
        summary = json.loads((RESULTS / "relay_transient_summary.json").read_text())
        self.assertEqual(
            summary["final_mean_relay"], summary["final_mean_relay_plus_direct"]
        )
        self.assertGreater(summary["area_between_curves_mean"], 0)
        self.assertEqual(
            summary["replicates_with_positive_area"], summary["replicates"]
        )

    def test_steady_state_directions_survived_random_rates(self):
        summary = json.loads((RESULTS / "rate_sensitivity_summary.json").read_text())
        self.assertEqual(summary["converged_agreement_fraction"], 1.0)


if __name__ == "__main__":
    unittest.main()
