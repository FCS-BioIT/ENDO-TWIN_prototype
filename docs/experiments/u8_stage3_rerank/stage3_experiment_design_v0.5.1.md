# Stage 3 — which single experiment separates which maternal mechanism

> **Generated file — do not edit.** Regenerate with `pixi run build-u8-stage3-rerank`. Computed by conditioning the committed `adoc-literature-superset-v0.5.1` network, and each mechanism class's in-memory rule substitution, on every candidate experiment's controlled inputs and intervention clamps. No MaBoSS run; no committed file is modified.

Latent variables marginalised: `E_KLF12_HIGH`, `X_MECHANICAL_STRESS_RELAY`, `X_INTERFACE_SPP1_RELAY`, `X_INTERFACE_REDUNDANT_RELAY`, `X_INTERFACE_ANTIADHESIVE_RELAY`. Experimenter-controlled inputs are conditioned on, never marginalised.

## Readouts the observation layer can actually validate

| Node | Analyte | Tier |
|---|---|---|
| `E_PAEP` | PAEP (top outlet) | `usable_assay` |
| `OUT_EPITHELIAL_RECEPTIVE` | multi_analyte_composite:PAEP;SPP1;DPP4;CEACAM5;CEACAM6 [reported_only, confidence=low, source_rows_n=0] | `mapped_composite_not_validating` |
| `OUT_STROMAL_DECIDUALIZED` | multi_analyte_composite:BMP2;DKK1;KDR;IL11;PRL;IGFBP-1 [reported_only, confidence=low, source_rows_n=0] | `mapped_composite_not_validating` |
| `S_IGFBP1` | IGFBP-1 (bottom outlet) | `usable_assay` |
| `S_PRL` | PRL [provisional, confidence=low, source_rows_n=18] | `mapped_composite_not_validating` |

Everything else is `no_assay`. A separation reported below at a node absent from this table is a difference between two model states.

## Summary: what each candidate experiment separates

| Experiment | Protocol | Perturbations | Forks separated | …on a usable assay | …at `mapped_composite` only | …at `no_assay` only | …with opposite predictions | Committed model propagates downstream? |
|---|---|---|---|---|---|---|---|---|
| `observe_e2_primed` | `existing_phase_new_sampling` | 0 | CD98, SEC | **SEC** | — | CD98 | **SEC** | n/a |
| `observe_hormone_treated` | `existing_recorded_state` | 0 | CD98 | **none** | — | CD98 | **none** | n/a |
| `dropout_e2` | `new_arm` | 1 | CD98, SEC | **SEC** | — | CD98 | **SEC** | yes |
| `dropout_camp` | `new_arm` | 1 | CAMP, CD98 | **CAMP** | — | CD98 | **CAMP** | yes |
| `dropout_xav939` | `new_arm` | 1 | CD98 | **none** | — | CD98 | **none** | **no** |
| `add_hcg_on_hormone_treated` | `new_arm` | 1 | CD98 | **none** | — | CD98 | **none** | **no** |
| `add_hcg_on_e2` | `new_arm` | 1 | CD98, SEC | **SEC** | — | CD98 | **SEC** | **no** |
| `add_il11` | `new_arm` | 1 | CD98, GP130 | **none** | GP130 | CD98 | **none** | **no** |
| `anti_lif` | `new_arm` | 1 | CD98 | **none** | — | CD98 | **none** | yes |
| `anti_lif_plus_il11` | `new_arm` | 2 | CD98, GP130 | **none** | GP130 | CD98 | **none** | yes |
| `smo_antagonist` | `new_arm` | 1 | CD98, HH | **HH** | — | CD98 | **HH** | **no** |
| `bmpr_inhibitor` | `new_arm` | 1 | CD98 | **none** | — | CD98 | **none** | yes |
| `pc6_knockdown` | `new_arm` | 1 | CD98 | **none** | — | CD98 | **none** | yes |
| `dag1_cleavage_resistant` | `new_arm` | 1 | CD98, PC6 | **none** | PC6 | CD98 | **none** | **no** |
| `anti_spp1` | `new_arm` | 1 | CD98 | **none** | — | CD98 | **none** | **no** |
| `hand2_loss` | `new_arm` | 1 | CD98 | **none** | — | CD98 | **none** | yes |

> The three tier columns partition the fourth: every fork an arm separates appears in exactly one of them. `CD98` lands in the `no_assay` column for **every** arm in the catalogue, which is the single fact about that axis worth carrying — it is separable in many arms and decidable in none of them.

> The last column is about INTERVENTIONS only, and reads `n/a` for the observation-only arms. An arm that applies nothing has an empty downstream set for any network whatever — the two marginals are computed from identical inputs — so printing **no** there would be a demerit the computation never tested.
> For an intervention, a **no** is not a disqualification — a predicted null is falsifiable — but it means a negative result is indistinguishable from failed target engagement unless the design carries its own engagement control.

## Which experiment separates which class pair

