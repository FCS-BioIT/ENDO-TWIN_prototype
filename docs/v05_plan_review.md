# ADOC v0.5 — reviewed plan

Status: planning document, 2026-09-15. Review of the draft
"ADOC v0.5 Reconstruction, Decoupling, Personalization and Prospective
Experimental Design". No model, rule, rate, protocol, calibration or
evidence file was changed in writing it. Every number below was read from
the repository or from a cited publication; none was simulated or fitted
here.

This document supersedes the draft as the working plan. It keeps the
draft's scientific objective verbatim and changes the order, the scope and
four of its conclusions.

**Revision 5, 2026-09-15 — final cleanup, not a redesign.** R43a restated:
the regimen wiring is repaired and pinned in executable code by the v0.4+
superset clone layer (`protocols/conditions.py`
`SUPERSET_CHALLENGE_PARENTS`, floor `REPAIRED_FROM_SUPERSET_VERSION`
(0,4,0), asserted by `MifepristoneArmLineageIsPinned`), and R43a is
non-assessable because of declared-horizon instability alone; R43b is the
held-out validation row and its regimen caveat is gone (§3.6). The stale
scRNA-object claim is scoped: it appears in **eleven** rows, R17 through R27
inclusive — nine inside the fifteen non-`continuous_spatial` rows, plus R18
and R26, which are formalism-limited but whose provenance should still be
corrected. **Provenance correction removes one blocker, it does not clear a
row**: the remainder are classified by type — topology, timing/dynamics,
mapping, assay design, calibration, formalism — and R20–R23 are the strongest
re-adjudication candidates only because they have comparators, which are
themselves `reported_only`/diagnostic and "not usable to validate".
Gate 3b criterion (i) now forbids *ungrounded*
hand-set stochastic variables rather than all of them. Gate 4's criterion
becomes a v0.4-versus-v0.5 comparison over the shared space rather than a
rigid `>8/32` bar. Evaluation-only representations must be a family, not one
convenient rule. Strategy is unchanged and closed to reopening (§2, §3.7).

**Revision 4, 2026-09-15.** §3.6 rewritten after review found that
`docs/results_reproducibility_matrix.tsv` already carries the interface
dynamics. R34, R35, R37 and R46 are adjudicated `not_assessable` /
`continuous_spatial`, R46 recording them "permanently out of scope for a
Boolean logical model, not pending work"; R41a is separate — a
`disagreement` on the attachment *fraction* under `timing;calibration`, not
a verdict about onset.
Two earlier revisions had this wrong in opposite directions. Gate 3b's
observable, Gate 1's starting point and open decision 3 are restated
against the matrix, and the headline it yields — **51 of 60 rows
`not_assessable`** — is split in §3.6 into 36 unreachable by formalism and
15 reachable, **nine** of which carry the stale scRNA-object claim (eleven
rows carry it in all, R17–R27; R18 and R26 sit outside the fifteen).
Correcting it removes one blocker per row and clears none of them. 51 is the
diagnosis, not v0.5's target.

**Revision 3, 2026-09-15**, after a second round of project-lead review. Seven
corrections: `dependency_depth` no longer treated as establishing temporal
ordering (§3.3 — it motivates a candidate; the ordering must be *simulated*);
`OM-016` settled as construction evidence including its direction, and
removed from the open decisions (§3.4); the admission test restored to five
criteria plus two parsimony filters, with `S_TGFB_CONTEXT` held as a
candidate variant rather than promoted (§3.8); a new **evaluation-only**
admission route so unrepresented axes can compete (§3.8); the anti-adhesive
relay result downgraded to a diagnostic, with Gate 3b opening on a per-relay
ambiguity decomposition (§3.2); the framework table rewritten to one
position (§3.7); and the open decisions cut from ten to three (§6).

> **OVERTAKEN, 2026-09-16.** The per-relay decomposition was run and found that
> the relays carry the model's only representation of between-unit variability,
> so decomposing them is blocked on a prior semantics question that is still
> undecided (`docs/adhesion_variability_semantics.md`). The Gate-3a closure
> audit then recommended **not** opening Gate 3b at all yet, on the separate
> ground that no maternal ambiguity has been resolved and none can be, because
> every discriminating observation lacks a usable assay. See
> [`gate3a_closure_audit.md`](gate3a_closure_audit.md), which is the current
> position on gate order and supersedes this line.

**Revision 2, 2026-09-15**, after the project lead reviewed this document in session. That
review changed four positions here, all in the direction of parsimony:
relative rates are no longer a prerequisite (§3.3); the interface objective
is to remove arbitrary free variables, not to replace each relay with a node
(§3.2, Gate 3b); the software default is MaBoSS plus local ADOC Python with
every external tool demoted to a methodological reference (§3.7); and no
molecule is privileged in the prospective design, anti-SPP1 included
(§3.5). It also added the separation of model-identification value from
translational value, and `perturbation × readout` as the ranking unit.

---

## 1. Verified starting point

| Item | Verified value |
|---|---|
| `main` / `origin/main` / `fransua/main` | `c81f54f1e488a2332860d38124c0b854121716ad` |
| Working tree | clean |
| Full test suite | **736 tests, OK** (`pixi run test`, 164 s) |
| Unmerged work | **one branch only**: `feat/design-alias-figure` @ `348f26d` (28 files, +48 577) |
| Other 8 worktree branches | all ancestors of `main`; nothing outstanding |
| scRNA annotations | **in hand** — E-MTAB-15842, 28,212 cells, `celltype_v2` labels, sha256 pinned in `config/scrna_observation_map.tsv` |

The draft's SHA was still current. Its claim that the last commit shipped
without the full suite is no longer true of the tree as it stands: the
suite passes on `c81f54f`.

### 1.1 The harness ledger does not say what the draft says

The draft asks to "close B10 and B13". Both exist, both are real — and
they are **not the only open blockers, and not the ones open against
`main`**. There are two independent gates:

| Gate | Basis | Status | Open blockers |
|---|---|---|---|
| `DT_ADOC_wt/scrna-klf12-prior` | 14 files, 11 rounds | **`ESCALATED`**, `accepted: false` | **B10**, **B13** |
| `DT_ADOC` (main worktree) | 30 files, 1 round | `ISSUES`, degraded, human-accepted | **B1**, **B2** |

Both gates recorded a stand-in reviewer, `degraded: true`. Codex was
unreachable (`failed_by_class: {"quota": 1}` on both the discovery and
verify stages). `cross_vendor_gap.last_independent_at` is
**2026-09-14T08:51Z**, 6 calls and 3 rounds ago.

Three consequences the draft does not account for:

1. **The KLF12 gate has escalated, and that changes *where* the repair
   belongs, not whether to make it.** Escalation is not a pass; nothing is
   approved; `aih review --require-independent` still fails on that state;
   only the user can run `aih accept`. But the decisive practical point is
   that `feat/scrna-klf12-prior` is **at the same commit as `main`**
   (`c81f54f`), so the defective strings are already merged: repairing
   inside the escalated worktree would leave `main` carrying them. **B10
   and B13 should therefore be repaired on `main`, alongside B1 and B2, as
   one increment reviewed once.** The escalated ledger entry stays as the
   honest record of how that worktree's review ended; it is not something
   the repair needs to clear, and re-running rounds there buys nothing.
2. **B1 and B2 are open against `main` and the draft does not mention
   them.** B1 is a *published figure asserting a reading the accompanying
   document withdraws*. That is the exact failure mode this repository has
   recorded twice before (stale generated artifact; orphaned artifact
   provenance). It is at least as serious as B10/B13.
3. **No independent acceptance exists for any of this.** The draft is right
   to say a same-vendor `VERIFIED` is not independent acceptance. It
   should be re-run against Codex once quota returns, and reported as
   degraded until then.

### 1.2 B10 — verified, and the draft's repair is correct

`src/dt_adoc/scrna/observability.py:757-759` still says the depth-matched
spread is `0.330 → 0.179` and the SZ25 contrast `+0.102 → −0.071`. The
committed artifacts say otherwise:

- `docs/scrna/klf12_raw_umi_findings.json:147` →
  `detection_fraction_spread_depth_matched = 0.2294572316260137`
- `docs/scrna/klf12_prior_finding.md:436` → SZ25 contrast **−0.118**
- `docs/scrna/klf12_raw_umi_findings.json:98` →
  `depth_matched_scheme_for_per_unit = "matched_cells_only"`

The stale sentence propagates to two further places, and **they are not
the same kind of file** — the draft's "fix the generator and regenerate"
would repair only one of them:

| File | Line | Generated? |
|---|---|---|
| `src/dt_adoc/scrna/observability.py` | 757-759 | the source string |
| `config/scrna_observation_map.tsv` | 12 (SC-011) | **generated**, by `observability.write_map` (`observability.py:980-991`) |
| `docs/scrna_observability.md` | 259-262 | **hand-written narrative.** No code in `src/`, `scripts/` or `pixi.toml` emits it; its own line 16 names the *TSV* as the generated artifact |

So the repair is three steps, not two: edit the source string; regenerate
the TSV (editing it directly would pass every quick check and fail only
the full suite); and **edit `docs/scrna_observability.md` by hand**, because
nothing will rewrite it.

