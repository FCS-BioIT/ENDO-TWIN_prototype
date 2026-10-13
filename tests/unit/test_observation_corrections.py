"""The post-closure observation-map correction layer (OC-001, OC-002: E_PC6 = PCSK5).

What is pinned here:

- the frozen map, the frozen node-support evidence and the closed-phase map are
  untouched, and the corrections file is a declared post-closure addition;
- the corrected map is exactly the frozen map with the declared corrections, and
  a correction may change only the gene fields, never a field the frozen-map
  readers (Stage 3, U8) use;
- the post-hoc PCSK5 evidence is labelled post hoc, is bound to the declared
  object, reproduces from the per-cell table when that table is available, and
  its node row is its gene row;
- no live artifact carries PCSK6, and the live verdict logic is the frozen rule.
"""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from dt_adoc import closure_replay as R
from dt_adoc.scrna import node_support as N
from dt_adoc.scrna import node_support_contract as C
from dt_adoc.scrna import node_support_expectations as X
from dt_adoc.scrna import observation_corrections as O
from dt_adoc.scrna import rna_endpoint_concordance as E

ROOT = Path(__file__).resolve().parents[2]
GENE_FIELDS = {"biological_state", "measurement_features"}
LIVE_ARTIFACTS = (
    "docs/scrna_corrections/scrna_observation_map_corrected.tsv",
    "docs/u6_semantics/component_map.tsv",
    "docs/rna_endpoint_concordance/concordance.tsv",
    "docs/scrna_corrections/pc6_pcsk5/evidence.tsv",
)


def _tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class CorrectionLayer(unittest.TestCase):
    def test_corrections_file_is_a_declared_post_closure_addition(self) -> None:
        self.assertIn(str(O.CORRECTIONS), R.POST_CLOSURE_FILES)
        self.assertEqual(R.undeclared_drift(ROOT), [])

    def test_the_frozen_writer_reproduces_the_frozen_map(self) -> None:
        fields, rows = O._frozen_map(ROOT)
        self.assertEqual(
            O.render_map(fields, rows),
            (ROOT / O.FROZEN_MAP).read_text(encoding="utf-8"),
        )

    def test_the_corrected_map_is_regenerated_byte_for_byte(self) -> None:
        self.assertEqual(
            (ROOT / O.CORRECTED_MAP).read_text(encoding="utf-8"),
            O.render_map(*O.corrected_map_rows(ROOT)),
        )

    def test_corrected_map_differs_from_frozen_only_in_declared_cells(self) -> None:
        frozen = {r["mapping_id"]: r for r in _tsv(ROOT / O.FROZEN_MAP)}
        corrected = {r["mapping_id"]: r for r in _tsv(ROOT / O.CORRECTED_MAP)}
        declared = {(c["mapping_id"], c["field"]) for c in O.load_corrections(ROOT)}
        changed = {
            (mapping, field)
            for mapping, row in corrected.items()
            for field, value in row.items()
            if frozen[mapping][field] != value
        }
        self.assertEqual(changed, declared)

    def test_a_correction_may_change_only_gene_fields(self) -> None:
        # Stage 3 and U8 stay on the frozen map because they read activation
        # status and observability class only; this keeps that true.
        for fix in O.load_corrections(ROOT):
            self.assertIn(fix["field"], GENE_FIELDS, fix["correction_id"])
            self.assertEqual(fix["status"], O.POST_HOC)

    def test_a_correction_against_the_wrong_frozen_value_refuses(self) -> None:
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in (O.FROZEN_MAP, O.CORRECTIONS):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / rel, root / rel)
            text = (root / O.CORRECTIONS).read_text(encoding="utf-8")
            (root / O.CORRECTIONS).write_text(
                text.replace("\tPCSK6\tPCSK5\t", "\tPCSK7\tPCSK5\t"), encoding="utf-8"
            )
            with self.assertRaises(O.CorrectionError):
                O.corrected_map_rows(root)

    def test_e_pc6_reads_the_gene_its_entity_map_names(self) -> None:
        corrected = C.assessable_nodes(ROOT / O.CORRECTED_MAP)
        self.assertEqual(C.features(corrected["E_PC6"]), ("PCSK5",))
        entities = {
            r["node_id"]: r
            for r in _tsv(ROOT / "config/node_entity_map.tsv")
            if r["model_version"] == "adoc-literature-superset-v0.6.0"
        }
        self.assertEqual(entities["E_PC6"]["entity"], "PCSK5")
        self.assertIn("PC6", O.GENE_IDENTITY["PCSK5"]["alias_symbols"])
        self.assertEqual(
            O.superseded(ROOT), {"E_PC6": {"removed": ("PCSK6",), "added": ("PCSK5",)}}
        )


