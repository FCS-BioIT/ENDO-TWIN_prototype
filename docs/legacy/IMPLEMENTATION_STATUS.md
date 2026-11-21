# DT_ADOC Implementation Status

Updated: 2026-07-26

> **Historical record.** This file was last updated on 2026-07-26 and
> describes the project as it stood then (`adoc-literature-superset-v0.3.0`,
> Phase 1D). It is not the current status: the current executable increment is
> `adoc-literature-superset-v0.6.0`, and the authoritative current status is
> the "Where the project stands" table in [`README.md`](README.md). The findings
> below are kept as written.

## Current Overall

- Current task state: `Phase 1D literature-superset family implemented, bundle/runtime plumbing repaired, bounded engineering gates passed, milestone completion blocked by reviewed endpoint behavior`
- Formal milestone: `adoc-literature-superset-v0.3.0 exists as a versioned executable reference panel, but Phase 1D cannot be claimed complete as a screening-ready milestone`
- Repository mode: full repository with immutable sources present under `data/`
- Claim ceiling: provisional executable research model, structural-only target architecture, and bounded smoke/runtime-analysis artifacts only
- Data audit: `not required: no new source data introduced`
- This Phase 1D section supersedes the older Phase 1C-focused overview below where they differ.

## Phase 1D Summary

### Passed In This Pass

- The repository now contains a new versioned family at
  [`models/superset/adoc-literature-superset-v0.3.0/`](./models/superset/adoc-literature-superset-v0.3.0/)
  with the required superset deliverables:
  `complete_nodes.tsv`, `complete_edges.tsv`, `modules.tsv`,
  `rule_variants.tsv`, `interface_contract.tsv`, `drug_target_catalog.tsv`,
  `executable_model_manifest.tsv`, `module_activity_report.tsv`,
  `ensemble_definition.tsv`, `unresolved_mechanisms.tsv`,
  `literature_superset_network.mmd`, and
  `executable_modules_network.mmd`.
- The superset catalog retains all current literature candidates:
  `complete_nodes.tsv` contains `63` rows and `complete_edges.tsv` contains
  `143` rows; `58` nodes are executable, `4` remain catalog-only, and
  `1` remains external-only.
- Runtime integration now resolves the real superset family through
  [`src/dt_adoc/model/runtime.py`](./src/dt_adoc/model/runtime.py),
  [`src/dt_adoc/model/validate.py`](./src/dt_adoc/model/validate.py), and
  [`src/dt_adoc/protocols/conditions.py`](./src/dt_adoc/protocols/conditions.py),
  with maternal-only and embryo-challenge protocol separation preserved.
- Focused superset contract and runtime tests passed, and the post-fix bounded
  repository gates passed:
  `pixi run all-checks` returned `0` after the manifest and bundle fixes, with
  `97` repository tests passing.
- The Phase 1D bundle defect is repaired: the ChatGPT bundle selector now finds
  the latest smoke run even when `output/smoke/` is nested by model version,
  and `pixi run chatgpt-results-bundle-test` passed after adding a regression
  test for nested smoke roots.
- The source-independent CLI import boundary remains intact:
  `tests.test_cli_import_boundary` passed, confirming non-smoke CLI commands do
  not require MaBoSS runtime imports.
- The dedicated superset smoke completed and its manifest validated at
  [`output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke-v2/`](./output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke-v2/).
- The superset smoke manifest now records explicit stability metadata under
  `simulation.stability` with seeds `1,2,3` and `trajectory_count=500`, so the
  previously implicit `stability.tsv` audit trail is now structured in
  `run_manifest.json`.
- A live bundle was generated at
  [`output/reports/phase1d_chatgpt_bundle_v4.tar.gz`](./output/reports/phase1d_chatgpt_bundle_v4.tar.gz)
  on 2026-07-26, and parent inspection confirmed that **that specific archive**
  contained the updated ledgers plus the superset smoke root
  [`phase1d-superset-smoke-v3`](./output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke-v3/).

  This is a statement about one archive at one point in time, not a standing
  property of the bundler. By default the bundler ships whichever smoke run has
  the newest `run_manifest.json` across all model families, so any v0.2.0 or
  baseline run created later silently displaces the superset run. Newer v0.2.0
  runs on 2026-07-27 did exactly that, and a bundle built today ships
  `output/smoke/adoc-literature-v0.2.0/final-check/` instead. To reproduce a
  superset-pinned archive, select it explicitly:

  ```bash
  pixi run bash scripts/make_chatgpt_results_bundle.sh \
      --smoke-run output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke-v3
  ```

  Note that this run predates trajectory capture, so it carries no
  `*_nodes_probtraj.tsv`; the bundler warns when that is the case. Every
  bundle records the run it actually shipped in the `smoke_run` row of
  `SECTION_STATUS.tsv`, so this should never again need to be inferred.

