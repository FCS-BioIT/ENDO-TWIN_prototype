# Collaborator metadata received 2026-09-18 — PAEP conditions

Source: a second communication from Sofía Zaragozano, relayed through a user
request on 2026-09-18, about the `PAEP` sheet of
`data/proteinas secretadas ADOC.xlsx`. It arrived with **no attachment**: unlike
the 2026-07-29 communication, no workbook followed it, and none can corroborate
it — the annotation workbook's PAEP sheet records day legends, not condition
semantics.

It is registered as a single evidence record, `SOFIA-COMM-007`, in
[`context/evidence-register.tsv`](../context/evidence-register.tsv) with
`source_file = collaborator_communication:sofia_zaragozano:2026-09-18` and
`status = verified_by_collaborator_no_file_corroboration` — the weaker status
already used for `SOFIA-COMM-006`, for the same reason. Its role is
`construction` in [`config/evidence_roles.yaml`](../config/evidence_roles.yaml):
it fixes how the canonical table is *read*, and deliberately not `calibration`
(see "What is recorded as rationale, not evidence" below).

This document is the companion to
[`collaborator_metadata_2026-07-29.md`](collaborator_metadata_2026-07-29.md),
which remains the record of the first communication and the annotation workbook.
Nothing there is superseded.

---

## What was asserted

Quoted exactly as relayed, including its spacing, its repeated word and its
missing accents — this is the only artifact behind the record, so it is not
tidied:

> HT es hormonal treatment, solo con E2 , que es fase proliferativa y con el
> resto de hormonas que es fase secretora , que supuestamente es cuando se
> produce el pico de receptividad y por tanto de secreción de de PAEP, con
> respecto al control , justo de este no teniamos día cero, pero tengo otros más
> viejos que si, lo que pasa que los datos no están tan finos pero si quieres te
> lo paso para que te hagas una idea
>
> S11, S12, son los identificativos de las diferentes chips que analice. S2 y S1
> están en blanco porque no añadí al final los valores, porque eran chips mucho
> más antiguos y no me fiaba de lo datos.

| Assertion | Recorded as |
|---|---|
| `HT` is hormone treatment. The E2-only row is the **proliferative** phase; the full-hormone row is the **secretory** phase. | `condition_resolution_note` on all 14 PAEP rows; the phase statement is added to `COND-E2-PRIMING` and `COND-FULL-COCKTAIL` in [`config/adoc_outlet_conditions.tsv`](../config/adoc_outlet_conditions.tsv), which now cite `SOFIA-COMM-007`. |
| The two PAEP rows are therefore **conditions, not sampled days**, so no day is assignable to them on the evidence held. | `time_resolution_note` on all 14 PAEP rows; the `paep_conditions_are_phases_not_timepoints` check in `src/dt_adoc/data/secreted_proteins.py`; the contract comment above `time_label_resolution_rule` in [`config/secreted_protein_contract.yaml`](../config/secreted_protein_contract.yaml). |
| This experiment had **no day-0 control**. | Nothing changed: `OM-001`'s claim ceiling already states that no untreated PAEP arm exists in the source workbook. The statement corroborates it. |
| `S1` and `S2` are blank **deliberately** — much older chips whose data she did not trust. | Nothing changed in `exclusion_reason`'s substance, which already said this from the context document. It now names `SOFIA-COMM-007`, and `quality_tier` is no longer listed in `externally_asserted_fields` for those four rows, because it now has a named confirming source. |

## What this settles, and how far

The repository already left `resolved_protocol_day` empty for PAEP, recording
that as a **gap in the workbook** — "the workbook records no protocol day for
PAEP", a day window without a sampling instant. `SOFIA-COMM-007` answers what
the two rows *are*: the design's two arms. It does **not** establish that a
sampling instant could never exist or be recovered, and nothing here claims
that. The invariant this record fixes is the conservative one:

> **No sampled day is assignable to a PAEP row on current evidence, and the
> workbook's day legends alone must never be used to backfill one.**

An explicit collaborator confirmation of PAEP sampling timing would be new
evidence. It would be registered as its own record, the day columns are already
in the schema to carry it, and the builder check below would be revised
deliberately alongside it. Three consequences follow. The first is enforced by
the builder; the other two are statements about scope, recorded here and in the
evidence register:

1. **`resolved_protocol_day`, `hours_after_cocktail_start` and
   `hours_after_e2_start` are empty for PAEP** and may not be backfilled from
   the legends. The trap is specific: the annotation workbook's PAEP sheet
   carries the same `Día 0/2/3/6` legend cells as the two time-series sheets, so
   a day axis *looks* available. Those cells are transcribed onto the two
   **interval** rows of `config/adoc_outlet_conditions.tsv`, not onto a
   measurement row.
2. **PAEP is outside the day-3 representation problem entirely.** That problem —
   day-3 rows with no protocol counterpart, `OM-004` and `OM-011` — belongs to
   IGFBP-1 and PRL, which do have excluded day-3 measurements. PAEP has no
   day-3 measurement being ignored, because PAEP was never a time course.
3. **`OM-001`'s existing mapping is confirmed**, not changed: the E2-only
   condition onto `e2_primed_maternal` and the full-cocktail condition onto
   `hormone_treated_maternal` is exactly the phase pair the collaborator
   describes.

