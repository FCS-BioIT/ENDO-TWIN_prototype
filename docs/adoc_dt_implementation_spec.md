# Codex task: implement the DT_ADOC MaBoSS repository

You are the parent Codex agent working at the root of the DT_ADOC repository. Execute the implementation; do not return only a plan.

## Objective

Build a reproducible Pixi/Python implementation of the ADOC stochastic Boolean digital twin using MaBoSS/PyMaBoSS. Reimplement the reusable ideas from PROFILE and PROFILE_v2 locally, while using MaBoSS itself as the simulation engine.

The implementation must:

1. reproduce the basal-to-hormone-conditioned ADOC transition;
2. represent epithelial and stromal compartments plus extracellular crosstalk;
3. support sequential hormone, mifepristone, anti-SPP1, and washout protocols;
4. support transparent donor contextualization inspired by PROFILE;
5. support graded single and double perturbations inspired by PROFILE_v2;
6. rank non-hormonal anti-adhesion hypotheses while penalizing toxicity, barrier damage, decidual failure, inflammation, senescence, and irreversibility;
7. preserve complete evidence, data-lineage, model, and run provenance;
8. remain explicit that all outputs are conditional model predictions, not clinical probabilities or treatment recommendations.

## Mandatory first steps

Before editing:

1. Read, in this order:
   - `AGENTS.md`
   - `codex/harness/data-lineage-contract.md`
   - `codex/harness/scientific-review-checklist.md`
   - `context/project-context.md`
   - `docs/roadmap.md`
   - `docs/digital-twin-architecture.md`
   - `docs/personalization-strategy.md`
   - `context/references/adoc-maboss-model-specification.user-provided.md`
   - `context/evidence-register.tsv`
   - `context/node-candidates.tsv`
   - `context/phase1-readouts.tsv`

2. Read and apply the repository-local skills:
   - `maboss-digital-twin`
   - `adoc-data-audit`
   - `adoc-result-validator`

3. Determine whether the current checkout is:
   - the full repository with immutable sources under `data/`; or
   - the compact ChatGPT review bundle, identified by `SECTION_STATUS.tsv` and missing large source files.

If this is the review bundle, proceed with implementation, synthetic fixtures, the included portable protein-readout tables, and structural/smoke validation. Do not fabricate missing RDS, papers, annotations, or real-data results. Record all blocked real-data gates in `IMPLEMENTATION_STATUS.md`.

4. Write the task contract before implementation. Use robust engineering mode. The task contract must state that this task produces a provisional executable research model and smoke results, not canonical biological or clinical claims.

## Agent and skill routing

Respect `max_threads = 4` and `max_depth = 1`. The parent is the sole orchestrator. Subagents must not delegate.

Use the smallest useful agent set:

1. Skip `repository_explorer` unless the actual paths or execution path differ materially from the documented repository.
2. Use `maboss_modeler` as the primary bounded implementation agent for:
   - MaBoSS `.bnd` and `.cfg` artifacts;
   - the MaBoSS adapter and sequential protocol runner;
   - strict/soft node variants;
   - graded perturbation logic;
   - model and simulation manifests.
3. The parent owns package scaffolding, integration, documentation, tests, and final validation.
4. Use `systems_biology_reviewer` after implementation for an independent read-only audit of topology, rules, phenotype definitions, personalization, calibration boundaries, and claim limits.
5. Apply `adoc-result-validator` in the parent to smoke artifacts and manifests. Do not promote results to canonical or make biological claims in this task. A separate `result_validator` task is required before any later result enters a report as canonical.
6. Use `data_steward` only if an unaudited source is actually processed. Do not instantiate every configured role.

Every delegation must follow the global Agent Harness task contract and every subagent must return its handoff format.

## Upstream methods to inspect

Inspect these public repositories read-only, preferably in a temporary directory:

- PROFILE: `https://github.com/sysbio-curie/PROFILE`
- PROFILE_v2: `https://github.com/ArnauMontagud/PROFILE_v2`
- Method paper: `https://elifesciences.org/articles/72626`

You are authorized to fetch these public repositories for inspection. Do not add them as runtime dependencies or Git submodules.

For each repository:

- pin the exact tag or commit inspected;
- record the URL, revision, date, and license;
- inspect the tutorial/example execution path;
- document handling of missing genes, duplicate identifiers, zeros, clipping, scaling, initial probabilities, rate modifiers, strict variants, partial inhibition, combinations, and output scoring;
- identify cancer-specific, manuscript-specific, R, Perl, shell, and plotting assumptions that must not be copied;
- retain copyright and license notices for any small fixture or formula copied;
- create `references/upstream_versions.yaml` and `THIRD_PARTY_NOTICES.md`;
- create `docs/profile_local_reimplementation.md` describing exact deviations from PROFILE and PROFILE_v2.

