"""The 2026-09-22 PRL/IGFBP1/FOXO1 evidence-registration unit, end to end.

Fifteen papers were read in full from the gitignored library of the main
checkout; fourteen are registered as `REF-078`..`REF-091`, and one -- Zhang 2020,
retracted on 10 September 2026 -- is deliberately NOT registered: it gets no
`REF-*` id, and its manifest row carries `registration_decision =
excluded_retracted`, so that a later search which ranks it highly cannot quietly
re-admit it. It *is* recorded at claim level, as ledger row `PIF-010`, which is
where the retraction notice and the reason live; "not registered" means no
bibliography entry, not absent from the record. The unit changes no executable
model artifact.

The pattern is `tests/unit/test_curation_increment_08_blocked_sources.py`
`ProvenanceTest`: a `PAPERS` table of facts read off the files, checked against
**three** of the four registration artifacts at once -- `references.tsv`,
`pdf_manifest.tsv` and the ledger -- because a registration consistent with only
some of them is the failure this repository keeps finding.

**The fourth, `citation_verification.tsv`, is NOT read here**, and an earlier
docstring claimed it was. It is covered by
`test_citation_integrity.test_cache_covers_every_reference`, which fails until
`pixi run verify-citations` has resolved every reference -- so the suite is
protected and only the coverage claim was wrong. Recorded rather than quietly
fixed, because a guard that overstates its own reach is the specific defect this
repository has had to repair more than once.

**The digests below are the single source of truth for what was read.** They were
recomputed from the files in this session and each one must also appear in the
`verification_route` of its ledger row, which is what stops a row citing a paper
nobody content-addressed.
"""

from __future__ import annotations

import csv
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

LITERATURE = ROOT / "context" / "literature"
REFERENCES = LITERATURE / "references.tsv"
MANIFEST = LITERATURE / "pdf_manifest.tsv"
LEDGER = LITERATURE / "reviews" / "prl_igfbp1_foxo1_2026-09-22.primary-verification.tsv"
DISPOSITIONS = (
    LITERATURE
    / "reviews"
    / "deep_research_adhesion_model_2026-09-11.candidate-node-dispositions.tsv"
)
U4B_LEDGER = (
    LITERATURE
    / "reviews"
    / "deep_research_adhesion_model_2026-09-11.primary-verification.tsv"
)
REGISTER = ROOT / "context" / "evidence-register.tsv"

