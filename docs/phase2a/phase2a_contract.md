# Phase 2A: the donor-contextualization input contract

**Status: `STRUCTURAL_MAPPING_READY_BUT_REFERENCE_BLOCKED`.** This status is
derived by `phase2a_status.json` from gates G1–G8; it is not chosen here. Phase 2
is not complete, and no donor-specific value, `.cfg` or model exists. Measured
personalization is separately blocked on RR13.

This unit is the bridge from the final ADOC scRNA object (E-MTAB-15842,
`EXT-SCRNA-001`) to `adoc-literature-superset-v0.5.1`. A later unit can use it
to write donor-specific **initial-state probabilities** without inventing a
threshold or leaking an outcome. Every number and category lives in the
generated files below. This page gives only the reasoning they cannot carry.

| file | what it holds |
|---|---|
| `scrna_metadata_extraction.json` | meta.data of the object, read in R and aggregated there. Committed counts only |
| `data_grain_audit.tsv` | donor × condition × `celltype_v2` (42 rows) and donor × condition × compartment (18 rows), zeros included |
| `node_personalization_map.tsv` | one row per v0.5.1 node |
| `donor_unit_summaries.tsv` | per-unit statistics for the eligible node, copied from `docs/scrna/node_support_evidence.tsv` |
| `reference_requirements.tsv`, `reference_gate.json` | what an external reference must supply, and the mechanical verdict |
| `mapping_specification.json` | the frozen three-step mapping; the owner parameter is unset |
| `provenance_contract.tsv` | the lineage chain and the three leakage rules |
| `phase2a_status.json` | gates, counts, owner decisions applied and still open |

Regenerate everything with `pixi run build-phase2a-contract` (no R, no object).
Re-reading the object uses `pixi run extract-phase2a-metadata <rds> --rscript <R>`.
The invariants are tested in `tests/unit/test_phase2a_contract.py`.

## What the object actually carries

The meta.data has five columns: `sample_id`, `orig.ident`, `celltype_v2`, and
two cluster resolutions. **There is no donor, condition, compartment or tissue
column.** Donor and condition are recoverable only by parsing `sample_id`
(`SZ09TE_HT` → donor `SZ09`, condition `HT`). `orig.ident` and each barcode
prefix agree with `sample_id` in every cell. Compartment is not metadata. It is
the frozen `celltype_v2` → epithelium / stroma / myofibroblast partition of the
node-support pre-registration. The cluster columns are not a model axis.

All three donors have both conditions. Of the 18 donor × condition × compartment
cells, one is empty (`SZ09_HT_myofibroblast`), and every myofibroblast unit is
below the node-support minimum. So the usable grain is **3 donors × 2
conditions × 2 primary compartments**. Cells are within-unit measurement
precision throughout, never replicates.

## Why only one node is eligible, and why that is correct

Of 59 nodes, 32 are not RNA-assessable. Of the other 27, 26 are derived: an
istate on a derived node is an initial condition that MaBoSS overwrites from the
rule within a few ticks (`docs/v05_mechanistic_integration_plan.md` §0.2(c)).
Personalizing one of them would mean editing its rule, which this contract
forbids. The owner decided (Q1, 2026-09-24) that only free variables are
eligible, so those 26 are `context_only`.

The one free, observable node is `E_KLF12_HIGH`. It is `blocked_missing_reference`:
it is eligible in structure but cannot be mapped yet (owner Q2). The closed
KLF12 prior finding is **not** reopened. That finding said these data establish
no boundary on their own, and an external reference is exactly what it said was
missing. The node also carries a `not_blind` flag, because its per-unit values
were committed before this contract existed.

## The mapping, and why it is not PROFILE's

The mapping is the three-step form already frozen in
`docs/scrna/klf12_prior_preregistration.md` (owner decision on review finding
B1). It replaces a rank transform an earlier draft proposed:

1. **Measurement.** KLF12 per cell, on the deposited decontX-corrected layer.
2. **Latent state.** Each cell is called high or not by a per-cell high-state
   definition that comes **only from an external reference**: a feature, a
   per-cell quantity, a rule and a threshold. The ADOC donors and their outcomes
   never contribute. The unit's estimate is the fraction of its epithelial cells
   called high.
3. **Conditioning.** `initial_on_probability` is that fraction, under the
   pre-registration's declared bridge. The ensemble frequency of initialising
   the compartment high is taken to equal the fraction of cells in the high
   state. This is an interpretive assumption with no experimental support here,
   and every conditioned result must carry it.

**Every value this contract can license is therefore an
`assumption_conditioned_scenario`.** Each summary row carries that claim level
and the bridge text verbatim, and no value may be described as measured
personalization. The only route to a `measured_personalization` status is
**RR13**: an independent, evidence-backed calibration or validation of
fraction-high → MaBoSS initial ensemble frequency. It must be hashed, committed
and owner-accepted before the claim is upgraded. None exists, so
`reference_gate.json` reports `measured_personalization_verdict:
BLOCKED_BRIDGE_UNVALIDATED` independently of the scenario verdict (owner
decision on review finding B1, 2026-09-24).

