# Scoping decision, 2026-09-30 — pause the modelling line pending `dropout_e2`

**Decision: no new modelling or scoping unit is opened. D2 (CD98/CD9 de-aliasing),
D3 (LIF/IL11/GP130-STAT3 de-aliasing) and the joint D2+D3 package are each
declined now, on measured grounds rather than on priority.** Nothing in the
executable model, the observation map, the frozen Stage-3 design or any
configuration file is changed by this decision. This document records why, and
what would license resuming.

**Provenance of the decision.** The owner asked for this scoping question to be
worked out and named "pause pending `dropout_e2`" as one of the four admissible
outcomes, alongside a narrow next unit, a combined unit, and register-and-defer.
The analysis below was produced in response, the pause was recommended on it, and
**the owner accepted that recommendation and directed that it be recorded as this
note**. So the decision is owner-endorsed, not taken unilaterally; what this
document contributes is the evidence, not the authority. The owner also directed
that no model, configuration or experiment file be changed, which is why none is.

**Scope of the record.** This is a scoping note. It adopts nothing, promotes
nothing and deprecates nothing. Every deferred increment in
`docs/deferred_topology_register.tsv` keeps its existing state and unblock
conditions.

**What the pause does and does not cover.** The pause is scoped to the **v0.5
biological-topology and de-aliasing line** — proposals that would add, split,
rewire or reinterpret nodes, edges, rules, thresholds or phenotypes on
biological grounds. It does **not** prohibit a semantics-preserving
software- or perturbation-layer refactor: a change that leaves every model
prediction identical under every declared condition, and changes only how
perturbations are represented and applied.

This matters for a scalability problem the owner has raised, which is
representational rather than biological. Compound identities are currently
embedded as MaBoSS nodes — `IN_MIFEPRISTONE` and `IN_ANTI_SPP1` are both
declared nodes in
`models/superset/adoc-literature-superset-v0.5.2/network.bnd`, each a free
input read by downstream rules. A future compound screen should not require one
new network node per compound, and refactoring that representation is not the
kind of change this pause declines. **Nothing of the sort is implemented,
designed or authorised here** — this paragraph only records that the pause does
not stand in its way. Such a refactor would need its own unit, its own
equivalence evidence that predictions are unchanged, and its own review.

---

## 1. What was measured

All figures are exhaustive over the 2^19 = 524,288 assignments of the 19 free
variables of `models/superset/adoc-literature-superset-v0.5.2/network.bnd`,
computed for this note with the repository's own analysis
(`dt_adoc.reporting.structure.load_structure`), so every count below is the
repository's quantity under the repository's definition — see the vocabulary box
in §1.1. They **confirm the findings already on record**
(`docs/v05_u3_ac01_no_derivable_rule.md`, `docs/v05_u5_structural_audit.md`), and
are re-measured here because C1 and C5 landed after those units and nobody had
re-run them against v0.5.2.

### 1.1 `E_CD98_CD9` is downstream-inert, and has been since v0.3.0

Clamping `E_CD98_CD9` OFF versus ON changes no other node in the network, under
any assignment. The cause is structural and not incidental:

```
E_CD98_CD9 = E_GP130_STAT3 = E_LIF = E_SECRETORY_STATE and not E_KLF12_HIGH
E_HBEGF    = E_SECRETORY_STATE
```

Every reader of `E_CD98_CD9` sits behind `E_GP130_STAT3`, which entails
`E_SECRETORY_STATE`, which entails `E_HBEGF` — and `E_HBEGF` alone satisfies both
disjunctions that mention CD98. Therefore:

| statement | verified |
|---|---|
| `E_RECEPTIVE_SURFACE` ≡ its five-conjunct prefix alone | yes, all assignments |
| its eight-member "redundant adhesion" disjunction is **vacuous** | yes |
| `X_ADHESION_ROUTE_REDUNDANT` ≡ `E_RECEPTIVE_SURFACE and X_INTERFACE_REDUNDANT_RELAY` | yes |
| `X_ADHESION_ROUTE_SPP1` ≡ `E_RECEPTIVE_SURFACE and X_SPP1_LUMEN_FREE and X_INTERFACE_SPP1_RELAY` | yes |

