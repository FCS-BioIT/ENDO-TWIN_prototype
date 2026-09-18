# Curation increment 5 — bibliography registration

Date: 2026-07-29. Claim level: `metadata and provenance only`. **No executable model file
was modified.** `network.bnd`, transition rates, initial conditions, protocol durations,
executable topology and all simulation results are untouched, and the 274 assertions are
byte-identical.

## Why registration cannot affect the model

Verified structurally, not merely empirically. `references.tsv` is on no path into the
executable model: `superset_family.py` reads `candidate-nodes.tsv` and `candidate-edges.tsv`,
never the bibliography. And `migrate_edge_evidence()` reaches a reference only by resolving an
edge's `evidence_id` through `context/evidence-register.tsv` — so **a reference no register
`location` names produces zero assertion rows and a byte-identical output file.**

## Registered: 12, REF-046 to REF-057

Ak 2026 · Bienert 2021 · Cai 2023 · Dong 2025 · Muhandiram 2023 · Peng 2021 · Ruane 2024 ·
Santos 2020 · Segura-Benitez 2025 · Shibata 2024 · Wang 2023 · Zhou 2024.

All 12 are versions of record. All DOIs resolve at Crossref, all PMIDs verified, no
retraction or correction on any. Bibliography 45 to **57**; `verify-citations` reports
57/57 resolved with only the pre-existing REF-006 abbreviated-title warning.

Ids were allocated by strict append-only sequence, which `git log -p` confirms is the
repository's invariant: across four commits touching `references.tsv`, **no id has ever been
reused, renumbered or changed meaning.** That is now load-bearing rather than incidental —
since `5f8d7b4` an assertion id is `ASRT-<edge>-<REF-id>`, so a REF id is a content address
and renumbering one would silently reassign curated judgements.

## Already registered: 12, not duplicated

REF-007, 019, 020, 021, 022, 038, 039, 041, 042, 043, 044, 045. Ruan is REF-019, Zaragozano
REF-020, Molè REF-021 — all three were registered in an earlier increment at mid-range ids.
Deduplication was checked by DOI, PMID and fuzzy title against all 45 prior rows: zero
collisions. Highest title similarity to any existing row is 0.65, from generic phrasing.
Huang 2009 (REF-039, Shih-Min A. Huang, *Nature*, tankyrase) and Huang 2026 (Bixia Huang,
NDRG2) were confirmed to be different papers by different authors with no shared institution.

## Deliberately not registered: 2 — and the agents disagreed

**Mo 2026 (ENTPD3) and Huang 2026 (NDRG2)**, both ACCEPTED UNEDITED MANUSCRIPTS carrying the
Springer Nature banner *"there may be errors present which affect the content."*

Their identifiers are not the problem — both DOIs resolve at Crossref and both PMIDs exist
(42014997, 42409918). Only volume and pages are absent, and the registry schema has no
volume or page columns, so nothing would break.

**The two reviewing agents reached different conclusions and both are recorded.**

- *Register Mo now.* Its identifiers are complete, and it contributes a catalytically dead
  S224A point mutant that abolishes the adhesion phenotype — a stronger specificity control
  than most papers in this registry carry.
- *Register neither.* `references.tsv` has **no `publication_status` column**, so a REF id
  minted for an unedited manuscript is indistinguishable from a version of record at the
  point of use. And because a REF id is now a content address, minting one for text that will
  still change reintroduces the class of bug commit `5f8d7b4` was written to eliminate — a
  curated judgement bound to content that later moves under it.

**Decision: register neither**, on the second argument, which is structural rather than
evidential. The repository's own test already pins the unedited set as something that must
*"stay visible rather than blending into the bibliography"*, and registering them is that
named failure mode. Note this defers Mo against one agent's recommendation; the disagreement
is genuine and is preserved here rather than resolved by assertion.

**The discriminating event is unambiguous and requires no experiment: publication of the
version of record.** At that point, verify the DOI is unchanged, re-hash the PDF, compare,
and register deliberately.

Neither is load-bearing meanwhile. Mo's adjudication is a *prohibition* — it must not be used
to encode `CDH1 inhibits attachment`, because it never perturbs CDH1 — and a prohibition is
recordable against the manifest row without a REF id. Huang 2026's only mechanistic claim
(`NDRG2 -> FHL1 -> adhesion`) has no rescue and no FHL1 perturbation of any kind, so it is a
candidate path rather than a chain.

## Traceability chain, now closed

```
PDF (gitignored) -> sha256 -> pdf_manifest.tsv (PDF-0NN)
                                 |- doi, pmid, publication_status, full_text_inspected
                                 |- registration_decision   <- paper-level review lives here
                                 `- ref_id -> references.tsv (REF-0NN)
                                                |- verified by -> citation_verification.tsv
                                                `- cited by evidence-register location
                                                     `- fans out -> edge_evidence_assertions.tsv
                                                                      `- curation_status  <- claim-level
```

