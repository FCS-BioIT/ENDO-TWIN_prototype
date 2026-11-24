# WP2 prospective prediction: selection workflow and current status

Status: **nothing is frozen, and nothing should be.** v10 selects the WP2
perturbation *after* WP1 model refinement, so the job now is to show a credible
route to an eligible prediction, not to declare one.

Reassessed 2026-11-24 against **`MemoriaCT-individual_Digital Twin_v10`** and
`endotwin-v0.3.0`.

Two things changed in this revision. The Smoothened draft is **withdrawn** (§3).
And the earlier conclusion that "no candidate meets the requirements" is
**narrowed**: it was true of the two drafted candidates, but those two were never
the candidate space. An exhaustive screen (§4) shows the space is larger than
the drafts, and names perturbations neither draft considered.

## 1. What v10 requires (SO2, Task 2.1)

A perturbation

- **not used in model development or calibration**;
- "resulting in an informative downstream **functional** response **beyond its
  direct molecular target**";
- whose "primary functional prediction must be robust to uncertainties in
  Boolean rules, transition rates and initial conditions";
- frozen before testing, with a literature-informed comparator for the same
  primary readout defined **without** MaBoSS;
- tested in five independent G1 donors, one control and one perturbed chip
  each. The donor is the unit, and **a non-significant difference never
  confirms a predicted no-change**.

### Functional response, pathway activity, target engagement

| | Meaning | Examples here |
|---|---|---|
| **Target engagement** | the drug reached and inhibited its target | GLI1/PTCH1 mRNA after a Smoothened antagonist; nuclear FOXO1 after a FOXO1 inhibitor |
| **Pathway activity** | a signalling intermediate moved | pSMAD1/5/8, WNT4, NR2F2, phospho-ERK1/2 |
| **Functional response** | the tissue did something different | decidualization (PRL, IGFBP-1), epithelial proliferation (Ki67/EdU), secretory differentiation (PAEP) |

**pSMAD1/5/8 is pathway activity.** Under v10 it cannot be the primary
prediction, whatever its robustness.

## 2. An interpretation question that should be settled explicitly

v10 says the primary functional prediction "must be robust to uncertainties in
Boolean rules, transition rates and initial conditions."

Read literally, that **excludes every hypothesis-discriminating experiment**: an
experiment that discriminates competing rules predicts *different* things under
those rules, so its prediction is by construction not rule-invariant. Taken
strictly, the criterion would admit only predictions the model makes the same
way regardless of which open question is true — which tends to select the
uninformative.

The reading that makes the clause do useful work is: **robust to the
uncertainties that are not under test.** A prediction may depend on the family
the experiment is designed to resolve, provided it is stable against all the
others, against rates and against initial conditions.

This document does **not** assume either reading. It reports both columns
separately in §4 and §5, so the choice stays visible. **It is a decision for the
PIs and, if useful, for the evaluating panel — not one to settle by silently
picking the convenient interpretation.**

## 3. The two drafted candidates

### Smoothened inhibition, hormone-only regimen — **withdrawn**

| Criterion | Assessment |
|---|---|
| Primary functional prediction | **None.** Every functional readout is `no_change` under both CAM variants |
| Target engagement | GLI1/PTCH1 mRNA — available and appropriate |
| Downstream pathway activity | pSMAD1/5/8, NR2F2, BMP2 — but these are pathway, not function |
| Independent of development perturbations | Yes |
| Robust to uncertain rules | **No.** pSMAD1/5/8 falls under `CAM_exogenous_only`, unchanged under `CAM_hormone_autocrine`, because endogenous PKA then supplies BMP2 through `E2-28` |
| Robust to rates and initial conditions | Yes — the network is acyclic, so fixed points depend on neither |
| Experimentally feasible | Yes |
| Beyond the direct target | Only `S_NR2F2` survives both CAM variants, and it is in the **same alias class** as `S_HH_SIGNALING`, so it is target engagement under another name |

Disqualified on the functional criterion alone, and separately not rule-robust.

