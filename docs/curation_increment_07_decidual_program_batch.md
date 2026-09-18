# Curation increment 7 — 14 new full-text PDFs, decidual-program batch

Date: 2026-07-30. Claim level: `full-text triage, bibliography registration,
citation retraction and claim-level adjudication`. **No executable model file was
modified. `network.bnd` is untouched, no rule changed, no rate or initial
condition changed, and every model artifact except the generated
`edge_evidence_assertions.tsv` is byte-identical to its pre-increment state,
verified by `sha256sum -c` against a baseline captured before the first edit.**

Seven independent reviewers examined the batch: literature, systems biology,
provenance, MaBoSS modelling, ADOC data, workflow and validation. Where they
disagreed, the disagreement is recorded below rather than resolved by fiat.

Four tiers, kept separate because they have different truth conditions:

| Tier | Count | Truth condition |
|---|---:|---|
| Bibliography registration | 11 | the paper exists, was read in full, and its identifiers resolve |
| Full-text upgrade | 2 | an already-registered paper's `key_use` now reflects its full text |
| Deferred | 1 | accepted-but-unedited manuscript; no identifier minted |
| Citation retraction | 10 | the cited paper does not contain the claim |
| Citation attachment | 3 | the paper does support a relation it was not cited on |
| Evidence gap recorded | 4 | a contradiction exists that no edge can carry |
| **Executable-model promotion** | **0** | see "Tier 4" |

---

## Inventory

Fourteen full-text PDFs. Twelve were new to the corpus; two were already
registered from abstract-level metadata and had never had a manifest row.

Manifest rows PDF-029 … PDF-042. Every sha256 and page count was computed from
the file, not asserted. All 14 hashes are unique and collide with none of the 28
existing rows. No PDF is tracked by git; `context/literature/pdfs/` stays
gitignored.

## Registered: 11, REF-060 to REF-062 and REF-064 to REF-071

| ref | paper | why it registers |
|---|---|---|
| REF-060 | Huang 2022, eLife | SOX4/HERC4/PGR protein stability; siHERC4 rescue |
| REF-061 | Tamura 2014, Endocrinology | C/EBPβ and H3K27ac at the IGFBP-1 and PRL promoters |
| REF-062 | Murata 2019, Reprod Biol | the only **human** HAND2-restrains-FGF evidence in the corpus |
| REF-064 | Tanaka 2001, Gynecol Endocrinol | IL-11 acts only on already-decidualised stroma |
| REF-065 | Gnecco 2023, Med | epithelial–stromal co-culture platform; orthogonal stiffness control |
| REF-066 | Paria 2001, PNAS | local bead sufficiency; BMP2 beads an explicit null |
| REF-067 | DeLoia 1998, Hum Reprod | human luminal MUC1 protein persists at receptivity |
| REF-068 | Horne 2006, Reproduction | progesterone raises MUC1 — but PR-independently |
| REF-069 | Schatz 1986, J Steroid Biochem | epithelial PGF2α competence is oestrogen-driven |
| REF-070 | Wang 2023, Kaohsiung J Med Sci | registered to make a conflict queryable, not to license an edge |
| REF-071 | Jin 2026, Mol Hum Reprod | embryo-conditioned epithelial transcriptome, one donor |

### Deduplication was proven, not asserted

All 14 DOIs were resolved against Crossref and matched against the PDF; all 14
sha256 hashes and all 13 determinable PMIDs were checked against the existing
corpus. **Zero DOI, PMID or hash collisions.** Title similarity for the 11 new
registrations ranges 0.94–1.00, all above `TITLE_SIMILARITY_FLOOR = 0.65`, so no
new resolution warning was introduced; the single warning remains the
pre-existing REF-006 abbreviated title.

### The two Wang and the two Jin traps

Author-name coincidence carries no deduplication signal. Two near-collisions were
checked explicitly and are **different papers**:

- REF-056 is Wang 2023 *Developmental Cell* `10.1016/j.devcel.2023.08.004`;
  REF-070 is Wang 2023 *Kaohsiung Journal of Medical Sciences* `10.1002/kjm2.12672`.
