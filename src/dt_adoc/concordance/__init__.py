"""Model-data concordance: what the ADOC digital twin does and does not explain.

This package exists because `docs/results_reproducibility_matrix.tsv` records a
*curated* comparison whose simulated column was pasted in by hand, and
`output/` is gitignored, so no tracked artifact backs any number in it. The
modules here regenerate the simulated side from the committed model and emit
tracked artifacts with provenance, so that every plotted quantity traces either
to a source datum or to a reproducible simulation.

The package deliberately adds no biology. `mechanism` reports properties of
`network.bnd` alone, `simulate` runs protocols that already exist, and `table`
joins them to observations that were already curated. Nothing here may change a
rule, a rate, an initial condition or a threshold to improve agreement.
"""

from __future__ import annotations
