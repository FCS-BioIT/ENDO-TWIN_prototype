# DT_ADOC Implementation Architecture

## Objective

The implementation builds a reproducible Python and MaBoSS workflow for the
phase-1 ADOC baseline model while preserving data lineage, evidence provenance,
and claim ceilings.

## Package Flow

```text
immutable sources
  -> source and preprocessing contracts
  -> model specs (nodes, edges, rules, phenotypes, scenarios)
  -> compiled versioned MaBoSS artifacts
  -> protocol runner
  -> smoke simulation outputs
  -> stability / sensitivity summaries
  -> manifest validation
  -> provisional report
```

## Key Modules

- `dt_adoc.model`:
  spec loading, schema checks, provenance, and model compilation utilities
- `dt_adoc.protocols`:
  YAML schema validation and sequential condition execution
- `dt_adoc.personalization`:
  strict and soft mapping interfaces for later donor contextualization
- `dt_adoc.perturbations`:
  target-engagement, single, pair, and synergy utilities
- `dt_adoc.calibration`:
  bounded objectives and search helpers for phase 1B
- `dt_adoc.scoring`:
  phenotype, safety, and multi-objective candidate scoring
- `dt_adoc.simulation`:
  run orchestration, manifest writing, stability, and sensitivity helpers
- `dt_adoc.reporting`:
  smoke tables, figures, and a concise provisional report

## Phase Boundaries

- Phase 0:
  source integrity, evidence roles, preprocessing contracts, upstream-method
  inspection
- Phase 1A:
  baseline model topology, phenotype contract, sequential conditions
- Phase 1B:
  bounded calibration, smoke outputs, manifest validation, stability and
  sensitivity
- Phase 2:
  donor contextualization without topology drift
- Phase 3:
  graded perturbation screening and candidate ranking

## Claim Boundary

Every output remains a conditional model prediction under the recorded
assumptions. Structural validity, stochastic stability, assumption robustness,
and biological validation are separate gates and must never be merged into one
claim.
