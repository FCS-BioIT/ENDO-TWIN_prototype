# Phase 2B pre-registration, amendment 15 (downstream role of the C4 product)

Committed **before any stack-identification matrix comparison, and before any
KLF12 value of any candidate reference was read**. It is committed on its own
and records the owner's decision of 2026-09-26. The ADOC per-unit KLF12 values
committed before Phase 2A keep their `not_blind` flag, as before.

No Cell Ranger reference or count output exists. The amendment-14 `mkref`
(9.0.1, started 00:49) was terminated at 01:09, before it completed.

This is a **semantic** amendment. It changes what the C4/C5 product is *for*.
It changes no measurement, comparability, derivation, verdict or stopping rule.

## Why

The frozen purpose ties the qualified reference to Phase 2A's
assumption-conditioned `E_KLF12_HIGH` scenario. Phase 2A maps that scenario to a
baseline `initial_on_probability`: `mapping_specification.json` step 3, whose
shared baseline is the `baseline.cfg` istate.

- **Where the model puts that value.** The istate sits at t=0, before the
  simulated E2 priming and hormone treatment (`config/protocols.yaml`;
  `simulate.py` `protocol_lineage`).
- **When the RNA was measured.** The paper fixes the HT scRNA as an
  end-of-hormonal-treatment observation (below).
- **The conflict.** Writing that observation at t=0 turns a post-treatment
  observation into a pre-treatment cause of the very treatment being simulated.
- **The hidden assumption.** `E_KLF12_HIGH` has `logic = E_KLF12_HIGH`, so the
  t=0 placement also silently asserts that the KLF12 state is unchanged by
  treatment.

## The experiment, from the paper

Source: Zaragozano et al. 2026, *Sci. Adv.* 12, eadz2249
(doi:10.1126/sciadv.adz2249). The local copy is `data/sciadv.adz2249.pdf`,
sha256 `51fe0acb…a319f1`, as in `config/data_manifest.tsv`. For experimental
timing the paper governs; for model semantics the repository does.

| step | what was done |
|---|---|
| expansion | 6 days in expansion medium, epithelial and stromal channels |
| HT day 0–2 | E2 10 nM |
| HT day 2–6 | E2 10 nM + MPA 1 µM + cAMP 250 µM + XAV939 10 µM |
| scRNA-seq | "stromal and epithelial cells from control and hormone-treated ADOC were collected separately" |

The Results frame the scRNA as "before and after hormonal treatment" under
"Hormonal stimulation drives transcriptional changes in ADOC".

- **HT scRNA** is an end-of-hormonal-treatment observation. There is no embryo
  in the scRNA experiment. The embryo-adhesion and mifepristone assays are
  separate, downstream functional assays.
- **CNT treatment status: untreated.** The paper calls these chips
  "nontreated", "untreated" and "control". This supersedes
  `owner_decisions.json` D1's `cnt` clause, as to treatment status only.
  `owner_decisions.json` is not edited.
- **CNT harvest timing: unresolved.** The paper does not say whether CNT chips
  were harvested at the start of treatment or time-matched to the HT harvest.
  This is not treated as resolved, and it is not declared biologically
  inconsequential. It matters for later RNA observation modelling.
- **CNT stays out of C4.** CNT units are matched to nothing. The T1 reference
  is hormone-treated and does not match an untreated unit.

## The downstream role

| | |
|---|---|
| **old** | external KLF12-high definition → ADOC fraction high → baseline `initial_on_probability` |
| **new** | external KLF12-high definition → endpoint HT KLF12 observation and calibration |

- **The C4/C5 output** is an **endpoint KLF12-high measurement definition** for
  hormone-treated epithelium: feature, layer, per-cell quantity, rule, and a
  primary threshold with its pre-registered variants. It applies to the three
  HT epithelial units as an end-of-hormonal-treatment observation.
- **The baseline `initial_on_probability`** is retired as the *default*
  downstream use. It is not forbidden.
- **Any use as a persistent donor state** must carry an explicit assumption
  that KLF12 is unchanged under treatment, or cite future independent
  validation of that invariance. This covers a baseline or t=0 istate, or any
  state held across the simulated protocol.
- **Verdicts** are computed exactly as before; the rules are carried verbatim.
  Only what `QUALIFIED_REFERENCE_FOUND` licenses changes: by default, the
  endpoint measurement definition. The baseline scenario is licensed only under
  the condition above.
- **Claim ceiling: unchanged.** Results stay assumption-conditioned, RR13 stays
  unmet, and no donor-specific model or `.cfg` is produced.
- **Phase 2A is not edited.** `docs/phase2a/*` and `phase2a_contract.py` keep
  their frozen bytes. Redefining the Phase-2A mapping is a later, separate unit.

## Unchanged

- **Candidate selection:** C03, E-MTAB-10283, and the fallthrough rule.
- **Stack identification:** amendments 13 and 14, including the `mkref`
  execution parameters and the acceptance criterion.
- **Donor and population rules.**
- **KLF12 measurement and quantity:** `count_per_10k` is primary, `count` a
  diagnostic.
- **Derivation:** S1 to S5, null calibration, thresholds, aggregation and
  variants (all reported, none selected).
- **Stopping and verdict rules.**
- **The amendment-05 frozen C5 citation,** and the owner's B1/B2 resolution.
- **Every other rule of amendments 01–14.**

No code changes. Amendment 12's pins are carried verbatim.