### Still Blocked

- Phase 1D cannot be called complete now. The final
  `systems_biology_reviewer` handoff returned `fail`, with one `critical` and
  four `major` findings against milestone completion.
- **2026-07-28 update — the adverse endpoint behaviour below is a measurement
  artifact, not a model defect.** The adhesion endpoints are read roughly
  4000x before the network reaches its logical fixed point. Extending only the
  readout horizon (no model, rule or protocol change) moves
  `adhesion_challenge_hormone_treated` competence from `0.0002` to `0.820`,
  matching the analytic prediction `1 - (1 - 0.7)(1 - 0.4) = 0.82`, and every
  perturbation arm then moves in the biologically expected direction:
  mifepristone `0.000` (abolished), anti-SPP1 `0.400`, ER stress and ECM
  stiffness `0.575`, against a hormone-treated reference of `0.820`.
  Increasing the trajectory budget does not help — it tightens the interval
  around an unconverged value. See
  [`docs/endpoint_convergence_finding.md`](./docs/endpoint_convergence_finding.md)
  and the gates in
  `tests/biological_constraints/test_superset_perturbation_gates.py`.
  The `fail` verdict above rests on findings this diagnostic attributes to the
  horizon and should be re-run against converged outputs. The one genuine
  model defect confirmed is that `IN_ER_STRESS_EXCESS` and
  `IN_HIGH_ECM_STIFFNESS` are logically interchangeable. Nothing has been
  promoted on the strength of this diagnostic: the converged magnitudes are
  uncalibrated, and correcting the horizon would supersede the existing
  fitted values in `config/calibration.yaml`.

- The dedicated superset smoke still shows adverse endpoint behavior:
  `adhesion_challenge_hormone_treated_mifepristone` reports
  `OUT_MATERNAL_ADHESION_COMPETENCE = 0.0009718013508105582`, which is higher
  than the `HT` challenge value `0.0005`, while
  `adhesion_challenge_hormone_treated_anti_spp1` leaves competence unchanged at
  `0.0005`. This blocks endpoint-level screening interpretation.
- ER stress and high ECM stiffness remain numerically identical at the reported
  phenotype layer in the dedicated superset smoke. The reviewer concluded that
  the current executable mechanics abstraction is still too coarse for
  mechanism-specific falsification of those two challenges.
- The module-activity ledger is not promotable as-is for all wording:
  `analysis_worker` accepted the non-executable classifications for `MOD-08`,
  `MOD-10`, `MOD-11`, and `MOD-12`, but flagged `MOD-13` as over-broadly
  labeled `functionally_active`; only the bounded stiffness/ER-stress subset is
  active in the current executable abstraction.
- Assumption robustness remains blocked for the key Phase 1D additions. The
  bounded ensemble and sensitivity artifacts remain explicitly
  `structural_only`, and the reviewer concluded they do not support a screened,
  assumption-robust ensemble claim.
- The current smoke report still disclaims calibration/validation, and the fit
  to observed adhesion remains poor. There is no basis to promote the current
  outputs from structural execution to validated screening behavior.

## What Changed In This Pass

- Replaced the scaffold-only superset wiring with the real family generator in
  [`src/dt_adoc/model/runtime.py`](./src/dt_adoc/model/runtime.py) and
  [`src/dt_adoc/model/validate.py`](./src/dt_adoc/model/validate.py).
- Repaired superset protocol cloning and continuation wiring in
  [`src/dt_adoc/protocols/conditions.py`](./src/dt_adoc/protocols/conditions.py)
  so maternal perturbation protocols stay embryo-off and challenge protocols
  continue from the intended maternal states.
- Added the versioned generator and validator in
  [`src/dt_adoc/model/superset_family.py`](./src/dt_adoc/model/superset_family.py)
  and generated the complete `adoc-literature-superset-v0.3.0` family.
- Added focused contract/runtime tests in
  [`tests/unit/test_superset_model_contracts.py`](./tests/unit/test_superset_model_contracts.py)
  and
  [`tests/integration/test_superset_model_runtime.py`](./tests/integration/test_superset_model_runtime.py).
