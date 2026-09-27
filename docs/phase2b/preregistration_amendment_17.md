# Phase 2B pre-registration, amendment 17 (candidate input route)

Committed **before any E-MTAB-10283 file was downloaded or processed, and before
any KLF12 value of any candidate was read**. It is committed on its own and
records the owner's decision of 2026-09-27.

It records an input route only. No rule, criterion, layer, quantity or
derivation changes.

## Why

The ArrayExpress FASTQs for the selected libraries have **no archive-published
checksum**: none in the SDRF, the BioStudies files API or the HTTP headers.
Only their byte sizes are published. The only published MD5s are ENA's, for
the depositors' submitted Cell Ranger BAMs. The frozen provenance rule requires
every processed input's MD5 to equal an archive-published MD5. The unchanged
`values.check_provenance` enforces that rule.

## Route

| run | BAM | bytes | ENA MD5 |
|---|---|---|---|
| ERR5545549 | `WSSS_END9397531.bam` | 32,437,071,164 | `983a9ef7eface9c08954cf57375118c6` |
| ERR5545551 | `WSSS_END9397535.bam` | 31,142,707,276 | `402e74e892a7355ca568196544080b3b` |

1. **Verify each BAM.** Its local MD5 and size must equal ENA's before it is
   used.
2. **Gate on the first BAM, before any conversion.** Its header must identify
   an original 10x Cell Ranger BAM that `bamtofastq` converts automatically:
   Cell Ranger 1.3 or later headers, with the 10x read tags present. Record the
   original Cell Ranger version from the header where it is present. If the
   gate fails, C4 stops.
3. **Reconstruct the FASTQs** with the pinned Cell Ranger 9.0.1's bundled
   `cellranger bamtofastq` (v1.4.1), at its defaults.
4. **Count** with the amendment-16 pinned stack at the amendment-13 count
   settings, one library at a time.

## Provenance

- **Sidecar.** The per-cell provenance sidecar names the two BAMs, each with
  its computed and its published MD5. `PROVENANCE_COLUMNS` is unchanged.
- **Intermediates.** The reconstructed FASTQs are recorded by sha256 and read
  count.
- **Not used:**
  - the ArrayExpress FASTQs, because they have no checksum;
  - the depositors' processed matrices, because they come from a different
    pipeline.

## Unchanged

Every rule of amendments 01-16 stands, including:
- the pinned stack and layer;
- QC;
- candidate, donor and population rules;
- `count_per_10k`;
- the derivation;
- the verdict rules;
- the endpoint role;
- the frozen C5 citation.

No code changes. Amendment 12's pins are carried verbatim. Review is degraded,
and no cross-vendor review is claimed.
