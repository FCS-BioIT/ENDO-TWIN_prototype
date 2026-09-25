# Phase 2B pre-registration, amendment 05 (provenance only)

Committed **before any candidate KLF12 value was read**, and on its own. It
changes no rule, method, threshold, criterion or implementation.

**What it freezes.** At C5, the definition's `threshold_derivation` will be
exactly this string:

    repo:docs/phase2b/preregistration_amendment_03.json@d5db35ded71b68b0dd4ceb38ff605de2bb0fde75#sha256:2f83828d5a7c12ed08a605d849fac9c700e7ac92ef2b1fa339199fb55d5318c1

That is amendment 03, at the commit that first added it, cited by its exact
sha256. Any other value is a deviation. It must pass Phase 2A RR14's
repository-citation check. The check was run against the current HEAD
before this commit, and the citation passed.

**Implementation pins.** Amendment 04 remains the authority for the pins.
The guard reads the pins of the latest amendment, so this file carries
amendment 04's `pinned_implementation_sha256`, copied verbatim, and a test
requires the two to be identical.
