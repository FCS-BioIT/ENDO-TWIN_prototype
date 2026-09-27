# Phase 2B pre-registration, amendment 16 (pinned stack and measurement layer)

Committed **before any KLF12 value of any candidate reference was read,
generated or summarised**. It is committed on its own and records the owner's
decision of 2026-09-27.

**Kind of change.** This is a **post-result change**, owner-directed:
- a comparability criterion is retired **after it was observed to fail**;
- the measurement layer changes.

It is value-blind with respect to KLF12. It is **not** blind to the
comparability result. That result is whole-matrix aggregates only; no gene-level
value was seen.

## What the stack test showed (Cell Ranger 9.0.1, ADOC SZ09TE_CNT)

| check | result |
|---|---|
| feature identity | pass: 78,724/78,724 names in order, ids one-to-one with the GTF |
| raw matrix | **pass, exact**: 1,701,390 barcodes in order; all 77,689,012 non-zero triples identical |
| filtered matrix | **pass, exact**: 11,599 barcodes in order; all 41,468,953 non-zero triples identical |
| decontX vs deposit | **fail**: barcodes identical, but max difference 2,140.59 against a limit of 1e-6 |
| decontX run 1 vs run 2 | **identical**: same content sha256, max difference 0 |

**What the rerun means.** The pinned decontX route is deterministic here. It
does not reproduce the historical deposited decontX matrix, and the cause is
untested.

**Why the search cannot pass.** Any earlier Cell Ranger release either:
- changes the raw and filtered matrices, so criterion (a) fails; or
- feeds decontX identical inputs, so criterion (b) fails the same way.

The frozen version search therefore cannot pass as written.

## Decided

- **Pinned stack.** Cell Ranger 9.0.1 with the amendment-13/14 reference,
  identified by exact raw and filtered reproduction. The version search ends,
  and no earlier release is run.
- **Criterion (b) is retired.** Reproducing the historical decontX matrix is no
  longer a gate. The failure is recorded above as a provenance observation.
- **Measurement layer.** The canonical layer is the Cell Ranger 9.0.1
  **filtered UMI counts**, with no ambient correction.
  - It is processed identically for the reference and for ADOC.
  - It replaces the decontX layer everywhere that layer was used.
- **Quantity.** `count_per_10k` is the KLF12 filtered UMI count divided by
  the cell's filtered-matrix column sum over all features, times 1e4.
  - The per-cell table is still exactly `donor_id`, `klf12_count`, `depth`,
    now both taken from the filtered layer.
  - `count` stays a diagnostic only.
- **QC.** The frozen ADOC QC is computed on the filtered layer:
  nFeature ≥ 500, mitoRatio < 15, nCount ≥ 1000, then scDblFinder 1.20.2
  with seed 47.
- **The S5 null.** The code is unchanged. For integer counts the shrinkage
  ratios `c / round(c)` are 1. S5 therefore tests against the unshrunk
  stateless Poisson null, at the donor's own depths and expected detection.

## Accepted risk

Ambient RNA is not corrected.
- **ADOC** loaded stromal and epithelial cells together.
- **The reference** is epithelium-only organoids.
- **So** ADOC epithelial counts may carry a stromal-soup floor that the
  reference lacks, and ADOC cells near the threshold may be biased toward
  "high".

The owner accepted this in preference to decontX. It is recorded here but not
quantified, because quantifying it would require reading values.

## Application to ADOC (not part of C4)

The ADOC HT units use the same layer. Whether they are reprocessed with the
pinned stack, or taken from the deposited filtered matrices, is decided in the
application unit, before any ADOC value is read. Exact reproduction was shown
for SZ09TE_CNT only.

## Unchanged

- candidate selection;
- donor and population rules;
- `count_per_10k` as the primary quantity;
- the derivation, S1 to S5 and every derivation constant;
- aggregation, and variants (all reported, none selected);
- stopping and verdict rules;
- amendment 15's endpoint role;
- the amendment-05 frozen citation, and the owner's B1/B2 resolution;
- every other rule of amendments 01-15.

No code changes. Amendment 12's pins are carried verbatim. No layer, QC
setting, quantity, threshold, variant, donor subset or candidate changes after
any KLF12 value is seen.

**Review provenance.** The cross-vendor reviewer is unavailable. Review is
degraded, and no independent cross-vendor review is claimed.
