# ADOC MaBoSS model for non-hormonal contraceptive discovery

The model should not be a flat collection of receptivity genes. I would build it as a **coupled epithelial–stromal regulatory network connected by extracellular signals**, with three explicit goals:

1. Reproduce the transition from the untreated ADOC state to the hormone-conditioned receptive state.
2. Predict **maternal adhesion competence**, even before an embryo is added.
3. Identify interventions that reduce adhesion competence while preserving epithelial barrier function, stromal decidualization, viability, and reversibility.

For the first MaBoSS version, I recommend one combined network with prefixes:

* `E_`: epithelial nodes
* `S_`: stromal nodes
* `X_`: extracellular or intercompartmental nodes
* `IN_`: experimental inputs
* `OUT_`: model phenotypes

Later, PhysiBoSS2 can convert the epithelial and stromal networks into separate cell agents coupled through diffusing substrates, flow and membrane transport. That is consistent with the planned implantation-twin architecture in IMPLANT-MOD and with the intended MaBoSS–PhysiBoSS2 progression.  PhysiBoSS2 was specifically designed to couple MaBoSS intracellular networks to cell-level mechanics, secretion, uptake and microenvironmental diffusion. ([Institut Curie][1])

## 1. Experimental states that the model must reproduce

A critical point is that the published ADOC “hormonal treatment” is **not simply estrogen plus progesterone**. It is a staged four-component protocol:

1. Two days of E2.
2. Four additional days of E2 + MPA + cAMP + XAV939.

Therefore, Codex must not collapse this into a single `HORMONES = ON` input. E2, progestin, cAMP and WNT/tankyrase inhibition must be independently controllable. Otherwise, the model will not distinguish hormonal from non-hormonal mechanisms. 

| State                    | Inputs                                      | Expected epithelial state                                                          | Expected stromal state                                                     | Adhesion constraint      |
| ------------------------ | ------------------------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------ |
| Basal ADOC               | All treatment inputs OFF                    | Luminal-like; `VTCN1`, `IL6`, `CDH6`, `THBS1`, `MMP7`; relatively more ciliated    | Mesenchymal/proliferative; `MMP11`, `ECM1`, `COL3A1/COL5A1`                | Very low                 |
| E2 priming               | `IN_E2=1`                                   | ESR1-dependent priming and proliferation; induction of progesterone responsiveness | Estrogen-responsive, not yet fully decidual                                | Low                      |
| Receptive ADOC           | `E2=1`, `PROGESTIN=1`, `cAMP=1`, `XAV939=1` | `PAEP`, `SPP1`, `DPP4`, `SCGB2A1`, `SCGB1D2`, `CEACAM5/6`; fewer ciliated cells    | `BMP2`, `DKK1`, `KDR`, `IL11`, `PRL`, `IGFBP1`; rounded decidual phenotype | Increased                |
| Receptive + mifepristone | Same, plus `MIFEPRISTONE=1`                 | PGR-dependent receptive programme reduced                                          | Decidual programme reduced                                                 | Reduced                  |
| Receptive + candidate    | Same, plus candidate-specific perturbation  | Ideally selective loss of adhesion competence                                      | Decidualization largely preserved                                          | Reduced without toxicity |
| Washout                  | Candidate OFF                               | Return toward receptive baseline                                                   | Return toward receptive baseline                                           | Recovery expected        |

The ADOC experiment observed stable attachment in 9 of 19 hormone-treated blastocysts, none of 12 untreated blastocysts and 1 of 8 blastocysts exposed to 10 μM mifepristone. These should be treated as **binomial calibration data**, not as exact target probabilities.  The paper also showed hormone-dependent epithelial secretory differentiation, stromal decidualization and human blastocyst adhesion through polar trophectoderm. ([PubMed][2])

The untreated chip should be described as the **basal ADOC state**, not assumed to be a perfect physiological proliferative-phase endometrium.

---

# 2. Recommended core MaBoSS node set

This is the model I would implement first. It should produce approximately 80–110 nodes after complexes and redundant genes are grouped into activity nodes.

## 2.1 Experimental and environmental inputs

```yaml
inputs:
  - IN_E2
  - IN_PROGESTIN
  - IN_cAMP
  - IN_XAV939
  - IN_MIFEPRISTONE
  - IN_ANTI_SPP1
  - IN_INTEGRIN_BLOCK
  - IN_LIF_BLOCK
  - IN_FAK_BLOCK
  - IN_EMBRYO_PRESENT
  - IN_TROPHECTODERM_COMPETENT
  - IN_GLUCOSE_SUFFICIENT
  - IN_GLUTAMINE_SUFFICIENT
  - IN_OXYGEN_LOW
  - IN_INFLAMMATORY_SIGNAL
  - IN_TGFB1_HIGH
  - IN_FLOW
  - IN_WASHOUT
```

Use generic `IN_PROGESTIN` in the logical model, with metadata recording whether the compound is MPA or progesterone. This makes later translation to physiological P4 possible.

`IN_XAV939` should act through `TNKS/AXIN/CTNNB1`, not as an unexplained “receptivity” input.

---

## 2.2 Epithelial hormone-response and secretory module

```yaml
epithelial_hormone_response:
  - E_ESR1
  - E_ESR2
  - E_PGR
  - E_GATA2
  - E_SOX17
  - E_FOXA2
  - E_IHH
  - E_SGK1
  - E_KLF5
  - E_ELF3
  - E_LIF
  - E_LIFR
  - E_IL6ST
  - E_JAK1
  - E_STAT3
  - E_TNKS
  - E_AXIN
  - E_CTNBB1
  - E_ERK
  - E_AKT
```

