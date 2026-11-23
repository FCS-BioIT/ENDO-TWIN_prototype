# Run manifest contract

Each canonical run uses a JSON object with:

- `schema_version`, `run_id`, and `created_at`;
- `software` with MaBoSS/PyMaBoSS and wrapper versions;
- `model` with baseline `.bnd`, `.cfg`, patient variant, and hashes;
- `data` with source manifest and analysis-ready/mapping artifacts;
- `cohort` with independent unit, included units, exclusions, and split role;
- `personalization` with mapping method, thresholds, uncertainty, and leakage
  controls;
- `simulation` with seeds, trajectory count, time horizon, time tick, thread
  count, and perturbation;
- `phenotypes` with explicit definitions;
- `outputs` with path, kind, size, and SHA-256;
- `validation` with completed levels and artifact paths;
- `warnings`.

Paths must be repository-relative, must not traverse outside the repository, and
must identify non-empty files. Hash every canonical input and output.

Smoke and full runs need different run IDs and output roots.
