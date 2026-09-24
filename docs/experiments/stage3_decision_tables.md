# Stage 3 — decision tables

> **Generated file — do not edit.** Regenerate with `pixi run build-stage3-design`. [`../stage3_experiment_selection.md`](../stage3_experiment_selection.md) cites these tables and deliberately does not restate them: five review rounds on that document found one class of defect and nothing else -- a statement about the work that the work contradicted, usually a hand-written sentence refuted by a computed cell.

## A. What the committed model collapses

`adoc-literature-superset-v0.4.0`: **59 nodes**, **35 distinct Boolean functions** over **19 free variables**. Every group below realises one function, so no experiment separates its members while the rules say what they say.

**Free and latent are different sets, and the decomposition is counted here rather than written by hand.** The 19 free variables are 14 declared `IN_*` inputs, 4 `X_*` relays and `E_KLF12_HIGH`. Of those, **5 are latent** — the free variables no arm assigns, whose per-unit value is unknown and is marginalised over: `E_KLF12_HIGH`, `X_MECHANICAL_STRESS_RELAY`, `X_INTERFACE_SPP1_RELAY`, `X_INTERFACE_REDUNDANT_RELAY`, `X_INTERFACE_ANTIADHESIVE_RELAY`. **13** are assigned by some recorded arm, and `IN_HAND2_LOSS` is declared but assigned by no RECORDED arm -- a condition cfg may still set it, and `hormone_treated_hand2_loss.cfg` does; it is simply not an arm the repository holds an observation for. *Free* is a property of the rules; *latent* is a property of the design.

| Size | Class | Contains a usable assay? |
|---|---|---|
| 9 | `E_SECRETORY_STATE` `E_PAEP` `E_PC6` `E_DAG1_CLEAVED` `E_MUC1_SLEX` `E_HBEGF` `E_SPP1_EXPR` `E_ITGAVB3_5` `E_ANXA2_ACTIN` | `E_PAEP` |
| 6 | `S_DECIDUALIZED` `S_PRL` `S_IGFBP1` `S_SPP1` `S_TAZ_ECM` `OUT_STROMAL_DECIDUALIZED` | `S_IGFBP1` |
| 5 | `E_PGR` `E_IHH` `S_PGR` `S_NR2F2` `S_BMP2` | no |
| 3 | `E_LIF` `E_GP130_STAT3` `E_CD98_CD9` | no |
| 3 | `E_PODXL` `E_DAG1_FULL` `E_MUC1_BARRIER` | no |
| 2 | `E_RECEPTIVE_SURFACE` `OUT_EPITHELIAL_RECEPTIVE` | no |
| 2 | `IN_EMBRYO_CONTACT` `E_CDH1_APICAL` | no |
| 2 | `IN_cAMP` `S_PKA` | no |

Inputs **no rule reads**, so the model predicts they do nothing: `IN_EMBRYO_CONDITIONED_SIGNAL`, `IN_HCG`, `IN_XAV939`.

## B. Candidate comparison

Computed columns come from the same evaluation as [`stage3_experiment_design.md`](stage3_experiment_design.md); the protocol, assay and feasibility columns are curated declarations on each `Experiment` in `src/dt_adoc/experiments/stage3_design.py`. Neither is retyped anywhere.

**Bold** nodes carry a usable assay; `(composite)` marks a node the observation map maps but says cannot validate, so a separation resting only on those is not runnable today.

