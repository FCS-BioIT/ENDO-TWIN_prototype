# Staging status: deep_research_adhesion_model_2026-09-11

Unpacked from `dt_adoc_deep_research_staging_2026-09-11.zip` on 2026-09-11.

**These rows are candidates from an external literature reviewer. Nothing here
has been reviewed, accepted, or promoted.** No canonical table was modified
when this bundle was filed.

## Raw / derived separation

`context/literature/staging/deep_research_adhesion_model_2026-09-11/` holds the
**complete verbatim bundle**: 12 files, being the 11 entries listed in
`manifest.tsv` plus `manifest.tsv` itself. Every one of the 11 manifest-listed
entries resolves inside that directory and matches its recorded SHA256, so the
bundle is self-verifying; re-run the check with the loop in "Mechanical
verification" below.

Nothing in that directory may be edited: the SHA256 digests are the record of
what the external reviewer actually sent, and repairing a defect in place would
destroy that record and misrepresent the source.

Note that `promotion_plan.tsv` specifies `action=copy` for the provenance YAML.
The bundle therefore retains its original, and
`deep_research_adhesion_model_2026-09-11.yaml` in this `reviews/` directory is
the filed copy, byte-identical to it. An earlier version of this note moved the
YAML out instead of copying it, which left the staged bundle incomplete against
its own manifest and made a blanket integrity claim that was false; both are
corrected here.

Defects found in staged rows are therefore recorded in the **derived** layer,
which gates promotion:

- `deep_research_adhesion_model_2026-09-11.adjudication.tsv` (this directory) -
  binding accept/reject/unresolved decisions per staged row.
- This file - unpack-time mechanical verification.

## Provenance

Bundle was constructed against `main` @ `6bceaec7b508c3425cbdd7b14714019fb5c6955f`
with active model `models/superset/adoc-literature-superset-v0.4.0`. The
reviewer's own provenance/scope/claim-boundary file was filed separately as
`context/literature/reviews/deep_research_adhesion_model_2026-09-11.yaml`
(alongside the pre-existing narrative `.md`), per `promotion_plan.tsv`
(`action=copy`, `when=now`, no blocking review).

## Mechanical verification performed at unpack time

All checks below are mechanical only. They say nothing about whether the
biology is correct.

- **Integrity**: all 11 SHA256 digests in `manifest.tsv` match; all row counts
  and column counts match the manifest.
- **Schema**: headers of `candidate_nodes`, `candidate_edges`, `mechanisms` and
  `references` are byte-identical to their canonical `context/literature/`
  counterparts. Headers of `edge_evidence`, `rule_variants`,
  `unresolved_mechanisms` and `drug_target_catalog` match v0.4.0 field-for-field
  but differ in line terminator (see below).
- **ID collisions**: none. Checked first-column IDs of all 8 data tables against
  their canonical targets.
- **Reference dedup**: none of the 9 staged DOIs or PMIDs appear in the 70-row
  canonical `context/literature/references.tsv`. All 9 are mechanically new.
  Citation *verification* (that each DOI supports the claim made) has NOT been
  done and remains a blocking review.

## Known integration detail

The bundle is LF throughout. The four `context/literature/` targets are also LF,
so those merge cleanly. **All v0.4.0 model tables are CRLF throughout**, and the
repo has no `.gitattributes`. Whoever creates v0.5.0 should settle line endings
deliberately rather than letting a mixed-ending file land in the model
directory.

## What is blocked

Per `promotion_plan.tsv`, every remaining file is gated:

- `references.tsv` — deduplicate_then_append, after citation verification.
- `candidate_nodes.tsv` / `candidate_edges.tsv` / `mechanisms.tsv` —
  review_then_merge, after node/edge/reference review.
- `edge_evidence.tsv` / `rule_variants.tsv` / `unresolved_mechanisms.tsv` /
  `drug_target_catalog.tsv` — target
  `models/superset/adoc-literature-superset-v0.5.0/`, which **does not exist**.
  Do not write these into v0.4.0.

## Adjudicated defects blocking promotion (as of 2026-09-11)

Independent review has already rejected three staged rows and flagged two more
as unresolved. See the adjudication TSV for the full basis:

- `DRE009` (`X_IL11 -> E_ITGA2B1`, marked `confidence=verified`) conflates
  integrin-alpha2 **abundance** with **alpha2beta1 receptor activity**, which
  `AGENTS.md` forbids. Not promotable at `verified`.
- `dr20260911_itgav_no_secretory_absorption` cites a YAML key
  (`structural_audit`) that does not exist. Unsupported topology claim.
- `dr20260911_lif_soft_surface` / `dr20260911_lif_hard_surface` cite
  `priority_changes`, which contains no mention of LIF. Provenance broken;
  hypotheses may be retained only if re-sourced.

The reviewer's stated guardrail: the substantive change is not adding 14 nodes,
it is replacing hand-set interface relay priors with an explicit finite-time
attachment/detachment process. The reviewer also asked explicitly that their
proposed topology NOT be reproduced uncritically — each suggestion is to be
independently accepted, rejected or modified, and each new node justified as
increasing identifiable biological information.