### Readout or marker nodes

```yaml
epithelial_secretory_markers:
  - E_PAEP
  - E_SPP1_EXPR
  - E_DPP4
  - E_SCGB2A1
  - E_SCGB1D2
  - E_CEACAM5
  - E_CEACAM6

epithelial_basal_markers:
  - E_VTCN1
  - E_IL6
  - E_CDH6
  - E_THBS1
  - E_MMP7
```

`PAEP`, secretoglobins and CEACAMs are primarily state markers. They should initially have few or no outgoing regulatory edges. `SPP1`, by contrast, should be both a marker and a functional extracellular ligand.

The ADOC scRNA-seq data directly support the hormone-dependent epithelial transition and the stromal `BMP2–DKK1–KDR–IL11` programme.  Independent human single-cell atlases also show that opening of the implantation window is an abrupt epithelial transition accompanied by stromal decidualization. Recent spatial work highlights epithelial `SGK1`, `KLF5` and `ELF3` and stromal `NR2F1` and `CEBPD`. ([Nature][3])

---

## 2.3 Stromal decidualization module

```yaml
stromal_hormone_camp:
  - S_ESR1
  - S_PGR
  - S_NCOA2
  - S_PKA
  - S_EPAC
  - S_RAP1
  - S_CREB1
  - S_CEBPB
  - S_GATA2
  - S_FOXO1
  - S_HOXA10

stromal_ihh_bmp_wnt:
  - S_PTCH1
  - S_SMO
  - S_GLI
  - S_NR2F2
  - S_HAND2
  - S_BMP2
  - S_BMPR
  - S_SMAD1_5
  - S_WNT4
  - S_CTNBB1
  - S_DKK1

stromal_cytokine_notch:
  - S_IL11
  - S_IL11RA
  - S_IL6ST
  - S_JAK1
  - S_STAT3
  - S_JAG1
  - S_NOTCH1
  - S_HES_HEY

stromal_decidual_outputs:
  - S_PRL
  - S_IGFBP1
  - S_FBLN1
  - S_DCN
  - S_TIMP3
  - S_IL15
  - S_FKBP5
  - S_KDR
  - S_VEGFA
```

The core decidualization backbone should be:

[
PGR/cAMP
\rightarrow PKA/CREB,\ CEBPB,\ FOXO1
\rightarrow PRL,\ IGFBP1
]

together with:

[
Epithelial\ IHH
\rightarrow Stromal\ PTCH/SMO/GLI
\rightarrow NR2F2
\rightarrow HAND2/BMP2
\rightarrow WNT4/\beta\text{-catenin}
\rightarrow FOXO1
]

BMP2–WNT4–β-catenin–FOXO1 is supported in primary human endometrial stromal cells, while human organotypic cocultures support hormone-responsive IHH–NR2F2–BMP2 signalling. ([PubMed][4]) Progesterone and cAMP should remain separate because they produce overlapping but non-identical decidual programmes. ([PubMed][5])

### Important FGF distinction

Do not use one generic `FGF` node. Include two branches:

```yaml
stromal_fgf:
  - S_FGF2
  - S_FGF7
  - S_FGF9
  - S_FGF18
  - E_FGFR2
  - E_FRS2_ERK
```

* `FGF9/FGF18` and related mitogenic FGFs can maintain estrogen-driven epithelial proliferation and oppose receptivity when not suppressed by HAND2.
* Recent human spatial data indicate that stromal `FGF2/FGF7 → epithelial FGFR2` can instead support epithelial differentiation around the opening of the window.

These apparently contradictory roles are likely ligand-, timing- and state-dependent. Codex should therefore create separate FGF nodes and mark their logic as an area requiring calibration, rather than forcing all FGF signalling to be positive or negative. ([Keio University][6])

---

## 2.4 Epithelial adhesion and glycocalyx module

This is the most important module for non-hormonal contraceptive discovery.

```yaml
epithelial_surface_adhesion:
  - E_SLC3A2_CD98
  - E_CD9
  - E_ANXA2
  - E_CDH1_APICAL
  - E_CTNND1
  - E_ITGAV
  - E_ITGB1
  - E_ITGB3
  - E_ITGB5
  - E_ITGB8
  - E_CD44
  - E_DAG1
  - E_DAG1_PROCESSED
  - E_PCSK5_6
  - E_TRO
  - E_TROAP
  - E_BYSL
  - E_LGALS1
  - E_LGALS3
  - E_BSG
  - E_HBEGF
  - E_EGFR
  - E_ERBB4
  - E_HAS2_HYALURONAN
  - E_SLEX_LIGAND

epithelial_antiadhesive_surface:
  - E_PODXL
  - E_MUC1_SURFACE
  - E_MUC1_RECEPTIVE_GLYCOFORM
  - E_DAG1_FULL_LENGTH
```

### High-value functional evidence

* `SLC3A2/CD98` and `CD9` are apical human endometrial receptivity factors, and experimental gain or loss altered blastocyst attachment in vitro. ([PubMed][7])
* `PODXL` is a strong negative regulator of human endometrial surface receptivity. Its downregulation permits attachment, whereas maintenance or overexpression inhibits attachment and penetration. ([PubMed][8])
* Cleavage of the N terminus of `DAG1` by `PCSK5/6` changes the human epithelial surface from antiadhesive to adhesive. ([PubMed][9])
* `ANXA2` supports endometrial adhesion through RHOA/F-actin regulation. ([FASEB Journal][10])
* A recent human study indicates that apical `CDH1–CDH1` homophilic binding can provide a major component of trophectoderm–epithelium adhesion. ([OUP Academic][11])
* `LGALS1`, `LGALS3`, `ITGB1`, `BSG` and `SPP1` emerged from paired human epithelial, stromal and trophectoderm transcriptomes as candidate embryo–endometrium interactions. ([OUP Academic][12])

