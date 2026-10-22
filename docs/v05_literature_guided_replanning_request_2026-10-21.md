# DT_ADOC — READ-ONLY planning request: literature-guided MaBoSS rule refinement

**Date:** 2026-10-21  
**Audience:** an AI coding assistant running **locally** at the DT_ADOC repository root.  
**Task type:** independent evidence reconciliation, structural diagnosis, and **an implementation plan for future owner approval**.  
**This is not authorization to execute the plan.**

## A. Mission

Design the **smallest defensible, staged, testable** improvement programme for the **maternal epithelial/stromal MaBoSS model of embryo contact/stable adhesion**. We want to remove artificial hormone-following Boolean aliases and distinguish non-hormonal adhesion mechanisms, while not manufacturing dynamics, gates, phenotypes or rates from literature that measured only markers.

Do not interpret this handoff as a direction to adopt every candidate. Resolve the competing recommendations using two independent axes:

1. **Endpoint/structural effect:** does this candidate yield a distinct, unabsorbed route to a specified observable (especially initial epithelial attachment vs stable whole-maternal adhesion)?
2. **Biological support:** is the signed interaction supported in the relevant **human tissue, cell compartment, molecular layer, developmental stage and perturbation**?

Assess a third axis separately: **identifiability from existing and frozen prospective ADOC measurements**. A correct mechanism may still be unidentifiable, and vice versa.

**Expected product:** one decision-ready, sequenced draft plan with explicit unblock conditions, not new MaBoSS code.

## B. Authority / safety boundaries — read before any work

- Read `AGENTS.md` and applicable `.codex/harness/` contracts, the repo's current review gates, and **`docs/v05_pause_decision_2026-09-30.md`**, before using or writing artifacts.
- The 2026-09-30 **owner-endorsed biological-topology pause pending `dropout_e2` remains in force**, unless a newer explicit owner decision has superseded it. This request authorizes **planning/document review only**, not a new executable scoping increment. The pause enumerates three resume triggers: `dropout_e2` data, a funded cell-associated assay, or repair of the absorbed redundant-adhesion structure first. Verify each trigger's present status before declaring anything unblocked.
- **No edits** to `network.bnd`, nodes/edges, MaBoSS logic or transition rates, initial-state distributions, condition encodings, endpoints, observation maps, protocols, calibration, experiment allocation/frozen pre-run documentation, model versions, benchmarks or canonical evidence ledgers during this pass. Do not run calibration or change frozen claims.
- **Do not create a git commit, push, branch, or merge.** Do not overwrite anything under `data/` or publish private patient/sample-level source information. Source PDFs stay under gitignored `context/literature/pdfs/` and must not be committed. The 147-paper **Markdown screen** is not a substitute for original PDFs. Do not upload private project data externally.
- By default, keep your working tree unchanged. You **may draft a new planning document** only if this is permitted by local repository governance; if any rule objects, provide the plan in the response or an ignored working output without modifying tracked files. Stop and report if existing worktree changes or review hooks create conflicts.
- No model change is justified merely because it improves a switch curve, increases graph size, fits old data or gives a desired clinical effect. No physical time conversion from MaBoSS `duration_units=relative_only` or identically encoded day-3/day-6 conditions.

## C. Inputs: use these exact repository-relative paths

**New secondary research artifacts (NOT canonical evidence):**

- `context/literature/reviews/adoc_2026-10-21_147_paper_screen.md` — 147-paper tiered navigation; **42 focused** source checks, **105** index/abstract/target screens. This is one bundle, not an independent additional 147 citations beyond September's 163-PDF Sofia corpus.
- `context/literature/reviews/adoc_2026-10-21_mechanistic_rule_dossier.md` — reconciled 2026-10-21 biological hypotheses; full 12-theme expanded synthesis plus **v3 figure checklist, DKK1 contradictions, Li S2 28-hit annex and v3→new mapping**.

**Local source of truth and existing decision records:**

