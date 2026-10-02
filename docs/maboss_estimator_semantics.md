# What a MaBoSS probability in this repository actually estimates

Status: bounded read-only spike, 2026-09-13. No model, protocol, rule or
calibration file was changed. Claim level: `structural` — this is a statement
about the simulator's estimator, not about biology or calibration.

## Why this exists

Three separate attempts in this repository tried to explain the reported
probabilities by reasoning **from the values**: that `0.00005` meant "one
trajectory in 20,000"; that a binomial standard error applied; that a `1/N`
resolution limit applied; that a weighted-mixture or support-cardinality story
explained the continuation. All four were withdrawn, and
`deep_research_adhesion_model_2026-09-11.next-stage.md` recorded the lesson:

> the provenance of the non-`1/20000` probabilities must be traced in the
> MaBoSS/cmaboss **output semantics**, read directly, not inferred from output
> values. Every attempt to infer it from values has been wrong.

This document does that. Every claim below is read from source, and the source
is pinned.

## What was read

| Artifact | Identity |
|---|---|
| `maboss` (Python) | 0.8.15 |
| `cmaboss` (compiled) | 1.0.0b32 |
| Upstream source | `sysbio-curie/MaBoSS` @ `fc3a8c9b2e35d3aa4adac44aa0f60c6557da4421` (2026-04-15) |
| `engine/src/Cumulator.h` | sha256 `69b53db16850b6b89bad0206fe538b01d6fa5c621856ccf36219d3f6340789e5` |
| `engine/python/src/maboss_res.cpp` | sha256 `f689bcd4d4cf21bd9d3a928c0fd4400241a022c33db3ded11157c1753b894933` |

**Bounding caveat, stated first because it limits everything here.** The wheel
this repository executes is a compiled binary with no bundled source. The source
read is upstream `HEAD`, not a tag identified as the provenance of
`cmaboss 1.0.0b32`. The formulas below are therefore the upstream
implementation, corroborated against this repository's own runtime behaviour
(see "Corroboration"), and not a decompilation of the installed artifact. Treat
them as strongly evidenced, not as proven properties of the installed binary.

## 1. What the reported number estimates

**It is a time-averaged occupancy over a tick window, not a fraction of
trajectories at an instant.**

`Cumulator::CumulMap::incr` accumulates, per network state, the quantity
`tm_slice` — the amount of *simulated time* a trajectory spent in that state
inside the current tick window:

```cpp
void incr(const S& state, double tm_slice, double TH) {
  ...
  (*iter).second.tm_slice += tm_slice;
  (*iter).second.TH += tm_slice * TH;
}
```

and every reported probability divides that accumulated time by
`time_tick * sample_count`:

```cpp
double ratio = time_tick*sample_count;
...
double proba = tick_value.tm_slice / ratio;
```

So for tick window `w`, state `s`, `N` trajectories and tick width `Δ`:

```
P̂(s, w) = ( Σ over trajectories of time spent in s during w ) / (Δ · N)
```

which is the mean over trajectories of the **fraction of window `w` spent in
state `s`**. The per-trajectory contribution is a continuous number in `[0, 1]`,
not a Bernoulli indicator.

Three consequences follow immediately, and they settle the withdrawn readings:

- **`0.00005` is not "one trajectory in 20,000".** It is
  `tm_slice / (Δ·N)`. That it coincides with `1/20000` is arithmetic
  coincidence, not provenance. Nothing in the estimator counts paths.
- **The values need not be multiples of `1/N`,** which is why
  `OUT_STROMAL_DECIDUALIZED = 0.04054164922510266` was never anomalous. The
  earlier observation was correct as a negative fact and is now explained.
- **A binomial standard error is not merely unjustified, it is the wrong
  family.** Binomial variance describes a sum of indicators. The quantity here
  is a mean of continuous occupancies, whose variance depends on how long
  trajectories dwell, not only on how many are in the state.

**A refinement that matters, found while testing this.** The time-average and
the path fraction coincide exactly whenever a node does not transition *inside*
the tick window: every trajectory then contributes a full window of dwell time,
and `tm_slice/(Δ·N)` reduces to `count/N`. Saturated free variables behave that
way — a 50/50 `istate` reports `0.4999` at `N = 10000` — so pointing at such a
value and observing that it *is* a multiple of `1/N` refutes nothing. The
distinction only becomes visible in nodes read while still in transit, which is
where the committed declared-horizon readouts sit. A first version of the
accompanying test got this backwards and is corrected in
`tests/unit/test_maboss_estimator_semantics.py`.