### FOXO1 inhibition, supplemented regimen

| Criterion | Assessment |
|---|---|
| Primary functional prediction | IGFBP-1 down — robust in all 48 scenarios |
| Target engagement | nuclear FOXO1 by immunofluorescence |
| Independent of development perturbations | Yes |
| Robust to uncertain rules | IGFBP-1 yes; **PRL no** (down under `FOX_prl_foxo1_dependent`, unchanged under `FOX_prl_foxo1_independent`) |
| Robust to rates and initial conditions | Yes |
| Experimentally feasible | Yes — both readouts are existing outlet ELISAs |
| Beyond the direct target | **IGFBP-1, no**: `E2-44` has FOXO1 binding the IGFBP1 promoter. **PRL, yes** (FOXO1 → IRF4 → PRL) |

Under the strict reading it is ineligible. Under the "uncertainties not under
test" reading, **PRL as primary** is eligible and the experiment also resolves
the FOX family.

## 4. The screen: the candidate space is not two

`pixi run endotwin-wp2-screen` enumerates **every** single-node perturbation the
network can express — each of the 32 internal nodes pinned ON and pinned OFF —
under both regimens, across all 48 scenarios, and records what each does to the
six functional readouts. Output:
[`wp2_candidate_screen.tsv`](../endotwin/results/endotwin-v0.3.0/wp2_candidate_screen.tsv).

It is exact, not sampled: the network is acyclic, so each input assignment has
one fixed point. That settles two of v10's three robustness requirements by
construction — **fixed points cannot depend on transition rates or on initial
conditions** — and enumerating all scenarios settles the third.

Under the supplemented regimen, after removing perturbations whose "effect" is
on the readout itself (pinning `X_PRL`, or a gene pinned against its own
secreted pool), **eight** perturbations have a robust functional effect:

| Perturbation | Robust functional effect | Status for WP2 |
|---|---|---|
| `S_IL1_SIGNALING=1`, `S_JNK=1` | decidualization, PRL, IGFBP-1 down | WP3 — not withheld |
| `S_PGR=0` | decidualization, PRL, IGFBP-1 down | the progestin stimulus itself |
| `S_FOXO1=0` | IGFBP-1 down | the drafted FOXO1 candidate |
| `S_CEBPB=0` | decidualization, PRL, IGFBP-1 down | **not previously considered** |
| `S_PKA=0` | decidualization, PRL, IGFBP-1 down | **not previously considered** |
| `E_ESR1=0` | PAEP down | **not previously considered** |
| `E_PGR=0` | PAEP down | **not previously considered** |

### The shape worth noting: compartment-restricted knockdown

`E_PGR=0` — epithelial PGR knocked down, stroma untouched — is the only entry
with all three of the following at once, and it illustrates what the workflow
should be looking for:

- **robust primary**: PAEP down in all 48 scenarios, measured by an outlet ELISA
  already in the plan;
- **cross-compartment specificity**: stromal decidualization and PRL predicted
  **unchanged**, which in a co-culture exchanging ligands is a real claim rather
  than a tautology;
- **a discriminating secondary in the same experiment**: Ki67 **up** under
  `Q2_epithelial_autonomous`, unchanged under both relay variants.

It also breaks an alias class. `IN_PROGESTIN`, `E_PGR`, `E_IHH`, `X_IHH`,
`S_PGR` and `S_HAND2` are indistinguishable by any change of the *medium*;
only a compartment-restricted perturbation separates them, which is exactly what
`docs/README.md` has long listed as a limitation. The funded plan already
contains one compartment-restricted knockdown (stromal HAND2, Task 1.4), so the
technique is not new to the project.

**This is not a selection, and it is not eligible as it stands.** Open
questions, none of which the model can answer: whether epithelial-restricted
siRNA delivery is reliable in ADOC; whether knocking down the receptor for the
differentiating stimulus counts as "withheld" rather than as part of model
development; and whether PAEP loss after PGR knockdown clears the "beyond an
obvious consequence" bar. Those are experimental and editorial judgements.

