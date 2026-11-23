#!/usr/bin/env bash
# Phase 2B C4 step 3 (amendments 16-18): E-MTAB-10283 XAV939 + E+P day-6 libraries,
# one at a time: ENA-md5-verified BAM -> reconstructed FASTQs -> pinned count.
# Value-blind: no expression value is read here.
set -euo pipefail
W=/scratch/dt_adoc_phase2b
CR=/home/francois/Tools/cellranger-9.0.1/cellranger
REF=$W/ref/cr9.0.1_a14/GRCh38_gencode_v47
declare -A EXPECT=([WSSS_END9397531]=400248540 [WSSS_END9397535]=387051041)

for LIB in WSSS_END9397531 WSSS_END9397535; do
  free=$(df -BG --output=avail /scratch | tail -1 | tr -dc 0-9)
  [ "$free" -ge 300 ] || { echo "ABORT: scratch ${free}G < 300G"; exit 2; }
  BAM=$W/candidate/bam/$LIB.bam
  grep -q $'\tMATCH$' "$BAM.check" || { echo "ABORT: $LIB BAM md5/size not verified"; exit 4; }
  FQ=$W/candidate/fastq_$LIB
  $W/src/bam_to_fastq.sh "$BAM" "$LIB" "$FQ"
  n=$(cat "$FQ/$LIB.read_count")
  [ "$n" = "${EXPECT[$LIB]}" ] || { echo "ABORT: $LIB reads $n != ENA read_count ${EXPECT[$LIB]}"; exit 5; }
  ( cd "$FQ"; for f in *_001.fastq.gz; do
      echo -e "$f\tgz_sha256=$(sha256sum "$f" | cut -d' ' -f1)\tcontent_sha256=$(pigz -dc "$f" | sha256sum | cut -d' ' -f1)"
    done > FASTQ.sha256 )
  OUT=$W/candidate/count_$LIB; mkdir -p "$OUT"; cd "$OUT"
  COUNT=("$CR" count --id="$LIB" --transcriptome="$REF" --fastqs="$FQ" --sample="$LIB" --create-bam=false --disable-ui)
  printf '%q ' "${COUNT[@]}" > COUNT_COMMAND.txt; echo >> COUNT_COMMAND.txt
  "${COUNT[@]}"
  O=$OUT/$LIB/outs
  sha256sum "$O"/filtered_feature_bc_matrix/* "$O"/raw_feature_bc_matrix/* "$O"/metrics_summary.csv \
    "$O"/filtered_feature_bc_matrix.h5 "$O"/raw_feature_bc_matrix.h5 > "$OUT/outputs.sha256"
  echo "LIBRARY_DONE $LIB reads=$n"
done
echo "CANDIDATE_DONE"
