# What the colours mean, and what they do not

Methods and interpretation note for
`docs/assets/adoc_design_alias_adoc-literature-superset-v0.4.0_A` (Figure A) and
`..._B` (Figure B), and for the tables in `docs/design_alias/`.

Model: `adoc-literature-superset-v0.4.0`. Design: the four-arm plan declared in
`config/planned_design.yaml`. Regenerate with `pixi run render-design-alias`.

---

## 1. The one-sentence version

Figure A colours each node by the group of nodes that **take the same value in
every arm of the current plan**. Two nodes sharing a colour are
*experimentally indistinguishable under this design*. That is a statement about
the experiment, not about the biology, and Section 5 is the list of things it
does not license.

## 2. What is computed, and from what

Nothing here simulates. Every class is an exhaustive enumeration over the
model's free variables, read from `network.bnd` and the condition `.cfg` files.
No trajectory, horizon, transition rate, seed or fitted parameter enters any
colour, so none of this depends on the unresolved endpoint-horizon question in
`docs/endpoint_convergence_finding.md`.

Three partitions of the 59 node labels, nested:

| Partition | Definition | Who caused a merge | What breaks it |
|---|---|---|---|
| `P_label` | one class per named node | — | — |
| `P_global` | one class per distinct Boolean function over all free variables | **the rules** | a model/rule change |
| `P_design` | one class per distinct value-vector across the plan's arms | **the design** | another experimental arm |

For v0.4.0 under the four-arm plan: **59 labels → 35 Boolean functions → 19
design-distinguishable states.** 24 states are lost to how the rules are
written and a further 16 to how the arms bundle their inputs.

Keeping the two collapses apart is the point. A measurement proposed to break a
`P_global` merge is asking for a model repair; one proposed to break a
`P_design` merge is asking for a protocol change. They do not cost the same.

## 3. The encodings

**Fill colour = design-equivalence class (`P_design`).** Same colour, same
behaviour under this plan. Only classes with more than one member get a hue;
singletons are neutral grey, because "this design already separates it" is the
absence of a finding. Hues are Okabe–Ito, assigned in fixed order to classes
sorted by descending size, so a class keeps its colour across re-runs.
Okabe–Ito is the standard colour-vision-deficiency-safe scientific sequence and
is used here unmodified, so the accessibility claim rests on the palette's
published provenance — checkable against `CLASS_HUES` in
`src/dt_adoc/reporting/design_alias_figure.py` — and **not** on any computation
this repository performs. An earlier revision of this paragraph quoted specific
colour-difference figures (worst adjacent pair ΔE 15.8 under deuteranopia, 16.4
at normal vision, against a ΔE 8 floor). Those named neither the difference
metric nor the deficiency simulation, and nothing in `src/`, `tests/` or
`scripts/` computes them, so a palette edit would have left them stated and
stale. They are withdrawn rather than reconstructed: choosing a formula until it
reproduced 15.8 would manufacture the provenance instead of supplying it.
Quoting numbers again means committing the computation first.

**Border = who caused the merge.** A heavy dark border means the node shares a
Boolean function with another node: `P_global` merged it, and *no arm separates
it*. A thin border means the merge is design-induced and a further arm can break
it. This is the structural-versus-design distinction, carried on the same node
as the fill.

**Badge letter = which Boolean function.** Lets a reader see which sub-groups
inside one fill colour are locked together by the rules. The companion panel,
"each class opened into its Boolean functions", is the same information as bar
segments: a bar of one segment is a class no arm will ever split.

**Hatched, violet, dashed = latent.** Five free variables are assigned by no arm,
so their per-unit value is unknown in every condition. Four are the
`X_*_RELAY` interface placeholders — selected not by their name but by the node
dictionary declaring "bounded stochastic initialization" as their only
measurement proxy, i.e. the model saying in its own words that they have no
assay target. `E_KLF12_HIGH` is latent but assayable and is marked differently.
**Latent is neither resolved nor aliased.** Drawing a relay as a neutral
singleton would be the most misleading thing this figure could do.