### MUC1 must not be encoded as simply positive or negative

Human `MUC1` is hormonally induced and can form an antiadhesive barrier that is locally removed at embryo attachment. However, specific highly glycosylated MUC1 forms also provide ligands for embryonic L-selectin. Therefore, use separate nodes:

```yaml
E_MUC1_BARRIER
E_MUC1_SLEX_GLYCOFORM
E_MUC1_LOCAL_REMOVAL
```

Do not use a single `MUC1 = adhesion inhibitor` rule. ([PubMed][13])

---

## 2.5 SPP1–integrin–focal adhesion module

```yaml
spp1_module:
  - E_SPP1_EXPR
  - S_SPP1_EXPR
  - X_SPP1_LUMEN_TOTAL
  - X_SPP1_LUMEN_FREE
  - X_SPP1_BASAL
  - E_ITGAV_ITGB3
  - E_ITGAV_ITGB5
  - E_CD44

focal_adhesion:
  - E_PTK2_FAK
  - E_SRC
  - E_VAV
  - E_RAC1
  - E_RHOA
  - E_ROCK
  - E_PXN
  - E_VCL
  - E_TLN1
  - E_ACTIN_REMODELING
```

Anti-SPP1 must be represented as:

```text
IN_ANTI_SPP1 ┤ X_SPP1_LUMEN_FREE
```

It should **not** directly inhibit `E_SPP1_EXPR`. The antibody neutralizes extracellular ligand; it may leave SPP1 RNA unchanged or even induce compensatory expression.

A minimal rule is:

```text
X_SPP1_LUMEN_FREE =
    (E_SPP1_EXPR or S_SPP1_DIFFUSION)
    and not IN_ANTI_SPP1
```

SPP1-integrin signalling can activate FAK, SRC, PI3K, MAPK, cytoskeletal assembly and traction-generating adhesion. ([ScienceDirect][14]) However, SPP1 biology is not necessarily monotonic: decidual stromal cells also produce it, and excessive exogenous osteopontin has attenuated weak attachment or inhibited invasion in some implantation models. ([ScienceDirect][15])

Consequently:

> Anti-SPP1 is an excellent mechanistic calibration perturbation, but it is not yet justified as the final safest contraceptive mechanism.

---

## 2.6 Barrier, polarity and controlled epithelial remodelling

```yaml
epithelial_barrier:
  - E_TJP1
  - E_OCLN
  - E_CLDN4
  - E_F11R
  - E_EPCAM
  - E_CDH1_JUNCTIONAL
  - E_DSG2
  - E_RAB11A
  - E_IQGAP1
  - E_APICAL_POLARITY

epithelial_cilia:
  - E_FOXJ1
  - E_TPPP3
  - E_PIFO
  - E_CILIATED_STATE
```

The model needs three barrier phenotypes rather than one:

```yaml
outputs:
  - OUT_BARRIER_MATURE
  - OUT_BARRIER_REMODELED
  - OUT_BARRIER_DAMAGED
```

Hormonal treatment increased ADOC permeability while producing a receptive, viable epithelium. Therefore, modest barrier remodelling must not automatically be interpreted as toxicity. 

A safe candidate should ideally produce:

```text
OUT_BARRIER_DAMAGED = 0
OUT_EPITHELIAL_VIABILITY = 1
```

even if it alters `OUT_BARRIER_REMODELED`.

`miR-124-3p → IQGAP1` and epithelial polarity are useful extended nodes because excessive epithelial miR-124-3p impaired primary human trophectoderm attachment. ([PubMed][16])

---

## 2.7 ECM and matrix-remodelling module

```yaml
extracellular_matrix:
  - X_FN1
  - X_COL4A1_A2
  - X_LAMA1
  - X_LAMA2
  - X_LAMA4
  - X_LAMB1
  - X_LAMC1
  - X_NID1
  - X_NID2
  - X_FBLN1
  - X_FBLN2
  - X_MFAP5
  - X_DCN
  - X_VCAN
  - X_ECM1
  - X_THBS1
  - X_HYALURONAN

matrix_remodeling:
  - X_MMP2
  - X_MMP7
  - X_MMP9
  - X_MMP11
  - X_ADAMTS1
  - X_TIMP1
  - X_TIMP2
  - X_TIMP3
```

For ADOC adhesion, most of these are supporting or safety nodes. They become more central when the model is extended to INVADE and PhysiBoSS2.

Useful epithelial–stromal interactions identified in human receptive endometrium include:

* `FBLN1–MFAP5`
* `NID1–FBLN2`
* `LAMA1–FBLN2`
* `DAG1–LAMA2`
* `SPP1–ITGAV`
* `PDGFA–PDGFRA` ([OUP Academic][12])

---

# 3. Metabolic nodes and metabolites

Metabolites should not be treated as if they were ordinary genes. In MaBoSS, represent them as **availability or state nodes**. Later, PhysiBoSS2 can model their continuous production, consumption and diffusion.

## 3.1 Core metabolic nodes

