# Stage 4c — first real direct admission: refusal record, 2026-10-05

**Outcome: `NOT_ADMISSIBLE_YET`.** Stage 4c took the realistic non-hormonal
candidates through the frozen Stage 4b admission process. No candidate satisfies
it. **No evidence-register row, declaration, ledger approval or
intervention-library row was written**, and no admission criterion, entity-map
reading, policy row or model rule was changed to accommodate a candidate.

Stage 4c is complete as a refusal. Its product is this record: which candidate is
closest, which condition each one fails, and what each failure would take to
close. Stage 4d remains blocked by the §5.6 two-approval condition, which no
finding here affects and which this record does not reinterpret (§6).

The governing documents are `docs/stage4b_direct_admission.md` (pre-registered,
owner decisions 1–7) and `docs/stage4b_implementation.md` (§10, amendments
A1/A2). Both are unedited. Section references below are to the first unless
marked O8b, which is `docs/o8b_direct_effect_governance.md`.

## 1. State verified before judging

- `main` at `c45ef46`, the merge of PR #22; tree clean. `check_admission`
  (C1–C8, §6.1 items 4–5) is present at
  `src/dt_adoc/perturbations/adjudication.py` and is called from
  `engine._license_direct_effects`.
- `config/direct_effect_target_declarations.tsv` and
  `config/direct_effect_adjudications.tsv` are header-only; the ledger header
  carries the 17 columns of §6.2. `config/intervention_library.tsv` holds, for
  v0.6.0, **four `migrated_legacy_behaviour` rows representing three
  interventions** — mifepristone on `E_PGR` and on `S_PGR`, anti-SPP1 on
  `X_SPP1_LUMEN_FREE`, HAND2 loss on `S_HAND2` — plus the `xav939` row, whose
  basis is `executable_legacy_behaviour` with mode `no_executable_effect`. No
  `direct_supported_effect` row exists on any version.
- `config/node_entity_map.tsv` holds 93 rows for v0.6.0, including the 36
  model-gap rows amendment A2 requires.

**The mechanical fact that decides two of the three cases:** C5 and C7 match a
declaration's `known_target_entities` against the map on the exact
`(entity, level)` pair. The level at which a node is modelled is therefore
binding, not the gene symbol alone.

## 2. Candidates considered

The eligible targets examined for this stage. **The first three rows are the
candidates the repository supplies with a named agent**, and they are what §3 and
§4 adjudicate. The remaining rows are recorded so the coverage of this refusal is
visible: two name no agent at all, and the rest are ruled out by a frozen
decision or by the absence of qualifying engagement evidence. The table is not a
claim that every conceivable agent for these nodes has been enumerated.

| candidate → node | map reading | status |
|---|---|---|
| STAT3 inhibitor peptide II (Calbiochem 573092, P3-AHNP-STAT3BP) → `E_GP130_STAT3` | `all_of` {LIFR, IL6ST, STAT3}@activity, epithelium | **closest**; refused, §3 |
| anti-LIF / LIF neutralisation → `E_LIF` | `single` LIF@expression, epithelium | refused, §4 |
| PC6 perturbation → `E_PC6` | `single` PCSK5@activity, epithelium | refused, §4 |
| TAZ inhibitor → `S_TAZ_ECM` | `single` WWTR1@activity, stroma | no named agent; PERT-012 is mouse genetics with human-data support |
| anti-SPP1 as a new direct intervention → `X_SPP1_LUMEN_FREE` | `single` SPP1@extracellular | LIT-SPP1-001 is "mixed mechanistic and descriptive"; no reagent, concentration or engagement measurement, so E1 is unmet before any other condition |
| anti-αv or anti-αvβ3 → `E_ITGAVB3_5` | `ambiguous` | unapprovable by **owner decision 7** until TI-03; not reopened here |
| `S_PKA`, `E_ANXA2_ACTIN` | `ambiguous` | refused by default (§11.2); each needs a recorded decision about what its node means |
| the nine structural nulls (§5.3) | various | none carries an abolition-grade engagement measurement: CD98 is abundance (PERT-006), PODXL would need activation (PERT-005), SPP1 knockdown is partial and stated as two nodes (PERT-011), `E_CDH1_APICAL`, `E_ANXA2_ACTIN` and `E_HBEGF` are phenotype- or abundance-level (PERT-007, PERT-008, PERT-015). Assessed at register and perturbation-record level, not full text |

