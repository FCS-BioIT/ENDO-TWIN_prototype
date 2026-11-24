# Experimental data

What ADOC data exist, how far their provenance can be trusted, how the prototype used
them, and what ENDO-TWIN will add. Counts are recomputed by
`src/endotwin/foundation_metrics.py`; the details come from the committed
tables and the prototype provenance records named in each section.

## 1. Published ADOC regimen

Zaragozano et al. 2026, *Sci Adv* 12:eadz2249 (in-house; `data/sciadv.adz2249.pdf`),
encoded as SOFIA-HT-001 and in `endotwin/config/protocols.yaml`:

| Phase | Medium | Duration |
|---|---|---|
| E2 priming | 10 nM E2 | 48 h |
| Hormone treatment (HT) | 10 nM E2 + 1 uM MPA + 250 uM 8-Br-cAMP + 10 uM XAV939 | 96 h |

The HT effect is a combined effect of an oestrogen, a synthetic progestin, a
cAMP analogue and a WNT pathway inhibitor. It is never attributed to ovarian
hormones alone.

## 2. Functional and molecular measurements

Source workbook `data/proteinas secretadas ADOC.xlsx` (immutable), canonical
table `input_tables/adoc_secreted_proteins.tsv` (62 rows), validation report
`input_tables/adoc_secreted_proteins_validation.md`, provenance
`config/adoc_chip_donor_provenance.tsv`, compartment attribution
`docs/c2_observation_compartments/attribution_report.md`.

| | PRL | IGFBP-1 | PAEP |
|---|---|---|---|
| Assay | ELISA (Boster EK0593; manuscript Methods) | ELISA (Raybiotech ELH-IGFBP1-1; manuscript Methods) | ELISA per the manuscript Methods (Abcam ab275904); **the source workbook does not name the assay** |
| Rows | 18: 10 observed, 8 no detectable secretion | 30: 19 observed, 11 no detectable secretion | 14: 10 observed, 4 missing |
| Conditions | Days 0, 3, 6 of the HT protocol; no untreated arm | Days 0, 3, 6 | Two protocol phases: E2-only and full HT; no untreated arm, no day-0 control |
| Compartment | Basal outlet only; stromal-attributed | Apical and basal; compartment-ambiguous | Outlet not verified in the source data (OM-001); glandular or global secretory readout |
| Unit of replication | 6 positional columns; chip mapping **lost** (LOST-002); at most 3 chip families | 10 positional columns; chip mapping **lost** (LOST-001) | 7 chip headers, 5 with values |
| Donors | Manuscript: 3 independent donors for PRL/IGFBP-1 and PAEP. The repository cannot reconstruct donor identity per value: donor_id is empty in all 62 rows, and PAEP has at most 2 epithelial source groups | | |
| Use in the prototype | Provisional mapping; onset-order mapping rejected | Diagnostic only (non-inversion, 3 of 5 units) | Feasibility constraint OM-001 (full HT > E2-only); circular for evaluation |

A chip is not an independent biological replicate: chips can share donors, and
epithelium and stroma in one chip can come from different donors.

### Known provenance inconsistencies (recorded, not resolved)

1. PAEP timing: the manuscript Methods mention collections on days 2 and 6;
   the repository records that no sampling day is assignable to the two
   workbook rows (SOFIA-COMM-007).
2. The PAEP condition label in the workbook names the progestin as "P4" with
   XAV939 and omits cAMP; the true composition is MPA + cAMP + XAV939.
3. IGFBP-1 at day 0: the manuscript reports no detectable levels; 5 of 10
   day-0 workbook values are detected.
4. Six PRL values below the manuscript's 10 pg/mL detection limit are labelled
   observed; the detection limit column is empty.
5. The registered PAEP readout says "HT versus untreated", but there is no
   untreated PAEP arm.
6. Manuscript chip and donor counts (for example 5 chips from 3 donors) cannot be
   reconciled with the recoverable chip mapping.

## 3. Embryo adhesion: prototype only, not ENDO-TWIN data

The ADOC paper also reports stable embryo adhesion (untreated 0/12, HT 9/19,
HT + 10 uM mifepristone 1/8; 39 embryos). The prototype used these counts as an
ordinal diagnostic and held out the mifepristone arm. ENDO-TWIN does not use
them, to build the model or to validate it:

- **They cannot separate the hypotheses.** Under untreated, HT and HT plus
  mifepristone (modelled either as progesterone receptor activity forced off in
  both compartments or as progestin removal), every node of `endotwin-v0.3.0`
  reaches the same steady state in all 48 rule-variant scenarios
  (`AdhesionConditionsAreUninformative` in
  `tests/mainline/test_structure_and_hypotheses.py`). Any readout computed from
  the steady state, an adhesion proxy included, is therefore identical for the
  Q1, Q2, inflammation and FOX variants in these conditions.
- **They cannot validate.** The proposal's validation is a perturbation withheld
  from development, with frozen predictions, in five new donors. The untreated
  and HT arms were already used as prototype diagnostics, the held-out arm has
  already been compared (prototype model 0 against 1/8 observed), and the units
  are embryos whose chip and donor mapping cannot be recovered.