```yaml
metabolic_inputs_states:
  - X_GLUCOSE_HIGH
  - X_GLUCOSE_LOW
  - X_LACTATE_HIGH
  - X_PYRUVATE
  - X_OXYGEN_LOW
  - X_ROS_HIGH
  - X_PGE2_HIGH
  - X_PGI2_HIGH
  - X_GLUTAMINE_HIGH
  - X_GLUTAMATE_HIGH
  - X_AKG_HIGH
  - X_ATP_LOW
  - X_PH_LOW

stromal_glycolysis:
  - S_SLC2A1_GLUT1
  - S_PFKFB3
  - S_HK2
  - S_PKM
  - S_LDHA
  - S_SLC16A3_MCT4
  - S_HIF1A
  - S_NCOA2
  - S_AMPK

stromal_glutaminolysis:
  - S_SLC1A5
  - S_GLS
  - S_GLUD1
  - S_AKG_METABOLISM

prostaglandins:
  - S_PLA2G2A
  - S_PLA2G4A
  - S_PTGS1
  - S_PTGS2
  - S_PTGES
  - S_PTGDS
  - S_PTGIS
  - S_PTGER2
  - S_PTGER4
  - S_PTGIR
```

Steroid receptor coactivator `NCOA2/SRC2 → PFKFB3` increases glycolytic flux during human stromal decidualization. ([PubMed][17]) Human decidualization also depends on glucose transport and glutamine–glutamate–α-ketoglutarate metabolism; αKG contributes both ATP production and epigenetic remodelling. ([PubMed][18])

PGE2 signalling through EP2/EP4 provides spatially regulated cAMP signals during decidualization, and endothelial-derived PGE2 and PGI2 can enhance decidualization under flow. ([PubMed][19])

## 3.2 Redox, autophagy and ferroptosis safety

```yaml
redox_safety:
  - S_NFE2L2_NRF2
  - S_HMOX1
  - S_SOD2
  - S_GPX3
  - S_GPX4
  - S_GCLC
  - S_SLC7A11
  - S_JNK
  - S_DUSP1_MKP1
  - S_AUTOPHAGY
  - S_FERROPTOSIS
```

Moderate ROS activates JNK and can suppress progesterone-receptor activity through altered SUMO regulation, while decidualization induces antioxidant resistance partly through FOXO1/SOD2 and MKP1. ([FASEB Journal][20])

The recently described `lactate → H3K18 lactylation → SLC7A11` epithelial axis is promising but still new. It should be included in the extended model, not treated as settled core biology. ([Life Science Network][21])

## 3.3 Extended metabolites

The extended inventory should also retain:

```yaml
extended_metabolites:
  - L_arginine
  - nitric_oxide
  - ornithine
  - putrescine
  - spermidine
  - spermine
  - cholesterol
  - phosphatidic_acid
  - phosphatidylcholine_16_0_20_4
  - sphingolipids
  - taurine
  - glutathione
```

These should remain optional until ADOC-specific measurements justify parameterizing them.

---

# 4. Angiogenesis and stromal support

Even without endothelial cells, the maternal layers can produce angiogenic signals. Include:

```yaml
angiogenesis:
  - S_VEGFA
  - E_VEGFA
  - S_KDR
  - X_FLT1_SFLT1
  - X_PGF
  - X_ANGPT1
  - X_ANGPT2
  - X_TEK
  - X_CXCL12
  - X_PROK1
```

In the current ADOC these are **paracrine support outputs**, not vascular phenotypes. The model should produce `OUT_ANGIOGENIC_SUPPORT`, but not claim actual angiogenesis without endothelial cells.

The ADOC transcriptomic data showed vascular-development pathways after treatment, and human endometrial studies implicate VEGF, angiopoietins and CXCL12 in decidual angiogenic support.  ([Obstetrics & Gynecology][22])

---

# 5. Inflammation, senescence and safety module

A contraceptive hit must not obtain a low adhesion score simply by killing or chronically inflaming the tissue.

```yaml
inflammatory_stress:
  - X_IL1B
  - X_TNF
  - X_IL6
  - X_CXCL8
  - X_CXCL1
  - X_TGFB1
  - E_NFKB
  - S_NFKB
  - S_SMAD2_3
  - S_JNK

cell_fate_safety:
  - E_TP53
  - S_TP53
  - E_CDKN1A
  - S_CDKN1A
  - E_CDKN2A
  - S_CDKN2A
  - E_BCL2
  - S_BCL2
  - E_BAX
  - S_BAX
  - E_CASP3
  - S_CASP3
  - E_DNA_DAMAGE
  - S_DNA_DAMAGE
```

Decidualization normally produces both differentiated and acutely senescent stromal populations. Acute senescence can participate in transient receptivity-associated remodelling, whereas persistent senescence and chronic SASP signalling are undesirable. Therefore use:

```yaml
outputs:
  - OUT_ACUTE_DECIDUAL_SENESCENCE
  - OUT_PERSISTENT_SENESCENCE
  - OUT_TRANSIENT_INFLAMMATION
  - OUT_CHRONIC_INFLAMMATION
```

Human decidual models show that FOXO1-associated acute senescence and IL-8 signalling contribute to remodelling, while persistent or excessive senescent populations disturb tissue homeostasis. ([eLife][23])

---

# 6. Optional future modules

## 6.1 Immune extension

Do not activate this module in ADOC v1 because the chip currently lacks immune cells.

