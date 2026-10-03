# ADOC Literature Superset v0.6.0 — intervention markers removed

**Status: increment of adoc-literature-superset-v0.5.2.** v0.5.2 is not edited; this directory
is the delta. Emitted by `dt_adoc.reporting.v060_increment` as Stage 3 of the
intervention-layer refactor. The design and its equivalence gate are in
`docs/intervention_layer_stage3.md`.

## The transformation

v0.5.2 represents three interventions as constant input nodes that their target
rules veto with `and not IN_X`. This version deletes those nodes and conjuncts:

```
E_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE   (adoc-literature-superset-v0.5.2)
E_PGR = IN_PROGESTIN   (adoc-literature-superset-v0.6.0)
S_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE   (adoc-literature-superset-v0.5.2)
S_PGR = IN_PROGESTIN   (adoc-literature-superset-v0.6.0)
X_SPP1_LUMEN_FREE = (E_SPP1_EXPR or S_SPP1) and not IN_ANTI_SPP1   (adoc-literature-superset-v0.5.2)
X_SPP1_LUMEN_FREE = E_SPP1_EXPR or S_SPP1   (adoc-literature-superset-v0.6.0)
S_HAND2 = (S_BMP2 or S_PGR) and not IN_HAND2_LOSS   (adoc-literature-superset-v0.5.2)
S_HAND2 = S_BMP2 or S_PGR   (adoc-literature-superset-v0.6.0)
```

| deleted marker | library intervention | target(s) |
|---|---|---|
| `IN_MIFEPRISTONE` | `mifepristone` | `E_PGR`, `S_PGR` |
| `IN_ANTI_SPP1` | `anti_spp1` | `X_SPP1_LUMEN_FREE` |
| `IN_HAND2_LOSS` | `hand2_loss` | `S_HAND2` |

The intervention is now timed by the protocol (`interventions` on a step, in
`config/protocols_markerless.yaml`) and rendered by the perturbation engine as an
`activity_veto` of its target(s). The library rows that license this are
`migrated_legacy_behaviour`: each reproduces the v0.5.2 row of the same
intervention, checked exhaustively against the v0.5.2 rule when the library
loads.

## What does not move

- **No biological rule changes.** Every other node's rule is v0.5.2's text, and
  the four rules above are v0.5.2's with the marker held OFF. Gate G8 runs every
  v0.5.2 lineage on both versions and requires the dynamics to be identical
  after projecting the deleted nodes out.
- **`IN_XAV939` is kept.** No rule reads it, and its library row records the
  model's silence about a cocktail reagent rather than a veto. Removing it is
  open question O2.
- **Condition cfg files keep their names.** With the markers gone, a cfg holds
  biological and environmental inputs only, so `hormone_treated_mifepristone.cfg`
  now equals `hormone_treated.cfg`. The arm's intervention is in its protocol. A
  cfg run on its own, outside a protocol, is untreated.

## What does move

- **The state space.** There are three fewer nodes, three fewer free variables
  and three fewer inputs. `IN_HAND2_LOSS`, the only tracked marker, is gone from
  state labels and trajectories. Structural counts are recomputed in
  `docs/intervention_layer_stage3/`, not carried over.
- **Curated edges stop executing in the network.** `LE002`, `LE038`, `LE059` and
  `LE096` are `retired` in `topology.tsv` against
  `topology_increment_adjudications.tsv`, and kept in `edge_evidence.tsv` as
  history. Their inhibition is executed by the intervention layer.

## What it is not

- **Not a new mechanism or a new claim.** The claim ceiling in `provenance.toml`
  is unchanged.
- **Not adopted by any analysis.** Every analysis module pins its own model
  version, and none is repointed here.
- **Not a calibrated or personalized model.** MaBoSS probabilities are simulated
  trajectory frequencies under stated rules, rates and initial conditions, and
  MaBoSS time is relative.

## Artifacts

Identical to adoc-literature-superset-v0.5.2 except the files listed under `[increment]` in
`provenance.toml`. See v0.4.0's `README.md` for the artifact inventory, scope and
claim boundary, all of which continue to apply.
