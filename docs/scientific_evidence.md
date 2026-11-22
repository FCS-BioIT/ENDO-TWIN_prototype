# Scientific evidence: from papers to predictions

ENDO-TWIN keeps a traceable chain for every executable rule:

**paper -> biological finding -> regulatory interaction -> Boolean function ->
simulated prediction -> experimental readout.**

| Link | Where it is recorded |
|---|---|
| Paper | `endotwin/evidence/references.tsv` (ET-xxx; corpus papers link to `context/literature/references.tsv` REF-xxx, DOI-checked by a test) |
| Finding | `finding_used_by_endotwin` column of the same table; for inherited edges, the prototype experimental evidence table `context/evidence/edge_experimental_evidence.tsv` |
| Interaction | `endotwin/models/endotwin-v0.2.0/edges.tsv`: one row per dependency, with sign, compartment crossing, evidence class, references, mechanism, assumption and the v0.1.0 edge it descends from |
| Boolean function | `endotwin/models/endotwin-v0.2.0/network.bnd` (default) and `rule_variants.tsv` (alternatives); `tests/mainline/test_model_integrity.py` requires the edge table to equal the dependencies derived from the rules |
| Prediction | `endotwin/results/endotwin-v0.2.0/fixed_point_predictions.tsv`, `comparison_directions.tsv`, `discrimination.tsv` |
| Readout | `endotwin/config/observation_map.tsv` |

## Evidence classes

Every dependency carries exactly one class (`edges.tsv`, column
`evidence_class`). The class says what kind of support exists, not how strong
the biology is in general.

| Class | Meaning | Count in the default network (47) |
|---|---|---|
| `literature_supported` | Primary literature supports the interaction in a relevant system | 13 |
| `literature_supported_topic_level` | Inherited from a prototype topic-level evidence record; where full-text graded, the cited papers did **not** demonstrate this specific edge | 5 |
| `literature_supported_species_transfer` | Supported in mouse only, applied to human | 3 |
| `literature_supported_contested` | Supported, but the subject of a competing hypothesis (Q1, FOX) | 2 |
| `literature_supported_route_unresolved` | The phenotype is supported; the intracellular route is not (IL-1β) | 3 |
| `adoc_supported` | Supported by ADOC observations (expression or secretion) | 6 |
| `experimental_definition` | Definitional effect of an experimental input on its target (ligand on receptor, inhibitor on its target) | 9 |
| `simplifying_assumption` | A modelling choice, stated as such (3 of them are secretion relays) | 6 |
| `alternative_hypothesis` | Present only in a rule variant | 3 (variant-only) |

## The rules most relevant to the grant questions

### Compartments and the shared extracellular space (new in v0.2.0)

ADOC separates organoid-derived epithelium and primary stroma by a porous
membrane (ET-020). The model therefore never lets a cell node read a node of the
other cell type: every signal passes through an extracellular node (`X_IHH`,
`X_BMP2`, `X_PARACRINE_MITOGEN`), and the measured secreted proteins (`X_PAEP`,
`X_PRL`, `X_IGFBP1`) sit there too. The secretion edges are classed
`simplifying_assumption`: they say a ligand reaches the other side, never how
much. They change no steady state and add a delay.

### Progesterone and oestrogen receptors

`E_PGR = IN_PROGESTIN`, `S_PGR = IN_PROGESTIN`, `E_ESR1 = IN_E2`,
`S_ESR1 = IN_E2`. The nodes are ligand-activated receptor activity, separate per
compartment so that a compartment-specific receptor perturbation stays
expressible. Evidence: the ADOC regimen (SOFIA-HT-001, in-house). E2 induction of
PGR expression is not represented. One progestin input still drives the
PGR-dependent module (`E_PGR`, `E_IHH`, `X_IHH`, `S_PGR`, `S_HAND2` share a
function); this inherited alias class is a limitation, not a finding.

### BMP-associated stromal decidualisation (Q1)

