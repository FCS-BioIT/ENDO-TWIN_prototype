# Embryo adhesion in endometrial epithelium and stroma: MaBoSS knowledge package

**Knowledge-base version:** `adoc-embryo-adhesion-literature-v0.1.0`  
**Generated:** 2026-07-26  
**Status:** candidate evidence layer; not the canonical executable network

## Executive summary

The strongest repeatedly supported architecture is a **gated, multicomponent
adhesion-permissive state**, not a single master receptor. Hormonal programming
must generate both an epithelial receptive surface and a stromal decidual/
mechanically permissive state; embryo contact then stabilizes attachment.

The highest-confidence regulatory backbone is mouse-derived but biologically
coherent with human endometrium: **LIF-LIFR/GP130-STAT3** in epithelium and
**P4/PGR-IHH-NR2F2/COUP-TFII-BMP2-HAND2** across epithelium and stroma. Human
studies add the detailed surface switch: **PODXL**, dual **MUC1** states,
**PCSK5/PC6-DAG1 processing**, **CD98/CD9**, **ANXA2-RHOA-actin**, apical
**CDH1/CTNND1**, **SPP1/osteopontin-integrins**, and **HB-EGF**. Stromal support
includes decidualization, balanced senescence/dynamic matrix remodeling,
**TAZ/WWTR1**, ER-stress control, and mechanical softening.

Because the current MaBoSS boundary contains only maternal epithelial and
stromal cells, **embryo presence, trophectoderm competence, hCG and generic
embryo-conditioned signals remain external inputs**. WNT5A/7A effects that act
by changing embryo integrin trafficking also remain external or are deferred to
PhysiBoSS2.

Direct human ADOC anchors are: HT **9/19 (47%)** stable attachments, untreated
**0/12**, HT+mifepristone **1/8 (12.5%)**, and mean attachment time
**34.1 +/- 12.2 h**. These are assay-level observations with small sample sizes,
not clinical probabilities. MaBoSS occupancy is a model trajectory frequency
and its time is relative unless explicitly scaled.

Human MUC1 force-spectroscopy data support a dual-state representation rather
than one MUC1 switch: reported intrinsic adhesion shifted from about **148 pN to
271 pN** with higher MUC1/glycosylation, fell from **271 pN to 118 pN** after
MUC1 depletion, and highly glycosylated states supported **>400 pN** L-selectin
interactions versus **<=200 pN** in low-expression/low-glycosylation states.

A systematic review found that many receptivity markers associate with outcome
but have weak clinical predictive performance. Therefore PAEP, PRL, IGFBP1,
SPP1 and related markers should be treated as mechanistic/state observables,
not as interchangeable surrogates for stable adhesion or pregnancy.

### Conservative confidence

| Domain | Confidence |
|---|---:|
| Mouse core attachment/receptivity circuitry | 9/10 |
| Direct human ADOC calibration anchors | 8/10 |
| Human epithelial adhesion effectors | 7/10 |
| Human stromal permissiveness/mechanics | 6/10 |
| Quantitative rate transfer into MaBoSS | 5/10 |
| Temperature/pH/oxygen causal adhesion rules | 2-3/10 |
| Overall package completeness for the reviewed scope | 8/10 |

## Scope and evidence rules

Included: maternal epithelial and stromal biology of apposition/attachment and
immediate pre-adhesion receptivity in humans, mice and closely related mammals.
Reviews provide consensus; knockouts, knockdowns, blocking, gain-of-function,
co-culture and biophysical assays provide mechanistic evidence; expression-only
and in-silico interaction studies remain descriptive/candidate evidence.

Excluded from internal logic: trophoblast, immune and endothelial cell networks.
Their signals can be explicit external inputs. No association-only marker is
promoted automatically to a causal edge. No threshold or kinetic rate is
invented when absent from the source.

## Mechanistic modules

| module_id | name | compartments | summary | evidence | refs | confidence | maboss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MOD-01 | Hormonal receptive-state induction | epithelium;stroma | E2, progestin/PGR, cAMP and XAV939 establish the ADOC secretory/decidual state; mifepristone antagonizes PGR and strongly reduces adhesion. | direct ADOC plus conserved uterine biology | REF-020;REF-001;REF-002 | 9 | Keep protocol agents as explicit inputs; do not collapse them into a single hormone switch. |
| MOD-02 | LIF-LIFR/GP130-STAT3 attachment gate | epithelium;stroma | Pre-attachment epithelial/glandular LIF activates GP130/STAT3 to remodel the epithelium and enable attachment; stromal LIF/STAT3 supports later stabilization. | replicated mouse genetics; human expression and cell-model support | REF-023;REF-024;REF-030;REF-031;REF-032;REF-033;REF-036;REF-038 | 9 | Core candidate module; separate epithelial and stromal STAT3 where model size allows. |
| MOD-03 | PGR-IHH-NR2F2-BMP2-HAND2 relay | epithelium to stroma to epithelium | Progesterone induces epithelial IHH; stromal NR2F2/BMP2/HAND2 drives decidualization and restrains epithelial estrogen/FGF proliferation. | replicated mouse conditional genetics; human decidual support | REF-002;REF-025;REF-026;REF-027;REF-028;REF-029 | 8 | Core cross-compartment relay; existing baseline already includes IHH, NR2F2 and BMP2; add HAND2 as first extension. |
| MOD-04 | Epithelial anti-adhesive glycocalyx/barrier removal | epithelium | PODXL, full-length DAG1 and some MUC1 states create a non-receptive barrier; receptivity requires downregulation, cleavage or glycoform switching. | direct human gain-loss and biophysical studies | REF-011;REF-012;REF-013;REF-014 | 7 | Use explicit inhibitory nodes. Split MUC1 barrier and MUC1 sLeX/glyco-permissive states. |
| MOD-05 | Human epithelial adhesive surface effectors | epithelium | CD98/CD9, apical CDH1/CTNND1, ANXA2-RHOA-actin, SPP1-integrins and HB-EGF collectively form a receptive adhesive surface. | human mechanistic, biophysical and descriptive evidence | REF-006;REF-007;REF-008;REF-009;REF-019;REF-038 | 7 | Prefer rate modifiers or redundant OR-gates, not a requirement that every effector be ON. |
| MOD-06 | PCSK5 membrane and dystroglycan processing | epithelium | PCSK5/PC6 cleaves EBP50 and alpha-DAG1 N-terminus, reorganizing membrane-cytoskeletal interactions and releasing an attachment barrier. | direct human knockdown and cleavage studies | REF-010;REF-011 | 7 | Represent PC6 -> DAG1_CLEAVED and DAG1_FULL as an inhibitor. |
| MOD-07 | SPP1/OPN-integrin adhesion and decidual support | epithelium;stroma;interface | Epithelial OPN supports interface adhesion while stromal OPN contributes to decidualization; integrin partners include alphaVbeta3/5 and ITGB1-related routes. | human, primate and cell-model evidence | REF-007;REF-015;REF-017;REF-022;REF-038 | 7 | Keep epithelial and stromal SPP1 separate; anti-SPP1 neutralizes extracellular ligand rather than transcription. |
| MOD-08 | Decidualization and dynamic senescence balance | stroma with glandular epithelium | Decidual transformation and a controlled senescence/remodeling program create a dynamic implantation matrix; complete removal or excess dysfunction is unfavorable. | human assembloid mechanistic evidence | REF-016 | 6 | Use a balanced state or uncertain rule variant, not a simplistic senescence ON=bad rule. |
| MOD-09 | TAZ-Hippo ECM remodeling and stromal mechanics | stroma | TAZ/WWTR1 coordinates collagen/ECM remodeling; normal decidualization softens stroma, while excess ER stress prevents softening and reduces adhesion/expansion. | recent mouse genetics plus human mechanobiology | REF-018;REF-035 | 6 | Add TAZ_ECM and Mechanical_Permissive_ECM; ER stress and excessive stiffness inhibit the mechanical state. |
| MOD-10 | Cell-type-specific interaction candidates | epithelium;stroma;interface | LGALS1, LGALS3, ITGB1, BSG and related interactions are receptive-phase candidates from compartment-resolved human RNA-seq. | human paired cell-type-specific RNA-seq plus in-silico interface inference | REF-015 | 5 | Expansion tier only; use for sensitivity analysis until perturbational evidence exists. |
| MOD-11 | Embryo-conditioned feedback | external embryo input to epithelium | Embryo contact and hCG can induce CD98/CD9 and apical CDH1/CTNND1, stabilizing first contact. | human direct and cell-model evidence | REF-008;REF-019;REF-020 | 7 | Model hCG/contact as exogenous inputs because trophoblast is outside the current MaBoSS cell types. |
| MOD-12 | Uterine WNT-Ca2+-integrin competence cue | maternal cue;embryo execution | Uterine WNT5A/7A rapidly increases embryo alpha5beta1 trafficking and fibronectin binding through CaMKII. | mouse mechanistic attachment assays | REF-034 | 6 | Do not implement as maternal intracellular output in the core model; retain as external embryo-competence modifier or later PhysiBoSS interface field. |
| MOD-13 | Physical microenvironment and transport | chip/extracellular | Flow, oxygen, pH, temperature, ligand presentation and matrix stiffness can alter assay context, transport and tissue state, but direct adhesion-specific causal data are uneven. | project/NAM context plus mechanics papers; limited direct adhesion perturbation for temperature/pH/O2 | REF-018;REF-020;REF-021 | 4 | Stiffness/ER stress may modify rates; temperature, pH, oxygen and flow should initially be boundary/QC variables or PhysiCell fields. |

