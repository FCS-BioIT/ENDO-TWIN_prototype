# Paywalled papers needed for curation

Papers that curation is blocked on, with the specific extraction fields each
would unblock. Access was attempted through Europe PMC, PMC and the publisher
before a paper was listed here.

Providing a PDF (or an institutional proxy) turns each of these from an
abstract-only seed into a curatable claim-level assertion.

## Resolved — full text supplied, no longer blocking

### Jin et al. 2025 — hCG → epithelial PGF2α → EREG/HB-EGF → IGFBP1

- **PMID** 40398806 · **DOI** 10.1016/j.mce.2025.112581 · *Molecular and Cellular
  Endocrinology* 606:112581
- **Resolved 2026-07-29.** Full text supplied by the owner, all 13 pages figure-rendered,
  registered as **REF-059** / **PDF-028**. Seed `ADH-SEED-125` moved to
  `full_text_or_relevant_results_inspected`.
- Adjudication: `docs/curation_increment_06_somkuti_jin.md`.

**All seven blocking fields are answered there.** The headline resolutions:

| blocking field | answer |
|---|---|
| hCG concentration and exposure duration | 0.2 and 5 µg/mL, for **1 h** and **6 h** — acute only, no chronic arm; only 5 µg/mL is reliably active. Dose physiologicality is **not** assessable (µg/mL only, no IU, no origin stated) |
| epithelial cell source and culture system | Ishikawa (Cell Bank CAS Shanghai), 2D, unpolarised. **No primary cells or organoids anywhere** |
| stromal cell source and decidualization protocol | ATCC CRL-4003, 250 µM db-cAMP + 1 µM MPA for 1, 2 or 4 d |
| whether ADAM17 was perturbed | **Not at all.** No siRNA, no TAPI-0/TAPI-2/marimastat, no activity assay — and the single blotted band is the ~120 kDa **pro-form**, not the mature enzyme. The step stays `composite_or_inferred` |
| conditioned medium vs co-culture | **Genuine non-contact coculture** (coverslip on pillars), better than either alternative anticipated. The inter-compartment step is `direct` |
| whether LHCGR was tested | **Neither expression nor necessity. `LHCGR` occurs zero times.** Resolves as *untested*, not as evidence of absence — so it does **not** upgrade the standing decision, and no LHCGR edge is licensed |
| figure/table/results locations | recorded per claim in the increment-6 document |

**Both conditionals this entry set out resolve negatively.** The `uncertain_rule_variant`
upgrade required ADAM17 perturbation **and** a real transfer experiment; the transfer half is
satisfied and the ADAM17 half is not, so the route stays `catalog_only`. The `IN_HCG → LHCGR`
edge is still not licensable.

Registration yielded **zero executable relations** — the fourth consecutive increment in which
hCG does. The reason is computed rather than cautious: every faithful Boolean encoding of the
route is inert against the current network, because `S_IGFBP1` reduces to `progestin and cAMP`,
which is exactly what Jin holds ON in every stromal experiment.

### Somkuti et al. 1997 — EGF and sex steroids on ITGB3 in Ishikawa

- **PMID** 9215293 · **DOI** 10.1210/jcem.82.7.4102 · *J Clin Endocrinol Metab* 82:2192-2197
- Never listed here, because it was never in the corpus in any form. Supplied together with Jin
  on 2026-07-29 and registered as **REF-058** / **PDF-027**.
- **Note for anyone re-requesting it:** Crossref carries a **second, duplicate DOI**,
  `10.1210/jc.82.7.2192`, which resolves to the canonical one and must not be used — the manifest
  and registry join on DOI, so the alias would mint a second id for an already-registered paper.

### Yu et al. 2018 — ST3Gal3/sLeX and endometrial receptivity

- **PMID** 30220088 · **DOI** 10.1002/1873-3468.13252 · *FEBS Letters* 592(21):3696-3707
- **Resolved 2026-09-17**, during U4b. Requested because it is one of the two references
  `E_GLYCOSYLATION_PROGRAM` and `E_SLEX_SURFACE` rest on; supplied by the owner the same day
  and read in full. 32 pages, sha256
  `1c488edc3042391adf4a8b2d517a077242784f19d51983354abfc83e13ccfd7d`.
