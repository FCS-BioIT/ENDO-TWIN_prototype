# Curation increment 6 — Somkuti 1997 and Jin 2025 full texts

Date: 2026-07-29. Claim level: `full-text triage, bibliography registration and claim-level
adjudication`. **No executable model file was modified. `network.bnd` is untouched, no rule
changed, no rate or initial condition changed, and `edge_evidence_assertions.tsv` stays at 274
byte-identical rows.**

Two papers that previous increments recorded as missing arrived as full text. Somkuti was
never in the corpus in any form. Jin was `ADH-SEED-125`, abstract-only, and was the **first
entry** under "Blocking now" in `docs/paywalled_papers_needed.md`.

> **Revised 2026-07-29 after an independent verification pass.** Every consequential claim below
> was re-checked against the PDFs at 400–500 dpi, against the repository schemas, and against the
> executing network. Four things in the first draft did not survive and are corrected in place:
> the Somkuti steroid result **corroborates** exemption `PAR-002` rather than conflicting with the
> model; the β3-versus-αvβ3 objection is **narrower** than stated, because `E_ITGAVB3_5`'s declared
> measurement proxy is already a disjunction including ITGB3 alone; the **provisional A–E grades
> were invented** and have been removed in favour of the repository's real scales; and the
> per-relation registry `config/edge_citation_adjudications.tsv` — which the first pass did not
> consult at all — is the correct home for such decisions and was found to warrant none. The
> structural argument now rests on the repository's own 262,144-state analysis instead of an
> analysis written for this increment.

Four tiers are kept separate throughout, because they have different truth conditions:

| tier | what it means | outcome here |
|---|---|---|
| **bibliography registration** | the model is *entitled* to cite the paper; its identity is verified | **2 registered**, REF-058 and REF-059 |
| **verified expression claim** | an abundance/localisation fact, explicitly not node activity or causal influence | **20 recorded** (5 Somkuti + 15 Jin) |
| **candidate signalling relation** | a directed relation worth cataloguing, with its blocker named | **9 catalogued**, 1 demoted to unsupported |
| **executable-model promotion** | licensed to change `network.bnd` | **0. Empty, and the reason is structural** |

Registration is not verification. Claim-level biological support across the model remains
**0**, unchanged by this increment.

## Registered: 2, REF-058 and REF-059

Both are versions of record, confirmed from the rendered first page rather than from metadata:
Somkuti carries `0021-972X/97/$03.00/0`, `Copyright © 1997 by The Endocrine Society`,
`Vol. 82, No. 7` and the abstract closer `(J Clin Endocrinol Metab 82: 2192–2197, 1997)`; Jin
carries the running header `Molecular and Cellular Endocrinology 606 (2025) 112581`, a printed
DOI, `Accepted 19 May 2025` and an assigned article number. Neither is an accepted-unedited
manuscript, so the `{Mo et al., Huang et al.}` deferred set is unchanged. No retraction,
correction, erratum or expression of concern on either — `efetch` returns no
`CommentsCorrectionsList` for either PMID and all Crossref records return an empty `relation`.

Ids allocated by strict append-only sequence: `PDF-027`, `PDF-028`, `REF-058`, `REF-059`. Since
`5f8d7b4` a REF id is a content address (`ASRT-<edge>-<REF-id>`), so this is load-bearing
rather than cosmetic.

### Deduplication was proven, not asserted

Zero DOI, PMID and sha256 collisions against all 57 prior references and all 26 prior manifest
rows. Highest title similarity is **0.495** (Somkuti vs REF-004 Craciunas 2019) and **0.429**
(Jin vs REF-045 Licht 2007), both from generic phrasing and both far below the repository's own
`TITLE_SIMILARITY_FLOOR = 0.65`.

The Lessey trap was checked explicitly, because **Bruce A. Lessey is the fourth author on
Somkuti** and is already a co-author on REF-006, REF-007, REF-042 (Lessey 2002, HB-EGF) and
REF-043 (Lessey 1996, integrins). Three distinct papers on four non-overlapping identifiers:
DOI prefixes `10.1210` / `10.1002` / `10.1111`, PMIDs 9215293 / 12112577 / 8962647, three
journals, three years. Lessey co-authorship therefore carries no deduplication signal in this
corpus. Somkuti appeared nowhere in the repository beforehand — zero grep hits for the author,
either DOI form, or the PMID.

### Somkuti has two registered DOIs; one is an alias and must never be used

Crossref returns **two** records for this article with identical volume and pages:

| DOI | status |
|---|---|
| `10.1210/jcem.82.7.4102` | **canonical — use this** |
| `10.1210/jc.82.7.2192` | duplicate registration, resolving alias, must not enter the manifest or registry |

Decided on four convergent signals, the first decisive: **the alias resolves to the canonical
one** — `https://doi.org/10.1210/jc.82.7.2192` returns 302 to
`press.endocrine.org/doi/10.1210/jcem.82.7.4102`. PubMed 9215293 carries
`10.1210/jcem.82.7.4102` as its *only* DOI in both `esummary.articleids` and `efetch`. The
`jcem` record has all four authors with full given names against the alias's single
`Somkuti, S. G.`, and two ISSNs against one. The alias's own `link[0]` points at the `jcem`
DOI with `content-version: "vor"`.

This matters mechanically: `test_pdf_manifest.py::test_registration_decision_agrees_with_the_registry_both_ways`
joins manifest to registry **on DOI**, so the wrong pick is a silent contract failure, and a
later increment picking the alias would mint a second REF id for a paper already registered.
Recorded here so that cannot happen.

Not resolved: Crossref does not itself flag either record as a duplicate — both return an empty
`relation` with no cross-link — and the OUP landing page returns 403, so the canonical record's
self-reported DOI could not be read. The conclusion rests on convergent evidence, not on a
publisher declaration.

## Tier 2 — verified expression claims

Abundance, secretion and localisation facts only. Under the AGENTS.md invariant these are
**not** node activity, interaction strength, transition rate or causal influence, and none is
promoted below.

