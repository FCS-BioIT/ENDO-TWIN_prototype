# What the ADOC single-cell data can and cannot observe in v0.4

Status: observability layer, 2026-09-13. No model, rule, protocol or
calibration file was changed, no node was conditioned and no simulation was run.
Claim level: `structural` and `provenance`.

## Why an observability layer comes before conditioning

Conditioning model nodes on single-cell data is only defensible once two
separate questions are answered per node: whether scRNA can observe the state at
all, and — if it can — what is actually resolved by doing so. The second
question is the one a node name hides, and it is answered here for the first
time.

Artifacts: [`config/scrna_observation_map.tsv`](../config/scrna_observation_map.tsv)
(59 rows, one per model node), generated and re-validated by
`src/dt_adoc/scrna/observability.py`, and
[`config/external_data_manifest.tsv`](../config/external_data_manifest.tsv),
which records the deposited object as an external asset.

**The object is deliberately not committed and not placed under `data/`.** It is
2.9 GB, and this repository has a shared remote and an external-bundle export
path. `config/data_manifest.tsv` keeps its invariant that every row is a file
actually present here; external assets live in the second manifest, which
records the URL, the verified digest and an `inspection_state`. That state is
currently `structurally_verified_not_integrated`, and the distinction is
enforced by `tests/unit/test_external_data_manifest.py`: verifying that a public
object exists, hashes correctly and contains what the paper says is a
**provenance** fact and licenses no model claim. Promotion to
`integrated_as_active_constraint` requires a row that actually activates it, and
no such row exists.

## The deposited object, structurally verified

Previously the repository held only the 61,843-cell intermediate and recorded,
correctly, that it carries no final annotation. The paper's final object is
public and has now been fetched and **parsed with R and SeuratObject**, not
token-scanned:

| Property | Value |
|---|---|
| Source | ArrayExpress `E-MTAB-15842`, `seurat_object.rds` |
| Size | 2,877,048,290 bytes |
| sha256 | `504a674db978779b03d02a73224ee425ec46efbf411c148b0903ceef15389a1a` (recomputed locally) |
| Class / dimensions | `Seurat`, 78,724 features x **28,212 cells** |
| Assay layers | `counts`, `data`, `scale.data` |
| Reductions | `pca.unintegrated`, `umap.unintegrated`, `pca.chip.unintegrated`, `pca.chip.harmony`, `umap.chip.harmony` |
| `meta.data` columns | `sample_id`, `orig.ident`, `celltype_v2`, `RNA_snn_res.0.5`, `RNA_snn_res.0.6` |
| Verified with | R 4.5.3, SeuratObject 5.4.0, in an environment OUTSIDE the project's pixi lock |

Cell counts match the manuscript exactly, per sample and per population:

```
SZ09TE_CNT 5605   SZ09TE_HT 3408   SZ10TE_CNT 6412
SZ10TE_HT  4253   SZ25TE_CNT 6742  SZ25TE_HT  1792      total 28212

Luminal-like epithelium 8857   HT epithelium I 4197   Stroma        4181
Cycling epithelium      3922   HT epithelium II 3465  HT stroma     3225
Myofibroblast            365                                 total 28212
```

### Three findings that change how this object may be used

**1. The `counts` layer is not raw counts.** Its values are non-integer
(minimum `3.3e-17`, maximum `328.45`), i.e. decontX-corrected. The accession's
file names confirm this (`*_decontx_feature_bc_matrix_filtered_matrix.mtx`), as
does the pipeline's `envs/decontx.yaml`. Any method that assumes integer UMI
counts — negative-binomial differential expression, most pseudobulk summation,
count-based normalisation — is misapplied on this layer. Raw counts are
available, but separately, as the per-sample
`*_raw_feature_bc_matrix_matrix.mtx` / `*_filtered_feature_bc_matrix_matrix.mtx`
files in the same accession.

**2. Donor and condition are recoverable, but only from `sample_id`.** The
deposited `meta.data` is much slimmer than the local intermediate's: there is no
`patient_id`, `group`, `mitoRatio`, `scDblFinder_RNA.score` or
`integrationCovariates`. Donor (`SZ09`/`SZ10`/`SZ25`) and condition
(`CNT`/`HT`) parse deterministically from `sample_id`, so donor-aware
aggregation is possible; per-cell QC covariates are not available for modelling.

**3. The population labels are near-deterministic in condition.** This is the
most consequential finding for evidence roles:

| `celltype_v2` | CNT | HT | % HT |
|---|---:|---:|---:|
| Luminal-like epithelium | 8786 | 71 | 0.8 |
| Stroma | 4147 | 34 | 0.8 |
| Cycling epithelium | 3372 | 550 | 14.0 |
| Myofibroblast | 282 | 83 | 22.7 |
| HT epithelium I | 879 | 3318 | 79.1 |
| HT epithelium II | 698 | 2767 | 79.9 |
| HT stroma | 595 | 2630 | 81.6 |

Stratifying by `celltype_v2` and then contrasting HT against CNT is close to
contrasting a variable with itself. Three of the seven labels are *named* for
the treatment, and the counts show the naming is nearly literal.

### How the 28,212 cells were selected

Read from `src/scrnaseq-preprocess/qc.R` in the same public pipeline: cells are
kept at `nFeature_RNA >= 500`, `mitoRatio < 15`, `nCount_RNA >= 1000`, then
multiplets are removed with `scDblFinder`. A further exclusion happens at the
annotation stage, where `RNA_snn_res.0.5` cluster 9 is dropped outright.

These thresholds are the paper's, not ours, and they are recorded here because
they define what population the 28,212 cells represent. They are not re-derived
and no alternative filtering is applied: reclustering or refiltering would
produce a comparison of the model against our reanalysis, reported under a
heading that promises the paper's populations.

### How `celltype_v2` was produced

Read from the paper's own public pipeline (`FCS-BioIT/single-cell-ADOC`,
`src/annotation/annotation.R`), not inferred. It is a **manual cluster-to-label
assignment**, principally over `RNA_snn_res.0.5`, with two labels taken from
`RNA_snn_res.0.6` and `RNA_snn_res.0.5` cluster 9 dropped entirely. `celltype_v2`
then *coarsens* an earlier `celltype`: "Decidual stroma" and "Non-decidual
stroma" are merged into "HT stroma", and "Stromal" is renamed "Stroma".

Two consequences worth recording. `celltype_v2` is a derived analytical product
and a human judgement, not a measurement — so it is not a neutral stratifier.
And because the assignments are applied as ordered overwrites across *two*
clustering resolutions, it is not a clean function of any single clustering; a
cell in both `res.0.6` cluster 7 and `res.0.5` cluster 7 takes the later
assignment. That is the pipeline's business, not ours, but it bounds how
reproducible the stratification is.

The pipeline also defines a `celltype_general` that bakes the treatment group
into the label ("Epithelium HT" vs "Epithelium No-HT"). It is **not** present in
the deposited object, and it should not be reconstructed for any HT-vs-CNT
comparison.

## Measurement reach versus model reach

These are two different systems and the map keeps them in separate columns,
because an earlier revision of this analysis collapsed them and got the
conclusion backwards.

Of 59 nodes, **27 have some scRNA observability and 32 have none**. Those 27
observable states realise only **9 distinct Boolean signatures** under v0.4:

| v0.4 signature class | Observable members | What v0.4 can represent |
|---|---:|---|
| `AC01` epithelial secretory | 7 | one value for all 9 class members |
| `AC02` stromal decidual | 5 | one value for all 6 class members |
| `AC03` progesterone response | 5 | one value for all 5 class members |
| `AC04` LIF / GP130-STAT3 | 3 | one value for all 3 class members |
| `AC05` apical anti-adhesive | 3 | one value for all 3 class members |
| `E_ESTROGENIC_PROLIFERATION` | 1 | independently |
| `E_KLF12_HIGH` | 1 | independently |
| `S_FGF_MITOGENIC` | 1 | independently |
| `S_HAND2` | 1 | independently |

**The correct reading, and it is the opposite of a limitation on the data:**

> 27 named biological states have some scRNA observability, but the v0.4 rule
> set compresses them into 9 native Boolean signatures. **v0.4 cannot
> independently represent much of the biological variation the data could
> measure.**

That is a representational deficit in the model, not a ceiling on the assay.

### Why the earlier framing was wrong

A previous revision said an observation "resolves the CLASS, not this node" and
that conditioning one member "conditions the others identically". Both are
false, and the error mattered because it blamed the measurement for the rules.

- **The measurement separates them.** PRL and IGFBP1 are separately
  quantifiable transcripts in different cells. If they diverge experimentally,
  the measurement has not failed to resolve them — **v0.4 has failed to
  represent them**, and the divergence *falsifies the aliasing*.
- **Function equality is not interventional equivalence.** Clamping `S_PRL`
  overrides only `S_PRL`'s rule; `S_IGFBP1` computes from its own and is
  unaffected. This repository demonstrates the asymmetry in its own numbers:
  **`E_CD98_CD9` is phenotype-inert while `E_GP130_STAT3`, in the same function
  class `AC04`, is not.** Identical natural dynamics, different consequence
  under intervention.

