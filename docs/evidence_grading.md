# Experimental evidence curation and confidence grading

This document is the rubric and the decision rules for the per-experiment
evidence table. What exists in this change:

| Artifact | Role | Written by |
| --- | --- | --- |
| `context/evidence/edge_experimental_evidence.tsv` | **Canonical.** One row per independent experimental evidence piece for one regulatory edge | curators; regenerated (merge, never overwrite) by `pixi run build-edge-evidence` |
| `context/evidence/edge_roles.tsv` | Role of every executable dependency (biological, external input, phenotype definition, structural relay) | curators |
| `src/dt_adoc/evidence/experimental.py` | Edge context, migration seeds, merge-regeneration, validation, currentness check | - |

**State.** 21 of the 274 rows are graded, all `curation_status = provisional`,
from the first independent audit of the evidence handoff (2026-11-16); they
cover 16 active edges and one retired one across 12 publications. The remaining
253 rows are migrated paper-level citations with `curation_status = unreviewed`:
not examined, no grade. A `not_demonstrated` row says *that citation* does not
test *that* edge — never that the interaction is false, and never that the edge
is unsupported across the literature, most of which is still unreviewed. The
edge-level summary, the coverage report and the confidence-filtered networks are
specified in section 7 but **not implemented**; no command for them exists, and
filtering on the present coverage would read unreviewed edges as unsupported.

Claim boundary. A grade says how well the *encoded Boolean relation* is supported
by the experiments recorded so far. It is not a probability and it is not a
clinical statement.

## 1. Which edges exist

`network.bnd` decides. `dt_adoc.evidence.experimental.edge_context` parses every
rule with `dt_adoc.model.topology` (recursive descent, negation propagated), so
the active set is the set of `(source, target)` dependencies the rules compute.
That set is reconciled against the version's committed `topology.tsv` and the
build fails on any disagreement. `edge_id` is the curated `LE*` id; an active
dependency without one keeps its topology exemption id (`PAR-*`), so it still has
a stable key and is still counted.

Retired edges (`provenance_status = retired` in `topology.tsv`, for example the
intervention-marker edges LE002, LE038, LE059, LE096 removed in v0.6.0) keep
their rows in the canonical table as history with `edge_status = retired` and
are excluded from active coverage.

Generated columns (`edge_id` through `model_version`, `publication`, `doi`) are
recomputed on every build from the model version, `edge_roles.tsv` and
`references.tsv`. Validation recomputes them too and rejects any cell that
differs, so a stale or hand-edited generated cell cannot pass.

## 2. Edge roles

| Role | Meaning | Intended treatment by a confidence filter (section 7, not implemented) |
| --- | --- | --- |
| `biological_regulatory` | A regulatory claim between two modelled biological entities, including membership of a molecule in an adhesion route | filtered |
| `external_input` | An experimental, environmental or embryo-side input acting on the maternal model (`IN_*` sources) | retained by default, optionally filtered |
| `phenotype_definition` | An edge that *defines* a reported phenotype or route aggregate from its constituents (`OUT_*` targets, `E_RECEPTIVE_SURFACE` gating a route) | never filtered |
| `structural_relay` | A bounded structural-uncertainty relay (`X_*_RELAY` sources) | never filtered |

Roles are curated in `context/evidence/edge_roles.tsv` with a rationale per row;
validation requires exactly one role for every active edge and none for anything
else. Two edges carrying the *same* biological claim are both biological:
CD98/CD9 feeding `E_RECEPTIVE_SURFACE` (LE029) and feeding
`X_ADHESION_ROUTE_REDUNDANT` (LE065) is one claim implemented twice, so neither
may be classed structural. Otherwise excluding LE029 while retaining LE065
would silently reintroduce the excluded dependency.

## 3. Per-piece axes

Each evidence piece is graded on three **separate** axes. A strong experiment is
not strong evidence for a rule it does not test.

### 3.1 `experimental_strength`, the experiment as an experiment

| Value | Criteria |
| --- | --- |
| `strong` | Direct perturbation of the proposed regulator (genetic loss, gain, or pharmacology) with appropriate controls **and** a specificity check: rescue, two independent reagents, gain *and* loss, or an orthogonal method. Quantitative (or semi-quantitative) readout, with biological replication reported as a count of two or more |
| `moderate` | One perturbation modality with appropriate negative controls but no specificity check; or a well-controlled molecular experiment (ChIP, reporter, binding) without functional perturbation; or a perturbation whose controls are incompletely reported |
| `weak` | Expression association, cycle-phase or time-course correlation, co-localisation, enrichment, computational inference, or a single uncontrolled experiment |
| `insufficient` | The cited source contains no data bearing on this edge, or the data cannot be evaluated |