- **No new adhesion data are planned.** The proposal plans no embryo
  experiments and no adhesion readout.

The prototype record is kept as legacy material (`docs/endpoint/`,
`docs/c3_kinetic_readouts/`, `docs/legacy/README.md`).

## 4. Single-cell transcriptomics

Accession **E-MTAB-15842** (the paper's annotated Seurat object; 2.9 GB, not
committed; SHA-256 pinned in `config/external_data_manifest.tsv`). Aggregates
from `docs/phase2a/scrna_metadata_extraction.json` (metadata read inside R; no
expression layer read):

| | |
|---|---|
| Cells | 28,212 |
| Donors | 3 |
| Samples | 6: control (CNT) and hormone-treated (HT) per donor |
| Epithelial cells | 20,441 (luminal-like 8,857; HT epithelium I 4,197; cycling 3,922; HT epithelium II 3,465) |
| Stromal cells | 7,771 (stroma 4,181; HT stroma 3,225; myofibroblast 365) |
| Cell-state labels | 7 |

The cell-state labels are almost determined by condition (for example,
luminal-like epithelium is 0.8% HT), so a state signature partly encodes the
treatment.

Analyses that used these data (all pre-registered, none changed a rule):

- **Node-support audit** (`docs/scrna/node_support_finding.md`): 12 primary
  compartment-units pass every QC gate. The LIF/GP130/CD98 alias class is
  rule-challenged, the epithelial secretory class alias-challenged.
- **KLF12 prior** (`docs/scrna/klf12_prior_finding.md`): no measured prior can
  be set; 83.2% of epithelial cells carry no KLF12 transcript.
- **RNA-endpoint concordance** (`docs/rna_endpoint_concordance/report.md`, v0.5.1):
  of 27 RNA-observable nodes, 0 concordant, 0 discordant, 1 circular agreement
  (`E_PAEP`, a construction analyte), 2 with no response within two-fold, the
  rest mixed or not scored.
- **Personalization contract** (`docs/phase2a/`): numerical mapping blocked;
  Phase 2B found no suitable external reference (`docs/phase2b_c4/PHASE2B_CLOSED.md`).

Relevance to ENDO-TWIN: hormone-treated stroma expresses BMP2 (SOFIA-SC-002),
which supports the BMP2 expression rule but says nothing about SMAD activity.
Transcript abundance is not pathway activity: pSMAD1/5/8 must be measured.

## 5. Construction versus evaluation

| Role | Data |
|---|---|
| Construction (fixed how the model reads data or what a state means) | The regimen; scRNA expression programmes (SOFIA-SC-001/002); PAEP, PRL and IGFBP-1 as markers of the programmes they now read out |
| Calibration or diagnostic (constrain or check, no magnitude fitted) | PAEP (OM-001); IGFBP-1 (OM-002) |
| Evaluation only | RNA-endpoint concordance (excluding the circular `E_PAEP`) |

No ADOC measurement has been used for prospective validation of either prototype
or ENDO-TWIN.

## 6. Planned ENDO-TWIN data and their interfaces

Nothing below exists yet. Planned per the proposal: 79 chips (24 WP1, 10 WP2,
15 WP3, 30 WP4) from 14 donors without known pathology (G1, G2) and 5
patients with ovarian endometriosis (G3); 42 compartment-resolved bulk RNA-seq
libraries from 21 chips (24 in WP1, 18 in WP3); protein and functional readouts
(PRL, IGFBP-1, PAEP, Ki67/EdU, pSMAD1/5/8, viability and compartment integrity).

| Interface | File | Enforces |
|---|---|---|
| Bulk RNA-seq sample sheet | `endotwin/config/data_schemas/bulk_rnaseq_samples.yaml` | Pseudonymised donor codes; group G1/G2/G3; compartment; analysis role |
| Functional measurements | `endotwin/config/data_schemas/functional_measurements.yaml` | Observed, below detection, missing and excluded stay distinct and agree with the value column; readouts must be in the observation map |
| Deconvolution output | `endotwin/config/data_schemas/deconvolution_estimates.yaml` | Estimates are `relative_state_contribution`, never absolute fractions, and sum to at most 1 per library |
| Leakage guards | `src/endotwin/data_interfaces.py` | WP2 evaluation donors never appear in development; G3 data never enter WP4 selection |

Planned analysis path (WP1, Task 1.3): derive cell-state signatures from
E-MTAB-15842, deconvolve compartment-resolved bulk libraries (for example with
CIBERSORTx), and compare the relative contribution of decidualising stromal and
secretory epithelial states across conditions with the functional readouts, through
`RO-BULK-DECID` and `RO-BULK-SECR` in the observation map. Two cautions apply.
The reference states are condition-confounded, so a hormone-treated reference
state is partly defined by the treatment it would be used to detect. And an
inferred proportion is not a measured cell fraction. Validate with
`pixi run endotwin-validate-data <schema> <table>`.

The Duempelmann et al. 2026 endometriosis atlas (466,371 cells) is planned as a
construction and consistency reference. Agreement with it is consistency, not
independent validation.
