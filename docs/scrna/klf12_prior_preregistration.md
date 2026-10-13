# Pre-registration: can `E_KLF12_HIGH` be given a measured initial-state prior?

Written **before** any KLF12 value was read from the deposited object. Committed
on its own so the ordering is checkable in `git log`, not merely asserted.

## What was already known when this was written

Everything in [`docs/scrna_observability.md`](../scrna_observability.md), and
nothing else about KLF12. Specifically: the deposited object's dimensions, its
six `sample_id` values, the seven `celltype_v2` labels with their per-condition
counts, that the `counts` layer is decontX-corrected rather than raw UMIs, that
the deposited `meta.data` carries no per-cell QC covariates, and that
`E_KLF12_HIGH` is the only model state whose conditioning needs no rule change.

**No KLF12 expression value, detection rate, distribution or per-unit summary
had been computed or seen.** That is the fact this document exists to fix in
time.

## The question

Does this evidence support an estimate of

> P(`E_KLF12_HIGH` = 1)

fit to be written into a MaBoSS initial-state prior, *without* inventing a
biological threshold the evidence does not carry?

## Three steps that must not be collapsed

1. **Measurement.** KLF12 transcript abundance per cell, in a named layer.
2. **Latent-state inference.** A declared state-estimation model taking that
   measurement to a per-unit probability that the epithelial compartment is in
   the KLF12-high state.
3. **Model conditioning.** That probability entering `E_KLF12_HIGH.istate`.

Step 2 is the one with no default answer. A detection fraction is a property of
cells; the model node is a property of a compartment. Identifying the two is an
**assumption**, declared in step 3 below, never a measurement.

## Unit of inference

**Donor x condition**: six units over three donors (`SZ09`, `SZ10`, `SZ25`) x
(`CNT`, `HT`). `config/preprocessing_contract.yaml` already declares
`donor_is_independent_unit_for_sc_rna: true`, and `config/personalization.yaml`
declares `independent_unit: donor`. This pre-registration does not relax either.

Cells inform the within-unit estimate and are **not** replicates. No test,
interval or p-value is computed over cells as independent observations. Every
per-unit estimate is reported separately before any pooling, and with three
donors no across-donor inferential statistic is computed at all.

## Population

Pre-declared, and fixed before any KLF12 value is read:

> **epithelium** := the union of the four `celltype_v2` labels that name an
> epithelium — `Luminal-like epithelium`, `Cycling epithelium`,
> `HT epithelium I`, `HT epithelium II`.

Reason. Three of the seven labels are *named for the treatment* and are ~80%
one condition; `Luminal-like epithelium` and `Stroma` are ~99% the other.
Stratifying by a single label and then contrasting HT against CNT would
manufacture the effect being inferred. The union is a condition-independent
*definition* — "any cell the paper's annotation calls epithelial" — and its
condition balance is recorded as a diagnostic, not assumed.

Forbidden in this increment: stratifying by individual `celltype_v2` label and
contrasting conditions within it; reconstructing the pipeline's
`celltype_general`, which bakes the treatment group into the label; and
re-clustering or re-filtering the object, which would substitute our reanalysis
for the paper's populations.

Marker genes (`EPCAM`, `PTPRC`, `COL1A1`, `VIM`) are extracted only to describe
the population that the pre-declared definition selects. They may not be used to
redefine it.

## Layer

Primary: the deposited `counts` layer, with its recorded caveat — it is
decontX-corrected, so it is neither raw UMIs nor free of a model whose
correction depends on cluster assignments. The log-normalised `data` layer is
extracted alongside it.

Sensitivity, only if the primary analysis is not already decisive: the raw
per-sample `filtered_feature_bc_matrix` UMIs from the same accession, joined by
barcode.

Per-cell sequencing depth is not in the deposited `meta.data` and is therefore
computed as the column sums of the `counts` layer — a decontX-corrected depth,
recorded as such.

## State-estimation models, declared in advance

- **M0 — detection.** KLF12-high := KLF12 > 0. Declared **inadmissible on its
  own**: non-zero expression is not a high state. Computed only as a description
  and as the upper bound on any threshold-based fraction.