Beyond that, as the draft proposes: name the scheme explicitly, and keep
the detailed report's statement of the unequal fraction of cells the
scheme sacrifices. **That column is the *unmatched* (dropped) share**
(`klf12_raw_umi.py:561-567` computes `below / len(members)`; the table at
`klf12_prior_finding.md:418-425` heads it "unmatched"), and the asymmetry
runs the opposite way to the intuition: matching drops only **4.1% of
`SZ25TE_HT`** cells — it retains 1,346 of 1,404, or 95.9% — while dropping
**36–50% everywhere else**. The deep unit keeps almost all its cells; the
shallow units pay. That is the cost of `matched_cells_only` and it must
not be dropped or inverted. Then grep the tree for `0.179` and `-0.071` and leave them
only where explicitly labelled as the withdrawn unmatched-inclusive
scheme.

### 1.3 B13 — verified; the draft's ratio is right, its range is loose

From `docs/scrna/klf12_raw_umi_evidence.tsv` (raw median library size):

| unit | median raw depth | ratio SZ25TE_HT : unit |
|---|---:|---:|
| SZ09TE_CNT | 17,079.0 | 4.04× |
| SZ09TE_HT | 16,572.0 | 4.16× |
| SZ10TE_CNT | 15,214.0 | 4.53× |
| SZ10TE_HT | 15,455.0 | 4.46× |
| SZ25TE_CNT | 14,503.0 | 4.75× |
| **SZ25TE_HT** | **68,953.5** | — |

So: **4.04× the next-deepest unit; 4.04–4.75× across the other five.** The
draft's "4.0–4.8×" is right to the stated precision; write 4.04–4.75×.

The stale `4.5×` appears at `docs/scrna/klf12_prior_finding.md:383` and
`:428`, both inside §1a (raw layer). The same file's `:515` uses 4.5–5.3×
correctly — that is §3, decontX-corrected column sums (61,403 against
11,692–13,511). §1a explicitly states the two quantities are different and
then borrows §3's number; that is the defect. The file is hand-written,
not generated, so this is a two-line prose edit.

### 1.4 B1 and B2 — verified

- **B1**: `src/dt_adoc/reporting/identifiability_figure.py:759` titles
  panel B *"What the current experiment can determine"*. The document that
  explains the figure opens by withdrawing exactly that reading: every
  fibre assumes one latent assignment carried through the whole design,
  which the current data are not. The string is baked into the committed
  SVG/PNG/PDF. Repair: scope the panel title and subtitle to the
  matched-unit assumption, regenerate all three assets, update the
  sha256s in `docs/identifiability/identifiability_metadata.json`.
- **B2**: `PERTURBATION_MARKER` at `identifiability_figure.py:92` holds
  only `independently_perturbed` and `bundled_perturbed`. The same module
  writes `perturbation_status` with six values, one of which —
  `set_alone_no_shared_readout` — applies to exactly one node (`IN_E2`)
  and silently gets no marker. The analysis text spends a paragraph
  defending that distinction; the figure erases it. Repair: give it a
  marker and legend entry, pin it with a test, regenerate.

Both are small. Both should be done **before** any v0.5 work, because
every downstream structural claim is read off these artifacts.

---

## 2. What the draft gets right, and should be kept verbatim

- **The objective.** "The smallest defensible mechanistic Digital Twin that
  preserves biologically meaningful causal degrees of freedom and can make
  different predictions for biologically different future interventions."
  Keep it as written.
- **`UNIDENTIFIED ≠ COLLAPSED ≠ ARTIFICIALLY_COUPLED`.** This is the
  single most valuable idea in the draft and it is genuinely missing from
  the repository. See §3.1.
- **Freeze v0.4, never overwrite it.** Already the repository's own
  convention (`models/superset/` is versioned; the staging
  `promotion_plan.tsv` already targets `v0.5.0` and explicitly forbids
  writing into v0.4).
- **Stop KLF12 refinement after the residual repairs.** Correct, and the
  escalated gate makes it more urgent, not less.
- **Maturity-dependent review rigor**, and the general rule that a valid
  reviewer finding does not automatically justify making a nonessential
  analysis more elaborate. Sometimes the repair is deletion. The KLF12
  arc — a BIC comparison fitted, hardened, then removed — is the
  precedent, and it was the right call.
- **Node-specific personalization contracts** rather than one universal
  RNA→probability mapping, and **`E_KLF12_HIGH` → `NO_MAPPING_CURRENTLY`**.
- **Construction / calibration / validation separation.** Already a
  repository contract; keep enforcing it.
- **Do not let available software determine the biological model.**

---

## 3. What I would change

### 3.1 Sections 5, 12, 13, 14, 19, 30 are already built — do not rebuild them

The draft proposes as future work several analyses the repository has
already produced, to a standard the draft's descriptions would not
improve on:

| Draft section | Already in the repository |
|---|---|
| §5 baseline v0.4 causal map | `docs/identifiability_analysis.md` (376 lines) + `docs/identifiability/node_classification.tsv`, all 59 nodes classified |
| §12 coupling classification | three nested partitions `P_label` 59 → `P_global` 35 → `P_design` 19, with the rule-collapse vs design-collapse distinction stated explicitly as "model repair vs protocol change" |
| §19 four levels of equivalence | the same three partitions plus a five-value observation status (`directly_measured`, `design_aliased_to_measured`, `indirectly_constrained`, `model_asserted_untested`, `latent_unresolved`) |
| §13/§14 PROFILE, PROFILE_v2 | `docs/profile_local_reimplementation.md` — both inspected at pinned SHAs, ideas reimplemented locally, assumptions-not-to-copy enumerated, `THIRD_PARTY_NOTICES.md` and `references/upstream_versions.yaml` complete. **The draft's architecture option E is the status quo.** |
| §30 minimum readout panel | `docs/identifiability/candidate_readouts.tsv`, `proposed_panel.tsv` — of 40 assayable unmeasured states, **34 change nothing**; only six help, each worth exactly one observation class. Four are on the LIF/GP130-STAT3/KLF12 axis (`E_LIF`, `E_GP130_STAT3`, `E_CD98_CD9`, `E_KLF12_HIGH`); the other two, `E_RECEPTIVE_SURFACE` and `OUT_EPITHELIAL_RECEPTIVE`, are downstream receptivity nodes sharing the `E_CD98_CD9` design class — the design class is the precise statement, not the pathway name |
| §24–§28 prospective arm ranking | `feat/design-alias-figure` — 112 candidate fifth arms generated mechanically and scored, unmerged |

**Change**: delete §5, §12, §13-for-PROFILE, §19 and §30 as *new work*.
Replace them with "read, re-verify after B1/B2, and extend along the one
axis that is missing".

That missing axis is the draft's own trichotomy. The existing partitions
are purely structural: they say *whether* two nodes are separable and *who
caused the merge* (rules vs arms). They do not say whether a merge is
**biologically defensible**. Adding one adjudicated column —
`BIOLOGICALLY_COLLAPSED` / `UNIDENTIFIED` / `ARTIFICIALLY_COUPLED` — to
`node_classification.tsv`, with a rationale and an evidence id per row, is
a day of work and is the entire contribution §12 was reaching for.

> **Standing caveat on every identifiability count below.**
> `docs/identifiability/identifiability_metadata.json` records
> `unit_assumption`: **"MATCHED-UNIT (hypothetical). Every fibre, observation
> class, information status and proposed-panel count assumes one biological
> unit carries a single latent assignment through every arm and assay. The
> current data do not provide that … These counts therefore describe what a
> matched-unit design of this shape could identify, and are NOT claims about
> what the current data identify."** `identifiability_analysis.md` opens by
> withdrawing the current-data reading explicitly.
>
> The caveat's scope is exactly the enumeration `unit_assumption` gives —
> **fibres, observation classes, information statuses and proposed-panel
> counts**. In this document that means **8 of 32**, the two current
> observation classes, the per-relay "classes if measured" counts, and "only
> six readouts help": all **matched-unit-conditional**. An earlier revision
> used them caveat-free — the same overclaim §1.4 raises as blocker B1
> against the figure.
>
> **59→35→19 is not in that scope and is not conditional.**
> `identifiability_analysis.md:20-22` exempts it in its own words: "What is
> unaffected is the structural half, which never depended on pairing: the 59
> named nodes, the 35 native Boolean functions". `P_design` = 19 is likewise
> a partition over the arms' value-vectors, which no pairing assumption
> enters. The relay rules and istates and the 0.82 arithmetic are structural
> for the same reason. (A later revision briefly listed 59→35→19 as
> conditional; that was wrong and is withdrawn.)

### 3.2 Promote §11 (the interface relays) to the top of the biological work

The draft places the relay question eleventh. The repository's own
analysis makes it **the binding constraint on everything downstream**, and
the plan should be reordered around it.

What the four relays are, read from `network.bnd`:

```
Node X_INTERFACE_SPP1_RELAY        { logic = X_INTERFACE_SPP1_RELAY; }
Node X_INTERFACE_REDUNDANT_RELAY   { logic = X_INTERFACE_REDUNDANT_RELAY; }
Node X_INTERFACE_ANTIADHESIVE_RELAY{ logic = X_INTERFACE_ANTIADHESIVE_RELAY; }
Node X_MECHANICAL_STRESS_RELAY     { logic = X_MECHANICAL_STRESS_RELAY; }
```

