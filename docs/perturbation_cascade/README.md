# Perturbation-response cascades

**Question.** Given an established model state and a precisely declared
perturbation, which model components respond, in which direction, how
consistently, and in what relative order?

**What the answer is.** A conditional model-internal prediction of
`adoc-literature-superset-v0.6.0` (or another registered model) under stated
rules, start state and perturbation semantics. MaBoSS time here is the
dimensionless continuous time of the asynchronous stochastic dynamics, with
every transition rate equal to 1; it is not calibrated to hours or days and is
not a count of Boolean updates. Nothing here is experimentally validated, nothing is a causal sequence in
tissue, and nothing licenses a screen: Stage 4b owner decision 6 excludes
transient differences from screenability, and this tool does not change that.

```
pixi run perturb-cascade --spec context/perturbations/progestin_withdrawal.yaml --n 2000
pixi run perturb-cascade --start hormone_treated_maternal --set IN_PROGESTIN=0 --n 2000
pixi run perturb-cascade --start hormone_treated_maternal --intervention mifepristone --n 2000
```

Output: `output/perturbations/<run-id>/` with `events.tsv`, `node_summary.tsv`,
`control_comparison.tsv`, `pairwise_precedence.tsv`, `cascade.{png,svg,pdf}` and
`metadata.json`. Code: `src/dt_adoc/cascade/` and `src/dt_adoc/perturbations/spec.py`.

## 1. What can be perturbed

A spec (`perturbations/*.yaml`, format in `src/dt_adoc/perturbations/spec.py`)
only *selects* mechanisms the repository already executes, and each declared
effect carries a machine-readable `provenance_class` in `metadata.json`:

| spec key | `provenance_class` | executed by |
|---|---|---|
| `input_changes` | `protocol_input_change` | the input values a protocol step sets (`IN_*` self-rule nodes only) |
| `interventions` | `registered_intervention` | `config/intervention_library.tsv` through the engine, with the row's `mapping_basis`, evidence ids and claim boundary recorded |
| `rule_variants` | `registered_rule_variant` | the model's registered rule-variant families (v0.6.0 has none) |

An input change is accepted only for an input the start protocol's last step
declares, and only if it changes that declared value, so every recorded change
has a known `from`. Refused by name: `veto` / `hypothetical_vetoes` / `effects` (reagent-free node
knockouts), `force_on` (the engine has no ON rendering) and `rule_replace` (free
rule text). Latched relays and `E_KLF12_HIGH` are self-rule nodes but latent
memory states, not inputs, and cannot be set.

**Boundary needing an owner decision.** A hypothetical target effect such as
"veto `E_GP130_STAT3`" names a node and no reagent. That is exactly the
*model-only target ablation* that `docs/stage4b_direct_admission.md` (§2, owner
decision 1) reserves as a separate future unit, so implementing it here would
open that unit. It is not implemented. If approved, the minimal design is a
fourth class `model_only_target_ablation`, executed by the engine's own
`activity_veto_logic` and target refusals, recorded outside the library and the
ledger, with `compound_claim_permitted: false` and no reagent name allowed in
the spec or its outputs.

Multi-target compounds already work through the library: a library row set with
several targets is one `interventions` entry, and several entries compose as the
engine composes them (Stage 4a). Composition is an executable statement about
the model, never evidence that compounds interact.

## 2. Starting state, perturbation boundary and the matched control

1. The start protocol's declared lineage (`protocol_lineage`) is run with
   `run_protocol`, each phase continuing from its parent by its own registered
   continuation, every phase to horizon 25 (`--init-horizon`), seed 1, 5,000
   trajectories.
2. The terminal joint state distribution is projected onto **all non-input nodes**
   (`memory_node_policy = all_non_inputs`, no probability cutoff). This is a
   recorded departure from the registered `extended_maternal_joint` policy that
   the repository's post-HT protocols use; §4.2 shows why, and owner decision
   OD-1 (§7) adopts it for this analysis only.
3. Each trajectory's starting state is drawn **i.i.d. here** from that
   distribution (NumPy, `SeedSequence([master_seed, 1])`) and the run is given
   that one state with probability 1.