### What the repository actually reads

`src/dt_adoc/maboss_adapter.py` reads `get_nodes_probtraj().iloc[-1]` — the
**last tick window**. With `time_tick = 0.1`, a reported endpoint is therefore
the mean occupancy over the final interval `[max_time − 0.1, max_time]`, not the
value "at" `max_time`. At a converged horizon this distinction is immaterial
because the process has settled; at the declared horizon, where
`docs/endpoint_convergence_finding.md` records the readout as ~4000× short of
its fixed point, it is not.

## 2. What randomness is involved

Two independent sources, and they are not interchangeable:

1. **Initial-state sampling.** `.cfg` `istate` lines are a probability
   distribution over starting states. In this model's `baseline.cfg` four
   interface relays carry Bernoulli priors (`0.70/0.30`, `0.30/0.70`,
   `0.60/0.40`, `0.80/0.20`). Each trajectory draws once.
2. **Trajectory stochasticity.** MaBoSS runs a continuous-time Markov process
   with asynchronous updating; transition timing and choice are random.

For **this** model the second source contributes nothing to the converged
endpoint, and that is a property of this network rather than of MaBoSS. The
network is a DAG over its 19 free variables with zero non-trivial strongly
connected components (`docs/topology_parity_correction.md`), so each phase has a
unique fixed point per free-variable assignment, independent of path and timing.
At convergence the reported value is therefore a deterministic function of the
**initial-state mixture** alone. This is visible in the committed run: the
priors `0.70` and `0.40` reappear as `X_ADHESION_ROUTE_SPP1 = 0.69995` and
`X_ADHESION_ROUTE_REDUNDANT = 0.40010`, and `OUT_STABLE_ADHESION = 0.8201`
is `1 − (1−0.70)(1−0.40)` to four decimals.

The practical reading: at the converged horizon MaBoSS is being used as an
exhaustive truth-table evaluator with a Bernoulli prior, and the residual
spread across seeds is Monte-Carlo error on that mixture, not dynamics.

## 3. Which uncertainty procedures are defensible

### 3a. The state-level error MaBoSS computes IS a standard error

For individual network states MaBoSS computes

```cpp
double variance_proba = (tm_slice_square / ((sample_count-1) * time_tick2))
                      - (proba*proba*sample_count/(sample_count-1));
double err_proba = sqrt(variance_proba/sample_count);
```

This is the textbook sample variance of the per-trajectory occupancy, divided by
`N` and square-rooted: a standard error of the mean over independent
trajectories. It is defensible **for a single state**.

### 3b. The node-level error MaBoSS reports is NOT a standard error — do not adopt it

This is the finding that matters most, because it is the column a maintainer
would most naturally reach for. A node marginal is assembled by summing over
every state in which the node is ON, and the error is assembled the same way:

```cpp
for (auto node: output_nodes) {
  if ((state).getNodeState(node)){
    node_probas[node] += proba;
    if (COMPUTE_ERRORS) {
      ...
      node_errors[node] += err_proba;      // <-- a SUM of standard errors
    }
  }
}
```

Summing the probabilities is correct — the states are mutually exclusive, so
the marginal really is the sum. **Summing their standard errors is not.** The
standard error of a sum depends on the component variances *and on every
pairwise covariance*; MaBoSS adds the component standard errors instead and
never forms the covariance terms. By the triangle (Minkowski) inequality
`Σ SE_i` is an **upper bound** on the SE of the sum, attained only under perfect
positive correlation, and it can be extremely loose. It is therefore not the
marginal's standard error and carries no stated bound on how far off it is.

**A correction, because an earlier revision of this section overreached.** It
argued that mutually exclusive states are *negatively* correlated and that the
bound is therefore always loose. Per-trajectory dwell fractions do sum to 1
across all states, which forces the *total* covariance to be negative — but that
says nothing about any particular pair. Two states in the node's ON set can
covary *positively* if both gain whenever a third state loses. The pairwise
claim was wrong and is withdrawn. Nothing here depends on it: the upper-bound
argument and the measurement below are sufficient on their own.

