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
| `docs/codex/agents/*.toml` | Assistant-vendor model pins removed | Tool configuration only (the tree was `.codex/` until 2026-11-23) |
| `docs/THIRD_PARTY_NOTICES.md` | MaBoSS and PyMaBoSS dependency section appended | |
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

## This repository's own history was rewritten once, on 2026-11-23

The commit that gave the earlier prototype a generic name was applied
retroactively, which rewrote every commit after `387b50a Initial commit`. The
rewrite was published on 2026-11-23 with `git push --force-with-lease`, so the
public history before that date — which still carried the prototype's own name
in `pixi.toml` and task descriptions from the second commit on — was replaced.

| | |
|---|---|
| Commits rewritten | 202 of 203; only `387b50a` is shared with the superseded history |
| End state | unchanged: both tips had tree `10eedbb46b0ffdb5bc809ee96d32a32a1b40503b` |
| Superseded tip | `55623df` (the rewrite's equivalent is `f7ba0f9`, same subject, author, dates and tree) |

Only commit identity changed, never content at the tip. Two consequences:

- `endotwin/results/endotwin-v0.2.0/run_manifest.json` records
  `repository_state_at_generation.commit = 7751fda…`, a commit of the superseded
  history. It was left as committed: the `inputs_sha256` digests, not the commit
  id, are what bind those results, and `pixi run endotwin-all` reproduces every
  one of them byte for byte.
- Clones, forks or caches taken before 2026-11-23 still hold the superseded
  commits. A force-push does not reach them.

### `.codex/` moved to `docs/codex/`, 2026-11-23

The owner asked for the smallest possible repository root and accepted the
consequence. `.codex/` is a tool-convention directory: Codex-style tooling
discovers agents and skills by looking for it **at the repository root**, so
after this move the three repository-local skills (`adoc-data-audit`,
`adoc-result-validator`, `maboss-digital-twin`) and the four agent definitions
are no longer auto-discovered. The owner's global `~/.codex/skills` install is
untouched, and the two validators that pixi executes keep working because the
tasks call them by explicit path.

Reverting is one `git mv docs/codex .codex` plus the reference updates in
`pixi.toml`, `AGENTS.md`, `src/scripts/make_chatgpt_results_bundle.sh`,
`tests/test_project_validators.py` and `tests/unit/test_manifests.py`.

Mentions under `docs/legacy/` still say `.codex/`; they record the layout as it
was. `docs/external-skills.md` and `context/references/README.md` refer to
`~/.codex/` in the owner's home directory, not to this tree, and are unchanged.

## Licences, data and redistribution

- **This repository is public**, at
  `github.com/FCS-BioIT/ENDO-TWIN_prototype`. The remote's name is historical:
  this repository is the ENDO-TWIN mainline, and the "prototype" named
  throughout this document is the separate private repository above, which has
  never been public.
- The source repository had **no licence file**. This repository carries one
  from 2026-11-23: `LICENSE`, an **evaluation licence**, not an open-source
  one. Copyright © 2026 Fundación Carlos Simón, all rights reserved, with a
  narrow grant to reviewers appointed by the Agencia Estatal de Investigación
  for the 2026 *Proyectos de Generación de Conocimiento* call — consultation,
  and the copies and test runs that evaluation needs. Commercial use, use for
  other purposes, modification (including for one's own use), incorporation
  into other products and redistribution are all excluded, and the licence
  covers this repository's own code and documentation only. The Spanish text
  is authoritative.
- Being publicly readable on GitHub does not widen that grant. The repository
  is public **by decision**, so that a reviewer can open the link given in the
  proposal without access being managed for each one. The accepted consequence
  is that GitHub's Terms of Service let any user view and fork a public
  repository: a fork is a redistribution the licence does not permit, the
  licence does not undo forks already made, and GitHub's own grant is not
  displaced by it. The alternative — a private repository with the reviewers
  invited — would match the licence's wording more closely and was not taken.
- `docs/THIRD_PARTY_NOTICES.md` (PROFILE and PROFILE_v2, BSD 3-Clause; a reference
  implementation inspected without copying) is preserved, with a section added
  for MaBoSS (BSD 3-Clause) and PyMaBoSS, which are installed dependencies
  (`pixi.toml`), not vendored.
- `data/` holds the in-house ADOC manuscript files, the secreted-protein
  workbook and three published PDFs (Zaragozano et al. 2026, Science Advances;
  Montagud et al. 2022; Montagud 2026). None of it is ours to redistribute and
  `LICENSE` does not cover it, so **`data/` has been untracked since
  2026-11-23** (`.gitignore`), including its README, whose text moved to
  `docs/source_data.md` so that `data/` does not appear in the repository
  listing at all. The files
  remain the immutable source layer on the machines that hold them and are
  still pinned by `config/data_manifest.tsv`; a clone obtains them out of band.
- Those files were tracked between the 2026-11-22 migration and 2026-11-23 and
  **remain in the Git history and on the public remote**. Untracking does not
  retract them, and forks or caches made in that window are not reachable from
  here. Removing them from history would rewrite every commit and break the
  SHA-256 chains in the closed-phase records; that was weighed and not done.
- Accepted consequence, already true for the gitignored RDS and annotation
  workbook: a fresh clone cannot pass `check_data_manifest.py --check-hashes`,
  and the prototype tests that read `data/` need the files restored. The
  ENDO-TWIN mainline (`src/endotwin`, `endotwin/`, `tests/mainline`) reads
  nothing under `data/`.

## Scientific limitations inherited from the prototype

Listed and classified (addressed in ENDO-TWIN, or kept as research questions)
in `docs/RESEARCH_FOUNDATION_AUDIT.md`, section 7.