| Experiment | Axis separated on a readout that exists | Class pairs separated | Protocol | Assay | Perturbations | Propagates? |
|---|---|---|---|---|---|---|
| `observe_e2_primed` | epithelial secretory input logic (`usable_assay`) | SEC-a/c on **`E_PAEP`**; SEC-b/c on **`E_PAEP`**; SEC-c/d on **`E_PAEP`**; SEC-c/e on **`E_PAEP`** | `existing_phase_new_sampling` | PAEP at this phase is already recorded (OM-001). Any CELL-surface readout here is new: every ADOC measurement in input_tables/adoc_secreted_proteins.tsv is a secretome ELISA (PAEP, IGFBP-1, PRL) and no cell-associated protein has ever been measured on the platform. | 0 | n/a |
| `observe_hormone_treated` | **nothing measurable** | **none** (reaches CD98, at `no_assay`) | `existing_recorded_state` | PAEP and IGFBP-1 recorded (OM-001, OM-002). | 0 | n/a |
| **`dropout_e2`** | epithelial secretory input logic (`usable_assay`) | SEC-a/b on **`E_PAEP`**, `OUT_EPITHELIAL_RECEPTIVE` (composite); SEC-a/c on **`E_PAEP`**, `OUT_EPITHELIAL_RECEPTIVE` (composite); SEC-a/d on **`S_IGFBP1`**, `OUT_STROMAL_DECIDUALIZED` (composite), `S_PRL` (composite); SEC-b/d on **`E_PAEP`**, **`S_IGFBP1`**, `OUT_EPITHELIAL_RECEPTIVE` (composite), `OUT_STROMAL_DECIDUALIZED` (composite), `S_PRL` (composite); SEC-b/e on **`E_PAEP`**, `OUT_EPITHELIAL_RECEPTIVE` (composite); SEC-c/d on **`E_PAEP`**, **`S_IGFBP1`**, `OUT_EPITHELIAL_RECEPTIVE` (composite), `OUT_STROMAL_DECIDUALIZED` (composite), `S_PRL` (composite); SEC-c/e on **`E_PAEP`**, `OUT_EPITHELIAL_RECEPTIVE` (composite); SEC-d/e on **`S_IGFBP1`**, `OUT_STROMAL_DECIDUALIZED` (composite), `S_PRL` (composite) | `new_arm` | No new assay. PAEP top outlet and IGFBP-1/PRL bottom outlet are the platform's three existing ELISAs. | 1 | yes |
| `dropout_camp` | cAMP necessity for the stromal decidual program (`usable_assay`) | CAMP-a/b on **`S_IGFBP1`**, `OUT_STROMAL_DECIDUALIZED` (composite), `S_PRL` (composite) | `new_arm` | No new assay. | 1 | yes |
| `dropout_xav939` | **nothing measurable** | **none** (reaches CD98, at `no_assay`) | `new_arm` | No new assay. | 1 | **no** |
| `add_hcg_on_hormone_treated` | **nothing measurable** | **none** (reaches CD98, at `no_assay`) | `new_arm` | Surface CD98/CD9 is a new assay class for this platform. | 1 | **no** |
| `add_hcg_on_e2` | epithelial secretory input logic (`usable_assay`) | SEC-a/c on **`E_PAEP`**; SEC-b/c on **`E_PAEP`**; SEC-c/d on **`E_PAEP`**; SEC-c/e on **`E_PAEP`** | `new_arm` | Surface CD98/CD9 is a new assay class for this platform. | 1 | **no** |
| `add_il11` | gp130/STAT3 ligand identity (`mapped_composite`) | GP130-a/b on `OUT_EPITHELIAL_RECEPTIVE` (composite) | `new_arm` | pSTAT3 is a new assay class for this platform. | 1 | **no** |
| `anti_lif` | **nothing measurable** | **none** (reaches CD98, at `no_assay`) | `new_arm` | pSTAT3 is a new assay class for this platform. | 1 | yes |
| `anti_lif_plus_il11` | gp130/STAT3 ligand identity (`mapped_composite`) | GP130-a/b on `OUT_EPITHELIAL_RECEPTIVE` (composite) | `new_arm` | pSTAT3 is a new assay class for this platform. | 2 | yes |
| `smo_antagonist` | Hedgehog reception necessity (`usable_assay`) | HH-a/b on **`S_IGFBP1`**, `OUT_STROMAL_DECIDUALIZED` (composite), `S_PRL` (composite) | `new_arm` | IGFBP-1/PRL need no new assay. A GLI1/PTCH1 pathway-activity readout in the stromal channel is new and is REQUIRED, because the committed model predicts no change and a null is otherwise indistinguishable from failed target engagement. | 1 | **no** |
| `bmpr_inhibitor` | **nothing measurable** | **none** (reaches CD98, at `no_assay`) | `new_arm` | IGFBP-1/PRL need no new assay. | 1 | yes |
| `pc6_knockdown` | **nothing measurable** | **none** (reaches CD98, at `no_assay`) | `new_arm` | alpha-DG-N shedding is a new assay class. | 1 | yes |
| `dag1_cleavage_resistant` | PC6 enzyme versus DAG1 substrate state (`mapped_composite`) | PC6-a/b on `OUT_EPITHELIAL_RECEPTIVE` (composite) | `new_arm` | alpha-DG-N shedding is a new assay class. | 1 | **no** |
| `anti_spp1` | **nothing measurable** | **none** (reaches CD98, at `no_assay`) | `new_arm` | No maternal readout exists: identifiability.py reports IN_ANTI_SPP1 as set_alone_no_shared_readout. | 1 | **no** |
| `hand2_loss` | **nothing measurable** | **none** (reaches CD98, at `no_assay`) | `new_arm` | HAND2 and FGF readouts are a new assay class. | 1 | yes |

