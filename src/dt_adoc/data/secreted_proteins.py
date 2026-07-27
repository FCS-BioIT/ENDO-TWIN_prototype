"""Transform the ADOC secreted-protein workbook into a tidy input table.

Source: ``data/proteinas secretadas ADOC.xlsx`` (immutable; never edited).
Sheets: ``PAEP``, ``IGFBP-1``, ``PRL `` (the trailing space in the last sheet
name is literal, not a typo -- it is how the workbook stores it).

The workbook does not offer assay-well granularity, so the finest available
observation level is one row per workbook data cell. This module preserves
several discrepancies honestly rather than papering over them:

* ``PAEP`` rows -- verbatim workbook labels ``HT (E2 only)`` /
  ``HT (E2+P4+XAV939)`` -- are the protocol's two treatment PHASES, not time
  points: ``HT`` is hormone treatment, the E2-only row is the proliferative
  phase and the full-cocktail row the secretory phase (collaborator-confirmed
  2026-09-18, SOFIA-COMM-007). No sampled day is assignable to a PAEP row on
  the evidence held, so ``resolved_protocol_day``,
  ``hours_after_cocktail_start`` and ``hours_after_e2_start`` are left empty
  for every PAEP row. The collaborator protocol does map each condition to a
  day *window*, recorded in ``protocol_phase``, but it pins no sampling
  instant. The day legends the annotation workbook carries on its PAEP sheet
  are transcribed onto the two interval rows of
  ``config/adoc_outlet_conditions.tsv`` and must not by themselves be used to
  backfill a day onto a measurement row. That is a statement about the
  evidence, not an impossibility claim: an explicit collaborator confirmation
  of PAEP sampling timing would be new evidence, and the columns are already
  there to carry it.
* PAEP chips ``S1`` and ``S2`` are present as column headers but their data
  cells carry no value. (At the OOXML level the ``<c>`` elements exist and are
  deliberately styled with the same highlight fill as their headers -- only
  ``<v>`` is absent.) Those are emitted as rows with
  ``measurement_state="missing"`` so the gap stays visible, and are marked
  ``quality_tier="exploratory"``. The collaborator confirmed on 2026-09-18
  (SOFIA-COMM-007) that she left those two older chips blank because she did
  not trust their data, so ``quality_tier`` is no longer listed in
  ``externally_asserted_fields`` for them -- it has a named confirming source.
* ``IGFBP-1`` has a real workbook fact for its outlet split: ``B2:F2`` is
  merged ``TOP`` and ``G2:K2`` is merged ``BOTTOM``.
  ``outlet_assignment_basis`` records this as ``workbook_merged_header``.
* ``PRL`` has no header row, but the collaborator confirmed the whole sheet was
  measured from the BOTTOM outlet (SOFIA-COMM-006), so all six columns are
  basal/stromal and carry
  ``outlet_assignment_basis="sheet_level_collaborator_confirmed"``. The earlier
  "first three TOP, last three BOTTOM" split, taken from
  ``docs/data-context/adoc-secreted-proteins.md``, was wrong. ``series_id``
  therefore renumbers ``PRL_BOTTOM_1..6`` in column order B..G -- note that
  ``PRL_BOTTOM_1..3`` used to mean columns E,F,G.
* The two basis columns are deliberately separate. The collaborator confirmed
  on 2026-07-29 (SOFIA-COMM-003) what an outlet *means* -- TOP = apical /
  epithelial, BOTTOM = basal / stromal -- which every row records as
  ``compartment_semantics_basis``. She did not confirm *which* PRL columns are
  which, nor that the whole PAEP sheet is the apical outlet. Collapsing the two
  into one "confirmed" basis would over-claim; see the module tests.
* Neither ``IGFBP-1`` nor ``PRL`` carries chip identifiers anywhere in the
  workbook, and the collaborator confirmed the column-to-chip and
  column-to-patient mapping for both sheets is LOST (SOFIA-COMM-005).
  ``chip_id`` is left empty for those sheets; a positional ``series_id``
  (e.g. ``IGFBP-1_BOTTOM_3``) is used instead and is explicitly positional,
  not a chip claim. It therefore does not license pairing a column across day
  rows -- see ``config/secreted_protein_contract.yaml``
  ``biological_independence_contract``.
* ``IGFBP-1`` labels its third day ``Day 7``; ``PRL`` labels the same stage
  ``Day 6``. The collaborator confirmed the ``Day 7`` label is an error and
  that row is day 6, so both resolve to protocol day 6. The original
  ``source_time_label`` is preserved verbatim (nbsp normalized to a plain
  space) alongside ``resolved_protocol_day`` and a ``time_resolution_note``.
* ``hours_after_cocktail_start`` anchors day 3 to 24 h and day 6 to 96 h in the
  full cocktail. It is wall-clock bench time and never a MaBoSS horizon. Day-0
  rows are left empty: the cocktail has not started and the day-0 collection
  window is unknown.
* Units (``pg/mL``) are not recorded anywhere in the workbook but are
  collaborator-confirmed (SOFIA-COMM-001), recorded as
  ``unit_basis="collaborator_confirmed"``.
* Stored zeros are real measurements. The collaborator confirmed absorbance was
  read and interpolation against the standard curve returned no detectable
  secretion (SOFIA-COMM-002), so they carry
  ``measurement_state="no_detectable_secretion"`` with ``raw_value`` kept at
  the stored ``0`` -- never blank, never NA, and distinct from both
  ``below_detection`` (censored) and ``missing`` (no measurement).
* ``condition`` preserves the workbook's own condition label, which is
  scientifically wrong twice over: it names ``P4`` where the progestin was
  MPA, and it omits cAMP entirely. It is never rewritten.
  ``condition_normalized`` carries the corrected identifier and
  ``condition_resolution_note`` records the discrepancy.
* Several fields the source-of-truth doc's recommended schema calls for have
  no support anywhere in this workbook (donor identity, technical-replicate
  or assay-well structure, collection volume/duration/flow rate). They are
  kept as real, always-empty columns rather than omitted, so the gap is
  machine-visible instead of only living in report prose.
* ``externally_asserted_fields`` names, per row, exactly which other column
  values are still asserted from ``docs/data-context/adoc-secreted-proteins.md``
  alone -- i.e. neither workbook-supported nor collaborator-confirmed. A
  field's ABSENCE from the list therefore means it is one of those two, never
  that it is unsupported. Read the ``*_basis`` columns to tell those two apart.
  WHICH fields they currently are is deliberately not restated here: it is
  ``externally_asserted_fields_current`` in
  ``config/secreted_protein_contract.yaml``, and the validator below fails if
  the emitted column disagrees with it. Three prose copies of that list drifted
  apart before it was made machine-readable.
* ``ValidationReport.status`` is ``structurally_valid``/``structurally_invalid``
  -- schema/contract conformance and traceability only. It does not assert
  that outlet-column assignment, replicate structure, or donor provenance are
  resolved; see the warnings section of the generated validation report for
  those open questions.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

import openpyxl
import yaml
from openpyxl.worksheet.worksheet import Worksheet

from dt_adoc.model.catalog import load_tsv
from dt_adoc.model.provenance import repo_root
from dt_adoc.reporting.tables import write_tsv

DATASET_ID = "adoc_secreted_proteins"
SOURCE_FILE = "data/proteinas secretadas ADOC.xlsx"
UNIT = "pg/mL"
#: pg/mL is absent from the workbook but collaborator-confirmed on 2026-07-29
#: (SOFIA-COMM-001), so it is no longer a context-document assumption.
UNIT_BASIS = "collaborator_confirmed"

#: TOP = apical/epithelial and BOTTOM = basal/stromal, confirmed by the
#: collaborator on 2026-07-29 (SOFIA-COMM-003). This is the *semantics* of an
#: outlet only; which columns belong to which outlet is a separate claim
#: tracked by ``outlet_assignment_basis``.
COMPARTMENT_SEMANTICS_BASIS = "collaborator_confirmed_top_apical_bottom_basal"

# Older PAEP chips the collaborator did not trust enough to include values
# for. First taken from docs/data-context/adoc-secreted-proteins.md and
# collaborator-confirmed on 2026-09-18 (SOFIA-COMM-007): "S2 y S1 estan en
# blanco porque no anadi al final los valores, porque eran chips mucho mas
# antiguos y no me fiaba de los datos."
EXPLORATORY_PAEP_CHIPS = frozenset({"S1", "S2"})

# The trailing space on "PRL " is literal in the workbook sheet name.
SHEET_PAEP = "PAEP"
SHEET_IGFBP1 = "IGFBP-1"
SHEET_PRL = "PRL "

COLUMNS = [
    "dataset_id",
    "source_file",
    "source_sheet",
    "source_cell",
    "source_row",
    "source_column",
    "source_label",
    "protein",
    "series_id",
    "chip_id",
    # Byte-faithful header cell, U+00A0 preserved. chip_id normalizes that
    # nbsp to a plain space; this column keeps the original recoverable so the
    # reconciliation with the collaborator's "S11-2" stays auditable. See
    # config/adoc_chip_donor_provenance.tsv.
    "chip_id_verbatim",
    # Identifiers the workbook does not provide anywhere. Kept as real,
    # always-empty columns (never synthesised) so the gap is machine-visible
    # rather than only living in report prose.
    "donor_id",
    "technical_replicate_id",
    "assay_well_id",
    "compartment",
    "outlet",
    # Two logically independent claims, deliberately NOT one column: which
    # columns are which outlet, versus what an outlet means biologically. The
    # collaborator confirmed only the second.
    "outlet_assignment_basis",
    "compartment_semantics_basis",
    # `condition` is the workbook's own label, preserved and never rewritten
    # even though it names P4 for MPA and omits cAMP. The corrected identifier
    # lives in `condition_normalized`.
    "condition",
    "condition_normalized",
    "condition_resolution_note",
    "protocol_phase",
    "source_time_label",
    "resolved_protocol_day",
    "hours_after_cocktail_start",
    "hours_after_e2_start",
    "time_resolution_note",
    "raw_value",
    "reported_concentration_pg_ml",
    "unit",
    "unit_basis",
    "dilution_factor",
    "dilution_corrected",
    "detection_limit_pg_ml",
    # Secretion-rate metadata the workbook does not provide. Kept empty for
    # the same reason as the identifiers above.
    "collected_volume",
    "collection_duration",
    "flow_rate",
    # Annotation-workbook facts, read from config/adoc_outlet_conditions.tsv --
    # never from the annotation workbook itself, which is gitignored. That keeps
    # `pixi run build-protein-table` reproducible on a fresh clone.
    "value_derivation",
    "technical_replicate_n",
    "value_is_technical_aggregate",
    "condition_interval_id",
    # Donor structure, from config/adoc_chip_donor_provenance.tsv. OPAQUE
    # repository-local labels only; the lab's own codes are never committed.
    "donor_group_id",
    "donor_matching_state",
    "measurement_state",
    "measurement_state_basis",
    "quality_tier",
    "exclusion_reason",
    # Delimited controlled flags naming every open uncertainty on this row, so
    # a reader need not reconstruct them from prose.
    "uncertainty_flags",
    # Delimited (see EXTERNAL_ASSERTION_DELIMITER) list of column names in
    # this row whose value came from the context document rather than the
    # workbook. A field's absence means the workbook itself supports it.
    "externally_asserted_fields",
    "resolution_note",
]

#: Delimiter joining field names in ``externally_asserted_fields``. Chosen
#: because none of the field names this module emits can contain it.
EXTERNAL_ASSERTION_DELIMITER = "|"

#: Always-empty columns: real, machine-visible gaps rather than omitted
#: fields or unstated report prose. Never populate these -- if evidence
#: arrives, extend the extraction, do not backfill a guess.
ALWAYS_EMPTY_COLUMNS = frozenset(
    {
        # Donor IDENTITY is never recorded. Only opaque group membership is, in
        # `donor_group_id`; see config/source_contract.yaml donor_label_scheme.
        "donor_id",
        # "cada pocillo 3 réplicas técnicas" gives the COUNT of technical
        # replicates, not an identifier, and neither workbook exposes a
        # per-replicate value. The count lives in `technical_replicate_n`;
        # synthesising 1/2/3 here would fabricate a grain the source lacks.
        "technical_replicate_id",
        "assay_well_id",
        # Left empty deliberately: the day-0 legend states "medio de 48 h o
        # 96 h", a disjunction. Collapsing it to one number, or averaging it,
        # would invent a window. The verbatim disjunction is preserved in
        # config/adoc_outlet_conditions.tsv.
        "collection_duration",
    }
)

DEFAULT_TABLE_OUTPUT = Path("input_tables/adoc_secreted_proteins.tsv")
DEFAULT_VALIDATION_REPORT = Path("input_tables/adoc_secreted_proteins_validation.md")
DEFAULT_CONTRACT_PATH = Path("config/secreted_protein_contract.yaml")

_ZERO_RESOLUTION_NOTE = (
    "Absorbance was measured and interpolation against the standard curve "
    "returned no detectable secretion; this is a measurement, not a missing "
    "or censored value (collaborator-confirmed 2026-07-29, SOFIA-COMM-002)."
)
_PAEP_TIME_ASSIGNABILITY_NOTE = (
    "PAEP sheet rows are experimental conditions, not time points. Their "
    "verbatim workbook labels are 'HT (E2 only)' and 'HT (E2+P4+XAV939)'; the "
    "workbook records no protocol day for PAEP. The collaborator protocol maps "
    "each condition to a day window (see protocol_phase) but pins no sampling "
    "instant, and the collaborator confirmed on 2026-09-18 (SOFIA-COMM-007) "
    "that the two rows ARE the two treatment phases. NO SAMPLED DAY IS "
    "ASSIGNABLE ON CURRENT EVIDENCE -- which is what is claimed here, not that "
    "a sampling instant could never exist or be recovered: an explicit "
    "collaborator confirmation of PAEP sampling timing would be new evidence "
    "and would be recorded as such. The annotation workbook's PAEP sheet "
    "carries the same Dia 0/2/3/6 legend cells as the other two sheets; they "
    "are transcribed onto the two INTERVAL rows of "
    "config/adoc_outlet_conditions.tsv (COND-E2-PRIMING, COND-FULL-COCKTAIL) "
    "and no PAEP measurement row is assigned to a timepoint row. "
    "resolved_protocol_day, hours_after_cocktail_start and hours_after_e2_start "
    "are therefore empty here, and those legends alone must never be used to "
    "backfill them."
)
_PAEP_PHASE_SEMANTICS_NOTE = (
    "PHASE SEMANTICS (SOFIA-COMM-007, collaborator-confirmed 2026-09-18): 'HT' "
    "is hormone treatment; the E2-only condition is the proliferative-phase "
    "arm (protocol days 0-2) and the full-cocktail condition the "
    "secretory-phase arm (days 2-6). These name what the protocol is intended "
    "to model in vitro; they are not a measured in vivo cycle phase and they "
    "supply no sampling instant, so no day is assignable from them (see "
    "time_resolution_note). The collaborator's "
    "accompanying expectation -- that receptivity, and therefore PAEP "
    "secretion, peaks in the secretory phase -- is recorded as her rationale "
    "and is NOT evidence: citing it as support for the E_PAEP direction would "
    "be circular with OM-001, the feasibility gate that tests exactly that "
    "direction."
)
_PAEP_MISSING_CHIP_NOTE = (
    "Collaborator did not trust this older chip's measurement; the workbook "
    "cell carries no value (styled but empty), which is neither a stored zero "
    "nor a measured non-detect. Confirmed by the collaborator on 2026-09-18 "
    "(SOFIA-COMM-007), which is why quality_tier is no longer listed as an "
    "external assertion for these rows."
)
_DAY7_RESOLUTION_NOTE = (
    "Workbook labels this row 'Day 7'; the collaborator confirmed it is "
    "day 6 -- a labelling error, not an endpoint convention "
    "(2026-07-29, SOFIA-COMM-003). The PRL sheet labels the same third "
    "timepoint 'Day 6'."
)
_CONDITION_CORRECTION_NOTE = (
    "Workbook label reads 'E2+P4+XAV939'. The progestin was MPA 1 uM, not "
    "P4, and the medium also contained cAMP 0.25 mM: the actual condition is "
    "E2 10 nM + MPA 1 uM + cAMP 0.25 mM + XAV939 10 uM (collaborator-"
    "confirmed 2026-07-29, SOFIA-COMM-004; consistent with SOFIA-HT-001 and "
    "config/protocols.yaml). The workbook label is preserved verbatim in "
    "`condition` and `source_label` and is never rewritten."
)
_DAY0_PHASE_NOTE = (
    "Day 0 precedes hormone addition: the annotation workbook records this "
    "sample as medium accumulated while connected with expansion medium "
    "('Conectado con medio de expansion', SOFIA-ANNO-005), which settles the "
    "previously open question of whether it integrates E2 exposure -- it does "
    "not. Two limits remain: the accumulation window is stated as a "
    "disjunction ('medio de 48 h o 96 h') and is therefore left empty rather "
    "than collapsed to one number, and expansion medium is a "
    "growth-factor-containing medium of unrecorded composition, so the model "
    "comparator basal_maternal (all inputs OFF) is the closest available "
    "match rather than a verified equivalent."
)

#: Normalized condition identifiers. `condition` keeps the workbook's own
#: label; these are the corrected, controlled values.
CONDITION_E2_ONLY = "e2_only_48h"
CONDITION_FULL_COCKTAIL = "e2_mpa_camp_xav939_96h"
CONDITION_PRE_COCKTAIL = "pre_cocktail_baseline"

#: Protocol phases. Day 0-2 is E2 10 nM alone (proliferative); day 2-6 adds
#: MPA 1 uM + cAMP 0.25 mM + XAV939 10 uM. Day-0 samples get their own term
#: because their E2 exposure is unverified (see _DAY0_PHASE_NOTE).
PHASE_E2_PROLIFERATIVE = "e2_proliferative_day0_2"
PHASE_FULL_COCKTAIL = "full_cocktail_day2_6"
PHASE_DAY0_BASELINE = "day0_baseline_expansion_medium_pre_hormone"

#: Elapsed wall-clock hours in the full cocktail per resolved protocol day.
#: Day 0 is deliberately absent: the cocktail has not started, and neither 0
#: nor -48 is defensible while the day-0 collection window is unknown. These
#: are bench hours and never a MaBoSS horizon or transition rate.
HOURS_AFTER_COCKTAIL_START = {3: 24, 6: 96}

#: Elapsed wall-clock hours since E2 was introduced at day 0. Day 0 itself is
#: absent for the same reason as above: its accumulation window is a stated
#: disjunction ("medio de 48 h o 96 h"), so no elapsed figure is defensible.
HOURS_AFTER_E2_START = {3: 72, 6: 144}

#: Per-sheet annotation facts, transcribed into
#: config/adoc_outlet_conditions.tsv rather than read from the annotation
#: workbook, which is gitignored for privacy. The builder therefore stays
#: reproducible on a clone that does not carry that file.
CONDITIONS_PATH = Path("config/adoc_outlet_conditions.tsv")
DONOR_PROVENANCE_PATH = Path("config/adoc_chip_donor_provenance.tsv")

#: "concentracion" = "abs muestra- abs control negativo" on all three annotation
#: sheets (SOFIA-ANNO-001): the reported figure is a concentration interpolated
#: from a blank-subtracted absorbance. Recorded so no downstream step applies a
#: second negative-control correction.
VALUE_DERIVATION = "concentration_from_blank_subtracted_absorbance"

#: "cada pocillo 3 réplicas técnicas" on all three annotation sheets
#: (SOFIA-ANNO-002). A COUNT, not an identifier: no per-replicate value exists
#: in either workbook and the aggregation function is unstated, so no SD, CV or
#: standard error is derivable and biological n is NOT raised.
TECHNICAL_REPLICATE_N = 3

#: "Medio recogido 1 mL" on all three annotation sheets (SOFIA-ANNO-003).
COLLECTED_VOLUME = "1 mL"

#: "Flujo 30 uL/h" on the PAEP sheet ONLY (PAEP!B6). Deliberately not broadcast
#: to the IGFBP-1 or PRL rows -- those sheets state no flow rate.
FLOW_RATE = "30 uL/h"

#: Basis for `measurement_state`. The zero note lives on the IGFBP-1 annotation
#: sheet only, so PAEP and PRL zeros rest on the collaborator statement alone.
#: The note also says which number was ENTERED, not that an absorbance read
#: exists, so it is recorded as operator-asserted rather than as a verified
#: curve interpolation.
_BASIS_ZERO_IGFBP1 = "operator_asserted_non_detect_annotation_sheet_igfbp1"
_BASIS_ZERO_OTHER = "operator_asserted_non_detect_collaborator_statement_only"
_BASIS_OBSERVED = "interpolated_from_blank_subtracted_absorbance"
_BASIS_MISSING = "no_measurement_exists"

_DAY_RE = re.compile(r"Day\s*(\d+)", re.IGNORECASE)


def _normalize_label(value: Any) -> str:
    return str(value).replace("\xa0", " ").strip()


def load_outlet_conditions(root: Path | None = None) -> list[dict[str, str]]:
    """Load the hand-curated annotation transcription."""
    return load_tsv((root or repo_root()) / CONDITIONS_PATH)


def load_donor_provenance(root: Path | None = None) -> list[dict[str, str]]:
    """Load the chip/donor provenance records."""
    return load_tsv((root or repo_root()) / DONOR_PROVENANCE_PATH)


def _donor_lookup(root: Path | None = None) -> dict[str, tuple[str, str]]:
    """Map chip_id -> (donor_group_id, donor_matching_state).

    ``donor_group_id`` combines the two opaque compartment source-group labels
    because a chip has no single donor: epithelial and stromal cells are not
    always from the same person, so a scalar donor per chip would be a false
    unit. An unannotated compartment yields ``unknown`` in its slot.
    """
    lookup: dict[str, tuple[str, str]] = {}
    for record in load_donor_provenance(root):
        if record.get("record_kind") != "chip":
            continue
        epi = record.get("epithelial_source_group", "") or "unknown"
        stro = record.get("stromal_source_group", "") or "unknown"
        lookup[record["subject_a"]] = (
            f"epi:{epi}|stroma:{stro}",
            record.get("donor_matching_state", "") or "unknown",
        )
    return lookup


def _classify_measurement(raw_value: Any) -> tuple[str, str]:
    """Return ``(measurement_state, resolution_note)`` for one workbook cell.

    A stored ``0`` is a measured non-detect, not a missing or censored value
    (SOFIA-COMM-002). ``raw_value`` is kept as the stored ``0`` by the caller;
    this function never blanks it. Applied to every sheet so the three sheets
    cannot drift apart if a future workbook revision stores a PAEP zero.
    """
    if raw_value is None:
        return "missing", ""
    if float(raw_value) == 0.0:
        return "no_detectable_secretion", _ZERO_RESOLUTION_NOTE
    return "observed", ""


def _resolve_day(source_time_label: str) -> tuple[int, str]:
    match = _DAY_RE.search(source_time_label)
    if not match:
        raise ValueError(f"unrecognized time label: {source_time_label!r}")
    day = int(match.group(1))
    if day == 7:
        return 6, _DAY7_RESOLUTION_NOTE
    return day, ""


def _base_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = dict.fromkeys(COLUMNS, "")
    row["dataset_id"] = DATASET_ID
    row["source_file"] = SOURCE_FILE
    row["unit"] = UNIT
    row["unit_basis"] = UNIT_BASIS
    row["compartment_semantics_basis"] = COMPARTMENT_SEMANTICS_BASIS
    row["value_derivation"] = VALUE_DERIVATION
    row["technical_replicate_n"] = TECHNICAL_REPLICATE_N
    row["value_is_technical_aggregate"] = "true"
    row["collected_volume"] = COLLECTED_VOLUME
    row.update(overrides)
    return row


def _paep_rows(
    ws: Worksheet,
    donors: dict[str, tuple[str, str]] | None = None,
    *,
    externally_asserted_fields: tuple[str, ...] = ("compartment", "outlet"),
) -> list[dict[str, Any]]:
    donors = donors or {}
    chip_by_col: dict[str, tuple[str, str]] = {}
    for col in range(2, 9):
        header = ws.cell(row=2, column=col)
        chip_by_col[header.column_letter] = (
            _normalize_label(header.value),
            str(header.value),
        )
    rows: list[dict[str, Any]] = []
    for row_idx in (3, 4):
        label_cell = ws.cell(row=row_idx, column=1)
        condition = _normalize_label(label_cell.value)
        is_full_cocktail = "only" not in condition.lower()
        for col in range(2, 9):
            cell = ws.cell(row=row_idx, column=col)
            column_letter = cell.column_letter
            chip_id, chip_id_verbatim = chip_by_col[column_letter]
            quality_tier = (
                "exploratory" if chip_id in EXPLORATORY_PAEP_CHIPS else "primary"
            )
            raw_value = cell.value
            observed = raw_value is not None
            state, zero_note = _classify_measurement(raw_value)
            donor_group, donor_state = donors.get(chip_id, ("", "unknown"))
            flags = ["paep_sheet_outlet_unverified", "paep_dilution_factor_unknown"]
            if state == "no_detectable_secretion":
                flags.append("zero_is_operator_asserted_non_detect")
            if not observed:
                flags.append("no_measurement_exists")
            flags.append("chip_not_an_independent_patient")
            # The PAEP sheet has no outlet axis at all -- its columns are
            # chips -- so "the whole sheet is the apical outlet" is a
            # sheet-level context-document claim, not a column-position one.
            # Read from the contract, never written out here: a second copy
            # of this list is exactly how the contract comment, the module
            # docstring and data/README.md came to disagree with the shipped
            # column. quality_tier is absent because the collaborator confirmed
            # on 2026-09-18 (SOFIA-COMM-007) why S1/S2 were left blank, as
            # `unit` and PRL's outlet left when their sources arrived.
            asserted_fields = list(externally_asserted_fields)
            rows.append(
                _base_row(
                    source_sheet=SHEET_PAEP,
                    source_cell=f"{column_letter}{row_idx}",
                    source_row=row_idx,
                    source_column=column_letter,
                    source_label=label_cell.value,
                    protein="PAEP",
                    series_id=f"PAEP_{chip_id}",
                    chip_id=chip_id,
                    chip_id_verbatim=chip_id_verbatim,
                    compartment="epithelial",
                    outlet="top",
                    outlet_assignment_basis="sheet_level_context_document_unverified",
                    condition=condition,
                    condition_normalized=(
                        CONDITION_FULL_COCKTAIL
                        if is_full_cocktail
                        else CONDITION_E2_ONLY
                    ),
                    condition_resolution_note=(
                        f"{_CONDITION_CORRECTION_NOTE} {_PAEP_PHASE_SEMANTICS_NOTE}"
                        if is_full_cocktail
                        else _PAEP_PHASE_SEMANTICS_NOTE
                    ),
                    protocol_phase=(
                        PHASE_FULL_COCKTAIL
                        if is_full_cocktail
                        else PHASE_E2_PROLIFERATIVE
                    ),
                    raw_value=raw_value if observed else "",
                    reported_concentration_pg_ml=raw_value if observed else "",
                    condition_interval_id=(
                        "COND-FULL-COCKTAIL" if is_full_cocktail else "COND-E2-PRIMING"
                    ),
                    donor_group_id=donor_group,
                    donor_matching_state=donor_state,
                    flow_rate=FLOW_RATE,
                    measurement_state=state,
                    measurement_state_basis=(
                        _BASIS_MISSING
                        if not observed
                        else _BASIS_ZERO_OTHER
                        if state == "no_detectable_secretion"
                        else _BASIS_OBSERVED
                    ),
                    uncertainty_flags=EXTERNAL_ASSERTION_DELIMITER.join(flags),
                    quality_tier=quality_tier,
                    exclusion_reason="" if observed else _PAEP_MISSING_CHIP_NOTE,
                    externally_asserted_fields=EXTERNAL_ASSERTION_DELIMITER.join(
                        asserted_fields
                    ),
                    # The time-assignability statement lives in the
                    # time-typed column, not in the general-purpose one, and
                    # is NOT duplicated across both: one row, one home for
                    # one fact.
                    time_resolution_note=_PAEP_TIME_ASSIGNABILITY_NOTE,
                    resolution_note=zero_note,
                )
            )
    return rows


def _time_series_rows(
    ws: Worksheet,
    *,
    protein: str,
    sheet: str,
    day_rows: range,
    groups: list[tuple[int, int, str, str]],
    outlet_basis: str,
) -> list[dict[str, Any]]:
    # No time-series sheet has an externally-asserted outlet any more: IGFBP-1's
    # split is a workbook fact and PRL's is collaborator-confirmed. Only PAEP
    # still asserts compartment/outlet from the context document.
    rows: list[dict[str, Any]] = []
    externally_asserted_fields = ""
    for row_idx in day_rows:
        label_cell = ws.cell(row=row_idx, column=1)
        source_time_label = _normalize_label(label_cell.value)
        resolved_day, time_note = _resolve_day(source_time_label)
        is_baseline = resolved_day == 0
        for group_start, group_end, outlet, compartment in groups:
            for position, col in enumerate(range(group_start, group_end + 1), start=1):
                cell = ws.cell(row=row_idx, column=col)
                column_letter = cell.column_letter
                raw_value = cell.value
                observed = raw_value is not None
                state, resolution_note = _classify_measurement(raw_value)
                flags = [
                    "column_to_chip_mapping_lost",
                    "not_paired_across_day_rows",
                    "chip_not_an_independent_patient",
                ]
                if sheet == SHEET_PRL:
                    flags.append("prl_column_count_exceeds_named_chip_families")
                if state == "no_detectable_secretion":
                    flags.append("zero_is_operator_asserted_non_detect")
                if is_baseline:
                    flags.append("day0_collection_window_disjunction_48_or_96h")
                if (
                    resolved_day == 6
                    and sheet == SHEET_IGFBP1
                    and state == ("no_detectable_secretion")
                ):
                    flags.append("igfbp1_day6_paired_zero_possible_dropout")
                rows.append(
                    _base_row(
                        source_sheet=sheet,
                        source_cell=f"{column_letter}{row_idx}",
                        source_row=row_idx,
                        source_column=column_letter,
                        source_label=label_cell.value,
                        protein=protein,
                        series_id=f"{protein}_{outlet.upper()}_{position}",
                        compartment=compartment,
                        outlet=outlet,
                        outlet_assignment_basis=outlet_basis,
                        condition_normalized=(
                            CONDITION_PRE_COCKTAIL
                            if is_baseline
                            else CONDITION_FULL_COCKTAIL
                        ),
                        condition_resolution_note=(
                            _DAY0_PHASE_NOTE
                            if is_baseline
                            else _CONDITION_CORRECTION_NOTE
                        ),
                        protocol_phase=(
                            PHASE_DAY0_BASELINE if is_baseline else PHASE_FULL_COCKTAIL
                        ),
                        source_time_label=source_time_label,
                        resolved_protocol_day=resolved_day,
                        hours_after_cocktail_start=HOURS_AFTER_COCKTAIL_START.get(
                            resolved_day, ""
                        ),
                        hours_after_e2_start=HOURS_AFTER_E2_START.get(resolved_day, ""),
                        time_resolution_note=time_note,
                        condition_interval_id=(
                            "COND-DAY0-BASELINE"
                            if is_baseline
                            else "COND-DAY3-SAMPLE"
                            if resolved_day == 3
                            else "COND-DAY6-SAMPLE"
                        ),
                        # chip_id is empty for these sheets, so no donor group
                        # can be attached: the column-to-chip mapping is lost.
                        donor_group_id="",
                        donor_matching_state="lost_column_assignment",
                        measurement_state_basis=(
                            _BASIS_ZERO_IGFBP1
                            if state == "no_detectable_secretion"
                            and sheet == SHEET_IGFBP1
                            else _BASIS_ZERO_OTHER
                            if state == "no_detectable_secretion"
                            else _BASIS_OBSERVED
                        ),
                        uncertainty_flags=EXTERNAL_ASSERTION_DELIMITER.join(flags),
                        raw_value=raw_value if observed else "",
                        reported_concentration_pg_ml=raw_value if observed else "",
                        measurement_state=state,
                        quality_tier="primary",
                        externally_asserted_fields=externally_asserted_fields,
                        resolution_note=resolution_note,
                    )
                )
    return rows


def build_protein_table(source_path: Path | None = None) -> list[dict[str, Any]]:
    """Read the ADOC secreted-protein workbook and return tidy rows.

    One row per workbook data cell. Never mutates or reopens the workbook for
    writing -- ``load_workbook`` is used read-only, ``data_only=True``.
    """
    path = source_path or (repo_root() / SOURCE_FILE)
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    donors = _donor_lookup()
    asserted = tuple(load_contract()["externally_asserted_fields_current"])
    rows: list[dict[str, Any]] = []
    rows.extend(
        _paep_rows(workbook[SHEET_PAEP], donors, externally_asserted_fields=asserted)
    )
    rows.extend(
        _time_series_rows(
            workbook[SHEET_IGFBP1],
            protein="IGFBP-1",
            sheet=SHEET_IGFBP1,
            day_rows=range(3, 6),
            groups=[(2, 6, "top", "epithelial"), (7, 11, "bottom", "stromal")],
            outlet_basis="workbook_merged_header",
        )
    )
    rows.extend(
        _time_series_rows(
            workbook[SHEET_PRL],
            protein="PRL",
            sheet=SHEET_PRL,
            day_rows=range(3, 6),
            # All six columns are the BOTTOM outlet (SOFIA-COMM-006). This is a
            # SHEET-level fact with no column axis, so series_id renumbers
            # PRL_BOTTOM_1..6 in workbook column order B..G. Note that
            # PRL_BOTTOM_1..3 previously denoted columns E,F,G and now denote
            # B,C,D -- config/observation_model_map.tsv was remapped in the same
            # change and a test now resolves every source_series_id against this
            # table so the referent can never drift silently again.
            groups=[(2, 7, "bottom", "stromal")],
            outlet_basis="sheet_level_collaborator_confirmed",
        )
    )
    workbook.close()
    return rows


def write_protein_table(
    rows: list[dict[str, Any]], output_path: Path | None = None
) -> Path:
    path = output_path or (repo_root() / DEFAULT_TABLE_OUTPUT)
    write_tsv(path, rows)
    return path


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Schema/contract conformance and traceability only.

        ``structurally_valid`` means the table's shape, controlled
        vocabularies, uniqueness, and internal consistency rules hold. It
        does **not** assert that compartment assignment, units, replicate
        structure, or zero semantics are biologically resolved -- see
        ``warnings`` for those open questions.
        """
        return "structurally_valid" if not self.errors else "structurally_invalid"

    def payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks,
        }