## Cross-species synthesis

- **Mouse genetics defines regulatory logic:** LIF/GP130/STAT3 and the
  PGR-IHH-NR2F2-BMP2-HAND2 relay have the strongest causal support.
- **Human experiments define the surface state:** anti-adhesive barriers must be
  removed/reconfigured while multiple positive adhesion routes become
  available.
- **Primate evidence supports ECM/integrin conservation**, especially OPN and
  fibronectin-related modules.
- **Stroma is not merely a marker compartment:** decidual and mechanical state
  can determine whether attachment is stabilized and whether the system can
  proceed toward invasion.

## Candidate nodes

| node_id | label | compartment | role | tier | sign | baseline_mapping | refs | confidence | measurable | perturbable | logic_hint | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IN_HCG | Embryo-derived hCG input | external_embryo | input | core_extension | positive | new | REF-008;REF-019;REF-020 | 7 | beta-hCG in outlet medium | yes | self-maintaining external input | Do not model trophoblast production internally in the maternal-only network. |
| IN_EMBRYO_CONDITIONED_SIGNAL | Generic embryo-conditioned signal | external_embryo | input | core_extension | positive | new | REF-008;REF-019;REF-020 | 5 | conditioned medium or contact state | yes | self-maintaining external input | Use only when hCG/contact-specific information is unavailable. |
| IN_ER_STRESS_EXCESS | Excess endoplasmic-reticulum stress | stroma_external | perturbation_input | core_extension | negative | new | REF-018 | 6 | UPR/ERS markers | yes | self-maintaining external input | Represents pathological excess, not physiological decidual ER stress. |
| IN_HIGH_ECM_STIFFNESS | Excessive ECM/stromal stiffness | extracellular | boundary_input | core_extension | negative | new | REF-018;REF-035 | 5 | AFM Young modulus or hydrogel modulus | yes | self-maintaining external input | Prefer a graded rate modifier in PhysiBoSS; Boolean input is a coarse sensitivity variable. |
| E_LIF | Epithelial/glandular LIF | epithelium | ligand | core_extension | positive | new | REF-023;REF-024;REF-033;REF-036;REF-037 | 9 | LIF secretion/expression | yes | E_SECRETORY_STATE and not E_KLF12_HIGH | Hard attachment gate in mouse; direct human causality is weaker. |
| E_KLF12_HIGH | High epithelial KLF12 | epithelium | negative_regulator | expansion | negative | new | REF-037 | 5 | KLF12 expression | yes | context-specific input or inferred state | Human recurrent implantation failure evidence; not required in first extension. |
| E_GP130_STAT3 | Epithelial LIFR/GP130-STAT3 activity | epithelium | pathway_state | core_extension | positive | new | REF-030;REF-031;REF-032;REF-033;REF-036 | 9 | pSTAT3 and target program | yes | E_LIF | Candidate central attachment gate and remodeling driver. |
| S_STAT3 | Stromal STAT3 activity | stroma | pathway_state | expansion | positive | new | REF-031;REF-033 | 7 | pSTAT3 or regulon | yes | stromal LIF/IL6-family cue and decidual state | Later support rather than sole initial attachment gate. |
| S_HAND2 | Stromal HAND2 | stroma | transcription_factor | core_extension | positive | new downstream of S_BMP2 | REF-028;REF-029 | 8 | HAND2 expression/activity | yes | S_BMP2 or S_PGR | Suppresses stromal FGF output and epithelial proliferative nonreceptivity. |
| S_FGF_MITOGENIC | Stromal mitogenic FGF output | stroma | paracrine_inhibitor_of_receptivity | expansion | negative | new | REF-028 | 7 | FGF family expression/secretion | yes | not S_HAND2 | Collapsed family-level state; avoid selecting a specific FGF without data. |
| E_ESTROGENIC_PROLIFERATION | Epithelial estrogen-driven proliferative state | epithelium | anti_receptive_state | expansion | negative | new | REF-025;REF-026;REF-028 | 8 | Ki67/ESR target program | yes | IN_E2 and S_FGF_MITOGENIC and not S_HAND2 | Should be suppressed during receptivity. |
| E_PODXL | Epithelial PODXL barrier | epithelium | anti_adhesive_surface | core_extension | negative | new | REF-013;REF-014 | 7 | apical PODXL | yes | not E_SECRETORY_STATE | Forced ON should suppress adhesion competence. |
| E_CD98_CD9 | Epithelial CD98/CD9 complex | epithelium | adhesive_effector | core_extension | positive | new | REF-008 | 7 | SLC3A2/CD98 and CD9 surface abundance | yes | E_GP130_STAT3 or IN_HCG or IN_E2 | Use as a rate accelerator or redundant route. |
| E_CDH1_APICAL | Apical epithelial CDH1/CTNND1 state | epithelium | adhesive_effector | core_extension | positive | new | REF-019 | 7 | free-apical CDH1 and CTNND1 | yes | IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL | Do not conflate apical adhesion CDH1 with lateral junctional CDH1. |
| E_ANXA2_ACTIN | ANXA2-RHOA-F-actin remodeling | epithelium | cytoskeletal_effector | core_extension | positive | new | REF-009 | 6 | ANXA2, RHOA-GTP, F-actin architecture | yes | uncertain: receptive state or embryo-conditioned activation | Single main mechanistic literature line; keep as rate modifier. |
| E_HBEGF | Epithelial HB-EGF | epithelium | growth_factor_effector | core_extension | positive | new | REF-006;REF-007 | 6 | HBEGF expression/secretion | yes | E_SECRETORY_STATE | Likely support/rate modifier rather than hard gate. |
| E_PC6 | Epithelial PCSK5/PC6 activity | epithelium | protease | core_extension | positive | new | REF-010;REF-011 | 7 | PCSK5 expression/activity and cleavage products | yes | E_SECRETORY_STATE | Window-specific protease with direct attachment evidence. |
| E_DAG1_FULL | Full-length alpha-dystroglycan barrier | epithelium | anti_adhesive_surface | core_extension | negative | new | REF-011 | 7 | cell-surface alpha-DG N-terminus | yes | not E_PC6 | Barrier state. |
| E_DAG1_CLEAVED | PC6-cleaved alpha-dystroglycan state | epithelium | adhesive_surface_release | core_extension | positive | new | REF-011 | 7 | uterine-fluid alpha-DG-N and tissue cleavage | yes | E_PC6 | Barrier-release state; can be complementary to E_DAG1_FULL. |
| E_MUC1_BARRIER | Anti-adhesive MUC1 glycocalyx state | epithelium | anti_adhesive_surface | core_extension | negative | new | REF-012;REF-025 | 6 | MUC1 abundance and non-permissive glycoforms | yes | not E_SECRETORY_STATE or E_ESTROGENIC_PROLIFERATION | Avoid a single MUC1 node because human glycoforms can be pro-adhesive. |
| E_MUC1_SLEX | Glyco-permissive MUC1 sLeX-like state | epithelium | adhesive_effector | core_extension | positive | new | REF-012 | 6 | MUC1 glycoform/sLeX and force spectroscopy | yes | E_SECRETORY_STATE and glycosylation program | Moderate early-contact rate enhancer. |
| E_ITGAVB3_5 | Epithelial alphaVbeta3/alphaVbeta5 integrin state | epithelium | adhesive_receptor | core_extension | positive | new | REF-007;REF-022;REF-038 | 6 | ITGAV/ITGB3/ITGB5 surface abundance | yes | E_LIF or E_HBEGF or E_SECRETORY_STATE | Human cell-model and primate support; receptor-side assignment depends on assay. |
| S_SPP1 | Stromal SPP1/osteopontin | stroma | decidual_effector | core_extension | positive | new | REF-017 | 6 | SPP1 expression/secretion | yes | S_DECIDUALIZED | Separate from existing epithelial E_SPP1_EXPR. |
| S_TAZ_ECM | Stromal TAZ/WWTR1 ECM-remodeling state | stroma | mechanical_regulator | core_extension | positive | new | REF-035 | 6 | TAZ activity and collagen/ECM program | yes | S_DECIDUALIZED | Recent evidence; use sensitivity analysis. |
| S_DECIDUAL_SENESCENCE_BALANCED | Balanced decidual senescence/remodeling state | stroma | dynamic_matrix_regulator | expansion | positive_biphasic | new | REF-016 | 6 | senescence subpopulation and SASP/remodeling markers | yes | S_DECIDUALIZED and not pathological persistence | Biphasic; do not equate all senescence with failure. |
| X_MECHANICAL_PERMISSIVE_ECM | Mechanical and dynamic ECM permissiveness | extracellular | latent_state | core_extension | positive | new | REF-016;REF-018;REF-035 | 6 | AFM stiffness, matrix dynamics, collagen architecture | yes | S_TAZ_ECM and S_DECIDUALIZED and not IN_ER_STRESS_EXCESS and not IN_HIGH_ECM_STIFFNESS | Bridge to later PhysiBoSS matrix fields. |
| E_RECEPTIVE_SURFACE | Epithelial receptive adhesive surface | epithelium | latent_state | core_extension | positive | refines OUT_EPITHELIAL_RECEPTIVE | REF-006;REF-008;REF-009;REF-010;REF-011;REF-012;REF-013;REF-014;REF-019 | 7 | composite surface panel | indirect | STAT3 gate, barriers OFF, at least one positive effector ON | Human evidence supports a multicomponent surface transition rather than one master receptor. |
| X_LGALS1_3 | LGALS1/LGALS3 interface state | interface | candidate_effector | expansion | positive | new | REF-015 | 5 | LGALS1/3 secretion/expression | yes | receptive compartment state | Computationally prioritized; needs perturbational confirmation. |
| X_BSG_ITGB1 | BSG-ITGB1 interface state | interface | candidate_effector | expansion | positive | new | REF-015 | 5 | BSG/ITGB1 surface abundance | yes | receptive compartment state | Expansion candidate only. |
| IN_UTERINE_WNT_CUE | Uterine WNT5A/WNT7A embryo-competence cue | external_interface | external_input | physiboss_later | positive | new | REF-034 | 6 | WNT5A/7A in uterine fluid | yes | external modifier of IN_TROPHECTODERM_COMPETENT | Embryo execution is outside the maternal-only MaBoSS network. |

