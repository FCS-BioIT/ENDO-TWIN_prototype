# ADOC secreted-protein table validation report

Status: **structurally_valid**

`structurally_valid` asserts schema/contract conformance and traceability to the source workbook only. It does **not** assert that outlet-column assignment, replicate structure, or donor provenance are resolved -- see Warnings below for those open questions. Units and zero semantics are no longer among them: both were confirmed by the collaborator on 2026-07-29 (see `docs/collaborator_metadata_2026-07-29.md`).

Total rows: 62

## Rows per source sheet

- `IGFBP-1`: 30
- `PAEP`: 14
- `PRL `: 18

## Rows per compartment

- epithelial: 29
- stromal: 33

## Rows per measurement_state

- missing: 4
- no_detectable_secretion: 19
- observed: 39

## Checks run

- columns_present
- required_nonempty
- controlled_vocabularies
- uniqueness_key
- measurement_state_consistency
- lost_chip_mapping_stays_empty
- condition_interval_resolves
- donor_provenance_resolves
- derivation_prohibitions_declared
- top_bottom_not_merged
- paep_has_no_time_axis
- paep_conditions_are_phases_not_timepoints
- externally_asserted_fields_match_contract
- always_empty_columns_stay_empty
- known_soft_spot_warnings
- warning_keys_declared_in_contract

## Errors

- none

## Warnings (known soft spots in the source, not table defects)

- [prl_column_count_exceeds_named_chip_families] The PRL sheet has 18 rows across 6 data columns, all confirmed as the BOTTOM outlet (SOFIA-COMM-006), but only 3 chip families are named in the annotation workbook (LOST-002). Either each family spans more than one column or the list is incomplete; either way the plausible independent-unit count is AT MOST 3 and possibly fewer, never 6. Confirming one outlet resolves the compartment, not the replicate structure: no column is a unit, columns must not be paired with each other within a day, and max_independent_units_prl stays not_determinable.
- [paep_sheet_outlet_unverified] The PAEP sheet carries no outlet axis (its columns are chips), so outlet=top for all 14 row(s) is a sheet-level context-document claim. The 2026-07-29 confirmation defined what TOP means but did not state which outlet PAEP was sampled from.
- [chip_donor_independence_partially_unknown] Chips are not independent biological replicates. S7.1 and S7.2 share patient sources, S11-1 and 'S11 2' are different patients, and S10-2 shares its EPITHELIAL source group with S7.1/S7.2 (REL-003, superseding the earlier 'unknown'), so the 5 PAEP chips carrying values span at most 3 independent units and at most 2 epithelial source groups (a ceiling, not a count). Epithelial and stromal cells within one chip may also come from different patients. See config/adoc_chip_donor_provenance.tsv (SOFIA-COMM-005, SOFIA-ANNO-007).
- [igfbp1_prl_column_to_chip_mapping_lost] The column-to-chip and column-to-patient mapping for IGFBP-1 and PRL was lost by the collaborator and is unrecoverable; affects 48 row(s). series_id for these sheets is a positional column index, so no column may be paired across day rows and no per-unit longitudinal or paired comparison is constructible (SOFIA-COMM-005).
- [igfbp1_day6_paired_zero_columns_possible_dropout] IGFBP-1 day-6 cells E5, F5, J5, K5 are recorded as measured non-detects per SOFIA-COMM-002, but the same two column positions read exactly zero in BOTH outlets after holding the highest day-3 values in both, which is more consistent with chip-level dropout than with secretion ceasing. Open question for the collaborator: were day-6 samples collected for all five IGFBP-1 chips? Until answered these four cells must not be used as evidence that secretion fell.

## Resolved by collaborator confirmation (2026-07-29)