def load_contract(contract_path: Path | None = None) -> dict[str, Any]:
    path = contract_path or (repo_root() / DEFAULT_CONTRACT_PATH)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a mapping.")
    return payload


def _non_empty(value: Any) -> bool:
    return str(value).strip() != ""


def validate_secreted_protein_table(
    rows: list[dict[str, Any]] | None = None,
    contract_path: Path | None = None,
    table_path: Path | None = None,
) -> ValidationReport:
    report = ValidationReport()
    contract = load_contract(contract_path)
    if rows is None:
        rows = load_tsv(table_path or (repo_root() / DEFAULT_TABLE_OUTPUT))

    header = set(rows[0].keys()) if rows else set()
    missing_columns = [c for c in contract["columns"] if c not in header]
    if missing_columns:
        report.errors.append(f"missing columns: {missing_columns}")
    report.checks.append("columns_present")

    required_nonempty = contract["required_nonempty"]
    for i, row in enumerate(rows):
        for field_name in required_nonempty:
            if not _non_empty(row.get(field_name, "")):
                report.errors.append(f"row {i}: empty required field {field_name!r}")
    report.checks.append("required_nonempty")

    vocab = contract["controlled_vocabularies"]
    for i, row in enumerate(rows):
        for field_name, allowed in vocab.items():
            value = row.get(field_name, "")
            if _non_empty(value) and str(value) not in allowed:
                report.errors.append(f"row {i}: invalid {field_name} value {value!r}")
    report.checks.append("controlled_vocabularies")

    key_fields = contract["uniqueness_key"]
    seen: set[tuple[Any, ...]] = set()
    for i, row in enumerate(rows):
        key = tuple(row.get(f, "") for f in key_fields)
        if key in seen:
            report.errors.append(f"row {i}: duplicate uniqueness key {key}")
        seen.add(key)
    report.checks.append("uniqueness_key")

    for i, row in enumerate(rows):
        state = row.get("measurement_state")
        has_value = _non_empty(row.get("raw_value", ""))
        if state == "missing":
            if has_value:
                report.errors.append(
                    f"row {i}: measurement_state=missing but raw_value is set"
                )
            # A measurement can only be absent for a stated reason. Without
            # this, a measured non-detect could be silently downgraded to
            # `missing` -- exactly the NA-for-zero conversion AGENTS.md forbids
            # -- and nothing would fail.
            if not _non_empty(row.get("exclusion_reason", "")):
                report.errors.append(
                    f"row {i}: measurement_state=missing requires an "
                    "exclusion_reason saying why no measurement exists; a "
                    "measured non-detect is not missing data"
                )
        if state in {"observed", "no_detectable_secretion"}:
            if not has_value:
                report.errors.append(
                    f"row {i}: measurement_state={state} but raw_value is empty"
                )
            else:
                try:
                    value = float(row["raw_value"])
                except (TypeError, ValueError):
                    report.errors.append(
                        f"row {i}: raw_value is not numeric for a measured row"
                    )
                else:
                    # A measured non-detect is a real measurement of zero, and
                    # a stored zero is never anything else. Both directions are
                    # errors so the confirmed zero semantics cannot regress
                    # into `observed`, `missing`, or `below_detection`.
                    if state == "no_detectable_secretion" and value != 0.0:
                        report.errors.append(
                            f"row {i}: measurement_state=no_detectable_secretion "
                            f"but raw_value is {row['raw_value']!r}, not zero"
                        )
                    if state == "observed" and value == 0.0:
                        report.errors.append(
                            f"row {i}: raw_value is zero but measurement_state is "
                            "'observed'; a stored zero is a measured non-detect "
                            "(no_detectable_secretion), never an unqualified "
                            "observation"
                        )
    report.checks.append("measurement_state_consistency")

    independence = contract.get("biological_independence_contract", {})
    if independence.get("chip_is_independent_biological_replicate") is not False:
        report.errors.append(
            "biological_independence_contract must assert "
            "chip_is_independent_biological_replicate: false (chips share "
            "patient sources; SOFIA-COMM-005)"
        )
    lost_sheets = set(independence.get("column_to_chip_mapping_lost", []))
    for i, row in enumerate(rows):
        if row.get("source_sheet") in lost_sheets and _non_empty(
            row.get("chip_id", "")
        ):
            report.errors.append(
                f"row {i}: sheet {row['source_sheet']!r} has a lost "
                "column-to-chip mapping, so chip_id must stay empty but "
                f"{row['chip_id']!r} was set"
            )
    report.checks.append("lost_chip_mapping_stays_empty")

    # --- cross-table consistency ------------------------------------------
    # The outlet record, the conditions transcription and the sample-provenance
    # table must agree. Without these three checks each table could drift into a
    # private version of the protocol.
    try:
        conditions = {row["condition_id"]: row for row in load_outlet_conditions()}
    except FileNotFoundError:  # pragma: no cover - contract file is committed
        conditions = {}
        report.errors.append(f"missing conditions table {CONDITIONS_PATH}")
    if conditions:
        for i, row in enumerate(rows):
            interval = row.get("condition_interval_id", "")
            if not _non_empty(interval):
                report.errors.append(f"row {i}: empty condition_interval_id")
                continue
            condition = conditions.get(interval)
            if condition is None:
                report.errors.append(
                    f"row {i}: condition_interval_id {interval!r} does not "
                    f"resolve in {CONDITIONS_PATH}"
                )
                continue
            for field_name in (
                "condition_normalized",
                "protocol_phase",
                "hours_after_cocktail_start",
                "hours_after_e2_start",
            ):
                expected = condition.get(field_name, "")
                actual = str(row.get(field_name, ""))
                if str(expected) != actual:
                    report.errors.append(
                        f"row {i}: {field_name} is {actual!r} but "
                        f"{interval} declares {expected!r}"
                    )
    report.checks.append("condition_interval_resolves")

    try:
        provenance = load_donor_provenance()
    except FileNotFoundError:  # pragma: no cover - contract file is committed
        provenance = []
        report.errors.append(f"missing provenance table {DONOR_PROVENANCE_PATH}")
    if provenance:
        known_chips = {
            record["subject_a"]
            for record in provenance
            if record.get("record_kind") == "chip"
        }
        table_chips = {row["chip_id"] for row in rows if _non_empty(row.get("chip_id"))}
        for chip in sorted(table_chips - known_chips):
            report.errors.append(
                f"chip_id {chip!r} is in the table but has no chip record in "
                f"{DONOR_PROVENANCE_PATH}"
            )
        # A donor group may only ever appear alongside a chip that has one. On
        # the sheets whose column-to-chip mapping is lost there is no chip, so
        # there must be no donor group either -- that is the guard against
        # backfilling donor structure onto positional columns.
        for i, row in enumerate(rows):
            if _non_empty(row.get("donor_group_id")) and not _non_empty(
                row.get("chip_id")
            ):
                report.errors.append(
                    f"row {i}: donor_group_id is set but chip_id is empty; a "
                    "donor group must never be attached to a positional column"
                )
    report.checks.append("donor_provenance_resolves")

    independence = contract.get("biological_independence_contract", {})
    if independence.get("secretion_rate_derivable") is not False:
        report.errors.append(
            "biological_independence_contract must assert "
            "secretion_rate_derivable: false -- 1 mL at 30 uL/h implies 33.3 h, "
            "contradicting both stated collection windows (SOFIA-ANNO-003)"
        )
    if independence.get("dispersion_statistic_derivable") is not False:
        report.errors.append(
            "biological_independence_contract must assert "
            "dispersion_statistic_derivable: false -- the 3 technical replicates "
            "are summarised in the source with no per-replicate value "
            "(SOFIA-ANNO-002)"
        )
    report.checks.append("derivation_prohibitions_declared")

    series_outlets: dict[str, set[str]] = {}
    for row in rows:
        series_outlets.setdefault(row.get("series_id", ""), set()).add(
            row.get("outlet", "")
        )
    for series_id, outlets in series_outlets.items():
        if len(outlets) > 1:
            report.errors.append(
                f"series {series_id!r}: TOP and BOTTOM merged into one series "
                f"({outlets})"
            )
    report.checks.append("top_bottom_not_merged")

    for i, row in enumerate(rows):
        is_paep = row.get("source_sheet") == SHEET_PAEP
        has_day = _non_empty(row.get("resolved_protocol_day", ""))
        if is_paep and has_day:
            report.errors.append(f"row {i}: PAEP row unexpectedly has a resolved day")
        if not is_paep and not has_day:
            report.errors.append(
                f"row {i}: non-PAEP row is missing resolved_protocol_day"
            )
    report.checks.append("paep_has_no_time_axis")

    # The PAEP rows are the two protocol PHASES, so on the evidence held they
    # resolve to the two INTERVAL rows of the conditions table and not to a
    # sampled-timepoint row (SOFIA-COMM-007). The annotation workbook's PAEP
    # sheet carries the same day legends as the time-series sheets, which is
    # precisely the trap: without this check a well-meaning edit can attach a
    # PAEP row -- or the timepoint row's applies_to_sheets -- to a day that
    # only those legends suggest. It pins the current evidence state, not an
    # impossibility: if the collaborator ever confirms PAEP sampling timing,
    # this check is revised deliberately alongside a new evidence record, and
    # the table's day columns already exist to carry the answer.
    for i, row in enumerate(rows):
        if row.get("source_sheet") != SHEET_PAEP:
            continue
        condition = conditions.get(row.get("condition_interval_id", ""))
        if condition is None:
            continue  # already reported by the resolution check above
        if condition.get("interval_or_timepoint") != "interval":
            report.errors.append(
                f"row {i}: PAEP row resolves to "
                f"{row['condition_interval_id']!r}, which is a "
                f"{condition.get('interval_or_timepoint')!r} row; PAEP "
                "conditions are protocol phases and no sampled day is "
                "assignable to them on current evidence"
            )
    for condition_id, condition in conditions.items():
        if condition.get("interval_or_timepoint") != "timepoint":
            continue
        sheets = [
            sheet.strip() for sheet in condition.get("applies_to_sheets", "").split(";")
        ]
        if SHEET_PAEP in sheets:
            report.errors.append(
                f"{condition_id}: a sampled timepoint must not declare "
                f"applies_to_sheets={SHEET_PAEP!r}; no PAEP measurement is "
                "assigned to a day on current evidence (SOFIA-COMM-007)"
            )
    report.checks.append("paep_conditions_are_phases_not_timepoints")

    declared = contract.get("externally_asserted_fields_current")
    if not isinstance(declared, list) or not declared:
        report.errors.append(
            "contract must declare externally_asserted_fields_current -- the "
            "list of still-externally-asserted columns has to have exactly one "
            "machine-readable home, because three prose copies of it drifted "
            "apart once already"
        )
    else:
        emitted: set[str] = set()
        for row in rows:
            emitted.update(
                token
                for token in str(row.get("externally_asserted_fields", "")).split(
                    EXTERNAL_ASSERTION_DELIMITER
                )
                if token
            )
        if emitted != set(declared):
            report.errors.append(
                "externally_asserted_fields emits "
                f"{sorted(emitted)} but the contract declares {sorted(declared)}; "
                "a field whose confirming source arrived must leave both, and a "
                "description that disagrees with the shipped column is how a "
                "reader learns the wrong provenance"
            )
    report.checks.append("externally_asserted_fields_match_contract")

    for i, row in enumerate(rows):
        for field_name in ALWAYS_EMPTY_COLUMNS & header:
            if _non_empty(row.get(field_name, "")):
                report.errors.append(
                    f"row {i}: {field_name!r} must stay empty (no source "
                    "evidence exists for it) but a value was set"
                )
    report.checks.append("always_empty_columns_stay_empty")

    # Warning keys mirror config/secreted_protein_contract.yaml
    # warning_conditions, and a test asserts the two lists agree.
    #
    # RETIRED: prl_outlet_column_positions_unverified. The whole PRL sheet is the
    # BOTTOM outlet (SOFIA-COMM-006), so there is no column split left to verify.
    # The circularity caution that warning carried is VINDICATED rather than
    # obsolete and is preserved in the contract: the day-6 magnitude asymmetry
    # that looked like an apical/basal difference lies entirely WITHIN the basal
    # outlet, so anyone who had resolved the split from it would have been
    # exactly wrong.
    #
    # REPLACED BY a structural mismatch the correction exposes: six data columns
    # in one outlet against the three chip families named in LOST-002 of
    # config/adoc_chip_donor_provenance.tsv.
    prl_rows = [row for row in rows if row.get("source_sheet") == SHEET_PRL]
    if prl_rows:
        report.warnings.append(
            "[prl_column_count_exceeds_named_chip_families] The PRL sheet has "
            f"{len(prl_rows)} rows across 6 data columns, all confirmed as the "
            "BOTTOM outlet (SOFIA-COMM-006), but only 3 chip families are named "
            "in the annotation workbook (LOST-002). Either each family spans "
            "more than one column or the list is incomplete; either way the "
            "plausible independent-unit count is AT MOST 3 and possibly fewer, "
            "never 6. Confirming one outlet resolves the compartment, not the "
            "replicate structure: no column is a unit, columns must not be "
            "paired with each other within a day, and "
            "max_independent_units_prl stays not_determinable."
        )

    paep_rows = [row for row in rows if row.get("source_sheet") == SHEET_PAEP]
    if paep_rows:
        report.warnings.append(
            "[paep_sheet_outlet_unverified] The PAEP sheet carries no outlet "
            "axis (its columns are chips), so outlet=top for all "
            f"{len(paep_rows)} row(s) is a sheet-level context-document claim. "
            "The 2026-07-29 confirmation defined what TOP means but did not "
            "state which outlet PAEP was sampled from."
        )

    if paep_rows:
        # The two ceilings are READ from the contract, never written here. A
        # hardcoded copy is how the superseded "<=4 donor groups" survived in
        # four places after SOFIA-ANNO-007 tightened it.
        independence_contract = contract.get("biological_independence_contract", {})
        max_units = independence_contract["max_independent_units_paep_observed"]
        max_groups = independence_contract[
            "max_independent_epithelial_source_groups_paep"
        ]
        report.warnings.append(
            "[chip_donor_independence_partially_unknown] Chips are not "
            "independent biological replicates. S7.1 and S7.2 share patient "
            "sources, S11-1 and 'S11 2' are different patients, and S10-2 "
            "shares its EPITHELIAL source group with S7.1/S7.2 (REL-003, "
            "superseding the earlier 'unknown'), so the 5 PAEP chips carrying "
            f"values span at most {max_units} independent units and at most "
            f"{max_groups} epithelial source groups (a ceiling, not a count). "
            "Epithelial and stromal cells within one chip may also come from "
            "different patients. See config/adoc_chip_donor_provenance.tsv "
            "(SOFIA-COMM-005, SOFIA-ANNO-007)."
        )

    lost_rows = [row for row in rows if row.get("source_sheet") in lost_sheets]
    if lost_rows:
        report.warnings.append(
            "[igfbp1_prl_column_to_chip_mapping_lost] The column-to-chip and "
            "column-to-patient mapping for IGFBP-1 and PRL was lost by the "
            f"collaborator and is unrecoverable; affects {len(lost_rows)} "
            "row(s). series_id for these sheets is a positional column index, "
            "so no column may be paired across day rows and no per-unit "
            "longitudinal or paired comparison is constructible "
            "(SOFIA-COMM-005)."
        )

    # Data-quality challenge raised in review, NOT a collaborator statement:
    # IGFBP-1 day-6 columns 4 and 5 read exactly zero in both outlets after
    # holding the highest day-3 values in both. Treating those four cells as
    # measured non-detects is the collaborator's stated default, but the
    # coincidence is more consistent with chip-level dropout, so the table
    # surfaces it rather than resolving it.
    dropout_candidates = sorted(
        row["source_cell"]
        for row in rows
        if row.get("source_sheet") == SHEET_IGFBP1
        and row.get("measurement_state") == "no_detectable_secretion"
        and str(row.get("resolved_protocol_day", "")) == "6"
    )
    if dropout_candidates:
        report.warnings.append(
            "[igfbp1_day6_paired_zero_columns_possible_dropout] IGFBP-1 day-6 "
            f"cells {', '.join(dropout_candidates)} are recorded as measured "
            "non-detects per SOFIA-COMM-002, but the same two column "
            "positions read exactly zero in BOTH outlets after holding the "
            "highest day-3 values in both, which is more consistent with "
            "chip-level dropout than with secretion ceasing. Open question "
            "for the collaborator: were day-6 samples collected for all five "
            "IGFBP-1 chips? Until answered these four cells must not be used "
            "as evidence that secretion fell."
        )
    report.checks.append("known_soft_spot_warnings")

    declared = contract.get("warning_conditions", [])
    emitted = [
        warning.split("]", 1)[0].lstrip("[")
        for warning in report.warnings
        if warning.startswith("[")
    ]
    unknown = [key for key in emitted if key not in declared]
    if unknown:
        report.errors.append(
            f"warnings emitted keys absent from contract warning_conditions: {unknown}"
        )
    report.checks.append("warning_keys_declared_in_contract")

    return report


