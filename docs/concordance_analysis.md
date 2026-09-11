# Model-data concordance: what the ADOC digital twin explains, and what stops it

Status: **diagnostic assessment**, `adoc-literature-superset-v0.4.0`. Claim level:
`structural` + `reproducible`. No rule, rate, threshold, topology or calibration
file was changed to produce it.

This document interprets the tracked artifacts below. The artifacts are
authoritative; this is the narrative.

| Artifact | What it is |
|---|---|
| [`docs/concordance/concordance_table.tsv`](concordance/concordance_table.tsv) | the canonical row-per-result table: observation, mechanism, regenerated simulation, concordance class |
| [`docs/concordance/run_settings.json`](concordance/run_settings.json) | every simulated number, per seed, with model hashes and commit |
| [`docs/concordance/mechanism_nodes.tsv`](concordance/mechanism_nodes.tsv) | per-node evidence class, declared confidence, alias roster, phenotype inertness |
| [`docs/concordance/figure_source_data.tsv`](concordance/figure_source_data.tsv) | exactly the quantities the figure draws |
| [`docs/concordance/scrna_object_audit.json`](concordance/scrna_object_audit.json) | what the local integrated Seurat object contains |
| [`docs/assets/adoc_concordance_v0.4.0.png`](assets/adoc_concordance_v0.4.0.png) | the figure |

Rebuild with `pixi run build-concordance` (runs MaBoSS), redraw with
`pixi run render-concordance` (no simulation), re-audit the RDS with
`pixi run audit-scrna-object`.

---

## What this adds to the existing matrix

[`docs/results_reproducibility_matrix.tsv`](results_reproducibility_matrix.tsv)
already curated 60 rows over 55 published results, and it stays the hand-owned
observation record: no code writes it. Four things were missing, and this
analysis supplies them.

1. **The simulated numbers had no tracked provenance.** They were typed into the
   matrix, the run lived under `output/`, which is gitignored, and the narrative
   pointed at `output/reproducibility/run_settings.json`, **a file that does not
   exist**. Every simulated number is now regenerated from the committed model
   into `run_settings.json`, per seed, with the `network.bnd`, `baseline.cfg` and
   `protocols.yaml` hashes and the commit.

   The regeneration reproduces the curated values to six decimals on 9 of 11
   rows, including both secreted-protein declared values and the declared-horizon
   mifepristone value of 0.000020.

   Two converged relay-driven rows do **not** reproduce: R41b differs by −0.00021
   and R55 by −0.00077. **The cause is not established, and this analysis does
   not attribute them.** They are not explained by the across-seed spread, which
   for R55 is about 4×10⁻¹⁷; but no alternative account is asserted either,
   because this repository has no validated characterisation of these estimates'
   sampling behaviour (see "No quantitative claim" below), so attributing them to
   Monte Carlo noise, or declaring them small relative to an error, would be an
   unfounded attribution.
   What is recorded is the discrepancy itself, that both rows are converged
   quantities whose only graded content is the hand-set relay istates, and that
   the curated values they are compared against were produced by a run this
   repository does not otherwise pin. Two earlier phrasings of this passage —
   "within a few multiples of the seed spread", then "consistent with
   independent Monte Carlo draws" — each attributed the difference on a ruler
   that does not apply, and both are withdrawn.

2. **No row said which nodes generate its prediction.** Each row now carries the
   readout's backward cone, its *essential* free variables (exhaustively, over
   all 524,288 assignments), the free assumptions it rests on, how many cone
   members are phenotype-inert, its alias class, and the carrying path — the
   nodes whose value actually differs between the two compared arms.

3. **The matrix was assessed against v0.3.0 while v0.4.0 is active.** Verified:
   v0.4.0 is bit-identical to v0.3.0 on every tracked node in all three adhesion
   arms; the only difference is the presence of `IN_HAND2_LOSS`, which is OFF in
   every default condition. The staleness was documentational, not numerical.

4. **Two categories the curated vocabulary could not express.**
   `structural_falsification` and `not_expressible_by_model_class` are recorded
   in a new `concordance_class` column, alongside the unchanged curated
   `verdict`, so the refinement is auditable rather than a silent recode.

---

## The headline

Of 60 curated rows:

| Class | Rows |
|---|---:|
| Not expressible by the model class (Boolean: no geometry, flux, populations) | **36** |
| Not assessable with current data | **15** |
| Calibration / circular agreement | **4** |
| Directional agreement | **3** |
| Disagreement | **1** |
| Partial agreement (direction agrees, magnitude fails) | **1** |
| **Structural falsification** | **0** |
| **Quantitative agreement** | **0** |

