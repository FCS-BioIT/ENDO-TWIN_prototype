# ADOC Digital Twin — calibration / discrimination candidates

> **Generated file — do not edit.** Regenerate with `pixi run build-calibration-candidates`. Sources: the curated `context/experiments/calibration_candidates.tsv` plus the committed model `adoc-literature-superset-v0.4.0` and the evidence layer.

This ranks usefulness for **mechanistic discrimination of the maternal DT**, not contraceptive efficacy. Information value is reported on separate axes and deliberately **not** collapsed into one score: a candidate can be strong for the terminal interface abstraction and weak for the maternal core, and a single number would hide exactly that.

Everything structural below is **derived** from the committed model and evidence files. Only judgement fields are curated. Where the two disagree, the derived column is right and the curated row needs fixing.

## Summary

| Candidate | Compartment | Ambiguity tested | Proximal readouts | Maternal-DT info | Interface info | Embryo | Perturbations | Model status | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| **CAND-01** E2-only priming -> surface CD98 | epithelial | CD98-c versus BOTH CD98-a (v0.4) and CD98-b, which Gate 3a computes to be mutual… | surface CD98/CD9 | high | low | no | 0 | present | direct_human |
| **CAND-02** LIF neutralisation -> pSTAT3 | epithelial | E_LIF, E_GP130_STAT3 and E_CD98_CD9 are one rule-induced class, so anti-LIF, STA… | pSTAT3, surface CD98/CD9, ITGA2 | high | medium | no | 1 | present | direct_human |
| **CAND-03** IL-11 exposure with LIF neutralised | epithelial | Same alias as CAND-02, plus whether the GP130-b variant (E_GP130_STAT3 = E_LIF o… | pSTAT3, ITGA2, surface CD98/CD9 | high | medium | no | 2 | present | direct_human |
| **CAND-04** STAT3 inhibition | epithelial | Same alias class as CAND-02. Less specific than ligand perturbation because it c… | pSTAT3, surface CD98/CD9, PAEP | medium | medium | no | 1 | present | transferred_only |
| **CAND-05** Hormone cocktail minus cAMP | stromal | IN_cAMP and S_PKA are one class, both re-adjudicated ARTIFICIALLY_COUPLED on 202… | PRL, IGFBP1 | high | low | no | 1 | present | direct_human |
| **CAND-06** SMO antagonist -> stromal NR2F2/HAND2/BMP2 | stromal | E_PGR, S_PGR, E_IHH, S_NR2F2 and S_BMP2 are a five-member class: PGR activity, I… | PTCH1, GLI1, NR2F2 | high | low | no | 1 | present | human_plus_transferred |
| **CAND-07** BMP signalling inhibition | stromal | Whether BMP2 acts through a receptor/SMAD step distinct from the PGR/IHH/NR2F2 a… | PRL, IGFBP1, BMP2 | medium | low | no | 1 | present | transferred_only |
| **CAND-08** PC6 knockdown -> alpha-DG-N shedding | epithelial | E_PC6 = E_DAG1_CLEAVED asserts the enzyme IS its product; both are adjudicated A… | PC6/PCSK5, alpha-dystroglycan full-length, alpha-DG N-terminal | medium | medium | no | 1 | present | direct_human |
| **CAND-09** HAND2 loss | stromal | S_HAND2 is NOT_RULE_COLLAPSED -- it has its own Boolean function, so this pertur… | HAND2, PRL, IGFBP1 | high | low | no | 1 | existing | human_plus_transferred |
| **CAND-10** hCG challenge | epithelial | IN_HCG is declared but ZERO-DEGREE -- read by no rule -- so it currently has no … | surface CD98/CD9, apical CDH1, PAEP | unresolved | low | no | 1 | **zero-degree** | direct_human |
| **CAND-11** Anti-SPP1 -> attachment | interface | Separates the two terminal interface relays, which the hormone-treated arm alone… | attachment fraction | low | high | yes | 1 | existing | direct_human |
| **CAND-12** XAV939 dropout | both | IN_XAV939 is ZERO-DEGREE: present in every HT protocol and read by no rule, so t… | PAEP, IGFBP1, PRL | unresolved | low | no | 1 | **zero-degree** | none_cited |
| **CAND-13** COX-2 / PGE2 pathway perturbation | unresolved | None that can be stated: there is no model representation to disambiguate. | — | unresolved | unresolved | no | 1 | **absent** | direct_human |
| **CAND-14** TLR3 / poly(I:C) | unresolved | None that can be stated. | — | unresolved | unresolved | no | 1 | **absent** | none_cited |

## Candidates

### CAND-01 — E2-only priming -> surface CD98

**Status:** `active` · **Compartment:** epithelial · **Perturbations required:** 0 · **Embryo required:** no

**Purpose.** Discriminate competing representations of epithelial CD98 regulation without embryo involvement.

**Experiment.** Run (or fix/stain at) the existing day 0-2 E2-only priming phase and measure epithelial surface CD98/CD9 protein.

**Ambiguity tested.** CD98-c versus BOTH CD98-a (v0.4) and CD98-b, which Gate 3a computes to be mutually indistinguishable in every recorded arm. So this measurement collapses the three CD98 readings to two classes; it does NOT separate CD98-a from CD98-b, and no available experiment does.

**Expected effect.** Opposite predictions: CD98-b (E_GP130_STAT3 or IN_HCG) predicts surface CD98 OFF under E2 alone; CD98-c (adds IN_E2) predicts ON. Verified from the committed model: E_PGR and E_GP130_STAT3 are false in all 32 assignments of e2_primed_maternal and IN_HCG is off.

**Model image (derived).**

* nodes present: `IN_E2`, `E_PGR`, `E_GP130_STAT3`, `E_CD98_CD9`
* reach: **maternal_and_downstream** (28 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* Gate-3 variants it touches: `CD98-a`, `CD98-b`, `CD98-c`, `GP130-b`

**Coupling adjudication (derived).**

* `E_CD98_CD9`: **ARTIFICIALLY_COUPLED** — alias class of 3: `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF`
* `E_GP130_STAT3`: **ARTIFICIALLY_COUPLED** — alias class of 3: `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF`
* `E_PGR`: **UNIDENTIFIED** — alias class of 5: `E_IHH`, `E_PGR`, `S_BMP2`, `S_NR2F2`, `S_PGR`
* `IN_E2`: **NOT_RULE_COLLAPSED**

**Proximal readouts (derived availability).**

* surface CD98/CD9: **NOT_IN_OBSERVATION_LAYER**

**Evidence.** `direct_human`

* REF-008 Dominguez 2010 [human epithelial;mouse blastocyst assay]

**Feasibility.** `existing_protocol_new_readout`

**Still uncertain.** Separating CD98-a from CD98-b needs an hCG arm (CAND-10), and IN_HCG is currently zero-degree, so that arm only becomes informative if CD98-b or CD98-c is adopted first. ADOC has no CD98/CD9 measurement at any timepoint and no E2-only transcriptome, so this is a NEW measurement, not a reanalysis. A transcript would not settle it: E_CD98_CD9 means surface availability and AGENTS.md separates expression from node activity.

### CAND-02 — LIF neutralisation -> pSTAT3

**Status:** `active` · **Compartment:** epithelial · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Separate extracellular LIF availability from common GP130/STAT3 pathway activity.

**Experiment.** Neutralising anti-LIF (or LIFR blockade) during the maternal phase; read pSTAT3 and downstream epithelial receptive markers.

**Ambiguity tested.** E_LIF, E_GP130_STAT3 and E_CD98_CD9 are one rule-induced class, so anti-LIF, STAT3 inhibition and CD98 knockdown are a single intervention in v0.4. Both E_LIF and E_GP130_STAT3 are adjudicated ARTIFICIALLY_COUPLED.

**Expected effect.** If pSTAT3 survives LIF neutralisation, the asserted identity E_GP130_STAT3 = E_LIF is false and a second GP130 ligand is required. Marwood 2009 shows IL-11 and LIF have non-interchangeable downstream effects in human endometrial epithelium.

**Model image (derived).**

* nodes present: `E_LIF`, `E_GP130_STAT3`, `E_CD98_CD9`
* reach: **maternal_and_downstream** (5 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* Gate-3 variants it touches: `CD98-a`, `CD98-b`, `CD98-c`, `GP130-b`

**Coupling adjudication (derived).**

* `E_CD98_CD9`: **ARTIFICIALLY_COUPLED** — alias class of 3: `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF`
* `E_GP130_STAT3`: **ARTIFICIALLY_COUPLED** — alias class of 3: `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF`
* `E_LIF`: **ARTIFICIALLY_COUPLED** — alias class of 3: `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF`

**Proximal readouts (derived availability).**

* pSTAT3: **NOT_IN_OBSERVATION_LAYER**
* surface CD98/CD9: **NOT_IN_OBSERVATION_LAYER**
* ITGA2: **NOT_IN_OBSERVATION_LAYER**

**Evidence.** `direct_human`

* REF-072 Marwood 2009 [human]
* REF-036 Cullinan 1996 [human]
* REF-038 Chung 2016 [human cell models]

**Feasibility.** `new_reagent_standard`

**Still uncertain.** Whether LIFR blockade and LIF neutralisation are separable in ADOC. The model has no IL11 node, so a negative result constrains but does not identify the alternative ligand.

### CAND-03 — IL-11 exposure with LIF neutralised

**Status:** `active` · **Compartment:** epithelial · **Perturbations required:** 2 · **Embryo required:** no

**Purpose.** Separate IL11-driven from LIF-driven GP130/STAT3 activity.

**Experiment.** Recombinant IL-11 exposure combined with LIF neutralisation; read pSTAT3, ITGA2, surface CD98.

**Ambiguity tested.** Same alias as CAND-02, plus whether the GP130-b variant (E_GP130_STAT3 = E_LIF or X_IL11) is warranted.

**Expected effect.** Marwood 2009: IL-11 stimulates trophoblast attachment where LIF does not, and alpha2beta1 blockade reduces the LIF but not the IL-11 collagen-IV response -- both downstream of STAT3. GP130-b breaks the ligand/pathway alias but does NOT represent that divergence.

**Model image (derived).**

* nodes present: `E_LIF`, `E_GP130_STAT3`
* concepts without a node: IL11 ligand availability -- no model node exists (GP130-b would add X_IL11 as a free experimental input)
* reach: **maternal_and_downstream** (5 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* Gate-3 variants it touches: `CD98-a`, `CD98-b`, `CD98-c`, `GP130-b`

**Coupling adjudication (derived).**

* `E_GP130_STAT3`: **ARTIFICIALLY_COUPLED** — alias class of 3: `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF`
* `E_LIF`: **ARTIFICIALLY_COUPLED** — alias class of 3: `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF`

**Proximal readouts (derived availability).**

* pSTAT3: **NOT_IN_OBSERVATION_LAYER**
* ITGA2: **NOT_IN_OBSERVATION_LAYER**
* surface CD98/CD9: **NOT_IN_OBSERVATION_LAYER**

**Evidence.** `direct_human`

* REF-072 Marwood 2009 [human]
* REF-064 Tanaka 2001 [human]

**Feasibility.** `new_reagent_standard`

**Still uncertain.** Two perturbations, so it does not fit a one-perturbation budget. Do not equate endogenous stromal IL11, epithelial exposure to IL11, and a recombinant ligand input.

### CAND-04 — STAT3 inhibition

**Status:** `active` · **Compartment:** epithelial · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Intervene downstream of LIF/IL11 to distinguish ligand-specific from common-pathway effects.

**Experiment.** Selective STAT3 inhibition in a defined compartment; read pSTAT3 for target engagement plus epithelial receptive markers.

**Ambiguity tested.** Same alias class as CAND-02. Less specific than ligand perturbation because it collapses every upstream signal onto one node.

**Expected effect.** Loss of the epithelial receptive program if the GP130/STAT3 arm is required. Mouse genetics (Pawar 2013, Hiraoka 2020) separate epithelial and stromal STAT3 roles; the model has only the epithelial one.

**Model image (derived).**

* nodes present: `E_GP130_STAT3`
* concepts without a node: stromal STAT3 -- NO model node exists (there is no S_STAT3); the seed proposal named one
* reach: **maternal_and_downstream** (3 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* Gate-3 variants it touches: `CD98-a`, `CD98-b`, `CD98-c`, `GP130-b`

**Coupling adjudication (derived).**

* `E_GP130_STAT3`: **ARTIFICIALLY_COUPLED** — alias class of 3: `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF`

**Proximal readouts (derived availability).**

* pSTAT3: **NOT_IN_OBSERVATION_LAYER**
* surface CD98/CD9: **NOT_IN_OBSERVATION_LAYER**
* PAEP: in_observation_map

**Evidence.** `transferred_only`

* REF-030 Pawar 2013 [mouse]
* REF-031 Hiraoka 2020 [mouse]

**Feasibility.** `new_reagent_standard`

**Still uncertain.** Compartment selectivity of a small-molecule STAT3 inhibitor in a two-channel chip is unproven. The model cannot represent stromal STAT3 at all, so a stromal effect would be uninterpretable.

### CAND-05 — Hormone cocktail minus cAMP

**Status:** `active` · **Compartment:** stromal · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Determine the contribution of the cAMP arm of the decidualization protocol.

**Experiment.** Standard maternal HT condition with cAMP omitted; read stromal decidual markers.

**Ambiguity tested.** IN_cAMP and S_PKA are one class, both re-adjudicated ARTIFICIALLY_COUPLED on 2026-09-16: the model asserts cAMP acts only through PKA.

**Expected effect.** Reduced but not abolished decidualization. Kusama 2013 shows PKA inhibition attenuates rather than abolishes, and an EPAC-only arm is inert -- i.e. a graded potentiator, which Boolean logic cannot represent.

**Model image (derived).**

* nodes present: `IN_cAMP`, `S_PKA`, `S_DECIDUALIZED`, `S_PRL`, `S_IGFBP1`
* concepts without a node: EPAC/RAP1 -- deliberately NOT a model node; a rate-free Boolean model cannot express potentiation
* reach: **maternal_and_downstream** (11 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* Gate-3 variants it touches: `IGFBP1-fb`

**Coupling adjudication (derived).**

* `IN_cAMP`: **ARTIFICIALLY_COUPLED** — alias class of 2: `IN_cAMP`, `S_PKA`
* `S_DECIDUALIZED`: **BIOLOGICALLY_COLLAPSED** — alias class of 6: `OUT_STROMAL_DECIDUALIZED`, `S_DECIDUALIZED`, `S_IGFBP1`, `S_PRL`, `S_SPP1`, `S_TAZ_ECM`
* `S_IGFBP1`: **ARTIFICIALLY_COUPLED** — alias class of 6: `OUT_STROMAL_DECIDUALIZED`, `S_DECIDUALIZED`, `S_IGFBP1`, `S_PRL`, `S_SPP1`, `S_TAZ_ECM`
* `S_PKA`: **ARTIFICIALLY_COUPLED** — alias class of 2: `IN_cAMP`, `S_PKA`
* `S_PRL`: **ARTIFICIALLY_COUPLED** — alias class of 6: `OUT_STROMAL_DECIDUALIZED`, `S_DECIDUALIZED`, `S_IGFBP1`, `S_PRL`, `S_SPP1`, `S_TAZ_ECM`

**Proximal readouts (derived availability).**

* PRL: in_observation_map
* IGFBP1: in_observation_map

**Evidence.** `direct_human`

* REF-073 Kusama 2013 [human]
* REF-061 Tamura 2014 [human]

**Feasibility.** `existing_protocol_new_readout`

**Still uncertain.** A partial effect is the predicted outcome and the Boolean model cannot distinguish 'attenuated' from 'abolished'. This may be evidence for a rate layer rather than a topology change.

### CAND-06 — SMO antagonist -> stromal NR2F2/HAND2/BMP2

**Status:** `active` · **Compartment:** stromal · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Test the epithelial PGR/IHH -> stromal Hedgehog reception -> NR2F2/HAND2/BMP2 axis.

**Experiment.** SMO antagonist (or PTCH1/GLI1 knockdown) in the stromal compartment; read PTCH1, GLI1, NR2F2, HAND2, BMP2.

**Ambiguity tested.** E_PGR, S_PGR, E_IHH, S_NR2F2 and S_BMP2 are a five-member class: PGR activity, IHH availability and stromal reception are one intervention.

**Expected effect.** If Hedgehog reception is required, SMO blockade should lower stromal NR2F2 and BMP2 without changing epithelial PGR. Inserting a pass-through reception node is structurally INERT (35->35) -- it only helps if it carries an independently measurable state.

**Model image (derived).**

* nodes present: `E_IHH`, `S_NR2F2`, `S_BMP2`, `S_HAND2`, `E_PGR`, `S_PGR`
* concepts without a node: stromal PTCH1/SMO/GLI reception state -- NO model node; GAP-014
* reach: **maternal_and_downstream** (29 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* Gate-3 variants it touches: `HH-reception`

**Coupling adjudication (derived).**

* `E_IHH`: **ARTIFICIALLY_COUPLED** — alias class of 5: `E_IHH`, `E_PGR`, `S_BMP2`, `S_NR2F2`, `S_PGR`
* `E_PGR`: **UNIDENTIFIED** — alias class of 5: `E_IHH`, `E_PGR`, `S_BMP2`, `S_NR2F2`, `S_PGR`
* `S_BMP2`: **ARTIFICIALLY_COUPLED** — alias class of 5: `E_IHH`, `E_PGR`, `S_BMP2`, `S_NR2F2`, `S_PGR`
* `S_HAND2`: **NOT_RULE_COLLAPSED**
* `S_NR2F2`: **ARTIFICIALLY_COUPLED** — alias class of 5: `E_IHH`, `E_PGR`, `S_BMP2`, `S_NR2F2`, `S_PGR`
* `S_PGR`: **UNIDENTIFIED** — alias class of 5: `E_IHH`, `E_PGR`, `S_BMP2`, `S_NR2F2`, `S_PGR`

**Proximal readouts (derived availability).**

* PTCH1: **NOT_IN_OBSERVATION_LAYER**
* GLI1: **NOT_IN_OBSERVATION_LAYER**
* NR2F2: **NOT_IN_OBSERVATION_LAYER**
* HAND2: **NOT_IN_OBSERVATION_LAYER**
* BMP2: in_observation_map

**Evidence.** `human_plus_transferred`

* REF-075 Wei 2010 [human]
* REF-025 Franco 2010 [mouse]
* REF-026 Kurihara 2007 [mouse]
* REF-027 Lee 2007 [mouse]

**Feasibility.** `new_reagent_standard`

**Still uncertain.** GAP-014: human EXPRESSION and pharmacological response exist (REF-075, Wei 2010), but the NECESSITY test does not. The causal chain rests substantially on mouse uterine genetics.

### CAND-07 — BMP signalling inhibition

**Status:** `active` · **Compartment:** stromal · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Interrogate the stromal decidualization branch downstream of the IHH/NR2F2 axis.

**Experiment.** BMP receptor / SMAD inhibition during decidualization; read decidual markers.

**Ambiguity tested.** Whether BMP2 acts through a receptor/SMAD step distinct from the PGR/IHH/NR2F2 alias it currently collapses into.

**Expected effect.** Reduced decidualization if the BMP arm is required. Mouse Bmp2 conditional deletion abolishes the decidual response (Lee 2007).

**Model image (derived).**

* nodes present: `S_BMP2`, `S_DECIDUALIZED`, `S_PRL`, `S_IGFBP1`
* concepts without a node: BMP receptor / SMAD state -- candidate node, measured as structurally inert
* reach: **maternal_and_downstream** (10 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* Gate-3 variants it touches: `IGFBP1-fb`

**Coupling adjudication (derived).**

* `S_BMP2`: **ARTIFICIALLY_COUPLED** — alias class of 5: `E_IHH`, `E_PGR`, `S_BMP2`, `S_NR2F2`, `S_PGR`
* `S_DECIDUALIZED`: **BIOLOGICALLY_COLLAPSED** — alias class of 6: `OUT_STROMAL_DECIDUALIZED`, `S_DECIDUALIZED`, `S_IGFBP1`, `S_PRL`, `S_SPP1`, `S_TAZ_ECM`
* `S_IGFBP1`: **ARTIFICIALLY_COUPLED** — alias class of 6: `OUT_STROMAL_DECIDUALIZED`, `S_DECIDUALIZED`, `S_IGFBP1`, `S_PRL`, `S_SPP1`, `S_TAZ_ECM`
* `S_PRL`: **ARTIFICIALLY_COUPLED** — alias class of 6: `OUT_STROMAL_DECIDUALIZED`, `S_DECIDUALIZED`, `S_IGFBP1`, `S_PRL`, `S_SPP1`, `S_TAZ_ECM`

**Proximal readouts (derived availability).**

* PRL: in_observation_map
* IGFBP1: in_observation_map
* BMP2: in_observation_map

**Evidence.** `transferred_only`

* REF-027 Lee 2007 [mouse]
* REF-026 Kurihara 2007 [mouse]

**Feasibility.** `new_reagent_standard`

**Still uncertain.** Adding a BMP-SMAD pass-through node was MEASURED to be structurally inert and does not resolve the upstream alias. The experiment may still be biologically informative, but it must not be claimed to decouple the model.

### CAND-08 — PC6 knockdown -> alpha-DG-N shedding

**Status:** `active` · **Compartment:** epithelial · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Separate PC6 enzyme activity from its DAG1 cleavage product.

**Experiment.** PCSK5/PC6 knockdown; measure full-length and N-terminally cleaved alpha-dystroglycan.

**Ambiguity tested.** E_PC6 = E_DAG1_CLEAVED asserts the enzyme IS its product; both are adjudicated ARTIFICIALLY_COUPLED and the identity is directly contradicted by Heng 2015.

**Expected effect.** PC6 knockdown should reduce alpha-DG-N shedding while leaving substrate abundance; Heng 2015 performed both arms in human cells.

**Model image (derived).**

* nodes present: `E_PC6`, `E_DAG1_CLEAVED`, `E_DAG1_FULL`
* concepts without a node: cleavage-resistant DAG1 substrate -- a laboratory construct, not a state ADOC varies
* reach: **maternal_and_downstream** (4 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* Gate-3 variants it touches: `PC6-b`

**Coupling adjudication (derived).**

* `E_DAG1_CLEAVED`: **ARTIFICIALLY_COUPLED** — alias class of 9: `E_ANXA2_ACTIN`, `E_DAG1_CLEAVED`, `E_HBEGF`, `E_ITGAVB3_5`, `E_MUC1_SLEX`, `E_PAEP`, `E_PC6`, `E_SECRETORY_STATE`, `E_SPP1_EXPR`
* `E_DAG1_FULL`: **UNIDENTIFIED** — alias class of 3: `E_DAG1_FULL`, `E_MUC1_BARRIER`, `E_PODXL`
* `E_PC6`: **ARTIFICIALLY_COUPLED** — alias class of 9: `E_ANXA2_ACTIN`, `E_DAG1_CLEAVED`, `E_HBEGF`, `E_ITGAVB3_5`, `E_MUC1_SLEX`, `E_PAEP`, `E_PC6`, `E_SECRETORY_STATE`, `E_SPP1_EXPR`

**Proximal readouts (derived availability).**

* PC6/PCSK5: **NOT_IN_OBSERVATION_LAYER**
* alpha-dystroglycan full-length: **NOT_IN_OBSERVATION_LAYER**
* alpha-DG N-terminal: **NOT_IN_OBSERVATION_LAYER**

**Evidence.** `direct_human`

* REF-011 Heng 2015 [human]
* REF-010 Heng 2011 [human]

**Feasibility.** `new_reagent_standard`

**Still uncertain.** The separation is required by evidence, but no free PC6 determinant exists; the cleavage-resistant arm would supply one and it is not a physiological state.

### CAND-09 — HAND2 loss

**Status:** `active` · **Compartment:** stromal · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Test the stromal HAND2 veto on epithelial proliferation, one of the few non-collapsed stromal nodes.

**Experiment.** siHAND2 in the stromal compartment during HT; read stromal decidual markers and epithelial proliferation state.

**Ambiguity tested.** S_HAND2 is NOT_RULE_COLLAPSED -- it has its own Boolean function, so this perturbation already has a distinct model image, unlike most stromal targets.

**Expected effect.** Loss of the HAND2 veto should de-repress epithelial mitogenic signalling. Direction only: the magnitude of epithelial collapse is a hard Boolean consequence of a veto with no held-out measurement behind it.

**Model image (derived).**

* nodes present: `IN_HAND2_LOSS`, `S_HAND2`, `S_FGF_MITOGENIC`, `E_ESTROGENIC_PROLIFERATION`
* reach: **maternal_and_downstream** (4 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* already implemented as: `hand2_loss_after_ht`

**Coupling adjudication (derived).**

* `E_ESTROGENIC_PROLIFERATION`: **NOT_RULE_COLLAPSED**
* `IN_HAND2_LOSS`: **NOT_RULE_COLLAPSED**
* `S_FGF_MITOGENIC`: **NOT_RULE_COLLAPSED**
* `S_HAND2`: **NOT_RULE_COLLAPSED**

**Proximal readouts (derived availability).**

* HAND2: **NOT_IN_OBSERVATION_LAYER**
* PRL: in_observation_map
* IGFBP1: in_observation_map

**Evidence.** `human_plus_transferred`

* REF-062 Murata 2019 [human]
* REF-025 Franco 2010 [mouse]

**Feasibility.** `new_reagent_standard`

**Still uncertain.** Already encoded as a boundary input (IN_HAND2_LOSS) rather than as a mechanism, so the experiment tests the consequence of the veto, not its mechanism.

### CAND-10 — hCG challenge

**Status:** `active` · **Compartment:** epithelial · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Give a declared but unread input a model image, and test embryo-independent hCG effects on the epithelium.

**Experiment.** Recombinant hCG exposure during the maternal phase; read surface CD98 and epithelial receptive markers.

**Ambiguity tested.** IN_HCG is declared but ZERO-DEGREE -- read by no rule -- so it currently has no model image at all. The CD98-b/c and CDH1-b/c variants would give it one.

**Expected effect.** Dominguez 2010 names hCG among the inducers of epithelial CD98. If CD98-b/c are adopted, hCG becomes readable on CD98 without progestin.

**Model image (derived).**

* nodes present: `IN_HCG`, `E_CD98_CD9`, `E_CDH1_APICAL`
* **zero-degree (declared, read by no rule): `IN_HCG`** — the model predicts no effect
* reach: **maternal_and_downstream** (3 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* Gate-3 variants it touches: `CD98-a`, `CD98-b`, `CD98-c`, `CDH1-b`, `CDH1-c`

**Coupling adjudication (derived).**

* `E_CD98_CD9`: **ARTIFICIALLY_COUPLED** — alias class of 3: `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF`
* `E_CDH1_APICAL`: **ARTIFICIALLY_COUPLED** — alias class of 2: `E_CDH1_APICAL`, `IN_EMBRYO_CONTACT`
* `IN_HCG`: **NOT_RULE_COLLAPSED**

**Proximal readouts (derived availability).**

* surface CD98/CD9: **NOT_IN_OBSERVATION_LAYER**
* apical CDH1: **NOT_IN_OBSERVATION_LAYER**
* PAEP: in_observation_map

**Evidence.** `direct_human`

* REF-008 Dominguez 2010 [human epithelial;mouse blastocyst assay]
* REF-059 Jin 2025 [human]
* REF-070 Wang 2023 [human;mouse]

**Feasibility.** `new_reagent_standard`

**Still uncertain.** CONDITIONAL VALUE: the generator confirms this perturbation moves no maternal node in any recorded arm, because its input is zero-degree. It becomes informative only if the topology gains an image for it. REF-059 (Jin 2025) routes hCG through epithelial PGF2alpha to a stromal readout, and REF-069 (Schatz 1986) records progestin SUPPRESSING that epithelial source -- a registered unresolved conflict.

### CAND-11 — Anti-SPP1 -> attachment

**Status:** `deprioritised` · **Compartment:** interface · **Perturbations required:** 1 · **Embryo required:** yes

**Purpose.** Interrogate one terminal embryo-maternal adhesion route.

**Experiment.** Neutralising anti-SPP1 during the embryo challenge; attachment fraction as the endpoint.

**Ambiguity tested.** Separates the two terminal interface relays, which the hormone-treated arm alone cannot: under IN_ANTI_SPP1 the endpoint stops depending on the SPP1 relay.

**Expected effect.** Reduced attachment if the SPP1 route is non-redundant. The relay pair is otherwise a one-dimensional ridge.

**Model image (derived).**

* nodes present: `IN_ANTI_SPP1`, `X_SPP1_LUMEN_FREE`, `X_ADHESION_ROUTE_SPP1`, `X_INTERFACE_SPP1_RELAY`, `X_INTERFACE_REDUNDANT_RELAY`
* reach: **maternal_and_downstream** (1 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)
* already implemented as: `anti_spp1_after_ht`, `anti_spp1_washout`

**Coupling adjudication (derived).**

* `IN_ANTI_SPP1`: **NOT_RULE_COLLAPSED**
* `X_ADHESION_ROUTE_SPP1`: **NOT_RULE_COLLAPSED**
* `X_INTERFACE_REDUNDANT_RELAY`: **NOT_RULE_COLLAPSED**
* `X_INTERFACE_SPP1_RELAY`: **NOT_RULE_COLLAPSED**
* `X_SPP1_LUMEN_FREE`: **NOT_RULE_COLLAPSED**

**Proximal readouts (derived availability).**

* attachment fraction: **NOT_IN_OBSERVATION_LAYER**

**Evidence.** `direct_human`

* REF-007 Apparao 2001 [human]
* REF-017 Wang 2018 [human]

**Feasibility.** `existing_protocol_new_readout`

**Still uncertain.** Its identifiability target is the relay abstraction now reinterpreted as unresolved terminal interface/penetrance variables and a candidate for removal. If the relays go, the parameters it uniquely identifies cease to exist.

### CAND-12 — XAV939 dropout

**Status:** `active` · **Compartment:** both · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Test whether the WNT/tankyrase inhibitor in the standard cocktail has any maternal effect the model can see.

**Experiment.** Standard HT condition with XAV939 omitted; read epithelial secretory and stromal decidual markers.

**Ambiguity tested.** IN_XAV939 is ZERO-DEGREE: present in every HT protocol and read by no rule, so the model predicts XAV939 does nothing. Any measured effect is unrepresented.

**Expected effect.** The model predicts NO change, because the input reaches nothing. An observed change would falsify the current encoding and motivate the E_AXIN gate the unused scenario already sketches.

**Model image (derived).**

* nodes present: `IN_XAV939`, `E_SECRETORY_STATE`, `E_PAEP`
* **zero-degree (declared, read by no rule): `IN_XAV939`** — the model predicts no effect
* concepts without a node: E_AXIN -- referenced by the phase1b_xav939_required scenario override but ABSENT from the network
* reach: **maternal_and_downstream** (16 maternal node(s) downstream, terminal: `OUT_MATERNAL_ADHESION_COMPETENCE`, `OUT_STABLE_ADHESION`)

**Coupling adjudication (derived).**

* `E_PAEP`: **BIOLOGICALLY_COLLAPSED** — alias class of 9: `E_ANXA2_ACTIN`, `E_DAG1_CLEAVED`, `E_HBEGF`, `E_ITGAVB3_5`, `E_MUC1_SLEX`, `E_PAEP`, `E_PC6`, `E_SECRETORY_STATE`, `E_SPP1_EXPR`
* `E_SECRETORY_STATE`: **BIOLOGICALLY_COLLAPSED** — alias class of 9: `E_ANXA2_ACTIN`, `E_DAG1_CLEAVED`, `E_HBEGF`, `E_ITGAVB3_5`, `E_MUC1_SLEX`, `E_PAEP`, `E_PC6`, `E_SECRETORY_STATE`, `E_SPP1_EXPR`
* `IN_XAV939`: **NOT_RULE_COLLAPSED**

**Proximal readouts (derived availability).**

* PAEP: in_observation_map
* IGFBP1: in_observation_map
* PRL: in_observation_map

**Evidence.** `none_cited`

* no reference cited

**Feasibility.** `existing_protocol_new_readout`

**Still uncertain.** CONDITIONAL VALUE: the generator confirms this perturbation moves no maternal node in any recorded arm, because its input is zero-degree. It becomes informative only if the topology gains an image for it. A null-prediction experiment: informative only if it fails. No primary reference in the corpus supports a specific XAV939 direction in human endometrium.

### CAND-13 — COX-2 / PGE2 pathway perturbation

**Status:** `evidence_gap` · **Compartment:** unresolved · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Proposed from experimental planning material; assessed here rather than promoted.

**Experiment.** Not specified -- would require a COX-2 inhibitor arm with prostaglandin readouts.

**Ambiguity tested.** None that can be stated: there is no model representation to disambiguate.

**Expected effect.** Not assertable from this corpus.

**Model image (derived).**

* nodes present: none
* concepts without a node: COX-2/PTGS2 and PGE2 -- no model node, no catalogued target
* reach: **no_model_image** (0 maternal node(s) downstream)

**Proximal readouts (derived availability).**

* none specified

**Evidence.** `direct_human`

* REF-069 Schatz 1986 [human]

**Feasibility.** `not_scoped`

**Still uncertain.** ZERO occurrences of COX-2/PTGS2/PGE2 anywhere in the reference, evidence or node-candidate layers. The nearest evidence is REF-069 (Schatz 1986), which measures PGF2alpha -- NOT PGE2 -- and is registered as an unresolved CONTRADICTION against REF-059. Do not add topology for this.

### CAND-14 — TLR3 / poly(I:C)

**Status:** `evidence_gap` · **Compartment:** unresolved · **Perturbations required:** 1 · **Embryo required:** no

**Purpose.** Proposed from experimental planning material; assessed here rather than promoted.

**Experiment.** Not specified -- innate/inflammatory activation.

**Ambiguity tested.** None that can be stated.

**Expected effect.** Not assertable from this corpus.

**Model image (derived).**

* nodes present: none
* concepts without a node: TLR3 and innate immune signalling -- no model node, no catalogued target
* reach: **no_model_image** (0 maternal node(s) downstream)

**Proximal readouts (derived availability).**

* none specified

**Evidence.** `none_cited`

* no reference cited

**Feasibility.** `not_scoped`

**Still uncertain.** ZERO occurrences of TLR3 or poly(I:C) anywhere in the evidence layer. It would also move the system outside the receptive-state context the DT is built for. Do not create an inflammatory branch to accommodate it.

## Regeneration diagnostics

Things the generator found wrong or worth knowing, this run:

* CAND-01: proximal readout(s) not in the observation layer -- surface CD98/CD9
* CAND-02: proximal readout(s) not in the observation layer -- pSTAT3, surface CD98/CD9, ITGA2
* CAND-03: proximal readout(s) not in the observation layer -- pSTAT3, ITGA2, surface CD98/CD9
* CAND-04: proximal readout(s) not in the observation layer -- pSTAT3, surface CD98/CD9
* CAND-04: supported only by non-human evidence
* CAND-06: proximal readout(s) not in the observation layer -- PTCH1, GLI1, NR2F2, HAND2
* CAND-07: supported only by non-human evidence
* CAND-08: proximal readout(s) not in the observation layer -- PC6/PCSK5, alpha-dystroglycan full-length, alpha-DG N-terminal
* CAND-09: proximal readout(s) not in the observation layer -- HAND2
* CAND-10: interrogates zero-degree input(s) IN_HCG -- declared but read by no rule, so the model predicts no effect
* CAND-10: proximal readout(s) not in the observation layer -- surface CD98/CD9, apical CDH1
* CAND-12: interrogates zero-degree input(s) IN_XAV939 -- declared but read by no rule, so the model predicts no effect
* CAND-12: ACTIVE but cites no reference

### Artificially coupled nodes with no active discriminating candidate

9 node(s) are adjudicated `ARTIFICIALLY_COUPLED` but no active candidate interrogates them:

`E_ANXA2_ACTIN`, `E_HBEGF`, `E_ITGAVB3_5`, `E_MUC1_SLEX`, `IN_EMBRYO_CONTACT`, `OUT_EPITHELIAL_RECEPTIVE`, `OUT_STROMAL_DECIDUALIZED`, `S_SPP1`, `S_TAZ_ECM`

