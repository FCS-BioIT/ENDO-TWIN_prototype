# Phase 2B pre-registration, amendment 09 (wording re-pin)

Committed **before any candidate KLF12 value was read**, and on its own.

**What changed.** Wording only, in `src/dt_adoc/personalization/phase2b/guard.py`
(commit ab7cda5). After amendment 07, `_only_commit` counts the commits that
*write* a frozen file, as decided by `_writes`. It does not count every
commit git lists as touching the file. Three places still said "touched":
- the module docstring on `owner_decisions.json`;
- the module docstring on amendments;
- the `OrderingError` message.

All three now say "written". One test matches the error text and was updated
to the new message.

**What did not change.** This is documentation and error-message wording
only. There is **no behavioural change and no acceptance-criterion change**.
`_writes` and the logic of `_only_commit` are unchanged. Every rule of
amendments 01-08 stands, including:
- amendment 07's guard criterion, as disclosed by amendment 08;
- the amendment-05 frozen citation;
- the owner's B1/B2 resolution.

**Pins.** Only `guard.py` is re-pinned. Every other pin is amendment 08's,
copied verbatim. Amendments 07 and 08 are not edited.

**Review provenance.** The final review that raised this wording point was a
stand-in: the same model family as the author, because the independent
reviewer was unavailable (no credits). Its PASS is **degraded evidence**. The
owner accepted it as the current execution gate on 2026-09-25, and the
independent review is to be rerun when available.