#: Metadata the 2026-07-29 collaborator confirmation RESOLVED, kept as an
#: explicit record so the resolution is auditable rather than a silent
#: disappearance from the unresolved list. See
#: docs/collaborator_metadata_2026-07-29.md.
RESOLVED_METADATA = [
    ("Units are pg/mL, collaborator-confirmed rather than assumed (SOFIA-COMM-001)."),
    (
        "A stored zero is a measured non-detect: absorbance was read and "
        "interpolation against the standard curve returned no detectable "
        "secretion (SOFIA-COMM-002)."
    ),
    (
        "TOP is the apical/epithelial compartment and BOTTOM the basal/"
        "stromal compartment (SOFIA-COMM-003)."
    ),
    (
        "The IGFBP-1 row labelled 'Day 7' is day 6 -- a workbook labelling "
        "error (SOFIA-COMM-003)."
    ),
    (
        "Protocol day anchoring: days 0-2 are E2 10 nM for 48 h; days 2-6 add "
        "MPA 1 uM + cAMP 0.25 mM + XAV939 10 uM for 96 h; day 3 is 24 h and "
        "day 6 is 96 h into the cocktail (SOFIA-COMM-004)."
    ),
    (
        "The treated condition is E2 + MPA + cAMP + XAV939. The workbook "
        "label 'HT (E2+P4+XAV939)' names P4 for MPA and omits cAMP; it is "
        "preserved verbatim and corrected in condition_normalized "
        "(SOFIA-COMM-004)."
    ),
    (
        "Chips are not independent biological replicates, and the "
        "column-to-chip mapping for IGFBP-1 and PRL is lost. Known relations "
        "are recorded in config/adoc_chip_donor_provenance.tsv "
        "(SOFIA-COMM-005)."
    ),
    (
        "Reported values are concentrations interpolated from a "
        "BLANK-SUBTRACTED absorbance ('abs muestra- abs control negativo'), so "
        "no further negative-control correction may be applied downstream "
        "(SOFIA-ANNO-001)."
    ),
    (
        "Each well was assayed in 3 technical replicates, so every reported "
        "value is an aggregate of 3 wells. Technical replicates raise no "
        "biological n (SOFIA-ANNO-002)."
    ),
    (
        "1 mL of medium was collected per sample, and the PAEP perfusion flow "
        "rate was 30 uL/h (SOFIA-ANNO-003). These are collection metadata "
        "only; see the unresolved list for why they do not yield a rate."
    ),
    (
        "The day-0 sample is expansion medium and therefore precedes hormone "
        "addition, so it is a genuine pre-treatment baseline rather than an "
        "unverified one (SOFIA-ANNO-005)."
    ),
    (
        "S10-2 shares its epithelial cell-source group with S7.1 and S7.2, so "
        "the 5 PAEP chips carrying values span at most 2 epithelial source "
        "groups. This TIGHTENED the independence ceiling (SOFIA-ANNO-007)."
    ),
    (
        "For IGFBP-1 and PRL what was lost is the column ASSIGNMENT, not the "
        "chip set: the collaborator states 'Son estos pero no se cual es cual' "
        "in the source itself. Still no column may be assigned to a chip "
        "(SOFIA-ANNO-007)."
    ),
    (
        "PRL was measured from the BOTTOM outlet: all six columns of the PRL "
        "sheet are basal/stromal, so no apical PRL series exists and the "
        "previously assumed first-three-TOP / last-three-BOTTOM split was "
        "wrong (SOFIA-COMM-006). This CONSTRAINS more than it licenses -- the "
        "day-6 magnitude asymmetry once read as a compartment difference lies "
        "entirely within the basal outlet -- and it does not touch the donor "
        "limitation: the column-to-chip mapping is still lost and no "
        "patient-specific inference becomes possible."
    ),
]

