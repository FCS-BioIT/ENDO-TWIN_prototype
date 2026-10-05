# Intervention-layer refactor — plan, 2026-10-01

**Status: plan adopted by the owner. Stages 1 and 2 are complete and merged
(PRs #13, #14). Stage 4a was authorised by the owner on 2026-10-01, ahead of
Stage 3, and is recorded in §5.2. O8 is addressed
by its own unit, recorded in `docs/o8_markerless_interventions.md`, and its
timing follow-up O8a by `docs/protocol_intervention_timing.md`. Stage 3 was
authorised by the owner on 2026-10-03 and is recorded in
`docs/intervention_layer_stage3.md`: it adds `adoc-literature-superset-v0.6.0`,
v0.5.2 without its three marker nodes, and gate G8. O8b/O8c, the scientific
licence of a direct row and its target-role policy, are recorded in
`docs/o8b_direct_effect_governance.md` (gate G12).** The rest of this
paragraph describes Stages 1, 2 and 4a, as it did when written. None of them changes a model, a protocol or a
result. Stages 1 and 2 are semantics-preserving refactors; Stage 4a adds a
capability, and leaves every existing call byte-identical. Stage 1 added one configuration file, `config/intervention_library.tsv`.
Stage 2 makes the runner read it for v0.5.2, with results that are bit-identical
to the legacy route (G7). Stage 4a adds composition, and produces no result: it
makes combinations executable and provable, and leaves running one to a unit of
its own. The v0.5 pause
(`docs/v05_pause_decision_2026-09-30.md`) explicitly leaves room for exactly this
kind of change, provided it has its own unit, its own equivalence evidence and its
own review. This document is the record for both units.

## 1. Problem

The DT is meant eventually to screen hundreds to thousands of compounds and other
interventions for their effect on adhesion. Today an intervention is a MaBoSS node
(`IN_MIFEPRISTONE`, `IN_ANTI_SPP1`, `IN_HAND2_LOSS`, `IN_XAV939`), with its effect
written into the downstream rules as `... and not IN_X`. Carried to a screen, that
representation:

- grows the topology with the compound library;
- repeats the same veto logic for every compound that hits the same target;
- handles multi-target compounds and combinations only by adding more inputs and
  more conjuncts;
- forces a new model version for each new compound;
- mixes reagent identity into the state space, so structural and identifiability
  analyses count reagents as if they were biology. This happens today:
  `docs/identifiability_analysis.md` (v0.4.0) counts the reagent nodes among
  the 14 declared inputs, and
  `drug_target_catalog.tsv` lists `IN_MIFEPRISTONE` and `IN_ANTI_SPP1` as
  targets.

The fix separates what an intervention **is** (a reagent or manipulation), what it
**does** (an effect on a biological node) and **when** it is active (a protocol
phase).

## 2. Current executable semantics (v0.5.2)

The canonical model is `models/superset/adoc-literature-superset-v0.5.2/`. Its
`network.bnd` declares **no** `rate_up` or `rate_down` anywhere, so every node runs
on MaBoSS's default rates: up-rate `@logic ? 1 : 0`, down-rate `@logic ? 0 : 1`.
Every input node has `logic = <self>`: it is constant within a phase and changes
only at phase boundaries, through the protocol's `input_states`. The runner writes
each phase's `input_states` both into the merged cfg (`IN_X.istate`) and into the
continuation's `forced_nodes`.

| input | every rule that reads it | phases where it is 1 | executable effect when 1 |
|---|---|---|---|
| `IN_MIFEPRISTONE` | `E_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE`; `S_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE` | `hormone_treated_mifepristone` and its challenge, after `hormone_treated_maternal` | Both rules become false. Neither node can switch on, and an active one switches off at the default down-rate of 1. |
| `IN_ANTI_SPP1` | `X_SPP1_LUMEN_FREE = (E_SPP1_EXPR or S_SPP1) and not IN_ANTI_SPP1` | `hormone_treated_anti_spp1` and its challenge; **lifted** in `washout` | Same, on the free luminal pool only. `E_SPP1_EXPR` and `S_SPP1` are untouched. |
| `IN_HAND2_LOSS` | `S_HAND2 = (S_BMP2 or S_PGR) and not IN_HAND2_LOSS` | `hormone_treated_hand2_loss` and its challenge | Same, on `S_HAND2`. This is the only input with `is_internal = FALSE`, so it appears in MaBoSS state labels. |
| `IN_XAV939` | none | every hormone-treated phase | None. No rule reads it. |

Each of the three effective inputs vetoes **the whole rule** of each node that
reads it. None of them masks a single term of a rule, appears in an activation
clause, or carries a rate. That is a property of v0.5.2, not a general one.
The reference parent `adoc-core-v0.1.0` puts
`and not IN_MIFEPRISTONE and (not IN_ANTI_SPP1 or X_ADHESION_ROUTE_REDUNDANT)`
inside `OUT_MATERNAL_ADHESION_COMPETENCE`, which masks terms of a rule rather
than a whole node. It also uses `IN_ANTI_SPP1` as an *activating* conjunct of
`X_ANTIADHESIVE_ROUTE`. **Earlier model versions are not migrated.**

**Time course.** An intervention that starts after a phase in which its target was
active does not set the target to OFF instantly. The target loses its activating
rule and decays stochastically at rate 1. This is what the equivalence gates must
preserve. Two existing mechanisms do *not* preserve it:

- pyMaBoSS `mutate(node, "OFF")`, which renders down-rate `1E308/$nb_mutable`, an
  effectively instantaneous clamp;
- forcing the target through `istate` or `forced_nodes`. That is also
  instantaneous, and the runner excludes forced nodes from the state carried into
  the next phase (`simulation/runner.py`, `build_continuation`).

**`IN_XAV939` is executable-inert, not biologically ineffective.** XAV939 is part
of the ADOC hormone cocktail (`config/protocols.yaml`: "10 nM E2 + 1 uM MPA + 250
uM cAMP + 10 uM XAV939"). The model encodes no effect for it, and the protocol
note states that the design has no single-agent arm. "No executable effect" is a
statement about this model's rules, and no claim is made about the reagent.

### 2.1 Classification of the v0.5.2 inputs

For the intervention identities and experimental conditions, the repository's
own `model_role` in `node_dictionary.tsv` (`perturbation_input`,
`pathology_input`, `boundary_input`) already draws this distinction, and the
refactor adopts it. `node_dictionary.tsv` gives `IN_XAV939` and `IN_cAMP` the same
role, `input`, as `IN_E2` and `IN_PROGESTIN`. Calling them protocol reagents is
this plan's reading, and O1 and O2 keep it open.

| class | inputs | fate in this refactor |
|---|---|---|
| biological or environmental input | `IN_E2`, `IN_PROGESTIN`, `IN_EMBRYO_PRESENT`, `IN_TROPHECTODERM_COMPETENT`, `IN_EMBRYO_CONTACT`, `IN_HCG`, `IN_EMBRYO_CONDITIONED_SIGNAL` | stays in the biological model |
| experimental condition (`pathology_input`, `boundary_input`) | `IN_ER_STRESS_EXCESS`, `IN_HIGH_ECM_STIFFNESS` | stays; see open question O3 |
| intervention identity (`perturbation_input`) | `IN_MIFEPRISTONE`, `IN_ANTI_SPP1`, `IN_HAND2_LOSS` (genetic loss of function, still an intervention) | moves to the intervention library |
| protocol reagent with no encoded effect | `IN_XAV939` | recorded in the library as `no_executable_effect`; final treatment is open question O2 |
| protocol reagent, unresolved | `IN_cAMP` | untouched; open question O1 |

## 3. Target architecture

| layer | owns | must not contain |
|---|---|---|
| **Biological model** (`models/**/network.bnd`, `.cfg`) | biological states and processes, plus genuine environmental or biological inputs | compound or reagent identities |
| **Protocol** (`config/protocols.yaml`, `protocols/conditions.py`) | which interventions are active in which phase; durations, horizons, continuation; dose metadata if ever recorded | mechanism: what an intervention does |
| **Intervention library** (`config/intervention_library.tsv`) | intervention → one or more (target node, mode) effects, each with provenance | timing, rates, pharmacokinetics, engagement values, targets not already in the model's executable semantics |
| **Perturbation engine** (`src/dt_adoc/perturbations/engine.py`) | rendering effects into an executable, hashable `.bnd` text through the existing `render_network_with_logic_overrides` | biology; any rendering that is not an exact, documented primitive |

The engine renders text and does not wrap MaBoSS at runtime. That is because the
backend is cmaboss, which has no mutation API, and because provenance here is
file-hash based. A rendered `.bnd` can be hashed, diffed and reviewed; an
in-memory mutation cannot.

The library is a **new file**. `drug_target_catalog.tsv` is the obvious home but
is part of the v0.5.2 model tree, and both `provenance.toml` and the C3a binding
hash it. `context/literature/perturbations.tsv` (PERT-001, PERT-002) and the
catalog stay as sources the library cites.

## 4. The first primitive: `activity_veto`

`activity_veto(target)` renders the target's logic as

```
logic = (<existing logic>) and not 1;
```

and leaves every other line of the `.bnd` unchanged.

- **While active,** the target's logic is false under every assignment. With the
  default rates, it cannot switch on (up-rate 0), and if it is on it switches off
  at the model's default down-rate of 1. That is exactly the legacy behaviour of
  `IN_X = 1` on every reader.
- **When lifted** (the next phase renders without the veto), the original rule
  applies again, as when the legacy input returns to 0, for example in `washout`.
- The existing rule stays visible inside the rendered line, so the rendered file
  shows what was vetoed rather than replacing the rule with a bare `0`.
- `1` is a numeric literal. MaBoSS rejects `TRUE` and `FALSE` in logic.

**Preconditions, enforced by the engine:**

- The target exists, has exactly one logic line, and is not an input
  (`logic = <self>`).
- The target node declares no explicit rate. The primitive's meaning rests on
  default rates, so the engine refuses rather than guesses when a rate is
  declared.
- The library row's `model_version` equals the model being rendered.

`no_executable_effect` renders nothing. It records an intervention for which this
model version encodes no effect.

## 5. Migration stages

1. **Stage 1 (done).** Library, engine and equivalence tests. Nothing was wired
   into the production runner, the CLI, the protocols or any model.
2. **Stage 2 (done; see §5.1).** The runner executes library-covered
   interventions through the engine, while v0.5.2 and its `IN_*` nodes stay as
   they are. It needs same-seed equivalence on every declared lineage and its own
   review.
3. **Stage 3.** Only after Stage 2 has been accepted: a new model version with the
   reagent nodes and their `and not IN_X` conjuncts removed, generated rather than
   hand-edited. Removing nodes changes the state space, the free-variable count
   (2^19 → 2^16), the identifiability tables and the state labels, so this needs
   its own decision and review. Closed phases stay replayable against v0.5.2.
4. **Stage 4a (done; see §5.2).** Composition: multi-target compounds and
   combinations at full engagement, executable through the runner. No screen is
   run and no prediction is committed.
5. **Stage 4b.** A screen over a larger library, which needs its own
   pre-registration because it produces results. Graded engagement only after a
   separate decision (O4, O5).

### 5.1 Stage 2 as implemented

- **Where.** `run_cmaboss_condition` in `simulation/runner.py`.
  - Every `run_protocol` caller passes through it, and so does
    `calibration/observation_map.py`, which builds its own inputs.
  - One caller does not: `scrna/klf12_conditioning.py` loads MaBoSS directly. It
    is pinned to v0.4.0, which the library does not cover, so nothing it computes
    changes. A future caller on a covered version must go through the runner.
- **What it renders.** For a model version the library covers (today only
  v0.5.2), `engine.legacy_route_overrides` rewrites every targeted rule:
  - its legacy inputs are replaced by `0`, so no rule reads them;
  - the veto is added when one of the interventions acting on that rule is active
    in the phase.

  "Active" means the value MaBoSS will start the legacy input at, read in the
  order the runner applies it:
  1. the merged cfg's istate;
  2. then the continuation, either the previous result's last marginal (marginal
     mode) or the joint distribution, when the input is one of its memory nodes;
  3. then `forced_nodes`.

  A value that is not exactly 0 or 1 is refused, and so is a joint istate key
  (`[..., IN_X].istate`) naming a legacy input. Each legacy input's own rule
  must be `logic = IN_X;` with no kinetics, so it stays constant within a phase.
  A root without the library routes nothing.
- **The legacy nodes become markers.** The `IN_*` node keeps the value the
  protocol gives it. So the merged cfg, the state labels and every output are
  unchanged, and the node only marks when the intervention is active. This is
  stricter than holding the input at 0, as G5 does: nothing has to be projected
  out.
- **Self-check.** Before rendering, every targeted rule is checked exhaustively
  against the legacy rule, under every combination of legacy-input values and not
  only the current phase's. A mapping that is not a pure veto of its target is
  refused in every phase. Phases with several legacy inputs active, which no
  v0.5.2 protocol declares, are covered by the same check. That makes them
  legacy-equivalent, not Stage 4 combinations.
- **Switch.** `runner.INTERVENTION_ROUTING` is `"engine"` by default. `"legacy"`
  exists so that G7 can compare the two routes.
- **Provenance.**
  - Each `ConditionRunResult` carries `executed_network`: the source network, the
    overrides (with the nodes the engine owns listed separately from rule
    variants), the routing, the library's path and sha256, and the sha256 of the
    exact text MaBoSS loaded.
  - The structural-smoke manifest lists one such record per phase.
  - The rendered `.bnd` is deleted once the run ends, whether it succeeded or
    failed, because the record reconstructs it.
- **Implementation digest.** `concordance.simulate.IMPLEMENTATION_GLOBS` now
  includes `perturbations/engine.py` and the library, because together they now
  determine executed networks.
- **Left alone.** The HAND2 injection in `protocols/conditions.py` stays a
  literal. It serves every superset from v0.4.0 onward, and the library is scoped
  to v0.5.2, so a lookup would tie earlier models to a v0.5.2 mapping without
  changing anything. It is part of the protocol layer's "when", which stays in
  `IN_*` form until Stage 3.

### 5.2 Stage 4a as implemented

Stage 4a was chosen ahead of Stage 3, on a reason that was then found to be
wrong and is corrected here.

**The reason given was that Stages 1 and 2 had already removed the barrier to
scale, so that a compound could be added to the library and run without touching
the network. That is false, and measuring it is what showed it.** A library row
must name a `legacy_input_node`, and the Stage 2 self-check requires the row's
rendering to reproduce that input's existing veto. So a row can only ever
re-describe a veto the `.bnd` already contains. A new compound is refused under
either spelling: a marker that is not a node fails as "not a constant input
node", and reusing an unused input fails the self-check as "not equivalent to the
legacy rule".

What Stages 1 and 2 achieved is therefore narrower than claimed: the three
declared interventions are described in a library and applied by an engine
instead of by rules, and `IN_*` survives only as a marker. **The screening goal
is not yet met**, and Stage 4a does not meet it either: it recombines declared
interventions and cannot introduce one the model does not encode (O8).

Stage 4a is still worth having on its own terms -- combinations and multi-target
compounds are a prerequisite for any screen, and they are now executable and
gated -- but it is a step toward the goal, not its arrival.

- **Composition.** `intervention_logic_overrides` accepts several interventions
  and returns the union of their effects.
  - A compound with several targets vetoes each. The library already expressed
    this: mifepristone is two rows, `E_PGR` and `S_PGR`.
  - Two interventions on one target leave one veto. The veto makes the rule false
    whatever else holds, so a second changes nothing. That is an algebraic
    consequence of the primitive, not a claim about potency: this model carries
    no dose, so "both hit this node" and "one hits it" are the same executable
    state.
  - Two interventions claiming one target under different modes are refused.
    Only `activity_veto` has a target today, so this cannot yet fire; it is there
    so that adding a mode cannot silently resolve a conflict.
  - Naming the same intervention twice is refused.
- **Execution.** `run_cmaboss_condition` and `run_protocol` take
  `interventions=`, naming library interventions active on top of whatever the
  protocol declares. They are rendered from the Stage 2 *disconnected* rules, so
  no rule reads a legacy input, and they are applied after the Stage 2
  self-check, which therefore keeps its meaning: the check establishes that the
  phase's legacy-driven rendering reproduces the legacy model, and a named
  intervention is a declared departure from it.
- **Refusals.** Naming an intervention whose own legacy input is already active
  in that phase, which can only arise for one that has a veto and therefore a
  marker; naming one under legacy routing (silently dropping it would run an
  unperturbed model under a perturbed name); naming one for a model version the
  library does not cover, or against a root with no library; passing a bare
  string instead of a sequence of ids.
- **Provenance.** `executed_network` records `named_interventions`, so a named
  run and a marker run stay distinguishable even where they agree.
- **No result is produced.** A combination's prediction is a conditional
  model-internal statement and nothing more; AGENTS.md requires it to be compared
  with the matched unperturbed twin and reported with uncertainty. Producing one
  is Stage 4b, with its own pre-registration. The tests assert rendering and
  equivalence, never an endpoint value.
- **Not a claim about the compounds.** Composition says what applying both means
  in this model. It is not evidence that the compounds interact, and a synergy
  score over such runs would be a statement about simulated trajectory
  frequencies under stated rules.

## 6. Equivalence gates

Gates G1–G6 are Stage 1 tests, G7 is the Stage 2 test and G9 is the Stage 4a
test. G8 applies to Stage 3.

| gate | requirement |
|---|---|
| G1 Library resolution | Every library target and legacy input is a node of the stated model. For each legacy input, the library's target set equals the set of rules that read it, derived from the `.bnd`, with none extra and none missing. The `config/perturbations.yaml` entries that toggle a library input are exactly the ones the library names, and each named entry targets that input. A veto row must name at least one. The `no_executable_effect` row (XAV939) names none, because no declared perturbation toggles its input, and the same test checks that none does. |
| G2 Rule equivalence | For each target, the rendered rule with the legacy input at 0 equals the legacy rule with the input at 1, exhaustively over every assignment of the rule's variables. With no intervention, rendering is the identity. |
| G3 Locality | Rendering changes only the logic line of the target nodes. Every other byte of the `.bnd` is unchanged, and no `rate_up`, `rate_down` or other kinetic line appears. |
| G4 Refusals | Each of these is refused: an unknown intervention; a model-version mismatch; more than one intervention at once (combinations are Stage 4); an input node as target; a target with an explicit rate; an unknown mode. |
| G5 Same-seed protocol runs | The mifepristone, anti-SPP1, HAND2-loss and washout lineages are run end to end on v0.5.2. The legacy route uses the protocols unchanged. The engine route sets the legacy input to 0 in every phase and renders `activity_veto` in exactly the phases where the legacy input was 1, through the production `run_cmaboss_condition` path. Two seeds are used. Result: every non-input column of `nodes_probtraj`, the last-node marginals, and the last-state distribution projected onto non-input nodes are bit-identical. Comparing whole state labels would be invalid for HAND2, whose input appears in them, so the projection is required. |
| G6 Negative controls | The same G5 comparison with a pyMaBoSS-style fast clamp (up-rate 0, down-rate `1E308/n` for n clamped nodes) replacing the veto **must fail** on the mifepristone lineage. That is the lineage in which the targets are already active when the intervention starts. Holding the input at 0 without rendering the veto must also fail on every lineage, so a route whose overrides never reach MaBoSS cannot pass. |
| G7 (Stage 2) | **Comparison.** Every v0.5.2 protocol lineage (15, chained through `run_protocol` and `protocol_continuation`) and every condition in the v0.5.2 condition suite run as a single phase (21) is executed with routing `"engine"` and `"legacy"`, at seeds 1 and 2. The two routes are bit-identical on full `nodes_probtraj`, full labelled last-state distributions, last-node marginals and the merged cfg. **Rendering checks.** The networks MaBoSS loads under the engine route read no legacy input and carry the veto only in the active phases. Removing the veto is refused by the self-check. A model the library does not cover still loads its own file. **Provenance.** Each run's `executed_network` record rebuilds the loaded text exactly, and the rendered file is gone after a successful run and after a failed one. A real structural-smoke run on v0.5.2 writes those records into its manifest. It runs with the three maternal phases that the default smoke list omits inserted, because without them that list fails before any routing code runs. **Not covered by a run.** Marginal continuation mode crashes MaBoSS on both routes in the pinned runtime (a pre-existing segfault in `cmabossresult` when the last marginals are read), so its input-value rule is tested statically only. |
| G9 (Stage 4a) | **Equivalence.** The HAND2-loss arm and the control arm have the same four phases, durations and cfgs, differing only by `IN_HAND2_LOSS`. So naming `hand2_loss` on the control arm must reproduce the declared arm, at two seeds, on everything that is not an input. The two routes in fact render the *same network text* (`network_sha256` equal), so this is an identity of plumbing rather than a statistical agreement — the check that the named path and the marker path are one mechanism rather than two that happen to agree. **Parity.** For every subset of the library, the documented composition (`intervention_logic_overrides`, against the model's rules) and the executed one (`legacy_route_overrides(also_active=)`, against the disconnected rules) veto the same targets, and no rendering carries a doubled veto. **Power.** Naming one must change the result, or the agreement above is vacuous. **Composition.** A combination's vetoes are exactly the union of its members'; an inert member changes nothing; a shared target is vetoed once. **Refusals.** Double application, legacy routing and unknown members are each refused. |
| G11 (O8a) | Protocol-declared step timing reproduces marker timing: mifepristone, anti-SPP1, HAND2 loss and the anti-SPP1 washout, with the marker OFF and the name declared in the marker's phases, are identical to the canonical lineages phase by phase at three seeds, on the executed network and everything that is not the marker. Mistimed controls must fail. A markerless compound switches OFF → ON → OFF across steps. See `docs/protocol_intervention_timing.md` §8. |
| G8 (Stage 3) | Node deletion changes state indexing, so bit-identity of whole state labels is no longer available. The gate becomes the projected biological-state distribution and per-node trajectories, same seed. If the MaBoSS draw sequence turns out to differ, a pre-registered distributional tolerance with stated trajectory counts is used instead. **As run** (`docs/intervention_layer_stage3.md` §8, §14): the same-seed projected comparison was exact on every lineage and condition at three seeds, so the fallback was not used. |

The same-seed results hold for the pinned runtime (maboss 0.8.15). If the binary
changes, G5 must be re-established rather than assumed.

## 7. Non-goals of Stages 1 and 2

- No edit to any file under `models/`, to `config/protocols.yaml`,
  `config/perturbations.yaml` or `drug_target_catalog.tsv`, or to the CLI. Only
  Stage 2 touches the runner, as described in §5.1.
- No new targets, rules, rates, thresholds, engagement levels or
  pharmacokinetics.
- No removal of any `IN_*` node.
- No screen, and no committed prediction from a combination. Stage 4a makes
  combinations executable; running one is Stage 4b.
- No partial engagement or rate scaling.
- No interpretation of mifepristone beyond the model's existing abstraction
  ("Modeled as effective PGR antagonism"). The library records the executable
  behaviour and cites its evidence; it adds no pharmacology. The concordance
  analysis's measured mismatch for mifepristone must never be "fixed" by an
  engagement value tuned on held-out rows.
- Nothing touching `dropout_e2`, D2/D3 or other paused topology work.

## 8. Open questions (not decided here)

- **O1 `IN_cAMP`.** 8-Br-cAMP is a reagent in the same sense as MPA
  (`IN_PROGESTIN`). It is currently an "input" in the hormone cocktail. Whether
  the cocktail components belong to the protocol layer as environmental inputs, or
  to the library, is undecided.
- **O2 `IN_XAV939`.** It is read by no rule. Options are to keep it as a
  protocol-provenance node, to drop it in Stage 3 with its library row as the
  record, or to give it an effect if evidence ever licenses one. Any of these
  needs its own decision.
- **O3 State-dependent masks.** `IN_ER_STRESS_EXCESS` and `IN_HIGH_ECM_STIFFNESS`
  act only through `not ((A or B) and X_MECHANICAL_STRESS_RELAY)`, which applies
  only when the relay is on. A whole-node veto cannot express that, and a
  compound acting this way would need a target that names part of a rule. They
  stay as inputs.
- **O4 Graded engagement.** Still open after Stage 4a, which fixes engagement at
  1 throughout. The candidate is a trajectory mixture over **whole
  lineages** (a fraction f of independent units fully vetoed), which invents no
  rate. Mixing per phase and then carrying the state forward is not equivalent.
  Within-cell rate scaling would be a new kinetic assumption, which AGENTS.md
  forbids without evidence. Nothing executes engagement < 1 today:
  `perturbations/target_engagement.py` only validates a grid.
- **O5 Correlated engagement under polypharmacology.** With partial engagement on
  several targets, whether engagement is independent or correlated between
  targets within a unit is unconstrained. Post-hoc mixing needs 2^k lineage runs
  for k targets. This must be declared, not defaulted.
- **O6 Structural descriptor, not a screening bound.** v0.5.2 has 35 distinct
  composed Boolean functions and 8 alias classes over its free variables
  (`docs/v05_pause_decision_2026-09-30.md` §1.2). v0.6.0 has 29 and 7 for its
  *unperturbed* network (`docs/intervention_layer_stage3.md` §14). These counts
  describe the network's structure and its identifiability from the declared
  inputs. They are **not** a bound on how many screened interventions can be
  distinguished:
  - an intervention renders a different network, and a veto on one member of a
    baseline alias class can break that alias;
  - combinations are not bounded by the number of singleton baseline functions.

  A screening report may cite the counts as a structural description only. Any
  claim that interventions are indistinguishable needs a perturbational
  equivalence computed and proved over the rendered networks of the screened set,
  which has not been done. *Reworded 2026-10-03 after external review; it
  previously read "a large screen ranks at most that many distinguishable
  interventions", which does not follow from the counts.*
- **O8 The library cannot yet hold a new compound.** Every row must re-describe a
  veto the `.bnd` already contains (§5.2), so the library is closed to any
  compound the model does not already encode — which is the screening goal.
  Opening it means allowing rows with no legacy marker, which the Stage 2
  self-check would then not cover, so such a row needs its own licence: an
  evidence citation for the target and mode, and a gate that is not "reproduces
  an existing rule". Whether that is easier before or after Stage 3 is open:
  Stage 3 removes the markers anyway, so the two may be one unit.
  **Addressed 2026-10-02**, as a unit separate from Stage 3, by
  `docs/o8_markerless_interventions.md`, which also records why they were kept
  apart. The text above is kept as it was written.
- **O7 Mode vocabulary.** Antagonist, inverse agonist and loss of function are
  all `activity_veto` in this model. Whether the library should record the
  pharmacological action type separately from the executable mode, as ChEMBL
  action types do, is open. No such field is added now.

## 9. Precedents consulted

- DrugLogics (Flobak et al. 2015, PLoS Comput Biol 11:e1004426; drabme) keeps a
  drug-panel file (`drug  inhibits|activates  targets`) separate from the network.
  It is the closest precedent and uses full clamps only.
- PROFILE_v2 (Montagud et al. 2022, eLife 11:e72626) grades inhibition as a
  fraction of trajectories set through `istate`, with no compound library.
- Béal et al. 2021 (PLoS Comput Biol 17:e1007900) uses a node per drug and calls
  it a qualitative simplification.
- bioLQM separates fixing a node's value, restricting its range and removing a
  single interaction.

No precedent found combines a compound library with graded engagement and
polypharmacology in a logical model, so Stage 4 is new design work.
