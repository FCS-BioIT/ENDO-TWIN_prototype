# ADOC source data inventory

Source integrity values are in `config/data_manifest.tsv`; source-handling rules
are in `data/README.md`.

## Current sources

| Source | Observed structure | Modeling use and limitation |
|---|---|---|
| `1 Supplementary_materials_Zaragozano et al Clean.docx` | OOXML supplement | Figure/method detail; extraction is incomplete |
| `2 Zaragozano et alClean copy.docx` | 45-page manuscript | Primary phase-1 context and readouts; claims still require provenance to exact figures/tables |
| `combined-dataset-patient-integration.rds` | Seurat object; 78,724 features × 61,843 cells; six donor-condition samples | Same ADOC study barcodes, but intermediate integrated object without the paper's final labels/graphs |
| `proteinas secretadas ADOC.xlsx` | Sheets `PAEP`, `IGFBP-1`, and `PRL ` | Molecular calibration data. Units and zero/censoring semantics were resolved by collaborator confirmation on 2026-07-29; donor/sample mapping is only partially recoverable and is lost for IGFBP-1 and PRL |
| `secreción proteinas ADOC anotaciones.xlsx` | Annotation metadata for the workbook above; sheets `PAEP`, `IGFBP-1`, `PRL` | LOCAL-ONLY, gitignored: carries the lab's own cell-source codes. Numeric cells are byte-identical to the measurement workbook, so it is never a second measurement source. Transcribed into `config/adoc_outlet_conditions.tsv` |
| `sciadv.adz2249.pdf` | Published 19-page ADOC article | Published evidence and cross-check for the manuscript-derived contract |
| `Montagud et al. - 2022 ...pdf` | eLife patient-specific Boolean-model study | Reference for generic model → PROFILE → MaBoSS → PROFILE_v2 workflow |
| `Montagud - 2026 ...pdf` | Systems-biology digital-twin perspective | Long-term design context, not phase-1 evidence |

## RDS audit result

The local object loads as a Seurat object and contains:

- 78,724 features and 61,843 cells;
- three donors (`SZ09`, `SZ10`, `SZ25`);
- control and hormone-treated samples for every donor;
- sample identifiers encoded by donor and condition; and
- a separate donor field (`patient_n`).

All local cell barcodes were found in their corresponding public E-MTAB-15842
sample, supporting study identity. However, the manuscript reports a final
28,212-cell, seven-population analysis. The local object lacks those final cell
annotations and graphs and should therefore be treated as an intermediate
integrated object, not as the exact paper analysis object.

**This is now a reproducible audit rather than prose.** `pixi run
audit-scrna-object` streams the object without R or Seurat and writes
[`concordance/scrna_object_audit.json`](concordance/scrna_object_audit.json),
which records the complete `meta.data` roster (`orig.ident`, `nCount_RNA`,
`nFeature_RNA`, `sample_id`, `patient_id`, `runs`, `lib_type`, `seq_time`,
`tissue`, `patient_n`, `mitoRatio`, `scDblFinder_RNA.score`,
`integrationCovariates`), the `active.ident` levels (the six donor-condition
*samples*, not clusters), and the absence of any `seurat_clusters`, `*_snn_res.*`,
cell-type column, `FindClusters` or `FindNeighbors` anywhere in the file.
Presence is exact; the absence claim is
evidential and bounded by the token list the audit records, so it is checkable.
`tests/unit/test_concordance.py` fails if an annotated object ever appears, which
is the point: eleven concordance rows are unassessable only while this holds.

Before node prioritization, either obtain the final annotated object or
reconstruct a versioned QC/annotation pipeline and compare its retained cells,
population markers, and condition composition with the paper. A barcode ->
final-population crosswalk keyed on the barcodes this object already carries
would be sufficient and is the cheapest route; see
[`concordance_analysis.md`](concordance_analysis.md).

## Canonical ADOC outlet tables

One auditable record of what was measured, in three tables:

| Table | Alias | Grain | Rows |
|---|---|---|---|
| `input_tables/adoc_secreted_proteins.tsv` | `adoc_outlet_measurements` | one row per workbook data cell | 62 |
| `config/adoc_outlet_conditions.tsv` | — | one row per protocol interval, sampled timepoint, or protocol note | 6 |
| `config/adoc_chip_donor_provenance.tsv` | `adoc_sample_provenance` | one row per chip, donor relation, unresolved mapping, or anomaly | 16 |

There is deliberately **no** separate `adoc_outlet_measurements.tsv`: the first
table above already is the one-row-per-measurement outlet record, and a second
table over the same 62 cells would be the duplicate this structure exists to
avoid.

## Workbook observations that must be preserved

- `PAEP` contains sample-like labels and two experimental conditions.
- `IGFBP-1` contains TOP/BOTTOM compartments and Day 0/3/7 rows.
- `PRL ` contains Day 0/3/6 rows.
- Numeric zeros and empty cells are distinct source states, and a stored zero is
  a *measured* non-detect rather than a censored or missing value.
- The PRL sheet name contains a trailing space.
- The manuscript describes PRL and IGFBP-1 collection at days 0, 3, and 6. The
  workbook's IGFBP-1 `Day 7` label is a labelling error, confirmed by the
  collaborator on 2026-07-29, and resolves to day 6 while the source label is
  preserved.
- Detection limits are 5 pg/mL for IGFBP-1, 10 pg/mL for PRL, and 3 pg/mL for
  PAEP according to the manuscript. These are **not** written into the canonical
  table: they are repo prose not yet traced to the supplementary methods, so
  `detection_limit_pg_ml` stays empty.

No quantitative fitting should use the workbook. Units and censoring semantics
are now documented, but donor/sample identifiers, technical replicates, channel
and normalization are not — and the donor mapping for IGFBP-1 and PRL is lost,
so it will never be documented. Chips are not independent biological replicates;
see `config/adoc_chip_donor_provenance.tsv` and
`docs/collaborator_metadata_2026-07-29.md`.
