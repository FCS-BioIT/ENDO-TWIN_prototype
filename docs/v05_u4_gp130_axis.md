# U4 — AC04 / GP130: the rule families stay families, and the one paper that could have closed them does not

**Unit:** U4 of `docs/v05_mechanistic_integration_plan.md`.
**Outcome:** **no canonical promotion, and no rule, node, edge, threshold, rate,
istate, condition or phenotype changed.** The GP130 and CD98 axes stay
**evaluation-only rule families**, which is what §4.1 and TI002 ask for. One
family member was staged (`CD98-d`, TI001's literal rule text); one was evaluated
and **deliberately not written** (`GP130-d`, the IL-11-specific downstream arm).
**Guards:** `tests/unit/test_v05_u4_gp130.py`.

**The executable digital twin is byte-identical to v0.4.** The free-variable
count is unchanged at 19 (5 non-input), the distinct-Boolean-function count is
unchanged at 35, and AC01 still has nine members.

---

## 0. What U4 was asked to do, and what each item returned

| §17 item | result |
|---|---|
| Read Yap/Dimitriadis 2011 (PMID 21619711) before any promotion | **Done, full text.** It does **not** collapse TI002's family, for a reason the abstract does not show: there is no LIF comparator and no functional endpoint. §1 |
| Full-text verification of everything TI001/TI002/TI004 rest on, into the §5(1) ledger | **Done.** Two rows moved to full-text read; two of the underlying findings have no primary source at all and are verified against the repository instead. §2 |
| Stage `X_IL11` and the CD98 rewire as evaluation-only rule families, using TI001's literal rule text | **Done.** `CD98-d` staged and computed; `GP130-b` was already staged and is confirmed; the second GP130 member is refused. §3 |
| Re-derive the Gate 2 invariant against a closed `target_class` vocabulary and surface every changed verdict | **Done, and the answer is none.** §4 |

## 0a. Prerequisites, checked before anything was edited

§17 lists four standing prerequisites against the unit each gates. Two name U4,
directly or by implication, and both were checked first rather than assumed.

- **"Gates any v0.5 claim about `E_ESTROGENIC_PROLIFERATION` — so U3, U4 and U5."
  Still open, and U4 makes no such claim.** The owner question — whether the CNT
  arm is unstimulated or E2-primed-only — is unanswered and U4 does not need it.
  Checked rather than asserted: the node appears **once** across everything U4
  generated, as a typing row in `gate2_target_level_rederivation.tsv`
  (`anti_receptive_state` → `state`, `NOT_RULE_COLLAPSED`). That is a statement
  about the catalog and the Boolean partition, not about what the node does in
  any arm, and no answer to the owner question could move it. Note in particular
  that §2.2 below reaches `IN_E2` as an evidenced inducer of `E_CD98_CD9` and
  stops there: it makes no claim about what E2 priming does to the proliferative
  state, which is what the owner question governs.
- **D1.** §17 marks U4 "*independent of D1*", and §0.7 states the ground: `AC04`'s
  `rule_challenged` verdict, every node-support label, every QC verdict and §0.1's
  zero-absences finding do **not** depend on D1. U4 inherits no part of U3's
  conditional mandate, and it also makes no `AC04` claim it would need one for —
  §7.2 holds `AC04` loosely and U4 leans on it less, not more.

The other two prerequisites gate Gate 3b and U8 and are untouched.

**One prerequisite of a different kind, recorded because it shaped the unit.**
The literature PDF library (`context/literature/pdfs/`) is gitignored and is
therefore **absent from this worktree**; the two papers U4 read were read from the
main checkout's copy. That is why each read is recorded with a sha256 rather than
a path, and why §17's "unregistered in the PDF library" wording for Yap 2011 was
true in a narrower sense than it reads: the PDF was supplied and held, and it was
the *manifest row* that was missing.

---

## 1. Yap/Dimitriadis 2011, read in full: two candidate executors, neither usable

*Reprod Biol Endocrinol* 9:73, doi 10.1186/1477-7827-9-73, PMID 21619711.
Read 2026-09-17 from the local PDF library (`context/literature/pdfs/`, which is
gitignored and therefore absent from this worktree; read from the main checkout),
15 pages, sha256
`307076c46158b12a25f1cd3e103be6d6477bcc8586449b229236ed042b3241da`.

### Why this paper and not another

`primary-verification.tsv` called it "**THE HIGHEST-VALUE UNREAD ITEM** … the
paper most likely to name an executor for the IL-11-specific
trophoblast-attachment effect that LIF lacks — the single finding that decides
whether the GP130 split needs a ligand-specific downstream arm or only a shared
STAT3 node, i.e. whether TI002's rule family can be collapsed to one member."
That is the question, and reading the paper is the only way to answer it. §17
puts it **before** any promotion for exactly that reason.

### What it reports

IL-11 (100 ng/ml, 24 h) raises two plasma-membrane proteins in human endometrial
epithelium:

| protein | 2D-DIGE | membrane Western | primary hEEC |
|---|---|---|---|
| **ANXA2** (annexin A2) | spot 9, fold 1.33, p 0.02 | 2-fold ECC-1, 2.5-fold Ishikawa (p ≤ 0.05) | stronger surface immunostaining; **total ANXA2 unchanged**; the membrane difference is described as apparent and is not quantified |
| **FLOT1** (flotillin-1) | spot 14, fold 1.40, p 0.04 | 1.8-fold ECC-1, 2.3/2.4-fold Ishikawa (p ≤ 0.05) | **total FLOT1 unchanged**; the authors state they were unable to detect FLOT1 in primary hEEC by Western |

**Every quantified fold-change above is from a carcinoma line.** No
membrane-fraction quantification is reported for primary hEEC for either
protein.

Independently of IL-11, FLOT1 immunostaining in glandular epithelium is maximal
in the **mid-secretory** phase (p ≤ 0.0001) — the receptive window.

### Why it does not close the question

Three reasons, in decreasing order of how decisive they are.

1. **There is no LIF arm anywhere in the paper.** The whole content of the second
   family member is that something downstream is IL-11-**specific**, i.e. moves
   under IL-11 and not under LIF. A study with one cytokine cannot make that
   comparison. This is not a weak result pointing the wrong way; it is the
   absence of the contrast.
2. **There is no functional endpoint.** No adhesion, attachment, trophoblast or
   blastocyst assay is run. The adhesive phenotype is cited from the authors'
   earlier work (their ref 15 = Marwood 2009, the paper this one was meant to
   explain). Nothing here shows either protein **executes** anything; the
   authors' own conclusion is that IL-11 "**may** regulate endometrial epithelial
   cell adhesion **at least in part** via these proteins" and that their role
   "**remains to be elucidated**".
3. **It is abundance, not activity**, which is the DRE009 failure mode
   `AGENTS.md` names. And the quantified abundance is in carcinoma lines: in
   primary hEEC neither protein's total abundance changes and no membrane
   fold-change is quantified at all, so every number in the table above comes
   from ECC-1 or Ishikawa.

### The edit that was available and is not made

This matters more than the negative result, because the tempting repair is
concrete rather than hypothetical. **ANXA2 is already a committed node** —
`E_ANXA2_ACTIN`, `logic = E_SECRETORY_STATE`, `network.bnd:133-135` — and it is
one of the nine members of AC01. So

```
E_ANXA2_ACTIN = E_SECRETORY_STATE or X_IL11
```

would write TI002's missing second family member *and* dent the alias class U3
could not break, in one line. Measured with the repository's own exhaustive
enumerator, it is the **most structurally effective edit available on this axis**:

| model | distinct Boolean functions | AC01 |
|---|---|---|
| committed | **35** | 9 |
| `GP130-b` (`E_GP130_STAT3 = E_LIF or X_IL11`) | **37** | 9 |
| ANXA2 arm alone | **37** | **8** |
| `GP130-b` + ANXA2 arm | **38** | **8** |

It is not written, and the structural result is why the refusal has to be stated
rather than assumed. Under §5's **edge**-promotion criteria the candidate edge
`X_IL11 → E_ANXA2_ACTIN` fails on:

| criterion | verdict | basis |
|---|---|---|
| direction | passes | IL-11 added, ANXA2 measured; the orientation is right |
| causal vs associative | partial | a sufficiency experiment only; no IL-11 blockade, no ANXA2 knockdown |
| species and system | **fails for a canonical rule** | the quantified effect is in ECC-1 and Ishikawa carcinoma lines; in primary hEEC total ANXA2 is unchanged and the membrane difference is unquantified |
| compartment | passes | human endometrial epithelium |
| **activity versus abundance** | **fails** | membrane abundance and punctate staining, against a node that is an actin-remodelling state. DRE009 |
| AND/OR/graded semantics | **fails** | `or X_IL11` makes IL-11 sufficient for the state; the measured effect is a 1.33–2.5-fold graded change over a non-zero baseline |
| Boolean abstraction overstates | **fails** | the paper's own claim is "may … at least in part" and "remains to be elucidated" |
| competing variants remain plausible | yes | FLOT1 is an equally supported candidate, and the convergent-only reading is still live |

**Tally, stated so the prose and the table cannot drift apart: four outright
failures, one partial, two passes.** The eighth criterion is not scored — as in
U3, competing variants remaining plausible *fixes the disposition* (§5's own
consequence is a `rule_variants.tsv` family, not a network fact) rather than
counting as a failure. Causal-vs-associative support is **partial and is left
partial**: the paper does run a real sufficiency experiment, and relabelling that
a failure to round the tally up would be altering a scientific judgment to
protect a number. The decisive failure is *activity versus abundance*, and one
decisive failure is sufficient — the count is context, not the argument.

And it fails the prior question that decides the family: **nothing in the paper
makes either protein IL-11-specific**, so an arm written on it would encode a
specificity no source reports. `gate3_candidate_variants_2026-09-16.tsv` already
records, in `GP130-b`'s own limitation column, "**No downstream IL11 effector is
invented to reproduce it**". That position was taken before this paper was read;
reading it confirms the position rather than lifting it.

### The consequence, stated so it is not mistaken for the opposite

**TI002's family is single-membered because the second member is not
representable, not because the evidence chose between the two.** Those are
different states and only one of them is progress. The dissociation Marwood 2009
measured is real and is downstream of both STAT3 and ITGA2; the model still
cannot express it; and after reading the paper most likely to supply the
executor, it still cannot. `variant_discrimination.py` records this in
`NOT_STAGED`, which exists so that a rule nobody wrote is distinguishable from a
rule nobody thought of.

**What would change it:** the same membrane proteomics with a LIF arm, or an
attachment endpoint under ANXA2 or FLOT1 knockdown in primary hEEC. Both are
specific enough to cost.

---

## 2. What TI001 / TI002 / TI004 rest on, and how each was verified

TI004 is the package "TI001 + TI002 together", so the three items rest on five
findings. Two of them have no primary source at all, and saying so is part of the
verification rather than a gap in it.

| finding | what it is | verification |
|---|---|---|
| **DTR002** (Marwood 2009) | the LIF/IL-11 dissociation TI002 rests on | full text read 2026-09-16; **re-checked in U4** against PDF-043, §2.1 below |
| **DTR002-followup** (Yap 2011) | the paper that would decide the family | **full text read 2026-09-17**, §1 |
| **DTR005** (Domínguez 2010) | the CD98 inducers TI001 rests on | **upgraded from abstract to full text 2026-09-17**, §2.2 below |
| **DTR001** | "commit `7e75da6` already reclassified `E_LIF`/`E_GP130_STAT3`" | **not a literature claim.** Verified against the repository: `config/coupling_adjudication.tsv` records `E_LIF`, `E_GP130_STAT3` and `E_CD98_CD9` all `ARTIFICIALLY_COUPLED` |
| **DTR003** | "the staged `X_IL11 = S_DECIDUALIZED` is measured inferior to a free input" | **not a literature claim.** It is a structural measurement, and U4 re-measured both numbers with the repository's own exhaustive enumerator: staged **35 → 36** with `X_IL11` inside a **seven**-member decidual class; free input **35 → 37**, `E_LIF` separated, `{E_CD98_CD9, E_GP130_STAT3}` left as a pair. Both reproduce exactly |

The ledger is the review-scoped file §0.6 identifies,
`context/literature/reviews/deep_research_drug_targets_2026-09-16.primary-verification.tsv`.
**U4 appended no rows.** It **revised two existing rows** — `DTR002-followup`
from "NOT YET READ" to a full-text record, and `DTR005` from abstract-verified to
full-text — which is what those rows were for. Manufacturing new finding ids for
claims the ledger already tracks would have inflated the count §0.6 quotes
without verifying anything new. The count is still seven.

**No reference or PDF registration was added**, and that is a statement about
U4's scope, not a rule. `DTR002-followup` keeps `ref_id = (not registered)`
because registering references was not part of this evaluation-only pass; the
read is instead made checkable by recording the PDF's sha256 and page count in
`verification_route`, which is what a later unit actually needs.

*Not to be read as an invariant.* Registration is **provenance and curation**;
canonical promotion of an edge, rule or node is a **separate modelling decision**
on §5's criteria. A later unit may legitimately register Yap 2011 — it was read
in full, and recording that is good practice — while still refusing every
mechanistic use of it, and doing so contradicts nothing U4 concluded. What must
not happen is the reverse: promoting anything on this paper, which the evidence
does not support. `tests/unit/test_v05_u4_gp130.py` guards the promotion
decision and deliberately does not guard the registration state.

### 2.1 Marwood 2009 — re-checked, and one caveat the ledger did not carry

The two claims TI002 turns on are confirmed against the full text:

- **Figure 2C** — IL-11 increased adhesion of primary human first-trimester
  trophoblast to EECs (P < 0.05); **LIF did not**.
- **Figure 6A/6B** — an integrin-α2β1 neutralising antibody reduced the
  **LIF**-induced collagen-IV adhesion (P < 0.05) and had **no effect** on the
  IL-11-induced one.
- **Figure 2B** — a STAT3 inhibitor reduced *both* cytokines' fibronectin
  adhesion, so the shared convergence node is demonstrated rather than inferred.

One caveat the ledger states less fully than the paper does: the authors write
that first-trimester trophoblast cells "are considered to be trophoblast stem
cells" and "may not fully reflect trophectoderm cells, but they are the best
available model". The dissociation is human-human, as the ledger says, and it is
not a blastocyst. Nothing in U4 depends on the difference, and it is recorded
because the next unit to lean on this result should know it is there.

### 2.2 Domínguez 2010 — the full text adds two things the abstract could not

**First, `IN_E2` is a directly evidenced inducer, and the repository had not
recorded it.** In primary human EEC, membrane CD98 rises under hCG (p < 0.02;
Western 4.4-fold), **17β-estradiol (p < 0.00001; Western 2.8-fold)**, E2+P4
(Western 3.5-fold) and LIF (p < 0.02). E2 is the *largest* effect in the panel.
Two negatives come with it, and both are new to the repository: **progesterone
alone does not induce CD98** (Western 0.6, i.e. reduced) and **TGF-β
significantly reduces it**. CD98 is not a marker either — overexpression gives
near-100% mouse blastocyst adhesion at 24 h and shRNA significantly impairs it.

This bears directly on a comparison the Gate-3 table currently frames the other
way. `CD98-c`'s entry says its prediction "sits awkwardly with Domínguez showing
LIF induces CD98". On the full text the awkwardness is smaller than that: the
same paper induces CD98 with LIF **and** with E2, so `CD98-c`
(`E_GP130_STAT3 or IN_HCG or IN_E2`) is the variant with the most direct evidence
behind its disjuncts of any member of this family.

**Stated precisely, because the three disjuncts are not equally direct.**
`IN_HCG` and `IN_E2` are measured inductions of membrane CD98 in primary human
EEC in this one paper. `E_GP130_STAT3` is **not**: what Domínguez measures is
**LIF**, and the step from LIF to the node is Marwood 2009's LIF → pSTAT3. So
the committed disjunct rests on a two-paper chain, and **no source tests whether
the LIF induction of CD98 is STAT3-dependent at all**. That is worth recording
against the variant rather than smoothing over: the strongest-evidenced member of
this family still has one disjunct whose own mechanism is inferred.

**It is still not a promotion**, and the reason is not squeamishness. The
induction is graded — 1.2- to 1.5-fold MFI over a non-zero untreated baseline —
so `or` asserts a *sufficiency* the data do not show; and §5 is explicit that
where competing variants remain plausible the candidate "enters
`rule_variants.tsv` as a family, not the network as a fact". Three variants
remain plausible on this axis. So the family stays a family, and `CD98-c`'s
evidential standing inside it is recorded rather than converted into a rule.

**Second, the embryo-conditioned disjunct is refined, not merely unsupported.**
DTR005 recorded that "no source read names" a generic embryo-conditioned inducer.
The full text is more specific and more useful: Domínguez **does** report that
JAR spheroids and their **conditioned medium** induce membrane CD98, and that
CD98 rises in the endometrial cells contacting a mouse blastocyst (Fig 4E). But
the conditioned-medium result is "**data not shown**", and the authors attribute
it to hCG in as many words — "*because of their capacity to secrete significant
amounts of chorionic gonadotropin*". **No hCG-depleted or hCG-blocked conditioned
medium was tested.** So the source supports an embryo-conditioned *route* and
does not support a generic inducer *distinct from hCG* — which is the only thing
TI001's third disjunct could contribute.

---

## 3. The rule families, as staged

Nothing here enters `network.bnd`, `baseline.cfg` or any model directory. The
families live where §5 says they live: as evaluation-only variants, computed
against the committed network in memory by
`src/dt_adoc/experiments/variant_discrimination.py`, and reported in
`docs/experiments/variant_discrimination.{md,tsv}`.

### 3.1 `CD98-d` — TI001's literal rule text, staged and measured

§17 says to use TI001's literal rule text, and §4.1 says its third disjunct is
unsupported. Both are honoured by **staging it and computing what the disjunct
buys**, rather than by quietly dropping it or quietly adopting it:

```
CD98-d:  E_CD98_CD9 = E_GP130_STAT3 or IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL
```

Measured: **35 → 36**, identical to `CD98-b` and `CD98-c` at the partition level,
leaving `{E_GP130_STAT3, E_LIF}` as a pair. The structural probe cannot choose
between the three, which is what DTR005 already recorded.

The discrimination computation gives the sharp result. **`CD98-d` differs from
`CD98-b` in exactly one setting of the controlled inputs**: embryo-conditioned
signal **present** and hCG **absent**. In every other setting — including
hCG-on — the two rules predict the same thing in every recorded arm.

That is not a modelling curiosity. The one experiment that could earn TI001's
third disjunct is **embryo-conditioned medium without hCG** — precisely the
control Domínguez did not run, having attributed the conditioned-medium effect to
hCG rather than tested it (§2.2). The model and the primary source agree on which
experiment is missing, which is the most useful thing a rule family can produce.

Against the v0.4 baseline, `CD98-a vs CD98-d` is `REQUIRES_A_NEW_CONTROLLED_INPUT`
— like `CD98-b`, it predicts exactly what v0.4 predicts wherever this project can
currently observe.

### 3.2 `GP130-b` — already staged, and confirmed

`E_GP130_STAT3 = E_LIF or X_IL11`, with `X_IL11` a free **input** and explicitly
not the staged `logic_hint = S_DECIDUALIZED` form. Re-measured in U4: **35 → 37**,
no new alias, `E_LIF` separated from `{E_CD98_CD9, E_GP130_STAT3}`. The rejected
staged form gives **35 → 36** and enlarges the decidual class to **seven** — the
class Gate 3a exists to break. U4 changes nothing about either verdict.

### 3.3 `GP130-d` — refused, and recorded as refused

See §1. Reported in `NOT_STAGED` rather than in `EXCLUDED`, because the two are
different: `EXCLUDED` holds variants the curated table proposes and the enumerator
cannot evaluate, and `NOT_STAGED` holds a variant that *could* be evaluated and is
not written because the evidence does not permit writing it.

### 3.4 What is **not** done, and why

- **No row is added to `models/superset/*/rule_variants.tsv`.** The plan's §6.1
  wants node-level requirement sets keyed to a `variant_id` there, and that is a
  **U6** deliverable that arrives with the component map. Adding variant rows now
  would also break the v0.5 scaffold's byte-identity assertion
  (`tests/unit/test_v05_scaffold.py`), which U1 installed so that the first real
  mechanism change shows up as exactly that change. U4 is not a mechanism change
  and should not look like one.
- **No row is added to `gate3_candidate_variants_2026-09-16.tsv`.** That table is
  the Sept-16 review's record; `CD98-d` is U4's staging of TI001, dated
  2026-09-17. Backdating it into that file would misattribute the curation. The
  commentary lives here and the rule text lives in the module, with both cited
  from the other.
- **No candidate-edge row, and no `complete_edges.tsv` regeneration.** That was
  already recorded as pending in three ledger rows for a stated reason
  (regeneration is a shared-resource change) and nothing in U4 is promoted, so
  nothing is owed.

---

## 4. The Gate 2 invariant, re-derived on a closed vocabulary

Generated report: `docs/gate2_target_level_rederivation.{md,tsv}`, from
`src/dt_adoc/reporting/target_levels.py` (`pixi run
build-target-level-rederivation`).

TI016 and DTR020 ask for the separability criterion to be re-derived against a
closed `target_class` vocabulary defined by biological **level**, with every
changed verdict surfaced. Three things about the result.

**No verdict changes.** Every separability signal the criterion reports is the
same under the closed vocabulary of 13 levels as under the catalog's free text.

**The exposure is smaller than the headline.** DTR020 and §4.2 both count "34
rows, 24 distinct values", which is the whole catalog. The criterion reads only
rows with `execution_status = executable`, so what it can actually see is **29
rows and 21 values**: the five non-executable rows carry three values
(`dynamic_matrix_regulator`, `candidate_effector`, `external_input`) that no
separability verdict has ever depended on. The catalog defect is real; its reach
*through this criterion* is narrower than the count implies, and that distinction
should be carried rather than restated as 34/24.

**"No change" is reported with its own fragility, because a vocabulary is a
judgement.** A mapping chosen after seeing the answer could reproduce it, so the
report also computes, per Boolean-function class, the minimum number of
relabellings that would flip the signal. Only five classes have two or more
catalogued members, and those are the only places any typing can matter at all:

| class | levels | verdict | relabellings to flip |
|---|---|---|---|
| `E_DAG1_FULL`, `E_MUC1_BARRIER`, `E_PODXL` | all `surface_molecule` | `MERGES_SAME_TARGET_CLASS` | **1** |
| `E_PGR`, `S_PGR` | both `receptor` | `MERGES_SAME_TARGET_CLASS` | **1** |
| `S_SPP1`, `S_TAZ_ECM` | `ligand`, `ecm` | `MERGES_DISTINCT_TARGET_CLASSES` | **1** |
| `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF` | `surface_molecule`, `pathway`, `ligand` | `MERGES_DISTINCT_TARGET_CLASSES` | **2** |
| AC01's six catalogued members | `cytoskeleton`, `surface_molecule`, `ligand`, `receptor`, `glycan`, `protease` | `MERGES_DISTINCT_TARGET_CLASSES` | **5** |

So DTR020's diagnosis is confirmed *and bounded*. The barrier trio is exactly as
fragile as DTR020 said — one relabelling, and the whole signal moves — and the
GP130 and AC01 signals, which are the ones this repository's scientific arguments
actually lean on, are not. The `E_PGR`/`S_PGR` pair reads as fragile by the same
metric and is not in practice: they are the same molecule in two compartments, and
a **level** axis has no vocabulary for compartment, so no defensible level
assignment separates them.

**Nothing here forces an adjudication, and none is changed.**
`config/coupling_adjudication.tsv` is untouched. The invariant
`MERGES_DISTINCT_TARGET_CLASSES` ⇒ `ARTIFICIALLY_COUPLED` was withdrawn on
2026-09-16 and is reported rather than enforced, so even a flipped signal would
move a reported column and no verdict.

**And the catalog is not rewritten.** The re-derivation passes the typing into
`coupling.perturbation_separability` as an override; `drug_target_catalog.tsv` is
byte-pinned in v0.4 and in the v0.5 scaffold, and DTR021's separate finding that
six rows carry the wrong `execution_status` is a scientific change that removes
catalog ground from real coupling verdicts. Editing the file to see what the
criterion would say is the "move the rule rather than the code" failure mode, and
is what §13.5 names.

**What this does not close.** TI016 also asks for a **reported non-forcing
node-dictionary axis** (DTR022) and depends on DTR021's `execution_status`
demotions. Neither is done here. Both are catalog changes with their own tests,
and `docs/coupling_adjudication.md` §2c already records them as a focused change
that must not be made silently. TI016's `blocks_v05 = yes` therefore still stands
for those two halves; what U4 closes is the half it was given — the invariant
re-derived, with every changed verdict surfaced, and there are none.

---

## 5. What U4 did not do

It did not change any rule, node, edge, threshold, rate, istate, condition or
phenotype; did not add a free Boolean variable; did not touch v0.4 or the v0.5
model directory; did not promote any candidate edge or node; did not upgrade
`AC04` (§7.2 holds it loosely, for two reasons — the §3.1(4) exemption it does
not meet and the §3.2 condition-entanglement caveat that the raw-UMI
re-derivation settled only for `PAEP` and `HBEGF`); did not restore "precise
null" anywhere; did not edit `drug_target_catalog.tsv` or
`config/coupling_adjudication.tsv`; did not reopen U1, U2 or U3; and did not
start U5.

**It also did not treat an evaluation-only family as a weaker promotion.** The
families are carried because the evidence supports carrying them, and the one
member the evidence does not support was refused even though it was the largest
structural gain on the table.