Two corollaries that survive the correction:

- `S_PRL` and `S_IGFBP1` cannot be given distinct temporal behaviour by better
  measurement. Only a **rule change** can lift that, and the data are what would
  justify making one.
- Seven observable nodes are **phenotype-inert** — `E_CD98_CD9`, `E_HBEGF`,
  `E_IHH`, `E_MUC1_SLEX`, `E_SPP1_EXPR`, `S_NR2F2`, `S_SPP1`. Clamping any
  changes no `OUT_` node in any of the 524,288 enumerated states, so an
  observation on them is real data that cannot reach any prediction *through
  this model*.

### How a measurement could actually be applied

`conditioning_compatibility` records the mechanics, and the answer is stark:

| | nodes |
|---|---:|
| `istate_prior` — takes a measured prior directly | **1** |
| `rule_override_required` — "conditioning" means editing the rule | 26 |
| `not_applicable` — not observable | 32 |

A free variable takes an initial-state prior. A derived node does not: its value
is computed, so applying a measurement to it means overriding its rule, which is
a model edit and one that *decouples* it from its function class rather than
moving the class together.

### The one high-value target

`E_KLF12_HIGH` is the single `istate_prior` row. It is simultaneously a
**hand-set free variable**, in a class of size one, not phenotype-inert, and
observable by a direct transcript present in the object. It is a bare `FALSE` in
`baseline.cfg` with nothing behind it, and of the five hand-set free variables
the other four are interface relays with no cellular correlate.

Replacing that value with a measured donor × condition × cell-type detection
fraction would be the first free variable in this model constrained by data. It
is deliberately **not** done here: it needs a pre-registered threshold and a
leakage rule, because the same cells must not both set the prior and score a
prediction that depends on it.

> **Since resolved, and the answer is no.** That pre-registration was written
> ([`scrna/klf12_prior_preregistration.md`](scrna/klf12_prior_preregistration.md))
> and the analysis run
> ([`scrna/klf12_prior_finding.md`](scrna/klf12_prior_finding.md)). **These data
> do not establish a measured prior for `E_KLF12_HIGH`** — which is a statement
> about what the measurement can identify, not a finding that no KLF12-high
> state exists in the tissue. 83.2% of epithelial cells carry no KLF12, and of
> the 3,429 that do, 65.5% carry exactly one raw UMI.
>
> **No interpretable high/low boundary comes out of that.** A two-component
> mixture on the detected values does fit, and whether it passes M1(a) depends
> on which reading of one frozen sentence is applied: the implemented rule says
> no, and the two readings closer to the pre-registered wording both say yes, at
> boundaries of 1.06 and 1.17 transcript-equivalents. F3 is loose in the same
> way and pulls the other way, so **the pre-registered decision branch is not
> uniquely determined** — crossing the two ambiguities reaches GO,
> CONDITIONAL_GO and NO_GO alike, and the artifact commits the whole grid.
> Nothing was activated under any cell.
>
> What rules a measured prior out under every cell is calibration, not wording:
> all three M1(a) readings, and M1(b), also pass on a population simulated with
> **no latent state at all**, 25 times out of 25. A criterion that fires on
> stateless data is not measuring a state. That calibration covers M1(a) and
> M1(b) only — M1(c) and the falsifiers need per-unit structure the null does
> not model — so the supported claim is about the M1(a) criterion, not about the
> whole battery. The multimodality the detected values have is the integer UMI
> lattice: eight modes at 0.57, 0.97, 1.91, 2.79, 3.77, 4.72, 5.92 and 6.88
> transcript-equivalents.
>
> **The raw-UMI sensitivity the pre-registration allows was run** and agrees
> ([`scrna/klf12_raw_umi_findings.json`](scrna/klf12_raw_umi_findings.json)):
> on integer counts **65.5% of detected cells carry exactly one UMI** and the
> median detected value is one molecule in every one of the six units. No
> latent-state model is fitted there — an earlier revision compared a
> two-component gamma-Poisson mixture against a single-rate model by BIC, and
> that analysis was **removed** because the likelihood is multimodal, three
> successive fitters each returned a demonstrable non-maximum, and the reported
> gain moved +17.0 → +10.24 → +21.52 as the search was hardened. It was never
> load-bearing. What the counts do show, model-free: thinning to the lowest unit
> median (14,503 UMIs) and recounting on **the cells that were actually
> matched** cuts the between-unit spread in KLF12 detection from 0.330 to
> 0.229, and reverses the HT-versus-CNT sign within donor `SZ25` (+0.102 crude,
> −0.118 depth-matched) — the same reversal §3 found by standardisation on the
> corrected layer, here from counting raw molecules with no model.
>
> The scheme is named rather than implied: the artifact records
> `depth_matched_scheme_for_per_unit: matched_cells_only`, because thinning
> cannot raise a cell already below the target, so keeping every cell would
> leave an unthinned remainder and compare units at different depths after all.
> The cost is real and runs **opposite to the intuition**: the unmatched
> (dropped) share is **4.1% for `SZ25TE_HT`**, which keeps 1,346 of its 1,404
> cells, against **36.3–50.0% for the other five**. The deep unit retains
> almost everything; the shallow units pay. Read that column before leaning on
> the matched comparison.
>
> It also corrects a claim an earlier revision of this passage made — the
> sub-one values are *not* decontX residue of cells that carried nothing. All
> 2,251 such epithelial cells carried at least one real KLF12 molecule, 2,247
> of them exactly one, and none carried zero.
>
> Three further findings, all **post-hoc** — the pre-registration named none of
> them as a falsifier. The pooled 75th and 80th percentile thresholds are
> exactly zero, so two of the five sensitivity parameters degenerate into bare
> detection. The per-unit estimate is not identified: the HT-versus-CNT
> difference changes sign depending on whether sequencing depth or epithelial
> subtype is adjusted for, and both adjustments put 20–43% of their weight on
> strata of 3–38 cells. And the "donor × condition × `celltype_v2`" aggregation
> this table proposes is itself part of the problem — it was replaced by a union
> over the epithelial labels; see that row's `aggregation` column.
>
> Conditioning was executed as a declared arbitrary-threshold sensitivity sweep.
> Its only finding is structural: at the converged horizon every tracked
> quantity is the two-extreme mixture `(1-p)·value(0) + p·value(1)`, to within
> 6.0e-4. Note the form — the special case "the unconditioned value scaled by
> `1 - prior`" holds for most `OUT_` nodes but **not** as a class: it is false
> for `E_KLF12_HIGH` itself, for `E_ITGAVB3_5`, whose `E_SECRETORY_STATE`
> disjunct survives the LIF gate closing, and for `OUT_STROMAL_DECIDUALIZED`,
> which reads 1.000 at p = 1 in the hormone-treated arm because no path from
> the conditioned node reaches it. Nothing was activated.

