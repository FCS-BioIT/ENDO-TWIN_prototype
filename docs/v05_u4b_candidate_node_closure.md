# U4b — the fourteen Sept-11 candidate nodes, closed: nothing promoted, and seven were carrying a disposition they had not earned

> **SUPERSEDED IN PART, 2026-09-18 — read this before using any verdict below.**
> U4b closed with two of its nine references **access-blocked**, and said so. The
> blocked-source refresh of 2026-09-18 obtained, read and registered both, and
> **re-adjudicated the three candidates that depended on them**:
> `E_JAG1_NOTCH3` (`EVIDENCE_UNVERIFIED` → **`WAIT_FOR_EXPERIMENT`**),
> `E_GLYCOSYLATION_PROGRAM` (`RETAIN_CATALOG_ONLY` → **`REJECT`**) and
> `E_SLEX_SURFACE` (disposition unchanged, first failing criterion **§5(2) → §5(4)**).
> **The machine-readable dispositions table is live and already carries those
> verdicts**; the prose in §1a, §4.2 and §5 below describes the access state U4b
> faced and is left verbatim as the record of it. See
> `docs/curation_increment_08_blocked_sources.md` and
> `context/literature/reviews/blocked_source_refresh_2026-09-18.primary-verification.tsv`.
> **Nothing executable changed in either unit.**

**Unit:** U4b of `docs/v05_mechanistic_integration_plan.md`, inserted before U5.
**Outcome:** **no canonical promotion, and no rule, node, edge, threshold, rate,
istate, condition or phenotype changed.** All fourteen candidates from
`context/literature/staging/deep_research_adhesion_model_2026-09-11/` now carry an
explicit, auditable disposition with a separate node verdict and encoding
verdict, and **as U4b closed it** the closure issued **no `REJECT` and no
`MERGE_WITH_EXISTING`** (see the banner above and §7 for the live counts, which now
include one `REJECT`).
**Guards:** `tests/unit/test_v05_u4b_candidate_closure.py`.

**Provenance.** This document states U4b's current closure. Its review and repair
history is authoritative in the Git commits that carry it and in the harness
review record, and is intentionally **not duplicated here**.

**The executable digital twin is byte-identical to v0.4.** Free variables 19
(5 non-input), distinct Boolean functions 35, AC01 nine members — all unchanged,
and re-derived in this unit rather than quoted.

**Artifacts.**
`context/literature/reviews/deep_research_adhesion_model_2026-09-11.candidate-node-dispositions.tsv`
(14 rows, machine-readable) and
`…deep_research_adhesion_model_2026-09-11.primary-verification.tsv`
(9 rows, the §5(1) ledger **for this review**). The two must state the same verdict
for any candidate both name, which the guards enforce candidate by candidate.

---

## 0. What U4b was asked to do, and what it found

| item | result |
|---|---|
| Give all 14 candidates a literature-grounded final admission decision | **Done.** *As U4b closed them:* 0 PROMOTE, 1 RULE_VARIANT_ONLY, 2 WAIT_FOR_EXPERIMENT, 6 RETAIN_CATALOG_ONLY, 5 EVIDENCE_UNVERIFIED, 0 MERGE_WITH_EXISTING, 0 REJECT. *Live:* 0 / 1 / 2 / 6 / 4 / 0 / **1** |
| Reuse existing U3/U4 adjudication rather than repeating it | **Done.** `X_IL11` and `E_ITGA2B1` are reused unchanged; Marwood 2009 was **not** re-read |
| Ensure candidates absent from the Sept-16 research got no weaker standard | **This is where the unit earned its keep.** **Seven candidate nodes changed disposition**, arising from **five §4.1 classification entries**; five of the seven moved in the *stricter* direction |
| Trace each candidate to its actual supporting references | **Done, and it is the headline.** 8 of the 9 `DRREF-*` references had no local PDF, no canonical `REF-*` id and zero rows in `citation_verification.tsv`. Six are now verified; two are access-blocked; one candidate turns out to be **miscited** |
| Repair §5 where it is insufficient for this task | **Done.** §5 defined a disposition for exactly one failure mode out of five; §2 is the ladder as repaired |
| Model/rule changes only for candidates that satisfy the criteria | **None satisfy them.** Nothing changed |

### 0a. Prerequisites, checked before anything was edited

- **"Gates any v0.5 claim about `E_ESTROGENIC_PROLIFERATION` — so U3, U4 and U5."
  Still open, and U4b makes no such claim.** The node appears nowhere in this
  unit's adjudication. `E_ESR1_ACTIVITY` is adjacent but is a claim about
  `IN_E2` → `E_SECRETORY_STATE`, not about the proliferative state, and its
  disposition turns on a missing reference, which no answer to the owner question
  could supply.
- **D1.** U4b, like U4, is independent of D1. It makes no `AC01` or `AC04` claim
  that needs it. It does *measure* AC01's size repeatedly, which is a property of
  the committed rules and not of any post-extraction call.
- **The PDF library is gitignored and absent from this worktree.** Yu 2018 was
  read from the main checkout's copy; the other five reads are network
  retrievals held only in the session scratchpad. That is why **every** read in
  the ledger is recorded with a sha256 or an explicit route limitation rather
  than a repository path.

---

## 1. The provenance census, which decided most of the unit

`§4` already said "the 9 `DRREF-*` references have zero rows in
`citation_verification.tsv`". What it did not say is how much worse that is:

