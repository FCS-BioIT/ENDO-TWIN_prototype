# Node-support audit: what the transcriptome does and does not support in v0.4

The result of the pre-registered audit in
`docs/scrna/node_support_preregistration.md`, which was committed at `491b337`
before any audited expression value was read. Every threshold, gene list and
decision rule applied here comes from that commit, which is byte-identical to
the file on disk and pinned by a test. Errors found in it afterwards are
corrected in `docs/scrna/node_support_deviations.md` and never in place — read
that document alongside this one. **This is the decision gate:
no change is made to `network.bnd`, the condition `.cfg` files, the interface
relays, the calibration policy or the Stage-3 frozen design, and Gate 3b stays
closed.**

Asset: `EXT-SCRNA-001` (`E-MTAB-15842/seurat_object.rds`, sha256
`504a674d…89a1a`), read with R 4.5.3 / SeuratObject 5.4.0. Layer: the deposited
`counts` layer, decontX-corrected and non-integer. 28,212 cells, all of them
assigned by the frozen partition.

---

## 0. Two things to check before reading any verdict

**The pipeline reproduces a committed number it did not write.** KLF12 detection
per epithelial unit, derived here by an independently written module, matches
`docs/scrna/klf12_state_evidence.tsv` **to zero error in all six units**
(0.100793, 0.036263, 0.154960, 0.103797, 0.263945, 0.366097), as do the six
epithelial cell counts. That is the strongest end-to-end check available without
a second dataset.

**Two committed features are not in the object.** `CTGF` and `CYR61` — two of
`S_TAZ_ECM`'s five features — are absent under those symbols (the object carries
78,724 features). Section 2 forbids substituting a synonym, so **no alias was
used**: `S_TAZ_ECM` votes on the three features that are present (`WWTR1`,
`FN1`, `COL4A1`), which is still above the two-gene floor, and the gap is
recorded in the artifact. Anyone re-running this should know that the modern
symbols `CCN2`/`CCN1` were *not* substituted, and that doing so is a change to
the frozen feature list, not a fix.

---

## 1. Node support

**All 12 primary compartment-units passed every gate**: n ≥ 300, exposure
≥ 1e7, C1 detection integrity and C2 compartment specificity. The six
`myofibroblast` grid cells that contain any cells at all failed `n_min` (96,
180, 2, 6, 81 cells across `SZ09_CNT`, `SZ10_CNT`, `SZ10_HT`, `SZ25_CNT`,
`SZ25_HT`), exactly as the pre-registration predicted, and contribute nothing.
The sixth, `SZ09_HT_myofibroblast`, contains **no cells** and writes no row, so
the artifact carries seventeen units for an eighteen-cell grid; the derivation
records that as `grid_cells_expected` / `units_written` / `empty_units` rather
than leaving a reader to notice the gap. `SZ25_HT_stroma` is the tightest primary unit at 307 cells — seven
above the `n_min` floor of 300 — and its intervals are correspondingly wide.

Across 27 nodes × 2 arms: **43 `robustly_detected`, 11 `sparse_or_low`, and
zero `not_detected_with_power`.**

The C1 correction made before extraction was not cosmetic. Had the original
`COL1A1 ≥ 50%` stromal control been kept:

| stromal unit | `COL1A1` d | original control | `VIM` d | C1 as registered |
|---|---:|---|---:|---|
| `SZ09_CNT` | 0.697 | pass | 0.999 | pass |
| `SZ09_HT` | 0.305 | **fail** | 0.868 | pass |
| `SZ10_CNT` | 0.685 | pass | 1.000 | pass |
| `SZ10_HT` | 0.247 | **fail** | 0.995 | pass |
| `SZ25_CNT` | 0.477 | **fail** | 0.942 | pass |
| `SZ25_HT` | 0.674 | pass | 0.971 | pass |

Three of six stromal units would have failed, and because
`not_detected_with_power` requires 3/3 donors the whole stromal arm would have
been lost. Worse, the failures are **condition-correlated** — both `HT` stromal
units in `SZ09` and `SZ10` fall to 0.25–0.31 — so the original control would
have removed one arm preferentially. `COL1A1` still does its other job well: it
separates the compartments in every unit (C2 passed 12/12).

---

## 2. Alias classes: supported, contradicted, partially constrained, uninformative

### 2.1 `AC04` — **rule challenged**: no material response where v0.4 predicts one

