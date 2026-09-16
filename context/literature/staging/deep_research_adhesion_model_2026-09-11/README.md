# dt-ADOC deep-research staging bundle - 2026-09-11

This bundle is a reviewed *staging delta*, not a replacement model.

It was constructed against `fransua-fcs/dt-ADOC_prototype` `main` at
`6bceaec7b508c3425cbdd7b14714019fb5c6955f`, with the active scientific model
`models/superset/adoc-literature-superset-v0.4.0`.

The repository already has canonical literature/model tables. Therefore these
files use collision-resistant `DR20260911-*`, `DRREF-*`, `DRMOD-*`, and
`DRUNR-*` identifiers and should be merged only after local review.

## Files

- `deep_research_adhesion_model_2026-09-11.yaml`: provenance, scope, claim boundary and promotion policy.
- `references.tsv`: literature records newly required by the proposed delta.
- `candidate_nodes.tsv`: staged node additions/refinements using the current candidate-node schema.
- `candidate_edges.tsv`: staged edge additions using the current candidate-edge schema.
- `mechanisms.tsv`: staged pathway/module summaries.
- `edge_evidence.tsv`: executable-model evidence rows for edges *if* they are promoted.
- `rule_variants.tsv`: competing Boolean hypotheses; all are catalog-only in this bundle.
- `unresolved_mechanisms.tsv`: explicit stop conditions and unresolved biology/architecture.
- `drug_target_catalog.tsv`: staged perturbation/target entries; no efficacy claims.
- `promotion_plan.tsv`: exact intended destination and merge action for each file.
- `manifest.tsv`: SHA256 and row-count verification for this bundle.

## Recommended order

1. Copy the YAML provenance under `context/literature/reviews/`.
2. Deduplicate `references.tsv` against the canonical bibliography by DOI/PMID.
3. Review and merge literature candidates into the canonical context tables.
4. Have the modeling agent decide which candidates are identifiable enough for v0.5.
5. Create a new `adoc-literature-superset-v0.5.0`; never overwrite v0.4.0.
6. Only then merge executable `edge_evidence`, `rule_variants`, unresolved items and target catalog.
7. Compile, run structural diagnostics and protocol regression tests before calibration.
8. Calibrate finite-time adhesion kinetics to ADOC outcomes before interpreting simulated occupancy as biological adhesion probability.

## Scientific guardrail

The most important change is not simply adding nodes. It is removing the
current dependence of absolute adhesion probability on hand-initialized relay
priors and replacing it with an explicit finite-time attachment/detachment
process, while preserving uncertainty about exact Boolean rule compression.
