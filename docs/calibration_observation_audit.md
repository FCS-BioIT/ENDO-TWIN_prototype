# Calibration observation audit

Status: data/contract layer only, 2026-07-28. This document audits
`config/observation_model_map.tsv`, which replaced the inert
`directional_readouts` stub in `config/calibration.yaml` (the stub named one
`protocol_id` per readout with no comparator arm, so it could not express a
contrast). No model, rule, rate, protocol duration, or recalibration was run
or changed while producing this audit. `adhesion_objective` in
`config/calibration.yaml` was the sole magnitude-fitted (scored) term when this
audit was written; it was **demoted to `diagnostic_ordinal` on 2026-09-16**
(`docs/gate3_scope_adjudication.md` §3), so **no magnitude-fitted term remains
anywhere**. That strengthens rather than weakens what follows: everything
described below is a pass/fail feasibility gate, a non-exclusionary diagnostic,
or reported-only, and that is now the whole of the calibration layer.

## Sources

- `input_tables/adoc_secreted_proteins.tsv` -- canonical secreted-protein
  table, 62 rows (PAEP 14, IGFBP-1 30, PRL 18).
- `context/phase1-readouts.tsv` -- registered Phase 1 readouts (`P1-*`).
- `context/evidence-register.tsv` -- evidence IDs (`SOFIA-*`, `LIT-*`).
- `config/protocols.yaml` -- protocol definitions for `adoc-literature-v0.2.0`.
- `models/extended/adoc-literature-v0.2.0/node_dictionary.tsv` -- the node
  vocabulary every `model_nodes` entry in the mapping table is checked
  against (`tests/unit/test_observation_map.py`).

## Combination rule

Lexicographic. `adhesion_objective` (binomial log-likelihood on
`adhesion_challenge_*`, mifepristone arm `validation_if_held_out`) is the sole
scored term and is unchanged. Rows in `config/observation_model_map.tsv` with
`activation_status=active_constraint` are pass/fail feasibility filters
applied to the retained ensemble after the adhesion ranking. Rows with
`activation_status=active_diagnostic` are evaluated and reported every run
but never exclude a candidate on their own. Rows with `activation_status` in
`{reported_only, provisional, rejected}` are descriptive only. There is no
weighted sum and no numeric weight on any directional row -- the `weight`
column is empty for every row in this table.

## Horizon decision (governs every activated row)

`docs/endpoint_convergence_finding.md` ("Horizon decision") settled the open
question of *when* a protocol's endpoint is read: at the **converged logical
fixed point**, not a fitted finite time. That decision, made and verified
outside this data/contract layer, governs both rows below:

- MaBoSS relative time remains uncalibrated regardless of horizon choice
  (`provenance.toml` declares `maboss_time_units = "relative_only"`). The
  fixed-point horizon is a dimensionless simulation parameter -- it is never
  "6 days" and must never be reported as a protocol duration.
- The constraint nodes are themselves horizon-sensitive and saturate at the
  fixed point:

  | node | max_time 4.0 (declared) | max_time 8.0 | max_time 15.0 | max_time 30.0 |
  |---|---|---|---|---|
  | `E_PAEP` (`hormone_treated_maternal`) | 0.7568 | 0.9867 | 1.0000 | 1.0000 |
  | `S_IGFBP1` (`hormone_treated_maternal`) | 0.4594 | 0.9368 | 0.9994 | 1.0000 |

  Both comparators (`e2_primed_maternal`, `basal_maternal`) read 0.0000 for
  these nodes at every horizon tested. At the fixed point, both checks
  therefore become **binary**: 1.0 vs 0.0. They still detect an inversion --
  a genuine failure mode worth guarding against -- but they carry **no graded
  ranking power** at that horizon. At the declared (unconverged) duration
  they are graded but read mid-transient, which is why the fixed point was
  chosen instead (see the rejected-finite-time discussion in
  `docs/endpoint_convergence_finding.md`). Do not read either constraint as
  more discriminating than this.

## Activated rows

### OM-001 -- PAEP direction (primary feasibility gate)

