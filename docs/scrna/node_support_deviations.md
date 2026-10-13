# Deviations, errata and clarifications against the registered pre-registration

`docs/scrna/node_support_preregistration.md` is the **registered** design. It is
byte-identical to the version committed at `491b337`, and
`tests/unit/test_node_support_preregistration.py` pins its sha256 so that it
cannot be edited again without a visible, deliberate change to a test. Errors in
it are corrected **here**, not there.

That is the opposite of what happened first. The registered document was
initially amended in place — 212 lines across the results commit — so that git
could no longer establish when any of those lines was written. The results were
unaffected, but the provenance guarantee was, and a pre-registration that can be
edited after the fact is not one. The repository owner directed the restore.

> Registered file sha256:
> `77f353359913c970784bc9aa15d9f3a075bd4e8db1d358b2ca3cfa61e6b8186a`
> (git blob `f10fcaf11630fa76e815b43a7c773acccaf1216f` at `491b337`).

## How to read the ordering claims below

**The only ordering git can establish is `491b337`.** Everything in this file was
written after that commit. Where an item below is marked *pre-extraction*, that
claim rests on the session record and on the content of the intermediate review
reports — **not** on git history, because the change was not committed before
extraction began. Read those marks as weaker evidence than the registration
commit itself, and weigh the items marked *post-extraction* accordingly: they
were made with results in view.

**One conclusion does depend on an item below, and the dependence is exact.**
An earlier version of this paragraph said no load-bearing conclusion did. That
was false, and it was false about the single post-extraction interpretive call
in this audit, which is the worst place to be wrong.

`AC01`'s `alias_challenged` verdict rests entirely on **D1**, the re-reading of
§2.1's direction-vote guard. Recomputing `class_verdict` over the committed
member verdicts under the *other* reading — every single-gene member
`uninformative` — gives:

| class | as reported | under the rejected reading |
|---|---|---|
| `AC01` | `alias_challenged` | **`unclassified_by_section_5_4`** |
| `AC02` | `unclassified_by_section_5_4` | unchanged |
| `AC03` | `unclassified_by_section_5_4` | unchanged |
| `AC04` | `rule_challenged` | unchanged |

`E_PAEP` is the only `concordant_with_alias` member in `AC01` and it is
single-gene, so the rejected reading removes the concordant half of the
challenge and nothing else moves. **Everything `AC01` carries falls with it**:
§5's "yes, and narrowly", P1, and the §8 reranking argument.

`AC04` does **not** depend on D1 — its `rule_challenged` verdict is identical
under both readings — and neither does any node-support label, any QC verdict,
or the finding that no node reached `not_detected_with_power`.

D1's merits are argued in §3 below from text frozen at `491b337`, independently
of the result it produces. That argument is what the reader should scrutinise;
this table is what tells them how much rides on it. The thresholds themselves
are unchanged and provably so (§4), but that proof covers the contract
constants and says nothing about D1.

---

## 1. Clarification added before extraction: gene-to-node aggregation

*Pre-extraction, by the session record; not committed before `258f07f`.*

The registered §4 defines `f` and `d` **per gene** but assigns §4.2's labels
**per node**, and nine of the twenty-seven nodes are measured by two to ten
genes. It does not say how to get from one to the other. The rule used is:

- **`f_node`** — the summed corrected values of **all** the node's committed
  features over the unit's total.
- **`d_node`** — the share of the unit's cells carrying **at least one** of the
  node's features (module detection, not a per-gene average).

Per-gene `f` and `d` are reported for every feature regardless, and the §5
direction vote uses **genes, never `f_node`**, exactly as registered §2.1 sets
out.

**The label that licenses a structural change does not depend on this choice.**
`d_node = 0` under the union rule means every one of the node's features is zero
in that unit, which is the same set of units any aggregation would call
undetected, so `not_detected_with_power` is invariant to it. What the choice can
move is the `robustly_detected` / `sparse_or_low` boundary, and neither licenses
anything. `test_a_node_is_undetected_only_when_every_feature_is` pins the
invariance.

