# ADOC secreted-protein data context

## Purpose

This document records the current interpretation of the ADOC secreted-protein datasets so repository agents can use them consistently while the raw workbooks are converted into well-annotated input tables.

This is a **temporary migration aid**, not the intended long-term source of truth.

Agents should transform the source workbooks into explicit, tidy input tables containing the necessary metadata. Once that transformation is complete and validated, downstream code should read the annotated tables directly rather than depend on prose in this document.

---

## Experimental context

The ADOC system contains epithelial and stromal compartments.

Secreted proteins were measured from outlet samples collected at defined stages of the hormone-treatment protocol.

| Protein | Primary compartment | Biological interpretation |
|---|---|---|
| PAEP | Epithelial / TOP outlet | Secretory epithelial differentiation and receptivity-associated state |
| IGFBP-1 | Stromal / BOTTOM outlet | Stromal decidualization |
| PRL | Stromal / BOTTOM outlet | Stromal decidualization |

IGFBP-1 values from the TOP outlet were included as a compartment control. The biologically relevant decidualization
readout is the BOTTOM outlet.

> **Corrected 2026-07-29 (`SOFIA-COMM-006`).** PRL has **no** TOP series: the
> collaborator confirmed the whole PRL sheet was measured from the BOTTOM
> outlet. All six PRL columns are basal/stromal. The statement below that its
> first three columns are TOP is **wrong** and is kept only as a record of what
> was superseded.

All three proteins are reported in **pg/mL**, collaborator-confirmed on
2026-07-29 (`SOFIA-COMM-001`). The workbook itself records no unit anywhere,
so this is an external assertion with a named source, not a workbook fact.

No inlet protein measurements are available.

The target proteins were not intentionally added to the inlet medium. Their presence in outlet samples is therefore consistent with cellular secretion, but the inlet concentration was not experimentally measured and must not be represented as confirmed zero.

---

## Hormonal treatment

The treatment medium contains:

| Compound | Concentration |
|---|---:|
| E2 | 10 nM |
| cAMP | 250 µM |
| MPA | 1 µM |
| XAV939 | 10 µM |

E2 alone is associated with the proliferative phase.

The combined hormone treatment is intended to induce the secretory/receptive epithelial state and stromal decidualization.

These concentrations come from previously described treatment protocols. Receptor saturation has not been experimentally demonstrated in this dataset.

For Boolean or qualitative models, represent the treatment as an active or high hormonal input. Do not interpret it as proven 100% receptor occupancy.

---

## Time points

The collaborator confirmed the following interpretation for the Emulate data:

| Resolved day | Meaning |
|---:|---|
| 0 | Before hormone treatment; cells maintained in expansion medium |
| 3 | During treatment |
| 6 | After completion of treatment; expected secretory-phase peak |

Some workbook labels may show `Day 7`, especially for IGFBP-1. The collaborator subsequently confirmed that the intended endpoint for these data is **day 6**.

Do not overwrite the original workbook label silently.

Processed tables should preserve both:

```text
source_time_label = "Day 7"
resolved_protocol_day = 6
time_resolution_note = "Collaborator confirmed endpoint as day 6"
```

If exact treatment duration differs from protocol day, preserve both:

```text
protocol_day
treatment_duration_days
```

Do not infer treatment duration unless explicitly supported by metadata.

---

## PAEP dataset

### Interpretation

PAEP was measured from the epithelial outlet and reflects the transition toward a secretory epithelial state.

`HT` means hormone treatment.

The collaborator described the broad treatment sequence as:

1. E2-associated proliferative phase;
2. combined hormone treatment;
3. expected secretory/receptive peak with increased PAEP secretion.

### Chip identifiers

Labels such as `S11` and `S12` are chip identifiers.

Older chip identifiers such as `S1` and `S2` may be present but empty because the collaborator did not trust those older measurements sufficiently to include the values.

Empty `S1` and `S2` fields must therefore be represented as **missing or excluded**, not as zero.

### Control limitation

The current PAEP dataset does not contain a sufficiently reliable day-0 control for all recent chips.

Older data with a day-0 reference may exist but are considered lower quality.

Use the recent PAEP data primarily for:

- qualitative or ordinal comparison;
- secretory-state direction;
- within-chip comparisons when mapping is available.

Do not use old and recent chips as one homogeneous quantitative cohort unless batch and quality differences are explicitly represented.

---

## IGFBP-1 dataset

### Compartment

- `TOP`: **apical / epithelial** outlet; included mainly as a compartment
  control.
- `BOTTOM`: **basal / stromal** outlet; primary decidualization readout.