## Candidate edges

| edge_id | source | target | sign | mechanism | refs | confidence | tier | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EDGE-001 | E_SECRETORY_STATE | E_LIF | activation | state_to_ligand | REF-023;REF-024;REF-033;REF-036 | 7 | core_extension | Candidate human-facing abstraction; exact hormonal induction logic remains uncertain. |
| EDGE-002 | E_KLF12_HIGH | E_LIF | inhibition | transcriptional | REF-037 | 5 | expansion | RIF-associated human mechanism. |
| EDGE-003 | E_LIF | E_GP130_STAT3 | activation | ligand_receptor_pathway | REF-030;REF-032;REF-033;REF-036 | 9 | core_extension | Central attachment pathway. |
| EDGE-004 | E_GP130_STAT3 | E_RECEPTIVE_SURFACE | activation | pathway_to_state | REF-030;REF-032;REF-033 | 8 | core_extension | Junctional/remodeling gate. |
| EDGE-005 | E_GP130_STAT3 | E_CD98_CD9 | activation | pathway_to_effector | REF-008 | 6 | core_extension | LIF induction reported in human epithelial adhesion system. |
| EDGE-006 | E_GP130_STAT3 | E_ITGAVB3_5 | activation | pathway_to_effector | REF-038 | 6 | core_extension | Human cell-model link. |
| EDGE-007 | E_GP130_STAT3 | E_ANXA2_ACTIN | activation | candidate_pathway_to_effector | REF-009;REF-030 | 4 | uncertain_variant | No direct LIF-to-ANXA2 proof in this inventory; use only as a tested variant. |
| EDGE-008 | E_IHH | S_NR2F2 | activation | paracrine | REF-002;REF-025;REF-026 | 8 | existing_core | Already represented in baseline. |
| EDGE-009 | S_NR2F2 | S_BMP2 | activation | transcriptional | REF-026;REF-027 | 8 | existing_core | Already represented in baseline. |
| EDGE-010 | S_BMP2 | S_HAND2 | activation | state_to_transcription_factor | REF-027;REF-028;REF-029 | 7 | core_extension | Compact relay; direct ordering may vary by context. |
| EDGE-011 | S_PGR | S_HAND2 | activation | hormone_to_transcription_factor | REF-028;REF-029 | 8 | core_extension | Conserved progesterone-sensitive stromal node. |
| EDGE-012 | S_HAND2 | S_FGF_MITOGENIC | inhibition | transcriptional | REF-028 | 8 | expansion | Family-level FGF collapse. |
| EDGE-013 | S_FGF_MITOGENIC | E_ESTROGENIC_PROLIFERATION | activation | paracrine | REF-028 | 8 | expansion | Stromal-to-epithelial mitogenic relay. |
| EDGE-014 | S_HAND2 | E_ESTROGENIC_PROLIFERATION | inhibition | cross_compartment | REF-028 | 8 | expansion | Net effect through FGF suppression. |
| EDGE-015 | E_ESTROGENIC_PROLIFERATION | E_RECEPTIVE_SURFACE | inhibition | state_to_state | REF-025;REF-026;REF-028 | 8 | expansion | Persistent proliferation is nonreceptive. |
| EDGE-016 | E_SECRETORY_STATE | E_PODXL | inhibition | state_to_barrier | REF-013;REF-014 | 7 | core_extension | PODXL falls in receptive luminal epithelium. |
| EDGE-017 | E_PODXL | E_RECEPTIVE_SURFACE | inhibition | barrier_to_state | REF-013;REF-014 | 7 | core_extension | Strong human anti-adhesive effect. |
| EDGE-018 | E_SECRETORY_STATE | E_PC6 | activation | state_to_protease | REF-010;REF-011 | 7 | core_extension | Window-specific PC6. |
| EDGE-019 | E_PC6 | E_DAG1_CLEAVED | activation | proteolysis | REF-011 | 8 | core_extension | Direct cleavage evidence. |
| EDGE-020 | E_PC6 | E_DAG1_FULL | inhibition | proteolysis | REF-011 | 8 | core_extension | Removal of alpha-DG N-terminus. |
| EDGE-021 | E_DAG1_FULL | E_RECEPTIVE_SURFACE | inhibition | barrier_to_state | REF-011 | 7 | core_extension | Full-length form blocks attachment. |
| EDGE-022 | E_DAG1_CLEAVED | E_RECEPTIVE_SURFACE | activation | surface_to_state | REF-011 | 7 | core_extension | Barrier release. |
| EDGE-023 | E_SECRETORY_STATE | E_MUC1_BARRIER | inhibition | state_to_glycocalyx | REF-012;REF-025 | 5 | uncertain_variant | Human MUC1 regulation is glycoform-dependent. |
| EDGE-024 | E_SECRETORY_STATE | E_MUC1_SLEX | activation | state_to_glycoform | REF-012 | 5 | uncertain_variant | Requires a glycosylation program not directly measured. |
| EDGE-025 | E_MUC1_BARRIER | E_RECEPTIVE_SURFACE | inhibition | glycocalyx_to_state | REF-012;REF-025 | 6 | core_extension | Anti-adhesive branch. |
| EDGE-026 | E_MUC1_SLEX | E_RECEPTIVE_SURFACE | activation | glycocalyx_to_state | REF-012 | 6 | core_extension | Early-contact rate enhancer. |
| EDGE-027 | IN_HCG | E_CD98_CD9 | activation | external_feedback | REF-008 | 7 | core_extension | Embryo input. |
| EDGE-028 | IN_HCG | E_CDH1_APICAL | activation | external_feedback | REF-019 | 8 | core_extension | Embryo input. |
| EDGE-029 | IN_EMBRYO_CONDITIONED_SIGNAL | E_CDH1_APICAL | activation | external_feedback | REF-019 | 6 | core_extension | Fallback external input. |
| EDGE-030 | E_CD98_CD9 | E_RECEPTIVE_SURFACE | activation | effector_to_state | REF-008 | 7 | core_extension | Use as redundant route/rate modifier. |
| EDGE-031 | E_CDH1_APICAL | E_RECEPTIVE_SURFACE | activation | effector_to_state | REF-019 | 7 | core_extension | Use as first-contact route/rate modifier. |
| EDGE-032 | E_ANXA2_ACTIN | E_RECEPTIVE_SURFACE | activation | effector_to_state | REF-009 | 6 | core_extension | Cytoskeletal rate modifier. |
| EDGE-033 | E_SECRETORY_STATE | E_HBEGF | activation | state_to_growth_factor | REF-006 | 6 | core_extension | Receptive phase association. |
| EDGE-034 | E_HBEGF | E_ITGAVB3_5 | activation | growth_factor_to_effector | REF-007 | 5 | uncertain_variant | Reported regulation in epithelial models. |
| EDGE-035 | E_HBEGF | E_RECEPTIVE_SURFACE | activation | growth_factor_to_state | REF-006;REF-007 | 6 | core_extension | Support/rate modifier. |
| EDGE-036 | E_SPP1_EXPR | E_RECEPTIVE_SURFACE | activation | ligand_to_state | REF-007;REF-015;REF-022 | 6 | existing_plus_extension | Existing baseline ligand; functional contribution remains provisional. |
| EDGE-037 | S_DECIDUALIZED | S_SPP1 | activation | state_to_ligand | REF-017 | 6 | core_extension | Stromal decidual output. |
| EDGE-038 | S_DECIDUALIZED | S_TAZ_ECM | activation | state_to_mechanics | REF-035 | 6 | core_extension | Recent causal evidence. |
| EDGE-039 | S_DECIDUALIZED | S_DECIDUAL_SENESCENCE_BALANCED | activation | state_to_dynamic_program | REF-016 | 6 | expansion | Balanced, time-dependent program. |
| EDGE-040 | S_TAZ_ECM | X_MECHANICAL_PERMISSIVE_ECM | activation | mechanics | REF-035 | 6 | core_extension | ECM remodeling route. |
| EDGE-041 | S_DECIDUAL_SENESCENCE_BALANCED | X_MECHANICAL_PERMISSIVE_ECM | activation | dynamic_matrix | REF-016 | 6 | expansion | Dynamic matrix contribution. |
| EDGE-042 | IN_ER_STRESS_EXCESS | X_MECHANICAL_PERMISSIVE_ECM | inhibition | pathological_input | REF-018 | 6 | core_extension | Excess ER stress prevents normal softening. |
| EDGE-043 | IN_HIGH_ECM_STIFFNESS | X_MECHANICAL_PERMISSIVE_ECM | inhibition | physical_input | REF-018;REF-035 | 5 | core_extension | Coarse Boolean stiffness state. |
| EDGE-044 | E_RECEPTIVE_SURFACE | OUT_MATERNAL_ADHESION_COMPETENCE | activation | latent_to_phenotype | REF-001;REF-020;REF-021 | 7 | core_extension | Epithelial gate. |
| EDGE-045 | S_DECIDUALIZED | OUT_MATERNAL_ADHESION_COMPETENCE | activation | latent_to_phenotype | REF-001;REF-016;REF-020;REF-021 | 7 | core_extension | Stromal gate. |
| EDGE-046 | X_MECHANICAL_PERMISSIVE_ECM | OUT_MATERNAL_ADHESION_COMPETENCE | activation | latent_to_phenotype | REF-016;REF-018;REF-035 | 6 | core_extension | Mechanical stabilization gate or rate modifier. |
| EDGE-047 | OUT_MATERNAL_ADHESION_COMPETENCE | OUT_STABLE_ADHESION | activation | phenotype_to_assay | REF-020 | 9 | existing_core | Requires explicit embryo challenge inputs as in baseline. |
| EDGE-048 | IN_UTERINE_WNT_CUE | IN_TROPHECTODERM_COMPETENT | activation | external_embryo_modifier | REF-034 | 6 | physiboss_later | Maternal cue with embryo-side execution. |
| EDGE-049 | X_LGALS1_3 | E_RECEPTIVE_SURFACE | activation | candidate_interface | REF-015 | 4 | expansion | Computational candidate only. |
| EDGE-050 | X_BSG_ITGB1 | E_RECEPTIVE_SURFACE | activation | candidate_interface | REF-015 | 4 | expansion | Computational candidate only. |

