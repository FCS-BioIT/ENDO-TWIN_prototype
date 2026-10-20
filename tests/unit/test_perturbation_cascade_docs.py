"""The committed perturbation-cascade documentation artifacts match their records.

Runs on the committed tree alone (no MaBoSS, no ``output/``): every archived
historical file named in ``ORIGINAL_SHA256SUMS.tsv`` that is committed matches
its original hash, no figure is committed, and every figure's hash is recorded
for checking a regeneration. Regenerating the Stage C bundles and the comparison is
``compare_historical.py --regenerate``.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/perturbation_cascade"
HISTORICAL = DOCS / "historical_v051"
STAGE_C = DOCS / "stage_c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ArchiveTests(unittest.TestCase):
    def test_archived_historical_files_match_the_originals(self):
        sums = (
            pd.read_csv(HISTORICAL / "ORIGINAL_SHA256SUMS.tsv", sep="\t")
            .set_index("file")
            .sha256
        )
        committed = [n for n in sums.index if (HISTORICAL / n).is_file()]
        for required in (
            "run_p4_withdrawal.py",
            "analyze_p4_withdrawal.py",
            "REPORT.md",
            "per_trajectory_events.tsv",
            "pairwise_precedence.tsv",
            "aggregate_final_state.tsv",
            "withdrawal_vs_control_delta.tsv",
            "aggregate_timecourse.tsv",
        ):
            self.assertIn(required, committed)
        for name in committed:
            with self.subTest(file=name):
                self.assertEqual(sha(HISTORICAL / name), sums[name])


class FigureRecordTests(unittest.TestCase):
    """No PNG is committed; each figure's hash is recorded so a regeneration can be checked."""

    def test_no_figure_is_committed_under_the_cascade_docs(self):
        self.assertEqual(sorted(DOCS.rglob("*.png")), [])

    def test_every_figure_has_a_recorded_hash(self):
        sums = (
            pd.read_csv(HISTORICAL / "ORIGINAL_SHA256SUMS.tsv", sep="\t")
            .set_index("file")
            .sha256
        )
        meta = json.loads(
            (STAGE_C / "cascade_progestin_withdrawal_v060.metadata.json").read_text()
        )
        summary = json.loads(
            (STAGE_C / "historical_comparison_summary.json").read_text()
        )
        for digest in (
            sums["fig3b_switch_positions_normalized.png"],
            meta["outputs"]["cascade.png"]["sha256"],
            summary["figure_sha256"]["historical_comparison.png"],
        ):
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_the_cascade_bundle_is_the_one_in_the_manifest(self):
        meta = json.loads(
            (STAGE_C / "cascade_progestin_withdrawal_v060.metadata.json").read_text()
        )
        manifest = json.loads((STAGE_C / "bundle_manifest.json").read_text())
        entry = manifest[meta["run_id"]]
        for name, digest in entry["tables"].items():
            with self.subTest(table=name):
                self.assertEqual(meta["outputs"][name]["sha256"], digest)


if __name__ == "__main__":
    unittest.main()
