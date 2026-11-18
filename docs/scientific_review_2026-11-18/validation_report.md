# Validation report — 2026-11-18 scientific review integration

Branch `feat/scientific-review-2026-11-18`.

**The authoritative, machine-readable record of the full suite for the final
commit is `docs/verification/runs/<commit>.json`**, written by
`pixi run run-record` on the committed HEAD of a clean tree; it names the
commit it tested and carries the gzipped log. This document cannot also hold
those numbers for its own commit without circularity — editing it would move
HEAD past the tested commit — so what follows is what was measured, each figure
labelled with the commit it was measured on.

Clean working tree throughout; `git status --porcelain` empty before and after
every command.
Model `adoc-literature-superset-v0.6.0`, `network.bnd` SHA-256
`64b5a3aa02394593bef5991b25005a71a27161ec75aefb6f80dbe7a1e347de27`.

Every number here was produced by a command in this document, on the commit
named beside it.

## Full suite

```
$ pixi run test
```

Measured on **`325fda0`**, clean tree:

| | |
|---|---|
| Exit code | **0** |
| Tests | **2760** |
| Failures | **0** |
| Errors | **0** |
| Skipped | **0** |
| Runtime | **1982.264 s** (33 min) |
| Verdict line | `OK` |

Commits after `325fda0` add tests and change `coverage.py`, so that run does
not cover them. `pixi run run-record` re-runs lint, format-check, test-guards
and the complete serial suite on the final commit and writes the record;
`pixi run check-run-record` passes only if a committed record covers HEAD.

### Where the tests came from

An earlier draft of this section decomposed the rise to 2760 wrongly, and the
error is instructive enough to state rather than quietly replace. It attributed
8 of them to `test_edge_experimental_evidence`; those 8 landed in `957ea09`,
the branch's **first** commit, and were already present at `d65333c`. It also
did not mention that `325fda0` **deleted 9 tests** from
`tests/unit/test_evidence_coverage.py`.

Measured, by counting `def test_` definitions per commit:

| | `d65333c` | `be3fcf8` |
|---|---:|---:|
| Test definitions across `tests/` | **2719** | **2767** |

The difference is **+48**: `test_edge_evidence_summary` +23,
`test_post_closure_adjudications` +21, `test_review_reconciliation` +13,
`test_evidence_coverage` **−9**. The nine removed targeted the deleted
`edge_confidence`/`EDGE_STATES` API; four of them (`TheFilterGuard`) were moved
into `test_edge_evidence_summary.py` and gained a fifth there. No test was
weakened to make anything pass. (Definition counts and executed-test counts
differ — a definition can yield several subtests — so the two columns above are
definitions, and 2760 is an executed count.)

### The previous run, for the record

The 2695-test run that finished `FAILED (failures=3)` was **not** a run of
`d65333c`. It was started mid-integration against an uncommitted working tree,
before `test_evidence_coverage`'s later additions, the clamp tests and the
lineage and ceiling tests existed, so its total is not comparable to either
commit. An earlier draft of this report attributed it to `d65333c`; that was
wrong.

What it does establish is which tests failed, and there were three, not the two
reported at the time:

- `test_closure_replay.LiveDriftTest.test_the_live_tree_differs_from_closure_only_as_declared`
- `test_observation_corrections.CorrectionLayer.test_corrections_file_is_a_declared_post_closure_addition`
- `test_evidence_assertions.RealMigrationTests.test_committed_table_is_what_the_migration_produces`

The third was the serious one and had not been reported: appending `CIT-038`
and `CIT-039` to the frozen registry had silently changed what the **historical**
v0.3.0 migration is recorded as producing, because `dt_adoc.evidence.assertions`
reads the same file. All three pass at `325fda0`.

## Commands run and their exact outcomes