## Candidate MaBoSS architecture

The proposed extension uses three latent states:

1. `E_RECEPTIVE_SURFACE`: epithelial surface/junction/glycocalyx state.
2. `X_MECHANICAL_PERMISSIVE_ECM`: decidual and mechanically dynamic stromal environment.
3. `OUT_MATERNAL_ADHESION_COMPETENCE_EXT`: maternal competence before embryo quality is applied.

A conservative candidate aggregation is:

```text
E_RECEPTIVE_SURFACE =
    E_GP130_STAT3
    AND NOT E_PODXL
    AND NOT E_DAG1_FULL
    AND NOT E_MUC1_BARRIER
    AND at_least_one(CD98/CD9, apical CDH1, ANXA2-actin, HB-EGF,
                     DAG1-cleaved, MUC1-sLeX, integrin, epithelial SPP1)

X_MECHANICAL_PERMISSIVE_ECM =
    S_DECIDUALIZED AND S_TAZ_ECM
    AND NOT IN_ER_STRESS_EXCESS
    AND NOT IN_HIGH_ECM_STIFFNESS

OUT_MATERNAL_ADHESION_COMPETENCE_EXT =
    E_RECEPTIVE_SURFACE
    AND S_DECIDUALIZED
    AND X_MECHANICAL_PERMISSIVE_ECM

OUT_STABLE_ADHESION_EXT =
    OUT_MATERNAL_ADHESION_COMPETENCE_EXT
    AND IN_EMBRYO_PRESENT
    AND IN_TROPHECTODERM_COMPETENT
```

