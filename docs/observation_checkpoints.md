# Within-phase observation checkpoints (unit U2b)

Status: architecture + records, 2026-09-18. **No topology, rule, istate, rate,
protocol, condition cfg or recorded model output changes.** No model node was
de-aliased and no transition rate was introduced.

An experiment samples a treatment phase more than once. ADOC samples the 96 h
full-cocktail phase at 24 h (day 3) and 96 h (day 6), and future runs are
expected to sample it roughly every 24 h. The model already runs that phase as
**one continuous MaBoSS trajectory**, initialised by continuation from E2
priming and emitted at every `time_tick`. What was missing was a way to record
*that an experiment looked, and in what order* — without smuggling in a
physical-time calibration, and without a rule whose answer changes when the next
experiment is declared. The honest answer turned out to be that an interior
observation gets **no simulated counterpart at all** while physical time is
uncalibrated; what it gets is a record, an order, and phase-wide comparisons
that need no position.

---

## 1. The three time quantities, kept apart

| quantity | example | what it is | where it lives |
|---|---|---|---|
| experimental elapsed time | 24 h, 96 h | a fact about the bench | `hours_after_phase_start`; `experimental_day_anchors` in `config/protocols.yaml` |
| experimental phase fraction | 24/96 = 0.25 | *still* a fact about the bench: where the sample sat in the **experimental** phase | `experimental_phase_fraction` |
| MaBoSS relative time | `phase_local_time` 0.0 … 3.9 declared, 0.0 … 24.9 converged | the simulation's own axis, and it has two executed extents | the executed timeline frame |

`config/calibration.yaml` records `calibrated_physical_time: false`. There is no
validated map between the first column and the third, **in either direction**,
and this unit does not create one.

## 2. Why an interior checkpoint gets no simulation time

Two placement rules were tried. Both are rejected, and the second was shipped
first and corrected under external review.

**Proportional placement is a calibration written as a ratio.** Reading 24 h of
a 96 h phase at `hours / phase_hours` of the simulated duration asserts
`hours = k × relative time` with `k = 96/4 = 24` hours per unit — precisely what
`calibrated_physical_time: false` denies. It is also under-determined: this
repository executes the same phase at two horizons, the declared
`relative_duration` (4.0) and the converged fixed point of
[`endpoint_convergence_finding.md`](endpoint_convergence_finding.md) (25.0),
and "0.25 of the phase" names a different part of a still-rising curve under
each.

**Ordinal-rank placement is unstable under extension**, which is worse. Placing
the *k*-th of *n* checkpoints at `k/n` of the phase uses no hours, but it makes
a reading depend on what else is declared: the day-3 reading sits at ½ of the
trajectory with two checkpoints and slides to ¼ the moment 48 h and 72 h are
added. An unchanged historical observation would acquire a different simulated
value because a *different* observation was declared. A rule with that property
cannot carry an observation, and the instability is not fixed by choosing
another arbitrary number.

**So an interior checkpoint has no simulation time and no read value.** It
carries its experimental hours, its experimental phase fraction and its order,
and that is the whole of what it asserts. This is a result, not a gap awaiting
a better rule: while physical time is uncalibrated there is no position in the
trajectory that means "24 h into the phase", and `validate_checkpoints()`
rejects both retired rules by name so neither can return quietly.

The one readable position is the **phase end**, because the end of an executed
phase is the only position no rule has to choose.

## 3. What is still comparable, and on what condition

Nothing here needs an interior position, because the comparisons that matter are
phase-wide.

**A correction to an earlier version of this document.** It claimed that
comparing two nodes *at the same checkpoint* is automatically invariant under
any monotone reparameterisation of time, because both are read at one position.
That is wrong where the trajectories cross: reparameterising moves the position
to a different underlying time, and the sign of the difference can differ there.
The invariance holds only where the sign is **constant across the phase**. The
analogous across-checkpoint claim is likewise conditional — it needs the
trajectory to be **monotone**, not merely the placement to preserve order.

