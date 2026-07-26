# Data Lineage Contract

Every derived artifact must identify its parent artifact and transformation.

## Required stages

1. `source`: immutable file under `data/`, with size and SHA-256.
2. `audited`: schema, units, identifiers, missingness, duplicates, and biological
   units recorded.
3. `analysis_ready`: explicit filters, transformations, normalization, and
   exclusions.
4. `model_mapping`: source feature to model node/parameter, direction, rule,
   threshold, uncertainty, and evidence class.
5. `model`: baseline and patient-specific `.bnd`/`.cfg` hashes.
6. `simulation`: software version, seed, trajectory count, time settings, and
   perturbation.
7. `summary`: output schema, aggregation, uncertainty, and QC status.
8. `claim`: exact artifacts and validation level supporting the statement.

## Required semantics

- Preserve raw values; do not overwrite them with transformed or binarized
  values.
- Store blank, missing, below-detection, excluded, and numeric zero separately.
- Record units before combining measurements.
- Record whether replicate aggregation occurs within patient/sample or across
  independent patients.
- Record every exclusion with a reason and stage.
- Record train/calibration/validation membership before outcome-guided tuning.
- Keep literature-derived topology distinct from patient-derived parameters.

An artifact without reconstructable lineage is exploratory and cannot be
canonical.