The inverse of the summary table, and the one that catches a fork no candidate can close. A pair listed with `(none)` is unreachable by every experiment in this catalogue, whatever the readout; a pair reachable only at `no_assay` is unreachable today.

| Fork | Pair | Separated by | Best readout tier |
|---|---|---|---|
| SEC | `SEC-a vs SEC-b` | `dropout_e2` | `usable_assay` |
| SEC | `SEC-a vs SEC-c` | `observe_e2_primed`, `dropout_e2`, `add_hcg_on_e2` | `usable_assay` |
| SEC | `SEC-a vs SEC-d` | `dropout_e2` | `usable_assay` |
| SEC | `SEC-a vs SEC-e` | `dropout_e2` | `no_assay` |
| SEC | `SEC-b vs SEC-c` | `observe_e2_primed`, `add_hcg_on_e2` | `usable_assay` |
| SEC | `SEC-b vs SEC-d` | `dropout_e2` | `usable_assay` |
| SEC | `SEC-b vs SEC-e` | `dropout_e2` | `usable_assay` |
| SEC | `SEC-c vs SEC-d` | `observe_e2_primed`, `dropout_e2`, `add_hcg_on_e2` | `usable_assay` |
| SEC | `SEC-c vs SEC-e` | `observe_e2_primed`, `dropout_e2`, `add_hcg_on_e2` | `usable_assay` |
| SEC | `SEC-d vs SEC-e` | `dropout_e2` | `usable_assay` |
| CAMP | `CAMP-a vs CAMP-b` | `dropout_camp` | `usable_assay` |
| HH | `HH-a vs HH-b` | `smo_antagonist` | `usable_assay` |
| GP130 | `GP130-a vs GP130-b` | `add_il11`, `anti_lif_plus_il11` | `mapped_composite_not_validating` |
| CD98 | `CD98-a vs CD98-b` | `add_hcg_on_hormone_treated`, `add_hcg_on_e2` | `no_assay` |
| CD98 | `CD98-a vs CD98-c` | `observe_e2_primed`, `observe_hormone_treated`, `dropout_camp`, `dropout_xav939`, `add_hcg_on_hormone_treated`, `add_hcg_on_e2`, `add_il11`, `anti_lif`, `anti_lif_plus_il11`, `smo_antagonist`, `bmpr_inhibitor`, `pc6_knockdown`, `dag1_cleavage_resistant`, `anti_spp1`, `hand2_loss` | `no_assay` |
| CD98 | `CD98-a vs CD98-x` | `observe_e2_primed`, `observe_hormone_treated`, `dropout_e2`, `dropout_camp`, `dropout_xav939`, `add_hcg_on_hormone_treated`, `add_hcg_on_e2`, `add_il11`, `anti_lif`, `anti_lif_plus_il11`, `smo_antagonist`, `bmpr_inhibitor`, `pc6_knockdown`, `dag1_cleavage_resistant`, `anti_spp1`, `hand2_loss` | `no_assay` |
| CD98 | `CD98-b vs CD98-c` | `observe_e2_primed`, `observe_hormone_treated`, `dropout_camp`, `dropout_xav939`, `add_il11`, `anti_lif`, `anti_lif_plus_il11`, `smo_antagonist`, `bmpr_inhibitor`, `pc6_knockdown`, `dag1_cleavage_resistant`, `anti_spp1`, `hand2_loss` | `no_assay` |
| CD98 | `CD98-b vs CD98-x` | `observe_e2_primed`, `observe_hormone_treated`, `dropout_e2`, `dropout_camp`, `dropout_xav939`, `add_il11`, `anti_lif`, `anti_lif_plus_il11`, `smo_antagonist`, `bmpr_inhibitor`, `pc6_knockdown`, `dag1_cleavage_resistant`, `anti_spp1`, `hand2_loss` | `no_assay` |
| CD98 | `CD98-c vs CD98-x` | `dropout_e2` | `no_assay` |
| PC6 | `PC6-a vs PC6-b` | `dag1_cleavage_resistant` | `mapped_composite_not_validating` |

## Forks

### SEC — epithelial secretory input logic

*Is concurrent E2 required for the epithelial secretory program, or does E2 act only upstream of PGR?*

`role` says what an outcome favouring the class would LICENSE — a rule change directly, or only opening an evidence gap. It is not a claim about how well supported the class already is, which is the separate `prior support` column and may be `none`.