- Source: `input_tables/adoc_secreted_proteins.tsv`, 10 `observed` rows
  (series `PAEP_S11-1`, `PAEP_S7.1`, `PAEP_S10-2`, `PAEP_S7.2`, `PAEP_S11 2`,
  two conditions each; cells `B3,E3,F3,G3,H3,B4,E4,F4,G4,H4`).
  `PAEP_S1`/`PAEP_S2` excluded (`measurement_state=missing`,
  `quality_tier=exploratory`, cells `C3/D3/C4/D4`).
- Protocols: `e2_primed_maternal` -> `hormone_treated_maternal`.
- Model node: `E_PAEP` only.
- Target type: directional. `P(E_PAEP=ON | hormone_treated_maternal) >
  P(E_PAEP=ON | e2_primed_maternal)`.
- Calibration/validation role: `calibration_constraint`,
  `activation_status=active_constraint`. A violation excludes the candidate
  from the retained ensemble.
- Confidence: moderate. Direction consistent 5/5 chips; magnitudes
  heterogeneous (9.5x-57.6x across chips) and never fitted.
- Weight: none (pass/fail only).
- Exclusion reason: n/a (activated).

**Registered-vs-actual comparator discrepancy.** `context/phase1-readouts.tsv`
row `P1-PAEP` states the comparator is **"HT versus untreated"**. The
workbook has **no untreated PAEP arm at all** -- only the verbatim workbook
labels `HT (E2 only)` vs `HT (E2+P4+XAV939)`. `OM-001` therefore supports a
narrower claim than the registered readout and must not be read as evidence for
"HT vs untreated". Note the second source label is itself wrong twice over: the
progestin was MPA 1 uM, not P4, and the label omits cAMP 0.25 mM, so the actual
condition is `E2 + MPA + cAMP + XAV939` (SOFIA-COMM-004). The label is quoted
here as provenance, never as a description of the treatment.
Both the registered and actual comparator text are recorded verbatim in the
mapping row (`registered_comparator`, `actual_comparator` columns).

### OM-002 -- IGFBP-1 non-inversion diagnostic (demoted from a hard gate)

- Source: `input_tables/adoc_secreted_proteins.tsv`, IGFBP-1 BOTTOM day 0 and
  day 6 (labelled "Day 7" in the workbook, resolved to protocol day 6), 10
  cells (`G3,H3,I3,J3,K3,G5,H5,I5,J5,K5`).
- Protocols: `basal_maternal` -> `hormone_treated_maternal`.
- Model node: `S_IGFBP1` only.
- Target type: directional. `P(S_IGFBP1=ON | hormone_treated_maternal) >
  P(S_IGFBP1=ON | basal_maternal)`.
- Calibration/validation role: `diagnostic`,
  `activation_status=active_diagnostic`,
  `objective_treatment=non_inversion_diagnostic_secondary_ranking`. Evaluated
  and reported every run; flags an inversion (simulated `basal_maternal` >
  simulated `hormone_treated_maternal` on `S_IGFBP1`) only, and **never
  excludes a candidate on its own** -- unlike `E_PAEP`, this is not a hard
  gate.
- Confidence: low-moderate.
- Weight: none.
- Support: **3/5 units** (fails `BOTTOM_4`: day6=0 <= day0=65.18 pg/mL;
  `BOTTOM_5`: day6=0 <= day0=37.90 pg/mL). Both failing units are the
  ambiguous day-6 zero cells (IGFBP-1 detection limit 5 pg/mL per
  `SOFIA-STR-001`; below-detection cannot be distinguished from a true zero
  here). Chip identity is also not verified as paired across day blocks
  (the source table records no `chip_id` for IGFBP-1/PRL series, unlike
  PAEP). Collectively this is too weak to gate the retained ensemble, hence
  the demotion from constraint to diagnostic.

Why demoted rather than activated at 4/5 or 5/5 as originally proposed: an
earlier review's fraction counts were wrong (see the recount below), the
`day3` comparator has no protocol counterpart (see the protocol-coverage gap
below), and two of five units carry ambiguous zeros. `E_PAEP` remains the
sole hard feasibility gate.

