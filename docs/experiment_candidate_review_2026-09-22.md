# ADOC DT — the 17 perturbation / measurement candidates, reviewed against the repository

**Date: 2026-09-22.** Review and revision of an owner-supplied planning handoff
listing 17 candidate experiments. The original list's candidate numbering is
preserved throughout so the two can be read side by side.

**Status: planning analysis.** No executable file changes. Nothing here promotes a
candidate node, adopts a rule, creates an objective or edits a condition `.cfg`.
Every computed number below is read from a committed artifact or recomputed from
the committed `.bnd` in this session, and the source is named each time.

---

## 0. The three findings that reorder the list

The list ranks candidates by biological interest, material availability and cost.
Those matter. But the repository already computes the two quantities that decide
whether an experiment can *identify* anything, and applying them moves several
items a long way.

### 0.1 The platform has two usable assay nodes — one constraint and one diagnostic

`config/observation_model_map.tsv`, read through
`dt_adoc.experiments.variant_discrimination._readout_tier`, classifies all 59
model nodes:

| tier | nodes |
|---|---|
| `usable_assay` | **`E_PAEP`** and **`S_IGFBP1`** |
| `mapped_composite_not_validating` | `S_PRL` (provisional), `OUT_EPITHELIAL_RECEPTIVE`, `OUT_STROMAL_DECIDUALIZED` |
| `no_assay` | **the other 54** |

**The two `usable_assay` nodes are not equivalent, and calling both "validating"
overstates one of them.** `E_PAEP` is an `active_constraint` with
`objective_treatment = pass_fail_feasibility_filter`: `OM-001` calls it *"the
primary feasibility gate; a violation excludes the candidate from the retained
ensemble"*. `S_IGFBP1` is an `active_diagnostic` with
`objective_treatment = non_inversion_diagnostic_secondary_ranking`, and `OM-002`
says it *"never excludes a candidate from the retained ensemble on its own"* — it
flags an inversion and contributes to secondary ranking. So the accurate summary
is **one validating constraint (PAEP) and one active diagnostic (IGFBP-1)**, not
two validating readouts. (`docs/stage3_experiment_selection.md` §3 writes "the
only two nodes the observation layer can validate" for both; that is loose, and
this document does not follow it.)

`input_tables/adoc_secreted_proteins.tsv` contains exactly three analytes —
IGFBP-1 (30 rows), PAEP (14), PRL (18) — and nothing else. **Every readout the
list proposes is `no_assay`**: pSTAT3, surface CD98, CD9, ITGA2, nuclear FOXO1,
MUC16/MUC1 immunofluorescence, PTCH1/GLI1, α-DG-N, pSMAD1/5/8, HAND2.

That does not make them bad ideas. It means each one is **an assay-development
project first and a discriminating experiment second**, and the list's cost
column — repeatedly "< EUR 1k, difficulty LOW-MEDIUM" — prices the second and
omits the first. `docs/stage3_experiment_selection.md` §3 names the classes
involved: surface CD98 is a cell-associated protein assay, pSTAT3 a lysate assay,
α-DG-N a shed-ectodomain ELISA, GLI1/PTCH1 a transcript assay. None exists on
this platform today.

### 0.2 The aliasing is worse under the planned design than it is in the model

Two different numbers, both from
`docs/design_alias/node_design_classes.tsv` (computed against
`adoc-literature-superset-v0.4.0`; **re-verified in this session to be identical
for the committed v0.5.0** — 59 labels, 19 free variables, 35 distinct Boolean
functions, and the same eight global classes):

**Global Boolean classes** — what the *rules* cannot distinguish, whatever you do:

| n | members |
|---|---|
| 9 | `E_ANXA2_ACTIN, E_DAG1_CLEAVED, E_HBEGF, E_ITGAVB3_5, E_MUC1_SLEX, E_PAEP, E_PC6, E_SECRETORY_STATE, E_SPP1_EXPR` |
| 6 | `OUT_STROMAL_DECIDUALIZED, S_DECIDUALIZED, S_IGFBP1, S_PRL, S_SPP1, S_TAZ_ECM` |
| 5 | `E_IHH, E_PGR, S_BMP2, S_NR2F2, S_PGR` (`AC03`) |
| 3 | `E_CD98_CD9, E_GP130_STAT3, E_LIF` (`AC04`) |
| 3 | `E_DAG1_FULL, E_MUC1_BARRIER, E_PODXL` |
| 2 | `IN_cAMP, S_PKA` · `E_CDH1_APICAL, IN_EMBRYO_CONTACT` · `E_RECEPTIVE_SURFACE, OUT_EPITHELIAL_RECEPTIVE` |

**Design classes** — what the four *planned arms* (untreated, hormone-treated,
+mifepristone, +anti-SPP1) cannot distinguish. 19 classes for 59 nodes, and the
largest is far worse than any global class:

| n | members |
|---|---|
| **22** | the whole epithelial secretory block **plus** all of `AC03` **plus** the whole stromal decidual block, **plus** `S_HAND2` and `X_MECHANICAL_PERMISSIVE_ECM` |
| 5 | **`IN_E2, IN_PROGESTIN, IN_XAV939, IN_cAMP, S_PKA`** |
| 5 | `IN_EMBRYO_CONDITIONED_SIGNAL, IN_ER_STRESS_EXCESS, IN_HAND2_LOSS, IN_HCG, IN_HIGH_ECM_STIFFNESS` |
| 5 | `E_CD98_CD9, E_GP130_STAT3, E_LIF, E_RECEPTIVE_SURFACE, OUT_EPITHELIAL_RECEPTIVE` |
| 4 | `E_CDH1_APICAL, IN_EMBRYO_CONTACT, IN_EMBRYO_PRESENT, IN_TROPHECTODERM_COMPETENT` · `E_DAG1_FULL, E_MUC1_BARRIER, E_PODXL, S_FGF_MITOGENIC` |
| 2 | `E_ESTROGENIC_PROLIFERATION, IN_MIFEPRISTONE` |

The second row is the whole problem in one line: **the four protocol agents are
experimentally indistinguishable from one another**, because the protocol always
moves them together. That is why single-agent dropouts are a different class of
experiment from everything else on the list, and it is a fact about the *design*,
not about the biology.

### 0.3 The repository already ranked 112 candidate fifth arms, and the list's two top-priority new-chip experiments are not among the winners

`docs/design_alias/candidate_fifth_arms.tsv` evaluates 112 candidate fifth arms
for design-class gain and for whether the split lands on a node the observation
layer can read. For the arms this list proposes:

| arm | list item | class gain | classes split | separates a **measured** node? |
|---|---|---|---|---|
| **minus E2** | **absent from the list** | **3** | `22→13/9`, `5→1/4`, `4→3/1` | **yes** — `E_PAEP` and `S_IGFBP1` |
| **minus cAMP** | C4 | **2** | `22→15/7`, `5→3/2` | **yes** — `E_PAEP` and `S_IGFBP1` |
| HAND2 loss | C6 | **5** (highest) | five classes, incl. `AC04 5→3/2` | **no** |
| +ER stress | — | 2 | `22→21/1`, `5→1/4` | no |
| +ECM stiffness | — | 2 | `22→21/1`, `5→4/1` | no |
| minus progestin | — | 2 | `5→4/1`, `2→1/1` | no |
| minus XAV939 | C14 | **1** | `5→4/1` only | no |
| +hCG | C10 | 1 | `5→4/1` only | no |
| +embryo-conditioned signal | — | 1 | `5→1/4` only | no |

`docs/coupling_adjudication.md` §5 states the consequence in one sentence: *"by
raw class gain the best fifth arm is HAND2 loss (+5); and by separation of the two
measured analytes **only minus-E2 and minus-cAMP score at all**."*

And `docs/stage3_experiment_selection.md` §2, from the independent
`build-stage3-design` computation, overturns four more of the list's positions
directly:

- **anti-LIF + pSTAT3 separates nothing** (C3, ranked HIGH). `GP130-a` and
  `GP130-b` agree in every arm where IL-11 is not supplied, so neutralising LIF
  cannot tell them apart; the separation needs supplied IL-11, and the opposite
  separation needs anti-LIF **and** IL-11 together. The fork's own readout,
  `E_GP130_STAT3`, is `no_assay`.
- **Surface CD98 under E2-only cannot close the CD98 axis** (C2, ranked HIGH).
  `CD98-c` vs `CD98-x` is separated by `dropout_e2` **and by nothing else** —
  under E2-only, with or without hCG, the two predict the same thing. And
  `E_CD98_CD9` is `no_assay`, so every CD98 pair is separable in many arms and
  decidable in none.
- **BMP receptor inhibition separates nothing** (C13). It clamps `S_BMP2`, which
  the committed rules already make necessary for `S_DECIDUALIZED`; every class
  predicts the same loss. It confirms a rule rather than choosing between rules.
- **PC6 knockdown separates nothing** (C7). Only the cleavage-resistant substrate
  does, and only at `no_assay` and `mapped_composite` nodes.
- **anti-SPP1 propagates to no maternal node at all** (C15) — the computed form
  of `set_alone_no_shared_readout`. Note also that anti-SPP1 is **already a
  planned arm**, `hormone_treated_anti_spp1`, carrying no recorded observation.

---

## 1. Four tracks, not one list

The list's central design principle — *targeted perturbation + proximal
mechanistic readout, over perturbation + distant endpoint* — is right, and every
revision below preserves it. What it needs is one distinction it does not make.
The 17 candidates are doing four different jobs, and they compete for different
budgets:

**Track A — de-aliasing.** Creates a network state the protocol never creates, and
the resulting split lands on one of the two `usable_assay` nodes. Shrinks a design
class. *Currently only two candidates qualify: minus-E2 (absent from the list) and
minus-cAMP (C4)* — and note what each half buys, per §0.1: a `E_PAEP` separation
can exclude a candidate from the retained ensemble, while an `S_IGFBP1`
separation ranks and flags inversions but excludes nothing on its own.

**Track B — assay development.** Turns a `no_assay` node into a readable one.
Resolves nothing by itself; every Track-A experiment of the future depends on it.
*C1, C2, C3's pSTAT3/CD98, C5's PTCH1/GLI1, C7, C8, C9, C11, C12, C13 are all
mostly this.* Judge them by which node they would make readable and how many
forks that node sits on — **not** by whether the perturbation is interesting.

**Track C — falsification.** Tests whether a committed rule is wrong. Can remove
a rule; cannot choose among rules, so it scores ~0 on class gain by construction.
*C14 (XAV939) is the clean example, and it is a good experiment mis-scored as a
weak one.*

**Track D — evidence registration on archived material.** No chip. Produces
catalog evidence and provenance, not identifiability. *The first steps of C1, C7,
C8, C9 and C15.* Cheap and genuinely useful, provided nobody later mistakes the
output for a calibration constraint.

A candidate can sit in two tracks; several do. The failure mode the list is
exposed to is scoring a Track-B item on a Track-A scale.

---

## 2. Corrections to the list's own preamble

Six of the seven constraints in the original preamble are correct and should be
kept. Two are now **done**, and one needs a correction.

