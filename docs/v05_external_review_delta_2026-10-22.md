# External-review delta and SETD7 three-way adjudication — 2026-10-22

**Status:** delta analysis, submitted for owner approval. Nothing here is executed.
**Supplements, does not replace:** `docs/v05_literature_guided_implementation_plan_DRAFT.md`.
**Authoring:** AI-assisted session; the assistant model was switched once
mid-session. **Every adjudication below was performed by the second model. No
review from the first model was obtained and none is claimed.**

> **Discipline.** Each fact appears once. The per-candidate reconciliation lives
> in `docs/v05_external_review_delta_2026-10-22.tsv` (31 rows × 17 columns) and
> is **not** restated here. This document carries only what the table cannot: the
> SETD7 adjudication, the structural consequences, and the plan impact.

## 1. Inputs and their standing

Two external artifacts were supplied and are preserved byte-unchanged at
`context/literature/reviews/prototype_scientific_review_2026-10-21.md` and
`context/literature/reviews/prototype_candidate_rules_2026-10-21.tsv`. They are
**unverified external review inputs**. No proposal in either has been merged into
a canonical ledger or an executable file, and the 31 candidates remain the
external author's claims, not repository findings. Corrections are recorded here
and in the delta TSV, leaving the originals intact.

The review inspected the public GitHub state at `9b9bf5b`-era `main`, commit
`9bc91a7`. This pass reads the local working tree at `495e48c`, which carries
eleven further commits of adjudication the review could not see. Where the two
disagree on repository state, **the local tree is authoritative and the review is
corrected.**

## 2. Reconciliation outcome

All 31 candidates were classified. **None is promoted to an executable rule, a
node, an edge, a rate or a sign.**

| classification | n | ranks |
|---|---|---|
| already covered | 6 | 4, 8, 14, 24, 27, 30 |
| supported addition (candidate only) | 4 | 16, 19, 21, 28 |
| contradictory | 3 | 2, 6, 26 |
| insufficient evidence | 8 | 3, 5, 9, 10, 12, 15, 20, 29 |
| deferred | 10 | 1, 7, 11, 13, 17, 18, 22, 23, 25, 31 |

### 2.1 Corrections to the external review

Five are material enough to state outside the table.

1. **Three candidates called unregistered are registered.** Ranks 10 (NDRG2), 11
   (ENTPD3) and 22 (gland secretome) are `PDF-011`, `PDF-015` and `PDF-034` in
   `context/literature/pdf_manifest.tsv`. The review tested membership of
   `references.tsv` only and reported the result as repository-wide absence.
   Rank 15 (Yap 2011) is in `active_evidence_manifest.tsv`, confirming the
   review's own hedge.
2. **Three of the four requested full texts are already local and already
   adjudicated.** Yang/NNMT, Yu/SETD7 and Izmaylova/DSG2 arrived on 2026-10-22
   and are adjudicated at figure level in plan §§4.13–4.15. **Only Zhou 2026
   DNM2 (rank 3) remains outstanding.** Two further candidates are also absent
   locally and abstract-only: rank 26 (PANX1) and rank 29 (anandamide).
3. **Rank 2 is contradicted, not a candidate.** The review proposes
   `ADD_TRAFFICKING_CANDIDATE` for RAB11A. Plan §4.2 had already read the same
   paper and found RAB11A does not differ between pre-receptive and receptive
   phase, that its E-cadherin effect is lateral rather than apical, and that
   knockdown cells lose transepithelial resistance and claudin-1, so the
   attachment deficit is not isolated.
4. **Rank 6 is a committed-rule divergence, not new literature.** The
   repository's own `context/literature/candidate-nodes.tsv` already records
   `E_CDH1_APICAL` with the logic hint the review proposes, at confidence 7. The
   committed `network.bnd` never implemented it.
5. **Rank 31 is higher-stakes than 6/10.** Plan §4.13 already identifies the
   Baek 2018 versus Lin 2026 pair as a system-matched contradiction governing the
   sign of everything upstream of the staged `S_FOXO1` node.

