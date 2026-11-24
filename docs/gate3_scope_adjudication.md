# Gate 3 scope: adhesion is a downstream phenotype, not a calibration target

Status: design adjudication, 2026-09-16. Supersedes the framing in
[`adhesion_variability_semantics.md`](adhesion_variability_semantics.md) §5–§6
on two points and corrects one claim there outright. No topology, rule, istate,
protocol, estimator or recorded output changes in this pass.

The prompting question was whether the A/B/C variability fork blocks Gate 3.
The measurements say it blocks only the interface subproblem, and that two of
the three options cannot explain the data they were proposed for.

## 1. Neither (A) nor (B) explains the mifepristone arm — proved, not argued

The endpoint is a **conjunction**, which the previous note did not take
seriously enough:

```
OUT_MATERNAL_ADHESION_COMPETENCE =
    OUT_EPITHELIAL_RECEPTIVE and S_DECIDUALIZED and X_MECHANICAL_PERMISSIVE_ECM
    and (X_ADHESION_ROUTE_SPP1 or X_ADHESION_ROUTE_REDUNDANT)
    and not X_ANTIADHESIVE_ROUTE

OUT_STABLE_ADHESION =
    OUT_MATERNAL_ADHESION_COMPETENCE and IN_EMBRYO_PRESENT
    and IN_TROPHECTODERM_COMPETENT and IN_EMBRYO_CONTACT
```

Exhaustively, over all 32 assignments of the cfg-weighted free variables:

| arm | maternal competence | stable adhesion |
|---|---|---|
| `adhesion_challenge_basal` | 0/32 | 0/32 |
| `adhesion_challenge_hormone_treated` | 12/32 | 12/32 |
| `..._mifepristone` | **0/32** | **0/32** |

And with all three embryo inputs *forced true* while every maternal free
variable varies, the mifepristone arm is still **0/32**.

So:

* **(A) embryo-side competence cannot rescue the 1/8.** Embryo competence is a
  conjunct multiplying a structural zero: `0 and x = 0` for every x. Making
  `IN_TROPHECTODERM_COMPETENT` stochastic can only *lower* the hormone-treated
  fraction; it can never create attachment under PGR blockade.
* **(B) maternal interface stochasticity cannot either**, as above.
* **(C) an observation model can**, and only because it sits *outside* the
  Boolean conjunction.

The previous note presented (A) and (B) as competing explanations of the same
three fractions. They are not: neither addresses the mifepristone arm at all.
That claim is withdrawn there and here.

The only *mechanistic* way to make the 1/8 non-zero is a maternal escape route
under PGR blockade. No evidence in this repository supports one, and inventing
it to fit a single event among eight would be precisely the move this project
has refused elsewhere. **The 1/8 is not evidence about maternal molecular
rules.**

## 2. The variability question cannot propagate into maternal topology

Pinning the three interface relays out of the model
(`X_INTERFACE_SPP1_RELAY`, `X_INTERFACE_REDUNDANT_RELAY` on;
`X_INTERFACE_ANTIADHESIVE_RELAY` off) and recomputing every arm:

* **0 of 34 maternal readouts change, in any of the 6 arms.**
* Only the terminal endpoint moves, and only in the hormone-treated arm
  (12/32 → 16/32).

Every maternal node is strictly upstream of every relay. Structurally, the
relays are **terminal coins multiplying an already fully-specified maternal
state**:

```
X_ADHESION_ROUTE_SPP1 = E_RECEPTIVE_SURFACE and X_SPP1_LUMEN_FREE
                        and E_ITGAVB3_5 and X_INTERFACE_SPP1_RELAY
```

All maternal content is in the first three conjuncts. The relay contributes no
maternal biology whatever. The earlier note called it "assay penetrance";
that over-committed. The defensible reading is narrower: these are
**unresolved terminal interface/penetrance variables** — they sit past the
maternal mechanism and conflate an unknown mixture of interface biology,
embryo variation and assay penetrance that this repository cannot currently
separate. Naming one of those as *the* content would be a claim the evidence
does not support. This is the conflation hazard stated directly: **a parameter inside
the maternal DT is absorbing embryo and assay variability**, and it is doing so
at the one place where it cannot be distinguished from mechanism.

