# Research foundation audit

A factual inventory of the research completed in the prototype before
ENDO-TWIN, written to establish exactly what this repository may claim.

**Scope and method.** Every number below was recomputed from committed files by
`src/endotwin/foundation_metrics.py` (`pixi run endotwin-metrics`, output
`docs/research_foundation_metrics.json`); the file and filter behind each count
are named. Where a figure circulated in earlier summaries could not be
reproduced from the files, this audit says so. Source commit:
`b1de5f90582f02291789eb72753fa5ab1f2d8c88` (`docs/ORIGIN.md`).

Historical achievements (prototype, models `v0.1.0`-`v0.6.0`) are kept separate
from the current executable ENDO-TWIN mainline (`endotwin-v0.1.0`).

---

## 1. Verification of the headline figures

| Circulated figure | Verified value | Source | Verdict |
|---|---|---|---|
| ~56 named Boolean nodes | **56** in `adoc-literature-superset-v0.6.0` | `models/superset/adoc-literature-superset-v0.6.0/network.bnd` | Confirmed (v0.6.0) |
| ~89 regulatory dependencies | **89** (76 activating, 13 inhibitory) in v0.6.0 | same; also `docs/intervention_layer_stage3/structure_counts.json` | Confirmed (v0.6.0) |
| ~29 distinct composed Boolean functions | **29** in v0.6.0, exhaustive over 2^16 input assignments | recomputed independently by `src/endotwin/structure.py`; matches the prototype record | Confirmed (v0.6.0) |
| 163-paper literature re-audit | The re-audit report (`context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md`) states a **163-PDF corpus**; it enumerates a **36-paper** recommended evidence set (20 core, 10 rule-variant, 1 boundary, 5 reviews) | parsed from the report | **Partly verifiable.** The 163-paper list itself is not in the repository; the pass is documented in the report, not as a per-paper table |
| ~2,415 automated tests | **2,415** on 2026-10-16 (OK, 1 skip). At the source commit the suite has grown to **2,767** tests | `docs/verification/cache_benchmark_record.json`; `docs/verification/source_baseline_b1de5f9.json` | Confirmed as a historical count; superseded by 2,767 |
| Published ADOC measurements | 62 secreted-protein rows (39 observed values); adhesion counts on 39 embryos | `input_tables/adoc_secreted_proteins.tsv`, `config/calibration.yaml` | Confirmed |
| scRNA-seq of the ADOC study | E-MTAB-15842: **28,212 cells**, 3 donors, 6 samples | `docs/phase2a/scrna_metadata_extraction.json` | Confirmed (from committed aggregates; the RDS is not in the repository) |
| Sensitivity and identifiability analyses | Identifiability, design-alias and rule-variant analyses exist; initial-condition sensitivity is partial; **transition-rate sensitivity was never run in the prototype** | `docs/identifiability_analysis.md`, `docs/phase1b_closure/` (sensitivity inventory) | Partly. ENDO-TWIN adds a rate-sensitivity analysis (section 6) |
| HAND2 relay changes transients, not steady states | Exact composed-function identity over 2^19 assignments plus a recorded 20-replicate transient difference | `docs/v052_paep_hand2_cleanup.md`, `docs/v052_paep_hand2/transient_comparison.tsv` | Confirmed; ENDO-TWIN reproduces it with a converged-horizon check (section 6) |

## 2. Literature curation

Counts from `literature()` and `evidence()` in `src/endotwin/foundation_metrics.py`.