4. Two arms run from the same drawn states with the same per-trajectory seeds:
   the **perturbed arm** (start-protocol inputs and interventions plus the spec's
   effects) and the **matched control** (start-protocol inputs and interventions
   only). Everything active at the end of the start protocol stays active in
   both arms; a start that already carries an intervention keeps it.
5. The perturbation acts at t = 0 of the new phase and is held to the horizon
   (25 by default, `--horizon`).

`--memory-policy` accepts only `all_non_inputs`, `relay_only` or a policy the
model registers; anything else is refused before any simulation. A bundle is
written into a staging directory beside its target and swapped in only when
complete, so a failed run, or a failed `--overwrite`, never leaves new tables
next to an old bundle's metadata or figures. `--overwrite` deletes nothing: the
replaced bundle is moved whole into `.trash/` inside the output root (empty it
yourself). Cascade runs commit one at a time under a lock on the output root;
anything else writing into a bundle directory is preserved, not coordinated.

A shared seed does **not** pair the event streams: a different network consumes
the random stream differently (Stage A: a node independent of the perturbation
switched at the same time in both arms in 0 of 100 seeds). Pair counts in
`control_comparison.tsv` are descriptive; differences are paired-bootstrap
estimates; nothing is an individual counterfactual.

The control is also the stationarity check. `metadata.json → diagnostics →
control_stationary` is true only if, in **every** control trajectory and for
**every** tracked node:

- no switch was observed (`n_switches_min = 0`);
- the node's executed rule could be evaluated on the final state and agrees with
  the node's value there (`rule_disagrees_at_horizon` is False, never True or
  unknown);
- the final state is known (the last tick window is whole).

The start is then a fixed point of the control's rules at the horizon, and every
perturbed-arm switch is perturbation-associated under the model. Any switch, any
disagreeing rule and any unevaluable rule or final state makes it false, and the
CLI warns.

## 3. Events, and the three quantities kept apart

pyMaBoSS 0.8.15 with cmaboss 1.0.0b32 exposes no event stream (`display_traj` is ignored,
`get_observed_graph` returns `<nil>`). Each trajectory is one `sample_count = 1`
run, and events are read off its tick occupancies (`src/dt_adoc/cascade/events.py`):
a whole window holds no switch, a fractional one at least one; a single switch
in a window is timed exactly as `t_j + tick · occupancy(entered state)`;
`n_switches_min` is the minimum count consistent with the occupancies (a lower
bound); a window shown to hold two or more switches marks the time unresolved.
Because a window can also hide an out-and-back pair that leaves no trace, the
first switch is only known to lie in `[first_switch_lower, first_switch_upper]`
(the window start and the reconstructed time). `pairwise_precedence.tsv` counts
A before B only when A's interval ends before B's begins, which holds whenever
their first switches fall in different windows and never within one; such
pairs are `n_order_unresolved` and `p_a_first` is over the identifiable ones
(0.20 % of comparisons in the Stage C withdrawal run, at most 19 for one pair).
Positions in the figure use the reconstructed times and are for display.

`events.tsv` has one row per arm, trajectory and **tracked** node: every node
the run reports, which is every non-internal node (all non-input nodes, plus any
input carried as memory). `metadata.json → tracked_nodes` lists them and those
the start does not carry; `starting_state → memory_nodes` lists the carried
ones. Under the default policy the two coincide in v0.6.0 (45 non-input nodes;
the 11 `IN_*` inputs are declared by the start step, internal, and recorded per
arm in `metadata.json → arms`). In v0.5.1 the carried set also includes
`IN_HAND2_LOSS`, an input the step does not declare, carried at OFF. Under
another policy a tracked node the start does not carry begins from the
condition cfg; its t = 0 state is read from the first tick window, and the run
is refused when that window is fractional.

Per node and trajectory, three things are reported and never collapsed:

- **first switch** — `first_switch_time`, the first departure from the t = 0 state;
- **net response** — `final != initial` at the horizon, over trajectories whose
  final state is known (`n_final_known`; an unknown final is missing, never
  "unchanged", and the control comparison uses `n_pairs_final_known` pairs),
  with `transient_return` and `net_change_n_switches_min_gt_1` separated (category
  names follow `n_switches_min`, a lower bound: see Stage C below);
