"""Gate G8 (Stage 3): v0.6.0 with named interventions is v0.5.2 with markers.

``docs/intervention_layer_stage3.md`` §8. The parent is v0.5.2 with its
marker-timed protocols; the child is v0.6.0 with its name-timed ones. Both run
the production ``run_protocol`` / ``protocol_continuation`` on the repository,
unpatched. Every v0.5.2 protocol is run as the last phase of its declared
lineage, at the pre-registered seeds and trajectory count, and every phase must
be identical after projecting the deleted nodes out: node trajectories,
last-node marginals, last-state distribution, the continuation it started from,
the vetoed targets, the executed rules and the merged cfg.

The negative controls must fail that comparison, so it is not vacuous. The
comparison code is ``dt_adoc.reporting.stage3_g8``; this test runs it afresh and
does not read the committed report.
"""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Self
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.maboss_adapter import render_network_with_logic_overrides
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.engine import LIBRARY_PATH, MIGRATED_BASIS
from dt_adoc.protocols.conditions import MARKERLESS_PROTOCOLS_PATH, protocol_definitions
from dt_adoc.reporting import stage3_g8 as g8
from dt_adoc.simulation import runner
from tests.unit.checkout_isolation import working_tree_copy

CHILD = g8.CHILD
PARENT = g8.PARENT


class _CreatedCfgDirs:
    """Every merged-cfg directory this process creates while active.

    Recorded at the source rather than by listing the temporary directory, which
    other processes (a concurrent regeneration, say) also write into.
    """

    def __init__(self) -> None:
        self.created: list[Path] = []
        self._patch = mock.patch.object(runner.tempfile, "mkdtemp", self._mkdtemp)
        self._real = tempfile.mkdtemp

    def _mkdtemp(self, *args, **kwargs):
        path = self._real(*args, **kwargs)
        if kwargs.get("prefix") == "dt_adoc_cfg_":
            self.created.append(Path(path))
        return path

    def __enter__(self) -> Self:
        self._patch.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._patch.stop()


class G8LineageTest(unittest.TestCase):
    """Stage B on every lineage, at every pre-registered seed."""

    @classmethod
    def setUpClass(cls) -> None:
        with _CreatedCfgDirs() as dirs:
            cls.parent = {s: g8.run_lineages(PARENT, s, root=ROOT) for s in g8.SEEDS}
            cls.child = {s: g8.run_lineages(CHILD, s, root=ROOT) for s in g8.SEEDS}
        cls.created = dirs.created
        cls.leaked = {str(p) for p in dirs.created if p.exists()}

    def test_the_pre_registered_settings(self) -> None:
        self.assertEqual(g8.SEEDS, (1, 2, 3))
        self.assertEqual(g8.SAMPLE_COUNT, 1000)

    def test_every_lineage_covers_all_fifteen_protocols(self) -> None:
        for seed in g8.SEEDS:
            self.assertEqual(len(self.parent[seed]), 15)
            self.assertEqual(set(self.parent[seed]), set(self.child[seed]))

    def test_every_phase_is_identical_after_projection(self) -> None:
        for seed in g8.SEEDS:
            for protocol_id in sorted(self.parent[seed]):
                with self.subTest(seed=seed, protocol=protocol_id):
                    self.assertEqual(
                        g8.compare_phase(
                            self.parent[seed][protocol_id],
                            self.child[seed][protocol_id],
                        ),
                        [],
                    )

    def test_the_comparison_is_not_of_empty_outputs(self) -> None:
        phase = self.child[1]["adhesion_challenge_hormone_treated_anti_spp1"]
        self.assertGreater(len(phase.outputs["times"]), 1)
        self.assertIn("OUT_STABLE_ADHESION", phase.outputs["columns"])
        self.assertGreater(len(phase.outputs["last_states"]), 1)
        self.assertIsNotNone(phase.initialisation)

    def test_the_interventions_act_where_the_markers_did(self) -> None:
        expected = {
            "hormone_treated_mifepristone": {"E_PGR", "S_PGR"},
            "adhesion_challenge_hormone_treated_mifepristone": {"E_PGR", "S_PGR"},
            "hormone_treated_anti_spp1": {"X_SPP1_LUMEN_FREE"},
            "adhesion_challenge_hormone_treated_anti_spp1": {"X_SPP1_LUMEN_FREE"},
            "hormone_treated_hand2_loss": {"S_HAND2"},
            "adhesion_challenge_hormone_treated_hand2_loss": {"S_HAND2"},
        }
        for protocol_id, phase in self.child[1].items():
            with self.subTest(protocol=protocol_id):
                self.assertEqual(set(phase.vetoed), expected.get(protocol_id, set()))
                self.assertEqual(
                    set(self.parent[1][protocol_id].vetoed),
                    expected.get(protocol_id, set()),
                )

    def test_washout_lifts_the_anti_spp1_veto(self) -> None:
        washout = self.child[1]["washout"]
        self.assertEqual(washout.vetoed, {})
        self.assertEqual(washout.named, ())
        self.assertEqual(
            washout.initialisation["source_protocol"], "hormone_treated_anti_spp1"
        )

    def test_the_child_names_no_marker_anywhere(self) -> None:
        for phase in self.child[1].values():
            self.assertEqual(phase.legacy_input_values, {})
            self.assertFalse(set(phase.outputs["columns"]) & set(g8.DELETED_NODES))
            self.assertFalse(set(phase.executed_rules) & set(g8.DELETED_NODES))

    def test_each_run_reconstructs_from_its_record(self) -> None:
        """Model hash, protocol, named interventions, library, executed network."""
        library_sha = hashlib.sha256((ROOT / LIBRARY_PATH).read_bytes()).hexdigest()
        text = resolve_model(CHILD, ROOT).network_bnd.read_text(encoding="utf-8")
        child_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        for protocol_id, phase in self.child[1].items():
            record = phase.executed_network
            with self.subTest(protocol=protocol_id):
                self.assertEqual(record["source_network"]["sha256"], child_sha)
                self.assertEqual(record["intervention_library"]["sha256"], library_sha)
                rebuilt = render_network_with_logic_overrides(
                    text, logic_overrides=record["logic_overrides"]
                )
                self.assertEqual(
                    record["network_sha256"],
                    hashlib.sha256(rebuilt.encode("utf-8")).hexdigest(),
                )
                timing = record["intervention_timing"]
                self.assertEqual(timing["protocol_id"], protocol_id)
                self.assertEqual(timing["protocol_declared"], list(phase.named))
                self.assertEqual(timing["caller_supplied"], [])
                for effect in record["named_intervention_effects"]:
                    self.assertEqual(effect["mapping_basis"], MIGRATED_BASIS)
                    self.assertEqual(effect["parent_model_version"], PARENT)

    def test_every_temporary_cfg_directory_is_released(self) -> None:
        # 15 protocols x 2 versions x 3 seeds, each one step.
        self.assertEqual(len(self.created), 90)
        self.assertEqual(self.leaked, set())


