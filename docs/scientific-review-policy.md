# Scientific review policy

Scientific review must challenge both code correctness and the biological
meaning assigned to each transformation.

## Critical questions

1. What independent observation could falsify the model or personalization
   rule?
2. Which decisions were fixed before viewing the phenotype?
3. Does the evidence constrain topology, node state, transition rate, or only
   contextual plausibility?
4. Which results change under plausible thresholds, uncertain logical rules,
   initial conditions, or rates?
5. Are simulated probabilities being over-interpreted as patient outcome
   probabilities?
6. Is the same observation used for construction, tuning, and validation?
7. Are patients treated as independent units where claims are patient-level?

## Evidence classes

Use separate labels:

- `source_observation`: measured value or documented source statement.
- `curated_evidence`: externally supported node, edge, sign, or phenotype.
- `model_assumption`: rule, threshold, initial distribution, or rate without
  direct calibration.
- `calibration_result`: agreement on data used to tune the model.
- `internal_validation`: held-out observations from the same study.
- `external_validation`: observations from a separate cohort or experiment.
- `model_prediction`: unobserved result conditional on the current model.

Never collapse these into a single confidence score without a documented,
validated scoring system.

## Minimum reporting

Every scientific result must include:

- model and data versions;
- independent unit and sample/patient coverage;
- mapping and phenotype definitions;
- simulation settings and Monte Carlo uncertainty;
- sensitivity results;
- validation level;
- exclusions and unresolved limitations;
- a claim sentence that stays within the evidence class.
