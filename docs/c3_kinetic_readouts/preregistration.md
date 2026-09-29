# C3a — kinetic readouts of the current perturbations, pre-registered

**Frozen before any C3a simulation is run.** This file is committed on its own,
ahead of the code and outputs that implement it, so the order is checkable from
history. Nothing below may change after the run starts. A deviation is recorded
as a deviation in the unit record, never as an edit to this file.

No C3a simulation, pilot or timing run has been executed.

The runtime estimate in section 13 is extrapolated from the v0.5.2 sizing
pilot, not measured.

**Wording amendments, 2026-09-29, before any simulation.** No design value,
rule, count, seed, margin, quantile or classification boundary changed.

- `ccb7789` reworded sections 7 and 9.
- The owner-review correction that follows it supersedes that wording:
  - sections 7, 8 and 10 describe empirical paired-block reproducibility bands
    and claim no coverage;
  - section 9 defines the zero-occupancy sub-label narrowly;
  - section 4 states how the fixed-point run is constructed.

## 1. Question and claim ceiling

C3 of the 163-paper re-audit (`SRC-006` section 4.1) asks that perturbations be
scored on dynamics as well as on fixed-point truth values. C3a asks, for the
existing hard perturbations on the pinned model:

> Relative to a schedule-matched unperturbed twin, does the perturbation
> materially suppress the stable-adhesion state at the fixed point, only over
> the declared finite challenge window, or neither?

- **Model:** `adoc-literature-superset-v0.5.2`, unchanged. It declares no
  `rate_up`/`rate_down`, so every transition runs at the MaBoSS default. No rate
  value, rate prior, model version, rule, protocol or horizon is added (owner
  decision 2026-09-29; C3b numerical rate priors are deferred).
- **Time** is dimensionless MaBoSS relative time, never hours or days
  (`calibrated_physical_time: false`).
- **Ceiling:** every result is a statement about this Boolean model under
  default rates: "under unit MaBoSS rates, the model's topology produces …".
  It is not a biological delay or block, not an experimental prediction in
  physical time, and not validation.
- **C4 is separate.** C3a evaluates the dynamics that the current hard
  `IN_ANTI_SPP1` clamp produces. It does not justify or implement a partial or
  rate-based anti-SPP1 penalty.

## 2. Readouts

- **Primary:** `OUT_STABLE_ADHESION`.
- **Secondary:** `OUT_MATERNAL_ADHESION_COMPETENCE`, its maternal-side parent
  (`OUT_STABLE_ADHESION = OUT_MATERNAL_ADHESION_COMPETENCE and IN_EMBRYO_PRESENT
  and IN_TROPHECTODERM_COMPETENT and IN_EMBRYO_CONTACT`).

## 3. Matched pairs

Every phase uses an existing v0.5.2 condition file and its declared continuation
rule. `config/protocols.yaml` and the model files are not modified.

| pair | control lineage (phase: duration) | perturbed lineage (phase: duration) | differing input |
|---|---|---|---|
| `anti_spp1` | basal 1 → E2 2 → HT 4 → **HT extension 2** → challenge 1 | basal 1 → E2 2 → HT 4 → anti-SPP1 maternal 2 → anti-SPP1 challenge 1 | `IN_ANTI_SPP1`, phases 4–5 |
| `mifepristone` | basal 1 → E2 2 → HT 4 → **HT extension 2** → challenge 1 | basal 1 → E2 2 → HT 4 → mifepristone maternal 2 → mifepristone challenge 1 | `IN_MIFEPRISTONE`, phases 4–5 |
| `hand2_loss` | basal 1 → E2 2 → HT 4 → challenge 1 (declared lineage) | basal 1 → E2 2 → HT with HAND2 loss 4 → HAND2-loss challenge 1 (declared lineage) | `IN_HAND2_LOSS`, phases 3–4 |

- **The perturbed lineages are the declared ones**, unchanged. The onset of each
  perturbation is where the declared protocol puts it.
- **The HT extension is a schedule-matching counterfactual.** It is analysis
  only, not a measured ADOC condition and not a protocol arm. It is the
  `hormone_treated_maternal` condition, with its inputs and continuation rule
  (`joint`, `extended_maternal_joint`, cutoff 1e-6), run for exactly the
  perturbation phase's declared relative duration (2.0, read from the
  perturbation protocol, never typed in), continued from the end of the HT
  phase. It is executed with `run_protocol`'s existing `phase_horizon` override,
  which leaves the declared value untouched.
