# Gate 3a closure audit — and why Gate 3b is not opened

Status: closure audit, 2026-09-16. Analysis only; nothing executable changes.

The question this audit answers is not "did Gate 3a do work" but **"is the
maternal core identified well enough to start reasoning about the interface"**.
The answer is no, and the reason is uniform across every axis.

## 1. What Gate 3a resolved

**No candidate rule variant was adopted, and the model is unchanged**: 59 nodes,
35 distinct Boolean functions, 5 free variables — the same partition Gate 3a
opened with. That is the correct outcome, not a failure, and §2 says why.

What *was* resolved is a set of scope and method questions, each of which
corrected a claim this repository had previously made:

| resolved | correction it forced |
|---|---|
| `CD98-b` is **empirically identical to v0.4** in every current arm; only `CD98-c` is separable there | the candidate table's "CD98-b — preferred" status was withdrawn: it had no observational support |
| the three `X_INTERFACE_*` relays are **terminal penetrance variables**, strictly downstream of every maternal node | they cannot carry maternal mechanism, so no maternal conclusion depends on them |
| adhesion is **not a fitting objective** | `adhesion_objective` demoted to `diagnostic_ordinal`; the repository now has no magnitude-fitted term at all |
| anti-SPP1 is **interface information, not maternal** | its earlier high ranking was withdrawn |
| the PRL/IGFBP-1 axis is **blocked on measurement, not modelling** | no rule or rate variant adopted; the blocker is an unregistered binarisation threshold |

Two method errors of my own were also found and fixed: marginalising
experimenter-controlled inputs as though they were latent, which invented
probabilities no experiment can produce; and treating a mapped observation-map
row as a usable assay when the map's own `claim_ceiling` says it cannot validate
the node.

## 2. What remains unidentified

**22 of 59 nodes are adjudicated `ARTIFICIALLY_COUPLED`** — the rules force an
identity the evidence contradicts or that makes a needed distinction
unreachable:

`E_ANXA2_ACTIN`, `E_CD98_CD9`, `E_CDH1_APICAL`, `E_DAG1_CLEAVED`,
`E_GP130_STAT3`, `E_HBEGF`, `E_IHH`, `E_ITGAVB3_5`, `E_LIF`, `E_MUC1_SLEX`,
`E_PC6`, `IN_EMBRYO_CONTACT`, `IN_cAMP`, `OUT_EPITHELIAL_RECEPTIVE`,
`OUT_STROMAL_DECIDUALIZED`, `S_BMP2`, `S_IGFBP1`, `S_NR2F2`, `S_PKA`, `S_PRL`,
`S_SPP1`, `S_TAZ_ECM`

A further **6 are `UNIDENTIFIED`** — merged, with nothing available to decide
whether they really are one thing: `E_DAG1_FULL`, `E_MUC1_BARRIER`, `E_PGR`,
`E_PODXL`, `E_SPP1_EXPR`, `S_PGR`.

Not one of these was resolved by Gate 3a.

## 3. Why: the binding constraint is the observation layer

Every discrimination Gate 3a computed is blocked the same way.

| axis | verdict | separating node measurable? |
|---|---|---|
| CD98 (a vs c, b vs c) | discriminable in current arms, embryo-free, opposite predictions | **no assay** |
| CD98 (a vs b) | requires a new controlled input (`IN_HCG`) | **no assay** |
| CDH1 (both pairs) | discriminable only with embryos | **no assay** |
| GP130 | requires supplying IL-11 | mapped composite that cannot validate the node |
| PC6 | requires a cleavage-resistant construct | mapped composite that cannot validate the node |

**No Gate-3a axis separates on a node with a usable assay.** The observation
layer acts on exactly two nodes — `E_PAEP` (OM-001, `active_constraint`) and
`S_IGFBP1` (OM-002, `active_diagnostic`). Everything else is either a
`reported_only`/`provisional` composite that the map itself says cannot validate
its node, or is not mapped at all.

That is the finding of the whole gate: **the maternal model is not
analysis-limited, it is assay-limited.** More modelling will not move it.

## 4. What requires prospective assays

In value order, and none of these is a reanalysis:

1. **Surface CD98/CD9 under E2-only priming.** Discriminates `CD98-c` from both
   other readings with opposite predictions, embryo-free, in a protocol phase
   every HT run already passes through. ADOC has never measured CD98 at any
   timepoint, and a transcript would not settle it because the node means
   surface availability.
2. **pSTAT3 under supplied IL-11.** The only route to separating ligand
   availability from pathway activity, which is the largest single alias in the
   epithelial layer (`E_LIF`, `E_GP130_STAT3`, `E_CD98_CD9` are one function).
3. **Independent, assay-compatible binarisation evidence for IGFBP-1.** It
   unblocks the PRL/IGFBP-1 axis, which is otherwise stuck for reasons that have
   nothing to do with the model. An earlier version of this list called it the
   cheapest item; that was wrong. A threshold is transferable only if the
   external evidence is compatible in collection geometry, accumulation time,
   medium, dilution and normalisation, or if it marks a genuine biological state
   boundary rather than an assay-specific cut — otherwise it substitutes one
   unregistered calibration choice for another.
