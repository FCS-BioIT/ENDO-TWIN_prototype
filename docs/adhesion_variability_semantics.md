# Where between-embryo variability lives, and why Gate 3b cannot start yet

Status: analysis finding, 2026-09-16. No topology, rule, istate, protocol or
recorded output changes with it. It exists because the plan's next step —
decomposing the interface relays into mechanism — turns out to be blocked by a
question nobody has answered, and the block is structural rather than a matter
of finding better evidence.

## What was already known, and is not restated as new

`docs/concordance_analysis.md` already records, and this note does not
rediscover:

* the hormone-treated magnitude is wrong: converged **0.820** against observed
  9/19 = 0.474, outside the Wilson 95% CI [0.27, 0.68];
* it is not a fitted quantity — `baseline.cfg` sets the two interface relays at
  **0.70** and **0.40** and `1 − (1−0.70)(1−0.40) = 0.82` exactly, so "the
  entire graded content of the model's headline prediction is two hand-set
  numbers";
* the **logical fixed point** under sustained mifepristone is 0 in all
  2¹⁹ = 524,288 assignments, and that result does **not** carry to finite
  horizons, which is why `structural_falsification` is an empty class.

All of that stands. What follows is about the *calibration objective* and the
*variability semantics*, which those sections do not cover.

## 1. The two carrier relays are not separately identifiable — even in principle

"Two hand-set numbers" understates the problem. In the hormone-treated arm the
endpoint is the **disjunction** of the two positive relays:

```
SPP1=0 REDUNDANT=0 -> 0       SPP1=1 REDUNDANT=0 -> 1
SPP1=0 REDUNDANT=1 -> 1       SPP1=1 REDUNDANT=1 -> 1
```

so the model probability is `1 − (1−p₁)(1−p₂)` and a binomial likelihood on an
attachment fraction sees **only that scalar**. Fitting cannot recover the pair.
These are bit-identical in log-likelihood:

| SPP1 p₁ | REDUNDANT p₂ | combined | logL on 9/19 |
|---|---|---|---|
| 0.70 | 0.4000 | 0.8200 | −18.934043 |
| 0.50 | 0.6400 | 0.8200 | −18.934043 |
| 0.82 | 0.0000 | 0.8200 | −18.934043 |
| 0.00 | 0.8200 | 0.8200 | −18.934043 |

The last two rows matter: "adhesion is entirely SPP1-routed" and "SPP1
contributes nothing" are the *same point* on this objective. The relay pair is
a one-dimensional ridge, and no adhesion fraction from the three recorded arms
can move along it.

For scale, the typed values are also not the maximum-likelihood ones: the MLE
for 9/19 is 0.4737 at logL −13.14, against −18.93 for the typed 0.82.

## 2. An experiment the project has already designed breaks the ridge

The arm is not hypothetical and needs no new modelling work. `IN_ANTI_SPP1` is
a declared model input, `anti_spp1_challenge` a declared phase in
`config/calibration.yaml`, and the full chain already exists and compiles:
`hormone_treated_anti_spp1.cfg` and
`adhesion_challenge_hormone_treated_anti_spp1.cfg` are committed conditions,
declared in `config/protocols.yaml` with
`continuation_from: hormone_treated_anti_spp1`, and both are in the
`pixi run compile-models` protocol list. **What is missing is only the wet
experiment** -- no embryo arm has been run under SPP1 blockade, so the row has
no observed fraction to fit.

Setting the input changes the endpoint's dependence structure:

```
IN_ANTI_SPP1 = True:
SPP1=0 REDUNDANT=0 -> 0       SPP1=1 REDUNDANT=0 -> 0
SPP1=0 REDUNDANT=1 -> 1       SPP1=1 REDUNDANT=1 -> 1
```

The endpoint no longer depends on the SPP1 relay at all, so that arm estimates
**p₂ alone**; with the existing hormone-treated arm it then identifies p₁. One
attachment fraction under SPP1 blockade converts a structurally unidentifiable
pair into an identified one.

