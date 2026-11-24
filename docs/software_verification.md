# Software verification and reproducibility

**Software correctness is not biological validation.** The suite below shows
that the code does what it says, reproducibly, and that recorded results still
follow from the committed files. It says nothing about whether the biological
rules are right.

## Test runs

Each row names the commit it was run on. A row is **not** a claim about the
current HEAD: documentation-only commits land after a suite run, so the tested
commit is normally an ancestor of HEAD. `tested_tree` in
`docs/verification/endotwin_suite_records.json` is authoritative.

| Run | Tests | Result | Record |
|---|---|---|---|
| This repository, complete suite (`pixi run test`), at commit `ad19a2e` | 2,613 | 2,550 passed, 0 failed, 63 skipped in 948 s wall, 1,037 s CPU (single process) | `docs/verification/endotwin_suite_records.json`, log `docs/verification/endotwin_suite.log.gz` |
| ENDO-TWIN mainline only (`pixi run endotwin-test`) | 140 | OK | same record |
| Prototype at the source commit `b1de5f9`, fresh clone, before any change | 2,767 | 2,757 passed, 1 failed, 9 skipped in 1,980 s | `docs/verification/source_baseline_b1de5f9.json`, log alongside |
| Prototype benchmark, 2026-10-16 (owner's working copy) | 2,415 | OK (1 skip) in 1,958 s | `docs/verification/cache_benchmark_record.json` |

## Where the suite's time goes, and how far it parallelises

Measured 2026-11-24 by timing every test module in one process;
[`verification/module_times.json`](verification/module_times.json) has all 139
modules with wall and CPU time each.

| | |
|---|---|
| Wall time, complete suite | **948 s** (`pixi run test`, single process) |
| CPU time, complete suite | **1,037 s** (user 1,006 s + system 30 s) |
| Peak resident memory | **9.7 GB** |
| Longest single module | **128 s** — `unit.test_v05_u6b_muc1_reconciliation` (36 tests) |

CPU time slightly **exceeds** wall time because some tests spawn subprocesses
(`pixi run`, MaBoSS, `git`), so a little work already overlaps. The ratio is
1.07, so the suite is otherwise serial.

**The parallel ceiling is set by the longest module**, because whole modules
must stay together for their fixtures. Ideal packings of the measured times:

| Workers | Makespan | Speedup |
|---|---|---|
| 1 (today) | 948 s | 1.0x |
| 2 | 474 s | 2.0x |
| 4 | 237 s | 4.0x |
| 8 | 128 s | 7.4x |
| 16 | 128 s | 7.4x — no further gain |

Beyond eight workers nothing improves: the 128 s critical path binds. Memory is
not the constraint on this machine (125 GB total against a 9.7 GB serial peak),
though per-worker peaks would need checking before fixing a worker count.

**`pixi run test-parallel` currently delivers none of this.** Its split gives
worker A a single module that was the longest in the prototype and that skips in
about 0.2 s here, so worker B runs everything: measured speedup **1.00x**. The
split is worth redoing against the measured times, and doing so is a deliberate
change, because `WORKER_A_MODULES` is pinned by `unit.test_test_parallel`.

The 10 non-passes at the source commit all need files that are local-only by
design and absent from any clone: the 3.4 GB scRNA RDS and the gitignored
annotation workbook (1 failure, 7 skips), the literature PDFs (1 skip) and a local
review extract (1 skip). For the run recorded here those local-only files were
hard-linked from the owner's prototype working copy (gitignored, never committed),
as in the 2026-10-16 benchmark, so all 10 checks ran and passed. In a plain
clone they fail or skip exactly as at the source.

### Skips declared in this repository

| Reason | Count |
|---|---|
| requires the prototype's source Git history: commit(s) 0c7da9c174b6, ef34c1079267 absent from this history-free repository (docs/ORIGIN.md); passed at | 44 |
| requires the prototype's source Git history: commit(s) 97f88f55ce62 absent from this history-free repository (docs/ORIGIN.md); passed at the source co | 13 |
| requires the prototype's source Git history: commit(s) 97f88f55ce62, 51b8bd11bc79 absent from this history-free repository (docs/ORIGIN.md); passed at | 4 |
| requires the prototype's source Git history: evidence-root commit 91f79ed is not available in this clone (shallow history or a synthetic snapshot); bl | 1 |
| requires the prototype's source Git history: recorded commit 7a7eb34a4f7e is absent from this history-free repository (docs/ORIGIN.md) | 1 |

**History-bound checks.** ENDO-TWIN has no prototype Git history
(`docs/ORIGIN.md`). Checks that read frozen commits of that history skip with a
reason starting "requires the prototype's source Git history"
(`tests/unit/source_history.py`). They are:

| Test module or class | What it reads |
|---|---|
| `unit.test_closure_replay` | closure commit `97f88f5` (closed-phase replay view) |
| `unit.test_phase1b_closure` | closure commit `97f88f5` |
| `unit.test_phase2a_contract` | closure commit `97f88f5` |
| `unit.test_phase2b_contract` | closure commit `97f88f5` and the Phase 2B base commit `51b8bd1` |
| `unit.test_post_closure_adjudications` | `97f88f5` |
| `unit.test_c3a_kinetic_readout`: `ConstantsMatchThePreregistration`, `TheBindingRefuses`, `CompleteBinding`, `BindingResolvesThroughGit`, `GeneratorInventoryIsImmutable` | pre-registration commits `0c7da9c`, `ef34c10`, and `HEAD~1` |
| `unit.test_endpoint_figure`: `test_recorded_commit_is_reachable_from_the_reviewed_tree` | recorded run commit `7a7eb34` |
| `unit.test_v05_u6_semantics`: evidence-root blob identity | evidence root `91f79ed` |
| `unit.test_observation_corrections`: `test_corrections_file_is_a_declared_post_closure_addition` | closure commit `97f88f5` (live drift against the closure tree) |
| `unit.test_generated_date_determinism`: the three closed-phase builder subtests | closure commit `97f88f5` (replay view) |
| `unit.test_test_guards`: per-guard subtests for the skipped guard modules (8) | indirect: those guard modules skip at import |

A skipped module counts as one skip. The five module-level skips stand for
301 tests that ran and passed at the source commit (closure replay 20, Phase 1B
64, Phase 2A 102, Phase 2B 94, post-closure adjudications 21); the other skips
are single tests, classes or subtests. Both runners (`scripts/run_test_guards.py`,
`scripts/run_test_parallel.py`) accept exactly this reason and still fail on any
other skip. The checks run unchanged in a checkout that has the commits, for
example the source repository at `b1de5f9`.

## What the tests verify

| Area | Representative tests |
|---|---|
| Boolean-rule execution and exact structure | `tests/mainline/test_structure_and_hypotheses.py` (closed-form enumeration; independent reproduction of the recorded v0.6.0 counts: 29 functions, 7 alias classes, 17 inert nodes, 15 + 5 absorbed or never-binding); `unit.test_cached_primitives_equivalence`, `unit.test_fixed_point_identities` |
| Competing hypotheses | Q1, Q2 and inflammation predictions asserted exactly; relay and relay-plus-direct proven to compute the same function; committed prediction and discrimination tables regenerate |
| Perturbation application and timing | `tests/mainline/test_simulation_and_timing.py`: perturbations only in their declared phase, bit-identical trajectories before onset, dynamic knockdown onset; `unit.test_protocol_intervention_timing`, integration runtime tests |
| Phase carry-over | No restart at phase boundaries (proliferation remains ON at the first sample after E2 priming) |
| Seed reproducibility | Identical trajectories for the same seed; phase and replicate seeds at least one trajectory block apart; different seeds agree at the fixed point; `integration.test_maboss_seed_structure` |
| Epithelial–stromal interface | `tests/mainline/test_interface.py`: coupled compartment networks equal the integrated network for every input assignment and every scenario; per-cell `RegulatoryUnit` API |
| Model integrity and provenance | `tests/mainline/test_model_integrity.py`: dictionary, edge table and network agree; every reference exists, with DOIs matching the corpus; lineage rules match v0.6.0 byte-for-byte; prototype `unit.test_v04_immutability`, `unit.test_line_endings`, implementation-digest checks |
| Committed results stay current | Run manifest binds results to the SHA-256 of model and configuration files; every committed dynamics table ends at the exact fixed point of its rules; figure and animation sidecars bind input digests; `docs/research_foundation_metrics.json` must equal a fresh computation; README dashboard must quote it |
| Prediction freezing | `tests/mainline/test_observations_and_predictions.py`: record contents, immutability, tamper detection, evaluation written once, development-donor leakage refused, a WP2 record without development donors refused, G3 data refused for WP4 selection, unstable predictions not eligible (rule variants, rates and initial conditions), WP2 drafts valid |
| Agreement rules | Concordant, discordant, inconclusive; a no-change needs equivalence |
| Data interfaces | `tests/mainline/test_data_interfaces.py`: pseudonymised identifiers, distinct measurement states, relative deconvolution contributions, WP2 and G3 partitions |
| Closed phases and frozen evidence | Prototype `unit.test_phase2a_contract`, `unit.test_phase2b_contract`, `unit.test_closure_replay` (history-bound) |
| Sensitivity-analysis verification | Rate-sensitivity summary asserts 100% steady-state direction agreement; relay delay positive in every replicate |

Code coverage was not measured.

## Reproducibility infrastructure

- **Environment.** `pixi.lock` pins every package (Python 3.12.13, maboss
  0.8.15, ruff 0.16.0); it is byte-identical to the source commit.
- **Content-addressed provenance.** ENDO-TWIN results carry the SHA-256 of
  their inputs (`endotwin/results/endotwin-v0.3.0/run_manifest.json`). Prototype
  results carry implementation digests and input hashes.
- **Determinism.** Fixed seeds give identical outputs; reported results use
  disjoint seed blocks for replicates.
- **Lint and format.** `pixi run lint` and `pixi run format-check` pass on
  `src/` and `tests/`.
- **Regeneration.** `pixi run endotwin-all` rebuilds every ENDO-TWIN result
  and figure in about 3 minutes.

## How this record was produced

The complete suite was run on a snapshot whose content is identical to the
final commit except for the files that report its outcome: this document,
`README.md`, `docs/verification/endotwin_suite_records.json`, the compressed log
and `docs/research_foundation_metrics.json`. After those files were written,
the mainline tests, lint and format checks were re-run on the final tree
(116 of 116 mainline tests OK; `pixi run test-guards`: 198 guard tests OK, checkout unchanged; `pixi run lint` and `pixi run format-check` pass).
