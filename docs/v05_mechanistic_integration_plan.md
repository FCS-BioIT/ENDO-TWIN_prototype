# v0.5 mechanistic integration — design plan

**Status: U1 complete · U2 complete as BLOCKED · U3 complete and negative ·
U4 complete, evaluation-only · U4b complete, candidate set closed · U5 complete,
result identity · U5b complete, one rule repaired in v0.5.1 · U6 complete, schema only · U6b complete, evaluation only · U8 complete, ranking unchanged · U7 not started, and not needed by U8.** *Kept current as units land; earlier revisions said "planning only.
Nothing here has been implemented", and then "U1 implemented; U2–U8 pending",
both of which outlived the state they described.*

**No unit before U5b changed a rule, node, edge, threshold, rate, condition or
phenotype.** U1 added a directory whose mechanism-bearing files are byte-identical
to v0.4's; U2, U3, U4, U4b and U5 added records, guards, computations and
corrections only.

**U5b is the first and, as scheduled, the only mechanism-changing unit in this
line, and it changed exactly one rule** (2026-09-23): `OUT_STROMAL_DECIDUALIZED =
S_DECIDUALIZED`, in the new version `adoc-literature-superset-v0.5.1`. It repaired
*existing* topology and admitted no candidate node. One candidate-node
disposition moved, by re-adjudication on evidence already registered and without
promotion: `S_AKT_EXCESS`, `EVIDENCE_UNVERIFIED` → `RETAIN_CATALOG_ONLY`
(`U5B-001`). Every other disposition stays as U4b closed it and the 2026-09-22
registration left it. **U6b is complete and was evaluation-only** — it emitted a rule family and its
measured consequences, changed no `network.bnd` and created no model version, because its
own evidence rule forbids a canonical clearance rule and no evidence selects one.
The executable MUC1 correction it evaluates is a **separate deferred
obligation**, `TI-06`, so that work stays visible as owed rather than folded into
a unit that cannot deliver it.

**A mechanism-changing unit emits a new model version rather than rewriting an
audited one:** U5b created `adoc-literature-superset-v0.5.1` and left v0.5.0
exactly as U5 audited it. An audited version is a fixed object; the delta is what
moves. That rule governs *how* an executable change is versioned whenever one
happens — including a later v0.5.2 if U6b's executable half is ever authorised —
and it does not by itself authorise one. Outstanding topology obligations —
scheduled and deferred alike — are registered in
`docs/deferred_topology_register.tsv`, together with any scoped closure record,
and guarded by `tests/unit/test_deferred_topology_register.py`.

- **§0–§16 are design.** They were written without modifying any file under
  `models/`, `config/` or `data/`, and that is still how they should be read.
- **U1 is implemented** at `d140b40`: the v0.5.0 scaffold, T-H, T-K and the
  pre-U7 cfg invariant. It changed **no** rule, node, edge, threshold, rate,
  condition or phenotype — v0.5.0 is a byte-for-byte copy of v0.4.0 and 38 of
  its 41 files are the same git blob. See §17 for the delivery record.
- **U2 is BLOCKED on measurement**, and that is its result rather than a gap.
  Both halves of it — de-aliasing `S_PRL`/`S_IGFBP1` and adding a day-3 arm —
  are refused by `docs/prl_igfbp1_temporal_axis.md` and `gate3a_closure_audit.md`,
  which postdate the `v05_plan_review.md` section U2 was derived from. What U2
  delivered is the record (`docs/v05_u2_gate3a_blocked.md`) and the guards that
  keep it blocked under v0.5 (`tests/unit/test_v05_gate3a_guards.py`). See §17.
- **U3 is COMPLETE AND NEGATIVE**, which is one of the two outputs §7.1 allows.
  No replacement rule for `AC01` is derivable on the evidence in hand; the alias
  stays in place and flagged, and no free Boolean variable was created. The
  closest candidate is **structurally effective** and is rejected on §5's
  **edge-promotion** criteria, failing seven of eight; §5(1) is unsatisfied for
  it as well — `docs/v05_u3_ac01_no_derivable_rule.md`, guards in
  `tests/unit/test_v05_u3_ac01.py`. **No mechanism changed.**
- **U4 is COMPLETE AND EVALUATION-ONLY**, which is what §4.1 and TI002 ask of
  it. Yap/Dimitriadis 2011 was read in full and does **not** collapse TI002's
  rule family: it runs no LIF comparator and no functional endpoint, so it cannot
  make ANXA2 or FLOT1 an IL-11-*specific* executor. The family is therefore
  single-membered **for want of a representable alternative, not because the
  evidence chose** — and the arm that would have written it,
  `E_ANXA2_ACTIN = E_SECRETORY_STATE or X_IL11`, is the largest structural gain
  on the axis (35 → 37 alone, 35 → 38 with GP130-b, AC01 9 → 8) and is refused on
  §5's edge criteria. `CD98-d` is staged as TI001's literal rule text and
  separates from `CD98-b` in exactly one setting: embryo-conditioned signal
  present, hCG absent — the control Domínguez 2010 did not run. The Gate 2
  invariant re-derived on a closed level vocabulary changes **no** verdict.
  `docs/v05_u4_gp130_axis.md`, guards in `tests/unit/test_v05_u4_gp130.py`.
  **No mechanism changed.**
- **U4b is COMPLETE and the Sept-11 candidate set is CLOSED.** All fourteen
  candidate nodes carry an explicit disposition with a **node verdict and an
  encoding verdict kept apart**; **none is promoted**. *As U4b closed it:* six of
  the nine `DRREF-*` references were verified at claim level, two were recorded as
  access blockers, and one candidate (`E_ESR1_ACTIVITY`) cites a paper that does not
  support it. The unit also found and repaired a real defect in **§5 itself**: it
  defined a disposition for one of its five failure modes, and **seven candidate
  nodes** — arising from **five §4.1 classification entries** — were sitting on
  labels that gap allowed, **five of the seven too lenient**. The largest
  structural gain in the unit, `S_WNT4_CTNNB1 = S_BMP_SMAD and not IN_XAV939`
  (**35 → 36** for that rule alone and **35 → 37** with the evidenced `S_FOXO1` conjunct,
  both with **no new free variable**, since `IN_XAV939` is declared and unread),
  is refused on DRUNR-003 — the third consecutive unit in which the biggest number
  on the table lost to the evidence. Final dispositions **as U4b closed them** are
  1 `RULE_VARIANT_ONLY`, 2 `WAIT_FOR_EXPERIMENT`, 6 `RETAIN_CATALOG_ONLY` and
  5 `EVIDENCE_UNVERIFIED`: that closure issued **no `REJECT` and no
  `MERGE_WITH_EXISTING`**, because on the evidence then available no Sept-11
  candidate's definition was refuted and none duplicated a committed state under
  §5(0b). **Live counts after U5b (2026-09-23), which moved `S_AKT_EXCESS` `EVIDENCE_UNVERIFIED` → `RETAIN_CATALOG_ONLY` on Kang 2022 (`U5B-001`): 1 `RULE_VARIANT_ONLY`, 2 `WAIT_FOR_EXPERIMENT`, 7 `RETAIN_CATALOG_ONLY`, 3 `EVIDENCE_UNVERIFIED`, 1 `REJECT` (`E_GLYCOSYLATION_PROGRAM`), 0 `MERGE_WITH_EXISTING`, 0 `PROMOTE`, and SEVEN split verdicts** (1 / 2 / 6 / 4 after the 2026-09-22 PRL/IGFBP1/FOXO1 evidence-registration unit) — see `docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md` (and `docs/curation_increment_08_blocked_sources.md` for the 2026-09-18 state). `docs/v05_u4b_candidate_node_closure.md`,
  guards in `tests/unit/test_v05_u4b_candidate_closure.py`. **No mechanism changed.**
- **U5 is COMPLETE, and its result is identity** (2026-09-23,
  `feat/v05-u5-structural-audit`). v0.5.0 is executable-byte-identical to v0.4.0
  (38 of 41 files identical; the 3 that differ are U1's scaffold metadata),
  **Δ = 0** against the 35-function baseline, no alias class broke or formed, and
  identifiability and both design-alias variants recompute identically on the
  v0.5 path with the matched-unit caveat carried as a field on every
  design-dependent number. Record: `docs/v05_u5_structural_audit.md`; artifacts:
  `docs/u5_structural_audit/`; guards: `tests/unit/test_v05_u5_structural_audit.py`.
- **U5b is COMPLETE, and it changed one rule** (2026-09-23,
  `feat/v05-u5b-readout-repair`). `adoc-literature-superset-v0.5.1` =
  v0.5.0 with `OUT_STROMAL_DECIDUALIZED = S_DECIDUALIZED`; v0.5.0 untouched. Every
  node's composed function is identical over all 2^19 assignments (35 / 19 /
  AC01 9 / decidual 6); what moves structurally is two retired edges and the two
  markers becoming phenotype-inert under clamping. The pre-registered paired
  transient moves `BEYOND_TOLERANCE` in all seven hormone-exposed phase cells
  (+0.085 to +0.467 occupancy), is exactly identical in the three controls, and is
  stable across trajectory counts; bands are empirical block-reproducibility
  screens, not confidence intervals. `S_AKT_EXCESS` → `RETAIN_CATALOG_ONLY` at
  §5(2), not promoted; `OM-001` cross-referenced to §9.1. Record:
  `docs/v05_u5b_readout_repair.md`; guards:
  `tests/unit/test_v05_u5b_readout_repair.py`.
- **U6 is COMPLETE, schema only** (2026-09-23,
  `feat/v05-u6-semantics-components`). `observability.py` now also emits the
  three semantic axes for all 59 nodes as a generated view
  (`docs/u6_semantics/node_semantics.tsv`) — the evidence-root observation map
  is untouched and still byte-identical to `91f79ed` — and
  `src/dt_adoc/scrna/components.py` adds the four-state enum (failed and
  undefined integrity controls kept apart as reasons), §6.3's combinator with
  dual provisional propagation and the clamp veto, and a generated component map
  (`docs/u6_semantics/component_map.tsv`). **No requirement structure is
  declared**: no cited source states one, and the committed node dictionary
  contradicts §6.1's `E_ITGAVB3_5` form, so every assessable node is
  `undeclared` except `E_CD98_CD9` (`requires_definition`). **Owner decision on
  HGNC:** explicit, forward-only `CTGF` → `CCN2` (HGNC:2500), `CYR61` → `CCN1`
  (HGNC:2654); the frozen audit is not reinterpreted, and `CCN2`/`CCN1` presence
  stays unverified until a registered extraction checks it. Record:
  `docs/v05_u6_semantics_components.md`; guards:
  `tests/unit/test_v05_u6_semantics.py`. **No mechanism changed.**
- **U6b is COMPLETE, evaluation only** (2026-09-24,
  `feat/v05-u6b-muc1-reconciliation`), and discharges `TI-02`. The
  `E_MUC1_BARRIER` rule family — the committed rule, a placement-only control,
  the naive sign flip in place and at the interface, and the abundance /
  clearance / barrier split with the clearance determinant contact-driven,
  contact-plus-competence (unlicensed) or unresolved, each crossed with the two
  abundance drivers `PIF-008` cannot tell apart — was measured as in-memory
  variants of v0.5.1 by the repository's own loaders. Placement alone is a
  Boolean identity; both naive flips are refused on measured grounds; with any
  contact-bearing determinant MUC1 is inert for the measured adhesion endpoint;
  on a measured node no arm in hand separates the abundance drivers, `A` from
  `B`, or either from the committed rule — only the unresolved member at
  clearance OFF moves the adhesion endpoint, by exactly a hand-set relay prior. **No canonical
  executable rule is licensed**, so `TI-06` stays `DEFERRED` on unchanged
  conditions. Record: `docs/v05_u6b_muc1_reconciliation.md`; artifacts:
  `docs/u6b_muc1_reconciliation/`; guards:
  `tests/unit/test_v05_u6b_muc1_reconciliation.py`. **No mechanism changed.**
- **U8 is COMPLETE, and `dropout_e2` remains first** (2026-09-24,
  `feat/v05-u8-stage3-rerank`). The unchanged Stage-3 computation was run against
  v0.5.1, with the model version as its only new parameter and readout tiers
  taken from `observation_model_map.tsv` alone. It is identical to v0.4 in every
  quantity the ranking reads. The cause is that U5b's rule change preserves the
  Boolean function whenever neither marker is forced on its own, and no Stage-3
  class or arm forces either one. The mandate is carried as conditional on D1
  (§0.7), not re-adjudicated. Record: `docs/v05_u8_stage3_rerank.md`; artifacts:
  `docs/experiments/u8_stage3_rerank/`; guards:
  `tests/unit/test_v05_u8_stage3_rerank.py`. **No mechanism changed.**
- **U7 is not started, and U8 did not need it.** Stage 3 is exact Boolean
  evaluation with in-memory rule substitutions and reads no mutation interface.
  U7 now waits only on personalization, and its §17 prerequisites are
  open. **U5b and U6b were added by the register revision and are
  not new work:** they schedule the topology increments that
  `docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md` §6 ordered and that
  no unit had picked up. Items 3 and 4 of that order stay deferred; §18 and
  `docs/deferred_topology_register.tsv` carry every outstanding obligation with
  its unblock conditions, so a later revision cannot drop one silently again.

**Base state.** `main` @ `58f0fba`. The **integration baseline** of this
branch is **`5a55cf1`**, which merges `feat/scrna-node-support` @ **`7ee303f`**;
that is the commit §0.8 reconciles against and the state every artifact claim
below is read from. The branch has since advanced — see §15 for the current
tip — so `5a55cf1` is a baseline, not "where the branch is". The **frozen
evidence root remains `91f79ed`** (`fix(scrna): restore the registered
pre-registration and move every deviation out`). That commit added
`docs/scrna/node_support_deviations.md` (239 lines at that commit, 266 after
`a028ef3`, 316 at `7ee303f`) and rewrote §6/P1 of `node_support_finding.md`
(420 / 453 / 547 lines at the same three states). **Revision 2 of this document
was re-derived against `91f79ed`**; revision 1 was written against `258f07f` and
quoted a draft of P1 that has since been withdrawn by owner decision.

**Three states, deliberately distinguished.** Read this document with all three
in mind; conflating any two of them is the failure mode this section exists to
prevent.

1. **Frozen evidence root — `91f79ed`.** Every number, verdict, support label
   and QC call cited below is read from that state and stays there. §0.1's
   headline, §3's taxonomy counts and §7's class verdicts are all claims about
   `91f79ed`, and all of them still hold at `5a55cf1` — see "What the evidence
   root still guarantees" below.
2. **Current implementation state — `7ee303f`, merged here at `5a55cf1`.** This
   is the code U1 onwards builds on. It is *not* `a028ef3`: `fbf5468` merged
   `a028ef3` specifically, and the audit branch ran on past it through five
   further commits — `252461b`, `9a5c52b`, `c551d9f`, `14b143f`, `7ee303f` —
   which `5a55cf1` now brings in. (`252461b` was already written when `fbf5468`
   ran; the merge took `a028ef3` deliberately, not the then-tip.) Wherever this
   document previously said "the code base is `a028ef3`" it now means `7ee303f`.
3. **Later errata, schema and provenance repairs — `a028ef3`..`7ee303f`.**
   Changes made *after* the evidence root for correctness, schema or provenance
   reasons that **moved no frozen biological result**. These are enumerated
   below and in §0.8, and they are the reason T-G cannot pin every artifact to
   `91f79ed` (§12, T-G).

**Why the code base moved off the evidence root at all.** `91f79ed` carries a
known defect in `src/dt_adoc/scrna/node_support.py` — `member_verdict` folded a
missing compartment-unit's `uninformative` into `no_material_move`, so an
unmeasured donor counted as evidence of *non*-movement and could carry a
`divergent` verdict alone. Precisely: the unmeasured donor blocks concordance by
itself under the 3/3 rule, and turns a case that should be `uninformative` into
`divergent` when the other two donors are `no_material_move`. `fbf5468` took
`a028ef3`'s fix for exactly this reason.

Its blast radius is wider than the paragraph that stood here claimed, and wider
in the direction that supports carrying the fix. That paragraph said no
production module imports `member_verdict` or `gene_movement`; **at `5a55cf1`
that is false.** `src/dt_adoc/scrna/node_support_raw_sensitivity.py` — added by
`252461b`, a production module — calls `N.unit_statistics` and `N.gene_movement`
directly (`:465`, `:471`), deliberately, so the raw-UMI re-derivation applies the
frozen rule rather than a reimplementation of it. `member_verdict` itself is
still called only inside `node_support.py` and its tests. What remains true is
that U5's Δ, identifiability and design-alias code (`src/dt_adoc/reporting/`) and
U6's `observability.py` do **not** call any of them, and that the defect bites
any **re-execution of the alias test on a grid with a missing compartment-unit**:
the audit reproduction route, the myofibroblast sensitivity, the raw sensitivity,
and bulk if bulk reuses this module.

Developing v0.5 on knowingly buggy code in order to preserve a provenance root
would conflate provenance with correctness.

**What the evidence root still guarantees at `5a55cf1`.** `fbf5468` verified five
artifacts across the merge and found all five byte-identical. That is no longer
the position: **three of those five** are still byte-identical to `91f79ed`, and
two are not. Adding `config/scrna_observation_map.tsv`, which was outside that
check and is also unmoved, gives **four artifacts that can legitimately stay
hash-pinned at the evidence root**:

| artifact | in the `fbf5468` check | `91f79ed` → `5a55cf1` |
|---|---|---|
| `docs/scrna/node_support_evidence.tsv` | yes | **byte-identical** |
| `docs/scrna/node_rna_interpretability.tsv` | yes | **byte-identical** |
| `docs/scrna/node_support_preregistration.md` | yes | **byte-identical** (still identical to `491b337`) |
| `config/scrna_observation_map.tsv` | no | **byte-identical** |
| `docs/scrna/node_support_findings.json` | yes | **changed** — additive schema + provenance only |
| `docs/scrna/node_support_qc.tsv` | yes | **changed** — new column + `not_applicable` semantics |

The two that changed did so **after** the evidence root, for schema and
provenance reasons, and **no biological result moved**. Verified field by field
at `5a55cf1` against `91f79ed`:

- `node_support` (all 27 nodes × 2 arms), `label_counts`, `unit_cell_counts`,
  `absent_features`, `empty_units`, `units_written`, `provenance` and
  `layer_caveat` in `node_support_findings.json` are **unchanged**.
- All four `class_verdict` values are **unchanged** (`AC01 alias_challenged`,
  `AC02`/`AC03` `unclassified_by_section_5_4`, `AC04 rule_challenged`), and every
  member verdict with them. The only change to `alias_classes` is an **added**
  `decision_provenance` block per class (§0.8).
- The only changes to `units` are the **added** `c1_evaluated` / `c2_evaluated`
  fields on all 17 units, and, on the five non-primary myofibroblast units only,
  `NaN`/`""`/`false` → `null` and `attribution` `compartment_attribution_unsafe`
  → `not_applicable`. All twelve primary units are untouched.
- `node_support_qc.tsv` gains a `c1_evaluated` column; every numeric value and
  every primary-unit row is unchanged, and the same five myofibroblast rows now
  report `not_applicable` for checks that were never run rather than `false`.

**Do not weaken T-G to cover this.** The correct pinning is stated in §12 (T-G):
pin the four unchanged artifacts at `91f79ed`, and pin the two changed ones —
with `node_support_raw_sensitivity.json`, which did not exist at the evidence
root — at `7ee303f`, each carrying the commit and the reason it moved. Re-pinning
everything to the current tip would make the test pass while destroying the
distinction the evidence root exists to carry, and reverting the two files would
reinstate a defect.

**One consequence for citations, stated so it is not discovered later.** The
*narrative* artifacts are not pinned: `node_support_deviations.md` and
`node_support_finding.md` changed in `a028ef3` and again in `252461b`,
`9a5c52b`, `c551d9f` and `14b143f`. This document's line citations into them
resolve at **`7ee303f`**, this branch's doc base after the merge at `5a55cf1`:

| citation | at `a028ef3` | at `7ee303f` (current) |
|---|---|---|
| `S_TAZ_ECM` HGNC owner decision | `deviations.md:241-246` | **`:270-275`** |
| AC01: no free variables; derive replacements | `:248-257` | **`:277-285`** |
| `dropout_e2` must be reranked | `:258-263` | **`:287-291`** |
| no raw-matrix fetch required | `:264-266` | **`:293-295`** |
| P1 | `finding.md:300-315` | **`:390-404`** |

Numbers at `91f79ed`; narrative at `7ee303f`.

**Reconciliation history.** This document was committed at `2d6fc30` against
`91f79ed`, reconciled with `a028ef3` at `10139e6`, revised at `82a8a64` and
`57f9355`, and reconciled with `7ee303f` at the merge `5a55cf1` — §0.7 records
what `a028ef3` changed for this plan and §0.8 what `252461b`..`7ee303f` changed.
The audit branch has moved repeatedly during the drafting of this document, so a
reader should check it again before acting on §7.

**Relation to existing plans.** `docs/v05_plan_review.md` (2026-09-15, revised
2026-09-16) is the superseding v0.5 plan. This is its *mechanistic-integration
annex*. It is also the work that `node_support_deviations.md:248-257` names as
the place where AC01's replacement rules must be **derived** — so this document
has a specific assigned job, not just an advisory one.

---

## 0. Seven findings that change the proposed design

### 0.1 The frozen audit contains zero powered absences

`node_support_finding.md` §1, §3: across 27 nodes × 2 arms, **43
`robustly_detected`, 11 `sparse_or_low`, zero `not_detected_with_power`**
(verified independently from `node_support_findings.json`). No
`provisional_corrected_layer_only` tag was written on any node; no conclusion
rests on an absence; **no raw-matrix fetch is required *for an absence*** —
`node_support_deviations.md:293-295` records this as a carried-forward limit.

**Re-verified at `5a55cf1`, and unchanged.** The `node_support` block of
`node_support_findings.json` is byte-identical to `91f79ed`, and recounting it at
the merged commit gives the same 43 / 11 / **0**. No node carries the
`provisional` flag, because the flag is emitted only on a
`not_detected_with_power` label and there are none. Nothing in `252461b`..`7ee303f`
touches this, and §0.2's consequence stands: `ABSENT_POWERED` still has no
instance in the only RNA dataset in hand.

**A raw-matrix re-derivation was nonetheless run, for a different reason, and it
does not create an absence.** `252461b` re-derived `PAEP` and `HBEGF` on raw
`filtered_feature_bc_matrix` UMIs (`docs/scrna/node_support_raw_sensitivity.json`)
to settle a *condition-entanglement* question about `AC01`'s magnitudes, not a
power question — see §0.8. `deviations.md:297-307` records it separately from the
carried-forward limit above, and the limit is unchanged: the decontX-zero
question still gates nothing, because there is still nothing it could gate.

The specification anticipates provisional powered-absence calls. There are none.
The closest case, `E_IHH`, sits at the detection floor in both arms (CNT
d = 0.0000 / 0.00024 / 0.00035) and is explicitly not an absence.

**Consequence:** `ABSENT_POWERED` — the only branch of the proposed RNA
architecture that can change a simulation — has no instance in the only RNA
dataset in hand.

### 0.2 There is no mechanism in this model by which an RNA gate could act

**(a)** 26 of the 27 RNA-observable nodes are derived; only `E_KLF12_HIGH` is
free (`logic = <self>`).

**(b)** The repository's only conditioning layer is `istate`
(`src/dt_adoc/simulation/runner.py:166` writes `{node}.istate = TRUE|FALSE;`);
the only other emitted overrides are `is_internal`, `max_time`, `time_tick`.
There is no mutation, clamp or rate-modifier machinery in `src/dt_adoc/`.

**(c)** An `istate` *is* syntactically expressible on a derived node —
`baseline.cfg` assigns one to all 59 — but it is an **initial condition, not a
constraint**: MaBoSS overwrites it from the logic within a few ticks. The
objection is dynamical, not syntactic.

**(d)** No `.cfg` clamp is expressible either. `network.bnd` has **zero**
`rate_up`/`rate_down` and **zero** `$` parameters, in v0.4 and every other model
(`grep -rn "rate_up\|rate_down" models/ config/` → no hits; the only tree-wide
hits are float multipliers computed in `personalization/soft_nv.py`, which writes
no cfg). A MaBoSS `.cfg` can set `$` parameters only if the `.bnd` declares them.
There is nothing to bind to.

**Consequence.** Any clamp-style gate needs a one-time, uniform,
donor-independent MaBoSS mutation interface in the `.bnd`. **Do not invent the
expression** — an earlier revision of this document proposed
`rate_up = @logic ? $NODE_high : 0.0`, which is *wrong*: it constrains only the
upward transition, so a node that starts ON with its logic TRUE has
`rate_down = 0` and stays ON for as long as that logic holds. Suppressing
`rate_up` alone is not a hard OFF. See §0.2(f) for the derived form.

That interface is not a per-donor topology change, so it does not violate
`personalization.yaml:26 topology_changes_forbidden_per_donor: true` — but it is
a prerequisite unit nobody has scoped, and it must be labelled a **mutation
interface, not a rate layer**, with an inertness test at defaults.

