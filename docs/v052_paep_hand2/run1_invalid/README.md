# v0.5.2 transient comparison, run 1 — INVALID under its frozen gate

**Status: INVALID.** Kept byte for byte as provenance. No result in this
directory supports v0.5.2, and none may be quoted as evidence for it.

## What ran

Run 1 is the paired comparison frozen in `../transient_preregistration.md`
(commit `969d1fe`), executed on 2026-09-28 from 17:52 to 21:03 CEST, with 2
workers and a 60 GB cap. An earlier start with 4 workers was killed by the OOM
killer after 2.5 minutes and produced no output.

- **Recorded `git_commit` is `969d1fe`.** v0.5.2, `v052_increment.py` and
  `v052_transient.py` were uncommitted when the run started.
- **Inputs are bound by hash.** `transient_run_settings.json` records sha256
  values for every generator file, both models' `network.bnd`, `baseline.cfg`
  and `provenance.toml`, and the pre-registration. On 2026-09-28 every one of
  them matched the files committed beside this directory. That is how this run
  is tied to its inputs.

## Why it is invalid

Expectation 1 of the pre-registration requires `EXACTLY_IDENTICAL` for every
node in `basal_maternal`, `e2_primed_maternal` and `adhesion_challenge_basal`,
defined as every per-block difference being exactly `0.0`. It says that if this
fails, "the run is invalid". The recorded outcome:

| comparison | expectation 1 |
|---|---|
| `c1only_vs_v051` | held |
| `c5only_vs_v051` | **failed** in all three cells |
| `v052_vs_v051` | **failed** in all three cells |

## Diagnosis, recorded after the fact (it does not rescue this run)

- **The failing differences are at most 7.7 × 10⁻¹⁶** in node occupancy. They
  appear in nodes that neither rule reads, such as the random-start relays.
- **The per-state distributions are exactly identical.** A direct check on
  2026-09-28 (seed 1, 20,000 trajectories) compared the final-tick per-state
  distributions of v0.5.1 against C5-only and against v0.5.2, in
  `basal_maternal` (368 states) and `e2_primed_maternal` (472 states). The
  largest difference was `0.0`.
- **Cause: floating-point rounding in the node-marginal roll-up.** The paired
  stochastic realisation is identical. The node marginals are sums over
  states, and removing `S_HAND2` from a rule's inputs changes the order of that
  summation.
- **C1 alone does not change any input set in these cells**, which is why it
  held exactly.

The owner ruled on 2026-09-28 that the frozen rule stands:

- this run is invalid;
- the exactness check is corrected prospectively, in
  `../transient_preregistration_addendum_01.md`, committed before run 2;
- run 2 is run on fresh seed blocks.

The one interval reported `UNSTABLE` here
(`e2_primed_maternal:E_ESTROGENIC_PROLIFERATION:final_tick`) is the same
rounding: exactly 0 at one trajectory count and about 10⁻¹⁶ at the other.