---

## 2. Errata — statements in the registered document that are wrong

The registered text is left as written. These are the corrections.

### E1 — §0's blindness enumeration is too narrow

*Pre-extraction.* §0 names `docs/scrna_observability.md` and
`docs/scrna/klf12_raw_umi_evidence.tsv` as "the only single-cell numbers that
existed when this was written". Two further committed artifacts were used, both
reachable from `58f0fba` (committed at `c81f54f`):

| artifact | what the design took from it |
|---|---|
| `docs/scrna/klf12_state_evidence.tsv` | the six epithelial units' cell counts and **corrected** median depths, for §4.1's exposure argument |
| `docs/scrna/klf12_state_findings.json` | `marker_detection` — the pooled `EPCAM` / `VIM` / `COL1A1` rates the C1 and C2 controls rest on |

None carries a value for any **audited** gene. `EPCAM`, `VIM` and `COL1A1` are
controls and are measurement features of no node; KLF12 is audited for node
support only and its row is tagged `not_blind` for exactly this reason.

### E2 — Appendix A prints a measurement type the map contradicts, for two rows

*Pre-extraction.* The type column was typed by hand. Twenty-five of the
twenty-seven rows agree with `config/scrna_observation_map.tsv`; two do not.

| node | registered Appendix A prints | the map records | corrected type |
|---|---|---|---|
| `S_HAND2` | regulon/activity proxy | `direct_transcript` | **direct transcript** |
| `S_FGF_MITOGENIC` | abundance proxy | `pathway_score` | **pathway score** |

`test_appendix_type_errata_match_the_map` asserts that these two rows are
*exactly* the rows that disagree, and that the corrected values are the
map-derived ones. Registered §7's vocabulary also has no entry for
`pathway_score`; it is treated as its own type rather than folded into
`gene_program`, which would assert a ceiling the map does not record.

### E3 — the document is not "committed on its own"

*Pre-extraction.* §0 says the document was "committed on its own, as the first
commit of this unit". `491b337` carries **four** files — the document, the
Appendix-A generator, the decision contract in code and the tests that pin both
— and no extraction output. The substance of the claim holds and is checkable
with `git show --stat 491b337`; the wording does not. A threshold frozen only in
prose is not frozen, which is why the contract and its tests belong in that
commit.

### E4 — the grid has eighteen cells but seventeen units are written

*Post-extraction.* §1 says `myofibroblast` "adds six further compartment-units,
so eighteen are written to the artifact". Eighteen is the size of the
3 × 2 × 3 grid. `SZ09` contributes **no** `myofibroblast` cells in the HT arm, so
that cell is empty and writes no row: the artifact carries **seventeen**. The 365
myofibroblast cells divide 96 / 180 / 2 / 6 / 81 over five units, and the
committed 282 CNT + 83 HT split in `docs/scrna_observability.md` agrees.

The design is unaffected — every `myofibroblast` unit fails `n_min` and none was
ever going to carry the audit — but a reader reconciling the grid against the QC
table would have found a row missing with no way to tell whether it had been
dropped. The derivation now emits `grid_cells_expected`, `units_written` and
`empty_units` in `node_support_findings.json`, so the reconciliation is in the
artifact rather than in prose.

### E5 — two claims about v0.4's graph that `network.bnd` contradicts

*Post-extraction, and both introduced while repairing the one before.* The
finding document's phenotype section asserted a path through the network twice,
and was wrong twice.

1. **"The route from `E_PAEP`/`E_HBEGF` to an `OUT_` node runs through
   `E_ITGAVB3_5`."** False: `network.bnd:226` is
   `OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE and E_PAEP`, so `E_PAEP` is a
   **direct conjunct** of an `OUT_` node. The claim also understated the audit's
   reach, which is the more embarrassing direction to be wrong in.
