# Source data

This directory is the immutable source layer for DT_ADOC. Do not rename, edit,
normalize in place, or reorganize these files. Derived tables belong in a
versioned output directory and must point back to the source hash in
`config/data_manifest.tsv`.

## ADOC study sources

- `2 Zaragozano et alClean copy.docx`: Sofia Zaragozano and colleagues'
  manuscript, including methods, quantitative results, and figure legends.
- `1 Supplementary_materials_Zaragozano et al Clean.docx`: supplementary
  methods and figures.
- `sciadv.adz2249.pdf`: published ADOC article.
- `combined-dataset-patient-integration.rds`: intermediate integrated Seurat
  object from three donors under control and hormone-treated conditions.
- `proteinas secretadas ADOC.xlsx`: PAEP, PRL, and IGFBP-1 measurements.

## Modeling references

- `Montagud et al. - 2022 - Patient-specific Boolean models of signalling
  networks guide personalised treatments.pdf`: reference workflow for
  generic-model construction, PROFILE personalization, MaBoSS simulation, and
  graded perturbation with PROFILE_v2.
- `Montagud - 2026 - Systems biology at the body scale Toward adaptive digital
  twins in precision medicine.pdf`: long-term digital-twin context. It does not
  define phase-1 acceptance criteria.

The authoritative machine-readable inventory is
[`../config/data_manifest.tsv`](../config/data_manifest.tsv).

## Canonical ADOC secreted-protein table

> **Two workbooks, one measurement source.** `proteinas secretadas ADOC.xlsx` is
> the only source of values. `secreción proteinas ADOC anotaciones.xlsx`
> (received 2026-07-29) is annotation metadata whose numeric cells are
> byte-identical; it is **gitignored** because it carries the lab's own
> cell-source codes, and its facts reach the canonical table through the
> committed transcription in `config/adoc_outlet_conditions.tsv` rather than
> being read directly, so the build stays reproducible on a clone that lacks it.
> The table below is also the record requested as `adoc_outlet_measurements`;
> its companions are `config/adoc_outlet_conditions.tsv` (protocol intervals and
> treatment concentrations) and `config/adoc_chip_donor_provenance.tsv` (chip,
> donor and uncertainty). See `docs/collaborator_metadata_2026-07-29.md`.

`proteinas secretadas ADOC.xlsx` (sha256
`e60f73c45746b7e1bde46f9d41fb8e55885fcbf33802ef2f4427f0700e161192`, see
`config/data_manifest.tsv`) is transformed into a tidy, one-row-per-workbook-
cell table rather than read ad hoc from downstream code:

- Canonical table: `input_tables/adoc_secreted_proteins.tsv`
- Contract: [`../config/secreted_protein_contract.yaml`](../config/secreted_protein_contract.yaml)
- Validation report: `input_tables/adoc_secreted_proteins_validation.md`
  (regenerated alongside the table)
- Build command: `pixi run build-protein-table` (implemented in
  `src/dt_adoc/data/secreted_proteins.py`, exposed as `dt-adoc
  build-protein-table`)

**This canonical table and its contract now supersede
[`../docs/data-context/adoc-secreted-proteins.md`](../docs/data-context/adoc-secreted-proteins.md)
as the operational source of truth.** Downstream analysis, calibration, and
figure code should read the table, not the prose document. The document
remains only as provenance and historical context for the interpretation
decisions the table encodes.

### Discrepancies encoded, not papered over

- `PAEP` carries no assignable time axis: its two data rows are the workbook's
  own verbatim labels for hormone-treatment conditions
  (`HT (E2 only)`, `HT (E2+P4+XAV939)`), not days, and `resolved_protocol_day`
  is left empty for every PAEP row rather than guessed. The second label is
  wrong twice: the progestin was MPA 1 uM, not P4, and the label omits cAMP
  0.25 mM (`config/observation_model_map.tsv`, OM-001). What those two rows are
  was confirmed by the collaborator on 2026-09-18 (`SOFIA-COMM-007`): `HT` is
  hormone treatment, the E2-only row is the proliferative-phase arm and the
  full-hormone row the secretory-phase arm. So **no sampled day is assignable on
  current evidence** — the conservative claim, not that a sampling instant could
  never be confirmed. The annotation workbook's `Día` legends on its PAEP sheet
  are transcribed onto the two interval rows of
  `config/adoc_outlet_conditions.tsv` and must never by themselves be mapped
  onto a PAEP measurement row; an explicit confirmation of PAEP sampling timing
  would be new evidence, and the day columns are already there to carry it. See
  [`../docs/collaborator_metadata_2026-09-18.md`](../docs/collaborator_metadata_2026-09-18.md).
- PAEP chips `S1` and `S2` have column headers but the corresponding data
  cells carry no value. (At the OOXML level the cell elements exist and are
  deliberately styled with the same highlight fill as their headers; only the
  value is absent.) Those cells appear as `measurement_state=missing` rows
  tagged `quality_tier=exploratory`, which is a different state from a stored
  zero. The collaborator confirmed on 2026-09-18 (`SOFIA-COMM-007`) that she
  left them blank because those two chips are much older and she did not trust
  their data, so `quality_tier` is no longer an external assertion for them.