- Fixed repository validation integration so the superset family validates under
  `pixi run validate-models` and the full repository suite.
- Repaired the nested-smoke ChatGPT bundle selection bug in
  [`scripts/make_chatgpt_results_bundle.sh`](./scripts/make_chatgpt_results_bundle.sh)
  and added the regression test in
  [`tests/test_chatgpt_bundle.py`](./tests/test_chatgpt_bundle.py).
- Added structured stability metadata to run manifests via
  [`src/dt_adoc/simulation/manifests.py`](./src/dt_adoc/simulation/manifests.py),
  [`src/dt_adoc/simulation/runner.py`](./src/dt_adoc/simulation/runner.py), and
  [`tests/unit/test_manifests.py`](./tests/unit/test_manifests.py).

## July 26, 2026 Phase 1D Validation

| Command | Return Code | Result |
|---|---:|---|
| `pixi run python -B -m unittest tests.unit.test_superset_model_contracts tests.integration.test_superset_model_runtime -v` | `0` | Focused superset suite passed (`12` tests). |
| `pixi run all-checks` | `0` | Post-fix bounded aggregate gate passed on Sunday, July 26, 2026, with `97` repository tests passing. |
| `pixi run chatgpt-results-bundle-test` | `0` | Bundle inclusion/exclusion tests passed after adding nested smoke-run selection coverage. |
| `bash -lc 'export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1; pixi run python -B -m dt_adoc.cli smoke --run-id phase1d-superset-smoke-v2 --model-version adoc-literature-superset-v0.3.0'` | `0` | Dedicated superset smoke completed at [`output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke-v2/`](./output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke-v2/). |
| `python -B .codex/skills/adoc-result-validator/scripts/validate_run_manifest.py output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke-v2/run_manifest.json --root .` | `0` | Dedicated superset smoke manifest validated successfully. |
| `pixi run python -B -m unittest tests.unit.test_manifests -v` | `0` | Manifest helper test passed after adding explicit `simulation.stability` coverage. |
| `pixi run chatgpt-results-bundle -- --output output/reports/phase1d_chatgpt_bundle_v4.tar.gz` | `0` | Final live bundle validated and includes the latest dedicated superset smoke root `phase1d-superset-smoke-v3`. |

## Phase 1D Read-Only Reviews

- `analysis_worker` (`019f9e02-e3ed-7a00-bfed-823da9cd35f0`) returned
  `partial`:
  candidate ranking must remain `structural_only`, `MOD-13` is over-broadly
  labeled `functionally_active`, and the dedicated superset smoke still shows
  adverse phenotype-level behavior that blocks screening-readiness claims.
- `systems_biology_reviewer` (`019f9e0a-16d8-78e3-88a2-fc10c86944af`) returned
  `fail`:
  the live executable behavior falsifies Phase 1D as a completed screening
  milestone even though the structural family, catalog coverage, and external
  boundary bookkeeping are explicit.

## Overall

- Current task state: `Phase 1C literature-model integration advanced through post-review repair and bounded revalidation; full scientific acceptance remains blocked`
- Formal milestone: `Phase 1C literature model now runs through the canonical runtime with nonzero challenge competence, separated calibration/held-out reporting, and bounded analysis helpers; scientific promotion remains unsupported`
- Repository mode: full repository with immutable sources present under `data/`
- Claim ceiling: provisional executable research model and bounded smoke/runtime-analysis artifacts only
- Data audit: `not required: no new source data introduced`
- Independent scientific review: a `systems_biology_reviewer` handoff returned on July 26, 2026 from reviewer session `019f9dad-c733-70b1-b622-3f520504ce55` with `partial` status, classifying 1 finding as `critical`, 3 as `major`, and 1 as `note`; the parent repaired the critical protocol-semantics issue and a linked zero-pinned literature competence defect locally, which reopened the scientific-review gate, but no focused reviewer recheck was obtained afterward

## Phase 1C Summary

### Passed In This Pass

- Explicit model-version selection now works through the main runtime for both
  `adoc-core-v0.1.0` and `adoc-literature-v0.2.0`, and both model manifests
  validate.
- The literature protocol suite runs through the main sequential runtime and
  writes a dedicated smoke root at
  [`output/smoke/adoc-literature-v0.2.0/phase1c-lit-smoke-check/`](./output/smoke/adoc-literature-v0.2.0/phase1c-lit-smoke-check/).