| Class | Rule | Role (what an outcome licenses) | Prior support | Provenance |
|---|---|---|---|---|
| `SEC-a` | E_SECRETORY_STATE = IN_E2 and E_PGR (v0.4 as committed) | `committed` | none for the conjunction itself. MOD-01 is a modelling convention -- keep the agents separate -- not evidence that both are required. | network.bnd |
| `SEC-b` | E_SECRETORY_STATE = E_PGR (E2 primes, progestin drives) | `adoptable_alternative` | none. Nothing recorded discriminates SEC-b from the committed SEC-a: both predict E_PAEP OFF under E2-only, so OM-001 cannot tell them apart, and the computed pair index reaches `SEC-a vs SEC-b` only through the prospective dropout_e2 arm. That is the reason to run it. | introduced by this Stage-3 analysis |
| `SEC-c` | E_SECRETORY_STATE = IN_E2 or E_PGR (either agent sufficient) | `adoptable_alternative` | OM-001's E2-only PAEP of 10165-25470 pg/mL, against a 3 pg/mL sensitivity. SEC-c is the ONLY class in this fork that predicts E_PAEP ON there, so it is also the only one data already held can support -- subject to the binarisation that same row calls implicit and unrecorded. | introduced by this Stage-3 analysis |
| `SEC-d` | E2 acts only by maintaining PGR, in BOTH compartments | `confounder_only` | none; context/literature/candidate-edges.tsv holds no E2 -> PGR edge. | introduced by this Stage-3 analysis |
| `SEC-e` | E2 maintains PGR in the EPITHELIUM ONLY | `confounder_only` | none, and the same gap as SEC-d: no repository row asserts an E2 -> PGR edge in either compartment. | introduced by this Stage-3 analysis |

* `SEC-a` — MOD-01 keeps the protocol agents as explicit inputs; no single-agent arm exists, so the conjunction is untested.
* `SEC-b` — The standard reading in which E2 acts by priming and the progestin drives the secretory program. It is ADOPTABLE because §5 of docs/stage3_experiment_selection.md records the rule change its outcome licenses, NOT because the repository supports it -- see prior_support, which is `none`.
* `SEC-c` — The same OM-001 observation read as an induction rather than as a sub-threshold baseline.
* `SEC-d` — An outcome favouring it -- PAEP and IGFBP-1 both OFF -- licenses OPENING AN EVIDENCE GAP and nothing else: the rule it points at is an E2 dependence of E_PGR and S_PGR, and no repository row asserts an E2 -> PGR edge (context/literature/candidate-edges.tsv has none), so the action is to seek that citation before encoding anything. Carried because it predicts the same epithelial readout as SEC-a and a DIFFERENT stromal one, so an experiment reading only the epithelial outlet could not exclude it.
* `SEC-e` — No outcome of this design licenses anything about it, which is the point: it predicts EXACTLY what the committed SEC-a predicts on both usable assays, in every arm of the catalogue, so nothing here can favour one over the other. Its role is to BOUND the interpretation rather than to be chosen -- a reader of the decision tree would otherwise take a PAEP-OFF/IGFBP-1-ON result as establishing the SEC-a conjunction specifically. Carried so that the indistinguishability is computed and visible rather than argued.

> The fork the observation layer can actually read: E_PAEP is the only active_constraint and S_IGFBP1 the only active_diagnostic, and they sit on opposite sides of it. What opens the fork is a fact about the committed rule rather than support for any alternative: OM-001 records PAEP at 10165-25470 pg/mL under E2-only, roughly 3400-8500x the 3 pg/mL sensitivity -- that row's own claim_ceiling says 'five orders of magnitude', which is its arithmetic and is not repeated here -- and calls it OFF by a threshold the same claim_ceiling admits is implicit and unrecorded. So the committed conjunction is not ESTABLISHED by the data meant to support it. That is absence of support for SEC-a; it is not support for SEC-b, and no class below claims it as such.

### CAMP — cAMP necessity for the stromal decidual program

*Is cAMP a necessary conjunct of S_DECIDUALIZED, or a potentiator the Boolean class cannot express?*

`role` says what an outcome favouring the class would LICENSE — a rule change directly, or only opening an evidence gap. It is not a claim about how well supported the class already is, which is the separate `prior support` column and may be `none`.

| Class | Rule | Role (what an outcome licenses) | Prior support | Provenance |
|---|---|---|---|---|
| `CAMP-a` | S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2 (v0.4) | `committed` | REF-073, for cAMP driving the response. | network.bnd |
| `CAMP-b` | S_DECIDUALIZED = S_PGR and S_BMP2 (cAMP dispensable) | `confounder_only` | none, and REF-073 points the other way: EPAC alone inert, EPAC/RAP1 knockdown attenuating rather than abolishing. | introduced by this Stage-3 analysis |

* `CAMP-a` — REF-073 (Kusama 2013): the PKA-selective analogue drives the IGFBP-1 and PRL response.
* `CAMP-b` — An outcome favouring it -- IGFBP-1 still secreted without cAMP -- would license OPENING A GAP, not a rule edit, and that is why the role is confounder-only. The reason is not weak support: it is that the outcome would be Kusama's graded potentiation, and a rate-free Boolean model cannot express potentiation at all, so the repair it points at belongs to a future rate layer rather than to `S_DECIDUALIZED`'s rule. The candidate table already rejected `EPAC` as a node on exactly that ground. Separately, and not the reason for the role: REF-073 shows EPAC alone INERT and EPAC/RAP1 knockdown ATTENUATING the PKA-driven response -- attenuation, not abolition, and only of the second arm.