- `models/superset/adoc-literature-superset-v0.6.0/network.bnd` (the previously reviewed snapshot has blob SHA `ee40f2a4e98f74a461dc308bf83323785eb45bb4`; verify local HEAD/version), companion node dictionary and actual current model selection.
- `docs/v05_pause_decision_2026-09-30.md`, `docs/deferred_topology_register.tsv` (**especially TI-03, TI-04, TI-06**), `docs/v05_mechanistic_integration_plan.md`, `docs/v05_u3_ac01_no_derivable_rule.md`, `docs/v05_u4_gp130_axis.md`, `docs/v05_u5_structural_audit.md`, `docs/v05_u6b_muc1_reconciliation.md`, `docs/v05_u8_stage3_rerank.md`, `docs/v052_paep_hand2_cleanup.md`.
- `docs/curation_increment_01_xav939.md`, `docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md`, `docs/v05_u2_gate3a_blocked.md`, `docs/identifiability_experiment_design.md`, and the frozen `dropout_e2` allocation/assay notes (READ ONLY).
- `context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md` (separate Sofia corpus); `context/literature/knowledge-base.yaml`, `references.tsv`, `active_evidence_manifest.tsv`, `candidate-nodes.tsv`, `candidate-edges.tsv`, `evidence-gaps.tsv`, `source-provenance.tsv`, and `context/evidence-register.tsv`.
- `docs/evidence_schema.md` and any canonical assertion relation tables; do **not** create parallel bibliography/evidence ledgers.
- Current `config/` (nodes, interventions, protocols, measured observables), `src/dt_adoc/` structural and model-generation utilities, relevant tests and available data-validation summaries; use existing code/contracts rather than making a parallel Boolean auditor.

**Primary source availability:** Check `context/literature/pdfs/`, its manifests, and any local transfer directory. `DT_ADOC_literature_bundle_2026-10-21.pdf` is a compressed convenience bundle (72–100 dpi figures), not a substitute for figure-level source PDFs. Check originals for Retis-Resendiz 2024, Thathiah 2004, Paule 2015 and the core DKK1/WNT/Cloke/Kagawa studies. Li 2026 **`mmc2.xlsx`** is an *additional* workbook; locate it locally if needed, do not pretend its 28 hits are quantitative evidence. Heng 2010 (DOI `10.1210/en.2010-0326`) may need its full PDF to resolve a **specific** stromal PC6→mature BMP2 mechanism, but is **not required to prepare the plan**. Request any truly missing full text by exact DOI and figure only when necessary.

## D. Required work, in order

### 1. Preflight and delta from established audits

Record `git status --short`, current model/version/commit, input document hashes and which existing curation/structural audits already cover each proposal. Deduplicate the 147-paper bundle against the earlier 163-paper audit by DOI/title; **do not claim 310 distinct papers**. Identify factual corrections in the handoff and report them with primary figure/method citations. Explicitly flag where a new paper provides no new experimental condition relative to an existing experiment.

### 2. Structural baseline **before proposing new edges**

Reproduce or verify the repo's previous **fixed-rule Boolean** identities and structural results, including:

- `E_SECRETORY_STATE = IN_E2 ∧ E_PGR`, and `E_PAEP`, `E_HBEGF`, `E_PC6`, `E_SPP1_EXPR`, `E_MUC1_SLEX` currently share/descend from that state.
- `E_RECEPTIVE_SURFACE`'s **hard** GP130/STAT3 and anti-barrier requirements; why current CD98/CD9, integrin and adhesion-route disjunctions may be absorbed. Previous observations: settled epithelial surface can reduce to `IN_E2 ∧ IN_PROGESTIN ∧ ¬E_KLF12_HIGH` when intermediate nodes are not clamped; check it in the active version and declared assumptions.
- Stromal cascade `E_IHH→S_NR2F2→S_BMP2→S_HAND2`; why composed steady-state rules collapse under common hormone inputs; distinguish this from finite-time **asynchronous** transients.
- `S_PRL = S_IGFBP1 = S_DECIDUALIZED` and what TI-01 already repaired in the stromal **output** without independently regulating markers.
- Endpoint-specific effects of **clamps and inputs**, not just a tidy drawn graph. Examine existing `docs/v05_u5_structural_audit.md` before recomputing any counts. Check separately the currently unused `IN_XAV939`, `IN_HCG`, and `IN_EMBRYO_CONDITIONED_SIGNAL` declarations; do not wire them in simply to eliminate an unused-input warning. Do not quote another model version's function count as current without verifying its condition set and exact rule family.