```yaml
immune_extension:
  - S_IL15
  - NK_IL2RB
  - NK_IL2RG
  - NK_STAT5
  - NK_KLRD1
  - NK_NCR1
  - NK_PRF1
  - NK_GZMB
  - X_CSF1
  - MAC_CSF1R
  - X_IL10
  - X_TGFB1
  - T_HLAG
  - NK_KIR
```

Stromal IL15–IL2RB/IL2RG signalling is a well-supported stromal–NK interaction in receptive human endometrium. ([Nature][24])

## 6.2 Endothelial extension

```yaml
endothelial_extension:
  - V_KDR
  - V_FLT1
  - V_TEK
  - V_NOS3
  - V_BARRIER
  - V_ANGIOGENESIS
  - V_PGE2
  - V_PGI2
```

## 6.3 Embryo/trophectoderm extension

For MaBoSS v1, a binary `IN_TROPHECTODERM_COMPETENT` input is sufficient. Later add:

```yaml
trophectoderm_extension:
  - T_GATA3
  - T_TEAD4
  - T_CDX2
  - T_NR2F2
  - T_CDH1_APICAL
  - T_SELL
  - T_ITGAV
  - T_ITGB1
  - T_CD44
  - T_ERBB4
  - T_CGB_HCG
  - T_MMP2
  - T_MMP9
  - OUT_T_SPREADING
```

---

# 7. Example Boolean rules

These are starting hypotheses, not final locked rules.

```text
E_PGR =
    IN_PROGESTIN
    and not IN_MIFEPRISTONE

S_PGR =
    IN_PROGESTIN
    and not IN_MIFEPRISTONE

E_AXIN =
    IN_XAV939 or E_AXIN_baseline

E_CTNBB1 =
    E_WNT_CANONICAL
    and not E_AXIN

E_IHH =
    E_PGR
    and E_SOX17
    and E_GATA2

S_HH_ACTIVE =
    E_IHH
    and S_PTCH1
    and S_SMO

S_NR2F2 =
    S_HH_ACTIVE
    and S_PGR

S_HAND2 =
    S_PGR
    and S_NR2F2

S_BMP2 =
    (S_PGR and S_PKA)
    or S_NR2F2

S_WNT4 =
    S_BMP2

S_FOXO1 =
    S_CEBPB
    and (S_PKA or S_WNT4)
    and not S_AKT_HIGH

S_DECIDUALIZED =
    S_PGR
    and S_FOXO1
    and S_CEBPB
    and (S_BMP2 or S_IL11_STAT3)
    and S_METABOLIC_OK
    and not S_APOPTOSIS

S_PRL =
    S_DECIDUALIZED
    and S_FOXO1

S_IGFBP1 =
    S_DECIDUALIZED
    and S_FOXO1
    and S_CEBPB

E_LIF_STAT3 =
    E_LIF
    and E_LIFR
    and E_IL6ST
    and E_JAK1

E_PODXL =
    not E_PGR
    or E_PODXL_FORCED

X_SPP1_LUMEN_FREE =
    E_SPP1_EXPR
    and not IN_ANTI_SPP1

E_SPP1_INTEGRIN =
    X_SPP1_LUMEN_FREE
    and E_ITGAV
    and (E_ITGB3 or E_ITGB5)

E_FOCAL_ADHESION =
    E_SPP1_INTEGRIN
    and E_PTK2_FAK
    and E_SRC
    and E_RAC1

E_ANTIADHESIVE_SURFACE =
    E_PODXL
    or (E_MUC1_BARRIER and not E_MUC1_LOCAL_REMOVAL)
    or E_DAG1_FULL_LENGTH

OUT_EPITHELIAL_ADHESION_SURFACE =
    E_SECRETORY_STATE
    and E_LIF_STAT3
    and E_FOCAL_ADHESION
    and E_SLC3A2_CD98
    and E_CD9
    and not E_ANTIADHESIVE_SURFACE
    and not OUT_BARRIER_DAMAGED
    and E_VIABLE

OUT_MATERNAL_ADHESION_COMPETENCE =
    OUT_EPITHELIAL_ADHESION_SURFACE
    and S_DECIDUALIZED
    and OUT_CROSSTALK_FUNCTIONAL

OUT_STABLE_ADHESION =
    OUT_MATERNAL_ADHESION_COMPETENCE
    and IN_EMBRYO_PRESENT
    and IN_TROPHECTODERM_COMPETENT
```

Codex should annotate every rule with:

* literature source;
* evidence class;
* compartment;
* human versus animal evidence;
* whether the edge is direct, inferred or merely correlative.

CellChat edges from ADOC should be recorded as **inferred communication**, not causal proof.

---

# 8. Required model phenotype outputs

The most important output is not a single `ADHESION` Boolean node. Use a panel of probabilities.

```yaml
primary_outputs:
  - OUT_EPITHELIAL_RECEPTIVE
  - OUT_STROMAL_DECIDUALIZED
  - OUT_CROSSTALK_FUNCTIONAL
  - OUT_MATERNAL_ADHESION_COMPETENCE
  - OUT_STABLE_ADHESION

safety_outputs:
  - OUT_EPITHELIAL_VIABLE
  - OUT_STROMAL_VIABLE
  - OUT_BARRIER_DAMAGED
  - OUT_CHRONIC_INFLAMMATION
  - OUT_PERSISTENT_SENESCENCE
  - OUT_DNA_DAMAGE
  - OUT_APOPTOSIS
  - OUT_ECM_FIBROTIC
  - OUT_RECOVERY_AFTER_WASHOUT

supporting_outputs:
  - OUT_EPITHELIAL_SECRETORY
  - OUT_EPITHELIAL_CILIATED
  - OUT_STROMAL_PROLIFERATIVE
  - OUT_STROMAL_MYOFIBROBLAST
  - OUT_ANGIOGENIC_SUPPORT
  - OUT_METABOLIC_HEALTH
```