> Kusama's graded potentiation is a model-CLASS limitation, not a topology fork; the candidate table already rejects EPAC as a node for that reason. An arm that returns 'reduced but present' rediscovers a limitation the repository has recorded.

### HH — Hedgehog reception necessity

*Is stromal BMP2 induction reachable without Hedgehog reception, as v0.4's disjunct asserts, or does it require it?*

Recorded evidence gap: `GAP-014`.

`role` says what an outcome favouring the class would LICENSE — a rule change directly, or only opening an evidence gap. It is not a claim about how well supported the class already is, which is the separate `prior support` column and may be `none`.

| Class | Rule | Role (what an outcome licenses) | Prior support | Provenance |
|---|---|---|---|---|
| `HH-a` | S_BMP2 = (S_PGR and S_PKA) or S_NR2F2 (v0.4) | `committed` | none for the disjunct itself; GAP-014 records that it makes the relay vacuous. | network.bnd |
| `HH-b` | S_BMP2 = S_NR2F2 (Hedgehog reception required) | `adoptable_alternative` | REF-026, mouse and rescue-grade. REF-075 supports the human UPSTREAM half only, and GAP-014 records that NR2F2 was not among its measured targets. | introduced by this Stage-3 analysis |

* `HH-a` — The disjunct makes the relay structurally vacuous: E_PGR = E_IHH = S_PGR = S_NR2F2 = S_BMP2 is one Boolean function, as GAP-014's impact column already records.
* `HH-b` — REF-026 (Kurihara 2007) is rescue-grade: epithelial Ihh acts on stromal COUP-TFII, COUP-TFII is REQUIRED for Bmp2 induction, and intrauterine BMP2 add-back rescues the decidual response. Entirely mouse in vivo. REF-075 (Wei 2010) gives human compartment-resolved expression and a progestin response of GLI1, i.e. the relay's UPSTREAM half only.

> GAP-014 states the limit precisely: NR2F2/COUP-TFII was not among REF-075's measured targets, so even the correlative human link from Hedgehog output to NR2F2 is untested.

### GP130 — gp130/STAT3 ligand identity

*Is E_GP130_STAT3 driven by LIF alone, as the committed three-way alias asserts, or by any gp130 ligand?*

`role` says what an outcome favouring the class would LICENSE — a rule change directly, or only opening an evidence gap. It is not a claim about how well supported the class already is, which is the separate `prior support` column and may be `none`.

| Class | Rule | Role (what an outcome licenses) | Prior support | Provenance |
|---|---|---|---|---|
| `GP130-a` | E_GP130_STAT3 = E_LIF (v0.4) | `committed` | none beyond the rule as committed. | network.bnd |
| `GP130-b` | E_GP130_STAT3 = E_LIF or X_IL11 | `adoptable_alternative` | REF-072: IL-11 and LIF both act on primary human EEC, so gp130 activity is not LIF alone. | gate3_candidate_variants_2026-09-16.tsv |

* `GP130-a` — E_LIF, E_GP130_STAT3 and E_CD98_CD9 are ONE Boolean function.
* `GP130-b` — REF-072 (Marwood 2009): IL-11 and LIF both raise primary human EEC adhesion and integrin-alpha2, yet dissociate on phenotype. The variant breaks the ligand/pathway alias and does NOT represent that downstream divergence.

> X_IL11 is supplied, never endogenous: the repository encodes no stromal IL-11 source, and REF-064 (Tanaka 2001) forbids one -- IL-11 has NO effect on unstimulated stroma and, in the co-stimulated arm, raises viability without raising prolactin.

### CD98 — CD98/CD9 surface regulation

*Is surface CD98 availability a pure STAT3 readout, or is it induced by hCG and/or E2 independently?*

`role` says what an outcome favouring the class would LICENSE — a rule change directly, or only opening an evidence gap. It is not a claim about how well supported the class already is, which is the separate `prior support` column and may be `none`.

| Class | Rule | Role (what an outcome licenses) | Prior support | Provenance |
|---|---|---|---|---|
| `CD98-a` | E_CD98_CD9 = E_GP130_STAT3 (v0.4) | `committed` | none beyond the rule as committed. | network.bnd |
| `CD98-b` | E_CD98_CD9 = E_GP130_STAT3 or IN_HCG | `adoptable_alternative` | REF-008 lists hCG among the inducers of human CD98. | gate3_candidate_variants_2026-09-16.tsv |
| `CD98-c` | E_CD98_CD9 = E_GP130_STAT3 or IN_HCG or IN_E2 | `adoptable_alternative` | REF-008 lists E2 among the same inducers. | gate3_candidate_variants_2026-09-16.tsv |
| `CD98-x` | E_CD98_CD9 = 1 (constitutive; CD98 is not a switch) | `confounder_only` | none as a rule. That SLC3A2 is a broadly expressed transporter subunit is general biology, not a repository row, which is exactly why this class is carried to be excluded rather than proposed. | introduced by this Stage-3 analysis |