#: The fourteen registered papers: finding id -> the facts read off the file.
PAPERS: dict[str, dict[str, str]] = {
    "REF-078": {
        "pdf": "PDF-050",
        "finding": "PIF-001",
        "pages": "10",
        "doi": "10.1210/me.2005-0275",
        "pmid": "16123151",
        "sha256": "3044044c08fc9a8e132f6485d0445aa5b983373ffc4ab0707bb7db21ec2b3670",
    },
    "REF-079": {
        "pdf": "PDF-051",
        "finding": "PIF-002",
        "pages": "9",
        "doi": "10.1677/joe.1.06451",
        "pmid": "16614392",
        "sha256": "bf941a40db958f50bd7b628e9b6194cfc53d69861c1e4d6eb25c05159186b235",
    },
    "REF-080": {
        "pdf": "PDF-052",
        "finding": "PIF-003",
        "pages": "7",
        "doi": "10.1210/en.2006-0167",
        "pmid": "16690806",
        "sha256": "90e3233e2b245076c61eab66e265e3b7421855298ecb5db958dd0b2e09947e4f",
    },
    "REF-081": {
        "pdf": "PDF-053",
        "finding": "PIF-004",
        "pages": "18",
        "doi": "10.1371/journal.pone.0171004",
        "pmid": "28135285",
        "sha256": "9eaaa29b4ebac1e2d3e5f9495ede11d15657de064cfe307fae9115074fcaebfd",
    },
    "REF-082": {
        "pdf": "PDF-054",
        "finding": "PIF-005",
        "pages": "18",
        "doi": "10.1095/biolreprod.105.043182",
        "pmid": "15987820",
        "sha256": "4d90f1b164863978d75b161b8c4298ef6be0d92aa4b08f9b51e22483c717e066",
    },
    "REF-083": {
        "pdf": "PDF-055",
        "finding": "PIF-006",
        "pages": "8",
        "doi": "10.1371/journal.pone.0006845",
        "pmid": "19727442",
        "sha256": "276090cd0d0954f2399e826f861ff04f0bda779b52a3bd12b1716e0d5892e0e0",
    },
    "REF-084": {
        "pdf": "PDF-056",
        "finding": "PIF-007",
        "pages": "14",
        "doi": "10.1093/biolre/ioac041",
        "pmid": "35191464",
        "sha256": "4854c5ca1a3844c15144e2d3e45dcf63600ad6ea7fd2bb1feafa46ee5fbb1f1a",
    },
    "REF-085": {
        "pdf": "PDF-057",
        "finding": "PIF-008",
        "pages": "12",
        "doi": "10.1095/biolreprod64.2.590",
        "pmid": "11159362",
        "sha256": "3154d72d3c2fa1b0520750788e72078c9b787e6dc4d5fea403e6dc009b12ed99",
    },
    "REF-086": {
        "pdf": "PDF-058",
        "finding": "PIF-009",
        "pages": "9",
        "doi": "10.1095/biolreprod.106.058347",
        "pmid": "17942799",
        "sha256": "14b13608028ac3e6bcbc604b4c0fad6d562de652dfe90c0e666226f93d2d0adf",
    },
    "REF-087": {
        "pdf": "PDF-060",
        "finding": "PIF-011",
        "pages": "8",
        "doi": "10.1074/jbc.M704723200",
        "pmid": "17711857",
        "sha256": "ee6e74bbafe0b7ed021712476ab7d561439d7edcca3130d6b0adb982a4593880",
    },
    "REF-088": {
        "pdf": "PDF-061",
        "finding": "PIF-012",
        "pages": "10",
        "doi": "10.1530/REP-10-0468",
        "pmid": "21307272",
        "sha256": "5c78f2113ed8bc6652a24d6fd8ea8c9c357045582834051d809e6e9b2f3bec2f",
    },
    "REF-089": {
        "pdf": "PDF-062",
        "finding": "PIF-013",
        "pages": "9",
        "doi": "10.1093/humrep/des203",
        "pmid": "22740495",
        "sha256": "8ec7e22cb3db0c3458f4fc8c24ab10da1b169978c936ed471daf8957c5459111",
    },
    "REF-090": {
        "pdf": "PDF-063",
        "finding": "PIF-014",
        "pages": "9",
        "doi": "10.1371/journal.pone.0012970",
        "pmid": "20885978",
        "sha256": "198ecdd8dc90fd8b2d95158e49b4986979584f669f8d4b8f339a8d4baa38b6c8",
    },
    "REF-091": {
        "pdf": "PDF-064",
        "finding": "PIF-015",
        "pages": "13",
        "doi": "10.1210/me.2014-1292",
        "pmid": "25584414",
        "sha256": "4a856d3cf79792f5203001e794e5686f914921f77ba4fb5a180bc6ed1e0d931e",
    },
}

