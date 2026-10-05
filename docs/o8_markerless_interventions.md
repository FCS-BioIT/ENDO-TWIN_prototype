# O8 — markerless interventions, 2026-10-02

**Status: implemented on `feat/o8-markerless-interventions`; not merged.** This
unit closes open question O8 of `docs/intervention_layer_refactor_plan.md`. It
adds an execution route and its licence. It produces no result: no model
version, protocol, prediction or ranking. The committed library is unchanged and
holds no direct row. Stage 3 and Stage 4b are untouched.

## 1. Why Stages 1–4a did not meet the requirement

The requirement is that adding compound N+1 normally means adding evidence and
mapping data, not adding a MaBoSS node, editing a rule or changing engine code.

Stages 1 and 2 were reported as having met it. They had not, and §5.2 of the
plan records the correction, which this document leaves as written. What
blocked it was in the code:

- `load_intervention_library` refused a row with no `legacy_input_node`, and
  accepted one mapping basis, `executable_legacy_behaviour`;
- `legacy_route_overrides` derives everything from the legacy inputs. A new
  marker that is not a node fails as "not a constant input node". Reusing an
  unrelated input fails the exhaustive check as "not equivalent to the legacy
  rule";
- Stage 4a's `also_active` vetoed `overrides[target]`, which exists only for a
  target some legacy row already routes. A target outside that set raised
  `KeyError`.

So every row could only re-describe a veto the `.bnd` already contained. Stage
4a recombined those rows, and added nothing the model did not already encode.

## 2. Two mapping bases

| | `executable_legacy_behaviour` | `direct_supported_effect` |
|---|---|---|
| what the row claims | the model's existing `and not IN_X` veto, re-described | "under this model's abstraction, this intervention is a full `activity_veto` of this target" |
| `legacy_input_node` | required | must be empty |
| `legacy_perturbation_ids` | required for a veto row | must be empty |
| mode | `activity_veto` or `no_executable_effect` | `activity_veto` only |
| licence | Stage 2's exhaustive equivalence with the legacy rule, at every render | the checks in §3, when the library is loaded |
| how it is activated | the protocol's `IN_X` marker, or by name | by name only (`interventions=`) |
| examples | mifepristone, anti-SPP1, HAND2 loss, XAV939 | none committed; two synthetic fixtures |

The basis is an intervention-level field. One intervention cannot mix legacy and
direct rows.

**The schema is unchanged.** `config/intervention_library.tsv` keeps its 13
columns. The change is to the vocabulary of `mapping_basis`, plus the rules
above. No column was needed: a direct row's target, mode, evidence ids, sources,
abstraction and claim boundary already had columns. Splitting intervention
metadata from effect rows is not needed yet either: the loader already refuses
rows of one intervention that disagree on an intervention-level field, and the
basis was added to that set.

## 3. The licence of a direct row

All of these are checked in `engine._license_direct_effects`, and any failure
refuses the whole library, so a run cannot proceed on a partially licensed one:

1. **No marker.** `legacy_input_node` and `legacy_perturbation_ids` are empty.
   Otherwise the row would be a legacy row in all but name, and would escape the
   check that licenses those.
2. **One mode.** `activity_veto`. `no_executable_effect` is refused on a direct
   row, since it records a model's silence about a reagent the model already
   names.
3. **A target the primitive can mean.** The same `_target_logic` the legacy
   route uses: the node exists, has exactly one logic line, is not an input
   (`logic = <self>`, which also covers every v0.5.2 memory relay) and declares
   no rate.
4. **No unrouted marker in the target's rule.** If the rule reads a legacy input
   that no legacy row routes, the veto would not be over the rule that runs, so
   the row is refused.
5. **Not a phenotype and not a structural relay.** The target's
   `node_dictionary.tsv` row must exist, and its `model_role` must not be
   `phenotype` or `structural_uncertainty`. Vetoing a phenotype reads the
   endpoint off the intervention. A relay is a modelling device the dictionary
   itself flags as uncertain, not an entity a compound can act on.
