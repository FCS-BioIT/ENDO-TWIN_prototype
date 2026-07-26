---
name: adoc-data-audit
description: Audit ADOC source data and preprocessing for scientifically valid MaBoSS personalization. Use when inspecting the large RDS object, Excel secretion measurements, manuscript or supplementary sources, defining patient/sample/replicate units, checking identifiers, units, batches, missingness and zeros, designing normalization or binarization, mapping source features to model inputs, or reviewing whether preprocessing leaks outcome information.
---

# DT_ADOC Data Audit

Inspect source evidence without altering it, then create an explicit,
reconstructable data contract before patient modeling. Read `AGENTS.md` and
`.codex/harness/data-lineage-contract.md`.

## Workflow

1. Run `scripts/check_data_manifest.py --root <repo>`; add `--check-hashes` when
   source-integrity verification is required.
2. Read `references/source-inventory.md` and update it only from bounded,
   reproducible inspection.
3. Identify object class, tables/assays, dimensions, identifiers, units,
   missingness states, batches, outcomes, and prior transformations.
4. Define patient, sample, time point, compartment, well, technical replicate,
   and measurement separately.
5. Write the preprocessing contract before deriving model inputs. Read
   `references/preprocessing-contract.md`.
6. Produce analysis-ready values, QC flags, exclusions, and binarized/model
   mappings as distinct artifacts.
7. Validate counts, uniqueness, missingness, distributions, and patient coverage
   before model construction.

## Core rules

- Never edit or convert source files in place.
- Never treat blank, missing, below-detection, excluded, and numeric zero as the
  same value.
- Never infer RDS structure without successfully loading it with the appropriate
  R package and recording versions.
- Do not materialize a multi-gigabyte matrix until storage type and memory
  feasibility are known.
- Do not treat cells, wells, time points, or technical replicates as independent
  patients.
- Preserve source units and raw values; transformations get new columns or
  artifacts.
- Do not pool TOP/BOTTOM compartments or unequal days without a stated
  biological rationale.
- Do not select thresholds from the desired phenotype or validation outcome.
- Treat expression and secretion as noisy proxies, not direct Boolean states or
  kinetic rates.
- Record exclusions and unmatched identifiers explicitly.

## Minimum RDS audit

Record object class, package versions, dimensions, assays/layers/slots,
normalization state, raw-count availability, reductions, metadata columns,
non-sensitive value counts, patient/sample identifiers, batch, condition, time,
compartment, outcome, and prior exclusions. Use bounded summaries and avoid
row-level patient data in reports.

## Mapping output

Every source-to-model mapping row must include:

- source artifact and field;
- patient/sample/compartment/time key;
- raw value, unit, missingness/QC state, and transformation reference;
- target node or parameter;
- mapping layer: initial state, clamp, rate, rule, or topology;
- direction, threshold/method, uncertainty band, and sensitivity variants;
- evidence class and leakage-control status.

## Delegation

- Using this skill does not require subagent creation.
- Follow the global Agent Harness delegation and review policy.
- Use `data_steward` for an independent source/schema review and
  `analysis_worker` for bounded implementation.
- The parent may apply this skill directly when capacity is unavailable.

## References

- Read `references/source-inventory.md` for known source structure and current
  unavailable checks.
- Read `references/preprocessing-contract.md` before normalization,
  aggregation, imputation, binarization, feature selection, or model mapping.
