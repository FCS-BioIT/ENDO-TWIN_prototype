# Next stage: deep-research drug/perturbation review (2026-09-16)

Adjudication of the staged external review. Written 2026-09-16.

## Status in one line

**Filed, adjudicated, not integrated into the canonical layer.** No canonical
literature table, no catalog and no model file has been modified. v0.4 is
untouched. The staged source is preserved verbatim.

**`config/coupling_adjudication.tsv` is the exception**, and an earlier version
of this line wrongly included it in the list above. This batch's
primary-verification pass changed the `IN_cAMP` and `S_PKA` verdicts and
corrected the `E_CD98_CD9` rationale there; see the staging-status note and
`...primary-verification.tsv` for the rows and the reasons.

| Path | What it is |
|---|---|
| `context/literature/staging/deep_research_drug_targets_2026-09-16/` | the verbatim external review. Immutable. |
| `…reviews/deep_research_drug_targets_2026-09-16.adjudication.tsv` | **binding** decisions, DTR001–DTR025 |
| `…reviews/deep_research_drug_targets_2026-09-16.topology-implications.tsv` | model consequences, TI001–TI016, kept separate from catalog changes |
| this file | the audit narrative |

## 0. The review read a stale commit, and it matters

The review states it read `main` at **`3715da1`**. `main` is now `01a63d1`.
Between them, `7e75da6` revised Gate 2 and `01a63d1` repaired four review
findings. Three of the review's "recommended immediate changes" are therefore
**already implemented**, and one rests on a false premise:

| Review recommendation | Actual state |
|---|---|
| Reclassify `E_LIF`/`E_GP130_STAT3` from `BIOLOGICALLY_COLLAPSED` | **Already `ARTIFICIALLY_COUPLED`** since `7e75da6` |
| Keep the anti-SPP1 fourth arm provisional | **Already enforced in code**, with a test that sandboxes a repurposed file and requires refusal |
| Keep `S_PRL`/`S_IGFBP1` out of the drug layer | Already true — neither is in the catalog |
| Replace the interface relays' drug-target entries | **No relay has a catalog row.** Nothing to replace |

That the review reached the `E_LIF`/`E_GP130_STAT3` verdict independently — from
primary human endometrial literature, where Gate 2 reached it from the catalog —
is the most reassuring thing in the bundle. Two routes, one conclusion.

## 1. The most important finding is about the criterion, not the biology

**`target_class` is free text with near-unique values: 24 distinct values across
34 rows, 17 appearing exactly once.**

The Gate 2 invariant fires when a rule-induced merge contains executable targets
of *different* `target_class`. Of the five alias classes holding ≥2 executable
targets it fired on three and not on two — and what stopped it firing on the
barrier trio is that somebody happened to give `E_PODXL`, `E_DAG1_FULL` and
`E_MUC1_BARRIER` the same coarse label `anti_adhesive_surface`, while
`adhesive_effector` lumps a glycoform (`E_MUC1_SLEX`), a transmembrane complex
(`E_CD98_CD9`) and a junction protein (`E_CDH1_APICAL`).

So the invariant is **partly an artefact of naming granularity**. The review is
right that the catalog must not be a druggability-driven topology filter; the
sharper local problem is that it is currently a *vocabulary*-driven one. This is
DTR020 and TI016, and it should be fixed before any further Gate 2 movement.

**The repository already has a better axis, and it is not druggability.** The
node dictionary curates `model_role` and `measurement_proxies` per node:

| alias class | distinct `model_role` | distinct `measurement_proxies` |
|---|---:|---:|
| `E_ANXA2_ACTIN` (9) | 6 | 9 |
| `OUT_STROMAL_DECIDUALIZED` (6) | 5 | 6 |
| `E_IHH` (5) | 3 | 4 |
| `E_CD98_CD9` (3) | 3 | 3 |
| `E_DAG1_FULL` (3) | **1** | 3 |
| `E_RECEPTIVE_SURFACE` (2) | 2 | 2 |
| `E_CDH1_APICAL` (2) | 2 | 2 |
| `IN_cAMP` (2) | 2 | 2 |