**Conclusion: Gate 3's maternal work is not blocked.** The A/B/C fork is
confined to the terminal adhesion conjunction.

## 3. Adhesion's role in v0.5: diagnostic, not a magnitude-fitted objective

Three independent reasons, none of which is "the fit is poor":

1. **Two of three arms can never rank anything.** The basal arm contributes
   logL ≡ 0 and the mifepristone arm logL ≡ log(ε) for *every* candidate in the
   ensemble, because both are structurally deterministic. Only one arm carries
   any gradient at all.
2. **That one gradient is w.r.t. two relay coins containing no maternal
   biology**, and it is a one-dimensional ridge: the endpoint is their OR, so
   `(p₁,p₂) = (0.82, 0)` and `(0, 0.82)` — "entirely SPP1-routed" and "SPP1
   contributes nothing" — are bit-identical in log-likelihood.
3. **No per-embryo covariate exists** (§5), so embryo variability cannot be
   separated from maternal mechanism in these data by any analysis.

A term with one informative arm, whose gradient runs into a ridge between two
non-mechanistic parameters, and whose residual confounder is unmeasured, is not
a model-selection instrument. **Recommended status: downstream functional
validation / diagnostic.**

What is retained is the **ordinal** claim, which the model does satisfy and
which does not depend on any relay value: untreated < hormone-treated >
mifepristone. That is a real consistency check on maternal receptivity and it
survives removing the relays entirely.

