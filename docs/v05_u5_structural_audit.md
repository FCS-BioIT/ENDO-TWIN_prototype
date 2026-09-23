# U5 — structural audit and identifiability rerun on the v0.5 line

**Status: COMPLETE. Result: identity.** 2026-09-23, branch
`feat/v05-u5-structural-audit`, based on `main` @ `bef8b75` (after PR #8).
No rule, node, edge, threshold, rate, istate, condition or phenotype was changed.

Defined by `docs/v05_mechanistic_integration_plan.md` §17 U5:

- recompute Δ and confirm which alias classes actually broke;
- rerun identifiability and design-alias, **carrying the matched-unit caveat onto
  every number** (§13.12).

Computed by `pixi run u5-structural-audit`
(`src/dt_adoc/reporting/u5_structural_audit.py`) into
[`u5_structural_audit/u5_audit_summary.json`](u5_structural_audit/u5_audit_summary.json)
and the per-node table
[`u5_structural_audit/u5_node_audit.tsv`](u5_structural_audit/u5_node_audit.tsv).
Guards: `tests/unit/test_v05_u5_structural_audit.py`, which regenerates both
files byte-for-byte and re-derives every number quoted below.

## 1. The result

**`adoc-literature-superset-v0.5.0` is executable-byte-identical to
`adoc-literature-superset-v0.4.0`.** Of the 41 files in each model directory, 38
are byte-identical and the 3 that differ are exactly the scaffold metadata U1 was
allowed to change (`provenance.toml`, `README.md`,
`executable_model_manifest.tsv`). `network.bnd`, `baseline.cfg`, the node
dictionary and every `conditions/*.cfg` are identical.

**Δ = 0.** The audited model implements 35 distinct Boolean functions, exactly the
v0.4 baseline. **No alias class broke and none formed.** Every recomputed block —
structural, identifiability, design-alias as declared, design-alias
maternal-phase-only — is identical to the same computation on v0.4 once the
model-version label is removed, and each also matches the committed v0.4
artifacts (`docs/identifiability/identifiability_metadata.json`,
`docs/design_alias/design_alias_metadata*.json`,
`docs/assets/adoc_superset_structure_v0.4.0_metadata.json`).

This is the U5 result, not a gap. U1–U4b changed no mechanism and U4c's evidence
half (PR #8) did not either, so there was nothing for the audit to find. The
audit's value is that it now *proves* this from the v0.5 path, rather than the
plan asserting it, and that the machinery is in place to report a real Δ when a
unit does change the model.

Byte identity and recomputation are recorded separately on purpose. Identity says
the inputs cannot differ. Recomputation says the v0.5 directory is the one
actually read — a resolver that silently fell back to v0.4 would pass the first
and fail the second. To make the design-alias rerun possible,
`design_alias.load_plan`/`load_design_alias` gained an optional
`model_version` override; the declared plan in `config/planned_design.yaml` is
unchanged and still names v0.4.

## 2. Structural facts (design-independent)

A property of `network.bnd` alone, exhaustive over all 2^19 = 524,288 assignments
of the free variables. **These do not need the matched-unit caveat.**

| quantity | v0.5.0 = v0.4.0 |
|---|---:|
| named nodes | 59 |
| dependencies derived from `network.bnd` | 97 |
| free variables (rule is its own name) | 19 |
| distinct Boolean functions | **35** |
| exact alias classes (largest) | 8 (9 members) |
| absorbed dependencies | 15 |
| inhibitions that never bind | 4 |
| absorbed or never-binding, union | 19 |
| phenotype-inert nodes | 14 |
| declared inputs no rule reads | 3 (`IN_XAV939`, `IN_HCG`, `IN_EMBRYO_CONDITIONED_SIGNAL`) |

The eight alias classes are spelled out in the JSON and on the network figure
(`docs/assets/adoc_network_overview_v0.5.0.png`). The two that bound what ADOC
can test: the nine-member epithelial secretory class containing `E_PAEP`
(`AC01`), and the six-member stromal decidual class in which
`S_DECIDUALIZED = S_IGFBP1 = S_PRL = S_SPP1 = S_TAZ_ECM = OUT_STROMAL_DECIDUALIZED`.
`E_PGR = E_IHH = S_PGR = S_NR2F2 = S_BMP2` remains one function.

## 3. Identifiability and design-alias — matched-unit conditional

> **Every number in this section is matched-unit conditional.** It assumes one
> biological unit carries a single latent assignment through every arm and assay.
> ADOC does not provide that: adhesion is an aggregate per-embryo count, the
> secreted-protein mappings are unpaired, chips can share donors and epithelial
> and stromal cells in one chip may come from different donors, and the
> column-to-chip mapping for IGFBP-1 and PRL was lost
> (`config/adoc_chip_donor_provenance.tsv`). These numbers describe what a
> matched-unit design of this shape *could* identify, **not what the current data
> identify.** The caveat is carried as a field on every such block in the JSON and
> as a column in the node table.

| quantity (matched-unit conditional) | v0.5.0 = v0.4.0 |
|---|---:|
| design-effective states, recorded arms (`P_design`) | 19 |
| … with the greedy proposed arms | 34 |
| … ceiling (`P_global`) | 35 |
| latent free variables / assignments | 5 / 32 |
| observation classes reached now | 2 of 32 |
| observation classes reachable with every proposed arm and every assayable readout | **8 of 32** |
| design classes, declared four-arm plan (as declared / maternal phase only) | 19 / 17 |
| candidate fifth arms evaluated (as declared / maternal phase only) | 112 / 56 |
| best fifth-arm gain; arms that also separate two measured nodes | +5 (`IN_HAND2_LOSS`); +3 (`dropout_IN_E2`) |

The 8-of-32 ceiling is the binding one: the interface relays carry four
initial-state coins no assay can read, so no arm reaches more than a quarter of
the latent state. That is unchanged and is a rule-encoding problem, not a design
problem.

## 4. What the measured nodes imply

From `measured_node_implications` in the JSON. The *structural* class is what a
reading stands for under **any** experiment; the *design* class is what it stands
for under the declared plan (matched-unit conditional).

| node | ADOC tier | structural class | design class (declared plan) | information status |
|---|---|---:|---:|---|
| `E_PAEP` | active observation mapping (`OM-001`) | 9 | 22 | directly measured |
| `S_IGFBP1` | active observation mapping (`OM-002`) | 6 | 22 | directly measured |
| `OUT_STABLE_ADHESION` | functional endpoint (embryo counts; ordinal only) | 1 | 1 | directly measured |
| `S_PRL` | assayed, mapping provisional (`OM-006`) | 6 | 22 | design-aliased to measured |
| `OUT_STROMAL_DECIDUALIZED` | reported composite, 0 source rows (`OM-010`) | 6 | 22 | design-aliased to measured |
| `OUT_EPITHELIAL_RECEPTIVE` | reported composite, 0 source rows (`OM-009`) | 2 | 5 | latent unresolved |

Two consequences stand out.

- **Under the declared plan `E_PAEP` and `S_IGFBP1` are one design class.**
  Because every existing arm moves the hormone cocktail as a bundle, the two
  active readouts, from two compartments, carry the same information, so measuring
  both is one bit, not two, until a single-agent arm exists. This is the
  structural reason the frozen Stage-3 choice is a single-agent dropout.
- **`S_PRL` is not an independent readout of anything.** It is the same Boolean
  function as `S_IGFBP1`, so the IGFBP-1-before-PRL onset order ADOC observes
  cannot be represented. That is U2/U4c's standing refusal
  (`docs/prl_igfbp1_temporal_axis.md`, `docs/v05_u2_gate3a_blocked.md`),
  re-confirmed here, not reopened.

## 5. Reconciliation with existing records

| record | status after U5 |
|---|---|
| `docs/design_alias/`, `docs/design_alias_note.md` | Unchanged. Recomputed on v0.5 and identical. The figures and tables are byte-identical; the two metadata JSONs were re-rendered only because `design_alias.py` gained the `model_version` override, and they differ in `git_commit` / `implementation_digest` alone. |
| `docs/identifiability/`, `docs/identifiability_analysis.md` | Unchanged. Recomputed on v0.5 and identical; the committed v0.4 artifacts stand. |
| `docs/stage3_experiment_selection.md` (frozen minus-E2 dropout) | **Stands.** Its computation conditions the v0.4 network, and every executable input it reads is byte-identical in v0.5, so re-running it on v0.5 cannot move it. The mandatory U8 rerank (§14) exists for a v0.5 that *differs*; it has not been run. Its `E_PAEP` prerequisite is **already met**: the owner adopted the three-band ordinal rule on 2026-09-17 (`stage3_experiment_selection.md` §9.1; `experiment_candidate_review_2026-09-22.md` M2). What remains is pointing `OM-001`'s `claim_ceiling` at it. |
| `docs/experiment_candidate_review_2026-09-22.md` | Consistent. Its readout tiers (two usable assays, three mapped composites, 54 no-assay nodes) match the measurement tiers recomputed here from the same observation map. |
| `config/observation_model_map.tsv` | Read, not edited. Its tiers drive the network figure's measurement markers and §4 above. |

**Carried caveats.** The matched-unit / donor-chip caveat applies to every
number in §3 and to the design and information columns of §4, and to every place
experimental evidence is used: ADOC chips are not independent biological
replicates, and embryo counts are per-embryo outcomes, not donor-level ones.

## 6. Residuals encountered and deliberately left

- **`S_AKT_EXCESS`** still reads `5(1)` / `EVIDENCE_UNVERIFIED` although
  `PIF-007` registers Kang 2022 as its unblock source
  (`docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md` §4 item 8). It is
  a catalogue candidate-node disposition, touches no executable file, and enters
  none of U5's computations. **Separate atomic follow-up**; re-adjudicating it
  here would be the "moving by implication" that unit refused.
- **`OM-001`'s `claim_ceiling` versus the frozen §9.1 three-band rule.** It is
  observation-map text; changing it moves no activation status and therefore no
  number in this audit, and §14.2 requires any observation-map change to carry
  its own justification. **Separate atomic follow-up**, which should land before
  U8. The band rule itself is not open: it is adopted in
  `stage3_experiment_selection.md` §9.1 and only the cross-reference is missing.
- **`E_ESTROGENIC_PROLIFERATION`.** §17 records that the owner question "is the
  CNT arm unstimulated or E2-primed-only?" gates any v0.5 claim about this node.
  U5 makes none beyond the structural counts above, which do not depend on the
  answer; the question stays open.
- **The concordance across-seed spread.** While building the endpoint figure it
  was measured that a MaBoSS run is the union of single-trajectory runs on
  consecutive seeds, so the concordance build's seeds 1–5 at 20,000 trajectories
  share 19,996 per-trajectory seeds
  and `simulated_sd_across_seeds` is not a spread across runs that share no trajectory
  (`docs/maboss_estimator_semantics.md`, addendum 2026-09-23). The concordance
  artifacts are hash-pinned by `IMPLEMENTATION_GLOBS` and need a MaBoSS rebuild to
  correct, so this is **not** fixed here; it is a separate follow-up. The
  disjoint-seed-block spreads in `docs/endpoint/` are the ones to cite. On them
  (`docs/endpoint/endpoint_figure_source_data.tsv`, 50 runs × 20,000), the
  declared-horizon mifepristone mean sits **below** the hormone-treated mean,
  not above it as the overlapping-seed concordance record has it, and both arms'
  run-to-run SD is about the size of their value. The concordance conclusion
  that the declared-horizon mifepristone arm has no stable value survives; its
  numbers and the direction it quotes do not, and correcting them is part of that
  follow-up.

## 7. What this means for U6

1. **U6 cannot be motivated by U5 numbers, because there are none to move.** Any
   U6 schema should be judged by whether a *later* unit's audit can report a Δ
   and a broken class through it, not by anything measured here.
2. **Emit the three semantic axes for the six ADOC-touched nodes first.** §4 shows
   that the whole observation layer rests on two design-aliased active readouts
   and one ordinal endpoint. A semantics generator that is correct for those six
   and carries their tiers explicitly is worth more than full coverage of the 54
   no-assay nodes.
3. **Carry `matched_unit_conditional` as a field, not a paragraph.** This audit
   had to add it as a column so the caveat travels with the number. U6's
   component map should do the same for any requirement derived from a design
   class rather than from `P_global`.
4. **Keep the 8-of-32 ceiling visible.** It is set by the four interface relays
   (`logic = self` with typed istates). No node-semantics or component work
   changes it; only a rule repair of the relays does, and Gate 3b remains closed
   on the variability-semantics decision.
