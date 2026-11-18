"""Citation-integrity tests for the DT_ADOC bibliography.

These run offline against the cached verification table so CI never depends on
Crossref being reachable. Regenerate the cache with `pixi run verify-citations`.

What these tests do and do not establish: they establish that every cited
identifier is a real, resolvable published record and that the model's evidence
ids reach the bibliography. They establish nothing about whether a given paper
supports the edge direction, compartment or species it is cited for.
"""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.evidence.citations import (
    REQUIRED_REFERENCE_COLUMNS,
    TITLE_SIMILARITY_FLOOR,
    VERIFICATION_COLUMNS,
    check_bibliography,
    check_resolution_cache,
    load_references,
    load_verification,
)


class BibliographyIntegrityTest(unittest.TestCase):
    def test_bibliography_is_structurally_intact(self) -> None:
        report = check_bibliography(ROOT)
        self.assertEqual(report.errors, [], f"bibliography defects: {report.errors}")

    def test_required_columns_present(self) -> None:
        for row in load_references(ROOT):
            for column in REQUIRED_REFERENCE_COLUMNS:
                self.assertIn(column, row)

    def test_every_reference_has_a_well_formed_doi(self) -> None:
        for row in load_references(ROOT):
            self.assertTrue(row["doi"].strip().startswith("10."), row["ref_id"])

    def test_the_resolver_url_resolves_the_doi_the_row_records(self) -> None:
        """A row may not disagree with itself about which paper it cites.

        `verify-citations` resolves the `doi` COLUMN against Crossref and never
        looks at `url`, so a row can carry a crossref-verified DOI and a link to
        a different paper. That is not hypothetical: REF-073's DOI was corrected
        after Crossref resolved the original to an unrelated article, and the
        targeted fix patched the `doi` column while leaving the stale identifier
        in `url` -- so the verified row pointed a reader at the paper the
        verification had just rejected. The citation that broke this way is the
        sole support for a coupling verdict, which is the worst place for a
        reader to land somewhere else.
        """
        for row in load_references(ROOT):
            doi, url = row.get("doi", "").strip(), row.get("url", "").strip()
            if not doi or not url:
                continue
            for prefix in (
                "https://doi.org/",
                "http://doi.org/",
                "https://dx.doi.org/",
            ):
                if url.startswith(prefix):
                    self.assertEqual(
                        url[len(prefix) :].lower(),
                        doi.lower(),
                        f"{row['ref_id']}: url resolves {url[len(prefix) :]} but "
                        f"the row records doi {doi}",
                    )
                    break

    def test_dois_are_deduplicated(self) -> None:
        dois = [r["doi"].strip().lower() for r in load_references(ROOT)]
        self.assertEqual(len(dois), len(set(dois)))

    def test_pmids_are_deduplicated(self) -> None:
        pmids = [
            r["pmid"].strip()
            for r in load_references(ROOT)
            if r.get("pmid", "").strip()
        ]
        self.assertEqual(len(pmids), len(set(pmids)))

    def test_duplicate_doi_is_detected(self) -> None:
        """The dedup check must actually fire, not merely pass on clean data."""
        rows = [dict(r) for r in load_references(ROOT)]
        rows[1]["doi"] = rows[0]["doi"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "context/literature").mkdir(parents=True)
            with (root / "context/literature/references.tsv").open(
                "w", newline="", encoding="utf-8"
            ) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=list(rows[0]), delimiter="\t"
                )
                writer.writeheader()
                writer.writerows(rows)
            report = check_bibliography(root)
            self.assertTrue(any("duplicate doi" in e.lower() for e in report.errors))


class ResolutionCacheTest(unittest.TestCase):
    def test_every_reference_resolved_to_a_real_record(self) -> None:
        report = check_resolution_cache(ROOT)
        self.assertEqual(report.errors, [], f"unresolved citations: {report.errors}")

    def test_cache_covers_every_reference(self) -> None:
        refs = {r["ref_id"] for r in load_references(ROOT)}
        cached = {r["ref_id"] for r in load_verification(ROOT)}
        self.assertEqual(
            refs - cached, set(), "references missing a verification record"
        )

    def test_cache_has_expected_columns(self) -> None:
        for row in load_verification(ROOT):
            self.assertEqual(set(row), set(VERIFICATION_COLUMNS))

    def test_title_mismatches_are_surfaced_as_warnings_not_hidden(self) -> None:
        """A stored title that diverges from the record must be visible."""
        report = check_resolution_cache(ROOT)
        low = [
            r
            for r in load_verification(ROOT)
            if float(r["title_similarity"]) < TITLE_SIMILARITY_FLOOR
        ]
        self.assertEqual(len(report.warnings), len(low))

    def test_unresolved_doi_is_reported_as_an_error(self) -> None:
        """Prove the resolution check fails on a bad record rather than passing."""
        refs = load_references(ROOT)
        cache = [dict(r) for r in load_verification(ROOT)]
        cache[0]["resolved"] = "false"
        cache[0]["note"] = "synthetic failure"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "context/literature").mkdir(parents=True)
            for name, rows in (
                ("references.tsv", refs),
                ("citation_verification.tsv", cache),
            ):
                with (root / "context/literature" / name).open(
                    "w", newline="", encoding="utf-8"
                ) as handle:
                    writer = csv.DictWriter(
                        handle, fieldnames=list(rows[0]), delimiter="\t"
                    )
                    writer.writeheader()
                    writer.writerows(rows)
            report = check_resolution_cache(root)
            self.assertTrue(any("did not resolve" in e for e in report.errors))


class ModelEvidenceReachesBibliographyTest(unittest.TestCase):
    def test_every_executable_edge_cites_a_known_evidence_id(self) -> None:
        model = (
            ROOT / "models/superset/adoc-literature-superset-v0.3.0/edge_evidence.tsv"
        )
        with model.open(encoding="utf-8") as handle:
            edges = list(csv.DictReader(handle, delimiter="\t"))
        with (ROOT / "context/evidence-register.tsv").open(encoding="utf-8") as handle:
            known = {r["evidence_id"] for r in csv.DictReader(handle, delimiter="\t")}
        unknown = sorted({e["evidence_id"] for e in edges} - known)
        self.assertEqual(unknown, [], f"edges cite unregistered evidence: {unknown}")

    def test_no_executable_edge_has_an_empty_evidence_id(self) -> None:
        model = (
            ROOT / "models/superset/adoc-literature-superset-v0.3.0/edge_evidence.tsv"
        )
        with model.open(encoding="utf-8") as handle:
            edges = list(csv.DictReader(handle, delimiter="\t"))
        empty = [e["edge_id"] for e in edges if not e["evidence_id"].strip()]
        self.assertEqual(empty, [])


if __name__ == "__main__":
    unittest.main()