- **perturbation-associated response** — perturbed vs control
  (`control_comparison.tsv`).

A node that does not switch is split into "rule agrees at the horizon" (at a
fixed point) and "rule disagrees" (still at risk: censored, not a non-response).
Nodes already in the target state at t = 0 are visible through `p_initial_on`
and the `p_switch_given_initial_on/off` columns. `node_summary.tsv` has a row
for every direction in which a node switched at least once, so
`direction = none` means exactly that it never switched; `shown_in_figure`
marks the rows the figure draws (a direction holding at least 5 % of
trajectories, or every switch). The figure's footer lists the nodes with
`p_switch = 0` as never switching, and separately any node that switched but
has no drawn row. A node whose t = 0 state is unknown
(possible only with a start policy that does not carry it, when its first tick
window is fractional) is refused with an error rather than summarised: it would
otherwise fall into neither direction and look like a non-switcher.

## 4. Stage A: what was checked before building on it

Scripts and raw output: `stage_a/`. Lineage:
`python -B docs/perturbation_cascade/stage_a/pilot.py` (about 15 minutes, fixed
seeds) writes `output/perturbations/stage_a_pilot.pkl`, and
`python -B docs/perturbation_cascade/stage_a/analyze_pilot.py` prints the text
committed verbatim in `stage_a/pilot_analysis_output.md` (re-run 2026-10-08:
byte-identical). The backend probes `stage_a/backend_*.py` take any scratch
directory as their argument (they write their embedded test network there) and
print the §4.1 and §4.3 numbers.

### 4.1 Event reconstruction (implementation gate)

- **Tick invariance.** For the same seed the event stream does not depend on
  the tick: a single-switch time reconstructed at ticks 1.0, 0.1, 0.01 agrees
  with tick 0.001 to ≤ 1.1e-16 (200 seeds; `KS` vs Exp(1) p = 0.23). This is what
  makes a fine tick a valid reference.
- **Hidden switches.** On a rate-1 toggle over T = 5 (200 seeds), the lower
  bound never exceeds the tick-1e-4 count and equals it in 74 % of trajectories
  at tick 0.5, 99.5 % at 0.1 and 100 % at 0.01 and 0.001. A float-dust snap of
  1e-9 is required (1e-12 left dust windows counted as switches), and the last
  window's state must not be assumed: `get_last_probtraj` returns the last
  window's occupancy, not the final state.
- **On v0.6.0** (progestin withdrawal, 200 trajectories re-run with identical
  states and seeds): ticks 0.05 and 0.001 and horizon 40 reproduce every
  first-switch time to ≤ 3.6e-15, every switch count and every presence; no
  window was unresolved. `tests/integration/test_cascade_event_reconstruction_runtime.py`
  keeps the synthetic checks as a regression gate.

### 4.2 Starting state

| start construction (withdrawal arm and control, 1,000 pairs each) | control nodes switching | note |
|---|---|---|
| all non-inputs carried, lineage horizon 25 | **0** | start is a fixed point; no rule disagrees at the horizon |
| registered `extended_maternal_joint`, horizon 25 | 8 nodes, up to 100 % of trajectories | the 10 non-memory nodes (`E_PAEP`, `S_PRL`, `S_IGFBP1`, the four `OUT_*`, the three `X_*_ROUTE`) restart from their cfg state 0 and relax back |
| all non-inputs, lineage horizon 50 | 0 | start distribution identical to horizon 25 (total variation 0.0000) |
| all non-inputs, declared phase durations | 38 nodes | total variation 0.9993 from horizon 25: not stationary |

The registered policy is harmless for the converged endpoints it was designed
for, but for a cascade it injects a re-initialisation transient that the
control shows directly (and that shifts, for example, the median first switch of
`OUT_EPITHELIAL_RECEPTIVE` from 4.02 to 0.59). Carrying every non-input node at
horizon 25 is the default; the control's stationarity is checked on every run.

The latched interface relays are drawn from their priors and never switch. They
change *which* nodes respond (`X_ANTIADHESIVE_ROUTE` switches only where its relay
is ON, ≈ 19 %) and shift other nodes' medians by up to 0.36 absolute time,
0.088 rank position and 0.057 normalised-time position — about a third of the
spread of the medians in every statistic.