**This is a model-identification argument and nothing else.** It is not a claim
that SPP1 is a contraceptive target, not a recommendation to prioritise
anti-SPP1 translationally, and it does not pre-select anti-SPP1 for Gate 6. The
value here is that the arm discriminates between two model states that no
current observation can separate; that value would be identical if the blocking
agent were of no therapeutic interest whatever.

## 3. The reported log-likelihoods are partly a function of a clip constant

`calibration/adhesion_likelihood.py` clips the model probability into
`[1e-9, 1−1e-9]` before taking logs. That is a correct and ordinary numerical
guard when a probability is merely *small*. It is unsound here, because the
probability is not small — in several arms it is **structurally zero**, and the
clip silently converts "the model says this observation is impossible" into
"the model is penalised by an amount someone chose".

**Held-out validation arm** (mifepristone, observed 1/8). At the converged
horizon the model gives exactly 0.0 in 5/5 seeds, so the reported held-out
log-likelihood is **−20.72 for every candidate in the ensemble** — and −20.72
is `log(1e-9)`, not a property of the model:

| clip ε | held-out logL |
|---|---|
| 1e-6 | −13.82 |
| 1e-9 | −20.72 |
| 1e-12 | −27.63 |

At the *declared* horizon the same model swings **10.8 nats across seeds**
(−20.72, −15.20, −20.72, −9.90, −9.90) purely according to whether the clip
binds in that seed.

**The fitted term too.** At the declared horizon the hormone-treated arm is 0.0
in 5/5 seeds, so the calibration log-likelihood is `9·log(ε) + 10·log(1−ε)` =
−186.51, against −18.93 at the converged horizon: a **168-nat** difference from
a horizon choice, with the declared-horizon value determined by ε.

**Resolved 2026-09-16, after this note was written.** The fork — report −∞ and
call the arm falsified, keep the clip and mark the number uninterpretable, or
declare the arm unscorable — was decided in favour of the middle option, and
the estimator was *not* silently changed: `structural_verdict` and
`is_rankable` in `calibration/adhesion_likelihood.py` now classify an arm from
the **unclipped** probability, the clip survives only as a numerical guard, and
a `structurally_contradicted` arm is excluded from candidate ranking. The
mifepristone arm is currently the one that fires. Declared to the review gate as
a `SEMANTIC_OR_PROTOCOL` repair, but **not yet judged by a broad sweep and
therefore not settled** — see
[`gate3_scope_adjudication.md`](gate3_scope_adjudication.md) §3 and §7.

## 4. Two of the four relays are unconstrained by every observation

Over all 32 assignments of the cfg-weighted free variables, per arm:

| arm | reachable endpoint values | depends on |
|---|---|---|
| `adhesion_challenge_basal` | {0} only (0/32) | nothing — deterministic |
| `adhesion_challenge_hormone_treated` | {0,1} (12/32) | `E_KLF12_HIGH`, SPP1 relay, REDUNDANT relay |
| `adhesion_challenge_hormone_treated_mifepristone` | {0} only (0/32) | nothing — deterministic |

`X_INTERFACE_ANTIADHESIVE_RELAY` and `X_MECHANICAL_STRESS_RELAY` change the
endpoint in **no recorded arm**. They carry istates (0.2 and 0.3) that no
observation the project holds can constrain in either direction.

## 5. The relays are doing two incompatible jobs, and that blocks Gate 3b

Collecting the above: two of the three challenge arms are deterministic, so the
model's **entire** capacity to produce a fraction rather than a 0 or a 1 is two
relay coins in one arm. The relays are therefore simultaneously

1. **stand-ins for unknown interface biology** — the thing Gate 3b exists to
   replace with mechanism; and
2. **the only representation of between-unit variability** — the thing that
   lets the model express 9/19 at all.

Replacing (1) with mechanism destroys (2). A mechanised interface is a function
of the arm's inputs, so every arm becomes deterministic, the model predicts 0 or
1 everywhere, and it then matches *none* of 0/12, 9/19, 1/8 — a strictly worse
fit than it has now. Gate 3b as planned cannot be executed without first
deciding where between-unit variability lives.

## 6. The current attribution is biologically the wrong default

`IN_TROPHECTODERM_COMPETENT` is `True` in all three challenge arms, and the
embryo-side inputs are `bundled_perturbed` — not independently controllable. So
the model asserts that **every embryo is competent** and places 100% of
between-embryo variability in the maternal interface.

