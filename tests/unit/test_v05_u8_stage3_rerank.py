"""U8: the frozen Stage-3 selection, recomputed against adopted v0.5.1.

What these guards hold, and why each one exists:

* The frozen v0.4 artifacts are byte-for-byte what they were, and the default
  Stage-3 generator still regenerates them -- so parameterising the model
  version did not move the historical result.
* The rerank reads v0.5.1 and never writes a model, and it creates no model
  version.
* The scoring contract is the frozen one: readout tiers from
  `config/observation_model_map.tsv` and from nothing else, and
  `config/candidate_score.yaml` never opened -- proven by recording file opens,
  not by grepping the source.
* The answer is an output. A rerank whose premises moved must say
  `READJUDICATION_REQUIRED`, and a test drives that branch, so the carried-over
  ordering is not something the code could return regardless.
* The D1 condition is read from the machine-readable scRNA findings and carried,
  and the U6b MUC1 catalogue stays out of the Stage-3 fork set.
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

from dt_adoc.experiments import stage3_design
from dt_adoc.experiments import u8_stage3_rerank as u8
from dt_adoc.experiments.stage3_design import (
    EXPERIMENTS,
    FORKS,
    evaluate,
    render,
    render_tables,
)
from dt_adoc.experiments.variant_discrimination import _readout_tier
from dt_adoc.reporting.identifiability import parse_bnd_rules, repo_root, resolve_model

ROOT = repo_root()

#: Pinned literals, so a frozen artifact cannot be edited and its recorded digest
#: restated to match. Last changed by `1facb8f`, before any v0.5 unit.
FROZEN_DIGESTS = {
    "docs/experiments/stage3_experiment_design.tsv": "987d75644925346fab73e7251067094d04c01883af783a83c3775705b444ee74",
    "docs/experiments/stage3_experiment_design.md": "7368b1f85007f677cd16c5f308d9571f9573a83771b3dfdb2bb34b593b068520",
    "docs/experiments/stage3_decision_tables.md": "a2cc7291adfaf130f79f345201a30556ab16c9391c8598315a5735d6b0c3305b",
    "docs/stage3_experiment_selection.md": "e6a5fa558bede27f20b329cfbfe7bd3ec90d4d41c0f5091ed52e3dd4cbdb113c",
}

MODEL_DIRECTORIES = {
    "adoc-literature-superset-v0.3.0",
    "adoc-literature-superset-v0.4.0",
    "adoc-literature-superset-v0.5.0",
    "adoc-literature-superset-v0.5.1",
}

#: The frozen fork set, class by class. U8 reruns this question; it neither
#: adds a class (U6b's MUC1 family is catalogue-only) nor drops one.
FROZEN_FORKS = {
    "SEC": ["SEC-a", "SEC-b", "SEC-c", "SEC-d", "SEC-e"],
    "CAMP": ["CAMP-a", "CAMP-b"],
    "HH": ["HH-a", "HH-b"],
    "GP130": ["GP130-a", "GP130-b"],
    "CD98": ["CD98-a", "CD98-b", "CD98-c", "CD98-x"],
    "PC6": ["PC6-a", "PC6-b"],
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_digests(directory: Path) -> dict[str, str]:
    return {
        str(p.relative_to(ROOT)): _sha(p)
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def _tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


class _OpenRecorder:
    """Records every path opened through `open`/`io.open`, and the mode."""

    def __init__(self) -> None:
        self.opened: list[tuple[Path, str]] = []
        self._real = builtins.open

    def __call__(self, file, mode="r", *args, **kwargs):
        if isinstance(file, (str, Path)):
            self.opened.append((Path(file).resolve(), mode))
        return self._real(file, mode, *args, **kwargs)


class U8RerankTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.models_before = _tree_digests(ROOT / "models")
        recorder = _OpenRecorder()
        with mock.patch("builtins.open", recorder), mock.patch("io.open", recorder):
            cls.result = u8.compute(ROOT)
        cls.opened = recorder.opened
        cls.summary = cls.result["summary"]

    # -- the frozen reference --------------------------------------------------

    def test_frozen_v04_artifacts_are_byte_identical(self) -> None:
        for relative, digest in FROZEN_DIGESTS.items():
            with self.subTest(artifact=relative):
                self.assertEqual(_sha(ROOT / relative), digest)
                self.assertEqual(self.summary["frozen_artifacts"][relative], digest)

    def test_the_default_generator_still_regenerates_the_frozen_artifacts(self) -> None:
        """Parameterising the version must leave the historical task byte-exact."""
        self.assertEqual(stage3_design.MODEL_VERSION, u8.FROZEN_VERSION)
        report = evaluate(ROOT)
        self.assertEqual(report["model_version"], "adoc-literature-superset-v0.4.0")
        self.assertEqual(
            u8._tsv_text(report),
            (ROOT / stage3_design.OUT_TSV).read_text(encoding="utf-8"),
        )
        self.assertEqual(
            render(report), (ROOT / stage3_design.OUT_MD).read_text(encoding="utf-8")
        )
        self.assertEqual(
            render_tables(report, ROOT),
            (ROOT / stage3_design.OUT_TABLES).read_text(encoding="utf-8"),
        )

    def test_the_v04_tables_refuse_to_render_for_another_model(self) -> None:
        """Their prose argues about v0.4 by name; a v0.5 copy would misstate it."""
        with self.assertRaises(ValueError):
            render_tables(self.result["adopted"], ROOT)

    def test_a_drifted_frozen_reference_stops_the_rerank(self) -> None:
        real = u8._tsv_text

        def drifted(report: dict) -> str:
            text = real(report)
            if report["model_version"] == u8.FROZEN_VERSION:
                return text + "drift\n"
            return text

        with (
            mock.patch.object(u8, "_tsv_text", drifted),
            self.assertRaises(RuntimeError),
        ):
            u8.compute(ROOT)

    # -- models are read, never written ----------------------------------------

    def test_no_model_is_modified_and_none_is_created(self) -> None:
        self.assertEqual(_tree_digests(ROOT / "models"), self.models_before)
        # The computation created nothing (digests above). Later, explicitly
        # versioned models may exist beside these (dt_adoc.closure_replay).
        self.assertTrue(
            MODEL_DIRECTORIES
            <= {p.name for p in (ROOT / "models/superset").iterdir() if p.is_dir()}
        )
        models = (ROOT / "models").resolve()
        writes = [
            p
            for p, mode in self.opened
            if p.is_relative_to(models) and set(mode) & set("wax+")
        ]
        self.assertEqual(writes, [])

    def test_compute_writes_nothing_at_all(self) -> None:
        writes = [p for p, mode in self.opened if set(mode) & set("wax+")]
        self.assertEqual(writes, [])

    def test_the_adopted_model_is_what_was_read(self) -> None:
        spec = resolve_model(u8.ADOPTED_VERSION, ROOT)
        self.assertEqual(
            self.summary["models"][u8.ADOPTED_VERSION]["network_bnd_sha256"],
            _sha(spec.network_bnd),
        )
        self.assertIn(spec.network_bnd.resolve(), {p for p, _ in self.opened})

    def test_every_model_and_config_input_read_is_hash_recorded(self) -> None:
        """Configuration lineage: whatever the computation opens under `models/`
        or `config/` must appear, with its current digest, in the summary."""
        recorded: dict[str, str] = {}
        for version in (u8.FROZEN_VERSION, u8.ADOPTED_VERSION):
            recorded.update(self.summary["models"][version]["inputs_sha256"])
        root = ROOT.resolve()
        opened = {
            str(p.relative_to(root))
            for p, mode in self.opened
            if p.is_relative_to(root)
            and p.relative_to(root).parts[0] in {"models", "config"}
            and p.is_file()
        }
        opened.discard(str(u8.SCRNA_MAP))  # recorded under scoring_contract
        # The model registry opens every version's provenance.toml to locate
        # directories; only the two versions compared enter any calculation.
        compared = {u8.FROZEN_VERSION, u8.ADOPTED_VERSION}
        opened = {
            p
            for p in opened
            if not (
                p.endswith("/provenance.toml") and Path(p).parent.name not in compared
            )
        }
        self.assertTrue(opened)
        self.assertLessEqual(opened, set(recorded))
        for relative, digest in recorded.items():
            with self.subTest(input=relative):
                self.assertEqual(_sha(ROOT / relative), digest)
        for version in (u8.FROZEN_VERSION, u8.ADOPTED_VERSION):
            inputs = self.summary["models"][version]["inputs_sha256"]
            self.assertIn("config/calibration.yaml", inputs)
            self.assertIn(f"models/superset/{version}/baseline.cfg", inputs)
            self.assertTrue(
                any(
                    k.startswith(f"models/superset/{version}/conditions/")
                    for k in inputs
                )
            )

    # -- the scoring contract --------------------------------------------------

    def test_candidate_score_is_never_opened(self) -> None:
        opened = {p for p, _ in self.opened}
        self.assertNotIn((ROOT / u8.NOT_READ_CANDIDATE_SCORE).resolve(), opened)
        self.assertIn((ROOT / u8.OBSERVATION_MAP).resolve(), opened)
        self.assertFalse(self.summary["scoring_contract"]["candidate_score_yaml_read"])

    def test_readout_tiers_come_from_the_observation_map_and_match_frozen(self) -> None:
        expected = {
            n: t
            for n, (t, _) in _readout_tier(ROOT).items()
            if n in self.result["frozen"]["readout_tiers"]
        }
        recorded = self.summary["scoring_contract"]["readout_tiers"]
        self.assertEqual(recorded, dict(sorted(expected.items())))
        self.assertEqual(
            self.result["frozen"]["readout_tiers"],
            self.result["adopted"]["readout_tiers"],
        )
        self.assertEqual(
            self.summary["scoring_contract"]["readout_tier_source_sha256"],
            _sha(ROOT / "config/observation_model_map.tsv"),
        )

    def test_scrna_cannot_promote_a_readout_tier(self) -> None:
        contract = self.summary["scoring_contract"]
        self.assertFalse(contract["scrna_can_promote_a_readout_tier"])
        statuses = {
            r["activation_status"].strip()
            for r in _tsv(ROOT / "config/scrna_observation_map.tsv")
        }
        self.assertEqual(sorted(statuses), contract["scrna_activation_statuses"])
        self.assertFalse(statuses & {"active_constraint", "active_diagnostic"})

    # -- the candidate set -----------------------------------------------------

    def test_candidate_experiments_and_forks_are_the_frozen_ones(self) -> None:
        frozen_rows = _tsv(ROOT / stage3_design.OUT_TSV)
        adopted_rows = _tsv(ROOT / u8.OUT_DESIGN_TSV)
        frozen_ids = list(dict.fromkeys(r["experiment"] for r in frozen_rows))
        self.assertEqual([e.experiment_id for e in EXPERIMENTS], frozen_ids)
        self.assertEqual(len(frozen_ids), 16)
        self.assertEqual(
            {f.fork_id: [k.class_id for k in f.classes] for f in FORKS}, FROZEN_FORKS
        )
        key = ("experiment", "fork", "left_class", "right_class")
        self.assertEqual(
            [tuple(r[k] for k in key) for r in frozen_rows],
            [tuple(r[k] for k in key) for r in adopted_rows],
        )

    def test_u6b_muc1_variants_are_not_stage3_mechanisms(self) -> None:
        iso = self.summary["u6b_isolation"]
        self.assertEqual(iso["stage3_nodes_touching_catalog"], [])
        self.assertEqual(
            set(iso["catalog_statuses"]), {"catalog_only", "reference_only"}
        )
        catalog_nodes = {r["node_id"] for r in _tsv(ROOT / u8.U6B_CATALOG)}
        for fork in FORKS:
            for klass in fork.classes:
                self.assertFalse(set(klass.overrides) & catalog_nodes, klass.class_id)
                self.assertFalse(set(klass.added_free) & catalog_nodes, klass.class_id)
        for experiment in EXPERIMENTS:
            touched = set(experiment.input_overrides) | set(experiment.clamps)
            self.assertFalse(touched & catalog_nodes, experiment.experiment_id)
        adopted = parse_bnd_rules(resolve_model(u8.ADOPTED_VERSION, ROOT).network_bnd)
        frozen = parse_bnd_rules(resolve_model(u8.FROZEN_VERSION, ROOT).network_bnd)
        # The split's new nodes do not exist in the adopted model, and the MUC1
        # rule it would replace is still the frozen one.
        self.assertFalse({"E_MUC1_ABUNDANCE", "E_MUC1_LOCAL_CLEARANCE"} & set(adopted))
        self.assertEqual(adopted["E_MUC1_BARRIER"], frozen["E_MUC1_BARRIER"])

    # -- the three reported objects and their reconciliation -------------------

    def test_committed_outputs_are_a_fresh_deterministic_computation(self) -> None:
        again = u8.compute(ROOT)
        first = u8.render_outputs(self.result)
        self.assertEqual(first, u8.render_outputs(again))
        self.assertEqual(tuple(first), u8.OUTPUTS)
        for relative, text in first.items():
            with self.subTest(artifact=str(relative)):
                self.assertEqual(
                    (ROOT / relative).read_text(encoding="utf-8"),
                    text,
                    f"regenerate with `pixi run {u8.TASK}`",
                )

    def test_per_arm_deltas_reconcile_with_the_two_rankings(self) -> None:
        tiers = _readout_tier(ROOT)
        frozen = u8.arm_profiles(_tsv(ROOT / stage3_design.OUT_TSV), tiers)
        adopted = u8.arm_profiles(_tsv(ROOT / u8.OUT_DESIGN_TSV), tiers)
        rows = _tsv(ROOT / u8.OUT_PER_ARM)
        self.assertEqual(
            [r["experiment"] for r in rows], [e.experiment_id for e in EXPERIMENTS]
        )
        for row in rows:
            x = row["experiment"]
            with self.subTest(experiment=x):
                for field in u8.PROFILE_FIELDS:
                    self.assertEqual(row[f"v0.4_{field}"], frozen[x][field])
                    self.assertEqual(row[f"v0.5.1_{field}"], adopted[x][field])
                changed = [
                    f for f in u8.PROFILE_FIELDS if frozen[x][f] != adopted[x][f]
                ]
                self.assertEqual(row["changed_fields"], ",".join(changed) or "none")
        three = self.summary["three_reported_objects"]
        for side, profiles in (
            ("frozen_v0_4_ranking", frozen),
            ("adopted_v0_5_1_ranking", adopted),
        ):
            self.assertEqual(
                three[side]["candidate_set"],
                sorted(
                    x for x, p in profiles.items() if p["in_candidate_set"] == "True"
                ),
            )

    def test_the_tsv_derived_profile_is_stage3s_own_tier_columns(self) -> None:
        """The profile is re-derived from the TSV so the v0.4 side is read from
        the frozen artifact; it must agree with what Stage 3 itself computes, or
        the delta would be comparing a different criterion."""
        tiers = _readout_tier(ROOT)
        for key, text in (
            ("frozen", (ROOT / stage3_design.OUT_TSV).read_text(encoding="utf-8")),
            ("adopted", self.result["adopted_tsv"]),
        ):
            profiles = u8.arm_profiles(u8._read_tsv(text), tiers)
            for result in self.result[key]["results"]:
                x = result["experiment"]
                with self.subTest(model=key, experiment=x):
                    for column in (
                        "forks_separated_any",
                        "forks_separated_usable_assay",
                        "forks_separated_mapped_composite",
                        "forks_separated_no_assay_only",
                        "forks_separated_usable_opposite",
                    ):
                        self.assertEqual(profiles[x][column], ",".join(result[column]))
                    self.assertEqual(
                        profiles[x]["committed_model_propagates"],
                        str(bool(result["committed_model_changes"])),
                    )

    def test_pair_deltas_reconcile_with_the_two_design_tsvs(self) -> None:
        frozen = _tsv(ROOT / stage3_design.OUT_TSV)
        adopted = _tsv(ROOT / u8.OUT_DESIGN_TSV)
        pairs = _tsv(ROOT / u8.OUT_PAIRS)
        self.assertEqual(len(pairs), len(frozen))
        for a, b, p in zip(frozen, adopted, pairs, strict=True):
            self.assertEqual(p["v0.4_separating_nodes"], a["separating_nodes"])
            self.assertEqual(p["v0.5.1_separating_nodes"], b["separating_nodes"])
            self.assertEqual(p["v0.4_usable_assay_nodes"], a["usable_assay_nodes"])
            self.assertEqual(p["v0.5.1_usable_assay_nodes"], b["usable_assay_nodes"])
        self.assertEqual(
            self.summary["pair_separations_changed"],
            sum(p["changed"] == "True" for p in pairs),
        )

    # -- the answer, and that it is an output ----------------------------------

    def test_the_measured_answer(self) -> None:
        """Pinned as a RESULT: if a later model moves it, this is the test that says so."""
        self.assertTrue(self.summary["dropout_e2_remains_first"])
        adopted = self.summary["three_reported_objects"]["adopted_v0_5_1_ranking"]
        self.assertEqual(adopted["status"], u8.CARRIED_OVER)
        self.assertEqual(adopted["ordering"][0]["experiment"], "dropout_e2")
        self.assertEqual(self.summary["pair_separations_changed"], 0)
        self.assertEqual(self.summary["usable_readout_separations_changed"], 0)
        self.assertEqual(self.summary["full_state_comparison"]["differing"], [])

    def test_a_moved_premise_withholds_the_ordering(self) -> None:
        real = u8._premises

        def moved(report: dict) -> list[dict]:
            premises = real(report)
            if report["model_version"] == u8.ADOPTED_VERSION:
                premises[3] = {
                    **premises[3],
                    "value": {"arms_at_maximum": ["smo_antagonist"]},
                }
            return premises

        with mock.patch.object(u8, "_premises", moved):
            summary = u8.compute(ROOT)["summary"]
        adopted = summary["three_reported_objects"]["adopted_v0_5_1_ranking"]
        self.assertEqual(adopted["status"], u8.READJUDICATION_REQUIRED)
        self.assertEqual(adopted["ordering"], [])
        self.assertFalse(summary["dropout_e2_remains_first"])

    def test_every_frozen_premise_is_evaluated_on_both_models(self) -> None:
        for premise in self.summary["premises"]:
            with self.subTest(premise=premise["id"]):
                self.assertIn(u8.FROZEN_VERSION, premise)
                self.assertIn(u8.ADOPTED_VERSION, premise)
                self.assertEqual(
                    premise["unchanged"],
                    premise[u8.FROZEN_VERSION] == premise[u8.ADOPTED_VERSION],
                )
        by_id = {p["id"]: p[u8.FROZEN_VERSION] for p in self.summary["premises"]}
        # The v0.4 values are the ones test_stage3_design pins for the frozen claim.
        self.assertEqual(by_id["P2_only_arm_on_both_usable_readouts"], ["dropout_e2"])
        self.assertEqual(
            by_id["P6_sec_pairs_unreached_at_a_readout_that_exists"],
            ["SEC:SEC-a vs SEC-e"],
        )

    # -- cause attribution -----------------------------------------------------

    def test_the_only_rule_change_is_u5b_and_stage3_cannot_see_it(self) -> None:
        cause = self.summary["cause"]
        diff = cause["u5b_executable_rule_change"]["rule_diff"]
        self.assertEqual([d["node"] for d in diff], ["OUT_STROMAL_DECIDUALIZED"])
        self.assertEqual(diff[0]["dependencies_retired"], ["S_IGFBP1", "S_PRL"])
        # Why it is invisible: the retired regulators alias S_DECIDUALIZED in
        # both models, and no Stage-3 class rewrites or arm clamps either one.
        touched = set().union(*self.summary["stage3_touched_nodes"].values())
        self.assertFalse({"S_PRL", "S_IGFBP1"} & touched)
        for version in (u8.FROZEN_VERSION, u8.ADOPTED_VERSION):
            rules = parse_bnd_rules(resolve_model(version, ROOT).network_bnd)
            self.assertEqual(rules["S_PRL"], "S_DECIDUALIZED")
            self.assertEqual(rules["S_IGFBP1"], "S_DECIDUALIZED")
        self.assertFalse(cause["altered_alias_classes"])
        self.assertFalse(cause["changed_model_structure"]["enters_stage3"])
        self.assertEqual(len(cause["bookkeeping_only"]), 1)
        self.assertIn(u8.ADOPTED_VERSION, cause["bookkeeping_only"][0])

    # -- D1 --------------------------------------------------------------------

    def test_d1_dependence_is_carried_from_the_findings(self) -> None:
        findings = json.loads((ROOT / u8.D1_SOURCE).read_text(encoding="utf-8"))
        ac01 = findings["alias_classes"]["AC01"]
        d1 = self.summary["d1_dependency"]
        self.assertEqual(d1["AC01_class_verdict"], ac01["class_verdict"])
        self.assertEqual(d1["AC01_class_verdict"], "alias_challenged")
        self.assertEqual(d1["depends_on_deviations"], ["D1"])
        self.assertEqual(
            d1["counterfactual_verdict_without_D1"], "unclassified_by_section_5_4"
        )
        self.assertEqual(d1["mandate"], "MANDATORY_CONDITIONAL_ON_D1")
        self.assertEqual(d1["source_sha256"], _sha(ROOT / u8.D1_SOURCE))
        report = (ROOT / u8.OUT_REPORT).read_text(encoding="utf-8")
        self.assertIn("unclassified_by_section_5_4", report)
        record = (ROOT / "docs/v05_u8_stage3_rerank.md").read_text(encoding="utf-8")
        self.assertIn("D1", record)
        self.assertIn("unclassified_by_section_5_4", record)

    def test_a_changed_d1_record_is_not_reported_as_the_mandate(self) -> None:
        findings = json.loads((ROOT / u8.D1_SOURCE).read_text(encoding="utf-8"))
        findings["alias_classes"]["AC01"]["decision_provenance"][
            "depends_on_deviations"
        ] = []
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / u8.D1_SOURCE
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(findings), encoding="utf-8")
            self.assertEqual(
                u8._d1(Path(tmp))["mandate"], "D1_CONDITION_NOT_AS_RECORDED"
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
