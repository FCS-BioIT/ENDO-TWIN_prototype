# Progesterone withdrawal after the hormone cocktail: model v0.5.1

**Model:** `adoc-literature-superset-v0.5.1` (the current adopted model), MaBoSS 0.8.15 (cmaboss).
**Status:** an exploratory simulation of the model's own dynamics. It is not a validation, and it is not a biological or clinical prediction.

## Protocol

| Phase | Inputs ON | Horizon |
|---|---|---|
| 1 `basal_maternal` | none | 25 |
| 2 `e2_primed_maternal` | E2 | 25 |
| 3 `hormone_treated_maternal` (the cocktail) | E2, progestin, cAMP, XAV939 | 25 |
| **4 withdrawal** | **E2, cAMP, XAV939, with progestin OFF** | 25 |
| 4 control, matched | E2, progestin, cAMP, XAV939 | 25 |
| 4 mifepristone, check arm | cocktail + mifepristone | 25 |

- **Phases 1–3** are the repository's declared lineage, run with the repo's own `run_protocol` and continuation code. Each phase runs at the converged horizon of 25, which is where the cocktail reaches its fixed point.
- **Phase 4** starts from the exact terminal joint state of the cocktail phase (16 joint states, and all 46 non-input nodes are carried over). Every change after t = 0 is therefore caused by the input switch.
- **Time** is MaBoSS relative time with every rate equal to 1. It has no mapping to hours or days.

### Estimators and their statistics

**A. Aggregate estimator.** 10 independent replicates, using seeds 1–10. Each replicate re-runs the whole lineage with 5,000 trajectories.
- The replicate is the independent unit.
- Intervals are t-intervals across the 10 replicates.
- No binomial standard error is used on MaBoSS node values, because they are dwell-time fractions (see `docs/maboss_estimator_semantics.md`).

**B. Per-trajectory estimator.** 2,000 single-trajectory MaBoSS runs (sample_count = 1, one seed per run), read at tick 0.01.
- Each run is one independent draw of the event sequence.
- Proportions get exact Clopper–Pearson 95% intervals.
- Medians and quantiles get bootstrap 95% intervals (4,000 resamples).
- Pairwise order tests are exact binomial tests against 0.5, Holm-corrected over the 666 node pairs.
- Every node switched **at most once** in every trajectory (0 reversals), so the cascade is monotone and a single "switch time" per node is well defined.

## 1. Final phenotype

The final phenotype is fully determined.

| Readout at t = 25 | Cocktail kept | Progesterone removed | Per-trajectory count (95% CP interval) |
|---|---|---|---|
| OUT_EPITHELIAL_RECEPTIVE | 1.000 | **0.000** | 0/2000 (≤ 0.18%) |
| OUT_STROMAL_DECIDUALIZED | 1.000 | **0.000** | 0/2000 (≤ 0.18%) |
| OUT_MATERNAL_ADHESION_COMPETENCE | 0.8195 | **0.000** | 0/2000 (≤ 0.18%) |
| OUT_STABLE_ADHESION (no embryo) | 0 | 0 | 0/2000 |
| E_ESTROGENIC_PROLIFERATION | 0.000 | **1.000** | 2000/2000 (≥ 99.82%) |
| X_ANTIADHESIVE_ROUTE | 0.000 | 0.199 | 397/2000 (18.1–21.7%) |

**The terminal state.** The withdrawal arm always reaches one attractor. In it:
- every progesterone-dependent node is OFF;
- the anti-receptive surface (MUC1 barrier, PODXL, full-length DAG1) is ON;
- the estrogenic proliferation branch is ON;
- S_PKA stays ON, because cAMP is still present.

**Replicate spread.** Across the 10 replicates, the spread of every OUT readout is exactly 0. That is what a deterministic fixed point looks like: the answer does not depend on the random stream. It does not mean the model is certain about biology.

**Paired changes versus the matched control** (same seed, same starting state):
- epithelial receptive −1.000;
- stromal decidualized −1.000;
- adhesion competence −0.8195, with 95% CI −0.8195 to −0.8194;
- estrogenic proliferation +1.000.

**The 19.9% anti-adhesive fraction is not a biological estimate.** It equals the prior on the latched placeholder relay `X_INTERFACE_ANTIADHESIVE_RELAY` (istate 0.2). The route switches on only in trajectories where that unidentified relay happens to be ON.

**Time to settle.** The per-trajectory time of the last switch has these quantiles, each with a bootstrap 95% CI:

| Quantile | Time | 95% CI |
|---|---|---|
| Median | 7.46 | 7.36–7.58 |
| 95th percentile | 11.6 | 11.3–11.9 |
| 99th percentile | 13.6 | 13.1–14.1 |