Read that as: the model **engages 9 of 60 rows**, and of those, four are
agreement with evidence that built or filtered it, three are ordering-only, and
two are failures. Neither of the two strongest categories is occupied: nothing
is quantitatively reproduced, and nothing is structurally falsified either. That
is structural rather than a matter of tuning — at the converged horizon almost
every readout is
exactly 0 or 1, and the one graded endpoint is an arithmetic consequence of two
typed-in numbers.

### Reproduced

* **Three-arm adhesion ordering** (untreated < hormone-treated > mifepristone) at
  the converged horizon: 0.000 / 0.820 / 0.000 against observed 0/12, 9/19, 1/8.
  Ordering only. Two of the three arms are `role=calibration`.
* **PAEP rises** under the full cocktail versus E2-only priming, 5/5 chips.
  Direction only; this is the OM-001 feasibility gate, so agreeing with it is
  agreeing with the filter.
* **IGFBP-1 rises** from day 0 to day 6 in 3/5 column positions. Direction only;
  this is the OM-002 diagnostic, so it is circular too, and the column-to-chip
  mapping is lost so it is not a within-unit trajectory.

**PRL is not among them.** It is easy to state PAEP, IGFBP-1 and PRL as three
molecular successes, and that would be wrong twice over: PRL's mappings
(OM-006/014/015) are provisional or `context_only`, so the curated matrix
licenses **no directional verdict** at all and records the observation as a
heterogeneous late onset (0/6 at day 0, 1/6 at day 3, 3/6 at day 6, with day-6
values spanning 1.30–1465.44 pg/mL); and `S_PRL` is the same Boolean function as
`S_IGFBP1`, so even if it were assessable it would not be an independent readout.
The figure's panel B derives each status from the table's `concordance_class`
rather than from hand-written text, precisely so this cannot drift back.

### Partially reproduced / contradicted

* **The hormone-treated magnitude is wrong.** Simulated 0.820 against observed
  9/19 = 0.474, whose Wilson 95% CI is [0.27, 0.68]. The simulated value lies
  outside it. It is also not a fitted quantity: `baseline.cfg` configures the two
  interface relays at istate **0.70** and **0.40**, and
  `1 − (1 − 0.70)(1 − 0.40) = 0.82` exactly. The entire graded content of the
  model's headline prediction is two hand-set numbers.
* **R43a is not assessable at all**, and this is the analysis's most consequential
  finding about the repository. Its value is the declared-horizon mifepristone
  transient, and that transient is produced by switching mifepristone on *at the
  embryo challenge* — which is not the experiment. Under the recorded regimen
  there is no such transient to read. Reporting it as a disagreement would
  attribute to the model a failure that belongs to the protocol encoding, so the
  row is classed `not_assessable_with_current_data` with the reason recorded.
  What the run does show, for the record:

* **At the declared horizon the seed-averaged arm scores above the reference,
  and not reproducibly so.**
  Mifepristone averages 0.000020 against an unperturbed 0.000000. The declared
  horizon reads the endpoints roughly 4000× before their fixed point, so what
  this records is transient occupancy carried in from the hormone-conditioned
  state rather than a converged prediction.

  **The inversion does not survive the seed stream.** Seeds 1–5 give `0.0`,
  `2.5×10⁻⁷`, `0.0`, `5.03×10⁻⁵`, `5.03×10⁻⁵`
  (`docs/concordance/run_settings.json`): the arm exceeds the reference in three
  of five runs and ties it exactly in the other two, and the across-seed spread
  of `2.46×10⁻⁵` is larger than the mean it surrounds.

  An earlier revision of this section reported one value repeated identically in
  every seed, and called the inversion stable on that basis while noting that a
  zero seed spread is not evidence of precision. On the repaired lineage that is
  simply not what the run does, and the reading is withdrawn rather than
  rephrased. What replaces it is weaker, not stronger: a difference that vanishes
  in two of five seeds is not a direction this design establishes at all, and the
  caveat is no longer that a stable number might be imprecise but that the number
  is not stable. The two non-zero seeds do sit near 1/20 000, and
  `docs/maboss_estimator_semantics.md` records why that proximity is not
  provenance — nothing in the estimator counts paths, so this analysis does
  **not** read them as a count of one trajectory.

  **No quantitative claim is made about this difference, in either direction.**
  Two criteria were tried and the run artifact refutes both: a binomial standard
  error assumes independent trajectory draws, and treating `1/20000` as the
  smallest representable value assumes the marginal is a count — yet
  `OUT_STROMAL_DECIDUALIZED = 0.04054164922510266` is no multiple of `1/20000`,
  so MaBoSS reports ensemble probabilities rather than counting trajectories.
  This repository has **no validated characterisation of these estimates'
  sampling behaviour**, so asserting that 0.000020 against 0.000000 is resolvable,
  or that it is not, would be unfounded. The value is recorded; nothing is
  concluded from its size. **R43a's non-assessability rests on horizon
  instability alone, not on the regimen** -- the executed chain now matches the
  recorded one, which `regimen_fidelity` in
  `docs/concordance/concordance_table.tsv` states for this row. What is solid is
  the 4000× horizon gap itself, which does not depend on this count.

