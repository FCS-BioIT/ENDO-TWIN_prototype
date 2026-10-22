# DT_ADOC literature-guided MaBoSS rule refinement — reconciled evidence dossier

> **Review artifact / proposed biology only; NOT a canonical model specification, evidence promotion, or implementation authorization.**
> Created 2026-10-21 by reconciling the supplied `DT_ADOC_revised_mechanistic_conclusions_2026-10-21.md` with the detailed source-adjudication checklist and Li S2 annotations in `DT_ADOC_curation_prompt_2026-10-21_v3_fulltext.md` (external file, renamed in this copy). The earlier v3 task prompt is **superseded for instructions**, but its scientific questions are retained in §§7–9. **Every scientific claim remains subject to independent PDF/source verification** by the local agent.
>
> **Source navigation:** [`adoc_2026-10-21_147_paper_screen.md`](adoc_2026-10-21_147_paper_screen.md), plus the prior `maboss_163_reaudit_v3_2026-09-28.md` (a DIFFERENT 163-PDF corpus; do not add counts without deduplication). Source PDFs are local and gitignored. 
> **Planner entrypoint:** [`docs/v05_literature_guided_replanning_request_2026-10-21.md`](../../../docs/v05_literature_guided_replanning_request_2026-10-21.md).

## Authority and boundaries

- The executable `v0.6.0` rules and cited GitHub blob SHA below were **observed**, not changed; verify the local HEAD rather than trusting a historical snapshot.
- This material updates the *literature hypotheses*, **not** the owner-endorsed topology pause (`docs/v05_pause_decision_2026-09-30.md`) and **not** any deferred-item unblock condition (`docs/deferred_topology_register.tsv`).
- Evidence tiers (functional primary, molecular primary, correlative, inferred) are distinct from whether a specific Boolean expression or MaBoSS transition rate is warranted. The original index is a **screen**, not a claim-level evidence ledger.
- Scope: human maternal epithelium/stroma through embryo contact and stable attachment. Trophoblast outgrowth/invasion and embryo lineage specification are separate future-stage phenomena; tumor-cell / mouse evidence requires transfer labeling.
- **Two priority tracks**, not a single ranked biological list: (A) independent mechanisms reaching the adhesion endpoint, and (B) correct molecular regulation/readouts under hormone changes. Neither should be mistaken for experimental *identifiability*.

---

**Date:** 21 October 2026.  **Current executable network:** `models/superset/adoc-literature-superset-v0.6.0/network.bnd`, GitHub SHA `ee40f2a4e98f74a461dc308bf83323785eb45bb4` (read-only comparison). **Model governance:** v0.5 biological-topology pause pending `dropout_e2` remains in force. No changes made.

## Scope and evidence grading

Corpus supplied: 147 articles / 2118 article pages in `DT_ADOC_literature_bundle_2026-10-21.pdf`, plus original PDFs of Thathiah et al. (2004), Paule et al. (2015) and Retis-Resendiz et al. (2024; also represented in the bundle). All 147 were indexed and their full text screened for relevance. 42 highest-relevance articles received targeted methods/results/figure-description inspection in this session or in the immediately preceding review. This is **not** a claim of figure-by-figure appraisal of all 2,118 pages, and the compressed bundle is inadequate for numerical figure digitization. See the companion 147-paper index for transparent coverage.

Evidence classes used below: **functional primary** (perturbation with molecular or adhesion outcome), **molecular primary** (intervention plus proximal readout), **correlative** (expression/localization), **inferred** (proposed topology or cross-system extrapolation). A paper can support a biological direction without selecting a specific Boolean AND/OR or MaBoSS rate.

## 1. Change to earlier headline conclusions

| Previously emphasized | Revised interpretation | Why |
|---|---|---|
| IHH direction should be the first rewiring priority | **Priority for scientific adjudication, not the first executable fix.** Human PGR/IHH responses are context-/donor-dependent; the current IHH cascade is also Boolean-absorbed. | Mouse-positive relationships do not select the sign in human epithelium. The acute adhesion problem is more proximal. Hewitt 2022 is open access but outside the 147-paper bundle. |
| Literature establishes epithelial adhesion persistence after progesterone withdrawal (Ak 2026) | **Downgrade claim.** It demonstrates persistence after an E2-only preconditioning interval, but the blastoid adhesion assay then ran for 48 h in IVC-1 containing **1 µM P4 + 10 nM E2**. | Ak et al. 2026 Methods, bundle pp. 57–58. It does not isolate uninterrupted P4 withdrawal at the assay endpoint. |
| STAT3/GP130 is an unconditional adhesion requirement | **Hard gate unvalidated; candidate strength modifier.** SC144 changed a broad transcriptomic program and several WOI markers but had a modest functional effect, significant at highest shear only, not in AUC. | Ak et al. 2026, Figure 3; n=3 for SC144 functional comparison. Not a receptor knockout or necessarily complete target inhibition. |
| CD98 is most important for a new adhesion branch | **Still high, but homophilic CDH1 binding across the heterocellular interface should be prioritized alongside it.** | Ruan et al. 2026 directly blocked maternal/embryonic CDH1 and quantified ~50% reduction in trophoblast-like spheroid attachment. |
| SLeX is a permissive MUC1 state | **MUC1 abundance, MUC1 glycoforms, and non-MUC1 cell-surface glycan ligands must not be equated.** | Ma et al. 2023 IL1β/FUT3/sLeX; Dong et al. 2025 ST6GALNAC1/sTn-CD44-SIGLEC6. No evidence that both epitopes in those assays were carried specifically by MUC1. |
| TNFα supplies the missing MUC1 clearance determinant | **No.** TNFα promotes shedding **and** increases MUC1 mRNA and cell-associated MUC1; no embryo-triggered local causality or net surface-barrier removal is measured. | Thathiah et al. 2004, Figs 1–7, HES cell line. TI-06 evidence requirement remains unresolved. |
| PC6 is one epithelium-linked receptivity regulator | **It is a multi-substrate proteolytic system, with distinct epithelial and stromal roles.** | Heng 2011/2015; Paule 2012/2015; Okada 2005 and Heng 2010 (outside bundle). Split tissue compartments and precursor vs mature products. |
| PRL and IGFBP1 should be de-aliased | **Strengthen; also separate stromal PGR protein availability from ligand-mediated PGR activity, and transcription from secretion.** | Retis-Resendiz 2024, Cloke 2008, Tamura 2014, Buzzio 2006, Kane 2010. |

