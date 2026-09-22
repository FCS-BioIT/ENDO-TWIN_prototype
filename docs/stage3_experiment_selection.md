# Stage 3 — the one prospective experiment that most reduces maternal ambiguity

Status: **FROZEN prospective design, 2026-09-17.** Both owner decisions are
adjudicated (§9) and the design in §12 is fixed: it may be executed or
superseded, but not edited in place. Analysis only. No executable file changes:
`network.bnd`, every condition `.cfg`, `config/calibration.yaml` and
`config/perturbations.yaml` are untouched, no rule or rate is adopted, and no
quantitative objective is created.

Computed companion: [`experiments/stage3_experiment_design.md`](experiments/stage3_experiment_design.md)
and its TSV, regenerated with `pixi run build-stage3-design`. Every prediction
quoted here is read from that generated file, which conditions the committed
`adoc-literature-superset-v0.4.0` network — and each competing mechanism class's
in-memory rule substitution — on each candidate experiment's controlled inputs.

**Review status.** Two different things are true and must not be merged.

* **No harness-native independent Codex verdict was available during the gate
  rounds on this change**, so the harness gate's own record is same-vendor
  throughout. `aih scope` reports every call to the Codex reviewer failing on
  `quota` — 4 discovery, 5 final, 10 verify, zero verdicts — with the last
  harness-native cross-vendor review dated **2026-09-14T08:51:27Z**. Every
  verdict the gate recorded since came from the same-vendor Claude stand-in and
  carries `recorded_degraded = true`.
* **This repository is nevertheless under ongoing external cross-vendor
  review**, outside the session: OpenAI GPT-5.6 Sol, at extra-high effort,
  reading the pushed GitHub tree. It has reviewed `5a1044b` and `c78b506` so
  far, and §10 records each round with its disposition. This is genuine
  cross-vendor evidence and it is **not** a harness verdict — the gate never
  sees it, so it neither clears a round nor spends one.

Neither amounts to acceptance. The harness still reads `accepted = false`;
`aih accept` records *human* acceptance and is the owner's alone; and the
harness has no command that imports an external verdict, which is why §10 is a
record rather than a gate entry. The internal adversarial pass in §8 is
same-vendor and is labelled as such throughout.

---

## 1. Current binding uncertainties

**Two counts that are not the same set.** *Free* is a property of the rules —
every node whose rule is its own name. *Latent* is a property of the design — the
free variables no arm assigns, whose per-unit value is unknown and is
marginalised over. This document and the generated files use the two words only
in those senses, and **the decomposition is counted in table A** rather than
written out here: an earlier version of this paragraph did write it out, and got
both components wrong while the total happened to survive.

Verified against the repository, not inherited, and **not transcribed**: the
counts and the alias classes are table A of
[`experiments/stage3_decision_tables.md`](experiments/stage3_decision_tables.md),
generated from the committed network. Read them there.

Only four of those collapses are *binding* for choosing an experiment, in the
sense that a feasible measurement could move them.

**U1 — The hormone cocktail is one lump, and it contains the two measured
nodes.** `OM-001`'s own `claim_ceiling` states it: "Because the design has no
single-agent arm, no effect may be attributed to MPA, cAMP or XAV939
individually." The committed model asserts a specific factorisation of that lump
— `IN_E2` into the epithelium via `E_SECRETORY_STATE`, `IN_PROGESTIN` into both
compartments via PGR, `IN_cAMP` into the stroma via `S_PKA`, `IN_XAV939` into
nothing — and **no arm tests any part of it.** The 9-member epithelial class
contains `E_PAEP`, the only `active_constraint`; the 6-member stromal class
contains `S_IGFBP1`, the only `active_diagnostic`. `docs/design_alias_note.md`
reached the same place from a different computation: of 112 candidate fifth
arms, 8 pull two measured nodes into different classes, and those 8 are exactly
two interventions across four backgrounds each — **minus-E2** (design-class gain
3) and **minus-cAMP** (gain 2). Nothing else scores at all, HAND2 loss included,
although HAND2 loss leads on raw class gain (+5).

**U1 is sharper than "untested".** `OM-001` records PAEP at **10,165–25,470
pg/mL under E2-only priming** against a 3 pg/mL assay sensitivity, and calls
`E_PAEP` OFF there. The same `claim_ceiling` admits the binarisation threshold is
"implicit and unrecorded" and must lie in (25,470, 178,073] pg/mL — a window
whose lower bound is the largest E2-only observation and whose upper bound is
OM-001's rounding of the smallest full-cocktail one, which is 178,072.464 pg/mL
in `input_tables/adoc_secreted_proteins.tsv`. The committed conjunction `E_SECRETORY_STATE = IN_E2
and E_PGR` is therefore consistent with the data *because a threshold was placed
where it had to be*, not because an arm tested it.

**U2 — Hedgehog reception (`GAP-014`).** `E_PGR = E_IHH = S_PGR = S_NR2F2 =
S_BMP2` is one Boolean function, so the epithelium→stroma relay the whole
two-channel chip exists to represent is **structurally vacuous**: `S_BMP2 =
(S_PGR and S_PKA) or S_NR2F2` reduces to `S_PGR`, and deleting the relay changes
no downstream prediction. Whether reception is required is untested in human.

**U3 — The epithelial receptivity trio.** `E_LIF = E_GP130_STAT3 = E_CD98_CD9`
is one function; anti-LIF, STAT3 inhibition and CD98 knockdown are one
intervention. No member has any assay.

**U4 — PC6 enzyme versus DAG1 substrate.** `E_DAG1_CLEAVED = E_PC6` makes the
enzyme identical to its product, which REF-011 (Heng 2015) directly contradicts.
No member has any assay.

**Not binding, and why.** The PRL/IGFBP-1 kinetic axis stays closed as Gate 3a
left it: the blocker is an unregistered binarisation threshold and a *lost*
column-to-chip mapping, not a rule. Adhesion stays `diagnostic_ordinal`; nothing
below fits an attachment fraction. The Gate-3b interface/penetrance fork is not
touched. Three declared inputs are read by **no rule in the committed network** —
`IN_XAV939`, `IN_HCG` and `IN_EMBRYO_CONDITIONED_SIGNAL`, per table A — so the
model predicts each does nothing. Only the first is *administered*: the protocol
sets `IN_XAV939` TRUE in every hormone-treated condition, while the other two are
never turned on in any arm. That is what makes XAV939 a finding rather than a
fork (§6). It is also why **adding hCG separates nothing measurable**: no rule
reads it, so the addition contributes nothing in either background. That is a
statement about the hCG *addition*, not about both hCG arms —
`add_hcg_on_e2` does separate the `SEC` fork on `E_PAEP`, and it does so
entirely because its background is the E2-only phase, which `observe_e2_primed`
already provides for free.

---

## 2. Candidate comparison

Six mechanism forks and sixteen candidate experiments — two observation-only,
thirteen single-intervention, one deliberately two-intervention — were evaluated
programmatically.

**The comparison table is table B of
[`experiments/stage3_decision_tables.md`](experiments/stage3_decision_tables.md)
and is not reproduced here.** Its computed columns come from the evaluation; its
protocol, assay and feasibility columns are the curated declarations on each
`Experiment`. Nothing in it is retyped, which is the point: review round after
round on this document found one class of defect above all others — a
hand-written statement about a computed cell that the artifact contradicted —
and a table nobody retypes cannot produce another. The count of rounds is
deliberately not given here; it is a number that goes stale for the same reason
everything else did.

