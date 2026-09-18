# Curation increment 4 — 17 new full-text PDFs

Date: 2026-07-29. Claim level: `read-only full-text triage`. **No executable model file was
modified. `network.bnd` is untouched. No rule changed. No integrin decomposition.**

## Inventory

26 PDFs in `context/literature/pdfs/` (gitignored, never committed), 130 MB, **zero duplicate
hashes**. 17 are new; 9 were inspected in increment 3. `context/literature/pdf_manifest.tsv`
records DOI, PMID, publication status, study type, system, compartment, pages, SHA256 and
figure-inspection status for all 26. The owner's list of 17 matched the directory exactly.

**Two are ACCEPTED, UNEDITED MANUSCRIPTS** and are flagged as such throughout: Mo 2026
(PMID 42014997) and Huang 2026 NDRG2. Nothing from either may enter `executable_core` before
a version of record exists.

## Figure rendering was decisive, again

Panel labels and bar values are raster and invisible to `pdftotext`. Rendering overturned or
materially qualified a prose-based reading in **eight** places across this and the previous
increment:

| paper | prose says | figure shows |
|---|---|---|
| Chung 2016 Fig. 3 | ambiguous "b3 and b5 antibodies" | **five separate arms** — individual necessity IS assignable |
| Apparao 2001 Fig. 6 | dRGD-OPN result is "data not shown" | plotted at ~4% of control, asterisked |
| Cai 2023 Fig. 1A | legend says Nur77 | panel shows **HOXA10** |
| Santos 2020 Discussion | "**up**regulation of SIRT1, BCL2, p53" | figures show all three **decreased** |
| Dong 2025 Fig. 6C-ii | bait captures CD44 from OE lysate | bait-only lane carries CD44 at 0.65 vs test lane 0.58 |
| Mo 2026 Fig. 5H/5I | ENTPD3 "inhibited migration and invasion" | ENTPD3 arm migrates **more** than its control; two empty-vector controls differ >2-fold |
| Ruane 2024 Fig. 1C | "reduced embryo attachment" | **all arms converge by E6.5** — a rate effect, not a deficit |
| Wang 2023 Fig. 7C | "largely conserved between humans and mice" | **13.3–18.6%** at ligand-receptor level |

Any future curation of a figure-dependent claim must render the panel.

## The one relation that escapes absorption

Eight epithelial nodes are bit-identical to `E_SECRETORY_STATE`, three are its complement, and
all eight disjuncts of `E_RECEPTIVE_SURFACE` are absorbed. Almost every mechanism in this batch
would therefore be inert if encoded. The exception:

```
ATTACH_CDH1 = IN_EMBRYO_CONTACT and E_CDH1_APICAL and T_CDH1_APICAL
```

It escapes because it is a **conjunctive gate on the attachment transition**, not a ninth
disjunct of an already-absorbed OR-group. Licensed by Ruan 2026, which blocked maternal and
embryonic CDH1 **separately** (7 antibody arms with matched IgG per side, plus a 4-arm peptide
replication) and found the effect **non-additive** — single-side ~38%, double ~53%, peptide
49%/50%/48%. Blocking either side saturates, which is the signature of one bond requiring both
partners.

**The current `E_CDH1_APICAL = IN_EMBRYO_CONTACT` is causally inverted.** Ruan: apical CDH1
rises in response to soluble hCG and blastocyst-conditioned medium *"prior to its physical
contact with the endometrium"* — 30 min to 3 h, no embryo present. The model makes it a
consequence of contact.

## Contradictions resolved by localisation and stage

**CDH1 has no global sign.** Mo 2026 reports reduced CDH1 accompanying attachment competence;
Ruan 2026 reports apical CDH1 mediating attachment. They are reconcilable:

- **Localisation** — Ruan measures the *apical* pool by confocal segmentation and reports
  **relocation** from basolateral to apical, at roughly constant total. Mo measures *total*
  cellular CDH1 by whole-lysate western with no apical/basal discrimination. A cell dismantling
  lateral junctions while trafficking CDH1 apically shows both.
- **Stage** — Mo is stages 1–2 (hormonal preparation, competence); Ruan is stage 3 (first
  contact), by AFM.

**This reconciliation is a consistent hypothesis, not a demonstrated fact.** No experiment in
either paper measures apical and lateral CDH1 in the same cells under the same perturbation,
and Ishikawa — Mo's system — is poorly polarised and arguably cannot report the distinction the
reconciliation turns on.

**Mo must not be used to encode `CDH1 inhibits attachment`.** Mo never perturbs CDH1: there is
no knockdown, no overexpression, no blocking antibody. Every CDH1 statement is a marker
readout. The adhesion drop is confounded by co-suppression of ITGB3 and LIF in the same
condition. The only causal CDH1 perturbation in the corpus is Ruan's, and it points the other
way.

## Mechanisms that would break the equivalence class