### 2.2 What the review got right, and should be credited for

The de-aliasing programme in its §A and §D is the same seam the repository
reached independently, and two of its judgements survive scrutiny unchanged:
rank 26's refusal to assign PANX1 a Boolean sign, and rank 16's ranking of HBP1
as the top stromal candidate. Rank 16 is **the only candidate in the whole set
that targets the seven-member hormone alias class**, which is the largest
structural defect the model has.

---

## 3. SETD7: three papers, now all read at figure level

Plan §4.13 assigned no sign and recorded that two of the three papers had been
read as abstracts only. **Both are now local full texts and both have been read.**
This section supersedes §4.13's evidence basis. **The verdict does not change —
no sign is assigned — but the reasons change, and one of them is new and
model-relevant.**

### 3.1 The three experiments

| | Yu 2026 | Chen 2026 | Konyushatova 2025 |
|---|---|---|---|
| DOI | `10.1007/s10815-025-03771-4` | `10.1093/biolre/ioag005` | `10.1093/molehr/gaaf028` |
| direction of perturbation | **gain** only | **loss** only | **loss** only |
| tool | graded overexpression | adenoviral shRNA (MOI 50, >50 %) **and** PFI-2, a catalytic inhibitor | CRISPR/Cas9 knockout |
| second independent tool | none | **yes** — PFI-2 does not change SETD7 protein, so it isolates catalytic activity | none |
| rescue | none | **yes** — wild-type HOXA10 rescues, methylation-dead HOXA10<sup>K392R</sup> does not | none (MG132 restores ER-α, which is a mechanism control) |
| claimed mechanism | FOXO1 phosphorylation; **no substrate relationship shown** | HOXA10 **methylated** at K392 | ER-α stabilised; substrate inferred from prior work |
| SETD7 localisation | not measured | **nuclear**, bright foci, colocalised with HOXA10 (Fig 5H) | **cytoplasmic at every timepoint; never nuclear** (Fig 2A, 2B) |
| patient direction | SETD7 **up** in RIF (Fig 2A–C) | SETD7 **down** in RIF, 3 GEO sets + 7/13 own cohort (Fig 8, S6) | SETD7 **down** in RPL, 2 microarray sets (Fig 4B, 4C) |

**On evidence quality the ordering is not close.** Chen carries two independent
loss-of-function modalities, a mapped methylation site, a structure-function
rescue with a point mutant, and a patient cohort. Konyushatova carries a clean
genetic knockout and a proteasome-inhibitor mechanism control. Yu carries one
gain-of-function modality, no rescue, no localisation measurement, and — as plan
§4.13 established and this reading confirms — **no methylation experiment of any
kind**, despite proposing a methyltransferase mechanism.

### 3.2 The conflict is not one conflict. It is three, and they are not the same shape

**(a) Net sign for decidualization: two against one, and the minority report is
the weakest paper.** Chen and Konyushatova both find SETD7 required. Yu finds
excess SETD7 deleterious. These are *not* formally contradictory: a factor can be
required at endogenous level and harmful when forced far above it. **No paper
measures achieved dose against endogenous level**, so the non-monotonic
reconciliation plan §4.13 left open remains open, and is now the most economical
reading of the whole set.

**(b) Substrate and compartment: the two "agreeing" papers disagree with each
other.** This is new, and plan §4.13 could not have seen it. Chen's entire
mechanism is nuclear — H3K4me1 redistribution by CUT&Tag, HOXA10 methylation,
nuclear colocalisation. Konyushatova reports SETD7 is **cytoplasmic at every
timepoint tested and undetectable in the nucleus**, and concludes explicitly that
the effect is *unlikely to be mediated through methylation of H3 assembled in
nucleosome*. Both cannot be describing the same protein in the same cell type.
**So the plan's characterisation of "two independent loss-of-function studies"
converging must be qualified: they converge on direction and diverge on
mechanism, compartment and substrate.**

