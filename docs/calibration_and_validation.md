# Calibration And Validation

## Evidence Roles

- Construction:
  mechanistic literature, compartment definitions, and the frozen topology/rule
  contract
- Calibration:
  untreated versus HT molecular directions, PAEP behavior, PRL/IGFBP1 behavior,
  and untreated versus HT adhesion counts
- Internal validation:
  HT plus mifepristone only if that perturbation was not used to encode or tune
  PGR antagonism

## Objectives

- binomial likelihood or deviance for published adhesion counts
- directional agreement for epithelial and stromal molecular programs
- ordinal agreement for censored temporal readouts such as PRL and IGFBP1
- penalties for unsafe or nonrecovering perturbation behavior

## Search Policy

- bounded scenario search only
- no unconstrained fitting of many rates
- retain multiple acceptable scenarios when non-identifiability persists
- label every output as calibration or validation explicitly

## Validation Levels

1. structural parsing
2. source integrity
3. synthetic runtime check
4. bounded smoke
5. stochastic stability
6. assumption sensitivity
7. biological validation
8. full reproducible run

Passing a lower level never implies a higher one.

## Current Limitation

The live repository snapshot contains the full immutable sources, but some
machine-readable annotation and workbook semantics remain unresolved. Any gate
that depends on those unavailable details must remain blocked rather than
guessed.
