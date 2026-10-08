# Perturbation specs

Each file declares a perturbation of an established protocol state for
`python -m dt_adoc.cli perturb cascade --spec perturbations/<file>.yaml`
(`pixi run perturb-cascade --spec ...`). The format is defined and enforced by
`src/dt_adoc/perturbations/spec.py`; see `docs/perturbation_cascade/README.md`.

A spec can only *select* mechanisms the repository already executes:

| key | provenance class | executes through |
|---|---|---|
| `input_changes` | `protocol_input_change` | the input values a protocol step sets (`IN_*` nodes only) |
| `interventions` | `registered_intervention` | `config/intervention_library.tsv` and its licences |
| `rule_variants` | `registered_rule_variant` | the model's registered rule-variant families |

Reagent-free node vetoes (`veto`, `hypothetical_vetoes`, `effects`), forced-ON
clamps (`force_on`) and free rule text (`rule_replace`) are refused by name. A
node knockout named without a reagent is the model-only target-ablation unit
that Stage 4b owner decision 1 reserves as separate work.

Every result is a conditional model-internal prediction under the declared
semantics. `e2_input_withdrawal` is a model-internal relaxation, not the
pre-registered `dropout_e2` experiment, and does not touch its design or calling
rules.
