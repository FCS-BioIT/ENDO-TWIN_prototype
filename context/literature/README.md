# Embryo-adhesion literature knowledge layer

This directory is the Codex-readable evidence package for extending the ADOC
MaBoSS model with maternal epithelial and stromal embryo-adhesion mechanisms.

## Entry points

- `knowledge-base.yaml`: canonical machine-readable inventory containing scope,
  calibration anchors, modules, nodes, edges, perturbations, environmental
  factors, gaps and references.
- `embryo-adhesion-review.md`: complete human-readable review.
- `candidate-nodes.tsv` and `candidate-edges.tsv`: flat tables for joins,
  filtering, evidence review and model-spec generation.
- `references.tsv`: DOI/PMID-indexed bibliography.
- `source-provenance.tsv`: provenance for the prior research report, project proposal, local ADOC sources, and metadata verification.
- `mechanisms.tsv`: one row per pathway/mechanism.
- `perturbations.tsv`: model perturbations and expected direction.
- `environmental-factors.tsv`: temperature, oxygen, pH, flow, matrix and assay
  variables, including explicit evidence limitations.
- `evidence-gaps.tsv`: unresolved items that must not be guessed.
- `codex-ingestion.md`: deterministic instructions for using this package.

Rows in this directory are candidates. They do not replace the executable
baseline until they pass the repository evidence and validation gates.
