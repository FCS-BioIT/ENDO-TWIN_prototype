# Drug-only calibration candidate selection, 2026-10-07

**Outcome: no comparative ranking is established and no verdict token is
asserted.** The STAT3 inhibitor peptide is the candidate this document evaluates
in most detail (§5.2), which reflects where the evidence trail led and **not** a
ranked position. Which arm to run is an owner disposition; this document
evaluates candidates individually and does not supply a defensible comparison of
the field (§5.0).

**A superseded draft claimed `OTHER_DRUG_BETTER` (recombinant hCG on the
E2-primed arm). Withdrawn in full**, on five verified defects: it mis-transcribed
its own computation (the full-HT row showed KLF12-low values labelled as the
KLF12-high result); it counted `CD98-a` as a variant when
`gate3_candidate_variants_2026-09-16.tsv` records it as the baseline, and
`CD98-c` as "IDENTICAL to `CD98-b`" at partition level; it omitted `CD98-x`
entirely; it scored `e2_primed_maternal`/v0.6.0/`E_CD98_CD9` against
`CHK-HTM-D6`, which covers `hormone_treated_maternal`, v0.2.0–v0.5.0 and
`S_IGFBP1;S_PRL`; and its universe missed
`context/experiments/calibration_candidates.tsv` (`CAND-01`–`CAND-14`).

**Candidates examined here were already adjudicated elsewhere** — under that
review's own numbering, not the `CAND-*` registry's, and no repository artifact
formally maps the two (§5.0). Three bear closely enough to quote. From
`docs/experiment_candidate_review_2026-09-22.md`, which that draft had not read:
**C2** (E2-only → surface CD98) "RESCOPE … drop the HIGH priority", since
`CD98-c` vs `CD98-x` "is separated by `dropout_e2` and by nothing else"; **C10**
(hCG) "DEFER", class gain 1 "separating no measured node"; and **C12** (STAT3
inhibition) "KEEP as a control, not as a discriminator".

**The same review also constrains the overlapping anti-LIF/LIFR (C3),
SMO/Hedgehog (C5), IL-11 (C11), BMPR (C13), anti-SPP1 (C15), COX/prostaglandin
(C16) and TLR3/poly(I:C) (C17) subjects; §5.0 gives the verified dispositions.**
The constraint is by **experiment-subject overlap**, not by any asserted formal
identifier correspondence. **Those dispositions govern their own subjects until a
unit scoped to redo them says otherwise**, and this document does not redo them.

That review covers **17 owner-supplied candidates (C1–C17)**, a different list
from the 14 `CAND-*` rows in `context/experiments/calibration_candidates.tsv`,
and no repository artifact formally maps the two. **Several entries overlap by
experiment subject, so its dispositions constrain those subjects even without an
identifier mapping**; §5.0 tabulates the ten that bear on candidates examined
here. What is missing is the formal correspondence, not adjudication of the
subjects. On C12 specifically, see §5.2: it and PR24 speak to different
uncertainty axes and do not conflict.

**Execution precondition, not a disqualifier.** Surface CD98/CD9 is a graded
readout and the CD98 variants rest on graded evidence, so **any** CD98-reading
arm requires a **pre-registered quantitative observation rule with demonstrated
adequate dynamic range**, fixed before execution. That is one unit; the STAT3
arm needs four more on top of it, five in all (§7.1). These say *sequence the
prerequisites first*; they do not zero an arm's value (§6).

**Stage 4c admission is not closed here**, so direct model execution of any such
arm remains barred until its items are met through the Stage 4b process (§7.1).

**The owner may still conclude `NO_DRUG_ONLY_EXPERIMENT_WORTH_THE_ONE_SHOT`
operationally.** Nothing here speaks against that: no verdict token is asserted,
so there is none to contradict. If one shot cannot absorb the calibration arm
plus its mapping unit, declining is reasonable — a resourcing judgement this
analysis cannot make (§7.2).

**Scope.** This unit kept no reproducible literature-search record, so every
"best" and "none exists" claim here is scoped to **candidates recorded in this
repository** and asserts nothing about the wider literature (§4.1, §5.0, §5.2).

**Nothing was changed.** No model rule, rule variant, entity-map reading,
observation-map row, intervention-library row, declaration, ledger approval or
policy row was written or edited. The merged PR24 identifiability analysis
(`docs/identifiability_experiment_design.md`) and the Stage 4c refusal
(`docs/stage4c_admission_refusal.md`) are read as fixed inputs and are not
reinterpreted. §4 records an evidence finding about the committed `S_HAND2` rule
and proposes alternatives; **none is implemented**, and the proposal is not an
argument for implementing any of them under time pressure.

---

## 1. Scope

This unit asks one question: given that the owner will run a single perturbation
arm and will not do transfection or construct work, which soluble reagent is
worth it?

Two things are deliberately outside this candidate-assessment scope.
`dropout_e2` is a reagent *omission* with a frozen design and bench handoff
(`docs/phase1b_closure/prospective_dropout_e2_handoff.md`); it is not an added
reagent and the owner scoped this unit to added reagents, so it is excluded here
rather than compared. And the HAND2 arm recommended by PR24 requires a direct
`do(S_HAND2 = 0)` manipulation, which the constraint excludes; §4 records why
that exclusion is a property of the constraint and not a defect in PR24.

## 2. Three metrics, kept separate

An earlier draft of this analysis collapsed these and then described candidates
as "zero yield" without saying which was zero. They are not interchangeable, and
no candidate below is called zero without naming the metric.

| Metric | Source | What it counts |
|---|---|---|
| Stage-3 usable forks | `docs/experiments/stage3_experiment_design.tsv` | class-pair forks separated on a node the platform can assay |
| PR24 variants low/high | `docs/identifiability_design/design_yield.tsv` | registered rule variants discriminated, per `E_KLF12_HIGH` scenario |
| PR24 alias pairs | same | alias pairs resolved |

A design absent from `design_yield.tsv` is **not scored** on the PR24 metrics.
That is distinct from scoring zero, and `smo_antagonist`, `add_hcg_on_e2` and
`dropout_e2` are all in that position.

The two layers are **not** in one-to-one correspondence and no mapping between
them is asserted here. A PR24 design is an idealised node veto; a Stage-3
experiment is a named bench arm, and PR24 §6 records that a reagent realising a
given veto may not exist (anti-LIF does not realise `E_LIF@expression`). The two
tables are therefore kept apart.