A non-hormonal contraceptive should maximize:

[
1-P(\text{adhesion competence})
]

while also maximizing:

[
P(\text{epithelial viability})
\times
P(\text{stromal viability})
\times
P(\text{barrier not damaged})
\times
P(\text{decidualization preserved})
\times
P(\text{recovery after washout})
]

and minimizing:

[
P(\text{chronic inflammation})
+
P(\text{persistent senescence})
+
P(\text{DNA damage})
]

This multi-objective definition prevents broad FAK, PI3K, MAPK or cytotoxic inhibitors from being incorrectly ranked as “good contraceptives.”

---

# 9. Experimental measurements required to constrain the network

## 9.1 Compartment-specific bulk RNA-seq

### Epithelial signature

Priority genes:

```text
ESR1, PGR, GATA2, SOX17, FOXA2, IHH,
LIF, LIFR, IL6ST, STAT3,
PAEP, SPP1, DPP4,
SCGB2A1, SCGB1D2,
CEACAM5, CEACAM6,
SGK1, KLF5, ELF3,
SLC3A2, CD9, ANXA2,
ITGAV, ITGB1, ITGB3, ITGB5,
CD44, CDH1, CTNND1,
PODXL, MUC1, DAG1, PCSK5, PCSK6,
TJP1, OCLN, CLDN4, F11R,
VTCN1, CDH6, THBS1, MMP7
```

### Stromal signature

```text
ESR1, PGR, NCOA2,
CREB1, CEBPB, FOXO1, GATA2,
NR2F2, HAND2,
BMP2, BMPR1A, SMAD1, SMAD5,
WNT4, CTNNB1, DKK1,
IL11, IL11RA, IL6ST, STAT3,
NOTCH1, JAG1,
PRL, IGFBP1, FBLN1, DCN, TIMP3, IL15,
VEGFA, KDR,
SLC2A1, PFKFB3, LDHA, SLC16A3,
GLS, GLUD1,
PTGS1, PTGS2, PTGES, PTGER2, PTGER4,
NFE2L2, SOD2, GPX3,
MMP11, ECM1, COL3A1, COL5A1
```

Bulk RNA should initialize or calibrate transcriptional nodes, but it cannot directly establish kinase or transcription-factor activity.

## 9.2 Targeted intracellular protein/activity measurements

This is the most important missing layer if you want a mechanistic MaBoSS model.

### Epithelial

* nuclear ESR1 and PGR;
* p-STAT3;
* p-FAK;
* p-SRC;
* p-ERK;
* p-AKT;
* nuclear β-catenin;
* SPP1;
* PODXL;
* MUC1 surface localization;
* ITGAV/ITGB3;
* CD98/CD9;
* apical versus junctional CDH1;
* TJP1/ZO-1.

### Stromal

* nuclear FOXO1;
* p-CREB;
* HAND2;
* NR2F2;
* BMP2;
* p-SMAD1/5;
* p-STAT3;
* PRL;
* IGFBP1.

These could be measured in selected chips by quantitative immunofluorescence rather than consuming a large fraction of cells for Western blotting.

## 9.3 Outlet proteins

### Retain the published core panel

* PRL
* IGFBP1
* PAEP/glycodelin

The paper measured PRL and IGFBP1 longitudinally and epithelial PAEP after hormonal treatment. 

### Strongly recommended additions

* SPP1/osteopontin
* LIF
* IL11
* VEGFA
* IL6
* CXCL8/IL8
* CXCL1
* MMP2
* MMP9
* TIMP1
* PGE2

For anti-SPP1 experiments, validate the SPP1 assay with spike recovery because the neutralizing antibody can mask the ELISA epitope. Ideally distinguish:

* total SPP1;
* free bioavailable SPP1;
* antibody-bound SPP1.

## 9.4 Metabolic outlet measurements

Use **inlet–outlet differences**, not outlet concentration alone:

* glucose consumption;
* lactate production;
* pyruvate production or consumption;
* lactate:pyruvate ratio;
* glutamine consumption;
* glutamate release;
* PGE2;
* PGI2 metabolite;
* pH;
* dissolved oxygen, where technically feasible;
* LDH release as tissue-damage control.

αKG is biologically important but likely more useful in intracellular extracts or untargeted metabolomics than as a routine outlet marker.

## 9.5 Functional/QC measurements

Even without embryo adhesion in the pilot:

* permeability or TEER;
* epithelial morphology;
* stromal roundness;
* cell number;
* live/dead staining;
* LDH;
* cleaved CASP3;
* γH2AX;
* p21 and p16;
* recovery after washout.

---

# 10. How to calibrate adhesion probability

Use sequential simulations rather than one stationary-state simulation:

```text
Phase 0: basal expansion
Phase 1: E2 priming, days 0–2
Phase 2: E2 + MPA + cAMP + XAV939, days 2–6
Phase 3: candidate perturbation, e.g. days 6–7
Phase 4: optional washout/recovery
```

The final state distribution from one phase becomes the initial distribution of the next.

Suggested fitting hierarchy:

1. Fit topology and qualitative directions using published human biology.
2. Fit untreated versus hormone-treated transition rates using ADOC scRNA-seq and outlet time series.
3. Use mifepristone as the first independent perturbation test.
4. Freeze the model.
5. Predict anti-SPP1 or another non-hormonal perturbation.
6. Compare predictions with new bulk RNA-seq, outlet and safety readouts.
7. Later, validate predicted adhesion probabilities with blastoids or embryos.

