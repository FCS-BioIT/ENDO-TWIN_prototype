# Prospective `dropout_e2` experiment — handoff to the experimental team

> **Generated file — do not edit.** Regenerate with `pixi run build-phase1b-closure`. The frozen text quoted in the next section is rendered from `docs/stage3_experiment_selection.md` itself, and the §5 decision table is copied cell for cell. The doses are cross-checked against `config/protocols.yaml`, and the band limits are recomputed from the canonical protein table. The handoff's own dose, day, compartment and replication statements are asserted to agree with the frozen quotes. The build fails if any of these diverge. The remaining prose is a restatement for the bench, and where it differs, the quotes and the addendum (`pre_run_analysis_addendum.tsv`) govern.

Frozen design: 2026-09-17. Pre-run analysis addendum: 2026-09-24, recorded before any prospective data exist. The frozen text is unchanged. The addendum only closes ambiguities in it.

## The frozen design, verbatim

Quoted from `docs/stage3_experiment_selection.md` by the generator. This is the frozen wording. Where the pre-run addenda say so it is superseded: the joint unit is now the source-pair block (SPB1), and the optional SPP1 assay is not exercised (SPP1X).

- (12) Days 2–6: **MPA 1 µM + cAMP 0.25 mM + XAV939 10 µM, E2 omitted.**
- (12) Days 0–2 unchanged: E2-only priming, as the current protocol runs it.
- (4) **Full cocktail** (E2 + MPA + cAMP + XAV939) — the ON reference band.
- (4) **E2-only, sampled at day 2** — the low reference band
- (4) **Pre-cocktail baseline PAEP.**
- (4) Existing assay, existing timepoint, one extra aliquot.
- (12) phase-contrast confluence imaging at days 2, 4 and 6 in **both** the epithelial and the stromal channel
- (12) Top outlet for PAEP, bottom outlet for IGFBP-1 and PRL, sampled at the existing day-3 and day-6 windows, with chip identity carried
- (12) PAEP, IGFBP-1 and PRL by the three existing ELISAs. **Nothing else.**
- (12) No surface CD98, no pSTAT3, no α-DG-N, no GLI1/PTCH1, no embryos, no attachment.
- (12) Three donors, one chip per donor per condition, plus a technical duplicate of the minus-E2 arm if capacity permits (§9.2).
- (12) Donor is the biological unit; chips are not independent replicates; no patient-level variance, confidence interval, paired-donor test or personalization claim may be derived.
- (9) It does not raise biological *n*
- (9) **ON** — the minus-E2 value lies in or above the full-cocktail band;
- (9) **OFF** — it lies in or below the E2-only band;
- (9) **indeterminate** — anything between, which is an admissible verdict and not a tie to be broken.
- (9) **The rule must never be fitted from the minus-E2 result**
- (4) (ii) the same three-level rule for IGFBP-1 against its own day-0 and day-6 bands
- (4) (iii) **IGFBP-1 is the stromal decision variable and PRL is corroborative, not a substitute.**
- (12) **PRL is corroborative and never decisive**
- (12) `PAEP OFF + IGFBP-1 ON` establishes **sustained E2 dependence of the epithelial secretory programme**, not the mechanism, because `SEC-e` predicts identically on both usable assays.

## What is being tested

Whether the epithelial secretory programme still needs E2 once the progestin cocktail is running. The model's competing rule classes predict different PAEP (top) × IGFBP-1 (bottom) patterns when E2 is omitted on days 2–6. **No embryo is needed.** This is a discrimination experiment. It is not a validation of the model, and it is not a clinical or patient-level test.

## Protocol

| | Days 0–2 | Days 2–6 |
|---|---|---|
| **Minus-E2 arm** | E2-only priming (10 nM E2), unchanged | **MPA 1 µM + cAMP 0.25 mM + XAV939 10 µM, E2 omitted** |
| **Full cocktail (comparator)** | E2-only priming (10 nM E2), unchanged | E2 10 nM + MPA 1 uM + cAMP 250 uM + XAV939 10 uM |

Nothing else changes: same chip, same flow rate, same medium base, same collection windows. Both arms run on the same source-pair blocks in the same run. Historical chips are never the comparator.

## Unit and replication