This is a testable candidate, not a claim that every positive effector must be
binary ON. The human surface effectors are better represented as redundant
routes or **rate modifiers**. `candidate-rules.yaml` preserves alternatives.

## Perturbation inventory

| perturbation_id | name | target | action | evidence | expected_effect | refs | confidence | implementation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PERT-001 | Mifepristone | E_PGR;S_PGR | inhibit | direct ADOC | strong decrease in maternal competence and stable adhesion | REF-020 | 9 | existing IN_MIFEPRISTONE input; preserve partial/context-dependent response during calibration |
| PERT-002 | Anti-SPP1 neutralization | free extracellular SPP1 | neutralize | mechanistic hypothesis plus SPP1 literature | decrease one adhesion route but not necessarily abolish adhesion | REF-007;REF-015;REF-017;REF-022 | 6 | existing IN_ANTI_SPP1; never set E_SPP1_EXPR OFF as a surrogate for antibody treatment |
| PERT-003 | LIF or LIFR blockade | E_LIF/E_GP130_STAT3 | inhibit | mouse knockout and human cell-model support | strong decrease in attachment competence | REF-023;REF-030;REF-032;REF-033;REF-038 | 8 | candidate clamp or rate reduction; test epithelial-specific blockade first |
| PERT-004 | STAT3 inhibition | E_GP130_STAT3;S_STAT3 | inhibit | mouse compartment-specific genetics | attachment failure and impaired remodeling | REF-030;REF-031 | 8 | separate epithelial and stromal interventions to preserve stage interpretation |
| PERT-005 | Forced PODXL maintenance/overexpression | E_PODXL | activate | human gain-function | strong decrease in embryo attachment and penetration | REF-013;REF-014 | 7 | force ON or increase OFF-to-ON rate; check barrier/viability counter-readouts |
| PERT-006 | CD98/SLC3A2 knockdown or blocking | E_CD98_CD9 | inhibit | human gain-loss adhesion assay | decreased attachment | REF-008 | 7 | prefer rate modifier rather than sole hard gate |
| PERT-007 | Apical CDH1 blockade/knockdown | E_CDH1_APICAL | inhibit | human blastocyst/spheroid and AFM | decreased first-contact adhesiveness | REF-019 | 7 | do not interpret as global lateral junction disruption unless experiment does so |
| PERT-008 | ANXA2 knockdown or RHOA/actin interference | E_ANXA2_ACTIN | inhibit | human mechanistic cell model | decreased epithelial adhesiveness | REF-009 | 6 | medium-priority rate modifier with cytotoxicity/morphology counter-screen |
| PERT-009 | PCSK5/PC6 inhibition | E_PC6 | inhibit | human knockdown and substrate cleavage | retain DAG1 barrier and reduce attachment | REF-010;REF-011 | 7 | measure alpha-DG-N cleavage product to validate mechanism |
| PERT-010 | MUC1 abundance/glycosylation perturbation | E_MUC1_BARRIER;E_MUC1_SLEX | context_dependent | human force spectroscopy | can decrease or increase adhesion depending on glycoform | REF-012 | 6 | never use a single MUC1 knockout rule; measure glycoform and surface density |
| PERT-011 | SPP1 knockdown | E_SPP1_EXPR or S_SPP1 | inhibit | human epithelial association and stromal mechanistic evidence | decreased adhesion support and/or decidual quality | REF-007;REF-017 | 6 | compartment-specific perturbation required |
| PERT-012 | TAZ/WWTR1 inhibition | S_TAZ_ECM | inhibit | mouse genetics with human-data support | defective ECM remodeling and reduced stabilization | REF-035 | 6 | later extension; measure collagen architecture and mechanics |
| PERT-013 | Excess ER stress (for example thapsigargin) | IN_ER_STRESS_EXCESS | activate_pathology | human stromal mechanobiology | prevent normal softening and impair spheroid adhesion/expansion | REF-018 | 6 | external perturbation input with toxicity controls |
| PERT-014 | Increase ECM stiffness | IN_HIGH_ECM_STIFFNESS | activate_pathology | mechanics synthesis | reduce mechanical permissiveness; effect size requires calibration | REF-018;REF-035 | 5 | prefer continuous PhysiBoSS field or rate scaling over permanent Boolean clamp |
| PERT-015 | HB-EGF/EGFR-family blockade | E_HBEGF | inhibit | human receptive-phase expression and integrin regulation | moderate decrease in receptive surface | REF-006;REF-007 | 5 | test as a secondary, non-hard-gate perturbation |
| PERT-016 | alphaVbeta3/alphaVbeta5 blockade | E_ITGAVB3_5 | inhibit | human/primate/cell-model evidence | decreased interface adhesion | REF-007;REF-022;REF-038 | 6 | clarify maternal versus embryo receptor target in the actual reagent/assay |
| PERT-017 | WNT5A/7A depletion or sFRP2 | IN_UTERINE_WNT_CUE | inhibit | mouse attachment assay | decrease embryo fibronectin-binding competence | REF-034 | 6 | external embryo-competence modifier, not maternal intracellular core logic |
| PERT-018 | Temperature, pH or oxygen excursion | microenvironment | vary | NAM/QC context; little direct adhesion-specific causal evidence in this inventory | unknown direction until measured in ADOC | REF-020;REF-021 | 3 | record as boundary/QC variables; do not invent Boolean edges |

## Physical and environmental factors