**(c) A partial convergence, stated at the evidence level each paper actually
reaches.** All three report a transcription factor's **protein** moving with its
**mRNA unchanged**. They do **not** all demonstrate stabilisation, and an earlier
revision of this subsection wrongly called all three a convergence on
post-translational stabilisation and called FOXO1 a SETD7 substrate.

| paper | protein / mRNA observation | turnover or binding evidence | what it supports |
|---|---|---|---|
| Chen Figs 5B–5C, 6A–6D | HOXA10 protein falls on knockdown, mRNA unchanged | **yes** — cycloheximide chase, methyl-lysine co-IP, K392R mutant | stabilisation by direct methylation |
| Konyushatova Figs 1E, 2C–2E | ER-α nearly undetectable in knockout, `ESR1` comparable | **partial** — MG132 restores it, implicating proteasomal turnover; no binding or methylation assay here | stabilisation, substrate inferred from prior breast-cancer work |
| Yu Supp Fig 2A | FOXO1 protein rises on overexpression, mRNA unchanged | **none** — no chase, no co-IP, no methylation assay | **protein accumulation only** |

**So the shared observation is protein/mRNA discordance, which is weaker than a
shared mechanism.** Chen demonstrates stabilisation. Konyushatova supports it with
a proteasome control. **Yu demonstrates neither, and FOXO1 is not shown to be a
SETD7 substrate anywhere**; Yu's own account is AKT-dependent phosphorylation and
protein accumulation, not stabilisation by SETD7. That matters for the sign,
because Yu's consequence is backwards on its face: FOXO1 is required for human
decidualization (`REF-079`), so more FOXO1 protein should help. Yu resolves this
by invoking inactivating phosphorylation, which brings us to the drug.

### 3.3 AZD8055: worse than the task flagged, and Yu's own figure shows why

The task noted AZD8055 is an mTORC1/mTORC2 inhibitor rather than a FOXO1-specific
one. Plan §4.13 recorded that. Reading the figures adds a sharper point.

Yu's Figs 4F–4H apply AZD8055 to **primary RIF stromal cells with no SETD7
overexpression at all**, and report reduced senescence and restored PRL and
IGFBP1. So the drug's benefit is **not contingent on the SETD7 manipulation**.
That is exactly what mTORC2 inhibition is independently expected to do here: the
corpus already contains Baek 2018, in which rictor knockdown *enhances* prolactin
in these cells. **The arm that is presented as evidence for a SETD7–FOXO1 axis is
reproduced by the drug acting on its own documented target, in the absence of any
SETD7 perturbation.** It cannot discriminate the axis.

Two further points stand. The drug's documented action at that residue is to
**relieve** AKT-mediated nuclear exclusion, i.e. to activate FOXO1 — the opposite
sign to the one the paper applies. And **FOXO1 localisation is never measured in
any arm**, so the one claim the whole mechanism rests on is untested.

The standing methodological row plan §6.0a adds to U1 is confirmed and
strengthened: **AZD8055 is never a FOXO1-specific intervention in this project,
and in this paper it is not even a SETD7-contingent one.**

### 3.4 The single-cell contradiction, verified and partly dissolved

Plan §4.13 recorded that the same public resource is read oppositely. Confirmed
at panel level: Yu Fig 3A/3B assigns SETD7 **high** to the senescent cluster
(DIO2-high / SCARA5-low); Konyushatova Fig 3A reports SETD7 peaking on **day 2**,
with the mature and senescent subpopulations emerging only on days 6 and 8, and
Fig 3B/3C shows knockout **lowering** mature markers (SCARA5, IL1R1, PROK1) while
**raising** senescent markers (CLU, DIO2) and SA-β-Gal.

*Provenance note:* Yu cites the accession as `GSE127718`; Konyushatova cites
`GSE127918` (Lucas 2020). These differ by one digit and the second is the
Lucas dataset. Yu's is most likely a typographical error, and this document does
not treat the two as different resources on that basis alone.

