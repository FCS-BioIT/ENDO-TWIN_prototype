# WP2 prospective prediction: selection and draft

Status: **no candidate currently meets the proposal's requirements.** Nothing is
frozen, and nothing should be. This document records the screen, the verdict and
the smallest correction that would produce an eligible prediction.

Reassessed 2026-11-24 against **`MemoriaCT-individual_Digital Twin_v10`** and
`endotwin-v0.3.0`. The previous version of this page recommended Smoothened
inhibition with pSMAD1/5/8 as the primary readout. **That recommendation is
withdrawn**, for two independent reasons given below.

## What the proposal asks for (SO2, Task 2.1)

v10 is more specific than v8 was. Task 2.1 requires a perturbation

- **not used in model development or calibration**;
- "resulting in an informative downstream **functional** response **beyond its
  direct molecular target**";
- whose "primary functional prediction must be robust to uncertainties in
  Boolean rules, transition rates and initial conditions";
- with everything frozen before testing, and a literature-informed comparator
  for the same primary readout defined **without** MaBoSS;
- evaluated in five independent G1 donors, one control and one perturbed chip
  each. The donor is the unit. **A non-significant difference never confirms a
  predicted no-change.**

### Functional response, pathway activity and target engagement

v10's wording forces a distinction the previous draft blurred.

| | Meaning | Examples in this model |
|---|---|---|
| **Target engagement** | the drug reached and inhibited its target | GLI1/PTCH1 mRNA after a Smoothened antagonist; nuclear FOXO1 after a FOXO1 inhibitor |
| **Pathway activity** | a signalling intermediate moved | pSMAD1/5/8, WNT4, NR2F2, phospho-ERK1/2 |
| **Functional response** | the tissue did something different | decidualization (PRL, IGFBP-1 secretion), epithelial proliferation (Ki67/EdU), epithelial secretory differentiation (PAEP) |

**pSMAD1/5/8 is pathway activity, not a functional endpoint.** Under v10 it
cannot serve as the primary prediction, whatever its robustness.

## The screen

Every comparison in `endotwin/config/protocols.yaml`, every readout WP2 can
measure, across all **48** rule-variant scenarios of `endotwin-v0.3.0`
(`endotwin/results/endotwin-v0.3.0/comparison_directions.tsv`).

A prediction counts as *unambiguous* when its direction is the same in every one
of the 48 scenarios. Only **two of the nine** comparisons produce an unambiguous
**functional** movement at all:

| Comparison | Functional readout | Direction |
|---|---|---|
| `INF_il1b` | decidualization, PRL, IGFBP-1 | down |
| `FOX_foxo1_inhibition` | IGFBP-1 | down |

`HH_smo_inhibition`, `HH_smo_inhibition_hormone_only`, `Q1_bmpr_inhibition`,
`Q2_hand2_knockdown`, `Q2_paracrine_block_e2`,
`Q2_paracrine_block_differentiation` and `REG_hormone_only_vs_supplemented`
produce **no** unambiguous functional movement. For the WP1 comparisons that is
expected and desirable — they are the experiments that *discriminate* open
hypothesis families, so the model deliberately predicts different things under
different variants. It is disqualifying only for WP2, which needs one frozen
direction.

## Candidates assessed

### Smoothened inhibition, hormone-only regimen — **withdrawn**

| Criterion | Assessment |
|---|---|
| Primary functional prediction | **None.** Every functional readout is `no_change` under both CAM variants: decidualization, PRL, IGFBP-1, Ki67, PAEP. |
| Target engagement | GLI1/PTCH1 mRNA — available and appropriate |
| Independent of development perturbations | Yes; no SMO antagonist is in the funded WP1 or WP3 plan |
| Robust to alternative rules | **No, and this is new.** pSMAD1/5/8 falls under `CAM_exogenous_only` but is `no_change` under `CAM_hormone_autocrine`, because endogenous PKA then supplies BMP2 through `E2-28`. The prediction is conditional on an unresolved family. |
| Robust to rates and initial conditions | Yes — the network is acyclic, so fixed points depend on neither |
| Evaluable with planned assays | Yes |
| Beyond the direct target | Only `S_NR2F2` survives both CAM variants, and `S_HH_SIGNALING` and `S_NR2F2` are in the **same alias class**, so NR2F2 is a target-engagement readout wearing a different name |