UNRESOLVED_METADATA = [
    (
        "Donor identity per chip. Only pairwise relations are known (S7.1 and "
        "S7.2 share patient sources; S11-1 and 'S11 2' are different "
        "patients; S10-2 unknown), so donor_id stays empty throughout and no "
        "chip is assigned a donor."
    ),
    (
        "Which epithelial and which stromal donor a given chip used: matching "
        "was attempted where possible but is not always the same patient, and "
        "the per-compartment mapping is unrecorded."
    ),
    (
        "The lost column-to-chip and column-to-patient mapping for IGFBP-1 "
        "and PRL is unrecoverable, so those columns cannot be paired across "
        "day rows."
    ),
    (
        "How the 3 technical replicates per well were combined (mean, median, "
        "or one-of-three). The COUNT is now known from the annotation workbook "
        "(SOFIA-ANNO-002); the aggregation function is not, so no dispersion, "
        "SD, CV or standard error is derivable from this dataset."
    ),
    (
        "Whether reported concentrations are already dilution-corrected "
        "(dilution_factor and dilution_corrected are left empty throughout). "
        "Review found all ten PAEP values are exact multiples of 1/69 and "
        "run 17x-1000x above the top standard of the workbook's own cached "
        "ELISA curves, so some uniform correction was applied upstream; the "
        "factor itself is unknown and is never asserted."
    ),
    (
        "Assay detection limits (detection_limit_pg_ml is left empty "
        "throughout). Values appear in context/adoc-paper-and-readout-"
        "context.md but are not traced to the supplementary methods, so they "
        "are not written into this table."
    ),
    (
        "The collection interval, and with it any concentration-to-secretion-"
        "rate conversion. Volume (1 mL) and flow rate (30 uL/h, PAEP sheet "
        "only) are now recorded from the annotation workbook, but they are "
        "MUTUALLY INCONSISTENT with the stated windows: 1000 uL / 30 uL/h = "
        "33.3 h, neither the 48 h nor the 96 h medium named in the day "
        "legends. No hydraulic regime, per-channel split, cell count or "
        "secreting area is recorded, so no rate is derivable (SOFIA-ANNO-003)."
    ),
    (
        "The day-0 accumulation window: the legend states a disjunction, "
        "'medio de 48 h o 96 h'. It is never collapsed to one number or "
        "averaged, so collection_duration and both hours columns stay empty "
        "for day-0 rows."
    ),
    (
        "The composition of the expansion medium used for the day-0 baseline. "
        "It is a growth-factor-containing medium of unrecorded formulation, so "
        "the model comparator basal_maternal (all inputs OFF) is the closest "
        "available match rather than a verified equivalent."
    ),
    (
        "Whether a shared cell-source group means one patient or one isolate/"
        "passage. The PAEP independence ceiling was tightened from 4 to 3 on "
        "the conservative reading; if the groups are patients it drops to 2."
    ),
    (
        "Whether the S11 chips share a cell-source pairing or have one each. "
        "The annotation names a pairing for the family without splitting it, "
        "which neither confirms nor refutes the confirmed statement that "
        "S11-1 and S11-2 are different patients."
    ),
    (
        "What the date-formatted value at PAEP!I8 of the annotation workbook "
        "originally read. It sits under a line of cell-source tokens and "
        "appears to be an Excel-autoformatted code. Neither the value nor a "
        "reconstructed token is written into any committed artifact."
    ),
    (
        "PAEP sampling instant: PAEP rows record only "
        "'HT (E2 only)' / 'HT (E2+P4+XAV939)' condition labels. The protocol "
        "maps each to a day window (protocol_phase) but not to a day."
    ),
    (
        "How many independent units the 6 PRL columns represent. All six are "
        "confirmed to be the BOTTOM outlet, but only 3 chip families are named "
        "for them, so the count is at most 3 and possibly fewer -- never 6."
    ),
    (
        "Which outlet the PAEP sheet was sampled from (apical, basal, or "
        "pooled); the sheet has no outlet axis."
    ),
    (
        "Whether day-6 samples were collected for all five IGFBP-1 chips. "
        "Two column positions read exactly zero in both outlets at day 6 "
        "after holding the highest day-3 values in both, which is more "
        "consistent with dropout than with secretion ceasing."
    ),
]