Feasibility, as declared per experiment:

* `observe_e2_primed` — No intervention; cannot fail to engage a target.
* `observe_hormone_treated` — Already run.
* `dropout_e2` — Omission of one cocktail component after the normal E2 priming phase; no drug, no construct, no target-engagement risk. The residual risk is cell loss over four E2-free days, and confluence imaging is required in BOTH the epithelial and the stromal channel. Epithelial loss reads as the committed SEC-a on PAEP; stromal loss is the half more easily forgotten and the one that costs more, because S_IGFBP1 from the bottom outlet is the only thing separating SEC-a from the confounder SEC-d, so it reads as the SEC-d signature. See section 4 of docs/stage3_experiment_selection.md.
* `dropout_camp` — Reagent omission; cannot fail to engage.
* `dropout_xav939` — Reagent omission; cannot fail to engage.
* `add_hcg_on_hormone_treated` — Recombinant hCG addition.
* `add_hcg_on_e2` — Recombinant hCG addition during the priming phase.
* `add_il11` — Recombinant ligand.
* `anti_lif` — Neutralising antibody; needs its own engagement control.
* `anti_lif_plus_il11` — Violates the one-perturbation preference.
* `smo_antagonist` — Small molecule on both channels. GAP-014's proposed_resolution names this arm. The clamp is an INTERPRETATION of the intervention, not a model of it: the network has no reception node, so blockade is applied to S_NR2F2 directly. That is defensible only because S_NR2F2 is aliased to E_IHH, and it would stop being defensible the moment a reception node existed.
* `bmpr_inhibitor` — Clamps a node the committed rules already make necessary for S_DECIDUALIZED, so the committed prediction is a near-certain loss of both stromal analytes.
* `pc6_knockdown` — siRNA/shRNA in the epithelial channel.
* `dag1_cleavage_resistant` — Requires transfecting primary epithelium with a mutant substrate; the candidate table records the determinant as absent from ADOC.
* `anti_spp1` — Neutralising antibody.
* `hand2_loss` — siRNA in the stromal channel.

## C. `dropout_e2`: predictions by mechanism class

The outcome table of the recommended arm, on the nodes the observation layer can validate. The **model action** each row licenses is a curated judgement and lives in §5 of the selection document; the predictions are computed and live here.

| Class | `E_PAEP` — PAEP, top outlet | `S_IGFBP1` — IGFBP-1, bottom outlet |
|---|---|---|
| `SEC-a` (committed) | **OFF** | **ON** |
| `SEC-b` (adoptable_alternative) | **ON** | **ON** |
| `SEC-c` (adoptable_alternative) | **ON** | **ON** |
| `SEC-d` (confounder_only) | **OFF** | **OFF** |
| `SEC-e` (confounder_only) | **OFF** | **ON** |

Distinct predicted patterns: 3, over 5 classes.

## D. Mechanism classes