For every candidate explain: (i) does it change settled Boolean logic? (ii) does it affect temporal trajectories? (iii) does it affect **a measured phenotype** under any admissible experiment? (iv) is its effect solely from hand-set unresolved relay priors? (v) does it require changing a phenotype definition, a higher-impact decision needing separate permission?

### 3. Independently adjudicate the most decision-relevant biology

Two tracks; **do not assume implementing all nodes is desirable**.

**Track A — adhesion/endpoints and independent mechanisms**

1. **GP130/STAT3:** Marwood 2009 and Ak 2026 challenge compulsory `E_GP130_STAT3` as *the sole* route. Distinguish IL11 versus LIF molecular pSTAT3 effects from adhesion effects, pharmacological SC144 from complete knockout, epithelial-only shear-resisted adhesion from whole-maternal stable adhesion. Assess alternative hard-gate placements and rate/supportive variants jointly with downstream absorbed OR-routes; no automatic gate deletion.
2. **CDH1/CTNND1:** Ruan 2026 tests primary EEC surface CDH1 localization, embryo-side vs maternal antibody blockade/siRNA in trophoblast-like systems. Separate maternal **surface** CDH1, embryo-side availability, contact, CTNND1/trafficking and CDH1's role in epithelial integrity. Avoid equating `E_CDH1_APICAL = IN_EMBRYO_CONTACT` with data showing contact sufficiency.
3. **CD98/CD9, integrins, HB-EGF:** Domínguez 2010 hormonal CD98 surface induction and cell-line/mouse blastocyst functional assay; Lessey 2002 epithelial versus stromal HB-EGF; LIF/IL11 and αVβ3/β5, Paule 2012. A CD98 rewiring confined to current absorbed readers remains **endpoint-inert**. Read D2/D3 refusal and TI-03 unblock requirements before suggesting implementation.
4. **Glycans:** Ma 2023 FUT3/sLeX, Dong 2025 ST6GALNAC1/sTn–CD44/SIGLEC6, Yu 2018 ST3GAL3. These are not synonyms for `MUC1_SLEX`; separate glycan carrier and species/stage transfer. Compare with other apical surface/polarity evidence (Kakar-Bhanot 2019 Rab11a, Peng 2021 PAR3).
5. **MUC1:** Meseguer 2001 in vivo, Thathiah 2004 TNFα-driven **synthesis plus shedding**, ADAM17/MMP14 studies, Ak 2026 local surface changes. Preserve TI-06's explicit requirement for a **perturbationally established local embryo-contact clearance determinant**; TNFα-associated shedding in HES does not satisfy it.
6. **PC6 and persistence:** Heng 2011/2015, Paule 2012/2015 support distinct proteolytic products (DAG1/EBP50/integrins/PDGFA). Distinguish activity, cleavage/processing and substrate replacement/turnover. Do not make PDGFA an adhesion gate or assign turnover from paper collection times.

**Track B — stromal regulation and molecular readouts**

