# Computational resources: what is measured, and what is assumed

This page assesses the planning estimates in
`MemoriaCT-individual_Digital Twin_v10` §5 — **up to 300,000 MaBoSS CPU-hours,
40,000 CPU-hours for transcriptomic processing and 120 TB-months of storage** —
against what this repository actually runs.

It exists so the estimates can be checked rather than believed. **No figure from
this page belongs in the proposal text**; the proposal justifies the cloud line
by capability, and the numbers here are machine-specific and will change.

Measured values live in `endotwin/results/benchmarks/benchmark.md`, regenerated
by `pixi run endotwin-benchmark`. They are not repeated here, so the two cannot
drift apart.

## Measured: what the repository consumes today

Three facts, each reproducible:

1. **Each MaBoSS run is single-threaded.** `src/endotwin/simulate.py` writes
   `thread_count = 1`. CPU time and wall time per run are therefore close, and
   the ensemble parallelises across scenarios, rate sets, conditions and donors
   rather than within a run.
2. **The unit of work is small.** One three-phase condition at 10,000
   trajectories is well under a second of CPU time (`benchmark.md`). Per-trajectory
   cost falls as the batch grows, because fixed setup is amortised.
3. **The complete committed workflow is cheap.** `pixi run endotwin-all`
   regenerates every result in `endotwin/results/<version>/` — the exact
   predictions for all 48 scenarios, the 1,680-record fixed-point confirmation,
   the 5,670-record rate-sensitivity ensemble, the reference dynamics and every
   figure — in minutes of CPU time, not hours.

**The model as it stands does not consume meaningful compute.** Any resource
case must rest on work that is planned but not yet implemented.

## The arithmetic, and where 300,000 sits in it

Taking the measured unit cost and multiplying out an exhaustive pairwise
perturbation screen under rate uncertainty, per donor, repeated once per major
model revision:

| Factor | Value | Status |
|---|---|---|
| Perturbation pairs | 2,016 | **derived** — 32 internal nodes, each forcible ON or OFF, give 64 single perturbations and 2,016 unordered pairs. That pairs are screened at all is the assumption |
| Rule-variant scenarios | 48 | **measured** from the model |
| Rate sets per combination | 1,000 | **assumption** — the committed ensemble uses 30 |
| Donors parameterised | 30 | **assumption** — the funded plan names 5 G1 donors for WP2 |
| Campaigns over the project | 4 | **assumption** — one per major model revision |

`benchmark.md` multiplies these out: about **1.2 × 10¹⁰ condition runs, or
3.2 million CPU-hours**.

**So 300,000 CPU-hours is not an inflated figure — it is about 9% of one full
combinatorial campaign as specified above.** It buys a materially reduced
version: fewer rate sets, or fewer donors, or one campaign rather than four. The
v10 estimate therefore constrains the analysis design rather than exceeding it.

**Verdict: technically defensible.** Nothing in the arithmetic requires the
figure to be padded, and the natural campaign overshoots it by more than an
order of magnitude.

## The gap, stated plainly

Technically defensible is not the same as supported. Two things are missing, and
neither should be papered over:

1. **No pairwise screening exists in this repository.** Every screen implemented
   so far varies **one** perturbation at a time, over the nine comparisons
   declared in `endotwin/config/protocols.yaml`. The combinatorial screen that
   justifies the figure is not written, not tested, and not scheduled in the
   work plan.
2. **Nothing commits the project to 1,000 rate sets or 10,000-trajectory
   ensembles.** The committed workflow uses 30 and 2,000. Those choices were
   made because the network is acyclic and its fixed points are provably
   independent of rates, so large rate ensembles buy little on the quantities
   currently reported.

There is a real scientific argument for closing gap 1, and it is recorded in
[wp2_prediction_selection.md](wp2_prediction_selection.md): across all 48
scenarios, **only two of the nine planned comparisons produce an unambiguous
functional prediction at all**, and no single perturbation meets the WP2
selection bar. A single-perturbation space that nearly empty is an argument for
looking at pairs — particularly for WP4, where intervention selection is about
combinations. That argument is about science, not budget, and it should be made
on its own terms or not at all.

## What would make the estimate supported rather than merely defensible

In rough order of effort:

- implement pairwise perturbation screening, with the output contract and
  provenance the single-perturbation screens already have;
- state in the work plan which work package runs it, and when;
- record the rate-set and trajectory choices with the reason for each, so the
  ensemble size is a decision rather than a default.

Until then the honest description is: *the planned campaign would consume the
budgeted compute; the implemented campaign consumes a negligible fraction of
it.*

## The other two figures

**40,000 CPU-hours for transcriptomic processing.** The 42 libraries are bulk
RNA-seq — v10 states "42 RNA-seq libraries will be prepared from 21 selected
chips, with one library per compartment per chip" — and bulk
alignment and quantification costs on the order of CPU-hours per library, not
tens. Primary processing of all 42 is therefore a small fraction of this figure.
The remainder would have to come from reprocessing the public single-cell
atlases used for deconvolution signatures, which is plausible but is not
currently implemented here either.

**120 TB-months of storage.** 42 bulk libraries produce a few hundred gigabytes
of raw sequence, with intermediates of comparable size. Reaching 120 TB-months
requires either retaining substantially more than the sequencing data — the
microscopy images that §4.5 lists among generated data would be the candidate —
or a retention policy more generous than the analysis needs. The figure is not
unreasonable; it is simply not derived from the sequencing plan alone.

## Reproducing

```bash
pixi run endotwin-benchmark          # writes endotwin/results/benchmarks/
pixi run endotwin-all                # the full committed workflow
```

Timings are specific to the machine that produced them; the benchmark records
the platform, engine version and trajectory counts alongside every number.