- **The anti-SPP1 and mifepristone pairs share one control lineage.** Both
  extensions are the same HT extension of the same duration, so it is run once
  per block. The two contrasts are therefore not independent; the multiplier of
  section 8 is applied to them unchanged.
- **Verified before this freeze, without simulation**, from the resolved
  protocols: within each pair the phase count and every phase duration are
  identical; the inputs are identical except the named perturbation input in
  the named phases; each pair's phases share the same continuation rule; and
  the condition files of each pair differ in exactly that one input line.
- **Declared-but-unmatched comparisons**, reported as descriptive only (section
  11): the anti-SPP1 and mifepristone perturbed lineages against the declared
  twin `adhesion_challenge_hormone_treated`, whose challenge starts 2.0 units
  earlier. They never enter the classifier.

## 4. Horizons

Only the two horizons the repository already uses:

- **Finite window:** the challenge phase at its declared `relative_duration`
  (1.0).
- **Fixed point:** the challenge phase at the existing converged horizon
  `CONVERGED_PHASE_HORIZON` = 25.0 (`docs/endpoint_convergence_finding.md`,
  "Horizon decision"), continued from the same pre-challenge state.

**How the fixed-point run is constructed.** C3a reuses the repository's
existing numerical challenge horizons, 1.0 and 25.0.

- Its fixed-point construction extends **only the final challenge phase** to
  25.0.
- Every pre-challenge phase keeps its declared duration, and the continuation
  state that results from it.
- The implementation must therefore not call the existing
  `run_arm(horizon_class="converged")`, which overrides every phase to 25.0.

This clarifies the construction already frozen here; it is not a new
methodological choice.

No other horizon, crossing threshold or physical-time mapping is introduced.

## 5. Simulation design

- **Blocks:** `R = 20` disjoint seed blocks.
- **Governing count:** `N = 20,000` trajectories per block,
  `seed_r = 2,000,001 + r·20,000` for `r = 0 … 19` (seeds 2,000,001 to
  2,400,000).
- **Check count:** `N = 2,000`, `seed_r = 2,400,001 + r·2,000` (seeds 2,400,001
  to 2,440,000).
- **Disjointness:** these ranges overlap none used before. Those are U5b and
  v0.5.2 run 1 (1–440,000), v0.5.2 run 2 (1,000,001–1,440,000), and the v0.5.2
  sizing pilot (10,000,000 and above).
- **Common random numbers:** within a block every phase of every lineage uses
  `seed_r`, so each control and perturbed phase share a seed. Pairing is variance
  reduction only: once the lineages diverge the streams are consumed
  differently, and the paired difference carries Monte Carlo error.
- **Execution:** as in v0.5.2, the lineage chain uses projected continuation
  between phases, and shared lineage prefixes are run once per block.

## 6. Estimands

For pair `p`, readout `X` and block `r`, with `P(t)` the per-tick `P(X = ON)` of
the challenge phase:

- **Finite-window occupancy difference:**
  `O_r = mean_t [P_pert(t) − P_ctrl(t)]` over the ticks of the challenge phase at
  its declared duration. This is the `time_averaged` estimand of U5b and v0.5.2,
  over the same tick set (the MaBoSS `nodes_probtraj` index of that phase).
- **Fixed-point difference:** `F_r = P_pert − P_ctrl` at the final tick of the
  challenge phase at the converged horizon.
- **Rounding:** a per-tick difference with `|d| ≤ 1e-12` counts as exactly 0,
  the rule of v0.5.2 addendum 01 (A2).

`O` is an occupancy, not a probability that any tissue adheres, and not a
hitting time.

## 7. Empirical paired-block reproducibility bands

Each estimand is summarised by an **empirical paired-block reproducibility
band**:

`mean ± t₁₉ · SD / √R`

- The mean and SD are taken over the `R = 20` per-block paired differences at
  `N = 20,000`.
- `t₁₉ = 2.943895` is the two-sided quantile at `0.05 / 6` per estimand, the
  pre-registered multiplicity-adjusted multiplier (section 8).

The band quantifies how reproducible the paired estimate is across the 20
disjoint simulation blocks.

