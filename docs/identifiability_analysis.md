# What a matched-unit ADOC design of this shape could identify

How every class in `docs/assets/adoc_identifiability_adoc-literature-superset-v0.4.0.svg`
was computed, and what each one is and is not entitled to claim.

> **This document does not say what the current data identify, and an earlier
> revision did.** Every fibre here is built by applying ONE latent assignment
> across every arm and assay at once, which is a statement about a single
> biological unit carried through the whole design and observed in all of it.
> The current data are not that: adhesion is an aggregate count over embryos
> rather than a per-unit readout, the secretion mappings are explicitly
> unpaired, and the unit mapping is not recoverable from what is recorded. Under
> independent per-arm latent draws a joint observation constrains no single
> shared assignment, so the counts below -- 32 latent assignments, 2 observation
> classes, every information status, the whole proposed panel -- describe a
> HYPOTHETICAL matched-unit design. Read as current-data identifiability they
> would be an overclaim, and that reading is withdrawn. `unit_assumption` in
> `identifiability_metadata.json` records the same thing beside the numbers.
>
> What is unaffected is the structural half, which never depended on pairing:
> the 59 named nodes, the 35 native Boolean functions, and the fact that the
> model represents more mechanism than any of this could separate.

Regenerate everything with:

```bash
pixi run render-identifiability
```

Source: `src/dt_adoc/reporting/identifiability.py` (analysis),
`src/dt_adoc/reporting/identifiability_figure.py` (figure and tables),
`tests/unit/test_identifiability.py` (the claims, pinned).

Nothing here simulates. Every quantity is a property of `network.bnd`, the
condition `.cfg` files, `config/observation_model_map.tsv` and
`config/calibration.yaml`. That is deliberate: the endpoint-horizon decision
(`docs/endpoint_convergence_finding.md`) is unresolved, and a claim about what an
experiment can identify must not depend on it. The single exception is the
adhesion-endpoint decomposition below, which reads two initial probabilities from
`baseline.cfg` in order to show that the headline 0.82 is arithmetic rather than
inference; it is reported separately from every partition count.

## The framing

Not "observability and perturbability" as two lists, but **structural
identifiability of a Boolean model under a finite experimental design**, expressed
as three nested partitions of the 59 node labels.

| Partition | Classes | What merges labels here |
| --- | ---: | --- |
| `P_label` | 59 | nothing; this is how the network is drawn |
| `P_global` | 35 | the v0.4 **rules**: labels realising the identical Boolean function over all 2^19 free-variable assignments |
| `P_design` | 19 | the **arms**: functions the recorded conditions never make differ |

Keeping the two collapses apart is the point. 24 labels merge because the rules
say `E_PAEP := E_SECRETORY_STATE`; no experiment can separate those while the
rules say that, so a measurement proposed to break such a merge is asking for a
**model repair**. A further 16 merge because the hormone cocktail moves three
inputs at once; those an experiment *can* separate, so a proposal there is asking
for a **protocol change**. The two are not interchangeable and do not cost the
same. Reporting only the 59 overstates what the model resolves; reporting only
`P_global` blames the rules for degeneracy the experiment caused; reporting only
`P_design` blames the experiment for degeneracy the rules caused.

On top sits the measurement layer. The free variables split three ways:

- **controlled** — some arm assigns it (13 inputs).
- **held off** — a declared `IN_` intervention no arm assigns. Known to be off,
  because the drug was not added. Not an unknown, but a mechanism never excited.
- **latent** — an internal free variable no arm assigns: `E_KLF12_HIGH` and the
  four interface relays. A property of the biological material, so its per-unit
  value is genuinely unknown. `baseline.cfg` gives these an initial value, but a
  configured assumption is not an observation and is not counted as one.

Five latent variables give 2^5 = 32 internal configurations. Each yields one
observation vector; the **fibres** of that map are the observationally equivalent
states, and a node is **identified** exactly when its value is constant on every
fibre.

## Definitions

**Design arm.** A condition `.cfg` for which the repository records an
observation — `config/calibration.yaml`'s adhesion objective names the protocols
with embryo-attachment counts, and `config/observation_model_map.tsv` names the
nodes with an evaluable activation status and the protocols they are compared
across. An arm earns its place by carrying data, never by having a `.cfg`. The
superset also ships conditions for anti-SPP1, washout, HAND2 loss, ER stress and
high stiffness; none was run, and counting them would credit the design with
excitation it never applied. Six arms qualify.

A condition `.cfg` is an *overlay* on `baseline.cfg` and lists only what the
condition changes — `basal_maternal.cfg` sets nothing at all. The overlay is
therefore applied over the free variables only, with `baseline.cfg` as the
default. Reading a condition alone would misreport every unmentioned input as
unknown; reading `baseline.cfg` wholesale would pin all 59 nodes, derived ones
included, and flatten the network to constant zero.

