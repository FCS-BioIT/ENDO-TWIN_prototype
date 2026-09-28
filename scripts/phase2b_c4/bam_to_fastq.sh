#!/usr/bin/env bash
# Amendment 18: reconstruct the original FASTQs of one ENA fastq_pre_barcodes BAM.
#   R1 = CR+RX (28), qual CY+QX   R2 = SEQ/QUAL (91)   I1 = BC/QT (8)
#   names from `on` (text before '@'), comments from `on` after '@'
# Fails closed on any record lacking a tag or with a wrong length.
set -euo pipefail
BAM=$1; LIB=$2; OUT=$3
S=/home/francois/Tools/cellranger-9.0.1/lib/bin/samtools
mkdir -p "$OUT"
R1="$OUT/${LIB}_S1_L001_R1_001.fastq.gz"; R2="$OUT/${LIB}_S1_L001_R2_001.fastq.gz"
I1="$OUT/${LIB}_S1_L001_I1_001.fastq.gz"
"$S" view -@ 4 "$BAM" | awk -F'\t' -v r1="pigz -p 4 > $R1" -v r2="pigz -p 4 > $R2" -v i1="pigz -p 4 > $I1" '
{
  cr=cy=rx=qx=bc=qt=on=""
  for (i = 12; i <= NF; i++) {
    t = substr($i, 1, 2); v = substr($i, 6)
    if (t == "CR") cr = v; else if (t == "CY") cy = v; else if (t == "RX") rx = v
    else if (t == "QX") qx = v; else if (t == "BC") bc = v; else if (t == "QT") qt = v
    else if (t == "on") on = v
  }
  if (and($2, 4) == 0 || length(cr) != 16 || length(cy) != 16 || length(rx) != 12 ||
      length(qx) != 12 || length(bc) != 8 || length(qt) != 8 || length($10) != 91 ||
      length($11) != 91 || on == "" || index(on, "@") == 0) {
    printf "VIOLATION at record %d\n", NR > "/dev/stderr"; bad = 1; exit 3
  }
  a = index(on, "@"); name = substr(on, 1, a - 1); idx = substr(on, a + 1)
  sub(/^[0-9]:/, "", idx)                     # comment tail after the read number
  print "@" name " 1:" idx "\n" cr rx "\n+\n" cy qx | r1
  print "@" name " 2:" idx "\n" $10 "\n+\n" $11 | r2
  print "@" name " 1:" idx "\n" bc "\n+\n" qt | i1
  n++
}
END { close(r1); close(r2); close(i1); if (!bad) print n > "/dev/stdout" }' > "$OUT/${LIB}.read_count"
echo "reads $(cat "$OUT/${LIB}.read_count")"
