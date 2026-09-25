# Phase 2B rules pre-registration: an external reference for `E_KLF12_HIGH`

Written and committed **before any KLF12 value of any candidate reference was
read, computed or seen**. This commit contains only this file and
`preregistration.json`. The JSON is the machine-checkable form, and where the
two differ the JSON governs. `src/dt_adoc/personalization/phase2b/guard.py`
refuses to release a candidate value unless:
- this commit is intact and is the only commit that ever touched either file;
- the owner decisions precede it;
- every implementation file it pins still hashes as pinned.

## What this does and does not do

It qualifies an external reference for the Phase-2A
**assumption-conditioned** `E_KLF12_HIGH` scenarios only. It produces:
- no donor `.cfg`;
- no probability, rate, clamp, mutation or topology change;
- no measured-personalization claim, because RR13 is separately blocked.

The only ADOC units in scope are the three **HT** epithelial units. CNT is
unresolved (Phase-2A Q4) and is matched to nothing.

## The rules, in brief

| step | rule | owner decision |
|---|---|---|
| context | in-vitro hormone-treated endometrial epithelium, tier T1 (E2 + progestogen + cAMP + XAV939) or T2 (one of cAMP or XAV939 missing); tissue and T3 never qualify | D1 |
| donors | at least 3 identifiable independent donors in the qualifying arm; clones and technical replicates are one donor | D2 |
| selection | `qualification.select` on the metadata inventory, in the D7 order; this selects **C03, E-MTAB-10283, the XAV939 + E+P day-6 arm** (libraries WSSS_END9397531 and WSSS_END9397535), and no other candidate qualifies | D7 |
| donor identity | the depositors' genotype demultiplexing (B44, U1, U2), both replicate libraries pooled per donor; no genotype inference of our own | D2 |
| epithelium | every author `Celltype` label except `Low QC`; no expression filter | D6 |
| comparability | same pipeline only: GRCh38/GENCODE v47, Cell Ranger, the ADOC decontX script, the ADOC QC and scDblFinder | D5 |
| quantity | `count_per_10k` on the decontX layer; `count` is a diagnostic only | D4 |
| threshold | the null-calibrated two-component separation in `derivation.py`; primary threshold and two variants, all reported, none selected | D3 |

## Two things the owner should know before C4

**The ADOC counting stack is not recorded anywhere.** The deposit states only
"aligned to GRCh38 Gencode v47", the pipeline repository starts from Cell
Ranger outputs, and no version survives in the deposited matrices. "Same
pipeline" is therefore proved, not assumed. The SZ09TE_CNT ADOC library is
reprocessed from its FASTQ, and a Cell Ranger version is pinned only if:
1. it reproduces that library's deposited raw and filtered matrices exactly;
2. the pinned decontX step then reproduces the deposited decontX matrix, to
   within 1e-6.

This test compares whole matrices. It extracts no KLF12 value. If no version
passes, the verdict is `BLOCKED_COMPARABILITY`. A version supplied by the
depositors would be tried first.

**`threshold_derivation` has no valid citation.** The derivation is this
document's own procedure. Under the owner's citation rule, no DOI is minted
and no dataset is cited as a method. Unless the owner adjusts the RR14
citation schema before the definition-freeze commit, the verdict is at most
`BLOCKED_OWNER_DECISION`, even if a separation is found.

## Verdicts

| verdict | when |
|---|---|
| `NO_SUITABLE_REFERENCE` | no candidate qualifies; every qualified candidate fails a value-blind, non-comparability check; or `derive()` finds no stable separation, after which nothing else is tried |
| `BLOCKED_COMPARABILITY` | no Cell Ranger stack reproduces the ADOC library, or the pinned stack cannot process the selected candidate |
| `BLOCKED_OWNER_DECISION` | a separation is found but an owner decision is still missing: the RR14 citation, RR12 acceptance or activation |
| `QUALIFIED_REFERENCE_FOUND` | the separation qualifies and Phase 2A's `evaluate_reference` reports nothing but the activation clause; this enables `assumption_conditioned_scenario` mapping only, RR13 stays unmet, and no donor model exists |

## Operating characteristics, measured on synthetic data only

- A synthetic population with a genuine two-state mixture (30% high,
  60-fold rate difference, 700 cells) qualifies.
- A stateless Poisson population, a one-molecule lattice, depth batches at 2x
  and 4x, and depth-dependent dropout do not qualify.
- A stateless negative-binomial population (shape 0.5) passes a single donor
  at about the nominal rate. That rate was about 4% with the earlier
  25-replicate null. With 99 replicates the per-donor p floor is 0.01, and
  every donor must pass.

These are properties of the estimator, fixed before any real value exists.