That is not a neutral modelling choice. Blastocyst quality is a large and
well-documented source of implantation variability, ADOC contributed 39 human
blastocysts across these arms, and the biological unit recorded throughout
`docs/concordance/concordance_table.tsv` is the **embryo**, not the chip or the
donor. The single mifepristone attachment (1/8) is precisely the observation a
maternal-only stochastic model cannot produce: under full PGR blockade the
maternal side is deterministically non-receptive, so any attachment must come
from somewhere the model has no variable for.

At least three positions are defensible, and the evidence in hand does not
choose between them:

* **(A) Embryo-side competence.** `IN_TROPHECTODERM_COMPETENT` becomes a
  genuine per-embryo stochastic input; attachment fraction reflects the fraction
  of competent blastocysts. Biologically the most conventional reading, and it
  uses a variable the model already declares.

  > **Correction, 2026-09-16.** An earlier version of this bullet added that (A)
  > "predicts the mifepristone survivor is a high-competence embryo rather than
  > a maternal escape". **That is false and is withdrawn.**
  > `OUT_STABLE_ADHESION` is a *conjunction*:
  > `OUT_MATERNAL_ADHESION_COMPETENCE and IN_EMBRYO_PRESENT and
  > IN_TROPHECTODERM_COMPETENT and IN_EMBRYO_CONTACT`. Under mifepristone
  > `OUT_MATERNAL_ADHESION_COMPETENCE` is false in **all 32** assignments, so
  > embryo competence multiplies a structural zero and cannot rescue the 1/8 at
  > any value. The same holds for (B): with every maternal free variable
  > varying *and* all three embryo inputs forced true, adhesion under
  > mifepristone is still 0/32. Neither (A) nor (B) explains that arm. See
  > [`gate3_scope_adjudication.md`](gate3_scope_adjudication.md).
* **(B) Maternal interface stochasticity** (the status quo). Defensible if the
  interface genuinely has bistable or threshold behaviour per chip. It predicts
  the fraction should track chip/donor identity, which
  `SOFIA-ADH-001`'s own note says must be recovered "if available" — and it has
  not been.
* **(C) A separate observation model.** The Boolean twin returns a
  deterministic competence state and a declared observation layer maps it to a
  per-embryo attachment probability. Cleanest separation of mechanism from
  penetrance, and the honest home for a quantity the Boolean class cannot
  express; costs an explicit new layer.

These make **different, testable** predictions about the same existing data —
(A) predicts variance structured by embryo, (B) by chip/donor — and the
per-embryo chip and donor mapping needed to separate them is exactly what the
concordance table records as lost for some readouts and present for others.

## What this note does not do

It does not choose between (A), (B) and (C); that choice sets the meaning of
every probability the project reports and belongs to a consultation, not to a
silent edit. `aih consult` was run against the brief on 2026-09-16 and returned
`UNAVAILABLE - the Codex workspace is out of credits`, which is not agreement,
so the fork is referred to the project owner undecided rather than resolved by
the author of the analysis. It does not change `network.bnd`, any `.cfg`, any istate, the
clip, or any recorded output. It does not promote `IN_TROPHECTODERM_COMPETENT`
to a free stochastic variable, which would be exactly the "invent a latent
variable because it improves the fit" move the project has refused elsewhere.
The *structural* facts above are pinned by
`tests/unit/test_adhesion_variability_semantics.py` so they cannot drift
unnoticed: the two deterministic arms and the one that varies (§4), the relay
disjunction and the likelihood-identity of opposite attributions (§1), the
anti-SPP1 dependence change (§2), the two endpoint-inert relays (§4), the
clip's behaviour on a structural zero (§3), and the per-arm embryo-input
assignments and their `bundled_perturbed` status (§6). Each fails if the
limitation it records is repaired, at which point this document must be revised
rather than the test loosened.

What is **not** pinned, because no test can pin it, is the inference in §5 that
mechanising the relays would make every arm deterministic, and the judgement in
§6 that maternal-only attribution is the wrong default. Those are arguments
from the pinned facts, not facts.
