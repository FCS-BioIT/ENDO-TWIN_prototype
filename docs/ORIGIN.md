# Origin of this repository

ENDO-TWIN was created on **2026-11-22** from an earlier, private prototype of
the same group. It is a new, independent repository: it carries the prototype's
files but **none of its Git history**. This page records where everything came from, so that provenance
survives the loss of history.

## Source

| | |
|---|---|
| Source repository | a private repository of the same group (not public) |
| Source commit | `b1de5f90582f02291789eb72753fa5ab1f2d8c88` |
| Commit date | 2026-11-18 15:00:55 +0100 |
| Commit subject | Merge pull request #37 from fransua-fcs/feat/scientific-review-2026-11-18 |
| Source history | 538 commits on `main`; 59 remote branches. None retained. |
| Migration date | 2026-11-22 |

## How the copy was made

1. A fresh clone of the source repository was made from GitHub (the source
   working copy was not touched).
2. The clone's `.git` directory was moved out of the new tree, and a new
   repository was initialised with `git init -b main`. No original objects,
   branches, tags, refs or remotes are present.
3. Only files tracked at the source commit were carried. Untracked and ignored
   material was never copied: `output/`, `tmp/`, environments and caches, the
   local 3.4 GB scRNA RDS, the gitignored annotation workbook and the literature
   PDFs (which were never committed in the source either).
4. The adaptation described below was made and committed. The history of
   this repository starts at the migration; no prototype commit is included.

## Source model versions

All eight prototype model versions are kept unchanged under `models/`. Counts are
recomputed by `src/endotwin/foundation_metrics.py`
(`docs/research_foundation_metrics.json`).

| Version | Path | Nodes | Dependencies | Distinct Boolean functions |
|---|---|---|---|---|
| adoc-core-v0.1.0 | `models/baseline/` | 43 | 56 | not computed |
| adoc-literature-v0.2.0 | `models/extended/` | 55 | 90 | not computed |
| adoc-literature-superset-v0.3.0 | `models/superset/` | 58 | 96 | 32 |
| adoc-literature-superset-v0.4.0 | `models/superset/` | 59 | 97 | 35 |
| adoc-literature-superset-v0.5.0 | `models/superset/` | 59 | 97 | 35 (executable files identical to v0.4.0) |
| adoc-literature-superset-v0.5.1 | `models/superset/` | 59 | 95 | 35 |
| adoc-literature-superset-v0.5.2 | `models/superset/` | 59 | 93 | 35 |
| adoc-literature-superset-v0.6.0 | `models/superset/` | 56 | 89 | 29 |

The ENDO-TWIN mainline versions are new. `endotwin-v0.1.0`
(`endotwin/models/endotwin-v0.1.0/`) derives from
`adoc-literature-superset-v0.6.0`, and the current `endotwin-v0.2.0` derives from
v0.1.0; each version's `lineage.tsv` maps every node of its parent.

## Reused unchanged

- The complete prototype code base `src/dt_adoc/` (simulation, protocols,
  intervention layer, evidence grading, structure and identifiability analysis,
  concordance, scRNA audits, personalization contracts, reporting).
- All model versions under `models/`, all configuration under `config/`, the
  evidence and literature registers under `context/`, the source data under
  `data/` and the canonical tables under `input_tables/`.
- All analysis reports and committed results under `docs/` (except the wording
  changes listed below), the figures under `docs/assets/`, the perturbation
  specifications and the PROFILE parity fixtures.
- The prototype test suite, with the changes listed below.

## Added

- The ENDO-TWIN mainline: `src/endotwin/`, `endotwin/` (model, configuration,
  evidence, prediction-freezing records, results), `tests/mainline/`, the
  ENDO-TWIN figures in `docs/assets/endotwin/`.
- New documentation: this file, `README.md`, `docs/RESEARCH_FOUNDATION_AUDIT.md`,
  `docs/scientific_evidence.md`, `docs/literature_curation.md`,
  `docs/model_construction.md`, `docs/experimental_data.md`,
  `docs/model_evaluation.md`, `docs/software_verification.md`,
  `docs/architecture/future_multiscale_extension.md`, `docs/legacy/README.md`,
  `docs/research_foundation_metrics.json` and the verification records in
  `docs/verification/`.
- `tests/unit/source_history.py`, the guard for history-bound legacy checks.

## Modified

