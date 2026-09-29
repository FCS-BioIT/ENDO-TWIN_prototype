# C3a pre-registration — addendum 01: anti-SPP1 removed from scope

**Dated 2026-09-29. Prospective. Committed alone, before any C3a simulation.**
It amends `docs/c3_kinetic_readouts/preregistration.md` as frozen at `0c7da9c`.
The governing C3a specification is now that file plus this addendum. Where
they differ, this addendum governs. Neither file may change after the run
starts.

**Classification: `SEMANTIC_OR_PROTOCOL`.** It changes the scope of the
pre-registered comparison and its multiplicity. It is not a wording correction.

## Why, and why it is prospective

- **Owner decision, 2026-09-29.** Anti-SPP1 is no longer an interesting
  digital-twin calibration perturbation, and is unlikely ever to be
  perturbed experimentally.
- **No C3a simulation has run and no C3a result has been observed.** At
  this commit `docs/c3_kinetic_readouts/` holds only the two
  pre-registration files. No attempt journal, output table or run manifest
  exists, and no seed has been reserved or spent.
- The decision is therefore not informed by any C3a value.

## What is removed from C3a scope

- the classified `anti_spp1` pair: control `control_ext`, perturbed
  `anti_spp1`, differing input `IN_ANTI_SPP1`;
- the descriptive contrast `anti_spp1_vs_declared_twin`;
- the phases `anti_spp1_maternal` (`hormone_treated_anti_spp1`) and the
  anti-SPP1 challenge (`adhesion_challenge_hormone_treated_anti_spp1`), at
  both horizons;
- the descriptive washout arms `washout` and `adhesion_challenge_washout`.
  Their lineage runs through the anti-SPP1 maternal phase, so they go with it.

**This is a scope removal, not a deletion of SPP1 biology.** Nothing in
`config/protocols.yaml`, `config/perturbations.yaml` or the v0.5.2 model is
edited. `IN_ANTI_SPP1`, `X_SPP1_LUMEN_FREE`, the SPP1 adhesion route and the
anti-SPP1 protocols keep their historical definitions.

## What remains, frozen

Two classified pairs per family:

| pair | control | perturbed | differing input |
|---|---|---|---|
| `mifepristone` | basal 1 → E2 2 → HT 4 → **HT extension 2** → challenge 1 | basal 1 → E2 2 → HT 4 → mifepristone maternal 2 → mifepristone challenge 1 | `IN_MIFEPRISTONE`, phases 4–5 |
| `hand2_loss` | basal 1 → E2 2 → HT 4 → challenge 1 | basal 1 → E2 2 → HT with HAND2 loss 4 → HAND2-loss challenge 1 | `IN_HAND2_LOSS`, phases 3–4 |

- **The HT extension** is the same schedule-matching counterfactual as
  before. Its duration is now read from the declared mifepristone maternal
  phase (2.0), where it was read from the anti-SPP1 phase before; both are
  2.0.
- **One descriptive contrast** remains: `mifepristone_vs_declared_twin`,
  labelled `schedule_unmatched_descriptive` and never classified.

**Multiplicity.** Each family has 2 pairs × 2 estimands = **4 bands**, so
the multiplier is at `0.05 / 4` per estimand:

- `t₁₉ = 2.758586` (was 2.943895), for the empirical paired-block
  reproducibility bands of section 7;
- `q = 2.497705` (was 2.638257), for the section 10 trajectory-count
  sensitivity criterion.

Both are two-sided quantiles at `α = 0.0125`: t with 19 degrees of freedom,
and the standard normal.

**MaBoSS tasks.** Per block, at both trajectory counts:

| phase run | declared horizon | converged horizon |
|---|---:|---:|
| basal, E2, HT (shared prefix) | 3 | |
| HT extension (counterfactual) | 1 | |
| maternal perturbation phases: mifepristone, HAND2-loss HT | 2 | |
| challenges: twin after HT, control after extension, mifepristone, HAND2 loss | 4 | 4 |
| **per block** | **10** | **4** |

- That is **14 tasks per block** at `N = 20,000` and at `N = 2,000`. There
  are no descriptive washout phases left to skip at the check count.
- **Total: 560 MaBoSS tasks** in 40 worker jobs.
- At the section 13 extrapolation, this is about 70–80% of the former
  runtime.

**Unchanged:**

- `δ = 0.005`;
- `R = 20`;
- `N = 20,000` governing and `N = 2,000` as the check count;
- the seed rules and ranges (`2,000,001 + r·20,000` and `2,400,001 + r·2,000`),
  which are unspent;
- both estimands and both horizons (declared 1.0, converged 25.0);
- the bands, the section 9 kinetic classifier, the zero-occupancy sub-label,
  the section 10 records, and the claim ceiling.

## Binding

The run binds to both governing files:

- the pre-registration, at its blob in `0c7da9c`;
- this addendum, at its blob in the commit that adds it.

It also binds to `config/protocols.yaml`,
`models/specs/parameter_scenarios.yaml` and the v0.5.2 model tree, each at
its blob in `0c7da9c`. The run manifest and the attempt journal name both
governing files.

## C4

The C4 work on a rate-based or partial anti-SPP1 penalty is **not pursued**.
It would be reopened only if an SPP1 perturbation is explicitly
reintroduced in a future scope decision.
