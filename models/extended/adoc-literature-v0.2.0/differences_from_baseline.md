# Differences From `adoc-core-v0.1.0`

## New executable nodes

- Inputs: `IN_HCG`, `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_ER_STRESS_EXCESS`,
  `IN_HIGH_ECM_STIFFNESS`.
- Epithelial mechanism: `E_LIF`, `E_GP130_STAT3`, `E_PODXL`, `E_PC6`,
  `E_DAG1_FULL`, `E_DAG1_CLEAVED`, `E_MUC1_BARRIER`, `E_MUC1_SLEX`,
  `E_HBEGF`, `E_ITGAVB3_5`, `E_CD98_CD9`, `E_ANXA2_ACTIN`,
  `E_CDH1_APICAL`, `E_RECEPTIVE_SURFACE`.
- Stromal or extracellular mechanism: `S_TAZ_ECM`,
  `X_MECHANICAL_STRESS_RELAY`, `X_MECHANICAL_PERMISSIVE_ECM`.

## Refined logic

- `OUT_EPITHELIAL_RECEPTIVE` now requires both the inherited secretory program
  and the promoted receptive-surface state.
- `OUT_MATERNAL_ADHESION_COMPETENCE` now reads directly from mechanistic
  receptive and decidual states so sequential continuation does not depend on
  carrying downstream PAEP, PRL, or IGFBP1 reporting nodes through joint
  memory.
- Maternal interface logic is decomposed into explicit SPP1-linked, redundant
  positive, and anti-adhesive routes so anti-SPP1 reduces one route rather than
  forcing competence to zero.
- ER stress and excessive stiffness now reduce competence through the bounded
  `X_MECHANICAL_STRESS_RELAY` instead of a deterministic kill switch.
- External hCG and embryo-conditioned signals remain available as optional
  inputs but are not required in the executable challenge suite.

## Inherited structures left unchanged

- External embryo presence and trophectoderm competence remain explicit gates.
- Anti-SPP1 still acts on free extracellular `SPP1`, not transcription.
- The bounded interface relay nodes remain the mechanism used to keep
  anti-SPP1 effects partial rather than absolute.
- No explicit trophoblast, immune, endothelial, viability, or barrier-damage
  subnetwork is introduced.
