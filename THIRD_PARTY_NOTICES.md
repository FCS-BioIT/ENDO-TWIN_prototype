# Third-Party Notices

## PROFILE

- Upstream: `https://github.com/sysbio-curie/PROFILE`
- Revision inspected: `87db279aa064efd5c923560f0aefac653a79a9e6`
- Commit date inspected: `2025-12-02T16:54:01+01:00`
- License: BSD 3-Clause
- Copyright notice:
  Copyright (c) 2018, Computational Systems Biology of Cancer at Institut Curie

PROTOTYPE inspects PROFILE as a read-only methodological reference. Any local
reimplementation must preserve provenance for reused ideas, fixtures, or small
formulas. PROTOTYPE must not copy PROFILE's cancer-specific datasets, RMarkdown
profile builders, shell orchestration, or bundled model assumptions as if they
were ADOC evidence.

## PROFILE_v2

- Upstream: `https://github.com/ArnauMontagud/PROFILE_v2`
- Revision inspected: `c3e8c39dacb0cad1ff21a79aa871667356b6bf42`
- Commit date inspected: `2025-11-05T23:22:52+01:00`
- License: BSD 3-Clause
- Copyright notice:
  Copyright (c) 2021, Arnau Montagud

PROTOTYPE inspects PROFILE_v2 as a read-only methodological reference for graded
target engagement and combination screening. PROTOTYPE must not copy its
prostate-cancer phenotype names, shell script generators, bundled MaBoSS
executables, or R plotting pipeline into the ADOC scientific workflow.

## cb-implant_lock_DT_Ia

- Upstream: `git@github.com:FCS-BioIT/cb-implant_lock_DT_Ia.git`
- Revision inspected: `13ed950`
- License: not redistributed; inspected in place, no files vendored.

PROTOTYPE inspects cb-implant_lock_DT_Ia as a read-only IMPLEMENTATION REFERENCE,
scoped strictly to the rendering approach used for the MaBoSS pathway-dynamics
animation: its fixed graph layout, config-driven node styling, Pillow GIF frame
assembly, and the synchronized time-series panel grammar. No code was copied
verbatim, and no biological rules, topology, or parameters were taken from it.
This prototype is NOT a biological authority for PROTOTYPE. Its spatial
agent-based model, PhysiBoSS coupling, chip geometry, diffusion fields,
embryo/blastoid mechanics, and adhesion-bond physics were deliberately
excluded from this reference and must not be reused in PROTOTYPE.

## MaBoSS and PyMaBoSS (installed dependencies, not vendored)

- MaBoSS engine: `https://github.com/sysbio-curie/MaBoSS`, BSD 3-Clause License,
  copyright Institut Curie (per the upstream README, checked 2026-11-22).
- PyMaBoSS (`maboss` 0.8.15 on PyPI, with the `cmaboss` backend), pinned in
  `pixi.lock`: Python interface maintained in the CoLoMoTo organisation; consult
  its upstream repository for licence terms (not recorded in the installed
  package metadata).

ENDO-TWIN calls these packages at run time. No MaBoSS source or binary is
copied into this repository.