| factor_id | factor | normal_or_reference | evidence_for_adhesion | recommended_representation | maboss_action | confidence |
| --- | --- | --- | --- | --- | --- | --- |
| ENV-001 | Temperature | approximately 37 C culture/perfusion context | No robust dose-response for maternal epithelial/stromal adhesion identified in the reviewed corpus. | metadata/QC and later continuous field | No causal edge in core model; define IN_TEMPERATURE_STRESS only after ADOC perturbation data. | 3 |
| ENV-002 | Dissolved oxygen/hypoxia | platform-specific oxygenation | Biologically plausible and monitored in IMPLANT-MOD, but direct adhesion-specific epithelial/stromal thresholds are not established here. | microenvironment boundary condition or PhysiCell substrate | Context input only until measured perturbation data support a sign. | 3 |
| ENV-003 | pH | culture-medium physiological range | No reviewed direct human adhesion dose-response. | QC/boundary variable | Do not create pathway rule yet. | 2 |
| ENV-004 | Flow and shear/flushing | ADOC continuous perfusion; flushing defines stable attachment | Directly part of the assay and attachment-strength validation, but not an intracellular molecular pathway. | assay challenge parameter and later mechanics field | Keep stable adhesion phenotype separate from contact; optionally modify detachment rate outside core Boolean logic. | 8 |
| ENV-005 | ECM/stromal stiffness | donor- and decidual-state-dependent | Human AFM/spheroid and recent TAZ-ECM evidence support a permissive mechanical state. | Boolean coarse state plus continuous PhysiBoSS parameter | Use X_MECHANICAL_PERMISSIVE_ECM and sensitivity ranges. | 6 |
| ENV-006 | ECM ligand presentation | SPP1, fibronectin, laminin/RGD-like motifs | Human/primate/mouse interface evidence supports ligand-specific effects. | extracellular ligand pools | Keep free ligand distinct from expression; future PhysiBoSS spatial fields. | 7 |
| ENV-007 | Hormone sequence and duration | ADOC: E2 2 d, then E2+MPA+cAMP+XAV939 4 d | Direct platform evidence and mifepristone perturbation. | explicit inputs and staged initial conditions | Do not collapse into one receptive input. | 9 |
| ENV-008 | Embryo contact/quality/competence | hatched, viable blastocyst challenge | Directly determines observable adhesion but is outside the current cell-type boundary. | external IN_EMBRYO_PRESENT and IN_TROPHECTODERM_COMPETENT | Never infer maternal failure from a negative adhesion event without embryo-side uncertainty. | 9 |
| ENV-009 | Epithelial polarization and barrier integrity | polarized monolayer with tight junctions and microvilli | ADOC and human surface-mechanism studies. | latent receptive surface plus safety phenotypes | Distinguish physiological remodeling from nonspecific barrier damage. | 8 |
| ENV-010 | PDMS absorption and effective drug/hormone exposure | continuous-flow ADOC device | Technical limitation noted by the ADOC manuscript. | protocol metadata and exposure uncertainty | Do not equate nominal concentration with receptor activity; use uncertainty/sensitivity. | 7 |

Temperature, oxygen and pH are included because they are measurable and could
matter, but they do **not** yet have defensible adhesion-specific Boolean signs
or thresholds in this evidence set. Flow/flushing is an assay/mechanics
parameter; ECM stiffness has stronger mechanistic support and can be introduced
as a coarse Boolean input plus a later continuous PhysiBoSS2 parameter.

## Highest-value ADOC experiments

The most informative common perturbation panel would target **PODXL, CD98,
apical CDH1, ANXA2, PCSK5, MUC1 glycosylation, epithelial and stromal SPP1,
TAZ**, plus LIF/GP130-STAT3 controls. Each should use the same endpoints:
stable attachment after flushing, time to adhesion, embryo area trajectory,
Delta-Z embedding, PAEP, PRL, IGFBP1, barrier integrity/permeability, viability,
reversibility, and—where relevant—AFM or matrix stiffness. Use matched donors
and freeze predictions before experiments.

## Evidence gaps

| gap_id | topic | missing | impact | priority | proposed_resolution |
| --- | --- | --- | --- | --- | --- |
| GAP-001 | Quantitative human kinetics | Compartment-specific rates for P4->IHH, LIF->STAT3 and decidualization->mechanical permissiveness. | Absolute MaBoSS time and transition rates are weakly identifiable. | high | Time-course pSTAT3/IHH/BMP2/HAND2 and matched adhesion imaging in ADOC. |
| GAP-002 | Dose-response | True human embryo adhesion concentration-response for HBEGF, SPP1, CD98, CDH1, PODXL, PCSK5 and ANXA2. | Cannot assign quantitative rate modifiers confidently. | high | Common-dose perturbation panel with the same adhesion endpoints and toxicity controls. |
| GAP-003 | Maternal versus embryo receptor assignment | Several integrin, WNT and ligand mechanisms execute partly on trophectoderm. | Risk of putting embryo biology inside maternal cells. | high | Use external inputs now; add trophoblast only with identifiable embryo data in PhysiBoSS2. |
| GAP-004 | MUC1 state definition | Surface abundance, glycosylation and spatial clearance are not equivalent. | Single-node MUC1 rules can reverse the biological interpretation. | high | Measure glycoforms/sLeX and abundance separately; retain dual nodes. |
| GAP-005 | Stromal mechanics | Donor-specific AFM/hydrogel stiffness linked directly to human blastocyst adhesion is sparse. | Mechanical gate remains qualitative. | high | Paired AFM, stromal state profiling and adhesion assays across donors. |
| GAP-006 | Temperature, oxygen and pH | Adhesion-specific causal curves in ADOC. | Cannot justify direction or thresholds in MaBoSS. | medium | Small factorial perturbation around physiological ranges with viability/barrier counter-readouts. |
| GAP-007 | Barrier versus adhesion | Many perturbations affect junctions, viability or morphology nonspecifically. | False anti-adhesion hits may simply damage epithelium. | high | Always pair adhesion with TEER/permeability, viability and reversibility endpoints. |
| GAP-008 | Donor variability | Current human embryo sample sizes and donor matching are limited. | Network may overfit a pooled average. | high | At least three donors with matched conditions; hierarchical uncertainty and leave-one-donor-out predictions. |
| GAP-009 | Clinical marker prediction | Receptivity marker associations do not imply clinical predictive performance. | Risk of interpreting PAEP/PRL/IGFBP1 or any single marker as implantation outcome. | high | Use markers as internal state observables only; validate stable adhesion separately. |

## Reference inventory

