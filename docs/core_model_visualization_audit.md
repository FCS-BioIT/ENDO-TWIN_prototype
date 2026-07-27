# Core MaBoSS model audit from a visualization standpoint

Building the sequential pathway-dynamics animation
([`docs/visualization.md`](./visualization.md)) required reading the model's own
metadata tables as a machine-readable source of node identity, compartment,
role and edge sign. That exercise surfaced places where the current core is
already sufficient, and places where a downstream consumer has to infer
something the model does not state.

This document records those findings and nothing else. **No recommendation here
justifies altering the Boolean model to make a figure look better.** Where a
finding touches biology, the correct next step is evidence review, not a layout
change.

Scope of evidence: `adoc-core-v0.1.0` (43 nodes, 58 edges) and
`adoc-literature-v0.2.0` (55 nodes, 88 edges), plus one bounded sequential run
of each model's declared continuation lineage at seed 1. Claim level:
`structural` — these are contract and reachability observations, not calibrated
or validated results.

---

## 1. Findings

### 1.1 The node dictionary is already a usable visual registry

`node_dictionary.tsv` carries `node_id`, `label`, `compartment`, `model_role`
and `confidence` for every node in both models. That was enough to drive node
placement, colour, uncertainty styling and panel membership without inventing a
parallel node list. `config/visualization.yaml` therefore holds layout
coordinates, ordering and short display labels only.

This is the single most useful property of the current design and it should be
preserved. A second, undocumented biological node list maintained beside the
model would be a regression.

### 1.2 Compartment values are richer than three compartments

Observed `compartment` vocabulary:

| Model | Values |
|---|---|
| `adoc-core-v0.1.0` | `epithelium`, `stroma`, `interface`, `extracellular`, `shared` |
| `adoc-literature-v0.2.0` | the above plus `input_boundary`, `stroma_external` |

Two consequences for any consumer:

- `interface` and `extracellular` are distinct in the table but both belong
  outside the cells. The animation maps both to one extracellular/interface
  band. Whether that distinction is load-bearing biology or incidental
  vocabulary drift is not recorded anywhere.
- `shared` and `input_boundary` are not really compartments; they mark protocol
  inputs. The renderer has to fall back on the `IN_` prefix to place them. The
  prefix and the compartment column carry overlapping information, and the
  prefix is the more reliable of the two.

Similarly, `OUT_` phenotype nodes carry a *cellular* compartment
(`OUT_STROMAL_DECIDUALIZED` is `stroma`) even though they are derived readouts
rather than located entities. Again the prefix, not the column, is what a
consumer can trust.

### 1.3 `model_role` is expressive but unbounded

`adoc-core-v0.1.0` uses 13 distinct roles; `adoc-literature-v0.2.0` uses 25,
including singletons such as `protease`, `pathology_input`, `boundary_input`,
`mechanical_regulator` and `decidual_support`. Nothing constrains the
vocabulary, and the two models do not share one.

The animation needed only a coarse partition — which roles indicate structural
uncertainty — and had to enumerate the relevant values in configuration. A
consumer wanting "all readouts" or "all perturbable targets" cannot get a
reliable answer today.

### 1.4 Confidence vocabularies differ between models

| Model | Values |
|---|---|
| `adoc-core-v0.1.0` | `verified`, `candidate`, `assumption` |
| `adoc-literature-v0.2.0` | `verified`, `high`, `medium`, `assumption` |

`candidate` disappears and `high`/`medium` appear. Any consumer thresholding on
confidence — the animation's dashed-border rule does exactly this — must special
case per model. This is a contract inconsistency, not a presentation problem.

### 1.5 Orphan nodes

Nodes with no incoming and no outgoing edge in `edge_evidence.tsv`:

| Model | Orphans |
|---|---|
| `adoc-core-v0.1.0` | `OUT_EPITHELIAL_VIABLE`, `OUT_STROMAL_VIABLE` |
| `adoc-literature-v0.2.0` | `IN_XAV939`, `IN_HCG`, `IN_EMBRYO_CONDITIONED_SIGNAL` |

The two core orphans are the declared safety placeholders, which the phenotype
contract already marks `structural_placeholder`. Their absence from the edge
table is consistent with that.