### Not a structural falsification — a magnitude failure (the regimen is now repaired)

An earlier revision of this analysis classified the mifepristone residual as a
**structural falsification**, on the argument that
`E_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE` (likewise `S_PGR`) makes
`OUT_STABLE_ADHESION` false in all 524,288 assignments whenever
`IN_MIFEPRISTONE` is set, so the observed 1/8 had zero likelihood and no
parameter could rescue it.

**That argument is wrong, and this repository's own run artifact refutes it.**
The enumeration establishes a property of the Boolean *target function* at its
fixed point. MaBoSS simulates asynchronous stochastic dynamics, and the observable
at a finite horizon is not the target function: at the declared horizon the same
mifepristone arm records a seed-averaged `OUT_STABLE_ADHESION = 0.000020` and is
non-zero in three of its five seeds, transient occupancy carried in from the
hormone-conditioned state. A finite-horizon probability is
therefore not zero, and it depends on rates, initial states and the horizon —
none of which the Boolean enumeration constrains. Claiming zero likelihood would
need a proof over all of those, and there isn't one.

So `structural_falsification` is an **empty class** in this analysis, kept in the
vocabulary so its emptiness is visible.

**This withdraws only the mifepristone claim.** The repository records one other,
unrelated structural falsification — that the model cannot express the observed
IGFBP-1-before-PRL onset order, because `S_IGFBP1` and `S_PRL` share one Boolean
rule, one initial state and one (default) transition rate, so their onset
distributions are identical by construction and any difference the simulation
produces is a node-ordering artifact that runs the wrong way. That claim is about
*expressiveness*, not about a finite-horizon probability, and nothing here
disturbs it. It lives in
[`results_reproducibility_matrix.md`](results_reproducibility_matrix.md) and
`OM-016` rather than in a TSV verdict, so this table's `concordance_class` column
does not count it: R12c, the row that carries the PRL observation, is
`not_assessable_with_current_data` for a different reason (no directional verdict
is licensed for PRL at all).

The accurate, weaker statement about mifepristone is:

* the **logical fixed point** under sustained mifepristone is 0, and that part is
  proved rather than sampled: the network is a DAG over 19 free variables, and
  exhaustive enumeration over all 2¹⁹ = 524,288 assignments shows
  `OUT_STABLE_ADHESION` false at the fixed point in every one of the 262,144 with
  `IN_MIFEPRISTONE` set. That is a statement about *t → ∞*;
* the reported numbers are read at **finite** horizons, and the fixed-point result
  does not carry to them. At the **declared** horizon the repaired arm records a
  mean of 2.0×10⁻⁵ across seeds 1–5 with an across-seed spread of 2.5×10⁻⁵ —
  a spread the size of the value, including exact zeros — so there is no stable
  declared-horizon number to compare against 0.125 at all (that is why R43a is
  not assessable). Before the wiring repair this arm reported exactly 5×10⁻⁵ in
  all five seeds; that apparent stability was an artifact of the bypassed
  lineage, and its coincidence with 1/20000 is the origin of the withdrawn
  "one trajectory in 20,000" reading (see
  `docs/maboss_estimator_semantics.md`). At the
  **converged** horizon (`converged_phase_horizon = 25.0` per phase) the run
  records `0.0` in 5/5 seeds at 20 000 trajectories. That is an observation about
  those runs, not a demonstration that the finite-horizon support *is* {0};
* either way this is a **magnitude failure on the held-out arm**, and it is a
  failure of the complete-antagonism *encoding* rather than of the Boolean model
  class. A partial-antagonism encoding sits inside the class and would not fail
  this way.

**The simulated regimen WAS not the experiment's regimen. It now is.** The
executed chain for the mifepristone arm is

```
basal_maternal -> e2_primed_maternal -> hormone_treated_maternal
    -> hormone_treated_mifepristone
    -> adhesion_challenge_hormone_treated_mifepristone
```

so the embryo challenge is seeded from the terminal joint state of the maternal
mifepristone phase, and mifepristone has acted on maternal tissue before any
embryo is present. That is what `SOFIA-HT-002` and
`context/adoc-paper-and-readout-context.md` record: 10 µM mifepristone for
**24 h after** the six-day hormone protocol.

