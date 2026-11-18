# Design: two measured performance fixes

Status: **implemented** on `perf/verification-caches` (2026-10-16), with the
correction to the §1 sketch described under "As implemented" below. The design
text is kept as reviewed. Measurements come from the 2026-10-15 verification
audit (baseline `9b9bf5b`). In one instrumented full-suite run of 3,827 s,
`builtins.eval` of rule strings took 1,250 s (32.7 %) and `tomllib.loads` took
603 s (15.8 %). The wrappers add overhead, so read the true combined share as
40–48 %.

Both target files are inside `IMPLEMENTATION_GLOBS`
(`perturbations/engine.py`, `model/*.py`). Each change therefore invalidates
the digest-pinned artifacts and costs one regeneration, so the two should land
together and share **one** regeneration. Done correctly, that regeneration
changes only `implementation_digest`, `git_commit` and `run_settings_sha256`.
Any other difference is a defect in the change.

## 1. Compiled Boolean expressions — `perturbations/engine.py`

**Today.** `_value(expression, assignment)` calls
`eval(expression, {"__builtins__": {}}, assignment)` with the expression as a
*string*, so Python re-parses and re-compiles it on every call. One test made
12.9 M such calls.

**Change.** Compile each distinct expression once and evaluate the code object:

```python
@functools.lru_cache(maxsize=4096)
def _compiled(expression: str) -> types.CodeType:
    return compile(expression, "<rule>", "eval")


def _value(expression: str, assignment: dict[str, bool]) -> bool:
    return bool(eval(_compiled(expression), {"__builtins__": {}}, assignment))
```

* **Cache key:** the exact expression string. Compilation is a pure function of
  that string. The assignment is never part of the key.
* **Invalidation:** none needed. A changed rule is a different string, so it is
  a different key. No file or model state is cached: callers still read and
  render rules exactly as today. `maxsize` bounds memory: each rule text of
  each version is one entry, a few thousand at most.
* **Mutable files / temporary roots:** not applicable. A sandbox that edits a
  rule produces new rule text and therefore a new key, and a stale entry can
  never be returned for it.
* **Safety:** `_evaluable` keeps validating the token set before anything is
  evaluated, and the restricted globals are unchanged. Compiling in `eval`
  mode accepts exactly what `eval` of a string accepts.
* **Measured:** 23.5× faster on all 56 v0.6.0 rules, with identical results over
  2,000 random assignments.

**Equivalence tests required before acceptance:**

1. For every rule of every model version under `models/` (core, literature,
   superset v0.3.0–v0.6.0): exhaustive assignments for rules with ≤ 12 inputs
   and 10,000 seeded random assignments otherwise. Require compiled result ==
   string-`eval` result. The string-`eval` reference is written in the test
   itself, not imported from the engine.
2. A cache-hygiene test: two different expressions sharing a prefix and a
   repeated expression with different assignments each return their own value.
3. The required checks below.

## 2. Repeated TOML parsing — `model/runtime.py`

**Today.** `resolve_model` calls `available_models`, which builds the *whole*
registry: it parses `provenance.toml` for every model directory on every call,
plus once more in `validate_model_runtime_spec`. One integration test parsed
65,637 TOML documents (125 s of its 173 s; MaBoSS took 29 s).

**Change (primary).** Keep every read and cache only the parse:

```python
@functools.lru_cache(maxsize=256)
def _parse_toml(text: str) -> dict[str, object]:
    return tomllib.loads(text)


def _provenance_payload(path: Path) -> dict[str, object]:
    return copy.deepcopy(_parse_toml(path.read_text(encoding="utf-8")))
```

* **Cache key:** the file's *content* (the decoded text), never its path or
  mtime. The file is still opened and read on every call. Only the parse is
  skipped.
* **Invalidation:** automatic. Edited content is a new key, so a sandbox that
  rewrites `provenance.toml` (e.g. `test_v060_marker_removal`'s
  "unparented" case) gets the new payload, and a restored file gets the old
  one. There is no window in which a stale parse can be returned, because the
  key *is* the bytes just read.
* **Mutable results:** callers receive a deep copy, so a caller that mutates a
  payload cannot leak into another call. Copying a few-KB dict is negligible
  next to the parse.
* **Temporary model roots:** unaffected. The key ignores the path, so two roots
  with identical files share one parse, which is correct.
* **File-open behaviour preserved:** `test_v05_u8_stage3_rerank` traces every
  file opened under `models/` and `config/` and compares the set with the
  recorded inputs. Because every file is still read, the opened set is
  unchanged. This is why a path- or mtime-keyed cache, or an in-memory
  registry, is **rejected**: either changes the open pattern, and either can
  return stale data after an in-place edit within the mtime resolution.

**Change (optional, second step).** Make `resolve_model` build only the
requested model rather than the whole registry. This changes which files are
read and how an unknown version is reported, so it is a behaviour change of
its own and is not proposed together with the cache.

**Equivalence tests required before acceptance:**

1. For every committed `provenance.toml`: the cached payload equals
   `tomllib.loads` of the same text, and mutating the returned dict does not
   change a second call's result.
