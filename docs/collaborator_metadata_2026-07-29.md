# Collaborator metadata received 2026-07-29

Source: a communication from Sofía Zaragozano, relayed through a user request on
2026-07-29, followed later the same day by the annotation workbook it referenced.
This document is the durable record of what was asserted, what each assertion
became in the repository, and what the workbook then corroborated, refined or
left open.

A **later, separate communication on 2026-09-18** settled what PAEP's two
condition rows are — the protocol's proliferative and secretory phases, not
sampled days. It has its own record,
[`collaborator_metadata_2026-09-18.md`](collaborator_metadata_2026-09-18.md)
(`SOFIA-COMM-007`), and supersedes nothing here.

Every assertion is registered as an evidence record in
[`context/evidence-register.tsv`](../context/evidence-register.tsv) under the new
`SOFIA-COMM-*` family, with
`source_file = collaborator_communication:sofia_zaragozano:2026-07-29` — a
deliberately non-path token, so no validator mistakes it for a file — and
`status = verified_by_collaborator_corroborated_by_source_file` after
re-verification, distinct from the manuscript-backed `verified`. Facts that come
from the workbook itself are a separate `SOFIA-ANNO-*` family with a real
`source_file` path. Roles are assigned in
[`config/evidence_roles.yaml`](../config/evidence_roles.yaml).

The three canonical ADOC outlet tables are:

| Table | Grain | Rows |
|---|---|---|
| [`input_tables/adoc_secreted_proteins.tsv`](../input_tables/adoc_secreted_proteins.tsv) — alias `adoc_outlet_measurements` | one row per workbook data cell | 62 |
| [`config/adoc_outlet_conditions.tsv`](../config/adoc_outlet_conditions.tsv) | one row per protocol interval, sampled timepoint, or protocol note | 6 |
| [`config/adoc_chip_donor_provenance.tsv`](../config/adoc_chip_donor_provenance.tsv) | one row per chip, donor relation, unresolved mapping, or anomaly | 16 |

---

## The annotation workbook arrived the same day

`data/secreción proteinas ADOC anotaciones.xlsx` was received on 2026-07-29
(12,697 bytes, sha256 `400e291b773d95eba30e288be4d18d9ad530df4d2f2ea0f16ee13146e57e7481`).
It is **annotation metadata, not a second measurement source**: every numeric
cell is byte-identical to `data/proteinas secretadas ADOC.xlsx`, which remains
the only source of values.

**It is deliberately NOT committed.** Its shared strings carry the lab's own
cell-source codes and a collection date, this repository has a shared GitHub
remote, and `scripts/make_chatgpt_results_bundle.sh` exports `config/`,
`context/`, `docs/` and `input_tables/` to an external service. The file is
therefore gitignored and manifested locally — the same arrangement already used
for the 3.46 GB RDS — and only opaque repository-local donor labels
(`SRC-EPI-A`, …) plus source-cell coordinates are committed. The crosswalk
between label and code deliberately does not exist in this repository. See
`config/source_contract.yaml` `local_only_verification` and `donor_label_scheme`.

Accepted consequence: a clone without the file cannot pass
`check_data_manifest.py --check-hashes`. That is already true of the RDS.

**Auditability, stated honestly.** A reader with repository access alone can
verify the relational skeleton — how many source groups, which chips share one,
which mapping is unresolved — but not its correspondence to the source cells.
Every affected row names that dependency in `verification_requires_source_file`.
The trade-off is acceptable only because every claim those rows touch is a
*prohibition*: forbidden claims, replicate ceilings, `donor_id` staying empty.
An unverifiable ceiling errs toward claiming less. An unverifiable row that
*supported* a model claim would not be acceptable on the same terms, and none
does.

Its layout differs enough that it cannot be silently substituted for the
measurement workbook: the PRL sheet drops the trailing space, PAEP is
column-compacted with the S1/S2 columns deleted, and the data blocks are
row-offset. A positional read of PAEP misaligns 8 of 10 cells; keyed by chip
label it agrees exactly. `SHEET_PRL` keeps the measurement workbook's literal
trailing space so a substitution raises `KeyError` rather than misreading.

### Scope carve-out on "the workbook wins"

The re-verification path below says the workbook wins any conflict. That rule
presupposes an unambiguous conflict, and two cases show it needs scoping:

* the day-3/day-6 legends say `progesterona y estradiol` and mention neither
  cAMP nor XAV939. Applied literally the rule would revert the repository to the
  condition label the guard exists to forbid. Treated as loose bench shorthand
  and **not** adopted; the composition stays the reaffirmed, manuscript-sourced
  `E2 + MPA + cAMP + XAV939`.
* `PAEP!I4` names one source-group pairing for the S11 family without splitting
  it per chip, which neither confirms nor refutes the confirmed "different
  patients" statement. Recorded as an unresolved tension, not flipped.