| Command | Outcome |
|---|---|
| `pixi run build-edge-evidence` | **exit 0** — 276 rows, 38 graded, 0 errors; tree clean afterwards (generation is deterministic) |
| `pixi run check-edge-evidence` | **exit 0** — `{"current": true, "errors": []}` |
| `pixi run validate-models` | **exit 0** |
| `pixi run test-guards` | **exit 0** — 238 tests, 1919 subtests, 47 classes |
| `pixi run lint` | **exit 0** — all checks passed |
| `pixi run format-check` | **exit 0** — 274 files already formatted |
| `pixi run test` | **exit 0** — see above |
| `pixi run replay-closed-phases` | **exit 0** — Phase 1B 9 outputs, Phase 2A 8, Phase 2B 1, **all byte for byte** |
| `pixi run harness-check` | **exit 0** — `aih: OK` |
| `python -m dt_adoc.reporting.fixed_point_identities` | **exit 0** — 7 of 7 identities hold, 0 counterexamples |
| `pixi run run-record` | see **Verification record** |

Not run, with reason: **MaBoSS perturbation comparisons**. None of the five
targets in section 7 of the November brief has a registered intervention in
`config/intervention_library.tsv` (four have an executable effect:
`mifepristone`, `anti_spp1`, `hand2_loss`; `xav939` is recorded as
`no_executable_effect`). Registering one runs through the direct-effect
governance in `docs/o8b_direct_effect_governance.md`, not through this
integration. See `dynamic_identifiability.md`.

## Frozen-file integrity

**PASS.**

`config/edge_citation_adjudications.tsv` is byte-identical to the Phase 2B
closure commit `97f88f55ce62e2adca23f631de3ad8e1270ad3e6`, asserted by
`TheFrozenRegistryIsUntouched.test_it_is_byte_identical_to_the_phase2b_closure_commit`.

`closure_replay.undeclared_drift` reports nothing. No exception, category or
allowance was added to the closure checker, and no test was weakened or
skipped. `POST_CLOSURE_FILES` is unchanged.

The two directives live in
`context/evidence/post_closure_citation_adjudications_2026-11-18.tsv`, outside
every path in `CLOSURE_FROZEN_PATHS` (asserted, not assumed:
`test_the_addendum_file_exists_and_is_outside_the_frozen_paths`).

`dt_adoc.evidence.experimental` reads frozen plus addenda through
`load_with_addenda`. `dt_adoc.evidence.assertions` still reads the frozen
registry alone, and a test asserts that its source names neither
`load_with_addenda` nor `POST_CLOSURE_ADJUDICATION_PATHS`.

The combining loader validates each file on its own and then the combination,
since per-file checks cannot see across files. Refused: an id reused between
files, the same citation registered twice, a pair directed both `attach` and
`retract`, an unknown edge, an unknown reference. A missing addendum is not an
error, and the frozen registry loaded with no addenda is equal to what the
original loader returns.

## Citation associations

**Both preserved and correctly generated.**

| | |
|---|---|
| `CIT-038` | `LE018` ← `REF-042` (Lessey 2002), `attach`, in the addendum |
| `CIT-039` | `LE049` ← `REF-016` (Rawlings 2021), `attach`, in the addendum |
| `EVP-LE018-REF042-01` | present, `provisional`, `partial`, `medium`, `seeded:adoc-literature-superset-v0.6.0` |
| `EVP-LE049-REF016-01` | present, `provisional`, `partial`, `medium`, `seeded:adoc-literature-superset-v0.6.0` |
| `EVP-LE049-SOFIASTR001-01` | intact, `ASRT-LE049-SOFIA-STR-001` |

Each seeds exactly one row, and rebuilding preserves grade and lineage.

## Evidence records

| | |
|---|---|
| Rows | **276** |
| Graded | **38** — 16 `medium`, 22 `unsupported` |
| `high` anywhere | **0** |
| `verified` anywhere | **0** |
| Contradictory records anywhere | **0** |
| Publications examined | 21 of 35 |
| Active edges | 89; biological regulatory 63 |
| Biological edges with ≥1 examined record | **26** (8 fully examined, 18 partly) |
| Biological edges with none | **37** (35 whose citations are all unexamined, 2 with no citation) |

