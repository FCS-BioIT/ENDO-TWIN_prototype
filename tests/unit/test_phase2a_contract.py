"""Phase 2A donor-contextualization input contract (`docs/phase2a/`).

Each test class is one invariant of the contract. The negative tests mutate an
input in memory and require the contract to refuse or reclassify, so a guard
that could never fire is caught as well as one that fires wrongly.
"""

from __future__ import annotations

import builtins
import copy
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc import closure_replay
from dt_adoc.personalization import phase2a_contract as P
from dt_adoc.personalization.strict_nv import decide_strict_variant
from dt_adoc.scrna import node_support_contract as C
from dt_adoc.scrna import verify_rds

# Closed phases are reproduced against their closure-time models/ snapshot
# (src/dt_adoc/closure_replay.py); later model versions are outside it.
_CLOSURE_TMP = tempfile.TemporaryDirectory(prefix="closure-replay-")
CLOSURE, _CLOSURE_INDEX = closure_replay.build_view(ROOT, Path(_CLOSURE_TMP.name))
CLOSURE_ENV = {"GIT_INDEX_FILE": str(_CLOSURE_INDEX)}


def tearDownModule() -> None:
    _CLOSURE_TMP.cleanup()


RDS_SHA256 = "504a674db978779b03d02a73224ee425ec46efbf411c148b0903ceef15389a1a"
MODELS_TREE_SHA256 = "de1bddba2be91e837fefbd784c21790531790ec0ee85c5babd7d4dd2844657b5"

