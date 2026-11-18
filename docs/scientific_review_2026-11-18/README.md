# Integration of the 18 November 2026 independent scientific audit

This directory records what an independent three-round review of DT-ADOC
v0.6.0 proposed, what this repository verified, what it accepted, and what it
refused. It is the audit trail for commit-level changes made elsewhere in the
tree, not a parallel evidence store.

**Nothing in the executable model changed.** `network.bnd` is byte-identical,
and the `docs/v05_pause_decision_2026-09-30.md` pause on biological topology
and de-aliasing stands.

## The audit

| | |
|---|---|
| Archive | `output/review_inbox/2026-11-18/DT_ADOC_scientific_audit_round3.zip` (gitignored) |
| Integrity | 10 of 10 bundled SHA-256 checksums verified; zip CRC clean |
| Assessments | 74 across three rounds (R1 21, R2 32, R3 21) |
| Findings | 15 rows (14 `SCI-*`, 1 `PKG-*`) |
| Proposed new citations | 2 |
| Boolean identities | 7 |

The auditor also supplied its own draft of this directory. It was **not**
adopted as the deliverable — it states the auditor's conclusions, and the point
of this integration is to say which of them survive checking. It is kept intact
as input at `output/review_inbox/2026-11-18/auditor_handoff/`.

### Two reported discrepancies, resolved before anything was edited

The audit names source commit `0c4b2d8` but reports 274 canonical records.
`0c4b2d8` has **273**; `17122a5` has **274**. The audit therefore read the
table as it stands at `17122a5`/HEAD and recorded an earlier commit id. This
matters because it means the audit is *not* stale with respect to the round-1
curation — and indeed it counts those 21 rows separately, as "canonical
provisional piece assessments". No older snapshot was written over anything.

The audit's bundled `model_network_v060.bnd` is byte-identical to the committed
`models/superset/adoc-literature-superset-v0.6.0/network.bnd`: same SHA-256
`64b5a3aa…`, same 4 095 bytes. Audit and repository analysed the same model.

## What was accepted, and on what basis

| Disposition | Count |
|---|---:|
| Already canonical (round 1, commit `17122a5`) | 21 |
| **Accepted into the canonical table this round** | **15** |
| **Proposed new citations adjudicated and accepted** | **2** |
| Retained as provisional reviewer assessment | 29 |
| Requires additional experimental verification | 5 |
| Conflicts with an existing adjudication | 2 |

Row-by-row in `curation_reconciliation.tsv`.

The selection rule is the substance of this integration, so it is stated
plainly. **A reviewer's grade is a proposal, not a finding.** Round 2's
`not_demonstrated` rows all carried the same sentence — "The cited publication
does not experimentally test this exact encoded dependency" — which asserts the
conclusion and shows nothing. Each was therefore re-derived from the
publication's own full text by the method
`config/edge_citation_adjudications.tsv` already uses: resolve both endpoints to
their molecules via `config/node_entity_map.tsv`, then count those molecules and
their printed aliases in the text. The evidence that settled each claim is
written into the canonical row's own `confidence_rationale`, so it can be
rechecked without rerunning anything.

What that produced, concretely: Huyen & Bany 2011 contains **no** fibroblast
growth factor of any kind (`FGF` 0, `fibroblast growth factor` 0), so it cannot
support `S_HAND2 → S_FGF_MITOGENIC`; the only sentence in Stewart 1992 linking
LIF to its receptor is a speculation attributed to a personal communication;
Kurihara 2007's `PGR → IHH` step is carried by an explicit citation to
reference 9, not by an experiment of its own; and Ruan 2026 states in its own
words that hCG acts "prior to its physical contact with the endometrium", which
is the opposite of what `LE024` encodes.

**No positive grade was imported without reading the experiment.** The 29
`partial`/`direct` assessments held back are not doubted — they are simply not
verified here, and importing them would record someone else's reading as this
repository's assessment. Their canonical rows stay `unreviewed` and
`outstanding_checks` says what each still needs.

### The two new citations