Note also, independently of RNA: `personalization.yaml:5-8` has listed `clamp`
and `rate_modifier` as allowed mapping layers since before anything could execute
them, and `strict_nv.decide_strict_variant` returns clamp decisions nothing
downstream can act on. That gap is worth recording on its own.

**(f) The derived clamp form, taken from the installed MaBoSS package rather
than invented.** `maboss/simulation.py:378-395` (`_make_mutant_node`) defines the
canonical mutable node. **Cite that function, not the `mutate()` docstring at
`:300`** — the docstring shows `$HighNode ? 1 : (@logic ? rt_up : 0)`, a rate of
1 rather than `1E308/$nb_mutable`. It is stale, and it is precisely the
"eventually OFF" form warned against below.

```
rate_up   = $Low_X  ? 0 : ($High_X ? 1E308/$nb_mutable : (<original rate_up>));
rate_down = $High_X ? 0 : ($Low_X  ? 1E308/$nb_mutable : (<original rate_down>));
```

Both halves are required. Working the three settings through:

| setting | `rate_up` | `rate_down` | behaviour |
|---|---|---|---|
| **WT** `$Low=0, $High=0` | original | original | reduces exactly to the unmutated node — this is what makes the inertness test well-founded |
| **OFF** `$Low=1, $High=0` | **0** | **1E308/$nb_mutable** | cannot turn on; if it starts ON it is driven OFF essentially instantaneously, **regardless of `istate` and regardless of the logic** |
| **ON** `$Low=0, $High=1` | 1E308/$nb_mutable | 0 | the dual |

Three details that must survive into U7 and are easy to lose:

- **The near-infinite rate is deliberate.** Using `rate_down = 1` would make the
  clamp *eventually* OFF rather than *immediately* OFF, which changes transient
  results — and U2's whole deliverable is a transient.
- **`$nb_mutable` is an overflow guard.** It keeps the *sum* of clamp rates at
  or below `1E308` so the total-rate normalisation does not overflow to infinity
  when several nodes are clamped at once. A single-node derivation that drops it
  breaks on the second clamp.
- **`<original rate_up>` / `<original rate_down>` must be preserved verbatim.**
  v0.4 declares no rates, so the originals are MaBoSS's implicit defaults for a
  logic-only node: `maboss/gsparser.py:306-307` sets them to `@logic ? 1.0 : 0.0`
  and `@logic ? 0.0 : 1.0`. U7 should still confirm this on the runtime it
  actually uses, because the inertness test is exactly the claim that the
  rewritten node reproduces them.

**And one thing the package will not do for us.**
`src/dt_adoc/simulation/runner.py:652` calls `maboss.load(..., cmaboss=True)`,
which returns a `CMaBoSSSimulation` handing the raw `.bnd`/`.cfg` to the C++
engine. That class has no `mutate()`, no `_make_mutant_node`, and **never emits
`$nb_mutable`**. The idiom is plain MaBoSS syntax and carries fine, but
`$nb_mutable`, `$Low_*` and `$High_*` must be **declared by this repository in
every generated cfg, WT included** — with them absent the engine refuses to load
(`BNException: symbol $nb_mutable is not defined`). So T-B does not merely pass
or fail: without the declarations it *errors*, which is a different and
easier-to-misread outcome.

**(e)** A caveat on an earlier claim in this document. Revision 1 called the
`ABSENT_POWERED` vs `below_detection` conflict in
`strict_nv.py:7 NON_EVIDENCE_STATES` a "direct collision". It may not be one:
those are per-donor *measurement-value* states, while `not_detected_with_power`
is a zero carrying an exposure bound, n ≥ 300, E ≥ 1e7 and C1 in 3/3 donors.
**Whether `strict_nv` is even on the RNA-gate code path is unverified.** Verify
the call path before recording any adjudication. The policy point — that adding
a state name to escape a forbidden set is "moving the rule rather than the code"
— stands regardless, but it is not yet owed to anything.

### 0.3 Interface repair is explicitly blocked; the maternal layer comes first

Revision 1 of this plan put relay repair first, on the strength of
`v05_plan_review.md` §3.2. **That section has been overtaken and the plan was
wrong.** `v05_plan_review.md:64-71` carries an explicit override: the per-relay
decomposition was run and found the relays carry the model's only representation
of between-unit variability, so decomposing them is "blocked on a prior semantics
question that is still undecided (`docs/adhesion_variability_semantics.md`)", and
`gate3a_closure_audit.md` "is the current position on gate order and supersedes
this line."

`gate3a_closure_audit.md:171`: **"Recommendation: do not close Gate 3a and do not
open Gate 3b."** On three recorded grounds: nothing in the maternal layer is
identified (22 artificially coupled, 6 unidentified nodes); the thing Gate 3b
most needs — whether `E_RECEPTIVE_SURFACE` is correctly specified — is what
Gate 3a could not deliver; and Gate 3b's own prerequisite is recorded unmet.
Line 21 adds that the three `X_INTERFACE_*` relays are **terminal penetrance
variables, strictly downstream of every maternal node**, so "no maternal
conclusion depends on them."

And `v05_plan_review.md:1113-1122` orders the repairs explicitly: **3a first**
("De-alias S_PRL from S_IGFBP1 and add the day-3 maternal protocol stage, so
OM-016 becomes evaluable"), 3b (interface) after.

The falsified 0.82 endpoint is real and stays recorded. It is not the first
thing to fix.

### 0.4 The measured-Δ criterion is a screen, not the primary criterion

`topology-implications.tsv` carries `measured_delta_boolean_functions` against
the v0.4 baseline of 35 (`P_label` 59 → `P_global` 35 → `P_design` 19). It is
computed and reproducible, and revision 1 proposed it as the primary admission
criterion "above any prose checklist". **That is wrong, and the repository
contains the counterexample.**

**TI005**: `S_NR2F2` given an epithelial-competence determinant — Δ **35 → 38**,
and it breaks `E_IHH(5)` into three classes. It passes a conjunctive
"Δ > 0 **and** an alias broken" test outright. And the determinant is an
**invented latent variable**, which the repository withdrew, recording: "Improving
the partition is evidence that a determinant is structurally useful, **NOT** that
this latent variable is the right one."

So the conjunction revision 1 added to block TI011's free variable does not block
TI005's,
because a free variable *inserted as a determinant* both raises Δ and breaks a
class. Both conjuncts are also computed from the same partition `P_global`, so
they are not independent evidence, and neither is evidential about biology at
all.

**Corrected role:** Δ is a necessary screen that ranks *structural usefulness*.
What excludes TI005 is the prose criteria — a real determinant, primary
verification, compartment support. Those come first; Δ breaks ties among
candidates that already pass them.

### 0.5 The Δ screen silently forbids every timing repair

**TI012** (not cited in revision 1): routing `S_PRL` through an intermediate —
the Gate 3a separation that `v05_plan_review.md` calls the **first concrete v0.5
deliverable** — measures Δ **35 → 35**, "no class broken; decidual class grows
from six to seven", with the recommendation: "The IGFBP-1-before-PRL claim lives
only in the **transient**; no fixed-point partition can test it, so Gate 3a
cannot be evaluated by the structural machinery and needs a transient readout."

So the repository's designated first deliverable scores zero on the screen. Any
admission rule built on Δ needs an **explicit exemption for repairs whose effect
is transient rather than partition-level**, or it forbids every timing repair and
a structural audit would report Gate 3a as having achieved nothing.

### 0.6 Full-text verification is thinner than it looks, and revision 1 named the wrong file

`primary-verification.tsv` has **7** rows, not 8. Of those, DTR002-followup
(Yap/Dimitriadis 2011) is "NOT YET READ"; DTR011 and DTR005 are abstract-verified
via web search with the PDF "not re-read in this pass". **Genuine full-text
reads: 4** (DTR002, DTR006, DTR017, DTR026).

And `context/literature/citation_verification.tsv` — which revision 1 named as
the record of full-text verification — is a **DOI-resolution / title-match**
table (`ref_id, doi, resolver, resolved, title_similarity, year_matches, …`,
every row `resolver=crossref`). A criterion written against it would be satisfied
by a DOI that resolves, which is exactly the failure mode DRE009 exists to
prevent. Full-text verification lives in `primary-verification.tsv`.

**Where that file actually is, resolved in U3 and recorded so no later unit has
to rediscover it.** This document's bare `primary-verification.tsv` is
**shorthand**; there is no file at `context/literature/primary-verification.tsv`,
and `git log --all --diff-filter=ADR` shows the name has only ever existed at one
path, added once at `f99e082`:

```
context/literature/reviews/deep_research_drug_targets_2026-09-16.primary-verification.tsv
```

The identification is checkable, not assumed: every claim this section makes
about the ledger matches that file exactly — 7 rows; genuine full-text reads
`DTR002`, `DTR006`, `DTR017`, `DTR026`; `DTR002-followup` "PDF available,
unread"; `DTR011` and `DTR005` abstract-verified. It is **review-scoped**, so a
later review either appends to it or opens its own; U3 took neither option,
because that is a curation decision for the unit that needs a row.

`pdf_manifest.tsv` is **not** a substitute for it. The manifest records whether a
PDF was inspected; §5(1) asks whether a *claim* was verified against a primary
source. `PDF-028` being `full_text_inspected = yes` does not put REF-059 in the
ledger, and U3 wrongly read it as satisfying §5(1) before correcting itself.

---

### 0.7 AC01 — and therefore U3 and U8 — rests on one post-extraction call

`a028ef3` withdraws a reassurance the audit had made about itself, and the
withdrawal lands squarely on this plan.

`AC01`'s `alias_challenged` verdict **rests entirely on D1**, the re-reading of
§2.1's direction-vote guard — the single post-extraction interpretive call in the
audit. Recomputing `class_verdict` over the committed member verdicts under the
*rejected* reading (every single-gene member `uninformative`):

| class | as reported | under the rejected reading |
|---|---|---|
| `AC01` | `alias_challenged` | **`unclassified_by_section_5_4`** |
| `AC02` | `unclassified_by_section_5_4` | unchanged |
| `AC03` | `unclassified_by_section_5_4` | unchanged |
| `AC04` | `rule_challenged` | unchanged |

`E_PAEP` is the only `concordant_with_alias` member of `AC01` and it is
single-gene, so the rejected reading removes the concordant half of the challenge
and nothing else moves. The audit states the consequence plainly: **"Everything
`AC01` carries falls with it: §5's 'yes, and narrowly', P1, and the §8 reranking
argument."**

**What that means here.** Two of this plan's units inherit D1 and must say so:

- **U3** exists only because `AC01` is `alias_challenged`. If D1 is wrong, U3 has
  no mandate and `AC01` joins `AC02`/`AC03` as unclassified.
- **U8**'s claim that the `dropout_e2` rerank is *mandatory* derives from the
  same §8 argument. If D1 is wrong, the rerank is optional rather than owed.

D1 is now declared to the harness as a `SEMANTIC_OR_PROTOCOL` repair, which is
the right category for it. Its merits are argued from text frozen at `491b337`
independently of the result it produces — §2.1's own table enumerates the eleven
single-gene members under "genes voting" with `n = 1`, none *reduced* by
anything, and `scrna_observation_map.tsv` records that an `S_PRL`/`S_IGFBP1`
divergence "is a FALSIFICATION of the aliasing, not a limit on the assay", which
is impossible if both members are undecidable. That argument looks sound. The
point is not that D1 is wrong; it is that **U3 and U8 are downstream of an
interpretive call rather than of a measurement**, and a v0.5 built on them must
carry that rather than present AC01 as raw data.

**What does *not* depend on D1:** `AC04`'s `rule_challenged` verdict, every
node-support label, every QC verdict, and the zero-absences finding of §0.1. So
§0.1, §0.2 and U4 stand untouched.

**Two further `a028ef3` corrections carried into this plan:**

- **`AC04` is held more loosely than §7.2 implied.** It was claimed under
  §3.1(4)'s exemption, which covers conclusions resting on presence or on
  divergence *between two members*; `rule_challenged` means the members agree,
  so its finding is a null on CNT-versus-HT magnitudes and the exemption does not
  apply — "a pun on the verdict name". **The §3.2 condition-entanglement caveat
  therefore binds `AC04` with full force**: decontX is cluster-dependent, the
  clusters are near-deterministic in condition, "and a flat CNT-versus-HT result
  on this layer is exactly the shape of result that a condition-entangled
  correction could produce."

  *Superseded in part at `252461b` — see §0.8.* This bullet's closing clause used
  to add that `AC01` survives the same caveat "because a correction that depresses
  HT uniformly cannot make one member rise ten-fold while its class-mates stay
  flat." **That argument has been withdrawn by the repository as never
  established** — decontX is not uniform — and replaced by a raw-UMI measurement
  (`node_support_finding.md:282-288`). `AC04`'s half of this bullet is unaffected
  and still binds with full force.
- **A zero-cell compartment-unit could have become evidence of non-movement.**
  `gene_movement` returned `uninformative` for a missing unit and `member_verdict`
  folded that into `no_material_move`. Latent — no committed verdict changes, all
  twelve primary units exist — but a reproduction with `SZ25`'s HT stromal unit
  dropped returned `S_PRL` as `divergent` on three donors, one of which did not
  exist. Anyone reproducing the audit needs the fix, not just the artifact.

---

### 0.8 What `252461b`..`7ee303f` changes for this plan — and what it does not

Five commits landed on `feat/scrna-node-support` past `a028ef3` — the state
`fbf5468` merged — and reached this branch through the merge at `5a55cf1`. **No U1–U8 prerequisite, ordering, test
requirement or scientific conclusion in this document changes because of them.**
What changes is the accuracy of five of its statements, and the strength of the
foundation under one of its units.

**(a) `AC01`'s condition-entanglement objection is now discharged by measurement,
not by argument — and only for two genes.** `252461b` withdrew the "decontX
depresses HT uniformly" reassurance (§0.7) and re-derived `AC01`'s two
load-bearing genes on raw `filtered_feature_bc_matrix` UMIs under the *identical
frozen rule*, applied by `node_support`'s own `unit_statistics` and
`gene_movement` rather than reimplemented. The join is complete — all 20,441
epithelial cells, zero unmatched — and **the divergence reproduces**: `PAEP`
`moves_up` 3/3 (+3.13 / +2.23 / +2.13 raw against +3.31 / +2.34 / +2.30
corrected), `HBEGF` `no_material_move` 3/3 (−0.34 / +0.65 / +0.19 against
−0.48 / +0.72 / +0.16). Every fold is within about 0.2 log2 of its corrected
counterpart, in both directions.

  The scope is deliberately narrow and this document must carry it that way:
  `decision_provenance.raw_layer_sensitivity.condition_entanglement_status` reads
  **`resolved_for_PAEP_HBEGF_only`**. The **pre-registration's** §3.2 still binds
  every other magnitude in the audit, `AC04`'s included. This **strengthens U3's evidence base without
  changing U3's mandate**, and it does not touch D1: the entanglement question and
  the D1 question are independent, and `AC01` still rests on D1 (§0.7).

**(b) The D1 dependence is now machine-readable and computed.** Each class in
`node_support_findings.json` carries a `decision_provenance` block with
`depends_on_deviations`, `registration_status`,
`counterfactual_verdict_without_D1` and `licenses_structural_change`. The
counterfactual is **computed, not asserted**, and it reproduces §0.7's table
exactly: `AC01` `alias_challenged` → `unclassified_by_section_5_4`, `AC02`,
`AC03` and `AC04` unchanged. **U3's checklist item "confirm D1 still stands" now
has an artifact to read** rather than only prose, and a unit that ingests the JSON
instead of the finding can no longer take `AC01`'s verdict without its condition.

**(c) `AC04` is weaker than §7.2 states, in the same direction §0.7 already
pushed it.** `252461b` removed "precise null" and "the cocktail does not raise
`E_LIF`" from the finding. `E_LIF` **does** rise in a separated way in two donors
(+0.59, +0.46 log2), below the pre-registered two-fold bar. The claim is now that
nothing moves *by the margin the design declared material in advance*, not that
nothing moves. §7.2 is corrected accordingly; §4.1's `AC04`-adjacent rows needed
no change, because they already carried the TI rows as evaluation-only. This does
**not** change U4, which was already evaluation-only; it lowers how hard `AC04`
may be leaned on inside it.

**(d) Two frozen artifacts moved for schema and provenance reasons, and no result
moved with them.** `node_support_findings.json` and `node_support_qc.tsv` are no
longer byte-identical to `91f79ed`. The base-state section enumerates every field
that changed and every field that did not; the changes are additive schema
(`c1_evaluated`, `c2_evaluated`, `decision_provenance`) plus **not-evaluated
semantics** for checks that were never run on the five non-primary myofibroblast
units — `NaN` / `""` / `false` → `null` / `not_applicable`, and `attribution`
`compartment_attribution_unsafe` → `not_applicable`. Reporting a *failure* for a
control that was never executed was the defect; reporting `not_applicable` is the
repair. Every primary-unit row, every numeric value, every node support label,
every member verdict and all four class verdicts are unchanged. **This is a
provenance repair, not an evidence revision**, and §12's T-G must record it as
such rather than re-pin the two files to make a test pass.

**(e) One vocabulary item was added and reaches §1.2.** `14b143f` added
`uninformative_no_integrity_control`, distinguishing "no integrity control is
*defined* for this compartment" from "the integrity control *failed*"
(`node_support.py:353-368`). It fires on no committed unit — every myofibroblast
unit fails `n_min` first — so it changes no result, but the U6 enum must carry it
or it will conflate the two on first reuse. §1.2's mapping table is corrected.

**(f) Two commits corrected claims about paths through v0.4's graph, and this
document makes one of its own.** `c551d9f` and `14b143f` (B7) found two
successive false route claims in `node_support_finding.md`, and `14b143f`
installed `NetworkClaimTest`, which now permits that document only literal quoted
rules and the separately computed `phenotype_inert` result — no transitive
reasoning at all. **That test guards `node_support_finding.md` only; it does not
guard this plan.** §7.1 contains a transitive claim of exactly the guarded shape:
that `network.bnd:214` makes `E_ITGAVB3_5` a required conjunct of
`X_ADHESION_ROUTE_SPP1`, "feeding `OUT_MATERNAL_ADHESION_COMPETENCE` and
`OUT_STABLE_ADHESION`". **Re-checked line by line against
`models/superset/adoc-literature-superset-v0.4.0/network.bnd` at `5a55cf1` and it
holds**: `:214` requires `E_ITGAVB3_5`; `:234` takes
`X_ADHESION_ROUTE_SPP1 or X_ADHESION_ROUTE_REDUNDANT` as a conjunct of
`OUT_MATERNAL_ADHESION_COMPETENCE`; `:238` takes that node as a conjunct of
`OUT_STABLE_ADHESION`. It is left as written because it is true and §7.1's
argument needs it. Any v0.5 unit that restates it must re-derive it from the
committed rules rather than copy it.

**What is untouched.** The headline of §0.1; §0.2 in full, including the derived
clamp form and the `strict_nv` call-path question; §3's taxonomy (both source
tables are byte-identical); §4's backlog adjudications; §5's promotion framework;
§6's combination table; §7.1's P1 reading and the owner decision under it; §7.3;
§8–§11; §14's rerank protocol; §16's do-not-implement list. The workflow ordering
U1 → U8 and the `[BLOCKED]` status of Gate 3b are unchanged.

---

## 1. Assessment of the proposed RNA → DT architecture

### 1.1 The core principle is right and already binding

"RNA constrains availability; it never sets a node ON" is the asymmetry
`node_support_preregistration.md` §6 already states as binding: strong presence
establishes biological availability and never that the Boolean state is ON; no
`retain` verdict may be upgraded to "node confirmed". Adopt unchanged.

### 1.2 Map the three states onto the frozen labels; keep both

| proposed state | frozen support label |
|---|---|
| `PRESENT` | `robustly_detected` (d ≥ 10% in 3/3) |
| `INDETERMINATE` | `sparse_or_low`, and every `uninformative` reason: `uninformative_n`, `uninformative_exposure`, `uninformative_integrity`, `uninformative_no_integrity_control`, `missing_unit` |
| `ABSENT_POWERED` | `not_detected_with_power` (+ `provisional_corrected_layer_only`) |
| **`NOT_ASSESSABLE`** | `not_RNA_assessable` |

The frozen vocabulary records *why* something is indeterminate; the coarsening
throws that away, so keep the three-state value as a derived view.
`uninformative_no_integrity_control` was added after the evidence root, at
`14b143f`, and fires on no committed unit (§0.8(e)); it is in the table because
U6 must not conflate "no integrity control is defined for this compartment" with
"the integrity control failed". And
`not_RNA_assessable` is a fourth state, not a kind of indeterminate: collapsing
them makes a node RNA can never speak about indistinguishable from one RNA
happened not to resolve.

Encode as a 4-element enum with the combination table frozen in §6.3 below, and
test that the combinator performs **no arithmetic on evidence states**. Writing
`ABSENT < INDETERMINATE < PRESENT` as `min()`/`max()` over integers is how it
silently becomes 0/50/100%.

### 1.3 Three of the four layers already exist

| proposed layer | already in the repository |
|---|---|
| A. node semantics | **three times.** `node_dictionary.tsv` (59 rows); `config/scrna_observation_map.tsv` (59 rows, **generated** by `src/dt_adoc/scrna/observability.py`); `docs/scrna/node_rna_interpretability.tsv` (27 rows, derived, three orthogonal axes) |
| B. component requirement logic | **absent.** `measurement_features` is a flat `;`-list: no grouping, no AND/OR, no role. The genuine gap. |
| C. assay-level evidence | **exists, frozen.** `node_support_evidence.tsv` (1,428 data rows + header) + `node_support_findings.json`. |
| D. contextual gates | **absent**, and blocked by §0.2. |

**Do not create `config/model_node_semantics.tsv`.** It would be the fourth
semantics table and two of the three existing ones are generated; a
hand-maintained fourth will drift. The repository has already been bitten by
exactly this (`v05_plan_review.md:158-159`). Extend `observability.py` to emit
the three axes for all 59 nodes instead.

**Keep the repository's three orthogonal axes over the proposed A/B/C/D
classes.** A single class conflates *what is measured* with *what may be
concluded*, and the two come apart: `E_PGR` is an activity state (proposed Class
B) measured by a regulon proxy whose namesake transcript moves **opposite** to
the state. `rna_can_constrain` / `rna_can_hard_off` become derived columns.

### 1.4 The gate layer should be generated, not hand-authored

The preference for a separate provenance-rich gate layer over embedding RNA state
in `.cfg` files is right, with one amendment: generate it from (component map ×
assay evidence × node semantics), for the same reason as §1.3. Add fields the
specification omits: `support_label` (the frozen label, not only the coarsened
state), `evidence_role`, `layer_caveat` (decontX condition-entanglement applies
to presence as well as absence), and `gate_computed` distinct from
`gate_applied`, so a gate deliberately not applied is visible rather than absent.

---

## 2. Proposed v0.5 workflow

Ordering corrected per §0.3.