6. **Evidence that resolves.** Every `evidence_ids` entry is an `evidence_id` in
   `context/evidence-register.tsv`. Every `abstraction_sources` entry names a
   file that exists. `model_abstraction` and `claim_boundary` are non-empty.

*Since O8b (`docs/o8b_direct_effect_governance.md`), check 5 reads its refused
roles from `config/direct_effect_target_policy.tsv`, and a seventh check requires
an approved effect adjudication. The paragraph below describes O8 as built.*

**What the licence does not establish:** that the evidence supports the claim.
That is a scientific judgement the row records and a reviewer makes. Register
status is not gated: every `LIT-*` entry is `candidate` today, so requiring
`verified` would close the route to all literature evidence. It is recorded in
§8 as open.

## 4. What the engine may and may not infer

The engine **may**:

- render the declared `(target, mode)` with the existing primitive;
- compose several interventions through the Stage 4a rule, the idempotent union
  of vetoes;
- refuse anything outside the licence.

The engine **may not**:

- infer a target from a compound's name, class or label;
- create a node, an input, a marker or a protocol entry;
- edit a canonical model file;
- route a direct row through the legacy marker machinery, or let a legacy row
  skip the Stage 2 check by calling itself direct.

## 5. Execution path

For `run_protocol(..., interventions=("compound_x",))` on a library-covered
model:

1. `run_protocol` calls `run_cmaboss_condition` once per step with the same
   names.
2. `_intervention_overrides` loads the library, so the direct licence (§3) is
   checked here. It collects the **legacy** inputs only and reads their values
   from the merged cfg and the continuation, exactly as before. When a version
   has no legacy row, named interventions still reach step 3.
3. `legacy_route_overrides` runs the Stage 2 disconnect and its exhaustive
   check over the legacy rows, unchanged. The named interventions then pass
   through `_composed_effects`, the one point where both bases converge. That
   step refuses unknown, duplicated, wrong-version or unsupported-mode names. It
   also refuses a mode conflict, against the other named effects *and* against
   the targets a marker vetoes in this phase. Each target is then rendered
   through `_render_mode`: a target a legacy row routes is vetoed over its
   disconnected rule, and any other target over its own rule. Either way it is
   vetoed once.
4. The runner renders the text through `render_network_with_logic_overrides`,
   loads it into MaBoSS, deletes it afterwards, and records:
   - `named_interventions`;
   - `named_intervention_effects`: each row's basis, target, mode, evidence and
     sources;
   - `evidence_register`: path and sha256, when a direct row was named;
   - the library's sha256, the logic overrides, and the sha256 of the executed
     text.

   Those reconstruct the executed network exactly.

`intervention_logic_overrides`, the documented composition against the model's
own rules, shares `_composed_effects` and `_render_mode`, so the two paths
cannot drift on which targets a set vetoes.

## 6. Why O8 precedes Stage 3

The two units carry independent risks, and doing them together would confound
them:

- **O8** shows that a new intervention can be represented without a new node. It
  is additive. It leaves every legacy rendering, and so every existing result,
  bit-identical. That is testable because the markers still exist.
- **Stage 3** shows that the historical marker nodes can be removed without
  changing biology. It changes the state space and needs G8.

O8 first also means Stage 3 can rest on a route that already runs: after
deletion, the legacy rows need the markerless path to execute at all.
Measuring O8 surfaced what Stage 3 must then add: a way for the **protocol** to
say when a markerless intervention is active (§8).

## 7. Gate G10 and regressions

The tests are `tests/unit/test_markerless_interventions.py` (static) and
`tests/integration/test_markerless_intervention_runtime.py` (MaBoSS). The
runtime tests build a sandbox repository from copies of `models/`, `config/` and
the evidence register, with the synthetic rows from `tests/fixtures/o8_markerless/`
appended. They then run the production `run_protocol` against it, unpatched.

