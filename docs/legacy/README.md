# Legacy prototype material

ENDO-TWIN builds on the prototype, whose primary question was
embryo-adhesion competence (receptivity) in the ADOC chip. That work is preserved
in full. It is not the focus of ENDO-TWIN.

## Where the legacy work lives

Paths are unchanged from the source repository, because closed-phase records
pin files by path and SHA-256.

| Material | Path |
|---|---|
| Prototype front page (2026-10-21), verbatim apart from two renamed skill folders; its links are relative to the repository root | [`PROTOTYPE_README_2026-10-21.md`](PROTOTYPE_README_2026-10-21.md) |
| Planning ledgers | [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md), [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md), [`REQUIREMENTS_COVERAGE.tsv`](REQUIREMENTS_COVERAGE.tsv), [`TASK_CONTRACT.md`](TASK_CONTRACT.md) |
| Model versions v0.1.0-v0.6.0, including the adhesion module | `models/` |
| Embryo-adhesion endpoint: observed counts, replicate simulations, C3a pre-registered kinetic readouts | `config/calibration.yaml`, `docs/endpoint/`, `docs/c3_kinetic_readouts/`, figure `docs/assets/adoc_functional_endpoint_v0.5.0.png` |
| Code (simulation, interventions, evidence, audits, reporting) | `src/dt_adoc/` |
| Protocols, observation mappings, intervention library | `config/` |
| Literature and evidence registers | `context/` |
| Analysis reports and committed results | `docs/` (for example `docs/v05_u5_structural_audit.md`, `docs/concordance_analysis.md`, `docs/c3_kinetic_readouts/`) |
| Figures | `docs/assets/` (legacy figures named `adoc_*`) |
| Tests | `tests/unit`, `tests/integration`, `tests/biological_constraints`, `tests/regression_profile*` |

## Using it

The prototype tasks in `pixi.toml` still run, for example `pixi run
render-network` (v0.6.0 network figure) or `pixi run perturb-cascade --spec
perturbations/progestin_withdrawal.yaml`. Tasks that replay closed phases need
the prototype Git history and must be run in the source repository at
`b1de5f9` (`docs/ORIGIN.md`).

## Labelling rule

A result produced by a prototype model version is always quoted with that
version (for example "v0.5.0 functional-endpoint figure"). It is never presented
as an ENDO-TWIN result. Embryo adhesion in particular is not ENDO-TWIN data:
the grant measures no adhesion, and the published adhesion arms cannot separate
any ENDO-TWIN hypothesis (`docs/experimental_data.md`, section 3).