### One internal contradiction this exposed and fixes

`COND-DAY6-SAMPLE` declared `applies_to_sheets = PAEP;IGFBP-1;PRL `, while its
two sibling timepoint rows — `COND-DAY0-BASELINE` and `COND-DAY3-SAMPLE` —
declared `IGFBP-1;PRL ` and no PAEP measurement row had ever resolved to any of
the three. One table therefore held both readings of what a PAEP row is. With
the phases confirmed, the `PAEP` entry is simply wrong and is removed; the row's
`annotation_source_cells` still cite `PAEP!A14;PAEP!B14`, because the legend
genuinely is on that sheet, exactly as `COND-DAY0-BASELINE` cites `PAEP!A8`.

The builder now rejects both halves of the contradiction: a PAEP measurement row
that resolves to a sampled-timepoint condition, and a timepoint condition that
declares `applies_to_sheets=PAEP`. That check pins the current evidence state,
not an impossibility — it is what a future confirmation of sampling timing would
have to revise deliberately, which is the point of having it.

## What is recorded as rationale, not evidence

The message continues: *"que supuestamente es cuando se produce el pico de
receptividad y por tanto de secreción de de PAEP"* (verbatim, repeated word and
all) — the expectation that
receptivity, and so PAEP secretion, peaks in the secretory phase.

That is the collaborator's **rationale for the design**, and it is recorded as
such on every PAEP row. It is **not** evidence, and it must never be cited as
support for the `E_PAEP` direction: `OM-001` is the primary feasibility gate and
it tests exactly that direction, so using the expectation as support would make
the gate circular. This is why `SOFIA-COMM-007` carries a `construction` role
and not a `calibration` one.

## What is deliberately not adopted

`"S11, S12, son los identificativos de las diferentes chips"` is loose. The
sheet's own identifiers are `S11-1`, `S11 2` (with a non-breaking space), `S7.1`,
`S7.2`, `S10-2`, `S1` and `S2`; there is no `S12`. A free-text mention does not
overwrite header-derived identifiers — the same carve-out the 2026-07-29 document
applies to the annotation legend's drug names: file-backed structure wins, a
bench note does not.

## Offered and not received: older day-0 PAEP measurements

*"tengo otros más viejos que si [tenían día cero] … los datos no están tan
finos pero si quieres te lo paso"*.

Nothing in this repository uses these data and none have been received. They
matter more than the offhand offer suggests: `OM-001` is the repository's primary
feasibility gate, and its claim ceiling currently forbids reading it as evidence
for the registered `P1-PAEP` claim "HT versus untreated", because no untreated
arm exists. Older day-0 measurements are the only thing on the table that could
lift that ceiling.

They also arrive pre-flagged as *"no están tan finos"* — the same quality
judgement that excluded `S1` and `S2` from the current sheet. So the **admission
rule is pre-registered now, in `config/evidence_roles.yaml` `open_questions`, and
is value-blind**: if the data arrive they enter as their own dataset id, and
their role is settled **before any numerical value is inspected**, on metadata
and QC alone — protocol and medium composition, outlet and compartment, assay and
standard curve, dilution, collection window and volume, chip and source-group
provenance, and whether a day-0/untreated arm is documented as such rather than
inferred.

- **Sufficiently compatible** on that assessment: they may serve as an
  **independent untreated comparator** under the role the `P1-PAEP` readout's
  other observations already carry — `calibration`, alongside `SOFIA-EPI-001`
  and `SOFIA-EPI-002` — and not under a role invented for them. That is what
  could lift `OM-001`'s ceiling. A separate batch is a real confound, so the
  comparison and its residual limits are stated when it happens.
- **Incompatible or undocumented**: they stay `context_only`.
- **Either way**: they may never define the `E_PAEP` OFF/ON binarization
  threshold. `OM-001` forbids taking that threshold from observations that also
  serve as the feasibility gate, and that prohibition does not depend on how
  these data are admitted.

What the leakage rule requires is that the *criterion* be fixed before the values
are seen — not that the *answer* be fixed to no. An earlier version of this
section pre-registered a permanent `context_only` ban while naming the untreated
comparator as the only thing these data could do; those two statements were
incompatible, and the ban was the wrong half to keep.

## What this does **not** change

- **PAEP's outlet is still unverified.** The sheet has no outlet axis and this
  message does not say which outlet PAEP was sampled from, so
  `outlet_assignment_basis` stays `sheet_level_context_document_unverified` and
  `compartment`/`outlet` stay in `externally_asserted_fields`. PAEP remains the
  only row set with an unverified outlet assignment.
- **The PAEP dilution factor is still unknown**; `dilution_factor` stays empty.
- **The replicate ceilings are untouched**: at most 3 independent units and at
  most 2 epithelial source groups across the 5 PAEP chips carrying values
  (`SOFIA-COMM-005`, `SOFIA-ANNO-007`). Phase semantics say nothing about
  independence.
- **No time is calibrated.** "Proliferative" and "secretory" name what the
  protocol is intended to model in vitro. They are not a measured in vivo cycle
  phase, they add no sampling instant, and MaBoSS time stays relative
  (`config/calibration.yaml: calibrated_physical_time: false`).