The maximum was 19.6. All 2,000 trajectories had settled before the horizon of 25 (Clopper–Pearson lower bound 99.8%).

**Withdrawal and mifepristone are identical in this model.** The largest absolute difference between the two final states is exactly 0. The rule `PGR = IN_PROGESTIN and not IN_MIFEPRISTONE` makes removing the agonist and adding the antagonist logically the same. The model therefore **cannot distinguish** progesterone withdrawal from receptor antagonism. Any experimental difference between the two would be evidence the current topology lacks.

## 2. The sequence

The table gives medians with bootstrap 95% CIs and the central 95% range across trajectories. D is the shortest regulatory path from `IN_PROGESTIN`, which is a lower bound on the number of events needed. The full table is in `switch_times.tsv`.

| Wave | Events | Median switch time (95% CI) | 2.5–97.5% range |
|---|---|---|---|
| 1. Receptor loss | E_PGR off, S_PGR off | 0.70 (0.65–0.74), 0.70 (0.65–0.75) | 0.02–3.7 |
| 2. Upstream programs | S_NR2F2 off; E_IHH off; **E_SECRETORY_STATE off**; **S_DECIDUALIZED off** | 1.45; 1.64; 1.68 (1.61–1.75); 1.70 (1.63–1.74) | 0.2–5.6 |
| 3. First phenotype lost | **OUT_MATERNAL_ADHESION_COMPETENCE off** | 2.42 (2.36–2.49) | 0.7–6.2 |
| 4. Broad secretory/decidual wave | S_BMP2, E_PAEP, E_LIF, E_HBEGF, E_SPP1, S_PRL, S_IGFBP1, S_SPP1, S_TAZ_ECM, mechanical-permissive ECM, **OUT_STROMAL_DECIDUALIZED** off; **E_MUC1_BARRIER ON, E_PODXL ON** | 2.52–2.71 | 0.6–7.3 |
| 5. Epithelial receptivity lost | E_RECEPTIVE_SURFACE off; **OUT_EPITHELIAL_RECEPTIVE off** | 3.02; 3.28 (3.20–3.36) | 1.0–7.7 |
| 6. Stromal brake released | **S_HAND2 off** | 3.48 (3.35–3.57) | 1.1–8.1 |
| 7. Adhesion machinery dismantled | GP130/STAT3, cleaved DAG1, SPP1 and redundant routes, αvβ3/5 integrin, luminal SPP1, CD98/CD9 off; **full-length DAG1 ON** | 3.6–4.7 | 1.1–10.4 |
| 8. Proliferative switch | **S_FGF_MITOGENIC ON** → **E_ESTROGENIC_PROLIFERATION ON** (last event) | 4.53; 5.53 (5.42–5.65) | 2.2–11.1 |

### Which orderings are statistically supported

The per-trajectory pairwise results are in `pairwise_precedence.tsv` and `fig4`. 507 of the 666 node pairs have an order that differs from a coin flip (Holm p < 0.05). The ones that matter:

**Enforced by the network in every trajectory (100%, 95% CP lower bound ≥ 99.8%):**
- S_PGR before S_DECIDUALIZED before OUT_STROMAL_DECIDUALIZED;
- E_PGR before E_SECRETORY_STATE before OUT_EPITHELIAL_RECEPTIVE;
- S_PGR before S_HAND2 before E_ESTROGENIC_PROLIFERATION.

The proliferative branch can only open after HAND2 falls, and HAND2 falls only after both stromal PGR and BMP2 are gone.

**The stroma loses its phenotype before the epithelium, as a bias rather than a rule.** OUT_STROMAL_DECIDUALIZED switches off before OUT_EPITHELIAL_RECEPTIVE in **59.8%** of trajectories (95% CI 57.6–61.9%, Holm p < 1e-10). The epithelial readout needs one extra step: it is gated through the receptive surface as well as PAEP.

**Adhesion competence is usually the first readout to go:**
- before epithelial receptivity in 62.7% (60.3–65.1%);
- before stromal decidualization in 55.8% (53.3–58.2%);
- both are significant after Holm correction.

It is an AND over both compartments and the ECM, so the first failure anywhere removes it.

**Not resolvable (consistent with 50%):**
- epithelial vs stromal PGR loss: 50.0% (47.8–52.2%);
- secretory-state vs decidual-core loss: 50.4% (48.2–52.6%);
- the PRL, IGFBP1 and PAEP drops relative to each other: about 50%;
- OUT_EPITHELIAL_RECEPTIVE loss vs HAND2 loss: 53% (Holm p = 1).