2. **"The SPP1 adhesion route does not carry `E_PAEP` or `E_HBEGF`."** Written to
   repair the first, and false in the same class: `network.bnd:126` is
   `E_ITGAVB3_5 = E_LIF or E_HBEGF or E_SECRETORY_STATE`, so `E_HBEGF` is a
   **direct input** of the node that defines that route. The claim held only
   under a token-membership reading of one rule string, which the surrounding
   prose did not support. The test guarding it, named for a route property,
   checked exactly that token membership — its name asserted what its body never
   tested.

Tracing influence through a Boolean network by eye is evidently easy to get
wrong, and no conclusion in this audit needs it. The section now states only
literal committed rules, quoted with their line numbers, and the
`phenotype_inert` result computed separately by a 524,288-state sweep.
`NetworkClaimTest` asserts that each quoted rule is the rule at the cited line,
that each appears in the document verbatim, that the inertness flags match the
map — and that the document contains no transitive route phrasing at all, which
is a guard on the error's shape rather than on either instance of it.

---

## 3. Implementation defects found during the run

*Post-extraction.* Both were corrections to **code**, against rules that already
stood. Neither rule was edited.

### D1 — the direction-vote guard was read as a size test

Registered §2.1: *"A program reduced below 2 voting genes **by R1/R2** cannot be
direction-called."* The implementation applied it to any program with fewer than
two genes, which returned `uninformative` for all eleven single-gene members.

That reading is refuted by text frozen at `491b337`, independently of any result:
§2.1's own table enumerates those eleven under the heading **"genes voting"**
with `n = 1`, and none of them was *reduced* by anything — they measure one gene
by construction. `config/scrna_observation_map.tsv` also records, for `S_PRL`,
that a `S_PRL`/`S_IGFBP1` divergence "is a FALSIFICATION of the aliasing, not a
limit on the assay", which is impossible if both members are undecidable. The
code now votes with the single gene where there is one, applies "both must agree"
at exactly two and a strict majority above two, exactly as registered.

A feature absent from the object is handled separately and is never substituted
by a synonym: see §5.

### D2 — `uninformative` was returned for a pattern §5.4 does not name

Registered §5.4's `uninformative` has a **stated condition**: "fewer than two
direction-callable members". `AC02` (five `inconsistent` members) and `AC03` (two
`divergent`, three `inconsistent`) satisfy none of the four verdicts' conditions
while having five callable members each, so reporting them as `uninformative`
asserted something false about the evidence.

They are reported as **`unclassified_by_section_5_4`**, carrying the member
census. **It licenses nothing.** It was introduced after extraction and is
therefore disqualified from supporting any structural claim; it exists so the
artifact does not misreport which branch of the frozen rule was taken.

**Owner decision, recorded here and not applied to this audit:** the current
audit keeps `unclassified_by_section_5_4` exactly as recorded. Before the *next*
unit the taxonomy is to be made exhaustive with a generic catch-all —
`mixed_or_inconclusive`, defined as ≥ 2 callable members and none of the other
patterns, licensing no structural change. Defining it generically, in advance,
is what keeps it from being a category designed around `AC02` and `AC03`'s
observed results.

---

## 4. Changes to the frozen contract after registration, and proof they moved nothing

`src/dt_adoc/scrna/node_support_contract.py` was also modified after `491b337`.
Unlike the document it is not restored, because two of the three changes fix real
defects and reverting them would reintroduce a bug. What matters is whether any
of them moved a number, and none did. Executing the registered contract and the
current one against the committed observation map:

```
r1_programs identical:                         True
direction_vote_programs identical:             True
THETA N_MIN E_MIN C1_FLOOR ROBUST_DETECTION    same
LOG2_FOLD_MIN BOOTSTRAP_{B,SEED,ALPHA}         same
MIN_VOTING_GENES C1_GENE C2_GENE               same
DONORS CONDITIONS PRIMARY_COMPARTMENTS         same
COMPARTMENT_OF_LABEL ALIAS_TEST_ORDER          same
R2_EXCLUSIONS                                  same
```