#: Phase-1B closure outputs and the frozen Stage-3 design, as merged in PR #6.
FROZEN = {
    "docs/phase1b_closure/phase1b_claims.tsv": "c1d07a30cbf438ad79167d0dffcf721cca70d3d1adb5f456a7d616fcb1a7340f",
    "docs/phase1b_closure/phase1b_closure_summary.json": "4ec154d07b5bbc9623b2808a0a23f9478859d01d745e796589808061b36fe38a",
    "docs/phase1b_closure/phase1b_exit_gate.tsv": "f2ae7ad1ff401389a007f669ce6b2e97f604ba9ae951d6ad7b2bb230e393b298",
    "docs/phase1b_closure/pre_run_analysis_addendum.tsv": "9969353d473a4023d1564e96e397f72685ec398ff1d5b7f5ba677d97fcb24ea7",
    "docs/phase1b_closure/prospective_allocation_manifest_template.tsv": "aa2e38c962bba22784ce76c26ac7a09c27668e6f2c0c9d550b7cedb26bc68740",
    "docs/phase1b_closure/prospective_assay_metadata_template.tsv": "02ad28cc392281032337da9ba88f29d19061b9cf79a23173ea52af74d91e24d9",
    "docs/phase1b_closure/prospective_dropout_e2_handoff.md": "3a2d2c5e97eee3594502c8d65e565726adb649ec3ac9e60349707a099ddf3209",
    "docs/phase1b_closure/prospective_dropout_e2_handoff.tsv": "c98b7f27b0329d423dd5fe6f2cd218e115a1af4e6296a8988db0e309c1c38011",
    "docs/phase1b_closure/sensitivity_inventory.tsv": "69f4b5aaaa8dfab799a8a0752ce88a85c827edff3cb6eef22315da61e2099edf",
    "docs/experiments/stage3_experiment_design.tsv": "987d75644925346fab73e7251067094d04c01883af783a83c3775705b444ee74",
    "docs/experiments/stage3_experiment_design.md": "7368b1f85007f677cd16c5f308d9571f9573a83771b3dfdb2bb34b593b068520",
    "docs/experiments/stage3_decision_tables.md": "a2cc7291adfaf130f79f345201a30556ab16c9391c8598315a5735d6b0c3305b",
    "docs/stage3_experiment_selection.md": "e6a5fa558bede27f20b329cfbfe7bd3ec90d4d41c0f5091ed52e3dd4cbdb113c",
    # Owner Q3: the policy file and the existing personalization layer are left alone.
    "config/personalization.yaml": "16b2f4e33f305ff280df0cdb78649ad320201511dde236dd39387cd00282c4c7",
    "src/dt_adoc/personalization/mapping.py": "411dfb75d7c9051711dc345a00e115be0d9c6d7a9211d8af8faad81917929bad",
    "src/dt_adoc/personalization/reference.py": "7c6b8bda69973e679042230d63bcfebab7fc74205cce22f6b2ef29a3a1407e23",
    "src/dt_adoc/personalization/soft_nv.py": "76825bb97b2b68909857ce84602c4c2b0003a1feb90a130d9af2e60fcbef8313",
    "src/dt_adoc/personalization/strict_nv.py": "f3666b50bdf42c3dbba6fcd476d7ce0387642c59da790f52555ed685a5d90069",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tsv(relative: Path) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _json(relative: Path):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class _Computed(unittest.TestCase):
    """One in-memory computation, with every file the computation opened."""

    @classmethod
    def setUpClass(cls) -> None:
        opened: list[tuple[Path, str]] = []
        real_open = builtins.open
        real_path_open = Path.open

        def spy(file, mode="r", *args, **kwargs):
            opened.append((Path(file).resolve(), mode))
            return real_open(file, mode, *args, **kwargs)

        def path_spy(self, mode="r", *args, **kwargs):
            opened.append((self.resolve(), mode))
            return real_path_open(self, mode, *args, **kwargs)

        builtins.open, Path.open = spy, path_spy
        try:
            cls.outputs = P.compute(CLOSURE)
        finally:
            builtins.open, Path.open = real_open, real_path_open
        cls.opened = opened
        cls.map = _tsv(P.OUT_MAP)
        cls.grain = _tsv(P.OUT_GRAIN)
        cls.summaries = _tsv(P.OUT_SUMMARIES)
        cls.gate = _json(P.OUT_GATE)
        cls.spec = _json(P.OUT_SPEC)
        cls.status = _json(P.OUT_STATUS)
        cls.extraction = _json(P.EXTRACTION)


class SourceIdentity(_Computed):
    """1. The final E-MTAB-15842 object is pinned, everywhere it is named."""

    def test_every_binding_names_the_manifest_hash(self) -> None:
        self.assertEqual(P.manifest_sha(ROOT), RDS_SHA256)
        self.assertEqual(self.extraction["rds_sha256"], RDS_SHA256)
        self.assertEqual(self.extraction["rds_size_bytes"], 2877048290)
        self.assertEqual(
            _json(P.NODE_SUPPORT_FINDINGS)["provenance"]["rds_sha256"], RDS_SHA256
        )
        self.assertEqual(self.status["lineage"]["rds_sha256"], RDS_SHA256)
        self.assertTrue(self.status["gates"]["G1_source_identity_pinned"])

    def test_an_extraction_from_another_object_is_refused(self) -> None:
        forged = copy.deepcopy(self.extraction)
        forged["rds_sha256"] = "0" * 64
        with self.assertRaises(P.Phase2AError):
            P.check_extraction(forged, ROOT)

    def test_extraction_refuses_bytes_that_do_not_hash_to_the_manifest(self) -> None:
        with (
            tempfile.NamedTemporaryFile(suffix=".rds") as handle,
            self.assertRaises(P.Phase2AError),
        ):
            P.extract(Path(handle.name), rscript="false", root=ROOT)

    def test_the_committed_extraction_carries_no_row_level_metadata(self) -> None:
        text = (ROOT / P.EXTRACTION).read_text(encoding="utf-8")
        self.assertNotRegex(text, r"[ACGT]{16}-1")
        self.assertEqual(len(self.extraction["groups"]), 40)


class MetadataAxes(_Computed):
    """2. Donor, sample, condition and compartment come from the object."""

    def test_the_object_has_no_donor_condition_or_compartment_column(self) -> None:
        names = [c["name"] for c in self.extraction["columns"]]
        self.assertEqual(tuple(names), verify_rds.EXPECTED_META_COLUMNS)
        for axis in ("donor", "condition", "compartment", "tissue", "patient"):
            self.assertFalse(any(axis in n.lower() for n in names), axis)
        self.assertTrue(all(c["n_na"] == 0 for c in self.extraction["columns"]))

    def test_sample_id_is_the_only_carrier_and_agrees_with_orig_ident(self) -> None:
        self.assertEqual(self.extraction["orig_ident_equals_sample_id"], 28212)
        self.assertEqual(self.extraction["barcode_prefix_equals_sample_id"], 28212)
        samples = {g["sample_id"] for g in self.extraction["groups"]}
        self.assertEqual(samples, set(verify_rds.EXPECTED_SAMPLES))

    def test_grain_rows_are_the_extraction_regrouped(self) -> None:
        labels = [r for r in self.grain if r["level"] == "celltype_v2"]
        self.assertEqual(len(labels), 3 * 2 * 7)
        observed = {
            (g["sample_id"], g["celltype_v2"]): g["n_cells"]
            for g in self.extraction["groups"]
        }
        for row in labels:
            key = (row["sample_id"], row["celltype_v2"])
            self.assertEqual(int(row["n_cells"]), observed.get(key, 0))
            self.assertEqual(
                row["compartment"], C.COMPARTMENT_OF_LABEL[row["celltype_v2"]]
            )

    def test_the_compartment_grid_equals_node_support_and_records_the_empty_cell(
        self,
    ) -> None:
        units = [r for r in self.grain if r["level"] == "compartment_unit"]
        self.assertEqual(len(units), 18)
        recorded = _json(P.NODE_SUPPORT_FINDINGS)["unit_cell_counts"]
        for row in units:
            unit = f"{row['donor']}_{row['condition']}_{row['compartment']}"
            self.assertEqual(int(row["n_cells"]), recorded.get(unit, 0))
        empty = [
            f"{r['donor']}_{r['condition']}_{r['compartment']}"
            for r in units
            if r["grid_status"] != "populated"
        ]
        self.assertEqual(empty, ["SZ09_HT_myofibroblast"])

    def test_a_count_that_disagrees_with_the_object_is_refused(self) -> None:
        forged = copy.deepcopy(self.extraction)
        forged["groups"][0]["n_cells"] += 1
        with self.assertRaises(P.Phase2AError):
            P.check_extraction(forged, ROOT)

    def test_an_unpartitioned_label_is_refused(self) -> None:
        forged = copy.deepcopy(self.extraction)
        forged["groups"][0]["celltype_v2"] = "Unknown"
        with self.assertRaises(P.Phase2AError):
            P.check_extraction(forged, ROOT)

    def test_a_malformed_sample_id_is_refused(self) -> None:
        for bad in ("SZ09_CNT", "SZ99TE_CNT", "SZ09TE_E2", "SZ09TECNT"):
            with self.subTest(bad=bad), self.assertRaises(P.Phase2AError):
                P.parse_sample(bad)


class CellsAreNotReplicates(_Computed):
    """3. The donor is the unit; cells are within-unit precision."""

    def test_every_grain_row_names_the_donor_as_the_unit(self) -> None:
        self.assertEqual({r["independent_unit"] for r in self.grain}, {"donor"})
        self.assertEqual(
            {r["replicate_status"] for r in self.grain},
            {"cells_are_within_unit_measurement_precision_not_replicates"},
        )

    def test_no_artifact_counts_cells_as_replicates(self) -> None:
        for relative, text in self.outputs.items():
            header = text.splitlines()[0].lower() if relative.suffix == ".tsv" else ""
            self.assertNotIn("n_replicates", header)
            self.assertNotIn("replicate_n", header)
        for row in self.summaries:
            if row["missingness_state"] == "measured":
                self.assertIn("not a replicate", row["interval_meaning"])

    def test_a_per_cell_reference_is_refused(self) -> None:
        reference, spec, root = _valid_reference()
        reference["aggregation_unit"] = "cell"
        self.assertIn("RR07", " ".join(_evaluate(reference, spec, root)))


class OneRowPerNode(_Computed):
    """4-5. Exactly one row per v0.5.1 node, with the model's exact names."""

    def test_the_map_names_exactly_the_adopted_nodes(self) -> None:
        dictionary = [r["node_id"] for r in _tsv(P.NODE_DICTIONARY)]
        from dt_adoc.model.topology import parse_bnd_rules

        bnd = list(parse_bnd_rules(ROOT / P.NETWORK))
        names = [r["model_node"] for r in self.map]
        self.assertEqual(len(names), 59)
        self.assertEqual(len(set(names)), 59)
        self.assertEqual(sorted(names), sorted(dictionary))
        self.assertEqual(sorted(names), sorted(bnd))

    def test_every_eligibility_value_is_in_the_vocabulary(self) -> None:
        for row in self.map:
            self.assertIn(row["structural_eligibility"], P.ELIGIBILITY)
            self.assertIn(row["mapping_eligibility"], P.ELIGIBILITY)

    def test_the_counts_are_the_reported_ones(self) -> None:
        counts = self.status["mapping_eligibility_counts"]
        self.assertEqual(counts[P.NOT_ASSESSABLE], 32)
        self.assertEqual(counts[P.CONTEXT_ONLY], 26)
        self.assertEqual(counts[P.BLOCKED_REFERENCE], 1)
        self.assertEqual(counts[P.ELIGIBLE], 0)
        self.assertEqual(sum(counts.values()), 59)

    def test_eligibility_is_exactly_the_free_observable_variables(self) -> None:
        eligible = {
            r["model_node"]
            for r in self.map
            if r["structural_eligibility"] == P.ELIGIBLE
        }
        self.assertEqual(eligible, {"E_KLF12_HIGH"})
        free = {
            r["model_node"]
            for r in self.map
            if r["model_logic_is_self"] == "true"
            and r["source_feature_type"] != "not_RNA_assessable"
        }
        self.assertEqual(eligible, free)
        for row in self.map:
            if row["conditioning_compatibility"] == "rule_override_required":
                self.assertEqual(row["structural_eligibility"], P.CONTEXT_ONLY)

    def test_the_layer_rr04_names_is_the_node_support_layer(self) -> None:
        self.assertEqual(_json(P.NODE_SUPPORT_FINDINGS)["layer"], P.ADOC_LAYER)

    def test_the_map_reuses_the_frozen_node_support_vocabulary(self) -> None:
        interpretability = {
            r["model_node"]: r
            for r in _tsv(Path("docs/scrna/node_rna_interpretability.tsv"))
        }
        for row in self.map:
            if row["model_node"] in interpretability:
                self.assertEqual(
                    row["source_feature_type"],
                    interpretability[row["model_node"]]["measurement_type"],
                )
                self.assertEqual(
                    row["source_gene_or_signature"],
                    interpretability[row["model_node"]]["measurement_features"],
                )


def _obs(node: str) -> dict[str, str]:
    rows = {r["model_node"]: r for r in C.observation_rows(ROOT / P.OBSERVATION_MAP)}
    return copy.deepcopy(rows[node])


def _node(node: str) -> dict[str, str]:
    return copy.deepcopy({n["node_id"]: n for n in P.model_nodes(ROOT)}[node])


class CompartmentMismatch(unittest.TestCase):
    """6. A compartment mismatch is refused, at the map and at the reference."""

    def test_a_node_whose_map_compartment_is_not_its_model_compartment_is_blocked(
        self,
    ) -> None:
        obs = _obs("E_KLF12_HIGH")
        obs["compartment"] = "stromal"
        verdict = P.classify(obs, _node("E_KLF12_HIGH"), frozenset())
        self.assertEqual(verdict["structural"], P.BLOCKED_COMPARTMENT)

    def test_a_non_primary_compartment_is_blocked(self) -> None:
        obs, node = _obs("S_PRL"), _node("S_PRL")
        obs["compartment"] = "myofibroblast"
        self.assertEqual(
            P.classify(obs, node, frozenset())["structural"], P.BLOCKED_COMPARTMENT
        )

    def test_summaries_only_use_the_node_compartment(self) -> None:
        for row in _tsv(P.OUT_SUMMARIES):
            self.assertEqual(row["compartment"], "epithelium")

    def test_a_stromal_reference_cannot_place_an_epithelial_node(self) -> None:
        reference, spec, root = _valid_reference()
        reference["compartment"] = "stroma"
        self.assertIn("RR05", " ".join(_evaluate(reference, spec, root)))


class MissingNeverOff(unittest.TestCase):
    """7. Missing features and missing units stay missing, never OFF."""

    def test_all_features_absent_blocks_the_node(self) -> None:
        obs = _obs("E_KLF12_HIGH")
        verdict = P.classify(obs, _node("E_KLF12_HIGH"), frozenset(C.features(obs)))
        self.assertEqual(verdict["structural"], P.BLOCKED_ABSENT)

    def test_a_partially_absent_feature_is_flagged_not_aliased(self) -> None:
        row = {r["model_node"]: r for r in _tsv(P.OUT_MAP)}["S_TAZ_ECM"]
        self.assertEqual(row["absent_features"], "CTGF;CYR61")
        self.assertIn(
            "feature_partially_absent_no_alias_substituted", row["leakage_flags"]
        )
        self.assertIn("CTGF", row["source_gene_or_signature"])

    def test_missing_values_are_unresolved(self) -> None:
        for estimate in ((None, 0.1, 0.3), (0.2, None, 0.3), (float("nan"), 0.1, 0.3)):
            self.assertEqual(P.initial_probability(*estimate), "unresolved")
        for row in _tsv(P.OUT_SUMMARIES):
            self.assertEqual(row["high_state_fraction"], "unresolved")
            self.assertEqual(row["initial_on_probability"], "unresolved")

    def test_an_empty_unit_is_a_row_with_blank_statistics_not_zeros(self) -> None:
        # Remove one unit's evidence and QC in a shadow copy: the summary must
        # report it empty with blanks, never zero-fill it.
        with tempfile.TemporaryDirectory() as tmp:
            shadow = _shadow(Path(tmp))
            for relative in (P.NODE_SUPPORT_EVIDENCE, P.NODE_SUPPORT_QC):
                lines = (
                    (shadow / relative)
                    .read_text(encoding="utf-8")
                    .splitlines(keepends=True)
                )
                (shadow / relative).unlink()
                (shadow / relative).write_text(
                    "".join(l for l in lines if not l.startswith("SZ25_HT_epithelium")),
                    encoding="utf-8",
                )
            mapping = P.map_rows(shadow, reference_ready=False)
            rows = {r["unit_id"]: r for r in P.summary_rows(shadow, mapping)}
        empty = rows["SZ25_HT_epithelium"]
        # The unit has cells; only its statistics are missing -- not an empty
        # unit, and certainly not zero cells.
        self.assertEqual(empty["missingness_state"], "unit_statistics_missing")
        self.assertEqual(empty["n_cells"], "1404")
        for field in (
            "pseudobulk_fraction_f",
            "detection_fraction_d",
            "f_ci_lo",
            "d_ci_hi",
        ):
            self.assertEqual(empty[field], "-")
        self.assertEqual(empty["initial_on_probability"], "unresolved")

    def test_the_specification_never_defaults_missing_to_one_half(self) -> None:
        spec = P.mapping_specification()
        self.assertIn("unresolved", spec["missing"]["rule"])
        self.assertIn("never applied implicitly", spec["missing"]["default_0_5"])


class ZeroCannotClamp(unittest.TestCase):
    """8. A zero or dropout can never produce a hard state."""

    def test_a_boundary_fraction_is_never_written(self) -> None:
        # E_KLF12_HIGH has logic = self: an istate of 0 or 1 is a clamp in effect.
        for estimate in (
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.02),
            (0.01, 0.0, 0.03),
            (1.0, 0.97, 1.0),
        ):
            with self.subTest(estimate=estimate):
                self.assertEqual(
                    P.initial_probability(*estimate), "unresolved_boundary"
                )
        self.assertEqual(P.initial_probability(0.3, 0.2, 0.4), 0.3)

    def test_an_all_zero_unit_cannot_become_a_hard_off(self) -> None:
        fraction = P.high_state_fraction([0.0] * 500, rule=">=", threshold=0.5)
        self.assertEqual(fraction, 0.0)
        self.assertEqual(
            P.initial_probability(fraction, 0.0, 0.0), "unresolved_boundary"
        )

    def test_the_fraction_is_the_external_rule_applied_per_cell(self) -> None:
        cells = [0.0, 0.0, 1.0, 2.0, 3.0]
        self.assertEqual(P.high_state_fraction(cells, rule=">=", threshold=2.0), 0.4)
        self.assertEqual(P.high_state_fraction(cells, rule=">", threshold=2.0), 0.2)

    def test_an_incoherent_or_malformed_input_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            P.initial_probability(0.5, 0.6, 0.7)
        for kwargs in (
            {"per_cell": [], "rule": ">=", "threshold": 1.0},
            {"per_cell": [-1.0], "rule": ">=", "threshold": 1.0},
            {"per_cell": [1.0], "rule": "<", "threshold": 1.0},
            {"per_cell": [1.0], "rule": ">=", "threshold": float("nan")},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                P.high_state_fraction(**kwargs)

    def test_no_rank_transform_survives(self) -> None:
        source = (SRC / "dt_adoc/personalization/phase2a_contract.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("midrank", source)
        self.assertNotIn("DKW", source)
        spec = P.mapping_specification()
        self.assertEqual(spec["bridge_assumption"]["text"], P.BRIDGE_ASSUMPTION)
        text = (ROOT / P.BRIDGE_SOURCE).read_text(encoding="utf-8")
        prereg = " ".join(text.replace("> ", " ").replace("*", "").split())
        self.assertIn(P.BRIDGE_ASSUMPTION, prereg)

    def test_dropout_cannot_justify_a_strict_variant(self) -> None:
        decision = decide_strict_variant(
            has_constitutive_evidence=True, measurement_state="dropout", desired_state=0
        )
        self.assertIsNone(decision.clamp)

    def test_clamp_is_a_forbidden_layer(self) -> None:
        spec = P.mapping_specification()
        self.assertEqual(spec["permitted_layer"], "initial_probability")
        self.assertIn("clamp", spec["forbidden_layers"])
        for row in _tsv(P.OUT_MAP):
            self.assertIn(
                row["preferred_mapping_layer"], ("initial_probability", "none")
            )


class NothingForbiddenIsEmitted(_Computed):
    """9-11. No topology, rule, cfg, rate modifier or mutation interface."""

    def test_the_computation_writes_nothing(self) -> None:
        writes = [str(p) for p, mode in self.opened if any(c in mode for c in "wax+")]
        self.assertEqual(writes, [])

    def test_outputs_are_only_the_declared_contract_files(self) -> None:
        self.assertEqual(tuple(self.outputs), P.OUTPUTS)
        for relative in self.outputs:
            self.assertEqual(relative.parent, P.OUT_DIR)
            self.assertNotIn(relative.suffix, (".bnd", ".cfg"))
        self.assertEqual(P.forbidden_emission(self.outputs), [])
        self.assertTrue(self.status["gates"]["G8_no_forbidden_emission"])

    def test_the_forbidden_emission_check_fires(self) -> None:
        self.assertTrue(P.forbidden_emission({Path("x.cfg"): "a\n"}))
        self.assertTrue(P.forbidden_emission({Path("x.tsv"): "node\trate_up\n"}))
        self.assertTrue(
            P.forbidden_emission({Path("x.json"): '{"a": {"is_mutant": 1}}'})
        )

    def test_no_output_carries_a_rate_or_mutation_field(self) -> None:
        for relative, text in self.outputs.items():
            if relative.suffix == ".tsv":
                header = text.splitlines()[0]
                for bad in P.FORBIDDEN_OUTPUT_FIELDS:
                    self.assertNotIn(bad, header, relative)

    def test_the_module_calls_no_rate_or_mutation_machinery(self) -> None:
        source = (SRC / "dt_adoc/personalization/phase2a_contract.py").read_text(
            encoding="utf-8"
        )
        for token in (
            "score_to_rate_modifiers",
            "_make_mutant_node",
            ".mutate(",
            "$High_",
            "$Low_",
            "write_bnd",
            "emit_condition",
        ):
            self.assertNotIn(token, source)

    def test_no_u7_or_mutation_interface_exists_in_the_models(self) -> None:
        bnd = (ROOT / P.NETWORK).read_text(encoding="utf-8")
        self.assertNotIn("rate_up", bnd)
        self.assertNotIn("$", bnd)


def _shadow(tmp: Path) -> Path:
    """A copy of the inputs a computation reads, so a test can mutate them."""
    for relative in (
        P.EXTRACTION,
        P.NODE_SUPPORT_FINDINGS,
        P.NODE_SUPPORT_EVIDENCE,
        P.NODE_SUPPORT_QC,
        P.OBSERVATION_MAP,
        P.EXTERNAL_MANIFEST,
        P.DATA_MANIFEST,
        P.PERSONALIZATION,
        P.NETWORK,
        P.NODE_DICTIONARY,
    ):
        (tmp / relative).parent.mkdir(parents=True, exist_ok=True)
        (tmp / relative).write_bytes((ROOT / relative).read_bytes())
    return tmp


_TMPS: list[tempfile.TemporaryDirectory] = []
_PREREG = "prereg/reference_preregistration.md"
_MANIFEST = "reference/manifest.yaml"

DONORS_TSV = "donor_id\tcondition_class\tcompartment\tn_cells\n" + "".join(
    f"R{i}\thormone_treated\tepithelium\t{400 + i}\n" for i in range(1, 6)
)
DEFINITION = {
    "feature": "KLF12",
    "layer": P.ADOC_LAYER,
    "per_cell_quantity": "count",
    "rule": ">=",
    "threshold": "2.0",
    "evidence_citation": "doi:10.0000/synthetic",
    "evidence_kind": "published_per_cell_definition",
    "owner_accepted_on": "2026-01-02",
    "comparability": "same_pipeline_reprocessed",
    "comparability_evidence": "doi:10.0000/synthetic-pipeline",
    "threshold_derivation": "doi:10.0000/synthetic-threshold",
    "threshold_variants": "1.0;3.0",
    "variant_selection": "all_reported_none_selected",
}


def _definition_tsv(**changes: str) -> str:
    row = {**DEFINITION, **changes}
    return "\t".join(row) + "\n" + "\t".join(row.values()) + "\n"


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
    )


def _write(root: Path, name: str, text: str) -> str:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(text, encoding="utf-8")
    return _sha(root / name)


def _valid_reference(
    *,
    definition: str | None = None,
    donors: str = DONORS_TSV,
    layout: str = "normal",
    calibration: str | None = None,
    register_calibration: bool = True,
    repo_method: str | None = None,
) -> tuple[dict, dict, Path]:
    """A synthetic reference that satisfies every requirement -- the positive
    control without which every refusal below could be vacuous -- in its own
    throwaway git repository: the pre-registration is committed first, then the
    reference files and the personalization.yaml that activates them."""
    tmp = tempfile.TemporaryDirectory()
    _TMPS.append(tmp)
    root = Path(tmp.name)
    _git(root, "init", "-q")
    if repo_method is not None:
        # Owner RR14 schema change (2026-09-25): a custom threshold method cites
        # the repository artifact that froze it, by path, commit and sha256.
        cited_path = (
            "data/method.md" if repo_method == "in_data" else "methods/derivation.md"
        )
        digest = _write(root, cited_path, "the frozen method\n")
        _git(root, "add", cited_path)
        _git(root, "commit", "-q", "-m", "method")
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if repo_method == "not_earliest":
            _write(root, "unrelated.txt", "x\n")
            _git(root, "add", "unrelated.txt")
            _git(root, "commit", "-q", "-m", "later")
            commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        if repo_method == "wrong_sha":
            digest = "0" * 64
        if repo_method == "outside_data":
            cited_path = "../methods/derivation.md"
        citation = f"repo:{cited_path}@{commit}#sha256:{digest}"
        definition = _definition_tsv(threshold_derivation=citation)
    spec = P.mapping_specification()
    spec["parameters"]["min_reference_donors"] = {
        "value": 5,
        "provenance": "owner_decided",
    }
    reference = {
        "source_accession": "E-SYNT-0001",
        "source_sha256": _write(root, "reference/donors.tsv", donors),
        "retrieved_on": "2026-01-01",
        "donors_path": "reference/donors.tsv",
        "definition_path": "reference/definition.tsv",
        "definition_sha256": _write(
            root, "reference/definition.tsv", definition or _definition_tsv()
        ),
        "donor_ids": ["R1", "R2", "R3", "R4", "R5"],
        "derived_from_adoc": False,
        "assay": "scRNA-seq",
        "compartment": "epithelium",
        "condition_class": "hormone_treated",
        "aggregation_unit": "donor",
        "outcome_blind": True,
        "preregistration_path": _PREREG,
        "preregistration_sha256": "",
        "__path__": _MANIFEST,
    }
    registered = (
        f"definition_path: {reference['definition_path']}\n"
        f"definition_sha256: {reference['definition_sha256']}\n"
    )
    if calibration is not None:
        reference["calibration_path"] = "reference/calibration.tsv"
        reference["calibration_sha256"] = _write(
            root, "reference/calibration.tsv", calibration
        )
        if register_calibration:
            registered += (
                f"calibration_path: {reference['calibration_path']}\n"
                f"calibration_sha256: {reference['calibration_sha256']}\n"
            )
    reference["preregistration_sha256"] = _write(
        root, _PREREG, "synthetic pre-registration\n" + registered
    )
    _write(
        root,
        _MANIFEST,
        yaml.safe_dump({k: v for k, v in reference.items() if k != "__path__"}),
    )
    policy = yaml.safe_load((ROOT / P.PERSONALIZATION).read_text(encoding="utf-8"))
    policy["reference_strategy"]["reference_path"] = _MANIFEST
    _write(root, str(P.PERSONALIZATION), yaml.safe_dump(policy))
    activation = [
        _MANIFEST,
        "reference/donors.tsv",
        "reference/definition.tsv",
        str(P.PERSONALIZATION),
    ] + (["reference/calibration.tsv"] if calibration is not None else [])
    early = {
        "normal": [],
        "manifest_first": [_MANIFEST],
        "definition_first": ["reference/definition.tsv"],
        "activated_first": [str(P.PERSONALIZATION)],
        "unactivated": [],
    }[layout]
    steps = [early, [_PREREG], [f for f in activation if f not in early]]
    if layout == "unactivated":
        steps = [[_PREREG], activation[:3]]
    for files in steps:
        if files:
            _git(root, "add", *files)
            _git(root, "commit", "-q", "-m", files[0])
    return reference, spec, root


def _evaluate(reference: dict | None, spec: dict, root: Path) -> list[str]:
    node = {r["model_node"]: r for r in _tsv(P.OUT_MAP)}["E_KLF12_HIGH"]
    return P.evaluate_reference(
        reference,
        node=node,
        spec=spec,
        forbidden_shas=P.forbidden_reference_shas(ROOT),
        root=root,
    )


def _ids(failures: list[str]) -> list[str]:
    return [f[:4] for f in failures]


class ReferenceGate(_Computed):
    """12-14. No ADOC-derived reference; a missing reference blocks mechanically."""

    def test_the_synthetic_positive_control_passes(self) -> None:
        self.assertEqual(_evaluate(*_valid_reference()), [])

    def test_the_manifest_loader_records_its_own_path(self) -> None:
        _, spec, root = _valid_reference()
        policy = {"reference_strategy": {"reference_path": _MANIFEST}}
        loaded = P.load_reference_manifest(root, policy)
        self.assertEqual(loaded["__path__"], _MANIFEST)
        self.assertEqual(_evaluate(loaded, spec, root), [])

    def test_the_adoc_donors_are_refused_as_the_reference_population(self) -> None:
        for donors in (
            ["SZ09", "R2", "R3", "R4", "R5"],
            ["SZ10TE_HT", "R2", "R3", "R4", "R5"],
        ):
            reference, spec, root = _valid_reference()
            reference["donor_ids"] = donors
            with self.subTest(donors=donors):
                self.assertIn("RR03", _ids(_evaluate(reference, spec, root)))

    def test_the_adoc_accession_or_object_is_refused(self) -> None:
        reference, spec, root = _valid_reference()
        reference["source_accession"] = "e-mtab-15842"
        self.assertIn("RR03", _ids(_evaluate(reference, spec, root)))
        reference, spec, root = _valid_reference()
        reference["definition_sha256"] = RDS_SHA256
        self.assertIn("RR03", _ids(_evaluate(reference, spec, root)))

    def test_adoc_donors_relabelled_are_refused_without_attestation(self) -> None:
        # PROFILE normalizes against its own cohort; here that cohort would be
        # the three ADOC donors under new names.
        reference, spec, root = _valid_reference()
        reference.pop("derived_from_adoc")
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR03"])

    def test_an_unrelated_hashed_file_is_refused(self) -> None:
        # Review B2's first counterexample: a real, correctly hashed, unrelated file.
        reference, spec, root = _valid_reference()
        text = (ROOT / P.EXTERNAL_MANIFEST).read_text(encoding="utf-8")
        reference.update(
            source_sha256=_write(root, "unrelated.tsv", text),
            donors_path="unrelated.tsv",
        )
        self.assertIn("RR02", _ids(_evaluate(reference, spec, root)))

    def test_the_definition_is_read_from_its_hashed_file_only(self) -> None:
        # Review B2 round 2: definition fields in the manifest are ignored; an
        # unhashed or multi-row definition is refused.
        reference, spec, root = _valid_reference()
        reference["high_state_definition"] = {**DEFINITION, "feature": "KLF12"}
        reference["definition_sha256"] = "0" * 64
        self.assertIn("RR02", _ids(_evaluate(reference, spec, root)))
        two_rows = _definition_tsv() + "\t".join(DEFINITION.values()) + "\n"
        self.assertIn("RR02", _ids(_evaluate(*_valid_reference(definition=two_rows))))

    def test_a_donors_file_that_disagrees_with_the_manifest_is_refused(self) -> None:
        for text in (
            DONORS_TSV.replace("R5\t", "R9\t"),
            DONORS_TSV.replace("R5\thormone_treated", "R5\tunstimulated"),
            DONORS_TSV.replace(
                "R5\thormone_treated\tepithelium", "R5\thormone_treated\tstroma"
            ),
        ):
            with self.subTest(text=text[-40:]):
                self.assertIn("RR02", _ids(_evaluate(*_valid_reference(donors=text))))

    def test_an_outcome_column_in_either_file_is_refused(self) -> None:
        donors = (
            "donor_id\tcondition_class\tcompartment\tn_cells\tadhesion\n"
            + "".join(
                f"R{i}\thormone_treated\tepithelium\t400\t1\n" for i in range(1, 6)
            )
        )
        self.assertIn("RR09", _ids(_evaluate(*_valid_reference(donors=donors))))
        definition = _definition_tsv(pregnancy="1")
        self.assertIn("RR09", _ids(_evaluate(*_valid_reference(definition=definition))))

    def test_a_self_attested_or_late_preregistration_is_refused(self) -> None:
        # Review B3: a digest of 'x', an uncommitted file, and a pre-registration
        # committed only AFTER the reference manifest.
        reference, spec, root = _valid_reference()
        reference["preregistration_sha256"] = "x"
        # A broken pre-registration also leaves the variants unregistered.
        self.assertEqual(
            sorted(_ids(_evaluate(reference, spec, root))), ["RR10", "RR14"]
        )
        reference, spec, root = _valid_reference()
        digest = _write(root, "uncommitted.md", "late\n")
        reference.update(
            preregistration_path="uncommitted.md", preregistration_sha256=digest
        )
        self.assertEqual(
            sorted(_ids(_evaluate(reference, spec, root))), ["RR10", "RR14"]
        )
        # Review B3 round 3: every selecting or activating commit counts.
        for layout in (
            "manifest_first",
            "definition_first",
            "activated_first",
            "unactivated",
        ):
            with self.subTest(layout=layout):
                failures = _evaluate(*_valid_reference(layout=layout))
                self.assertEqual(_ids(failures), ["RR10"])

    def test_every_single_requirement_can_fail(self) -> None:
        cases = {
            "RR04": {
                "definition": _definition_tsv(per_cell_quantity="protein_ng_per_ml")
            },
            "RR06": {"definition": _definition_tsv(feature="KLF13")},
            "RR07": {"definition": _definition_tsv(threshold="-1")},
            "RR12": {"definition": _definition_tsv(owner_accepted_on="")},
        }
        for req, kwargs in cases.items():
            with self.subTest(req=req):
                self.assertEqual(_ids(_evaluate(*_valid_reference(**kwargs))), [req])
        mutations = {
            "RR02": lambda r: r.update(source_sha256="0" * 64),
            "RR04": lambda r: r.update(assay="ELISA"),
            "RR05": lambda r: r.update(compartment="stroma"),
            "RR09": lambda r: r.update(outcome_blind=False),
        }
        for req, mutate in mutations.items():
            reference, spec, root = _valid_reference()
            mutate(reference)
            with self.subTest(req=req):
                failures = _ids(_evaluate(reference, spec, root))
                self.assertIn(req, failures)
                if (
                    req != "RR05"
                ):  # a moved compartment also contradicts the donors file
                    self.assertEqual(failures, [req])

    def test_an_inapplicable_measurement_is_refused(self) -> None:
        # Review B5: a non-RNA assay, another layer, another per-cell quantity.
        reference, spec, root = _valid_reference()
        reference["assay"] = "ELISA"
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR04"])
        for definition in (
            _definition_tsv(layer="raw UMI"),
            _definition_tsv(per_cell_quantity="protein_ng_per_ml"),
        ):
            self.assertEqual(
                _ids(_evaluate(*_valid_reference(definition=definition))), ["RR04"]
            )

    def test_the_per_cell_quantity_is_computed_as_specified(self) -> None:
        self.assertEqual(P.per_cell_quantity(3.0, 6000.0, "count"), 3.0)
        self.assertEqual(P.per_cell_quantity(3.0, 6000.0, "count_per_10k"), 5.0)
        for bad in ((3.0, 0.0, "count_per_10k"), (3.0, 10.0, "cpm")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                P.per_cell_quantity(*bad)
        spec = P.mapping_specification()["high_state_definition"]
        self.assertEqual(
            set(spec["per_cell_quantity_definitions"]), set(P.PER_CELL_QUANTITIES)
        )

    def test_unaccepted_or_unevidenced_definitions_are_refused(self) -> None:
        # Review B1 round 2: evidence and the owner's acceptance are required.
        for changes in (
            {"evidence_citation": ""},
            {"evidence_kind": "analyst_choice"},
            {"owner_accepted_on": ""},
        ):
            with self.subTest(changes=changes):
                failures = _evaluate(
                    *_valid_reference(definition=_definition_tsv(**changes))
                )
                self.assertEqual(_ids(failures), ["RR12"])

    def test_too_few_reference_donors_is_refused(self) -> None:
        reference, spec, root = _valid_reference()
        spec["parameters"]["min_reference_donors"]["value"] = 6
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR07"])

    def test_an_unresolved_condition_class_is_refused(self) -> None:
        cnt = P.CONDITION_CLASS["CNT"]
        reference, spec, root = _valid_reference(
            donors=DONORS_TSV.replace("hormone_treated", cnt)
        )
        reference["condition_class"] = cnt
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR08"])

    def test_open_owner_parameters_block_even_a_valid_reference(self) -> None:
        # Review B4: an unset or pending parameter keeps the gate closed.
        reference, _, root = _valid_reference()
        pending = P.mapping_specification()
        pending["parameters"]["min_reference_donors"] = {
            "value": None,
            "provenance": P.PENDING,
        }
        self.assertEqual(_ids(_evaluate(reference, pending, root)), ["RR11"])
        spec = P.mapping_specification()
        spec["parameters"]["min_reference_donors"] = {
            "value": 5,
            "provenance": "fitted",
        }
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR11"])

    def test_a_null_reference_path_blocks_mechanically(self) -> None:
        self.assertIsNone(self.gate["policy_reference_path"])
        self.assertEqual(self.gate["verdict"], "BLOCKED_REFERENCE_REQUIRED")
        self.assertEqual(self.gate["ready_nodes"], [])
        self.assertTrue(
            self.gate["unmet_requirements"]["E_KLF12_HIGH"][0].startswith("RR01")
        )
        self.assertEqual(self.status["numerical_personalization"], "BLOCKED")
        self.assertEqual(
            self.status["status"], "STRUCTURAL_MAPPING_READY_BUT_REFERENCE_BLOCKED"
        )
        self.assertFalse(self.status["phase2_complete"])

    def test_a_reference_path_outside_the_repository_is_refused(self) -> None:
        policy = {"reference_strategy": {"reference_path": "../../etc/passwd"}}
        loaded = P.load_reference_manifest(ROOT, policy)
        spec = P.mapping_specification()
        self.assertEqual(_ids(_evaluate(loaded, spec, ROOT)), ["RR01"])

    def test_every_requirement_in_the_table_is_checked(self) -> None:
        source = (SRC / "dt_adoc/personalization/phase2a_contract.py").read_text(
            encoding="utf-8"
        )
        for row in _tsv(P.OUT_REQUIREMENTS):
            self.assertIn(f'"{row["req_id"]}: ', source)


def _bridge_tsv(**changes: str) -> str:
    row = {
        "bridge_statement": P.BRIDGE_ASSUMPTION,
        "evidence_citation": "doi:10.0000/synthetic-bridge",
        "evidence_kind": "independent_validation",
        "independent_of_adoc": "true",
        "owner_accepted_on": "2026-01-03",
        **changes,
    }
    return "\t".join(row) + "\n" + "\t".join(row.values()) + "\n"


def _with_bridge(text: str, *, commit: bool = True) -> tuple[dict, Path]:
    reference, _, root = _valid_reference()
    reference["bridge_validation_path"] = "reference/bridge.tsv"
    reference["bridge_validation_sha256"] = _write(root, "reference/bridge.tsv", text)
    if commit:
        _git(root, "add", "reference/bridge.tsv")
        _git(root, "commit", "-q", "-m", "bridge")
    return reference, root


class ClaimLevel(_Computed):
    """Owner decision on B1: every value is an assumption-conditioned scenario;
    RR13 is the only route to measured personalization."""

    def test_every_summary_row_carries_the_scenario_claim_and_the_bridge(self) -> None:
        self.assertTrue(self.summaries)
        for row in self.summaries:
            self.assertEqual(row["claim_level"], P.CLAIM_LEVEL)
            self.assertEqual(row["bridge_assumption"], P.BRIDGE_ASSUMPTION)
        self.assertEqual(self.spec["claim_level"], P.CLAIM_LEVEL)
        self.assertEqual(self.status["claim_level"], P.CLAIM_LEVEL)

    def test_no_value_is_described_as_measured_personalization(self) -> None:
        for row in self.summaries:
            self.assertNotEqual(row["claim_level"], P.MEASURED_CLAIM_LEVEL)
        self.assertEqual(self.gate["claim_level_if_ready"], P.CLAIM_LEVEL)

    def test_measured_personalization_is_blocked_on_rr13(self) -> None:
        self.assertEqual(
            self.gate["measured_personalization_verdict"], "BLOCKED_BRIDGE_UNVALIDATED"
        )
        self.assertEqual(self.status["measured_personalization"], "BLOCKED")
        unmet = self.gate["measured_unmet_requirements"]["E_KLF12_HIGH"]
        self.assertIn("RR13", _ids(unmet))

    def test_the_measured_rule_names_what_the_code_requires(self) -> None:
        # Measured = the ordinary gate (RR01-RR14, RR14 included) plus RR13.
        rule = self.gate["measured_personalization_rule"]
        self.assertIn("RR01-RR14", rule)
        self.assertIn("RR13", rule)
        applied = self.status["owner_decisions_applied"]
        for key in ("RR12_vocabulary", "boundary_rule", "B13"):
            self.assertIn(key, applied)
        # Owner decision D2 (2026-09-25, Phase 2B): set, not open.
        self.assertFalse(
            any(
                d.startswith("min_reference_donors")
                for d in self.status["owner_decisions_open"]
            )
        )
        self.assertIn("D2_min_reference_donors", applied)
        self.assertEqual(
            self.spec["parameters"]["min_reference_donors"],
            {"value": 3, "provenance": "owner_decided"},
        )

    def test_a_complete_scenario_reference_is_still_not_a_measurement(self) -> None:
        reference, spec, root = _valid_reference()
        self.assertEqual(_evaluate(reference, spec, root), [])
        self.assertEqual(
            _ids(P.evaluate_bridge_validation(reference, root=root)), ["RR13"]
        )

    def test_an_independent_accepted_bridge_validation_passes(self) -> None:
        reference, root = _with_bridge(_bridge_tsv())
        self.assertEqual(P.evaluate_bridge_validation(reference, root=root), [])

    def test_every_weakened_bridge_validation_is_refused(self) -> None:
        cases = {
            "another bridge": _bridge_tsv(bridge_statement="cells equal compartments."),
            "not independent": _bridge_tsv(independent_of_adoc="false"),
            "no evidence": _bridge_tsv(evidence_citation=""),
            "wrong kind": _bridge_tsv(evidence_kind="analyst_judgement"),
            "not accepted": _bridge_tsv(owner_accepted_on=""),
            "two rows": _bridge_tsv() + "\t".join(["x"] * 5) + "\n",
            "extra column": _bridge_tsv(outcome="1"),
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                reference, root = _with_bridge(text)
                self.assertEqual(
                    _ids(P.evaluate_bridge_validation(reference, root=root)), ["RR13"]
                )
        reference, root = _with_bridge(_bridge_tsv(), commit=False)
        self.assertEqual(
            _ids(P.evaluate_bridge_validation(reference, root=root)), ["RR13"]
        )
        reference, root = _with_bridge(_bridge_tsv())
        reference["bridge_validation_sha256"] = "0" * 64
        self.assertEqual(
            _ids(P.evaluate_bridge_validation(reference, root=root)), ["RR13"]
        )


class ProvenanceSchema(unittest.TestCase):
    """Sweep-2 blockers: malformed provenance values, cell counts and dates."""

    def test_a_malformed_cell_count_is_refused(self) -> None:
        for bad in ("NOT_A_NUMBER", "0", "-3", "2.5", ""):
            donors = DONORS_TSV.replace("\t405\n", f"\t{bad}\n")
            with self.subTest(n_cells=bad):
                failures = _evaluate(*_valid_reference(donors=donors))
                self.assertEqual(_ids(failures), ["RR02"])

    def test_malformed_citations_and_dates_are_refused(self) -> None:
        reference, spec, root = _valid_reference()
        reference["retrieved_on"] = "x"
        self.assertIn("RR02", _ids(_evaluate(reference, spec, root)))
        reference, spec, root = _valid_reference()
        reference["source_accession"] = "x"
        self.assertIn("RR02", _ids(_evaluate(reference, spec, root)))
        for changes in (
            {"evidence_citation": "x"},
            {"owner_accepted_on": "x"},
            {"owner_accepted_on": "2026-02-30"},
            {"owner_accepted_on": "2025-12-31"},  # before retrieval
        ):
            with self.subTest(changes=changes):
                failures = _evaluate(
                    *_valid_reference(definition=_definition_tsv(**changes))
                )
                self.assertEqual(_ids(failures), ["RR12"])
        for changes in ({"evidence_citation": "x"}, {"owner_accepted_on": "x"}):
            with self.subTest(bridge=changes):
                reference, root = _with_bridge(_bridge_tsv(**changes))
                self.assertEqual(
                    _ids(P.evaluate_bridge_validation(reference, root=root)), ["RR13"]
                )

    def test_well_formed_citations_are_accepted(self) -> None:
        for value in (
            "doi:10.7554/eLife.72626",
            "10.1000/xyz",
            "E-MTAB-15842",
            "GSE123456",
            "PRJNA123456",
        ):
            self.assertTrue(P._is_citation(value), value)
        for value in ("x", "doi:11.1/x", "see paper", ""):
            self.assertFalse(P._is_citation(value), value)


def _ready_shadow() -> Path:
    """A complete repository copy with a valid reference ACTIVATED, the
    pre-registration committed first: the end-to-end positive control."""
    _, _, root = _valid_reference()
    for relative in (
        P.EXTRACTION,
        P.NODE_SUPPORT_FINDINGS,
        P.NODE_SUPPORT_EVIDENCE,
        P.NODE_SUPPORT_QC,
        P.OBSERVATION_MAP,
        P.EXTERNAL_MANIFEST,
        P.DATA_MANIFEST,
        P.PHASE1B_SUMMARY,
        *(Path(p) for p in _json(P.PHASE1B_SUMMARY)["lineage"]["frozen_stage3_sha256"]),
    ):
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_bytes((ROOT / relative).read_bytes())
    shutil.copytree(
        CLOSURE / "models",
        root / "models",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    return root


class EndToEndReady(unittest.TestCase):
    """The READY transition is reachable, and its lineage names the reference."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = _ready_shadow()
        real = P.mapping_specification

        def owner_set() -> dict:
            spec = real()
            spec["parameters"]["min_reference_donors"] = {
                "value": 5,
                "provenance": "owner_decided",
            }
            return spec

        P.mapping_specification = owner_set
        try:
            cls.outputs = P.compute(cls.root)
        finally:
            P.mapping_specification = real

    def _json(self, relative: Path) -> dict:
        return json.loads(self.outputs[relative])

    def test_the_scenario_gate_opens_and_measured_stays_blocked(self) -> None:
        gate = self._json(P.OUT_GATE)
        self.assertEqual(gate["verdict"], "READY_FOR_MAPPING")
        self.assertEqual(gate["ready_nodes"], ["E_KLF12_HIGH"])
        self.assertEqual(
            gate["measured_personalization_verdict"], "BLOCKED_BRIDGE_UNVALIDATED"
        )
        status = self._json(P.OUT_STATUS)
        self.assertEqual(
            status["status"], "STRUCTURAL_MAPPING_READY_REFERENCE_AVAILABLE"
        )
        self.assertTrue(status["gates"]["G6_spec_parameters_owner_controlled"])
        self.assertEqual(status["measured_personalization"], "BLOCKED")
        self.assertEqual(status["mapping_eligibility_counts"][P.ELIGIBLE], 1)
        self.assertFalse(status["phase2_complete"])

    def test_the_lineage_names_the_active_reference(self) -> None:
        rows = {
            r["stage"]: r
            for r in csv.DictReader(
                self.outputs[P.OUT_PROVENANCE].splitlines(), delimiter="\t"
            )
        }
        identity = rows["6_external_reference"]["identity"]
        self.assertIn(_MANIFEST, identity)
        self.assertIn(_sha(self.root / _MANIFEST), identity)
        self.assertIn("READY_FOR_MAPPING", identity)

    def test_a_fitted_parameter_fails_the_structural_gate(self) -> None:
        real = P.mapping_specification

        def fitted() -> dict:
            spec = real()
            spec["parameters"]["min_reference_donors"] = {
                "value": 5,
                "provenance": "fitted",
            }
            return spec

        P.mapping_specification = fitted
        try:
            with self.assertRaises(P.Phase2AError):
                P.compute(self.root)
        finally:
            P.mapping_specification = real


class SweepThree(unittest.TestCase):
    """Sweep-3 blockers: preregistered CONTENT ordering, parameter domain, RR14."""

    def test_an_early_placeholder_rewritten_later_is_refused(self) -> None:
        # B11: the path was committed first, but the declared bytes only after
        # the reference was selected and activated.
        reference, spec, root = _valid_reference()
        digest = _write(root, _PREREG, "rewritten after selection\n")
        _git(root, "commit", "-qam", "rewrite prereg")
        reference["preregistration_sha256"] = digest
        self.assertEqual(
            sorted(_ids(_evaluate(reference, spec, root))), ["RR10", "RR14"]
        )

    def test_parameters_need_a_domain_value_and_the_owner_provenance(self) -> None:
        # B12: -1, 0, "five", a boolean, and an outcome-tuned provenance.
        reference, _, root = _valid_reference()
        for value, provenance in (
            (-1, "owner_decided"),
            (0, "owner_decided"),
            ("five", "owner_decided"),
            (True, "owner_decided"),
            (5, "fit_to_adhesion_outcome"),
            (5, "owner_decision_pending"),
        ):
            spec = P.mapping_specification()
            spec["parameters"]["min_reference_donors"] = {
                "value": value,
                "provenance": provenance,
            }
            with self.subTest(value=value, provenance=provenance):
                self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR11"])

    def test_rr14_requires_comparability_derivation_and_variants(self) -> None:
        for changes in (
            {"comparability": "assumed"},
            {"comparability_evidence": "x"},
            {"threshold_derivation": ""},
            {"threshold_variants": "3.0"},
            {"threshold_variants": "2.0;3.0"},  # one variant is the primary
            {"threshold_variants": "1.0;1.0"},
            {"threshold_variants": "1.0;nan"},
            {"threshold_variants": "a;b"},
            {"variant_selection": "best_fit"},
            {"comparability": "cross_dataset_calibration"},  # no calibration artifact
        ):
            with self.subTest(changes=changes):
                failures = _evaluate(
                    *_valid_reference(definition=_definition_tsv(**changes))
                )
                self.assertEqual(_ids(failures), ["RR14"])

    def test_a_preregistered_committed_calibration_opens_the_calibration_route(
        self,
    ) -> None:
        definition = _definition_tsv(comparability="cross_dataset_calibration")
        calibration = "a\tb\n1\t2\n"
        self.assertEqual(
            _evaluate(
                *_valid_reference(definition=definition, calibration=calibration)
            ),
            [],
        )
        # B13 round 3: a calibration the pre-registration does not name is refused.
        unbound = _valid_reference(
            definition=definition, calibration=calibration, register_calibration=False
        )
        self.assertEqual(_ids(_evaluate(*unbound)), ["RR14"])
        # B14: the same bytes at a path the pre-registration never named.
        reference, spec, root = _valid_reference(
            definition=definition, calibration=calibration
        )
        (root / "elsewhere").mkdir()
        (root / "elsewhere/cal.tsv").write_text(calibration, encoding="utf-8")
        _git(root, "add", "elsewhere/cal.tsv")
        _git(root, "commit", "-q", "-m", "moved calibration")
        reference["calibration_path"] = "elsewhere/cal.tsv"
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR14"])
        # B16: a path merely MENTIONED (not bound as calibration_path) is refused.
        definition2 = definition
        reference, spec, root = _valid_reference(
            definition=definition2, calibration=calibration, register_calibration=False
        )
        text = (root / _PREREG).read_text(encoding="utf-8")
        text += (
            f"see also reference/calibration.tsv ({reference['calibration_sha256']})\n"
        )
        reference["preregistration_sha256"] = _write(root, _PREREG, text)
        _git(root, "commit", "-qam", "mention only")
        self.assertIn("RR14", _ids(_evaluate(reference, spec, root)))
        # And one whose declared content was never committed.
        reference, spec, root = _valid_reference(
            definition=definition, calibration=calibration
        )
        reference["calibration_sha256"] = _write(
            root, "reference/calibration.tsv", "a\n9\n"
        )
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR14"])

    def test_variants_absent_from_the_frozen_preregistration_are_refused(self) -> None:
        # B13 round 2: the definition (and so its variants) must be named by the
        # pre-registration as frozen, not merely present later.
        reference, spec, root = _valid_reference()
        digest = _write(
            root,
            "reference/definition.tsv",
            _definition_tsv(threshold_variants="0.5;4.0"),
        )
        _git(root, "commit", "-qam", "variants changed after selection")
        reference["definition_sha256"] = digest
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR14"])

    def test_meeting_rr14_upgrades_no_claim(self) -> None:
        reference, spec, root = _valid_reference()
        self.assertEqual(_evaluate(reference, spec, root), [])
        self.assertEqual(
            _ids(P.evaluate_bridge_validation(reference, root=root)), ["RR13"]
        )
        sensitivity = P.mapping_specification()["sensitivity"]
        self.assertIn("never satisfy RR13", sensitivity["claim"])
        self.assertIn("ADOC outcomes", sensitivity["selection"])


class ProbeFindings(unittest.TestCase):
    """Pre-sweep probe: ADOC identity under other spellings, content-committed
    artifacts, ADOC objects as calibration/bridge, several pre-registered digests."""

    def test_adoc_donors_in_any_spelling_are_refused(self) -> None:
        for alias in ("sz09", " SZ09", "ADOC-SZ09", "sz_25"):
            donors = DONORS_TSV.replace("R1\t", f"{alias}\t")
            reference, spec, root = _valid_reference(donors=donors)
            reference["donor_ids"] = [alias, "R2", "R3", "R4", "R5"]
            with self.subTest(alias=alias):
                self.assertIn("RR03", _ids(_evaluate(reference, spec, root)))

    def test_the_adoc_accession_is_never_independent_evidence(self) -> None:
        for field in P.CITATION_FIELDS:
            with self.subTest(field=field):
                definition = _definition_tsv(**{field: "E-MTAB-15842"})
                failures = _evaluate(*_valid_reference(definition=definition))
                self.assertIn("RR03", _ids(failures))
        reference, root = _with_bridge(_bridge_tsv(evidence_citation="e-mtab-15842"))
        self.assertEqual(
            _ids(P.evaluate_bridge_validation(reference, root=root)), ["RR13"]
        )

    def test_bridge_content_must_be_the_committed_content(self) -> None:
        reference, root = _with_bridge(_bridge_tsv())
        digest = _write(
            root,
            "reference/bridge.tsv",
            _bridge_tsv(evidence_citation="doi:10.0000/late"),
        )
        reference["bridge_validation_sha256"] = digest
        self.assertEqual(
            _ids(P.evaluate_bridge_validation(reference, root=root)), ["RR13"]
        )

    def test_an_adoc_object_cannot_be_the_calibration_or_the_bridge(self) -> None:
        adoc = (ROOT / "data/proteinas secretadas ADOC.xlsx").read_bytes()
        definition = _definition_tsv(comparability="cross_dataset_calibration")
        reference, spec, root = _valid_reference(definition=definition)
        (root / "cal").mkdir()
        (root / "cal/c.xlsx").write_bytes(adoc)
        _git(root, "add", "cal/c.xlsx")
        _git(root, "commit", "-q", "-m", "calibration")
        reference.update(
            calibration_path="cal/c.xlsx", calibration_sha256=_sha(root / "cal/c.xlsx")
        )
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR14"])
        reference, root = _with_bridge(_bridge_tsv())
        forbidden = frozenset({reference["bridge_validation_sha256"]})
        failures = P.evaluate_bridge_validation(
            reference, root=root, forbidden_shas=forbidden
        )
        self.assertEqual(_ids(failures), ["RR13"])

    def test_a_preregistration_listing_several_definitions_is_refused(self) -> None:
        reference, spec, root = _valid_reference()
        text = (root / _PREREG).read_text(
            encoding="utf-8"
        ) + f"alternative: {'a' * 64}\n"
        digest = _write(root, _PREREG, text)
        _git(root, "commit", "-qam", "two candidates")
        reference["preregistration_sha256"] = digest
        self.assertIn("RR14", _ids(_evaluate(reference, spec, root)))


class OutcomeIndependence(_Computed):
    """15. Nothing outcome-derived can choose a reference, statistic or threshold."""

    def test_no_parameter_is_fitted(self) -> None:
        for name, parameter in self.spec["parameters"].items():
            with self.subTest(parameter=name):
                self.assertIn(parameter["provenance"], P.PERMITTED_PROVENANCE)
                self.assertTrue(P.parameter_set(parameter))
        for forbidden in ("fitted", "tuned_on_outcome", "estimated_from_adoc_donors"):
            self.assertIn(forbidden, self.spec["parameter_provenance_forbidden"])
        self.assertIn("never_from", self.spec["high_state_definition"])
        self.assertTrue(self.status["gates"]["G6_spec_parameters_owner_controlled"])

    def test_the_module_reads_no_outcome_or_model_output(self) -> None:
        code = (
            "import sys; sys.path.insert(0, 'src');"
            "import dt_adoc.personalization.phase2a_contract;"
            "print('\\n'.join(sorted(m for m in sys.modules if m.startswith('dt_adoc'))))"
        )
        loaded = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        for forbidden in (
            "dt_adoc.simulation",
            "dt_adoc.concordance",
            "dt_adoc.calibration",
            "dt_adoc.scoring",
            "dt_adoc.perturbations",
            "dt_adoc.experiments",
            "dt_adoc.observations",
        ):
            self.assertFalse(
                any(m == forbidden or m.startswith(forbidden + ".") for m in loaded),
                forbidden,
            )

    def test_no_outcome_file_is_opened(self) -> None:
        names = {p.name for p, _ in self.opened}
        for outcome in (
            "adoc_secreted_proteins.tsv",
            "calibration.yaml",
            "observation_model_map.tsv",
            "protocols.yaml",
        ):
            self.assertNotIn(outcome, names)
        self.assertFalse(any("concordance" in p.parts for p, _ in self.opened))


class Determinism(_Computed):
    """16. Regeneration is deterministic and equals what is committed."""

    def test_the_committed_outputs_equal_a_fresh_computation(self) -> None:
        for relative, text in self.outputs.items():
            with self.subTest(output=str(relative)):
                self.assertEqual((ROOT / relative).read_text(encoding="utf-8"), text)

    def test_two_computations_are_identical(self) -> None:
        self.assertEqual(P.compute(CLOSURE), self.outputs)

    def test_the_generator_is_registered_in_the_clock_frozen_guard(self) -> None:
        from tests.unit import test_generated_date_determinism as guard

        modules = {g.module: g for g in guard.GENERATORS}
        self.assertIn(P.__name__, modules)
        self.assertEqual(modules[P.__name__].outputs, P.OUTPUTS)


class Immutability(_Computed):
    """17-18. v0.5.1, Phase 1B and the frozen Stage-3 design are untouched."""

    def test_no_file_under_models_changed(self) -> None:
        self.assertEqual(P._tree_sha(CLOSURE, Path("models")), MODELS_TREE_SHA256)
        self.assertEqual(
            self.status["lineage"]["models_tree_sha256"], MODELS_TREE_SHA256
        )
        self.assertTrue(
            self.status["gates"]["G7_models_and_frozen_artifacts_unchanged"]
        )

    def test_the_frozen_artifacts_are_byte_identical(self) -> None:
        for relative, digest in FROZEN.items():
            with self.subTest(file=relative):
                self.assertEqual(_sha(ROOT / relative), digest)


class RepositoryMethodCitation(unittest.TestCase):
    """Owner RR14 schema change (2026-09-25): a custom threshold method may cite
    an immutable repository-local artifact, verified by commit, path and sha256."""

    def test_a_valid_repository_citation_satisfies_rr14(self) -> None:
        self.assertEqual(_evaluate(*_valid_reference(repo_method="valid")), [])

    def test_a_bad_repository_citation_is_not_a_citation(self) -> None:
        for mode in ("not_earliest", "wrong_sha", "outside_data"):
            with self.subTest(mode=mode):
                self.assertEqual(
                    _ids(_evaluate(*_valid_reference(repo_method=mode))), ["RR14"]
                )

    def test_an_edited_cited_artifact_is_refused(self) -> None:
        reference, spec, root = _valid_reference(repo_method="valid")
        (root / "methods/derivation.md").write_text("edited\n", encoding="utf-8")
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR14"])

    def _method_repo(self) -> tuple[Path, str, str]:
        tmp = tempfile.TemporaryDirectory()
        _TMPS.append(tmp)
        root = Path(tmp.name)
        _git(root, "init", "-q")
        digest = _write(root, "methods/derivation.md", "the frozen method\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "method")
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return root, commit, digest

    def _head(self, root: Path) -> str:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def test_the_cited_commit_must_strictly_precede_the_frozen_preregistration(
        self,
    ) -> None:
        root, commit, digest = self._method_repo()
        citation = f"repo:methods/derivation.md@{commit}#sha256:{digest}"
        _write(root, "later.txt", "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "later")
        later = self._head(root)
        self.assertTrue(P._repository_citation(citation, root, later, frozenset()))
        # equal to, or after, the frozen pre-registration: refused
        self.assertFalse(P._repository_citation(citation, root, commit, frozenset()))
        parent = subprocess.run(
            ["git", "-C", str(root), "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(parent, commit)
        self.assertFalse(P._repository_citation(citation, root, "", frozenset()))

    def test_a_citation_under_data_or_through_a_symlink_is_refused(self) -> None:
        root, commit, digest = self._method_repo()
        data_digest = _write(root, "data/method.md", "the frozen method\n")
        (root / "docs").mkdir()
        (root / "docs/method.md").symlink_to(root / "methods/derivation.md")
        (root / "linked").symlink_to(root / "data")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "data and links")
        frozen_later = self._head(root)
        _write(root, "after.txt", "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "after")
        frozen = self._head(root)
        self.assertTrue(
            P._repository_citation(
                f"repo:methods/derivation.md@{commit}#sha256:{digest}",
                root,
                frozen,
                frozenset(),
            )
        )
        # A symlink to an in-repo, non-data/ file, cited with the TARGET's own
        # earliest commit and digest: it would pass if the path were resolved
        # before the symlink check. Only the pre-resolve check refuses it.
        self.assertFalse(
            P._repository_citation(
                f"repo:docs/method.md@{commit}#sha256:{digest}",
                root,
                frozen,
                frozenset(),
            )
        )
        for cited in ("data/method.md", "docs/method.md", "linked/method.md"):
            with self.subTest(cited=cited):
                self.assertFalse(
                    P._repository_citation(
                        f"repo:{cited}@{frozen_later}#sha256:{data_digest}",
                        root,
                        frozen,
                        frozenset(),
                    )
                )

    def test_a_correctly_bound_data_citation_fails_rr14_in_the_full_gate(self) -> None:
        # Non-vacuous: the method file is committed under data/ and cited with
        # its own earliest commit and exact digest, strictly before the frozen
        # pre-registration -- the construction that passes under methods/. The
        # data/ exclusion is the only thing left to refuse it.
        self.assertEqual(_evaluate(*_valid_reference(repo_method="valid")), [])
        reference, spec, root = _valid_reference(repo_method="in_data")
        definition = (root / "reference/definition.tsv").read_text(encoding="utf-8")
        self.assertIn("repo:data/method.md@", definition)
        self.assertEqual(_ids(_evaluate(reference, spec, root)), ["RR14"])

    def test_free_text_and_unparsable_forms_stay_refused(self) -> None:
        for bad in (
            "our own method",
            "repo:methods/derivation.md",
            "repo:x@abc#sha256:def",
        ):
            with self.subTest(bad=bad):
                failures = _evaluate(
                    *_valid_reference(
                        definition=_definition_tsv(threshold_derivation=bad)
                    )
                )
                self.assertEqual(_ids(failures), ["RR14"])

    def test_only_threshold_derivation_may_cite_the_repository(self) -> None:
        _, _, root = _valid_reference(repo_method="valid")
        citation = next(
            line.split("\t")
            for line in (root / "reference/definition.tsv").read_text().splitlines()[1:]
        )
        header = (
            (root / "reference/definition.tsv").read_text().splitlines()[0].split("\t")
        )
        cited = dict(zip(header, citation))["threshold_derivation"]
        for field in ("evidence_citation", "comparability_evidence"):
            with self.subTest(field=field):
                failures = _evaluate(
                    *_valid_reference(definition=_definition_tsv(**{field: cited}))
                )
                self.assertIn(_ids(failures)[0], ("RR12", "RR14"))


if __name__ == "__main__":
    unittest.main()