Two independent disqualifications: no functional prediction, and the pathway
prediction it does make is no longer rule-robust.

### FOXO1 inhibition, supplemented regimen — closest, still ineligible

| Criterion | Assessment |
|---|---|
| Primary functional prediction | IGFBP-1 down — unambiguous in all 48 scenarios |
| Target engagement | nuclear FOXO1 by immunofluorescence |
| Independent of development perturbations | Yes; no FOXO1 inhibitor is in the funded plan |
| Robust to alternative rules | IGFBP-1 yes; **PRL no** — down under `FOX_prl_foxo1_dependent`, unchanged under `FOX_prl_foxo1_independent` |
| Robust to rates and initial conditions | Yes |
| Evaluable with planned assays | Yes — both are already ADOC outlet ELISAs |
| Beyond the direct target | **No for IGFBP-1.** `E2-44` has FOXO1 binding the IGFBP1 promoter: IGFBP-1 falling after FOXO1 inhibition is the direct consequence of inhibiting the target. PRL *is* beyond it (FOXO1 → IRF4 → PRL), but PRL is the readout that is not rule-robust. |

So the robust prediction is uninformative, and the informative prediction is not
robust. That is the whole difficulty, and it is not an accident of this
candidate.

## Why no candidate qualifies, structurally

The functional readouts are **saturated in both regimens**, and the CAM family
now makes this explicit:

- Under the **supplemented** regimen, `IN_cAMP` is ON, so PKA, C/EBPβ and the
  cAMP arm of BMP2 are all held up. Removing an upstream signal changes no
  functional output; the reagent backs it up.
- Under the **hormone-only** regimen with `CAM_exogenous_only`, every stromal
  functional readout is already at **0**. Nothing can fall further.
- Under hormone-only with `CAM_hormone_autocrine` they are all at **1**, and the
  perturbations available outside WP1 do not reach them.

A perturbation can therefore move a functional readout only if it is one of the
WP1 perturbations — which are excluded from WP2 by definition — or if it acts on
PKA itself, which is the direct target rather than something beyond it.

## The smallest necessary correction

Not a change to the model. Two possibilities, in order of preference:

1. **Read v10's robustness requirement as robustness to the uncertainties *not*
   under test.** Taken literally, "robust to uncertainties in Boolean rules"
   excludes every experiment that discriminates competing rules — that is, every
   informative experiment. Under the narrower reading, **FOXO1 inhibition with
   secreted PRL as the primary functional prediction** becomes eligible: it is
   functional, it is three steps beyond the drug target, it is robust to rates,
   to initial conditions and to the Q1, Q2, INF and CAM families, and the FOX
   family it depends on is exactly what the experiment tests. The frozen
   prediction would be the default rule's: **PRL down**, with IGFBP-1 down as
   target engagement and a pre-specified equivalence margin for the alternative.
   This requires a wording decision from the PIs, not new work.

2. **Resolve CAM in Task 1.1 first.** The regimen comparison already in the
   funded plan (`REG_hormone_only_vs_supplemented`) separates the CAM variants
   robustly on functional readouts. Resolving it restores the Smoothened
   prediction's rule-robustness — but leaves it a *pathway-activity* prediction,
   so it still fails v10's functional requirement. This helps the model; it does
   not by itself produce an eligible WP2 candidate.

**Neither option is adopted here.** The proposal freezes the WP2 prediction at
the end of WP1 (milestone MS1), and both options depend on decisions and data
that do not yet exist.

## Agreement criteria and freezing

Unchanged from the previous draft and still unsigned: direction, effect size,
donor-level pairing, evaluability gates and the equivalence margin that any
predicted no-change requires. `pixi run endotwin-freeze` writes the record from
a clean tree; `endotwin/predictions/drafts/` holds the drafts, and nothing in
`endotwin/predictions/frozen/` is to be written before the first WP1 data exist.