If network access is unavailable, use the repository documentation already present, mark upstream parity as unverified, and do not invent behavior.

## Engineering principles

- Use Pixi for all dependencies and tasks.
- Use Python for the production implementation.
- Reuse MaBoSS/PyMaBoSS. Do not reimplement the stochastic Boolean engine.
- Verify the currently supported MaBoSS/PyMaBoSS package and API before pinning versions. Adjust the Python version only when required for compatibility.
- Do not install dependencies system-wide.
- Do not commit, push, rewrite Git history, or perform destructive Git operations.
- Never edit, rename, convert, or overwrite source files under `data/`.
- Keep derived artifacts outside `data/`.
- Keep smoke and full outputs separate.
- Fail loudly when MaBoSS is unavailable; do not silently substitute a fake simulator.
- Do not assign physical time units to MaBoSS time without calibration.
- Do not invent topology, signs, logical operators, thresholds, rates, or mappings.

## Required repository structure

Preserve existing files and add a maintainable package approximately as follows. Adapt names only when an existing convention clearly requires it.

```text
src/dt_adoc/
  __init__.py
  cli.py
  maboss_adapter.py
  model/
    catalog.py
    compile.py
    validate.py
    provenance.py
  protocols/
    schema.py
    runner.py
    conditions.py
  personalization/
    reference.py
    strict_nv.py
    soft_nv.py
    mapping.py
  perturbations/
    target_engagement.py
    single.py
    combinations.py
    synergy.py
  calibration/
    objectives.py
    search.py
    adhesion_likelihood.py
  scoring/
    phenotypes.py
    safety.py
    candidates.py
  simulation/
    runner.py
    stability.py
    sensitivity.py
    manifests.py
  reporting/
    tables.py
    figures.py
    report.py

config/
  protocols.yaml
  perturbations.yaml
  personalization.yaml
  calibration.yaml
  phenotype_definitions.yaml
  candidate_score.yaml

models/specs/
  nodes.tsv
  edges.tsv
  rules.yaml
  uncertain_rule_variants.yaml
  phenotypes.yaml
  parameter_scenarios.yaml

models/baseline/adoc-core-v0.1.0/
  network.bnd
  baseline.cfg
  conditions/
    basal.cfg
    e2_priming.cfg
    hormone_treated.cfg
    hormone_treated_mifepristone.cfg
    hormone_treated_anti_spp1.cfg
    washout.cfg
  node_dictionary.tsv
  edge_evidence.tsv
  phenotype_contract.tsv
  provenance.toml

models/extended/adoc-extended-v0.1.0/
  ...

references/fixtures/profile/
references/fixtures/profile_v2/

tests/
  unit/
  integration/
  regression_profile/
  regression_profile_v2/
  biological_constraints/
  fixtures/

output/
  smoke/<run-id>/
  full/<run-id>/
```

Do not create derived `nodes.tsv`, `edges.tsv`, or similar files under immutable `data/`. The source of truth belongs under `models/specs/` and compiled model-version directories.

## Model source of truth and provenance

Use the node inventory, modules, example rules, and phenotype definitions in `context/references/adoc-maboss-model-specification.user-provided.md` as an implementation specification, not as unquestionable evidence.

Implement:

1. `adoc_core`: a runnable coupled epithelial-stromal-extracellular model containing the evidence-backed core needed for hormone response, decidualization, maternal adhesion competence, barrier state, viability, inflammation, and reversibility.
2. `adoc_extended`: the core plus ECM/remodeling, metabolism, redox, senescence, angiogenic support, and optional immune, endothelial, and embryo-interface modules.

Use prefixes:

- `E_`: epithelial
- `S_`: stromal
- `X_`: extracellular/intercompartmental
- `IN_`: experimental input
- `OUT_`: reported phenotype

The full evidence catalog may be large. The executable model must remain conservative:

- high-confidence mechanistic nodes and required readouts enter the core;
- uncertain or context-dependent rules receive explicit variant IDs;
- marker-only nodes must not gain outgoing causal edges without evidence;
- catalogued nodes lacking defensible rules remain non-executable candidates rather than receiving invented logic;
- untreated, hormone-treated, and perturbation conditions must use the same topology;
- a topology change creates a new baseline model version.

### Required node table fields

At minimum:

```text
node_id
label
compartment
entity_type
module
tier
state_0_meaning
state_1_meaning
measurement_proxies
measurable
perturbable
expected_hormone_direction
model_role
evidence_ids
confidence
notes
```

