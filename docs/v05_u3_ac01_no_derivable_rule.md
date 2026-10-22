# U3 — AC01: no replacement rule is derivable, and the closest candidate fails on evidence, not on structure

**Unit:** U3 of `docs/v05_mechanistic_integration_plan.md`.
**Outcome:** **no replacement rule adopted.** The alias stays in place and is
flagged. No rule, node, edge, threshold, rate, istate or recorded output changes,
and **no free Boolean variable was created** — the owner decision §7.1 records.
**Guards:** `tests/unit/test_v05_u3_ac01.py`.

This is one of the two admissible outputs §7.1 allows. It is not the same as
"nothing was found", and the difference matters: a candidate rule exists and it
is **structurally effective** — it breaks part of AC01 at no new node. What
excludes it is the **edge-promotion evidence**, on six of §5's eight edge
criteria. The structural result is kept as a diagnostic and is not treated as an
evidence basis, which is the ordering §0.4 and §5 were written to enforce.

---

## 1. The conditional basis still stands

U3's mandate is downstream of D1, so it was checked first rather than assumed.
At `1463e6b`, `docs/scrna/node_support_findings.json` records for `AC01`:

| field | value |
|---|---|
| `class_verdict` | `alias_challenged` |
| `depends_on_deviations` | `["D1"]` |
| `registration_status` | `post_extraction_semantic_repair` |
| `counterfactual_verdict_without_D1` | `unclassified_by_section_5_4` (computed) |
| `licenses_structural_change` | `true` |
| `raw_layer_sensitivity.condition_entanglement_status` | `resolved_for_PAEP_HBEGF_only` |

The recorded `artifact_sha256` for the raw sensitivity was re-derived and
matches. So D1 stands, U3 has a mandate, and **it is still a mandate downstream
of an interpretive call rather than of a measurement** (§0.7, §13.7). Nothing
below presents `AC01` as raw data.

## 2. AC01 is one structural fact, not nine modelling errors

Computed from the committed network, not asserted.

*Stated precisely after review, because an earlier revision blurred two different
things.* The claim is **not** that the nine members have an identical syntactic
upstream graph closure — they do not: `E_ITGAVB3_5` syntactically reaches
`E_KLF12_HIGH` through `E_LIF`, and the other eight do not. The claim is the
stronger one that survives reduction:

> **All nine members compute the same effective Boolean function, and the support
> of that function is `{IN_E2, IN_PROGESTIN, IN_MIFEPRISTONE}`.**

`E_KLF12_HIGH` is in `E_ITGAVB3_5`'s syntactic closure but **not in its
function's support**, because the arm carrying it is absorbed. That is verified
by exhaustive enumeration, which holds for both values of `E_KLF12_HIGH`, and by
the repository's own `load_structure`, which puts all nine in one alias class.

`E_ITGAVB3_5` is therefore the useful case: it already draws on a source the
others do not, and is aliased anyway. Its committed rule is

```
E_ITGAVB3_5 = E_LIF or E_HBEGF or E_SECRETORY_STATE
```

and with `E_LIF = E_SECRETORY_STATE and not E_KLF12_HIGH` and
`E_HBEGF = E_SECRETORY_STATE`, both disjuncts are subsets of the third. **The
rule is degenerate: it reduces to `E_SECRETORY_STATE` exactly**, verified by
exhaustive enumeration over the four variables the class depends on (16
assignments — exhaustive, not sampled, because nothing else reaches these
nodes), and again by the repository's own `load_structure`, which is exhaustive
over all 19 free variables.

So the alias is not nine independent mistakes. **The epithelial effector layer
has exactly one determinant and every effector hangs off it.** Breaking the
alias needs a second determinant that is *not* a subset of `E_SECRETORY_STATE`.
Adding an existing upstream node is not enough — `E_ITGAVB3_5` already does that
and is still aliased.

This also disposes of the one catalog variant aimed at the problem.
`dr20260911_itgav_no_secretory_absorption` (`E_ITGAVB3_5 = E_LIF or E_HBEGF`,
`catalog_only`) is annotated "removes bare OR E_SECRETORY_STATE so LIF/HBEGF
branches **can become** distinguishable". Measured against the committed model it
is **structurally inert**: 35 distinct Boolean functions before and after, AC01
still 9 members. It is a prerequisite for a repair, not a repair.

## 3. Every candidate edge into the class, enumerated

Every candidate edge into an AC01 member in `context/literature/candidate-edges.tsv`:

