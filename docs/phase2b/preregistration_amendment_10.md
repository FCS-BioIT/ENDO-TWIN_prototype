# Phase 2B pre-registration, amendment 10

Committed **before any candidate KLF12 value was read**, and on its own. It
re-pins `src/dt_adoc/personalization/phase2b/guard.py` after commit ac94849,
and supersedes amendment 09 as the implementation-pin authority.

**What it strengthens.** The invariant is already frozen: nothing is written
to `docs/phase2b/` between two amendment stages, so every amendment precedes
any value-derived work. This amendment **strengthens how that invariant is
enforced**. It does not change the invariant.

**The gap, reproduced before the fix.** The check listed each commit's
changes with `diff-tree` without `-m`, and that lists nothing for a merge
commit. So a merge placed between two amendments could itself add a file
under `docs/phase2b/` that neither parent held, and the guard accepted the
history. A focused test built exactly that history, and the old guard
accepted it.

**The fix.** A merge's paths are listed with `-m`. Each path is kept only if
the merge wrote it, by amendment 07's merge rule (`_writes`). Plain `-m`
alone would also list what a merge merely carries from either parent. It
would refuse an ordinary merge of an older branch between amendments, which
the invariant permits.

**Tests.**
- The evil merge between amendments now refuses.
- The ordinary older-branch merge still passes.

**What does not change.** The scientific method and the C4 protocol are
unchanged: candidate selection, donors, population, the comparability route
and stack identification, the quantity, the derivation, S1 to S5,
thresholds, variants and verdicts. Every rule of amendments 01-09 stands,
as do the amendment-05 frozen citation and the owner's B1/B2 resolution. No
other guard acceptance criterion changes. Amendments 07 to 09 are not edited.

**Pins.** Only `guard.py` is re-pinned. Every other pin is amendment 09's,
copied verbatim.

**Review provenance.** The advisory that found this gap came from a stand-in
final review: the same model family as the author, because the independent
reviewer had no credits. That PASS is degraded evidence, and the independent
review is to be rerun when available.