- REF-059 is Jin **2025** *Molecular and Cellular Endocrinology* `10.1016/j.mce.2025.112581`;
  REF-071 is Jin **2026** *Molecular Human Reproduction* `10.1093/molehr/gaaf062`.

The DOI and PMID deduplication tests would catch a merged row. They would **not**
catch a correct `key_use` written into the wrong row, which is why both pairs are
named here.

### REF-063 is permanently vacant

Lin 2026 was pre-assigned REF-063 before its publication form was established.
It deferred, so no identifier was minted. The gap is deliberate and is the first
in the sequence. Nothing enforces contiguity — `check_bibliography` and the
`REF-\d{3}` scraper are both order-blind — and a REF id is a content address
inside `ASRT-<edge>-<REF-id>`, so density has no value. Renumbering was
considered and rejected: it would have required rewriting 19 prose
cross-references embedded in adjudication rationales, gap rows and `key_use`
text, which is the same class of careless reference handling this increment
exists to correct.

## Full-text upgrades: REF-026 and REF-028

Neither acquires a new identifier. Both acquire their first manifest row.

**Only `key_use` was rewritten, plus REF-026's empty `pmid` cell (→ 17590085).**
`species` and `compartment` were deliberately left untouched:
`src/dt_adoc/evidence/assertions.py` copies both into every assertion row and
**derives `species_transfer_required` from the species text**, so editing either
would have rewritten the generated assertion table inside a commit that claims no
model file changed.

## Deliberately not registered: 1

**Lin 2026, *Endometrial gland secretome maintains the homeostasis of
decidualization*, J Mol Cell Biol `10.1093/jmcb/mjag023`.**

The PDF carries the OUP vertical watermark reading `ORIGINAL UNEDITED MANUSCRIPT`
down the left margin, the download path is `academic.oup.com/jmcb/advance-article/`,
Crossref returns null volume and page, and the body still carries a bare
"Running title:" line. This is the same form as PDF-011 (Huang 2026, NDRG2) and
PDF-015 (Mo 2026, ENTPD3), both recorded `deferred_unedited_manuscript`.

**Four of the seven reviewers reached this independently, by three different
routes** — watermark decoding, URL inspection and Crossref metadata. None
dissented. Manifest row PDF-034 carries `publication_status = accepted_unedited`,
`ref_id = ""`, `registration_decision = deferred_unedited_manuscript`.

This is a costly deferral and the cost is recorded honestly: Lin's Figure 1 is the
**most model-relevant single result in the batch** — 17 of 25 canonical in-vitro
decidualisation markers, *including PRL and IGFBP1*, fail to distinguish
proliferative from secretory stroma in the Garcia-Alonso in-vivo atlas. That
result directly challenges this model's only two stromal outputs, and it is
stranded behind the deferral until a version of record exists.

## Tier 3 — candidate signalling relations

| relation | class | blocker |
|---|---|---|
| `S_PGR → S_SOX4 → S_FOXO1 → decidual program` | catalog-only | composes to `S_FOXO1 ≡ S_PGR`; measured no-op |
| `SOX4 ⊣ HERC4 ⊣ PGR protein` | unresolved | Huang states no direct SOX4 binding on HERC4 was observed |
| `S_cAMP → S_CEBPB_COMPETENCE → IGFBP1/PRL` | catalog-only | absorbed; Tamura reports the two genes behaving *identically* |
| `S_HAND2 ⊣ FGF9 → ANGPT2` (human) | catalog-only | no vascular compartment; 5 of 6 FGFs explicit nulls |
| gland-secretome homeostatic brake | deferred | source is an unedited manuscript; effect size absent from text |
| local `IL11 → decidual-cell survival` | catalog-only | no survival axis; survival never measured (XTT only) |
| `hCG → epithelial PI3K/AKT/eNOS` | rejected | see "Contradictions" |
| embryo-conditioned signal → epithelial remodelling | catalog-only | no ligand identified; n=1 endometrial donor |
| glandular vs luminal epithelial split | rejected | no compartment-selective input exists in the free-variable set |