## 2. Structural baseline of v0.6.0

The actual executable rules include:

```
E_SECRETORY_STATE = IN_E2 and E_PGR
E_LIF            = E_SECRETORY_STATE and not E_KLF12_HIGH
E_GP130_STAT3    = E_LIF
E_PC6            = E_SECRETORY_STATE
E_MUC1_BARRIER   = not E_SECRETORY_STATE
E_HBEGF          = E_SECRETORY_STATE
E_PAEP           = E_SECRETORY_STATE
E_SPP1_EXPR      = E_SECRETORY_STATE
E_CD98_CD9       = E_GP130_STAT3
E_CDH1_APICAL    = IN_EMBRYO_CONTACT
S_BMP2           = (S_PGR and S_PKA) or S_NR2F2
S_DECIDUALIZED   = S_PGR and S_PKA and S_BMP2
S_PRL            = S_DECIDUALIZED
S_IGFBP1         = S_DECIDUALIZED
```

Under settled endogenous rules and with no intermediate clamps, `E_RECEPTIVE_SURFACE` reduces to the **E2+progestin+not-KLF12** condition. The `S_NR2F2/BMP2/HAND2` family collapses to progestin, and `S_DECIDUALIZED` collapses to progestin AND cAMP. Asynchronous updating creates different transient delays but does not make the molecular determinants independent in the final state. Adding new inputs to an OR that is already absorbed by a hard permissiveness gate cannot rescue that design.

## 3. Ranked curation opportunities (not authorized executable edits)

### A1 — Separate hormone history / surface attachment competence / secretory markers

**Evidence:** Ak et al. 2026: functional shear-resisted blastoid attachment appears after 2 days of EPCX; PAEP rises later; SPP1 expression is weak despite functional attachment; early change in GP130-inhibited markers greatly exceeds change in measured adhesion (bundle pp. 41–46). **Caveat:** the `2-4-2` apparent withdrawal arm is P4 re-exposed during IVC-1 blastoid co-culture (p. 57), so not a true uninterrupted withdrawal test.

**Rule-family proposal:** keep a *historical epithelial adhesion-competence* state distinct from `E_SECRETORY_STATE`, `E_PAEP`, `E_SPP1_EXPR` and `E_GP130_STAT3`. Allow state persistence, but do not assign physical off-rates from this paper. Evaluate whether `E_GP130_STAT3` modifies adhesion strength/rate rather than being an absolute gate. A separate epithelial-only adhesion output is essential for comparing to epithelial-only studies without changing the all-maternal/stromal endpoint.

**Confidence:** 8/10 for de-aliasing marker vs function; 5/10 for replacing GP130 hard requirement; 3/10 for specific rates.

### A2 — Genuine maternal–embryonic CDH1 route

**Evidence:** Ruan et al. 2026, Human Reproduction 41:563–582, DOI 10.1093/humrep/deag009; bundle pp. 1306–1326, Figs 3–6. Maternal apical CDH1 localized in primary human EEC; E2+P4 induces membranous CDH1 in Ishikawa; siCDH1 and CTNND1 knockdown reduce adhesive force and attachment; antibody blockade of either maternal or trophoblast-like CDH1 reduces 1-h attachment by ~50%. Blastoid/trophoblast-conditioned medium or blastocyst medium and hCG increase apical presentation. **Limits:** key adhesion system uses BAP-EB trophoblast-like spheroids/Ishikawa, not a large series of directly manipulated human blastocysts; CDH1 also affects epithelial integrity, and hCG receptor mechanism was not mapped.

**Proposal:** catalog maternal surface CDH1, CTNND1-dependent stabilization/trafficking, embryo-side CDH1, embryo-conditioned signal and physical contact separately. No rule saying contact alone guarantees CDH1 presentation, nor CDH1 an obligatory universal gate.

**Confidence:** 9/10 for the experimentally contributing CDH1 adhesion route; 5/10 for its precise logical function in ADOC.

### A3 — Independently regulated glycan routes, NOT `MUC1_SLEX = SECRETORY_STATE`

**Evidence:** Ma et al. 2023 (bundle p. 964) show IL1β induction of FUT3/sLeX and partial blockade of HTR8 spheroid–RL95-2 attachment by anti-sLeX or FUT3 siRNA. Dong et al. 2025 (p. 274) show ST6GALNAC1 modifies CD44 with sialyl-Tn, with SIGLEC6 as putative human embryo receptor (human cell-line attachment plus mouse in vivo studies). Yu et al. 2018 (p. 1780) add ST3GAL3/sLeX loss-of-function evidence; carrier identity and regulation differ by system.