| # | original constraint | status |
|---|---|---|
| 1 | repair readout leakage before de-aliasing PRL/IGFBP1 | **still binding.** `OUT_STROMAL_DECIDUALIZED = S_DECIDUALIZED and S_PRL and S_IGFBP1`; the marker conjuncts **change the output in 0 of 524,288 assignments** — absorbed in all of them — so the alias is what keeps the conjunction harmless. Verified this session. |
| 2 | PC6 supports αVβ5, not αVβ3 | **correct, and now registered** — Paule 2012 is `REF-089`, ledger row `PIF-013`. |
| 3 | `E_ITGAVB3_5 = E_LIF or E_HBEGF` is a no-op | **correct, verified** — Boolean-identical to the committed rule, because `E_HBEGF ≡ E_SECRETORY_STATE ≡ E_ITGAVB3_5`. |
| 4 | FOXO1: re-adjudicate; likely catalog-only; Labied may be more relevant | **DONE, 2026-09-22.** `S_FOXO1` moved `WAIT_FOR_EXPERIMENT → RETAIN_CATALOG_ONLY`, first failing criterion `5(2) → 5(4)`. Labied 2006 is `REF-078`. **See §4 C8 — the unblock condition changed, and that changes what to run.** |
| 5 | MUC1 is not a simple sign flip; MUC16 may be cleaner | **correct, and now registered** — Meseguer `REF-085`, Gipson `REF-086`. One numeric correction: Gipson puts MUC1 on *uterodomes* in **4 of 12** receptive samples, not 12/12; MUC16 is absent from uterodomes in 12/12. The two figures are about different structures. |
| 6 | SOFIA-STR-001 needs correction | **DONE, 2026-09-22.** Status narrowed `verified → verified_by_source_file`; the manuscript's wording is preserved and quoted, and the row no longer asserts it as an observation of the canonical data. |
| 7 | LIF abundance alone is insufficient; measure pSTAT3 and CD98 | **the biology is right and the experiment still does not separate the fork.** See §0.3 and §4 C3. CD98 is indeed downstream, not the LIF receptor. |

---

## 3. Two things the cost model must include

**Assay development is the real cost.** A "< EUR 1k" multiplex panel on archived
medium (C1) is six analytes this platform has never measured. That is worth
doing — it is the cheapest way to create new measurement classes — but it should
be budgeted and scheduled as assay development, with a failure mode, not as a
cheap screen that might happen to answer something.

**Independent-unit provenance is the silent tax.** `SOFIA-COMM-005`: the
column-to-chip and column-to-patient mapping for IGFBP-1 and PRL is **LOST**, not
merely unverified; `config/adoc_chip_donor_provenance.tsv` records
`independent_biological_unit = no` for the chips, with donor identity unknown.
Every fraction in the existing data is therefore an unpaired group comparison. **A
new arm that does not capture chip → donor mapping at collection inherits the same
ceiling and cannot support a patient-level claim** — which is the whole point of a
digital twin. This costs nothing to fix prospectively and cannot be fixed
retrospectively. It belongs in the protocol of every candidate in the list.
(`GAP-008`.)

---

## 4. The 17 candidates, item by item

Verdict key: **KEEP** (unchanged) · **RESCOPE** (good, wrong track or wrong claim)
· **DEFER** (right later, wrong now) · **RETIRE** (superseded or computed
uninformative).

### C1 — retrospective frozen outlet-medium panel · **KEEP, rescope to Track B/D**
`GAP-001` in part. The reasoning is sound and this should still be first: it is
the only item that costs no chip and no embryo. Two changes. (i) It is assay
development, not a screen — six new analyte classes. (ii) State the decision rule
*before* running it, or it becomes a fishing expedition: a ligand found in the
right compartment moves a node from "not known to be present" to "present", which
is catalog evidence and **not** a calibration constraint. Add PRL/IGFBP-1/PAEP
re-runs on the same aliquots as the assay-transfer control — that is the only way
to know a new panel is comparable to the existing series.

### C2 — E2-only → surface CD98 · **RESCOPE to Track B; drop the HIGH priority**
Computed: `CD98-c` vs `CD98-x` is separated by **`dropout_e2` and by nothing
else**, so E2-only cannot exclude "CD98 is simply constitutive", which is the most
likely explanation of a positive result. `E_CD98_CD9` is `no_assay` in every arm
of the catalogue. Also relevant, now registered: Domínguez 2010 (`REF-008`) reports
CD98 induced by hCG, 17β-estradiol, LIF **and** EGF — four inducers, so an
E2-responsive result would not be specific either. Keep it as the **assay
build** for surface CD98, and run the assay on the minus-E2 arm, where it can
actually decide the axis.

