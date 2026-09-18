# Curation increment 8 — the two blocked U4b sources, read: one candidate rejected, one advanced, nothing executable moved

Date: 2026-09-18. Claim level: `full-text verification, bibliography registration
and candidate re-adjudication`. **No executable model file was modified** — nothing
under `models/`, `config/` or `data/` differs, which `git diff` shows directly — so no
rule, node, edge, threshold, rate, initial condition, input or phenotype changed.
**Guards:** `tests/unit/test_curation_increment_08_blocked_sources.py`, whose
`NoExecutableChangeTest` re-derives in this unit that both supersets still measure 19
free variables and that no name from either paper reaches either rule set. Byte-identity
between the v0.5 scaffold and v0.4 is a separate invariant, guarded by
`tests/unit/test_v05_scaffold.py::ScaffoldIdentityTest`, not here.

U4b closed the fourteen September-11 candidates with two of its nine references
**access-blocked**, recorded both as blocked rather than as negative evidence, named
the specific fields each would unblock, and said in terms that registering them later
"is legitimate and changes no U4b conclusion". This is that later unit. It was scoped
to those two papers and to the candidates whose decisions depended on them; Unit C,
U5, calibration and topology were out of scope and stayed out.

---

## 0. The three things this unit keeps apart

The whole risk of a literature refresh is that these collapse into one another, so
they are separate columns in the machine-readable record and separate test classes
in the guard:

| | happened? |
|---|---|
| **evidence strengthened** — a reference moved from unread to read | **yes, twice** |
| **candidate admitted** — a node moved on the §5 ladder | **yes, in both directions** |
| **executable encoding justified** — a rule, edge, input or rate changed | **no, for nothing** |

The headline is that **the same paper moved two candidates in opposite directions**.
Ma 2023 supplies the determinant that advances `E_SLEX_SURFACE` and, in the same
figure, falsifies `E_GLYCOSYLATION_PROGRAM`. That is the clearest sign available that
the unit was not run toward a conclusion.

---

## 1. What was read, and how it is checkable

Both PDFs were located in the main checkout's gitignored library
(`/home/francois/Projects/DT_ADOC/context/literature/pdfs/`), hashed before reading,
and read in full via `pdftotext -layout`. **Neither PDF is committed**, and the guard
checks that.

| | Zhou 2021 | Ma 2023 |
|---|---|---|
| DOI | `10.1096/fj.202100590R` | `10.1093/biolre/ioad007` |
| PMID | 34252231 | 36648484 |
| citation | *FASEB J* 35(8):e21784 | *Biol Reprod* 108(4):564–574 |
| pages | 28 | 11 |
| sha256 | `17c81107f6a5224045eeefba4b7f95146fdcd0d15a878b1486b33c83fce33e9c` | `13a1e0352fafad24f666a2112fd6108dea2b3a685645a20d14bad51c283a7f97` |
| version read | **accepted author manuscript** (Minerva Access) | **version of record** (OUP typeset) |
| registered | **REF-076 / PDF-048** | **REF-077 / PDF-049** |
| ledger row | `BSR-DRREF-007` | `BSR-DRREF-006` |

### 1.1 Why these were registered when U4b registered nothing

U4b declined `REF-*` ids deliberately: "registration is curation and U4b is an
adjudication unit". **This unit is a curation increment**, which is the case U4b
named as legitimate. Registration is consistent across all four artifacts —
`references.tsv`, `pdf_manifest.tsv`, `citation_verification.tsv` and the new ledger
— and the guard checks the join end to end rather than per file.

### 1.2 The Zhou provenance caveat, recorded rather than glossed

The Zhou file is the **accepted author manuscript** deposited in the University of
Melbourne's institutional repository, *not* the publisher version of record. It
carries the banner "has undergone full peer review but has not been through the
copyediting, typesetting, pagination and proofreading process"; its internal citation
line gives the **Wiley alias** `10.1002/FSB2.21784` rather than the canonical DOI; and
the repository's own metadata header **drops the "1" from "Jagged1"**.

**Recording that in prose alone would not be enough.** `publication_status` was
the only machine-readable field bearing on it, and it reads `published`, which would
leave `REF-076` indistinguishable from a version-of-record citation at every point of
use and the corpus-wide count of files that are not versions of record short by one —
while every figure and page reference in the ledger row is to the manuscript.

**So one column no longer carries two facts.** `pdf_manifest.tsv`
gains a `rendering_read` column, and the two are now settled and separately asserted:

| column | describes | Zhou 2021 |
|---|---|---|
| `publication_status` | the **article** — is there a version of record at all? | `published` |
| `rendering_read` | the **file** that was hashed and read | `author_manuscript` |

Recording Zhou as `accepted_unedited` instead would have been simply **false** — that
value means "accepted, not yet through production, final text may still change", and
this article has been published for five years. It would also have forbidden the
`REF-*` id, defeating the unit's purpose. The article *is* published; only the
rendering diverges, and that now has a field of its own.

Vocabulary: `version_of_record` | `author_manuscript` | `preprint` | `unrecorded`.
Only the two rows this increment read carry a substantive value; every other row carries
`unrecorded`, which is backfill
and **not an escape hatch** — `test_new_registrations_must_record_their_rendering`
forbids it for anything registered from this batch onward, and a later increment may
resolve the older rows from their digests. Two invariants are asserted: an
`accepted_unedited` article cannot have been read from a version of record, and the
set of files **recorded as** not versions of record is pinned exactly — `{PDF-048}` —
so joining it is a deliberate act, taken on inspection.

**What that set is not.** It is what the manifest *records*, not what is true of the
corpus: 47 rows carry `unrecorded` and any of them could be a manuscript or a preprint.
The three `accepted_unedited` rows briefly carried `author_manuscript` on the reasoning
that an article not through production has no version of record to have been read from —
which is sound but **too weak for the value it was used to justify**. It excludes
`version_of_record` and leaves three vocabulary values standing, so it cannot choose
`author_manuscript` over `preprint`. They carry `unrecorded` now, which is the value for
"not established", and nothing is lost by it: that those files are not versions of record
is already carried by `publication_status = accepted_unedited`. Establishing the rendering
means opening the files, which is a later increment's work, not this one's.

### 1.3 No older ledger was backdated

U4b's `U4B-DRREF-006` and `U4B-DRREF-007` still say, verbatim, that nothing was
verified and that access was blocked — because on 2026-09-17 that was true, and
rewriting it would misattribute a 2026-09-18 curation to U4b. This is the same
refusal U4 made when it declined to backdate `CD98-d` into the September-16 ledger.

What was added is a **supersession pointer** in each row's `verification_route`,
naming the superseding finding and file, so that a reader landing on the old row
learns the fact stopped being true instead of taking it at face value.
`U4B-DRREF-005` (Yu 2018) carries a third pointer, in a **different column** —
`canonical_promotion_decision`, because its own *read* is superseded by nothing and
only the verdict it states for `E_GLYCOSYLATION_PROGRAM` was re-adjudicated, on a
different paper. All three are guarded by
`test_superseded_rows_declare_their_successor`, which reads each row in the column
that row actually uses.

That distinction is why **supersession is recorded per candidate, not per row.** The
agreement check between the ledger and the dispositions table now resolves the
*governing* row for each candidate — the last one, in ledger order, that names it —
and a companion test requires that any row disagreeing with the live table be covered
by a later row that re-adjudicated the same candidate. Without that second test, the
exemption would have quietly tolerated exactly the drift the check exists to catch.

---

## 2. Zhou 2021 — JAG1 / NOTCH

### 2.1 What is established, separated by system as U4b's blocking field (a) asked

**Figure 2's own legend reads "JAG1 knockdown in *Ishikawa cells*".** That single fact
governs most of the extraction, because the Results prose says "human endometrial
epithelial cells" throughout and the Abstract says "we confirmed that in human
endometrial epithelial cells, JAG1 interacted with NOTCH3". The primary-cell evidence
is confined to **Fig 1A, Fig 1C and Fig 3B**.

| finding | primary HEECs | Ishikawa |
|---|---|---|
| JAG1 knockdown confirmed | ✔ *p* < 0.05, n = 5 | ✔ n = 4 |
| **trophoblast-spheroid adhesion reduced** | **✔ *p* < 0.05** | ✔ *p* < 0.05 |
| NOTCH3 NICD reduced | **✘ *P* = 0.073, n = 3 — not significant** | ✔ *p* < 0.05 |
| NOTCH1 / NOTCH2 NICD | not measured | **significantly *increased*** |
| HEY1 down, HES1 unaffected | not measured | ✔ *p* < 0.01, n = 7 |
| LIFR, SPP1, ITGB3, MAOA, IGFBP1 down; GPX3, DPP4 unchanged | not measured | ✔ |
| PGR, ESR1 | not measured | **unchanged** |
| MAML1 knockdown arm | not measured | ✔ n = 6–7 |

