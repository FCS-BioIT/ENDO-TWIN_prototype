# O8a — protocol-native intervention timing, 2026-10-02

**Status: implemented on `feat/protocol-intervention-timing`; not merged.** This
unit closes open question O8a of `docs/o8_markerless_interventions.md`. It adds a
capability and its proof, and produces no result: no model version, no
prediction, no ranking. **No committed protocol uses the new field**, every `IN_*`
node is kept, and Stage 3 and Stage 4b are untouched.

## 1. Why O8 left timing unresolved

O8 made an intervention representable as library data, with no compound node.
It did not give the protocol a way to say *when* that intervention is active:

- `run_protocol(..., interventions=(...))` applied the names to **every step** of
  the call. Running them in one phase and not the next meant calling the runner
  per phase with different arguments, which nothing persisted.
- `config/protocols.yaml` could say "active from this phase" only through an
  `IN_*` marker in `input_states`. That is how mifepristone, anti-SPP1, HAND2 loss
  and the anti-SPP1 washout are timed today.

So the markers still carried timing, and Stage 3 could not delete them: deleting
`IN_ANTI_SPP1` would also delete the only record that anti-SPP1 is on in
`hormone_treated_anti_spp1` and off again in `washout`.

## 2. Where timing belongs

| layer | owns |
|---|---|
| biological model (`.bnd`, node dictionary) | states and rules |
| intervention library (`config/intervention_library.tsv`) | what intervention X does: target, mode, evidence |
| **protocol** (`config/protocols.yaml`) | **when X is active** |
| perturbation engine | how the declared effect is rendered |

Timing is a property of an experiment, not of a compound. The same reagent is
given for 24 h after hormone treatment in one design and throughout it in
another, and the library row must not change between them. Putting a schedule in
the library would make one row per schedule; putting it in the engine would make
the engine infer an experiment. The protocol already owns the phase structure
(steps, durations, continuation), so it is the layer that can say "on here, off
there" without restating what the intervention does.

## 3. Representation

One optional field per protocol step:

```json
{
  "step_id": "anti_spp1_challenge",
  "relative_order": 1,
  "relative_duration": 1.0,
  "duration_note": "...",
  "input_states": {"IN_ANTI_SPP1": false, "...": false},
  "interventions": ["anti_spp1"]
}
```

- `ProtocolStep.interventions: tuple[str, ...]`, default `()`.
- **Absent** and **`[]`** both mean the step names no intervention. A file that
  never uses the field resolves to exactly the definitions it resolved to before.
- **Order is not semantic.** Composition is the Stage 4a idempotent union, so the
  parser stores the names sorted. Two spellings of one schedule are one
  `ProtocolDefinition`.
- **Refused at load** (`protocols.conditions.step_interventions`): a value that is
  not a list of non-empty strings, a duplicate, an id the library does not have,
  an intervention defined for another model version, and a legacy-basis name
  whose marker the same step sets `ON` (§5). The library is read only when some
  step of the selected model version names an intervention.
- A **markerless** (`direct_supported_effect`) intervention is legal, and is the
  case this exists for.
- The field says only *when*. Target, mode and evidence come from the library
  row, unchanged; nothing in a protocol can redefine them.

`protocol_sequence` lists a step's `interventions` only when it declares some, so
every existing sequence record (the smoke manifest's protocol sequence, the
dynamics metadata) is byte-identical. The per-step `executed_network` record does
change shape (§7): every step now carries `legacy_input_values` and, under
`run_protocol`, `intervention_timing`. No committed artifact embeds that record;
the structural-smoke manifest under `output/` does, and gains those fields.

## 4. Execution

`run_protocol` resolves the active set **per step**:

```text
active(step) = step.interventions  +  caller interventions
```

Each step's set is passed to `run_cmaboss_condition`, which renders it through
the merged Stage 4a / O8 engine exactly as before (`legacy_route_overrides(...,
also_active=active)`). Nothing in the engine changed.

**Caller-supplied names: union, not override.** Every production caller of
`run_protocol` passes no names; only tests and the documented combination path
do. An override would let a caller silently remove a step's declared
intervention while still running under that protocol's id, which is the
mislabelled-run outcome this layer exists to refuse. The union keeps both
meanings explicit:

- a caller name applies to **every** step of that call, on top of each step's own;
- a name both declared by a step and supplied by the caller is **refused before
  any step runs**, as is a caller name given twice. Neither is absorbed.

The terminal re-read in `calibration/observation_map.py`, which rebuilds a step
outside `run_protocol`, now passes that step's `interventions`. The other
executor that bypasses `run_protocol`, `scrna/klf12_conditioning.py`, is pinned
to v0.4.0, for which the library has no row, so the parser refuses any named
step it could see.

