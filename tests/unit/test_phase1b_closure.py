"""Phase-1B closure audit and the prospective `dropout_e2` handoff.

What these guards hold, and why each one exists:

* **Nothing the audit reads was moved to make it pass.** `models/`, the
  observation map, the calibration contract, the protocols and the four frozen
  Stage-3 artifacts are pinned to literals. The generator opens nothing for
  writing outside `docs/phase1b_closure/`.
* **The handoff quotes the frozen design and is checked against it.** The quoted
  phrases must appear verbatim in the frozen text and are rendered into the
  handoff. The handoff's own dose, day, outlet and replication statements are
  asserted against those quotes.
  The bands are recomputed from the canonical protein table and must match the
  frozen quotes, and the frozen §5 decision tree is carried cell for cell. A
  test removes a phrase from the frozen text in memory and shows that the build
  refuses.
* **The claim ceilings are the contract's.** Every `MAY` claim about constraints,
  adhesion and mifepristone is checked against `config/calibration.yaml` and
  `config/observation_model_map.tsv`, as the build read them.
* **The status is derived.** The overall status is recomputed here from the
  committed exit-gate TSV by the declared rule, and the rule is driven through
  all three outcomes.
* **A moved premise stops the build.** If the adopted model stopped
  contradicting the mifepristone arm, the audit's statuses would outlive their
  ground, so the build raises `AUDIT_PREMISE_MOVED` instead.
* **The owner's pre-run addendum is carried whole**, dated and labelled, with
  its precedence order, and PRL never decides a call anywhere in the handoff.
"""

from __future__ import annotations

import builtins
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# History-bound: replays and audits read frozen commits of the DT-ADOC history,
# which ENDO-TWIN does not carry (tests/unit/source_history.py).
from tests.unit.source_history import skip_module_unless_available

skip_module_unless_available("97f88f55ce62e2adca23f631de3ad8e1270ad3e6")

from dt_adoc import closure_replay
from dt_adoc.experiments import phase1b_closure as p1b
from dt_adoc.reporting.identifiability import repo_root

ROOT = repo_root()


# Closed phases are reproduced against their closure-time models/ snapshot
# (src/dt_adoc/closure_replay.py); later model versions are outside it.
_CLOSURE_TMP = tempfile.TemporaryDirectory(prefix="closure-replay-")
CLOSURE, _CLOSURE_INDEX = closure_replay.build_view(ROOT, Path(_CLOSURE_TMP.name))
CLOSURE_ENV = {"GIT_INDEX_FILE": str(_CLOSURE_INDEX)}


def tearDownModule() -> None:
    _CLOSURE_TMP.cleanup()


#: The same literals `tests/unit/test_v05_u8_stage3_rerank.py` pins.
FROZEN_DIGESTS = {
    "docs/experiments/stage3_experiment_design.tsv": "987d75644925346fab73e7251067094d04c01883af783a83c3775705b444ee74",
    "docs/experiments/stage3_experiment_design.md": "7368b1f85007f677cd16c5f308d9571f9573a83771b3dfdb2bb34b593b068520",
    "docs/experiments/stage3_decision_tables.md": "a2cc7291adfaf130f79f345201a30556ab16c9391c8598315a5735d6b0c3305b",
    "docs/stage3_experiment_selection.md": "e6a5fa558bede27f20b329cfbfe7bd3ec90d4d41c0f5091ed52e3dd4cbdb113c",
}

#: Contract files this unit must not touch, pinned at the unit's base (228831c).
CONTRACT_DIGESTS = {
    "config/observation_model_map.tsv": "74f0d5d0896beba57a0a03960239ad2fc039f315fa42a2209a65e228bfa3aff5",
    "config/calibration.yaml": "8fd4662ae17e6a112545e086831b5d46dab46746f00157136ededf962ee27a0b",
    "config/protocols.yaml": "243887238ee927770e53b8d5116c8f464c864abb84ddd8b0b4214b7146019f1a",
}

