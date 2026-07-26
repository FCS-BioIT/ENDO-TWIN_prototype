# Scientific context layer

This directory translates immutable source material into reviewable modeling
contracts. It must not contain patient-level expression matrices or generated
simulation results.

- `project-context.md`: scientific objective, scope, and validation strategy.
- `evidence-register.tsv`: source observations and their permitted modeling use.
- `phase1-readouts.tsv`: phase-1 conditions, expected behavior, and success
  criteria.
- `node-candidates.tsv`: provisional nodes for curation; not accepted topology.
- `literature/`: reconciled embryo-adhesion literature package, including
  machine-readable candidate nodes, edges, mechanisms, perturbations,
  environmental factors, and reference provenance.
- `references/`: user-provided design specifications retained verbatim, with
  provenance and evidence-status notes.

Rows labeled `candidate` or `to_verify` are hypotheses or extraction tasks.
They must not be promoted to Boolean rules without evidence review.
