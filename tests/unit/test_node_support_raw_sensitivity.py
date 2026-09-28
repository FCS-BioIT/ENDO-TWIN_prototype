"""Tests for the raw-layer sensitivity behind AC01.

The module answers one question -- does `E_PAEP` / `E_HBEGF` diverge on raw UMIs
as it does on the decontX-corrected layer -- and the dangerous failure is not a
wrong number but a **confident verdict computed from nothing**. The first run
matched zero cells because the barcode parse was wrong, and reported
`divergence_reproduced_on_raw: false`, which reads as the raw layer refuting the
audit's only load-bearing finding. Most of what follows guards that.
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.scrna import node_support as N
from dt_adoc.scrna import node_support_contract as C
from dt_adoc.scrna import node_support_raw_sensitivity as R

EPI = "Luminal-like epithelium"
ARTIFACT = ROOT / "docs/scrna/node_support_raw_sensitivity.json"


def write_cells(path: Path, rows: list[tuple[str, str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["cell", "sample_id", "celltype_v2"])
        writer.writerows(rows)


def write_reduced(path: Path, rows: list[tuple[str, int, int, int]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["barcode", *R.GENES, "total_umi"])
        writer.writerows(rows)


class BarcodeJoinTest(unittest.TestCase):
    """`sample_id` contains an underscore, so the barcode is a suffix."""

    def test_the_barcode_is_the_suffix_after_the_full_sample_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            cells = work / "cells.tsv"
            write_cells(
                cells,
                [
                    (f"{sample}_{barcode}", sample, EPI)
                    for sample in R.SAMPLES
                    for barcode in ("AAACCCAAGAGCAACC-1", "AAACCCAAGCCATTTG-1")
                ],
            )
            for sample in R.SAMPLES:
                write_reduced(
                    work / f"{sample}.reduced.tsv",
                    [
                        ("AAACCCAAGAGCAACC-1", 1, 0, 10_000),
                        ("AAACCCAAGCCATTTG-1", 2, 1, 10_000),
                    ],
                )
            built, join = R.build_cells(cells, work)
        # Splitting on the FIRST underscore gives "CNT_AAAC..." and matches
        # nothing; this is the regression that produced a verdict from no data.
        self.assertEqual(join["cells_joined"], 12)
        self.assertEqual(set(join["cells_in_object_not_in_matrix"].values()), {0})
        self.assertEqual(len(built.by_unit), 6)

    def test_a_cell_name_without_its_sample_prefix_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            cells = work / "cells.tsv"
            write_cells(cells, [("WRONG_AAACCCAAGAGCAACC-1", "SZ09TE_CNT", EPI)])
            with self.assertRaises(R.RawSensitivityError) as caught:
                R.build_cells(cells, work)
        self.assertIn("does not carry the prefix", str(caught.exception))


class EmptyJoinTest(unittest.TestCase):
    """A comparison of nothing must raise, never report `false`."""

    def _build(self, matching: bool):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            cells = work / "cells.tsv"
            write_cells(
                cells,
                [(f"{sample}_AAACCCAAGAGCAACC-1", sample, EPI) for sample in R.SAMPLES],
            )
            for sample in R.SAMPLES:
                barcode = "AAACCCAAGAGCAACC-1" if matching else "TTTTTTTTTTTTTTTT-1"
                write_reduced(work / f"{sample}.reduced.tsv", [(barcode, 1, 0, 10_000)])
            return R.build_cells(cells, work)

    def test_a_join_that_matches_nothing_raises(self) -> None:
        with self.assertRaises(R.RawSensitivityError) as caught:
            self._build(matching=False)
        self.assertIn(
            "refusing to report a comparison of nothing", str(caught.exception)
        )

    def test_a_join_that_matches_everything_proceeds(self) -> None:
        _, join = self._build(matching=True)
        self.assertEqual(join["cells_joined"], len(R.SAMPLES))


class ReducedTableBindingTest(unittest.TestCase):
    """A recorded digest is only worth what re-checking it costs.

    `gather_provenance` carries each sidecar's `reduced_sha256` into the shipped
    artifact, and `build_cells` reads the reduced tables. An earlier revision
    never compared the two, so an edited reduced table would have been consumed
    and then shipped under the digest of the file it replaced.
    """

    @staticmethod
    def _workspace(tmp: Path) -> Path:
        work = Path(tmp)
        cells = work / "cells.tsv"
        write_cells(
            cells,
            [(f"{sample}_AAACCCAAGAGCAACC-1", sample, EPI) for sample in R.SAMPLES],
        )
        extraction = {
            "cells_sha256": R._sha256_file(cells),
            "rds_sha256": N.source_digest(ROOT),
            "r_version": "R version 4.5.3 (2026-03-11)",
            "seuratobject_version": "5.4.0",
        }
        Path(str(cells) + R.CELLS_SIDECAR).write_text(json.dumps(extraction))
        for sample in R.SAMPLES:
            reduced = work / f"{sample}.reduced.tsv"
            write_reduced(reduced, [("AAACCCAAGAGCAACC-1", 3, 1, 10_000)])
            (work / f"{sample}.reduction.json").write_text(
                json.dumps(
                    {
                        "sample": sample,
                        "genes": list(R.GENES),
                        "matrix_bytes": 1,
                        "matrix_sha256": "0" * 64,
                        "reduced_sha256": R._sha256_file(reduced),
                    }
                )
            )
        return work

    def test_an_intact_workspace_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = self._workspace(Path(tmp))
            provenance = R.gather_provenance(work, work / "cells.tsv", root=ROOT)
        self.assertEqual(provenance["source_binding"], "verified")
        self.assertEqual(len(provenance["reductions"]), len(R.SAMPLES))

    def test_editing_a_reduced_table_after_its_sidecar_is_rejected(self) -> None:
        """The regression: the numbers would not be the ones provenance describes."""
        with tempfile.TemporaryDirectory() as tmp:
            work = self._workspace(Path(tmp))
            tampered = work / f"{R.SAMPLES[2]}.reduced.tsv"
            # A plausible edit: one cell's PAEP count raised, sidecar untouched.
            write_reduced(tampered, [("AAACCCAAGAGCAACC-1", 999, 1, 10_000)])
            with self.assertRaises(R.RawSensitivityError) as caught:
                R.gather_provenance(work, work / "cells.tsv", root=ROOT)
        message = str(caught.exception)
        self.assertIn("has changed since it was reduced", message)
        self.assertIn(R.SAMPLES[2], message)

    def test_a_missing_reduced_table_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = self._workspace(Path(tmp))
            (work / f"{R.SAMPLES[0]}.reduced.tsv").unlink()
            with self.assertRaises(R.RawSensitivityError) as caught:
                R.gather_provenance(work, work / "cells.tsv", root=ROOT)
        self.assertIn("is missing", str(caught.exception))

    def test_editing_the_cell_table_after_its_sidecar_is_rejected(self) -> None:
        """The binding that already existed, pinned alongside the new one."""
        with tempfile.TemporaryDirectory() as tmp:
            work = self._workspace(Path(tmp))
            cells = work / "cells.tsv"
            write_cells(cells, [("SZ09TE_CNT_AAACCCAAGAGCAACC-1", "SZ09TE_CNT", EPI)])
            with self.assertRaises(R.RawSensitivityError) as caught:
                R.gather_provenance(work, cells, root=ROOT)
        self.assertIn("has changed since extraction", str(caught.exception))


class VerdictTest(unittest.TestCase):
    def test_an_uninformative_donor_blocks_a_reproduction_verdict(self) -> None:
        """`false` means measured-and-different, never not-measured."""
        comparison = {
            "PAEP": {
                "per_donor": dict.fromkeys(C.DONORS, "uninformative"),
                "detail": {},
            },
            "HBEGF": {
                "per_donor": dict.fromkeys(C.DONORS, "uninformative"),
                "detail": {},
            },
        }
        verdict = R.verdict(comparison)
        self.assertIsNone(verdict["divergence_reproduced_on_raw"])
        self.assertEqual(verdict["status"], "not_evaluated")

    def test_reproduction_requires_both_patterns_in_all_three_donors(self) -> None:
        good = {
            "PAEP": {"per_donor": dict.fromkeys(C.DONORS, "moves_up"), "detail": {}},
            "HBEGF": {
                "per_donor": dict.fromkeys(C.DONORS, "no_material_move"),
                "detail": {},
            },
        }
        self.assertTrue(R.verdict(good)["divergence_reproduced_on_raw"])
        weaker = {
            "PAEP": {
                "per_donor": {
                    "SZ09": "moves_up",
                    "SZ10": "moves_up",
                    "SZ25": "no_material_move",
                },
                "detail": {},
            },
            "HBEGF": {
                "per_donor": dict.fromkeys(C.DONORS, "no_material_move"),
                "detail": {},
            },
        }
        self.assertFalse(R.verdict(weaker)["divergence_reproduced_on_raw"])


class FrozenRuleTest(unittest.TestCase):
    """The sensitivity must use the audit's rule, not a rule of its own."""

    def test_only_the_two_load_bearing_genes_are_read(self) -> None:
        self.assertEqual(R.GENES, ("PAEP", "HBEGF"))

    def test_no_threshold_is_defined_in_this_module(self) -> None:
        """Every constant comes from the frozen contract."""
        source = (SRC / "dt_adoc/scrna/node_support_raw_sensitivity.py").read_text()
        for constant in (
            "LOG2_FOLD_MIN",
            "BOOTSTRAP_B",
            "BOOTSTRAP_SEED",
            "BOOTSTRAP_ALPHA",
        ):
            self.assertNotIn(f"{constant} =", source)
            self.assertIn(f"C.{constant}", source)

    def test_it_calls_the_audits_own_movement_function(self) -> None:
        source = (SRC / "dt_adoc/scrna/node_support_raw_sensitivity.py").read_text()
        self.assertIn("N.gene_movement", source)
        self.assertIn("N.unit_statistics", source)