PR24 designs (`design_yield.tsv`):

| Design | Variants low/high | Alias pairs |
|---|---|---|
| `4_stat3_veto` | **1 / 2** (`CD98-c`) | 0 |
| `5_lif_veto` | **1 / 2** (`CD98-c`) | 0 |
| `6_two_arm_stat3_and_lif` | 1 / 2 | **1** (KLF12-low only) |
| `3_hand2_veto` | 1 / 2 | 0 |
| `1_readout_only_existing_arms` | 0 / 1 | 0 |

Stage-3 experiments, usable-fork counts (`stage3_experiment_design.tsv`), for the
added-reagent arms in scope:

| Experiment | Usable forks |
|---|---|
| `add_hcg_on_e2` | **4** |
| `smo_antagonist` | **1** |
| `anti_lif`, `anti_lif_plus_il11`, `add_il11`, `anti_spp1`, `bmpr_inhibitor` | 0 |

No single-arm design resolves an alias pair. That is PR24's own headline and is
not re-derived here.

## 3. The reagent registry as it stands

`config/intervention_library.tsv` holds three interventions on v0.6.0:
`mifepristone` (→ `E_PGR`, `S_PGR`), `anti_spp1` (→ `X_SPP1_LUMEN_FREE`), and
`hand2_loss` (genetic). `xav939` is `no_executable_effect`. All four carry
`mapping_basis = migrated_legacy_behaviour` or `executable_legacy_behaviour`.

`models/superset/adoc-literature-superset-v0.6.0/drug_target_catalog.tsv` holds
32 rows: **27 `screening_readiness = structural_only`** and **5 `catalog_only`**
(`S_STAT3`, `S_DECIDUAL_SENESCENCE_BALANCED`, `X_LGALS1_3`, `X_BSG_ITGB1`,
`IN_UTERINE_WNT_CUE`). An earlier draft said every non-library row was
`structural_only`, which the catalog contradicts. Neither state carries an
efficacy claim.

`config/direct_effect_target_declarations.tsv` and
`config/direct_effect_adjudications.tsv` each contain **0 data rows**.
**No direct-effect declaration exists for any agent, including `mifepristone`
and `anti_spp1`** — their intervention-library rows are migrated legacy
behaviour, which is a different and weaker thing than a governance approval, and
§5 reports the two statuses in separate columns for that reason. Any added
reagent below would be the first declaration ever written, recorded per
candidate as `would_require_first_declaration` rather than used to eliminate
anything. Governance status is not a scientific objection.

## 4. Why HAND2 is unavailable here

### 4.1 No pharmacological route exists

**Category A — direct HAND2 agents: none recorded.** **No HAND2-selective
inhibitor, degrader, dimerisation blocker or DNA-binding antagonist appears
anywhere in this repository's registered corpus** (`context/literature/`,
`config/`, `docs/`). As in §5.1, that is a claim about the corpus and **not**
about the literature: this unit kept no reproducible search record, so it does
not assert that no such agent is reported anywhere. HAND2 is a bHLH
transcription factor, a class for which the repository registers no small-molecule
agent of any kind.

Two further statements are flagged as **unregistered background, carried for
orientation and load-bearing on nothing**: that bHLH transcription factors are
generally not addressed by small molecules, and that HAND2 is silenced by
promoter hypermethylation in endometrial cancer such that demethylating agents
raise it. Neither is registered here, neither was full-text inspected, and no
conclusion in this document rests on either.

**Category C — mifepristone.** In primary human ESCs (E2 10⁻⁸ M + MPA 10⁻⁷ M,
RU-486 10⁻⁶ M, 12 d, n = 4), RU486 "blocked the induction of HAND2 mRNA levels"
(Murata et al. 2019, *Reprod Biol* 19:14–21, held at
`context/literature/pdfs/`). The verb is *blocked the induction*, not *reduced
expression*: the effect is PGR-mediated by construction, and no HAND2 protein or
activity measurement appears in the source. Mifepristone maps to `S_PGR`, not
`S_HAND2`.

**Category B is empty, and §4.2 says why it is empty structurally rather than
for want of searching.**

### 4.2 Evidence audit of the committed `S_HAND2` rule

**Verdict: `CURRENT_HAND2_RULE_OVERCOMPRESSED`.**

The committed stromal chain (`models/superset/adoc-literature-superset-v0.6.0/network.bnd`)
is `S_PGR = IN_PROGESTIN`; `S_PKA = IN_cAMP`; `S_NR2F2 = E_IHH and S_PGR`;
`S_BMP2 = (S_PGR and S_PKA) or S_NR2F2`; `S_HAND2 = S_BMP2 or S_PGR`;
`S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2`.

A local truth table over `IN_PROGESTIN`, `IN_cAMP` and `E_IHH`, **at fixed
points**. Two scope statements, both load-bearing.

**`E_IHH` is varied independently here, which the committed model does not do.**
`network.bnd` derives it: `E_IHH = E_PGR` and `E_PGR = IN_PROGESTIN`, so rows
with `IN_PROGESTIN = 0` and `E_IHH = 1` are unreachable in the committed wiring.
Varying it independently makes the enumeration a **superset** of the reachable
states, which is the conservative direction for the conclusion drawn below: a
collapse that holds across the superset holds across the reachable subset. It is
not a claim that `E_IHH` is a free input.

**The table is an equilibrium substitution, not a statement about
trajectories** — §4.2b gives the asynchronous counterexample that forces that
scope.

| `IN_PROGESTIN` | `IN_cAMP` | `E_IHH` | `S_PGR` | `S_BMP2` | `S_HAND2` | committed | variant |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| 1 | 0 | 1 | 1 | 1 | 1 | 0 | 0 |
| 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

Both disjuncts of `S_BMP2` contain `S_PGR`, so `S_BMP2 ⟹ S_PGR` and the
disjunction `S_BMP2 or S_PGR` collapses: **`S_HAND2 ≡ S_PGR` on every row**.
Consequently the committed `S_DECIDUALIZED` and the registered
`hand2_required_decidual_variant` (`rule_variants.tsv`, `catalog_only`) agree on
every row. Both reduce to `IN_PROGESTIN and IN_cAMP`.