## Tier 4 — executable-model promotion: 0, and the reason is computed

The MaBoSS reviewer applied each candidate to the network and enumerated **all
2^18 = 262,144 assignments of the free variables** — exact, not sampled, because
the network is a strict DAG over its inputs. Every proposed module produced
**zero output changes in zero declared conditions**.

The reason is a degeneracy the batch incidentally exposed and which two reviewers
derived independently:

```
E_PGR ≡ E_IHH ≡ S_PGR ≡ S_NR2F2 ≡ S_BMP2 ≡ S_HAND2 ≡ IN_PROGESTIN ∧ ¬IN_MIFEPRISTONE
```

The `∨ S_NR2F2` disjunct in `S_BMP2` swallows the cAMP requirement, so the entire
PGR→IHH→NR2F2→BMP2→HAND2 relay — six named nodes across two compartments, the
exact architecture this batch was expected to strengthen — is one Boolean
function. Anything hung off `S_PGR` is an alias by construction.

**The registered biology is real; the Boolean encoding of it is degenerate.**
Those are different findings and the literature and systems-biology reviewers
disagreed precisely because they were answering different questions. Huang's
PGR→SOX4→FOXO1 chain is directly evidenced — PGR ChIP-qPCR plus luciferase for
SOX4, SOX4 ChIP-qPCR plus knockout and overexpression for FOXO1 — and inserting
it as a node changes nothing in any state. Both are recorded.

`models/baseline/adoc-core-v0.1.0/network.bnd` already carried `S_FOXO1 = S_PGR
and S_PKA`, `S_CEBPB = S_PKA` and `S_IL11 = S_BMP2`, and v0.3.0 removed them for
this reason. Promoting the proposed layer would reinstate nodes this repository
has already demoted once.

## Citation retractions: 10

The full texts expose a fan-out defect of the same kind CIT-001…CIT-024 closed
elsewhere. Two mouse references had been cited across an entire evidence topic
rather than onto the relations they actually support. Term counts are from the
full text:

| directives | edges | reference | evidence |
|---|---|---|---|
| CIT-025…029 | LE044, LE045, LE092, LE093, LE094 | REF-026 Kurihara | `HAND2` occurs **0** times, `FGF` **0** times |
| CIT-030…032 | LE003, LE040, LE041 | REF-028 Li | `Ihh` twice, both reporting it *unaffected*; `Nr2f2` once, *unchanged* |
| CIT-033, 034 | LE043, LE048 | REF-028 Li | `Bmp2` occurs **0** times, `COUP` **0** times |

The result is a clean swap: REF-026 is now cited only on the IHH/NR2F2/BMP2
edges, REF-028 only on the HAND2/FGF edges. **Obtaining the full text is what
exposed this** — it was invisible at abstract level, and it is the most valuable
outcome of the increment.

## Citation attachments: 3

- **CIT-035** attaches **REF-062 (Murata)** to **LE092** (`S_HAND2 ⊣
  S_FGF_MITOGENIC`), which until now rested entirely on mouse REF-028. This is
  the only human evidence for the relation in the corpus. Mandatory
  `context_dependence` note: **only FGF9 moved**; FGF1, FGF2, FGF7 and FGF18 were
  measured in the same experiment and did not.
- **CIT-036 / CIT-037** attach **REF-067 (DeLoia)** and **REF-068 (Horne)** to
  **LE013** (`E_SECRETORY_STATE ⊣ E_MUC1_BARRIER`) as contradictions, marked
  `direction_supported = contradicted`, `curation_status = disputed`.

## Contradictions and nulls retained explicitly

**1. The MUC1-off rule does not transfer to human.** DeLoia used CT-1 against the
glycosylation-independent cytoplasmic tail: human luminal MUC1 protein is present
at every cycle phase including mid-luteal and two conception cycles. The apparent
secretory-phase loss is **ectodomain masking by keratan sulphate and sialic acid,
fully reversed by keratanase or neuraminidase** — which simultaneously validates
`E_MUC1_SLEX`. Horne is the second hit from the opposite direction but is weaker
than it appears: the progesterone effect is **equally strong in PR-negative
HEC1B**, is concentration-independent across four log units, and measures total
cellular rather than apical MUC1. Recorded as **GAP-011**. The honest position is
not "progesterone raises MUC1" but "the mouse-derived rule does not transfer and
human regulation is unresolved."