Until 2026-09-13 the chain omitted `hormone_treated_mifepristone` and the
challenge was seeded from `hormone_treated_maternal`, so the drug switched on
*simultaneously with the embryo*. The paragraphs below record that defect and its
repair, because two separate revisions described it wrongly and the corrections
are worth keeping.

> **Correction, 2026-09-12.** Earlier revisions of this section, of
> `src/dt_adoc/concordance/build.py` and of the `regimen_fidelity` column said
> the maternal protocol suite "has no mifepristone phase at all" and that
> "`config/protocols.yaml` has no maternal mifepristone phase". **Both are
> false and are withdrawn.** `config/protocols.yaml` declares
> `hormone_treated_mifepristone` — a 24 h maternal mifepristone phase — in the
> `adoc-core-v0.1.0` family, where it is correctly chained
> `hormone_treated_mifepristone -> adhesion_challenge_hormone_treated_mifepristone`.
> The superset clone layer in `src/dt_adoc/protocols/conditions.py` imports that
> protocol into `adoc-literature-superset-v0.4.0` and rewires it onto
> `hormone_treated_maternal`, and
> `models/superset/adoc-literature-superset-v0.4.0/conditions/hormone_treated_mifepristone.cfg`
> exists, so the phase is fully executable in the version this analysis runs.
>
> The defect was **wiring, not absence**: the phase was *orphaned*. Nothing
> declared `continuation_from: hormone_treated_mifepristone`, so the executed
> chain bypassed it. The conclusion at the time was unchanged — the simulated arm
> was not the experiment's arm and R43a stayed not assessable — but the reason
> had been wrong, and a reader inspecting `config/protocols.yaml` directly would
> have reached the opposite conclusion from the core-family rows.
>
> **Superseded 2026-09-13: the wiring is repaired.** The chain is derived from
> the resolved protocol graph by `build._regimen_mismatch` rather than typed, and
> that function now raises if the repair is ever REVERTED — the tripwire it
> carried for the repair having been made has fired and been replaced by its
> mirror image. `MifepristoneArmLineageIsPinned` asserts the repaired chain, that
> the maternal phase is executable and consumed, and that the archived families
> are untouched.

This defect in the protocol wiring is **now REPAIRED** (2026-09-13). It was left
standing by the analysis that found it, on the grounds that rewiring a
continuation changes what a held-out validation arm simulates and that the same
gap affected the other maternal perturbation arms — so the repair was made as one
coherent decision across the whole suite rather than piecemeal.

Stated exactly, because a previous revision of this paragraph called
`hormone_treated_anti_spp1` orphaned, which was **false and withdrawn**;
`AllMaternalPerturbationWiringIsPinned` in
`tests/integration/test_concordance_runtime.py` pins the table before and after:

| maternal phase | orphaned before? | its challenge continued from | now continues from | runnable? |
|---|---|---|---|---|
| `hormone_treated_mifepristone` | yes | `hormone_treated_maternal` (bypass) | `hormone_treated_mifepristone` | yes |
| `hormone_treated_anti_spp1` | **no** — `washout` continued from it | `hormone_treated_maternal` (bypass) | `hormone_treated_anti_spp1` | yes |
| `hormone_treated_hand2_loss` | yes | `hormone_treated_maternal` (bypass) | `hormone_treated_hand2_loss` | yes |
| `washout` | yes | *(has no challenge of its own)* | — | **now yes**: superset `.cfg` is emitted |

The shared defect was the **bypass** across the three named perturbation
challenges: each was seeded from `hormone_treated_maternal` rather than from the
maternal phase whose name it carries, so the perturbation switched on at the same
instant as the embryo. `washout` was not one of them — it has no challenge of its
own — and its problem was different and worse: `adhesion_challenge_washout`
continued from the *anti-SPP1 challenge*, a challenge seeded from a challenge,
and `washout` itself was an orphan whose superset condition `.cfg` was never
emitted, so it resolved but could not run. Both are fixed:
`adhesion_challenge_washout` now continues from `washout`, and `washout.cfg` is
emitted.

Two properties of the repair are worth recording because they bound it.

**Scope.** The archived `adoc-core-v0.1.0` and `adoc-literature-v0.2.0` families
are deliberately untouched — editing them would silently change what a published
model version simulates. The repair lives in the superset clone layer, which now
overrides the `continuation_from` it used to inherit from v0.2.0. The unperturbed
comparator `adhesion_challenge_hormone_treated` is deliberately **not** rewired:
`hormone_treated_maternal` is genuinely its parent.

