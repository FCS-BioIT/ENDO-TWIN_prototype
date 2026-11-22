"""The executable network, its dictionaries, evidence table and lineage agree."""

from __future__ import annotations

import csv
import re
import sys
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from endotwin.model import dependencies, load_model, read_tsv
from endotwin.topology import parse_bnd_rules

MODEL = load_model()
V010 = ROOT / "endotwin/models/endotwin-v0.1.0/network.bnd"
V010_LINEAGE = ROOT / "endotwin/models/endotwin-v0.1.0/lineage.tsv"
V060 = ROOT / "models/superset/adoc-literature-superset-v0.6.0/network.bnd"
SOURCE_COMMIT = "b1de5f90582f02291789eb72753fa5ab1f2d8c88"
EVIDENCE_CLASSES = {
    "experimental_definition",
    "literature_supported",
    "literature_supported_topic_level",
    "literature_supported_species_transfer",
    "literature_supported_contested",
    "literature_supported_route_unresolved",
    "adoc_supported",
    "simplifying_assumption",
    "alternative_hypothesis",
}


def _edge_rows(default: str) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (e["source"], e["target"]): e
        for e in MODEL.edges
        if e["in_default_network"] == default
    }


class NodeTables(unittest.TestCase):
    def test_dictionary_matches_network_in_order(self):
        self.assertEqual(list(MODEL.node_info), list(MODEL.rules))

    def test_every_node_has_a_known_compartment_and_layer(self):
        for node, info in MODEL.node_info.items():
            self.assertIn(
                info["compartment"],
                {"medium", "epithelium", "extracellular", "stroma"},
                node,
            )
            self.assertIn(
                info["layer"],
                {
                    "experimental_input",
                    "epithelial_intracellular",
                    "stromal_intracellular",
                    "extracellular_ligand",
                    "secreted_protein",
                    "functional_output",
                },
                node,
            )
            prefix = {
                "medium": "IN_",
                "epithelium": ("E_", "OUT_"),
                "extracellular": "X_",
                "stroma": ("S_", "OUT_"),
            }
            self.assertTrue(node.startswith(prefix[info["compartment"]]), node)
            if node.startswith("IN_"):
                self.assertEqual(info["layer"], "experimental_input")
                self.assertEqual(MODEL.rules[node], node)

    def test_three_functional_outputs_with_grant_readouts(self):
        readouts = {n: MODEL.node_info[n]["readouts"] for n in MODEL.outputs}
        self.assertEqual(
            readouts,
            {
                "OUT_EPITHELIAL_SECRETORY": "secretory signature",
                "OUT_EPITHELIAL_PROLIFERATION": "Ki67;EdU",
                "OUT_STROMAL_DECIDUALIZATION": "decidual signature",
            },
        )
        # The grant's secreted readouts sit on their own extracellular nodes.
        for node, readout in (
            ("X_PAEP", "PAEP"),
            ("X_PRL", "PRL"),
            ("X_IGFBP1", "IGFBP-1"),
        ):
            self.assertEqual(MODEL.node_info[node]["readouts"], readout)
            self.assertEqual(MODEL.node_info[node]["layer"], "secreted_protein")

    def test_bmp_ligand_and_pathway_activity_are_separate_nodes(self):
        self.assertEqual(MODEL.node_info["S_BMP2"]["entity_type"], "ligand_expression")
        self.assertEqual(
            MODEL.node_info["S_BMP_SMAD"]["entity_type"], "protein_activity"
        )
        self.assertEqual(MODEL.node_info["S_BMP_SMAD"]["readouts"], "pSMAD1/5/8")
        self.assertIn("IN_BMPR_INHIBITOR", MODEL.rules["S_BMP_SMAD"])
        self.assertNotIn("IN_BMPR_INHIBITOR", MODEL.rules["S_BMP2"])
        # The receptor reads the secreted ligand pool, not the expression node.
        self.assertIn("X_BMP2", MODEL.rules["S_BMP_SMAD"])
        self.assertEqual(MODEL.rules["X_BMP2"], "S_BMP2")

    def test_config_starts_every_node_off_and_observable(self):
        cfg = (MODEL.root / "baseline.cfg").read_text()
        for node in MODEL.rules:
            self.assertIn(f"{node}.istate = FALSE;", cfg)
            self.assertIn(f"{node}.is_internal = FALSE;", cfg)