The repository's own analysis reports the same thing for CD98 directly: at v0.5.2,
`absorbed_edges` contains **both** of its outgoing dependencies —
`E_CD98_CD9 → E_RECEPTIVE_SURFACE` and `E_CD98_CD9 → X_ADHESION_ROUTE_REDUNDANT`.
Nothing it feeds depends on it.

> **Vocabulary, taken from the repository rather than invented.**
> `src/dt_adoc/reporting/structure.py` defines the two quantities this note uses,
> and they are not the same thing: **`phenotype_inert`** is a node whose clamping
> to 0 and to 1 leaves every `OUT_` node unchanged in every enumerated state
> (`OUT_` nodes themselves are excluded from the count), and **`unread_inputs`**
> are free variables no rule reads. All counts below are `load_structure()`'s, so
> they agree with `docs/v05_u5_structural_audit.md` (14 at v0.5.0) and
> `docs/visualization.md` (15 at v0.3.0, with the three consumerless inputs
> counted separately) by construction. An earlier draft of this note used a
> stricter ad-hoc criterion of its own and reported 10 at v0.5.2; that criterion is
> not used in this repository, and it is withdrawn.

**This is not a defect in C1 or TI-01.** `E_PAEP`, `S_PRL` and `S_IGFBP1` became
inert precisely because those units correctly demoted readouts out of phenotype
definitions, removing a circularity. An inert readout still carries information
about the upstream latent state it equals; what it cannot be is a cause.

### 1.2 The v0.5 line produced no de-aliasing

All five rows are `dt_adoc.reporting.structure.load_structure()` output, not a
private computation. `unread_inputs` is 3 in every version (`IN_XAV939`,
`IN_HCG`, `IN_EMBRYO_CONDITIONED_SIGNAL`) and is reported separately from
`phenotype_inert`, as the repository does.

| version | distinct Boolean functions | alias classes | largest | `phenotype_inert` | enumerated states |
|---|---:|---:|---:|---:|---:|
| v0.3.0 | 32 | 7 | 9 | 15 | 262,144 |
| v0.4.0 | 35 | 8 | 9 | 14 | 524,288 |
| v0.5.0 | 35 | 8 | 9 | 14 | 524,288 |
| v0.5.1 | 35 | 8 | 9 | 16 | 524,288 |
| v0.5.2 | 35 | 8 | 9 | 17 | 524,288 |

Each row is exhaustive over that version's own free variables — v0.3.0 has 18, the
rest 19 — which is why the enumerated-state column differs in the first row.

The nine-member epithelial secretory class is unchanged throughout. Stated plainly
so the next unit does not assume otherwise. This is a fact about the function
count, not a criticism of the units: C2 landed as an overlay in `context/` and C3a
was a preregistered run, and neither set out to change an executable rule. The
point is only that **no unit in the v0.5 line separated one**, so a de-aliasing
unit cannot be justified by momentum.

### 1.3 D3's endpoint effect is unreachable in every declared arm

**How this was encoded, since it is not checkable from the network file alone.**
There is no `E_IL11` or `X_IL11` node in v0.5.2 — D3 is a proposed family member
(`GP130-b` in `gate3_candidate_variants_2026-09-16.tsv`), not committed topology.
The measurement holds the committed 19 free variables fixed and evaluates the
variant in its IL-11-supplied limit: with IL-11 present, `E_LIF or E_IL11` is
identically true, so the variant is computed by **clamping `E_GP130_STAT3` to
TRUE** and comparing against the committed network on the same 524,288
assignments. That limit is the most favourable case for D3; a free `X_IL11` input
would add a 20th variable and reproduce this case in half of the enlarged space.

On that comparison, `OUT_MATERNAL_ADHESION_COMPETENCE` differs in **3,200 of
524,288 assignments, and `E_KLF12_HIGH` is true in every one of them.**
`baseline.cfg:31` sets `E_KLF12_HIGH.istate = FALSE`, and no file in `conditions/`
overrides it. The one regime in which D3 would alter a prediction is not
instantiated anywhere.