`E_LIF`, `E_GP130_STAT3` and `E_CD98_CD9` are one Boolean function in v0.4, and
Appendix A predicts all three switch `OFF -> ON` with the cocktail. **None moves
materially in any donor.** All three are `divergent`, and this is not a power
failure: 12 of the 15 gene × donor comparisons have *non-overlapping* bootstrap
intervals with a median |log2 fold| of 0.35. Read that precisely — the
differences are **resolvable but below the pre-registered two-fold
convention**, not zero. `E_LIF` rises in a separated way in two donors (+0.59,
+0.46). The claim is that nothing moves by the margin the design declared
material in advance, not that nothing moves at all.

| member | per-donor log2 fold (SZ09 / SZ10 / SZ25) |
|---|---|
| `E_LIF` (LIF) | −0.26 / +0.59 / +0.46, separated 3/3 |
| `E_GP130_STAT3` (SOCS3, BCL3) | −0.68,−0.08 / −0.35,−0.10 / −0.69,−0.52 |
| `E_CD98_CD9` (SLC3A2, CD9) | +0.36,−0.34 / +0.28,+0.05 / −0.11,−0.51 |

The members still agree **with each other**, so the alias is not falsified. What
fails is the rule that the cocktail switches this class on. Section 5.4 is
explicit that these are different findings, and this one is the second.

### 2.2 `AC01` — **alias challenged**

One member moves strongly and three do not, in the same cells, in the same
donors, on the same layer.

| member | verdict | evidence |
|---|---|---|
| `E_PAEP` | `concordant_with_alias` | **+3.31 / +2.34 / +2.30** log2, separated in 3/3 — a 5- to 10-fold rise |
| `E_HBEGF` | `divergent` | −0.48 / +0.72 / +0.16, separated in 2/3 |
| `E_ITGAVB3_5` | `divergent` | every subunit flat or mildly **down** in every donor (ITGAV −1.59/−0.37/−0.80) |
| `E_MUC1_SLEX` | `divergent` | members disagree internally: FUT6 +1.60/+2.99/+2.73 while ST3GAL4 −1.11/−0.25/−1.45 |
| `E_PC6`, `E_SECRETORY_STATE`, `E_SPP1_EXPR` | `inconsistent` | move in some donors only |

This is the precise pattern v0.4 cannot represent: `E_PAEP` and `E_HBEGF` are
*the same variable* in the model, and one rises up to tenfold with the cocktail
while the other does not move. 26 of 38 sub-two-fold comparisons in this class
have separated intervals, so the non-movers are measured, not missed.

`E_MUC1_SLEX` deserves its own line: its ten glycosyltransferases do not behave
as a program at all — three fucosyltransferases rise while two sialyltransferases
fall. Under §6 this is biosynthetic competence and **never** a measured surface
glycan, so it says nothing about sLeX.

### 2.3 `AC03` — **partially constrained; the `UNIDENTIFIED` verdict stands**

This is the class `config/coupling_adjudication.tsv` records as `UNIDENTIFIED`
for `E_PGR` and `S_PGR`, with `what_would_change_it` naming a
compartment-resolved PGR readout. The audit delivers that readout, and the
answer is *not yet*.

- **`E_PGR`** (GREB1, HOXA10, HOXA11 — `PGR` itself excluded by R2, on the
  committed ground that epithelial PGR transcript can move opposite to the
  state): `moves_up` in `SZ09` only, and emphatically — +1.46 / +2.64 / +4.85
  across the three genes, all separated. Flat in `SZ10`. In `SZ25` the program
  splits (GREB1 +2.18, HOXA10 −2.01). Verdict `inconsistent`.
- **`S_PGR`** (GREB1, HAND2): flat in all three donors. Verdict `divergent` —
  but 4 of 6 comparisons **overlap**, so this is a weak null, not a precise one.
- **`E_IHH`**: flat in 3/3, all three overlapping. Also weak.

The suggestive reading — epithelial progesterone response moves in at least one
donor while the stromal response never does, in a model that forces them to be
identical — is the shape of evidence a revision would need. It **does not meet the
pre-registered bar**: `inconsistent` is defined in §5.3 as "not evidence for or
against the alias", so there is no `concordant` member to pair with a
`divergent` one. Recording this as an alias challenge would be reading the rule
backwards from the result. `E_PGR` / `S_PGR` stay `UNIDENTIFIED`, now with
evidence attached and a sharper statement of what would settle it.

