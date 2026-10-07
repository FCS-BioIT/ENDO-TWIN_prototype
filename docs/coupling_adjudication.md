# Which of v0.4's node merges are biologically defensible?

Status: **adjudication, 2026-09-16.** Claim level: `structural` + `curation`.
No model, rule, protocol, calibration or evidence file was changed to produce
it. Nothing here was simulated. The four absorption facts below are exhaustive
enumerations over `network.bnd`; everything else is a judgement, labelled as
one, with its evidence and its reopening condition.

Artifacts. The judgement is curated in
[`config/coupling_adjudication.tsv`](../config/coupling_adjudication.tsv)
(59 rows, one per model node). The **separability** verdict beside it is
derived, never curated. Both are joined into
[`docs/identifiability/node_classification.tsv`](identifiability/node_classification.tsv)
by `src/dt_adoc/reporting/coupling.py` as four columns —
`coupling_adjudication`, `coupling_evidence_ids`, `perturbation_separability`
and `merged_with_catalogued_targets` — and guarded by
`tests/unit/test_coupling_adjudication.py`.

---

## 1. Why a fourth column was needed

`docs/identifiability_analysis.md` already partitions the 59 named nodes three
ways — 59 labels → 35 distinct Boolean functions (`P_global`) → 19
design-distinguishable states (`P_design`) — and already separates *who* caused
each merge: the rules, or the arms. That distinction is the difference between a
model repair and a protocol change, and it is the most useful thing the analysis
says.

What it does not say is whether a merge the rules force is **biologically
defensible**. Two nodes can be one Boolean function because the abstraction is
right, because nothing available decides, or because the encoding asserts an
identity the evidence contradicts. Those three call for deletion, for patience
and for repair respectively, and the existing partitions treat them alike.

## 2. The vocabulary

| Verdict | Meaning | Count |
|---|---|---:|
| `ARTIFICIALLY_COUPLED` | the rules force an identity the evidence contradicts, or one that makes a distinction the model must be able to draw unreachable | **22** |
| `BIOLOGICALLY_COLLAPSED` | the rules make them one function and that is defensible at this level of description | 4 |
| `UNIDENTIFIED` | the rules make them one function and nothing available decides whether they really are. Asserted neither way | 6 |
| `NOT_RULE_COLLAPSED` | the rules already give this node its own function; any remaining merge is design-induced | 27 |

**Revised 2026-09-16, after review.** The first pass called eleven merges
artificial. Nine more were moved into that column — `E_LIF`, `E_GP130_STAT3`,
`E_PC6`, `E_DAG1_CLEAVED`, `E_MUC1_SLEX`, `E_HBEGF`, `E_ANXA2_ACTIN`, `S_SPP1`
and `S_TAZ_ECM` — because the first pass applied the wrong test to them. It
asked whether the literature contradicted the merge. The question that decides
a *collapsed upstream state* is narrower and harder: **does the merge destroy
the ability to tell two perturbations apart?** §2.1 makes that computable and
enforces it.

The first three are the draft's trichotomy. The fourth exists because the
trichotomy adjudicates a *merge* and 27 nodes are not rule-merged at all;
forcing them into it would either overstate or understate. `NOT_RULE_COLLAPSED`
is the one verdict that is a computable fact rather than a judgement, and a test
checks it against the partition rather than trusting the file.

### 2.1 The separability criterion, derived and enforced

A collapse cannot be a defensible abstraction if it means two perturbations
*this repository itself declares as separate targets* are one intervention.
`models/superset/…/drug_target_catalog.tsv` types every executable target —
`ligand`, `pathway_state`, `protease`, `adhesive_receptor`, and so on — so the
question is computable rather than a matter of taste. `perturbation_separability`
computes it from the catalog and `network.bnd`, it is **never curated**, and it
is emitted into `node_classification.tsv` as two more columns:

| value | meaning |
|---|---|
| `MERGES_DISTINCT_TARGET_CLASSES` | shares one Boolean function with an executable target the catalog types **differently** |
| `MERGES_SAME_TARGET_CLASS` | shares one Boolean function with an executable target of the **same** declared type |
| `MERGES_NO_CATALOGUED_TARGET` | is an executable target, but every node it shares a function with is not |
| `NOT_A_CATALOGUED_TARGET` | not an executable target |
| `NOT_RULE_COLLAPSED` | its own Boolean function |

The last two were one value in the first version of this column, and that was a
defect rather than a shorthand: `E_CDH1_APICAL` **is** executable in the catalog
and read `NOT_A_CATALOGUED_TARGET`, so the shipped column stated something the
catalog contradicts — and a test could assert that value while proving nothing
about catalog membership. Splitting them changes no verdict (`E_CDH1_APICAL`
was and remains `ARTIFICIALLY_COUPLED`, on the grounds in §3.6) and makes the
column self-describing.

**WITHDRAWN 2026-09-16 — the invariant `MERGES_DISTINCT_TARGET_CLASSES` ⇒
`ARTIFICIALLY_COUPLED` is no longer enforced.** It was refused at load time; it
is now *reported* by `separability_disagreements()` and watched by a tripwire
test, and the loader no longer refuses any verdict on this ground.

Two reasons, and the second is the deeper one.

* **DTR020**, this repository's own high-confidence finding, rates it the most
  important catalog defect found: `target_class` is free text with 24 distinct
  values across 34 rows, 17 of them unique, so *which* merges tripped the
  invariant followed naming granularity rather than biology. The barrier trio is
  the demonstration — `E_PODXL`, `E_DAG1_FULL` and `E_MUC1_BARRIER` are three
  separately druggable molecules sharing one Boolean function, exactly the
  condition the rule called artificial by definition, and they escaped only
  because somebody gave all three the same coarse label `anti_adhesive_surface`.
  Applied consistently the rule would have overridden their curated
  `UNIDENTIFIED` verdict on a naming accident.
* **The two axes are orthogonal.** `perturbation_separability` asks what the
  *model can express*; `adjudication` asks whether the *biological collapse is
  defensible*. A merge can be biologically defensible and still destroy a
  perturbation distinction. Deriving one from the other conflates model
  expressiveness with biology, and that error survives any improvement to the
  taxonomy — which is why the repair is to stop forcing rather than to redesign
  `drug_target_catalog.tsv` now.

**No adjudication changed.** All 11 nodes reporting the signal are
independently `ARTIFICIALLY_COUPLED` on their own rationale and evidence, and 11
of the 22 `ARTIFICIALLY_COUPLED` verdicts sit on nodes the catalog does not list
at all. What was removed is an unsound assertion, not a verdict.

And after the revision the
stronger property holds and is asserted separately, by reading
`drug_target_catalog.tsv` directly rather than trusting the derived column to
keep encoding it: **no node adjudicated `BIOLOGICALLY_COLLAPSED` is a
catalogued perturbation target at all.** The **four** that remain after the
2026-09-16 verification round (§2b) are `E_SECRETORY_STATE`, `E_PAEP`,
`E_RECEPTIVE_SURFACE` and `S_DECIDUALIZED` — three composite states and a
secreted readout. None is something an agent acts on. `IN_cAMP` and `S_PKA`
were in this list and left it, on primary literature rather than on the
catalog; that route is what §2c calls a demonstrated false negative of this
criterion.

**What the criterion does and does not claim.** Every executable row of the
catalog carries `screening_readiness: structural_only` and the claim boundary
"No efficacy claim; target listing only", so being in it means the repository
has *typed this node as a distinct point of intervention* — not that an agent
exists, is validated, or would work. That is enough for the question being
asked, which is about what the **model can express**, and it is not enough to
call any of these perturbations available. The strongest case does not rest on
the catalog alone: `docs/v05_plan_review.md` §3.5 independently lists LIF
neutralisation and STAT3 inhibition as two candidate perturbations on one axis,
and the catalog and the plan agree.