## Rejected rows (audit trail of what was considered and refused)

Recounted directly from `input_tables/adoc_secreted_proteins.tsv` IGFBP-1
BOTTOM series (`BOTTOM_1..5`, protocol days 0/3/6); these supersede an
earlier review's misreported fractions:

| comparison | supporting fraction | failing units |
|---|---|---|
| strictly monotone day0 < day3 < day6 | **1/5** | 4 of 5 units break strict ordering somewhere |
| day3 > day0 | 4/5 | `BOTTOM_3` (day0=551.26 > day3=261.69) |
| day6 > day0 | 3/5 | `BOTTOM_4`, `BOTTOM_5` (both day6=0) |
| day6 > day3 | 2/5 | `BOTTOM_2`, `BOTTOM_4`, `BOTTOM_5` |

Ambiguous zero-valued BOTTOM cells (below-detection vs. true zero cannot be
distinguished from the source table alone): `BOTTOM_2` day 0, `BOTTOM_4` day
6, `BOTTOM_5` day 6.

- **OM-003** (rejected): strict monotone day0<day3<day6, 1/5 support. Falsified
  by the data; also has no protocol counterpart for day 3 (see OM-004/OM-011).
- **OM-004** (rejected): day3 > day0, 4/5 support **on the raw data**, but
  rejected outright for a **protocol-coverage gap, not a data problem**: the
  manuscript chronology is 2 days of E2-only priming followed by 4 days of
  the full E2+MPA+cAMP+XAV939 cocktail, so experimental day 3 is already one
  day into the full-cocktail phase. The model's only E2-only protocol,
  `e2_primed_maternal` (`relative_duration=2.0`), represents approximately
  day 2, not day 3. No protocol in `config/protocols.yaml` represents a
  partial full-cocktail (mid-day-3) maternal state, so the day-3
  measurements -- which are good data -- have no model comparator to be
  checked against.
- **OM-005** (rejected): day6 > day3, 2/5 support on the raw data;
  independently rejected because day 3 has no protocol counterpart.
- **OM-011** (rejected, `target_type=protocol_coverage_gap`): explicit
  **"experimental metadata still needed"** entry. A protocol representing the
  partial-treatment day-3 maternal state (roughly one day into the 4-day
  cocktail phase) would make the day-3 IGFBP-1 (OM-004) and day-3 PRL rows
  (part of OM-006) usable -- without it, one third of the assayed HT time
  course remains unmappable to any model comparator.

None of these rejected comparisons is activated as a constraint or
diagnostic; each carries its `exclusion_reason` and supporting fraction in
the mapping table so the rejection is auditable rather than invisible.

## Reported-only rows

- **OM-006 (PRL, all)**: `calibration_role=context_only`,
  `activation_status=provisional`, `calibration_eligible=false` expressed as
  the role value (not as a fractional weight, which would smuggle in an
  unverified TOP/BOTTOM exchange rate). Reason: the PRL sheet has no header
  row at all; the TOP/BOTTOM split is `context_document_unverified`, with
  only 3+3 columns and no workbook-native label to check it against. Never
  `active_constraint` or `active_diagnostic`.
- **OM-007 / OM-008 (TOP compartment sanity checks, PRL and IGFBP-1)**:
  `target_type=compartment_sanity_check`, `activation_status=reported_only`,
  `model_nodes` empty. Assert only "TOP should not systematically exceed
  BOTTOM for a stromal readout" as an assay-QC diagnostic; never expressed as
  a term on `S_PRL` or `S_IGFBP1`.
- **OM-009 / OM-010 (composite phenotypes)**: `OUT_EPITHELIAL_RECEPTIVE` /
  `OUT_STROMAL_DECIDUALIZED`, `activation_status=reported_only`. Reason: both
  conflate several distinct markers into one composite node against
  single-analyte assay designs, and both are read by an embryo-challenge
  endpoint that is sampled before the network converges (per
  `docs/endpoint_convergence_finding.md`). Diagnostic only.

