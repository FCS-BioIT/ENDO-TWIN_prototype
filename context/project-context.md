# Scientific context and model objective

## Long-term question

Can a mechanistic, donor-contextualized model of epithelial–stromal endometrial
receptivity identify non-hormonal intervention points that reduce stable embryo
adhesion while avoiding broad disruption of endometrial viability, barrier
function, and homeostasis?

This is a target-discovery question. The repository is not intended to make
clinical contraceptive recommendations, and a simulated perturbation is not
evidence of efficacy or safety.

## Phase-1 question

Can one baseline MaBoSS model reproduce, under matched experimental inputs:

1. the untreated versus hormone-induced epithelial and stromal molecular states;
2. the observed changes in PAEP, PRL, and IGFBP-1;
3. the hormone-associated IHH/COUP-TFII/BMP2 and SPP1 signaling programs; and
4. the condition-dependent probability of stable human blastocyst adhesion?

The starting abstraction is a coupled two-compartment system:

```text
hormone/environment inputs
          |
          v
 epithelial receptivity ---- paracrine signals ---- stromal decidualization
          |                                             |
          +---------------- adhesion permissiveness ----+
                                  |
                                  v
                    stable embryo adhesion readout
```

The embryo is initially represented as an adhesion challenge/readout, not as a
fully modeled third cell. That boundary can be revisited only if embryo-side
data support identifiable rules.

## Experimental context to reproduce

The source manuscript describes:

- untreated ADOC;
- a six-day hormone protocol: two days of 10 nM E2, then four days of 10 nM
  E2 + 1 µM MPA + 250 µM cAMP + 10 µM XAV939;
- the same hormone protocol followed by 24 hours of 10 µM mifepristone;
- stable adhesion defined by resistance to flushing.

Reported human embryo outcomes are 0/12 untreated, 9/19 hormone-treated, and
1/8 hormone-treated plus mifepristone. Mouse adhesion (23/44, 52%) is useful as
assay-supporting evidence but is not a species-matched quantitative target for
the human model.

The manuscript reports hormone-associated:

- epithelial PAEP/glycodelin-positive cells increasing from 0.9 ± 0.14% to
  15.81 ± 10.21%;
- ciliated cells decreasing from 18.67 ± 10.49% to 6.10 ± 5.35%;
- PAEP secretion increasing by day 6;
- stromal PRL and IGFBP-1 secretion increasing from undetectable at day 0 to
  higher levels at days 3 and 6;
- hormone-treated epithelial states expressing PAEP, SPP1, DPP4, CEACAM5/6,
  and secretoglobins;
- hormone-treated stroma expressing BMP2, DKK1, KDR, and IL11;
- epithelial IHH signaling toward stromal COUP-TFII/NR2F2 and BMP2, plus
  SPP1-mediated adhesion signaling.

These observations are registered in `evidence-register.tsv`; inclusion there
does not mean every marker becomes a node.

## How scRNA-seq will be used

The local RDS is an intermediate integrated object with 61,843 cells from
`SZ09`, `SZ10`, and `SZ25`, each represented under control and hormone-treated
conditions. Its barcodes match the corresponding public study samples, but it
is not the paper's final 28,212-cell annotated analysis object.

The scRNA-seq may:

- establish whether a candidate node is measured in the relevant compartment;
- prioritize nodes with donor-consistent condition changes;
- define epithelial/stromal state signatures;
- support pathway and ligand–receptor hypotheses for literature review; and
- later provide donor-level continuous inputs for personalization.

It may not, by itself:

- prove a regulatory edge or its sign;
- justify treating cells as independent biological replicates;
- turn dropout or missing values into OFF states;
- map normalized abundance directly to transition rates; or
- validate a model that was tuned to the same expression pattern.

Condition comparisons must be donor-aware. With three donors, personalization
and donor-stratified conclusions remain exploratory.

## Evidence separation

Each observation receives one of four roles:

1. **Construction:** establishes topology, rule sign, compartment, or phenotype
   definition.
2. **Calibration:** selects among pre-declared parameter or initial-state
   alternatives.
3. **Validation:** remains unseen during construction/calibration and tests a
   prediction.
4. **Context only:** supports interpretation but cannot adjudicate the model.

The preferred first split uses mechanistic literature and scRNA-seq programs for
construction, molecular secretion/state behavior for calibration, and the
mifepristone adhesion response as a held-out perturbational validation. If
mifepristone evidence is used to encode PGR antagonism, it can no longer serve
as independent validation; that decision must be recorded before fitting.

## Acceptance boundary for phase 1

Phase 1 is accepted only if:

- the model syntax and provenance contracts pass;
- untreated and hormone-treated states reproduce pre-registered qualitative
  molecular directions without condition-specific topology changes;
- simulated adhesion probabilities are stable across seeds and trajectory
  counts;
- the result is robust to plausible thresholds, rates, and uncertain rules;
- calibration and held-out validation evidence remain distinguishable;
- discrepancies, non-identifiability, and alternative rule sets are reported;
  and
- an independent scientific review finds no evidence leakage or unsupported
  mechanistic claim.

Matching 9/19 exactly is neither required nor sufficient. The model should
report uncertainty-aware agreement with the binomial observations and must not
be over-tuned to three small groups.

## Later personalization and target discovery

After phase 1, donor-level expression summaries may be mapped using a
PROFILE-like recipe. The least invasive mapping is preferred: initial-state
probabilities, then justified clamps, then calibrated rate modifiers. Topology
changes require separate evidence.

PROFILE_v2 is a reference implementation for graded node inhibition, not a
drop-in scientific validation layer. Candidate non-hormonal targets should be
ranked only if their simulated effects:

- reduce adhesion permissiveness across donors and model uncertainties;
- persist across plausible hormone contexts;
- spare pre-specified viability, barrier, and homeostatic readouts;
- have a mechanistically supported, accessible intervention point; and
- survive orthogonal experimental validation in ADOC.

SPP1–integrin adhesion, IHH/SMO signaling, and the epithelial–stromal BMP2 axis
are reasonable *hypothesis classes* for later screening because they appear in
the ADOC evidence. They are not validated targets or safety-qualified
contraceptive recommendations.