**Proposal:** keep `MUC1` abundance/barrier separate from `X_SLEX_SURFACE` and `X_CD44_STN`. Test independently inducible cytokine- or glycosyltransferase-dependent routes. Do not treat sLeX, sTn and MUC1 as synonyms, or automatically OR each route into fully competent adhesion.

**Confidence:** 8/10 mechanistic independence, 5/10 for a quantitative adhesion function.

### A4 — De-alias cAMP/PGR/PRL/IGFBP1 without keeping the decidual phenotype permanently ON

**Evidence:** Retis-Resendiz et al. 2024, Steroids 203:109363, DOI 10.1016/j.steroids.2024.109363, original PDF Figs 3–6. **At 24 hours in T-HESC**, cAMP induces PGR-B/PGR-AB RNA and PRL RNA, with MPA reducing PRL relative to cAMP-alone; IGFBP1 responds more to combined MPA+cAMP. H89 and RU486 perturb expected directions. Primary hESC validation in their supplement concerns the full hormone cocktail, not the isolated cAMP/MPA factorial experiment. H89 is not a perfectly PKA-specific perturbation; MPA also engages glucocorticoid and androgen receptors. The study **does not establish** maintained protein secretion under progesterone withdrawal. Cloke 2008 and Tamura 2014 provide independent human stromal evidence for differential PRL/IGFBP1 and cAMP/CEBPβ responsiveness. Kane 2010 shows TGFβ1 suppression of secreted PRL/IGFBP1 can **precede** suppression of their mRNAs, with distinct SMAD4 dependence. Lin et al. 2026 (p. 917) further cautions that conventional in-vitro markers do not straightforwardly map onto in-vivo stromal states.

**Proposal:** `S_PGR_EXPRESSION` != `S_PGR_ACTIVITY`; `S_PRL_TRANSCRIPTION` != `S_PRL_SECRETED`; similarly for IGFBP1. A minimal version can keep transcription/readout as one observable each, but give PRL and IGFBP1 separate stimulus and rate families. Do not make `S_PRL = S_PKA` or `S_IGFBP1 = S_PKA` an indefinite positive switch. Consider EPAC/RAP1/CEBPβ and FOXO1 (Kusama 2013; Buzzio 2006), subject to measurement/identifiability limits. Cloke+Kane+Ujvari already motivated TI-04; new evidence strengthens rationale but not its measurement unblock conditions.

**Confidence:** 9/10 for non-equivalent regulation, 4/10 exact Boolean gates, 3/10 physical kinetic rates.

### A5 — MUC1 production and local apical removal must be separate

**Evidence:** Meseguer 2001 (p. 1035) shows P4-associated human uterine MUC1 increase and local apparent reduction at embryo attachment. Thathiah et al. 2004, DOI 10.1210/en.2004-0399, original Fig. 1: TNFα 3–5× shed ectodomain while also increasing mRNA 5–6× and cell-associated protein 2–3× after 24 hours in HES cells. Brefeldin/monensin experiments show shedding is not simply more nascent delivery. TAPI and TIMP-3 inhibit induced shedding, but broad-spectrum GM6001 did not under tested conditions, so an exclusive ADAM17 assignment is unsupported by this experiment alone. Earlier Thathiah 2003 (ADAM17) and Thathiah & Carson 2004 (MMP14) provide two biochemical sheddases in surrogate cells. Ak 2026 documents local MUC1 reduction at blastoid contact, and **also** shows EPCX downregulation in the epithelial culture, contrasting with in-vivo P4-associated MUC1 increase.

**Proposal:** `E_MUC1_TOTAL`, `E_MUC1_APICAL_PRESENT`, `E_MUC1_SHEDDING_ACTIVITY`, `E_MUC1_BARRIER_AT_CONTACT`, perhaps with contact-local spatial logic that a global well-mixed MaBoSS Boolean node cannot fully capture. No `IN_TNF → NOT E_MUC1_BARRIER` shortcut; increased shedding can coexist with increased cell-associated abundance. The *embryo-local determinant* of shedding is not established. **TI-06 remains deferred.**

**Confidence:** 9/10 separation of production/processing, 4/10 local trigger, 2/10 rates.

### A6 — PC6 activity, precursor maturation and persistence (two cell compartments)

**Evidence:** Heng 2011/2015 (bundle pp. 524, 536) show PC6 cleavage of EBP50 and DAG1 N-terminus in human uterine epithelial systems with functional adhesion assays. Paule 2012 (p. 1250) demonstrates α-integrin processing and surface integrin differences; the β5 route should not be silently transferred to β3. Paule 2015, DOI 10.1093/molehr/gau109, original Figs 2–6, demonstrates PC6-dependent pro-PDGFA processing in HEC1A and direct recombinant substrate cleavage; apical active PDGFA and luteal fluid PDGFAA support physiological occurrence (lavage secretory n=5, proliferative n=5; roughly 160.5 vs 8.96 pg/mL). No direct PDGFA-dependent adhesion experiment was performed. The proteomic discovery pooled n=3 cultures (not n=3 independent discovery samples); follow-up western studies were repeated. **Distinct stromal evidence outside the supplied bundle:** Okada 2005 (DOI 10.1210/jc.2004-0904) shows PC5/6 requirement in human ESC decidualization. Heng 2010 (DOI 10.1210/en.2010-0326) reports stromal PC6 cleavage/activation of BMP2 and partial rescue with active BMP2; obtain full text for full adjudication.

