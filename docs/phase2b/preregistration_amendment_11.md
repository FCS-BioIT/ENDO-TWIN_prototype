# Phase 2B pre-registration, amendment 11

Committed **before any candidate KLF12 value was read**, and on its own. It
re-pins `src/dt_adoc/personalization/phase2b/guard.py` after commit ece9cdb,
supersedes amendment 10 as the implementation-pin authority, and corrects
amendment 10's record.

**Corrected.** Amendment 10 claims "No history the invariant permits is newly
refused". That claim was **false** for the guard it pinned (ac94849).

This was reproduced before the fix. `main` deletes a pre-rules file under
`docs/phase2b/`. A branch cut before that deletion is then merged between two
amendments. The merge holds `main`'s absence of the file and so wrote
nothing. `_writes`, however, counted any absent entry in a merge as a write,
so the new merge-aware between check refused a history the invariant
permits.

**The fix.** Amendment 07's merge rule now applies uniformly, with absence as
one more state: a merge writes a path only if its state (mode and blob, or
absence) differs from every parent's.
- **Between amendments:** a merge carrying one parent's deletion passes
  (tested). The evil merge that adds a file still refuses (tested).
- **`_only_commit`:** a merge that drops a frozen file present in only one
  parent no longer counts as writing it. This cannot hide bytes. Afterwards
  either HEAD lacks the file, and the guard refuses, or a later commit
  restored it, which is itself a write and is refused (tested). A merge that
  drops a file every parent holds is still a write.

Amendment 10's claim holds for the guard pinned here.

**What does not change.** The scientific method and the C4 protocol are
unchanged: candidate selection, donors, population, the comparability route
and stack identification, the quantity, the derivation, S1 to S5,
thresholds, variants and verdicts. Every rule of amendments 01-10 stands,
except the amendment-10 claim corrected above. So do the amendment-05 frozen
citation and the owner's B1/B2 resolution. Amendments 07 to 10 are not
edited.

**Pins.** Only `guard.py` is re-pinned. Every other pin is amendment 10's,
copied verbatim.

**Review provenance.** The finding came from a stand-in review: the same
model family as the author, because the independent reviewer had no credits.
It is degraded evidence, and the independent review is to be rerun when
available.