- The repaired literature smoke no longer pins challenge competence and stable
  adhesion at zero:
  `adhesion_challenge_hormone_treated` now reports
  `OUT_MATERNAL_ADHESION_COMPETENCE = 0.00498` and
  `OUT_STABLE_ADHESION = 0.00108` in
  [`phenotype_probabilities.tsv`](./output/smoke/adoc-literature-v0.2.0/phase1c-lit-smoke-check/tables/phenotype_probabilities.tsv).
- Smoke tables now separate calibration from held-out validation via
  [`adhesion_calibration.tsv`](./output/smoke/phase1-structural-smoke/tables/adhesion_calibration.tsv)
  and
  [`adhesion_calibration_summary.tsv`](./output/smoke/phase1-structural-smoke/tables/adhesion_calibration_summary.tsv)
  for the baseline smoke, with matching literature-model tables under the
  literature smoke root.
- The literature calibration loss improved after the post-review repair from
  the earlier all-zero failure mode to
  `calibration_log_likelihood = -61.469139454430824` in
  [`adhesion_calibration_summary.tsv`](./output/smoke/adoc-literature-v0.2.0/phase1c-lit-smoke-check/tables/adhesion_calibration_summary.tsv).
- New bounded Phase 1C helper coverage now passes for:
  calibration leakage prevention, deterministic retained-ensemble logic,
  full-sequence stability record validation, bounded sensitivity-matrix
  completeness, and baseline-versus-literature comparison row construction.
- All bounded repository gates listed below passed on July 26, 2026, including
  a fresh `all-checks` rerun after the literature-topology repair.

### Still Blocked Or Partial

- The scientific-review gate is reopened because the parent repaired
  literature-model protocol semantics and the mechanistic competence rule after
  the reviewer handoff, but no focused reviewer recheck was obtained from the
  same session.
- The literature held-out comparator remains adverse:
  `adhesion_challenge_hormone_treated_mifepristone` still reports
  `OUT_STABLE_ADHESION = 0.00200`, which is higher than the repaired
  `HT` challenge smoke value `0.00108`; this blocks any claim that held-out
  behavior supports promotion.
- The emitted smoke artifacts
  [`tables/stability.tsv`](./output/smoke/phase1-structural-smoke/tables/stability.tsv)
  and
  [`tables/assumption_sensitivity.tsv`](./output/smoke/phase1-structural-smoke/tables/assumption_sensitivity.tsv)
  still reflect Phase 1B-style bounded summaries rather than a fully executed
  Phase 1C sequence-wide stability/comparison/sensitivity artifact set.
- The helper layer for bounded ensemble retention, full-sequence stability, and
  baseline-versus-literature comparison is implemented and tested, but it is
  not yet fully emitted as canonical smoke tables/reports/manifests.
- Phase 0 source-semantic blockers are now partially resolved.
  Collaborator confirmation on 2026-07-29 settled units (pg/mL), zero semantics
  (a stored zero is a measured non-detect), TOP/BOTTOM compartment semantics,
  the IGFBP-1 day-label discrepancy, the protocol day anchoring, and the true
  treated condition (`E2 + MPA + cAMP + XAV939`). Still unresolved: final cell
  labels, detection limits, the PAEP dilution factor, and donor/channel mapping
  -- the last of which is now known to be *partially unrecoverable* rather than
  merely undocumented, since the IGFBP-1/PRL column-to-chip mapping was lost.
  See `docs/collaborator_metadata_2026-07-29.md`.

## What Changed In This Pass

- Repaired the partially integrated Phase 1C validator/runtime scaffold so
  static validation now resolves each protocol condition against its declared
  model instead of the baseline/global node set.
- Repaired the literature perturbation challenge semantics so the mifepristone,
  anti-SPP1, ER-stress, and high-stiffness challenge protocols continue from
  `hormone_treated_maternal` rather than from an already challenged embryo
  comparator.
- Repaired the literature mechanistic competence rule in
  [`models/extended/adoc-literature-v0.2.0/network.bnd`](./models/extended/adoc-literature-v0.2.0/network.bnd)
  so `OUT_MATERNAL_ADHESION_COMPETENCE` reads directly from mechanistic
  receptive and decidual states instead of from downstream PAEP/PRL/IGFBP1
  reporting outputs that the joint-memory policy intentionally excludes.
