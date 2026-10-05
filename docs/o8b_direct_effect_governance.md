# O8b/O8c — scientific licensing of direct effects, 2026-10-03

**Status: pre-registered before any execution code changed (`bb597a8`), then
implemented on branch `feat/o8b-direct-effect-governance` from `main` at
`1052ff7` (PR #18, Stage 3 merged); §14 records what was run. This unit adds governance and nothing else. It produces no model
version, protocol, prediction, ranking or screen result. It approves no real
compound. Stage 4b is not started.**

It closes O8b (evidence strength) and O8c (refused target roles), the two open
questions of `docs/o8_markerless_interventions.md` §8 that a production
`direct_supported_effect` row needs settled.

## 1. Starting point, verified on `main`

- `main` is `1052ff74c3d4ac212fa6f90546ecb190f2565685` and the tree is clean.
  No branch, document or test addresses O8b or O8c beyond the open-question
  text of the O8 note.
- `context/evidence-register.tsv` is unchanged since O8 (`e30759c`). Its last
  change is `71505c2`. All 16 `LIT-*` rows and both `SOFIA-CCC-*` rows are
  `candidate`, as O8 recorded.
- The committed library holds no `direct_supported_effect` row. Its v0.6.0 rows
  are three `migrated_legacy_behaviour` interventions and `xav939`
  (`executable_legacy_behaviour`, `no_executable_effect`).
- v0.6.0 `node_dictionary.tsv` uses 27 `model_role` values over 56 nodes. They
  are the v0.5.2 roles less `perturbation_input`, which left with the three
  markers (§7.3 lists them all).
- What the O8 loader checks for a direct row (`engine._license_direct_effects`)
  is mechanical: a legal target, refused roles `phenotype` and
  `structural_uncertainty`, evidence ids that resolve, sources that exist,
  non-empty abstraction and claim boundary. Nothing records that the cited
  evidence supports the executed claim.

## 2. Four questions, four layers

| layer | question | where it lives | who answers |
|---|---|---|---|
| evidence existence | what source exists, and what does it say? | `context/evidence-register.tsv` (`status`: `candidate`, `verified`, …) | curation |
| evidence interpretation | what does that source establish, and about which level of biology? | review records: `context/literature/reviews/*.adjudication.tsv`, `*.primary-verification.tsv`, `config/coupling_adjudication.tsv` | scientific review |
| executable-effect approval | does that evidence justify **this** intervention → **this** target → **this** mode, in **this** model version's abstraction? | **new:** `config/direct_effect_adjudications.tsv` | scientific review, recorded per effect |
| execution | render the approved effect | `config/intervention_library.tsv` + `perturbations/engine.py` | the engine, mechanically |

The register's `status` answers the first question, not the third. A `verified`
register row may support no executable effect at all. A `candidate` row may be
the very evidence that licenses one once its interpretation is adjudicated.
**Register status is therefore not gated, and neither status nor its change can
license a direct effect.** Only an approval row can.

**Approving an executable effect is a modelling decision.** It says that under
the recorded abstraction this model may represent the intervention as a full
`activity_veto` of that node. It is not a claim of:

- clinical efficacy;
- target specificity, beyond the effects listed;
- the dose or exposure at which the effect holds;
- the completeness of the compound's target list.

The library row's `claim_boundary` states those limits for each effect.

## 3. Why a new file

No existing table can carry the approval:

- **`context/evidence-register.tsv`.** One row per source. It has no
  intervention, target, mode or model version, and its `status` is the
  existence question.
- **`context/literature/perturbations.tsv`.** A canonical literature table. It
  has no model version or decision, and DTR023 records that it conflates levels:
  PERT-003 targets the string `E_LIF/E_GP130_STAT3`. Review layers do not edit
  it.
- **`models/.../drug_target_catalog.tsv`.** Generated per version.
  DTR019–DTR021 record that its `target_class` is free text and that its
  `execution_status = executable` is applied to states and products. DTR019
  accepts that it is not an authority.
- **The deep-research `adjudication.tsv` / `primary-verification.tsv`.** Keyed
  by review finding, not by executable effect. They are the right **basis
  records** for an approval, and the new ledger cites them (`basis_record`).
- **`edge_evidence_assertions.tsv`, `edge_citation_adjudications.tsv`,
  `coupling_adjudication.tsv`.** Keyed by edge, citation and node collapse
  respectively.

So the approval gets one dedicated source of truth. It follows the conventions
of the existing `config/*_adjudications.tsv` files: an `*_id`, a decision,
`rationale`, `dated`.

## 4. The ledger: `config/direct_effect_adjudications.tsv`

One row per adjudicated effect. Fifteen columns:

| column | meaning |
|---|---|
| `adjudication_id` | `DEA-NNN`, unique |
| `intervention_id`, `model_version`, `target_node`, `mode` | **the key**. Exactly the library row's. `target_node` is one node id of that model, never a list, class or pattern. `mode` is one of the direct modes (`activity_veto`) |
| `decision` | `approved_for_model_execution`, `candidate` or `rejected` |
| `evidence_ids` | the exact evidence set adjudicated. Must equal the library row's as a set |
| `effect_evidence` | what the cited evidence shows about **this intervention acting on this target** (§4.1) |
| `system_match` | how the system the evidence comes from relates to this node (§4.1) |
| `biological_system` | the species, cells and compartment of that evidence, stated |
| `library_row_sha256` | sha256 of the library row approved (§5) |
| `basis_record` | the review record the decision rests on (`path#anchor`; the file must exist) |
| `rationale` | why the decision follows from the basis |
| `adjudicator`, `dated` | who decided, and when (ISO date) |

At most one row per key. Re-adjudication edits that row, and git keeps the
history. A ledger row with no matching library row licenses nothing and is not
an error. That is how a candidate is recorded before any executable row exists.

### 4.1 Vocabularies

`effect_evidence`:

| value | means | approvable |
|---|---|---|
| `target_activity_reduced` | the intervention, as specified (agent, or genetic manipulation), was shown to abolish or near-completely block the activity the node represents, in the system cited | **yes** |
| `target_activity_partially_reduced` | it reduces that activity partially or gradedly: a knockdown that leaves the target substantially expressed, a potentiator, an attenuation rather than a block | no |
| `target_abundance_reduced` | it reduces the target's abundance or expression, and activity was not shown | no |
| `target_necessity_only` | loss of the target alters a phenotype (genetic necessity); this intervention's action on it was not shown | no |
| `adjacent_level_only` | the evidence is at another level of the same axis: ligand vs receptor vs pathway vs product | no |
| `phenotype_only` | the intervention changes a phenotype; target engagement was not shown | no |
| `inferred_from_class` | by class, name or similarity to another agent | no |
| `synthetic_fixture` | test fixtures only (§4.2) | fixtures only |

`system_match`:

| value | approvable |
|---|---|
| `matches_model_compartment`: human endometrial cells or tissue of the target node's compartment | **yes** |
| `other_human_endometrial_compartment` | no |
| `human_non_endometrial` | no |
| `non_human` | no |
| `synthetic_fixture` | fixtures only |

The split between the first two values is the licensing layer's reading of O4,
which is open: the only executable mode is a **full** veto and engagement is
fixed at 1, so evidence that an intervention *attenuates* a target does not
establish that abolishing it is the right abstraction. It is a statement about
what the model would execute, not a judgement of the experiment.

**Which of the two applies is decided by the source, not by the reviewer's
impression.** The operational rule, in order:

1. If the source **quantifies** residual target activity, expression or protein
   under the intervention, anything the source itself reports as remaining —
   a "~50% knockdown", a partial inhibition, an attenuation — is
   `target_activity_partially_reduced`. There is no numeric cut-off to argue
   about, because the source's own quantification decides it.
2. If the source reports the activity as **abolished, blocked, abrogated or
   lost** by its own measurement, it is `target_activity_reduced`.
3. If the source neither quantifies residual activity nor reports it abolished,
   the activity claim is not established at all, and the row belongs under
   `phenotype_only`, `target_abundance_reduced` or `adjacent_level_only`
   according to what *was* measured.

So an approval must cite a measurement, and the measurement decides the value.
A reviewer who cannot point to one of the three has not met the bar.

*Added 2026-10-03, after the stress test of §11 found that
`target_activity_reduced` as first written would have admitted a 50% knockdown;
recorded with `aih repair --kind SEMANTIC_OR_PROTOCOL`. It narrows the gate and
approves nothing.*

Only one value per column is approvable, which is deliberately conservative.
Admitting species or compartment transfer would be a policy change made in this
file and its test, by an explicit decision. No single approval can admit it.

### 4.2 Definition: approved for production direct execution

A `direct_supported_effect` library row `R` is licensed if and only if all of
the following hold:

1. `R` passes every O8 check (§3 of the O8 note): no marker, mode
   `activity_veto`, a target the primitive can mean, no unrouted marker read,
   evidence that resolves, sources that exist, non-empty abstraction and claim
   boundary;
2. `R`'s target passes the O8c target policy (§7);
3. the ledger holds exactly one row `A` with `R`'s
   `(intervention_id, model_version, target_node, mode)`;
4. `A.decision == approved_for_model_execution`;
5. `set(A.evidence_ids) == set(R.evidence_ids)`;
6. `A.library_row_sha256 == sha256(R)` (§5);
7. `A.effect_evidence == target_activity_reduced` and
   `A.system_match == matches_model_compartment`. Alternatively both are
   `synthetic_fixture`, which also requires every cited evidence row to have
   register `status = synthetic_fixture`. Real evidence cannot carry a synthetic
   approval, and synthetic evidence cannot carry a real one;
8. `A.basis_record` names a file that exists.

Every row of the intervention for that version is checked, and any failure
refuses the whole library, as in O8. A multi-target compound with one
unapproved effect therefore cannot run at all. Neither can its approved effects
on their own.

The ledger is validated as a whole whenever it exists, whether or not a direct
row does. These are refused:

- an unknown decision or vocabulary value;
- a duplicated key;
- a `target_node` that is not exactly one node of that model version (a list,
  pattern or class is an attempt at target inference);
- an approved row whose vocabulary is not approvable;
- **any ledger row for an intervention/version whose library rows have another
  basis.** An adjudication cannot convert a legacy or migrated row into a direct
  one, which keeps the three bases distinct. Stage 3 §7.1 records why this
  matters: relabelling a migrated row as direct would have passed O8's checks.

## 5. Binding

The key binds identity, version, target and mode. `evidence_ids` binds the
evidence set explicitly, so a reviewer can read it. `library_row_sha256` binds
everything else the row says.

The digest is the sha256 of the row's 13 library columns, tab-joined in
`LIBRARY_COLUMNS` order, with each list column normalised to its `;`-joined
parsed form. So any change to the label, class, abstraction, sources, evidence
order or claim boundary invalidates the approval.
`python -m dt_adoc.perturbations.adjudication digests` prints the key and digest
of each direct row, read without licensing it, so drafting an approval never
means computing the digest by hand.

What each required refusal hits:

| change after approval | refused by |
|---|---|
| target A → target B | key (no row for B) |
| `activity_veto` → another mode | key, and the direct-mode check |
| approved for v0.6.0, used on another version | key (`model_version`) |
| row cites a different evidence set | `evidence_ids` and the digest |
| row's abstraction, claim boundary, label or sources edited | digest |
| second target of a compound unapproved | key, for that row |
| approval for an entity not written as a row | licenses nothing; an approval naming a non-node is refused |

No approval is inferred from another compound's, from a class, or from a shared
target.

## 6. Loader enforcement

`engine._license_direct_effects` keeps the O8 checks and their order. Two
changes:

- the hard-coded `DIRECT_REFUSED_ROLES` is replaced by the policy table (§7);
- after the mechanical checks it calls the new
  `perturbations/adjudication.py`, which loads and validates the ledger and
  licenses each direct row against it.

On success each direct effect carries its `adjudication_id` and the sha256 of
its ledger row, in the way a migrated row carries `parent_model_version`.

**Legacy and migrated rows are untouched.** `executable_legacy_behaviour` keeps
the Stage 2 check, and `migrated_legacy_behaviour` keeps the Stage 3 licence.
Neither is read against the ledger. Their only contact with it is that the
ledger may not name them (§4.2).

## 7. O8c — target-role policy

### 7.1 Principle

An `activity_veto` is admissible only on a node that stands for a biological
entity or process that an intervention can act on: a ligand, receptor,
regulator, pathway activity, enzyme, adhesion molecule, or a defined
extracellular pool. A node is refused when vetoing it would amount to setting a
**derived** variable directly. These are:

- a phenotype, readout or marker;
- a composite program or latent state;
- an interface route, which is a logical aggregate;
- a structural relay;
- a product whose level the model derives from an upstream enzyme ("you perturb
  the protease", DTR021);
- an input that belongs to the protocol layer.

The default is refusal. A role absent from the policy is refused.

### 7.2 Mechanism: `config/direct_effect_target_policy.tsv`

Columns: `scope` (`role` or `node`), `key`, `policy` (`eligible` or
`refused`), `basis`, `rationale`.

- A `role` row sets the default for every node with that `model_role`.
- A `node` row may only **refuse** a node whose role is eligible. A node row
  that admits a refused-role node is invalid. This is how a more specific
  adjudication overrides a role name. It never widens one.
- Every row needs a non-empty basis on load. That each basis names an existing
  file is checked statically (`pixi run validate-direct-effects` and the test
  suite), not on load: the basis is a record for a reviewer, and a sandbox root
  that executes need not carry the review records.

### 7.3 Policy

| role | policy | nodes (v0.6.0) | basis |
|---|---|---|---|
| `regulator` | eligible | E_PGR, S_PGR, S_PKA, S_NR2F2, S_HAND2 | receptor, kinase and TF activities: entities an agent acts on |
| `paracrine_bridge` | eligible | E_IHH | a secreted ligand |
| `attachment_gate` | eligible | E_LIF | the LIF ligand (catalog `ligand`; DTR022) |
| `pathway_gate` | eligible | E_GP130_STAT3 | "a pathway state is what an inhibitor acts on" (coupling, E_GP130_STAT3) |
| `protease` | eligible | E_PC6 | an enzyme (DTR011) |
| `adhesion_receptor` | eligible | E_ITGAVB3_5 | a receptor. **Flag:** absorbed in its route (DTR009), so a veto is structurally near-inert |
| `adhesion_support` | eligible, with node refusals | E_HBEGF, E_CD98_CD9, E_ANXA2_ACTIN, E_CDH1_APICAL | molecules and processes |
| `anti_adhesive_surface` | eligible, with node refusals | E_PODXL | a surface protein |
| `ligand_source` | eligible | E_SPP1_EXPR | expression of a ligand (PERT-011 level) |
| `decidual_support` | eligible | S_SPP1 | stromal SPP1 |
| `mechanical_regulator` | eligible | S_TAZ_ECM | DTR013: the mechanical *target* is expressible |
| `extracellular_bridge` | eligible | X_SPP1_LUMEN_FREE | the free-ligand pool (DTR010) |
| `state` | refused | E_SECRETORY_STATE, S_DECIDUALIZED | composite programs; coupling rows call them the intended program abstraction |
| `latent_state` | refused | E_RECEPTIVE_SURFACE, X_MECHANICAL_PERMISSIVE_ECM | composite states (coupling; DTR021) |
| `readout` | refused | E_PAEP, S_PRL, S_IGFBP1 | measured markers; DTR016 "do not drug either marker"; vetoing a readout reads the observation off the intervention |
| `regulator_or_readout` | refused | S_BMP2 | the dictionary itself leaves it ambiguous, and DTR007 separates BMP2 abundance from pathway activity, which one node conflates |
| `interface_route` | refused | X_ADHESION_ROUTE_SPP1, X_ADHESION_ROUTE_REDUNDANT, X_ANTIADHESIVE_ROUTE | logical aggregates of routes |
| `anti_receptive_state` | refused | E_ESTROGENIC_PROLIFERATION | a derived proliferative state (DTR021) |
| `paracrine_inhibitor_of_receptivity` | refused | S_FGF_MITOGENIC | derived as `not S_HAND2` (DTR021) |
| `anti_receptive_context` | refused | E_KLF12_HIGH | a hand-set free variable, genetic-only (DTR021; the KLF12 prior was frozen with nothing activated) |
| `phenotype` | refused | four `OUT_*` | O8 |
| `structural_uncertainty` | refused | four relays | O8 |
| `input`, `assay_gate`, `external_input`, `pathology_input`, `boundary_input`, `perturbation_input` | refused | inputs | protocol or environment layer (O1–O3). Mechanically refused anyway as self-loops |

Node refusals inside eligible roles:

| node | basis |
|---|---|
| E_DAG1_CLEAVED | a cleavage product: "you perturb the protease" (DTR021); LIT-PC6-002 dissociates product from enzyme |
| E_DAG1_FULL | the substrate state, derived as `not E_PC6`; the same product/enzyme argument applies (DTR011) |
| E_MUC1_SLEX | a glycoform reachable only via machinery absent from the model (DTR021, DTR012) |
| E_MUC1_BARRIER | the exact logical complement of E_MUC1_SLEX. LIT-BARRIER-001 warns that abundance and glycoform can reverse the interpretation, so a single veto would mean neither MUC1 knockdown nor deglycosylation |

The audit of every v0.6.0 node under this policy, together with its mechanical
status, is generated into `docs/o8b_direct_effect_governance/v060_target_audit.tsv`.
A test regenerates it and requires the committed copy to match.

**What eligibility does not mean.** It is necessary, not sufficient: every
eligible node still needs an approved adjudication. It says nothing about
whether a veto there is distinguishable from another in this model. Coupling
adjudications record that many eligible nodes are rule-identical to the
secretory program. That is a Stage 4b question about expressivity, not a
licence question.

## 8. Provenance

When a direct row is named, the run record already holds its effects, the
library's sha256 and the evidence register's. It additionally records:

- per direct effect: `model_version`, `adjudication_id`,
  `adjudication_sha256` (the sha256 of its ledger row) and
  `library_row_sha256`;
- `direct_effect_adjudications`: the ledger's path, sha256 and size;
- `direct_effect_target_policy`: the policy file's path, sha256 and size.

Two runs licensed by different approvals therefore differ in their record even
when the executed network is identical. Legacy and migrated records keep their
exact shape. The new top-level fields are `null` when no direct row is named.

## 9. N+1, restated

O8 proved that adding compound N+1 is a data operation on two files. After
O8b it is a data operation on three, each appended to:

```
evidence registration     context/evidence-register.tsv
effect approval           config/direct_effect_adjudications.tsv
executable row(s)         config/intervention_library.tsv
```

No model file and no source file changes. The updated gate requires:

1. Y is unavailable before its data exist;
2. Y's evidence alone leaves Y unavailable;
3. Y's library rows without an approval are refused;
4. Y's approval without library rows licenses nothing: Y stays unavailable and
   X stays bit-identical;
5. after evidence, approval and rows are appended, Y executes;
6. exactly those three files changed, by appending; `models/` and `src/` are
   byte-identical;
7. X is bit-identical before and after.

## 10. Gate G12 and tests

G12 is this unit's gate. It is `tests/unit/test_direct_effect_governance.py`
(static) plus the updated `tests/integration/test_markerless_intervention_runtime.py`.

It must refuse:

- no adjudication;
- candidate;
- rejected;
- wrong target;
- wrong mode;
- wrong model version;
- mismatching evidence ids;
- a changed abstraction, claim boundary or label (digest);
- unresolved evidence;
- a missing source;
- a mechanically illegal target, even with an approval;
- a policy-refused role, even with an approval;
- a node-level policy refusal;
- a partially approved multi-target compound;
- a duplicated key;
- an approval naming a list, pattern or non-node target;
- an approval for a legacy or migrated intervention;
- a non-approvable vocabulary on an approved row;
- synthetic/real mismatch;
- a missing ledger with a direct row present;
- a missing basis record;
- invalid policy rows: unknown policy, or a node row admitting a refused role.

It must also accept a multi-target compound whose effects are each approved.

The O8 gates G10 and N+1, and G7/G8/G9/G11, run unchanged in substance. The
synthetic fixtures gain an `*.adjudication.tsv` each. The committed ledger
holds a header and no row, and a test requires it to hold no synthetic row.

## 11. Literature stress test, not a promotion

The committed records were used to check that the vocabulary can say what the
repository already knows. **No row below is added to the ledger or the
library.** Each is how a reviewer would have to record the effect today.

| hypothetical effect | how it would be recorded | distinction exercised |
|---|---|---|
| anti-LIF antibody → `E_LIF` | `candidate`. LIT-LIF-001 is `non_human` for causal support: "mouse causal support is stronger than direct human perturbation evidence". The human perturbation that does exist in the record (REF-072 Fig. 1D: a LIF antagonist diminished LIF-induced pSTAT3) acts at the **receptor**, so for the ligand node it is `adjacent_level_only`, and it was done in the HES cell line rather than primary EEC | mouse causal ≠ human ADOC causal; receptor blockade ≠ ligand neutralisation |
| STAT3 inhibitor → `E_GP130_STAT3` | the closest to qualifying, and still `candidate` / `phenotype_only`. REF-072 (full text, PDF-043) names the agent and dose — STAT3 inhibitor peptide II, Calbiochem, 20 µM — so identity is not what is missing. Two things are: pSTAT3 was **not** measured under the inhibitor (Fig. 1 blots pSTAT3 under the cytokines and their neutralisers; Fig. 2B reads adhesion under the inhibitor), so target engagement by this agent is inferred rather than shown; and that experiment used the **HES cell line**, not the primary EEC of the other panels | phenotype ≠ engagement; the system actually used, not the paper's best system |
| anti-IL-11 → anything | not expressible. The model has no IL-11 node (DTR003 rejected the staged one), and mapping it onto `E_LIF` or `E_GP130_STAT3` would be inference by similarity | no target inference |
| BMP2 neutralisation → `S_BMP2` | refused by policy (`regulator_or_readout`). DTR007 separates BMP2 abundance from BMP pathway activity | abundance ≠ activity |
| CD98 knockdown → `E_CD98_CD9` | `candidate`: `target_abundance_reduced` + `matches_model_compartment` (LIT-CD98-001, human gain/loss). A knockdown is partial, and the register prefers a "rate modifier" form | abundance ≠ full activity veto |
| PC6 knockdown → `E_PC6` | `candidate`: `target_activity_partially_reduced` + `matches_model_compartment`. This is the case that moved the vocabulary. The measurement is the right kind — REF-011 (full text, PDF-044) reads α-DG-N release, a readout of PC6 proteolytic activity in situ, in human endometrial epithelial cells, so it is activity and not abundance, and it is the modelled compartment. But the model is a **stable ~50% siRNA knockdown** in **HEC-1A**, an endometrial carcinoma line: half the enzyme remains, and a full `activity_veto` is not what was demonstrated. Under `target_activity_reduced` as first written this would have been approvable, which is why §4.1 now separates the partial case | partial knockdown ≠ full veto; the right assay at the wrong depth |
| pan-proprotein-convertase inhibitor → `E_PC6` | `candidate` at best: knockdown evidence is `target_necessity_only` for a pharmacological agent | genetic necessity ≠ pharmacological specificity |
| PC6 → `E_DAG1_CLEAVED` | refused by node policy | derived product ≠ target |
| anti-αvβ3 → `E_ITGAVB3_5` | eligible by role but structurally absorbed (DTR009). Approving it would yield a near-null by construction, which Stage 4b must handle | eligibility ≠ expressivity |
| SPP1 knockdown → "`E_SPP1_EXPR` or `S_SPP1`" (PERT-011) | the string is not one node and is refused as target inference. It must be two explicit rows, each with its own adjudication | no inferred targets |
| anti-SPP1 on v0.6.0 | already `migrated_legacy_behaviour`. A ledger row for it is refused | bases stay distinct |
| TAZ inhibitor → `S_TAZ_ECM` | `candidate`: `non_human` (PERT-012: "mouse genetics with human-data support") | species transfer |
| hedgehog-pathway inhibitor → `E_IHH` | not licensable as written. LIT-IHH-002 is evidence for PR-associated regulation of IHH, not for an agent acting on IHH | regulation ≠ intervention |
| PODXL maintenance (PERT-005) | not expressible: it would need activation, a second mode, out of scope | mode vocabulary |

No existing source qualifies today. The STAT3-inhibitor and PC6-knockdown rows
are the nearest, and the full texts were read here (PDF-043, PDF-044) rather
than left as a pending check: neither clears the bar, and each fails it for a
different and now explicitly recorded reason — engagement not measured, and
engagement only partial. Both remain `candidate`, and no row was added.

What would change each: for `E_GP130_STAT3`, a pSTAT3 (or STAT3-target)
measurement under the named inhibitor in primary human endometrial epithelium,
with its selectivity stated; for `E_PC6`, an intervention that abolishes rather
than halves PC6 activity, or a decision under O4 to represent partial
engagement, which this unit does not take.

## 12. Non-goals

None of the following is in this unit:

- a real direct row or a real approval;
- a bulk import (ChEMBL, DrugBank);
- compound selection, ranking, efficacy or synergy;
- partial engagement, dose or PK;
- a second executable mode;
- a v0.6.0 biology change;
- O1/O2 (XAV939, cAMP);
- dropout_e2;
- reopening O6;
- Stage 4b.

## 13. Residual risks, recorded up front

- **Completeness of a compound's target list is not checked.** The ledger
  approves each listed effect. It cannot know about an omitted off-target effect
  on a model node. Stage 4b must decide how a target list is declared complete.
- **The approval binds the library row, not the target node's definition.**
  Model versions are immutable by convention, and `provenance.toml` hashes them.
  An in-place edit of v0.6.0's rule for a target would not invalidate an approval
  by itself.
- **`system_match` and `effect_evidence` are reviewer judgements.** The loader
  checks that they are recorded and approvable, not that they are true. The
  `basis_record` is what a second reviewer reads.
- **Eligible is not distinguishable.** See §7.3 and the coupling adjudications.
- **`system_match` does not grade the system within a compartment.** A primary
  cell, an immortalised line and a carcinoma line all read
  `matches_model_compartment`. §11 shows this mattering twice, and both times
  the refusal came from `effect_evidence` instead. Splitting the column is a
  change this unit does not make.

## 14. What was run

On the exact tree of each commit, in the pixi environment.

| commit | what |
|---|---|
| `bb597a8` | the pre-registration above, no code |
| `0e36791` | the implementation, the policy, the empty ledger, the audit, G12 |
| `21cb12d` | a first regeneration of the four digest-pinned artifacts, **superseded**: `2cb512e` then changed `adjudication.py`, which is globbed, so the digest it recorded no longer recomputes |
| `2cb512e` | the §11 corrections and the §4.1 vocabulary split, after reading PDF-043 and PDF-044 |
| the next commit | the four digest-pinned artifacts, regenerated against the code of `2b804cb` by one systemd unit running `build-concordance`, `sweep-klf12-conditioning`, `build-endpoint-replicates` and `render-endpoint` **in that order on a verified-clean tree** (`git status --porcelain` empty at launch). All four record `git_commit 2b804cb` and `implementation_digest ba915a6e…`, which is what `implementation_digest()` computes on that tree. Only `git_commit`, `implementation_digest`, the implementation file list and hashes, and the `run_settings_sha256` that chains to them changed; every scientific number, the figure and its source data are byte-identical |

The artifacts record the commit of the tree they were generated from, which is
the parent of the commit that then carries them. That is how the three previous
regenerations on `main` (`95e3011`, `22c2478`, `864ed0b`) record it too.

**Why three of the four record `git_tree_dirty: true`.** The generators run in
sequence against one frozen code state, and the first of them writes tracked
outputs, so the tree is no longer clean when the later ones read it.
`build-concordance` therefore records `false` and the three that follow record
`true`, which is exactly the pattern of all three previous regenerations on
`main`. The flag describes the *working tree* at run time, not the code: the
digest covers only the globbed `src/` and `config/` files, which no generator
writes, so all four record the same `implementation_digest` and the same commit.
A run started on a dirty tree, or two generators run in parallel, would break
that correspondence — and did once here: an earlier attempt ran
`build-endpoint-replicates` and `build-concordance` concurrently and edited this
document while they ran, so concordance alone recorded a different digest and
`git_tree_dirty: true`. Those partial artifacts were discarded with `git
checkout` rather than patched, and the sequence above was re-run from the
committed tree. The two-line diff per artifact is the expected signature of a
correct regeneration here, not a hand-edited stamp: it is what "no scientific
number changed" looks like.

Gates and checks, with their results in the unit's final report: the full suite;
the O8/G10 markerless tests and the N+1 gate; G7/G8/G9/G11; `replay-closed-phases`;
`validate-models`; `harness-check`; and `validate-direct-effects`, the new
consistency validator, which loads every licence, validates both new tables and
requires the committed audit to be current.

The mechanical checks were probed by disabling each licence check in turn and
confirming that its tests fail: the digest binding, the decision, the evidence
set, the basis separation, the node-level policy refusal, the approvable
vocabulary and the synthetic/real split each turned their own tests red and
nothing else.

Independent review: see the unit's report. A stand-in reviewer of the same model
family as the author is recorded as degraded and is not independent review.
