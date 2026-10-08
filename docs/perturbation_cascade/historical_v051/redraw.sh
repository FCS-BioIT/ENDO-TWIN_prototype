#!/usr/bin/env bash
# Redraw the historical figures from the archived run outputs, without
# re-simulating, into the gitignored output/progesterone_withdrawal_redraw/,
# then check fig3b and the analysis tables against ORIGINAL_SHA256SUMS.tsv.
# Verified byte-identical on 2026-10-08 at 1ef913e.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../.." && pwd)"
out="$root/output/progesterone_withdrawal_redraw"
mkdir -p "$out"
for f in run_metadata.json per_trajectory_events.tsv aggregate_final_state.tsv \
         withdrawal_vs_control_delta.tsv aggregate_timecourse.tsv analyze_p4_withdrawal.py; do
  cp "$here/$f" "$out/"
done
cd "$root"
pixi run -e default python -B "$out/analyze_p4_withdrawal.py" > "$out/redraw.log"
status=0
for f in fig3b_switch_positions_normalized.png switch_positions_normalized.tsv \
         switch_times.tsv pairwise_precedence.tsv analysis_summary.json; do
  want="$(awk -F'\t' -v f="$f" '$2 == f {print $1}' "$here/ORIGINAL_SHA256SUMS.tsv")"
  got="$(sha256sum "$out/$f" | cut -d' ' -f1)"
  if [ "$want" = "$got" ]; then echo "identical  $f"; else echo "DIFFERS    $f"; status=1; fi
done
exit "$status"