Both were read at figure level before being attached, and both are recorded as
`partial` rather than direct:

- **`CIT-038`, REF-042 (Lessey 2002) → `LE018`.** Increasing doses of
  recombinant HB-EGF induce the β3 integrin subunit in primary human
  endometrial epithelium. The audit's caution that this is β3-only was
  **confirmed, not assumed**: counts over the full text give `beta5` 0 and
  `avb5` 0, so two of the composite target's three entities are never measured.
- **`CIT-039`, REF-016 (Rawlings 2021) → `LE049`.** Human assembloids
  decidualized with 8-bromo-cAMP and MPA secrete prolactin, by ELISA.
  `partial` here is forced by the schema, not chosen: `S_DECIDUALIZED` is a
  derived state with no entity, so the hormonal cocktail is the decidualization
  protocol rather than a perturbation of the Boolean source node. This is the
  first publication ever attached to `LE049`.

### What was refused, and why

- **R3-015 and R3-016 (MUC1).** They contradict `CIT-036` and `CIT-037`, which
  already stand and call DeLoia 1998 and Horne 2006 *contradictions* of `LE013`
  rather than silence about it. Both readings are defensible; the difference is
  whether `E_MUC1_BARRIER` denotes abundance or antiadhesive function. Not
  resolvable by re-reading the papers. Recorded as `MCC-04`; owner's decision.
- **R3-007 (Hiraoka stromal `Stat3-sKO`).** The audit is right that a stromal
  knockout does not demonstrate an epithelial edge. Held back anyway, because
  the same paper's epithelial `Stat3-eKO` (R3-006) *does* bear on `LE025` and is
  not yet verified; grading the seeded row `not_demonstrated` alone would report
  the citation as silent about an edge it addresses. Both land together or
  neither does.
- **V2-LE067-REF-009-01.** The audit grades Garrido-Gómez 2012 `not_demonstrated`
  for `LE067` while grading the same ANXA2-siRNA-and-spheroid-adhesion
  experiment `partial` for `LE031`. That inconsistency is unexplained and
  entity counting cannot settle it, since the target is a derived route node.
- **Three assessments whose edges are derived at both ends**, where the
  full-text check has nothing to count.

## The seven Boolean identities

All seven hold. They were re-derived by **exhaustive enumeration over all
65 536 free-variable assignments** using this repository's own network parser —
a decision procedure independent of the audit's SymPy script, which would have
reproduced its own loading or free-variable mistakes perfectly.

Details, assumptions and the explicit list of what the identities do *not*
license: `boolean_identifiability.md`.

## Identifiability of the five audited mechanisms

The structural question is answered exactly; the dynamical one is not, and the
blocker is named rather than worked around. Headline results:

- Clamping `E_CDH1_APICAL` or `E_HBEGF`, in either direction, changes **no
  output in any of the 65 536 states**.
- `S_BMP2` and `S_TAZ_ECM` are visible only on loss, never on gain — they sit
  inside conjunctions, so an overexpression study would read as a null for a
  structural rather than biological reason.
- Every one of the five is an exact alias of other nodes, and **neither of the
  two measured ADOC readouts (`E_PAEP`, `S_IGFBP1`) can discriminate any target
  from its own alias class.**
- MaBoSS transient comparisons were **not** run: none of the five has a
  registered intervention in `config/intervention_library.tsv`, and registering
  one runs through the direct-effect governance rather than being a gap to fill
  in passing.

Details: `dynamic_identifiability.md`.

## Model change candidates

`model_change_candidates.tsv` holds seven proposals, **none implemented**. Each
names affected nodes, the biological issue, supporting and conflicting
publications, the current rule, what would change, expected impact, evidence
strength, observability, identifiability concerns and the approval required.

A proposal in that file is a question for the owner, not an accepted biological
correction.

## Edge-level confidence

Not published, deliberately, and `edge_evidence_summary` emits **no field that
is a grade**. All counts below are computed from the canonical table by
`tests/unit/test_review_reconciliation.py` and
`tests/unit/test_evidence_coverage.py` rather than copied forward.

