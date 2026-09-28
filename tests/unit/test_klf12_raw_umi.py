"""The raw-UMI sensitivity must be a sensitivity, not a second primary analysis.

The pre-registration allows exactly one fallback layer and binds it with the
same constraints as the primary: the same pre-declared epithelial population,
donor x condition as the unit, no re-clustering, no condition-dependent
population, no model output reaching any choice. The specific risks here are
that the fallback quietly becomes the headline, that it inherits a provenance
it does not have, or that a count model is declared to find a state when what
it has found is the detection boundary.

Every fit in this file is checked on data the test constructs, so a fit that
starts agreeing with itself rather than with arithmetic fails here.
"""

from __future__ import annotations

import json
import random
import sys
import unittest
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.scrna import klf12_raw_umi, klf12_state

FINDINGS = ROOT / "docs" / "scrna" / "klf12_raw_umi_findings.json"
EVIDENCE = ROOT / "docs" / "scrna" / "klf12_raw_umi_evidence.tsv"


def _findings() -> dict:
    return json.loads(FINDINGS.read_text(encoding="utf-8"))


class TheSensitivityCannotSeeAnOutcome(unittest.TestCase):
    """Leakage control 1, enforced on the source as it is for the primary."""

    FORBIDDEN = (
        "dt_adoc.simulation",
        "dt_adoc.concordance",
        "dt_adoc.calibration",
        "dt_adoc.scoring",
        "dt_adoc.perturbations",
        "docs/concordance",
        "OUT_STABLE_ADHESION",
    )

    def test_the_module_imports_and_reads_no_model_output(self) -> None:
        source = Path(klf12_raw_umi.__file__).read_text(encoding="utf-8")
        body = source.split('"""', 2)[-1]
        for token in self.FORBIDDEN:
            with self.subTest(token=token):
                self.assertNotIn(token, body)

    def test_the_population_is_the_primary_analysis_definition_itself(self) -> None:
        """Re-imported, not restated: two copies could drift apart."""
        self.assertIs(klf12_raw_umi.EPITHELIAL_LABELS, klf12_state.EPITHELIAL_LABELS)
        self.assertEqual(
            _findings()["population_definition"], list(klf12_state.EPITHELIAL_LABELS)
        )


class TheReductionIsArithmeticNotTrust(unittest.TestCase):
    """The 2.4 GB of matrices are streamed once and discarded, so the reducer
    itself is the only thing standing between the accession and the result."""

    MATRIX: ClassVar[list[str]] = [
        "%%MatrixMarket matrix coordinate integer general",
        "%",
        "5 3 6",
        "2 1 7",
        "4 1 1",
        "2 2 3",
        "5 2 2",
        "1 3 4",
        "4 3 9",
    ]

    def test_one_row_and_the_column_totals_come_back(self) -> None:
        reduced = klf12_raw_umi.reduce_matrix(self.MATRIX, row=4, columns=3)
        self.assertEqual(reduced, [(1, 8, 2), (0, 5, 2), (9, 13, 2)])

    def test_a_column_the_stream_never_mentions_is_a_zero_not_a_gap(self) -> None:
        """An empty column must be an explicit zero: dropping it would shift
        every later barcode's index and silently mislabel every cell."""
        reduced = klf12_raw_umi.reduce_matrix(
            [
                "%%MatrixMarket matrix coordinate integer general",
                "3 4 1",
                "2 2 5",
            ],
            row=2,
            columns=4,
        )
        self.assertEqual(len(reduced), 4)
        self.assertEqual(reduced[0], (0, 0, 0))
        self.assertEqual(reduced[1], (5, 5, 1))

    def test_a_barcode_count_mismatch_is_refused(self) -> None:
        with self.assertRaises(klf12_state.Klf12StateError):
            klf12_raw_umi.reduce_matrix(self.MATRIX, row=4, columns=99)