The qualitative form needs no enumeration: when `E_KLF12_HIGH` is false,
`E_LIF = E_SECRETORY_STATE`, so supplying IL-11 adds nothing; and
`E_RECEPTIVE_SURFACE` requires `not E_PODXL`, i.e. `E_SECRETORY_STATE` true. So
the only regime where an IL-11 disjunct can move an endpoint is exactly
`E_SECRETORY_STATE` true with `E_KLF12_HIGH` true.

### 1.4 The observation layer cannot decide either axis

`config/observation_model_map.tsv` holds 17 rows. Exactly one is an active
constraint (`OM-001`, PAEP), one an active diagnostic (`OM-002`, IGFBP-1) and two
provisional (`OM-006`, `OM-014`, PRL); the remainder are `reported_only` —
including the two multi-analyte composites `OM-009` and `OM-010` — or rejected.
**The three analytes carrying an active or provisional mapping — PAEP, IGFBP-1 and
PRL — are secreted proteins read by ELISA** (`input_tables/adoc_secreted_proteins.tsv`;
`P1-PAEP` records a day-6 ELISA). The composites are weaker than that, not
stronger: `OM-009` and `OM-010` resolve to `P1-EPI-STATE` and `P1-STR-STATE` in
`context/phase1-readouts.tsv`, both at `status = to_specify_signature`, and **no
assay platform is recorded for their markers** (SPP1, DPP4, CEACAM5/6, BMP2, DKK1,
KDR, IL11). So they cannot constrain anything either, for a second and independent
reason. No cell-associated readout has ever been run on the platform: surface
CD98, CD9, pSTAT3 and α-DG-N are proposed measurements, not existing assays.

The three ELISA analytes map onto two latent functions
(`E_SECRETORY_STATE`, `S_DECIDUALIZED`),
and while every arm moves the cocktail as a bundle they are one design class —
which is the standing reason the frozen Stage-3 choice is a single-agent dropout.

---

## 2. Primary-literature re-check

`docs/v052_paep_hand2_cleanup.md` §6 already records that, of the four papers
previously cited for LIF/IL11 convergence, **only Marwood 2009 carries it**. That
is confirmed independently here (Cullinan 1996: no IL-11 and no STAT3 anywhere;
Chung 2016: one IL-11 mention, no STAT3; Yap 2011: no LIF arm, consistent with the
full-text read recorded in `docs/v05_u4_gp130_axis.md` §1). One finding sharpens
it, and it is new to the record.

**In Marwood 2009 the upstream convergence is primary-cell evidence, but the
functional STAT3 dependence of adhesion is cell-line evidence, and the
primary-cell functional results diverge by ligand.** Read 2026-09-30 from the local PDF
library, which is gitignored and present only in the main checkout, so the read is
recorded by digest rather than by path — sha256
`0aecddeb59a70622655e6c01298b900b32b2e99e198c747fbdbaa5dc53f6a681`, 9 pages:

| result | figure | system |
|---|---|---|
| IL-11 and LIF each induce pSTAT3 | 1A, 1B | primary human EEC |
| **STAT3 inhibition reduces both cytokines' fibronectin adhesion** — the functional STAT3 dependence of adhesion | **2B** | **HES cell line** |
| Neutralising anti-IL-11 **reduced**, and a LIF antagonist **diminished**, cytokine-induced pSTAT3 — the Results' wording; the abstract says the same interventions "abolished" it (see the note below) | 1C, 1D | **HES cell line** |
| IL-11 but not LIF raises trophoblast adhesion to EEC | 2C | primary EEC + primary first-trimester trophoblast |
| α2β1 blockade reduces LIF- but not IL-11-induced collagen-IV adhesion | 6A, 6B | primary EEC |

The Methods state HES was used "for the extended experiments in which
insufficient primary EECs were available." Three distinct statements follow, and
they must not be collapsed:

1. **The upstream convergence has primary-EEC evidence.** Fig 1A/B shows both
   IL-11 and LIF inducing pSTAT3 in primary human EEC. The step that
   `E_LIF or E_IL11 → E_GP130_STAT3` represents is therefore *not* a cell-line-only
   result, and this note does not claim it is.
2. **The functional STAT3 dependence of adhesion is HES.** Fig 2B — STAT3
   inhibition reducing both cytokines' fibronectin adhesion — is the cell-line
   result, as are the reagent controls in 1C/1D. So it is the *functional*
   link from the shared node to an adhesion phenotype, not the convergence itself,
   that rests on HES.