**Implemented and declared 2026-09-16. Owner-directed; review-gate adjudication
still outstanding.** The demotion itself was not a unilateral call — the project
owner instructed it ("Proceed with demoting adhesion from the magnitude-fitted
objective to diagnostic/ordinal validation"). What is outstanding is the gate's
separate requirement, below.
`config/calibration.yaml` declares `role: diagnostic_ordinal`,
`magnitude_fitted: false`, and the retained ordinal claim, and the change is
declared to the review gate as a `SEMANTIC_OR_PROTOCOL` repair
(`repairs.json`, 11:04:32Z, re-declared later against a newer review subject).

**Declaration is not adjudication.** The gate requires such a repair to be
*judged by a broad sweep against the four repair questions* before it counts as
settled, and no broad sweep has judged this state: `aih scope` reports
`review: none`, `reviewed: False`. So this section describes a change that is
**in force in the code and unadjudicated by the gate**, and nothing here should
be read as the gate having accepted it. The blocking finding B1 that says so is
correct on this second point, and an earlier version of this paragraph — which
said only "Executed" and "Recorded" — asserted a settledness nothing had
conferred.

What would settle it: a cross-vendor broad sweep (`aih review
--require-independent`, blocked while Codex is out of credits), or the project
owner's `aih accept`. The scientific merits were separately reviewed PASS at
`b177511`; that is evidence about the change, not the gate judgement this
paragraph is missing.

### 3a. The consequence, stated rather than papered over

**This repository now has no quantitative magnitude-fitted objective at all.**
`adhesion_objective` was the only one. No replacement scalar has been
manufactured and none should be: a substitute would have to be a readout whose
*magnitude* the model can express and whose confounders are measured, and there
is no such readout here. Inventing one would re-import the same defect under a
new name.

**Gate 3a therefore proceeds as structural and evidence-based discrimination.**
Candidate rules are separated by whether they make *different predictions on
maternal molecular readouts*, and chosen on the evidence for those predictions —
not by a fitted score. This is a real constraint, not a formality: it means a
candidate can no longer be preferred because it "fits better", only because an
observation distinguishes it.

**What this does not change, verified rather than assumed.** Nothing in `src/`
ever ranked candidates on this likelihood. `rank_scenarios` and
`retain_acceptable_scenarios` in `calibration/search.py` are called only from
tests; `runner.py` takes `load_parameter_scenarios(root)["scenarios"][0]` — the
first scenario, unconditionally. So the second declared scenario
(`phase1b_xav939_required`, the XAV939 assumption-sensitivity variant) has never
been selected against the first by anything. The demotion removes an aspiration,
not a working fitting loop.

**A related dead-configuration finding, recorded not repaired.**
`models/specs/parameter_scenarios.yaml` declares
`relay_initial_states: {SPP1: 0.95, REDUNDANT: 0.01, ANTIADHESIVE: 0.05}`. No
Python reads that key. The istates that actually run come from `baseline.cfg`
(0.70 / 0.40 / 0.20), which is what produces the recorded 0.820. So the
repository states two different answers to "what relay values does this model
use?", and the one a reader would most likely edit is inert. Repairing it is a
v0.5 topology-adjacent decision, not part of this demotion.

## 4. What each relay means — they are not one class, and none changes yet

The previous note lumped all four. They are structurally different and their
dispositions differ.

| relay | position | disposition |
|---|---|---|
| `X_INTERFACE_SPP1_RELAY` | terminal, gates the SPP1 route | **Unchanged for now.** Reinterpreted as an unresolved terminal interface/penetrance variable. Removal or replacement is a separate v0.5 topology decision. |
| `X_INTERFACE_REDUNDANT_RELAY` | terminal, gates the redundant route | **Unchanged for now**, same reinterpretation. |
| `X_INTERFACE_ANTIADHESIVE_RELAY` | terminal, gates the antiadhesive route | **Unchanged for now**, same reinterpretation. The barrier biology upstream of it (`E_PODXL`, `E_DAG1_FULL`, `E_MUC1_BARRIER`) is maternal and testable regardless. |
| `X_MECHANICAL_STRESS_RELAY` | **upstream, not terminal** | **Retain as an explicit unresolved placeholder.** Categorically different from the other three, and the earlier lumping was wrong. |

On the fourth: it gates

```
X_MECHANICAL_PERMISSIVE_ECM = S_DECIDUALIZED and S_TAZ_ECM
    and not ((IN_ER_STRESS_EXCESS or IN_HIGH_ECM_STIFFNESS)
             and X_MECHANICAL_STRESS_RELAY)
```

It is not a penetrance coin. It is a **conditional switch for stress-challenge
arms that have never been run** — both `IN_ER_STRESS_EXCESS` and
`IN_HIGH_ECM_STIFFNESS` are off in every recorded arm, which is the real reason
it is endpoint-inert, not because it is vacuous in principle. It encodes a
genuine maternal mechanistic hypothesis (ER stress or matrix stiffening impairs
decidual ECM permissiveness), it is upstream of maternal readouts, and it is
testable with maternal readouts alone. It should **not** be removed with the
interface trio.

## 5. Embryo/chip/donor metadata, and the claim ceiling

Audited against `data/2 Zaragozano et alClean copy.docx`, the supplementary
file, `context/evidence-register.tsv` and
`config/adoc_chip_donor_provenance.tsv` (which covers the secreted-protein
outlet only — it contains **no** embryo rows).

| field | status |
|---|---|
| condition / arm | **available** |
| adhesion yes/no | **available in aggregate only** (0/12, 9/19, 1/8) |
| day 5–6 p.f. | **available as a range**, not per embryo |
| hatching state | **available and uniform** — all embryos underwent 30% assisted hatching, and only hatched blastocysts were selected |
| attachment time | **aggregate only** — 34.1 ± 12.2 h among the 9 attached |
| chips / donors | **aggregate only** (9 chips, 4 donors for the HT arm); per-embryo assignment is **referenced but absent** — `SOFIA-ADH-001` says it "must be recovered if available" and it never was |
| TE grade, ICM grade, expansion | **unavailable** — no Gardner or other grading of study embryos is reported; "Gardner" occurs in the manuscript only as an author surname in the reference list |
| euploidy / PGT | **unavailable** |
| per-embryo morphology or imaging | **unavailable** as data (time-lapse exists as figures, not as a per-embryo table) |
| batch / date | **unavailable** |

Two consequences:

* **The claim ceiling on adhesion is an ordinal, aggregate one.** No per-embryo
  covariate exists, so no analysis can attribute any part of 9/19 to embryo
  versus maternal versus assay variation.
* **An embryo heterogeneity model cannot be fitted or tested** on these data. It
  would have one free distribution constrained by one number, and no covariate
  to validate against. Building it now would be inventing a latent.

Worth recording: assisted hatching was applied to **all** embryos and only
hatched blastocysts were used, so two large quality covariates were
experimentally standardised away rather than left to vary. That narrows, but
does not eliminate, the embryo-heterogeneity channel.

## 6. An explicit observation model is **not** required now

Deferred, on §5's evidence rather than on preference. The interim architecture
is sufficient and is adopted:

* the core DT models **maternal molecular competence**;
* embryo attachment is **conditional on embryo and interface factors not
  modelled**;
* attachment fractions are therefore **not quantitative calibration targets**
  for the maternal DT at this stage.

This is strictly more honest than the status quo, which encodes the same
ignorance as two typed numbers inside maternal nodes.

## 7. Structural-zero observations: flag, do not fit away

Adopted and **implemented** in
`src/dt_adoc/calibration/adhesion_likelihood.py`:

* keep numerical clipping internally for code stability;
* compute the **unclipped** model probability, and when it is exactly 0 with
  `successes > 0`, mark that arm/model pair **`structurally_contradicted`**;
* **never** use the clipped log-likelihood of a structurally contradicted arm as
  a quantitative model-selection score — it is `log(ε)`, a property of the
  constant, not of the model. Such an arm is
  `structurally_contradicted` **and** `quantitatively_unscorable_for_ranking`:
  the number must not be compared, summed into a total that is then compared, or
  read as "how badly" the model missed;
* report the contradiction as a qualitative verdict instead.

> **SCIENCE: owner-adjudicated. REVIEW GATE: broad-sweep adjudication still
> outstanding.** The history, because it matters for how the choice was made:
> an external reviewer correctly flagged (2026-09-16) that choosing between
> (A) report −∞ and record the arm as structurally falsified, (B) keep the clip
> and mark the arm uninterpretable, and (C) declare the arm unscorable is a
> three-way methodological fork that met the consultation bar, and that I
> implemented (B) without consulting. `aih consult` was run afterwards on this
> specific fork and returned `UNAVAILABLE — the Codex workspace is out of
> credits`, which is not agreement. Per the exit-3 path the choice was therefore
> referred to the project owner.
>
> **ADJUDICATED BY THE PROJECT OWNER, 2026-09-16.** The owner responded and
> chose option (B), in these words: *"I prefer treating an observed-success /
> model-P=0 arm as: `structurally_contradicted + quantitatively_unscorable_for_
> ranking`. The numerical clip may remain internally for stability, but
> `log(1e-9)` should never look like a scientifically meaningful score."* That
> is recorded here because it is otherwise unverifiable: it was given in
> session, and a reviewer reading this repository has no other artifact for it.
> `config/calibration.yaml`'s `structural_contradiction_policy` implements
> exactly that wording.
>
> **This settles the science, not the gate.** The scientific fork is decided by
> the person entitled to decide it. The review gate's separate requirement —
> that the `SEMANTIC_OR_PROTOCOL` repair be judged by a broad sweep — is still
> unmet, and §3 says so. The two must not be conflated: an earlier `aih defer`
> reason of mine cited the owner's endorsement as though it closed the gate
> finding, which it does not, and cited it without any repository artifact
> backing it, which a reviewer correctly caught.
>
> For the record, the argument against (A) is this repository's own: the
> concordance analysis already withdrew a "structural falsification" claim for
> this exact arm, on the grounds that a fixed-point result does not carry to a
> finite horizon. The argument against (C) is that a blank hides a genuine
> model/data conflict.

Explicitly **not** done: altering any maternal rule to make the mifepristone
event non-zero. Per §1 that event carries no information about maternal rules,
and fitting it would import assay penetrance into mechanism.

## 8. Gate 3 is split

* **Gate 3a — maternal (proceeds now).** Epithelial/stromal topology
  discrimination on maternal molecular readouts. Unblocked, per §2.
* **Gate 3b — interface/penetrance (quarantined).** Relay disposition, the
  observation boundary, and any attachment-probability modelling. Revisited when
  the maternal core is mature, or if per-embryo metadata is recovered.

### 8a. Gate 3a, after the first discrimination pass

Computed in [`variant_discrimination.md`](experiments/variant_discrimination.md). Three
distinctions are kept apart there, because collapsing any of them overstates a
candidate: structural vs experimental separability; discrimination in a
**current arm** vs one needing a **new controlled input**; and a difference in a
**model state** vs one in a **measurable readout**.

| Axis | Status |
|---|---|
| CD98 | `CD98-c` separable from both others in the embryo-free `e2_primed_maternal` arm, opposite predictions. `CD98-a` vs `CD98-b` needs an **hCG-on arm**: `IN_HCG` is declared and off everywhere, so no current arm separates them but one that supplies hCG does. |
| CDH1 | both pairs separable **only with embryos in the current design**. Turning on `IN_HCG` or `IN_EMBRYO_CONDITIONED_SIGNAL` opens an embryo-free route for `a vs b`, but **destroys** the `b vs c` discrimination — with either cue on, both rules are satisfied everywhere, so `b vs c` is separable only where contact occurs without a cue, which needs an embryo |
| GP130 | **requires supplying IL-11**; with IL-11 absent the variant is identical to v0.4 |
| PC6 | **requires a cleavage-resistant DAG1 construct**; with wild-type substrate the variant is identical to v0.4 |

**Readout availability, in three tiers rather than two.** The comparison and
the readout lookup run over one universe — `E_*`, `S_*` and the two maternal
composites — and the lookup now distinguishes:

* **`usable_assay`** — the observation layer acts on it (`active_constraint` or
  `active_diagnostic`) *and* it has real source rows. Only `E_PAEP` and
  `S_IGFBP1` qualify.
* **`mapped_composite_not_validating`** — mapped, propagation preserved and
  reported, but `reported_only`/`provisional` or `source_rows_n = 0`. `S_PRL`,
  `OUT_EPITHELIAL_RECEPTIVE` and `OUT_STROMAL_DECIDUALIZED` are here.
* **`no_assay`** — not mapped at all.

An earlier version of this section called `OUT_EPITHELIAL_RECEPTIVE`
"measurable today" on the strength of its being mapped. That was wrong, and
OM-009 says so itself: `reported_only`, `confidence=low`, `source_rows_n=0`,
`objective_treatment=not_used`, and a `claim_ceiling` reading *"Not usable to
validate OUT_EPITHELIAL_RECEPTIVE behavior"*. On the corrected tiering
**no Gate-3a pair separates on a usable assay** — GP130 and PC6 separate on a
mapped composite that cannot validate the node, and CD98 and CDH1 on nothing
mapped at all.

**Excluding `IGFBP1-fb` does not close the PRL/IGFBP1 task.** What was excluded
is one proposed *repair* — adding `S_IGFBP1` as an input to `S_DECIDUALIZED` —
on two independent grounds: it creates a 14-node cycle the structural
enumerator cannot evaluate, and `S_IGFBP1` carries an observation-map role, so
an outgoing causal edge would make the model that interprets that measurement
depend on it. The underlying problem is untouched and live: `S_PRL = S_IGFBP1 =
S_DECIDUALIZED` share one rule, one initial state and one default rate, so their
onset distributions are identical by construction and the recorded
IGFBP-1-before-PRL onset order is not expressible at all. That axis is also the
**only** one whose nodes the observation layer actually measures, which makes it
the next unit rather than GP130.

**Done in this unit:** §3 and §7 are executed — `adhesion_objective` demoted to
`diagnostic_ordinal`, the ordinal claim retained, `structural_verdict` /
`is_rankable` added and wired through the runner, recorded with
`aih repair --kind SEMANTIC_OR_PROTOCOL`. No topology changed.

**Smallest next unit: the PRL/IGFBP1 axis** — an executable day-3 state plus
transient rule variants. It is the only Gate-3a axis whose nodes the observation
layer actually measures (`S_IGFBP1` active, `S_PRL` provisional), and the
recorded IGFBP-1-before-PRL onset order is currently inexpressible because
`S_PRL = S_IGFBP1 = S_DECIDUALIZED` share one rule, one initial state and one
default rate. The Gate-3a discrimination pass that used to be named here is
**done**; see §8a.

## 9. Perturbations re-ranked: axis A, under a one-perturbation budget

Ranked by how strongly each discriminates **maternal mechanisms we expect to
retain**, read out on **proximal maternal markers** — not by distinct-function
count, not by relay-ridge reduction, not by adhesion fit. Two constraints are
applied that the first version of this ranking ignored:

* **the one-perturbation budget** — a realistic campaign affords roughly one
  perturbation, so a proposal needing two is a different and more expensive
  thing, and is listed separately rather than mixed in;
* **new measurement vs reanalysis** — a readout ADOC has never performed is a
  new measurement even when the *arm* already exists.

### Clean one-shot experiments

| # | perturbation | maternal readout | discriminates | measurement status |
|---|---|---|---|---|
| 1 | **none** — add a day-2 readout to the existing E2-priming phase | **surface CD98/CD9** | CD98-b (predicts OFF) vs CD98-c (predicts ON) | **new measurement** |
| 2 | **anti-LIF alone** | **pSTAT3** | whether `E_GP130_STAT3 = E_LIF` (v0.4's identity) survives LIF neutralisation; if pSTAT3 persists, that identity is false and a second GP130 ligand is required | new measurement |
| 3 | **SMO antagonist alone** (stromal) | **NR2F2, HAND2, BMP2** | the PGR→IHH→stroma axis; directly addresses GAP-014, which is a *necessity* gap rather than an expression gap | new measurement |
| 4 | **PC6 knockdown alone** | **α-DG-N shedding** | whether PC6 is required for DAG1 cleavage — `E_PC6 = E_DAG1_CLEAVED` is directly contradicted | new measurement |

### Coupled perturbations — theoretically stronger, but two interventions

| perturbation | readout | discriminates | why parked |
|---|---|---|---|
| IL-11 **plus** LIF neutralisation | pSTAT3, surface CD98, surface ITGA2 | GP130-b, CD98-b and CD98-c at once | two perturbations; #2 recovers much of the GP130 content for one |
| PC6 knockdown **vs** cleavage-resistant DAG1 substrate | α-DG-N shedding | enzyme from substrate | the second arm is a laboratory construct, not a state ADOC varies |
| EPAC- vs PKA-selective cAMP analogues | PRL, IGFBP1 | informs a future **rate layer**, not topology — Kusama 2013 shows graded potentiation, which a rate-free Boolean model cannot express | wrong model class, not wrong experiment |

### On #1: the arm exists, the measurement does not

Corrected from the first version of this ranking, which called it "free". It is
not free, and it is not a reanalysis.

* **What exists.** `e2_primed_maternal` is a committed, runnable condition, and
  `COND-E2-PRIMING` (day 0–2, E2 10 nM, 48 h) is a real protocol interval that
  **every HT run already passes through** — so a day-2 readout can be added to
  the standard protocol rather than needing a separate arm. That is a genuine
  practical advantage and the reason this stays ranked first.
* **What does not exist.** ADOC has **no CD98/CD9 measurement at any
  timepoint**. The day-2 outlet panel is `PAEP; IGFBP-1; PRL`; the scRNA-seq is
  HT vs untreated only, so there is no E2-only transcriptome either. The only
  CD98 evidence in the repository is `LIT-CD98-001` (REF-008, Domínguez),
  which is literature, not ADOC data.
* **And a transcript would not settle it.** The node `E_CD98_CD9` means
  *surface availability*. `AGENTS.md` is explicit that expression and protein
  abundance are not node activity, so `SLC3A2` counts would not discriminate
  the variants even if an E2-only transcriptome existed. The readout has to be
  surface protein.

So #1 is a **new measurement on existing material and an existing protocol
phase** — the cheapest real information available, but it must be planned and
costed as a measurement, not assumed to be sitting in the data.

The structural premise is verified against the committed model: under
`e2_primed_maternal` (inputs ON: `IN_E2` only), `E_PGR` and therefore
`E_GP130_STAT3` are false in **all 32** assignments and `IN_HCG` is off, so
CD98-b predicts **OFF** and CD98-c predicts **ON** — opposite predictions from
one readout.

> **Refined by the Gate-3a pass**
> ([`variant_discrimination.md`](experiments/variant_discrimination.md)). The contrast above
> is true but incomplete: **CD98-b is not discriminable from v0.4 in any
> recorded arm at all**, because its only new disjunct is `IN_HCG`, which is
> false everywhere. Its recorded 35 → 36 structural gain is real and
> experimentally empty. So this measurement collapses three CD98 readings to
> **two** classes, `{a, b}` against `{c}`, and no available experiment separates
> `a` from `b`. The candidate table's "CD98-b — preferred" status is withdrawn:
> preferring it over v0.4 had no observational support. Separating them needs an
> hCG arm, and `IN_HCG` is zero-degree, so that arm only becomes informative once
> a variant that reads it is adopted. The row at #1 above should therefore be
> read as *CD98-c versus the other two*.

## 10. anti-SPP1: the earlier recommendation is withdrawn

The identifiability result stands mathematically — under `IN_ANTI_SPP1` the
endpoint stops depending on `X_INTERFACE_SPP1_RELAY`, so that arm estimates p₂
alone and with the hormone-treated arm identifies p₁.

**But the target of that identification is the relay abstraction itself**, and
§4 recommends moving those relays out of the core DT. If that is done, the
parameters anti-SPP1 was uniquely good at identifying **cease to exist**. The
value was conditional on retaining precisely the construct now judged to be a
modelling artifact — which is a clear case of interface/adhesion information
value (axis B) masquerading as overall information value.

On axis A the perturbation is weak, and the candidate generator sharpened this
after the first version of this section was written. `X_SPP1_LUMEN_FREE` is
**not** purely terminal: it is one disjunct of `E_RECEPTIVE_SURFACE`, a
maternal epithelial node, so `IN_ANTI_SPP1` does have a topological path into
the maternal network. But that path carries nothing. The other seven disjuncts
of `E_RECEPTIVE_SURFACE` are true in **all 32** assignments under hormone
treatment, so toggling `IN_ANTI_SPP1` leaves `E_RECEPTIVE_SURFACE` at 16/32
unchanged while the endpoint moves 12/32 → 8/32. Measured across every recorded
arm, anti-SPP1 **moves no maternal node at all**.

That is the distinction the report is built to keep: structural reach is not
experimental information, and reporting the reach alone would have overstated
this experiment. The perturbation also reads out only through the embryo
endpoint, the noisiest phenotype available.

**Decision: de-prioritised as a calibration experiment.** It retains axis-C
(translational) interest, which is a separate question for Gate 6 and is not
evidence for running it now. Nothing here pre-selects anti-SPP1 for Gate 6.