Note that `X_` is a naming convention, not a category: five `X_`-prefixed nodes
(`X_MECHANICAL_PERMISSIVE_ECM`, `X_SPP1_LUMEN_FREE`, and the three interface
routes) are ordinary derived nodes and are not hatched.

**Black dashed ring = the repository records an observation for this node**
(`E_PAEP`, `S_IGFBP1`, `OUT_STABLE_ADHESION`), read from `config/calibration.yaml`
and `config/observation_model_map.tsv`.

## 4. The current equivalence classes

Seven classes have more than one member; twelve nodes are singletons. Every one
of the seven is a **design-induced union of several Boolean functions**, so
every one is in principle breakable by a further arm — there is no class here
that is purely structural.

| Size | Composition | Reading |
|---|---|---|
| **22** | 5 functions: an epithelial 9 (incl. **PAEP**), a stromal 6 (incl. **IGFBP-1**), a PGR/NR2F2/BMP2 5, plus `S_HAND2` and `X_MECHANICAL_PERMISSIVE_ECM` | the headline class; spans epithelium, stroma and interface |
| 5 | 2 functions: LIF/GP130/CD98 and receptive-surface/`OUT_EPITHELIAL_RECEPTIVE` | epithelial receptivity axis |
| 5 | 4 functions: `IN_E2`, `IN_PROGESTIN`, `IN_XAV939`, and `IN_cAMP`≡`S_PKA` | the hormone cocktail, moved as one |
| 5 | 5 functions: the five inputs the plan never turns on | never excited, so indistinguishable from each other |
| 4 | 3 functions: `E_CDH1_APICAL`≡`IN_EMBRYO_CONTACT`, plus embryo-present and TE-competent | the embryo challenge, moved as one |
| 4 | 2 functions: PODXL/MUC1-barrier/DAG1-full, plus `S_FGF_MITOGENIC` | anti-adhesive barrier |
| 2 | 2 functions: `E_ESTROGENIC_PROLIFERATION` and `IN_MIFEPRISTONE` | — |

The 22-member class is the important one. Two of the three quantities the
repository actually measures — **PAEP and IGFBP-1** — sit inside it. Under this
plan **no contrast between PAEP and IGFBP-1 is informative**: the model predicts
they move identically in all four arms, so a measured divergence between them
would falsify the aliasing rather than be explained by it.

Note that the 22-member class is *not* one Boolean function. It is five, which
the plan's arms happen to move in lockstep. That is why it is breakable at all.

## 5. What the colours do **not** mean

Same colour does **not** mean:

- **the same biology.** Not the same molecule, pathway, cell type, compartment
  or mechanism. The 22-member class spans luminal epithelium, decidualising
  stroma and the ECM/interface.
- **that the nodes are interchangeable, or that one can substitute for another**
  in a model, an assay or an interpretation.
- **that the distinction does not matter.** It may matter a great deal; this
  design simply cannot see it.
- **that measuring both is wasted.** It is precisely the way to *falsify* the
  aliasing. A measured divergence inside a class is evidence against the model's
  rules, and is one of the few genuinely informative negative results available
  here.
- **that the model has been validated.** No colour here reflects agreement with
  data. This is a structural property of rules and protocols.

Neutral grey does **not** mean "unimportant" — it means this plan separates the
node from every other node. Hatched violet does **not** mean "aliased" — it means
unknown in every arm.

And the figure is not spatial: compartments are a schematic, not anatomy, and
node positions carry no cellular location.

## 6. Figure B: which couplings a fifth arm could break

112 candidate arms, constructed mechanically from the plan's own structure so
the ranking cannot favour a preferred answer — every input the plan never moves,
turned on against each of the plan's backgrounds; and every input the plan moves
only inside a bundle, both alone and as the bundle minus that input. Each is
scored by how many design classes the plan plus that arm can separate.