* `CD98-b` — REF-008 (Dominguez 2010): human endometrial CD98 is essential for blastocyst adhesion and is induced by hCG, E2, LIF and EGF.
* `CD98-c` — Same REF-008 induction list, read as including E2.
* `CD98-x` — An outcome favouring it -- CD98 detected wherever it is looked for -- licenses REOPENING whether E_CD98_CD9 is a switch at all, not adopting `E_CD98_CD9 = 1` as a rule: a constitutive node earns its place by what reads it, and that is a modelling question no single readout settles. SLC3A2/4F2hc is the heavy chain of the broadly expressed amino-acid transporter heterodimers, and REF-008 reports INDUCTION of an already-present protein rather than its appearance. Carried because it predicts the same 'CD98 detected' result as CD98-b and CD98-c in every arm, so a presence/absence surface readout cannot exclude it.

> E_CD98_CD9's only consumers are E_RECEPTIVE_SURFACE and the redundant adhesion route, so the fork is maternal but terminal.

### PC6 — PC6 enzyme versus DAG1 substrate state

*Is cleaved alpha-dystroglycan identical to PC6 activity, as v0.4 asserts, or does it also depend on substrate availability?*

`role` says what an outcome favouring the class would LICENSE — a rule change directly, or only opening an evidence gap. It is not a claim about how well supported the class already is, which is the separate `prior support` column and may be `none`.

| Class | Rule | Role (what an outcome licenses) | Prior support | Provenance |
|---|---|---|---|---|
| `PC6-a` | E_DAG1_CLEAVED = E_PC6; E_DAG1_FULL = not E_PC6 (v0.4) | `committed` | none beyond the rule as committed, and REF-011 contradicts it. | network.bnd |
| `PC6-b` | E_DAG1_CLEAVED = E_PC6 and E_DAG1_CLEAVABLE | `adoptable_alternative` | REF-011: full-length DAG1 is a barrier and PC6 cleavage creates the permissive form; the paper ran both the knockdown and the cleavage-resistant substrate. | gate3_candidate_variants_2026-09-16.tsv |

* `PC6-b` — REF-011 (Heng 2015): full-length DAG1 is a barrier and PC6 cleavage creates the adhesion-permissive form; the paper ran both the knockdown and the cleavage-resistant substrate.

> E_DAG1_CLEAVABLE has no physiological determinant: the cleavage-site mutant is a laboratory construct, not a state ADOC varies. The candidate table records this as ACKNOWLEDGED ABSENT.

## Per-experiment detail

### `observe_e2_primed` — E2-only priming, day 2 (observation only)

Background `e2_primed_maternal`; observation_only; `existing_phase_new_sampling`.

* **Assay:** PAEP at this phase is already recorded (OM-001). Any CELL-surface readout here is new: every ADOC measurement in input_tables/adoc_secreted_proteins.tsv is a secretome ELISA (PAEP, IGFBP-1, PRL) and no cell-associated protein has ever been measured on the platform.
* **Feasibility:** No intervention; cannot fail to engage a target.
* **Committed model, downstream of the intervention:** n/a — this arm applies no intervention

**SEC: SEC-a vs SEC-c**

| Node | SEC-a | SEC-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_HBEGF` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 0.0 | 1.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SECRETORY_STATE` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**SEC: SEC-b vs SEC-c**

| Node | SEC-b | SEC-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_HBEGF` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 0.0 | 1.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SECRETORY_STATE` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**SEC: SEC-c vs SEC-d**

| Node | SEC-c | SEC-d | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_HBEGF` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 1.0 | 0.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SECRETORY_STATE` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**SEC: SEC-c vs SEC-e**

| Node | SEC-c | SEC-e | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_HBEGF` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 1.0 | 0.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SECRETORY_STATE` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

### `observe_hormone_treated` — Full cocktail, day 6 (observation only)

Background `hormone_treated_maternal`; observation_only; `existing_recorded_state`.

* **Assay:** PAEP and IGFBP-1 recorded (OM-001, OM-002).
* **Feasibility:** Already run.
* **Committed model, downstream of the intervention:** n/a — this arm applies no intervention

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

### `dropout_e2` — Cocktail minus E2 (MPA + cAMP + XAV939, days 2-6)

Background `hormone_treated_maternal`; reagent_omission; `new_arm`.

