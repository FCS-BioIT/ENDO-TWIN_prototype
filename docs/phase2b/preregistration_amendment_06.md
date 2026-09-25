# Phase 2B pre-registration, amendment 06

Committed **before any candidate KLF12 value was read**, and on its own. It
re-pins the implementation after commit 07649f4, which fixed defects the
independent review found. It supersedes amendment 04 as the authority for
the implementation pins.

**Fixed.** The fixes implement rules that already stood. No acceptance
criterion moves.
- **The S5 null rate.** It is now the unique root of the *expected*
  detection fraction over the donor's depths. It had been bisected on one
  simulated draw, which is not monotone in the rate. A donor detected in
  every cell, or in none, cannot be calibrated, and it fails S5.
- **The mixture fit.** The Phase-1B fit could crash on a report-only field
  after EM had converged. It no longer can, and its values are otherwise
  identical to the frozen fitter's. A genuine failure to fit still counts
  against the separation.
- **T2 with unknown components.** An unknown cAMP or XAV939 status never
  qualifies as T2.
- **Per-cell input.** A KLF12 count above its cell's depth is refused.

**Owner resolution of B1 and B2 (2026-09-25).** Both are
review-environment incompatibilities, not product defects. The guard and the
RR14 ancestry check are defined over the authentic repository history. The
aih review snapshot is a synthetic two-commit history, which does not
preserve it. Neither check is weakened or modified to pass there.

The accepted evidence is:
- in the real checkout, `assert_rules_frozen(ROOT)` passes on the exact
  final commit, naming the C3 rules commit and the amendments in order;
- the amendment-05 citation keeps its exact frozen path, commit and sha256,
  and passes `_repository_citation` in the real history;
- at C5, that citation must pass again against the actual definition-freeze
  commit.

Unchanged: every other rule, including the amendment-03 ratifications and
the amendment-05 frozen citation.