**Observed** is not one category, because it conflates four different situations.
Each node gets exactly one status, in this precedence order:

| Status | Meaning |
| --- | --- |
| `directly_measured` | an active observation mapping resolves to this node |
| `design_aliased_to_measured` | its value equals a measured node's everywhere the design goes. Inferred — but only as the class; measuring it separately adds nothing under these arms |
| `indirectly_constrained` | depends on a latent variable, is not aliased to a measured node, and its value is still a function of the observation |
| `model_asserted_untested` | the arm alone fixes its value and nothing observes it. The model predicts it; the experiment neither confirms nor refutes it |
| `latent_unresolved` | depends on a latent variable and is not a function of the observation |

A node is never called observed because it lies upstream of adhesion.
`design_aliased_to_measured` says the current design cannot tell it apart from a
measured node — **not** that the biology is the same, and never that the state
does not matter.

**Perturbed** likewise splits, and attribution needs two things rather than one.
An input is `independently_perturbed` when two arms differ in that input *alone*
**and share a measured node**, so a change in that node is attributable to it.
Differing alone is not sufficient: if the two arms read different quantities
there is no common outcome whose change could be attributed, and the contrast
establishes nothing about the input's effect. That case is
`set_alone_no_shared_readout` -- a property of the input assignment, not of what
the experiment can attribute. `bundled_perturbed` is when the smallest set of
inputs that changes with it between two arms has size > 1, naming the bundle the
effect is confounded within; and `never_perturbed` when no arm moves it.

`IN_E2` is the reason the distinction is drawn rather than assumed. Its only
single-input contrast is `basal_maternal`, which reads `S_IGFBP1`, against
`e2_primed_maternal`, which reads `E_PAEP` -- no shared readout, so nothing is
attributable. `IN_MIFEPRISTONE` has a real one: both of its arms read
`OUT_STABLE_ADHESION`. An earlier revision counted the two alike and reported
two independently perturbed inputs, which stated a design property as an
experimental one.

**Assayable.** Taken from the node dictionary's `measurement_proxies`, not
curated here. The four relays declare `bounded stochastic initialization` and the
three interface routes declare `derived route state`: the dictionary is saying, in
its own words, that these are modelling placeholders. They are excluded from every
candidate readout search, and the exclusion is reported rather than silent —
unrestricted, the "optimal" panel is the four relays, which is a correct answer to
the wrong question.

## What the design determines, under the matched-unit assumption

| Quantity | Value |
| --- | ---: |
| Named nodes | 59 |
| Distinct Boolean functions (`P_global`) | 35 |
| States separable by the recorded arms (`P_design`) | 19 |
| Arms carrying a recorded observation | 6 |
| Measured quantities | 3 (`E_PAEP`, `S_IGFBP1`, `OUT_STABLE_ADHESION`) |
| Declared inputs | 14 |
| — independently perturbed (effect-attributable) | 1 (`IN_MIFEPRISTONE`) |
| — set alone, but no shared readout | 1 (`IN_E2`) |
| — perturbed only inside a bundle of three | 6 |
| — never moved | 6 |
| Latent internal variables / configurations | 5 / 32 |
| **Distinct observations over those 32 configurations** | **2** |
| Nodes that cannot change any readout | 14 |
| Declared inputs no rule reads | 3 |

Per-node detail is in `docs/identifiability/node_classification.tsv`.

### The finding that governs the rest

`E_PAEP` and `S_IGFBP1` — the only two active molecular readouts — fall in the
**same 23-member design state**, together with `S_PRL`, `S_SPP1`, `S_TAZ_ECM`,
`E_HBEGF`, `E_ITGAVB3_5`, `E_SPP1_EXPR`, `OUT_STROMAL_DECIDUALIZED` and the rest
of both the epithelial secretory and stromal decidual programs.

The cause is the cocktail. `E_SECRETORY_STATE = IN_E2 and E_PGR` and
`S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2`, and because E2 is on in every arm
where the progestin is on, these are the same function across all six arms.
Epithelium and stroma never move independently, so no measurement taken in this
design can separate them. Two readouts are one bit.

### The adhesion endpoint

In the hormone-treated challenge arm, every conjunct of `OUT_STABLE_ADHESION`
except the two positive interface routes holds for every internal configuration
with `E_KLF12_HIGH` off — which `baseline.cfg` sets deterministically. The
endpoint reduces exactly to

```
OUT_STABLE_ADHESION  ==  X_INTERFACE_SPP1_RELAY  or  X_INTERFACE_REDUNDANT_RELAY
```

verified by enumeration, not asserted, so its converged value is

```
1 - (1 - 0.70)(1 - 0.40)  =  0.82
```