`role` records what an outcome favouring the class would LICENSE -- a rule change directly, or only opening an evidence gap. It is **not** a claim that the repository already supports the class: prior support is the separate column, and `none` is an admissible entry that `SEC-b` actually carries.

| Fork | Class | Rule | Role | Prior support | Provenance |
|---|---|---|---|---|---|
| SEC | `SEC-a` | E_SECRETORY_STATE = IN_E2 and E_PGR (v0.4 as committed) | `committed` | none for the conjunction itself. MOD-01 is a modelling convention -- keep the agents separate -- not evidence that both are required. | network.bnd |
| SEC | `SEC-b` | E_SECRETORY_STATE = E_PGR (E2 primes, progestin drives) | `adoptable_alternative` | none. Nothing recorded discriminates SEC-b from the committed SEC-a: both predict E_PAEP OFF under E2-only, so OM-001 cannot tell them apart, and the computed pair index reaches `SEC-a vs SEC-b` only through the prospective dropout_e2 arm. That is the reason to run it. | introduced by this Stage-3 analysis |
| SEC | `SEC-c` | E_SECRETORY_STATE = IN_E2 or E_PGR (either agent sufficient) | `adoptable_alternative` | OM-001's E2-only PAEP of 10165-25470 pg/mL, against a 3 pg/mL sensitivity. SEC-c is the ONLY class in this fork that predicts E_PAEP ON there, so it is also the only one data already held can support -- subject to the binarisation that same row calls implicit and unrecorded. | introduced by this Stage-3 analysis |
| SEC | `SEC-d` | E2 acts only by maintaining PGR, in BOTH compartments | `confounder_only` | none; context/literature/candidate-edges.tsv holds no E2 -> PGR edge. | introduced by this Stage-3 analysis |
| SEC | `SEC-e` | E2 maintains PGR in the EPITHELIUM ONLY | `confounder_only` | none, and the same gap as SEC-d: no repository row asserts an E2 -> PGR edge in either compartment. | introduced by this Stage-3 analysis |
| CAMP | `CAMP-a` | S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2 (v0.4) | `committed` | REF-073, for cAMP driving the response. | network.bnd |
| CAMP | `CAMP-b` | S_DECIDUALIZED = S_PGR and S_BMP2 (cAMP dispensable) | `confounder_only` | none, and REF-073 points the other way: EPAC alone inert, EPAC/RAP1 knockdown attenuating rather than abolishing. | introduced by this Stage-3 analysis |
| HH | `HH-a` | S_BMP2 = (S_PGR and S_PKA) or S_NR2F2 (v0.4) | `committed` | none for the disjunct itself; GAP-014 records that it makes the relay vacuous. | network.bnd |
| HH | `HH-b` | S_BMP2 = S_NR2F2 (Hedgehog reception required) | `adoptable_alternative` | REF-026, mouse and rescue-grade. REF-075 supports the human UPSTREAM half only, and GAP-014 records that NR2F2 was not among its measured targets. | introduced by this Stage-3 analysis |
| GP130 | `GP130-a` | E_GP130_STAT3 = E_LIF (v0.4) | `committed` | none beyond the rule as committed. | network.bnd |
| GP130 | `GP130-b` | E_GP130_STAT3 = E_LIF or X_IL11 | `adoptable_alternative` | REF-072: IL-11 and LIF both act on primary human EEC, so gp130 activity is not LIF alone. | gate3_candidate_variants_2026-09-16.tsv |
| CD98 | `CD98-a` | E_CD98_CD9 = E_GP130_STAT3 (v0.4) | `committed` | none beyond the rule as committed. | network.bnd |
| CD98 | `CD98-b` | E_CD98_CD9 = E_GP130_STAT3 or IN_HCG | `adoptable_alternative` | REF-008 lists hCG among the inducers of human CD98. | gate3_candidate_variants_2026-09-16.tsv |
| CD98 | `CD98-c` | E_CD98_CD9 = E_GP130_STAT3 or IN_HCG or IN_E2 | `adoptable_alternative` | REF-008 lists E2 among the same inducers. | gate3_candidate_variants_2026-09-16.tsv |
| CD98 | `CD98-x` | E_CD98_CD9 = 1 (constitutive; CD98 is not a switch) | `confounder_only` | none as a rule. That SLC3A2 is a broadly expressed transporter subunit is general biology, not a repository row, which is exactly why this class is carried to be excluded rather than proposed. | introduced by this Stage-3 analysis |
| PC6 | `PC6-a` | E_DAG1_CLEAVED = E_PC6; E_DAG1_FULL = not E_PC6 (v0.4) | `committed` | none beyond the rule as committed, and REF-011 contradicts it. | network.bnd |
| PC6 | `PC6-b` | E_DAG1_CLEAVED = E_PC6 and E_DAG1_CLEAVABLE | `adoptable_alternative` | REF-011: full-length DAG1 is a barrier and PC6 cleavage creates the permissive form; the paper ran both the knockdown and the cleavage-resistant substrate. | gate3_candidate_variants_2026-09-16.tsv |