`E_LIF` (proxy *LIF expression or secretion*, role `attachment_gate`) is one bit
with `E_GP130_STAT3` (proxy *pSTAT3 or target-program activity*, role
`pathway_gate`). `E_SPP1_EXPR` (role `ligand_source`) is one bit with
`E_ITGAVB3_5` (role `adhesion_receptor`) — **a ligand and its own receptor**.
This is internal to the model, needs no catalog, and cannot be gamed by drug
availability. It is also the axis that reaches `E_SPP1_EXPR`, which the catalog
axis misses exactly as §8 of the brief anticipated.

It must be **reported, never verdict-forcing**: role-distinctness alone would
fire on `E_PAEP` (readout) against `E_SECRETORY_STATE` (state), which both the
brief and the current adjudication decline. The barrier trio is the useful
control — one `model_role`, three proxies, and deliberately still `UNIDENTIFIED`.

## 2. What the structural probe measured

Every candidate was applied to an in-memory copy of v0.4's rules and the
rule-induced partition recomputed. Nothing was written. **Distinct Boolean
functions is the currency**: a node that adds none adds no expressive power.

| Variant | Δ functions | Effect |
|---|---:|---|
| CD98 via embryo cue (**no new node**) | 35 → 36 | splits `E_CD98_CD9` out |
| IL11 as an independent free ligand | 35 → 37 | splits `E_LIF` out |
| **both together** | 35 → **38** | GP130 axis fully separated into three |
| `S_NR2F2` competence determinant *(placeholder, withdrawn — §2a)* | 35 → **38** | `E_IHH`(5) → three classes |
| `E_PC6` own determinant | 35 → **38** | breaks **two** classes at once |
| `E_ITGAVB3_5` own determinant | 35 → 37 | splits the integrin out |
| **CD98 + IL11 + NR2F2 together** | 35 → **41** | +6 states for +2 nodes |
| `X_IL11` **as staged** (`= S_DECIDUALIZED`) | 35 → 36 | splits GP130 but grows the decidual class to **7** |
| `S_BMP_SMAD` **as staged** (`= S_BMP2`) | 35 → **35** | grows `E_IHH` to 6. **Inert** |
| full staged BMP chain | 35 → **35** | grows `E_IHH` to 8. **Inert** |
| BMP chain *after* the stromal repair | 41 → **41** | still inert, plus a new alias |
| `S_EPAC_RAP1` as staged | 35 → 35 | grows the cAMP class to 3. **Inert** |
| PRL intermediate (Gate 3a) | 35 → **35** | **inert at the fixed point** |

Three of these overturn or redirect a review recommendation.

### The BMP recommendation is aimed at the wrong end of the relay

The review says the BMP chain "gives you a biologically much better route for
breaking the current `PGR/IHH/NR2F2/BMP2` alias". **Measured: it does not break
it at all.** The alias is caused *upstream* — `E_IHH = E_PGR = S_PGR =
IN_PROGESTIN and not IN_MIFEPRISTONE` — and nothing added downstream of `S_BMP2`
touches that, in any variant tested, including after the stromal channel is
otherwise repaired. What breaks it is a determinant at the **receiving** end.

The biology in the review's BMP section is good and is accepted (DTR007). The
*remedy* is misdirected (DTR008). **But "a determinant at the receiving end" is
a structural result, not a proposal** — see §2a, where the obvious candidate is
withdrawn.

### 2a. What that receiving-end determinant should be — and why none is yet justified

An earlier draft of this note proposed a free `S_NR2F2` "epithelial competence"
input because it splits the class three ways for 35 → 38. **That is withdrawn.**
It was reverse-engineered from the partition: a bit with no biological
semantics, no measurement and no perturbation. Improving the partition is
evidence that *a* determinant is structurally useful, never evidence that *this*
latent variable is the right one — which is the exact error this whole review
exists to prevent.

Four representations were examined.