* **Assay:** No new assay. PAEP top outlet and IGFBP-1/PRL bottom outlet are the platform's three existing ELISAs.
* **Feasibility:** Omission of one cocktail component after the normal E2 priming phase; no drug, no construct, no target-engagement risk. The residual risk is cell loss over four E2-free days, and confluence imaging is required in BOTH the epithelial and the stromal channel. Epithelial loss reads as the committed SEC-a on PAEP; stromal loss is the half more easily forgotten and the one that costs more, because S_IGFBP1 from the bottom outlet is the only thing separating SEC-a from the confounder SEC-d, so it reads as the SEC-d signature. See section 4 of docs/stage3_experiment_selection.md.
* **Committed model, downstream of the intervention:** `E_ANXA2_ACTIN`, `E_CD98_CD9`, `E_DAG1_CLEAVED`, `E_DAG1_FULL`, `E_GP130_STAT3`, `E_HBEGF`, `E_ITGAVB3_5`, `E_LIF`, `E_MUC1_BARRIER`, `E_MUC1_SLEX`, `E_PAEP`, `E_PC6`, `E_PODXL`, `E_RECEPTIVE_SURFACE`, `E_SECRETORY_STATE`, `E_SPP1_EXPR`, `OUT_EPITHELIAL_RECEPTIVE`

**SEC: SEC-a vs SEC-b**

| Node | SEC-a | SEC-b | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_HBEGF` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 0.0 | 1.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_RECEPTIVE_SURFACE` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_SECRETORY_STATE` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `OUT_EPITHELIAL_RECEPTIVE` | 0.0 | 0.5 | no | `mapped_composite_not_validating` | — |

**SEC: SEC-a vs SEC-c**

| Node | SEC-a | SEC-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_HBEGF` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 0.0 | 1.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_RECEPTIVE_SURFACE` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_SECRETORY_STATE` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `OUT_EPITHELIAL_RECEPTIVE` | 0.0 | 0.5 | no | `mapped_composite_not_validating` | — |

**SEC: SEC-a vs SEC-d**

| Node | SEC-a | SEC-d | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_IHH` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PGR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `OUT_STROMAL_DECIDUALIZED` | 1.0 | 0.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_BMP2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_DECIDUALIZED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_FGF_MITOGENIC` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_HAND2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_IGFBP1` | 1.0 | 0.0 | **yes** | `usable_assay` | IGFBP-1 (bottom outlet) |
| `S_NR2F2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_PGR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_PRL` | 1.0 | 0.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_SPP1` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_TAZ_ECM` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**SEC: SEC-a vs SEC-e**

| Node | SEC-a | SEC-e | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_IHH` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PGR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_NR2F2` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**SEC: SEC-b vs SEC-d**

| Node | SEC-b | SEC-d | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_HBEGF` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_IHH` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 1.0 | 0.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PGR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_RECEPTIVE_SURFACE` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_SECRETORY_STATE` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 0.0 | no | `mapped_composite_not_validating` | — |
| `OUT_STROMAL_DECIDUALIZED` | 1.0 | 0.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_BMP2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_DECIDUALIZED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_FGF_MITOGENIC` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_HAND2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_IGFBP1` | 1.0 | 0.0 | **yes** | `usable_assay` | IGFBP-1 (bottom outlet) |
| `S_NR2F2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_PGR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_PRL` | 1.0 | 0.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_SPP1` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_TAZ_ECM` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**SEC: SEC-b vs SEC-e**

| Node | SEC-b | SEC-e | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_HBEGF` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_IHH` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 1.0 | 0.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PGR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_RECEPTIVE_SURFACE` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_SECRETORY_STATE` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 0.0 | no | `mapped_composite_not_validating` | — |
| `S_NR2F2` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**SEC: SEC-c vs SEC-d**

| Node | SEC-c | SEC-d | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_HBEGF` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_IHH` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 1.0 | 0.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PGR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_RECEPTIVE_SURFACE` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_SECRETORY_STATE` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 0.0 | no | `mapped_composite_not_validating` | — |
| `OUT_STROMAL_DECIDUALIZED` | 1.0 | 0.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_BMP2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_DECIDUALIZED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_FGF_MITOGENIC` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_HAND2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_IGFBP1` | 1.0 | 0.0 | **yes** | `usable_assay` | IGFBP-1 (bottom outlet) |
| `S_NR2F2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_PGR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_PRL` | 1.0 | 0.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_SPP1` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_TAZ_ECM` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**SEC: SEC-c vs SEC-e**

| Node | SEC-c | SEC-e | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_HBEGF` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_IHH` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 1.0 | 0.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PGR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_RECEPTIVE_SURFACE` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_SECRETORY_STATE` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 0.0 | no | `mapped_composite_not_validating` | — |
| `S_NR2F2` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**SEC: SEC-d vs SEC-e**

| Node | SEC-d | SEC-e | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `OUT_STROMAL_DECIDUALIZED` | 0.0 | 1.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_BMP2` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_DECIDUALIZED` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_FGF_MITOGENIC` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_HAND2` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_IGFBP1` | 0.0 | 1.0 | **yes** | `usable_assay` | IGFBP-1 (bottom outlet) |
| `S_PGR` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_PRL` | 0.0 | 1.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_SPP1` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_TAZ_ECM` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-c vs CD98-x**

| Node | CD98-c | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

### `dropout_camp` — Cocktail minus cAMP (E2 + MPA + XAV939, days 2-6)

Background `hormone_treated_maternal`; reagent_omission; `new_arm`.

* **Assay:** No new assay.
* **Feasibility:** Reagent omission; cannot fail to engage.
* **Committed model, downstream of the intervention:** `OUT_STROMAL_DECIDUALIZED`, `S_DECIDUALIZED`, `S_IGFBP1`, `S_PKA`, `S_PRL`, `S_SPP1`, `S_TAZ_ECM`

**CAMP: CAMP-a vs CAMP-b**

| Node | CAMP-a | CAMP-b | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `OUT_STROMAL_DECIDUALIZED` | 0.0 | 1.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_DECIDUALIZED` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_IGFBP1` | 0.0 | 1.0 | **yes** | `usable_assay` | IGFBP-1 (bottom outlet) |
| `S_PRL` | 0.0 | 1.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_SPP1` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `S_TAZ_ECM` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

