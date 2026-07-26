# Source inventory

The canonical expected files, sizes, and hashes are stored in
`config/data_manifest.tsv`.

## Known structure

- Two OOXML Word documents contain manuscript and supplementary material.
- One 3.46 GB RDS contains an integrated patient dataset; its class and schema
  are unverified without R/Seurat.
- One workbook contains three heterogeneous sheets: `PAEP`, `IGFBP-1`, and
  `PRL `.
- One PDF is a 19-page published article.

The workbook contains both numeric zeros and blank cells. The `PRL ` sheet name
contains a trailing space. Preserve both facts until a preprocessing contract
defines canonical representations.

## Required next evidence

- RDS object class, packages, dimensions, assays/layers, metadata columns, and
  normalization state;
- relation among patient, sample, compartment, time, well, and measurement;
- workbook units, detection limits, technical replicates, and sample mapping;
- correspondence between workbook identifiers and RDS metadata;
- intended phenotype and observations reserved for validation;
- source-document methods that define the assays.

Unavailable evidence must be labeled `unverified`, never inferred.