One rule governs what that table reports, applied by the generator rather than by
me: a fork appears only if the arm separates it on a readout that **exists**,
`usable_assay` or `mapped_composite` with the tier marked. A separation reachable
only at `no_assay` is a difference between two model states, and appears instead
in the `no_assay only` column of
[`experiments/stage3_experiment_design.md`](experiments/stage3_experiment_design.md)
and in its pair index. The whole **CD98** axis falls there, in **every** arm of
the catalogue: `E_CD98_CD9` has no assay, so that axis is separable in many arms
and decidable in none.

Five results in table B overturn a previously recorded position, and each is
computed rather than asserted:

* **anti-LIF + pSTAT3 separates nothing.** `GP130-a` (`E_GP130_STAT3 = E_LIF`)
  and `GP130-b` (`E_LIF or X_IL11`) agree in every arm where IL-11 is not
  supplied, so neutralising LIF cannot tell them apart. The separation needs
  supplied IL-11, and an *opposite* separation needs anti-LIF **and** IL-11
  together — two perturbations. That is the design the project prefers to avoid.
  And the readout the fork is *about* — pSTAT3, i.e. `E_GP130_STAT3` — is
  `no_assay`; the separation itself is reachable only at
  `mapped_composite_not_validating`, on `OUT_EPITHELIAL_RECEPTIVE`, which the
  map says cannot validate its node.
* **Surface CD98 under E2-only cannot close the CD98 axis.** The generated
  pair index shows `CD98-c vs CD98-x` — the E2-induction reading against the
  reading in which CD98 is simply constitutive — is separated by **`dropout_e2`
  and by nothing else**. Under E2-only, with or without hCG, `CD98-c` and
  `CD98-x` predict the same thing. Gate 3a §4 ranked this measurement first; on
  a presence/absence surface readout in that arm it cannot exclude the most
  likely explanation of a positive result. The broader fact is worse for the
  axis: `E_CD98_CD9` has no assay, so **every** CD98 pair is unmeasurable in
  **every** arm of the catalogue. It is separable in many and decidable in none.
* **BMP receptor inhibition separates nothing.** It clamps `S_BMP2`, which the
  committed rules already make necessary for `S_DECIDUALIZED`; every class
  predicts the same loss. It confirms a rule rather than choosing between rules.
* **PC6 knockdown separates nothing**; only the cleavage-resistant substrate
  does, and only at `no_assay` and `mapped_composite` nodes.
* **anti-SPP1 propagates to no maternal node at all.** This is the computed form
  of what `identifiability.py` already reports as
  `set_alone_no_shared_readout`, and it closes the question the Gate-3a audit
  left as a withdrawal of an earlier ranking.

### Mechanism classes, and where each one comes from

Curated classes cite their row in
`context/literature/reviews/gate3_candidate_variants_2026-09-16.tsv`; classes
introduced by this analysis say so.

**`role` and prior support are two different facts, and conflating them is a
mistake this artifact made twice.** `role` records what an outcome favouring the
class would *license*: `adoptable` means a rule change directly, `confounder only`
means opening an evidence gap and nothing else. It is **not** a claim that the
repository already supports the class, and an `adoptable` class may rest on
nothing yet — `SEC-b` does. The support column below says so per class, and
`none` is an admissible entry.

Every class, with its rule, role, prior support and provenance, is **table D**
of [`experiments/stage3_decision_tables.md`](experiments/stage3_decision_tables.md).
It is not reproduced here. An earlier version kept the four `SEC` rows by hand
"because §5 argues from them", and claimed a test pinned them; the test compared
the class ids and, for support, only `none` against non-`none`, so a non-`none`
entry could have drifted to a different non-`none` claim unnoticed. Generating
the rows removes the question instead of strengthening the comparison, which is
the same move the rest of this document already made.

`GP130-b`, `CD98-b`, `CD98-c` and `PC6-b` are the curated variants, reused
unchanged.

---

## 3. Recommended experiment

> **Cocktail minus E2: run days 2–6 with MPA + cAMP + XAV939 after the normal
> E2-only priming phase, and read PAEP from the top outlet and IGFBP-1 and PRL
> from the bottom outlet.**

It dominates every other **intervention** on the dimensions that matter here.
It does not dominate everything, and saying that it does would be manufacturing
certainty: the zero-cost E2-only observation is on the Pareto frontier too, it
reaches one class pair `dropout_e2` cannot, and the honest relation between them
is complement, not rival. The two interventions closest to it lose on the
dimension each is supposed to win.

**Mechanisms separated.** More `SEC` class pairs on a usable assay than any
other candidate — the counts are table B and the pair index of
[`experiments/stage3_experiment_design.md`](experiments/stage3_experiment_design.md),
and are deliberately not restated here, because the last time they were they
went stale the moment the fork grew a class. The *structure* is what the
recommendation rests on and it is stable: this arm separates the committed rule
from **three of its four rivals** — `SEC-b` and `SEC-c` on `E_PAEP`, `SEC-d` on
`S_IGFBP1`. The fourth is the honest limit, stated wherever the result is
interpreted: `SEC-a` against `SEC-e` is **not** among them, because the two
predict identically on both usable assays (§5, §7). The only other candidates reaching more than one pair on a usable
assay are the E2-only observation and its hCG variant, whose pairs the index
carries — both the membership and the count — and which this document
deliberately does not restate. The structural fact is what matters and it does not move when the fork
grows: **every pair those arms reach has `SEC-c` on one side.** Those arms resolve exactly one bit, whether
`SEC-c` is in or out, and **cannot separate `SEC-a` from `SEC-b` or from
`SEC-d`** — which is the distinction that decides whether concurrent E2 is
required at all.

**Readouts.** `E_PAEP` and `S_IGFBP1` are the only two nodes the observation
layer can validate — `active_constraint` and `active_diagnostic` respectively —
and this is the only experiment whose separations land on **both**.

**Assay cost: zero.** PAEP, IGFBP-1 and PRL are the platform's three existing
ELISAs; `input_tables/adoc_secreted_proteins.tsv` contains nothing else. Every
other informative candidate requires a first-of-kind measurement class on this
platform: surface CD98 (cell-associated protein), pSTAT3 (lysate), α-DG-N
(shed-ectodomain ELISA), GLI1/PTCH1 (transcript).

**Intervention cost and risk: minimal.** One reagent omitted from an existing
medium. There is no drug, no construct, no antibody, and therefore no
target-engagement failure mode — the objection that forces the runner-up to buy
an extra assay.

**Robustness to the repository's worst measurement problem — on the epithelial
side.** The verdict there is a *band assignment*, not a threshold crossing, and
it does **not** transfer symmetrically to the stromal readout: IGFBP-1's day-0
and day-6 bands both contain exact zeros and so are not disjoint. §4's
pre-registration rule (ii) records that asymmetry and (iii) is what compensates
for it. The two PAEP bands already in hand
do not overlap and are separated about sevenfold: E2-only spans 10,165–25,470
pg/mL across 5 chips, full cocktail 178,072–585,609 pg/mL across 5 chips. Minus-E2
PAEP lands in one band or the other. This matters more than it may look: the
unregistered `E_PAEP` threshold is exactly what stops the current E2-only
observation settling even the one bit it reaches, and this design routes around
it instead of inheriting it.

**Informative under every outcome.** All four cells of the PAEP × IGFBP-1 table
license a distinct model action, and one of them falsifies the entire fork (§5).

**Why not the two candidates it does not dominate.**