## 3. The closest candidate, and why it is refused

**"STAT3 inhibitor peptide II" (Calbiochem), 20 µM, 1 h pre-treatment, then 24 h
— identified below as catalogue 573092, P3-AHNP-STAT3BP.** Source REF-072 /
LIT-IL11-001 (Marwood *et al.* 2009, *Endocrinology* 150(6):2915–2923),
registered as PDF-043 and read in full text here.

What it satisfies: `E_GP130_STAT3` can mean the intervention, because C5 on an
`all_of` node needs one member hit and STAT3@activity hits it, C7 is met and C3
forces no further epithelial node; `system_match` would be
`matches_model_compartment`; the target is non-null (class A1, §5.3), so §5.6
would not block a phenotype claim; and the cited source supports no edge on a
path from the target to O, so it is not construction-circular in the sense §6.5
records for PC6.

It fails three conditions, two of them blocking:

1. **E2 — target engagement was never measured at the node's modelled level
   (blocking, §6.1 item 1 via O8b §4.2.7).** `E_GP130_STAT3` is modelled at
   `activity`, with proxy "pSTAT3 or target-program activity". pSTAT3 was not
   measured under the inhibitor. The paper blots pSTAT3 under the cytokines and
   their ligand-specific blockers (Fig. 1), while the only readout under the
   inhibitor is adhesion to fibronectin (Fig. 2B): "Addition of STAT3i to either
   IL-11- or LIF-treated cells reduced binding to fibronectin". Under O8b §4.1
   rule 3, an effect whose activity claim rests on no measurement is
   `phenotype_only`, which is not approvable. Engagement is inferred from the
   agent's name, which is the inference O8b exists to refuse.
2. **`system_grade` — the decisive experiment is in an immortalised line
   (blocking, §6.1 item 3 and §6.3).** Fig. 2B is the HES line; the Methods
   state the inhibitor was assessed on "HES cell adhesion", and the legend reads
   "B, HES cell line". That grades `immortalised_endometrial_line`, which §6.3
   makes non-approvable alone. The primary endometrial epithelial panels of the
   same paper do not carry the inhibitor experiment, so the paper's better system
   cannot be borrowed: §6.3 grades the cited measurement, not the paper.
3. **E4 — the profile is demonstrably incomplete; J1 — the criterion is
   unassessable (required for approval; reviewer judgement, not loader-checked).**
   These are two different statements and are kept apart. **E4 fails on a fact
   that holds under any standard:** no selectivity profile for this construct at
   or above 20 µM exists in the repository at all, for either moiety, so there is
   nothing for a standard to be applied to. **J1 is a separate matter: it cannot
   be assessed at all** until the owner defines what §3.6 requires of a
   `biologic`, because the contract states no minimum for that class (below). So
   this item is not "J1 failed" — it is "E4 failed, and J1 is pending a standard".
   No selectivity profile for this construct at or above 20 µM exists in the
   repository, and the reagent's own composition puts **two** entities in
   `known_target_entities`, not one (see "Reagent identity" below): STAT3, the
   intracellular pharmacological target, and ERBB2/HER2, bound by the carrier.
   A profile covering only the STAT3-binding moiety would not be complete under
   J1.

   The applicable J1 minimum follows from `agent_class`, which §3.3 fixes to one
   of five values — `small_molecule`, `biologic`, `antibody`,
   `genetic_knockdown`, `genetic_knockout` (`AGENT_CLASSES`,
   `src/dt_adoc/perturbations/adjudication.py`). **`biologic` is the fit**: the
   construct is a synthetic phosphopeptide–peptide conjugate. `small_molecule` is
   wrong, and `antibody` is wrong for a reason worth recording — P3-AHNP is a
   peptide *mimetic* derived from an anti-HER2 antibody CDR, not an antibody, and
   §3.6's antibody minimum ("its antigen and a cross-reactivity statement") would
   point at **HER2, the carrier's antigen**, rather than at the STAT3-directed
   moiety that is supposed to do the work. Classing it `antibody` would therefore
   satisfy J1 with evidence about the wrong half of the molecule.

   §3.6 states a minimum source for a small molecule, an antibody and a knockdown
   or knockout, and **states none for a `biologic`**. So J1 is **unassessable**
   for this construct — not failed, not met — until the owner says what a
   `biologic` requires. *This is recorded as a gap in the frozen contract, not
   filled here.* It is also why J1 is not among the refusal's grounds: the
   candidate is refused by items 1 and 2 and by E4, none of which depends on the
   missing standard.

   *An earlier draft of this record called the agent a small molecule, applied the
   small-molecule J1 minimum, and then — after review rejected that — replaced the
   reagent with an unresolved candidate set. Both were wrong, and independent
   review was right to refuse each in turn.*