| Candidate | Verdict |
|---|---|
| free `S_NR2F2` competence input | **reject** — invented latent variable |
| `S_NR2F2_ACTIVITY` (abundance vs transcriptional activity) | **reject** — the node's own `measurement_proxies` already read *expression or regulon activity*; a second abstraction over one quantity, with no independent determinant |
| stromal **IHH/PTCH/SMO/GLI reception state** | **best grounded, still not promotable** |
| no new node | **adopted** |

The Hedgehog reception state deserves the detail, because it is the right
*location* and still fails:

- **Not invention.** `docs/adoc_dt_implementation_spec.md:284` names the chain
  verbatim — `IHH-PTCH-SMO-GLI-NR2F2-HAND2-BMP2-WNT4`. The executable model
  dropped the reception step; the spec never did.
- **Measurable.** `PTCH1` and `GLI1` are themselves Hedgehog target genes and
  are the canonical pathway-activity readout — not a proxy invented for this.
- **Perturbable, specifically.** SMO antagonists are a well-characterised class.
- **And measured to buy nothing.** As a pass-through (`S_HH_RECEPTION = E_IHH`)
  it is **inert: 35 → 35**, and it grows the `E_IHH` class from five to six —
  the `S_BMP_SMAD` failure mode exactly, one level up. Given a competence
  conjunct it reaches 38 but leaves a **new** `S_HH_RECEPTION ≡ S_NR2F2` alias,
  so it *relocates* the unknown instead of resolving it, at the cost of a node.
- **Species.** `REF-025` (Franco 2010) and `REF-026` (Kurihara 2007) are both
  mouse uterine conditional knockouts, and `LIT-IHH-001` itself records that
  "human attachment causality is partly transferred from mouse uterine
  genetics".

**Conclusion: no new node is yet justified.** What would change it is human or
ADOC Hedgehog-pathway-activity data — `PTCH1`/`GLI1` induction in stromal cells
under the ADOC protocol, or an SMO-antagonist arm. Structural gain alone must
never be the reason.

### 2b. A documented edge that turns out to be already wired — and harmful to add

`LIT-IHH-001` states the relay "suppresses nonreceptive epithelial
proliferation", and `S_NR2F2` has exactly one out-edge (to `S_BMP2`). That looks
like an unwired documented consequence of the same shape as the CD98/hCG
finding. It is not: the arm is **already represented**, through `S_HAND2 →
S_FGF_MITOGENIC → E_ESTROGENIC_PROLIFERATION`.

Adding a direct `not S_NR2F2` repression on top is measured to make the model
**worse: 35 → 34**, merging `E_LIF`, `E_GP130_STAT3`, `E_CD98_CD9`,
`E_RECEPTIVE_SURFACE` and `OUT_EPITHELIAL_RECEPTIVE` into one five-member class.
It absorbs the `IN_HAND2_LOSS` sensitivity and collapses the epithelial
receptive axis. **Rejected** (DTR027).

### 2c. A fifth absorbed conjunct, found on the way

Checking 2b turned up one the Gate 2 enumeration missed.
`S_FGF_MITOGENIC = not S_HAND2`, so `S_FGF_MITOGENIC and not S_HAND2` in
`E_ESTROGENIC_PROLIFERATION` reduces to `not S_HAND2`: **the FGF intermediate
contributes nothing**. Same class as the four already pinned (`E_PAEP`,
`S_PRL`/`S_IGFBP1`, `E_ITGAVB3_5`, `S_TAZ_ECM`), and it should join them in
`tests/unit/test_coupling_adjudication.py`.

Consequence worth stating: HAND2 loss and an FGF9-level perturbation are **one
intervention** in this model, so the review's own recommendation to probe FGF9
separately from HAND2 currently has no model image (DTR028).

### The staged IL11 implementation is worse than the alternative

The review's direction is right and the evidence is the best in the bundle. But
`candidate_nodes.tsv` gives `X_IL11` `logic_hint = S_DECIDUALIZED`, which puts
IL11 **inside the six-member decidual alias class** — the exact class Gate 3a
exists to break. As an independent free ligand it costs nothing and yields one
more distinct function. Stage the second form.

### Gate 3a cannot be evaluated by this machinery at all