**This does not make the variant vacuous, and an earlier draft of this analysis
wrongly called it that.** A direct `do(S_HAND2 = 0)` overrides the structural
equation for `S_HAND2`; two models that differ only under such an intervention
are a valid causal distinction, not a notational one. PR24 scores Design 3 as
`hand2_required_decidual_variant@veto:S_HAND2` and **remains correct for a direct
HAND2 manipulation**. What the collapse establishes is narrower and is the point
for this unit: **at a fixed point**, every route to `S_HAND2 = 0` through the
model's own wiring requires `S_BMP2 = 0` and `S_PGR = 0`, each of which
independently zeroes the committed rule.

#### 4.2b The equivalence holds at fixed points only

**An earlier draft claimed the two rules agree everywhere and that no
upstream-acting agent could discriminate them. That is false for transient
dynamics and is withdrawn.** MaBoSS is asynchronous: nodes update one at a time,
so an intermediate state can hold a value no simultaneous substitution produces.

From the all-zero internal state with `IN_PROGESTIN = IN_cAMP = 1`, the enabled
update sequence `S_PGR↑`, `S_PKA↑`, `S_BMP2↑`, `S_DECIDUALIZED↑` reaches
`S_DECIDUALIZED = 1` while `S_HAND2` has not yet been scheduled and is still 0.
The committed rule permits that transition; `hand2_required_decidual_variant`
forbids it. **So the two models are distinguishable on trajectories**, and only
their fixed points coincide.

The consequence is that the equivalence in §4.2 is an **equilibrium algebraic
result and nothing more**. No observation-layer conclusion is drawn from it.

**An earlier draft restricted the no-upstream-discrimination conclusion to
`CHK-HTM-D6` and called that the declared experimental endpoint. That is
withdrawn**: `CHK-HTM-D6` covers `hormone_treated_maternal`, model versions
v0.2.0–v0.5.0 and `S_IGFBP1;S_PRL` (`config/observation_checkpoints.tsv`), so it
applies neither to the v0.6.0 rule audited here nor to a HAND2 readout. **No
registered checkpoint applies to either**, so this document draws no conclusion
about what an experiment could or could not separate — at a fixed point, in a
transient, or at all. Establishing that would need an applicable checkpoint and
a bounded asynchronous analysis, neither of which exists.

The overcompression is in the `S_BMP2 → S_HAND2` edge, graded by system:

| Claim | Human primary ESC | Mouse | Verdict |
|---|---|---|---|
| PGR → HAND2 | Cho 2013 *Fertil Steril* 99:248–55 (MPA induces, time/dose-dependent); Murata 2019 (RU486 blocks induction) | REF-028, PR-Cre | **Supported** |
| BMP2 → HAND2 | none in the registered corpus | REF-027 *Bmp2* cKO, REF-028 — neither tests the edge directly | **Not established** |
| HAND2 → PRL | Shindoh 2014 *Fertil Steril* 101:1781–90: HAND2 siRNA under MPA+E2 "significantly reduced … fibulin-1, prolactin, TIMP-3, IL-15, and FOXO1A" | — | **Supported** |
| HAND2 → IGFBP1 | not reported in Shindoh (IGFBP-**5** reported unaffected) | — | **Absent** |

The curators' own annotation on the BMP2 edge already hedges it —
`context/literature/candidate-edges.tsv` EDGE-010, "Compact relay; direct
ordering may vary by context" — and the `S_BMP2 or S_PGR` logic hint is a
literature-curation field in `candidate-nodes.tsv`, not a derivation.

**The tension worth recording, stated at the grade the evidence supports.**
Shindoh 2014 reduced HAND2 by siRNA under E2+MPA — PGR signalling intact — and
the mRNA levels of fibulin-1, prolactin, TIMP-3, IL-15 and FOXO1A fell. So
**graded suppression of HAND2 changes selected decidual outputs while PGR is
active**, which the committed `S_HAND2 ≡ S_PGR` encoding gives no way to express.

**An earlier draft called this `do(S_HAND2 = 0)` with `S_PGR = 1`, and that
overstates it.** siRNA knockdown is graded and acts at expression level; the
source reports suppression, not abolition, and **HAND2@activity — the level
`node_entity_map.tsv` declares for `S_HAND2` — was never measured**. Reading a
graded expression knockdown as a Boolean zero-activity state needs a validated
mapping, which no source supplies. This is the same graded-to-Boolean objection
§6 applies to CD98, and it applies here with equal force; not applying it to the
repository's own HAND2 evidence was an inconsistency in that draft.

What survives is weaker than a contradiction and still sufficient for §4.2's
verdict, because that verdict rests on the truth table and the edge grading
rather than on this experiment: `S_HAND2` carries no information independent of
`S_PGR` under the committed rule, while the one human primary experiment that
manipulates HAND2 directly reports an effect on outputs with PGR held active.
Whether that effect licenses a Boolean HAND2 requirement is exactly what the
missing mapping would decide, and this document does not decide it.

`models/extended/adoc-literature-v0.2.0/uncertainty_notes.md`
already records that `S_HAND2` "does not alter downstream logic" in the default
comparator; what was not recorded is that the stricter variant does not alter it
either.

### 4.3 Alternatives, proposed and not implemented

For the variant to differ endogenously, the requirement is that some
**fixed point** has `S_DECIDUALIZED = 1` and `S_HAND2 = 0`. The qualifier is
necessary, not stylistic: §4.2b shows such a state *is* reachable as an
asynchronous transient under the committed rule, so stating the requirement over
reachable states would make it already satisfied and the comparison below
vacuous.

**An earlier draft stated this as "`S_HAND2` must depend on something outside
`{S_PGR, S_PKA, S_BMP2}`", which is false.** A rule over those three variables
alone can satisfy the requirement. Take the alternative rule
`S_HAND2 = S_BMP2 and not S_PKA`, leaving the committed
`S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2` unchanged. With
`S_PGR = S_PKA = S_BMP2 = 1`, the committed rule evaluates to `S_DECIDUALIZED = 1`
while the alternative gives `S_HAND2 = 0`, since its `not S_PKA` conjunct is 0. The outside-determinant framing holds only under an unstated
monotonicity restriction on the rule, which is not asserted anywhere and is not
asserted here. The three alternatives below are therefore **candidates, not an
exhaustive repair space**; a non-monotone rule over the existing variables is a
fourth family that this unit has not explored.