### 4.3 Seeds

The installed generator is MaBoSS's default `Rand48RandomGenerator` (Mersenne
Twister is compiled in as `use_mtrandgen`; the repository does not set it).
Over 1,500 seeds, consecutive seeds give a lag-1 correlation of −0.088 between
successive first-event times (≈ 3.4 SE), on top of the stratified initial draws
the estimator note already records; `SeedSequence`-spread seeds give −0.021
(≈ 0.8 SE). Within one trajectory, two competing nodes' times are uncorrelated
(−0.007). The tool keeps the repository's generator, uses spread seeds checked to
be distinct, records each, and draws starting states itself. Distinct seeds are
not a proof of independence, and the record says so.

### 4.4 Which position statistic

Four candidates were compared on the withdrawal arm (two independent blocks of
1,000; same blocks for all statistics):

| | block-to-block max \|Δ median\| / spread of medians | drop last node: max shift | drop first two: max shift | relay strata: max shift / spread |
|---|---|---|---|---|
| absolute time | 0.153 / 1.094 (0.14) | 0 by definition | 0 | 0.383 / 1.094 (0.35) |
| normalised rank | 0.067 / 0.248 (0.27) | 0.025 | 0.053 | 0.088 / 0.248 (0.35) |
| normalised time | 0.046 / 0.160 (0.29) | 0.028 | 0.066 | 0.057 / 0.160 (0.36) |

No position statistic is robust where it matters: **92 % of rows adjacent in
median order have P(upper first) between 0.4 and 0.6**, so the vertical order
inside a wave is noise in all three. Pairwise precedence is the stable object
(block-to-block median |Δ| 0.012, max 0.099), and over all 666 pairs 28 % are
unresolved and 11 % strictly ordered.

(These Stage A precedence numbers used point times; the tool now leaves
same-window pairs unresolved, §3, which changes 0.2 % of comparisons.)

Decision: **positions are for display; order claims come from
`pairwise_precedence.tsv`.** The figure defaults to normalised time, which is
as robust as rank in relative terms, continuous (rank medians tie: five nodes
shared 0.441 in the historical figure) and independent of how many nodes a wave
contains; `--position normalized_rank` reproduces the historical axis and
`--position absolute_time` keeps the scale. Adjacent rows whose order is
unresolved (|P − 0.5| < 0.1 with ≥ 50 trajectories where both switch) are joined
by a grey bracket in the gutter; this is a stated precedence criterion, not a
wave boundary.

### 4.5 Is 2,000 enough?

At 1,000 trajectories the bootstrap 95 % half-width of a node's median
normalised-time position is 0.020 at the median node (max 0.047), and of its
97.5 % quantile 0.036 (max 0.095); at 2,000 these shrink by about √2. That is
adequate for the medians, for the switching fractions, and for precedence
probabilities (SE ≤ 0.011 at 2,000 when both nodes always switch). It is not
enough to resolve within-wave order, which more trajectories would not fix
because those orders are near 0.5 by construction (equal rates, exchangeable
nodes). The smallest contributing group is `X_ANTIADHESIVE_ROUTE` (≈ 400 of 2,000),
whose tails are the least precise.

## 5. Progestin withdrawal vs mifepristone

`IN_PROGESTIN` is read only by `E_PGR` and `S_PGR` (`logic = IN_PROGESTIN`).
Mifepristone vetoes both (`(IN_PROGESTIN) and not 1`), so under the cocktail
inputs the effective PGR rules are identically FALSE in both manipulations,
while the networks differ (different `network_sha256`; the input node stays ON
under mifepristone). With identical starting states and seeds every tracked
non-input node's events were identical in every trajectory (Stage A, 1,000 pairs, both
start policies; Stage C, §6). In this model the two are indistinguishable at
every node and every time, as the historical v0.5.1 run found for the endpoint.
Any experimental difference between withdrawal and antagonism would be evidence
the topology lacks.

## 6. Stage C: the updated figure against the historical one

