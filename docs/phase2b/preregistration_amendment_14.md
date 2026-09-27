# Phase 2B pre-registration, amendment 14 (mkref execution parameters)

Committed **before any stack-identification matrix comparison, and before any
KLF12 value of any candidate or of ADOC was read**. It is committed on its
own and records the owner's decision of 2026-09-26.

No Cell Ranger reference or count output exists. The only `mkref` started
(9.0.1, at 00:38) was stopped at 00:42, before it completed. Its partial
output is discarded and never used.

## Why

Amendment 13 froze `mkref` with "otherwise default settings". The reference
build needs explicit resource options: the 9.0.1 default of `--memgb 16` is
below what STAR needs for GRCh38.

## Frozen for every Cell Ranger version tried

Every version tried runs `cellranger mkref` with:

| option | value |
|---|---|
| `--nthreads` | `16` |
| `--memgb` | `64` |
| FASTA | `GRCh38.primary_assembly.genome.fa.gz`, GENCODE release 47, md5 `0c33152b…558771e` |
| GTF | `gencode.v47.annotation.gtf.gz`, md5 `2459f586…fed6a` |
| all other options | that version's defaults |

- **What these are.** They are **fixed execution parameters across the
  entire version search**. They are *not* claimed to be equivalent to the
  defaults, nor to leave the built reference byte-identical.
- **Only the version varies.** The Cell Ranger version remains the only
  parameter varied between candidate stacks.
- **No tuning.** Memory, threads, reference inputs and every other option are
  not tuned, retried or changed after any stack result is seen.

## Unchanged

- **The acceptance criterion:**
  - exact reproduction of the raw and filtered matrices;
  - the frozen decontX criterion: identical barcodes, and a maximum absolute
    entrywise difference ≤ 1e-6;
  - amendment 13's feature-identity criterion.
- **Everything else in amendment 13,** including the count parameters. This
  amendment supersedes only its "otherwise default settings" for `mkref`,
  and only as to `--nthreads` and `--memgb`.
- **The rest of the rules:**
  - candidate selection, and the donor and population rules;
  - the KLF12 measurement;
  - the derivation, S1 to S5, thresholds and variants;
  - stopping and verdict rules;
  - the amendment-05 frozen citation, and the owner's B1/B2 resolution;
  - every other rule of amendments 01-13.

No code changes. Amendment 12's pins are carried verbatim.
