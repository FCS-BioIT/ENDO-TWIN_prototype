# Model Building

## Source Of Truth

The executable baseline is built from:

- immutable repository sources under `data/`
- `context/evidence-register.tsv`
- `context/node-candidates.tsv`
- `context/phase1-readouts.tsv`
- `context/references/adoc-maboss-model-specification.user-provided.md`

The user-provided model specification is an implementation reference, not a
standalone evidence source.

## Node Acceptance Rule

Accept a node into the executable model only when at least one of these is
true:

- it is a required experimental input;
- it is needed for a mechanistically supported edge;
- it is required for a pre-registered phenotype or readout;
- it provides necessary safety or recovery context.

Candidate nodes lacking defensible Boolean semantics remain catalogued but
non-executable.

## Edge And Rule Curation

For every executable edge record:

- source and target
- sign and direction
- mechanism
- evidence class
- human-versus-nonhuman scope
- direct versus inferred status
- confidence and notes

For every rule record:

- Boolean expression
- why each `AND` implies joint necessity
- why each `OR` implies alternative sufficiency
- why each `NOT` implies inhibition or absence requirement
- whether the rule is evidence-backed or an explicit model assumption
- any sensitivity or variant identifier

## Condition Policy

- untreated, E2 priming, HT, HT+mifepristone, HT+anti-SPP1, and washout share
  one baseline topology
- condition differences belong in inputs, initial states, or bounded rate
  scenarios
- topology changes require a new baseline model version

## Non-Negotiable Modeling Constraints

- anti-SPP1 acts on free extracellular SPP1, not transcription
- maternal adhesion competence stays separate from observed embryo adhesion
- marker-only nodes do not gain outgoing causal edges without evidence
- MaBoSS time remains relative unless externally calibrated
