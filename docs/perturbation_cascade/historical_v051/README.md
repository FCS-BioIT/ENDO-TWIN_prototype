# Historical progestin-withdrawal cascade (v0.5.1, 2026-09-28)

This directory preserves the only implementation of the original "When each
part of the network switches after progesterone is removed" analysis. It was
written and run on 2026-09-28 under the gitignored `output/progesterone_withdrawal/`
and was never committed. The files here are byte copies of the originals, and
`tests/unit/test_perturbation_cascade_docs.py` checks each one against the
original hash.
`ORIGINAL_SHA256SUMS.tsv` lists the SHA-256 of **every** file in that directory as
found on 2026-10-08, including the large regenerable tables that are not copied.

It is kept as a historical record, limitations included. The reusable tool that
replaces it is described in `../README.md`. Nothing here is a default of that tool.

## Contents

| file | what it is |
|---|---|
| `run_p4_withdrawal.py` | simulation: lineage, three phase-4 arms, 2,000 single-trajectory runs |
| `analyze_p4_withdrawal.py` | statistics and figures, reads the run outputs only |
| `causal_consistency_check.py` | replay of every switch against the Boolean rules |
| `REPORT.md` | the original write-up, unedited |
| `run_metadata.json`, `analysis_summary.json` | the original run record and summary |
| `switch_times.tsv`, `switch_positions_normalized.tsv` | per-node summaries behind fig3 / fig3b |
| `pairwise_precedence.tsv` | the original per-pair order table (read by `../stage_c/compare_historical.py`) |
| `per_trajectory_events.tsv` | the per-trajectory event table, byte-identical to the original |
| `aggregate_final_state.tsv`, `withdrawal_vs_control_delta.tsv`, `aggregate_timecourse.tsv` | the run's aggregate outputs, read by the analysis script |
| `redraw.sh` | redraws the figures from the files above without re-simulating, into the gitignored `output/progesterone_withdrawal_redraw/`, and checks the result against `ORIGINAL_SHA256SUMS.tsv` |
| (not committed) `fig3b_switch_positions_normalized.png` | the figure the reusable tool was asked to generalise. It is not tracked (no figure is; see `../README.md` §6); the original was kept in the gitignored `output/progesterone_withdrawal/`, a local copy that can be overwritten there (it was, by a higher-resolution redraw, on 2026-10-19); its hash and the pre-correction redraw described next are the record. `redraw.sh` reproduced it **byte for byte** (SHA-256 `c92f687d…`, its `ORIGINAL_SHA256SUMS.tsv` row), together with `switch_positions_normalized.tsv`, `switch_times.tsv`, `pairwise_precedence.tsv` and `analysis_summary.json`; verified 2026-10-08. Since the PCSK5 correction (`0735b73`) its marker labels read `E_PC6` through PCSK5, so on the current tree only the four tables are byte-identical; against the pre-correction component map fig3b is too (`../README.md` §6, checked 2026-10-19) |

## Exact semantics, as implemented

- **Model** `adoc-literature-superset-v0.5.1`, MaBoSS 0.8.15 (cmaboss).
- **Starting state** `basal_maternal → e2_primed_maternal → hormone_treated_maternal`,
  each phase run to horizon 25 (the converged horizon, not the declared
  durations), seed 1, 5,000 trajectories, using the protocols' own continuations.
  Phase 4 started from the cocktail's terminal joint state distribution (16 joint
  states) carrying **46 nodes**: all 45 non-input nodes plus the undeclared input
  `IN_HAND2_LOSS` (see the erratum) (`memory_node_policy="all_non_inputs"`),
  not the protocol's registered `extended_maternal_joint` policy.
- **Perturbation** `IN_PROGESTIN → FALSE`; E2, cAMP and XAV939 stay ON. The protocol
  encodes 1 µM MPA, so the figure title's "progesterone" is a mislabel: it is
  removal of the progestin input. In v0.5.1 only `E_PGR` and `S_PGR` read it.
- **Switch** the first departure from the node's t = 0 state, reconstructed from a
  single-trajectory tick-occupancy table at tick 0.01 with sub-tick interpolation.
- **Repeated switches** counted, but the analysis asserts there are none and aborts
  otherwise (none occurred).
- **Never-switching** trajectories are dropped from a node's distribution; the 9
  nodes that never switch are absent from the figure.
