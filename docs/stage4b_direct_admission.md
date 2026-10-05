# Stage 4b — admitting real direct interventions: pre-registration, 2026-10-04

**Status: PRE-REGISTERED. The owner accepted this design on 2026-10-04 and the
seven decisions of §11 are taken.** It is pre-registered at the commit that lands
this document, before any §10 governance code exists — the same ordering as the
O8b note (`bb597a8`). The §5 expressivity unit is committed with it, because it
is what the design's claims are read from; it adds no governance, no approval
and no executable row.

**What is still not done, deliberately:** §10, the entity map, the declarations
table, the two new ledger columns and the C1–C8 loader checks. No real
declaration, approval or library row exists, and 4c and 4d are not authorised.

**Revision history.** Revision 1 proposed the re-scoping; revision 2 added the
reproducible artefact and the L1/L2/L3 separation after owner feedback;
revision 3 (this one) records the decisions as taken and the review repairs.
Earlier framings that were corrected rather than deleted are marked in place, so
that what changed stays legible.

**The §5 classification comes from committed code, output and a test**, not from
a session's scratch space:
`src/dt_adoc/reporting/veto_expressivity.py`,
`docs/stage4b/v060_veto_expressivity.tsv`, `tests/unit/test_veto_expressivity.py`
and the `veto-expressivity` task. Nothing else is implemented: no governance
code, no new config table, no real approval.

This document settles what must hold before a real `direct_supported_effect` row
can execute: the three separate questions of §2a, target-list completeness (§3),
engagement semantics (§4), expressivity (§5), and the admission gate (§6).

## 1. Starting point, verified on `main`

- `main` is `1517eec`, the merge of PR #19, and the tree is clean. The merge
  tree is byte-identical to `744b88d`, the O8b branch head
  (`git diff 744b88d 1517eec` is empty).
- `pixi run validate-direct-effects` reports `0 adjudication rows, 0 licensed
  direct rows, audit current`. G12 and the O8 static suites ran 90 tests, all
  passing.
- The ledger `config/direct_effect_adjudications.tsv` holds a header and no row.
  The library holds no `direct_supported_effect` row. Its v0.6.0 rows are three
  `migrated_legacy_behaviour` interventions (mifepristone, anti-SPP1, HAND2 loss)
  and `xav939` (`no_executable_effect`).
- **The review caveat stands.** The harness record for O8b's final state is
  `PASS` with `degraded: true`, stand-in reviewer, `accepted: false`. Every
  verdict on O8b came from the same-family stand-in, because the independent
  reviewer was unavailable. O8b has had **no independent cross-vendor review**,
  and nothing here treats it as having had one.
- O8b is treated as closed. No blocker to that was found. Two of its statements,
  and two rows of `config/coupling_adjudication.tsv`, are wrong about what a veto
  does; §5.5 records them for a dated correction. Neither changes a licence,
  since the ledger is empty.
- Nothing executes partial engagement anywhere. `perturbations/target_engagement.py`,
  `single.py` and `combinations.py` build engagement grids that only the CLI
  prints and the PROFILE parity tests check. The runner's
  `target_engagement_curves.json` holds the protocol-pair deltas of
  `perturbation_effects.tsv`, not engagement levels.

## 2. Scope: why Stage 4b is not the screen

The refactor plan (§5, item 5) defines Stage 4b as "a screen over a larger
library". The repository shows that a screen cannot yet mean anything:

1. **There is nothing to screen.** The ledger is empty, and §11 of the O8b note
   found no committed source that clears the bar.
2. **The observable space is small.** Of the 19 eligible targets, 9 are
   structural nulls and the other 10 fall into 4 classes that the observed
   readouts cannot separate (§5). Within a context every non-null effect on
   adhesion has one of two sizes, and both are set by the hand-set relay priors.
3. **The score is undefined.** `config/candidate_score.yaml` (status
   `structural_only`) scores 10 phenotypes, 7 of which are not nodes of v0.6.0.
4. **The licences are unequal.** The migrated rows keep licences the direct bar
   would refuse: HAND2 loss rests on a mouse conditional knockout plus human
   siRNA, and mifepristone has no target declaration.

**Adopted** (owner, 2026-10-04): split the plan's Stage 4 remainder into three.

| unit | content | produces a result? |
|---|---|---|
| **4b (this document)** | the three-layer separation of §2a, the completeness rules, the expressivity artefact, the admission gate, gate G13. Synthetic fixtures only | no |
| **4c** | the first real admission: one intervention, its declaration, its approval, one run against the matched unperturbed twin | one conditional model-internal prediction |
| **4d** | a screen, once enough approved interventions are distinguishable and the score names existing outputs | rankings |

4c and 4d are not authorised by this document. **Model-only target ablation** —
"what if this node's activity were lost", naming a node and no reagent — stays a
separate future unit (§4.3). It needs none of the compound governance here, and
mixing the two would let a compound claim ride on a target-level result.

## 2a. Three questions that must not be conflated

Every rule below belongs to exactly one of these layers, and the gate keeps them
in separate columns so that a result can never silently borrow another layer's
authority.

| layer | question | decided by | recorded in |
|---|---|---|---|
| **L1 scientific effect licence** | does the cited evidence establish that this agent abolishes this node's activity, in a system this model stands for? | evidence plus reviewer judgement | `config/direct_effect_adjudications.tsv` (O8b), extended in §6.2 |
| **L2 model expressivity** | what does a full veto of that node change in this model version, under the declared conditions? | computation on the committed rules | `docs/stage4b/v060_veto_expressivity.tsv`, regenerated and pinned (§5) |
| **L3 screen eligibility** | can a result for this target be ranked against others, or reported as a phenotype claim? | L2 plus the observation map and the score | the run record and the report rules (§5.6) |

The consequences of keeping them apart:

- **L1 does not imply L2.** An impeccably evidenced agent may have no effect on
  any observed node. That is a fact about the model, not about the compound.
- **L2 does not imply L1.** A large simulated effect licenses nothing.
- **L3 is narrower than both.** Two licensed, expressive interventions can still
  be indistinguishable from each other on the observed readouts.
- **L2 and L3 are version- and condition-relative.** They are recomputed from
  the committed rules, cfgs and observation map; L1 is not, and an approval is
  never withdrawn because the model changed.

An earlier draft of this document made a structurally null target
*unapprovable*, which collapsed L2 into L1. §5.6 replaces that.

## 3. Target-list completeness (L1, with an L2 consequence)

### 3.1 What can be omitted

O8b approves each listed effect, so an intervention could be approved while
omitting something it is known to do:

| omission | example in this model | control |
|---|---|---|
| **another entity** the agent engages, which a model node represents | an inhibitor that also hits a second modelled kinase | C3 (§3.4) |
| **the same entity in another compartment** the agent reaches | PGR is `E_PGR` and `S_PGR`; SPP1 is `E_SPP1_EXPR`, `S_SPP1` and `X_SPP1_LUMEN_FREE`. A bath-applied PGR antagonist declaring only `S_PGR` omits the epithelium | C3, with the reached compartments (C4) |
| **part of the node** — the node aggregates entities and the agent hits a subset | `E_ITGAVB3_5` is two heterodimers sharing αv, so anti-β3 leaves αvβ5 while anti-αv disables both | node coverage, C5 (§4.4); and §3.2.1, where this node defeats the flat vocabulary and is made unapprovable |
| **an entity with no node** | a known target the model does not represent | C6 (§3.5) |

No gate can establish that the list of engaged entities is complete: that is an
absence claim. The gate makes the claim explicit, sourced, dated and bounded by
concentration, then mechanically forces every *known* entity onto every node
that represents it. Completeness of the known list stays reviewer judgement
(§3.6).

### 3.2 New table: `config/node_entity_map.tsv`

A reading of each version's `node_dictionary.tsv`; it adds no topology. One row
per (model version, node, entity, level):