- **3 planned source-pair blocks.** A block is one identified epithelial source plus one identified stromal source. The full-cocktail and minus-E2 chips of a block MUST use the same epithelial and the same stromal source (SPB1).
- A block is **not** a patient or donor, and n = 3 independent biological donors is not asserted. A source reused across blocks is recorded, and then no independence claim is made.
- **A technical duplicate of the minus-E2 arm, in the same block, if material and chip capacity permit.** It never increases biological n and is never reported as if it did.
- **No patient-level variance, standard error, confidence interval, personalization or paired-patient claim** may be derived. Results are reported per source-pair block.

## Allocation (required before treatment)

Within each source-pair block, conditions are **randomly assigned** to physical chip IDs and positions, with the optional minus-E2 duplicate included in the same step. Processing order is randomised independently where operationally possible, or, where hardware prevents it, counterbalanced across blocks. The realised allocation is recorded in `prospective_allocation_manifest_template.tsv` **before treatment starts**, and no treatment begins until it is complete (AL1). The manifest records the block, epithelial source, stromal source, chip, condition, duplicate link, position, processing order, randomisation record, time and person, and three methods. `allocation_method` must be `randomized`: condition assignment is always randomised. `position_allocation_method` and `order_allocation_method` are `randomized`, or `counterbalanced_hardware_constraint` only when hardware prevents randomising them, and counterbalancing must vary the within-block layout across blocks. Positions and processing-order slots are unique in the run. Until real IDs exist it reads `REQUIRED_PRE_RUN_MANIFEST`, which is an operational prerequisite, not an open interpretation question.

**Assay metadata (required before classification).** `prospective_assay_metadata_template.tsv` must carry a documented detection limit for each of PAEP, IGFBP-1 and PRL on this run. Without one, nothing is classified (MS1). The historical 5 pg/mL IGFBP-1 figure is manuscript prose and is not used.

## Sampling

| Sample | Compartment | Assay | When | Role |
|---|---|---|---|---|
| every chip | top outlet | PAEP | **day 0**, before E2 priming (one extra aliquot; RQ2) | referent for the model's E_PAEP = 0; descriptive, gates no call |
| every chip | bottom outlet | IGFBP-1, PRL | day 0 (existing window) | baseline; descriptive, gates no call (RQ4) |
| every chip | top outlet | PAEP | day 2 (end of E2-only priming) | contemporaneous E2-only (low) reference |
| every chip | top outlet | PAEP | day 3, **day 6** | day 6 decides, day 3 is secondary |
| every chip | bottom outlet | IGFBP-1, PRL | day 3, **day 6** | day 6 decides, day 3 is secondary; carry chip identity so day 3/day 6 are paired |
| every chip | both channels | phase-contrast confluence imaging | days 2, 4, 6 | compartment integrity, epithelial **and** stromal |

**Assays: PAEP, IGFBP-1, PRL by the existing ELISAs, plus phase-contrast integrity imaging. Nothing else.** The optional SPP1 assay is not exercised in this run (SPP1X). No CD98, pSTAT3, α-DG-N, GLI1/PTCH1, embryos or attachment.

## Pre-registered interpretation (fixed before the run)

Applied per source-pair block, **in this order**. A failure at an earlier step stops every later step.

1. technical validity
2. compartment integrity
3. contemporaneous expected-state confirmation
4. molecular ordinal call
5. SEC-class mapping

**1. Technical validity and measurement state (MS1).** Only an `observed` value at or above the documented prospective assay limit is classified. `no_detectable_secretion` → `INDETERMINATE_ZERO`; `below_detection` → `INDETERMINATE_BELOW_DETECTION`, **never OFF**; `missing` → `MISSING`; an `observed` record below the limit is rejected as inconsistent. No LOD/2 or other value is imputed. A documented technical failure is `MISSING/TECHNICAL_FAILURE`, never ON, OFF or indeterminate. There is no averaging over blocks and no inference from PRL. Without an already documented pre-run technical-repeat SOP, a failed assay or chip stays failed. A measurement is never repeated because its value is inconvenient; if a legitimate repeat happens, the original record and the reason for the repeat are both kept (G4R). With duplicates: concordant calls are kept; one failure plus one valid replicate keeps the valid one (the loss is noted); two valid but different calls give `TECHNICAL_DISCORDANCE`. Duplicates are never averaged and never raise biological n.

