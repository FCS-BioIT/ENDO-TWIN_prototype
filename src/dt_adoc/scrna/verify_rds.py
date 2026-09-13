"""Re-verify the deposited ADOC single-cell object against its recorded facts.

The structural verification behind `docs/scrna_observability.md` was performed
once, by hand, with R and SeuratObject. That is not good enough for a claim the
rest of the map rests on: a reader cannot check it and a later maintainer cannot
re-run it. This turns it into a script.

WHAT IT CHECKS, against `config/external_data_manifest.tsv` and the expectations
below: size, sha256, cell and feature counts, assay layers, meta.data columns,
per-sample counts, per-population counts, and that the `counts` layer is NOT raw
integer UMIs.

WHAT IT DOES NOT DO. It never downloads: the object is 2.9 GB and the manifest
records where it lives. Point it at a local copy. The test suite therefore does
NOT run the structural half -- it runs the parts that need no RDS (manifest
agreement, expectation self-consistency) and skips the rest unless a path is
given. `AGENTS.md` forbids loading the multi-gigabyte object merely to test
runtime availability, and an unavailable R/Seurat gate must be REPORTED rather
than its result inferred.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ASSET_ID = "EXT-SCRNA-001"

EXPECTED_CELLS = 28212
EXPECTED_FEATURES = 78724
EXPECTED_LAYERS = ("counts", "data", "scale.data")
EXPECTED_META_COLUMNS = (
    "sample_id",
    "orig.ident",
    "celltype_v2",
    "RNA_snn_res.0.5",
    "RNA_snn_res.0.6",
)
EXPECTED_SAMPLES = {
    "SZ09TE_CNT": 5605,
    "SZ09TE_HT": 3408,
    "SZ10TE_CNT": 6412,
    "SZ10TE_HT": 4253,
    "SZ25TE_CNT": 6742,
    "SZ25TE_HT": 1792,
}
EXPECTED_POPULATIONS = {
    "Luminal-like epithelium": 8857,
    "HT epithelium I": 4197,
    "Stroma": 4181,
    "Cycling epithelium": 3922,
    "HT epithelium II": 3465,
    "HT stroma": 3225,
    "Myofibroblast": 365,
}

#: Emits plain `kind\tkey\tvalue` lines rather than JSON, so the only R
#: dependency is SeuratObject. Requiring jsonlite would make the one check a
#: reader is most likely to want to re-run harder to run.
_R_SCRIPT = """
suppressPackageStartupMessages(library(SeuratObject))
obj <- readRDS(commandArgs(trailingOnly = TRUE)[1])
md <- obj@meta.data
emit <- function(kind, key, value) cat(sprintf("%s\\t%s\\t%s\\n", kind, key, value))
emit("scalar", "cells", ncol(obj))
emit("scalar", "features", nrow(obj))
for (l in SeuratObject::Layers(obj[["RNA"]])) emit("layer", l, 1)
for (c in colnames(md)) emit("meta", c, 1)
ts <- table(md$sample_id)
for (n in names(ts)) emit("sample", n, ts[[n]])
tp <- table(md$celltype_v2)
for (n in names(tp)) emit("population", n, tp[[n]])
cm <- SeuratObject::LayerData(obj[["RNA"]], layer = "counts")
n <- min(2000L, nrow(cm)); m <- min(2000L, ncol(cm))
sub <- cm[seq_len(n), seq_len(m)]
emit("scalar", "counts_all_integer", as.integer(all(sub@x == floor(sub@x))))
"""


def _parse(stdout: str) -> dict[str, dict[str, int]]:
    parsed: dict[str, dict[str, int]] = {}
    for line in stdout.splitlines():
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 3:
            continue
        kind, key, value = parts
        try:
            parsed.setdefault(kind, {})[key] = int(value)
        except ValueError:
            continue
    return parsed


def manifest_row(root: Path) -> dict[str, str]:
    path = root / "config" / "external_data_manifest.tsv"
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["asset_id"] == ASSET_ID:
                return row
    raise KeyError(f"{ASSET_ID} is not in {path}")


def expectation_totals() -> tuple[int, int]:
    """Sample and population counts must each total the cell count."""
    return sum(EXPECTED_SAMPLES.values()), sum(EXPECTED_POPULATIONS.values())


def digest(path: Path, chunk: int = 1 << 24) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            sha.update(block)
    return sha.hexdigest()


def check_bytes(path: Path, row: dict[str, str]) -> list[str]:
    problems: list[str] = []
    size = path.stat().st_size
    if size != int(row["size_bytes"]):
        problems.append(f"size {size} != manifest {row['size_bytes']}")
    actual = digest(path)
    if actual != row["sha256"]:
        problems.append(f"sha256 {actual} != manifest {row['sha256']}")
    return problems


def check_structure(path: Path, rscript: str) -> list[str]:
    """Parse the object with R and compare against the recorded facts."""
    # Written to a file rather than passed with `-e`: with `-e` the `--args`
    # separator itself lands in commandArgs(trailingOnly = TRUE) and R tries to
    # open it as the RDS.
    with tempfile.NamedTemporaryFile(
        "w", suffix=".R", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(_R_SCRIPT)
        script_path = handle.name
    try:
        completed = subprocess.run(
            [rscript, script_path, str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        Path(script_path).unlink(missing_ok=True)
    if completed.returncode != 0:
        return [f"R failed: {completed.stderr.strip()[:400]}"]
    seen = _parse(completed.stdout)
    scalar = seen.get("scalar", {})
    problems: list[str] = []
    if scalar.get("cells") != EXPECTED_CELLS:
        problems.append(f"cells {scalar.get('cells')} != {EXPECTED_CELLS}")
    if scalar.get("features") != EXPECTED_FEATURES:
        problems.append(f"features {scalar.get('features')} != {EXPECTED_FEATURES}")
    for layer in EXPECTED_LAYERS:
        if layer not in seen.get("layer", {}):
            problems.append(f"missing assay layer {layer!r}")
    for column in EXPECTED_META_COLUMNS:
        if column not in seen.get("meta", {}):
            problems.append(f"missing meta.data column {column!r}")
    for name, count in EXPECTED_SAMPLES.items():
        if seen.get("sample", {}).get(name) != count:
            problems.append(
                f"sample {name}: {seen.get('sample', {}).get(name)} != {count}"
            )
    for name, count in EXPECTED_POPULATIONS.items():
        if seen.get("population", {}).get(name) != count:
            problems.append(
                f"population {name}: {seen.get('population', {}).get(name)} != {count}"
            )
    # The finding that changes downstream method choice: this layer is decontX
    # output, not raw UMIs. If it ever becomes integral the map's warning is
    # wrong and must be revisited.
    if scalar.get("counts_all_integer") == 1:
        problems.append(
            "the counts layer is integral, so it may now be raw UMIs; the "
            "decontX warning in docs/scrna_observability.md must be re-derived"
        )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rds", type=Path, help="local copy of seurat_object.rds")
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--skip-structure", action="store_true")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args(argv)

    row = manifest_row(args.root)
    problems = check_bytes(args.rds, row)
    if args.skip_structure:
        print("structural check SKIPPED (requested)")
    else:
        problems += check_structure(args.rds, args.rscript)
    for problem in problems:
        print(f"MISMATCH: {problem}", file=sys.stderr)
    print("OK" if not problems else f"{len(problems)} mismatch(es)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
