# ADOC paper and readout context

## What the study models

Sofia Zaragozano and colleagues developed ADOC, a dual-channel
endometrium-on-a-chip with organoid-derived endometrial epithelium in the upper
channel and primary stromal cells in the lower channel. The channels communicate
through a porous membrane. The system was used to study hormone-induced
endometrial receptivity and stable mouse and human blastocyst adhesion.

The phase-1 DT_ADOC model treats the chip as a coupled epithelial–stromal
system. Stable embryo adhesion is initially an observed probabilistic output,
not a complete embryo signaling model.

## Experimental conditions

- **Basal ADOC:** no E2/MPA/cAMP/XAV939 treatment.
- **E2 priming:** 10 nM E2 for two days.
- **Hormone-treated ADOC:** four additional days of 10 nM E2, 1 µM MPA,
  250 µM cAMP, and 10 µM XAV939.
- **Mifepristone perturbation:** 10 µM mifepristone for 24 hours after the
  six-day hormone protocol.

The four treatment components must remain independently controllable in the
model. Untreated ADOC is a basal chip state and should not automatically be
equated with a perfect physiological proliferative-phase endometrium.

## Functional adhesion readout

Stable adhesion was defined by resistance to flushing. The manuscript reports:

| Condition | Stable human blastocyst adhesion |
|---|---:|
| Basal/untreated | 0/12 |
| Hormone treated | 9/19 (47%) |
| Hormone treated plus mifepristone | 1/8 (12.5%) |

These are small binomial observations with substantial uncertainty. They are
calibration or validation evidence, not exact probabilities that the model must
reproduce.

## Protein readouts

The source workbook `data/proteinas secretadas ADOC.xlsx` contains three
heterogeneous worksheets:

- **`PAEP`:** epithelial glycodelin/PAEP measurements with sample-like labels
  and two experimental conditions. The manuscript reports increased PAEP after
  hormone treatment and a day-6 ELISA difference.
- **`IGFBP-1`:** decidualization readout with TOP/BOTTOM compartments and
  Day 0/3/7 labels in the workbook.
- **`PRL `:** decidualization readout whose source sheet name contains a
  trailing space, with Day 0/3/6 labels.

The manuscript describes PRL and IGFBP-1 collections at days 0, 3, and 6. The
collaborator confirmed on 2026-07-29 that the workbook's IGFBP-1 `Day 7` label is
an error and that row is day 6; the source label is preserved rather than
silently harmonized. Reported assay detection limits are 5 pg/mL for IGFBP-1,
10 pg/mL for PRL, and 3 pg/mL for PAEP -- repo prose sourced to the manuscript,
not yet traced to the supplementary methods, so `detection_limit_pg_ml` stays
empty in the canonical table.

The workbook contains both numeric zeros and blank cells. They remain distinct,
and their meanings are now settled: a blank is never converted to zero, and a
stored zero is a **measured** non-detect (absorbance read, interpolated against
the standard curve to no detectable secretion) rather than a censored
below-detection value. Units are confirmed as pg/mL. Sample-to-donor mapping,
technical replicates and normalization still must be audited before quantitative
calibration -- and the IGFBP-1/PRL column-to-chip mapping is lost, so it cannot
be. See `docs/collaborator_metadata_2026-07-29.md`.

## Transcriptomic context

The manuscript reports a final analysis of 28,212 cells and seven populations.
The local RDS is an earlier integrated Seurat object with 61,843 cells from
three donors (`SZ09`, `SZ10`, and `SZ25`) under control and hormone-treated
conditions. Its barcodes correspond to the public study samples, but it lacks
the paper's final annotations and graphs.

The single-cell data can prioritize compartment-specific nodes and state
signatures. Expression alone cannot establish a causal edge, Boolean state, or
transition rate, and cells must not be treated as independent donor replicates.

## Bundle contents and limits

The ChatGPT bundle includes this context, the original small protein workbook,
and full TSV exports of every worksheet. It excludes the RDS and full paper
files. The source workbook remains authoritative; TSV files are portable
cell-value representations with source hashes and sheet metadata.
