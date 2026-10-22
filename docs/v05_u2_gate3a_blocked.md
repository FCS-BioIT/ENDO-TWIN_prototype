# U2 — Gate 3a cannot be delivered as the plan specifies it

**Unit:** U2 of `docs/v05_mechanistic_integration_plan.md`.
**Outcome:** **both halves of U2 are blocked — but on two different things, and
conflating them would send the next unit after the wrong evidence.**
De-aliasing `S_PRL`/`S_IGFBP1` is blocked on **measurement**. The day-3 arm is
blocked on **physical-time semantics**, which no assay supplies: it needs a
calibrated time axis, and this project explicitly disclaims one. An earlier
revision of this record labelled both "measurement", following
`gate3a_closure_audit.md`'s summary line, which is accurate for the axis it was
written about and too narrow for the day-3 half. No rule, node, edge, threshold,
rate, istate, protocol arm or recorded output changes.
**Delivered instead:** the guards that keep them blocked under v0.5, and this
record. `tests/unit/test_v05_gate3a_guards.py`.

---

## 1. What U2 was told to do, and why it cannot be done

The plan gives U2 two deliverables and calls it "the first concrete v0.5
deliverable":

> De-alias `S_PRL` from `S_IGFBP1`; add the day-3 maternal protocol stage …
> **Simulate the transient** and test whether IGFBP-1-before-PRL emerges
> robustly across seeds, trajectory counts, initial conditions and admissible
> variants.

Each half is refused by a completed analysis unit in this repository, on grounds
that are structural rather than a matter of looking harder.

### 1.1 The transient cannot distinguish the two nodes — this is a proof

`docs/prl_igfbp1_temporal_axis.md` §1. In the committed model:

```
Node S_DECIDUALIZED { logic = S_PGR and S_PKA and S_BMP2; }
Node S_PRL          { logic = S_DECIDUALIZED; }
Node S_IGFBP1       { logic = S_DECIDUALIZED; }

S_PRL.istate = FALSE;   S_IGFBP1.istate = FALSE;
```

and no `rate_up` or `rate_down` is declared in `baseline.cfg` or in any of the
21 condition `.cfg` files, so both take the MaBoSS default. **One Boolean
function, one initial state, one rate: the nodes are exchangeable.** Their onset
distributions are identical at every horizon and under every seed.

So "simulate the transient and test whether IGFBP-1-before-PRL emerges robustly
across seeds and trajectory counts" is not a test that can pass or fail — it is
a test whose answer is fixed by construction.

**Stated precisely, because the loose version would mislead if this becomes
methods text.** Individual stochastic trajectories *can* fire the two nodes in
either order: that is ordinary transition timing in a continuous-time Markov
process, not a defect and not an artefact. What is established is the stronger
and more useful thing — **there is no systematic directional information to
recover.** Given equal logic, equal effective rates and equal effective initial
states, the two onset distributions are identical, so the pathwise ordering is
symmetric and its expectation carries nothing about biology. (`prl_igfbp1_temporal_axis.md`
§1 puts this as "node-ordering noise", which is the same claim more loosely
phrased; that document belongs to a completed unit and is not edited here.)

Re-verified against both v0.4 and the v0.5 scaffold at this commit and asserted
in `AliasStaysInPlaceTest`.

### 1.2 A day-3 arm cannot be identified with day 3

`docs/prl_igfbp1_temporal_axis.md` §2, re-verified field by field against
`config/adoc_outlet_conditions.tsv`: `COND-DAY3-SAMPLE` and `COND-DAY6-SAMPLE`
carry **identical `agents`, `agent_concentrations` and `condition_normalized`**
(E2 10 nM; MPA 1 µM; cAMP 0.25 mM; XAV939 10 µM). **That is the part the argument
needs: the Boolean input vector is the same.**