### C3 — anti-LIF / LIFR blockade · **RESCOPE; remove from the top tier**
Computed: `GP130-a` and `GP130-b` agree in every arm without supplied IL-11, so
**anti-LIF separates nothing**. The separation needs supplied IL-11; the opposite
separation needs anti-LIF *and* IL-11 — the two-perturbation design the project
avoids. The collaborator's point stands and is the useful residue: if this is run,
target engagement must be read (pSTAT3), because a null is otherwise
uninterpretable. Treat as Track B for pSTAT3 + surface CD98, sequenced after C1
establishes whether endogenous LIF and IL-11 are even present.

### C4 — full cocktail minus cAMP · **KEEP, promote to joint first place**
One of exactly two arms that separates a measured node. Class gain 2: splits the
22-node class `15/7` and the input class `5→3/2`, landing on `E_PAEP` and
`S_IGFBP1`. Two refinements. (i) **`S_PRL` is `mapped_composite_not_validating`
(provisional)** — so "PRL and IGFBP1 separately" only half-lands, and the PRL half
cannot validate a node today. Read it, but do not plan a conclusion on it. (ii)
The list's "do not automatically add EPAC as a Boolean node from a partial
phenotype" is exactly right and should be kept verbatim.

### C5 — SMO / Hedgehog inhibition · **KEEP as written, with its caveat strengthened**
This is `GAP-014`, stated there almost word for word. Harman 2011 is now
`REF-088`/`PIF-012` and explicitly does **not** close it: mouse, only a 49% Smo
reduction so not a necessity test, day-7 implantation site number unchanged, and
NR2F2 and HAND2 never measured anywhere in the paper. The list's "without
PTCH1/GLI1 the experiment becomes much less informative" is right and understated:
`docs/stage3_experiment_selection.md` §6 records that `smo_antagonist` separates
**one** class pair on one outlet, the committed model predicts nothing propagates,
so a null is confounded with failed target engagement — and it must buy a
GLI1/PTCH1 transcript assay to escape that. Runner-up, not a contender.

### C6 — HAND2 / FGF axis · **KEEP, and re-label: highest structural value, unreadable**
`GAP-010`. The **largest class gain of any candidate arm (+5)**, splitting five
classes including the CD98/LIF class `5→3/2` — and it **separates no measured
node**. `docs/identifiability/proposed_panel.tsv` ranks it step 1 on pure
structure, and stage-3 overruled it on assay availability. That is the honest
framing: C6 is the best experiment the platform cannot currently read. It becomes
first-rate the moment an epithelial-state readout exists. Keep the list's
knockdown-optimisation caveat.

### C7 — PC6 / DAG1 protein-state split · **RESCOPE to Track B/D**
Computed: **PC6 knockdown separates nothing**; only the cleavage-resistant
substrate does, and only at `no_assay` and `mapped_composite` nodes. So the
archived-material mapping step is the valuable half and the inhibition step is
not yet worth a chip. The list's own critical correction — do not use this for a
generic `PC6 → E_ITGAVB3_5` edge — is correct and now has a registered citation
(`REF-089`). Add: `E_PC6` and `E_DAG1_CLEAVED` both sit inside the 9-member
epithelial class, so neither is separable from `E_SECRETORY_STATE` by any arm
that does not first break that class.

### C8 — AKT / FOXO1 nuclear localisation · **KEEP, and the unblock condition has changed**
**This is the item most changed by the 2026-09-22 registration.** The list says
"do not treat Kang 2022 alone as sufficient; Labied 2006 may be more relevant" —
both correct, and both now resolved. `S_FOXO1` is `RETAIN_CATALOG_ONLY`, first
failing criterion `5(4)_delta_and_alias`. The determinant question is **closed**:
Labied 2006 supplies it, measured as localisation, under MPA and 8-br-cAMP.