7. **PRL/IGFBP1:** Cloke 2008, Buzzio 2006, Tamura 2014, Kane 2010, Retis-Resendiz 2024 demonstrate different AR/FOXO1/TGFβ1/cAMP/MPA responses. Distinguish **PGR expression vs ligand-activated activity**, mRNA vs accumulated secreted protein, short 24-h immortalized-cell RNA vs sustained primary-cell secretion. Consider PKA–EPAC/Rap1/CEBPβ only as supported extensions. Respect TI-04's **data/identifiability unblock requirements**; never implement `PRL = PKA` or `IGFBP1 = PKA` forever ON.
8. **PROK1/DKK1/BMP2/WNT4:** Tulac 2003/06, Cloke 2008, Macdonald 2011, Li 2013; BMP2 co-induces WNT4 **and WNT antagonists**. Contrast native PROK1/DKK1 loss-of-function, exogenous DKK1 on JAr, and DKK1 forced overexpression; do not deduce one biphasic curve/threshold or universal sign. Liu 2010 exposes **JAr**, not natural stromal DKK1. Li 2026 LRP5/6 is a prediction, not measured paracrine mediation.
9. **TGFβ1 and developmental stages:** Kane 2008 distinguishes delayed SMAD4-dependent PGR downregulation from DKK **secreted-protein** downregulation persisting after SMAD4 knockdown. Do not conflate TGFB1/SMAD2/3 with BMP2/SMAD1/5/8, nor first-trimester invasion/PROS1-AXL outgrowth with initial adhesion. Heng 2010 stromal PC6/BMP2: request figure-level paper only if it would change an actual plan decision.
10. **Epithelial markers and environmental modifier:** Garcia-Alonso 2021, Kagawa 2022 and Ak 2026 allow XAV939 effects on epithelial marker expression, **not a demonstrated direct adhesion gate**. Respect RSPO1-withdrawal confounding; Kagawa Ext Data 8d is marker-only. Re-adjudicate human `E_PGR→E_IHH` with Hewitt 2022 vs human-cycle associations; no sign reversal from mouse-to-human extrapolation without context.

**Separate lower-priority annex:** Li 2026 `mmc2.xlsx` Round II 28 drug hits (10/7/11), supplier metadata vs mechanism, CCK-8 Round I vs 48-h outgrowth Round II, K2EDTA identity QC; rank as *screening hypotheses*, not new molecular rules or adhesion therapies. The full hit names and caveats are in dossier §8. If the original workbook is available, make a **28-row screening annex** (donor, compound, CAS, vendor target versus observed effect, stage, source panel, decision); **do not** invent efficacy estimates or use drug hits to change MaBoSS rules.

### 4. Build, but DO NOT implement, candidate rule families

For each viable candidate, provide **at least two alternatives**: e.g. minimal context-dependent upstream change versus a more explicit expression/activity/surface/turnover split, and explain if a rate-based modifier is more defensible than a hard Boolean gate. Also include the **null model** (no change). Specify all proposed names as provisional.

Before choosing a plan unit, require a **traceability and identifiability matrix** with columns:

`increment_id | model_version/rule_path | problem_and_original_logic | experiment+panel | system/compartment/species | intervention/comparator | molecular_layer | supported_sign | contrary_evidence | candidate_rules_or_rates | endpoints_read | Boolean_alias_or_absorption_effect | transient_effect | ADOC_measured_observable | prospective_data_needed | exact_pause_and_TI_gate | uncertainty | falsifier | proposed_unit_size | action(status)`.

The status vocabulary should distinguish **already correct**, **documentation/evidence correction only**, **candidate model after owner authorization**, **blocked on evidence**, **blocked on ADOC observability**, **future embryo/outgrowth**, and **rejected**. Never collapse “scientifically plausible” into “authorized executable.”

### 5. Produce a minimal staged **implementation plan for later approval**

Deliver ONE ordered proposal, **maximum three near-term candidate implementation units** (everything else deferred/annex). A good default *starting hypothesis* is:

- **Unit 0 — read-only structural & source checks**: dedup, exact Boolean reduction, actual endpoint readers, version/metadata, missing source/control checks; no simulations/reanalysis if already documented and sufficient.
- **Unit 1 — endpoint/route architecture**: propose epithelial-only vs whole-maternal endpoints and assess the GP130 hard gate together with absorbed adhesion-route redundancy, before any CD98/CD9 de-aliasing. Could be a *planning/measurement blocker* rather than executable unit if pause still bars it.
- **Unit 2 — a single falsifiable adhesion route** (e.g. CDH1/CTNND1 *or* glycan route) selected on source specificity, non-absorption and experimental observability, **not both automatically**.
- **Unit 3 — independent stromal readout regulation** (PRL vs IGFBP1/PGR), only if `dropout_e2` or a different valid witness meets TI-04's stated measurement conditions. DKK1/WNT4/PC6 complex modules may rank above Unit 3 **only if** they improve an observable and pass the same gates; otherwise catalog/defer.