class G8ConditionSuiteTest(unittest.TestCase):
    """The 21 condition cfgs, each run standalone, with the interventions named."""

    def test_every_condition_is_identical_after_projection(self) -> None:
        for seed in g8.SEEDS:
            for cfg, result in sorted(g8.condition_suite(ROOT, seed).items()):
                with self.subTest(seed=seed, condition=cfg):
                    self.assertTrue(result["identical"], result["differences"])

    def test_a_standalone_v060_cfg_is_untreated(self) -> None:
        """Without its protocol, a v0.6.0 arm cfg runs no intervention (design §6)."""
        parent_dir = resolve_model(PARENT, ROOT).condition_dir
        self.assertEqual(
            g8._cfg_markers(parent_dir / "hormone_treated_anti_spp1.cfg"), ["anti_spp1"]
        )
        phase = g8._condition_phase(CHILD, "hormone_treated_anti_spp1.cfg", 1, ROOT, ())
        self.assertEqual(phase.vetoed, {})


class G8NegativeControlTest(unittest.TestCase):
    """Each mistake must fail G8; the correctly timed phases must not."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = g8.run_lineages(PARENT, 1, root=ROOT)
        cls.results = g8.negative_controls(ROOT, cls.parent, 1)

    def test_every_control_is_detected(self) -> None:
        for name, result in self.results.items():
            with self.subTest(control=name):
                self.assertTrue(result["detected"])

    def test_the_errors_show_in_the_dynamics(self) -> None:
        for name in g8.NEGATIVE_CONTROLS:
            for protocol_id, compared in self.results[name]["lineages"].items():
                if compared["identical"]:
                    continue
                with self.subTest(control=name, protocol=protocol_id):
                    self.assertIn("trajectory", compared["differences"])
                    self.assertIn("last_states", compared["differences"])

    def test_omission_and_a_missing_washout_fail_where_they_act(self) -> None:
        omitted = self.results["NC1_anti_spp1_omitted"]["lineages"]
        self.assertFalse(omitted["hormone_treated_anti_spp1"]["identical"])
        not_washed = self.results["NC2_anti_spp1_not_washed_out"]["lineages"]
        self.assertFalse(not_washed["washout"]["identical"])
        self.assertIn("vetoed_targets", not_washed["washout"]["differences"])

    def test_mistiming_fails_both_phases(self) -> None:
        lineages = self.results["NC3_mifepristone_mistimed"]["lineages"]
        self.assertFalse(lineages["hormone_treated_mifepristone"]["identical"])
        challenge = lineages["adhesion_challenge_hormone_treated_mifepristone"]
        self.assertFalse(challenge["identical"])
        # The challenge's own veto is correct; it differs because it starts from
        # a maternal phase that was never treated.
        self.assertNotIn("vetoed_targets", challenge["differences"])
        self.assertIn("initialisation", challenge["differences"])

    def test_a_gate_left_in_place_is_refused_structurally(self) -> None:
        for name in (
            "NC4a_gate_kept_node_deleted",
            "NC4b_gate_and_node_kept_marker_off",
        ):
            with self.subTest(control=name):
                result = self.results[name]
                self.assertIn("IN_HAND2_LOSS", result["library_licence"])
                self.assertTrue(
                    any(
                        v.startswith("IN_HAND2_LOSS is read by")
                        for v in result["structural_assertions"]
                    )
                )


class ConsumerTest(unittest.TestCase):
    """A name-timed intervention must not vanish from the consumers (design §12)."""

    def test_the_timeline_carries_each_phase_s_interventions(self) -> None:
        from dt_adoc.simulation.timeline import build_sequential_timeline

        timeline = build_sequential_timeline(
            model_version=CHILD,
            terminal_protocol="adhesion_challenge_washout",
            root=ROOT,
            trajectory_count=200,
        )
        by_protocol = {p.protocol_id: p for p in timeline.phases}
        self.assertEqual(
            by_protocol["hormone_treated_anti_spp1"].interventions, ("anti_spp1",)
        )
        self.assertEqual(by_protocol["washout"].interventions, ())
        for phase in timeline.phases:
            self.assertFalse(set(phase.input_states) & set(g8.DELETED_NODES))
        self.assertFalse(set(timeline.input_ids) & set(g8.DELETED_NODES))

    def test_the_smoke_records_step_interventions(self) -> None:
        spec = resolve_model(CHILD, ROOT)
        definitions = protocol_definitions(ROOT, model_version=CHILD)
        lineage: list[str] = []
        for protocol_id in spec.default_smoke_protocols:
            parent = definitions[protocol_id].continuation_from
            if parent is not None and parent not in lineage:
                lineage.append(parent)
            lineage.append(protocol_id)
        # The smoke writes under its root; run it on a copy, not the checkout.
        work = working_tree_copy(Path(self.enterContext(tempfile.TemporaryDirectory())))
        narrowed = dataclasses.replace(
            resolve_model(CHILD, work), default_smoke_protocols=tuple(lineage)
        )
        with mock.patch.object(runner, "resolve_model", return_value=narrowed):
            output_root = runner.run_structural_smoke(
                run_id="stage3-g8-consumer-fixture", model_version=CHILD, root=work
            )
        manifest = json.loads((output_root / "run_manifest.json").read_text())
        continuation = manifest["simulation"]["continuation"]
        self.assertEqual(
            continuation["declared_in"], MARKERLESS_PROTOCOLS_PATH.as_posix()
        )
        recorded = {
            row["protocol_id"]: row["step_interventions"]
            for row in continuation["protocol_initializations"]
        }
        self.assertEqual(recorded["hormone_treated_anti_spp1"], ["anti_spp1"])
        self.assertEqual(
            recorded["adhesion_challenge_hormone_treated_mifepristone"],
            ["mifepristone"],
        )
        self.assertEqual(recorded["washout"], [])
        with (output_root / "tables/protocol_initializations.tsv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = {r["protocol_id"]: r for r in csv.DictReader(handle, delimiter="\t")}
        self.assertEqual(
            rows["hormone_treated_anti_spp1"]["step_interventions"], "anti_spp1"
        )
        self.assertNotIn(
            "IN_ANTI_SPP1", rows["hormone_treated_anti_spp1"]["forced_input_nodes"]
        )
        executed = {
            row["protocol_id"]: row["named_interventions"]
            for row in manifest["model"]["executed_networks"]
        }
        self.assertEqual(executed["hormone_treated_anti_spp1"], ["anti_spp1"])


if __name__ == "__main__":
    unittest.main()