Same-class merges are reported and are deliberately **not** forced. The three
barrier nodes are all `anti_adhesive_surface`: three molecules the catalog types
as performing one declared function, and whether they should be separated is
Gate 3b's question, not a defect on its face. The same holds for `E_PGR` against
`S_PGR`, both `regulator`.

**Scope, stated once.** This adjudicates the **rule** collapse. A design
collapse is a statement about the arms and never about the biology, and no row
here says two nodes are the same thing because one experiment cannot tell them
apart. Where the design collapse is the operative limit, the rationale says so
and names the arm that would break it.

## 2b. What primary verification changed, 2026-09-16

Four rows moved or were corrected after the drug-target review's claims were
checked against the primary sources (see
`context/literature/reviews/deep_research_drug_targets_2026-09-16.primary-verification.tsv`).

**`IN_cAMP` and `S_PKA`: `BIOLOGICALLY_COLLAPSED` → `ARTIFICIALLY_COUPLED`.**
The reopening condition this file itself recorded — *"evidence that a cAMP
effector other than PKA carries part of the decidual response"* — is met.
Kusama et al. (2013, Placenta; human primary ESC) show the EPAC-selective cAMP
analogue is inert alone, potentiates the PKA-selective analogue, and that
EPAC1/EPAC2/RAP1 knockdown **inhibits** the PKA-driven IGFBP-1 and PRL
response. cAMP drives two effectors and the response requires both.

Two things make this the most instructive verdict in the file. **No node was
added**: the pass-through form measures 35 → 35 and the evidenced arm is
*cooperative*, not independent, so a disjunctive EPAC node is positively wrong.
Acknowledging that an equivalence is false does not require knowing the right
replacement. And **the catalog-derived invariant could never have found it** —
neither `IN_cAMP` nor `S_PKA` is a catalogued target. This is a demonstrated
false negative of the §2.1 criterion.

**`E_CD98_CD9`: verdict stands, rationale corrected.** An earlier revision said
the encoding "asserts an inducer the evidence does not name and omits the one it
does". That is **wrong**. Domínguez et al. (2010) report CD98 induced in primary
human EEC by hCG, 17β-estradiol, **LIF** *and* EGF — LIF is among them. Worse,
`REF-008`'s own `key_use` field already recorded all four, so the repository held
the correction to its own rationale the whole time. The defect is
**incompleteness**, not misattribution: four inducers, one encoded.

**A fifth absorbed conjunct.** `S_FGF_MITOGENIC = not S_HAND2`, so its conjunct
in `E_ESTROGENIC_PROLIFERATION` reduces to `not S_HAND2`. It is a *different
shape* from the other four — `S_FGF_MITOGENIC` is not in an alias class at all,
it has its own Boolean function, and its **use** is still vacuous. Absorption is
therefore not only a property of alias classes. Consequence: **HAND2 loss and an
FGF-level perturbation have no distinct image in this model.** Pinned by
`test_the_fgf_conjunct_in_epithelial_proliferation_is_vacuous`.

## 2c. Is `target_class` fit to be verdict-forcing? — assessment, not yet a change

**Finding: it is a sound *sufficient* condition and an unsound *primary*
criterion.** Three lines of evidence, all from this round.

1. **Its coverage is accidental.** `target_class` is free text: 24 distinct
   values across 34 rows, 17 appearing exactly once. It fired on three of the
   five multi-target alias classes and not on two — and what protected the
   barrier trio was that somebody gave all three the same coarse label
   `anti_adhesive_surface`, while `adhesive_effector` lumps a glycoform, a
   transmembrane complex and a junction protein.
2. **It has a demonstrated false negative.** The `IN_cAMP`/`S_PKA` defect is
   real, is now recorded, and is invisible to the criterion because neither node
   is catalogued.
3. **The structure cannot choose between evidenced and unevidenced forms.** For
   the CD98 repair, `STAT3 or hCG`, `STAT3 or hCG or E2` and `STAT3 or
   generic-embryo-signal` all give an identical 35 → 36. Only the evidence picks
   `hCG`.