The three changes:

1. **R1 grouped every classless row into one class.** The map leaves
   `v04_function_class` empty for the four rows it treats as classes of one, and
   keying on that raw value made `KLF12` and `HAND2` count as siblings' whole
   measurements for `E_ESTROGENIC_PROLIFERATION` and `S_FGF_MITOGENIC`. It
   deleted nothing on the committed map — neither gene appears in those two
   programs, which is why `r1_programs` is identical above — but the rule applied
   was not the rule registered, and a later map edit would have removed a voting
   gene silently. Each classless row is now its own class.
2. **`pathway_score` is no longer folded into `gene_program`** (E2). This changes
   a descriptive label in the Phase-A table, not a criterion.
3. **`LEVEL_CEILING_QUOTES` was added**: the three rows R2 deliberately does
   *not* exclude are now quoted and verified against the map exactly as the two
   exclusions are. Verification only; it excludes nothing.

---

## 5. Recorded limits carried forward to v0.5 planning

Not deviations — decisions and constraints this audit hands on.

**`CTGF` and `CYR61` are not in the object under those symbols.** Registered §2
forbids substituting a synonym, so none was used and `S_TAZ_ECM` voted on its
three present features (`WWTR1`, `FN1`, `COL4A1`), above the two-gene floor, with
the gap recorded. **Owner decision:** the current audit stays as run; HGNC alias
handling (`CTGF`/`CCN2`, `CYR61`/`CCN1`) is to be reconsidered explicitly before
any `S_TAZ_ECM` evidence is used in v0.5.

**`AC01` is not to be repaired with free Boolean variables.** An earlier draft of
`node_support_finding.md` proposed giving the divergent members "distinct
variables with determination recorded as open". **Owner decision:** that replaces
a false equality with unconstrained biology, which is not an improvement. `AC01`
is accepted as evidence that the identity requires **mechanistic
reconsideration**, and defensible replacement rules are to be derived from
literature together with this audit, in the mechanistic-integration work, rather
than asserted here. `AC04` likewise says *the current activation rule is
challenged*, not *split these nodes*.

**`dropout_e2` must be reranked, and this audit does not predict the outcome.**
The `AC01` result attacks an assumption that contributed to that arm's
discriminating power, so a rerank against an adopted v0.5 is mandatory. Whether
`dropout_e2` remains the best choice is an output of the new model, not a
conclusion of this audit.

**No raw-matrix fetch is required for an absence.** Zero nodes reached
`not_detected_with_power`, so no conclusion rests on an absence and the
decontX-zero question does not gate anything proposed.

**A raw re-derivation was nonetheless run, for a different reason.** Registered
§3.2 says the correction is condition-entangled and that the caveat applies to
presence as well as absence, and an earlier draft of the finding waved that away
for `AC01` with an argument assuming decontX is uniform, which it is not. An
external review raised it as blocking. `AC01`'s two load-bearing genes were
therefore re-derived on raw UMIs under the identical frozen rule
(`docs/scrna/node_support_raw_sensitivity.json`): the join is complete at 20,441
cells and the divergence reproduces — `PAEP` `moves_up` 3/3, `HBEGF`
`no_material_move` 3/3, every fold within ~0.2 log2 of its corrected
counterpart. The sensitivity introduces no threshold of its own; a test asserts
that every constant it uses comes from the frozen contract.

**One defect in that sensitivity is worth recording, because of its shape.** Its
first run matched *zero* cells — the object's cell names are
`{sample_id}_{barcode}` and `sample_id` itself contains an underscore, so
splitting on the first one recovered no barcode — and it nonetheless reported
`divergence_reproduced_on_raw: false`. A check that can fail silently in the
direction of refuting its own subject is worse than no check. It now refuses to
emit a verdict when a join is empty or more than 1% incomplete, and returns
`not_evaluated` rather than `false` when any donor is uninformative.
