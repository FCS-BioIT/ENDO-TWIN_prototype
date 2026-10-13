"""Contract tests for the ADOC secreted-protein table transformation.

These run the real transformation against the real, immutable workbook
(``data/proteinas secretadas ADOC.xlsx``) rather than a synthetic fixture --
the whole point of this module is to encode exactly what that specific file
contains, so a synthetic stand-in would not exercise the discrepancies it is
meant to catch.
"""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.data.secreted_proteins import (
    ALWAYS_EMPTY_COLUMNS,
    HOURS_AFTER_COCKTAIL_START,
    PHASE_DAY0_BASELINE,
    build_protein_table,
    load_contract,
    load_outlet_conditions,
    validate_secreted_protein_table,
)

#: Every workbook cell storing a literal 0. Asserted as an EXACT set, not a
#: count, so silently re-coding one cell fails rather than passing a threshold.
ZERO_CELLS = frozenset(
    {
        ("IGFBP-1", c)
        for c in ("B3", "D3", "E3", "F3", "H3", "C4", "D4", "E5", "F5", "J5", "K5")
    }
    | {("PRL ", c) for c in ("C3", "E3", "F3", "G3", "C4", "D4", "E4", "G4")}
)

#: Workbook cells that carry no value at all -- distinct from a stored zero.
ABSENT_CELLS = frozenset({("PAEP", c) for c in ("C3", "D3", "C4", "D4")})


def _find(rows: list[dict], sheet: str, cell: str) -> dict:
    for row in rows:
        if row["source_sheet"] == sheet and row["source_cell"] == cell:
            return row
    raise AssertionError(f"no row for {sheet}!{cell}")


class BuildProteinTableTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_protein_table()

    def test_exact_row_count(self) -> None:
        # PAEP: 2 condition rows x 7 chip columns = 14.
        # IGFBP-1: 3 day rows x 10 columns = 30.
        # PRL: 3 day rows x 6 columns = 18.
        self.assertEqual(len(self.rows), 62)

    def test_paep_missing_chips_have_no_numeric_value(self) -> None:
        for cell in ("C3", "D3", "C4", "D4"):
            row = _find(self.rows, "PAEP", cell)
            self.assertEqual(row["measurement_state"], "missing")
            self.assertEqual(row["raw_value"], "")
            self.assertEqual(row["reported_concentration_pg_ml"], "")
            self.assertEqual(row["quality_tier"], "exploratory")

    def test_known_igfbp1_cell_round_trips(self) -> None:
        row = _find(self.rows, "IGFBP-1", "G5")
        self.assertEqual(row["protein"], "IGFBP-1")
        self.assertEqual(row["outlet"], "bottom")
        self.assertEqual(row["source_time_label"], "Day 7")
        self.assertEqual(row["resolved_protocol_day"], 6)
        self.assertIn("labelling error", row["time_resolution_note"])
        self.assertIn("SOFIA-COMM-003", row["time_resolution_note"])
        self.assertAlmostEqual(float(row["raw_value"]), 8118.142)

    def test_known_prl_cell_is_confirmed_bottom(self) -> None:
        """The whole PRL sheet is the BOTTOM outlet (SOFIA-COMM-006).

        Column B was previously filed as apical on a context-document claim that
        turned out to be wrong. The two basis columns stay separate: the outlet
        assignment is now confirmed at SHEET level, while what an outlet MEANS
        is still SOFIA-COMM-003's separate confirmation.
        """
        row = _find(self.rows, "PRL ", "B3")
        self.assertEqual(row["protein"], "PRL")
        self.assertEqual(row["outlet"], "bottom")
        self.assertEqual(row["compartment"], "stromal")
        self.assertEqual(
            row["outlet_assignment_basis"], "sheet_level_collaborator_confirmed"
        )
        self.assertEqual(
            row["compartment_semantics_basis"],
            "collaborator_confirmed_top_apical_bottom_basal",
        )

    def test_paep_sheet_outlet_is_a_sheet_level_assumption(self) -> None:
        row = _find(self.rows, "PAEP", "B3")
        self.assertEqual(
            row["outlet_assignment_basis"], "sheet_level_context_document_unverified"
        )

    def test_igfbp1_outlet_split_is_a_workbook_fact(self) -> None:
        row = _find(self.rows, "IGFBP-1", "G5")
        self.assertEqual(row["outlet_assignment_basis"], "workbook_merged_header")

    def test_every_row_records_confirmed_compartment_semantics(self) -> None:
        for row in self.rows:
            self.assertEqual(
                row["compartment_semantics_basis"],
                "collaborator_confirmed_top_apical_bottom_basal",
            )

    def test_always_empty_columns_are_never_populated(self) -> None:
        for row in self.rows:
            for field_name in ALWAYS_EMPTY_COLUMNS:
                self.assertEqual(
                    row[field_name],
                    "",
                    f"{field_name!r} must stay empty but was {row[field_name]!r}",
                )

    def test_igfbp1_compartment_is_not_externally_asserted(self) -> None:
        row = _find(self.rows, "IGFBP-1", "G5")
        asserted = row["externally_asserted_fields"].split("|")
        self.assertNotIn("compartment", asserted)
        self.assertNotIn("outlet", asserted)

    def test_prl_compartment_is_no_longer_externally_asserted(self) -> None:
        """Inverted by SOFIA-COMM-006: PRL's outlet is confirmed, so it is no
        longer asserted from the context document alone. PAEP still is.
        """
        row = _find(self.rows, "PRL ", "B3")
        self.assertEqual(row["externally_asserted_fields"], "")
        paep = _find(self.rows, "PAEP", "B3")
        self.assertIn("compartment", paep["externally_asserted_fields"].split("|"))

    def test_units_are_collaborator_confirmed_not_a_document_assumption(self) -> None:
        """pg/mL is confirmed (SOFIA-COMM-001), so `unit` is no longer listed as
        an unsupported external assertion and the old basis term is retired.
        """
        for row in self.rows:
            self.assertEqual(row["unit"], "pg/mL")
            self.assertEqual(row["unit_basis"], "collaborator_confirmed")
            self.assertNotIn("unit", row["externally_asserted_fields"].split("|"))

    def test_retired_unit_basis_term_appears_nowhere(self) -> None:
        stale = "external_assumption_context_document"
        for path in (
            ROOT / "input_tables" / "adoc_secreted_proteins.tsv",
            ROOT / "config" / "secreted_protein_contract.yaml",
            ROOT / "src" / "dt_adoc" / "data" / "secreted_proteins.py",
        ):
            self.assertNotIn(stale, path.read_text(encoding="utf-8"), str(path))

    def test_paep_exploratory_quality_tier_is_no_longer_externally_asserted(
        self,
    ) -> None:
        """Inverted by SOFIA-COMM-007, exactly as SOFIA-COMM-006 inverted PRL's
        outlet: the collaborator confirmed on 2026-09-18 that S1 and S2 were
        left blank because she did not trust those older chips, so
        ``quality_tier`` has a named confirming source and is no longer an
        assertion carried by the context document alone. Compartment and outlet
        still are -- the PAEP sheet's outlet remains the one unconfirmed
        assignment -- so this must not be read as PAEP becoming confirmed.
        """
        trusted = _find(self.rows, "PAEP", "B3")
        distrusted = _find(self.rows, "PAEP", "C3")
        for row in (trusted, distrusted):
            self.assertEqual(row["externally_asserted_fields"], "compartment|outlet")
        self.assertIn("SOFIA-COMM-007", distrusted["exclusion_reason"])
        self.assertEqual(trusted["exclusion_reason"], "")

    def test_paep_rows_have_no_resolved_day_but_have_condition(self) -> None:
        for row in self.rows:
            if row["source_sheet"] != "PAEP":
                continue
            self.assertEqual(row["resolved_protocol_day"], "")
            # The workbook's own label, preserved verbatim and never rewritten
            # even though it names P4 for MPA and omits cAMP.
            self.assertIn(row["condition"], {"HT (E2 only)", "HT (E2+P4+XAV939)"})
            self.assertIn(
                row["condition_normalized"], {"e2_only_48h", "e2_mpa_camp_xav939_96h"}
            )
            # No PAEP row has a sampling instant, so no elapsed-hours anchor.
            self.assertEqual(row["hours_after_cocktail_start"], "")

    def test_top_and_bottom_never_share_a_series_id(self) -> None:
        by_series: dict[str, set[str]] = {}
        for row in self.rows:
            by_series.setdefault(row["series_id"], set()).add(row["outlet"])
        for series_id, outlets in by_series.items():
            self.assertEqual(len(outlets), 1, f"{series_id} mixes outlets {outlets}")

    def test_generated_table_validates_cleanly(self) -> None:
        report = validate_secreted_protein_table(self.rows)
        self.assertEqual(report.errors, [], report.errors)
        self.assertEqual(report.status, "structurally_valid")

    def test_validation_catches_corrupted_missing_state_with_value(self) -> None:
        corrupted = [dict(row) for row in self.rows]
        corrupted[0]["measurement_state"] = "missing"
        corrupted[0]["raw_value"] = "123.0"
        report = validate_secreted_protein_table(corrupted)
        self.assertEqual(report.status, "structurally_invalid")
        self.assertTrue(
            any(
                "measurement_state=missing but raw_value is set" in e
                for e in report.errors
            )
        )

    def test_validation_catches_corrupted_always_empty_column(self) -> None:
        corrupted = [dict(row) for row in self.rows]
        corrupted[0]["donor_id"] = "donor-1"
        report = validate_secreted_protein_table(corrupted)
        self.assertEqual(report.status, "structurally_invalid")
        self.assertTrue(any("must stay empty" in e for e in report.errors))

    def test_known_soft_spot_warnings_fire(self) -> None:
        report = validate_secreted_protein_table(self.rows)
        self.assertEqual(report.status, "structurally_valid")
        keys = [w.split("]", 1)[0].lstrip("[") for w in report.warnings]
        self.assertEqual(
            keys,
            [
                "prl_column_count_exceeds_named_chip_families",
                "paep_sheet_outlet_unverified",
                "chip_donor_independence_partially_unknown",
                "igfbp1_prl_column_to_chip_mapping_lost",
                "igfbp1_day6_paired_zero_columns_possible_dropout",
            ],
        )

    def test_retired_warnings_no_longer_fire(self) -> None:
        """Units and zero semantics were confirmed on 2026-07-29, so the two
        warnings that said they were unresolvable must be gone -- not merely
        renamed in the contract while the prose survives.
        """
        report = validate_secreted_protein_table(self.rows)
        joined = " ".join(report.warnings)
        self.assertNotIn("externally asserted", joined)
        self.assertNotIn("cannot be distinguished from below-detection", joined)
        declared = load_contract()["warning_conditions"]
        self.assertNotIn("unit_externally_asserted", declared)
        self.assertNotIn("zero_values_indistinguishable_from_below_detection", declared)

    def test_every_emitted_warning_key_is_declared_in_the_contract(self) -> None:
        """Binds the contract's warning_conditions list to the warnings the
        validator actually emits. Without this the list is inert prose that can
        be renamed without anything failing.
        """
        report = validate_secreted_protein_table(self.rows)
        declared = load_contract()["warning_conditions"]
        emitted = {w.split("]", 1)[0].lstrip("[") for w in report.warnings}
        self.assertEqual(emitted, set(declared))


