# Phase 2B pre-registration, amendment 02

Committed **before any candidate KLF12 value was read**, and on its own.
It changes no rule and no code. The pins are identical to amendment 01's.

**Withdrawn.** `preregistration.md` said that a stateless negative-binomial
population (shape 0.5) "passes a single donor at about the nominal rate. That
rate was about 4% with the earlier 25-replicate null." That number came from
uncommitted probe scripts. No committed artifact measures a per-donor rate,
so none is claimed.

**What is backed, and where.** `tests/unit/test_phase2b_contract.py`:
- **OperatingCharacteristics:** three stateless donors do not qualify under
  any of these confounders: depth batches at 2x and at 4x, depth-dependent
  dropout, or negative-binomial overdispersion at shape 0.5, 1 or 2.
- **Derivation:**
  - a genuine two-state population qualifies;
  - a stateless Poisson population does not, and neither does a one-molecule
    lattice;
  - a criterion that certifies anything is refused by the null.

**The stated level.** Per donor, p <= 0.01 holds by construction against the
stateless *Poisson* null (amendment 01). No level is claimed against an
overdispersed null, and every donor must pass.
