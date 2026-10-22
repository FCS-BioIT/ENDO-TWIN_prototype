# Next stage: deep-research adhesion delta (2026-09-11)

Handoff note for whoever picks this up. Written 2026-09-11.

## Status in one line

The bundle is **filed and verified, not integrated**. No canonical literature
table and no model file has been modified. Nothing has been promoted.

That distinction matters: "integrated" would mean rows merged into
`context/literature/*.tsv` and a v0.5.0 model built. Neither has happened, by
design -- `promotion_plan.tsv` gates every file behind review that has only just
begun.

## What exists now

| Path | What it is |
|---|---|
| `context/literature/staging/deep_research_adhesion_model_2026-09-11/` | The complete verbatim bundle: 12 files (11 manifest entries + `manifest.tsv`). Immutable. |
| `context/literature/reviews/…yaml` | Bundle provenance, scope, claim boundaries. Filed copy per `action=copy`. |
| `context/literature/reviews/…md` | The external reviewer's narrative review. |
| `context/literature/reviews/…staging-status.md` | Unpack-time mechanical verification. |
| `context/literature/reviews/…adjudication.tsv` | **Binding** accept/reject decisions. The promotion gate. |

Re-verify the bundle at any time: every one of the 11 manifest entries resolves
inside the staging directory and matches its recorded SHA256.

## Mechanical checks already done (do not repeat)

- All 11 SHA256 digests match; row and column counts match the manifest.
- `candidate_nodes`, `candidate_edges`, `mechanisms`, `references` headers are
  byte-identical to their canonical counterparts.
- No first-column ID collides with any canonical table.
- None of the 9 staged DOIs or PMIDs appears in the 70-row canonical
  bibliography -- all mechanically new.

## Adjudicated so far (4 blocking)

Recorded in the adjudication TSV with `blocks_promotion=yes`:

- `DRE009` `X_IL11 -> E_ITGA2B1` marked `confidence=verified` -- **REJECT**.
  The row's own note records integrin-alpha2 *expression/protein*, while the
  target node is defined as an adhesive receptor state ("surface ITGA2/ITGB1").
  `AGENTS.md` forbids substituting abundance for activity. PMID 19213836
  additionally reports alpha2beta1 neutralisation reducing **LIF**-induced, not
  IL11-induced, collagen-IV adhesion.
- `dr20260911_itgav_no_secretory_absorption` -- **REJECT**. Cites YAML key
  `structural_audit`, which does not exist.
- `dr20260911_lif_soft_surface`, `dr20260911_lif_hard_surface` --
  **UNRESOLVED**. Cite `priority_changes`, which contains no mention of LIF
  (`grep -ci lif` returns 0), so the expressions are underivable from the cited
  location. The hypotheses themselves remain worth keeping if re-sourced.

Two rows (`marker_free_epi_output`, `marker_free_stroma_output`) have resolving
provenance; their scientific merit is still unadjudicated.

## What remains -- Phases A to D, essentially all of it

**Phase A.** 9 references still need verification from strongest available
source (preferably full text). Then adjudicate all 14 staged nodes and 20 edges
as PROMOTE / MERGE_WITH_EXISTING / RULE_VARIANT_ONLY / UNRESOLVED / REJECT, with
reason and confidence each. Test whether BMP-SMAD, FOXO1, WNT4,
IL11/STAT3/ITGA2B1, SOX17, sLeX, FN1/COL4, ESR1, JAG1/NOTCH3 and hCG->CD98/CDH1
genuinely add *identifiable* information beyond v0.4, rather than node count.
Only then merge accepted rows into canonical tables.

**Phase B.** Independently review -- do not assume correct -- the claim that
hand-initialised interface relay priors should be replaced by explicit
finite-time attachment/detachment. Trace where absolute adhesion occupancy
actually comes from in the MaBoSS implementation; establish the computational
provenance of the non-`1/20000` probabilities; do not impose binomial or
trajectory-count uncertainty unless output semantics justify it. Prefer
independent complete-run replicate variability.

> **Phase B provenance question: attempted, abandoned, still OPEN.** A probe was
> built to measure the declared-horizon difference between the as-built chain and
> one with the bypassed maternal mifepristone phase inserted, and to read the
> mechanism off the continuation support and mass. It was **removed**: the mass it
> recorded was `1.0` by construction, because `project_joint_distribution`
> renormalises the retained distribution, and support cardinality is compatible
> with almost all the weight on a single state, so neither quantity could support
> a mechanism claim. Two conclusions drawn from it — a weighted-mixture
> explanation, and then a claimed refutation of that explanation — are both
> withdrawn.
>
> The lesson is the one Phase B already stated: the provenance of the
> non-`1/20000` probabilities must be traced in the MaBoSS/cmaboss **output
> semantics**, read directly, not inferred from output values. Every attempt to
> infer it from values has been wrong. A binomial SE and a `1/N` resolution limit
> remain unjustified and withdrawn, independent complete-run replicate
> variability remains the preferred candidate ruler, and nothing in the
> repository yet quantifies uncertainty on these numbers.