**These two readings are less contradictory than they look, and the difference
matters for the model.** Yu's is a cross-sectional association in a terminal
state. Konyushatova's is a temporal and causal claim about an earlier step. A
gene can be expressed in senescent cells *and* be required beforehand to prevent
that fate. **What is genuinely irreconcilable is the patient direction** — SETD7
up in RIF (Yu) against down in RIF (Chen) and down in RPL (Konyushatova) — and
that is a measurement of the same molecule in the same tissue at the same phase.
RIF and RPL are different conditions, so Yu and Chen are the direct clash; they
sample different centres with different RIF definitions (≥4 transfers in Chen and
Yu both, but different exclusion criteria and cohorts).

### 3.5 The finding that changes something: a PRL/IGFBP1 dissociation

**Konyushatova Fig 1F is the most model-relevant panel in the three papers, and
neither the task brief nor the external review identifies it.**

Under the standard cocktail — cAMP + MPA + E2 — SETD7 knockout gives:

- **PRL significantly lower** than control;
- **IGFBP1 markedly *higher*** than control.

One genetic perturbation, the two core decidual markers, **opposite directions**.

Fig 1G then removes cAMP from the cocktail, and both markers fall together in the
knockout. **So the dissociation is conditional on cAMP.**

Three caveats travel with it and must travel into any register row. The authors
themselves attribute the elevated IGFBP1 to **stress overload** rather than to
decidualization, citing IGFBP1's role as a stress signal; on their reading the
high IGFBP1 is not a decidual readout at all. The design is RT-qPCR at n = 3 with
two-way ANOVA reporting the interaction term. And the cells are primary EnSC
carrying a CRISPR construct, so a clonal or construct effect is not excluded by
anything in the paper.

**Why this matters, stated against the separators the repository already holds
rather than against an empty field.** An earlier revision of this subsection
called Konyushatova the second separator and claimed the existing ones move only
one marker while the other stays null. **Both claims are wrong and are
withdrawn.** The corpus already records at least four, two of them in a canonical
register this document failed to consult:

| record | perturbation | pattern |
|---|---|---|
| `PIF-003` (Buzzio 2006) | FOXO1A siRNA | IGFBP1 **down**, PRL **up** — opposite directions, already on file |
| `PIF-004` (Ujvari 2017) | AS1842856, a FOXO1 activity inhibitor | IGFBP1 collapses, PRL unchanged; the register calls it *"the cleanest de-aliasing signal in the corpus"* |
| Kane 2010 Fig 4 | SMAD4 siRNA | PRL reversed, IGFBP-1 unaffected |
| Cloke 2008 Fig 1A | DHT | PRL up, IGFBP-1 not |

`PIF-003` already documents the **same opposite-direction pattern** I presented as
novel. So Konyushatova is not the second separator, it does not introduce the
pattern, and no ordinal claim is made here.

**What is actually new in it, narrowly.** Two things, neither of which is the
dissociation itself. The perturbation is a **CRISPR knockout** rather than an
siRNA, which matters because `PIF-003`'s own register entry records that its
siRNA co-targets FOXO3A and therefore cannot carry a sign alone. And the
dissociation is **conditional on cAMP** — present under the standard cocktail,
absent when cAMP is withdrawn — which is a dependence on an input the model
carries as `IN_cAMP`. That conditionality is the part worth registering.

*A pre-existing discrepancy this surfaces, recorded rather than silently
resolved.* Plan §4.12 states that Kane 2010 is **the only** separator in the
corpus; §4.7 names Cloke 2008 as *"a second separator"*; and the PIF register
holds two more. Those statements cannot all be right. Reconciling them against
the full separator inventory is a U2 task on the TI-04 row, not a finding of this
delta.

---

## 4. Structural implications

Re-derived this session from the repository's own loader, not inherited:

```sh
PYTHONPATH=src pixi run python -B -c "
from dt_adoc.reporting.structure import load_structure
s = load_structure('adoc-literature-superset-v0.6.0')
print(len(s.node_ids), len(s.free), s.enumerated_states, len(s.phenotype_inert))
print(s.alias_classes)"
```