**What it should not become.** Not `model_role`. A ligand source and its
receptor having different roles does not by itself invalidate a collapse —
`E_PAEP` (`readout`) against `E_SECRETORY_STATE` (`state`) is the counterexample
already in this file, and it is deliberately `BIOLOGICALLY_COLLAPSED`. Swapping
one free-text categorical for another would reproduce the same failure.

**The defensible criterion is a question, not an axis:**

> *Does this merge make two interventions the repository can distinguish
> experimentally indistinguishable in the model?*

Several independent routes can answer it — the drug catalog is one, primary
literature is another (as `IN_cAMP`/`S_PKA` now shows), and the node
dictionary's `measurement_proxies` is a third. Each is **sufficient** to force
`ARTIFICIALLY_COUPLED`; none is **necessary**; and none should be the sole
gate.

**Recommended, and deliberately not done in this increment** (it is a focused
structural change and belongs with its own tests, per the standing instruction
not to alter the catalog silently to satisfy an invariant):

- close the `target_class` vocabulary by biological **level** — ligand,
  receptor, pathway, protease, glycan, transcription factor, ECM, mechanical,
  state, readout;
- add `perturbation_level` as a separate explicit field rather than overloading
  `target_class`;
- keep the invariant as one sufficient condition among several, and record per
  verdict **which** route established it — the `IN_cAMP` row is the first whose
  route is primary literature.

### 2c.1 What v0.5 U4 answered without making that change, 2026-09-17

The first bullet has now been **asked and answered without touching the
catalog**. `src/dt_adoc/reporting/target_levels.py` re-derives this criterion
with the free-text `target_class` replaced by a closed vocabulary of biological
levels, passed to `perturbation_separability` as an override rather than written
into `drug_target_catalog.tsv`. Report:
`docs/gate2_target_level_rederivation.{md,tsv}`; reasoning:
`docs/v05_u4_gp130_axis.md` §4.

**No verdict changes**, and three things follow that are worth having before
anyone closes the vocabulary for real.

- **The exposure is 29 rows and 21 values, not 34 and 24.** The criterion reads
  only `execution_status = executable` rows, so three of the 24 free-text values
  live entirely on rows it never sees. DTR020's count is right about the catalog
  and overstates the reach *through this criterion*.
- **Only five Boolean-function classes have two or more catalogued members**, so
  those are the only places any typing can matter at all. The minimum
  relabellings that would flip each signal: barrier trio **1**, `E_PGR`/`S_PGR`
  **1**, `S_SPP1`/`S_TAZ_ECM` **1**, the GP130 trio **2**, AC01's six catalogued
  members **5**. DTR020's demonstration is therefore confirmed *and bounded* —
  the barrier trio really does turn on one label, and the signals this file's
  arguments lean on do not.
- **`E_PGR`/`S_PGR` reads fragile and is not.** It is one molecule in two
  compartments, and a *level* axis has no vocabulary for compartment, so no
  defensible assignment separates them. That is a limit of the axis, not a close
  call.

The other two bullets — `perturbation_level` as its own field, and recording the
route per verdict — are untouched, as are DTR021's six `execution_status`
demotions and DTR022's reported node-dictionary axis. All of those change the
catalog, and the paragraph above still applies to them.

## 3. The artificial couplings

Twenty-two after the 2026-09-16 verification round (§2b). Grouped by the repair
each implies, not by class; `IN_cAMP`/`S_PKA` is covered in §2b rather than
repeated here.

### 3.1 The epithelium→stroma channel transmits nothing — `E_IHH`, `S_NR2F2`, `S_BMP2`