### Required edge table fields

At minimum:

```text
edge_id
source
target
sign
mechanism
logical_role
evidence_class
species
direct_or_inferred
citation_or_source
evidence_id
confidence
status
variant_id
notes
```

For every logical rule, document why AND, OR, and NOT are biologically appropriate. Mark all assumptions explicitly.

## Core biological modules

At minimum, implement evidence-traceable versions of:

1. Epithelial estrogen/progestin response: ESR/PGR, GATA2, SOX17, FOXA2, IHH, LIF-LIFR-IL6ST-STAT3, and XAV939/TNKS/AXIN/CTNNB1 handling.
2. Stromal decidualization: PGR and cAMP/PKA/CREB, CEBPB, FOXO1, IHH-PTCH-SMO-GLI-NR2F2-HAND2-BMP2-WNT4, IL11-JAK-STAT3, PRL, and IGFBP1.
3. Epithelial adhesion/glycocalyx: SPP1-integrins, CD98/CD9, ANXA2, apical CDH1, PODXL, MUC1 state variants, DAG1 and PCSK5/6, and selected interface factors supported by the evidence catalog.
4. Focal adhesion/cytoskeleton: FAK, SRC, RAC1/RHOA/ROCK and a compact actin-remodeling phenotype.
5. Barrier/polarity: TJP1, OCLN, selected claudins, epithelial polarity, and distinct mature, receptivity-remodeled, and damaged barrier outputs.
6. Safety: apoptosis, DNA damage, chronic inflammation, persistent senescence, epithelial viability, stromal viability, and recovery after washout.
7. Core metabolic support: glucose/glycolytic sufficiency, glutamine/glutamate/alpha-ketoglutarate support, lactate, oxygen/ROS, prostaglandin-cAMP signaling, and metabolic health outputs, only at the granularity supported by the model specification.

Do not collapse the published hormone protocol into one `HORMONES` node. E2, progestin, cAMP, and XAV939 must remain independently controllable.

Anti-SPP1 must inhibit free extracellular/luminal SPP1 activity, not directly switch off `SPP1` transcription.

## Required phenotypes

Define explicit Boolean expressions before simulation for at least:

```text
OUT_EPITHELIAL_RECEPTIVE
OUT_EPITHELIAL_SECRETORY
OUT_STROMAL_DECIDUALIZED
OUT_CROSSTALK_FUNCTIONAL
OUT_MATERNAL_ADHESION_COMPETENCE
OUT_STABLE_ADHESION
OUT_BARRIER_MATURE
OUT_BARRIER_REMODELED
OUT_BARRIER_DAMAGED
OUT_EPITHELIAL_VIABLE
OUT_STROMAL_VIABLE
OUT_CHRONIC_INFLAMMATION
OUT_PERSISTENT_SENESCENCE
OUT_DNA_DAMAGE
OUT_APOPTOSIS
OUT_METABOLIC_HEALTH
OUT_RECOVERY_AFTER_WASHOUT
```

Keep maternal adhesion competence separate from observed embryo adhesion. `OUT_STABLE_ADHESION` may require `IN_EMBRYO_PRESENT` and `IN_TROPHECTODERM_COMPETENT`; the initial pilot can validate the maternal state without claiming embryo-side validation.

## Sequential protocol runner

Implement phased simulations where the final distribution from one phase initializes the next. Support at least:

1. basal;
2. E2 priming;
3. E2 + progestin + cAMP + XAV939;
4. hormone-treated + mifepristone;
5. hormone-treated + anti-SPP1;
6. perturbation washout.

Store protocol definitions in YAML and validate them with a schema. Record phase order, relative duration, input changes, model/config hashes, and continuation method.

## Local PROFILE reimplementation

Implement transparent local equivalents of the reusable PROFILE concepts:

### Strict node variants

- Force a node ON or OFF only when strong constitutive evidence exists.
- A missing gene, scRNA dropout, blank value, or below-detection measurement is never sufficient for a clamp.
- Preserve the matched unmodified baseline.

### Soft node variants

Implement an explicit mapping from a normalized continuous score `p` to:

- initial ON probability;
- optional relative `rate_up` and `rate_down` modifiers.

The mapping must be configurable, monotonic, clipped, unit-tested, and uncertainty-aware. Use a configurable strength parameter such as `alpha`; do not hard-code the aggressive PROFILE scaling without ADOC calibration.

Do not estimate PROFILE-style unimodal/bimodal/zero-inflated reference distributions from only three ADOC donors. Design the interface to use a fixed external reference derived later from published ADOC scRNA-seq pseudobulks and/or a larger reference atlas.