*`observe_e2_primed` is cheaper, is not dominated, and is not a substitute.* It
costs nothing — the E2-only PAEP values are already held under OM-001 — and it
separates `SEC-b` from `SEC-c`, which `dropout_e2` cannot. Neither dominates the
other, and the two are complementary rather than competing, because they resolve
different bits: **every pair the E2-only arms reach has `SEC-c` on one side**, so
they decide whether `SEC-c` survives and nothing else, while `dropout_e2` decides
among the rest. It does separate `SEC-a` from `SEC-c`, so it can falsify the committed
rule — but only along that one axis, and what stops it doing so today is a
threshold rather than a missing measurement: the call is precisely whether
10,165–25,470 pg/mL is ON or OFF, and OM-001's `claim_ceiling` admits the
threshold deciding it is implicit and unrecorded. So it should be **registered,
not run**: fix the `E_PAEP` binarisation before the new arm is executed. Their
pair sets are complementary, and their union leaves **exactly one** pair
unreached by any arm in the catalogue at a readout that exists: `SEC-a vs
SEC-e`, the one §7 records as residual. That last statement is the one worth
carrying, because it is the design's limit rather than a count that moves when
the fork does; it is pinned by a test. That
registration is a prerequisite of the recommendation, not an alternative to it.

*`smo_antagonist` addresses a recorded gap and loses on confounding.* See §6.

---

## 3a. What evidence already in hand can settle, before new material is spent

The repository holds a curated single-cell layer, so the right question before
spending material is whether it already resolves any ambiguity that makes
`dropout_e2` rank first. **Tables E and F** of
[`experiments/stage3_decision_tables.md`](experiments/stage3_decision_tables.md)
compute the answer. It is no, and — following a second external review that
rejected an earlier, weaker version of this section — the reasons are now given
as facts about the *design* rather than as labels, and the invariance is proved
rather than asserted.

### Why the scRNA data cannot decide the fork that decides the recommendation

Not because its readouts are `construction`-role. That matters for independent
validation and it is recorded, but Stage 3 is choosing an experiment to
**calibrate an underidentified twin**, and construction-role data may legitimately
inform calibration so long as nothing later claims it as held-out validation. On
its own it would not settle anything.

The decisive reason is the deposited experiment's design. Derived from the
committed per-unit table, that object contains **two conditions, `CNT` and `HT`,
across three donors** — and `HT` moves E2, MPA, cAMP and XAV939 **together**. The
contrast that separates `SEC-a` from `SEC-b` is an E2 dropout against a matched
full cocktail. **That contrast is not in the data.** No detection quality, no
regulon score and no choice of unit creates it.

That also corrects how `IN_E2` and `IN_cAMP` should be read in table E. They
appear as `not_observable`, but they are experimenter-set: their values are known
from the protocol and never need recovering from RNA. The real limitation is
causal, not observational — `CNT` versus `HT` is a bundled intervention, so a
transcript programme that differs between them cannot be attributed to any single
component. That is **the same bundling `U1` records for the ADOC secretome, in
the same protocol**, and it is precisely why the recommended arm is a
single-component dropout.

### What no scRNA result can change, stated as the theorem it is

Table F proves a **conditional** invariance, and the heading says so because an
earlier one ("why no scRNA result could change the choice") claimed more than the
proof delivers. What is proved:

> Under the frozen v0.4 model and the current observation-activation policy, no
> scRNA finding can add or remove an arm from the set that separates a fork on an
> already-usable assay. Separately, the deposited scRNA design cannot resolve the
> `SEC` E2-dropout contrast at all, because that contrast is not in it.

That is narrower than "the preference is invariant", because preference here also
weighs which uncertainty stays credible, how many classes an arm separates,
target-engagement ambiguity, assay cost and robustness — and a strong scRNA
finding can move the *uncertainty set* without touching any `readout_tier`. The
steps:

1. **The ranking criterion is a readout tier, and the scRNA layer cannot set
   one.** An arm is preferred here for separating a fork on a readout that
   exists, and that tier is computed from `config/observation_model_map.tsv`
   alone. Every row of `config/scrna_observation_map.tsv` is `reported_only`,
   `provisional` or `rejected` — **none active** — so no scRNA finding promotes
   any node to `usable_assay`.
2. **The forks an AC04 result bears on are not decided at that tier.** `GP130`
   is decided at `mapped_composite_not_validating`, `CD98` at `no_assay`. Strong
   support for the `E_LIF`/`E_GP130_STAT3`/`E_CD98_CD9` aliasing leaves both
   where they are; strong contradiction makes both matter *more* and still leaves
   both where they are. A fork that matters more but still cannot be read does
   not make its arm more informative.
3. **The candidate set is therefore invariant** under both extremes: no arm can
   enter it, and none can leave.

**What that argument does and does not close, stated precisely.** It proves no
scRNA result can make a *non-candidate* arm preferred, because nothing can
promote a fork into the deciding tier. It does **not** by itself exclude
re-ordering *within* the candidate set, and one route deserves naming, because
the external reviewer raised `AC04` and the more relevant class is `AC03`.
`AC03` is `E_PGR`/`E_IHH`/`S_PGR`/`S_NR2F2`/`S_BMP2`, and a within-`HT`
divergence among them — a within-condition test, so the `CNT`/`HT` bundling bites
less — would bear on `HH`, which *is* a candidate fork and is the runner-up's.

That route still does not dethrone the recommendation, for reasons that are
about the design rather than the prior. Even granting `HH-b` outright,
`smo_antagonist` separates **one** class pair, on one outlet, and the committed
model predicts nothing propagates — so its null stays confounded with failed
target engagement and it still has to buy a GLI1/PTCH1 engagement assay.
`dropout_e2` separates the committed rule from three of its four rivals, across
both outlets, with no new assay and no engagement failure mode. No prior shift
reaches that gap. Four of the five `AC03` members also carry
`evidence_role = construction`, which does not forbid calibration use but does
mean such a result would inform rather than settle.

**So the focused expression analysis was not run, and this is why** — not because
`AGENTS.md` forbids it. It does not: it forbids loading the 2.9 GB object *merely
to test runtime availability*, and the KLF12 workstream deliberately used the same
object for a pre-specified analysis. An AC04 divergence test is admissible,
within-compartment, and scientifically interesting. It simply cannot change which
arm to run next, and running it to value a prospective experiment would be
answering a question whose answer is already fixed.

**What this does not claim.** It does not claim the analysis would be
uninteresting. Contradicting AC04 would be evidence that the epithelial
receptivity layer is mis-specified — a reason to *develop an assay* for it, which
is a different decision from which arm to run with the assays that exist, and a
good candidate for the unit after this one.

**Effect on the ranking: none, and that is the result.** No fork changed status.
The ambiguity that makes `dropout_e2` rank first is untouched by evidence in
hand, which is a positive reason to spend material on it.

---

## 4. Minimum implementation

**Intervention.** One arm. Days 0–2 unchanged (E2-only priming as in the current
protocol). Days 2–6: MPA 1 µM + cAMP 0.25 mM + XAV939 10 µM, **E2 omitted**.
Nothing else changes: same chip, same flow rate, same medium base, same
collection windows.

**Controls, all contemporaneous.** Historical chips must not be used as the
comparator; `OM-002` records 2 of 5 day-6 units reading exactly zero in both
outlets, which is more consistent with chip-level dropout than with secretion
ceasing, and a dropout that hits only the treated arm would be read as an effect.
So, on the same donors and the same run:

1. **Full cocktail** (E2 + MPA + cAMP + XAV939) — the ON reference band.
2. **E2-only, sampled at day 2** — the low reference band, and the sample that
   makes the PAEP call ordinal rather than threshold-based.