**`IN_XAV939` deserves attention.** It is a protocol input that
`hormone_treated_maternal` sets ON — it is part of the published hormone
conditioning cocktail — yet `adoc-literature-v0.2.0`'s evidence table records no
edge from it to anything. In `adoc-core-v0.1.0` it does act, via
`IN_XAV939 -> E_AXIN` (edge E003, `candidate`). So the literature model accepts
a documented experimental input that currently cannot influence any downstream
node.

That is a modelling question, not a visualization question. It is recorded here
because building the figure is what made it visible. It should go to evidence
review, and the model must not be edited to resolve it on visual grounds.

### 1.6 Terminal and source-only nodes

Non-`OUT_` nodes that never regulate anything: `S_IL11` (core), `S_HAND2`
(literature). Non-`IN_` nodes that are never themselves regulated: the three
`X_INTERFACE_*_RELAY` structural-uncertainty nodes in both models, plus
`X_MECHANICAL_STRESS_RELAY` (literature) and `OUT_BARRIER_DAMAGED` (core).

The relay nodes being ungoverned is by design — they are explicit uncertainty
placeholders — but nothing in the tables distinguishes "deliberately ungoverned
relay" from "regulator we have not wired up yet".

### 1.7 Nodes whose probability never moves

Across the declared reference lineage at seed 1:

- `adoc-core-v0.1.0`: `OUT_BARRIER_DAMAGED` is identically 0.0 for the entire
  six-phase run. Near-invariant (range < 0.02): `OUT_EPITHELIAL_VIABLE` and
  `OUT_STROMAL_VIABLE` (pinned at 1.0), `X_ADHESION_ROUTE_REDUNDANT`,
  `X_INTERFACE_ANTIADHESIVE_RELAY`, `X_INTERFACE_REDUNDANT_RELAY`.
- `adoc-literature-v0.2.0`: none are strictly invariant. Near-invariant:
  `OUT_MATERNAL_ADHESION_COMPETENCE` (max 0.009), `OUT_STABLE_ADHESION`
  (max 0.002), `X_INTERFACE_ANTIADHESIVE_RELAY`.

The literature model's two adhesion phenotypes barely leave zero under this
lineage. That is a real property of the current provisional model, and the
animation displays it honestly rather than rescaling to make the panel look
active. It is consistent with the repository's existing position that the model
is not yet calibrated.

`X_INTERFACE_SPP1_RELAY` is worth separating out: its *range* across the run is
small but its *level* is high (up to 0.95 core / 0.70 literature). A
"never changes" filter must not be confused with a "never active" filter.

### 1.8 Edges that cannot act under the tested protocol

Edges whose regulator never exceeds P = 0.01 anywhere in the reference lineage:
3 of 58 (core), 5 of 88 (literature).

Both models: `IN_MIFEPRISTONE -> E_PGR` and `IN_MIFEPRISTONE -> S_PGR`. This is
expected — the reference lineage animated for the README runs the anti-SPP1
branch, not the mifepristone branch, so the drug input is off throughout. These
edges are protocol-inactive, not model-inactive, and a different lineage
activates them.

The remaining ones are more informative: `OUT_BARRIER_DAMAGED -> OUT_BARRIER_MATURE`
(core) and `OUT_MATERNAL_ADHESION_COMPETENCE -> OUT_STABLE_ADHESION` (literature)
have regulators that stay at or near zero, so downstream nodes are effectively
unreachable through them under this protocol.

The animation draws these edges at its minimum opacity rather than hiding them,
so a reader can see that a wired route is not carrying activity. Hiding them
would misrepresent the topology.

### 1.9 What the model does not state machine-readably

Assembling the figure required three mappings that are not in the model:

1. **Node to observable panel.** Which nodes are the reportable molecular
   readouts had to be enumerated in `config/visualization.yaml`. `model_role`
   nearly encodes this (`readout`, `readout_or_ligand`) but not consistently —
   `S_SPP1` is `decidual_support` and `E_SPP1_EXPR` is `ligand_source`, yet both
   are reported readouts.