class ZeroSemanticsTest(unittest.TestCase):
    """A stored 0 is a MEASURED non-detect (SOFIA-COMM-002).

    Absorbance was read and interpolation against the standard curve returned
    no detectable secretion. It is not NA, not blank, and not a censored
    below-detection value.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_protein_table()

    def test_every_stored_zero_is_a_measured_non_detect(self) -> None:
        found = set()
        for row in self.rows:
            if row["raw_value"] == "" or float(row["raw_value"]) != 0.0:
                continue
            key = (row["source_sheet"], row["source_cell"])
            found.add(key)
            self.assertEqual(row["measurement_state"], "no_detectable_secretion", key)
            self.assertEqual(row["raw_value"], 0, key)
            self.assertEqual(row["reported_concentration_pg_ml"], 0, key)
            self.assertIn("no detectable secretion", row["resolution_note"])
        self.assertEqual(found, set(ZERO_CELLS))

    def test_no_zero_is_recorded_as_missing_or_censored(self) -> None:
        forbidden = {"missing", "below_detection", "excluded", "blank_control"}
        for row in self.rows:
            if (row["source_sheet"], row["source_cell"]) in ZERO_CELLS:
                self.assertNotIn(row["measurement_state"], forbidden)

    def test_absent_cells_stay_missing_and_are_disjoint_from_zeros(self) -> None:
        """Guards both directions of the confusion at once: a cell with no
        value must never become a zero, and a zero must never become missing.
        """
        missing = {
            (row["source_sheet"], row["source_cell"])
            for row in self.rows
            if row["measurement_state"] == "missing"
        }
        self.assertEqual(missing, set(ABSENT_CELLS))
        self.assertEqual(missing & set(ZERO_CELLS), set())

    def test_below_detection_is_unused_by_this_dataset(self) -> None:
        """The term stays in the vocabulary for future assays, but nothing here
        may use it: no value in this workbook is a censored measurement.
        """
        states = {row["measurement_state"] for row in self.rows}
        self.assertNotIn("below_detection", states)

    def test_validation_rejects_a_zero_recoded_as_missing(self) -> None:
        corrupted = [dict(row) for row in self.rows]
        target = next(
            row
            for row in corrupted
            if (row["source_sheet"], row["source_cell"]) in ZERO_CELLS
        )
        target["measurement_state"] = "missing"
        target["raw_value"] = ""
        target["reported_concentration_pg_ml"] = ""
        report = validate_secreted_protein_table(corrupted)
        self.assertEqual(report.status, "structurally_invalid")

    def test_validation_rejects_a_zero_recoded_as_plain_observed(self) -> None:
        corrupted = [dict(row) for row in self.rows]
        target = next(
            row
            for row in corrupted
            if (row["source_sheet"], row["source_cell"]) in ZERO_CELLS
        )
        target["measurement_state"] = "observed"
        report = validate_secreted_protein_table(corrupted)
        self.assertEqual(report.status, "structurally_invalid")
        self.assertTrue(
            any("measured non-detect" in e for e in report.errors), report.errors
        )

    def test_validation_rejects_a_non_zero_marked_as_a_non_detect(self) -> None:
        corrupted = [dict(row) for row in self.rows]
        target = _find(corrupted, "IGFBP-1", "G5")
        target["measurement_state"] = "no_detectable_secretion"
        report = validate_secreted_protein_table(corrupted)
        self.assertEqual(report.status, "structurally_invalid")
        self.assertTrue(any("not zero" in e for e in report.errors), report.errors)


class ProtocolAnchoringTest(unittest.TestCase):
    """Day anchoring and condition identity confirmed 2026-07-29."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_protein_table()
        cls.contract = load_contract()

    def test_every_igfbp1_day7_row_preserves_both_labels(self) -> None:
        rows = [
            row
            for row in self.rows
            if row["source_sheet"] == "IGFBP-1" and row["source_row"] == 5
        ]
        self.assertEqual(len(rows), 10)
        for row in rows:
            self.assertEqual(row["source_time_label"], "Day 7")
            self.assertEqual(row["resolved_protocol_day"], 6)
            self.assertNotEqual(row["time_resolution_note"], "")

    def test_prl_day6_rows_need_no_resolution_note(self) -> None:
        rows = [
            row
            for row in self.rows
            if row["source_sheet"] == "PRL " and row["source_row"] == 5
        ]
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row["source_time_label"], "Day 6")
            self.assertEqual(row["resolved_protocol_day"], 6)
            self.assertEqual(row["time_resolution_note"], "")

    def test_no_row_reports_protocol_day_seven(self) -> None:
        for row in self.rows:
            self.assertNotEqual(str(row["resolved_protocol_day"]), "7")

    def test_hours_after_cocktail_start_matches_the_contract_rule(self) -> None:
        self.assertEqual(HOURS_AFTER_COCKTAIL_START, {3: 24, 6: 96})
        for row in self.rows:
            day = row["resolved_protocol_day"]
            hours = row["hours_after_cocktail_start"]
            if row["source_sheet"] == "PAEP" or day == 0:
                # Day 0 precedes the cocktail and the collection window is
                # unknown, so neither 0 nor -48 is defensible.
                self.assertEqual(hours, "")
            else:
                self.assertEqual(hours, HOURS_AFTER_COCKTAIL_START[day])

    def test_day0_rows_declare_a_pre_hormone_expansion_medium_baseline(self) -> None:
        """The annotation workbook records day 0 as expansion medium, so the
        earlier "E2 exposure unverified" phrasing is retired. The accumulation
        window stays a disjunction and is therefore never given an hours value.
        """
        rows = [row for row in self.rows if row["resolved_protocol_day"] == 0]
        self.assertEqual(len(rows), 16)
        for row in rows:
            self.assertEqual(
                row["protocol_phase"], "day0_baseline_expansion_medium_pre_hormone"
            )
            self.assertEqual(row["condition_normalized"], "pre_cocktail_baseline")
            self.assertEqual(row["condition_interval_id"], "COND-DAY0-BASELINE")
            self.assertEqual(row["hours_after_cocktail_start"], "")
            self.assertEqual(row["hours_after_e2_start"], "")
            self.assertIn("expansion medium", row["condition_resolution_note"])

    def test_all_eighteen_prl_rows_are_bottom_stromal(self) -> None:
        """PRL was measured from the BOTTOM outlet (SOFIA-COMM-006).

        Counted per day as well as in total, so a partial regression that leaves
        one column apical cannot pass.
        """
        prl = [row for row in self.rows if row["source_sheet"] == "PRL "]
        self.assertEqual(len(prl), 18)
        self.assertEqual({row["outlet"] for row in prl}, {"bottom"})
        self.assertEqual({row["compartment"] for row in prl}, {"stromal"})
        for day in (0, 3, 6):
            per_day = [row for row in prl if row["resolved_protocol_day"] == day]
            self.assertEqual(len(per_day), 6, f"day {day}")
        self.assertEqual(
            {row["series_id"] for row in prl},
            {f"PRL_BOTTOM_{n}" for n in range(1, 7)},
        )

    def test_no_row_anywhere_reports_an_apical_prl_measurement(self) -> None:
        """Checks the freshly built rows AND the committed table, so a forgotten
        `pixi run build-protein-table` is caught rather than hidden.
        """
        for row in self.rows:
            if row["protein"] == "PRL":
                self.assertNotEqual(row["outlet"], "top")
                self.assertNotEqual(row["compartment"], "epithelial")
        path = ROOT / "input_tables" / "adoc_secreted_proteins.tsv"
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["protein"] == "PRL":
                    self.assertEqual(row["outlet"], "bottom")
                    self.assertEqual(row["compartment"], "stromal")

    def test_every_prl_row_records_the_confirmed_bottom_outlet_basis(self) -> None:
        """And the promotion is not over-applied: PAEP's outlet is still
        unconfirmed and IGFBP-1's is still a workbook fact.
        """
        prl = [row for row in self.rows if row["source_sheet"] == "PRL "]
        self.assertEqual(
            {row["outlet_assignment_basis"] for row in prl},
            {"sheet_level_collaborator_confirmed"},
        )
        self.assertIn(
            "sheet_level_collaborator_confirmed",
            self.contract["controlled_vocabularies"]["outlet_assignment_basis"],
        )
        self.assertEqual(
            _find(self.rows, "PAEP", "B3")["outlet_assignment_basis"],
            "sheet_level_context_document_unverified",
        )
        self.assertEqual(
            _find(self.rows, "IGFBP-1", "G5")["outlet_assignment_basis"],
            "workbook_merged_header",
        )

    def test_the_retired_prl_outlet_terms_are_no_longer_valid_values(self) -> None:
        """Values, not prose: the contract names both retired terms in comments
        so a reader grepping for them lands on the explanation.
        """
        stale_basis = "column_position_context_document_unverified"
        self.assertNotIn(
            stale_basis,
            self.contract["controlled_vocabularies"]["outlet_assignment_basis"],
        )
        stale_key = "prl_outlet_column_positions_unverified"
        self.assertNotIn(stale_key, self.contract["warning_conditions"])
        report = validate_secreted_protein_table(self.rows)
        self.assertNotIn(stale_key, " ".join(report.warnings))
        for row in self.rows:
            self.assertNotEqual(row["outlet_assignment_basis"], stale_basis)
            self.assertNotIn(stale_key, row["uncertainty_flags"])

    def test_one_outlet_does_not_license_cross_column_pairing_or_a_larger_n(
        self,
    ) -> None:
        """The critical guard on this correction.

        Six columns of one condition in one compartment look exactly like six
        replicates. They are not: only 3 chip families are named for them, so
        the plausible unit count is at most 3 and possibly fewer. Confirming the
        outlet resolves the compartment, never the replicate structure.
        """
        contract = self.contract["biological_independence_contract"]
        self.assertEqual(contract["max_independent_units_prl"], "not_determinable")
        self.assertIn("PRL ", contract["column_to_chip_mapping_lost"])
        self.assertEqual(
            contract["series_id_semantics"], "positional_column_index_not_chip"
        )
        for claim in (
            "n_equals_number_of_columns",
            "within_column_pairing_across_day_rows_for_igfbp1_or_prl",
            "column_assignment_resolved_from_a_partial_chip_set",
            "prl_column_count_implies_independent_unit_count",
            "cross_column_pairing_within_a_day_for_prl",
        ):
            self.assertIn(claim, contract["forbidden_claims"], claim)
        for row in self.rows:
            if row["source_sheet"] != "PRL ":
                continue
            self.assertEqual(row["chip_id"], "")
            self.assertEqual(row["donor_group_id"], "")
            self.assertEqual(row["donor_matching_state"], "lost_column_assignment")
            self.assertIn("column_to_chip_mapping_lost", row["uncertainty_flags"])
            self.assertIn("not_paired_across_day_rows", row["uncertainty_flags"])

    def test_the_retired_day0_phase_term_is_no_longer_a_valid_value(self) -> None:
        """Checks VALUES, not prose.

        The contract deliberately names the retired term in a comment so a
        reader grepping for it lands on the explanation. What must be gone is
        every USE of it: as a row value, as a vocabulary entry, or as a live
        constant.
        """
        stale = "day0_baseline_e2_exposure_unverified"
        self.assertNotIn(
            stale, self.contract["controlled_vocabularies"]["protocol_phase"]
        )
        self.assertNotEqual(PHASE_DAY0_BASELINE, stale)
        for row in self.rows:
            self.assertNotEqual(row["protocol_phase"], stale)
        # And no other artifact may still carry it as a field value.
        for rel in (
            "input_tables/adoc_secreted_proteins.tsv",
            "config/adoc_outlet_conditions.tsv",
        ):
            self.assertNotIn(stale, (ROOT / rel).read_text(encoding="utf-8"), rel)

    def test_the_corrected_condition_names_all_four_agents(self) -> None:
        row = _find(self.rows, "PAEP", "B4")
        self.assertEqual(row["condition_normalized"], "e2_mpa_camp_xav939_96h")
        note = row["condition_resolution_note"]
        for token in ("MPA", "cAMP", "XAV939", "E2"):
            self.assertIn(token, note)
        self.assertIn("not", note)

    def test_the_verbatim_workbook_label_is_still_recoverable(self) -> None:
        """A guard that permitted deleting the source label would destroy
        provenance. The nbsp-bearing original must survive in source_label.
        """
        row = _find(self.rows, "PAEP", "B4")
        self.assertEqual(row["source_label"], "HT\xa0(E2+P4+XAV939)")


