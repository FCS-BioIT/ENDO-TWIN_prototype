"""The perturbation-cascade tool on the real v0.6.0 model, with few trajectories.

These check what the tool guarantees by construction: pairing, the perturbation
boundary, inherited interventions, reproducibility and provenance. The
withdrawal-versus-mifepristone comparison is a scientific diagnostic run by
``docs/perturbation_cascade``; here only its effective-logic premise is tested.
"""

from __future__ import annotations

import itertools
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.cascade.run import CascadeRequest, run_cascade
from dt_adoc.cascade.simulate import (
    PhaseSettings,
    StartSettings,
    arms_for,
    build_starting_ensemble,
    run_arm,
    sample_initial_states,
    trajectory_seeds,
)
from dt_adoc.perturbations.engine import _evaluable, _value
from dt_adoc.perturbations.spec import parse_spec

MV = "adoc-literature-superset-v0.6.0"
FAST_START = StartSettings(init_horizon=25.0, lineage_trajectories=500)
PHASE = PhaseSettings(horizon=25.0, tick=0.01)


def spec(**kw):
    payload = {"name": "t", "model_version": MV, "start": "hormone_treated_maternal"}
    payload.update(kw)
    return parse_spec(payload)


class CascadeRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.withdrawal = spec(input_changes={"IN_PROGESTIN": False})
        cls.ensemble = build_starting_ensemble(cls.withdrawal, FAST_START)
        cls.states = sample_initial_states(cls.ensemble, 8, 11)
        cls.seeds = trajectory_seeds(11, 8)

    def test_seeds_are_distinct_and_not_consecutive(self):
        seeds = trajectory_seeds(11, 2000)
        self.assertEqual(len(set(seeds.tolist())), 2000)
        self.assertFalse(any(b - a == 1 for a, b in itertools.pairwise(sorted(seeds))))

    def test_arms_are_paired_and_start_at_the_boundary(self):
        perturbed, control = arms_for(self.withdrawal, self.ensemble)
        self.assertEqual(perturbed.input_states["IN_PROGESTIN"], False)
        self.assertEqual(control.input_states["IN_PROGESTIN"], True)
        diff = {
            k
            for k in perturbed.input_states
            if perturbed.input_states[k] != control.input_states[k]
        }
        self.assertEqual(diff, {"IN_PROGESTIN"})
        p = run_arm(
            self.ensemble, perturbed, self.states, self.seeds, PHASE, workers=1
        ).events
        c = run_arm(
            self.ensemble, control, self.states, self.seeds, PHASE, workers=1
        ).events
        key = ["trajectory", "node"]
        j = p.merge(c, on=key, suffixes=("_p", "_c"))
        self.assertEqual(len(j), len(p))
        self.assertTrue((j.seed_p == j.seed_c).all())
        self.assertTrue((j.initial_p == j.initial_c).all())
        # Every carried node starts exactly in the sampled state.
        nodes = self.ensemble.continuation.node_ids
        for k in range(len(self.seeds)):
            sampled = dict(zip(nodes, self.states[k].tolist()))
            got = p[p.trajectory == k].set_index("node").initial
            for node, value in sampled.items():
                self.assertEqual(int(got[node]), value, (k, node))

    def test_start_protocol_interventions_stay_active_in_both_arms(self):
        s = spec(
            start="hormone_treated_hand2_loss", input_changes={"IN_PROGESTIN": False}
        )
        ensemble = build_starting_ensemble(s, FAST_START)
        perturbed, control = arms_for(s, ensemble)
        self.assertEqual(control.interventions, ("hand2_loss",))
        self.assertEqual(perturbed.interventions, ("hand2_loss",))
        r = run_arm(
            ensemble,
            control,
            sample_initial_states(ensemble, 2, 3),
            trajectory_seeds(3, 2),
            PHASE,
            workers=1,
        )
        self.assertEqual(r.executed_network["named_interventions"], ["hand2_loss"])

    def test_mifepristone_and_withdrawal_have_the_same_effective_pgr_logic(self):
        mife = spec(interventions=["mifepristone"])
        wd = run_arm(
            self.ensemble,
            arms_for(self.withdrawal, self.ensemble)[0],
            self.states[:1],
            self.seeds[:1],
            PHASE,
            workers=1,
        )
        mf = run_arm(
            self.ensemble,
            arms_for(mife, self.ensemble)[0],
            self.states[:1],
            self.seeds[:1],
            PHASE,
            workers=1,
        )
        self.assertEqual(
            sorted(mf.executed_network["intervention_overrides"]), ["E_PGR", "S_PGR"]
        )
        self.assertNotEqual(
            wd.executed_network["network_sha256"], mf.executed_network["network_sha256"]
        )
        for node in ("E_PGR", "S_PGR"):
            expr_mf, names = _evaluable(mf.executed_network["logic_overrides"][node])
            # Under mifepristone IN_PROGESTIN stays ON; under withdrawal it is OFF.
            for values in itertools.product([False, True], repeat=len(names)):
                assignment = dict(zip(sorted(names), values))
                assignment["IN_PROGESTIN"] = True
                self.assertFalse(_value(expr_mf, assignment))
            self.assertEqual(names, {"IN_PROGESTIN"})

    def test_a_truncated_window_set_is_refused_at_run_time(self):
        # Bypass the PhaseSettings check: 0.3 / 0.1 makes MaBoSS stop at 0.2.
        phase = PhaseSettings(horizon=1.0, tick=0.1)
        object.__setattr__(phase, "horizon", 0.3)
        perturbed, _ = arms_for(self.withdrawal, self.ensemble)
        with self.assertRaisesRegex(RuntimeError, "returned 2 windows"):
            run_arm(
                self.ensemble,
                perturbed,
                self.states[:1],
                self.seeds[:1],
                phase,
                workers=1,
            )

    def test_bundle_is_reproducible_and_worker_invariant(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            a = run_cascade(
                CascadeRequest(
                    self.withdrawal,
                    n_trajectories=6,
                    master_seed=5,
                    start=FAST_START,
                    workers=1,
                    run_id="a",
                ),
                out_root=out,
            )
            b = run_cascade(
                CascadeRequest(
                    self.withdrawal,
                    n_trajectories=6,
                    master_seed=5,
                    start=FAST_START,
                    workers=3,
                    run_id="b",
                ),
                out_root=out,
            )
            ea, eb = (pd.read_csv(x / "events.tsv", sep="\t") for x in (a, b))
            pd.testing.assert_frame_equal(ea, eb)
            meta = json.loads((a / "metadata.json").read_text())
            for key in (
                "source_commit",
                "claims",
                "perturbation",
                "model",
                "starting_state",
                "arms",
                "simulation",
                "event_definition",
                "positions",
                "software",
                "outputs",
            ):
                self.assertIn(key, meta)
            self.assertEqual(
                meta["perturbation"]["provenance_classes"], ["protocol_input_change"]
            )
            self.assertFalse(meta["claims"]["experimentally_validated"])
            # The default start is a fixed point: a stationary control, no warning.
            self.assertTrue(meta["diagnostics"]["control_stationary"])
            self.assertEqual(meta["warnings"], [])
            self.assertEqual(
                meta["validation_level"]["level"], "exploratory_model_internal"
            )
            self.assertEqual(
                meta["claim_ceiling"]["ceiling"], meta["claims"]["result_kind"]
            )
            # Every lineage phase names the condition cfg it ran with, by content.
            for phase in meta["starting_state"]["lineage_phases"]:
                self.assertTrue(phase["condition_cfg"]["sha256"], phase["protocol_id"])
            recorded = {f["path"] for f in meta["implementation_files"]}
            self.assertIn("src/dt_adoc/maboss_adapter.py", recorded)
            self.assertIn("src/dt_adoc/simulation/runner.py", recorded)
            self.assertFalse(meta["claims"]["screenability_claim"])
            self.assertEqual(
                meta["starting_state"]["lineage"],
                ["basal_maternal", "e2_primed_maternal", "hormone_treated_maternal"],
            )
            self.assertIn("cmaboss", meta["software"])
            nodes = ea.node.nunique()
            self.assertEqual(
                len(ea), 2 * 6 * nodes
            )  # every node of every trajectory of both arms
            summary = pd.read_csv(a / "node_summary.tsv", sep="\t")
            self.assertEqual(
                set(summary[summary.arm == "perturbed"].node), set(ea.node)
            )
            for name in (
                "cascade.png",
                "cascade.svg",
                "cascade.pdf",
                "pairwise_precedence.tsv",
                "control_comparison.tsv",
            ):
                self.assertTrue((a / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()


OPENED_FILES_PROBE = """
import json, os, sys, tempfile
from pathlib import Path
root = Path(sys.argv[1]).resolve()
opened = set()
def hook(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        try:
            path = Path(os.fsdecode(args[0])).resolve()
        except (OSError, ValueError):
            return
        if path.is_relative_to(root) and path.is_file():
            opened.add(path.relative_to(root).as_posix())
sys.addaudithook(hook)
from dt_adoc.cascade.run import CascadeRequest, run_cascade
from dt_adoc.cascade.simulate import StartSettings
from dt_adoc.perturbations.spec import parse_spec
spec = parse_spec({"name": "t", "model_version": "adoc-literature-superset-v0.6.0",
                   "start": "hormone_treated_maternal", "input_changes": {"IN_PROGESTIN": False}})
with tempfile.TemporaryDirectory() as tmp:
    bundle = run_cascade(CascadeRequest(spec, n_trajectories=4, master_seed=5,
        start=StartSettings(init_horizon=25.0, lineage_trajectories=200), workers=1,
        run_id="probe"), out_root=Path(tmp))
    meta = json.loads((bundle / "metadata.json").read_text())
recorded = {f["path"] for f in meta["implementation_files"] + meta["configuration_files"]}
for source in meta["annotation_sources"].values() if isinstance(meta["annotation_sources"], dict) else meta["annotation_sources"]:
    if isinstance(source, dict) and "path" in source:
        recorded.add(source["path"])
print(json.dumps(sorted(p for p in opened - recorded
                        if not p.startswith(".pixi/") and not p.endswith(".pyc"))))
"""


class EveryOpenedInputIsRecordedRuntimeTests(unittest.TestCase):
    def test_every_repository_file_a_run_opens_is_in_its_record(self):
        import subprocess

        result = subprocess.run(
            [sys.executable, "-B", "-c", OPENED_FILES_PROBE, str(ROOT)],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(SRC)},
            capture_output=True,
            text=True,
            check=True,
        )
        unrecorded = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(unrecorded, [], "opened by the run but not content-pinned")


class LateEntryDuringOverwriteRuntimeTests(unittest.TestCase):
    def test_a_late_entry_in_the_replaced_bundle_keeps_the_new_bundle(self):
        from unittest import mock

        from dt_adoc.cascade import run as run_module

        withdrawal = spec(input_changes={"IN_PROGESTIN": False})

        def request():
            return CascadeRequest(
                withdrawal,
                n_trajectories=4,
                master_seed=5,
                start=FAST_START,
                workers=1,
                run_id="late",
                overwrite=True,
            )

        with tempfile.TemporaryDirectory() as tmp:
            first = run_cascade(request(), out_root=Path(tmp))
            first_meta = (first / "metadata.json").read_text()
            real = run_module._refuse_unless_replaceable
            calls = []

            def late_directory(path, *, overwrite):
                result = real(path, overwrite=overwrite)
                calls.append(path)
                if (
                    path.parent.name == ".trash"
                ):  # the moved bundle, after its last check
                    (path / "events.tsv").unlink()
                    (path / "events.tsv").mkdir()
                return result

            with mock.patch.object(
                run_module, "_refuse_unless_replaceable", late_directory
            ):
                second = run_cascade(request(), out_root=Path(tmp))
            self.assertEqual(second, first)
            for name in ("events.tsv", "metadata.json", "cascade.png"):
                self.assertTrue((second / name).is_file(), name)
            self.assertNotEqual((second / "metadata.json").read_text(), first_meta)
            kept = list((Path(tmp) / ".trash").iterdir())
            self.assertEqual(len(kept), 1)
            self.assertTrue((kept[0] / "events.tsv").is_dir())


class NonstationaryControlRuntimeTests(unittest.TestCase):
    def test_a_switching_control_is_recorded_as_a_warning_in_metadata(self):
        # extended_maternal_joint does not carry every node, so the restarted
        # nodes relax and the unperturbed control switches (Stage A).
        start = StartSettings(
            init_horizon=25.0,
            lineage_trajectories=500,
            memory_policy="extended_maternal_joint",
        )
        withdrawal = spec(input_changes={"IN_PROGESTIN": False})
        with tempfile.TemporaryDirectory() as tmp:
            bundle = run_cascade(
                CascadeRequest(
                    withdrawal,
                    n_trajectories=4,
                    master_seed=5,
                    start=start,
                    workers=1,
                    run_id="nonstationary",
                ),
                out_root=Path(tmp),
            )
            meta = json.loads((bundle / "metadata.json").read_text())
        self.assertFalse(meta["diagnostics"]["control_stationary"])
        self.assertEqual(len(meta["warnings"]), 1)
        self.assertIn("matched control switched", meta["warnings"][0])


class InertPerturbationRuntimeTests(unittest.TestCase):
    def test_an_inert_perturbation_completes_its_bundle(self):
        # No v0.6.0 rule reads IN_XAV939, so no tracked node switches in either
        # arm: precedence is empty and the figure must still be drawn.
        inert = spec(name="xav939_off", input_changes={"IN_XAV939": False})
        with tempfile.TemporaryDirectory() as tmp:
            bundle = run_cascade(
                CascadeRequest(
                    inert,
                    n_trajectories=4,
                    master_seed=5,
                    start=FAST_START,
                    workers=1,
                    run_id="inert",
                ),
                out_root=Path(tmp),
            )
            events = pd.read_csv(bundle / "events.tsv", sep="\t")
            self.assertEqual(int(events.n_switches_min.sum()), 0)
            precedence = pd.read_csv(bundle / "pairwise_precedence.tsv", sep="\t")
            self.assertTrue(precedence.empty)
            self.assertIn("p_a_first", precedence.columns)
            for name in ("cascade.png", "cascade.svg", "cascade.pdf", "metadata.json"):
                self.assertTrue((bundle / name).is_file(), name)