56 nodes, 16 free variables, 65,536 states, 17 phenotype-inert nodes, and the
seven alias classes of plan §3.1 reproduce exactly. The stromal class is
`{OUT_STROMAL_DECIDUALIZED, S_DECIDUALIZED, S_IGFBP1, S_PRL, S_SPP1, S_TAZ_ECM}`.

### 4.1 Which candidates could break a Boolean equivalence

Four of the 31 **could break an existing Boolean equivalence**, and they attack
three different seams. Others would **join or enlarge** an alias class rather
than cut one — ranks 4, 18, 20 and 27 are the clearest, and the TSV's
`structural_consequence_if_added` column says which. Joining a class is a
structural consequence too, so this table is the candidates that could break an
equivalence, not the candidates that bear on one:

| candidate | seam | class attacked | size |
|---|---|---|---|
| rank 16 HBP1 (with rank 17 SOX4) | PGR **protein** versus PGR **transcriptional activity** | hormone cascade | **7** |
| rank 19 EPAC/RAP1 | `S_PKA` versus `IN_cAMP` | cAMP | 2 |
| rank 21 nuclear actin (= R6) | decidual **state** versus its **markers** | stromal decidual | 6 |
| rank 28 SETD7 / Konyushatova | `S_PRL` versus `S_IGFBP1` | stromal decidual | 6 |

**Rank 16 is the highest-value structural candidate in the external set**, because
the seven-member hormone class is the largest in the model and nothing else in
the 31 touches it. That ranking agrees with the review's own, reached
independently.

**It is a ranking by structural target, not by evidence, and the two must not be
confused.** Ranks 16, 17 and 19 are all `registers_only_not_read_this_pass`: no
panel from Guo 2026, Huang 2022 or Kusama 2013 has been read in this repository.
Rank 21 is the only row in this table that is figure-verified here. So the table
says which seams *would* be cut if the sources hold, and says nothing about
whether they hold.

### 4.2 The PRL/IGFBP1 split is an observation-layer repair, not a topology repair

This is the sharpest structural result of the pass and it cuts against treating
the Konyushatova finding as a topology win.

`S_PRL` and `S_IGFBP1` appear in `network.bnd` **only as node definitions**
(lines 161 and 165). No rule reads either. They are pure leaves — `OUT_STROMAL_DECIDUALIZED`
was reduced to `S_DECIDUALIZED` when TI-01 was discharged. Verify with:

```sh
grep -n 'S_PRL\|S_IGFBP1' models/superset/adoc-literature-superset-v0.6.0/network.bnd
```

**Consequence: giving the two markers different rules changes no `OUT_` node in
any of the 65,536 states.** It is not a route repair and it buys no
discriminability between adhesion mechanisms. What it changes is what the model
**predicts for a measurement** — and `S_IGFBP1` is the ADOC stromal observable.

That makes it consequential in a different way, and the direction is
uncomfortable. The model asserts IGFBP1 rises with the decidual state. Konyushatova
shows a perturbation that **impairs** decidualization while **raising** IGFBP1,
under a cocktail containing cAMP. If that generalises, then IGFBP-1 read alone is
not a monotone reporter of the stromal state, and **calibrating against it could
move the model the wrong way.** Plan §10.3 ranks `dropout_e2` first partly
because it separates the two measured nodes; this adds a caveat to how the
resulting IGFBP-1 trace may be interpreted, without changing the ranking.

### 4.3 The witness is not currently measurable, and the gap is already registered

Reading `config/observation_model_map.tsv` at row level rather than by summary:

| row | protein | model node | activation | role |
|---|---|---|---|---|
| OM-001 | PAEP | `E_PAEP` | `active_constraint` | calibration_constraint |
| OM-002 | IGFBP-1 (bottom) | `S_IGFBP1` | `active_diagnostic` | diagnostic |
| OM-006, OM-014 | PRL (bottom) | `S_PRL` | `provisional` | context_only |
| **OM-011, OM-016** | **IGFBP-1 *and* PRL jointly** | `S_IGFBP1;S_PRL` | **`rejected`** | **`gap`** |