Those two conditions are not assumed anywhere; they are what
`ordering_verdict()` and `monotonicity_verdict()` examine, over every sampled
time in the phase, and that is the safeguard the earlier prose was wrongly
attributing to a reparameterisation argument.

**But only the first is ever certified.** `ordering_verdict` returns
`invariant_greater`/`invariant_less` when every estimate lies outside the band
in one direction, which does establish the true sign. The monotonicity
diagnostic cannot do the same: its band bounds the error of the *estimate*, so
"every later-minus-earlier estimate is at least −t" establishes only that the
truth is at least −2t, not that nothing fell. A fall from 0.50 to 0.45 inside a
band of 0.081 is a real fall. So that function claims only what it has —
`no_resolved_decrease_within_mc_error` — and **no across-checkpoint ordering is
licensed by this unit at all.** None is needed: the interior checkpoint is
unplaced, so there is nothing to order it against. Certifying a true
non-decrease would require every ordered estimate to exceed *+t*, which a
saturating trajectory cannot meet.

The cost is stated plainly: **no magnitude, rate, half-time or absolute-time
claim is licensed by any checkpoint**, and none becomes licensed by adding more
of them.

## 4. What a checkpoint *is*

One row of [`config/observation_checkpoints.tsv`](../config/observation_checkpoints.tsv):
a predeclared observation position inside one existing protocol phase, carrying
its experimental timing, its order, its placement rule, the endpoint horizon it
belongs to (terminal checkpoints only), the model nodes it is read for, the
observation-map rows that hold the measured side, what it licenses, and an
explicit list of forbidden uses.

**What it licenses is checked against what it can support.** The vocabulary
splits on whether a comparison needs a model value *at* the checkpoint:
`phase_wide_sign_invariance` and `phase_wide_resolved_change` are properties of
the executed phase and need no position, so an unplaced checkpoint may declare
them; `endpoint_node_value` and `endpoint_cross_analyte` read a value, so only a
`phase_end` checkpoint may. `CHK-HTM-D3` therefore licenses the two phase-wide
diagnostics and nothing else. Both rows previously declared
`within_phase_ordering;cross_analyte_same_checkpoint` — each of which names a
comparison at a checkpoint — so the contract was licensing, for the unplaced
one, exactly the reading `read_checkpoints` returns as `None`. The field was
parsed and never validated; `validate_checkpoints` now enforces it.

It is **not** a protocol, a condition cfg, an input vector, a horizon or a
restart. `read_checkpoints()` selects rows from an already-executed phase frame:
it runs no simulation, so it cannot reset a state even by accident.

**The endpoint horizon is measured, not asserted.** `executed_phase()`
classifies the run from its own executed extent against the declared duration in
`config/protocols.yaml` and the converged horizon: equal to one, equal to the
other, or refused. `read_checkpoints()` has no `horizon` argument at all, and
refuses a terminal checkpoint whose `endpoint_horizon_policy` disagrees with the
measurement.

An earlier version took the horizon as a string on the caller's word, which
protected nothing: a declared-duration frame labelled `converged_fixed_point`
was read as converged, and the label and the frame are exactly what has to
agree. The two runs genuinely differ — `S_IGFBP1` ends near 0.46 at the declared
duration and at 1.0 at the converged fixed point — so `CHK-HTM-D6` declares
`converged_fixed_point`, the horizon `OM-002` and the active constraints are
read at, and a declared-duration run is rejected for it.

**Predeclaration.** Placement is fixed by the experiment's own timing and the
order it implies. A checkpoint may never be moved, added or reordered because of
a molecular value seen afterwards; `validate_checkpoints()` rejects a phase whose
ordinal order does not follow its experimental hours.

**Future sampling needs no code.** Declaring 48 h and 72 h rows gives four
ordered checkpoints on the same single trajectory, with no new protocol, no cfg
and no branch — and, by construction now, without disturbing what the existing
two mean. `test_declaring_future_checkpoints_cannot_move_an_existing_one`
asserts that directly.

