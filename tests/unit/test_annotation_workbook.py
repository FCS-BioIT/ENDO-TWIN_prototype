"""Contracts for the ADOC annotation workbook and the tables derived from it.

`data/secreción proteinas ADOC anotaciones.xlsx` arrived on 2026-07-29 as
annotation metadata for the measurement workbook. It is **gitignored** because
its shared strings carry the lab's own cell-source codes, so every test that
reads it skips when it is absent -- the same accommodation the repository already
makes for the 3.46 GB RDS. The tests that do NOT need it (the conditions table,
the privacy guard, the manifest row) always run.

Two invariants this module exists to protect:

* the annotation workbook is **not** a second measurement source. Its numeric
  cells are byte-identical to the measurement workbook, and its layout differs
  enough that a positional read silently misaligns. `SHEET_PRL` keeps the
  measurement workbook's literal trailing space precisely so a substitution
  fails loudly.
* the lab's raw cell-source codes never enter a tracked artifact.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.data.secreted_proteins import (
    COLLECTED_VOLUME,
    FLOW_RATE,
    SHEET_IGFBP1,
    SHEET_PAEP,
    SHEET_PRL,
    TECHNICAL_REPLICATE_N,
    build_protein_table,
    load_outlet_conditions,
)

MEASUREMENT = ROOT / "data" / "proteinas secretadas ADOC.xlsx"
ANNOTATION = ROOT / "data" / "secreción proteinas ADOC anotaciones.xlsx"

ANNOTATION_SHA256 = "400e291b773d95eba30e288be4d18d9ad530df4d2f2ea0f16ee13146e57e7481"
ANNOTATION_SIZE = 12697

#: Annotation-workbook layout, pinned so a silent re-save that shifts rows fails
#: loudly instead of being re-keyed by accident.
ANNOTATION_LAYOUT = {
    "PAEP": {"header_row": 17, "data_rows": (18, 19), "data_cols": "B:F"},
    "IGFBP-1": {"header_row": 26, "data_rows": (27, 28, 29), "data_cols": "B:K"},
    "PRL": {"header_row": None, "data_rows": (22, 23, 24), "data_cols": "B:G"},
}


def _require_annotation() -> None:
    if not ANNOTATION.is_file():
        raise unittest.SkipTest(
            f"{ANNOTATION.name} is gitignored (it carries the lab's own "
            "cell-source codes); present only on machines that hold it"
        )


def _load(path: Path):
    import openpyxl

    return openpyxl.load_workbook(path, data_only=True, read_only=False)


class AnnotationWorkbookIdentityTest(unittest.TestCase):
    """The two workbooks agree on values and differ on layout."""

    def setUp(self) -> None:
        _require_annotation()

    def test_the_recorded_hash_and_size_match_the_file(self) -> None:
        import hashlib

        payload = ANNOTATION.read_bytes()
        self.assertEqual(len(payload), ANNOTATION_SIZE)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), ANNOTATION_SHA256)

    def test_the_prl_sheet_name_differs_between_the_two_workbooks(self) -> None:
        """Both facts pinned at once.

        The measurement workbook's trailing space is literal and canonical; the
        annotation workbook drops it. Keying on one form and reading the other
        raises KeyError -- which is the safe outcome and must stay reachable.
        """
        measurement = _load(MEASUREMENT)
        annotation = _load(ANNOTATION)
        try:
            self.assertEqual(SHEET_PRL, "PRL ")
            self.assertIn("PRL ", measurement.sheetnames)
            self.assertNotIn("PRL ", annotation.sheetnames)
            self.assertIn("PRL", annotation.sheetnames)
            with self.assertRaises(KeyError):
                annotation[SHEET_PRL]
        finally:
            measurement.close()
            annotation.close()

    def test_annotation_layout_offsets_are_pinned(self) -> None:
        annotation = _load(ANNOTATION)
        try:
            for sheet, layout in ANNOTATION_LAYOUT.items():
                worksheet = annotation[sheet]
                for row_idx in layout["data_rows"]:
                    start, end = layout["data_cols"].split(":")
                    values = [
                        worksheet[f"{chr(col)}{row_idx}"].value
                        for col in range(ord(start), ord(end) + 1)
                    ]
                    self.assertTrue(
                        any(value is not None for value in values),
                        f"{sheet} row {row_idx} should carry data",
                    )
            merged = {str(rng) for rng in annotation[SHEET_IGFBP1].merged_cells.ranges}
            self.assertEqual(merged, {"B26:F26", "G26:K26"})
        finally:
            annotation.close()

    def test_paep_drops_the_two_valueless_chip_columns(self) -> None:
        measurement = _load(MEASUREMENT)
        annotation = _load(ANNOTATION)
        try:
            old = [
                measurement[SHEET_PAEP].cell(row=2, column=col).value
                for col in range(2, 9)
            ]
            new = [
                annotation[SHEET_PAEP].cell(row=17, column=col).value
                for col in range(2, 7)
            ]
            self.assertEqual(len(old), 7)
            self.assertEqual(len(new), 5)
            dropped = {str(v).replace("\xa0", " ").strip() for v in old} - {
                str(v).replace("\xa0", " ").strip() for v in new
            }
            self.assertEqual(dropped, {"S1", "S2"})
        finally:
            measurement.close()
            annotation.close()

    def test_values_agree_cell_for_cell_when_keyed_by_chip_and_day(self) -> None:
        measurement = _load(MEASUREMENT)
        annotation = _load(ANNOTATION)
        try:
            mismatches: list[str] = []

            def norm(value: object) -> str:
                return str(value).replace("\xa0", " ").strip()

            # PAEP: key on chip label, never on column position.
            old_ws, new_ws = measurement[SHEET_PAEP], annotation[SHEET_PAEP]
            old_chips = {
                norm(old_ws.cell(row=2, column=c).value): c for c in range(2, 9)
            }
            new_chips = {
                norm(new_ws.cell(row=17, column=c).value): c for c in range(2, 7)
            }
            for chip, new_col in new_chips.items():
                old_col = old_chips[chip]
                for old_row, new_row in ((3, 18), (4, 19)):
                    a = old_ws.cell(row=old_row, column=old_col).value
                    b = new_ws.cell(row=new_row, column=new_col).value
                    if a != b:
                        mismatches.append(f"PAEP {chip}: {a!r} vs {b!r}")

            # Time-series sheets: key on (day label, column letter).
            for old_name, new_name, cols, new_rows in (
                (SHEET_IGFBP1, "IGFBP-1", range(2, 12), (27, 28, 29)),
                (SHEET_PRL, "PRL", range(2, 8), (22, 23, 24)),
            ):
                old_ws, new_ws = measurement[old_name], annotation[new_name]
                for offset, new_row in enumerate(new_rows):
                    old_row = 3 + offset
                    self.assertEqual(
                        norm(old_ws.cell(row=old_row, column=1).value),
                        norm(new_ws.cell(row=new_row, column=1).value),
                    )
                    for col in cols:
                        a = old_ws.cell(row=old_row, column=col).value
                        b = new_ws.cell(row=new_row, column=col).value
                        if a != b:
                            mismatches.append(
                                f"{old_name} r{old_row}c{col}: {a!r} vs {b!r}"
                            )
            self.assertEqual(mismatches, [], mismatches)
        finally:
            measurement.close()
            annotation.close()

    def test_a_positional_paep_comparison_would_misalign(self) -> None:
        """Pins WHY keying is mandatory, so nobody simplifies the test above
        into a positional loop. The annotation dropped two columns, so the
        surviving chips shifted left.
        """
        measurement = _load(MEASUREMENT)
        annotation = _load(ANNOTATION)
        try:
            mismatches = 0
            for col in range(2, 7):
                for old_row, new_row in ((3, 18), (4, 19)):
                    a = measurement[SHEET_PAEP].cell(row=old_row, column=col).value
                    b = annotation[SHEET_PAEP].cell(row=new_row, column=col).value
                    if a != b:
                        mismatches += 1
            self.assertEqual(mismatches, 8)
        finally:
            measurement.close()
            annotation.close()

    def test_the_annotation_workbook_states_no_detection_limit(self) -> None:
        """Detection limits stay repo prose, so detection_limit_pg_ml stays
        empty. If a future revision adds one, this test should fail and prompt
        populating the column.
        """
        annotation = _load(ANNOTATION)
        try:
            haystack = " ".join(
                str(cell.value).lower()
                for sheet in annotation.sheetnames
                for row in annotation[sheet].iter_rows()
                for cell in row
                if cell.value is not None
            )
            for token in ("detection limit", "límite de detección", "lloq", "lod"):
                self.assertNotIn(token, haystack)
        finally:
            annotation.close()


class OutletConditionsTableTest(unittest.TestCase):
    """The hand-curated annotation transcription. Always runs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.conditions = load_outlet_conditions()
        cls.by_id = {row["condition_id"]: row for row in cls.conditions}

    def test_the_expected_condition_records_exist(self) -> None:
        self.assertEqual(
            set(self.by_id),
            {
                "COND-E2-PRIMING",
                "COND-FULL-COCKTAIL",
                "COND-DAY0-BASELINE",
                "COND-DAY3-SAMPLE",
                "COND-DAY6-SAMPLE",
                "COND-COLLECTION-GEOMETRY",
            },
        )

    def test_the_protocol_intervals_partition_without_gap_or_overlap(self) -> None:
        e2 = self.by_id["COND-E2-PRIMING"]
        cocktail = self.by_id["COND-FULL-COCKTAIL"]
        self.assertEqual((e2["protocol_day_start"], e2["protocol_day_end"]), ("0", "2"))
        self.assertEqual(
            (cocktail["protocol_day_start"], cocktail["protocol_day_end"]), ("2", "6")
        )
        self.assertEqual(e2["protocol_day_end"], cocktail["protocol_day_start"])
        self.assertEqual(int(e2["duration_h"]), 48)
        self.assertEqual(int(cocktail["duration_h"]), 96)
        self.assertEqual(int(e2["duration_h"]), (2 - 0) * 24)
        self.assertEqual(int(cocktail["duration_h"]), (6 - 2) * 24)

    def test_the_hours_anchors_match_the_transform(self) -> None:
        self.assertEqual(
            int(self.by_id["COND-DAY3-SAMPLE"]["hours_after_cocktail_start"]),
            HOURS_AFTER_COCKTAIL_START_EXPECTED[3],
        )
        self.assertEqual(
            int(self.by_id["COND-DAY6-SAMPLE"]["hours_after_cocktail_start"]),
            HOURS_AFTER_COCKTAIL_START_EXPECTED[6],
        )
        self.assertEqual(
            int(self.by_id["COND-DAY3-SAMPLE"]["hours_after_e2_start"]), 72
        )
        self.assertEqual(
            int(self.by_id["COND-DAY6-SAMPLE"]["hours_after_e2_start"]), 144
        )

    def test_the_day0_window_disjunction_is_preserved_not_collapsed(self) -> None:
        """`medio de 48 h o 96 h` is a disjunction the collaborator did not
        resolve. Collapsing it to one number, or averaging to 72, would invent a
        collection window.
        """
        day0 = self.by_id["COND-DAY0-BASELINE"]
        self.assertEqual(day0["collection_duration"], "48|96")
        self.assertEqual(day0["collection_duration_state"], "disjunction_unresolved")
        self.assertNotIn(day0["collection_duration"], {"48", "96", "72"})
        self.assertEqual(day0["hours_after_e2_start"], "")
        self.assertEqual(day0["hours_after_cocktail_start"], "")
        self.assertEqual(day0["medium_state"], "expansion_medium")

    def test_the_treated_condition_names_all_four_agents(self) -> None:
        for condition_id in (
            "COND-FULL-COCKTAIL",
            "COND-DAY3-SAMPLE",
            "COND-DAY6-SAMPLE",
        ):
            agents = self.by_id[condition_id]["agent_concentrations"]
            for token in ("E2 10 nM", "MPA 1 uM", "cAMP 0.25 mM", "XAV939 10 uM"):
                self.assertIn(token, agents, condition_id)

    def test_the_annotation_shorthand_is_recorded_but_not_adopted(self) -> None:
        """The legend says `progesterona y estradiol` and omits cAMP/XAV939.

        It is preserved verbatim as provenance while the composition stays the
        reaffirmed MPA-based one. The conflict must be visible in the record.
        """
        cocktail = self.by_id["COND-FULL-COCKTAIL"]
        self.assertIn("progesterona y estradiol", cocktail["legend_verbatim"])
        self.assertIn("MPA", cocktail["agent_concentrations"])
        self.assertNotIn("progesterona", cocktail["agent_concentrations"])
        self.assertIn("shorthand", cocktail["note"])
        self.assertIn("UNRATIFIED", cocktail["note"])

    def test_the_collection_geometry_forbids_a_rate(self) -> None:
        geometry = self.by_id["COND-COLLECTION-GEOMETRY"]
        self.assertEqual(geometry["collected_volume"], COLLECTED_VOLUME)
        self.assertEqual(geometry["flow_rate"], FLOW_RATE)
        self.assertEqual(geometry["flow_rate_scope"], "paep_sheet_legend_only")
        self.assertEqual(int(geometry["technical_replicates_n"]), TECHNICAL_REPLICATE_N)
        self.assertIn("NO SECRETION RATE", geometry["note"])
        self.assertIn("33.3 h", geometry["note"])

    def test_every_record_declares_its_verification_dependency(self) -> None:
        """Every row transcribes a cell from a file the repository does not
        carry, so every row must name that dependency -- the mechanism that
        makes the privacy/auditability trade-off visible rather than assumed.
        """
        for row in self.conditions:
            self.assertEqual(
                row["verification_requires_source_file"],
                "data/secreción proteinas ADOC anotaciones.xlsx",
                row["condition_id"],
            )
            self.assertNotEqual(row["annotation_source_cells"].strip(), "")

    def test_measurement_rows_resolve_to_a_condition_record(self) -> None:
        rows = build_protein_table()
        for row in rows:
            self.assertIn(row["condition_interval_id"], self.by_id)

    def test_no_sampled_timepoint_claims_the_paep_sheet(self) -> None:
        """PAEP has no sampled day, so no timepoint row may declare it.

        The annotation workbook's PAEP sheet carries the same Día 0/2/3/6
        legends as the time-series sheets, which is exactly the trap: those
        cells are transcribed onto the two INTERVAL rows, and the two PAEP
        measurement rows are the protocol's treatment phases, not days
        (SOFIA-COMM-007). COND-DAY6-SAMPLE listed PAEP while its two sibling
        timepoint rows did not, and no PAEP measurement was ever assigned to
        it -- a contradiction inside one table that this pins shut.
        """
        for record in self.conditions:
            if record["interval_or_timepoint"] != "timepoint":
                continue
            sheets = [sheet.strip() for sheet in record["applies_to_sheets"].split(";")]
            self.assertNotIn("PAEP", sheets, record["condition_id"])
            self.assertEqual(sheets, ["IGFBP-1", "PRL"], record["condition_id"])

    def test_every_paep_row_resolves_to_a_protocol_interval_not_a_timepoint(
        self,
    ) -> None:
        paep = [row for row in build_protein_table() if row["source_sheet"] == "PAEP"]
        self.assertEqual(len(paep), 14)
        for row in paep:
            record = self.by_id[row["condition_interval_id"]]
            self.assertEqual(
                record["interval_or_timepoint"], "interval", row["source_cell"]
            )
            self.assertIn("SOFIA-COMM-007", record["evidence_ids"])