**The joint PRL-and-IGFBP1 mapping — exactly the observable a dissociation
witness requires — is already registered as a rejected gap**, OM-011 citing
unresolved temporal alignment of the protocol arms. So the new evidence lands
precisely on a measurement limitation the repository had already identified and
recorded. That is a good outcome for the register and a blocking one for the
science: **TI-04 stays deferred, and its blocker is unchanged.**

A refinement worth registering, though. Plan §4.7 blocks TI-04 because the
separating axes — TGFβ1/SMAD4 and AR/DHT — are not in the model's alphabet.
SETD7 is not in the alphabet either. But the **conditioning variable is**: the
dissociation appears with cAMP and disappears without it, and `IN_cAMP` is a
declared input. The separator remains outside the alphabet; the modifier is
inside it. That is a two-factor interaction, not a new edge, and it is not
sufficient to unblock TI-04.

---

## 5. Impact on the implementation plan

**U1, U2 and U3 keep their scope, their order and their verdicts.** No candidate
becomes GO, no executable artifact is proposed, and the 2026-09-30 pause is
untouched — all three of its resume triggers remain false, unchanged from plan
§7.1.

Four amendments, each additive:

1. **§4.13 is superseded in its evidence basis, not its verdict.** Chen and
   Konyushatova were read as abstracts there and are read at figure level here.
   N5 remains **no sign assigned**. The three new reasons are §3.2(b), §3.3 and
   §3.5 above.
2. **U1 gains seven mutations: seven appended article rows, and no field
   correction.** Not thirty-one, not eleven, and not ten. U1's contract
   requires one digest, one DOI and **the panel actually read, per article**, so
   the unit of counting is the article, not the delta row. Two deductions follow,
   and an earlier revision of this item got both wrong.

   **Deduction 1: a row is not an article.** Rank 28 is a composite row covering
   **three** papers — Yu 2026, Chen 2026 and Konyushatova 2025 — so the eleven
   `figure_level_verified` rows span thirteen articles.

   **Deduction 2: most of them are already registered, so registering them again
   would duplicate.** Of the thirteen, six already carry a `REF-` or `PDF-`
   identifier and report no new experimental evidence: Dong 2025, Ma 2023,
   Ruan 2026, Paule 2012, Peng 2021 and Marwood 2009. Their adjudications live in
   plan §4 and U1 points at the plan for verdicts rather than restating them.

   **The resulting exact list, seven articles and seven mutations:**
   Kakar-Bhanot 2019, Tamura 2024, Yang 2026 (NNMT), Yu 2026, Chen 2026,
   Konyushatova 2025 and Izmaylova 2026 — each figure-read, each unregistered in
   both digest-bearing ledgers. **U1 appends seven rows and edits no existing
   row.**

   **All three of U1's canonical artifacts are accounted for, and only one is
   written.** An earlier revision of this item named two and left the third
   unmentioned, which is the mismatch gate finding B10 raised:

   | artifact | U1 decision | why |
   |---|---|---|
   | `context/literature/pdf_manifest.tsv` | **MODIFIED**, 7 appended rows | keyed per held PDF rendering, so it is the article-provenance ledger; all 17 fields populated, `ref_id` left empty |
   | `context/literature/active_evidence_manifest.tsv` | **UNCHANGED** | its verification column is scoped to the 2026-09-28 audit, and `model_nodes_or_rules_supported` would be empty for all seven |
   | `context/evidence-register.tsv` | **UNCHANGED** | claim-level, not article-level: its `LIT-` rows assert `planned_use = construction`, which none of the seven licenses |

   The per-field enumeration, the expected old and new state of every row, and
   the validation for each are in
   `docs/v05_u1_mutation_contract_2026-10-22.tsv`, checked by
   `python3 -I scripts/check_u1_mutation_contract.py`. Plan §6/U1 carries the
   same table and the reconciled totals: 24 original plus 7 delta equals 31
   appended rows. **The `PDF-048` row correction is withdrawn** — simulation
   against the canonical tests showed the rewrite breaks a pin that is
   load-bearing for the audit trail, so the digest mismatch stays documented and
   unrepaired. See plan §6/U1.

   **The seven appends carry `registration_decision = recorded_not_registered`
   with an empty `ref_id`**, not `registered`: recording an obtained PDF is not
   registering a source in the bibliography, and the canonical registry-agreement
   test forbids the pairing this delta originally proposed.

   **U1 is not execution-ready.** Only 7 of its 31 appends are individually
   specified, 29 of the 31 reconciliation rows carry no DOI, and the 31
   renderings are 30 distinct articles.

   **The repository-level checks run without the gitignored corpus; the
   source-digest check does not and is not expected to.** Running the validator
   with no argument is the clean-checkout level and passes there; `--verify-sources`
   hashes the PDFs and is a mandatory precondition for executing U1, satisfied
   only in a tree that holds the corpus.

   **Deduction 3, and an earlier revision of this item got it wrong: the three
   manifest-identifier items are not U1 mutations.** `PDF-011`, `PDF-015` and
   `PDF-034` are **already present and correct** in `pdf_manifest.tsv`; verify
   with `cut -f1 context/literature/pdf_manifest.tsv | grep -cx PDF-011` and the
   other two, each returning 1. There is nothing in a ledger to correct. They are
   corrections to the **external review document**, which reported those papers
   as unregistered, and they live in §2.1 of this document. Counting them as
   future ledger edits would have had U1 perform three spurious mutations.
   Rank 15's membership of `active_evidence_manifest.tsv` is likewise a
   **confirmation, not a correction**.

   **What happens to everything else, stated so it is not read as a ledger
   claim.** The six already-registered figure-verified articles **receive no new
   entry**; they are in a canonical ledger already and U1 leaves them untouched.
   Separately, the seventeen `registers_only_not_read_this_pass` rows and the
   three `abstract_only_absent_locally` rows are the ones genuinely outside both
   digest-bearing ledgers, and they stay outside them as explicitly unverified
   candidates; U2 carries the ones that need a deferred row. An earlier revision
   conflated these two groups into a single claim that the remainder sits outside
   every canonical ledger, which was false for the six.