| mechanism | breaks? | blocker |
|---|---|---|
| **Wang 2023** `E_LE_EEC`/`E_LE_AEC`/`E_LE_SEC` decomposition | **yes**, into >=3 distinct variables | only if `IN_EMBRYO_PDGFA` and `IN_EMBRYO_EFNA34` are **separate** inputs. Collapsing them into one embryo signal restores the class exactly. All causal evidence is mouse; ligands are CellPhoneDB/nichenetR predictions, never perturbed |
| **Dong 2025** sTn-CD44 : SIGLEC6 | **yes, at the route level** — integrin-independent and not gated by `E_LIF`/`E_GP130_STAT3`, so it bypasses the bottleneck | human embryonic SIGLEC6 is scRNA-seq only at ~400-count scale, no protein at any stage; the human-cell `ST6GALNAC1` shRNA appears in Methods but no knockdown result appears anywhere |
| **Ruane 2024** ROCK/myosin-II contractility | would break if it held | Fig. 5D is underpowered — p=0.06, nothing significant at E6.5, and **no 17 mM comparator** despite the text asserting equivalence to it |
| **Cai 2023** MST1/NUR77/ITGB3 | **no** | the authors' own Fig. 2L shows MST1 *mediates* the E2+P4 effect. It refines an existing edge rather than adding a parallel one, and would be doubly absorbed |

## XAV939 — status changes from unfalsifiable to contradicted

No standalone XAV939 perturbation exists in ADOC or the repository; every protocol with
`IN_XAV939: true` also sets E2, progestin and cAMP, and the node has no outgoing edge.

New cross-platform evidence: **Molè 2026 reaches implantation of real human blastocysts (52 of
86 surviving) on an E2+P4+cAMP differentiation protocol**, and **Shibata 2024 reaches 54.3%
blastoid adhesion on E2+MPA+cAMP+prolactin** — neither includes XAV939 in the differentiation
step. (Molè lists XAV939 in its key-resources table, so the reagent is used somewhere,
most likely organoid expansion medium.)

Rejected variants A and B encode XAV939 as **necessary for the entire epithelial adhesion arm**
(competence 0.820 to 0.000 on withdrawal). That specific claim is now **positively contradicted
across platforms**, not merely unfalsifiable. It remains `catalog_only`; a future ADOC
HT-minus-XAV939 experiment should be framed as testing a graded modulation, not a hard gate.

Shibata Fig. 1K is a genuine standalone XAV939 manipulation, but in organoid expansion medium
containing CHIR99021, with apical-out morphology rather than receptivity as the readout, and it
points the other way (XAV939 *suppresses* apical-out formation). Catalogued, not wired.

## hCG — third consecutive increment with zero relations

Bienert 2021 lands entirely outside the modelled compartment (endothelial CD144/CD146) **and
returns a null inside it**: epithelial CDH1 p>0.9999 and desmocollin-2 p=0.6286, both point
estimates moving *downward*, at n=7. Same cohort, same assay, on exactly the compartment the
model represents. Ruan 2026 adds hCG-ligand sufficiency for apical CDH1 redistribution but
explicitly declines LHCGR necessity — the authors *"postulated"* it and name lectin-like and
LHCGR-independent routes as live alternatives.

With Herrmann-Lavoie (sufficiency only) and Licht (a review), **LHCGR is sufficiency-only from
every direction**. An `IN_HCG` input feeding CDH1 is defensible; an `LHCGR` gate is not.

## Extracellular vesicles

Both directions catalogued separately; directionality is the load-bearing distinction and must
not be merged. Segura-Benítez 2025 (maternal to embryo) has the better system — human primary
EVs, human blastocysts — and **no specificity control at all** (the comparator is medium alone);
its cargo evidence is a database intersection of two published datasets. Muhandiram 2023
(embryo to maternal) has the worse system (three cancer lines) and the better controls
(HEK293-EV comparator, orthogonal MFGE8 ELISA at 2.8x vs 1.05x) but **no adhesion assay of any
kind**, and its one adhesion-adjacent pathway term carries **FDR 0.94** while being captioned as
p<=0.05.

Neither warrants a consumer for `IN_EMBRYO_CONDITIONED_SIGNAL`. Wiring it would relocate a dead
end by one node while *breaking* the epithelial equivalence class as a side effect.

## ADOC observables

Of 13 candidate readouts in Zaragozano 2026, **8 appear nowhere** in
`config/observation_model_map.tsv`. The highest-value unmapped one is the **ciliated-cell
fraction** (18.67% to 6.10%, 5 chips / 3 donors, same figure panel as PAEP, cross-supported by
Ak and Molè) — and it matters because it moves **downward**. Both currently activated gates
(OM-001 PAEP, OM-002 IGFBP-1) move upward and both saturate to 1.0000 vs 0.0000 at the decided
horizon. A third same-direction gate adds nothing; a down-moving readout is the only cheap way
to catch a candidate that simply switches the whole epithelial arm on.

Rejected as calibration targets: **adhesion onset time** (`calibration.yaml` declares
`calibrated_physical_time: false` and `duration_units: relative_only`, so an hours-valued output
is a category error); **EVs** (the paper's own fig. S4D reports EV release is hormone-
*independent*); **permeability** (no node with the right semantics, and the paper's two Papp
statements point in opposite directions); **betahCG, embryo area, dZ, polar-TE orientation**
(embryo-side, post-attachment).