Separately, `E_IHH` is at the detection floor in the epithelium, in **both**
arms — CNT d = 0.0000 / 0.00024 / 0.00035 and HT d = 0.0000 / 0.00036 / 0.0021
across `SZ09` / `SZ10` / `SZ25`. It is exactly zero in `SZ09` in both arms. It is
the closest thing in this audit to an absence, and it is **not** one:
`not_detected_with_power` requires exactly zero in 3/3 donors, and the other two
donors each carry a handful of positive cells. It licenses
nothing. It is worth the owner's attention anyway, because
`coupling_adjudication.tsv` already records the epithelium-to-stroma IHH relay
as carrying no information in v0.4, and the transcript that relay is named for
is barely present.

### 2.4 `AC02` — **uninformative about the alias; the falsification target is untouched**

All five members are `inconsistent`, and the reason is donor disagreement, not
imprecision: the decidualization response **reverses sign between donors**.

| member | SZ09 | SZ10 | SZ25 |
|---|---|---|---|
| `S_PRL` (PRL) | −1.41 ↓ | +3.86 ↑ | +2.04 (overlapping) |
| `S_IGFBP1` (IGFBP1) | −3.87 ↓ | +4.49 ↑ | −0.17 (overlapping) |
| `S_DECIDUALIZED` | ↓ | ↑ | flat |

The repository's pre-recorded falsification target was a `S_PRL` / `S_IGFBP1`
**divergence**. There is none: the two move together, in the same direction, in
every donor. `OM-016`'s timing claim (IGFBP-1 precedes PRL) is neither supported
nor contradicted, because a single-timepoint contrast cannot address an ordering
claim — see §5 below. In `SZ25` both sit near the floor — PRL d = 0.00095 (CNT) and
0.0195 (HT), IGFBP1 d = 0.0095 and 0.0163 — and that donor's stromal units are
the smallest in the study (1,053 and 307 cells), so its intervals overlap and it
contributes little.

### 2.5 `AC05`

Measured for node support only, never alias-tested, as pre-registered.
`E_PODXL`, `E_DAG1_FULL` and `E_MUC1_BARRIER` are all `robustly_detected` in
both arms. Under §6 none of this establishes an apical coat, an intact
dystroglycan or a barrier: `E_DAG1_FULL` in particular cannot be separated from
`E_DAG1_CLEAVED` by any transcript, which is a recorded assay limit.

### 2.6 A gap in the frozen vocabulary, found after extraction

§5.4 defines four class verdicts, and its `uninformative` has a **stated
condition**: "fewer than two direction-callable members". `AC02` (five
`inconsistent` members) and `AC03` (two `divergent`, three `inconsistent`) meet
none of the four conditions while having five callable members each. Reporting
them as `uninformative` would assert something false about the evidence, so they
are recorded as `unclassified_by_section_5_4`, carrying the member census.

**That value licenses nothing.** It was introduced after extraction and is
therefore disqualified from supporting any structural claim; it exists so the
artifact does not lie about which branch of the frozen rule was taken.

**Owner decision (recorded, not applied here):** this audit keeps
`unclassified_by_section_5_4` exactly as recorded. Before the *next* unit the
taxonomy is made exhaustive with a generic catch-all, `mixed_or_inconclusive` —
≥ 2 callable members and none of the other patterns, licensing no structural
change. Defining it generically and in advance is what keeps it from being a
category built around `AC02` and `AC03`'s observed results.

---

## 3. Absence findings, and whether raw confirmation is needed

**There are none.** No node in either arm reached `not_detected_with_power`, so
no `provisional_corrected_layer_only` tag was written and **no conclusion in
this audit rests on an absence**.

This is the cleanest possible outcome for §3.1's problem, and the reason is
simply that **nothing was undetected**. The decontX-corrected layer's inability
to certify a zero — the reason an absence here would have been provisional, and
the reason the raw per-sample matrices would have had to be re-fetched — never
comes into play, because no absence call exists to be marked.

**No raw-matrix confirmation is required for anything proposed below.** That is a
result, not an assumption: it was equally possible for this audit to have come
back with absence-dependent conclusions and a ~3 GB fetch attached.

### 3.1 `AC01` on raw UMIs — the condition-entanglement caveat, measured

Because `AC01` is the only finding licensing mechanistic reconsideration, and
because §3.2's caveat binds presence as well as absence, the finding was
re-derived on the **raw** layer:
`docs/scrna/node_support_raw_sensitivity.json`.

