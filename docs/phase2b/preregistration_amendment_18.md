# Phase 2B pre-registration, amendment 18 (candidate FASTQ reconstruction)

Committed **before any E-MTAB-10283 read was converted or counted, and before
any KLF12 value of any candidate was read**. It is committed on its own and
records the owner's decision of 2026-09-27.

Only BAM header and raw read-structure statistics were inspected: tag lengths,
`N` positions and the quality alphabet, from the first ~200,000 records of a
partial download.

It records an input reconstruction route only, replacing amendment 17's
`bamtofastq` step, whose gate failed. No rule, criterion, layer, quantity or
derivation changes.

## Amendment 17's gate failed

The ENA BAMs are not Cell Ranger BAMs. They are ENA's unaligned packaging of
the original FASTQs:
- the only program record is `fastq_pre_barcodes`, run on the library's R2, R1
  and I1, taking the UMI from R1 bases 17–28 and the barcode from R1 bases
  1–16, followed by a samtools conversion;
- there are no `@SQ` lines and no 10x `@RG`/`@CO` headers;
- `bamtofastq` therefore cannot convert them. It was not run.

No original Cell Ranger version is recorded.

## The packaging is lossless

| tag | holds |
|---|---|
| SEQ/QUAL | R2: 91 bases and 91 qualities |
| `CR`/`CY` | raw cell barcode and its qualities: 16/16 |
| `RX`/`QX` | raw UMI and its qualities: 12/12 |
| `BC`/`QT` | sample index and its qualities: 8/8 |
| `on` | the original Illumina read name |
| `op` | equals QUAL in 200,000/200,000 records |

`OX`/`BZ` are absent. `RX`/`QX` are nonetheless the original, uncorrected UMI
and qualities:
- **No correction step.** The `@PG` chain holds only the extraction and a
  conversion.
- **`CR` is uncorrected.** 301 of 200,000 barcodes contain `N`, which
  correction would remove.
- **`N` calls are cycle-specific.** They occur at cycles 1, 2, 4 and 8, and
  none after cycle 8. Zero `N` in the UMI (cycles 17–28) is therefore
  expected of raw reads.
- **Qualities are the raw binned alphabet** (`,` `:` `F`).
- **No corrected tags.** There is no `CB`/`UB`.

## Reconstruction

From each ENA BAM, after its MD5 and size equal ENA's (amendment 17), using the
pinned 9.0.1's bundled `samtools view`, a deterministic text transform and
`pigz`:

| file | sequence | quality |
|---|---|---|
| R1 | `CR` + `RX` (28 bases) | `CY` + `QX` |
| R2 | SEQ (91 bases) | QUAL |
| I1 | `BC` (8 bases) | `QT` |

- **Read names** are taken from `on`, identical in R1, R2 and I1. Each file
  gets its own Illumina comment (`1:N:0:<index>`, `2:N:0:<index>`).
- **Files** are `<library>_S1_L001_{R1,R2,I1}_001.fastq.gz`, written in BAM
  record order.
- **Required.** Every record must carry exactly these tags and lengths. The
  number of reads must equal ENA's `read_count`: 400,248,540 for ERR5545549
  and 387,051,041 for ERR5545551. Any violation stops C4.
- **Recorded.** Each FASTQ is recorded by sha256, uncompressed-content sha256
  and read count. The provenance sidecar still names the BAMs, each with its
  computed and its published MD5.
- **No cross-check.** The ArrayExpress FASTQs are not downloaded unless the
  reconstruction exposes an ambiguity.

Counting is unchanged: the amendment-16 pinned stack at the amendment-13
settings, one library at a time.

## Unchanged

Every rule of amendments 01-17 stands, apart from amendment 17's
`bamtofastq` step. No code changes. Amendment 12's pins are carried verbatim.
Review is degraded, and no cross-vendor review is claimed.