**2. Paria 2001 contradicts Kurihara 2007 on IHH→BMP2, mouse against mouse.**
Paria states that "the lack of temporal and spatial correlation between Ihh and
Bmp2 expression suggests that the later gene is not a target of hedgehog
signaling in the uterus," and reports *Ihh* unchanged at the attachment site.
Kurihara builds its model on Ihh→NR2F2→BMP2. Both are strong. Not resolved.

**3. Li 2011 contradicts Kurihara 2007 on LIF.** *Lif* is significantly reduced
in Hand2-null uteri; LIF is unchanged in the NR2F2 mutant by both qRT-PCR and
immunocytochemistry.

**4. Schatz 1986 against Jin 2025 (REF-059) on PGF2α.** Recorded as **GAP-012**
rather than an adjudication, because REF-059 is cited by zero edges and
`test_expression_only_references_support_no_relation` pins that. Schatz shows
progesterone **inhibits** epithelial PGF2α, in primary separated epithelium under
a chronic 64 h oestrogenic stimulus with no progestin; REF-059 sites an
hCG→PGF2α→decidualisation relay in a progestin-dominant context in immortalised
lines. Different stimulus, cells and compartment resolution — Schatz does not
refute Jin, but it establishes that the hormonal precondition for epithelial
PGF2α competence is **oestrogenic, not progestational**.

**5. What counts as "receptivity".** Wang 2023 operationalises endometrial
receptivity as *increased* epithelial proliferation; Li 2011 and Kurihara 2007
require proliferation to *cease*. Recorded as **GAP-013**.

## Where the reviewed conclusions needed correcting

- The parent pre-assigned REF-063 to Lin 2026 before its publication form was
  established. Corrected: no identifier is minted for a deferred manuscript.
- The parent raised the enumeration ceiling as a possible hard blocker on adding
  any input node. **Refuted:** `MAX_ENUMERATION_STATES = 2**22`, which admits 22
  free variables against the model's 18.
- The workflow reviewer reported REF-026 and REF-028 as cited by 8 edges each.
  The actual fan-out was **11 each**; the three missed edges (LE093, LE094,
  LE095) are exactly the dead FGF/proliferation edges.
- One reviewer proposed attaching REF-070 to LE095 as a contradiction and flagged
  its own reservation. **Not applied.** Wang's proliferation is hCG-driven rather
  than estrogenic, and its in-vivo arm is a mifepristone-induced mouse — obtained
  under the very perturbation the model encodes as `IN_MIFEPRISTONE`. GAP-013
  carries the conflict instead.

## Data-integrity flags found in the sources

- **Huang 2022:** Key Resources Table gives MPA at 1 µM, Methods text gives 1 mM
  — a 1000-fold discrepancy. db-cAMP misnamed "dibutyl cyclophospsinoside".
- **Tamura 2014:** the Abstract claims C/EBPβ knockdown *completely* abolished
  the mRNA induction; Fig 2B marks those bars `a,b`, i.e. still significantly
  above control. The inhibition is **partial**.
- **Murata 2019:** Results list six FGFs analysed including FGF4; Fig 1 has five
  panels and no FGF4 panel.
- **Horne 2006:** Table 3 lists progesterone at 10⁻¹⁰/10⁻⁹/10⁻⁶ M while Tables
  1–2 and both figures use 10⁻¹⁰/10⁻⁸/10⁻⁶ M.
- **Lin 2026:** secretome treatment is 7 days in Results, six in Methods; RT-qPCR
  validation cross-referenced to the KEGG panel; mouse decidual stimulus given as
  "25 µg of sesame oil" (unit error for µl).
