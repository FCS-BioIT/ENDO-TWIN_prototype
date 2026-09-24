# U6 — semantics and components

**Status: complete, schema only.** Branch `feat/v05-u6-semantics-components`,
based on `main` @ `7d9368f` (2026-09-23). No rule, node, edge, threshold, rate,
condition, phenotype or model version changed. `network.bnd` is untouched in
every version, and v0.4.0, v0.5.0 and v0.5.1 are unchanged.

U6 is the unit `docs/v05_mechanistic_integration_plan.md` §17 defines as
"semantics and components". It builds layer B of §1.3 — the component
requirement layer, the one that did not exist — and extends the node-semantics
generator to cover every node. It computes no gate, writes no `.cfg`, clamps
nothing and reads no expression value.

## What was delivered

| §17 item | where |
|---|---|
| Three semantic axes for all 59 nodes, from `observability.py` | `semantics_rows` → `docs/u6_semantics/node_semantics.tsv` |
| Owner decision on HGNC alias handling (`CTGF`/`CCN2`, `CYR61`/`CCN1`) | below; `components.HGNC_PREVIOUS_SYMBOL_RESOLUTIONS` |
| §6.3 combination table frozen before coding; exhaustive enumeration (T-D); empty groups raise | `components.combine`, `PRECEDENCE` |
| `provisional_corrected_layer_only` as orthogonal metadata with dual propagation; clamp veto (T-E2) | `components.Evidence`, `combine`, `clamp_permitted_by_evidence` |
| Component map with `requirement_group`, `logic`, `role`, `symbol_as_committed`, `resolution_status`, `variant_id` / `requirement_set`; default `undeclared`. §17's `resolution_status` is not one column: it is carried as four, `committed_symbol_status`, `current_hgnc_symbol` + `hgnc_id`, `alias_resolution` and `current_symbol_presence` (owner decision, below) | `components.COMPONENT_FIELDS` → `docs/u6_semantics/component_map.tsv` |

Regenerate both artifacts with `pixi run build-u6-semantics`. Both are
generated, and `tests/unit/test_v05_u6_semantics.py` fails if either one differs
from what the generator emits.

## Decisions and resolved conflicts

**1. The observation map is not extended in place.** §17 says "extend
`observability.py` to emit the three axes". `observability.py` writes
`config/scrna_observation_map.tsv`, which is a T-G Tier-1 artifact:
byte-identical to the evidence root `91f79ed` and required to regenerate byte
for byte. Adding columns to it would move the evidence root. The generator was
therefore extended with a **second output** instead. `FIELDS` and `CURATION` are
unchanged. `test_the_evidence_root_inputs_are_untouched` asserts that the map and
`node_rna_interpretability.tsv` are byte-identical to their `91f79ed` blobs
**wherever that commit is reachable**, and fails if the commit is reachable but a
blob is missing. Where the commit is not reachable (a shallow clone, a synthetic
review snapshot) or the tree is not its own git work tree, the test skips and
names which of those it was. No test in this repository requires full history,
so this one does not either. The regenerate-byte-for-byte test in
`test_scrna_observability.py` runs everywhere, regardless of git.

**2. The axes come from one derivation, not a new one.** For the 27
RNA-assessable nodes, `semantics_rows` calls `node_support.interpretability_rows`
— the function that produced the frozen `node_rna_interpretability.tsv` — and
the test checks every shared column against that frozen file. The other 32 nodes
get `not_RNA_assessable`, with both establishment axes set to `not_applicable`.
This is a fourth state, not missing data (§1.2). The view carries no
model-version property (function class, phenotype inertness), because U5b
changed inertness in v0.5.1 and a view keyed to no version must not assert one.
No `config/model_node_semantics.tsv` was created (§1.3).

**3. Failed versus undefined integrity controls stay distinct.** The frozen
vocabulary maps onto the four-state enum of §1.2. `uninformative_integrity` (a
C1 control ran and failed) and `uninformative_no_integrity_control` (no C1 is
defined for the compartment) both coarsen to `INDETERMINATE`. Each keeps its
reason verbatim, the two never compare equal, and a combined result keeps every
component's reason. Every support call committed in `node_support_findings.json`
maps under this rule, and any unknown label or reason raises.

**4. No requirement structure is declared, and this is a finding, not a gap.**

*`E_ITGAVB3_5` — a specification conflict, resolved in favour of §6.2.
Accepted by the owner, 2026-09-23, and declared in the harness as a
`SEMANTIC_OR_PROTOCOL` repair whose semantic surface names this decision
(`aih repair --show`: `semantic_change: true`). A first declaration was replaced
by a later `aih repair` call in the same round and never reached the record; the
declaration now on record is the re-recording.* Three committed statements
disagree:

- the plan's §6.1 calls `ITGAV AND (ITGB3 OR ITGB5)` biologically justified;
- the plan's §6.2 admits a requirement structure only when a **cited source**
  states it;
- the committed `models/superset/adoc-literature-superset-v0.5.1/node_dictionary.tsv:32`
  describes the node's observation as "surface ITGAV **or** ITGB3 **or** ITGB5".