It is also demonstrably not a standard error of the node marginal, which can be
checked in one run: for `hormone_treated_maternal`,
`OUT_STROMAL_DECIDUALIZED` has a last-tick value of `1.0000000000000002` and a
reported error of `0.0793`. A marginal that is deterministically 1.0 has zero
sampling error; the 0.0793 is the accumulated spread of the many underlying
states, which cancels in the marginal and does not cancel in the sum.

**Consequence for this repository:** the repo reads node marginals, so
MaBoSS's own error column is unusable for it as published. It should not be
surfaced as an uncertainty, and if it is ever surfaced it must be labelled an
upper bound on a quantity nobody needs.

### 3c. What IS defensible here

In order of preference:

1. **Independent complete-run replicate variability across seeds.** Re-running
   the whole lineage under a different RNG seed and taking the spread of the
   endpoint. It requires no assumption about the estimator's internals,
   propagates through the multi-phase continuation (which the per-run error
   cannot, since continuations resample), and is what the concordance build
   already records as `simulated_sd_across_seeds`. The prior sessions preferred
   this on instinct; this document supplies the reason.
2. **State-level `err_proba`**, where a single network state genuinely is the
   quantity of interest. It is not, for any current readout.
3. **Exhaustive enumeration**, where the question is asymptotic rather than
   statistical. Because the network is a DAG over 19 free variables, all
   524,288 assignments can be enumerated exactly, and the repository already
   does this. For fixed-point questions this replaces uncertainty entirely
   rather than quantifying it — it is a proof, not an estimate.

### 3d. Explicitly not defensible

- Binomial / Wilson / Agresti–Coull intervals **on a MaBoSS time-averaged
  occupancy, in general**. Wrong variance family (§1): the per-trajectory
  quantity is a continuous dwell fraction, not an indicator.

  Scoped deliberately, because a blanket ban would be wrong twice over. It would
  forbid the **degenerate simulator case** §1 itself identifies — a node that
  never transitions inside the tick window contributes a 0/1 indicator per
  trajectory, and binomial reasoning does apply there, which is why such values
  come out as exact multiples of `1/N`. And it would forbid these intervals on
  **experimental count data**, where they are simply correct: `R41b` already
  reports a Wilson 95% CI of [0.27, 0.68] on 9/19 attached blastocysts, and
  nothing in this document bears on that. The prohibition is about the
  simulator's estimator, never about counting embryos.
- Any `1/N` resolution or detection-limit claim. Nothing counts paths.
- MaBoSS's node-level error column as a standard error (§3b).
- Treating `simulated_sd_across_seeds` at a small seed count as a stability
  characterisation. Five seeds bound gross instability; they do not estimate a
  variance well, and `AGENTS.md` already says fixed seeds give reproducibility,
  not Monte-Carlo stability.

## Corroboration

The formulas above were checked against this repository's own runtime, not only
read:

- A node marginal was reproduced as a non-multiple of `1/N`, consistent with a
  time-average and inconsistent with a path count.
- The node error was reproduced as non-zero on a marginal of exactly `1.0`,
  which is the signature of §3b and cannot arise from a correct standard error.
- The converged relay pass-through (`0.69995`, `0.40010`) and the
  `1 − (1−p₁)(1−p₂) = 0.82` identity were reproduced from the committed run
  settings, consistent with §2.

## What this does not settle

- It does not characterise the continuation estimator. `project_joint_distribution`
  renormalises the retained distribution between phases; how sampling error
  propagates across a five-phase chain is **not** answered here and remains open.
  A prior probe that tried to read this off support cardinality and mass was
  withdrawn for good reason and is not revived.
- It does not license a physical-time interpretation. `time_tick` and `max_time`
  remain dimensionless MaBoSS time throughout, never hours or days.
- It says nothing about whether any reported probability is a good estimate of an
  experimental adhesion frequency. That is a calibration question, and the
  answer elsewhere in this repository is still no.

## Addendum 2026-09-23 — how the seed enters, measured on the installed binary

Found while building the functional-endpoint figure on
`feat/v05-u5-structural-audit`. Unlike §1–§3, this is **measured on the
executed `cmaboss 1.0.0b32` wheel**, not read from upstream source, so it does
not inherit the bounding caveat above. It refines §3c(1); it does not withdraw it.

