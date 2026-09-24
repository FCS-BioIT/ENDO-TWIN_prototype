# Gate 3a — which maternal observation separates each candidate variant

> **Generated file — do not edit.** Regenerate with `pixi run build-variant-discrimination`. Computed by applying each variant's rule change to the committed `adoc-literature-superset-v0.4.0` network in memory and comparing predictions across every recorded arm.

`adhesion_objective` is `diagnostic_ordinal`, so **no fitted score exists**. A candidate can only be preferred because an observation distinguishes it, and this table is that test.

Three distinctions are kept separate, because collapsing any of them overstates a candidate:

1. **Structural vs experimental.** A variant can add a distinct Boolean function to the partition and still be unseparable from v0.4 in every arm anyone can run, because the input it newly reads is off in all of them. `CD98-b` is exactly that.
2. **Current arms vs a new controlled input.** A variant that introduces a supplied ligand or a construct is *not* discriminable today; it is discriminable in an experiment that does not yet exist. Those inputs are **conditioned on, never marginalised** — averaging over "IL-11 supplied" and "IL-11 absent" yields a number no experiment can produce.
3. **Model state vs readout, in three tiers, not two.** A difference in a node nothing can assay is a difference between two model states. But "measurable" is not one thing: a node can be mapped by the observation layer and still not be usable to validate it. The tiers are derived from the map, never asserted:

| Pair | Axis | Verdict | Separating nodes | Usable assay | Mapped composite | Controlled inputs varied |
|---|---|---|---|---|---|---|
| CD98-a vs CD98-b | CD98 | **REQUIRES_A_NEW_CONTROLLED_INPUT** | `E_CD98_CD9` | **none** | — | `IN_HCG` |
| CD98-a vs CD98-c | CD98 | **DISCRIMINABLE_IN_CURRENT_ARMS_EMBRYO_FREE_OPPOSITE** | `E_CD98_CD9` | **none** | — | `IN_HCG` |
| CD98-b vs CD98-c | CD98 | **DISCRIMINABLE_IN_CURRENT_ARMS_EMBRYO_FREE_OPPOSITE** | `E_CD98_CD9` | **none** | — | `IN_HCG` |
| CD98-a vs CD98-d | CD98 | **REQUIRES_A_NEW_CONTROLLED_INPUT** | `E_CD98_CD9` | **none** | — | `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_HCG` |
| CD98-b vs CD98-d | CD98 | **REQUIRES_A_NEW_CONTROLLED_INPUT** | `E_CD98_CD9` | **none** | — | `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_HCG` |
| CDH1-a vs CDH1-b | CDH1 | **DISCRIMINABLE_IN_CURRENT_ARMS_ONLY_WITH_EMBRYOS** | `E_CDH1_APICAL` | **none** | — | `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_HCG` |
| CDH1-b vs CDH1-c | CDH1 | **DISCRIMINABLE_IN_CURRENT_ARMS_ONLY_WITH_EMBRYOS** | `E_CDH1_APICAL` | **none** | — | `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_HCG` |
| GP130-a vs GP130-b | GP130/STAT3 | **REQUIRES_A_NEW_CONTROLLED_INPUT** | `E_CD98_CD9`, `E_GP130_STAT3`, `E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE` | **none** | `OUT_EPITHELIAL_RECEPTIVE` | `X_IL11` |
| PC6-a vs PC6-b | PC6/DAG1 | **REQUIRES_A_NEW_CONTROLLED_INPUT** | `E_DAG1_CLEAVED`, `E_DAG1_FULL`, `E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE` | **none** | `OUT_EPITHELIAL_RECEPTIVE` | `E_DAG1_CLEAVABLE` |

## CD98-a vs CD98-b

**Verdict:** `REQUIRES_A_NEW_CONTROLLED_INPUT`

**Controlled inputs varied:** `IN_HCG`. Each setting below is a distinct experiment. The setting marked *current design* is the one the existing arms already run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only the other settings separate the pair.

> **No separating node is in the observation layer at all.** Every discrimination below needs a readout ADOC has never measured, so the experiment must be costed as a new assay.

### Setting: IN_HCG=absent [current design]

No maternal node differs in any recorded arm under this setting.

### Setting: IN_HCG=present [INTERVENTION]

| Arm | Node | CD98-a | CD98-b | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_basal` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_CD98_CD9` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `basal_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CD98_CD9` | 0.5 | 1.0 | yes | no | `no_assay` |

## CD98-a vs CD98-c