2. **Protocol to input timeline.** Effective input state per phase had to be
   reconstructed by parsing `IN_*.istate` from each condition `.cfg` and applying
   the step's `input_states` override. It is derivable and the derivation is
   tested, but it is a derivation, not a declaration.
3. **Latent state vs measured readout vs perturbable target vs derived
   phenotype.** Only the last is explicit, via `phenotype_contract.tsv`. The
   other three are inferable only by reading `model_role` values case by case.

---

## 2. Recommendations

### Implement now

- **Freeze the confidence vocabulary across models** (§1.4). One enumerated set
  in a contract file, validated by `validate-models`. This is a contract fix
  with no biological content and it removes a per-model special case from every
  downstream consumer.
- **Send `IN_XAV939` to evidence review** (§1.5). An accepted protocol input
  with no outgoing edge in the literature model is either a missing edge or a
  reason to stop setting it. Resolve by evidence, not by layout.
- **Record the prefix convention as a contract** (§1.2). `IN_` = protocol input,
  `OUT_` = derived phenotype is already relied on by the runner
  (`_state_tracking_override_text_for_model` externalises exactly the non-`IN_`
  nodes) and now by the renderer. It should be stated and validated rather than
  assumed.

### Useful after Phase 1C

- **Bound the `model_role` vocabulary** (§1.3) and add an explicit
  `node_kind` column distinguishing latent state / measured readout /
  perturbable target / derived phenotype (§1.9.3). This is the single change
  that would most reduce configuration in downstream consumers.
- **A machine-readable node-to-observable mapping** (§1.9.1), so the readout
  panels derive from the model the way the phenotype panel already derives from
  `phenotype_contract.tsv`.
- **A declared protocol-to-input timeline** (§1.9.2), replacing cfg parsing with
  a stated per-phase input table.
- **Mark deliberately ungoverned relays** (§1.6) so "uncertainty placeholder"
  is distinguishable from "not yet wired".
- **A `never_varies` diagnostic in `validate-models`** (§1.7), reporting nodes
  invariant across a declared reference lineage. Diagnostic only — an invariant
  node is not automatically a defect.

### Future PhysiBoSS / interface work

- Explicit cross-compartment signal annotations on edges. The renderer currently
  infers cross-compartment status by comparing the two endpoints' compartments,
  which is adequate for a schematic but would not survive a real spatial
  coupling where the transport mechanism matters.
- Separating `interface` from `extracellular` with stated semantics (§1.2).
  Irrelevant to a well-mixed MaBoSS model; load-bearing the moment there is
  geometry.

### Not appropriate for the current MaBoSS model

- **Manual layout coordinates in the model tables.** Layout is presentation and
  belongs in `config/visualization.yaml`. Rejected.
- **Pruning orphan or invariant nodes to tidy the figure.** The safety
  placeholders and uncertainty relays are declared, intentional, and documented
  in the phenotype contract. Rejected.
- **Adding edges so that every node visibly moves.** This would fabricate
  mechanism to improve a picture. Rejected outright.
- **Encoding edge weights or activity levels in the model to drive opacity.**
  MaBoSS edges have no weight. The animation's opacity cue is explicitly labelled
  as a regulator-activity cue and not a strength. Rejected.
- **Rescaling phenotype panels so near-zero adhesion probabilities look
  active** (§1.7). The values are what the provisional model produces. Rejected.

---

## 3. Patterns taken from the reference prototype

`git@github.com:FCS-BioIT/cb-implant_lock_DT_Ia.git` was read as an
implementation reference only and is recorded as such in
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md). It is **not** a
biological authority for DT_ADOC, and none of its Boolean rules, topology or
parameters were carried over.

Adopted: config-driven network diagrams with a fixed per-compartment layout;
static sign-derived edge styling; synchronized marker panels beside the graph;
stride-based frame sampling that always retains the final frame; Pillow frame
assembly; artifact-existence tests.

Deliberately excluded: the spatial agent-based model, PhysiBoSS coupling, chip
geometry, diffusion fields, embryo and blastoid mechanics, trophoblast networks,
adhesion-bond physics, representative-agent selection, and synthetic
transcriptomic profile generation.