**Proposal:** `E_PC6_ACTIVE` separate from epithelial differentiation, and precursor/mature states for `E_DAG1`, `E_ITGAV` and potentially `E_PDGFA_ACTIVE` (orthogonal biochemical readout, **not adhesion gate**). Independently catalog stromal `S_PC6_ACTIVE → S_BMP2_MATURE` (do not equate maternal epithelial and stromal PC6). Mature/cleaved products require turnover, not instantaneous inversion when enzyme switches off. Do not connect maternal apical PDGFA to **embryonic** Pdgfa→receptor signaling observed in mouse Wang 2023 without matched human evidence.

**Confidence:** 9/10 PC6 processing direction, 6/10 retention/memory model, 3/10 active-molecule turnover rates.

### A7 — HB-EGF stromal source and distinct receptor-level routes

**Evidence:** Lessey et al. 2002 (p. 835): primary human stroma induces HB-EGF RNA with E2 **or** P4 alone, whereas epithelial HB-EGF requires both under tested conditions; HB-EGF and conditioned stromal medium increased epithelial LIF and β3 integrin, with EGFR antibody reducing integrin stimulation. Somkuti 1997 in Ishikawa showed EGF induction of integrin β3 but differential steroid effects. Domínguez 2010 (p. 263) shows independent estradiol, hCG, EGF and LIF induction of epithelial surface CD98, while progesterone alone did not significantly induce it. Direct E2 induction of surface CD98 is **not** evidence that the whole adhesion phenotype survives withdrawal.

**Proposal:** `S_HBEGF` separately regulatable by E2/PGR; `E_HBEGF` production, `E_ERBB_SIGNAL`, and `E_CD98_SURFACE` separately considered. Avoid using an OR rule that makes any low-dose ligand fully sufficient for the entire receptive surface; consider rate effects and direct ligand concentration constraints. `E_CD98_CD9` needs disaggregation if distinct functions are wanted.

### A8 — Revisit LIF/IL11/GP130 as a modifier or non-obligate contributor

**Evidence:** Marwood 2009 (p. 1021) shows both LIF and IL11 induce STAT3 phosphorylation and EEC attachment to fibronectin, but only IL11 increased binding of primary first-trimester trophoblasts in the tested assay. Ak 2026's SC144 intervention substantially perturbs receptor-associated epithelial transcription but has only a modest high-shear functional effect, significant only at the highest flow condition (n=3). Chung 2016 links LIF–integrins to attachment in a different surrogate system. The experiments differ in cells, time, comparator and functional endpoint.

**Proposal:** include non-LIF STAT3 inputs and ligand-specific downstream branches. Treat compulsory `E_GP130_STAT3` in `E_RECEPTIVE_SURFACE` as **questionable**, but do not infer zero role from partial pharmacological inhibition. Its gate placement should be examined **jointly** with all alternative adhesion routes, otherwise new routes remain phenotype-inert.

### A9 — WNT/DKK1 balance, alternative stromal fate regulators and in-vitro marker caveats

**Evidence:** Tulac 2003/2006 (p. 1543/1550) show physiological and PGR-associated DKK1 induction in human stroma. Macdonald 2011 (p. 975) supplies PROK1→DKK1 loss-of-function evidence. Li 2013 (p. 897) supports BMP2/WNT4/β-catenin and shows excessive DKK1 can inhibit decidualization, whereas Macdonald DKK1 loss-of-function also compromises decidual markers. Kane 2008 (p. 694) demonstrates TGFβ1-dependent DKK1 suppression. Additional human stromal modifiers: Thapa 2023 BMP2→ATOH8→FZD4/FOXO1 (p. 2064) and Guo 2026 HBP1→IGFBP1 / PGR transcriptional activity (p. 1918). These challenge overly compact pathway representations but often are not observationally identifiable under current ADOC protocols. Lin 2026 gland/organoid co-culture (p. 917) shows gland secretome can inhibit stromal decidual markers in hormone+cAMP cultures, while its in-vivo scRNA analysis finds poor agreement between conventional in-vitro marker expression and decidual subtypes; scRNA sensitivity/dropout and tissue compartment definitions limit how strongly this can be generalized.

**Proposal:** catalog alternative rule families, **not** `DKK1 = decidualized` nor any one hard DKK1 gate. Consider gland paracrine state or CEBPA/EDN1 as a regulatory candidate only if a specific primary functional ligand is available. Avoid setting quantitative WNT feedback from two opposing gain-/loss-of-function studies conducted under different conditions.

### A10 — XAV939 is a candidate secretory-differentiation modifier, not a direct adhesion gate

**Evidence:** Garcia-Alonso et al. 2021 (bundle p. 351) combined WNT inhibitor exposure with culture conditions that also removed RSPO1 and observed increased secretory differentiation and PAEP expression in human epithelial organoids. Kagawa et al. 2022 Extended Data Fig. 8d (p. 651 onwards) directly compares hormone-stimulated human epithelial layers ±XAV939 for PAEP, LIF, SPP1, GPX3 and DPP4 markers, but not matched blastoid adhesion. Ak 2026's EPCX condition includes XAV939 **together with** E2/P4/cAMP; its adhesion results do not identify the marginal effect of XAV939.

**Proposal:** distinguish hormone-induced secretory differentiation from the WNT-inhibition modifier, while retaining `IN_XAV939` as an as-yet-uncalibrated experimental input. No `IN_XAV939` hard gate and no endorsement of a numerically defined XAV939 activation/repression rate.