*Corrected after review.* An earlier revision of this sentence said "only
`hours_after_cocktail_start` differs — 24 against 96". **Ten fields differ**,
and one of them matters to a different claim in this same document:
`collection_duration` is blank for day 3 and `48` for day 6, with
`collection_duration_state` `not_stated` against `stated`. The day-3 row's own
note says why that is not a detail — *"The collection window for this timepoint
is NOT stated ... so a day-3 versus day-6 magnitude comparison is **not
window-matched**"*. Both rows carry `applies_to_sheets = IGFBP-1;PRL`, with no
PAEP series at all — day 6 read `PAEP;IGFBP-1;PRL` when this record was written,
which was an error in the table corrected under `SOFIA-COMM-007` (PAEP's two
rows are treatment phases, not sampled days; see
`docs/collaborator_metadata_2026-09-18.md`). That is why the count is ten here
and was eleven before: the field stopped differing, and no argument in this
document rests on it.

This **strengthens** §1.3's magnitude argument rather than weakening it: the 83×
day-3 gap is measured across accumulation windows that are not matched and one
of which is unrecorded. But "only elapsed time differs" was false about the
shipped table and suppressed a caveat the table itself records, so it is stated
correctly here. What survives unchanged is the claim the day-3 blocker rests
on — same agents, same concentrations, therefore the same Boolean arm.

A Boolean arm expresses an input vector, not an elapsed time. The two conditions
therefore have the same arm, and `config/calibration.yaml` records
`duration_units: relative_only` with no physical-time calibration claimed;
`COND-DAY3-SAMPLE`'s own note calls its 24 h "Wall-clock bench time only: never
a MaBoSS horizon or transition rate". An arm named for day 3 would carry inputs
identical to `hormone_treated_maternal`, could not be identified with day 3, and
by §1.1 would show the two nodes identical regardless.

### 1.3 The ordering the repair targets is not established

Three separate confounds, all recorded, none resolved:

- **Magnitude and detection limit.** On the like-for-like stromal outlet the
  IGFBP-1/PRL median gap is **83× at day 3 and 9× at day 6**, on top of a **2×
  lower detection limit** (LOD 5 against 10). Two analytes with *identical*
  onset kinetics would still show IGFBP-1 crossing detection first, by a wide
  margin, on those numbers alone.
- **It is not a lag at all.** IGFBP-1 is detected in **4 of 5 stromal units at
  day 0, before any hormone**, at a median of 237 pg/mL; PRL in **0 of 6**. That
  is constitutive against induced, not early against late, and the two call for
  different repairs.
- **Provenance.** The column-to-chip mapping is recorded as **lost, not merely
  unverified**, rows are not paired across days, chips are not independent
  patients, and n is 5 and 6. IGFBP-1 detection also *falls* from 5/5 at day 3
  to 3/5 at day 6.

### 1.4 The one repair that survives on the merits is a leakage violation

`prl_igfbp1_temporal_axis.md` §6 rates "give `S_IGFBP1` a hormone-independent
basal route" the best-supported of four candidates, and still rejects it. It
rests entirely on where the IGFBP-1 ON/OFF boundary sits relative to that 237
pg/mL day-0 median, and **there is no pre-registered binarisation threshold for
IGFBP-1**.

OM-002 — the day-0/3/6 IGFBP-1 series — is itself `active_diagnostic`. Choosing
a threshold from that series to justify a topology change, and then letting
OM-002 evaluate the changed model, is the leakage OM-001's recorded rule forbids
in terms, for the analogous PAEP case:

> It **must never be chosen from these same observations while they also serve
> as the feasibility gate.**

and which `AGENTS.md` states as a project contract: *"Pre-register thresholds and
leakage controls; do not tune topology, mapping, rates, or interpretations on
the same held-out outcomes used for validation."*

**This is the decisive point for U2.** The only way to deliver U2 as written is
to pick that threshold from the diagnostic data. Doing so would make the plan's
checklist green by moving the rule rather than the code — the failure mode
`AGENTS.md`, the harness policy and the plan's own §13.5 all name.

## 2. Why the plan asked for something the repository had already refused

Not an error of reasoning — an error of chronology, and the same one §0.3
records happening once already.