| reference | paper | local PDF | canonical `REF-*` | U4b outcome |
|---|---|---|---|---|
| DRREF-001 | Li 2013, WNT4/BMP2 | no | no | **verified** (PMC web) |
| DRREF-002 | Vasquez 2015, FOXO1/IRF4 | no | no | **verified** (PMC web) |
| DRREF-003 | Marwood 2009, IL-11/LIF | **yes** | **REF-072** | **reused**, not re-read |
| DRREF-004 | Kinnear 2019, SOX17 | no | no | **verified** (XML, sha256) |
| DRREF-005 | Yu 2018, ST3Gal3/sLeX | *supplied by the owner during this unit* | no | **verified** (PDF, sha256) |
| DRREF-006 | Ma 2023, sLeX/IL1B | no *(supplied 2026-09-18)* | no *(now **REF-077**)* | **access blocked in U4b**; read and registered 2026-09-18 |
| DRREF-007 | Zhou 2021, JAG1 | no *(supplied 2026-09-18)* | no *(now **REF-076**)* | **access blocked in U4b**; read and registered 2026-09-18 |
| DRREF-008 | Griffiths 2019, COL4A1 | no | no | **verified** (XML, sha256) |
| DRREF-009 | Liao 2024, BMP/SMAD | no | no | **verified** (XML, sha256) |

**Census, stated so it cannot be miscounted:** **six newly read in U4b** (Li 2013,
Vasquez 2015, Kinnear 2019, Yu 2018, Griffiths 2019, Liao 2024) **plus Marwood
2009 reused from U4 = seven of nine verified or reused**, and **two remain
access-blocked** (Ma 2023, Zhou 2021).

Plus one case that is not on this axis at all: **`E_ESR1_ACTIVITY` cites
`REF-020`, which is Zaragozano 2026 — the ADOC platform paper.** It studies
neither ESR1 nor receptor pathway activity. `mechanisms.tsv` DRMOD-06 states the
evidence as "model necessity plus ADOC hormonal context" in as many words. That
is a **miscitation**, and it is the only one of the fourteen in that state.

**Two provenance decisions, stated so they are not mistaken for oversights.**

- **The reads went into a new, review-scoped ledger.** U4 refused to backdate
  `CD98-d` into the Sept-16 review's files because that would misattribute the
  curation. Appending Sept-11 verifications to
  `deep_research_drug_targets_2026-09-16.primary-verification.tsv` would be the
  same error in the same direction, so U4b created the Sept-11 file the Sept-16
  review already has a counterpart for.
- **No `REF-*` id was allocated, no `pdf_manifest.tsv` row was written and no PDF
  was placed in the gitignored library.** Registration is repository curation and
  a shared-resource change; U4b is an adjudication unit. Each read is instead
  made checkable by its URL, retrieval date, byte count and sha256, which is what
  a later curation increment actually needs. This mirrors U4's handling of Yap
  2011 and is **not** an invariant — a later unit may legitimately register any
  of these papers while still refusing every mechanistic use of them.

### 1a. Two papers are blocked, and that blocks *promotion* only

**Both papers were obtained on 2026-09-18** and are now `REF-077`/`PDF-049` and
`REF-076`/`PDF-048`. The paragraph below records the access state at the time U4b
ran, which is what fixed its verdicts; it is not a current statement of
availability.

`Ma 2023` (`10.1093/biolre/ioad007`) and `Zhou 2021` (`10.1096/fj.202100590R`)
were subscription-only: Europe PMC returns no PMCID and
`availability = ['Subscription required']` for both, probed 2026-09-17. They are
recorded in `docs/paywalled_papers_needed.md` with the specific fields each would
unblock.

**Neither node is rejected on that ground, and the record says so in the row.**
Absence of access is not negative evidence.

What it does is fix *which criterion* fails, and the two cases differ — which is
why §5 states the rule generally rather than by example:

> **An inaccessible source blocks the criterion whose claim depends on it.** If
> **node admission** rests on it → **(1)**, `EVIDENCE_UNVERIFIED`. If the node is
> already established and the source is wanted only for the **determinant** →
> **(2)**, `RETAIN_CATALOG_ONLY`. In neither position is access failure negative
> evidence, and in neither does it by itself yield `REJECT`.

So `E_JAG1_NOTCH3` fails at **(1)** — Zhou 2021 is its only reference — while
`E_SLEX_SURFACE` fails at **(2)**, because Yu 2018 establishes surface sLeX
causally and Ma 2023 is wanted for the IL1B → FUT3 input alone.

---

## 2. The §5 admission ladder, as U4b repaired it

§5's node ladder had four criteria and stated a disposition for **one** outcome:
"Failing (4) but passing (1)–(3) is `RETAIN_CATALOG_ONLY`, not `REJECT`." It said
nothing about failing (1) or (2), and it never asked whether the proposed node
denotes a coherent state or duplicates one already committed. Those gaps were not
theoretical: **seven of the fourteen were sitting on dispositions those gaps
allowed**, and five of the seven were too lenient.

**(0) Node coherence, which fails two ways and must not merge them.**
Does the node denote a *single coherent biological state, as defined*, in this
system?

- **(0-refuted)** — evidence positively establishes that it does not → `REJECT`,
  scoped to that definition. **The burden is on the rejecting unit** to show the
  definition *logically entails* what the evidence falsifies.
- **(0-insufficient)** — the definition is merely *not established*: a named
  component has no evidence either way, or the reference bearing on it was never
  read → **`RETAIN_CATALOG_ONLY`**, with the component named.

`E_GLYCOSYLATION_PROGRAM` and `X_ECM_FN1_COL4` both fail at **(0-insufficient)**,
and **U4b issues no `REJECT` at all**.

**(0b) Non-duplication — semantic state and compartment first, Boolean function
last.** Satisfied only when two nodes agree on **the state they denote and the
compartment they denote it in**, with equivalent rather than merely overlapping
measurement sets. **Equality of the current effective Boolean function is never
sufficient**, because that function is a property of the *proposed rule* — and
where the rule is rejected, its function equality is evidence about the rejected
rule and nothing else. **No Sept-11 candidate meets this criterion**, and U4b
issues no `MERGE_WITH_EXISTING`.

**(1) as it stood. (2) gains an explicit test.** A node defined as an activity,
localisation, cleavage or engagement state is **not** given a determinant by
evidence that something moves its namesake's **mRNA or total protein**.
`AGENTS.md` forbids that substitution for the *node*; this forbids it for the
*edge into* the node, which is the DRE009 failure mode arriving one step upstream
and is easy to miss because the citation looks right. **(3)–(4) as they stood.**