**Revised rule: file-backed structure and metadata win; a free-text bench note
does not override an explicit correction.** Both exceptions are unratified and
listed in `config/evidence_roles.yaml` `open_questions`.

## What was confirmed, and where each assertion now lives

| Evidence | Assertion | Recorded as |
|---|---|---|
| `SOFIA-COMM-001` | Concentrations are in pg/mL. | `unit_basis=collaborator_confirmed` on all 62 rows; `unit` removed from `externally_asserted_fields`; the `unit_externally_asserted` warning retired. |
| `SOFIA-COMM-002` | A stored `0` is not missing data: absorbance was measured and interpolation against the standard curve indicated no detectable secretion. | `measurement_state=no_detectable_secretion` on 19 rows, `raw_value` kept at the stored `0`; the `zero_values_indistinguishable_from_below_detection` warning retired; two new validator rules reject recoding a zero as `observed` or as `missing`. |
| `SOFIA-COMM-003` | `TOP` = apical/epithelial, `BOTTOM` = basal/stromal. The row labelled `Day 7` is actually `Day 6`. | `compartment_semantics_basis` on all 62 rows; `time_resolution_note` restated as a labelling error rather than an endpoint convention. |
| `SOFIA-COMM-004` | Days 0–2 are E2 10 nM for 48 h; days 2–6 add MPA 1 µM + cAMP 0.25 mM + XAV939 10 µM for 96 h; day 3 is 24 h and day 6 is 96 h into the cocktail. The condition is `E2 + MPA + cAMP + XAV939`, not `E2 + P4 + XAV939`. | `protocol_phase` and `hours_after_cocktail_start` columns; `condition_normalized` and `condition_resolution_note`; `experimental_day_anchors` on the hormone-treatment steps of `config/protocols.yaml`; a repo-wide guard in `tests/unit/test_condition_label_guard.py`. |
| `SOFIA-COMM-005` | Donor provenance is only partially recoverable; chips are not independent biological replicates; the IGFBP-1/PRL column-to-chip mapping is lost. | `config/adoc_chip_donor_provenance.tsv`; the `biological_independence_contract` block of `config/secreted_protein_contract.yaml`; replicate ceilings on every affected `config/observation_model_map.tsv` row. |

### What the annotation workbook added (`SOFIA-ANNO-001` … `007`)

| Evidence | Fact | Effect |
|---|---|---|
| `SOFIA-ANNO-001` | Values are concentrations from a blank-subtracted absorbance (`abs muestra- abs control negativo`). | `value_derivation`; forbids a second negative-control correction downstream. |
| `SOFIA-ANNO-002` | 3 technical replicates per well. | `technical_replicate_n`; a COUNT, so `technical_replicate_id` stays empty, no n is raised, and no SD/CV/error bar is derivable. |
| `SOFIA-ANNO-003` | 1 mL collected (all sheets); 30 µL/h flow (PAEP sheet only). | `collected_volume`, `flow_rate`; **no rate** — 1 mL at 30 µL/h is 33.3 h, matching neither stated window. |
| `SOFIA-ANNO-004` | Day legends: day 2 = 48 h E2; day 3 = 24 h; day 6 = 96 h with 48 h medium. | Corroborates the hours anchors; the legend enumerates no día 7, supporting the Day-7 label error. |
| `SOFIA-ANNO-005` | Day 0 is expansion medium, before hormone addition. | Retires `day0_baseline_e2_exposure_unverified`; the window stays a `48 h o 96 h` disjunction. |
| `SOFIA-ANNO-006` | A stored 0 means no secretion (IGFBP-1 sheet only). | Corroborates the conclusion; `measurement_state_basis` records that it is operator-asserted, not a verified interpolation. |
| `SOFIA-ANNO-007` | Partial cell-source structure; the IGFBP-1 chip set is known but not its column order. | S10-2 shares an epithelial source with S7.1/S7.2, so the ceiling **tightened** from 4 to at most 2 epithelial groups. |

The five `SOFIA-COMM-*` records keep their `source_file` and `evidence_level`
unchanged — they were built on the collaborator's word with no file behind them,
and that stays historically true. Only their `status` moved, to
`verified_by_collaborator_corroborated_by_source_file`.

### Consistency with what the repository already held

The protocol was already correctly recorded and needed no correction:
`SOFIA-HT-001` and `config/protocols.yaml` both state
`10 nM E2 for 2 days then 10 nM E2 + 1 uM MPA + 250 uM cAMP + 10 uM XAV939 for 4 days`,
and 250 µM ≡ 0.25 mM. `IN_PROGESTIN` is already the generic node name with MPA
recorded in metadata. The genuinely new content is the **day-to-elapsed-hours
anchoring**, which existed nowhere.

### One distinction that was deliberately not collapsed