Three things deserve to be pulled out.

**The node is measured as *activity*, which is what its definition requires.** NICD
production by receptor-specific cleaved-domain immunoblot with densitometry is
pathway activity, not transcript abundance — so `E_JAG1_NOTCH3` does *not* fail the
§5(2) activity-versus-abundance test that defeated `S_FOXO1`, `E_SOX17` and
`E_ITGA2B1`.

**The viability confound is bounded here, which it is not in Yu 2018 or Ma 2023.**
xCELLigence shows adhesion significantly reduced within **3–8 h** of seeding, while
the authors state proliferation was **unimpaired up to 60 h** and fell only after 80 h
(*p* < 0.0001). The adhesion effect is temporally separated from the proliferation
effect rather than entangled with it — the cleanest handling of `DRUNR-010` in any
source read across U4b or this increment.

**The primary-cell NOTCH3 result is a non-significant trend that the paper's own prose
calls "confirmed".** *P* = 0.073 at n = 3, per the Figure 3B legend. **The legend
governs**, and the discrepancy is recorded in the ledger so that a later unit reading
only the abstract does not inherit a significance the data do not carry.

### 2.2 What the node may defensibly mean

> the epithelial state in which JAG1 is present and JAG1-dependent NOTCH3 NICD is
> being produced, functionally coupled to trophoblast-spheroid adhesive capacity.

It may **not** mean that NOTCH3 is the *necessary receptor* for that adhesion. No
NOTCH3 knockdown, blockade or γ-secretase arm exists anywhere in the paper; receptor
attribution rests entirely on the **direction** of NICD change; and NOTCH1 and NOTCH2
NICD moved the *other* way, which the authors concede did not compensate. Their own
wording is that JAG1-NOTCH3 "**may** play a dominant role". So the receptor half of
the node's name is the weaker half, and it is carcinoma-line-only besides.

### 2.3 Disposition

`EVIDENCE_UNVERIFIED` → **`WAIT_FOR_EXPERIMENT`**; node verdict `UNVERIFIED` →
`JUSTIFIED_SYSTEM_LIMITED`; first failing criterion **§5(1) → §5(2)**; unblock locus
`ACCESS_BLOCKED` → `ADOC_RUNNABLE`. **Encoding verdict unchanged at
`REJECT_AS_STAGED`.**

§5(2) fails **completely rather than narrowly**: no hormonal, steroidal, cAMP or
cytokine input to JAG1 is perturbed *anywhere in the paper*. The only upstream
statement is observational cycle-phase immunostaining carried over from the authors'
prior work — which is precisely the "observational tissue expression" U4b refused to
accept as a determinant for `E_SLEX_SURFACE`. So **`DRUNR-005` is now confirmed by the
source rather than inherited**, and U4b's prediction that "obtaining (a) alone does
not make the node promotable" held exactly.