**`washout` is a no-op at a converged horizon, and that is honest rather than a
bug.** Its input state is byte-identical to `hormone_treated_maternal` — the core
protocol's own step note says it "reverts to the matched HT maternal input
state" — so what distinguishes it is only its continuation. Since the network is
a DAG over its free variables, each phase has a unique fixed point under a
sustained input assignment, so at convergence `washout` must equal
`hormone_treated`. Any difference between them is a finite-horizon transient and
this arm can only ever be read as one.

Which comparisons the mismatch invalidates is settled by evidence, not by
argument (`tests/integration/test_concordance_runtime.py`):

- **The recorded phase ordering is now what actually runs, and it gives the same
  converged answer.** This was first established as a counterfactual, by building
  the bypassed phase at run time. It is now measured directly against the
  pre-repair chain: the converged endpoint is `0.0` on **both** chains across
  seeds 1–5 at 20 000 trajectories, which supersedes the original 3-seed,
  2 000-trajectory evidence. The repair therefore does not move R43b, and R43b's
  held-out direction agreement and magnitude disagreement survive it with no
  regimen caveat attached. What is reproduced is the ordering and the perturbation, **not the
  regimen**: the counterfactual runs at `CONVERGED_PHASE_HORIZON = 25.0`, which
  `simulate.py` defines as dimensionless MaBoSS relative time and explicitly
  "never a day count", so nothing here represents 24 h, and this model carries no
  mapping from simulated time to physical time. Nothing is written:
  `config/protocols.yaml` stays untouched. Nor is any single artifact the
  culprit, and the runtime test pins the split rather than arguing it: the
  committed YAML declares this challenge twice and disagrees with itself — the
  `adoc-core-v0.1.0` row wires it to `hormone_treated_mifepristone` correctly,
  the `adoc-literature-v0.2.0` row wires it to `hormone_treated_maternal` — and
  the superset clone layer in `src/dt_adoc/protocols/conditions.py` inherits that
  second value verbatim while filtering out the core row that would correct it.
  The bypassing wiring is committed; what the clone layer adds is that nothing
  overrides it.
- **And the converged endpoint was unchanged under every other lineage tried.**
  Run from the declared lineage, from the challenge protocol alone, or from basal
  only, it is `0.0` in each of those three cases. The fixed-point argument
  explains why — each phase runs to its logical fixed point and the network is a
  DAG over its free variables, so the fixed point under a sustained input
  assignment is unique and independent of the starting state — but that argument
  is about the *asymptotic* fixed point, while these are finite-horizon runs, so
  it predicts the observation rather than proving it.

  So two different things hold, and they are not the same strength. The
  **asymptotic** endpoint provably does not depend on the lineage. The
  **reported, finite-horizon** converged value is `0.0` on the repaired lineage
  in 5/5 seeds (`docs/concordance/run_settings.json`), and equals the value on
  the pre-repair lineage in every run of
  `test_the_repair_leaves_the_converged_endpoint_unmoved` (3 seeds × 2000
  trajectories). Note what the second comparison is and is not: the maternal
  mifepristone phase is now IN the executed lineage, so the pre-repair chain is
  reconstructed explicitly as a legacy counterfactual, not the other way round.
  Both results are bounded to the runs performed, since fixed seeds give
  reproducibility, not Monte Carlo stability — five seeds is not a Monte-Carlo
  stability characterisation. The fixed-point value does not carry to finite
  horizons: this same arm reads a nonzero 5×10⁻⁵ at the declared horizon and
  `0.0` at the converged horizon, on one and the same lineage, so that figure
  measures horizon-dependence and is not evidence about lineage. Nothing in this
  repository compares declared-horizon values across lineages at all: `_run_from`
  in the runtime test pins `phase_horizon=CONVERGED_PHASE_HORIZON` for every
  lineage it tries, and the two `mifepristone` arms in `run_settings.json` share
  one lineage and differ only in horizon. So finite-horizon lineage-invariance is
  neither shown nor refuted here — away from the converged horizon it is simply
  untested. On the evidence that does exist, its direction *and* its magnitude
  failure both survive the mismatch: the observed 0.125 is ~2500× above the
  largest value this arm produces at any horizon tested.