2. In a temporary root: edit `provenance.toml`, resolve, restore, resolve. Each
   resolution reflects the content present at that moment. Repeat the edit and
   restore within one mtime tick, which a path/mtime key would get wrong.
3. Two temporary roots that differ only in one provenance value resolve
   differently.
4. The required checks below.

## Required checks before either change is accepted

* `pixi run test-guards`
* `tests/unit/test_joint_continuation_semantics.py` and
  `tests/integration/test_golden_lineage_v060.py`, both **unchanged**. The
  golden reference must reproduce exactly without re-freezing. A re-freeze in
  the same change would be the rule moving to fit the code.
* the new equivalence tests above;
* the regenerated digest-pinned artifacts differ from their committed versions
  only in `implementation_digest`, `git_commit` and `run_settings_sha256`;
* the complete suite, `pixi run test`, with every directory under `tests/`;
* a re-measurement of the suite runtime, reported against the 3,474 s baseline.
  (As implemented, it is reported against both baselines: see "Measured
  results".)

## As implemented

Both changes follow the design, with one correction to the §1 sketch, which was
**not** exactly equivalent to string `eval`. CPython's `eval` of a string
strips leading spaces and tabs before compiling and names the source
`"<string>"`. `compile(expression, "<rule>", "eval")` does neither, so `"  A"`
would turn from `True` into an `IndentationError`, and a `SyntaxError` would
carry a different filename. `engine._compiled` therefore compiles
`expression.lstrip(" \t")` under `"<string>"`. Only a `str` is cached: any other
object goes to `eval` unchanged, so it is accepted or refused as before.

`runtime._parsed_toml` is the §2 primary change as designed (key: the decoded
text; every call still reads the file; callers receive a deep copy). The
optional resolve-only-the-requested-model step was not done.

`tests/unit/test_cached_primitives_equivalence.py` holds the equivalence tests
listed above. Their uncached references are written in the test. Each of these
deliberately wrong implementations makes it fail: the §1 sketch as written; the
sketch with `"<string>"` but no strip; an unbounded cache; a prefix-keyed
expression cache; caching non-`str` inputs; no copy; a shallow copy; a
path-keyed TOML cache; a path + mtime + size key.

## Measured results (2026-10-16)

Same workstation and Pixi environment, single process. There are two suite
baselines, and both are reported:

* **3,496 s**: the complete-suite run of the merged
  verification-foundation state (2,389 tests, 1 PDF skip). It is the same test
  set as now, minus the 26 added tests, so it is the comparable baseline.
* **3,474 s**: the 2026-10-15 audit run at `9b9bf5b` (2,347 tests), which §
  "Required checks" above names. The suite has grown since, so this comparison
  understates the reduction slightly.

The commands, environment and summaries are in `cache_benchmark_record.json`.
The raw outputs behind both baselines and both runs on this branch are in
`benchmark_raw/` (gzipped, with checksums in the record). The primitive timings come from
`scripts/bench_cached_primitives.py`, run on an extract of `87c56ab` (before)
and on this branch (after).

| | before | after | |
|---|---|---|---|
| `pixi run test` vs the comparable baseline (2,389 → 2,415 tests, 1 PDF skip) | 3,496 s | 1,957.6 s | −44.0 % |
| `pixi run test` vs the audit baseline (2,347 → 2,415 tests) | 3,474 s | 1,957.6 s | −43.6 % |
| `_value`: 130,200 calls over all 651 committed rule rows (72 distinct) | 0.754 s | 0.039 s | 19.4× |
| `_provenance_payload`: 600 reads of all 12 committed `provenance.toml` files | 0.330 s | 0.031 s | 10.5× |
| `resolve_model(v0.6.0)`: 50 calls | 0.403 s | 0.055 s | 7.4× |

Primitive timings are the best of five warm repetitions. The 26 added tests
take about 2.5 s.

The digest moved from `e21c8d3e` to `ca2894bb`, and the five pinned artifacts
were regenerated once, sequentially, from the clean committed implementation
(`a567951`). Their JSON differs from `87c56ab` only in `git_commit`,
`implementation_digest` and, in the endpoint figure metadata,
`run_settings_sha256`, compared leaf by leaf. All eight data and figure files
the generators rewrote are byte-identical: the concordance table, mechanism
nodes, figure source data, the 50-lineage endpoint replicates, the endpoint
figure source data, the KLF12 response table and both PNGs.

The rule corpus is every rule row of every `network.bnd` and `rule_variants.tsv`
under `models/`, generated subvariants included; the provenance corpus is every
`provenance.toml` under `models/`.

The largest remaining cost is the four test modules that import Phase 2B
(`test_phase2b_contract`, `test_closure_replay`, `test_compartment_attribution`,
`test_generated_date_determinism`), which run byte-pinned frozen code. In the
baseline profile they take 1,007.2 s including class fixtures, of which
`test_phase2b_contract` is 957.4 s (773.9 s of tests and 183.5 s of fixtures;
`scripts/summarize_profile_modules.py`). Run alone on this branch they take
1,006.0 s (`benchmark_raw/after_phase2b_modules.log.gz`), so the caches do not
change them, and they are now about 51 % of the 1,957.6 s suite. They can be
scheduled differently but not optimised.
