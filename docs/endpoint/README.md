# Functional-endpoint source data

Tracked inputs of `docs/assets/adoc_functional_endpoint_v0.5.0.png`.

| file | written by | content |
|---|---|---|
| `endpoint_replicates.tsv` | `pixi run build-endpoint-replicates` | every replicate: arm, horizon, replicate index, seed, per-trajectory seed range, node, value |
| `endpoint_run_settings.json` | same | model identity vs v0.4.0, seeds, trajectory count, lineages, observed counts and roles from `config/calibration.yaml`, exact converged values by enumeration, the seed-structure probe, generator hashes, git provenance |
| `endpoint_figure_source_data.tsv` | `pixi run render-endpoint` | every plotted value and interval, recomputed from the two files above |

## What the simulated spread is

Each replicate is a complete MaBoSS lineage (every protocol phase, with the
projected continuation between phases) under one seed. A MaBoSS run with seed
`s` and `N` trajectories is the union of single-trajectory runs with seeds
`s … s+N−1` (measured on the full node table and joint state distribution of a
dynamic protocol; `docs/maboss_estimator_semantics.md`, addendum 2026-09-23, and
`seed_structure_probe` in the run settings), so replicate `r` uses
`seed = 1 + r · N`: blocks are disjoint **between replicate indices**, and the
same block is deliberately reused across the three arms and both horizons for a
given replicate index (common random numbers, a paired design).

The plotted **±1 SD across replicates** is the run-to-run reproducibility of the
simulator's time-averaged occupancy estimator. It is not experimental,
biological or model-structure uncertainty; it is not an i.i.d. Monte Carlo SE
(the initial-state draw over consecutive per-trajectory seeds is stratified); it
is not MaBoSS's node error column, and it is not a binomial or Wilson interval.
The Wilson 95% intervals in the figure belong to the **embryo counts** only.

## Running the replicates safely

A declared-horizon worker can reach 11–14 GB resident. Running many in an
interactive session exhausted a 125 GB host and the OOM kill took the whole
terminal session with it. Run it as its own capped unit:

```bash
systemd-run --user --unit=dtadoc-endpoint-replicates \
  -p MemoryMax=60G -p MemorySwapMax=0 --working-directory="$PWD" \
  "$(command -v pixi)" run build-endpoint-replicates
pixi run render-endpoint
```