| ref_id | first_author | year | title | journal | species | study_type | doi | pmid | evidence_level | compartment | key_use | url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REF-001 | Muter | 2023 | Human embryo implantation | Development | human | review | 10.1242/dev.201507 |  | consensus | epithelium;stroma | Two-gate framing: epithelial attachment plus stromal decidual support. | https://doi.org/10.1242/dev.201507 |
| REF-002 | Hantak | 2014 | Role of uterine stromal-epithelial crosstalk in embryo implantation | International Journal of Developmental Biology | mouse;human | review | 10.1387/ijdb.130348mb |  | consensus | epithelium;stroma | PGR-IHH-NR2F2-BMP2-HAND2 cross-compartment backbone. | https://doi.org/10.1387/ijdb.130348mb |
| REF-003 | Fukui | 2019 | Uterine receptivity, embryo attachment, and embryo invasion: Multistep processes in embryo implantation | Reproductive Medicine and Biology | mostly mouse | review | 10.1002/rmb2.12280 |  | consensus | epithelium;stroma | Separate receptivity, attachment and invasion; FOXA2-LIF and HAND2/BMI1 context. | https://doi.org/10.1002/rmb2.12280 |
| REF-004 | Craciunas | 2019 | Conventional and modern markers of endometrial receptivity: a systematic review and meta-analysis | Human Reproduction Update | human | systematic_review_meta_analysis | 10.1093/humupd/dmy044 |  | consensus | whole endometrium | Markers are mechanistic/context variables, not reliable standalone clinical predictors. | https://doi.org/10.1093/humupd/dmy044 |
| REF-005 | Hiraoka | 2026 | Toward Implantation-Assisting Technologies: Lessons From In Vivo and Ex Vivo Models | Reproductive Medicine and Biology | mouse;human models | review | 10.1002/rmb2.70042 |  | consensus | epithelium;stroma | Stage-specific interpretation of epithelial attachment and stromal post-attachment support. | https://doi.org/10.1002/rmb2.70042 |
| REF-006 | Leach | 1999 | Heparin-binding EGF-like growth factor cell-specific expression during the human endometrial cycle and early placentation | Journal of Clinical Endocrinology and Metabolism | human | primary_descriptive | 10.1210/jcem.84.9.5980 |  | primary_descriptive | epithelium;decidua | HB-EGF as receptive-phase epithelial support and later decidual signal. | https://doi.org/10.1210/jcem.84.9.5980 |
| REF-007 | Apparao | 2001 | Osteopontin and its receptor alphavbeta3 integrin are coexpressed in the human endometrium during the menstrual cycle but regulated differentially | Journal of Clinical Endocrinology and Metabolism | human | primary_mechanistic_descriptive | 10.1210/jcem.86.10.7906 |  | primary_mechanistic | epithelium | SPP1/OPN-integrin adhesive surface; progesterone and EGF-family regulation. | https://doi.org/10.1210/jcem.86.10.7906 |
| REF-008 | Dominguez | 2010 | Human endometrial CD98 is essential for blastocyst adhesion | PLoS ONE | human epithelial;mouse blastocyst assay | primary_mechanistic | 10.1371/journal.pone.0013380 | 20976164 | primary_mechanistic | epithelium | CD98/CD9 direct gain-loss evidence; induced by hCG, E2, LIF and EGF. | https://doi.org/10.1371/journal.pone.0013380 |
| REF-009 | Garrido-Gomez | 2012 | Annexin A2 is critical for embryo adhesiveness to the human endometrium by RhoA activation through F-actin regulation | FASEB Journal | human cell models | primary_mechanistic | 10.1096/fj.12-204008 |  | primary_mechanistic | epithelium | ANXA2-RHOA-F-actin remodeling as adhesion rate modulator. | https://doi.org/10.1096/fj.12-204008 |
| REF-010 | Heng | 2011 | Proprotein convertase 5/6 is critical for embryo implantation in women: regulating receptivity by cleaving EBP50, modulating ezrin binding, and membrane-cytoskeletal interactions | Endocrinology | human | primary_mechanistic | 10.1210/en.2011-1273 | 21971156 | primary_mechanistic | epithelium;stroma | PCSK5/PC6 controls membrane-cytoskeletal remodeling and attachment. | https://doi.org/10.1210/en.2011-1273 |
| REF-011 | Heng | 2015 | Posttranslational removal of alpha-dystroglycan N terminus by PC5/6 cleavage is important for uterine preparation for embryo implantation in women | FASEB Journal | human | primary_mechanistic | 10.1096/fj.14-269456 | 26077903 | primary_mechanistic | epithelium | Full-length DAG1 is a barrier; PC6 cleavage creates an adhesion-permissive form. | https://doi.org/10.1096/fj.14-269456 |
| REF-012 | Francis | 2021 | Highly glycosylated MUC1 mediates high affinity L-selectin binding | Journal of Nanobiotechnology | human epithelial model | primary_biophysical | 10.1186/s12951-021-00793-9 |  | primary_mechanistic | epithelium | MUC1 has dual behavior: barrier versus glyco-permissive adhesive state. | https://doi.org/10.1186/s12951-021-00793-9 |
| REF-013 | Paule | 2021 | Podocalyxin is a key negative regulator of human endometrial epithelial receptivity for embryo implantation | Human Reproduction | human | primary_mechanistic | 10.1093/humrep/deab032 | 33822049 | primary_mechanistic | epithelium | PODXL is a major anti-adhesive luminal barrier node. | https://doi.org/10.1093/humrep/deab032 |
| REF-014 | Heng | 2021 | Podocalyxin promotes an impermeable epithelium and inhibits pro-implantation factors to negatively regulate endometrial receptivity | Scientific Reports | human epithelial model | primary_mechanistic | 10.1038/s41598-021-03425-2 |  | primary_mechanistic | epithelium | PODXL strengthens tight/adherens-junction barrier and suppresses LIF, WNT and calcium signaling. | https://doi.org/10.1038/s41598-021-03425-2 |
| REF-015 | Koel | 2022 | Human endometrial cell-type-specific RNA sequencing provides new insights into the embryo-endometrium interplay | Human Reproduction Open | human | primary_computational_integrative | 10.1093/hropen/hoac043 | 36339249 | primary_descriptive | epithelium;stroma | LGALS1/3, ITGB1, BSG and SPP1 interaction candidates; 16 paired women and trophectoderm data. | https://doi.org/10.1093/hropen/hoac043 |
| REF-016 | Rawlings | 2021 | Modelling the impact of decidual senescence on embryo implantation in human endometrial assembloids | eLife | human assembloid | primary_mechanistic_platform | 10.7554/eLife.69603 |  | primary_mechanistic | epithelium;stroma | Balanced decidual senescence and dynamic ECM are required; eliminating senescent cells creates a static matrix and failure. | https://doi.org/10.7554/eLife.69603 |
| REF-017 | Wang | 2018 | Role of osteopontin in decidualization and pregnancy success | Reproduction | human | primary_mechanistic_clinical | 10.1530/REP-17-0782 |  | primary_mechanistic | stroma | Stromal SPP1 promotes decidual and angiogenic programs and is lower in implantation failure. | https://doi.org/10.1530/REP-17-0782 |
| REF-018 | Schafir | 2026 | How decidualization dysregulation reshapes the nanomechanics of endometrial stromal cells | Molecular Human Reproduction | human stromal model | primary_mechanobiology | 10.1093/molehr/gaag037 |  | primary_mechanistic | stroma | Decidualization-associated softening; excess ER stress prevents softening and impairs spheroid adhesion/expansion. | https://doi.org/10.1093/molehr/gaag037 |
| REF-019 | Ruan | 2026 | Free apical surface hetero-cellular CDH1 homophilic binding is a major mediator of blastocyst-endometrium interaction in humans | Human Reproduction | human | primary_mechanistic_biophysical | 10.1093/humrep/deag009 | 41704048 | primary_mechanistic | epithelium | Embryo/hCG induces apical CDH1 and CTNND1; blocking/knockdown reduces adhesion. | https://doi.org/10.1093/humrep/deag009 |
| REF-020 | Zaragozano | 2026 | Modeling human embryo adhesion using a microfluidic platform | Science Advances | human ADOC;mouse validation | primary_platform_mechanistic | 10.1126/sciadv.adz2249 |  | direct_human_adhesion | epithelium;stroma | Best direct human calibration: 9/19 HT, 0/12 untreated, 1/8 mifepristone; mean attachment 34.1 +/- 12.2 h. | https://doi.org/10.1126/sciadv.adz2249 |
| REF-021 | Mole | 2026 | Modeling human embryo implantation in vitro | Cell | human embryo;endometrial model | primary_high_fidelity_platform | 10.1016/j.cell.2025.10.027 |  | primary_mechanistic | epithelium;stroma | Strong support for explicit stromal coupling and interface perturbation in a human implantation model. | https://doi.org/10.1016/j.cell.2025.10.027 |
| REF-022 | Fazleabas | 1997 | Distribution of integrins and the extracellular matrix proteins in the baboon endometrium during the menstrual cycle and early pregnancy | Biology of Reproduction | baboon | primary_comparative | 10.1095/biolreprod56.2.348 | 9116133 | primary_descriptive | epithelium;stroma | Primate support for OPN-integrin and fibronectin/ECM modules. | https://doi.org/10.1095/biolreprod56.2.348 |
| REF-023 | Stewart | 1992 | Blastocyst implantation depends on maternal expression of leukaemia inhibitory factor | Nature | mouse | maternal_knockout | 10.1038/359076a0 | 1522892 | foundational_causal | glandular epithelium | Maternal LIF is an essential attachment trigger. | https://doi.org/10.1038/359076a0 |
| REF-024 | Shen | 1992 | Leukemia inhibitory factor is expressed by the preimplantation uterus and selectively blocks primitive ectoderm formation in vitro | Proceedings of the National Academy of Sciences USA | mouse | primary_descriptive | 10.1073/pnas.89.17.8240 | 1518852 | primary_descriptive | uterine epithelium | Temporal uterine LIF activation before implantation. | https://doi.org/10.1073/pnas.89.17.8240 |
| REF-025 | Franco | 2010 | Ablation of Indian hedgehog in the murine uterus results in aberrant estrogen signaling and infertility | Biology of Reproduction | mouse | uterine_conditional_knockout | 10.1095/biolreprod.109.080259 |  | foundational_causal | epithelium to stroma | IHH loss causes attachment failure, high epithelial estrogenic signaling and MUC1 persistence. | https://doi.org/10.1095/biolreprod.109.080259 |
| REF-026 | Kurihara | 2007 | COUP-TFII mediates progesterone regulation of uterine implantation by controlling ER activity | PLoS Genetics | mouse | uterine_conditional_knockout | 10.1371/journal.pgen.0030102 |  | foundational_causal | stroma to epithelium | NR2F2 relay downstream of IHH, upstream of BMP2, restraining epithelial estrogenic nonreceptivity. | https://doi.org/10.1371/journal.pgen.0030102 |
| REF-027 | Lee | 2007 | Bmp2 is critical for the murine uterine decidual response | Molecular and Cellular Biology | mouse | uterine_conditional_knockout | 10.1128/MCB.00342-07 |  | foundational_causal | stroma | BMP2 is essential for decidual support; initial attachment may precede stromal failure. | https://doi.org/10.1128/MCB.00342-07 |
| REF-028 | Li | 2011 | The antiproliferative action of progesterone in uterine epithelium is mediated by Hand2 | Science | mouse | uterine_conditional_knockout | 10.1126/science.1197454 | 21330545 | foundational_causal | stroma to epithelium | HAND2 suppresses stromal FGFs and epithelial estrogen-driven proliferation. | https://doi.org/10.1126/science.1197454 |
| REF-029 | Huyen | 2011 | Evidence for a conserved function of heart and neural crest derivatives expressed transcript 2 in mouse and human decidualization | Reproduction | mouse;human | primary_mechanistic | 10.1530/REP-11-0060 | 21527398 | primary_mechanistic | stroma | Conserved HAND2 induction and requirement in decidualization. | https://doi.org/10.1530/REP-11-0060 |
| REF-030 | Pawar | 2013 | STAT3 regulates uterine epithelial remodeling and epithelial-stromal crosstalk during implantation | Molecular Endocrinology | mouse | epithelial_conditional_knockout | 10.1210/me.2013-1206 |  | foundational_causal | epithelium;stroma | STAT3 controls epithelial junction remodeling and paracrine support. | https://doi.org/10.1210/me.2013-1206 |
| REF-031 | Hiraoka | 2020 | Differential roles of uterine epithelial and stromal STAT3 coordinate uterine receptivity and embryo attachment | Scientific Reports | mouse | compartment_specific_knockouts | 10.1038/s41598-020-72640-0 |  | foundational_causal | epithelium;stroma | Represent epithelial and stromal STAT3 separately. | https://doi.org/10.1038/s41598-020-72640-0 |
| REF-032 | Namiki | 2023 | Uterine epithelial Gp130 orchestrates hormone response and epithelial remodeling for successful embryo attachment in mice | Scientific Reports | mouse | epithelial_conditional_knockout | 10.1038/s41598-023-27859-y |  | foundational_causal | epithelium | GP130 is essential; connects hormone response to SNAI1-like epithelial remodeling. | https://doi.org/10.1038/s41598-023-27859-y |
| REF-033 | Aikawa | 2024 | Spatiotemporal functions of leukemia inhibitory factor in embryo attachment and implantation chamber formation | Cell Death Discovery | mouse | uterine_and_epithelial_knockouts | 10.1038/s41420-024-02228-4 | 39587062 | foundational_causal | epithelium;stroma | Pre-attachment epithelial LIF-STAT3 and later stromal LIF have distinct temporal roles. | https://doi.org/10.1038/s41420-024-02228-4 |
| REF-034 | Lou | 2023 | Uterine WNTS modulates fibronectin binding activity required for blastocyst attachment through the WNT/Ca2+ signaling pathway in mice | Reproductive Biology and Endocrinology | mouse | primary_mechanistic | 10.1186/s12958-023-01135-0 |  | primary_mechanistic | maternal cue;embryo execution | WNT5A/7A uterine cue controls embryo integrin trafficking; external cue in maternal-only model. | https://doi.org/10.1186/s12958-023-01135-0 |
| REF-035 | He | 2026 | TAZ integrates ECM remodeling with uterine stromal differentiation | Proceedings of the National Academy of Sciences USA | mouse;human datasets | uterine_genetics_and_integrative | 10.1073/pnas.2528309123 |  | primary_mechanistic | stroma | TAZ/WWTR1 coordinates collagen/ECM remodeling and decidual function. | https://doi.org/10.1073/pnas.2528309123 |
| REF-036 | Cullinan | 1996 | Leukemia inhibitory factor and LIF receptor expression in human endometrium suggests a potential autocrine/paracrine function in regulating embryo implantation | Proceedings of the National Academy of Sciences USA | human | primary_descriptive | 10.1073/pnas.93.7.3115 | 8610178 | primary_descriptive | glandular epithelium | Human secretory-phase LIF/LIFR/GP130 expression support. | https://doi.org/10.1073/pnas.93.7.3115 |
| REF-037 | Huang | 2018 | Increased KLF12 impairs embryo attachment via downregulation of leukemia inhibitory factor in women with recurrent implantation failure | Cell Death Discovery | human | primary_mechanistic_clinical | 10.1038/s41420-018-0088-8 | 30109142 | primary_mechanistic | epithelium | KLF12 as a negative upstream regulator of LIF; extension candidate. | https://doi.org/10.1038/s41420-018-0088-8 |
| REF-038 | Chung | 2016 | Integrin alphaVbeta3 and alphaVbeta5 are required for leukemia inhibitory factor-mediated adhesion of trophoblast cells to endometrial cells | Biochemical and Biophysical Research Communications | human cell models | primary_mechanistic | 10.1016/j.bbrc.2015.12.103 | 26723254 | primary_mechanistic | epithelium;interface | LIF-to-integrin connection and attachment in human cell models. | https://doi.org/10.1016/j.bbrc.2015.12.103 |

