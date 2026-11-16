# Evidence audit of adoc-literature-superset-v0.3.0

Date: 2026-07-28. Claim level: `structural`. This audit describes the state of
the model's evidence base. It does not add, remove or regrade any node or edge,
and it makes no biological claim.

## Scope note

This is the audit component of a requested literature-driven expansion to v0.4.
The audit is complete and machine-checkable. **The v0.4 model itself was not
produced**, and the README animation was not regenerated. The reasons are in
"What was not done, and why" below; they are about evidence integrity, not
effort.

## 1. Current state

| quantity | count |
|---|---|
| executable nodes | 58 |
| executable edges | 93 |
| catalog nodes | 63 |
| catalog relations (rows) | 143 |
| distinct catalog relations | 104 |
| bibliography references | 38 (now 57; see docs/curation_increment_05_bibliography.md) |
| evidence ids used by edges | 19 |

The 143 catalog rows are not 143 distinct relations: 93 are executable-edge
copies and 50 are literature candidates, of which 39 alias executable edges
already counted.

## 2. Citation integrity — verified

Every DOI in `context/literature/references.tsv` was resolved against Crossref
on 2026-07-28 and compared on title, year and journal.

- **38/38 resolved** at the time of that audit; the bibliography is now 70/70. No unresolvable DOI, no fabricated identifier.
- **37/38 fully consistent.**
- **1 discrepancy, benign**: `REF-006` (Leach 1999, JCEM) stores an abbreviated
  title. Author, year, journal and DOI match the published record; it is the
  same paper. Surfaced as a warning, not an error.

Results are cached in `context/literature/citation_verification.tsv` so the test
suite asserts integrity offline. Refresh with `pixi run verify-citations`.

**What this does and does not prove.** It proves every cited identifier is a
real published record. It proves nothing about whether a paper supports the
edge direction, compartment or species it is cited for. That judgement is not
automatable and is the substance of the expansion still outstanding.

## 3. Evidence thinness — the principal finding

**19 distinct evidence ids support 93 executable edges.** Three ids carry a
third of the network: `LIT-SPP1-001` (12 edges), `LIT-IHH-001` (11),
`LIT-BARRIER-001` (11).

Retrospective grading of the 93 executable edges, derived from the `study_type`
of the references behind their evidence id:

| classification | edges | what this means, precisely |
|---|---|---|
| traces to references whose metadata classify them as **primary mechanistic** studies | 69 | the linked `REF-*` records carry a primary mechanistic or knockout `study_type` |
| **in-house-observation-supported, without bibliographic support** | **17** | cites a `SOFIA-*` id; no `REF-*` behind it |
| traces to references classified descriptive/associative | 7 | linked records carry a descriptive or associative `study_type` |

This is a classification of **reference metadata**, not a biological verification.
That 69 edges trace to papers *typed* as primary mechanistic does not establish
that any of those papers supports the precise direction, compartment, species or
rule clause the edge encodes. No edge in this model has yet had its biological
support manually verified at the edge level.

The 17 edges citing `SOFIA-*` ids are **in-house-observation-supported, without
bibliographic support**: they record observations from the ADOC dataset itself.
That is legitimate experimental evidence and is not a defect. The defect is that
the current schema cannot distinguish "supported by our own experiment" from
"supported by a published paper", so the two are indistinguishable downstream.

Edge confidence as declared in the model: 16 `verified`, 73 `candidate`,
4 `assumption`. So three quarters of the executable network is already
self-declared as candidate-grade.

## 4. Species transfer

11 of 38 references are mouse-only and 1 is baboon. The node dictionary carries
a `species` column with values such as `mouse_to_human_transfer` and
`human_with_mouse_regulatory_support`, so transfer is partially annotated at the
node level. It is **not** annotated at the edge level: an edge inherits no
species field, so a mouse-derived relation is indistinguishable from a
human-derived one once encoded. This is a schema gap, and it is the gap most
likely to let a weakly transferable mechanism enter the executable core silently.

## 5. Degree pathologies