- Units are pg/mL, collaborator-confirmed rather than assumed (SOFIA-COMM-001).
- A stored zero is a measured non-detect: absorbance was read and interpolation against the standard curve returned no detectable secretion (SOFIA-COMM-002).
- TOP is the apical/epithelial compartment and BOTTOM the basal/stromal compartment (SOFIA-COMM-003).
- The IGFBP-1 row labelled 'Day 7' is day 6 -- a workbook labelling error (SOFIA-COMM-003).
- Protocol day anchoring: days 0-2 are E2 10 nM for 48 h; days 2-6 add MPA 1 uM + cAMP 0.25 mM + XAV939 10 uM for 96 h; day 3 is 24 h and day 6 is 96 h into the cocktail (SOFIA-COMM-004).
- The treated condition is E2 + MPA + cAMP + XAV939. The workbook label 'HT (E2+P4+XAV939)' names P4 for MPA and omits cAMP; it is preserved verbatim and corrected in condition_normalized (SOFIA-COMM-004).
- Chips are not independent biological replicates, and the column-to-chip mapping for IGFBP-1 and PRL is lost. Known relations are recorded in config/adoc_chip_donor_provenance.tsv (SOFIA-COMM-005).
- Reported values are concentrations interpolated from a BLANK-SUBTRACTED absorbance ('abs muestra- abs control negativo'), so no further negative-control correction may be applied downstream (SOFIA-ANNO-001).
- Each well was assayed in 3 technical replicates, so every reported value is an aggregate of 3 wells. Technical replicates raise no biological n (SOFIA-ANNO-002).
- 1 mL of medium was collected per sample, and the PAEP perfusion flow rate was 30 uL/h (SOFIA-ANNO-003). These are collection metadata only; see the unresolved list for why they do not yield a rate.
- The day-0 sample is expansion medium and therefore precedes hormone addition, so it is a genuine pre-treatment baseline rather than an unverified one (SOFIA-ANNO-005).
- S10-2 shares its epithelial cell-source group with S7.1 and S7.2, so the 5 PAEP chips carrying values span at most 2 epithelial source groups. This TIGHTENED the independence ceiling (SOFIA-ANNO-007).
- For IGFBP-1 and PRL what was lost is the column ASSIGNMENT, not the chip set: the collaborator states 'Son estos pero no se cual es cual' in the source itself. Still no column may be assigned to a chip (SOFIA-ANNO-007).
- PRL was measured from the BOTTOM outlet: all six columns of the PRL sheet are basal/stromal, so no apical PRL series exists and the previously assumed first-three-TOP / last-three-BOTTOM split was wrong (SOFIA-COMM-006). This CONSTRAINS more than it licenses -- the day-6 magnitude asymmetry once read as a compartment difference lies entirely within the basal outlet -- and it does not touch the donor limitation: the column-to-chip mapping is still lost and no patient-specific inference becomes possible.

## Unresolved metadata

- Donor identity per chip. Only pairwise relations are known (S7.1 and S7.2 share patient sources; S11-1 and 'S11 2' are different patients; S10-2 unknown), so donor_id stays empty throughout and no chip is assigned a donor.
- Which epithelial and which stromal donor a given chip used: matching was attempted where possible but is not always the same patient, and the per-compartment mapping is unrecorded.
- The lost column-to-chip and column-to-patient mapping for IGFBP-1 and PRL is unrecoverable, so those columns cannot be paired across day rows.
- How the 3 technical replicates per well were combined (mean, median, or one-of-three). The COUNT is now known from the annotation workbook (SOFIA-ANNO-002); the aggregation function is not, so no dispersion, SD, CV or standard error is derivable from this dataset.
- Whether reported concentrations are already dilution-corrected (dilution_factor and dilution_corrected are left empty throughout). Review found all ten PAEP values are exact multiples of 1/69 and run 17x-1000x above the top standard of the workbook's own cached ELISA curves, so some uniform correction was applied upstream; the factor itself is unknown and is never asserted.
- Assay detection limits (detection_limit_pg_ml is left empty throughout). Values appear in context/adoc-paper-and-readout-context.md but are not traced to the supplementary methods, so they are not written into this table.
- The collection interval, and with it any concentration-to-secretion-rate conversion. Volume (1 mL) and flow rate (30 uL/h, PAEP sheet only) are now recorded from the annotation workbook, but they are MUTUALLY INCONSISTENT with the stated windows: 1000 uL / 30 uL/h = 33.3 h, neither the 48 h nor the 96 h medium named in the day legends. No hydraulic regime, per-channel split, cell count or secreting area is recorded, so no rate is derivable (SOFIA-ANNO-003).
- The day-0 accumulation window: the legend states a disjunction, 'medio de 48 h o 96 h'. It is never collapsed to one number or averaged, so collection_duration and both hours columns stay empty for day-0 rows.
- The composition of the expansion medium used for the day-0 baseline. It is a growth-factor-containing medium of unrecorded formulation, so the model comparator basal_maternal (all inputs OFF) is the closest available match rather than a verified equivalent.
- Whether a shared cell-source group means one patient or one isolate/passage. The PAEP independence ceiling was tightened from 4 to 3 on the conservative reading; if the groups are patients it drops to 2.
- Whether the S11 chips share a cell-source pairing or have one each. The annotation names a pairing for the family without splitting it, which neither confirms nor refutes the confirmed statement that S11-1 and S11-2 are different patients.
- What the date-formatted value at PAEP!I8 of the annotation workbook originally read. It sits under a line of cell-source tokens and appears to be an Excel-autoformatted code. Neither the value nor a reconstructed token is written into any committed artifact.
- PAEP sampling instant: PAEP rows record only 'HT (E2 only)' / 'HT (E2+P4+XAV939)' condition labels. The protocol maps each to a day window (protocol_phase) but not to a day.
- How many independent units the 6 PRL columns represent. All six are confirmed to be the BOTTOM outlet, but only 3 chip families are named for them, so the count is at most 3 and possibly fewer -- never 6.
- Which outlet the PAEP sheet was sampled from (apical, basal, or pooled); the sheet has no outlet axis.
- Whether day-6 samples were collected for all five IGFBP-1 chips. Two column positions read exactly zero in both outlets at day 6 after holding the highest day-3 values in both, which is more consistent with dropout than with secretion ceasing.