**Verdict:** `DISCRIMINABLE_IN_CURRENT_ARMS_EMBRYO_FREE_OPPOSITE`

**Controlled inputs varied:** `IN_HCG`. Each setting below is a distinct experiment. The setting marked *current design* is the one the existing arms already run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only the other settings separate the pair.

> **No separating node is in the observation layer at all.** Every discrimination below needs a readout ADOC has never measured, so the experiment must be costed as a new assay.

### Setting: IN_HCG=absent [current design]

| Arm | Node | CD98-a | CD98-c | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_hormone_treated` | `E_CD98_CD9` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CD98_CD9` | 0.5 | 1.0 | yes | no | `no_assay` |

### Setting: IN_HCG=present [INTERVENTION]

| Arm | Node | CD98-a | CD98-c | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_basal` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_CD98_CD9` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `basal_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CD98_CD9` | 0.5 | 1.0 | yes | no | `no_assay` |

## CD98-b vs CD98-c

**Verdict:** `DISCRIMINABLE_IN_CURRENT_ARMS_EMBRYO_FREE_OPPOSITE`

**Controlled inputs varied:** `IN_HCG`. Each setting below is a distinct experiment. The setting marked *current design* is the one the existing arms already run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only the other settings separate the pair.

> **No separating node is in the observation layer at all.** Every discrimination below needs a readout ADOC has never measured, so the experiment must be costed as a new assay.

### Setting: IN_HCG=absent [current design]

| Arm | Node | CD98-b | CD98-c | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_hormone_treated` | `E_CD98_CD9` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CD98_CD9` | 0.5 | 1.0 | yes | no | `no_assay` |

### Setting: IN_HCG=present [INTERVENTION]

No maternal node differs in any recorded arm under this setting.

## CD98-a vs CD98-d

**Verdict:** `REQUIRES_A_NEW_CONTROLLED_INPUT`

**Controlled inputs varied:** `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_HCG`. Each setting below is a distinct experiment. The setting marked *current design* is the one the existing arms already run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only the other settings separate the pair.

> **No separating node is in the observation layer at all.** Every discrimination below needs a readout ADOC has never measured, so the experiment must be costed as a new assay.

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=absent [current design], IN_HCG=absent [current design]

No maternal node differs in any recorded arm under this setting.

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=absent [current design], IN_HCG=present [INTERVENTION]

| Arm | Node | CD98-a | CD98-d | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_basal` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_CD98_CD9` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `basal_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CD98_CD9` | 0.5 | 1.0 | yes | no | `no_assay` |

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=present [INTERVENTION], IN_HCG=absent [current design]

| Arm | Node | CD98-a | CD98-d | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_basal` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_CD98_CD9` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `basal_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CD98_CD9` | 0.5 | 1.0 | yes | no | `no_assay` |

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=present [INTERVENTION], IN_HCG=present [INTERVENTION]

| Arm | Node | CD98-a | CD98-d | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_basal` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_CD98_CD9` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `basal_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CD98_CD9` | 0.5 | 1.0 | yes | no | `no_assay` |

## CD98-b vs CD98-d

**Verdict:** `REQUIRES_A_NEW_CONTROLLED_INPUT`

**Controlled inputs varied:** `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_HCG`. Each setting below is a distinct experiment. The setting marked *current design* is the one the existing arms already run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only the other settings separate the pair.

> **No separating node is in the observation layer at all.** Every discrimination below needs a readout ADOC has never measured, so the experiment must be costed as a new assay.

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=absent [current design], IN_HCG=absent [current design]

No maternal node differs in any recorded arm under this setting.

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=absent [current design], IN_HCG=present [INTERVENTION]

No maternal node differs in any recorded arm under this setting.

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=present [INTERVENTION], IN_HCG=absent [current design]

| Arm | Node | CD98-b | CD98-d | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_basal` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_CD98_CD9` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `basal_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CD98_CD9` | 0.5 | 1.0 | yes | no | `no_assay` |

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=present [INTERVENTION], IN_HCG=present [INTERVENTION]

No maternal node differs in any recorded arm under this setting.

## CDH1-a vs CDH1-b

**Verdict:** `DISCRIMINABLE_IN_CURRENT_ARMS_ONLY_WITH_EMBRYOS`

**Controlled inputs varied:** `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_HCG`. Each setting below is a distinct experiment. The setting marked *current design* is the one the existing arms already run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only the other settings separate the pair.

> **No separating node is in the observation layer at all.** Every discrimination below needs a readout ADOC has never measured, so the experiment must be costed as a new assay.

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=absent [current design], IN_HCG=absent [current design]