## Source provenance

| source_id | title | source_type | status | role | location | notes |
| --- | --- | --- | --- | --- | --- | --- |
| SRC-001 | Embryo Adhesion in Endometrial Epithelium and Stroma for MaBoSS | derived_deep_research_report | input synthesis | Base literature inventory and prior mechanistic synthesis | ChatGPT File Library; not duplicated as a binary file in this archive | All scientific claims were decomposed into REF-* entries and candidate mechanism rows. |
| SRC-002 | IMPLANT-MOD Part B | project_proposal_pdf | non-peer-reviewed project context | ADOC/INVADE/PhysiBoSS2 scope, readout strategy, biosensing and physical boundary context | User-provided IMPLANT-MOD_PartB.pdf; excluded from share archive by source-data policy | Used for platform architecture and context, not as causal molecular evidence. |
| SRC-003 | Modeling human embryo adhesion using a microfluidic platform - local manuscript and supplement | local_manuscript_sources | source documents | ADOC protocol, endpoints, calibration counts and assay definitions | Original repository data paths referenced in config/data_manifest.tsv; binaries excluded from share archive | Final scientific citation is REF-020. |
| SRC-004 | Consensus and primary-source metadata verification | search_provenance | completed 2026-07-26 | Locate literature and verify recent publication metadata/DOIs | External search results are represented by canonical DOI/PMID URLs in references.tsv | This package is comprehensive for the prior report scope but is not claimed to be a PRISMA-complete systematic review. |

## Implementation boundary

The executable baseline was **not** modified. This package is additive under
`context/literature/` and `models/extended/adoc-literature-v0.1.0/`. Codex must
promote only reviewed nodes/edges into `models/specs/`, preserve construction /
calibration / validation separation, and retain uncertain alternatives rather
than silently choosing one topology.
