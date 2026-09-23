# ADOC Literature Superset v0.5.1 — U5b readout repair

**Status: increment of v0.5.0 by exactly one rule.** This is the first
mechanism-changing version of the v0.5 line
(`docs/v05_mechanistic_integration_plan.md` §17, U5b). v0.5.0 is not edited: it
stays the object U5 audited, and this directory is the delta.

## The one change

```
OUT_STROMAL_DECIDUALIZED = S_DECIDUALIZED and S_PRL and S_IGFBP1   (v0.5.0)
OUT_STROMAL_DECIDUALIZED = S_DECIDUALIZED                             (v0.5.1)
```

`S_PRL` and `S_IGFBP1` are calibration readouts (`OM-002`, `SOFIA-STR-001`). A
reported phenotype that is gated on them uses an observation marker as a causal
gate, which becomes a real defect the moment the two markers get rules of their
own. The repair has to land before any de-aliasing, and this is it
(`docs/deferred_topology_register.tsv`, `TI-01`).

## What does not move, and what does

- **The composed Boolean function of every node is unchanged.** The two conjuncts
  are absorbed in all 2^19 free-variable assignments, and every node's truth
  table is compared against v0.5.0's in `docs/u5b_readout_repair/`. So the fixed
  point cannot move: 35 distinct functions, 19 free variables, AC01 = 9, decidual
  class = 6, as before.
- **The node is a leaf.** No rule reads `OUT_STROMAL_DECIDUALIZED`, and
  `OUT_MATERNAL_ADHESION_COMPETENCE` reads `S_DECIDUALIZED` directly, so no other
  node's behaviour can change — only the realisation of it under common random
  numbers.
- **The transient does move, and is measured, not assumed.** Under asynchronous
  updating v0.5.0's readout waits for `S_PRL` and `S_IGFBP1`; v0.5.1's does not.
  See `docs/v05_u5b_readout_repair.md` for the paired comparison and its
  pre-registration.
- **Two curated edges stop executing.** `LE079` and `LE080` are `retired` in
  `topology.tsv` against `topology_increment_adjudications.tsv` and are kept in
  `edge_evidence.tsv` as history.

## What it is not

- **Not a new biological claim.** Removing a marker gate from a readout asserts
  nothing about decidualisation. The claim ceiling in `provenance.toml` is
  unchanged.
- **Not generator output of `dt_adoc.model.superset_family`**, whose
  `MODEL_VERSION` still targets v0.4.0. It is emitted by
  `dt_adoc.reporting.u5b_increment` from v0.5.0, and
  `tests/unit/test_v05_u5b_readout_repair.py` rebuilds it byte for byte.
- **Not a calibrated or personalized model.** MaBoSS probabilities are simulated
  trajectory frequencies under stated rules, rates and initial conditions, and
  MaBoSS time is relative.

## Artifacts

Identical to v0.5.0 except the files listed under `[increment]` in
`provenance.toml`; see v0.4.0's `README.md` for the artifact inventory, scope and
claim boundary, all of which continue to apply.