What is missing now is different, and it names the experiment: **an
ADOC-addressable input that separates `S_FOXO1` from `S_DECIDUALIZED`.** Labied
tested MPA and cAMP and tested **neither E2 nor XAV939**. So the discriminating
measurement is nuclear/cytoplasmic FOXO1 fractionation **across arms that vary E2
or XAV939** — which means C8's assay run on the minus-E2 arm (§5) or on C14.
Archived-material mapping first, as the list says; but the prospective version is
C8 × (minus-E2 **or** minus-XAV939), not C8 alone, and not an AKT perturbation.
The relation is conditional, not conjunctive: `S_DECIDUALIZED` reads neither E2
nor XAV939, so those are the two cocktail agents that could separate `S_FOXO1`
from it, and either arm works *if* FOXO1 localisation responds to that agent —
which is the unknown. **A null in one does not clear the other.** Run it on
minus-E2 first, because that arm is already frozen for independent reasons (M1);
keep minus-XAV939 as the fallback rather than as a second requirement.

### C9 — MUC16 / MUC1 barrier module · **KEEP, with one number corrected**
`GAP-004` + `GAP-011`, both open and both stated in those terms. The list's
critical caveat — abundance ≠ glycoform ≠ localisation ≠ contact-dependent
clearance — is exactly the repository's position and should be kept verbatim.
Correction to carry: Gipson 2008 reports MUC1 on **uterodomes in 4 of 12**
receptive samples (luminal surface in 12/12), against MUC16 absent from uterodomes
in 12/12. Structural note: `E_MUC1_BARRIER` sits in the 3-member class with
`E_DAG1_FULL` and `E_PODXL`, and `E_MUC1_SLEX` sits in the 9-member epithelial
class — so the two MUC1 nodes are already in *different* classes, which is the
model-side reason the split is representable at all.

### C10 — hCG → CDH1 / CD98 · **DEFER**
Class gain **1**, on the never-varied-input class only, separating no measured
node. Domínguez 2010 (`REF-008`) already lists hCG among four CD98 inducers, so a
positive result is not specific. The list's caveat against collapsing all
embryo-conditioned signal into hCG is correct and worth keeping — the corpus
carries both pro-adhesive and anti-adhesive embryo signals. Note that
`IN_HCG` is one of the two declared-but-unread inputs, so any rule for it is new
topology, not a repair.

### C11 — IL-11 ligand split · **KEEP the sequencing, lower the expectation**
The list's own sequencing (measure endogenous LIF/IL-11 in frozen medium first) is
the right instinct and is what C3's computed null argues for. But the design that
actually separates `GP130-a` from `GP130-b` is **supplied IL-11**, and the
opposite separation needs anti-LIF **and** IL-11 together. So C11 is not a
follow-up to C3 — it is the half of the pair that carries the information.

### C12 — STAT3 inhibition · **KEEP as a control, not as a discriminator**
The list's own caveat is correct and complete: shared necessity, not ligand
attribution. Add that `E_GP130_STAT3` is `no_assay`, so the inhibitor and its
proximal readout are both assay-development items.

### C13 — BMP receptor / SMAD inhibition · **RETIRE as a discriminator**
Computed: **separates nothing.** It clamps `S_BMP2`, which the committed rules
already make necessary for `S_DECIDUALIZED`; every class predicts the same loss.
It confirms a rule. The list's own caveat says nearly this; the computation makes
it definite. The `S_BMP2 ≡ S_PGR` degeneracy is real and important — `PIF-011`
records it as falsified with no replacement — but it is an **evidence-acquisition**
problem, and downstream inhibition is not the acquisition.

### C14 — XAV939 dropout · **KEEP, and re-label as Track C, paired with C8**
Class gain **1**, on the input class only, separating no measured node — so as a
de-aliasing arm it is correctly ranked LOW. But that is the wrong scale for it:
it is a **falsifier**, and the list says so itself. `IN_XAV939` is in the
protocol and has no model image; a strong effect falsifies the zero-rule
treatment, which no amount of class gain measures. Two upgrades: (i) pair it with
C8's FOXO1 localisation readout, which is the one arm Labied 2006 leaves open for
`S_FOXO1`; (ii) it is the cheapest arm in the list — one reagent omitted, no drug,
no antibody, no target-engagement failure mode. The list's "a positive result does
not by itself justify a WNT module" should be kept.

