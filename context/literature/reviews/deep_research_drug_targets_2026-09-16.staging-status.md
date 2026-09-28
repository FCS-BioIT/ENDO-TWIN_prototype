# Staging status: deep_research_drug_targets_2026-09-16

Filed 2026-09-16.

**This is an external literature reviewer's narrative. Nothing in it has been
accepted, promoted, or integrated as written.** No canonical literature table,
no catalog and no model file was modified when it was filed or adjudicated, and
v0.4 executable behaviour is untouched.

**It did, however, change coupling adjudications**, and an earlier version of
this line wrongly said it had not. The primary-verification pass moved `IN_cAMP`
and `S_PKA` from `BIOLOGICALLY_COLLAPSED` to `ARTIFICIALLY_COUPLED` (DTR006) and
corrected the `E_CD98_CD9` rationale (DTR005) in
`config/coupling_adjudication.tsv`. Eleven rows in that file self-date as
changed on 2026-09-16; the ones this batch caused are named in
`...primary-verification.tsv`, which records them as
"COUPLING VERDICT CHANGED" and "COUPLING RATIONALE CORRECTED". The scope of
"not integrated" is therefore the canonical literature layer and the model, not
the adjudication table.

## Raw / derived separation

`context/literature/staging/deep_research_drug_targets_2026-09-16/` holds the
**verbatim source**, unmodified:

| File | sha256 |
|---|---|
| `deep_research_drug_targets_2026-09-16.md` | `c000b07e17f4e59dec7117bd6e6d581f7a3f4fb1ab507c0c303032aa818b8a06` |

Unlike the 2026-09-11 bundle this one arrived as a single narrative document
with **no manifest and no candidate TSVs**, so there is no row/column
verification to perform and no staged table that could be promoted by accident.
Everything it proposes has to pass through the adjudication before it can touch
anything.

## Mechanical checks done

- The staged file is present, readable, and hashed above. Re-verify with
  `sha256sum`.
- It cites `main` at commit **`3715da1`**. That is **two commits stale**:
  `7e75da6` (Gate 2 separability revision) and `01a63d1` (review repairs)
  landed after it. Four of its recommendations are consequently already
  implemented or rest on a superseded reading — see §0 of the next-stage note.
- No file under `context/literature/staging/` was modified.

## What was produced from it

| Path | What it is |
|---|---|
| `…reviews/deep_research_drug_targets_2026-09-16.adjudication.tsv` | **binding** decisions DTR001–DTR025. The promotion gate. |
| `…reviews/deep_research_drug_targets_2026-09-16.topology-implications.tsv` | TI001–TI016, model consequences kept separate from catalog changes |
| `…reviews/deep_research_drug_targets_2026-09-16.next-stage.md` | the audit narrative and the deliverables |

## Claim boundaries

- **No primary full text was opened during this adjudication.** Every external
  evidence claim is accepted *on the reviewer's report of it*. Promotions
  resting on DTR002 (IL11 as a second GP130 ligand), DTR006 (EPAC/RAP1),
  DTR011 (PC6/DAG1) or DTR017 (IGFBP1 outgoing edge) require full-text
  verification first.
- The structural measurements quoted in the adjudication are **local and
  reproducible**: exhaustive evaluation over the 19 free variables of the
  committed `network.bnd`, no simulation, no horizon, no rate, no fitted
  parameter. They describe what a candidate rule change would do to the
  rule-induced partition, and nothing about whether the biology is right.
- The Gate 0–2 increment these decisions build on has **same-vendor, degraded**
  review only. Any catalog or topology promotion that follows should receive
  independent review.