`E_IHH = E_PGR`, `S_NR2F2 = E_IHH and S_PGR`, `S_BMP2 = (S_PGR and S_PKA) or
S_NR2F2`, and `E_PGR = S_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE`. All five
nodes reduce to the same function of progestin, so the relay `LIT-IHH-001`
records as the mechanism by which epithelial PGR drives stromal decidualization
carries no information at all. The repository already states the consequence in
`results_reproducibility_matrix.md`: `S_DECIDUALIZED` has no epithelial input
that survives absorption, so **the model has no working epithelium→stroma
channel**. `S_BMP2` is the sharper case, because BMP2 is the one stromal
transcript the paper reports as HT-upregulated (`SOFIA-SC-002`, R21) and the
encoding makes it indistinguishable from receptor state — and the `S_PKA`
conjunct in its own rule is absorbed and does nothing.

`E_PGR` against `S_PGR` is deliberately **not** in this list. Nothing reads
receptor state in either compartment and no perturbation reaches one alone, so
that merge is an information limit: `UNIDENTIFIED`.

### 3.2 PRL and IGFBP-1 are synchronous by construction — `S_PRL`, `S_IGFBP1`

The strongest adjudication in the file, and the one Gate 3a repairs. Both rules
are `= S_DECIDUALIZED`, with no `rate_up` or `rate_down` declared anywhere, so
the two analytes cannot differ in onset. ADOC's own ELISA says they do: at day 0
basal IGFBP-1 is detected in 4/5 units at 37.90–551.26 pg/mL while basal PRL is
0/6; at day 3 IGFBP-1 is 5/5 with four above 1000 pg/mL while PRL is 1/6 at a
maximum of 113.60 pg/mL. The 2× difference in detection limits cannot
manufacture a >25× day-0 gap. `OM-016` records this as a falsifiable structural
requirement on candidate models and **v0.4 fails it**. Kane et al. (PLOS One
2010) dissociate the two independently in human endometrial stromal cells, by
SMAD-dependent and SMAD-independent routes — which establishes that they *can*
be separated, not that TGFβ is the mechanism of the ADOC divergence.

### 3.3 Two phenotype outputs cannot disagree with the states they report — `OUT_STROMAL_DECIDUALIZED`, `OUT_EPITHELIAL_RECEPTIVE`

Both are defined as a state conjoined with the markers that are supposed to
evidence it, and in both cases **every marker conjunct is absorbed**:

| rule | conjunct asserted vacuous | assignments where it bites |
|---|---|---:|
| `OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE and E_PAEP` | `E_PAEP` | **0** of 524,288 |
| `OUT_STROMAL_DECIDUALIZED = S_DECIDUALIZED and S_PRL and S_IGFBP1` | `S_PRL`, `S_IGFBP1` | **0** of 524,288 |
| `X_ADHESION_ROUTE_SPP1 = … and E_ITGAVB3_5 and …` | `E_ITGAVB3_5` | **0** of 524,288 |
| `X_MECHANICAL_PERMISSIVE_ECM = S_DECIDUALIZED and S_TAZ_ECM and …` | `S_TAZ_ECM` | **0** of 524,288 |

These are enumerations, not arguments, and
`test_coupling_adjudication.AbsorbedConjunctTest` keeps them true.

So no PAEP observation can disagree with the receptive-surface state, and no
PRL or IGFBP-1 observation can disagree with the decidual state. That is the
structural reason `OM-009` and `OM-010` are confined to diagnostic use, why
`OM-010`'s claim ceiling has to *forbid* reading it as evidence that PRL and
IGFBP-1 are co-timed, and why R20, R22 and R23 stay `not_assessable` after
their provenance was corrected.

The fourth absorbed conjunct, `S_TAZ_ECM`, supports an `UNIDENTIFIED` rather
than an artificial verdict: `LIT-MECH-001` records mechanical effects as
qualitative for want of donor-linked human calibration, and the mechanical half
of the interface is adjudicated out of the Boolean formalism in any case.

### 3.4 The integrin conjunct is vacuous — `E_ITGAVB3_5`, and five more targets beside it