## E. What the committed scRNA layer can and cannot settle

Derived from `config/scrna_observation_map.tsv`, scoped to the quantities each fork is actually DECIDED on -- the separating nodes at the best readout tier any arm reaches for it, plus the interventions of the arms that reach it. This answers one question and not a wider one: **can evidence already in hand move a fork, before any new biological material is spent?**

The verdict is a function of the **separating** quantities only. The intervention is listed after the `·` as context and does not enter it: being able to see what an arm perturbs constrains nothing if the consequence that tells the classes apart cannot be seen. An earlier version let it in, and `GP130` and `PC6` -- identical separators -- came out with different verdicts.

| Fork | Axis | Decided at | scRNA verdict | Deciding quantities |
|---|---|---|---|---|
| SEC | epithelial secretory input logic | `usable_assay` | **CONSTRUCTION_ROLE_ONLY** | `E_PAEP` (direct_transcript, construction); `S_IGFBP1` (direct_transcript, construction) · intervention: `IN_E2` (not_observable); `IN_HCG` (not_observable) |
| CAMP | cAMP necessity for the stromal decidual program | `usable_assay` | **CONSTRUCTION_ROLE_ONLY** | `S_IGFBP1` (direct_transcript, construction) · intervention: `IN_cAMP` (not_observable) |
| HH | Hedgehog reception necessity | `usable_assay` | **CONSTRUCTION_ROLE_ONLY** | `S_IGFBP1` (direct_transcript, construction) · intervention: `S_NR2F2` (regulon_activity) |
| GP130 | gp130/STAT3 ligand identity | `mapped_composite_not_validating` | **NOT_OBSERVABLE** | `OUT_EPITHELIAL_RECEPTIVE` (not_observable, not_applicable) · intervention: `E_LIF` (direct_transcript) |
| CD98 | CD98/CD9 surface regulation | `no_assay` | **PROXY_LEVEL_ONLY** | `E_CD98_CD9` (proxy_abundance_not_activity, same_dataset_internal) · intervention: `E_LIF` (direct_transcript); `E_PC6` (direct_transcript); `IN_ANTI_SPP1` (not_observable); `IN_E2` (not_observable); `IN_HAND2_LOSS` (not_observable); `IN_HCG` (not_observable); `IN_XAV939` (not_observable); `IN_cAMP` (not_observable); `S_BMP2` (direct_transcript); `S_NR2F2` (regulon_activity) |
| PC6 | PC6 enzyme versus DAG1 substrate state | `mapped_composite_not_validating` | **NOT_OBSERVABLE** | `OUT_EPITHELIAL_RECEPTIVE` (not_observable, not_applicable) |

> Two caveats apply to **every** row and are why no verdict above is `SUPPORTED` or `CONTRADICTED`. The first is that **no row of the scRNA map carries an ACTIVE status** -- the statuses present are `provisional`, `rejected`, `reported_only`, counted from the file rather than asserted -- so nothing there is activated, and `config/external_data_manifest.tsv` records that no model node is conditioned on the object and that it constrains nothing. The second is that the map records near-total confounding between cell label and condition (Luminal-like epithelium 0.8% HT against HT epithelium I 79.1%), so a between-condition contrast in that data is not separable from a between-label one.