These are **candidate priorities to challenge, not a preselected implementation agenda**. For each selected unit specify: exact intended test files, mutation boundary, whether a new version is required, deterministic derivation script/reused functions, input conditions, predicted qualitative falsifier (and negative controls), structural equivalence test, MaBoSS transient tests (relative time only), held-out measurement strategy, and independent scientific reviewer gate. State what will remain impossible to infer without more experimental arms.

Do **not** run candidate simulations to choose the preferred biological story in this stage. If local governance would permit only an evaluation-only unit, return that rather than proposing immediate code edits. Never bundle multiple disjoint biological changes in one comparison that makes attribution impossible.

### 6. Check prior blocked decisions, do not overwrite them

Specifically cross-check `TI-03`, `TI-04`, `TI-06`, the D2/D3 refusal and the precise September pause resume conditions. If new literature *strengthens evidence* without satisfying an explicit **observation/causal-determinant** unblock, the status remains **deferred**. The agent must state this clearly in the plan. For all candidate rules involving hormones, separate **P4, MPA, RU486, E2, cAMP and XAV939** and the actual withdrawal schedules. Distinguish endogenous versus exogenous hormone and receptor expression versus activity.

## E. Required deliverables / stop point

**Main deliverable:** `DRAFT IMPLEMENTATION PLAN — NOT AUTHORIZED`, with:

1. **Repository current-state audit** (model hash, HEAD, working tree, applicable governance), plus documents and PDFs found/missing.
2. **Source crosswalk** (new vs already in the 163-PDF review/canonical ledgers; version-stable IDs; no fabricated new count), and a short list of corrected factual claims from the supplied three documents.
3. **Mechanism/edge/rule decision table** with literal exact upstream rules and outcome of Boolean simplification; distinguish matched biology from endpoint influence.
4. **Ranked, staged plan** of at most 3 near-term future implementation units, showing each prerequisite and a definite **GO / NO GO / WAIT** rationale against the topology pause and all TI item gates. Include zero-change/document-only option explicitly.
5. **Validation/falsification matrix:** intended code paths/tests/conditions, measurable outputs and negative controls, model/version provenance and a conservative test of whether route independence actually increased rather than a switch simply slowing down.
6. **Scientific reviewer challenge:** at least one independent `systems_biology_reviewer` or equivalent critique of the proposed plan (if available), including the strongest argument **against** each candidate unit. Document absent reviewer if unavailable; do not invent a PASS.
7. **Precise requests for missing data/papers** only where their absence would change an actual decision. Li S2 effects and Heng 2010 full text are optional for many branches. No generalized “need more literature.”
8. **Change log:** list any touched files. Default expected changes are **none**. If creating an authorized planning-only draft file, use `docs/v05_literature_guided_implementation_plan_DRAFT.md`, and state that it remains **unapproved and non-executable**. Never modify implementation tracking ledgers or canonical evidence tables without further user authorization.

**Stop after the plan and ask the owner for approval** before opening a new modeling/scoping unit, changing any executable rule, or modifying protected documents. If the evidence cannot select among rule alternatives, the correct answer is *retain uncertainty and propose discriminating measurements*.

## F. Quality checks before responding

- All input/output paths actually exist at local HEAD or are explicitly labeled missing.
- No original paper was silently treated as a validated edge merely because a review or automated screen lists it.
- New P4-withdrawal claims do **not** cite Ak 2026 as an uninterrupted P4-free blastoid assay (IVC-1 re-exposes to P4).
- No MARWOOD/LI/KAGAWA result is misassigned between maternal/embryonic compartments or between marker vs adhesion vs outgrowth endpoints.
- No false claim that the user supplied `mmc2.xlsx` *in the current three Markdown files*.
- No numerically invented MaBoSS transition rates or forced clinical outcomes.
- `git status` / `git diff` confirm no unintended edits; citations link actual panels and local evidence paths.

**Remember: You have more complete local data. You must correct mistaken premises in these notes and refuse low-evidence topology even if the text sounds confident.**
