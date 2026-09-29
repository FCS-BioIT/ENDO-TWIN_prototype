# C3a — post-run execution note and unit record

**Written 2026-09-29, after the run.** This note is a retrospective
repository record. It does not edit, and must not be read as amending, the
completed run artifacts committed in `50b50e0`:

- `run_settings.json`;
- `attempts/attempt_20260929T174746194150Z.json`;
- `classification.tsv`, `bands.tsv`, `blocks.tsv` and `curves.tsv`.

Those files are canonical exactly as committed.

## 1. Run identity

| item | value |
|---|---|
| governing specification | `preregistration.md` at `0c7da9c`, plus `preregistration_addendum_01.md` at `ef34c10` |
| executed from | `c5081b0af0530dfbda1bf9f11360900ecd48fca1` (`feat/c3a-kinetic-readouts`) |
| attempt | `attempt_20260929T174746194150Z`, status `COMPLETED`, no error |
| blocks | 40 (20 at N = 20,000 and 20 at N = 2,000), 560 MaBoSS tasks, 3 workers, 34.6 min |
| seeds | 2,000,001–2,400,000 and 2,400,001–2,440,000; all reserved and spent by this attempt. **Never to be reused.** |
| result commit | `50b50e086c76a6defe3021ffa1f70563837e86ee` |

`validate_manifest` (required status `COMPLETED`) reported no problems, both on
the working tree after the run and on the committed state.

## 2. Execution deviation: live memory cap change

- **Launch:** the run was launched as the systemd user unit `dtadoc-c3a-run`
  with `MemoryMax=60G` and `MemorySwapMax=0`.
- **Trigger:** about 32 minutes into the run, the unit's recorded
  `MemoryPeak` was **52.1 GB** (52,144,664,576 bytes) against the 60G cap.
  Current use was 33.5 GB.
- **Change:** to avoid an out-of-memory kill of a worker, which would have
  failed the attempt and spent the seeds, the running unit's cap was raised
  to 90G with `systemctl --user set-property --runtime dtadoc-c3a-run.service
  MemoryMax=90G`.
- **No restart and no re-execution:** the job continued in the same process
  tree. No file, input, code or setting that the analysis reads was changed.
- **Bound inputs unchanged:** the end-of-run check requires the bound and
  generator hashes at the end to equal those at the start
  (`input_sha256_at_end == binding.input_sha256_at_start`). It passed, and
  canonical validation re-derives both from the `start_head` blobs.
- **Result-neutral:** section 13 of the pre-registration treats the worker
  count and the memory cap as execution settings that do not affect results.
- **Not in the manifest:** the manifest does not record the cap. This note
  and the `50b50e0` commit message are the record of the change.

## 3. Independent review record

This is a retrospective record of reviews that happened before this note was
written. It is **not** a claim that this note, or any review record, was
committed before the run. The repository's `aih` gate could not see these
reviews, which were carried out outside it.

| subject | review | verdict |
|---|---|---|
| `c5081b0` (exact implementation head, **before execution**) | external OpenAI broad independent review, supplied by the owner | PASS, no blockers; accepted for execution |
| `50b50e0` (results and provenance, after execution) | external OpenAI broad independent results/provenance review, supplied by the owner | PASS, no scientific or result blocker |

The `aih` gate's own rounds on the C3a runner were split between Codex and
the stand-in reviewer. Stand-in passes are degraded evidence and were not
treated as satisfying the independent-review precondition for simulation.

## 4. What C3a supports, and what it does not

**Pre-registered outcome.**

- **Classes:** all four classified outcomes are `PERSISTENT_SUPPRESSION`:
  mifepristone and HAND2 loss, each on `OUT_STABLE_ADHESION` and on
  `OUT_MATERNAL_ADHESION_COMPETENCE`.
- **Count checks:** every 20k-vs-2k check is `STABLE`.
- **Fixed-point difference:** about −0.82 in every case, against converged
  controls ending near 0.82.
- **No literal block:** every perturbed arm carries
  `ON_OCCUPANCY_OBSERVED_AT_SOME_RECORDED_TICK`, so no "block", "unreachable"
  or "never reached" wording is licensed.

**The robust statement.** Under default unit MaBoSS rates, in dimensionless
relative time, the v0.5.2 model shows fixed-point suppression of stable
adhesion and maternal adhesion competence, relative to the schedule-matched
unperturbed twin, for the hard mifepristone and HAND2-loss perturbations.

**Finite-window limitation, stated explicitly.**

- At the declared 1.0 challenge horizon, even the controls stay at the
  stable-adhesion floor: maximum mean P(`OUT_STABLE_ADHESION`) is about
  0.00128 (control after the HT extension) and 0.00019 (declared twin).
- The finite-window "equivalent" labels are therefore **not informative**
  about transient equivalence, delay, or the absence of an early effect.
  They hold because both arms are near zero.
- C3a cannot distinguish delay from block at the declared horizon.

**Not licensed:**

- any biological, clinical, kinetic or physical-time claim;
- any rate value;
- any statement that these perturbations delay or block implantation.

**No post hoc horizon.** No new transient horizon may be chosen from these
results. Any alternative kinetic horizon is a new analysis that must be
pre-registered prospectively, with fresh, disjoint seeds.

## 5. Closure

- **C3a is closed with this note.** It is not to be rerun, and its seeds are
  not to be reused.
- **C3b:** numerical relative-rate priors remain deferred.
- **C4:** the rate-based or partial anti-SPP1 penalty is not pursued (addendum
  01) unless an SPP1 perturbation is explicitly reintroduced.
- **Cleanup:** the empty `attempts/.reservation.lock` committed in `50b50e0`
  is removed in a separate cleanup commit.

## 6. Known provenance limitation (recorded 2026-09-30)

This is a **known provenance limitation, not a scientific deviation**. It is
recorded after the run, in response to independent review. Nothing was
recomputed or rerun, no seed was used, no horizon was added, and nothing in
`50b50e0` or the canonical result set changes.

- **Classes and bands reproduce.** The primary C3a kinetic classes and the
  empirical paired-block reproducibility bands are reproducible from the
  retained `blocks.tsv`. `outputs_problems` re-derives both tables byte for
  byte, from different inputs:
  - `bands.tsv` from `blocks.tsv` alone;
  - `classification.tsv` from `blocks.tsv` plus `curves.tsv`. Its fixed-point
    and finite-window labels, classes and count records come from
    `blocks.tsv`; its occupancy sub-label comes from `curves.tsv`.
- **Curve values do not.** `curves.tsv` is a canonical retained summary, and
  its schema, horizons, ranges and consistency are validated. Its `mean_p_on`
  and `sd_p_on` values **cannot be re-derived** from committed per-block curve
  trajectories, because those trajectories were not retained.
- **The sub-label inherits this.** The curve-dependent occupancy sub-label in
  `classification.tsv` (`ON_OCCUPANCY_OBSERVED_AT_SOME_RECORDED_TICK`) is read
  from `curves.tsv`, so the same lineage limitation applies to it.
- **The governing results are unaffected.** This does not invalidate the
  fixed-point `PERSISTENT_SUPPRESSION` classes or the 20k-vs-2k stability
  checks, which rest on `blocks.tsv`.
- **Requirement for future runs.** Any future pre-registered simulation unit
  that produces canonical curve summaries must retain the per-block curve or
  trajectory-level inputs needed to regenerate them.
