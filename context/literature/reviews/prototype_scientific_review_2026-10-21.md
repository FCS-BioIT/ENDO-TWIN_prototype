# DT_ADOC: independent repository-to-literature rule audit

Review date: 21 October 2026. Read-only scientific assessment. **No repository files were modified.**

## Scope and provenance

- Live GitHub repository: https://github.com/fransua-fcs/dt-ADOC_prototype ; default branch `main`, inspected at commit `9bc91a70e08059ce2cafb359ef1b81408e0c92cf` (PR #36 merge, 21 October 2026).
- Current executable maternal MaBoSS model: `models/superset/adoc-literature-superset-v0.6.0/network.bnd`. This model contains 56 nodes, 89 dependencies, 29 distinct composed Boolean functions, 17 phenotype-inert nodes (under the repository's structural clamping definition), and three unread inputs (`IN_HCG`, `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_XAV939`).
- Repository's prior primary literature re-audit: `context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md` (review of *a different 163-PDF archive*, not this 156-PDF bundle). Prior recommended deferrals include MUC1 abundance/clearance, CD98/CD9, LIF/IL11, alphaVbeta3/alphaVbeta5, IHH/PGR, stromal mechanics, PRL/IGFBP1 timing.
- Repository's explicit pause: `docs/v05_pause_decision_2026-09-30.md`; no biological topology extension until prospective `dropout_e2` evidence. Software-only intervention refactor into v0.6.0 does not change the biology.
- Newly provided literature bundle: 156 articles, 2,304 article pages, 135 in its main collection and 21 in the `prl_igfbp1_foxo1` subcollection. Every article was separated and text-indexed. All titles/abstracts were screened; **40 prioritized articles had selected full-text sections inspected in greater detail**. Perturbation claims in the candidate ledger were checked against methods, results or figure captions for the highest-ranked bundled sources; the other triaged papers are not independently verified at figure level. This is **not** a completed 156-paper, figure-by-figure independent replication or a guarantee that the corpus is exhaustive.
- Outside literature: targeted public-web/PubMed search through 21 October 2026, including 2026 new primaries. Paywalled full text was not inferred from abstracts.

Associated deliverables:
- `DT_ADOC_literature_triage_156_2026-10-21.tsv`: every supplied article, bundle page and preliminary relevance class; **a screening index, not 156 verified mechanisms**.
- `prototype_candidate_rules_2026-10-21.tsv`: 31 ranked, compartment-specific candidate mechanisms with sign, endpoint, evidence strength, source DOI, overlap with the current references register, disposition, and a conservative confidence score.

## Definition of a candidate MaBoSS edge

A signed edge is proposed as *candidate* when the source supplies either (A) a direct molecular interaction or promoter-level effect in a relevant human cell type, or (B) a perturbational association with a relevant adhesion/decidualization endpoint. These are distinguished in the ledger caveat field. Associations are never promoted to a necessity gate without an intervention/rescue sufficient to support the causal interpretation. Mouse-only findings are considered transfer hypotheses, not human rules. External embryo signals remain external in a maternal-only network.

Confidence grades in the ledger rate **whether the reported evidence supports the narrowly worded candidate direction**, not the probability that a proposed rule will generalize to an ADOC phenotype. An executable Boolean AND/OR relationship may be much less certain than a source-supported positive or negative influence.

## Highest-value direct adhesion/interface mechanisms

### 1. Human embryo-derived miR-661 / nectin-1 (PVRL1): prioritized missing reference and rule

Cuman et al. (2015), DOI [10.1016/j.ebiom.2015.09.003](https://doi.org/10.1016/j.ebiom.2015.09.003), bundle P016 / page 259. Human blastocyst-conditioned media carry miR-661 (greater in the nonimplanting group). Primary human endometrial epithelial cells take up miR-661. Mimic treatment downregulates PVRL1 protein and reduces HTR8 trophoblast spheroid attachment; a PVRL1 target protector inhibits the miRNA-PVRL1 interaction and partially restores attachment (Results 3.4-3.5 and Fig. 4). Proposal: `IN_EMBRYO_MIR661 -| E_PVRL1_SURFACE`, with PVRL1 supporting initial adhesion. **Do not treat the clinical correlation as proof that this miRNA causes implantation failure in patients.**

### 2. RAB11A-mediated adhesion-protein surface trafficking

Kakar-Bhanot et al. (2019), DOI [10.1093/humrep/dey365](https://doi.org/10.1093/humrep/dey365), bundle P051 / p. 799. Stable Rab11a knockdown in Ishikawa epithelium reduces *surface* alphaVbeta3 integrin and alphaV and lowers JAr spheroid adhesion; total E-cadherin also falls. Proposal: de-alias expression from surface availability, e.g. a candidate `E_ITGAVB3_SURFACE <- E_ITGAVB3_EXPR AND E_RAB11A_TRAFFIC`; **the AND is a modeling hypothesis**, not verified across all hormone states. Do not equate RAB11A-mediated trafficking with CDH1 transcription.

### 3. DNM2-mediated polarized secretion

Zhou et al. (published 3 October 2026), DOI [10.1093/reprod/xaag120](https://doi.org/10.1093/reprod/xaag120), PubMed PMID 42830467. This **is outside the 156-paper bundle** and absent from the main repository reference register. Human progestin-responsive endometrial organoids show DNM2 induction; DNM2 inhibition alters apical secretory proteome; DNM2 knockdown lowers trophoblast spheroid adhesion and STAT3/SPP1 expression. Proposal: `IN_PROGESTIN -> E_DNM2_ACTIVITY -> E_APICAL_SECRETOME`, associated with attachment. **Do not write `DNM2 -> pSTAT3 -> SPP1 -> attachment` until direct mediator/rescue data are checked.** Oxford labels the accepted manuscript open access, but I verified the abstract/metadata rather than extracting the paper's full figures in this session.

### 4. Distinct glycan-receptor mechanisms (do not collapse into MUC1)

Dong et al. (2025), DOI [10.1016/j.jare.2024.07.021](https://doi.org/10.1016/j.jare.2024.07.021), bundle P023/p. 340, already repository REF-049: progesterone induces endometrial ST6GALNAC1; it generates sialyl-Tn (sTn) decoration on CD44 that binds embryo-side SIGLEC6 in biochemical/receptor models. Functional human in-vitro attachment assays use AN3CA epithelium and JAr spheroids, supported by mouse experiments. Distinguish **sTn/CD44/SIGLEC6** from the other glycan mechanism.

Ma et al. (2023), DOI [10.1093/biolre/ioad007](https://doi.org/10.1093/biolre/ioad007), bundle P070/p.1080, already REF-077: `IL1B -> FUT3 -> surface sLeX -> trophoblast-spheroid attachment`, supported by FUT3 knockdown and anti-sLeX. Its sLeX substrate need not be MUC1. Existing `E_MUC1_SLEX` should not imply sLeX exclusively modifies MUC1. Human trophoblast receptor assignment remains uncertain; it is not automatically the same as the SIGLEC6/sTn pathway.

### 5. Additional candidates worth registering, not necessarily canonicalizing

- Ruan et al. (2026), [10.1093/humrep/deag009](https://doi.org/10.1093/humrep/deag009), P092, REF-019: embryo-conditioned cues relocalize CTNND1/CDH1 to the **apical surface**; homophilic CDH1 attachment is supported by blocking and AFM. Functional assays mostly use human embryo surrogates. Currently `E_CDH1_APICAL = IN_EMBRYO_CONTACT`, so the biological intermediate cannot act independently in the model.
- Zhou et al. (2024), [10.1073/pnas.2401071121](https://doi.org/10.1073/pnas.2401071121), P135, REF-057: epithelial miR-124-3p directly inhibits IQGAP1 and influences polarity and attachment in primary human cells with human embryo trophoblast material. LIF/STAT3 are listed as *predicted* targets in the introduction; do not encode those as verified direct effects.
- Paule et al. (2012), [10.1093/humrep/des203](https://doi.org/10.1093/humrep/des203), P085: PCSK5/PC6 processes pro-alpha integrins including alphaV and alpha5 and affects epithelial trophoblast spheroid attachment; alphaVbeta5 surface loss was observed. Does **not** establish equal alphaVbeta3 regulation. This strengthens the existing TI-03 beta3/beta5 split.
- Mo et al. (2026), [10.1186/s11658-026-00927-7](https://doi.org/10.1186/s11658-026-00927-7), P076: elevated ENTPD3 hydrolyzes extracellular ATP and inhibits epithelial EMT/P2Y2-dependent adhesive behavior in Ishikawa plus mouse systems. This is a candidate *apical epithelial* purinergic route, not a universal physiological EMT gate.
- Huang et al. (2026), [10.1038/s41598-026-60110-y](https://doi.org/10.1038/s41598-026-60110-y), P047: NDRG2 loss impairs Ishikawa adhesion and mouse implantation and downregulates FHL1. **No demonstrated direct `NDRG2 -> FHL1 -> adhesion` necessity chain**: candidate mediator only.
- Sugihara et al. (2008), [10.1016/j.febslet.2007.12.001](https://doi.org/10.1016/j.febslet.2007.12.001), P106: contact-localized hCG plus IL1B induces epithelial TRO/trophinin and adhesiveness to trophoblast-derived cells. Human embryo ligand production is not an intervention tested here; older surrogate model.
- Santos et al. (2020), [10.1186/s12958-020-00682-0](https://doi.org/10.1186/s12958-020-00682-0), P095, REF-053: epithelial TPP1 knockdown reduces spheroid adhesion, but SIRT1/BCL2/TP53 changes are not proven mediators.
- Marwood et al. (2009), [10.1210/en.2008-1538](https://doi.org/10.1210/en.2008-1538), P073, REF-072: IL11 and LIF both promote epithelial cell **ECM** adhesion via STAT3; only IL11 increases trophoblast-to-epithelium adhesion under this assay. This is a reason to de-alias LIF/IL11 and discriminate outcome definitions.

## Highest-value stromal decidualization mechanisms

### 6. HBP1 transcriptional activity branch (high)

Guo et al. (2026), DOI [10.1038/s42003-026-09567-1](https://doi.org/10.1038/s42003-026-09567-1), bundle P141/p. 2113. HBP1 knockdown impairs stromal decidualization and FOXO1/IGFBP1 expression. ChIP-seq/RNA-seq implicate **direct HBP1 transcriptional activation of IGFBP1**; overexpression increases promoter H3K4me3 at PGR and its targets, improving PGR target transcription **without necessarily raising PGR protein abundance**. A useful candidate distinction is `S_PGR_PROTEIN` versus `S_PGR_TRANSCRIPTIONAL_ACTIVITY`, with HBP1 modifying the latter. Avoid inventing a hard necessary AND gate across all states.

### 7. BMP2/cAMP to ATOH8 branch (high)

Thapa et al. (2024), DOI [10.1210/endocr/bqad188](https://doi.org/10.1210/endocr/bqad188), P153/p. 2250. Human endometrial stromal fibroblasts: ATOH8 siRNA decreases decidualization, overexpression strengthens it; BMP2 and cAMP induce ATOH8; knockdown lowers FZD4, FOXO1 and several FOXO1-responsive markers. Candidate `S_BMP2/cAMP -> S_ATOH8 -> S_FZD4/FOXO1-dependent program`, where second edge signifies perturbational downstream response, not necessarily direct TF binding. This supplies a specific branch between modeled `S_BMP2` and the previously absent functional FOXO1 layer.

### 8. Nuclear actin / cell-cycle arrest (high)

Tamura et al. (2024), [10.1038/s42003-024-06492-z](https://doi.org/10.1038/s42003-024-06492-z), P108/p. 1649. Human stromal decidualization forms reversible **nuclear F-actin filaments**; nuclear non-polymerizable actin and XPO6 overexpression impair decidualization and appropriate cell-cycle exit; CEBPB suppresses XPO6. Mechanistically orthogonal to hormone transcription/readouts: an explicit differentiation/cell-cycle output could prevent `S_DECIDUALIZED` from being merely the same as PRL/IGFBP1. Do not identify nuclear filament assembly with the epithelial `E_ANXA2_ACTIN` node.

### 9. CDC42 / excessive WNT / stromal senescence (high)

Tang et al. (2024), [10.1093/humrep/deae246](https://doi.org/10.1093/humrep/deae246), P111/p.1682. In human primary stromal cells, CDC42 loss is associated with AKT-mediated GSK3B inhibition, beta-catenin nuclear accumulation, senescence, poor decidual differentiation and weakened BeWo trophoblast coculture phenotype. XAV939 partially rescues the defect. **This licenses a context-specific excessive-WNT defect, not a universal `WNT OFF = good` rule.** Candidate useful when representing heterogeneous stromal maturation and senescence.

### 10. Counterregulation from glandular epithelium (high)

Lin et al. (2026), [10.1093/jmcb/mjag023](https://doi.org/10.1093/jmcb/mjag023), P067/p.1033. Human gland organoid-conditioned medium **reduces** progesterone/cAMP-induced stromal PRL/IGFBP1 and mesenchymal-to-epithelial morphologic transition; this occurs without gross loss of viability, and a dose effect was measured. CEBPA and EDN1 decrease. WNT7A and CSF1 are reported among changing secreted proteins but are **not isolated as the causal inhibitory ligands**. This supports a placeholder `X_GLAND_SECRETOME_DECID_BRAKE` *uncertainty variant*, not a molecule-specific hard edge. Particularly important for multicompartment ADOC.

Lin also shows standard PRL/IGFBP1 **in-vitro markers do not necessarily resolve in-vivo stromal states** in the Garcia-Alonso atlas. It flags eight more discriminating in-vivo markers (STAT3, CEBPB, WNT4, IL15, TIMP3, HAND2, FOXO1, MMP19); this comparison uses transcript abundances and should not be over-generalized to protein or culture-system calibration.

### 11. Other stromal branches supported by perturbation

- Huang et al. 2022, [10.7554/eLife.72073](https://doi.org/10.7554/eLife.72073), P046, REF-060: `SOX4 -| HERC4-dependent PGR ubiquitination`; SOX4 also positively affects FOXO1. Primary human stromal evidence; already in reference register but not independent network state.
- Kusama et al. 2013, [10.1016/j.placenta.2012.12.017](https://doi.org/10.1016/j.placenta.2012.12.017), P057, REF-073: EPAC1/EPAC2-RAP1 potentiates PKA-driven stromal differentiation. **EPAC-selective cAMP analog alone does not induce PRL/IGFBP1**, arguing against a single cAMP branch.
- Kusama et al. 2014, [10.1210/en.2013-1478](https://doi.org/10.1210/en.2013-1478), P058: EPAC2-related calreticulin contributes to decidual markers and morphology (separate senescence effects). Candidate `S_EPAC2 -> S_CALR`.
- Matsumoto et al. 2008, [10.1093/molehr/gan038](https://doi.org/10.1093/molehr/gan038), P074, REF-074: IGFBP1 acts through alpha5beta1 integrin in cultured human stroma to promote decidualization; this is a **potential feedback edge**, unlike simply treating IGFBP1 as a reporter.
- Murata et al. 2019, [10.1016/j.repbio.2019.02.005](https://doi.org/10.1016/j.repbio.2019.02.005), P080, REF-062: progesterone→stromal HAND2 ┤ FGF9 → ANGPT2. Strong human stroma; **does not show human epithelial mitogenic activity of FGF9**, which remains an unverified cross-compartment step.
- Carriero et al. 2026, [10.1093/reprod/xaag096](https://doi.org/10.1093/reprod/xaag096), *external, open access*: anandamide exposure to decidualizing immortalized stromal cells lowers FOXO1/IGFBP1 but leaves PRL unchanged; NOTCH1/HEY1 is also affected. Supports **differential readouts**, not an established causal NOTCH1→FOXO1 chain.
- Liu et al. 2026, [10.1038/s41598-026-41800-z](https://doi.org/10.1038/s41598-026-41800-z), *external, open access*: both increased and decreased PANX1 compromise human stromal decidualization; eATP peaks transiently. This **directly rejects assigning PANX1 a single monotonic Boolean sign**; model level, duration or rate instead.
- Yang et al. 2026, [10.1016/j.mce.2026.112913](https://doi.org/10.1016/j.mce.2026.112913), *external, abstract verified*: NNMT loss increases intracellular SAM/PRC2 and H3K27me3 at decid genes, suppressing differentiation; EZH2 inhibitor rescues partially. Excellent chromatin/metabolism branch **pending primary figures**.
- Yu et al. 2026, [10.1007/s10815-025-03771-4](https://doi.org/10.1007/s10815-025-03771-4), *external, abstract verified*: SETD7-associated decidual senescence and AKT-FOXO1(T24) regulation. Precise FOXO1 **protein accumulation vs nuclear activity** requires full paper; do not encode exact molecular sign before reading figures.

## Model-level recommendations (not executable patches)

**A. De-alias molecular expression, maturation, trafficking, surface contact.**

A conditional, *not-yet-executable* family could distinguish `E_ITGAVB3_EXPR` from `E_ITGAVB3_SURFACE` (RAB11A-dependent), `E_ITGAVB5_MATURE` (PCSK5 processing), `E_CDH1_APICAL` (contact/CTNND1-dependent) and sTn/sLeX glycoforms. Distinguish temporal occupancy from necessity: clamping redundant adhesion effectors may be inert when hormone-dependent `E_HBEGF` already satisfies a disjunction.

**B. Keep embryo-side binding partners external.**

For a maternal-only model, `TE_SIGLEC6`, `TE_CDH1`, trophoblast competence, blastocyst miR-661 and embryo hCG/IL1B should be embryo input conditions, not silently treated as maternal intracellular states. Their direct genotype/state is unknown in ADOC unless separately measured.

**C. Split endpoints by stage.**

Use `OUT_INITIAL_ATTACHMENT`, `OUT_ATTACHMENT_PERSISTENCE`, and (separately, after appropriate evidence) `OUT_TRANSEPITHELIAL_INVASION`. Current `OUT_STABLE_ADHESION` hard-requires `S_DECIDUALIZED` and a permissive ECM; that is a conceptual definition not a direct proof that the same prerequisites govern first contact. The latest 2026 Izmaylova paper (DOI 10.1093/molehr/gaag053, external) shows antibody interference with DSG2 affects transepithelial *invasion after attachment*, not necessarily initial attachment.

**D. Decidual differentiation should not be defined by only PRL/IGFBP1.**

Introduce, at least in an observation-level variant, stromal `S_TRANSCRIPTIONAL_COMPETENCE` (HBP1, SOX4, FOXO1, ATOH8), `S_STRUCTURAL_DIFFERENTIATION` (nuclear actin / cell-cycle arrest), `S_SENESCENCE_OR_MALADAPTIVE_WNT` and separate PRL/IGFBP1 reporters. Their regulatory truth tables need timed stimulus and matched human-data support; expression correlations cannot identify all gates.

**E. Restraint and negative feedback are biologically real.**

`X_GLAND_SECRETOME_DECID_BRAKE`, pathological `S_PANX1_HIGH` and `S_CDC42_LOW_WNT_HIGH` may explain differing decidualization potential under the same hormone/cAMP cocktail. Avoid a one-bit universal WNT, senescence, ATP or gland-secretome sign.

**F. Preserve the owner-approved pause.**

Rank and register evidence now; do **not** rewrite `network.bnd` or reclassify prior deferred topology as approved. When the `dropout_e2` endpoint becomes available, ask first which of the alternative rule families can be distinguished. A new network that simply adds all 31 candidates increases state space while leaving many causal parameters non-identifiable.

## Papers I would request from you (not already included and currently abstract-only)

1. **Yang et al. 2026 NNMT/EZH2/H3K27me3:** DOI [10.1016/j.mce.2026.112913](https://doi.org/10.1016/j.mce.2026.112913). Elsevier paper; publisher access for full figures was not available in this session. Highest missing full-text priority for the decidualization network.
2. **Yu et al. 2026 SETD7/AKT-FOXO1/senescence:** DOI [10.1007/s10815-025-03771-4](https://doi.org/10.1007/s10815-025-03771-4). PubMed indicates PMC deposit is embargoed until **1 March 2027**. Full text needed to resolve phospho-FOXO1 interpretation.
3. **Izmaylova et al. 2026 heterotypic junction / DSG2:** DOI [10.1093/molehr/gaag053](https://doi.org/10.1093/molehr/gaag053). Journal page carries all-rights-reserved information and only public abstract was accessible, so figures are required to validate the DSG2 mechanism. Prioritize when the model extends beyond initial adhesion to epithelial traversal.
4. **Zhou et al. 2026 DNM2:** DOI [10.1093/reprod/xaag120](https://doi.org/10.1093/reprod/xaag120). **Open access**, not a paywall request. The accepted manuscript is available as publisher PDF, but figure-level extraction was not completed here; uploading it would accelerate experimental-detail adjudication.

No PDFs need to be supplied for articles already in the 156-document bundle, including HBP1, RAB11A, Cuman miR-661, and Lin gland secretome.

## Limitations and confidence

- Confidence that the current GitHub state and structural counts were accurately read: **9/10**.
- Confidence that the selected **source-reported directions** are fairly represented: **8/10** for the examined bundled primaries, **6/10** for abstract-only outside papers.
- Confidence that the **exact MaBoSS logic** proposed here would be valid without additional experimental calibration: **4/10**. This is deliberately lower; many source interventions are context-specific, use surrogate embryos or immortalized epithelia, and test attachment rather than long-lived adhesion.
- Strong evidence for a **gene's functional involvement** is not equivalent to proof of a particular edge being indispensable for *ADOC* adhesion. None of the 31 candidates was promoted to an executable rule by this read-only review.
