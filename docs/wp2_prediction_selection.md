# WP2 prospective prediction: selection and draft

Status: **drafts ready, nothing frozen.** The proposal fixes the WP2 prediction
at the end of WP1 (Task 2.1, milestone MS1). Freezing now would lock in a model
that has not seen the WP1 data and an empty list of development donors. The
drafts below are therefore checked but not frozen.

## What the proposal asks for (SO2, Task 2.1)

- A perturbation **withheld from model development and calibration**.
- Chosen because the model predicts an **informative downstream response,
  beyond the expected effect on its direct molecular target**.
- That prediction must be **stable under sensitivity analysis of the uncertain
  rules, transition rates and initial conditions**.
- One **primary functional prediction** with its direction and agreement
  criteria, plus supporting secondary readouts, all fixed before testing.
- Five independent G1 donors, one control and one perturbed chip each; the donor
  is the unit. A non-significant difference never confirms a predicted
  no-change.

## Candidates

Excluded before scoring: BMP receptor inhibition and the paracrine perturbation
(WP1 Task 1.4, so used in development), IL-1β (WP3), the regimen comparison
(Task 1.1) and progestin withdrawal (no planned arm).

Screen over every comparison in `endotwin/config/protocols.yaml` and every
readout WP2 can measure, using the exact predictions for all 24 rule-variant
scenarios and the random-rate results (`endotwin/results/endotwin-v0.2.0/`):

| Candidate (comparison) | Stable predicted change | Beyond the direct target? | Verdict |
|---|---|---|---|
| Smoothened antagonist, hormone-only regimen (`HH_smo_inhibition_hormone_only`) | pSMAD1/5/8 down | Yes: reception → NR2F2 → BMP2 → secreted BMP2 → receptor activity | **Recommended** |
| FOXO1 inhibitor, supplemented regimen (`FOX_foxo1_inhibition`) | IGFBP-1 down; nuclear FOXO1 down | Weakly: IGFBP1 is a direct FOXO1 target gene. PRL changes only under one FOX rule | Alternative |
| Smoothened antagonist, supplemented regimen (`HH_smo_inhibition`) | none (cAMP backs BMP2 up) | Only no-change predictions | Not suitable as primary |

## Recommended draft: Smoothened inhibition under the hormone-only regimen

`endotwin/predictions/drafts/WP2-SMOI-HO-PSMAD.yaml`

| Readout | Role | Predicted direction |
|---|---|---|
| pSMAD1/5/8 (RO-PSMAD158) | primary | down |
| GLI1/PTCH1 mRNA (RO-RNA-GLI1) | target engagement | down |
| NR2F2 mRNA | secondary | down |
| BMP2 mRNA | secondary | down |
| Ki67 | secondary | no change (needs equivalence) |

Why: the model predicts that, without cAMP, stromal BMP2 depends on Hedgehog
reception through NR2F2, so blocking Smoothened removes BMP/SMAD activity four
steps downstream of the drug's target. The prediction is the same in all 24 rule
scenarios, under 30 random rate sets and from 5 random initial states (the
network is acyclic, so its fixed points cannot depend on the initial state).

What makes it a real test: the IHH–NR2F2–BMP2 edges are only topic-level in the
literature, and no human study shows that Hedgehog reception is needed for NR2F2
(the prototype's GAP-014). A failure would point to exactly those edges.

Conditions and risks:

- **It needs the hormone-only regimen.** Task 1.1 decides which regimen WP2 uses.
  The model also predicts no decidualisation without cAMP; if Task 1.1 shows
  otherwise, the model is revised and this prediction must be re-derived.
- The antagonist (compound and dose) must reach the stroma in the chip; target
  engagement is read by GLI1/PTCH1 transcripts.
- SMO inhibitors are not in the funded protocol; reagent cost is small.

## Alternative draft: FOXO1 inhibition

`endotwin/predictions/drafts/WP2-FOXO1I-IGFBP1.yaml`, for the case where WP2
keeps the published supplemented regimen. Primary IGFBP-1 down (stable in every
scenario); target engagement nuclear FOXO1; PRL is a secondary readout because
it separates the two FOX hypotheses (down if PRL needs FOXO1, unchanged if not).
It is weaker on the proposal's criterion: IGFBP-1 loss is the expected effect of
inhibiting FOXO1.

## Agreement criteria (proposed, to be signed off)

Donor-level effect = log2(perturbed / control) per readout. A predicted change is
concordant when at least 4 of the 5 donors are evaluable and at least 4 move
beyond 0.5 (about 1.4-fold) in the predicted direction; discordant when as many
move the other way; otherwise inconclusive. A predicted no-change is concordant
only if every evaluable donor stays within ±0.3. Comparisons that fail
viability, integrity or target-engagement criteria are not evaluable,
independently of the prediction (`src/endotwin/observations.py`).

## Eligibility check (run on the committed drafts)

`pixi run endotwin-freeze --check endotwin/predictions/drafts/<draft>.yaml`

| Draft | Rule variants (24 scenarios) | Rates (30 sets) | Initial conditions (5 states, acyclic) | Eligible |
|---|---|---|---|---|
| WP2-SMOI-HO-PSMAD | stable | stable | stable | yes |
| WP2-FOXO1I-IGFBP1 | stable | stable | stable | yes |

## Freezing at the end of WP1

1. Revise the model with the WP1 data if needed, and bump its version.
2. Copy the chosen draft, set `model_version`, fill `development_donors` with
   every WP1 donor code, and confirm the agreement criteria.
3. Commit, then run `pixi run endotwin-freeze <spec>` on a clean working tree.
   The tool refuses a WP2 record without development donors, re-runs the rule,
   rate and initial-condition checks, and writes an immutable record with a
   SHA-256 manifest under `endotwin/predictions/frozen/`.
4. Commit the record before any WP2 chip is run.
