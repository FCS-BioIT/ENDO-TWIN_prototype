# MaBoSS pathway-dynamics visualization

> **Historical guide (written for the `v0.2.0` animation, last revised
> 2026-07-30).** The animation now in the README is
> `docs/assets/adoc_superset_pathway_dynamics_v0.6.0.gif`, rendered by
> `pixi run render-dynamics-superset` from `adoc-literature-superset-v0.6.0`
> along `config/protocols_markerless.yaml` (basal → E2-primed →
> hormone-treated → adhesion challenge; provenance in its `_metadata.json`
> sidecar). Its phase-boundary behaviour is described in the README caption:
> only the declared memory set is carried across a boundary, and every other
> non-input node restarts from its initial state. The phase table and the
> continuation paragraph below describe the `v0.2.0` render and do not say
> that. Two statements below were later superseded: the superset `v0.3.0` GIF
> *was* committed (`ab2fa9d`), and superset animations now exist (`v0.3.0`,
> `v0.4.0`, `v0.6.0`). The rest is kept as written.

This document explains the animated figure produced by
`dt_adoc.reporting.dynamics`, `dt_adoc.reporting.network_figure`,
`dt_adoc.reporting.render_dynamics` and `dt_adoc.simulation.timeline`, and
configured by `config/visualization.yaml`. Read it alongside
[`docs/scientific-review-policy.md`](scientific-review-policy.md) before
quoting anything the figure shows.

## What the animation shows

The animation renders one MaBoSS model — by default `adoc-literature-v0.2.0`,
though the renderer works with every model returned by
`available_models()` — as it runs the model's own declared protocol lineage
(the `continuation_from` chain, not a narrative ordering chosen for the
figure). For `adoc-literature-v0.2.0` that lineage is:

`basal_maternal` → `e2_primed_maternal` → `hormone_treated_maternal` →
`adhesion_challenge_hormone_treated_anti_spp1` → `adhesion_challenge_washout`

5 phases spanning 9.0 MaBoSS relative time units. Each frame shows:

- a compartment schematic where node fill encodes **P(node = ON) across
  simulated MaBoSS trajectories** — never a concentration, expression level,
  secretion amount or flux;
- static, evidence-derived edges whose opacity tracks the regulator node's
  P(ON) as a visual cue;
- four synchronized time-series panels (protocol inputs, epithelial readouts,
  stromal readouts, phenotype probabilities) with a moving time cursor;
- a header naming the active phase, the model version, the protocol id, the
  seed and the trajectory count.

The committed animation (`adoc_maboss_pathway_dynamics.gif`) shows the
**complete executable network of `adoc-literature-v0.2.0`: all 55 nodes and all
88 evidence edges**, rendered at 3000×1650 px, 46 frames, from seed 1 with 2000
trajectories per phase (about 3.4 MB). Nothing is dropped for readability.

The resolution and the `--font-scale` multiplier are set together deliberately.
Raising dpi alone adds pixels but leaves text the same fraction of the frame, so
it stays unreadable once the image is scaled down to README width; `--font-scale`
enlarges every text element relative to the canvas, which is what actually makes
a 55-node figure legible inline. Click through for full resolution.

A smaller curated 36-node / 54-edge overview is still available via
`--view overview`; it is no longer what ships in the README.

## What it does not show

The figure is a MaBoSS state-probability visualization and must not be
described as, or read as implying, any of the following:

- molecular concentrations, expression levels, or secretion amounts;
- single-cell trajectories;
- spatial or cellularly resolved tissue organisation;
- actual pathway flux;
- causal edge strength, joint edge activity, or regulatory strength;
- PhysiBoSS or any other agent-based simulation output;
- clinical implantation probability;
- validated drug efficacy.

Use phrasings such as "P(node = ON)", "P(stable adhesion)", and "protocol
input state" rather than causal or clinical language. See
`codex/skills/adoc-result-validator/references/claim-boundaries.md` for the
safe-language rules this figure follows.

## Figure layout and compartments

The network panel is a fixed compartment schematic, not a spatial map. A
node's visual class is resolved by `classify_node()`:

1. Node-id **prefix** wins first: `IN_` → the `input` class (top band),
   `OUT_` → the `output` class (bottom band).
2. Otherwise the model's own `node_dictionary.compartment` column decides the
   class: `epithelium` → `epithelial` (left), `stroma` → `stromal` (right),
   and `interface`, `extracellular`, `stroma_external` → `extracellular`
   (centre). `input_boundary` and `shared` also map to the `input` class.

