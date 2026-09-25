# Phase 2B pre-registration, amendment 03 (owner decisions)

Committed **before any candidate KLF12 value was read**, and on its own. It
records the owner's decisions of 2026-09-25 and re-pins the implementation
after commit cb66db6.

## Ratified, unchanged

- **S4 (Phase-1B M1(b))** is a reported diagnostic only. It never gates.
- **S5's decision rule** is amendment 01's: all 99 plug-in stateless-Poisson
  replicates must be fitted, and the observed Ashman's D must strictly exceed
  every one of them.
- **Comparability** is strict same-pipeline. The pinned stack must exactly
  reproduce the deposited ADOC SZ09TE_CNT raw and filtered matrices, and the
  decontX output to within 1e-6. Otherwise the verdict is
  `BLOCKED_COMPARABILITY`.

## Changed

**How S5 is described.** `(1 + exceeding + unfitted) / 100` is a
*plug-in-null Monte Carlo exceedance score*. The null's rate and shrinkage
are estimated from the same donor, so the score is **not an exact p-value**,
and no exact frequentist or Type-I level is claimed.
- This supersedes earlier wording that calls it "p", "p <= 0.01" or a
  nominal level: in `preregistration.md`, amendment 01 and amendment 02.
- The code field is now `plugin_null_exceedance_score`.
- The decision rule is unchanged.

**RR14's citation schema.** This is an owner-approved change to Phase 2A.
`threshold_derivation` may cite, for a custom method only, the immutable
repository artifact that froze it:

    repo:<path>@<commit>#sha256:<digest>

Phase 2A (`_repository_citation`) accepts it only if all of these hold:
- the commit is the earliest one holding exactly those bytes;
- that commit strictly precedes the frozen pre-registration;
- the working tree still holds the same bytes;
- the path is repository-relative and outside `data/`.

No DOI is invented or minted. `evidence_citation` and
`comparability_evidence` still need a DOI or accession.

At C5, the definition's `threshold_derivation` will cite this file, by this
commit and this file's sha256. The derivation's code is pinned below.

## Consequences for the verdicts

The expected ceiling of `BLOCKED_OWNER_DECISION` for the citation no
longer applies. `BLOCKED_OWNER_DECISION` now means only one of two things:
owner acceptance under RR12 is missing, or activation of
`config/personalization.yaml` is missing.

## Resources

C4 downloads and reprocessing do not start until a safe disk high-water
plan exists.
