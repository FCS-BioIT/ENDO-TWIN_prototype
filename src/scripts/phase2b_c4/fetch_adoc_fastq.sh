#!/usr/bin/env bash
# Value-blind retrieval: ADOC SZ09TE_CNT (ENA ERR15772621) submitted FASTQs and the
# GENCODE v47 primary-assembly FASTA; each verified against its published MD5.
set -euo pipefail
W=/scratch/dt_adoc_phase2b
free=$(df -BG --output=avail /scratch | tail -1 | tr -dc 0-9); [ "$free" -ge 300 ] || { echo "ABORT: scratch ${free}G < 300G"; exit 2; }
cd $W/ref
wget -q -c https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_47/GRCh38.primary_assembly.genome.fa.gz
echo "fasta md5 $(md5sum GRCh38.primary_assembly.genome.fa.gz | cut -d' ' -f1) published $(grep ' GRCh38.primary_assembly.genome.fa.gz$' MD5SUMS | cut -d' ' -f1)"
cd $W/adoc/fastq
python3 - <<'PY' > manifest.tsv
import csv
r=list(csv.DictReader(open('/scratch/dt_adoc_phase2b/provenance/ERR15772621.filereport.tsv'),delimiter='\t'))[0]
for u,m,b in zip(r['submitted_ftp'].split(';'),r['submitted_md5'].split(';'),r['submitted_bytes'].split(';')):
    print(f"https://{u}\t{m}\t{b}")
PY
while IFS=$'\t' read -r url md5 bytes; do
  f=$(basename "$url")
  wget -q -c "$url" -O "$f"
  got=$(md5sum "$f" | cut -d' ' -f1); size=$(stat -c %s "$f")
  echo -e "$f\t$url\tpublished_md5=$md5\tlocal_md5=$got\tbytes=$size\tpublished_bytes=$bytes\t$([ "$got" = "$md5" ] && [ "$size" = "$bytes" ] && echo MATCH || echo MISMATCH)"
done < manifest.tsv | tee checksums.tsv
