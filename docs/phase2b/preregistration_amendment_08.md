# Phase 2B pre-registration, amendment 08 (disclosure correction)

Committed **before any candidate KLF12 value was read**, and on its own. It
changes no code and no pin. Its pins are amendment 07's, copied verbatim.

**Corrected.** Amendment 07's Markdown opens with "It changes no rule, method,
threshold or criterion", and its commit message says "No rule, threshold or
criterion moves". Both are wrong about one thing. Amendment 07 **did change an
acceptance criterion, the guard's.**
- **Before:** every commit that `git log --all --full-history` listed for a
  frozen file counted as writing it. That included a merge that carried one
  parent's exact bytes.
- **After:** such a merge does not count. A merge that holds bytes no parent
  holds, changes only the mode, or drops the file still counts. So does every
  non-merge commit.
- **Effect:** histories with an ordinary `--no-ff` merge of the frozen branch,
  such as `main` at 41259f1, are now accepted where they were refused.
  No history accepted before is refused now.

The owner directed this change on 2026-09-25 ("draft amendment 07, do not
rewrite main").

**Unchanged.** The scientific method is unchanged: candidate selection,
donors, population, comparability route, quantity, derivation, S1 to S5,
thresholds, variants and verdict rules. So are the authentic-DAG checks, the
amendment-chain rule, the RR14 ancestry check, the amendment-05 frozen
citation and the owner's B1/B2 resolution.

Amendment 07's files are not edited, because a frozen file is written once.
This amendment is the record of the correction.