| edge | source → target | conf | tier | breaks AC01? |
|---|---|---|---|---|
| EDGE-033 | `E_SECRETORY_STATE` → `E_HBEGF` | 6 | core_extension | no — it *is* the alias |
| EDGE-018 | `E_SECRETORY_STATE` → `E_PC6` | 7 | core_extension | no |
| EDGE-019 | `E_PC6` → `E_DAG1_CLEAVED` | 8 | core_extension | no — both inside the class |
| EDGE-024 | `E_SECRETORY_STATE` → `E_MUC1_SLEX` | 5 | uncertain_variant | no; and it "requires a glycosylation program not directly measured", whose programme premise the audit **refutes** (FUT6 +1.60/+2.99/+2.73 against ST3GAL4 −1.11/−0.25/−1.45) |
| EDGE-006 | `E_GP130_STAT3` → `E_ITGAVB3_5` | 6 | core_extension | **no — absorbs.** `E_GP130_STAT3 = E_LIF ⊆ E_SECRETORY_STATE`, verified by enumeration |
| EDGE-034 | `E_HBEGF` → `E_ITGAVB3_5` | 5 | uncertain_variant | no — absorbs |
| EDGE-007 | `E_GP130_STAT3` → `E_ANXA2_ACTIN` | 4 | uncertain_variant | no; "no direct LIF-to-ANXA2 proof in this inventory" |

**`E_PAEP` has no incoming candidate edge at all.** Its committed rule has no
candidate-edge backing, and its registered evidence is `SOFIA-EPI-001` /
`SOFIA-EPI-002`, both `planned_use: calibration` from the ADOC study itself.

