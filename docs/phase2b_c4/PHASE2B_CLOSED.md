# Phase 2B: closed, NO_SUITABLE_REFERENCE

Recorded 2026-09-28, owner decision. **Phase 2B is complete.**

## Terminal verdict

**`NO_SUITABLE_REFERENCE`**, reached under the preregistered verdict rules.
C4 ran the frozen derivation on the only metadata-qualified candidate:
- **candidate:** C03, E-MTAB-10283, the XAV939 + E+P day-6 arm;
- **donors:** B44, U1, U2 (7,200, 3,049 and 1,914 included cells);
- **layer:** Cell Ranger 9.0.1 filtered counts (amendment 16).

`derive()` returned `NO_STABLE_SEPARATION`, because no donor's fitted
two-component mixture is bimodal (S2). U1 and U2 also fail S1 and S3, so S5
never ran. The count-scale diagnostic and both per-library diagnostics agree.
Evidence: `docs/phase2b_c4/step5_6/RESULT.json` (commit e43cdc6).

## What follows from it

- **No KLF12-high definition exists.** No threshold or variant was emitted.
- **C5 and C6 are not run.** C5 exists to freeze a threshold definition, and
  there is none.
- **Nothing else is tried:** no other threshold, fit, quantity, donor subset
  or reference. The frozen fallthrough forbids it, and C03 was the only
  candidate.
- **`E_KLF12_HIGH` keeps no externally derived definition.** Phase-2A mapping
  stays blocked. No donor-specific model or `.cfg` exists, and RR13 is unmet.
- **What this does not claim:** that KLF12 has no biological states. The
  preregistered separation procedure found no stable two-state separation in
  this reference.

## Record

| step | where |
|---|---|
| rules and amendments 01–19 | `docs/phase2b/` |
| stack identification | `docs/phase2b_c4/stack_identification_cr9.0.1.json` (c527c43) |
| Steps 3–4, value-blind | `docs/phase2b_c4/candidate_processing_steps_3_4.json` (62883dc) |
| Steps 5–6, value-aware | `docs/phase2b_c4/step5_6/` (e43cdc6) |

**First KLF12 exposure:** 2026-09-28T06:56:50Z, read through
`values.open_reference_values` with the guard passing.

**Review.** The independent gate ended `ESCALATED`, which is recorded as
unverified rather than reviewed.
- **B1 stays deferred.** It is the legacy Phase-2A RR04 decontX-layer
  conflict, and is moot now that no definition exists.
- **Accepted by the owner, not reviewed.** Whatever acceptance applies was
  given by the owner.

**Retained data.** The raw and intermediate data remain on
`/scratch/dt_adoc_phase2b/`, and every retained output is hashed in the
records above.
