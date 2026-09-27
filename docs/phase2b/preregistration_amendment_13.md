# Phase 2B pre-registration, amendment 13 (comparability execution choices)

Committed **before any stack-identification matrix comparison, and before any
KLF12 value of any candidate or of ADOC was read**. No Cell Ranger run has
been made. It is committed on its own, and records the owner's decision of
2026-09-26.

**Kind of change.** This is an adjustment to a comparability acceptance
criterion, not a wording change. Amendment 12's implementation pins are
carried verbatim, and no code changes.

## Why

At C4 pre-flight, the E-MTAB-15842 file `all_feature_bc_matrix_features.tsv`
(sha256 `61081d3c…8dd`) turned out to be a **single column** of Seurat
feature row names. It has no feature id and no feature type. The frozen check
"feature id, name, type, order" therefore cannot be evaluated literally. The
IDF also records no Cell Ranger version, FASTA or count parameters.

## 1. Feature identity (criterion adjusted)

- **Passes when** the deposited feature names, in order, exactly equal a
  sequence reconstructed from GENCODE v47:
  - every gene record of `gencode.v47.annotation.gtf.gz`, the
    chromosome-only annotation;
  - in GTF order;
  - named by `gene_name`;
  - with duplicate names resolved by R-compatible `make.unique`.
- **The rebuilt reference must carry** those same genes, one-to-one with the
  deposited rows and in the same order. Each keeps its GENCODE v47 gene id
  and the feature type `Gene Expression`.
- **Id and type are reconstructed** from the frozen annotation. They are not
  compared, because the deposit has no such columns.
- **Value-blind diagnostic at freeze:** 78,724 of 78,724 names match in
  order.

## 2. FASTA and annotation

| file | published md5 |
|---|---|
| `GRCh38.primary_assembly.genome.fa.gz` | `0c33152bea6f09b89fb5e3f89558771e` |
| `gencode.v47.annotation.gtf.gz` | `2459f58694fd330740627a8c371fed6a` |

Both come from GENCODE release 47, with the checksums from its `MD5SUMS`.
Every download's local md5 must equal the published one before `mkref` runs.

Not used:
- `GRCh38.p14.genome.fa.gz`, which includes alternate haplotypes;
- the primary-assembly GTF, which has 78,932 genes rather than 78,724.

## 3. Reference build

Each candidate Cell Ranger release builds its own reference:
- with that release's own `cellranger mkref`;
- from exactly the files above;
- otherwise at default settings, with no GTF filtering.

The Cell Ranger version is the only variable in the stack search.

## 4. Count parameters

Each release runs `cellranger count` at its own defaults: chemistry
autodetection, default cell calling and default intron behaviour.
- `--expect-cells` and `--force-cells` are not set.
- `--create-bam false` is allowed. It only suppresses an output and does not
  alter the matrices compared.

## Search, unchanged

- **Order.** Releases are tried in the frozen order, starting at 9.0.1.
- **Pass.** The first complete stack to pass all three frozen checks is
  pinned:
  - whole-matrix reproduction of the raw matrix;
  - whole-matrix reproduction of the filtered matrix;
  - the pinned decontX reproduction: identical barcodes, and a maximum
    absolute entrywise difference ≤ 1e-6.
- **No tuning.** No setting above is retried, tuned or changed after any
  matrix result.
- **Failure.** If no release passes, the verdict is `BLOCKED_COMPARABILITY`.
- **Value-blind.** The comparisons are whole-matrix only. No KLF12 value is
  extracted, inspected or summarised during stack identification.

## Unchanged

- candidate selection;
- donor and population rules;
- the KLF12 measurement;
- the derivation, S1 to S5, thresholds and variants;
- stopping and verdict rules;
- the amendment-05 frozen citation;
- the owner's B1/B2 resolution;
- every other rule of amendments 01-12.
