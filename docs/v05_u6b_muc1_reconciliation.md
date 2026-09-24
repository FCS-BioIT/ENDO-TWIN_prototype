# U6b — `E_MUC1_BARRIER` reconciliation: the rule family, evaluated and not adopted

**Status: COMPLETE, evaluation only (2026-09-24, `feat/v05-u6b-muc1-reconciliation`).**
Discharges register row `TI-02`. **`TI-06` (the executable correction) stays
`DEFERRED` and its unblock conditions have not changed.** Condition (1), "U6b has
landed", is met by this unit. Conditions (2), evidence that *selects* a clearance
determinant by perturbation, and (3), owner adoption of the exact names and rules,
are both open.

**No `network.bnd` was edited, no model version was created, and no file under
`models/` changed.** Every member below is an in-memory edit of
`adoc-literature-superset-v0.5.1`. It is measured by the repository's own
unmodified loaders (`structure.load_structure`,
`identifiability.load_identifiability` / `compute_gain`,
`design_alias.load_design_alias`), which run on a temporary copy of `models/` and
`config/`. That is the pattern `tests/unit/test_v05_u4_gp130.py` uses for unadopted
variants.

**The result.** The committed rule is contradicted by primary human evidence, and
the family has measured consequences, listed below. **No canonical executable rule
is licensed.** The mechanism of local clearance is undetermined, and no member's
clearance determinant rests on more than spatial association. That result is the
successful outcome this unit is allowed to reach.

| Artifact | What it holds |
|---|---|
| `docs/u6b_muc1_reconciliation/rule_variants.tsv` | **the U6b rule-variant catalog** (§3), in the exact model `rule_variants.tsv` schema: one row per member and MUC1-locus node, `status` `reference_only` / `catalog_only` only, `default_in_family` false everywhere. The only file that tabulates the member rules |
| `docs/u6b_muc1_reconciliation/family_members.tsv` | one row per member: licensing, rule elements, structural and design metrics and deltas against v0.5.1; joins the catalog on `source_row_id` |
| `docs/u6b_muc1_reconciliation/rule_elements.tsv` | every edge or rule component any member writes, with its evidence status |
| `docs/u6b_muc1_reconciliation/endpoints.tsv` | fixed-point value of the barrier, the anti-adhesive route and every adhesion output, per member and per committed condition |
| `docs/u6b_muc1_reconciliation/u6b_summary.json` | everything above plus alias moves, information statuses, pairwise contrasts, input and generator digests |
| `src/dt_adoc/reporting/u6b_muc1_family.py` | the generator (`pixi run build-u6b-muc1-family`) |
| `tests/unit/test_v05_u6b_muc1_reconciliation.py` | byte-for-byte regeneration and the guards cited below |

## 1. The contradiction, from the source