**Shibata Fig. 4E must not constrain the maternal hormone-to-adhesion arm**: removing the
epithelium *doubles* adhesion (100% vs 54.3% control), and both hormone withdrawal and combined
ER/PGR blockade are non-significant.

**New confound for OM-001**, the sole active constraint: Shibata Fig. 2E/2F shows substrate
alone (collagen vs Matrigel) raises PAEP mRNA and secreted glycodelin independent of hormone.
ADOC coats the epithelial channel with Matrigel.

## Stage decomposition — six collapse to four

The practical test is whether ADOC can measure the boundary. It cannot distinguish
(1)->(2) (there is no embryo-free competence assay) and cannot observe (5)->(6) at all — the
platform paper says so: *"Because of its architecture, ADOC has just been used to study embryo
adhesion."*

Recommended: **1a** E2-driven proliferative / **1b** P4-driven differentiation (Wang's
ovariectomy reconstitution is the cleanest hormonal boundary in the batch) — then **2** apical
adhesion competence, modelled despite being unmeasured because Ak shows it dissociates from
markers — then **3** stabilised attachment, the only calibrated endpoint — then **4** a single
lumped post-attachment placeholder deferred to `physiboss2_coupled_model_later`.

**Initial contact should not be a stage.** It is an experimental delivery step and is already
correctly an input.

Wang additionally argues the chain should **branch** at 1b into an adhesive track (PDGFA/PDGFRA
to attachment) and a supporting track (EFNA3/4/EPHA1 to stromal decidual licensing, via PDZ area
and Prl8a2/FoxO1), converging later — because two embryonic ligands act simultaneously on two
epithelial populations with different downstream targets.

## Ak 2026 — what it does and does not show

It falsifies *"PAEP level is a faithful proxy for adhesion competence"*, which is exactly what
`OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE and E_PAEP` assumes: competence saturates by
day 2 while PAEP peaks at day 6.

It does **not** show competence is flat. Point estimates *decline* 50.09% to ~45% to ~36%; the
6-day AUC carries no significance bracket against the pre-receptive control; and there is no
2d-vs-4d-vs-6d comparison or equivalence test at n=3. The chip is also epithelium-only, and the
authors warn the missing stroma may explain the extended permissiveness. ADOC has stroma.

## Deferred to later executable architecture work

Integrin decomposition; the CDH1 attachment gate; the Wang three-state decomposition; the
sTn-CD44 route; ROCK/myosin-II; adding a ciliated-cell node and OM-012; dropping `and E_PAEP`
from `OUT_EPITHELIAL_RECEPTIVE`; splitting the transcriptomic and competence axes. Each is
recorded above with its named blocking experiment.

## Correction, 2026-07-29: two papers were inspected but not adjudicated

Peng 2021 and Zhou 2024 were obtained, hashed, paginated, figure-rendered and marked
`full_text_inspected=yes`, but neither appears anywhere in the text above. The manifest
therefore claimed they were read while no adjudication existed. Recording both now.

**Zhou 2024 — miR-124-3p / IQGAP1.** `catalog_only`, with one relation at
`uncertain_rule_variant`. Target evidence is a site blocker rather than a reporter — a
target-site blocker restored both IQGAP1 protein and spheroid adhesion in **primary human
HEEC**, which is at least as strong as a heterologous 3'UTR luciferase assay and is done in
the right cell type. The strongest human-relevance result is a loss-of-function rescue in
cells from infertile women. Three limits: miR-124-3p significantly downregulates at least
20 of 88 screened predicted targets, so it is not an IQGAP1-specific perturbation; the
barrier/polarity readouts (TER, SCRIBBLE) are Ishikawa-only while the adhesion readouts are
HEEC-only, so the causal ordering `IQGAP1 loss -> depolarisation -> adhesion loss` is not
established and the two should be encoded as parallel outputs rather than a chain; and LIF
was never measured, appearing only as an Introduction-level prediction. The causal in vivo
backbone is entirely mouse.

**Peng 2021 — PARD3 / ITGB1.** `catalog_only`. A directed `PARD3 -> ITGB1` rule is
**contradicted by the paper's own Fig. 7C**, where si-Par3 raises ITGB1 protein. The data
support mutual antagonism, which would introduce the model's first feedback loop and break
its DAG property — flagged, not adopted. The antagonism is also inferred across systems:
Par3 is knocked down only in HEC-1A and ITGB1 only in RL95-2, two lines whose differing
baseline receptivity is the very variable the experiment is meant to explain. Reciprocal
siRNA cross-elevation of this magnitude is equally the signature of compensation. The clean
part is the steroid link (E2+P4 lowers PARD3, raises ITGB1, dose-ordered), which folds into
`E_SECRETORY_STATE` and is absorbed. Data-quality flag: the western molecular-weight labels
are internally inconsistent between Fig. 6A and Fig. 7A, which are the two panels the causal
claim rests on. Peng's transwell assays measure **maternal epithelial** invasion as a
polarity surrogate and must never be mapped to a trophoblast-invasion stage.