**Somkuti (Ishikawa; surface β3 by SSA6 flow cytometry unless stated).** EGF 1 ng/mL, TGFα
5 ng/mL and bFGF 10 ng/mL each raise surface β3 to **2.60× / 2.20× / 2.15×** of control at 6 d,
while nine other factors do not (1.02–1.15×) · the EGF threshold sits between 0.1 (1.21×) and
0.5 (1.96×) ng/mL, plateauing to 2.76× at 100 ng/mL · E2 10⁻⁸ M and E2+P4 10⁻⁸/10⁻⁶ M for 6 d
**lower** surface β3 (Fig. 2 panel ≈ −52% and ≈ −70%; Fig. 6 gives E+P as ≈ −61%) · EGF
10 ng/mL raises ITGB3 mRNA at every timepoint 2 h–8 d, and both steroid arms lower it, ordinally
only · β3-immunoreactive material sits at pericellular borders and cell–cell contacts (Fig. 1B),
i.e. a **lateral** pool.

**Jin (protein by western unless stated).** hCG 5 µg/mL 1 h raises epithelial p-cPLA2, COX-1,
COX-2 and AKR1C3, with CBR1/AKR1B1/AKR1C1 unchanged · hCG raises epithelial PGF2α, intracellular
36.5→55 and medium **102→142 pg/mL** · PGF2α 1 nM raises AKR1C3 in both Ishikawa and CRL-4003 ·
PGF2α 1 nM raises whole-cell p-cPLA2, AREG, EREG, HB-EGF, PTGFR and the pro-ADAM17 band ≈1.5× ·
PGF2α 0.1–1 nM raises **supernatant** AREG 1.53×, EREG 4.3×, HB-EGF 6.0× · hCG 6 h raises
epithelial p-cPLA2, AREG, EREG and HB-EGF, with ADAM17 only at 5 µg/mL · under db-cAMP+MPA,
EREG and HB-EGF each raise stromal IGFBP1 mRNA and IGFBP1/PRL protein while **AREG does not** ·
coculture raises stromal cAMP 1.68→2.50 ng/mL *on top of* 250 µM db-cAMP · human luminal
epithelium peaks at **LH+2** for all four molecules, with **no stated n**.

## Tier 3 — candidate signalling relations

| relation | class | blocker |
|---|---|---|
| EGF/TGFα (EGFR agonists) → epithelial ITGB3 transcription and surface β3 | `catalog_only` | expression endpoint only; no receptor-level necessity; technical replication only |
| bFGF → epithelial surface β3 | `catalog_only` | different receptor family; single dose; no FGFR perturbation; no transcript arm |
| E2, and E2+P4, ⊣ epithelial ITGB3 | `catalog_only`, `direction_supported = contradicted` vs the encoded sign | PGR never measured; no P4-alone arm; no interaction test; needs an unmodelled receptor-downregulation step to reconcile with in vivo timing |
| EGF-family input **overrides** steroid suppression of ITGB3 | `catalog_only` | the only two-factor design in the paper, and it carries **no significance brackets** |
| `IN_HCG` → epithelial PGF2α synthesis and secretion | `catalog_only` | sufficiency only; receptor unidentified; no hCG specificity control; active only at 5 µg/mL |
| PGF2α/PTGFR → epithelial EREG and HB-EGF | `uncertain_rule_variant` (best-supported step) | one antagonist, no PTGFR knockdown, no antagonist-alone arm |
| **epithelial EREG/HB-EGF → stromal IGFBP1/PRL increment, conditional on a running db-cAMP+MPA program** | `catalog_only` | the ligand-**without**-DEC arm was never run; see below |
| PGF2α → stromal IGFBP1 **directly** | `catalog_only` | concentration disputed; AL-8810 at 50 µM; ~250× the PGF2α level hCG actually achieves |
| PGF2α → ADAM17 → ectodomain shedding | **`unsupported_candidate`** | never perturbed; no activity assay; no precursor-to-ectodomain size shift |
| AREG → stromal decidual markers | scoped **negative**, not a relation | no reagent-bioactivity control; single dose; unmatched duration |

## Tier 4 — executable-model promotion: empty, for a computed reason

