#!/usr/bin/env bash
# Regenerate the four Stage C bundles under output/perturbations/ (gitignored).
# Deterministic: the same command writes byte-identical events, summaries and
# precedence tables. compare_historical.py checks them against
# bundle_manifest.json before computing anything.
set -euo pipefail
cd "$(dirname "$0")/../../.."
C=(pixi run perturb-cascade)
"${C[@]}" --spec perturbations/progestin_withdrawal.yaml --n 2000 --seed 20261008 --workers 8 --overwrite --run-id progestin_withdrawal__v060__n2000__seedA
"${C[@]}" --spec perturbations/progestin_withdrawal.yaml --n 2000 --seed 20261009 --workers 8 --overwrite --run-id progestin_withdrawal__v060__n2000__seedB
"${C[@]}" --spec perturbations/mifepristone_after_ht.yaml --n 2000 --seed 20261008 --workers 8 --overwrite --run-id mifepristone_after_ht__v060__n2000__seedA
"${C[@]}" --model adoc-literature-superset-v0.5.1 --start hormone_treated_maternal --set IN_PROGESTIN=0 \
  --name progestin_withdrawal_v051 --description "progestin (MPA) input withdrawal after hormone treatment" \
  --n 2000 --seed 20261008 --workers 8 --overwrite --run-id progestin_withdrawal__v051__n2000__seedA
