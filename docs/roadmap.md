# DT_ADOC roadmap

## Phase 0 — evidence and data contracts

Status: in progress.

- Preserve immutable source hashes and complete schema audits.
- ~~Reconstruct the paper's final cell labels or obtain the final annotated
  object.~~ **DONE 2026-09-15.** Obtained, not reconstructed: ArrayExpress
  **E-MTAB-15842** `seurat_object.rds`, 28,212 cells with `celltype_v2`
  labels, sha256 `504a674d…`, recorded as `EXT-SCRNA-001` in
  `config/external_data_manifest.tsv` and hash-pinned in
  `config/scrna_observation_map.tsv`. The whole KLF12 workstream ran against
  it. Holding the object removes an availability blocker and settles no
  modelling question: see `docs/results_reproducibility_matrix.md`, where
  correcting the same stale claim across eleven rows cleared none of them.
- Map workbook columns to donor, channel, day, condition, unit, replicate, and
  detection-limit semantics.
- Extract the ligand–receptor pairs behind the IHH/BMP and SPP1 claims.
- Freeze construction, calibration, and validation evidence assignments.

Exit gate: all phase-1 inputs and readouts have machine-readable provenance and
no unresolved identifier or unit ambiguity affects modeling.

## Phase 1A — baseline topology

- Build a compact coupled epithelial–stromal prior-knowledge network.
- Accept nodes because they are needed for an input, mechanism, or readout—not
  merely because they are differentially expressed.
- Record one evidence row per edge and every alternative sign/rule.
- Define `Epithelial_Receptivity`, `Stromal_Decidualization`,
  `Adhesion_Permissive`, and `Stable_Adhesion` before fitting.
- Create untreated, HT, and HT+mifepristone configurations without changing
  topology between conditions.

Exit gate: syntax passes, provenance is complete, and an independent scientific
review accepts the phenotype and evidence contracts.

**v0.5 unit sequence and outstanding topology obligations.** The unit-level plan
is `docs/v05_mechanistic_integration_plan.md` §17 — U1–U5, U5b, U6 (schema only), U6b (evaluation only) and U8 (Stage-3 rerank; `dropout_e2` remains first) complete;
U7 pending and not needed by U8. `docs/deferred_topology_register.tsv` holds **every outstanding
topology obligation, scheduled and deferred alike** — each with its forcing
evidence, the unit that owns it where one does, and the exact conditions that
would unblock it where none does — **and, separately, any scoped closure record**,
which owes no work and is kept so a later unit can see what a closure did and did
not settle. The `state` column is what distinguishes them: `SCHEDULED` and
`DEFERRED` are outstanding; `DISCHARGED` was owed and is done (`TI-01`, by U5b; `TI-02`, by U6b as an evaluation, its executable half deferred as `TI-06`);
`CLOSED_ON_CURRENT_EVIDENCE` never owed anything. It is guarded by
`tests/unit/test_deferred_topology_register.py`. Do not treat this phase as closed
while the register holds an outstanding row whose unblock conditions are met.

## Phase 1B — calibration and validation

- Calibrate only pre-declared initial-state/rate alternatives against untreated
  and HT molecular/adhesion data.
- Quantify seed and trajectory stability.
- Perform one-at-a-time and global sensitivity over uncertain thresholds,
  rates, initial states, and alternative rules.
- Test the frozen mifepristone perturbation as held-out validation if it was not
  used in construction.
- Report ensembles of acceptable models when parameters are not identifiable.

Exit gate: the model reproduces qualitative molecular directions, gives
uncertainty-aware adhesion agreement, predicts the held-out perturbation, and
does not depend on one fragile assumption.

**Status (audit of 2026-09-24): BLOCKED.** It is derived by a fixed rule, not
chosen. See `docs/phase1b_closure_and_prospective_handoff.md` and
`docs/phase1b_closure/phase1b_exit_gate.tsv`. Adhesion agreement and the
held-out perturbation have no scheduled route. Nor does the full fragile-assumption
criterion, because threshold evidence and an alternative mifepristone encoding
are unscheduled. The frozen `dropout_e2` experiment advances the
molecular-direction and fragile-assumption criteria, but closes neither.

## Phase 2 — donor contextualization

- Aggregate scRNA-seq at donor × condition × compartment level.
- Compare PROFILE, a transparent local reimplementation, and any current
  MaBoSS-native alternative against the repository mapping contract.
- Prefer initial-state personalization; introduce rate modifiers only with
  calibration and sensitivity analysis.
- Use leave-one-donor-out exercises as exploratory stress tests, not estimates
  of population generalization.

Exit gate: donor variants preserve baseline provenance and add predictive value
beyond the shared model without evidence leakage.

**Status (Phase 2A, 2026-09-24): the input contract only.** The status is derived
by `docs/phase2a/phase2a_status.json`: numerical personalization is blocked, and
its unmet requirements are listed in `docs/phase2a/reference_gate.json`. See
`docs/phase2a/phase2a_contract.md`. No donor variant exists, so this exit gate
is untouched.

## Phase 3 — non-hormonal target hypotheses

- Define protected outputs for viability, barrier/homeostasis, and non-adhesion
  endometrial functions.
- Simulate graded single and double perturbations across donor and uncertainty
  ensembles.
- Rank effects by robustness, selectivity, mechanistic plausibility,
  accessibility, and novelty.
- Experimentally test prioritized perturbations in ADOC before any translational
  claim.

Exit gate: target hypotheses have robust simulated selectivity and orthogonal
experimental support. Safety and contraceptive efficacy remain separate
questions requiring appropriate preclinical and clinical evidence.