> **Why the `SEC` fork cannot be decided there, stated as a design fact rather than as a label.** `CONSTRUCTION_ROLE_ONLY` says the deciding readouts helped build v0.4, so they cannot serve as independent validation of it. That alone would not settle the question, because Stage 3 is choosing an experiment to CALIBRATE an underidentified twin, and construction-role data may legitimately inform calibration provided nothing later claims it as held-out validation. The decisive reason is the design of the deposited experiment itself: it contains **2 conditions (CNT, HT)** across 3 donors, and `HT` moves E2, MPA, cAMP and XAV939 **together**. The contrast that separates `SEC-a` from `SEC-b` is an E2 dropout against a matched full cocktail, and that contrast does not exist in the data. No amount of detection quality creates it.

> **Controlled inputs are known, not inferred.** `IN_E2` and `IN_cAMP` appear in the map as `not_observable`, and that is the wrong frame for reading this table: they are experimenter-set, so their values are known from the protocol and never need to be recovered from RNA. The real limitation is causal rather than observational -- `CNT` versus `HT` is a bundled intervention, so a transcript programme that differs between them cannot be attributed to E2, to MPA, to cAMP or to XAV939 individually. That is the same bundling `U1` records for the ADOC secretome, in the same protocol, and it is why the recommended arm is a single-component dropout.

## F. What no scRNA result can change (a conditional invariance)

Asked because a reviewer was right that "it is not what the recommendation turns on" is not an argument. What is proved here is narrower than "the preference is invariant", and the heading says so:

> Under the frozen v0.4 model and the current observation-activation policy, no scRNA finding can add or remove an arm from the set that separates a fork on an already-usable assay.

Preference also weighs which uncertainty stays credible, how many classes an arm separates, target-engagement ambiguity, assay cost and robustness. A strong scRNA finding can move that uncertainty set without touching any `readout_tier`, so this bounds the candidate set and not the ordering within it.

1. **The ranking criterion is a tier, and scRNA cannot set one.** An arm is preferred here for separating a fork on a readout that EXISTS, and that tier is computed by `_readout_tier` from `config/observation_model_map.tsv` **and nothing else**. Every row of `config/scrna_observation_map.tsv` carries `activation_status` in {`provisional`, `rejected`, `reported_only`} -- none of them active. So no scRNA finding promotes any node to `usable_assay`.

2. **The forks an AC04 result bears on are not decided at that tier.** `GP130` is decided at `mapped_composite_not_validating` and `CD98` at `no_assay` (table E). Strong support for the `E_LIF`/`E_GP130_STAT3`/`E_CD98_CD9` aliasing leaves both where they are; strong contradiction makes both *more* worth resolving and still leaves both where they are, because step 1 says the tier cannot move. A fork that matters more but still cannot be read does not make its arm more informative.

3. **The arms that separate a fork on a usable assay are fixed under both extremes**, and none of them is decided by AC04:

| Arm | Fork it decides on a usable assay |
|---|---|
| `observe_e2_primed` | SEC |
| `dropout_e2` | SEC |
| `dropout_camp` | CAMP |
| `add_hcg_on_e2` | SEC |
| `smo_antagonist` | HH |

So the candidate set for "preferred" is invariant: no arm can enter it and none can leave. That does not by itself exclude RE-ORDERING within it -- an `AC03` within-condition divergence would bear on `HH`, which is a candidate fork and the runner-up's -- and section 3a of the selection document gives the separate design reason why no prior shift closes the gap between the runner-up and the recommended arm.

> **What this does not prove.** It shows no admissible scRNA finding changes the experiment CHOICE. It does not show such a finding would be uninteresting: contradicting AC04 would be evidence that the epithelial receptivity layer is mis-specified, which is a reason to develop an assay for it, and that is a different decision from which arm to run next with the assays that exist.

