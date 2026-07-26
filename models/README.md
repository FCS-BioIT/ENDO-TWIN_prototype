# Model workspace contract

Store versioned baseline and donor-contextualized MaBoSS artifacts here. Do not
put generated simulation outputs or source data in this directory.

The phase-1 model is a coupled epithelial–stromal baseline with matched
untreated, hormone-treated, and hormone-treated plus mifepristone
configurations. Conditions may change inputs, initial states, or declared
perturbations; they must not silently change topology.

The current standalone literature-derived extension lives under
`models/extended/adoc-literature-v0.2.0/`. It is versioned separately from the
baseline because it adds evidence-backed maternal adhesion mechanisms without
changing the committed `adoc-core-v0.1.0` topology.

A baseline model version requires:

- `network.bnd`;
- `baseline.cfg`;
- `conditions/untreated.cfg`;
- `conditions/hormone_treated.cfg`;
- `conditions/hormone_treated_mifepristone.cfg`;
- `node_dictionary.tsv`;
- `edge_evidence.tsv`;
- `phenotype_contract.tsv`; and
- `provenance.toml`.

A donor-contextualized variant requires:

- a repository-safe donor pseudonym;
- `donor.cfg` or an explicit patch against the baseline;
- `mapping.tsv` linking audited donor-level features to model changes; and
- `provenance.toml` recording parent hashes, mappings, and assumptions.

Never overwrite a baseline to create a donor model. Never encode direct patient
identifiers in filenames or node names. No model is currently canonical.
