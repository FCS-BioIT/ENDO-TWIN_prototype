# Scientific Review Checklist

## Question And Design

- Is the biological question explicit?
- Is the independent biological unit correct?
- Are inclusion, exclusion, pairing, time, compartment, and batch explicit?
- Is calibration separated from validation?

## Data Processing

- Are raw, QC, transformed, and binarized values separate?
- Are zeros, blanks, missing, and below-detection states preserved?
- Are units and normalization justified?
- Are patient/sample identifiers unique and traceable?
- Is outcome leakage excluded?

## Logical Model

- Does every node have a biological definition?
- Does every edge have direction, sign, source, and confidence?
- Are AND/OR/NOT choices biologically justified?
- Are topology uncertainty and alternative rules tested?
- Are initial conditions and phenotype outputs pre-specified?

## MaBoSS Simulation

- Are `.bnd` and `.cfg` versions and hashes recorded?
- Are rates evidence-derived or clearly labeled assumptions?
- Are time units relative unless calibrated?
- Are seed, trajectory count, time horizon, and time tick recorded?
- Is Monte Carlo stability quantified?
- Are matched unperturbed controls present?

## Validation And Claims

- Are syntactic, stochastic, sensitivity, biological, and external validation
  reported separately?
- Are results stable to plausible thresholds, rates, and uncertain rules?
- Are predictions tested on data not used to construct them?
- Are model-internal perturbations distinguished from causal evidence?
- Does every table, figure, and sentence respect the claim ceiling?