## 5. How day 3 and day 6 map

| checkpoint | experimental | phase fraction (experimental) | order | placement | simulated value |
|---|---|---|---|---|---|
| `CHK-HTM-D3` | 24 h into the cocktail (protocol day 3) | 0.25 | 1 of 2 | `unplaced_ordinal` | **none** |
| `CHK-HTM-D6` | 96 h into the cocktail (protocol day 6) | 1.0 | 2 of 2 | `phase_end`, `converged_fixed_point` | the converged endpoint |

Both sit in the single `hormone_treated_maternal` phase and share its input
vector exactly — which is why an *arm* for day 3 was never the right object.
Day 3 is represented, ordered and auditable, and has no model counterpart value;
that is the honest state of the alignment, not an omission. `CHK-HTM-D6` reads
the end of the **converged** run, which is the horizon `OM-002` is evaluated at,
so the two refer to the same state rather than merely sounding alike.

The **measured** side is not duplicated here. The numbers stay in
`config/observation_model_map.tsv` (`OM-002`, `OM-004`, `OM-006`, `OM-013`,
`OM-014`, `OM-016`); the checkpoint rows point at them.

**PAEP is deliberately absent.** Unit B established only that no sampled PAEP
day is assignable on current evidence (`SOFIA-COMM-007`); its two rows are
treatment phases. No PAEP checkpoint exists and none may be invented.

## 6. What changed in the observation map, and why

| row | before | now |
|---|---|---|
| `OM-004` | rejected — "no protocol counterpart" for day 3 | still **rejected**, on the ground that always sat underneath: the column-to-chip mapping is lost, so "across all 5 BOTTOM units" is an unpaired group comparison, and the day-3 collection window is unstated so it is not window-matched to day 6 |
| `OM-005` | rejected — 2/5 on the data, *and* "no protocol counterpart" | still **rejected** on the data ground alone; the coverage ground is withdrawn |
| `OM-006` | not calibration-eligible, ground (i) "no protocol represents day 3" | still not eligible; ground (i) is replaced by "the day-3 checkpoint carries no simulation time, so there is no day-3 model value to compare against" |
| `OM-011` | open protocol-coverage gap; **instructed** "add a mid-cocktail protocol stage" | **partially closed**: the need for a day-3 *arm* is gone and the instruction is withdrawn (it contradicted `NoDayThreeArmTest`), while the experimental→MaBoSS *temporal alignment* is recorded as still unresolved |
| `OM-016` | not evaluable: (a) no day-3 protocol, (b) the alias | (a) closed in its protocol half, open in its temporal half; (b) stands and is now measured rather than assumed; (c) — the confounded observation — governs what may be concluded |

The verdicts did not move. The **reasons** did. Two of them moved from a
modelling gap to a measurement limit, which matters because a modelling gap
invites building something and that invitation is now withdrawn.

**The canonical current state, in one place.** The protocol phase exists; the
day-3 experimental checkpoint exists; the experimental→MaBoSS alignment is
**unresolved**; there is therefore **no day-3 simulated value**. Every
current-state home says that and nothing more: `config/protocols.yaml`, the
checkpoint table, the contract and the observation map. Rows may cite this
document; they may not restate *how* a checkpoint is placed, and they may not
say day 3 has "no protocol counterpart" — the phase is the counterpart, what is
missing is the alignment.

Two guards hold that, and both were checked by reinjecting the retired wording
and watching them fail: `test_the_observation_map_describes_no_placement_rule`
(placement vocabulary, case-insensitively) and
`test_no_current_state_home_still_says_day_three_has_no_protocol` (the retired
claim, sentence by sentence, allowing it only where a history marker shows it is
the superseded record). `OM-011` keeps its history deliberately; history is not
drift.