- **The declared horizon reads far from that fixed point.** For the unperturbed
  arm the declared readout is orders of magnitude below its converged value, which
  is what the test asserts. That, and only that, is demonstrated here: the test
  varies the horizon, not the starting lineage. An earlier revision of this
  sentence went on to assert that the transient's size therefore *depends on the
  state the challenge phase began in* — plausible, and what the bypassed maternal
  phase would set, but **not demonstrated, and withdrawn**; the paragraph below
  then disclaimed the same dependence it had just asserted.

  **That dependence is not separately demonstrated, and the analysis does not
  claim it is.** Three successive revisions each tried to say more and each was
  wrong, so the claim is abandoned rather than narrowed again. The first asserted
  a demonstrated lineage-sensitivity on one-trajectory grounds. The second
  asserted the chained/unchained difference was quantitatively unresolvable, via
  a binomial standard error and then a `1/trajectory_count` resolution model. The
  third committed a probe measuring the difference and drew a mechanism from it —
  first asserting a weighted-mixture explanation, then claiming to have refuted
  it. **All are withdrawn.**

  The last of those is worth recording because it shows why this section now says
  nothing. The probe reported the continuation support entering the challenge and
  its probability mass, and neither quantity could bear the weight put on it:
  `project_joint_distribution` renormalises the retained distribution to 1, so
  the recorded mass was `1.0` by construction and measured nothing; and a support
  of a few thousand states is compatible with almost all the weight sitting on
  one of them, so it could not establish that a continuation was "mixed" either.
  Both conclusions drawn from it are void.

  **R43a is classed not assessable on horizon instability alone**, which needs
  no error model and no probe. The recorded phase ORDERING is now simulated —
  `hormone_treated_mifepristone` is in the executed lineage — so the old
  regimen-mismatch explanation is withdrawn and must not be reintroduced. What
  remains is that the declared readout is demonstrably pre-convergence and has no
  stable value there: on the repaired lineage at 20 000 trajectories it reads
  `0.0`, `2.5×10⁻⁷`, `0.0`, `5.03×10⁻⁵`, `5.03×10⁻⁵` across seeds 1–5
  (`docs/concordance/run_settings.json`) — a spread the size of the value itself,
  including exact zeros. Comparing that against an observed `1/8 = 0.125` would
  not be meaningful.

  The converged endpoint, by contrast, is stable in every run performed: `0.0` in
  5/5 seeds at 20 000 trajectories on the repaired lineage, and equal to the
  pre-repair lineage at 3 seeds × 2000 in
  `test_the_repair_leaves_the_converged_endpoint_unmoved`. That asymmetry —
  declared-horizon instability against converged invariance — is the whole basis
  of the classification. It is bounded to those runs: fixed seeds give
  reproducibility, not Monte Carlo stability, and five seeds characterise
  nothing. One caveat on physical time survives the repair unchanged: the phase
  ordering is simulated, but its dimensionless duration is not 24 h, because this
  model carries no mapping from simulated to physical time. The computational provenance of the non-`1/20000`
  probabilities remains **unestablished**, and establishing it needs
  MaBoSS/cmaboss output semantics read directly rather than inferred from output
  values. That is Phase B work and is not attempted here.

Both statements are asserted under test, so if a rule change ever breaks the
fixed-point argument the classification fails loudly instead of drifting.

### An honest weakening of the hold-out claim

The existing narrative calls mifepristone "the only genuinely held-out
comparison". That is too strong, and independent review caught it. Only the
**magnitude** is held out: `SOFIA-ADH-003` (the 1/8 outcome) has
`role=validation_if_held_out` and the hold-out is enforced in code
(`objectives.py` sums only `roles=('calibration',)`). The **direction** is not an
independent prediction — both `IN_MIFEPRISTONE ⊣ E_PGR` (LE002) and
`IN_MIFEPRISTONE ⊣ S_PGR` (LE038) were constructed citing `SOFIA-HT-002`, the
same study's own methods section. A reduction under mifepristone was guaranteed
by construction.

Worth recording as an open gap: **`SOFIA-HT-002` has no entry in
`config/evidence_roles.yaml` at all.** The evidence register's own note on that
row — *"Pre-register whether this row defines a perturbation or remains held
out"* — was never closed.

---

## What generates the predictions

The figure's panel C draws the model's dependency graph **quotiented by Boolean
function equivalence**, because the raw carrying path for the adhesion endpoint
is 35 nodes and drawing all of them would imply 35 independent mechanisms.

The model has **59 nodes implementing 35 distinct Boolean functions**. Three
collapses dominate the ADOC readouts:

* `E_PGR = E_IHH = S_PGR = S_NR2F2 = S_BMP2` — **one variable**. The entire
  epithelial→stromal IHH → COUP-TFII → BMP2 axis, which is the mechanism the
  paper's Fig. 3G CellChat result is about, is indistinguishable from
  progesterone itself. No comparison against that figure can discriminate them.
* `E_SECRETORY_STATE = E_PAEP = E_PC6 = E_DAG1_CLEAVED = E_MUC1_SLEX = E_HBEGF =
  E_SPP1_EXPR = E_ITGAVB3_5 = E_ANXA2_ACTIN` — **nine nodes, one variable**, and
  one of them is a measured node.
* `S_DECIDUALIZED = S_PRL = S_IGFBP1 = S_SPP1 = S_TAZ_ECM =
  OUT_STROMAL_DECIDUALIZED` — **six nodes, one variable**, again containing a
  measured node. PAEP, IGFBP-1 and PRL are therefore **not three independent
  successes**; they are two.

