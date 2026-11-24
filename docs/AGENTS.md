# ENDO-TWIN Project Instructions

ENDO-TWIN builds a mechanistic, stochastic Boolean (MaBoSS) model of human
endometrial hormonal regulation in the ADOC endometrium-on-chip, and tests it
prospectively. It was derived from an earlier, private prototype (`docs/ORIGIN.md`).

> **This file is no longer discovered automatically.** It moved from the
> repository root to `docs/AGENTS.md` on 2026-11-23 at the owner's request, to
> shrink the root listing. Coding agents look for `AGENTS.md` at the root, so
> nothing loads these instructions for you any more: read this file at the start
> of any session that touches the model, the evidence or `data/`. The same move
> took `README.md` and `LICENSE` into `docs/` (`docs/ORIGIN.md` §root tidying).

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
- **Do not relocate a top-level directory.** This was attempted on 2026-11-23
  with the owner's permission and rolled back twice. Three separate mechanisms
  pin paths, and checking only one of them gives false confidence:
  1. the implementation digest, recomputed from **live globs**
     (`concordance.simulate.IMPLEMENTATION_GLOBS`) by `unit.test_concordance`,
     `unit.test_endpoint_figure` and `unit.test_klf12_conditioning_contract`.
     Editing any globbed file, **including one comment line**, stales eight
     digest-stamped artifacts, and they cannot all be regenerated here
     (`klf12_conditioning_settings.json` needs the local-only RDS,
     `endpoint_run_settings.json` ~100 CPU-minutes);
  2. standalone frozen-byte constants, such as `FROZEN_MAP_SHA256` in
     `tests/unit/test_compartment_attribution.py`, which pins
     `config/observation_model_map.tsv`; and
  3. closed-phase records that pin paths as well as hashes, such as
     `docs/phase1b_closure/phase1b_closure_summary.json`.
  `context/` is blocked by (1), `input_tables/` by (2), `data/` by (1) through
  `src/dt_adoc/concordance/scrna_audit_cli.py`, and `docs/` additionally
  contains the closed-phase directories. `models/` must also stay distinct from
  `endotwin/models/`, which is the mainline. Watch the **skip count** as well as
  failures: a stale path can turn a passing test into a silent skip.
  **Single files are a different case.** `README.md`, `LICENSE` and this file
  moved into `docs/` on 2026-11-23 and `.ruff.toml` was deleted outright (its
  two exclusions are now arguments in `pixi.toml`). None of them was pinned by
  any of the three mechanisms, and each move was a handful of path edits. What
  the rule above forbids is moving a **directory** that frozen bytes name.

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
- Follow `docs/codex/harness/data-lineage-contract.md` for canonical runs and
  `docs/codex/harness/scientific-review-checklist.md` for scientific review.

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
  suite. `pixi run endotwin-all` regenerates every mainline result and figure,
  ending with the scientific verification report
  (`endotwin/results/<version>/verification_report.md`, also available on its own
  as `pixi run endotwin-verification-report`).
- `pixi run endotwin-benchmark` measures representative workloads into
  `endotwin/results/benchmarks/`. Those timings are for repository planning
  (`docs/computational_resources.md`) and are machine-specific; they do not
  belong in the proposal text.
- **Adding a node means touching two hard-coded tables.** `LAYOUT` in
  `src/endotwin/figures.py` and `FRIENDLY` in `src/endotwin/animation.py` both
  raise `KeyError` on an unknown node, which kills the figure step near the end
  of `endotwin-all` after the expensive MaBoSS work has already been written.
- **Never run `ruff format` on a path directly.** The exclusions live on the
  `lint` and `format-check` command lines in `pixi.toml`, not in a config file,
  so `ruff format src/` silently reformats the two byte-pinned files
  (`protocols/conditions.py`, `observations/compartment_attribution.py`) and all
  of `src/scripts/`. This happened on 2026-11-24; six files had to be restored.
  Use `pixi run format-check` to check, and pass the same `--extend-exclude`
  list if you must format.
- **Read the exit status of the right command.** `endotwin-all` propagates
  failure correctly (the CLI exits non-zero and pixi passes it through); a note
  here previously claimed otherwise and was wrong. What hides it is the shell:
  in `pixi run endotwin-all > log 2>&1; echo $?; tail log` the status belongs to
  `tail`, not to pixi, and a background runner reports the same. Capture the
  status immediately, or use `&&`/`set -o pipefail`. Also note that stderr is
  unbuffered while redirected stdout is not, so a traceback appears at the TOP
  of such a log even though it happened last.
- Keep smoke and full outputs separate. Record model and configuration hashes,
  software versions, seeds, trajectory counts and time settings.
- Do not load the multi-gigabyte RDS merely to test runtime availability.
  Report unavailable R, Seurat or MaBoSS gates instead of inferring results.
- Legacy checks that read the prototype Git history skip with a declared reason
  here (`tests/unit/source_history.py`); do not convert other failures into
  skips.
