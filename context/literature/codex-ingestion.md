# Codex ingestion contract: embryo-adhesion literature

## Goal

Use `knowledge-base.yaml` to propose evidence-backed extensions to the existing
ADOC MaBoSS baseline while preserving the repository's claim and validation
boundaries.

## Required sequence

1. Read `docs/AGENTS.md`, `context/project-context.md`, `models/README.md`, and this file.
2. Load `context/literature/knowledge-base.yaml` as the source of candidate
   mechanisms. Join `REF-*` identifiers to `references.tsv`.
3. Compare candidate nodes with `models/specs/nodes.tsv` using
   `models/extended/adoc-literature-v0.2.0/node_dictionary.tsv`.
4. Start with the smallest identifiable extension. Recommended first addition:
   `E_LIF`, `E_GP130_STAT3`, `S_HAND2`, `E_PODXL`, `E_CD98_CD9`,
   `E_CDH1_APICAL`, `E_PC6`, the two DAG1 states, `S_TAZ_ECM`, and
   `X_MECHANICAL_PERMISSIVE_ECM`.
5. Add every promoted node and edge to the versioned extended model with
   definition, sign, evidence IDs, confidence and direct/inferred status. Do
   not edit `data/`.
6. Keep embryo presence, competence, hCG and conditioned signals as external
   inputs. Do not add trophoblast intracellular logic to the maternal network.
7. Preserve alternative rules as explicit uncertainty notes or alternate edges.
   Do not choose the desired phenotype as the criterion for topology.
8. Compile and run the same topology under untreated, HT, HT+mifepristone,
   HT+anti-SPP1, embryo-absent, embryo-incompetent, excess-ER-stress, and
   high-stiffness configurations. Do not use condition-specific topology.
9. Calibrate only parameters declared before validation. Prefer the
   mifepristone adhesion response as held-out validation if its effect was not
   already used to construct/fix the rules.
10. Report stochastic convergence, alternative-rule sensitivity and uncertainty.

## Modeling rules

- LIF/GP130/STAT3 and the PGR-IHH-NR2F2-BMP2-HAND2 relay can be tested as
  stronger gates because causal mouse evidence is replicated.
- Human epithelial effectors (CD98, apical CDH1, ANXA2, HB-EGF, MUC1 glycoform,
  integrins) should usually be redundant routes or rate modifiers rather than
  mandatory simultaneous gates.
- Split barrier and permissive MUC1 states.
- Anti-SPP1 acts on free extracellular ligand, not on the expression node.
- Distinguish physiological barrier remodeling from nonspecific barrier damage.
- Temperature, oxygen and pH remain metadata/boundary variables until a direct
  ADOC perturbation establishes sign and threshold.
- Treat MaBoSS time as relative. The ADOC 34.1 +/- 12.2 h anchor may be used only
  in a separately documented scaling analysis.

## Stop conditions

Stop and record a gap instead of inventing a rule when:

- a receptor/ligand belongs mainly to the excluded embryo compartment;
- the sign differs by MUC1 glycoform or senescence state;
- only expression correlation supports the edge;
- a concentration, threshold or time constant is absent;
- the proposed perturbation cannot be separated from toxicity or barrier damage.
