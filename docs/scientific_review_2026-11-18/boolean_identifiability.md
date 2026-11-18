# Baseline fixed-point identities of v0.6.0

The 2026-11-18 audit reported that seven nodes of the executable network lose
their apparent molecular detail when the deterministic rules are substituted
into one another. All seven are confirmed here by an independent method.

## What was verified, and against what

| | |
|---|---|
| Model | `adoc-literature-superset-v0.6.0` |
| Network | `models/superset/adoc-literature-superset-v0.6.0/network.bnd` |
| SHA-256 | `64b5a3aa02394593bef5991b25005a71a27161ec75aefb6f80dbe7a1e347de27` |
| Free variables | 16 |
| Assignments enumerated | 65 536 (all of them) |
| Result | 7 of 7 hold, 0 counterexamples each |

The audit shipped its own `model_network_v060.bnd`. It is byte-identical to the
committed network — same SHA-256, same 4 095 bytes — so the audit and this
repository analysed the same model and no reconciliation was needed.

## Method, and why not the supplied script

The audit's `verify_boolean_reduction.py` proves each identity by asking SymPy
whether `XOR(rule, identity)` is satisfiable. Re-running it would check its
arithmetic, not its claim: a mistake in how the network was loaded, or in which
variables were held free, would reproduce perfectly.

`src/dt_adoc/reporting/fixed_point_identities.py` therefore re-derives the same
seven from this repository's own `network.bnd` parser, by exhaustive
enumeration. The network is a DAG over its free variables, so every node's
value across all 2^16 assignments is computable exactly: `structure._columns`
evaluates the whole network as a few dozen big-integer operations, one bit per
assignment. Two Boolean functions over the same variables are equal if and only
if their bit columns are equal integers. That is a decision procedure, it never
calls SymPy, and it reuses `load_structure`'s own definition of which nodes are
free so the two analyses cannot silently be describing different models.

The verifier is itself tested on hand-built networks whose answers can be read
off by eye, including a case that differs on exactly one assignment in eight —
because an "all seven hold" result from a broken checker looks exactly like a
correct one. During development that test caught a real bug in this module: the
bit mask was the width of a state *index* rather than of the state *space*,
silently truncating every column. The first run of this analysis was wrong and
is not the run reported above.

## The seven identities

```text
S_DECIDUALIZED              = IN_PROGESTIN and IN_cAMP

S_TAZ_ECM                   = IN_PROGESTIN and IN_cAMP

E_RECEPTIVE_SURFACE         = IN_E2 and IN_PROGESTIN and not E_KLF12_HIGH

X_MECHANICAL_PERMISSIVE_ECM = IN_PROGESTIN and IN_cAMP
                              and not (X_MECHANICAL_STRESS_RELAY
                                       and (IN_ER_STRESS_EXCESS
                                            or IN_HIGH_ECM_STIFFNESS))

X_ADHESION_ROUTE_SPP1       = IN_E2 and IN_PROGESTIN and not E_KLF12_HIGH
                              and X_INTERFACE_SPP1_RELAY

X_ADHESION_ROUTE_REDUNDANT  = IN_E2 and IN_PROGESTIN and not E_KLF12_HIGH
                              and X_INTERFACE_REDUNDANT_RELAY

OUT_STABLE_ADHESION         = IN_E2 and IN_PROGESTIN and IN_cAMP
                              and not E_KLF12_HIGH and IN_EMBRYO_PRESENT
                              and IN_TROPHECTODERM_COMPETENT
                              and IN_EMBRYO_CONTACT
                              and (X_INTERFACE_REDUNDANT_RELAY
                                   or X_INTERFACE_SPP1_RELAY)
                              and not (X_MECHANICAL_STRESS_RELAY
                                       and (IN_ER_STRESS_EXCESS
                                            or IN_HIGH_ECM_STIFFNESS))
```

Reproduce with:

```bash
PYTHONPATH=src pixi run python -B -m dt_adoc.reporting.fixed_point_identities --json
```

Regression tests: `tests/unit/test_fixed_point_identities.py`. Machine-readable
result: `output/scientific_review_2026-11-18/boolean_identities.json`.

## Assumptions

1. **Inputs and structural relays are free.** A node whose rule is itself —
   the `IN_*` inputs and the `X_*_RELAY` nodes — is a variable, not a
   computation. There are 16.
2. **Rules are substituted, not simulated.** Each identity describes the
   function a node computes once every determined node has been unrolled to
   free variables. No update schedule, rate or horizon enters.
3. **Nothing is clamped.** Every node obeys its own rule.

## What this does and does not license

These are statements about unperturbed logical fixed points. They say nothing
about asynchronous MaBoSS trajectories, transition rates, transients, hitting
times, or any intervention that clamps an internal node — clamping replaces the
rule that the substitution depends on, which is precisely why an intervention
can separate mechanisms these identities call equal. They say nothing about
whether the biology is correct.

The warning they carry is about **calibration**, not biology. If
`S_DECIDUALIZED` and `S_TAZ_ECM` compute the same function of the inputs, then
an experiment that reads only those terminals at steady state cannot tell the
TAZ branch from the hormonal conjunction, and cannot be used to fit one. It
remains entirely possible that TAZ is essential and that the model's
representation of it is simply uninformative at this readout.

Algebraic redundancy is not evidence that a protein is unnecessary. It is
evidence that this model, read this way, cannot see it.

## Three inputs with no effect at all

`load_structure` reports `unread_inputs = (IN_XAV939, IN_HCG,
IN_EMBRYO_CONDITIONED_SIGNAL)`. All three are declared, all three are
self-referential, and no rule reads any of them, so setting them changes
nothing anywhere in the network. Any protocol arm that varies one is a
structural null, and a null result from such an arm is a property of the model
rather than a finding about the treatment. This matters immediately for
`MCC-01`: the Ruan 2026 result that hCG and conditioned media redistribute
CDH1 before contact has nowhere in the current model to land.