The committed rule is `E_MUC1_BARRIER = not E_SECRETORY_STATE` (edge `LE013`, *"Nonpermissive MUC1 falls in receptive
epithelium"*). It says the progestin-driven secretory state switches MUC1 off.
`PIF-008` (Meseguer 2001, REF-085) is human *in vivo* work on a hormone-replacement
cycle with blastocysts, read in full. It reports:

- a **twofold MUC1 mRNA increase** in receptive (Day 21) versus non-receptive
  (Day 13) endometrium (p<0.05);
- **apposition to a developing blastocyst raising epithelial MUC1 further**;
- **removal that is strictly local** to the attached embryo, with cytokeratin
  confirming the epithelium is intact.

The committed rule has the sign of the progestin dependence backwards. It also
carries three things the source measures separately in one Boolean node:
abundance, glycoform and local clearance (`GAP-004`, `GAP-011`).

## 2. The committed graph, derived rather than quoted

`E_MUC1_BARRIER` has exactly **two readers** in v0.5.1: `E_RECEPTIVE_SURFACE` and
`X_ANTIADHESIVE_ROUTE` (`u6b_summary.json` → `readers_of_barrier_in_model`; asserted
by the test). Today the barrier computes the **same Boolean function as `E_PODXL`
and `E_DAG1_FULL`** (alias class of three), so it is absorbed in both readers:

- `E_RECEPTIVE_SURFACE` already requires `not E_PODXL`, which implies the
  secretory state, so its `and not E_MUC1_BARRIER` conjunct never binds.
- `X_ANTIADHESIVE_ROUTE` already contains `E_PODXL` as a disjunct.

The owner's placement decision is to remove that conjunct (edge `LE028`) and keep
the barrier only in `X_ANTIADHESIVE_ROUTE` (edge `LE074`). **On the committed rule
that removal is a Boolean identity.** The placement-only control `P0` changes no
node's composed function in any assignment, and no fixed point in any condition.
Everything that moves below is therefore caused by the rule change, not by the
placement.

## 3. The family — pre-registered in code, not adopted

The members are fixed in `MEMBERS` in the generator, so any later edit shows up in
the diff. All of them except `V0`, `P0` and `N1` use the interface placement.
Every member with a clearance term uses `E_MUC1_BARRIER = E_MUC1_ABUNDANCE and not
E_MUC1_LOCAL_CLEARANCE`. **The names are proposals, not adoptions**: abundance,
local clearance and the barrier presented at the interface are kept as three
distinguishable things, as the plan requires.

| id | clearance determinant | abundance driver | why it is here |
|---|---|---|---|
| `V0` | — (committed rule) | — | reference |
| `P0` | — (committed rule, conjunct removed) | — | control: separates placement from rule |
| `N1` | none; `E_MUC1_BARRIER = E_SECRETORY_STATE`, both readers kept | — | naive flip, measured before refusal |
| `N2` | none; same flip, interface placement | — | naive flip, measured before refusal |
| `A-SEC` / `A-PGR` | `IN_EMBRYO_CONTACT` | `E_SECRETORY_STATE` / `E_PGR` | contact-driven |
| `B-SEC` / `B-PGR` | `IN_EMBRYO_CONTACT and IN_TROPHECTODERM_COMPETENT` | as above | contact plus competence, **unlicensed stress test** |
| `C-SEC` / `C-PGR` | free placeholder, no prior | as above | clearance unresolved |

**Why two abundance drivers.** `PIF-008` compares estrogen alone with estrogen
followed by progesterone and runs **no progesterone-alone arm**. It therefore cannot
choose between `E_SECRETORY_STATE` (`IN_E2 and E_PGR`) and `E_PGR`. Picking one
would be a silent choice, so both are carried (`RE-02`, `RE-03`).

**Where the family is catalogued.** §17 says an unlicensed family "goes to
`rule_variants.tsv`". v0.5.1's own `rule_variants.tsv` belongs to an audited model
and may not change, and U6b creates no version. For this evaluation-only unit the
clause is therefore met by **the committed U6b catalog,
`docs/u6b_muc1_reconciliation/rule_variants.tsv`**, by owner decision on
2026-09-24. It uses the model file's exact schema, and a test asserts that the two
headers are equal.

Each row is one member and one node of the MUC1 locus. How rows are marked:
- `status` takes only the schema's non-executable values: `reference_only` for
  `V0`/`P0`, `catalog_only` otherwise.
- `default_in_family` is `false` on every row.
- `notes` opens with "EVALUATION ONLY" and gives the member's licensing class:
  refused, unlicensed, stress test, or no determinant asserted.

The runtime reads only model-local catalogs, so this file cannot become
executable. It is the **only** place the member rules are tabulated:
`family_members.tsv` carries metrics and licensing and joins on `source_row_id`,
so the family is not represented twice. If `TI-06` creates a new model version,
the relevant rows can be transcribed unchanged into that version's model-local
`rule_variants.tsv`.

**Not represented, stated so it is not mistaken for an omission.** Apposition
raising MUC1 *further* is a graded increase in a state that is already ON, and a
Boolean node cannot express it. MUC16, which `PIF-009` catalogues as the possibly
cleaner anti-adhesive candidate, is **not** admitted. `E_MUC1_SLEX` is not
reopened.

## 4. Licensing: the evidence status of every element

The two axes are separate and must stay separate. §5 of this record *measures*.
This section says what the evidence *licenses*, and in this family it licenses
almost nothing. Full wording is in `rule_elements.tsv`.

| element | rule | status |
|---|---|---|
| `RE-01` | conjunct removed from `E_RECEPTIVE_SURFACE`; barrier acts via `X_ANTIADHESIVE_ROUTE` | `OWNER_DECISION_PLACEMENT` |
| `RE-02` | `E_MUC1_ABUNDANCE = E_SECRETORY_STATE` | `SUPPORTED_DIRECTION_ONLY`: sign from `PIF-008`; binarising a twofold change is not stated by the source |
| `RE-03` | `E_MUC1_ABUNDANCE = E_PGR` | `NOT_DISTINGUISHED_BY_SOURCE` |
| `RE-04` | `E_MUC1_BARRIER = abundance and not clearance` | `SUPPORTED_AS_SEPARATION_CONSEQUENCE_WEAKENED`: the split is what `GAP-004` prescribes, but `PIF-009` finds **no statistical difference** in trophoblast adhesion on MUC1 knockdown at matched efficiency (cell line on cell line, 1 h). That is a non-significant result, not a demonstrated absence of effect, and not grounds to remove the edge either |
| `RE-05` | clearance = `IN_EMBRYO_CONTACT` | `UNLICENSED_SPATIAL_ASSOCIATION`: n = 3 sites, descriptive, no perturbation, mechanism undetermined, apoptosis not excluded |
| `RE-06` | clearance = contact ∧ competence | `UNLICENSED_STRESS_TEST`: arrested embryos were tested only at apposition, where their effect was intermediate, and never at attachment |
| `RE-07` | clearance = free placeholder | `REPRESENTS_IGNORANCE`: asserts no determinant; adds a latent variable with no prior |
| `RE-08` | naive flip, no clearance term | `REFUSED_BY_SOURCE`: the `PIF-008` row reads "DOES NOT LICENSE A SIGN FLIP" |

`PIF-009` has not been used to supply a human-endometrial clearance mechanism. It
contributes one thing only: it weakens the premise that the MUC1 barrier is
anti-adhesive at all.

## 5. Measured consequences

The structural numbers are exhaustive over every assignment of the free variables.
The endpoints are exact fixed-point values weighted by `baseline.cfg`'s own latent
priors. `docs/endpoint_convergence_finding.md` shows converged MaBoSS reproduces
these values (0.82 in the hormone-treated challenge). **No simulation, horizon,
rate or transient enters.** The Δ is measured against v0.5.1, which U5b proved
function-identical to the 35-function baseline U5 established.

### 5.1 Structure

| member | licensing | nodes | free | distinct (Δ) | barrier alias | inert | changed nodes | design states rec / plan / maternal |
|---|---|---|---|---|---|---|---|---|
| `V0` | CONTRADICTED_BY_PIF-008 | 59 | 19 | 35 (+0) | UNCHANGED_ALIAS | 16 | 0 | 19 / 19 / 17 |
| `P0` | CONTROL_NOT_A_CANDIDATE | 59 | 19 | 35 (+0) | UNCHANGED_ALIAS | 16 | 0 | 19 / 19 / 17 |
| `N1` | REFUSED | 59 | 19 | 30 (-5) | MOVED_TO_ANOTHER_ALIAS | 46 | 8 | 14 / 14 / 13 |
| `N2` | REFUSED | 59 | 19 | 34 (-1) | MOVED_TO_ANOTHER_ALIAS | 15 | 4 | 18 / 18 / 16 |
| `A-SEC` | UNLICENSED | 61 | 19 | 36 (+1) | SEPARATED_TO_SINGLETON | 15 | 3 | 20 / 20 / 16 |
| `A-PGR` | UNLICENSED | 61 | 19 | 36 (+1) | SEPARATED_TO_SINGLETON | 15 | 3 | 20 / 20 / 16 |
| `B-SEC` | UNLICENSED_STRESS_TEST | 61 | 19 | 37 (+2) | SEPARATED_TO_SINGLETON | 15 | 3 | 20 / 20 / 16 |
| `B-PGR` | UNLICENSED_STRESS_TEST | 61 | 19 | 37 (+2) | SEPARATED_TO_SINGLETON | 15 | 3 | 20 / 20 / 16 |
| `C-SEC` | NO_DETERMINANT_ASSERTED | 61 | 20 | 37 (+2) | SEPARATED_TO_SINGLETON | 15 | 4 | 21 / 21 / 19 |
| `C-PGR` | NO_DETERMINANT_ASSERTED | 61 | 20 | 37 (+2) | SEPARATED_TO_SINGLETON | 15 | 4 | 21 / 21 / 19 |

"Changed nodes" counts committed nodes whose **composed** function differs from
v0.5.1 over the union of both members' free variables; `family_members.tsv` lists
them. The design-state columns are **matched-unit conditional**: they assume one
biological unit carries one latent draw through every arm and assay, which ADOC
does not provide (`config/adoc_chip_donor_provenance.tsv`). They describe what a
design of this shape could identify, not what the current data identify.
The two added nodes are given temporary node-dictionary rows in the evaluation
copy (`ADDED_NODE_METADATA`, serialised in `u6b_summary.json`). Their measurement
proxies are `PIF-008`'s own measurements: MUC1 abundance, and local apical loss by
confocal localisation. Without those rows, the loaders' empty-proxy default would
have classed the unresolved clearance state as an interface placeholder. No model
dictionary was changed.

**Does a member separate an alias, or only move one?** It does both, and the cost
is reported next to the gain rather than netted against it.

- **Separates.** Every split member takes `E_MUC1_BARRIER` out of the
  `{E_DAG1_FULL, E_MUC1_BARRIER, E_PODXL}` class and makes it a singleton, so the
  barrier stops being a relabelled podocalyxin.
- **Enlarges.** The abundance node is a pass-through, so it joins the class it
  passes through: `E_SECRETORY_STATE`'s class grows from nine to ten under `-SEC`,
  and `E_PGR`'s class grows from five to six under `-PGR`. In the declared plan it
  sits in the 23-member design class and is `design_aliased_to_measured`. It adds
  no identifiable state.
- Under `A`, the clearance node is a pass-through of `IN_EMBRYO_CONTACT`, so the
  contact class grows from two to three.
- **The naive flips only move the alias.** `N1` and `N2` put the barrier into the
  `E_SECRETORY_STATE` class, which is the collapse `GAP-004` forbids.

**Where the structural gain comes from, stated because it is the recurring
pattern.** Among the split members the count rises `A` < `B` = `C`. `C` asserts
no determinant and is included only for comparison. Each extra function is bought
by exactly the element the evidence supports least:
- in `B`, by the unlicensed competence conjunct, because contact ∧ competence is a
  new function where contact alone is an alias;
- in `C`, by a free variable inserted as a determinant, which is the admission route
  `TI-05` and §5 forbid.

The largest number on the table again points away from the evidence.

**Phenotype-inert change: a dead placeholder comes alive.** Every
interface-placed member except `P0` makes `X_INTERFACE_ANTIADHESIVE_RELAY`
**non-inert**. Its prior in `baseline.cfg` is a hand-set 0.20, with no evidence row
behind it. In v0.5.1 that number never touches a phenotype; under every candidate
it does. **Whatever an executable correction writes, it will make an
interface placeholder's typed-in probability load-bearing.** TI-06 must answer for
that.

### 5.2 The naive sign flip — measured, then refused

- **`N1` (flip in place) makes six nodes unsatisfiable**: `E_RECEPTIVE_SURFACE`,
  `OUT_EPITHELIAL_RECEPTIVE`, both adhesion routes,
  `OUT_MATERNAL_ADHESION_COMPETENCE` and `OUT_STABLE_ADHESION`. The receptive
  surface would then need the secretory state and its negation at once. The
  distinct-function count falls by five, 46 nodes are phenotype-inert (30 more
  than in v0.5.1), and the
  one measured adhesion endpoint is zero in every condition. The plan expected
  "unsatisfiable epithelial phenotype nodes", and that is what happens, exactly and
  only for the in-place form.
- **`N2` (flip plus interface placement) is not unsatisfiable, and that is why it
  needs its own refusal.** Because `E_PODXL or E_SECRETORY_STATE` is a tautology,
  the anti-adhesive route becomes **identical to its own placeholder relay**.
  `X_ANTIADHESIVE_ROUTE` and `X_INTERFACE_ANTIADHESIVE_RELAY` form a new alias
  class. The measured endpoint in the hormone-treated challenge falls from 0.82 to
  0.656 = 0.82 × (1 − 0.20), exactly the typed-in relay prior. Biologically, `N2`
  asserts that the barrier is present at the attachment site whenever the
  epithelium is secretory, which is precisely what `PIF-008`'s local absence at
  attachment contradicts.
- **Refusal, now on measured grounds.** `N1` destroys the epithelial phenotype.
  `N2` removes the barrier's biological content, turns the route into a
  relabelled placeholder, and contradicts the one observation it was meant to
  honour. Neither is a partial repair.

### 5.3 Endpoints, and whether the barrier can bind at adhesion

Exact values from `endpoints.tsv` (fixed point, `baseline.cfg` priors):

| member | HT maternal: `OUT_MATERNAL_ADHESION_COMPETENCE` | HT challenge: `OUT_STABLE_ADHESION` | `embryo_incompetent`: competence |
|---|---|---|---|
| `V0`, `P0` | 0.820 | 0.820 | 0.820 |
| `N1` | 0 | 0 | 0 |
| `N2` | 0.656 | 0.656 | 0.656 |
| `A-*` | 0.656 | 0.820 | 0.820 |
| `B-*` | 0.656 | 0.820 | 0.656 |
| `C-*`, clearance OFF / ON | 0.656 / 0.820 | 0.656 / 0.820 | 0.656 / 0.820 |

- **Under `A` and `B` the barrier is never ON when adhesion is evaluated.**
  `OUT_STABLE_ADHESION` requires contact (and competence), and both force
  clearance. So `barrier_on_when_stable_adhesion_is_evaluable = false`,
  `OUT_STABLE_ADHESION` is **not** in the blast radius, and its value equals
  v0.5.1's in every committed condition. **For the one measured adhesion endpoint,
  MUC1 is inert under both determinant-bearing members.** This is the result the
  plan asked to have stated rather than discovered later. Clamping the barrier
  would still move the endpoint, because a clamp overrides the rule
  (`clamping_barrier_changes_stable_adhesion`). That is a perturbation prediction,
  not something the unperturbed rule can produce.
- **What `A` and `B` do move is an unmeasured composite.**
  `OUT_MATERNAL_ADHESION_COMPETENCE` reads `X_ANTIADHESIVE_ROUTE`, so it becomes
  **embryo-contact-dependent**: 0.656 rather than 0.820 in the hormone-treated
  conditions without contact (maternal phase, `embryo_absent`), unchanged at 0.820
  in the challenge arm with contact. The owner's placement keeps *receptivity*
  (`E_RECEPTIVE_SURFACE`, `OUT_EPITHELIAL_RECEPTIVE`) definable without contact,
  and those values are unchanged. It does **not** keep this composite
  embryo-independent. Its information status moves from `indirectly_constrained`
  to `latent_unresolved`.
- **`A` versus `B`** differ in exactly one committed condition, `embryo_incompetent`
  (contact without competence), and there on no measured node. The competence
  conjunct is invisible to every readout the repository holds.
- **`C` is the only family whose members move the measured endpoint**, and only at
  clearance OFF, by exactly the relay prior (0.656 vs 0.820). Both factors are
  latent: the barrier becomes `latent_unresolved`, and no arm can separate
  "clearance absent" from "anti-adhesive relay on". The measured endpoint aliases
  the new placeholder with the old one.
- **The abundance drivers** (`-SEC` vs `-PGR`) differ in **no** committed
  condition. They differ only in the evaluated frozen minus-E2 arm
  (`docs/stage3_experiment_selection.md` §12). There they move `E_MUC1_ABUNDANCE`
  and the barrier. They do not move the route, which `E_PODXL` already holds ON
  when E2 is absent, and they move none of the arm's three assays (PAEP, IGFBP-1,
  PRL). The frozen experiment cannot choose between them, and it was not edited.