| column | meaning |
|---|---|
| `model_version`, `node_id` | a node of that version |
| `entity` | an HGNC symbol, or `process:<name>` for a non-gene process |
| `level` | `expression`, `activity` or `extracellular` — the level distinction DTR023 found `perturbations.tsv` conflating |
| `compartment` | `epithelium`, `stroma` or `extracellular`, from the dictionary |
| `aggregation` | `single`; `any_of` (a full veto must hit every member); `all_of` (hitting one suffices); `ambiguous` (the dictionary does not decide); `derived` (the node has no entity of its own, so a veto would set a derived variable) |
| `basis` | the dictionary label, or the coupling or DTR row it is read from |

Rules:

- Every node of the version has a row, except the 11 protocol inputs (roles
  `input`, `assay_gate`, `external_input`, `pathology_input`, `boundary_input`).
  That is 45 nodes for v0.6.0.
- **`aggregation` is filled for every node, including every policy-refused one**,
  and it is an independent reading. The two refusal grounds answer different
  questions, so they must not be assumed to agree:
  - `derived` means the node stands for **no entity of its own**: the model
    computes it from other nodes. That is the composite roles (`state`,
    `latent_state`, `interface_route`, `phenotype`, `structural_uncertainty`)
    and the rule-derived abstractions `E_ESTROGENIC_PROLIFERATION` and
    `S_FGF_MITOGENIC` (`not S_HAND2`).
  - A node refused for any other reason keeps its real aggregation, because it
    does stand for entities. `E_PAEP`, `S_PRL` and `S_IGFBP1` are `single`
    (PAEP, PRL, IGFBP1 at `expression`); `S_BMP2` is `ambiguous`, which is why
    its role reads `regulator_or_readout`; `E_MUC1_BARRIER` and `E_MUC1_SLEX`
    are `single` on MUC1 at `activity`, refused at node scope because one veto
    cannot separate abundance from glycoform (LIT-BARRIER-001); **`E_DAG1_FULL`
    and `E_DAG1_CLEAVED` are `single` on DAG1**, refused at node scope under the
    product/enzyme argument (DTR011, DTR021) rather than for standing for
    nothing.
  - The reason this matters is C3: a known target entity landing on a
    policy-refused node must be detected, and it can only be detected if that
    node's entities are written down. A blanket `derived` on every refused node
    would hide exactly the cases C3 exists for — a PAEP-directed, MUC1-directed
    or DAG1-directed agent would pass unnoticed instead of being refused.
- **Known model gaps are rows too.** The four `catalog_only` targets of
  `drug_target_catalog.tsv` (`S_STAT3`, `S_DECIDUAL_SENESCENCE_BALANCED`,
  `X_LGALS1_3`, `X_BSG_ITGB1`) are entered with `node_id` empty and
  `aggregation = model_gap`. They are entities the repository has itself recorded
  as relevant and absent.
- An `ambiguous` node cannot be an approved target. Candidates from the current
  labels are `E_ANXA2_ACTIN` ("ANXA2, RHOA-GTP, or F-actin architecture") and
  `S_PKA` (per the `IN_cAMP` and `S_PKA` coupling rows). The owner may resolve
  either by a recorded decision, never by an approval.
- A test regenerates the node list from the dictionary and requires the map to
  cover it exactly, so a model version cannot gain a node the map does not
  mention.
- **The map is not compound data, and admitting a compound may not change it.**
  It is a reading of the model version, so it changes only when the model
  version does, or when a recorded decision resolves an `ambiguous` node. The
  N+1 gate (§7) asserts this: adding compound Y appends to the register, the
  declarations, the ledger and the library, and leaves `node_entity_map.tsv`
  byte-identical. Otherwise an inconvenient C3 or C5 refusal could be cleared by
  quietly re-reading what a node means, which is the one move that would hollow
  out every rule in §3.4.

### 3.2.1 The one node the flat vocabulary cannot represent: `E_ITGAVB3_5`

`E_ITGAVB3_5` is "Epithelial alphaVbeta3/alphaVbeta5 integrin state": **two
heterodimers sharing one α subunit**, not a flat set of three interchangeable
entities. The structure that matters is which *complexes* exist and which
subunit each agent hits:

- anti-β3 disables αvβ3 and leaves αvβ5, so the node's activity survives;
- anti-β3 **plus** anti-β5 disables both;
- **anti-αv disables both at once**, by hitting the subunit they share.

Neither `any_of` nor `all_of` expresses that. Under `any_of` over
{ITGAV, ITGB3, ITGB5}, C5 demands all three and so refuses anti-αv, although
anti-αv is exactly the agent that *does* abolish the node. Under `all_of`, C5
accepts anti-β3, which does not. An earlier revision asserted in §3.7 that "an
anti-αv agent could satisfy C5"; under the flat rule as written it could not,
and that contradiction is what this section resolves.

