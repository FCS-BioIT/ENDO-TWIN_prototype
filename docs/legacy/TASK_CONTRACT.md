# DT_ADOC Phase 1D Task Contract

## Objective

Reach the Phase 1D milestone by adding a new, versioned literature-superset
model family under `models/superset/adoc-literature-superset-v0.3.0/` without
overwriting `adoc-core-v0.1.0` or `adoc-literature-v0.2.0`.

The concrete goal is to create a complete, provenance-traceable catalog of
baseline plus literature candidate nodes and edges, classify executable versus
non-executable biology explicitly, define modular model slices and uncertain
rule alternatives, generate a bounded executable model family for structural and
module-activity validation, produce a drug-target catalog and screening-ensemble
definition, and update the project ledgers from inspected evidence.

## Phase

implementation

## Engineering Mode

robust

## Scope And Ownership

In scope:

- `models/superset/adoc-literature-superset-v0.3.0/**`
- `src/dt_adoc/model/**`
- `src/dt_adoc/simulation/**`
- `src/dt_adoc/perturbations/**`
- `src/dt_adoc/reporting/**` only if needed for bounded superset artifacts
- `config/perturbations.yaml` only if the new superset catalog requires a
  bounded repository-level registration
- focused tests under `tests/`
- bounded derived artifacts under `output/smoke/`
- project-control ledgers:
  `IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_STATUS.md`,
  `REQUIREMENTS_COVERAGE.tsv`

Explicit exclusions:

- any edit under `data/`
- overwriting or renaming `models/baseline/adoc-core-v0.1.0/`
- overwriting or renaming `models/extended/adoc-literature-v0.2.0/`
- broad perturbation screening across an unrestricted Cartesian product
- candidate ranking beyond `structural_only`
- fabricated causal edges, thresholds, rates, or source mappings
- any claim of validated contraceptive efficacy or clinically predictive output
- automatic commit/push or destructive Git operations

Editing ownership:

- parent: orchestration, contract maintenance, implementation integration,
  validation, ledgers, final response
- `repository_explorer`: read-only mapping of current catalogs and generation
  paths
- `data_steward`: read-only audit of candidate tables, provenance, identifiers,
  and source-facing classification consistency
- `maboss_modeler`: bounded superset-family implementation and structural tests
- `analysis_worker`: bounded module-activity checks, ensemble-definition checks,
  target-screening readiness outputs
- `systems_biology_reviewer`: independent read-only falsification review after
  parent validation

## Source Evidence

Primary inspected artifacts for this phase:

- `AGENTS.md`
- `TASK_CONTRACT.md`
- `.codex/config.toml`
- `.codex/harness/task-contract.md`
- `.codex/harness/handoff-format.md`
- `.codex/harness/routing-and-review-gates.md`
- `.codex/harness/scientific-review-checklist.md`
- `.codex/harness/validation-levels.md`
- `.codex/harness/skills.toml`
- `docs/adoc_dt_implementation_spec.md`
- `IMPLEMENTATION_PLAN.md`
- `IMPLEMENTATION_STATUS.md`
- `REQUIREMENTS_COVERAGE.tsv`
- `context/evidence-register.tsv`
- `context/literature/candidate-nodes.tsv`
- `context/literature/candidate-edges.tsv`
- `context/literature/mechanisms.tsv`
- `models/baseline/adoc-core-v0.1.0/`
- `models/extended/adoc-literature-v0.2.0/`
- current model/runtime/test code under `src/dt_adoc/` and `tests/`
- repository-local skills:
  `maboss-digital-twin`, `adoc-data-audit`, `adoc-result-validator`

Known environment limits:

- the large RDS remains source-only and unverified for structure without
  R/Seurat; do not materialize it for this phase
- standalone `MaBoSS` binary is not installed on `PATH`
- `git-lfs` is not installed; large immutable source files remain local and must
  not be forced into Git-based workflows
- currently open subagent capacity may be constrained by older sessions; if a
  required read-only agent cannot complete, continue in the parent and record
  the missing handoff explicitly

## Scientific Contract

