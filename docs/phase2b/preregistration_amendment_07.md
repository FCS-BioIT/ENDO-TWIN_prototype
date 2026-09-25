# Phase 2B pre-registration, amendment 07

Committed **before any candidate KLF12 value was read**, and on its own. It
changes no rule, method, threshold or criterion. It re-pins the guard after
commit 0357273, and supersedes amendment 06 as the implementation-pin
authority.

**Why.** At C4 pre-flight on `main` at 41259f1, `assert_rules_frozen` refused:

    docs/phase2b/preregistration.json was touched by 2 commits; a frozen file is written once

41259f1 is the `--no-ff` merge of PR #8. Its tree is identical to the branch
tip 4484aff, and it wrote no bytes. The guard's `git log --all --full-history`
still lists such a merge for every file where it differs from its other
parent. So every frozen file (the rules, the owner decisions, all twelve
amendment files) appeared twice, and no value could ever be read on `main`.

**The fix.** A merge counts as writing a frozen file only if the file's tree
entry (mode and blob) differs from every parent's, or the merge drops the file.
A merge that carries one parent's exact bytes wrote nothing, and every commit
that ever changed those bytes is still listed. Non-merge commits are counted
exactly as before.

**What does not change.**
- A draft on a side branch hidden by `merge -s ours` is still refused, because
  the side branch's own commit is listed.
- A merge that brings in bytes no parent holds (an evil merge) is still a
  write, and so is a mode-only change or a deletion inside a merge. Each is
  tested.
- The authentic-DAG checks stand: no shallow clone, no replace refs, no
  grafts, `GIT_*` stripped. So do the amendment-chain rule and the RR14
  ancestry check (owner B1/B2 resolution, amendment 06).
- The amendment-05 frozen citation and every rule of amendments 01-06 stand.

Only `src/dt_adoc/personalization/phase2b/guard.py` changes pin. Every other
pin is copied from amendment 06.