HOURS_AFTER_COCKTAIL_START_EXPECTED = {3: 24, 6: 96}


class DonorSourceCodePrivacyTest(unittest.TestCase):
    """The lab's raw cell-source codes must never enter a tracked artifact.

    Patterns are ASSEMBLED FROM FRAGMENTS so this file does not itself contain a
    code -- a self-path exclusion would silence the test while leaving the codes
    committed in it, which defeats the purpose. Word boundaries are mandatory:
    unanchored searches hit DOI substrings and PDF byte streams.
    """

    #: (prefix, suffix) halves of each code. Never spelled whole in source.
    _FRAGMENTS = (
        ("ma", "sce"),
        ("ca", "sh"),
        ("M", "77"),
        ("XS", "1"),
        ("UT", "1"),
        ("04", "_3"),
        ("05", "_2"),
        ("1.18", "-te"),
    )
    #: Deliberately NOT in the list: the chip labels S1/S2/S7.x/S10-2/S11-x/S12.
    #: Those are device identifiers, already committed throughout the repo, and
    #: are not the privacy-sensitive class.

    #: Fragments of the collection date at PAEP!I8, kept apart for the same
    #: reason as the code fragments above. Ruff would prefer the literal; the
    #: literal is exactly what must not appear in a tracked file.
    _DATE_PARTS = ("2026", "05", "04")

    TEXT_SUFFIXES = frozenset(
        {
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
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.patterns = [
            re.compile(r"\b" + re.escape(a + b) + r"\b", re.IGNORECASE)
            for a, b in cls._FRAGMENTS
        ]
        listing = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        cls.tracked = [
            path
            for path in listing
            if Path(path).suffix in cls.TEXT_SUFFIXES
            and not path.startswith("data/")
            and (ROOT / path).is_file()
        ]

    def test_there_are_tracked_files_to_scan(self) -> None:
        self.assertGreater(len(self.tracked), 100)

    def test_no_raw_cell_source_code_appears_in_a_tracked_artifact(self) -> None:
        hits: list[str] = []
        for rel in self.tracked:
            try:
                text = (ROOT / rel).read_text(encoding="utf-8")
            except UnicodeDecodeError:  # pragma: no cover - defensive
                continue
            for index, line in enumerate(text.splitlines(), start=1):
                for pattern in self.patterns:
                    if pattern.search(line):
                        hits.append(f"{rel}:{index}")
        self.assertEqual(
            hits,
            [],
            "the lab's own cell-source codes must never be committed; use the "
            "opaque labels in config/adoc_chip_donor_provenance.tsv instead:\n"
            + "\n".join(hits),
        )

    def test_the_annotation_workbook_is_not_tracked(self) -> None:
        listing = subprocess.run(
            ["git", "ls-files", "data/"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertNotIn("anotaciones", listing)

    def test_the_annotation_workbook_is_not_in_the_external_bundle(self) -> None:
        script = (
            ROOT / "src" / "scripts" / "make_chatgpt_results_bundle.sh"
        ).read_text(encoding="utf-8")
        self.assertNotIn("anotaciones", script)

    def test_donor_labels_are_opaque_and_registered(self) -> None:
        path = ROOT / "config" / "adoc_chip_donor_provenance.tsv"
        with path.open(newline="", encoding="utf-8") as handle:
            records = list(csv.DictReader(handle, delimiter="\t"))
        labels = {
            record[field]
            for record in records
            for field in ("epithelial_source_group", "stromal_source_group")
            if record[field]
        }
        self.assertTrue(labels)
        for label in labels:
            self.assertRegex(label, r"^SRC-(EPI|STR)-[A-Z]$")

    def test_no_collection_date_is_committed(self) -> None:
        """A single-day date plus tissue plus a named institution is a
        quasi-identifier, and it adds nothing over the relational day anchors.

        The date is ASSEMBLED here for the same reason the code patterns are: a
        guard that spells its own needle matches itself the moment it is
        tracked, which is precisely how the condition-label guard shipped red.
        """
        needle = "-".join(self._DATE_PARTS)
        for rel in self.tracked:
            try:
                text = (ROOT / rel).read_text(encoding="utf-8")
            except UnicodeDecodeError:  # pragma: no cover - defensive
                continue
            self.assertNotIn(needle, text, rel)


class ManifestRegistrationTest(unittest.TestCase):
    """The annotation workbook is declared even though it is not committed."""

    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "config" / "data_manifest.tsv").open(
            newline="", encoding="utf-8"
        ) as handle:
            cls.manifest = list(csv.DictReader(handle, delimiter="\t"))

    def test_the_annotation_workbook_is_manifested_with_its_hash(self) -> None:
        row = next(
            r for r in self.manifest if r["relative_path"].endswith("anotaciones.xlsx")
        )
        self.assertEqual(int(row["size_bytes"]), ANNOTATION_SIZE)
        self.assertEqual(row["sha256"], ANNOTATION_SHA256)

    def test_every_file_in_data_is_manifested(self) -> None:
        """The reverse direction the manifest validator entirely lacks: it walks
        manifest rows to the filesystem and never back, so an unlisted source
        file in data/ is silently invisible to every gate.
        """
        declared = {row["relative_path"] for row in self.manifest}
        allowed_unmanifested: set[str] = set()
        on_disk = {
            f"data/{path.name}" for path in (ROOT / "data").iterdir() if path.is_file()
        }
        self.assertEqual(on_disk - declared - allowed_unmanifested, set())

    def test_the_workbook_is_no_longer_declared_unavailable(self) -> None:
        import yaml

        contract = yaml.safe_load(
            (ROOT / "config" / "source_contract.yaml").read_text(encoding="utf-8")
        )
        self.assertNotIn("declared_but_unavailable_artifacts", contract)
        paths = {entry["relative_path"] for entry in contract["source_artifacts"]}
        self.assertIn("data/secreción proteinas ADOC anotaciones.xlsx", paths)
        history = contract["previously_declared_unavailable_artifacts"][0]
        self.assertEqual(history["availability"], "received_2026_07_29")
        # The audit trail must survive: these five were file-less when written.
        self.assertEqual(len(history["evidence_records_created_while_file_less"]), 5)


if __name__ == "__main__":
    unittest.main()
