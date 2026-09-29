# v0.5.2 — transient comparison, pre-registered

**Frozen before any `adoc-literature-superset-v0.5.2` simulation was run.** This
file is committed on its own, ahead of the directory it describes, so the order
is checkable from history rather than asserted here. Nothing below may be
changed after the comparison is run. A deviation is recorded as a deviation in
the unit record (`docs/v052_paep_hand2_cleanup.md`), not as an edit to this file.
The design is U5b's (`docs/u5b_readout_repair/transient_preregistration.md`)
unless a section says otherwise.

The only simulation run before this freeze was a **sizing pilot on v0.5.1
alone**: 5 blocks of 2,000 trajectories over all ten cells, on seeds from
10,000,000 upward (outside every range below). It took about 3 s per block and
peaked at 1.9 GB. In the cells where the rules can disagree, across-block SDs
of the phase-averaged occupancy were 0.0016–0.0083 for
`E_ESTROGENIC_PROLIFERATION` and 0.0007–0.0051 for `OUT_EPITHELIAL_RECEPTIVE`.
It also showed that at the declared horizons `E_PAEP` is well below
`E_RECEPTIVE_SURFACE` in the hormone-exposed cells
(`adhesion_challenge_washout`: 0.29 against 0.57; `washout`: 0.36 against 0.57). A single-version
occupancy is not a paired difference, but the implication is recorded here
before the comparison: **the C1 transient is expected to be large, not
cosmetic.** A 2026-09-28 scratch attempt to run the variants in another harness
hung before producing any output, so no v0.5.2 or variant result has been seen.

## 1. The changes being compared

Two rules, both from the 2026-09-28 reconciliation of the 163-paper literature
re-audit (items C1 and C5):

- **C1:** `OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE and E_PAEP` (v0.5.1) →
  `OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE` (v0.5.2). PAEP/glycodelin is a
  secretory-differentiation readout. No primary source perturbs it with an
  adhesion endpoint, so it must not gate the reported receptivity phenotype.
- **C5:** `E_ESTROGENIC_PROLIFERATION = IN_E2 and S_FGF_MITOGENIC and not
  S_HAND2` (v0.5.1) → `E_ESTROGENIC_PROLIFERATION = IN_E2 and S_FGF_MITOGENIC`
  (v0.5.2). The HAND2 effect on epithelial proliferation is a net effect through
  the stromal relay (`S_FGF_MITOGENIC = not S_HAND2`), not a demonstrated direct
  epithelial edge.

Nothing else in the executable model differs.

**What is known without simulating, and is not what this measures.** Both
removed conjuncts are absorbed: `E_PAEP = E_SECRETORY_STATE` is implied by
`E_RECEPTIVE_SURFACE`, and `not S_HAND2` is implied by `S_FGF_MITOGENIC` once the
relay has updated. So each node's composed Boolean function over the free
variables is unchanged; the unit checks that by exhaustive enumeration, node by
node. **Unlike U5b, neither changed node is a leaf.** The rules that read them:

| changed node | readers | transitive descendants |
|---|---|---|
| `OUT_EPITHELIAL_RECEPTIVE` | `OUT_MATERNAL_ADHESION_COMPETENCE` | + `OUT_STABLE_ADHESION` |
| `E_ESTROGENIC_PROLIFERATION` | `E_RECEPTIVE_SURFACE` | + `OUT_EPITHELIAL_RECEPTIVE`, `X_ADHESION_ROUTE_SPP1`, `X_ADHESION_ROUTE_REDUNDANT`, `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION` |

The **affected set** is these seven nodes: the two changed nodes and their five
descendants. The other 52 nodes read none of them, directly or transitively, so
the process restricted to them has the same generator in both versions and
therefore the same law.

Under asynchronous updating the two rules disagree only transiently:

- **C1:** while `E_RECEPTIVE_SURFACE` is on and `E_PAEP` has not yet updated on
  (onset), or has updated off first (offset).
- **C5:** while `S_HAND2` is on and `S_FGF_MITOGENIC` has not yet updated off.

**The two changes push in opposite directions.** C1 can only turn the epithelial
readout on in more states. C5 can only turn proliferation on in more states,
and `not E_ESTROGENIC_PROLIFERATION` is a conjunct of `E_RECEPTIVE_SURFACE`,
which pushes the readout the other way. So the combined comparison is
attributed with the two single-change arms of section 2.

## 2. Design

- **Arms, cells, horizon, lineages:** exactly U5b's four lineages
  (`adhesion_challenge_basal`, `adhesion_challenge_hormone_treated`,
  `adhesion_challenge_hormone_treated_mifepristone`,
  `adhesion_challenge_washout`). They run through `protocol_lineage` with the
  projected continuation between phases, and are deduplicated by lineage prefix
  into the same ten cells. Each phase runs at its **declared**
  `relative_duration`. Time is dimensionless MaBoSS time, never days. The
  converged horizon is not run, because enumeration already settles the fixed
  point.
- **Primary comparison:** v0.5.2 against v0.5.1, on common random numbers.
  Replicate `r` of both versions uses the same seed.
- **Seeds and replicates:** exactly U5b's scheme. `R = 20` at each of two
  trajectory counts. At `N = 20,000`: `seed_r = 1 + r·20,000`. At `N = 2,000`:
  `seed_r = 400,001 + r·2,000`.
- **Attribution (secondary):** two single-change variants, each against v0.5.1
  on the same seeds, at `N = 20,000` with `R = 20`: **C1-only** and
  **C5-only**. They are emitted by the same emitter, with the same provenance
  checks, into a scratch repository root and never committed as model
  versions. Their intervals are reported with verdicts but carry no
  expectations beyond the direction statements in section 5. If a variant
  cannot be built so that the runtime validates it, the attribution is recorded
  as **not run**, with the error, and nothing is substituted for it.