Nothing from either paper is promoted, and the reason is structural rather than cautious. It
rests on the repository's **own** authoritative structural analysis of the active model
(`docs/assets/adoc_superset_structure_v0.3.0_metadata.json`, exhaustive over all **262,144**
assignments of the superset's 18 free variables) rather than on any analysis introduced by this
increment. Three of its recorded facts decide the matter:

| repository-recorded fact | consequence here |
|---|---|
| `E_ITGAVB3_5` is in a **9-member exact-alias class** with `E_HBEGF`, `E_SECRETORY_STATE`, `E_PAEP`, `E_SPP1_EXPR`, `E_PC6`, `E_MUC1_SLEX`, `E_DAG1_CLEAVED`, `E_ANXA2_ACTIN` | any Somkuti-derived growth-factor disjunct on the integrin node is absorbed |
| `S_IGFBP1` is in an exact-alias class with `S_DECIDUALIZED`, `S_PRL`, `S_SPP1`, `S_TAZ_ECM`, `OUT_STROMAL_DECIDUALIZED` | `S_IGFBP1` reduces to `S_DECIDUALIZED`, and by substitution to **`progestin and not mifepristone and cAMP`** — exactly the agents Jin holds ON in every stromal experiment |
| `E_HBEGF` and `IN_HCG` are both listed as **phenotype-inert**, and `IN_HCG` is one of 3 **unread inputs** | no hCG- or HB-EGF-routed encoding can move any phenotype output, whatever its evidence |

**That is why every faithful encoding of Jin is inert.** A Boolean readout already saturated at
1 under db-cAMP+MPA cannot represent a 1.6–3× potentiation of itself, so the relation Jin
actually demonstrates — a *magnitude increment above an already-running program* — has no
Boolean expression in this model. Encodings that *do* move states (`S_IGFBP1 = S_DECIDUALIZED
or E_EREG`) move them only where progestin or cAMP is absent, which is the one region Jin never
tested.

Somkuti is the mirror image, and here the repository had already done the work: **exemption
`PAR-002` records that dropping the `E_SECRETORY_STATE` disjunct from `E_ITGAVB3_5` was tested
and is "verified inert over all 262144 input assignments"**, because `E_HBEGF` is identically
`E_SECRETORY_STATE` and the integrin node reaches the outputs only through a gate that already
requires `E_LIF`. Somkuti changes none of that.

Jin's coculture relation remains **the most promotable candidate in the corpus**, because it is
neither a further disjunct of an absorbed epithelial OR-group nor absorbed by the stromal
alias class — it is a new epithelium→stroma coupling into a subgraph that currently has no
epithelial input at all (`S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2`). The single named
blocking experiment: **EREG and HB-EGF on stromal cells without db-cAMP and without MPA.** That
one arm decides whether any Boolean edge exists. Also required before wiring: the missing mediation

Jin's coculture relation is nevertheless **the most promotable thing in the corpus so far**,
because it is the only candidate that is neither a further disjunct of an absorbed epithelial
OR-group nor absorbed by the stromal collapse — it is a new epithelium→stroma coupling into a
currently epithelium-blind subgraph (`S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2` has no
epithelial input at all, and `IN_HCG` still has **no consumer**). The single named blocking
experiment: **EREG and HB-EGF on stromal cells without db-cAMP and without MPA.** That one arm
decides whether any Boolean edge exists. Also required before wiring: the missing mediation
joint (hCG on epithelium under PGF2α blockade), the siRNA-without-stimulus arm, a double
knockdown, a rescue, ligand measurement in the coculture medium, and a stage resolution for the
LH+2 problem below.

## Where the reviewed conclusions needed correcting

The conclusions put forward for review were largely right. Five needed qualification, and two
were wrong as stated.

1. **"E2+P4 suppresses more strongly than E2 alone" — true in the protein panel only.** Fig. 2
   reads ≈ −52% vs ≈ −70%, but it carries **no error bars, no n and no significance test of any
   kind**, and the paper's own second estimate of the same condition is −61% in Fig. 6 — so
   between-experiment drift is comparable to the E-vs-E+P gap. At mRNA level the ordering is
   **not reproduced**: the E2 lane is the more suppressed while the E2+P4 lane carries the
   heaviest GAPDH of the eight lanes. Treat the mRNA ordering as not determinable.
2. **"P4 alone reportedly has no effect" — this is not a null, it is an absent experiment.**
   Verbatim `"P alone had no effect (not shown)"`. No bar in Fig. 2, no lane in Fig. 4, no n, no
   statistic, no positive control for P4-responsiveness, no mifepristone arm. It is also
   *pre-explained*: the paper's own cited basis is that Ishikawa PGR is oestrogen-induced, so a
   null without E2 priming reflects low receptor, and PGR was never measured. Graded **E** and
   recorded as absence of evidence. The word "reportedly" in the original framing is carrying
   real weight and should not be dropped.
3. **"Somkuti supports EGF/TGFα/bFGF induction of ITGB3/αvβ3" — confirmed, but the species is
   narrower than "αvβ3".** Every detecting reagent is β3-directed (mAbs AP3 and SSA6, and a β3
   cDNA probe). **αv was never measured, β5 was never measured, and no heterodimer-specific
   antibody was used** — heterodimer specificity is asserted by citation. The model node
   `E_ITGAVB3_5` lumps αvβ3 with αvβ5; Somkuti speaks to neither, only to the β3 subunit. The
   transcriptional arm was run with **EGF only**.
4. **"Jin proposes hCG → epithelial PGF2α → EREG/HB-EGF → stromal decidualization support" —
   correct, but dropping ADAM17 from the chain hides the step that fails**, and the paper *also*
   demonstrates a **parallel epithelium-independent route** (PGF2α applied directly to stroma,
   Fig. 4M–P; §3.4 says PGF2α "also acted directly on stromal cells"). The epithelium is not
   shown to be obligate. Separately, **the load-bearing joint is missing**: no experiment applies
   hCG to epithelium under PGF2α blockade, so "through PGF2α" — the paper's own title claim — is
   an inference from two side-by-side sufficiency results.
5. **"Strongest evidence is epithelial EREG/HB-EGF siRNA in coculture" — confirmed, and the
   coculture is better designed than expected**: not conditioned medium and not a commercial
   transwell, but Ishikawa on a coverslip **transferred onto four pillars** above the stromal
   monolayer, so the compartments exchange soluble factors only and the epithelial pretreatment
   happens in a *separate well before transfer*, which largely excludes stimulus carryover. Two
   qualifications: in **all four** panels IGFBP1 returns to the DEC+ baseline and **not below**,
   so what is necessary is the *increment above the protocol*, not decidualization; and each
   single knockdown fully abolishes an increment that either ligand alone can produce, which is
   internally tense and is not resolved without a double knockdown or a rescue.
6. **"No LHCGR necessity experiment" — confirmed, and stronger than stated.** `LHCGR` occurs
   **zero** times; so do `LHR` and `luteinizing`. No expression measurement, no antagonist, no
   knockdown — **no receptor of any kind is identified** for the hCG stimulus. The
   `paywalled_papers_needed.md` conditional therefore resolves to **untested, not evidence of
   absence** — materially weaker footing than the bioRxiv/PMC pair listed under Tier 1 there
   would provide, and it does not upgrade the standing decision to decline the edge.
7. **"AREG did not promote the decidualization markers" — confirmed as a within-experiment
   observation, not as a general negative.** IGFBP1 mRNA 37→33 ns, IGFBP1 IF 3.70→3.35 ns, PRL
   IF 3.40→3.35 ns, at the same 50 ng/mL and 4 d as the positive EREG arm. But **AREG's
   bioactivity was never independently confirmed** — no receptor phosphorylation, no
   proliferation, no positive comparator in the same wells — and the three-ligand grid is
   unmatched (HB-EGF was 100 ng/mL for **1 d**). A negative with no reagent-activity control is
   weak evidence of biological absence. What it *does* show is sharp: Jin's own Fig. 3 has PGF2α
   **raising** AREG secretion, so within one paper an EGF-family ligand is secreted yet
   functionally inert — a direct in-paper illustration of the abundance-≠-influence invariant,
   and an argument against ever lumping "epithelial EGFR-ligand secretion" into one node.

## ADAM17: abundance, and not even of the active species

Handled separately because the requested distinction turns out to understate the gap. The
instruction was not to equate abundance with demonstrated enzymatic activation. Correct — and
**the abundance measured is of the wrong species to support the mechanism at all.**

Re-verified independently at 500 dpi for this review: the ADAM17 row of Fig. 3A is a **single band
at the in-panel 120 kDa marker**, one band per lane, with no second, smaller band resolved
anywhere. ADAM17 is synthesised as a full-length precursor and matures by pro-domain removal to a
markedly smaller catalytically competent species, so **a single ~120 kDa band is consistent with
the precursor and resolves no processed form at all** — the blot cannot distinguish a change in
total ADAM17 from a change in the active enzyme, which is the quantity the mechanism needs.

The same 500-dpi read corrects one detail from the first pass: Fig. 3A carries a proper **GAPDH
(37 kDa) loading control**. The Coomassie total-protein control applies only to the *supernatant*
blot in Fig. 3B, where no housekeeping protein is available.

Never measured: ADAM17 mRNA, phosphorylation, mature-vs-pro form, surface localisation, any
sheddase-activity assay. Never perturbed: **zero** occurrences of TAPI-0, TAPI-2, marimastat,
batimastat or GM6001, and the siRNA list contains only EREG and HB-EGF. The changes themselves
are the weakest in the paper: 0.52→0.76 with the largest SD in its panel, and 0.46→**0.44 (ns)**
→0.59, non-monotonic.

Corroborating, from the same rendered panels: the supernatant species in Fig. 3B run at **AREG
43, EREG 19, HB-EGF 23 kDa — identical to the whole-cell-lysate masses in Figs 3A and 3C**. If
ADAM17-mediated ectodomain shedding were the mechanism, the secreted species should be the
smaller shed ectodomain. **No size shift is demonstrated**, so "shedding" is imported from the
cited literature rather than measured, and a Coomassie total-protein control on serum-containing
medium cannot exclude lysis or vesicular release. The abstract's *"induces EREG and HB-EGF
secretion by activating ADAM17"* is unsupported by this paper's own data.

### "Unsupported by this paper" is not "unsupported globally" — and here nothing is being removed

An important distinction, deliberately kept separate from the finding above. Everything in this
section is a statement about **Jin's evidence**, not about ADAM17 biology, where ectodomain
shedding of EGF-family ligands is well established in the wider literature.

The question of whether a corpus-independent case exists was checked rather than assumed:
`ADAM17`, `EREG`, `PTGFR`, `AREG`, `PGF2` and `LHCGR` appear in **no** model artifact anywhere in
the repository — not in either `network.bnd`, not in `node_dictionary.tsv`, `complete_nodes.tsv`,
`complete_edges.tsv`, `edge_evidence.tsv`, `topology.tsv` or `rule_variants.tsv`. Their only
occurrences are in `references.tsv`, `pdf_manifest.tsv`, the seed table and curation docs.

Two consequences follow, and they should not be conflated:

1. **There is no ADAM17 node to remove, so nothing is removed or demoted by this increment.**
   The decision is only that Jin does not license *creating* one.
2. **No other reference in this corpus supplies ADAM17 evidence either**, so the absence is
   currently a coverage gap rather than a considered rejection. If a future increment wants an
   ADAM17 intermediate, the correct route is a paper that perturbs ADAM17 and reads out ligand
   shedding — not this one. Jin may legitimately be cited *alongside* such a paper for the
   PGF2α-responsiveness of ADAM17 abundance, which it does show.

## Data-integrity flags

### The PGF2α concentration discrepancy — recorded, not resolved

Located in **Fig. 4, panels M–P**: panels on p.8, caption on p.9.

- **In-panel labels**, read at 600 dpi and identical under all four panels M, N, O and P —
  invisible to `pdftotext`:
  ```
  DEC              -    +    +     +
  PGF2α  (nM)      0    0    100   100
  AL-8810  (μM)    0    0    0     50
  ```
- **Caption, verbatim (p.9):** panel M is described with *"100 nM PGF2α"*, while the clauses for
  **N, O and P** each say *"followed by 1 nM PGF2α for 4 days"* — so the caption is inconsistent
  **with itself** across panels of one treatment series.
- **Results §3.4, verbatim (p.7):** *"100 nM PGF2α"*, twice.
- **Methods support neither.** §2.2 lists the reagent as *"PGF2α (P0424, Merck)"* with **no
  concentration for any experiment**, and no AL-8810 concentration either. Every dose in this
  paper appears only in captions and in-panel labels.

Three sources say 100 nM (the four in-panel labels and the Results twice); one says 1 nM (the
caption for N/O/P). The caption is the outlier, and it contradicts **itself** — its own panel-M
clause says 100 nM. Independently re-verified at 400 dpi for this review: all four panels carry
`PGF2α (nM) 0 0 100 100` and `AL-8810 (μM) 0 0 0 50`. **Not resolved here** — the Methods give no
concentration for either reagent, so there is no independent anchor and only the authors can
settle it. Requires author clarification; any future assertion resting on this concentration
must be `disputed`.

**A second, previously unreported discrepancy in the same panels:** AL-8810 is **50 µM** in
Fig. 4M–P but **1 µM** everywhere else (Figs. 2H, 2O, 3A, and the Results text) — a 50-fold
difference in the one experiment where the antagonist carries the causal weight, with **no
antagonist-alone control arm anywhere in the paper**. At 50 µM an FP-receptor antagonist is far
outside its selective range, so the Fig. 4M–P "abrogation" cannot be attributed to PTGFR
blockade on this evidence. Also note Fig. 2I, where the antagonist arm falls *below* the
untreated baseline — which a competitive block should not do.

### The human biopsy sample size is not adequately reported

Assessed as requested; the answer is **no**, and the defect is omission rather than
contradiction.

**No n appears anywhere** — zero occurrences of `n =`, `patient`, `patients`, `donor`,
`donors`, `biopsy` or `biopsies` in all 13 pages. Fig. 6B–E plot mean ± SD with **no individual
data points**, and the legend states no n.

Methods **§2.4 is titled "Collection of human endometria during the menstrual cycle"** and
contains, in full, only an ethics statement: approval by the Ethics Committee for Clinical
Trials at Drum Tower Hospital under the Nanjing Multicenter Biobank Project, **approval number
2013-081-01**, with informed consent. **A section titled "Collection of human endometria"
contains no collection information at all** — no number of women, no age, parity or fertility
status, no indication for biopsy, no inclusion or exclusion criteria, no exclusions, no sampling
or cycle-dating method. Ethics approval is the only adequately reported element of the
human-tissue work.

Cycle phase appears **only as group labels** (proliferative, LH+2, LH+7, LH+11), with no
statement of how LH was timed and no histological dating — four groups with zero stated n each.
The only replication statement is §2.10's *"All the experiments were repeated individually at
least three times"*, which **cannot serve as a donor n** for fixed-tissue IF: it is ambiguous
between three donors, three sections from one donor, and three staining runs. Under the
AGENTS.md invariant on identifying the independent biological unit, **the experimental unit for
Fig. 6 is not determinable from this PDF**, and the Data availability statement points to an
"attached file" that is not present and gives no accession. Graded **D**; `curation_status` must
not advance past `not_yet_curated` while the experimental unit is unknown.

### Figure rendering was decisive twice more

Consistent with the increment-4 finding, and both are raster-only:

| paper | prose says | rendered panel shows |
|---|---|---|
| Somkuti Fig. 4 | Methods, Results **and** Discussion all call the Northern EGF arm **dose-dependent** | lane labels are `C E2 E2+P4 \| 2h 12h 3d 6d 8d` under the bracket `EGF (10 ng/ml)` — a **time course at one fixed dose**. mRNA dose-dependence is demonstrated nowhere in the paper |
| Jin Fig. 3A | *"activating ADAM17"* | a single band at the in-panel **120 kDa** marker — the pro-form only |

### Other overstatements found against the panels

Jin's Results call the Fig. 3C hCG dose-response "markedly increased" for five proteins, but
p-cPLA2, AREG and HB-EGF are all **ns** between 0.2 and 5 µg/mL · the stromal AL-8810 reversal
is called "abrogated" while Fig. 2P retains ~44% of the increment · Fig. 6 is described as
showing "moderate" mid-secretory signal while AKR1C3 falls 120→3.6 and HB-EGF 27.5→2.6, both
**ns** against LH+11 · the Discussion contains the sign inversion *"hCG is used to reduce
pregnancy rates"* · §2.5 normalises to "RPL" while Table 1 lists **RPL7**. Somkuti's Fig. 5
legend claims a maximum at 1 ng/mL while the panel's highest value is at 100 ng/mL, with no
0 ng/mL control bar, and its Fig. 3 y-axis is truncated at 0.5 with no control bar.

## The stage problem — the most consequential fact for the model

Jin's own Fig. 6 places **every component of the route at maximum at LH+2** and near baseline by
LH+7: AKR1C3 1.0→**120**→3.6→1.35; PTGFR 1.0→42→26→10; EREG 1.0→**193**→55→19; HB-EGF
1.0→**27**→2.6→0.15 (proliferative / LH+2 / LH+7 / LH+11). Arriving at the receptivity window,
AKR1C3 has fallen ~97% and HB-EGF ~90%.

**An embryo-derived hCG signal cannot act at LH+2, because there is no embryo yet.** The paper
never confronts this. Consequence for us: mapping this route onto `E_SECRETORY_STATE` or
`E_RECEPTIVE_SURFACE` would be a **stage misassignment**, and the route cannot be sited on the
model's timeline at all until it is resolved.

## Somkuti and the secretory-state rule: corroboration, not conflict

The first pass framed this as Somkuti conflicting with the model. On verification that framing
is wrong, in the repository's favour. **Exemption `PAR-002` already records the position
Somkuti supports**, in its own words: *"Progesterone is not a verified direct inducer of ITGB3:
REF-007 … reports osteopontin induced by progesterone while the beta3 subunit is induced by EGF
or HB-EGF, and PMID 18647810 found no integrin difference across a fourfold progesterone dose."*

So Somkuti is not a new contradiction. It is the **direct primary measurement behind an
adjudication the repository had already made from secondary statements**, and it independently
confirms the EGF half of REF-007's claim. `PAR-002` was extended with a dated note recording
exactly that, and its `dated` field moved to 2026-07-29. Its already-declared
`action_required=reformulate_hbegf_and_receptive_surface_or_group` is strengthened, not changed.

**Scope of the disagreements, stated precisely.** Neither REF-041 (Daftary) nor REF-048 (Cai) is
cited by **any** edge — verified by querying the assertion table — and
`E_SECRETORY_STATE → E_ITGAVB3_5` carries **no `edge_id`** at all, because unsupported
dependencies get a `topology.tsv` row with an empty `edge_id` and no assertion. **No current
relation is affected by any of this.** These are bibliography-level tensions to settle before a
future hormone-to-ITGB3 edge is signed, not defects in the executing model:

- **vs Cai 2023 (REF-048).** Somkuti has E2+P4 *lowering* surface β3 (~71%) in Ishikawa at 6 d;
  REF-048 has E2+P4 *raising* ITGB3 via MST1/NUR77, with its Fig. 2L showing MST1 mediates the
  steroid effect. Both are human and both include Ishikawa, so this is a genuine scientific
  disagreement, not a species or system artefact.
- **vs Daftary 2002 (REF-041).** REF-041's entry states *"sex steroids do not directly regulate
  beta3"* — and Somkuti, a source that claim plausibly rests on, reports steroid regulation in
  its own design. The tension is real but weaker than it looks: Daftary's claim is about *direct*
  transcriptional regulation, and Somkuti's steroid arms are 6-day continuous exposures with no
  promoter-level evidence of directness at all (its promoter claim is an unpublished abstract).

**The reconciliation, recorded as context-dependence rather than resolution.** Somkuti's own
Discussion argues that in vivo αvβ3 appears only *after* epithelial ER and PR are downregulated
— a sequence a continuously steroid-replete 6-day culture cannot produce, and one this model
cannot represent because `E_PGR` is permanently ON under progestin. That is a legitimate
`context_dependence` note and it is **not** a licence to flip a sign. Two further limits keep it
non-decisive: the readout is the β3 **subunit** alone, and the flip is in any case the one
non-inert Somkuti encoding, deleting `X_ADHESION_ROUTE_SPP1` outright.

## The β3-subunit / αvβ3 distinction is narrower than it first appears

Worth stating precisely, because the first pass overstated it. `E_ITGAVB3_5`'s `node_dictionary`
entry declares its measurement proxy as **"surface ITGAV or ITGB3 or ITGB5"** — a *disjunction*,
not a heterodimer claim, and its own caveat already reads *"Assay-side receptor assignment may
remain mixed."* Somkuti's β3-only measurement therefore falls **within** the node's declared
proxy and is admissible evidence for it; the node was never asserting a heterodimer.

What remains true, and is what the prohibition rests on: Somkuti measures β3 with β3-directed
reagents (AP3, SSA6, a β3 cDNA probe), **never measures ITGAV or ITGB5**, and its heterodimer
specificity is asserted by citation. The paper's own Fig. 2 panel title reads **"Ishikawa Beta
3"** while its caption says αvβ3 — the distinction is visible in the source. So Somkuti supports
the **ITGB3 arm** of that proxy and must not be cited for αv, β5, or heterodimer-specific
behaviour such as ligand engagement or integrin activation.

## Prohibitions — what these papers must NOT be used to encode

Recorded in the style of increment 4's "Mo must not be used to encode `CDH1 inhibits
attachment`", so a later pass cannot resurrect them.

1. **Somkuti must not support `LE018 E_HBEGF → E_ITGAVB3_5`, or any HB-EGF relation.** It tested
   EGF, TGFα and bFGF. HB-EGF appears in the paper **only twice, both in the reference list**,
   never as an experimental arm; EREG and AREG appear not at all. Attaching it would repeat the
   ligand-substitution defect `docs/topology_parity_correction.md` already corrected for
   Apparao on `LE015`.
2. **Somkuti must not be used to flip the sign of `E_SECRETORY_STATE → E_ITGAVB3_5`.** The flip
   is **not inert** — it deletes the SPP1 adhesion route — and the supporting panel has no error
   bars, no statistics and no biological replication, in a depolarised carcinoma line measuring
   a lateral pool.
3. **Somkuti must not be used to encode "P4 has no effect on ITGB3", or any P4/PGR relation.**
   The arm was never quantified and is uninformative by construction given oestrogen-induced PGR.
4. **Somkuti must not license a lumped growth-factor input.** EGF/TGFα signal through EGFR and
   bFGF does not, so the convergence point spans two receptor families and was never localised;
   the nine negatives are confounded by unmeasured receptor expression, making Fig. 3 a
   ligand-availability screen rather than a specificity result. The encoding is inert anyway.
5. **Somkuti must not be cited for promoter- or TF-level regulation of ITGB3, or for mRNA
   dose-dependence.** The promoter claim is an unpublished 1996 SGI abstract (their ref 44), and
   the dose-dependence claim is contradicted by its own Fig. 4 lane labels.
6. **Somkuti must not support any adhesion, attachment or receptivity-function claim.** No
   embryo, spheroid, trophoblast or matrix adhesion assay; no function-blocking antibody or RGD
   peptide; no ITGB3 perturbation. It also speaks to neither αv, β5, nor the heterodimer.
7. **Jin must not be used to encode any LHCGR relation, or any direct `IN_HCG → S_*` stromal
   edge.** LHCGR is absent from the full text, and **no stroma-only + hCG arm exists**, so even
   the epithelium-dependence of the hCG effect rests on external citations.
8. **Jin must not be used to encode an ADAM17 node, or `ADAM17 activates EREG/HB-EGF`.**
9. **Jin must not be used to encode `EREG or HB-EGF → S_IGFBP1` (or `→ S_DECIDUALIZED`) as an
   OR-sufficiency edge.** The licensing arm — ligand **without** the decidualization protocol —
   was never run, and the encoding changes behaviour only in that untested region.
10. **Jin must not be used to encode epithelial EREG/HB-EGF as *necessary* for stromal
    decidualization.** Only the increment above DEC is abolished; necessity would additionally
    force the stromal program to require `IN_E2`, contradicting `SOFIA-HT-001`.
11. **Jin must not be used to encode directed apical-vs-basolateral secretion, or "epithelium
    releases ligand toward the stroma".** The coculture is unpolarised and shares medium, so the
    *direction* of transfer is a property of the well layout, not a measurement.
12. **Jin must not be used to place PGF2α, EREG, HB-EGF, AKR1C3 or PTGFR in the mid-secretory
    window.** Its own Fig. 6 puts them at LH+2.
13. **Jin must not be read as distinguishing a decidual program from cAMP potentiation.** Its
    Fig. 5B shows the coculture raising stromal cAMP *on top of* 250 µM db-cAMP, no arm clamps
    cAMP, and no siEREG/siHB-EGF arm exists for the cAMP readout. Under GAP-009 (severity
    `high`), IGFBP1/PRL change must not be read as implantation outcome, decidual competence or
    adhesion.

## What the Jin full text resolved in `docs/paywalled_papers_needed.md`

All seven blocking fields are answered, so Jin is removed from "Blocking now". The two stated
conditionals resolve as follows.

*"If ADAM17 was genuinely perturbed **and** the epithelial→stromal step used conditioned medium
or co-culture, the route becomes a candidate for `uncertain_rule_variant` with `direct`
intermediate steps."* → **The conjunction fails.** The coculture half is satisfied and is
better than either alternative the doc anticipated; the ADAM17 half is not satisfied at all. The
route therefore **stays `catalog_only` as a whole**, while the single relation *epithelial
EREG/HB-EGF is required for the hCG/PGF2α-driven stromal IGFBP1 increment* stands on its own
merits.

*"If LHCGR was tested and shown necessary, an `IN_HCG → LHCGR` edge becomes licensable."* →
**Still not licensable**, and the reason is weaker than absence-of-effect: the receptor was
never looked at.

*"If hCG was applied chronically at supraphysiological dose, the route may belong to the
chronic-exposure arm."* → **Acute only** (1 h and 6 h; no 24 h or multi-day arm), so it belongs
to the acute arm. Dose physiologicality is **not assessable**: the reagent is given as µg/mL
with no IU, no specific activity and no statement of recombinant vs urinary origin.

This is the **fourth consecutive increment in which hCG yields zero executable relations**.

## Seed-table state corrected

`ADH-SEED-125`: `full_text_status` moves `full_text_inaccessible_paywalled` →
`full_text_or_relevant_results_inspected`; `candidate_claim` rewritten (it asserted "by
activating ADAM17", omitted the AREG negative entirely, left the EREG/HB-EGF effect unqualified
by the DEC protocol, and asserted the untested negative "NOT direct stromal LHCGR signalling");
`notes` rewritten, because all five items it recorded as "NOT obtainable" are now answered and
its final LHCGR sentence is now true of the **full text**, not merely the abstract.

`edge_review_status` deliberately **stays `not_yet_curated`** — the same treatment increment 5
gave the three rows it corrected. Promoting it here would repeat the discovery-tier
misreporting defect that workstream exists to close. `seed_confidence` stays 0.85 but now
applies to the corrected claim, with the notes recording that it does not extend to the ADAM17
clause.

**No seed row was created for Somkuti**, deliberately. The `source_of_discovery` column holds
search provenance and all ten of its existing values are queries; this PDF was surfaced by no
query, so any value would misrepresent the column. **17 of the 26 prior manifest rows already
have no seed row**, so registering directly at the manifest is the majority pattern, and
increment 5's traceability chain begins at `PDF → sha256 → pdf_manifest`, with the seed table
nowhere in it. The seed table is a *backlog* of things to obtain; a paper already in hand does
not belong in it.

## Stale counts corrected

- `docs/model_evidence_audit.md`: its forward-reference "the bibliography is now 57/57" → **59/59**
  (the dated 38/38 figure beside it is left as written, per increment 5's precedent for superseded
  counts).
- **The README needed no count edits, and an earlier claim that it did is withdrawn.** Commit
  `8ebbc5c` removed the whole bibliography/evidence section from `README.md`, so the `57/57`,
  `canonical bibliography records` and seed-backlog figures no longer exist there. A first draft of
  this document recorded corrections to those lines; they were made against the pre-`8ebbc5c`
  README and are now moot.
- **A defect found while checking those counts, recorded because it will resurface.** The README's
  former seed figure of `107` ("129 rows, 107 not yet in the canonical bibliography") was
  **reproducible under no definition**: recomputing gives 113 by DOI and 108 by DOI-or-PMID at the
  current state, and 113/110 at its origin commit. It was wrong when written, not made stale by
  later registration. If that section is ever restored, the figure is **112 whose DOI is not in the
  canonical bibliography** (113 before Jin's registration), and it should be stated together with
  the join that produces it.
- `tests/unit/test_pdf_manifest.py`: the cited-DOI overlap assertion `24` → **26**. This is the
  **only** count-sensitive assertion in the suite; `test_literature_contracts.py` and
  `test_citation_integrity.py` are fully relational, and the 93/96/274 figures derive from
  `edge_evidence.tsv` and `network.bnd`, both untouched.
- Increment 5's "26 manifest rows, 24 registered" and `docs/model_evidence_audit.md`'s "57/57"
  are **dated statements and are left as written**, per the precedent increment 5 set for
  superseded figures.
- `citation_verification.tsv` shows a 116-line diff for 2 new references. That is expected and
  benign: all 57 pre-existing `checked_on` cells were **empty**, and `verify-citations` rebuilds
  every row, so the run stamped today's date across the file. Verified column-by-column that
  **`checked_on` is the only field that changed on any pre-existing row** — no `resolved`,
  `title_similarity`, `year_matches` or `resolved_title` value moved.

## Why claim-level adjudications live here and not in the assertion table

Established from the code, not assumed. `edge_evidence_assertions.tsv` is regenerated by
`migrate_edge_evidence()`, and `test_evidence_assertions.py` runs that regeneration against the
real repository root and asserts byte-identity — so a hand-inserted row would be deleted and
then fail the suite. Independently, neither new reference is named in any
`context/evidence-register.tsv` `location`, so there is **no legal `(edge_id, reference_id)`
pair** for either paper and `validate_assertions` would reject one.

Paper-level judgements therefore live in the manifest's `registration_decision`, and
claim-level judgements live in this document plus the seed `notes`. No placeholder assertion was
created, exactly as in increment 5.

**Registration cannot change the executable model, structurally.** `superset_family.py` reads
`candidate-nodes.tsv`, `candidate-edges.tsv`, `mechanisms.tsv` and the evidence register — never
the bibliography. `references.tsv` is touched only by `evidence/assertions.py` and
`evidence/citations.py`, and `migrate_edge_evidence()` reaches a reference solely by resolving
an edge's `evidence_id` through the register's `location` field, so **a reference that no
`location` names produces zero assertion rows and a byte-identical output file**.
`pdf_manifest.tsv` is read by exactly one file in the repository: its own test.

### The per-relation registry was checked, and correctly holds nothing

The repository *does* have a first-class, machine-validated home for claim-level citation
decisions — `config/edge_citation_adjudications.tsv`, loaded by
`dt_adoc.evidence.citation_adjudications`, with `action` ∈ {`retract`, `attach`} and a `basis`
vocabulary in which **no metadata-only value exists**, so a scope mismatch inferred from a title
can never delete a citation. That registry, not prose, is where per-relation judgements belong,
and it was evaluated for both papers. **Neither yields a legal directive:**

- **`retract` is unavailable.** It requires an existing `(edge_id, reference_id)` pair, and
  `check_applicability()` fails any retraction of something the register does not fan out.
  Neither new reference is named in any `evidence-register.tsv` `location`, so there is nothing
  to retract. Symmetrically, this is why neither paper can *dispute* an existing assertion: the
  contradiction they bear on (`E_SECRETORY_STATE → E_ITGAVB3_5`) has no `edge_id`.
- **`attach` is legal but unwarranted.** The tempting target is `LE018` (`E_HBEGF →
  E_ITGAVB3_5`), because Somkuti is a Lessey-group paper showing EGF-family induction of β3
  sitting next to an HB-EGF→β3 edge. It must be refused: Somkuti never tested HB-EGF, and
  attaching it would reproduce precisely the defect `CIT-005`/`CIT-006` closed on `LE015`, where
  Apparao was retracted for applying HB-EGF as a *treatment* rather than measuring its
  regulation. Note the corpus is already internally consistent here — REF-007 remains correctly
  attached to `LE018`, where HB-EGF *is* the independent variable and β3 the readout.

An empty registry outcome is a finding, not an omission, so a test now pins it (below).

## Not done, deliberately

- **No claim-level `curation_status` was advanced anywhere.** Both papers are now citable, and
  neither has been used to curate an existing assertion. Verified claim-level support stays
  **0/274**.
- **No A–E `evidence_grade` was assigned, and no rubric was invented.** An earlier draft of this
  document carried provisional A–E grades against a rubric written for the occasion. That has
  been removed as a convention violation on two counts. First, the repository's actual graded
  scale is `confidence_scale` in `context/literature/knowledge-base.yaml` (*9* = replicated causal
  or direct platform anchor; *7–8* strong mechanistic with some transfer; *5–6* plausible but
  limited replication or indirect; *1–4* context or unresolved), together with the
  `evidence_level` vocabulary in `references.tsv` — both are already populated for these papers.
  Second, `evidence_grade` is a **field on an assertion row**, and neither paper has an assertion
  row, so any grade would have been unanchored prose. Strength is instead carried where the schema
  puts it: `evidence_level=primary_mechanistic` on both registry rows, with the limits spelled out
  in `key_use`.
- **`seed_confidence` was left at 0.85, deliberately, and an earlier note about it was
  withdrawn.** A draft lowered it, and then justified keeping it by scoping it to "the coculture
  relation, not the ADAM17 clause". Both readings misuse the column: `README.md` defines
  `seed_confidence` as *"how likely a paper is a useful search lead — it is **not** an evidence
  grade and not an edge-validation status"*. Jin is a maximally useful lead: it was requested,
  supplied, read and registered. Re-scoring it on evidential grounds would import exactly the
  tier confusion the discovery table exists to prevent. The evidential limits live in
  `candidate_claim` and `notes`, which were corrected instead.
- **`ADH-SEED-125` was not split into two rows.** Correcting `candidate_claim` so it no longer
  asserts "by activating ADAM17" removes the problem at its source, without minting a seed id
  for a paper already registered.
- **The `route` id `hCG-epithelial-PGF2a-ADAM17-IGFBP1` was left unchanged**, though it embeds a
  step this increment found unsupported. It is a descriptive column, not a key; renaming it is
  cosmetic and would obscure the row's history.
- **No PMID backfill.** Still 22 of the pre-existing references without one, still recommended
  as its own commit.

## Validation performed

| command | result |
|---|---|
| `pixi run verify-citations` (network) | **resolved 59/59**, `citations_intact`, zero errors. One warning, the pre-existing REF-006 abbreviated title. Both new references resolved at `title_similarity = 1.00` with `year_matches = true`, so no new warning was introduced |
| `pixi run test` | **323 tests, OK.** Includes the `24 → 26` manifest assertion and the bidirectional manifest-to-registry DOI join |
| `pixi run validate-evidence-assertions` | **274 assertions / 93 edges / 93 edges with assertions**, `curated_count = 0`, `not_yet_curated_count = 274` — unchanged, and the regenerated file is byte-identical |
| `pixi run lint` / `pixi run format-check` | all checks passed; 94 files already formatted |
| `sha256sum -c` against a pre-change baseline | **all 13 model artifacts byte-identical** — both `network.bnd` files, both `baseline.cfg`, both `edge_evidence.tsv`, both `node_dictionary.tsv`, and `edge_evidence_assertions.tsv` |
| `git status` / `git diff --stat` | **nothing under `models/`**; no `.bnd` or `.cfg` touched |
| `pixi run validate-models --json` | `status: valid`, zero errors, zero warnings — run after extending `PAR-002`, since the exemptions registry is consumed by the topology reconciler and a stale or malformed waiver aborts generation |

Verification-pass checks additionally performed:

| check | result |
|---|---|
| Fig. 2 of Somkuti re-read at 400 dpi | bars ≈ −52% and ≈ −71% against prose values of 45% and 75%; no error bars, no *n*, no significance marker. Panel title reads **"Ishikawa Beta 3"** while the caption says αvβ3 |
| Jin Fig. 4M–P labels re-read at 400 dpi | `PGF2α (nM) 0 0 100 100`, `AL-8810 (μM) 0 0 0 50` on all four panels; AL-8810 returns each readout **to the DEC-alone level, not below** |
| Jin Fig. 3A re-read at 500 dpi | ADAM17 a single band at the in-panel **120 kDa** marker; **GAPDH** loading control present; `AL-8810 (μM) 0 0 0.1 1`, so 1 µM is the maximum here |
| Jin Fig. 5C–E re-read at 380 dpi | siEREG returns stromal IGFBP1 to ≈9.8 against a DEC-alone ≈11; **`siEREG` never appears without stimulus** — the absent knockdown-alone arm confirmed from the labels themselves |
| full-text string checks | `LHCGR`/`LHR`/`luteinizing` = 0 in Jin; `conditioned` = 0; no TAPI-0/TAPI-2/marimastat/batimastat/GM6001; no COX inhibitor and **no hCG arm under PGF2α blockade**; in Somkuti, `HB-EGF` occurs twice, **both in the reference list** |
| corpus-wide molecule search | `ADAM17`, `EREG`, `PTGFR`, `AREG`, `PGF2`, `LHCGR` appear in **no** model artifact — so no node is being removed or demoted |
| assertion-table query | REF-041, REF-048, REF-058 and REF-059 are cited by **zero** edges, so none of the direction conflicts touches a cited relation |

The byte-identity check was taken against hashes captured *before* any edit, so the
no-executable-change claim is verified rather than asserted.

`compile-models`, `smoke` and `render-dynamics-demo` were deliberately **not** run — each
regenerates a model or simulation artifact and would break the byte-identity claim without
testing anything this increment changed.