Routing PRL through an intermediate is **inert at the fixed point** (35 → 35).
That independently confirms what `results_reproducibility_matrix.md` already
recorded: the IGFBP-1-before-PRL claim lives only in the transient. No
fixed-point partition can test it, which is why Gate 3a needs a transient
readout and why no structural argument will ever settle it.

## 3. Deliverable C — current-catalog corrections

| Row | Correction | Why |
|---|---|---|
| `E_LIF`, `E_GP130_STAT3` | **split conceptually**; keep both rows, retype by level | ligand availability vs pathway activity |
| `E_DAG1_CLEAVED` | **demote from `executable`** | a cleavage *product*; you perturb the protease |
| `E_MUC1_SLEX` | **demote to genetic/mechanistic probe** | reachable only via FUT3/ST3GAL3, absent from the model |
| `X_MECHANICAL_PERMISSIVE_ECM` | **demote to observation/state** | `model_role = latent_state`, derived; stiffness inputs already exist |
| `E_ESTROGENIC_PROLIFERATION` | **demote to observation/state** | derived proliferative state; act on ESR1 or `IN_E2` |
| `E_KLF12_HIGH` | **demote to genetic probe** | genetic only; the repository's own scRNA work declined any prior |
| `S_FGF_MITOGENIC` | **demote to genetic/ligand probe** | derived (`not S_HAND2`); perturb FGF9 |
| `IN_HCG`, `IN_EMBRYO_CONDITIONED_SIGNAL` | keep `executable`, **flag zero model consequence** | manipulable, but read by no rule |
| `E_PGR`, `S_PGR` | annotate **multi-receptor** | mifepristone engages GR and AR; not a clean PGR knockout |
| `E_ITGAVB3_5` | annotate **αv-family probe, not αvβ3-only** | cilengitide is not a clean switch |
| `PERT-003` (`perturbations.tsv`) | **split** | its target field is literally the string `E_LIF/E_GP130_STAT3` |

**None of these is applied here.** Demoting six rows removes their *catalog*
ground for `ARTIFICIALLY_COUPLED`. Their verdicts should **not** revert, because
the node-dictionary axis separates them independently — which is precisely the
argument for landing TI016 before the demotions.

## 4. Deliverable D — execution-status audit

**A — credible executable perturbation:** `E_PGR`/`S_PGR` (multi-receptor),
`E_LIF` (recombinant + neutralising antibody), `X_IL11`, `E_ITGA2B1` (blocking
antibody), `X_SPP1_LUMEN_FREE` (anti-SPP1), `E_ITGAVB3_5` (blocking antibody),
`S_BMP2` (recombinant), `X_ECM_FN1_COL4` (matrix composition),
`IN_HIGH_ECM_STIFFNESS` (defined stiffness).

**B — genetic or mechanistic probe only:** `E_GP130_STAT3` (STAT3 RNAi; JAK
inhibitors are not STAT3-specific), `S_BMP_SMAD`, `S_WNT4_CTNNB1`, `S_FOXO1`,
`S_HAND2`, `E_PC6`, `E_CD98_CD9`, `E_SOX17`, `E_JAG1_NOTCH3`,
`E_GLYCOSYLATION_PROGRAM`, `E_KLF12_HIGH`, `S_FGF_MITOGENIC`, `E_MUC1_SLEX`.

**C — theoretical, no ADOC-suitable specific intervention:** `S_AKT_EXCESS`,
`S_ERK`, `S_TGFB_CONTEXT`, `S_TAZ_ECM` *as a drug target* (perturb mechanics
instead), `E_ANXA2_ACTIN` *as a clean target* (cytoskeletal agents are
pleiotropic).

**D — observation/state only:** `E_PAEP`, `S_PRL`, `S_IGFBP1`,
`E_SECRETORY_STATE`, `S_DECIDUALIZED`, `E_RECEPTIVE_SURFACE`,
`E_ESTROGENIC_PROLIFERATION`, `X_MECHANICAL_PERMISSIVE_ECM`, `E_DAG1_CLEAVED`,
all four `OUT_*`, and **all four `X_*_RELAY`** — which have no catalog rows and
must never acquire any.

## 5. Deliverable G — Gate-2 changes that genuinely follow

