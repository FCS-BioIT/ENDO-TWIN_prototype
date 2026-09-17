from __future__ import annotations

import csv
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


MODEL_DIR = ROOT / "models" / "extended" / "adoc-literature-v0.2.0"
NODE_RE = re.compile(r"^\s*Node\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{")
LOGIC_RE = re.compile(r"^\s*logic\s*=\s*(.+?)\s*;\s*$")


def _load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _bnd_nodes_and_logic(path: Path) -> tuple[list[str], dict[str, str]]:
    ordered: list[str] = []
    logic_map: dict[str, str] = {}
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        node_match = NODE_RE.match(line)
        if node_match:
            current = node_match.group(1)
            ordered.append(current)
            continue
        logic_match = LOGIC_RE.match(line)
        if logic_match and current is not None:
            logic_map[current] = logic_match.group(1)
    return ordered, logic_map


def _cfg_nodes(path: Path) -> set[str]:
    nodes: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("//", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key.startswith("[") and key.endswith("].istate"):
            key = key[1:-8]
        elif key.endswith((".istate", ".is_internal")):
            key = key.rsplit(".", 1)[0]
        else:
            continue
        nodes.add(key)
    return nodes


class ExtendedModelContractTest(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        expected = {
            "README.md",
            "provenance.toml",
            "uncertainty_notes.md",
            "differences_from_baseline.md",
            "network.bnd",
            "baseline.cfg",
            "node_dictionary.tsv",
            "edge_evidence.tsv",
            "phenotype_contract.tsv",
            "conditions/untreated.cfg",
            "conditions/hormone_treated.cfg",
            "conditions/hormone_treated_mifepristone.cfg",
            "conditions/hormone_treated_anti_spp1.cfg",
            "conditions/embryo_absent.cfg",
            "conditions/embryo_incompetent.cfg",
            "conditions/excess_er_stress.cfg",
            "conditions/high_ecm_stiffness.cfg",
            "conditions/basal_maternal.cfg",
            "conditions/e2_primed_maternal.cfg",
            "conditions/hormone_treated_maternal.cfg",
            "conditions/adhesion_challenge_basal.cfg",
            "conditions/adhesion_challenge_hormone_treated.cfg",
            "conditions/adhesion_challenge_hormone_treated_mifepristone.cfg",
            "conditions/adhesion_challenge_hormone_treated_anti_spp1.cfg",
            "conditions/adhesion_challenge_excess_er_stress.cfg",
            "conditions/adhesion_challenge_high_ecm_stiffness.cfg",
            "conditions/adhesion_challenge_washout.cfg",
        }
        for relative in expected:
            self.assertTrue((MODEL_DIR / relative).is_file(), relative)

    def test_node_and_edge_tables_are_consistent(self) -> None:
        nodes = _load_tsv(MODEL_DIR / "node_dictionary.tsv")
        edges = _load_tsv(MODEL_DIR / "edge_evidence.tsv")
        node_ids = [row["node_id"] for row in nodes]
        self.assertEqual(len(node_ids), len(set(node_ids)))
        edge_ids = [row["edge_id"] for row in edges]
        self.assertEqual(len(edge_ids), len(set(edge_ids)))
        node_id_set = set(node_ids)
        for row in edges:
            self.assertIn(row["source"], node_id_set, row["edge_id"])
            self.assertIn(row["target"], node_id_set, row["edge_id"])

    def test_every_catalog_node_has_a_boolean_rule(self) -> None:
        node_ids = [
            row["node_id"] for row in _load_tsv(MODEL_DIR / "node_dictionary.tsv")
        ]
        bnd_nodes, logic_map = _bnd_nodes_and_logic(MODEL_DIR / "network.bnd")
        self.assertEqual(bnd_nodes, node_ids)
        for node_id in node_ids:
            self.assertIn(node_id, logic_map)
            self.assertTrue(logic_map[node_id].strip(), node_id)

    def test_cfgs_reference_known_nodes(self) -> None:
        node_ids = {
            row["node_id"] for row in _load_tsv(MODEL_DIR / "node_dictionary.tsv")
        }
        for relative in [
            "baseline.cfg",
            "conditions/untreated.cfg",
            "conditions/hormone_treated.cfg",
            "conditions/hormone_treated_mifepristone.cfg",
            "conditions/hormone_treated_anti_spp1.cfg",
            "conditions/embryo_absent.cfg",
            "conditions/embryo_incompetent.cfg",
            "conditions/excess_er_stress.cfg",
            "conditions/high_ecm_stiffness.cfg",
            "conditions/basal_maternal.cfg",
            "conditions/e2_primed_maternal.cfg",
            "conditions/hormone_treated_maternal.cfg",
            "conditions/adhesion_challenge_basal.cfg",
            "conditions/adhesion_challenge_hormone_treated.cfg",
            "conditions/adhesion_challenge_hormone_treated_mifepristone.cfg",
            "conditions/adhesion_challenge_hormone_treated_anti_spp1.cfg",
            "conditions/adhesion_challenge_excess_er_stress.cfg",
            "conditions/adhesion_challenge_high_ecm_stiffness.cfg",
            "conditions/adhesion_challenge_washout.cfg",
        ]:
            cfg_nodes = _cfg_nodes(MODEL_DIR / relative)
            self.assertEqual(sorted(cfg_nodes - node_ids), [], relative)


if __name__ == "__main__":
    unittest.main()