with both numbers initial probabilities typed into `baseline.cfg` for relays whose
declared proxy is "bounded stochastic initialization". This reproduces the
repository's existing finding (`docs/concordance_analysis.md`,
`docs/endpoint_convergence_finding.md`) and adds the condition under which it
holds. Stable adhesion is a real and important phenotype, but its graded value
here is arithmetic on two assumptions and an attachment count cannot say which
route carried it. **Endpoint-only validation cannot identify mechanism**, and
stable adhesion must not be read as evidence that the upstream network was
observed.

## Marginal information gain

Two currencies, reported in separate columns because they are not exchangeable.
A perturbation buys **structural resolution** — how many distinct Boolean
functions the design can tell apart, bounded by `P_global` = 35. A readout buys
**latent resolution** — how finely the observation splits the 32 internal
configurations, bounded by 32. Combining them into one score would let a cheap arm
launder itself as a measurement, and a single "% identifiable" would divide one by
the other and mean nothing.

Candidate arms are generated mechanically rather than curated, so the search
cannot quietly favour a preferred answer: every bundled input gets an "alone" and
a "cocktail minus" arm, and every never-moved input gets an arm turning it on
against a permissive background. The background is the arm leaving the most
derived nodes reachable — not the arm with the most inputs on, which is the
mifepristone challenge, where PGR is blocked and nothing downstream can respond.

A proposed arm is scored with the readouts already taken in arms of its family
(an attachment count needs an embryo; the secreted proteins are sampled in the
maternal phase). Scoring a new arm with no readout in it would rate every
perturbation at zero.

| Frontier | Now | Reachable | Ceiling |
| --- | ---: | ---: | ---: |
| States separable (perturbations) | 19 | 34 | 35 |
| Observation classes (readouts) | 2 | **8** | 32 |

Rankings: `docs/identifiability/candidate_arms.tsv`,
`docs/identifiability/candidate_readouts.tsv`; the selected panel is
`docs/identifiability/proposed_panel.tsv`. The greedy panel is checked against an
exact best-subset search for small panels rather than assumed optimal.

### Two results worth stating plainly

**Most additional assays buy nothing.** Of the 40 assayable states not currently
measured, **34 leave the number of distinguishable observations unchanged** under
the arms as they are run — including `S_PRL`, `S_SPP1`, `S_TAZ_ECM`, `E_HBEGF`,
`E_ITGAVB3_5`, `E_MUC1_SLEX` and `E_SPP1_EXPR`. They report states the design
already covers. Only six help, all on the LIF/GP130-STAT3/KLF12 axis, and each
adds exactly one observation class.

This is a statement about the current arms and the current rules, **not** a
verdict on the biology. A mechanism that aliases under v0.4 may be exactly the
mechanism whose absence makes v0.4 wrong — `OM-016` already records that any model
in which `S_IGFBP1` and `S_PRL` are logically identical is inconsistent with the
observed onset order, and in v0.4 they *are* identical. The structural triage
ranks what the present encoding can exploit; it does not license dropping a
mechanism from the model.

**Measurement alone cannot close the gap.** Adding every assayable readout to
every proposed arm reaches 8 of 32 observation classes. The remaining factor of
four is carried by the four interface relays, whose declared proxy is a stochastic
initialisation — they *are* the unmodelled interface biology. Identifying the
interface is therefore a model repair (replace the relays with mechanism), and
only then a measurement.

## What the scRNA-seq dataset does and does not add

`config/scrna_observation_map.tsv` and `docs/scrna_observability.md` were
written without reference to this analysis, and they reach the same wall from
the measurement side. `tests/unit/test_identifiability.py` pins the agreement so
that a change to either side has to face the other.

**How much independence that agreement has, stated before it is used.** The two
sides are independent about `E_KLF12_HIGH` and not independent about the relays.
The map's per-node curation is real evidence — it names the transcripts, the
aggregation grain and the evidence role — and nothing in it was read off this
document. But the four relays are not curated entries: they fall to
`_default_curation`, which marks every `X_`-prefixed node unobservable by naming
convention. So the relay agreement restates a modelling convention both sides
already share; it is not two measurements of the same thing. It is reported here
because the convention is load-bearing and should be visible, not because it
corroborates anything.

The map classifies all 59 nodes. Twenty-seven have some scRNA observability,
and under unmodified v0.4 rules those 27 occupy only **nine** distinct Boolean
signatures — a representational deficit of the model, not a ceiling on the
assay. Where two separately measurable nodes fall in one v0.4 alias class,
a measured divergence between them *falsifies the aliasing*; it is not a limit
on what the experiment could see.

Line that up against the five latent variables above and the result is sharp:

| Latent variable | scRNA observability | Can it condition an `istate`? |
| --- | --- | --- |
| `E_KLF12_HIGH` | `direct_transcript` | yes — `istate_prior` |
| `X_MECHANICAL_STRESS_RELAY` | `not_observable` | no |
| `X_INTERFACE_SPP1_RELAY` | `not_observable` | no |
| `X_INTERFACE_REDUNDANT_RELAY` | `not_observable` | no |
| `X_INTERFACE_ANTIADHESIVE_RELAY` | `not_observable` | no |