Two currencies are reported separately, and they disagree:

**By raw class gain, HAND2 loss wins: +5 (19 → 24).** Four arms tie, all of them
HAND2 loss on some background; two correspond to committed condition cfgs
(`hormone_treated_hand2_loss`, `adhesion_challenge_hormone_treated_hand2_loss`).
It splits five classes — more than any other candidate — and it is the only one
that pulls `IN_HAND2_LOSS` itself out of the never-excited input class.

It is **not** the only candidate that resolves `S_HAND2` or `S_FGF_MITOGENIC`:
the cocktail-de-bundling arms (`dropout_IN_E2`, `solo_IN_PROGESTIN`, and for
`S_HAND2` also `dropout_IN_cAMP`) resolve both as well, and
`docs/design_alias/candidate_fifth_arms.tsv` is the checkable record of which
arm resolves what.

**By separation of the measured analytes, HAND2 loss scores nothing.** Only 8 of
112 candidates pull two measured nodes into different classes, and none of them
is a HAND2-loss arm:

| Candidate | Gain | Separates | Committed cfg? |
|---|---|---|---|
| hormone-treated **minus E2** | +3 | PAEP from IGFBP-1 | **no** |
| hormone-treated **minus cAMP** | +2 | PAEP from IGFBP-1 | **no** |

De-bundling the hormone cocktail is the only way to split the epithelial half of
the 22-member class from the stromal half. Neither arm has a committed cfg:
writing one is a model change and was not done here.

Gain is in design-equivalence classes. It is **not** a power calculation, an
effect size, or a probability of detecting anything, and it says nothing about
whether a perturbation is biologically achievable or ethically available.

## 6a. The plan is a baseline, not a selection

`config/planned_design.yaml` is the **as-declared** plan and the baseline the
candidates above are scored against. It is **not** a choice of the prospective
arm, and nothing downstream may read it as one. The file declares
`role: as_declared_plan_baseline_not_a_prospective_selection` and
`design_alias.load_plan` refuses any other value, so a later edit cannot turn it
into a recommendation that inherits this module's readers.

The fourth arm is the one that needs saying out loud. The plan names an
anti-SPP1 condition, so the file records one — and everything computed here
argues against reading that as the answer:

- `hormone_treated_anti_spp1` carries **no recorded observation**, and
  `IN_ANTI_SPP1` comes out `set_alone_no_shared_readout`: the plan moves the
  input on its own and no measured quantity exists whose change could be
  attributed to it. **As declared, the fourth arm perturbs a mechanism the
  design cannot read.**
- By raw class gain the best fifth arm is **HAND2 loss (+5)**, not anti-SPP1.
- By separation of the two measured analytes, only **minus-E2** and
  **minus-cAMP** score at all.

The prospective arm is an *output* of the design analysis, not an input to it:
no molecule is privileged in advance, and the maternal-phase panel is settled
before any embryo-challenge arm is chosen.

## 7. Recorded design versus planned design

The plan is **not** a subset of what has been run, and the difference cuts both
ways:

