"""Stage 3 guards: v0.6.0 is v0.5.2 without its intervention-marker nodes.

``docs/intervention_layer_stage3.md``. Each check guards a way this unit could
look finished without being finished:

1. **v0.6.0 is generated, not hand-edited.** Its directory, its protocol file
   and its library rows rebuild byte for byte from v0.5.2 through
   ``dt_adoc.reporting.v060_increment``, and only the declared files differ.
2. **The markers are gone wherever they would execute** (design §11): nodes,
   rules, cfgs, the node dictionary, protocol input states, library rows.
   ``IN_XAV939`` is deliberately kept.
3. **The Boolean transformation is right (G8 Stage A).** For every combination
   of marker values, every node's composed function over all 2**16 assignments
   equals v0.5.2's, with the engine rendering the interventions whose markers
   are ON.
4. **The migrated rows are licensed, and only by the parent.** Each way a
   ``migrated_legacy_behaviour`` row could escape its licence is refused.
5. **The protocol layer keeps archived versions where they were.** The
   markerless file cannot serve an archived version, an unrowed later version
   is refused rather than cloned, and an input state naming a missing node is
   refused at resolution.
6. **The static analyses refuse rather than mislead.** They read exposure from
   cfgs, so on a name-timed version they would read the treated arms as
   untreated.

No simulation runs here. The dynamic half of G8 is
``tests/integration/test_stage3_g8_runtime.py``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import available_models, resolve_model
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.perturbations.engine import (
    ACTIVITY_VETO,
    LEGACY_BASIS,
    LIBRARY_COLUMNS,
    LIBRARY_PATH,
    MIGRATED_BASIS,
    InterventionError,
    intervention_logic_overrides,
    library_for_version,
    load_intervention_library,
    named_effect_records,
)
from dt_adoc.protocols.conditions import (
    MARKERLESS_PROTOCOLS_PATH,
    protocol_definitions,
)
from dt_adoc.reporting import stage3_g8
from dt_adoc.reporting.v060_increment import (
    CHANGED_FILES,
    DELETED_NODES,
    KEPT_REAGENT_INPUT,
    MARKERS,
    MIGRATED_INTERVENTIONS,
    MODEL_DIR,
    MODEL_VERSION,
    PARENT_DIR,
    PARENT_VERSION,
    PROTOCOLS_PATH,
    build_increment,
    build_protocols,
    library_rows,
)

PARENT = ROOT / PARENT_DIR
MODEL = ROOT / MODEL_DIR


def _files(directory: Path) -> dict[str, bytes]:
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def _library_rows(root: Path) -> list[dict[str, str]]:
    with (root / LIBRARY_PATH).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_library(root: Path, rows: list[dict[str, str]]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=LIBRARY_COLUMNS, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    (root / LIBRARY_PATH).write_text(buffer.getvalue(), encoding="utf-8")


def _edit_rows(intervention_id: str, **fields: str):
    """An edit that changes the v0.6.0 rows of one intervention."""

    def apply(root: Path) -> None:
        rows = _library_rows(root)
        for row in rows:
            if (
                row["intervention_id"] == intervention_id
                and row["model_version"] == MODEL_VERSION
            ):
                row.update(fields)
        _write_library(root, rows)

    return apply


class GeneratedVersionTest(unittest.TestCase):
    def test_the_committed_directory_rebuilds_byte_for_byte(self) -> None:
        built = build_increment(ROOT)
        on_disk = _files(MODEL)
        self.assertEqual(sorted(built), sorted(on_disk))
        for name in sorted(built):
            with self.subTest(file=name):
                self.assertEqual(built[name], on_disk[name])

    def test_the_protocol_file_rebuilds_byte_for_byte(self) -> None:
        self.assertEqual(PROTOCOLS_PATH, MARKERLESS_PROTOCOLS_PATH)
        self.assertEqual(build_protocols(ROOT), (ROOT / PROTOCOLS_PATH).read_bytes())

    def test_the_library_rows_are_the_generated_ones(self) -> None:
        committed = [
            row for row in _library_rows(ROOT) if row["model_version"] == MODEL_VERSION
        ]
        self.assertEqual(committed, library_rows(ROOT))

    def test_only_the_declared_files_differ_from_the_parent(self) -> None:
        parent, child = _files(PARENT), _files(MODEL)
        self.assertEqual(set(child), set(parent), "no file added or removed")
        differing = {n for n in parent if parent[n] != child[n]}
        conditions = {n for n in parent if n.startswith("conditions/")}
        self.assertEqual(differing, set(CHANGED_FILES) | conditions)

    def test_exactly_the_marker_nodes_and_their_four_gates_go(self) -> None:
        parent = parse_bnd_rules(PARENT / "network.bnd")
        child = parse_bnd_rules(MODEL / "network.bnd")
        self.assertEqual(set(parent) - set(child), set(DELETED_NODES))
        self.assertEqual(set(child) - set(parent), set())
        changed = {n for n in child if child[n] != parent[n]}
        self.assertEqual(changed, {"E_PGR", "S_PGR", "X_SPP1_LUMEN_FREE", "S_HAND2"})
        for marker in MARKERS:
            for rule in marker.rules:
                with self.subTest(node=rule.node):
                    self.assertEqual(parent[rule.node], rule.logic_before)
                    self.assertEqual(child[rule.node], rule.logic_after)
                    self.assertEqual(
                        rule.logic_before.replace(f" and not {marker.node}", "")
                        .removeprefix("(")
                        .replace(")", ""),
                        rule.logic_after,
                    )

    def test_the_increment_records_its_ancestry(self) -> None:
        payload = tomllib.loads((MODEL / "provenance.toml").read_text())
        self.assertEqual(payload["model_version"], MODEL_VERSION)
        increment = payload["increment"]
        self.assertEqual(increment["parent_model_version"], PARENT_VERSION)
        self.assertEqual(increment["transformation"], "intervention_marker_removal")
        self.assertEqual(increment["deleted_nodes"], list(DELETED_NODES))
        self.assertEqual(increment["kept_reagent_inputs"], [KEPT_REAGENT_INPUT])
        self.assertEqual(increment["migrated_interventions"], MIGRATED_INTERVENTIONS)
        self.assertEqual(increment["migrated_protocols"], PROTOCOLS_PATH.as_posix())
        self.assertEqual(
            increment["migrated_protocols_sha256"],
            hashlib.sha256((ROOT / PROTOCOLS_PATH).read_bytes()).hexdigest(),
        )
        self.assertEqual(increment["equivalence_gate"], "G8")
        self.assertEqual(
            increment["retired_edges"], ["LE002", "LE038", "LE059", "LE096"]
        )
        self.assertEqual(increment["files_added"], [])
        for name, key in (
            ("network.bnd", "parent_network_bnd_sha256"),
            ("baseline.cfg", "parent_baseline_cfg_sha256"),
            ("provenance.toml", "parent_provenance_sha256"),
        ):
            with self.subTest(file=name):
                self.assertEqual(
                    increment[key],
                    hashlib.sha256((PARENT / name).read_bytes()).hexdigest(),
                )

    def test_every_hash_in_the_provenance_matches_its_file(self) -> None:
        payload = tomllib.loads((MODEL / "provenance.toml").read_text())
        for key, path in payload["artifacts"].items():
            with self.subTest(artifact=key):
                self.assertEqual(
                    payload["artifact_hashes"][f"{key}_sha256"],
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                )
        for cfg in sorted((MODEL / "conditions").glob("*.cfg")):
            with self.subTest(condition=cfg.name):
                self.assertEqual(
                    payload["condition_hashes"][f"{cfg.stem}_cfg_sha256"],
                    hashlib.sha256(cfg.read_bytes()).hexdigest(),
                )

    def test_the_parent_is_unchanged_and_every_version_still_resolves(self) -> None:
        # v0.5.2's own guard (test_v052_paep_hand2) rebuilds it byte for byte
        # from v0.5.1; here, every version resolves and keeps its protocols.
        for version in available_models(ROOT):
            with self.subTest(version=version):
                definitions = protocol_definitions(ROOT, model_version=version)
                if version != MODEL_VERSION:
                    self.assertFalse(
                        any(
                            s.interventions
                            for d in definitions.values()
                            for s in d.steps
                        )
                    )


class StructuralAssertionTest(unittest.TestCase):
    """Design §11, mechanically."""

    def test_no_marker_survives_where_it_would_execute(self) -> None:
        self.assertEqual(stage3_g8.structural_violations(ROOT), [])

    def test_xav939_is_kept(self) -> None:
        rules = parse_bnd_rules(MODEL / "network.bnd")
        self.assertEqual(rules[KEPT_REAGENT_INPUT], KEPT_REAGENT_INPUT)
        view = library_for_version(load_intervention_library(ROOT), MODEL_VERSION)
        (row,) = view["xav939"]
        self.assertEqual(
            (row.mapping_basis, row.mode, row.legacy_input_node),
            (LEGACY_BASIS, "no_executable_effect", KEPT_REAGENT_INPUT),
        )

    def test_the_named_interventions_hit_exactly_the_parent_targets(self) -> None:
        library = load_intervention_library(ROOT)
        text = (MODEL / "network.bnd").read_text(encoding="utf-8")
        for marker in MARKERS:
            with self.subTest(intervention=marker.intervention_id):
                overrides = intervention_logic_overrides(
                    text,
                    [marker.intervention_id],
                    model_version=MODEL_VERSION,
                    library=library,
                )
                self.assertEqual(set(overrides), {r.node for r in marker.rules})
                for rule in marker.rules:
                    self.assertEqual(
                        overrides[rule.node], f"({rule.logic_after}) and not 1"
                    )

    def test_the_v060_protocols_are_the_parent_schedule_under_the_projection(
        self,
    ) -> None:
        self.assertEqual(stage3_g8.protocol_mapping(ROOT), [])

    def test_the_schedule_names_the_interventions_in_the_marker_phases(self) -> None:
        definitions = protocol_definitions(ROOT, model_version=MODEL_VERSION)
        named = {
            pid: sorted({i for s in d.steps for i in s.interventions})
            for pid, d in definitions.items()
        }
        self.assertEqual(
            {pid: n for pid, n in named.items() if n},
            {
                "hormone_treated_mifepristone": ["mifepristone"],
                "adhesion_challenge_hormone_treated_mifepristone": ["mifepristone"],
                "hormone_treated_anti_spp1": ["anti_spp1"],
                "adhesion_challenge_hormone_treated_anti_spp1": ["anti_spp1"],
                "hormone_treated_hand2_loss": ["hand2_loss"],
                "adhesion_challenge_hormone_treated_hand2_loss": ["hand2_loss"],
            },
        )
        self.assertEqual(
            definitions["washout"].continuation_from, "hormone_treated_anti_spp1"
        )

    def test_the_committed_structural_counts_are_recomputed(self) -> None:
        committed = json.loads((ROOT / stage3_g8.STRUCTURE).read_text())
        self.assertEqual(
            committed, json.loads(json.dumps(stage3_g8.structural_counts(ROOT)))
        )
        versions = committed["versions"]
        self.assertEqual(
            (versions[PARENT_VERSION]["nodes"], versions[MODEL_VERSION]["nodes"]),
            (59, 56),
        )
        self.assertEqual(
            (
                versions[PARENT_VERSION]["enumerated_assignments"],
                versions[MODEL_VERSION]["enumerated_assignments"],
            ),
            (2**19, 2**16),
        )
        self.assertEqual(committed["removed_inputs"], sorted(DELETED_NODES))


class BooleanTransformationTest(unittest.TestCase):
    """G8 Stage A.1: composed functions for every combination of marker values."""

    def test_every_composed_function_matches_the_parent(self) -> None:
        result = stage3_g8.composed_equivalence(ROOT)
        self.assertEqual(result["enumerated_assignments"], 2**16)
        self.assertEqual(len(result["combinations"]), 2 ** len(DELETED_NODES))
        for combination in result["combinations"]:
            with self.subTest(markers_on=combination["markers_on"]):
                self.assertEqual(combination["nodes_compared"], 56)
                self.assertEqual(
                    combination["nodes_whose_composed_function_differs"], []
                )
        self.assertTrue(result["passed"])

    def test_the_check_detects_a_wrong_rule(self) -> None:
        def wrong(root: Path) -> None:
            path = root / MODEL_DIR / "network.bnd"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    "  logic = E_SPP1_EXPR or S_SPP1;\n", "  logic = E_SPP1_EXPR;\n"
                ),
                encoding="utf-8",
            )

        with (
            stage3_g8.sandbox(ROOT, wrong) as box,
            self.assertRaisesRegex(InterventionError, "not the parent's"),
        ):
            load_intervention_library(box)


class MigratedLicenceTest(unittest.TestCase):
    """What a ``migrated_legacy_behaviour`` row must satisfy (design §7.2)."""

    def test_the_committed_rows_are_licensed_by_v052(self) -> None:
        view = library_for_version(load_intervention_library(ROOT), MODEL_VERSION)
        for marker in MARKERS:
            effects = view[marker.intervention_id]
            with self.subTest(intervention=marker.intervention_id):
                self.assertEqual({e.mapping_basis for e in effects}, {MIGRATED_BASIS})
                self.assertEqual({e.mode for e in effects}, {ACTIVITY_VETO})
                self.assertEqual(
                    {e.parent_model_version for e in effects}, {PARENT_VERSION}
                )
                self.assertEqual({e.legacy_input_node for e in effects}, {""})

    def test_the_record_names_the_parent(self) -> None:
        records = named_effect_records(
            ["anti_spp1"], load_intervention_library(ROOT), model_version=MODEL_VERSION
        )
        (record,) = records
        self.assertEqual(record["mapping_basis"], MIGRATED_BASIS)
        self.assertEqual(record["parent_model_version"], PARENT_VERSION)
        self.assertEqual(record["model_version"], MODEL_VERSION)
        legacy = named_effect_records(
            ["anti_spp1"], load_intervention_library(ROOT), model_version=PARENT_VERSION
        )
        self.assertNotIn("parent_model_version", legacy[0])

    def _refused(self, edit, pattern: str) -> None:
        with (
            stage3_g8.sandbox(ROOT, edit) as box,
            self.assertRaisesRegex(InterventionError, pattern),
        ):
            load_intervention_library(box)

    def test_a_marker_on_a_migrated_row_is_refused(self) -> None:
        self._refused(
            _edit_rows("hand2_loss", legacy_input_node="IN_XAV939"),
            "names no legacy input",
        )

    def test_a_perturbation_id_on_a_migrated_row_is_refused(self) -> None:
        self._refused(
            _edit_rows("hand2_loss", legacy_perturbation_ids="hand2_loss_after_ht"),
            "names no legacy input",
        )

    def test_another_mode_is_refused(self) -> None:
        self._refused(
            _edit_rows("hand2_loss", target_node="", mode="no_executable_effect"),
            "takes mode activity_veto",
        )

    def test_a_target_the_parent_does_not_veto_is_refused(self) -> None:
        self._refused(
            _edit_rows("anti_spp1", target_node="E_SPP1_EXPR"), "targets differ"
        )

    def test_changed_evidence_is_refused(self) -> None:
        self._refused(
            _edit_rows("anti_spp1", evidence_ids="LIT-SPP1-001"),
            "evidence or abstraction differs",
        )

    def test_a_row_for_a_version_whose_marker_still_exists_is_refused(self) -> None:
        def move(root: Path) -> None:
            rows = _library_rows(root)
            for row in rows:
                if (
                    row["model_version"] == MODEL_VERSION
                    and row["intervention_id"] == "xav939"
                ):
                    row.update(
                        legacy_input_node="",
                        mapping_basis=MIGRATED_BASIS,
                        target_node="E_PGR",
                        mode=ACTIVITY_VETO,
                    )
            _write_library(root, rows)

        self._refused(
            move, "has no executable_legacy_behaviour row|mode differs|targets differ"
        )

    def test_a_parent_without_a_legacy_row_is_refused(self) -> None:
        def orphan(root: Path) -> None:
            rows = [
                r
                for r in _library_rows(root)
                if not (
                    r["intervention_id"] == "hand2_loss"
                    and r["model_version"] == PARENT_VERSION
                )
            ]
            _write_library(root, rows)

        self._refused(orphan, "has no executable_legacy_behaviour row")

    def test_a_model_with_no_parent_is_refused(self) -> None:
        def unparented(root: Path) -> None:
            path = root / MODEL_DIR / "provenance.toml"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(f'parent_model_version = "{PARENT_VERSION}"\n', ""),
                encoding="utf-8",
            )

        self._refused(unparented, "names no parent version")

    def test_a_kept_marker_is_refused(self) -> None:
        with (
            stage3_g8.sandbox(ROOT, stage3_g8.keep_gate_and_node) as box,
            self.assertRaisesRegex(InterventionError, "still a node"),
        ):
            load_intervention_library(box)

    def test_one_id_may_not_change_identity_across_versions(self) -> None:
        self._refused(
            _edit_rows("hand2_loss", intervention_label="Something else"),
            "label or class across model versions",
        )

    def test_a_version_without_the_row_is_refused_by_name(self) -> None:
        library = load_intervention_library(ROOT)
        text = resolve_model(
            "adoc-literature-superset-v0.5.1", ROOT
        ).network_bnd.read_text(encoding="utf-8")
        with self.assertRaisesRegex(
            InterventionError, "is defined for .*v0.5.2, .*v0.6.0, not .*v0.5.1"
        ):
            intervention_logic_overrides(
                text,
                ["hand2_loss"],
                model_version="adoc-literature-superset-v0.5.1",
                library=library,
            )


class ProtocolLayerTest(unittest.TestCase):
    """Design §6: what the markerless file may and may not do."""

    def _edit_payload(self, change):
        def apply(root: Path) -> None:
            path = root / MARKERLESS_PROTOCOLS_PATH
            payload = json.loads(path.read_text(encoding="utf-8"))
            change(payload)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        return apply

    def test_an_archived_version_cannot_take_rows_from_the_file(self) -> None:
        def archive(payload):
            payload["protocols"][0]["model_version"] = PARENT_VERSION

        with (
            stage3_g8.sandbox(ROOT, self._edit_payload(archive)) as box,
            self.assertRaisesRegex(ValueError, "predates the markerless"),
        ):
            protocol_definitions(box, model_version=PARENT_VERSION)

    def test_a_markerless_version_without_rows_is_refused_not_cloned(self) -> None:
        def empty(payload):
            payload["protocols"] = []

        with (
            stage3_g8.sandbox(ROOT, self._edit_payload(empty)) as box,
            self.assertRaisesRegex(ValueError, "cannot be cloned"),
        ):
            protocol_definitions(box, model_version=MODEL_VERSION)

    def test_an_input_state_naming_a_deleted_node_is_refused(self) -> None:
        def stale(payload):
            payload["protocols"][0]["steps"][0]["input_states"]["IN_ANTI_SPP1"] = False

        refusal = self.assertRaisesRegex(
            ValueError, "IN_ANTI_SPP1, which .* does not have"
        )
        with stage3_g8.sandbox(ROOT, self._edit_payload(stale)) as box, refusal:
            protocol_definitions(box, model_version=MODEL_VERSION)

    def test_the_file_is_a_declared_post_closure_file(self) -> None:
        from dt_adoc import closure_replay

        self.assertIn(
            MARKERLESS_PROTOCOLS_PATH.as_posix(), closure_replay.POST_CLOSURE_FILES
        )

    def test_config_protocols_yaml_names_no_v060_row(self) -> None:
        text = (ROOT / "config/protocols.yaml").read_text(encoding="utf-8")
        self.assertNotIn(MODEL_VERSION, text)


class StaticAnalysisPinTest(unittest.TestCase):
    """The cfg-reading static analyses never see a name-timed version.

    ``reporting.identifiability`` and ``reporting.design_alias`` read an arm's
    exposure off its condition cfg, so on v0.6.0 they would read the treated
    arms as untreated. They are not edited here: both files are pinned by sha256
    in closed units' outputs, the C3a run settings among them. So what is guarded
    is that every committed input that selects their model selects a
    marker-timed version (design §12).
    """

    def _markerless(self) -> set[str]:
        from dt_adoc.protocols.conditions import markerless_protocol_rows

        return {row["model_version"] for row in markerless_protocol_rows(ROOT)}

    def test_the_planned_design_pins_a_marker_timed_version(self) -> None:
        import yaml

        payload = yaml.safe_load((ROOT / "config/planned_design.yaml").read_text())
        self.assertNotIn(payload["model_version"], self._markerless())

    def test_the_cli_default_pins_a_marker_timed_version(self) -> None:
        text = (SRC / "dt_adoc/cli.py").read_text(encoding="utf-8")
        for version in self._markerless():
            self.assertNotIn(version, text)


class G8ReportTest(unittest.TestCase):
    """The committed G8 report describes the committed files."""

    def test_the_report_passed_and_matches_the_current_files(self) -> None:
        report = json.loads((ROOT / stage3_g8.REPORT).read_text())
        self.assertTrue(report["passed"])
        self.assertFalse(report["fallback_used"])
        self.assertTrue(report["stage_b"]["exact"])
        self.assertEqual(report["settings"]["seeds"], [1, 2, 3])
        current = {
            "parent_network_bnd": PARENT / "network.bnd",
            "child_network_bnd": MODEL / "network.bnd",
            "intervention_library": ROOT / LIBRARY_PATH,
            "protocols_yaml": ROOT / "config/protocols.yaml",
            "protocols_markerless_yaml": ROOT / MARKERLESS_PROTOCOLS_PATH,
        }
        for key, path in current.items():
            with self.subTest(file=key):
                self.assertEqual(
                    report["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest()
                )
        controls = report["negative_controls"]
        self.assertEqual(
            set(controls),
            {
                "NC1_anti_spp1_omitted",
                "NC2_anti_spp1_not_washed_out",
                "NC3_mifepristone_mistimed",
                "NC4a_gate_kept_node_deleted",
                "NC4b_gate_and_node_kept_marker_off",
            },
        )
        for name, control in controls.items():
            with self.subTest(control=name):
                self.assertTrue(control["detected"])


if __name__ == "__main__":
    unittest.main()