## Evidence roles, decided per measurement

Not blanket-assigned. An earlier revision marked every observable row
`same_dataset_internal`, which was exactly the circularity `AGENTS.md` forbids:
`config/evidence_roles.yaml` places `P1-EPI-STATE`, `P1-STR-STATE`,
`P1-IHH-BMP` and `P1-SPP1` in the **construction** role, and
`context/phase1-readouts.tsv` records what each observed. The scRNA detection of
PRL and IGFBP1 in HT stroma is `SOFIA-SC-002` — a construction record — so it
cannot afterwards be cited as same-dataset concordance for the nodes it built.

The rule is now derived from those records rather than judged per row: a
measurement whose features appear in a construction readout is `construction`.

| role | rows | meaning |
|---|---:|---|
| `construction` | 11 | these features BUILT the model; never citable as concordance |
| `same_dataset_internal` | 16 | a different feature of the same 28,212 cells |
| `not_applicable` | 32 | not observable |
| `held_out` / `external` | 0 | unavailable in this repository |

The 11 construction rows are `E_IHH`, `E_PAEP`, `E_PGR`, `E_SECRETORY_STATE`,
`E_SPP1_EXPR`, `S_BMP2`, `S_DECIDUALIZED`, `S_IGFBP1`, `S_NR2F2`, `S_PRL` and
`S_SPP1`. The loader refuses any row that uses a construction feature while
claiming a weaker role.

No row is `held_out` or `external`, and that follows from where the data sit:
these are the study's own cells. Promotion to `held_out` needs a different chip,
assay or experiment; `external` needs a different dataset.

## What this does not do

- It conditions nothing and fits nothing. No prior is set, no node is clamped.
- It does not license reclassifying the concordance rows R17-R27. Those rows say
  the *repository* does not hold the annotated object; that statement is about
  the repository and is addressed by obtaining the object, which is a separate
  change with its own tests.
- It says nothing about whether a conditioned model would predict adhesion
  better. Nine constrainable degrees of freedom is an upper bound on what can be
  informed, not evidence that informing them helps.