- Biological question:
  can the repository represent the full evidence-backed maternal literature
  superset as an auditable modular model family while keeping unsupported or
  spatially dependent biology explicit rather than silently executable?
- Independent unit:
  catalog rows, executable model artifacts, structural tests, bounded module
  activation checks, and screening-architecture manifests
- Baseline model and versions:
  `adoc-core-v0.1.0`, `adoc-literature-v0.2.0`, and new
  `adoc-literature-superset-v0.3.0`
- Phenotype/output definition:
  no new clinical phenotype claims; keep mechanistic outputs explicit and
  candidate ranking `structural_only`
- Personalization target:
  none in this phase
- Validation split:
  no new fitting on source data; bounded module-activity simulations and
  structural validation only
- Comparator:
  minimal core, current literature parity, module-expanded slices, and full
  executable superset where causal specification supports execution
- Claim ceiling:
  provisional catalog and executable-architecture milestone only; not a
  calibrated, patient-specific, or biologically validated screening engine

## Relevant Skills

- `maboss-digital-twin`
- `adoc-data-audit`
- `adoc-result-validator`

## Invariants

- keep every file under `data/` immutable
- include every candidate node and candidate edge in the superset catalogs
- do not invent new biological edges solely to connect isolated candidates
- distinguish executable, uncertain, context-dependent, spatial-only, and
  insufficient-mechanism biology explicitly
- keep embryo, immune, endothelial, and spatially dependent biology external or
  future-mapped unless the current evidence supports a bounded Boolean rule
- do not silently choose one uncertain interpretation when multiple explicitly
  requested alternatives are required
- do not let module selection duplicate nodes across overlapping mechanisms
- keep baseline and current literature model artifacts unchanged
- keep candidate ranking and screening interpretation labeled `structural_only`
- do not claim safety, viability, inflammation, senescence, DNA-damage, or
  washout-recovery conclusions as mechanistic unless the executable model truly
  implements them

## Acceptance Criteria

- `models/superset/adoc-literature-superset-v0.3.0/` exists with the required
  deliverables:
  `complete_nodes.tsv`, `complete_edges.tsv`, `modules.tsv`,
  `rule_variants.tsv`, `interface_contract.tsv`, `drug_target_catalog.tsv`,
  `executable_model_manifest.tsv`, `module_activity_report.tsv`,
  `ensemble_definition.tsv`, `unresolved_mechanisms.tsv`,
  `literature_superset_network.mmd`, and `executable_modules_network.mmd`
- every candidate node from `context/literature/candidate-nodes.tsv` is present
  in `complete_nodes.tsv`
- every candidate edge from `context/literature/candidate-edges.tsv` is present
  in `complete_edges.tsv`
- every node is assigned the required classifications:
  compartment, cell type, class, evidence level, druggability, execution
  status, uncertainty status, spatial-dependence status, default module, and
  provenance identifiers
- every edge is assigned the required classifications:
  sign, directness, compartment, context, evidence, default enabled, variant,
  spatial requirement, uncertainty note, and provenance
- the superset family records a minimal core model, current literature parity
  model, module-expanded models, and a full executable superset where possible
- model generation is deterministic and leaves baseline/literature models
  unchanged
- module enable/disable behavior is testable, and each executable module is
  flagged in `module_activity_report.tsv` as functionally active, contextually
  inactive, structurally disconnected, unparameterized, or spatially blocked
- every drug perturbation entry references a valid catalog node
- screening-ensemble pruning rules are explicit and bounded
- final manifests and outputs stay within the structural-only claim ceiling

## Validation Commands

Preflight:

- `pwd`
- `git status --short`
- `git diff --stat`
- `pixi run harness-check`

Focused superset implementation and tests:

- focused superset unit and integration tests to be added in this phase
- `pixi run compile-models`
- `pixi run validate-models`

Bounded repository gates:

- `pixi run lint`
- `pixi run format-check`
- `pixi run test`

Artifact validation:

- parent inspection of generated superset catalogs, executable manifests,
  module-activity report, and ensemble definition
- `adoc-result-validator` manifest validation where a bounded superset run
  manifest is emitted

Independent review:

- `systems_biology_reviewer` handoff after implementation and parent validation,
  if agent capacity permits