| Arm | Node | CDH1-a | CDH1-b | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_basal` | `E_CDH1_APICAL` | 1.0 | 0.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_CDH1_APICAL` | 1.0 | 0.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CDH1_APICAL` | 1.0 | 0.0 | no | **yes** | `no_assay` |

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=absent [current design], IN_HCG=present [INTERVENTION]

| Arm | Node | CDH1-a | CDH1-b | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `basal_maternal` | `E_CDH1_APICAL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CDH1_APICAL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CDH1_APICAL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=present [INTERVENTION], IN_HCG=absent [current design]

| Arm | Node | CDH1-a | CDH1-b | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `basal_maternal` | `E_CDH1_APICAL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CDH1_APICAL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CDH1_APICAL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=present [INTERVENTION], IN_HCG=present [INTERVENTION]

| Arm | Node | CDH1-a | CDH1-b | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `basal_maternal` | `E_CDH1_APICAL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CDH1_APICAL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CDH1_APICAL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |

## CDH1-b vs CDH1-c

**Verdict:** `DISCRIMINABLE_IN_CURRENT_ARMS_ONLY_WITH_EMBRYOS`

**Controlled inputs varied:** `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_HCG`. Each setting below is a distinct experiment. The setting marked *current design* is the one the existing arms already run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only the other settings separate the pair.

> **No separating node is in the observation layer at all.** Every discrimination below needs a readout ADOC has never measured, so the experiment must be costed as a new assay.

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=absent [current design], IN_HCG=absent [current design]

| Arm | Node | CDH1-b | CDH1-c | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_basal` | `E_CDH1_APICAL` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_CDH1_APICAL` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CDH1_APICAL` | 0.0 | 1.0 | no | **yes** | `no_assay` |

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=absent [current design], IN_HCG=present [INTERVENTION]

No maternal node differs in any recorded arm under this setting.

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=present [INTERVENTION], IN_HCG=absent [current design]

No maternal node differs in any recorded arm under this setting.

### Setting: IN_EMBRYO_CONDITIONED_SIGNAL=present [INTERVENTION], IN_HCG=present [INTERVENTION]

No maternal node differs in any recorded arm under this setting.

## GP130-a vs GP130-b

**Verdict:** `REQUIRES_A_NEW_CONTROLLED_INPUT`

**Controlled inputs varied:** `X_IL11`. Each setting below is a distinct experiment. The setting marked *current design* is the one the existing arms already run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only the other settings separate the pair.

> **No separating node has a usable assay.** `OUT_EPITHELIAL_RECEPTIVE` is mapped by the observation layer, but at a tier the map itself says cannot validate the node, so it does not make this discrimination runnable today.

### Setting: X_IL11=absent [current design]

No maternal node differs in any recorded arm under this setting.

### Setting: X_IL11=present [INTERVENTION]

| Arm | Node | GP130-a | GP130-b | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_basal` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_basal` | `E_GP130_STAT3` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_CD98_CD9` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_GP130_STAT3` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_RECEPTIVE_SURFACE` | 0.5 | 1.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated` | `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 1.0 | no | no | `mapped_composite_not_validating` — multi_analyte_composite:PAEP;SPP1;DPP4;CEACAM5;CEACAM6 [reported_only, confidence=low, source_rows_n=0] |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_CD98_CD9` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated_mifepristone` | `E_GP130_STAT3` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `basal_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `basal_maternal` | `E_GP130_STAT3` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_CD98_CD9` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `e2_primed_maternal` | `E_GP130_STAT3` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_CD98_CD9` | 0.5 | 1.0 | yes | no | `no_assay` |
| `hormone_treated_maternal` | `E_GP130_STAT3` | 0.5 | 1.0 | yes | no | `no_assay` |
| `hormone_treated_maternal` | `E_RECEPTIVE_SURFACE` | 0.5 | 1.0 | yes | no | `no_assay` |
| `hormone_treated_maternal` | `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 1.0 | yes | no | `mapped_composite_not_validating` — multi_analyte_composite:PAEP;SPP1;DPP4;CEACAM5;CEACAM6 [reported_only, confidence=low, source_rows_n=0] |

## PC6-a vs PC6-b

**Verdict:** `REQUIRES_A_NEW_CONTROLLED_INPUT`

**Controlled inputs varied:** `E_DAG1_CLEAVABLE`. Each setting below is a distinct experiment. The setting marked *current design* is the one the existing arms already run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only the other settings separate the pair.