What follows is the narrower claim §4.2 rests on, **stated at fixed points, as
§4.2b requires**: under the committed rule `S_HAND2 = S_BMP2 or S_PGR`, no such
state is a fixed point. It is reachable as an asynchronous *transient* — that is
precisely the §4.2b counterexample — so "reachable" without qualification would
contradict §4.2b. Fixing the outputs alone cannot produce a fixed point with
that property either, for the same reason.

| | Alternative | Basis | Endogenously distinguishable? | Soluble upstream perturbation sufficient? |
|---|---|---|---|---|
| **A** | `S_HAND2 = (S_BMP2 or S_PGR) and not IN_HAND2_LOSS` | reinstates `LE096`, retired at `topology.tsv` under `INC-V060-LE096` | **not endogenously; yes under a direct HAND2-loss intervention** | **no** — the input is a knockdown by another name |
| **B** | `S_HAND2 = S_PGR and S_NR2F2` | an NR2F2-occupied site conserved human↔mouse enhances endogenous HAND2 mRNA in human endometrial stromal cells | **not endogenously; yes under an `E_IHH`/`S_NR2F2` intervention** | **yes**, via an `E_IHH`/`S_NR2F2` veto |
| **C** | `S_PRL = S_DECIDUALIZED and S_HAND2`; `S_IGFBP1` unchanged | Shindoh reduces PRL and does not establish IGFBP-1 | **no**, while `S_HAND2 ≡ S_PGR` | only combined with A or B |

**None of the three removes the collapse endogenously, and an earlier draft
claimed B did.** That is withdrawn. `S_NR2F2 = E_IHH and S_PGR`, `E_IHH = E_PGR`
and `E_PGR = IN_PROGESTIN` (`network.bnd`), so B reduces to `IN_PROGESTIN`, which
is `S_PGR` — the same collapse as the committed rule. A state with `S_PGR = 1`
and `E_IHH = 0` does not exist endogenously; reaching it requires an intervention
on `E_IHH`/`S_NR2F2`, exactly as A requires one on HAND2.

What distinguishes them is **which node the intervention must target**, and that
is the practically relevant difference: A's target is HAND2 itself, reachable
only by knockdown, while B's is the IHH/NR2F2 arm, where a soluble SMO antagonist
is at least conceivable (though §5.3 records why that arm is weak on its own
terms). B also needs the most scrutiny on evidence: the NR2F2 support is
*enhancement*, not *necessity*, and encoding it as a conjunction is a stronger
claim than the source makes. C is the best-evidenced change and is inert alone. Adjudicating
among them is a model-reading decision to be taken on its own, separately from
any experiment selection, and is not taken here.

Note also that `S_PRL` and `S_IGFBP1` are both defined as `S_DECIDUALIZED` and
are therefore the same Boolean function under two names, so the model cannot
currently represent PRL/IGFBP-1 divergence at all. That is recorded as an
observation, not proposed for change in this unit.

## 5. Candidate assessment

### 5.0 Why this document does not rank the candidates

**No comparative ranking is offered, and the two drafts that offered one are
withdrawn** — the first for mixing Stage-3 usable-fork counts with PR24 variant
counts, the second for the five defects itemised in the header. What follows
records what a valid comparison would need, so a later unit can do it properly.

**The universe is not what either draft said.** There are three registries, and
they do not coincide:

| Registry | Contents |
|---|---|
| `context/literature/perturbations.tsv` | `PERT-001`–`PERT-018`, mechanism-level perturbations |
| `docs/experiments/stage3_experiment_design.tsv` | named bench arms, scored on usable forks |
| `context/experiments/calibration_candidates.tsv` | **`CAND-01`–`CAND-14`** — the registry actually named for calibration candidates |

The third is the one this unit's question belongs to and the one both drafts
missed. It already contains `CAND-01` (E2-only priming → surface CD98),
`CAND-10` (hCG challenge), `CAND-04` (STAT3 inhibition), `CAND-13` (COX-2/PGE2)
and `CAND-14` (TLR3/poly(I:C)).

**A separate review has adjudicated overlapping ground**, and an earlier draft
of this section misdescribed it. `docs/experiment_candidate_review_2026-09-22.md`
reviews **17 candidates from an owner-supplied planning handoff, numbered
C1–C17** — *not* the fourteen `CAND-*` rows above, which are a different registry
with different numbering. The two lists overlap in substance but are not the same
list, and **no document maps one onto the other**.

**No repository artifact formally maps C1–C17 onto `CAND-01`–`CAND-14`.
However, several entries clearly overlap by experiment subject, and the
2026-09-22 review's dispositions therefore constrain those subjects.** The
constraint runs on the subject, not on the identifier, so it holds without a
formal mapping — and an earlier draft of this section wrongly inferred from the
missing mapping that subjects it covers were unadjudicated.

Dispositions that bear on subjects examined here, verified against that document:

| | Subject | Disposition |
|---|---|---|
| **C2** | E2-only → surface CD98 | RESCOPE to Track B; drop the HIGH priority |
| **C3** | anti-LIF / LIFR blockade | RESCOPE; remove from the top tier |
| **C5** | SMO / Hedgehog inhibition | KEEP as written, with its caveat strengthened |
| **C10** | hCG → CDH1 / CD98 | DEFER |
| **C11** | IL-11 ligand split | KEEP the sequencing, lower the expectation |
| **C12** | STAT3 inhibition | KEEP as a control, not as a discriminator |
| **C13** | BMP receptor / SMAD inhibition | RETIRE as a discriminator |
| **C15** | anti-SPP1 downstream challenge | RETIRE from the maternal programme |
| **C16** | COX / prostaglandin route | KEEP as written |
| **C17** | TLR3 / poly(I:C) | RETIRE from this programme |

So the COX/PGE2 and TLR3/poly(I:C) subjects — `CAND-13` and `CAND-14` in the
other registry — **are** addressed there, as C16 and C17; what is absent is a
formal identifier correspondence, not an adjudication of the subject. A ranking
unit would still have to establish that correspondence before treating either
list as a complete field.

**What a valid comparison would have to fix**, beyond reading that review:

1. **One variant-counting convention**, applied to every candidate — PR24 counts
   distinct non-default `variant_id` values, and a baseline class is not a
   variant.