| File | Change | Why |
|---|---|---|
| `README.md` | New ENDO-TWIN front page | The prototype page is kept at `docs/legacy/PROTOTYPE_README_2026-10-21.md`, verbatim apart from two renamed skill folders |
| `AGENTS.md` | Rewritten for ENDO-TWIN | Same evidence and claim rules; new layout and prospective-evaluation rules |
| `pixi.toml` | Workspace renamed `endo-twin`; `endotwin-*` tasks added; review-harness task removed | `pixi.lock` is byte-identical to the source |
| `.gitignore` | Assistant-tool block removed; `endotwin/results/` exempted from the inherited `results/` rule | Tool configuration is not part of the project; ENDO-TWIN results are committed |
| `tests/unit/test_readme_contract.py` | Reads the preserved prototype README | Its assertions are unchanged |
| `tests/unit/test_source_test_references.py` | One class removed (it checked the removed tool configuration) | |
| `tests/test_chatgpt_bundle.py`, `scripts/make_chatgpt_results_bundle.sh` | Planning ledgers read from `docs/legacy/`; removed configuration files no longer bundled | |
| `tests/unit/test_closure_replay.py`, `test_phase1b_closure.py`, `test_phase2a_contract.py`, `test_phase2b_contract.py`, `test_post_closure_adjudications.py`, `test_c3a_kinetic_readout.py`, `test_endpoint_figure.py`, `test_v05_u6_semantics.py`, `test_observation_corrections.py`, `test_generated_date_determinism.py`, `test_test_guards.py` | Declared skip when the prototype commits they read are absent (the guard-list test adjusts its expected count accordingly) | See `docs/software_verification.md` |
| `scripts/run_test_guards.py`, `scripts/run_test_parallel.py` | Accept exactly that declared skip reason | Any other skip still fails |
| `.codex/agents/*.toml` | Assistant-vendor model pins removed | Tool configuration only |
| `THIRD_PARTY_NOTICES.md` | MaBoSS and PyMaBoSS dependency section appended | |
| Nine legacy documents under `docs/` and `context/literature/` | Names of AI assistant products removed from authorship and reviewer notes; the review-quality caveats (for example "same-model-family stand-in review, degraded") are kept | At the owner's request. Byte-exact originals are at the source commit |

One frozen document, `docs/stage3_experiment_selection.md`, was **not**
reworded. Its SHA-256 is chained through the closed Phase 1B, 2A and 2B records
into the code-digest record of the pre-registered C3a run, so any byte change
would rewrite historical execution records.

## Moved

- The prototype's `README.md` to `docs/legacy/PROTOTYPE_README_2026-10-21.md`.
- `IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_STATUS.md`,
  `REQUIREMENTS_COVERAGE.tsv`, `TASK_CONTRACT.md` to `docs/legacy/`.

## Not carried

- Assistant-specific instruction and settings files, three assistant agent
  descriptors, and the review-harness configuration with its explanatory
  document. None is read by the scientific code.
- Everything untracked at the source commit (see "How the copy was made").

## What the loss of history changes

- Legacy checks in ten test modules read frozen commits of the prototype history
  (closed-phase replays, pre-registration bindings, ancestry of recorded
  commits): five whole modules (301 tests) and individual classes, tests and
  subtests in five more; the guard-list self-test reports the skipped guard
  modules as subtest skips. They skip here with one declared reason (63 skips in
  the recorded run) and passed at the source commit
  (`docs/verification/source_baseline_b1de5f9.json`; list in
  `docs/software_verification.md`).
- `pixi run replay-closed-phases`, `build-phase1b-closure`,
  `build-phase2a-contract`, `build-phase2b-audit` and the C3a execution path
  need that history and cannot run in this repository. Run them in the source
  repository at the source commit.
- The run records in `docs/verification/runs/` name commits of the source
  history; `pixi run check-run-record` therefore cannot pass here. They remain as
  historical records.
- Recorded `git_commit` fields in the prototype result metadata name source commits.
  Content digests (SHA-256) still bind those results to the files present here.

## Licences, data and redistribution

- The source repository had **no licence file**, and none has been added.
  Choosing a licence is the owners' decision.
- `THIRD_PARTY_NOTICES.md` (PROFILE and PROFILE_v2, BSD 3-Clause; a reference
  implementation inspected without copying) is preserved, with a section added
  for MaBoSS (BSD 3-Clause) and PyMaBoSS, which are installed dependencies
  (`pixi.toml`), not vendored.
- `data/` holds the in-house ADOC manuscript files, the secreted-protein
  workbook and three published PDFs (Zaragozano et al. 2026, Science Advances;
  Montagud et al. 2022; Montagud 2026). The repository is private. Before any
  public release, check the redistribution terms of the three PDFs and the
  status of the unpublished manuscript files; `data/` is otherwise immutable
  source evidence and is pinned by `config/data_manifest.tsv`.

## Scientific limitations inherited from the prototype

Listed and classified (addressed in ENDO-TWIN, or kept as research questions)
in `docs/RESEARCH_FOUNDATION_AUDIT.md`, section 7.
