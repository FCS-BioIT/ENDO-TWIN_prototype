# Validation report

Date: 2026-07-25

## Passed

- Parsed `knowledge-base.yaml` with PyYAML.
- Verified all `REF-*` identifiers used by modules, nodes, edges, and
  perturbations exist in `references.tsv`.
- Verified all candidate edge endpoints resolve to a candidate node or an
  existing parent-model node.
- Verified consistent column counts in all literature TSV files.
- Focused repository tests passed:

```text
python -m pytest -q \
  tests/test_chatgpt_bundle.py \
  tests/unit/test_model_contracts.py \
  tests/unit/test_config_contracts.py \
  tests/unit/test_manifests.py

9 passed
```

## Deliberately not claimed

- The promoted standalone executable model is validated separately under
  `models/extended/adoc-literature-v0.2.0/`; this report covers only the
  literature package itself.
- The full harness tests cannot pass in this compact shared repository because
  the immutable source data listed in `config/data_manifest.tsv` and several
  machine-global Codex skills are absent. A focused run produced 12 passing
  tests and 3 expected environment/source-presence failures.
- No stochastic MaBoSS calibration or biological validation was performed.