`SOFIA-COMM-003` confirms what an outlet **means**. It does not by itself confirm
**which columns** belong to which outlet. Those are separate claims, so the
canonical table carries them in separate columns:

- `compartment_semantics_basis` — collaborator-confirmed, all rows.
- `outlet_assignment_basis` — `workbook_merged_header` for IGFBP-1 (a real
  workbook fact), `sheet_level_collaborator_confirmed` for PRL
  (`SOFIA-COMM-006`, below), `sheet_level_context_document_unverified` for PAEP
  (no outlet axis exists, and still unconfirmed).

### PRL is entirely the BOTTOM outlet (`SOFIA-COMM-006`)

A later correction the same day: **PRL was measured from the BOTTOM outlet.** All
six columns are basal/stromal, so there is no apical PRL series and the
first-three-TOP / last-three-BOTTOM split taken from the context document was
wrong. `series_id` renumbers `PRL_BOTTOM_1..6` in column order B..G — note that
`PRL_BOTTOM_1..3` previously denoted columns E,F,G, so every mapping reference
was remapped in the same change and a test now resolves each `source_series_id`
against the table so the referent cannot drift silently again.

**It constrains more than it licenses.** The day-6 magnitude asymmetry that
looked like an apical/basal difference lies entirely *within* the basal outlet:

| claim | before | after |
|---|---|---|
| basal PRL detection (10 pg/mL limit) | 0/3, 1/3, 3/3 | **0/6, 1/6, 3/6** |
| day-6 "complete separation" | ">=5.4x" | **retracted** — min day 6 = 1.30 < max earlier = 113.60 (and the old ratio was really 5.35x) |
| `OM-015` apical-PRL censoring record | a silent control compartment | **three sub-limit columns of the primary readout** |
| `OM-007` apical-vs-basal check | trivially passing | **structurally undefined, retired** |

So "PRL is a late decidualization readout" is **weaker** as a calibration target
than it looked: half the basal columns are below the assay limit at the endpoint,
spanning 1.30–1465.44 pg/mL within one outlet on one day. Only the ordinal onset
order survives, and it is marginally better attested (day-0 non-detection now
rests on six sub-limit cells rather than three).

**And it vindicates a refusal.** The repository declined to infer PRL's split
from the day-6 asymmetry because `OM-007` tested that very inequality and would
have become circular. That inference would have been not merely circular but
*wrong*. The rule stays.

**Donor limitation untouched.** Confirming one outlet resolves the compartment,
never the replicate structure. Six columns against the three chip families named
in `LOST-002` is an unresolved count mismatch that *lowers* the plausible unit
count: `max_independent_units_prl` stays `not_determinable`, `donor_id` stays
empty, the column-to-chip mapping stays lost, and two new entries in
`forbidden_claims` block reading six columns as n=6 or pairing them within a
day.

---

## Where the review challenged the metadata

The user invited the reviewers to challenge any interpretation. Three challenges
were substantive and are recorded rather than silently applied — the
collaborator's stated defaults stand, with the objection visible next to them.

1. **The four IGFBP-1 day-6 zeros are probably dropout, not non-detects.**
   Cells `E5`, `F5`, `J5`, `K5` read exactly `0` in *both* outlets at the same
   two column positions, after those positions held the highest day-3 values in
   both (947.75 / 1513.00 apical, 9450.72 / 14726.98 basal). A fall from ~9–15
   ng/mL to exactly zero in both outlets of the same two columns is not credible
   as secretion ceasing. Recorded as the warning
   `igfbp1_day6_paired_zero_columns_possible_dropout` and in `OM-002`; those four
   cells must not be used as evidence that secretion fell until answered.

2. **Most of the PRL series is below the reported detection limit.** 14 of the
   18 values are under 10 pg/mL. One, 0.022709 pg/mL, is ~440× below it at five
   significant figures, implying standard-curve extrapolation outside the
   calibrated range. Recorded as `OM-015`. *Superseded in scope by
   `SOFIA-COMM-006`*: these are not an apical control series but three columns
   of the primary basal readout, which makes the finding more serious, and it
   retired `OM-007` outright rather than merely making it uninformative.

3. **`SOFIA-STR-001` says IGFBP-1 was undetectable at day 0; the workbook says
   otherwise.** Four of five basal values are 37.90–551.26 pg/mL against a
   5 pg/mL limit. The canonical decidualization literature (IGFBP-1 is measurable
   in undifferentiated stromal cells, unlike PRL) sides with the workbook. The
   conflict is recorded in `OM-002` rather than resolved by preferring one
   source.

Two smaller review findings are recorded in the transform docstring and the
unresolved list: the PAEP S1/S2 cells exist at the OOXML level and are
deliberately styled (rather than being wholly absent as the repository previously
stated), and all ten PAEP values are exact multiples of 1/69, proving an
undocumented uniform correction was applied upstream. The factor itself is
unknown and is **not** asserted; `dilution_factor` stays empty.