- **Not registered**, deliberately: U4b allocates no `REF-*` id and writes no
  `pdf_manifest.tsv` row, because registration is curation and U4b is an adjudication unit.
  The digest above is the checkable record. Registering it later is legitimate and changes
  no U4b conclusion.
- **What it decided**, recorded in
  `context/literature/reviews/deep_research_adhesion_model_2026-09-11.primary-verification.tsv`
  (`U4B-DRREF-005`): it shows the `E_GLYCOSYLATION_PROGRAM` node's definition is **not
  established** — it names ST3Gal3 as "the key enzyme", reports no ST3Gal4 difference between
  cycle phases and measures no FUT3 at all, so it supports one enzyme rather than a
  co-regulated programme. **Yu 2018 alone does not refute the node**, and an earlier revision
  of this entry said it did: falsifying transcript co-regulation among selected enzymes is not
  falsifying the existence of a functional glycosylation state, and at the time **Ma 2023 —
  the reference covering the FUT3 half of the definition — was still unread**. On that
  evidence the candidate was `RETAIN_CATALOG_ONLY` / `DEFINITION_INSUFFICIENT`, not `REJECT`.
- **SUPERSEDED 2026-09-18 — the verdict above is U4b's, not the live one.** Ma 2023 has since
  been read and registered (REF-077 / PDF-049, ledger row `BSR-DRREF-006`, entry below), and
  it measured **both** named enzymes in the same cells under the same stimulus moving
  significantly in **opposite** directions. `E_GLYCOSYLATION_PROGRAM` is now **`REJECT` /
  `SEMANTICS_REFUTED`** at §5(0-refuted), scoped to the definition. Yu 2018's own findings
  are unchanged and are not what moved; what changed is that the silence Yu left on FUT3 was
  filled, against the definition. `E_SLEX_SURFACE` is unaffected and stays
  `RETAIN_CATALOG_ONLY`. See `docs/curation_increment_08_blocked_sources.md`.
- Yu 2018 **supports**
  `E_SLEX_SURFACE`'s core claim by three orthogonal perturbations, with three limits: every
  human experiment is in RL95-2/JAR carcinoma lines, the in vivo arm is mouse, and ST3Gal3
  knockdown also reduced proliferation, so adhesion loss is entangled with viability.

### Ma et al. 2023 — sLeX, IL-1β and trophoblast adhesion

- **PMID** 36648484 · **DOI** 10.1093/biolre/ioad007 · *Biology of Reproduction*
  108(4):564-574
- **Resolved 2026-09-18**, in the blocked-source refresh. Supplied by the owner and
  found in the main checkout's gitignored library; 11 pages, version of record, sha256
  `13a1e0352fafad24f666a2112fd6108dea2b3a685645a20d14bad51c283a7f97`. Read in full and
  **registered as REF-077 / PDF-049** — unlike Yu 2018, because this is a curation
  increment rather than an adjudication-only unit.
- Adjudication: `docs/curation_increment_08_blocked_sources.md`; claim-level record
  `context/literature/reviews/blocked_source_refresh_2026-09-18.primary-verification.tsv`
  (`BSR-DRREF-006`).

**All four blocking fields are answered, and three of the four answer against the
paper's usefulness for promotion.**

| blocking field | answer |
|---|---|
| (a) primary epithelium or organoid, or a cell line? | **RL95-2 only** — and it is the *same* carcinoma line as Yu 2018, so the two references are **not** independent system support. No primary cells, no organoid |
| (b) is there a viability control? | **None at all.** No CCK-8, no EdU, no MTT, no apoptosis assay, no cell-count normalisation. Yu *measured* a proliferation effect of ST3Gal3 knockdown in this same line, so Ma's 72 h FUT3 knockdown and 4 d IL-1β exposure **inherit that confound unmeasured**. `DRUNR-010` applies. The anti-sLeX blockade arm — 1 h pretreatment, 2 h coculture — is the exception and is the paper's cleanest evidence |
| (c) graded or switch-like? | **Neither is established.** One concentration, 20 ng/mL, throughout. No dose-response, so **no Boolean threshold and no `or` disjunct asserting sufficiency is licensed**. There is also no FUT3 overexpression arm, so FUT3 is shown necessary and **not** sufficient |
| (d) is IL-1β a state ADOC varies or could vary? | **No.** The deposited contrast sets `IN_E2`, `IN_PROGESTIN`, `IN_cAMP` and `IN_XAV939` together and `config/protocols.yaml` records no single-agent arm. **No `X_IL1B` and no `IN_IL1B` input was created** |