**The disposition rule: the first criterion that fails governs.** This was the
piece missing altogether, and its absence is exactly how §4.1 drifted — its rows
were assigned on the most *interesting* failure, which is almost always the
structural one, rather than on the first.

| first failing criterion | disposition |
|---|---|
| (0-refuted) definition falsified | `REJECT`, scoped to the definition |
| (0-insufficient) definition not established | `RETAIN_CATALOG_ONLY`, component named |
| (0b) non-duplication | `MERGE_WITH_EXISTING` |
| (1) primary verification | `EVIDENCE_UNVERIFIED` |
| (2) determinant | **`WAIT_FOR_EXPERIMENT` when the missing evidence can be obtained by a named experiment feasible within the current or planned ADOC programme; otherwise `RETAIN_CATALOG_ONLY`.** *Owner-ratified wording, 2026-09-18 — quoted in full below, and it governs* |
| (3) compartment / measurability | `RETAIN_CATALOG_ONLY` |
| (4) Δ and alias | `RETAIN_CATALOG_ONLY` — unchanged |
| several encodings remain defensible | `RULE_VARIANT_ONLY` — §5's existing consequence, orthogonal to the ladder |

The (2) discriminator operationalises §4.3's own gloss — "blocked on evidence we
have arranged to get" versus "blocked indefinitely" — because *nameable* is too
weak a test: almost any missing determinant can be named. **The governing wording
is the owner's, ratified 2026-09-18, and a later unit must apply it as written
rather than any paraphrase of it:**

> `WAIT_FOR_EXPERIMENT` when the missing evidence can be obtained by a named
> experiment feasible within the current or planned ADOC programme; otherwise
> `RETAIN_CATALOG_ONLY`.

Checked row by row, **the ratified wording changes no disposition.** Each row
records its own answer in the `unblock_locus` column, and a guard enforces the
rule per row.

**Two vocabulary values are added and one is restored.** `EVIDENCE_UNVERIFIED`
is new and necessary: without it, a candidate with no traceable source receives
the label reserved for one whose evidence was weighed and found sufficient at
(1)–(3). `MERGE_WITH_EXISTING` is **restored** from the repository's own earlier
vocabulary — `…2026-09-11.next-stage.md:61` lists it — which §4.3's requested
five-value set had dropped. Both are defined by §5 and **neither is used by any
Sept-11 candidate**, which is the correct outcome rather than an
embarrassment: a rubric needs the value for the case even when no candidate
reaches it.

**`formalism_verdict`: orthogonal to the ladder and subordinate to it.**

- **Earlier admission failures continue to govern.** `S_TGFB_CONTEXT` is
  `EVIDENCE_UNVERIFIED` **and** carries `outside_formalism`, and both are
  load-bearing: the first says nothing has been weighed, the second says weighing
  it would not be enough.
- **Only once (0)–(3) are satisfied** does `outside_formalism` — §8's **Q3**
  category, graded potentiation, timing, or dose- or context-dependent sign —
  **cap** the modelling disposition at `RETAIN_CATALOG_ONLY`.
- **It never produces a `REJECT`**, in either position, because the blocker is
  the model class rather than the biology.

This states for future candidates what TI011 said in prose and then flattened into
"REJECT THE NODE": its own reason is "not because the biology is weak but because
the model class cannot represent it". **U4b does not relabel TI011** —
`S_EPAC_RAP1` is not one of the fourteen, its prose already says the right thing,
and reopening a settled unit to change a label is exactly the speculative
reopening this branch forbids.

**And node verdict and encoding verdict are separate columns in every row.**
Rejecting an encoding never rejects a node. **Six** candidates have a defensible
node and a rejected encoding — `S_BMP_SMAD`, `S_FOXO1`, `S_WNT4_CTNNB1`,
`E_ITGA2B1`, `E_SOX17`, `E_SLEX_SURFACE` — the single most common outcome in this
unit, and invisible under one column.

---

## 3. The stromal chain: the evidence and the structure point opposite ways

`S_BMP_SMAD`, `S_WNT4_CTNNB1` and `S_FOXO1` were the bundle's "first high-value
de-aliasing nodes". Three papers were read for them and the biology holds up
better than the repository had recorded. The encodings do not.

### 3.1 `S_BMP_SMAD` — the paper that would have supplied the determinant does not

Liao 2024 (*Commun Biol* 7:227, read in full) is a much stronger paper than
DTR007's abstract-level basis suggested. **pSMAD1/5 is directly measured**, by
Western with densitometry, across an EPC day-2/4/6/8 time course in primary human
endometrial stromal cells from donors with (n = 4) and without (n = 5)
endometriosis. **SMAD1/5 siRNA causally impairs decidualization** — IGFBP1 and
WNT4 significantly down. **BMP2 add-back rescues** in patient-derived 2D cultures
*and* 3D assembloids. The EPC stimulus (35 nM E2, 1 µM MPA, 50 µM cAMP) is the
model's three stromal inputs.

So §5(3) is comfortably satisfied — the state is measurable, by a canonical
readout, and perturbable. §5(1) moves from nothing to full text.

**§5(2) does not move, and now it is established rather than inferred.** DTR007's
condition was "a determinant for BMP pathway activity that is not BMP2
abundance — receptor availability, an antagonist, or cAMP-dependence."

- In the only **physiological** comparison the paper makes, BMP2 transcript
  induction (Fig 3D) and pSMAD1/5 (Fig 3B/C) are **both** blunted in
  endometriosis. That is co-movement, not dissociation.
- BMPR2 and ACVR2A appear **only in the Discussion**, as a GWAS risk locus and as
  mouse genetics. Nothing is measured.
- The one real dissociation is **SMAD1/5 siRNA** — a laboratory construct, which
  is the §5(2) exclusion that already blocks PC6-b and TI009. The cleavage-site
  mutant and the siRNA are the same category of evidence.
- And the repository records **no endometriosis stratification for the ADOC
  donors**, so even the disease contrast has no ADOC image.