| document | last written | says |
|---|---|---|
| `docs/v05_plan_review.md` §1113-1122 | `4d4aa0c`, 2026-09-16 20:31 | order the repairs 3a first: "De-alias S_PRL from S_IGFBP1 and add the day-3 maternal protocol stage, so OM-016 becomes evaluable" |
| `docs/prl_igfbp1_temporal_axis.md` | `77c5b5e`, 2026-09-16 21:18 | no variant adopted, no rate introduced, no day-3 arm created; "blocked on measurement, not modelling" |
| `docs/gate3a_closure_audit.md` | `1340810`, 2026-09-17 09:54 | records the axis as "**blocked on measurement, not modelling**"; "do not close Gate 3a and do not open Gate 3b" |

U2 was derived from the first row. The second and third **postdate it** and
reverse it. The mechanistic plan cites `prl_igfbp1_temporal_axis.md` only in a
reading list and never carries its conclusion, which is precisely why that
reading was a prerequisite of this unit.

`gate3a_closure_audit.md` also states the general position: "Gate 3a's analysis
is complete — every axis has been taken as far as the evidence allows, and **the
remaining work is measurement**."

## 3. The gap this exposed, and what U2 delivered

`tests/unit/test_prl_igfbp1_axis.py` already pins most of §1 — **against
`adoc-literature-superset-v0.4.0` only**. v0.4 is now immutable (T-H), so those
assertions can no longer fail. The model that *can* change is v0.5.

**A de-aliased `S_PRL` written into v0.5's `network.bnd`, or a day-3 arm added
to v0.5's condition suite, would have passed the entire existing 1,069-test
suite in silence** — while doing exactly what the plan instructed the next
session to do.

`tests/unit/test_v05_gate3a_guards.py` closes that. It asserts across **both**
executable supersets that the two nodes share one Boolean function, one initial
state and no declared rate; that no `*day3*` / `*day_3*` / `*day-3*` arm exists;
and that v0.5's condition suite is still v0.4's 21-file set, so an arm cannot be
added under an unrelated name. Both forbidden changes were applied to v0.5 and
observed to fail the guards before this was committed.

## 4. What would unblock U2 — two lists, not one

### 4a. The de-aliasing half — blocked on measurement

From `prl_igfbp1_temporal_axis.md` §6, unchanged and not re-derived here:

1. **Assay-compatible binarisation evidence for IGFBP-1** that is not drawn from
   the OM-002 series. A threshold borrowed from another study transfers only if
   that study matches in what sets the number — collection geometry,
   accumulation time, medium, dilution, normalisation — or establishes a genuine
   biological boundary. Otherwise it replaces one unregistered calibration choice
   with another and hides it behind a citation.
2. **Paired per-chip PRL and IGFBP-1 at the same timepoints**, making the
   ordering a within-unit comparison. The mapping is recorded as lost; recovering
   it is a metadata request, not an experiment.
3. **A normalised or absolute-quantified readout** removing the 83× confound.

### 4b. The day-3 half — not blocked on measurement at all

None of 4a's three items unblocks it. Day 3 and day 6 are the same Boolean input
vector; what is missing is a **mapping between bench hours and MaBoSS relative
time**, and `config/calibration.yaml` records `duration_units: relative_only`
with no physical-time calibration claimed. Supplying a better IGFBP-1 assay,
paired chips, or absolute quantification would leave the arm exactly as
unidentifiable as it is now.

Unblocking it means **changing what the model claims about time** — a
pre-registered physical-time calibration with its own evidence and its own claim
ceiling. That is a larger decision than U2, it is nobody's to take incidentally
while adding a condition file, and `AGENTS.md` forbids inventing physical time
units where evidence is unavailable.

Until 4a lands, the de-aliasing stays blocked; until time semantics are decided,
the day-3 arm stays unrepresentable. Gate 3a stays open in the state "analysis
complete, blocked on assays".

## 5. What U2 did not do

It did not de-alias `S_PRL`, add a day-3 arm, introduce a transition rate,
choose a binarisation threshold, simulate a transient whose result is fixed by
construction, alter any recorded output, or re-derive the day-0 contradiction
that OM-002 already records. It did not modify v0.4, and it did not modify any
mechanism-bearing file in v0.5 — the scaffold's 38 shared git blobs are
unchanged.

**It also did not renumber the plan's units.** U3–U8 keep their identifiers and
their order; U2 is recorded as blocked in place, because a unit that is blocked
on measurement is a result, not a gap to be closed by resequencing.