The same donors, the same broad epithelial compartment, raw
`filtered_feature_bc_matrix` UMIs from the same accession joined to the
deposited object by barcode, and **the same frozen movement rule** — applied by
the audit's own `unit_statistics` and `gene_movement`, not reimplemented. No new
genes, no re-clustering, no re-annotation, no new threshold. Only `PAEP` and
`HBEGF` were read: they are the two members the conclusion rests on and both are
`direct_transcript` rows. The join is complete — **all 20,441 epithelial cells
matched, zero unmatched in every sample**.

| gene | donor | corrected log2 | **raw log2** | raw intervals |
|---|---|---:|---:|---|
| `PAEP` | SZ09 | +3.31 | **+3.13** | separated |
| `PAEP` | SZ10 | +2.34 | **+2.23** | separated |
| `PAEP` | SZ25 | +2.30 | **+2.13** | separated |
| `HBEGF` | SZ09 | −0.48 | **−0.34** | separated |
| `HBEGF` | SZ10 | +0.72 | **+0.65** | separated |
| `HBEGF` | SZ25 | +0.16 | **+0.19** | overlapping |

**The divergence reproduces on raw counts**: `PAEP` `moves_up` in 3/3,
`HBEGF` `no_material_move` in 3/3, under the identical rule. Every fold agrees
with its corrected counterpart to within about 0.2 log2, in both directions, so
decontX is neither manufacturing `PAEP`'s rise nor suppressing `HBEGF`'s. **This
closes the condition-entanglement question for `AC01` specifically.** It does
not close it for anything else: §3.2 still binds every other magnitude in this
audit, including `AC04`'s, and only these two genes were re-derived.

One observation the rule does not act on, recorded because a reader should see
it: `HBEGF`'s *detection fraction* in `SZ25` rises from 0.169 to 0.392 while its
pseudobulk share barely moves. `SZ25_HT` is the depth outlier, and `d` rises
with depth where `f` does not; the pre-registered criterion is on `f`, which is
why it is ratio-form in the first place.

**What that does not buy, and an earlier draft claimed it did.** §3.1(4) exempts
from the layer caveat a conclusion resting on presence *or on divergence between
two members measured on the same layer*. `AC01` qualifies on both counts:
`E_PAEP` rises, and it does so while `E_HBEGF` does not, which is a comparison
between two members. **`AC04` qualifies on neither.** `rule_challenged` means
its members *agree with each other* — there is no between-member divergence to
appeal to — and its finding is a **null on CNT-versus-HT magnitudes**. An
earlier draft listed `AC04` under §3.1(4) anyway, which was a pun on the verdict
name `divergent`.

So the §3.2 caveat binds `AC04` with full force: decontX is cluster-dependent,
the clusters are near-deterministic in condition, and a flat CNT-versus-HT
result on this layer is exactly the shape of result that a condition-entangled
correction could produce. That is a reason to hold `AC04` loosely, and P2
proposes no split for it.

§3.2 applies to `AC01`'s magnitudes just as much — so it was **measured rather
than argued away**. An earlier draft said `AC01` survives the caveat because "a
correction that depresses HT uniformly cannot make one member rise ten-fold
while its class-mates stay flat". That reassurance assumed a uniformity decontX
does not have: contamination estimates and corrected values differ by gene, by
cell and by cluster, so the argument was never established. §3.1 below reports
what the raw layer actually says.

---

## 4. What reaches a phenotype, and what cannot

Seven of the audited nodes are recorded `phenotype_inert` in v0.4: clamping any
of them changes no `OUT_` node across all 524,288 enumerated states. The
findings split as follows.

| finding | members carrying it | reaches an `OUT_` node? |
|---|---|---|
| `AC04` rule challenged | `E_LIF`, `E_GP130_STAT3` **(both phenotype-relevant)**, `E_CD98_CD9` (inert) | **yes** |
| `AC01` alias challenged | `E_PAEP` **(relevant)** vs `E_ITGAVB3_5` **(relevant)**, `E_HBEGF` (inert), `E_MUC1_SLEX` (inert) | **yes** |
| `E_IHH` at the detection floor | `E_IHH` (inert) | no |
| `AC02`, `AC03` | — no §5.4 verdict — | n/a |

Both headline findings have phenotype-relevant members on **both sides**, so
neither is an inert-only observation.