| Stage | Count | File |
|---|---|---|
| Structured seed search: candidate records | 129 (75 unique DOIs) | `context/literature/searches/adhesion_routes_seed.tsv` |
| 2026-10-21 bundle screen: papers screened | 147 (tier A 52, B 80, C 15) | `context/literature/reviews/adoc_2026-10-21_147_paper_screen.md` |
| 2026-09-28 re-audit: stated corpus | 163 PDFs (not enumerated) | `context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md` |
| 2026-09-28 re-audit: enumerated active evidence set | 36 papers | same, section 15 |
| Registered references (canonical registry) | 95, all with unique DOIs, all 95 resolved against Crossref | `context/literature/references.tsv`, `citation_verification.tsv` |
| PDF manifest | 64 entries, 62 full-text inspected | `context/literature/pdf_manifest.tsv` |
| Active evidence manifest | 50 rows, 49 unique papers | `context/literature/active_evidence_manifest.tsv` |
| Edge-level experimental evidence rows | 276 rows; 247 active, on 85 edges, citing 35 references | `context/evidence/edge_experimental_evidence.tsv` |
| Full-text graded evidence rows | 37 active rows on 27 edges, from 21 references | same, `source_verification = full_text_verified` |
| Citation adjudications (paper attached to or retracted from an edge after full-text reading) | 39 (32 retractions, 7 attachments) | `config/edge_citation_adjudications.tsv`, `context/evidence/post_closure_citation_adjudications_2026-11-18.tsv` |

The corpora were never deduplicated against each other, so these counts must not
be summed into a single "papers reviewed" figure. Details:
[`literature_curation.md`](literature_curation.md).

## 3. Regulatory network and Boolean modelling

Recomputed by `network_versions()`; distinct functions, alias classes,
absorbed or never-binding dependencies and phenotype-inert nodes use the
Prototype definitions (`dt_adoc.reporting.structure`), re-implemented
independently in `src/endotwin/structure.py` and cross-checked against the
recorded v0.6.0 values by `tests/mainline/test_structure_and_hypotheses.py`.

| Version | Nodes | Deps | Act/Inh | E-S crossing deps | Distinct functions | Alias classes | Absorbed or never binding | Phenotype-inert nodes |
|---|---|---|---|---|---|---|---|---|
| adoc-core-v0.1.0 | 43 | 56 | 46/10 | 1 | - | - | - | - |
| adoc-literature-v0.2.0 | 55 | 90 | 77/13 | 1 | - | - | - | - |
| superset-v0.3.0 | 58 | 96 | 79/17 | 3 | 32 | 7 | 20 | 15 |
| superset-v0.4.0 | 59 | 97 | 79/18 | 3 | 35 | 8 | 19 | 14 |
| superset-v0.5.0 | 59 | 97 | 79/18 | 3 | 35 | 8 | 19 | 14 |
| superset-v0.5.1 | 59 | 95 | 77/18 | 3 | 35 | 8 | 19 | 16 |
| superset-v0.5.2 | 59 | 93 | 76/17 | 2 | 35 | 8 | 19 | 17 |
| superset-v0.6.0 | 56 | 89 | 76/13 | 2 | 29 | 7 | 20 | 17 |

"E-S crossing deps" counts direct epithelial-to-stromal or stromal-to-epithelial
dependencies between `E_` and `S_` nodes; the adhesion module's `X_` interface
relays are not counted. Distinct functions were not computed for v0.1.0 and
v0.2.0 (different output conventions).

Further structure of v0.6.0: 85 of its 89 dependencies are declared edges with
an evidence record; 4 execute without provenance (`config/topology_parity_exemptions.tsv`).
Edge confidence: 11 verified, 70 candidate, 4 assumption. 74 of the 85 declared
edges cite at least one non-review primary paper in the experimental evidence
table; 11 rest on in-house ADOC evidence only.

Alternatives considered: 11 candidate rule variants (Gate 3a,
`context/literature/reviews/gate3_candidate_variants_2026-09-16.tsv`), 9
variant pairs computed for discriminability (`docs/experiments/variant_discrimination.tsv`),
a 10-member MUC1 rule family (`docs/u6b_muc1_reconciliation/`), 14 candidate
nodes adjudicated (7 retain catalog only, 3 evidence unverified, 2 wait for
experiment, 1 rule variant only, 1 rejected), 6 entries in the deferred
topology register and 10 unresolved mechanisms in v0.6.0. Two executable rules
were changed as a direct result of the literature re-audit: v0.5.2 **C1** (PAEP
removed from the receptivity output) and **C5** (HAND2 acts on epithelial
proliferation only through the stromal relay).