**2. Compartment integrity.** From the day-2/4/6 images, each channel independently gets `INTACT`, `COMPROMISED` or `INDETERMINATE`. **These calls are locked before any PAEP/IGFBP-1/PRL value is revealed to the person assigning biological calls** (G3R). Condition identity need not be blinded if that is impossible, but secretion results must not influence the integrity judgement. Record the image id, channel, day, call, adjudicator and timestamp/version. `COMPROMISED` means clear monolayer loss, detachment or denudation, enough that a change in secretion could come from losing the producing cells. If the relevant channel is COMPROMISED or INDETERMINATE at day 6, its molecular result is `integrity_invalid` and day 3 cannot rescue it. **Loss of epithelium mimics PAEP OFF, and loss of stroma mimics IGFBP-1 OFF; neither is ever read as biological OFF.** A validated quantitative confluence SOP may replace this only through another documented pre-run addendum, before assay values are unblinded.

**3. Contemporaneous expected-state confirmation (one-sided, RQ5).** Each required reference must show the state it exists to show. **Boundaries are never refitted, and a value beyond the old historical extreme on the expected side still confirms.**

- Full-cocktail PAEP, day 6: ≥ 178,072.464 pg/mL → `CONTROL_ON_CONFIRMED`; otherwise `CONTROL_STATE_NOT_CONFIRMED`.
- E2-only PAEP, day 2 (the minus-E2 chip's own sample): ≤ 25,469.5652 pg/mL → `CONTROL_LOW_CONFIRMED`; otherwise `CONTROL_STATE_NOT_CONFIRMED`.
- Full-cocktail IGFBP-1, day 6: exact zero → `CONTROL_STATE_NOT_CONFIRMED` (raw zero kept; not a technical failure without independent QC evidence; PRL cannot rescue it); ≥ 8,118.142 pg/mL → `CONTROL_ON_CONFIRMED`; 0 < x < 8,118.142 → `CONTROL_STATE_NOT_CONFIRMED`.

A reference that is not confirmed invalidates the corresponding minus-E2 call **for that source-pair block only**: the PAEP references gate PAEP, and the IGFBP-1 reference gates the stromal call. There is no majority rule, no 2-of-3 block rule, no run-level average and no systematic-failure threshold. Day-0 IGFBP-1 and the day-0 PAEP baseline are descriptive and never gate (RQ2, RQ4). Day-3 control values never gate (G7).

**4. Molecular calls (day 6).**

- **PAEP (top):** ≥ 178,072.464 → ON; ≤ 25,469.5652 → OFF; strictly between → `graded_not_boolean`. The intermediate result is admissible, not a tie to be broken.
- **IGFBP-1 (bottom), the stromal decision variable (RQ6):** exact zero → `INDETERMINATE_ZERO` (not graded); 0 < x ≤ 551.2605 (IGFBP1_OFF_UPPER, the largest non-zero day-0 value) → OFF; between → `graded_not_boolean`; ≥ 8,118.142 (IGFBP1_ON_LOWER, the smallest non-zero day-6 value) → ON. So a positive value below the historical day-0 minimum is OFF, and a value above the historical day-6 maximum is ON: the historical ranges are not symmetric acceptance bands.
- **PRL:** reported alongside, **never decisive**. It has no band and no weight, and it cannot rescue an uninterpretable IGFBP-1 or an unconfirmed reference. PRL/IGFBP-1 disagreement is recorded as a finding.
- **Day 3** is secondary. It cannot override or rescue a day-6 call, and disagreement between day 3 and day 6 is reported.

`graded_not_boolean` arises only from a valid level-4 intermediate value. Every QC indeterminacy (`MISSING/TECHNICAL_FAILURE`, `MISSING`, `INDETERMINATE_BELOW_DETECTION`, `integrity_invalid`, `CONTROL_STATE_NOT_CONFIRMED`, `INDETERMINATE_ZERO`, `TECHNICAL_DISCORDANCE`) is `NO_CLASS_ASSIGNMENT` with its reason and never maps to a SEC class (RQ3).

**5. What each source-pair block's day-6 pattern supports.** The predictions are frozen decision table C, and the build checks that each row's classes match it.

The first four columns are frozen §5, verbatim. The last column is what the pre-run addendum adds; it rewrites nothing.

| PAEP (top) | IGFBP-1 (bottom) | Supported | Model action (frozen) | Pre-run addendum |
|---|---|---|---|---|
| **OFF** | **ON** | `SEC-a` **or** `SEC-e` — the arm cannot tell them apart | **Sustained E2 dependence of the epithelial secretory programme is established; the mechanism is not.** What the result licenses is the claim that continued E2 is required to maintain that programme under this protocol while the stromal programme runs on. It does **not** establish that `IN_E2` is a direct Boolean conjunct with `E_PGR`: `SEC-e`, in which E2 acts only by maintaining epithelial PGR, predicts the identical PAEP and IGFBP-1 pattern, and the computation shows the two separate only at `E_IHH`, `E_PGR` and `S_NR2F2` — every one of them `no_assay`. So the committed rule is retained as the simplest expression of a dependence now demonstrated, not as a mechanism now proven, and the OM-001 threshold gains real evidence either way. |  |
| **ON** | **ON** | `SEC-b` or `SEC-c` | Concurrent E2 is not required. Propose `E_SECRETORY_STATE = E_PGR`. Which of the two is settled by the registered E2-only PAEP call, not by this arm — table C shows they predict identically here. Note the cost before adopting: the partition goes **35 → 34** distinct functions, because `E_SECRETORY_STATE` merges into the `E_PGR` class. The model becomes more correct and more collapsed at once, and the E2-priming phase then needs an explicit primed state it does not currently have. | G8: the registered E2-only PAEP call this row defers to does not exist. The result narrows to SEC-b OR SEC-c and establishes only what they share: concurrent E2 during days 2-6 is not required for the observed epithelial secretory output under this protocol. It does NOT distinguish SEC-b from SEC-c. |
| **OFF** | **OFF** | `SEC-d` | E2 is required in both compartments, which the model expresses nowhere. The action is **not** a secretory-state edit: it is an E2 dependence on `E_PGR` and `S_PGR`, for which the repository holds no evidence row, so the action is to open an evidence gap and seek the E2→PGR citation before encoding anything. Partition also 35 → 34. |  |
| **ON** | **OFF** | none | The fork as posed is wrong: E2 would be required stromally and not epithelially, which no class predicts and no rule in the model can produce. Action is to stop and re-pose the fork, not to patch a rule. |  |
| **indeterminate** in either channel | — | — | Record as `graded_not_boolean`. This is a model-**class** finding, not an identification: it says the input layer is dose-graded where the network is Boolean, and it belongs to the same future rate layer as the EPAC entry. Do not force a band call to avoid this outcome. | RQ3: `graded_not_boolean` applies ONLY to a valid level-4 value that lies between OFF and ON after every upstream QC level has passed. QC and measurement indeterminacies are NOT graded and carry no SEC-class inference: MISSING/TECHNICAL_FAILURE, integrity_invalid, CONTROL_STATE_NOT_CONFIRMED, INDETERMINATE_ZERO and TECHNICAL_DISCORDANCE. Each is recorded as NO_CLASS_ASSIGNMENT with its reason. |

The first row is the one to read carefully: **`PAEP OFF + IGFBP-1 ON` establishes sustained E2 dependence of the epithelial secretory programme, not the mechanism.** SEC-a (E2 as a direct conjunct) and SEC-e (E2 maintaining epithelial PGR) cannot be told apart on any usable assay.

The three source-pair blocks are reported **individually**. Disagreement between blocks is reported as disagreement and is never averaged into a class call.

## Pre-run decisions

Every interpretation gap found before the run has been decided by the owner (`pre_run_analysis_addendum.tsv`, rounds 1-3, all dated 2026-09-24). No pre-run question is open.

## After the data arrive

1. Ingest the raw values into a new, declared derived table. Nothing under `data/` is edited. **No band, rule or threshold is changed.**
2. Apply the five-step order per source-pair block and record every intermediate call, including every QC indeterminacy (technical failure, integrity_invalid, CONTROL_STATE_NOT_CONFIRMED, INDETERMINATE_ZERO, TECHNICAL_DISCORDANCE) and every graded_not_boolean result, with its reason.
3. Map each valid source-pair-block pattern to the table above. Record disagreement between blocks, and between day 3 and day 6, explicitly.
4. Re-evaluate the SEC fork and AC01 against those per-block outcomes, in a new unit.
5. Only then decide whether a new executable model version is licensed. This handoff does not prescribe which rule the data must produce.

Phase-1B status from the companion audit: **BLOCKED**. This experiment does not close Phase 1B on its own: it is construction and discrimination evidence, and it cannot also serve as the held-out validation.