## 5. Interaction with `input_states` and legacy markers

`input_states` keeps its meaning: deterministic values of input nodes,
biological ones (`IN_E2`, `IN_EMBRYO_PRESENT`, …) and, until Stage 3, the legacy
markers. Under the engine route a marker is read by no rule. It only switches its
intervention's veto on, which is what makes it a timing device.

An intervention may be timed **one way per step, not both**:

| marker in this step | named in this step | outcome |
|---|---|---|
| OFF | no | not active |
| ON | no | active through the marker (legacy timing) |
| OFF | yes | active through the name (protocol timing) |
| ON | yes | **refused** |

The last case is refused twice over. The parser refuses it when the marker is
`ON` in the step's `input_states`. When it is `ON` through the condition cfg or a
continuation's forced nodes instead, only the runtime knows, and the step
refuses it then, through the existing check in `legacy_route_overrides`
("naming it again would apply it twice"). A test exercises each layer.

One corner is deliberately not refused at run time: `xav939`, whose row is
`no_executable_effect`, named while `IN_XAV939` is ON through the cfg. Nothing is
applied, so nothing is applied twice, and Stage 4a already accepts this as an
inert combination member (`test_an_inert_member_leaves_a_combination_unchanged`).
A runtime refusal was tried in this unit and reverted, because it changed that
reviewed behaviour. The parser still refuses it when the step's own
`input_states` sets the marker.

## 6. Onset, persistence, washout

These are statements about consecutive steps (or consecutive protocols of a
lineage, chained by `continuation_from`; every committed protocol has one step):

- **onset**: the first step that names X;
- **persistence**: every following step that names X again;
- **washout / removal**: the first following step that does not.

Removal ends the veto and nothing else: the next step renders the target's rule
as written, and the state carried over by the continuation is whatever the
vetoed phase left. That is exactly what the legacy `washout` protocol does with
`IN_ANTI_SPP1 = FALSE`, and the gate below shows the two are identical. There is
no implicit carry-over: a step that wants X must name it.

## 7. Provenance