## 4. Experimental data integrated

Details, units and every provenance problem: [`experimental_data.md`](experimental_data.md).

| Dataset | Content | Unit of replication | Use in the prototype |
|---|---|---|---|
| Secreted proteins (ADOC outlets) | PRL 18 rows (10 observed, 8 no detectable secretion); IGFBP-1 30 rows (19 observed, 11 not detected); PAEP 14 rows (10 observed, 4 missing) | chip-level series; chip-to-donor mapping lost for PRL and IGFBP-1 | PAEP as an ordinal feasibility constraint; IGFBP-1 as a diagnostic; PRL provisional |
| Stable embryo adhesion (legacy endpoint) | untreated 0/12, hormone-treated 9/19, mifepristone 1/8 | embryos, not donors | Ordinal diagnostic; mifepristone held out |
| scRNA-seq E-MTAB-15842 | 28,212 cells; donors 3; samples 6 (control and hormone-treated per donor); 20,441 epithelial and 7,771 stromal cells; 7 cell-state labels | donor | Node-support audit, KLF12 prior, RNA-endpoint concordance |
| E-MTAB-10283 (external organoids) | candidate reference for a KLF12-high state | donor | Phase 2B closed `NO_SUITABLE_REFERENCE` |

## 5. Simulations and analyses completed

25 prototype analyses have a committed result file (all present; listed with
model version in `docs/research_foundation_metrics.json`, key
`completed_analyses`). The principal ones, with the model version each is
pinned to:

| Analysis | Version | Principal result |
|---|---|---|
| Structural, identifiability and design audit (U5) | v0.5.0 | 59 nodes implement 35 functions; 19 of 97 dependencies absorbed or never binding; a matched-unit design reaches 8 of 32 latent observation classes |
| Model-data concordance | v0.4.0 | 60 curated result rows: 36 not expressible, 15 not assessable, 4 calibration-circular, 3 directional, 1 partial, 1 disagreement, 0 quantitative agreement |
| Functional-endpoint replicates | v0.5.0 | Ordering untreated < hormone-treated > mifepristone at the converged horizon only; converged value 0.82 is a product of two typed-in relay priors |
| Endpoint convergence finding | v0.3.0-v0.4.0 | Declared phase durations ~4,000x shorter than the endpoint's fixed-point time |
| C3a pre-registered kinetic readouts | v0.5.2 | Mifepristone and HAND2 loss: persistent fixed-point suppression (about -0.82); cannot distinguish delay from block |
| v0.5.2 paired transient (C1, C5) | v0.5.1 vs v0.5.2 | Proliferation difference +0.043 to +0.167 (phase mean) in 7 of 7 hormone-exposed cells, 20 replicates; composed functions identical |
| Stage 3 experiment selection and U8 rerank | v0.4.0, v0.5.1 | One prospective arm frozen (E2 dropout); 112 candidate fifth arms evaluated |
| Identifiability-driven design | v0.6.0 | No single perturbation de-aliases the model |
| RNA-endpoint concordance | v0.5.1 | 27 RNA-observable nodes: 0 concordant, 0 discordant, 1 circular, 2 no response, rest mixed or not scored |
| scRNA node-support audit | v0.4.0 | 12 compartment-units pass QC; one alias class rule-challenged |
| Perturbation cascades | v0.5.1, v0.6.0 | Progestin withdrawal response order; two-seed rank Spearman 0.961 |

## 6. ENDO-TWIN mainline (new, `endotwin-v0.1.0`)

