# Claim boundaries

## Validation labels

- `structural`: files parse and contracts are complete.
- `reproducible`: recorded inputs and settings reproduce the run.
- `stochastically_stable`: primary outputs are stable across seeds/trajectory
  counts within a pre-specified tolerance.
- `assumption_robust`: conclusions remain under plausible thresholds, rates,
  initial states, and uncertain rules.
- `calibrated`: model agrees with evidence used to tune it.
- `internally_validated`: agrees with held-out observations from the same study.
- `externally_validated`: agrees in an independent cohort or experiment.
- `clinically_validated`: supported by a suitable clinical validation design.

Apply only labels supported by inspected artifacts.

## Safe language

- Structural: “The model is executable under the recorded configuration.”
- Stable: “The simulated phenotype estimate was stable under the tested Monte
  Carlo settings.”
- Assumption robust: “The direction persisted across the tested model and
  personalization assumptions.”
- Internal validation: “The model agreed with held-out observations from this
  study under the stated metric.”
- Unvalidated perturbation: “The model predicts, conditional on its assumptions,
  that the perturbation changes the simulated phenotype.”

Do not replace these with “the patient will respond,” “causes,” “proves,” or
“clinically validated” without matching evidence.