- The compartment basis is split across **two** columns, because two logically
  independent claims were previously conflated. `compartment_semantics_basis`
  records what an outlet means (TOP = apical/epithelial, BOTTOM = basal/stromal)
  and is `collaborator_confirmed_top_apical_bottom_basal` on every row.
  `outlet_assignment_basis` records which columns are which outlet, and is
  `workbook_merged_header` for `IGFBP-1` (a real workbook fact: merged
  `B2:F2`/`G2:K2`), `sheet_level_collaborator_confirmed` for `PRL` (the sheet has
  no header row, but the collaborator confirmed all six columns are the BOTTOM
  outlet -- `SOFIA-COMM-006`), and `sheet_level_context_document_unverified` for
  `PAEP` (the sheet has no outlet axis at all). **PAEP is now the only row set
  with an unverified outlet assignment**, which makes its warning more important,
  not less.
- Neither `IGFBP-1` nor `PRL` carries chip identifiers anywhere in the
  workbook, and the collaborator confirmed the column-to-chip and
  column-to-patient mapping for both sheets is **lost**. `chip_id` is left empty
  for those sheets and a positional `series_id` (e.g. `IGFBP-1_BOTTOM_3`) is
  used instead, which must never be read as a chip or followed across day rows.
- `IGFBP-1`'s third day is labelled `Day 7` in the workbook; `PRL`'s
  equivalent day is labelled `Day 6`. Both resolve to
  `resolved_protocol_day=6`: the collaborator confirmed the `Day 7` label is an
  error, not an endpoint convention. `source_time_label` preserves the original
  label verbatim.
- Units (`pg/mL`) are not recorded anywhere in the workbook but are
  collaborator-confirmed, recorded as `unit_basis=collaborator_confirmed`.
- Stored zeros are **measurements**: absorbance was read and interpolation
  against the standard curve returned no detectable secretion. They carry
  `measurement_state=no_detectable_secretion` with `raw_value` kept at the
  stored `0` — never blank, never `NA`, and distinct from both
  `below_detection` (a censored value) and `missing` (no measurement exists).
- `condition` preserves the workbook's own condition label unchanged, even
  though that label is wrong twice over (it names `P4` where the progestin was
  MPA, and omits cAMP). `condition_normalized` carries the corrected identifier
  and `condition_resolution_note` records the discrepancy.
- `externally_asserted_fields` names, per row (pipe-delimited), which other
  column values are still asserted from the context document **alone** —
  neither workbook-supported nor collaborator-confirmed. Absence from the list
  means one of those two, never "unsupported"; read the `*_basis` columns to
  tell them apart. **Which fields those currently are is
  `externally_asserted_fields_current` in the contract**, not this sentence:
  the builder fails if the emitted column disagrees with it. A field leaves the
  list when a named confirming source arrives — `unit` did (`SOFIA-COMM-001`),
  PRL's outlet did (`SOFIA-COMM-006`), and the `S1`/`S2` `quality_tier` did
  (`SOFIA-COMM-007`).

### Fields the workbook cannot support

`donor_id`, `technical_replicate_id`, `assay_well_id`, `collected_volume`,
`collection_duration`, and `flow_rate` are real, always-empty columns rather
than omitted fields: the workbook has no evidence for any of them, and they
are never populated with a guess. Their emptiness is enforced by
`validate_secreted_protein_table()`.

### Unresolved metadata

Donor identity per chip, ELISA well/technical-replicate structure, whether
concentrations are already dilution-corrected, assay detection limits,
collection volume/duration/flow rate, and the PAEP sampling instant are all
unavailable from the source file. These are listed explicitly in the
generated validation report rather than being inferred, alongside a companion
list of what the 2026-07-29 collaborator confirmation resolved; see
`input_tables/adoc_secreted_proteins_validation.md` after running the build
command and `docs/collaborator_metadata_2026-07-29.md` for the provenance of
each confirmation.

Donor provenance deserves its own note. Chips are **not** independent
biological replicates: several can share cells from the same patients, and
epithelial and stromal cells within one chip do not always come from the same
patient. `donor_id` therefore stays permanently empty — only *relations* are
partly known, never identities — and those relations are recorded in
`config/adoc_chip_donor_provenance.tsv`.

### Validation status vocabulary

`validate_secreted_protein_table()` reports `structurally_valid` /
`structurally_invalid`, deliberately not `valid`/`invalid`. This status
asserts schema/contract conformance and traceability to the source workbook
only. **It does not assert that outlet-column assignment, replicate structure,
or donor provenance are resolved.** Those open questions are always surfaced as
`warnings` (never errors, since they are ambiguities in the *source*, not
defects in the table) — currently: PRL's unverified outlet column positions,
PAEP's unverified sheet-level outlet, partially-unknown chip donor
independence, the lost IGFBP-1/PRL column-to-chip mapping, and the IGFBP-1
day-6 paired zeros that may be chip dropout. Units and zero semantics are no
longer among them: both were collaborator-confirmed on 2026-07-29. Each warning
carries a bracketed key that must appear in the contract's
`warning_conditions`, so the list cannot drift into stale prose. See the
validation report's Warnings section for the current counts.

### Limitations

- The workbook offers no finer granularity than one value per data cell; no
  assay-well-level data exists to build a finer table from.
- Reported concentrations are not secretion rates: no collection volume,
  duration, or flow rate is available to convert between the two.
- `input_tables/` is a derived-output directory rebuilt from the immutable
  workbook; it is intentionally not added to `config/data_manifest.tsv`,
  which hashes only the immutable source layer under `data/` and would need
  re-hashing on every legitimate rebuild.