3. **Pre-cocktail baseline PAEP.** The repository holds **no** pre-cocktail PAEP
   row; IGFBP-1 and PRL have day-0 baselines and PAEP does not. Without it the
   model's Boolean `E_PAEP = 0` has no measured referent. Existing assay,
   existing timepoint, one extra aliquot.
4. **Compartment integrity, in both channels.** Phase-contrast confluence
   imaging at days 2, 4 and 6, epithelial **and** stromal. The epithelial case
   is the obvious one: four E2-free days could reduce PAEP by losing epithelium
   rather than by switching the secretory program off, and that failure mode
   mimics `SEC-a` exactly. The stromal case is less obvious and matters as
   much, because the only thing separating `SEC-a` from the confounder `SEC-d`
   is `S_IGFBP1` from the bottom outlet — so stromal loss over the same four
   days would read as IGFBP-1 OFF, which is the `SEC-d` signature. An earlier
   version of this list controlled only the epithelial side, leaving the arm's
   confounder-exclusion resting on an uncontrolled channel. Neither control is
   optional; see §8.

**Compartment and timing.** Top outlet (epithelial) for PAEP; bottom outlet
(stromal) for IGFBP-1 and PRL. Sample at the existing day-3 and day-6 windows.
Day 3 is retained because the day-6 bottom-outlet IGFBP-1 values in hand are not
uniformly the highest of the series — three of the five column positions read
lower at day 6 than at day 3 — and a single day-6 sample would inherit that risk.
Because `OM-002` records the column-to-chip mapping as **lost**, that is a
statement about positions in a sheet and not a within-unit trajectory; the new
arm should carry chip identity so its own day-3/day-6 comparison is paired.

**Assays.** PAEP, IGFBP-1 and PRL by the existing ELISAs. **Nothing else.**

**Replication.** Three donors, one chip per condition per donor — with one
question left open for the owner. Removing PRL's ability to rescue an
uninterpretable IGFBP-1 (rule (iii) above) means a unit with a day-6 zero now
returns `indeterminate` rather than ON, and the data in hand show that happening
in 2 of 5 units. A **technical duplicate of the `full cocktail` versus `minus
E2` pair** would protect the stromal call against exactly that, and it is worth
more than the PRL rescue was, because it addresses the dropout instead of
masking it. It is not adopted here: it costs chips, and whether that is
affordable is a material constraint this analysis cannot see. If only one
duplicate can be afforded, duplicate the minus-E2 arm, since the full-cocktail
band is already characterised by five chips in hand. State the
ceiling in the analysis plan before the run: `config/adoc_chip_donor_provenance.tsv`
and `SOFIA-COMM-005` establish that chips are not independent biological
replicates, so **no patient-level variance, standard error, confidence interval,
paired-donor test or personalization claim may be derived**. The decision table
is an ordinal band assignment per unit, reported per unit, with disagreement
between units reported as disagreement rather than averaged.

**Pre-registration, before the run.** (i) the `E_PAEP` band rule — minus-E2 is
called ON if it lies in or above the full-cocktail band, OFF if in or below the
E2-only band, and **indeterminate** otherwise, with indeterminate an admissible
result and not a tie to be broken; (ii) the same three-level rule for IGFBP-1
against its own day-0 and day-6 bands, **with the asymmetry stated rather than
assumed** — unlike PAEP's, those two bands are not disjoint, because both
contain exact zeros in the source table (day-0 `BOTTOM_2`; day-6 `BOTTOM_4` and
`BOTTOM_5`), and what separates them is the non-zero values, roughly
8,100–14,300 pg/mL at day 6 against 37.9–551.3 at day 0, while a dropout reads
zero in either; so the stromal call is weaker than the epithelial one by
construction, and (iii) is what carries that weight; (iii) **IGFBP-1 is the stromal decision variable and PRL is corroborative, not a
substitute.** The stromal call is ON when IGFBP-1 is in its ON band, OFF when it
is in its day-0 band, and **discordant/indeterminate** when IGFBP-1 is
uninterpretable — zero, or between bands — while PRL is convincingly ON. PRL is
reported alongside in every unit and a PRL/IGFBP-1 disagreement is recorded as a
finding about the assay or the biology, never resolved silently in favour of
whichever analyte is convenient.

An earlier version of this rule said the stromal call was ON if **either**
analyte was ON. That was wrong, and wrong in a way the repository's own record
forbids: `OM-002` makes IGFBP-1 the `active_diagnostic`, while `OM-006` places
PRL at `provisional` / `context_only` / `objective_treatment = not_used` and its
`exclusion_reason` ends "No numeric weight, ever." Letting PRL flip a stromal
call from OFF to ON gives it decisive weight — more than the activated
diagnostic has — and it would have changed the model-class assignment, since
table C defines the stromal prediction through `S_IGFBP1` alone. The convenience
it bought was covering the known 2-of-5 day-6 dropout; the honest cost of
removing it is that those units now return `indeterminate`, which is what the
replication note below exists to address.

**What does not need to be measured.** Surface CD98, CD9, pSTAT3, ITGA2, α-DG-N,
GLI1, PTCH1, NR2F2, HAND2, BMP2, SPP1, embryos, attachment. None of them
separates a SEC class pair, and each is a new assay class. In particular **no
embryo is needed**: every separation is in an embryo-free maternal arm.

**Optional, in strict priority order, only if capacity exists.** A single
top-outlet SPP1 ELISA. `E_SPP1_EXPR` is a second member of the same 9-node
epithelial class, so agreement with PAEP extends the conclusion from the
`E_PAEP` branch to the class, and disagreement is a genuine falsification of the
class itself. This is the only addition that buys identifiability; it is optional
because the primary decision does not need it.

---

## 5. Decision tree

Read at the pre-registered band rule, per unit. **The predicted values are table
C of [`experiments/stage3_decision_tables.md`](experiments/stage3_decision_tables.md)**;
what each observed pattern licenses is the judgement below, and is the part that
is mine rather than the computation's.

| PAEP (top) | IGFBP-1 (bottom) | Supported | Model action |
|---|---|---|---|
| **OFF** | **ON** | `SEC-a` **or** `SEC-e` — the arm cannot tell them apart | **Sustained E2 dependence of the epithelial secretory programme is established; the mechanism is not.** What the result licenses is the claim that continued E2 is required to maintain that programme under this protocol while the stromal programme runs on. It does **not** establish that `IN_E2` is a direct Boolean conjunct with `E_PGR`: `SEC-e`, in which E2 acts only by maintaining epithelial PGR, predicts the identical PAEP and IGFBP-1 pattern, and the computation shows the two separate only at `E_IHH`, `E_PGR` and `S_NR2F2` — every one of them `no_assay`. So the committed rule is retained as the simplest expression of a dependence now demonstrated, not as a mechanism now proven, and the OM-001 threshold gains real evidence either way. |
| **ON** | **ON** | `SEC-b` or `SEC-c` | Concurrent E2 is not required. Propose `E_SECRETORY_STATE = E_PGR`. Which of the two is settled by the registered E2-only PAEP call, not by this arm — table C shows they predict identically here. Note the cost before adopting: the partition goes **35 → 34** distinct functions, because `E_SECRETORY_STATE` merges into the `E_PGR` class. The model becomes more correct and more collapsed at once, and the E2-priming phase then needs an explicit primed state it does not currently have. |
| **OFF** | **OFF** | `SEC-d` | E2 is required in both compartments, which the model expresses nowhere. The action is **not** a secretory-state edit: it is an E2 dependence on `E_PGR` and `S_PGR`, for which the repository holds no evidence row, so the action is to open an evidence gap and seek the E2→PGR citation before encoding anything. Partition also 35 → 34. |
| **ON** | **OFF** | none | The fork as posed is wrong: E2 would be required stromally and not epithelially, which no class predicts and no rule in the model can produce. Action is to stop and re-pose the fork, not to patch a rule. |
| **indeterminate** in either channel | — | — | Record as `graded_not_boolean`. This is a model-**class** finding, not an identification: it says the input layer is dose-graded where the network is Boolean, and it belongs to the same future rate layer as the EPAC entry. Do not force a band call to avoid this outcome. |