2. **`CD98-x` included.** The constitutive class is the live confounder, and C2
   records that only `dropout_e2` separates it from `CD98-c`.
3. **An endpoint that governs the arms being compared.** `CHK-HTM-D6` covers
   `hormone_treated_maternal`, v0.2.0–v0.5.0 and `S_IGFBP1;S_PRL` only; no
   registered checkpoint covers an E2-priming CD98 readout on v0.6.0, so one
   would have to be registered first.
4. **A readout panel and cost rule fixed before scoring**, not chosen per
   candidate.

Each is a prerequisite, not a detail: item 3 in particular means the comparison
cannot be made at all until an applicable observation checkpoint exists.

### 5.0a Per-candidate notes

These are observations about individual candidates, **not** a ranking: no common
criterion is applied (§5.0). Several are decisive on their own terms — a
candidate that reaches no node cannot discriminate anything regardless of how
the comparison is eventually framed.

| Candidate | Ground |
|---|---|
| `PERT-001` mifepristone | zeroes `S_PGR`, so every downstream rule agrees; non-discriminating (§4.1) |
| `PERT-002` anti-SPP1 | 0 variants in both latents (`docs/identifiability_experiment_design.md` §7b.1); no maternal readout |
| `PERT-003` LIF/LIFR | target string conflates three interventions (DTR023, unfixed); an antibody does not realise `LIF@expression` (C7) |
| `PERT-012` TAZ | DTR013 forbids a YAP/TAZ compound as a mechanics surrogate; no reagent identified |
| **`PERT-013` thapsigargin** | **It does have a modelled effect.** `PERT-013` sets `IN_ER_STRESS_EXCESS`, a disjunct of the gate in `network.bnd:182` (`X_MECHANICAL_PERMISSIVE_ECM = S_DECIDUALIZED and S_TAZ_ECM and not ((IN_ER_STRESS_EXCESS or IN_HIGH_ECM_STIFFNESS) and X_MECHANICAL_STRESS_RELAY)`), so it suppresses `X_MECHANICAL_PERMISSIVE_ECM`, and hence `OUT_MATERNAL_ADHESION_COMPETENCE`, **in the relay-ON fraction**. `baseline.cfg` sets that relay to `0.70[0], 0.30[1]` — a Bernoulli flipped once at t=0 — so the effect appears in ~30% of trajectories and is absent in the rest. *Two earlier claims here are withdrawn: that the relay is off by default (the config contradicts it), and that the intervention "cannot drive the gate". `coupling_adjudication.tsv`'s "no recorded arm can excite" constrains the **relay's own state**, which is `logic = self`; it does not constrain `IN_ER_STRESS_EXCESS`, and a thapsigargin arm is exactly the arm that sets it.* What remains against it is the readout, not the reachability: the only consumer is `OUT_MATERNAL_ADHESION_COMPETENCE`, which PR24 §8.2 limits to ordinal and aggregate, against an effect present in only ~30% of trajectories |
| `PERT-016` integrins | `E_ITGAVB3_5` absorbed in all 2¹⁹ assignments (DTR009); must be de-aliased first |
| `PERT-017` sFRP2 | `IN_UTERINE_WNT_CUE` is read by **no** committed rule; reaches nothing |
| `PERT-005`, `-008`, `-011` | overexpression or knockdown — outside the no-construct constraint |
| `PERT-014`, `-018` | stiffness and temperature/pH/oxygen excursions are not soluble reagents |
| `PERT-006`, `-007`, `-009`, `-010`, `-015` | epithelial surface or protease targets whose forks are decided at `no_assay` or `mapped_composite_not_validating` (`docs/experiments/stage3_decision_tables.md` table E); each needs a new assay class **before** any variant is separable. `PERT-009` (PC6) is additionally evidence-barred by Stage 4c |

### 5.1 Candidate table — descriptive, not a ranking

`dropout_e2` excluded per §1.

| Candidate | Exact reagent | Node / effect | Stage-3 forks | PR24 var low/high | PR24 pairs | Assay | Evidence system | Level match | Off-target / compartment | Declaration | Experimental value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **STAT3** | STAT3 inhibitor peptide II (Calbiochem 573092 / P3-AHNP-STAT3BP), 20 µM, 1 h + 24 h | `E_GP130_STAT3` veto | — (no Stage-3 arm) | **1 / 2** | 0 | **new** (surface CD98/CD9; mapping unit is a prerequisite, §6) | **HES immortalised line** | **yes** — STAT3@activity hits a member | ERBB2 carrier; stromal `S_STAT3` | first declaration | evaluated in detail; §5.2 |
| LIFR blockade | PEGylated LIF antagonist, 500 ng/ml | `E_GP130_STAT3` via C3 | — (no Stage-3 arm) | not scored | not scored | new (pSTAT3) | HES line | partial — IL-11 route stays open | receptor-level, both channels | first declaration | cannot realise the veto |
| anti-LIF | neutralising anti-LIF | `E_LIF` = LIF@**expression** | 0 | 1 / 2 | 0 | new (pSTAT3) | HES line | **no** — C7 refuses | — | refused, Stage 4c §4 | structurally excluded |
| IL-11 | recombinant human IL11 | **`X_IL11` is not a node on v0.6.0** | 0 | — | — | new (pSTAT3) | primary human EEC | n/a | — | DTR003 `BLOCKS=yes` | reaches nothing |
| SMO antagonist | vismodegib / cyclopamine / SANT-1 | clamp on `S_NR2F2` | **1** | not scored | not scored | **new, required** (GLI1/PTCH1) | mouse (REF-026, PR-Cre); human necessity untested | approximate | both channels, 4 d | first declaration | §5.2 |
| **hCG on E2-priming** | recombinant hCG | `IN_HCG`; read by no committed rule but by `CD98-b`/`CD98-c` | 4 (background-attributable) | **not scored** — no hCG design in `design_yield.tsv` | **not scored** | **new** (surface CD98/CD9) + mapping unit | **REF-008 human primary, full text verified** | n/a — input activation | none identified | first declaration | see §5.4; **not ranked** |
| anti-SPP1 | anti-SPP1 neutralisation | `X_SPP1_LUMEN_FREE` | 0 | **0 / 0** (`docs/identifiability_experiment_design.md` §7b.1; not a `design_yield.tsv` row) | — | none | human | **yes** (DTR010) | — | **none**; library row `migrated_legacy_behaviour` | no maternal readout |
| BMPR inhibitor | DMH-1 / dorsomorphin | BMPR/pSMAD | 0 | not scored | not scored | none | human stromal | `S_BMP2` is both expression *and* activity | "not perfectly selective" | DTR007 `BLOCKS=yes` | "near-certain loss of both stromal analytes" |
| Mifepristone | mifepristone 10 µM, 24 h | `E_PGR` + `S_PGR` | — | — | — | none | **ADOC-executed** (R43a) | yes | not PGR-selective (GR, AR, PXR); both compartments | **none**; library rows `migrated_legacy_behaviour` | restates PGR blockade (§4.1) |
| Integrins | αvβ3 blocking antibody / cilengitide | `E_ITGAVB3_5` | — | — | — | — | — | — | — | — | DTR009: vacuous, absorbed in all 2¹⁹ assignments |
| TAZ | **none identified** | `S_TAZ_ECM` | — | — | — | — | — | — | — | — | DTR013 forbids a YAP/TAZ surrogate |