- **Wang 2023:** the dual-luciferase specificity control is mis-specified —
  `PIK3R2-mut + mimics-NC` where `PIK3R2-mut + miR-126-3p mimics` is required, so
  the binding-site claim is not established. Two contradictory administration
  routes in one Methods paragraph. In-vivo hCG dose given only as "2.5 µl" with
  no concentration. Fig 1B reports a CD146 blot with no anti-CD146 antibody in
  the list. Abstract says EECs were used "for in vivo experiments".
- **Jin 2026:** KEGG "Wnt signaling" and "neutrophil extracellular trap
  formation" are both reported as significant at adjusted P = **0.082221**, above
  the paper's own stated 0.05 threshold, yet the Abstract, Discussion and
  Conclusion are built on them. Only the two cytoskeletal/ciliary GO terms are
  genuinely significant.
- **Schatz 1986:** the PDF text is heavily OCR-degraded; several dose figures
  were reconstructed and should be re-checked against the printed page before
  being quoted.

## Prohibitions — what these papers must NOT be used to encode

1. **No `S_SOX4` or `S_FOXO1` node.** Both compose to exact aliases of existing
   states. Measured: zero output changes across all 262,144 assignments.
2. **No `S_CEBPB_COMPETENCE` node fitted to the ADOC IGFBP-1/PRL timing.** That
   would fit topology, rates and outcome interpretation on the same 48 cells that
   produced OM-002/006/014/015/016 — strictly worse than the R12/R15 circularity
   the reproducibility matrix already flags. Tamura also reports the two genes
   behaving identically, so the asymmetry would be invented.
3. **No transition rates.** The repository declares none, `compile.py` states
   their omission is intentional, and `test_the_model_declares_no_transition_rates`
   asserts their absence. Differential PRL/IGFBP1 onset is documentation-only.
4. **No hard Boolean veto for the gland secretome.** Lin's effect is
   dose-proportional attenuation with both arms significantly above control, and
   co-culture without the inducer has no effect at all.
5. **No fifth anonymous relay.** An attenuating gland brake would require one
   whose `istate` probability is the entire content of the claim, with nothing in
   the source fixing its value.
6. **No individual FGF edges.** No individual FGF was ever perturbed in Li 2011;
   in Murata only FGF9 moved while four others were explicit nulls. Family-level
   aggregation matches the actual experiments; four edges would manufacture
   resolution neither paper has.
7. **No HB-EGF edge from Li 2011.** *Hbegf* mRNA rises in Hand2-null stroma but
   activated ErbB1 and ErbB4 are **undetectable in the epithelium of both
   genotypes**; the paper concludes it did not act on the epithelium.
8. **No PI3K/AKT epithelial proliferation arm.** Li 2011 explicitly excludes it
   (p-AKT undetectable and unaltered), which would put two registered references
   in unadjudicated conflict.
9. **No `PGR → MUC1` edge.** Horne's effect is PR-independent.
10. **No `IL1B → epithelial MUC1` edge.** Complete null at protein and promoter
    level in both lines.
11. **No glandular/luminal split.** No input in the free-variable set is
    compartment-selective, so both states would be driven by identical
    antecedents and would be unobservable.
12. **No ligand edges from secretome, EV or enrichment membership.** Lin's WNT7A
    and CSF1 come from an N=2 re-analysis of a previously published dataset and
    were never perturbed; Gnecco's stromal mediator is never identified; Jin 2026
    identifies no ligand at all.

## Not done, deliberately

- No `candidate-nodes.tsv`, `candidate-edges.tsv` or `mechanisms.tsv` row was
  added or edited. Their `refs` columns feed `complete_nodes.tsv`,
  `complete_edges.tsv` and `modules.tsv` through `superset_family`, so editing
  them would mutate committed model artifacts inside a curation increment.
- No `context/evidence-register.tsv` `location` was edited beyond what the
  adjudications require.
- No seed rows created. None of the 14 papers appears in
  `searches/adhesion_routes_seed.tsv`, and a paper already in hand does not
  belong in a discovery backlog.
- No figure regenerated. The executable network did not change, so re-rendering
  could not change what the figures depict.
