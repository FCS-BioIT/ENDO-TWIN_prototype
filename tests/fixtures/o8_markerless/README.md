# O8 markerless-intervention fixture

Synthetic data for the O8 gates (`docs/o8_markerless_interventions.md`). Nothing
here is evidence, and nothing here is a compound. The identifiers are invented so
that a test can add an intervention the model does not encode, and the targets
were chosen only because their rules are simple and read no legacy input.

Since Stage 4b (`docs/stage4b_direct_admission.md`) each synthetic compound is
four files, and those four files are the whole of what adding it takes:

- `<compound>.evidence.tsv` holds its `context/evidence-register.tsv` rows,
  without the header;
- `<compound>.declaration.tsv` holds its
  `config/direct_effect_target_declarations.tsv` row, without the header: the
  known target entities, the reached compartments and the `library_rows_sha256`
  of its rows, checked by C1-C8 against `config/node_entity_map.tsv`;
- `<compound>.adjudication.tsv` holds its `config/direct_effect_adjudications.tsv`
  rows, without the header: one synthetic approval per effect, each bound to the
  library row's digest and to the declaration's sha256. They use the
  `synthetic_fixture` vocabulary (including `system_grade`), which the loader
  accepts only together with evidence whose register status is
  `synthetic_fixture`;
- `<compound>.library.tsv` holds its `config/intervention_library.tsv` rows,
  without the header.

The tests build a sandbox repository from `models/`, `config/`, the evidence
register, the two `docs/stage4b` expressivity tables and the staged candidate
table, append these rows to the sandbox copies, and run the production
`run_protocol` against the sandbox. Appending library rows adds an arm to the
expressivity artefact, so the sandbox regenerates those two tables with the
committed generator. The canonical library, declarations, ledger and register
are never edited. Editing a fixture library row invalidates its approval's
`library_row_sha256` and its declaration's `library_rows_sha256`;
`python -m dt_adoc.perturbations.adjudication digests`, run against a sandbox
root, prints the new row digest.

Stage 4b moved both compounds from v0.5.2 to v0.6.0: a direct row now needs an
entity map and an expressivity artefact for its version, and only v0.6.0 has
them.

## synthetic_compound_x

One target, `E_GP130_STAT3`, under `activity_veto`, declared through
`LIFR@activity` (one member of an `all_of` node). Not a claim about any reagent.

## synthetic_compound_y

Two targets, `E_HBEGF` and `S_TAZ_ECM`, under `activity_veto`. It exists to show
that a second markerless compound, with more than one target, is again only
rows. Until Stage 4b its second target was `E_ITGAVB3_5`, which owner decision 7
makes unapprovable in v0.6.0. Not a claim about any reagent.