Two further structural facts bound what the mechanism can claim:

* **The anti-adhesive arm cannot act, on either of its routes.** Both
  `X_ANTIADHESIVE_ROUTE ⊣ OUT_MATERNAL_ADHESION_COMPETENCE` and the three
  `{E_PODXL, E_DAG1_FULL, E_MUC1_BARRIER} ⊣ E_RECEPTIVE_SURFACE` vetoes are
  **never-binding inhibitions**: pinning them off changes no output in any
  enumerated state. PODXL, full-length DAG1 and the MUC1 barrier are modelled,
  cited, and unable to suppress either receptivity or adhesion. The figure draws
  both struck through. (The second one was found by the completeness check that
  compares the drawing against every dependency the model computes between the
  nodes drawn — an earlier revision of the panel omitted it along with six other
  real dependencies.)
* **11 of the 52 nodes in the adhesion cone are phenotype-inert** — they cannot
  change any reported output under any clamping.

### The prediction reduces to three inputs and two typed-in numbers

Exhaustively, `OUT_STABLE_ADHESION` depends on 15 of the 19 free variables. But
in the three ADOC arms every non-protocol free variable except the relays is OFF,
and the endpoint reduces to

```
OUT_STABLE_ADHESION
  = (IN_E2 and IN_PROGESTIN and IN_cAMP and not IN_MIFEPRISTONE
     and IN_EMBRYO_PRESENT and IN_TROPHECTODERM_COMPETENT and IN_EMBRYO_CONTACT)
    and (X_INTERFACE_SPP1_RELAY or X_INTERFACE_REDUNDANT_RELAY)
```

**This is an identifiability statement, not a model comparison.** For these three
arms the 59-node mechanistic model is functionally a one-bit hormone gate scaled
by one constant. A deliberately trivial baseline would reproduce the same
observed ordering, so the three-arm adhesion readout **cannot discriminate**
between the mechanistic twin and a one-parameter model.

It does not follow that the twin is no better than a baseline, and this document
does not claim that: with three arms, one ordering and two of the three arms
fitted, no comparison here has the resolving power to rank two models. The
correct conclusion is that **the current readout set is uninformative about the
mechanism**, which is a statement about the experiment, not about the twin. What
would change that is named in "Most valuable next measurements" below.

---

## The paper's final single-cell annotations

Eleven rows (`R17`–`R27`) are blocked on this, so the claim was verified rather
than repeated.

`pixi run audit-scrna-object` streams the local
`combined-dataset-patient-integration.rds` (3.46 GB gzip, ~5.17 GB decompressed)
without R or Seurat and records what it holds. Result
(`docs/concordance/scrna_object_audit.json`):

* `meta.data` columns, complete: `orig.ident`, `nCount_RNA`, `nFeature_RNA`,
  `sample_id`, `patient_id`, `runs`, `lib_type`, `seq_time`, `tissue`,
  `patient_n`, `mitoRatio`, `scDblFinder_RNA.score`, `integrationCovariates`.
* `active.ident` levels: the six **samples** — `SZ09/SZ10/SZ25 × TE_CNT/TE_HT` —
  which is what an unclustered object identifies cells by.
* **No** `seurat_clusters`, no `*_snn_res.*`, no cell-type or annotation column,
  and **no** `FindClusters` or `FindNeighbors` anywhere in the file — so no
  clustering call was ever recorded in the object's command history.

So the object is a **post-integration, pre-clustering, pre-annotation**
intermediate: 61,843 cells against the manuscript's final 28,212-cell,
seven-population analysis. The repository's existing statement was **correct, not
stale**. What changed is that it is now reproducible and checkable instead of
being prose from a one-off audit; the audit records every token it searched for,
because an absence claim is only checkable if its scope is recorded.

A search of this machine found no barcode-to-label table for this study.

**Nothing was reconstructed, and that is deliberate.** Clustering and annotating
these cells would produce *my* populations, and comparing the model to them while
labelling the result concordance with the paper's Fig. 3 would be a comparison
against my own reanalysis presented as a comparison against published results.
The compartment split the model needs (`E_*` versus `S_*`) is exactly what the
object lacks, so there is no defensible partial step either.

**What would unblock these 11 rows**, in order of preference:

1. The final 28,212-cell annotated Seurat object.
2. A barcode → final-population crosswalk keyed on the barcodes this object
   already carries (`SZ10TE_CNT_AAACCCAAGAGTGACC-1` and so on). This is
   sufficient: the local object holds the expression, and the labels are the only
   missing piece.