- **M1 — empirical state separation.** A two-component mixture on KLF12 within
  the epithelial population. Admissible only if the separation is real, judged
  by all three of:
  - **(a)** the implied boundary falls in a genuine density valley, not inside
    the zero spike;
  - **(b)** the high component is materially *not* the detected/dropout split —
    it must exclude a substantial share of the cells M0 would call high;
  - **(c)** component assignment is not explained by sequencing depth (F1).
- **M2 — quantile sensitivity.** Thresholds at the qth percentile of KLF12
  within the pooled epithelial population, q in {0.75, 0.80, 0.85, 0.90, 0.95},
  used explicitly as **sensitivity parameters and never as biological truth**.
  Yields an interval over P per unit, not a value.

## Falsifiers, declared in advance

- **F1 — depth confounding.** Detection rate is compared between the lowest and
  highest depth quartile of epithelial cells *within* each unit. If that ratio
  exceeds 2 in a majority of units, a detection-boundary state call is reading
  library depth rather than state, and M0 and any threshold near the detection
  boundary are inadmissible.
- **F2 — no separation.** If the distribution is a zero spike plus a monotone
  decreasing tail with no valley, M1 has no boundary to find and fails.
- **F3 — threshold dominance.** If, for any unit, the width of the across-q
  interval from M2 exceeds the largest across-unit difference at any fixed q,
  then the analyst's choice of q moves the prior more than the biology it is
  meant to express, and no point prior is identified.
- **F4 — no reference for "high".** REF-037 (Huang 2018) defines increased
  KLF12 **comparatively**: recurrent-implantation-failure endometrium against
  fertile controls. This repository holds no RIF or fertile label for any donor,
  and `config/personalization.yaml` declares
  `reference_strategy.mode: external_reference_required` with
  `reference_path: null` and the note *"Do not estimate PROFILE-style reference
  distributions from the three currently available donors."* F4 is therefore
  **already true at writing time**: no route in this increment may define "high"
  by comparison to a reference population. Only a within-data, cell-intrinsic
  separation (M1) can define it here.

## Decision rule

- **GO** — M1 passes (a), (b) and (c), and F1, F2, F3 do not fire. A measured
  prior exists. Only in this case may `EXT-SCRNA-001` be promoted towards
  `integrated_as_active_constraint`.
- **CONDITIONAL-GO** — M1 fails but F1 and F3 do not fire. Conditioning may be
  executed and reported **only** as an explicitly arbitrary-threshold
  sensitivity analysis. The scRNA row stays a diagnostic, the external asset
  stays `structurally_verified_not_integrated`, and no text may call the result
  a measured prior.
- **NO-GO** — F1 or F3 fires. Report the quantified ambiguity and the minimum
  additional measurement or biological definition that would lift it.

## Leakage rules, binding on the implementation

1. No model output, node occupancy, concordance value, attachment count or
   desired contraceptive behaviour may enter the choice of population, layer,
   state-estimation model, threshold or q. The derivation module must not import
   `dt_adoc.simulation`, `dt_adoc.concordance`, `dt_adoc.calibration`,
   `dt_adoc.scoring` or `dt_adoc.perturbations`, and must not read
   `docs/concordance/`.
2. These are the study's own cells. The evidence role stays
   `same_dataset_internal`; it may never be recorded as `held_out` or
   `external`, and nothing produced here is validation.
3. `network.bnd` is not edited. No Boolean rule changes, `E_KLF12_HIGH`'s least
   of all. The canonical unconditioned v0.4 model stays available unchanged, and
   conditioning is expressed as an overlay on top of it.
4. The presence of the external object on a local disk activates nothing. An
   active constraint requires the GO branch above and an explicit row.

## The assumption that bridges step 2 to step 3

Declared here so it cannot be smuggled in later as a result.

> The prior is applied as: *the ensemble frequency with which the modelled
> epithelial compartment is initialised in the KLF12-high state equals the
> estimated fraction of epithelial cells in that state.*

This is an interpretive choice with no experimental support in this repository.
A MaBoSS initial-state probability is a distribution over the starting state of
**one** modelled compartment; a cell fraction is spatial heterogeneity within a
tissue. Equating them treats population heterogeneity as compartment-state
uncertainty. It is recorded as an assumption of the conditioning layer, and any
report of a conditioned result must carry it.
