---
name: maboss-digital-twin
description: Design, implement, and critically review patient-contextualized stochastic Boolean models with MaBoSS or PyMaBoSS. Use when constructing or changing .bnd/.cfg models, translating biological evidence into nodes and logical rules, mapping omics or secreted-protein measurements to initial states, clamps, or transition rates, defining phenotypes and perturbations, running MaBoSS simulations, or evaluating whether a claimed ADOC digital-twin result is scientifically supported.
---

# MaBoSS Digital Twin

Build an auditable chain from biological evidence to a baseline logical network,
patient context, stochastic simulation, and evidence-bounded claim. Read
`docs/AGENTS.md` before using this skill.

## Non-negotiable boundaries

- Treat a patient twin as a conditional hypothesis model, not a clinical replica.
- Keep baseline topology separate from patient personalization.
- Do not map abundance directly to Boolean activity or transition rate without a
  documented biological bridge and sensitivity analysis.
- Do not invent topology, logical operators, thresholds, rates, phenotype
  definitions, or time units.
- Interpret MaBoSS probabilities as simulated trajectory frequencies under the
  model, not literal patient outcome probabilities.
- Treat model perturbations as model-internal predictions until independently
  validated.

## Workflow

1. Write the biological question, independent unit, comparator, phenotype, and
   maximum defensible claim.
2. Audit the source schema with `adoc-data-audit`.
3. Curate a baseline network with node definitions and edge evidence. Read
   `references/model-contract.md`.
4. Pre-register the data-to-model mapping and leakage controls. Read
   `references/personalization-and-validation.md`.
5. Implement versioned `.bnd` and `.cfg` artifacts without overwriting the
   baseline.
6. Validate syntax and a small known-behavior model before using patient data.
7. Run a bounded patient smoke with declared seed, trajectories, time settings,
   and matched unperturbed control.
8. Quantify Monte Carlo stability and sensitivity to plausible thresholds,
   rates, initial states, and uncertain rules.
9. Validate against observations not used to construct or tune the model.
10. Use `adoc-result-validator` before interpretation.

## Model construction contract

For every node, record biological entity/process, spatial context, state meaning,
and observable evidence. For every edge, record source, target, sign, direction,
mechanism, citation/source, and confidence. For every logical rule, explain why
AND, OR, or NOT matches the biological interpretation.

Treat transition rates as inverse relative time scales. State whether they are
default assumptions, ordered qualitative constraints, or calibrated values.
Do not assign physical time units without external temporal calibration.

## Personalization decision order

Use the least invasive layer supported by evidence:

1. initial-state distribution;
2. node clamp;
3. transition-rate modifier;
4. logical-rule or topology change.

Record the unchanged matched baseline for every patient perturbation. If a
patient feature is uncertain or near a threshold, propagate that uncertainty
through alternative model variants instead of forcing one state.

## Required outputs

- versioned baseline `.bnd` and `.cfg`;
- node dictionary and edge-evidence table;
- explicit patient mapping table;
- model/run manifest with hashes and software versions;
- raw outputs plus validated summary tables;
- stability, assumption-sensitivity, and biological-validation reports;
- limitations and claim ceiling.

## Delegation

- Using this skill does not require subagent creation.
- Follow the global Agent Harness delegation and review policy.
- Use `maboss_modeler` only after the contract is settled.
- Require `systems_biology_reviewer` for canonical topology, mapping, phenotype,
  calibration, or scientific-claim changes.
- The parent may apply this skill directly when capacity is unavailable, but
  must not claim independent review.

## References

- Read `references/model-contract.md` when constructing or reviewing `.bnd`,
  `.cfg`, topology, rules, rates, phenotypes, or perturbations.
- Read `references/personalization-and-validation.md` when mapping ADOC data to
  patient models or designing validation and sensitivity analyses.
- Read `references/official-sources.md` before relying on version-sensitive
  MaBoSS or PyMaBoSS behavior.