#: The one paper read and deliberately refused, with the reason machine-readable.
RETRACTED = {
    "pdf": "PDF-059",
    "finding": "PIF-010",
    "doi": "10.3389/fcell.2020.573028",
    "notice_doi": "10.3389/fcell.2026.1988449",
    "sha256": "f0b80cc514b2c14d252f4b6ffb18a68534835444462d4231ff0e21c3396f7bd1",
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class ProvenanceTest(unittest.TestCase):
    """Registration is consistent across `references.tsv`, `pdf_manifest.tsv` and
    the ledger, or it is not done. `citation_verification.tsv` is the fourth
    registration artifact and is guarded by `test_citation_integrity`, not here."""

    def test_every_registered_paper_is_registered_end_to_end(self) -> None:
        refs = {r["ref_id"]: r for r in _rows(REFERENCES)}
        manifest = {r["ref_id"]: r for r in _rows(MANIFEST) if r["ref_id"]}
        ledger = {r["finding_id"]: r for r in _rows(LEDGER)}
        for ref_id, facts in PAPERS.items():
            with self.subTest(ref=ref_id):
                self.assertIn(ref_id, refs)
                self.assertEqual(refs[ref_id]["doi"], facts["doi"])
                self.assertEqual(refs[ref_id]["pmid"], facts["pmid"])
                row = manifest[ref_id]
                self.assertEqual(row["manifest_id"], facts["pdf"])
                self.assertEqual(row["sha256"], facts["sha256"])
                self.assertEqual(row["pages"], facts["pages"])
                self.assertEqual(row["doi"].lower(), facts["doi"].lower())
                self.assertEqual(row["full_text_inspected"], "yes")
                self.assertEqual(row["registration_decision"], "registered")
                self.assertEqual(row["batch"], "prl_igfbp1_foxo1_2026-09-22")
                # The ledger row must content-address the file it read.
                route = ledger[facts["finding"]]["verification_route"]
                self.assertIn(facts["sha256"], route)
                self.assertIn(facts["pages"] + " pages", route)
                self.assertEqual(
                    ledger[facts["finding"]]["ref_id"], f"{ref_id} ({facts['pdf']})"
                )

    def test_the_retracted_paper_is_refused_in_a_machine_readable_way(self) -> None:
        """A retraction recorded only in prose is a retraction the next search
        will not see.

        Zhang 2020 would otherwise have been the best available lever on the
        `S_BMP2` = `S_PGR` degeneracy, so it is exactly the paper a later unit
        would re-find and rank first. The refusal therefore lives in three
        machine-readable places at once: no `REF-*` id anywhere, a manifest row
        whose `registration_decision` is not `registered`, and a ledger row whose
        `confidence` is `excluded`. The ledger row is deliberate -- refusing a
        paper silently is how the refusal gets lost -- so "not registered" here
        means "no bibliography entry", never "not written down".
        """
        manifest = {r["manifest_id"]: r for r in _rows(MANIFEST)}
        row = manifest[RETRACTED["pdf"]]
        self.assertEqual(row["doi"], RETRACTED["doi"])
        self.assertEqual(row["sha256"], RETRACTED["sha256"])
        self.assertEqual(row["ref_id"], "")
        self.assertEqual(row["registration_decision"], "excluded_retracted")
        self.assertIn("RETRACTED", row["key_finding_for_adoc"].upper())
        self.assertIn(RETRACTED["notice_doi"], row["key_finding_for_adoc"])

        refs = _rows(REFERENCES)
        self.assertNotIn(RETRACTED["doi"].lower(), {r["doi"].lower() for r in refs})

        ledger = {r["finding_id"]: r for r in _rows(LEDGER)}
        pif = ledger[RETRACTED["finding"]]
        self.assertEqual(pif["confidence"], "excluded")
        self.assertEqual(pif["ref_id"], f"(not registered; {RETRACTED['pdf']})")
        self.assertIn("MUST NOT BE CITED", pif["canonical_promotion_decision"])

    def test_no_pdf_was_committed_by_this_increment(self) -> None:
        """Source PDFs stay in the gitignored library; only the digest is tracked.

        Checked by author-and-year against the tracked `*.pdf` list rather than by
        the manifest's `batch` tag, because the manifest is exactly the artifact
        that would be consistent with itself if a PDF had been committed.
        """
        tracked = subprocess.run(
            ["git", "ls-files", "*.pdf"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        for path in tracked:
            for author in (
                "Labied et al.",
                "Grinius et al.",
                "Buzzio et al.",
                "Ujvari et al.",
                "Kim et al. - 2005",
                "Lynch et al.",
                "Kang et al. - 2022",
                "Meseguer et al.",
                "Gipson et al.",
                "Zhang et al. - 2020",
                "Li et al. - 2007",
                "Harman et al.",
                "Paule et al.",
                "Kane et al.",
                "Vasquez et al.",
            ):
                self.assertNotIn(author, path)

    def test_the_corpus_transport_archives_were_not_committed(self) -> None:
        """`context/literature/pdfs.tar.gz` and `pdfs.zip` are transport
        artifacts for moving the gitignored library between checkouts. They carry
        every source PDF, so committing one would defeat the whole no-PDF rule in
        a single file that no per-paper check would notice."""
        tracked = subprocess.run(
            ["git", "ls-files", "context/literature"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        for path in tracked:
            self.assertFalse(
                path.endswith((".tar.gz", ".zip", ".tgz", ".7z")),
                f"{path} looks like a corpus transport archive",
            )


class AuthorManuscriptTest(unittest.TestCase):
    def test_the_one_author_manuscript_is_flagged_where_a_reader_will_see_it(
        self,
    ) -> None:
        """Kim 2005 is held as an NIH Public Access author manuscript.

        Its file opens "NIH Public Access / Author Manuscript / Biol Reprod.
        Author manuscript; available in PMC 2005 October 11", so the 18 pages the
        manifest records are the manuscript's pagination and NOT journal pages
        833-839. A reader following a page reference needs that from the
        machine-readable record, which is the lesson `PDF-048` taught on
        2026-09-18; the corpus-wide census is in
        `test_pdf_manifest.test_files_recorded_as_not_versions_of_record_stay_countable`.
        """
        manifest = {r["manifest_id"]: r for r in _rows(MANIFEST)}
        self.assertEqual(manifest["PDF-054"]["rendering_read"], "author_manuscript")
        self.assertEqual(manifest["PDF-054"]["publication_status"], "published")
        self.assertIn(
            "AUTHOR MANUSCRIPT", manifest["PDF-054"]["key_finding_for_adoc"].upper()
        )
        route = {r["finding_id"]: r for r in _rows(LEDGER)}["PIF-005"][
            "verification_route"
        ]
        self.assertIn("AUTHOR MANUSCRIPT", route.upper())
        self.assertIn("not the version of record", route)
        # Everything else in the unit is a version of record.
        for facts in PAPERS.values():
            if facts["pdf"] == "PDF-054":
                continue
            with self.subTest(pdf=facts["pdf"]):
                self.assertEqual(
                    manifest[facts["pdf"]]["rendering_read"], "version_of_record"
                )


class ScopeTest(unittest.TestCase):
    """This is an evidence-registration unit. Nothing executable may move."""

    def test_no_ledger_row_claims_an_executable_change(self) -> None:
        """Every one of the fifteen rows must state, in its own promotion column,
        that nothing was promoted.

        Deliberately NOT written as a `git status` check on `models/**`. That was
        the first version and it is inert the moment the change is committed: on a
        clean tree it iterates an empty list and passes without asserting
        anything, which is precisely the shape of guard this repository has
        already been bitten by. The executable invariant is carried where it can
        actually bind -- `test_curation_increment_08_blocked_sources.NoExecutableChangeTest`
        and `test_v05_u4b_candidate_closure.NoMechanismChangeTest` pin the
        committed `.bnd` at 19 free variables and 35 distinct Boolean functions,
        and they run against the file rather than against a diff. What binds HERE
        is the claim each row makes, and it binds all fifteen of them.
        """
        rows = _rows(LEDGER)
        self.assertEqual(len(rows), 15)
        for row in rows:
            with self.subTest(finding=row["finding_id"]):
                verdict = row["canonical_promotion_decision"].upper()
                self.assertTrue(
                    verdict.startswith(("NO PROMOTION", "EXCLUDED")),
                    f"{row['finding_id']} does not open by refusing promotion",
                )

    def test_the_ledger_claims_no_disposition_it_is_not_entitled_to(self) -> None:
        """Only `PIF-001` moves a candidate, and it moves exactly one.

        `candidate_ids` and `final_dispositions` are the machine-readable columns
        the U4b verdict-agreement guards read, so a row that names a candidate is
        asserting a live verdict for it. Fourteen of the fifteen rows here bear on
        model elements without being entitled to a verdict -- `PIF-007` is the
        sharp case, because Kang 2022 really does bear on `S_AKT_EXCESS` and
        moving that row was explicitly out of scope. Those rows leave both columns
        empty and say what they bear on in prose instead.
        """
        rows = _rows(LEDGER)
        self.assertEqual(len(rows), 15)
        named = {
            r["finding_id"]: (r["candidate_ids"], r["final_dispositions"])
            for r in rows
            if r["candidate_ids"] or r["final_dispositions"]
        }
        self.assertEqual(named, {"PIF-001": ("S_FOXO1", "S_FOXO1=RETAIN_CATALOG_ONLY")})
        by_id = {r["candidate_id"]: r for r in _rows(DISPOSITIONS)}
        self.assertEqual(by_id["S_FOXO1"]["final_disposition"], "RETAIN_CATALOG_ONLY")
        self.assertEqual(
            by_id["S_FOXO1"]["first_failing_criterion"], "5(4)_delta_and_alias"
        )
        self.assertEqual(by_id["S_FOXO1"]["unblock_locus"], "ADOC_RUNNABLE")
        # Node and encoding verdicts are untouched: the node was never in doubt.
        self.assertEqual(by_id["S_FOXO1"]["node_verdict"], "JUSTIFIED")
        self.assertEqual(by_id["S_FOXO1"]["encoding_verdict"], "REJECT_AS_STAGED")
        # ...and the row Kang 2022 bears on was NOT moved by this unit. It has
        # since moved, in U5b (2026-09-23), and that move must be attributed to
        # U5b's own dated ledger rather than to `PIF-007`, which still names no
        # candidate (asserted above). So what this unit guarantees is checked
        # as attribution, not as a frozen value that a later unit may not change.
        akt = by_id["S_AKT_EXCESS"]
        self.assertIn("U5B-001", akt["verification_finding_ids"])
        self.assertIn("2026-09-23 IN U5b", akt["change_from_prior"])
        self.assertNotIn("PIF-007", named)

    def test_the_two_superseded_u4b_rows_point_forward(self) -> None:
        """Both rows that stated `S_FOXO1=WAIT_FOR_EXPERIMENT` keep their read and
        say where the verdict went. Enforced here as well as in
        `test_v05_u4b_candidate_closure`, because a reader landing on the 2026-09-17
        ledger is the person this pointer exists for."""
        u4b = {r["finding_id"]: r for r in _rows(U4B_LEDGER)}
        for finding in ("U4B-DRREF-001", "U4B-DRREF-002"):
            with self.subTest(finding=finding):
                note = u4b[finding]["canonical_promotion_decision"]
                self.assertIn("FORWARD REFERENCE", note)
                self.assertIn("PIF-001", note)
                self.assertIn("THIS ROW'S READ STANDS", note)
                self.assertNotIn("SUPERSEDED", u4b[finding]["verification_route"])


class SupersessionTest(unittest.TestCase):
    def test_sofia_str_001_no_longer_asserts_a_false_observation(self) -> None:
        """The manuscript's wording is preserved; its status as a verified
        observation of the canonical data is not.

        The register row transcribed the manuscript summary "PRL and IGFBP-1 were
        undetectable day 0". That is true for PRL and false for IGFBP-1, which the
        canonical workbook detects in 4 of 5 day-0 stromal units. The repair keeps
        the quoted wording -- the manuscript is immutable evidence and the row is
        the record of what it says -- and narrows the claim the row makes about it.
        The id is unchanged because four other artifacts cite it, including two
        test modules that read the detection limits off this row.
        """
        row = {r["evidence_id"]: r for r in _rows(REGISTER)}["SOFIA-STR-001"]
        self.assertEqual(row["status"], "verified_by_source_file")
        # The manuscript's own words survive, quoted rather than asserted.
        self.assertIn(
            "PRL and IGFBP-1 were undetectable day 0 and increased at days 3 and 6",
            row["observation"],
        )
        self.assertIn("4 OF 5 DAY-0 UNITS", row["observation"])
        self.assertIn("37.90-551.26 pg/mL", row["observation"])
        # ...and the detection limits its consumers read are untouched.
        self.assertIn("PRL detection limit 10 pg/mL", row["notes"])
        self.assertIn("IGFBP-1 detection limit 5 pg/mL", row["notes"])
        self.assertIn("below detection is not numeric zero", row["notes"])


if __name__ == "__main__":
    unittest.main()