The three retained variants outside this fork — `GP130-b`, `CD98-b`/`CD98-c`,
`PC6-b` — are untouched by every outcome. This experiment does not advance them,
and no result licenses adopting one.

---

## 6. Runner-up

> **Full cocktail + SMO antagonist, reading IGFBP-1 and PRL from the bottom
> outlet, plus a GLI1/PTCH1 pathway-activity readout in the stromal channel.**

This is the strongest alternative, and the right one if E2 withdrawal turns out
to be incompatible with maintaining the epithelium (§8, objection 2).

It is the only candidate that targets a **recorded** evidence gap with a stated
ADOC-tractable resolution: GAP-014 asks for exactly this arm. It attacks the one
mechanism the two-channel chip exists to represent — the epithelium→stroma
relay — and that relay is currently *structurally vacuous*, so a positive result
forces a genuine topology change rather than an input-logic edit. Its separation
lands on `S_IGFBP1`, a usable assay, with opposite predictions: `HH-a` predicts
IGFBP-1 and PRL unchanged, `HH-b` predicts both lost.

Three things keep it second, and the first is decisive:

1. **The committed model predicts that nothing propagates.** Blocking reception
   changes no maternal node downstream, because `S_BMP2 = (S_PGR and S_PKA) or
   S_NR2F2` reduces to `S_PGR`. So the `HH-a` outcome is "no change anywhere" —
   which is exactly what a failed drug, a wrong dose or poor chip penetration
   also produces. The arm is only interpretable with a target-engagement control,
   which is a **new assay class** (GLI1/PTCH1 transcript in the stromal channel).
   The recommended experiment has no equivalent failure mode.
2. **The link being tested has no human correlative support, let alone causal.**
   GAP-014 records it: NR2F2/COUP-TFII was not among REF-075's measured targets,
   so even the correlative human step from Hedgehog output to NR2F2 is untested.
   REF-026 is rescue-grade but entirely mouse in vivo and PR-Cre driven, so
   compartment attribution rests on a reported expression pattern.
3. **Off-target risk over six days.** A small molecule on both channels for four
   days carries a specificity burden that a reagent omission does not, and
   `GAP-007` records that many perturbations affect junctions, viability or
   morphology non-specifically.

**Third, and explicitly not recommended: cocktail minus cAMP.** It is as cheap as
the recommendation and separates a pair on a usable assay, so it is worth saying
why it loses. Its only alternative class, `CAMP-b`, has nothing supporting it:
REF-073 shows the EPAC-selective analogue *inert alone* and EPAC/RAP1 knockdown
*attenuating* the PKA-driven IGFBP-1 and PRL response. The informative-sounding
outcome — reduced but present — is Kusama's graded potentiation, which the
candidate table already rejected as a node because a rate-free Boolean model
cannot express it. The arm would spend a donor rediscovering a model-class
limitation this repository has already recorded.

**A free observation, not an experiment: `dropout_xav939`.** `IN_XAV939` is one
of three inputs table A reports as **read by no rule** in `network.bnd`, and the
only one of the three the protocol administers: it is set TRUE in every
hormone-treated `.cfg`, while `IN_HCG` and `IN_EMBRYO_CONDITIONED_SIGNAL` are
never turned on in any arm. The model therefore predicts that removing XAV939 changes
nothing, anywhere. That is a clean falsification target and the cheapest possible
intervention, and it is still not the recommendation: it separates no class pair,
because no competing class exists — writing one would mean inventing a WNT edge
and a target that no repository evidence row supports. A positive result would
prove a node is missing without saying which. Worth appending to any future run
that has a spare channel; not worth a donor.

---

## 7. Residual ambiguity

What the recommended experiment will **not** identify, stated so that no later
reading of its result overreaches:

* **Everything in U3 and U4.** `E_LIF = E_GP130_STAT3 = E_CD98_CD9` stays one
  function and `E_DAG1_CLEAVED = E_PC6` stays an identity. No SEC outcome
  touches either, and neither has any assay.
* **Which member of the 9-node epithelial class the result applies to.** The
  readout is `E_PAEP`, and the model's claim that the other eight share its rule
  is an assumption this arm inherits rather than tests. The optional SPP1 ELISA
  is the only cheap way to probe it.
* **Where E2 acts.** `SEC-a` and `SEC-e` — a direct conjunct with `E_PGR`, or
  maintenance of epithelial PGR itself — are indistinguishable by this arm and
  by every other arm in the catalogue at a readout that exists. They differ only
  at `E_IHH`, `E_PGR` and `S_NR2F2`, none of which has an assay. Separating them
  needs a proximal epithelial PGR-state measurement, which this design
  deliberately does not buy; see §6.
* **The `SEC-b` versus `SEC-c` distinction**, which needs the registered E2-only
  PAEP band and not this arm.
* **Hedgehog reception (U2, GAP-014)** — untouched, and left as the runner-up.
* **Anything graded.** If either analyte lands between bands, the experiment
  returns a model-class verdict rather than a rule. That limitation is shared by
  every candidate considered and is not specific to this one.
* **The PRL/IGFBP-1 kinetic axis.** The lost column-to-chip mapping and the
  unregistered IGFBP-1 threshold are untouched. Running this arm does not make
  the day-0/3/6 series interpretable as a trajectory.
* **Any interface or penetrance question.** Every separation here is embryo-free;
  the three `X_INTERFACE_*` relays are not exercised, and Gate 3b stays closed.
* **Time.** MaBoSS relative time stays uncalibrated. "Day 6" is a sampling
  instruction for the wet lab and never a simulation horizon.

---

## 8. Internal adversarial pass

Same-vendor. This is not independent review, and the findings below changed the
artifact before it was committed.

> **Read this section as chronology, not specification.** It records what was
> found and when, including states the document has since left behind. Where an
> item describes an architecture that later changed, it says so; §§1–7 and the
> generated tables are the current specification. Treating this log as a second
> specification is itself a defect the reviews have caught.

1. **Tried to falsify the recommendation on the threshold it claims to avoid.**
   Partly successful. The PAEP bands in hand do not overlap, so the ordinal call
   is defensible — but only if a minus-E2 value actually lands in a band. An
   intermediate value is a real possibility and the design now names it as an
   admissible `graded_not_boolean` outcome rather than forcing a call. The
   pre-registration clause in §4 was added for this.
2. **Looked for an outcome that makes the experiment uninformative.** Found one,
   and it is not the graded case: **cell loss over four E2-free days.** Reduced
   epithelium reproduces the `SEC-a` signature on PAEP exactly and would be read
   as confirmation of the committed rule; reduced stroma reproduces the `SEC-d`
   signature on IGFBP-1, which is worse, because `S_IGFBP1` is the *only* thing
   separating `SEC-a` from that confounder. Confluence imaging in both channels
   was promoted from an afterthought to a required control — and the stromal
   half of it only after the round-5 review pointed out that I had controlled
   the epithelial side alone. This is the recommendation's most serious
   weakness and it is not fully eliminated by imaging.