**What it decided, and the two candidates move in opposite directions.**
`E_SLEX_SURFACE` gains the determinant §5(2) was missing — and gains it *for the right
variable*, because IL-1β raises surface sLeX measured **as surface sLeX** by flow
cytometry, so the activity-versus-abundance test that defeated `S_FOXO1`, `E_SOX17`
and `E_ITGA2B1` does not fire. Its first failing criterion moves **§5(2) → §5(4)** with
the disposition unchanged at `RETAIN_CATALOG_ONLY`. `E_GLYCOSYLATION_PROGRAM` is
**`REJECT`ed**, scoped to its definition: the two enzymes its label conjoins were
measured together, in the same cells under the same stimulus, and move **significantly
in opposite directions** (FUT3 up *p* < 0.001, ST3GAL3 down *p* < 0.05). The human-tissue
FUT3/IL1B association (GSE98386, *r* = 0.72) is **correlational bulk tissue** and cannot
localise IL1B to the epithelium, so it supports physiological relevance and not human
epithelial causality.

### Zhou et al. 2021 — JAG1 and endometrial receptivity

- **PMID** 34252231 · **DOI** 10.1096/fj.202100590R · *FASEB Journal* 35(8):e21784
- **Resolved 2026-09-18**, in the same refresh. 28 pages, sha256
  `17c81107f6a5224045eeefba4b7f95146fdcd0d15a878b1486b33c83fce33e9c`, **registered as
  REF-076 / PDF-048**.
- **Provenance caveat, recorded because it is checkable:** the file is the **accepted
  author manuscript** deposited in Minerva Access (University of Melbourne), *not* the
  publisher version of record. Its internal citation line gives the Wiley alias
  `10.1002/FSB2.21784` rather than the canonical DOI, and the repository's own header
  drops the "1" from "Jagged1". It is registered `published` because the paper is
  published; every figure reference in the ledger row is to the manuscript.
- Adjudication: `BSR-DRREF-007` in the same ledger.

| blocking field | answer |
|---|---|
| (a) cell system for the functional experiments | **Primary human endometrial epithelial cells (HEECs, n = 5)** *and* Ishikawa — the best human system of any candidate read in U4b or this increment. But **Figure 2's own legend confines** HEY1, HES1, all seven receptivity markers, PGR, ESR1 and the entire MAML1 arm to **Ishikawa**; the primary-cell evidence is Fig 1A, Fig 1C and Fig 3B only |
| (b) adhesion endpoint | **HTR8/SVneo trophoblast cell-line spheroid**, not a blastocyst or blastoid |
| (c) pathway activity or transcript abundance? | **Activity.** NOTCH1–4 NICD by cleaved-domain-specific immunoblot with densitometry — which is what a node defined as a signalling state requires. NOTCH3 NICD falls (*p* < 0.05, Ishikawa); **NOTCH1 and NOTCH2 NICD rise significantly**. The primary-cell replication is a **non-significant trend, *P* = 0.073, n = 3** (Fig 3B legend), although the Results text and Abstract call it "confirmed" — **the legend governs** |
| (d) **is any hormonal or contextual input to JAG1 perturbed?** | **No. None, anywhere.** No E2, no progestin, no cAMP, no cytokine. The only upstream statement is observational cycle-phase immunostaining from the authors' prior work |

**So U4b's prediction held exactly.** Obtaining the paper moved the **node** off
`EVIDENCE_UNVERIFIED` to `WAIT_FOR_EXPERIMENT`; it moved the **encoding** not at all.
`DRUNR-005` is now **confirmed by the source** rather than inherited: **no
`IN_P4 → JAG1`, no `IN_E2 → JAG1` and no `E_SECRETORY_STATE → JAG1` is licensed.**

