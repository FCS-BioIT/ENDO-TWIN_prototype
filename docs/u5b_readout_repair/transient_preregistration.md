# U5b — transient comparison, pre-registered

**Frozen before any `adoc-literature-superset-v0.5.1` simulation was run.** This
file is committed on its own, ahead of the directory it describes, so the order
is checkable from history rather than asserted here. Nothing below may be
changed after the comparison is run. A deviation is recorded as a deviation in
the U5b record (`docs/v05_u5b_readout_repair.md`), not as an edit to this file.

The only simulation run before this freeze was a **sizing pilot on v0.5.0
alone**: 5 disjoint blocks of 2,000 trajectories on the
`adhesion_challenge_hormone_treated` lineage, used to size the design (it takes
about 0.6 s per lineage replicate and 0.36 GB; the across-block SD of the
readout's phase-averaged occupancy was about 0.0015 in `hormone_treated_maternal`
and 0.0020 in the challenge phase). v0.5.1 did not exist when it ran, so no
paired difference was seen before the tolerance below was fixed.

## 1. The change being compared

`OUT_STROMAL_DECIDUALIZED = S_DECIDUALIZED and S_PRL and S_IGFBP1` (v0.5.0) →
`OUT_STROMAL_DECIDUALIZED = S_DECIDUALIZED` (v0.5.1). Nothing else in the
executable model differs.

**What is already known without simulating, and is not what this measures.** The
composed Boolean function of every node is unchanged, and the node is read by no
rule; both are checked by exhaustive enumeration, not by this comparison. The
question here is the *transient*: under asynchronous updating `S_PRL` and
`S_IGFBP1` lag `S_DECIDUALIZED`, so v0.5.0's readout has to wait for them and
v0.5.1's does not. **A change is expected, not a null**, and this design is
built to measure its size rather than to confirm an assumption either way.

## 2. Design

- **Arms.** Four lineages, each run through `protocol_lineage` with the
  projected continuation between phases, exactly as the concordance and endpoint
  builds run them: `adhesion_challenge_basal`,
  `adhesion_challenge_hormone_treated`,
  `adhesion_challenge_hormone_treated_mifepristone`, `adhesion_challenge_washout`.
- **Cells.** Every phase of every lineage, **deduplicated by lineage prefix**,
  because a shared prefix under the same seed is the same computation. That is
  ten cells: `basal_maternal`, `adhesion_challenge_basal`, `e2_primed_maternal`,
  `hormone_treated_maternal`, `adhesion_challenge_hormone_treated`,
  `hormone_treated_mifepristone`,
  `adhesion_challenge_hormone_treated_mifepristone`,
  `hormone_treated_anti_spp1`, `washout`, `adhesion_challenge_washout`.
- **Horizon.** The **declared** `relative_duration` of each phase only.
  Dimensionless MaBoSS time, never days. The converged horizon is not run: the
  fixed point cannot move, and that is shown by enumeration.
- **Pairing — common random numbers.** For replicate index `r`, v0.5.0 and v0.5.1
  are run on the **same seed**, and a run with seed `s` and `N` trajectories is
  the union of single-trajectory runs on seeds `s … s+N−1`
  (`docs/maboss_estimator_semantics.md`, addendum 2026-09-23). So trajectory `k`
  of both arms starts from the same per-trajectory stream.
- **Disjoint blocks between replicate indices.** `R = 20` replicates at each of two
  trajectory counts. At `N = 20,000`: `seed_r = 1 + r·20,000`. At `N = 2,000`:
  `seed_r = 400,001 + r·2,000`, i.e. **after** the whole 20,000 range, so the two
  trajectory counts share no per-trajectory seed either.

**Pairing is variance reduction and nothing more.** Once a trajectory reaches a
state where the two rules disagree, the total transition rate differs, and from
there on the two arms consume the same stream differently. Every node's paired
per-trajectory difference is then random, and the finite-sample paired mean is
an estimate with Monte Carlo error, not the rule's effect read off exactly.

## 3. Estimands

For node `X`, cell `c`, replicate `r`: `A_r(t)` and `B_r(t)` are v0.5.1's and
v0.5.0's per-tick `P(X = ON)` from the phase's `nodes_probtraj`.

- **Primary, time-averaged:** `D_r = mean_t [A_r(t) − B_r(t)]` over the phase's
  ticks — the phase-averaged occupancy difference.