`logic = self` is a constant. Each is a Bernoulli coin flipped once at
`t = 0` from a hand-typed `istate` in `baseline.cfg` (0.70, 0.40, 0.20,
0.30). They are not mechanisms, not dynamics, and not measurable — the
node dictionary says so in its own words ("bounded stochastic
initialization").

Three facts follow, all already established in the repository:

1. The headline endpoint is arithmetic on two typed numbers. With
   `E_KLF12_HIGH` off, `OUT_STABLE_ADHESION` reduces by enumeration to
   `X_INTERFACE_SPP1_RELAY or X_INTERFACE_REDUNDANT_RELAY`, giving
   `1 − (1−0.70)(1−0.40) = 0.82`, which the converged simulation
   reproduces to three decimals (R41b: 0.820340, MC sd 0.000120).
   **And the repository has already scored that against the data**: R41b
   records the magnitude as disagreeing, 0.820 lying above the Wilson 95%
   CI [0.27, 0.68] for the observed 9/19 (§3.6). So the relays are not only
   unidentifiable — the value they produce is measurably too high.
2. **Measurement alone cannot close the gap** — *under the matched-unit
   assumption*. Adding every assayable readout to every proposed arm reaches
   8 of 32 observation classes.
   The remaining factor of four is carried by the four relays.
   (`identifiability_analysis.md:252-254` says "carried by" and shows no
   arithmetic reconciling a factor of four with four independent binary
   relays, which would span 2⁴ = 16 configurations. The gap is in the
   source; it is reported here as the source states it and should be
   resolved when that document is next regenerated.)
3. Therefore identifying the interface is a **model repair first**, and a
   measurement only afterwards. No new assay and no new arm changes this.

**The four relays are not equivalent, and `node_classification.tsv` says
which one to look at.** Reading the four rows directly:

(class counts matched-unit-conditional; `phenotype_inert` and `assayable` are not)

| relay | `phenotype_inert` | `assayable` | classes if measured, proposed arms |
|---|---|---|---:|
| `X_INTERFACE_SPP1_RELAY` | false | false | 8 |
| `X_INTERFACE_REDUNDANT_RELAY` | false | false | 6 |
| `X_MECHANICAL_STRESS_RELAY` | false | false | 6 |
| `X_INTERFACE_ANTIADHESIVE_RELAY` | **true** | false | **10** |

The anti-adhesive relay would resolve more observation classes than any
assayable node reaches — 10 — while being recorded `phenotype_inert = true`.
The current encoding has **separated information from consequence** on that
branch.

**That is a diagnostic, not yet a reason to repair the barrier branch
first** (project lead, in session, 2026-09-15). The relay is unassayable and
artificial: its 10 classes are what an *unmeasurable* quantity would buy,
which is a statement about the encoding, not a route to an experiment. What
it licenses is a question, not a plan — is reconnecting the real barrier
states (`E_PODXL`, `E_MUC1_BARRIER`, `E_DAG1_FULL`, which share one design
class) to attachment or retention **evidence-supported**, and does it change
any intervention? That must be established before the branch is called the
first repair.

Separately, `X_MECHANICAL_STRESS_RELAY` gates only through
`IN_ER_STRESS_EXCESS` and `IN_HIGH_ECM_STIFFNESS`, and **both are `FALSE`
in every one of the six recorded arms** (they are `TRUE` only in
`excess_er_stress.cfg`, `high_ecm_stiffness.cfg` and their challenge
variants, none of which carries a recorded observation). So within the
recorded design that relay cannot move any readout, even though
`phenotype_inert` — a global property over all free-variable assignments —
records `false`. Whether the two inert bits are exactly the unexplained
factor of four is a **hypothesis this document does not settle**: it is
deduced from the rules, not enumerated.

**Decompose it computationally before any of it becomes a v0.5 success
criterion.** `identifiability.py` already enumerates; the missing analysis
is per-relay and per-combination attribution — how much of the residual
ambiguity each relay carries alone, and which combinations carry the rest.
"8 of 32, factor of four, blame the relays" is the right diagnosis at the
wrong resolution to plan a repair against, and Gate 3b should open with
that decomposition rather than assume it.

**Change**: the interface is not item 11 on a list of modules. It is the
first structural repair after the cheap falsifier, and the yardstick for
whether v0.5 was worth building. Adding intracellular nodes while the
interface remains four coin flips would raise node count and leave the
residual ambiguity untouched.

### 3.3 The model has no rates at all — this is the unstated blocker

`grep -c "rate_up\|rate_down" network.bnd` → **0**. Every transition rate
in v0.4 is the MaBoSS default. The model has no time semantics beyond
"converged or not".

This silently invalidates several draft sections:

- §18's "rate modification" perturbations are vacuous — there is nothing
  to modify.
- §21's `RATE_MODIFIER_CANDIDATE` mapping class has no target.
- §32's "transition rates" calibration has no parameters.

It sits alongside `docs/endpoint_convergence_finding.md`, which attributes
the anomalies to the readout horizon — endpoints read ~4000× before
convergence. Zero rates and that horizon gap are compatible and both bear on
when anything is read, but the finding does not name the absent rates as the
cause, and this document does not either.

**Change, revised after project-lead review in session (2026-09-15).** An earlier
revision of this document made *introducing relative rates* a v0.5
prerequisite. That was not the most parsimonious reading, and the
repository's own artifact says so.

`node_classification.tsv` already computes a `dependency_depth` per node,
ranging 0 to 11, and the two nodes at issue are pinned together on that
axis:

| node | `dependency_depth` | `effective_function_id` | `design_state_id` |
|---|---:|---|---|
| `S_DECIDUALIZED` | 5 | `OUT_STROMAL_DECIDUALIZED` | `E_ANXA2_ACTIN` |
| `S_IGFBP1` | **6** | `OUT_STROMAL_DECIDUALIZED` | `E_ANXA2_ACTIN` |
| `S_PRL` | **6** | `OUT_STROMAL_DECIDUALIZED` | `E_ANXA2_ACTIN` |

Same depth, same function, same class. So the candidate minimal repair is a
*rule* difference — for instance an intermediate on the PRL branch — rather
than a fitted rate.

**`dependency_depth` is a graph metric, not a proof of temporal ordering,
and an earlier revision of this section overstated it.** In MaBoSS's
continuous-time kinetics a deeper node can activate earlier than, or
together with, a shallower one: initial states, AND versus OR structure,
alternate paths and feedback all bear on the transient, and depth bounds
none of them. The correct procedure is therefore three-step and its middle
step is empirical:

1. propose rule/topology separations that could produce IGFBP-1 before PRL;
2. **simulate the transient and test whether that ordering actually emerges,
   and emerges robustly** — across seeds, trajectory counts, initial
   conditions and the admissible rule variants, not in one run;
3. only if no admissible rule variant reproduces the ordering, consider a
   relative rate.

Revised position: **rate-free by default, and ordering demonstrated by
simulation rather than inferred from topology.** If rates are ever declared
they stay relative: AGENTS.md forbids inventing physical time units, so the
admissible claim is an **ordering**, never a delay in hours.

What remains true from the original observation is the negative half: with
zero rates declared, the draft's §18 rate perturbations, §21
`RATE_MODIFIER_CANDIDATE` class and §32 rate calibration have no target
today, and none should be created speculatively. `docs/concordance_analysis.md`
already frames a result this way — its claim ceiling reads **"Ordering
only"** (`concordance_analysis.md:105`) — and v0.5 should adopt that as the
general contract for anything temporal. (An earlier revision of this
document paraphrased that as "reproduces an ordering, not the regimen".
No such string is in the file, and the second half inverts it: the regimen
mismatch was repaired and now matches, `concordance_analysis.md:175-176`
and `:242`.)

### 3.4 The strongest available constraint is in-house, unused, and falsifies v0.4 today

`OM-016` in `config/observation_model_map.tsv` records ADOC's own ELISA
data:

| day | basal IGFBP-1 | basal PRL |
|---|---|---|
| 0 | detected 4/5 units, 37.90–551.26 pg/mL | **0/6** |
| 3 | 5/5, four of them >1000 pg/mL | 1/6, max 113.60 pg/mL |
| 6 | — | 3/6 |

The row's `claim_ceiling` states it as an ordinal onset order and as a
**falsifiable structural requirement on candidate models**: any model in
which `S_IGFBP1` and `S_PRL` are logically and dynamically identical is
inconsistent with it. In v0.4 both are literally `= S_DECIDUALIZED`, with
no rate declaration. **v0.4 fails a falsifier the repository already
holds.**

It is currently `activation_status: rejected` for two stated reasons:
(a) `config/protocols.yaml` has no protocol representing the mid-cocktail
day-3 state (`OM-011`), and (b) the model structurally forces synchrony.
Both are repairs inside v0.5's scope, and neither needs new data.

Independent human evidence supports the split rather than merely
permitting it: in human endometrial stromal cells TGFβ1 suppresses both
analytes but by different routes — SMAD4 knockdown showed the effect on
PRL release is SMAD-dependent while the effect on IGFBP-1 is
SMAD-independent (Kane et al., PLOS One 2010). So `S_PRL ≡ S_IGFBP1` is
`ARTIFICIALLY_COUPLED` in the draft's taxonomy, not `UNIDENTIFIED`.

**But that evidence does not make TGFβ the mechanism of the ADOC
divergence, and an earlier revision of this document slid between the
two** (project lead, in session, 2026-09-15). Keep them apart:

- *PRL and IGFBP-1 must be separable* — established, by ADOC's own ELISA
  (`OM-016`) and independently by Kane 2010.
- *TGFβ/SMAD generates the ADOC temporal difference* — **not established.**
  Nothing measures TGFβ in these chips, and a mechanism that can dissociate
  two outputs under exogenous ligand is not thereby the mechanism operating
  in an untreated maternal phase.

The minimal v0.5 repair is therefore structural and mechanism-agnostic:
`S_DECIDUALIZED` branching to `S_IGFBP1` and `S_PRL` through *different*
rules, with the PRL branch reached later. `S_TGFB_CONTEXT` stays what the
staging table already makes it — a candidate, admissible as an uncertain
rule variant — and is promoted only if evidence specific to ADOC warrants
it. Its staged confidence is 4, the lowest in the set; that is an argument
for holding it as a variant, not for promoting it as canon.

**Change**: make "de-alias `S_PRL` from `S_IGFBP1`, add a day-3 maternal
protocol stage, and make `OM-016` evaluable" the **first concrete v0.5
deliverable**.

**`OM-016` is construction evidence for v0.5, not validation of it.** An
earlier revision of this document called it a "held-out validation
constraint". That was wrong and would have breached the separation
AGENTS.md requires and §2 endorses: the same row cannot both motivate the
repair (§3.4 above, §3.8's admission test 3) and then independently test
it. Once v0.5 splits `S_PRL` from `S_IGFBP1` *because* of `OM-016`, the
row's agreement with v0.5 is a consistency check, not evidence.

What `OM-016` legitimately does, and what it does not:

- **Does**: falsify v0.4, which forces the two synchronous. That is a real
  and checkable result and needs no new data.
- **Does**: constrain the admissible v0.5 model class to those that can
  express a non-synchronous ordering.
- **Does not**: fix the ordering's direction independently. The document
  names no source for that other than `OM-016` itself and the external
  TGFβ1/SMAD dissociation (Kane 2010), which is mechanism, not an ADOC
  measurement.
- **Does not**: serve as held-out validation of the repair it motivated.

**This is settled, not an open question** — decided by the project lead in
session on 2026-09-15 and relayed here. It is *not* a recorded `aih consult`,
and the harness ledger holds no consultation for this repository; the
provenance is the session, and is stated that way rather than dressed as an
independent review.
`OM-016` is used as **construction evidence, including its direction**:
v0.5 is constrained to permit IGFBP-1 earlier than PRL, and that use is
labelled construction. The alternative an earlier revision offered — hold
`OM-016` back and build the split from the TGFβ literature so the row can
validate it — is scientifically worse, because the TGFβ evidence
establishes neither the mechanism nor the direction of the ADOC divergence.
Building on the weaker evidence to preserve the stronger one as a test
would be a trade that buys a validation term by making the model worse.

Independent validation therefore comes **prospectively**, from data not yet
collected, under a pre-registered prediction. That is the honest position
and it costs the plan one validation term it never legitimately had.

### 3.5 The prospective design section is asking the wrong question first

The draft (§24, §29) treats the fourth arm as the decision. The
unmerged design-alias work already computed the answer under the declared
four-arm plan, and it is uncomfortable:

- **The planned anti-SPP1 arm isolates an input the design cannot read.**
  `design_alias_metadata.json` records `IN_ANTI_SPP1` under
  `inputs_isolated_without_a_shared_readout` and
  `hormone_treated_anti_spp1` under `planned_not_recorded`: the plan moves
  the input on its own, but neither anti-SPP1 cfg carries a recorded
  observation. As declared, *the fourth arm perturbs a mechanism the
  design cannot read.* Attaching a readout to it is a separate decision
  the plan has not made. (The `perturbation_status` token
  `set_alone_no_shared_readout` in `node_classification.tsv` describes the
  *recorded* design and is held there by exactly one node, `IN_E2` — see
  §1.4. The two are the same property computed over different arm sets,
  and must not be quoted interchangeably.)
- **By raw class gain the winner is HAND2 loss (+5, 19 → 24)**, not
  anti-SPP1.
- **By separation of the measured analytes, only eight of 112 candidates
  score at all** (`candidates_separating_two_measured_nodes: 8`), and they
  are **two distinct manipulations across four backgrounds each**:
  **minus E2** (four rows, gain 3) and **minus cAMP** (four rows, gain 2).
  Every one separates the same pair, `E_PAEP | S_IGFBP1`. No other
  manipulation splits PAEP from IGFBP-1, and none of the eight has a
  committed cfg.
- The plan also silently **drops** the E2-priming arm the recorded design
  has. Net 19 classes either way — but different classes. Reporting the
  count alone hides the trade.

On top of that, the SPP1 route's functional evidence is largely porcine
and murine (SPP1–αvβ6/αvβ3 trophectoderm adhesion; ITGAV siRNA in porcine
trophoblast), with one human in-vitro functional study; ADOC's own SPP1
claim comes from scRNA-seq ligand–receptor communication inference, which
is co-expression, not causation.

**No molecule is privileged, including anti-SPP1** (project lead, in
session, 2026-09-15). The candidate space is a set of *causal axes*, and membership
in it is not a recommendation:

| axis | candidates | in v0.4 today? |
|---|---|---|
| GP130/STAT3 | LIF neutralisation, STAT3 inhibition | `E_LIF`, `E_GP130_STAT3` present |
| ″ | IL11 / IL11R blockade | **no** — `X_IL11` is a staged candidate only |
| stromal decidualisation | cocktail minus cAMP, BMP-receptor inhibition | `IN_cAMP`, `S_PKA`, `S_BMP2` present |
| ″ | TGFβ/SMAD | **no** — `S_TGFB_CONTEXT` staged, confidence 4 |
| ″ | COX2 / PGE2 axis | **not in the executable model.** `X_PGE2_HIGH` and `S_PTGS2` appear only in `context/references/adoc-maboss-model-specification.user-provided.md:440,469` — a user-provided spec, never promoted; zero occurrences in `network.bnd` or `complete_nodes.tsv` |
| interface/adhesion | SPP1-axis blockade, integrin/ECM | `IN_ANTI_SPP1`, `E_ITGAVB3_5` present |
| orthogonal calibration | TLR3 activation | **no node, and no candidate row.** Zero occurrences in `network.bnd`, `complete_nodes.tsv`, the candidate tables and the staged set; it appears only as two literature seeds, `context/literature/searches/adhesion_routes_seed.tsv:32,77` |

That column is the cost nobody has priced. A perturbation whose target the
model does not contain cannot be ranked by any of the machinery here until
the node is promoted through §3.8's admission test — and TLR3 in particular
would mean importing an inflammatory module v0.4 has no trace of, for a
perturbation that is explicitly not a therapeutic candidate. Whether that
is worth it is a real question, not a foregone yes.

**Two axes of value, never one score.** A perturbation's *model-identification*
value and its *translational* value are different quantities, and the
immediate objective is the first. TLR3 activation is the clean example of
high identification value with no contraceptive plausibility; a clinically
attractive target that moves only one endpoint is the converse. Ranking
must report both and combine neither.

**Rank `perturbation × readout`, never a molecule alone.** The repository
already proves why: `IN_ANTI_SPP1` is isolated in the planned design and
still unreadable, because no readout is attached to either of its cfgs. The
same perturbation with and without a mechanistic readout are different
experiments with different information content.

**Change**: reframe §24–§29 around a distinction the draft never draws and
the repository's tooling already supports —

> **Maternal-phase arms are cheap. Challenge arms cost embryos.**

The published ADOC paper reports 39 human blastocysts total, 9/19 adhering
in the hormone-treated arm and 1/8 under mifepristone. A challenge arm is
embryo-limited and statistically thin. A maternal-phase-only arm needs no
embryos at all, and *every* candidate that separates the measured
analytes — minus-E2 and minus-cAMP among the 112 scored candidates, and
prospectively a TGFβ1/SMAD manipulation, which is *not* among them — is a
maternal-phase manipulation.

So the design question splits in two, and should be answered separately:

1. **Which maternal-phase arms de-alias the molecular readouts?**
   (cheap, embryo-free, directly attacks `P_design` and `OM-016`)
2. **Which single challenge arm is worth an embryo allocation?**
   (expensive, and must have a readout attached or it is unreadable)

The design-alias tool already computes (1) — it ships a
`maternal_phase_only` variant giving 17 classes, under which both
headline conclusions are unchanged.

### 3.6 The interface dynamics are curated, and adjudicated out of scope

The draft asks (§31) whether richer adhesion measurements are feasible. Two
earlier revisions of this section got this wrong in opposite directions —
first calling the measurements a free observable, then calling them
uncurated. **Both were wrong. `docs/results_reproducibility_matrix.tsv`
already carries them, with figure anchors, printed sample sizes and a
recorded adjudication:**

| row | figure | quantity | verdict | binding limitation |
|---|---|---|---|---|
| R41a | Fig. 6C | human **attachment fraction**, 9/19 = 0.474 (onset 34.1 ± 12.2 h recorded as context only) | **`disagreement`** | `timing;calibration` |
| R34 | fig. S5A | **mouse** onset, 59.3 ± 29.5 h, n=15 | `not_assessable` | `continuous_spatial;topology` |
| R35 | Fig. 5C | spreading area, n=8 embryos, 4 chips, 4 donors | `not_assessable` | `continuous_spatial;topology` |
| R37 | Fig. 5E,F,G | TE spread, nuclei aligned in focal plane | `not_assessable` | `continuous_spatial;topology` |
| R46 | Fig. 6F,G | Z-displacement, unit = **nucleus, not embryo** | `not_assessable` | `continuous_spatial;assay_design` |

**The four rows are not adjudicated identically, and the distinction
matters.** R46 carries the decisive sentence — **"Permanently out of scope
for a Boolean logical model, not pending work."** R34, R35 and R37 carry a
different one: *"Embryo lineage identity and position. No GATA3/GATA4/OCT3-4
node and no geometry."* That is a missing-node-and-geometry adjudication, not
a permanence claim. Both sit under `continuous_spatial`, and the class-wide
"permanently out of scope" wording appears in nine rows elsewhere in the
matrix — but it is not what R34, R35 and R37 individually say. R34 adds that
timing is
"additionally blocked by `calibrated_physical_time: false`", which
`config/calibration.yaml:88` confirms, with `duration_units: relative_only`
at `:60`.

**So Gate 3b cannot be scored on morphodynamics, and no amount of curation
changes that.** ΔZ, spreading and TE alignment are continuous and spatial;
the repository has already judged that a Boolean logical model is the wrong
formalism for them, and that judgement is a decision already taken, not an
omission to repair. This is independent support for the per-relay
disposition §3.2 now requires: the mechanical and morphodynamic parts of the
interface point at **PhysiBoSS, or at staying outside the model entirely**,
not at more MaBoSS nodes.

What survives for Gate 3b is narrower and worth stating exactly.

**Attachment fraction is in scope, and the matrix scores it twice — once at
each horizon.** R41a and R41b are the same observation (Fig. 6C, 9/19 =
0.474, `SOFIA-ADH-002`, `dt_node_or_proxy = OUT_STABLE_ADHESION`) evaluated
at two horizons, and only reading both gives the right picture:

| row | `horizon_class` | simulated | verdict | `binding_limitation` |
|---|---|---:|---|---|
| R41a | `declared` | **0.000000** | `disagreement` | `timing;calibration` |
| R41b | `converged` | **0.820340** | `qualitatively_reproduced_direction_only` | `calibration` |

> **The executed converged horizon is 25.0 dimensionless MaBoSS time per
> phase.** `src/dt_adoc/concordance/simulate.py:89` applies
> `CONVERGED_PHASE_HORIZON = 25.0` globally to converged runs and
> `docs/concordance/run_settings.json` records
> `provenance.converged_phase_horizon: 25.0`. The `max_time = 30.0` carried by
> the matrix's converged rows is **stale metadata**: R43b's own note says so —
> "this row's `max_time` column still reads a stale 30.0, which predates this
> analysis and is not what was run" — and adds that
> `endpoint_convergence_finding.md` records the endpoint as stable from 20 to
> 60, "so nothing numeric turns on it". A previous revision of this document
> reported this as an unresolved disagreement between two artifacts. It is
> not: it is a metadata cleanup for the matrix, and no result changes.

R41a's disagreement is a **convergence artifact**, and its own note says so:
"the endpoint is read ~4000× before its logical fixed point … more
trajectories tighten the interval around the wrong value". R41b is the row
that carries the real verdict, and it is the sharper one:

> "Direction agrees (HT > basal). **MAGNITUDE DISAGREES: 0.820 lies above
> the Wilson 95% CI for 9/19.** And 0.820 is not a fitted quantity at all —
> it equals 1−(1−0.70)(1−0.40) = 0.82 exactly, from the two hand-set relay
> istates configured in `baseline.cfg`, so its entire graded content is two
> typed-in numbers."

**That is §3.2's argument about the relays, already in the repository, with
a statistical test attached** — the observed Wilson interval is [0.27, 0.68]
and the model sits outside it, at a value that is arithmetic on two
configured constants. An earlier revision of this section cited only R41a
and therefore reported the convergence artifact as the verdict, missing the
converged row that actually indicts the relays.

Note also that the 34.1 ± 12.2 h appears in R41a only as `observed_numbers`
and `time_point` context; **no row in the matrix compares a simulated onset
to anything.** An earlier revision read R41a's verdict as being about onset.
It is not.

Two consequences, and they pull in opposite directions:

- the error the interface repair must eliminate shows up in the attachment
  fraction, and at the converged horizon the matrix attributes it **to the
  relays themselves**: R41b's 0.820 is 1−(1−0.70)(1−0.40) on the two
  hand-set istates, and it sits above the Wilson 95% CI for the observed
  9/19. (The separate declared-horizon error in R41a *is* independent of the
  relays — it is the readout-horizon problem of
  `endpoint_convergence_finding.md` — and must not be confused with this
  one. An earlier revision of this bullet described only that one.);
- **agreement there would not be validation.** R41a's `circularity` column
  reads "fitted: role=calibration in `config/calibration.yaml`, so
  agreement would be calibration agreement"; R41b's adds that its converged
  value "is compared against fits made at the SHORT horizon, which are
  superseded". Gate 3b must not score itself on reproducing a number it was
  fitted to, and must not treat R41b's direction-only agreement as more than
  that.

**Ordinal onset comparison is blocked, for reasons that have nothing to do
with R41a's verdict**: `config/calibration.yaml:88` sets
`calibrated_physical_time: false` and `:60` sets `duration_units:
relative_only`, no
row simulates an onset at all, and the untreated arm is 0/12 — no
attachments, so no onset exists there to order against.

**The wider number frames v0.5 — but only after it is split.** Of the 60
rows in that matrix, **51 are `not_assessable`**, three direction-only, one
partial, one a disagreement, four `circular_by_construction`. The digital
twin cannot be assessed against the large majority of its own paper's
results.

51 is **not** v0.5's target, and quoting it as one would overstate the
reachable work about threefold. Splitting by `binding_limitation`:

| subset | count | reachable by a Boolean model? |
|---|---:|---|
| `not_assessable` carrying `continuous_spatial` | **36** | **no** — the formalism decision of §3.6 |
| `not_assessable` not carrying `continuous_spatial` | **15** | **yes, in principle** |

The 15 are nameable: R11, R12c, R17, R19, R20, R21, R22, R23, R24, R25,
R27, R33, R43a, R48, R54. Ten carry `topology` in `binding_limitation`, but
**reading their notes rather than their codes changes the picture entirely**,
and in a way that is worth more than the interface repair:

**The stale scRNA-object claim appears in eleven rows: R17 through R27
inclusive.** Each note reads *"The repository does NOT hold the paper's
28,212-cell annotated object. SOFIA-RDS-001 is a different 61,843-cell
intermediate."* But `config/scrna_observation_map.tsv` records that object as
held — ArrayExpress E-MTAB-15842, `seurat_object.rds`, 28,212 cells, sha256
`504a674db978779b03d02a73224ee425ec46efbf411c148b0903ceef15389a1a` — and the
entire KLF12 workstream ran against it. The matrix predates that acquisition
and was not revisited.

**Nine of the eleven are inside the fifteen** (R17, R19, R20–R25, R27).
**R18 and R26 are outside it** — both `topology;continuous_spatial`, so
formalism-limited whatever their provenance says — but their stale claim
should be corrected too, because a wrong statement about what the repository
holds is wrong regardless of whether fixing it changes a verdict.

**Provenance correction removes one blocker; it does not clear a row.** The
remaining limitations are what decide each row, and they are of six kinds.
Classifying the fifteen by what `binding_limitation` actually records:

| row | stale claim | remaining blocker types |
|---|---|---|
| R20, R21, R22, R23 | yes | topology, assay design, calibration |
| R17 | yes | topology, missing provenance |
| R19, R24 | yes | topology |
| R27 | yes | topology, assay design |
| R25 | yes | calibration, assay design |
| R11 | no | calibration, assay design |
| R12c | no | timing/dynamics, calibration, missing provenance |
| R33 | no | topology, assay design |
| R43a | no | timing/dynamics, calibration |
| R48 | no | topology, calibration |
| R54 | no | assay design |

**R20–R23 are the strongest re-adjudication candidates, and that is not the
same as clearing.** They are the only stale rows with existing comparators —
`OM-009`/`OM-010`, `P1-EPI-STATE`/`P1-STR-STATE`, against
`OUT_EPITHELIAL_RECEPTIVE`, `S_BMP2` and `S_PRL;S_IGFBP1`. But those mappings
are `activation_status: reported_only`, `calibration_role: diagnostic`,
`confidence: low`, and their claim ceilings read **"Diagnostic only. Not
usable to validate …"**; the matrix additionally records topology, assay-design
and calibration limits on all four. So the honest statement is: correcting
provenance removes the object-availability blocker, and **every remaining
limitation must then be re-evaluated on its own terms**. An earlier revision
of this document said these four "may clear on provenance correction alone",
which the mapping table does not support.

Re-adjudicating all eleven against the object now held remains the cheapest
move in the plan, and it belongs in Gate 1 beside the roadmap correction
(§3.9) that fixes the same staleness. What it buys is an accurate record of
which blockers are real — not a count of rows that become assessable.

**None of the fifteen is interface-blocked**, which is why this metric
belongs to v0.5 as a whole and not to Gate 3b. Gate 3b's own criterion is
structural; see §5.

One of the 15 is worth naming separately: **R12c is the PRL onset row**
("basal PRL heterogeneous LATE onset … 0/6, 1/6, 3/6 against a 10 pg/mL
limit"), `timing;calibration;missing_provenance`. It is `OM-016`'s
counterpart in this matrix, so Gate 3a's repair has a specific row it
should flip, not merely a constraint it should satisfy.

One honesty note, corrected. An earlier revision said the matrix used
"permanently out of scope" for R46 alone, making the class-wide reading this
document's generalisation. That understated the matrix: the phrase
**"Permanently out of scope for a Boolean logical model" appears verbatim in
nine rows** — R40, R45, R46, R47, R49, R50, R51, R52, R53 — five of which
(R40, R45, R46, R47, R49) continue ", not pending work"; R50–R53 stop at the
full stop. The adjudication is the matrix's own across most of the
`continuous_spatial` class, not an inference from one row, which makes §6
decision 3 a question about *reopening a standing decision* rather than
about endorsing a generalisation. And the `binding_limitation` column is already a machine-readable
inventory of *why* each row fails, which Gate 1 should read before Gate 2
adjudicates anything.

### 3.7 Framework review: narrower than the draft, and one tool it misses

Verified 2026-09-15 via the GitHub API and each project's own
documentation:

**The default is MaBoSS + local ADOC Python.** Everything below is a
methodological reference until a concrete capability defeats a local
implementation; nothing below is a component of the architecture. Push
dates and licences were read on 2026-09-15 and are recorded for provenance,
not as a live gate — while the repository is private and every entry is
read-and-borrow, licensing is a deferred note (one exception, marked).

| Tool | Last push | License | Position |
|---|---|---|---|
| **MaBoSS / PyMaBoSS** | active | — | **KEEP** — the only runtime dependency |
| **PROFILE** | 2025-12-02 | BSD-3 | **ALREADY BORROWED** — reimplemented locally; no change |
| **PROFILE_v2** | 2025-11-05 | BSD-3 | **ALREADY BORROWED** (graded target engagement); no change |
| **BoNesis** | 2026-09-01 | CeCILL-2.1 | **REFERENCE / ESCAPE HATCH IF COMBINATORIAL** — declarative synthesis of Most Permissive BNs. Explicit local variants are simpler for a handful of rules; revisit only if the admissible set stops being enumerable by hand. |
| **AstroLogics** | 2026-09-08 | none declared | **REFERENCE / BENCHMARK** — MaBoSS-native ensemble analyser (dynamical distance, clustering, DNF logic-feature extraction). Inspect so no methodological idea is missed; reproduce the needed subset locally. |
| **EnsembleMaBoSS** | — | — | **OPTIONAL, CURRENTLY UNNECESSARY** — built for heterogeneous *cell populations*, not epistemic uncertainty over topologies; and a Python loop over a modest variant set is clearer. |
| **caspo** | 2026-02-10 | GPL-3.0 | **METHODOLOGICAL REFERENCE** — its model-discrimination experimental design is the idea worth having; implement the criterion locally. |
| **CellNOptR** | 2025-11-24 | none declared | **DEFER** — relevant only once prospective perturbation-response data exist. |
| **CellNOptR-MaBoSS** | **2020-02-13** | GPL-3 | **REJECT** — six years stale. |
| **scBONITA** | 2023-07-26 | MIT | **IDEA ONLY** — stale, and transcript-derived rule inference is not biological truth. |
| **scBOLT** | — | **none — "internal research use"** | **REJECT, and do not run it.** The one licensing carve-out: this restricts *use*, not distribution, so it is not available even privately. |

An earlier revision of this document had BoNesis inside the recommended
stack and called AstroLogics "the right tool". That inverted the burden of
proof: the repository already ships `rule_variants.tsv`,
`uncertain_rule_variants.yaml` and `ensemble_definition.tsv`, and iterating
a handful of admissible variants through PyMaBoSS is a loop, not a
synthesis problem. The table above is now the single position.

Recommended architecture:

```
v0.5 canonical model
    +  a small EXPLICIT set of admissible rule/model variants
           (rule_variants.tsv, uncertain_rule_variants.yaml — both already exist)
    ↓
ADOC-specific local Python   (personalization, perturbation and variant
                             generation, standardized execution)
    ↓
MaBoSS / PyMaBoSS            (incumbent, unchanged, the only runtime dependency)
    ↓
ADOC-specific local analysis (perturbation signatures, model comparison,
                             uncertainty summaries, perturbation × readout
                             discrimination scoring)

ESCAPE HATCHES, not components:
    BoNesis      — only if admissible variants become combinatorial
    AstroLogics  — only if local distance/clustering/DNF-feature analysis fails
```

A researcher should be able to explain any prediction by reading this
repository alone. That is the acceptance test for the architecture, and it
is the reason the two escape hatches sit outside the diagram.

**Deferred licensing note.** DT_ADOC ships no LICENSE file. That matters
for distribution, not for reading and borrowing from a private exploratory
repository, so it is deferred — and returns in full if release or
publication is on the table. The one thing not deferred is scBOLT, above.

### 3.8 Reject §6–§10 as scoped

"Build one complete biological candidate universe", "deeply review every
current node as well as every proposed node" across ~19 attributes for 59
existing plus 14 staged nodes is roughly 1,400 adjudications. It is the
most expensive item in the draft and the least connected to the binding
constraint.

The staged deep-research nodes are already triaged:
`context/literature/staging/deep_research_adhesion_model_2026-09-11/promotion_plan.tsv`
routes each file to a canonical target with a stated blocking review, and
already names `models/superset/adoc-literature-superset-v0.5.0/` as the
destination. The 14 candidates carry confidence scores from 9
(`S_BMP_SMAD`, `S_FOXO1`, `S_WNT4_CTNNB1`, `E_SOX17`) down to 4
(`S_TGFB_CONTEXT`) and 5 (`S_AKT_EXCESS`, `S_ERK`).

**Change**: replace the exhaustive review with an **admission test**. A
node enters v0.5 only if it does at least one of:

1. breaks a coupling the adjudication marked `ARTIFICIALLY_COUPLED`;
2. is the mechanism a replaced or constrained interface free variable needs;
3. makes an existing rejected observation row evaluable;
4. is required by a perturbation the prospective design will actually run;
5. is a **necessary causal or temporal intermediate** whose omission would
   force a biologically false direct edge, destroy an observed temporal
   ordering, or make two interventions that should differ become
   artificially identical.

and then passes **both** parsimony filters:

- it does not duplicate an abstraction already adequate for its purpose;
- adding it changes at least one reachable dynamic, intervention or
  observable prediction. A node that changes nothing is not admitted, however
  well evidenced.

**A node admitted is not a mechanism asserted.** Applied to the staged set,
what test 1 and test 5 promote is the **separation of `S_PRL` from
`S_IGFBP1`** — the structural repair. `S_TGFB_CONTEXT` is *not* thereby
promoted: §3.4 establishes that TGFβ/SMAD is not shown to be the mechanism
of the ADOC divergence, so it remains an **admissible candidate rule
variant**, and earns canonical promotion only on evidence specific to ADOC.
An earlier revision of this section said the test "promotes
`S_TGFB_CONTEXT`", contradicting §3.4; that is withdrawn.

Likely to pass on test 1 (PGR/IHH/BMP decomposition): `S_BMP_SMAD`,
`S_FOXO1`, `S_WNT4_CTNNB1`. Deferred until a test is met:
`E_JAG1_NOTCH3`, `E_ESR1_ACTIVITY`, `S_AKT_EXCESS`, `S_ERK`. Nodes that
fail every test are recorded as deferred with the reason — an auditable
line, not a 19-attribute dossier.

#### The evaluation-only route, and why it is necessary

Test 4 is circular as stated, and the circularity has a direction: a
perturbation cannot be ranked until its target is represented, so
**the admission rule as written silently favours perturbations v0.4 already
contains**. `IN_ANTI_SPP1` is in the model; IL11 is staged only, COX2/PGE2 exists
solely in a never-promoted user-provided spec, and TLR3 only as two
literature seeds (§3.5). Left uncorrected, the design analysis would conclude that the
best experiments are the ones the previous model version happened to encode.

So a candidate axis may receive the **minimal temporary representation
needed to evaluate its information value**, under explicit conditions:

- it lives in the **candidate/variant layer, never in canonical v0.5**;
- it is built to be *sufficient for ranking*, not to be right — the
  smallest structure that lets the discrimination scorer ask whether
  perturbing it separates models;
- **it is never a single convenient rule.** Where the biology is uncertain,
  the axis is evaluated across the **smallest plausible family of temporary
  representations**, and the reported result is whether its information value
  is *robust to that uncertainty*. An axis that looks valuable under one
  hand-chosen rule and worthless under an equally plausible alternative has
  not been shown to be valuable — and ranking it on the convenient rule would
  reintroduce, inside the design analysis, exactly the arbitrary-typed-value
  problem §3.2 is trying to remove from the interface;
- its provenance records that it is evaluation-only, and it is retired
  rather than left in place if it does not earn promotion;
- **promotion is a separate decision**, taken only if the evaluation shows
  value and the node then passes tests 1–5 and both parsimony filters on
  its own merits.

`X_IL11` is the case that motivates this: it is staged, not canonical, and
it connects directly to the LIF/GP130-STAT3 ambiguity that carries the only
six class-gaining readouts in the model. Evaluating it must not require
promoting it first. TLR3 and COX2/PGE2 enter by the same route or not at
all — and for TLR3 the evaluation should be explicit that an entire
inflammatory module would have to be built for a perturbation that is not a
therapeutic candidate.

### 3.9 Roadmap correction

`docs/roadmap.md` Phase 0 still lists "Reconstruct the paper's final cell
labels or obtain the final annotated object" as outstanding. The labels
are in hand (E-MTAB-15842, `celltype_v2`, 28,212 cells, hash-pinned).
The draft is right; fix the roadmap.

---

## 4. What is missing from the draft

1. **B1 and B2.** Open against `main`, unmentioned, and B1 is a published
   figure asserting a withdrawn reading.
2. **The escalated gate.** Changes *where* the B10/B13 repair belongs, not
   whether to make it: repair on `main`, stop running rounds in the
   escalated worktree, and hand the gate itself to the user (§1.1).
3. **Zero rate declarations.** §3.3.
4. **`OM-016` as a falsifier v0.4 already fails.** §3.4.
5. **The four-arm plan's anti-SPP1 arm is unreadable as declared.** §3.5.
6. **The interface dynamics are curated and already adjudicated.** R34,
   R35, R37 and R46 of `results_reproducibility_matrix.tsv` carry them with
   figure anchors, sample sizes and a `not_assessable` /
   `continuous_spatial` verdict; R46 records "permanently out of scope for
   a Boolean logical model, not pending work". Nothing here is blocked
   pending curation. §3.6.
7. **Maternal-phase vs challenge arms as separate budgets.** §3.5.
8. **AstroLogics.** §3.7.
9. **No LICENSE file.** Recorded for completeness; **deferred**, not a live
   gate — the repository is private and every external tool is
   read-and-borrow (§3.7, §6). It returns if release or publication is on
   the table. The single carve-out is scBOLT, which restricts *use*.
10. **Embryo statistics.** 9/19 and 1/8 are the numbers a fourth arm must
    be powered against. The draft never mentions power;
    `docs/design_alias_note.md:168` — on the unmerged branch, not in
    `identifiability_analysis.md` — is explicit that class gain "is not a
    power calculation".
11. **`config/protocols.yaml` has no day-3 stage** (`OM-011`), which blocks
    the strongest in-house temporal constraint.

---

## 5. Revised execution order

Each gate names what closes it. Gates 0–2 need no new biology; Gate 3
onward is where the draft's work begins.

```
GATE 0   Repair and re-verify the current increment
         B1, B2 (main)  — fix source, regenerate 3 assets, update hashes, pin with a test
         B10            — edit observability.py, regenerate the TSV, and edit
                          docs/scrna_observability.md BY HAND (nothing emits it)
         B13            — two prose lines in klf12_prior_finding.md (hand-written)
         full suite     — 736 tests green
         hand escalated KLF12 gate to the user with the open findings
         re-run aih review against Codex when quota returns; report degraded until then

GATE 1   Read, don't rebuild
         read results_reproducibility_matrix.tsv FIRST: 51 of 60 rows are
           not_assessable, and its binding_limitation column is already a
           machine-readable inventory of why each one fails. That inventory
           should drive Gate 2, not a fresh survey.
         RE-ADJUDICATE the ELEVEN scRNA rows against the 28,212-cell object the
           repository now holds (E-MTAB-15842, sha256 504a674d...): R17 through
           R27 inclusive. Their notes say it is NOT held;
           config/scrna_observation_map.tsv says it is, and the KLF12 work ran
           against it. Nine are inside the fifteen; R18 and R26 are
           topology;continuous_spatial and stay formalism-limited, but a wrong
           statement about what the repository holds is corrected anyway.
           EXPECT NO ROW TO CLEAR ON PROVENANCE ALONE. The fix removes the
           object-availability blocker; every remaining limitation is then
           re-evaluated on its own terms, by type -- topology, timing/dynamics,
           mapping, assay design, calibration, formalism (§3.6). R20-R23 are the
           strongest candidates because they have comparators, but OM-009/OM-010
           are reported_only, diagnostic, "not usable to validate".
         While there: the matrix's converged max_time column reads a stale 30.0.
           The executed horizon is 25.0 per phase and R43b already says so; this
           is metadata cleanup, and no result changes (§3.6).
         re-verify the identifiability and design-alias numbers after Gate 0 regeneration
         merge or close feat/design-alias-figure
         fix docs/roadmap.md Phase 0
         --> the v0.4 baseline is then current, not assumed

GATE 2   Biological adjudication of existing couplings ONLY
         one new column on node_classification.tsv:
           BIOLOGICALLY_COLLAPSED | UNIDENTIFIED | ARTIFICIALLY_COUPLED
         with rationale + evidence id per row
         start with that file's largest design class, E_ANXA2_ACTIN,
           design_state_size = 23, which holds both E_PAEP and S_IGFBP1
           (23 is the RECORDED six-arm design. The corresponding PLANNED
            four-arm figure is 22, in docs/design_alias/node_design_classes.tsv
            and design_alias_metadata.json largest_design_class, on the
            unmerged branch. Different arm sets, different classes; the two
            numbers must never be swapped or quoted for each other.)
         --> the defect list for v0.5, evidence-backed

GATE 3   The structural repairs, in this order
         3a  CHEAP FALSIFIER. De-alias S_PRL from S_IGFBP1 and add the day-3
             maternal protocol stage, so OM-016 becomes evaluable.
             Propose rule/topology separations; then SIMULATE the transient and
             test whether IGFBP-1-before-PRL actually emerges, robustly across
             seeds, trajectory counts, initial conditions and admissible
             variants. dependency_depth motivates a candidate, it does not
             establish an ordering (§3.3). Declare a relative rate only if NO
             admissible rule variant reproduces it. Fit rates for nothing else.
             OM-016 is construction evidence, direction included (§3.4).
             Independent validation is prospective, not from this row.
         3b  INTERFACE. OPEN WITH THE DECOMPOSITION, not with a repair:
             enumerate how much of the residual ambiguity each relay carries
             alone and which combinations carry the rest. "8 of 32, factor of
             four" is too coarse to plan against (§3.2).
             Then remove or constrain the arbitrary free Bernoulli variables
             — NOT "one MaBoSS node per relay". Adjudicate each relay into:
             explicit mechanism / derived state / external-contextual /
             deferred to PhysiBoSS / explicit uncertainty. Do not force
             mechanical permissiveness into a Boolean biochemical model for
             symmetry.
             The anti-adhesive relay's 10 classes with phenotype_inert=true is
             a DIAGNOSTIC that information and consequence have been separated
             — it is not by itself a reason to repair the barrier branch first.
             Test whether reconnecting PODXL/MUC1/DAG1 to attachment or
             retention is evidence-supported and changes an intervention.
             OBSERVABLE, stated exactly (§3.6): NOT morphodynamics. ΔZ,
             spreading and TE alignment are curated in
             results_reproducibility_matrix.tsv and adjudicated
             not_assessable / continuous_spatial — R46 in those exact words,
             "permanently out of scope for a Boolean logical model, not
             pending work". No curation changes that; they point at
             PhysiBoSS or at staying out.
             In scope: attachment fraction, scored by the matrix at BOTH
             horizons. R41a (declared) is 0.000000 vs 0.474 -- a convergence
             artifact by its own note. R41b (converged, 25.0 per phase; the
             matrix's 30.0 is stale metadata, §3.6) is 0.820340: direction
             agrees, MAGNITUDE
             DISAGREES, 0.820 above the Wilson 95% CI [0.27, 0.68], and it
             is arithmetic on the two relay istates. R41b is the row that
             indicts the relays and the one Gate 3b should move.
             Both are calibration rows, so reproducing 0.474 is not
             validation and must not be scored as it.
             Ordinal onset comparison is blocked because no row simulates an
             onset, calibrated_physical_time is false, and untreated is 0/12.
             GATE 3b CRITERION -- STRUCTURAL, not data-agreement.
             PASS when, and only when:
               (i) no UNGROUNDED hand-set Bernoulli variable determines an
                   adhesion prediction. Retained stochastic uncertainty is
                   allowed, but only if it is explicitly labelled as such and
                   is evidence-bounded or sensitivity-only -- never a typed
                   point value doing load-bearing work; AND
               (ii) OUT_STABLE_ADHESION's converged value arises from
                   modelled biology rather than arithmetic on arbitrary typed
                   constants; AND
               (iii) each of the four relays carries a recorded disposition
                   with its evidence (mechanism / derived / external /
                   deferred to PhysiBoSS / explicit uncertainty).
             All three are directly attributable to this gate's own work and
             none requires agreement with any fitted number.

             HELD-OUT CHECK, secondary and legitimate: R43b, the converged
             mifepristone row. config/calibration.yaml gives that arm
             role=validation_if_held_out; R43b's circularity column reads
             "HELD OUT and enforced in code -- the ONLY genuinely held-out
             comparison IN THIS MATRIX". The hold-out is enforced in code
             (objectives.py sums only roles=('calibration',)); the scope
             claim is the matrix's, not the repository's. Its regimen caveat
             is gone. If the
             interface repair is not fitted to it, its prediction there IS
             validation. Currently partial_direction_only at 0.000000
             against an observed 1/8.

             NOT A CRITERION: the HT attachment fraction. calibration.yaml
             records successes 9 / trials 19 with role=calibration, so moving
             0.820 toward 0.474 is fitting to the fit. STRENGTHENED 2026-09-16:
             this passage used to add that calibration.yaml names
             adhesion_objective "the sole magnitude-fitted (scored) term". It
             no longer does -- the objective was demoted to diagnostic_ordinal
             and NO magnitude-fitted term remains (see
             gate3_scope_adjudication.md). The prohibition below therefore
             holds a fortiori: there is no longer any fitted score for the
             attachment fraction to be a criterion for. R41b's
             magnitude disagreement is the DIAGNOSTIC that motivates the
             repair, never the thing the repair is scored on. An earlier
             revision made it the criterion, which reinstated the very
             circularity an earlier round had removed.

             The 15-row reachable metric belongs to v0.5 AS A WHOLE, not to
             Gate 3b: none of those 15 is interface-blocked (they are the
             scRNA block, unquantified IF, a missing species term, a missing
             hCG output node, a missing mapping row, and R12c which is Gate
             3a's). An earlier revision scored Gate 3b on them, which its own
             work could neither satisfy nor fail.
             (See the criterion block above: the attachment fraction is a
             diagnostic, not a score.)
         3c  TARGETED PROMOTION. Only nodes passing the admission test (§3.8):
             five criteria AND both parsimony filters.
             Promoting the PRL/IGFBP1 SEPARATION is not promoting a mechanism
             for it — S_TGFB_CONTEXT stays a candidate rule variant.
             EVALUATION-ONLY REPRESENTATIONS are allowed and are not promotion:
             a candidate axis (X_IL11 first) may get the minimal temporary
             structure needed to rank it, in the variant layer, retired if it
             does not earn promotion. Without this, the design analysis would
             conclude that the best experiments are the ones v0.4 happens to
             already encode.
         --> v0.5 candidate topology, built from defects rather than from a node catalogue

GATE 4   Structural + interventional expressivity audit on v0.5
         rerun P_label / P_global / P_design; compare directly with v0.4
         success is COMPARATIVE, not a threshold. Recompute identifiability on
           v0.5 and compare v0.4 against v0.5 over the SHARED perturbation and
           readout space. v0.5 passes when it has FEWER biologically artificial
           observational equivalences and better discriminates the mechanisms
           Gate 2 judged independently meaningful.
         8/32 is the v0.4 matched-unit baseline and a useful reference point,
           NOT a rigid bar: v0.5 may change the latent state space, so the
           denominator can move and a raw count comparison would mislead.
           Both sides stay matched-unit-conditional (§3.1 caveat).
         Also: a model class that can express OM-016's ordering (a consistency
           check, not validation).
         NOT more nodes

GATE 5   Uncertainty, represented locally
         rule families held open where evidence is genuinely open, as explicit
           variants in the files that already exist
         iterate them through PyMaBoSS in ordinary Python; no framework
         BoNesis only if the admissible set becomes combinatorial

GATE 6   Prospective design, split by COST and ranked as PERTURBATION × READOUT
         6a  maternal-phase panel (no embryos): which perturbation × readout
             configurations de-alias the measured analytes and the coupling
             classes Gate 2 marked ARTIFICIALLY_COUPLED? Report best ONE,
             best TWO by COMPLEMENTARITY (not top-two individually), and a
             best small panel.
         6b  embryo-challenge arm(s), chosen AFTER 6a: the perturbation with
             the strongest remaining interface/adhesion value, with a readout
             attached. No molecule privileged in advance.
         report model-identification value and translational value SEPARATELY;
           never one combined score
         local discrimination scorer, caspo's idea without caspo
         embryo numbers: report feasibility, sensitivity to embryo count and
           expected information gain. Do NOT treat 9/19 and 1/8 as independent
           binomials — the evidence register itself records embryos as
           observational units with chip and donor dependence to be respected
           (SOFIA-ADH-001). Formal power only if that structure is checked first.

GATE 7   Node-specific personalization contracts
GATE 8   Quantitative calibration
GATE 9   Freeze predictions; prospective ADOC validation
GATE 10  Only then: use the constrained DT to rank non-hormonal intervention
         candidates. Contraceptive prioritisation is downstream of calibration,
         never a filter on which perturbation calibrates best.
```

The draft's dependency graph is otherwise sound. The changes are: B1/B2
added at the top; the framework review collapsed into a decision already
largely made; the biological inventory moved *after* the coupling
adjudication and scoped by an admission test; the interface promoted from
eleventh to the first structural repair.

---

## 6. Decisions that need the user

Trimmed after project-lead review in session (2026-09-15). Six items that were here are
now settled or are mine to investigate; they are listed as resolved below
so the record shows where each went.

### Open

1. **Experimental resource structure — the one genuine unknown.** How many
   donor × chip conditions can actually be run; which perturbations can be
   applied in the maternal phase **without embryos**; and what a
   maternal-only condition costs relative to a full embryo-challenge arm.
   Nothing in the repository answers this, and it is the highest-leverage
   input to the whole plan: if maternal arms are cheap, a larger
   system-identification panel plus one or two challenge arms dominates
   3 × 4 for the same embryo spend. Everything in Gate 6 is conditional on
   it.
2. **Confirmation of the repair locus.** B10, B13, B1 and B2 repaired on
   `main` as one increment reviewed once (§1.1), rather than inside the
   escalated worktree where the repair would not reach the merged defect.
   Repair rather than `aih accept` is settled; only the locus needs a nod.
3. **Whether the `continuous_spatial` adjudication stands.** This replaces
   an earlier decision asking you to fund curation of the interface
   measurements — a false premise: they are already curated, as R34, R35,
   R37 and R46 of `results_reproducibility_matrix.tsv`, and already
   adjudicated `not_assessable` / `continuous_spatial`, with R46 recording
   "permanently out of scope for a Boolean logical model" — a phrase the
   matrix uses verbatim in **nine** rows (R40, R45, R46, R47, R49–R53), five
   of them adding ", not pending work" — so this is a standing adjudication,
   not an inference from one row (§3.6). The live question is whether it stands for v0.5. If it does,
   the morphodynamic half of the interface is a **PhysiBoSS question, not a
   MaBoSS one**, and Gate 3b is scored on its structural criterion (§5)
   rather than on timing. If you want it reopened, that is a
   formalism decision and it belongs to you, not to the plan.

### Resolved, and by what

| Was a question | Now | Because |
|---|---|---|
| Escalated KLF12 gate: repair or accept? | **Repair** | Stale-prose corrections do not warrant acceptance. |
| The fourth arm: keep, drop or re-read anti-SPP1? | **Leave the challenge arm open until Gate 6** | No molecule is privileged; the arm is an output of the design analysis, not an input to it. |
| Relative rates as a v0.5 prerequisite? | **Withdrawn** | §3.3: `dependency_depth` proves nothing about transients; rate-free by default, ordering demonstrated by simulation, rates a fallback. |
| How is `OM-016` allocated? | **Construction evidence, including its direction** | §3.4: the alternative buys a validation term by building on weaker evidence. Validation comes prospectively. |
| Per-relay disposition | **Mine to investigate and recommend** | Gate 3b opens with the per-relay ambiguity decomposition; a recommendation follows from it, not from a prior choice. |
| Licensing | **Deferred** | Private, exploratory, read-and-borrow. One carve-out: scBOLT is not run at all. |
| Identification or contraceptive screening first? | **Identification first** | Stated project priority; Gate 10 puts intervention ranking strictly downstream. |
| Scope of deep-research promotion | **§3.8 as revised** | Five criteria, two parsimony filters, plus the evaluation-only route so the existing model does not decide which experiments may compete. |

## 7. Claim boundaries for this document

- Nothing here was simulated, fitted or calibrated. **Two kinds of fact
  appear here and they are not equally checkable.** Scientific repository
  numbers — node counts, rules, istates, matrix verdicts, evidence rows,
  config values — are *artifact-traced*: each is cited by path and line and a
  reader can reproduce it from the committed tree. Harness and test-status
  facts — "736 tests, OK (164 s)", the §1.1 gate statuses, round counts and
  `cross_vendor_gap`, and §3.7's external push dates and licences — are
  *runtime observations* made in this session against state that is not in
  the tree (the harness ledger) or not in the repository at all (GitHub). A
  read-only reviewer cannot reproduce those, and they should be re-observed
  rather than trusted if they matter later.
- The `0.82` endpoint and the `19/35/59` partitions are properties of
  `network.bnd`, the condition `.cfg` files and `config/*.tsv` as committed
  at `c81f54f`. The `8/32` observation-class ceiling and every other
  observation-class count is **matched-unit-conditional** (§3.1 caveat) and
  is not a claim about what the current data identify. They will
  need re-verification after the Gate 0 regenerations.
- Literature statements are attributed to their sources and are not
  ADOC findings. The TGFβ1/SMAD dissociation of PRL from IGFBP-1 is
  external human in-vitro evidence; it motivates a model repair and is
  not itself validation of one.
- Adhesion-timing quantities from the published ADOC work are reported as
  measured. No correspondence between them and any MaBoSS time is claimed
  or implied, and none may be asserted without a separate, evidenced
  decision on physical time units.
- Ratios in §1.3 are arithmetic on committed medians, not estimates.

## 8. Sources

- ADOC platform: *Modeling human embryo adhesion using a microfluidic
  platform*, Science Advances 2026 — https://pmc.ncbi.nlm.nih.gov/articles/PMC13353414/
- Kane et al., *TGFβ1 attenuates expression of prolactin and IGFBP-1 in
  decidualized endometrial stromal cells by both SMAD-dependent and
  SMAD-independent pathways*, PLOS One 2010 — https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0012970
- SPP1–integrin adhesion (porcine/murine): https://academic.oup.com/biolreprod/article/81/5/814/2557733 ;
  human in-vitro: https://academic.oup.com/humrep/article/29/4/739/603544
- AstroLogics, Bioinformatics 2026 — https://academic.oup.com/bioinformatics/article/42/8/btag555/8741836 ;
  code https://github.com/sysbio-curie/AstroLogics
- BoNesis — https://github.com/bnediction/bonesis , https://bnediction.github.io/bonesis/
- caspo — https://github.com/bioasp/caspo
- CellNOptR-MaBoSS — https://github.com/saezlab/CellNOptR-MaBoSS
- scBOLT — https://github.com/bnediction/scbolt
- scBONITA — https://github.com/Thakar-Lab/scBONITA
- PROFILE / PROFILE_v2 — https://github.com/sysbio-curie/PROFILE , https://github.com/ArnauMontagud/PROFILE_v2