One further null worth keeping: four of the five JAG1-regulated receptivity markers —
LIFR, ITGB3, MAOA, IGFBP1 — **survive MAML1 knockdown**, so they are Notch-*independent*
outputs of JAG1 and must not become downstream edges of `E_JAG1_NOTCH3`. Only **SPP1**
is canonical-Notch-dependent, and it is registered as a candidate relation at *that*
specificity — never as a NOTCH3-specific edge, because MAML1 is shared by all four
receptors and no NOTCH3 perturbation exists.

## Blocking now

### 1. Huang et al. 2009 — tankyrase/AXIN mechanism for XAV939

- **PMID** 19759537 · **DOI** 10.1038/nature08356 · *Nature*
- Access: paywalled; abstract inspected only. Already promoted to the canonical
  bibliography as **REF-039** because its identity is Crossref-verified and its
  abstract states the mechanism explicitly.
- Curation impact: **low**. The abstract states target, direction and mechanism
  unambiguously, and the paper tested no reproductive tissue, which is the fact
  the model relies on. Listed for completeness rather than because it blocks a
  decision.

## Tier 1 — likely decisive for a proposed relation

### Lack of evidence for functional LHCGR in non-pregnant endometrium
- **DOI** 10.1101/2022.01.05.474837 · bioRxiv preprint, 2022 · seed `ADH-SEED-126`
- Status: **primary paper identified, full text needed** (preprint; check for a
  peer-reviewed version first)
- Why decisive: reports a **negative** result on functional LHCGR in
  non-pregnant endometrium. The model currently declines a direct endometrial
  LHCGR edge on *absence of positive evidence*. If this holds, the decision
  upgrades to *evidence of absence*, which is a materially stronger footing and
  would justify recording LHCGR relations as **rejected** rather than merely
  uncurated.

### Expression and function of LHCGR in human endometrial stromal cells
- **PMID** 35597810 · PMC9124191 · seed `ADH-SEED-127`
- Status: **primary paper identified, full text available (open access)**
- The direct counterpart to the preprint above. Together they should settle the
  direct-stromal-LHCGR question in one bounded curation pass. **No PDF needed.**

### Mechanism of human chorionic gonadotropin in endometrial receptivity
- **PMID** 36912344 · PMC11895872 · seed `ADH-SEED-128`
- Status: **primary paper identified, full text available (open access)**
- Candidate source for acute hCG signalling relations. **No PDF needed.**

## Tier 2 — useful for directness, timing or compartment

### Intrauterine hCG and endothelial adhesion molecules
- **PMID** 33903941 · PMC8553705 · seed `ADH-SEED-129`
- Status: **primary paper identified, full text available (open access)**

## Excluded — retracted, must not re-enter curation

- **PMID 39561163** (PMC11575823) — retraction of "Human Chorionic Gonadotropin
  β Induces Migration and Invasion". Recorded as `ADH-SEED-130`,
  `edge_review_status=rejected_retracted`.
- **PMID 38550158** — "Retracted: Trophinin Is an Important Biomarker…".

Both surfaced during relation-specific searching and are logged so a later
search cannot silently reintroduce them.

## Domains with no primary source located yet

The remaining hCG domains (CD98/CD9, trophinin/IL1B, LHCGR→ERK/AKT, chronic
desensitisation, LIF/integrins, CDH1/CTNND1, endothelial, MMP/TIMP,
trophoblast-side) have **no specific paywalled paper identified yet**, because
open-access-filtered searching did not surface targeted primary studies for
them — see `docs/curation_increment_02_hcg.md` for the per-domain
classification. Requesting PDFs for those requires first identifying the right
primaries, which is a search problem rather than an access problem.

## How to supply

Drop PDFs into an untracked local directory (for example `tmp/papers/`, already
gitignored) and say so. PDFs must not be committed — only the extracted,
attributed claim-level assertions and the bibliographic record belong in the
repository.