- Updated the synchronized literature provenance layer in
  [`edge_evidence.tsv`](./models/extended/adoc-literature-v0.2.0/edge_evidence.tsv),
  [`README.md`](./models/extended/adoc-literature-v0.2.0/README.md), and
  [`differences_from_baseline.md`](./models/extended/adoc-literature-v0.2.0/differences_from_baseline.md)
  to match that repaired executable logic.
- Updated the baseline protocol integration tests to use the explicit
  `model_version` runtime API and added an end-to-end literature smoke runtime
  test through the main runner.
- Enabled literature-model smoke execution through the main CLI/runtime path and
  validated the resulting run manifest with the repository-local result
  validator.
- Added role-separated calibration summary tables to both baseline and
  literature smoke outputs so held-out `HT + mifepristone (1/8)` is reported
  separately from calibration rows.
- Added or verified bounded Phase 1C helper coverage in:
  [`src/dt_adoc/calibration/objectives.py`](./src/dt_adoc/calibration/objectives.py),
  [`src/dt_adoc/calibration/search.py`](./src/dt_adoc/calibration/search.py),
  [`src/dt_adoc/simulation/stability.py`](./src/dt_adoc/simulation/stability.py),
  and
  [`src/dt_adoc/simulation/sensitivity.py`](./src/dt_adoc/simulation/sensitivity.py),
  with corresponding focused tests.
- Re-ran the bounded repository validation suite and the separate literature
  smoke manifest validation successfully on July 26, 2026.
- Integrated the independent reviewer handoff into the parent ledger and kept
  the final Phase 1C status blocked rather than downgrading or suppressing the
  remaining scientific objections.

## July 26, 2026 Validation

| Command | Return Code | Result |
|---|---:|---|
| `pixi run harness-check` | `0` | Harness valid; warning only that data content hashes were not recomputed in that command. |
| `pixi run profile-parity` | `0` | PROFILE and PROFILE_v2 parity fixtures passed. |
| `pixi run lint` | `0` | Ruff checks passed after final cleanup. |
| `pixi run format-check` | `0` | Ruff format check passed after final cleanup. |
| `pixi run test` | `0` | `84` tests passed after the literature regression was added. |
| `pixi run compile-models` | `0` | Baseline compile task passed. |
| `pixi run validate-models` | `0` | Static model validation returned `status: valid` for baseline and literature models. |
| `pixi run smoke` | `0` | Baseline smoke completed at [`output/smoke/phase1-structural-smoke/`](./output/smoke/phase1-structural-smoke/). |
| `pixi run validate-smoke` | `0` | Baseline smoke manifest validated successfully. |
| `pixi run report-smoke` | `0` | Baseline smoke report exists. |
| `pixi run chatgpt-results-bundle-test` | `0` | Bundle inclusion/exclusion tests passed. |
| `pixi run all-checks` | `0` | Bounded aggregate gate passed on July 26, 2026. |
| `pixi run bash -lc 'export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1; python -B -m dt_adoc.cli smoke --run-id phase1c-lit-smoke-check --model-version adoc-literature-v0.2.0'` | `0` | Literature smoke completed at [`output/smoke/adoc-literature-v0.2.0/phase1c-lit-smoke-check/`](./output/smoke/adoc-literature-v0.2.0/phase1c-lit-smoke-check/). |
| `python -B .codex/skills/adoc-result-validator/scripts/validate_run_manifest.py output/smoke/adoc-literature-v0.2.0/phase1c-lit-smoke-check/run_manifest.json --root .` | `0` | Literature smoke manifest validated successfully. |

## Phase 1C Reviewer Findings

- `critical`: literature perturbation challenges were originally chained from
  `adhesion_challenge_hormone_treated` instead of from the matched maternal
  comparator; the parent repaired this in
  [`config/protocols.yaml`](./config/protocols.yaml) and verified the repaired
  initialization chain in
  [`protocol_initializations.tsv`](./output/smoke/adoc-literature-v0.2.0/phase1c-lit-smoke-check/tables/protocol_initializations.tsv).
- `major`: curated literature memory policies still depend on latent interface
  and mechanics relays that remain scientifically fragile and not independently
  falsified.
- `major`: the pre-repair literature smoke artifact was not promotable because
  challenge outputs were pinned at zero; the parent repaired the competence
  logic and improved the smoke artifact, but promotion remains unsupported.
- `major`: the helper layer for full-sequence stability, assumption sensitivity,
  and comparison remains only partially wired into the canonical emitted smoke
  tables and reports.
- `note`: the reviewer did not find anti-SPP1 directly shutting off total
  competence or SPP1 transcription in the default executable logic.