The `candidate-nodes.tsv` logic hints add nothing: `E_HBEGF`'s hint **is** the
committed rule (`E_SECRETORY_STATE`, notes "Likely support/rate modifier rather
than hard gate"), and `E_MUC1_SLEX`'s hint names the refuted glycosylation
programme.

Note also that **EDGE-006, a core_extension edge with confidence 6, is not
implemented in v0.4 at all** — and implementing it would change nothing, because
it absorbs. The most-supported unimplemented edge touching this class does not
solve the problem.

## 4. The one real candidate, and why it is rejected

`REF-059` (Jin 2025, *Mol Cell Endocrinol*) is about epithelial HB-EGF and hCG,
and `IN_HCG` is **declared in v0.4 and read by no rule** — exactly the shape of
repair that worked for `E_CD98_CD9` under TI001/DTR005. The candidate rule is

```
E_HBEGF = E_SECRETORY_STATE or IN_HCG
```

### A framework correction first: this is an EDGE, and it was judged as a node

*Corrected after external review.* An earlier revision of this section scored the
candidate against §5's numbered **node-admission** criteria — "passes §5(1) and
§5(4), fails §5(2) and §5(3)". That was the wrong rubric. §5 states that **"Node
and edge promotion stay separate decisions"**, and the numbered 1–4 sequence sits
under *Node admission*. `E_HBEGF` is an existing node; what this candidate
proposes is a new **edge**, `IN_HCG → E_HBEGF`, and a changed rule. Edge
promotion has its own criteria in §5, and those are what decide it.

Carrying the node rubric forward would have mattered beyond this unit: U4 is
largely about rule and edge families, and it would have inherited the wrong
framework.

### The structural result, kept as a diagnostic and not as a criterion

Computed with the repository's own exhaustive `load_structure`:

| model | distinct Boolean functions | AC01 |
|---|---|---|
| committed | **35** | 9 members |
| with `E_HBEGF = E_SECRETORY_STATE or IN_HCG` | **36** | **7** — `E_HBEGF` and `E_ITGAVB3_5` both leave |

This is a real and useful finding: **a structurally effective repair exists**, it
addresses the divergence P1 rests on, and it costs no new node. It is not free —
it creates a new two-member alias `{E_HBEGF, E_ITGAVB3_5}`, trading one alias for
a smaller one rather than separating the layer.

**It is a diagnostic, not an evidence basis.** §0.4 is explicit that Δ ranks
structural usefulness and that the prose criteria come first; a Δ result cannot
promote an edge, and §5's edge list contains no Δ term at all.

### The verdict under §5's edge-promotion criteria

§5: *"direction; causal vs associative support; species and system; compartment;
**activity versus abundance**; whether the rule needs AND/OR/graded semantics;
whether the Boolean abstraction overstates the evidence; and whether alternative
variants remain plausible — in which case it enters `rule_variants.tsv` as a
family, not the network as a fact."*

| criterion | verdict | basis |
|---|---|---|
| **direction** | **fails** | the edge needs `hCG → HB-EGF`. What REF-059 measures is the opposite orientation — epithelial `siHB-EGF` abolishing a **stromal** IGFBP1 increment, i.e. HB-EGF as an *output*. The incoming direction is the inferred link |
| **causal vs associative** | **fails** | *"the full hCG to PGF2a to EREG/HB-EGF chain was **NEVER tested end to end** … assembled from separate sufficiency experiments"*, and no arm applies hCG under PGF2α-receptor blockade or COX inhibition |
| **species and system** | **fails for a canonical rule** | human, but Ishikawa and T-HESC — *"both compartments are immortalised lines"*, not primary epithelium |
| **compartment** | **fails for the arm it would act in** | epithelium nominally, but *"there is no adhesion, attachment or embryo endpoint, so nothing here constrains the epithelial attachment arm"*, and `E_HBEGF` sits only there (`network.bnd:142`, `:218`) |
| **activity vs abundance** | **fails** | knockdown *"validated at mRNA level only"*, while the node is an effector state whose own claim ceiling reads *"Transcript only; HB-EGF is shed and acts extracellularly, which RNA does not see"*. This is the DRE009 failure mode `AGENTS.md` names |
| **AND/OR/graded semantics** | **fails** | `or IN_HCG` makes hCG **sufficient**. MOD-05's guidance is *"Prefer rate modifiers or redundant OR-gates, not a requirement that every effector be ON"*; `candidate-nodes.tsv` says *"Likely support/rate modifier rather than hard gate"*; `LIT-HBEGF-001` says the Boolean direction *"should remain supportive"* |
| **Boolean abstraction overstates** | **fails** | the reference's Fig 6 puts HB-EGF at maximum **LH+2 and near baseline by LH+7, before an embryo exists**. hCG is embryo-supplied, so the rule asserts a sufficient embryo-borne inducer in a window where the same paper measures the target at baseline |
| **competing variants remain plausible** | **yes** | the committed rule, the hCG variant, and a rate-modifier form are all live, and `REF-069` is a **registered unresolved contradiction** in the same hormonal context. §5's stated consequence is that it *"enters `rule_variants.tsv` as a family, not the network as a fact"* |

**Seven of the eight fail, and the eighth is the one that fixes the disposition.**
*(Corrected: an earlier revision summarised this as "six of eight", dropping
AND/OR/graded semantics from the count while leaving it marked `fails` in the
table. The individual verdicts are unchanged; the total was wrong.)*
The edge is not promotable. Its most it could be is an **evaluation-only
rule-variant family** — and U3 does not add one, because curating rule families
is where U4 works and doing it here would pre-empt that unit.

### The node-admission step it would also have to clear, and does not

Even setting the framework question aside, the rule changes `E_HBEGF`'s
determinant, so §5(1) applies to the reference it rests on.

**§5(1) is NOT satisfied.** §5 requires full-text verification *"recorded in
`primary-verification.tsv`"*. That ledger is
`context/literature/reviews/deep_research_drug_targets_2026-09-16.primary-verification.tsv`
— see §4a below — and **REF-059 has no row in it**. An earlier revision of this
document claimed §5(1) *passes* on the strength of `pdf_manifest.tsv` recording
`PDF-028` with `full_text_inspected = yes`. Those facts are real and are stated
below, but they are **not the claim-level ledger §5 names**, and substituting one
artifact for another silently is exactly the move §0.6 was written to prevent.

What is true: REF-059 is registered as `REF-059`, held as `PDF-028`, 13 pages,
`full_text_inspected = yes`, `registration_decision = registered`. What is not
true is that this satisfies §5(1). **An unsatisfied §5(1) is a further reason not
to promote the rule**, not a reason to relax §5.

### 4a. Where the verification ledger actually is

*Resolved by inspection of the committed tree and its history, not reconstructed.*

The plan refers to `primary-verification.tsv` in §0.6, §5(1) and §17. There is no
file at `context/literature/primary-verification.tsv`, and
`git log --all --diff-filter=ADR` over `*primary-verification.tsv` shows the name
has **only ever existed at one path**, added once at `f99e082`:

```
context/literature/reviews/deep_research_drug_targets_2026-09-16.primary-verification.tsv
```

So the plan's bare name is **shorthand for that review-scoped file**. Nothing is
missing, nothing was migrated, and nothing needs reconstructing. The
identification is checkable rather than assumed — every specific claim §0.6 makes
about the ledger matches that file exactly: 7 rows; genuine full-text reads
`DTR002`, `DTR006`, `DTR017`, `DTR026`; `DTR002-followup` *"PDF available,
unread"*; `DTR011` and `DTR005` abstract-verified via web search.

**No verification rows were added.** The plan says the ledger holds seven and it
holds seven; manufacturing an eighth for REF-059 would fabricate the very
provenance §5(1) exists to require.

**For U4:** its checklist says to record full-text verification of TI001/TI002/TI004
"into `primary-verification.tsv`". That resolves to the review-scoped path above.
Whether U4 appends to the Sept-16 file or opens its own review-scoped ledger is a
curation decision for U4 — U3 records the path and takes neither option.

### The two table rows that carry the most weight, stated in full

- **Window.** The reference's own Fig 6 puts EREG and HB-EGF *"at maximum at LH+2
  and near baseline by LH+7, before an embryo exists, so the route cannot be
  sited in the mid-secretory window on this evidence."* hCG is embryo-supplied.
  So the rule would make an embryo-borne input the sufficient determinant of a
  node that the same paper measures at baseline once an embryo could be present.
  That is not a gap in the evidence; it is the evidence pointing the other way.
- **A registered contradiction.** `REF-069` (Schatz 1986) — the only
  compartment-resolved measurement of endometrial PGF2α output — finds progestin
  *suppresses* the epithelial PGF2α source, in the same hormonal context REF-059
  asserts the route. The repository registers this as *"an unresolved conflict,
  not a refutation of either paper"*. An unresolved conflict is not a basis for
  canonical topology, and it is also why competing variants stay plausible.

And the registered evidence entry for this node says the same thing directly.
`LIT-HBEGF-001`: *"Direct Boolean direction is weaker than for LIF or PODXL and
**should remain supportive**"*, `planned_use: construction`, `status: candidate`.

## 5. A constraint on the other side of the pair

`E_PAEP` cannot be given a determinant derived from this audit either, and the
reason is circularity rather than absence. `PAEP` is one of the seven
`measurement_features` that **define** `E_SECRETORY_STATE`
(`PAEP;SPP1;CEACAM5;CEACAM6;DPP4;SCGB1D2;SCGB2A1`), and the observation map's
own claim ceiling for that node reads: *"This IS the P1-EPI-STATE construction
composite, so it is CONSTRUCTION evidence and cannot be concordance for the
epithelial state it built."*

So a rule tuned to make `E_PAEP` track `E_SECRETORY_STATE` while `E_HBEGF` does
not would be writing the construction composite into the topology and then
citing the same object as support — §13.1's laundering trap. The audit's
divergence is still a real finding about the pair; it is not a licence to derive
either half from the object that built the state.

## 6. What would unblock U3

Not more structural analysis — the structure is settled and exhaustive. What is
needed is evidence for a second epithelial determinant, in this order:

1. **An end-to-end test of an inducer → HB-EGF link in the receptive window**, in
   primary human epithelium rather than Ishikawa, with an attachment or adhesion
   endpoint. This is the experiment that would convert REF-059's candidate rule
   from assembled to established, and it is specific enough to cost.
2. **Resolution of the REF-059 / REF-069 conflict** on whether progestin
   suppresses the epithelial PGF2α source in the context the route is asserted.
3. **Any evidenced edge from `IN_HCG` or `IN_EMBRYO_CONDITIONED_SIGNAL` to an
   AC01 member.** Both are declared in v0.4 and read by no rule, so such an edge
   costs no new node — the cheapest structural gain available, as TI001 showed
   for `E_CD98_CD9`. `DTR005` records that for a *generic* embryo-conditioned
   inducer *"no source read names one"*.

## 7. What U3 did not do

It did not create a free Boolean variable for any member — rejected by owner
decision, and independently wrong on identifiability grounds (a free node is
`logic = <self>`, a Bernoulli flipped once from a hand-typed istate; and
`E_ITGAVB3_5` is a required conjunct of `X_ADHESION_ROUTE_SPP1` at
`network.bnd:214`, so a new one would sit directly on the adhesion prediction,
which Gate 3b criterion (i) forbids).

It did not adopt the hCG rule, adopt the inert catalog variant, split any node,
add an edge, change any rule or istate, promote `E_GLYCOSYLATION_PROGRAM`,
upgrade `AC03` (§7.3), or touch v0.4. The free-variable count is unchanged at
**19**, of which 5 are non-input, in both v0.4 and v0.5.

**It also did not renumber or resequence the plan.** U3 is recorded as
*attempted and negative* in place. A unit that looked for a rule and found the
evidence insufficient is a result; the alias stays, flagged, exactly as §7.1
allows.