#: Every file under `models/`, as one digest, at the unit's base.
MODELS_TREE_SHA256 = "de1bddba2be91e837fefbd784c21790531790ec0ee85c5babd7d4dd2844657b5"
MODEL_DIRECTORIES = {
    "adoc-literature-superset-v0.3.0",
    "adoc-literature-superset-v0.4.0",
    "adoc-literature-superset-v0.5.0",
    "adoc-literature-superset-v0.5.1",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tsv(relative: Path) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class _OpenRecorder:
    def __init__(self) -> None:
        self.opened: list[tuple[Path, str]] = []
        self._real = builtins.open

    def __call__(self, file, mode="r", *args, **kwargs):
        if isinstance(file, (str, Path)):
            self.opened.append((Path(file).resolve(), mode))
        return self._real(file, mode, *args, **kwargs)


class Phase1BClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        recorder = _OpenRecorder()
        with mock.patch("builtins.open", recorder), mock.patch("io.open", recorder):
            cls.result = p1b.compute(CLOSURE)
        cls.opened = recorder.opened
        cls.outputs = p1b.render_outputs(cls.result)
        cls.summary = json.loads((ROOT / p1b.OUT_SUMMARY).read_text(encoding="utf-8"))
        cls.selection = (ROOT / p1b.FROZEN_SELECTION).read_text(encoding="utf-8")

    # -- immutability -----------------------------------------------------------

    def test_frozen_stage3_artifacts_are_byte_identical(self) -> None:
        self.assertEqual(p1b.FROZEN_DIGESTS, FROZEN_DIGESTS)
        for relative, digest in FROZEN_DIGESTS.items():
            with self.subTest(artifact=relative):
                self.assertEqual(_sha(ROOT / relative), digest)

    def test_contract_files_are_unchanged(self) -> None:
        for relative, digest in CONTRACT_DIGESTS.items():
            with self.subTest(file=relative):
                self.assertEqual(_sha(ROOT / relative), digest)
                if relative in self.summary["lineage"]["inputs_sha256"]:
                    self.assertEqual(
                        self.summary["lineage"]["inputs_sha256"][relative], digest
                    )

    def test_no_file_under_models_changed_and_no_version_was_created(self) -> None:
        # The closure-time snapshot, copied from the live tree, is the tree the
        # closure recorded: every historical version is byte-identical.
        self.assertEqual(p1b._tree_sha(CLOSURE, Path("models")), MODELS_TREE_SHA256)
        self.assertEqual(
            self.summary["lineage"]["models_tree_sha256"], MODELS_TREE_SHA256
        )
        self.assertEqual(
            {p.name for p in (CLOSURE / "models/superset").iterdir() if p.is_dir()},
            MODEL_DIRECTORIES,
        )
        self.assertEqual(closure_replay.CLOSURE_SUPERSET_VERSIONS, MODEL_DIRECTORIES)

    def test_the_computation_writes_nothing(self) -> None:
        writes = [str(p) for p, mode in self.opened if any(c in mode for c in "wax+")]
        self.assertEqual(writes, [])

    def test_the_adopted_network_is_the_one_read(self) -> None:
        bnd = (
            CLOSURE / "models/superset/adoc-literature-superset-v0.5.1/network.bnd"
        ).resolve()
        self.assertIn(bnd, {p for p, _ in self.opened})

    # -- regeneration -----------------------------------------------------------

    def test_committed_outputs_equal_a_fresh_computation(self) -> None:
        self.assertEqual(tuple(self.outputs), p1b.OUTPUTS)
        for relative, text in self.outputs.items():
            with self.subTest(output=str(relative)):
                self.assertEqual((ROOT / relative).read_text(encoding="utf-8"), text)

    def test_two_computations_are_identical(self) -> None:
        again = p1b.render_outputs(p1b.compute(CLOSURE))
        self.assertEqual(again, self.outputs)

    def test_the_build_is_registered_in_the_clock_frozen_determinism_test(self) -> None:
        from tests.unit import test_generated_date_determinism as determinism

        registered = {g.task: g for g in determinism.GENERATORS}
        self.assertIn(p1b.TASK, registered)
        self.assertEqual(registered[p1b.TASK].outputs, p1b.OUTPUTS)

    # -- the handoff is derived from the frozen design ----------------------------

    def test_every_carried_phrase_is_in_its_frozen_section(self) -> None:
        for field, phrase, heading in p1b.FROZEN_PHRASES:
            with self.subTest(field=field):
                section = " ".join(p1b._section(self.selection, heading).split())
                self.assertIn(phrase, section)

    def test_a_removed_frozen_phrase_stops_the_build(self) -> None:
        _field, _phrase, _heading = p1b.FROZEN_PHRASES[0]
        tampered = self.selection.replace("MPA 1 µM", "MPA 2 µM")
        self.assertNotEqual(tampered, self.selection)
        with self.assertRaisesRegex(RuntimeError, "no longer states"):
            p1b.check_frozen_phrases(tampered)

    def test_handoff_doses_and_timing_match_the_frozen_arm_and_the_protocol(
        self,
    ) -> None:
        rows = {r["row_id"]: r for r in _tsv(p1b.OUT_HANDOFF_TSV)}
        minus = rows["H01"]
        for dose in ("MPA 1 uM", "cAMP 250 uM (0.25 mM)", "XAV939 10 uM", "E2 omitted"):
            self.assertIn(dose, minus["reagent_dose"])
        self.assertIn("days 0-2 E2-only priming (10 nM E2", minus["protocol_timing"])
        self.assertIn("days 2-6", minus["protocol_timing"])
        cocktail = self.result["doses"]["cocktail_note"]
        for dose in ("10 nM E2", "1 uM MPA", "250 uM cAMP", "10 uM XAV939"):
            self.assertIn(dose, cocktail)
            self.assertIn(dose.split()[-1], rows["H06"]["reagent_dose"])

    def test_the_human_readable_handoff_carries_the_frozen_arm_verbatim(self) -> None:
        md = (ROOT / p1b.OUT_HANDOFF_MD).read_text(encoding="utf-8")
        arm = "MPA 1 µM + cAMP 0.25 mM + XAV939 10 µM, E2 omitted"
        self.assertIn(arm, " ".join(p1b._section(self.selection, "## 12.").split()))
        self.assertIn(f"**{arm}**", md)
        self.assertIn("**3 planned source-pair blocks.**", md)
        self.assertIn("days 2, 4, 6", md)

    def test_a_divergent_handoff_value_stops_the_build(self) -> None:
        md = self.outputs[p1b.OUT_HANDOFF_MD]
        rows = [dict(r) for r in self.result["handoff"]]
        notes = self.result["doses"]
        carried = self.result["carried"]
        rows[0]["reagent_dose"] = rows[0]["reagent_dose"].replace(
            "MPA 1 uM", "MPA 2 uM"
        )
        with self.assertRaisesRegex(RuntimeError, "differ from config/protocols.yaml"):
            p1b.check_handoff_against_frozen(rows, md, carried, notes)
        moved = [dict(r) for r in self.result["handoff"]]
        moved[0]["compartment"] = "stromal (bottom outlet)"
        with self.assertRaisesRegex(RuntimeError, "outside the top outlet"):
            p1b.check_handoff_against_frozen(moved, md, carried, notes)

    def test_every_dose_bearing_row_is_validated_and_comparator_mutations_fail(
        self,
    ) -> None:
        md = self.outputs[p1b.OUT_HANDOFF_MD]
        notes, carried = self.result["doses"], self.result["carried"]
        p1b.check_handoff_against_frozen(self.result["handoff"], md, carried, notes)
        mutations = (
            ("H06", "E2 10 nM", "E2 100 nM"),
            ("H06", "XAV939 10 uM", "XAV939 0 uM"),
            ("H07", "cAMP 250 uM", "cAMP 1 uM"),
            ("H06", "MPA 1 uM", "MPA 99 uM"),
            ("H08", "E2 10 nM", "E2 100 nM"),
            ("H03", "XAV939 10 uM", "XAV939 0 uM"),
            ("H01", "; E2 omitted", " + E2 10 nM"),
        )
        for row_id, old, new in mutations:
            with self.subTest(row=row_id, mutation=new):
                rows = [dict(r) for r in self.result["handoff"]]
                target = next(r for r in rows if r["row_id"] == row_id)
                self.assertIn(old, target["reagent_dose"])
                target["reagent_dose"] = target["reagent_dose"].replace(old, new)
                with self.assertRaises(RuntimeError):
                    p1b.check_handoff_against_frozen(rows, md, carried, notes)
        bad_md = md.replace("| E2 10 nM + MPA 1 uM", "| E2 100 nM + MPA 1 uM", 1)
        self.assertNotEqual(bad_md, md)
        with self.assertRaisesRegex(RuntimeError, "full-cocktail doses"):
            p1b.check_handoff_against_frozen(
                self.result["handoff"], bad_md, carried, notes
            )
        expected = p1b.expected_doses(notes)
        self.assertEqual(
            expected["full_cocktail"],
            {"E2": 0.01, "MPA": 1.0, "cAMP": 250.0, "XAV939": 10.0},
        )
        self.assertEqual(
            expected["minus_E2"], {"MPA": 1.0, "cAMP": 250.0, "XAV939": 10.0}
        )
        self.assertEqual(expected["priming"], {"E2": 0.01})

    def test_every_frozen_phrase_is_rendered_into_the_handoff(self) -> None:
        md = (ROOT / p1b.OUT_HANDOFF_MD).read_text(encoding="utf-8")
        for _field, phrase, _heading in p1b.FROZEN_PHRASES:
            self.assertIn(phrase, md)

    def test_ordinal_claim_is_stated_per_assignment_as_it_holds(self) -> None:
        claim = self.summary["premises"]["ordinal_claim"]
        self.assertFalse(claim["untreated_on_in_any_assignment"])
        self.assertFalse(claim["mifepristone_on_in_any_assignment"])
        gate = {r["criterion_id"]: r for r in _tsv(p1b.OUT_EXIT_GATE)}
        self.assertIn("holds only in expectation", gate["R3c"]["current_claim"])
        self.assertNotIn("holds in every latent", gate["R3c"]["current_claim"])
        self.assertNotIn("survives every latent", gate["E4"]["what_was_tested"])

    def test_handoff_compartments_assays_and_times(self) -> None:
        rows = _tsv(p1b.OUT_HANDOFF_TSV)
        by = {(r["arm"], r["assay"], r["timepoint"]): r for r in rows}
        self.assertEqual(
            by[("minus_E2", "PAEP ELISA", "day 6 (primary, G7)")]["compartment"],
            "epithelial (top outlet)",
        )
        self.assertEqual(
            by[("minus_E2", "IGFBP-1 ELISA", "day 6 (primary, G7)")]["compartment"],
            "stromal (bottom outlet)",
        )
        self.assertEqual(
            by[("minus_E2", "PRL ELISA", "day 3 and day 6")]["compartment"],
            "stromal (bottom outlet)",
        )
        assays = {r["assay"] for r in rows}
        self.assertEqual(
            assays,
            {
                "PAEP ELISA",
                "IGFBP-1 ELISA",
                "PRL ELISA",
                "IGFBP-1 and PRL ELISA",
            },
        )
        for row in rows:
            with self.subTest(row=row["row_id"]):
                self.assertIn(
                    "source-pair block (3 planned blocks", row["biological_replicate"]
                )
                self.assertIn(
                    "days 2, 4 and 6 in BOTH channels", row["integrity_control"]
                )
        self.assertIn("day 2", {r["timepoint"] for r in rows})

    def test_technical_duplicate_is_minus_e2_only_and_never_raises_n(self) -> None:
        for row in _tsv(p1b.OUT_HANDOFF_TSV):
            with self.subTest(row=row["row_id"]):
                if (
                    "technical duplicate of this arm"
                    in row["technical_replicate_policy"]
                ):
                    self.assertTrue(row["arm"].startswith("minus_E2"))
                    self.assertIn(
                        "never raises biological n", row["technical_replicate_policy"]
                    )

    def test_bands_are_recomputed_and_match_the_frozen_quotes(self) -> None:
        bands = self.result["bands"]
        self.assertEqual(bands["paep_e2_only"]["n"], 5)
        self.assertEqual(bands["paep_full_cocktail"]["n"], 5)
        self.assertLess(
            bands["paep_e2_only"]["max"], bands["paep_full_cocktail"]["min"]
        )
        self.assertGreaterEqual(bands["igfbp1_day0"]["exact_zeros"], 1)
        self.assertGreaterEqual(bands["igfbp1_day6"]["exact_zeros"], 1)
        self.assertFalse(bands["paep_rows_carry_a_sampling_day"])
        self.assertIn(
            "E2-only 10,165–25,470 pg/mL and full cocktail 178,072–585,609 pg/mL",
            " ".join(self.selection.split()),
        )

    def test_frozen_decision_tree_is_carried_verbatim(self) -> None:
        tree = p1b.frozen_decision_tree(self.selection)
        md = (ROOT / p1b.OUT_HANDOFF_MD).read_text(encoding="utf-8")
        for row in tree:
            with self.subTest(paep=row["paep"], igfbp1=row["igfbp1"]):
                self.assertIn(
                    f"| {row['paep']} | {row['igfbp1']} | {row['supported']} | {row['model_action']} |",
                    md,
                )

    def test_first_row_licenses_dependence_not_mechanism(self) -> None:
        md = (ROOT / p1b.OUT_HANDOFF_MD).read_text(encoding="utf-8")
        self.assertIn(
            "establishes sustained E2 dependence of the epithelial secretory programme, not the mechanism.",
            md,
        )
        self.assertEqual(
            self.result["table_c"]["SEC-a"], self.result["table_c"]["SEC-e"]
        )

    def test_prl_never_decides_a_call(self) -> None:
        for row in _tsv(p1b.OUT_HANDOFF_TSV):
            with self.subTest(row=row["row_id"]):
                if row["assay"] == "PRL ELISA":
                    self.assertIn(
                        "never changes the stromal call", row["interpretation_rule"]
                    )
                if row["assay"] == "IGFBP-1 ELISA" and "primary" in row["timepoint"]:
                    self.assertIn(
                        "PRL cannot rescue", row["failure_indeterminate_rule"]
                    )
        self.assertNotIn(
            "convincingly ON", (ROOT / p1b.OUT_HANDOFF_TSV).read_text(encoding="utf-8")
        )

    # -- the pre-run addendum ----------------------------------------------------

    def test_addendum_does_not_edit_the_frozen_design(self) -> None:
        """The addendum lives in its own file; the frozen text keeps its digest."""
        self.assertEqual(
            _sha(ROOT / p1b.FROZEN_SELECTION), FROZEN_DIGESTS[str(p1b.FROZEN_SELECTION)]
        )
        self.assertNotIn("PRE_RUN_ADDENDUM", self.selection)

    # -- the pre-run interpretation contract (owner addenda, rounds 1 and 2) -----

    @property
    def b(self) -> dict[str, float]:
        return p1b.boundaries(self.result["bands"])

    def test_no_pre_run_question_is_open(self) -> None:
        self.assertEqual(p1b.RESIDUAL_QUESTIONS, ())
        self.assertEqual(self.summary["residual_pre_run_questions"], [])
        for relative in p1b.OUTPUTS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(output=str(relative)):
                self.assertNotRegex(
                    text,
                    r"(?i)unresolved|residual (pre-run )?question|open pre-run question",
                )

    def test_a_reintroduced_open_question_fails(self) -> None:
        with mock.patch.object(p1b, "RESIDUAL_QUESTIONS", (("RQ7", "open"),)):
            outputs = p1b.render_outputs(self.result)
        summary = json.loads(outputs[p1b.OUT_SUMMARY])
        self.assertNotEqual(
            summary["residual_pre_run_questions"],
            self.summary["residual_pre_run_questions"],
        )

    def test_the_boundaries_are_the_frozen_historical_values(self) -> None:
        bands = self.result["bands"]
        self.assertEqual(self.b["PAEP_ON_LOWER"], bands["paep_full_cocktail"]["min"])
        self.assertEqual(self.b["PAEP_LOW_UPPER"], bands["paep_e2_only"]["max"])
        self.assertEqual(
            self.b["IGFBP1_OFF_UPPER"], bands["igfbp1_day0"]["nonzero_max"]
        )
        self.assertEqual(self.b["IGFBP1_ON_LOWER"], bands["igfbp1_day6"]["nonzero_min"])
        self.assertEqual(
            self.b,
            {
                "PAEP_ON_LOWER": 178072.464,
                "PAEP_LOW_UPPER": 25469.5652,
                "IGFBP1_OFF_UPPER": 551.2605,
                "IGFBP1_ON_LOWER": 8118.142,
            },
        )
        self.assertEqual(self.summary["frozen_boundaries"], self.b)

    def test_no_operational_rule_uses_symmetric_out_of_band_gating(self) -> None:
        for relative in p1b.OUTPUTS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            if relative == p1b.OUT_ADDENDUM:
                for row in _tsv(relative):
                    if "CONTROL_OUT_OF_BAND" in row["decision"]:
                        self.assertTrue(
                            row["status"].startswith("SUPERSEDED"), row["gap_id"]
                        )
                continue
            with self.subTest(output=str(relative)):
                self.assertNotIn("CONTROL_OUT_OF_BAND", text)
                self.assertNotIn("systematically", text)

    def test_expected_state_controls_are_one_sided(self) -> None:
        b = self.b
        full_max = self.result["bands"]["paep_full_cocktail"]["max"]
        e2_min = self.result["bands"]["paep_e2_only"]["min"]
        d6_max = self.result["bands"]["igfbp1_day6"]["nonzero_max"]
        self.assertEqual(p1b.paep_on_control(full_max * 10, b), p1b.ON_CONFIRMED)
        self.assertEqual(p1b.paep_on_control(b["PAEP_ON_LOWER"], b), p1b.ON_CONFIRMED)
        self.assertEqual(
            p1b.paep_on_control(b["PAEP_ON_LOWER"] - 1, b), p1b.NOT_CONFIRMED
        )
        self.assertEqual(p1b.paep_low_control(e2_min / 10, b), p1b.LOW_CONFIRMED)
        self.assertEqual(p1b.paep_low_control(0.0, b), p1b.LOW_CONFIRMED)
        self.assertEqual(
            p1b.paep_low_control(b["PAEP_LOW_UPPER"] + 1, b), p1b.NOT_CONFIRMED
        )
        self.assertEqual(p1b.igfbp1_on_control(0.0, b), p1b.NOT_CONFIRMED)
        self.assertEqual(p1b.igfbp1_on_control(d6_max * 10, b), p1b.ON_CONFIRMED)
        self.assertEqual(
            p1b.igfbp1_on_control(b["IGFBP1_ON_LOWER"] - 1, b), p1b.NOT_CONFIRMED
        )

    def test_igfbp1_final_ordinal_rule(self) -> None:
        b = self.b
        d0_min = self.result["bands"]["igfbp1_day0"]["nonzero_min"]
        d6_max = self.result["bands"]["igfbp1_day6"]["nonzero_max"]
        self.assertEqual(p1b.igfbp1_call(0.0, b), p1b.INDETERMINATE_ZERO)
        self.assertNotEqual(p1b.igfbp1_call(0.0, b), p1b.GRADED)
        self.assertEqual(p1b.igfbp1_call(d0_min / 2, b), p1b.OFF)
        self.assertEqual(p1b.igfbp1_call(b["IGFBP1_OFF_UPPER"], b), p1b.OFF)
        self.assertEqual(p1b.igfbp1_call(1000.0, b), p1b.GRADED)
        self.assertEqual(p1b.igfbp1_call(b["IGFBP1_ON_LOWER"], b), p1b.ON)
        self.assertEqual(p1b.igfbp1_call(d6_max * 2, b), p1b.ON)

    def test_paep_frozen_three_band_rule(self) -> None:
        b = self.b
        self.assertEqual(p1b.paep_call(b["PAEP_ON_LOWER"], b), p1b.ON)
        self.assertEqual(p1b.paep_call(b["PAEP_LOW_UPPER"], b), p1b.OFF)
        self.assertEqual(p1b.paep_call(100000.0, b), p1b.GRADED)

    def _channel(self, **overrides):
        args = {
            "technical_ok": True,
            "day6_integrity": p1b.INTACT,
            "controls": (p1b.ON_CONFIRMED,),
            "state": p1b.OBSERVED,
            "value": 1000.0,
            "detection_limit": 5.0,
            "caller": p1b.igfbp1_call,
            "b": self.b,
        }
        args.update(overrides)
        return p1b.channel_outcome(**args)

    def test_precedence_and_prl_cannot_rescue(self) -> None:
        """Earlier levels win; PRL is not an input to any call."""
        import inspect

        self.assertEqual(
            self._channel(technical_ok=False, day6_integrity="COMPROMISED"),
            p1b.TECHNICAL_FAILURE,
        )
        self.assertEqual(
            self._channel(day6_integrity="COMPROMISED"), p1b.INTEGRITY_INVALID
        )
        self.assertEqual(
            self._channel(day6_integrity="INDETERMINATE"), p1b.INTEGRITY_INVALID
        )
        self.assertEqual(
            self._channel(controls=(p1b.NOT_CONFIRMED,)), p1b.NOT_CONFIRMED
        )
        self.assertEqual(
            self._channel(state=p1b.NO_DETECTABLE_SECRETION, value=0.0),
            p1b.INDETERMINATE_ZERO,
        )
        self.assertEqual(self._channel(), p1b.GRADED)
        for fn in (
            p1b.channel_outcome,
            p1b.igfbp1_call,
            p1b.igfbp1_on_control,
            p1b.sec_mapping,
        ):
            self.assertNotIn("prl", " ".join(inspect.signature(fn).parameters).lower())
        self.assertEqual(
            p1b.PRECEDENCE,
            (
                "technical validity",
                "compartment integrity",
                "contemporaneous expected-state confirmation",
                "molecular ordinal call",
                "SEC-class mapping",
            ),
        )

    def test_qc_indeterminates_never_map_to_a_class_and_graded_still_can(self) -> None:
        table_c = self.result["table_c"]
        for qc in p1b.QC_INDETERMINATE:
            with self.subTest(qc=qc):
                self.assertEqual(p1b.sec_mapping(qc, p1b.ON, table_c), p1b.NO_CLASS)
                self.assertEqual(p1b.sec_mapping(p1b.OFF, qc, table_c), p1b.NO_CLASS)
                self.assertEqual(p1b.sec_mapping(p1b.GRADED, qc, table_c), p1b.NO_CLASS)
        self.assertEqual(p1b.sec_mapping(p1b.GRADED, p1b.ON, table_c), p1b.GRADED)
        self.assertEqual(p1b.sec_mapping(p1b.OFF, p1b.ON, table_c), "SEC-a or SEC-e")
        self.assertEqual(p1b.sec_mapping(p1b.ON, p1b.ON, table_c), "SEC-b or SEC-c")

    def test_day3_cannot_rescue_a_day6_failure(self) -> None:
        import inspect

        params = set(inspect.signature(p1b.channel_outcome).parameters)
        self.assertIn("day6_integrity", params)
        self.assertFalse(any("day3" in p for p in params))
        rows = {r["row_id"]: r for r in _tsv(p1b.OUT_HANDOFF_TSV)}
        for row_id in ("H01", "H03"):
            self.assertIn(
                "day 3 cannot rescue it", rows[row_id]["failure_indeterminate_rule"]
            )
        for row_id in ("H06", "H07"):
            self.assertIn(
                "A day-3 value never gates (G7)",
                rows[row_id]["failure_indeterminate_rule"],
            )

    def test_pre_cocktail_paep_is_day0_and_day0_igfbp1_is_descriptive(self) -> None:
        rows = {r["row_id"]: r for r in _tsv(p1b.OUT_HANDOFF_TSV)}
        self.assertEqual(rows["H09"]["timepoint"], "day 0")
        self.assertIn("before E2 priming", rows["H09"]["protocol_timing"])
        self.assertIn("gates no call", rows["H09"]["interpretation_rule"])
        self.assertIn("DESCRIPTIVE", rows["H10"]["interpretation_rule"])
        self.assertIn("decides no call", rows["H10"]["failure_indeterminate_rule"])
        gating = {
            r["row_id"]
            for r in rows.values()
            if p1b.NOT_CONFIRMED in r["failure_indeterminate_rule"]
            and r["arm"] != "minus_E2"
        }
        self.assertEqual(gating, {"H06", "H07", "H08"})

    def test_integrity_is_locked_before_assay_values_are_revealed(self) -> None:
        md = (ROOT / p1b.OUT_HANDOFF_MD).read_text(encoding="utf-8")
        self.assertIn("locked before any PAEP/IGFBP-1/PRL value is revealed", md)
        for row in _tsv(p1b.OUT_HANDOFF_TSV):
            with self.subTest(row=row["row_id"]):
                self.assertIn(
                    "LOCKED before assay values are revealed", row["integrity_control"]
                )
        g3r = next(r for r in _tsv(p1b.OUT_ADDENDUM) if r["gap_id"] == "G3R")
        for field in (
            "image identifier",
            "channel",
            "day",
            "adjudicator",
            "timestamp/version",
        ):
            self.assertIn(field, g3r["decision"])

    def test_the_narrative_boundary_table_matches_the_summary(self) -> None:
        record = (ROOT / "docs/phase1b_closure_and_prospective_handoff.md").read_text(
            encoding="utf-8"
        )
        for name, value in self.summary["frozen_boundaries"].items():
            with self.subTest(boundary=name):
                self.assertIn(f"| {name} | {value:,} |", record)

    def test_addendum_rounds_are_complete_dated_and_owner_decided(self) -> None:
        rows = _tsv(p1b.OUT_ADDENDUM)
        self.assertEqual(
            [r["gap_id"] for r in rows],
            [f"G{i}" for i in range(1, 9)]
            + ["P0"]
            + [f"RQ{i}" for i in range(1, 7)]
            + ["G3R", "G4R"]
            + ["MS1", "SPB1", "AL1", "RAT1", "SPP1X"],
        )
        for row in rows:
            with self.subTest(gap=row["gap_id"]):
                self.assertEqual(
                    row["record_type"], "OWNER_DECISION / PRE_RUN_ADDENDUM"
                )
                self.assertEqual(row["decided_on"], "2026-09-24")
                self.assertIn(
                    row["frozen_text_it_resolves"], " ".join(self.selection.split())
                )
        decisions = {r["gap_id"]: r["decision"] for r in rows}
        self.assertIn("removed from classification entirely", decisions["G1"])
        self.assertIn("DAY 6 is the PRIMARY decision timepoint", decisions["G7"])
        self.assertIn("does NOT distinguish SEC-b from SEC-c", decisions["G8"])
        self.assertIn("DAY 0, before E2 priming", decisions["RQ2"])
        self.assertIn("descriptive reference extrema", decisions["RQ5"])
        statuses = {r["gap_id"]: r["status"] for r in rows}
        self.assertTrue(statuses["G6"].startswith("SUPERSEDED_BY_RQ5"))

    # -- round 3: measurement states, unit, allocation, SPP1 --------------------

    def test_below_detection_never_becomes_off_and_states_stay_distinct(self) -> None:
        b, lod = self.b, 5.0
        labels = {
            state: p1b.measured(state, None if state != p1b.OBSERVED else 10.0, lod)
            for state in p1b.MEASUREMENT_STATES
        }
        self.assertEqual(labels[p1b.NO_DETECTABLE_SECRETION], p1b.INDETERMINATE_ZERO)
        self.assertEqual(labels[p1b.BELOW_DETECTION], p1b.INDETERMINATE_BELOW_DETECTION)
        self.assertEqual(labels[p1b.STATE_MISSING], p1b.MISSING)
        self.assertEqual(labels[p1b.STATE_TECHNICAL_FAILURE], p1b.TECHNICAL_FAILURE)
        self.assertEqual(labels[p1b.OBSERVED], 10.0)
        non_observed = [labels[s] for s in p1b.MEASUREMENT_STATES if s != p1b.OBSERVED]
        self.assertEqual(len(set(non_observed)), 4)
        for label in non_observed:
            self.assertIn(label, p1b.QC_INDETERMINATE)
        below = self._channel(state=p1b.BELOW_DETECTION, value=1.0, detection_limit=lod)
        self.assertEqual(below, p1b.INDETERMINATE_BELOW_DETECTION)
        self.assertNotEqual(below, p1b.OFF)
        self.assertEqual(
            p1b.sec_mapping(p1b.ON, below, self.result["table_c"]), p1b.NO_CLASS
        )
        self.assertEqual(
            p1b.igfbp1_call(1.0, b), p1b.OFF
        )  # only reachable if wrongly fed raw

    def test_only_an_observed_reportable_value_enters_the_classifier(self) -> None:
        with self.assertRaises(p1b.InconsistentRecord):
            p1b.measured(p1b.OBSERVED, 1.0, 5.0)
        with self.assertRaises(p1b.InconsistentRecord):
            p1b.measured(p1b.OBSERVED, None, 5.0)
        with self.assertRaises(p1b.InconsistentRecord):
            self._channel(state=p1b.OBSERVED, value=1.0, detection_limit=5.0)
        with self.assertRaises(p1b.InconsistentRecord):
            p1b.measured("imputed", 2.5, 5.0)
        self.assertEqual(
            self._channel(state=p1b.OBSERVED, value=100.0, detection_limit=5.0), p1b.OFF
        )

    def test_no_documented_assay_limit_prevents_classification(self) -> None:
        for lod in (None, 0.0):
            with self.subTest(lod=lod):
                with self.assertRaises(p1b.AssayLimitUndocumented):
                    p1b.measured(p1b.OBSERVED, 100.0, lod)
                with self.assertRaises(p1b.AssayLimitUndocumented):
                    self._channel(detection_limit=lod)
                with self.assertRaises(p1b.AssayLimitUndocumented):
                    p1b.confirm_control(
                        p1b.OBSERVED, 9000.0, lod, p1b.igfbp1_on_control, self.b
                    )
        template = _tsv(p1b.OUT_ASSAY_METADATA)
        self.assertEqual([r["analyte"] for r in template], ["PAEP", "IGFBP-1", "PRL"])
        with self.assertRaises(p1b.AssayLimitUndocumented):
            p1b.assay_limits(template)
        self.assertEqual(
            p1b.assay_limits(self._assay_rows()),
            {"PAEP": 7.5, "IGFBP-1": 7.5, "PRL": 7.5},
        )
        self.assertFalse(
            self.summary["operational_prerequisites"]["classification_ready"]
        )

    def test_controls_confirm_only_from_observed_values(self) -> None:
        b = self.b
        cc = p1b.confirm_control
        self.assertEqual(
            cc(p1b.NO_DETECTABLE_SECRETION, 0.0, 5.0, p1b.igfbp1_on_control, b),
            p1b.NOT_CONFIRMED,
        )
        self.assertEqual(
            cc(p1b.BELOW_DETECTION, None, 5.0, p1b.igfbp1_on_control, b),
            p1b.NOT_CONFIRMED,
        )
        self.assertEqual(
            cc(p1b.STATE_MISSING, None, 5.0, p1b.paep_on_control, b), p1b.MISSING
        )
        self.assertEqual(
            cc(p1b.OBSERVED, 9000.0, 5.0, p1b.igfbp1_on_control, b), p1b.ON_CONFIRMED
        )
        self.assertEqual(self._channel(controls=(p1b.MISSING,)), p1b.NOT_CONFIRMED)

    def test_source_pair_block_replaces_donor_in_the_execution_handoff(self) -> None:
        allowed = (
            "not a patient or donor",
            "**not** a patient or donor",
            "independent biological donors is not asserted",
        )
        md = (ROOT / p1b.OUT_HANDOFF_MD).read_text(encoding="utf-8")
        execution = md.split("## What is being tested", 1)[1]
        texts = {
            "md": execution,
            "tsv": (ROOT / p1b.OUT_HANDOFF_TSV).read_text(encoding="utf-8"),
        }
        for name, text in texts.items():
            for phrase in allowed:
                text = text.replace(phrase, "")
            with self.subTest(output=name):
                self.assertNotRegex(text, r"(?i)donor")
        self.assertIn("source-pair block", execution)
        cols = p1b.ALLOCATION_COLUMNS
        self.assertIn("epithelial_source_id", cols)
        self.assertIn("stromal_source_id", cols)
        self.assertIn("source_pair_block_id", cols)
        self.assertEqual(tuple(_tsv(p1b.OUT_ALLOCATION)[0]), cols)

    def _manifest(self):
        rows = []
        slot = 0
        for b_index, (block, epi, stro) in enumerate(
            (("SPB-1", "E1", "S1"), ("SPB-2", "E2", "S2"), ("SPB-3", "E3", "S3"))
        ):
            conditions = (
                ("full_cocktail", "minus_E2")
                if b_index % 2 == 0
                else ("minus_E2", "full_cocktail")
            )
            for condition in conditions:
                slot += 1
                rows.append(
                    {
                        "source_pair_block_id": block,
                        "epithelial_source_id": epi,
                        "stromal_source_id": stro,
                        "chip_id": f"{block}-{condition}",
                        "condition": condition,
                        "technical_duplicate_of": "",
                        "physical_position": f"P{slot}",
                        "processing_order": str(slot),
                        "allocation_method": p1b.RANDOMIZED,
                        "position_allocation_method": p1b.RANDOMIZED,
                        "order_allocation_method": p1b.RANDOMIZED,
                        "rng_seed_or_randomisation_record": f"seed 20260924 draw {slot}",
                        "allocated_at": "t",
                        "allocated_by": "x",
                    }
                )
        return rows

    def test_allocation_manifest_is_required_before_treatment(self) -> None:
        self.assertFalse(
            p1b.validate_manifest(_tsv(p1b.OUT_ALLOCATION))["treatment_may_start"]
        )
        self.assertFalse(
            self.summary["operational_prerequisites"]["treatment_may_start"]
        )
        good = p1b.validate_manifest(self._manifest())
        self.assertTrue(good["treatment_may_start"], good)
        self.assertTrue(good["independent_blocks_claimable"])
        incomplete = self._manifest()
        incomplete[0]["rng_seed_or_randomisation_record"] = p1b.PLACEHOLDER
        self.assertFalse(p1b.validate_manifest(incomplete)["treatment_may_start"])
        md = (ROOT / p1b.OUT_HANDOFF_MD).read_text(encoding="utf-8")
        self.assertIn("**before treatment starts**", md)

    def test_condition_assignment_must_be_randomised_with_a_record(self) -> None:
        for bad in (
            "not-randomized",
            "counterbalanced_hardware_constraint",
            "random",
            "",
        ):
            with self.subTest(allocation_method=bad):
                rows = self._manifest()
                for row in rows:
                    row["allocation_method"] = bad
                verdict = p1b.validate_manifest(rows)
                self.assertFalse(verdict["treatment_may_start"])
                self.assertTrue(
                    any("condition assignment must be" in e for e in verdict["errors"])
                )
        for bad in ("", "   "):
            rows = self._manifest()
            rows[2]["rng_seed_or_randomisation_record"] = bad
            self.assertFalse(p1b.validate_manifest(rows)["treatment_may_start"])

    def test_the_reviewers_non_randomised_manifest_is_rejected(self) -> None:
        """B12's counterexample: not randomised, identical positions, fixed order."""
        rows = self._manifest()
        for row in rows:
            row.update(
                allocation_method="not-randomized",
                physical_position="P1",
                processing_order="1",
            )
        verdict = p1b.validate_manifest(rows)
        self.assertFalse(verdict["treatment_may_start"])
        self.assertTrue(any("duplicate values" in e for e in verdict["errors"]))

    def test_positions_and_order_are_unique_and_well_formed(self) -> None:
        rows = self._manifest()
        rows[3]["physical_position"] = rows[0]["physical_position"]
        self.assertFalse(p1b.validate_manifest(rows)["treatment_may_start"])
        rows = self._manifest()
        rows[1]["processing_order"] = "first"
        self.assertFalse(p1b.validate_manifest(rows)["treatment_may_start"])
        rows = self._manifest()
        rows[1]["physical_position"] = ""
        self.assertFalse(p1b.validate_manifest(rows)["treatment_may_start"])
        rows = self._manifest()
        rows[0]["position_allocation_method"] = "fixed"
        self.assertFalse(p1b.validate_manifest(rows)["treatment_may_start"])

    def test_counterbalancing_is_only_for_layout_and_must_vary_across_blocks(
        self,
    ) -> None:
        varied = self._manifest()
        for row in varied:
            row["order_allocation_method"] = p1b.COUNTERBALANCED
            row["position_allocation_method"] = p1b.COUNTERBALANCED
        self.assertTrue(
            p1b.validate_manifest(varied)["treatment_may_start"],
            p1b.validate_manifest(varied),
        )
        flat = self._manifest()
        slot = 0
        for block in ("SPB-1", "SPB-2", "SPB-3"):
            for condition in ("full_cocktail", "minus_E2"):
                slot += 1
                row = next(
                    r
                    for r in flat
                    if r["source_pair_block_id"] == block
                    and r["condition"] == condition
                )
                row.update(
                    physical_position=f"P{slot}",
                    processing_order=str(slot),
                    order_allocation_method=p1b.COUNTERBALANCED,
                )
        verdict = p1b.validate_manifest(flat)
        self.assertFalse(verdict["treatment_may_start"])
        self.assertTrue(
            any("identical within-block layout" in e for e in verdict["errors"])
        )
        self.assertNotIn(p1b.COUNTERBALANCED, (p1b.RANDOMIZED,))
        self.assertEqual(p1b.LAYOUT_METHODS, (p1b.RANDOMIZED, p1b.COUNTERBALANCED))

    def test_assay_limits_must_be_finite_and_positive(self) -> None:
        for bad in ("0", "0.0", "-5", "nan", "NaN", "inf", "-inf", "five"):
            with self.subTest(limit=bad):
                rows = [dict(r, detection_limit_pg_ml=bad) for r in self._assay_rows()]
                with self.assertRaises(p1b.AssayLimitUndocumented):
                    p1b.assay_limits(rows)
        for bad in (float("nan"), float("inf"), -1.0):
            with self.assertRaises(p1b.AssayLimitUndocumented):
                p1b.measured(p1b.OBSERVED, 100.0, bad)

    def _assay_rows(self):
        return [
            {
                "analyte": analyte,
                "assay_run_id": f"RUN-{analyte}",
                "detection_limit_pg_ml": "7.5",
                "limit_source": "kit certificate",
                "recorded_at": "t",
                "recorded_by": "x",
            }
            for analyte in ("PAEP", "IGFBP-1", "PRL")
        ]

    def test_assay_metadata_must_be_complete(self) -> None:
        self.assertEqual(p1b.REQUIRED_ANALYTES, ("PAEP", "IGFBP-1", "PRL"))
        rows = self._assay_rows()
        cases = {
            "missing analyte": rows[:2],
            "duplicate analyte": rows + [dict(rows[0])],
            "unexpected analyte": rows + [dict(rows[0], analyte="SPP1")],
            "renamed analyte": [dict(rows[0], analyte="SPP1")] + rows[1:],
        }
        for field in (
            "assay_run_id",
            "detection_limit_pg_ml",
            "limit_source",
            "recorded_at",
            "recorded_by",
        ):
            for blank in ("", "  ", p1b.PLACEHOLDER):
                bad = [dict(r) for r in rows]
                bad[1][field] = blank
                cases[f"{field}={blank!r}"] = bad
        for name, bad in cases.items():
            with (
                self.subTest(case=name),
                self.assertRaises(p1b.AssayLimitUndocumented),
            ):
                p1b.assay_limits(bad)

    def test_observed_values_must_be_finite(self) -> None:
        b = self.b
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=bad):
                with self.assertRaises(p1b.InconsistentRecord):
                    p1b.measured(p1b.OBSERVED, bad, 5.0)
                with self.assertRaises(p1b.InconsistentRecord):
                    self._channel(
                        state=p1b.OBSERVED,
                        value=bad,
                        detection_limit=5.0,
                        caller=p1b.igfbp1_call,
                    )
                with self.assertRaises(p1b.InconsistentRecord):
                    self._channel(
                        state=p1b.OBSERVED,
                        value=bad,
                        detection_limit=5.0,
                        caller=p1b.paep_call,
                    )
                with self.assertRaises(p1b.InconsistentRecord):
                    p1b.confirm_control(p1b.OBSERVED, bad, 5.0, p1b.paep_on_control, b)
        # the raw classifiers would call +inf ON, which is why it must never reach them
        self.assertEqual(p1b.igfbp1_call(float("inf"), b), p1b.ON)

    def _with_duplicate(self, rows, block="SPB-1", of=None, slot="P99", order="99"):
        primary = next(
            r
            for r in rows
            if r["source_pair_block_id"] == block and r["condition"] == "minus_E2"
        )
        rows.append(
            dict(
                primary,
                chip_id=f"{block}-minus_E2-dup",
                technical_duplicate_of=primary["chip_id"] if of is None else of,
                physical_position=slot,
                processing_order=order,
            )
        )
        return rows

    def test_manifest_requires_the_complete_planned_design(self) -> None:
        self.assertEqual(p1b.PLANNED_BLOCKS, ("SPB-1", "SPB-2", "SPB-3"))
        ok = self._with_duplicate(self._manifest())
        self.assertTrue(
            p1b.validate_manifest(ok)["treatment_may_start"], p1b.validate_manifest(ok)
        )
        base = self._manifest()
        cases = {
            "one block": [r for r in base if r["source_pair_block_id"] == "SPB-1"],
            "missing block": [r for r in base if r["source_pair_block_id"] != "SPB-3"],
            "extra block": base
            + [
                dict(
                    r,
                    source_pair_block_id="SPB-4",
                    chip_id=r["chip_id"] + "-4",
                    physical_position=r["physical_position"] + "x",
                    processing_order=str(50 + i),
                )
                for i, r in enumerate(base[:2])
            ],
        }
        for field in (
            "epithelial_source_id",
            "stromal_source_id",
            "chip_id",
            "allocated_at",
            "allocated_by",
            "source_pair_block_id",
        ):
            rows = [dict(r) for r in base]
            for row in rows:
                if row["source_pair_block_id"] == "SPB-2":
                    row[field] = ""
            cases[f"blank {field}"] = rows
        rows = [dict(r) for r in base]
        rows[3]["chip_id"] = rows[0]["chip_id"]
        cases["duplicate chip_id"] = rows
        cases["arbitrary technical_duplicate_of"] = self._with_duplicate(
            [dict(r) for r in base], of="whatever"
        )
        cases["duplicate of another block's chip"] = self._with_duplicate(
            [dict(r) for r in base], of="SPB-2-minus_E2"
        )
        two = self._with_duplicate([dict(r) for r in base])
        two = self._with_duplicate(two, slot="P98", order="98")
        two[-1]["chip_id"] = "SPB-1-minus_E2-dup2"
        cases["two duplicates in one block"] = two
        for name, rows in cases.items():
            with self.subTest(case=name):
                self.assertFalse(
                    p1b.validate_manifest(rows)["treatment_may_start"], name
                )

    def test_both_condition_chips_of_a_block_share_the_source_pair(self) -> None:
        mixed = self._manifest()
        mixed[1]["stromal_source_id"] = "S9"
        verdict = p1b.validate_manifest(mixed)
        self.assertFalse(verdict["treatment_may_start"])
        self.assertTrue(
            any("do not share one source pair" in e for e in verdict["errors"])
        )
        missing_arm = [
            r
            for r in self._manifest()
            if not (
                r["source_pair_block_id"] == "SPB-2" and r["condition"] == "minus_E2"
            )
        ]
        self.assertFalse(p1b.validate_manifest(missing_arm)["treatment_may_start"])

    def test_source_reuse_is_visible_and_never_counted_independent(self) -> None:
        reused = self._manifest()
        for row in reused:
            if row["source_pair_block_id"] == "SPB-3":
                row["epithelial_source_id"] = "E1"
        verdict = p1b.validate_manifest(reused)
        self.assertEqual(verdict["reused_sources"]["epithelial"], ["E1"])
        self.assertFalse(verdict["independent_blocks_claimable"])

    def test_no_exchangeability_rate_or_historical_chip_count_remains(self) -> None:
        paths = list(p1b.OUTPUTS) + [
            Path("docs/phase1b_closure_and_prospective_handoff.md")
        ]
        for relative in paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(output=str(relative)):
                self.assertNotIn("2/(n+1)", text)
                self.assertNotRegex(text, r"(?<!day-)\b2/[0-9]+\b")
                self.assertNotRegex(
                    text, r"non-zero of [0-9]+ chips|of its [0-9]+ chips"
                )

    def test_spp1_is_not_exercised(self) -> None:
        rows = _tsv(p1b.OUT_HANDOFF_TSV)
        self.assertNotIn("H11", {r["row_id"] for r in rows})
        self.assertFalse(any("SPP1" in " ".join(r.values()) for r in rows))
        md = (ROOT / p1b.OUT_HANDOFF_MD).read_text(encoding="utf-8")
        self.assertNotIn("SPP1 ELISA", md)
        self.assertIn("not exercised", md)
        self.assertNotIn("spp1", {f for f, _p, _h in p1b.FROZEN_PHRASES})

    # -- claim ceilings match the contract --------------------------------------

    def test_contract_premises_match_calibration_and_observation_map(self) -> None:
        c = self.summary["premises"]["contract"]
        self.assertEqual(c["adhesion_role"], "diagnostic_ordinal")
        self.assertIs(c["magnitude_fitted"], False)
        self.assertTrue(c["no_quantitative_objective"])
        self.assertIs(c["calibrated_physical_time"], False)
        self.assertEqual(c["active_constraint_nodes"], ["E_PAEP"])
        self.assertEqual(c["active_diagnostic_nodes"], ["S_IGFBP1"])
        for mapping_id, row in c["prl_rows"].items():
            with self.subTest(prl=mapping_id):
                self.assertNotIn(
                    row["activation_status"], ("active_constraint", "active_diagnostic")
                )

    def test_claims_ledger_forbids_what_the_contract_forbids(self) -> None:
        claims = {r["claim_id"]: r for r in _tsv(p1b.OUT_CLAIMS)}
        may_not = " ".join(
            r["statement"] for r in claims.values() if r["permission"] == "MAY_NOT"
        )
        for forbidden in (
            "magnitude-fitted calibration",
            "mifepristone is a successful validation",
            "physical time",
            "PRL as a calibration or validation term",
            "patient-level variance",
            "Phase 1B is closed",
        ):
            self.assertIn(forbidden, may_not)
        may = " ".join(
            r["statement"] for r in claims.values() if r["permission"] == "MAY"
        )
        self.assertNotIn("validat", may.replace("validation", "").lower())

    def test_mifepristone_statement_matches_the_model_and_contract(self) -> None:
        mife = self.summary["premises"]["adhesion_arms"]["hormone_treated_mifepristone"]
        self.assertEqual(mife["exact_fixed_point_probability"], 0)
        self.assertEqual((mife["observed_successes"], mife["observed_trials"]), (1, 8))
        self.assertEqual(mife["structural_verdict"], "structurally_contradicted")
        self.assertFalse(mife["rankable"])
        policy = p1b.load_calibration(ROOT)["adhesion_objective"][
            "structural_contradiction_policy"
        ]
        self.assertIn(
            "structurally_contradicted: observed 1/8", " ".join(policy.split())
        )
        gate = {r["criterion_id"]: r for r in _tsv(p1b.OUT_EXIT_GATE)}
        self.assertEqual(gate["R4b"]["status"], p1b.NOT_SATISFIED)
        self.assertEqual(gate["R4a"]["status"], p1b.NOT_APPLICABLE)
        self.assertEqual(gate["E3"]["status"], p1b.NOT_SATISFIED)
        self.assertIn("structurally_contradicted", gate["R4b"]["current_claim"])
        self.assertIn("none", self.summary["mifepristone"]["validation_claim"])

    def test_ordinal_claim_holds_on_the_adopted_model(self) -> None:
        arms = self.summary["premises"]["adhesion_arms"]
        u, h, m = (
            arms[k]["exact_fixed_point_probability"]
            for k in ("untreated", "hormone_treated", "hormone_treated_mifepristone")
        )
        self.assertTrue(u < h > m)
        self.assertTrue(
            self.summary["premises"]["ordinal_claim"]["holds_on_adopted_model"]
        )

    def test_a_moved_premise_stops_the_build(self) -> None:
        premises = json.loads(json.dumps(self.result["premises"]))
        premises["adhesion_arms"]["hormone_treated_mifepristone"][
            "structural_verdict"
        ] = "consistent"
        with self.assertRaisesRegex(RuntimeError, "AUDIT_PREMISE_MOVED"):
            p1b.check_premises(premises)

    # -- the status is derived ---------------------------------------------------

    def test_overall_status_is_recomputed_from_the_committed_rows(self) -> None:
        rows = _tsv(p1b.OUT_EXIT_GATE)
        self.assertEqual(
            p1b.derive_overall_status(rows), self.summary["phase1b_overall_status"]
        )
        self.assertEqual(self.summary["phase1b_overall_status"], p1b.BLOCKED)
        self.assertEqual(
            sorted(self.summary["unmet_exit_criteria_without_scheduled_route"]),
            ["E1", "E2", "E3", "E4"],
        )

    def test_the_rule_reaches_all_three_outcomes(self) -> None:
        base = [dict(r) for r in _tsv(p1b.OUT_EXIT_GATE)]
        closed = [
            dict(r, status=p1b.SATISFIED) if r["kind"] == "exit_gate" else r
            for r in base
        ]
        self.assertEqual(p1b.derive_overall_status(closed), p1b.CLOSED)
        partial = [
            dict(r, unblock_route=p1b.PROSPECTIVE_DATA)
            if r["kind"] == "exit_gate"
            else r
            for r in base
        ]
        self.assertEqual(p1b.derive_overall_status(partial), p1b.PARTIAL)
        roadmap_only = [
            dict(r, status=p1b.SATISFIED)
            if r["kind"] == "exit_gate"
            else dict(r, status=p1b.NOT_SATISFIED, unblock_route=p1b.NO_SCHEDULED_ROUTE)
            for r in base
        ]
        self.assertEqual(p1b.derive_overall_status(roadmap_only), p1b.CLOSED)

    def test_the_hand_written_record_and_roadmap_agree_with_the_audit(self) -> None:
        """The narrative's status table is read back against the generated TSV."""
        record = (ROOT / "docs/phase1b_closure_and_prospective_handoff.md").read_text(
            encoding="utf-8"
        )
        statuses = {r["criterion_id"]: r["status"] for r in _tsv(p1b.OUT_EXIT_GATE)}
        table = {}
        for line in record.splitlines():
            cells = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
            if len(cells) == 3 and cells[0] in statuses:
                table[cells[0]] = cells[2]
        self.assertEqual(table, statuses)
        overall = self.summary["phase1b_overall_status"]
        self.assertIn(f"**Status: Phase 1B is {overall}", record)
        roadmap = p1b.roadmap_phase1b(ROOT)
        self.assertIn(f"**Status (audit of 2026-09-24): {overall}.**", roadmap)

    def test_every_row_quotes_the_roadmap_and_cites_existing_artifacts(self) -> None:
        section = " ".join(p1b.roadmap_phase1b(ROOT).split())
        for row in _tsv(p1b.OUT_EXIT_GATE):
            with self.subTest(criterion=row["criterion_id"]):
                self.assertIn(row["criterion_verbatim"], section)
                self.assertIn(row["status"], p1b.STATUSES)
                for cited in row["evidence_artifacts"].split(";"):
                    path = cited.strip().split(" ")[0]
                    if "/" in path:
                        self.assertTrue((ROOT / path).exists(), path)
        for row in _tsv(p1b.OUT_SENSITIVITY):
            for cited in row["artifacts"].split(";"):
                path = cited.strip().split(" ")[0]
                if "/" in path:
                    with self.subTest(artifact=path):
                        self.assertTrue((ROOT / path).exists(), path)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
