"""The 2026-11-18 reconciliation, held to the canonical evidence table.

`docs/scientific_review_2026-11-18/curation_reconciliation.tsv` says what the
repository did with each of 74 reviewer assessments. It is prose-adjacent, but
its `canonical_evidence_piece_id` column is a claim about the evidence table and
can be wrong in ways nothing else notices.

The first version of it was: Dominguez 2010 contributes two independent
experiments to LE029 -- CD9 in Figure 5A-B and CD98 heavy chain in Figure
5C-D -- which the canonical table separates as `-01` and `-02`, and both
assessments were mapped onto `-01`. That misreports which experiment carries
which grade while every row still points at something real, so a mere
existence check would have passed it.

Hence the shape of these tests: existence, then *distinctness* of experiments,
then the independence rule that stops two experiments from one paper being
counted as two studies.
"""

from __future__ import annotations

import csv
import unittest

from dt_adoc.evidence import experimental as ex

RECONCILIATION = (
    ex.repo_root() / "docs/scientific_review_2026-11-18/curation_reconciliation.tsv"
)

#: Dispositions whose rows assert a specific canonical record.
ACCEPTING = {
    "already_present",
    "accepted_into_canonical_table",
    "proposed_new_citation_adjudicated_and_accepted",
}


def _rows() -> list[dict[str, str]]:
    with RECONCILIATION.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class TheReconciliationResolves(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = _rows()
        self.table = {r["evidence_piece_id"]: r for r in ex.load_table()}

    def test_it_covers_every_reviewer_assessment(self) -> None:
        self.assertEqual(len(self.rows), 74)
        self.assertEqual(len({r["review_id"] for r in self.rows}), 74)

    def test_it_is_current_with_the_audit_it_reconciles(self) -> None:
        """The reconciliation is hand-authored and has no in-repo generator,
        so nothing would otherwise notice it drifting from its source. This is
        the currency guard: exactly the audit's review ids, each against the
        same edge and reference the audit assessed.

        The audit archive is gitignored, so this skips rather than fails where
        it is absent -- a fresh clone cannot be expected to hold it.
        """
        source = (
            ex.repo_root()
            / "output/review_inbox/2026-11-18/extracted"
            / "all_rounds_provisional_evidence_assessments.tsv"
        )
        if not source.exists():
            self.skipTest(f"audit source not present: {source}")
        with source.open(newline="", encoding="utf-8") as handle:
            audit = {r["review_id"]: r for r in csv.DictReader(handle, delimiter="\t")}
        self.assertEqual(
            {r["review_id"] for r in self.rows},
            set(audit),
            "the reconciliation and the audit disagree about which assessments exist",
        )
        for row in self.rows:
            assessed = audit[row["review_id"]]
            with self.subTest(review=row["review_id"]):
                self.assertEqual(row["edge_id"], assessed["edge_id"])
                self.assertEqual(row["reference_id"], assessed["reference_id"])
                self.assertEqual(row["review_round"], assessed["review_round"])
                self.assertEqual(
                    row["reviewer_proposed_confidence"],
                    assessed["piece_confidence_proposed"],
                )

    def test_every_accepted_assessment_names_a_real_record(self) -> None:
        for row in self.rows:
            if row["reconciliation_action"] not in ACCEPTING:
                continue
            with self.subTest(review=row["review_id"]):
                piece = row["canonical_evidence_piece_id"]
                self.assertTrue(piece, "an accepted assessment must name a record")
                self.assertIn(piece, self.table)

    def test_an_accepted_record_belongs_to_the_assessed_edge_and_reference(
        self,
    ) -> None:
        """A record that exists but describes a different relation would still
        pass an existence check."""
        for row in self.rows:
            if row["reconciliation_action"] not in ACCEPTING:
                continue
            record = self.table[row["canonical_evidence_piece_id"]]
            with self.subTest(review=row["review_id"]):
                self.assertEqual(record["edge_id"], row["edge_id"])
                self.assertEqual(record["reference_id"], row["reference_id"])

    def test_a_held_back_assessment_names_no_record(self) -> None:
        """Holding an assessment back and still pointing it at a canonical row
        would read as if it had been accepted."""
        for row in self.rows:
            if row["reconciliation_action"] in ACCEPTING:
                continue
            with self.subTest(review=row["review_id"]):
                self.assertEqual(row["canonical_evidence_piece_id"], "")
                self.assertEqual(row["accepted_confidence"], "")

    def test_the_recorded_confidence_is_the_records_own(self) -> None:
        for row in self.rows:
            if row["reconciliation_action"] not in ACCEPTING:
                continue
            record = self.table[row["canonical_evidence_piece_id"]]
            with self.subTest(review=row["review_id"]):
                self.assertEqual(
                    row["accepted_confidence"], record["overall_confidence"]
                )


class DistinctExperimentsStayDistinct(unittest.TestCase):
    """The defect this file was written for."""

    def setUp(self) -> None:
        self.rows = _rows()
        self.table = {r["evidence_piece_id"]: r for r in ex.load_table()}

    def test_no_two_assessments_claim_the_same_record(self) -> None:
        seen: dict[str, str] = {}
        for row in self.rows:
            piece = row["canonical_evidence_piece_id"]
            if not piece:
                continue
            with self.subTest(review=row["review_id"]):
                self.assertNotIn(
                    piece,
                    seen,
                    f"{row['review_id']} and {seen.get(piece)} both claim {piece}",
                )
            seen[piece] = row["review_id"]

    def test_dominguez_cd9_and_cd98_map_to_their_own_records(self) -> None:
        """Named explicitly because it is the case that was wrong, and because
        the molecular target is what makes them different experiments."""
        mapping = {r["review_id"]: r for r in self.rows}
        self.assertEqual(
            mapping["R1-010"]["canonical_evidence_piece_id"],
            "EVP-LE029-REF008-01",
        )
        self.assertEqual(
            mapping["R1-011"]["canonical_evidence_piece_id"],
            "EVP-LE029-REF008-02",
        )
        self.assertEqual(
            self.table["EVP-LE029-REF008-01"]["perturbation_target"], "CD9"
        )
        self.assertEqual(
            self.table["EVP-LE029-REF008-02"]["perturbation_target"], "SLC3A2"
        )

    def test_a_multi_record_pair_is_never_mapped_by_position(self) -> None:
        """Where an (edge, reference) pair has several canonical records and
        several assessments, each assessment must resolve to a different one."""
        from collections import defaultdict

        by_pair = defaultdict(list)
        for row in self.rows:
            if row["canonical_evidence_piece_id"]:
                by_pair[(row["edge_id"], row["reference_id"])].append(row)
        for pair, group in by_pair.items():
            if len(group) < 2:
                continue
            with self.subTest(pair=pair):
                self.assertEqual(
                    len({r["canonical_evidence_piece_id"] for r in group}),
                    len(group),
                )

    def test_each_mapped_record_cites_the_figure_its_assessment_cites(self) -> None:
        """Identity is the experiment, not the row. If the record's own
        source_location names a figure, the assessment's must overlap it."""
        import re

        def panels(text: str) -> frozenset[str]:
            """Figure panels a location string names.

            ``Figure 5A-B``     -> {5a, 5b}   a range of panels
            ``Figures 4 and 6`` -> {4, 6}     a list of figures
            ``Figures 3-4``     -> {3, 4}     a range of figures
            ``Fig. 2 PDF p.5``  -> {2}        and not {2p}

            Three things this has to get right, each of which a simpler version got
            wrong. Panel letters must touch their number, or "PDF" donates a "P". A
            dash between bare numbers is a range of figures while a dash between
            letters is a range of panels. And a list has to be followed past its
            separators: "Figures 4 and 6" reduced to figure 4 alone made a record
            citing both look like a different experiment from an assessment citing
            only the second.
            """
            item = re.compile(
                r"(\d+)((?:[A-Za-z](?![A-Za-z]))(?:\s*[-–]\s*[A-Za-z](?![A-Za-z]))?)?"
            )
            separator = re.compile(r"\s*(?:,|&|and)\s*")
            span = re.compile(r"\s*(?:[-–]|to)\s*")
            found: set[str] = set()
            for keyword in re.finditer(
                r"Fig(?:ure)?s?\.?\s*(?=\d)", text, re.IGNORECASE
            ):
                cursor = keyword.end()
                while True:
                    step = item.match(text, cursor)
                    if step is None:
                        break
                    number, panels = step.group(1), step.group(2) or ""
                    letters = [c.lower() for c in re.findall(r"[A-Za-z]", panels)]
                    if len(letters) == 2:
                        first, last = sorted(letters)
                        letters = [chr(c) for c in range(ord(first), ord(last) + 1)]
                    if letters:
                        found.update(f"{number}{letter}" for letter in letters)
                    else:
                        found.add(number)
                    cursor = step.end()
                    if not letters:
                        ranged = span.match(text, cursor)
                        tail = (
                            re.match(r"\d+", text[ranged.end() :]) if ranged else None
                        )
                        if tail:
                            for n in range(int(number) + 1, int(tail.group()) + 1):
                                found.add(str(n))
                            cursor = ranged.end() + tail.end()
                            continue
                    joined = separator.match(text, cursor)
                    if joined and re.match(r"\d", text[joined.end() :]):
                        cursor = joined.end()
                        continue
                    break
            return frozenset(found)

        checked = 0
        for row in self.rows:
            piece = row["canonical_evidence_piece_id"]
            if not piece:
                continue
            wanted = panels(row["source_location"])
            have = panels(self.table[piece]["source_location"])
            if not wanted or not have:
                continue
            checked += 1
            with self.subTest(review=row["review_id"]):
                self.assertTrue(
                    wanted & have,
                    f"{row['review_id']} cites {sorted(wanted)} but {piece} "
                    f"records {sorted(have)}",
                )
        # Many locations cite page ranges rather than figures, so a skip is
        # legitimate -- but a silent one can degrade until the check covers
        # nothing. Pin the floor so that becomes a failure.
        self.assertGreaterEqual(checked, 20, "the panel check covered almost nothing")


class OnePublicationIsOneStudy(unittest.TestCase):
    """Several experiments from one paper are several rows and one study."""

    def setUp(self) -> None:
        self.table = ex.load_table()

    def test_the_validator_agrees(self) -> None:
        self.assertEqual(ex.independence_errors(self.table), [])

    def test_rows_sharing_a_reference_share_an_independence_group(self) -> None:
        from collections import defaultdict

        groups = defaultdict(set)
        for row in self.table:
            source = row["reference_id"] or row["source_observation_id"]
            if source and row["independence_group"]:
                groups[source].add(row["independence_group"])
        for source, found in groups.items():
            with self.subTest(source=source):
                self.assertEqual(len(found), 1)

    def test_dominguez_two_experiments_are_one_study(self) -> None:
        rows = [
            r
            for r in self.table
            if r["edge_id"] == "LE029" and r["reference_id"] == "REF-008"
        ]
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["independence_group"] for r in rows}, {"REF-008"})

    def test_an_edge_is_not_promoted_by_one_paper_twice_over(self) -> None:
        """The edge-level rule counts independent groups, so two rows from one
        paper must contribute one group, not two."""
        from dt_adoc.evidence.coverage import edge_evidence_summary

        for edge, confidence in edge_evidence_summary().items():
            if len(confidence.supporting_pieces) < 2:
                continue
            sources = {
                r["reference_id"] or r["source_observation_id"]
                for r in self.table
                if r["evidence_piece_id"] in confidence.supporting_pieces
            }
            with self.subTest(edge=edge):
                self.assertLessEqual(
                    confidence.independent_supporting_groups, len(sources)
                )


if __name__ == "__main__":
    unittest.main()
