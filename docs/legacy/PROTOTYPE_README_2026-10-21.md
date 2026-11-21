# DT_ADOC

DT_ADOC builds a stochastic Boolean (MaBoSS) model of the human endometrium's
hormone response and its receptivity to embryo adhesion, anchored to the **ADOC**
organ-on-chip experiments. The long-term aim is a donor-contextualized digital
twin that can screen hypotheses for non-hormonal contraception.

"Digital twin" here means a **patient-contextualized computational hypothesis
model**, not a clinically validated replica or a treatment recommender. MaBoSS
probabilities are simulated occupancies under stated rules and initial
conditions, not clinical outcome probabilities, and a simulated perturbation is a
conditional model prediction, not causal evidence.

## Where the project stands (2026-10-18)

| | state |
|---|---|
| **Model versions** | `adoc-literature-superset-v0.4.0` is the immutable executable parent. `v0.5.0` is a **scaffold**: its executable files are **byte-identical to v0.4.0** ([`docs/v05_u5_structural_audit.md`](docs/v05_u5_structural_audit.md)). It is not a new biological model. `v0.5.1` adds one repaired rule: `OUT_STROMAL_DECIDUALIZED` is no longer gated on the PRL/IGFBP1 markers ([`docs/v05_u5b_readout_repair.md`](docs/v05_u5b_readout_repair.md)). `v0.5.2` is `v0.5.1` plus two rules from the 163-paper re-audit ([`docs/v052_paep_hand2_cleanup.md`](docs/v052_paep_hand2_cleanup.md)). **C1** takes PAEP out of `OUT_EPITHELIAL_RECEPTIVE`. **C5** makes HAND2 act on epithelial proliferation only through the stromal relay; this is a semantic change. No node's composed Boolean function over the free variables changes in any of them; transients do, and are measured. `v0.6.0` is the current executable increment: `v0.5.2` without its three intervention-marker inputs (`IN_MIFEPRISTONE`, `IN_ANTI_SPP1`, `IN_HAND2_LOSS`), with interventions timed by the protocol/intervention layer (`config/protocols_markerless.yaml`). Gate G8 shows it reproduces `v0.5.2` trajectory for trajectory at seeds 1–3 in the pinned MaBoSS runtime ([`docs/intervention_layer_stage3.md`](docs/intervention_layer_stage3.md)). Its structure is recomputed in [`docs/intervention_layer_stage3/structure_counts.json`](docs/intervention_layer_stage3/structure_counts.json) (see [below](#what-the-model-cannot-distinguish)). |
| **Which version each result uses** | Each analysis pins its own version, and the marker removal repointed none of them ([`docs/intervention_layer_stage3.md`](docs/intervention_layer_stage3.md) §12–13). `v0.4.0`: model-data concordance, the scRNA node-support audit and the calibration candidates. `v0.5.0` (executable-identical to `v0.4.0`): the U5 structural, identifiability and design audit, and the functional-endpoint figure. `v0.5.1`: the U8 Stage-3 rerank and the RNA endpoint concordance. `v0.5.2`: C3a. `v0.6.0`: the current structural counts, the Stage 4b/4c admission work and the identifiability-design analysis. Of the README figures, the network overview and the exploratory dynamics animation are rendered from `v0.6.0`; the functional-endpoint figure stays a historical `v0.5.0` render. |
| **Calibration** | **None.** The adhesion objective was demoted to an ordinal diagnostic (`config/calibration.yaml`); no magnitude is fitted, and no quantitative objective exists. |
| **Validation** | **None.** One ordinal claim holds; no quantity is reproduced. |
| **Personalization** | Input contract only (Phase 2A, [`docs/phase2a/phase2a_contract.md`](docs/phase2a/phase2a_contract.md)): numerical mapping is **blocked**. Phase 2B closed as **`NO_SUITABLE_REFERENCE`** ([`docs/phase2b_c4/PHASE2B_CLOSED.md`](docs/phase2b_c4/PHASE2B_CLOSED.md)): the only qualifying external reference (E-MTAB-10283) shows no stable two-state KLF12 separation under the pre-registered procedure, so no KLF12-high definition exists. Any future value is an assumption-conditioned scenario, not measured personalization. No donor-specific model exists. |
| **Observation model** | C2 ([`docs/c2_observation_compartments/attribution_report.md`](docs/c2_observation_compartments/attribution_report.md)): PRL is stromal-attributed, IGFBP-1 is compartment-ambiguous between epithelium and stroma, PAEP is a glandular/global secretory readout, and an SPP1 outlet would read a mixed free-ligand pool. The frozen observation map is unchanged. OM-002 stays an active diagnostic on the computational proxy `S_IGFBP1`, and current outputs carry that ambiguity (CA-002). |
| **Kinetic readouts** | C3a, pre-registered and run on `v0.5.2` ([`docs/c3_kinetic_readouts/execution_note.md`](docs/c3_kinetic_readouts/execution_note.md)). Mifepristone and HAND2 loss give **persistent fixed-point suppression** of stable adhesion (about −0.82 against a schedule-matched twin, under unit MaBoSS rates). The declared challenge window sits at the adhesion floor even in controls, so C3a **cannot distinguish delay from block**. No rate values exist; C3b is deferred. |
| **Verification** | `pixi run test` is the complete, required pre-merge check (every directory under `tests/`; 2,415 tests, 1 skip, 1,957.6 s single-core on the 2026-10-16 benchmark after the expression and registry caches, down from 3,496 s; [`docs/verification/cache_design.md`](docs/verification/cache_design.md), [`cache_benchmark_record.json`](docs/verification/cache_benchmark_record.json)). `pixi run test-guards` is a fast integrity and provenance guard (238 tests, about 31 s), not a substitute for it ([`docs/verification/README.md`](docs/verification/README.md)). `pixi run lint` and `pixi run format-check` pass (ruff 0.16.0; two pinned files are left out of formatting, see [Checks](#checks)). |
| **Next stage** | One **prospective discriminating experiment** (frozen, `dropout_e2`), waiting on lab data; not more topology. The v0.5 topology line is paused pending it ([`docs/v05_pause_decision_2026-09-30.md`](docs/v05_pause_decision_2026-09-30.md)). The intervention layer, which the pause does not cover, made interventions markerless (`v0.6.0`). Its first real direct admission was refused as **`NOT_ADMISSIBLE_YET`** (Stage 4c, [`docs/stage4c_admission_refusal.md`](docs/stage4c_admission_refusal.md)), and Stage 4d stays blocked. Two later analyses are for owner review only, and neither replaces the frozen arm. The identifiability-design analysis on `v0.6.0` makes a scoped, conditional recommendation and is not pre-registered ([`docs/identifiability_experiment_design.md`](docs/identifiability_experiment_design.md)). The drug-only calibration-candidate review establishes **no comparative ranking** ([`docs/drug_only_calibration_candidates.md`](docs/drug_only_calibration_candidates.md)). |

## What is measured and what is simulated

**Measured by ADOC** (manuscript protocol: 2 days of 10 nM E2, then 4 days of
E2 + 1 µM MPA + 250 µM cAMP + 10 µM XAV939; mifepristone 10 µM afterwards):

- **stable blastocyst adhesion** after flushing — 0/12 untreated, 9/19
  hormone-treated, 1/8 with mifepristone. Per-embryo counts, not donor-level
  outcomes;
- three **secreted proteins** by ELISA, with the compartments C2 attributes them
  to:
  - PAEP: a glandular/global secretory readout of uncertain compartment purity;
    the outlet it was sampled from is unverified (`OM-001`);
  - IGFBP-1: compartment-ambiguous between epithelium and stroma, since apical
    IGFBP-1 rises too;
  - PRL: basal outlet only, stromal-attributed;
- donor-resolved **scRNA-seq** (E-MTAB-15842, HT sequenced at the end of the
  hormonal protocol). It is used to audit node support and as an
  end-of-treatment readout compared with the model's predicted endpoint, never
  as node activity or as a t = 0 input.

A chip is **not** an independent biological replicate: chips can share donors,
epithelial and stromal cells in one chip may come from different donors, and the
column-to-chip mapping for IGFBP-1 and PRL was lost
([`config/adoc_chip_donor_provenance.tsv`](config/adoc_chip_donor_provenance.tsv)).

**Simulated.** Every node's `P(ON)` along the protocol lineage basal → E2-primed →
hormone-conditioned (→ mifepristone) → embryo challenge. MaBoSS time is
dimensionless and has no mapping to days. Two model nodes have an active ADOC
observation mapping: `E_PAEP`, and `S_IGFBP1` as the computational proxy for a
compartment-ambiguous measurement. One carries the ordinal adhesion
endpoint (`OUT_STABLE_ADHESION`), `S_PRL` is assayed but its mapping is only
provisional, and the two composite outputs carry reported-only mappings with
zero source rows.

## The executable network

![Executable MaBoSS network of adoc-literature-superset-v0.6.0](docs/assets/adoc_network_overview_v0.6.0.png)

> Every node and dependency is derived from the `v0.6.0` `network.bnd` (`pixi run
> render-network`; deterministic, no simulation). Bands give the compartment;
> arrowheads activate and bars inhibit; dotted edges are absorbed or never bind.
> Heavy borders are free variables (set, not computed); hatched nodes cannot
> change any phenotype output. Letters mark exact Boolean aliases, spelled out
> on the right. ● = active ADOC observation mapping, ◆ = functional endpoint
> (ordinal only), ○ = assayed, provisional mapping, ◇ = reported composite mapping
> with no source rows. The sidecar
> [`adoc_network_overview_v0.6.0_metadata.json`](docs/assets/adoc_network_overview_v0.6.0_metadata.json)
> records every count, alias roster and absorbed or never-binding edge, the
> hashes of every input and generator file, and the clean commit it was rendered
> from.
>
> This is the **unperturbed** `v0.6.0` network. Mifepristone, anti-SPP1 and HAND2
> loss are no longer nodes, so they are not drawn. The protocol layer applies
> them per step as rule vetoes (`config/protocols_markerless.yaml`), and a veto
> can separate nodes that share a letter here. The `v0.5.0` render, with the
> three marker inputs, is kept as a historical artifact (below).

## The functional endpoint against experiment

![Stable embryo adhesion: ADOC observation vs MaBoSS simulation](docs/assets/adoc_functional_endpoint_v0.5.0.png)

> **A historical `v0.5.0` render; not regenerated for `v0.6.0`.** The pipeline
> is pinned to `v0.5.0` (`MODEL_VERSION` in
> `src/dt_adoc/reporting/endpoint_replicates.py`). Its exact converged values
> read each arm's treatment from the protocol's marker `input_states`, so on
> `v0.6.0` it would score the mifepristone arm as untreated. A `v0.6.0` endpoint
> figure needs an intervention-aware pipeline, which does not exist yet.
> `pixi run render-endpoint` re-renders the `v0.5.0` figure from the tracked
> replicate rows in [`docs/endpoint/`](docs/endpoint/README.md).
>
> **The two kinds of error bar are not comparable.** Observed: Wilson 95% CI on the per-embryo proportion (it
> ignores chip/donor clustering, which cannot be reconstructed). Simulated: mean
> ± 1 SD across complete MaBoSS runs on seed blocks **disjoint between replicate
> indices** (the same block is reused across arms and horizons, a paired design). That SD is only
> the simulator's run-to-run reproducibility: it is not biological uncertainty,
> not an i.i.d. Monte Carlo SE, and not MaBoSS's node error column. Panel B
> magnifies it because it is invisible at figure scale. See
> [`docs/maboss_estimator_semantics.md`](docs/maboss_estimator_semantics.md),
> including its 2026-09-23 addendum: a MaBoSS run is the union of
> single-trajectory runs on consecutive seeds, so runs whose seeds differ by less
> than the trajectory count share almost all their trajectories.

What the figure supports is **only the ordering** untreated < hormone-treated >
mifepristone at the converged horizon. In `v0.5.0` (U5 audit), the converged
hormone-treated value is `1 − (1 − 0.70)(1 − 0.40) = 0.82`, two hand-typed interface-relay priors in
`baseline.cfg`, not a fit; the observed 9/19 interval excludes it. The declared
phase durations are ~4000× shorter than the time the endpoint needs to reach its
fixed point ([`docs/endpoint_convergence_finding.md`](docs/endpoint_convergence_finding.md)),
and there the simulated endpoint is about four orders of magnitude below its
converged value. At the adopted converged readout the model predicts exactly 0
under mifepristone against 1/8 observed, and no maternal rule has been changed to
accommodate it.

## Exploratory dynamics

![MaBoSS pathway dynamics through the ADOC protocol sequence](docs/assets/adoc_superset_pathway_dynamics_v0.6.0.gif)

> **Exploratory dynamics.** Node `P(ON)` through the protocol sequence (basal →
> E2-primed → hormone-treated → adhesion challenge) for `v0.6.0`, the current
> markerless executable increment. Interventions are timed by the
> protocol/intervention layer (`config/protocols_markerless.yaml`), not by the
> retired marker nodes, and this sequence applies none. MaBoSS time is
> dimensionless and is not mapped to experimental days; trajectories should be
> interpreted qualitatively, not as calibrated temporal predictions.
>
> Rendered from `adoc-literature-superset-v0.6.0` with `pixi run
> render-dynamics-superset` (seed 1, 20,000 trajectories, each phase run to its
> fixed point at relative horizon 25; orange dashes mark the declared phase
> durations). The horizon-25 render is a converged, fixed-point-oriented view,
> not a temporal prediction. One seed, so no run-to-run spread is shown; for
> that, see the (`v0.5.0`) endpoint figure above. Provenance:
> [`adoc_superset_pathway_dynamics_v0.6.0_metadata.json`](docs/assets/adoc_superset_pathway_dynamics_v0.6.0_metadata.json).
> The earlier `v0.4.0` and `v0.2.0` animations are kept as reproducibility
> artifacts (see below).
>
> **Phase boundaries are re-initialisations, not predictions.** At each
> boundary only the protocol's declared memory set is carried over as a joint
> distribution; every other non-input node restarts from its model initial
> state, and the new phase's inputs are forced. Basal → E2-primed and
> hormone-treated → adhesion challenge carry `minimal_stable_joint` (17 nodes),
> E2-primed → hormone-treated carries `extended_maternal_joint` (35 nodes)
> (`src/dt_adoc/model/runtime.py`). The drops at t = 75 (for example `E_PAEP`,
> `S_PRL` and `S_IGFBP1` from 1.00 to about 0.05, and adhesion competence from
> 0.82 to 0) are such restarts with the hormone inputs still ON. The dip in
> carried nodes over the next few time units (`S_DECIDUALIZED` to about 0.47)
> follows from restarting `E_PGR`, `S_PGR` and `S_PKA`, which the minimal set
> does not carry. Each first sample after a boundary is a MaBoSS time-window
> mean, not the instantaneous restart value. None of these jumps is a
> biological prediction.

## What the model cannot distinguish

**Current structure (`v0.6.0`)**, exhaustive over all 2^16 = 65,536
free-variable assignments. Every count is from
[`docs/intervention_layer_stage3/structure_counts.json`](docs/intervention_layer_stage3/structure_counts.json).
The absorbed and never-binding edges are from the network figure's sidecar,
computed by the same code (`dt_adoc.reporting.structure`).

- **56 named nodes implement 29 distinct Boolean functions**, in 7 alias
  classes. The 16 free variables are the 11 input nodes plus `E_KLF12_HIGH` and
  four interface relays.
  - `E_PAEP` sits in a 9-member epithelial secretory class.
  - `S_IGFBP1 = S_PRL` and four more nodes are one stromal decidual function,
    so the IGFBP-1-before-PRL onset order ADOC observes cannot be represented.
  - `IN_PROGESTIN = E_PGR = E_IHH = S_PGR = S_NR2F2 = S_BMP2 = S_HAND2` is a
    single progesterone variable. In `v0.5.x` the class had five members. With
    the mifepristone and HAND2-loss markers gone, the unperturbed `E_PGR`,
    `S_PGR` and `S_HAND2` compute `IN_PROGESTIN` itself.
  - `E_LIF = E_GP130_STAT3 = E_CD98_CD9` now also equals
    `E_RECEPTIVE_SURFACE = OUT_EPITHELIAL_RECEPTIVE`, which was a separate class
    in `v0.5.x`.
- **20 of 89 dependencies are absorbed or never bind** (15 absorbed, 5
  inhibitions that never bind).
- **17 nodes cannot change any phenotype output**, among them `E_PAEP`,
  `S_IGFBP1` and `S_PRL`, the model nodes of all three ELISA analytes.
- **3 declared inputs are read by no rule**: `IN_XAV939`, `IN_HCG` and
  `IN_EMBRYO_CONDITIONED_SIGNAL`.
- The four **interface relays** are free variables with typed-in priors.
- These counts describe the **unperturbed** network. An intervention renders a
  different network and can break an alias here: the mifepristone veto
  separates `E_PGR` and `S_PGR` from `IN_PROGESTIN` again. No bound over
  intervened networks has been computed
  ([`docs/intervention_layer_stage3.md`](docs/intervention_layer_stage3.md) §14).

**Pinned historical results: the U5 audit of `v0.5.0`**, executable-identical
to `v0.4.0` ([`docs/v05_u5_structural_audit.md`](docs/v05_u5_structural_audit.md)).

- Exhaustive over all 2^19 free-variable assignments of that version:
  **59 named nodes implement 35 distinct Boolean functions**, and **19 of 97
  dependencies** are absorbed or never bind. 14 nodes cannot change any
  phenotype output.
- `v0.5.1` and `v0.5.2` keep the same 59-node set and every composed function.
  What changes is the dependency and readout structure:
  - executable dependencies fall to 95, then 93;
  - the phenotype-inert set grows to 16, then 17 nodes.

  Sources: [`docs/v05_u5b_readout_repair.md`](docs/v05_u5b_readout_repair.md)
  and `structure_counts.json`.

The design and identifiability numbers below come from the same audit. They
were **not recomputed** for `v0.5.2` or `v0.6.0`. The static design tooling
reads an arm's exposure from its condition cfg, so on `v0.6.0` it would read
the treated arms as untreated, and it is deliberately not repointed
([`docs/intervention_layer_stage3.md`](docs/intervention_layer_stage3.md) §12).
An intervention-aware design analysis would be its own unit. On `v0.5.0`:

- The adhesion endpoint is a function of two relay priors. Even with every
  proposed arm and every assayable readout, a matched-unit design would reach
  **8 of 32** latent observation classes.
- Under the existing arms the whole hormone cocktail moves as one bundle, so
  **PAEP and IGFBP-1 carry the same design information**: 19 design-effective
  states out of 35.
- Design and identifiability counts are matched-unit conditional
  ([`docs/identifiability_analysis.md`](docs/identifiability_analysis.md),
  [`docs/design_alias_note.md`](docs/design_alias_note.md)).

## What the transcriptome adds

Three pre-registered units read the deposited scRNA object (`E-MTAB-15842`).
None changed a rule, a relay or an initial condition.

- **Node-support audit** ([`docs/scrna/node_support_finding.md`](docs/scrna/node_support_finding.md),
  on `v0.4`). All 12 primary compartment-units pass every quality gate.
  - `AC04` (`E_LIF = E_GP130_STAT3 = E_CD98_CD9`) is **rule-challenged**: there
    is no material response where the rule predicts one.
  - `AC01`, the epithelial secretory class, is **alias-challenged**.
  - `AC03` stays unidentified.
  - Its proposed changes are recorded, not implemented.
- **KLF12 prior** ([`docs/scrna/klf12_prior_finding.md`](docs/scrna/klf12_prior_finding.md)).
  These data do not establish a measured prior for `E_KLF12_HIGH`, and nothing
  was activated. Phase 2B then found no suitable external reference either (see
  the Personalization row above).
- **RNA ↔ MaBoSS endpoint concordance** ([`docs/rna_endpoint_concordance/report.md`](docs/rna_endpoint_concordance/report.md),
  on `v0.5.1`). The end-of-treatment RNA is compared with the model's predicted
  endpoint for 27 RNA-observable nodes:
  - **0 concordant, 0 discordant**;
  - 1 circular agreement (`E_PAEP`, a construction analyte);
  - 2 with no response within two-fold (`E_LIF`, `E_GP130_STAT3`), which is
    reported as a measurement, not as discordance;
  - the rest mixed, or reported and not scored.

  The RNA supports no predicted endpoint switch in a way that counts as
  evidence.

## The experimental-design conclusion

The next evidence must come from an experiment that **separates** what the model
currently aliases, not from adding topology. Stage 3, computed on the frozen
`v0.4.0` model, froze one prospective arm
([`docs/stage3_experiment_selection.md`](docs/stage3_experiment_selection.md)
§12). U8 found the `v0.5.1` computation identical in every quantity the ranking
reads ([`docs/v05_u8_stage3_rerank.md`](docs/v05_u8_stage3_rerank.md)). The arm
is **the hormone cocktail with E2 omitted** on days 2–6 (MPA + cAMP + XAV939,
after normal E2 priming), read by the three existing ELISAs, with contemporaneous
full-cocktail and E2-only controls on the same donors. Of the 112 candidate
fifth arms, only single-component dropouts of E2 or of cAMP separate the two
active readouts, and minus-E2 resolves the most design states while doing so
(+3 against +2). The runner-up is an SMO antagonist. A review of 17 further candidates
([`docs/experiment_candidate_review_2026-09-22.md`](docs/experiment_candidate_review_2026-09-22.md))
found every other proposed readout needs a new assay first.

In U3, U4 and U4b the largest available structural gain was refused on
evidence each time ([`docs/v05_mechanistic_integration_plan.md`](docs/v05_mechanistic_integration_plan.md)).
Unrestricted topology expansion is therefore **not** the next step: new nodes
would add aliases faster than any current assay can resolve them.

Two later analyses, both for owner review, do not replace this frozen arm.
[`docs/identifiability_experiment_design.md`](docs/identifiability_experiment_design.md)
asks which single perturbation would most reduce ambiguity in `v0.6.0`. It finds
that one perturbation de-aliases nothing. Its recommendation is scoped and
conditional, and it is not a pre-registration.
[`docs/drug_only_calibration_candidates.md`](docs/drug_only_calibration_candidates.md)
evaluates drug-only candidates one at a time and establishes no comparative
ranking.

## Where the detail lives

| question | document |
|---|---|
| v0.5 unit plan and status (U1–U8) | [`docs/v05_mechanistic_integration_plan.md`](docs/v05_mechanistic_integration_plan.md) |
| U5 structural, identifiability and design audit (`v0.5.0`, historical) | [`docs/v05_u5_structural_audit.md`](docs/v05_u5_structural_audit.md) |
| U5b readout repair (v0.5.1) | [`docs/v05_u5b_readout_repair.md`](docs/v05_u5b_readout_repair.md) |
| U6 node semantics and component map (schema only) | [`docs/v05_u6_semantics_components.md`](docs/v05_u6_semantics_components.md) |
| U6b `E_MUC1_BARRIER` rule family (evaluation only) | [`docs/v05_u6b_muc1_reconciliation.md`](docs/v05_u6b_muc1_reconciliation.md) |
| U8 Stage-3 rerank against v0.5.1 | [`docs/v05_u8_stage3_rerank.md`](docs/v05_u8_stage3_rerank.md) |
| v0.5.2: C1 (PAEP readout) and C5 (HAND2 routing) | [`docs/v052_paep_hand2_cleanup.md`](docs/v052_paep_hand2_cleanup.md) |
| **v0.6.0** (current): marker removal, gate G8, and the current structural counts | [`docs/intervention_layer_stage3.md`](docs/intervention_layer_stage3.md), [`docs/intervention_layer_stage3/structure_counts.json`](docs/intervention_layer_stage3/structure_counts.json), [`models/superset/adoc-literature-superset-v0.6.0/README.md`](models/superset/adoc-literature-superset-v0.6.0/README.md), [`provenance.toml`](models/superset/adoc-literature-superset-v0.6.0/provenance.toml), [`config/protocols_markerless.yaml`](config/protocols_markerless.yaml) |
| intervention layer: plan, markerless interventions, admission (Stage 4b) and its refusal (Stage 4c) | [`docs/intervention_layer_refactor_plan.md`](docs/intervention_layer_refactor_plan.md), [`docs/o8_markerless_interventions.md`](docs/o8_markerless_interventions.md), [`docs/stage4b_direct_admission.md`](docs/stage4b_direct_admission.md), [`docs/stage4c_admission_refusal.md`](docs/stage4c_admission_refusal.md) |
| identifiability-driven design and drug-only candidates (analyses for owner review, not pre-registered) | [`docs/identifiability_experiment_design.md`](docs/identifiability_experiment_design.md), [`docs/drug_only_calibration_candidates.md`](docs/drug_only_calibration_candidates.md) |
| 163-paper re-audit (owner input) and the verified active evidence set | [`context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md`](context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md), [`context/literature/active_evidence_manifest.tsv`](context/literature/active_evidence_manifest.tsv) |
| C2 observation compartment attribution | [`docs/c2_observation_compartments/attribution_report.md`](docs/c2_observation_compartments/attribution_report.md), [`context/observation_compartment_attribution.tsv`](context/observation_compartment_attribution.tsv) |
| C3a kinetic readouts: pre-registration, addendum, results | [`docs/c3_kinetic_readouts/preregistration.md`](docs/c3_kinetic_readouts/preregistration.md), [`docs/c3_kinetic_readouts/preregistration_addendum_01.md`](docs/c3_kinetic_readouts/preregistration_addendum_01.md), [`docs/c3_kinetic_readouts/execution_note.md`](docs/c3_kinetic_readouts/execution_note.md) |
| scRNA node support and the KLF12 prior | [`docs/scrna/node_support_finding.md`](docs/scrna/node_support_finding.md), [`docs/scrna/klf12_prior_finding.md`](docs/scrna/klf12_prior_finding.md) |
| RNA ↔ MaBoSS endpoint concordance | [`docs/rna_endpoint_concordance/report.md`](docs/rna_endpoint_concordance/report.md) |
| personalization: Phase 2A contract and Phase 2B closure | [`docs/phase2a/phase2a_contract.md`](docs/phase2a/phase2a_contract.md), [`docs/phase2b_c4/PHASE2B_CLOSED.md`](docs/phase2b_c4/PHASE2B_CLOSED.md) |
| deferred topology register (TI-03, TI-04, TI-06) | [`docs/deferred_topology_register.tsv`](docs/deferred_topology_register.tsv) |
| what a MaBoSS number estimates | [`docs/maboss_estimator_semantics.md`](docs/maboss_estimator_semantics.md) |
| model-data concordance, row by row | [`docs/concordance_analysis.md`](docs/concordance_analysis.md) |
| observation mappings | [`config/observation_model_map.tsv`](config/observation_model_map.tsv) |
| calibration status and its demotion | [`config/calibration.yaml`](config/calibration.yaml), [`docs/gate3_scope_adjudication.md`](docs/gate3_scope_adjudication.md) |
| scientific question and readout contract | [`context/project-context.md`](context/project-context.md), [`context/phase1-readouts.tsv`](context/phase1-readouts.tsv) |
| review policy | [`docs/scientific-review-policy.md`](docs/scientific-review-policy.md) |

### Secondary and historical figures

Retained for reproducibility; none is the current primary view.

- [`adoc_network_overview_v0.5.0.png`](docs/assets/adoc_network_overview_v0.5.0.png) —
  the network overview of `v0.5.0`, with the three intervention-marker inputs and
  a sidecar proving its byte-identity to `v0.4.0`. Superseded by the `v0.6.0`
  render; regenerate it with `pixi run render-network-v050`.
- [`adoc_concordance_v0.4.0.png`](docs/assets/adoc_concordance_v0.4.0.png) — concordance
  of v0.4 with 60 curated result rows. Its panel A predates the disjoint-seed
  replicates and quotes an across-seed spread over overlapping seeds 1–5; on
  disjoint blocks the declared-horizon mifepristone value is below, not above,
  the hormone-treated one ([`docs/v05_u5_structural_audit.md`](docs/v05_u5_structural_audit.md) §6).
- [`adoc_superset_structure_v0.4.0.png`](docs/assets/adoc_superset_structure_v0.4.0.png) —
  the earlier depth-layered structural figure, superseded by the network overview.
- [`adoc_identifiability_…v0.4.0.png`](docs/assets/adoc_identifiability_adoc-literature-superset-v0.4.0.png)
  and the design-alias figures in `docs/assets/`.
- [`adoc_superset_pathway_dynamics_v0.4.0.gif`](docs/assets/adoc_superset_pathway_dynamics_v0.4.0.gif) —
  the earlier README animation of v0.4.0 (59 nodes, with the intervention-marker
  inputs), superseded by the v0.6.0 render; its metadata sits beside it.
- [`adoc_maboss_pathway_dynamics.gif`](docs/assets/adoc_maboss_pathway_dynamics.gif) —
  the frozen v0.2.0 animation, with known edge defects.

## Repository map

| Path | Purpose |
|---|---|
| `data/` | Immutable source datasets and papers (`data/README.md`) |
| `config/` | Manifests, protocols, calibration, observation mappings, planned design |
| `context/` | Scientific question, evidence register, literature package |
| `models/` | Versioned MaBoSS models: `superset/` (v0.3–v0.6.0), `extended/` (v0.2), `baseline/` (v0.1) |
| `src/dt_adoc/` | Simulation, protocols, calibration, reporting and audit code |
| `docs/` | Audits, plans, generated tables and figures (`docs/assets/`) |
| `tests/` | Unit and integration guards |
| `.codex/` | Agent roles, skills and harness contracts |

## Checks

```bash
pixi run harness-check
pixi run test          # complete suite: the required pre-merge check
pixi run test-guards   # fast integrity/provenance guard; not a substitute for `test`
pixi run test-parallel # optional: the same suite on two workers; `test` stays required
pixi run run-record    # run the required checks on HEAD and write the PR's run record
pixi run check-run-record  # the committed record covers the code at HEAD
pixi run lint
pixi run format-check
pixi run validate-models
python -B .codex/skills/adoc-data-audit/scripts/check_data_manifest.py --root . --check-hashes
```

`pixi run test` passed on the 2026-10-16 benchmark (2,415 tests, 1 skip;
[`docs/verification/cache_benchmark_record.json`](docs/verification/cache_benchmark_record.json)).
`pixi run test-guards` covers the recorded implementation digests, frozen
evidence, closed phases and committed-table regeneration only
([`docs/verification/README.md`](docs/verification/README.md)).
`pixi run lint` and `pixi run format-check` pass (ruff 0.16.0). The earlier
baseline of 75 lint errors and 16 unformatted files was cleared without changing
behaviour: every edited file under `src/` parses to the same syntax tree as
before, and so does every edited test file except two, whose lint fixes are
equivalent rewrites (an unused import and unused names removed, a `dict()` call
written as a literal, nested `with` statements merged). Two
files are deliberately left out of formatting (`ruff.toml`):
`src/dt_adoc/protocols/conditions.py`, which the implementation digest covers,
and `src/dt_adoc/observations/compartment_attribution.py`, which the closed C2
overlay pins by hash.

Regenerating the README's artifacts:

| artifact | version | command |
|---|---|---|
| network overview | `v0.6.0` (current) | `pixi run render-network` |
| exploratory dynamics animation | `v0.6.0` (current) | `pixi run render-dynamics-superset` (needs MaBoSS) |
| current structural counts | `v0.5.2` and `v0.6.0` | `docs/intervention_layer_stage3/structure_counts.json`, written by `PYTHONPATH=src python -m dt_adoc.reporting.stage3_g8 --structure` (no MaBoSS) and recomputed by `tests/unit/test_v060_marker_removal.py` |
| functional-endpoint figure | `v0.5.0` (historical) | `pixi run render-endpoint`, from `pixi run build-endpoint-replicates` |
| U5 structural, identifiability and design audit | `v0.5.0` (historical) | `pixi run u5-structural-audit` |
| historical network overview | `v0.5.0` | `pixi run render-network-v050` |

`u5-structural-audit` does **not** produce the current `v0.6.0` counts. The
replicate simulation is memory-hungry, so see
[`docs/endpoint/README.md`](docs/endpoint/README.md) before running it. A
missing MaBoSS, R or Seurat runtime must be reported, never silently bypassed.

`pixi run chatgpt-results-bundle` writes a compact, hash-manifested archive of
source, models, docs and eligible results under `output/reports/`.