```
frozen v0.4 / Stage-3      (58f0fba, never rewritten)
frozen scRNA audit         (91f79ed — the EVIDENCE root, already frozen)
scRNA code base            (7ee303f, merged here at 5a55cf1 — NOT 91f79ed)
        |
        v
U1  v0.5.0 scaffold + v0.4 immutability tests + line endings
        |
        v
U2  Gate 3a: de-alias S_PRL / S_IGFBP1, add the day-3 maternal stage,
    make OM-016 evaluable, and TEST THE ORDERING BY SIMULATING THE TRANSIENT
    ** [BLOCKED -- both halves refused, on DIFFERENT grounds. See docs/
       v05_u2_gate3a_blocked.md.
         de-alias : blocked on MEASUREMENT. The nodes are indistinguishable to
                    the model, and the one surviving repair needs an IGFBP-1
                    binarisation threshold that may not be drawn from the
                    diagnostic series OM-002 without leakage.
         day-3 arm: blocked on PHYSICAL-TIME SEMANTICS, which no assay supplies.
                    Day 3 and day 6 carry the same agents and concentrations, so
                    the BOOLEAN INPUT VECTOR is the same, and duration_units is
                    relative_only. (Other fields do differ, including the
                    collection window -- see the U2 record.) ] **
        |
        v
U3  AC01 mechanistic reconsideration -- DERIVE replacement rules, or record
    that none can be derived.  No free Boolean variables.
    ** [DONE, NEGATIVE -- none derivable; alias left in place and flagged.
       AC01 is ONE structural fact: all nine members compute the SAME EFFECTIVE
       BOOLEAN FUNCTION, whose SUPPORT is {IN_E2, IN_PROGESTIN,
       IN_MIFEPRISTONE}. NOT a shared syntactic closure -- E_ITGAVB3_5
       additionally reaches E_KLF12_HIGH through E_LIF and the other eight do
       not; that arm is absorbed, so E_KLF12_HIGH is in its closure and not in
       its function's support. A repair needs a second determinant that is NOT
       a subset of E_SECRETORY_STATE. The closest
       candidate passes the delta screen and fails the evidence criteria.
       See docs/v05_u3_ac01_no_derivable_rule.md. ] **
        |
        v
U4  AC04 / GP130 axis: rule-variant FAMILIES, evaluation-only
    ** [DONE, EVALUATION-ONLY -- no canonical promotion and no mechanism change.
       Yap/Dimitriadis 2011 read in full: it names ANXA2 and FLOT1 as IL-11-
       regulated membrane proteins and settles NOTHING, because it runs no LIF
       comparator and no functional endpoint. TI002's family stays uncollapsed
       AND uncompleted; the IL-11-specific arm is refused on evidence despite
       being the largest structural gain available. CD98-d staged from TI001's
       literal text; the one experiment that would earn its third disjunct is
       hCG-free embryo-conditioned medium. Gate 2 re-derived on a closed level
       vocabulary: no verdict changes.
       See docs/v05_u4_gp130_axis.md. ] **
        |
        v
U4b candidate-node closure: all 14 Sept-11 candidates adjudicated
    ** [DONE, NOTHING PROMOTED -- no mechanism change. Every candidate carries a
       node verdict and an encoding verdict SEPARATELY. AS U4b CLOSED THEM:
       1 RULE_VARIANT_ONLY, 2 WAIT_FOR_EXPERIMENT, 6 RETAIN_CATALOG_ONLY,
       5 EVIDENCE_UNVERIFIED, 0 MERGE_WITH_EXISTING, 0 REJECT. LIVE COUNTS AFTER
       U5b (2026-09-23): 1 / 2 / 7 / 3 with 1 REJECT (E_GLYCOSYLATION_PROGRAM),
       0 MERGE_WITH_EXISTING and 0 PROMOTE; 1 / 2 / 6 / 4 after the 2026-09-22
       PRL/IGFBP1/FOXO1 unit.
       Seven candidate nodes changed disposition,
       from five section 4.1 entries; five moved stricter. Seven of nine DRREF
       references verified or reused, two access-blocked, one candidate MISCITED.
       Section 5 itself was defective and is repaired -- it defined a consequence
       for one of its failure modes. Three structural gains found, all three
       refused on evidence; the largest, S_WNT4_CTNNB1 with the declared-but-unread
       IN_XAV939, reaches 35 -> 36 alone and 35 -> 37 with the evidenced S_FOXO1
       conjunct, both at no free-variable cost.
       See docs/v05_u4b_candidate_node_closure.md. ] **
        |
        v
U5  structural audit + identifiability rerun (carry the matched-unit caveat)
    -- audits the model AS OF U4b, which is byte-identical to the pre-U4b model
        |
        v
U6  node-semantics generator extension + component map (schema only)
    ** [DONE, SCHEMA ONLY -- no requirement structure declared; HGNC renames
       recorded forward-only. See docs/v05_u6_semantics_components.md. ] **
        |
        v
U7  MaBoSS mutation interface (§0.2) -- only if U8 or personalization needs it
        |
        v
U8  Stage-3 rerank vs the frozen dropout_e2   <- MANDATORY, per the audit
        |
        v
[BLOCKED]  Gate 3b / interface relays -- gated on the variability-semantics
           decision and on gate3a_closure_audit.md's three grounds
```

Each U is its own unit, session and review-gate lineage. Do not batch.

---

## 3. Node-semantic taxonomy for current v0.4 nodes

27 of 59 nodes are RNA-relevant; 32 are `not_RNA_assessable` (14 `IN_*`,
4 `OUT_*`, 9 `X_*`, plus `E_ANXA2_ACTIN`, `E_CDH1_APICAL`, `E_DAG1_CLEAVED`,
`E_RECEPTIVE_SURFACE`, `S_PKA`). Assignments below are the frozen
`node_rna_interpretability.tsv`, made before any expression value was read.

| measurement_type | nodes | absence establishes |
|---|---|---|
| `direct_transcript` (12) | `E_PAEP`, `E_HBEGF`, `E_IHH`, `E_LIF`, `E_PC6`, `E_SPP1_EXPR`, `E_KLF12_HIGH`, `S_BMP2`, `S_PRL`, `S_IGFBP1`, `S_SPP1`, `S_HAND2` | 9 × `challenges_contemporaneous_expression`; **3** × `cannot_inform_functional_state` (`E_PAEP`, `E_SPP1_EXPR`, `S_PRL`) |
| `regulon_or_activity_proxy` (4) | `E_PGR`, `S_PGR`, `S_NR2F2`, `E_GP130_STAT3` | mostly `challenges_constitutive_or_active_use` |
| `abundance_proxy_only` (6) | `E_CD98_CD9`, `E_DAG1_FULL`, `E_ITGAVB3_5`, `E_MUC1_BARRIER`, `E_PODXL`, `S_TAZ_ECM` | **`cannot_inform_functional_state`, all six** |
| `gene_program` (4) | `E_SECRETORY_STATE`, `E_MUC1_SLEX`, `E_ESTROGENIC_PROLIFERATION`, `S_DECIDUALIZED` | varies |
| `pathway_score` (1) | `S_FGF_MITOGENIC` | challenges constitutive use |

### Ambiguous cases — each a real problem

1. **`E_SECRETORY_STATE` — class and rule disagree.** Classified `gene_program`
   with seven markers, but its rule is `IN_E2 and E_PGR`, a two-signal
   conjunction. Whatever RNA concludes about the programme does not constrain the
   conjunction. It is the hub of the 9-member AC01 class, so the mismatch is
   upstream of everything in U3.
2. **`E_PGR` / `S_PGR` — the namesake gene is direction-uninterpretable.** R2
   excludes `PGR` from both direction votes: epithelial PGR transcript can move
   opposite to the state. A component map keyed on "the gene named like the node"
   is wrong here.
3. **`E_MUC1_SLEX` / `E_MUC1_BARRIER` — one feature, two nodes, exact logical
   complements.** `MUC1` measures both; the pre-registration records the
   cross-class dependence as a caveat on both. A component map must represent the
   shared feature or it double-counts one measurement as two.
4. **`E_DAG1_FULL` / `E_DAG1_CLEAVED` — a recorded assay limit.** One transcript
   cannot distinguish intact from cleaved; `E_DAG1_CLEAVED` is `not_observable`.
   RNA can never adjudicate this pair.
5. **`S_TAZ_ECM` — committed symbols absent from the object.** `CTGF`/`CYR61` are
   not present under those symbols and **no alias was substituted**.
   `node_support_deviations.md:241-246` records an **owner decision**: the audit
   stays as run, and HGNC alias handling (`CTGF`/`CCN2`, `CYR61`/`CCN1`) is "to be
   reconsidered explicitly **before any `S_TAZ_ECM` evidence is used in v0.5**".
   That is a required U6 decision, not a test to write.
6. **`E_KLF12_HIGH` — `not_blind = true`.** Values committed before the audit
   design existed. Excluded from any construction-role mapping.
7. **`S_FGF_MITOGENIC` — its rule is vacuous.** TI019: `S_FGF_MITOGENIC =
   not S_HAND2`, so `S_FGF_MITOGENIC and not S_HAND2` inside
   `E_ESTROGENIC_PROLIFERATION` **reduces to `not S_HAND2`**; the intermediate
   contributes nothing. It carries five measurement features and is a live
   `pathway_score` node in the taxonomy, so RNA evidence about it can reach no
   prediction at all. Prune it from any RNA work until the rule is repaired.

---

## 4. Deep-research backlog status

**No Sept-11 candidate node may be promoted *on Sept-11 evidence*.** ~~All 14 are
unadjudicated~~ **— all 14 are now adjudicated, by U4b, and none is promoted** —
and the 9 `DRREF-*` references have zero rows in
`citation_verification.tsv` — and per §0.6 that file would not establish full text
anyway. The Sept-16 bundle is the usable one: 28 adjudications, 19 TI rows
(14 with a measured Δ; TI013/014/015/016/019 read `not measured` or `n/a`), and
4 genuine full-text reads.

**U4b closed the Sept-11 node set.** Of the 9 `DRREF-*` references, **seven are
now verified or reused**: **six newly read in U4b** — Yu 2018 from a PDF the owner
supplied during the unit, Kinnear 2019, Griffiths 2019 and Liao 2024 from
Europe PMC full-text XML, and (at weaker provenance, via the PMC web rendering)
Li 2013 and Vasquez 2015 — **plus Marwood 2009 reused from U4 without re-reading**. **Two were subscription-only at the time and were recorded as
access blockers, not as negative evidence** (Ma 2023, Zhou 2021) — **both have
since been read and registered**, on 2026-09-18, as REF-077/PDF-049 and
REF-076/PDF-048, so **all nine are now verified or reused**. And one
candidate, `E_ESR1_ACTIVITY`, turns out to cite a paper that does not support it.
Record: `docs/v05_u4b_candidate_node_closure.md`; ledger and disposition table in
`context/literature/reviews/deep_research_adhesion_model_2026-09-11.{primary-verification,candidate-node-dispositions}.tsv`.

### 4.1 Classification

> **Superseded for the fourteen Sept-11 candidate *nodes* by U4b.** The
> authoritative record is now
> `context/literature/reviews/deep_research_adhesion_model_2026-09-11.candidate-node-dispositions.tsv`
> with `docs/v05_u4b_candidate_node_closure.md`, which carry a **node verdict and
> an encoding verdict separately** — a distinction this table has only one column
> for. The rows below are kept and **corrected in place** rather than deleted,
> because the errors in them are instructive: four of the five that changed had
> drifted in the *lenient* direction, and all five drifted for the same reason,
> which §5's repair now names. Rows about candidates that are not Sept-11 nodes
> (TI005, TI009, TI010, TI017, TI011, TI014, TI018, the CD98 family) are
> untouched by U4b and stand as written.
>
> **Two counts, kept apart because they are different things: five §4.1
> classification *entries* changed, covering **seven candidate *nodes*** whose
> disposition moved.**
>
> | candidate node | was | is | why it moved |
> |---|---|---|---|
> | `S_BMP_SMAD` | split across RETAIN_CATALOG_ONLY (TI006/7) and WAIT_FOR_EXPERIMENT (TI008) | **WAIT_FOR_EXPERIMENT** | consolidated onto the first failing criterion, §5(2); evidence upgraded to full text |
> | `S_FOXO1` | RETAIN_CATALOG_ONLY | **WAIT_FOR_EXPERIMENT** | the evidenced determinants are of FOXO1 mRNA/total protein, not of the **nuclear** activity the node names — §5(2), not §5(4) |
> | `E_ESR1_ACTIVITY` | WAIT_FOR_EXPERIMENT | **EVIDENCE_UNVERIFIED** | its sole citation, `REF-020`, does not support the node |
> | `E_JAG1_NOTCH3` | RETAIN_CATALOG_ONLY | **EVIDENCE_UNVERIFIED** | §5(1) was never assessed; the row's basis is an *encoding* argument |
> | `S_AKT_EXCESS`, `S_ERK`, `S_TGFB_CONTEXT` | RETAIN_CATALOG_ONLY | **EVIDENCE_UNVERIFIED** | no reference, no candidate edge, no `mechanisms.tsv` row |
>
> Two more §4.1 entries are **resolved or split without the disposition value
> moving**: `X_ECM_FN1_COL4`'s "pending a measured Δ" is closed (the Δ is
> measured, and the node fails earlier, on its definition), and the
> `E_GLYCOSYLATION_PROGRAM` / `E_SLEX_SURFACE` row is split because the two fail
> differently. `S_WNT4_CTNNB1`, `E_SOX17`, `E_ITGA2B1` and `X_IL11` keep their
> disposition with the basis corrected or strengthened.
>
> **U4b issues no `REJECT` and no `MERGE_WITH_EXISTING`.** `X_ECM_FN1_COL4` is
> not a duplicate of `S_TAZ_ECM` — Boolean-function equality under a *rejected*
> rule is not node identity, and the node dictionary puts the two in different
> compartments with different model roles. `E_GLYCOSYLATION_PROGRAM` is not
> refuted — falsifying transcript co-regulation is not falsifying a functional
> state while the reference covering half the definition is unread. Both are
> `RETAIN_CATALOG_ONLY`, failing §5(0-insufficient).
> `docs/v05_u4b_candidate_node_closure.md` §4.2 and §4.4.

| candidate | class | why |
|---|---|---|
| `X_IL11` as an independent free input, `E_GP130_STAT3 = E_LIF or X_IL11` | **RULE_VARIANT_ONLY — evaluation-only family** | Revision 1 said PROMOTE; that was wrong. TI002's recommendation is verbatim "**EVALUATION-ONLY VARIANT** with X_IL11 as a free input … Carry as a **RULE FAMILY**: convergent-only versus convergent-plus-an-IL11-specific-arm." DTR002's `what_is_NOT_supported` is explicit that "a convergent-only motif suffices" is **not** supported — "the dissociation is DOWNSTREAM of both STAT3 and ITGA2, so a model in which both ligands feed one STAT3 node predicts interchangeability, which this contradicts." The exact rule revision 1 promoted is the one the full text contradicts. Δ 35 → 37 for the family. |
| `E_CD98_CD9` rewire | **RULE_VARIANT_ONLY** | Two distinct rows, which revision 1 merged. **TI001** is `= E_GP130_STAT3 or IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL` (Δ 35 → 36), and its "both inputs are declared in v0.4 and **read by no rule**" applies to *those* two inputs. **CD98-c** (`gate3_candidate_variants`) is `… or IN_E2` — and `IN_E2` **is** read, at `network.bnd:70` and `:90`. Also: DTR005 records "a generic embryo-conditioned inducer — **no source read names one**", so TI001's literal rule contains an unsupported disjunct. Carry both as a family; promote neither. |
| TI004 package (TI001 + TI002) | **RULE_VARIANT_ONLY** | Δ 35 → 38, the preferred *evaluation* package. Not a promotion. |
| `X_IL11` staged form (`= S_DECIDUALIZED`, TI003) | **REJECT** | Enlarges the decidual class Gate 3a exists to break. `blocks_v05 = yes`. |
| `E_ITGA2B1` | **REJECT** (edge) / **RETAIN_CATALOG_ONLY** (node) | DRE009 `REJECT_CONFIDENCE_LABEL`, reconfirmed DTR018: the row records integrin-α2 *expression/protein* while the node is a receptor-activity state, and PMID 19213836 reports α2β1 neutralisation reducing **LIF**-induced, not IL11-induced adhesion. The 2026-09-14 clarification is explicit that redefinition as an abundance state **is not a promotion route**. |
| `S_BMP_SMAD`, `S_WNT4_CTNNB1`, `S_FOXO1` as staged (TI006/TI007) | **RETAIN_CATALOG_ONLY** for `S_WNT4_CTNNB1` and `S_FOXO1`; `S_BMP_SMAD` consolidates below | **UPDATED 2026-09-22:** Labied 2006 (`REF-078`/`PDF-050`, ledger row `PIF-001`) measures FOXO1 nuclear versus cytoplasmic localisation *as localisation* — confocal immunofluorescence plus cytosolic/nuclear fractionation — in primary human endometrial stroma, under 8-br-cAMP ± MPA, both agents of `COND-FULL-COCKTAIL`. §5(2) therefore **clears**, and `S_FOXO1` now fails at **§5(4)** → **RETAIN_CATALOG_ONLY**: `S_PGR and S_PKA` is *identical* to `S_DECIDUALIZED` (Δ 35 → 35, vacuous, re-verified over all 524,288 assignments), and no evidence-supported variant both gains a function and breaks a named alias class. See `docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md`. This is an evidence **advance** recorded as a vocabulary **demotion**. **Superseded basis, retained for the record:** Δ 35 → 35; still inert after stromal repair (41 → 41) plus a new alias. Biology accepted, staged form rejected. **U4b, three corrections.** (i) "Biology accepted" was an *assertion*: all three references are now read in full (`U4B-DRREF-001/002/009`) and the biology is accepted on evidence, with `S_FOXO1`'s semantics materially strengthened — FOXO1 siRNA abolishes PR genomic binding, so it is not a marker and not a duplicate of `S_DECIDUALIZED`. (ii) `S_WNT4_CTNNB1`'s inertness is a *faithful-encoding* consequence, not a staging defect: Li 2013 tests exactly one input to WNT4, and a necessary mediator with one input is an alias by construction. (iii) `S_FOXO1` moves to **WAIT_FOR_EXPERIMENT**, failing at §5(2) rather than §5(4). Revision 1 recorded two evidenced determinants and therefore a passed §5(2); **under external review that is corrected** — both Li and Vasquez measure FOXO1 **mRNA and total protein**, while the node is FOXO1 **nuclear** activity and Vasquez's own fractionation shows most FOXO1 is cytoplasmic. A determinant of namesake abundance is not a determinant of an activity state. The two-rule divergence stays on the record as a **diagnostic**: `and S_PKA` is supported and measures 35 → 35 with the decidual class growing to seven, while `or S_PKA` measures 35 → 36 and is **contradicted** by Li 2013, where WNT4 siRNA suppressed FOXO1 *with cAMP present*. It is a real conflict and it is not what excludes the node. |
| `S_BMP_SMAD` with a determinant ≠ BMP2 (TI008) | **WAIT_FOR_EXPERIMENT** | Δ 35 → 37 if it exists; no local evidence bounds it. **U4b: confirmed from full text, and `S_BMP_SMAD` consolidates onto this row.** Liao 2024 was the paper most likely to supply the determinant and does not: in its only physiological comparison BMP2 transcript and pSMAD1/5 fall *together*, receptors and antagonists are Discussion context and unmeasured, and the one dissociation is SMAD1/5 siRNA — a laboratory construct, the same §5(2) exclusion that blocks PC6-b. What the full text *does* settle is §5(3): pSMAD1/5 is a directly measured activity state in primary human stroma and SMAD1/5 knockdown causally impairs decidualization, so the node is not a relabelling. |
| `E_GLYCOSYLATION_PROGRAM` → `E_SLEX_SURFACE` (TI013) | **UPDATED 2026-09-18, AND THE TWO NOW MOVE IN OPPOSITE DIRECTIONS.** Ma 2023 was obtained, read in full and registered as **REF-077/PDF-049**. `E_GLYCOSYLATION_PROGRAM` → **`REJECT`** at §5(0-refuted), scoped to its definition: the two enzymes its label conjoins were measured **together, in the same cells, under the same stimulus**, and move significantly in **opposite** directions (FUT3 up *p* < 0.001, ST3GAL3 down *p* < 0.05), with the frozen ADOC scRNA audit corroborating that these enzymes do not co-move (a *different* exemplar pair, FUT6 against ST3GAL4, so supporting context rather than independent replication of the named pair). This **discharges** the evidentiary ground of external-review finding B3 — that the reference bearing on the FUT3 half was unread — while **honouring** B3's logical ground, because the functional glycan-output state survives as `E_SLEX_SURFACE`. `E_SLEX_SURFACE` → disposition **unchanged** at `RETAIN_CATALOG_ONLY`, but its first failing criterion moves **§5(2) → §5(4)**: Ma supplies the determinant U4b lacked, and supplies it for the **right variable** (surface sLeX measured *as* surface sLeX by flow cytometry), so the activity-versus-abundance test does not fire. It now fails only on measurement — the staged pair still takes 35 → 35 while growing AC01 9 → 11. The **committed `E_MUC1_SLEX` was not reopened**, and no `X_IL1B` or `IN_IL1B` input was created. See `docs/curation_increment_08_blocked_sources.md`. **Superseded basis, retained for the record:** U4b split this row; both → RETAIN_CATALOG_ONLY, for different reasons. The replacement of `E_MUC1_SLEX` stays rejected for both | TI013: the staged pair is pass-through and inert. The staged bundle already records `disposition = catalog_only` for it (DRUNR-004: "No single bounded upstream Boolean rule is established"), so catalog retention is the repo's own position and is preserved. What is newly **rejected** is the proposal that it *replace* the committed node, and the audit is why: the ten glycosyltransferases do not behave as a programme — FUT6 +1.60/+2.99/+2.73 while ST3GAL4 −1.11/−0.25/−1.45 — so the *replacement* premise fails. **That is a statement about the replacement, not a refutation of the candidate node**; an earlier revision wrote "refutes the programme premise" and correction (ii) below withdraws the stronger reading. **U4b, three corrections.** (i) **TI013's structural expectation was wrong in the lenient direction.** It predicted "no alias broken"; measured, the staged pair takes 35 → 35 **and grows AC01 from nine to eleven**. (ii) **The two candidates fail differently and must not share a verdict.** Yu 2018 (DRREF-005, now read in full) names ST3Gal3 "the key enzyme", reports no ST3Gal4 difference across the cycle and measures no FUT3 at all — so the node's **own cited primary** does not support the programme semantics, independently agreeing with the audit. **That is definition-insufficiency, not refutation, and revision 1's `REJECT` is WITHDRAWN under external review:** falsifying transcript co-regulation among selected enzymes is not falsifying the existence of a coherent functional glycosylation state, and DRREF-006 (Ma 2023) — the reference bearing on the **FUT3** half of the definition — is access-blocked and unread. A refutation cannot rest on silence about a component whose evidence was never obtained. A measured glycan *output* state would be a different candidate. (iii) `E_SLEX_SURFACE`'s core claim **is** verified — three orthogonal perturbations — but only in RL95-2/JAR carcinoma lines, with a measured proliferation confound, and with no determinant, because DRREF-006 (Ma 2023) is subscription-only and was not obtained. |
| `E_SOX17` | **RETAIN_CATALOG_ONLY** | ~~DRE012/DRE013 marked `confidence=verified` but DRREF-004 has no full-text check; as staged it is a pass-through inside AC01, hence inert.~~ **Both halves of that basis are corrected by U4b, and the disposition survives both corrections.** DRREF-004 (Kinnear 2019) **now has a full-text check** (`U4B-DRREF-004`), and the full text makes the refusal *firmer*, not weaker: **every functional experiment is in ECC-1, an endometrial carcinoma line by the authors' own Methods**, and the only primary human tissue data is immunohistochemistry with no perturbation — the same species-and-system failure U4 recorded for ANXA2/FLOT1. And "hence inert" is too kind: measured, the staged EDGE-012 + EDGE-013 takes 35 → 35 **and grows AC01 from nine to ten**. The biology is real — knockdown and SOXF inhibition both abolish spheroid adhesion — and is dose-graded, which `or` cannot express. **The first failing criterion is §5(2), not §5(4)**, corrected under external review on the same test that moved `S_FOXO1`: the node is SOX17 *activity* and its only determinant evidence is a 1.6-fold *protein abundance* rise. The AC01 measurement is retained as a diagnostic. It stays `RETAIN_CATALOG_ONLY` rather than `WAIT_FOR_EXPERIMENT` because half the unblock — a primary-cell or organoid replication — is external to this platform. |
| `E_ESR1_ACTIVITY` | ~~WAIT_FOR_EXPERIMENT~~ → **EVIDENCE_UNVERIFIED** (U4b) | As a pass-through between `IN_E2` and `E_SECRETORY_STATE` it is Δ 35 → 35. `IN_E2` is *design*-collapsed into the 5-member cocktail class, not rule-collapsed, so the node gains only with a determinant `IN_E2` lacks. The frozen `dropout_e2` arm is the experiment that informs it. **U4b: the Δ was asserted here and is now measured — it holds at 35 → 35. But the disposition cannot rest on the structural step, because an earlier criterion fails: the node's *sole citation* is `REF-020` = Zaragozano 2026, the ADOC platform paper, which studies neither ESR1 nor receptor pathway activity, and `mechanisms.tsv` DRMOD-06 states the evidence as "model necessity plus ADOC hormonal context".** This is the only one of the fourteen that is **miscited** rather than merely unverified. `WAIT_FOR_EXPERIMENT` implies §5(1) was cleared; it never was. `dropout_e2` stays in the unblock condition, but it informs only whether `IN_E2` has a determinant-relevant effect — not the prior question of whether ESR1 *activity* is separable from exposure at all. |
| `E_JAG1_NOTCH3` | ~~RETAIN_CATALOG_ONLY~~ → ~~EVIDENCE_UNVERIFIED~~ (U4b) → **WAIT_FOR_EXPERIMENT** (2026-09-18) | **UPDATED 2026-09-18:** Zhou 2021 was obtained, read in full and registered as **REF-076/PDF-048**, so §5(1) is satisfied and the node moves to `JUSTIFIED_SYSTEM_LIMITED` — JAG1 knockdown reduces trophoblast-spheroid adhesion in **primary human endometrial epithelial cells** (n = 5) as well as Ishikawa, NOTCH3 NICD is measured as **pathway activity** by cleaved-domain immunoblot, and the adhesion effect is temporally separated from the proliferation effect (3–8 h versus > 80 h). **The encoding did not move at all.** The paper perturbs **no** hormonal, steroidal, cAMP or cytokine input to JAG1 anywhere, so the first failing criterion is now §5(2) and **DRUNR-005 is confirmed by the source rather than inherited**: no `IN_P4 → JAG1`, no `IN_E2 → JAG1`, no `E_SECRETORY_STATE → JAG1`. Two limits are recorded and are not the unblock: NOTCH3 is **not** shown to be the necessary receptor (no receptor perturbation; NOTCH1/2 NICD *rise*), and the primary-cell NOTCH3 replication is a **non-significant trend, *P* = 0.073**, although the paper's own prose calls it "confirmed". A JAG1/canonical-Notch → `E_SPP1_EXPR` candidate relation is catalogued at **canonical-Notch specificity, never NOTCH3**, because MAML1 is shared by all four receptors. See `docs/curation_increment_08_blocked_sources.md`. **Superseded basis, retained for the record:** DRUNR-005 (`context/literature/staging/deep_research_adhesion_model_2026-09-11/unresolved_mechanisms.tsv`, **not** the v0.4 model file, which uses `UNR-*` ids): "Would require inventing hormone-to-JAG1 logic" — forbidden. **U4b: that basis is an *encoding* argument and the node's evidence step was never assessed.** DRREF-007 (Zhou 2021) is subscription-only and was not obtained, so §5(1) fails and `RETAIN_CATALOG_ONLY` — which §5 reserves for candidates passing (1)–(3) — was inherited rather than earned. The encoding stays rejected independently: measured, the only gaining form (free input, 35 → 36) *is* the invented determinant, and binding it to the secretory programme gives 35 → 35 with AC01 9 → 10. **The node is not rejected for being paywalled.** |
| `S_AKT_EXCESS` / `S_ERK` | ~~RETAIN_CATALOG_ONLY~~ → **EVIDENCE_UNVERIFIED** (U4b) | DRUNR-007 disease/context dependent; DRUNR-008 "No identifiable first-version rule from current ADOC data." **U4b: both have an *empty* `refs` field in `candidate_nodes.tsv`, no candidate edge, and no `mechanisms.tsv` row of their own.** There is nothing to verify, so §5(1) fails at the first step and the softer label was pure inheritance — this is the clearest instance of the drift U4b was run to find. No structural measurement was made for either, deliberately: no encoding was ever proposed, and constructing one to measure it would be evaluating an invention. *Worth carrying forward:* DRUNR-007 names `S_AKT_EXCESS` a "candidate modifier of `S_FOXO1`", and Vasquez 2015 shows FOXO1 activity is set by nuclear-versus-cytoplasmic localisation without identifying what sets it — so one verified localisation determinant would move two candidates. **UPDATED 2026-09-23 (U5b), `S_AKT_EXCESS` only:** re-adjudicated on Kang 2022 (`PIF-007`, `U5B-001`) it clears §5(1) and fails at §5(2) — CAPN7 and the endometriosis state are its determinants and ADOC varies neither — so it reads **`RETAIN_CATALOG_ONLY`**, `EXTERNAL`. `S_ERK` is unchanged. |
| `S_TGFB_CONTEXT` | ~~RETAIN_CATALOG_ONLY~~ → **EVIDENCE_UNVERIFIED** (U4b), still flagged `ensemble_only`, and now also `formalism_verdict = outside_formalism` | DRUNR-006: "A single universal sign would be biologically misleading." Not waiting for anything — unrepresentable as a single-sign Boolean node. **U4b: there are two independent blocks here and one label carried neither explicitly.** (1) `refs` is empty — nothing to verify, so §5(1) fails first. (2) The declared sign is `biphasic`, which is §8's Q3 category, the same class as the EPAC/RAP1 potentiation TI011 refused — so verification alone would *not* make it promotable. The two are now recorded in separate columns. *The only verified TGF-β observation this repository holds* is Domínguez 2010 (DTR005, read in full in U4): TGF-β significantly **reduces** membrane CD98 in primary human EEC — epithelial, single-direction, wrong compartment for this node. |
| `X_ECM_FN1_COL4` | **RETAIN_CATALOG_ONLY**, "pending a measured Δ" resolved (U4b) | No TI row computes one. `S_TAZ_ECM`'s feature list already contains `FN1` and `COL4A1`. Run the Δ computation before adjudicating. **U4b ran it, and the Δ is a trap.** The staged package measures 35 → **36** — which reads as a promotion case until you see that the whole +1 comes from `E_ITGA2B1`, an edge rejected twice; the ECM node *alone* is 35 → 35 and **enlarges the decidual class from six to seven**, the TI003 failure mode. But it never reaches the structural rung: (i) Griffiths 2019 (now read in full) localises COL4A1 to the **epithelial** basement membrane and reports *no* stromal difference, so EDGE-016's decidual determinant points at the compartment measured as unchanged; (ii) **FN1 is supported by neither reference** — Griffiths never measures fibronectin, and in Marwood it is an assay *substrate*, so the node conjoins two ligands with evidence for one. That definition defect is the **first** failing criterion, §5(0-insufficient). **Revision 1 recorded `MERGE_WITH_EXISTING` against `S_TAZ_ECM` and that is WITHDRAWN under external review:** the staged rule's Boolean equality is a property of a rule this same document rejects, and the model's own dictionary separates the two — `S_TAZ_ECM` is `compartment = stroma`, `model_role = mechanical_regulator`, `measurement_proxies = "TAZ activity and collagen program"`, naming neither `FN1` nor `COL4A1`, while the candidate is `compartment = extracellular`, `role = matrix_state`, proposed explicitly to "complement stiffness/mechanics". The alias under the staged rule is **recorded** against any future encoding rather than acted on. The verified COL4A1 biology is real and is the component a restated definition should be built on. |
| `E_PC6` / `E_DAG1_CLEAVED` split (TI009 / PC6-b) | **WAIT_FOR_EXPERIMENT** | Δ 35 → 38, breaks **two** classes — highest single-edit leverage. Full-text verified (DTR011, Heng 2015). Blocked: the *physiological* cleavability determinant is absent, and a cleavage-site mutant is a laboratory construct, not an ADOC state. |
| `E_ITGAVB3_5` own determinant (TI010) | **WAIT_FOR_EXPERIMENT**, prerequisite | Δ 35 → 37; absorbed in all 2^19 assignments, so an anti-integrin arm would spend embryos on a model-unpredictable result. |
| `S_HH_RECEPTION` (TI017) | **WAIT_FOR_EXPERIMENT** | Measurable (PTCH1/GLI1), druggable (SMO antagonists), named in `adoc_dt_implementation_spec.md:284`. Recorded as "**CANDIDATE NODE, NOT PROMOTABLE.** Better biologically grounded than any competence placeholder, and measured to buy nothing on its own." Inert as pass-through (35 → 35); with a competence determinant it creates a new `S_HH_RECEPTION ≡ S_NR2F2` alias. Its evidence base is **mouse uterine conditional knockout** (REF-025 Franco 2010, REF-026 Kurihara 2007), and LIT-IHH-001 itself flags that human attachment causality is partly transferred from mouse genetics. **Correction to revision 1:** REF-075 (Wei 2010) records response to **CDB-2914 (ulipristal, a PR modulator/antagonist)**, not a progestin, and DTR026 states general human expression is "**explicitly NOT sufficient**". What is missing is a human compartment-specific **necessity** test. |
| `S_NR2F2` competence determinant (TI005) | **REJECT the placeholder**; the determinant question stays open | The repo's own verdict is "**UNRESOLVED.** The determinant question is real and unanswered. **Do NOT promote a competence node.** The best-evidenced LOCATION for the missing step is the stromal Hedgehog reception step — see TI017 — which is also not yet promotable." Δ 35 → 38 and it breaks a class, on an invented latent variable. See §0.4. |
| `S_EPAC_RAP1` (TI011) | **REJECT as a node, keep the verdict** | Kusama 2013 full text: the EPAC/RAP1 arm is a **graded potentiator**, which a rate-free Boolean model cannot express. Evidence accepted (coupling verdict changed); node rejected. See §8's third category. |
| Direct `S_NR2F2 → E_ESTROGENIC_PROLIFERATION` (TI018) | **REJECT — measured worse** | Δ 35 → 34; already represented via `S_HAND2 → S_FGF_MITOGENIC`, and the direct edge absorbs `IN_HAND2_LOSS`. |
| `S_IGFBP1 → S_DECIDUALIZED` (TI014 / IGFBP1-fb) | **REJECT for v0.5** | Stands on the **cycle hazard**: a 14-node cycle where the enumerator assumes a DAG. *Correction to revision 1:* the leakage half is overstated — OM-002 is `calibration_role = diagnostic` / `non_inversion_diagnostic_secondary_ranking`, explicitly "demoted from a hard gate" and "never excludes a candidate on its own", and no magnitude-fitted term remains. Note separately that OM-002's `censoring_note` records "the column-to-chip mapping for IGFBP-1 is **LOST, not merely unverified**", so the 3/5 direction is an unpaired column comparison. **But TI014 also yields something U2 should use:** the full text "confirms an IGF-INDEPENDENT alpha5beta1 route and rules out a separate direct PRL edge", giving Gate 3a "an evidenced structural **ASYMMETRY** between the two markers — IGFBP-1 has an outgoing route, PRL is not shown to". That is mechanistic support for separating them, independent of the ELISA timing. |

