# ADOC MaBoSS digital-twin architecture

## Model hierarchy

```text
immutable sources + curated literature
                 |
                 v
       evidence-registered baseline
       epithelial <-> stromal model
          (.bnd + base .cfg)
                 |
        condition configurations
     untreated / HT / HT+mifepristone
                 |
                 v
       stochastic MaBoSS simulations
                 |
 stability + sensitivity + biological validation
                 |
                 v
    donor-contextualized variants (phase 2)
                 |
                 v
 graded perturbation ensembles (phase 3)
```

The baseline topology remains distinct from experimental condition and donor
personalization. Untreated, HT, and mifepristone comparisons must share one
topology. A topology change creates a new baseline model version.

## Biological boundary

Phase 1 models epithelial receptivity, stromal decidualization, their paracrine
coupling, and an adhesion-permissive interface. Stable embryo adhesion is an
observed probabilistic output. Embryo-intrinsic signaling is outside the first
model unless new data make it identifiable.

## Planned artifact layout

```text
models/
  baseline/<model-version>/
    network.bnd
    baseline.cfg
    conditions/
      untreated.cfg
      hormone_treated.cfg
      hormone_treated_mifepristone.cfg
    node_dictionary.tsv
    edge_evidence.tsv
    phenotype_contract.tsv
    provenance.toml
  donors/<model-version>/<donor-pseudonym>/
    donor.cfg
    mapping.tsv
    provenance.toml

output/
  smoke/<run-id>/
  full/<run-id>/
    run_manifest.json
    raw/
    tables/
    figures/
    logs/
    validation/
```

Source data remain under `data/` and are not copied into result bundles unless
explicitly authorized.

## Personalization layers

Use the least structurally invasive layer supported by evidence:

1. initial-state distributions for starting cellular context;
2. node clamps for strong constitutive activity evidence;
3. calibrated transition-rate modifiers;
4. topology or logical-rule changes only as new baseline versions.

Every mapping records direction, threshold, uncertainty, source field, source
units, and whether it was chosen before evaluating the validation phenotype.

## Validation hierarchy

Passing a lower level never implies a higher one:

- source integrity and object schema;
- model syntax and configuration compatibility;
- simulation reproducibility;
- Monte Carlo stability;
- robustness to plausible thresholds, rates, and alternative rules;
- agreement with held-out molecular and functional observations;
- external or prospective validation;
- clinical utility.

Current state: source hashes and the local RDS schema/study identity have been
audited. No canonical Boolean topology, MaBoSS runtime result, calibrated
adhesion model, or biological validation has yet been accepted.