- **No formal claim:** no confidence-interval coverage and no family-wise error
  control is claimed for it.
- **Not other variability:** it carries no biological, experimental or
  between-patient variability.
- **Kept apart from the margin:** material equivalence is defined separately,
  by a fixed margin (section 9).

## 8. Families and multiplicity

- **Primary family:** `OUT_STABLE_ADHESION`, three pairs × two estimands = **6
  bands**, each with the two-sided multiplier at `0.05 / 6`.
- **Secondary family:** `OUT_MATERNAL_ADHESION_COMPETENCE`, the same 6
  bands, each with the multiplier at `0.05 / 6`, classified by the same table but reported
  separately.
- The same Bonferroni-type multiplier is applied to the six estimands of each
  family. It is the pre-registered multiplicity adjustment.
- Descriptive outputs (section 11) are not in any family and are never
  classified.

## 9. Classification, declared now

**Margin `δ = 0.005`** in occupancy/probability units: a fixed practical margin
for material equivalence, the value U5b and v0.5.2 used. It is not derived from
the across-block SD or from any C3a result.

For the band `I` of one estimand:

- **materially suppressed:** `I` lies wholly below `−δ`;
- **equivalent:** `I` lies wholly inside `[−δ, δ]`, including a degenerate
  `[0, 0]` when every block difference is exactly 0.

For each pair and readout, from the fixed-point band `I_F` and the
finite-window band `I_O`:

| `I_F` | `I_O` | class |
|---|---|---|
| materially suppressed | any | **`PERSISTENT_SUPPRESSION`** |
| equivalent | materially suppressed | **transient suppression, consistent with delay** |
| equivalent | equivalent | **no material difference detected** |
| anything else | anything else | **indeterminate** |

- **Order:** the first row that matches applies.
- **Increases:** a band wholly above `+δ` falls under "indeterminate", with
  the direction recorded as a descriptive sub-label ("material increase"). It is
  never reinterpreted as another class.
- **No literal block.** `PERSISTENT_SUPPRESSION` is never called a literal,
  complete or biological block.
- **Zero-occupancy sub-label** `NO_ON_OCCUPANCY_OBSERVED_AT_RECORDED_TICKS`:
  - **Definition:** the perturbed arm's empirical `P(X = ON)` is exactly zero at
    every recorded tick of the converged challenge phase, in every governing
    block.
  - **What it shows:** only that no ON occupancy was observed at the recorded
    ticks. It does not show that no simulated trajectory entered the state
    between recorded ticks.
  - **What it does not license:** "unreachable", "impossible", "never reached"
    or "complete block".
  - **Structural unreachability** would need a separate logical or exhaustive
    proof, which C3a does not perform.
- **"No material difference detected"** means no difference beyond `δ` at this
  precision. It never means no difference.
- **No directional expectation** is declared for any pair.

## 10. Trajectory-count sensitivity check

`N = 20,000` is the governing analysis. `N = 2,000` is only a numerical Monte
Carlo sensitivity check, and it never overrides a numerically compatible
governing result.

For every classified band, compare the two block means `D̄` of that
estimand. The numerical compatibility criterion is:

`|D̄₂ₖ − D̄₂₀ₖ| ≤ q·√(SE₂ₖ² + SE₂₀ₖ²)`

- `SE` is the across-block standard error, `sd / √20`.
- `q = 2.638257`, the two-sided normal quantile at `0.05 / 6` per estimand,
  the same for both families. It is frozen here.

For each estimand:

| criterion | labels at the two counts | record | governing label |
|---|---|---|---|
| passes | same | `STABLE` | the `N = 20,000` label |
| passes | differ | `LOW_COUNT_LABEL_DIFFERENCE` | the `N = 20,000` label |
| fails | any | `TRAJECTORY_COUNT_SENSITIVE` | none: not interpreted |

- The labels compared are materially suppressed, equivalent or neither
  (section 9).
- `LOW_COUNT_LABEL_DIFFERENCE` means that the wider `N = 2,000` band
  crosses a classification boundary the governing band does not. It records
  reduced low-count precision, not instability.
- If either estimand of a pair and readout is `TRAJECTORY_COUNT_SENSITIVE`, that
  pair's kinetic class is reported as `trajectory_count_sensitive` and is not
  interpreted.

**Three separate quantities, not to be conflated:**