## Historical Note

- The older Phase 1B and literature-extension sections below remain as lineage
  history. They are superseded where this July 26, 2026 Phase 1C summary and
  validation log differ.

## Literature Extension Milestone

### Passed

- `context/literature/` now contains the reconciled embryo-adhesion knowledge
  package promoted from `tmp/`, including `knowledge-base.yaml`,
  `references.tsv`, `mechanisms.tsv`, `candidate-nodes.tsv`,
  `candidate-edges.tsv`, `source-provenance.tsv`, and
  `validation-report.md`.
- Repository discovery files were updated so the literature package is visible
  from [`README.md`](./README.md), [`context/README.md`](./context/README.md),
  [`context/references/README.md`](./context/references/README.md), and
  [`models/README.md`](./models/README.md).
- The literature extension is executable as
  [`models/extended/adoc-literature-v0.2.0/network.bnd`](./models/extended/adoc-literature-v0.2.0/network.bnd)
  with matching `baseline.cfg`, eight condition configs, and synchronized
  `node_dictionary.tsv`, `edge_evidence.tsv`, `phenotype_contract.tsv`, and
  `provenance.toml`.
- The standalone model preserves the required qualitative directions:
  hormone-treated > untreated, mifepristone reduces adhesion, anti-SPP1 causes
  a partial reduction, embryo absence and embryo incompetence force stable
  adhesion to zero, and ER stress or excessive stiffness reduce but do not
  deterministically abolish adhesion competence.
- Bundle coverage now includes the literature context package through the
  existing ChatGPT bundle tests.

### Independent Review And Resolution

- A `systems_biology_reviewer` handoff completed on 2026-07-25.
- The reviewer flagged five major issues:
  embryo-conditioned cues were enabled in the required suite;
  the mechanics branch acted as a hard failure gate;
  the uncertainty notes did not match the executable logic;
  provenance still pointed at `tmp/`;
  and the phenotype contract overstated executable outputs.
- Those issues were resolved by:
  setting `IN_HCG` and `IN_EMBRYO_CONDITIONED_SIGNAL` to `FALSE` in the required
  suite;
  introducing `X_MECHANICAL_STRESS_RELAY`;
  updating the uncertainty and differences notes to match the executable rules;
  repointing `provenance.toml` to `context/literature/`;
  and shrinking `phenotype_contract.tsv` to the actual executable outputs.

## Preflight And Environment

| Gate | Evidence | Status |
|---|---|---|
| `pwd` | `/home/francois/Projects/DT_ADOC` | passed |
| `git status --short` | return code `128`: `fatal: not a git repository (or any of the parent directories): .git` | blocked |
| `git diff --stat` | return code `129`: `warning: Not a git repository. Use --no-index ...` | blocked |
| Harness validity | `pixi run harness-check` returned `0` on July 25, 2026 | passed |
| Immutable source manifest validity | `python -B .codex/skills/adoc-data-audit/scripts/check_data_manifest.py --root . --check-hashes` returned `0` on July 25, 2026 | passed |

## Phase 1B Scientific Execution

### Passed

- Maternal-state protocols keep `IN_EMBRYO_PRESENT=FALSE` and
  `IN_TROPHECTODERM_COMPETENT=FALSE`; embryo-challenge protocols flip both to
  `TRUE`.
- Sequential continuation is now explicitly joint by default for Phase 1B and
  the transferred support is recorded per protocol.
- The continuation fixture in
  [`tests/integration/test_maboss_continuation_modes.py`](./tests/integration/test_maboss_continuation_modes.py)
  proves:
  - CFG bracket `istate` form executes.
  - deterministic `TRUE`/`FALSE` CFG forms execute.
  - Python single-node and joint `set_istate` forms execute.
  - marginal continuation introduces mixed `A`-only and `B`-only states.
  - joint continuation preserves the correlated `00/11` support.
  - excessive cutoff rejection raises an explicit error.
- The modular adhesion interface remains in place; anti-SPP1 reduces one route
  and no longer forces total adhesion competence to zero.
- XAV939 necessity remains isolated in an explicit uncertain-rule variant rather
  than an obligatory gate in the default baseline.
- Intermediate adhesion probabilities emerge in the smoke run and feed the
  binomial calibration table.
- Candidate ranking remains labeled `structural_only`.
- PROFILE parity and PROFILE_v2 gradient-inhibition parity fixtures both pass.

### Still Provisional Or Blocked

