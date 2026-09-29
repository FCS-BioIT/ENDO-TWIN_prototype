# RNA ↔ MaBoSS endpoint concordance

Status: **model evaluation, not calibration.** Model `adoc-literature-superset-v0.5.1`.
No rule, rate, threshold or topology was changed to produce this, and nothing
here is fed back into the model. A discordance is a result. One observation
mapping is read through a declared post-closure correction: `E_PC6` is measured
by PCSK5, not PCSK6 (see [the correction](#post-closure-correction-e_pc6-reads-pcsk5)).

| Artifact | What it is |
|---|---|
| [`concordance.tsv`](concordance.tsv) | one row per RNA-observable node: prediction, per-donor RNA call and state, RNA effect sizes, verdict, limitations |
| [`concordance.png`](concordance.png) | the table drawn as a grid; reads `concordance.tsv` and nothing else |

Rebuild with `pixi run build-rna-endpoint-concordance` (seconds; no expression
object, no MaBoSS run). Pinned by `tests/unit/test_rna_endpoint_concordance.py`.

## The question and the comparison

*Does the model's predicted end-of-treatment state agree with what the RNA
shows, for the nodes RNA can meaningfully observe?*

- **The scRNA is a readout, not an initial condition.** HT was sequenced at the
  end of the hormonal protocol, so it is compared with the model's predicted
  endpoint and is never used as a t = 0 input.
- **Prediction.** The fixed point of the v0.5.1 rules under the four HT inputs
  (`IN_E2`, `IN_PROGESTIN`, `IN_cAMP`, `IN_XAV939`) against each candidate CNT
  arm. It is cross-checked against the committed v0.4.0 MaBoSS run
  (`docs/concordance/run_settings.json`, maternal arms, converged horizon): every
  converged P(ON) is exactly 0 or 1 and matches the prediction. v0.5.1 differs
  from v0.4.0 only in `OUT_STROMAL_DECIDUALIZED`, which no other rule reads, so
  every RNA-observable node has the same Boolean function in both (asserted by
  the tests). Declared-horizon P(ON) is in the table as **description only**,
  because MaBoSS time has no mapping to days.
- **Observation.** Within-donor CNT vs HT in 3 donors (SZ09, SZ10, SZ25), in two
  broad compartments that are well populated in both arms (epithelium = 4
  celltype_v2 labels, stroma = 2). No individual celltype_v2 label is used, since
  each one is 80–99% one condition. The per-unit quantities and within-donor 95%
  bootstrap intervals come from the pre-registered node-support audit
  (`docs/scrna/node_support_*`), except `E_PC6`, whose PCSK5 values come from a
  post-hoc extraction (`docs/scrna_corrections/pc6_pcsk5/`).
- **Unit.** The donor. Cells are not replicates, and the bootstrap interval
  describes cell-sampling precision only. Each donor has one library per arm, so
  within a donor, treatment cannot be separated from library or chip.

### How a donor and a node are called

For each donor, the audit's frozen rule gives `call_<donor>`: `moves_up` or
`moves_down` only if the CNT and HT intervals do not overlap **and** the change
is at least two-fold. Multi-gene programs are called by the audit's agreement
rule. For every node except `E_PC6`, these calls are reproduced exactly
(asserted against `node_support_findings.json`). `E_PC6` is the exception: its
map row was corrected after the audit, so its calls are the same frozen rule
applied to the corrected program (PCSK5) over the post-hoc evidence, and they
differ from the audit's PCSK6 calls (see [the correction](#post-closure-correction-e_pc6-reads-pcsk5)).
The test asserts both.

This unit then refines one of them into `rna_state_<donor>`. The audit's
`no_material_move` lumps together two different things:
- a change measured precisely and shown to be under two-fold;
- an imprecise change that failed to reach significance.

Only the first is evidence of no response, so:

- **`flat_within_two_fold`**: every voting gene's fold interval lies inside
  ±1 log2. The fold interval is the smallest and largest fold admitted by the
  two arms' intervals, which is conservative.
- **`indeterminate`**: everything else, including a gene undetected in either
  arm, where the pseudocount pins the fold near zero.

Node verdicts use the rule you set, over 3 donors:

| Verdict | Condition |
|---|---|
| `concordant` | predicted direction in 3/3 |
| `circular_agreement` | as concordant, but on a **construction** analyte; not counted as support |
| `discordant_opposite` | movement against the prediction in 3/3 |
| `no_response_within_two_fold` | `flat_within_two_fold` in 3/3 where a switch is predicted. Recorded as a measurement, **not** as a demonstrated discordance |
| `mixed_or_inconclusive` | anything else, including any `indeterminate` donor |

**Why "no response" is not called discordance.** Calling a non-response a
discordance would need two things this unit does not have:
- a justified link from a Boolean switch to a minimum transcript change;
- an equivalence criterion justified by power, which three donors with one
  library per arm cannot supply.

The two-fold margin is the node-support audit's pre-registered materiality
convention, and here it only describes what was measured. The one verdict in
the discordant family is `discordant_opposite`: material movement against the
prediction in 3/3 donors. No node reaches it.

**Construction analytes.** The observation map marks 11 of these rows
`evidence_role = construction`: the measurement helped build the modelled
state. The map's claim ceilings say such agreement cannot be cited as
concordance (E_PAEP: "can never be cited as concordance for it"). Agreement on
them is therefore circular. Disagreement is not circular, because construction
cannot manufacture it.

The RNA effects in the table (`rna_log2_fold_by_gene`, with `*` = intervals
separated) are log2 folds of a pseudobulk share. **They are not MaBoSS
probabilities and must not be read as node activity.**

## Results (27 RNA-observable nodes)

| Verdict | n | Nodes |
|---|---:|---|
| concordant | **0** | — |
| circular agreement | 1 | E_PAEP |
| no response within two-fold (not discordance) | 2 | E_LIF, E_GP130_STAT3 |
| discordant (opposite) | 0 | — |
| mixed / inconclusive | 13 | E_HBEGF, E_PC6, E_SECRETORY_STATE, E_SPP1_EXPR, S_DECIDUALIZED, S_IGFBP1, S_PRL, S_SPP1, E_IHH, E_PGR, S_BMP2, S_PGR, S_HAND2 |
| reported, not scored | 9 | 6 abundance proxies + E_MUC1_SLEX, S_FGF_MITOGENIC, S_NR2F2 |
| uninformative | 1 | E_ESTROGENIC_PROLIFERATION |
| descriptive only | 1 | E_KLF12_HIGH |

**The RNA supports no model-predicted endpoint switch in a way that counts as
evidence.** The model predicts a switch for 25 of the 27 nodes. The only node
that moves as predicted in all three donors is a construction analyte.

### Strongest concordances

- **None qualifies.**
- **E_PAEP moves as predicted, but circularly**: PAEP log2 +3.31 / +2.34 / +2.30,
  separated in 3/3, and reproduced on raw UMIs (+3.13 / +2.23 / +2.13). The
  signal is real and large. It cannot count as support for `E_PAEP` because the
  PAEP transcript built that state.
- Near misses, also construction analytes, so they would not count either:
  - E_SECRETORY_STATE rises in SZ09 and SZ25. In SZ10 two of its five genes rise
    materially, which is not a strict majority.
  - E_SPP1_EXPR moves in the predicted direction with separated intervals in all
    three donors, but by at least two-fold only in SZ09 (+2.17 / +0.80 / +0.61).

### Strongest discordances

**No node is discordant.** Nothing moves against its prediction in 3/3 donors.
The strongest disagreements are two rows that do not move:

- **E_LIF** (direct transcript), no response within two-fold. LIF moves −0.26 / +0.59 /
  +0.46 with separated intervals, and every fold interval lies inside two-fold
  (widest: SZ10 [+0.50, +0.68]). The switch the cocktail is supposed to cause is
  not visible.
- **E_GP130_STAT3** (SOCS3 and BCL3 target program), no response within
  two-fold.
  SOCS3 −0.68 / −0.35 / −0.69, BCL3 −0.08 / −0.10 / −0.52, all inside two-fold.
  Both are on the decontX-corrected layer (see "Limits"). decontX correction
  depends on cluster, and the clusters are nearly determined by condition, so a
  flat CNT-vs-HT result on that layer is the kind an entangled correction could
  produce.
- **E_HBEGF does not qualify either.** HBEGF (raw-verified) is flat in
  SZ09 and SZ25, but in SZ10 its fold interval is **[+0.42, +1.03]** log2. That
  reaches past the two-fold margin by 0.03, so the donor is `indeterminate`.
  This is a knife-edge, and the margin was **not** adjusted to decide it.
- Earlier drafts called E_IHH, S_PGR, E_MUC1_SLEX and S_FGF_MITOGENIC discordant
  (and E_LIF, E_GP130_STAT3 "discordant, no material response"). All are
  withdrawn. E_IHH and S_PGR are imprecise (E_IHH is undetected in
  SZ09); the other two are not scored (see below).

### Post-closure correction: E_PC6 reads PCSK5

PC6 is PCSK5 (HGNC:8747). The frozen observation map measured `E_PC6` through
PCSK6 (HGNC:8569, formerly PACE4), a different convertase. The frozen map and
the node-support artifacts are kept unchanged as history. This table reads the
corrected map (`docs/scrna_corrections/scrna_observation_map_corrected.tsv`) and
the live evidence, in which every PCSK6-derived row is superseded. The PCSK5
values are a **post-hoc extraction, not pre-registered**. They were computed
with the audit's statistics unchanged, which the extraction proved by
re-deriving PCSK6 and reproducing the frozen rows byte for byte. See
`docs/scrna_corrections/README.md`.

| | PCSK6 (frozen, superseded) | PCSK5 (corrected) |
|---|---|---|
| epithelial detection, share of cells | 0.7–5.1 % | 50–67 % |
| per-donor call, CNT → HT | up / indeterminate / down | down / flat within two-fold / down |
| log2 fold, SZ09 / SZ10 / SZ25 | +2.10 / −0.67 / −1.11 | −1.17 / −0.22 / −1.66 |
| verdict against the predicted OFF → ON | mixed or inconclusive | mixed or inconclusive |

The verdict does not change, and neither does any class verdict or any other
row. Its content does: the corrected gene moves **against** the predicted switch
in two donors and is flat in the third. That is not `discordant_opposite`, which
needs 3/3. It is also a transcript share on the corrected layer: it says nothing
about PC6 activity or DAG1 cleavage, which is what the node represents.

### Alias classes challenged by RNA

**None is demonstrated in this table.** Two classes come closest:

- **AC04 — jointly no response within two-fold.** E_LIF and E_GP130_STAT3 agree
  with each other: neither moves. This is **not** recorded as a challenge. It is
  the shape a failed "cocktail switches this class on" rule would leave, but
  without a powered equivalence criterion, no response is not shown to be a
  failure to respond. It is also on the caveated layer. The node-support audit
  recorded it, under its own rule, as a weak `rule_challenged`.
- **AC01 — not demonstrated under this unit's rule. It is at the margin.**
  E_PAEP moves up 5–10-fold in 3/3 donors while E_HBEGF, in the same Boolean
  function, stays inside two-fold in 2/3 donors, with the third interval ending
  at +1.03. The pre-registered node-support audit, under its own rule
  (`no_material_move` = not ≥ two-fold with separated intervals), recorded AC01
  as **`alias_challenged`** and reproduced it on raw UMIs. That committed verdict
  stands and is carried in `node_support_audit_class_verdict`. Here, HBEGF in
  SZ10 falls 0.03 log2 short of being shown flat. Even if it had been shown flat
  in all three donors, this table would record
  `members_diverge_one_within_two_fold`, not a challenge, for the same reason as
  AC04. None of this is evidence that PAEP and HBEGF co-vary.

### Alias classes not challenged

- **AC02 (PRL / IGFBP1 / S_DECIDUALIZED / S_SPP1): mixed or inconclusive.** This
  is **not** evidence against the PRL = IGFBP1 alias. The two move together in
  SZ09 (down) and SZ10 (up) (PRL −1.41 / +3.86 / +2.04, IGFBP1 −3.87 / +4.49 /
  −0.17), and SZ25 is imprecise. The decidualization response **reverses sign
  between donors**, so the OFF→ON prediction is neither supported nor
  contradicted. The scRNA has a single timepoint, so it cannot test the timing
  claim that IGFBP-1 precedes PRL.
- **AC03 (E_PGR / E_IHH / S_PGR / S_NR2F2 / S_BMP2): mixed or inconclusive.**
  E_PGR moves strongly in SZ09 only. S_PGR and E_IHH are imprecise in every
  donor, and S_BMP2 reverses between donors. The epithelial-vs-stromal PGR
  asymmetry does not meet the bar, and `config/coupling_adjudication.tsv` stays
  `UNIDENTIFIED`.
- **AC05: no scored members.**

### Uninformative because the assay does not observe the model state

These are **reported, not scored**. Their RNA movement is in the table and on
the figure (hatched), but it cannot confirm or refute the modelled state at any
strength.

| Node | What the node means | Why the RNA cannot observe it (map text) |
|---|---|---|
| E_ITGAVB3_5 | ligand-engaged αvβ3/β5 receptor | subunit transcripts "do NOT distinguish an engaged receptor from an unengaged one" |
| E_CD98_CD9 | CD98/CD9 surface complex | "complex formation and surface presentation are not resolved" |
| E_DAG1_FULL | intact dystroglycan | one transcript for intact and cleaved |
| E_MUC1_BARRIER | apical anti-adhesive barrier | "apical presentation and glycosylation, neither resolved" |
| E_PODXL | apical anti-adhesive coat | "the node's meaning is spatial (APICAL) and scRNA has no spatial axis" |
| S_TAZ_ECM | TAZ nuclear localisation | "neither resolves TAZ nuclear localisation"; CTGF and CYR61 absent from the object |
| E_MUC1_SLEX | surface sLeX-decorated MUC1 | biosynthetic capacity; "does NOT distinguish a cell that carries surface sLeX from one that merely could make it" |
| S_FGF_MITOGENIC | FGF-driven mitogenic state | "receptor engagement is not resolved" |
| S_NR2F2 | NR2F2 regulatory activity | "regulatory activity is NOT resolved by this measurement" |

The first six are the map's `proxy_abundance_not_activity` class. The last
three carry other map classes (`gene_program`, `pathway_score`,
`regulon_activity`), but their own committed resolution text says the modelled
state is not resolved. They are excluded on the same ground, and a test fails if
that text leaves the map.

E_MUC1_BARRIER and E_PODXL transcripts rise with treatment while the model
predicts the barrier states switch OFF. **That is not a discordance:** a rising
transcript says nothing about apical presentation.

Two further rows are excluded for other reasons:

- **E_ESTROGENIC_PROLIFERATION: uninformative.** The prediction depends on what
  CNT was, which is still unresolved: no change if CNT was untreated, ON→OFF if
  E2-only. MKI67 and TOP2A fall in all three donors, but no verdict is taken.
- **E_KLF12_HIGH: descriptive only.** KLF12 log2 −1.44 / −0.62 / −1.29 is shown
  as a continuous quantity. There is no call, state or threshold. Phase 2B stays
  closed as `NO_SUITABLE_REFERENCE`.

## Flagged, not fixed

The committed observation map (`config/scrna_observation_map.tsv`) is the
authority for observation class here. Two entries look inconsistent and are
recorded in `classification_flag`:

- **S_HAND2.** The map says `direct_transcript`, but the node-support
  pre-registration's Appendix A prints it as a regulon/activity proxy. The map
  class is used.
- **S_NR2F2.** The map says `regulon_activity`, but its only feature is NR2F2
  itself, and its own resolution text says regulatory activity is not resolved.
  It is therefore not scored (above). Its class is not changed.

## Limits

- Three donors, a two-fold convention and a conservative interval bound give
  coarse verdicts. Many rows are `indeterminate` because the within-donor
  intervals are wide, not because the biology is flat. This measures how well
  model and data agree; it validates nothing.
- Every row except E_PAEP and E_HBEGF is on the decontX-corrected layer. That
  layer is condition-entangled, so its nulls (both AC04 no-response rows among them)
  carry the caveat. Re-deriving on raw UMIs needs about 3 GB of per-sample
  matrices and was not done here.
- The comparison is one bundled cocktail against CNT. The design has no
  single-agent arm, so no effect can be attributed to any one agent.
- A few genes vote in more than one node (GREB1 in E_PGR, S_PGR and
  E_ESTROGENIC_PROLIFERATION; HAND2 in S_PGR and S_HAND2; SPP1 in both
  compartments), so those rows are not independent.