**Decision (owner decision 7, §11.3): `E_ITGAVB3_5` is `ambiguous`, and
therefore not approvable, until the model distinguishes the two complexes.** The alternative — a hitting-set or
complex-level representation (`complexes = ITGAV+ITGB3; ITGAV+ITGB5`, with C5
asking whether the agent's entities form a hitting set over the complexes) — is
genuine new design work for a single node, and it would describe a distinction
the *model* does not carry: v0.6.0 has one integrin node, so αvβ3 and αvβ5 are
one Boolean variable and no intervention can act on one of them anyway. Adding
expressive machinery in the licensing layer for a distinction the executable
layer cannot honour is how a licence comes to say more than the model can mean.

This is not a new judgement about the integrin. `docs/deferred_topology_register.tsv`
already carries **TI-03** (state `DEFERRED`): "Split `E_ITGAVB3_5` into beta3
and beta5 states and repair the upstream `E_HBEGF = E_SECRETORY_STATE`
collapse". Discharging TI-03 is exactly the unblocking condition here, and at
that point the two complexes become two nodes and the flat `single`
vocabulary suffices — no hitting-set machinery is ever needed.

Consequences, stated so they are not discovered later:

- **No direct intervention may be approved on `E_ITGAVB3_5` in v0.6.0**, anti-αv
  included. C5 refuses `ambiguous` targets.
- **The §5 expressivity artefact is unchanged.** It is generated from the O8b
  target audit, which reads `config/direct_effect_target_policy.tsv`, not this
  entity map. `E_ITGAVB3_5` stays O8c-eligible and stays in class A2, and the
  committed TSV does not move. Eligibility (O8c), approvability (C5) and
  expressivity (§5) are three different questions, exactly as §2a requires — and
  this node is now a worked example of all three disagreeing.
- `E_ANXA2_ACTIN` and `S_PKA` are `ambiguous` for a different reason: their
  dictionary labels conflate entities that are not complexes. The remedy there is
  a recorded decision about what the node means (§11.2), not a topology split.

### 3.3 New table: `config/direct_effect_target_declarations.tsv`

One row per (intervention, model version) — the intervention-level record O8b
lacks.

| column | meaning |
|---|---|
| `declaration_id` | `DTD-NNN` |
| `intervention_id`, `model_version` | the key |
| `agent_class` | `small_molecule`, `biologic`, `antibody`, `genetic_knockdown` or `genetic_knockout` |
| `agent_specification` | the exact reagent the approving evidence used: name, an identifier (ChEMBL id, catalogue number, clone, siRNA/sgRNA id) and the concentration or construct. **Approval is for that reagent at that concentration**, not for a class or a name |
| `reached_compartments` | the compartments the agent reaches in the evidence system. The default for a bath- or channel-applied agent is all of them; a narrower value needs a cited reason |
| `known_target_entities` | every `entity@level` the profile sources report the agent to engage at the stated concentration |
| `declared_targets` | must equal, as a set, the intervention's library target nodes for that version |
| `unrepresented_known_targets` | every known entity with no node, each classified `scope_relevant` or `out_of_scope` with its basis (§3.5) |
| `target_profile_sources` | the evidence ids or reference records consulted; each must resolve |
| `profile_searched_on` | an ISO date |
| `construction_overlap` | generated (§6.5) |
| `library_rows_sha256` | sha256 of the intervention's library rows for that version, in library order, each digested as O8b §5 digests one row |
| `adjudicator`, `dated` | who declared it, and when |

### 3.4 Mechanical completeness rules (checked at every load)

Evaluated against the current entity map each time the library loads, so they
cannot go stale. A failure refuses the whole library, as in O8.

- **C1** Every direct intervention has exactly one declaration per model version
  it has rows for.
- **C2** `declared_targets` equals the library's target set, and
  `library_rows_sha256` matches.
- **C3 (no omitted known effect).** For every `entity@level` in
  `known_target_entities` and every node whose map row carries that entity and
  level in a reached compartment, the node must be in `declared_targets`. If that
  node is policy-refused, the intervention **cannot be represented** and is
  refused: its known action includes setting a node the policy says a veto may
  not mean.
- **C4** A narrowed `reached_compartments` cites a source that resolves.
- **C5 (node coverage, §4.4).** For each declared target: `single` needs the
  entity; `any_of` needs every member entity at a level the node represents;
  `all_of` needs at least one; `ambiguous` and `derived` are refused. The
  aggregation vocabulary is deliberately flat, and §3.2.1 records the one node
  it cannot represent and what is done about it instead.
- **C6 (known model gaps).** Every known entity with no node is classified in
  `unrepresented_known_targets`, and an unclassified one refuses the library.
  Classification itself never refuses: a `scope_relevant` entry sets the run-level
  flag `compound_claim_blocked`, and an `out_of_scope` entry is carried into the
  claim boundary (§3.5). **C6 constrains what may be *claimed*, not what may be
  licensed or executed.** This is owner decision 4.

  *Corrected: an earlier revision of this bullet read "a `scope_relevant` one
  refuses the intervention", which contradicted §3.5, §6.5, G13 and the decision
  itself. The single mechanical rule is the one stated here, and §6.1 lists C6
  among the licence conditions only through the "classified at all" half.*
- **C7** Every declared target's entity appears in `known_target_entities`.
- **C8** The ledger row for each effect names this declaration
  (`target_declaration_sha256`, §6.2).

### 3.5 Unrepresented known targets: two kinds, one of them blocking

**Revised from the earlier draft**, which refused every intervention with a known
target outside the model. That is too strong: a bath-applied agent will almost
always engage something the model does not represent, and a blanket refusal would
admit nothing while telling the reader nothing.

The declaration must classify each unrepresented known target, with its basis:

| class | definition | consequence |
|---|---|---|
| `scope_relevant` | **both** hold: the entity is one the repository itself treats as acting within the modelled biology (§3.5.1), **and** it sits in a compartment the agent reaches (`reached_compartments`) such that it could affect a modelled endpoint | **compound-level prediction is blocked.** The library row may still be licensed and run, but the run is recorded `compound_claim_blocked`, and the result may be reported only as the effect of the declared vetoes, never attributed to the named agent |
| `out_of_scope` | the entity acts on biology outside the modelled scope or compartment, with no recorded claim that it reaches a modelled node or readout in this system | permitted; the entity is carried verbatim into the run record's claim boundary |

Both halves of `scope_relevant` are required, which is the owner's decision 4:
an entity the repository calls relevant but which the agent cannot reach in this
preparation does not block, and an entity in a reached compartment that bears on
nothing modelled does not block either. The reachability half is read from the
declaration's `reached_compartments` (§3.3), so it is as well evidenced as that
field; the "could affect a modelled endpoint" half is J2 judgement, with §3.5.1's
two lists as its floor.

Two consequences of the split:

- A STAT3 inhibitor applied to both channels is `scope_relevant`: `S_STAT3` is
  `catalog_only` in v0.6.0. It may be licensed and executed, but a prediction
  may not be presented as "what this inhibitor does", because a target the
  repository itself calls relevant is unmodelled.
- An agent's effect on, say, hepatic metabolism is `out_of_scope` and belongs in
  the claim boundary.

### 3.5.1 The mechanical floor for `scope_relevant`

The classification is reviewer judgement, but two lists are generated from
committed tables, and a declaration calling an entity on either of them
`out_of_scope` is refused:

- **non-executable catalogue targets** — `drug_target_catalog.tsv` rows of that
  version whose `execution_status` is not `executable`. For v0.6.0 that is
  `S_STAT3`, `S_DECIDUAL_SENESCENCE_BALANCED`, `X_LGALS1_3`, `X_BSG_ITGB1`
  (`catalog_only`) and `IN_UTERINE_WNT_CUE` (`external_only`);
- **staged candidate nodes that were not admitted** —
  `context/literature/staging/deep_research_adhesion_model_2026-09-11/candidate_nodes.tsv`,
  keyed by `node_id`: 14 entries including `X_IL11` (rejected as canonical by
  DTR003), `S_FOXO1`, `E_ESR1_ACTIVITY`, `S_ERK`, `E_ITGA2B1` and
  `E_GLYCOSYLATION_PROGRAM`.

Everything else is judgement under J2, with one standing example: an entity a
cited source reports to change a modelled node or a measured readout in
endometrial cells is `scope_relevant` even when it appears on neither list.

Two sources deliberately **not** used as the floor. The node sets of the other
superset versions differ from v0.6.0 only by the three retired intervention
markers, so they name no entity. And `docs/deferred_topology_register.tsv` is
keyed by increment and describes rule changes rather than entities, so it is not
mechanically convertible to an entity list; TI-03 (splitting `E_ITGAVB3_5` into
β3 and β5) is nevertheless the kind of record J2 should read, because it says the
model's granularity is known to be coarser than some agents are.

### 3.6 What remains reviewer judgement

- **J1** Whether `known_target_entities` is complete at the stated
  concentration. Minimum source per `agent_class`: a small molecule needs a
  quantitative selectivity profile at or above the evidence concentration; an
  antibody needs its antigen and a cross-reactivity statement; a knockdown or
  knockout needs the targeted gene plus an off-target control in the cited work
  (two independent reagents, or rescue).
- **J2** Whether each unrepresented effect is `scope_relevant` (§3.5).
  Mifepristone's glucocorticoid-receptor antagonism in decidualizing stroma is
  the kind of case this exists for.
- **J3** That each `entity@level` reading matches what the source measured.

The `basis_record` O8b already requires must address J1–J3 explicitly.

### 3.7 The rules against cases the repository knows (not approvals)

| case | outcome |
|---|---|
| mifepristone, bath-applied | C3 forces both `E_PGR` and `S_PGR`. GR antagonism is for J2 to classify. (Migrated rows are not subject to these rules; this shows only that the rules can express the case) |
| anti-SPP1 antibody | `SPP1@extracellular` maps only to `X_SPP1_LUMEN_FREE`; neither expression node is forced, which is the abstraction the legacy row states |
| bath-applied STAT3 inhibitor → `E_GP130_STAT3` | licensable on its own merits, but `scope_relevant` via `S_STAT3`, so compound-level prediction is blocked. O8b's separate `phenotype_only` finding already refuses the current source |
| anti-αvβ3 → `E_ITGAVB3_5` | refused by C5, and so is **anti-αv**: the node is `ambiguous` because it is two complexes sharing a subunit, which the flat vocabulary cannot express (§3.2.1). Unblocked by TI-03, not by a better agent |
| PKA-selective inhibitor → `S_PKA` | refused while `S_PKA` is `ambiguous`; and if mapped `any_of {PKA, EPAC}`, C5 would still refuse it |
| a PAEP-directed antibody | refused by C3: `E_PAEP` carries PAEP in the map and is policy-refused as a readout |

## 4. Engagement semantics (question 2)

**Decision (owner, 2026-10-04): Stage 4b adds no representation of partial or
graded engagement. A full `activity_veto` stays the only executable effect of a
direct row.** The reasons differ per meaning, so they are separated.

### 4.1 Three meanings of partial engagement

| meaning | example | in this model |
|---|---|---|
| (i) **node coverage**: the agent hits a subset of what the node aggregates | anti-αvβ3 on `E_ITGAVB3_5` | a licence rule (C5); no new mode |
| (ii) **population heterogeneity**: a fraction f of independent units fully engaged, the rest untouched | mosaic transfection; incomplete delivery | adds nothing beyond the two endpoints (§4.2) |
| (iii) **within-cell attenuation**: every unit's target activity reduced to some fraction | a ~50 % knockdown (PDF-044); a partial inhibitor | not representable without inventing a threshold or a rate (§4.3) |

### 4.2 Population heterogeneity is a mixture of units, and needs no mode

**This argument is about (ii) only.** It concerns a population made of units that
are each either *fully* vetoed for the whole lineage or *entirely* untouched, in
proportions f and 1 − f. It is not an argument about (iii), and it does not say
that a partially inhibited cell behaves like a mixture of unaffected and fully
inhibited cells. That claim would be false in general: a Boolean node is not
linear in its inputs, so attenuating activity inside one unit is not the average
of two unit states.

Under that reading, each unit's trajectory is drawn from either the fully vetoed
model or the matched twin, so every population quantity — a node marginal, a
state frequency, a phenotype probability — is exactly
`(1 − f) · twin + f · full veto`, at every time point. It is linear in f, so the
pair (matched twin, full veto) already contains everything such a mixture can
say. Executing it would add only f, and no source in the repository measures f as
a fraction of fully engaged units. For k targets with any joint engagement
distribution w over subsets S, the result is `Σ_S w_S · run(S)`: it lies in the
convex hull of the 2^k subset runs, each of which Stage 4a composition already
executes. The open part is w, which is O5.

Reporting rules for 4c and 4d:

- a direct intervention's result is reported as the pair (matched twin, full
  veto), labelled **complete-engagement counterfactual**. It is never an
  interpolated value at an assumed f;