3. **U2 gains exactly one new mutation, plus two field revisions.** The new
   mutation is a candidate row **N8**, the PGR-protein-versus-PGR-activity seam,
   carrying rank 17 (SOX4) as its companion and an unblock condition of
   figure-level adjudication of both sources. The two field revisions are to
   mutations U2 already performs: TI-04's row records the Konyushatova
   dissociation as **an additional and differently-shaped separator**, reconciles
   the §4.7-versus-§4.12 discrepancy on how many separators the corpus holds
   (§3.5 above), and records that the joint observation
   mapping is a registered gap, and N5's row records the three-way figure-level
   basis. U2's stated total therefore moves from fourteen mutations to
   **fifteen**, and plan §6/U2 carries the count, the row list and a test that
   enforces both.
4. **U3's candidate list gains rank 16 conditionally**, not outright. It is the
   only external candidate that targets the seven-member hormone class, which is
   why it is worth the slot. But **neither Guo 2026 nor Huang 2022 has been read
   at figure level**, so its structural promise rests on the external review's
   reading rather than on this repository's. The condition is therefore explicit:
   **figure-level adjudication of both sources first, and U3 scores it only if
   that adjudication holds.** Ranking a candidate by its structural target before
   its evidence is verified is the error §5.1 of the plan warns against, and this
   item is written so it cannot be read as the verdict of an adjudication that
   has not happened.

**No change to the near-term priority order.** The binding constraints are
unchanged: the pause, the vacuous adhesive disjunction, and the fact that both
actively-mapped nodes are phenotype-inert.

---

## 6. Provenance

**Files added by this pass:**

| path | what it is |
|---|---|
| `docs/v05_external_review_delta_2026-10-22.md` | this document |
| `docs/v05_external_review_delta_2026-10-22.tsv` | the 31-row reconciliation |

**Files modified by this pass:**