`OM-016` was also **narrowed**. It used to say that any model in which
`S_IGFBP1` and `S_PRL` are identical "is inconsistent with this observation".
That was incoherent with the rest of the same row, which records the observation
as too assay-confounded to establish a kinetic ordering: an observation that
cannot establish an ordering cannot falsify a model for lacking one. The row now
records what is actually established — that the current model **cannot express
analyte-specific divergence** between the two — which is a measured property of
the model and a real limit on any candidate in this family, and stops short of
calling the model refuted.

## 7. The PRL / IGFBP-1 alias: adjudicated, not retired

**They remain aliased, and this unit deliberately leaves them aliased.**

`S_PRL`, `S_IGFBP1` and `S_SPP1` all carry `logic = S_DECIDUALIZED`, with no
distinguishing rate and equal effective initial states under every committed
condition. [`prl_igfbp1_temporal_axis.md`](prl_igfbp1_temporal_axis.md) §1 proves
this makes them exchangeable — identical onset distributions at every horizon and
under every seed — and `tests/unit/test_v05_gate3a_guards.py` pins it.

What the checkpoint layer adds is that the degeneracy is now **measured on a real
run rather than assumed**, and that the measurement has demonstrated power:

| comparison on one 2000-trajectory maternal-lineage run | verdict |
|---|---|
| `S_IGFBP1` vs `S_PRL` | `indistinguishable_within_monte_carlo_tolerance` — no sampled time shows a gap outside the band |
| `S_PGR` vs `S_PRL` (a genuine upstream/downstream pair) | `placement_dependent` — some sampled time does |
| `S_PKA` vs `S_IGFBP1`, `S_DECIDUALIZED` vs `S_PRL` | `placement_dependent` |

Same trajectory, same band, two different answers. So `indistinguishable` for
the aliased pair is a property of the model, not the sensitivity floor of the
method: a real difference in the same phase is seen. At the converged horizon
the measured gap for the aliased pair is about 0.015 against a band of 0.11 —
a sevenfold margin — while `S_PGR` against `S_PRL` reaches 0.79.

**The band, and why it changed.** It was `z·√2·0.5/√N`, the normal-approximation
bound for the difference of two **independent** estimates. Two nodes read from
one set of trajectories are not independent, and their covariance is *not
identifiable* from marginal `nodes_probtraj` curves — those give `P(A)` and
`P(B)`, never `P(A, B)` — so it can be neither assumed nor measured from what
the layer is given. What the layer computes is already a **paired** quantity:
`P̂(A) − P̂(B)` is the mean of the per-trajectory difference `D = A − B ∈ [−1, 1]`.
Hoeffding's inequality on that mean gives

> `t = √( 2 · ln(2·comparisons / α) / N )`

which holds under **arbitrary** within-trajectory dependence between A and B,
because the dependence never has to be decomposed. It is wider than the retired
band — the conservative direction for asserting a difference. Its assumptions
are stated in the function: trajectories independent of one another, both nodes
read from the *same* run so the pairing is real, and `comparisons` counting
every comparison the verdict makes.

**Multiplicity belongs to the verdict, not the caller.** `ordering_verdict`
compares every sampled time (*n*); `monotonicity_verdict` compares every ordered
pair (*n(n−1)/2*). Each derives its own band from its own count, so a band
computed for one multiplicity can no longer be handed to the other — which is
how the monotonicity relation was widened without anyone noticing the arithmetic
had moved with it.

**And the execution belongs to the data.** The band's other input is the
trajectory count, which was also a caller's argument until the same rows
evaluated at a claimed *N* = 10⁹ returned `invariant_greater` where at their
real *N* = 2000 they returned `indistinguishable`. Reading and verdicts now
consume an `ExecutedPhase` built by `executed_phase()` from the
`SequentialTimeline` that produced the rows, carrying the model version,
trajectory count, seed, declared and executed duration and the measured horizon.
A synthetic test may construct one; a production caller has nothing left to
assert. `applies_to_model_versions`, previously parsed and never enforced, is
checked at that boundary.