The apical/basal anatomy was confirmed on 2026-07-29 (`SOFIA-COMM-003`). That
confirmation covers what an outlet **means**, not by itself **which columns** are
which, and the canonical table keeps the two claims in separate columns
(`compartment_semantics_basis` and `outlet_assignment_basis`) for that reason.
Per sheet: IGFBP-1's split is a workbook fact (merged headers `B2:F2` / `G2:K2`);
PRL is entirely the BOTTOM outlet, confirmed separately the same day
(`SOFIA-COMM-006`); and **PAEP's sheet-level outlet remains the only unverified
one**.

### Replicates

> **Corrected 2026-07-29 (`SOFIA-COMM-005`).** The two statements this section
> previously made -- that each column is a different chip, and that a chip is an
> independent biological replicate -- are both **wrong**. They are kept here only
> as a record of what was superseded.

For **PAEP**, each column is a chip. For **IGFBP-1** and **PRL** the
column-to-chip and column-to-patient mapping was **lost** and is unrecoverable:
neither sheet carries a chip identifier in any cell, and the PRL sheet has no
header row at all. `series_id` for those sheets is a positional column index and
must never be read as a chip, a donor, or a unit that can be followed across day
rows.

A chip is **not** an independent biological replicate. Several chips can share
cells from the same patients; one chip is not one independent patient; and
epithelial and stromal cells within a chip do not always come from the same
patient, although matching was attempted where possible. The known relations are
recorded in [`config/adoc_chip_donor_provenance.tsv`](../../config/adoc_chip_donor_provenance.tsv):
S7.1 and S7.2 share patient sources, S11-1 and `S11 2` are different patients,
and S10-2 shares its *epithelial* source group with S7.1/S7.2 (`REL-003`,
superseding the earlier "unknown" once the annotation workbook arrived). The 5
PAEP chips carrying values therefore span **at most 3 independent units and at
most 2 epithelial source groups** -- a ceiling, not a count. Both figures are
*quoted here for the reader* from `max_independent_units_paep_observed` and
`max_independent_epithelial_source_groups_paep` in
[`config/secreted_protein_contract.yaml`](../../config/secreted_protein_contract.yaml),
which is the single source of truth. Code, generated artifacts and tests must
read them from the contract and must never hardcode a copy: a hardcoded copy is
exactly how the superseded "at most 4 donor groups" survived in four places
after `SOFIA-ANNO-007` tightened it.

Donor *identity* is unknown for every chip; only *relations* are partly known.
`donor_id` stays permanently empty and must never be backfilled.

A chip must not automatically be called a technical replicate.

Technical replicates are repeated measurements of the same collected sample, such as:

- repeated ELISA wells;
- repeated optical-density reads;
- multiple dilutions of the same sample.

If the same sample was measured more than once, those measurements must be identified separately and collapsed or modelled at the technical-replicate level before biological inference.

### Expected biological trend

The intended calibration trend is:

```text
BOTTOM IGFBP-1:
day 0 < day 3 < day 6
```

This can be used to evaluate progressive stromal decidualization.

---

## PRL dataset

PRL follows the same time points as IGFBP-1, but **not** the same compartment
logic.

> **Corrected 2026-07-29 (`SOFIA-COMM-006`).** All six PRL columns were measured
> from the **BOTTOM** outlet, so every PRL value is basal/stromal and there is no
> apical PRL series. The superseded statement is kept below as a record of what
> was believed.

Superseded: *"the first three columns are TOP; the last three columns are
BOTTOM."* That split came from this document, not from the workbook -- the PRL
sheet has no header row -- and it was wrong.

`series_id` therefore renumbers `PRL_BOTTOM_1..6` in workbook column order B..G.
Note the hazard this created: `PRL_BOTTOM_1..3` previously denoted columns E,F,G
and now denote B,C,D, so every mapping reference was remapped in the same change
and a test resolves each `source_series_id` against the canonical table.

The intended calibration trend was:

```text
BOTTOM PRL:
day 0 < day 3 < day 6
```

**It does not hold as stated.** Against the 10 pg/mL limit, basal detection is
0/6 at day 0, 1/6 at day 3 and only 3/6 at day 6, and the day-6 values span
1.30-1465.44 pg/mL -- a 1125-fold range within one outlet on one day. The
ordinal onset order survives; uniform induction does not. See `OM-014` and
`OM-015`.

Confirming a single outlet resolves the compartment, **never** the replicate
structure: three chip families are named for six columns, so the plausible
independent-unit count is at most 3 and never 6, and columns must not be pooled
or paired with each other.

---

## Replicate terminology

Use the following definitions consistently:

| Level | Definition |
|---|---|
| Donor | Biological source individual |
| Chip | Independent experimental device |
| Biological replicate | Independent donor. An independently prepared chip does **not** qualify: chips can share patient sources (`SOFIA-COMM-005`) |
| Technical replicate | Repeated assay of the same collected biological sample |
| Dilution replicate | Different dilution of the same sample; not an independent biological observation |

