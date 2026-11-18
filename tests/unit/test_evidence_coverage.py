"""Per-edge literature coverage, and the staleness class that produced it.

The 2026-11-18 audit found 47 coverage rows still calling recovered
publications abstract-only. The interesting tests here are not that the
arithmetic is right -- it was right before too -- but that the shape of
mistake which made those rows possible is now impossible to repeat silently.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from dt_adoc.evidence.coverage import (
    AVAILABILITY_VALUES,
    CoverageError,
    availability_from_inventory,
    build_coverage,
    fingerprint_availability,
    stale_rows,
)

MODEL = "adoc-literature-superset-v0.6.0"


class AStaleAvailabilitySnapshot(unittest.TestCase):
    """The defect the audit found, reproduced and then caught."""

    def test_a_report_built_on_an_old_snapshot_is_detected_against_a_new_one(
        self,
    ) -> None:
        """This is PKG-01 exactly: build with everything abstract-only, then
        check against a snapshot in which the papers were recovered."""
        old = {f"REF-{n:03d}": "abstract_only" for n in (2, 27, 29)}
        report = build_coverage({**_all_unknown(), **old}, model_version=MODEL)
        recovered = {ref: "complete" for ref in old}
        found = stale_rows(report, {**_all_unknown(), **recovered})
        self.assertTrue(found, "a stale report must be reported as stale")
        self.assertTrue(any("REF-002" in line for line in found))

    def test_a_report_is_not_stale_against_the_snapshot_that_built_it(self) -> None:
        snapshot = {**_all_unknown(), "REF-002": "complete"}
        report = build_coverage(snapshot, model_version=MODEL)
        self.assertEqual(stale_rows(report, snapshot), [])

    def test_the_snapshot_used_is_recorded_in_the_report(self) -> None:
        """Without this, a row and the availability behind it cannot be paired
        after the fact, which is how the old table drifted unnoticed."""
        a = {**_all_unknown(), "REF-002": "complete"}
        b = {**_all_unknown(), "REF-002": "abstract_only"}
        self.assertNotEqual(
            build_coverage(a, model_version=MODEL).availability_sha256,
            build_coverage(b, model_version=MODEL).availability_sha256,
        )

    def test_availability_has_no_default(self) -> None:
        """It is a required argument. A generator that could fall back to a
        file on disk is one that can silently reuse the wrong one."""
        with self.assertRaises(TypeError):
            build_coverage()  # type: ignore[call-arg]

    def test_fingerprint_ignores_ordering_but_not_content(self) -> None:
        self.assertEqual(
            fingerprint_availability({"A": "complete", "B": "unknown"}),
            fingerprint_availability({"B": "unknown", "A": "complete"}),
        )
        self.assertNotEqual(
            fingerprint_availability({"A": "complete"}),
            fingerprint_availability({"A": "unavailable"}),
        )


class SilenceIsNotAbsence(unittest.TestCase):
    """A reference the snapshot does not mention is unknown, not missing."""

    def test_an_unmentioned_reference_is_unknown_not_abstract_only(self) -> None:
        report = build_coverage({}, model_version=MODEL)
        for row in report.rows:
            with self.subTest(edge=row["edge_id"]):
                self.assertEqual(row["references_abstract_only"], "")
        cited = [r for r in report.rows if r["references_cited"]]
        self.assertTrue(cited)
        self.assertTrue(
            all(r["references_unknown_availability"] for r in cited),
            "cited references with no availability stated must read unknown",
        )

    def test_an_all_unknown_edge_is_not_labelled_none_available(self) -> None:
        report = build_coverage({}, model_version=MODEL)
        labels = {r["coverage"] for r in report.rows if r["references_cited"]}
        self.assertNotIn("none_available", labels)
        self.assertIn("availability_unknown", labels)

    def test_an_unrecognised_availability_value_is_refused(self) -> None:
        with self.assertRaises(CoverageError):
            build_coverage({"REF-002": "probably_fine"}, model_version=MODEL)

    def test_an_inventory_state_outside_the_vocabulary_becomes_unknown(
        self,
    ) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inventory.tsv"
            path.write_text(
                "reference_id\tavailability\nREF-002\tsomething_else\n"
                "REF-003\tcomplete\n",
                encoding="utf-8",
            )
            mapping = availability_from_inventory(path)
        self.assertEqual(mapping["REF-002"], "unknown")
        self.assertEqual(mapping["REF-003"], "complete")


class TheCoverageTableItself(unittest.TestCase):
    def setUp(self) -> None:
        self.report = build_coverage(_all_unknown(), model_version=MODEL)

    def test_every_edge_of_the_model_has_a_row(self) -> None:
        from dt_adoc.evidence import experimental as ex

        self.assertEqual(
            {r["edge_id"] for r in self.report.rows},
            set(ex.edge_context(MODEL)),
        )

    def test_rows_are_in_natural_edge_order(self) -> None:
        from dt_adoc.evidence import experimental as ex

        ids = [r["edge_id"] for r in self.report.rows]
        self.assertEqual(ids, sorted(ids, key=ex._natural_edge_key))

    def test_graded_record_counts_match_the_canonical_table(self) -> None:
        from dt_adoc.evidence import experimental as ex

        table = ex.read_tsv(ex.repo_root() / ex.EVIDENCE_TABLE_PATH)
        expected = sum(1 for r in table if r["curation_status"] != "unreviewed")
        counted = sum(int(r["records_graded"]) for r in self.report.rows)
        self.assertEqual(counted, expected)

    def test_availability_vocabulary_is_closed(self) -> None:
        self.assertEqual(
            AVAILABILITY_VALUES,
            ("complete", "abstract_only", "unavailable", "unknown"),
        )


def _all_unknown() -> dict[str, str]:
    from dt_adoc.evidence import experimental as ex

    return {
        row["ref_id"]: "unknown"
        for row in ex.read_tsv(ex.repo_root() / ex.REFERENCES_PATH)
    }


if __name__ == "__main__":
    unittest.main()