A rescue is valuable but not mandatory for `strong`; any one of the listed
specificity checks suffices.

### 3.2 `human_ADOC_relevance`, applicability to the human ADOC compartment

| Value | Criteria |
| --- | --- |
| `direct` | Human, donor-derived primary endometrial cells, organoids or tissue of the compartment the edge is encoded in, or the ADOC itself, or in-vivo human endometrium |
| `close` | Human endometrial cells that are immortalised but not cancer-derived (for example hTERT-immortalised stromal lines); or primary human endometrium of a different compartment than encoded; or a heterologous assay whose maternal side would otherwise be `direct` (human cells with a mouse blastocyst or a trophoblast cell-line spheroid) |
| `indirect` | Human cancer-derived endometrial lines (Ishikawa, ECC-1, RL95-2, HEC-1A/B); or non-human in-vivo or primary uterine tissue (mouse, rat, baboon) |
| `poor` | Non-endometrial cells or tissue (HeLa, HEK293, placental or gestational fibroblasts used for an endometrial claim) |
| `unknown` | The system could not be resolved from the Methods |

The species of every relevant compartment is recorded in `species`
(`maternal: human; embryo: mouse`), never collapsed into one organism. Each
entry is `<organism>` or `<compartment>: <organism>`, and the organism comes
from a closed list (`human`, `mouse`, `rat`, `rabbit`, `guinea_pig`, `baboon`,
`macaque`, `bovine`, `porcine`, `ovine`, `other_nonhuman`, `not_applicable`;
an unlisted animal is `other_nonhuman`, named in `model_details`). Validation
enforces the species side of this table: `direct` requires every entry to be
`human`; `close` requires at least one `human` entry; cancer-derived cells
cannot be `direct` or `close`; immortalised cells cannot be `direct`. An
unlisted organism is an error, so it cannot pass as human.

### 3.3 `edge_support`, what the result says about the encoded relation

| Value | Criteria |
| --- | --- |
| `direct` | The regulator itself was perturbed and the encoded target responded in the encoded direction, at the level the node represents |
| `partial` | Supports the direction but only for one member of a composite node (one FGF of `S_FGF_MITOGENIC`, CD98 but not CD9), or the readout is downstream of the target without the intermediate, or the regulator is a proxy (hormone rather than the receptor node) |
| `contradictory` | The result shows the opposite direction, or no effect where the rule requires one, under conditions the rule claims to cover |
| `not_demonstrated` | The source was examined and does not test this relation (descriptive co-expression only, wrong node, wrong compartment) |

## 4. Per-piece overall confidence and its ceiling

The curator assigns `overall_confidence`. The validator holds it at or below the
ceiling the three axes allow, so it can never be inflated past what they
record. Lowering it below the ceiling is allowed and must be explained in
`limitations_rationale`.

| Ceiling | Requires all of |
| --- | --- |
| `high` | strength `strong`; relevance `direct`; support `direct` |
| `medium` | strength `strong` or `moderate`; relevance `direct`, `close` or `indirect`; support `direct` or `partial` |
| `low` | strength `strong`, `moderate` or `weak`; support `direct` or `partial` (any relevance) |
| `unsupported` | otherwise: support `contradictory` or `not_demonstrated`, or strength `insufficient` |

Consequences, stated because they are easy to miss:

* Mouse knockout evidence tops out at `medium`: its relevance is at most
  `indirect`.
* A well-controlled cancer cell-line experiment tops out at `medium`.
* A human primary experiment that supports one member of a composite node tops
  out at `medium` (`partial`).
* Correlation, enrichment and computational inference top out at `low`.
* `primary_mechanistic` in `references.tsv` is a paper label and promotes
  nothing; only the recorded experiment does.

### Mandatory text

Every examined row (`curation_status` not `unreviewed`) carries:

* `confidence_rationale`: why the grade is what it is, naming the experiment.
* `limitations_rationale`: **what prevents a higher grade**, concretely (for
  example "no perturbation of KLF12 itself; only LIF was measured", "Ishikawa
  only, no primary confirmation", "supports FGF9, not the FGF family encoded").
  For a `high` piece it names the residual limitation.

Generic statements ("limited evidence", "needs more work") are not
acceptable.

## 5. Curation status and source verification

| `curation_status` | Meaning |
| --- | --- |
| `verified` | The figure, table or panel was read in the full text and the extracted fields were checked against it. Requires `source_verification = full_text_verified` and a non-empty `source_location` |
| `provisional` | Graded from incomplete access (abstract, secondary summary, partial text) or awaiting a second check. Capped at `low` when the full text was not read |
| `unreviewed` | Citation recorded, experiment not yet examined. All assessment fields are `unassessed` |
| `disputed` | Examined; curators or sources disagree; the disagreement is written in the rationale |

When the full text cannot be obtained, the citation stays,
`source_verification = unavailable`, and the row stays `unreviewed`: an
unresolved assessment is never converted into a grade. Experimental details,
replicate counts, figure numbers and controls are written only when the source
states them. Otherwise the field says `not_reported` (source examined, detail
absent) or `not_examined`.

An examined row fills every descriptive cell (`cell_type`, `perturbation`,
`perturbation_target`, `measured_effect`, `functional_endpoint`, `controls`,
`biological_replicates`, `experimental_limitations`). Missingness is written as
`not_reported`, never left blank, so "the source does not state it" is
distinguishable from "nobody filled it in". A cell that asserts nothing
(`none`, `n/a`, `-`, with or without punctuation) does not count as reported
where the rubric requires something reported.

The prerequisites of section 3 are enforced, not merely described.

**`edge_support = direct`** requires an `experiment_type` that perturbs the
regulator *and* a `perturbation_target` that is the edge's own source:

* one of the source node's entities in `config/node_entity_map.tsv` (so
  `E_KLF12_HIGH` is perturbed through `KLF12`);
* or the source node id itself, but only for an `external_input` edge, where
  the input node *is* the manipulation (`IN_PROGESTIN`);
* a source with no declared entity is a derived state — nothing in a laboratory
  is that node — so `direct` is unavailable for it and evidence through a proxy
  is `partial`. `E_SECRETORY_STATE`, `S_DECIDUALIZED` and the route aggregates
  are in this class.

Naming the regulator is what separates evidence for *this* relation from a
proxy (progesterone standing in for PGR) or from an experiment on something
else entirely.

**`experimental_strength = strong`** requires all of: a perturbation of the
regulator, reported controls, a quantitative or semi-quantitative readout
(`readout_quantitation`), reported biological replication of two or more, and
one of the four specificity routes the rubric lists — `rescue`,
`two_independent_reagents`, `gain_and_loss` or `orthogonal_method`. All four
are first-class values of `rescue_experiment`; two independent reagents is a
specificity check in its own right and needs no rescue on top.

**Direction.** An edge carries a sign, so support for it is a claim about two
directions at once: `perturbation_direction` (which way the regulator was
moved) and `response_direction` (which way the target went). An activation edge
claims they move together; an inhibition edge claims they move oppositely. When
both are recorded, the pattern is checked against the edge's own sign, so
lowering KLF12 and seeing *less* LIF cannot be recorded as support for
`E_KLF12_HIGH ⊣ E_LIF` — that result opposes the edge. A `no_change` response
supports no direction and belongs under `contradictory`; a contradiction whose
directions agree with the edge is refused as well.

Observational rows record `not_applicable` and are not forced to invent a
direction. A row that names a perturbational `experiment_type` has no such
exit: both fields must be concrete (`increase`/`decrease`, and `no_change` for
the response). `not_applicable` and `not_examined` both mean "no direction
recorded", so allowing either on a perturbational row would let a knockdown
opt out of the sign check altogether.

`edge_support = not_demonstrated` is the one exception, and the only one. That
value records that the source does not test this relation, which is usually
because the encoded target was never measured — a paper that raises LIF and
assays integrins but never GP130 or phospho-STAT3, or one that silences PC5/6
and never assays dystroglycan. Both fields may then be `not_examined` or
`not_applicable`, because writing a direction would mean writing a measurement
that does not exist. Nothing is bought with the exemption: `not_demonstrated`
pins `overall_confidence` to `unsupported`, and `contradictory` — the grade
that rests entirely on direction — must still state both.

**`experimental_strength = strong` is checked whatever the support grade.** A
strong experiment on a different molecule is not strong evidence for *this*
relation, so the `perturbation_target` rule applies to `strong` rows even when
their support is `partial`.

**Observation cannot exceed `weak`.** If every `experiment_type` of a row only
observes — expression profiling, RNA-seq, single-cell RNA-seq, immunostaining,
western blot, ELISA, computational inference, a review statement — the row
cannot be `moderate` or `strong`. The controlled molecular experiments the
rubric does allow at `moderate` (ChIP, reporter, binding) are deliberately not
in that set.

