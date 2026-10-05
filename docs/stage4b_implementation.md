# Stage 4b §10 — implementation record, 2026-10-04

**Status: IMPLEMENTED against the merged pre-registration
`docs/stage4b_direct_admission.md` (main `ea7f5ed`).** This note records what
was built, the readings the implementation had to make where the contract does
not decide, and the owner decisions taken on the three points where it could not
proceed without one. The pre-registration itself is not edited.

**Still not done, deliberately:** no real declaration, approval or
`direct_supported_effect` row exists; the committed declarations table and
ledger hold a header and no row. Stage 4c and 4d are not started. No partial
engagement exists anywhere. `E_ANXA2_ACTIN` and `S_PKA` stay `ambiguous`
(§11.2), and `E_ITGAVB3_5` stays unapprovable until TI-03 (owner decision 7).
The dated correction notes of §5.5 are outside §10 and were not written.

## 1. O8b retrospective independent review (before any 4b code)

O8b's original acceptance was **degraded**: every verdict came from the
same-family stand-in reviewer, and the record for its final state reads
`PASS`, `degraded: true`. That record stands and is not rewritten; this is a
separate, retrospective review.

| field | value |
|---|---|
| subject | the O8b merge range, `1052ff7` (pre-O8b main) → `1517eec` (merge of PR #19, the state Stage 4b was based on) |
| trees | base `782b2455`, reviewed `0b657c8d` (the tree of `1517eec`) |
| scope | 22 files, 2165 semantic lines, tier `full`, attested |
| reviewer | Codex (`gpt-5.6-sol`, high), independent, not degraded |
| verdict | **PASS**, fingerprint `02d259922887…`, one broad sweep, no blocking finding |
| advisory | two `UNCONSULTED_DECISION` notes: the "full or near-complete target-activity loss" approval definition, and the classification of v0.6.0 roles and four node exceptions as eligible or refused |

Both advisories name decisions the owner has since taken explicitly: Stage 4b
owner decision 2 (engagement) and the O8c policy, which decision 3 keeps
separate from expressivity. No defect was found, so O8b is unchanged.

## 2. What was built (§10 items 1–3)

| file | role |
|---|---|
| `config/node_entity_map.tsv` | 93 rows: the 45 v0.6.0 nodes in 57 rows (one per entity and level), plus the 19 §3.5.1 floor items in 36 model-gap rows (amendment A2); the 4 catalog_only gaps of §10 are 6 of those rows |
| `config/direct_effect_target_declarations.tsv` | header only |
| `config/direct_effect_adjudications.tsv` | header grows from 15 to 17 columns: `system_grade`, `target_declaration_sha256` |
| `src/dt_adoc/perturbations/adjudication.py` | `load_entity_map`, `load_declarations`, `check_admission` (C1–C8, §6.1 items 4–5), `system_grade`, `construction_overlap`, `expressivity_classes`, `admission_record` |
| `src/dt_adoc/perturbations/engine.py` | `_license_direct_effects` calls `check_admission` after every O8b approval, and also with no direct row, so a malformed map or a declaration of a non-direct intervention refuses the library |
| `src/dt_adoc/simulation/runner.py` | `executed_network["direct_admission"]`, the §6.5 record |
| `src/dt_adoc/closure_replay.py`, `src/dt_adoc/concordance/simulate.py` | the two new config files in `POST_CLOSURE_FILES` and `IMPLEMENTATION_GLOBS`; the expressivity generator, the observation map and both expressivity tables also in `IMPLEMENTATION_GLOBS` (amendment A1) |
| `pixi run validate-direct-effects` | now also requires both expressivity artefacts current and validates the map and the declarations (§6.6) |
| `tests/unit/test_stage4b_admission.py`, `tests/integration/test_stage4b_admission_runtime.py`, `tests/fixtures/stage4b/` | gate G13 |

Every §6.1 failure refuses the whole library, names the intervention, the node
or entity and the rule (`(C3)`, `(C8)`, …), and falls back to nothing (§6.6).

## 3. Owner decisions taken during implementation (2026-10-04)

Each was a point where implementing the contract exactly would otherwise have
broken an existing gate or required a reading the contract does not give.

1. **The O8/O8a/O8b synthetic fixtures move from v0.5.2 to v0.6.0.** §6.1 makes
   every direct licence depend on a per-version entity map and expressivity
   artefact, and §10 builds both for v0.6.0 only. Kept strict: a version with
   neither cannot hold a direct row. `synthetic_compound_x` and `_y` now run on
   v0.6.0 with synthetic declarations. `_y`'s second target moved from
   `E_ITGAVB3_5`, which C5 refuses, to `S_TAZ_ECM`. Two consequences:
   - "direct + legacy" composition is no longer possible by construction, since
     legacy rows exist only on marker versions. The tests now compose direct
     with migrated rows.
   - G11's marker-equivalence schedules stay on v0.5.2, because they need
     markers. Its named-compound protocols run on v0.6.0.
2. **N+1 is four appended files plus two regenerated tables.** The expressivity
   artefact has one arm per veto-mode library intervention (§5.1), so admitting
   a compound adds an arm and changes the class-member lists. G13 asserts:
   - the register, declarations, ledger and library change only by appending;
   - the two `docs/stage4b` tables equal exactly what the committed generator
     writes;
   - `models/`, `src/` and `config/node_entity_map.tsv` are byte-identical.
3. **§3.5.1 floor items are cited by id.** The floor tables are keyed by node
   id, not entity, and the map carries entity readings only for the four
   catalog_only gaps. An `unrepresented_known_targets` entry names the floor item
   it falls under (`floor:<id>`) or `none`. Two cases are refused: a floor item
   classified `out_of_scope`, and an entity a model-gap row carries without its
   gap id. An entry naming no floor item, for an entity no gap row carries, is
   J2 reviewer judgement. The known weakness: a declarer can fail to link a
   floor item whose name does not match, and only a reviewer catches that.
   **Superseded by amendment A2 (§3a):** independent review showed the weakness
   lets an unlinked IL11 pass as `out_of_scope`, against §3.5.1's "is
   refused"; the owner chose to close it mechanically. The `floor:<id>` syntax
   stays.

All three are recorded with `aih repair --kind SEMANTIC_OR_PROTOCOL`, together
with amendments A1 and A2.

## 3a. Amendments after independent review (owner, 2026-10-05)

The final broad sweep raised two blockers that were not code defects but places
where the frozen text pulls two ways. Deferring them on the existing readings
was contested by the reviewer; the owner decided both. They amend
`docs/stage4b_direct_admission.md`, which is itself left unedited.

- **A1 — the implementation digest covers the expressivity dependency set.**
  §9 kept `reporting/veto_expressivity.py` and its tables outside
  `IMPLEMENTATION_GLOBS` on the premise that "no execution path reads it". §6.1
  item 5 and §6.5 make the direct-row licence and run record read it, so after
  §10 that premise is false. Added to the globs:
  - `src/dt_adoc/reporting/veto_expressivity.py`;
  - `config/observation_model_map.tsv`, which defines O;
  - `docs/stage4b/v060_veto_expressivity.tsv` and
    `docs/stage4b/v060_veto_invariance.tsv`.

  This adds no cost per admission: `config/intervention_library.tsv` was already
  globbed, so every admission already changes the digest.
- **A2 — every §3.5.1 floor item has an entity reading.** §10 gave the map four
  gap rows, for the catalog_only targets. The other 15 floor items — the
  external-only `IN_UTERINE_WNT_CUE` and the 14 staged candidates — now have
  `model_gap` rows too, 36 gap rows in all. The loader requires the version's
  model gaps to equal its floor exactly (`check_floor_coverage`), so the floor
  cannot gain an item without a reading. It runs for every version that holds
  a direct row, and in `validate-direct-effects` always; a sandbox with no
  direct row need not carry the staged floor table.

  Consequence: an unrepresented entity that a floor item carries, in a reached
  compartment or an unstated one, must name that floor item. Naming it
  `out_of_scope` is refused. An entity on no floor item stays J2 judgement.
  The match is by entity at **any** level: `FOXO1@expression` names the floor
  item `S_FOXO1`, although its row reads FOXO1 at activity. (A first version
  matched the exact level and let it through; the broad sweep found it.)

  **C3 still matches the exact `entity@level`, as §3.4 states it.** A
  declaration that reads an entity at a level no node carries (e.g. `MUC1` at
  expression, where the map reads it at activity) forces no node and must
  classify it as unrepresented instead. Whether the declared level matches what
  the source measured is J3 reviewer judgement (§3.6). It is not loader-checked,
  and it is the check that keeps C3 from being sidestepped.

  The 15 new readings are J3 judgement, each with its row as basis:
  - single entities: `S_FOXO1` FOXO1, `E_SOX17` SOX17 and `E_ESR1_ACTIVITY`
    ESR1, at activity;
  - pathway members at activity: `S_BMP_SMAD` SMAD1/5/4, `E_ITGA2B1` ITGA2 and
    ITGB1, `E_GLYCOSYLATION_PROGRAM` FUT3 and ST3GAL3, `E_JAG1_NOTCH3` JAG1 and
    NOTCH3, `S_AKT_EXCESS` AKT1/2/3, `S_ERK` MAPK1 and MAPK3;
  - mixed levels: `X_IL11` is IL11 at expression and extracellular;
    `S_WNT4_CTNNB1` is WNT4 at expression and CTNNB1 at activity;
    `S_TGFB_CONTEXT` is TGFB1 at expression and SMAD2/3 at activity;
  - extracellular: `X_ECM_FN1_COL4` FN1, COL4A1 and COL4A2;
    `IN_UTERINE_WNT_CUE` WNT5A and WNT7A;
  - a process: `E_SLEX_SURFACE` is `process:sialyl_lewis_x_surface`.

  The interface items (`X_IL11`, `X_LGALS1_3`, `X_BSG_ITGB1`,
  `IN_UTERINE_WNT_CUE`) carry an empty compartment, which every declaration
  counts as reached.

## 4. Readings the implementation made (not owner decisions)

Recorded so a reviewer can check each against the contract.

**Entity map (J3 judgement, §6.4).**
- Ambiguous: exactly the four nodes the pre-registration names — `E_ITGAVB3_5`,
  `E_ANXA2_ACTIN`, `S_PKA` and `S_BMP2`.
- `E_GP130_STAT3` is `all_of` {LIFR, IL6ST, STAT3} at `activity`. That is what
  makes §3.7's "STAT3 inhibitor → `E_GP130_STAT3`, licensable" expressible.
- `E_CD98_CD9` and `E_CDH1_APICAL` are `any_of`, the conservative reading of
  "X or Y": a veto must hit both members. `E_CDH1_APICAL` was not made
  `ambiguous`, which would have added a fifth ambiguous node the
  pre-registration does not name.
- `derived` rows carry no entity, level or compartment. The model-gap rows for
  `X_BSG_ITGB1` carry an empty compartment, because the catalogue calls it an
  interface state.
- Every reading and its basis is in the map's `basis` column.

**Declaration syntax.**
- `reached_compartments` takes `;`-separated compartments plus optional
  `source:<ref>` items; a narrowed set needs at least one, and each must
  resolve (C4).
- `unrepresented_known_targets` entries are
  `ENTITY@level|class|floor:<id> or none|basis[,basis]`.
- A reference resolves when it is an evidence id in the register, or a file
  path (before any `#`) under the root.
- `library_rows_sha256` is the sha256 of the newline-joined O8b row digests, in
  library order.
- A declaration whose intervention has no rows yet licenses nothing, as an
  approval does. One naming a legacy or migrated intervention is refused.

**"Unrepresented" (C6).** A known `entity@level` is unrepresented when no node
carries it at that level, or when a model-gap row carries it in a reached
compartment. So a bath-applied STAT3 inhibitor must classify stromal STAT3
(`S_STAT3`), and narrowing to the epithelium removes that obligation. This is
§3.5's two-part `scope_relevant` test made mechanical on the reachability half.

**`construction_overlap` (§6.5).**
- It is generated; the declaration column must equal it.
- An edge is on a path when its source is reachable from a target and its
  target reaches O, along the executed rules. Support is the edge's
  `executable_edge` rows in `complete_edges.tsv` plus their evidence ids'
  references.
- For the PC6 example it flags REF-011, as §6.5 says, on seven edges: the four
  §6.5 names (LE011, LE012, LE027, LE033), plus LE069 and LE073 (LIT-PC6-001)
  and LE086 (LIT-BARRIER-001, which also cites REF-011). The example names a
  subset of what the rule finds.

**Claim flags (§6.5).**
- `phenotype_claim_blocked` is set when any named direct effect's target is a
  structural null — the literal and conservative reading of "(a null target)".
- A two-target compound with one null and one non-null target, like the O8
  fixture `synthetic_compound_y`, is therefore flagged, although its compound
  arm is non-null. The record keeps the per-effect classes and the compound
  arm's class, so a report can see both.

**Expressivity currency (§6.1 item 5).**
- Both committed tables are regenerated and compared before any direct row
  licenses.
- The check is cached on the bytes of every file the generator reads, about
  4.6 s the first time.
- A version with no artefact is refused. A version the §5.2 generator refuses
  is refused, with the generator's reason.

## 5. The bounded class-agreement check (§7), registered before it ran

Registered in `tests/integration/test_stage4b_admission_runtime.py`, with its
derivation, before the test was first executed:

- **What runs:** one synthetic direct compound per class: `E_IHH` (null), `E_LIF`
  (A1), `X_SPP1_LUMEN_FREE` (A2), `S_PGR` (A3, stroma only, sourced) and `E_PGR`
  (A4, epithelium only, sourced).
- **How:** each arm against its matched unperturbed run under the reference
  context's condition cfg, from the baseline istates to `max_time = 20`, 2000
  trajectories, seed 1.
- **Tolerance 0.10** on the arm-minus-control difference of each observed
  readout. That is more than six Monte-Carlo standard errors of a difference of
  two proportions at N = 2000, and well below 0.42, the smallest non-zero effect
  on O in that context.
- **What it asserts:** agreement of class — which readouts move, and in which
  direction — never equality of a marginal.

It passed on its first run. The tolerance was not adjusted.