### `dropout_xav939` — Cocktail minus XAV939 (E2 + MPA + cAMP, days 2-6)

Background `hormone_treated_maternal`; reagent_omission; `new_arm`.

* **Assay:** No new assay.
* **Feasibility:** Reagent omission; cannot fail to engage.
* **Committed model, downstream of the intervention:** **nothing propagates**

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

### `add_hcg_on_hormone_treated` — Full cocktail + hCG

Background `hormone_treated_maternal`; reagent_addition; `new_arm`.

* **Assay:** Surface CD98/CD9 is a new assay class for this platform.
* **Feasibility:** Recombinant hCG addition.
* **Committed model, downstream of the intervention:** **nothing propagates**

**CD98: CD98-a vs CD98-b**

| Node | CD98-a | CD98-b | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

### `add_hcg_on_e2` — E2-only priming + hCG

Background `e2_primed_maternal`; reagent_addition; `new_arm`.

* **Assay:** Surface CD98/CD9 is a new assay class for this platform.
* **Feasibility:** Recombinant hCG addition during the priming phase.
* **Committed model, downstream of the intervention:** **nothing propagates**

**SEC: SEC-a vs SEC-c**

| Node | SEC-a | SEC-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_HBEGF` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 0.0 | 1.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SECRETORY_STATE` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**SEC: SEC-b vs SEC-c**

| Node | SEC-b | SEC-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_HBEGF` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.0 | 0.5 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 0.0 | 1.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SECRETORY_STATE` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**SEC: SEC-c vs SEC-d**

| Node | SEC-c | SEC-d | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_HBEGF` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 1.0 | 0.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SECRETORY_STATE` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**SEC: SEC-c vs SEC-e**

| Node | SEC-c | SEC-e | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_ANXA2_ACTIN` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_CD98_CD9` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_DAG1_CLEAVED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_HBEGF` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_ITGAVB3_5` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_LIF` | 0.5 | 0.0 | no | `no_assay` | — |
| `E_MUC1_BARRIER` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_MUC1_SLEX` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PAEP` | 1.0 | 0.0 | **yes** | `usable_assay` | PAEP (top outlet) |
| `E_PC6` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_PODXL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_SECRETORY_STATE` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_SPP1_EXPR` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-b**

| Node | CD98-a | CD98-b | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

### `add_il11` — Full cocktail + recombinant IL-11

Background `hormone_treated_maternal`; reagent_addition; `new_arm`.

* **Assay:** pSTAT3 is a new assay class for this platform.
* **Feasibility:** Recombinant ligand.
* **Committed model, downstream of the intervention:** **nothing propagates**

**GP130: GP130-a vs GP130-b**

| Node | GP130-a | GP130-b | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |
| `E_GP130_STAT3` | 0.5 | 1.0 | no | `no_assay` | — |
| `E_RECEPTIVE_SURFACE` | 0.5 | 1.0 | no | `no_assay` | — |
| `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 1.0 | no | `mapped_composite_not_validating` | — |

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

### `anti_lif` — Full cocktail + LIF/LIFR neutralisation

Background `hormone_treated_maternal`; biologic; `new_arm`.

* **Assay:** pSTAT3 is a new assay class for this platform.
* **Feasibility:** Neutralising antibody; needs its own engagement control.
* **Committed model, downstream of the intervention:** `E_CD98_CD9`, `E_GP130_STAT3`, `E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE`

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

### `anti_lif_plus_il11` — Full cocktail + LIF neutralisation + recombinant IL-11

Background `hormone_treated_maternal`; biologic+reagent_addition; `new_arm`.

* **Assay:** pSTAT3 is a new assay class for this platform.
* **Feasibility:** Violates the one-perturbation preference.
* **Committed model, downstream of the intervention:** `E_CD98_CD9`, `E_GP130_STAT3`, `E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE`

**GP130: GP130-a vs GP130-b**