- for a multi-target intervention, the 2^k − 1 non-empty subsets are reported as
  an engagement sensitivity, labelled as corners and carrying no weights. (For
  mifepristone, `E_PGR` alone and `S_PGR` alone are different classes in §5.3,
  so the corners are informative.)

Mixing per phase and carrying the state forward is a different object and is not
done here, as the plan's O4 note already says.

### 4.3 Within-cell attenuation is out of scope

A Boolean node has no defined activity fraction at which it switches. Mapping
"50 % residual" to ON, OFF, a probability or a rate scaling would invent the
threshold or the kinetics AGENTS.md forbids without evidence.
`target_activity_partially_reduced` therefore stays non-approvable.

Scientific consequences:

- Most real perturbation evidence — siRNA knockdowns, partial or reversible
  inhibitors, attenuators — cannot license a named reagent in this model. The
  approvable set is agents shown to abolish or block the node's activity. O8b
  §11 found no current source that does.
- A full-veto result is a statement about complete loss of the node's activity
  under the stated rules. It says nothing about dose or exposure, and it may not
  be used to argue for one.
- Partial evidence still has an honest use: it can motivate a **model-only
  target ablation**, which names a node and no reagent and needs no compound
  evidence. That is a separate future unit (§2), not part of 4b, and a compound
  may never be named in its results.
- **O4 re-entry conditions, recorded.** For (ii): a source measuring
  single-unit engagement and showing it all-or-none. For (iii): an
  evidence-licensed mapping from activity level to node state, for a specific
  node.

### 4.4 Node coverage (meaning i) becomes mechanical

C5 makes coverage decidable from the entity map. It also tightens O8b's
`target_activity_reduced`: "abolished" must hold for **the node's activity as
the node is defined**. Abolishing one member of an `any_of` node is partial
engagement of that node, whatever the source says about the member.

### 4.5 Guard

G13 asserts that no execution path accepts an engagement level for a library
intervention, and that the engagement-grid helpers are reachable from no runner
or engine path, so a future change cannot quietly create a partial mode.

## 5. Model expressivity (L2)

### 5.1 It is computed in the repository, not asserted here

`src/dt_adoc/reporting/veto_expressivity.py` generates
`docs/stage4b/v060_veto_expressivity.tsv`;
`tests/unit/test_veto_expressivity.py` pins the classification and
`pixi run veto-expressivity` checks the committed copy is current. The numbers in
§5.3 are read from that artefact, so a rule, cfg, policy or observation-map
change that moves them is a visible diff rather than a silent change to what this
document claims. The generator runs no MaBoSS, writes nothing under `models/` or
`config/`, and is read by no execution path.

### 5.2 Method, and why it is exact

v0.6.0 is feed-forward apart from 16 self-loops (11 protocol inputs,
`E_KLF12_HIGH`, 4 structural relays). For fixed inputs and free variables such a
rule set has exactly one fixed point, which MaBoSS reaches with probability 1; a
veto renders `(...) and not 1` and only pins that node at 0. The asymptotic
marginals are therefore an exact weighted sum over the free variables' baseline
istates. **The argument has preconditions, and the generator refuses every
network or cfg set that breaks one** rather than returning a number:

- a cycle other than a self-loop, which destroys the single fixed point;
- **a node declaring `rate_up`, `rate_down` or `max_rate`.** The fixed point is
  where the trajectories end only because every node runs at MaBoSS's default
  rates. `engine._target_logic` already refuses a rate on a *veto target*,
  because it would change what the veto means; here the condition is wider,
  since a declared rate anywhere puts the whole network outside the argument.
  No superset `.bnd` declares one today, so v0.6.0's classification is
  unaffected;
- a condition cfg that sets a free variable, which this computation would
  otherwise ignore;
- a mixed istate on a protocol input, in a condition cfg or in the baseline,
  since no single assignment represents it;
- a **multi-node** `[A,B].istate`, in a cfg or the baseline. It declares a joint
  distribution over several nodes, and per-node marginals cannot represent the
  correlation. No v0.6.0 cfg uses the form;
- **a veto of a free (self-loop) node.** Its value is a declared initial
  condition, not something the network computes, so applying a veto to it would
  change nothing and the arm would be reported as a structural null — the most
  damaging wrong answer available, since §5.6 reads a null as "no observed change
  under complete engagement". The O8b audit already refuses every self-loop node
  mechanically, so this is unreachable today and guards the case where that
  changes;
- a `REFERENCE_CONTEXT` that is not a distinct context, which would otherwise
  empty a reported column in silence;
- an `activation_status` the observed-set rule does not classify (below).

A condition cfg is read the way the runner merges it: an input the cfg does not
name keeps its **baseline** value rather than defaulting to off. Every v0.6.0
cfg names all 11 inputs, so this changes no number here; it is what makes the
rule right for a later version that omits one.

It evaluates, for the 19 eligible targets and the veto-mode library
interventions: each distinct input vector of the version's condition cfgs (10
for v0.6.0), at the baseline istates and with each hand-set free variable
flipped (`E_KLF12_HIGH` = 0 and 1).

This is asymptotic. Transients differ, but time is relative and uncalibrated, so
they are not read as distinguishability.

#### The observed set O, stated exhaustively

O is read from one column, `activation_status` of
`config/observation_model_map.tsv`, which takes exactly five values. **All five
are classified, so nothing is excluded by omission**, and a sixth value would be
refused rather than silently dropped:

| `activation_status` | rows | treatment | nodes it contributes |
|---|---|---|---|
| `active_constraint` | 1 | **in O** | `E_PAEP` |
| `active_diagnostic` | 1 | **in O** | `S_IGFBP1` |
| `provisional` | 2 | **in O** | `S_PRL` (one row names no node) |
| `reported_only` | 6 | **extended set only** | `OUT_EPITHELIAL_RECEPTIVE`, `OUT_STROMAL_DECIDUALIZED` (four name no node) |
| `rejected` | 7 | **excluded entirely** | — |

So O = {`E_PAEP`, `S_IGFBP1`, `S_PRL`} plus the binomial adhesion assay
`OUT_STABLE_ADHESION`, which is a node-dictionary readout rather than an
observation-map row and is therefore named in the code. The extended set adds
the two `reported_only` phenotypes; it is reported in its own column and never
used to claim distinguishability.