```
S_BMP2      = (S_PGR and S_PKA) or S_NR2F2          // BMP2 expression
X_BMP2      = S_BMP2                                 // secreted ligand (new)
S_BMP_SMAD  = X_BMP2 and not IN_BMPR_INHIBITOR       // receptor / SMAD1/5/8 activity
S_WNT4      = S_BMP_SMAD                             // new
S_CEBPB     = S_PKA                                  // new
OUT_STROMAL_DECIDUALIZATION
            = S_PGR and S_CEBPB and S_WNT4 and not S_JNK    // default, BMP required
            = S_PGR and S_CEBPB and not S_JNK               // variant, PGR sufficient
```

- Mechanism: BMP2 signals through BMP receptors to phosphorylate SMAD1/5/8;
  SMAD1/5 knockdown impairs human decidualisation (IGFBP1 and WNT4 fall) and
  BMP2 add-back rescues, in 2D and in assembloids (Liao et al. 2024, ET-013,
  read in full in the prototype's U4b). Recombinant BMP2 enhances human stromal
  differentiation on top of E2+P+cAMP and raises WNT4; Wnt4 knockdown blocks
  BMP2-driven decidualisation in mouse (Li et al. 2007, ET-008). cAMP increases
  C/EBPβ binding at the IGFBP1 and PRL promoters (Tamura et al. 2014, ET-011).
- What the model assumes: receptor availability and BMP antagonists are not
  represented; the inhibitor acts only on stroma. WNT4 is also regulated by IRF4
  (ET-027), which is not encoded.
- Prediction: under confirmed receptor inhibition (pSMAD1/5/8 and WNT4 down in
  both hypotheses), PRL and IGFBP-1 fall under the BMP-required rule and are
  unchanged under the PGR-sufficient rule.

### The decidual transcription module and the FOX family (new in v0.2.0)

```
S_FOXO1  = S_PKA and not IN_FOXO1_INHIBITOR
S_IRF4   = S_PGR and S_FOXO1
S_IGFBP1 = OUT_STROMAL_DECIDUALIZATION and S_FOXO1
S_PRL    = OUT_STROMAL_DECIDUALIZATION and S_IRF4     // default, PRL needs FOXO1
S_PRL    = OUT_STROMAL_DECIDUALIZATION                // variant, PRL FOXO1-independent
```

- Mechanism (all read in full in the prototype's PRL/IGFBP-1/FOXO1 unit): cAMP
  confines FOXO1 to the nucleus, progestin attenuating it only partially
  (Labied 2006, ET-021). FOXO1 binds the IGFBP1 promoter with PR, and its
  knockdown or inhibition lowers IGFBP1 in four concordant studies (ET-022 to
  ET-025). FOXO1 is required for PR binding at IRF4, and IRF4 knockdown
  attenuates PRL (Vasquez 2015, ET-027).
- Why PRL is a competing hypothesis: FOXO1 knockdown lowers PRL (ET-022), but
  a FOXO1 activity inhibitor leaves PRL unchanged (ET-024, a null at n=6), FOXO1
  alone is inert on the PRL enhancer (ET-026), and silencing with a siRNA that
  also hits FOXO3A raises PRL (ET-023).
- Prediction: a FOXO1 inhibitor lowers IGFBP-1 under every hypothesis and leaves
  the decidual programme on; PRL falls only under the default. Readouts: the
  existing PRL and IGFBP-1 ELISAs, or the RNA.
- Status: the inhibitor is a candidate WP2 perturbation, not in the funded
  protocol. The prototype refused this module because no ADOC perturbation could
  separate its nodes; the inhibitor and the planned RNA-seq now can.

### Hedgehog reception (new node in v0.2.0)

`S_HH_SIGNALING = X_IHH and not IN_SMO_INHIBITOR`, `S_NR2F2 = S_HH_SIGNALING and
S_PGR`. Human endometrium expresses IHH and its targets PTCH1 and GLI1 across the
cycle (Wei 2010, ET-009); partial stromal Smo loss defers implantation in mouse
(Harman 2011, ET-028). No human study shows that reception is required for NR2F2
(the prototype's GAP-014). The node was refused in the prototype as an exact alias; the
Smoothened inhibitor (candidate perturbation) gives it a determinant. Prediction:
SMO inhibition lowers GLI1/PTCH1 and NR2F2 but not BMP2 under the supplemented
regimen (cAMP backs BMP2 up), and lowers BMP2 and pSMAD1/5/8 under the hormone-
only regimen.

### Stromal regulation of epithelial proliferation (Q2)

```
S_HAND2             = S_BMP_SMAD or S_PGR
S_PARACRINE_MITOGEN = S_ESR1 and not S_HAND2                    // FGF9 expression
X_PARACRINE_MITOGEN = S_PARACRINE_MITOGEN                       // secreted mitogen
E_FGFR_ERK          = X_PARACRINE_MITOGEN
OUT_EPITHELIAL_PROLIFERATION
                    = E_ESR1 and E_FGFR_ERK                      // default, stromal relay
                    = E_ESR1 and E_FGFR_ERK and not S_HAND2      // variant, v0.5.1 representation
                    = E_ESR1 and not E_PGR                       // variant, epithelial-autonomous
```

- Mechanism: E2 drives epithelial proliferation through stromal, not
  epithelial, ERα in mouse tissue recombinants (Cooke et al. 1997, ET-029,
  abstract level). Progesterone induces stromal HAND2, which represses stromal
  FGFs; FGFR blockade (PD173074) lowers epithelial phospho-FRS2, phospho-ERK1/2
  and Ki67 in Hand2-deficient mouse uterus (Li et al. 2011, ET-005). In human
  stromal cells HAND2 siRNA raises FGF9 only (Murata et al. 2019, ET-007), which
  is evidence **against** an aggregate FGF node; the readout is FGF9 mRNA, but
  the node stands for the stromal mitogenic route.
- What the model assumes: no primary paper in the corpus supports the
  epithelial-autonomous route; it is included because Q2 requires the
  comparison. Whether epithelial ERα is needed beside the stromal route is not
  resolved here.
- Predictions: stromal HAND2 knockdown under the full regimen raises
  proliferation only under the stromal hypotheses; neutralising the mitogen
  during E2 priming lowers proliferation only under the stromal hypotheses;
  doing it during differentiation discriminates nothing. Readouts: Ki67, EdU,
  epithelial phospho-ERK1/2.

### Epithelial secretory differentiation

`OUT_EPITHELIAL_SECRETORY = E_ESR1 and E_PGR`, `X_PAEP = OUT_EPITHELIAL_SECRETORY`.
Evidence: ADOC observations (SOFIA-SC-001, SOFIA-EPI-001). Because MPA, cAMP and
XAV939 are applied together, the PAEP rise cannot be attributed to the progestin
alone. The published PAEP rise was used to construct this rule; agreeing with it
is circular, not evaluation.

### IL-1β (provisional, WP3/WP4)

```
S_IL1_SIGNALING = IN_IL1B
S_JNK           = S_IL1_SIGNALING
S_ERK1_2        = S_IL1_SIGNALING
OUT_STROMAL_DECIDUALIZATION = ... and not S_JNK                   // every Q1 variant
S_PGR = IN_PROGESTIN                                              // default, INF decidual-only
S_PGR = IN_PROGESTIN and not S_ERK1_2                             // variant, INF PGR depletion
```

- Mechanism: IL-1β impairs human stromal decidualisation, with PRL and IGFBP-1
  reduced (Frank et al. 1995, ET-014; Yu et al. 2019, ET-015; Taylor et al.
  2024, ET-016; Gnecco et al. 2023, ET-012). Taylor et al. place the effect on
  JNK; Yu et al. report rapid ERK1/2-dependent depletion of PR (and ERα) that
  ERK blockade restores. NF-κB was not added: the only source (Kalkhoven 1996,
  ET-017) is not endometrial.
- Evidence depth: the non-corpus IL-1β papers were read at abstract level and
  DOI-verified against Crossref on 2026-11-22; they were not read in full.
- Prediction: pSMAD1/5/8, HAND2, WNT4 and IRF4 separate the two routes
  (unchanged vs down), and epithelial phospho-ERK1/2 rises only under PR
  depletion; proliferation rises only if Q2 is stromal.
- Status: to be revised with the G2 data (Task 4.1). IL-1β exposure is not
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
