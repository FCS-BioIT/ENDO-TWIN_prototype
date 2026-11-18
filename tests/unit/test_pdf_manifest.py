"""The literature PDF manifest records what was inspected, without the PDFs.

Source PDFs must never be committed; only extracted, attributed metadata belongs
in the repository. This manifest is the record that a paper was obtained and
read, and it is what a later increment consults before re-requesting a source.

The tracked-PDF invariant enforced here is deliberately NOT "no file ends in
.pdf". Evidence is not defined by extension or by directory: Deep Research and
literature evidence arrive as YAML, TSV, Markdown, PMID/DOI-backed records,
staged extracts and adjudications, and a rule keyed on `*.pdf` under
`context/literature/pdfs/` would both miss those and misclassify a figure the
repository generates itself. The invariant is instead:

    a tracked PDF is forbidden by default, and permitted only when it is
    PROVENANCE-BOUND -- a generated artifact that a metadata sidecar records by
    path and content hash, alongside the hashes of the source data it was
    rendered from.

That is what separates `docs/assets/adoc_identifiability_*.pdf`, which is a
deterministic render of tracked tables and is reproduced byte-for-byte by
`pixi run render-identifiability`, from a paper dropped into the tree. A source
PDF has no sidecar, so it still fails wherever it is put -- `docs/assets/`
included -- and a generated PDF whose bytes drift from its recorded hash fails
too.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MANIFEST = ROOT / "context/literature/pdf_manifest.tsv"
REFERENCES = ROOT / "context/literature/references.tsv"

EXPECTED_COLUMNS = (
    "manifest_id",
    "file_stem",
    "doi",
    "pmid",
    "publication_status",
    "rendering_read",
    "study_type",
    "system",
    "compartment",
    "key_finding_for_adoc",
    "figures_rendered",
    "batch",
    "pages",
    "sha256",
    "full_text_inspected",
    "ref_id",
    "registration_decision",
)

#: **`publication_status` describes the ARTICLE; `rendering_read` describes the
#: FILE.** Until 2026-09-18 one column carried both, because for every paper in
#: the corpus they coincided: a published article had been read from its version
#: of record, and an unedited manuscript from the manuscript. Zhou 2021 is the
#: first case where they come apart -- an article published in 2021, read from the
#: accepted author manuscript deposited in an institutional repository -- and a
#: single column could only misstate one of the two facts. The review of that
#: increment caught it: the prose said "author manuscript" while the only
#: machine-readable field said `published`, so the census of files that are not
#: versions of record was short by one.
PUBLICATION_STATUS_VALUES = ("published", "accepted_unedited")

#: Which rendering of the article was actually read and hashed. `unrecorded` is
#: for rows registered before the column existed; it is NOT an escape hatch, and
#: `test_new_registrations_must_record_their_rendering` forbids it for every row
#: minted from `PDF-048` onward. A later increment may resolve the `unrecorded`
#: rows from their digests, which is a shrink and needs no new rule.
RENDERING_READ_VALUES = (
    "version_of_record",
    "author_manuscript",
    "preprint",
    "unrecorded",
)

#: The first manifest id minted after `rendering_read` existed. Ids are sequential
#: and only increase, so "below this number" is exactly the frozen pre-column set
#: and every future row is bound.
#:
#: An earlier revision allowlisted a BATCH instead -- a one-element tuple holding
#: `blocked_source_refresh_2026-09-18` -- and that did not bind: the manifest
#: already carries 38 rows tagged `new` and 9 tagged `prior`, so a row appended
#: tomorrow as `new` with `unrecorded` passed every test in this file, which is
#: precisely the failure the rule exists to prevent.
FIRST_ID_REQUIRING_RENDERING = 48

#: Source PDFs committed before the no-source-PDF rule was adopted. Enumerated so
#: the invariant holds for everything new while the pre-existing set stays visible
#: rather than silently tolerated. `data/sciadv.adz2249.pdf` duplicates the
#: Zaragozano entry in the manifest; removing these is a separate decision, not
#: this increment's. Nothing may be added here: a new generated PDF earns its place
#: by being provenance-bound, and a new source PDF has no place at all.
PRE_EXISTING_TRACKED_PDFS = (
    (
        "data/Montagud - 2026 - Systems biology at the body scale "
        "Toward adaptive digital twins in precision medicine.pdf"
    ),
    (
        "data/Montagud et al. - 2022 - Patient-specific Boolean models of "
        "signalling networks guide personalised treatments.pdf"
    ),
    "data/sciadv.adz2249.pdf",
)


def provenance_bound_figures() -> dict[str, str]:
    """Map repo-relative figure path -> recorded sha256, from every tracked sidecar.

    A figure entry counts only when the sidecar ALSO hashes the source data the
    figure was rendered from. Recording an output hash alone would let any file
    be blessed by appending two lines to a JSON file; requiring the inputs means
    the entry asserts a reproducible derivation, which `pixi run
    render-identifiability` is what actually satisfies.

    Only entries carrying their own ``sha256`` are returned, because the caller
    verifies the bytes. The concordance sidecar uses a different shape -- a bare
    ``figure`` filename plus ``source_data_sha256`` -- and records no hash for
    the figure itself, so it contributes nothing here and could not bind a PDF.
    It has never held one; if that shape ever needs to, it must start emitting
    the output hash rather than this test relaxing to accept an unverifiable
    entry.
    """
    found: dict[str, str] = {}
    for sidecar in sorted(ROOT.glob("docs/**/*metadata*.json")):
        try:
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):  # pragma: no cover - malformed
            continue
        if not isinstance(payload, dict):  # pragma: no cover - unexpected shape
            continue

        figures = payload.get("figures")
        tables = payload.get("tables")
        if not isinstance(figures, list) or not isinstance(tables, list):
            continue
        # Inputs must be hashed too, or the figure entry asserts nothing.
        if not any(
            isinstance(t, dict) and t.get("path") and t.get("sha256") for t in tables
        ):
            continue
        for entry in figures:
            if isinstance(entry, dict) and entry.get("path") and entry.get("sha256"):
                found[str(entry["path"])] = str(entry["sha256"])
    return found


def rows() -> list[dict[str, str]]:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class PdfManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = rows()

    def test_columns_and_identifiers(self) -> None:
        self.assertEqual(list(self.rows[0]), list(EXPECTED_COLUMNS))
        ids = [row["manifest_id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_tracked_pdfs_are_provenance_bound_or_pre_existing(self) -> None:
        """A tracked PDF is forbidden unless it is a provenance-bound artifact.

        Renamed from `test_no_pdf_is_tracked_by_git`, which globbed `*.pdf` and
        so encoded a rule the repository does not hold. The manifest exists so
        that SOURCE papers need not be committed; it says nothing about a figure
        the repository renders from its own tracked tables. Under the old glob a
        deterministic PDF render failed while a paper renamed to `.txt` passed,
        which is the wrong invariant in both directions.

        What must stay true is that a committed PDF is traceable to inputs the
        repository also tracks. So each one must either be in the enumerated
        pre-existing set or be recorded, by path AND by content hash, in a
        sidecar that hashes its source data too -- and the recorded hash must
        match the bytes on disk, so the entry cannot be stale or forged.

        Checks what git tracks, not what is on disk: source PDFs are present in
        the working tree by design and gitignored.
        """
        tracked = subprocess.run(
            ["git", "ls-files", "*.pdf"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()

        bound = provenance_bound_figures()
        unexplained = []
        for path in sorted(set(tracked) - set(PRE_EXISTING_TRACKED_PDFS)):
            if path not in bound:
                unexplained.append(f"{path} (no sidecar records it as a figure)")
                continue
            digest = sha256((ROOT / path).read_bytes()).hexdigest()
            if digest != bound[path]:
                unexplained.append(
                    f"{path} (sidecar records {bound[path][:12]}..., "
                    f"file is {digest[:12]}...)"
                )
        self.assertEqual(
            unexplained,
            [],
            "tracked PDFs that are neither pre-existing nor provenance-bound: "
            f"{unexplained}",
        )

    def test_a_source_pdf_is_not_rescued_by_sitting_beside_generated_ones(
        self,
    ) -> None:
        """The exemption is provenance, never the directory.

        `docs/assets/` is where generated figures live, so it is the one place a
        stray paper could plausibly be dropped and look like it belonged. It
        would carry no sidecar entry, so the guard above already rejects it --
        this pins that the reason is the missing provenance and not the path,
        because a future refactor could otherwise quietly turn the check into a
        directory allowlist and lose the invariant while staying green.
        """
        bound = provenance_bound_figures()
        self.assertTrue(bound, "no sidecar records any figure; the guard is inert")
        for path in bound:
            self.assertTrue(
                (ROOT / path).exists(),
                f"sidecar records {path}, which is not in the tree",
            )
        intruder = "docs/assets/some_unregistered_paper.pdf"
        self.assertNotIn(
            intruder,
            bound,
            "a path that no sidecar emitted must never be considered bound",
        )

    def test_the_pdf_directory_is_ignored(self) -> None:
        ignored = subprocess.run(
            ["git", "check-ignore", "context/literature/pdfs/"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            ignored.returncode, 0, "context/literature/pdfs/ is not ignored"
        )

    def test_every_entry_has_a_doi_and_a_content_hash(self) -> None:
        for row in self.rows:
            self.assertTrue(row["doi"].startswith("10."), row["manifest_id"])
            self.assertEqual(len(row["sha256"]), 64, row["manifest_id"])

    def test_content_hashes_are_unique(self) -> None:
        """A duplicate hash means the same paper was supplied twice."""
        hashes = [row["sha256"] for row in self.rows]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_publication_status_is_in_vocabulary(self) -> None:
        for row in self.rows:
            self.assertIn(
                row["publication_status"], PUBLICATION_STATUS_VALUES, row["manifest_id"]
            )

    def test_unedited_manuscripts_are_flagged_and_countable(self) -> None:
        """Nothing from an unedited manuscript may reach executable_core, so the
        set must stay visible rather than blending into the bibliography.

        This set is about the ARTICLE -- accepted but not yet through production,
        so its final text may still change. See
        `test_files_that_are_not_versions_of_record_stay_countable` for the wider
        set, which is about the FILE and is the one a reader chasing a figure
        number or a page reference actually needs.
        """
        unedited = {
            row["file_stem"].split(" - ")[0]
            for row in self.rows
            if row["publication_status"] == "accepted_unedited"
        }
        self.assertEqual(unedited, {"Mo et al.", "Huang et al.", "Lin et al."})

    def test_rendering_read_is_in_vocabulary(self) -> None:
        for row in self.rows:
            self.assertIn(
                row["rendering_read"], RENDERING_READ_VALUES, row["manifest_id"]
            )

    def test_an_unedited_article_cannot_have_a_version_of_record(self) -> None:
        """The one relation between the two columns that is a matter of fact
        rather than of record-keeping: a version of record cannot exist for an
        article that has not been through production.

        Note what this does NOT license, because an earlier revision of this
        increment got it wrong: the entailment excludes `version_of_record` and
        nothing else. Three values remain, so it cannot select `author_manuscript`
        over `preprint`. `PDF-011`, `PDF-015` and `PDF-034` were briefly recorded
        as `author_manuscript` on this basis alone; they carry `unrecorded` now,
        which is the value for "not established", and establishing it means opening
        the files.
        """
        for row in self.rows:
            if row["publication_status"] != "accepted_unedited":
                continue
            with self.subTest(manifest=row["manifest_id"]):
                self.assertNotEqual(row["rendering_read"], "version_of_record")

    def test_new_registrations_must_record_their_rendering(self) -> None:
        """`unrecorded` is backfill for rows that pre-date the column, and must
        not become the default for new ones -- which is how the distinction would
        quietly stop being recorded at all.

        Keyed on the manifest id rather than on a batch allowlist. Ids are
        sequential, so every row minted from `PDF-048` on is bound by this whether
        or not anyone remembers to enumerate its batch; an allowlist binds only
        the batches someone thought of, which is no constraint on the next one.
        """
        bound = 0
        for row in self.rows:
            number = int(row["manifest_id"].split("-")[1])
            if number < FIRST_ID_REQUIRING_RENDERING:
                continue
            bound += 1
            with self.subTest(manifest=row["manifest_id"]):
                self.assertNotEqual(row["rendering_read"], "unrecorded")
        self.assertTrue(bound, "the rule must bind at least one row, or it is inert")

    def test_files_recorded_as_not_versions_of_record_stay_countable(self) -> None:
        """The census the single-column design could not express.

        `REF-076` content-addresses the **accepted author manuscript** of Zhou
        2021, and every figure number and page reference in
        `blocked_source_refresh_2026-09-18.primary-verification.tsv` is to that
        rendering. The article is published, so `publication_status` correctly
        reads `published` and the `REF-*` id is correctly minted -- but a reader
        following a figure reference needs to know which rendering they will be
        holding, and before this column nothing machine-readable said so.

        **This pins what is RECORDED as not a version of record, not what is.** The
        true set may be larger: 47 rows carry `unrecorded`, and any of them could
        turn out to be a manuscript or a preprint. An earlier name and docstring for
        this test said "files that are not versions of record" and called it a
        corpus-wide census, which claimed knowledge of files nobody has inspected.

        Pinned exactly rather than counted, because the point is visibility: a new
        row joining this set must be a deliberate act, taken on inspection.
        """
        not_vor = {
            row["manifest_id"]
            for row in self.rows
            if row["rendering_read"] in {"author_manuscript", "preprint"}
        }
        self.assertEqual(not_vor, {"PDF-048", "PDF-054"})
        by_id = {row["manifest_id"]: row for row in self.rows}
        # The divergence that forced the column, pinned as such.
        self.assertEqual(by_id["PDF-048"]["publication_status"], "published")
        self.assertEqual(by_id["PDF-048"]["rendering_read"], "author_manuscript")
        self.assertEqual(by_id["PDF-048"]["ref_id"], "REF-076")
        # ...and its companion in the same batch, which did not diverge.
        self.assertEqual(by_id["PDF-049"]["rendering_read"], "version_of_record")
        # `PDF-054` joined the set on 2026-09-22, on inspection, which is the
        # deliberate act this pin asks for. The file held for Kim 2005
        # (`REF-082`) opens "NIH Public Access / Author Manuscript / Biol
        # Reprod. Author manuscript; available in PMC 2005 October 11", so its
        # 18 pages are the manuscript's pagination and not journal pages
        # 833-839. A reader chasing a page reference in
        # `prl_igfbp1_foxo1_2026-09-22.primary-verification.tsv` row `PIF-005`
        # needs that, and `verification_route` on that row says it too.
        self.assertEqual(by_id["PDF-054"]["publication_status"], "published")
        self.assertEqual(by_id["PDF-054"]["rendering_read"], "author_manuscript")
        self.assertEqual(by_id["PDF-054"]["ref_id"], "REF-082")

    def test_manifest_dois_that_are_cited_resolve_in_the_bibliography(self) -> None:
        """A manifest entry need not be cited -- reading a paper and rejecting it
        is a valid outcome -- but a cited DOI must match the bibliography."""
        with REFERENCES.open(encoding="utf-8", newline="") as handle:
            known = {
                row["doi"].lower() for row in csv.DictReader(handle, delimiter="\t")
            }
        overlap = [row for row in self.rows if row["doi"].lower() in known]
        # 44 before the 2026-09-18 blocked-source refresh; PDF-048 (Zhou 2021,
        # REF-076) and PDF-049 (Ma 2023, REF-077) are both read AND registered,
        # so both are cited and both count here. The 2026-09-22 PRL/IGFBP1/FOXO1
        # unit adds 15 manifest rows, of which 14 are registered (REF-078 to
        # REF-091) and one is not: PDF-059 is Zhang 2020, retracted 10 September
        # 2026, recorded with `registration_decision = excluded_retracted` and no
        # REF id, so its DOI is deliberately absent from the bibliography and it
        # does not count here. 46 + 14 = 60.
        self.assertEqual(len(overlap), 60)

    def test_registration_decision_agrees_with_the_registry_both_ways(self) -> None:
        """A paper is registered, or it is deliberately not. Silent drift between
        the manifest and the registry becomes a failure rather than a gap."""
        with REFERENCES.open(encoding="utf-8", newline="") as handle:
            by_id = {
                row["ref_id"]: row for row in csv.DictReader(handle, delimiter="\t")
            }
        by_doi = {row["doi"].lower() for row in by_id.values()}
        for row in self.rows:
            if row["ref_id"]:
                self.assertEqual(row["registration_decision"], "registered", row)
                self.assertIn(row["ref_id"], by_id, row)
                self.assertEqual(
                    by_id[row["ref_id"]]["doi"].lower(), row["doi"].lower(), row
                )
            else:
                self.assertNotEqual(row["registration_decision"], "registered", row)
                self.assertNotIn(row["doi"].lower(), by_doi, row)

    def test_unedited_manuscripts_are_not_registered(self) -> None:
        """references.tsv has no publication_status column, so a REF id minted for
        an unedited manuscript is indistinguishable from a version of record at
        the point of use -- and since 5f8d7b4 a REF id is a content address."""
        for row in self.rows:
            if row["publication_status"] == "accepted_unedited":
                self.assertEqual(row["ref_id"], "", row)
                self.assertEqual(
                    row["registration_decision"], "deferred_unedited_manuscript", row
                )


if __name__ == "__main__":
    unittest.main()