`rejected` rows are excluded because the repository has already adjudicated them
as carrying no claim — OM-007 is "structurally undefined", OM-016 and OM-017 are
coverage gaps. Including them would let a veto be called distinguishable on a
readout the repository has ruled cannot support one.

**O is not the set of rows that carry an objective term.** That is a different
column, `objective_treatment`, whose values include
`provisional_no_objective_term` and `reported_only_no_objective_term`. The two
do not line up: `S_PRL` enters O through OM-006, whose `objective_treatment` is
`not_used`. Membership of O means *measured and not rejected*, because the
question L3 asks is what the ADOC assays could see — not what currently enters
the calibration objective, which is narrower and would change for reasons that
have nothing to do with an intervention.

### 5.3 Result (as generated)

| class on O | members | effect in `adhesion_challenge_hormone_treated` |
|---|---|---|
| **structural null** | `E_IHH`, `E_PODXL`, `E_HBEGF`, `E_SPP1_EXPR`, `E_CD98_CD9`, `E_ANXA2_ACTIN`, `E_CDH1_APICAL`, `S_NR2F2`, `S_SPP1` | nothing in O, in any context, at either KLF12 value. Eight change no node but themselves; `E_IHH` changes only `S_NR2F2` |
| **A1** | `E_LIF`, `E_GP130_STAT3`, `E_PC6`, `S_HAND2`, `S_TAZ_ECM`; and migrated `hand2_loss` | stable adhesion −0.82 |
| **A2** | `E_ITGAVB3_5`, `X_SPP1_LUMEN_FREE`; and migrated `anti_spp1` | stable adhesion −0.42 |
| **A3** | `S_PGR`, `S_PKA` | PRL and IGFBP1 1 → 0; adhesion −0.82 |
| **A4** | `E_PGR` | PAEP 1 → 0; adhesion −0.82 |
| — | migrated `mifepristone` | A3 ∪ A4 |

**Context-dependence of the magnitudes** (the numbers above are that one
context; the artefact carries the rest). Adhesion is non-null in three contexts
only, and the baselines differ: 0.82 in `adhesion_challenge_hormone_treated`, and
0.574 in `adhesion_challenge_excess_er_stress` and
`adhesion_challenge_high_ecm_stiffness`, where `X_MECHANICAL_STRESS_RELAY` can
block the permissive ECM. So A1's loss is −0.82 in the first and −0.574 in the
other two, and A2's is −0.42 and −0.294. A3 additionally moves PRL and IGFBP1 in
all seven progestin contexts.

**The magnitudes are relay priors, not evidence.** Baseline adhesion is
1 − 0.30 × 0.60 = 0.82: the SPP1 relay or the redundant relay must be on. Losing
the SPP1 route leaves P(redundant relay) = 0.40, hence −0.42. The stress contexts
multiply by P(stress relay off) = 0.70. All three numbers are istates of
`structural_uncertainty` nodes. **Any prediction from an admitted intervention is
direction-only.**

Adding the two `reported_only` phenotypes splits A1 into
{`E_LIF`, `E_GP130_STAT3`, `E_PC6`, `S_HAND2`, `hand2_loss`} and {`S_TAZ_ECM`},
and A3 into {`S_PGR`} and {`S_PKA`}. The nulls do not change.

### 5.4 Why, from the rules

- **`E_IHH`, `S_NR2F2`.** `S_BMP2 = (S_PGR and S_PKA) or S_NR2F2`, and every
  declared progestin context also carries cAMP, so the first disjunct is already
  true and **`S_BMP2` never changes at all** — there is no BMP2 loss for
  `S_HAND2` to absorb. Vetoing `E_IHH` therefore moves only `S_NR2F2`, and
  vetoing `S_NR2F2` moves nothing. (Verified: the veto of `E_IHH` changes exactly
  `{S_NR2F2}` and that of `S_NR2F2` changes nothing, over all 10 contexts and
  both KLF12 values.) A progestin-without-cAMP arm would make `S_BMP2` move, but
  **not** O: `S_HAND2` stays on through `S_PGR`, and `S_DECIDUALIZED` is off
  without cAMP, so the edge would surface only on unobserved nodes.
- **`E_HBEGF`, `E_CD98_CD9`, `E_ANXA2_ACTIN`, `E_CDH1_APICAL`.** They occur only
  in disjunctions whose other members are implied whenever these are on. This is
  the "nominal redundancy" of the `X_ADHESION_ROUTE_REDUNDANT` coupling row,
  now shown to hold under vetoes too.
- **`E_SPP1_EXPR`, `S_SPP1`.** `X_SPP1_LUMEN_FREE = E_SPP1_EXPR or S_SPP1`, and
  **each veto is null on O for every input vector of v0.6.0**, not only for the
  declared ones. Adhesion needs `OUT_MATERNAL_ADHESION_COMPETENCE`, which needs
  `S_DECIDUALIZED`, and `S_SPP1 = S_DECIDUALIZED`; so wherever adhesion can be
  non-zero, `S_SPP1 = 1` and the pool is on whatever `E_SPP1_EXPR` does.
  Conversely adhesion needs `E_GP130_STAT3`, hence `E_SECRETORY_STATE`, which
  *equals* `E_SPP1_EXPR`; so wherever adhesion can be non-zero the pool is on
  whatever `S_SPP1` does. `E_PAEP`, `S_PRL` and `S_IGFBP1` are downstream of
  neither node.

  *Corrected after review. An earlier revision called this null
  "condition-relative" and offered a progestin-without-cAMP arm as the example
  that would unmask it. That is false: without cAMP, `S_DECIDUALIZED` is 0, so
  adhesion is 0 anyway and nothing on O moves. The claim was checked
  exhaustively rather than re-argued — see §5.4.1.*
- **`E_PODXL`** is `not E_SECRETORY_STATE`, on only where the receptive surface
  is already impossible, and `E_MUC1_BARRIER` duplicates it in
  `X_ANTIADHESIVE_ROUTE`.

### 5.4.1 The classes are invariant over every input vector of v0.6.0

Review raised the `E_SPP1_EXPR`/`S_SPP1` null as falsely condition-relative. It
was, and checking it exhaustively showed the error is not confined to that pair.

The declared conditions give 10 input vectors. **`invariance()` in the same
module evaluates all 2^16 = 65,536 assignments of all 16 free variables** — the
11 protocol inputs, `E_KLF12_HIGH` and the 4 structural relays — and writes
`docs/stage4b/v060_veto_invariance.tsv`, which `pixi run veto-expressivity`
checks and `tests/unit/test_veto_expressivity.py` pins. Nothing is sampled and
nothing is weighted: a class either survives every assignment or it does not.
The result:

- **all 9 structural nulls are null on O for every input vector**, not only the
  declared ones;
- **no input vector splits any of the four classes.** `S_PGR`/`S_PKA`,
  `{E_LIF, E_GP130_STAT3, E_PC6, S_HAND2, S_TAZ_ECM}` and
  `{E_ITGAVB3_5, X_SPP1_LUMEN_FREE}` are each identical on O under *every*
  assignment of the protocol inputs.

So for v0.6.0 the classification is a property of the rules alone. The review
suggested recording the `S_PGR`/`S_PKA` alias as a genuine condition-relative
example instead; **that suggestion is also wrong**, and the same run shows it —
the pair is identical on O everywhere, so no arm of any kind separates them.
Adopting it would have replaced one false example with another.

What survives is the weaker and still important statement in §2a: L2 and L3 are
*recomputed* per version and per declared condition set, because a later version
or a wider condition set could change them. For v0.6.0 specifically, nothing in
the protocol inputs can. The §5.4 arguments above are therefore proofs about the
rules, not observations about the declared arms.

**How it is cheap enough to be a test.** The network is feed-forward, so one
pass in topological order evaluates every assignment at once if each node's
value across all 65,536 assignments is held as a single Python integer used as a
bit vector, with `and`/`or`/`not` becoming `&`/`|`/`~`. The whole exhaustive
check is then a few hundred integer operations and runs in about 2.5 seconds,
against roughly 1.5 million separate fixed-point evaluations the naive way.

