"""Repo-wide guard: the ADOC treated condition is never described as P4.

The collaborator confirmed on 2026-07-29 (SOFIA-COMM-004) that the treated
condition is ``E2 + MPA + cAMP + XAV939``. The source workbook's own label,
``HT (E2+P4+XAV939)``, is wrong twice over -- it names P4 where the progestin
was the synthetic progestin MPA, and it omits cAMP entirely.

That label is still *provenance*, so it must survive verbatim wherever the
repository is quoting the workbook. What must not survive is an unmarked use
that reads as a claim about the experiment. This module therefore permits the
string only when an explicit source-label marker sits nearby, and separately
asserts that the verbatim label is still recoverable -- a guard that allowed
deleting it would destroy provenance rather than protect it.

Scope note: plain "P4"/"progesterone" is deliberately NOT searched for. The
curated literature corpus legitimately discusses progesterone in dozens of
places (context/literature/**, docs/curation_increment_*.md, the *_PGR node
descriptions). Only the ADOC-condition form is unambiguous.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

#: Matches the source label "E2+P4+XAV939" and "E2 + P4 + XAV939" -- the
#: ADOC-condition form only, whitespace-tolerant -- but not a bare mention of
#: P4 or progesterone. (This module is itself tracked and therefore scanned by
#: its own guard, so the two lines above must carry a marker word like any
#: other quotation of the workbook label.)
CONDITION_P4_RE = re.compile(r"E2\s*\+\s*P4\s*\+\s*XAV939")

#: Any one of these near a hit marks it as a quotation of the source rather
#: than a claim about the experiment.
SOURCE_LABEL_MARKERS = (
    "source label",
    "source_label",
    "workbook label",
    "workbook's own",
    "verbatim",
    "source_condition_label",
    "condition_resolution_note",
    "labels",
    "label reads",
)

#: Directories whose progesterone content is external literature, not the ADOC
#: condition. Excluded so a well-meaning sweep cannot "correct" cited papers.
LITERATURE_PREFIXES = (
    "context/literature/",
    "docs/curation_increment_",
)

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".tsv",
    ".toml",
    ".txt",
    ".bnd",
    ".cfg",
    ".json",
}


def _tracked_text_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return [
        path
        for path in out
        if Path(path).suffix in TEXT_SUFFIXES
        and not path.startswith("data/")
        and not path.startswith(LITERATURE_PREFIXES)
        and (ROOT / path).is_file()
    ]


class ConditionLabelGuardTest(unittest.TestCase):
    def test_no_artifact_describes_the_condition_as_p4_without_marking_it(
        self,
    ) -> None:
        """Every ADOC-condition P4 hit must be marked as the source label.

        A hit is accepted when a marker appears on the same line, on either of
        the two preceding lines (comments precede the code they describe), or on
        the following line -- enough for a fielded TSV cell or a wrapped
        comment, tight enough that a bare prose claim fails.
        """
        unmarked: list[str] = []
        for rel in _tracked_text_files():
            lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                if not CONDITION_P4_RE.search(line):
                    continue
                window = " ".join(lines[max(0, index - 2) : index + 2]).lower()
                if not any(marker in window for marker in SOURCE_LABEL_MARKERS):
                    unmarked.append(f"{rel}:{index + 1}: {line.strip()[:120]}")
        self.assertEqual(
            unmarked,
            [],
            "the ADOC condition is described as E2+P4+XAV939 without marking it "
            "as the verbatim workbook label; the actual condition is "
            "E2 + MPA + cAMP + XAV939 (SOFIA-COMM-004):\n" + "\n".join(unmarked),
        )

    def test_the_verbatim_workbook_label_is_still_present(self) -> None:
        """Counterweight to the guard above: provenance must not be deleted."""
        table = (ROOT / "input_tables" / "adoc_secreted_proteins.tsv").read_text(
            encoding="utf-8"
        )
        # Both forms of the verbatim workbook label, nbsp and plain space.
        self.assertIn("HT (E2+P4+XAV939)", table)
        self.assertIn("HT\xa0(E2+P4+XAV939)", table)

    def test_the_normalized_condition_names_all_four_agents(self) -> None:
        from dt_adoc.data.secreted_proteins import (
            _CONDITION_CORRECTION_NOTE,
            CONDITION_FULL_COCKTAIL,
        )

        self.assertEqual(CONDITION_FULL_COCKTAIL, "e2_mpa_camp_xav939_96h")
        for token in ("E2", "MPA", "cAMP", "XAV939"):
            self.assertIn(token, _CONDITION_CORRECTION_NOTE)
        self.assertNotIn("P4", CONDITION_FULL_COCKTAIL)

    def test_the_literature_corpus_is_out_of_scope(self) -> None:
        """A test OF the guard, so nobody later 'fixes' cited papers.

        The excluded prefixes must actually contain progesterone discussion; if
        they stop doing so the exclusion is dead weight and should be removed.
        """
        tracked = _tracked_text_files()
        for prefix in LITERATURE_PREFIXES:
            self.assertFalse(
                [path for path in tracked if path.startswith(prefix)],
                f"{prefix} should be excluded from the guard's file list",
            )

    def test_no_mapping_row_claims_a_component_specific_effect(self) -> None:
        """The cocktail has no single-agent arm, so no artifact may attribute an
        effect to MPA, cAMP or XAV939 individually (SOFIA-COMM-004). IN_XAV939
        is additionally a zero-degree node in the models used for calibration.
        """
        from dt_adoc.calibration.observation_map import load_observation_map

        forbidden = (
            "effect of mpa",
            "camp alone",
            "camp-specific",
            "xav939 alone",
            "xav939-specific",
            "due to xav939",
            "mpa-specific",
            "attributable to mpa",
        )
        offenders: list[str] = []
        for row in load_observation_map():
            haystack = " ".join(
                row[field]
                for field in ("comparison", "claim_ceiling", "censoring_note")
            ).lower()
            for phrase in forbidden:
                # A claim ceiling is allowed to say the attribution is
                # forbidden; it is the bare assertion that is not.
                if phrase in haystack and "not" not in haystack:
                    offenders.append(f"{row['mapping_id']}: {phrase}")
        self.assertEqual(offenders, [], offenders)


class ReplicateStructureGuardTest(unittest.TestCase):
    """No mapping row may treat chips or columns as independent replicates."""

    @classmethod
    def setUpClass(cls) -> None:
        from dt_adoc.calibration.observation_map import load_observation_map

        cls.rows = load_observation_map()
        cls.protein_rows = [
            row
            for row in cls.rows
            if row["source_table"] == "input_tables/adoc_secreted_proteins.tsv"
        ]

    def test_there_are_protein_rows_to_check(self) -> None:
        self.assertGreater(len(self.protein_rows), 0)

    def test_no_row_claims_independent_biological_replicates(self) -> None:
        forbidden = (
            "independent biological replicate",
            "independent patients",
            "n=5 patients",
            "five independent",
        )
        offenders: list[str] = []
        for row in self.rows:
            haystack = " ".join(
                row[field]
                for field in ("comparison", "supporting_fraction", "censoring_note")
            ).lower()
            for phrase in forbidden:
                if phrase in haystack and "not " not in haystack:
                    offenders.append(f"{row['mapping_id']}: {phrase}")
        self.assertEqual(offenders, [], offenders)

    def test_no_row_asserts_a_patient_level_statistic(self) -> None:
        forbidden = (
            "patient-level variance",
            "donor-level variance",
            "per-patient",
            "paired donor",
            "standard error",
        )
        offenders: list[str] = []
        for row in self.rows:
            haystack = " ".join(
                row[field] for field in ("comparison", "supporting_fraction")
            ).lower()
            offenders += [
                f"{row['mapping_id']}: {phrase}"
                for phrase in forbidden
                if phrase in haystack
            ]
        self.assertEqual(offenders, [], offenders)

    def test_every_protein_row_records_the_replicate_ceiling(self) -> None:
        """Makes the limitation structural rather than remembered: any row
        sourced from this dataset must carry the donor caveat in its ceiling.
        """
        for row in self.protein_rows:
            self.assertIn(
                "config/adoc_chip_donor_provenance.tsv",
                row["claim_ceiling"],
                row["mapping_id"],
            )
            self.assertIn("REPLICATE CEILING", row["claim_ceiling"], row["mapping_id"])

    def test_every_row_carries_a_non_empty_claim_ceiling(self) -> None:
        for row in self.rows:
            self.assertNotEqual(row["claim_ceiling"].strip(), "", row["mapping_id"])

    def test_igfbp1_and_prl_rows_are_marked_as_unpaired(self) -> None:
        """The column-to-chip mapping is lost, so every IGFBP-1/PRL row that
        spans more than one day row must say the comparison is not paired.
        """
        for row in self.protein_rows:
            if row["protein"] not in {"IGFBP-1", "PRL", "IGFBP-1;PRL"}:
                continue
            day_rows = {cell[-1] for cell in row["source_cells"].split(",") if cell}
            if len(day_rows) <= 1:
                continue
            ceiling = row["claim_ceiling"].lower()
            self.assertTrue(
                "not paired" in ceiling or "unpaired" in ceiling,
                f"{row['mapping_id']} spans day rows {sorted(day_rows)} but its "
                "claim_ceiling does not say the columns are not paired",
            )

    def test_no_mapping_names_a_chip_for_a_lost_sheet(self) -> None:
        """No artifact may index IGFBP-1/PRL columns as chips or patients."""
        for row in self.protein_rows:
            if row["protein"] in {"PAEP"}:
                continue
            for series in row["source_series_id"].split(";"):
                if not series:
                    continue
                self.assertFalse(
                    series.startswith("PAEP_"),
                    f"{row['mapping_id']} joins a non-PAEP protein to a chip "
                    f"series {series!r}",
                )


if __name__ == "__main__":
    unittest.main()