### Reagent identity, and the ERBB2 consequence

**The reagent is Calbiochem catalogue 573092, "STAT3 Inhibitor Peptide II,
ErbB2-Selective, Cell-Permeable" (P3-AHNP-STAT3BP).** The supplier catalogue
describes it as a STAT3-binding phosphopeptide conjugated to the P3-AHNP carrier
for preferential delivery to ErbB2-high cells, and the supplier's page for the
P3-AHNP carrier states that the carrier contains an anti-HER-2/neu peptide
mimetic developed to target ErbB2-overexpressing cells, naming
P3-AHNP-STAT3BP, Cat. No. 573092 as the delivered construct
(`https://www.sigmaaldrich.com/`, `https://www.merckmillipore.com/`; owner
verification, 2026-10-05).

Two provenance points, because the identification does not come from the cited
experiment. The source names only "a STAT3 inhibitor peptide II (Calbiochem, San
Diego, CA)" with no catalogue number, and the supplier catalogue identifies that
distinctive product name as 573092. The match therefore rests on the product
name, and it is an **E1/E6 identity judgement** — E1 being the agent's identity
and construct, E6 "that the evidence measured this agent, not another of the same
class" (§6.4) — to be stated as such in any declaration. **It is not J3**: §3.6
reserves J3 for `entity@level` readings, which here are the separate judgements
that STAT3 and ERBB2 are engaged at the levels claimed. And a declaration's
`target_profile_sources` must resolve to an
evidence id in the register or a file under the root (§3.3, and the
implementation note's declaration syntax), so a supplier URL is not by itself a
resolving source: admitting this reagent would first require registering the
supplier record as evidence.

**C6 on ERBB2.** ERBB2 is carried by no node of v0.6.0 and appears on neither
§3.5.1 floor list — verified against `config/node_entity_map.tsv`,
`models/superset/adoc-literature-superset-v0.6.0/drug_target_catalog.tsv` and the
staged `candidate_nodes.tsv`, which return no ERBB2 row. It is therefore a known
**unrepresented** engaged entity, classified under J2, at a level (`activity`, the
conservative reading for a receptor-binding carrier) that is itself J3.

**It is classified `out_of_scope`** (owner, 2026-10-05), under the frozen §3.5
definition applied as written. `scope_relevant` requires **both** halves: that
the entity is one *the repository itself treats as acting within the modelled
biology* (§3.5.1), **and** that it sits in a reached compartment. Only the second
holds. ERBB2 is on neither floor list, and no repository source reports it
changing a modelled node or a measured readout in endometrial cells — which is
§3.5.1's standing example of a non-floor entity that still qualifies. So the
first half is unmet, and `out_of_scope` is what the rule gives.

*An earlier revision of this section classified ERBB2 `scope_relevant` on the
ground that no evidence showed HER2 to be irrelevant here. That inverts the
burden §3.5 sets — it requires affirmative relevance, not the absence of a
disproof — and independent review was right to refuse it. Supplying such a basis
without a source would have been inventing biology to reach a chosen
classification, in a record whose subject is refusing exactly that inference.
Stage 4b is not amended to accommodate it.*

**`out_of_scope` is a statement about this model's scope, not about HER2.** It
does not assert that HER2 is biologically irrelevant in endometrial epithelium,
and it does not remove ERBB2 from the agent's profile: ERBB2 stays in
`known_target_entities` for this construct (§3 item 3), and §3.5 carries an
`out_of_scope` entity **verbatim into the run record's claim boundary**. If a
source later reports ERBB2 acting on a modelled node or readout in this system,
the classification changes with it, by §3.5.1's own standing example.

**`compound_claim_blocked` still holds**, through stromal `S_STAT3` alone — a
genuine §3.5.1 floor item, set out below. The ERBB2 classification changes which
grounds carry that flag, not whether the candidate has it, and no result could be
attributed to the named agent either way.

**The verdict is unchanged.** The corrected identity makes the agent's profile
more complicated, not cleaner: it does not supply the missing pSTAT3 measurement,
it does not move the experiment out of the HES line, and it adds a second known
engaged entity to a profile that is already incomplete. Items 1 and 2 remain the
blocking failures.

**The `compound_claim_blocked` ground**, which shapes a future approval rather
than blocking one: the agent is bath-applied, so under §3.5 and the A2 reading
stromal STAT3 is unrepresented in a reached compartment. Unlike ERBB2 it **is** a
§3.5.1 floor
item (`S_STAT3`, `catalog_only`), so it must be declared `scope_relevant` naming
`floor:S_STAT3` — calling it `out_of_scope` is mechanically refused — and the run
would carry `compound_claim_blocked`. Narrowing `reached_compartments` to the
epithelium would remove the obligation but needs a resolving source under C4, and
none exists.

## 4. The two candidates with deeper problems

These are not near misses. Each fails in a way that an improved experiment on the
same agent would not fix.

**anti-LIF / LIF neutralisation → `E_LIF`.** The reagent in the human experiment
is not LIF neutralisation: Fig. 1D used a **LIF antagonist at 500 ng/ml**, cited
to the PEGylated LIF antagonist, which acts at the receptor. For a ligand node
that is `adjacent_level_only`. The experiment is also in the HES line
(Fig. 1 legend, "C and D, HES cells"), and the challenge was exogenous
recombinant LIF rather than endogenous epithelial LIF.

**Engagement depth is not a ground of this refusal.** The source reports the
blockade as abolition — the abstract reads "abolished cytokine induced
phosphorylated STAT3", and `context/evidence-register.tsv` LIT-IL11-001 records
"neutralizing either ligand abolished its own pSTAT3" — while the results text
for the same figure reads "a combination of LIF and a LIF antagonist (9)
diminished pSTAT3". **The source is internally inconsistent on engagement
depth, and this record does not adjudicate which wording governs**, because
nothing here turns on it. Both wordings are recorded so a later reviewer meets
the inconsistency already noted; the O8b §4.1 reading is left to whoever needs
it. The refusal rests elsewhere: pSTAT3 is the
pathway node's proxy, not the ligand node's, so this measurement is engagement of
`E_GP130_STAT3` and not of `E_LIF` however deep it is. (It could not license
`E_GP130_STAT3` either: the system is the HES line, and a LIF-specific antagonist
leaves the IL-11-driven route of that node intact, which the same paper
demonstrates.)

Beneath all of that sits a structural
problem: the map reads `E_LIF` as **LIF@expression**, and a neutralising antibody
engages LIF extracellularly without changing expression, so C7 refuses unless the
declaration asserts `LIF@expression` — a false J3 reading. A receptor-directed
agent is further away still, since C3 would force `E_GP130_STAT3`. Re-reading the
node's level to admit the agent is the move §3.2 and the N+1 gate of §7 exist to
forbid; if the level reading is wrong it is a model-reading decision taken on its
own, before and separately from any admission.

**PC6 perturbation → `E_PC6`.** Read in this session from the held PDF-044 file
(Heng *et al.* 2015): "A previously established HEC-1A cell line with 50%
knockdown of PC6 by stable small interfering RNA (siRNA) transfection", and "The
PC6 knockdown (PC6-siRNA)
cells contain ~50% less PC6". The source quantifies the residual, so O8b §4.1
rule 1 settles it as `target_activity_partially_reduced` with no judgement to
argue, and owner decision 2 keeps graded engagement out of scope. Independently,
HEC-1A is `endometrial_carcinoma_line` and the paper's second system, Ishikawa,
is also carcinoma-derived, so no qualifying system carries the measurement. And
REF-011 is both the knockdown source and a source of the PC6 → DAG1 edges, so
`construction_overlap` would flag it: that source's phenotype result could never
serve as validation of the prediction.

**Provenance caveat on the two quotations above, and what the refusal rests on.**
The repository's lineage does **not** record a full-text inspection of this
paper: `context/literature/pdf_manifest.tsv` carries `full_text_inspected = no`
and `rendering_read = unrecorded` for PDF-044, and the DTR011 verification row
records that the abstract was verified, that the PDF was "not re-read in this
pass", and that quantitative and system details were still wanted. The ~50%
residual and the HEC-1A identification are therefore **session-level full-text
observations**, not canonical facts: neither LIT-PC6-002 nor the DTR011 row
states either of them.

**The canonical refusal rests on the narrower ground**, which those rows do
support: no abolition-grade measurement of PC6 activity is established anywhere
in the record. LIT-PC6-002 and DTR011 show that knockdown *reduces* α-DG-N
removal and that the enzyme and its cleavage product are dissociable; neither
reports PC6 activity abolished. Under O8b §4.1 that is not
`target_activity_reduced`, independently of how much enzyme remains. The session
reading is consistent with that and sharpens it, but the refusal does not depend
on it.

Promoting the session reading to a canonical inspection — updating the manifest
and the verification record with figure anchors — is a separate evidence-lineage
act requiring owner authorization, and it is **not** performed here.

## 5. What was not done

- No row was appended to the evidence register, the declarations table, the
  ledger or the intervention library. The N+1 operation of §7 was not performed.
- No admission criterion, threshold or vocabulary was altered, and
  `config/node_entity_map.tsv`, `config/direct_effect_target_policy.tsv` and the
  model are byte-identical.
- Owner decisions 1–7 and amendments A1/A2 are preserved; decision 7 and §11.2
  were applied as written rather than revisited.
- No candidate was forced through. Where a condition could have been met by
  re-reading a node, a policy row or a source, it was not.
- The §3.6 J1 gap for a `biologic` (§3 item 3) is **recorded, not filled**. This
  record does not supply a minimum source for that class; that is an owner
  decision. The reagent identity was not chosen to make some minimum apply — it
  was established from the supplier catalogue and the class follows from it.

## 6. Stage 4d remains blocked, independently of this refusal

§5.6 unblocks 4d only when **two approved interventions** fall in **different**
non-null observed classes on O. There are zero approvals, so 4d is blocked today
by that condition alone, and this refusal does not change its status.

What follows about the candidates examined, stated precisely so it is not read as
more than it is. `docs/stage4b/v060_veto_expressivity.tsv` places
`E_GP130_STAT3`, `E_LIF`, `E_PC6`, `S_HAND2`, `S_TAZ_ECM` and the migrated
`hand2_loss` in one class (A1). So **admitting the STAT3 candidate alone would
add no distinguishability**: it would be one approval, in a class an
already-running migrated intervention occupies, and one approval cannot satisfy a
two-approval condition in any case. It would additionally run
`compound_claim_blocked` (§3), so its result could not be attributed to the named
agent.

**This does not make the model's observable structure the binding constraint on
4d, and an earlier draft of this section wrongly said so.** The candidate set of
§2 spans two non-null classes, not one: `X_SPP1_LUMEN_FREE` and `E_ITGAVB3_5` are
A2. So two future approvals — one in A1, one in A2 — would satisfy §5.6 under the
frozen rule, with no model change. Resemblance to an unapproved migrated
intervention is not what §5.6 counts, and nothing here licenses weakening or
reinterpreting that rule. What blocks 4d today is the absence of qualifying
engagement evidence for any target, which is the same thing that blocks 4c.

Two separate observations survive that correction, and neither is a 4d gate.
First, the §2a separation is doing visible work: scientific licence, model
expressivity and screen eligibility disagree across this candidate set. Second,
even a satisfied §5.6 would rank arms whose magnitudes are relay priors (§5.3),
so a ranking's informativeness is a different question from its admissibility.

## 7. What would change each answer

Stated as conditions, not as a work plan. None is scheduled by this record, and
§6 is the reason none is proposed as the next priority.

| candidate | condition that would close the refusal |
|---|---|
| Calbiochem 573092 (P3-AHNP-STAT3BP) → `E_GP130_STAT3` | three things, none of which the existing literature supplies. (a) **Measure engagement**: pSTAT3, or a STAT3 target-program readout, under **this construct** at its stated concentration in a §6.3-qualifying system, reported as abolished rather than reduced. One experiment closes E2 and `system_grade` together, because it moves the decisive measurement into a qualifying system. (b) **J1 for a `biologic`**: an owner decision on what §3.6 requires for that class, which it currently leaves unspecified, then a profile covering **both** moieties — the STAT3-binding phosphopeptide and the P3-AHNP/HER2 carrier. (c) **Register the supplier record** as an evidence id or a file under the root, so the identity and profile sources resolve under §3.3. Even then it would be one approval in A1, so on its own it would not satisfy §5.6, and it would run `compound_claim_blocked` through stromal `S_STAT3`, with ERBB2 carried verbatim into the claim boundary |
| anti-LIF → `E_LIF` | a genuine LIF-neutralising reagent, in a qualifying system, abolishing the node's activity — **and**, separately and first, a recorded model-reading decision about the level at which `E_LIF` stands for LIF. Neither substitutes for the other |
| PC6 → `E_PC6` | an agent that abolishes rather than halves PC6 activity, in a §6.3-qualifying system. Construction overlap is **not** an admission condition: §6.5 records it and bars the overlapping source's phenotype result from serving as validation, and it never refuses a licence. It would carry into the claim boundary, not into the gate |
| `E_ITGAVB3_5` | TI-03, which splits αvβ3 from αvβ5 (owner decision 7, §11.3). Not a better agent and not a better declaration |
| `S_PKA`, `E_ANXA2_ACTIN` | a recorded decision about what each node means (§11.2). No approval may resolve one |

## 8. Next unit

Not a compound admission. **Owner decision, 2026-10-05:** the next separate unit
is an **identifiability-driven experimental-design stage** — given one
experimental shot, which perturbation and which additional readouts would
maximally split the current non-hormonal equivalence classes.
`docs/stage4b/v060_veto_expressivity.tsv` with its invariance companion is the
artefact it would be designed against.

The motivation is the equivalence-class structure of §6, and it is a question of
what a result could *tell us*, not of what the admission gate permits: §6 is
explicit that 4d's gate is the §5.6 two-approval condition and that approvals in
A1 and A2 would satisfy it without any model change. Sequencing this unit ahead
of further admission work is the owner's prioritisation and is recorded as such,
not derived from an admission rule. It is recorded here because the independent
review flagged the choice as one a reader should see attributed.

Nothing in that unit requires a declaration, an approval or an executable row,
and it does not reopen any decision recorded here.