**The system must be internally coherent.** `experimental_model` and
`cell_source` describe the same cells, so a row that declares a single model,
`cell_line`, and sources it as `donor_derived_primary` is refused, as is a
cancer or immortalised source without a line model. `direct` relevance
additionally requires a donor-derived system — primary culture, organoid,
assembloid, explant, section or in vivo — and never a line.

Both columns are multi-valued because the systems in this literature often have
several parts: a cancer line co-cultured with primary trophoblast spheroids, or
donor-tissue immunostaining followed by an adhesion assay in Ishikawa cells. A
row that names more than one `experimental_model` is describing more than one
population, so `cell_line` beside `donor_derived_primary` is accepted there and
each part is recorded instead of one of them being deleted to satisfy the
check. This opens no route upward: `direct` requires *every* declared model to
be donor-derived, and a `cancer_derived` or `immortalized_primary_like` source
bars both `direct` and `close` on its own.

**Mandatory text may not be a null in disguise.** `source_location`,
`confidence_rationale`, `limitations_rationale` and `curated_on` are rejected
when blank *and* when they say `none`, `N/A` or `not_reported`: those read as
filled in and carry no traceability.

**Contradictions are not held to the `perturbation_target` rule.** Section 3.3
defines `contradictory` by the result opposing the rule — the opposite
direction, or no effect where the rule requires one — not by what was
perturbed. Meseguer 2001 contradicts `E_SECRETORY_STATE ⊣ E_MUC1_BARRIER` by
hormone treatment in vivo, and that source is derived, so requiring a named
regulator would reject a real contradiction the corpus already holds. A
contradiction's weight is still capped by the same strength and relevance
ceiling as support.

A citation retracted from an edge in `config/edge_citation_adjudications.tsv`
may be recorded on that edge only as `not_demonstrated`. The recorded bases for
a retraction are that the node is absent from the full text or that the study is
out of scope, and neither supports *or* opposes the relation; a contradiction
weighs as heavily as support in the edge-level rule, so letting a retracted
source contradict would reintroduce it through the other side.

**Lineage.** `migrated_from` records where a row came from. Validation checks it
against the computed seed set, not against its shape: every seed must be present
under its own `evidence_piece_id` carrying its own lineage, and a row that is
not a seed must leave `migrated_from` empty. The two forms a seed may carry
are:

* `ASRT-<edge>-<source>`: the paper-level assertion of
  `models/superset/adoc-literature-superset-v0.3.0/edge_evidence_assertions.tsv`
  this seed was migrated from. It must exist in that table and name the row's
  own edge and source;
* `seeded:<model version>`: a seed for an edge the v0.3.0 table never had
  (LE096, added in v0.4.0), taken from that version's `edge_evidence.tsv` and
  the evidence register;
* empty, on every row that is not a seed: a second experiment from the same
  paper, or a source outside the register's topic set.

Seeds are the v0.3.0 migration applied to the target version: the register's
topic fan-out, minus every retraction and plus every attachment in
`config/edge_citation_adjudications.tsv`. A retracted citation is never
re-seeded. A seed is restored under its exact id, so a curator's second row for
the same paper (`-02`) never stands in for the migrated row (`-01`) and its
lineage cannot be lost that way.

## 6. Independence

`independence_group` defaults to the reference id. Pieces sharing a group are
not independent replications. The curator assigns one group across references
when they report the same cohort or dataset. Several systems within one paper
are separate pieces (separate rows) but one study for replication counting, and
validation enforces that direction: every row of one reference carries the same
group, so a single paper cannot promote an edge by appearing twice. The
converse, two references sharing a group, is what the column is for and stays
allowed.

## 7. Specification for later stages (not implemented)

Nothing in this section exists as code, artifact or command yet. It records the
rules the next stages are to implement, so that curation can be done against
them now. They are design decisions that have not been reviewed by the owner.

### 7.1 Edge-level aggregation (to be computed, never hand-maintained)

Edge-level grades are to exist in one place, a derived summary with one row per
active edge, computed by applying these rules in order. Only rows whose
`curation_status` is not `unreviewed` count as examined.