Lineage: `stage_c/run_stage_c.sh` regenerates the four bundles (seeds, models
and specs in the script; about 6 minutes) under the gitignored
`output/perturbations/`. Their tables are byte-deterministic, and
`stage_c/bundle_manifest.json` records each one's SHA-256.
`python -B docs/perturbation_cascade/stage_c/compare_historical.py --regenerate`
runs the script first when the bundles are missing or differ, so the comparison
runs from the committed state alone; it then refuses to continue unless every
bundle table and the archived historical files match their recorded hashes, and
writes `historical_comparison.tsv`, `historical_comparison_summary.json`
and the figure `output/perturbations/stage_c/historical_comparison.png` (whose
hash it records in the summary JSON).

No figure is tracked in the repository; each is regenerated from committed code
and data, and each regeneration has been checked byte for byte against a hash
recorded in a committed text file (`tests/unit/test_perturbation_cascade_docs.py`
checks that no PNG is tracked and that every hash is recorded):

| figure | regenerated by | recorded SHA-256 |
|---|---|---|
| `output/perturbations/progestin_withdrawal__v060__n2000__seedA/cascade.png` (the updated cascade) | `stage_c/run_stage_c.sh` | `e1ae184c…`, `stage_c/cascade_progestin_withdrawal_v060.metadata.json → outputs` |
| `output/perturbations/stage_c/historical_comparison.png` | `stage_c/compare_historical.py --regenerate` | `58d76ae7…`, `stage_c/historical_comparison_summary.json → figure_sha256` |
| `output/progesterone_withdrawal_redraw/fig3b_switch_positions_normalized.png` (the historical figure) | `historical_v051/redraw.sh` | `c92f687d…`, `historical_v051/ORIGINAL_SHA256SUMS.tsv` |

Both figures read marker-gene labels from `docs/u6_semantics/component_map.tsv`,
which the PCSK5 correction (`0735b73`) changed: `E_PC6` is now read through
PCSK5, not PCSK6. That is why the cascade's hash moved from `17f736e6…` to
`e1ae184c…` on this branch, while every bundle table stayed byte-identical. It
is also why `historical_v051/redraw.sh` on the current tree reproduces the four
historical tables byte for byte but not fig3b: redrawn against the component map
before the correction (`0735b73^`), fig3b is again byte-identical to
`c92f687d…` (checked 2026-10-19).

They are kept out of the tree because the independent review snapshot does not
read binary files, so a tracked PNG could not be reviewed. The updated cascade
shows 2,000 paired trajectories, control stationary, no node that needs more
than one switch (`n_switches_min` ≤ 1, a lower bound: an out-and-back pair hidden
inside one 0.01 window is not excluded), no unresolved window and no censored
node in either arm. A second independent
block (`seedB`) was run, and re-runs reproduced every bundle table byte for byte
for the same seed.

**Where the differences from the historical figure come from** (medians of
per-node positions; `stage_c/historical_comparison_summary.json` and the
regenerated comparison figure):

| factor | how isolated | max \|Δ median\| (normalised time / rank / absolute) | verdict |
|---|---|---|---|
| stochastic variability | v0.6.0 block A vs block B | 0.024 / 0.029 / 0.19 (median 0.008 / 0.009 / 0.04) | the reference envelope |
| initialisation and seed scheme | historical run vs new tool, both v0.5.1 | 0.021 / 0.044 / 0.17 | within or near the envelope; switching fractions differ by ≤ 0.016 (relay draws: stratified vs i.i.d.) |
| normalisation | rank vs normalised time, same events | rows move by up to 7 places (Spearman 0.98) | changes within-wave order only, which is unresolved anyway |
| event definition | same first-switch definition and tick in both; no node needs more than one switch in any run (`n_switches_min` ≤ 1, a lower bound) | none detected | none from the definition; hidden pairs inside one tick window are invisible to both alike |
| model version | new tool on v0.5.1 vs v0.6.0, same settings and drawn states | 0.095 / 0.129 / 0.68, all at `OUT_EPITHELIAL_RECEPTIVE` (0.42 → 0.52); every other node ≤ 0.018 in normalised time (next largest: 0.029 in rank, 0.099 in absolute time) | one real change, explained by a rule change |

