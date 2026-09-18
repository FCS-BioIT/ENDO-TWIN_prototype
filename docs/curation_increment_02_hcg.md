# Curation increment 2 — IN_HCG (open-access-first pass)

Date: 2026-07-28. Claim level: `discovery and access assessment`. **No evidence
assertion was created and no executable model file was modified.**

## Outcome

`IN_HCG` is **retained as an external/catalog input**. No global
`hCG → receptivity` rule was wired, and no relation reached claim-level
curation, because no domain yielded a readable primary study testing the
specific relation at the required resolution.

## Searches

Europe PMC, 2026-07-28. First pass: ten domain queries, unfiltered. Second pass:
the same ten filtered to `OPEN_ACCESS:Y AND HAS_FT:Y`, excluding review
publication types, sorted by citation count.

**The second pass failed as a curation instrument, and the reason is worth
recording.** Citation-sorting an open-access-filtered corpus returns
high-citation atlases, organoid-platform papers and single-cell surveys —
`PMC5410172` (Turco organoids), `PMC6209386` (placenta/decidua atlas),
`PMC7220805` (trophoblast organoids) recur across six of the ten domains. These
are excellent papers that do not test the specific relations. Sorting by
citations optimises for influence, not for relation-specificity, so the ranking
actively buried any targeted mechanistic study.

Domain hit counts before OA filtering ranged 17–3694, so the literature exists;
it is simply not concentrated in the open-access, highly-cited stratum. Several
of these relations (hCG→CD98, hCG+IL1B→trophinin) originate in 1990s–2000s
reproductive-endocrinology journals that predate routine PMC deposition.

## Per-domain classification

| # | domain | classification | basis |
|---|---|---|---|
| 1 | hCG → epithelial CD98/SLC3A2, CD9 | **no relevant primary evidence found (open access)** | 126 OA hits, none testing hCG regulation of CD98/CD9 in endometrial epithelium; top hits are exosome and atlas papers |
| 2 | hCG + IL1B → trophinin/TRO–TROAP–BYSL | **no relevant primary evidence found (open access)** | 373 OA hits dominated by unrelated TNF/IL-1 and tumour-microenvironment literature; the trophinin primaries are not in the OA stratum |
| 3 | acute hCG/LHCGR → ERK or AKT | **no relevant primary evidence found (open access)** | 273 OA hits, all ovarian, oncological or GWAS; none endometrial |
| 4 | chronic hCG → LHCGR desensitisation/internalisation | **no relevant primary evidence found (open access)** | 609 OA hits dominated by GPCR pharmacology guides — reviews by nature, usable only for onward discovery |
| 5 | hCG → LIF and integrin regulation | **no relevant primary evidence found (open access)** | 665 OA hits; top results are organoid and blastoid platform papers, not hCG perturbation studies |
| 6 | hCG → CDH1/CTNND1 apical redistribution | **no relevant primary evidence found (open access)** | 327 OA hits; trophoblast/atlas papers, no hCG-perturbation experiment |
| 7 | endothelial hCG effects (VEGF, VE-cadherin, CD146) | **no relevant primary evidence found (open access)** | 3694 OA hits, query too broad; needs endothelial-cell-specific re-scoping |
| 8 | hCG → MMP/TIMP balance | **no relevant primary evidence found (open access)** | 495 OA hits; platform and atlas papers |
| 9 | epithelial-to-stromal decidual signalling, IGFBP1 | **abstract-only candidate** | Jin 2025 (ADH-SEED-125) establishes the route at abstract level; full text paywalled |
| 10 | trophoblast-side hCG effects | **no relevant primary evidence found (open access)** | 1690 OA hits; organoid and exosome papers, no autocrine-hCG perturbation study |

"No relevant primary evidence found (open access)" means exactly that — the
open-access slice searched did not contain it. It is **not** a claim that no
evidence exists; domains 1–8 and 10 almost certainly have paywalled primaries.

## Decisions carried

**Direct stromal LHCGR signalling: not encoded.** Nothing accessible tests it.
Jin 2025, the one candidate touching a stromal readout, reaches IGFBP1 *through
the epithelium* — hCG → epithelial PGF2α → EREG/HB-EGF → IGFBP1. Reading "hCG
raises IGFBP1" as licensing a direct stromal hCG edge would be wrong, and that
paper is the specific reason.

**No LHCGR edge of any kind.** LHCGR is not mentioned in the Jin abstract and
was not shown to be tested. Applying hCG does not license an LHCGR relation.

**Acute versus chronic: not separable.** No accessible source states hCG
concentration or exposure duration for an endometrial relation, so the two
cannot be distinguished. They are therefore not collapsed into one rule — they
are simply both absent.

## Relations recommended for dynamic testing

**None.** The threshold is a small, falsifiable set of relations with claim-level
evidence, and no relation cleared it. Recommending dynamic tests for
abstract-level claims would repeat the XAV939 failure mode: variants that are
either unfalsifiable under existing protocols or discriminable only by
conditions ADOC never runs.

## What would change with the Jin 2025 full text

See `docs/paywalled_papers_needed.md` for the field-by-field list. In summary:
whether the PGF2α→ADAM17→EREG/HB-EGF steps are `direct` or
`composite_or_inferred` depends on whether ADAM17 was perturbed; whether the
inter-compartment edge is a transfer experiment or an inference depends on
whether conditioned medium or co-culture was used; whether **any** LHCGR edge is
licensable depends on whether LHCGR necessity was tested; and whether the route
belongs to the acute or chronic arm depends on the unreported dose and duration.

## Recommended ADOC measurements

Flagged for the experimental side, independent of the literature blockage:
PGF2α in outlet fluid; EREG and HB-EGF; ADAM17 activity or cleavage products;
**epithelial versus stromal LHCGR expression, measured separately**; IGFBP1
under hCG with and without epithelial co-culture; exposure-time dependence; and
hCG withdrawal and repeated-exposure response. The LHCGR compartment
measurement is the highest-value single experiment: it would settle the direct
stromal question that the literature currently cannot.

## Reference / assertion audit (live, re-run before closure)

| metric | value |
|---|---|
| canonical bibliography | 40 |
| seed-file records | 125 |
| overlap / genuinely novel | 17 / 108 |
| assertions | 294 (277 bibliographic, 17 in-house) |
| distinct references used | 30 |
| assertions per reference min/median/mean/max | 3 / 9.0 / 9.2 / 18 |
| exact duplicate assertions | 0 |
| repeated edge/reference pairs | 0 |
| seed duplicates by DOI / PMID / title | 0 / 0 / 0 |

Unchanged from increment 1 apart from the added seed, because no assertion was
created.