class ShippedArtifactTest(unittest.TestCase):
    def setUp(self) -> None:
        if not ARTIFACT.is_file():
            self.skipTest("the raw sensitivity has not been run in this checkout")
        self.payload = json.loads(ARTIFACT.read_text())

    def test_the_join_is_complete(self) -> None:
        join = self.payload["join"]
        self.assertEqual(join["cells_joined"], 20_441)
        self.assertEqual(set(join["cells_in_object_not_in_matrix"].values()), {0})

    def test_the_rule_recorded_is_the_frozen_one(self) -> None:
        rule = self.payload["rule"]
        self.assertEqual(rule["log2_fold_min"], C.LOG2_FOLD_MIN)
        self.assertEqual(rule["bootstrap_b"], C.BOOTSTRAP_B)
        self.assertEqual(rule["bootstrap_seed"], C.BOOTSTRAP_SEED)

    def test_the_divergence_reproduces_on_raw_umis(self) -> None:
        verdict = self.payload["verdict"]
        self.assertTrue(verdict["divergence_reproduced_on_raw"])
        self.assertEqual(verdict["paep_moves_up_donors"], 3)
        self.assertEqual(verdict["hbegf_no_material_move_donors"], 3)

    def test_the_artifact_is_strict_json(self) -> None:
        text = ARTIFACT.read_text()
        for token in ("NaN", "Infinity", "-Infinity"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