class NoLatentStateModelIsFittedHere(unittest.TestCase):
    """The removal is an invariant, not an absence that could drift back.

    An earlier revision fitted a two-component gamma-Poisson mixture to the raw
    counts and compared it against a single-rate model by BIC. Three successive
    fitters were each shown to return a non-maximum -- the reported gain moved
    +17.0, +10.24, +21.52 as the search was hardened -- on a likelihood surface
    that is multimodal by construction. The statistic was removed because a
    model-selection number that tracks how hard one looked is not evidence, and
    because nothing in the conclusion rested on it.

    These tests exist so that the module cannot quietly regrow the dependency:
    the fitters must stay gone, and the committed artifact must not carry a BIC
    field that a reader could mistake for support.
    """

    REMOVED: ClassVar[tuple[str, ...]] = (
        "fit_negative_binomial",
        "fit_two_component_negative_binomial",
        "fit_nb_mean_and_size",
        "weighted_nb_loglik",
        "nb_logpmf",
        "posterior_boundary_count",
        "boundary_by_depth",
        "calibrate_two_state_specificity",
    )

    def test_the_mixture_fitters_are_gone(self) -> None:
        for name in self.REMOVED:
            with self.subTest(name=name):
                self.assertFalse(
                    hasattr(klf12_raw_umi, name),
                    f"{name} is back; the BIC analysis was removed because its "
                    "optimiser could not be shown to reach a maximum",
                )

    def test_the_artifact_carries_no_model_selection_claim(self) -> None:
        findings = _findings()
        blob = json.dumps(findings)
        for token in ("bic_gain", "bic_single", "bic_two_component", "log_likelihood"):
            with self.subTest(token=token):
                self.assertNotIn(token, blob)
        self.assertIn("NONE FITTED", str(findings["latent_state_model"]))

    def test_the_removal_is_explained_where_a_reader_will_look(self) -> None:
        """A removed analysis leaves no trace unless the record keeps one."""
        note = str(_findings()["latent_state_model"])
        self.assertIn("multimodal", note)
        self.assertIn("never load-bearing", note)


class DepthMatchingIsCountingNotFitting(unittest.TestCase):
    """What survived the removal: thinning, and the counts it produces."""

    def test_downsampling_reports_the_depths_it_actually_achieved(self) -> None:
        """A cell that could not be thinned must not be reported as if it were.

        Thinning leaves a cell already at or below the target untouched. An
        earlier revision then treated every cell as sitting at the target,
        misstating the depth of 41% of the epithelial cells in the one
        comparison whose purpose was to hold depth constant.
        """
        rng = random.Random(3)
        counts = [10, 4, 0, 7]
        depths = [1000.0, 1000.0, 1000.0, 100.0]
        thinned, effective, unmatched = klf12_raw_umi.downsample(
            counts, depths, 500.0, rng
        )
        for before, after in zip(counts, thinned):
            self.assertLessEqual(after, before)
        self.assertEqual(thinned[3], 7, "a cell already at target is left alone")
        self.assertEqual(unmatched, 1)
        self.assertEqual(
            effective,
            [500.0, 500.0, 500.0, 100.0],
            "the shallow cell must keep its own depth, not the target",
        )

    def test_thinning_never_invents_a_molecule(self) -> None:
        rng = random.Random(9)
        counts = [5, 0, 12, 3]
        depths = [4000.0, 4000.0, 4000.0, 4000.0]
        thinned, effective, unmatched = klf12_raw_umi.downsample(
            counts, depths, 1000.0, rng
        )
        self.assertEqual(unmatched, 0)
        self.assertTrue(all(d == 1000.0 for d in effective))
        self.assertTrue(all(a <= b for a, b in zip(thinned, counts)))
        self.assertEqual(thinned[1], 0, "a zero cannot be thinned into a count")