**Phase C — DONE 2026-09-12. Answer: it does NOT run.** Verified from executable
behaviour by resolving the protocol graph for the model version the concordance
build actually executes (`adoc-literature-superset-v0.4.0`) rather than by
reading `config/protocols.yaml`, which is ambiguous because protocol ids are
**duplicated across model-version families**:

* `adoc-core-v0.1.0` does chain
  `hormone_treated -> hormone_treated_mifepristone -> adhesion_challenge_hormone_treated_mifepristone`.
  A reader inspecting the YAML alone sees this and concludes the phase runs.
* `adoc-literature-v0.2.0` has no maternal mifepristone protocol at all, and its
  `adhesion_challenge_hormone_treated_mifepristone` continues from
  `hormone_treated_maternal`.
* The superset clone layer in `src/dt_adoc/protocols/conditions.py` builds
  v0.4.0 from **both**: it takes the v0.2.0 rows wholesale and additionally
  imports exactly three core rows — `hormone_treated_mifepristone`,
  `hormone_treated_anti_spp1`, `washout` — rewiring their `continuation_from`
  onto the maternal lineage. It does **not** rewire the adhesion challenges to
  consume them.

So the maternal mifepristone phase **exists, resolves, and is executable**
(`models/superset/adoc-literature-superset-v0.4.0/conditions/hormone_treated_mifepristone.cfg`
is present), embryo inputs **are** OFF within it — but it is **orphaned**:
nothing declares `continuation_from: hormone_treated_mifepristone`, so its
terminal distribution seeds nothing. The executed chain is

```
basal_maternal -> e2_primed_maternal -> hormone_treated_maternal
    -> adhesion_challenge_hormone_treated_mifepristone
```

and the challenge is seeded from the **hormone-treated** terminal joint state.
The standing instruction was followed: **the protocol was not changed.** The
concordance interpretation was corrected instead — earlier text claiming the
phase was *missing* is withdrawn as false; the defect is wiring, not absence —
and `MifepristoneArmLineageIsPinned` in
`tests/integration/test_concordance_runtime.py` now asserts the chain, the
phase's existence and its orphaning, so this cannot drift again.

The same wiring gap affects the other maternal perturbation arms. Stated
exactly, because an earlier revision of this paragraph called
`hormone_treated_anti_spp1` orphaned, which is **false and withdrawn** —
`washout` continues from it. `AllMaternalPerturbationWiringIsPinned` in
`tests/integration/test_concordance_runtime.py` pins the table:

| maternal phase | orphaned? | its adhesion challenge continues from | runnable? |
|---|---|---|---|
| `hormone_treated_mifepristone` | yes | `hormone_treated_maternal` (bypass) | yes |
| `hormone_treated_anti_spp1` | **no** — `washout` continues from it | `hormone_treated_maternal` (bypass) | yes |
| `hormone_treated_hand2_loss` | yes | `hormone_treated_maternal` (bypass) | yes |
| `washout` | yes | *(has no challenge of its own)* | **no**: superset `.cfg` absent |

The shared defect is the **bypass**, covering the **three** named perturbation
challenges (`adhesion_challenge_hormone_treated_*`): each is seeded from
`hormone_treated_maternal` rather than from the maternal phase whose name it
carries. `washout` is not one of them — it has no challenge of its own, so it
cannot bypass one; `adhesion_challenge_washout` continues from the *anti-SPP1
challenge*. Its problem is different and worse: it resolves but its superset
condition `.cfg` does not exist, so running it would fail. Repairing the suite is
a single coherent maternal-perturbation wiring decision and is the recommended
next task — it is **not** Phase D.

**Phase D.** Only then decide whether v0.5.0 is warranted. Preserve v0.4.0.
Settle line endings deliberately -- **all v0.4.0 model tables are CRLF, the
bundle is LF, and there is no `.gitattributes`**.

## Standing instruction from the source

The external reviewer asked explicitly that their topology **not** be reproduced
uncritically, and stated their own confidence as ~0.65 on the exact Boolean
formulations. Their stated priority is the attachment/detachment refactor, not
adding 14 nodes.