- **x-axis of fig3b** event **rank**, not time: `(rank − 1) / (m − 1)` with `m` the
  number of nodes that switched in that trajectory (33–37), ties broken by column
  order.
- **Direction** one per node, taken from the first trajectory where it switched.
- **Seeds** 2,000 runs of `sample_count = 1`, consecutive seeds 100001–102000, all
  from the seed-1 continuation. Consecutive seeds draw stratified, not
  independent, initial states (`docs/maboss_estimator_semantics.md`, addendum).

## Erratum in the preserved report

`REPORT.md` is kept byte-identical, so its errors stay in it. It says that "all
46 non-input nodes are carried". 46 nodes were carried, but not all are
non-input: the v0.5.1 network has 59 nodes, 14 of them `IN_*` inputs, so 45 are
non-input, and the 46th carried node is the input `IN_HAND2_LOSS`. The
`hormone_treated_maternal` step does not declare it (`run_metadata.json →
arm_inputs`), so it was carried at its terminal value, OFF, instead of being
forced; it is OFF in every archived trajectory and never switches. The archived
events cover these 46 nodes.

A second error: `REPORT.md` says the withdrawal arm "always reaches one
attractor". The archived final states contain **16 distinct terminal states**.
They agree on every node except the four latched relays
(`X_INTERFACE_ANTIADHESIVE_RELAY`, `X_INTERFACE_REDUNDANT_RELAY`,
`X_INTERFACE_SPP1_RELAY`, `X_MECHANICAL_STRESS_RELAY`), which keep their drawn
priors, and `X_ANTIADHESIVE_ROUTE`, which follows the anti-adhesive relay. So the
statement holds for the nodes the relays do not set; the terminal state as a
whole depends on the relay priors (the report's own 19.9 % anti-adhesive
fraction is that dependence).

A third error: `REPORT.md` §B calls each run "one independent draw" and gives
Clopper–Pearson intervals, bootstrap intervals and Holm-corrected exact
binomial order tests on that basis. The runs used consecutive seeds
100001–102000, which draw stratified, not independent, initial states
(`docs/maboss_estimator_semantics.md`, addendum), and successive first-event
times under consecutive seeds are lag-correlated (−0.088 at lag 1 over 1,500
seeds, `../README.md`, Stage A). So
the report's intervals, its bootstrap CIs and its claim that 507 of the 666
node pairs have an order that differs from a coin flip (Holm p < 0.05) are not
valid as stated: their coverage and error rates were not established. The
frequencies, medians and orderings themselves are descriptive and stand as
descriptions of these 2,000 runs. The reusable tool draws i.i.d. starting
states and spread seeds instead; it still records that the event streams are
not proven independent (`metadata.json → simulation.independence`).

## Known limitations (measured 2026-10-07 on the archived events)

- Within a response wave the plotted order is not resolved: five nodes tie at a
  median rank position of 0.441, and `E_LIF` moves ten places between rank and
  normalised-time axes. The broad wave order is stable (Spearman 0.95 between
  the rank, normalised-time and absolute-time medians).
- Rank position depends on how many nodes switch, which varied from 33 to 37
  with the latched interface relays' random starting states.
- Conditioning on switching is not shown: `OUT_MATERNAL_ADHESION_COMPETENCE`
  switched in 81.8 % of trajectories, `X_ANTIADHESIVE_ROUTE` in 19.8 %.
- There is no trajectory-level unperturbed control.

## Reproducing it

To redraw the figures from the archived run outputs, with a byte-for-byte check:
`bash docs/perturbation_cascade/historical_v051/redraw.sh`. To re-run the
simulation as well:

The scripts locate the repository as `parents[2]` of their own path and write
next to themselves, so run copies from their original location, not from here:

```
mkdir -p output/progesterone_withdrawal
cp docs/perturbation_cascade/historical_v051/{run_p4_withdrawal,analyze_p4_withdrawal}.py output/progesterone_withdrawal/
pixi run -e default python -B output/progesterone_withdrawal/run_p4_withdrawal.py      # ~140 s
pixi run -e default python -B output/progesterone_withdrawal/analyze_p4_withdrawal.py
```

On 2026-10-08, at main `e4296f0`, the seed-1 lineage plus the first 20
single-trajectory runs reproduced the archived events exactly (0 mismatches in
initial state, final state, switch presence and reversal count; largest switch-time
difference 1.8e-15).