`E_KLF12_HIGH` is the **only** node in the entire 59-row map whose measured
value is directly compatible with an `istate` prior; the other 26 observable
nodes are derived, and conditioning on their measured value would require a
rule or model change, not merely a config edit.

**What conditioning it buys, computed rather than estimated.** Taking
`E_KLF12_HIGH` as externally given refines the design's two observation classes
into **three** — not four, because the 12-member class already resolves it:

| Branch | Latent configurations | Relays resolved |
| --- | ---: | --- |
| `E_KLF12_HIGH` off, no attachment | 4 | `X_INTERFACE_SPP1_RELAY`, `X_INTERFACE_REDUNDANT_RELAY` |
| `E_KLF12_HIGH` on | 16 | none |
| `E_KLF12_HIGH` off, other observation | 12 | none |

The first row is worth reading twice, because it is a real gain and it is not
the gain one would guess. It follows directly from the endpoint decomposition
above: with `E_KLF12_HIGH` off, `OUT_STABLE_ADHESION` reduces exactly to
`X_INTERFACE_SPP1_RELAY or X_INTERFACE_REDUNDANT_RELAY`, so **observing no
attachment in that branch pins both relays off**. An scRNA prior on one node
converts the attachment count into a partial relay probe — in 4 of the 32
internal configurations.

That is where it stops. `X_MECHANICAL_STRESS_RELAY` and
`X_INTERFACE_ANTIADHESIVE_RELAY` are resolved in **no** branch, before or after
conditioning; the two that are resolved are resolved only in the branch where
attachment fails, which says nothing about the successful case the experiment is
actually about.

**And the two documents do not say quite the same thing about why, which is
worth keeping rather than smoothing over.** This analysis excludes the relays
because the node dictionary declares their proxy to be `bounded stochastic
initialization` — they are placeholders, so identifying the interface means
replacing them with mechanism, a **model repair**. The scRNA map's default
ceiling instead calls it an *assay* limit: "no change to the model would make it
measurable". Both are defensible and they are not in conflict once stated
carefully — a placeholder has no transcriptional correlate *because it stands for
nothing in particular*, and the route forward is to replace it with a mechanism
that does have one, which is then measurable. But the two sentences are
different claims, and a reader who needs the distinction should find it here
rather than infer agreement that was never established.

**Three limits on even that one gain, all recorded in the map.**

- `E_KLF12_HIGH`'s evidence role is `same_dataset_internal`. Across all 27
  observable states the roles are 11 `construction` and 16
  `same_dataset_internal`, and **none** held-out or external. Conditioning the
  model on a value derived from the same dataset used to build it is not
  validation and must never be reported as such.
- Seven of the 27 observable states are `phenotype_inert` in the current model.
  That is structural triage — this encoding routes nothing from them to a
  phenotype — and never a claim that the biology is irrelevant.
- Transcript abundance is not activity. Six of the observable rows are
  `proxy_abundance_not_activity` and the map forbids reading them as protein or
  pathway activity; four more are regulon or gene-program scores. Nothing here
  licenses substituting a transcript level for a node's activation.

**Measurement and perturbation stay separate.** An scRNA profile observes or
infers state; it excites nothing. The structural frontier in this document moves
only when an arm makes two conditions differ, and the 2×2 that matters is:
observable *and* independently perturbed gives the strongest causal test;
observable but never independently perturbed gives state or correlation evidence
only; perturbed but unobservable makes downstream consequences visible while
leaving the mechanism poorly localized; neither leaves the mechanism
unconstrained. The current `E2 + MPA + cAMP + XAV939` cocktail sits in the second
and third boxes for most of its components — it is a bundle, so no effect is
attributable to MPA, cAMP or XAV939 individually, which is why the candidate arms
above are dominated by "alone" and "cocktail minus" designs.

## What this analysis does not claim

- No percentage of the model is called "identifiable". The two frontiers are in
  different units and a ratio between them would be meaningless.
- Nothing here is a claim about biological importance. Grey in the figure means
  *this design cannot infer this state*, never *this state does not matter*.
- Trajectory frequencies, horizons, rates and physical time are untouched. The
  0.82 appears only as arithmetic on two declared initial probabilities.
- The scRNA-seq dataset is not counted in either frontier. It is not an arm: it
  carries no perturbation, so it cannot move the structural frontier at all, and
  what it can and cannot do to the latent frontier is worked out in the section
  below rather than left as an assumption.
- The candidate arms are structurally scored. Whether each is biologically
  sound, feasible in the ADOC chip, or ethically available is a separate
  judgement this analysis does not make.