## 5. Is the model structurally incapable of a functional prediction?

Partly, and the reason is worth stating because it bounds every candidate.

The functional readouts **saturate**:

- under the **supplemented** regimen `IN_cAMP` is ON, so PKA, C/EBPβ and the
  cAMP arm of BMP2 are all held up; removing an upstream signal changes no
  functional output because the reagent backs it up;
- under **hormone-only** with `CAM_exogenous_only` every stromal functional
  readout is already at **0**, so nothing can fall further;
- under hormone-only with `CAM_hormone_autocrine` they are all at **1**.

So a perturbation moves a functional readout only if it sits on the *last*
unsaturated step, which is why the screen's survivors cluster on `S_PKA`,
`S_CEBPB` and the epithelial receptors. This is a property of a Boolean model
with a saturating reagent in the medium, not a defect to be fixed by adding
mechanism.

**Finite-time predictions do not rescue this.** A perturbation could in
principle show a transient difference that the fixed point hides, and the engine
can produce one. But the size and even the existence of that difference is set
by transition rates that are not calibrated, and MaBoSS time is not experimental
time. A WP2 primary prediction resting on a transient would be resting on a free
parameter. Transients remain useful as *secondary*, hypothesis-generating
observations — the HAND2 relay delay in `docs/README.md` is one — and must not
be frozen as primary.

## 6. The candidate-selection workflow

What WP1 hands over, and how a candidate becomes a frozen prediction.

**Established now**
- The exhaustive single-perturbation screen, reproducible by one command.
- Which hypothesis families the funded arms separate: 4 of 5 structurally;
  `FOX` only by an unfunded candidate ([verification report](../endotwin/results/endotwin-v0.3.0/verification_report.md)).
- That fixed points are rate- and initial-condition-independent, so two of the
  three robustness criteria are satisfied by construction.

**What WP1 must resolve first**
1. **The regimen** (Task 1.1). Supplemented and hormone-only have different
   saturation, so they have different candidate sets. This also resolves `CAM`.
2. **The development-donor list**, so "withheld" can be checked rather than
   asserted.
3. **The model version**, frozen after the Task 1.4 perturbations.

**Screening, once those are fixed**
4. Re-run `pixi run endotwin-wp2-screen` on the frozen version and regimen.
5. Drop perturbations used in WP1/WP3, and those whose "effect" is on the
   readout itself.
6. Keep those with a **functional** primary that is robust across scenarios
   (strict reading) or across all families except the one under test
   (the §2 reading) — recording which reading was used.
7. Drop those with no feasible reagent or delivery route in ADOC, and those
   lacking a target-engagement readout.
8. For survivors, check the prediction is not simply the direct consequence of
   inhibiting the target, and that a **literature-informed comparator** can be
   stated for the same readout without MaBoSS.

**Freezing**
9. Write the spec from `endotwin/predictions/templates/`, check it with
   `pixi run endotwin-freeze --check <spec>`, then freeze from a clean,
   committed tree with `pixi run endotwin-freeze`. The record pins model
   version, hashes, readouts, directions, agreement criteria and the
   development-donor exclusions. Never edit a frozen record.

**If nothing qualifies**
v10 anticipates this: "if no defensible prediction is possible, this will be
recorded." That record is the honest outcome and should be made as such, with
the screen output as evidence. The fallbacks, in order of preference, are to
adopt the §2 reading and use a hypothesis-discriminating prediction; to accept a
pathway-activity primary with the functional readout as secondary, stating
plainly that this is weaker than v10 asks for; or to report that the model's
saturation structure prevents an eligible prediction at the frozen version. The
one unacceptable course is changing rules to manufacture a candidate.

## 7. Agreement criteria

Unchanged and still unsigned: direction, effect size, donor-level pairing,
evaluability gates, and the equivalence margin that any predicted no-change
requires. `endotwin/predictions/drafts/` holds the two drafts; nothing in
`endotwin/predictions/frozen/` is to be written before the first WP1 data exist.