**Why two implementations are kept.** `expressivity()` evaluates one assignment
at a time through `fixed_point()` and produces the per-condition table;
`invariance()` evaluates all of them at once through bitwise operators. They
share the parser and the arm list and nothing else, so a mistake in the operator
translation or the bit patterns would show up as disagreement. A test asserts
they agree on which arms are null, which is what rules out a translation bug in
either.

*This section previously said the exhaustive check was "a design-time
verification, not a committed artefact". Independent review was right to call
that a canonical claim with no reproducible transformation behind it: §11.1
rests on this result, so a reader of the frozen pre-registration must be able to
re-run it. It is now committed, checked and pinned like the per-condition table.*

### 5.5 Corrections to existing records (dated notes, no silent edit)

- O8b §7.3 flags `E_ITGAVB3_5` as "absorbed in its route (DTR009), so a veto is
  structurally near-inert", and §11 says approving anti-αvβ3 "would yield a
  near-null by construction". **Both are wrong.** A veto of `E_ITGAVB3_5` removes
  the SPP1 route, exactly as anti-SPP1 does (class A2), and
  `test_the_integrin_veto_is_not_inert` pins that.
- The coupling rows `E_ITGAVB3_5` ("an integrin blockade is therefore
  unrepresentable"; "no perturbation here can reach the integrin alone") and
  `S_TAZ_ECM` ("the TAZ arm contributes nothing there") are true of the
  *unperturbed* composed function, where the conjunct is implied; they are not
  true of a node-level veto, which makes that conjunct binding. Both date from
  2026-09-16, before the veto primitive existed, when a perturbation meant
  toggling an input.

The lesson is the plan's O6: baseline coupling and alias analysis do not predict
what a veto expresses. The proposal is a dated correction note on O8b §7.3 and
§11 and on the two coupling rows, original text kept. `config/` is a
closure-frozen path, so whether the coupling table can be annotated in place is
checked against `closure_replay` before any edit; if it cannot, the correction
lives in this document and the audit, and the coupling row is left alone.

### 5.6 Screen eligibility (L3) — and what it does *not* restrict

**Revised from the earlier draft**, which made structural nulls unapprovable.
That conflated L2 with L1: whether a veto moves an observed node is a property of
the model, not of the evidence, and refusing the licence would have written a
modelling limitation into a scientific verdict.

- **A structurally null target may be licensed and approved** on its evidence
  like any other. Its approval records the evidence; nothing more.
- Its library row carries a generated, non-editable marker
  `expressivity_class = null` in the run record, and the run is recorded
  `phenotype_claim_blocked`. The report may say that the model predicts no
  change in any observed readout under complete engagement of that target, and
  must say that this is a structural property of this version under the declared
  conditions. It may **not** be reported as evidence that the compound is
  inactive, nor as a negative result about the biology.
- **It is not screenable.** A null arm cannot enter a ranking, since its score is
  zero by construction.
- **Aliased targets may be approved and run**, with results reported at class
  level: a prediction for an A1 member may not be presented as discriminating it
  from the other A1 members, `hand2_loss` included.
- **4d stays blocked** until at least two approved interventions fall in
  different non-null classes on O. Today the artefact holds **4 non-null classes
  among single-node vetoes** (A1–A4), and a fifth formed by `mifepristone`, whose
  two targets put it in the union A3 ∪ A4. A multi-target intervention can
  therefore create a class its members do not have, so the 4 is a bound on
  single targets and not on what a library could express. It remains true that a
  ranking across these classes ranks relay priors (§5.3).
- Every one of these is computed from the committed artefact, so a later model
  version that gives a node a rule of its own un-blocks it automatically, with no
  re-adjudication of the licence.

## 6. The admission gate

### 6.1 Mechanical licence (G12 plus G13, at load)

A `direct_supported_effect` row is licensed if and only if:

1. every O8b condition holds (§4.2 of that note);
2. its intervention passes C1–C8 (§3.4). C6 contributes only its
   *classification* requirement here: an unclassified unrepresented target
   refuses the library, while a `scope_relevant` classification sets
   `compound_claim_blocked` on the run and never withholds the licence
   (owner decision 4);
3. the ledger row's `system_grade` is approvable (§6.3);
4. the ledger row's `target_declaration_sha256` equals the sha256 of the
   intervention's declaration row;
5. the committed expressivity artefact is current for that model version.

Being non-null is **not** a licence condition (§5.6). It is a reporting and
screening condition, enforced on the run record.

### 6.2 Ledger changes

The ledger grows from 15 to 17 columns: `system_grade` and
`target_declaration_sha256`. It holds no row, so nothing migrates.

### 6.3 `system_grade`: a conservative hierarchy, checked against the register

**Revised from the earlier draft**, which required primary cells literally. The
repository's own evidence shows why that is both too narrow and not what matters:

- the ADOC system itself (`SOFIA-*`) is a primary-cell organ-on-chip, not
  "primary cells" in culture; a literal primary-cell rule would not obviously
  admit the system the model is *of*;
- the register's qualifying literature is mostly primary or primary-derived:
  `LIT-IL11-001` ("human primary endometrial epithelial cells"),
  `LIT-CAMP-001` and `LIT-IGFBP1-001` ("human primary endometrial stromal
  cells"), `LIT-IHH-002` (human endometrium in vivo, compartment-resolved);
- the two cases that actually failed are line-based: the STAT3 inhibitor in HES
  (an immortalised endometrial line) and the PC6 knockdown in HEC-1A (an
  endometrial carcinoma line), both inside `LIT-IL11-001`/`LIT-PC6-002` whose
  other panels are primary.

So the rule grades the system that produced **the cited measurement**, not the
paper:

| `system_grade` | definition | approvable |
|---|---|---|
| `human_endometrium_in_vivo` | human endometrial tissue, compartment-resolved | **yes** |
| `primary_human_endometrial` | primary human endometrial epithelial or stromal cells, including the ADOC chip and primary-derived organoids or assembloids, at any passage the source states | **yes** |
| `primary_derived_other` | another primary human endometrial preparation the source names and the reviewer judges equivalent, with the reason recorded | **yes**, and the reason is part of the basis record |
| `immortalised_endometrial_line` | an immortalised but non-tumour endometrial line (HES, and similar) | no, alone |
| `endometrial_carcinoma_line` | a carcinoma-derived line (HEC-1A, Ishikawa, and similar) | no, alone |
| `non_endometrial_human`, `non_human` | O8b's existing grounds | no |
| `synthetic_fixture` | fixtures only, with the O8b synthetic/real split extended to this column | fixtures only |

"Alone" is meant literally: a line result can support an approval when a
qualifying system carries the same measurement for the same agent, recorded as a
second evidence id with its own grade. One qualifying system is required; lines
may corroborate. This keeps O8b's `system_match` compartment rule unchanged and
adds the depth grading its §13 recorded as missing.

**With several evidence ids on one effect, `system_grade` grades the E2
measurement** — the one establishing that the node's activity is abolished
(§6.4). It is a single column because an approval rests on a single
demonstration of engagement; the other cited ids are corroboration and are not
silently averaged into it. Concretely:

- exactly one cited evidence id must carry the E2 measurement, and
  `system_grade` is *that* id's system. Which id it is, is named in
  `basis_record`;
- a second id showing the same agent abolishing the same node in a different
  system does not change the grade. If it is a *better* system, the approval
  should cite it as the E2 id instead;
- line-based evidence corroborates (§6.3's "alone") by being cited alongside a
  qualifying E2 id, never by raising the grade;
- an effect whose only abolition measurement is line-based is refused, however
  many such lines agree. Agreement among carcinoma lines is not a primary
  system.

So the column is unambiguous by construction: it grades one named measurement,
not a body of literature. Reviewers who want the per-id systems have them in the
verification records below.

The grade is read off a record that already exists where one is available:
`context/literature/reviews/*.primary-verification.tsv` carries a
`species_system` column per finding, alongside `perturbation_used` and
`proximal_measurement` — which are also what E1 and E2 need. A grade that
contradicts the `species_system` of a cited verification row is a defect, not a
judgement call. Ishikawa, which the references table uses for the β3 integrin
evidence, is `endometrial_carcinoma_line` on this scale.

### 6.4 What must be independently evidenced, and what stays judgement

Each item needs a cited measurement read in full text, with a figure or table
anchor in the basis record.

| id | evidence |
|---|---|
| E1 | the agent's identity, concentration or construct, and system (§3.3) |
| E2 | the node's activity **as defined** is abolished or blocked under that agent: O8b's three-step rule plus C5 coverage |
| E3 | the system grade (§6.3) and the compartment match (O8b) |
| E4 | the selectivity profile behind `known_target_entities`, at the evidence concentration (J1) |
| E5 | the reached compartments, if narrower than the default |
| E6 | that the evidence measured this agent, not another of the same class |

Reviewer judgement, recorded and checkable but not loader-checked: J1
completeness; J2 the `scope_relevant` / `out_of_scope` split; J3 the entity and
level readings; whether "blocked" means near-complete at the node's level; the
`primary_derived_other` equivalence; and the entity-map readings themselves.

### 6.5 Provenance (added to the O8b run record when a direct row is named)

- per intervention: `declaration_id`, its sha256, `library_rows_sha256`, and the
  `unrepresented_known_targets` with their classes;
- top level: path, sha256 and size of `node_entity_map.tsv`,
  `direct_effect_target_declarations.tsv` and the expressivity artefact;
- per direct effect: `expressivity_class`, its class over O plus the
  `reported_only` phenotypes, and the class members, so a report cannot drop the
  alias;
- run-level flags: `phenotype_claim_blocked` (a null target) and
  `compound_claim_blocked` (a `scope_relevant` unrepresented target);
- `construction_overlap`, generated: the reference ids cited by the approval that
  also support an edge on a path from the target to O. For PC6 this flags REF-011,
  which is both the knockdown source (LIT-PC6-002) and a source of the
  PC6 → DAG1 → receptive-surface edges (LIT-PC6-001; LE011, LE012, LE027, LE033).
  A source's phenotype result in that set **cannot be used as validation** of the
  prediction: it is circular by construction. It is recorded, not refused.

### 6.6 Failure behaviour

- Any failure of §6.1 refuses the whole library at load and names the
  intervention, node, entity and rule. Nothing runs, no effect is dropped, there
  is no fallback to the approved subset. This is the O8 convention.
- A missing or stale expressivity artefact — either the per-condition table or
  the invariance table — fails `veto-expressivity` and
  `tests/unit/test_veto_expressivity.py` today. Extending
  `validate-direct-effects` to fail on it too is part of §10, not yet built. A
  version with no current artefact may not hold an approved executable row,
  because the run record could not carry its class.
- The generator refuses a non-self-loop cycle, a node declaring a transition
  rate, a cfg that sets a free variable, and a mixed istate on a protocol input
  (in a cfg or in the baseline). Each is a case where the exact fixed-point
  argument of §5.2 does not hold. Such a version cannot hold an approval until a
  substitute method is
  pre-registered.
- An approval that is mechanically valid but whose reviewer judgement is disputed
  stays `candidate`. The loader never resolves a dispute.

### 6.7 Additional conditions for 4c (not run here)

- **Independent review.** The first real approval requires a non-degraded
  independent verdict on the exact admission state, or the owner's `aih accept`
  with the stand-in caveat stated. A same-family stand-in PASS is not sufficient
  for promoting the first real compound.
- **An informative target**, or an explicit decision to run a null or blocked
  one with the §5.6 and §3.5 reporting restrictions stated in the 4c
  pre-registration before the run.
- **Comparison** with the matched unperturbed twin, same protocol and seeds,
  absolute changes, stated trajectory counts and a seed-spread check. Fixed seeds
  give reproducibility, not Monte Carlo stability.
- **Staged gates:** a bounded smoke before any full run, outputs kept separate.
- **Claim boundary:** complete-engagement counterfactual (§4.2), direction-only
  (§5.3), class-level (§5.6), with construction-circular sources named (§6.5).

## 7. Gate G13 (tests for the Stage 4b implementation)

Static unless marked, synthetic fixtures only. G13 must refuse:

- a direct intervention with no declaration (C1); a stale `library_rows_sha256`
  or a mismatched target set (C2);
- a known entity mapping to an undeclared node in a reached compartment — fixture:
  a PGR-like entity declared on `S_PGR` only, bath-applied (C3);
- a known entity mapping to a policy-refused node that carries it, with a
  role-refusal fixture (`E_PAEP`, a readout) and two node-refusal fixtures
  (`E_MUC1_BARRIER` and `E_DAG1_CLEAVED`), which together prove §3.2's
  aggregation rule is doing work — under a blanket `derived` each of these three
  agents would pass unnoticed (C3);
- a narrowed compartment with no resolving source (C4);
- a subset of an `any_of` node, and an `ambiguous` or `derived` target (C5),
  including **`E_ITGAVB3_5` under an anti-αv declaration**, which §3.2.1 makes
  unapprovable in v0.6.0 and which an earlier revision wrongly said would pass;
- an **unclassified** unrepresented known target, and one that calls a
  `catalog_only` or staged-candidate entity `out_of_scope` (C6). A
  `scope_relevant` classification must **not** be refused — it is tested under
  "must accept" below;
- a declared target with no named entity (C7);
- a mismatched `target_declaration_sha256` (C8);
- a non-approvable `system_grade`, including a line-only approval, and the
  synthetic/real split on the new column;
- a stale expressivity artefact, and each generator refusal of §5.2: a cyclic
  network, a declared transition rate, a free-variable-setting cfg, a mixed or
  multi-node istate, an uninterpreted istate value, a veto of a free node, a
  missing reference context, an unknown `activation_status`, and more hand-set
  free variables than the scenario cap;
- **an N+1 admission that modifies `node_entity_map.tsv`** (§3.2);
- an engagement argument on any execution path (§4.5).

G13 must accept:

- a declaration forcing two compartments, with both declared;
- an `all_of` node hit through one member;
- a line-corroborated approval whose qualifying evidence is primary;
- **an approved null target**, which must license and execute, with
  `phenotype_claim_blocked` set — the test that §5.6 did not quietly become a
  refusal;
- a `scope_relevant` unrepresented target, which must execute with
  `compound_claim_blocked` set.

G13 must check the artefact: the regenerated table equals the committed one; the
classification reproduces §5.3 (pinned in `tests/unit/test_veto_expressivity.py`,
already committed); and, as an **integration** test, one member of each class
run bounded in the `tests/fixtures/o8_markerless/` sandbox agrees with the
artefact's class on O at stated trajectory counts.

That integration check compares a **finite** run against an **asymptotic**
value. The baseline cfg stops at `max_time = 20`, so a trajectory need not have
reached the fixed point, and Monte-Carlo error adds to that. The check must
therefore be registered with an explicit tolerance and trajectory count, and it
tests *agreement of class* — which arms move a readout and which do not — never
equality of the marginal. A pre-registered tolerance belongs in the 4b
implementation, not here, and asserting exact equality would make the test fail
for a reason that has nothing to do with the classification.

The N+1 gate is restated with **four** appended files — the evidence register,
the declaration, the ledger and the library — while `models/`, `src/` **and
`config/node_entity_map.tsv`** stay byte-identical. The entity map is a reading
of the model version, not compound data (§3.2), so an ordinary compound
admission may not touch it; the gate asserts that rather than permitting it "if
needed".

*Corrected 2026-10-04 on the owner's reading of the pushed document. This
sentence previously said "five appended files (register, entity map if needed,
declaration, ledger, library)", which contradicted §3.2 and would have let an
admission clear its own C3 or C5 refusal by re-reading what a node means. If a
compound genuinely needs a node the map does not describe, that is a model-reading
decision taken on its own, before and separately from the admission, and it is
not an N+1 operation.*

## 8. Non-goals

- No real declaration, approval or library row.
- No screen, ranking, score or synergy, and no prediction from a direct row.
- No partial engagement, dose, PK, rate scaling or second mode.
- No model-only target-ablation category (§4.3); a separate future unit.
- No change to v0.6.0 rules, relay priors or the observation map.
- No change to the migrated rows' licences.
- O1, O2, O3, `dropout_e2`, D2/D3 untouched.
- No edit to the coupling table or O8b text beyond the dated notes of §5.5.

## 9. What is already implemented (this revision)

Only the §5 artefact, which the owner asked to be reproducible:

| file | role |
|---|---|
| `src/dt_adoc/reporting/veto_expressivity.py` | generator; exact asymptotic marginals, refusing the cases the method does not cover |
| `docs/stage4b/v060_veto_expressivity.tsv` | the committed classification of 19 eligible targets and 3 veto-mode library interventions, under the declared conditions |
| `docs/stage4b/v060_veto_invariance.tsv` | the same classification under **every** assignment of every free variable (§5.4.1), which is what licenses the rule-wide claims |
| `tests/unit/test_veto_expressivity.py` | pins the nulls, the classes, the relay-prior baselines, the integrin correction, and each of the generator's refusals |
| `pixi.toml` task `veto-expressivity` | `check` verifies **both** committed artefacts; `write` regenerates them |

The repository has no CI workflow, so nothing runs `veto-expressivity`
automatically; `pixi run test` discovers the unit test, which makes the same
comparison. Adding the task to an aggregate check is a one-line change left for
§10, so that the two new config tables and this artefact are wired in together.

It is deliberately outside `concordance.simulate.IMPLEMENTATION_GLOBS`: it
generates no simulation result and no execution path reads it, so it must not
force a regeneration of the digest-pinned artifacts.

## 10. Smallest remaining implementation (after acceptance)

1. Data: `config/node_entity_map.tsv` (45 v0.6.0 nodes plus 4 gap rows) and an
   empty `config/direct_effect_target_declarations.tsv`; the ledger header gains
   two columns.
2. Code: `perturbations/adjudication.py` gains C1–C8 and §6.1; `engine.py` adds
   the §6.5 provenance fields.
3. Wiring: both new config files into `closure_replay.POST_CLOSURE_FILES` (a new
   `config/` file otherwise fails the Phase 2B closure replay) and into
   `concordance.simulate.IMPLEMENTATION_GLOBS` — they determine executed
   networks, as the O8b tables do.
4. Cost: those files are in the implementation digest, so **one** sequential
   regeneration of the four digest-pinned artifacts (~55 min, capped systemd
   unit, verified-clean committed tree) at the end. No scientific number should
   move. Batch every code edit before it.

## 11. Owner decisions, taken 2026-10-04

The owner accepted the design on 2026-10-04. These are the decisions as taken;
each is binding on 4c and 4d, and changing one is a change to this
pre-registration rather than an implementation choice.

| # | decision | taken |
|---|---|---|
| 1 | §2 staging | The 4b / 4c / 4d split is adopted. Model-only target knockouts stay a **separate later unit** from named-compound admission |
| 2 | §4 engagement | Partial and graded engagement stay out of scope. The executable result is a complete-engagement counterfactual. The mixture formula applies **only** to a population of fully affected and unaffected units, never to graded inhibition within a cell |
| 3 | §2a, §5.6 | Scientific licence, model expressivity and screen eligibility stay separate. A structurally null target may be licensed on its evidence, labelled structural-null and not-screenable, with no phenotype claim |
| 4 | §3.5 | A known effect on an unrepresented target refuses **compound-level prediction** when the target is in a relevant reachable compartment and could affect the modelled endpoint. An effect clearly outside the modelled scope or compartment stays explicit in the claim boundary instead |
| 5 | §6.3 | No literal primary-cells-only rule. Primary cells, tissue or explant, organoid, and defensible primary-derived systems may support approval; carcinoma- or immortalised-line evidence alone may not, though it may corroborate |
| 6 | §5.2, §5.6 | Screenability is distinguishability by **asymptotic marginals on the measured set O under the declared conditions**. Whole-model-state distinguishability is explicitly **not** the screen criterion. Transient distinguishability is a separate later question, to be reopened only if temporal observations justify it |
| 7 | §3.2.1 | **`E_ITGAVB3_5` is unapprovable in v0.6.0**, anti-αv included, and stays so until TI-03 splits αvβ3 from αvβ5. The flat aggregation vocabulary is **not** extended with a complex or hitting-set representation to accommodate it |

### 11.1 What decision 6 commits to, in full

It was raised by review as an unconsulted methodological choice, so the
commitments are recorded rather than left implicit. Two interventions count as
distinguishable when their **asymptotic** marginals differ on O (defined
exhaustively in §5.2). Three things follow, and each could have been set
otherwise:

- **Transients are excluded.** Two arms differing only in how fast they reach
  the same fixed point are one class. Model time is relative and uncalibrated, so
  a transient difference is not a predicted observable; the cost is that a
  genuinely faster-acting agent is invisible here. Including transients would
  need a declared time grid and a tolerance, neither pre-registered. The owner
  has left this reopenable if temporal observations arrive.
- **O is the measured set, not the model state.** Distinguishability is about
  what the ADOC assays could see. Widening O to the two `reported_only`
  phenotypes splits two classes immediately, which §5.3 reports separately.
  Defining L3 on the whole model state would make nearly every target
  distinguishable and would make the screen a statement about the model rather
  than about anything measurable; the owner has rejected that.
- **The declared condition set bounds it, in principle.** A class is computed
  across the conditions the cfgs declare, and a wider set could in general split
  one. **For v0.6.0 it cannot:** §5.4.1 checks all 65,536 free-variable
  assignments — committed as `docs/stage4b/v060_veto_invariance.tsv` and pinned
  by a test — and finds every null and every class invariant. So decision 6's condition-relativity is
  real as a rule for later versions, and vacuous for this one — which is the
  safer way round, since it means no undeclared arm is quietly holding a class
  together.

### 11.3 What decision 7 commits to, and what reopens it

Taken on the owner's acceptance of 2026-10-04, after review showed C5's flat
`any_of`/`all_of` vocabulary cannot represent the node (§3.2.1). Recorded as a
decision rather than left as an implementation choice, because it narrows the
approvable set and because the alternative is a standing invitation to add
machinery later without anyone deciding to.

- **No direct intervention may be approved on `E_ITGAVB3_5` in v0.6.0.** That
  includes an anti-αv agent, which genuinely would abolish the node's activity:
  the refusal is about what the licensing layer can *state*, not about the agent.
- **The flat vocabulary is not extended.** A complex or hitting-set
  representation would describe a distinction the executable model does not
  carry — v0.6.0 has one integrin node, so αvβ3 and αvβ5 are one Boolean
  variable and no intervention can reach one of them. A licence must not be able
  to say more than the model can mean.
- **What reopens it is TI-03, not a better agent and not a better declaration.**
  Once the node is split, each complex is a `single` entity and the existing
  vocabulary suffices; no machinery is ever needed. Until then the answer does
  not depend on who asks.
- **The expressivity artefact is untouched.** `E_ITGAVB3_5` stays O8c-eligible
  and stays in class A2. Eligible, unapprovable and expressive are three
  different statuses, and this node holds all three at once — which is the §2a
  separation doing visible work rather than failing.

### 11.2 Still open, and not blocking this pre-registration

- §3.2: `E_ANXA2_ACTIN` and `S_PKA` are `ambiguous` in the entity map and so
  unapprovable. They stay refused by default and no approval may resolve one;
  each needs a recorded decision about what its node means.
  (`E_ITGAVB3_5` is also `ambiguous`, but it is no longer open — it is decision
  7, and §11.3 records what settles it.)
- Sequencing: whether the model-only target-ablation unit runs before 4c. It
  needs none of this governance and would exercise the same artefact.
