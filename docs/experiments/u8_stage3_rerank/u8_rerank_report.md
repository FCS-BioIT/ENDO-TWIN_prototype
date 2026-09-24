# U8 — Stage-3 experiment rerank against adopted v0.5.1

> **Generated file — do not edit.** Regenerate with `pixi run build-u8-stage3-rerank`. The Stage-3 computation of `src/dt_adoc/experiments/stage3_design.py`, run unchanged against `adoc-literature-superset-v0.4.0` (the frozen reference, read from `docs/experiments/stage3_experiment_design.tsv`) and `adoc-literature-superset-v0.5.1`. No MaBoSS run; no model or frozen artifact is modified.

## Mandate: conditional on D1

`AC01` is `alias_challenged`, depending on D1; without D1 it is `unclassified_by_section_5_4` (`docs/scrna/node_support_findings.json`). Status: `MANDATORY_CONDITIONAL_ON_D1`. The rerank is owed because AC01 is alias_challenged, and that verdict rests on D1, a post-extraction interpretive call. Without D1, AC01 is unclassified_by_section_5_4 and the rerank is optional. U8 carries this condition and does not re-adjudicate D1.

## Answer

**`dropout_e2` remains first: True.** v0.5.1 ordering status: `CARRIED_OVER_UNCHANGED`. Premises unchanged: 10 of 10. Pair separations changed: 0 of 320; on a usable readout: 0. Exact marginals compared across every node, experiment and class: 16080, differing: 0.

## 1. Frozen v0.4 ranking (curated positions, quoted)

| Position | Experiment | Source |
|---|---|---|
| recommended | `dropout_e2` | docs/stage3_experiment_selection.md §3 |
| runner_up | `smo_antagonist` | docs/stage3_experiment_selection.md §6 |
| third_explicitly_not_recommended | `dropout_camp` | docs/stage3_experiment_selection.md §6 |
| prerequisite_registration_not_run | `observe_e2_primed` | docs/stage3_experiment_selection.md §3 |

Candidate set (separates a fork on a usable assay): `add_hcg_on_e2`, `dropout_camp`, `dropout_e2`, `observe_e2_primed`, `smo_antagonist`.

## 2. v0.5.1 ranking

Every computed premise of the frozen ordering is unchanged and the curated declarations are the same objects, so the ordering carries over without re-adjudication:

| Position | Experiment |
|---|---|
| recommended | `dropout_e2` |
| runner_up | `smo_antagonist` |
| third_explicitly_not_recommended | `dropout_camp` |
| prerequisite_registration_not_run | `observe_e2_primed` |

Candidate set: `add_hcg_on_e2`, `dropout_camp`, `dropout_e2`, `observe_e2_primed`, `smo_antagonist`.

## 3. Per-arm delta

| Experiment | Forks on a usable assay (v0.4 → v0.5.1) | Usable pairs | Changed fields |
|---|---|---|---|
| `observe_e2_primed` | SEC → SEC | 4 → 4 | none |
| `observe_hormone_treated` | — → — | 0 → 0 | none |
| `dropout_e2` | SEC → SEC | 8 → 8 | none |
| `dropout_camp` | CAMP → CAMP | 1 → 1 | none |
| `dropout_xav939` | — → — | 0 → 0 | none |
| `add_hcg_on_hormone_treated` | — → — | 0 → 0 | none |
| `add_hcg_on_e2` | SEC → SEC | 4 → 4 | none |
| `add_il11` | — → — | 0 → 0 | none |
| `anti_lif` | — → — | 0 → 0 | none |
| `anti_lif_plus_il11` | — → — | 0 → 0 | none |
| `smo_antagonist` | HH → HH | 1 → 1 | none |
| `bmpr_inhibitor` | — → — | 0 → 0 | none |
| `pc6_knockdown` | — → — | 0 → 0 | none |
| `dag1_cleavage_resistant` | — → — | 0 → 0 | none |
| `anti_spp1` | — → — | 0 → 0 | none |
| `hand2_loss` | — → — | 0 → 0 | none |

## Premises of the frozen ordering, on both models

| Premise | Cited by | Unchanged |
|---|---|---|
| `P1_usable_readouts` | §3 Readouts; test_only_two_maternal_nodes_carry_a_usable_assay | yes |
| `P2_only_arm_on_both_usable_readouts` | §3 Readouts; test_dropout_e2_is_the_only_arm_separating_both_usable_assays | yes |
| `P3_dropout_e2_opposite_against_committed` | §3 Mechanisms separated; test_dropout_e2_separates_the_committed_class_from_every_other | yes |
| `P4_most_sec_pairs_on_usable_assay` | §3 'More SEC class pairs on a usable assay than any other candidate' | yes |
| `P5_e2_only_arms_reach_only_sec_c_pairs` | §3; test_the_e2_only_arms_resolve_only_whether_sec_c_survives | yes |
| `P6_sec_pairs_unreached_at_a_readout_that_exists` | §3 'exactly one pair unreached'; §7 | yes |
| `P7_dropout_e2_decision_table` | §5; test_the_four_outcome_decision_table_is_what_the_model_predicts | yes |
| `P8_runner_up_propagates_nowhere` | §6 point 1 (decisive); test_xav939_and_smo_propagate_nowhere_in_the_committed_model | yes |
| `P9_runner_up_usable_opposite_separation` | §6 'Its separation lands on S_IGFBP1 ... with opposite predictions' | yes |
| `P10_third_arm_usable_separation` | §6 'separates a pair on a usable assay' | yes |

Values for both models are in `u8_rerank_summary.json`.

## Cause attribution

* **U5b's executable rule change.** `OUT_STROMAL_DECIDUALIZED`: `S_DECIDUALIZED and S_PRL and S_IGFBP1` → `S_DECIDUALIZED`, retiring `S_IGFBP1→OUT_STROMAL_DECIDUALIZED`, `S_PRL→OUT_STROMAL_DECIDUALIZED`. Stage-3 marginals it changes: 0.
* **Changed model structure.** Edges absorbed only in v0.4: none; phenotype-inert only in v0.5.1: `S_IGFBP1`, `S_PRL`. Enters any Stage-3 class rewrite or arm: False.
* **Altered alias classes:** False.
* **Bookkeeping only:** the rendered design differs from v0.4's in 1 line(s), the generated-file banner.

## Scoring contract

Readout tiers from `config/observation_model_map.tsv` only (sha256 `74f0d5d0896b`), identical for both models; `config/candidate_score.yaml` read: False. scRNA activation statuses: `provisional`, `rejected`, `reported_only`; can promote a tier: False.

U6b catalogue (`docs/u6b_muc1_reconciliation/rule_variants.tsv`) statuses `catalog_only`, `reference_only`; Stage-3 nodes touching it: none.