1. `δ = 0.005`: the practical, material-effect margin (section 9);
2. the `N = 20,000` empirical paired-block reproducibility band: the
   block-to-block reproducibility of the governing
   result (section 7);
3. the `N = 2,000` against `N = 20,000` comparison: trajectory-count
   sensitivity (this section).

## 11. Descriptive outputs (never classified)

- **P(ON) curves:** the per-tick mean and across-block SD of `P(X = ON)` for
  both readouts, every matched-pair arm at both challenge horizons, plus the
  pre-challenge phases. The washout arms are read at their declared horizons
  only. No crossing time, half-maximum or threshold is read from them.
- **Declared-but-unmatched contrasts:** anti-SPP1 and mifepristone against the
  declared twin (section 3), with the same estimands and bands, labelled
  `schedule_unmatched_descriptive`.
- **Washout:** the declared `anti_spp1_washout` perturbation (`washout` against
  `hormone_treated_anti_spp1`) and the `adhesion_challenge_washout` arm, with the
  curves of both readouts only. Both maternal phases have no embryo, so
  `OUT_STABLE_ADHESION` is structurally OFF there; only
  `OUT_MATERNAL_ADHESION_COMPETENCE` is informative. No contrast is classified.

## 12. What invalidates or stops the run

- **No simulation starts** until this committed file and the C2 follow-ups
  (`a4a88d4`, `696f965`) have passed independent review, or the owner has explicitly
  adjudicated that review (owner instruction, 2026-09-29).

- **Before any seed is spent**, the implementation re-checks the section 3
  construction against the resolved protocols and aborts if any check fails:
  phase count, durations, inputs, continuation rule, the condition-file diff,
  and that `config/protocols.yaml` and the v0.5.2 model files match the hashes
  recorded at run start. It also records those hashes and the implementation's
  hash in the run settings.
- A runtime error or a MaBoSS failure in any block invalidates the run. It is
  recorded with the error and the seeds already spent. A rerun needs fresh,
  disjoint seeds under a dated addendum; spent seeds are never reused.
- The run is not stopped, extended or resized on the basis of any result.

## 13. MaBoSS tasks, runtime and resources (estimated, not measured)

One MaBoSS task is one phase simulated once in one block. Shared lineage
prefixes run once per block.

| phase run | declared horizon | converged horizon |
|---|---:|---:|
| basal, E2, HT (shared prefix) | 3 | |
| HT extension (counterfactual; shared by two pairs) | 1 | |
| maternal perturbation phases: anti-SPP1, mifepristone, HAND2-loss HT | 3 | |
| challenges: twin after HT, control after extension, anti-SPP1, mifepristone, HAND2 loss | 5 | 5 |
| washout phase and `adhesion_challenge_washout` (descriptive) | 2 | |
| **per block** | **14** | **5** |

- **At `N = 20,000`:** 19 tasks per block × 20 blocks = **380 tasks**.
- **At `N = 2,000`:** the washout phases are not needed for any classified
  band, so 17 tasks per block × 20 = **340 tasks**.
- **Total: 720 MaBoSS tasks** in 40 worker jobs (one per block and count).

The runtime estimate is extrapolated from the v0.5.2 sizing pilot (about 0.3 s
per phase run per 2,000 trajectories at declared durations):

- A declared-horizon task at `N = 20,000` takes about 3 s, so about 42 s per
  block.
- A converged task, at horizon 25, is estimated at 10–25× a unit phase, so
  30–75 s each and 150–375 s per block.
- That makes about 3–7 min per governing block, and 1–2.5 h serial for 20. The
  `N = 2,000` blocks add about 10%.
- **With 3 workers: about 25–55 min wall-clock**, possibly off by 2× either way.
- Workers run as a capped `systemd-run` service, never inside tmux, because
  parallel MaBoSS workers have reached 11–14 GB here. The worker count and the
  memory cap are execution settings, recorded, and result-neutral.

## 14. What no outcome licenses

- No biological, clinical, kinetic or physical-time claim; no statement that
  anti-SPP1, mifepristone or HAND2 loss delays or blocks implantation.
- No rate value, rate prior or partial-perturbation strength (C3b, C4).
- No change to any activation status, weight, objective, observation-map row or
  perturbation definition.
- The HT extension is a model counterfactual, not an ADOC condition. It must
  never be reported as a measured or measurable arm.
