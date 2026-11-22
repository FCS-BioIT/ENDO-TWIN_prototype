# ENDO-TWIN Project Instructions

ENDO-TWIN builds a mechanistic, stochastic Boolean (MaBoSS) model of human
endometrial hormonal regulation in the ADOC endometrium-on-chip, and tests it
prospectively. It was derived from the prototype (`docs/ORIGIN.md`).

## Repository layout

- **Mainline (active work):** `src/endotwin/` (code), `endotwin/models/`
  (versioned networks), `endotwin/config/` (protocols, interventions,
  observation map, data schemas), `endotwin/evidence/`, `endotwin/predictions/`,
  `endotwin/results/`, `tests/mainline/`.
- **Prototype foundation and legacy:** `src/dt_adoc/`, `models/`, `config/`,
  `context/`, `data/`, `input_tables/`, most of `docs/` and `tests/unit`,
  `tests/integration`. Many of these files are pinned by SHA-256 in closed-phase
  records. Do not edit, move or add files under `models/`, `config/`,
  `docs/phase2a/`, `docs/phase1b_closure/`, `docs/scrna/` or
  `docs/experiments/`; put new mainline material under `endotwin/`.

## Evidence and data contracts

- Treat every existing file under `data/` as immutable. Never edit, rename,
  convert in place or overwrite source evidence; write derived data only to a
  declared output directory outside `data/`.
- Preserve blanks, missing values, below-detection values, excluded observations
  and numeric zeros as distinct states. Keep raw, QC, transformed, binarised,
  mapping and model-parameter stages separate.
- The donor is the independent biological unit. Chips, cells, fields, wells,
  time points and technical replicates are not independent donors.
- Protect row-level donor metadata; use pseudonymised codes only.
- Follow `.codex/harness/data-lineage-contract.md` for canonical runs and
  `.codex/harness/scientific-review-checklist.md` for scientific review.

## Model and claim boundaries

- "Digital twin" means a computational hypothesis model of the experimentally
  defined ADOC system, not a clinical replica, a complete menstrual cycle or a
  treatment recommender.
- MaBoSS probabilities are simulated trajectory frequencies under stated rules,
  rates, initial conditions and perturbations: not concentrations, not cell
  fractions, not clinical probabilities. MaBoSS time is not experimental time.
- A model perturbation is a conditional model prediction, not causal evidence.
- Do not invent Boolean rules, topology, thresholds, rates, phenotype
  definitions, mappings or physical time units. Every rule in
  `endotwin/models/*/edges.tsv` carries an evidence class; alternatives go in
  `rule_variants.tsv`, never silently into the default network.
- Expression, protein abundance and secretion are not node activity. Inferred
  deconvolution proportions are relative state contributions, not absolute cell
  fractions.
- Software tests verify the implementation; they are not biological validation.

## Prospective evaluation (WP2, WP4)

- Freeze predictions with `pixi run endotwin-freeze` from a committed, clean
  tree before any evaluation data exist. Never edit a frozen record; never use
  evaluation data to revise it.
- WP2 evaluation donors must not appear in model development.
- The WP4 intervention is selected with G2 data only; G3 data never inform the
  selection. Do not assume that IL-1beta exposure (G2) reproduces endometriosis
  (G3).

## Validation

- `pixi run endotwin-test` for the mainline; `pixi run test` is the complete
  suite. `pixi run endotwin-all` regenerates every mainline result and figure.
- Keep smoke and full outputs separate. Record model and configuration hashes,
  software versions, seeds, trajectory counts and time settings.
- Do not load the multi-gigabyte RDS merely to test runtime availability.
  Report unavailable R, Seurat or MaBoSS gates instead of inferring results.
- Legacy checks that read the prototype Git history skip with a declared reason
  here (`tests/unit/source_history.py`); do not convert other failures into
  skips.