### 4.2 Two non-topology items that gate everything above

- **TI016 — the Gate 2 separability invariant.** `target_class` in
  `drug_target_catalog.tsv` is free text: **34 rows, 24 distinct values**
  (revision 1 inverted this). The invariant is partly an artifact of naming
  granularity and must be re-derived against a closed vocabulary, with every
  changed verdict surfaced, before topology promotion — otherwise the
  `ARTIFICIALLY_COUPLED` verdicts that motivate the repairs rest on a defective
  axis.

  *Two corrections from U4, which did the re-derivation
  (`docs/gate2_target_level_rederivation.md`).* **(a) The closing clause was
  already superseded when it was written.** No `ARTIFICIALLY_COUPLED` verdict
  rests on this axis at all: the invariant
  `MERGES_DISTINCT_TARGET_CLASSES` ⇒ `ARTIFICIALLY_COUPLED` was **withdrawn on
  2026-09-16** (`docs/coupling_adjudication.md` §2.1) and is reported rather than
  enforced, and all eleven nodes reporting the signal are independently
  adjudicated on their own rationale. The re-derivation is worth doing because
  the *reported* axis should be sound, not because a verdict hangs on it.
  **(b) 34/24 is the catalog; the criterion's exposure is 29 rows and 21
  values**, because it reads only `execution_status = executable` rows. Three of
  the 24 values live entirely on rows it never sees. **The re-derivation changes
  no verdict**, and the typing is load-bearing in only one place — the barrier
  trio, one relabelling from flipping, exactly as DTR020 said.
- **DTR021/DTR022 — six nodes marked `executable` that are products or derived
  states.** Demoting them removes catalog ground for some coupling verdicts; the
  verdicts should not revert, because the node-dictionary axis separates them
  independently. Dependent on TI016.
- **TI015** — no relay has a catalog row at all, "**Recorded to stop a future
  round acting on the false premise.**" Relevant to any interface work.

### 4.3 Vocabulary reconciliation

Adopt the requested vocabulary as canonical — its two `WAIT_*` values usefully
split `UNRESOLVED` into "blocked on evidence we have arranged to get" versus
"blocked indefinitely" — and record a one-time mapping from `next-stage.md`'s set
and from `unresolved_mechanisms.tsv`'s `disposition`. Keep `ensemble_only` as an
orthogonal flag rather than folding it in.

**Done in U4b, and the mapping is not a bijection — which is the finding.**

| `next-stage.md:61` | canonical | note |
|---|---|---|
| `PROMOTE` | `PROMOTE` | — |
| `MERGE_WITH_EXISTING` | **`MERGE_WITH_EXISTING`** | **restored**, and **used by no Sept-11 candidate**. The requested five-value set dropped it, and there is no substitute: a node that duplicates a committed state in both the biological state it denotes and its compartment is not "retained in the catalog", it is already in the model under another name. A rubric needs the value for the case even when no candidate reaches it. *Revision 1 named `X_ECM_FN1_COL4` here; that disposition is withdrawn — see §4.1 and §5(0b)* |
| `RULE_VARIANT_ONLY` | `RULE_VARIANT_ONLY` | — |
| `UNRESOLVED` | `WAIT_FOR_EXPERIMENT` \| `RETAIN_CATALOG_ONLY` \| **`EVIDENCE_UNVERIFIED`** | splits three ways, not two |
| `REJECT` | `REJECT` | — |

| `unresolved_mechanisms.tsv` `disposition` | canonical |
|---|---|
| `catalog_only` | `RETAIN_CATALOG_ONLY` **only if §5(1)–(3) pass** — otherwise the earlier failure governs. DRUNR-004/005/007/008 all read `catalog_only` and four of the candidates carrying it had not cleared §5(1) |
| `ensemble_only` | orthogonal flag, retained as such |
| `requires_implementation_review`, `requires_calibration`, `requires_definition` | `WAIT_FOR_EXPERIMENT` |
| `external_only` | out of scope for node admission |

**One value added beyond both sets: `EVIDENCE_UNVERIFIED`.** Without it, a
candidate with no traceable primary source receives the label reserved for one
whose evidence was weighed and found sufficient at (1)–(3). That is not a
notational preference — it is how five of the fourteen came to hold
`RETAIN_CATALOG_ONLY`, and four of those five had never cleared step 1.

**And one column, not a sixth value: `formalism_verdict`** ∈ {`representable`,
`outside_formalism`, `not_assessed`}. §8's Q3 category — graded potentiation,
timing, dose- or context-dependent sign — is a property of the *model class*, not
of the evidence, so it is orthogonal to the ladder and applies to every row. See
§5.

---

## 5. Promotion framework

Node and edge promotion stay separate decisions.

> **Repaired by U4b, because it was insufficient for a closure task.** As
> originally written this section had four criteria and stated a disposition for
> **one** outcome — "failing (4) but passing (1)–(3)". It said nothing about
> failing (1) or (2), and it never asked whether the proposed node denotes a
> coherent state or duplicates one already committed. Those are not theoretical
> gaps: **seven of the fourteen Sept-11 candidate nodes were holding dispositions
> the gaps allowed, and five of the seven were too lenient.** (Those seven arise
> from **five §4.1 classification entries** — two different counts, kept apart
> here because §4.1 itself says so.) The repair adds two
> prior criteria, one disposition rule and one orthogonal column. It is a repair
> of this rubric, not a second one — every disposition in
> `…candidate-node-dispositions.tsv` is issued under the section as it now
> stands, and `docs/v05_u4b_candidate_node_closure.md` §2 records the derivation.

**Node admission — in this order:**

0. **Node coherence — and it fails two ways, which must not be merged.** Does the
   proposed node denote a *single coherent biological state, as defined*, in this
   system?
   - **(0-refuted)** Evidence positively establishes that the state, as defined,
     does not hold → `REJECT`, **scoped to that definition**; a differently-defined
     node is a different candidate and is not thereby rejected. This requires
     showing that the definition *logically entails* what the evidence falsifies.
   - **(0-insufficient)** The definition is *not established* — a named component
     has no supporting evidence either way, or the evidence read is silent on it →
     **`RETAIN_CATALOG_ONLY`**, with the definition defect recorded and the
     component named.

   *This split is itself a U4b repair, made under external review.* The first
   draft collapsed them and produced one `REJECT` that did not survive scrutiny:
   absence of transcript co-movement among selected enzymes falsifies a
   *co-regulated transcriptional programme*, which is not the same proposition as
   "no coherent functional glycosylation state exists", and one of the two
   references bearing on the definition was unread. **Refutation is a high bar and
   the burden is on the rejecting unit.** Nothing in U4b clears it.

0b. **Non-duplication — semantic state and compartment first, Boolean function
   last.** Is the node already realised by a committed node? This is satisfied
   only when the two agree on **the biological state they denote and the
   compartment they denote it in**, *and* the measurement sets are equivalent
   rather than merely overlapping. **Equality of the current effective Boolean
   function is never sufficient**, because that function is a property of the
   *proposed rule* — and where the proposed rule has been rejected, its function
   equality is evidence about the rejected rule and about nothing else.
   Failure is `MERGE_WITH_EXISTING`; **no Sept-11 candidate meets it.**

   *Also a U4b repair made under external review.* The first draft merged
   `X_ECM_FN1_COL4` into `S_TAZ_ECM` on function equality plus an overlapping
   feature list. The model's own dictionary refutes that: `S_TAZ_ECM` is
   "Stromal TAZ or WWTR1 ECM-remodeling state", `compartment = stroma`,
   `model_role = mechanical_regulator`, `measurement_proxies = "TAZ activity and
   collagen program"` — it does not name `FN1` or `COL4A1` at all, and the
   overlap was with the *scRNA pre-registration's* feature list, a different
   artifact for a different purpose. The candidate is `compartment =
   extracellular`, `role = matrix_state`, and its own note says it "complements
   stiffness/mechanics", i.e. it is proposed as the thing `S_TAZ_ECM` is *not*.
   Two biologically different states sharing a Boolean function is an alias to
   record, not an identity to merge on.

1. **Primary full-text verification** of every reference the promotion rests on,
   recorded in `primary-verification.tsv` (**not** `citation_verification.tsv`,
   which only resolves DOIs — §0.6). *As written in §0–§16 this excluded all 14
   Sept-11 candidates, and that was true of the **staging** state.* **It is no
   longer the state:** U4b verified seven of the nine `DRREF-*` references, and
   the 2026-09-18 blocked-source refresh read and registered the remaining two, so
   **all nine are now verified or reused**. The **four** candidates that still fail
   here fail for two different reasons — **one** on a miscitation
   (`E_ESR1_ACTIVITY`), and **three** on having named no reference at all.
   (`E_JAG1_NOTCH3` failed here for U4b, on access; Zhou 2021 is now read, so it
   passes (1) and fails at **(2)**. `E_SLEX_SURFACE` failed at **(2)** for U4b and
   now passes it too, failing at **(4)** — see the access rule below.) See
   `…candidate-node-dispositions.tsv`.
2. **A determinant that exists in the biology as studied**, not in a laboratory
   construct and not invented. This is what excludes PC6-b and TI005.

   **And the determinant must be a determinant of *the variable the node names*.**
   A node defined as an activity, localisation, cleavage or engagement state is
   not given a determinant by evidence that something changes its namesake's
   **mRNA or total protein**. `AGENTS.md` already forbids reading abundance as
   activity for the *node*; this says the same thing about the *edge into* it,
   which is the DRE009 failure mode arriving one step upstream and is easy to
   miss because the citation looks right. *Added in U4b under external review,
   which found it firing on two candidates at once:* `S_FOXO1` names **nuclear**
   FOXO1 and its determinants are measured as FOXO1 mRNA and total protein;
   `E_SOX17` names SOX17 **activity** and its determinant is a 1.6-fold protein
   abundance change. Both were first recorded as failing at (4); both fail here,
   which is earlier and is what the disposition must be read from.
   *(`S_FOXO1` **cleared** (2) on 2026-09-22, when Labied 2006 supplied a
   determinant of FOXO1 **localisation measured as localisation**; it now fails
   at (4) and reads `RETAIN_CATALOG_ONLY`. `E_SOX17` is unchanged. The rule is
   not relaxed by that — it is satisfied. See `docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md`.)*
3. **Compartment support**, and for a `not_RNA_assessable` state, an explicit
   statement of what could ever measure it.
4. **Measured Δ distinct Boolean functions > 0 *and* a named alias class
   broken** — as a tie-breaking screen among candidates that already pass 1–3,
   not as the primary criterion (§0.4). Report the **latent-space delta**
   alongside it.
5. **Exemption:** a repair whose effect is transient rather than partition-level
   is admissible at Δ = 0, with TI012 cited (§0.5). Without this the framework
   forbids every timing repair, including Gate 3a.

**Edge promotion — separately:** direction; causal vs associative support;
species and system; compartment; **activity versus abundance** (the DRE009 failure
mode, named in `AGENTS.md`); whether the rule needs AND/OR/graded semantics;
whether the Boolean abstraction overstates the evidence; and whether alternative
variants remain plausible — in which case it enters `rule_variants.tsv` as a
family, not the network as a fact.

**Failing (4) but passing (1)–(3) is `RETAIN_CATALOG_ONLY`, not `REJECT`.**
Catalog rows are the input to the next review; rejections are not.

**The disposition rule: the first criterion that fails governs.** This is the
piece that was missing, and its absence is precisely how §4.1 drifted — its rows
were assigned on the most *interesting* failure, which is almost always the
structural one, rather than on the first.

| first failing criterion | disposition |
|---|---|
| (0-refuted) definition falsified | `REJECT`, scoped to the definition |
| (0-insufficient) definition not established | `RETAIN_CATALOG_ONLY`, component named |
| (0b) non-duplication | `MERGE_WITH_EXISTING` |
| (1) primary verification | **`EVIDENCE_UNVERIFIED`** |
| (2) determinant | **`WAIT_FOR_EXPERIMENT` when the missing evidence can be obtained by a named experiment feasible within the current or planned ADOC programme; otherwise `RETAIN_CATALOG_ONLY`.** *Owner-ratified wording, 2026-09-18* |
| (3) compartment / measurability | `RETAIN_CATALOG_ONLY` |
| (4) Δ and alias | `RETAIN_CATALOG_ONLY` — as above, unchanged |
| several encodings remain defensible | `RULE_VARIANT_ONLY` — the existing consequence below, orthogonal to the ladder |

**The (2) discriminator is owner-ratified and is no longer an open decision.**
It was introduced in U4b and flagged `UNCONSULTED_DECISION`; the owner approved it
on 2026-09-18 in the wording above and asked that the ratification be recorded
rather than left unresolved. It operationalises §4.3's own gloss — "blocked on
evidence we have arranged to get" versus "blocked indefinitely" — because
*nameable* is too weak a test: almost any missing determinant can be named.
**`WAIT_FOR_EXPERIMENT` means this project could go and get it.** Its effect on the
Sept-11 set is to hold `E_SOX17`, `E_SLEX_SURFACE` and `E_ITGA2B1` at
`RETAIN_CATALOG_ONLY` rather than promoting them to `WAIT_FOR_EXPERIMENT`, i.e. it
makes the record **more** conservative; the ratified wording changes no
disposition, which was checked row by row. Each row records its own answer in the
`unblock_locus` column of `…candidate-node-dispositions.tsv`, and a guard enforces
the rule.

**An access blocker attaches to the criterion whose claim depends on the
inaccessible source — not automatically to (1).** *Corrected under external
review, which found this paragraph over-generalising past the table it describes.*

- If **node admission itself** rests on the source, it is a **(1)** failure →
  `EVIDENCE_UNVERIFIED`. `E_JAG1_NOTCH3` **was** here for U4b: Zhou 2021 is its only
  reference, so without it nothing could be said at claim level. *Zhou 2021 was read
  and registered on 2026-09-18, so the node now passes (1) and fails at (2) —
  `WAIT_FOR_EXPERIMENT`, `JUSTIFIED_SYSTEM_LIMITED`. The rule is unchanged; the
  example is spent.*
- If the node is **already established** by an accessible source and the
  inaccessible one is needed only for its **determinant**, it is a **(2)** failure
  → `RETAIN_CATALOG_ONLY` (the locus being external, not ADOC-runnable).
  `E_SLEX_SURFACE` **was** here for U4b: Yu 2018 establishes surface sLeX causally,
  and Ma 2023 was wanted for the IL1B → FUT3 input alone. *Ma 2023 was read on
  2026-09-18 and supplies that determinant, so the node passes (2) and now fails at
  (4), on measurement. Its disposition is unchanged at `RETAIN_CATALOG_ONLY`.*

**In no position is access failure negative evidence, and in no position does it
by itself yield `REJECT`.** A paper that could not be obtained says nothing about
the biology.

**`formalism_verdict`, orthogonal to the ladder and subordinate to it.**
*Corrected in U4b under external review, which found the first draft
self-contradictory:* it said the first failing criterion governs, and then said
`outside_formalism` makes the disposition `RETAIN_CATALOG_ONLY` — two rules that
give different answers for `S_TGFB_CONTEXT`, which fails at (1) and is also
biphasic. The total rule:

- **Earlier admission failures continue to govern.** A candidate that fails
  (0)–(3) takes that disposition, whatever its `formalism_verdict`.
  `S_TGFB_CONTEXT` is `EVIDENCE_UNVERIFIED` **and** carries `outside_formalism`,
  and both facts are load-bearing: the first says nothing has been weighed, the
  second says that weighing it would not be enough.
- **Only once (0)–(3) are satisfied** does `outside_formalism` — §8's **Q3**
  category, graded potentiation, timing, or dose- or context-dependent sign —
  **cap** the modelling disposition at `RETAIN_CATALOG_ONLY`.
- **It never produces a `REJECT`**, in either position, because the blocker is
  the model class rather than the biology.

This states for future candidates what TI011 said in prose and then flattened
into "REJECT THE NODE": its own reason was "not because the biology is weak but
because the model class cannot represent it". **U4b does not relabel TI011** —
`S_EPAC_RAP1` is not a Sept-11 candidate, its prose already carries the right
reason, and reopening a settled unit to change a label is the speculative
reopening this branch forbids.

**Node verdict and encoding verdict are recorded separately, always.** Rejecting
an encoding never rejects a node. **Seven** of the fourteen Sept-11 candidates
have a defensible node and a rejected encoding (six as U4b closed it;
`E_JAG1_NOTCH3` joined them on 2026-09-18); under a single column that outcome is
invisible, which is how "the staged form is rejected" and "the biology is
unsupported" came to wear the same label.

---

## 6. Component maps — where AND/OR is justified, and where MIN/MAX is wrong

### 6.1 Justified

- **`E_ITGAVB3_5`** — `ITGAV AND (ITGB3 OR ITGB5)`, i.e. the proposed
  `MIN(A, MAX(C, D))` shape. An obligate α subunit with two alternative β
  partners is real component biology; the audit measured `ITGAV` at
  −1.59 / −0.37 / −0.80, so the obligate subunit is the one that falls.