The choice between `WAIT_FOR_EXPERIMENT` and `RETAIN_CATALOG_ONLY` was genuinely
contestable — `S_FOXO1` is the precedent for the former ("add a protein readout across
the existing arms"), `E_SOX17` for the latter ("half the unblock is external to this
platform"). It was put to the owner and ratified on 2026-09-18: the ratified §5(2)
wording is applied to the evidence missing **at the first failing rung**, which is
ADOC-obtainable, and the external width limits are recorded in `node_verdict` instead
of being folded into the unblock.

**The named experiment, and the scope that binds it.** Measure epithelial JAG1 protein
together with NOTCH3 NICD, and preferably HEY1, across the **existing** control-versus-
hormone-treated arms in the three deposited donors. But the deposited contrast sets
`IN_E2`, `IN_PROGESTIN`, `IN_cAMP` and `IN_XAV939` **together**, and
`config/protocols.yaml` records that the design has **no single-agent arm**. Such an
experiment can therefore establish only a **context-level** determinant — that the
cocktail moves the state — and can **never name a hormone**. A control-versus-cocktail
difference **must not** be converted into `IN_P4 → JAG1` or `IN_E2 → JAG1`. The
unblock condition says so in terms and the guard asserts it, because a row reading
`ADOC_RUNNABLE` without that clause would license the very invention `DRUNR-005`
forbids.

### 2.4 The SPP1 candidate relation — registered, at canonical-Notch specificity

Registered as `BSR-REL-001` in
`context/literature/reviews/blocked_source_refresh_2026-09-18.candidate-relations.tsv`:

> **JAG1-dependent, MAML1/canonical-Notch-dependent transcriptional output →
> `E_SPP1_EXPR`**, activation, confidence 4, **not executable**.

**Why SPP1 and nothing else.** Five receptivity markers fall on JAG1 knockdown. MAML1
knockdown — of the shared Notch transcriptional coactivator — reproduces **only
SPP1** (*p* < 0.05) and leaves LIFR, ITGB3, MAOA and IGFBP1 unaffected. The
canonical-Notch attribution is therefore supported by an **elimination**, not by a
single positive, and corroborated by an RBPJ site at −723 to −734 bp of the SPP1 TSS.

**Why not at NOTCH3 specificity.** MAML1 is shared by all four Notch receptors, so its
knockdown cannot assign SPP1 to NOTCH3 — and the assignment is *actively undermined*
in this very paper, because JAG1 knockdown pushed NOTCH1 and NOTCH2 NICD the opposite
way, so a MAML1-dependent output could run through a receptor whose activity rose.
Recording this as an `E_JAG1_NOTCH3 → E_SPP1_EXPR` edge would claim a receptor the
experiment never tested.

**Why it is measurement-compatible at all**, which is the unusual part: the target
`E_SPP1_EXPR` is a committed node defined as "SPP1 expression or secretion" with RNA
interpretability `direct_transcript`, and the evidence is SPP1 **mRNA**. So §5(2)'s
activity-versus-abundance test — which defeated three other candidates — does **not**
fire against this relation. It is nonetheless **Ishikawa-only**, with no primary-cell
support, which is why the confidence is 4 and the verdict is catalogue.

**Why it is not in `context/literature/candidate-edges.tsv`.**
`test_candidate_edges_resolve_to_known_nodes` requires both endpoints to resolve to
`candidate-nodes.tsv` or `models/specs/nodes.tsv`. The source resolves to neither:
`E_JAG1_NOTCH3` exists only in the quarantined staged bundle, and the honest source is
not `E_JAG1_NOTCH3` in any case but the broader canonical-Notch output, which is not a
node anywhere. Adding either to the canonical catalogue would promote a staged
`catalog_only` candidate on the strength of an Ishikawa-only relation. Recording it in
the increment's own ledger keeps it queryable, attributed and at its true specificity
without minting a node to hang it on.

### 2.5 What was refused, and why each refusal is checked

Each of these is a relation someone could plausibly draw from this PDF. Each is pinned
by a test in `ForbiddenInferencesTest`.

- **No `IN_P4 → JAG1`, `IN_E2 → JAG1` or `E_SECRETORY_STATE → JAG1`.** Nothing upstream
  was perturbed.
- **No downstream `E_JAG1_NOTCH3` edges to LIFR, ITGB3, MAOA or IGFBP1.** They survive
  MAML1 knockdown, so they are Notch-*independent* outputs of JAG1. ITGB3 and IGFBP1
  are the tempting ones, being model-relevant already.
- **No `JAG1 → PGR` and no `JAG1 → ESR1`.** Both explicitly unchanged in the human
  models. Mouse `Esr1` *does* fall — a species difference, not an edge.
- **No tight-junction edges in human.** `Cldn4`, `Cldn1` and `Ocln` fall in mouse
  luminal epithelium; CLDN4 is explicitly **not** regulated in HEECs or Ishikawa. The
  canonical targets diverge by species too — HEY1 falls in human and not HES1, `Hes1`
  falls in mouse and not `Hey1` — and the authors conclude the species act "likely via
  different mechanisms". **No mouse-only finding became a human epithelial edge.**

---

## 3. Ma 2023 — IL1B / FUT3 / surface sLeX

### 3.1 The central result, and which legs of it are clean

RL95-2 endometrial carcinoma monolayers, IL-1β 20 ng/mL, HTR-8/SVneo spheroid
attachment at 2 h.

| leg | result | confounded? |
|---|---|---|
| IL-1β → surface sLeX | up, *p* < 0.0001 (flow, n = 6); **LeY unchanged** | per-cell MFI; no viability control |
| IL-1β → spheroid attachment | up, *p* < 0.01 (n = 18) | no viability control |
| **anti-sLeX blockade → attachment** | **down at basal *and* induced, *p* < 0.05 / *p* < 0.001** | **largely avoided — 1 h pretreatment, 2 h coculture** |
| FUT3 siRNA → surface sLeX | down, *p* < 0.05 / *p* < 0.01; **LeY unmodified** | 72 h transfection, no viability control |
| FUT3 siRNA → attachment | down at basal *and* induced, *p* < 0.05 / *p* < 0.0001 | 72 h transfection, no viability control |

The **anti-sLeX blockade arm is the paper's cleanest evidence**: at 1 h of antibody
pretreatment plus 2 h of coculture it largely avoids the *proliferation* confound that
a 72 h knockdown or a 4-day cytokine exposure carries. **Stated at that width and no
wider** — acute viability and cytotoxicity were not directly measured in any arm, so
the right claim is that this arm makes a proliferation explanation very unlikely, not
that it excludes every viability effect.

### 3.2 The four U4b blocking fields, answered

| field | answer |
|---|---|
| (a) primary epithelium or organoid, or a line? | **RL95-2 only — and it is the *same* line as Yu 2018**, so the two references are *not* independent system support |
| (b) viability control? | **None at all.** No CCK-8, no EdU, no MTT, no apoptosis assay, no cell-count normalisation |
| (c) graded or switch-like? | **Neither established.** One concentration throughout. No FUT3 overexpression arm either, so FUT3 is necessary and **not** sufficient |
| (d) is IL-1β a state ADOC varies? | **No.** No `X_IL1B` and no `IN_IL1B` input was created |

Field (b) deserves emphasis because it runs the opposite way to the intuition that a
second paper relieves a first paper's limitation. **Yu *measured* proliferation in this
same cell line and found ST3Gal3 knockdown reduced it.** Ma's 72 h FUT3 knockdown and
4-day IL-1β exposure therefore **inherit that concern unmeasured** rather than
resolving it. `DRUNR-010` applies, and the node's system limitation is now **doubly
confirmed rather than relieved**.

The human-tissue arm (GSE98386, 20 fertile women, paired early- versus mid-secretory)
shows FUT3 and IL1B both higher in mid-secretory (*p* < 0.001) and correlated
(Spearman *r* = 0.72, *p* < 0.0001). This is **correlational bulk tissue**. It cannot
localise IL1B to the epithelium — the paper's own Introduction attributes endometrial
IL-1β to trophoblast, decidual cells and leukocytes — so it supports **physiological
relevance and not human epithelial IL1B → FUT3 causality**.

### 3.3 `E_SLEX_SURFACE` — two rungs gained, the verdict unchanged

Disposition **unchanged** at `RETAIN_CATALOG_ONLY`; first failing criterion **§5(2) →
§5(4)**; evidence state → `BOTH_REFERENCES_VERIFIED`; unblock locus
`EXTERNAL_AND_ACCESS_BLOCKED` → `EXTERNAL`.

**Ma supplies the determinant U4b recorded as missing, and supplies it for the right
variable.** IL-1β raises surface sLeX measured **as surface sLeX**, by flow cytometry
with an anti-sLeX antibody — the node's own variable, not a transcript proxy for it. So
§5(2)'s activity-versus-abundance test does not fire, and the node now passes
§5(0)–(3).

It fails at **§5(4)**, the last rung, on measurement that has not changed: as the
replacement for the committed `E_MUC1_SLEX` the staged pair takes 35 → 35 distinct
Boolean functions **while growing AC01 from nine to eleven**. §5's original and only
stated disposition governs — failing (4) while passing (1)–(3) is
`RETAIN_CATALOG_ONLY`, not `REJECT`.

**Separately and independently, the encoding stays rejected.** The evidenced
determinant is IL-1β, which is not an ADOC state and is not a node; creating one would
be exactly the invented free input `DRUNR-004` refuses. **The committed `E_MUC1_SLEX`
was not reopened as a topology change**, as instructed — the measurement/identifiability
limit that closed that question is untouched by Ma's availability.

This row is the clearest illustration of the three-way separation in §0: **evidence
strengthened, node admission advanced two rungs — it now clears (2) and (3) —
disposition unchanged, encoding
still blocked.**

### 3.4 `E_GLYCOSYLATION_PROGRAM` — `REJECT`, scoped to the definition

`RETAIN_CATALOG_ONLY` → **`REJECT`**; node verdict `DEFINITION_INSUFFICIENT` →
`SEMANTICS_REFUTED`; criterion **§5(0-insufficient) → §5(0-refuted)**. This is the
closure's **only** `REJECT`.

The node is defined as an "Epithelial **FUT3/ST3GAL3**-like glycosylation program",
with measurables "FUT3; ST3GAL3; glycan profiling". Ma measured **both named enzymes,
in the same cells, under the same stimulus**:

| | direction | *p* |
|---|---|---|
| **FUT3** | **up** | **< 0.001** |
| **ST3GAL3** | **down** | **< 0.05** |
| ST3GAL4 | down | < 0.01 |
| FUT4, FUT7 | down | < 0.05 |
| ST3GAL6, FUT1 | ns | 0.08, 0.09 |
| FUT2 | undetectable | — |

The authors state the dissociation in terms: sLeX is "not suppressed by IL-1β induced
decrease of ST3GAL3/4 and FUT7 but rather **enhanced by the upregulated FUT3**".

**The entailment burden §5(0-refuted) places on the rejecting unit is met.** The
definition names those two enzymes and the measurables column names exactly those two;
a single Boolean node over them **asserts they share a state**, and no assignment of
one Boolean variable represents FUT3 ON with ST3GAL3 OFF.

The repository's own frozen ADOC scRNA audit corroborates the general proposition that
these enzymes do not behave as a co-regulated programme — a different platform,
different cells, a different stimulus — with FUT6 +1.60/+2.99/+2.73 against ST3GAL4
−1.11/−0.25/−1.45 across three donors (`docs/scrna/node_support_finding.md:112`).
**Stated at the width it supports, and no wider:** those exemplars are a **different
enzyme pair** from the FUT3/ST3GAL3 one the definition names, so the audit is
*supporting context* and **not** an independent replication of the specific
dissociation. **The refutation rests on Ma 2023**, which measured the two named enzymes
themselves.

**This is not a reversal of external review finding B3, and must not be read as one.**
B3 withdrew U4b's first `REJECT` on two grounds. The **logical** ground — falsifying
transcript co-regulation among selected enzymes is not falsifying the existence of a
functional state — is permanent, and it is *honoured* here by scoping the `REJECT`
strictly to the transcriptional programme and leaving the functional glycan-output
state with `E_SLEX_SURFACE`, which this same paper strengthens. The **evidentiary**
ground was specific and dischargeable: "DRREF-006, the reference bearing on the FUT3
half of the definition, is ACCESS BLOCKED and unread. A refutation cannot rest on
silence about a component whose evidence was never obtained." **That reference has now
been read, and it contradicts the definition rather than being silent on it.** B3 was
correct on the evidence available to it; this unit obtained the evidence it named as
missing.

The guard encodes the conditions under which a `SEMANTICS_REFUTED` row is admissible
at all: the falsified components must be the ones the **definition** names, no
access-blocked reference may appear among its decisive references, and the row must
name the surviving candidate — which must itself still be alive, or the scoping is a
form of words.

**Decision route.** This met the hard-decision consultation bar, so `aih consult` was
run first; it returned **UNAVAILABLE — the Codex workspace is out of credits**, which
is not agreement. Per policy the options, the evidence and the competing readings were
put to the owner, who chose the (0-refuted) reading on 2026-09-18 with the scoping
above. No unresolved disagreement remains.

---

## 4. The two papers stay mechanistically independent

They were curated together because they were the two remaining access-blocked U4b
sources, **not** because they describe one pathway. No cross-link was inferred: no
`JAG1 → IL1B`, no `JAG1 → FUT3`, no `NOTCH3 → sLeX`, no `IL1B → JAG1`. The guard
asserts that neither ledger row's supported findings mention the other paper's
entities.

---

## 5. What did not happen

Unit C was not reopened; temporal integration, PAEP, PRL/IGFBP1 and checkpoint
architecture were not touched, and **this unit found no contradiction requiring it**.
U5 was not started. MaBoSS was not recalibrated. No Boolean input, transition rate or
dose threshold was added. No mouse-only edge was imported. No transcript abundance was
equated with pathway activity or surface glycan state. The staged bundle was not
edited — a re-adjudication records a **new** verdict against it and never rewrites the
reviewed delta. `models/`, `config/` and `data/` are untouched.

**One executable change was considered and is explicitly *not* compelled.** The
candidate that comes closest is the SPP1 relation, because its target is a committed
node and its measurement type matches. It falls short on three counts, each
independently sufficient: the source state is not a node in the model; the evidence is
Ishikawa-only; and the relation's own upstream, `E_JAG1_NOTCH3`, has **no determinant**
— so wiring it would introduce the free variable §5(2) exists to refuse.

---

## 6. Open questions this unit did not close

- **The receptor half of `E_JAG1_NOTCH3` is unproven and externally blocked.** No
  NOTCH3 perturbation exists; NOTCH1/2 NICD move the other way. ADOC cannot supply a
  receptor-resolved knockdown.
- **`E_SLEX_SURFACE` has no viability-controlled replication.** Both its references use
  RL95-2; one measured a proliferation confound and the other measured nothing. The
  unblock is external.
- **`E_SLEX_SURFACE` and a restated glycan-output candidate may be the same node.** U4b
  flagged it; this unit did not decide it, because deciding it would be proposing a new
  candidate rather than adjudicating an existing one.
- **Whether the ADOC cocktail moves JAG1 at all is untested**, and by design can only
  ever answer at cocktail level.
- **`docs/paywalled_papers_needed.md` now lists one remaining blocker** (Huang 2009,
  low curation impact) plus the Tier-1/Tier-2 items, which are search problems rather
  than access problems.

---

## 7. Files changed and tests affected

This section names **what** each artifact records or guards, not how many rows or
methods it has. A count belongs here only when the number is itself the claim; the
disposition tally is the one that is, and it is derived by
`test_the_disposition_tally_is_derived_and_the_documents_match_it`, which checks it
against `docs/v05_mechanistic_integration_plan.md` and
`docs/v05_u4b_candidate_node_closure.md` — the two documents that quote it.
Repair history is deliberately not recorded here: it is authoritative in the Git
commits that carry it and in the harness review record, as
`docs/v05_u4b_candidate_node_closure.md` states for its own unit.

**Registered:** `context/literature/references.tsv` (REF-076, REF-077);
`context/literature/citation_verification.tsv` — **regenerated by
`pixi run verify-citations`, never hand-edited**, so every row records a resolution
that actually ran; `context/literature/pdf_manifest.tsv` (PDF-048, PDF-049, plus the
`rendering_read` column, see §1.2).

**New:** `context/literature/reviews/blocked_source_refresh_2026-09-18.primary-verification.tsv`
— the claim-level read of each paper, one row per source;
`…candidate-relations.tsv` — the JAG1/canonical-Notch → `E_SPP1_EXPR` relation, at
the specificity §2.4 states; `tests/unit/test_curation_increment_08_blocked_sources.py`
— provenance, the three re-adjudications, the SPP1 relation's specificity, the
refused inferences, and the no-executable-change invariant; and this document.

**Re-adjudicated:** `…candidate-node-dispositions.tsv`, the three rows §2 and §3
decide. **Supersession pointers only:** `…2026-09-11.primary-verification.tsv` — no
U4b finding is altered.

**Guards amended.** `test_v05_u4b_candidate_closure.py`: supersession is now resolved
per candidate rather than per row, with tests forbidding uncovered drift, requiring a
superseded row to declare its successor, requiring re-adjudication to be total, and
imposing §5(0-refuted)'s entailment burden on any `SEMANTICS_REFUTED` row; the
ledger-citation check reads a prefix set rather than `startswith`.
`assertNotIn("REJECT", set(table.values()))` is **removed**, necessarily, since this
increment issues a `REJECT` — what it protected is carried more tightly by
`test_a_refutation_discharges_the_burden_section_5_carries`, and by
`test_unverified_candidates_are_not_rejected_for_being_unverified`, which keeps the
principle external review B3 established: a paywall never produces a `REJECT`.
`test_pdf_manifest.py` gains the `rendering_read` vocabulary, the
`accepted_unedited` ⇒ not-a-version-of-record invariant, the rule that a new batch
may not use `unrecorded`, and the pinned set of files that are not versions of record.

**One scope item taken on because the repository asked for it.**
`context/literature/pdf_manifest.tsv` was the single tracked file with **mixed** line
endings, and `docs/v05_line_endings.md` records that it is "flagged here so a future
unit that has a substantive reason to touch that file fixes the endings in the same
commit". Appending rows to it is exactly the append that pin warns is invisible in
review, so it was normalised to CRLF — the convention of its header and its majority —
in the same commit, and the pinned mixed set is now empty.