`E_ITGAVB3_5` is rule-identical to the whole secretory program, and in
`X_ADHESION_ROUTE_SPP1` its conjunct is absorbed by `E_RECEPTIVE_SURFACE` (table
above). **An integrin blockade is therefore unrepresentable in the model whose
headline adhesion route is integrin-mediated** — and the ADOC design never
measured ITGB3, αvβ3 or ITGB5, so nothing in the observation record would have
caught it. This is what makes an integrin or SPP1-receptor perturbation
unrankable today, which matters to Gate 6.

The nine-node secretory class is the worst case in the model by the separability
criterion: it merges **six executable catalog targets of six different types** —
`E_PC6` (protease), `E_ITGAVB3_5` (adhesive_receptor), `E_HBEGF`
(growth_factor_effector), `E_MUC1_SLEX` (adhesive_effector), `E_DAG1_CLEAVED`
(adhesive_surface_release) and `E_ANXA2_ACTIN` (cytoskeletal_effector). A
convertase inhibitor, an integrin blockade, an HB-EGF neutralisation and a
cytoskeletal agent are one intervention here. **Three** nodes in that class are
*not* catalogued targets and keep the verdicts they had:
`E_SECRETORY_STATE` and `E_PAEP` stay `BIOLOGICALLY_COLLAPSED` — the hub is the
program and PAEP is a readout — and `E_SPP1_EXPR` stays `UNIDENTIFIED`, because
the modularity `LIT-SPP1-001` asks for survives downstream (`IN_ANTI_SPP1` acts
on `X_SPP1_LUMEN_FREE`, not on expression), so the merge costs an information
distinction rather than an intervention.

The stromal pair `S_SPP1` (decidual_effector) and `S_TAZ_ECM`
(mechanical_regulator) fail the same way, and one distinction is worth stating
because the first pass blurred it: the mechanical **readouts** are adjudicated
out of the Boolean formalism by the reproducibility matrix, and that stands. The
mechanical **target** is not out of scope — a TAZ/WWTR1-directed agent's effect
on the attachment fraction is perfectly expressible, so §3.6 of the plan does
not excuse this merge.

### 3.5 The GP130/STAT3 axis cannot tell its own two perturbations apart — `E_LIF`, `E_GP130_STAT3`, `E_CD98_CD9`

The case the review turned on, and the most consequential of the nine
revisions. `E_LIF = E_GP130_STAT3 = E_CD98_CD9 = E_SECRETORY_STATE and not
E_KLF12_HIGH`, and the catalog lists all three as **executable targets of three
different classes** — `ligand`, `pathway_state`, `adhesive_effector`.

`docs/v05_plan_review.md` §3.5 lists **LIF neutralisation** and **STAT3
inhibition** side by side as candidate perturbations on this axis, over the note
that `E_LIF` and `E_GP130_STAT3` are both *present* in v0.4. They are present
and they are **one variable**, so the two candidates are the same intervention
in the model — while being different experiments in the laboratory: STAT3
inhibition blocks the pathway whichever ligand drives it, LIF neutralisation
does not, and `X_IL11` is precisely the staged candidate that makes the
difference real rather than hypothetical.

This matters more than any other entry in the file, because
`docs/identifiability/candidate_readouts.tsv` puts **four of the only six
class-gaining readouts** on this axis: of its 40 assayable unmeasured states,
exactly six carry `marginal_gain_now = 1`, and four of those are `E_LIF`,
`E_GP130_STAT3`, `E_CD98_CD9` and `E_KLF12_HIGH` (the other two are
`E_RECEPTIVE_SURFACE` and `OUT_EPITHELIAL_RECEPTIVE`). An earlier revision cited
`proposed_panel.tsv` for this, which holds the greedy panel — nine perturbation
arms and two readouts — and none of the four. A ranking of perturbations run against v0.4 today would score
LIF neutralisation and STAT3 inhibition identically and would have no way to
report that it could not tell them apart. `test_the_lif_gp130_case_is_caught_by_name`
holds this case specifically, so a general invariant cannot quietly stop
covering the case it was written for.

