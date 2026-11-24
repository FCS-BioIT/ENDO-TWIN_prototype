# Verification foundation

What runs when, what each check does and does not establish, and the evidence
that each check works. It is based on the 2026-10-15 verification audit
(baseline `9b9bf5b`). The audit report and its raw measurements are **not**
part of the repository. They are a local archive on the owner's workstation
(`/home/francois/Projects/DT_ADOC_audit/2026-10-15-verification-audit/`), so
that path is not portable. Everything a check here depends on is committed:
`scripts/test_guards.txt`, the runner, the tests and the golden reference.

## The required pre-merge check

`pixi run test`: every directory under `tests/`, including integration and
biological-constraint tests. It is the only complete check.
`unittest discover -s tests/unit` is **not** a substitute: it skips all
integration tests, including every MaBoSS runtime test.

## Run records: the required checks, committed with each PR

`pixi run run-record` runs `lint`, `format-check`, `test-guards` and the
complete serial `test` on the committed `HEAD` of a clean tree (it refuses a
dirty one, and refuses to write if `HEAD` or the tree changed during the run).
It writes `docs/verification/runs/<commit>.json`, with the gzipped test log
beside it, recording each check's exit code and duration, the test, failure and
skip counts with the skip reasons, the environment and the log's SHA-256.
Commit both on the PR branch.

`pixi run check-run-record` passes only if a committed record covers the code
at `HEAD`: its tested commit is `HEAD` or an ancestor with nothing outside
`docs/verification/runs/` changed since, every recorded check exited 0, and the
committed log matches its digest. A code commit after the record makes it fail
until the record is regenerated. It is meant for PR branches; on `main` after a
merge other PRs' changes sit between a record and `HEAD`.

A record attests what was run on the author's machine. It lets a reviewer see
exactly which commit was tested, with what result, without rerunning the suite;
it is not an independent CI result.

## `pixi run test-parallel` — optional, the same suite on two workers

Runs exactly the tests `pixi run test` runs, in two processes: worker A runs
`unit.test_phase2b_contract` and worker B runs every other module. It is not a
replacement for `pixi run test`, which stays the required pre-merge check.
`src/scripts/run_test_parallel.py` describes the checks.

> **The split no longer speeds anything up here, and the rationale behind it is
> no longer true in this repository.** It was chosen because
> `unit.test_phase2b_contract` was the longest module, about 1,000 s, in the
> *prototype*, where its Git history exists. This repository is history-free by
> design (`docs/ORIGIN.md`), so that module skips in about 0.2 s: worker A
> finishes immediately and worker B carries the whole suite. Measured speedup
> today: **1.00x**.
>
> [`module_times.json`](module_times.json) records every module's wall and CPU
> time, measured 2026-11-24. The real critical path is
> `unit.test_v05_u6b_muc1_reconciliation` at **128 s**, which is the floor for
> any split that keeps whole modules together. Ideal packings from that data:
> 2 workers 474 s (2.0x), 4 workers 237 s (4.0x), 8 workers 128 s (7.4x), and
> nothing beyond 8 — the critical path binds. Re-splitting is therefore worth
> doing, and is a deliberate change: `WORKER_A_MODULES` is pinned by
> `unit.test_test_parallel`, so the test moves with it.

* Each worker is started through `pixi run` with inherited activation cleared
  (PATH, CONDA_PREFIX, PIXI_PROJECT_*, PYTHONPATH), its own TMPDIR and the
  repository root as working directory, inside one systemd user scope capped at
  MemoryMax=40G without swap. It refuses to run if its interpreter or `python`
  on PATH is not this checkout's environment. Because PYTHONPATH is cleared, a
  run does not see anything a personal PYTHONPATH adds to `pixi run test`.
* It fails unless both workers discovered the same suite, their shares are
  disjoint and cover it, every test has a structured outcome and passed, both
  workers exited 0 within the timeout (`--timeout`, default 7,200 s), and the
  checkout is unchanged, with no in-process write recorded by either worker.
  On a timeout or a failed launch every started worker is stopped with its
  whole process group.