| requirement | test |
|---|---|
| a markerless compound executes through the production path | `test_a_markerless_compound_executes_and_records_its_licence` |
| no compound node exists; the executed network has the canonical node list | same test, and the N+1 test |
| no canonical model file is modified | the record's `source_network` sha256 is the canonical network's; the N+1 test compares `models/` byte for byte |
| exactly one veto on the target | same test; `test_naming_x_vetoes_exactly_its_target_once` |
| the executed network is reconstructible from the record | same test |
| the record names the intervention, its basis and its evidence | same test; `test_the_legacy_record_names_its_basis_too` |
| removing the row makes the intervention unavailable | `test_removing_the_row_makes_it_unavailable` |
| **N+1 is a data operation** | `test_adding_compound_n_plus_one_is_a_data_append`: Y is refused before its rows exist and runs after. Adding it changes exactly the library and the register, each by appending. `models/` stays byte-identical to the repository's and `src/` is unchanged. X's run is bit-identical before and after Y is added |
| naming one is not a no-op | `test_naming_it_is_not_a_no_op` |
| the sandbox itself distorts nothing | `test_the_sandbox_runs_the_repository_bit_for_bit`, two seeds |
| composition with legacy and direct compounds | `test_it_composes_with_legacy_and_direct_compounds`; static parity over every subset |
| refusals | `DirectRowLicenceTest`: a marker, a perturbation id, a wrong mode, a missing, input, rated, phenotype or relay target, unrouted marker reads, unresolved evidence, missing sources, an unknown model, mixed bases, a duplicate target |
| future modes cannot collapse silently | `FutureModeConflictTest`: a conflict with an active marker, between named members, and a supported mode with no renderer are each refused |
| a refused later step leaves no merged cfg behind | `ProtocolCleanupTest` |

The legacy gates G1–G7 and G9 run unchanged against the committed library. The
Stage 1 fixture now selects legacy-basis rows, so a real direct row added later
leaves them asserting what they asserted.

## 8. Non-goals and open questions

**Not in this unit:** activation or any second mode, partial engagement, rate
scaling, dose, pharmacokinetics, new nodes or rules, target inference, a bulk
import, a real compound row, predictions or rankings, Stage 3, Stage 4b.

**Open:**

- **O8a Protocol timing.** A direct intervention is active only by name, for
  every step of a `run_protocol` call, or per condition through
  `run_cmaboss_condition`. `config/protocols.yaml` cannot say "active from this
  phase", because its only vocabulary for that is an `IN_*` marker. Stage 3
  needs this anyway; this unit does not add it.
  **Addressed 2026-10-02** by `docs/protocol_intervention_timing.md`: a step-level
  `interventions` field, proven equivalent to marker timing (gate G11).
- **O8b Evidence strength.** Whether a production direct row must cite
  `verified` evidence, and who adjudicates support, is undecided. Today any
  registered id resolves.
  **Addressed 2026-10-03** by `docs/o8b_direct_effect_governance.md`: not by
  register status, which answers a different question, but by an approved
  effect-level adjudication in `config/direct_effect_adjudications.tsv`, keyed by
  intervention, model version, target and mode and bound to the row (gate G12).
- **O8c Refused roles.** `phenotype` and `structural_uncertainty` are refused.
  Whether composite states (`state`, `latent_state`, `interface_route`) should
  be too is open.
  **Addressed 2026-10-03** by the same document: the refused roles now live in
  `config/direct_effect_target_policy.tsv`, which refuses every derived readout,
  state, route and relay, refuses some nodes individually, and refuses any role
  it does not list.
- **O8d Mixed interventions.** A compound with one legacy-backed effect and one
  direct effect cannot be written as one intervention. It could be two.
- **Follow-up, not O8.** Successful runs hand their merged-cfg directory back,
  and no production caller removes it. A screen would accumulate one per phase
  run. This unit fixes only the failure path in `run_protocol`.
  O8a gives the holder an explicit `release()` and a `with` form, and leaves
  migrating existing callers as a follow-up (`docs/protocol_intervention_timing.md`
  §9).
