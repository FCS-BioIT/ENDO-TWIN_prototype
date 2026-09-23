# Correction: provenance coverage was narrower than reported

Dated 2026-07-28. This is a correction note. Earlier audit artifacts are left
as written; nothing is rewritten retrospectively.

## What was claimed, and what was actually true

The provenance migration in commit `8a0f6e4` reported 93 edges covered by 294
assertions, and subsequent increments repeated that as full coverage of the
executable model. That was keyed on `edge_evidence.tsv`.

**It proved coverage of the 93 rows in that table. It did not prove coverage of
the dependencies the executable network computes.** Parsing `network.bnd`
directly gives **96 non-self dependencies**, not 93, and the two sets are not
nested: four dependencies execute with no topology row, and one topology row
describes a relation the model does not compute.

No check in the repository could have detected this, because every validator —
including the assertion migration, the citation harness and the evidence
validators — read the topology table rather than the network. The defect was
found only when the network was parsed independently during the Phase 1
structural audit.

## Adjudication

Each mismatch was adjudicated from the live files, the parent v0.2.0 model and
the surrounding rule structure. Recorded in
`config/topology_parity_exemptions.tsv`.

The decisive observation: **every sibling disjunct or conjunct of the four
undeclared dependencies carries a topology row, and none of the four appears in
the catalog.** They are isolated omissions, not deliberate design.

| pair | category | decision |
|---|---|---|
| `OUT_EPITHELIAL_RECEPTIVE → OUT_MATERNAL_ADHESION_COMPETENCE` | phenotype/logical aggregate | retain, documented exemption — not a molecular edge |
| `E_SECRETORY_STATE → E_ITGAVB3_5` | executing without provenance | retain pending curation; possibly generic pathway completion |
| `IN_E2 → E_ESTROGENIC_PROLIFERATION` | executing without provenance | retain pending curation; hormone driver of a v0.3.0-new node |
| `S_PKA → S_BMP2` | executing without provenance | retain pending curation; cAMP/PKA arm of decidualization |
| `E_RECEPTIVE_SURFACE → OUT_MATERNAL_ADHESION_COMPETENCE` (LE081) | stale row, undocumented migration | retire row, preserve its 8 assertions |

**LE081 and the first row are the same biological claim, migrated.** In v0.2.0
the epithelial permissive contribution entered adhesion competence directly from
`E_RECEPTIVE_SURFACE`. v0.3.0 moved it one level up:
`OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE and E_PAEP`, and the competence
rule now reads the phenotype. The claim survives; the row did not follow. Its 8
assertions must be migrated or explicitly retired, never silently dropped.

No BND dependency was removed. Removing one changes dynamics and requires the
perturbation and convergence gates, which belong to a separate increment.

## Coverage status after this increment

| quantity | value |
|---|---|
| executable BND nodes | 58 |
| non-self BND dependencies | 96 |
| topology rows (`edge_evidence.tsv`) | 93 |
| evidence assertions | 294 |
| dependencies executing without a topology row | 4, all adjudicated and exempted |
| topology rows not executing | 1, adjudicated for retirement |
| dependencies with claim-level verified biological support | **0** — unchanged; no edge has ever been curated at edge level |

## Still outstanding

The exemptions record decisions, not repairs. Three of the four undeclared
dependencies still need topology rows, and LE081 still needs retiring with its
assertions migrated. Both require changing the generator in
`src/dt_adoc/model/superset_family.py` and regenerating the family, since
`edge_evidence.tsv` is generated rather than hand-maintained. That is the next
atomic increment.

## Structural findings retained from Phase 1

Limitations, not necessarily defects:

- The network is a **directed acyclic graph with zero non-trivial strongly
  connected components** — no feedback loops anywhere. Decidualization,
  receptivity and adhesion are described biologically as reciprocal, so this is
  a real modelling limitation. Feedback must only be added through
  evidence-backed curation, never to raise apparent complexity.
- Longest dependency path is **11**; the model is deep but strictly feed-forward.
- **Four weakly connected components**, not one: `IN_XAV939`, `IN_HCG` and
  `IN_EMBRYO_CONDITIONED_SIGNAL` are each isolated.