### C15 — anti-SPP1 downstream challenge · **RETIRE from the maternal programme**
`IN_ANTI_SPP1` is `set_alone_no_shared_readout`: it **propagates to no maternal
node at all**. It is also already a planned arm carrying no recorded observation.
The list's own priority ("LOW for immediate maternal calibration") is right; what
it does not say is that the arm exists on paper and is unreadable as declared.
Keep the frozen-medium SPP1 measurement (Track D, part of C1) and let the
interface question wait for Gate 6, which chooses the embryo-challenge arm after
the maternal panel with no molecule privileged in advance.

### C16 — COX / prostaglandin route · **KEEP as written**
`GAP-012`, stated there in more detail than here, including the factorial
progestin × hCG design and the PTGFR blockade control. The list's caveat against
creating COX2/PGE2 topology to accommodate the candidate is exactly the
repository's position. Note the one corpus paper that would have anchored a
BMP2 → PGE2 route, Zhang 2020, is **retracted** and recorded as
`registration_decision = excluded_retracted`; do not let a fresh search re-admit it.

### C17 — TLR3 / poly(I:C) · **RETIRE from this programme**
The list's own reasoning is sufficient and correct. Nothing to add except that it
maps to no gap and no node, so there is no model-side statement it could confirm
or refute.

---

## 5. Five things missing from the list

**M1 — cocktail minus E2, the arm the repository already chose.** Absent from all
17 items, and it is the frozen prospective design in
`docs/stage3_experiment_selection.md` §12 (status: FROZEN 2026-09-17, may be
executed or superseded but not edited). Days 0–2 unchanged; days 2–6 MPA + cAMP +
XAV939 with **E2 omitted**; read PAEP top, IGFBP-1 and PRL bottom. Highest class
gain of any arm that lands on a measured node (3; splits the 22-node class
`13/9`), separates the committed rule from three of its four rivals, **zero new
assay**, one reagent omitted, no target-engagement failure mode, and all four
cells of the PAEP × IGFBP-1 outcome table license a distinct action. Whatever else
is run, this is the comparator everything else should be scored against.

**M2 — the `E_PAEP` interpretation rule. Already adjudicated; what is left is a
cross-reference.** An earlier draft of this document listed registering the
`E_PAEP` binarisation threshold as a missing zero-cost prerequisite. **That was
wrong, and it is corrected here:** it reads `docs/stage3_experiment_selection.md`
§3's problem statement and misses §9.1's resolution. The owner adjudicated it on
**2026-09-17**, adopting option (b) — **no external glycodelin threshold is
transferred**, and in its place a pre-registered **three-band ordinal rule**,
fixed before the run:

> **ON** — the value lies in or above the full-cocktail band (178,072–585,609
> pg/mL); **OFF** — in or below the E2-only band (10,165–25,470 pg/mL);
> **indeterminate** — anything between, which is an admissible verdict and not a
> tie to be broken.

That settles the E2-only call (`OFF`) and the minus-E2 call, and §9.1 adds the
constraint that **the rule must never be fitted from the minus-E2 result**. No new
number is wanted and none should be proposed.

What *is* left is small and is documentation coherence, not adjudication:
`OM-001`'s `claim_ceiling` in `config/observation_model_map.tsv` still reads *"The
`E_PAEP` OFF/ON binarization threshold is implicit and unrecorded"* and does not
reference §9.1, so a reader of the config alone would still think the question is
open. Point it at the frozen rule. Not done here — it is a config edit against a
frozen artifact and belongs to whichever unit next touches that file.

**M3 — the leakage repair is a repository action, not an experiment.** The list's
preamble constraint 1 is right, but it is listed as a caution rather than as work.
It is the first item in the committed order of operations
(`docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md` §6) and it costs no
material at all.