Every number below is produced by
`dt_adoc.reporting.endpoint_replicates.seed_structure_probe`, re-run by every
`pixi run build-endpoint-replicates` and recorded under `seed_structure_probe`
in [`endpoint/endpoint_run_settings.json`](endpoint/endpoint_run_settings.json);
`tests/integration/test_maboss_seed_structure.py` re-runs the union test.

**1. A run with seed `s` and `N` trajectories is the union of `N`
single-trajectory runs with seeds `s, …, s+N−1`.** Tested on
`hormone_treated_maternal` from `baseline.cfg` at its **declared** horizon, where
nodes are caught in transit (`transient_node_tick_cells`: most node×tick cells
lie strictly between 0 and 1), so the test is on dynamic trajectories, not on
free variables that never move. For `s = 1` and for `s = 2`, with `N = 40`, the
pooled run and the mean of the single runs agree to floating-point rounding on
**the whole time-resolved per-node occupancy table** (every recorded node at
every tick) **and on the whole joint state distribution at the last tick**
(`union_tests`). Two pooled runs on non-overlapping seed ranges differ by 0.42 on
the same table (`disjoint_control`), so the test can fail.

Equal aggregates do not by themselves identify a trajectory collection, so a
second, attributing test is recorded in
[`endpoint/seed_structure_probe.json`](endpoint/seed_structure_probe.json)
(`dt_adoc.reporting.seed_structure`). If trajectory `k` is seeded `s + k`, the
pooled runs with seeds `s` and `s + d` share all but `d` trajectories at each
end, so `N · (pooled(s+d) − pooled(s))` must equal the sum of the `d` named
single-seed trajectories that enter minus the `d` that leave, **exactly, at every
tick, for every recorded node**. For `d` = 1, 3 and 7 on the same dynamic
protocol the residual is at rounding (~1e-14) against differences of order 1–4
(`shift_tests`); the same identity with the entering trajectories shifted by one
seed leaves a residual of 1.0 (`wrong_attribution_max_abs_residual`).

**Inference, stated as such.** Trajectory `k` of a run with seed `s` behaves as
the single-trajectory run with seed `s + k`. That is inferred from these
measurements on the installed binary; the generator's source was not read.

*Consequence, under that inference.* Runs whose seeds differ by less than the
trajectory count share trajectories. The concordance build's seeds 1–5 at 20,000
trajectories would share 19,996 of their 20,000 trajectories, so `simulated_sd_across_seeds` in
`docs/concordance/run_settings.json` reflects the swap of at most four
trajectories. It is **not** the complete-run variability §3c(1) recommends, and
§3d's last bullet already forbade reading it as a stability characterisation.
Replicates that share no per-trajectory seed need **disjoint seed blocks**:
`seed_r = 1 + r · N`. The endpoint build keeps blocks disjoint between replicate
indices and reuses the same block across arms and horizons for one index — common
random numbers, so arms are compared on paired streams.

**2. The initial-state draw over consecutive per-trajectory seeds is
stratified, not i.i.d.** Over seeds 1..40 the Bernoulli(0.70)
`X_INTERFACE_SPP1_RELAY` single-trajectory draws read
`1011011101101110110110111011011001101101`
(`relay_single_trajectory_draws_seeds_1_to_block`) — near-periodic. Across ten
disjoint blocks (`relay_disjoint_blocks`) the relay occupancy has SD ≈ 0.0099 at
100 trajectories against an i.i.d. binomial reference of 0.046, and ≈ 7.8e-5 at
20,000 against 3.2e-3.

*Consequence.* The disjoint-block spread of an endpoint driven by the
initial-state mixture is smaller than an i.i.d. Monte Carlo error would be. It is
still the honest run-to-run reproducibility of *this* estimator, and it is what
the endpoint figure reports — but it must not be labelled an i.i.d. Monte Carlo
SE, and binomial reasoning about the mixture does not apply to it. Two block
sizes do not establish a scaling law, and none is claimed.

**What this does not settle.** Whether the transition-time draws later in each
trajectory's stream are equally stratified was not tested separately; at the
declared horizon the disjoint-block spread is reported without an i.i.d.
interpretation for that reason. "Disjoint" means the replicates share no
per-trajectory seed; it is not a proof of statistical independence of the
streams.