- **`E_GP130_STAT3`** — availability genuinely requires receptor and effector
  components, and the audit's *direction* vote uses `SOCS3` + `BCL3` while
  **excluding `STAT3` by R2**. Availability logic and direction logic use
  different gene sets for the same node. **Schema requirement the specification
  misses:** a `role` column (`availability_requirement` vs `direction_readout`),
  or the two will be conflated on first reuse.

  **But the requirement set must not be declared at node level, or it decides
  U4 in advance.** An earlier revision of this document wrote the requirement as
  `IL6ST AND LIFR AND STAT3`. U4 keeps `E_GP130_STAT3 = E_LIF or X_IL11` under
  evaluation as a rule family (GP130-b, `gate3_candidate_variants_2026-09-16.tsv`;
  TI002): the LIF route needs LIFR, the IL-11 route does not. Making LIFR
  obligatory at node level would make the IL-11 arm unavailable wherever LIFR is
  low — exactly the comparison U4 exists to make.

  (The node's label in
  `models/superset/adoc-literature-superset-v0.4.0/node_dictionary.tsv:22`,
  *"Epithelial LIFR or GP130 to STAT3 state"*, is **not** a good second argument
  and should not be used as one: LIF signals through a LIFR:gp130 heterodimer, so
  both are required on that route and the label's "or" is loose naming, not a
  receptor disjunction. The argument rests on the variant family.)

  **Rule:** node-level requirements carry only what is common to every admissible
  variant; anything variant-specific attaches to the variant. The component map
  needs a `requirement_set` keyed to a `variant_id` in `rule_variants.tsv`, and
  **"admissible variants" must be defined explicitly as the variant set declared
  there for the model under evaluation, evaluation-only families included.** That
  definition is load-bearing: the only *committed* v0.4 rule is
  `E_GP130_STAT3 = E_LIF` (`network.bnd:85-87`), so an intersection taken over
  committed rules alone has one member and re-imposes obligatory LIFR — the very
  outcome this rule exists to prevent. The safer alternative, if the intersection
  proves awkward, is to evaluate availability **per selected variant** rather
  than against a fixed node-level set.

  Two consequences to state rather than discover. `IL6ST` is ubiquitous in
  epithelium, so a node-level set of `IL6ST` + the `STAT3` effector will almost
  always evaluate `PRESENT`, and essentially all discriminating power moves to
  the LIF variant's `LIFR`. And the IL-11 route's receptor component `IL11RA` is
  named only in `context/references/adoc-maboss-model-specification.user-provided.md`
  and in deep-research context (DTR004 records that "Separate E_LIFR and
  E_IL11RA Boolean nodes are not immediately required — ACCEPT"); **no committed
  model, config table or scRNA feature list declares it**, and none of those
  sources states a requirement structure for the epithelial IL-11 route. By
  §6.2's general rule that variant is `undeclared` → `INDETERMINATE`, which is
  the correct outcome and must not be repaired by inventing the component.
- **`E_PC6` → `E_DAG1_CLEAVED`** — enzyme-and-substrate, a true AND in
  availability terms even though the functional state needs more.

### 6.2 Where MIN/MAX would be wrong

- **`E_MUC1_SLEX`** — ten glycosyltransferases are alternative and partly
  antagonistic enzymes, not components of a complex. MIN is dominated by the
  least-expressed; MAX is satisfied by any one. The audit's data settle it.
- **`S_DECIDUALIZED`** — `PRL AND IGFBP1 AND FOXO1 AND WNT4` is what the
  specification warns against, plus a second reason: R1 already removes `PRL` and
  `IGFBP1` from its direction vote **because they are other model nodes**, so a
  naive conjunction makes the node partly self-measuring.
- **`E_SECRETORY_STATE`**, **`E_ESTROGENIC_PROLIFERATION`**,
  **`S_FGF_MITOGENIC`** — programmes and pathway scores; same argument, and see
  §3.7 for why `S_FGF_MITOGENIC` should be pruned entirely.
- **`E_CD98_CD9`** — one node named for two different complexes (CD98 is
  `SLC3A2`+`SLC7A*`; CD9 is a tetraspanin). The requirement structure is
  undefined and `MIN(SLC3A2, CD9)` would invent one. Flag `requires_definition`.

**General rule:** a component group is admissible only when the requirement
structure is stated in a cited source. Otherwise `requirement_structure =
undeclared` and the RNA layer returns `INDETERMINATE`, which by §1.2 creates no
constraint. Safe default, and it costs nothing given §0.1.

### 6.3 The frozen combination table

Total over the four states, to be frozen **before** U6 codes anything. Both
operations are "first match wins" over a fixed precedence order, which makes each
one commutative, associative and idempotent by construction, so arbitrary nesting
— the `MIN(A, MAX(C, D))` shape of `E_ITGAVB3_5` — is well defined.

**Obligatory AND** (every component required). Precedence:

```
ABSENT_POWERED  >  NOT_ASSESSABLE  >  INDETERMINATE  >  PRESENT
```

- any `ABSENT_POWERED` → `ABSENT_POWERED`. An obligatory component established
  absent with power means the machinery cannot be complete, whatever is unknown
  about the rest.
- else any `NOT_ASSESSABLE` → `NOT_ASSESSABLE`. An obligatory component RNA can
  *never* assess means the node can never be called `PRESENT` by RNA. Note this
  is **one-sided**: `ABSENT_POWERED` stays reachable, because an `INDETERMINATE`
  component could still resolve absent later.
- else any `INDETERMINATE` → `INDETERMINATE`.
- else → `PRESENT`.

**Alternative OR** (any component sufficient). Precedence:

```
PRESENT  >  NOT_ASSESSABLE  >  INDETERMINATE  >  ABSENT_POWERED
```

- any `PRESENT` → `PRESENT`. One available route is enough.
- else any `NOT_ASSESSABLE` → `NOT_ASSESSABLE`. An alternative that can never be
  assessed might be available, so absence cannot be declared. One-sided again:
  `PRESENT` stays reachable through an `INDETERMINATE` arm.
- else any `INDETERMINATE` → `INDETERMINATE`.
- else (all `ABSENT_POWERED`) → `ABSENT_POWERED`.

**Three properties to record, so nobody "fixes" them later.**

1. **The two operators are not De Morgan duals.** A true duality would swap
   `NOT_ASSESSABLE` and `INDETERMINATE` as well; here `NOT_ASSESSABLE` outranks
   `INDETERMINATE` in *both*, because both are "cannot conclude" and
   `NOT_ASSESSABLE` is the permanent form. This is deliberate and is not a
   defect: the component schema has **no negation**, because "the machinery for X
   is absent" does not make anything else available, so there is no operation for
   a duality to hold over. Each operator is a semilattice; together they are not
   a lattice, and §1.2's earlier "lattice meet/join" phrasing was loose.
2. **`NOT_ASSESSABLE` is preserved, never downgraded to `INDETERMINATE`.** That
   is the whole point of carrying four states rather than three (§1.2):
   `INDETERMINATE` says better data could resolve this. `NOT_ASSESSABLE` on a
   *single* component says do not bother collecting RNA for that component — but
   on a **combined** node it means only that one of the two verdicts has become
   unreachable, not that the node is beyond RNA entirely. Do not read a combined
   `NOT_ASSESSABLE` as "stop measuring".
3. **Empty groups are a schema error, not an identity.** The AND identity is
   `PRESENT` and the OR identity is `ABSENT_POWERED`, so an empty group would
   silently assert availability or absence. An empty `requirement_group` must
   therefore **raise at map load**, as a schema-validation failure. Keep that
   distinct from `requirement_structure = undeclared`, which is a *valid* state
   meaning the biology was never established and which evaluates to
   `INDETERMINATE`. The two must not be identified: one is a broken table, the
   other is an honest gap.
4. **`provisional_corrected_layer_only` travels beside the enum, and never
   authorizes a clamp.** Settled here rather than deferred: the combinator is
   written once in U6, and retrofitting provenance into it later is how the flag
   gets lost.

   The rule:

   - the four-state enum is **unchanged**, and a provisional absence still maps
     to `ABSENT_POWERED` and still contributes to the combined state exactly as a
     confirmed one does;
   - `provisional_corrected_layer_only` is carried as **orthogonal provenance
     metadata** through the combination, never folded into the enum value;
   - **no provisional absence, direct or combined, may authorize a hard clamp.**

   This is not new policy. It is the gate-layer instantiation of the
   pre-registration's §3.1(3), which already binds: *"No structural conclusion may
   rest on a provisional absence"*, with such a change stated as **conditional on
   raw-matrix confirmation** rather than asserted. The clamp is the strongest
   structural consequence in the architecture, so it inherits that rule directly.

   The alternative — keeping provisional absences out of `ABSENT_POWERED` — is
   worse, and is rejected. It would map them to `INDETERMINATE`, discarding the
   fact that an absence was observed, contradicting §1.2's mapping table, and
   changing the *combined evidence state* for what is purely a provenance reason.
   Provenance problems get provenance fixes.

   **The flag propagates dually, and this is the part an implementer will get
   wrong** by propagating it the same way in both operators:

   - **AND**, result `ABSENT_POWERED`: any one absent component justifies the
     result, so the result is provisional **only if every absent component is
     provisional**. One confirmed absence makes the combined absence confirmed.
   - **OR**, result `ABSENT_POWERED`: every alternative must be absent for the
     result to hold, so each is load-bearing and the result is provisional **if
     any component is provisional**.

   Moot on today's data — there are no absences at all (§0.1) — which is exactly
   why it is cheap to fix now and expensive to fix after the first one arrives.

---

## 7. What the audit and the deep research jointly say

### 7.1 AC01 — the assignment, not a proposal

The current P1 (`node_support_finding.md:390-404` at `7ee303f`; `:300-315` at
`a028ef3`) is narrower and stronger than
the draft revision 1 quoted. It now rests on **`E_PAEP` vs `E_HBEGF` alone** —
"a **direct transcript**, not a proxy" — and states that "the weaker integrin and
glycosylation proxies are not needed to carry the conclusion." The identity
`E_PAEP = E_HBEGF = E_SECRETORY_STATE` is not defensible.

And it carries an explicit owner decision, which revision 1 of this plan violated:

> *What this does **not** license.* An earlier draft of this section proposed
> giving the divergent members "distinct variables with their determination
> recorded as open". **The owner rejected that, and rightly:** free Boolean
> variables replace a false equality with unconstrained biology, which is not a
> smaller error.

`node_support_deviations.md:248-257` repeats it and names the next step:
replacement rules are "to be **derived** — from literature together with this
audit — **in the mechanistic-integration work**".

**That is this document's assigned job. U3 did it, and the answer is negative —
but for a different and more useful reason than this section predicted.**

*Corrected by U3; `docs/v05_u3_ac01_no_derivable_rule.md` is the record.* The
list below said of `E_HBEGF` that "the backlog offers nothing". **That is false.**
`REF-059` (Jin 2025), held as `PDF-028` with `full_text_inspected = yes`, is
about epithelial HB-EGF and hCG, and `IN_HCG` is declared in v0.4 and read by no
rule. The candidate rule `E_HBEGF = E_SECRETORY_STATE or IN_HCG` is
**structurally effective**: 35 → 36 distinct Boolean functions, AC01 9 → 7,
computed exhaustively, at no new node.

*Corrected after external review.* An earlier revision scored it against §5's
numbered **node-admission** criteria. That is the wrong rubric — §5 says node and
edge promotion are separate decisions, and this candidate is an **edge**
(`IN_HCG → E_HBEGF`) on an existing node. Judged against §5's **edge-promotion**
criteria it fails **seven of eight**: direction, causal-vs-associative support,
species and system, compartment for the arm it acts in, activity-vs-abundance,
whether the rule needs AND/OR/graded semantics, and whether the Boolean
abstraction overstates the evidence. The eighth,
competing variants remaining plausible, fixes the disposition: §5's own
consequence is `rule_variants.tsv` **as a family, not the network as a fact**.
The Δ result is retained as a structural **diagnostic**, which is all §0.4 ever
let it be.

§5(1) is **not satisfied** either: the ledger §5 names holds seven rows and
REF-059 is not among them. `pdf_manifest.tsv` records `PDF-028` as full-text
inspected and registered, but that is not the claim-level ledger, and treating
the two as interchangeable is the substitution §0.6 exists to prevent.

The substantive reasons for rejection are unchanged. The hCG → epithelial HB-EGF induction is
the one link the reference's own registered record says was "NEVER tested end to
end — assembled from separate sufficiency experiments"; the siRNA arms license
necessity of HB-EGF for a *stromal increment*, not hCG sufficiency for HB-EGF;
both compartments are immortalised lines; and "there is no adhesion, attachment
or embryo endpoint, so nothing here constrains the epithelial attachment arm" —
which is the only arm `E_HBEGF` sits in. Its own Fig 6 puts HB-EGF at maximum at
**LH+2 and near baseline by LH+7**, so an embryo-supplied inducer would be
asserted in a window where the same paper measures the target at baseline; and
`REF-069` is a registered, unresolved contradiction in the same hormonal
context. `LIT-HBEGF-001` already says the Boolean direction here "should remain
supportive".

**This is the §0.4 hazard in its purest form** — a candidate that passes a
conjunctive Δ-plus-alias test and must still be excluded by the prose criteria.
Keep the ordering.

The other two entries stand as written:

- `E_ITGAVB3_5` — TI010 independently concludes it needs a determinant outside
  the secretory program, and records that none is available locally. Convergence
  on the *problem*, not on a solution. U3 adds that its committed rule is
  **degenerate**: `E_LIF or E_HBEGF or E_SECRETORY_STATE` reduces to
  `E_SECRETORY_STATE` exactly.
- `E_MUC1_SLEX` — the backlog's candidate (`E_GLYCOSYLATION_PROGRAM`) does **not
  displace it**: the audit's own data show the ten glycosyltransferases do not move
  as a programme, so the proposed *replacement* fails. *Narrowed in U4b: an earlier
  revision wrote "refuted", and that is more than the data support — the evidence
  does not establish the proposed co-regulated programme, and it does not
  establish the absence of a coherent functional glycosylation state. The candidate
  is `DEFINITION_INSUFFICIENT`, not refuted.*

**The owner decision is also independently correct on identifiability grounds,
which is worth recording because it makes the decision robust rather than merely
authoritative.** In MaBoSS a node with no incoming rule is `logic = <self>` —
which `v05_plan_review.md:324-328` describes as "a **Bernoulli coin flipped once
at t = 0 from a hand-typed istate**. They are not mechanisms, not dynamics, and
not measurable." So free variables here would be *three more relays*. Worse,
`network.bnd:214` makes `E_ITGAVB3_5` a required conjunct of
`X_ADHESION_ROUTE_SPP1`, feeding `OUT_MATERNAL_ADHESION_COMPETENCE` and
`OUT_STABLE_ADHESION` — placing a new ungrounded hand-set Bernoulli **directly on
the adhesion prediction**, which Gate 3b criterion (i)
(`v05_plan_review.md:1160-1164`) forbids outright. And
`identifiability_analysis.md:70-75, 252` records five latent variables giving
2^5 = 32 configurations of which every proposed arm reaches 8; each addition
doubles the space, and `E_HBEGF` / `E_MUC1_SLEX` are phenotype-inert so they
cannot add an observation class at all.

**U3's admissible outputs are therefore:** a derived, literature-backed
replacement rule; or a recorded finding that none can be derived, with the alias
left in place and flagged. Three new free variables is not among them.

### 7.2 AC04 — two artifacts pointing at one node

The audit finds `E_LIF`, `E_GP130_STAT3`, `E_CD98_CD9` all `divergent`, verdict
`rule_challenged`. P2 is explicit that this "says '**the current activation rule
is challenged**', not 'split these nodes', and it licenses no split", and that
the failure may lie "in the rule's inputs, its logic, or in the assumption that
transcript tracks the state at all".

***Corrected at `252461b` — this was a "precise null" and is not one.*** Earlier
revisions of this section, following the finding as it then read, called the
result a **precise null** on which "the cocktail does not raise `E_LIF`". The
repository withdrew both. What the finding says at `7ee303f`
(`node_support_finding.md:80-90`, P2 at `:411-423`) is narrower:

- the 12-of-15 non-overlapping comparisons and the median |log2| of 0.35 **still
  stand**, and mean the differences are **resolvable but below the pre-registered
  two-fold convention** — *not* zero;
- **`E_LIF` does rise** in a separated way in two donors, **+0.59 and +0.46
  log2**, under the two-fold bar the design declared material in advance;
- the verdict is therefore that nothing moves *by the registered margin*, not
  that nothing moves. The finding calls it a **weak rule challenge and not a v0.5
  driver on its own**.

Do not restore the stronger wording, and do not carry "precise null" into any
v0.5 artifact.

TI001/TI002 independently say these nodes have inputs the cocktail does not
supply. **Carry §0.7's correction here:** `AC04` was claimed under §3.1(4)'s
exemption and does not meet it, so the §3.2 condition-entanglement caveat binds
it with full force — a flat CNT-versus-HT result on this layer is the shape of
result a condition-entangled correction could itself produce. That caveat is
**undischarged for `AC04`**: the raw-UMI re-derivation of `252461b` is scoped
`resolved_for_PAEP_HBEGF_only` (§0.8(a)) and re-derived nothing of `AC04`'s. So
hold `AC04` more loosely than `AC01` — for two reasons now, the exemption it does
not meet and the entanglement question `AC01` has settled and it has not.
Revision 1 called this "the same finding reached from two directions" and
made it the v0.5 headline. **That overstated it:** the audit measures a transcript
programme and the TI rows concern rule inputs; two artifacts pointing at the same
node is weaker than one finding. Treat it as convergent motivation for an
**evaluation-only rule family** (§4.1), which is also what TI002 asks for.

### 7.3 AC03, AC02 — nothing moves

AC03: the audit delivered the compartment-resolved PGR readout
`coupling_adjudication.tsv` asked for and the answer is *not yet* — `E_PGR`
`inconsistent`, `S_PGR` `divergent` on a weak null (4 of 6 comparisons overlap).
`inconsistent` is "not evidence for or against the alias", so there is no
`concordant` member to pair with a `divergent` one. `UNIDENTIFIED` stands. TI005
is withdrawn, TI017 is gated. **v0.5 must not upgrade AC03** — that would be
reading the rule backwards from the result, which the audit declined to do.

AC02: five `inconsistent` members, the response reversing sign between donors
(`S_IGFBP1` −3.87 in SZ09, +4.49 in SZ10). The pre-recorded falsification target
was an `S_PRL` / `S_IGFBP1` *divergence*; there is none. The falsifier that stands
is OM-016, an ELISA **timing** result, so U2 was to proceed on the protein
evidence and the transient, not on RNA. **That is now blocked** — the transient
cannot distinguish `S_PRL` from `S_IGFBP1`, which are exchangeable by
construction, and the ELISA ordering is confounded by an 83× magnitude gap and a
2× detection-limit gap on unpaired series. See `docs/v05_u2_gate3a_blocked.md`.

---

## 8. Topology, kinetics, and a third category

**Q1 — structural, no rate layer needed:** the AC04 rule-input variants; AC01's
identity *if* a rule can be derived.

**Q2 — needs rates or a time axis:** OM-016 ordering — and note TI012's finding
that it "lives only in the transient" and "no fixed-point partition can test it",
so U2's deliverable was to be a **simulated transient tested for robustness
across seeds, trajectory counts, initial conditions and admissible variants**,
per `v05_plan_review.md:1115-1122`, declaring a relative rate only if no
admissible variant reproduces the ordering.

**That deliverable is unreachable and U2 is blocked.** `S_PRL` and `S_IGFBP1`
have one Boolean function, one initial state and no declared rate, so they are
exchangeable and their onset distributions are identical at every horizon and
every seed — a robustness sweep over seeds and trajectory counts has its answer
fixed by construction. And the fallback the sentence offers, "declaring a
relative rate", is the option `prl_igfbp1_temporal_axis.md` §6 rejects outright
as fitting a rate to an assay artifact. `docs/v05_u2_gate3a_blocked.md` records
it; `tests/unit/test_v05_gate3a_guards.py` holds it across both supersets. Also: AC04's flat result at one timepoint
(the finding records this as a sampling-time limitation; note that
`inconclusive_sampling_time` appears only in the pre-registration's §7
enumeration — **no code path emits it and no row of
`node_rna_interpretability.tsv` carries it**, per `a028ef3` defect 4, so it is a
vocabulary item and not a recorded classification), and any claim about which
AC01 member changes
first.

**Q3 — outside the Boolean formalism:** the EPAC/RAP1 graded potentiation (not a
missing rate — potentiation is inexpressible in a rate-free Boolean model);
morphodynamics, permanently out of scope; any graded expression → activity
mapping.

**On `OUT_STABLE_ADHESION`.** Revision 1 suggested possibly "stop reporting it as
a fraction". **That does not follow and would make things worse.** Gate 3b(ii)
(`v05_plan_review.md:1165-1167`) already states the right criterion: the converged
value must "**arise from modelled biology** rather than arithmetic on arbitrary
typed constants". That is about *provenance*, satisfiable without the number
matching 9/19 — and suppressing the endpoint would make the criterion
unevaluable. The correct framing is **replace the constants' provenance, report
the fraction with its provenance**. Re-tuning 0.70/0.40 into [0.27, 0.68] remains
forbidden, and `v05_plan_review.md:1186-1199` already bars scoring on it: the
magnitude disagreement "is the DIAGNOSTIC that motivates the repair, **never the
thing the repair is scored on**". All of which is gated anyway by §0.3.

---

## 9. Bulk integration strategy

**Deconvolution is avoided only if the separation is physical.** If the layers are
separated as chip outlets the claim holds; if after dissociation,
cross-contamination returns and the C2 compartment-specificity control becomes
mandatory for bulk too. Verify before designing around it.

**Bulk's value is the axis scRNA structurally cannot supply.** The three largest
open questions — OM-016's ordering, AC04's sampling-time limitation, and any
ordering among AC01 members — are all temporal, and none is answerable by more
cells. Compartment-resolved bulk at ≥ 2 timepoints with a dropout arm addresses
them, but **not all to the same standard**, and OM-016 is the exception that
matters.

**OM-016 is a secreted-protein observation and bulk RNA cannot settle it.**
`config/observation_model_map.tsv` OM-016 draws on
`input_tables/adoc_secreted_proteins.tsv`, analytes `IGFBP-1;PRL`, outlet
`bottom` — an ELISA on secreted protein. Transcription, translation and secretion
have different and unmeasured lags per protein, so a transcript ordering is not
a secretion ordering. `AGENTS.md` is binding here: *"Expression, protein
abundance, and secretion are not node activity, interaction strength, transition
rate, or causal influence."*

What bulk can therefore do for OM-016 is test whether the **transcriptional**
mechanism and its temporal ordering are **compatible with** the observed
secretion ordering — a falsifier, not a confirmation. A transcript ordering that
contradicts IGFBP-1-before-PRL is evidence against a **transcriptional-onset**
reading of the `S_IGFBP1`/`S_PRL` ordering — conditional on bulk's own timepoint
and compartment resolution, and on OM-016's recorded unpaired-column ceiling. It
does not touch the ELISA constraint itself, and it cannot on its own reject a
model whose nodes are read as secreted-protein states with lags. A transcript
ordering that agrees with the ELISA establishes nothing, since only protein
measurement can. U2's deliverable was to be a **simulated
transient tested against the ELISA**, with bulk as a compatibility check on the
mechanism — never as a substitute for the protein-level ground truth. **With U2
blocked, this paragraph describes what bulk would be for, not work now in
progress**: the transient cannot separate the two nodes as they stand, so there
is nothing yet for bulk to be a compatibility check on.

**Bulk is the plausible source of the first powered absences**, since dropout and
the decontX correction both fall away. Stated as an expectation, not a result:
`node_support_preregistration.md:246-248` derives `E_min` for scRNA specifically
and **nothing in the repository bounds bulk power**. That derivation is itself a
prerequisite for the claim.

Carried unchanged: per-donor first, never pooled (already binding via
`preprocessing_contract.yaml` and `personalization.yaml: independent_unit:
donor`); matched bulk and scRNA that disagree are flagged and downgraded, never
averaged; and bulk must be **pre-registered** the way the scRNA audit was, with
thresholds and evidence role fixed before target inspection.

---

## 10. Contextual RNA-gating design

- The immutable `.bnd` describes mechanism. Nothing RNA-derived, donor-specific
  or condition-specific enters it. The U7 mutation interface is the sole
  exception and is uniform across donors and conditions by construction.
- The gate layer writes `.cfg` `$`-parameter settings only, against that
  interface, to a v0.5 output directory. It never writes a `.bnd`.
- `INDETERMINATE` and `NOT_ASSESSABLE` emit nothing — not a permissive gate, not
  a null row. Record the computed-but-not-applied state in `gate_computed`.
- `PRESENT` emits nothing. Presence never forces ON and never modifies a rate.
- `ABSENT_POWERED` emits a clamp only where all four conditions hold, **the
  evidence does not carry `provisional_corrected_layer_only`** (§6.3(4)), and the
  §0.2(e) call-path question has been resolved. In v0.5 this path is exercised by
  synthetic fixtures only.
- Protein-persistence uncertainty lives in explicit bounding scenarios, never
  averaged into one number.

---

## 11. Persistence-sensitive states

From the `cannot_inform_functional_state` set intersected with phenotype reach:
**`E_GP130_STAT3`** (phospho-state; the audit flags this exact risk against its
own P2), **`E_ITGAVB3_5`** (surface receptor on the adhesion path),
**`E_DAG1_FULL`** (a cleavage product persists independently of the enzyme —
Heng 2015 is that dissociation), **`S_TAZ_ECM`** (nuclear localisation plus
deposited ECM), **`E_PODXL`**, **`E_MUC1_BARRIER`**.

*Correction to revision 1:* `E_DAG1_CLEAVED` and `E_CDH1_APICAL` were listed and
should not have been — neither appears in `node_rna_interpretability.tsv` at all;
both are among the 32 `not_RNA_assessable` nodes, so they cannot be drawn from a
set they are not in.

**Not worth a VOI analysis:** the seven phenotype-inert nodes (`E_IHH`,
`S_NR2F2`, `S_SPP1`, `E_HBEGF`, `E_MUC1_SLEX`, `E_SPP1_EXPR`, `E_CD98_CD9`) —
clamping any changes no `OUT_` node across all 2^19 = 524,288 enumerated states,
so the question cannot reach a prediction. Add `S_FGF_MITOGENIC` for the separate
TI019 reason (§3.7). Apply this pruning before any half-life is looked up.

**Do not build a universal protein half-life layer.** Agreed, and doubly so given
§0.1.

---

## 12. Required tests and provenance controls

The 17 tests in the originating specification are sound and should all be kept.
Because that numbering has no anchor in the repository, the additions below are
stated self-containedly rather than by number.

**One of them needs its comparand pinned, or it becomes unsatisfiable at U7.**
The specification's "with RNA integration disabled, the model reproduces the
corresponding unconditioned model exactly" is two different invariants depending
on what it is compared against, and only one of them can be textual:

- **v0.5 RNA-disabled vs v0.5 unconditioned — byte-identical `.cfg`.** This is
  the stronger form and it stays valid *after* U7: with no gate rows the
  generator emits no `$Low_*`/`$High_*` *settings*, and the WT declarations are
  present in both sides of the comparison, so the two files are textually equal.
  Keep this one as written.
- **v0.5 (WT) vs v0.4 — trajectory equivalence only, never byte-identity.** After
  U7 every v0.5 cfg necessarily carries `$nb_mutable` and the `$Low_*`/`$High_*`
  pairs (§0.2(f)) and v0.4 carries none, so textual identity is impossible *by
  construction*. This comparison is T-B's job and T-B already states it
  correctly. An earlier revision of this section demanded byte-identity here,
  which would have been unsatisfiable the moment U7 landed.

Before U7, byte-identity against v0.4 is still a legitimate invariant for cfg
generation and worth asserting in U1; it is retired at U7 and replaced by T-B,
not weakened in general.

- **T-A. cfg-only.** The RNA layer writes `.cfg` `$`-parameter settings only;
  assert no `.bnd` is written per donor or condition.
- **T-B. Mutation-interface inertness.** With every `$Low_*`/`$High_*` at **0**
  (WT), the v0.5 model reproduces v0.4 trajectories for every committed condition
  at the same seed and sample count. This is what makes U7 a non-claim rather
  than a silent rate layer; it must exist before U7 merges.
- **T-B2. Clamp behaviour — two invariants, separate from T-B.** T-B only shows
  the interface is inert when unused. It says nothing about whether the clamp
  *works*, and the failure mode is silent (§0.2(f)): a one-sided `rate_up`
  suppression leaves a node that starts ON frozen ON. So, per gateable node, with
  `$Low_X = 1, $High_X = 0`:
  1. **starting OFF + clamp → remains OFF** for the whole trajectory, including
     under input conditions whose logic would otherwise drive it ON;
  2. **starting ON + clamp → becomes OFF and never reactivates** — the case the
     wrong expression passes and the right one fails to break. (Precisely: the
     one-sided form holds the node ON only while its logic stays TRUE; if inputs
     later drive the logic FALSE it turns OFF and cannot return. Still not a hard
     OFF, but "frozen ON forever" would overstate it.)
  Invariant 2 must be asserted with `istate = TRUE` *and* a logic-TRUE input
  condition, or it tests nothing. A third, cheap: with two nodes clamped
  simultaneously, both invariants still hold (this is what `$nb_mutable` is
  for). A fourth, and the one most likely to be skipped: **assert that
  `$nb_mutable`, `$Low_*` and `$High_*` are present in the WT cfg**, or T-B
  errors on a missing symbol instead of testing inertness.
- **T-C. Import boundary.** The gate module must not import
  `dt_adoc.simulation`, `.concordance`, `.calibration`, `.scoring` or
  `.perturbations` — mirroring pre-registration §10.1, which already has such a
  test to copy.
- **T-D. Total combinator.** The component combinator is a total function on the
  4-element evidence enum, proven by exhaustive enumeration over 4^k, and
  contains no arithmetic on evidence states.
- **T-E. No silent aliasing.** A `measurement_features` symbol absent from the
  source object is recorded as `feature_absent`. The `CTGF`/`CYR61` case is an
  **owner decision to make in U6** (§3.5), not a behaviour to freeze in a test
  before it is taken — the test encodes whatever is decided.
- **T-E2. Provisional absences never clamp.** A gate row whose evidence carries
  `provisional_corrected_layer_only`, directly or after combination, emits no
  clamp — and the flag survives combination under the dual propagation rule in
  §6.3(4). Assert both halves: that the flag is present on the combined result
  where it should be, and that the clamp is withheld. Exercised by synthetic
  fixtures, since no absence exists.
- **T-F. Blindness.** `E_KLF12_HIGH` (`not_blind = true`) cannot enter any
  construction-role mapping.
- **T-G. Frozen-audit pinning — two tiers, and the reason each artifact is in
  the tier it is in.** *Corrected at `5a55cf1`.* Earlier revisions said "audit
  artifacts are hash-pinned at `91f79ed`; the test fails if a digest changes".
  Written that way the test **fails today**, because two of the five artifacts
  moved after the evidence root for schema and provenance reasons (§0.8(d)).
  There are two wrong ways to make it pass — re-pinning everything to the current
  tip, which discards the evidence root, and reverting the two files, which
  reinstates a defect — and one right way, which is to pin each artifact where it
  legitimately belongs **and record why**:

  **Tier 1 — pinned at `91f79ed`, the frozen evidence root.** Byte-identical
  there and at `5a55cf1`; any change is a test failure and an evidence revision:

  - `docs/scrna/node_support_evidence.tsv`
  - `docs/scrna/node_rna_interpretability.tsv`
  - `docs/scrna/node_support_preregistration.md` (also still byte-identical to
    `491b337`, its registration commit — assert both)
  - `config/scrna_observation_map.tsv`

  **Tier 2 — pinned at `7ee303f`, with a recorded post-root reason.** Each entry
  carries the commit that moved it and the reason, and the test asserts the digest
  *and* that a reason is recorded:

  - `docs/scrna/node_support_findings.json` — `252461b` (additive
    `decision_provenance`; strict JSON, `NaN` → `null`; `c2_evaluated`),
    `9a5c52b` (`raw_layer_sensitivity` binding), `14b143f` (`c1_evaluated`;
    not-evaluated semantics on the five non-primary myofibroblast units)
  - `docs/scrna/node_support_qc.tsv` — `252461b`, `14b143f` (same two reasons)
  - `docs/scrna/node_support_raw_sensitivity.json` — created at `252461b`,
    bound to its sources at `9a5c52b`, digest-verified at `7ee303f`; it did not
    exist at `91f79ed` and can never be pinned there

  **The invariant that makes Tier 2 safe, and which T-G must assert directly
  rather than infer from a digest.** A Tier-2 artifact may move for schema or
  provenance reasons; it may not move a result. So T-G additionally asserts,
  against `91f79ed`:

  1. the `node_support` block of `node_support_findings.json` is **unchanged**,
     and recounting it gives **43 `robustly_detected`, 11 `sparse_or_low`, 0
     `not_detected_with_power`** over 27 nodes × 2 arms;
  2. all four `class_verdict` values and every member verdict are **unchanged**;
  3. `label_counts`, `unit_cell_counts`, `absent_features`, `empty_units`,
     `units_written`, `provenance` and `layer_caveat` are **unchanged**;
  4. every **primary** unit row in `node_support_qc.tsv` is unchanged, and the
     only differing rows are the five non-primary myofibroblast ones.

  A Tier-2 digest change that also breaks (1)–(4) is an evidence revision and must
  fail. Moving an artifact from Tier 2 to Tier 1, or deleting a recorded reason to
  quiet the test, is the "move the rule rather than the code" failure mode §13.5
  names, and is forbidden.
- **T-H. v0.4 immutability**, building on `test_manifests.py` and
  `test_topology_parity.py`.
- **T-I. Compartment coupling — directional, not isolation.** *Correction to
  revision 1, which asserted "cross-compartment isolation with one exception" and
  would have failed on the frozen model.* v0.4 has **one** epithelium → stroma
  edge (`E_IHH → S_NR2F2`, `network.bnd:154`) and **several** stroma → epithelium
  ones: `network.bnd:90` (`E_ESTROGENIC_PROLIFERATION = IN_E2 and
  S_FGF_MITOGENIC and not S_HAND2`) and `:198` (`X_SPP1_LUMEN_FREE =
  (E_SPP1_EXPR or S_SPP1) and …`, feeding `E_RECEPTIVE_SURFACE` at `:142`). State
  the invariant directionally and enumerate both sets explicitly.
- **T-J. Undeclared structure is inert.** A node with `requirement_structure =
  undeclared` yields `INDETERMINATE` and therefore no constraint.
- **T-K. Line endings.** v0.4 tables are CRLF, the staged bundle LF, no
  `.gitattributes` (`next-stage.md:156-157`). Merging staged rows will otherwise
  produce whole-file diffs that hide the real change from every reviewer. Settle
  in U1.

---

## 13. Scientific risks and circularity traps

1. **Construction → validation laundering.** The scRNA object is the same study's
   cells; evidence role is `construction` / `same_dataset_internal`. Using the
   audit to write a rule and later citing concordance with the same object as
   support is circular.
2. **Retro-fitting the Stage-3 ranking.** See §14.
3. **Reading the rule backwards from the result.** The audit refused this for
   AC03. The `E_PGR`/`S_PGR` asymmetry is suggestive; that is not the bar.
4. **`unclassified_by_section_5_4`.** Introduced after extraction; "licenses
   nothing" and is "disqualified from supporting any structural claim". Treating
   it as a verdict compromises the pre-registration retroactively. Note this is
   now documented in `node_support_deviations.md` D2 rather than being an open
   owner decision.
5. **Moving the rule rather than the code.** The likeliest instance is relaxing
   `forbid_missing_as_clamp` or `require_constitutive_evidence` so an RNA absence
   can clamp — but see §0.2(e): verify the call path first, because the collision
   may not exist and an adjudication would then be premature.
6. **Δ gaming.** TI005 passes a conjunctive Δ test on an invented latent
   variable; hence the reordering in §5.
7. **U3 and U8 rest on an interpretive call, not a measurement.** `AC01`'s
   verdict — and with it U3's whole mandate and U8's "mandatory" — falls if D1
   is wrong (§0.7). D1 looks sound and is argued from pre-registered text, but a
   v0.5 that presents `AC01` as raw data rather than as a verdict downstream of a
   post-extraction reading has overstated its own foundation.
8. **`AC04` is condition-entanglement-bound**, not exempt (§0.7). A flat
   CNT-versus-HT null on the decontX-corrected layer is the shape of result a
   condition-entangled correction can itself produce.
9. **Node-count creep under a parsimony banner.** The backlog holds 14 candidate
   nodes. The measured evidence supports **zero** new nodes and two
   **evaluation-only** rule-variant families. A v0.5 landing more than that has
   stopped being parsimonious whatever its introduction says.
10. **decontX condition-entanglement applies to presence too**; the correction is
   cluster-dependent and the clusters are near-deterministic in condition.
   *Partly discharged at `252461b`, and only partly:* P1's two load-bearing
   genes, `PAEP` and `HBEGF`, were re-derived on raw UMIs and the divergence
   reproduces, so the artifact records
   `condition_entanglement_status = resolved_for_PAEP_HBEGF_only` (§0.8(a)).
   **Every other magnitude in the audit still carries the caveat undischarged**,
   `AC04`'s included — and the earlier reassurance that `AC01` survives it by
   argument has been withdrawn as never established. Cite the measurement, never
   the argument, and never widen its scope past the two genes.
11. **Three donors, no across-donor inferential statistic.** None was computed and
   none should be.
12. **The two `E_PAEP` measurements are not independent.** scRNA +3.31 log2 and
    the ELISA's 9.5×–57.6× are two measurements of one claim on one study.
13. **The `E_PAEP` band is unregistered** (implicit window 25,470–178,073 pg/mL)
    and blocks even the zero-cost E2-only observation.
14. **Matched-unit caveat.** `v05_plan_review.md:282-290` records that fibres,
    observation classes, information statuses and panel counts are
    matched-unit-conditional and "are NOT claims about what the current data
    identify". `identifiability_analysis.md:20-22` exempts "the structural half,
    which never depended on pairing: **the 59 named nodes, the 35 native Boolean
    functions**, and the fact that the model represents more mechanism than any
    of this could separate." Note what that does **not** cover: the exemption
    names 59 and 35 only. **`P_design` = 19 is a design-equivalence count, it
    depends on which arms exist, and it is therefore inside the caveat, not
    outside it.** Any v0.5 statement resting on 19 — including the 8-of-32
    observation-class figures used in §7.1 — carries the matched-unit caveat and
    must be reported with it. U5's rerun must carry it onto every number.

---

## 14. Rerunning Stage-3 against v0.5

**This is mandatory, not optional — conditional on D1 (§0.7).**
`node_support_deviations.md:258-263`:
"`dropout_e2` **must** be reranked, and this audit does not predict the outcome …
a rerank against an adopted v0.5 is mandatory. Whether `dropout_e2` remains the
best choice is an output of the new model, not a conclusion of this audit."

*Correction to revision 1, which specified the wrong machinery.*
`config/candidate_score.yaml` is **not** used by Stage-3: nothing in
`src/dt_adoc/experiments/` reads it, its only references are requirement P3-007
(status `pending`) and a test asserting the YAML parses, and it scores phenotypes
that do not exist in `network.bnd` (`OUT_EPITHELIAL_VIABLE`,
`OUT_BARRIER_DAMAGED`, …) while omitting `OUT_EPITHELIAL_RECEPTIVE`. It is a
Phase-3 drug-candidate scorer for a model that was never built. **Drop it from
the protocol.**

Stage-3's actual criterion (`stage3_experiment_selection.md:340-341`): "**The
ranking criterion is a readout tier** … that tier is computed from
`config/observation_model_map.tsv` alone." Note also that every row of
`scrna_observation_map.tsv` is `reported_only`, `provisional` or `rejected` —
none active — so no scRNA finding promotes a readout tier by itself.

Protocol:

1. Touch no v0.4 artifact; write to a v0.5 output directory.
2. Re-run the same code against the v0.5 model with the **same readout-tier
   computation from `observation_model_map.tsv`**. Any change to the observation
   map is a separate change with its own justification, or the comparison
   confounds structure with scoring.
3. Report the frozen v0.4 ranking (`docs/experiments/stage3_experiment_design.tsv`),
   the v0.5 ranking, and the per-arm delta.
4. The 112-arm comparator is in `docs/design_alias_note.md`, which **is on
   `main`** — an adversarial review of this plan claimed it was only on the
   unmerged `feat/design-alias-figure` branch; that was checked and is wrong.
   What does hold is `stage3_experiment_selection.md:66-68` and `:684-687`: it
   "reached the same place from **a different computation**", ranking minus-E2
   best of 112 arms at +3 against minus-cAMP's +2, and Stage-3 "did not reuse"
   that computation. So the comparator is available, and reusing it in a rerank
   is a deliberate methodological change that needs stating — not a free
   cross-check.
5. State whether `dropout_e2` still ranks first. It may not: its value came from
   `E_SECRETORY_STATE = IN_E2 and E_PGR` carrying the whole epithelial secretory
   programme in one variable.
6. **The frozen result is historical evidence and is never rewritten.** If
   `dropout_e2` loses, record that; it remains correct *given v0.4*. The inverse
   trap is worse: using a v0.5 rerank to retro-justify the frozen choice.
7. Prerequisite either way: an `E_PAEP` interpretation rule. **Met** — the
   owner adopted the three-band ordinal rule on 2026-09-17
   (`stage3_experiment_selection.md` §9.1); only `OM-001`'s `claim_ceiling`
   cross-reference to it remains (`experiment_candidate_review_2026-09-22.md` M2).

---

## 15. Worktree, session and review sequence

**This branch already exists. Do not recreate it.** Earlier revisions of this
section instructed a future agent to
`git worktree add … -b feat/mechanistic-v05 91f79ed`; following that now would
re-root the implementation on the pre-fix code and discard the correctness merge.
What follows is the provenance record.

1. **Evidence root: `91f79ed`** — `feat/scrna-node-support` frozen and clean at
   that commit. Every number, verdict and QC call in this document is read from
   that state. T-G pins **four** artifacts there and **three** at `7ee303f` with
   a recorded post-root reason; the base-state section says which and why, and
   §12 (T-G) is the specification. *Earlier revisions of this item said "T-G pins
   the five numeric artifacts to it", which is no longer true and was the
   instruction most likely to be repaired by weakening the pin.*
2. **Branch created** from `91f79ed` as `feat/mechanistic-v05`, in
   `../DT_ADOC_wt/mechanistic-v05`. Code base then advanced to `a028ef3` by merge
   at `fbf5468`, for the `node_support.py` correctness fixes.
3. **Code base now `7ee303f`, merged at `5a55cf1`.** `feat/scrna-node-support`
   continued past `a028ef3` through `252461b`, `9a5c52b`, `c551d9f`, `14b143f`
   and `7ee303f`; `5a55cf1` merges that tip into this branch. §0.8 records what
   those five commits change for this plan. **`a028ef3` is no longer the code
   base and no instruction here should be followed as though it were.**
4. Commit sequence on this branch, in order: `2d6fc30` the plan — `10139e6` its
   reconciliation with `a028ef3` — `fbf5468` the merge — `82a8a64` five verified
   reviewer corrections — `57f9355` three consistency fixes — `5a55cf1` the merge
   of `7ee303f` — **`ee2903a` the reconciliation of this plan with `7ee303f`**
   (documentation only) — **`d140b40` U1**, the first commit on this branch to
   add a model directory and tests — and this repair of §15, §17 and the status
   block after external review of `d140b40`.

   *Corrected after that review.* Up to and including `ee2903a` this item read
   "this unit has made no model, code, rule, topology, threshold or config
   change", and it stayed on the page after `d140b40` had added
   `models/superset/adoc-literature-superset-v0.5.0/`, three test modules and
   `.gitattributes`. That was false. What **is** true, and is the claim worth
   keeping, is narrower and checkable: **no unit on this branch has changed a
   rule, node, edge, threshold, rate, condition or phenotype.** U1 added a
   directory whose 38 mechanism-bearing files are the same git blobs as v0.4's.
   Everything before `d140b40` is documentation; the code and artifact changes
   under `src/` and `docs/scrna/` arrived by merge and were authored, tested and
   reviewed on `feat/scrna-node-support`.
5. **Review-gate state carried in by the merge.** The five merged commits were
   produced under the harness gate on `feat/scrna-node-support`, and `7ee303f`
   records that gate as explicitly **`ESCALATED`, with blockers B1 and B4
   deferred and the deferrals accepted**, rather than a manufactured PASS. That
   state belongs to the scRNA unit, not to this one. Do not read this branch's
   own gate result as covering it, and do not restate it as a pass.

Standing rules for the units that follow:

6. Use **hard links** for any `data/` evidence — symlinked files are rejected by
   the manifest validator.
7. Start each unit in a **fresh session inside this worktree**, so the
   SessionStart hook seeds the `aih` baseline before any edit. A worktree entered
   mid-session leaves the review gate with nothing to review, which reads as a
   pass and is not one.
8. Run U1–U8 as separate units and sessions, each with its own review-gate
   lineage. Do not batch.
9. Record this document as the mechanistic-integration annex to
   `docs/v05_plan_review.md`.

---

## 16. Parts of the specification that should not be implemented

1. **The hard-OFF RNA gate, wired.** Two independent reasons: no powered
   absences to gate on (§0.1), and no clamp mechanism to gate with (§0.2).
   Specify and synthetic-test it; wire it only after U7 lands and bulk produces
   an absence. U7 is worth doing on its own merits and should not be justified by
   the RNA gate.
2. **`config/model_node_semantics.tsv` as a new hand-maintained file** — it would
   be the fourth semantics table, two of which are generated.
3. **The A/B/C/D single-class taxonomy as canonical semantics** — the three
   orthogonal axes are more expressive and were assigned pre-extraction.
4. **`ABSENT < INDETERMINATE < PRESENT` as numeric `min()`/`max()`.**
5. **MIN/MAX component logic for programme nodes** (§6.2).
6. **`X_IL11` in its staged form** (`= S_DECIDUALIZED`).
7. **`E_ITGA2B1` on any reading of DRE009**, including via redefinition as an
   abundance state.
8. **A universal protein half-life layer.**
9. **Re-running the scRNA audit with more convenient rules.** Consume `91f79ed`.
10. **Averaging bulk and scRNA**, with the §9 condition on physical separation.
11. **Any `rate_up = rate_up * RNA` mapping.**
12. **Free Boolean variables for AC01** — rejected by owner decision, and
    independently wrong on identifiability grounds (§7.1).
13. **Interface / relay repair in v0.5** — `gate3a_closure_audit.md:171`
    recommends not opening Gate 3b, on three recorded grounds (§0.3).

---

## 17. Checklist

**Standing prerequisites, listed against the unit each actually gates.**
*Corrected after external review of `d140b40`.* An earlier revision put all four
of these under "before opening the v0.5 worktree" and then described them as
gating U1 — which was false in both directions once U1 landed: the worktree was
already open, and three of the four do not gate a scaffold that changes no
mechanism. **None of them is resolved here. They are relocated, not closed.**

- [x] **Gated U1, and was done.** Confirm `91f79ed` is still the frozen
      **evidence** root, and that the four Tier-1 artifacts are byte-identical
      to it (§12, T-G). The **code** base is `7ee303f`, not `91f79ed` and not
      `a028ef3`. Verified at `5a55cf1`; T-H and T-G now hold it.
- [x] **Gated U1, and was done.** Read the actual cfg-writing path —
      `src/dt_adoc/model/superset_family.py`, `src/dt_adoc/model/runtime.py`,
      `src/dt_adoc/protocols/conditions.py`. This is what established that the
      generator emits exactly one version, that earlier supersets stay
      resolvable as immutable parents, and that a new directory with a
      `provenance.toml` is picked up by `available_models` automatically.
- [x] **Gated U2, and was done — it is what blocked U2.** Read
      `adhesion_variability_semantics.md`, `gate3a_closure_audit.md`,
      `prl_igfbp1_temporal_axis.md` and `node_support_deviations.md`. The second
      and third postdate the `v05_plan_review.md` section U2 was derived from and
      reverse it; that is the whole content of U2's result. Still unread, and
      carried to the next unit that needs them: `gate3_scope_adjudication.md`,
      `endpoint_convergence_finding.md`.
- [ ] **Gates any reopening of Gate 3b.** The variability-semantics fork in
      `adhesion_variability_semantics.md` was referred to the owner and is
      **still undecided** — the independent reviewer returned `UNAVAILABLE`, which
      is not agreement. §0.3 and `gate3a_closure_audit.md:171` both keep Gate 3b
      closed on this.
- [ ] **Gates any v0.5 claim about `E_ESTROGENIC_PROLIFERATION` — so U3, U4 and
      U5, not U1.** Owner answer: is the CNT arm unstimulated or E2-primed-only?
      **Still unrecorded, and still open.** It changes the expectation for that
      node only. The U1 scaffold makes no claim about any node, which is why it
      could proceed; the moment a unit interprets that node, this binds.
- [x] **Gated U8.** An `E_PAEP` interpretation rule. **Met on 2026-09-17**, and
      this line was stale until U5 (2026-09-23): the owner adopted the
      three-band ordinal rule in `stage3_experiment_selection.md` §9.1 (ON at or
      above the full-cocktail band, OFF at or below the E2-only band,
      indeterminate between), which `experiment_candidate_review_2026-09-22.md`
      M2 already recorded as correcting this prerequisite. What remains open is
      the cross-reference: `OM-001`'s `claim_ceiling` still describes the
      threshold as implicit and unrecorded.

**U1 — scaffold** — *delivered; see the record below.*
- [x] `models/superset/adoc-literature-superset-v0.5.0/` as a copy with a new
      provenance record; v0.4 untouched. All 41 files copied byte-for-byte;
      only `provenance.toml`, `README.md` and `executable_model_manifest.tsv`
      differ, and only to name v0.5.0. `[scaffold]` in the new provenance
      records the parent, its digests, and `mechanism_changes = 0`.
      Asserted file by file in `tests/unit/test_v05_scaffold.py`, so U2's first
      rule change shows up as exactly that change.
- [x] v0.4 immutability (T-H) — `tests/unit/test_v04_immutability.py`. Every
      one of v0.4's 41 files is checked against the digest its own
      `provenance.toml` records, **and that provenance file is itself pinned to
      a literal in the test**, so an artifact cannot be edited and its recorded
      hash restated to match. The file set is enumerated from disk, so a file
      cannot be added either. Both tamper cases were verified to fail before
      this was committed.
- [x] Separate v0.5 artifact versioning — satisfied by the existing runtime:
      `resolve_model` gives v0.5.0 its own `output/smoke/<version>` root, and
      the test asserts v0.5 cannot land on v0.4's outputs and has not become
      anyone's default.
- [x] Line endings and `.gitattributes` (T-K) — **settled by freezing, not by
      normalizing**, which is the opposite of the obvious fix. `docs/v05_line_endings.md`
      records why: two of T-G's four tier-1 artifacts are CRLF, so `*.tsv text
      eol=lf` would rewrite the frozen evidence root's bytes at checkout,
      invisibly, and invite a re-pin as the repair.
      `tests/unit/test_line_endings.py` pins the inventory and **rejects every
      route back into git's EOL machinery** — `eol=*`, bare `text`, any `text=*`
      including `text=auto`, and `!text` — and asserts the *effective*
      attributes of the frozen artifacts with `git check-attr`, so a spelling
      nobody anticipated still fails. (`text=auto` bypassed the first version of
      this guard; see `docs/v05_line_endings.md` §6.)
- [x] Pre-U7 cfg byte-identity (§12) — asserted, and labelled in the test as
      the invariant U7 retires and replaces with T-B rather than weakens. A
      companion test asserts no cfg declares `$nb_mutable` / `$Low_*` /
      `$High_*` yet, so U7 cannot land without retiring it deliberately.

**Two things U1 deliberately did not do.**

- **It did not retarget the generator.**
  `dt_adoc.model.superset_family.MODEL_VERSION` still reads
  `adoc-literature-superset-v0.4.0`, and the v0.5 provenance says
  `generator_module = "none_copied_from_parent"` rather than claiming an
  emission that did not happen. Whether U2 retargets the generator or edits the
  v0.5 artifacts directly is a U2 decision, and taking it in U1 would have meant
  regenerating from context sources — a topology risk U1 has no mandate for.
- **It did not repair two defects it found in frozen files.** v0.4's `README.md`
  is titled *"ADOC Literature Superset v0.3.0"* (the generator hardcodes the
  string), and `context/literature/pdf_manifest.tsv` carries mixed line endings.
  Both are recorded — in `[scaffold.inherited_defects]` and
  `docs/v05_line_endings.md` §5 — and neither is fixed, because v0.4 is frozen
  and the manifest is outside this unit.

**U2 — Gate 3a: BLOCKED. Analysis complete, no mechanism change.**
*Record: `docs/v05_u2_gate3a_blocked.md`. Guards:
`tests/unit/test_v05_gate3a_guards.py`.*

**Do not perform the three items below.** They are kept, struck, because a plan
that silently deletes what it once instructed leaves the next session unable to
tell an abandoned idea from one that was never considered. Each is now rejected
by a test.

- [x] ~~De-alias `S_PRL` from `S_IGFBP1`~~ — **blocked on MEASUREMENT.** The two
      nodes are indistinguishable to the model, and the one repair that survives
      on the merits needs an IGFBP-1 binarisation threshold that may not be drawn
      from diagnostic OM-002 without the leakage `AGENTS.md` forbids.
- [x] ~~Add the day-3 maternal protocol stage~~ — **blocked on PHYSICAL-TIME
      SEMANTICS, which is a different blocker and not an assay.** Day 3 and day 6
      carry identical `agents` and `agent_concentrations`, so the **Boolean input
      vector is the same**, and `calibration.yaml` records
      `duration_units: relative_only`. (Eleven other fields differ, including an
      unmatched collection window; `docs/v05_u2_gate3a_blocked.md` §1.2 states
      them, and they do not give the arm a different input vector.) A better
      IGFBP-1 assay would not unblock this; a calibrated time axis would, and
      this project disclaims one.
- [x] ~~Simulate the transient ... declare a relative rate~~ — **unreachable.**
      With one Boolean function, equal rates and equal initial states the two
      nodes' onset distributions are identical at every horizon and seed, so the
      sweep's answer is fixed by construction. The fallback, declaring a relative
      rate, is rejected outright by `prl_igfbp1_temporal_axis.md` §6 as fitting a
      rate to an assay artifact.
- [x] Δ = 0 here is expected (TI012) and admissible under §5.5 — recorded, and
      moot while U2 is blocked.

**What would unblock each half** (they are not the same, and an earlier revision
of this record wrongly labelled both "measurement"): for the de-aliasing, an
assay-compatible IGFBP-1 threshold not drawn from OM-002, paired per-chip PRL and
IGFBP-1 at matched timepoints, or a normalised readout removing the 83× confound.
For the day-3 arm, a physical-time calibration — which is a change to what the
model claims, not a measurement to go and take.

**U3 — AC01 mechanistic reconsideration: ATTEMPTED, NEGATIVE. No rule adopted,
alias left in place and flagged.**
*Record: `docs/v05_u3_ac01_no_derivable_rule.md`. Guards:
`tests/unit/test_v05_u3_ac01.py`.*

This is one of the two outputs this checklist allowed, and it was reached by
looking rather than by assuming.

- [x] **D1 confirmed** (§0.7) before anything else.
      `alias_classes.AC01.decision_provenance` carries `depends_on_deviations =
      ["D1"]`, `registration_status = post_extraction_semantic_repair` and the
      **computed** `counterfactual_verdict_without_D1 =
      unclassified_by_section_5_4`; the recorded raw-sensitivity digest was
      re-derived and matches. U3 has a mandate, and it is still a mandate
      downstream of an interpretive call rather than of a measurement.
- [x] **Derivation attempted, against every candidate edge, logic hint and rule
      variant touching the class.** The result is negative, and §7.1's stated
      reason for expecting it was **wrong in one place** — see the correction
      there. A candidate rule does exist:
      `E_HBEGF = E_SECRETORY_STATE or IN_HCG`, from `REF-059` / `PDF-028`. It is
      **structurally effective** (35 → 36 distinct Boolean functions, AC01 9 → 7,
      computed with the repository's own exhaustive `load_structure`) and is
      **rejected on §5's EDGE-promotion criteria**, failing seven of eight. §5(1)
      is not satisfied either — REF-059 has no row in the ledger §5 names. The
      Δ result stays a diagnostic, never an evidence basis: the ordering §0.4
      exists to enforce.
- [x] **Recorded as the finding, alias left in place. No free Boolean variables.**
      The free-variable count is pinned at 19 (5 non-input) in both models, and
      no AC01 member may become `logic = <self>`.
- [x] P1 rests on `E_PAEP` vs `E_HBEGF` alone, and the condition-entanglement
      objection to those two is **discharged by measurement** on the raw layer
      and **only for those two** (§0.8(a)). Carried at that scope throughout, and
      not widened.

**Two structural facts U3 established that the next unit should not re-derive.**

- **AC01 is one fact, not nine errors.** All nine members compute the **same
  effective Boolean function**, and that function's **support** is `{IN_E2,
  IN_PROGESTIN, IN_MIFEPRISTONE}`. This is *not* a claim that the nine share a
  syntactic upstream closure, and they do not: `E_ITGAVB3_5` syntactically
  reaches `E_KLF12_HIGH` through `E_LIF` and the other eight do not. That branch
  is **absorbed**, so `E_KLF12_HIGH` sits in `E_ITGAVB3_5`'s closure but not in
  its function's support — verified by exhaustive enumeration over both of its
  values (`DegenerateRuleTest`). The epithelial effector layer has one
  determinant and every effector hangs off it, so breaking the alias needs a
  second determinant that is **not a subset of** `E_SECRETORY_STATE`.
- **`E_ITGAVB3_5`'s committed rule is degenerate.**
  `E_LIF or E_HBEGF or E_SECRETORY_STATE` reduces to `E_SECRETORY_STATE`
  exactly, because both other disjuncts are subsets of the third. So does the
  one catalog variant aimed at it (`dr20260911_itgav_no_secretory_absorption`,
  35 → 35, AC01 still 9) — it is a prerequisite for a repair, not a repair. So
  does adding EDGE-006 (`E_GP130_STAT3 → E_ITGAVB3_5`), the highest-confidence
  edge touching the class that v0.4 does not implement.

**U4 — AC04 / GP130: COMPLETE, EVALUATION-ONLY. No canonical promotion, no
mechanism change.** *(independent of D1)*
*Record: `docs/v05_u4_gp130_axis.md`. Guards: `tests/unit/test_v05_u4_gp130.py`.
Generated: `docs/gate2_target_level_rederivation.{md,tsv}` and the extended
`docs/experiments/variant_discrimination.{md,tsv}`.*

- [x] **Read Yap/Dimitriadis 2011 (PMID 21619711) first, and it does not decide
      what it was expected to decide.** Full text, 15 pages, sha256 recorded in
      the ledger. It identifies **ANXA2** and **FLOT1** as IL-11-regulated
      plasma-membrane proteins in human endometrial epithelium — and runs **no
      LIF comparator and no functional endpoint**, so it cannot establish that
      either is IL-11-*specific*, which is the whole content of TI002's second
      family member. Every quantified fold-change is in ECC-1 or Ishikawa; in
      primary hEEC neither protein's total abundance moves. **TI002's family is
      therefore single-membered for want of a representable alternative, not
      because the evidence chose** — two different states, and only one of them
      is progress.
- [x] **The arm that was available, and is refused.** `ANXA2` **is** the
      committed node `E_ANXA2_ACTIN` (`network.bnd:133-135`) and an AC01 member,
      so `E_ANXA2_ACTIN = E_SECRETORY_STATE or X_IL11` would write the missing
      family member and dent AC01 in one line. Measured with the repository's own
      exhaustive enumerator it is the **largest structural gain on this axis** —
      35 → 37 alone, **35 → 38** with GP130-b, AC01 9 → 8, against 35 → 37 for
      GP130-b by itself. Against §5's eight **edge** criteria it fails **four**
      outright — species and system, *activity versus abundance*, AND/OR/graded
      semantics, and Boolean abstraction overstates — with causal-vs-associative
      support **partial** (a sufficiency experiment only) and direction and
      compartment passing; the eighth, competing variants remaining plausible,
      fixes the disposition rather than scoring, exactly as in U3. The decisive
      one is *activity versus abundance*. And it fails the prior question,
      because no source makes either protein IL-11-specific. Recorded in
      `NOT_STAGED`, not dropped.
- [x] **Full-text verification of everything TI001/TI002/TI004 rest on.** Into
      the ledger §0.6 identifies, which is
      `context/literature/reviews/deep_research_drug_targets_2026-09-16.primary-verification.tsv`.
      **Two rows revised, none appended, count still seven:** `DTR002-followup`
      from "NOT YET READ" to a full-text record, and `DTR005` (Domínguez 2010)
      from abstract-verified to full text. `DTR002` (Marwood 2009) was re-checked
      against PDF-043 and holds. The remaining two findings — `DTR001` and
      `DTR003` — **have no primary source at all**: one is a claim about a commit
      and one is a structural measurement, and both were verified against the
      repository instead. **No reference or PDF registration was added**, which
      is U4's scope and not a rule: registration is provenance, canonical
      promotion is a separate decision on §5's criteria, and a later unit may
      register Yap 2011 while still refusing every mechanistic use of it.
- [x] **`X_IL11` and the CD98 rewire staged as evaluation-only rule families.**
      `GP130-b` was already staged and is re-confirmed (35 → 37, no new alias,
      `E_LIF` separated); DTR003's rejected staged form re-measured at 35 → 36
      with `X_IL11` inside a **seven**-member decidual class. `CD98-d` is TI001's
      **literal** rule text, third disjunct included, staged precisely so that
      what the disjunct buys is computed rather than argued: it separates from
      `CD98-b` in **exactly one** setting — embryo-conditioned signal present,
      hCG **absent**. That is the hCG-depleted conditioned-medium control
      Domínguez did not run, having attributed the conditioned-medium effect to
      hCG rather than tested it. Nothing entered `network.bnd` or
      `rule_variants.tsv`; §6.1's `variant_id` / `requirement_set` schema is a U6
      deliverable and adding variant rows now would also break U1's scaffold
      assertion.
- [x] **Gate 2 invariant re-derived against a closed `target_class` vocabulary —
      and no verdict changes.** `docs/gate2_target_level_rederivation.md`, from
      `src/dt_adoc/reporting/target_levels.py`. Three results. **(i)** Zero
      changed verdicts under 13 biological levels. **(ii)** The exposure is
      narrower than the headline: DTR020's "34 rows, 24 distinct values" is a
      *catalog* statement, and the criterion reads only executable rows, so what
      it can see is **29 rows and 21 values**. **(iii)** "No change" is reported
      with its own fragility — only five Boolean-function classes have two or
      more catalogued members, and the minimum relabellings to flip each are
      barrier trio **1**, `E_PGR`/`S_PGR` **1**, `S_SPP1`/`S_TAZ_ECM` **1**,
      GP130 **2**, AC01 **5**. DTR020's demonstration is confirmed *and bounded*:
      the trio is exactly as fragile as it said, and the signals this
      repository's arguments lean on are not. The catalog is **not** rewritten —
      the typing is passed in as an override — and no coupling adjudication is
      forced, proposed or changed.
- [ ] **TI016 is NOT fully closed, and `blocks_v05 = yes` still stands for the
      rest of it.** What U4 closed is the invariant re-derivation. DTR022's
      reported non-forcing node-dictionary axis and DTR021's six
      `execution_status` demotions are untouched: both are catalog changes that
      remove catalog ground from real coupling verdicts, and
      `docs/coupling_adjudication.md` §2c already records them as a focused
      change that must not be made silently.

**U4b — candidate-node closure: COMPLETE. Nothing promoted, no mechanism change.**
*Record: `docs/v05_u4b_candidate_node_closure.md`. Guards:
`tests/unit/test_v05_u4b_candidate_closure.py`. Artifacts:
`context/literature/reviews/deep_research_adhesion_model_2026-09-11.{primary-verification,candidate-node-dispositions}.tsv`.*

Inserted before U5 so that U5 audits a model whose candidate set is closed. It
turned out to be the unit that found §5's own defect.

- [x] **All fourteen Sept-11 candidates carry an explicit, auditable
      disposition**, with a **node verdict and an encoding verdict in separate
      columns**. **As U4b closed them:** 0 `PROMOTE`, 1 `RULE_VARIANT_ONLY`,
      2 `WAIT_FOR_EXPERIMENT`, 6 `RETAIN_CATALOG_ONLY`, 5 `EVIDENCE_UNVERIFIED`,
      **0 `MERGE_WITH_EXISTING`, 0 `REJECT`**, and **six** had a justified node
      with a rejected encoding — the distinction a single column cannot carry.
      **Live counts after U5b (2026-09-23), which moved `S_AKT_EXCESS` `EVIDENCE_UNVERIFIED` → `RETAIN_CATALOG_ONLY` on Kang 2022 (`U5B-001`): 1 `RULE_VARIANT_ONLY`, 2 `WAIT_FOR_EXPERIMENT`, 7 `RETAIN_CATALOG_ONLY`, 3 `EVIDENCE_UNVERIFIED`, 1 `REJECT` (`E_GLYCOSYLATION_PROGRAM`), 0 `MERGE_WITH_EXISTING`, 0 `PROMOTE`, and SEVEN split verdicts** (1 / 2 / 6 / 4 after the 2026-09-22 PRL/IGFBP1/FOXO1 evidence-registration unit) — see `docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md` (and `docs/curation_increment_08_blocked_sources.md` for the 2026-09-18 state).
- [x] **§5 repaired, not supplemented.** It defined a disposition for one of its
      failure modes. It now has two prior criteria
      (node coherence split into *refuted* and *insufficient*; non-duplication
      keyed to semantic state and compartment rather than to Boolean equality),
      an explicit activity-versus-abundance test on (2), the rule that **the first
      failing criterion governs**, the value `EVIDENCE_UNVERIFIED`, the restored
      `MERGE_WITH_EXISTING`, and a `formalism_verdict` that is orthogonal **and
      subordinate**. §4.3's vocabulary mapping is recorded and is **not a
      bijection**. Every U4b disposition is issued under the repaired §5.
- [x] **Seven candidate nodes changed disposition, from five §4.1 classification
      entries; five of the seven moved stricter.** §4.1's rows are corrected in
      place rather than deleted. Two further entries are resolved or split without
      the disposition value moving.
- [x] **`S_FOXO1` and `E_SOX17` fail at §5(2), not §5(4).** The
      abundance-for-activity substitution `AGENTS.md` forbids for a *node* is
      forbidden here for the *edge into* the node: a determinant of the namesake's
      mRNA or total protein is not a determinant of an activity state. Both fail
      before the structural screen is reached, so their structural measurements
      are diagnostics rather than reasons. `S_FOXO1` is `WAIT_FOR_EXPERIMENT`;
      `E_SOX17` stays `RETAIN_CATALOG_ONLY`, because half its unblock is external
      to this platform.
      **Superseded for `S_FOXO1` on 2026-09-22** — Labied 2006 supplies the
      localisation determinant, so it cleared §5(2), now fails at §5(4) and reads
      `RETAIN_CATALOG_ONLY`; see the live-count line above and
      `docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md`. `E_SOX17` is unchanged.
- [x] **§5(2)'s actionability discriminator is owner-ratified (2026-09-18)** and,
      checked row by row, changes no disposition. Each row records its own answer
      in `unblock_locus` and a guard enforces the rule per row.
- [x] **The closure's invariants are machine-readable, not prose-matched.** The
      §5(1) ledger carries a `final_dispositions` field and a guard compares it to
      `…candidate-node-dispositions.tsv` candidate by candidate. The Sept-16
      ledger guard asserts what is actually U4b's — its `U4B-*` ids and the
      `(U4b)` curation stamp — rather than a row count, since that file is not
      U4b's to freeze and a later unit may legitimately add a verified claim to
      it. Papers, verification routes and source digests belong to nobody.
- [x] **Primary verification: six of nine references claim-level verified by U4b,
      into a Sept-11-scoped ledger** — **all nine as of 2026-09-18**, when the two
      access-blocked sources were read and registered. Marwood 2009 **reused, not re-read**; Yu
      2018 read from a PDF the owner supplied during the unit (sha256 recorded);
      Kinnear 2019, Griffiths 2019 and Liao 2024 read from Europe PMC full-text
      XML (sha256 recorded); Li 2013 and Vasquez 2015 read via the PMC web
      rendering, which serves no XML — recorded as **weaker provenance**, and
      nothing is promoted on them. **No `REF-*` id, no `pdf_manifest.tsv` row and
      no write to the gitignored PDF library**: registration is curation and a
      shared-resource change, exactly as U4 reasoned for Yap 2011. *The
      2026-09-18 curation increment did register the two it read.*
- [x] **Two access blockers recorded as blockers, not as evidence.** Ma 2023 and
      Zhou 2021 were subscription-only when U4b probed Europe PMC on 2026-09-17;
      `docs/paywalled_papers_needed.md` named the specific fields each would
      unblock. **Neither node was rejected on that ground.** Yu 2018 moved to that
      file's resolved section. **RESOLVED 2026-09-18:** both were supplied, read in
      full and registered, and all four of Ma's blocking fields and all four of
      Zhou's are answered — three of Ma's negatively. See
      `docs/curation_increment_08_blocked_sources.md`.
- [x] **One candidate is miscited.** `E_ESR1_ACTIVITY`'s sole reference is
      `REF-020` = Zaragozano 2026, the ADOC platform paper, which studies neither
      ESR1 nor receptor pathway activity. Three more — `S_AKT_EXCESS`, `S_ERK`,
      `S_TGFB_CONTEXT` — have an **empty `refs` field, no candidate edge and no
      `mechanisms.tsv` row**, and all four were holding a disposition that
      implies their evidence had been weighed.
- [x] **Three structural gains found and all three refused, with tests.**
      `S_WNT4_CTNNB1 = S_BMP_SMAD and not IN_XAV939` reaches **35 → 37** with the
      evidenced FOXO1 conjunct and **costs no new free variable**, because
      `IN_XAV939` is a declared input that no rule reads — refused on DRUNR-003,
      which requires compartment-specific exposure evidence that does not exist.
      `S_FOXO1 = S_WNT4_CTNNB1 or S_PKA` gains (35 → 36) where the conjunctive
      form does not (35 → 35, decidual class 6 → 7) — and is **contradicted** by
      Li 2013, which applied WNT4 siRNA with cAMP present and still saw FOXO1
      fall. `X_ECM_FN1_COL4`'s package reaches 35 → 36 and the entire +1 belongs
      to `E_ITGA2B1`, an edge rejected twice. **This is the third consecutive
      unit in which the largest available structural gain was refused on
      evidence**, after U3's `E_HBEGF` arm and U4's ANXA2 arm.
- [x] **Two asserted structural claims corrected by measurement.** `E_SOX17` as
      staged and the glycosylation pair were recorded as *inert*; measured, they
      **enlarge AC01** 9 → 10 and 9 → 11. `E_ESR1_ACTIVITY`'s asserted 35 → 35 is
      measured and holds.
- [x] **No mechanism change.** No rule, node, edge, threshold, rate, istate,
      condition or phenotype moved; no free Boolean variable added; v0.4 and the
      v0.5 model directory untouched; the staged bundle not edited. Both
      supersets still measure 35 distinct functions, 19 free variables and a
      nine-member AC01, re-derived in the guards rather than quoted.

**U5 — audit** *(audits the post-U4b model, which U4b left byte-identical to the
pre-U4b model — so the numbers below are the v0.4 numbers, and that is a result,
not an omission)*
- [x] Recompute Δ and confirm which alias classes actually broke. **Δ = 0; none
      broke, none formed** — recomputed from the v0.5 directory, not inherited.
- [x] Rerun identifiability and design-alias; **carry the matched-unit caveat**
      onto every number (§13.12). Identical to v0.4 in every block; the caveat is a
      field on each design-dependent block and a column in
      `docs/u5_structural_audit/u5_node_audit.tsv`. Record:
      `docs/v05_u5_structural_audit.md` (its §6 lists the residuals deliberately
      left: `S_AKT_EXCESS`, `OM-001`'s `claim_ceiling`, the CNT-arm question and
      the overlapping-seed concordance spread).

**U5b — deferred-repair closure: readout leakage and two U5 residuals.**
*The first mechanism-changing unit in the v0.5 line. It emits
`adoc-literature-superset-v0.5.1`; v0.5.0 stays exactly as U5 audited it.*
*Delivered 2026-09-23; record `docs/v05_u5b_readout_repair.md`. Each item below
is ticked against that record, which carries the numbers; they are not restated
here, so that there is one place to keep current. Two things differ from what this
block predicted and are recorded there: the `S_AKT_EXCESS` label does move
(to `RETAIN_CATALOG_ONLY`, because §5's table reserves `EVIDENCE_UNVERIFIED` for a
failure at (1)), though nothing is promoted; and the transient change is large,
not marginal. The interval wording is narrowed to block-reproducibility bands at
the owner's instruction.*
- [x] **Emit v0.5.1 rather than editing v0.5.0.** v0.5.0 is an audited object and
      `tests/unit/test_v05_scaffold.py::ScaffoldIdentityTest` — which asserts it is
      byte-identical to v0.4.0, `network.bnd` included — **stays intact and stays
      passing**. The new directory carries a `[increment]` provenance block naming
      its parent, the one rule changed, and `mechanism_changes = 1`, in the same
      shape U1's `[scaffold]` block uses for a copy.
- [x] **Repair `OUT_STROMAL_DECIDUALIZED` in v0.5.1.** `= S_DECIDUALIZED and
      S_PRL and S_IGFBP1` → `= S_DECIDUALIZED`. The two marker conjuncts are
      absorbed in **all** 524,288 assignments, so the composed function does not
      move: 35 distinct functions, 19 free variables, AC01 = 9, decidual class = 6,
      each re-derived in the unit rather than inherited. Admissible under §5.5 /
      TI012 — a repair whose effect is transient rather than partition-level,
      which is exactly what the Δ screen cannot see.
- [x] **Measure the transient; do not assume it.** Under asynchronous updating
      `S_PRL` and `S_IGFBP1` lag `S_DECIDUALIZED`, so the repaired node's *onset*
      can move even though its fixed point cannot. Compare v0.5.0 against v0.5.1
      **paired, on common random numbers** — the same seed blocks driving both
      arms, and blocks disjoint between replicate indices.
      **Pairing is variance reduction and nothing more.** It does not remove Monte
      Carlo error and does not make the contrast "the rule change rather than seed
      noise": unless every paired per-trajectory difference is constant, the
      finite-sample paired mean stays random. So the result is reported as an
      estimate with an uncertainty, never as a bare difference —
      **independent replicate blocks, a stated uncertainty measure across them, a
      trajectory-count stability check, and a tolerance declared before the
      comparison is run.** A paired difference inside that tolerance is "no
      detected transient change at this precision", **not** "no change".
      **Do not rerun the 50 × 20,000 endpoint dataset** unless an artifact this
      unit must regenerate actually depends on it; the endpoint figure reports
      `OUT_STABLE_ADHESION`, which cannot move here.
- [x] **Blast radius, stated and checked:** exactly one node.
      `OUT_STROMAL_DECIDUALIZED` is read by **no** rule, and
      `OUT_MATERNAL_ADHESION_COMPETENCE` reads `S_DECIDUALIZED` directly, so no
      other trajectory can change. Assert it rather than assert around it.
- [x] **Correct the recorded blast radius where it is overstated.**
      `prl_igfbp1_foxo1_evidence_registration_2026-09-22.md` §4 item 2 says
      de-aliasing would make the markers "causal gates on adhesion competence". It
      would not — the node is a leaf. The sequencing constraint the sentence
      supports is unaffected and **stands**; only the stated consequence is wrong.
- [x] **`OM-001`'s `claim_ceiling` → the frozen three-band rule**
      (`stage3_experiment_selection.md` §9.1, owner-adopted 2026-09-17). A
      cross-reference, not an adjudication; §14.2's requirement that any
      observation-map change carry its own justification is met by naming the
      adopted rule.
- [x] **Re-adjudicate `S_AKT_EXCESS` against `PIF-007` / Kang 2022.** §5(1) is
      satisfied by a registered primary human source, so `evidence_state` and
      `first_failing_criterion` move. **The disposition is expected not to move** —
      Kang supplies no ADOC-addressable exposure — which makes this the same shape
      as `S_FOXO1` on 2026-09-22: an evidence advance recorded as a later failing
      rung. Repair the now-inaccurate comment in
      `test_v05_u4b_candidate_closure` that calls it a candidate with no
      verifiable reference.
- [x] **Out of scope, stated so it is not drifted into:** no de-aliasing, no
      candidate-node admission, no threshold, no rate, no istate, no condition
      change. v0.4.0 and v0.5.0 are both immutable in this unit.

**U6 — semantics and components** — *delivered; see `docs/v05_u6_semantics_components.md`.*
- [x] Extend `observability.py` to emit the three axes for all 59 nodes. Done as
      a **second generated output**, `docs/u6_semantics/node_semantics.tsv`, not
      as new map columns: the map is Tier 1 of T-G and must stay byte-identical
      to `91f79ed`. The 27 assessable rows are computed by the same
      `interpretability_rows` that froze `node_rna_interpretability.tsv` and are
      tested against it; the other 32 are `not_RNA_assessable`. `rna_can_*`
      columns (§1.3) are **not** emitted: they are the gate layer's clamp rule,
      which §0.2/U7 block.
- [x] **Owner decision on HGNC alias handling** (`CTGF`/`CCN2`, `CYR61`/`CCN1`)
      before any `S_TAZ_ECM` evidence is used. **Taken 2026-09-23: explicit,
      forward-only, per-symbol** — `CTGF` → `CCN2` (HGNC:2500), `CYR61` →
      `CCN1` (HGNC:2654), verified 1:1 renames. The frozen audit is not altered;
      `feature_absent` means the committed symbol was absent, not the gene;
      `CCN2`/`CCN1` presence is `unverified`, and no `S_TAZ_ECM` evidence may use
      an alias-resolved feature until a registered extraction checks it. No
      general normaliser.
- [x] **Freeze §6.3's combination table before writing the combinator**, and
      assert it by exhaustive enumeration (T-D), including that empty groups
      raise rather than evaluate.
- [x] Implement `provisional_corrected_layer_only` as orthogonal metadata with
      the dual AND/OR propagation of §6.3(4), and the clamp veto (T-E2). Doing
      this with the combinator, not after it.
- [x] Component map with `requirement_group`, `logic`, `role`,
      `symbol_as_committed`, `resolution_status`, and **`variant_id` /
      `requirement_set`** so node-level requirements stay the intersection over
      admissible variants (§6.1); default `requirement_structure = undeclared`.
      `resolution_status` is carried as four separate fields
      (`committed_symbol_status`, `current_hgnc_symbol`/`hgnc_id`,
      `alias_resolution`, `current_symbol_presence`) per the owner decision.
      **No group is declared** (§6.2; `node_dictionary.tsv:32` reads
      `E_ITGAVB3_5` as an OR of all three subunits, contradicting §6.1), and no
      variant set exists because GP130-b is in no `rule_variants.tsv`. The
      declared path is exercised on synthetic fixtures only.
- [ ] **Still owed, found here:** T-G's two-tier digest pinning is recorded above
      as held since U1, but a search of `tests/`, `src/`, `docs/` and `config/`
      for the artifacts' current digests found no pin. U6 adds a blob-identity
      check for the two evidence-root inputs it reads, which runs wherever
      `91f79ed` is reachable; full T-G is not done.

**U6b — `E_MUC1_BARRIER` reconciliation.** *After U6, before U8; independent of
U7.* — *delivered 2026-09-24, evaluation only; see
`docs/v05_u6b_muc1_reconciliation.md`. Every structural and endpoint figure lives
there and in `docs/u6b_muc1_reconciliation/`, generated by a committed derivation;
none is restated in this block, which the register guard keeps count-free.*

> **Scheduled deliverable: evaluation only. The executable correction is
> `TI-06`, deferred — owner decision, 2026-09-23.**
>
> *Corrected under external review, which found this block promising a rule-level
> repair and a new model version while its own clearance bullet forbids any family
> member becoming the canonical rule unless the evidence chooses one — and no
> evidence does. As written the unit could only be satisfied by inventing an
> unsupported causal rule, or by not delivering what it promised while appearing
> to close TI-02.*
>
> There is no partial executable repair hiding in between: a barrier with no
> clearance term is the naive sign flip, which is measured and refused below.
> So U6b as scheduled emits the rule family, its per-member consequences and the
> evidence record — and changes no `network.bnd`, exactly as U3 and U4 did when
> their best candidate lost to the evidence.
>
> **Resolved by the owner, 2026-09-23: U6b stays evaluation-only, and the
> executable correction becomes its own deferred obligation, `TI-06`, with its own
> unblock condition.** So the split is visible as work still owed rather than
> folded into a unit that cannot deliver it, and U6b can complete — and TI-02
> close — with no canonical clearance rule written. `TI-06`'s conditions are U6b
> having landed, evidence that *selects* a clearance determinant by perturbation
> rather than by spatial association, and owner adoption of the exact rules. If it
> ever lands it takes a further explicit model version (v0.5.2) rather than
> rewriting v0.5.1 — the versioning rule governs *how* an executable change is
> recorded and does not by itself authorise one.
- [x] **State the contradiction from the source.** The committed
      `E_MUC1_BARRIER = not E_SECRETORY_STATE` says the progestin-driven secretory
      state switches MUC1 off. Meseguer 2001 (`PIF-008`) — human *in vivo*,
      hormone-replacement cycles, with blastocysts — reports progesterone raising
      MUC1 about twofold, apposition raising epithelial MUC1 further, and removal
      that is **strictly local** to the attached embryo, with intact epithelium
      confirmed by cytokeratin. *Done: record §1.*
- [x] **The licensed repair is the `GAP-004` split, not a sign flip.**
      `GAP-004`/`GAP-011` have prescribed a dual-node design since before v0.4:
      abundance, glycoform and local clearance are three measurements and the
      committed node collapses them. A naive sign flip is *expected* to make the
      epithelial phenotype nodes unsatisfiable and is **refused on that ground only
      once the unit has measured it** against the adopted variant and committed the
      derivation. No structural count for any unadopted variant is published in
      this plan — see the second bullet below. *Done: both flips measured
      (record §5.2). The in-place flip makes the epithelial phenotype
      unsatisfiable, as expected; the interface flip does not, and is refused on
      a different measured ground — the anti-adhesive route becomes an alias of
      its own hand-set relay. No variant was adopted, so the refusal is recorded
      against the evaluated family rather than an adopted variant.*
- [x] **Placement — DECIDED BY THE OWNER, 2026-09-23: the interface.** The barrier
      acts in `X_ANTIADHESIVE_ROUTE`, **not** in `E_RECEPTIVE_SURFACE`. Rationale,
      recorded because it is a claim about what the model means: maternal
      epithelial receptivity must stay definable **without embryo contact**, and
      Meseguer supports high bulk MUC1 together with strictly local clearance at
      apposition. *This is a decision about where a state acts, and it is separate
      from the next bullet, which is about what causes clearance. Conflating the
      two is what made an earlier revision of this block overclaim.*
      **What the placement mechanically implies, stated because an earlier
      revision left it to be discovered:** the `and not E_MUC1_BARRIER` conjunct
      at `network.bnd:142` is **removed** from `E_RECEPTIVE_SURFACE`, whose three
      readers are `OUT_EPITHELIAL_RECEPTIVE`, `X_ADHESION_ROUTE_SPP1` and
      `X_ADHESION_ROUTE_REDUNDANT`. U6b measures and reports that blast radius
      rather than asserting it is small. *(An external review described this
      conjunct as also feeding `S_PGR`; it does not — `S_PGR` is upstream, and
      `E_RECEPTIVE_SURFACE` has exactly the three readers named above, checked
      against the committed `network.bnd`.)* *Done: the two readers of
      `E_MUC1_BARRIER` are derived from `network.bnd` and asserted; removing the
      conjunct is a Boolean identity on the committed rule, so the blast radius of
      the placement alone is empty and everything that moves is the rule change
      (record §2, §5).*
- [x] **The determinant of local clearance is an ASSUMPTION, and must be carried
      as a rule family rather than as a fact.** `PIF-008` is explicit: the
      mechanism of local MUC1 removal is **undetermined** — the authors concede
      embryo-induced epithelial apoptosis would look the same — the adhesion-phase
      observation is **n = 3 sites, descriptive, with no perturbation**, and the
      paper does not license an embryo-competence conjunct. So writing
      `clearance = f(IN_EMBRYO_CONTACT)` as the unique rule would turn a spatial
      association into a causal edge, which §5's edge criteria and `AGENTS.md`
      both forbid. **Before any `.bnd` is written**, U6b pre-registers a rule
      family over the clearance determinant, with at least: contact-driven;
      contact-plus-competence (recorded as *not* licensed by `PIF-008`, carried to
      show what it would change); and clearance left unresolved. It reports the
      endpoint consequence of each — including, explicitly, whether the barrier can
      ever be ON at the moment adhesion is evaluated, since a family member that
      makes MUC1 inert for `OUT_STABLE_ADHESION` is a result the unit must state
      rather than discover later. No family member enters `network.bnd` as the
      canonical rule unless the evidence chooses it; otherwise the family goes to
      `rule_variants.tsv`, which is §5's stated consequence for exactly this case.
      *Done: the family is pre-registered in `MEMBERS` of
      `src/dt_adoc/reporting/u6b_muc1_family.py`; under contact-driven and
      contact-plus-competence clearance the barrier is never ON when
      `OUT_STABLE_ADHESION` is evaluated (record §5.3). No member entered
      `network.bnd`. **Clarified (owner, 2026-09-24):** for an evaluation-only
      unit, "goes to `rule_variants.tsv`" means the committed U6b rule-variant
      catalog, `docs/u6b_muc1_reconciliation/rule_variants.tsv`, in the model
      file's exact schema with non-executable statuses only and
      `default_in_family` false on every row. It is the only file that
      tabulates the member rules. v0.5.1's own `rule_variants.tsv` is part of an
      audited model and is untouched. If `TI-06` creates a new version, the
      relevant variants can then enter that version's model-local
      `rule_variants.tsv`.*
- [x] **Node names and rules are PROPOSED, NOT ADOPTED**, and must be shown to the
      owner and adopted explicitly before any `.bnd` is written. The naming
      requirement is semantic: **abundance, barrier competence and local clearance
      must stay three distinguishable things** and must not be collapsed back into
      one label. *Held: the names in the record are proposals, and no `.bnd` was
      written.*
- [x] **No structural count for an unadopted variant appears in this plan or in
      the register.** Counts are published only once the variant that generates
      them is committed **and** a deterministic derivation — a script or a guard
      that recomputes them from `network.bnd` — is committed with them. *Added
      under external review, which found this block publishing exact counts for a
      variant that did not exist in the repository and that the plan itself
      described as merely proposed; the figures were also stale, having been
      computed for a two-node sketch while the block proposed a three-node split.*
      *Held: counts for the evaluated members appear only in the record and its
      artifacts, which regenerate byte for byte from `network.bnd`
      (`pixi run build-u6b-muc1-family`); none appears here or in the register.*
- [x] **Report the structural and identifiability consequences in both
      directions.** A bulk-abundance node whose rule is a pass-through of an
      existing state **enlarges the alias class it passes through** — the size of
      that cost depends on which state drives it and is therefore a number U6b
      derives from the adopted variant, not one this plan asserts in advance. It
      is reported as a cost, not netted against the gain. Rerun identifiability
      and design-alias with the matched-unit caveat carried as a field (§13.12),
      and report Δ against the 35-function baseline U5 proved. *Done: record
      §5.1, both directions, with the enlargement reported beside the separation.*
- [x] **Not reopened by this unit:** `E_MUC1_SLEX` stays committed and
      `E_SLEX_SURFACE` stays `RETAIN_CATALOG_ONLY`; the Sept-18 refusal stands on
      its own record. MUC16 is *catalogued* as the possibly cleaner anti-adhesive
      candidate (Gipson 2008) and is **not** admitted here. *Held.*

**U7 — mutation interface (only if needed)**
- [ ] Verify whether `strict_nv` is on the gate code path (§0.2(e)) before any
      adjudication.
- [ ] Adopt the installed package's mutable-node form verbatim (§0.2(f)); do not
      re-derive it. Confirm MaBoSS's implicit default rates for a logic-only node
      empirically first — T-B is exactly the claim that they are reproduced.
- [ ] `$`-parameterised interface, labelled as such, with **both** T-B
      (inertness) and T-B2 (clamp actually clamps, from either initial state)
      before merge.

**U8 — Stage-3 rerank (mandatory, conditional on D1 — §0.7)** — *delivered
2026-09-24; see `docs/v05_u8_stage3_rerank.md`.*
- [x] Same readout-tier computation from `observation_model_map.tsv`; **not**
      `candidate_score.yaml`. *The guard records file opens and proves the YAML
      is never opened.*
- [x] Three rankings reported; frozen v0.4 result untouched whichever way it
      goes. *Read as §14 item 3's triple: frozen v0.4, v0.5.1 and per-arm delta.
      The four frozen Stage-3 files are digest-pinned.*

---

## 18. Outstanding topology obligations — the register

`docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md` §6 gives **five
ordered items, four of which are topology increments**. Item 1 is **discharged**
by U5b (2026-09-23, `adoc-literature-superset-v0.5.1`); item 2's evaluation is
**discharged** by U6b (2026-09-24, `TI-02`) and its executable half stays
**deferred** as `TI-06`; items 3 and 4 stay **deferred with named unblock conditions**.

**Three kinds of row, and they must not be read alike.** `TI-03`, `TI-04` and
`TI-06` are *outstanding obligations*: work this repository owes, each either scheduled to a
unit or deferred behind stated conditions. `TI-01` and `TI-02` are *discharged obligations*:
work that was owed and has been done, by the unit each names, with the result
cited in the row — `TI-02` by an evaluation that changed no model file, which is
why its executable half, `TI-06`, is still owed. `TI-05` is a *scoped closure record*: nothing is owed, and it
is carried so a later unit can see that the closure covers one adjudication
rather than standing for all time. The `state` column carries the distinction —
`SCHEDULED` and `DEFERRED`, `DISCHARGED`, and `CLOSED_ON_CURRENT_EVIDENCE` — and
the roadmap and the guard use the same vocabulary. *`DISCHARGED` was added by
U5b, the first unit to carry an obligation out; reusing the closure state for it
would have made "done" and "never owed" read alike.* *Separated under external review, which found the plan, the roadmap
and the test presenting every row as outstanding work.*

**Item 5 is not of the same kind, and TI-05 is not its discharge.** "New nodes
last, if at all" is a *sequencing instruction*, not a topology increment with an
exit condition. TI-05 records the state that instruction presupposes — the
Sept-11 candidate set adjudicated with `PROMOTE` = 0 — so the instruction is
currently satisfied rather than outstanding. It is carried in the register
because a later unit needs to see that the closure is scoped, not standing.
*Flagged as a loose mapping by external review and stated properly here.*

Every row also lives in `docs/deferred_topology_register.tsv`, which
`tests/unit/test_deferred_topology_register.py` pins against this section and
against the documents each row cites. Prose alone is how items 1–3 became
invisible between 2026-09-22 and 2026-09-23 — recorded in a dated evidence
document, absent from every scheduled unit. A guard is what stops that recurring.

| id | increment | state | unit |
|---|---|---|---|
| `TI-01` | `OUT_STROMAL_DECIDUALIZED` readout leakage | `DISCHARGED` | U5b |
| `TI-02` | `E_MUC1_BARRIER` split — **evaluation** of the rule family | `DISCHARGED` | U6b |
| `TI-06` | `E_MUC1_BARRIER` split — the **executable** correction | `DEFERRED` | — |
| `TI-03` | β3/β5 split and the upstream `E_HBEGF` collapse | `DEFERRED` | — |
| `TI-04` | `S_PRL` / `S_IGFBP1` de-aliasing | `DEFERRED` | — |
| `TI-05` | Sept-11 candidate-node admissions | `CLOSED_ON_CURRENT_EVIDENCE` | U4b |

### TI-03 — β3/β5 and `E_HBEGF`: two conditions, both required

Both are external to the split and checkable *before* it. *Corrected under
external review, which found an earlier revision of this list making the split one
of its own three preconditions — an exit condition that cannot be evaluated,
which is the defect the register exists to prevent.*

1. **A second AC01 determinant that is not a subset of `E_SECRETORY_STATE`** (U3's
   structural finding). Without it the split buys nothing: `E_ITGAVB3_5` reduces
   to exactly `E_SECRETORY_STATE`, and deleting a disjunct is Boolean-identical to
   the committed rule — a prerequisite, not a repair.
2. **An adjudication of which half *every* reader of `E_ITGAVB3_5` reads.** The
   committed network has **two**, and an earlier revision of this list named only
   one. *Corrected under external review.*
   - `X_ADHESION_ROUTE_SPP1` (`network.bnd:214`), where osteopontin binds αvβ3 —
     the half with no determinant — so splitting without deciding re-routes the
     SPP1 arm.
   - `E_RECEPTIVE_SURFACE` (`network.bnd:142`), where `E_ITGAVB3_5` is one
     disjunct of the adhesive-competence group. Splitting without deciding this
     changes what epithelial receptive competence *means*, and it propagates to
     `OUT_EPITHELIAL_RECEPTIVE`, `X_ADHESION_ROUTE_SPP1` and
     `X_ADHESION_ROUTE_REDUNDANT`, which are its three readers.

   A later unit may conclude that one reader takes both halves; what it may not do
   is split without answering for each.

**A consequence of the split, not a condition on it.** Once β3 and β5 are separate
states, `PIF-013` attaches to the β5 half only: it supports PC6 → αvβ**5**, while
for αvβ**3** the same flow-cytometry panel **did not establish a change** — a
non-significant result, which is not evidence of equivalence and must not be
quoted as a demonstrated absence of effect. Until the split exists, a generic
`PC6 → E_ITGAVB3_5` edge would attribute to both halves an effect shown for one
and untested-to-conclusion for the other, so **no PC6 edge may be written against
the merged node** — which is a constraint on the present model, not something to
be satisfied before the split.

### TI-04 — PRL / IGFBP1 de-aliasing: four required, plus a ranked measurement list

*Restructured under external review, which found the earlier "five conditions,
all required" wrong twice over: it **dropped** the third item of
`v05_u2_gate3a_blocked.md` §4a, and it asserted a conjunction the source does not
state. `prl_igfbp1_temporal_axis.md` §6 gives its list "**in order of value**",
and §17's own restatement joins the three with "or". So the register now
separates what is structurally required from what is a ranked measurement list,
and requires a de-aliasing unit to say which measurement item it is relying on
rather than leaving the conjunction implicit.*

**Required, all four.**

1. **TI-01 landed.** Until the leakage conjuncts are gone, independent marker
   rules convert two calibration readouts into gates on the reported stromal
   phenotype — the leakage `AGENTS.md` forbids. **Met 2026-09-23:** U5b
   discharged TI-01 in `adoc-literature-superset-v0.5.1`, so a de-aliasing unit
   starts from v0.5.1. Conditions 2–4 are untouched.
2. **A witness that is both observation-compatible and design-identifiable.**
   None exists today: of the 16 single-input forms of
   `S_IGFBP1 = S_DECIDUALIZED and [not] X` that gain a function *and* survive
   `OM-002`, **10** condition on an input no arm ever turns on, **2** on agents
   inside the four-agent bundle (one design-equivalence class), and **4** would
   make a maternal stromal marker depend on the embryo.
3. **No invented physical time.** Day 3 and day 6 carry an identical Boolean input
   vector and `calibration.yaml` records `duration_units: relative_only`, so the
   temporal half is blocked on time semantics — a *different* blocker from the
   assay one, and not closed by a better assay. This is a prohibition that always
   holds, not a box to tick.
4. **A stated choice from the measurement list below.** A unit proposing to
   de-alias must say which of §4a's three items it is relying on, and why that one
   suffices for the rule it proposes. Silence here is the failure mode: the source
   ranks the three rather than conjoining them, so "some measurement improved"
   must not be allowed to read as "the axis is unblocked".

**The measurement list, `v05_u2_gate3a_blocked.md` §4a, quoted in full and in the
source's own order of value.** Whether these are jointly required or alternatives
is **not stated by the source**, and this register does not decide it.

   i. **An IGFBP-1 binarisation threshold not drawn from `OM-002`**
   (`prl_igfbp1_temporal_axis.md` §5 forbids taking one from the same series that
   serves as the diagnostic).
   ii. **Paired per-chip PRL and IGFBP-1 at matched timepoints.** What
   `config/adoc_chip_donor_provenance.tsv` records is narrower than "the mapping
   is lost", and the narrower statement is the one to carry: `LOST-001` attests
   that the chip **set** is partly identified while the column **assignment** is
   not — "what is lost is the ASSIGNMENT, not the set" — and the named tokens do
   not cleanly cover the five columns per outlet, so the set is additionally
   incomplete. The operative consequence is unchanged and is stated there: no
   column may be assigned to a chip and no column may be paired across day rows,
   so the existing direction is an unpaired column comparison.
   iii. **A normalised or absolute-quantified readout removing the 83× confound.**
   *Dropped by an earlier revision of this register and restored here.* It is the
   item that matters most to the claim the axis is actually about: with an 83×
   day-3 median gap on top of a 2× lower detection limit, two analytes with
   identical onset kinetics would still show IGFBP-1 crossing detection first, so
   a detection-fraction ordering cannot establish a kinetic one. A de-aliasing
   unit that leaves this unaddressed has not removed the confound that motivates
   the repair.

### TI-06 — the executable MUC1 correction: three conditions, all required

All three are external to the correction itself and checkable before it.

1. **U6b has landed**, so the rule family and each member's structural and
   endpoint consequences are on the record. The executable choice is then made
   against measured alternatives rather than in place of them. **Met
   2026-09-24:** `docs/v05_u6b_muc1_reconciliation.md`. Conditions 2 and 3 are
   untouched, and the condition text in the register is unchanged.
2. **Evidence that *selects* a clearance determinant** for local MUC1 removal in
   human endometrium — a determinant of the variable the node names, established
   by perturbation rather than by spatial association. `PIF-008` explicitly does
   not supply this: the mechanism is undetermined, the authors concede
   embryo-induced epithelial apoptosis would look the same, the adhesion-phase
   observation is n = 3 sites and descriptive with no perturbation, and the paper
   licenses no embryo-competence conjunct. Without it §5 forbids any family member
   becoming canonical, and this obligation stays deferred however long that takes.
3. **Owner adoption of the exact node names and Boolean rules**, which are
   proposed and not adopted.

**Why this is a separate row rather than part of U6b.** *Owner decision,
2026-09-23.* The evaluation is supportable today and the executable correction is
not, and folding them together produced a unit that could be satisfied only by
inventing a rule — the defect external review raised twice. Split, U6b completes
and TI-02 closes on what the evidence supports, while the correction stays
visible as work still owed, which is what this register is for.

### TI-05 — scope of the closure, stated precisely

`PROMOTE` = 0 closes **the adjudication of the Sept-11 candidate set on the
evidence held at closure**. It is not a standing bar on new-node admission and
must not be quoted as one. New primary evidence is grounds for an **explicit
re-adjudication** of a named candidate under §5, recorded the way `S_FOXO1` was on
2026-09-22 and the way `S_AKT_EXCESS` was in U5b on 2026-09-23 (`U5B-001`:
`RETAIN_CATALOG_ONLY` at §5(2), not promoted). What the closure
does forbid is admission by accumulation — a candidate entering because its
biological state is justified, because it raises the distinct-function count, or
because a free input inserted as a determinant makes both numbers move. §0.4 and
§5 govern that, unchanged.