Do not increase biological sample size by counting repeated ELISA wells or multiple dilutions as independent chips.

The mapping between chip and donor remains important. If several chips derive from the same donor, donor and chip effects must be represented separately.

---

## Units, dilution and normalization

The reported units are:

```text
pg/mL
```

For each value, the processed table should explicitly record whether it is:

- raw optical density;
- blank-corrected optical density;
- concentration interpolated from the standard curve;
- concentration before dilution correction;
- concentration after dilution correction;
- mean of technical wells;
- normalized to volume, time, cell number or chip area.

Different dilutions of the same sample are not independent observations.

A dilution-corrected concentration should be represented explicitly:

```text
measured_concentration_pg_ml
dilution_factor
reported_concentration_pg_ml
dilution_corrected = true | false
```

Do not multiply by the dilution factor twice.

### Concentration versus secretion rate

Outlet concentration is not equivalent to secretion rate.

A secretion-rate estimate would require at least:

```text
outlet concentration
collected volume
collection duration
flow rate
inlet/background concentration
```

Because these metadata are not currently available, use the data as outlet concentrations or relative secretion readouts, not as absolute production rates.

---

## Zeros, non-detects and missing values

**Resolved for this dataset on 2026-07-29 (`SOFIA-COMM-002`).** A stored `0`
means absorbance was measured and interpolation against the standard curve
returned **no detectable secretion**. It is a measurement, not a missing value
and not a censored one. The canonical table records it as
`measurement_state=no_detectable_secretion` with `raw_value` kept at the stored
`0`, which is distinct from both `below_detection` (censored) and `missing`
(no measurement exists).

The generic possibilities below no longer apply to this workbook and are kept
only for future assays: true numeric zero; below the assay detection limit;
manually encoded non-detect; missing value converted to zero; blank or
background control.

One caveat survives the confirmation. IGFBP-1's day-6 cells `E5`, `F5`, `J5` and
`K5` read exactly zero in **both** outlets at the same two column positions,
after those positions held the highest day-3 values in both. That is more
consistent with chip-level dropout than with secretion ceasing, so the
validation report raises
`igfbp1_day6_paired_zero_columns_possible_dropout` and those four cells must not
be used as evidence that secretion fell until the collaborator confirms whether
day-6 samples were collected for all five chips.

Processed data should distinguish:

```text
measurement_state =
  observed
  below_detection
  missing
  excluded
  blank_control
  out_of_range
```

Recommended fields:

```text
raw_value
reported_value_pg_ml
detection_limit_pg_ml
measurement_state
imputation_value_pg_ml
```

Do not compute fold changes from an exact zero without a documented rule.

If an exploratory substitution such as `LOD / 2` is used, retain the original non-detect state and document the substitution.

---

## Inlet interpretation

No inlet measurements are available for PAEP, PRL or IGFBP-1.

The correct statement is:

> These proteins were not intentionally added to the inlet medium, and the inlet was not experimentally measured.

Do not state:

> The inlet concentration was experimentally confirmed as 0 pg/mL.

No other inlet or outlet molecular measurements are currently available from this dataset.

---

## Imaging interpretation

Secreted-protein imaging captures cells actively secreting at the fixation time.

It does not measure:

- all cells capable of secretion;
- cumulative secretion over the full protocol;
- secretion rate per cell;
- the fraction of cells that secreted at any point during treatment.

Final-treatment images were acquired when the probability of detecting active secretion was expected to be highest.

Therefore:

- imaging is an instantaneous readout;
- outlet ELISA integrates secretion over a collection interval;
- the two readouts should not be interpreted as directly equivalent.

---

## Adhesion-related interpretation

PAEP, PRL and IGFBP-1 are not direct adhesion measurements.

They provide evidence for upstream or supporting biological states:

```text
PAEP
→ secretory/receptive epithelial state

PRL + IGFBP-1
→ stromal decidualization
```

Direct adhesion validation should rely on:

- stable embryo-attachment counts;
- attachment timing;
- resistance to flushing;
- perturbations such as mifepristone;
- coordinated changes in receptivity-associated markers.

Markers reported or analysed in relation to epithelial receptivity and mifepristone include:

- PAEP;
- SPP1;
- IL1B;
- HOXA11;
- glycoproteins;
- secretoglobins.

Do not treat any single marker as proof of adhesion competence.

---

## Recommended canonical input table

Agents should convert source spreadsheets into one tidy table per observation, preferably one row per assay well before aggregation.

Recommended schema:

