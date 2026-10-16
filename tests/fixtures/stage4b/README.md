# Stage 4b G13 fixtures

Synthetic compounds for gate G13 of `docs/stage4b_direct_admission.md` §7.
Nothing here is evidence, a reagent or an approval. `admission.py` builds each
compound's four parts — evidence-register rows, the target declaration, one
approval per effect and the library rows — with every digest bound, and appends
them to a sandbox built by `tests/fixtures/o8_markerless/sandbox.py`. The
committed library, ledger, declarations and evidence register are never edited.

Rows built with `real_shape=True` carry a non-synthetic register status so that a
test can exercise the rules a real approval must meet (`system_grade`). They
exist only inside a temporary sandbox and say in every field that they are not
evidence.