class PostHocEvidence(unittest.TestCase):
    def setUp(self) -> None:
        self.findings = json.loads((ROOT / O.PC6_FINDINGS).read_text(encoding="utf-8"))
        self.evidence = _tsv(ROOT / O.PC6_EVIDENCE)

    def test_labelled_post_hoc_and_bound_to_the_declared_object(self) -> None:
        self.assertEqual(
            self.findings["registration_status"], "post_hoc_not_preregistered"
        )
        provenance = self.findings["provenance"]
        self.assertEqual(provenance["source_binding"], "verified")
        self.assertEqual(provenance["source_sha256_observed"], N.source_digest(ROOT))
        self.assertEqual(self.findings["reproduction_check"]["result"], "identical")
        self.assertTrue(
            self.findings["object_identity_check"]["corrected_gene_present"]
        )
        self.assertIn(
            "PCSK5", self.findings["object_identity_check"]["pcsk_features_in_object"]
        )

    def test_covers_every_frozen_unit_with_a_gene_row_and_an_equal_node_row(
        self,
    ) -> None:
        frozen_units = {r["unit_id"] for r in _tsv(ROOT / O.FROZEN_EVIDENCE)}
        by_key = {(r["unit_id"], r["level"], r["name"]): r for r in self.evidence}
        self.assertEqual(len(self.evidence), 2 * len(frozen_units))
        numeric = ("f", "f_ci_lo", "f_ci_hi", "d", "d_ci_lo", "d_ci_hi")
        for unit in frozen_units:
            gene = by_key[(unit, "gene", "PCSK5")]
            node = by_key[(unit, "node", "E_PC6")]
            self.assertEqual([gene[k] for k in numeric], [node[k] for k in numeric])

    def test_single_feature_node_rows_equal_their_gene_rows_in_the_frozen_audit(
        self,
    ) -> None:
        # The premise that lets node:E_PC6 be copied from gene:PCSK5.
        rows = {
            (r["unit_id"], r["level"], r["name"]): r
            for r in _tsv(ROOT / O.FROZEN_EVIDENCE)
        }
        frozen_nodes = C.assessable_nodes()
        singles = {
            n: C.features(r)[0]
            for n, r in frozen_nodes.items()
            if len(C.features(r)) == 1
        }
        checked = 0
        for (unit, level, name), row in rows.items():
            if level == "node" and name in singles:
                gene = rows[(unit, "gene", singles[name])]
                self.assertEqual(row["f"], gene["f"])
                self.assertEqual(row["f_ci_lo"], gene["f_ci_lo"])
                self.assertEqual(row["d_ci_hi"], gene["d_ci_hi"])
                checked += 1
        self.assertGreater(checked, 100)

    @unittest.skipUnless(
        O.DEFAULT_PER_CELL.is_file(), "per-cell table is outside the repo"
    )
    def test_re_derivation_from_the_per_cell_table_reproduces_the_committed_files(
        self,
    ) -> None:
        record = N.extraction_provenance(O.DEFAULT_PER_CELL)
        evidence, findings = O.derive(O.DEFAULT_PER_CELL, record, root=ROOT)
        self.assertEqual(
            [{k: str(v) for k, v in row.items()} for row in evidence], self.evidence
        )
        self.assertEqual(json.loads(json.dumps(findings)), self.findings)


class LiveConsumers(unittest.TestCase):
    def test_no_live_artifact_carries_the_superseded_gene(self) -> None:
        for rel in LIVE_ARTIFACTS:
            self.assertNotIn("PCSK6", (ROOT / rel).read_text(encoding="utf-8"), rel)

    def test_live_evidence_drops_every_superseded_row(self) -> None:
        live = O.live_evidence_rows(ROOT)
        self.assertFalse([r for r in live if r["name"] == "PCSK6"])
        pc6 = [r for r in live if r["level"] == "node" and r["name"] == "E_PC6"]
        corrected = [r for r in _tsv(ROOT / O.PC6_EVIDENCE) if r["level"] == "node"]
        self.assertEqual(pc6, corrected)
        frozen = _tsv(ROOT / O.FROZEN_EVIDENCE)
        dropped = [
            r
            for r in frozen
            if r["name"] == "PCSK6" or (r["level"] == "node" and r["name"] == "E_PC6")
        ]
        self.assertEqual(len(live), len(frozen) - len(dropped) + len(corrected) * 2)

    def test_concordance_reads_pcsk5_for_e_pc6(self) -> None:
        row = next(r for r in E.read_table() if r["model_node"] == "E_PC6")
        self.assertEqual(row["rna_features_voting"], "PCSK5")
        self.assertEqual(row["rna_features_committed"], "PCSK5")
        self.assertTrue(row["rna_log2_fold_by_gene"].startswith("PCSK5["))

    def test_the_program_verdict_is_the_frozen_rule_for_every_node(self) -> None:
        stats = E.load_stats()
        expected = {
            r["model_node"]: r["expected_cnt_to_ht"] for r in X.expectation_table()
        }
        programs = C.direction_vote_programs()
        for node, row in C.assessable_nodes().items():
            compartment = C.COMPARTMENT_OF_NODE.get(row["compartment"])
            if compartment not in C.PRIMARY_COMPARTMENTS:
                continue
            frozen = N.member_verdict(node, compartment, stats, {})
            ours = O.program_verdict(
                node,
                compartment,
                stats,
                programs[node],
                C.features(row),
                expected[node],
            )
            self.assertEqual(ours["verdict"], frozen["verdict"], node)
            self.assertEqual(ours.get("per_donor"), frozen.get("per_donor"), node)
            self.assertEqual(ours["program"], frozen["program"], node)


if __name__ == "__main__":
    unittest.main()