## Sequential protocol state -- verified, not assumed

The `hormone_treated_maternal` and `e2_primed_maternal` protocols consumed by
OM-001/OM-002 genuinely transfer joint continuation state rather than
resetting between phases; this was checked, not assumed:

- `e2_primed_maternal` receives 17 memory nodes / 32 retained states from
  `basal_maternal`, in `joint` continuation mode.
- `hormone_treated_maternal` receives 35 memory nodes / 256 retained states
  from `e2_primed_maternal`, also in `joint` mode.
- Running `hormone_treated_maternal` from the `e2_primed_maternal` ancestor
  versus directly from `basal_maternal` gives measurably different results
  (`E_PAEP` 0.7568 vs 0.7590; `S_IGFBP1` 0.4594 vs 0.4532). **These are
  DECLARED-horizon values** (`max_time` 4.0 for the HT phase, `time_tick` 0.1,
  5000 trajectories, seed 1) — the same unconverged class that
  [`docs/endpoint_convergence_finding.md`](endpoint_convergence_finding.md)
  later showed is read ~4000x before the logical fixed point. At the converged
  horizon both nodes saturate to 1.0000 and the lineage difference vanishes, so
  this diagnostic exists only in the transient.
  **Correction, 2026-07-29:** the original claim that "every difference exceeds
  roughly 3x the across-seed standard deviation (~0.0001)" does not hold. The
  across-seed spread understates the sampling error, because cmaboss allocates
  initial states proportionally and the seed varies only update ordering. The
  honest floor comes from the model's own exchangeable-node null control —
  `S_PRL`, `S_IGFBP1`, `S_SPP1` and `S_TAZ_ECM` share byte-identical logic and
  span **0.0036** at the declared horizon. That floor is larger than the 0.0022
  gap this argument rested on. The lineage difference is real (it is reproducible
  and seed-independent) but it is not resolved by this comparison.

## Claim ceiling

- There is **no magnitude-fitted claim in this calibration layer at all**.
  `adhesion_objective` was the only one and was demoted to `diagnostic_ordinal`
  on 2026-09-16; no replacement scalar was manufactured. What survives from it
  is the ordinal claim `untreated < hormone_treated > mifepristone`.
- `E_PAEP` (OM-001) supports only "full HT > E2-only priming" -- quoting the
  verbatim workbook labels, "full HT (E2+P4+XAV939) > E2-only priming", where
  the actual treated condition is `E2 + MPA + cAMP + XAV939`. It is not the
  registered "HT versus untreated" claim, which has no matching data.
- `S_IGFBP1` (OM-002) supports only a non-exclusionary inversion check
  between `basal_maternal` and `hormone_treated_maternal` -- no day-3 claim,
  no monotone claim, no magnitude claim.
- No row in this table asserts a magnitude, a rate, or a day
  correspondence. Physical time is not calibrated: MaBoSS relative time
  stays dimensionless regardless of which horizon a run uses, and the
  fixed-point horizon chosen for evaluating these constraints is itself a
  simulation parameter, never a day count.
- PRL, TOP compartment checks, and the two composite phenotypes carry no
  calibration or validation claim at all -- diagnostic/context only.
- The IGFBP-1 day-3 gap (OM-004, OM-005, OM-011) is recorded as a modeling
  gap, not evidence against the underlying data, which remain usable once a
  matching protocol exists.

## Implementation

- Loader/validator: `src/dt_adoc/calibration/observation_map.py`,
  `load_observation_map(root)`.
- Evaluator: `evaluate_directional_constraints(simulated, rows)`, a pure
  function over already-simulated `{protocol_id: {node_id: probability}}`
  values -- it never runs MaBoSS and never converts a pg/mL concentration
  into a probability. `ConstraintCheck.excludes_candidate` distinguishes an
  `active_constraint` violation (excludes) from an `active_diagnostic`
  violation (reported only).
- Tests: `tests/unit/test_observation_map.py`.