| path | what changed |
|---|---|
| `docs/v05_literature_guided_implementation_plan_DRAFT.md` | §4.12 separator correction; §4.13 supersession note; §5.2 gains N8; U2's scope, row list, TI-04 deliverable and test; new §6.0b |
| `docs/v05_literature_corpus_reconciliation_2026-10-21.tsv` | **one column added**, `source_doi`, populated for two rows. Those two rows — Chen 2026 and Konyushatova 2025, carrying path and SHA-256 — were themselves added earlier in this same pass and **already existed when the `source_doi` column was added**, so that later edit gave DOI values to pre-existing rows rather than creating them. Against the session baseline the net change is both: 163 data rows and 15 columns become 165 and 16 |
| `docs/v05_traceability_identifiability_matrix_2026-10-21.tsv` | the `N5-SETD7` row rewritten: its full-text obligation is discharged and six fields are re-stated at figure level |

**On the new `source_doi` column.** The reconciliation's only DOI field was
`manifest_doi`, which is populated in all 64 rows that are in
`pdf_manifest.tsv` and in none of the 101 rows that are not, so it means *the
DOI the manifest records* and cannot carry a DOI for an unregistered paper
without meaning two things at once. `source_doi` is therefore additive, and is
populated only for the two rows this pass established, leaving the other 163
empty. Reproduce with

```sh
awk -F'\t' 'NR>1 && $6!=""{print $6"\t"$2}' \
  docs/v05_literature_corpus_reconciliation_2026-10-21.tsv
```

**Files preserved unchanged:** the two supplied review artifacts under
`context/literature/reviews/`, byte-identical to what was supplied.

**Not touched:** `network.bnd`, any condition config, protocol, calibration,
observation map, phenotype definition, intervention library, or any canonical
evidence ledger — `references.tsv`, `pdf_manifest.tsv`,
`active_evidence_manifest.tsv`, `candidate-nodes.tsv`, `candidate-edges.tsv`,
`mechanisms.tsv` and `docs/deferred_topology_register.tsv` are all unmodified.
Nothing under `data/`. No model version, no simulation run, no seeds spent. The
`dropout_e2` pause is not lifted. No PDF or publisher supplement is committed.

**Corpus state:** 164 PDFs locally, two more than the 162 recorded at `495e48c`
— Chen 2026 and Konyushatova 2025, both read this pass. The corpus is gitignored,
so this count is reproducible only in a working tree that holds it.

**Remaining uncertainties, stated rather than resolved:**

- Three candidates are abstract-only and absent locally: ranks 3 (DNM2), 26
  (PANX1), 29 (anandamide). Rank 3 is the only one whose absence blocks a
  decision.
- The SETD7 sign is **unresolved**, and this pass deliberately leaves it so. The
  non-monotonic reading is the most economical but is not demonstrated, because
  no paper measures achieved dose against endogenous level.
- The Chen-versus-Konyushatova localisation contradiction (nuclear versus
  cytoplasmic) is **unexplained**. It is recorded, not reconciled.
- **Twenty of the 31 candidates are not figure-verified**, and this is the
  largest limitation of the pass. Seventeen are
  `registers_only_not_read_this_pass` and three are
  `abstract_only_absent_locally`; eleven are `figure_level_verified`. The TSV's
  `verification_depth_this_pass` column carries one of those three tokens in
  every row, so the split is reproducible rather than asserted:

  ```sh
  awk -F'\t' 'NR>1{split($7,a,";"); print a[1]}' \
    docs/v05_external_review_delta_2026-10-22.tsv | sort | uniq -c
  ```
- The Baek 2018 versus Lin 2026 contradiction on mTORC2/RICTOR→FOXO1 remains the
  named prerequisite for the staged `S_FOXO1` node and is **not** adjudicated
  here.

**Claim boundaries.** Nothing here is clinical. Every relationship discussed is a
candidate. No perturbation discussed is causal biological evidence for a patient.
No transition rate, no physical time and no calibration is proposed:
`duration_units` remains `relative_only`.