---

## Highest-value questions for the collaborator

In descending order of what they would unlock:

1. **Is column position stable across the day rows in the IGFBP-1 and PRL
   sheets**, even if chip identity is unrecoverable? A yes would legitimise
   longitudinal comparisons and repair `OM-003`/`OM-004`/`OM-005`. This is the
   single highest-leverage clarification available.
2. **Were day-6 samples collected for all five IGFBP-1 chips?** Determines
   whether `OM-002`'s support is 3/5 or 3/3, and whether the apparent day-6
   decline is an artifact.
3. **Which outlet was PAEP sampled from, and what was the dilution factor?**
   Resolves the last workbook-unsupported field in the only active calibration
   constraint.
4. **Does the day-0 outlet sample precede E2 addition?** `OM-002` maps day 0 to
   `basal_maternal`, which assumes it does.

---

## Re-verification path

**Executed 2026-07-29**; the outcome is recorded above and in
`config/source_contract.yaml` `previously_declared_unavailable_artifacts`. The
steps are retained for the next annotation workbook, with one rule amended: see
the scope carve-out above — file-backed structure and metadata win, a free-text
bench note does not override an explicit correction.

1. Copy the file into `data/` **unmodified**. Never edit, rename, or convert a
   file in `data/` in place.
2. Add a row to `config/data_manifest.tsv` with its real `size_bytes` and
   `sha256`, then verify:
   `python docs/codex/skills/adoc-data-audit/scripts/check_data_manifest.py --root . --check-hashes`
3. Move the `declared_but_unavailable_artifacts` entry in
   `config/source_contract.yaml` into `source_artifacts` with its real hash.
4. Re-verify **each** `SOFIA-COMM-*` record against the workbook. **On any
   conflict the workbook wins**, and the affected record is marked
   `status=superseded_by_file` — never silently edited.
5. Re-check these specifically, because each is currently recorded as unknown or
   lost and a workbook could change the answer:
   - the column-to-chip mapping for IGFBP-1 and PRL (currently **lost**);
   - S10-2's *stromal* source (its **epithelial** source is resolved: the
     workbook assigns it the same group as S7.1/S7.2, `REL-003`, which
     superseded the earlier "unknown"; the stromal side stays unannotated);
   - whether the header storing `S11` + U+00A0 + `2` really is the
     collaborator's `S11-2` (currently a reconciliation *hypothesis*, recorded in
     `config/adoc_chip_donor_provenance.tsv` as `CHIP-007`);

   - detection limits and the PAEP dilution factor;
   - whether the four IGFBP-1 day-6 zeros are non-detects or dropout.
6. Rebuild and revalidate:
   `pixi run build-protein-table`, then `pixi run test`, then
   `pixi run all-checks`.
7. Re-audit the supporting fractions and claim ceilings in
   `config/observation_model_map.tsv` and
   `docs/calibration_observation_audit.md`. If a donor mapping is recovered, the
   replicate ceilings recorded there become too strict and must be revised
   deliberately, with the new evidence cited.

---

## What these data still may not be used for

Unchanged by this integration, and in several respects tightened by it:

- MaBoSS transition rates, in any form. The day anchors are wall-clock bench
  time; MaBoSS time stays uncalibrated
  (`config/calibration.yaml: calibrated_physical_time: false`).
- Patient-level variability, standard errors, confidence intervals, paired-donor
  tests, personalization, or per-patient twins.
- Any `n`-based statistic treating chips or columns as independent, including
  reading `5/5` as five independent observations.
- Component-specific attribution to MPA, cAMP or XAV939. No single-agent arm
  exists, and `IN_XAV939` is additionally a zero-degree node in
  `adoc-literature-v0.2.0` and the v0.3.0 superset, so the simulated hormone
  response contains no XAV939 contribution at all (`OM-017`).
- Any within-column or paired longitudinal comparison for IGFBP-1 or PRL.
- Any apical PRL claim whatsoever -- there is no apical PRL series (`SOFIA-COMM-006`).
- Reading PRL's six single-outlet columns as six replicates, or pairing them with
  each other within a day (`OM-015`, `LOST-002`).
- Absolute-concentration, cross-protein, or cross-compartment magnitude claims:
  the PAEP dilution is unrecorded and collection volume, duration and flow rate
  are structurally empty, so a concentration cannot become a secretion rate.
- An "HT versus untreated" claim for any analyte. PAEP has an E2-only arm and no
  untreated arm; IGFBP-1 and PRL have a pre-treatment arm and no E2-only arm, so
  the two comparator designs do not overlap.

What they **do** support is qualitative direction, compartment and temporal
constraints — which is how every mapping row above is scoped.
