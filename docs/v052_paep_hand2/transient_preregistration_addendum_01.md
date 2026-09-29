# v0.5.2 transient comparison — addendum 01 (prospective correction), 2026-09-28

**Frozen before run 2.** This addendum is committed on its own, after run 1 and
before any run-2 simulation. It extends `transient_preregistration.md`, which it
does not edit (sha256 `03cb1029530a8b0d08fbe53cb41b334db34444c619d6043888f1179cbbe9d901`).
Where the two differ, this addendum governs **run 2 only**.

**This addendum is not blind to run 1.** Run 1's results were seen before it
was written, and they are preserved, invalid, in `run1_invalid/`. Two things
limit what that knowledge can buy:

- the addendum changes only how rounding is handled, the seeds, and one
  sentence of wording;
- run 2 uses fresh seed blocks, so its realisation is new data.

Every other constant is unchanged, and no tolerance, family, verdict rule or
expectation 2–3 condition is altered.

## The model under test

This is exactly the candidate of run 1:

- `adoc-literature-superset-v0.5.2`, `network.bnd` sha256
  `7a73529c28ab7533c25c0673744bad7496ee8d75d7849fe3971838dbcf2d7b25`;
- against `adoc-literature-superset-v0.5.1`, `network.bnd` sha256
  `d7068867429cfdafe89442ee2fb0bc3fb94ae9f985d3d65b1c4be19d01cad063`.

It has two rule changes, C1 and C5. v0.5.2's README and provenance text may be
re-emitted before run 2 to document C5's semantics. Its rules may not change.
If `network.bnd` differs from the hash above, run 2 is not the run registered
here.

## A1. The exact-identity check (expectation 1) — corrected

**The intended invariant is unchanged.** Where the compared rules cannot
differ, the paired stochastic realisation must be identical.

**Why the original check failed.** Run 1 tested that invariant on node
marginals, which MaBoSS computes as sums over states. When a rule's input set
changes, so does the order of that summation, and the marginals then carry
rounding of up to 7.7 × 10⁻¹⁶ even when every trajectory is identical.

**Corrected rule.** Expectation 1 holds for a comparison if and only if, for
every replicate at both trajectory counts and every phase of
`basal_maternal`, `e2_primed_maternal` and `adhesion_challenge_basal`, both of
these hold:

1. **State-level identity, exact.** The phase's final-tick per-state
   probability distribution (`last_states_probtraj`) is the same in both
   versions:
   - the same set of states;
   - every probability bitwise equal (`==` on the stored float64).

   Each per-state value is accumulated state by state, with no cross-state
   summation. So identical trajectories give identical bits, and exact
   equality is meaningful here.
2. **Node-level identity, to rounding.** Every per-tick node-marginal paired
   difference satisfies `|d| ≤ 1e-12`. That bound is more than 1,000 times
   run 1's observed rounding, and five million times below the tolerance δ.

If either fails in any replicate, run 2 is **invalid**, reported as such, and
not rescued by a further correction.

## A2. Rounding-level differences are snapped to zero before the estimands

For every node, cell and comparison:

- **Snapping.** A per-tick paired difference with `|d| ≤ 1e-12` is set to
  exactly `0.0` before the phase-averaged and final-tick estimands are
  computed. Nothing larger is touched.
- **What it changes.** Run 1 split the `EXACTLY_IDENTICAL` and
  `WITHIN_TOLERANCE` verdicts on rounding alone, and that split made one
  stability check disagree (`UNSTABLE`). This fixes both.
- **What it cannot change.** It cannot move any interval by more than 1e-12.
  So it cannot change a `WITHIN_TOLERANCE`, `BEYOND_TOLERANCE` or
  `INDETERMINATE` verdict, and it cannot alter expectations 2 or 3.

## A3. Fresh, disjoint seed blocks

Run 2 uses `R = 20` replicates at each count, as before, on new seed blocks:

- **governing count, N = 20,000:** `seed_r = 1,000,001 + r·20,000`, covering
  seeds 1,000,001 to 1,400,000;
- **check count, N = 2,000:** `seed_r = 1,400,001 + r·2,000`, covering seeds
  1,400,001 to 1,440,000.

These blocks are disjoint from:

- run 1 (seeds 1 to 440,000);
- the sizing pilot (10,000,000 upward);
- the 2026-09-28 state-level diagnostic (seeds 1 to 20,000);
- each other.

Pairing is unchanged: both arms of a pair share a seed.

## A4. How the interval is described (wording only)

The original §4 calls the interval one "at family-wise level 0.05". That phrase
is withdrawn, as the owner withdrew it for U5b on 2026-09-23
(`docs/v05_u5b_readout_repair.md` §4). The reason: the replicate blocks are
stratified draws, not independent ones. The interval is an **empirical paired
block-reproducibility band**:

- the across-block mean, ± the pre-declared Bonferroni-adjusted t-quantile ×
  the across-block SD/√R;
- a stability screen, with no coverage claim.

The computation, multiplier, tolerance and verdict table are unchanged.

## A5. How the affected-set differences are read (owner, 2026-09-28)

C5 is a semantic change to the model, recorded as such:

- **Before:** HAND2 vetoes epithelial proliferation directly, **and** it
  suppresses the stromal mitogenic relay.
- **After:** HAND2 acts **only** through the stromal relay,
  `S_FGF_MITOGENIC = not S_HAND2`.

Transient differences in the seven affected nodes are therefore expected
consequences of that change. No neutrality is required of them, and none was
required by the original §5, which declared no direction for the combined
comparison. Expectations 2 (unaffected family) and 3 (attribution directions)
are unchanged.

## Unchanged, restated so nothing is inferred

The following are all exactly as in `transient_preregistration.md`:

- arms, lineages, the ten cells and the declared horizons;
- `R = 20` and trajectory counts 20,000 and 2,000;
- tolerance `δ = 0.005`;
- the three families per comparison and the Bonferroni divisor per family;
- the verdict table;
- expectations 2 and 3;
- the stability check;
- the two attribution arms (C1-only, C5-only);
- the claim boundary of §7.