3. **Looked for a cheaper experiment with the same discrimination.** Found a
   genuinely cheaper one — `observe_e2_primed`, whose data are already held — and
   it is not a substitute. Every pair it reaches has `SEC-c` on one side, so it
   resolves whether `SEC-c` survives and nothing else, and it cannot tell
   `SEC-a` from `SEC-b` or `SEC-d`. The membership is the pair index's; listing
   it here is what went stale twice. It was reclassified as a **prerequisite
   registration task** rather than an alternative, which is a real change to the
   recommendation. An earlier draft of this artifact said it separates `SEC-a`
   from nothing at all; that was wrong, the shipped pair index contradicted it,
   and it is now pinned by a test rather than only stated.
4. **Checked whether the readout distinguishes the classes or merely correlates.**
   `E_PAEP` and `S_IGFBP1` are the mapped nodes themselves, so the correlation
   objection does not bite at the node. It does bite one level up: PAEP identifies
   the input logic of its own branch, and the extension to the other eight
   epithelial nodes is assumed. Recorded in §7 and given the optional SPP1 probe.
5. **Checked whether the cited literature supports the causal edge being tested.**
   The recommendation does not rest on a paper, and the first version of this
   item overstated what it does rest on. OM-001's E2-only PAEP measurement is
   positive support for `SEC-c` and for `SEC-c` only; against the committed
   `SEC-a` it is *absence of support*, not support for `SEC-b`, because both
   predict `E_PAEP` OFF there. `SEC-b` rests on nothing recorded, which is
   precisely why the arm is worth running and is now stated in its own support
   entry rather than implied by its role. `SEC-d` and `CAMP-b` rest on nothing
   either; what makes them confounders is not weaker support but that a
   favourable outcome licenses opening a gap rather than an edit.
6. **Checked for a hidden assumption absent from the model.** Found one and
   stated it: the design assumes E2 priming leaves a persistent state, which the
   committed network cannot express, since it has no memory. This is why the
   `SEC-b` outcome is recorded in §5 as *increasing* collapse (35 → 34) — an
   honest cost of the repair, not a footnote.
7. **Argued the runner-up's case.** SMO antagonism targets the only *recorded*
   gap, the only cross-compartment relay, and the only fork whose committed form
   is structurally vacuous — a stronger scientific story than an input-logic
   edit. It lost on one computed fact: the committed model predicts nothing
   propagates, so its null is confounded with failed engagement and it must buy a
   new assay to be interpretable at all. That asymmetry is what decided the
   ranking, not the biology.