- The plan **adds** an anti-SPP1 arm. `hormone_treated_anti_spp1.cfg` and
  `adhesion_challenge_hormone_treated_anti_spp1.cfg` exist in the model and
  carry **no recorded observation** — they are in-silico probes. The arm is
  reported as `planned_not_recorded` and must not be counted as data in hand.
  Its input assignment is exactly the committed cfg's, so nothing is
  approximated. Adding it makes `IN_ANTI_SPP1` independently perturbed and pulls
  `X_SPP1_LUMEN_FREE` out of the big class.
  Isolating an input is not the same as being able to read its effect, and the
  plan's two isolated inputs differ on exactly that point. `IN_MIFEPRISTONE` is
  **effect-attributable**: `adhesion_challenge_hormone_treated` and
  `adhesion_challenge_hormone_treated_mifepristone` differ in that input alone
  and both carry a recorded `OUT_STABLE_ADHESION` readout, so a change in
  attachment between them is attributable to mifepristone. `IN_ANTI_SPP1` is
  **isolated but unreadable**: the plan moves it on its own, and neither
  anti-SPP1 cfg carries any recorded observation, so no measured quantity exists
  whose change could be attributed to it. It is reported as
  `set_alone_no_shared_readout`, not as independently perturbed.

  This is the practical form of the flag above. Attaching a readout to the
  anti-SPP1 arm is a separate decision from running it, and the plan as stated
  has not made it: as declared, the fourth arm perturbs a mechanism the design
  cannot yet read.
- The plan **drops** the E2-priming arm (`e2_primed_maternal`), which the
  recorded design has. Losing it re-bundles `IN_E2` into the progestin cocktail
  and merges `IN_MIFEPRISTONE` with `E_ESTROGENIC_PROLIFERATION`.

Net: 19 design classes either way, but **different classes**. Reporting the count
alone would hide the trade.

The plan names four conditions without saying which phase each is run in. The
repository realises every condition in both a maternal conditioning phase and an
embryo challenge, and `config/perturbations.yaml` pairs them explicitly, so the
figures use both phases (8 cfgs). The maternal-phase-only reading is available as
`--variant maternal_phase_only` and gives 17 classes; **both conclusions above
are unchanged under it** (HAND2 loss +5; minus-E2 +3 and among the measured-pair
separators). That run writes its own suffixed artifacts —
`docs/design_alias/*_maternal_phase_only.tsv` and
`design_alias_metadata_maternal_phase_only.json`, all committed — so the numbers
here are checkable without overwriting the as-declared tables, and
`tests/unit/test_design_alias.py` exercises the variant.

## 8. Provenance and reproducibility

`docs/design_alias/design_alias_metadata.json` records the sha256 of
`network.bnd`, `baseline.cfg`, the node dictionary, every condition cfg,
`config/planned_design.yaml`, `config/visualization.yaml`, the implementation
files and each output artifact, plus the git commit and library versions.

Figures are rendered with a pinned SVG hash salt and suppressed creation
timestamps, so re-running produces byte-identical files and the recorded hash
certifies content rather than run time.

The attribution rule is the one `identifiability.perturbation_split` applies to
the recorded design, shared rather than reimplemented: an input counts as
independently perturbed only when two arms differ in it alone *and* share a
measured node. Note that the bundle classification does not depend on that
readout test -- an input is bundled exactly when no single-input contrast exists
at all -- so the de-bundling candidates in Figure B are unaffected by whether the
planned arms are measured.

`tests/unit/test_design_alias.py` holds the checks that matter:

- the enumerator, handed the recorded six arms, reproduces
  `identifiability.load_identifiability(...).design_classes` **exactly** — the
  pin that this module has not grown a second, drifting copy of the model;
- the partition changes when the arm set changes;
- `P_global` refines `P_design`, so fill and border cannot contradict each other;
- placeholders are selected by latency and assayability, never by name prefix;
- colours are a function of the partition, in an order the partition fixes;
- **no model node identifier appears as a literal in either module's code** —
  the direct check that nothing in the picture was decided before the model was
  read;
- every recorded hash still matches the file on disk — the implementation
  digest, the model and condition hashes, and the sha256 of each emitted
  artifact. The recorded commit is checked for being present and well formed
  and is deliberately **not** checked for reachability from `HEAD`:
  `tests/unit/test_concordance.py` removed that same invariant because
  ancestry is a property of whichever checkout is looking rather than of the
  artifact, and a repository gate cannot pass it in a reviewing checkout
  whose `HEAD` is a synthetic commit of the tree. Content carries the
  reconstructability the lineage contract asks for; ancestry does not.
