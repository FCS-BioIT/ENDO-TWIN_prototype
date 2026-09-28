# ADOC Literature Superset v0.5.2 — PAEP readout gate and HAND2 routing

**Status: increment of adoc-literature-superset-v0.5.1 by 2 rule(s).** v0.5.1 is not
edited; this directory is the delta. Emitted by `dt_adoc.reporting.v052_increment`
from the 2026-09-28 reconciliation of the 163-paper literature re-audit.

## The changes

```
C1  OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE and E_PAEP   (adoc-literature-superset-v0.5.1)
C1  OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE   (adoc-literature-superset-v0.5.2)
C5  E_ESTROGENIC_PROLIFERATION = IN_E2 and S_FGF_MITOGENIC and not S_HAND2   (adoc-literature-superset-v0.5.1)
C5  E_ESTROGENIC_PROLIFERATION = IN_E2 and S_FGF_MITOGENIC   (adoc-literature-superset-v0.5.2)
```

- **C1 — phenotype and output semantics.** PAEP/glycodelin is a
  secretory-differentiation readout. No primary source perturbs it with an
  adhesion endpoint, so it must not define the reported epithelial receptivity
  phenotype. This does **not** make PAEP biologically irrelevant: `E_PAEP`
  remains an executable, observable secretory state, and the ADOC PAEP outlet
  still maps to it (`OM-001`).
- **C5 — a semantic change to the model architecture, by design.** The parent
  encoded HAND2 twice: it vetoed epithelial proliferation directly, and it also
  suppressed the stromal mitogenic relay. This version encodes HAND2 once, as
  HAND2 → stromal mitogenic relay (`S_FGF_MITOGENIC = not S_HAND2`) → epithelial
  proliferation. The evidence supports stromal paracrine mediation, not a direct
  epithelial HAND2 edge. C5 is **not** a bit-identical refactor, **not** a safe
  algebraic cleanup, and **not** dynamically neutral. Under asynchronous
  updating, proliferation now stays on until the relay itself switches off. That
  delay is the intended consequence of representing the relay explicitly.
- **The relay's name is kept; its identity is not asserted.** `S_FGF_MITOGENIC`
  keeps its name in this version so the scope stays bounded. The exact human
  relay identity is uncertain: Murata 2019 finds only FGF9 HAND2-regulated in
  human stroma, and measures a stromal and vascular effect, not an epithelial
  one. A later version may generalise the node to `S_TO_E_PROLIFERATION_RELAY`.
  No FGF, WNT or HAND2 mechanism is added here.

## What does not move, and what does

- **The composed Boolean function of every node is unchanged over the free
  variables.** Every node's truth table is compared against v0.5.1's in
  `docs/v052_paep_hand2/`. So no condition can move an unperturbed fixed point.
- **Three internal-node clamps do separate the versions at steady state.**
  - `E_PAEP` forced off no longer abolishes receptivity (C1's intent).
  - `E_RECEPTIVE_SURFACE` forced on no longer needs PAEP (C1's intent).
  - `S_FGF_MITOGENIC` forced on now drives proliferation under progestin
    (C5's full-mediation semantics).

  The list is in `docs/v052_paep_hand2/separating_clamps.json`.
- **Neither changed node is a leaf.** `OUT_EPITHELIAL_RECEPTIVE` is read by
  `OUT_MATERNAL_ADHESION_COMPETENCE`. `E_ESTROGENIC_PROLIFERATION` is read by
  `E_RECEPTIVE_SURFACE`, and through it by the adhesion routes and outputs. The
  transient therefore reaches seven nodes, and it is measured, not assumed:
  `docs/v052_paep_hand2_cleanup.md` gives the paired comparison, and
  `docs/v052_paep_hand2/transient_preregistration.md` its frozen design.
- **Curated edges stop executing.** `LE077`, `LE094` are `retired` in `topology.tsv`
  against `topology_increment_adjudications.tsv`, and are kept in
  `edge_evidence.tsv` as history.

## What it is not

- **Not a new molecular mechanism.** C1 removes a readout gate. C5 removes an
  unsupported direct edge in favour of the stromal relay the model already
  carried. The claim ceiling in `provenance.toml` is unchanged.
- **Not adopted by any analysis.** Every analysis module pins its own model
  version, and none is repointed here.
- **Not a calibrated or personalized model.** MaBoSS probabilities are simulated
  trajectory frequencies under stated rules, rates and initial conditions, and
  MaBoSS time is relative.

## Artifacts

Identical to adoc-literature-superset-v0.5.1 except the files listed under `[increment]` in
`provenance.toml`. See v0.4.0's `README.md` for the artifact inventory, scope and
claim boundary, all of which continue to apply.