Every donor mapping row must contain source, donor, condition, compartment, raw/QC/transformed value references, missingness state, reference, mapping function, threshold or probability, rate modifier if used, uncertainty, evidence role, and leakage-control status.

Donor personalization must not alter topology unless a separate, independently supported baseline model version is created.

## Local PROFILE_v2 reimplementation

Implement graded perturbations as target-engagement or affected-trajectory fractions from 0 to 1. Never call these fractions drug concentrations, doses, or occupancy unless a separate pharmacodynamic mapping exists.

Support:

- a configurable target-engagement grid;
- single-node inhibition/activation;
- pairwise perturbations;
- matched unperturbed controls;
- multiple seeds and trajectory counts;
- Bliss independence and HSA-style summaries with clearly defined effect direction;
- efficacy and safety effects calculated separately;
- target-engagement curves;
- deterministic output schemas and provenance.

Do not carry forward cancer-specific phenotype names, hard-coded targets, plotting limits, or shell/R orchestration from PROFILE_v2.

## Candidate score

Implement a configurable multi-objective score. It should reward reduction in `OUT_MATERNAL_ADHESION_COMPETENCE` and, when embryo inputs are present, `OUT_STABLE_ADHESION`, while penalizing:

- epithelial or stromal death;
- barrier damage;
- chronic inflammation;
- persistent senescence;
- DNA damage;
- loss of stromal decidualization beyond a configurable tolerance;
- failure to recover after washout;
- instability across seeds, trajectory counts, rule variants, or donor contexts.

Return both a scalar ranking and the full component vector. Produce a Pareto-front table so that the scalar weight choice is not hidden.

## Calibration and validation

Use `context/phase1-readouts.tsv` and the evidence assignments already documented.

Preferred split:

- construction: mechanistic literature plus the registered ADOC state programs;
- calibration: untreated versus hormone-treated qualitative molecular directions, PAEP/PRL/IGFBP1 behavior, and untreated versus hormone-treated adhesion;
- internal validation: mifepristone adhesion response, only if it was not used to construct or tune the perturbation behavior.

Implement:

- binomial likelihood or deviance for 0/12 untreated and 9/19 hormone-treated adhesion observations;
- held-out comparison to 1/8 mifepristone when valid;
- qualitative/ordinal penalties for molecular directions and time ordering;
- bounded parameter scenarios rather than unconstrained fitting of many rates;
- reproducible grid or bounded search configured in YAML;
- retention of an ensemble of acceptable parameter/rule variants when non-identifiability exists;
- explicit calibration-versus-validation labels in all outputs.

Do not optimize for exact reproduction of 0, 47%, or 12.5%. Do not assign physical time units. Do not use the same evidence for construction, calibration, and validation without documenting the leakage.

## Run manifests and outputs

Conform to `codex/skills/adoc-result-validator/references/run-manifest-contract.md`.

Every smoke or full run must create a repository-relative `run_manifest.json` recording:

- schema version, run ID, timestamp, command;
- software versions;
- model, config, rules, mapping, and input hashes;
- independent unit and cohort/split role;
- personalization method and uncertainty;
- protocol and perturbation;
- seeds, trajectories, relative time horizon, time tick, and threads;
- phenotype definitions;
- warnings and completed validation levels;
- every output path, kind, size, and SHA-256.

Generate under `output/smoke/<run-id>/`:

- raw MaBoSS outputs;
- phenotype probability tables;
- protocol-phase table;
- perturbation effects;
- seed/trajectory stability table;
- assumption-sensitivity table;
- candidate-score and Pareto tables;
- logs;
- validation report;
- concise Markdown or HTML report;
- figures for protocol state changes, target-engagement curves, efficacy-versus-safety, and uncertainty.

All smoke outputs must be labeled provisional.

## Tests

Add focused tests for:

1. node/edge/rule schema validation;
2. `.bnd` and `.cfg` generation/parsing;
3. a small known Boolean network using the real MaBoSS runtime;
4. strict node variants;
5. soft initial-probability mapping;
6. soft rate modifiers and clipping;
7. missing/blank/below-detection handling;
8. sequential continuation between phases;
9. target-engagement mixtures;
10. single and pair screens;
11. Bliss and HSA calculations on hand-computable fixtures;
12. manifest creation and existing manifest validator compatibility;
13. PROFILE and PROFILE_v2 parity on at least one small pinned upstream example, within stated stochastic tolerance;
14. biological constraints:
    - hormone treatment increases epithelial secretory/receptive probability;
    - hormone treatment increases stromal decidualization probability;
    - hormone treatment increases maternal adhesion competence;
    - PAEP/SPP1 and PRL/IGFBP1 outputs change in the registered directions;
    - ciliated-state probability decreases after hormone treatment when represented;
    - mifepristone reduces PGR-dependent outputs and adhesion competence;
    - anti-SPP1 reduces free extracellular SPP1 but not SPP1 transcription directly;
    - anti-SPP1 is not forced to switch stromal decidualization off;
    - broad FAK/SRC inhibition receives a safety penalty;
    - washout can recover a selective perturbation toward the receptive baseline;