## 6. What U6b establishes, and what stays unresolved

**Established, by measurement:**
1. The committed rule is contradicted in sign by `PIF-008`, and its placement
   conjunct is absorbed. Moving the barrier to the interface is a Boolean
   identity on the committed rule.
2. Neither naive flip is acceptable, for measured reasons: in place it is
   unsatisfiable; at the interface it turns the route into a typed-in placeholder.
3. Any member that separates abundance from clearance takes the barrier out of its
   podocalyxin alias. It also enlarges the class the abundance node passes through,
   and it makes `X_INTERFACE_ANTIADHESIVE_RELAY`'s hand-set prior load-bearing.
4. With any contact-bearing determinant, MUC1 is **inert for
   `OUT_STABLE_ADHESION`**, and the only moved phenotype is the unmeasured
   `OUT_MATERNAL_ADHESION_COMPETENCE`. With no determinant, the measured endpoint
   moves only through two confounded latent variables.
5. On a measured node, meaning the recorded design's readouts plus the frozen
   arm's three assays, evaluated across every committed condition cfg (the
   declared plan's included) and the frozen arm, nothing separates the two abundance drivers, `A` from `B`, or either
   of them from the committed rule. The **only** measured separation is `C` at
   clearance OFF: it differs from `A`, `B` and v0.5.1 on `OUT_STABLE_ADHESION` in
   the hormone-treated challenge arms (0.656 against 0.820). That difference is
   exactly the hand-set relay prior, and its cause is a latent placeholder the
   design cannot set. At clearance ON, `C` cannot be told from `A`. So the one
   difference a measurement could show would not identify a clearance
   determinant.