**M4 — prospective donor/chip provenance capture.** See §3. Free now, impossible
later, and it caps every patient-level claim the twin is for.

**M5 — an explicit assay-development roadmap, ranked by what each readout would
make decidable.** Given §0.1, the highest-leverage question is not "which
perturbation" but "which `no_assay` node, made readable, changes the most
verdicts".

Three different things are worth keeping apart here, and it is easy to run them
together:

- **An arm splits classes.** Adding a condition changes the response profile, so
  it can move two nodes out of the same design class. Only arms do this.
- **A readout makes a split decidable.** It cannot create a separation; it
  determines whether a separation the model already predicts can be read. This is
  what `readout_tier` measures, and it is why `E_CD98_CD9` is separable in many
  arms and decidable in none.
- **A second readout inside one class tests whether the class is real.** Nothing
  measured can split a *global* Boolean class — those nodes are the same function,
  so the model predicts the same value for every member under every input. What a
  second member's assay buys is **falsification**: if two members of a class
  disagree experimentally, the shared rule is wrong. That is the most valuable
  thing the 9-member epithelial class could yield, because `E_PAEP` is already
  readable and a second independent epithelial readout in that class turns an
  untested identity into a testable one.

On the current structure the two highest-value builds are therefore a **second
epithelial-state readout inside the 9-member class** (falsifies or sustains the
largest identity in the model) and a **stromal FOXO1 localisation readout** (C8 —
the named unblock for `S_FOXO1`, and the one whose target node has an explicit
open condition). Those two would change the ranking of half this list.

---

## 6. Revised order of operations

**Now, costing nothing:**
1. Readout-leakage repair (**M3**).
2. Add donor/chip provenance capture to the protocol template (**M4**).
3. Point `OM-001`'s `claim_ceiling` at the frozen three-band rule (**M2**) — a
   cross-reference, not a decision; the rule itself was adjudicated 2026-09-17.

**Then, on existing material (Track D, no chip):**
4. C1 frozen-medium panel, with a decision rule written first and PRL/IGFBP-1/PAEP
   re-runs as assay-transfer controls.
5. C8, C9, C7 archived-material mapping — in that order, because C8's target is
   the only one of the three with a named model unblock.

**Then, one arm (Track A):**
6. **M1 minus-E2** — the frozen design, and the only arm with class gain 3 on a
   measured readout at zero assay cost. Carry C8's FOXO1 fractionation on it if
   that assay exists by then; it is the first half of the `S_FOXO1` unblock.
7. **C4 minus-cAMP** — the only other arm that separates a measured node. Run
   second, or in parallel if two arms are affordable; they split the 22-node class
   differently (`13/9` vs `15/7`).
8. **C14 minus-XAV939 with C8's FOXO1 readout** — cheapest arm in the list, and
   the fallback half of the `S_FOXO1` unblock. Only if the same readout on the
   minus-E2 arm (step 6) returns a null; see §4 C8 for why the two are
   alternatives and not a pair.

**In parallel, as a funded track (Track B):**
9. Assay development for a second epithelial-state readout inside the 9-member
   class, and for stromal FOXO1 localisation (**M5**) — which is what C2, C3, C5,
   C6, C11 and C12 are all actually waiting on.

**Later or elsewhere:** C5 (needs GLI1/PTCH1 first), C6 (needs an epithelial
readout first), C10, C16; C13, C15 and C17 retired from this programme.

---

## 7. What this document does not do

It does not supersede `docs/stage3_experiment_selection.md`, whose §12 design is
frozen and whose §9 owner adjudications stand. It proposes no rule, node, edge,
input, rate, threshold or phenotype, and adopts nothing. Where it quotes a number
it names the artifact; where it recomputes one — the v0.5.0 class structure, the
0-of-524,288 absorption, the identity of the v0.4.0 and v0.5.0 global classes —
it says so. A candidate being structurally useful is not a reason to promote the
topology it would test, and nothing here should be read as doing so.