### 3.6 The model asserts an inducer the evidence does not name — `E_CD98_CD9`, `E_CDH1_APICAL`, `IN_EMBRYO_CONTACT`

`E_CD98_CD9 = E_GP130_STAT3`, so CD98/CD9 availability is a function of LIF.
`LIT-CD98-001` records the opposite: CD98 and CD9 "are induced by
embryo-conditioned cues such as hCG". `E_CDH1_APICAL = IN_EMBRYO_CONTACT`
literally, so contact and the epithelial response to contact are one variable;
`LIT-CDH1-001` names an embryo-conditioned induction step between them and
requires apical CDH1 to stay distinct from lateral-junction CDH1.

Both inducers exist in this model as declared inputs and **no rule reads
either**. `IN_HCG` and `IN_EMBRYO_CONDITIONED_SIGNAL` are zero-degree nodes, as
is `IN_XAV939`, pinned by `ZeroDegreeInputTest`. These are therefore curation of
edges the register already records, not invented topology.

The CDH1 repair is in fact **already written down**: the `cdh1` rule-variant
family holds `maternal_receptive_state_dependent`
(`E_SECRETORY_STATE and (IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL)`) and
`maternal_priming_with_contact_reinforcement`. But those families are declared
for `adoc-literature-v0.2.0` only — **`resolve_model` returns no rule-variant
families at all for the v0.4.0 superset**, so the alternative cannot currently
be executed against the model that carries the defect. That gap belongs to
Gate 5, which assumes the variant layer exists in "the files that already
exist"; the catalog file
`models/superset/adoc-literature-superset-v0.4.0/rule_variants.tsv` does exist,
and the runtime does not read it as a variant family.

## 4. What this does not say

- It does not rank the repairs. Gate 3 does that, and its order is set by the
  plan, not by this file.
- It does not promote a node. A coupling being artificial says the model must be
  able to express a distinction; it does not say which mechanism expresses it.
  `S_TGFB_CONTEXT` in particular stays a candidate rule variant.
- It does not settle the barrier branch. `E_PODXL`, `E_DAG1_FULL` and
  `E_MUC1_BARRIER` are recorded `UNIDENTIFIED` **deliberately** — the
  separability criterion reports them as `MERGES_SAME_TARGET_CLASS` and does not
  force a verdict on them: whether
  reconnecting them to attachment or retention is evidence-supported, and
  whether it changes any intervention, is what Gate 3b is to establish, and
  adjudicating it here would settle by verdict what the plan asks to settle by
  analysis.
- It does not make any row in `results_reproducibility_matrix.tsv` assessable.

## 5. What `planned_design.yaml` is, and is not

Recorded here because the two are read together and the second is easy to
misread. `config/planned_design.yaml` names a four-arm plan whose fourth arm is
anti-SPP1. That file is the **as-declared plan**, and its only role is to be the
baseline partition candidate arms are scored against. It is **not** a selection
of the prospective arm, it now declares `role:
as_declared_plan_baseline_not_a_prospective_selection`, and
`design_alias.load_plan` refuses any other value, so a later edit cannot
repurpose the file into a recommendation that inherits its readers.

The analysis the file feeds argues against reading the fourth arm as the choice:
`hormone_treated_anti_spp1` carries **no recorded observation** and
`IN_ANTI_SPP1` is `set_alone_no_shared_readout`, so as declared the arm perturbs
a mechanism the design cannot read; by raw class gain the best fifth arm is
HAND2 loss (+5); and by separation of the two measured analytes only minus-E2
and minus-cAMP score at all. Gate 6 chooses the embryo-challenge arm **after**
the maternal-phase panel, with no molecule privileged in advance.

## 6. How a verdict is invalidated

Each row pins the `effective_function_id` it was adjudicated against. If a rule
edit moves a node into a different class, loading **fails** rather than carrying
the old verdict into a model it no longer describes. Each row also names its
evidence, checked against `context/evidence-register.tsv`, and the condition
that would reopen it. No row may be added without all three.