- **18 self-maintaining or externally clamped nodes**: 13 inputs, the four `X_*`
  structural relays, and `E_KLF12_HIGH`.
- `E_RECEPTIVE_SURFACE` has the largest rule at 13 dependencies.
- Node classes: 13 input, 21 epithelial, 11 stromal, 9 interface, 4 phenotype.

---

# Addendum, 2026-07-28: parity is now generated, not checked

The section above recorded the defect and the adjudication. This addendum records
the repair, and corrects three claims made above. The original text is left as
written.

## Corrections to the section above

1. **"Adding rows requires changing the generator" — superseded.** No evidence row
   was added. Adding rows was the wrong repair: it would have put relations with no
   claim-level support into the curated evidence store, where every coverage counter
   would have absorbed them.
2. **The four undeclared dependencies were called "isolated omissions ... not
   design."** True for the superset, but the framing was too narrow. Parity is
   broken in every model: `adoc-core-v0.1.0` has **12 undeclared and 14 stale**,
   `adoc-literature-v0.2.0` has **2 undeclared**. `S_PKA -> S_BMP2` has been
   unprovenanced since the initial import. The superset is the *best* of the three.
3. **`E_SECRETORY_STATE -> E_ITGAVB3_5` was listed for possible removal.** Removing
   it does not repair anything, and the row should not be read as endorsing removal.
   See PAR-002.

## What was built

`src/dt_adoc/model/topology.py` derives the dependency set and its polarity from
`network.bnd` and reconciles it against `edge_evidence.tsv`. `write_family()` runs
that reconciliation **before it creates or unlinks anything**, so an unadjudicated
mismatch aborts generation with nothing written, and `validate_written()` re-derives
it from the files on disk afterwards.

`edge_evidence.tsv` is **not written by the reconciler** and gained no columns. It
remains purely curated. The reconciliation is a separate generated artifact,
`topology.tsv`.

Architectures considered and rejected:

| option | why rejected |
|---|---|
| auto-derive evidence rows from the rules | makes counts agree by construction; would have silently materialised a covered-looking row for `IN_MIFEPRISTONE -> OUT_MATERNAL_ADHESION_COMPETENCE`. The original defect inverted. |
| co-declare rules with provenance in one structure | the superset inherits 52 of 58 rules from a parent declared `immutable_parent`; would require re-authoring every rule and breaking that contract. |
| hand-maintain both, assert at generation time | cannot bootstrap — it raises on the first write, leaving the family ungenerable until fixed by the same hand-maintenance that caused the drift. |
| add `provenance_status` columns to `edge_evidence.tsv` with synthesized rows | breaks the strongest existing invariant (no row may have an empty `evidence_id`), and five render/runtime consumers would each need to learn a new exclusion rule. |

## Unsupported dependencies carry no assertion

A dependency that executes without curated support gets a `topology.tsv` row with an
empty `edge_id`, **no row in `edge_evidence.tsv`, and no assertion at all.**

Emitting a structural assertion was considered and rejected. Every assertion class
resolves to a source: `bibliographic` to a `reference_id`, `in_house_experiment` to a
`source_observation_id`. An assertion citing nothing would be the only class that
resolves to nothing, and it would enter `assertion_count` and `edges_with_assertions`
— making an unsupported edge look evidenced at exactly the granularity where the
claim lives. Absence of provenance is represented by absence from the evidence store
and made visible in the topology store. This also leaves the `validate_assertions()`
interlock — every evidence row must have an assertion — at full strength, instead of
relaxing it.

## Polarity is derived and cross-checked

`derived_sign` comes from a recursive-descent parse with negation propagated down
the tree. It agrees with **all 224 curated signs across all three models**, with
zero ambiguous edges, including `X_MECHANICAL_PERMISSIVE_ECM`, which negates a
parenthesised group and defeats a token-local heuristic. The generator now fails if
a curated sign contradicts how the rule uses the token — a check that did not
previously exist in either direction.

## Counts