### 5.2 STAT3 inhibitor peptide

`E_GP130_STAT3` aggregates {LIFR, IL6ST, STAT3}@activity under `aggregation =
all_of`. **In this repository `all_of` means hitting one member suffices and
`any_of` means a full veto must hit every member** — the labels carry the
opposite of their set-theoretic sense, consistently across
`docs/stage4b_direct_admission.md`, `src/dt_adoc/perturbations/adjudication.py`
and `tests/unit/test_stage4b_admission.py`. Prose asserting that an agent must
engage all three entities would invert the one condition this candidate passes.

So the mapping is sound: Stage 4c calls the agent "**closest**" and records that
it passes C5, C7, C3, compartment match and non-null class A1. A JAK inhibitor is
*not* equivalent — it hits no member — and an earlier draft of this analysis
conflated the two and rejected STAT3 on mapping grounds. That rejection is
withdrawn.

Stage 4c refuses it on two blocking grounds, neither of which is mapping: target
engagement was never measured at the node's modelled level (pSTAT3 is blotted
under the cytokines, not under the inhibitor; the only inhibitor readout is
fibronectin adhesion), and the decisive experiment is in the HES immortalised
line, which §6.3 makes non-approvable alone. E4 fails separately — no selectivity
profile exists at or above 20 µM for either moiety — and J1 is *unassessable*
rather than failed, because §3.6 states no minimum for `agent_class = biologic`.

**For this unit the distinction matters in both directions.** The engagement
ground is an admission bar and does not by itself block calibration use. The
system ground is also a scientific limitation: the sole experiment with this
reagent is in an immortalised line, and ADOC runs primary cells. Two further
facts survive any improvement to the evidence: the reagent identification rests
on product-name matching, since the source names no catalogue number, making it
an E1/E6 identity judgement; and `compound_claim_blocked` through stromal
`S_STAT3` is mechanically unavoidable, with ERBB2 carried verbatim into the claim
boundary.

**No stronger direct STAT3 reagent is recorded in this repository.** Stattic,
S3I-201, napabucasin, WP1066, cryptotanshinone, STA-21, LLL12, C188-9, TTI-101,
BP-1-102, OPB-31121, niclosamide and ruxolitinib return no hits under
`grep -rni` across `docs/`, `context/` and `config/`; the only adjacent mention
is tofacitinib, inside the quarantined staging narrative, which itself rejects
it as "a JAK inhibitor, not a STAT3-specific probe".

**That is a claim about the repository, not about the literature.** An earlier
draft also asserted that a current literature search found nothing better. No
search record — databases, queries, dates, inclusion criteria, hit counts — was
kept for that sweep, so the claim is not reproducible and is **withdrawn as
stated**. The field-exhaustiveness claims in §5 are accordingly scoped to
**candidates already recorded in this repository**.
Establishing that no better reagent exists in the literature would require a
registered systematic search, which this unit did not perform and which is a
separate unit.

**C12 and PR24 do not conflict; they address different uncertainty axes.**
`docs/experiment_candidate_review_2026-09-22.md` C12 records STAT3 inhibition as
"KEEP as a control, **not as a discriminator**", and its stated ground is
"shared necessity, **not ligand attribution**": because `E_GP130_STAT3` is the
convergence node for LIF and IL-11, blocking it shows that the pathway is
required and cannot say **which ligand** drives it. PR24 scores a different
question — whether `E_CD98_CD9` is a function of `E_GP130_STAT3` alone or also
of `IN_HCG`/`IN_E2` — and a STAT3 veto read on surface CD98/CD9 separates
`CD98-c` on that axis. One arm can be uninformative about ligand attribution and
informative about the CD98 regulation rule at the same time.

Two consequences. C12 is **not** an objection to the PR24 yield and should not
be read as one. And C12's second clause reinforces §7.1 item 1 rather than
competing with it: `E_GP130_STAT3` is `no_assay`, "so the inhibitor and its
proximal readout are both **assay-development items**" — the same prerequisite
the CD98 observation rule names.

### 5.3 SMO antagonist

The model has no reception node, so blockade is applied to `S_NR2F2` directly;
`docs/experiments/stage3_decision_tables.md` records this as "an INTERPRETATION
of the intervention, not a model of it". The `HH-a`/`HH-b` fork does land on
`S_IGFBP1` with opposite predictions, which is a genuine separation on an
existing assay.

It is not promoted for two reasons. The committed model predicts nothing
propagates, so the `HH-a` outcome is "no change anywhere" — indistinguishable
from a failed drug, a wrong dose or poor chip penetration — and the arm is
interpretable only with a GLI1/PTCH1 engagement readout, a new assay class. And
the human evidence base for the fork remains thin, though **less decisively so
than an earlier draft of this section claimed**.

That draft cited a human-ESC experiment in which activating Hedgehog with
recombinant SHH or a Smoothened agonist did not induce FOXO1 or IGFBP1, and
reclassified GAP-014 from untested to "contradicted". **That inference is
invalid and is withdrawn.** The cited design is an *activation* test and bears
on **sufficiency**; `HH-b` asserts that Hedgehog reception is **necessary** for
`S_BMP2`. A failed sufficiency test cannot establish that reception is
unnecessary — the two contrasts are independent, and only an antagonist or
knockdown design speaks to necessity. Correctly stated, the result is that
**Hedgehog activation failed to induce these decidual markers in human ESCs,
while necessity remains untested**, which is exactly what GAP-014 already
records.

