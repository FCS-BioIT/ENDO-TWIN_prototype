# Post-closure corrections to the scRNA observation map

`config/scrna_observation_map.tsv` cannot be edited. Phase 2B's closure audit
freezes `config/` and `docs/scrna/`, and `dt_adoc.closure_replay` holds the live
tree to that freeze. The node-support pre-registration also fixes the map's
feature lists as the only genes its audit reads. An error found after both
freezes is therefore corrected here, as a declared layer that **live** consumers
apply. Frozen and closed analyses never see it.

Code: `src/dt_adoc/scrna/observation_corrections.py`.
Declared corrections: `config/scrna_observation_map_corrections.tsv`. This file
is listed in `closure_replay.POST_CLOSURE_FILES`, and the frozen map is not
edited.

## OC-001 / OC-002: `E_PC6` is PCSK5, not PCSK6

| | symbol | HGNC | Ensembl | note |
|---|---|---|---|---|
| what `E_PC6` means | PCSK5 | HGNC:8747 | ENSG00000099139 | aliases PC5, **PC6**, SPC6 |
| what the frozen map measured | PCSK6 | HGNC:8569 | ENSG00000140479 | formerly PACE4, a different convertase |

HGNC records were retrieved on 2026-10-13. The model's node dictionary and
`config/node_entity_map.tsv` already named PCSK5. Only the observation map, and
everything generated from it, named PCSK6.

**What the deposited object shows.** Both symbols are separate features. The
other PCSK-family features are PCSK1, PCSK1N, PCSK2, PCSK4, PCSK6-AS1, PCSK7 and
PCSK9, so no alias collides. The object carries no gene-identifier column, so
identity rests on the symbol and the HGNC records above.

**What changes in the evidence.** In epithelium, PCSK6 was detected in 0.7–5.1 %
of cells and PCSK5 is detected in 50–67 %, at a pseudobulk share 70 to 1,440
times larger. Against the predicted CNT→HT switch (OFF→ON), PCSK5 goes down in
SZ09 and SZ25 and is flat within two-fold in SZ10. The RNA-endpoint verdict for
`E_PC6` remains `mixed_or_inconclusive`
(`docs/rna_endpoint_concordance/report.md`). None of this observes PC6 activity
or DAG1 cleavage.

## The files

| file | what it is | how it is made |
|---|---|---|
| `scrna_observation_map_corrected.tsv` | the frozen map with the declared corrections applied, byte-identical elsewhere | `python -m dt_adoc.scrna.observation_corrections map` |
| `pc6_pcsk5/evidence.tsv` | per-unit `gene:PCSK5` and `node:E_PC6` rows, in the frozen audit's columns and format | `extract --rds … --rscript …` or `derive --from-per-cell …` |
| `pc6_pcsk5/findings.json` | identity check, reproduction check, supersession list, provenance | same |

Run these with `PYTHONPATH=src`. The per-cell table holds sample-level metadata,
so it stays outside the repository (default
`~/ext/dt_adoc_node_support/pc6_pcsk5_per_cell.tsv`, with an extraction sidecar
binding it to the object's SHA-256). The extraction used R 4.5.3 and
SeuratObject 5.4.0, the versions the external-data manifest records.

**Post-hoc, not pre-registered.** The PCSK5 values were extracted on
2026-10-13, after the node-support audit, and are labelled
`post_hoc_not_preregistered`. No threshold, rule or statistic is new. The
extraction runs the frozen R script verbatim and the frozen
`node_support.unit_statistics` unchanged. It also re-derives PCSK6 and **refuses
to write unless every PCSK6 row reproduces `docs/scrna/node_support_evidence.tsv`
byte for byte** (17 units). The bootstrap resamples cells by unit ordinal,
independent of which genes are present, so that check also covers the PCSK5
rows.

## Who reads what

| consumer | reads | why |
|---|---|---|
| U6 component map (`docs/u6_semantics/component_map.tsv`), and through it the perturbation-cascade marker annotations | corrected map | live description of what each node is read through |
| RNA-endpoint concordance (`docs/rna_endpoint_concordance/`) | corrected map and live evidence | live model-vs-data evaluation |
| node-support audit (`docs/scrna/node_support_*`) | frozen map | pre-registered: its inputs are fixed |
| Phase 2A personalization map (`docs/phase2a/`) | frozen map | closed phase, replayed from its closure snapshot |
| Stage 3 design, U8 rerank | frozen map | read only activation status and observability class, which no correction may change (enforced by test) |

**Live evidence** is the frozen `docs/scrna/node_support_evidence.tsv` with every
superseded row dropped (`gene:PCSK6`, and `node:E_PC6`, which was PCSK6) and the
correction's rows added (`observation_corrections.live_evidence_rows`). The
historical rows stay readable in the frozen file. They do not reach any live
result, and `tests/unit/test_observation_corrections.py` checks that no live
artifact carries PCSK6.

## Limits

- The node-support audit's own `AC01` verdict and its findings JSON still
  describe PCSK6. They are a pre-registered record and are not re-derived. The
  concordance table carries that frozen class verdict in
  `node_support_audit_class_verdict`, unchanged.
- `docs/scrna/node_rna_interpretability.tsv` (frozen node-support output) still
  names PCSK6 for `E_PC6`. It is history, like the rest of `docs/scrna/`.
- `docs/phase2a/node_personalization_map.tsv` still lists PCSK6. Phase 2A is
  closed, and this correction does not reopen it.
- PCSK5 RNA observes transcript abundance only. It does not observe PC6
  enzymatic activity, DAG1 cleavage, or the instant reversibility the network
  assumes.
- The values are on the decontX-corrected layer, with the same provisional
  absence caveat as the audit.
