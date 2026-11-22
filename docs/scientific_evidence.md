# Scientific evidence: from papers to predictions

ENDO-TWIN keeps a traceable chain for every executable rule:

**paper -> biological finding -> regulatory interaction -> Boolean function ->
simulated prediction -> experimental readout.**

| Link | Where it is recorded |
|---|---|
| Paper | `endotwin/evidence/references.tsv` (ET-xxx; corpus papers link to `context/literature/references.tsv` REF-xxx, DOI-checked by a test) |
| Finding | `finding_used_by_endotwin` column of the same table; for inherited edges, the prototype experimental evidence table `context/evidence/edge_experimental_evidence.tsv` |
| Interaction | `endotwin/models/endotwin-v0.1.0/edges.tsv`: one row per dependency, with sign, compartment crossing, evidence class, references, the v0.6.0 edge it descends from and the grading that edge received |
| Boolean function | `endotwin/models/endotwin-v0.1.0/network.bnd` (default) and `rule_variants.tsv` (alternatives); `tests/mainline/test_model_integrity.py` requires the edge table to equal the dependencies derived from the rules |
| Prediction | `endotwin/results/endotwin-v0.1.0/fixed_point_predictions.tsv`, `comparison_directions.tsv`, `discrimination.tsv` |
| Readout | `endotwin/config/observation_map.tsv` |

## Evidence classes

Every dependency carries exactly one class (`edges.tsv`, column
`evidence_class`). The class says what kind of support exists, not how strong
the biology is in general.

| Class | Meaning | Count in the default network |
|---|---|---|
| `literature_supported` | Primary literature supports the interaction in a relevant system | 5 |
| `literature_supported_topic_level` | Inherited from a prototype topic-level evidence record; where full-text graded, the cited papers did **not** demonstrate this specific edge | 4 |
| `literature_supported_species_transfer` | Supported in mouse only, applied to human | 1 |
| `literature_supported_contested` | Supported, but the subject of a competing hypothesis (Q1) | 1 |
| `literature_supported_route_unresolved` | The phenotype is supported; the intracellular route is not | 1 |
| `adoc_supported` | Supported by ADOC observations (expression or secretion) | 3 |
| `experimental_definition` | Definitional effect of an experimental input on its target (ligand on receptor, inhibitor on its target) | 5 |
| `simplifying_assumption` | A modelling choice, stated as such | 3 |
| `alternative_hypothesis` | Present only in a rule variant | 3 (variant-only) |

## The rules most relevant to the grant questions

### Progesterone and PGR signalling (inherited, unchanged)

`E_PGR = IN_PROGESTIN`, `S_PGR = IN_PROGESTIN`. The nodes are ligand-activated
receptor activity, separate per compartment so that a compartment-specific
receptor perturbation stays expressible. Evidence: the ADOC regimen
(SOFIA-HT-001, in-house). E2 induction of PGR expression is not represented.
In the unperturbed network the two nodes, together with `E_IHH`, `S_NR2F2`,
`S_BMP2` and `S_HAND2`, compute the same function as `IN_PROGESTIN`: one
progestin input drives the whole PGR-dependent module. This inherited alias
class is a limitation, not a finding.

### BMP-associated stromal decidualisation (new structure, Q1)

```
S_BMP2      = (S_PGR and S_PKA) or S_NR2F2                  // BMP2 ligand expression (unchanged)
S_BMP_SMAD  = S_BMP2 and not IN_BMPR_INHIBITOR               // receptor / SMAD1/5/8 activity (new)
OUT_STROMAL_DECIDUALIZATION
            = S_PGR and S_PKA and S_BMP_SMAD and not S_IL1_SIGNALING    // default, H1 BMP-required
            = S_PGR and S_PKA and not S_IL1_SIGNALING                   // variant, H1 PGR-sufficient
```

