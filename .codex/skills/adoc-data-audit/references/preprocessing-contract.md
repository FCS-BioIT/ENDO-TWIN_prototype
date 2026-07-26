# Preprocessing contract

Write this contract before implementing data-to-model processing.

## Input

Record source path and SHA-256, object/table/sheet and schema version, row
meaning, independent unit, identifier keys, units, assay range, missingness
semantics, and prior transformations.

## Operations

For each operation record the exact filter or transformation, grouping unit,
technical-replicate handling, batch adjustment, any imputation, output columns,
before/after row and patient counts, and deterministic seed when applicable.

Never overwrite raw values. Keep QC flags, transformed values, and binarized
states separate.

## Feature-to-model mapping

Record source feature, target node/parameter, biological direction, mapping
layer, threshold/method, uncertainty band, evidence class, and sensitivity
variants.

Expression, protein abundance, and secretion are not interchangeable. If an
extracellular protein maps to an intracellular signaling node, document the
biological bridge and compartment assumption.

## Leakage controls

Record which data inform feature selection, threshold selection, topology/rules,
rate calibration, phenotype definition, and validation. If outcome labels
influenced an earlier stage, do not describe evaluation on the same observations
as validation.