**Unresolved, and not resolvable here:**
- **What causes local clearance.** No registered source supplies a determinant
  established by perturbation. This is `TI-06` condition (2).
- **Whether the MUC1 barrier is anti-adhesive in human endometrium at all**
  (`PIF-009`'s null).
- **The abundance driver** (`RE-02` vs `RE-03`).
- **Which variants enter a model-local `rule_variants.tsv`.** That happens only
  when `TI-06` creates a version; until then the catalog is
  `docs/u6b_muc1_reconciliation/rule_variants.tsv` (§3).

## 7. Invariants held, and how they are checked

- No `network.bnd` edited: the test asserts v0.5.1 still carries
  `E_MUC1_BARRIER = not E_SECRETORY_STATE` and the `and not E_MUC1_BARRIER`
  conjunct. Separately, `test_deferred_topology_register` asserts that every
  audited version still carries the unrepaired rules.
- No v0.5.2: the test asserts no superset directory beyond v0.5.1 exists.
- TI-06 unblock conditions are byte-identical to their pre-U6b text (digest-pinned
  in the test), and its state is `DEFERRED`.
- No structural count for the unadopted split appears in the register or in the
  plan's U6b block (existing guards). Counts appear only here, and every one is
  generated by a committed derivation that regenerates byte-for-byte.
- No MaBoSS run was needed. Every question the plan posed has an exact fixed-point
  or enumeration answer. The one thing this unit does **not** evaluate is the
  finite-horizon transient: under asynchronous updating `E_MUC1_ABUNDANCE` could
  rise before clearance does. That is a question for whichever member TI-06
  adopts, and it cannot change a conclusion that adopts none.