8. **Searched the repository for evidence contradicting the ranking.** Found
   both directions and reported both. *Against:* Gate 3a's closure audit §4
   ranks surface CD98 under E2-only first; this analysis demotes it, on the
   computed ground that `CD98-c` and `CD98-x` are inseparable in that arm and on
   the curated ground that the platform has never measured a cell-associated
   protein. *For:* `docs/design_alias_note.md` independently ranked
   hormone-treated minus-E2 as the best of 112 candidate arms by separation of
   the measured analytes (+3, ahead of minus-cAMP's +2), from a different
   computation that this analysis did not reuse.
9. **Checked the prohibitions.** No executable model file is modified; no rule,
   rate or topology is adopted; no quantitative objective is created; adhesion is
   not optimised; PRL/IGFBP-1 is not reopened; Gate 3b is not resolved; the one
   latent-style classes introduced (`SEC-d`, and later `SEC-e`) are explicitly
   non-adoptable; transcript
   is nowhere equated with surface protein — which is itself part of why the CD98
   candidate was demoted.

10. **Counted the defects this document actually produced, after four review
    rounds.** Every blocking finding across all of them was the same thing: a
    hand-written sentence about a computed cell that the generated artifact
    contradicted. Not one touched the computation, the recommendation, the
    runner-up or the decision tree, and the TSV has been byte-identical
    throughout. That is a defect of *form*, and repairing instances of it does
    not stop the next one — a document that retypes forty computed cells has
    forty places to drift, and a cell carrying a prose caveat cannot even be
    checked mechanically, as an attempt to audit this one automatically
    demonstrated. So the tables moved: §1's alias classes, §2's comparison and
    §5's predictions are generated into
    [`experiments/stage3_decision_tables.md`](experiments/stage3_decision_tables.md)
    and cited here. *At that round* four hand-written rows remained — the `SEC`
    classes — pinned against `FORKS` and verified by mutation rather than by
    assertion. **They no longer exist**: the first external review showed the
    support half of that pin compared only `none` against non-`none`, and the
    rows were moved into generated table D, which is the current architecture.
    §5's observation-to-class mapping is still hand-written, because the model
    action each result licenses is a judgement, and it is pinned by a test that
    checks it inverts the generated prediction table.

    Generating the tables immediately surfaced two errors reading had not: the
    alias listing was incomplete, and `IN_XAV939` is not the only input no rule
    reads — `IN_HCG` and `IN_EMBRYO_CONDITIONED_SIGNAL` are too, which this
    document had implied was special to XAV939. A third came from the same
    round and was in the code, not the prose: the `#:` block defining
    `ADOPTABLE` had been left attached to the wrong constant by an earlier
    edit, carrying with it the superseded prior-support wording that repair had
    replaced. The only in-code statement of the criterion was therefore both
    misplaced and self-contradictory.

11. **A defect of a different kind, and the first of it.** Rounds 1 to 5 found
    statements contradicting the work. Round 7 found the work wrong and the
    statement right: `_scrna_verdict` also took the arm's *interventions*, so
    `GP130` — whose only separating quantity is unobservable, exactly like
    `PC6`'s — was diverted into `PROXY_LEVEL_ONLY`, a verdict whose own
    definition was false of it. §3a's `GP130` row already said `not_observable`
    and was correct; table E disagreed with it. The verdict is now a pure
    function of the separating quantities, which is what its docstring always
    claimed, and a test requires identical separators to yield identical
    verdicts. Being able to see what an arm perturbs constrains nothing if the
    consequence that tells the classes apart cannot be seen. The aggregate
    conclusion of §3a is unchanged: no fork is `IN_PRINCIPLE_CONSTRAINABLE`.

## 9. Owner adjudication — both decisions made

Both were referred rather than decided by this analysis, and both were
**adjudicated by the owner on 2026-09-17**. They are recorded here in the form
the repository uses for the structural-zero fork: what was chosen, and what it
commits the run to.

### 9.1 `E_PAEP` interpretation — the internal three-band ordinal rule

**Adopted: option (b).** No external glycodelin threshold is transferred. The
rule, fixed before the run:

* **ON** — the minus-E2 value lies in or above the full-cocktail band;
* **OFF** — it lies in or below the E2-only band;
* **indeterminate** — anything between, which is an admissible verdict and not a
  tie to be broken.

The bands are the ones already in hand: E2-only 10,165–25,470 pg/mL and full
cocktail 178,072–585,609 pg/mL, five chips each, non-overlapping and about
sevenfold apart. **The rule must never be fitted from the minus-E2 result**, which
would be adjusting the ruler to the measurement; it is fixed now, before the
experiment exists.

*What this costs, stated so it is not discovered later.* Option (a) would have
given a sharper call on intermediate values; it is declined because the transfer
assumption across collection geometry, accumulation time, medium, dilution and
normalisation is not verifiable from here, and if it were wrong the epithelial
call inverts and the arm misreads. The price of declining it is that some units
may return `indeterminate`, and that is the honest outcome rather than a failure.

### 9.2 Replication — a technical duplicate of the minus-E2 arm

**Adopted: add a technical duplicate of the minus-E2 arm if material and chip
capacity permit.** It is the arm with no prior; the full-cocktail band is already
characterised by five chips in hand.

**It is technical replication only.** It does not raise biological *n*, it must
never be reported as though it does, and the biological unit remains the donor —
three of them. What it buys is narrower and real: it converts a chip-level
failure from a lost donor-condition measurement into a lost technical replicate,
which matters because the stromal call can no longer be rescued by PRL and 2 of 5
historical units read zero at day 6 in both outlets.

**If capacity does not permit it:** retain one chip per donor per condition and
**pre-register, before the run**, how a technical failure and an uninterpretable
unit are reported — not decided afterwards.

---

## 10. External review of `5a1044b`, and what it changed

On 2026-09-17 the pushed tree at `5a1044b` was reviewed **outside this session by
OpenAI GPT-5.6 Sol**, against the pushed GitHub tree. That makes it the first
**cross-vendor** evidence on this change: every gate round recorded against it so
far came from the same-vendor Claude stand-in, because the independent Codex
reviewer has been quota-exhausted since 2026-09-14.

**It is evidence, and it is not acceptance.** The harness has no command that
imports an external verdict — `aih accept` records *human* acceptance and is the
owner's alone — so this section is the record, the gate still reads
`accepted = false`, and nothing here is independently accepted. Every finding was
reproduced against the local tree before being acted on.

| Finding | Disposition | What the local check showed |
|---|---|---|
| **B1** — the claimed pin on the `SEC` rows was weaker than the test | **CONFIRMED** | The assertion compared `startswith("none")` on both sides: `none` against non-`none`, so `SEC-c`'s support could have drifted to a different non-`none` claim unnoticed. Resolved structurally, as the reviewer preferred: the rows are now **table D** and no class row remains in this document. |
| **B2** — PRL was making a decision it is not activated to make | **CONFIRMED, and worse than stated** | `OM-006` puts PRL at `provisional` / `context_only` / `not_used`, and its `exclusion_reason` ends "No numeric weight, ever." The either-analyte rule gave it power to flip a stromal call that the activated diagnostic does not have. IGFBP-1 is now the decision variable; PRL corroborates; the uninterpretable case returns `discordant/indeterminate`. |
| **B3** — existing scRNA evidence had not been used to update the ranking | **CONFIRMED as a gap; result is that the ranking does not move** | §3a and **table E**. No fork the ranking turns on is movable: `SEC` is decided on two `construction`-role nodes and a `not_observable` input. Reported as positive evidence for the recommendation, not as an absence. |
| **B4** — `PAEP OFF + stromal ON` licensed more than the arm proves | **CONFIRMED, and sharper than argued** | The reviewer reasoned from what the confluence controls do not cover. The computation is stronger: `SEC-e` — E2 maintaining *epithelial* PGR only — predicts the **identical** PAEP and IGFBP-1 pattern, and separates from `SEC-a` only at `E_IHH`, `E_PGR`, `S_NR2F2`, all `no_assay`. Resolution **A** adopted: the outcome establishes sustained E2 dependence, not the mechanism. |

Both advisories were adopted: *free* (19, structural) and *latent* (5, design)
are now used only in those senses, and the replication question is recorded in
§9 rather than decided here.

**Nothing the reviewer recommended against was done.** `network.bnd`, every
condition `.cfg`, the calibration policy and the interface/penetrance topology
are untouched, and Gate 3b stays closed.

### Second round, on `c78b506`

The same external reviewer confirmed B1, B2 and B4 as resolved and said to keep
them. Three further findings, all reproduced locally first:

| Finding | Disposition | What the local check showed |
|---|---|---|
| **B5** — §3's pair counts went stale when the fork grew | **CONFIRMED** | The E2-only arms separate **four** `SEC` pairs, not three — `SEC-c/e` appeared with `SEC-e` — and "the remaining three-way between `SEC-a`, `SEC-b` and `SEC-d`" was left over from a four-class fork. Fixed as the reviewer preferred: the counts are **removed**, not updated. §3 now states the structure — every pair the E2-only arms reach has `SEC-c` on one side; their union with `dropout_e2` leaves exactly `SEC-a vs SEC-e` — and cites the generated pair index for numbers. The whole document was swept for counts that moved with the fork; the three that remain were checked and are correct. |
| **B6** — the header's provenance claim was stale | **CONFIRMED** | It said no cross-vendor review was available, which §10 contradicts. Rewritten to separate the two true statements: no harness-native Codex verdict during the gate rounds, and an ongoing external cross-vendor review that is not a harness verdict. Chronology preserved; acceptance not implied. |
| **B3** — partly resolved, not scientifically closed | **CONFIRMED on all three sub-points** | See §3a, rewritten. (1) `CONSTRUCTION_ROLE_ONLY` was too absolute for a calibration task, and the decisive reason is now the *design*: the deposited object holds two conditions, `CNT` and `HT`, and `HT` moves E2, MPA, cAMP and XAV939 together, so the E2-dropout contrast that separates `SEC-a` from `SEC-b` **is not in the data**. (2) `IN_E2` and `IN_cAMP` are experimenter-set and known from the protocol; treating "not inferable from RNA" as the limitation was the wrong frame, and the real one is that `CNT` vs `HT` is bundled — the same bundling `U1` records. (3) The expression analysis was still not run, but the justification is replaced: `AGENTS.md` forbids loading the object *to test availability*, not a pre-specified analysis, and KLF12 used it deliberately. |

### Third round, on `fef95a1`

Three findings, all reproduced locally and all confirmed. The reviewer also
re-confirmed `dropout_e2` as preferred with `smo_antagonist` runner-up.

| Finding | Disposition | What the local check showed |
|---|---|---|
| **B7** — B5 was not fully closed | **CONFIRMED** | §3 and §8.3 still enumerated three `SEC` pairs; the artifact says four. My earlier sweep fixed §3's *counts* and missed both *lists*. Fixed by forbidding the enumeration rather than correcting it: a test now fails if the document lists computed pair sets at all, and only the structural statements — every pair the E2-only arms reach has `SEC-c` on one side; exactly one pair is unreachable — remain. |
| **B8** — §8 read as a second, stale specification | **CONFIRMED** | It still described four hand-written `SEC` rows as current, after table D removed them, and named `SEC-d` as the only introduced confounder after `SEC-e` joined. §8 now opens by declaring itself chronology rather than specification, and the superseded states are in the past tense with what replaced them. |
| **B9** — table F proved less than its heading claimed | **CONFIRMED** | The heading said "why no scRNA result could change the choice". What is proved is a **conditional** invariance: under frozen v0.4 and the current activation policy, no scRNA finding can add or remove a usable-assay candidate arm. Preference also weighs credible uncertainty, class count, engagement ambiguity, cost and robustness, and a strong finding can move the uncertainty set without touching a tier. Heading and conclusion narrowed in both the document and the generated table. |

The stand-in gate sweep, running against the same tree, independently found three
more: the same stale enumerations, an over-general claim that "the two hCG arms
separate nothing measurable" (true of the hCG *addition*, false of
`add_hcg_on_e2`, which separates `SEC` on `E_PAEP` via its E2 background), and a
free-variable decomposition that said 13 `IN_*` and 5 `X_*` where the network has
**14** and **4**. The last was introduced while *fixing* the free/latent
terminology advisory, and the total happened to survive, which is why reading it
did not catch it. It is now counted in table A rather than written by hand. It
also found that `CAMP-b`'s recorded reason for being confounder-only was a
support argument, not a licensing one.