**Pairing is variance reduction and nothing more**, exactly as in U5b. Once a
trajectory reaches a state where the rules disagree, the two versions consume
the stream differently, and the paired mean is an estimate with Monte Carlo
error.

## 3. Estimands and families

The estimands are U5b's, per node `X`, cell `c` and replicate `r`:

- the phase-averaged difference `D_r = mean_t [A_r(t) − B_r(t)]`;
- the final-tick difference `F_r`.

Here `A` is the new version's per-tick `P(X = ON)` and `B` is v0.5.1's. The
per-tick trace is descriptive only.

- **Primary family:** the two estimands for `OUT_EPITHELIAL_RECEPTIVE` and
  `E_ESTROGENIC_PROLIFERATION` in all ten cells — **40 intervals**.
- **Downstream family:** the two estimands for the other five affected nodes in
  all ten cells — 100 intervals.
- **Unaffected family:** the two estimands for every other node the phase
  reports, in all ten cells.
- **Attribution families:** each single-change variant has its own primary,
  downstream and unaffected families, defined the same way.

## 4. Uncertainty measure

This is U5b's measure unchanged: a two-sided t-interval across the `R`
disjoint blocks, with `R − 1` degrees of freedom. It is Bonferroni-adjusted at
family-wise level 0.05 **within each family** (0.05 divided by that family's
interval count). It measures the run-to-run reproducibility of the paired
estimator on disjoint seed blocks. It is not an i.i.d. Monte Carlo error, and
it carries nothing biological or experimental.

## 5. Tolerance, verdicts and expectations — declared now

**Tolerance `δ = 0.005`** in occupancy units, U5b's value, kept so that the two
increments are read on one scale. The verdict table is U5b's:

- `EXACTLY_IDENTICAL`: every per-block difference is exactly 0.
- `WITHIN_TOLERANCE`: the interval lies inside `[−δ, δ]`.
- `BEYOND_TOLERANCE`: the interval does not meet `[−δ, δ]`.
- `INDETERMINATE`: anything else.

`WITHIN_TOLERANCE` means no detected change at this precision, never no change.

**Pre-declared expectations, each of which can fail:**

1. **Exact identity where the rules never disagree.** `EXACTLY_IDENTICAL` for
   every node in `basal_maternal`, `e2_primed_maternal` and
   `adhesion_challenge_basal`, in the primary comparison and in both
   attribution arms.
   - C5's rules differ only when `S_HAND2` is on. `S_HAND2 = (S_BMP2 or S_PGR)
     and not IN_HAND2_LOSS`, and `S_PGR`, `S_NR2F2` and `S_BMP2` all need
     `IN_PROGESTIN`, which is off in all three cells.
   - C1's rules differ only when `E_RECEPTIVE_SURFACE` is on, which needs
     `E_GP130_STAT3`, hence `E_SECRETORY_STATE`, hence `E_PGR`, hence
     `IN_PROGESTIN`.

   **If this fails, the pairing does not work as claimed and the run is
   invalid.**
2. **The unaffected family has the same law.** Every one of its intervals is
   `WITHIN_TOLERANCE` or `EXACTLY_IDENTICAL`.
   - A `BEYOND_TOLERANCE` there contradicts section 1's argument and is
     reported as a defect, not interpreted.
   - An `INDETERMINATE` there is a precision shortfall, not a violation. U5b's
     equivalent family left 52 of 900 bands too wide to certify. The count of
     such bands is reported, and this expectation is then recorded as **not met
     at this precision** rather than as held.
3. **Directions in the attribution arms, stated for falsification only.**
   - **C1-only:** the phase-averaged `OUT_EPITHELIAL_RECEPTIVE` difference is
     `≥ 0` in every cell. The node's inputs keep their law, because C1 changes
     no rule they depend on, and the new rule is a pointwise weakening.
   - **C5-only:** the phase-averaged `E_ESTROGENIC_PROLIFERATION` difference is
     `≥ 0` in every cell, by the same argument.

   A difference whose interval lies wholly below `0` falsifies the statement
   and is reported as such.

   **No direction or size is pre-declared for the combined comparison**,
   because the two changes act in opposite directions on
   `E_RECEPTIVE_SURFACE`'s descendants.

## 6. Trajectory-count stability check

This is U5b's check, applied to the primary family of the primary comparison
only. `|D̄₂ₖ − D̄₂₀ₖ| ≤ q·√(SE₂ₖ² + SE₂₀ₖ²)` must hold, with `q` the
Bonferroni-adjusted normal quantile, **and** both counts must reach the same
verdict. Verdicts are read at `N = 20,000`. A cell that fails is `UNSTABLE` and
is not interpreted. The attribution arms run at one count only and are not
stability-checked.

## 7. What no outcome of this licenses, and what it decides

- **No biological, clinical or kinetic claim.** MaBoSS time is uncalibrated,
  and a phase-averaged occupancy is not a probability that any epithelium is
  receptive.
- **It does not adopt v0.5.2 anywhere.** Every analysis module pins its own
  model version, and none is repointed by this unit. Whether any artifact moves
  to v0.5.2 is a separate decision, taken by the owner after reading this
  comparison, and recorded where it is made.
- **A large transient is not a reason to keep the conjuncts.** Both conjuncts
  are removed on evidence grounds (section 1). The comparison exists so that
  any later reader of v0.5.2's finite-horizon readouts knows how far they move
  from v0.5.1's, and why.