- Mechanism: BMP2 signals through BMP receptors to phosphorylate SMAD1/5/8;
  SMAD1/5 knockdown impairs human decidualisation (IGFBP1 and WNT4 fall) and
  BMP2 add-back rescues, in 2D and in assembloids (Liao et al. 2024, ET-013,
  read in full in the prototype's U4b). Recombinant BMP2 enhances human stromal
  differentiation on top of E2+P+cAMP (Li et al. 2007, ET-008); uterine Bmp2 is
  required in mouse (Lee et al. 2007, ET-004).
- What the model assumes: receptor availability and BMP antagonists are not
  represented; the inhibitor acts only on stroma.
- Why it is new: the prototype had refused a SMAD node because, without an
  independent determinant, it would be an exact alias of `S_BMP2`
  (`docs/v05_u4b_candidate_node_closure.md`, section 3.1, disposition
  `WAIT_FOR_EXPERIMENT`). The BMP receptor inhibitor of WP1 Task 1.4 is that
  determinant; with it, `S_BMP_SMAD` is no longer an alias.
- Prediction: under confirmed receptor inhibition (pSMAD1/5/8 down in both
  hypotheses), PRL and IGFBP-1 fall under H1 BMP-required and are unchanged
  under H1 PGR-sufficient. Readouts: pSMAD1/5/8 (target engagement), PRL,
  IGFBP-1. Residual decidualisation would not by itself identify the mediator
  (for example PGR-SOX4-FOXO1, ET-010), which is not encoded.

### Stromal regulation of epithelial proliferation (Q2)

```
S_HAND2             = S_BMP_SMAD or S_PGR
S_PARACRINE_MITOGEN = not S_HAND2                                  // renamed from S_FGF_MITOGENIC
OUT_EPITHELIAL_PROLIFERATION
                    = IN_E2 and S_PARACRINE_MITOGEN                // default, stromal relay (v0.5.2 C5)
                    = IN_E2 and S_PARACRINE_MITOGEN and not S_HAND2   // variant, v0.5.1 representation
                    = IN_E2 and not E_PGR                          // variant, epithelial-autonomous
```

- Mechanism: progesterone induces stromal HAND2, which represses stromal
  mitogenic signals and so restrains E2-driven epithelial proliferation (mouse
  conditional deletion: Li et al. 2011, ET-005). In human stromal cells HAND2
  siRNA raises FGF9 only; FGF1, FGF2, FGF7 and FGF18 are not progestin-regulated
  (Murata et al. 2019, ET-007), which is evidence **against** an aggregate FGF
  node. The node was therefore renamed to a ligand-agnostic
  `S_PARACRINE_MITOGEN`.
- What the model assumes: the FGF-to-epithelium step is inferred in mouse, not
  demonstrated (no add-back, no receptor blockade). No primary paper in the
  corpus supports the epithelial-autonomous route; it is included because Q2
  requires the comparison.
- Predictions: stromal HAND2 knockdown under the full regimen raises
  proliferation only under the stromal hypotheses; blocking the paracrine route
  during E2 priming lowers proliferation only under the stromal hypotheses;
  blocking it during differentiation discriminates nothing, because the relay is
  already silenced there. Readouts: Ki67, EdU (planned; ADOC has no
  proliferation readout yet).

### Epithelial secretory differentiation

`OUT_EPITHELIAL_SECRETORY = IN_E2 and E_PGR` (inherited `E_SECRETORY_STATE`,
merged with its exact alias `E_PAEP`). Evidence: ADOC observations (SOFIA-SC-001,
SOFIA-EPI-001). Because MPA, cAMP and XAV939 are applied together, the PAEP rise
cannot be attributed to the progestin alone. The published PAEP rise was used to
construct this rule; agreeing with it is circular, not evaluation.

### IL-1beta (provisional, WP3/WP4)

```
S_IL1_SIGNALING = IN_IL1B
OUT_STROMAL_DECIDUALIZATION = ... and not S_IL1_SIGNALING       // every Q1 variant
S_PGR = IN_PROGESTIN                                              // default, INF decidual-only
S_PGR = IN_PROGESTIN and not S_IL1_SIGNALING                      // variant, INF PGR depletion
```

- Mechanism: IL-1beta impairs human stromal decidualisation, with PRL and
  IGFBP-1 reduced (Frank et al. 1995, ET-014; Yu et al. 2019, ET-015; Taylor
  et al. 2024, ET-016; Gnecco et al. 2023, ET-012). The intracellular route is
  contested (ERK1/2 in Yu et al., JNK in Taylor et al.); NF-kappaB has no paper
  in the corpus, so the node is generic IL-1 receptor signalling. Yu et al. also
  report PR depletion, and Gnecco et al. report IL-1beta dysregulating
  epithelial proliferation via the stroma, which motivates the PGR-depletion
  variant.
- Evidence depth: the three non-corpus IL-1beta papers were read at abstract
  level and DOI-verified against Crossref on 2026-11-22; they were not read in
  full.
- Prediction: pSMAD1/5/8 separates the two routes (unchanged vs down);
  proliferation rises under the PGR-depletion route only if Q2 is stromal.
- Status: to be revised with the G2 data (Task 4.1). IL-1beta exposure is not
  assumed to reproduce endometriosis.

## Inherited evidence weaknesses made visible

- The IHH-NR2F2-BMP2 backbone was cited through one topic-level record
  (LIT-IHH-001) that fanned six references onto every edge. Full-text grading
  found `not_demonstrated` for every graded row of those edges, and the prototype
  retracted several citations (for example Kurihara 2007 from BMP2 -> HAND2,
  CIT-025). ENDO-TWIN keeps these edges, classed `literature_supported_topic_level`.
- Two dependencies executed without curated provenance in v0.6.0 (`PAR-003`,
  E2 -> proliferation; `PAR-004`, cAMP -> BMP2). They are classed
  `simplifying_assumption`.
- Only 37 of 247 active prototype evidence rows were graded from full text; none
  reached curation status `verified`.