**Why no pair returns `invariant_greater` here**, and why that is not a defect:
this phase begins from the E2-primed state, before the decidualization cascade
fires, so every upstream/downstream pair in it starts at or near zero and
separates only later. Two series that coincide at the start cannot be ordered at
*every* sampled time under any tolerance. That is the abstraction earning its
keep rather than failing: it says that "does PGR lead PRL in this phase?" has a
different answer depending on where one looks, and that without a calibrated time
axis this repository cannot say where that is.

### What the data do and do not license

**Do:** establish, on the model side, that it has *no discriminating power at
all* on this axis. Whatever an observation eventually says about IGFBP-1 and PRL
onset, the current model answers identically everywhere in the phase. That is
now measured rather than assumed, and it is a limit on what any candidate in
this family could predict here.

It is **not** a refutation. `OM-016` is not "failed": for the model to fail an
observation, the observation would have to establish the thing the model cannot
produce, and blocker (c) says this one does not.

**Do not:** retire the alias. The observed ordering is a *detection-fraction*
ordering, and §§3–4 of the temporal-axis finding show it cannot establish a
kinetic one — an 83× day-3 magnitude gap on top of a 2× lower detection limit
would produce it between two analytes with identical onset kinetics, and IGFBP-1
is detected in 4/5 stromal units at day 0 *before any hormone*, which is a
constitutive-versus-induced difference rather than a timing one. Checkpoints
remove the protocol-coverage blocker; they do not touch that one.

**Certainly do not:** choose between the candidate repairs — a different Boolean
rule, an explicit delay, a differential transition rate, an intermediate node.
Nothing here distinguishes them, and §5 of the same finding shows the
binarisation threshold that would settle the day-0 question may not be drawn from
the same series that serves as diagnostic `OM-002`.

So the observation layer is now *able* to falsify the alias when an
assay-compatible readout arrives — it can express the comparison and has
demonstrated it would see a difference — and the data in hand do not falsify it.
The model is therefore not yet allowed to choose a replacement. That ordering —
be able to falsify first, repair second — is the reason this unit stopped here.

## 8. Tests

`tests/unit/test_observation_checkpoints.py` covers the schema, the
committed rows, placement, validation and the invariance verdicts. The negative
controls are the substance: a `proportional` row is rejected while physical time
is uncalibrated *and admitted if it were* (so the rule states its own condition);
an `ordinal_rank` row is rejected under **either** time semantics, because its
defect is instability rather than an unwarranted calibration; declaring 48 h and
72 h leaves every existing reading and every verdict identical; reading the
endpoint off the wrong horizon raises; an interior checkpoint that declares an
endpoint horizon is rejected, as is a phase with two ends; a phase whose ordinal
order contradicts its hours is rejected; a checkpoint on an undeclared phase is
rejected; a crossing trajectory returns `placement_dependent` rather than a
verdict; and a gap inside the Monte Carlo tolerance returns `indistinguishable`
while a gap outside it returns a verdict; and a series that falls from 1.0 to
0.002 through individually sub-band steps does **not** come back as "no
decrease" — the regression for a real defect, since `monotonicity_verdict` used
to compare adjacent steps, which is not transitive under a band. Two further
regressions pin the provenance holes: the same rows evaluated at an inflated
trajectory count used to flip `indistinguishable` into `invariant_greater`, and
a checkpoint read against a model version it does not declare used to pass
silently.

`tests/integration/test_observation_checkpoints_runtime.py` runs the
real maternal lineage on the live v0.5 superset at **both** horizons and asserts
that the executed lineage has exactly its three declared arms, that the observed
phase is one continuous trajectory with a single phase index and a monotone axis
from zero, that the experimental 96 h corresponds to neither executed duration,
that the two horizons genuinely end in different states and that reading
`CHK-HTM-D6` off the declared-duration run is refused, that day 3 gets no
simulated value from the real run either, the verdicts in §7, that the measured
gap for the aliased pair sits well inside its band rather than on the edge of
it, and that the phase starts from a state in which no pair could be ordered
everywhere.