3. Failing both, the exact QC, integration and clustering parameters used to get
   from 61,843 to 28,212 cells, so a reconstruction could at least be compared
   against the published population sizes before being trusted.

Even with the annotations, the resulting comparisons would be **donor-aware and
compartment-aware summaries over three donors**, would not treat cells as
biological replicates, and would not equate transcript abundance with
`P(node = ON)` — they would constrain direction of a latent state, not its
magnitude.

---

## What is responsible for what

**Strongest successful predictions** rest on one mechanism:
`IN_PROGESTIN → E_PGR/S_PGR → {E_SECRETORY_STATE, S_DECIDUALIZED}`, together with
`IN_E2` for the epithelial arm and `IN_cAMP → S_PKA` for the stromal arm. Every
reproduced direction — the adhesion ordering, PAEP up, IGFBP-1 up — is generated
by that single progesterone-dependent gate (PRL is not among them; see above). Nothing downstream of it
contributes a direction that the gate does not already determine.

**Strongest failures** rest on assumptions, not on biology:

| Failure | Responsible structure |
|---|---|
| HT magnitude 0.820 vs observed 0.474 | the two hand-set relay istates, 0.70 and 0.40; nothing else is graded |
| Mifepristone residual 1/8 missed by ~2500× | complete-antagonism encoding of `IN_MIFEPRISTONE ⊣ PGR`. The regimen no longer contributes: the maternal mifepristone phase is in the executed lineage, and the converged endpoint was unmoved by putting it there |
| Declared-horizon inversion of the held-out arm | `relative_duration` in `config/protocols.yaml` reading ~4000× before the fixed point |
| IGFBP-1-before-PRL onset order not represented | `S_PRL` and `S_IGFBP1` are the same Boolean function with the same default rates |
| Anti-adhesive biology contributes nothing | both of its vetoes never bind: `X_ANTIADHESIVE_ROUTE ⊣ OUT_MATERNAL_ADHESION_COMPETENCE` and the three `⊣ E_RECEPTIVE_SURFACE` |

---

## Most valuable next measurements

Ranked by ability to discriminate between model variants that currently make
identical predictions.

1. **A graded mifepristone dose-response on adhesion.** The single highest-value
   measurement. It directly tests the complete-antagonism encoding that produces
   the encoding responsible for the held-out magnitude failure, and it is the
   only measurement that can distinguish a full clamp from a partial one.
2. **Any readout that separates the five-node PGR alias class** — for instance
   IHH or BMP2 perturbation with an adhesion readout, rather than co-expression
   inference. Until something does, the paper's BMP/SPP1 communication result
   cannot constrain the model beyond progesterone.
3. **A perturbation of the anti-adhesive arm** (PODXL, MUC1) with an adhesion
   readout. The model says it cannot matter; that is a falsifiable prediction and
   nothing currently tests it.
4. **Time-resolved IGFBP-1 and PRL in the same chips, with chip identity
   retained.** The observed onset order is a real constraint the model cannot
   currently represent, and the existing workbook cannot supply it because the
   column-to-chip mapping is lost.
5. **The final scRNA annotations** (see above) — which unblock 11 rows at no
   experimental cost at all, and so are the cheapest item on this list.

---

## Boundaries this analysis holds

* Calibration agreement is not validation, and four of the nine engaged rows are
  calibration agreement.
* MaBoSS relative time is dimensionless. No horizon here is a day count.
* No concentration or signature score is compared numerically to a Boolean
  probability; no validated observation model exists to relate them.
* The adhesion denominators are **embryos**, not donors. The secreted-protein
  denominators are chips or workbook column positions, and chips are not
  independent biological replicates.
* Three donors. No generalisation claim.
* Every plotted quantity traces to `figure_source_data.tsv` and from there to
  `run_settings.json` or to `config/calibration.yaml`.
* No uncertainty statement is made about the simulated values beyond recording
  the across-seed spread as a diagnostic. This repository has no validated
  characterisation of these estimates' sampling behaviour, so that quantity is
  not used to conclude anything and does not bound model or observation
  uncertainty. A binomial plug-in `sqrt(p(1-p)/n)` was recorded alongside it
  until 2026-09-14 and is **withdrawn**: a MaBoSS node value is accumulated
  dwell time divided by `(tick x trajectories)`, so the per-trajectory quantity
  is a continuous occupancy and not an indicator, which makes the plug-in the
  wrong variance family rather than a loose estimate
  (`docs/maboss_estimator_semantics.md`, section 3d). The `simulated_trajectory_se`
  column and the `node_trajectory_se` record are removed for that reason. The
  **observed** adhesion counts keep their Wilson 95% intervals, which are correct
  for counting embryos and which this withdrawal does not touch.