This precedence is why extracellular/lumen nodes such as
`X_SPP1_LUMEN_FREE` and `X_MECHANICAL_PERMISSIVE_ECM` sit in the centre band
with the maternal-embryo interface rather than inside the stromal
compartment box, even though stromal cells strongly regulate them.

Each compartment box is drawn with its own pale/saturated colour pair and a
titled border; node positions are computed once per (model, view) and held
fixed for every frame, so nothing moves between frames except fill colour,
edge opacity, the time cursor and the phase header.

## Node colour semantics

Node fill is a **deterministic, monotonic linear RGB interpolation** between
the node's compartment `pale` colour at P(ON) = 0 and its `color` at
P(ON) = 1 (`probability_to_color()`). Intermediate probabilities render as
visibly intermediate colours; they are never rounded to an on/off colour.
Each node also carries a numeric caption: two decimal places for simulated
nodes, and a single `0` or `1` for protocol-input nodes, whose deterministic
state reads as an exact value rather than a probability.

Nodes whose `model_role` is `structural_uncertainty` or `latent_state`, or
whose `confidence` is `assumption` or `candidate` (per
`config/visualization.yaml`'s `uncertainty` block), get a dashed border.
Phenotype outputs (`OUT_` prefix) get a heavy square border instead of a
rounded one, regardless of uncertainty status.

## Edge semantics and the opacity limitation

Edge existence, sign and static style come entirely from the selected
model's `edge_evidence.tsv` — nothing about an edge is invented in the
visualization layer:

- **activation** → a green (`#2D6A4F`) filled arrowhead;
- **inhibition** → a red (`#BC4749`) blunt-bar ("T") head;
- **low-confidence** edges (`assumption` or `candidate` in `edge_evidence`)
  → dashed line style;
- **cross-compartment** edges (source and target in different visual
  classes) → drawn thicker.

The only value that changes frame to frame is **opacity**, which follows the
regulator (source) node's P(ON), linearly rescaled between a minimum and
maximum alpha (0.10–0.85 by default). For an edge whose source is a protocol
input, the input's deterministic 0/1 state is used in place of a trajectory
value, since input nodes are never in the simulated trajectory (see below).

This opacity is a **visual regulator-activity cue only**. It is not causal
flux, reaction rate, edge probability, regulatory strength or pathway flow,
and because it is derived from a single marginal node probability, it cannot
be used to infer joint edge activity or any two-node correlation.

## Protocol phases and time semantics

Time in the figure, on the x-axis of every panel and in the phase header, is
**MaBoSS relative time** as declared by `provenance.toml`
(`maboss_time_units = "relative_only"`). There is no validated mapping to
hours or any other physical time unit, and none is offered anywhere in the
figure or its metadata.

For the committed animation, the five phases and their relative-time spans
are:

| Phase | Protocol id | Relative time | Continues from |
|---|---|---|---|
| 1 | `basal_maternal` | 0.0 – 1.0 | (start of lineage) |
| 2 | `e2_primed_maternal` | 1.0 – 3.0 | `basal_maternal` |
| 3 | `hormone_treated_maternal` | 3.0 – 7.0 | `e2_primed_maternal` |
| 4 | `adhesion_challenge_hormone_treated_anti_spp1` | 7.0 – 8.0 | `hormone_treated_maternal` |
| 5 | `adhesion_challenge_washout` | 8.0 – 9.0 | `adhesion_challenge_hormone_treated_anti_spp1` |

Each phase after the first is initialised from the **actual transferred
continuation state** of the preceding phase (the same
`protocol_continuation` machinery the structural smoke uses) — nothing is
recomputed, interpolated or synthesised across the phase boundary. Vertical
dotted lines and alternating phase-band shading in the time-series panels
mark these boundaries.

## The synchronized panels

Panel membership is a *preferred ordering* declared in
`config/visualization.yaml`; any listed node absent from the selected model
is silently skipped (not substituted), so one configuration file serves every
registered model.

- **Protocol inputs** (`inputs` panel) — deterministic step functions for the
  `IN_*` nodes listed under `panels[0].members` (e.g. `IN_E2`,
  `IN_PROGESTIN`, `IN_cAMP`, `IN_ANTI_SPP1`, `IN_EMBRYO_PRESENT`, …). These
  are protocol settings, never simulated quantities — see the next section.
- **Epithelial readouts** — a curated set of epithelial nodes
  (`E_PAEP`, `E_SPP1_EXPR`, `E_LIF`, `E_HBEGF`, `E_PODXL`,
  `E_MUC1_BARRIER`), read straight from the concatenated trajectory table.
- **Stromal readouts** — the stromal counterpart
  (`S_PRL`, `S_IGFBP1`, `S_SPP1`, `S_BMP2`, `S_HAND2`, `S_IL11`).
- **Phenotypes** — *not* a fixed member list in the config. Its members are
  resolved at build time from the model's own `phenotype_contract.tsv`:
  every row with `executable = true` and `category = primary` that is
  present in the current view (`build_panels()`, `source:
  phenotype_contract`).

## Where biological identity comes from

Node identity, compartment, model role, confidence, human-readable label,
edge existence/sign/confidence, and phenotype definitions all come from the
selected model's own tables — `node_dictionary.tsv`, `edge_evidence.tsv` and
`phenotype_contract.tsv` under `models/extended/<model>/`. `config/visualization.yaml`
is **visual metadata only**: layout regions, colours, node-class mapping,
panel ordering and short display labels. `load_visualization_config()`
enforces this at load time — it raises if the file defines any of the
reserved biological keys (`nodes`, `node_dictionary`, `edge_evidence`,
`phenotypes`, `phenotype_contract`, `compartment`, `model_role`,
`confidence`, `logic`, `sign`, or a biological `edges` list; the one `edges`
key the file is allowed is edge *styling*, not an edge list). A presentation
change can therefore never silently restate or override biology.

### Executable model versus literature catalog

Only the **executable** model is ever rendered. The renderer reads
`node_dictionary.tsv` and `edge_evidence.tsv`; it never reads
`complete_nodes.tsv` or `complete_edges.tsv`. Catalog-only and external-only
entities are therefore structurally unreachable, not merely filtered out — for
the superset they are absent from `network.bnd` entirely, so MaBoSS could not
produce a probability for them even if asked. **No catalog-only node can ever
be displayed with a simulated probability.**

Exact counts, all verified against the canonical TSVs:

| Model | Executable nodes | Executable edges | README overview |
|---|---|---|---|
| `adoc-core-v0.1.0` | 43 | 58 | 28 nodes / 37 edges |
| `adoc-literature-v0.2.0` | 55 | 88 | **36 nodes / 54 edges (the committed GIF)** |
| `adoc-literature-superset-v0.3.0` | 58 | 93 | 39 nodes / 59 edges (not committed) |

The superset additionally ships a literature catalog in `complete_nodes.tsv`
(63 rows) and `complete_edges.tsv` (143 rows). Those totals need care:

- **Nodes**: 63 = 58 `executable` + 4 `catalog_only` + 1 `external_only`. The
  five non-executable ones are `S_STAT3`, `S_DECIDUAL_SENESCENCE_BALANCED`,
  `X_LGALS1_3`, `X_BSG_ITGB1` (catalog-only) and `IN_UTERINE_WNT_CUE`
  (external-only, embryo-side).
- **Edges**: 143 rows are *not* 143 distinct relations. They union two
  provenance views: 93 rows with `catalog_origin=executable_edge` (a 1:1 copy
  of `edge_evidence.tsv`) plus 50 `literature_candidate` rows, of which **39
  are aliases of executable edges already counted** among the 93. The distinct
  relation count is therefore **104** = 93 executable + 10 catalog-only + 1
  external-only.

The discriminating column is `implementation_status` in both files. Do not use
`catalog_origin` for this — it records where a row entered the catalog, not
whether it executes.

The two Mermaid diagrams in the superset directory are code-generated by
`build_mermaid_executable()` and `build_mermaid_complete()` in
`src/dt_adoc/model/superset_family.py`, and are reproducible:
`executable_modules_network.mmd` is the **complete executable graph** (93
edges); `literature_superset_network.mmd` is the 50 `literature_candidate`
rows only, so despite its name it is **not** an exhaustive catalog view.

One consequence worth calling out explicitly: `IN_*` nodes are internal to
the MaBoSS `.cfg` for each condition (the model's state-tracking override
only externalises non-input nodes), so they never appear in
`get_nodes_probtraj()`. The values shown in the inputs panel and as input-node
captions are **deterministic protocol settings** resolved from the condition
`.cfg`'s baseline `istate` plus the active protocol step's overrides
(`resolved_input_states()`) — not simulated or measured quantities.

## Reproducing the animation

```bash
pixi run render-dynamics-demo
```

which is equivalent to:

```bash
PYTHONPATH=src python -B -m dt_adoc.cli render-dynamics \
  --model adoc-literature-v0.2.0 \
  --protocol-suite reference-sequence \
  --output docs/assets/adoc_maboss_pathway_dynamics.gif
```

Other `render-dynamics` options: `--model`, `--protocol-suite`,
`--terminal-protocol`, `--seed`, `--trajectories`, `--frame-stride`,
`--frame-duration`, `--readme-max-width`, `--run-id`, `--view
{overview,full}`, `--output`, `--preview`, `--metadata`, and
`--no-full-resolution`. Rendering executes only the protocol lineage being
animated (five bounded MaBoSS runs for the reference sequence above); it
never triggers a calibration fit, a perturbation screen, or the full
structural smoke.

## Artifacts and provenance

Each run writes:

- `docs/assets/adoc_maboss_pathway_dynamics.gif` — the committed, size-capped
  animation embedded in the README;
- `docs/assets/adoc_maboss_pathway_dynamics_preview.png` — a single static
  frame (about two-thirds through the timeline);
- `docs/assets/adoc_maboss_pathway_dynamics_metadata.json` — model id and
  version, the exact protocol sequence and phase boundaries, seed, trajectory
  count, frame count/duration, image dimensions, and a SHA-256 of every
  source file involved (network `.bnd`, node dictionary, edge evidence,
  phenotype contract, `config/protocols.yaml`, `config/visualization.yaml`,
  and each per-phase trajectory table);
- under `output/visualization/<model_version>/<run_id>/` (gitignored, and
  regenerated by the command above rather than committed): a full-resolution
  GIF (`adoc_maboss_pathway_dynamics_full.gif`, uncapped width) and
  `raw/<protocol_id>__<step_id>_nodes_probtraj.tsv` — the exact concatenated
  MaBoSS trajectory table each phase was drawn from, one file per phase, so
  any value shown on screen can be checked against its source.

Artifacts are deliberately timestamp-free: re-running with the same model,
protocol lineage, seed and trajectory count reproduces byte-identical
metadata and images within one environment.

## Limitations

- The x-axis is MaBoSS relative time only; no validated conversion to hours
  or any other physical unit exists anywhere in this pipeline.
- Edge opacity is a single-node visual cue and cannot establish joint edge
  activity, causal flux, or regulatory strength between two nodes.
- The committed animation shows every executable node and edge of
  `adoc-literature-v0.2.0`. It does not show catalog-only or external-only
  entities, which are structurally unreachable by the renderer.
- Dashed node borders flag declared structural uncertainty or low-confidence
  roles; they are a qualitative flag from the node dictionary, not a
  statistical confidence interval.
- The colour ramp and edge opacity are presentation choices with no
  statistical meaning beyond the P(ON) value they encode; they carry no
  error bars or Monte Carlo uncertainty of their own.
- Rendering runs only the five (or six) lineage protocols needed for the
  animation. It is not a calibration run, a perturbation screen, or the
  project's structural smoke, and passing this render does not itself confer
  any validation label from
  `codex/skills/adoc-result-validator/references/claim-boundaries.md`.

---

## Label change, 2026-07-29 — and why the committed GIF still shows the old wording

`config/visualization.yaml` `short_labels` were changed for two nodes:

| node | was | now |
|---|---|---|
| `X_INTERFACE_REDUNDANT_RELAY` | "Redundant relay" | **"Assumed non-SPP1 relay"** |
| `X_ADHESION_ROUTE_REDUNDANT` | "Redundant route" | **"Non-SPP1 route (assumed relay)"** |

"Redundant relay" was an implementation placeholder read as a biological claim. The node's
own dictionary entry gives the intent away: *"Prevents anti-SPP1 from forcing competence to
zero."* That is a statement about desired model output, not about endometrial biology.

**"Assumed" is the load-bearing word.** It maps to `confidence=assumption` and
`model_role=structural_uncertainty`, and it is the one term that cannot be read as a
measurement. "Capacity" was considered and rejected: it names a tissue property with a
magnitude, which invites reading the relay's `0.40` as an estimate. It is not — it is a
hand-set `istate` in `baseline.cfg:62`, constrained by nothing in `config/calibration.yaml`
or `config/observation_model_map.tsv`.

### What the label must not imply

Verified exhaustively over all 2^18 = 262,144 free-variable assignments:

```
X_ADHESION_ROUTE_REDUNDANT  ==  E_RECEPTIVE_SURFACE  and  X_INTERFACE_REDUNDANT_RELAY
```

Its rule names six epithelial effectors — `E_CD98_CD9`, `E_CDH1_APICAL`, `E_ANXA2_ACTIN`,
`E_HBEGF`, `E_DAG1_CLEAVED`, `E_MUC1_SLEX`. **All six are logically absorbed**, and all six
sit in the 15-node fully clamp-inert set. Deleting the entire OR-group changes nothing.

The evidentiary consequence is sharp. Of the eight declared inputs to this route, `LE064`
through `LE070` are graded `candidate` and carry genuine primary human citations — and every
one of them is provably inert. `LE071`, the relay edge, is graded `assumption` and is the
only input that does any work. **The route's behaviour has zero evidentiary content.**

The label must therefore not imply: a named molecule or effector; that the six curated
effectors contribute anything; that `0.40` is a measured frequency or tissue fraction; any
experimental validation; or that "redundant" is an established finding about SPP1-independent
adhesion.

"non-SPP1" is accurate about *behaviour* — toggling `IN_ANTI_SPP1` changes the route in 0 of
131,072 paired assignments — but note that `X_SPP1_LUMEN_FREE` is in its transitive ancestry
via `LE036`, so any drawn topology will show an SPP1 edge feeding a node labelled non-SPP1.
That path is inert only because the `E_RECEPTIVE_SURFACE` OR-group is also fully absorbed.

### The committed GIF is unchanged and still renders "Redundant relay"

The animation is a raster of `adoc-literature-v0.2.0` and was **not** re-rendered. So
`docs/assets/adoc_maboss_pathway_dynamics_metadata.json` now records a `config/visualization.yaml`
sha256 that no longer matches the live file. That is expected and is recorded here rather than
repaired by a re-render, because re-rendering would not change the frozen model and the label
fix is forward-looking: it takes effect the next time any animation is produced.

### Why no superset animation was produced

The README caption carries a standing gate — the animation is regenerated only when a new
executable candidate model exists and has passed structural, evidence-integrity and
perturbation validation. All three limbs and the precondition are unmet: no new executable
model exists (every increment since records `network.bnd` as untouched); 15 of 58 nodes are
clamp-inert with eight bit-identical to `E_SECRETORY_STATE`; **0 of 267 assertions have
claim-level verified support**; and the Phase 1D review returned `fail` and has not been
re-run.

There is also a mechanical bar. `build_sequential_timeline()` accepts no duration override —
durations come straight from `config/protocols.yaml` (1.0 / 2.0 / 4.0 / 1.0 / 1.0). A superset
animation rendered today would therefore run the challenge at the horizon
`docs/endpoint_convergence_finding.md` identifies as roughly 4000x too early, terminate on the
anti-SPP1 perturbation arm rather than the reference condition, show a phenotype panel flat
near zero, and display the held-out mifepristone arm **above** the unperturbed one. Producing
an honest one requires a code change, not just a render.

Note the legacy figure is not a safe alternative so much as a correctly-labelled one:
`adoc-literature-v0.2.0` carries the *identical* redundant-route rule and the identical
0.70/0.40 relays, so it has the same collapse.

### Capability gaps for any future animation

Three distinctions a current-model figure would need, which the renderer cannot express today:

- **measured vs unmeasured** — nothing in `src/dt_adoc/reporting/` reads
  `config/observation_model_map.tsv`. Only `E_PAEP` (OM-001) and `S_IGFBP1` (OM-002) are
  mapped, yet the panels titled "Epithelial readouts" and "Stromal readouts" are hand-listed
  and include nodes with no ADOC measurement at all. This mislabelling already applies to the
  committed GIF.
- **degree of uncertainty** — `NodeView.uncertain` is a single boolean, so
  `X_ADHESION_ROUTE_REDUNDANT` renders *solid* despite being driven entirely by an assumption.
- **inert and disconnected nodes** — no hook exists; the 15 clamp-inert nodes and the three
  consumerless inputs render identically to load-bearing ones.

An inert-node list must be *derived* (from `dt_adoc.model.topology`), never hand-listed here:
`dynamics.py` rejects biological keys in this config by design.

### Output-path safety (fixed 2026-07-29)

`--preview` and `--metadata` used to fall back to the v0.2.0 defaults **independently of**
`--output`, so rendering another model with only `--output` set wrote its GIF to the new path
while silently overwriting the frozen v0.2.0 preview PNG and metadata JSON.

Both are now **derived from `--output`'s stem** (`_preview.png`, `_metadata.json`). The
derivation reproduces the committed names exactly, so `pixi run render-dynamics-demo` --- which
passes only `--output` --- is unaffected. Explicit `--preview`/`--metadata` still override.

Naming a committed v0.2.0 artifact while rendering any other model now **raises before any
simulation starts**, as does a destination outside the repository root, which previously failed
only after the whole animation had already been rendered. Do not repoint the
`render-dynamics-demo` task, which is hardcoded to v0.2.0.

Note the guard set is a literal frozenset of the three committed paths, not a read of
`provenance.toml`: every model declares an immutability flag --- `immutable` for the baseline,
`immutable_parent` for both others --- so that flag cannot say which model owns `docs/assets/`.
