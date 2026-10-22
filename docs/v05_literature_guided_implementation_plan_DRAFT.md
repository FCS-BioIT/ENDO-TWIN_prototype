# DRAFT IMPLEMENTATION PLAN — NOT AUTHORIZED

**Date:** 2026-10-21
**Governing request:** `docs/v05_literature_guided_replanning_request_2026-10-21.md`
**Status:** complete plan, submitted for owner approval. Nothing here is executed.
**Authoring:** AI-assisted session; the assistant model was switched once
mid-session. The first model returned no review and no adjudication, and none
is claimed for it.

> **Discipline for this document.** Every fact appears **once**. Later sections
> cross-reference rather than restate. Where a number is given, the command that
> reproduces it is given with it.

## 0. What changed relative to the previous revision

The previous revision of this file was retitled a *structural audit and scoping
memo* because the §D.3 primary-evidence adjudication had not been done and the
§E.2 crosswalk was judged unachievable. Gate finding **B4** recorded that as a
blocker: *"the delivered plan must contain the decision-ready work explicitly
required by its governing request"*, closed when *"the required crosswalk,
adjudication, matrices, unit details, and independent critique are completed and
the staged decisions are reconsidered from them"*.

This revision does that work. Specifically:

1. The corpus crosswalk is **completed**, not declared impossible (§2). The
   obstacle the previous revision reported — that corpus claims have no tracked
   artifact because the PDFs are gitignored — is dissolved by writing the
   reconciliation itself as a repository artifact carrying only hashes, paths and
   ledger membership, with no copyrighted content.
2. The Track A and Track B adjudication is **performed against the original
   PDFs**, figure and methods level (§4).
3. The traceability and identifiability matrix is **built** (§5), on the
   repository's own design-alias machinery rather than on a new one.
4. The §4 decisions of the previous revision, including the withdrawn CDH1
   selection and the replaced prioritization rule, are **reconsidered from the
   adjudicated evidence** (§7).
5. An independent critique was commissioned, and its six blocking findings are
   answered in §9 — three of them by re-deriving the structural counterfactual
   myself and **correcting this plan's central ordering claim**.

The structural results of the previous revision were **re-derived from the
repository's own loader this session**, not inherited. Where this document
departs from them it says so.

---

## 1. Repository current-state audit

