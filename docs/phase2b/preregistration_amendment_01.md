# Phase 2B pre-registration, amendment 01

Committed **before any candidate KLF12 value was read**, and on its own.
The rules in `preregistration.json` (commit b586488) stand unchanged
except for the one rule below. That file is never rewritten. Where this
amendment speaks, it governs, and its pins are the ones the guard checks.

**What changed: S5, the null-specificity test.** As first frozen, S5
accepted a donor when at least 80 of the 99 null replicates could be fitted
and the observed separation beat every one that was fitted. That bounds the
Monte Carlo p at 1/81 = 0.0123. The rules claimed p <= 0.01.

The amended rule counts an unfitted null replicate as one the observed
separation did not beat:

    p = (1 + replicates at or above the observed Ashman's D + unfitted replicates) / 100

S5 passes iff p <= 0.01. That means all 99 replicates must be fitted and
the observed D must be strictly above every one of them.

**Direction.** The change is stricter. Every donor that passes now would
have passed before. It was raised by the independent review, not by any
data, and no value-derived artifact exists.

**Mechanism.** The guard now accepts numbered amendments like this one:
- each is its own commit and is touched once;
- each is built on the stage before it, with nothing else written to
  `docs/phase2b/` in between.

Every amendment therefore precedes any value-derived work. An amendment
made after values have been read is a deviation, and the guard refuses it.