No registered source in the repository establishes the exact component
requirement structure. §6.1 is a design argument, not a citation, so §6.2
governs the U6 output: `E_ITGAVB3_5` is `requirement_structure = undeclared`,
which evaluates to `INDETERMINATE` and creates no constraint. This is deliberate
scientific conservatism, not missing implementation. No requirement group was
added. Declaring either reading would settle the contradiction by fiat; a later
declaration needs a registered source that states the structure. The same rule
leaves every other node without a declaration:

- 26 of the 27 assessable nodes are `undeclared`.
- `E_CD98_CD9` is `requires_definition`, as §6.2 names it. Its own dictionary
  row reads "CD98 or CD9" in the label and "CD98 and CD9" in the observation
  column.
- `E_GP130_STAT3` carries no node-level set, and no variant set either. GP130-b
  is not a row of any `rule_variants.tsv`, and §6.1's IL-11 route has no
  declared components. A `variant` set must name a `(variant_id, node)` pair
  declared in the governing model's `rule_variants.tsv`
  (`components.GOVERNING_MODEL`, v0.5.1); the loader rejects an unknown id or
  one declared for a different node.

`DECLARED_REQUIREMENTS` is empty and a test pins it empty. The declared-group
path is exercised only on synthetic fixtures (an `A AND (C OR D)` shape, empty
groups, two roots, unknown and unreachable groups, and groups declared twice), so
the first real declaration lands in code that is already tested. It must bring
its cited source with it.

**5. Roles are carried.** Each assessable node has two kinds of rows:
`support_feature` rows (its committed `measurement_features`) and
`direction_readout` rows (the symbols of the committed direction-vote program
after R1 and R2, as computed by `node_support_contract.direction_vote_programs`,
not transcribed). For `E_GP130_STAT3` they differ: STAT3 is measured, but by R2
it does not vote (§6.1). A `direction_readout` row says a symbol is in the
program, not that it contributed to the frozen audit's vote. `S_TAZ_ECM`'s
program lists `CTGF` and `CYR61`, but both were absent from the audited
namespace, so the audit voted on `WWTR1`, `FN1` and `COL4A1` only. The rows keep
`committed_symbol_status = feature_absent`, and both symbols stay unusable until
a registered alias extraction verifies `CCN2`/`CCN1`.

**6. `rna_can_constrain` / `rna_can_hard_off` are not emitted.** §1.3 mentions
them as derived columns. Defining when RNA may hard-off a node is the clamp rule
of the gate layer, which §0.2 and U7 block, so writing it here would decide that
rule early. U6 provides only the evidence-side veto,
`clamp_permitted_by_evidence`. It is true only for a confirmed powered absence,
and it is necessary for a clamp, not sufficient.

## HGNC alias handling — owner decision, 2026-09-23

**Adopted: explicit, forward-only, per-symbol resolution.**

- `CTGF` → `CCN2`, HGNC:2500.
- `CYR61` → `CCN1`, HGNC:2654.

Both are 1:1 renames, verified against the HGNC REST service
(`rest.genenames.org`) on 2026-09-23. Each old symbol is a `prev_symbol` of
exactly one approved gene, and both carry `date_symbol_changed` 2018-10-11.

- **The frozen scRNA audit is not altered or reinterpreted.** It ran with
  `CTGF`/`CYR61` absent under the committed symbols, substituted nothing, and
  `S_TAZ_ECM` voted on `WWTR1`, `FN1` and `COL4A1`. That stands.
- **`feature_absent` means that the committed symbol was absent from the audited
  feature namespace.** It does not mean the gene is absent, and the component map
  keeps these apart as separate fields: `symbol_as_committed`,
  `committed_symbol_status = feature_absent`, `current_hgnc_symbol`, `hgnc_id`,
  `alias_resolution = verified_rename` and `current_symbol_presence =
  unverified`.
- **Whether `CCN2`/`CCN1` are present in the 78,724-feature object is
  unverified.** No `S_TAZ_ECM` evidence may use an alias-resolved feature until a
  new, registered extraction checks this. `usable_feature_symbols` returns only
  symbols that were present under their committed names. `verified` is not yet a
  legal value of `current_symbol_presence`, so that extraction will show up as a
  schema change. U6 did not load the RDS.
- **No general symbol normaliser exists.** The resolution table may name only
  symbols that the audit recorded as absent, and both the generator and a test
  refuse anything else. This is the same pattern as `_ANALYTE_TO_SYMBOL` in
  `observability.py`.
- The Boolean rule for `S_TAZ_ECM` is not touched.

## What U6 did not do

- It made no `network.bnd` edit and created no v0.5.2.
- It did not start the MUC1 rule family (U6b).
- It promoted no candidate node and did not de-alias PRL/IGFBP1.
- It did not split the integrin node.
- It did no mutation-interface work (U7) and no Stage-3 rerank (U8).
- It did not touch the frozen experiment.
- It edited no file under `IMPLEMENTATION_GLOBS`.
- It did not implement T-G's digest-based two-tier pinning. §17 records it as
  held since U1, but a search of `tests/`, `src/`, `docs/` and `config/` for the
  current sha256 digests of the map, the interpretability table and the evidence
  table found no pin. The guards identified for the two inputs U6 reads are
  `test_line_endings.py`'s endings convention and the map's
  regenerate-byte-for-byte test; this was not an audit of every guard in the
  repository. U6 adds the conditional blob-identity check described above. Full
  T-G remains owed, and is recorded here rather than silently assumed.