**But a sharper distinction has to be kept, and an earlier draft blurred it.**
`AC01`'s load-bearing evidence is `E_PAEP` against `E_HBEGF` — both
`direct_transcript` rows, both re-derived on raw UMIs (§3.1). `E_ITGAVB3_5` is
*also* `divergent`, and it *is* the integrin state feeding the adhesion
interface — but the committed map records it as
`proxy_abundance_not_activity`: subunit transcripts "support receptor ABUNDANCE
at best, and the node is a ligand-engaged receptor state". Under §6 that cannot
establish the functional integrin state in either direction, so it is **not**
load-bearing and was deliberately excluded from the raw sensitivity.

What follows is the boundary this audit stops at:

> **`AC01`'s Boolean identity is biologically indefensible — a representational
> failure, established on two direct transcripts. Whether repairing it changes
> any adhesion prediction is a separate question, and this audit does not
> answer it.**

**This document makes no claim about paths through v0.4's graph** — two earlier
drafts did, and both were false about `network.bnd` (erratum E5 in
`docs/scrna/node_support_deviations.md`). Nothing here needs such a claim, so
only two kinds of statement are made below: **literal committed rules**, quoted,
and the **separately computed** inertness result.

The literal rules, verbatim from
`models/superset/adoc-literature-superset-v0.4.0/network.bnd`:

| line | rule as committed |
|---:|---|
| 126 | `E_ITGAVB3_5 = E_LIF or E_HBEGF or E_SECRETORY_STATE` |
| 214 | `X_ADHESION_ROUTE_SPP1 = E_RECEPTIVE_SURFACE and X_SPP1_LUMEN_FREE and E_ITGAVB3_5 and X_INTERFACE_SPP1_RELAY` |
| 218 | `X_ADHESION_ROUTE_REDUNDANT = E_RECEPTIVE_SURFACE and (E_CD98_CD9 or E_CDH1_APICAL or E_ANXA2_ACTIN or E_HBEGF or E_DAG1_CLEAVED or E_MUC1_SLEX) and X_INTERFACE_REDUNDANT_RELAY` |
| 226 | `OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE and E_PAEP` |

The computed result, from the committed map's `phenotype_inert` column — which
is not read off the rules above but obtained by clamping each node and
enumerating all 524,288 input/free states: **`E_PAEP` `false`, `E_HBEGF`
`true`, `E_ITGAVB3_5` `false`.**

That is the whole of what this audit says about reach, and it is enough for the
boundary: the identity is contradicted by two direct transcripts, and **what any
`OUT_` node does next depends on the rule that replaces it**, which this audit
deliberately does not propose (P1). `E_ITGAVB3_5` is the member that would speak
to the engaged integrin state, and it is the one whose measurement cannot. Both
questions belong to the mechanistic-integration work.

---

## 5. Does the evidence justify a structural v0.5?

**Yes, and narrowly.** §9's Q1 is decided on §5.4 class verdicts alone, and two
classes returned one:

- `AC01` is `alias_challenged` on presence and divergence, not on a provisional
  absence, and it **reproduces on raw UMIs** (§3.1), so it does not rest on the
  corrected layer's condition entanglement either. §9 states that this is
  sufficient to propose splitting the alias —
  and the **owner has declined that proposal** in favour of deriving replacement
  rules mechanistically (P1). What the verdict establishes is that the identity
  is false; what replaces it is not settled here.
- `AC04` is `rule_challenged`, which §5.4 states does **not** falsify the alias.
  Its members agree with each other; what the data do not support is the rule
  that the cocktail switches them on. The repair is to a rule, not to a
  collapse. It is a **weak** rule challenge — a null on CNT-versus-HT
  magnitudes on a condition-entangled layer (§3) — and it is not a v0.5 driver
  on its own.

`AC02`, `AC03` and `AC05` support no structural proposal. §9's parsimony clause
is binding: *a proposal is admissible only if a named §5.4 verdict requires it.*
Neither the suggestive `E_PGR` / `S_PGR` asymmetry nor `E_IHH`'s near-absence
qualifies, however tempting each is.

Note what is **not** being proposed. RNA supplied 56 genes and a great deal of
structure this model does not represent; none of it enlarges the network here.
The goal is the smallest mechanistically defensible correction to false
collapses, and the evidence names two.

---

## 6. Proposed minimal changes — **not implemented**