So the human-evidence point neither promotes nor demotes the fork; what keeps
`smo_antagonist` out of contention is the engagement problem above, which stands on its
own.

**Provenance of the withdrawn claim, recorded rather than deleted.** The
activation result was taken from a web-search summary during this session; the
full text was **not** inspected, the source is **not registered** in
`context/literature/references.tsv`, and no PDF is held. Independent review
identified the primary article as
`https://pmc.ncbi.nlm.nih.gov/articles/PMC12980961/` and confirmed that it
carries only the activation design. Nothing in this document now rests on it,
and it should be registered and read in full before any future unit relies on
it either way.

The `CONSTRUCTION_ROLE_ONLY` flag on `S_IGFBP1` is **not** disqualifying here, and
an earlier draft implied it was. The same table states that construction-role
data may legitimately inform calibration provided nothing later claims it as
held-out validation, which is this unit's position.

### 5.4 hCG on E2-priming

Recombinant hCG is a biologic rather than a small molecule; it is soluble and
perfusable and so meets the constraint literally, and is reported separately on
that basis.

**Its four Stage-3 usable forks are not attributable to hCG**, and an earlier
draft stopped there, which was the error. They are SEC-a/c, SEC-b/c, SEC-c/d and
SEC-c/e on `E_PAEP` — fork for fork identical to `observe_e2_primed`, which
applies no perturbation — and `IN_HCG` has `logic = IN_HCG` in `network.bnd`,
read by no committed rule. On the Stage-3 metric hCG adds nothing.

`IN_HCG` is read by the `CD98-b` and `CD98-c` variant bodies, and a superseded
draft built a selection on that. **That selection is withdrawn** (header), and
the repository had already settled the point:

> **C10 — hCG → CDH1 / CD98 · DEFER.** "Class gain **1**, on the never-varied-input
> class only, **separating no measured node**. Domínguez 2010 (`REF-008`) already
> lists hCG among four CD98 inducers, so a positive result is not specific …
> `IN_HCG` is one of the two declared-but-unread inputs, so **any rule for it is
> new topology, not a repair**."
> — `docs/experiment_candidate_review_2026-09-22.md`

Three things there defeat the withdrawn argument independently. The separation
is on a node with **no assay** (`E_CD98_CD9` is `no_assay` in every catalogue
arm), so "separating no measured node" is the operative fact. REF-008's **four**
inducers — hCG, E2, LIF and EGF — make neither an hCG-responsive nor an
E2-responsive result specific. And giving `IN_HCG` a consumer is **new topology**,
which is outside what a calibration unit may propose.

The companion disposition for the E2-only half is **C2 — "RESCOPE … drop the HIGH
priority"**, on the ground that `CD98-c` vs `CD98-x` "is separated by `dropout_e2`
and by nothing else", so an E2-priming arm cannot exclude the constitutive class.
`CD98-x` was absent from the withdrawn comparison altogether.

**hCG is therefore not a candidate this document advances.** It is recorded here
because the withdrawn draft advanced it, and because C2 keeps the surface-CD98
**assay build** alive — to be run on the minus-E2 arm, where C2 says it can
actually decide the axis.

## 6. The CD98 variant: unresolved, and what resolving it would require

Under a STAT3 veto the CD98 variants make **different** predictions —
`CD98-a` (committed) `= E_GP130_STAT3` → 0; `CD98-b` `= E_GP130_STAT3 or IN_HCG`;
`CD98-c` `= E_GP130_STAT3 or IN_HCG or IN_E2` → 1 under HT, since `IN_E2 = 1`.

**Where these rule bodies live**, because they are not in any `rule_variants.tsv`
and an earlier draft left that untraceable: `docs/experiments/stage3_decision_tables.md`
table D, rows `CD98-a` to `CD98-x`. `CD98-a` is sourced to `network.bnd` and the
two alternatives to `gate3_candidate_variants_2026-09-16.tsv`, each citing REF-008
for its added inducer — hCG for `CD98-b`, E2 for `CD98-c`. PR24 independently
records the discrimination as `CD98-c@veto:E_GP130_STAT3` in
`docs/identifiability_design/design_yield.tsv`.

**Two withdrawn objections to this measurement, recorded once.** That it is
circular — it is not, the variants make different predictions under the veto.
And that `CD98-c` is already curatable from REF-008, so the experiment has low
value of information; that rested on the DTR005 adjudication row of 2026-09-16
("Nothing blocking. This is curation of an edge the evidence register already
states"), and **that row is superseded** by the full-text verification of
2026-09-17 in the same review's `primary-verification.tsv`:

> "**U4 2026-09-17: NO CANONICAL PROMOTION.** `CD98-c` now has the most direct
> evidence of any member of this family — `IN_HCG` and `IN_E2` are both measured
> inductions of membrane CD98 in primary human EEC in this one paper — **and it
> is still not enough** … the induction is **GRADED (1.2–1.5 fold MFI) against a
> non-zero baseline, so 'or' asserts a sufficiency the data do not show**, and
> competing variants remain plausible — section 5's stated consequence is a
> `rule_variants` FAMILY, not a network fact. **CANDIDATE-EDGE PROMOTION IS
> PENDING AND NOT DONE.**"

The same record notes that `CD98-c`'s third disjunct is weaker still: the paper
measures LIF, not STAT3 activity, so `E_GP130_STAT3` rests on a two-paper chain
and no source tests whether the LIF induction of CD98 is STAT3-dependent.

**So `CD98-c` is genuinely unresolved, and discriminating it carries real
calibration value.** The value-of-information objection is withdrawn. **This is
not a ranking and does not place the STAT3 arm above any other candidate**: it
says only that the objection previously raised against that arm does not hold.
§5.0 records why no comparative ranking is offered, and §7 records the
preconditions on the STAT3 arm rather than its position in a field.

**A third draft then replaced it with a readiness objection, arguing that the
arm "cannot deliver its variant" until a CD98 mapping exists. That conflated two
different things and is also withdrawn.** Readiness is a condition on *when the
experiment may be executed*, not a reason to treat its information value as
zero. An arm whose prerequisite is unmet is **not ready yet**; it is not
worthless, and the distinction matters because the two license different
decisions — the first says *sequence the prerequisite first*, the second says
*drop the candidate*.

The prerequisite is real and is stated as such. Surface CD98/CD9 is a graded
measurement, and the evidence that motivates `CD98-c` is graded too (1.2–1.5
fold MFI against a non-zero baseline), so a Boolean call on it requires **a
pre-registered quantitative observation rule and a demonstration of adequate
dynamic range, fixed before execution**. The repository's precedent for exactly
this is `E_KLF12_HIGH` in `docs/identifiability_experiment_design.md`: a
represented node whose transcript is measurable, which "could constrain [the
node] only behind an independently pre-registered mapping and threshold with
adequate dynamic range." That precedent also records that a criterion can fire
on stateless simulated data, so the rule needs null calibration, not only a
threshold.

