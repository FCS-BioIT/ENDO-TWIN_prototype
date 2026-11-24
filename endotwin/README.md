# ENDO-TWIN mainline data

| Directory | Content |
|---|---|
| `models/endotwin-v0.3.0/` | The current executable network and its dictionaries ([`docs/model_construction.md`](../docs/model_construction.md)) |
| `models/endotwin-v0.1.0/` | The previous version (19 nodes), kept because v0.2.0's `lineage.tsv` maps every node back to it |
| `config/` | Protocols and timing, interventions, observation map, planned data schemas |
| `evidence/` | References used by the mainline rules, with evidence depth and Crossref check |
| `predictions/` | Template, the two checked WP2 drafts, and (future) frozen records of prospective predictions |
| `results/endotwin-v0.3.0/` | Every committed result for the current version; regenerate with `pixi run endotwin-all` |
| `results/endotwin-v0.1.0/` | Results of the previous version, frozen as committed (its configuration is in Git history, not in `config/`). The v0.1.0 model text files were later edited to remove the prototype's private name (comments and notes only; no rule changed), so their digests no longer match that manifest |

`results/endotwin-v0.3.0/run_manifest.json` binds the results to the SHA-256 of
every model and configuration file they were computed from. A test fails if any
of those files changes without regenerating the results.

| Result | Content |
|---|---|
| `structure.json` | Exact structure of the default network and of all 24 rule-variant scenarios |
| `fixed_point_predictions.tsv` | Fixed point of every phase of every condition under every scenario |
| `comparison_directions.tsv`, `discrimination.tsv` | Predicted directions per matched comparison, and which comparisons separate which hypotheses |
| `maboss_confirmation.tsv` | MaBoSS end-of-phase probabilities versus exact fixed points (2,000 trajectories) |
| `relay_transient.tsv`, `relay_transient_summary.json` | The HAND2-relay example (10 paired replicates, 5,000 trajectories) |
| `rate_sensitivity.tsv`, `relay_rate_robustness.tsv`, `rate_sensitivity_summary.json` | Random transition-rate sensitivity |
| `dynamics_*.tsv` with `_provenance.json` | Example trajectories (10,000 trajectories, seed 1): reference and BMP receptor inhibition under both Q1 rules, IL-1β under both inflammation rules, FOXO1 inhibition under both PRL rules |