Each is a proposal carrying what supports it and what is still missing.

**P1 — `AC01`'s identity requires mechanistic reconsideration.** v0.4 makes nine
nodes one function through `E_SECRETORY_STATE = IN_E2 and E_PGR`. `E_PAEP` rises
5–10 fold with the cocktail in 3/3 donors; `E_HBEGF` — a **direct transcript**,
not a proxy — does not materially move. That pair alone is sufficient: the
identity `E_PAEP = E_HBEGF = E_SECRETORY_STATE` is not a defensible biological
identity, and the weaker integrin and glycosylation proxies are not needed to
carry the conclusion.

*What this does **not** license.* An earlier draft of this section proposed
giving the divergent members "distinct variables with their determination
recorded as open". **The owner rejected that, and rightly:** free Boolean
variables replace a false equality with unconstrained biology, which is not a
smaller error. §5.4 is explicit that a divergence tells us the alias is
inadequate and does **not** tell us what stands in its place, and `AGENTS.md`
forbids inventing rules where evidence is unavailable.

*What the next step is.* Defensible replacement rules are to be **derived** — from
literature together with this audit — in the mechanistic-integration work, not
asserted here. This audit's contribution is a concrete, data-demonstrated
problem for that work to solve.

**P2 — record that the `AC04` activation rule is unsupported at the sampled
state.** The cocktail does not produce the pre-registered >= 2-fold material
response v0.4 predicts, in any donor, for `E_LIF`, `SOCS3`/`BCL3` or
`SLC3A2`/`CD9`. It is *not* true that nothing moves: `E_LIF` rises in a
separated way in two donors (+0.59, +0.46 log2), below the two-fold bar the
design declared material in advance. The three members remain mutually compatible; what is unsupported
is the predicted cocktail-driven `OFF -> ON` transition at the sampled state.
**This says "the current activation rule is challenged", not "split these
nodes",** and it licenses no split.
*What is missing:* whether the failure is in the rule's inputs, its logic, or in
the assumption that transcript tracks the state at all — `E_GP130_STAT3`'s own
claim ceiling says STAT3 activity is post-translational, and a flat target
program is weaker evidence against a signalling state than it looks.

**P3 — nothing for `AC02`, `AC03`, `AC05`.** Recorded deliberately.

Two constraints on any v0.5 built from these, both from §6 and §9:

- No `retain` verdict here may be upgraded to "node confirmed". Strong presence
  establishes biological availability, never that the Boolean state is ON.
- A v0.5 that revises `AC01` may claim its members are **distinct states**. It
  may claim nothing about the **order** in which they change.

---

## 7. What stays unidentified for want of rates or kinetics

§9's Q2, kept apart from Q1. `network.bnd` has **zero** rate declarations, so
v0.4 has no time semantics at all, and this audit adds none: a single-timepoint
contrast constrains no ordering.

1. **`S_PRL` / `S_IGFBP1` ordering (`OM-016`).** The repository's own ELISA says
   IGFBP-1 precedes PRL. The two transcripts move *together* here, in the same
   direction, in every donor. A one-timepoint design cannot see an ordering, so
   this falsifier is untouched and needs time-resolved data — not more cells.
2. **Any rate claim about an `AC01` revision.** The evidence can say the members
   are distinct. It cannot say which changes first, or how fast.
3. **`AC04`'s flat result over time.** A null at one timepoint does not exclude
   a transient that preceded sampling. The registered §7 lists
   `inconclusive_sampling_time` as an available value on its
   convincing-absence axis, for nodes whose relevant mechanism is transient and
   precedes sampling — but **nothing in the committed map identifies which nodes
   those are**, so the classifier never assigns it and **no row of
   `docs/scrna/node_rna_interpretability.tsv` carries it**. The table's values
   are `cannot_inform_functional_state` (12), `challenges_contemporaneous_expression`
   (9) and `challenges_constitutive_or_active_use` (6); `AC04`'s own nodes are
   recorded `challenges_contemporaneous_expression` (`E_LIF`) and
   `cannot_inform_functional_state` (`E_GP130_STAT3`). An earlier draft said §6
   records the timing limitation in the artifact. It does not, and no code path
   emits it. The limitation is real and is recorded **here**, in prose, which is
   the honest place for it until the map carries the distinction.