Two columns were added to the manifest: `ref_id` and `registration_decision`
(`registered` | `deferred_unedited_manuscript` | `pending`). The DOI join remains the source
of truth and `ref_id` is a validated projection of it, enforced **bidirectionally** — a
manifest row with a `ref_id` must resolve to a registry row with the same DOI, and a row
*without* one must have a DOI absent from the registry. Silent drift is now a test failure
rather than an invisible gap.

This closes the state the design previously could not express: **read and deliberately not
registered.** No placeholder assertion was created to achieve it. Placeholders would have been
actively harmful — `validate_assertions` rejects an assertion whose `edge_id` is not in
`edge_evidence.tsv`, so a paper-level judgement has no legal `edge_id`, and
`migrate_edge_evidence` would delete any hand-inserted row on the next run.

Current state: 26 manifest rows, **24 registered, 2 deferred**. Every version-of-record PDF
in the corpus now has a REF id.

## Registered but uncited is normal here

The repository already tolerates it: 13 references are cited by no assertion, and six —
REF-039 through REF-045 — appear in no table, register, or assertion at all.
`test_literature_contracts.py` checks only `used_refs subset of refs`. Registration means the
model is *entitled* to cite a paper; it does not mean the paper has been verified at claim
level. Claim-level verification remains **zero** across all 274 assertions.

Possession of a PDF has never been the promotion criterion either — `docs/paywalled_papers_needed.md`
records REF-039 being promoted from an abstract, with no full text.

## Stale state corrected

- `README.md` bibliography counts: 38/38 to 57/57, and 40 to 57 records.
- `README.md` assertion counts: 294 to **274**. Commit `c0c64dd` took the table from 294 to
  274 but updated only `docs/topology_parity_correction.md`; the README and
  `docs/evidence_schema.md` were left behind. The schema doc's migration-time distribution is
  annotated as superseded rather than rewritten.
- `README.md` seed-table row count: 124 to 129.
- `docs/model_evidence_audit.md`: its 38/38 figure is annotated as correct at the time of that
  audit, with a pointer here, rather than rewritten.
- **Three seed rows were lying about their own state.** `ADH-SEED-015` (Dong 2025),
  `ADH-SEED-025` (Peng 2021) and `ADH-SEED-067` (Segura-Benitez 2025) all read
  `not_yet_inspected` while the manifest recorded them as fully inspected with figures
  rendered. Corrected to `full_text_or_relevant_results_inspected`. This was the discovery
  tier misreporting the state of the registered tier — the exact integrity problem this
  workstream exists to close.
- **Two papers were inspected but never adjudicated.** Peng 2021 and Zhou 2024 appear nowhere
  in `docs/curation_increment_04_pdf_batch.md` — `grep -ci` returns 0 for both, and for
  miR-124, IQGAP1 and PARD3. Both adjudications are now recorded there as a dated correction.
  Registering a paper whose adjudication was never written down would have established
  "we have the PDF" as the promotion criterion, which is precisely what the repository has so
  far avoided.

## Not done, deliberately

**PMID backfill.** 22 of the 45 pre-existing references have an empty `pmid`, and every one is
in a MEDLINE-indexed journal — these are 22 lookups nobody did, not papers without PMIDs. All
12 new rows carry verified PMIDs, so the newest block is dense while the older two-thirds
stays sparse, which makes the empty cells look intentional. Recommended as its own commit
before any non-emptiness guard is added, and the guard should tolerate an explicit sentinel
(`not_in_medline`, `awaiting_indexing`) rather than demanding a PMID that sometimes cannot
exist. Note that adding `pmid` to `REQUIRED_REFERENCE_COLUMNS` would change nothing at
runtime: that check tests column *presence*, and the column is already present in all rows.

**`conditions/washout.cfg`.** Deliberately excluded. It is the one item in the proposed
sequence that is a genuine executable change — creating the cfg would **add initial
conditions**, which is exactly the class this increment must not touch. It is also not a
prerequisite for anything: the superset's `adhesion_challenge_washout` continues from
`adhesion_challenge_hormone_treated_anti_spp1`, not from `washout`, so the chain never
resolves it and the synthesised protocol is dead code. The safer repair is deletion — stop
cloning `washout` in `protocols/conditions.py` — which creates no cfg and touches no initial
condition. It wants its own commit and its own justification.

## Recommended next

1. **PMID backfill** (no network beyond lookups, risk-free, own commit).
2. **`washout` adjudication** — independent of everything else, prefer deletion over creation.
3. **Report-only structural diagnostics** — pure Boolean enumeration, no MaBoSS, no horizon
   dependence, so it cannot be invalidated by the endpoint decision.
4. **Endpoint-policy adjudication.** This is the one genuine dependency on the present
   increment: Ak 2026 (REF-046) falsifies the PAEP-as-proxy assumption baked into
   `OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE and E_PAEP`, and Shibata 2024 (REF-055)
   supplies a substrate confound for OM-001, the sole active calibration constraint. Both now
   have citable identifiers.
5. **Probabilistic diagnostics**, once the horizon is decided.