```text
dataset_id
source_file
source_sheet
source_row
source_column
source_label
donor_id
chip_id
sample_id
protein
compartment
outlet
condition
protocol_day
source_time_label
resolved_protocol_day
treatment_duration_days
collection_start
collection_end
collection_duration
flow_rate
collected_volume
technical_replicate_id
assay_well_id
dilution_factor
raw_od
blank_corrected_od
measured_concentration_pg_ml
reported_concentration_pg_ml
dilution_corrected
unit
detection_limit_pg_ml
measurement_state
quality_tier
exclusion_reason
resolution_note
```

Not every field must be populated immediately. Unknown values should remain explicit missing values rather than being inferred.

Use controlled values where possible:

```text
compartment:
  epithelial
  stromal

outlet:
  top
  bottom

condition:
  pretreatment
  hormone_treatment
  mifepristone
  other

measurement_state:
  observed
  below_detection
  missing
  excluded
  blank_control
  out_of_range

quality_tier:
  primary
  exploratory
  excluded
```

---

## Required data-transformation behaviour

Agents working on these data must:

1. Inspect the workbook structure before transforming values.
2. Preserve the original workbook labels and coordinates.
3. Create explicit chip, donor, compartment, time and condition fields.
4. Keep TOP and BOTTOM values separate.
5. Distinguish biological and technical replicates.
6. Preserve dilution factors and correction status.
7. Preserve non-detects and missing values as distinct states.
8. Resolve `Day 7` to protocol day 6 only with an explicit note.
9. Mark old or distrusted PAEP chips as exploratory or excluded.
10. Produce a validation report listing unresolved metadata.
11. Avoid silently filling unknown donor, chip or assay metadata.
12. Write downstream analyses against the canonical annotated tables, not workbook positions or this prose document.

---

## Source-of-truth migration rule

This document should become unnecessary.

The intended hierarchy is:

```text
raw workbook
→ canonical annotated input table
→ schema/contract validation
→ analysis-ready table
→ model calibration and figures
```

After the canonical table is created and validated:

- analysis code must use the table;
- figure code must use the table;
- model calibration must use the table;
- repository agents should treat the table and its schema as the source of truth;
- this document should remain only as provenance and historical context.

Do not duplicate these semantics independently across scripts.

---

## Remaining metadata to request or resolve

The following items remain useful to clarify:

Items 1, 2, 7, 11 and 12 were answered on 2026-07-29; see
[`docs/collaborator_metadata_2026-07-29.md`](../collaborator_metadata_2026-07-29.md)
for what was confirmed and what each answer became. The list below is what
remains:

1. Donor identity per chip. Only pairwise relations are known, and the
   column-to-chip mapping for IGFBP-1 and PRL is **permanently lost**.
2. Which epithelial and which stromal donor a given chip used.
3. Number of ELISA wells per sample.
4. How technical replicates were averaged.
5. Whether reported concentrations are already dilution-corrected. Review found
   all ten PAEP values are exact multiples of 1/69 and run far above the top
   standard of the workbook's own cached ELISA curves, so a uniform correction
   was applied upstream; the factor is unknown and is never asserted.
6. Whether blank subtraction was performed.
7. Assay detection limits used for each workbook. Values appear in
   `context/adoc-paper-and-readout-context.md` but are not traced to the
   supplementary methods, so `detection_limit_pg_ml` stays empty.
8. Collection interval and volume; flow rate. This also leaves it undetermined
   whether the day-0 sample precedes E2 addition.
9. Which outlet PAEP was sampled from. (The PRL half of this question was
   answered on 2026-07-29: the whole sheet is BOTTOM.)
10. Whether day-6 samples were collected for all five IGFBP-1 chips.
11. Whether older PAEP data should be exploratory or fully excluded.

Unresolved fields must be represented in the canonical table and validation report rather than hidden.

---

## Agent decision rules

Use these defaults unless stronger repository evidence exists:

- Prefer BOTTOM PRL and IGFBP-1 for decidualization. All PRL is BOTTOM.
- Keep IGFBP-1 TOP values as controls; there is no PRL TOP series.
- Use day 0, day 3 and resolved day 6.
- Treat `Day 7` as a source label resolved to day 6: the collaborator confirmed
  the label is an error, not an endpoint convention.
- Treat empty old PAEP chips as missing or excluded, not zero.
- Treat a stored zero as a measured non-detect, never as `NA`.
- **Never** treat a chip as an independent experimental or biological unit, and
  never invent the lost IGFBP-1/PRL column-to-chip mapping. The former default
  ("independent until donor mapping shows otherwise") is inverted: donor mapping
  has shown otherwise.
- Describe the treated condition as `E2 + MPA + cAMP + XAV939`. The workbook
  label `HT (E2+P4+XAV939)` is a verbatim source string, wrong twice over, and is
  never a description of the experiment.
- Do not count assay wells or dilutions as biological replicates.
- Treat outlet values as concentrations, not secretion rates.
- Treat inlet target-protein concentration as unmeasured.
- Use the smallest defensible assumption and record it explicitly.