These are unchanged from the reviewed integration: the correction moved where
two directives are *stored*, not what the table contains.
`check-edge-evidence` reports `current: true`, so the committed table equals
what `build-edge-evidence` writes.

The reconciliation's 74 rows account as the review expected: 21 already
present, 15 accepted, 2 new citations accepted, 29 retained provisional, 5
requiring verification, 2 conflicting with an existing adjudication.

### A count that was reported two ways

The README and an earlier draft of this report gave **37** and **35** for what
read as the same quantity. They are different quantities. 37 biological edges
have no examined record; of those, 35 have citations none of which has been
examined, and 2 have no citation at all. Both are now stated with their
definition and are computed from the table rather than copied forward.

## Reconciliation

**Corrected.** Domínguez 2010 contributes two experiments to `LE029`, which the
canonical table already separated:

| Review | Experiment | Record | `perturbation_target` |
|---|---|---|---|
| `R1-010` | CD9 gain/loss, Fig. 5A–B | `EVP-LE029-REF008-01` | `CD9` |
| `R1-011` | CD98hc gain/loss, Fig. 5C–D | `EVP-LE029-REF008-02` | `SLC3A2` |

Both carry `independence_group = REF-008`: two rows, one study. Matching is by
the figure panels each side cites, and an ambiguous match is reported as
unmatched rather than resolved by position — position is what produced the
original error.

All 38 mapped assessments resolve to distinct, existing records whose
`edge_id` and `reference_id` match the assessment, and no two assessments
claim the same record. Other repeated edge/reference pairs were inspected:
`LE025`/`REF-031`, `LE030`/`REF-019`, `LE031`/`REF-009` and `LE045`/`REF-029`
each carry two assessments, all held back, so none is mapped.

## Confidence aggregation

**Corrected semantics.** `edge_confidence()` is replaced by
`edge_evidence_summary()`, which emits **no field that is a grade**.

The old function set `contradicted` whenever any examined row carried
`edge_support='contradictory'`. Section 7.1 of `docs/evidence_grading.md` says
otherwise: a contradiction counts only at strength `strong` or `moderate`, its
weight is compared against the base grade, a lighter one downgrades by one
level and flags the edge `contested` rather than overturning it, and every
grade carries a curation-completeness label. Strong positive evidence beside
one weak contradictory observation came out as a contradicted edge.

Implementing 7.1 partially would look like a grade and be read as one, so the
summary is descriptive: coverage (`no_evidence`, `unassessed`,
`partially_examined`, `examined`), curation completeness, supporting pieces
with best provisional confidence, independent group count and whether any is
verified, and each contradiction with its strength, relevance, credibility
against the rubric's bar and the weight it would have carried.

`not_demonstrated_pieces` is a separate field and is never merged into
`contradictions`. A publication silent about a relation is not evidence
against it, and the four states — unsupported citation, unassessed
interaction, citation that does not test the edge, contradiction across
studies — stay distinct.

Tested on synthetic evidence sets covering all ten scenarios the review listed,
because the live table holds 38 graded rows and **no contradiction at all**: a
test written against it would be a test against one thin sample and would pass
whatever the contradiction logic did.

Premature filtering stays refused (`refuse_filter_if_premature`), `all` is
permitted because it asserts nothing, and **no Boolean rule filtering is
implemented** — section 7.2 requires a parsed rule tree, and with no
edge-level grade there is nothing for it to keep.

## Boolean model

**Unchanged.** `network.bnd` SHA-256
`64b5a3aa02394593bef5991b25005a71a27161ec75aefb6f80dbe7a1e347de27`, identical
to the audit's bundled copy and to `main`. `git diff main..HEAD` is empty for
`models/`, `config/protocols.yaml`, `config/protocols_markerless.yaml`,
`config/calibration.yaml` and `config/observation_model_map.tsv`.

Seven of seven fixed-point identities hold, 0 counterexamples, by exhaustive
enumeration over all 65 536 free-variable assignments.

All seven model-change candidates remain proposals. None is implemented, and
the `docs/v05_pause_decision_2026-09-30.md` pause stands.

## Verification record