| | |
|---|---|
| Nodes | 19 (6 experimental inputs, 10 intracellular or interface nodes, 3 functional outputs) |
| Dependencies | 23 (20 activating, 3 inhibitory); 2 cross the epithelial-stromal interface |
| Distinct Boolean functions | 11; 3 alias classes (the inherited 7-member progesterone class, cAMP/PKA, IL-1beta/IL-1 signalling) |
| Absorbed or never-binding dependencies | 1 (`S_PKA -> S_BMP2`) |
| Readout-inert nodes | 1 (`IN_XAV939`, declared and read by no rule) |
| Evidence classes of the 23 default dependencies | 12 literature-supported (of which 4 topic-level only, 1 contested, 1 route-unresolved, 1 species transfer), 3 ADOC-supported, 5 experimental definitions, 3 simplifying assumptions |
| Rule-variant families | 3 (Q1 BMP, Q2 paracrine, INF inflammation); 7 variants; 12 scenarios |
| Protocols | 9 conditions, 6 matched comparisons, 2 interventions |
| Exact predictions | every condition x scenario fixed point; MaBoSS reaches all 312 phase fixed points (max deviation 0.002) |
| Rate sensitivity | 30 random rate sets: 720 of 720 steady-state directions unchanged |
| HAND2 relay example | area between curves 1.005 +/- 0.016 (10 of 10 replicates positive); identical end-of-phase values; delay present in 20 of 20 random-rate samples |

## 7. Inherited limitations and what ENDO-TWIN did with them

| Limitation in the prototype | Status in ENDO-TWIN |
|---|---|
| No quantitative calibration | **Kept as a research question.** Not addressed by migration; the WP1 data are required. No rate or magnitude is fitted |
| No independent prospective biological validation | **Kept; addressed by design.** A prediction-freezing workflow (`src/endotwin/predictions.py`) implements the WP2/WP4 separation; no prediction is frozen yet |
| Equivalent or redundant Boolean functions | **Partly addressed.** Pure marker aliases (PRL, IGFBP-1, PAEP) were merged into their functional outputs. The progesterone alias class (7 nodes) remains: one progestin input drives every PGR-dependent node. BMP receptor inhibition now separates SMAD activity from it |
| Dependencies that never influence outputs | Reduced from 20 of 89 to 1 of 23 |
| Inputs that affect nothing downstream | `IN_HCG` and `IN_EMBRYO_CONDITIONED_SIGNAL` left with the adhesion module. **`IN_XAV939` kept unread** on purpose: no evidence says which ADOC compartment a tankyrase inhibitor reaches (The prototype refused this wiring, U4b) |
| BMP2 expression conflated with pathway activity | **Addressed.** `S_BMP2` (ligand expression) and `S_BMP_SMAD` (receptor/SMAD1/5/8 activity, read as pSMAD1/5/8) are separate, with a receptor-inhibitor input. This is exactly the determinant the prototype was waiting for (`WAIT_FOR_EXPERIMENT`, `docs/v05_u4b_candidate_node_closure.md` section 3.1) |
| Uncertain compartment attribution of measurements | **Kept and carried into the observation map** (`endotwin/config/observation_map.tsv`): IGFBP-1 compartment-ambiguous, PAEP outlet unverified |
| Regulatory assumptions that remain hypotheses | **Made explicit.** Each dependency has an evidence class; Q1, Q2 and inflammation alternatives are executable variants |
| Restricted mechanistic identifiability | **Kept, and quantified for the new questions.** The discrimination table names which perturbation and readout separate which hypotheses |
| Simulated time not equal to experimental time | **Kept.** Phases run to their fixed point; no physical time mapping is made |
| Weak per-edge evidence for the IHH-NR2F2-BMP2 backbone | **Newly visible.** Where full-text graded, those edges are `not_demonstrated` (citations inherited from a topic-level evidence record) |
| Typed-in interface relay priors | Left with the adhesion module |