Only one adjudication changes on the new evidence, and it is a rationale
amendment rather than a verdict change:

- **`IN_cAMP` / `S_PKA`** — verdict stays `BIOLOGICALLY_COLLAPSED`; the
  rationale must stop implying biological equivalence. Its own stated reopening
  condition ("evidence that a cAMP effector other than PKA carries part of the
  decidual response") **is now met** by the human ESC EPAC/RAP1 result. The
  honest label is *a deliberate simplifying abstraction whose reopening
  condition has been satisfied and whose replacement is not yet representable* —
  the proposed node is measured inert.

No verdict flips. `E_LIF`, `E_GP130_STAT3`, `E_CD98_CD9`, `E_ITGAVB3_5`,
`S_PRL`, `S_IGFBP1`, `E_PC6` and `S_TAZ_ECM` are already `ARTIFICIALLY_COUPLED`
and the new review strengthens rather than changes them. The barrier trio stays
`UNIDENTIFIED`. **Gate 2 is not re-run.**

## 6. Deliverable H — staged-candidate disposition

| Candidate | Disposition | Reason |
|---|---|---|
| `X_IL11` | **rule variant (corrected form)** | strongest new evidence; stage as a free ligand, not the staged hint |
| `S_BMP_SMAD` | **unresolved** | biology accepted, representation inert as staged |
| `S_WNT4_CTNNB1`, `S_FOXO1` | **unresolved** | same; pass-through chain adds nothing |
| `E_ITGA2B1` | **reject at `verified`; candidate only** | DRE009 stands — see §7 |
| `E_GLYCOSYLATION_PROGRAM`, `E_SLEX_SURFACE` | **candidate** | do not replace a committed node with an inert pair |
| `X_ECM_FN1_COL4` | **candidate, high value** | biochemical ECM is separable from mechanical ECM and cheaply perturbable |
| `E_SOX17`, `E_JAG1_NOTCH3` | **candidate** | good genetic evidence, no measured structural gain yet |
| `E_ESR1_ACTIVITY` | **candidate** | distinct from the protocol bit `IN_E2` |
| `S_AKT_EXCESS`, `S_ERK`, `S_TGFB_CONTEXT` | **catalog only** | sensitivity analysis, not topology |
| `S_EPAC_RAP1` (new) | **catalog only / staged** | evidence accepted, node inert |
| `S_IGFBP1` outgoing edge (new) | **unresolved, gated** | a causal edge from a calibration readout needs its own leakage control |

## 7. `X_IL11 → E_ITGA2B1`: the prior adjudication stands

The new review **corroborates** the 2026-09-11 rejection of DRE009 rather than
overturning it. Its own table records α2β1 blockade against the **LIF-induced**
collagen-IV response, not the IL11-induced one. By level:

| Claim | Status |
|---|---|
| IL11 → STAT3 | **supported** |
| IL11 → ITGA2 abundance | **supported** |
| IL11 → *active* α2β1 adhesive receptor | **not established** |
| LIF-dependent α2β1 function | **supported** |
| IL11-specific α2β1 necessity | **not established** |

`E_ITGA2B1` is staged as `role = adhesive_receptor`, `measurable: surface
ITGA2/ITGB1`. Abundance evidence does not reach a receptor-activity state.
DRE009 stands, including its 2026-09-14 clarification that redefining the node
to an abundance state requires a **new** adjudication and may never be inferred
from that row.

## 8. Deliverable I — perturbation × readout shortlist

Ranked by *topology discrimination*, not by translational appeal, and honouring
the maternal-vs-challenge cost split: maternal arms need no embryos.

### 1. GP130-axis decomposition — **embryo-free, discriminates three implications at once**

- **Perturbation:** four maternal-phase exposures — vehicle; recombinant LIF;
  recombinant IL11; hCG or embryo-conditioned medium — each ± STAT3 knockdown.
- **Level targeted:** ligand availability (LIF, IL11) vs pathway activity
  (STAT3) vs embryo-cue-driven effector (CD98/CD9).
- **Proximal engagement readout:** pSTAT3 / nuclear STAT3 — *not* STAT3 RNA.
- **Secondary mechanistic readout:** surface CD98/CD9; surface ITGA2.
- **Functional readout:** FN and collagen-IV adhesion (embryo-free).
- **Separates:** TI001, TI002, TI004 — i.e. whether `E_CD98_CD9` is downstream of
  STAT3 (v0.4) or of embryo-conditioned cues (`LIT-CD98-001`), and whether
  `E_GP130_STAT3` has a LIF-independent input.
- **Result patterns:** CD98 rises on hCG without pSTAT3 → TI001 confirmed, the
  no-new-node repair is justified. pSTAT3 rises on IL11 with LIF neutralised →
  TI002 confirmed. Neither → the collapse survives, on evidence rather than by
  default.

This is the one to run if only one is possible. One exposure set, no embryos,
three topology questions.

### 2. PC6 loss with a DAG1-processing readout

Highest measured structural leverage (breaks **two** classes). Perturbation:
PCSK5/PC6 knockdown. Proximal: α-DG N-terminal shedding — not PC6 RNA.
Functional: adhesion. Separates TI009. Needs embryos for the functional arm.

### 3. αvβ3 blockade — **explicitly deferred**

Attractive biologically and **should not be run yet**: `E_ITGAVB3_5` is absorbed
in all 2¹⁹ = 524,288 assignments, so the model cannot represent the perturbation.
Running it first would spend embryos against a model mathematically incapable of
predicting the result. Repair TI010 first. This is the review's own point and I
endorse it.

## 9. Deliverable J — v0.5 implications

**Sufficiently supported to enter v0.5:** nothing yet, as a topology change.
The best-supported single edit (TI001, CD98 via embryo cue) should enter as an
**admissible rule variant** first.

**Rule variants:** TI001 (CD98 rewire), TI002/TI004 (independent IL11 ligand).

**Candidates:** glycosylation/sLeX pair, `X_ECM_FN1_COL4`, `E_SOX17`,
`E_JAG1_NOTCH3`, `E_ESR1_ACTIVITY`, `S_EPAC_RAP1`, the `S_IGFBP1` outgoing edge.

**Unresolved, pending a determinant:** the IHH reception step (TI005/TI017),
BMP pathway state (TI008), PC6 regulation (TI009), integrin state (TI010). Each
has a measured information value and no local evidence for the determinant that
would realise it. These are the targeted evidence-gathering questions — and note
that for the IHH step the best-grounded candidate (a stromal PTCH/SMO/GLI
reception state) is measured to be inert on its own, so the open question is the
*competence* of that step, not the step itself.

**Rejected:** the staged `X_IL11` form (TI003), `S_BMP_SMAD` and the full BMP
chain as staged (TI006, TI007), the claim that the BMP chain repairs the stromal
alias (DTR008), the premise that interface relays have catalog rows (DTR014), a
free `S_NR2F2` competence node (DTR026), and a direct NR2F2 repression edge onto
epithelial proliferation (DTR027, measured to reduce expressive power).

**Ordering.** TI016 first — fix the criterion before moving anything it judges.
Then the rule variants. Then the prospective experiment. Topology promotion last.

## 10. Provenance and limits

- The staged source is preserved verbatim; nothing in
  `context/literature/staging/` was modified.
- `models/superset/adoc-literature-superset-v0.4.0/` is untouched, as is
  `config/coupling_adjudication.tsv`, `drug_target_catalog.tsv` and
  `context/literature/perturbations.tsv`.
- The structural measurements are reproducible from the committed `network.bnd`
  by exhaustive evaluation over the 19 free variables. They are **structural**:
  no simulation, no horizon, no rate, no fitted parameter.
- **Every external evidence claim is accepted on the review's report of it.** No
  primary full text was opened in this adjudication. Any promotion resting on
  DTR002, DTR006, DTR011 or DTR017 needs full-text verification first.
- The Gate 0–2 increment these decisions build on carries **same-vendor,
  degraded** review only: Codex was unavailable and a stand-in from the
  author's model family reviewed the work. Nothing here changes that, and any catalog or topology
  promotion should receive independent review before it lands.
