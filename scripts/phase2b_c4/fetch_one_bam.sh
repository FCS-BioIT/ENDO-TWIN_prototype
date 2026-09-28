#!/usr/bin/env bash
# One submitted FASTQ: resumable download, then md5/size check against ENA's published values.
set -euo pipefail
url=$1; md5=$2; bytes=$3; f=$(basename "$url")
cd /scratch/dt_adoc_phase2b/candidate/bam
wget -q -c "$url" -O "$f"
got=$(md5sum "$f" | cut -d' ' -f1); size=$(stat -c %s "$f")
ok=$([ "$got" = "$md5" ] && [ "$size" = "$bytes" ] && echo MATCH || echo MISMATCH)
echo -e "$f\t$url\tpublished_md5=$md5\tlocal_md5=$got\tbytes=$size\tpublished_bytes=$bytes\t$ok" > "$f.check"