> **No separating node has a usable assay.** `OUT_EPITHELIAL_RECEPTIVE` is mapped by the observation layer, but at a tier the map itself says cannot validate the node, so it does not make this discrimination runnable today.

### Setting: E_DAG1_CLEAVABLE=absent [INTERVENTION]

| Arm | Node | PC6-a | PC6-b | embryo-free | opposite | readout tier |
|---|---|---|---|---|---|---|
| `adhesion_challenge_hormone_treated` | `E_DAG1_CLEAVED` | 1.0 | 0.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_DAG1_FULL` | 0.0 | 1.0 | no | **yes** | `no_assay` |
| `adhesion_challenge_hormone_treated` | `E_RECEPTIVE_SURFACE` | 0.5 | 0.0 | no | no | `no_assay` |
| `adhesion_challenge_hormone_treated` | `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 0.0 | no | no | `mapped_composite_not_validating` — multi_analyte_composite:PAEP;SPP1;DPP4;CEACAM5;CEACAM6 [reported_only, confidence=low, source_rows_n=0] |
| `hormone_treated_maternal` | `E_DAG1_CLEAVED` | 1.0 | 0.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_DAG1_FULL` | 0.0 | 1.0 | yes | **yes** | `no_assay` |
| `hormone_treated_maternal` | `E_RECEPTIVE_SURFACE` | 0.5 | 0.0 | yes | no | `no_assay` |
| `hormone_treated_maternal` | `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 0.0 | yes | no | `mapped_composite_not_validating` — multi_analyte_composite:PAEP;SPP1;DPP4;CEACAM5;CEACAM6 [reported_only, confidence=low, source_rows_n=0] |

### Setting: E_DAG1_CLEAVABLE=present [current design]

No maternal node differs in any recorded arm under this setting.

## Variants excluded from this computation

* **EPAC** — recorded in the candidate table as a pass-through that leaves the partition at 35 -> 35; Kusama 2013 shows graded potentiation, which a rate-free Boolean model cannot express at all
* **HH-reception** — pass-through, 35 -> 35, and blocked on GAP-014: no free stromal competence determinant exists that is not invented
* **IGFBP1-fb** — introduces a cycle among 14 nodes, which the structural enumerator refuses to evaluate; separately blocked on calibration leakage because S_IGFBP1 carries an observation-map role

> **Excluding `IGFBP1-fb` does NOT close the PRL/IGFBP1 Gate-3a task.** What is excluded is one proposed *repair* — adding `S_IGFBP1` as an input to `S_DECIDUALIZED` — because it creates a 14-node cycle the enumerator cannot evaluate and because `S_IGFBP1` carries an observation-map role, so an outgoing causal edge would make the model that interprets that measurement depend on it. The underlying problem is untouched and is live: `S_PRL = S_IGFBP1 = S_DECIDUALIZED` share one rule, one initial state and one default rate, so their onset distributions are identical by construction, and the recorded IGFBP-1-before-PRL onset order is something the model cannot express at all. That axis is also the **only** one whose nodes the observation layer actually measures.

## Family members proposed and deliberately not written

* **GP130-d (convergent-plus-an-IL11-specific-arm)** — TI002 asks for the GP130 family to be carried as convergent-only VERSUS convergent-plus-an-IL11-specific-arm, because Marwood 2009 shows the two ligands dissociate DOWNSTREAM of STAT3 -- IL-11 stimulates trophoblast attachment where LIF does not, and alpha2beta1 blockade reduces the LIF but not the IL-11 collagen-IV response. U4 read the paper named as most likely to supply the missing executor, Yap/Dimitriadis 2011 (PMID 21619711), in full. It identifies ANXA2 and FLOT1 as IL-11-regulated plasma-membrane proteins, and ANXA2 is already a committed node -- so the arm could be written in one line as `E_ANXA2_ACTIN = E_SECRETORY_STATE or X_IL11`, which would also break it out of the nine-member AC01 class. It is not written, because that paper runs NO LIF COMPARATOR and NO ADHESION OR ATTACHMENT ENDPOINT: it cannot establish that either protein is IL-11-SPECIFIC, which is the entire content of the second family member, and it measures membrane ABUNDANCE where the node is an actin-remodelling state. Writing it would invent the functional link, which is what GP130-b's own limitation column already says must not be done. So the family is single-membered for want of a representable alternative, NOT because the evidence chose between the two. See docs/v05_u4_gp130_axis.md.

## Embryo-free arms

A discrimination available in one of these avoids the attachment assay entirely: `basal_maternal`, `e2_primed_maternal`, `hormone_treated_maternal`