class TheCrossLayerClaimIsComputedNotAsserted(unittest.TestCase):
    """The one claim in the report that spans both layers, pinned on fixtures.

    The report states that a decontX value strictly between 0 and 1 is a cell
    that captured a molecule -- correcting an earlier revision which called
    those values residue of cells that captured none. That is a cross-layer
    claim, so it needs a cross-layer computation with a test, not a number
    quoted from a one-off check.
    """

    def _cell(self, klf12: int, corrected: float | None) -> object:
        return klf12_raw_umi.RawCell(
            sample_id="SZ09TE_CNT",
            celltype_v2="Cycling epithelium",
            barcode=f"BC{klf12}-{corrected}",
            klf12=klf12,
            depth=10_000,
            nfeature=2_000,
            corrected=corrected,
        )

    def test_the_cross_tab_counts_what_it_says_it_counts(self) -> None:
        cells = [
            self._cell(0, 0.0),  # agreed zero
            self._cell(0, 0.0),
            self._cell(1, 0.9),  # sub-one, one molecule
            self._cell(1, 0.4),  # sub-one, one molecule
            self._cell(2, 0.8),  # sub-one, TWO molecules
            self._cell(3, 2.7),  # not sub-one
            self._cell(7, 6.1),  # not sub-one
        ]
        table = klf12_raw_umi.cross_layer_table(cells)
        self.assertTrue(table["available"])
        self.assertEqual(table["n_cells"], 7)
        self.assertEqual(
            table["detection_agreement"],
            {
                "both_zero": 2,
                "both_positive": 5,
                "corrected_positive_raw_zero": 0,
                "raw_positive_corrected_zero": 0,
            },
        )
        self.assertEqual(table["sub_one_corrected_cells"], 3)
        self.assertEqual(table["sub_one_corrected_by_raw_umi"], {"1": 2, "2": 1})
        self.assertEqual(table["sub_one_corrected_cells_with_zero_raw_umi"], 0)

    def test_a_disagreeing_layer_is_reported_not_hidden(self) -> None:
        """If decontX ever did zero a detection, the table must say so.

        The report leans on the two layers agreeing exactly on detection. A
        cross-tab that could not express disagreement would make that agreement
        unfalsifiable, so the disagreeing cells are counted explicitly.
        """
        cells = [self._cell(0, 0.5), self._cell(4, 0.0), self._cell(1, 0.9)]
        table = klf12_raw_umi.cross_layer_table(cells)
        self.assertEqual(table["detection_agreement"]["corrected_positive_raw_zero"], 1)
        self.assertEqual(table["detection_agreement"]["raw_positive_corrected_zero"], 1)
        self.assertFalse(table["decontx_never_creates_or_destroys_a_detection"])

    def test_a_table_without_corrected_values_is_declared_unavailable(self) -> None:
        """Absence is reported, never silently counted as zero."""
        table = klf12_raw_umi.cross_layer_table(
            [self._cell(1, None), self._cell(0, None)]
        )
        self.assertFalse(table["available"])
        self.assertIn("no corrected value", str(table["reason"]))

    def test_the_corrected_column_is_parsed_from_the_per_cell_table(self) -> None:
        """`read_cells` must carry the corrected value, or the table is empty."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            path.write_text(
                "cell\tsample_id\tcelltype_v2\tcounts_KLF12\n"
                "SZ09TE_CNT_AAAC-1\tSZ09TE_CNT\tCycling epithelium\t0.917\n"
                "SZ09TE_CNT_AAAG-1\tSZ09TE_CNT\tStroma\t0\n",
                encoding="utf-8",
            )
            cells = klf12_raw_umi.read_cells(path)
            self.assertAlmostEqual(cells["SZ09TE_CNT_AAAC-1"][2], 0.917)
            self.assertEqual(cells["SZ09TE_CNT_AAAG-1"][2], 0.0)

        # A table without the column still loads; the value is simply unknown.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            path.write_text(
                "cell\tsample_id\tcelltype_v2\n"
                "SZ09TE_CNT_AAAC-1\tSZ09TE_CNT\tCycling epithelium\n",
                encoding="utf-8",
            )
            self.assertIsNone(klf12_raw_umi.read_cells(path)["SZ09TE_CNT_AAAC-1"][2])


class TheProvenancePathIsExercisedNotJustDeclared(unittest.TestCase):
    """The streamed reduction and the two-parent binding, run on fixtures.

    These two functions are what stand between the accession's bytes and every
    number in the committed artifact, and an earlier revision shipped them with
    no test at all -- the suite passed while asserting the *previous* artifact
    schema, so neither the source hashing nor the binding refusals were ever
    executed. A provenance guarantee that is never run is a comment.

    `reduce_sample` is driven over `file://`, so the streaming, the digesting
    and the sidecar are the real code paths on a matrix the test owns.
    """

    MATRIX: ClassVar[list[str]] = [
        "%%MatrixMarket matrix coordinate integer general",
        "4 3 5",
        "2 1 7",
        "3 1 1",
        "2 2 4",
        "1 3 2",
        "3 3 9",
    ]
    BARCODES: ClassVar[list[str]] = ["AAAC-1", "AAAG-1", "AAAT-1"]
    FEATURES: ClassVar[list[str]] = ["GENE_A", "GENE_B", "KLF12", "GENE_D"]

    def _accession(self, root: Path) -> str:
        """A miniature accession: every sample the module expects, on disk."""
        (root / "all_feature_bc_matrix_features.tsv").write_text(
            "\n".join(self.FEATURES) + "\n", encoding="utf-8"
        )
        for sample in klf12_raw_umi.SAMPLES:
            (root / f"{sample}_filtered_feature_bc_matrix_barcodes.tsv").write_text(
                "\n".join(self.BARCODES) + "\n", encoding="utf-8"
            )
            (root / f"{sample}_filtered_feature_bc_matrix_matrix.mtx").write_text(
                "\n".join(self.MATRIX) + "\n", encoding="utf-8"
            )
        return root.as_uri()

    def test_the_reduction_digests_the_bytes_it_actually_streamed(self) -> None:
        import hashlib
        import tempfile

        sample = klf12_raw_umi.SAMPLES[0]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "accession"
            source.mkdir()
            out = Path(tmp) / "reduced"
            record = klf12_raw_umi.reduce_sample(
                sample, out, base_url=self._accession(source)
            )

            matrix = source / f"{sample}_filtered_feature_bc_matrix_matrix.mtx"
            self.assertEqual(
                record["matrix_sha256"],
                hashlib.sha256(matrix.read_bytes()).hexdigest(),
                "the recorded digest is not of the bytes that were read",
            )
            self.assertEqual(record["matrix_bytes"], matrix.stat().st_size)
            # KLF12 is row 3 of the fixture, so the reduction must find it there
            # rather than at whatever index the real accession happens to use.
            self.assertEqual(record["feature_row_one_based"], 3)

            rows = [
                line.split("\t")
                for line in (out / f"{sample}.klf12.tsv")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            # column 1: KLF12=1, total 8, 2 genes; column 2: KLF12=0, total 4,
            # 1 gene; column 3: KLF12=9, total 11, 2 genes.
            self.assertEqual([r[1] for r in rows], ["1", "0", "9"])
            self.assertEqual([r[2] for r in rows], ["8", "4", "11"])

    def test_a_tampered_reduction_is_refused(self) -> None:
        """The sidecar binds the reduced table; editing it must not pass."""
        import tempfile

        sample = klf12_raw_umi.SAMPLES[0]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "accession"
            source.mkdir()
            out = Path(tmp) / "reduced"
            klf12_raw_umi.reduce_sample(sample, out, base_url=self._accession(source))
            target = out / f"{sample}.klf12.tsv"
            target.write_text(
                target.read_text(encoding="utf-8").replace("\t9\t", "\t99\t"),
                encoding="utf-8",
            )
            with self.assertRaises(klf12_state.Klf12StateError) as raised:
                klf12_raw_umi.reduction_provenance(
                    out, Path(tmp) / "cells.tsv", root=ROOT
                )
            self.assertIn("changed since it was reduced", str(raised.exception))

    def test_a_missing_sidecar_is_refused_rather_than_assumed(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "reduced"
            empty.mkdir()
            with self.assertRaises(klf12_state.Klf12StateError) as raised:
                klf12_raw_umi.reduction_provenance(
                    empty, Path(tmp) / "cells.tsv", root=ROOT
                )
            self.assertIn("not bound to the accession file", str(raised.exception))

    def test_an_unbound_annotation_parent_is_refused(self) -> None:
        """The population half of the input must be bound too.

        A per-cell table with no extraction sidecar could have come from
        anywhere, and the epithelial population it defines decides which cells
        every number in the artifact is computed over.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "accession"
            source.mkdir()
            out = Path(tmp) / "reduced"
            base = self._accession(source)
            # Every count sidecar present, so the refusal below can only be the
            # ANNOTATION binding and not a missing reduction.
            for name in klf12_raw_umi.SAMPLES:
                klf12_raw_umi.reduce_sample(name, out, base_url=base)
            cells = Path(tmp) / "cells.tsv"
            cells.write_text("cell\tsample_id\tcelltype_v2\n", encoding="utf-8")
            with self.assertRaises(klf12_state.Klf12StateError) as raised:
                klf12_raw_umi.reduction_provenance(out, cells, root=ROOT)
            self.assertIn("not bound to", str(raised.exception))