The interval is a within-donor cell bootstrap. It measures cell-sampling
uncertainty only, never donor or population inference. **A point or bound of
exactly 0 or 1 is `unresolved` and is not written**, because
`E_KLF12_HIGH` has `logic = E_KLF12_HIGH`: an istate of 0 or 1 would fix it in
every trajectory, a clamp in effect. The owner accepted this rule on 2026-09-25 as
a conservative interface rule. It is not evidence that the biological state
cannot be all-low or all-high.
Nothing is clipped into range. Missing, empty, below-minimum and
condition-unresolved units stay `unresolved` and keep the shared baseline
istate. Nothing defaults to 0.5.

Comparison with the existing local path (`src/dt_adoc/personalization/`,
`tests/regression_profile*/`):

- **Deliberately different.** PROFILE normalizes each gene against the cohort
  being personalized and treats the normalized score as the probability
  (`soft_nv.score_to_initial_probability`). Here the cohort is three donors,
  and `docs/profile_local_reimplementation.md` forbids estimating a reference
  from them. The probability here is a fraction of cells meeting an external
  per-cell rule, not a cohort-relative score. RR03 refuses a reference built on
  the ADOC donors, and the refusal is tested.
- **Rate modifiers are deliberately not used.** `soft_nv.score_to_rate_modifiers`
  reproduces PROFILE's log-scaled rate factor, and its parity fixture still
  passes. Phase 2A neither calls it nor emits a rate field. PROFILE_v2's graded
  inhibition is a perturbation method, not personalization, and is out of scope.
- **It is not yet executable.** There is no external high-state definition, so
  nothing can be compared on real values. The shared idea, a continuous signal
  setting an initial condition on an unchanged topology, is methodological
  inspiration, not demonstrated parity.

## What would unblock numerical mapping

`reference_gate.json` lists the unmet requirements. Two were unmet at the end of Phase 2A: there
is no reference path (RR01), and the owner had not set `min_reference_donors`
(RR11). A reference alone cannot open the gate, because the specification's
parameter is a requirement too. **Update (owner decision D2, 2026-09-25, Phase
2B):** `min_reference_donors` is now 3, `owner_decided`, set before any
candidate reference value was read. It is a minimum for assumption-conditioned
scenario generation only, not a claim of population adequacy; clones and
technical replicates do not count. RR01 alone remains unmet. For the CNT rows, the condition class must also
be resolved (RR08). CNT's composition, unstimulated versus E2-primed only, is
recorded nowhere, so only the three HT epithelial units could map even with a
reference. A future reference must also be checkable by content, not only by
hash: both its donor list and its one-row per-cell definition are read from
hashed files (RR02, RR09). It must be frozen by a pre-registration committed
strictly before the reference manifest (RR10). Its definition must cite its
evidence and record the owner's acceptance of it (RR12). The gate can check
that evidence is present and accepted, but not whether the biology is
adequate. Before any scenario can execute, **RR14** requires three things.
The reference's per-cell values must be shown comparable with ADOC's (the same
pipeline and layer, or a hashed, committed cross-dataset calibration). The
threshold derivation must be cited: by a DOI or accession, or, for a custom
method only, by the immutable repository artifact that froze it
(`repo:<path>@<commit>#sha256:<digest>`), machine-verified by commit, path and
content and strictly preceding the frozen pre-registration (owner schema change,
2026-09-25, Phase-2B amendment 03; no DOI is minted). That the repository form
is used only for a custom method is the owner's rule, not a machine check. At least two pre-registered threshold
variants must be reported alongside the primary threshold as separate scenario
values, with none selected, and never by ADOC outcomes. RR14 upgrades no claim:
it does not satisfy RR13 (owner decision on review finding B13). Measured personalization therefore needs every applicable
requirement of RR01–RR14 **and** RR13.

RR12's two evidence kinds (`published_per_cell_definition`,
`reference_state_separation`) are a Phase-2A-local controlled vocabulary,
accepted by the owner. They do not change the repository-wide evidence-schema
vocabularies. Phase 2A itself set no value for `min_reference_donors`; the
owner set it to 3 at the start of Phase 2B (D2 above).

## Recorded, not repaired

- `config/personalization.yaml` still lists `clamp` and `rate_modifier` as
  allowed layers, and its clipping is `[0, 1]`. Both are left unchanged (owner
  Q3). This contract permits only `initial_probability` and a test enforces it.
- Using these same cells both to personalize a donor and to score a prediction
  about that feature is forbidden without a declared validation design
  (`provenance_contract.tsv`, `leakage_reuse`). Rows whose features built the
  model are flagged `construction_feature_not_citable_as_independent_validation`.
- The corrected-layer caveat still applies. Every zero or low-detection value is
  `provisional_corrected_layer_only`, and is never OFF.