### A11 — Membrane localization / polarity provides a second axis distinct from RNA expression

**Evidence:** Kakar-Bhanot et al. 2019 (bundle p. 683) Rab11a knockdown reduced cell-surface αVβ3 integrin and JAr spheroid attachment in Ishikawa. Peng et al. 2021 (p. 1259) manipulations of PAR3 / integrin β1 altered epithelial polarity and adhesion in endometrial carcinoma lines, with tissue comparisons. Ruane et al. 2024 (p. 1327) perturbed O-GlcNAcylation, ROCK and actomyosin during Ishikawa attachment; high-glucose cell-line conditions mean its quantitative values are not generalizable to human ADOC. Ruan 2026 further identifies CTNND1 as supporting apical CDH1 localization and adhesion. Lessey 2002, Domínguez 2010 and Heng 2015 independently separate availability of ligand/protease from surface presentation or cleavage.

**Proposal:** consider a small membrane-trafficking/apical-polarity *regulatory layer* driving localization of a few measured adhesion effectors, rather than indiscriminately adding a new common obligatory membrane-state AND gate. A route becomes distinguishable only when its surface exposure and actual attachment contribution are independently measured.

### A12 — Alternative mucin barrier and adhesion-feedback candidates remain lower priority

**Evidence:** Gipson et al. 2008 (p. 444) demonstrated reduced MUC16 at the receptive uterodome apical surface in human biopsies, and Liu et al. 2020 (p. 953) reassessed human MUC16 around implantation. These are not MUC1 effects, and the model does not explicitly distinguish their roles. Berneau et al. 2019 (p. 86) tested CD44/hyaluronan adhesion using mouse embryos and human Ishikawa. Matsumoto et al. 2008 (p. 1030) reported that **added IGFBP1 alone** induced stromal PRL secretion/morphological decidualization after long exposure and implicated α5β1/RGD binding; this suggests possible extracellular feedback but does not license restoring `S_IGFBP1` as a mandatory gate on the compact decidual-state readout. Embryo/decidual feedback, endothelial prostanoid and invasion studies should remain later-stage candidates unless tied to measured ADOC adhesion endpoints.

**Proposal:** retain candidates in the evidence catalog and report their assay system and developmental stage, but prioritize currently actionable molecular layers and measured outputs first.

## 4. Unresolved contradictions to preserve, not smooth over

1. **Human IHH:** mouse PGR→Ihh is strong; human epithelial organoid data (Hewitt 2022; not among 147) show MPA can attenuate E2-induced IHH in 2/3 donors, while secretory human tissue often exhibits higher IHH. No automatic edge reversal without stage/compartment context.
2. **MUC1:** high in human secretory tissue, locally reduced at contact, yet EPCX organoid culture shows globally lower MUC1. Hormone combinations, isolation of stroma, surface compartment and detection reagents differ.
3. **PRL after PGR blockade:** 24-h MPA effects in immortalized cells differ from long-term P4-supported secretion in primary hESCs. Distinguish time, dose, receptor cross-reactivity, RNA and protein.
4. **LIF/Gp130:** positive STAT3/ECM adhesion in cultured EECs does not prove zero embryo attachment when the pathway is pharmacologically diminished. SC144's modest functional effect cannot prove total dispensability.
5. **Integrin αVβ3/β5:** a single merged node hides separate biochemical processing/regulation and reader context. In particular, PC6 effect on β5 cannot be silently treated as proven for β3.
6. **Embryonic versus maternal PDGFA:** a mature maternal apical ligand and embryonic mouse PDGFA signaling are not the same compartment or causal link.
7. **In-vitro PRL/IGFBP1 vs native decidual cells:** normal hormonal responses in culture do not imply markers are equally discriminative in in-vivo scRNA states.

## 5. Minimal comparison plan when topology pause is lifted

Run one-factor-at-a-time candidate variants, not a wholesale seven-module rewrite. First, simplify composed Boolean functions and enumerate absorbed/phenotype-inert nodes before adding biology. Then evaluate `E_GP130_STAT3` gate placement, persistence of epithelial adhesion competence, CDH1/CTNND1 contact route, independent sLeX-FUT3 pathway, and separately regulated PRL/IGFBP1 with stromal PGR expression vs activity. Test epithelial-only and whole-maternal endpoints distinctly. Assess all original conditions and withdrawal schedules with identical input encoding. Require each variant to specify falsifying observations, cell compartment, molecular layer (RNA, protein, activity, localization, secretion), and measurable quantity; use uncalibrated rates only as sensitivity parameters.

No model modification can retroactively make absent cross-factorial ADOC measurements identifiable. Tissue-/cell-line-derived qualitative edges can improve biological prior plausibility while increasing parameter uncertainty. Preserve `dropout_e2`, fixed baseline outputs, node dictionaries and the existing deferred items; never silently reinterpret an old benchmark as support for a newly changed model.

## 6. Additional primary PDF worth requesting