def write_validation_report(
    rows: list[dict[str, Any]],
    report: ValidationReport,
    path: Path | None = None,
) -> Path:
    out_path = path or (repo_root() / DEFAULT_VALIDATION_REPORT)
    by_sheet = Counter(row["source_sheet"] for row in rows)
    by_compartment = Counter(
        row["compartment"] for row in rows if _non_empty(row["compartment"])
    )
    by_state = Counter(row["measurement_state"] for row in rows)

    lines = [
        "# ADOC secreted-protein table validation report",
        "",
        f"Status: **{report.status}**",
        "",
        (
            "`structurally_valid` asserts schema/contract conformance and "
            "traceability to the source workbook only. It does **not** "
            "assert that outlet-column assignment, replicate structure, or "
            "donor provenance are resolved -- see Warnings below for those "
            "open questions. Units and zero semantics are no longer among "
            "them: both were confirmed by the collaborator on 2026-07-29 "
            "(see `docs/collaborator_metadata_2026-07-29.md`)."
        ),
        "",
        f"Total rows: {len(rows)}",
        "",
        "## Rows per source sheet",
        "",
    ]
    for sheet, count in sorted(by_sheet.items()):
        lines.append(f"- `{sheet}`: {count}")
    lines += ["", "## Rows per compartment", ""]
    for compartment, count in sorted(by_compartment.items()):
        lines.append(f"- {compartment}: {count}")
    lines += ["", "## Rows per measurement_state", ""]
    for state, count in sorted(by_state.items()):
        lines.append(f"- {state}: {count}")

    lines += ["", "## Checks run", ""]
    for check in report.checks:
        lines.append(f"- {check}")

    lines += ["", "## Errors", ""]
    if report.errors:
        lines += [f"- {err}" for err in report.errors]
    else:
        lines.append("- none")

    lines += ["", "## Warnings (known soft spots in the source, not table defects)", ""]
    if report.warnings:
        lines += [f"- {warn}" for warn in report.warnings]
    else:
        lines.append("- none")

    lines += [
        "",
        "## Resolved by collaborator confirmation (2026-07-29)",
        "",
    ]
    lines += [f"- {item}" for item in RESOLVED_METADATA]

    lines += ["", "## Unresolved metadata", ""]
    lines += [f"- {item}" for item in UNRESOLVED_METADATA]
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def build_and_validate(
    source_path: Path | None = None,
    table_path: Path | None = None,
    validation_path: Path | None = None,
    contract_path: Path | None = None,
) -> dict[str, Any]:
    """Build the canonical table and its validation report in one call."""
    rows = build_protein_table(source_path)
    written_table_path = write_protein_table(rows, table_path)
    report = validate_secreted_protein_table(rows, contract_path=contract_path)
    written_report_path = write_validation_report(rows, report, validation_path)
    return {
        "row_count": len(rows),
        "table_path": written_table_path,
        "validation_path": written_report_path,
        "status": report.status,
        "errors": report.errors,
        "warnings": report.warnings,
    }