| quantity | value |
|---|---|
| executable BND nodes | 58 |
| non-self BND dependencies | 96 |
| relations in `topology.tsv` | 97 |
| **active** (= the 96 dependencies) | **96** |
| — `declared` (curated provenance) | **92** |
| — `unprovenanced` | 3 (PAR-002, PAR-003, PAR-004) |
| — `logical_aggregate` | 1 (PAR-001) |
| **retired** (history, excluded from coverage) | **1** (LE081, PAR-005, 8 assertions kept) |
| curated `edge_evidence.tsv` rows | 93, unchanged |
| assertions | 294, unchanged |
| **relations with claim-level verified biological support** | **0**, unchanged |

Coverage is **92 declared of 96 active**. It must never be collapsed to one number,
and must never be conflated with curated depth, which is zero.

## Effective evidence depth is 42, not 294

The 294 assertions are a mechanical fan-out, not 294 curation decisions.
`migrate_edge_evidence()` splits each evidence id's reference list and emits one row
per reference per edge. `LIT-LIF-001` lists eight references and is cited by six
edges, so it produces 48 byte-identical rows across LE007, LE008, LE025, LE076,
LE081 and LE091. Those are six *different* relations — ligand induction, receptor
engagement, surface remodelling, phenotype projection, and in LE091's case an
**inhibition**. The same eight papers cannot support "secretory state induces LIF"
and "KLF12-high restrains LIF" at claim level. `LIT-SPP1-001` spans 12 edges,
`LIT-IHH-001` 11, `LIT-BARRIER-001` 11.

Distinct `(evidence_id, cited paper)` pairs: **44**.

**Correction, 2026-07-29.** This section originally said 42 and claimed the figure
"reproduces exactly". It was 42 before this same commit's citation adjudications, which
retracted 22 citations *and attached 2* (`REF-042` to `LE015`, `REF-037` to `LE091`). The
addendum failed to count its own attachments. The live value is 44. The unit is the pair of an
evidence id and one bibliographic or in-house source it cites -- not the edge's
source node, which gives 67 and is a different question. Reporting that quotes 294
without this qualification overstates evidence depth roughly sevenfold. The upside:
the curation backlog is 42 decisions, not 294.

## No rule was changed

Five reformulations were evaluated against the full protocol suite at a converged
horizon (10^5 trajectories, two seeds) **and** by exhaustive enumeration of all
2^18 = 262,144 input assignments. All were rejected or deferred.

| candidate | result | decision |
|---|---|---|
| drop `E_SECRETORY_STATE` from `E_ITGAVB3_5` | fixed points identical everywhere | rejected — does not repair the collapse, since `E_HBEGF` is identically `E_SECRETORY_STATE` |
| drop `IN_E2` from `E_ESTROGENIC_PROLIFERATION` | differs on that node in 37.5% of assignments | rejected — asserts oestrogen-driven proliferation with no oestrogen |
| drop the redundant `S_FGF_MITOGENIC` conjunct | identical | deferred to the FGF increment |
| drop `S_PKA` from `S_BMP2` | identical | rejected — annotate instead; see PAR-004 |
| competence reads `E_RECEPTIVE_SURFACE` | identical | rejected — inert, and narrows the perturbation surface |

`network.bnd`, `baseline.cfg`, all 18 `conditions/*.cfg`, `node_dictionary.tsv`,
`edge_evidence.tsv`, `edge_evidence_assertions.tsv` and `phenotype_contract.tsv` are
**byte-identical** after regeneration. OM-001, OM-002, the held-out mifepristone
response and the perturbation ordering are untouched because no rule moved.

## Structural findings that outrank the parity defect

Recorded as limitations, not coding errors, and not addressed here.

**Six logical identity classes collapse the network.** Verified exhaustively:

- `E_PGR` and `S_PGR` are **literally the same expression**
  (`IN_PROGESTIN and not IN_MIFEPRISTONE`). Therefore `E_IHH`, `S_NR2F2`, `S_BMP2`
  and `S_HAND2` all reduce to `S_PGR`, and the model's cross-compartment
  IHH -> NR2F2 -> BMP2 -> HAND2 relay computes nothing beyond progestin
  availability. The "cross-compartment" bridge crosses nothing.