* "Unchanged" means: every tracked file has the same SHA-256; every other file
  outside `.git/` and `.pixi/` (untracked and ignored ones, including the large
  data objects, which are not hashed) has the same size and mtime; and
  `git status` and the index are the same.
* One skip is accepted, and named in the summary: the cited-PDF check, when
  the gitignored PDFs are absent (a worktree, a fresh clone). Any other skip
  fails the run. Failures that occur only in worktrees fail it as they fail
  `pixi run test`.

Measured on 2026-10-19 at `c549001` in the main checkout
([`parallel_record.json`](parallel_record.json)): 2,440 tests, all passed, in
1,099.7 s against 1,972.5 s for `pixi run test` on the same commit (−44 %),
peak memory 7.9 GB for either. A run of the whole process tree under `strace`
found no write inside the checkout other than git's `.git/index.lock`
(created and removed) and Pixi's task cache. The final runner, at `8e1a3a4`,
passed 2,448 tests in 1,097.5 s.

The checkout check cannot tell who changed the checkout: anything else writing
into it during a run (another session, an editor, a generator) fails the run,
as it did once while another session redrew a figure under `output/`.

## `pixi run test-guards` — integrity and provenance guard

Runs the classes listed in `scripts/test_guards.txt` (47 classes, minus two
excluded commit-reachability tests: 238 tests, about 31 s). It is an integrity and provenance guard. It does
not protect scientific behaviour in general, it does not replace
`pixi run test`, and it is **not** configured as an AIH `checks` command.

It covers the recorded implementation digests, the line-ending inventory,
closed phases and frozen evidence, the PCSK5 correction and its live
consumers, and committed-table regeneration. `scripts/test_guards.txt`
explains its membership and its exclusions: two classes, plus two
commit-reachability tests that fail by construction in a review snapshot of
uncommitted work, because ancestry belongs to the checkout, not to the
artifact. All of them stay in `pixi run test`.

**Execution contract.** The guard's tests must never modify the checkout. The
environment manager is a separate matter and may need somewhere writable to
install its environment.

* **Writable isolated checkout**, including the disposable checkout used for
  AIH deterministic checks: `pixi run test-guards` is the supported entry
  point.
* **Read-only snapshot**: Pixi cannot create `.pixi/` inside an immutable
  checkout. `pixi run test-guards` still works there if Pixi installs its
  environments in a writable location *outside* the checkout. Give it a Pixi
  configuration that sets `detached-environments` and point `PIXI_HOME` at it
  (pixi 0.67.2 reads `$PIXI_HOME/config.toml`; it has no `PIXI_CONFIG_FILE`):

      EXT=$(mktemp -d)
      printf 'detached-environments = "%s/envs"\n' "$EXT" > "$EXT/config.toml"
      PIXI_HOME="$EXT" pixi run --frozen test-guards

  Pixi logs two non-fatal errors: it cannot create its `.pixi/envs` convenience
  symlink. It then runs the task. The packages must be obtainable from Pixi's
  cache or the network. Without that, run the guard directly with an existing,
  pinned interpreter:

      PYTHONDONTWRITEBYTECODE=1 <pixi env>/bin/python -B scripts/run_test_guards.py

  Verified on 2026-10-16 on a pristine snapshot of uncommitted work (no
  `.pixi/`, neither evidence file) in which no directory entry could be
  created. `pixi run --frozen test-guards` exited 0 (238 tests, 1,919
  subtests, 2 excluded). No `.pixi/` was created, `pixi.lock` was unchanged,
  and no file in the checkout was newer than the run.

The runner (`scripts/run_test_guards.py`) fails on any failure, any failing
subtest, any skip, any listed class that does not resolve to tests, and any
change to the checkout. Every tracked file is compared by size and mtime
before and after the run, and an audit hook records in-process writes inside
the checkout. It prints the exact number of tests and subtests executed.

Verified on 2026-10-16:

| Case | Result |
|---|---|
| clean, parentless commit of uncommitted work that no ref carries (the review-snapshot shape), with neither gitignored evidence file | pass: 238 tests, 1,919 subtests, 2 excluded |
| M1: additive edit to `src/dt_adoc/simulation/timeline.py` | fail: 3 tests (the three implementation-digest recomputes) |
| M2: new staged TSV with CRLF | fail: 1 test (CRLF inventory) |
| M3: PCSK5 → PCSK6 in the live corrected observation map | fail: 8 tests |
| M4: one cell of frozen `docs/phase1b_closure/phase1b_exit_gate.tsv` | fail: 3 tests |
| a failure inside a `subTest` only (phase 2A immutability under M4) | fail |
| a test that rewrites a tracked file and restores it | fail: checkout modified |
| a test that creates and deletes an untracked file in `src/` | fail: write recorded |
| a listed class that does not exist | refused before running |
| M5: one probability in `docs/rna_endpoint_concordance/concordance.tsv` | fail: 1 test (table regeneration) |

## Joint continuation: two independent protections

The joint continuation (`maboss_adapter.project_joint_distribution` and
`apply_joint_distribution`) carries every phase of every multi-phase lineage
into the next. Audit mutation M6c moved 1 % of the carried joint mass, and it
passed every test of the adopted model.

* `tests/unit/test_joint_continuation_semantics.py` checks the projection
  against small joint distributions whose results are worked out by hand in
  the test. It covers exact projected probabilities, mass conservation, the
  strict cutoff and renormalisation, preserved correlations, a rare (2⁻⁸)
  state at the production cutoff, invalid input, and the order in which
  forced inputs are applied.
* `tests/integration/test_golden_lineage_v060.py` re-runs four seeded v0.6.0
  lineages through the production chain and requires every node probability
  to equal the frozen reference
  (`tests/fixtures/golden_lineage/v060_continuation_reference.json`) exactly.
  It is a **computational regression reference, not biological validation**.
  Exact equality was established before freezing: separate processes gave
  bit-identical results with `thread_count = 1`, fixed seeds and the pinned
  environment. The test checks the recorded environment and input digests
  first, so a deliberate model change is reported as such. Re-freezing
  (`scripts/freeze_golden_lineage.py`, from committed code only) is a reviewed
  change in its own right. It must never be done to make a failing test pass.

| | semantics test (19) | golden lineage (5) |
|---|---|---|
| frozen baseline | pass | pass (10.7 s) |
| M6c: tilt 1 % of the modal carried state | 11 fail | 4 / 4 cases fail by value (42, 42, 43, 12 nodes moved) |
| M6b: drop carried states below 1 % | 1 fail (rare state) | 2 cases fail by value, 2 raise |

`maboss_adapter.py` is also inside `concordance.simulate.IMPLEMENTATION_GLOBS`,
so the digest-stamped artifacts record its content and the digest tests fail
when it changes. `tests/unit/test_implementation_digest_coverage.py` shows that
an edit to the adapter, including one inside `project_joint_distribution`,
changes the digest and that unrelated files do not. This is provenance only: a
change to the adapter is reported, not judged, and the two tests above remain
the protections of its behaviour.

## The RNA-endpoint figure and its table (audit scenario 5)

M5 changed `maboss_v040_declared_p_on_ht_descriptive` and was caught only by
table regeneration. The figure does not draw that column. Re-rendering after
an edit to each column in turn showed that the figure changes with eight
columns (`model_node`, `compartment`, `observation_type`,
`predicted_cnt_to_ht`, `verdict`, `alias_class`, `alias_class_verdict`, and
the `rna_state_*` calls) and with none of the `maboss_v040_*` probabilities.
So the figure was not stale under M5. `report.md` quotes none of those
probabilities.

A direct source-to-render check already exists:
`Regeneration.test_the_committed_figure_is_drawn_from_the_committed_table`.
It fails, as it should, when a drawn column (`verdict`) changes and the PNG is
left stale. No new dependency was added. The audit's statement that no such
check existed was wrong.

## Not done here

The two production-code optimisations in `cache_design.md` are implemented
(see its "As implemented" section).
Removing Phase 2B from default pre-merge testing, redefining the provenance
fingerprint, deleting tests, parallelising the suite and changing AIH review
policy were not approved and were not done as part of this work. A parallel
runner was approved later and added as the optional `pixi run test-parallel`
(above); `pixi run test` is still serial.
