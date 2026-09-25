# Personalization strategy

## What is borrowed from Montagud et al. (2022)

The useful pattern is:

1. construct and validate one generic mechanistic Boolean model;
2. map individual molecular profiles onto MaBoSS variables without rewriting
   the generic regulatory logic;
3. simulate matched baseline and perturbation conditions; and
4. evaluate graded single and double inhibition on the personalized models.

In PROFILE, discrete alterations can clamp nodes, while continuous expression
can modify initial conditions and transition rates. PROFILE_v2 represents
partial inhibition through ensembles of trajectories with different node
activity fractions.

This is methodological inspiration, not an automatic recipe for ADOC. The
published code is a reproducibility repository built around specific cancer
models and data-processing assumptions. DT_ADOC must make its mapping explicit
and test it against endometrial biology.

## Proposed ADOC recipe

For phase 2, create donor × condition × compartment summaries using the donor as
the independent unit. For every model node, store:

- source gene(s) or signature;
- assay and transformation;
- donor/condition/compartment;
- missingness and detection support;
- normalization reference;
- mapping function and threshold;
- resulting initial-state probability, clamp, or rate modifier;
- uncertainty range; and
- whether the choice preceded evaluation of the target phenotype.

Use the least invasive supported mapping:

1. **Initial-state probability:** default for continuous expression/state
   evidence.
2. **Clamp:** only for strong constitutive loss/gain evidence; scRNA dropout is
   not such evidence.
3. **Transition rate:** only if the abundance-to-rate bridge is declared,
   calibrated, and sensitivity-tested.
4. **Topology/rule:** never changed per donor without independent mechanistic
   evidence and a separate model version.

Because only three donors are currently represented, do not optimize thresholds
for association with donor-specific adhesion. Prefer thresholds defined from
external biology, measurement models, or broad sensitivity ensembles.

## PROFILE and PROFILE_v2 adoption gate

Before importing code or choosing a built-in replacement:

- pin and inspect the exact release and license;
- reproduce its tutorial on a bundled example;
- determine whether it supports the installed MaBoSS/PyMaBoSS version;
- inspect how it handles missing genes, duplicated identifiers, scaling,
  clipping, and zero expression;
- compare generated `.bnd`/`.cfg` changes against a transparent local mapping;
- add fixture-based regression tests; and
- record deviations from the 2022 workflow.

Until that gate passes, the repository treats PROFILE and PROFILE_v2 as
reference methods, not dependencies.

## Perturbation interpretation

Graded activity fractions are stochastic scenario mixtures, not measured drug
concentrations. A 40% node inhibition simulation must not be called a 40% dose
or target occupancy unless an external pharmacodynamic model supplies that
mapping.

## Method references

- Montagud A et al. (2022), *Patient-specific Boolean models of signalling
  networks guide personalised treatments*, eLife 11:e72626,
  https://doi.org/10.7554/eLife.72626.
- PROFILE source and tutorial: https://github.com/sysbio-curie/PROFILE.
- PROFILE_v2 source and graded-inhibition workflow:
  https://github.com/ArnauMontagud/PROFILE_v2.

Pin an exact revision before adopting either codebase; a moving repository URL
is not sufficient provenance for a model run.