- `E_ITGAVB3_5`, `E_PAEP`, `E_HBEGF`, `E_SPP1_EXPR`, `E_MUC1_SLEX`,
  `E_DAG1_CLEAVED` and `E_ANXA2_ACTIN` all reduce to `E_SECRETORY_STATE`.
- `S_FGF_MITOGENIC` is a pure alias of `not S_HAND2`, so
  `E_ESTROGENIC_PROLIFERATION` is `IN_E2 and not S_HAND2` and its two separately
  curated edges encode one constraint.

**15 of 58 nodes (26%) are fully inert** — clamping them ON or OFF cannot change any
`OUT_*` phenotype in any of the 262,144 states. A further 14 clamp-directions are
one-way inert. Of a nominal 116 single-node interventions, **38% are provably
silent**. `IN_XAV939`, `IN_HCG` and `IN_EMBRYO_CONDITIONED_SIGNAL` are declared
inputs with no consumer in this model.

The network is a DAG with **zero non-trivial strongly connected components** — no
feedback anywhere — against biology that is described as reciprocal. Feedback must
only be added through evidence-backed curation, never to raise apparent complexity.

Highest-value structural fix, ahead of any further curation: **break
`S_NR2F2` = `S_PGR`**, which is what makes five nodes restate progestin status and
what makes `S_PKA -> S_BMP2` untestable.

## Not fixed here, deliberately

- **Parent models.** `adoc-core-v0.1.0` (12 undeclared / 14 stale) and
  `adoc-literature-v0.2.0` (2 undeclared) are declared `immutable_parent`. Their
  drift is now pinned by test so it can shrink but never grow. Twenty of the 26
  baseline mismatches are 13 refactor pairs from a documented Phase 1B rule
  compaction whose pre-compaction rules survive in
  `context/references/adoc-maboss-model-specification.user-provided.md`; the rows
  are an accurate record of it and must be retired, not deleted. `S_FOXO1` is
  computed and read by nothing.
- **`models/superset/.../generated/*/edge_evidence.tsv`.** Not a parity defect. These
  are candidate-mapping tables with a different schema (`SUPEDGE-*` ids,
  `mapping_type`), hand-committed and generated by nothing. Applying parity to them
  would be a category error. Recorded so a later audit does not "fix" them.
- **REF-027's empty PMID** (verified value 17515606). Not spot-fixed: **23 of 40
  references have an empty `pmid`** and all 40 have a DOI, so the column is sparse
  by construction. Populate all 23, then add a guard — in that order.
- **`adoc-literature-v0.2.0`'s recorded parent hashes do not reproduce**
  (`807bf0df…`/`44830c85…` recorded, `080e2a43…`/`53bc5621…` actual). No test
  verifies them. Separate defect.
- **The FGF reformulation.** Routing E2 through the stromal relay is supported by
  four verified mouse papers and would add a perturbable target, but it changes
  Boolean logic and retires LE094 with 6 assertions. Out of scope for a parity
  repair; needs its own increment with transient validation.

---

# Addendum, 2026-07-29: citations adjudicated per relation

## The defect

`context/evidence-register.tsv` keys its bibliography by *topic*, and
`migrate_edge_evidence()` fanned a topic's whole `location` list onto every edge
citing it. A topic is not a citation unit. `LIT-SPP1-001` lists five references
and is cited by twelve edges, so Apparao 2001 and Fazleabas 1997 — **neither of
which contains the string "LIF"** — were asserted as supporting `LE017`
(`E_LIF -> E_ITGAVB3_5`). The register could not fix this, because `LE017` and
`LE018` cite the same topic and need different subsets of it.

## What was repaired

`config/edge_citation_adjudications.tsv` supplies the missing
`(edge_id, reference_id)` granularity as dated data, mirroring the
`topology_parity_exemptions.tsv` idiom: rationale, date, and staleness detection
in both directions. It never edits `edge_evidence.tsv` or the `immutable_parent`
it inherits from — `LE015` and `LE017` are parent rows and were repaired without
touching the parent.

