# ENDO-TWIN — reviewer guide

Evidence, predictions and reproducibility, in about three minutes. Every claim
below links to the file that supports it. Where something has not been done,
this page says so.

## 1. The project and its questions

ENDO-TWIN is a mechanistic, stochastic Boolean (MaBoSS) model of how ovarian
hormones coordinate the epithelium and the stroma of the human endometrium,
built to be tested prospectively in ADOC, an endometrium-on-chip with the two
compartments physically separated. Two questions drive it:

- **Q1** — does stromal decidualisation *require* BMP/SMAD signalling through
  WNT4, or is progesterone receptor signalling sufficient?
- **Q2** — does progesterone suppress epithelial proliferation through a
  *stromal* paracrine relay (the HAND2 route), or inside the epithelium itself?

Both have credible literature on each side. The model's purpose is to turn that
disagreement into experiments that distinguish the alternatives, rather than to
produce one more plausible network.

## 2. What exists today

`endotwin-v0.3.0`: **40 nodes**, **49 regulatory dependencies** (44 activating,
5 inhibiting), across **four compartments** — culture medium, epithelium, the
shared extracellular space, and stroma. Compartments communicate only through
ligand pools crossing the chip membrane.

Open questions are encoded as **5 hypothesis families** with **11 alternative
rules**, giving **48 scenarios** that are all executable. The repository
computes exact fixed points for every scenario, confirms them against
stochastic simulation, runs rate-sensitivity ensembles, and renders figures.

**This is not the historical prototype.** An earlier, private model of the same
group addressed embryo adhesion; its networks and analyses remain here as
clearly-marked legacy material under `models/` and `docs/legacy/`, and are not
part of ENDO-TWIN. The derivation is documented in [`docs/ORIGIN.md`](docs/ORIGIN.md).

## 3. Evidence you can check

| Claim | Evidence | Reproduce / inspect |
|---|---|---|
| An executable network exists | MaBoSS source, 40 nodes | [`network.bnd`](endotwin/models/endotwin-v0.3.0/network.bnd) |
| Competing hypotheses are encoded, not chosen | 11 variants in 5 families, each with its hypothesis and discriminating readouts | [`rule_variants.tsv`](endotwin/models/endotwin-v0.3.0/rule_variants.tsv) |
| Every edge carries graded evidence | class, mechanism, references, stated assumption per edge | [`edges.tsv`](endotwin/models/endotwin-v0.3.0/edges.tsv), [`references.tsv`](endotwin/evidence/references.tsv) |
| Specific experiments separate specific hypotheses | exact directions for every comparison × scenario | [`discrimination.tsv`](endotwin/results/endotwin-v0.3.0/discrimination.tsv) |
| Conclusions survive rate uncertainty | 5,670 of 5,670 predicted directions unchanged under 30 random rate sets | [`rate_sensitivity.tsv`](endotwin/results/endotwin-v0.3.0/rate_sensitivity.tsv) |
| Simulation matches exact computation | 1,680 phase records, worst deviation 0.0005 | [`maboss_confirmation.tsv`](endotwin/results/endotwin-v0.3.0/maboss_confirmation.tsv) |
| The whole thing is audited automatically | 2,613 tests, 0 failed, 63 skipped (commit `TESTED_COMMIT`) | [`verification_report.md`](endotwin/results/endotwin-v0.3.0/verification_report.md), [`tests/`](tests/) |
| Candidate WP2 perturbations are screened exhaustively | all 32 internal nodes × 2 states × 48 scenarios | [`wp2_candidate_screen.tsv`](endotwin/results/endotwin-v0.3.0/wp2_candidate_screen.tsv) |

## 4. Falsifiable predictions

**Q1 — BMP dependence.** Competing explanations: decidualisation requires
BMP/SMAD through WNT4, or progesterone receptor signalling suffices.
Perturbation: BMP type-I receptor inhibitor during differentiation. Primary
functional readout: secreted PRL and IGFBP-1. Discriminating result: both rules
lose pSMAD1/5/8, but **only the BMP-required rule loses PRL and IGFBP-1**.
Limitation: pSMAD1/5/8 is needed alongside, to show the inhibitor engaged its
target.

**Q2 — stromal control of proliferation.** Competing explanations: a stromal
paracrine relay, or an epithelium-autonomous route. Perturbation: stromal HAND2
knockdown, or blocking the paracrine mitogen **during E2 priming**. Primary
functional readout: epithelial Ki67/EdU. Discriminating result: proliferation
**rises** after HAND2 knockdown under the relay rule and is unchanged under the
autonomous rule. Limitation: the paracrine block is only informative during
priming — applied later, HAND2 already holds the mitogen off.

## 5. Computational verification is not biological validation

**Demonstrated.** The rules are executable and their fixed points computable
exactly; results regenerate reproducibly from committed inputs with recorded
hashes, seeds and trajectory counts; structural and sensitivity analyses exist;
and the encoded hypotheses do generate distinguishable predictions under the
stated assumptions.

**Not demonstrated.** No calibration against WP1 data — none exists yet. No
prospective predictive accuracy. No generalisation across donors. No functional
rescue in patient-derived endometriosis models. **Nothing in this repository is
experimental validation of the biology**, and no prediction has been frozen or
evaluated.

## 6. Reproducing the main results

```bash
pixi install                      # linux-64; pixi.lock pins Python 3.12, MaBoSS 0.8.15
pixi run endotwin-smoke           # clean-clone check, ~1 min, needs no private data
pixi run endotwin-test            # 140 mainline tests, ~35 s
pixi run endotwin-all             # every result, figure and the verification report
```

Outputs land in `endotwin/results/endotwin-v0.3.0/` (predictions, discrimination,
sensitivity, verification report) and `docs/assets/endotwin/` (figures). The
complete suite, `pixi run test`, additionally runs legacy prototype tests; 63 of
them skip because they need the prototype's Git history, which this repository
deliberately does not carry ([`docs/software_verification.md`](docs/software_verification.md)).

## 7. Current limitations

- **No calibration or experimental validation.** Everything is a conditional
  model prediction.
- **Regulatory uncertainty is explicit, not resolved** — that is what the five
  hypothesis families are.
- **cAMP sourcing and timescale.** Whether hormone exposure alone reaches PKA is
  an open family (CAM); the model cannot represent the acute-versus-extended
  distinction the evidence turns on, because MaBoSS time is dimensionless.
- **XAV939 is in the regimen but unmodelled.** The model is *silent* about it,
  which is not a prediction that it does nothing.
- **No WP2 candidate is eligible yet**, and the selection workflow — including
  an interpretation question for the panel — is in
  [`docs/wp2_prediction_selection.md`](docs/wp2_prediction_selection.md).

## 8. Relation to the funded work plan

**WP1** uses the discrimination table and the RNA/protein readout map to choose
which perturbations to run, and the rule variants to interpret them. **WP2** uses
the exhaustive candidate screen and the prediction-freezing machinery, with a
donor-leakage guard. **WP3** uses the IL-1β hypothesis family. **WP4** uses
perturbation screening with a G2-only selection record. All four are *supported*
by what is here; none has been *performed*. The computational resource
assessment is in [`docs/computational_resources.md`](docs/computational_resources.md).

Full documentation: [`docs/README.md`](docs/README.md).