Six rules differ between v0.5.1 and v0.6.0. Four only remove an intervention
marker (`E_PGR`, `S_PGR`, `S_HAND2`, `X_SPP1_LUMEN_FREE`) and behave identically
with the marker OFF. `OUT_EPITHELIAL_RECEPTIVE` no longer requires `E_PAEP`
(`E_RECEPTIVE_SURFACE and E_PAEP` → `E_RECEPTIVE_SURFACE`), so it now falls with
the receptive surface instead of at the earlier of the two, hence its later
position. `E_ESTROGENIC_PROLIFERATION` no longer reads `not S_HAND2`, yet HAND2
loss still precedes it in every trajectory (2,000 / 2,000 in both versions),
now only through `S_FGF_MITOGENIC` (HAND2 before FGF in all 1,992 trajectories
where the order is identifiable; in the other 8 both switched within one tick
window).

**The historical ordering claims, re-read** (P(A before B | both switch, order
identifiable), exact binomial 95 % interval over the identifiable trajectories;
v0.6.0 block B in brackets; at most 15 trajectories per claim share a window and
are left out, `ordering_claims` in the summary JSON):

| claim | historical v0.5.1 | tool v0.5.1 | tool v0.6.0 A [B] |
|---|---|---|---|
| stromal before epithelial phenotype loss | 0.598 | 0.612 | 0.701 (0.681–0.721) [0.694] |
| adhesion competence before epithelial receptivity | 0.627 | 0.634 | 0.752 (0.730–0.773) [0.732] |
| adhesion competence before stromal decidualisation | 0.557 | 0.614 | 0.593 (0.568–0.617) [0.564] |
| epithelial vs stromal PGR loss | 0.500 | 0.501 | 0.501 [0.497] |
| S_HAND2 before E_ESTROGENIC_PROLIFERATION | 1.000 | 1.000 | 1.000 [1.000] |

The first two move with the `OUT_EPITHELIAL_RECEPTIVE` rule change. The third
differs by 0.057 between the historical run and the tool on the same model,
more than the 0.029 between two independent v0.6.0 blocks, which is consistent
with the historical intervals being too narrow (consecutive seeds, §4.3); it is
not attributed to the model.

**Withdrawal vs mifepristone at 2,000 pairs** (`mifepristone_after_ht__v060__n2000__seedA`):
identical first-switch times in every node-trajectory cell, and identical
switching fractions.

## 7. Owner decisions

**OD-1 (2026-10-08): `all_non_inputs` is the default continuation policy for the
perturbation-cascade analysis.** Approved by the owner on the evidence of §4.2:
with the registered `extended_maternal_joint` policy the 10 nodes it does not
carry (`E_PAEP`, `S_PRL`, `S_IGFBP1`, the four `OUT_*`, the three `X_*_ROUTE`)
restart from their cfg state and relax back, so the *unperturbed* control
switches in up to 100 % of trajectories (8 nodes, 1,000 pairs), whereas carrying
every non-input node from a horizon-25 lineage gives 0 control switches and a
start that is a fixed point.

Scope: the default of `dt_adoc.cascade` (`StartSettings.memory_policy`,
`--memory-policy`) only. It does **not** change any registered protocol's
continuation policy in `config/protocols_markerless.yaml`, the runner's
defaults, the biological model, or the frozen `dropout_e2` design and its
interpretation. The departure is recorded in every bundle (`metadata.json →
starting_state → perturbation_memory_policy`), and `control_stationary` checks on
every run that it holds.

## 8. Limits

- Rates are all 1, so timing reflects topology and the stochastic dynamics, not
  calibrated kinetics; only order is
  interpretable, and only where precedence resolves it.
- Positions are conditional on switching; the switching fractions beside each
  row say how many trajectories contribute.
- The interface relays are hand-set priors (Stage 4b §5): any fraction tied to
  them is a prior, not a measurement.
- Marker genes and measurability classes come from the U6 tables, generated
  from the scRNA observation map; `metadata.json → annotation_sources` pins them.
- Not implemented now: comparing two perturbations beyond the per-run control,
  forced-ON effects, model-only target ablation (owner decision), rule
  replacement, and faster backends for 10⁵ trajectories (the bundle format and
  the per-trajectory runner allow both later).