| Node | GP130-a | GP130-b | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_GP130_STAT3` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_RECEPTIVE_SURFACE` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `OUT_EPITHELIAL_RECEPTIVE` | 0.0 | 1.0 | **yes** | `mapped_composite_not_validating` | — |

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.0 | 1.0 | **yes** | `no_assay` | — |

### `smo_antagonist` — Full cocktail + SMO antagonist (Hedgehog reception blockade)

Background `hormone_treated_maternal`; small_molecule; `new_arm`.

* **Assay:** IGFBP-1/PRL need no new assay. A GLI1/PTCH1 pathway-activity readout in the stromal channel is new and is REQUIRED, because the committed model predicts no change and a null is otherwise indistinguishable from failed target engagement.
* **Feasibility:** Small molecule on both channels. GAP-014's proposed_resolution names this arm. The clamp is an INTERPRETATION of the intervention, not a model of it: the network has no reception node, so blockade is applied to S_NR2F2 directly. That is defensible only because S_NR2F2 is aliased to E_IHH, and it would stop being defensible the moment a reception node existed.
* **Committed model, downstream of the intervention:** **nothing propagates**

**HH: HH-a vs HH-b**

| Node | HH-a | HH-b | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `OUT_STROMAL_DECIDUALIZED` | 1.0 | 0.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_BMP2` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_DECIDUALIZED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_IGFBP1` | 1.0 | 0.0 | **yes** | `usable_assay` | IGFBP-1 (bottom outlet) |
| `S_PRL` | 1.0 | 0.0 | **yes** | `mapped_composite_not_validating` | — |
| `S_SPP1` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `S_TAZ_ECM` | 1.0 | 0.0 | **yes** | `no_assay` | — |

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

### `bmpr_inhibitor` — Full cocktail + BMP type-I receptor inhibitor

Background `hormone_treated_maternal`; small_molecule; `new_arm`.

* **Assay:** IGFBP-1/PRL need no new assay.
* **Feasibility:** Clamps a node the committed rules already make necessary for S_DECIDUALIZED, so the committed prediction is a near-certain loss of both stromal analytes.
* **Committed model, downstream of the intervention:** `OUT_STROMAL_DECIDUALIZED`, `S_DECIDUALIZED`, `S_IGFBP1`, `S_PRL`, `S_SPP1`, `S_TAZ_ECM`

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

### `pc6_knockdown` — Full cocktail + PC6/PCSK5 knockdown

Background `hormone_treated_maternal`; construct; `new_arm`.

* **Assay:** alpha-DG-N shedding is a new assay class.
* **Feasibility:** siRNA/shRNA in the epithelial channel.
* **Committed model, downstream of the intervention:** `E_DAG1_CLEAVED`, `E_DAG1_FULL`, `E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE`

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

### `dag1_cleavage_resistant` — Full cocktail + cleavage-resistant alpha-dystroglycan construct

Background `hormone_treated_maternal`; construct; `new_arm`.

* **Assay:** alpha-DG-N shedding is a new assay class.
* **Feasibility:** Requires transfecting primary epithelium with a mutant substrate; the candidate table records the determinant as absent from ADOC.
* **Committed model, downstream of the intervention:** **nothing propagates**

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**PC6: PC6-a vs PC6-b**

| Node | PC6-a | PC6-b | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_DAG1_CLEAVED` | 1.0 | 0.0 | **yes** | `no_assay` | — |
| `E_DAG1_FULL` | 0.0 | 1.0 | **yes** | `no_assay` | — |
| `E_RECEPTIVE_SURFACE` | 0.5 | 0.0 | no | `no_assay` | — |
| `OUT_EPITHELIAL_RECEPTIVE` | 0.5 | 0.0 | no | `mapped_composite_not_validating` | — |

### `anti_spp1` — Full cocktail + anti-SPP1

Background `hormone_treated_maternal`; biologic; `new_arm`.

* **Assay:** No maternal readout exists: identifiability.py reports IN_ANTI_SPP1 as set_alone_no_shared_readout.
* **Feasibility:** Neutralising antibody.
* **Committed model, downstream of the intervention:** **nothing propagates**

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

### `hand2_loss` — Full cocktail + siHAND2

Background `hormone_treated_maternal`; construct; `new_arm`.

* **Assay:** HAND2 and FGF readouts are a new assay class.
* **Feasibility:** siRNA in the stromal channel.
* **Committed model, downstream of the intervention:** `E_ESTROGENIC_PROLIFERATION`, `E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE`, `S_FGF_MITOGENIC`, `S_HAND2`

**CD98: CD98-a vs CD98-c**

| Node | CD98-a | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-a vs CD98-x**

| Node | CD98-a | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-c**

| Node | CD98-b | CD98-c | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

**CD98: CD98-b vs CD98-x**

| Node | CD98-b | CD98-x | opposite | readout tier | analyte |
|---|---|---|---|---|---|
| `E_CD98_CD9` | 0.5 | 1.0 | no | `no_assay` | — |

