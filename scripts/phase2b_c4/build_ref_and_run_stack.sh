#!/usr/bin/env bash
# Amendment 14 mkref for one Cell Ranger version, then run_stack.sh for that version.
set -euo pipefail
VER=$1
W=/scratch/dt_adoc_phase2b
free=$(df -BG --output=avail /scratch | tail -1 | tr -dc 0-9)
[ "$free" -ge 300 ] || { echo "ABORT: scratch ${free}G < 300G"; exit 2; }
cd $W/ref/cr${VER}_a14
MKREF=(/home/francois/Tools/cellranger-$VER/cellranger mkref --genome=GRCh38_gencode_v47
  --fasta=$W/ref/GRCh38.primary_assembly.genome.fa --genes=$W/ref/gencode.v47.annotation.gtf
  --nthreads=16 --memgb=64 --disable-ui)
printf '%q ' "${MKREF[@]}" > COMMAND.txt; echo >> COMMAND.txt
"${MKREF[@]}"
[ -f GRCh38_gencode_v47/reference.json ] || { echo "ABORT: mkref produced no reference"; exit 3; }
find GRCh38_gencode_v47 -type f -exec sha256sum {} + | sort -k2 > REFERENCE.sha256
echo "MKREF_DONE $VER"
exec $W/src/run_stack.sh "$VER"