class TheRawResultIsAFallbackNotTheHeadline(unittest.TestCase):
    """What the committed artifact is allowed to claim."""

    def test_the_layer_and_claim_level_say_what_this_is(self) -> None:
        findings = _findings()
        self.assertEqual(findings["layer"], "raw_filtered_feature_bc_matrix")
        self.assertEqual(
            findings["provenance"]["claim_level"],
            "sensitivity_not_primary_not_validation",
        )
        self.assertEqual(
            findings["provenance"]["evidence_role"], "same_dataset_internal"
        )

    def test_the_count_parent_is_not_bound_by_the_rds_digest(self) -> None:
        """Two parents, two bindings, and neither may stand in for the other.

        The raw counts come from six per-sample matrices; the epithelial
        population, donor and condition come from the deposited RDS. An earlier
        revision recorded only the first and identified its files by a
        wildcard, which left the half of the input that decides WHICH cells are
        analysed entirely unbound. The RDS digest is now recorded -- but under
        `annotation_parent`, where it belongs, and it must not appear as the
        binding for the counts.
        """
        provenance = _findings()["provenance"]
        rds = klf12_state.source_digest(ROOT)
        self.assertEqual(provenance["annotation_parent"]["rds_sha256"], rds)
        self.assertEqual(provenance["annotation_parent"]["source_binding"], "verified")
        self.assertNotIn(
            rds,
            json.dumps(provenance["count_parent"]),
            "the RDS digest must not be presented as the counts' provenance",
        )

    def test_every_source_matrix_is_named_with_its_own_digest(self) -> None:
        """No wildcards: the exact bytes each number was computed from."""
        per_sample = _findings()["provenance"]["count_parent"]["per_sample"]
        self.assertEqual(set(per_sample), set(klf12_raw_umi.SAMPLES))
        for sample, record in per_sample.items():
            with self.subTest(sample=sample):
                self.assertTrue(
                    record["matrix_file"].startswith(sample)
                    and record["matrix_file"].endswith(".mtx")
                )
                self.assertEqual(len(record["matrix_sha256"]), 64)
                self.assertEqual(len(record["barcodes_sha256"]), 64)
                self.assertGreater(int(record["matrix_bytes"]), 10_000_000)
                self.assertEqual(record["gene"], klf12_raw_umi.GENE)
                self.assertGreater(int(record["feature_row_one_based"]), 0)

    def test_the_join_covered_every_cell_of_the_object(self) -> None:
        """A partial join would drop exactly the cells that differ."""
        findings = _findings()
        self.assertEqual(findings["n_cells_joined"], 28212)
        self.assertEqual(findings["n_cells_epithelial"], 20441)

    def test_the_raw_layer_agrees_with_the_corrected_one_on_detection(self) -> None:
        """decontX neither zeroes a detected gene nor creates one, so the two
        layers must report the SAME zero fraction. If they ever stop doing so,
        the raw analysis is not describing the same cells."""
        raw = _findings()["zero_fraction"]
        corrected = json.loads(
            (ROOT / "docs" / "scrna" / "klf12_state_findings.json").read_text(
                encoding="utf-8"
            )
        )["zero_fraction"]
        self.assertAlmostEqual(raw, corrected, places=12)

    def test_the_measurement_is_dominated_by_single_molecules(self) -> None:
        """The finding that survives every model choice."""
        findings = _findings()
        self.assertGreater(float(findings["share_of_detected_at_one_umi"]), 0.5)
        self.assertGreater(
            float(findings["share_of_detected_at_or_below_two_umi"]), 0.8
        )

    def test_the_between_unit_spread_is_reported_before_and_after_depth(
        self,
    ) -> None:
        """The depth argument, made by counting rather than by fitting.

        The crude per-unit detection fractions span a ten-fold range, and the
        deepest-sequenced unit has the highest. Thinning every cell to a common
        depth and recounting is the model-free way to ask how much of that
        spread is library size. Both spreads are committed so a reader can see
        the comparison rather than take it on trust.
        """
        findings = _findings()
        crude = findings["detection_fraction_crude_by_unit"]
        matched = findings["detection_fraction_depth_matched_by_unit"]
        self.assertEqual(set(crude), set(klf12_raw_umi.SAMPLES))
        self.assertEqual(set(matched), set(klf12_raw_umi.SAMPLES))
        self.assertIsNotNone(findings["detection_fraction_spread_crude"])
        self.assertIsNotNone(findings["detection_fraction_spread_depth_matched"])
        for unit, value in matched.items():
            with self.subTest(unit=unit):
                self.assertIsNotNone(value)
                self.assertLessEqual(
                    float(value),
                    float(crude[unit]) + 1e-9,
                    "thinning cannot raise a detection fraction",
                )

    def test_the_per_unit_table_uses_the_matched_only_scheme(self) -> None:
        """Pins the scheme, because both schemes satisfy the weaker assertions.

        An earlier revision built the per-unit breakdown from the scheme that
        keeps every cell, including those already below the target. That
        remainder is wildly uneven between units -- 50.0% of `SZ25TE_CNT`
        against 4.1% of `SZ25TE_HT`, because the target IS `SZ25TE_CNT`'s
        median depth -- so it thinned the deep unit almost completely and
        barely touched the shallow one, which is the opposite of holding depth
        constant. Key-set, non-null and "<= crude" are all true of that broken
        scheme too, so this asserts the scheme itself.
        """
        findings = _findings()
        self.assertEqual(
            findings["depth_matched_scheme_for_per_unit"], "matched_cells_only"
        )
        matched_cells = findings["depth_matched_cells_per_unit"]
        unmatched_share = findings["depth_matched_unmatched_share_per_unit"]
        self.assertEqual(set(matched_cells), set(klf12_raw_umi.SAMPLES))
        self.assertEqual(set(unmatched_share), set(klf12_raw_umi.SAMPLES))

        # The per-unit matched counts must account for exactly the cells the
        # artifact says sit above the target, unit by unit and in total.
        total_below = int(findings["depth_matched_cells_below_target"])
        total_matched = sum(int(v) for v in matched_cells.values())
        self.assertEqual(
            total_matched + total_below, int(findings["n_cells_epithelial"])
        )
        for unit, share in unmatched_share.items():
            with self.subTest(unit=unit):
                self.assertGreaterEqual(float(share), 0.0)
                self.assertLess(float(share), 1.0)
                self.assertGreater(int(matched_cells[unit]), 0)

        # The asymmetry that made the old scheme wrong must stay visible.
        self.assertGreater(
            float(unmatched_share["SZ25TE_CNT"]),
            float(unmatched_share["SZ25TE_HT"]) * 5,
            "the uneven unmatched share is the reason the scheme matters and "
            "must remain reported",
        )

    def test_the_minimum_corrected_cell_is_committed(self) -> None:
        """§1's support-floor claim spans both layers, so it is computed."""
        cell = _findings()["cross_layer_corrected_vs_raw"]["minimum_corrected_cell"]
        self.assertIsNotNone(cell)
        self.assertGreater(int(cell["raw_umi"]), 0)
        self.assertGreater(int(cell["raw_depth"]), 0)
        self.assertLess(float(cell["corrected_value"]), 1e-9)

    def test_the_thinning_target_and_its_unmatched_cells_are_recorded(self) -> None:
        """A depth match that leaves cells unmatched must say how many."""
        findings = _findings()
        self.assertGreater(float(findings["depth_matched_target_umi"]), 0)
        self.assertGreater(int(findings["depth_matched_cells_below_target"]), 0)
        schemes = {row["scheme"] for row in findings["depth_matched_replicates"]}
        self.assertEqual(
            schemes,
            {"all_cells_at_their_effective_depth", "matched_cells_only"},
        )
        for row in findings["depth_matched_replicates"]:
            with self.subTest(scheme=row["scheme"]):
                self.assertIn("cells_left_unmatched", row)
                self.assertNotIn("bic_gain", row)


if __name__ == "__main__":
    unittest.main()