| edge | before | after | basis |
|---|---|---|---|
| `LE017` | REF-007, 015, 017, 022, 038 | **REF-038** | Apparao and Fazleabas contain zero occurrences of "LIF" |
| `LE015` | REF-006, 007 | **REF-006, REF-042** | Apparao applies HB-EGF as a *treatment* and never measures its regulation; Lessey 2002 is the regulation study |
| `LE091` | 8 references | **REF-037** | none of the eight concerned KLF12; REF-037 (Huang 2018) was orphaned |
| 9 barrier edges | + REF-011 | REF-011 removed | α-dystroglycan is wrong for PODXL and MUC1 edges |

**22 citations retracted, 2 attached. 294 → 274 assertions.**

## A retraction may not rest on metadata

`basis` has **no metadata-only value**. A scope mismatch inferred from a title
and abstract can be recorded as a suspicion but can never delete a citation.
That is the enforced form of the distinction between a *confirmed* and a merely
*probable* misattribution: the audit's 105 suspected cases are structurally
unable to remove anything.

## Refutations of the audit, found on re-verification

The audit was re-checked against full text before action, and was wrong in four
places. All four were corrected before implementing.

- **REF-011 supports 2 of the 11 barrier edges, not 0.** `LE075` and `LE086`
  aggregate `X_ANTIADHESIVE_ROUTE`, whose rule contains `E_DAG1_FULL` — sourced
  entirely to REF-011. It is retained there and on all seven `LIT-PC6-001` edges.
- **Apparao does contain ligand-side loss-of-function for `LE059`.** Fig. 6
  plots `ΔRGD-GST-OPN` at ~4% of control, asterisked. The prose reports it as
  "data not shown"; it is visible only in the rendered figure. This is the
  second time in this project that a figure-only result overturned a
  prose-based reading — the first was Chung's Fig. 3.
- **"Fazleabas has no perturbation" is false.** It has an ovariectomised
  steroid-replacement arm. The `LE059` verdict survives; the stated reason did not.
- **The list enumerated 22 assertions, not 24**, and missed
  `ASRT-LE062-REF-038`.

## `LE059` and `IN_ANTI_SPP1`

`IN_ANTI_SPP1` is a **purely in-silico construct**. No anti-SPP1 arm exists in
the ADOC wet-lab protocol set, and `SOFIA-CCC-002` is an scRNA-seq pathway
interpretation, not a perturbation. Four other inputs are likewise synthetic, so
requiring inputs to be experimentally established is not this project's rule.

Classification: **retained as an unvalidated mechanistic prediction**, re-based
onto the ΔRGD ligand-mutant result rather than the anti-OPN antibody claim —
Apparao's two anti-OPN antibodies are detection reagents and were never used to
neutralise. No neutralising-antibody experiment in endometrial adhesion was
located. Any simulation output under this input is a prediction and must not be
presented as validated.

## Evidence coverage

The "42 distinct curation units" figure was challenged as unreproducible during
review. It reproduces exactly — under the intended reading. The word "source"
was ambiguous between *cited paper* (42) and *edge source node* (67), and a
reviewer computing the second concluded the first was wrong. The number stands;
the **label** was defective and is now `(evidence id, cited paper)`.

Coverage remains reported as raw counts. The only percentage this project
publishes is topology coverage, **92 declared / 96 active**, defined in
`dt_adoc.model.topology.coverage_counts`. Relations with claim-level verified
biological support: **still 0**.

## Not done in this increment

`network.bnd` untouched; no rule changed; no integrin decomposition. The
proposed decomposition (`E_ITGAV` / `E_ITGB3` / `E_ITGB5` / heterodimers, with
`E_HOXA10` as an external boundary) is recorded as a candidate, not settled —
separate LIFR and HOXA10 necessity experiments do not jointly prove ITGB3
requires both, defaulting HOXA10 to TRUE is a modelling assumption, and
fixed-point equivalence at that default does not establish transient
equivalence. The triage columns, the 20 modelling-construct reclassifications
and `tested_no_effect` are designed but not landed.