| item | value |
|---|---|
| HEAD | `9bc91a7` (merge of PR #36, run records) |
| branch | `main` |
| model under review | `adoc-literature-superset-v0.6.0` |
| `network.bnd` blob | `ee40f2a4e98f74a461dc308bf83323785eb45bb4` |

The blob equals the SHA the governing request names, so this plan and the
request address the same model bytes. Reproduce with
`git hash-object models/superset/adoc-literature-superset-v0.6.0/network.bnd`.

### 1.0a Why a document called "v0.5" analyses the v0.6.0 model

Three version numbers appear in this plan and they refer to different things.
Stating it once, because the filename invites exactly the wrong reading:

| number | what it names |
|---|---|
| **v0.6.0** | **the model this plan analyses** — the latest, and the one the request names by blob. Every structural result here is computed against it |
| **v0.5** | a **work line**, not a model. The 2026-09-30 pause is "scoped to the **v0.5 biological-topology and de-aliasing line**", which produced v0.5.0 through v0.5.2 and left the TI items this plan inherits. The request, and therefore this document, carry that name |
| **v0.4.0** | the model declared in `config/planned_design.yaml`, which is why the committed identifiability tables under `docs/design_alias/` describe v0.4.0 and not the current model (§3.4) |

**So "v0.5" is the name of the open work, and v0.6.0 is the code under it.** The
one place this genuinely bites is the third row: a reader who takes
`docs/design_alias/` as current is reading v0.4.0 figures, and an earlier
revision of §3.4 made that mistake. §3.4 now derives both and says which is
which.

**Working tree at session start:** five paths present but not in `HEAD` — the two
2026-10-21 review documents, `context/literature/supplements/`, the previous
revision of this file, and the request — and no file in `HEAD` modified. **No
commit, branch, merge or push has been made, and none is proposed.** The status of
the four artifacts this pass writes is stated once, in §11, in the review
subject's terms.

### 1.1 Governance in force, and what it forbids this pass

- The **2026-09-30 owner-endorsed pause** (`docs/v05_pause_decision_2026-09-30.md`)
  is scoped to *"the v0.5 biological-topology and de-aliasing line — proposals
  that would add, split, rewire or reinterpret nodes, edges, rules, thresholds or
  phenotypes on biological grounds"*. It is **in force**: §7.1 shows all three of
  its resume triggers are false today.
- `AGENTS.md` forbids editing anything under `data/`, forbids inventing rules,
  topology, thresholds, rates, phenotype definitions or mappings where evidence
  is absent, and requires literature-derived baseline topology to stay separate
  from data-derived personalization.
- The repository review gate (`cross_review = true`) reviews the exact final
  state of changed files.

### 1.2 Files this pass writes

Six artifacts across this pass: three modified in the state submitted and three
committed earlier on the branch. None is executable and none is a canonical
ledger. §11 gives the exact `git status` and distinguishes the two groups:

| path | what it is |
|---|---|
| `docs/v05_literature_guided_implementation_plan_DRAFT.md` | this plan |
| `docs/v05_literature_corpus_reconciliation_2026-10-21.tsv` | §2's reconciliation: digests, paths, ledger membership and which cluster adjudicated each paper |
| `docs/v05_traceability_identifiability_matrix_2026-10-21.tsv` | §5's matrix, 12 rows × 20 columns |
| `docs/v05_li2026_s2_roundii_screening_annex.tsv` | §4.9's 28-row screening annex |
| `.gitignore` | one added line, `context/literature/supplements/`, so the publisher workbook §4.9 reads cannot be committed by a `git add -A` |

No model, condition, protocol, calibration, observation-map, phenotype,
perturbation or canonical evidence ledger is touched. The `dropout_e2` pause is
not lifted and no frozen artifact is modified.

---

## 2. Source crosswalk

### 2.1 The obstacle the previous revision reported, and how it is removed

The previous revision removed every corpus-derived number, recording that the
request forbids commits and permits one file while the corpus is gitignored, so
no tracked artifact could reproduce a corpus claim. That reasoning conflated two
different things. What the gate requires is an artifact **in the review subject**
that reproduces the claim, and the review subject is computed from the working
tree rather than from the commit graph. The demonstration is this file's own
history: the previous revision was reviewed, and its findings acted on, before any
commit existed for it. A reconciliation table listing SHA-256 digests, relative paths and
ledger membership contains **no copyrighted content** and is therefore admissible
where the PDFs are not.

That table is `docs/v05_literature_corpus_reconciliation_2026-10-21.tsv`,
**160 data rows: 159 local-file rows plus one row for a registered file that is
absent locally** (§2.4). Every count below is a query against it.

### 2.2 The corpus as it actually is

| quantity | value |
|---|---|
| PDF files under `context/literature/pdfs/` | **162** |
| distinct SHA-256 digests | **161** |
| distinct articles (normalized stem) | **159** |
| articles in the 147-paper bundle screen | 147 |
| articles local but outside that bundle | **12** |

**The corpus grew during this pass, and these counts are the live tree.** Seven
PDFs arrived after the first snapshot, in three waves:

| arrived | paper | adjudicated in |
|---|---|---|
| 15:03 | Heng 2010, PC6-dependent BMP2 maturation (`10.1210/en.2010-0326`) — **the DOI the request §C names** | §4.6a |
| 15:04 | Paule 2021, PODXL and receptivity (`10.1093/humrep/deab032`) | §4.11 |
| 15:07 | Heng 2021, PODXL and epithelial impermeability (`10.1038/s41598-021-03425-2`) | §4.11 |
| 15:07 | Tamura 2024, nuclear actin and decidualization (`10.1038/s42003-024-06492-z`) | §4.12 |
| 15:48 | **Hewitt 2022**, progesterone signalling in endometrial organoids (`10.3390/cells11111760`) | §4.10 |
| 15:50 | Apostolov 2026, semaglutide at the embryo–endometrium interface — a **preprint** | §4.12 |
| 23:08 | **Heng 2021, *Fertil Steril***, PODXL with real human embryos and 81 biopsies — a **second, different** Heng 2021 paper | §4.11 |
| 10-22 | Yu 2026, SETD7 and decidual senescence | §4.13 |
| 10-22 | Yang 2026, NNMT and EZH2/H3K27me3 | §4.14 |
| 10-22 | Izmaylova 2026, DSG2 heterologous junctions | §4.15 |

Earlier revisions reported 152/151/149, then 153/152/150, then 157/156/154, as
the corpus grew under the pass. Each was correct when taken and all are
superseded by the table above, which is the live tree. **The lesson is worth more than the number:**
a corpus that grows during a pass makes any count a timestamped claim, which is
why every count here is a query against the reconciliation TSV rather than a
figure written into prose.

**Hewitt 2022 is now in the corpus and has been re-read from the PDF.** An
earlier revision adjudicated it from the publisher's open-access record, through
a model that could not see the panels, and recorded it as the one adjudicated
source with no local digest. Both are superseded: it has a digest, and §4.10
reports what the panels actually show, which is weaker than the web read
implied. **Every adjudicated source now has a local digest.**

Reproduce the file and digest counts with:

```sh
find context/literature/pdfs -name '*.pdf' | wc -l
find context/literature/pdfs -name '*.pdf' -exec sha256sum {} + | awk '{print $1}' | sort -u | wc -l
```

**Where those commands do and do not run, stated once and applying to every
corpus path in this plan.** `context/literature/pdfs/` and
`context/literature/supplements/` hold third-party published material and are
**not in version control**. The two commands therefore reproduce these counts
only in a working tree that holds the corpus; in a fresh clone, or in the harness
review snapshot, they return nothing. **The in-subject artifact is the
reconciliation TSV**, which carries a SHA-256 for every row — so every count
below is checkable against a committed-shaped artifact, and every *file* claim is
checkable by digest against a copy the reader holds, never by resolving a path.
This is the same constraint §2.1 is built around.

**The 147-paper screen's own arithmetic is correct and is not inflated.** It
states 125 main-library PDFs plus 24 in the PRL/IGFBP1/FOXO1 subset, less two
duplicates, giving 147. The local tree now holds **135** top-level files. Ten
exceed 125: Paule 2015 and Thathiah 2004, which the screen itself declares
outside the bundle; a second rendition of Retis-Resendiz 2024, which it declares
supplied separately; and the **seven** that arrived after the screen was written.
**All 147 screen rows match a local PDF; none is missing**, and the screen's page
numbers were remapped when the bundle was rebuilt.

Three stems carry more than one file. Marečková 2024 is byte-identical in both
locations. Rawlings 2021 and Retis-Resendiz 2024 are two different renditions of
the same article. These are the duplicates the screen already declares, so the
corpus contains no undeclared duplication.

### 2.3 The 163-paper September audit cannot be deduplicated, and why that is a finding

`context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md` is a synthesis
over *"163 PDFs in the Sofia bibliography archive"*. **It enumerates no
per-paper list**, and no artifact in the repository enumerates that archive. So a
DOI- or title-level overlap between the 147-bundle and the 163-corpus **cannot be
computed from anything the repository holds**, and this plan does not compute one.

Two consequences, both binding:

- **"310 distinct papers" is unsupportable** and is asserted nowhere here.
- The honest statement is: 156 distinct articles are present locally; the
  September audit's 163 are a separate and partly unknown set; the intersection
  is undetermined. Resolving it needs the Sofia archive's own manifest, which
  §10 requests.

### 2.4 Crosswalk against the canonical ledgers

| ledger | rows | present locally |
|---|---|---|
| `context/literature/pdf_manifest.tsv` | 64 | 63 |
| `context/literature/active_evidence_manifest.tsv` | 50 (48 with a digest) | 48 |
| union of both, by digest | 99 | 98 |

**A note on rows versus digests, so the table above can be checked against the
TSV without a false mismatch.** The TSV has 160 rows: 159 local files plus one
registered-but-absent entry. Its 158 distinct local digests become 156 distinct
articles because three stems carry two files each (§2.2). So the TSV shows 150
rows flagged `in_147_screen = yes` for 147 distinct articles, and 49 rows flagged
`in_active_evidence_manifest = yes` for 48 distinct digests. **The counts in the
table above are digest counts; the TSV's are row counts.**

**Three findings, each checkable:**

1. **`PDF-048` is a digest mismatch, not a missing paper.** The manifest
   registers Zhou 2021, *Jagged1 regulates endometrial receptivity in both humans
   and mice* (`10.1096/fj.202100590R`), with digest `17c81107…`, which matches no
   local file. **But the article is present locally**, as a different rendering
   with digest `0322711f…`. An earlier revision of this section reported the file
   as absent and said any claim resting on it was unverifiable locally; **both
   statements were wrong** and are withdrawn. The article is verifiable; what is
   unverifiable is the specific rendering the manifest registered. The
   reconciliation TSV now links the two rows in both directions through an
   `article_also_registered_as` field.
2. **61 articles are genuinely unregistered.** This count is stated at an
   explicit unit, because the three units differ and earlier revisions mixed
   them: **63 file rows, 63 distinct digests, 62 distinct articles** sit in
   neither digest-bearing ledger, and of those 62 articles **one — Zhou 2021 — is
   registered as `PDF-048` under a different digest** (finding 1), leaving
   **61 genuinely unregistered articles**. The 60-versus-59 gap is Retis-Resendiz
   2024, held in two renderings. Every figure in this paragraph is a query
   against the reconciliation TSV; earlier revisions quoted 52, then 56, as the
   corpus grew, and both are superseded. *A qualification on "unregistered": the test is
   membership of `pdf_manifest.tsv` or `active_evidence_manifest.tsv`, the two
   ledgers that carry digests. `references.tsv` carries none and cannot be
   crosswalked this way — Paule 2021 and Heng 2021 do have entries there, as
   `REF-013` and `REF-014`.* Reproduce all three counts from the `in_pdf_manifest`,
   `in_active_evidence_manifest`, `sha256` and `relative_path` columns of the
   reconciliation TSV.

   This is the material finding for evidence integrity, because **Cloke 2008 is
   among the 58** — a Track B primary this plan adjudicates in §4.7, unregistered
   in any canonical ledger. Heng 2010 is another, and so are both PODXL papers,
   which carry `references.tsv` entries but no digest-bearing registration.
3. **The two ledgers overlap in only 13 digests.** They are near-disjoint
   registries with different purposes, and neither alone describes the corpus.

### 2.5 Gate finding B7, independently reproduced

The previous revision contested B7, which asserted that `pdf_manifest.tsv` holds
58 DOIs rather than 64. The deferral was accepted. Reproduced here independently:

```sh
awk -F'\t' 'NR>1{n++; if($3!="")d++; if($3 ~ /^10\./)p++; if($14 ~ /^[0-9a-f]{64}$/)s++} \
  END{print "rows="n" doi_nonempty="d" doi_10prefix="p" sha256_valid="s}' \
  context/literature/pdf_manifest.tsv
```

gives `rows=64 doi_nonempty=64 doi_10prefix=64 sha256_valid=64`. All 64 rows
carry both a DOI and a valid digest. The contested claim was correct as written.

### 2.6 Corrections to the three supplied documents

| # | claim as supplied | correction | basis |
|---|---|---|---|
| C-1 | the 147 bundle and the 163 audit might be summed | they may not; the overlap is uncomputable from repository artifacts | §2.3 |
| C-2 | `mmc2.xlsx` / Table S2 is described as possibly unavailable | it was supplied as a file, not inside the three Markdown documents, and it is **held in the local working tree only** at `context/literature/supplements/Li_2026_Table_S2.xlsx`, untracked and absent from `HEAD`. Identified by digest `eef64eb6…`, not by that path | §4.9 |
| C-4 | six papers were flagged as *potentially missing* from the corpus | **five of the six were already present locally** — Paule 2021, Heng 2021, Heng 2010, Tamura 2024 and the Apostolov preprint; **Hewitt 2022 has since been added too**, so all six are now local. Most had arrived *after* the first corpus snapshot, which is why an earlier revision did not list them. A seventh paper also appeared, a **second** Heng 2021 on PODXL in a different journal, which falsified three statements in §4.11 | §2.2, §4.6a, §4.10–§4.12 |
| C-3 | the bundle is the readable source for figures | it is 72–100 dpi; every §4 adjudication below was run against the original PDFs, not the bundle | §4 |

---

## 3. Structural baseline

Every figure in this section is output of the repository's own loader, re-run
this session. No private Boolean auditor was written:

```sh
PYTHONPATH=src pixi run python -B -c "
from dt_adoc.reporting.structure import load_structure
s = load_structure('adoc-literature-superset-v0.6.0')
print(len(s.node_ids), len(s.free), s.enumerated_states, len(s.phenotype_inert))
print(s.alias_classes); print(s.never_binding_inhibitions); print(s.absorbed_edges)"
```

| quantity | value |
|---|---|
| nodes | 56 |
| free variables | 16 |
| enumerated states | 65,536 |
| distinct functions | 29 |
| alias classes | 7 |
| phenotype-inert nodes | 17 |
| unread inputs | 3 (`IN_XAV939`, `IN_HCG`, `IN_EMBRYO_CONDITIONED_SIGNAL`) |
| never-binding inhibitions | 5 |

### 3.1 Thirty-four of fifty-six nodes collapse into seven variables

The alias classes are the governing fact of this plan. Each row below is **one
variable**; the model cannot distinguish its members in any of the 65,536 states.
The seven classes cover **34 of the 56 nodes**; the other 22 are singletons, and
the model realises **29 distinct functions** in all.

| class | members |
|---|---|
| hormone cascade | `IN_PROGESTIN`, `E_PGR`, `E_IHH`, `S_PGR`, `S_NR2F2`, `S_BMP2`, `S_HAND2` |
| epithelial secretory arm | `E_SECRETORY_STATE`, `E_PAEP`, `E_PC6`, `E_DAG1_CLEAVED`, `E_MUC1_SLEX`, `E_HBEGF`, `E_SPP1_EXPR`, `E_ITGAVB3_5`, `E_ANXA2_ACTIN` |
| receptive-surface arm | `E_LIF`, `E_GP130_STAT3`, `E_CD98_CD9`, `E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE` |
| stromal decidual arm | `S_DECIDUALIZED`, `S_PRL`, `S_IGFBP1`, `S_SPP1`, `S_TAZ_ECM`, `OUT_STROMAL_DECIDUALIZED` |
| barrier arm | `E_PODXL`, `E_DAG1_FULL`, `E_MUC1_BARRIER` |
| contact | `E_CDH1_APICAL`, `IN_EMBRYO_CONTACT` |
| cAMP | `IN_cAMP`, `S_PKA` |

`E_RECEPTIVE_SURFACE` therefore reduces exactly to
`IN_E2 ∧ IN_PROGESTIN ∧ ¬E_KLF12_HIGH`.

### 3.2 The adhesive disjunction is entirely vacuous, and so is the barrier prefix

`absorbed_edges` reports that **all eight** disjuncts of `E_RECEPTIVE_SURFACE`'s
adhesive group are absorbed — `E_ANXA2_ACTIN`, `E_CD98_CD9`, `E_CDH1_APICAL`,
`E_DAG1_CLEAVED`, `E_HBEGF`, `E_ITGAVB3_5`, `E_MUC1_SLEX`, `X_SPP1_LUMEN_FREE` —
and that **all six** disjuncts of `X_ADHESION_ROUTE_REDUNDANT` are absorbed.
The redundant route is therefore exactly
`E_RECEPTIVE_SURFACE ∧ X_INTERFACE_REDUNDANT_RELAY`, and the two adhesion routes
differ **only** in which hand-set relay prior is ON.

Four of the five never-binding inhibitions feed `E_RECEPTIVE_SURFACE`
(`E_DAG1_FULL`, `E_ESTROGENIC_PROLIFERATION`, `E_MUC1_BARRIER`, `E_PODXL`); the
fifth is `X_ANTIADHESIVE_ROUTE → OUT_MATERNAL_ADHESION_COMPETENCE`. The reason is
in `complement_pairs`: `E_PODXL`, `E_MUC1_BARRIER` and `E_DAG1_FULL` are each the
**exact logical complement of `E_SECRETORY_STATE`**.

Two consequences carry into §7:

- **The anti-barrier prefix is dead.** Only `E_GP130_STAT3` binds. Describing
  `E_RECEPTIVE_SURFACE` as having a GP130 gate *and* anti-barrier requirements is
  half wrong at v0.6.0.
- **Barrier persistence is unrepresentable.** "Secretory epithelium that still
  carries a MUC1 barrier" cannot be written, because barrier ≡ ¬secretory by
  construction. This is exactly TI-06's subject, so **TI-06 is structurally
  blocked independently of its evidence condition**, and a repair confined to the
  adhesive disjunction does not unblock it.

A sharper claim appears in the previous revision — that seven of the eight
disjuncts individually reproduce the committed node and the smallest changing
deletion set has size seven. That is a minimal-sufficient-subset question, which
the loader does not answer and which needs an enumerator the repository
discourages. **It is not re-derived here and nothing below depends on it.**

### 3.3 No measured node can move any endpoint

`measured = {E_PAEP, S_IGFBP1}` — the two nodes with an activated row in
`config/observation_model_map.tsv`. **Both are phenotype-inert.** No node that
ADOC observes can move any `OUT_` node in any state. "Moves an observable"
therefore means "moves an unmeasured `OUT_` node", and `OUT_EPITHELIAL_RECEPTIVE`
is itself an alias of the hormone condition (§3.1).

### 3.4 Identifiability is worse than structure, and it is the binding constraint

Structural aliasing asks what the model cannot distinguish. Identifiability asks
what **the declared experiment** cannot distinguish, and the repository already
computes it. The four declared arms are untreated control, hormone-treated,
hormone-treated + mifepristone and anti-SPP1
(`docs/design_alias/planned_arms.tsv`).

**A version caveat that must come first, because the previous revision did not
make it and this plan nearly repeated the error.** The committed tables under
`docs/design_alias/` are **v0.4.0** artifacts: `config/planned_design.yaml`
declares `model_version: adoc-literature-superset-v0.4.0`, and
`pixi run render-design-alias` regenerates them against that declared model. Their
node count is 59, while v0.6.0 has 56. **Quoting them as the current picture
would be quoting another model version's counts**, which the governing request
explicitly forbids.

Both versions were therefore computed this session, with the same four declared
arms, via the model-version override the API already provides:

```sh
PYTHONPATH=src pixi run python -B -c "
from dt_adoc.reporting.design_alias import load_design_alias
f = load_design_alias(model_version='adoc-literature-superset-v0.6.0')
dc = f.design_class_of
print(len(dc), len({tuple(c) for c in dc.values()}), sum(1 for c in dc.values() if len(c)>1))"
```

| | v0.4.0 (committed tables) | v0.6.0 run of the same code |
|---|---|---|
| nodes | 59 | 56 |
| design classes | 19 | 15 |
| design-aliased nodes | 47 | 46 |
| largest indistinguishable class | 22 | 28 |

> **The v0.6.0 column is not a property of the v0.6.0 model or of the declared
> design, and an earlier revision of this section wrongly read it as one. The
> claims "identifiability is worse at v0.6.0" and "the 28-member class now
> absorbs the hormone inputs" are WITHDRAWN.**

**Why, verified this session.** At v0.6.0,
`hormone_treated_mifepristone.cfg`, `hormone_treated_anti_spp1.cfg` and both
`adhesion_challenge_*` counterparts are **byte-identical to their hormone-treated
baselines** — the perturbations moved to the intervention layer, so the condition
files no longer carry them. At v0.4.0 they differ
(`IN_MIFEPRISTONE.istate = TRUE`). `load_design_alias` partitions on condition-file
input states alone, so **the v0.6.0 run sees two distinguishable arm assignments,
not four**, and is being compared against a four-arm result.

The arithmetic confirms it exactly: the 28-member class **is** v0.4.0's 22-member
class, plus v0.4.0's five-member hormone-input class
`{IN_E2, IN_PROGESTIN, IN_XAV939, IN_cAMP, S_PKA}`, plus `X_SPP1_LUMEN_FREE` —
precisely the nodes that v0.4.0's mifepristone and anti-SPP1 arms separate. And
**E2, progestin and cAMP were already mutually indistinguishable at v0.4.0**, so
"now absorbs the hormone inputs" was wrong twice over.

This is the §3.5 enumeration gap biting the baseline rather than the candidate
arms, and it is the same insight applied one level further than the earlier
revision applied it. **A v0.6.0 identifiability figure comparable to the committed
tables requires applying the intervention layer, which the enumerator cannot do.
Until that exists, the committed v0.4.0 tables are the only four-arm picture this
repository holds, and §7's verdicts rest on the two classes below, which hold in
both runs.** For completeness, the class the two-arm run reports is:

> `IN_E2`, `IN_PROGESTIN`, `IN_cAMP`, `IN_XAV939`, `S_PKA`, `E_PGR`, `E_IHH`,
> `E_SECRETORY_STATE`, `E_PAEP`, `E_PC6`, `E_DAG1_CLEAVED`, `E_MUC1_SLEX`,
> `E_HBEGF`, `E_SPP1_EXPR`, `E_ITGAVB3_5`, `E_ANXA2_ACTIN`, `S_PGR`, `S_NR2F2`,
> `S_BMP2`, `S_HAND2`, `S_DECIDUALIZED`, `S_PRL`, `S_IGFBP1`, `S_SPP1`,
> `S_TAZ_ECM`, `OUT_STROMAL_DECIDUALIZED`, `X_MECHANICAL_PERMISSIVE_ECM`,
> `X_SPP1_LUMEN_FREE`

Both measured nodes sit inside that class, as they do inside v0.4.0's 22-member
class. **No conclusion in this plan rests on the two-arm figures.**

**Two classes decide several verdicts in §7, and they hold in both versions:**

- **`E_CDH1_APICAL` is design-aliased with `IN_EMBRYO_CONTACT`,
  `IN_EMBRYO_PRESENT` and `IN_TROPHECTODERM_COMPETENT`.** Even if the biology
  licensed separating apical CDH1 from contact, the declared design could not.
- **`E_CD98_CD9` is design-aliased with `E_GP130_STAT3`, `E_LIF`,
  `E_RECEPTIVE_SURFACE` and `OUT_EPITHELIAL_RECEPTIVE`** — the identifiability
  form of the D2/D3 refusal.

### 3.5 What a fifth arm would buy — and why the repository cannot currently answer that for v0.6.0

`docs/design_alias/candidate_fifth_arms.tsv` scores **112** candidate arms. Read
against its own model, v0.4.0, the ranking is:

| arm family | class gain | splits the CD98/GP130 class | separates the two measured nodes |
|---|---|---|---|
| `IN_HAND2_LOSS` on a hormone-treated background | +5 (largest) | **yes**, 5 → 3/2 | no |
| `dropout_IN_E2` (the `dropout_e2` family) | +3 | no | **yes** (`E_PAEP` \| `S_IGFBP1`) |
| `dropout_IN_cAMP` | +2 | no | **yes** |
| `solo_IN_PROGESTIN` | +3 | no | no |

**These numbers are v0.4.0's and do not transfer**, for a concrete reason.
v0.4.0 carries `IN_HAND2_LOSS`, `IN_MIFEPRISTONE` and `IN_ANTI_SPP1` as **MaBoSS
nodes**; v0.6.0 carries none of them, because the intervention layer now
expresses those perturbations outside the network. Recomputing the enumeration
against v0.6.0 returns **44 candidates with a maximum gain of +2, and no
HAND2-loss arm at all** — not because the perturbation became useless, but
because the enumerator walks free *nodes*, and that perturbation is no longer
one.

**This is a reportable tooling gap, and it is what makes U3 necessary rather than
duplicative: the repository's candidate-arm enumeration traverses only free
network inputs, so it omits v0.6.0's intervention-layer perturbations at any
model version. The committed tables are separately v0.4.0, because
`config/planned_design.yaml` declares that model; the code itself is not pinned
and runs against v0.6.0 on request.** The HAND2-loss condition
configs do exist in the committed v0.6.0 model —
`conditions/hormone_treated_hand2_loss.cfg` and
`conditions/adhesion_challenge_hormone_treated_hand2_loss.cfg`, declared in
`config/protocols_markerless.yaml` — so the arm is expressible; it is simply
invisible to the scoring code.

What survives the version change, and what this plan relies on:

- **`dropout_e2` is the pause's first resume trigger and the arm the frozen design
  was built around.** Its v0.4.0 scoring is the only quantitative statement
  available, and it is quoted as v0.4.0's. It is **not** the only family that
  separates the two measured nodes: **four of the six** `dropout_IN_cAMP` variants
  separate `E_PAEP` from `S_IGFBP1` too, at a gain of +2 rather than +3, while the
  two on a mifepristone background gain only +1 and separate nothing. An earlier
  revision called `dropout_e2` the only such family, contradicting this plan's own
  table; that is corrected here.
- **No single-perturbation design resolves any alias pair.** This is the headline
  of `docs/identifiability_experiment_design.md`, derived independently of the
  fifth-arm table, and the only two-arm design that resolves one does so at
  engagement level.
- **Nothing in either version's enumeration splits the CD98/GP130 class without a
  perturbation the current model cannot score.**

### 3.6 Condition-set fact used in §7

Across the 21 declared condition configs, `IN_EMBRYO_CONTACT` is TRUE in **9**
(the eight `adhesion_challenge_*` configs and `embryo_incompetent`) and FALSE in
**12**. The previous revision's correction of an earlier 8/13 reading is
confirmed. Reproduce with:

```sh
grep -H '^IN_EMBRYO_CONTACT' models/superset/adoc-literature-superset-v0.6.0/conditions/*.cfg
```

---

## 4. Primary-evidence adjudication (request §D.3)

**Method.** Eight clusters were adjudicated against the **original PDFs**, not the
compressed bundle and not the screening index, with `pdftotext -layout` and
figure/methods-level reading. For every claim four layers were kept apart —
interaction, direction, exact Boolean form, and relevance to a *measurable* ADOC
observable — together with species, system, compartment, molecular layer,
intervention, comparator, panel, and replicate structure. Contrary evidence
inside the same paper was recorded. Where a panel could not be resolved from the
text layer it is marked so rather than guessed.

Each subsection states only what its cluster establishes. Consequences for the
plan are drawn once, in §7.

### 4.1 GP130/STAT3 is not an obligatory gate — the hard conjunct is unsupported

**Nothing in this cluster tests GP130/STAT3 necessity for embryo adhesion to
maternal epithelium, and no genetic knockout of LIF, LIFR, IL6ST/gp130 or STAT3
exists in it.** Necessity needs a loss-of-function that abolishes the endpoint.
What the papers show instead:

- **Ak 2026 is the only shear-resisted embryo-adhesion endpoint in the cluster**
  (percentage of blastoids retained at 50, 100 and 400 µL/min on a
  patient-derived organoid-to-luminal monolayer, epithelium-only chip). SC144 at
  3 µM for 4 days collapses the maternal transcriptional programme — PAEP, GPX3
  and LIF itself — while adhesion is reduced **significantly only at 400 µL/min**
  (p = 0.01, n = 3), **not significant at 50 or 100 µL/min and not significant in
  AUC** (Fig 3A vs 3B). The authors read it as *"a supportive role in maintaining
  adhesion strength, rather than being essential for initial attachment."*
  The negative is strong rather than weak: SC144 is non-selective and also
  suppresses proliferation, metabolism and the E2 programme and shrinks organoids
  (Fig S5C/S5E), so the assay is **biased toward a false positive for necessity**
  and still returned none.
- **Marwood 2009 separates pSTAT3 from adhesion.** LIF raises pSTAT3 maximally
  (Fig 1B) and changes adhesion of primary first-trimester trophoblast to primary
  human EEC by **zero** (Fig 2C), while IL-11 raises it (p < 0.05, n = 5). Two
  GP130-family ligands, one shared receptor, opposite functional outcomes:
  **pSTAT3 is not sufficient**, and a single collapsing node cannot carry both.
  The STAT3 manipulation available is a dimerization-blocking peptidomimetic at
  20 µM, used in the **HES immortalized line only**, never in the trophoblast
  assay, with no western confirming pSTAT3 fell and no STAT1 control. It reduces
  and never abolishes, and **STAT3 inhibition alone leaves basal adhesion
  unchanged** — a direct counter-example to a gate.
- **The model's OFF state is not an adhesion null.** Non-induced epithelium —
  EPCX-free, MUC1-high — still retains 41.08 % ± 23.3 of blastoids at 50 µL/min
  (Ak Fig 2F, n = 6), and adhesive competence is already full at 2-day induction
  while PAEP peaks only at day 6 (Fig 3D/3G). Marker state and adhesive state
  decouple three independent ways.

  **This is not a progesterone-withdrawal result and is not cited as one.** The
  blastoids settle for 48 h in IVC-1 medium, which contains progesterone, so the
  assay **re-exposes the tissue to P4** whatever the epithelium's prior induction
  state. "Non-induced" here refers to the maternal induction protocol, never to
  an uninterrupted P4-free interval. No claim in this plan rests on Ak as a
  P4-free adhesion assay.

**Licensed:** GP130/LIF as a **contributor to adhesion strength under load** — a
rate modifier, or at Boolean level a disjunct inside the existing OR. **Not
licensed:** the AND-prefix.

**A boundary this plan holds, and an earlier revision blurred.** SC144 is a
pharmacological inhibitor at one concentration; it is **not a complete
loss-of-function** for GP130, and no knockout of LIF, LIFR, IL6ST or STAT3
appears anywhere in the corpus. So what the evidence supplies is **an absence of
support for necessity, not a demonstration of dispensability.** The committed
AND-prefix asserts necessity and is therefore **unsupported**; that is the
claim. Writing instead that GP130 has been shown to be *dispensable* would
overstate a non-abolition result from a partial inhibitor, and this plan does not
write it.

**A structural warning that belongs with this licence, not after it.** Moving
`E_GP130_STAT3` into the OR *on its own* does not reduce hormone-following — it
increases it. Computed this session over all 65,536 states: under that edit alone
`E_RECEPTIVE_SURFACE` becomes **exactly `IN_E2 ∧ IN_PROGESTIN`** and **joins the
secretory alias class, enlarging it from nine members to eleven**, carrying
`OUT_EPITHELIAL_RECEPTIVE` with it. Against the governing request's stated mission
of removing hormone-following aliases, R1-a alone moves the model the wrong way,
and it fails this plan's own §8.2 test 5. **R1 is therefore only defensible
jointly with R3-a1** (§5.1a), which is the configuration that makes every disjunct
live.

**A direct conflict to preserve, not smooth.** Marwood finds LIF does not change
trophoblast adhesion to endometrial epithelium in **primary** cells; Chung 2016
finds LIF increases JAr adhesion to Ishikawa. Same compartment, same ligand,
opposite sign, both carcinoma lines in Chung. No single Boolean edge may be
written over this.

**Two compartment errors found in the supplied reading.** Evans 2009 contains no
endometrial cell in its adhesion assay at all — it treats JEG-3 choriocarcinoma
with LIF and plates it on fibronectin or laminin (Fig 6) — yet its text concludes
"trophoblast–endometrium adhesion". And its cell-line arm needs PROKR1
overexpression because wild-type Ishikawa is unresponsive (Fig 1A). Chung's JAr
is choriocarcinoma, labelled "trophectoderm-derived".

**`E_CD98_CD9 = E_GP130_STAT3` is licensed by nothing in this cluster.** CD98 and
SLC3A2 appear **zero** times across all five papers. CD9 appears once, as a
negative-selection reagent used to deplete fibroblasts from the **embryonic-side**
preparation — not a maternal adhesion effector. The rule must be sourced from
Domínguez 2010 (§4.3) or withdrawn.

**Narrower licensed corrections.** Cullinan 1996 supports the LIF **ligand** half
of `E_LIF` descriptively, in the right species and compartment, but shows gp130
and LIFRβ are **constitutive across the cycle including the proliferative phase**
— so `E_GP130_STAT3 = E_LIF` can only mean pathway *activity*, never receptor
availability. Ak adds that SC144 lowers LIF itself, a feedforward the rule does
not represent. Evans adds hCG → PROK1 → LIF, an upstream embryo-dependent input
the committed rule omits entirely.

### 4.2 Apical CDH1 — the committed rule is contradicted, not merely unlicensed

This is the largest single correction this adjudication produces, and it runs
**against** the direction the previous revision assumed.

**What Ruan 2026 actually did.** Maternal side is **Ishikawa for every functional
experiment** (HEC-1B, AN3CA, OE-E6/E7 as comparators); primary EEC appear only in
immunocytochemistry, cycle-phase westerns (LH+2 n = 9 vs LH+7 n = 28) and outcome
westerns (live birth 29, not pregnant 30, RIF 10). The embryo side is a BAP-EB
spheroid from hESC. **Four real human blastocysts were used for
immunocytochemistry only and eighteen for spent medium; no real blastocyst was
ever attached to anything.** Endpoints: attachment percentage at 1 h after
centrifugation, spreading area at 24 h, and AFM rupture force.

**Effect size and Boolean form.** Blockade arms were run separately on the
embryonic side, the maternal side, or both, against a mouse-IgG isotype control.
Full bilateral blockade gives only about a **50 % reduction** in attachment. The
n and p-values for those blockade panels are **not resolvable from the PDF text
layer** and are not quoted here. That
licenses an **OR-disjunct or a strength modifier, never an AND gate.** The
paper's own junction-integrity control is partial: the acute washed-out antibody
arm is the only clean one and carries no TEER or ZO-1 readout, and the authors
concede the knockdown arm cannot be separated from global adherens-junction
disruption.

**The decisive finding: apical CDH1 is a regulated maternal state, and it exists
without an embryo.** Four independent demonstrations:

| observation | panel |
|---|---|
| E2 + P4 for 3 h raises surface CDH1 **in Ishikawa**, not primary EEC | Fig 3G, n = 5, p = 0.0079 |
| LH+7 exceeds LH+2 in primary EEC (total, not apical) | Fig 3F, p = 0.0020 |
| apical fraction higher in live-birth than RIF luminal epithelium | Fig 7C, 12 vs 7, p = 0.0278, a single uncorrected test |
| live-cell staining of untreated Ishikawa and untreated primary EEC | Fig 3C/3D |

and the embryonic inducer the paper identifies is **soluble** — conditioned
medium, blastocyst spent medium, hCG at 50 IU/L — acting, in the authors' words,
*"prior to its physical contact"*.

**One measurement caveat carried from the cluster report, because it limits how
hard the "apical" claim can be pushed:** the apical fraction is quantified in a
0.2–0.3 µm band, an order of magnitude below the 1.5 µm z-step of the imaging.
The *existence* of surface CDH1 is also shown by live-cell staining of unfixed,
unpermeabilized cells, which does not depend on that band; the *quantified apical
fraction* does.

**Therefore `E_CDH1_APICAL = IN_EMBRYO_CONTACT` is not a conservative placeholder.
It is contradicted by four panels of the very paper it cites, and it reads the
wrong input.** The repository already knows this: `context/literature/candidate-nodes.tsv`
records `E_CDH1_APICAL` with `logic_hint = IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL`
at confidence 7, labelled "Apical epithelial CDH1/CTNND1 state", carrying the note
*"Do not conflate apical adhesion CDH1 with lateral junctional CDH1."* The
committed `network.bnd` never implemented that hint. This is a **divergence
between the repository's own curated candidate logic and its committed rule**,
discoverable with no new literature at all.

**But fixing it buys no discriminability.** `E_CDH1_APICAL` enters the model in
exactly two places and both disjunctions are vacuous (§3.2), because
`E_CD98_CD9 = E_GP130_STAT3` already satisfies them. The node is phenotype-inert
**whatever it equals**. Correcting the rule is a provenance repair; the binding
constraint remains the CD98 identity.

**A second mapping defect, independently checkable.**
`config/node_entity_map.tsv` lines 28–29 union CDH1 and CTNND1 into
`E_CDH1_APICAL` with `any_of`. No panel supports that union: CTNND1 has strong
functional evidence (siRNA abolishes CDH1, p = 0.0059; cuts attachment,
p = 0.0040) but is **negative in live-cell surface staining** — it sits on the
cytoplasmic face and cannot be the homophilic ligand — and blastocyst spent
medium raises apical CDH1 while leaving CTNND1 unmoved (Fig 6D). CTNND1 is
upstream of integrin αV, a different node.

**Contrary evidence retained.** Kakar-Bhanot 2019 does **not** support trafficking
as a regulated receptive axis: Rab11a does not differ between pre-receptive and
receptive phase in fertile women (Suppl Fig S8), its E-cadherin effect is
**lateral, not apical**, and knockdown cells lose TEER and claudin-1, confounding
the attachment deficit. Peng 2021 and Ruane 2024 contain **zero** occurrences of
"cadherin"; both score **mouse** blastocysts on human carcinoma lines, and Peng's
48-hour endpoint is outgrowth, not initial adhesion. Whitby 2020 records the
canonical human position as E-cadherin **down**-regulated with adherens junctions
displaced, attributing apicolateral redistribution to rodent work, and Ruan itself
concedes the cycle-regulation literature is split. Ruan's title claim "in humans"
and its "represented endometrial receptivity" claim both overstate their panels.

### 4.3 CD98, CD9, integrins and HB-EGF — the merge is a model choice, not a measurement limit

**`E_CD98_CD9 = E_GP130_STAT3` has no evidential basis in either direction.**
Case-sensitive full-text counts give **zero** occurrences of `STAT3`, `Stat3`,
`gp130` or `GP130` in Domínguez 2010, Chung 2016 and Lessey 2002. No paper in
either cluster manipulates or even names the axis in connection with CD98. This
is now established from both ends (§4.1 from the GP130 side, here from the CD98
side).

**What Domínguez 2010 does establish, and what it does not.** Figs 4A and 4D are
the only **surface** panels — flow cytometry on primary human EEC at 48 h. The
legends state **independent experiments**, not donors, and this plan does not
upgrade them to donors. **hCG, E2, E2+P, LIF, NGF and EGF each raise surface CD98.**
LIF is therefore one of five sufficient inducers and necessity is never tested.
Two panel-level facts contradict the committed rule's shape:

- **Progesterone alone does not significantly change surface CD98; E2 alone
  does** — verbatim: *"Treatment with progesterone did not significantly alter
  the plasma membrane expression of CD98, while exposure to 17-β-estradiol
  induced a significant increase of CD98hc in primary endometrial cells"*
  (Fig 4A/4B). The committed rule inherits a progestin requirement through
  `E_SECRETORY_STATE = IN_E2 ∧ E_PGR` that this panel refutes.
- **TGFβ significantly reduces surface CD98** (Fig 4D) — an inhibitory input no
  rule encodes. IL-1β is null.

**Necessity is not shown.** The functional assay is mouse hatching blastocysts on
human HEC-1-A, and the perturbation is correctly maternal-side — lentiviral
overexpression and shRNA on the epithelial monolayer. But shRNA reached only a
30 % reduction in surface CD98, because more *"could not be attained without
impairing cell viability"*. Significant, partial, against a 70 % control
baseline. **The title word "Essential" is supported by no panel**, and the
repository inherits it at confidence `high` on a single reference.

**A constraint on calibration, from the paper itself:** a myc-CD98hc plasmid
raised CD98 **mRNA but not surface protein**. CD98 transcript does not predict
CD98 surface protein, so the node may not be calibrated from an ADOC `SLC3A2`
measurement.

**CD98 and CD9 are different evidence bases and should not be one node.** CD9
shows *"no significant differences throughout the menstrual cycle"* (Fig 2A)
while CD98 is window-restricted (Fig 2B); Table 1 gives CD98 a 6-fold rise in
receptive RL95-2 (p < 0.001) with CD9 flat and unmarked. The co-immunoprecipitation
is weak and the authors themselves suspect *"a different tetraspanin"*. Only the
adhesion phenotype is shared, which is a downstream effect, not a shared input.
`models/.../node_dictionary.tsv` compounds this by giving `E_CD98_CD9` the
semantics "CD98 **or** CD9" while declaring the observable "surface CD98 **and**
CD9".

**TI-03 is supported by three independent dissociations**, which is more than the
register currently records:

| dissociation | source |
|---|---|
| αVβ5 is absent from epithelium, stromal only after day 23 | Lessey 1996, 500+ biopsies |
| anti-αVβ3 blocks osteopontin adhesion; anti-αVβ5 does not | Apparao Fig 6 |
| PC6 knockdown lowers surface αVβ5 and leaves αVβ3 unchanged | Paule 2012 Fig 4 |

**The only evidence for merging them is Chung 2016** — qRT-PCR in two carcinoma
lines, whose abstract and schematic assert a plasma-membrane increase that is
**never measured** (no flow, no western, no immunofluorescence). It is the sole
surviving citation for that edge after two earlier references were retracted.

**Two further licensed findings the model does not carry.** Paule 2012 shows PC6
cleaves pro-integrin α5 and αV into heavy and light chains (Figs 5–8, n = 3,
confirmed in primary human EEC), licensing `αVβ5 ← PC6` and **explicitly
forbidding** `αVβ3 ← PC6`; the model has no PC6→integrin edge at all. And
Apparao Fig 7 **contradicts the sign of the surviving disjunct**: β3 protein is
*"induced primarily by HB-EGF and inhibited by E2"*, while `E_ITGAVB3_5` reduces
to `IN_E2 ∧ E_PGR`. That is one blot with no stated n, so it is recorded as an
**open conflict, not a flip**.

**HB-EGF.** Lessey 2002 is mRNA by RNase protection assay **only** — no protein,
no surface, and transmembrane versus soluble HB-EGF never distinguished. Its
epithelial panel (Fig 2A) does license `E2 ∧ P4`, but its **stromal** panel
(Fig 2B) — the compartment the paper argues is functional — gives `E2 ∨ P4`, and
the model has no stromal HB-EGF node. Fig 3C licenses a missing edge,
HB-EGF → LIF.

**The merges are choices, not limits.** All three nodes are `reported_only`;
CD98 and HB-EGF are phenotype-inert. But SLC3A2 and CD9, and ITGAV, ITGB3 and
ITGB5, are separately quantifiable. Every claim this cluster establishes
nonetheless lives at surface, cleavage or engagement layers that single-cell RNA
cannot reach.

### 4.4 Glycans: three epitopes, no MUC1 carrier, and a barrier that is wrong rather than merely vacuous

**`E_MUC1_SLEX` conflates three chemically distinct epitopes with a carrier none
of these papers identifies.** The epitopes are sialyl-Lewis-X (Ma, Yu; via
ST3Gal3 and FUT3), sialyl-Tn (Dong; via ST6GALNAC1) and Lewis-Y (Ma's control).
Ma Figs 3C/3D and 5D/5E show sLeX and LeY **moving independently** under two
perturbations in the same cells. Worse, **sTn is a truncated O-glycan that
terminates the very elongation sLeX requires**, so a single node imposes a
positive co-regulation the chemistry argues against.

**No paper in this cluster identifies MUC1 as the carrier of anything.** Ma and
Yu identify no carrier at all, measuring only bulk surface epitope; Dong
identifies CD44 and integrin β1, for a different epitope. **The `MUC1_` prefix
on `E_MUC1_SLEX` is unlicensed.**

**The decisive question — is any glycan route regulated independently of the
hormone state? — gets one weak candidate and one clear negative.**

- **Candidate:** FUT3/sLeX induced by IL-1β (Ma Figs 3C/3E, 4, 5), in medium with
  no steroid. But "independent" here means only *sufficient without hormone*, not
  *insensitive to hormone*: **nobody ran IL-1β × P4**. And the candidate is thin —
  one paper, one line (RL95-2), zero donors, no carrier, no receptor (L-selectin
  asserted, never tested), and its in vivo correlate is mid- versus early-secretory,
  i.e. hormone-phase confounded.
- **Negative:** sTn/ST6GALNAC1 is explicitly P4-driven — E2 alone no change, E2+P4
  up (Fig 3D), PR-A-dependent, with a progesterone response element and a PR
  ChIP-seq peak. **It is another alias of `E_SECRETORY_STATE`**; adding it would
  enlarge the nine-member alias class rather than break it.

**A species split that must not be crossed.** Dong's human data are
gain-of-function only — roughly 50-fold lentiviral overexpression in AN3CA, a
**non-receptive** line, with anti-sTn having no effect in vector cells.
**Necessity exists only in mouse.** And the mouse receptor Siglec-G is the
ortholog of human **SIGLEC10, not SIGLEC6** — the paper says so. The maternal
ligand side transfers; the trophectoderm receptor does not.

**An unresolved contradiction in the same cell line, to preserve:** Ma Fig 4 has
IL-1β **lowering** ST3GAL3 while sLeX rises; Yu Fig 2 has ST3Gal3 knockdown
**lowering** sLeX. These cannot both hold under a single-signed edge. Note also
that Yu's knockdown also lowers proliferation, PCNA and cyclins and strips
microvilli, so its adhesion loss is not isolated from a general cell-state
defect; and that Dong's own 2024 Introduction states there is **no** literature
associating any sLeX-glycogene deficiency with implantation failure in human or
animal models — written after Yu 2018, by an overlapping author group.

**The most consequential finding in this adjudication: the barrier arm is not
merely vacuous (§3.2), it has the wrong carrier and the wrong sign.**

| finding | panel |
|---|---|
| MUC16 knockdown gives **3.8× more** trophoblast adhesion (p < 0.01), while MUC1 knockdown at 87 % protein reduction gives **no effect** | Gipson Fig 6E |
| MUC1 is present on the luminal surface in **12 of 12** receptive-phase biopsies | Gipson Table 1 |
| MUC16 mRNA does **not** fall at mid-secretory and **rises** at late secretory; loss is luminal-only, glands retaining it in 6 of 12; within the luminal surface it is uterodome/secretory cells, ciliated cells retaining mucin | Gipson Fig 3 |
| higher progesterone associates with **higher** luminal MUC16 | Liu 2020 cohort II (confounded by advanced dating) |

So `E_MUC1_BARRIER = ¬E_SECRETORY_STATE` encodes a loss the data contradict, and
attributes to MUC1 a function the one functional panel assigns to MUC16.

**The licensed replacement shape** is a **MUC16** barrier cleared at the
**surface without an expression change**, restricted to the luminal/uterodome
compartment — that is, explicitly **not** the logical complement of
`E_SECRETORY_STATE`. This is the first candidate in this plan that would make the
anti-barrier prefix and `X_ANTIADHESIVE_ROUTE` **non-vacuous**.

**But it does not satisfy TI-06.** Gipson's biopsies contain no embryo. The
clearance is uterodome-associated and uterodomes are progesterone-dependent, so
the timing still tracks the hormone phase. **No embryo-local, perturbationally
established clearance determinant is supplied by this cluster**, and a new barrier
node must not be driven from `IN_EMBRYO_CONTACT` on this evidence.

**Unrepresented and reasonably evidenced, with a species caveat this plan states
because it states them everywhere else:** Berneau Figs 4F/4G — removing hyaluronan
from the **epithelial apical surface accelerates** stable attachment, while
embryo-side treatment does nothing, with converging in vivo sheep data. **The
embryos are mouse blastocysts on a human epithelial line**, so the maternal side
is human and the embryonic side is not. An apical
glycan acting as a **brake**. Conversely, CD44 blockade only *delays* attachment
(caught up by 36 h) and CD44-null mice are fertile, so Boolean necessity for CD44
is excluded. (Caveat: Gipson's ECC-1 is STR-reported Ishikawa-derived, so Gipson
and Berneau are not two independent maternal systems.)

**ADOC relevance of this entire cluster: zero.** Nothing in it maps to an active
ADOC observation; all of it bears on unmeasured `OUT_` nodes.

### 4.5 MUC1 — the barrier rule has the sign backwards, and TI-06 is not discharged

**`E_MUC1_BARRIER = ¬E_SECRETORY_STATE` is contradicted, not merely unsupported.**
Four independent human datasets put MUC1 **up** in the secretory/receptive state:

| finding | source |
|---|---|
| whole-biopsy mRNA about 2× up at day 21 of a hormone-replacement cycle | Meseguer Fig 3 |
| protein up by immunohistochemistry, mainly glandular | Meseguer Figs 4–5 |
| full-length luminal MUC1 **persists** through mid-luteal and in conceptive cycles | DeLoia Fig 1, glycosylation-independent antibody |
| progesterone dose- and time-dependently raises MUC1 protein ~1.7–1.9× and promoter activity 1.8–2.3× in two lines | Horne Tables 1–3, Fig 4 |

The single contrary measurement is Ak Fig 1J's 26.7 % reduction, with n = 2
replicates and a p-value pooled over cells, and its authors flag the conflict
themselves. **No evidence supports a clean complement in either direction.**

**TI-06 stands.** It requires a perturbationally established **local
embryo-contact** clearance determinant. The two local observations — Meseguer
Fig 10 (n = 3) and Ak Fig 4J (n = 5) — are single-antibody immunofluorescence of
contact sites with **zero perturbation**, and both papers attribute part of the
local signal loss to epithelial displacement or apoptosis at the implantation
site. The only paper holding MUC1-removal tools is Thathiah, and it has **no
adhesion endpoint at all**, identifies **no sheddase** (its one genetic test was
uninformative: both wild-type and null failed to shed), and found **LIF, IL-1β,
HB-EGF and hCG all negative**. And — weighted correctly rather than decisively — the
same paper reports that **human blastocyst-conditioned medium also failed to
stimulate MUC1 shedding**. That statement sits in the Discussion, is attributed
*"(Thathiah, A., M. Meseguer, C. Simon, and D. D. Carson, **unpublished
observations**)"*, and the authors themselves offer an alternative reading — an
embryonic stimulus with a limited active lifespan, or too dilute in culture to
detect. **It carries no panel weight** and is recorded here as an unpublished
negative, not as evidence.

**Meseguer's own perturbational panels point the opposite way from the hypothesis
they are cited for.** A human embryo present during apposition **raises** EEC MUC1
more than twofold at both mRNA (Fig 8) and protein (Fig 9), and the authors
concede this *"argues against"* embryo-driven glycocalyx reduction. The deferred
register already records this direction; the adjudication confirms it at panel
level.

A caution on the one genuine dose-by-time hormonal perturbation: Horne's
progesterone effect is **just as large in HEC1B, which that paper itself
documents as PR-negative**, and the discrepancy is unaddressed. So the effect is
real but **must not be wired to `E_PGR`**.

So the correction the literature licenses is **deletion or re-specification, not
inversion**. The naive sign flip — which the deferred register already refuses —
remains refused, now on primary evidence rather than on principle.

**A cleaner finding underneath it, stated with its source level explicit because
§4.4 reaches the opposite conclusion from a different evidence layer.** DeLoia
Figs 2–3 show the secretory-phase change in human luminal MUC1 is a change of
**glycoform** — keratan sulphate and sialic acid accumulating on a core protein
whose abundance is unchanged. On that panel alone, `E_MUC1_BARRIER` and
`E_MUC1_SLEX` would be one molecule in two glycoforms, and modelling them as two
nodes with **opposite** dependence on `E_SECRETORY_STATE` would be a modelling
artefact.

**The step that would complete that argument is not panel-supported.** That MUC1
specifically carries sialyl-Lewis-X in endometrial cells is asserted in
**Meseguer's introduction**, i.e. secondary citation, not measured in any paper in
either cluster — and §4.4 establishes from the glycan papers that **no paper
identifies MUC1 as the carrier of any epitope**. The two subsections are therefore
not in conflict once the layers are named: DeLoia establishes *glycoform change on
MUC1*, and the glycan cluster establishes *no identified carrier for sLeX*. **What
is licensed is that the barrier node and the glycan node are not independent; what
is not licensed is that MUC1 is the sLeX carrier.** The `MUC1_` prefix on
`E_MUC1_SLEX` stays unlicensed either way, and R3-b's MUC16 shape and a
graded-MUC1-glycoform shape remain **alternatives, not a settled choice** — see
the discriminating observation named below. What the
evidence would license is **one node with a graded glycosylation state**, which
Boolean form cannot carry. DeLoia also notes added keratan sulphate should make
MUC1 **more** anti-adhesive, not less.

**An open disagreement between clusters, preserved rather than resolved.** §4.4
finds the one functional mucin panel assigns the barrier effect to **MUC16**, not
MUC1 (MUC16 knockdown 3.8× more adhesion; MUC1 knockdown at 87 % protein
reduction no effect). This cluster finds MUC1 itself is progesterone-**induced**.
The two agree the committed sign is wrong and agree the naive flip is refused.
They do **not** jointly determine which mucin the node should name, and this plan
does not decide it.

**On the function question MUC16 wins uncontested, and it is worth being precise
about what is actually open.** Gipson Fig 6E is the **only functional test of
either mucin in this corpus**, and it is matched within one paper: MUC16 siRNA at
86 % knockdown raises trophoblast adhesion about 3.8-fold (n = 6, p < 0.01),
while MUC1 siRNA at 87 % knockdown gives no statistical difference. §4.5 supplies
**no functional counter-evidence**, because its only paper with MUC1-removal
tools has no adhesion endpoint at all.

**What blocks naming MUC16 in the node is therefore not a competing MUC1 result.**
It is three things: the result rests on a single system (Gipson's ECC-1 is
STR-reported as Ishikawa-derived, so it and Berneau are not independent maternal
systems); the mechanism is post-transcriptional and uterodome-restricted, which a
Boolean node expresses badly; and a **conditional** objection to the MUC1 null, which this plan must not state
as a fact because §4.4 establishes the opposite. **If** MUC1 carries
sialyl-Lewis-X in this system, then knocking it down removes an anti-adhesive
mucin and an adhesion-promoting glycan carrier together, and two opposing
contributions could cancel. **That antecedent is unestablished**: no paper in
either cluster identifies MUC1 as the carrier of any epitope, and the only
assertion that it does sits in a review introduction. So the cancellation
argument is a **hypothesis that would have to be tested, not a reason the panel
is unreliable**, and it is removed from the decision.

**What actually withholds the MUC16 naming, then, is narrower than an earlier
revision implied:** single-system dependence, and a post-transcriptional
uterodome-restricted mechanism a Boolean node expresses badly. Settling either
the carrier question or the cancellation hypothesis needs a
**glycoform-selective** perturbation, which no paper in this corpus performs.

**Two negatives that constrain future units:** LIF produced no MUC1 shedding at
10 or 100 ng/mL (Thathiah Table 1), so routing the LIF arm into barrier removal
via MUC1 has an explicit negative against it; and the HES line's provenance
should be authenticated before any shedding mechanism becomes load-bearing.

### 4.6 PC6 — a quantitative modifier, on an evidence base that is one experiment wide

**PC6 hormonal regulation is not tested in any of the four PC6 papers in this
cluster** — no steroid is ever applied. (A fifth PC6 paper, Heng 2010, does apply
steroids, but in the **stromal** compartment; see §4.6a. The epithelial gap
stands.) Activity *is* separable from expression (PolyR perturbs
activity alone; substrate abundance and processed fraction move independently),
but every activity tool used is pan-PC rather than PC6-selective.

**`E_PC6 = E_SECRETORY_STATE` is not tested in any of the four PC6 papers.**
Every causal experiment runs in HEC1A or Ishikawa under ordinary culture with no
hormone control, and in HEC1A α-dystroglycan cleavage is constitutive and
essentially complete. The committed rule rests on a cycle-phase expression
correlation sourced outside this cluster.

**`E_DAG1_CLEAVED = E_PC6` — direction correct, strength overstated.** Heng 2015
is the cluster's best evidence: a cleavage-site point mutation abolishes the
adhesion gain for laminin, fibronectin and BeWo spheroids (Fig 8, n = 4). But it
is gain-of-function over dystroglycan **overexpression**, the endpoint is 2-hour
spheroid attachment, and the mutant line sits **at control level, not below it**
— so "intact α-DG is a barrier" is the paper's prose, not its panel.

**`E_DAG1_FULL = ¬E_PC6` is refuted as a complement.** In human tissue α-DG-N
intensity is **unchanged** between phases, only the N/C ratio falling (Fig 5N);
in uterine lavage α-DG-N is present in **every sample in both phases** (Fig 6);
and at 50 % knockdown membrane retention and continued release occur
**simultaneously** (Fig 3B/3C). The same partial-processing picture holds for
integrin-α5 and PDGF-A. **Processing is a ratio, not a switch** — the same
Boolean-expressivity limit as the MUC1 glycoform.

**PC6 is not a unique gate on anything.** PDGF-A is a documented **furin**
substrate; the activity assay used to attribute the knockdown phenotype is a
**pan-PC** fluorogenic substrate; the primary-cell validation uses PolyR, a
polybasic **pan-PC** inhibitor presented as "a known PC6 inhibitor" with no
selectivity data. A 50 % knockdown yields a 43–60 % reduction in attachment,
never abolition. **What is licensed is a quantitative modifier, not a hard AND.**

**Substrate by substrate, only one cleavage is shown to change a function.**
α-dystroglycan is that one: cleavage removes the N-terminus and unmasks the
adhesive central region. Integrin α5 and αV show processing, with function
established only at the level of PC6 itself. PDGF-A shows cleavage with **no
functional endpoint anywhere**, and is a known furin substrate. EBP50 is the
weakest: cleavage is demonstrated only on a 31-amino-acid synthetic peptide, the
in-cell band shift was explicitly unresolvable, and **PC6 is a secretory-pathway
protease while EBP50's cleavage site is cytosolic** — a topology the paper never
addresses, although its title asserts the mechanism.

**A fragility finding that bears on every PC6 claim in the repository.**
Heng 2015's "PC6 knockdown reduces blastocyst adhesion" **is** Heng 2011 Fig 2E,
cited as a reference — no new adhesion experiment. Paule 2012 and Paule 2015
reuse the identical Heng 2011 stable PC6-siRNA HEC1A line. **All four PC6 papers in this
cluster therefore share one siRNA sequence, one clone pool and one cell line, with
no rescue and no second knockdown reagent anywhere** — and that remains true of
the **epithelial** evidence arm after Heng 2010 is added (§4.6a), because Heng
2010 is stromal and pharmacological. Any systematic off-target
effect of that single construct propagates through the entire PC6 evidence base
— EBP50, α-DG, integrins and PDGF-A alike. Paule 2015 adds a substrate but no
function, and its title's "in preparation for embryo implantation" is carried by
no implantation, adhesion or attachment endpoint in the paper.

### 4.6a Heng 2010 — the paper the request named, now read

This paper arrived in the corpus mid-session (§2.2) and is the DOI the governing
request §C flags as possibly needed for *"a **specific** stromal PC6→mature BMP2
mechanism"*. It was adjudicated separately. The request asked for three things —
inhibitor specificity, dosage, and temporal ordering — and **all three come back
negative**.

**What it establishes.** In human primary endometrial **stromal** cells from
three donors, a proprotein convertase cleaves the BMP2 pro-domain at a
`KREKR282↓` site, raising mature BMP2 (Fig 4B western, Fig 4C secreted-mature
ELISA), and recombinant PC6 cleaves a synthetic 16-mer but not its
`KREKR→AAAAA` mutant (Fig 5). The functional tie is to **PRL secretion only**
(Fig 3) — not SMAD signalling, **and there is no adhesion or attachment endpoint
anywhere in the paper**.

**Three negatives that cap what it licenses.**

- **Specificity.** The inhibitor is nona-D-arginine, cited to the authors' own
  reference titled *"…potent inhibitors of PC5/6 **and PC7**"*. PC7 is expressed
  in these cells and unchanged, and **no PC7 control was run**. "PC6 was
  primarily responsible" is not separable from PC7 by any panel.
- **Dose.** 0.1 µM inhibits decidualization by about half in cells (Fig 3B), at a
  dose giving no detectable inhibition of recombinant PC6 in the tube — where
  about half needs 1 µM. **The cellular endpoint is ten-fold more sensitive than
  the catalytic target**, which the paper does not discuss and which does not
  exclude an off-target or polycation effect.
- **Time.** A single 72-hour endpoint for BMP2 against PRL loss beginning at 48
  hours. **No ordering is established**, so maturation loss cannot be shown to
  precede the arrest.

**It changes the shape of §4.6's fragility finding without dissolving it.** This
is genuinely a different system — primary stromal cells and a pharmacological
inhibitor, with **no siRNA and no HEC1A** — and it carries the only rescue in the
set. But the two halves are different compartments with different endpoints, so
**the epithelial `E_PC6` arm is still one siRNA clone pool wide with no rescue**,
and all five PC6 papers come from one laboratory. §4.6's statement stands for the
epithelial rule; it is now explicitly scoped to it.

**It is the only steroid exposure in the five-paper PC6 set** (E2 + MPA +
8-Br-cAMP, PC6 mRNA about six-fold up, Fig 1B) — and it still **cannot support
`E_PC6 = E_SECRETORY_STATE`**, because `E_PC6` is declared epithelial and this is
stromal, and because there is no progestin-alone, E2-alone or cAMP-alone arm. The
epithelial steroid gap stands and this paper neither supports nor refutes a
progesterone-specific determinant.

**A layer caution for any rule text citing it:** the paper measures BMP2 **protein
forms and never BMP2 mRNA**. It licenses nothing about BMP2 *induction* — only
*maturation*.

**Consequence for R4, which is why it was read.** It bears on the `S_NR2F2`
disjunct only mildly, and in the direction §4.8 already argues: one more human
BMP2 measurement made under E2 + MPA + cAMP with **no progestin-alone arm**.
NR2F2 itself is never measured or perturbed here.

**It does argue for an edge the model lacks entirely — a stromal
`S_PC6_ACTIVE → S_BMP2` maturation route — and that edge is behaviourally
non-identifiable.** A stromal PC6 node would be driven by the same stimulus the
model already encodes as `S_PGR ∧ S_PKA`, so

```
S_BMP2 = (S_PGR and S_PKA and S_PC6_ACTIVE) or S_NR2F2
```

is **truth-table identical to the committed rule — zero nodes differ across all
65,536 states**, verified this session.

**But truth-table identity is not trajectory identity, and an earlier revision
called this candidate "behaviourally null" on the strength of the first.** That
was wrong. The candidate **adds a node**, so it adds a dimension to the state
space and an update step: in a hormone-treated state with `S_PGR` and `S_PKA` on,
`S_NR2F2` off and `S_PC6_ACTIVE` off, the committed `S_BMP2` is enabled
immediately, while under the candidate `S_PC6_ACTIVE` must transition first.
Under asynchronous update that is a **delay**, and it can move transient
probabilities and the order in which nodes arrive. The enumerator this plan uses
computes fixed-state columns and says nothing about trajectories.

**The distinction, stated once because it governs three candidates.** An edit
that changes no node's Boolean function **and introduces no new variable** leaves
the transition system identical — that is R3-a1, which is why its
prediction-identity claim survives this correction. An edit that changes a
function changes trajectories too, which is R1. An edit that **adds a variable**
can be truth-table identical and still change trajectories, which is N4. Only the
first is a genuine no-op.

So N4 is **evidence-supported, identifiable by no fixed-state comparison, and not
demonstrated to be trajectory-neutral**: it belongs in the
evidence ledger, not in `network.bnd`, and it does not become identifiable until
BMP2 is split into expression and active states — which nothing in this corpus
licenses.

This is the cleanest instance in the plan of the category the governing request
asks to be kept open: a literature-supported mechanism admissible as an
explicitly uncertain candidate, which **current ADOC measurement cannot identify
and which ADOC observations have therefore neither validated nor calibrated**.

### 4.7 PRL and IGFBP1 are mechanistically non-identical, and no Boolean rule follows

**Direct differential evidence exists, and it is good.** The cleanest separator
is **Kane 2010 Fig 4**: SMAD 4 siRNA — two independent target-specific sequences,
with MAPK and unrelated-sequence controls, **n = 5 endometrial samples in
triplicate**, primary endometrial stromal cells. The legend is explicit:
depletion *"had no significant impact on the TGFβ1-dependent reduction in
IGFBP-1 mRNA or protein … but reversed the reduction in PRL mRNA (p < 0.001) and
protein (p < 0.01)"*. One perturbation, opposite outcomes, at both molecular
layers.

*Prose-versus-panel note, recorded because this plan flags such gaps elsewhere:*
the paper's **abstract** softens this to *"did not fully restore expression of
IGFBP-1"*, which would read as partial restoration. The **figure legend reports
no significant impact**. This plan follows the panel.

**Three qualifiers that travel with it, and must travel into any register row.**
(i) The IGFBP-1 arm is a **negative result with no power analysis, so
"SMAD-independent" is an untested null at n = 5** — the same objection this plan
raises against Cloke's IGFBP-1 null, and it applies here too. (ii) **All cells
were cultured in MPA throughout**, and the authors state they are unable to reject
an indirect route via TGFβ1-mediated PR suppression. (iii) The literature the
authors themselves cite reports TGFβ1 *increasing* PRL. So the separator is the
cleanest in the cluster and is still **not** "primary and figure-verified" without
these three riders.
A second separator **in this cluster** is **Cloke 2008 Fig 1A**: DHT raises PRL
but not IGFBP-1
secretion on a cAMP + P4 background in primary stromal cells, supported by
dose-response, bicalutamide and AR siRNA arms — though the IGFBP-1 null in that
panel is statistically untested. *"Second" counts within this cluster only. The
corpus holds five separators in all, two of them in the PRL/IGFBP1 primary-
verification register rather than in this section; §4.12 carries the inventory
and U2 states it once on the TI-04 row.*

**So `S_PRL = S_IGFBP1 = S_DECIDUALIZED` should stop being presented as
evidence-based. It is a modelling convenience and it is false as biology.**

**And yet no Boolean rule is licensed.** The two strong separators act through
**TGFβ1/SMAD4 and AR/DHT, neither of which is in the model's alphabet**. The one
separating axis that is in the alphabet — PR activity — fails against primary-cell
evidence: Retis-Resendiz 2024 reports RU486 raising PRL with no effect on IGFBP1
and cAMP alone maximal for PRL, but that is T-HESC immortalized cells, mRNA only,
24 h, H89 at 10 µM which is not PKA-selective, with RU486 and MPA not
receptor-selective and the paper's Results and Discussion contradicting each other
about Fig 5A. At longer horizons in primary cells the sign reverses: Tamura 2014
Fig 1 shows cAMP **alone** induces IGFBP-1 by day 4, and Cloke Fig 1A shows P4 is
positively required for **sustained** PRL. Writing `not S_PGR` into a PRL rule
would switch PRL ON in the untreated state, which every paper in the cluster
contradicts — the same failure the earlier `PRL = PKA` / `IGFBP1 = PKA` refusal
already rejected.

**No onset-timing difference between the two genes is demonstrated anywhere in
the cluster.** Every time course moves them together. So not even a rate
difference is established, only non-identity of mechanism.

**Corrections to the supplied dossier.**

- **Tamura 2014 is unifying, not separating.** C/EBPβ occupancy and H3K27ac were
  measured at **both** promoters; both rise on cAMP, both collapse on C/EBPβ
  knockdown, both respond to HDAC inhibition. Its differential is PRL and IGFBP-1
  together **versus Mn-SOD**. The dossier lists it among the separation evidence.
- **Buzzio 2006's differential is not robust.** Its siRNA explicitly co-targets
  FOXO3A, there is no rescue, and overexpression raises **both** genes (Fig
  2B/2C); Grinius 2006 finds PRL and IGFBP-1 both down 60–81 %.
- **Cloke's AR-versus-PR siRNA comparison does not separate them.** Fig 3B shows
  AR and PR knockdown attenuate PRL mRNA equally, there is no IGFBP1 arm in Fig 3,
  and neither gene appears in Tables 1–5.

**Not licensed: an `S_PKA → S_PGR` edge.** Retis-Resendiz supports PGR
*transcript* only, in a cell line, with a non-selective inhibitor.

**Not licensed: reading the ADOC observation mapping as node activity.** Kane is
the cleanest refutation — in stromal cells the secreted protein falls about 46 h
**before** the mRNA (Fig 1B vs 1A), and in decidualized cells the mRNA falls with
**no** protein change (Fig 3A vs 3B). `AGENTS.md` already forbids equating
secretion with node activity; this cluster supplies the primary demonstration.

**TI-04 is untouched.** Nothing in this cluster is an ADOC measurement, so there
is no tension between the deferral and the evidence. The register's blocker is
identifiability, and §3.1 shows why: the only ADOC-measured stromal observable is
logically identical to the stromal phenotype it would have to test.

### 4.8 WNT, DKK1, BMP2 and TGFβ1 — no new node, but one committed rule is contradicted

**No DKK1, WNT4 or PROK1 node is licensed.** Each would be an alias of an input
the model already has:

- **DKK1 would reduce to `S_PGR` *under a rule written from the model's existing
  inputs only*** — Tulac 2006 has P4 inducing DKK1 at mRNA, lysate and secreted
  layers in primary stromal cells while cAMP and E2 do not, at an IGFBP-1-matched
  cAMP dose, with RU486 and withdrawal reversing it, and Cloke 2008 Table 3
  confirms by PR siRNA at −2.05. So a DKK1 node drawn with the inputs the model
  has would join the seven-member `IN_PROGESTIN` class.

  **That is a statement about the model's input alphabet, not a biological
  identity, and this plan does not confuse the two.** DKK1 is additionally
  controlled by PROK1 (Macdonald 2011) and by TGFβ1 (Kane 2008), neither of
  which the model carries, and the contradiction matrix below shows its sign is
  not even consistent across compartments. **DKK1 is not biologically identical
  to PGR activity; it is currently *inexpressible apart from it*.** Those are
  different findings with different remedies — the second is fixed by adding an
  input, not by adding a node.
- **WNT4 = `S_PGR ∧ S_PKA`**, logically identical to the reduced
  `S_DECIDUALIZED`. Its only non-redundant driver is AR, for which the model has
  no input.
- **PROK1** is the only candidate with a non-hormonal driver (hCG, via Evans
  2009), but the model has no hCG-to-stroma route and Macdonald's stromal
  knockdown is run under MPA + cAMP anyway.

**The DKK1 contradiction matrix — four experiments, no common sign.**

| # | system / compartment | manipulation | direction |
|---|---|---|---|
| a | primary human stromal cells | P4, RU486, withdrawal | P4 **induces** DKK1; cAMP and E2 do not |
| b | PROKR1-Ishikawa (**epithelial**) and decidua explants | PROK1 → DKK1 via Gq/Ca/calcineurin/NFAT; DKK1 siRNA | DKK1 is **anti**-proliferative in epithelium but **required** for stromal IGFBP1/PRL/IL11 |
| c | JAr (**embryonic** trophoblast surrogate) | recombinant DKK1 applied to **JAr**, 2 days | β-catenin falls **in spheroids, not in Ishikawa** (their own Fig 5E) |
| d | HESC | adenoviral DKK1 **over**expression | blocks IGFBP1/PRL |

Rows (b) and (d) are loss- and gain-of-function **in the same compartment with
the same markers, both reducing the endpoint** — non-monotonic and
un-Booleanisable. Li 2013's authors concede decidual DKK1's significance
*"remains unclear"*. **Liu 2010 is confirmed as an embryo-side experiment**: the
Ishikawa maternal monolayer is never treated and co-culture runs 1 h in
DKK1-free medium, so it is not a stromal loss-of-function and its direction may
not be read as a maternal one. Its late-secretory cycle peak also conflicts with
the mid-secretory peaks in Tulac 2003 and Macdonald 2011.

**BMP2→WNT4 is an oversimplification by its own data.** Li 2013 Fig 2C shows
BMP2 co-inducing **DKK1, DKK2 and SFRP3** alongside WNT4 — and the paper then
uses forced DKK1 as its Wnt blocker. Li 2007 is **mouse** for every causal
experiment; its human half adds recombinant BMP2 on top of E+P+cAMP with no
human knockdown and no condition without cAMP. The human loss-of-function is in
the companion Li 2013 (WNT4 siRNA, overexpression, and a BMP2-cannot-rescue
epistasis) — real, but decidual-marker biology inside a cAMP cocktail.

**The Kane 2008 dissociation holds only partly.** PR suppression is
SMAD4-dependent (Fig 7A-II, 7D, n = 6 donors, two siRNAs). DKK1 suppression is
SMAD4-independent **at the secreted-protein layer only** (Fig 7C); the mRNA panel
(7B) points the other way and is dismissed in prose, and Fig 4A states the mRNA
effect is gone by 48 h, contradicting Fig 7B at 72 h. The abstract also claims
anti-TGFβ1 restored DKK release while the Results heading and Fig 5B legend say
it had no effect.

**What this cluster establishes about a committed rule — and it is an absence,
not a licence.** The `S_NR2F2` disjunct in `S_BMP2 = (S_PGR ∧ S_PKA) ∨ S_NR2F2`
makes BMP2 true on **progestin alone**, discarding the cAMP requirement. Every
human BMP2 induction measurement in this cluster uses E + P + cAMP and **none
tests progestin alone**.

**An earlier revision read that as licensing removal of the disjunct, "restoring
the cAMP requirement every human measurement actually used". That inference is
invalid and is withdrawn.** A bundled treatment with no component-withdrawal
comparator cannot identify any component as necessary: observing BMP2 induction
under E + P + cAMP shows the bundle suffices, and says nothing about whether cAMP
is required. Licensing `S_BMP2 = S_PGR ∧ S_PKA` would need either a human
progestin-alone arm that fails, or a human cAMP-withdrawal arm that abolishes.
**Neither exists in this corpus.**

The evidence is in fact mildly against removal: the **only** progestin-alone
measurement anywhere in the cluster is Li 2007 Fig 1A, it is **mouse**, and it is
**positive** — P4 alone induces BMP2 there. So the disjunct is supported by
mouse evidence and untested in human, while its removal is supported by nothing.

**R4-b cannot be treated as independent of this, and an earlier revision missed
that.** `S_NR2F2 = E_IHH ∧ S_PGR` and `S_BMP2 = (S_PGR ∧ S_PKA) ∨ S_NR2F2`, so the
disjunct is true on progestin alone **only because `E_IHH = E_PGR`**. Any R4-b
form that breaks that identity changes progestin-alone BMP2. Verified this session
over all 65,536 states, counting states with progestin on and cAMP off:

| rule | progestin-alone states with `S_BMP2` OFF |
|---|---|
| committed | **0** of 16,384 |
| R4-b as a sign flip, `E_IHH = ¬E_PGR` | **16,384** — identical to R4-a |
| R4-b as a free input | 16,384 of 32,768 |
| R4-a explicit, drop the disjunct | 16,384 |

**So a sign-flip R4-b enacts exactly the R4-a edit this section withdraws as
supported by nothing, on IHH evidence that says nothing about BMP2.** That is a
governance hole, not a modelling nicety: the withdrawn change would re-enter under
another identifier without ever being adjudicated.

**Consequence for R4-b's specification.** It may not be registered as "remove or
demote `E_PGR → E_IHH`" alone. Either it is specified so that progestin-alone
`S_BMP2` is **preserved** — which requires naming a replacement for the `S_NR2F2`
disjunct and therefore re-opens R4-a — or its unblock condition explicitly covers
the BMP2 consequence and it stays blocked until R4-a is resolved. **This plan takes
the second branch**, because the first would decide R4-a by the back door.

**The correct status is UNRESOLVED in both directions**, and that is what this
plan records. What is licensed is the narrower statement that the human evidence
base cannot adjudicate this disjunct at all, and that a progestin-alone or
cAMP-withdrawal human arm is the measurement that would.

**Adhesion relevance: none.** The cluster is decidualization-marker and
proliferation biology throughout, except Liu 2010, whose only adhesion endpoint
manipulates the embryo. **Nothing licenses an edge into `E_RECEPTIVE_SURFACE`,
`X_ADHESION_ROUTE_*`, `X_ANTIADHESIVE_ROUTE` or
`OUT_MATERNAL_ADHESION_COMPETENCE`.**

**A secondary keeper for the observation layer, not for topology:** DKK1's
progestin-dependence and cAMP-independence is the one discriminating fact here,
and it is a candidate future **observation** mapping that would separate
`IN_PROGESTIN` from `IN_cAMP` — **but only under a design that varies the two
independently**, which no declared arm does: in all four they co-vary.

### 4.9 Li 2026 Table S2 — screening hypotheses, with no effect sizes

**Provenance, stated so it cannot be mistaken for a repository artifact.** The
workbook is a **publisher supplement held only in the local working tree**, at
`context/literature/supplements/Li_2026_Table_S2.xlsx`, digest
`eef64eb64fc75606e3fec77462ad55837ed8361a75952c49ae5d456071b3e011`. It is
**untracked and not in `HEAD`**, and this plan does **not** propose committing it:
it is third-party published material of the same kind as the PDFs the governing
request requires to stay out of version control.

**The consequence is that the path does not resolve for anyone who does not hold
the file** — not in a fresh clone, and not in the harness review snapshot, which
materializes tracked content plus the files in scope. An earlier revision wrote
"the workbook **is present**", which is true only of this working tree and read as
a repository claim; that wording is corrected here. **What is independently
checkable is the digest**: anyone holding the supplement can confirm it is the
same file, and the annex records that digest in every row.

The Round II sheet resolves to **28 hits across three donor panels — RIF-29th 10,
RIF-44th 7, RIF-60th 11** — confirming the 10/7/11 split the dossier reports. The
28-row annex is `docs/v05_li2026_s2_roundii_screening_annex.tsv`, and it carries
its own lineage: source path, source SHA-256, sheet name, the source row each
entry came from, a description of the extraction, and an explicit
`source_availability` field recording that the parent is untracked. It records the **screen stage explicitly** — the
48-hour Round II outgrowth endpoint, which is neither the Round I CCK-8 viability
screen nor an adhesion assay — and the donor panel verbatim. Compound names are
kept **raw** in one column and normalized in a separate one, so no source value is
silently altered.

Two caveats are structural to the workbook itself and are recorded in the annex:

- **The sheet carries no effect column.** Its fields are catalogue metadata —
  compound, synonyms, CAS, molecular weight, supplier-annotated target and
  pathway, solubility, batch, SMILES, vendor URL, research area, clinical status.
  **No efficacy estimate exists in S2 to quote**, and none is invented.
- **The "Target" field is supplier annotation, not observed mechanism.** K2EDTA
  appears in the RIF-60th panel annotated "DNA/RNA Synthesis"; it is a chelator
  and anticoagulant. That row is flagged as an identity-QC item and is a warning
  about the whole column.

**No rule, rate, node or edge may be changed from this annex.** It ranks as
screening hypotheses only.

### 4.10 XAV939 is not an adhesion gate, and `E_PGR → E_IHH` is refuted for human

**XAV939.** No paper demonstrates it as a direct adhesion gate. In all three
papers it is one component of a bundled differentiation medium, and **the bundle
is the experimental unit in every adhesion assay**.

- **The RSPO1 confound is confirmed verbatim in Garcia-Alonso 2021**, twice:
  Fig 7a's legend and the Methods both state that R-spondin-1 *"was omitted from
  ExM in the presence of WNT inhibitors"*. XAV939 at 2 µM and RSPO1 withdrawal are
  perfectly confounded and no arm separates them. That paper has **zero** adhesion
  or embryo endpoints.
- **Kagawa 2022 and Ak 2026 have the opposite design**: RSPO1 is **retained** in
  the base medium, and XAV939 is added on top as one of four components — a
  correction for an exogenous culture agonist, not a physiological signal.
- **Kagawa Extended Data Fig 8d is marker-only** — qRT-PCR of window-of-implantation
  markers, n = 2 independent experiments, no statistics, with an internally
  inconsistent replicate statement. **There is no EPC-versus-EPCX attachment arm
  anywhere in Kagawa**, so XAV939's contribution to attachment is unidentifiable;
  the headline contrast is non-stimulated versus E2-then-EPCX (Fig 4b, n = 7
  experiments across 3 donors). Kagawa's attachment endpoint carries **no applied
  shear**. Its Fig 4e SC144 arm is an **embryonic-side** manipulation on
  trophospheres and is easy to misassign to the maternal side.

**Recommendation: do not wire `IN_XAV939`.** Beyond the confound, it appears on
**both** the embryonic priming side and the maternal side, so a single global node
would be a maternal/embryonic compartment misassignment. Annotate it as an
unwired culture-protocol input — silence the lint, not the biology.

**`E_PGR → E_IHH` is contradicted for human, and the contradiction is about the
INPUT more than the sign.** Stated carefully, because the two parts carry
different weight: the **estrogen induction is robust** — 16 to 73-fold, all three
donors, plus two independent atlases placing IHH in the proliferative-phase
compartment and the canonical mouse paper's own note of a human decline. The
**progestin suppression is donor-dependent**, annotated in one donor, obtained
with an antagonist that is not PGR-specific, in a system its authors call
progesterone-incompetent. **This plan therefore claims a wrong input, not a
universal human sign reversal**, and §4.10 records the distinction.

- Garcia-Alonso 2021 places IHH in SOX9+ LGR5− cells of the **basal glands**,
  within a population *"enriched in the proliferative phase … rising estrogen
  levels"*.
- Marečková 2024 reports that the SOX9 functionalis II population *"distinctly
  expressed KMO, IHH and EMID1"*, and separately that *"during the secretory
  phase, the SOX9+ populations were markedly reduced"*. Both strings are verified
  in the PDF. (Note the two atlases are not fully independent: Marečková
  partially re-integrates Garcia-Alonso's data.)
- **Franco 2010 — the canonical mouse Ihh paper — records the human decline in its
  own Discussion**: *"In the human endometrium, expression of IHH … decreases from
  the early to mid secretory phase."*
- Wang 2018 is **mouse** (Sox17/Ihh enhancer deletion, incomplete IHH loss); its
  only human data is a bulk SOX17–IHH mRNA correlation with no hormonal contrast
  and no compartment resolution, equally explained by both genes tracking the
  proliferative compartment. Wang 2020 reports IHH **zero** times — a null from a
  curated panel, not an independent contradiction.
- **Hewitt 2022, now read from the local PDF rather than from a web record, and
  downgraded in the reading.** An earlier revision declined it, then adjudicated
  it from a summary of the publisher's page by a model that could not see the
  panels. The paper is now in the corpus and the panels have been checked. It is
  a perturbation experiment in **human endometrial epithelial organoids**, with
  four arms and no others: vehicle; E2; E2 then E2+MPA; and RU486+E2+MPA.

  | claim | verdict against the panel |
  |---|---|
  | E2 induces IHH | **holds, and robustly** — 16 to 73-fold, across all three donors |
  | MPA inhibits that induction "in two of three donors" | **the phrase is verbatim in the text, and the figure does not carry it.** A significance bracket for E2 versus E2+MPA exists in **donor 1 only**; donors 2 and 3 are unmarked |
  | RU486 reverses the inhibition | holds in-panel, **donor 2 only**, with no RU486-alone control |
  | there is no MPA-alone arm | **confirmed, and absolute** — no progestin-without-E2 arm exists for any gene in any assay |

  **Three qualifications that change how much weight this can carry.** The
  "n = 3 samples per group" are **culture replicates within one donor**, not
  biological units, and passage is never reported. RU486 at 1 µM antagonises the
  glucocorticoid receptor as well, so "PGR-dependent" overstates what the arm
  shows; "sensitive to a steroid-receptor antagonist" is what it supports. And
  **Figs 1a and 1b do not reproduce each other**: in 1a donor 2 is unmarked for
  E2 versus E2+MPA, while in 1b, a separate run of that same donor, the same
  comparison is marked and the E2 fold-change differs about two-fold.

  **The paper's own headline is a negative result about its system**, which an
  earlier revision did not report. E2+MPA versus E2 yielded only 102
  differentially expressed genes, "mostly attenuation"; organoid PGR binds
  distally and does not occupy the PGR sites seen in biopsy. The authors
  conclude verbatim that *"the current culture condition of endometrial organoids
  is not sufficient to investigate PGR regulation of gene expression"*. A
  progestin claim drawn from this system inherits that caveat.

  **So what survives, and it is enough — as a wrong input, not a sign reversal.**
The committed rule `E_IHH = E_PGR`
  makes IHH progestin-driven. Hewitt shows IHH is **estrogen-driven**, robustly
  and in every donor. **The rule has the wrong input**, and that is the part this
  plan now rests on. The progestin-attenuation sign is real in direction but
  rests on one annotated donor in a system its authors call
  progesterone-incompetent, so it is recorded as supporting and not as decisive.
  Note also that only **MPA** was ever applied, while the title and abstract say
  "progesterone".

  **Two further contradictions, recorded and not actioned.** `E_PGR =
  IN_PROGESTIN` is refuted on the expression reading, since PGR transcript is
  itself E2-induced and MPA-reduced here; and on the ligand-activated reading the
  supported form would be `IN_E2 ∧ IN_PROGESTIN`, which makes
  `E_SECRETORY_STATE = IN_E2 ∧ E_PGR` a tautology. Neither is actioned: one
  organoid paper that disclaims its own progestin competence is not grounds to
  move a committed rule.

  **NR2F2, BMP2 and HAND2 appear nowhere in the article**, and there is no
  stromal compartment at all, so the epithelial-to-stromal bridge gets no support
  here.

- Li 2011 is **mouse**, HAND2 is **stromal** and P-induced, and its endpoint is
  epithelial **proliferation**, not adhesion. Its Figs S7/S10 add a sharp negative:
  Ihh and Nr2f2 are **unaffected** in Hand2-null uteri, so an intact IHH→NR2F2 arm
  is **not sufficient** for the progesterone antiproliferative outcome.

The structural stake is high: `E_IHH = E_PGR` is one of the identities collapsing
`{E_IHH, E_PGR, IN_PROGESTIN, S_BMP2, S_HAND2, S_NR2F2, S_PGR}` into one variable.
Removing it breaks a tautology rather than damaging the model.

**And Hewitt makes R4-b's entanglement with R4-a worse, not better.** Any
corrected `E_IHH` that is not constantly true under progestin — whether written
on the robust estrogen-induction finding or on the weaker attenuation term — is
the sign-flip case §4.8 computes, turning `S_BMP2` off in all
16,384 progestin-alone states and reproducing the withdrawn R4-a edit. **The
better the IHH evidence gets, the more urgently R4-a must be resolved first**,
because writing the licensed IHH sign into the model silently decides a question
this plan records as unresolved. Hewitt cannot resolve it either: it has no
MPA-alone arm.


---

### 4.11 PODXL — the best-evidenced barrier node, and its committed form is still wrong

**Three** papers bear on `E_PODXL = ¬E_SECRETORY_STATE`, a rule this plan had
analysed structurally and never adjudicated biologically. They must be kept
apart by journal, because **two are by Heng in 2021** and an earlier revision of
this section conflated them:

| paper | what it adds |
|---|---|
| Paule 2021, *Hum Reprod* | the overexpression clone pair; cycle-phase IHC; spheroid attachment and penetration |
| Heng 2021, *Fertil Steril* | **real human embryos** on the same clones, and **81 IVF endometrial biopsies** |
| Heng 2021, *Sci Rep* | transepithelial resistance, dextran flux, junction proteins, transcript panel |

**The evidence base is one clone pair, across all three.** **None of the three
papers performs a PODXL loss-of-function** — no siRNA, shRNA, CRISPR, antibody
block, enzymatic removal or rescue anywhere; the *Fertil Steril* paper's own
journal field reads "Intervention(s): N/A". All three rest on a **single stable
overexpression clone pair** in Ishikawa, made in Paule 2021 and re-used by
explicit citation in both 2021 papers. The *Sci Rep* paper adds new readouts and
**no new experimental condition**; the *Fertil Steril* paper does add conditions,
and an earlier revision of this section wrongly denied it. **No primary
epithelial cells are used in any functional assay in any of the three.** The
same laboratory and the same clone platform produced the PC6 papers (§4.6), so
the single-construct fragility finding extends across both arms. The lab owns a
stable-knockdown platform and did not apply it here.

**The effect is modulation, it converges, and what persists is depth rather than
adhesion.** With spheroids (Paule Fig 5): 25→6 % at 1 h, 45→10 % at 2 h,
65→28 % at 4 h, 68→24 % at 6 h, and **no difference at 12 h or 24 h**. With
**real human embryos** (*Fertil Steril*): 64 % versus 27 % retained at 15 h
(p = 0.025, 11 embryos per arm), and at 24 h **both arms reach 78 %**. *That 24-h
null is reported as "data not shown", and §4.5 refuses an unpublished negative
elsewhere in this plan. It is used here only because it agrees with Paule's
independently published 12-and-24-hour convergence; on its own it would carry no
weight.* Penetration persists in both: volume down
about 60 % in Paule, about 70 % at 24 h in *Fertil Steril* (**p < 0.01** as the
legend gives it, n = 5 embryos per arm), yet **every spheroid penetrates by
48 h**.

Endpoints are retention after gentle washing — three washes in Paule, three to
four pipette strokes in *Fertil Steril*, neither quantified — and a confocal
penetration volume. **No shear is applied anywhere in the cluster.** The n count
embryos or culture replicates of one clone, never donors; the *Fertil Steril*
paper never reports how many donor couples supplied the embryos. Paule's
abstract drops the 12-to-24-hour convergence, and the *Fertil Steril* abstract
drops the hedge its own title carries.

**Q-A, lateral versus apical: confounded in every arm.** The only directly
measured barrier properties are transepithelial. Heng 2021 shows transepithelial
resistance up (p = 0.0034, n = 3), 40 kDa dextran flux down (p = 0.001, n = 5),
and junction transcripts and proteins up with explicit localization "to cell
junctions". The apical-blocking hypothesis rests on chromogenic
immunohistochemistry plus an analogy to the podocyte glycocalyx. **No
apical-versus-lateral partition was ever measured**, PODXL was never localized
on the Transwell geometry where resistance and flux were run, and there is no
truncation mutant, no sialidase arm, no junction-protein epistasis and no
rescue. **The two mechanisms are not separable from this evidence**, and this
plan does not choose between them.

**The complement form is refuted on three independent grounds, two of them new.**

1. **Between compartments.** Paule Fig 2B: luminal PODXL falls at mid-secretory
   (p = 0.013–0.020), **glandular falls only late** (p = 0.044), **endothelial
   never falls**. One compartment-free node cannot be the complement of a
   secretory state when three compartments in one tissue diverge at one
   timepoint. The *Fertil Steril* cohort confirms the endothelial limb in **81
   biopsies**, 3.5 times Paule's cohort.
2. **Within the luminal compartment.** In that same cohort, **22 of 81 (27 %)
   histologically mid-secretory biopsies retain a PODXL-positive luminal
   epithelium.** A complement rule says the barrier is absent whenever the
   secretory state is present; in a quarter of dated secretory samples it is
   present. This is the sharpest refutation and it does not depend on the
   compartment argument at all.
3. **Gradedness.** The fall is graded, with "limited luminal staining still
   evident" — the *Sci Rep* introduction escalates this to "below detection",
   overstating the panel it cites. And the hormonal arm
is MPA on an E2 background with **no E2-versus-vehicle arm**, so it says nothing
about the `IN_E2` half of `E_SECRETORY_STATE`; transcript falls at 72 and 96 h,
total protein only at 96 h, and **no surface measurement exists anywhere** — no
biotinylation, no live-cell flow, no non-permeabilized staining.

**No support for treating the three barrier nodes as one class.** MUC1, MUC16 and
dystroglycan are **not measured** in any of the three. Paule's own Discussion offers
PODXL as a **replacement** for MUC1 rather than a classmate, which is a further
source against `E_MUC1_BARRIER` (§4.5).

**No apical CDH1 unmasking, and the measurement does not exist.** Overexpression
*increases* E-cadherin, junctional and lateral by the authors' own wording; the
**apical pool was never measured**. So the barrier and the adhesive route are
shown neither independent nor entangled, and this plan records the absence
rather than a finding.

**Two sign conflicts with committed rules, recorded and not resolved.** SPP1 is
**up** in the overexpressing clone (Heng Table 1) against `E_SPP1_EXPR =
E_SECRETORY_STATE`; and junctional CDH1 is **up** in an explicitly non-receptive
state. `ITGAV` and `ITGB3` appear in no differential list, so `E_ITGAVB3_5` gets
neither support nor refutation, and `HBEGF` is absent.

**A structural result that changes how the vacuity should be read.** Computed
this session over all 65,536 states: `E_PODXL` is read at `E_RECEPTIVE_SURFACE`
as a never-binding inhibition and at `X_ANTIADHESIVE_ROUTE` as a disjunct.
Endogenously it can never bite, because it is the exact complement of the state
the GP130 gate requires. **But clamped ON it abolishes adhesion competence
entirely — `OUT_MATERNAL_ADHESION_COMPETENCE` falls from 1,920 states to zero.**

So the repository's own curated expectation for this node, recorded in
`candidate-nodes.tsv` as *"Forced ON should suppress adhesion competence"*, **is
exactly right — and is satisfiable only by an intervention, never by the model's
own dynamics.**

**But a clamp and the experiment are not the same claim, and the gap is the
point.** A permanently ON anti-adhesive Boolean gate predicts a **persistent
veto**: competence is zero and stays zero. What the papers show is **partial and
time-dependent** — attachment reduced at 1 to 6 hours and **converged by 12 to
24 hours**, with penetration still reduced after attachment has caught up.
**The committed formalism can represent the direction of the initial inhibitory
perturbation and nothing else about this phenotype.** Three quantities are
conflated by one Boolean and must be kept apart in any future unit:

| quantity | what the papers show | can v0.6.0 express it? |
|---|---|---|
| initial attachment probability or rate | reduced | **no** — Boolean has no rate |
| attachment persistence | **not** reduced; converges by 12–24 h | **no** — the clamp never releases |
| subsequent epithelial penetration | reduced, and persists past convergence | **no** — no penetration variable exists |

**No physical MaBoSS timescale is assigned here.** `duration_units` is
`relative_only`, so "12 to 24 hours" is a property of the experiment and not of
any model quantity, and converting one into the other would need a calibration
this plan neither has nor proposes. That is a sharper diagnosis than "the prefix is vacuous": the
barrier is **fully potent as a perturbation and wholly inert as a state**. It
also means the committed model *can* represent what Paule and Heng actually did,
since overexpression is an intervention; what it cannot represent is a barrier
arising from hormonal history.

**Contrary evidence inside the clinical arm, which the plan records because it
bounds the claim.** The proportion of PODXL-positive luminal epithelium **does
not differ** between patients with fewer than three and three or more prior
failed cycles, which the authors concede argues against an endometrial
aetiology for repeated failure. And the marker is neither necessary nor
sufficient: **18 % of PODXL-positive patients conceive and 47 % of
PODXL-negative patients do not.** The authors themselves offer a timing
alternative, that a PODXL-positive endometrium "may simply need a longer time to
reach receptivity" — which is a rate claim, not a gate claim, and Boolean form
cannot carry it. Against all of that, the *Fertil Steril* Discussion calls
PODXL downregulation "essential", a necessity claim with **no loss-of-function
anywhere in the cluster**.

**What this licenses.** Interaction and direction are genuinely supported, and
are the best-evidenced part of the anti-barrier arm — now including an arm with
real human embryos and an 81-patient cohort, which is more than any other
barrier node has. The **complement form is
refuted** on compartment, gradedness, kinetics and molecular layer. ADOC
relevance is **nil**: PODXL is unmapped in the observation layer and the endpoint
are wash-retention and penetration volume, not shear-resisted adhesion. The
cluster also asserts a
PODXL→LIF negative edge the model lacks entirely — in the model they are
parallel siblings of `E_SECRETORY_STATE`, which is part of what makes the prefix
vacuous — but on transcript-only evidence from two clonal populations, far too
thin to move topology. **On governance, R5 is not TI-06's to govern, and this plan says so rather than
borrowing.** TI-06 is written specifically for the `E_MUC1_BARRIER` correction:
its forcing evidence is Meseguer's MUC1 panel, and its unblock conditions name a
**local embryo-contact clearance determinant for MUC1**. PODXL is a different
molecule with a different mechanism — the papers here argue transepithelial
impermeability, not local clearance at a contact footprint — so TI-06's
conditions are not the right test for it and satisfying them would not license
R5.

**R5 therefore needs its own recorded conditions**, and on this adjudication they
are: a **loss-of-function** in primary human epithelium, since all three papers
are overexpression from one clone pair; a **surface-level** measurement, since
none exists; an arm **separating apical occupancy from lateral junction
integrity**, which no experiment attempts; and a representation decision about
the three quantities tabulated above, since a Boolean gate cannot carry the
observed time dependence. Writing those into the register is U2's job. **The
2026-09-30 pause applies to R5 regardless of which TI item owns it.**

### 4.12 Does the model need states distinct from transcript abundance?

The question is whether one Boolean per entity, standing for "expression", is
adequate. Two late-arriving papers bear on it, one peer-reviewed and one a
preprint.

**First, a framing correction. Tamura 2024 does not measure decidualization
reversal against transcript.** Its withdrawal experiment (Fig 2a–c) measures
**only** the percentage of cells carrying a nuclear actin network, falling from
71.1 ± 5.5 % to 20.5 ± 1.8 % over 144 h of recovery. **PRL and IGFBP1
transcripts are never measured at any recovery timepoint**, and the
reversibility of the decidual programme is *cited* rather than shown. So the
stimulus-withdrawal framing cannot answer the dissociation question, and this
plan does not use it for that.

**The dissociation is real but comes from a different experiment.** Under a
dominant-negative nuclear actin, of the 709 genes cAMP normally upregulates
**646 still rise and only 63 fail**, while of the 618 it normally downregulates
**304 fail to be repressed** (Fig 4b). In the same perturbation, cell-cycle
arrest is **abolished**: the cell-number ratio moves 1.15 → 1.55 (Fig 5a) and
Ki67 positivity 4.5 % → 8.5 % (Fig 5b). So a decidual **function** is lost while
most of the induction programme survives.

**Stated honestly, because the paper's own summary overstates it.** Fig 3b from
that same perturbation shows IGFBP1 at ~0.4 and PRL at ~0.55 of control, both
p < 0.01 by targeted qPCR, which the RNA-seq significance cut does not call. The
accurate reading is **induction partially impaired at roughly 40–60 % of normal,
repression and arrest abolished** — different magnitudes of response to one
perturbation, not a clean all-or-nothing split.

**What that licenses, and how far.** It licenses that `S_DECIDUALIZED` **must
not be alias-identical to `S_PRL` and `S_IGFBP1`**: one perturbation, implemented
two independent ways, moves arrest and the marker arm by different amounts, so
they are not one variable.

**It does not by itself determine two discrete Boolean states, and this plan
separates those two claims.** What the panels show is a **quantitative**
difference — arrest abolished, induction retained at 40 to 60 percent — and a
quantitative difference fixes no binarization threshold. Committing to two
Booleans additionally requires a stated threshold rule and a reason that
threshold is the right one, neither of which this evidence supplies and neither
of which this plan invents. **The licensed object is two distinguishable
biological processes; two discrete model states are a design proposal resting on
them.** On that reading the stromal arm plausibly needs **two states where the
model has one**: a commitment-and-arrest state and a marker arm,
separated by a single perturbation implemented two independent ways. The
hierarchy is proven rather than assumed — the dominant-negative does not affect
cAMP-induced C/EBPβ at mRNA or protein (Suppl Fig 6a/6b), so the arc runs
C/EBPβ → assembly and not the reverse. Note this licenses **necessity for arrest
only**; for the markers nuclear actin is a **modifier**, not a gate.

**What it does not license: separating PRL from IGFBP1.** Four panels measure
both and in all four they move **together, in the same direction**. Tamura 2024
therefore joins Tamura 2014 (§4.7) as **unifying** evidence. **TI-04 stays
deferred.**

> **Correction, 2026-10-22.** This paragraph previously ended *"and Kane 2010's
> SMAD4 knockdown remains the only separator in the corpus."* **That is false and
> is withdrawn.** §4.7 of this same document already names Cloke 2008 Fig 1A as a
> second separator, and
> `context/literature/reviews/prl_igfbp1_foxo1_2026-09-22.primary-verification.tsv`
> holds two more: `PIF-003` (Buzzio 2006 — IGFBP1 down while PRL up, the
> opposite-direction pattern, on an siRNA that co-targets FOXO3A) and `PIF-004`
> (Ujvari 2017 — IGFBP1 collapses while PRL is unchanged, recorded there as the
> cleanest de-aliasing signal in the corpus). Konyushatova 2025 adds a fifth
> (delta §3.5). **The deferral itself is unaffected**, because the blocker was
> never the number of separators: it is that no separating axis is in the model's
> alphabet and the joint PRL-and-IGFBP1 observation mapping is a rejected gap.
> Stating the inventory once, on the TI-04 register row, is U2's job.

**A side finding that contradicts a committed rule, recorded and not actioned.**
Tamura obtains full PRL and IGFBP1 induction with **dibutyryl-cAMP alone**, 0.5
mM for 96 h in charcoal-stripped serum, with **no progestin, no MPA and no E2**,
in primary stromal cells from donors aged 40–45. The committed `S_DECIDUALIZED =
S_PGR ∧ S_PKA ∧ S_BMP2` with `S_PGR = IN_PROGESTIN` predicts **no induction**
under that condition. This is contrary evidence against the necessity of the
`S_PGR` conjunct *in vitro*. It is recorded here and nowhere else, because it is
one paper in one system and the pause is in force.

**On the general question, the answer is yes with a sharp limit.** Four
independent instances show separately-measured layers of one entity moving
apart, the cleanest being four hCG species assayed separately with only two
moving under one perturbation, and an IGFBP1 panel where secreted protein falls
to 27 % while transcript *rises* to ~128 % at the lowest dose. **But the full
three-layer stack — transcript, protein, activated state — is established for no
single entity; each instance supplies two layers.** And there is a counter-case:
PAEP transcript and glycodelin protein move concordantly, so that pair should
**not** be split. For BMP2 specifically, §4.6a's evidence supports **two protein
states, pro and mature, and no transcript state**, because transcript was never
measured.

**The preprint licenses nothing, and its hormone-independence claim does not
hold.** Apostolov 2026 uses blastoids from one cell line against an
organoid-derived epithelial monolayer, scoring five blastoids per well at 48 h
after a wash, N = 4 from 2 biological replicates. The effect is **unattributed**:
blastoids express the receptor and the drug raised free hCG-β three-fold in the
same wells, so it acts on the embryo too. The "hormone-free" arm removes
estradiol, progestin, cAMP and the WNT inhibitor **together**, while the drug's
own action raises cAMP; the co-culture medium still contains estradiol and
progesterone; and glycodelin stayed undetectable in the very arm where
attachment was called restored. Receptor dependence is unresolved by the
authors' own statement, with no antagonist, no knockdown and no
excipient-matched vehicle. **Nothing here moves a rule**, and the plan records
it as an exploratory phenotype.

**Nothing in this cluster touches the epithelial nodes.** Neither paper mentions
PC6, BMP2, MUC1, PODXL or dystroglycan, so neither adds an experimental
condition relative to §4.6. In particular, Tamura's **stromal, nuclear** actin is
a different object from the committed **epithelial, apical** `E_ANXA2_ACTIN`, and
is not evidence about it.

### 4.13 SETD7 — an unresolved sign conflict, and no sign is assigned

> **Superseded in its evidence basis on 2026-10-22, not in its verdict.** Chen
> 2026 and Konyushatova 2025 are now local full texts and have been read at
> figure level. The verdict below — **no sign assigned** — survives, and the
> three-way adjudication that replaces this subsection's evidence base is
> `docs/v05_external_review_delta_2026-10-22.md` §3. Three things there are new
> and are not restated here: the two loss-of-function papers **disagree with each
> other** on substrate and subcellular compartment; Yu's own rescue arm works in
> cells carrying **no SETD7 manipulation**; and Konyushatova reports a
> **PRL/IGFBP1 dissociation** that bears on TI-04. The table immediately below
> describes the state of knowledge *before* those readings and is kept for the
> record.

Three papers bear on SETD7 in decidualization. **Only one is in the local corpus;
the other two were retrieved at abstract level and are cited as such.** No panel,
n or reagent from either is treated as read.

| source | availability | perturbation | SETD7's effect |
|---|---|---|---|
| Yu 2026 (local PDF) | full text | **overexpression only** | **negative** — more SETD7, less PRL/IGFBP1 |
| Chen 2026, *Biol Reprod* `10.1093/biolre/ioag005` | abstract only, paywalled | SETD7 deficiency; HOXA10 knockdown | **positive** — "indispensable" for the transition |
| Konyushatova 2025, *Mol Hum Reprod* `10.1093/molehr/gaaf028` | abstract only | **knockout** | **positive** — KO gives accelerated senescence and impaired decidual response |

**The third paper was not named in the task and was found during adjudication.**
It is from the same laboratory as the corpus's existing stromal-senescence
source, and it matters because it is a second, independent loss-of-function.

#### The conflict is not about substrate, and it is a reversal of sign

A difference of substrate or endpoint would not be a contradiction. Here there
is no substrate contest at all: **Yu contains no methylation experiment of any
kind.** The string "methylat" appears only in its Introduction and references,
never in Methods or Results — no methyltransferase assay, no methyl antibody, no
mass spectrometry, no residue, no histone ChIP, no SETD7–FOXO1 co-immunoprecipitation.
Its asserted mechanism is **phosphorylation**, and how a lysine methyltransferase
causes AKT-site phosphorylation is never addressed. So "FOXO1 versus HOXA10" is
one claim against zero.

**What actually conflicts is the sign, on three identically measured endpoints:**

1. **SETD7 level versus IGFBP1/PRL.** Yu: more SETD7, less marker. Chen: SETD7
   deficiency, less IGFBP1. Konyushatova: knockout impairs the decidual
   response. **Two independent loss-of-function studies place SETD7 as required
   and positive; one gain-of-function study places it as negative.**
2. **SETD7 in pathological endometrium.** Yu reports it **up** in recurrent
   implantation failure; Chen reports it **down** in mid-secretory endometrium
   from a subset of the same patient group; Konyushatova reports it down in
   recurrent pregnancy loss.
3. **The same public single-cell resource, read oppositely.** Yu assigns SETD7
   **high** to the senescent cluster; Konyushatova reports **low** SETD7 with a
   reduced ratio of the same marker pair. No difference of system, species or
   timepoint can absorb that.

#### The AZD8055 problem, which the task flagged and which is worse than flagged

Yu's paper **calls AZD8055 "an inhibitor of FOXO1 T24 phosphorylation"** and
proposes it as a *specific* inhibitor of the SETD7–FOXO1 axis. **It is an
ATP-competitive mTORC1/mTORC2 inhibitor**, used here at a concentration far above
its cellular potency for the kinase it actually targets. It licenses one
statement only: *this endpoint is sensitive to combined mTORC1/2 inhibition*.
**It never licenses FOXO1-dependence.** Three further reasons the inference
fails:

- the drug's documented effect on that residue is to **relieve** AKT-mediated
  nuclear exclusion, i.e. to **activate** FOXO1 — the opposite sign to the one
  the paper applies;
- mTOR inhibition suppresses senescence with no FOXO1 in the path at all, so the
  senescence result follows from the primary target alone;
- **the corpus already contains the confound**: Baek 2018 shows rictor knockdown
  *enhances* PRL in these cells, which is what mTORC2 ablation does on its own.

There is also **no FOXO1-specific perturbation anywhere** — no siRNA, knockout,
dominant-negative or selective inhibitor — and **FOXO1 localisation is never
measured**. The only FOXO1-activity readout is PRL/IGFBP1 itself, which is
precisely the collapse `candidate-nodes.tsv` forbids in writing for the staged
`S_FOXO1` node.

#### Verdict: no sign assigned, no node, no edge

**This plan assigns SETD7 no regulatory sign.** The task asked for the conflict
to be investigated before assigning one; the investigation says the question is
open. On evidence quality Yu is the weakest source on every axis and is the one
to discount — but **discounting is not resolving**, and the two stronger papers
were read only as abstracts. **One reconciliation is not excluded**: a
non-monotonic dependence in which SETD7 is required at endogenous level and
deleterious when forced far above it. Yu only ever adds; the others only ever
remove; none measures achieved dose against endogenous.

**It does not resolve the staged `S_AKT_EXCESS` edge either**, which is exactly
the edge it looks like it should resolve. That node is staged "unresolved;
candidate inhibitor of `S_FOXO1`" at confidence 5, and it stays there: the AKT
arm here is purely correlational, with no AKT perturbation of any kind.

**And even on Chen's better-evidenced reading, the mechanism lands inside the
`S_DECIDUALIZED` alias class**, which is already phenotype-inert. A real
mechanism that the model can neither express nor identify. Three
evidence-ledger rows follow, all cautionary, and the topology pause is untouched.

**A standing methodological note is recorded with them:** AZD8055 is never a
FOXO1-specific intervention in this project.

**One finding worth carrying forward, which is not about SETD7.** The corpus
holds a system-matched contradictory pair on mTORC2/RICTOR→FOXO1 in these cells
— Baek 2018 against Lin 2026 — and that pair governs the sign of everything
upstream of `S_FOXO1`. It must be adjudicated before `S_FOXO1` leaves
`model_gap`.

### 4.14 NNMT and EZH2/H3K27me3 — the pathway reproduces the decidual state

The decisive question was whether this supplies **independently useful** stromal
regulation or merely re-derives what the model already has. **It reproduces it.**

**NNMT is induced by the same stimulus the model already encodes.** Primary human
stromal cells, decidualized with a progestin plus cyclic-AMP analogue — the
literal conjunction `S_PGR ∧ S_PKA`. The paper reports PRL and IGFBP1 following a
*"nearly identical profile"* to each other across the time course. **No
independent upstream regulator of NNMT is tested anywhere**: no progestin-alone
arm, no cAMP-alone arm, no antagonist, no receptor knockdown, no estrogen arm.

**So an `S_NNMT` node would arrive as a seventh member of the existing stromal
alias class** — `{OUT_STROMAL_DECIDUALIZED, S_DECIDUALIZED, S_IGFBP1, S_PRL,
S_SPP1, S_TAZ_ECM}` — structurally unidentifiable on arrival, and unmeasured by
ADOC besides.

**The methyl-donor logic is asserted at the step that matters.** The proposal is
that NNMT consumes the methyl donor, so losing NNMT raises it and thus raises
the repressive mark. But the donor is measured **only as a consequence** of
knockdown, never set independently: no methionine manipulation, no synthetase
inhibitor, no add-back. Both rescue reagents act **downstream at the writer**, so
neither can distinguish a metabolic cause from any other cause of excess mark.
**The model therefore cannot borrow methyl-donor availability as a new input**,
which is the only way this pathway could have been independently useful.

**Further limits, recorded.** EZH2 is **never perturbed genetically**; one
inhibitor is described by the authors themselves as broad-spectrum, the other is
selective but applied only on top of the knockdown, and both rescue only
partially. A single siRNA sequence, no second sequence, no overexpression and no
re-expression rescue. Donor *n* is unreported for every in-vitro panel. And the
paper's own data contain a contradiction it does not reconcile: **all three
polycomb subunits rise in protein after knockdown**, which substrate
availability cannot explain.

**For the stromal-state candidate (R6), this is unifying rather than
separating.** Nothing here separates markers from a state: there is no
cell-cycle, senescence or proliferation readout, the only non-marker readout
moves in lockstep, and the only promoter-level mechanism sits at the **two marker
promoters**. It is the mirror image of Tamura 2014 with a repressive mark instead
of an activating one, and it supplies **no de-aliasing witness for TI-04**.

**Two provenance corrections.** The file name carries a forward-dated volume
year; the article was accepted and published in **2026** and is **not a
preprint**. And "endometrial receptivity" appears in its title and abstract while
**no attachment or co-culture experiment exists** anywhere in it.

**Model relevance: an evidence-ledger row, and nothing else.** No node, no edge,
no rate, and nothing bearing on the topology pause.

### 4.15 DSG2 — about invasion, and the model has no invasion endpoint

**The distinction the task asked for turns out sharper than expected.** This is
not a case of invasion being affected while adhesion is intact. **Adhesion is
never measured and never perturbed.** The blocking antibody is added *after firm
attachment, by design*. So no dissociation can be read from it, and reporting
one would be an over-read.

**The primary endpoint is null.** Invaded volume at the 48-hour endpoint is
**non-significant on both comparisons**. The highly significant figure quoted in
the abstract comes from a **post-hoc categorical reanalysis** devised after that
null, at an unregistered cut-off, pooling individual spheroids as though
independent within the same three biological replicates. The effect is
modulation in any case: the antibody was used at half the previously validated
dose, desmosomes were *"reduced but not completely depleted"*, heterologous
junctions remained detectable, and every analysed spheroid still invaded.

**The system is further from the model than the title suggests.** No embryo, no
blastoid, no organoid: the trophoblast is a single hybridoma line with an
extravillous rather than trophectoderm phenotype, and the maternal side for the
**only** functional experiment is a carcinoma line with zero donors. Primary
epithelium appears in descriptive imaging only. The antibody was added to bulk
medium with both cell types exposed, so **which side DSG2 acts on is unresolved**.

**Timing places this after the window the model represents.** Attachment occurs
within a few hours; all junction imaging and all electron microscopy are at the
single 48-hour endpoint, roughly two days after attachment completed. **These are
late post-attachment structures, and the model's adhesion endpoints are the wrong
readers for them.**

**Two cautions against importing it into adjacent nodes.** CDH1 and CTNND1 are
**not measured**; β-catenin is the adherens-junction marker here and **must not be
entered as CDH1 evidence**, which would repeat an error §4.2 already corrects.
And hormonal regulation is not addressed at all — the cultures are
steroid-free — so on this paper alone a DSG2 node would be **a constant**.

**A new invasion endpoint should not be requested on this basis.** Proposing an
endpoint is a higher-impact change than proposing a node and needs separate
permission; ADOC measures no invasion observable; the pause is in force; and the
supporting primary endpoint is null.

**Model relevance: an evidence-ledger row, and nothing else.** No node, because
the side is unresolved, there is no regulated parent and the endpoint is absent;
no edge into either adhesion endpoint, because the perturbation begins after the
attachment those endpoints stand for; and no trophoblast node is structurally
possible, that side being a single input.

## 5. Candidate rule families and the traceability/identifiability matrix

The full matrix is `docs/v05_traceability_identifiability_matrix_2026-10-21.tsv`,
fifteen rows carrying the twenty columns the request specifies — original logic,
experiment and panel, system/compartment/species, intervention and comparator,
molecular layer, supported sign, contrary evidence, candidate rules, endpoints
read, alias/absorption effect, transient effect, ADOC observable, prospective
data needed, pause and TI gate, uncertainty, falsifier, unit size and status.
Every candidate carries **at least two alternatives plus the null**, and every
proposed name is provisional.

It is not restated here. What this section adds is the single ordering fact the
matrix cannot show, and the decision summary.

### 5.1 The ordering rule, re-derived rather than inherited

The previous revision withdrew ranking by endpoint/structural effect and replaced
it with ranking by **identifiability among licensed candidates**. That
replacement **stands, and the adjudication strengthens its basis**: §3.4 shows
identifiability is strictly coarser than structure here, and §4 shows the
best-evidenced candidates (R1, R3, R4) are precisely the ones with no ADOC
observable. Ranking by endpoint movement would have ranked them last.

### 5.1a The vacuity is overdetermined, and "live" means two different things

An earlier revision of this section asserted that **R1 is a prerequisite of
N3-CD98, R3-a and R2 alike**. **That claim is false and was withdrawn.** The
counterfactual, computed over all 65,536 states with the repository's own
primitives, is that R1 alone, R3-a1 alone, N3 alone and R1+N3 all leave every
adhesive disjunct absorbed, while **R1 + R3-a1** makes them clamp-sensitive. The
vacuity has two independent causes — `¬E_MUC1_BARRIER ≡ E_SECRETORY_STATE` with
five disjuncts being exact aliases of it, and the GP130 prefix — and removing
either alone changes no disjunct's absorption status. The owner's pause note
says exactly this and an earlier revision misquoted it by dropping half a
sentence.

**A second and more serious correction now follows, because "all eight disjuncts
go live" was the wrong reading of that result.**

#### Clamp sensitivity is not endogenous influence

The repository's `absorbed_edges` asks whether **pinning a node ON versus OFF**,
overriding its own rule, changes its reader. That is a clamp question. It is the
right notion for asking what an *intervention* can reach, and it is the wrong
notion for asking whether a determinant is an **independent route**. Under
R1 + R3-a1 the composed rule reduces, exactly, to

```
E_RECEPTIVE_SURFACE = (IN_E2 ∧ IN_PROGESTIN) ∨ IN_EMBRYO_CONTACT ∨ (IN_PROGESTIN ∧ IN_cAMP)
```

verified by exhaustive comparison against that expression. **Three terms, not
eight.** Deleting each disjunct in turn while every other node keeps its own
rule gives:

| disjunct | clamp-sensitive | states changed by deleting it | endpoint moved |
|---|---|---|---|
| `E_CDH1_APICAL` | yes | **20,480** | `OUT_EPITHELIAL_RECEPTIVE` |
| `X_SPP1_LUMEN_FREE` | yes | **4,096** | `OUT_EPITHELIAL_RECEPTIVE` |

*The "endpoint moved" column lists `OUT_` nodes only. `X_ADHESION_ROUTE_REDUNDANT`
also moves for both passing disjuncts; §5.1b states that blast radius in full.*
| `E_CD98_CD9` | yes | 0 | none |
| `E_ANXA2_ACTIN` | yes | 0 | none |
| `E_HBEGF` | yes | 0 | none |
| `E_DAG1_CLEAVED` | yes | 0 | none |
| `E_MUC1_SLEX` | yes | 0 | none |
| `E_ITGAVB3_5` | yes | 0 | none |

**All eight are clamp-sensitive; only two have endogenous influence. Six are
individually redundant.** The external review raised this and it is confirmed,
not merely conceded.

**And the result is stronger than "individually redundant", which was the
obvious blind spot in the test above.** A determinant can be individually
redundant while a *subset* is jointly load-bearing, so all 63 non-empty subsets
of the six were deleted in turn. **The maximum number of states changed by any
subset is zero.** Deleting all six together changes nothing; deleting all six
**and `E_GP130_STAT3` as well** also changes nothing. Under R1 + R3-a1,

```
E_RECEPTIVE_SURFACE  =  E_CDH1_APICAL  ∨  X_SPP1_LUMEN_FREE          (exactly)
```

verified by exhaustive comparison. The reason is that
`X_SPP1_LUMEN_FREE = E_SPP1_EXPR ∨ S_SPP1` already equals
`(IN_E2 ∧ IN_PROGESTIN) ∨ (IN_PROGESTIN ∧ IN_cAMP)` on its own, so it subsumes
the entire secretory family **and** the GP130 term. **Seven of the nine disjuncts
in the repaired rule, including the GP130 route the repair was built to
liberate, are jointly redundant.**

**Where the three terms come from — and the six supply none of them.** An
earlier revision wrote that the six "contribute the `IN_E2 ∧ IN_PROGESTIN` term
jointly"; the joint-deletion control above refutes that, since removing all six
changes nothing. The correct attribution is:

- `E_CDH1_APICAL` supplies `IN_EMBRYO_CONTACT`, the committed rule making it
  exactly that.
- `X_SPP1_LUMEN_FREE` supplies **both** hormone terms on its own, because
  `E_SPP1_EXPR = E_SECRETORY_STATE` gives `IN_E2 ∧ IN_PROGESTIN` and
  `S_SPP1 = S_DECIDUALIZED` gives `IN_PROGESTIN ∧ IN_cAMP` — the **stromal
  decidual state leaking into epithelial receptivity**.
- The six, and the `E_GP130_STAT3` disjunct R1 creates, supply **nothing**: each
  is implied by `X_SPP1_LUMEN_FREE` and all are jointly removable.

**The consequence runs against this plan's own argument and is stated because of
that.** R1 is the repair §4.1 licenses on the GP130 evidence. Applying it yields
a model in which **GP130 is not a route by this plan's own Test 7** — its
disjunct is implied by `X_SPP1_LUMEN_FREE` and deletes without effect. So R1
corrects a rule that is biologically wrong and buys no route in the process.
That is an argument for doing it on correctness grounds alone, and against
describing it as route-liberating, which earlier revisions did.

**So R1 + R3-a1 does not buy eight routes. It buys three, and both of the
non-hormonal ones are defects rather than mechanisms** — one is the contact
identity §4.2 shows is contradicted, the other is a stromal state reaching an
epithelial node. This is the same class of error as the truth-table-versus-
trajectory conflation in §4.6a: a structural primitive answered a question
narrower than the one being asked.

#### A sixth acceptance test, because §8.2's five do not catch this

§8.2 tests 1–5 and the size-1 deletion control are all stated against absorption.
None of them distinguishes a clamp-sensitive disjunct from an independently
regulated one, which is why an earlier revision reported eight routes.

> **Test 7 — endogenous non-redundancy.** Delete the candidate determinant alone
> from its reader while every other node keeps its own rule, and re-derive over
> the full state space. The determinant qualifies as a route only if that
> deletion **changes the reader in at least one state**. Clamp sensitivity is
> reported separately and never substituted for it.

Applied now: of the eight, **two pass and six fail**. **What it measures, stated exactly.** Boolean non-redundancy, and nothing more.
A determinant that is biologically independent but **logically implied by an
existing disjunct** adds a mechanism and still fails Test 7. So a failure means
"this repair changes no model behaviour", not "this biology is not real" — the
two are separated in §10.4.

#### Corrected dependency statement

R1 and R3-a1 remain **jointly necessary** to make the disjunction clamp-sensitive
at all, and **N3 is not on the critical path**. Neither is a no-op in the loose
sense: R3-a1 changes no prediction, while R1 alone changes six nodes' predictions
and de-absorbs nothing. But the joint repair's *value* is now much smaller than
an earlier revision claimed, and §5.1b states what it would take to make it real.

### 5.1b Embryo contact alone should not make the epithelium receptive

Under R1 + R3-a1, with `IN_E2`, `IN_PROGESTIN` and `IN_cAMP` all OFF and
`IN_EMBRYO_CONTACT` ON, `E_RECEPTIVE_SURFACE` is **TRUE in all 4,096 such
states**. An unprimed epithelium becomes receptive because an embryo touched it.

**The endpoint distinction must be kept, and it holds.**
`OUT_MATERNAL_ADHESION_COMPETENCE` and `OUT_STABLE_ADHESION` are **zero** in
every one of those states, because they additionally require the stromal and
mechanical conjuncts.

**But the blast radius is three nodes, not one, and an earlier revision
understated it.** `E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE` **and
`X_ADHESION_ROUTE_REDUNDANT`** all move: the redundant route is ON in **2,048
of the 4,096** hormone-free contact states, against **0** in the committed
model. So an unprimed epithelium does not merely read as receptive, it opens an
adhesion route. The terminal endpoints still hold the line, which is why this is
a defect to fix rather than a failure to ship.

**This is why R2 re-enters, and on biological rather than structural grounds.**
R2 is not needed for de-absorption — §5.1a shows R1 + R3-a1 achieves that alone.
It may be needed for the result to be *biologically admissible*. Three
alternatives were composed and evaluated, with the null:

| option | hormone-free contact states with `E_RECEPTIVE_SURFACE` ON | disjuncts with endogenous influence |
|---|---|---|
| **null** — R1 + R3-a1, CDH1 unchanged | 4,096 of 4,096 | 2 |
| **R2-a** — `E_CDH1_APICAL = IN_HCG ∨ IN_EMBRYO_CONDITIONED_SIGNAL` | 3,072 | 2 |
| **R2-b** — `E_CDH1_APICAL = E_SECRETORY_STATE ∨ IN_HCG` | 2,048 | 2 |
| **R2-c** — `E_CDH1_APICAL = IN_EMBRYO_CONTACT ∧ E_SECRETORY_STATE` | **0** | **1** |

**The trade-off is real and this plan does not resolve it.** Only R2-c
eliminates the counterexample, and it does so by making apical CDH1 depend on the
secretory state — which **costs the independent route**, dropping endogenous
influence from two disjuncts to one. R2-a and R2-b keep the route but still allow
a hormone-free epithelium to become receptive, now on an embryo-derived soluble
signal rather than on contact.

**Whether that is a defect is a biological question the corpus does not settle.**
Ruan 2026 shows the embryonic inducer of apical CDH1 is soluble and acts before
contact (§4.2), so an embryo-signal route that does not require maternal priming
is not absurd. Whether maternal epithelium can reach adhesive competence with
**no** hormonal history is untested in anything this plan has read. **This is an
owner decision (§10.1), not a modelling preference**, and no option is selected
here. What this plan does rule out is inventing a permissive gate purely to
remove the counterexample: R2-c is listed because it was composed and evaluated,
not because it is recommended.

### 5.2 Decision summary

| id | candidate | verdict | binding constraint |
|---|---|---|---|
| R1 | GP130 hard gate → modifier or OR-disjunct | **WAIT** | pause; and inadmissible except jointly with R3-a1 (§5.1a, §4.1) |
| R2 | apical CDH1 ← hCG / embryo-conditioned signal | **WAIT** | pause; then design-unidentifiable |
| R3-a1 | delete the four never-binding conjuncts in `E_RECEPTIVE_SURFACE` | **WAIT** | pause: prediction-identical but **not** a perturbation-layer refactor |
| R3-a2 | reduce `X_ANTIADHESIVE_ROUTE` to its relay | **WAIT** | pause; not semantics-preserving |
| R3-b | MUC16 surface-clearance barrier | **NO GO** | TI-06 clearance determinant absent |
| R4-a | `S_NR2F2` disjunct in `S_BMP2` | **UNRESOLVED — no change proposed** | no human comparator identifies cAMP as necessary; mouse evidence favours keeping it |
| R4-b | correct `E_PGR→E_IHH`; the robust human finding is **estrogen induction**, i.e. a wrong input | **WAIT** | pause; **and blocked on R4-a**, because any form of it changes progestin-alone `S_BMP2` (§4.8, §4.10) |
| TI-03 | split αVβ3 from αVβ5 | **NO GO** | condition 1 unmet; condition 2 now advanced |
| TI-04 | independent PRL / IGFBP1 rules | **NO GO** | ADOC observability |
| N1 | wire `IN_XAV939` | **already correct — do not wire** | — |
| N2 | an independent glycan route | **rejected** | no hormone-independent determinant established |
| N3 | split CD98 from CD9; re-source CD98 | **WAIT** | pause; **not on the critical path** (§5.1a) |
| N4 | stromal PC6 → BMP2 maturation edge | **documentation only** | truth-table identical, but it adds a node, so **not** shown trajectory-neutral (§4.6a) |
| N5 | SETD7 stromal regulator | **no sign assigned** | all three sources now read at figure level; they reverse on sign and the two loss-of-function papers disagree on substrate and compartment (§4.13 note, delta §3) |
| N6 | NNMT / EZH2 stromal regulator | **rejected** | reproduces the decidual state; a node would be a seventh alias-class member (§4.14) |
| N7 | DSG2 heterologous junctions | **rejected** | post-attachment invasion, which the model does not represent; primary endpoint null (§4.15) |
| N8 | split `S_PGR` into PGR protein and PGR transcriptional activity (HBP1, SOX4) | **WAIT** | pause; the only external candidate that attacks the seven-member hormone alias class, and neither source is adjudicated at figure level yet (delta §4.1) |
| R5 | PODXL barrier re-specification | **NO GO** | complement form refuted on three grounds, no replacement licensed; **TI-06 does not govern it** — R5's own conditions apply (§4.11) |
| R6 | separate the decidual **state** from its **markers** | **WAIT** | pause; a different seam from TI-04, and the reversal question is open (§4.12) |

**No candidate is GO. Every one is inside the 2026-09-30 pause**, and §7.1 shows
no resume trigger is true.

**A correction to an earlier revision of this plan, which had R3-a1 as GO.**
R3-a1 deletes four conjuncts that `load_structure` reports as never-binding, and
deleting them leaves **every node identical in all 65,536 states** — verified
this session, and that verification stands. The error was in reading the pause's
carve-out. It exempts *"a semantics-preserving software- or perturbation-layer
refactor: a change that leaves every model prediction identical under every
declared condition, **and** changes only how perturbations are represented and
applied."* That is a **conjunction**, and the surrounding paragraph makes its
subject plain — compound identities such as `IN_MIFEPRISTONE` embedded as MaBoSS
nodes. **R3-a1 satisfies the first conjunct and fails the second**: deleting
biological conjuncts from network logic is not a change to how perturbations are
represented. So R3-a1 is **WAIT**, and only an explicit owner decision can
authorize it. The independent review of §9 also read the carve-out as a single
criterion and endorsed the GO; that endorsement is withdrawn with the verdict.

R3-a2, which additionally reduces `X_ANTIADHESIVE_ROUTE` to its relay, changes
three nodes including both endpoints, so it fails the first conjunct as well. The near-term units
in §6 are therefore the non-topology work that is admissible now and that the
topology units depend on.

---

## 6. The near-term plan — three units

Each unit below states its scope, its exact deliverables, the files it would
touch, its mutation boundary, its tests, its falsifier, its reviewer gate and
what it explicitly does not do. **None changes an executable rule, a rate, a
condition, a protocol, a calibration, an observation map or a phenotype
definition, and none creates a model version.**

### U1 — Evidence registration for the adjudicated corpus — **GO**, owner authorization required

**Why first.** §2.4 shows 61 articles sit in neither canonical ledger, and
one of them — Cloke 2008 — carries the strongest PRL/IGFBP1 separation in the
corpus. Every topology unit downstream draws on determinants from that
unregistered remainder. Registering it is the prerequisite that is admissible
now.

**Scope: additive registration only.** For each adjudicated article, record the
digest, DOI, system, compartment, molecular layer, the panel actually read, and
the adjudicated outcome from §4. For `PDF-048`, record the **digest mismatch**
and link the locally held rendering, rather than deleting the row or treating the
article as missing (§2.4 finding 1).

**Explicitly out of scope, and why.** The two mapping defects this adjudication
found — the `CDH1`/`CTNND1` `any_of` union in `config/node_entity_map.tsv`
(§4.2) and the `node_dictionary.tsv` "CD98 **or** CD9" / "surface CD98 **and**
CD9" mismatch (§4.3) — are **reinterpretations of a node on biological grounds**
and therefore fall inside the pause. They are put to the owner in §10.1
item 2, not folded into U1. *This is a judgment call on pause scope, stated as an
assumption: U1 is kept to changes that add evidence rows and alter no node's
meaning.*

**Narrowed after the first independent review** (§9.2): U1's rows record **evidence** —
paper, panel, system, compartment, molecular layer, sign — and **point at this
plan for verdicts** rather than restating a verdict in a ledger. A register row is
read later as established fact, and that is exactly how an overstatement becomes
durable.

**Files, decided per artifact.** An earlier revision listed three canonical
ledgers without saying what happens to each, and the delta report then named only
two. Both are superseded. The three artifacts have **different granularities**,
and only one of them is the right home for article provenance:

| artifact | granularity | U1 decision | fields U1 touches |
|---|---|---|---|
| `context/literature/pdf_manifest.tsv` | one row per held **PDF rendering** | **MODIFIED** | all 17: `manifest_id`, `file_stem`, `doi`, `pmid`, `publication_status`, `rendering_read`, `study_type`, `system`, `compartment`, `key_finding_for_adoc`, `figures_rendered`, `batch`, `pages`, `sha256`, `full_text_inspected`, `ref_id` (left empty), `registration_decision` |
| `context/literature/active_evidence_manifest.tsv` | one row per paper **per audit role** | **UNCHANGED** | none |
| `context/evidence-register.tsv` | one row per **claim**, `LIT-<MECHANISM>-NNN`, `planned_use = construction` | **UNCHANGED** | none |

**Why the two are unchanged, because this is a semantic decision and not an
omission.** `active_evidence_manifest.tsv` carries a verification column named for
a specific audit, `figure_verification_2026_09_28`; writing a 2026-10-22 reading
into it would assert participation in an audit that never read these papers, and
widening the schema is outside U1's additive boundary. Its
`model_nodes_or_rules_supported` field would also be empty for every new paper,
because none licenses a node, edge, rate or sign. `context/evidence-register.tsv`
is **claim-level, not article-level**: its 16 literature rows are mechanism
clusters pointing at `REF-` ids with `planned_use = construction`. None of the
articles U1 registers licenses a construction role — NNMT and DSG2 are rejected,
SETD7 is assigned no sign, Kakar-Bhanot is contradictory — so creating a `LIT-`
row would assert a use the adjudication refuses. **Registering an article's
provenance is not registering its evidence**, and U1 does only the former.

These are canonical ledgers, so the unit **cannot start without owner
authorization** — the governing request forbids modifying them otherwise.

**Mutation boundary, counted exactly.** All mutations land in
`pdf_manifest.tsv`. The totals reconcile as:

| component | appended rows | field corrections |
|---|---|---|
| U1's original scope — adjudicated articles in neither digest-bearing ledger, excluding the seven below | **24** | 0 |
| the 2026-10-22 delta's seven articles | **7** | 0 |
| `PDF-048` | 0 | **0 — WITHDRAWN, see below** |
| derived reconciliation refresh | 0 | **31 rows × 3 fields** |
| **U1 total in `pdf_manifest.tsv`** | **31** | **0** |

**The `PDF-048` rewrite is withdrawn, and this is the most important correction
in this revision.** Two earlier claims were wrong in sequence: that it changed
one field, then that it changed three. It changes **none**, because it must not
happen at all. Simulated in an isolated worktree on 2026-10-22, the swap breaks
`tests/unit/test_pdf_manifest.py::test_files_recorded_as_not_versions_of_record_stay_countable`,
which pins the not-version-of-record set to exactly `{PDF-048, PDF-054}` and pins
`PDF-048` to `author_manuscript`. **The pin is load-bearing for the audit, not
bookkeeping:** every figure and page reference in
`blocked_source_refresh_2026-09-18.primary-verification.tsv` is to the 28-page
author manuscript, so re-registering would silently repoint existing evidence at
a 15-page document with different pagination. The digest mismatch therefore stays
**documented and unrepaired** in the reconciliation, which is the
audit-preserving outcome.

*The alternative, for the owner.* Add the publisher rendering as a **separate**
row carrying `ref_id = REF-076` and `registration_decision = registered`.
Simulated: it passes every canonical test except
`test_manifest_dois_that_are_cited_resolve_in_the_bibliography`, whose pinned
overlap count of 60 becomes 61 and would have to be updated. That is a
canonical-test edit, so this plan does not take it unilaterally.

**Registration semantics for the seven appends are corrected too.** They may not
carry `registration_decision = registered` with an empty `ref_id`:
`test_registration_decision_agrees_with_the_registry_both_ways` forbids exactly
that pairing and additionally requires the DOI to be absent from
`references.tsv`. All seven DOIs are confirmed absent. They therefore take
`ref_id = EMPTY` with `registration_decision = recorded_not_registered`, a **new
value** meaning the PDF is held and read but no `REF` id has been minted.
Recording an obtained PDF is not registering a source in the canonical
bibliography, and the column had no value for that distinction. **The vocabulary
extension needs owner approval**, and the established invariant is not weakened
to accommodate the rows.

**U1 is now fully specified, and two blockers remain.** All 31 append-scope
articles have a contract row: **30 individually specified with a DOI extracted
from the source PDF itself**, and **one blocked** — Paule 2015, whose PDF carries
no DOI string and for which no repository artifact records one. No DOI is
supplied from memory, which would be fabricated provenance.

**Registration decisions, owner-approved 2026-10-22.** `recorded_not_registered`
is approved as a new value meaning the PDF is held and read but no `REF` id has
been minted. It applies to **27** rows. The other **3** carry a DOI already in
`references.tsv` and therefore take `ref_id` with
`registration_decision = registered`: `REF-025` Franco 2010, `REF-014` Heng 2021
*Sci Rep* and `REF-013` Paule 2021.

**One canonical test must change, and it is not changed here.** Those three
registered rows move
`test_manifest_dois_that_are_cited_resolve_in_the_bibliography` from its pinned
overlap of 60 to **63**. Simulated on the full 30-append poststate: that is the
**only** failure, the other 14 tests pass. This is a legitimate consequence of a
legitimate registration rather than a rule bent to fit the rows, and it is
recorded in the contract as `REQUIRES_OWNER_APPROVAL` for execution time.

**Article-versus-rendering multiplicity is resolved.** The 31 renderings are
**30 distinct articles**: Retis-Resendiz 2024 is held in two renderings sharing
one DOI, which is permitted because the digests differ. Franco 2010 and
Heng 2021 each appear twice as *different papers* sharing author and year.

Reproduce the 24 and the 31 from the reconciliation TSV and the two
digest-bearing ledgers:

```sh
python3 -I scripts/check_u1_mutation_contract.py
```

**Seven articles are seven rows here, and that is a property of this artifact
rather than an assumption.** `pdf_manifest.tsv` is keyed per *rendering*, and each
of the seven is a single rendering, so the mapping is one-to-one. It would not be
one-to-one in `context/evidence-register.tsv`, where one article with several
experimental observations yields several claim rows — which is a further reason
U1 does not write there. **No existing adjudication verdict is overwritten and no
existing row other than `PDF-048` is edited.**

**The delta contributes no field correction.** The three manifest identifiers it
discusses — `PDF-011`, `PDF-015`, `PDF-034` — are already present and correct in
`pdf_manifest.tsv`; those are corrections to the external review document, not to
a ledger.

**The exact contract is `docs/v05_u1_mutation_contract_2026-10-22.tsv`**, ten
rows carrying `source_doi`, `source_sha256`, `canonical_artifact`, `operation`,
`row_identifier`, `fields_changed`, `expected_old_state`, `expected_new_state`,
`supporting_primary_evidence` and `validation` — seven `APPEND_ROW`, one
`UPDATE_FIELDS` for `PDF-048`, and two explicit `NO_CHANGE` declarations so the
scope is finite and every artifact is accounted for. **The owner's stated
preference, recorded 2026-10-22, is to re-register `PDF-048` against the locally
held rendering**, subject to the identity verification above and to preserving
the superseded digest, and the contract row now carries that option with its
three fields rather than leaving the choice open.

**Tests.** Three layers. The first exists and runs today, **at two explicitly
separated levels**, because the literature corpus is gitignored and a reviewer is
entitled to validate this repository without it.

1. **The contract pre-condition check**, `scripts/check_u1_mutation_contract.py`,
   read-only and modifying nothing.

   **(a) Repository level — `python3 -I scripts/check_u1_mutation_contract.py`.**
   Runs from a clean checkout containing only tracked files and **passes there**.
   It asserts the contract schema and required fields; the operation counts
   (**7** `APPEND_ROW`, **1** `UPDATE_FIELDS`, **2** `NO_CHANGE`); that every
   append targets `pdf_manifest.tsv` and nothing else; that each digest is 64
   lowercase hex and each DOI well formed, both unique within the contract; that
   no proposed digest, DOI or `manifest_id` collides with an existing one in
   **either** digest-bearing ledger; that the proposed ids are contiguous above
   the current maximum; that every contract digest has a row in the
   reconciliation; that the `PDF-048` target exists, its recorded digest is not
   held locally, and `fields_changed` declares **all three** fields the rendering
   change moves; that both `NO_CHANGE` artifacts are in the state the contract
   declares, including that every `LIT-` row still carries
   `planned_use = construction`; that the derived append scope is **31 = 24 + 7**;
   and that no canonical ledger is modified relative to `HEAD`. **It never opens
   a PDF and never claims to have verified one.**

   **(b) Local-source verification — `--verify-sources`.** Hashes every PDF the
   contract names and requires an exact match, failing separately and
   informatively on a **missing** file and on a **digest mismatch**. It can only
   run where the gitignored corpus is held, so **it does not pass in a clean
   checkout and is not expected to.**

   **(c) Poststate compatibility, simulated 2026-10-22 in an isolated git
   worktree.** The intended post-U1 manifest was built and the canonical suites
   run against it: `tests/unit/test_pdf_manifest.py` **15/15 OK** and
   `tests/unit/test_curation_increment_08_blocked_sources.py` **25/25 OK** under
   `pixi`. The rejected designs were simulated too and fail, which is how the
   corrections above were found: `registration_decision = registered` with an
   empty `ref_id` fails the registry agreement test, and the `PDF-048` rewrite
   fails the not-version-of-record pin.

   **Successful local-source verification is a mandatory precondition for
   executing U1.** Repository-level success alone does not authorize execution:
   it establishes that the contract is coherent, not that the sources are the
   ones it names. Both failure branches were confirmed by negative controls — an
   append pointed at an already-registered digest, and a file whose bytes do not
   match its recorded digest — each of which must fail and does.
2. **On execution**, the repository's existing manifest validator plus
   `pixi run harness-check`, and a post-condition assertion that
   `pdf_manifest.tsv` grew by exactly **31** rows, that
   `active_evidence_manifest.tsv` still has **50** rows, and that
   `context/evidence-register.tsv` still has **47** rows with no new `LIT-`
   identifier.
3. **A membership test** asserting that each digest in the reconciliation TSV
   matches its declared per-ledger membership. Membership in more than one ledger
   is valid and common — 13 digests are in both — so it must check the `in_*`
   columns against the ledgers individually and accept four dispositions: in
   `pdf_manifest` only, in `active_evidence_manifest` only, in **both**, and in
   neither. A test demanding exactly one ledger row would fail on valid data,
   which is why it is specified this way.

**Falsifier:** if any newly registered digest fails to match its DOI on
resolution, the row is withdrawn rather than reconciled by hand.

**Does not:** promote any candidate node, write any edge, or change any
confidence already recorded.

### U2 — Deferred-register amendment — **GO**, owner authorization required

**Why.** The adjudication changed the status of **three** existing register items
and produced **twelve** new candidate rows. A register that does not carry them will
send the next session to re-derive them.

**Scope, counted to match the list below.** Three existing items are amended in
place — TI-03, TI-04 and TI-06 — each by editing fields, not state. **Twelve** rows
are added: **R1, R2, R3-a1, R3-a2, R4-b, N4, R5, R6, N5, N6, N7 and N8**. Of
these, **N5, N6 and N7** are the 2026-10-22 adjudications (§§4.13–4.15) and
**N8** is the 2026-10-22 external-review delta's one new candidate (§6.0b); none
proposes a node, and each is registered so the next session does not
re-adjudicate it. *An earlier revision of this sentence said "Eight rows are
added" while listing eleven, and the count has been wrong since before the N8
amendment; it is corrected here rather than patched around.* **R3-a1 and R3-a2 take
one row each, not one shared row**, because they differ in disposition and in
evidence: R3-a1 is prediction-identical and R3-a2 is not (§5.1a), so a shared row
could not state one unblock condition. **R4-a takes no row**: §4.8 leaves it
unresolved with no change proposed, and the register holds deferred increments
rather than open questions. **R5 and R6 are the two late-arriving clusters**
(§4.11, §4.12): R5 is blocked on **its own recorded conditions** and on evidence —
**not on TI-06**, which governs the MUC1 correction only — and R6 cuts the stromal
class along a different seam from TI-04's. **N8** is the
PGR-protein-versus-PGR-activity seam, and it takes a row on the same terms as the
others. That is three amendments and **twelve** additions, **fifteen mutations in
all**.

*Why the delta adds one mutation and not three.* It also revises the content of
**TI-04** and of **N5**. TI-04 is already one of the three amendments above, and
N5 is already one of the additions below, so both are field-level edits to
mutations this unit already performs. Only N8 is new. The count and the row list
move together, which is the drift this paragraph exists to prevent.

**Deliverables, one row or field each:**

- **TI-03** — record that condition 2 is now **partly answerable**: Apparao Fig 6
  shows anti-αVβ3 blocks osteopontin-driven adhesion while anti-αVβ5 does not, so
  the `X_ADHESION_ROUTE_SPP1` reader takes the **β3** half. Record that condition
  1 remains unmet and that the glycan cluster failed to supply the missing
  determinant. Record the three dissociations (§4.3) as strengthened forcing
  evidence, and record that the sole merge citation is carcinoma-line qRT-PCR.
- **TI-04** — record that the differential evidence is now **primary and
  figure-verified** (Kane 2010 Fig 4), that Tamura 2014 is **unifying rather than
  separating**, and that the blocker is unchanged because the separating inputs
  are not in the model's alphabet. Record that `S_PRL = S_IGFBP1` should no longer
  be presented as evidence-based. **Build the full separator inventory and
  reconcile it, which is the substantive part of this amendment:** §4.12 calls
  Kane 2010 *the only* separator in the corpus, §4.7 names Cloke 2008 Fig 1A as
  *a second separator*, and
  `context/literature/reviews/prl_igfbp1_foxo1_2026-09-22.primary-verification.tsv`
  holds two more that neither statement counts — **`PIF-003`** (Buzzio 2006,
  FOXO1A siRNA: IGFBP1 down while PRL up, the same opposite-direction pattern,
  with the caveat that the siRNA co-targets FOXO3A) and **`PIF-004`** (Ujvari
  2017, AS1842856: IGFBP1 collapses while PRL is unchanged, recorded there as
  *the cleanest de-aliasing signal in the corpus*). The row must carry all of
  them and state the count once. **Add the 2026-10-22 revision:** Konyushatova
  2025 Fig 1F adds a separator whose novelty is **not** the opposite-direction
  pattern, which `PIF-003` already records, but that it is a **CRISPR knockout**
  rather than a cross-reactive siRNA, and that the dissociation is
  **conditional on cAMP** — SETD7 knockout lowers PRL and raises
  IGFBP1 under the standard cocktail, with the dissociation disappearing when
  cAMP is withdrawn (Fig 1G) — and the authors attribute the raised IGFBP1 to
  stress rather than decidualization. Record that the witness is **not currently
  measurable**: the joint PRL-and-IGFBP1 mapping is registered as a rejected
  `gap` at `OM-011` and `OM-016` in `config/observation_model_map.tsv`. The
  blocker is therefore unchanged, and the row must say the separating axis
  (SETD7) is still outside the model's alphabet even though the conditioning
  variable (`IN_cAMP`) is inside it.
- **TI-06** — record that the naive inversion is now refused on **primary
  evidence** rather than on principle (§4.5), that Thathiah reports human
  blastocyst-conditioned medium failing to shed MUC1, and that the barrier arm is
  additionally **structurally** blocked (§3.2) independently of its evidence
  condition.
- **Twelve new deferred increments — `R1`, `R2`, `R3-a1`, `R3-a2`, `R4-b`, `N4`,
  `R5`, `R6`, `N5`, `N6`, `N7` and `N8`** — one row each, carrying the candidate rule families, structural
  consequence, unblock conditions and falsifier already in the §5 matrix. **`N8`'s
  unblock condition is figure-level adjudication of Guo 2026 and Huang 2022**,
  neither of which this repository has read at panel level; its row must say so,
  because its interest is structural and its evidence is still second-hand. Two
  notes on membership, so the list and the count above cannot drift apart again.
  **R3-a1 is included**: an earlier revision excluded it as semantics-preserving
  and destined to be a unit, and §5.2 now has it WAIT. **R4-a is excluded**: §4.8
  leaves it unresolved with no change proposed, and this register holds deferred
  increments rather than open questions, so it belongs in the plan and not in a
  row.

**Files:** `docs/deferred_topology_register.tsv`. An implementation-tracking
ledger, so again **owner authorization is required**.

**Mutation boundary:** no row changes `state` from `DEFERRED` to anything else.
No executable artifact is touched.

**Tests:** the register's existing schema check; `pixi run harness-check`; and a
count assertion that the unit performed exactly **fifteen** mutations — three
amended rows and twelve added `increment_id`s matching the list above — so the
scope, the row list and the count cannot diverge without a test failing.

**Falsifier:** if any recorded unblock condition is found already satisfied, the
row is wrong and the item must be re-adjudicated rather than registered.

**Does not:** unblock, discharge or close any TI item, and does not lift the
pause.

### U3 — Identifiability design for the new candidates — **GO** as a planning unit

**Why, and why it is not a duplicate.** `docs/identifiability_experiment_design.md`
already answers the perturbation × readout question for the *existing* variant
set, and its headline — no single-perturbation design resolves any alias pair —
stands. What does not exist is the same analysis for **R1–R4**.

**Deliverables.** Per candidate, the minimal observable that would discriminate
it, computed with the repository's own design-alias machinery rather than a new
one. Four results are already derived in §3.4–§3.5 and seed the unit:

- **The defect is in the committed configuration and tables, not in the code, and
  the enumeration gap is separate from both.** Stated precisely, because an
  earlier revision ran the two together: (i) `config/planned_design.yaml` declares
  `adoc-literature-superset-v0.4.0`, so `pixi run render-design-alias` and the
  committed tables under `docs/design_alias/` describe **v0.4.0**; (ii) the code
  is **not** pinned — `load_design_alias(model_version=…)` and
  `candidate_fifth_arms` run against v0.6.0 successfully and return 44 candidates,
  as this plan itself reports; (iii) the real limitation is that candidate
  generation **traverses only free network inputs**, so it omits the
  intervention-layer perturbations that v0.6.0 expresses outside the network.
  U3's first task is (iii) — extending scoring to the intervention library — and
  separately re-deriving the tables for the current model. That is why U3 is not a
  duplicate of the existing design document.
- **No comparable v0.6.0 identifiability figure exists yet, and producing one is
  part of this unit.** The 28-member class the v0.6.0 run reports is an artifact
  of that run seeing only two distinguishable arms, because the mifepristone and
  anti-SPP1 condition files are byte-identical to hormone-treated at v0.6.0
  (§3.4). An earlier revision seeded this unit with "the identifiability problem
  is worse than the committed tables show"; **that is withdrawn**, and U3 must not
  start from it. Until the intervention layer is applied, the committed v0.4.0
  tables are the only four-arm picture available.
- In the v0.4.0 scoring **two** families separate the two measured nodes:
  `dropout_IN_E2` at +3, and four of the six `dropout_IN_cAMP` variants at +2. Both leave the CD98/GP130
  class fused. The HAND2-loss arm splits that class and separates no measured
  node. **So the complementarity is between a dropout family and the HAND2 arm,
  and neither alone unlocks the adhesion work** — and the pairing must be
  re-derived at v0.6.0 before it is relied on. Any operational preference for
  `dropout_e2` over `dropout_IN_cAMP` is a separate claim about the frozen design
  and the assay, not an identifiability result, and U3 must state it as such.
- The HAND2-loss condition configs already exist in the committed v0.6.0 model,
  so the arm is expressible even though it is unscored.

The unit must also state, for each candidate, whether it is discriminable *in
principle* under any admissible arm, or only under a new assay class.

**Operational specification, because "extend the scoring" is not yet a method.**
The enumerator walks **free network variables**; v0.6.0's mifepristone,
anti-SPP1 and HAND2-loss perturbations are not free variables, they are
intervention-layer entries applied to condition configs. Extending the scoring
therefore means, concretely:

1. **Read the intervention set from `config/` rather than from the network** —
   the markerless protocol entries and their condition configs, which already
   name each perturbation and the arm it applies to.
2. **Realise each intervention as a clamp on the derived node it targets**, and
   partition states by the resulting column exactly as the current code
   partitions by condition-file input states. This reuses `_columns` and the
   existing partition logic; it does **not** introduce a second enumerator.
3. **Reproduce the committed v0.4.0 tables byte-for-byte first**, as the
   regression gate below requires, before any new arm is scored.

**This needs code, and that code is not authorized here.** Steps 1 and 2 are a
change to `src/dt_adoc/reporting/design_alias.py`, which is implementation, not
planning. **U3 as proposed is the written specification plus the v0.6.0
re-derivation that can be done with the existing API** — the model-version
override already works. The scoring extension is a **successor unit** requiring
its own authorization, and this plan does not fold it into a planning-only unit
to make the unit look complete.

**Mutation boundary, stated for both halves.** The planning half writes one
document and modifies nothing tracked. The successor half would touch exactly
one module and the regenerated tables under `docs/design_alias/`, and no
`network.bnd`, condition config or ledger.

**Files:** one new planning document. No tracked artifact is modified.

**Mutation boundary:** read-only against the model; the design-alias tables are
regenerated, not hand-edited.

**Tests:** regeneration must reproduce the committed
`docs/design_alias/node_design_classes.tsv` byte-for-byte before any new
candidate is scored; otherwise the analysis is not comparable to the existing one.

**Falsifier:** if regeneration does not reproduce the committed table, the unit
stops and reports a drift defect instead of proceeding.

**Does not:** propose, schedule or cost an experiment. Ranking a design is not
authorizing it, and the Stage-4c refusal already holds that the next unit on that
axis is identifiability design rather than the experiment.

### 6.0a The three late additions do not change these priorities

Three papers adjudicated on 2026-10-22 (§§4.13–4.15) produce **no node, no edge
and no rate between them**. Each yields evidence-ledger rows only, so each is
absorbed by **U1**, which already registers adjudicated evidence, and by **U2**,
which already records candidates and their conditions. **U1, U2 and U3 keep
their scope, their order and their verdicts.**

Two of the three additions sharpen an existing item rather than opening a new
one. The NNMT pathway is **unifying** for the stromal-state candidate R6, which
is useful because R6's case rested on a single separating result. And the SETD7
conflict reinforces why the staged `S_FOXO1` node stays in `model_gap`: the paper
that looked like it would resolve the edge above it does not.

**One item is added to U1's scope at no cost:** a standing methodological row
recording that AZD8055 is an mTORC1/mTORC2 inhibitor and is never a
FOXO1-specific intervention in this project.

### 6.0b The 2026-10-22 external-review delta does not change them either

A second external review and a 31-candidate rule table were supplied on
2026-10-21 and reconciled on 2026-10-22 in
`docs/v05_external_review_delta_2026-10-22.md` and its TSV. **None of the 31
candidates is promoted to a node, edge, rate or sign**, so U1, U2 and U3 again
keep their scope, order and verdicts. Four additive amendments follow from it and
are specified in that document's §5. **U1 gains seven mutations from the delta,
all of them appended article rows, and no field correction** — U1's
`PDF-048` row correction is pre-existing and unaffected by the delta, and it
moves **three** fields rather than one for the reason given in U1's mutation
boundary: Kakar-Bhanot 2019,
Tamura 2024, Yang 2026, Yu 2026, Chen 2026, Konyushatova 2025 and
Izmaylova 2026. The count is at **article** granularity, because U1 requires one
digest, DOI and read panel per article: the delta's eleven figure-verified rows
span thirteen articles, since one row covers three papers, and six of those
thirteen are already registered and carry no new evidence.

Two things an earlier revision of this paragraph got wrong, both withdrawn.
**It counted three manifest-identifier corrections as U1 mutations.** They are
not: `PDF-011`, `PDF-015` and `PDF-034` are already present and correct in
`context/literature/pdf_manifest.tsv`, so there is nothing in a ledger to
correct. Those three are corrections to the **external review document**, which
reported the papers as unregistered, and they are recorded in the delta's §2.1.
U1 edits no existing row. **And it said the remaining delta rows stay "outside
every canonical ledger".** That is false for the six figure-verified articles
already carrying a `REF-` or `PDF-` identifier — Dong 2025, Ma 2023, Ruan 2026,
Paule 2012, Peng 2021 and Marwood 2009. The accurate statement is that those
articles **receive no new entry**, their adjudications living in §4 of this plan;
only the rows that are genuinely in neither digest-bearing ledger are outside
them. **U2 gains one new row
(N8)** and two field revisions to mutations it already performs (TI-04, N5),
taking it from fourteen mutations to fifteen. **U3's candidate list gains the
HBP1 seam conditionally**, on figure-level adjudication of Guo 2026 and Huang
2022, neither of which this repository has read at panel level. The two findings
that would
have changed a verdict, had they gone the other way, both failed to: the SETD7
sign is still unassigned, and the PRL/IGFBP1 dissociation lands on an observation
mapping the repository has already registered as a rejected gap, so **TI-04 stays
deferred on an unchanged blocker**.

### 6.1 R3-a1 — prediction-identical, still inside the pause, still not a unit

An earlier revision marked R3-a1 **GO** and then explained why it was
nonetheless absent from U1–U3. Both halves of that are superseded: §5.2 now marks
it **WAIT**, because prediction-identity alone does not meet the pause's
carve-out, which also requires the change to touch only how perturbations are
represented.

Two things survive the correction and are worth keeping in view for the owner.
The edit **does** change zero nodes across all 65,536 states, so authorizing it
would carry no prediction risk. And its value is not standalone — it is half of
the joint R1 + R3-a1 condition, the only configuration in which the eight
adhesive disjuncts become live (§5.1a). Landing it alone would also set up the
attribution problem the no-bundling rule exists to prevent in reverse: a later
R1 unit whose measured effect is attributable only because its partner landed
silently months earlier.

So it is **neither proposed as a near-term unit nor recommended for separate
authorization**. It is registered as a deferred increment alongside R3-a2 (§6,
U2), and it becomes live as part of the joint unit when the pause lifts.

### 6.2 The zero-change option, stated explicitly

**Doing none of U1–U3 is admissible and is not absurd.** Its cost is that the §4
adjudication exists only in this document and in an untracked scratch directory;
the next session re-reads the articles the reconciliation TSV marks adjudicated
— **60 rows spanning 58 distinct articles**, two being held in two renderings —
to recover it. Its benefit is that no canonical
ledger moves while the pause is in force. **Recommended against**, because U1 and
U2 are additive, reversible and carry the adjudication into artifacts the review
gate can see — but it is the owner's call, and nothing in this plan executes
without it.

---

## 7. Reconsidering the previous revision's §4 decisions

The request requires the staged decisions to be reconsidered **from** the
adjudication, not merely restated. Each is taken in turn.

### 7.1 The pause — all three resume triggers are false

| trigger | status | evidence |
|---|---|---|
| 1. `dropout_e2` returns data | **FALSE** | `docs/phase1b_closure/prospective_allocation_manifest_template.tsv` still reads `REQUIRED_PRE_RUN_MANIFEST` in 9 rows, and the per-analyte detection limits for PAEP, IGFBP-1 and PRL are unrecorded. The run has not happened. |
| 2. a cell-associated assay is funded | **FALSE** | no artifact records funding for separate surface CD98/CD9, pSTAT3 or α-DG-N measurement. |
| 3. the redundant-adhesion structure is repaired first | **FALSE** | §3.2: the adhesive disjunction and the barrier prefix are both still vacuous at v0.6.0. |

**Trigger 3 is self-referential, and this plan reports it rather than resolving
it.** The repair it names is itself a topology change on biological grounds, so
the pause's own scope paragraph bars it. The carve-out does not help: it exempts
only a change that leaves every prediction identical **and** alters only how
perturbations are represented, and the redundant-adhesion repair fails the second
limb even in the one part of it that satisfies the first (§5.2). The pause can therefore only lift
through trigger 1 or 2, or through an explicit owner decision. **This is a
governance observation for the owner, not a licence to proceed**, and this plan
does not treat trigger 3 as satisfiable from inside.

### 7.2 The CDH1 withdrawal — upheld, but three of its four reasons were artifacts

The previous revision withdrew CDH1 as the preferred first adhesion route on four
grounds. Against the primary data:

| reason | verdict after adjudication |
|---|---|
| (a) contact-sufficiency is unlicensed | **Correct, and understated.** The rule is not unlicensed, it is **contradicted** by four panels of the paper it cites (§4.2). |
| (b) null at `OUT_STABLE_ADHESION` | **Correct, and for a deeper reason than the previous revision gave.** It is not merely an artifact of the contact identity: under R2-a the node is **still absorbed and still phenotype-inert**, verified over all 65,536 states. An earlier revision of this subsection claimed "under R2-a it would not be"; that is **false and is withdrawn**. Nothing short of the joint R1 + R3-a1 condition makes this disjunct live. |
| (c) a prior unit already refused a contact-bearing determinant | **An artifact of (a).** That refusal binds the *contact* form only and says nothing about an hCG-driven form. |
| (d) collinear with the arm family in all declared conditions | **Partly rebutted.** R2-a **disjoins** `IN_HCG` with `IN_EMBRYO_CONDITIONED_SIGNAL`, both undeclared inputs, so it is not collinear with the arm family. The honest objection is different and stronger: **`IN_HCG` is not ADOC-measurable**, and `E_CDH1_APICAL` is design-aliased with the three embryo inputs (§3.4). |

**The withdrawal is upheld on identifiability**, which is the axis §5.1 ranks on,
and is the axis the previous revision reached by a partly artifactual route. The
decisive new fact is different from all four: **`E_CDH1_APICAL` is phenotype-inert
whatever it equals**, because both disjunctions it enters are vacuous — and §5.1a
shows that vacuity is overdetermined, so it survives any single repair. Correcting its rule is a **provenance
repair**, not a route to discriminability.

### 7.3 The replaced prioritization rule — upheld, and the "addition" is withdrawn

Ranking by identifiability among licensed candidates stands (§5.1). An earlier
revision added that a **dependency constraint outranks it**, namely that R1 must
precede N3, R3-a and R2. **That addition rested on the ordering claim §5.1a
withdraws and goes with it.** The corrected statement is narrower and is not an
ordering at all: **R1 and R3-a1 are a joint precondition for making the
disjunction clamp-sensitive**, and nothing else is downstream of either. Neither
is "inert" in the loose sense: R3-a1 changes no prediction, while **R1 alone
changes six nodes' predictions and de-absorbs nothing** (§5.1a).

**And §5.1a now caps what that joint step is worth.** It yields three terms, of
which only two survive the endogenous test, and both of those are defects rather
than mechanisms. So the joint repair is a **prerequisite for any route work, not
a route repair in itself**, and §5.1b shows it additionally needs a CDH1 decision
to be biologically admissible. Identifiability ranks what remains.

### 7.4 What the previous revision got right and this one keeps

The structural results — the alias classes, the vacuous adhesive disjunction, the
vacuous barrier prefix, the relay-only difference between the two routes, and
both measured nodes being phenotype-inert — were **re-derived from the
repository's own loader this session** and are confirmed. The 9/12 split of
`IN_EMBRYO_CONTACT` across the 21 declared conditions is confirmed. The B7
deferral is confirmed. The withdrawal of the minimal-sufficient-subset claim's
load-bearing role is kept (§3.2).

### 7.5 One claim from the previous revision this plan retires

The previous revision recorded the §E.2 crosswalk as **unachievable under this
pass's boundaries** and removed every corpus-derived number. §2 shows the
crosswalk was achievable: the obstacle was the assumption that reproducibility
requires a *commit*, when the review subject is the working tree. The numbers are
restored and each is a query against a repository artifact.

---

## 8. Validation and falsification

### 8.1 What would make each unit wrong

Each unit's falsifier is stated in §6 and is a property of that unit's own
output, not of the biology. The candidates' falsifiers are in the matrix's
`falsifier` column. They are deliberately qualitative: MaBoSS here runs
`duration_units=relative_only`, and day-3 and day-6 conditions carry an identical
Boolean input vector, so **no physical-time claim and no rate calibration is
admissible from this model**, and none is proposed.

### 8.2 The route-independence test, and why a count will not do

A future de-absorption unit must demonstrate that route independence **actually
increased**, rather than that a switch slowed down. A bare fall in the
phenotype-inert count will not show this: the pause note records that count
*rising* across v0.5.0–v0.5.2 as **correct** work. The conservative test a future
unit must pass, stated so it can be challenged now:

1. **An explicit witness assignment** — a concrete state in which the two
   adhesion routes take different values, written out, not asserted.
2. **Instantiability** — that assignment must be reachable under a declared
   condition config, not merely in the 65,536-state enumeration.
3. **Relays held fixed** — the witness must survive with all three
   `X_INTERFACE_*_RELAY` priors held constant, or the "independence" is just a
   relay flip (§3.2).
4. **Prior-robustness** — the witness must not depend on a particular hand-set
   relay value.
5. **Alias-class non-membership** — the newly independent determinant must not
   join an existing alias class, and **the repaired node must not join one
   either**. Two candidates fail this test, and the second was found only when the
   test was applied to this plan's own top-ranked unit:
   - **N2-GLYCAN fails** on the determinant: sTn is P4-driven and would enlarge
     the nine-member secretory class.
   - **R1-a fails on the repaired node**: moving `E_GP130_STAT3` into the OR
     *alone* makes `E_RECEPTIVE_SURFACE` exactly `IN_E2 ∧ IN_PROGESTIN` and
     enlarges that same class from nine to eleven (§4.1). R1 passes only in the
     joint R1 + R3-a1 form.

   A test the plan states and does not run on its own preferred candidate is
   decoration. It is run here.

**Test 6 read against R1, and two senses that must not be run together.** A
size-1 deletion control asks whether removing one determinant changes the node.
**R1-a fails it too**: once `E_GP130_STAT3` is moved into the OR, deleting that
disjunct leaves `E_RECEPTIVE_SURFACE` unchanged, because `E_CD98_CD9` is
identically equal to it and still satisfies the disjunction. An earlier revision
said R1 alone "would pass test 6"; that is wrong and is withdrawn.

The general point stands and is why the tests are not sufficient alone. Tests 1–6
are about **absorption**. R1 alone changes six nodes' predictions while leaving
all eight disjuncts absorbed (§5.1a), so a unit reporting only absorption results
would describe an edit that moves every endpoint as though it moved nothing.
**A prediction diff over all 65,536 states must therefore be reported alongside
tests 1–6** — the discipline §8.4 already requires for provenance, applied to
acceptance.
6. **A size-1 deletion control** — deleting the new determinant alone must change
   the node, with an alias negative control that does not.

7. **Endogenous non-redundancy** — delete the candidate determinant alone from
   its reader while **every other node keeps its own rule**, and re-derive over
   the full state space. It qualifies as a route only if that deletion changes
   the reader in at least one state. **Clamp sensitivity is reported separately
   and never substituted for this.** Because a determinant can be individually
   redundant while a subset is jointly load-bearing, the unit must also delete
   **every subset** of the candidate group, not only singletons. §5.1a is the
   worked example: of the eight adhesive disjuncts, two pass and six fail
   individually, and **no subset of the six changes anything at all**.

### 8.3 Negative controls the plan commits to

- For any candidate wired to an unread input (R2-a, N3), the negative control is
  the same rule with the input held OFF, which must reproduce the committed node
  exactly.
- For any barrier re-specification (R3), the negative control is the naive sign
  inversion, which **must fail** — §4.5 establishes it is contradicted, so a
  variant family in which it passes is mis-specified.
- For **R4-b** — the only R4 edit proposed, since R4-a proposes none — the
  negative control is the committed cascade under progestin alone, which must
  continue to produce BMP2. **A variant that fails this control has enacted R4-a**
  (§4.8) and must be rejected on that ground rather than reported as an
  IHH result.

### 8.4 Provenance discipline for any future unit

Model version, `network.bnd` blob, condition-config set, seeds, trajectory count
and the structural-loader output must be recorded together, and the structural
figures must be regenerated rather than quoted from another version. §3's
reproduction command is the template. A unit that quotes a count from a different
model version without re-deriving it under its own condition set is invalid.

---

## 9. Independent scientific review, and what was done with it

### 9.1 Two reviews, and what each covered

**The first** was commissioned on an earlier state and is recorded in §9.2.
It returned six blocking findings, all accepted and repaired.

**The second** was commissioned on the final state, because the first did not
see §4.10's Hewitt re-read, §4.11 PODXL, §4.12 the stromal state, or §5.1a's
structural correction. It is the review this section now leads with.

- **Reviewer:** an AI reviewer, read-only; the working tree was unchanged at
  exit.
- **This is same-model-family review.** Author and reviewer come from the same
  model family, which is weaker than independent review, and it is **not** an
  `aih` gate verdict.
- **A second model declined this subject matter. No review from it was
  obtained and none is claimed.**
- **Verdict: DO NOT APPROVE AS SUBMITTED — nine blocking, ten advisory.**

**No scientific verdict moved.** Every WAIT and NO GO in §5.2 survives, and the
reviewer re-derived §3's baseline, §5.1a's deletion table, §5.1b's four option
counts and §4.11's 1,920→0 clamp result with the repository's own primitives,
all reproducing. It also verified every *Fertil Steril* number in §4.11 against
the PDF.

### 9.1a The nine blocking findings and their disposition

All nine accepted; none deferred. Three were re-derived independently before
acting.

| id | finding | disposition |
|---|---|---|
| B-1 | §5.1a mis-attributed the three terms: the six supply **none** of them, `X_SPP1_LUMEN_FREE` supplies both hormone terms alone | **Fixed.** Re-derived independently and the result **strengthened**: no subset of the six changes anything, and `{E_CDH1_APICAL, X_SPP1_LUMEN_FREE}` reproduces the rule exactly |
| B-2 | "the defect is confined to the epithelial node" was false — `X_ADHESION_ROUTE_REDUNDANT` moves in 2,048 of 4,096 states | **Fixed** (§5.1b); the `OUT_` half was correct and is kept |
| B-3 | §2.4's bold lead said 56 where its own body derives 58 | **Fixed** |
| B-4 | §6.2's "52 articles marked adjudicated" does not reproduce; the column gives 60 rows / 59 articles | **Fixed** |
| B-5 | R5 simultaneously governed and not governed by TI-06, across §5.2, §6/U2 and two matrix fields | **Fixed** in all four places |
| B-6 | the Hewitt PDF re-read never reached the matrix or §10.3 | **Fixed**; the "licensed sign is suppression" wording reconciled with §4.10's "wrong input, not a sign reversal" |
| B-7 | the matrix's claim that R2-b enlarges the secretory class is false | **Fixed.** Re-derived: the class stays at 9 and CDH1 joins none |
| B-8 | §11's change log described a tree that no longer exists | **Fixed**; it now matches `git status` exactly and lists the 147-screen edit |
| B-9 | §5.1b routed the CDH1 choice to §10.1, which did not carry it | **Fixed**; §10.1 item 4 now carries the four options with their numbers |

**The finding worth the owner's attention is B-1, because it runs against this
plan's own case.** Under the joint repair, the `E_GP130_STAT3` disjunct that R1
creates is itself implied by `X_SPP1_LUMEN_FREE` and deletes without effect. So
**R1 corrects a biologically wrong rule and buys no route by this plan's own
Test 7.** That is an argument for R1 on correctness grounds and against ever
describing it as route-liberating.

### 9.1b Advisories

Ten, all accepted. The substantive ones: the §4.1 heading said "refuted" where
its body says "unsupported" and §10.4 compounded it; Test 7 measures Boolean
non-redundancy rather than "adds a mechanism"; §5.1a's endpoint column omitted
the route node; the matrix said R1 moves "all four endpoints" when three `OUT_`
nodes and two route nodes move; §4.11 leaned on a "data not shown" null that
§4.5 refuses elsewhere; a p-value was quoted more precisely than the legend
gives it; and §10.4's "six of eight" understated the plan's own result, which is
seven of nine, jointly as well as individually.

**One reviewer observation is recorded because it cuts the other way:** §4.11 is
*understated*, since the complement form can only ever be ON where receptivity is
already OFF, so refuting it has no structural consequence at all.

### 9.2 The first review, on an earlier state

Commissioned before §4.10's Hewitt re-read, §4.11, §4.12 and §5.1a existed.
Reviewer: AI reviewer, read-only, same model family. **Verdict: DO NOT APPROVE AS
SUBMITTED — six blocking, ten advisory.** All six were accepted and repaired:
the corpus crosswalk and its counts, the withdrawn ordering claim, the
half-stated R1 structural effect, the sLeX carrier contradiction, the missing
§9 and §10, and two overstatements U2 would have written into a tracked ledger.
Two advisories changed something: the R3-a split, and the correction that
`dropout_e2` is not the only family separating the measured nodes.

**That review endorsed one thing the repository gate later refuted** — it read
the pause carve-out as a single criterion and approved R3-a1 as GO. §5.2 now has
it WAIT. Recorded because it bears on how much weight same-vendor review carries
here.

### 9.3 The strongest argument against each near-term unit

Recorded because §E.6 asks for it specifically, and because each is a real cost.

- **Against U1:** its "additive registration only" boundary survives only because
  it excludes the two mapping defects, and its riskiest field is the one recording
  "the adjudicated outcome". **Accepted and narrowed in §6:** U1 records evidence —
  paper, panel, system, layer, sign — and points at this plan for verdicts rather
  than restating them in a ledger.
- **Against U2:** its entire deliverable is prose in a tracked decision ledger, and
  a register row is read later as established fact. That is exactly how B6's two
  overstatements would have become durable. The mitigation is that U2's text now
  carries the qualifiers verbatim.
- **Against U3:** it could be read as re-doing
  `docs/identifiability_experiment_design.md`. The reviewer agreed it is not —
  that document covers the existing variant set, U3 covers R1–R4 — but U3's seeds
  inherited two errors (§3.5's "only family", and the withdrawn ordering claim),
  which is a fair warning that a design unit built on a wrong structural premise
  produces confident wrong rankings.
- **Against all three:** the zero-change option in §6.2 remains available, and
  under a pause that no trigger has lifted it is not an unreasonable choice.

---

## 10. Requests to the owner

Only decisions whose answer changes what happens next. Nothing proceeds without
them.

### 10.1 Authorizations the plan needs

1. **Authorize U1 and U2** (§6). Both touch canonical ledgers, which the governing
   request forbids without further authorization. Both are additive and
   reversible. Without them the adjudication lives only in this document.
2. **Decide the two mapping defects**, which this plan classes as pause-scoped and
   therefore does *not* fold into U1: the `CDH1`/`CTNND1` `any_of` union in
   `config/node_entity_map.tsv` (§4.2) and the `node_dictionary.tsv` "CD98 or
   CD9" versus "surface CD98 and CD9" mismatch (§4.3). If you read entity-map
   corrections as outside the pause, they join U1 and the plan is better for it.
3. **Three choices this plan made without consulting you, flagged because the
   review gate flagged them.** None was treated as settled and each is reversible
   in one edit, which is why none met the consultation bar — but each is yours:
   (i) **identifiability is the primary ranking axis** among licensed candidates
   (§5.1), inherited from the previous revision and not re-opened here;
   (ii) the **six-part route-independence acceptance test** (§8.2), likewise
   inherited, and now run against this plan's own top candidate, which fails it;
   (iii) the **ranking of the four measurements** (§10.3). Items 1 to 3 restate
   the pause's own resume triggers and the repository's own fifth-arm scoring,
   and add no judgement. **Two things in it are mine**: the preference between
   `dropout_e2` and `dropout_IN_cAMP`, which is operational and labelled as such,
   and **item 4, the progestin-alone arm, which is a measurement this plan
   proposes rather than inherits** — added because R4-b turns out to be blocked
   on R4-a and nothing in the corpus can resolve it.
4. **Choose among the four CDH1 options, or decline to** (§5.1b). This is the
   decision §5.1b routes here, and it is not a modelling preference: under
   R1 + R3-a1 an unprimed epithelium reads as receptive on embryo contact alone,
   in all 4,096 such states.

   | option | hormone-free contact states with `E_RECEPTIVE_SURFACE` ON | disjuncts with endogenous influence |
   |---|---|---|
   | null — CDH1 unchanged | 4,096 of 4,096 | 2 |
   | R2-a — `IN_HCG ∨ IN_EMBRYO_CONDITIONED_SIGNAL` | 3,072 | 2 |
   | R2-b — `E_SECRETORY_STATE ∨ IN_HCG` | 2,048 | 2 |
   | R2-c — `IN_EMBRYO_CONTACT ∧ E_SECRETORY_STATE` | **0** | **1** |

   Only R2-c removes the counterexample, and it costs the only non-hormonal
   route. **R2-a is the one option matching the repository's own
   `candidate-nodes.tsv` logic hint at confidence 7.** Nothing here is
   recommended; all four are live, and the null is one of them.

5. **Rule on the self-referential resume trigger** (§7.1). Trigger 3 names a
   repair the pause's own scope bars, so the pause can only lift through triggers
   1 or 2 or an explicit decision. This plan does not treat it as satisfiable from
   inside.

### 10.2 Primary sources whose absence changes a decision

Only two, and both are narrow:

1. **The Sofia 163-PDF archive manifest** — any list with DOIs or digests. Without
   it the 147/163 overlap is uncomputable (§2.3) and no honest total exists.
2. **A decision on `PDF-048`'s digest** — not the paper. An earlier revision
   requested Zhou 2021 as a missing source; **the article is in the local corpus**
   under a different rendering, so that request is withdrawn (§2.4 finding 1).
   What is needed is a choice: re-register the manifest row against the digest
   actually held, or keep the recorded digest and record the held rendering as a
   second row. This is U1's decision to carry out, not a literature request.

**Heng 2010 is no longer a request: it is held in the local corpus and has been
read** (§2.2, §4.6a) — like every other PDF, untracked and identified in the
reconciliation TSV by digest rather than by path. Its
three open questions — inhibitor specificity, dosage and temporal ordering — are
now answered, and all three answer negatively, so it adds an evidence-ledger row
and no executable edge.

**Hewitt 2022 is no longer declined: it has been adjudicated** (§4.10). An earlier
revision refused it on the ground that it could not change a verdict. It did not
change the verdict, but it re-based it — see §4.10, where the progestin effect is
recorded as **one annotated donor**, not the two of three the paper's prose
claims, and the antagonist is recorded as not PGR-specific. Declining a source
the request names, on a prediction about what it contains, was the wrong call. **No further primary source is requested.** What Hewitt leaves
open is not a missing paper but missing measurement, and it moves to §10.3
item 4 rather than staying here: it has no MPA-alone arm, its effect holds in 2
of 3 donors, its RU486 reversal rests on one donor, and it reads transcript
rather than protein.

### 10.3 Measurements that would unblock the most, ranked

1. **`dropout_e2`.** The **pre-registered** arm family the frozen design was built
   around, and the pause's first resume trigger. It separates the two measured
   nodes — but it is **not the only family that does**: four of the six
   `dropout_IN_cAMP` variants separate the same pair (§3.5). No dropout candidate
   has a committed condition config, so "committed" would be the wrong word here. Its blockers are
   operational, not scientific: the allocation manifest and the per-analyte
   detection limits (§7.1).
2. **A HAND2-loss arm.** In the v0.4.0 scoring it is the only candidate that
   splits the CD98/GP130 design class, and its condition configs already exist in
   the committed v0.6.0 model. It separates no measured node, so it buys
   structural identifiability without observational leverage unless paired with a
   readout. **Its v0.6.0 value is unscored** (§3.5), because the enumerator walks
   only free network inputs and this perturbation is no longer one — so this keeps
   the arm in view rather than costing it.
3. **A cell-associated assay** — separate surface CD98 and CD9, pSTAT3, α-DG-N.
   The pause's second resume trigger, and the only route to testing R1 and N3
   against measurement rather than against structure.
4. **A progestin-alone arm with a BMP2 readout, in human stromal cells.** Added
   because §4.8 and §4.10 together make it load-bearing: R4-a is unresolved in
   both directions, R4-b is **blocked on R4-a**, and no source in this corpus
   tests progestin without estrogen or cAMP — Hewitt included. It is the single
   measurement that would let the licensed IHH sign be written into the model
   without silently deciding R4-a. A protein-level IHH readout across more
   donors would additionally firm up R4-b itself, which currently rests on 2 of
   3 donors with a one-donor antagonist arm — corrected at §4.10, where the
   figure annotates **one** donor and the antagonist is not PGR-specific.

**These are requests for a decision about measurement, not a design.** Ranking a
design is not authorizing it.

### 10.4 Three judgements this plan keeps separate

Several candidates score differently on each, and collapsing them is how a
defensible candidate gets discarded for the wrong reason:

1. **Biological correctness** — is the committed rule right? R2, R3, R4-b and R5
   fail this on positive contrary evidence. **R1 is different and is listed
   separately**: its AND-prefix is **unsupported**, an absence of evidence for
   necessity, not a demonstration that GP130 is dispensable (§4.1).
2. **Structural or functional independence in the model** — would repairing it
   add a route, or only a term? §5.1a's Test 7 answers this, and **seven of the
   nine disjuncts in the repaired rule fail it — individually and jointly**,
   including the GP130 disjunct R1 itself creates.
3. **Identifiability from available ADOC measurement** — could the repair be
   told apart from its alternatives by anything the platform records? Almost
   nothing passes: both measured nodes are phenotype-inert.

**Present-day ADOC identifiability is not a requirement for retaining a
strongly-supported literature candidate**, and this plan retains several that
fail it — R5 and N4 most clearly. It *is* a requirement for claiming that ADOC
observations **selected, validated or calibrated** a candidate, and no such claim
is made anywhere in this document.

---

## 11. Change log

**Three paths, which is exactly what `git status --porcelain` reports for the
state submitted.** An earlier revision of this table described a different tree
and is superseded; the correction is recorded rather than quietly applied,
because §2.1 makes the working tree the review subject and §11 is therefore
answerable to it.

| path | status | what changed |
|---|---|---|
| `docs/v05_literature_guided_implementation_plan_DRAFT.md` | **modified** | this document |
| `docs/v05_traceability_identifiability_matrix_2026-10-21.tsv` | **modified** | §5's matrix, 12 rows × 20 columns |
| `context/literature/reviews/adoc_2026-10-21_147_paper_screen.md` | **modified** | page numbers remapped to the rebuilt 156-article bundle, and the nine articles the bundle holds but the screen never screened appended as a separate, clearly-labelled section |

**Already committed earlier on this branch, and therefore unmodified now:**
`docs/v05_literature_corpus_reconciliation_2026-10-21.tsv`,
`docs/v05_li2026_s2_roundii_screening_annex.tsv`, and the one-line
`context/literature/supplements/` entry in `.gitignore`. An earlier revision
listed the first two as *added* and `.gitignore` as *modified*; all three are in
`HEAD`.

**The 147-screen edit belongs to this pass and is listed above.** It follows from
rebuilding the literature bundle, which grew from 147 to 156 articles and so
invalidated every page reference in that index. Earlier revisions asserted "no
file outside these five was changed", which that edit falsifies.

**Outside version control, and therefore outside the review subject:** the
bundle at `output/literature_bundle/`, which is gitignored.

**Rebuilt on 2026-10-22 and the 2026-10-21 build replaced**, because the corpus
grew and was reorganised after that build (§1 of the gap assessment). The
2026-10-21 bundle of 156 articles and 2,307 pages no longer exists; quoting
those figures now would describe a file nobody holds.

| | 2026-10-21 build | 2026-10-22 build |
|---|---|---|
| source files | 156 | **183** |
| distinct articles | 156 | **164** |
| pages | 2,307 | **2,435** |
| bundle PDF size | 59.4 MB | **62.2 MB** |

The 19 extra source files are duplicate copies of papers held both at the top
level and under `prl_igfbp1_foxo1/`; the merge collapses them by accent-folded
filename, so each appears once in the body with its contents line pointing at
the single copy. Index rows therefore total 183 while the body holds 164
articles. Built with the documented five-step pipeline in
`output/literature_bundle/scripts/README.md`. **All 2,677 rendered pages passed
the same visual-difference gate the previous build set**, worst page 1.91 %
against the 2 % limit, so no page exceeded it. The bundle carries 1,910
bookmarks and a three-page contents section.

**Not done, deliberately:** nothing under `data/`. No model, condition config,
protocol, calibration, observation map, phenotype definition, perturbation,
intervention library or canonical evidence ledger. Not
`docs/deferred_topology_register.tsv`. No model version. No simulation run and no
seeds spent. The `dropout_e2` pause is not lifted and no frozen artifact is
touched. No PDF or publisher supplement was committed.

**Verified, not asserted.** `git status --porcelain` over `models/`, `config/`,
`data/`, `docs/experiments/`, `docs/phase1b_closure/`, `docs/phase2a/`,
`docs/scrna/`, the canonical ledgers and the deferred register is **empty**, and
`git hash-object models/superset/adoc-literature-superset-v0.6.0/network.bnd`
still returns `ee40f2a4e98f74a461dc308bf83323785eb45bb4`, the blob the governing
request names.

*Earlier commits on this branch did create commits; the "no commit" wording of
earlier revisions described the pass before the owner authorised committing for
external review, and is superseded.*

**Claim boundaries restated once, because this document is about a model of
implantation.** Nothing here is clinical. The model is a patient-contextualized
computational hypothesis, not a validated patient replica. Every rule discussed
is a candidate, and no perturbation discussed is causal biological evidence. No
physical time is inferred: `duration_units=relative_only`, and day-3 and day-6
conditions carry an identical Boolean input vector. No transition rate is
proposed anywhere in this plan.
