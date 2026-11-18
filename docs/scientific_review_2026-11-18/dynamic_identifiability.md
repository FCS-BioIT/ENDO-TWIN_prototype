# Identifiability of five internal mechanisms

Section 7 of the 2026-11-18 brief asks whether `S_BMP2`, `S_TAZ_ECM`,
`E_GP130_STAT3`, `E_CDH1_APICAL` and `E_HBEGF` can be distinguished from
baseline by perturbing them.

The structural half of that question is answered here, exactly. The dynamical
half is not, and the reason is recorded rather than worked around.

## What was run

For each target, the node was clamped OFF and ON and the whole network
re-evaluated across **all 65 536 free-variable assignments**, counting the
states in which each `OUT_` node changes. This is exhaustive, so a zero is a
proof of no effect at steady state rather than a failure to find one.

```bash
PYTHONPATH=src pixi run python -B -c \
  "from dt_adoc.reporting.fixed_point_identities import clamp_discrimination; \
   print(clamp_discrimination(('S_BMP2','S_TAZ_ECM','E_GP130_STAT3','E_CDH1_APICAL','E_HBEGF')))"
```

Full table: `output/scientific_review_2026-11-18/clamp_discrimination.tsv`.
Tests: `ClampingTheAuditedTargets` in `tests/unit/test_fixed_point_identities.py`.

## Result

States (of 65 536) in which an output changes:

| Target | Clamp OFF | Clamp ON | Visible at steady state? |
|---|---|---|---|
| `S_BMP2` | `OUT_STROMAL_DECIDUALIZED` 16 384; `OUT_MATERNAL_ADHESION_COMPETENCE` 1 920; `OUT_STABLE_ADHESION` 240 | nothing | loss only |
| `S_TAZ_ECM` | `OUT_MATERNAL_ADHESION_COMPETENCE` 1 920; `OUT_STABLE_ADHESION` 240 | nothing | loss only |
| `E_GP130_STAT3` | `OUT_EPITHELIAL_RECEPTIVE` 8 192; `OUT_MATERNAL_ADHESION_COMPETENCE` 1 920; `OUT_STABLE_ADHESION` 240 | same three | **both directions** |
| `E_CDH1_APICAL` | nothing | nothing | **never** |
| `E_HBEGF` | nothing | nothing | **never** |

Three things follow.

**Two of the five cannot be seen at all.** Clamping `E_CDH1_APICAL` or
`E_HBEGF` in either direction leaves every reported output identical in every
one of the 65 536 states. No steady-state experiment reading the model's
outputs can detect either intervention. Both nodes appear in
`load_structure(...).phenotype_inert`, which is the same fact arrived at
independently.

**Two more are visible only when removed.** `S_BMP2` and `S_TAZ_ECM` sit
inside conjunctions, so deleting one is decisive and forcing one on changes
nothing. An identifiability study designed around overexpression would read
these as nulls for a reason that is structural rather than biological, and
would be wrong to report the biology as insensitive.

**Each target is an exact alias of other nodes.** None of the five computes a
function of its own:

| Target | Identical function to |
|---|---|
| `S_BMP2` | `IN_PROGESTIN`, `E_PGR`, `E_IHH`, `S_PGR`, `S_NR2F2`, `S_HAND2` |
| `S_TAZ_ECM` | `S_DECIDUALIZED`, `S_PRL`, `S_IGFBP1`, `S_SPP1`, `OUT_STROMAL_DECIDUALIZED` |
| `E_GP130_STAT3` | `E_LIF`, `E_CD98_CD9`, `E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE` |
| `E_CDH1_APICAL` | `IN_EMBRYO_CONTACT` |
| `E_HBEGF` | `E_SECRETORY_STATE`, `E_PAEP`, `E_PC6`, `E_DAG1_CLEAVED`, `E_MUC1_SLEX`, `E_SPP1_EXPR`, `E_ITGAVB3_5`, `E_ANXA2_ACTIN` |

So the whole `S_BMP2` → decidualization branch is, at fixed point, a
relabelling of `IN_PROGESTIN`; `E_CDH1_APICAL` is a relabelling of
`IN_EMBRYO_CONTACT`; and `E_HBEGF` is one of nine nodes computing
`E_SECRETORY_STATE`.

## Which measured readouts could discriminate them

The ADOC measures two nodes: `E_PAEP` and `S_IGFBP1`
(`config/observation_model_map.tsv`). Both are inside alias classes listed
above — `E_PAEP` with `E_HBEGF` and seven others, `S_IGFBP1` with `S_TAZ_ECM`,
`S_PRL` and `OUT_STROMAL_DECIDUALIZED`.

**No currently measured ADOC readout can discriminate any of the five targets
from the other members of its own alias class.** That is the finding, and it
bears directly on `MCC-05`: `S_PRL` and `S_IGFBP1` are not merely
non-interchangeable biologically, in this model they are the identical
function, so the model cannot express the distinction that Rawlings 2021
reports between decidual and senescent subpopulations even in principle.

## What was NOT run, and why

The brief asks for MaBoSS comparisons of transient behaviour, timing and
trajectory-level differences. These were not run. The blocker is specific:

`config/intervention_library.tsv` registers four interventions with an
executable effect — `mifepristone` (`E_PGR`, `S_PGR`), `anti_spp1`
(`X_SPP1_LUMEN_FREE`), `hand2_loss` (`S_HAND2`) — plus `xav939`, recorded as
`no_executable_effect`. **None of the five targets has a registered
intervention.** The `perturb cascade` CLI accepts `--intervention <id>` from
that library, or `--set IN_NODE=0|1` for declared inputs; clamping an internal
node such as `S_BMP2` is reachable through neither.

Registering new interventions is not a gap to be filled in passing. It runs
through the direct-effect governance in `docs/o8b_direct_effect_governance.md`
and `config/direct_effect_target_policy.tsv`, which decides per target role
whether an agent can act on it at all. Of the five, the policy makes
`E_GP130_STAT3` eligible as a `pathway_gate`; the others would each need their
role adjudicated. Doing that silently, to produce a simulation the brief asked
for, is exactly the shape of change the harness policy calls moving the rule
rather than the code.

So the limitation is recorded instead of worked around. What a MaBoSS
comparison would add, on top of the exhaustive result above:

- whether `E_CDH1_APICAL` and `E_HBEGF`, unobservable at fixed point, differ in
  transient occupancy or in the order downstream nodes respond;
- whether `S_BMP2` and `S_TAZ_ECM` differ in hitting time even though they
  agree on which states are reached;
- whether `E_GP130_STAT3`, the one target visible in both directions, is
  distinguishable from `E_LIF` dynamically, since it is not statically.

None of those can be answered from the identities, and none is answerable with
the intervention library as it stands.

## Two cautions that apply to everything above

Model time is not experimental days, and no statement here maps onto one. And
a simulated intervention effect is a conditional model-internal prediction: it
is not biological target validation, and a node this analysis calls silent is
unobservable in this model at steady state, not biologically idle.