**That repair was itself defective, and the next round caught it.** The test I
added accepted the word "carried" as well as an explicit licensing statement —
which made it pass on the exact bare-support string it was written to reject. The
alternative was there because `SEC-d`, `SEC-e` and `CD98-x` all justified
themselves with "Carried …" and stated no licensing consequence: I weakened the
invariant to fit the data instead of fixing the data, which is the shape the
repair policy exists to catch. All three now state what an outcome favouring them
licenses — open an evidence gap for `SEC-d`; nothing at all for `SEC-e`, because
no outcome distinguishes it from the committed rule on either usable assay;
reopening whether `E_CD98_CD9` is a switch for `CD98-x`. The check requires an
explicit licensing statement and nothing else, and **it is verified by
mutation**: restoring `CAMP-b`'s pre-repair text turns the suite red. That step
exists because this is the fourth pin in this artifact that did not pin, and the
second time I claimed one without demonstrating it.

**Closure of B3 by demonstrated invariance, route B.** The reviewer set the
correct bar — that "AC04 is not what the recommendation turns on" is not an
argument — and **table F** now meets it: the ranking criterion is a readout tier;
that tier is computed from `config/observation_model_map.tsv` alone; **no row of
the scRNA map is active**, so no scRNA finding can promote any node to
`usable_assay`; `GP130` and `CD98` are decided at `mapped_composite` and
`no_assay`; therefore neither extreme AC04 result can move them, and the
candidate set for "preferred" is invariant. What that does not claim is recorded
alongside it.

---

## 11. What comes after this artifact, and what does not

Recorded so the boundary is explicit rather than assumed.

**Pre-freeze (this unit):** B7, B8 and B9 above; the pending broad gate sweep;
the two owner decisions in §9. Nothing else.

**Next unit — the scRNA node-support / alias audit.** Classified as
**post-freeze**, and the reasoning is the invariance in §3a rather than
convenience: the `SEC` E2-dropout contrast is absent from the deposited design,
so no node-support result can resolve the fork the recommendation turns on, and
the audit's purpose is model refinement rather than experiment selection.
Hypothesis-driven, not a DE atlas: for each RNA-assessable node, classify the
expression support (`robustly_detected` / `sparse` / `not_detected_with_power` /
`not_assessable_by_RNA`), what the measurement can mean (`direct_node_support` /
`availability_only` / `program_or_activity_proxy` /
`cannot_inform_functional_state`), and the consequence for the twin. The
asymmetry is the point: robust presence supports availability and rarely proves a
Boolean ON state, while convincing absence in the right compartment, with
adequate depth and donor consistency, can genuinely challenge a node that
requires contemporaneous expression. `AC03`
(`E_PGR`/`E_IHH`/`S_PGR`/`S_NR2F2`/`S_BMP2`) is the most valuable target, because
v0.4 forces five independently RNA-assessable states into one function;
then `AC04` and `AC01`, with their proxy limits stated. Donor is the unit, there
are three of them, cell count is not replication, and `celltype_v2` is
condition-defined so it cannot carry a condition contrast. Construction-role
evidence is usable here — the purpose is refinement — provided it stays labelled
as such and nothing later calls it validation.

**Also post-freeze: the README refresh.** It is stale. What should change is
framing, not the model: distinguish the **2 activated ADOC protein readouts**
(`E_PAEP`, `S_IGFBP1`) from the states carrying some scRNA observability; say
that adhesion is `diagnostic_ordinal` and not quantitatively calibrated; add the
Stage-3 status and the preferred prospective experiment. A new summary schematic
— evidence → v0.4 → structural aliases and gaps → prospective experiment →
refinement — is the right vehicle. The structural DAG and the dynamics GIF stay
as they are and stay labelled as the executable v0.4 model: `SEC-e` is a
hypothesis class, and GLI1/PTCH1, pSTAT3, surface CD98/CD9 and α-DG-N are
proposed measurements. **None of them is a MaBoSS node**, and drawing them as one
would be the error this whole artifact exists to avoid.

**Not in scope until the owner opens it:** Gate 3b, and any edit to
`network.bnd`, the condition `.cfg` files, the calibration policy or the
interface/penetrance topology.

---

## 12. The frozen prospective design

**Frozen 2026-09-17 against `adoc-literature-superset-v0.4.0`.** Everything below
is fixed before the experiment exists. It may be *executed*, or *superseded by a
later unit that says so*, but it is not edited in place — that is what freezing
is for, and it is why the interpretation rules are written down now rather than
after the numbers arrive.

**Arm.** Days 0–2 unchanged: E2-only priming, as the current protocol runs it.
Days 2–6: **MPA 1 µM + cAMP 0.25 mM + XAV939 10 µM, E2 omitted.** One
single-component dropout. No drug, no construct, no antibody.

**Contemporaneous controls, on the same donors in the same run.** Full cocktail
(the ON reference band); E2-only sampled at day 2 (the low reference band, and
what makes the PAEP call ordinal); a pre-cocktail PAEP baseline, which the
repository does not currently hold; and phase-contrast confluence imaging at days
2, 4 and 6 in **both** the epithelial and the stromal channel.

**Compartment and timing.** Top outlet for PAEP, bottom outlet for IGFBP-1 and
PRL, sampled at the existing day-3 and day-6 windows, with chip identity carried
so the arm's own day-3/day-6 comparison is paired.

**Assays.** PAEP, IGFBP-1 and PRL by the three existing ELISAs. **Nothing else.**
No surface CD98, no pSTAT3, no α-DG-N, no GLI1/PTCH1, no embryos, no attachment.

**Decision semantics.** `E_PAEP` by the three-band rule in §9.1. The stromal call
is **IGFBP-1's**: ON in its ON band, OFF in its day-0 band, and
**discordant/indeterminate** where IGFBP-1 is uninterpretable while PRL is
convincingly ON. **PRL is corroborative and never decisive** — `OM-006` places it
at `provisional` / `context_only` / `not_used` and its `exclusion_reason` ends
"No numeric weight, ever." A PRL/IGFBP-1 disagreement is reported as a finding,
not resolved in favour of the convenient analyte.

**Replication.** Three donors, one chip per donor per condition, plus a technical
duplicate of the minus-E2 arm if capacity permits (§9.2). Donor is the biological
unit; chips are not independent replicates; no patient-level variance, confidence
interval, paired-donor test or personalization claim may be derived.

**What each outcome licenses** is §5, unchanged, and its first row is the one to
read carefully: `PAEP OFF + IGFBP-1 ON` establishes **sustained E2 dependence of
the epithelial secretory programme**, not the mechanism, because `SEC-e` predicts
identically on both usable assays.

**Runner-up, if this proves impractical:** `smo_antagonist` — full cocktail plus
an SMO antagonist, reading IGFBP-1 and PRL, **with a GLI1/PTCH1 pathway-activity
readout that is not optional**, since the committed model predicts no propagation
and its null would otherwise be indistinguishable from failed target engagement.

**Unchanged by this freeze:** `network.bnd`, every condition `.cfg`,
`config/calibration.yaml`, `config/perturbations.yaml` and the
interface/penetrance topology. The executable model is still v0.4 — 59 nodes, 35
distinct Boolean functions. `SEC-e` is a hypothesis class and GLI1/PTCH1, pSTAT3,
surface CD98/CD9 and α-DG-N are proposed measurements; **none of them is a MaBoSS
node**. Gate 3b stays closed.

**Next unit, and explicitly not part of this one:** the hypothesis-driven scRNA
node-support / alias audit scoped in §11, `AC03` first. Mechanistic scRNA
integration comes after that and belongs to a **new model version**, not to an
edit that rewrites this frozen result.