- `compile-models`, `smoke`, `render-structure` and both `render-dynamics` tasks
  were deliberately not run.

## Stale counts corrected

- `docs/model_evidence_audit.md`: "the bibliography is now 59/59" → **70/70**
- `docs/results_reproducibility_matrix.md`: "the 59-entry bibliography" → **70-entry**
- `docs/evidence_schema.md`: current assertion table 274 → **267**
- `docs/visualization.md`: "0 of 274 assertions" → **0 of 267**
- `tests/unit/test_pdf_manifest.py`: cited-DOI overlap 26 → **39**
- `tests/unit/test_pdf_manifest.py`: unedited set gains `"Lin et al."`

Dated statements inside increments 5 and 6 are left as written, per the precedent
those increments set. Increment 6's claim that the cited-DOI overlap is "the only
count-sensitive assertion in the suite" is **now false** — the unedited-manuscript
set is a second one, and it only became count-sensitive when a manuscript was
first deferred.

## Recommended next

1. **`IN_HAND2_LOSS`** is the one executable change this literature supports.
   It was **not** part of this increment and was delivered separately as
   `models/superset/adoc-literature-superset-v0.4.0`; the paragraph below is the
   analysis that justified it and is left as written. It is a boundary perturbation input, off by
   default, that de-aliases `S_HAND2`, makes `S_FGF_MITOGENIC` load-bearing, and
   fires the previously unreachable `E_ESTROGENIC_PROLIFERATION` veto —
   reproducing the Li 2011 dissociation in cmaboss (`OUT_EPITHELIAL_RECEPTIVE`
   0.9996 → 0.0000 with `OUT_STROMAL_DECIDUALIZED` 0.9996 → 0.9998). It belongs
   in a separate model increment as
   `models/superset/adoc-literature-superset-v0.4.0/`, alongside a frozen v0.3.0.
2. **`IN_NR2F2_LOSS` was tested and rejected** as phenotype-inert: the
   `(S_PGR ∧ S_PKA)` disjunct keeps BMP2 on under ablation, so it raises
   `distinct_functions` by 3 while flipping zero outputs. It is a worked example
   of why de-aliasing alone is an insufficient promotion gate.
3. **Break `S_BMP2 ≡ S_PGR`.** This is a defect fix, not new biology, and it is
   the precondition for the whole stromal arm becoming testable. Kurihara 2007 is
   a substantially better evidential fit for a required-conjunct BMP2 rule than
   anything previously considered — it has both the conditional knockout and the
   intraluminal BMP2 add-back — but the rescue's completeness, dose, n and
   endpoint need a dedicated check first.
4. **Add conditions that vary progestin, cAMP and E2 independently.** Costs no
   topology change. Until they exist, the declared suite collapses to a
   **26-node** alias class and cannot distinguish the epithelial secretory arm
   from the stromal decidual arm at all.
5. **Replace the non-aliasing acceptance criterion.** `len(alias_classes) must
   not increase` is malformed: splitting one 5-member class into a 3 and a 2
   reduces degeneracy while raising the count. Use `nodes − distinct_functions`.

## Validation performed

| Command | Result |
|---|---|
| `pixi run verify-citations` | rc=0, **resolved 70/70**, `citations_intact`, zero errors. One warning, the pre-existing REF-006 abbreviated title; no new warning introduced |
| `pixi run test` | rc=0, **474 tests OK**, 0 failures, 0 errors, 0 skips |
| `pixi run lint` | rc=0 |
| `pixi run format-check` | rc=0 |
| `pixi run harness-check` | rc=0 |
| `pixi run validate-models` | rc=0 |
| `pixi run validate-evidence-assertions` | rc=0, **274 → 267 rows**, zero validator errors |
| `pixi run profile-parity` | rc=0 |
| `check_data_manifest.py --check-hashes` | rc=0 |
| `sha256sum -c` against pre-change baseline | 27 of 28 artifacts byte-identical; the single expected change is the generated `edge_evidence_assertions.tsv` |

Claim-level biological support across the model remains **0/267**. Registration
is not verification.