- Phase 0 donor/workbook semantics are now partially unblocked.
  Collaborator confirmation on 2026-07-29 settled units (pg/mL), zero semantics
  (a stored zero is a measured non-detect), TOP/BOTTOM compartment semantics,
  the IGFBP-1 day-label discrepancy, the protocol day anchoring, and the true
  treated condition (`E2 + MPA + cAMP + XAV939`). Still unresolved: final cell
  labels, detection limits, the PAEP dilution factor, and donor/channel mapping
  -- the last of which is now known to be *partially unrecoverable* rather than
  merely undocumented, since the IGFBP-1/PRL column-to-chip mapping was lost.
  See `docs/collaborator_metadata_2026-07-29.md`.
- No retained acceptable ensemble of parameter/rule variants is produced yet.
- Calibration-versus-validation labeling is explicit in
  `adhesion_calibration.tsv` and the manifest cohort metadata, but not all
  output tables are fully role-labeled, so canonical acceptance remains blocked.
- Barrier, viability, inflammation, senescence, and washout outputs remain
  structural placeholders rather than accepted mechanistic screening outputs.

## Smoke Snapshot

Smoke root:
[`output/smoke/phase1-structural-smoke/`](./output/smoke/phase1-structural-smoke/)

Key inspected artifacts:

- Manifest:
  [`run_manifest.json`](./output/smoke/phase1-structural-smoke/run_manifest.json)
- Protocol initialization table:
  [`tables/protocol_initializations.tsv`](./output/smoke/phase1-structural-smoke/tables/protocol_initializations.tsv)
- Phenotype table:
  [`tables/phenotype_probabilities.tsv`](./output/smoke/phase1-structural-smoke/tables/phenotype_probabilities.tsv)
- Adhesion calibration table:
  [`tables/adhesion_calibration.tsv`](./output/smoke/phase1-structural-smoke/tables/adhesion_calibration.tsv)
- Report:
  [`report/smoke_report.md`](./output/smoke/phase1-structural-smoke/report/smoke_report.md)

Observed July 25, 2026 smoke behavior.

> **HORIZON WARNING, added 2026-07-29.** Every probability in this section is a
> **declared-horizon** value: `max_time` 1.0 for each adhesion challenge and 4.0
> for the hormone phase, `time_tick` 0.1, single seed, as configured in
> `config/protocols.yaml` at the time. `docs/endpoint_convergence_finding.md`
> subsequently established that the adhesion endpoints are read roughly **4000x
> before their logical fixed point**, and that the anomalies recorded below —
> including the mifepristone arm scoring above the unperturbed reference — are
> consequences of that readout horizon rather than of the Boolean model. At the
> converged horizon every direction tested is correct. These numbers are retained
> as the historical record of what was observed; they must not be quoted as the
> model's behaviour without their horizon. All horizons are dimensionless MaBoSS
> relative-time parameters, never day counts.

- Maternal states:
  - `basal`: `OUT_MATERNAL_ADHESION_COMPETENCE = 0.0`
  - `e2_priming`: `OUT_MATERNAL_ADHESION_COMPETENCE = 0.0`
  - `hormone_treated`: `OUT_EPITHELIAL_RECEPTIVE = 0.7669`,
    `OUT_STROMAL_DECIDUALIZED = 0.4550`,
    `OUT_MATERNAL_ADHESION_COMPETENCE = 0.1738`
  - `hormone_treated_mifepristone`:
    `OUT_MATERNAL_ADHESION_COMPETENCE = 0.0224`
  - `hormone_treated_anti_spp1`:
    `OUT_MATERNAL_ADHESION_COMPETENCE = 0.0319`
  - `washout`: `OUT_MATERNAL_ADHESION_COMPETENCE = 0.1453`
- Embryo challenge states:
  - `adhesion_challenge_basal`: `OUT_STABLE_ADHESION = 0.0`
  - `adhesion_challenge_hormone_treated`:
    `OUT_STABLE_ADHESION = 0.1630`
  - `adhesion_challenge_hormone_treated_mifepristone`:
    `OUT_STABLE_ADHESION = 0.0119`
  - `adhesion_challenge_hormone_treated_anti_spp1`:
    `OUT_STABLE_ADHESION = 0.0121`
  - `adhesion_challenge_washout`:
    `OUT_STABLE_ADHESION = 0.1605`
- Calibration table:
  - basal `0/12` calibration probability `0.0`
  - HT `9/19` calibration probability `0.16295`
  - HT+mifepristone `1/8` validation probability `0.01188`