Of 276 evidence records, **38 are graded** — 16 `medium`, 22 `unsupported`,
**none `high`** and **none `verified`**. Of the 63 active biological regulatory
edges, **26 have at least one examined record** (8 fully examined, 18 partly)
and **37 do not** — 35 whose citations are all still unexamined, and 2 with no
citation at all. (An earlier draft of this file and of the validation report
gave 37 and 35 for what sounded like the same quantity; they are different
quantities, and both are now stated with their definition.)

Section 7.1 of `docs/evidence_grading.md` specifies edge-level aggregation, and
it is not a fold over rows: a contradiction counts only if its strength is
`strong` or `moderate`, its weight is compared against the base grade, a
lighter one downgrades by one level and flags the edge `contested` rather than
overturning it, and every grade carries a curation-completeness label. A
partial implementation of that would look like a grade and be read as one, so
none is published. What `edge_evidence_summary` returns instead is a
description: supporting pieces and their best provisional confidence, how many
independent studies back them, each contradiction with its strength and whether
it clears the rubric's credibility bar, and separately the pieces recording that
a citation does not test the edge at all.

Those last two are never merged. A publication that is silent about a relation
is not evidence against it, and `not_demonstrated_pieces` is a distinct field
from `contradictions` for that reason. As it happens the table currently holds
**no contradictory record at all**, so the contradiction logic is exercised
only by the synthetic evidence sets in
`tests/unit/test_edge_evidence_summary.py` — which is the point of testing it
there rather than against today's distribution.

## Files here

| File | What it is |
|---|---|
| `findings.tsv` | All 15 audit findings with this repository's disposition and what remains outstanding |
| `curation_reconciliation.tsv` | All 74 reviewer records against the canonical table |
| `evidence_coverage.tsv` | Per-edge literature coverage, regenerated (`PKG-01`) |
| `boolean_identifiability.md` | The seven identities, method, assumptions, limits |
| `dynamic_identifiability.md` | Clamp analysis of the five targets; what could not be run |
| `model_change_candidates.tsv` | Seven proposals, none implemented |
| `validation_report.md` | Every check run, with its exact outcome |

Derived artifacts (JSON, clamp table) are under
`output/scientific_review_2026-11-18/`.

## Reproducing

```bash
pixi run build-edge-evidence        # regenerate the canonical table
pixi run check-edge-evidence        # validate it and prove it is current
PYTHONPATH=src pixi run python -B -m dt_adoc.reporting.fixed_point_identities --json
PYTHONPATH=src pixi run python -B -m unittest \
    tests.unit.test_fixed_point_identities tests.unit.test_evidence_coverage
```

## The Phase 2B closure, and how the two citations are registered

`config/edge_citation_adjudications.tsv` is frozen twice over: `closure_replay`
reports any byte change to it, and the historical v0.3.0 generator in
`dt_adoc.evidence.assertions` replays against it. An earlier version of this
integration appended `CIT-038` and `CIT-039` to it directly, which broke both —
it tripped the closure guard, and it silently changed what the *historical*
migration is recorded as producing, because that generator reads the same file.
Three tests failed, not two: `test_closure_replay.LiveDriftTest`,
`test_observation_corrections.CorrectionLayer` and, less obviously,
`test_evidence_assertions.RealMigrationTests`.

The frozen file is now byte-identical to the Phase 2B closure commit
`97f88f55…`, and both directives live in
`context/evidence/post_closure_citation_adjudications_2026-11-18.tsv`, outside
every frozen path. `dt_adoc.evidence.experimental` reads frozen plus addenda via
`load_with_addenda`; `dt_adoc.evidence.assertions` still reads the frozen
registry alone, which is the point — a citation decided in November 2026 is not
part of what the v0.3.0 migration did.

The combining loader validates each file on its own and then the combination,
because the per-file checks cannot see across files: an id reused between
files, the same citation registered twice, and a pair both attached and
retracted are each refused. No exception was added to the closure checker.
`tests/unit/test_post_closure_adjudications.py` holds the boundary from both
sides.