3. **The primary-cell results diverge by ligand.** Fig 2C (IL-11 but not LIF
   raises trophoblast adhesion) and 6A/6B (α2β1 blockade reduces LIF- but not
   IL-11-induced collagen-IV adhesion) are primary-EEC results in which the two
   ligands behave differently downstream.

The consequence for D3 is (3), not (1): a single shared `E_GP130_STAT3` node
cannot represent ligand-specific divergence that primary-cell experiments show,
and the one experiment tying the shared node to adhesion function is in a cell
line. The re-audit's 9/10 confidence that the identity is incomplete is not
supported at that level for an executable rule, and D3's evidential standing
should be read through this table rather than through the convergence claim
alone.

> **The paper is internally inconsistent about the strength of 1C/1D, and this
> note does not resolve it.** Its abstract states that adding IL-11 neutralising
> antibody or a LIF antagonist "abolished cytokine induced phosphorylated
> STAT3". Its Results say the anti-IL-11 co-culture "reduced pSTAT3" (1C) and
> the LIF antagonist "diminished pSTAT3" (1D). Figs 1C/D are representative
> Western blots — the legend reports duplicate wells across three independent
> experiments, with no densitometry — so the paper supplies no quantity from
> which residual cytokine-induced pSTAT3 could be established or excluded.
> This note therefore quotes the Results' wording, records that the abstract is
> stronger, and asserts neither abolition nor non-abolition. Nothing in §2's
> argument turns on which is right: 1C/1D are cell-line reagent controls either
> way, and the consequence for D3 comes from (3) below.

Domínguez 2010 (sha256
`fb767f1080f7b241c79aaf7efd294a73a9db66f96af7ec120e0def93ea686709`, 11 pages)
re-checked for D2: CD98 induction by
hCG, 17β-estradiol, LIF and EGF, and the CD98 and CD9 overexpression/silencing
adhesion effects, are all real — but the perturbation experiments are **HEC-1-A
with mouse blastocysts**, and the primary-EEC work is expression, localisation
and co-immunoprecipitation only. Well-evidenced biology, attached to an inert
node.

---

## 3. Status of each remaining deficiency

| item | class of work | status |
|---|---|---|
| D2 — CD98/CD9 split | **bookkeeping** | A split or rewire **confined to the current absorbed readers** cannot change an endpoint, so it buys nothing today; a future literal split that also gave CD98 or CD9 a new route or an unabsorbed reader is **not** covered by that and is not guaranteed inert. No adopted exact literal split, so no licensed exact function count — see the note below. No assay either way. Declined. |
| D3 — LIF/IL11/STAT3 | **executable in principle, empty in practice** | 35→37, but its only effect needs `E_KLF12_HIGH` ON; needs supplied IL-11 *and* LIF neutralisation *and* pSTAT3. Declined. |
| D2+D3 (`GP130-c`) | as above | 35→38 for the staged package as recorded — see the note below. Same emptiness. Declined. |
| TI-06 — MUC1 split | evidence unit | Blocked: no human determinant of local clearance. |
| TI-03 — αVβ3/αVβ5 | evidence unit | Blocked: U3 found no second AC01 determinant outside `E_SECRETORY_STATE`; the β5 evidence rests on Paule 2012 Fig 4 alone. |
| TI-04 — PRL/IGFBP1 | design-blocked | Needs the single-agent dropout, i.e. `dropout_e2` itself. |
| D6 — mechanical permissiveness | evidence unit | Blocked: `IN_ER_STRESS_EXCESS` and `IN_HIGH_ECM_STIFFNESS` are not varied by ADOC. |
| D5, D7, window-closing, mifepristone binarity | Tier B | Unchanged; none newly actionable. |