Continuation manifest inspection:

- All sequential Phase 1B transitions are recorded as
  `continuation_mode = joint`.
- The recorded method is `projected_joint_memory`.
- `protocol_initializations.tsv` records memory nodes, cutoff `1e-06`,
  source-state counts, retained-state counts, dropped probability mass, and
  transferred-state counts for each sequential protocol.

Bundle inspection:

- Latest inspected archive root:
  [`output/reports/`](./output/reports/)
- The final inspected archive for this run was generated on July 25, 2026 with
  reported size `0.30 MiB`.
- Direct `tar -tf` inspection confirmed inclusion of:
  `IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_STATUS.md`,
  `REQUIREMENTS_COVERAGE.tsv`, `THIRD_PARTY_NOTICES.md`, `references/`, and
  `output/smoke/phase1-structural-smoke/`.

## Validation Commands

| Command | Return Code | Result |
|---|---:|---|
| `pixi run python -B -m unittest tests.unit.test_extended_model_contracts tests.integration.test_extended_model_runtime -v` | `0` | Standalone literature extension contracts and runtime smoke passed. |
| `pixi run python - <<'PY' ... _run_condition(...) ... PY` | `0` | Direct extended-model smoke confirmed the required qualitative directions and bounded ER-stress/stiffness reduction. |
| `pixi run compile-models` | `0` | Baseline BND and all required condition CFGs rendered after the literature-extension updates. |
| `pixi run validate-models` | `0` | Static model contract returned `status: valid`. |
| `pixi run test` | `0` | `61` tests passed, including the new literature-package and extended-model checks. |
| `pixi run harness-check` | `0` | Harness valid. |
| `python -B .codex/skills/adoc-data-audit/scripts/check_data_manifest.py --root . --check-hashes` | `0` | Immutable source manifest valid. |
| `pixi run lint` | `0` | Ruff checks passed. |
| `pixi run format-check` | `0` | Ruff format check passed. |
| `pixi run profile-parity` | `0` | PROFILE and PROFILE_v2 parity fixtures passed. |
| `pixi run python -m unittest tests.integration.test_maboss_continuation_modes -v` | `0` | Initial-state and continuation-mode fixture passed. |
| `pixi run python -m unittest tests.integration.test_protocols -v` | `0` | Protocol separation and continuation metadata checks passed. |
| `pixi run python -m unittest tests.integration.test_cmaboss_runtime tests.biological_constraints.test_phase1b_constraints -v` | `0` | Runtime toy model and biological constraints passed. |
| `pixi run test` | `0` | Earlier Phase 1B bounded suite passed before the literature-extension update; superseded by the later `61`-test rerun above. |
| `pixi run smoke` | `0` | Smoke run completed and rewrote `output/smoke/phase1-structural-smoke/`. |
| `pixi run validate-smoke` | `0` | Smoke manifest and all referenced outputs validated. |
| `pixi run report-smoke` | `0` | Smoke report file exists. |
| `pixi run chatgpt-results-bundle-test` | `0` | Bundle inclusion/exclusion tests passed. |
| `pixi run chatgpt-results-bundle --output output/reports/chatgpt_results_phase1b_20260725.tar.gz` | `0` | Initial bundle exported and validator reported `status: valid` with `checked_files: 211`. |
| `pixi run chatgpt-results-bundle --output output/reports/chatgpt_results_phase1b_20260725.tar.gz` | `1` | Re-run refused to overwrite the existing archive, so a new output path was required. |
| `pixi run chatgpt-results-bundle --output output/reports/chatgpt_results_phase1b_20260725_v2.tar.gz` | `0` | Final bundle exported and validator reported `status: valid` with `checked_files: 211`. |
| `pixi run all-checks` | `0` | Full bounded Phase 0/1 gate aggregate passed after the Phase 1B updates. |

## Remaining Blockers

1. Phase 0 source-semantic blockers remain unresolved.
2. No accepted ensemble retention exists for non-identifiability handling.
3. Calibration-versus-validation labeling is not yet complete across every
   output table.
4. Mechanistic safety and washout outputs are not yet sufficient for
   non-structural candidate ranking.

## Next Required Actions

1. Resolve or explicitly accept the remaining Phase 0 source-semantic blockers.
2. Extend calibration/validation role labeling across every canonical output
   table.
3. Keep canonical completion provisional until the remaining repository-level
   acceptance blockers are either passed or explicitly accepted as blocked.
