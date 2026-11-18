from __future__ import annotations

import csv
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


REF_RE = re.compile(r"\bREF-\d{3}\b")


def _load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _collect_refs(value: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            refs.update(_collect_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.update(_collect_refs(item))
    elif isinstance(value, str):
        refs.update(REF_RE.findall(value))
    return refs


class LiteratureContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.literature_dir = ROOT / "context" / "literature"

    def test_expected_literature_files_exist(self) -> None:
        expected = {
            "README.md",
            "knowledge-base.yaml",
            "embryo-adhesion-review.md",
            "codex-ingestion.md",
            "references.tsv",
            "source-provenance.tsv",
            "mechanisms.tsv",
            "perturbations.tsv",
            "environmental-factors.tsv",
            "evidence-gaps.tsv",
            "candidate-nodes.tsv",
            "candidate-edges.tsv",
            "validation-report.md",
        }
        observed = {
            path.name for path in self.literature_dir.iterdir() if path.is_file()
        }
        self.assertTrue(expected.issubset(observed), sorted(expected - observed))

    def test_knowledge_base_and_tables_parse(self) -> None:
        payload = yaml.safe_load(
            (self.literature_dir / "knowledge-base.yaml").read_text(encoding="utf-8")
        )
        self.assertIsInstance(payload, dict)
        self.assertEqual(
            payload["knowledge_base_id"], "adoc-embryo-adhesion-literature-v0.1.0"
        )
        for name in [
            "references.tsv",
            "source-provenance.tsv",
            "mechanisms.tsv",
            "perturbations.tsv",
            "environmental-factors.tsv",
            "evidence-gaps.tsv",
            "candidate-nodes.tsv",
            "candidate-edges.tsv",
        ]:
            rows = _load_tsv(self.literature_dir / name)
            self.assertGreater(len(rows), 0, name)

    def test_reference_ids_resolve(self) -> None:
        payload = yaml.safe_load(
            (self.literature_dir / "knowledge-base.yaml").read_text(encoding="utf-8")
        )
        refs = {
            row["ref_id"] for row in _load_tsv(self.literature_dir / "references.tsv")
        }
        self.assertEqual(
            len(refs), len(_load_tsv(self.literature_dir / "references.tsv"))
        )

        used_refs = _collect_refs(payload)
        for name in [
            "candidate-nodes.tsv",
            "candidate-edges.tsv",
            "mechanisms.tsv",
            "perturbations.tsv",
        ]:
            for row in _load_tsv(self.literature_dir / name):
                used_refs.update(REF_RE.findall(row.get("refs", "")))
        self.assertTrue(used_refs)
        self.assertEqual(sorted(used_refs - refs), [])

    def test_candidate_edges_resolve_to_known_nodes(self) -> None:
        candidate_nodes = {
            row["node_id"]
            for row in _load_tsv(self.literature_dir / "candidate-nodes.tsv")
        }
        baseline_nodes = {
            row["node_id"] for row in _load_tsv(ROOT / "models" / "specs" / "nodes.tsv")
        }
        allowed = candidate_nodes | baseline_nodes
        for row in _load_tsv(self.literature_dir / "candidate-edges.tsv"):
            self.assertIn(row["source"], allowed, row["edge_id"])
            self.assertIn(row["target"], allowed, row["edge_id"])


if __name__ == "__main__":
    unittest.main()
