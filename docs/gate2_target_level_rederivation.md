# Gate 2 separability, re-derived against a closed target-level vocabulary

> **Generated file — do not edit.** Regenerate with `pixi run build-target-level-rederivation`. Computed by running `coupling.perturbation_separability` twice over the same Boolean-function classes of `adoc-literature-superset-v0.4.0` — once with the catalog's free-text `target_class`, once with a closed vocabulary of biological levels.

`drug_target_catalog.tsv` types **29** executable targets with **21** distinct free-text values. DTR020 rates the free text this repository's most important catalog defect, because which merges trip the criterion then follows naming granularity. This re-derives the criterion on **12** of the 13 declared biological levels and surfaces every changed verdict.

**A smaller exposure than the catalog defect.** DTR020 and the plan's section 4.2 both count **34 rows, 24 distinct values**, which is the whole catalog. The criterion reads only rows with `execution_status = executable`, so what it can actually see is **29 rows, 21 values**: the 5 non-executable rows carry `dynamic_matrix_regulator`, `candidate_effector` and `external_input`, three values no separability verdict has ever depended on. The defect is real; its reach through this criterion is narrower than the headline count implies.

## Result

**No node changes verdict.** Every separability signal the criterion reports is the same under the closed vocabulary as under the free text.

That is a weak result on its own — a vocabulary is a judgement, and one chosen after seeing the answer could reproduce it. What follows is the part that is not a judgement: **how far each signal is from flipping**, computed as the minimum number of catalogued class members that would have to be relabelled.

## Where the typing is load-bearing

Only a Boolean-function class with at least two catalogued members can be affected by any typing at all. There are **5** of them.

| Class members | levels | verdict | relabellings to flip |
|---|---|---|---|
| `E_DAG1_FULL`, `E_MUC1_BARRIER`, `E_PODXL` | `surface_molecule`, `surface_molecule`, `surface_molecule` | `MERGES_SAME_TARGET_CLASS` | **1** |
| `E_PGR`, `S_PGR` | `receptor`, `receptor` | `MERGES_SAME_TARGET_CLASS` | **1** |
| `S_SPP1`, `S_TAZ_ECM` | `ligand`, `ecm` | `MERGES_DISTINCT_TARGET_CLASSES` | **1** |
| `E_CD98_CD9`, `E_GP130_STAT3`, `E_LIF` | `surface_molecule`, `pathway`, `ligand` | `MERGES_DISTINCT_TARGET_CLASSES` | **2** |
| `E_ANXA2_ACTIN`, `E_DAG1_CLEAVED`, `E_HBEGF`, `E_ITGAVB3_5`, `E_MUC1_SLEX`, `E_PC6` | `cytoskeleton`, `surface_molecule`, `ligand`, `receptor`, `glycan`, `protease` | `MERGES_DISTINCT_TARGET_CLASSES` | **5** |

> **Nothing here forces an adjudication.** The invariant `MERGES_DISTINCT_TARGET_CLASSES` ⇒ `ARTIFICIALLY_COUPLED` was withdrawn on 2026-09-16 (`docs/coupling_adjudication.md` §2.1) and is reported rather than enforced, so a flipped signal would move a reported column and no verdict. `config/coupling_adjudication.tsv` is untouched by this computation.

## The vocabulary

Closed set: `input`, `ligand`, `receptor`, `pathway`, `transcription_factor`, `protease`, `glycan`, `surface_molecule`, `cytoskeleton`, `ecm`, `mechanical`, `state`, `readout`. Levels with no executable target today are kept, because a vocabulary only as large as the current catalog closes nothing.

| free-text `target_class` | level | why |
|---|---|---|
| `adhesive_effector` | `surface_molecule` | default for the value; overridden per target for E_MUC1_SLEX, which is a glycan epitope rather than the protein carrying it |
| `adhesive_receptor` | `receptor` | alphaVbeta3/alphaVbeta5 integrin engagement state |
| `adhesive_surface_release` | `surface_molecule` | the PC6-cleaved alpha-dystroglycan product is a surface molecule in a second state; the ENZYME is typed protease separately, which is the dissociation Heng 2015 established |
| `anti_adhesive_surface` | `surface_molecule` | PODXL, full-length alpha-dystroglycan and the MUC1 glycocalyx: three cell-surface molecules whose abundance is the barrier |
| `anti_receptive_state` | `state` | a derived proliferative cell state with no single molecular target |
| `boundary_input` | `input` | a boundary condition set by the platform |
| `candidate_effector` | `surface_molecule` | LGALS1/3 and BSG-ITGB1 interface states are surface interactions |
| `cytoskeletal_effector` | `cytoskeleton` | ANXA2-RHOA-F-actin remodelling is intracellular structure, not a surface molecule and not a pathway |
| `decidual_effector` | `ligand` | stromal SPP1/osteopontin is a secreted matricellular ligand |
| `dynamic_matrix_regulator` | `ecm` | balanced decidual senescence/remodelling, same axis as the above |
| `external_input` | `input` | an exogenous cue declared outside the executable model |
| `extracellular_bridge` | `ligand` | the free maternal SPP1 pool is the same secreted ligand as a pool |
| `growth_factor_effector` | `ligand` | HB-EGF is shed and acts extracellularly on ERBB receptors; it is a ligand at this axis whatever the node's own claim ceiling says about transcript-versus-protein |
| `input` | `input` | an exogenous signal supplied to the culture |
| `latent_state` | `mechanical` | mechanical and dynamic ECM permissiveness is the physical state, not the matrix composition that sets it |
| `ligand` | `ligand` | a secreted protein acting on a receptor |
| `mechanical_regulator` | `ecm` | stromal TAZ/WWTR1 ECM remodelling acts on matrix composition; the PHYSICAL permissiveness it produces is typed mechanical separately |
| `negative_regulator` | `transcription_factor` | KLF12 is a Kruppel-like transcription factor; the node is its transcriptional state |
| `paracrine_inhibitor_of_receptivity` | `ligand` | stromal mitogenic FGF output is secreted FGF |
| `pathway_state` | `pathway` | intracellular signalling-pathway activity |
| `perturbation_input` | `input` | an agent the experimenter adds or withholds |
| `protease` | `protease` | PC6/PCSK5 enzymatic activity |
| `regulator` | `receptor` | PGR activity: a ligand-activated nuclear receptor, and the level a receptor antagonist acts on (mifepristone is catalogued separately as the agent) |
| `transcription_factor` | `transcription_factor` | stromal HAND2: the free-text value already names the level |

Per-target overrides, where one free-text value spans two levels:

| target | level | why |
|---|---|---|
| `E_MUC1_SLEX` | `glycan` | a carbohydrate epitope, targeted through glycosyltransferases; the MUC1 protein that carries it is typed surface_molecule as E_MUC1_BARRIER |