MaBoSS should return:

```text
P(OUT_MATERNAL_ADHESION_COMPETENCE = 1)
```

For the published adhesion experiments, fit the model using the actual binomial likelihood:

```text
HT:             9 adhered / 19
untreated:      0 adhered / 12
mifepristone:   1 adhered / 8
```

Do not force the simulated probabilities to equal 0, 0.47 and 0.125 exactly; the experimental confidence intervals are wide.

Because your initial 12-chip pilot contains no embryo, it can validate the **maternal state model** and perturbation mechanism. It cannot independently validate donor-specific adhesion probability. Published ADOC adhesion data will remain the functional prior until a later adhesion experiment is performed.

---

# 11. Most promising non-hormonal target classes

| Priority | Target strategy                                            | Why interesting                                                                                                                             | Main concern                                                                        |                                             Confidence |
| -------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | -----------------------------------------------------: |
| 1        | **Maintain luminal PODXL**                                 | Direct human evidence that PODXL creates a non-receptive surface and inhibits human embryo attachment; largely epithelial-surface mechanism | No mature, proven PODXL-activating drug; excessive barrier effects possible         |              Biology **8/10**, drug readiness **3/10** |
| 2        | **Prevent DAG1 activation by modulating PCSK5/6 cleavage** | Direct post-translational control of human epithelial adhesiveness; potentially fast and reversible                                         | PCSK5/6 have other substrates; specificity required                                 |              Biology **7/10**, drug readiness **3/10** |
| 3        | **Luminal SPP1 neutralization**                            | Easy to test, extracellular, directly represented in ADOC signalling and integrin biology                                                   | SPP1 also participates in decidual and stromal biology; effect may be non-monotonic | Experimental benchmark **8/10**, final safety **4/10** |
| 4        | **TRO–TROAP–BYSL interface**                               | Direct embryo–epithelium adhesion concept; potentially interface-selective                                                                  | Limited modern human functional and pharmacological evidence                        |                                               **5/10** |
| 5        | **MUC1 removal/glycoform control**                         | Could preserve the antiadhesive luminal glycocalyx                                                                                          | MUC1 has both antiadhesive and L-selectin-mediated adhesive roles                   |                                               **4/10** |
| 6        | **CD98/CD9, ANXA2 or apical CDH1 blockade**                | Strong experimental support for adhesion                                                                                                    | Important general epithelial and cellular functions; safety concern                 |   Biology **8/10**, translational selectivity **3/10** |
| 7        | **LIF/LIFR, HBEGF/ERBB4 or gp130 blockade**                | Strong receptivity pathways                                                                                                                 | Broad endometrial, regenerative and immune effects                                  |                                               **4/10** |
| 8        | **Integrin, FAK, SRC or PI3K inhibition**                  | Mechanistically clear and likely to reduce adhesion                                                                                         | Too broad; likely barrier, survival and tissue-remodelling toxicity                 |                               Final candidate **2/10** |

PODXL is particularly interesting conceptually because it represents the inverse strategy:

> instead of destroying receptivity, temporarily retain a physiologically non-receptive luminal surface.

However, anti-SPP1 remains a more practical first perturbation because a neutralizing reagent is already available and the intervention is easy to encode and experimentally control.

---

# 12. Codex-ready task

```text
Build a Pixi/Python repository containing two evidence-traceable MaBoSS models of ADOC:

1. adoc_core:
   Coupled epithelial, stromal and extracellular network implementing the node inventory and core rules in this specification.

2. adoc_extended:
   Adds ECM, metabolism, senescence, angiogenesis, optional immune/endothelial and embryo-interface modules.

Use E_, S_, X_, IN_ and OUT_ prefixes. Do not create a flat unprefixed network.

Create:
- data/nodes.tsv
- data/edges.tsv
- data/evidence.tsv
- models/adoc_core.bnd
- models/adoc_core.cfg
- models/adoc_extended.bnd
- models/adoc_extended.cfg
- src/run_protocol.py
- src/screen_perturbations.py
- src/calibrate.py
- src/report.py
- tests/

nodes.tsv columns:
node_id, compartment, entity_type, module, tier, measurable,
perturbable, expected_HT_direction, notes

edges.tsv columns:
source, target, sign, mechanism, evidence_class, species,
direct_or_inferred, citation, confidence

Implement sequential protocols:
- basal
- E2 priming
- E2+MPA+cAMP+XAV939
- hormone treatment+mifepristone
- hormone treatment+anti-SPP1
- perturbation washout

Required qualitative tests:
- hormone treatment increases epithelial secretory state,
  stromal decidualization and maternal adhesion competence
- hormone treatment increases PAEP/SPP1 and PRL/IGFBP1 outputs
- hormone treatment reduces ciliated-state probability
- mifepristone reduces PGR activity and adhesion competence
- anti-SPP1 inhibits extracellular free SPP1, not SPP1 transcription
- anti-SPP1 can reduce adhesion without automatically forcing
  stromal decidualization OFF
- cytotoxic FAK/SRC inhibition receives a safety penalty
- washout can return a selective perturbation toward the receptive state

Implement a multi-objective candidate score that minimizes adhesion
while penalizing epithelial/stromal death, barrier damage, chronic
inflammation, persistent senescence, decidual failure and failure to
recover after washout.

Do not invent unsupported edges. Mark uncertain rules explicitly and
make them replaceable. Generate network diagrams and a report listing
all assumptions, evidence levels, attractors, phenotype probabilities,
sensitivity analyses and top single/pair non-hormonal perturbations.
```