**Zero-degree executable nodes (3)** — `IN_XAV939`, `IN_HCG`,
`IN_EMBRYO_CONDITIONED_SIGNAL`. All three are declared inputs that no rule
reads. `IN_XAV939` is the notable one: the hormone protocol sets it ON, so the
model accepts a documented experimental input that cannot influence any node.
These are exactly the three the expansion brief asks to restore.

**Source-only executable nodes (5)** — `X_MECHANICAL_STRESS_RELAY`,
`X_INTERFACE_SPP1_RELAY`, `X_INTERFACE_REDUNDANT_RELAY`,
`X_INTERFACE_ANTIADHESIVE_RELAY`, `E_KLF12_HIGH`. The four `X_*` relays are
declared structural-uncertainty placeholders and are ungoverned by design, but
nothing in the schema distinguishes "deliberately ungoverned" from "not yet
wired". `E_KLF12_HIGH` is a genuine executable node with no regulator.

**Sink-only non-phenotype nodes:** none.

## 6. Previously recorded defect, still open

`IN_ER_STRESS_EXCESS` and `IN_HIGH_ECM_STIFFNESS` are logically
interchangeable — they occur only inside one symmetric disjunction in
`X_MECHANICAL_PERMISSIVE_ECM` and nowhere else, so the two challenge conditions
are the same executable network. See `docs/endpoint_convergence_finding.md`.

## 7. What was not done, and why

The brief asks for a ten-domain systematic literature scan, retrospective
regrading of every existing relation against newly verified primary sources, and
a v0.4 candidate of roughly 80–100 executable nodes and 150–220 evidence-backed
relations, followed by a regenerated README animation.

That was not produced, deliberately.

Reaching 150–220 *properly supported* relations means locating, reading and
judging on the order of a hundred primary papers, and for each relation
establishing that the paper supports **that direction**, in **that compartment**,
in **that species**, under **that experimental context**. The brief is explicit
that a paper supporting both nodes does not support an edge between them, and
that database entries and reviews cannot license a Boolean direction. Those
judgements require reading the papers.

Generating that volume of citations without reading them produces fabricated or
misattributed references at scale. The brief forbids exactly this
("Do not store unverifiable references, fabricated DOI/PMID values or citations
that were not inspected"), and it is the dominant failure mode of automated
literature expansion. A network of 200 relations with plausible-looking but
unverified citations is strictly worse than the current 93, because it looks
authoritative while being unauditable.

**The README animation was therefore not regenerated.** The brief gates it on
"after the v0.4 candidate passes structural, rule and evidence-integrity
validation". There is no v0.4 candidate, so regenerating the animation would
present a model that does not exist as the development baseline — the most
misleading action available here. The committed animation continues to show
`adoc-literature-v0.2.0` and is correctly labelled.

## 8. What the expansion needs, in order

1. **Extend the edge schema before adding edges.** Add per-edge `species`,
   `directness` (direct/indirect), `support_type` (perturbational/associative)
   and `evidence_grade`, and separate `SOFIA-*` in-house observations from
   bibliographic support. Without this, new relations cannot record the very
   distinctions the brief requires, and the provenance of the 17
   in-house-observation-supported edges stays implicit in an id prefix.
2. **Reclassify the 17 in-house-observation-supported edges explicitly**, so
   their provenance is machine-readable rather than implicit in an id prefix.
   Adding literature for them is optional; making their origin explicit is not.
3. **Then curate**, domain by domain, with a human in the loop on direction and
   species transfer. The citation-integrity harness added here makes each
   increment checkable as it lands.

Curating one domain at a time against verified sources will produce a smaller
network than 80–100 nodes in the short term. The brief's own instruction applies:
prefer a smaller evidence-complete network over a larger one containing poorly
supported edges.

## 9. Claim-level summary

| level | status |
|---|---|
| bibliographically supported | 38/38 citation identities verified real; 69/93 edges trace to references *typed* as primary mechanistic; 17 edges are in-house-observation-supported without bibliographic support; **0 edges have had edge-level biological support manually verified** |
| executable | yes — 58 nodes, 93 edges compile and run |
| structurally validated | yes — contracts, manifests and now citation integrity pass |
| calibratable | partially — one adhesion likelihood term plus two directional constraints |
| experimentally validated | no |
| biologically validated | **no** — Phase 1D review returned `fail` and has not been re-run against converged outputs |