**Disposition `WAIT_FOR_EXPERIMENT`**, consolidating §4.1's split of
RETAIN_CATALOG_ONLY (TI006/7) and WAIT_FOR_EXPERIMENT (TI008) onto the one that
matches the first failing criterion. The evidence state is upgraded; the
promotion state is not. Structurally, U4b re-derived TI006 (35 → 35, E_IHH 5 → 6)
and TI008 (35 → 37 with an invented free determinant) and both reproduce exactly.

### 3.2 `S_WNT4_CTNNB1` — a faithful encoding that is inert *because* it is faithful

Li 2013 (read in full) is strong and specific. WNT4 is not a correlate of BMP2:
"administration of recombinant BMP2 to HESCs treated with WNT4 siRNA **failed to
promote differentiation**". Active β-catenin accumulates in the nucleus on WNT4
overexpression, and β-catenin knockdown blocks the effect — so the node is an
*activity* state, not an abundance proxy. Liao 2024 independently shows WNT4
falls on SMAD1/5 knockdown.

And yet: **the paper tests exactly one input to WNT4.** A necessary mediator with
no second determinant is, in a Boolean model, *precisely an alias*. So
`S_WNT4_CTNNB1 = S_BMP_SMAD` is a faithful encoding of what was measured and is
inert for that reason. That is a formalism consequence, not a staging defect, and
§4.1's "biology accepted, staged form rejected" understates it: no better staging
exists on this evidence.

**The largest structural gain in this unit is available here, and is refused.**

`IN_XAV939` is a declared v0.4 input that **no rule reads** — confirmed from
`load_structure().unread_inputs`, which returns exactly
`('IN_XAV939', 'IN_HCG', 'IN_EMBRYO_CONDITIONED_SIGNAL')`. XAV939 is in the ADOC
conditioning protocol. So wiring it to the stromal WNT arm costs **no new free
variable at all**:

| model | distinct Boolean functions | AC01 | decidual | E_IHH |
|---|---|---|---|---|
| committed | **35** | 9 | 6 | 5 |
| `S_WNT4_CTNNB1 = S_BMP_SMAD and not IN_XAV939` | **36** | 9 | 6 | 6 |
| … plus `S_FOXO1 = S_WNT4_CTNNB1 and S_PKA` | **37** | 9 | 6 | 6 |

Nineteen free variables before and nineteen after. No alias class enlarged.
**Read the two rows separately**: the XAV939 rule *alone* is 35 → 36, and 35 → 37
needs the evidenced `S_FOXO1` conjunct with it. It is refused, and `DRUNR-003` is
why, in terms: "a global maternal WNT inhibition would
conflate epithelial exposure with stromal WNT4 decidual biology… **Do not connect
XAV939 directly to `S_WNT4_CTNNB1` by default**", blocking on "compartment-specific
exposure and biological response evidence" that does not exist. Li 2013 inhibits
WNT with **DKK1**, a secreted ligand antagonist applied to isolated stromal cells —
which is not evidence that a tankyrase inhibitor in a two-compartment chip reaches
the stroma.

**This is the third time in v0.5 that the largest available structural gain has
been refused on evidence** — after U3's `E_HBEGF = E_SECRETORY_STATE or IN_HCG`
and U4's `E_ANXA2_ACTIN = E_SECRETORY_STATE or X_IL11`. The pattern is worth
naming: the structural number is the visible one and it has now pointed the wrong
way three times running.

### 3.3 `S_FOXO1` — the evidence discriminates between two rules, and eliminates the one that gains

This is the unit's sharpest structure-versus-evidence conflict, and the reason
the constraint "do not choose rules because they maximize structural Δ" is not
hypothetical.

**The node is justified, and more strongly than the repository recorded.**
Vasquez 2015: FOXO1 siRNA **abolishes PR binding** at the shared IRF4 interval,
and FOXO1 or PR ablation blocks IRF4 induction. FOXO1 therefore *licenses*
progesterone-receptor genomic action — a step v0.4 represents nowhere, so this is
not a duplicate of `S_DECIDUALIZED` and not a marker. The candidate's own
measurable ("nuclear FOXO1") is vindicated by the paper's own fractionation:
**"most FOXO1 was found in the cytoplasm, with a residual nuclear fraction"** —
FOXO1 abundance is not FOXO1 activity.