> **What the function counts do and do not attach to.** The recorded **35→36**
> is the CD98 *rewire* measured in
> `context/literature/reviews/deep_research_drug_targets_2026-09-16.next-stage.md`,
> where it is listed as "CD98 via embryo cue (**no new node**)" — a rewire of
> the **still-merged** `E_CD98_CD9` node, the family `CD98-b` and `CD98-c` belong
> to. (`CD98-d`, U4's later staging of TI001's literal rule text, is the same
> shape of merged-node rewire but was deliberately **not** backdated into that
> September-16 ledger; see `docs/v05_u4_gp130_axis.md` §3.1.) None of them is a
> measurement of a literal CD98/CD9 split. A true D2 split
> (`E_CD98` separate from `E_CD9`, possibly with a microdomain or its own route)
> has **no adopted exact Boolean rule anywhere in this repository**, and
> therefore no licensed exact function-count delta; quoting one for it would be
> inventing a rule. Likewise **35→38** is that same source's "both together" row
> — the staged Gate-3 GP130 variant plus a merged-CD98 rule — not an arbitrary
> future literal D2+D3 split.
>
> The structural conclusion does not depend on any of those numbers, and is the
> stronger statement: **with the current absorbed readers, rewiring or splitting
> CD98 cannot alter any endpoint as long as the change stays confined to those
> readers.** Both of `E_CD98_CD9`'s outgoing edges are in `absorbed_edges` (§1.1),
> so whatever rule a split gave either part, nothing downstream reads it. That
> holds until the redundant-adhesion structure itself is repaired — resume
> condition 3.

---

## 4. What remains before `dropout_e2`

**No modelling unit and no owner-decision unit.** `dropout_e2` is
interpretation-frozen: `docs/phase1b_closure/pre_run_analysis_addendum.tsv`
records 22 owner decisions across three rounds, all 2026-09-24 — G1–G8 and P0;
RQ1–RQ6, G3R and G4R; MS1, SPB1, AL1, RAT1 and SPP1X — and
the generated `prospective_dropout_e2_handoff.md`, under **Pre-run decisions**,
states that no pre-run question is open.

What remains is **operational only**, and belongs to the run rather than to the
model:

1. complete `prospective_allocation_manifest_template.tsv` with real source,
   chip, position and order IDs before treatment begins; it reads
   `REQUIRED_PRE_RUN_MANIFEST` until then (AL1);
2. record a documented per-analyte detection limit for PAEP, IGFBP-1 and PRL in
   `prospective_assay_metadata_template.tsv` before anything is classified (MS1);
   the historical 5 pg/mL figure is manuscript prose and is not used.

Then wait for the experimental data.

---

## 5. Resume conditions

Resume when **any one** of these becomes true. Until then, opening a unit on this
axis spends a review cycle to add rule-variant rows the register already holds.

1. **`dropout_e2` returns data.** It breaks the `E_PAEP`/`S_IGFBP1` design class,
   makes TI-04 and the SEC fork decidable, and is the only separator of `CD98-c`
   from `CD98-x`. Re-rank everything against the result before choosing a unit.
2. **A cell-associated assay is funded on the platform** (surface CD98 and CD9
   separately, pSTAT3, α-DG-N). This makes D3 measurable. It does not by itself
   make D2 useful — see 3.
3. **The redundant-adhesion structure is repaired first.** While
   `E_RECEPTIVE_SURFACE` hard-conjoins `E_GP130_STAT3` and its disjunction is
   absorbed by `E_HBEGF`, no rewiring of CD98 can reach an endpoint. This — not
   the CD98 split — is the Tier-A defect on this axis, and it is a larger unit
   than D2 or D3.

### Sufficient evidence to proceed to an executable model version

- **D3:** a membrane or adhesion experiment with a **LIF comparator in primary
  human EEC** (Yap 2011's design plus the arm it lacks), or STAT3-dependence of
  adhesion demonstrated in primary EEC rather than HES — together with an ADOC
  arm in which the node is not saturated.
- **D2:** a repaired redundancy structure giving `E_CD98_CD9` a reader that is
  not absorbed, plus separate surface CD98 and CD9 measurement in
  hormone-conditioned human ADOC.

Neither is close. Both are specific enough to cost.

---

## 6. What this note did not do

It changed no rule, node, edge, threshold, rate, istate, condition or phenotype;
created no model version; touched no file under `models/`, `config/`,
`docs/experiments/`, `docs/phase1b_closure/`, `docs/phase2a/` or `docs/scrna/`;
reopened neither C3a nor C4; reran no simulation and spent no seeds; and altered
no part of the frozen `dropout_e2` design or its addendum.
