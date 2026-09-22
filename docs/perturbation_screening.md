# Perturbation Screening

## Scope

Phase-3 screening ranks model-internal non-hormonal hypotheses only after the
phase-1 baseline is structurally valid and appropriately bounded.

## Target Engagement

- use fractions from `0` to `1`
- interpret them as target engagement or affected-trajectory fractions
- do not call them dose or occupancy without an external pharmacodynamic bridge

## Comparison Policy

- compare each perturbation against its matched unperturbed control
- separate efficacy outputs from safety outputs
- quantify instability across seeds, trajectory counts, and uncertain rules
- report both scalar candidate score and full component vector
- include a Pareto-front table so weight choices remain visible

## Safety Penalties

Penalize:

- epithelial death
- stromal death
- barrier damage
- chronic inflammation
- persistent senescence
- DNA damage
- excessive decidual loss
- failure to recover after washout

## Claim Boundary

Screening outputs are model predictions conditional on the implemented ADOC
network, parameter scenarios, and perturbation abstraction. They are not causal
evidence, treatment recommendations, or clinical probabilities.