4. **The CNT arm's exact composition.** Still unrecorded in the repository —
   unstimulated or E2-primed-only. It changes the expectation for exactly one
   node, `E_ESTROGENIC_PROLIFERATION`, which is why no verdict here depends on
   it, and no verdict was made for that node. It remains an evidence gap for the
   owner.
5. **Every post-translational, spatial or complex-level node.** `E_PODXL`
   (apical), `E_DAG1_FULL` (cleavage), `E_MUC1_BARRIER` (apical presentation),
   `E_GP130_STAT3` (phosphorylation), `S_TAZ_ECM` (nuclear localisation): RNA
   cannot inform their functional state in either direction, whatever the
   measurement shows.

---

## 8. Would the frozen `dropout_e2` Stage-3 choice change under a v0.5 reranking?

**A rerank is mandatory; whether the choice changes is not something this audit
can tell you.** The Stage-3 prospective design is frozen and untouched here, as
pre-registered.

The argument for "plausibly": Stage-3 ranked candidate experiments by their
power to discriminate competing mechanism classes *given v0.4's structure*. The
minus-E2 dropout arm derives its value from `E_SECRETORY_STATE = IN_E2 and
E_PGR` — removing E2 is informative precisely because one variable carries the
whole epithelial secretory program. **`AC01` shows that variable's class is not
one thing.** If `E_PAEP` and `E_HBEGF` are distinct states, a minus-E2 arm no
longer moves one thing; it moves some members and not others, and its
discriminating power has to be recomputed rather than assumed to carry over.

`AC04` pushes the same way from a different direction: an arm scored on its
ability to switch `E_LIF -> E_GP130_STAT3 -> E_CD98_CD9` is scored on a rule the
data do not support at the sampled state. It is the weaker of the two findings
and should not drive a v0.5 on its own.

So the rerank is **mandatory**: an arm whose discriminating power was computed
against an assumption this audit attacks cannot keep its ranking by default.
But *mandatory rerank* is not *predicted change*. Whether `dropout_e2` remains
best is an **output of the new model**, not a conclusion of this audit, and
nothing here should be read as forecasting it.

What this does **not** license: changing the frozen choice, or re-running the
ranking now. The correct sequence is that a v0.5 is built and adopted first, and
Stage-3's ranking is recomputed against it as a distinct, recorded step.
Recomputing a prospective design's ranking against a structure that has not been
adopted would be the worst of both.

---

## 9. Limits of this audit, stated plainly

- These are the study's own cells. Evidence role stays `construction` or
  `same_dataset_internal`; **nothing here is validation**, and nothing produced
  here may later be cited as independent support for a rule it helped write.
- Three donors. No inferential statistic was computed across them, and none
  should be. Donor agreement is 3/3, 2/3 or 1/3 and never a p-value.
- The bootstrap intervals are **within-donor measurement precision only**. They
  are not biological-replicate intervals and were never pooled.
- One bundled contrast. `IN_E2`, `IN_PROGESTIN`, `IN_cAMP` and `IN_XAV939` move
  together and the design has no single-agent arm, so **no component-specific
  causal claim is admissible** from anything above. "The cocktail moves these
  together" is the only form of statement made.
- `consistent_with_alias` was never returned, and would not have confirmed an
  alias if it had been: agreeing on one bundled contrast is the weakest possible
  test of an identity.
- `E_KLF12_HIGH` carries a support label but is tagged `not_blind` — its values
  were committed before this design existed. It licenses nothing and the closed
  prior question stays closed.
- `S_TAZ_ECM` voted on three features rather than five, because `CTGF` and
  `CYR61` are not in the object under those symbols. No synonym was substituted,
  as the frozen design requires. **Owner decision:** this audit stays as run, and
  HGNC alias handling (`CTGF`/`CCN2`, `CYR61`/`CCN1`) is reconsidered explicitly
  before any `S_TAZ_ECM` evidence is used in v0.5.
- The "980 tests OK" run recorded in the commit message is a **local** run. No CI
  status check is attached to this commit, so it is a claim a reader has to
  re-run rather than one they can confirm from the forge.

## Reproducing this

```
PYTHONPATH=src python -B -m dt_adoc.scrna.node_support --from-per-cell <table>
```

re-derives every committed number with no R and no 2.9 GB object. The per-cell
table carries row-level sample metadata and is written **outside** the
repository; only per-unit aggregates are committed. The bootstrap is seeded from
the frozen seed and each unit's ordinal in a sorted list, so the re-derivation
reproduces the extraction run exactly.