Every executed step's `executed_network` record now carries, in addition to what
O8 recorded (`named_interventions`, each row's basis, target, mode, evidence and
sources, the library and register sha256, the logic overrides and the executed
network's sha256):

- `legacy_input_values`: the value each routed marker started the step at;
- `intervention_timing`: `protocol_id`, `step_id`, `step_index`, and which of the
  active names the step declared (`protocol_declared`) and which the caller
  supplied (`caller_supplied`).

So two runs whose timing differs have different records, including the two
encodings of one schedule, whose executed networks are identical: one records the
marker `ON` and no name, the other the marker `OFF` and the name.

## 8. Gate G11 and its tests

`tests/integration/test_protocol_intervention_timing_runtime.py` runs the
production `run_protocol` / `protocol_continuation`, unpatched, against a sandbox
built by `tests/fixtures/protocol_timing/sandbox.py`. The superset protocols are
cloned in code, and a v0.5.2 row in the sandbox file would switch that clone off,
so the sandbox first writes every canonical v0.5.2 protocol out as an explicit
row and checks that each parses back to the identical definition, and that a
canonical lineage runs bit for bit as in the repository.

| requirement | test |
|---|---|
| mifepristone, anti-SPP1, HAND2 loss and the washout, re-expressed with the marker OFF and the name in the marker's phases, reproduce the canonical lineage phase by phase, 3 seeds: same executed network (text sha256 and overrides), same non-marker trajectories, last-node marginals and last-state distribution, same continuation (memory nodes, distribution, policy, cutoff, forced nodes other than the marker) | `test_each_schedule_is_reproduced_phase_by_phase` |
| the only differences are the marker's istate line, its recorded value and the declared name | `test_the_two_encodings_differ_only_in_how_the_marker_is_set` |
| same durations, cfgs and continuation policies; the sequence records the names | `test_phase_boundaries_and_continuations_are_the_canonical_ones` |
| washout removes the veto | `test_washout_removes_the_veto` |
| the same, timed inside one three-step protocol | `test_named_steps_reproduce_marker_steps` |
| **negative controls**: mifepristone in the wrong phase, the washout omitted (as a phase and inside one protocol) each fail the comparison, while the correctly timed phases still pass it | `NegativeControlTest` |
| a markerless compound goes OFF → ON → OFF across steps with no compound node, renders the canonical network when off, and differs from keeping it on | `test_a_markerless_intervention_switches_off_on_off` |
| combinations compose per step; declaration order changes nothing | `test_combinations_compose_per_step_and_order_is_not_semantic` |
| a marker ON through the cfg plus the name is refused at run time | `test_a_marker_on_through_the_cfg_and_a_name_is_refused` |
| caller names are a union, applied to every step; overlap and repetition are refused before any step | `CallerCompositionTest` |
| each step records its own active set; different timing gives different records | `TimingProvenanceTest` |
| `observation_map`'s terminal re-read, outside `run_protocol`, runs the step's names | `ObservationMapReReadTest` |

`tests/unit/test_protocol_intervention_timing.py` holds the static refusals, the
check that no committed protocol declares the field and that every model
version resolves with no named timing, and the merged-cfg lifecycle tests.

Two mutations of `run_protocol` were run against G11 before it was committed:
ignoring the step field (49 failures) and applying the union of all steps' names
to every step (13 failures).

## 9. Merged-cfg ownership

`run_cmaboss_condition` writes each step's merged cfg into a fresh temporary
directory and returns its path in `ConditionRunResult.merged_cfg`. On success
nothing removes it. Every production caller was inspected: only
`run_structural_smoke` reads it, and it copies the text into its run directory.
None of the others reads it or removes it.

**Decision: the holder of the result owns the directory, and releases it
explicitly.** `ConditionRunResult.release()` and `ProtocolRunResult.release()`
remove the directories and are idempotent. `ProtocolRunResult` is also a context
manager (`with run_protocol(...) as run:`) that releases on exit, including on an
error. `merged_cfg` stays valid until then, so callers that inspect it are not
broken. The failure paths O8 fixed are unchanged.

Existing production callers are **not** migrated here: changing them touches
closed or digest-pinned analyses (concordance, endpoint replicates, the C3a and
U5b readouts) for a cleanup with no effect on results. **Follow-up:** a Stage 4b
screen must hold its runs in `with` blocks (or call `release()`), and each
existing caller should adopt `release()` the next time it is edited for its own
reasons. The G11 tests already release every run they make.

## 10. Migration path toward Stage 3

This unit proves that step-level names can replace marker timing exactly. It does
not migrate anything. Stage 3 would then, as its own reviewed unit:

1. re-express the canonical schedules with `interventions`, as G11 already does in
   a sandbox. The v0.5.2 protocols are generated by the clone layer in
   `protocols.conditions` (and the HAND2 arms by `_hand2_loss_protocols`, which
   sets `IN_HAND2_LOSS`), so the new version needs either explicit rows or a clone
   rule that emits names instead of markers;
2. decide what licenses the historical interventions once their markers are
   gone. A `executable_legacy_behaviour` row requires a `legacy_input_node`, so on
   a markerless version those rows need a basis whose licence is equivalence with
   v0.5.2 (G8), or `direct_supported_effect` rows;
3. delete the nodes and their `and not IN_X` conjuncts in a new, generated model
   version, and pass G8;
4. teach the consumers that read `input_states` as the record of an intervention
   to read `interventions` too: `simulation/timeline.py` (dynamics figures),
   `reporting/c3a_kinetic_readout.py`, and the smoke's forced-input summary.

v0.5.2 and every closed phase keep their markers and stay replayable.

**Done 2026-10-03** by Stage 3 (`docs/intervention_layer_stage3.md`):

- Item 1 uses explicit, generated rows in a new file,
  `config/protocols_markerless.yaml`, rather than a clone rule (O8a-1).
- Item 2 uses a third basis, `migrated_legacy_behaviour` (O8a-3).
- Item 4 records each step's interventions in the timeline, the dynamics
  metadata and the smoke (O8a-4).

The text above is kept as written.

## 11. Non-goals and open questions

**Not in this unit:** removing any `IN_*` node; editing any canonical rule,
protocol or library row; real compounds; new modes, partial engagement, dose or
pharmacokinetics; a screen; Stage 3; Stage 4b; `dropout_e2`.

**Open:**

- **O8a-1 Clone-layer interaction.** A cloned superset row copies its parent's
  steps, `interventions` included, but the parent's own version is validated
  against the library too. Declaring names on an archived parent row would
  therefore fail for the archived version. Stage 3 should give the new version
  its own rows rather than rely on cloning.
- **O8a-2 Sub-step timing.** The unit of timing is a step. Onset within a step,
  or a ramp, is not representable and would be a kinetic assumption.
- **O8a-3 Library basis without markers** (§10, item 2).
- **O8a-4 Timeline display.** `TimelinePhase` reports `input_states`; a figure of a
  name-timed protocol would not show the intervention. No committed figure is
  affected.
