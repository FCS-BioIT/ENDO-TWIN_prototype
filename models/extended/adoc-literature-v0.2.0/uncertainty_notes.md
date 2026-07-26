# Uncertainty Notes

## Executable assumptions retained

- `X_INTERFACE_SPP1_RELAY`, `X_INTERFACE_REDUNDANT_RELAY`,
  `X_INTERFACE_ANTIADHESIVE_RELAY`, and `X_MECHANICAL_STRESS_RELAY` are bounded
  structural uncertainty nodes. They represent unresolved route efficiency or
  sensitivity, not resolved molecular species.
- All transition rates remain implicit MaBoSS defaults. No physical time unit,
  rate ordering, or fitted kinetic parameter is introduced here.
- `IN_HIGH_ECM_STIFFNESS` and `IN_ER_STRESS_EXCESS` are coarse Boolean
  sensitivity inputs. The literature package supports adverse directional
  effects, not a calibrated mechanical threshold.

## Promoted but still provisional mechanisms

- `E_LIF -> E_GP130_STAT3` is promoted because it is the strongest maternal
  attachment-gate candidate in the literature package, but its executable use
  still mixes strong nonhuman causal evidence with weaker direct human
  perturbation evidence.
- `E_PODXL`, `E_PC6`, `E_DAG1_FULL`, `E_DAG1_CLEAVED`, `E_MUC1_BARRIER`, and
  `E_MUC1_SLEX` are promoted as a compact human epithelial barrier-release
  module without attempting to model broader glycocalyx or protease kinetics.
- `E_CD98_CD9`, `E_ANXA2_ACTIN`, `E_HBEGF`, `E_CDH1_APICAL`, `S_HAND2`,
  stromal `S_SPP1`, and `S_TAZ_ECM` are included as supportive maternal routes,
  not as individually necessary gates.
- In the default comparator, `S_HAND2` is recorded but does not alter
  downstream logic; only the stricter IHH uncertainty variant makes HAND2 a
  functional requirement downstream of `S_BMP2`.
- In the default comparator, `E_CDH1_APICAL` remains contact-gated. Alternate
  uncertainty variants may combine maternal priming with `IN_HCG` or
  `IN_EMBRYO_CONDITIONED_SIGNAL`, but no variant introduces an
  `E_CDH1_APICAL` self-loop.
- `X_MECHANICAL_PERMISSIVE_ECM` is implemented as a bounded adverse modifier via
  `X_MECHANICAL_STRESS_RELAY` so that ER stress and stiffness reduce, rather
  than deterministically abolish, competence trajectories.

## Alternatives kept out of the executable core

- Direct downstream hCG or embryo-conditioned induction of maternal epithelial
  effectors in the required condition suite.
- The stricter `IN_XAV939 -> E_AXIN -> E_SECRETORY_STATE` gate from the parent
  uncertainty catalog.
- Explicit trophoblast, immune, endothelial, senescence, barrier-damage, and
  viability subnetworks.
- Quantitative mechanobiology or spatial ECM formulations beyond the bounded
  relay abstraction used here.