See `docs/verification/runs/`. `pixi run run-record` re-runs lint,
format-check, test-guards and the complete serial suite on the committed HEAD
of a clean tree and writes the record itself; the record names the commit it
tested. `pixi run check-run-record` passes only if a committed record covers
the code at HEAD.

The earlier record `docs/verification/runs/17122a5f9c89.json` covers `17122a5`
and does not certify this work.

## What a passing suite does not establish

No statement here is evidence of biological correctness. Of 38 graded records,
16 are `medium` and 22 `unsupported`; none is `high` and none is `verified`,
and 37 of 63 active biological regulatory edges have no examined record at
all.

The fixed-point identities are statements about substituted logical functions
at unperturbed fixed points. They are not claims about asynchronous MaBoSS
trajectories, transition rates, transients, hitting times, or any intervention
that clamps an internal node — clamping replaces the substitution the identity
depends on. They are not evidence that the proteins involved are biologically
redundant, and a node this analysis calls observationally silent is
unobservable in this model at steady state, not biologically idle.

## Independent review

The harness gate returned **ESCALATED**, which is not a pass. The broad-sweep
allowance (4 sweeps) had been spent earlier in this session's lineage, so the
corrected state was never swept; the report carries **no open findings**
("every recorded obligation was closed") but records the change as
**unverified**. `aih review --require-independent` will keep failing on it, and
only the owner can run `aih accept`.

Because the gate could not judge the corrections, the repository's stand-in
reviewer was asked to falsify seven specific claims. It could falsify **two**:

- **`coverage.py` dropped half of a rubric definition.** Section 7.1 step 3
  defines a supporting piece by `edge_support` direct/partial **and**
  `overall_confidence` high/medium/low. The filter tested support only, so a
  row with `direct` support and `overall_confidence='unsupported'` — legal,
  because a direct perturbation at `experimental_strength='insufficient'` has
  exactly that ceiling — was reported as support with a "best supporting
  confidence" of `unsupported`, and set `competing_positive_evidence` on an
  edge the rubric says has no positive evidence. No row in the table triggers
  it, which is why it survived. Fixed, with five regression tests.
- **This report's test-count decomposition was wrong**, twice over. Corrected
  above, including the 9 deleted tests it had not mentioned.

Five claims it could not falsify: closure semantics, the post-closure
citations, evidence regeneration, the experiment-level reconciliation, and the
executable model. On the fixed-point module it verified independently that the
56-node network has 16 free variables forming a DAG over them, that 2**16 is
the whole logical state space rather than a sample, and that the mask is
bit-exact against per-state evaluation at all 65 536 states.

A stand-in reviewer is the same model family as the author, so this is weaker
evidence than an independent verdict and it clears nothing.

Its advisories are recorded rather than all acted on. Two were: the
reconciliation now has a currency guard against the audit source it
reconciles, and the figure-panel check now fails if its coverage degrades. The
rest stand as known limitations — `curation_reconciliation.tsv` has no in-repo
generator; the panel parser does not understand `Fig. 4AB` or supplementary
figure numbering (0 occurrences in the current data); and `partition` and
`check_applicability` do not strip whitespace from `reference_id`, which
`validate_rows` catches downstream as a confusing error rather than corrupt
data.

## Carried forward, unresolved

- **The four round-1 retraction candidates** (`LE011`/`REF-010`,
  `LE012`/`REF-010`, `LE019`/`REF-008`) remain `not_demonstrated` evidence rows
  rather than retractions. Not re-raised by this audit; still the owner's
  decision.
- **`MCC-04`** (what `E_MUC1_BARRIER` denotes) blocks `R3-015` and `R3-016`,
  which contradict the standing `CIT-036`/`CIT-037`.
- **`REF-007` on `LE018`** is worth a look next round: `CIT-005`'s own
  rationale says Apparao 2001 applies HB-EGF and blots β3, which is this edge
  rather than the one it was retracted from. The row stays `unreviewed`; no
  grade was invented for it.
- **Section 7.1 aggregation** is unimplemented, deliberately.