**Two determinants are evidenced, and neither is invented.** WNT4/β-catenin
(Li 2013, siRNA) and PKA/cAMP (Vasquez 2015: "an early-induced target of the
protein kinase A pathway"). **But both are determinants of FOXO1 mRNA and total
protein, while the node is FOXO1 nuclear activity — so §5(2) *fails*** on the
activity-versus-abundance test, and that is this candidate's first failing
criterion. The determinants are real, which is why they are stated here: the
distinction between "a determinant exists" and "a determinant of the variable the
node names" is the whole point.

**Then the two candidate rules diverge, and the evidence picks the inert one:**

| rule | distinct fns | AC01 | decidual | evidence |
|---|---|---|---|---|
| `S_FOXO1 = S_WNT4_CTNNB1` (staged) | 35 | 9 | 6 | pass-through; part of TI007's 8-member E_IHH class |
| `= S_WNT4_CTNNB1 and S_PKA` | **35** | 9 | **7** | **supported** |
| `= S_WNT4_CTNNB1 or S_PKA` | **36** | 9 | 6 | **contradicted** |

The disjunctive rule is the one that gains, and Li 2013 refutes it directly:
**the WNT4 siRNA was applied with 8-bromo-cAMP present, and FOXO1 mRNA still
fell.** Under `or`, PKA being ON would hold FOXO1 ON regardless of WNT4. It did
not.

The conjunctive rule the evidence supports is inert, and the inertness is
*inherited* rather than intrinsic: `S_BMP2` is an exact alias of `S_PGR` in v0.4
(the five-member E_IHH class is `E_PGR, E_IHH, S_PGR, S_NR2F2, S_BMP2`), so
`S_WNT4_CTNNB1 and S_PKA` collapses to `S_PGR and S_PKA`, which is
`S_DECIDUALIZED`. Fixing the upstream degeneracy would change this node's
structural answer with no new FOXO1 evidence at all.

Two further honest limits: both papers read FOXO1 as mRNA and total protein
against a node defined as nuclear activity; and Li reports *suppression*, not
abolition, so even `and` asserts a completeness the measurement does not show.

**Disposition `WAIT_FOR_EXPERIMENT`, and the first failing criterion is (2), not
(4).** The two evidenced determinants are determinants of the **wrong variable**.
The node is FOXO1 *nuclear* transcriptional activity; Li and Vasquez both measure
FOXO1 **mRNA and total protein**; and Vasquez's own fractionation shows most
FOXO1 is cytoplasmic. The row's unblock condition asks for exactly the determinant
the node is missing.

**The two-rule divergence is a diagnostic, not the reason.** The conflict is real
and worth keeping: the rule the evidence supports is inert, and the rule that
gains is the one Li 2013 refutes. It is simply not what excludes the node — an
earlier criterion does.

**Unblock:** a determinant of FOXO1 **nuclear localisation**, not mRNA and not
total protein, in human endometrial stroma. This is `WAIT_FOR_EXPERIMENT` rather
than `RETAIN_CATALOG_ONLY` because **ADOC can run it**: nuclear/cytoplasmic FOXO1
fractionation across the existing stromal protocol arms. `S_AKT_EXCESS` is the
candidate the bundle assigns to that role, with no reference at all — one verified
localisation determinant would move two candidates.

> **Superseded 2026-09-22.** Labied 2006 (`REF-078`/`PDF-050`, ledger row
> `PIF-001`) supplies exactly the determinant this section says is missing —
> FOXO1 nuclear versus cytoplasmic localisation measured *as localisation*, by
> confocal immunofluorescence and by cytosolic/nuclear fractionation, in primary
> human endometrial stroma, driven by MPA and by 8-br-cAMP, both agents of
> `COND-FULL-COCKTAIL`. §5(2) therefore **clears**; the node now fails at §5(4),
> and the live disposition is `RETAIN_CATALOG_ONLY` with `unblock_locus` still
> `ADOC_RUNNABLE` for a new reason — what is missing is no longer a determinant
> but an ADOC-addressable **input** that separates `S_FOXO1` from
> `S_DECIDUALIZED`. §3.3 above is U4b's record as U4b closed it and is left
> standing; the live state is in the table at §0 and in
> `docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md`.
>
> Note also that Labied tested MPA **and** cAMP but neither E2 nor XAV939. The
> fractionation named above is still the ADOC-runnable measurement, but it has to
> be read on a **new single-agent dropout arm** — full cocktail minus E2, or minus
> XAV939, whichever agent stromal FOXO1 localisation turns out to respond to, so a
> null in one does not clear the other — and not on the arms that exist: `config/protocols.yaml` records that
> the design has no single-agent arm and that no effect may be attributed to MPA,
> cAMP or XAV939 individually, and the four agents are one design-equivalence
> class in `docs/design_alias/node_design_classes.tsv`.

---

## 4. The epithelial candidates

### 4.1 `E_SOX17` — full text supplied, and it makes the refusal firmer

§4.1's basis was "DRE012/DRE013 marked `confidence=verified` but DRREF-004 has no
full-text check". It has one now, and **both halves of that basis change**.

Kinnear 2019 is a real functional result: SOX17 is necessary for
trophectoderm-spheroid adhesion under two independent perturbations — CRISPR
knockdown (controls 51%/46% adhesion; KD1 3.0%, KD2 2.1%, p < 0.0001) and the
SOXF inhibitor MCC177 (50% control; 4.6% at 20 µM, **0%** at 50 µM). SOX17 rises
1.6-fold on E2+MPA over E2 alone, and stains more intensely beneath the adhesion
site than away from it.

**And every functional experiment is in ECC-1** — "an endometrial cancer cell
line", in the authors' own Methods. The trophoblast is an L2-TSC spheroid. The
only primary human tissue data is immunohistochemistry with no perturbation. This
is the same species-and-system failure U4 recorded against ANXA2/FLOT1, reached
independently.

Measured, the staged encoding is **worse than §4.1 recorded**:

| encoding | distinct fns | AC01 |
|---|---|---|
| committed | 35 | 9 |
| EDGE-012 + EDGE-013 as staged | **35** | **10** |
| node present but read by nothing | 35 | **10** |
| with an independent (invented) determinant | 36 | 9 |

§4.1 called it "a pass-through inside AC01, hence inert". It is inert **and it
enlarges the class U3 could not break.** The edge additionally fails §5's edge
criteria on activity-versus-abundance (1.6-fold protein over a non-zero baseline,
against a node defined as activity) and on graded semantics (the adhesion
response is dose-responsive: 58–65% knockdown gives 6.8–9.4%, >99% gives 2.1–3.0%).

**`RETAIN_CATALOG_ONLY`, failing at (2) rather than (4).** §5(2)'s
activity-versus-abundance test fires here too. The node is SOX17
**activity**, and the only determinant evidence is a 1.6-fold SOX17 **protein
abundance** rise. A determinant of namesake abundance is not a determinant of the
activity state, so §5(2) fails before the structural screen is reached — and the
AC01 measurement above is a diagnostic rather than the reason. The disposition
value is the same as §4.1's, and it stays `RETAIN_CATALOG_ONLY` rather than
`WAIT_FOR_EXPERIMENT` because half the unblock is **external to this platform**:
ADOC cannot supply a primary-cell replication of someone else's knockdown.
Node justified but system-limited; encoding rejected.

### 4.2 The glycosylation pair — one row in §4.1, two different failures

§4.1 adjudicated `E_GLYCOSYLATION_PROGRAM` and `E_SLEX_SURFACE` together. They
fail for different reasons, at different rungs, with different unblock
conditions, and the shared row concealed that.

**`E_GLYCOSYLATION_PROGRAM` was `RETAIN_CATALOG_ONLY` as U4b closed it, on a
definition that was not established rather than refuted.** *Superseded 2026-09-18:
the live verdict is `REJECT` / `SEMANTICS_REFUTED`, because the reference the
paragraph below names as unread — Ma 2023 — was read and contradicts the
definition. What follows is U4b's reasoning on the evidence it had.*

What the evidence shows is that the node's own wording — a "FUT3/ST3GAL3-like
glycosylation program" — is not supported **as a co-regulated transcriptional
programme**. Yu 2018, one of the two references the node names, calls ST3Gal3
**"the key enzyme"**, reports **no difference in ST3Gal4** between proliferative
and secretory human endometrium, and **measures no FUT3 at all**. The frozen ADOC
audit agrees independently: `E_MUC1_SLEX` is `divergent` precisely because its ten
glycosyltransferases do not move together (FUT6 +1.60/+2.99/+2.73 against ST3GAL4
−1.11/−0.25/−1.45, `node_support_finding.md:112`).

**But that is not a refutation.** "These selected
transcripts do not co-move" and "no coherent functional glycosylation state
exists" are different propositions, and only the first is evidenced — a glycan
*output* state does not entail transcript co-regulation, which is precisely what
Yu's own neuraminidase and anti-sLeX results demonstrate. Decisively, **the
reference bearing on the FUT3 half of the definition is unread**: Ma 2023 is
reported to carry an IL1B → FUT3 → sLeX route and is access-blocked. A refutation
cannot rest on silence about a component whose evidence was never obtained.

So the defect is located in the **definition**, not in the biology, and the
disposition is `RETAIN_CATALOG_ONLY` with the component named. The **replacement**
of `E_MUC1_SLEX` is rejected independently, on measurement.

**`E_SLEX_SURFACE` is `RETAIN_CATALOG_ONLY`**, and still is — though *its first
failing criterion moved from §5(2) to §5(4) on 2026-09-18*, when Ma 2023 supplied
the determinant this section records as missing. Yu 2018 does establish the node's
core claim, by three orthogonal and additive perturbations — ST3Gal3 siRNA,
neuraminidase stripping of α2,3-sialic acid, and anti-sLeX antibody blockade,
each p < 0.001. And the adhesive species is the **glycan epitope**, not a named
scaffold, which sustains the biological criticism of `E_MUC1_SLEX` that DTR012
made.

Three limits keep it there. Every human functional experiment is RL95-2 with JAR,
both carcinoma lines, and the in vivo arm is mouse. **ST3Gal3 knockdown also
reduced proliferation** (CCK-8, EdU, PCNA/Cyclin D1/Cyclin E1 down, P21 up), so
the adhesion loss is entangled with viability — exactly the confound DRUNR-010
exists to stop being scored as mechanism. And **no determinant is supplied**: the
secretory-versus-proliferative difference is observational tissue expression, and
the reference that would give an upstream input (Ma 2023, the IL1B → FUT3 route)
is the access-blocked one.

The **replacement** of the committed `E_MUC1_SLEX` is refused independently, on
measurement: TI013 expected "no alias broken"; measured, the staged pair takes
35 → 35 and grows AC01 **from 9 to 11**.

*Recorded but not acted on:* Yu 2018 strengthens the standing caveat that
`E_MUC1_SLEX` uses total MUC1 for an adhesive glycoform. Acting on it would be a
mechanism change, which U4b does not make.

### 4.3 `E_ITGA2B1` and `X_IL11` — reused, not re-adjudicated

Both rest on Marwood 2009, which was read in full on 2026-09-16 (DTR002, PDF-043)
and re-checked in U4. **U4b did not re-read it** and changes neither verdict.
`X_IL11` stays `RULE_VARIANT_ONLY` as a free input (GP130-b re-measured at
35 → 37, reproducing U4 exactly); `E_ITGA2B1` stays `RETAIN_CATALOG_ONLY` with
DRE009 sustained and the 2026-09-14 clarification — that redefinition as an
abundance state is not a promotion route — intact.

One new corroborating null: Griffiths 2019 measured **ITGB1** in primary human
epithelial cells and found no change. It does not contradict anything; it adds a
second independent place where the β1 subunit did not move.

### 4.4 `X_ECM_FN1_COL4` — §4.1's one open action, and the Δ is a trap

§4.1 said: "`RETAIN_CATALOG_ONLY` pending a measured Δ. No TI row computes one.
Run the Δ computation before adjudicating." Run:

| encoding | distinct fns | decidual class |
|---|---|---|
| committed | 35 | 6 |
| EDGE-016 + EDGE-017 package (with `E_ITGA2B1`) | **36** | **7** |
| the ECM node alone | **35** | **7** |
| with an invented free determinant | 37 | 6 |

The package's +1 looks like a promotion case and is not. **It is bought entirely
by `E_ITGA2B1`** — whose edge this repository has rejected twice — while the ECM
node itself is inert and *enlarges the decidual class Gate 3a exists to break*,
which is the TI003 failure mode that got `X_IL11`'s staged form rejected.

But the node does not reach the structural rung. Two findings from the full text:

1. **The staged compartment is contradicted.** Griffiths localises COL4A1 to the
   luminal and glandular **epithelial basement membrane**, and reports that
   semi-quantitation in the **stromal** compartment showed *no differences*
   between fertile and infertile endometrium. EDGE-016's determinant is
   `S_DECIDUALIZED` — the stroma, i.e. the compartment measured as unchanged.
2. **FN1 has no support from either reference.** Griffiths never measures
   fibronectin. In Marwood, fibronectin is the *substrate* of an adhesion assay,
   not a maternal ECM state. The node conjoins two ligands and has evidence for
   one.

**`RETAIN_CATALOG_ONLY`, failing at (0-insufficient), and it does not meet
§5(0b).** The apparent duplication of `S_TAZ_ECM` — the staged rule
`X_ECM_FN1_COL4 = S_DECIDUALIZED` *is* `S_TAZ_ECM`'s committed rule, and the
scRNA pre-registration lists `WWTR1, CTGF, CYR61, FN1, COL4A1` as `S_TAZ_ECM`'s
features — **fails on both legs.**

- The rule equality is a property of a rule the same document rejects. If the
  staged rule is wrong, what its Boolean function coincides with says nothing
  about the node.
- **The model's own dictionary separates them.** `S_TAZ_ECM` is "Stromal TAZ or
  WWTR1 ECM-remodeling state", `compartment = stroma`, `model_role =
  mechanical_regulator`, `measurement_proxies = "TAZ activity and collagen
  program"` — it **does not name `FN1` or `COL4A1` at all**. The overlap was with
  the scRNA pre-registration's feature list, a different artifact serving a
  different purpose. The candidate is `compartment = extracellular`,
  `role = matrix_state`, and its own note says it "complements stiffness/
  mechanics" — it is proposed as precisely what `S_TAZ_ECM` is **not**.
- **And the Griffiths finding argues the opposite way.** COL4A1 at the epithelial
  basement membrane with no stromal difference *separates* the candidate from a
  stromal mechanotransduction state; one result cannot both invalidate the staged
  source rule and establish identity.

So the real defect is the definition: a fibronectin/collagen-IV composite with
evidence for one half. **Recorded and not acted on:** under the staged rule the
node *would* be an exact Boolean alias of `S_TAZ_ECM`, which any future encoding
must address. The COL4A1 biology is real, verified, and in the best system of any
paper read in this unit — primary human epithelial cells, causal knockdown,
functional endpoint. (Noting, without acting on it, that `S_TAZ_ECM` is itself
`abundance_proxy_only` and carries the open U6 owner decision on `CTGF`/`CCN2`
and `CYR61`/`CCN1`.)

---

## 5. The five that failed at the first step

`E_ESR1_ACTIVITY`, `E_JAG1_NOTCH3`, `S_AKT_EXCESS`, `S_ERK` and `S_TGFB_CONTEXT`
all failed §5(1) **as U4b closed them**, for three different reasons — *`E_JAG1_NOTCH3`
no longer does, since 2026-09-18; the remaining four still do* — and §4.1 gave four of them
`RETAIN_CATALOG_ONLY` — the label §5 reserves for candidates that *passed* (1)–(3).

| candidate | why (1) fails | prior | now |
|---|---|---|---|
| `E_ESR1_ACTIVITY` | cited reference does not support the claim | WAIT_FOR_EXPERIMENT | `EVIDENCE_UNVERIFIED` |
| `E_JAG1_NOTCH3` | sole reference subscription-only | RETAIN_CATALOG_ONLY | `EVIDENCE_UNVERIFIED` — *superseded 2026-09-18: `WAIT_FOR_EXPERIMENT`, §5(1) now satisfied* |
| `S_AKT_EXCESS` | **no reference named at all** | RETAIN_CATALOG_ONLY | `EVIDENCE_UNVERIFIED` |
| `S_ERK` | **no reference named at all** | RETAIN_CATALOG_ONLY | `EVIDENCE_UNVERIFIED` |
| `S_TGFB_CONTEXT` | **no reference named at all** | RETAIN_CATALOG_ONLY | `EVIDENCE_UNVERIFIED` + `outside_formalism` |

`S_AKT_EXCESS`, `S_ERK` and `S_TGFB_CONTEXT` have an **empty `refs` field** in
`candidate_nodes.tsv`, **no candidate edge** and **no `mechanisms.tsv` row of
their own**. They carry deep-search confidences of 5, 5 and 4, which §5 and this
unit's constraints both forbid promoting on. They are catalog stubs, and the
disposition should say so.

**For those three, no structural measurement was made, and that is deliberate.**
No encoding was ever proposed for them. Constructing one in order to measure it
would be inventing the proposal and then evaluating my own invention. The
`structural_result` column records `NOT MEASURED` with that reason, which is the
same discipline as U4's `NOT_STAGED`.

Three notes that make the unblock conditions concrete rather than generic:

- **`E_ESR1_ACTIVITY`'s reclassification loses nothing.** `WAIT_FOR_EXPERIMENT`
  implies the evidence step was cleared and the block is downstream; it was not
  cleared. The frozen `dropout_e2` arm is still named in the unblock condition —
  but it informs only the "does `IN_E2` have a determinant-relevant effect" half,
  not the prior question of whether ESR1 *pathway activity* is separable from
  exposure at all. §4.1's Δ claim for it (35 → 35) was **asserted**; it is now
  **measured** and confirmed.
- **`S_AKT_EXCESS` is the determinant `S_FOXO1` is missing.** *(Amended
  2026-09-22: `S_FOXO1` is no longer missing a determinant — Labied 2006 supplied
  one, and its route is PI3K/Akt, which **supports** rather than displaces this
  line. `S_AKT_EXCESS` itself stays `EVIDENCE_UNVERIFIED` and was deliberately
  not moved by that increment.)* *(Amended again 2026-09-23 by U5b: re-adjudicated
  on Kang 2022, it now clears §5(1) and fails at §5(2), because its determinants —
  CAPN7 and the endometriosis state — are not varied by ADOC. It reads
  `RETAIN_CATALOG_ONLY`, `EXTERNAL`; nothing is promoted, and AKT **necessity** for
  FOXO1 exclusion remains untested by either paper. See `U5B-001`.)* DRUNR-007 names it
  "candidate inhibitor of `S_FOXO1`", and Vasquez 2015 independently shows FOXO1
  activity is set by nuclear-versus-cytoplasmic localisation without identifying
  what sets it. That is a concrete, checkable target for a future search — stated
  as the shape of what would unblock, not as an established mechanism.
- **`S_TGFB_CONTEXT` has two blocks, not one.** (1) Nothing to verify. (2) Its own
  declared sign is `biphasic`, and DRUNR-006 says "a single universal sign would
  be biologically misleading" — which is §8's Q3 category, the same class as the
  EPAC/RAP1 potentiation TI011 refused. So verification alone would not make it
  promotable, and the `formalism_verdict` column records that separately so a
  future unit that obtains the evidence does not mistake it for a clear path.
  *The only verified TGF-β observation this repository holds* is from Domínguez
  2010 (DTR005, read in full in U4): TGF-β significantly **reduces** membrane
  CD98 in primary human EEC — epithelial, single-direction, and in the wrong
  compartment for this node.

---

## 6. What U4b did not do

It did not change any rule, node, edge, threshold, rate, istate, condition or
phenotype; did not add a free Boolean variable; did not touch v0.4 or the v0.5
model directory; did not promote any candidate node or edge; did not allocate a
`REF-*` id, write a `pdf_manifest.tsv` row or place a PDF in the gitignored
library; did not edit `candidate_nodes.tsv`, `candidate_edges.tsv` or any other
staged bundle file, which stay as the reviewed delta they are; did not relabel
TI011 or any other U1–U4 conclusion; did not overturn U4's GP130/ANXA2/CD98
positions; and did not start U5.

**It also did not treat "the deep research proposed it" as evidence of anything.**
Every disposition here rests on a read paper, a repository artifact, or a
measurement made with the repository's own enumerator — and where none of those
existed, the disposition says so rather than defaulting to a soft label.

**And U4b itself issued no `REJECT` and no `MERGE_WITH_EXISTING`** — one `REJECT`
was reached later, by the 2026-09-18 refresh, on evidence U4b could not obtain. Both
values are defined by §5 and neither was reached here: refuting a definition and establishing node
identity are the two most assertive conclusions this ladder can carry, and for
none of the fourteen does the evidence support either.

**And it did not take the three structural gains it found.** `S_WNT4_CTNNB1`
with `IN_XAV939` **together with the evidenced `S_FOXO1` conjunct** — 35 → 37 with
no new free variable, the XAV939 rule *alone* being **35 → 36** — `S_FOXO1`
disjunctive (35 → 36), and `X_ECM_FN1_COL4`'s package (35 → 36) are the three
largest numbers this unit produced. The first is forbidden by DRUNR-003, the second is
contradicted by the experiment that tested it, and the third is bought by a
rejected edge. The numbers are recorded, with tests, precisely because a later
round looking for a cheap win will find them.

---

## 7. What U4b closes on

**Nothing promoted, and no executable mechanism changed.** Both supersets still
measure 35 distinct Boolean functions, 19 free variables and a nine-member AC01.
`models/`, `config/` and `data/` are untouched, the staged bundle is unedited,
U1–U4 are not reopened, and U5 is not started.

Final dispositions **as U4b closed them**: 1 `RULE_VARIANT_ONLY`,
2 `WAIT_FOR_EXPERIMENT`, 6 `RETAIN_CATALOG_ONLY`, 5 `EVIDENCE_UNVERIFIED`,
**0 `MERGE_WITH_EXISTING`, 0 `REJECT`, 0 `PROMOTE`**. Six candidates carried a
justified node with a rejected encoding.

**As the live table now stands, after U5b (2026-09-23):**
1 `RULE_VARIANT_ONLY`, **2** `WAIT_FOR_EXPERIMENT`, **7** `RETAIN_CATALOG_ONLY`,
**3** `EVIDENCE_UNVERIFIED`, **1 `REJECT`**, 0 `MERGE_WITH_EXISTING`,
**0 `PROMOTE`** — and **seven** candidates carry a justified node with a rejected
encoding, `E_JAG1_NOTCH3` being the seventh. U5b moved one row: `S_AKT_EXCESS`
cleared §5(1) on Kang 2022 and fails at §5(2), `EXTERNAL`, so it reads
`RETAIN_CATALOG_ONLY` (`U5B-001`); its encoding is still `NONE_PROPOSED`, so the
split count does not move. The 2026-09-22 unit had left the table at 1 / 2 / 6 / 4. Both counts are derived from the table rather than
quoted: the seven split verdicts by
`test_v05_u4b_candidate_closure.test_node_and_encoding_verdicts_are_recorded_separately`,
and the disposition tally by
`test_curation_increment_08_blocked_sources.test_the_disposition_tally_is_derived_and_the_documents_match_it`,
which also asserts that this document and the plan quote the numbers it computes.
(The broad sweep caught the earlier version of this sentence claiming a tally guard
that did not yet exist; it was closed by writing the guard, not by softening the
sentence.)
**`PROMOTE` is still zero and both supersets are still byte-identical to v0.4.**

**The closure is machine-readable, and the prose above is secondary to it.**
`…candidate-node-dispositions.tsv` carries the fourteen rows with their node and
encoding verdicts; the §5(1) ledger `…primary-verification.tsv` carries a
`final_dispositions` field (`candidate=DISPOSITION;…`) for every candidate it
names; and `tests/unit/test_v05_u4b_candidate_closure.py` compares the two
candidate by candidate, enforces the §5(2) rule per row, and re-derives the
structural measurements it asserts with the repository's own enumerator rather
than quoting them.

---

## 8. Two follow-ups, explicitly outside U4b

**A test run dirties the working tree on a date rollover.** `pixi run test`
regenerates `docs/experiments/calibration_candidates.md`,
`docs/experiments/variant_discrimination.md` and
`docs/gate2_target_level_rederivation.md`, whose headers carry a **generation
date**. Any run on a new day therefore produces a date-only diff in three files,
which makes a real change easy to miss in `git status` — a hazard this repository
has already been bitten by. **The behaviour is not fixed and is not U4b's to
fix**; it deserves its own unit.

**Prose claims are guarded heuristically, and should not be.** One invariant here
is enforced by string matching: the `(U4b)` curation-event marker in the
provenance guard. An explicit structured `review_scope` / `curation_unit` field is
the cleaner form, and the same applies to deltas quoted in prose, which should be
derived from a machine-readable claim the way `final_dispositions` derives
verdicts. **Do not reopen U4b for this** — it is a follow-up.