1. **No row** for the edge: `unassessed` ("no evidence recorded").
2. **Only unreviewed rows**: `unassessed` ("N citations recorded, none
   examined").
3. Supporting pieces are examined rows with `edge_support` `direct` or `partial`
   and `overall_confidence` `high`, `medium` or `low`. Credible contradictions
   are examined rows with `edge_support = contradictory` and strength `strong` or
   `moderate`. A contradiction's weight is the ceiling its strength and relevance
   would give a supporting piece.
4. **No support.** With a credible contradiction the edge is `contradicted`;
   with unexamined citations remaining it is `unassessed` (partially examined:
   absence of evidence is not evidence of absence); otherwise it is
   `unsupported`.
5. **Base grade** is the best supporting piece-level confidence, with two
   limits:
   * `high` requires a `high` piece whose support is `direct`;
   * replication can promote `medium` to `high` only with at least two
     **independent** groups each holding a `medium` piece with `direct`
     support, at least one of them human with relevance `direct` or `close`,
     and at least one of them a causal perturbation. `low` pieces never add up
     to anything, and the number of papers mentioning a pathway is not counted.
6. **Contradiction.** If the heaviest credible contradiction weighs at least as
   much as the base grade, the edge is `contradicted`. A lighter one downgrades
   the base grade by one level (`high` to `medium`, `medium` to `low`) and the
   edge is flagged `contested`.
7. `curation_completeness` records whether unexamined citations remain
   (`complete`, `partial`). A partially examined edge keeps its grade but is
   labelled so, because further reading could move it in either direction.

A coverage report is to count biological edges by grade separately from
external inputs and structural definitions, and to list every edge where no
examined result supports the encoded direction.

### 7.2 Confidence-filtered networks

A filter must never edit text. It is to parse each rule into a tree (the same
grammar as `dt_adoc.model.topology`), remove literals, fold constants, and
re-render **only** the rules that changed, so that the unfiltered configuration
is byte-identical to the parent `network.bnd`, which a test must check. Filtered
networks are new artifacts; the parent model version is never edited.

#### Configurations

| Config | Biological edges retained |
| --- | --- |
| `all` | every edge (no filtering) |
| `high_medium` | edge grade `high` or `medium` |
| `high` | edge grade `high` |

`unassessed`, `unsupported` and `contradicted` never pass a filter. Missing
grades are not treated as `high`.

#### Removal policies

Removing the influence of `C` on `A` is not one operation. Two policies are
specified, to be run and compared side by side:

| Policy | Rewrite of the removed literal | `A = B and C` | `A = B or C` | `A = B and not C` | `A = B or not C` |
| --- | --- | --- | --- | --- | --- |
| `neutral` (default) | the identity of its parent operator: the regulator no longer constrains its clause | `B` | `B` | `B` | `B` |
| `absent` | the regulator is held inactive at this target (`C = 0`) | `0` | `B` | `B` | `1` |

They differ exactly where the biology is ambiguous: an unsupported required
activator is lifted by `neutral` and is unmet under `absent`. Removing an
inhibitor raises activity under both. That is reported, never hidden.

#### Ambiguous outcomes

Under `neutral` a rewrite is **ambiguous**, and generation is to be refused by
default, when:

* `emptied`: every literal of the rule was removed, so the target has no
  supported regulation and no defined value;
* `inhibitor_only`: the original rule had at least one activating literal and
  the rewrite has none, so the target becomes active whenever its inhibitors are
  off (constitutive activity created by the filter).

`--on-ambiguous retain` keeps the original rule for such a target and lists
every edge it thereby retains as `retained_by_ambiguity_resolution`.
`--on-ambiguous absent` rewrites only those targets under the `absent` policy.
Either choice is written to the manifest per node.

#### Reported structural effects

For every filtered network, to be evaluated exhaustively over all free-variable
assignments with the same evaluator as `dt_adoc.reporting.structure`:

* nodes that become constant (permanently active or inactive);
* nodes no longer reachable from any free input;
* phenotype (`OUT_*`) functions that change, with the fraction of assignments
  that differ;
* for every excluded biological edge, the retained non-biological edges leaving
  its source;
* the interventions of `config/protocols_markerless.yaml` whose target lost
  every downstream path. The markerless mechanism itself is untouched: node
  identities are preserved, retired marker nodes are never reintroduced, and an
  intervention still renders as an activity veto of its target.

## 8. Commands

Both exist and are the only ones this change ships. Section 7 has no command.

```bash
pixi run build-edge-evidence   # merge-regenerate the canonical table and validate it
pixi run check-edge-evidence   # require it to validate and to equal a rebuild; writes nothing
```

Equivalently, `PYTHONPATH=src python -m dt_adoc.evidence.experimental {build,check}
[--model-version <version>]`.

A build never drops a row, renames an id or overwrites a curated cell: it adds
missing seed rows, recomputes the generated columns, re-sorts, and writes only
if validation passes. `check` is what the test suite and a reviewer run.
