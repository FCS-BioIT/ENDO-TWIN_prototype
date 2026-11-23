#!/usr/bin/env bash
# Phase 2B C4 step 2: one candidate stack (Cell Ranger version) on ADOC SZ09TE_CNT.
# Amendments 13/14: that version's own mkref reference (built beforehand), count at
# the version's defaults with --create-bam=false only; then the pinned ADOC
# decontX route (convert_to_h5.R -> decontx_remove_background.R at 1f15801) and
# whole-matrix comparisons (compare_stack.R, value-blind: aggregates only).
set -euo pipefail
VER=$1                                   # e.g. 9.0.1
W=/scratch/dt_adoc_phase2b
CR=/home/francois/Tools/cellranger-$VER/cellranger
REF=$W/ref/cr${VER}_a14/GRCh38_gencode_v47
RS=$W/envs/decontx/bin/Rscript
PIPE=$W/src/single-cell-ADOC
DEP=$W/adoc/deposit
OUT=$W/adoc/stack_cr$VER
S=SZ09TE_CNT

free=$(df -BG --output=avail /scratch | tail -1 | tr -dc 0-9)
[ "$free" -ge 300 ] || { echo "ABORT: scratch ${free}G < 300G"; exit 2; }
mkdir -p "$OUT/fastq" "$OUT/input/matrix" "$OUT/h5" "$OUT/decontx" "$OUT/compare"

# Cell Ranger's bcl2fastq file-name convention; symlinks to the md5-verified ENA files.
for r in I1 I2 R1 R2; do
  ln -sfn "$W/adoc/fastq/${S}_${r}.fastq.gz" "$OUT/fastq/${S}_S1_L001_${r}_001.fastq.gz"
done

cd "$OUT"
COUNT=("$CR" count --id="$S" --transcriptome="$REF" --fastqs="$OUT/fastq" --sample="$S" --create-bam=false --disable-ui)
printf '%q ' "${COUNT[@]}" > COUNT_COMMAND.txt; echo >> COUNT_COMMAND.txt
"${COUNT[@]}"

O="$OUT/$S/outs"
# (1) feature identity (amendment 13), (2) raw and (3) filtered whole-matrix triples
"$RS" "$W/src/compare_stack.R" features "$O/filtered_feature_bc_matrix/features.tsv.gz" \
  "$W/ref/v47_chr_genes.tsv" "$W/adoc/all_feature_bc_matrix_features.tsv" \
  "$OUT/compare/feature_names.tsv" "$OUT/compare/features.json"
"$RS" "$W/src/compare_stack.R" counts "$O/raw_feature_bc_matrix" \
  "$DEP/${S}_raw_feature_bc_matrix_matrix.mtx" "$DEP/${S}_raw_feature_bc_matrix_barcodes.tsv" \
  "$OUT/compare/raw.json"
"$RS" "$W/src/compare_stack.R" counts "$O/filtered_feature_bc_matrix" \
  "$DEP/${S}_filtered_feature_bc_matrix_matrix.mtx" "$DEP/${S}_filtered_feature_bc_matrix_barcodes.tsv" \
  "$OUT/compare/filtered.json"

# (4) the pinned decontX route on OUR matrices, exactly as the ADOC Snakefile does
for t in raw filtered; do
  zcat "$O/${t}_feature_bc_matrix/matrix.mtx.gz" > "input/matrix/${S}_${t}_feature_bc_matrix_matrix.mtx"
  zcat "$O/${t}_feature_bc_matrix/barcodes.tsv.gz" > "input/matrix/${S}_${t}_feature_bc_matrix_barcodes.tsv"
  cp "$OUT/compare/feature_names.tsv" "input/matrix/${S}_${t}_feature_bc_matrix_features.tsv"
  "$RS" "$PIPE/src/upstream/convert_to_h5.R" \
    --matrix "input/matrix/${S}_${t}_feature_bc_matrix_matrix.mtx" \
    --features "input/matrix/${S}_${t}_feature_bc_matrix_features.tsv" \
    --barcodes "input/matrix/${S}_${t}_feature_bc_matrix_barcodes.tsv" \
    --output "h5/${S}_${t}.h5"
done
"$RS" "$PIPE/src/upstream/decontx_remove_background.R" \
  --input "h5/${S}_filtered.h5" --input_raw "h5/${S}_raw.h5" \
  --output_h5 "decontx/${S}_decontx.h5" --output_csv "decontx/${S}_decontx_metrics.csv" \
  > decontx/decontx.log 2>&1
"$RS" "$W/src/compare_stack.R" decontx "decontx/${S}_decontx.h5" \
  "$DEP/${S}_decontx_feature_bc_matrix_filtered_matrix.mtx" \
  "$DEP/${S}_filtered_and_decontx_feature_bc_matrix_filtered_barcodes.tsv" \
  "$OUT/compare/decontx.json"

sha256sum "$O"/raw_feature_bc_matrix/* "$O"/filtered_feature_bc_matrix/* "$O"/metrics_summary.csv \
  "$O"/raw_feature_bc_matrix.h5 "$O"/filtered_feature_bc_matrix.h5 decontx/* h5/* compare/*.json \
  > "$OUT/outputs.sha256"
echo "STACK_DONE $VER"