15. repeated-seed and increased-trajectory stability checks;
16. uncertain-rule and rate-strength sensitivity checks.

Stochastic tests must use tolerances and confidence intervals, not exact floating-point equality.

## Pixi tasks

Update `pixi.toml` and `pixi.lock` with compatible, pinned dependencies and tasks similar to:

```text
harness-check
test
lint
format-check
compile-models
validate-models
profile-parity
smoke
validate-smoke
report-smoke
screen-mini
all-checks
chatgpt-results-bundle
```

Keep expensive full screening out of the default task. Before any full screen, estimate variants x perturbations x seeds x trajectories, runtime, memory, and output size.

## Documentation

Update or add:

- `README.md`: installation, tasks, scope, claim boundary, quick start;
- `docs/implementation.md`: architecture and package flow;
- `docs/profile_local_reimplementation.md`: upstream parity and deviations;
- `docs/model_building.md`: evidence-to-node/edge/rule process;
- `docs/calibration_and_validation.md`: split, objectives, uncertainty, and non-identifiability;
- `docs/perturbation_screening.md`: target engagement, synergy, safety, and interpretation;
- `IMPLEMENTATION_STATUS.md`: completed, provisional, blocked, and unverified gates.

Keep the existing scientific context and review policies intact unless a correction is clearly justified and documented.

## Validation sequence

Run the highest feasible gates in this order and record exact commands and return codes:

1. parse TOML, YAML, JSON, TSV, Python, `.bnd`, and `.cfg`;
2. run repository harness checks;
3. run unit tests;
4. run lint and format checks;
5. run the synthetic MaBoSS fixture;
6. run upstream PROFILE/PROFILE_v2 regression fixtures;
7. compile and validate `adoc_core` and `adoc_extended`;
8. run one bounded ADOC smoke protocol with small declared settings;
9. repeat seeds and increase trajectories for primary phenotype stability;
10. run a small uncertain-rule/rate sensitivity matrix;
11. validate `run_manifest.json` with the repository validator;
12. inspect generated tables, figures, logs, and warnings;
13. request independent `systems_biology_reviewer` review.

If full source data are absent, do not fail the entire implementation merely because the compact bundle intentionally excludes them. Mark source-integrity and real-data gates blocked, while still requiring all source-independent implementation and smoke gates to pass.

If MaBoSS itself cannot be installed or executed, do not fake success. Complete source-independent implementation, report the exact dependency failure, and leave simulation-dependent acceptance criteria unverified.

## Acceptance criteria

The task is complete only when all applicable criteria pass or are explicitly marked blocked with evidence:

- repository-local harness and skills are preserved and valid;
- source data under `data/` are unchanged;
- Pixi creates a reproducible environment;
- MaBoSS/PyMaBoSS version is pinned and reported;
- local PROFILE and PROFILE_v2 logic is implemented in Python with provenance and at least one regression fixture;
- `adoc_core` is executable and evidence traceable;
- `adoc_extended` is structurally valid, with uncertain modules clearly labeled;
- all condition files share one baseline topology;
- sequential protocols run correctly;
- strict/soft personalization and target-engagement screens are tested;
- smoke run manifests pass the repository validator;
- qualitative biological constraint tests pass or discrepancies are documented without force-fitting;
- Monte Carlo and assumption-sensitivity outputs exist for the smoke run;
- generated results are labeled provisional and respect the claim ceiling;
- independent systems-biology review has no unresolved critical finding, or the model remains explicitly provisional with the findings listed;
- `IMPLEMENTATION_STATUS.md` accurately states every unverified gate.

## Final response

Return a concise but complete handoff containing:

- status: pass, partial, or blocked;
- agents and skills actually used;
- major design decisions;
- changed files grouped by purpose;
- exact validation commands and return codes;
- generated artifacts and hashes;
- independent-review findings;
- unverified gates and blockers;
- the single next scientific or technical action with highest value.

Do not claim the ADOC digital twin is biologically validated, clinically predictive, or a proven contraceptive discovery system unless the corresponding independent evidence exists.
