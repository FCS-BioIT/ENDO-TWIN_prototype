# Literature curation

How the prototype literature work was done, what it produced, and how to read its
numbers. All counts are recomputed by `src/endotwin/foundation_metrics.py`.

## Workflow (as practised in the prototype)

1. **Discovery.** Structured seed searches by mechanism (129 candidate records,
   75 unique DOIs; `context/literature/searches/adhesion_routes_seed.tsv`) and
   two deep-research staging rounds (`context/literature/staging/`).
2. **Screening.** A 156-article bundle (2026-10-21), of which 147 were screened
   into tiers A (52, direct rule relevance), B (80, contextual) and C (15); 42 by
   focused full-text inspection, 105 at index or abstract depth
   (`context/literature/reviews/adoc_2026-10-21_147_paper_screen.md`).
3. **Full-text reading and figure-level verification.** 64 papers are in the PDF
   manifest, 62 marked full-text inspected, with SHA-256 of each PDF
   (`context/literature/pdf_manifest.tsv`). One paper was excluded as retracted
   (Zhang 2020, ALK3-SMAD).
4. **Registration.** 95 references in the canonical registry, all with unique
   DOIs, all 95 resolved against Crossref on 2026-09-28
   (`context/literature/references.tsv`, `citation_verification.tsv`).
5. **Edge-level evidence.** One row per (edge, paper, experiment): 276 rows; 247
   active on 85 edges, citing 35 papers. 37 active rows were graded from full
   text on a rubric of experimental strength, human/ADOC relevance and edge
   support (`context/evidence/edge_experimental_evidence.tsv`,
   `docs/evidence_grading.md`). Best graded support per edge: direct 5, partial
   8, not demonstrated 14.
6. **Adjudication.** 39 citation adjudications after full-text reading: 32
   papers retracted from edges they did not support, 7 attached
   (`config/edge_citation_adjudications.tsv`).
7. **Re-audit.** A literature-to-model reconciliation report (2026-09-28)
   states a 163-PDF corpus and enumerates a 36-paper active evidence set: 20
   core, 10 rule-variant, 1 boundary, 5 reviews
   (`context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md`). Its
   recommendations C1 and C5 were implemented as v0.5.2; C2-C4 and D1-D8 were
   deferred with reasons. The 163-paper list itself is not committed; only the
   report and its 36-paper set are verifiable here.
8. **Independent review.** A 2026-11-18 scientific review produced 74
   assessments, of which 15 were accepted into the canonical evidence and 2 new
   citations attached (`docs/scientific_review_2026-11-18/`).

## Reading the counts correctly

- **Screened is not used.** 147 papers were screened; 35 papers are cited in the
  active edge evidence of v0.6.0.
- **The corpora overlap and were never deduplicated.** The 163-PDF archive, the
  156-article bundle and the staging rounds share papers. Their counts must not
  be summed.
- **Cited is not demonstrated.** 74 of 85 declared v0.6.0 edges cite at least
  one non-review primary paper, but of the 27 edges graded from full text, only
  5 have direct support.

## Rules changed by the literature

| Change | Version | Source |
|---|---|---|
| C1: PAEP removed from the receptivity output (it is a secretory marker) | v0.5.2 | re-audit section 4.1 |
| C5: HAND2 acts on epithelial proliferation only through the stromal relay | v0.5.2 | re-audit section 4.1 |
| `S_BMP2 -> S_HAND2` citation (Kurihara 2007) retracted | v0.6.0 evidence | CIT-025 |
| Mouse-only HAND2 -> FGF relation gains its human counterpart (Murata 2019), which also shows that only FGF9 responds | v0.6.0 evidence | CIT-035 |

Three times, the largest available structural gain was refused because the
evidence did not support it (U3, U4, U4b; `docs/v05_mechanistic_integration_plan.md`).

## Evidence added for ENDO-TWIN

`endotwin/evidence/references.tsv` lists 20 references used by the mainline.
Fourteen are corpus papers (DOIs checked against `references.tsv` by a test), and one is the in-house ADOC article.
Liao et al. 2024 was read in full in the prototype but only staged. Four IL-1beta and
NF-kappaB papers (Frank 1995, Yu 2019, Taylor 2024, Kalkhoven 1996) are new.
They were DOI-verified against Crossref on 2026-11-22 and read at abstract level
only. This is recorded in the `evidence_depth` column and must be upgraded by
full-text reading before WP3 relies on them.

## Gaps relevant to ENDO-TWIN

- No paper in the corpus measures BMP receptor (ALK2/ALK3/BMPR2) or SMAD1/5/8
  activity in ADOC; the only ALK3 paper is retracted.
- No paper supports an epithelial-autonomous route for progesterone suppression
  of proliferation, or a direct epithelial HAND2 effect.
- No corpus paper addresses progesterone resistance in endometriosis directly.
- No NF-kappaB paper in endometrium is in the corpus.
- ADOC has no Ki67 or EdU readout yet.