**Highest-value missing full text:** Heng et al. (2010), *Posttranslational Activation of Bone Morphogenetic Protein 2 Is Mediated by Proprotein Convertase 6 during Decidualization for Pregnancy Establishment*, DOI [10.1210/en.2010-0326](https://doi.org/10.1210/en.2010-0326). Published abstract documents direct human primary-stromal PC6 inhibition, complete loss of mature BMP2 and partial rescue by active BMP2. The full text is needed for inhibitor specificity, dosage and temporal adjudication of a possible `S_PC6_ACTIVE -> S_BMP2_MATURE` route. It is **not** in the 147-paper consolidated bundle. Okada et al. (2005), DOI [10.1210/jc.2004-0904](https://doi.org/10.1210/jc.2004-0904), provides complementary human ESC PC6 morpholino evidence and an accessible publisher PDF.

The 2003 ADAM17 and 2004 MMP14 MUC1-sheddase primary papers are available online without a new user upload (Thathiah et al., DOI 10.1074/jbc.M208326200; Thathiah & Carson, DOI 10.1042/BJ20040513).

## 7. Primary-figure adjudication checklist inherited from the v3 brief

This section retains high-value **source-level details and negative controls** from `DT_ADOC_curation_prompt_2026-10-21_v3_fulltext.md` (external file, renamed in this copy). They are assertions to **verify against the original PDFs**; no table entry here licenses a particular MaBoSS rule. These were not all independently re-checked in this packaging step.

| Study | Critical figures/contrasts | Specific limitation and prohibited inference |
|---|---|---|
| **Tulac 2003**, DOI `10.1210/jc.2003-030494` | Figs 2–3: DKK1 higher in secretory human endometrium (reported ~234-fold, only **n=3 tissues/phase**), primarily stromal; SFRP4/FRPHE opposite phase association. | Cycle association ≠ direct promoter binding or rate; no phase-fold-change conversion into MaBoSS rates. |
| **Tulac 2006**, DOI `10.1210/jc.2005-0769` | Figs 1–2 and 4–6: human stromal E2+P4 increases **DKK1 RNA and secreted protein**; RU486 interferes; long-term induction; cAMP alone fails to induce DKK1 in tested short condition. | Withdrawal includes **E2+P4 co-withdrawal**, not selective P4 withdrawal; RU486 does not prove direct promoter binding. Distinguish P4 from MPA. |
| **Cloke 2008**, DOI `10.1210/en.2008-0356` | Figs 1,5; Table 3: DHT enhances PRL secretion but not equally IGFBP1 in primary human stromal cells; AR antagonism/siRNA; PR siRNA reduces DKK1 and disrupts **nuclear** SMAD2/β-catenin accumulation; STAT3/STAT5b **protein abundance** changes. | Do not mistake total STAT3/STAT5b for phospho-STAT3; do not reverse nuclear β-catenin direction using secondary summaries. |
| **Kane 2008**, DOI `10.1210/me.2007-0316` | Figs 2,4,5,7: differentiated primary stromal cells + exogenous TGFβ1; initial transient PGR RNA rise; DKK1 RNA decline ~12–24 h, secreted DKK decline ~48–72 h; SMAD4 knockdown abrogates PGR suppression but not DKK **protein release** suppression. | Release result does not prove entirely SMAD-independent transcription; endogenous anti-TGFβ1 versus exogenous ligand give different results; late-differentiated context only. |
| **Li 2013**, DOI `10.1210/en.2012-1585` | Figs 2–5: BMP2 induces **WNT4 and DKK1/DKK2/SFRP3** concurrently; WNT4 and CTNNB1 loss-of-function decrease decidual markers; WNT4/CTNNB1 support FOXO1; enforced DKK1 overexpression inhibits. | Expression co-induction ≠ WNT pathway net sign; adenoviral DKK1 not physiological dose; microarray pooled three donors in one discovery experiment. |
| **Macdonald 2011**, DOI `10.1093/molehr/gar031` | Fig 5: primary stromal PROK1 knockdown reduces DKK1 RNA and **secreted protein**; PROK1 or DKK1 depletion reduces PRL, IGFBP1, IL11 and decidual morphology. | No rescue/epistasis proving all PROK1 effects run through DKK1; PROKR1→Ca2+→NFAT elaboration is particularly supported in engineered Ishikawa and decidual-explant systems, not the entire chain established in normal primary stroma. |
| **Liu 2010**, DOI `10.1093/humrep/dep429` | Fig 5: **recombinant** DKK1 applied to **JAr trophoblast-like spheroids** before a 1-h Ishikawa attachment assay; dose-related attachment decrease with anti-DKK1 rescue. | No proof endogenous maternal **stromal** DKK1 reaches the embryo in comparable doses; spheroid count ≠ donor replication; not direct patient implantation causality. |
| **Garcia-Alonso 2021**, DOI `10.1038/s41588-021-00972-2` | Fig 7/extended figures: WNT inhibitors including XAV939 alter epithelial organoid secretory/ciliated balance and PAEP. | Medium also omits RSPO1/changes other components; no matched blastoid-adhesion experiment. |
| **Kagawa 2022**, DOI `10.1038/s41586-021-04267-8` | Fig 4: stimulated OFELs support blastoids; Extended Data Fig 8d directly compares EPC and EPC+XAV939 for **PAEP, LIF, SPP1, GPX3, DPP4** (reported n=2 independent experiments). Fig 4e tests trophospheres modified during *formation* by SC144/XMU-MP-1. | XAV939 contrast is **marker only**, not isolated attachment; embryo formation perturbation ≠ acute maternal GP130/Hippo effect on physical attachment. |
| **Li 2026**, DOI `10.1016/j.cell.2025.10.026` | Fig 6/STAR Methods/S3H: Round I viability/metabolic activity, Round II **48-h outgrowth**; blocker effects involving VEGFA/VEGFR1 and CGA/FSHR are incompletely localized. Table S2 = supplier inventory/hit list. | 48-h outgrowth ≠ initial attachment. CGA is not uniquely hCG, FSHR is not LHCGR; no arbitrary receptor-direction edges. Vendor drug annotation ≠ target engagement. |
| **Paredes 2026 / Sonderegger 2010 reviews** | Citation chasing and developmental-stage context. | Reviews cannot individually license direct model edges; use cited primary papers. |

### DKK1 contradiction matrix — explicitly retain four different experiments

1. **Native/stromal expression:** E2/P4/PGR signaling is associated with stromal DKK1 induction and secretion (Tulac), with PGR knockdown support (Cloke).
2. **Native/stromal perturbation:** reducing PROK1 or DKK1 compromises decidual-marker responses (Macdonald).
3. **Strong forced overexpression:** high DKK1 expression suppresses BMP2/WNT4/β-catenin-induced decidualization markers (Li 2013).
4. **Embryonic-cell-line exposure:** supraphysiological recombinant DKK1 inhibits JAr-to-Ishikawa attachment when the JAr arm is exposed (Liu 2010).

These are not one experimentally measured U-shaped dose–response curve. Assign each its distinct **cell system, compartment, treatment dose, stage and readout**. A nonmonotonic DKK1/WNT hypothesis may be proposed for a *future* rule family, with unknown thresholds, but not made canonical.

### Distinct origins of published embryo/implantation phenotypes

- Primary human EEC *molecular* responses do not automatically constitute embryo adhesion perturbations: see Domínguez CD98 hormonal induction versus the different HEC1A/mouse-blastocyst perturbation assay.
- **Ak 2026**: EPCX induced adhesion strength in an epithelial-only chip; after E2-only preconditioning, the **subsequent IVC-1 blastoid assay reintroduced P4**. No uninterrupted progesterone-withdrawal adhesion inference or physical withdrawal off-rate is permitted.
- **Ruan 2026**: the ~50% CDH1-blockade effect supports a contributing route in a trophoblast-like spheroid / epithelial assay, not universal direct human-blastocyst essentiality.
- **Thathiah 2004**: TNFα elevates both MUC1 synthesis and shedding in HES; TAPI/TIMP3 sensitivity but GM6001 insensitivity caution against over-specific assignment; this is **not** the embryo-contact-local cleavage determinant sought by TI-06.
- **Paule 2015**: PC6 processes PDGFA in HEC1A and recombinant cleavage assays; apical mature PDGFA is correlated with receptive tissue, but **PDGFA-dependent attachment** was not measured.
- **Retis-Resendiz 2024**: 24-h T-HESC factorial MPA/cAMP **RNA** and PKA inhibitor assays support PRL/IGFBP1 distinct regulation; primary-cell validation is of the full cocktail rather than the complete factorial; H89 selectivity and MPA AR/GR effects matter.

## 8. Li 2026 Supplementary Table S2: inventory retained from v3

**File dependency:** `mmc2.xlsx` is NOT among the three Markdown files in this handoff; the local agent must locate the separately transferred original workbook. Do not infer that the Markdown summary substitutes for it. Verify actual sheets, file digest, chemical identities and counts before analysis.

- Sheet `1,119 compounds`: **1,119 distinct named inventory entries**; supplier compound/target/pathway annotations, CAS and vendors, *not assay effect sizes*. Avoid `max_row` as entry count.
- Sheet `Effective compounds in Round II`: **28 distinct hits** in **three** RIF-derived models, without per-hit quantitative outgrowth or uncertainty columns. Grouping: **RIF-29th n=10**, **RIF-44th n=7**, **RIF-60th n=11**. No identical compound appears in two hit lists.
- **RIF-29th (10):** Evocalcet; Choline (bitartrate); Nitrendipine; Nomegestrol acetate; Pranoprofen; Oxaliplatin; Adenine (hemisulfate); Ensulizole; Baicalin; Diacerein.
- **RIF-44th (7):** Phenylbutazone; Ferulic acid (sodium); L-Proline; Indinavir (sulfate); Sofalcone; Trelagliptin (succinate); Gemcitabine.
- **RIF-60th (11):** Avobenzone; Vasopressin; K2EDTA; Larotrectinib sulfate; Citicoline; Olprinone (Hydrochloride); Eltrombopag; L-Leucine; Fulvestrant; Malic acid; Ruxolitinib (phosphate).
- **Identity QC:** `K2EDTA ` (trailing space) matches first-sheet `EDTA (dipotassium dihydrate)` by CAS **25102-12-9** and vendor URL; verify before claiming missing identities.
- **Assay caveats:** Round I screens cell metabolic activity/viability; Round II measures **blastoid outgrowth**, with compound pretreatment and continued presence during co-culture. Do not turn any positive drug hit into a direct adhesion edge or assign embryo versus maternal target uniquely. Paper source data/Fig 6F, not Table S2, are needed for numerical efficacy and replication.
- **Mechanism hypotheses (catalog only):** nomegestrol/PGR; fulvestrant/ESR; ruxolitinib/JAK1/2; olprinone/PDE/cAMP; pranoprofen and phenylbutazone/COX. The broad categories are NOT validated MaBoSS signed edges. Flag chelation (EDTA), UV filter (avobenzone), metabolites/nutrients, cytotoxic agents and CCK-8 metabolic assay confounding. The supplier `Launched` flag is not proof of jurisdiction-specific FDA approval.
- **Required eventual annex:** agent-generated 28-row donor/compound/CAS/annotated target/source figure/stage/model overlap/support decision; if the workbook is unavailable, mark **unverified**, and request its real local path.

## 9. Audit correspondence: no topic from v3 silently discarded

| Legacy v3 request | Reconciled dossier locus / disposition |
|---|---|
| A: stromal PGR→DKK1 | §3 A9; §7 Tulac/Cloke; supported for expression/secretion, not adhesion gate |
| B: PROK1/PROKR1 and intermediate receptor mechanism | §3 A9; §7 Macdonald; intermediates system-specific, catalog only |
| C: conflicting DKK1 loss/gain and embryo exposure | §7 DKK1 matrix; keep contradictions explicit |
| D: BMP2→WNT4 AND DKK1/DKK2/SFRP3, CTNNB1→FOXO1 | §3 A9; §7 Li 2013; no unmeasured feedback law |
| E: stromal DKK1→epithelial LRP5/6 and embryo-side DKK1 | §7 Li 2026/Liu 2010; separate predictions from perturbations |
| F: XAV939/RSPO1/Kagawa marker-only contrast | §3 A10; §7; reject direct adhesion gate |
| G: PRL/IGFBP1 TI-04 and embryo competence | §3 A4; §7 Cloke/Kagawa; keep approved endpoint definitions |
| H: Li 2026 S2 28-compound screen | §8; outgrowth-only hypothesis annex |
| I: TGFβ1/SMAD4 vs BMP2 | §7 Kane; late-state RNA versus secretion, context restricted |
| J: embryo GP130/STAT3 vs maternal | §7 Kagawa; future embryo module boundary |
| K: prioritize stromal biology | **Revised** to two decision tracks: molecular correctness/observability and independent adhesion routes; see §10 |

## 10. Proposed prioritization framework for implementation planning (NOT an implementation decision)

**Track A — adhesion endpoint/structural independence:** baseline static alias and endpoint-gate audit → GP130 hard gate and adhesion-output definition → maternal/embryonic CDH1/CTNND1 route → FUT3/sLeX and ST6GALNAC1/sTn–CD44 candidate pathways → CD98/CD9 and Rab11a polarity/trafficking → MUC1 barrier (blocked causal clearance). Each proposed change must demonstrate unabsorbed downstream effect, or be explicitly *catalog-only*.

**Track B — stromal molecular validity/readouts:** PRL versus IGFBP1 independent cAMP/MPA/AR/FOXO1 regulation; RNA vs secretion; PGR expression vs ligand activity → PROK1/DKK1 and BMP2/WNT4/CTNNB1/FOXO1 → epithelial/stromal PC6, products/turnover → TGFβ1/SMAD4 late remodeled-state modulation, HB-EGF source separation. Do not force any stromal readout into the adhesion endpoint merely because it has a supported regulator.

**Cross-cutting**: XAV939 secretory marker modulation; human IHH sign contradiction; donor and time context; experimental identifiability; MaBoSS rates as uncertain **relative** parameters; separation of maternal-only from embryo/contact/outgrowth. A route is higher priority only if it changes a *specified measurable quantity* and passes the repository's pause/unblock criteria. Competing studies can support alternatives rather than one canonical rule.

**Missing figure-level paper:** Heng et al. (2010), DOI `10.1210/en.2010-0326`, stromal PC6→mature BMP2; useful for **specific** causal adjudication and not a prerequisite for planning the rest. No need to ask for already available papers without first checking local paths.

**Implementation is not approved.** This dossier has not modified any MaBoSS node, rate, state, phenotype, protocol, or evidence ledger. See the separate planning-only request in `docs/v05_literature_guided_replanning_request_2026-10-21.md`.

## 11. Explicit boundary items for the local reviewer

- **Human IHH fork:** the current executable `E_IHH = E_PGR` borrows a strong mouse-supported sign; compare human epithelial-organism observations (Hewitt 2022) with human secretory-phase association (Wei 2010), and distinguish stromal paracrine/phase context. No automatic `E_IHH = NOT E_PGR` correction, and no admission before source- and context-level adjudication.
- **Two separate glycan families:** **Ma et al. (2023)** implicate IL1β→FUT3→sLeX in RL95-2/HTR8 spheroid attachment, whereas **Dong et al. (2025)** examine ST6GALNAC1→sTn on CD44 and putative embryo-side SIGLEC6 with human cell-line and mouse evidence. Neither mechanism is a validated human MUC1-specific sLeX clearance or a direct universal implantation gate.
- **Post-attachment PROS1 axis:** **Molè et al. (2026)** report trophoblast PROS1 / stromal AXL–AKT as a post-adhesion outgrowth-support hypothesis, including AXL inhibitor effects after invasion has begun. Retain under *future post-attachment* mechanisms, not initial epithelial attachment, and do not treat AXL-inhibitor sensitivity as unique proof of PROS1 ligand identity.

## Final confidence (conservative)

- Presence of problematic hard aliases in current executable rules: **10/10** (symbolically inspectable; static composed identities).
- Human primary evidence that several molecules have independent upstream regulation: **9/10**.
- Need to distinguish transcription, activity, apical localization and secreted proteins: **9/10**.
- Particular alternative topologies affecting *human ADOC embryo adhesion*: **5–7/10** depending on mechanism.
- Unique Boolean functions / AND-vs-OR and physical MaBoSS transition rates from this corpus alone: **2–4/10**.

**Conclusion:** The priority is not to make switch curves visually smoother. It is to ensure that the experimentally observed entity (`surface CDH1`, `sLeX`, `cleaved DAG1`, `secreted PRL`, `epithelial shear-resistant adhesion`) corresponds to the correct model node, independently regulated upstream branch and appropriate endpoint. Source-specific effects can then become falsifiable hypotheses rather than artificial hormone clones.