class EvidenceTable(unittest.TestCase):
    def test_every_default_dependency_has_exactly_one_evidence_row(self):
        deps = dependencies(MODEL.rules)
        rows = _edge_rows("true")
        self.assertEqual(set(rows), set(deps))
        for pair, sign in deps.items():
            self.assertEqual(rows[pair]["sign"], sign, pair)

    def test_variant_only_dependencies_are_recorded(self):
        default = set(dependencies(MODEL.rules))
        variant_deps = set()
        for selection in MODEL.scenarios():
            variant_deps |= set(dependencies(MODEL.rules_for(selection))) - default
        self.assertEqual(variant_deps, set(_edge_rows("false")))

    def test_evidence_classes_are_from_the_vocabulary(self):
        for edge in MODEL.edges:
            self.assertIn(edge["evidence_class"], EVIDENCE_CLASSES, edge["edge_id"])

    def test_every_cited_reference_exists_and_corpus_links_agree(self):
        refs = {
            r["ref_id"]: r for r in read_tsv(ROOT / "endotwin/evidence/references.tsv")
        }
        corpus = {
            r["ref_id"]: r for r in read_tsv(ROOT / "context/literature/references.tsv")
        }
        for edge in MODEL.edges:
            for ref in filter(None, re.split(r"[;\s]+", edge["references"])):
                if ref == "none":
                    continue
                self.assertIn(ref, refs, edge["edge_id"])
        for ref in refs.values():
            if ref["corpus_ref_id"]:
                self.assertEqual(
                    ref["doi"].lower(),
                    corpus[ref["corpus_ref_id"]]["doi"].lower(),
                    ref["ref_id"],
                )
            self.assertTrue(ref["doi"].startswith("10."), ref["ref_id"])

    def test_cross_compartment_edges_are_the_declared_interface(self):
        crossing = {
            (e["source"], e["target"])
            for e in MODEL.edges
            if e["in_default_network"] == "true"
            and e["crossing"]
            in {
                "epithelium_to_extracellular",
                "extracellular_to_stroma",
                "stroma_to_extracellular",
                "extracellular_to_epithelium",
            }
        }
        declared = {(i["signal_node"], i["receiving_node"]) for i in MODEL.interface}
        self.assertEqual(crossing, declared)


class Lineage(unittest.TestCase):
    """v0.2.0 maps every node of its parent v0.1.0; v0.1.0 maps every v0.6.0 node."""

    rows = read_tsv(MODEL.root / "lineage.tsv")
    v010 = parse_bnd_rules(V010)
    v060 = parse_bnd_rules(V060)

    def test_every_v010_node_has_one_lineage_row(self):
        self.assertEqual(sorted(r["v010_node"] for r in self.rows), sorted(self.v010))

    def test_recorded_v010_rules_are_the_real_ones(self):
        for row in self.rows:
            self.assertEqual(
                row["v010_rule"], self.v010[row["v010_node"]], row["v010_node"]
            )

    def test_unchanged_rows_keep_their_logic_and_modified_rows_say_why(self):
        for row in self.rows:
            self.assertEqual(MODEL.rules[row["endotwin_node"]], row["endotwin_rule"])
            if row["change"] == "unchanged":
                self.assertEqual(
                    row["endotwin_rule"], row["v010_rule"], row["v010_node"]
                )
            else:
                self.assertEqual(row["change"], "modified")
                self.assertNotEqual(row["endotwin_rule"], row["v010_rule"])
                self.assertTrue(row["note"], row["v010_node"])

    def test_node_dictionary_lineage_agrees_with_lineage_table(self):
        changes = {r["endotwin_node"]: r["change"] for r in self.rows}
        for node, info in MODEL.node_info.items():
            if info["lineage_change"] == "new":
                self.assertNotIn(node, self.v010)
            else:
                self.assertEqual(info["lineage_change"], changes[node], node)

    def test_parent_lineage_still_covers_every_v060_node(self):
        parent = read_tsv(V010_LINEAGE)
        self.assertEqual(sorted(r["v060_node"] for r in parent), sorted(self.v060))
        for row in parent:
            if row["v060_rule"] != "(composite)":
                self.assertEqual(row["v060_rule"], self.v060[row["v060_node"]])


class Provenance(unittest.TestCase):
    def test_provenance_names_the_source_commit(self):
        payload = tomllib.loads((MODEL.root / "provenance.toml").read_text())
        self.assertEqual(payload["derived_from_commit"], SOURCE_COMMIT)
        self.assertFalse(payload["calibrated"])
        self.assertFalse(payload["biologically_validated"])
        self.assertFalse(payload["physical_time_mapping"])
        origin = (ROOT / "docs/ORIGIN.md").read_text()
        self.assertIn(SOURCE_COMMIT, origin)

    def test_tables_are_rectangular(self):
        for name in (
            "node_dictionary.tsv",
            "edges.tsv",
            "rule_variants.tsv",
            "lineage.tsv",
            "interface.tsv",
        ):
            with (MODEL.root / name).open(newline="") as handle:
                rows = list(csv.reader(handle, delimiter="\t"))
            widths = {len(r) for r in rows}
            self.assertEqual(len(widths), 1, name)


if __name__ == "__main__":
    unittest.main()