## Bottom line

The first trustworthy implementation should be a **coupled, approximately 80–110-node maternal ADOC model**, not an enormous network containing every differential gene. The extended evidence catalogue can contain 150–200 nodes, but only nodes with supported regulatory roles should enter the executable logic.

The highest-priority mechanistic modules are:

1. `ESR/PGR → epithelial IHH → stromal NR2F2/HAND2/BMP2`
2. `cAMP/PKA/CEBPB/FOXO1 → decidualization`
3. `LIF/LIFR/gp130/STAT3`
4. `SPP1–integrin–FAK/SRC/RAC1`
5. `PODXL/MUC1/DAG1` control of the apical antiadhesive surface
6. `CD98/CD9`, `ANXA2` and apical `CDH1`
7. glycolysis, PGE2 signalling, glutaminolysis and redox health
8. barrier, senescence, inflammation and washout recovery.

**Overall confidence: 7/10.**
The hormone-response and decidualization backbone is relatively well supported (**8–9/10**). The adhesion-surface catalogue is substantial but contains context-dependent mechanisms (**7/10**). Ranking a final safe non-hormonal contraceptive target remains more uncertain (**4–5/10**) because the necessary selective perturbation and reversibility data do not yet exist.

[1]: https://curie.fr/publications/physiboss-20-sustainable-integration-stochastic-boolean-and-agent-based-modelling-frameworks "https://curie.fr/publications/physiboss-20-sustainable-integration-stochastic-boolean-and-agent-based-modelling-frameworks"
[2]: https://pubmed.ncbi.nlm.nih.gov/42430472/ "https://pubmed.ncbi.nlm.nih.gov/42430472/"
[3]: https://www.nature.com/articles/s41591-020-1040-z "https://www.nature.com/articles/s41591-020-1040-z"
[4]: https://pubmed.ncbi.nlm.nih.gov/23142810/ "https://pubmed.ncbi.nlm.nih.gov/23142810/"
[5]: https://pubmed.ncbi.nlm.nih.gov/9368687/ "https://pubmed.ncbi.nlm.nih.gov/9368687/"
[6]: https://keio.elsevierpure.com/en/publications/the-antiproliferative-action-of-progesterone-in-uterine-epitheliu/ "https://keio.elsevierpure.com/en/publications/the-antiproliferative-action-of-progesterone-in-uterine-epitheliu/"
[7]: https://pubmed.ncbi.nlm.nih.gov/20976164/ "https://pubmed.ncbi.nlm.nih.gov/20976164/"
[8]: https://pubmed.ncbi.nlm.nih.gov/33822049/ "https://pubmed.ncbi.nlm.nih.gov/33822049/"
[9]: https://pubmed.ncbi.nlm.nih.gov/26077903/ "https://pubmed.ncbi.nlm.nih.gov/26077903/"
[10]: https://faseb.onlinelibrary.wiley.com/doi/full/10.1096/fj.12-204008 "https://faseb.onlinelibrary.wiley.com/doi/full/10.1096/fj.12-204008"
[11]: https://academic.oup.com/humrep/article/41/4/563/8489221 "https://academic.oup.com/humrep/article/41/4/563/8489221"
[12]: https://academic.oup.com/hropen/article-abstract/2022/4/hoac043/6760130 "https://academic.oup.com/hropen/article-abstract/2022/4/hoac043/6760130"
[13]: https://pubmed.ncbi.nlm.nih.gov/11159362/ "https://pubmed.ncbi.nlm.nih.gov/11159362/"
[14]: https://www.sciencedirect.com/science/article/abs/pii/S0945053X10000545 "https://www.sciencedirect.com/science/article/abs/pii/S0945053X10000545"
[15]: https://www.sciencedirect.com/science/article/pii/S0015028203030383 "https://www.sciencedirect.com/science/article/pii/S0015028203030383"
[16]: https://pubmed.ncbi.nlm.nih.gov/39365817/ "https://pubmed.ncbi.nlm.nih.gov/39365817/"
[17]: https://pubmed.ncbi.nlm.nih.gov/24204309/ "https://pubmed.ncbi.nlm.nih.gov/24204309/"
[18]: https://pubmed.ncbi.nlm.nih.gov/32548315/ "https://pubmed.ncbi.nlm.nih.gov/32548315/"
[19]: https://pubmed.ncbi.nlm.nih.gov/39555416/ "https://pubmed.ncbi.nlm.nih.gov/39555416/"
[20]: https://faseb.onlinelibrary.wiley.com/doi/abs/10.1096/fj.09-149153 "https://faseb.onlinelibrary.wiley.com/doi/abs/10.1096/fj.09-149153"
[21]: https://www.lifescience.net/publications/1730824/mechanistic-insights-into-recurrent-implantation-f/ "https://www.lifescience.net/publications/1730824/mechanistic-insights-into-recurrent-implantation-f/"
[22]: https://obgyn.onlinelibrary.wiley.com/doi/10.1111/jog.12392 "https://obgyn.onlinelibrary.wiley.com/doi/10.1111/jog.12392"
[23]: https://elifesciences.org/articles/31274 "https://elifesciences.org/articles/31274"
[24]: https://www.nature.com/articles/s41467-025-67492-z "https://www.nature.com/articles/s41467-025-67492-z"