4. **α-DG-N shedding under PC6 knockdown**, if a cleavage-resistant substrate
   arm is affordable.
5. **Per-chip PRL/IGFBP-1 pairing.** A metadata recovery request, not an
   experiment: the column-to-chip mapping is recorded as *lost*.

> **Stage 3 is now frozen.** The prospective design selected against this list is
> fixed in [`stage3_experiment_selection.md`](stage3_experiment_selection.md) §12,
> with both owner decisions adjudicated on 2026-09-17. Gate 3a stays open in the
> state this audit describes — "analysis complete, blocked on assays" — because
> freezing a design is not the same as landing a measurement.
>
> **This ordering has been superseded.**
> [`stage3_experiment_selection.md`](stage3_experiment_selection.md) re-derived
> it as an experiment-selection problem rather than an assay wish-list, and two
> items move. Item 1 is **demoted**: the computed pair index in
> [`experiments/stage3_experiment_design.md`](experiments/stage3_experiment_design.md)
> shows that under E2-only priming, with or without hCG, the E2-induction
> reading of CD98 and the reading in which CD98 is simply constitutive predict
> the same thing, so a presence/absence surface readout in that arm cannot
> exclude the likeliest explanation of a positive result. And a candidate this
> list did not contain — **de-bundling the hormone cocktail**, specifically a
> minus-E2 arm — is now first: it is the only single intervention that separates
> a fork on BOTH nodes the observation layer can validate, and it needs no new
> assay at all. Items 2, 4 and 5 stand as written.
>
> **Item 3 is untouched.** It asks for independent, assay-compatible
> binarisation evidence for **IGFBP-1**, and the Stage-3 analysis neither moves
> nor confirms it. An earlier version of this note called it a prerequisite of
> the recommended arm; that was wrong twice over. The recommended arm's
> prerequisite is about a different analyte — registering a binarisation rule for
> **`E_PAEP`** — and §9 of the companion document explicitly *declines* the
> external-threshold route for it, recommending instead an internal three-band
> ordinal rule against the E2-only and full-cocktail levels, with `indeterminate`
> admissible. Sourcing external IGFBP-1 threshold evidence does not block the
> recommended arm and should not be planned as though it does.

## 5. What is deliberately deferred

* **`IGFBP1-fb`** — a 14-node cycle the structural enumerator cannot evaluate,
  plus calibration leakage through OM-002. Deferring the repair does **not**
  close the PRL/IGFBP-1 question, which is live and blocked elsewhere.
* **`EPAC`** — Kusama 2013 shows graded potentiation, which a rate-free Boolean
  model cannot express. This belongs to a future rate layer, not to topology.
* **`HH-reception`** — blocked on GAP-014: human expression and pharmacological
  response exist, the necessity test does not.
* **The three terminal interface relays** — reinterpreted as unresolved
  interface/penetrance variables and left in place. Removal is a Gate-3b
  topology decision.
* **The `drug_target_catalog.tsv` vocabulary** (DTR020) — now a reporting-quality
  issue rather than a correctness blocker, since the taxonomy no longer forces
  any verdict.
* **The structural-zero scoring fork** — no longer deferred. It was implemented
  conservatively, referred to the owner after `aih consult` returned UNAVAILABLE,
  and **adjudicated by the owner on 2026-09-16** in favour of option (B):
  `structurally_contradicted` + `quantitatively_unscorable_for_ranking`, with the
  clip retained as numerical plumbing only. `config/calibration.yaml` implements
  that wording. What remains outstanding is not the science but the **review
  gate**: the `SEMANTIC_OR_PROTOCOL` repair has not been judged by a broad sweep.
  See [`gate3_scope_adjudication.md`](gate3_scope_adjudication.md) §3 and §7.

## 6. Is the maternal core mature enough to open Gate 3b? No.

Gate 3b is the interface and penetrance layer: what the relays should become,
where between-unit variability lives, whether an observation model is needed.
Opening it now would be a mistake, for three reasons.

1. **Nothing in the maternal layer is identified.** 22 artificially coupled and
   6 unidentified nodes stand exactly as Gate 3a found them. Interface work
   built on an unidentified maternal core would attribute to the interface
   whatever the maternal layer cannot currently distinguish.
2. **The one thing Gate 3b would most want to know is the thing Gate 3a could
   not deliver** — whether `E_RECEPTIVE_SURFACE` and its inputs are correctly
   specified. `E_RECEPTIVE_SURFACE` appears as a separating node in two axes and
   has no usable assay.
3. **Gate 3b's own prerequisite is already recorded as unmet.** The variability
   semantics question (embryo competence vs maternal interface vs an explicit
   observation model) was referred to the owner and returned `UNAVAILABLE` from
   the independent reviewer; it is still undecided, and it determines what the
   relays mean before anything can replace them.

**Recommendation: do not close Gate 3a and do not open Gate 3b.** Gate 3a's
analysis is complete — every axis has been taken as far as the evidence allows,
and the remaining work is measurement. The gate should stay open, in the state
"analysis complete, blocked on assays", until at least one of §4's items lands.

The honest summary is that this gate converted a set of unknowns into a costed
measurement list. That is a real result, and it is not the same as progress on
the model.
