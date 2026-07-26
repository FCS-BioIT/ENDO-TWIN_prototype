---
name: adoc-result-validator
description: Validate ADOC MaBoSS artifacts, stochastic simulations, scientific robustness, and result claims. Use when checking run manifests, source/model/output hashes, .bnd/.cfg pairs, patient inclusion, seeds and trajectory counts, output tables or figures, Monte Carlo stability, threshold/rate/rule sensitivity, held-out biological agreement, perturbation effects, or deciding whether a digital-twin result is safe to interpret.
---

# DT_ADOC Result Validator

Audit actual artifacts and distinguish file validity, reproducibility,
stochastic stability, assumption robustness, biological validation, and
clinical validity.

## Workflow

1. Identify the exact run directory and `run_manifest.json`.
2. Run `scripts/validate_run_manifest.py <manifest> --root <repo>`.
3. Verify referenced source, model, config, mapping, output, and log files exist
   and match recorded hashes.
4. Confirm patient inclusion/exclusion, model parentage, phenotype definitions,
   perturbations, software versions, seeds, trajectories, and time settings.
5. Inspect raw output and recompute key summaries when feasible.
6. Assess Monte Carlo stability and sensitivity to mapping/model assumptions.
7. Compare predictions with observations not used for model construction or
   tuning.
8. Read `references/claim-boundaries.md` and assign a validation level and claim
   ceiling.

## Required distinctions

- A valid manifest is not a valid model.
- A reproducible run is not a stable Monte Carlo estimate.
- A stable simulation is not robust to biological assumptions.
- Calibration agreement is not held-out validation.
- Held-out internal validation is not external or clinical validation.
- A model perturbation is not experimental causal evidence.

## Stochastic checks

Require multiple seeds and/or increased trajectory counts. For each primary
phenotype and perturbation, report an uncertainty interval or empirical
between-run variation. Mark results unstable if effect direction, rank, or
decision changes under a pre-specified tolerance.

Fixed seeds provide reproducibility only. They do not measure Monte Carlo error.

## Assumption checks

Vary plausible binarization thresholds, initial-state distributions, default or
calibrated rate ratios, uncertain edge signs and logical rules, phenotype
definitions, and missing-data handling. Separate stable conclusions from
configuration-dependent hypotheses.

## Output requirements

Report status, exact commands, return codes, checked artifacts, errors, warnings,
validation level, unverified gates, and claim ceiling. Do not summarize a partial
run as complete.

## ChatGPT review bundles

Run `pixi run chatgpt-results-bundle` from the repository root to create a
compact source/context/results archive. The task must succeed only after
`../../../scripts/validate_chatgpt_bundle.py` validates the manifest and a fresh
extraction. A valid review bundle does not imply that any included run or model
passed scientific validation.

## Delegation

- Using this skill does not require subagent creation.
- Follow the global Agent Harness delegation and review policy.
- Use `result_validator` for independent artifact review.
- Use `systems_biology_reviewer` when the unresolved question concerns model
  validity or biological interpretation.
- The parent may apply this skill directly when capacity is unavailable, but
  must not claim independent review.

## References

- Read `references/run-manifest-contract.md` when producing or validating a run
  manifest.
- Read `references/claim-boundaries.md` before interpreting, plotting, or
  writing MaBoSS results.