class PaepPhaseSemanticsTest(unittest.TestCase):
    """PAEP's two rows are treatment phases, not sampled days.

    Collaborator-confirmed 2026-09-18 (SOFIA-COMM-007): "HT" is hormone
    treatment, the E2-only row is the proliferative-phase arm and the
    full-hormone row the secretory-phase arm. PAEP is therefore outside the
    day-3 representation problem entirely -- that one is IGFBP-1 and PRL only.

    The invariant asserted here is the conservative one: no sampled day is
    assignable on current evidence, and the workbook's day legends alone may
    not supply one. SOFIA-COMM-007 says what the rows ARE; it does not
    establish that a sampling instant could never be recovered, so no test here
    asserts that, and a future confirmation of PAEP sampling timing would be
    new evidence rather than a violation.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_protein_table()
        cls.paep = [row for row in cls.rows if row["source_sheet"] == "PAEP"]

    def test_every_paep_row_records_the_confirmed_phase_semantics(self) -> None:
        self.assertEqual(len(self.paep), 14)
        for row in self.paep:
            note = row["condition_resolution_note"]
            self.assertIn("SOFIA-COMM-007", note, row["source_cell"])
            self.assertIn("proliferative-phase", note, row["source_cell"])
            self.assertIn("secretory-phase", note, row["source_cell"])

    def test_the_full_cocktail_rows_keep_the_condition_correction_as_well(
        self,
    ) -> None:
        """The phase note is added to the P4/cAMP correction, never instead of
        it: the workbook's condition label is still wrong twice over.
        """
        for row in self.paep:
            if row["condition_normalized"] != "e2_mpa_camp_xav939_96h":
                continue
            note = row["condition_resolution_note"]
            for token in ("MPA", "cAMP", "XAV939", "SOFIA-COMM-004"):
                self.assertIn(token, note, row["source_cell"])

    def test_the_collaborator_rationale_is_recorded_as_rationale_not_evidence(
        self,
    ) -> None:
        """The same message says receptivity, and so PAEP secretion, peaks in
        the secretory phase. OM-001 is the feasibility gate that tests exactly
        that direction, so citing the expectation as support would be circular.
        The row must say so, and the evidence register must not file the record
        under a calibration role.
        """
        for row in self.paep:
            self.assertIn("circular", row["condition_resolution_note"])
        with (ROOT / "config/evidence_roles.yaml").open(encoding="utf-8") as handle:
            roles = yaml.safe_load(handle)
        self.assertIn("SOFIA-COMM-007", roles["construction"]["evidence_ids"])
        self.assertNotIn("SOFIA-COMM-007", roles["calibration"]["evidence_ids"])
        self.assertNotIn("SOFIA-COMM-007", roles["validation"]["evidence_ids"])

    def test_the_time_axis_statement_lives_in_the_time_typed_column_only(
        self,
    ) -> None:
        """One fact, one home. It used to sit in the general-purpose
        ``resolution_note``; duplicating it into both columns is how a
        correction reaches one copy and not the other.
        """
        for row in self.paep:
            note = row["time_resolution_note"]
            self.assertIn("not time points", note)
            self.assertIn("SOFIA-COMM-007", note)
            self.assertEqual(row["resolution_note"], "")
            self.assertEqual(row["resolved_protocol_day"], "")
            self.assertEqual(row["hours_after_cocktail_start"], "")
            self.assertEqual(row["hours_after_e2_start"], "")

    def test_the_time_claim_is_about_the_evidence_not_about_impossibility(
        self,
    ) -> None:
        """The emitted note must state the conservative invariant.

        "No sampled day is assignable on current evidence" is what
        `SOFIA-COMM-007` supports. "No sampling instant can ever exist" is not,
        and a row that says so would overclaim in the artifact a reader
        actually consumes.
        """
        for row in self.paep:
            note = row["time_resolution_note"]
            self.assertIn("ON CURRENT EVIDENCE", note)
            self.assertIn("would be new evidence", note)
            self.assertNotIn("permanently", note)

    def test_validation_rejects_a_paep_row_pinned_to_a_sampled_day(self) -> None:
        corrupted = [dict(row) for row in self.rows]
        target = next(row for row in corrupted if row["source_sheet"] == "PAEP")
        target["condition_interval_id"] = "COND-DAY6-SAMPLE"
        report = validate_secreted_protein_table(corrupted)
        self.assertTrue(
            any("protocol phases" in error for error in report.errors), report.errors
        )

    def test_validation_rejects_a_timepoint_that_claims_the_paep_sheet(self) -> None:
        """The defect this closes: COND-DAY6-SAMPLE declared
        ``applies_to_sheets=PAEP;IGFBP-1;PRL`` while no PAEP measurement row
        resolved to it, and nothing failed.
        """
        conditions = load_outlet_conditions()
        for record in conditions:
            if record["condition_id"] == "COND-DAY6-SAMPLE":
                record["applies_to_sheets"] = "PAEP;IGFBP-1;PRL "
        with mock.patch(
            "dt_adoc.data.secreted_proteins.load_outlet_conditions",
            return_value=conditions,
        ):
            report = validate_secreted_protein_table(self.rows)
        self.assertTrue(
            any(
                "must not declare" in error and "COND-DAY6-SAMPLE" in error
                for error in report.errors
            ),
            report.errors,
        )


class DonorProvenanceTest(unittest.TestCase):
    """Chips are not independent biological replicates (SOFIA-COMM-005).

    Donor IDENTITY is unknown; only pairwise RELATIONS are partly known. These
    tests pin the known relations exactly so no additional one can be inferred,
    and pin the lost mappings so their loss is recorded rather than implied by
    absence.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_protein_table()
        cls.contract = load_contract()
        text = (ROOT / "config" / "adoc_chip_donor_provenance.tsv").read_text(
            encoding="utf-8"
        )
        lines = text.strip().split("\n")
        header = lines[0].split("\t")
        cls.provenance = [dict(zip(header, ln.split("\t"))) for ln in lines[1:]]

    def test_no_chip_is_ever_an_independent_biological_unit(self) -> None:
        contract = self.contract["biological_independence_contract"]
        self.assertIs(contract["chip_is_independent_biological_replicate"], False)
        for record in self.provenance:
            self.assertEqual(record["independent_biological_unit"], "no")

    def test_donor_relations_are_exactly_the_confirmed_facts(self) -> None:
        """S10-2's epithelial sharing was added from the annotation workbook.

        Its relation term is deliberately narrower than S7.1/S7.2's: only the
        epithelial source is annotated, so `shares_patient_sources` would
        over-claim.
        """
        known = {
            (r["subject_a"], r["subject_b"], r["relation"])
            for r in self.provenance
            if r["record_kind"] == "relation" and r["knowledge_state"] == "known"
        }
        self.assertEqual(
            known,
            {
                ("S7.1", "S7.2", "shares_patient_sources"),
                ("S10-2", "S7.1;S7.2", "shares_epithelial_cell_source"),
            },
        )

    def test_the_s11_relation_is_recorded_as_in_tension_not_flipped(self) -> None:
        """The annotation names one source pairing for the S11 family without a
        per-chip split, which neither confirms nor refutes the confirmed
        "different patients" statement. It must be escalated, not silently
        reversed -- "the workbook wins" presupposes an unambiguous conflict.
        """
        record = next(r for r in self.provenance if r["record_id"] == "REL-002")
        self.assertEqual(record["relation"], "distinct_patients")
        self.assertEqual(
            record["knowledge_state"], "known_but_in_tension_with_annotation"
        )
        self.assertIn("NOT RESOLVED", record["note"])

    def test_chips_without_a_confirmed_relation_are_explicit_unknowns(self) -> None:
        """Omission is how an unknown quietly becomes an assumption, so every
        chip with no confirmed relation carries an explicit `unknown` record.
        """
        unknown = {
            r["subject_a"]
            for r in self.provenance
            if r["record_kind"] == "relation" and r["knowledge_state"] == "unknown"
        }
        # S10-2 left this set when the annotation named its epithelial source.
        # S1/S2 stay: the annotation names a source pairing for the family
        # without saying which chip is which, which is not a relation.
        self.assertEqual(unknown, {"S1", "S2", "epithelial"})

    def test_every_chip_id_in_the_table_is_recorded(self) -> None:
        table_chips = {row["chip_id"] for row in self.rows if row["chip_id"]}
        recorded = {
            r["subject_a"] for r in self.provenance if r["record_kind"] == "chip"
        }
        self.assertEqual(table_chips, recorded)

    def test_the_nbsp_chip_label_reconciliation_is_recorded_not_silent(self) -> None:
        """The workbook stores S11 + U+00A0 + 2; the collaborator writes S11-2.
        chip_id is deliberately NOT renamed (OM-001 joins on the normalized
        form), so the reconciliation must be visible instead.
        """
        record = next(r for r in self.provenance if r["record_id"] == "CHIP-007")
        self.assertEqual(record["chip_label_verbatim"], "S11\xa02")
        self.assertEqual(record["collaborator_chip_label"], "S11-2")
        self.assertEqual(
            record["label_reconciliation"], "separator_differs_nbsp_vs_hyphen"
        )
        row = _find(self.rows, "PAEP", "H3")
        self.assertEqual(row["chip_id"], "S11 2")
        self.assertEqual(row["chip_id_verbatim"], "S11\xa02")

    def test_no_prefix_grouping_rule_would_be_safe(self) -> None:
        """S7.x share sources while S11-x do not, so any rule grouping on the
        leading S<n> token is wrong for one of the two pairs. This test exists
        so nobody 'simplifies' the per-pair records into such a rule.
        """
        relations = {
            (r["subject_a"], r["subject_b"]): r["relation"]
            for r in self.provenance
            if r["record_kind"] == "relation"
        }
        self.assertEqual(relations[("S7.1", "S7.2")], "shares_patient_sources")
        self.assertEqual(relations[("S11-1", "S11 2")], "distinct_patients")

    def test_lost_mappings_are_recorded_for_both_sheets(self) -> None:
        """What is lost is the column ASSIGNMENT, not the chip set.

        `Son estos pero no se cual es cual` file-attests that distinction, so
        the record kind is `unresolved_mapping` rather than `lost_mapping`. The
        sheet keys stay the MEASUREMENT workbook's names -- note the literal
        trailing space on "PRL " -- because these records describe that file.
        """
        lost = {
            r["source_sheet"]
            for r in self.provenance
            if r["record_kind"] == "unresolved_mapping"
        }
        self.assertEqual(lost, {"IGFBP-1", "PRL "})
        for record in self.provenance:
            if record["record_kind"] != "unresolved_mapping":
                continue
            self.assertEqual(
                record["knowledge_state"], "chip_set_partly_known_column_order_unknown"
            )
            self.assertEqual(record["donor_matching_state"], "lost_column_assignment")
        self.assertEqual(
            set(
                self.contract["biological_independence_contract"][
                    "column_to_chip_mapping_lost"
                ]
            ),
            {"IGFBP-1", "PRL "},
        )

    def test_lost_mapping_sheets_carry_no_chip_id(self) -> None:
        for row in self.rows:
            if row["source_sheet"] in {"IGFBP-1", "PRL "}:
                self.assertEqual(row["chip_id"], "")
                self.assertEqual(row["chip_id_verbatim"], "")

    def test_only_paep_rows_carry_a_chip_id(self) -> None:
        sheets = {row["source_sheet"] for row in self.rows if row["chip_id"]}
        self.assertEqual(sheets, {"PAEP"})

    def test_validation_rejects_a_chip_id_backfilled_onto_a_lost_sheet(self) -> None:
        corrupted = [dict(row) for row in self.rows]
        _find(corrupted, "IGFBP-1", "G5")["chip_id"] = "S7.1"
        report = validate_secreted_protein_table(corrupted)
        self.assertEqual(report.status, "structurally_invalid")
        self.assertTrue(
            any("lost" in e and "chip_id" in e for e in report.errors), report.errors
        )

    def test_series_id_is_declared_positional_not_a_chip_claim(self) -> None:
        contract = self.contract["biological_independence_contract"]
        self.assertEqual(
            contract["series_id_semantics"], "positional_column_index_not_chip"
        )

    def test_donor_identity_is_never_asserted_anywhere(self) -> None:
        self.assertIn("donor_id", self.contract["always_empty_columns"])
        self.assertEqual(
            set(self.contract["always_empty_columns"]), set(ALWAYS_EMPTY_COLUMNS)
        )
        for record in self.provenance:
            self.assertNotIn(record["knowledge_state"], {"donor_identity_known"})

    def test_the_replicate_ceiling_is_a_ceiling_not_a_count(self) -> None:
        """The ceiling TIGHTENED when the annotation arrived, from 4 to 3.

        S10-2 shares its epithelial source group with S7.1/S7.2, so the five
        valued PAEP chips span at most 2 epithelial groups. It must never be
        revised upward without evidence.
        """
        contract = self.contract["biological_independence_contract"]
        self.assertEqual(contract["max_independent_units_paep_observed"], 3)
        self.assertEqual(contract["max_independent_epithelial_source_groups_paep"], 2)
        self.assertEqual(contract["max_independent_units_igfbp1"], "not_determinable")
        self.assertEqual(contract["max_independent_units_prl"], "not_determinable")

    def test_forbidden_claims_are_enumerated(self) -> None:
        forbidden = set(
            self.contract["biological_independence_contract"]["forbidden_claims"]
        )
        for claim in (
            "patient_level_variance",
            "paired_donor_analysis",
            "personalization_from_this_dataset",
            "n_equals_number_of_chips",
            "n_equals_number_of_columns",
            "within_column_pairing_across_day_rows_for_igfbp1_or_prl",
            "component_specific_effect_of_mpa_camp_or_xav939",
        ):
            self.assertIn(claim, forbidden)

    def test_validation_rejects_a_relaxed_independence_contract(self) -> None:
        import copy
        import tempfile

        import yaml

        relaxed = copy.deepcopy(self.contract)
        relaxed["biological_independence_contract"][
            "chip_is_independent_biological_replicate"
        ] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.yaml"
            path.write_text(yaml.safe_dump(relaxed), encoding="utf-8")
            report = validate_secreted_protein_table(self.rows, contract_path=path)
        self.assertEqual(report.status, "structurally_invalid")


if __name__ == "__main__":
    unittest.main()