**That is an execution precondition on the STAT3 arm, not a deduction against
it.**

## 7. Preconditions, and the operational decision that remains the owner's

### 7.1 Preconditions

Conditions on execution, not on value, each checkable before any chip is
committed.

**Shared by any CD98-reading arm — one precondition:**

1. **A pre-registered CD98 observation rule**: a quantitative mapping from
   surface CD98/CD9 MFI to the Boolean node, with demonstrated adequate dynamic
   range and null calibration, fixed before execution, per the `E_KLF12_HIGH`
   precedent (§6). C2 keeps this assay build alive and directs it at the
   minus-E2 arm.

**On the STAT3 arm — that one, plus four more.** Items 2–5 are
the unresolved conditions of the governing Stage 4c refusal, listed in full
because an earlier draft gave three and called them exhaustive:

2. **Abolition-grade engagement**: a pSTAT3 or STAT3-target-program readout
   under this construct at 20 µM in a §6.3-qualifying primary system, reported
   as **abolished** rather than reduced. Closes both Stage 4c blocking grounds
   in one experiment.
3. **A J1 decision for `agent_class = biologic`.** §3.6 of
   `docs/stage4b_direct_admission.md` states a minimum source for a small
   molecule, an antibody and a knockdown or knockout, and **states none for a
   biologic**. J1 is therefore *unassessable*, not failed, until the owner
   defines it. Recorded in Stage 4c as a gap in the frozen contract, not filled.
4. **A selectivity profile covering both moieties** — the STAT3-binding
   phosphopeptide **and** the P3-AHNP/HER2 carrier — at or above 20 µM. None
   exists in the repository for either moiety.
5. **A declaration** naming both STAT3 and ERBB2 in `known_target_entities`,
   with the supplier record registered as evidence so identity and profile
   sources resolve.

**C12 is not a sixth condition.** It records STAT3 inhibition as a control
rather than a discriminator *of ligand attribution*, which is a different axis
from the CD98 rule PR24 scores; §5.2 reconciles them. Its operative contribution
here is its second clause — `E_GP130_STAT3` is `no_assay`, so the inhibitor and
its proximal readout are assay-development items, which is item 1 again.

**Stage 4c admission is not being closed here**, for any arm. No declaration,
ledger approval or `direct_supported_effect` row is created by this document, so
**direct model execution of any such arm remains barred** until the relevant items
above are met through the Stage 4b process. `compound_claim_blocked` through
stromal `S_STAT3` survives any of them and is carried verbatim into the claim
boundary.

### 7.2 The operational decision

Precondition 1 is an assay-qualification unit and does not itself return a model
variant. The STAT3 arm needs it **and** a reagent-feasibility
experiment (2), **and** three governance items (3, 4 and 5) — five units
against one budget, before any calibration value is returned. C12 is not a
further cost against it: it speaks to ligand attribution, a different axis from
the CD98 variant PR24 scores (§5.2).

**If the single shot cannot absorb that, the owner may reasonably conclude
`NO_DRUG_ONLY_EXPERIMENT_WORTH_THE_ONE_SHOT` operationally.** This analysis has
no basis for costing units against a budget it cannot see, and does not pretend
to.

### 7.3 What a ranking unit would have to settle

Not "what would displace X" — no X is established (§5.0). The open questions a
scoped unit would answer, in order:

- **How do the two candidate lists correspond by identifier?**
  `docs/experiment_candidate_review_2026-09-22.md` reviewed 17 owner-supplied
  candidates (C1–C17); `context/experiments/calibration_candidates.tsv` carries
  14 (`CAND-01`–`CAND-14`). No repository artifact formally maps them, so neither
  can currently be treated as a complete *enumerated* field — though the subject
  overlap recorded in §5.0 means the review's dispositions already constrain much
  of the ground.
- **Does that review still govern the ground it does cover?** Any new ranking
  either builds on its dispositions or states what has changed since.
- **Can an applicable observation checkpoint be registered** for a CD98 readout
  on v0.6.0? Without one, no CD98-reading arm can be scored at a declared
  endpoint at all (§5.0 item 3).
- **Is the CD98 graded-to-Boolean mapping achievable** at REF-008's 1.2–1.5 fold
  dynamic range (§6)? If not, every CD98-reading candidate falls together.
- **Does lifting the transfection constraint** reopen the HAND2 arm, which PR24
  already scores with no change to its arithmetic?

## 8. Not done here

**No ranking is established and no experiment is authorised or scheduled.** §5.0
records why this document does not rank the candidates and what a unit that does
would have to fix first; §7 records the preconditions on the STAT3 arm. Choosing
an arm is the owner's decision. `docs/experiment_candidate_review_2026-09-22.md`
governs **the candidates it covers** — its own C1–C17 list — until a unit scoped
to revisit it says otherwise; it is not a complete adjudication of the field, and
§5.0 records why no document currently is.

No model, rule variant, entity-map reading or frozen artefact is modified. No
Stage 4b declaration or approval is created, and §4.3's alternatives are
proposals only. The `S_HAND2` finding in §4.2 is an evidence audit; acting on it
is a separate model-reading decision with its own adjudication.

Claims this document made and has withdrawn are recorded where they were made —
the HAND2 variant called vacuous (§4.2), the readiness-as-worthlessness argument
(§6), and the hCG headline (header) — rather than restated here.
