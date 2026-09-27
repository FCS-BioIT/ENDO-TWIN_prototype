# Phase 2B pre-registration, amendment 12 (restoration)

Committed **before any candidate KLF12 value was read**, and on its own. It
re-pins `src/dt_adoc/personalization/phase2b/guard.py` after commit e05b931,
and supersedes amendment 11 as the implementation-pin authority.

**This restores a previously frozen criterion. It adopts no new one.**

**Withdrawn.** Amendment 11's guard changed the rule that decides when a
merge rewrites a frozen file, the rule `_only_commit` applies. Under it, a
merge that dropped a frozen file present in only one parent was not a write.
That contradicted the rule frozen by amendments 07 and 08, while amendment 11
said every rule of amendments 01-10 still stood. The owner decided on
2026-09-25 to withdraw this change, not ratify it.

**Restored.** Amendment 07's rule applies again to frozen files, exactly as
frozen. A merge writes a frozen file if either:
- its entry (mode and blob) differs from every parent's; or
- it **drops the file**.

`_writes` applies this rule by default, with the same logic as the guard
pinned by amendment 10.

**The between-amendments check, and only that check.** A merge between two
amendments is treated as follows:

| the merge | counts as a write between stages? |
|---|---|
| lacks a `docs/phase2b/` file exactly as one parent lacks it (it carries that parent's deletion) | no |
| adds a file neither parent holds | yes |
| deletes a file every parent holds | yes |
| holds novel bytes or a changed mode | yes |

This keeps the correction of the false refusal that amendment 11 reported
against amendment 10's claim, but confines it to the between check.

**Corrected in amendment 11.** "a later commit restored it, which is itself
a write" is too broad. The precise statement:
- A **non-merge** commit that restores a frozen file is a write.
- A **merge** that restores it by taking one parent's exact entry is not
  counted as a write. Those bytes are that parent's, and the commit that
  first wrote them is itself counted.
- So no bytes reach a frozen file without a counted write, but not every
  restoration is itself a counted write.

**Tests** distinguish the two rules explicitly.
- `_only_commit` counts a merge that deletes a frozen file, even when the
  other parent never held it.
- Between amendments:
  - an absence inherited from one parent passes;
  - a merge that adds a new file refuses;
  - a merge that deletes a file every parent holds refuses, with a positive
    control;
  - novel bytes and mode-only changes are writes under both rules.
- Under amendment 11's rule, the restored-rule tests fail.

**Unchanged.** The scientific method and the C4 protocol: candidate
selection, donors, population, the comparability route and stack
identification, the quantity, the derivation, S1 to S5, thresholds, variants
and verdicts. Also unchanged: the amendment-05 frozen citation and the
owner's B1/B2 resolution. Amendments 07 to 11 are not edited. Only
`guard.py` is re-pinned, and every other pin is amendment 11's, copied
verbatim.

**Review provenance.** The finding came from a stand-in review: the same
model family as the author, because the independent reviewer had no credits.
It is degraded evidence, and the independent review is to be rerun when
available.
