# ADOC Literature Superset v0.5.0 — scaffold

**Status: scaffold.** Every executable and catalog artifact in this directory is
**byte-identical to `models/superset/adoc-literature-superset-v0.4.0/`**. No
rule, node, edge, threshold, rate, condition or phenotype differs. Only three
files differ from v0.4.0, and only because a model directory must name itself:
`provenance.toml`, `README.md` and `executable_model_manifest.tsv`.

That identity is not a comment. `tests/unit/test_v05_scaffold.py` asserts it
file by file, so the first U2 commit that changes any rule shows up as exactly
that change and nothing else. Until then this directory makes no claim that
v0.4.0 does not already make.

## What this is for

U1 of `docs/v05_mechanistic_integration_plan.md`: give v0.5 somewhere to be
built, with v0.4 frozen behind it, before any mechanism changes. The ordered
units that follow are U2 (Gate 3a de-aliasing) onward; see the plan.

## What it is not

- **Not generator output.** `dt_adoc.model.superset_family.MODEL_VERSION` still
  reads `adoc-literature-superset-v0.4.0`. This directory was produced by
  copying, and its provenance record says so. Whether U2 retargets the generator
  or edits these artifacts directly is a U2 decision that U1 deliberately does
  not take.
- **Not a new claim.** `claim_boundary` is `scaffold_only_no_new_claim`. The
  v0.4.0 claim ceiling below still binds and is not relaxed here.
- **Not a personalized or calibrated model.** As in v0.4.0: MaBoSS
  probabilities are simulated trajectory frequencies under stated rules, rates
  and initial conditions, not clinical probabilities.

## Relationship to v0.4.0

`models/superset/adoc-literature-superset-v0.4.0/` is now an **immutable
parent**. `tests/unit/test_v04_immutability.py` pins every one of its 41 files
against the digests v0.4.0's own `provenance.toml` records, and pins that
provenance file too, so a file cannot be changed and its recorded hash restated
to match in the same commit.

That is **tamper-evident, review-enforced** immutability, not a cryptographic
guarantee: an agent willing to edit the pinned literal in the test can still
change v0.4 and get a green suite. What the pin buys is that doing so must
appear in the diff, as an edit to a test whose only purpose is to prevent it.
A diff touching that literal is a proposal to stop treating v0.4 as immutable,
and should be reviewed as one.

One inherited defect is recorded rather than repaired: v0.4.0's `README.md` is
titled *"ADOC Literature Superset v0.3.0"*, because the generator hardcodes that
string. It is wrong in v0.4.0 and stays wrong there, because v0.4.0 is frozen.
It is corrected in this file only, which makes the title the one intentional
content divergence beyond self-naming. That divergence is recorded in this
directory's `provenance.toml`, under `[scaffold.inherited_defects]`, and in
§17 of `docs/v05_mechanistic_integration_plan.md`.

*Corrected after review:* this paragraph previously cited
`docs/v05_line_endings.md`, which records the line-ending freeze and says
nothing about the README title. In a scaffold whose whole value is
byte-identity, the one deliberate exception must point at a document that
actually justifies it.

## Artifacts

Identical to v0.4.0; see that directory's `README.md` for the artifact
inventory, scope and claim boundary, all of which continue to apply.