With equal rates, nodes at the same causal depth are exchangeable. Their order is noise, and the model makes no claim about it.

**Full orderings are almost never repeated.** The nine milestones in `fig4` appeared in 798 distinct orders across 2,000 trajectories, and the most common order occurred only 34 times (1.7%). The sequence is well defined as a partial order (the depth structure above), not as one fixed chain.

## Figures

- `fig1_cascade_heatmap.png`: P(ON) for every dynamic node over time (aggregate estimator), with rows ordered by median switch time.
- `fig2_milestone_timecourses.png`: key nodes, withdrawal (solid, with 95% band across replicates) against the matched control (dashed).
- `fig3_switch_time_intervals.png`: each node's switch time after progesterone removal (median, IQR and 2.5–97.5% range across trajectories).
  - Labels come from the model's `node_dictionary.tsv`.
  - `[ ]` gives the marker genes the repo reads a node through.
  - `= …` gives what a node's v0.5.1 rule combines, for nodes the repo marks as not RNA-measurable (composite phenotypes, adhesion routes, protein and extracellular states). Those nodes have no gene list of their own.
- `fig3b_switch_positions_normalized.png`: the same nodes on a per-trajectory normalised axis (0 = first switch, 1 = last switch; values in `switch_positions_normalized.tsv`).
  - The order inside every trajectory is kept.
  - Differences in speed between trajectories are removed.
  - Read the order from this figure, not from fig3.
- `fig4_milestone_precedence.png`: P(row event before column event) for the nine milestones.

## Causal consistency check

**The wide bars in fig3 are not order violations.** The script `causal_consistency_check.py` (whose replay is re-implemented in the analysis script) replays every trajectory against the Boolean rules:
- of 70,231 switch events, **0** occurred while the node's own rule did not call for them;
- every trajectory ends in a true fixed point;
- where a rule has one required input, the input switches first in 2,000 of 2,000 trajectories.

**Why the bars in fig3 are wide.** They are spreads across trajectories, and random waiting times accumulate along the cascade.

**The delay from trigger to switch was dropped as a figure.** Each switch's trigger event and delay are recorded in `switch_delays_after_trigger.tsv`. With every rate equal to 1, the delay has the same exponential distribution for every node by construction, so a plot of it carries no information about the network. It stays useful as a check: the measured median is 0.695, against a theoretical 0.693.

**Epithelial PGR loss can follow the proliferative switch; stromal PGR loss cannot.**
- Stromal PGR turns off after estrogenic proliferation starts in 0/2000 trajectories. The order is enforced through HAND2.
- Epithelial PGR does so in 31/2000 (1.6%). The v0.5.1 rule `E_ESTROGENIC_PROLIFERATION = IN_E2 and S_FGF_MITOGENIC and not S_HAND2` is driven entirely by the stroma and never reads epithelial PGR.

Any plot of distributions across trajectories (fig3, fig3b) shows some overlap between bars even where the order is enforced. Compare bars from different trajectories as distributions, not as orderings.

**Where a node switches before one of its inputs, the rule permits it.** Under an AND rule, a node turns off as soon as any one required input is lost. For example, `S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2` turns off when PGR is lost, so it goes before BMP2 in 70% of trajectories.

## Limits on interpretation

1. **The timing is topology, not kinetics.** Every rate is the MaBoSS default of 1. Switch times measure how many update steps separate a node from the progesterone input, not how fast the biology responds. Only the **order** is meaningful, and only where it is enforced or significantly biased as described above. Relative time must not be read as hours or days.
2. **These are statistics over simulated trajectories.** The probabilities are frequencies under stated rules and initial conditions. They are not clinical or experimental outcome probabilities, and no ADOC withdrawal data were used or compared.
3. **E2, cAMP and XAV939 stay ON.** The proliferative switch depends on E2 remaining present. XAV939 does not regulate any node in v0.5.1, so leaving it on changes nothing.
4. **Latched placeholder relays are priors, not measurements.** Any fraction tied to the `X_*_RELAY` placeholders (0.82 adhesion competence before withdrawal, 0.199 anti-adhesive route after it) reflects those relays' istate priors.
5. **A no-embryo arm only.** Stable adhesion is 0 by construction. An adhesion challenge after withdrawal was not run.

## Reproduce

```
pixi run -e default python -B output/progesterone_withdrawal/run_p4_withdrawal.py      # ~140 s
pixi run -e default python -B output/progesterone_withdrawal/analyze_p4_withdrawal.py
```

`run_metadata.json` records the model, config and condition-file hashes, the seeds, the trajectory counts, the ticks and the arm inputs. Everything here lives under `output/`, which is gitignored. No model, config or `data/` file was modified.