- **Primary, final tick:** `F_r = A_r(t_last) − B_r(t_last)`, the value an arm
  report reads at the declared horizon.
- **Descriptive only:** the per-tick mean difference trace, reported with
  pointwise intervals and not used for any verdict.

The primary family is these two estimands for `X = OUT_STROMAL_DECIDUALIZED` in
all ten cells: **20 intervals**. The blast-radius family is the same two
estimands for **every other node** the phase reports, in all ten cells.

## 4. Uncertainty measure

Across the `R` disjoint blocks: mean `D̄`, sample SD `s`, `SE = s/√R`, and a
two-sided **t-interval** with `R − 1` degrees of freedom at family-wise level
0.05, **Bonferroni-adjusted** within each family (primary: 0.05/20; blast radius:
0.05 divided by that family's interval count).

What this interval is: the **run-to-run reproducibility of the paired estimator
on disjoint seed blocks**. What it is not: an i.i.d. Monte Carlo standard error.
The per-trajectory initial-state draw over consecutive seeds is stratified (same
addendum, item 2), which makes the across-block spread smaller than an i.i.d.
error would be, and "disjoint" is not a proof that the streams are independent.
Nothing biological or experimental is in it.

## 5. Tolerance and verdicts — declared now

**Tolerance `δ = 0.005`** on both primary estimands, in occupancy units (0–1).
Chosen as a practical-equivalence margin: half a percentage point of trajectory
frequency is below any difference this repository reports as meaningful for a
phenotype occupancy, and the pilot SD puts it about ten interval half-widths
above the resolution of this design at `N = 20,000`, `R = 20`. It is not tuned to
any result, since no paired difference existed when it was chosen.

Per interval:

| verdict | condition |
|---|---|
| `EXACTLY_IDENTICAL` | every one of the `R` per-block differences is exactly `0.0` |
| `WITHIN_TOLERANCE` | the interval lies inside `[−δ, δ]` |
| `BEYOND_TOLERANCE` | the interval does not meet `[−δ, δ]` |
| `INDETERMINATE` | anything else |

**`WITHIN_TOLERANCE` means "no detected transient change at this precision",
never "no change".** `BEYOND_TOLERANCE` means a detected change larger than the
tolerance, reported with its interval and absolute size.

**Pre-declared expectations, each of which can fail:**

1. `EXACTLY_IDENTICAL` for **every node** in `basal_maternal`,
   `e2_primed_maternal` and `adhesion_challenge_basal`. `IN_PROGESTIN` is off in
   all three, `S_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE` and
   `S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2`, so the rules never disagree
   there and common random numbers must give identical trajectories. **If this
   fails, the pairing does not work as claimed and the run is invalid**, not
   merely noisy.
2. Blast radius: `WITHIN_TOLERANCE` or `EXACTLY_IDENTICAL` for every node other
   than `OUT_STROMAL_DECIDUALIZED` in every cell. The node is read by no rule, so
   the process restricted to every other node has the same generator in both
   versions and the same law; only its realisation under common random numbers
   can differ. A `BEYOND_TOLERANCE` here would contradict that argument and is
   reported as a defect, not interpreted.
3. For `OUT_STROMAL_DECIDUALIZED` in the hormone-exposed cells: no direction or
   size is pre-declared beyond the sign argument in §1 (v0.5.1 can only turn on
   earlier). Whatever the verdict, it is reported with its interval.

## 6. Trajectory-count stability check

For each primary interval, the `N = 2,000` and `N = 20,000` estimates must satisfy
`|D̄₂ₖ − D̄₂₀ₖ| ≤ q·√(SE₂ₖ² + SE₂₀ₖ²)`, with `q` the same Bonferroni-adjusted
normal quantile, **and** must reach the same verdict. The ratio `SE₂ₖ / SE₂₀ₖ`
is reported (about 3.2 if SE went as 1/√N); no scaling law is claimed, because
the draws are stratified and two trajectory counts cannot establish one.

**The verdict is read at `N = 20,000`.** A cell that fails the stability check is
reported `UNSTABLE` and is not interpreted.

## 7. What no outcome of this licenses

No biological, clinical or kinetic claim. MaBoSS time is uncalibrated, so an
earlier onset in relative time is not an earlier onset in days, and a
phase-averaged occupancy is not a probability that any tissue is decidualised.
The result bears only on what a reader of v0.5.1's `OUT_STROMAL_DECIDUALIZED` at
a declared horizon would see relative to v0.5.0's.
