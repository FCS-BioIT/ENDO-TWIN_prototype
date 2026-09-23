"""Does AC01's divergence survive on raw UMIs, or is it a decontX artifact?

WHY THIS EXISTS. `AC01` is the only finding in the node-support audit that
licenses mechanistic reconsideration, and it rests on `E_PAEP` rising 5-10 fold
with the cocktail while `E_HBEGF` does not move. Both are read on the deposited
`counts` layer, which is decontX-corrected, and the registered pre-registration
Section 3.2 says that correction is condition-entangled: decontX is
cluster-dependent, the clusters are near-deterministic in condition, and the
caveat applies to PRESENCE as well as absence.

The finding document previously argued that `AC01` survives that caveat because
"a correction that depresses HT uniformly cannot make one member rise ten-fold
while its class-mates stay flat". **That reassurance assumed uniformity decontX
does not have** -- contamination estimates and corrected values differ by gene,
cell and cluster -- so the argument was not established. An external review
raised it as blocking. This module settles it by measurement instead.

WHAT IT DOES, AND WHAT IT DELIBERATELY DOES NOT. Exactly the pre-registered
comparison, on the raw layer:

- the same donors, the same broad epithelial compartment;
- raw `filtered_feature_bc_matrix` UMIs from the same accession, joined to the
  deposited object by barcode;
- **the same frozen movement rule** -- non-overlapping 95% within-donor
  bootstrap intervals on `f` AND `|log2 fold| >= LOG2_FOLD_MIN`, with the same
  one-transcript pseudocount, the same `BOOTSTRAP_B` and the same seed, reusing
  `node_support`'s own functions rather than reimplementing them;
- the same per-donor reporting, never pooled across donors.

**No new genes. No re-clustering. No re-annotation. No new threshold.** Only
`PAEP` and `HBEGF` are read, because they are the two members the conclusion
rests on and both are `direct_transcript` rows in the committed map. This is a
sensitivity analysis of one finding, not a second audit.

THE MATRICES ARE NOT LANDED. They are 200-540 MB each and two of 78,724 rows
are wanted, so each is streamed, reduced and discarded, with the sha256 computed
over the stream as it goes -- the reduced table is bound to the bytes it came
from without 2.4 GB ever reaching disk. That discipline is taken from
`klf12_raw_umi.py`, which established the route.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import tempfile
from collections.abc import Iterable, Iterator
from pathlib import Path

import numpy as np

from dt_adoc.scrna import node_support as N
from dt_adoc.scrna import node_support_contract as C

ACCESSION = "E-MTAB-15842"
ACCESSION_FILES_URL = (
    "https://ftp.ebi.ac.uk/pub/databases/biostudies/E-MTAB-/842/E-MTAB-15842/Files"
)

#: The two AC01 members the conclusion rests on. Both are `direct_transcript`
#: in the committed map, so neither is a proxy standing in for a state.
#: `E_ITGAVB3_5` is deliberately NOT here: it is an abundance proxy that the map
#: says cannot establish the functional integrin state, so it was never
#: load-bearing and adding it would be widening the question.
GENES: tuple[str, ...] = ("PAEP", "HBEGF")

SAMPLES: tuple[str, ...] = (
    "SZ09TE_CNT",
    "SZ09TE_HT",
    "SZ10TE_CNT",
    "SZ10TE_HT",
    "SZ25TE_CNT",
    "SZ25TE_HT",
)

COMPARTMENT = "epithelium"

_R_EXTRACT_CELLS = """
suppressPackageStartupMessages(library(SeuratObject))
args <- commandArgs(trailingOnly = TRUE)
obj <- readRDS(args[1])
md <- obj@meta.data
df <- data.frame(
  cell = colnames(obj),
  sample_id = as.character(md$sample_id),
  celltype_v2 = as.character(md$celltype_v2),
  stringsAsFactors = FALSE
)
write.table(df, args[2], sep = "\\t", quote = FALSE, row.names = FALSE)
cat(sprintf("r_version\\t%s\\n", R.version.string), file = stderr())
cat(sprintf("seuratobject_version\\t%s\\n",
            as.character(packageVersion("SeuratObject"))), file = stderr())
"""


class RawSensitivityError(RuntimeError):
    """The sensitivity cannot be computed from what it was given."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def feature_rows(features: Path, genes: Iterable[str]) -> dict[str, int]:
    """One-based row index of each gene in the accession's feature list."""
    wanted = set(genes)
    found: dict[str, int] = {}
    with features.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            symbol = line.strip()
            if symbol in wanted:
                found[symbol] = index
    missing = wanted - set(found)
    if missing:
        raise RawSensitivityError(f"{sorted(missing)} not in {features}")
    return found


def reduce_matrix(
    lines: Iterable[str], rows: dict[str, int], columns: int
) -> tuple[dict[str, list[int]], list[int]]:
    """Reduce a MatrixMarket stream to the wanted rows plus column totals.

    Returns per-gene counts in column order and the per-column total UMI, which
    is the denominator of `f` on this layer exactly as `depth_counts` is on the
    corrected one.
    """
    by_row = {row: gene for gene, row in rows.items()}
    counts: dict[str, dict[int, int]] = {gene: {} for gene in rows}
    total: dict[int, int] = {}
    header_seen = False
    for line in lines:
        if not line or line.startswith("%"):
            continue
        fields = line.split()
        if not header_seen:
            header_seen = True
            declared = int(fields[1])
            if declared != columns:
                raise RawSensitivityError(
                    f"matrix declares {declared} columns, barcodes file has {columns}"
                )
            continue
        r, c, value = int(fields[0]), int(fields[1]), int(fields[2])
        total[c] = total.get(c, 0) + value
        gene = by_row.get(r)
        if gene is not None:
            counts[gene][c] = value
    if not header_seen:
        raise RawSensitivityError("no MatrixMarket header in the stream")
    ordered = {
        gene: [counts[gene].get(c, 0) for c in range(1, columns + 1)] for gene in rows
    }
    return ordered, [total.get(c, 0) for c in range(1, columns + 1)]


def reduce_sample(
    sample: str, directory: Path, *, base_url: str = ACCESSION_FILES_URL
) -> dict[str, object]:
    """Stream one sample's matrix, reduce it to two rows, record what it read."""
    import urllib.request

    directory.mkdir(parents=True, exist_ok=True)
    features = directory / "all_feature_bc_matrix_features.tsv"
    if not features.is_file():
        with urllib.request.urlopen(
            f"{base_url}/all_feature_bc_matrix_features.tsv"
        ) as response:
            features.write_bytes(response.read())
    rows = feature_rows(features, GENES)

    barcodes_name = f"{sample}_filtered_feature_bc_matrix_barcodes.tsv"
    with urllib.request.urlopen(f"{base_url}/{barcodes_name}") as response:
        payload = response.read()
    barcodes = [line for line in payload.decode("utf-8").splitlines() if line.strip()]
    (directory / f"{sample}.barcodes.tsv").write_bytes(payload)

    matrix_name = f"{sample}_filtered_feature_bc_matrix_matrix.mtx"
    matrix_digest = hashlib.sha256()
    read_bytes = 0

    def _lines() -> Iterator[str]:
        nonlocal read_bytes
        remainder = b""
        with urllib.request.urlopen(f"{base_url}/{matrix_name}") as response:
            while True:
                block = response.read(1 << 20)
                if not block:
                    break
                matrix_digest.update(block)
                read_bytes += len(block)
                remainder += block
                *complete, remainder = remainder.split(b"\n")
                for line in complete:
                    yield line.decode("ascii")
        if remainder:
            yield remainder.decode("ascii")

    counts, total = reduce_matrix(_lines(), rows, len(barcodes))
    target = directory / f"{sample}.reduced.tsv"
    header = "barcode\t" + "\t".join(GENES) + "\ttotal_umi\n"
    target.write_text(
        header
        + "".join(
            f"{barcode}\t"
            + "\t".join(str(counts[g][i]) for g in GENES)
            + f"\t{total[i]}\n"
            for i, barcode in enumerate(barcodes)
        ),
        encoding="utf-8",
    )
    record = {
        "sample": sample,
        "genes": list(GENES),
        "feature_rows_one_based": rows,
        "matrix_file": matrix_name,
        "matrix_bytes": read_bytes,
        "matrix_sha256": matrix_digest.hexdigest(),
        "barcodes_file": barcodes_name,
        "barcodes_sha256": hashlib.sha256(payload).hexdigest(),
        "features_sha256": _sha256_file(features),
        "reduced_sha256": _sha256_file(target),
        "base_url": base_url,
        "n_barcodes": len(barcodes),
    }
    (directory / f"{sample}.reduction.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


CELLS_SIDECAR = ".extraction.json"


def extract_cells(rds: Path, destination: Path, *, rscript: str) -> dict[str, str]:
    """The object's cell names, which is what makes the barcode join possible.

    Writes a sidecar beside the table so a later run that does not re-extract
    can still say which R produced it and which object it came from.
    """
    with tempfile.NamedTemporaryFile(
        "w", suffix=".R", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(_R_EXTRACT_CELLS)
        script = handle.name
    try:
        completed = subprocess.run(
            [rscript, script, str(rds), str(destination)],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        Path(script).unlink(missing_ok=True)
    if completed.returncode != 0:
        raise RawSensitivityError(
            f"R extraction failed: {completed.stderr.strip()[:800]}"
        )
    versions = {}
    for line in completed.stderr.splitlines():
        key, _, value = line.partition("\t")
        if key in {"r_version", "seuratobject_version"}:
            versions[key] = value.strip()
    versions["rds_sha256"] = _sha256_file(rds)
    versions["cells_sha256"] = _sha256_file(destination)
    Path(str(destination) + CELLS_SIDECAR).write_text(
        json.dumps(versions, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return versions


def gather_provenance(work: Path, cells: Path, *, root: Path) -> dict[str, object]:
    """Every digest this artifact's numbers actually rest on.

    THE SIDECARS ARE THE POINT. `reduce_sample` hashes each matrix over the
    stream as it reads it, so the reduced table is bound to the bytes it came
    from without 2.4 GB landing on disk -- but an earlier revision computed all
    of that and then shipped a `provenance` block holding only the accession and
    the gene names, because the run that wrote the artifact had not itself done
    the download. A load-bearing artifact that records none of its sources is
    not reproducible, and both the review gate and an external reviewer raised
    it. The digests are now read back from disk on every run and their absence
    is an error, not a silently thinner artifact.

    RECORDING A DIGEST IS NOT THE SAME AS CHECKING IT. An earlier revision
    carried each sidecar's `reduced_sha256` into the artifact and never re-hashed
    the `<sample>.reduced.tsv` that `build_cells` then consumed, so an edited
    reduced table would have been read, used, and shipped under the digest of the
    file it replaced -- the artifact asserting a binding it had not verified.
    That is the same discipline already applied to the cell table below, and it
    is applied to every reduced table here.
    """
    reductions = []
    for sample in SAMPLES:
        sidecar = work / f"{sample}.reduction.json"
        if not sidecar.is_file():
            raise RawSensitivityError(
                f"{sidecar} is missing: this artifact would record no digest for "
                f"{sample}'s matrix. Re-run with --reduce."
            )
        record = json.loads(sidecar.read_text())
        reduced = work / f"{sample}.reduced.tsv"
        if not reduced.is_file():
            raise RawSensitivityError(
                f"{reduced} is missing, but {sidecar.name} records a digest for "
                "it. Re-run with --reduce."
            )
        observed = _sha256_file(reduced)
        declared = record.get("reduced_sha256", "")
        if observed != declared:
            raise RawSensitivityError(
                f"{reduced} has changed since it was reduced: it hashes to "
                f"{observed}, but {sidecar.name} records {declared}. The numbers "
                "in this artifact would not be the numbers its provenance "
                "describes."
            )
        reductions.append(record)

    cells_sidecar = Path(str(cells) + CELLS_SIDECAR)
    if not cells_sidecar.is_file():
        raise RawSensitivityError(
            f"{cells_sidecar} is missing: the cell table is not bound to the "
            "object it came from. Re-run with --rds."
        )
    extraction = json.loads(cells_sidecar.read_text())

    actual = _sha256_file(cells)
    if actual != extraction.get("cells_sha256"):
        raise RawSensitivityError(
            f"{cells} has changed since extraction: it hashes to {actual}, but "
            f"its sidecar records {extraction.get('cells_sha256')}"
        )
    declared = N.source_digest(root)
    if extraction.get("rds_sha256") != declared:
        raise RawSensitivityError(
            f"the cell table came from an object whose sha256 is "
            f"{extraction.get('rds_sha256')}, not the {declared} that "
            f"{N.ASSET_ID} declares"
        )
    return {
        "accession": ACCESSION,
        "asset_id": N.ASSET_ID,
        "genes": list(GENES),
        "source_binding": "verified",
        "extraction": extraction,
        "reductions": reductions,
        "matrix_bytes_total": sum(int(r["matrix_bytes"]) for r in reductions),
    }


def build_cells(
    cells_table: Path, reduced_dir: Path
) -> tuple[N.Cells, dict[str, object]]:
    """Join the raw matrices to the object's epithelial cells, by barcode.

    The object's cell names are `{sample_id}_{barcode}`, which is what makes the
    join possible at all. A cell the object carries but the filtered matrix does
    not is an inconsistency between two files of the same accession, so it is
    counted and reported rather than dropped silently.
    """
    wanted: dict[str, dict[str, str]] = {}
    with cells_table.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if C.COMPARTMENT_OF_LABEL.get(row["celltype_v2"]) != COMPARTMENT:
                continue
            # The object's cell names are `{sample_id}_{barcode}` and
            # `sample_id` ITSELF CONTAINS AN UNDERSCORE (`SZ09TE_CNT`), so
            # splitting on the first one yields `CNT_AAAC...` and matches
            # nothing. Strip the known prefix and refuse anything that does not
            # carry it, rather than guessing at a separator.
            prefix = f"{row['sample_id']}_"
            if not row["cell"].startswith(prefix):
                raise RawSensitivityError(
                    f"cell {row['cell']!r} does not carry the prefix {prefix!r}; "
                    "the barcode cannot be recovered and the join would be silent"
                )
            wanted.setdefault(row["sample_id"], {})[row["cell"][len(prefix) :]] = row[
                "celltype_v2"
            ]

    by_unit: dict[str, list[list[float]]] = {}
    depth_by_unit: dict[str, list[float]] = {}
    units: dict[str, N.Unit] = {}
    unmatched: dict[str, int] = {}
    label_counts: dict[str, int] = {}
    total_cells = 0

    for sample in SAMPLES:
        reduced = reduced_dir / f"{sample}.reduced.tsv"
        if not reduced.is_file():
            raise RawSensitivityError(f"{reduced} is missing; run --reduce first")
        donor, condition = N.parse_unit(sample)
        unit = N.Unit(donor, condition, COMPARTMENT)
        units.setdefault(unit.unit_id, unit)
        want = wanted.get(sample, {})
        seen = 0
        with reduced.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["barcode"] not in want:
                    continue
                seen += 1
                total_cells += 1
                label = want[row["barcode"]]
                label_counts[label] = label_counts.get(label, 0) + 1
                by_unit.setdefault(unit.unit_id, []).append(
                    [float(row[g]) for g in GENES]
                )
                depth_by_unit.setdefault(unit.unit_id, []).append(
                    float(row["total_umi"])
                )
        unmatched[sample] = len(want) - seen
        # AN EMPTY OR BADLY INCOMPLETE JOIN MUST NOT PRODUCE A VERDICT. The
        # first run of this module matched zero cells because of the barcode
        # parse above, and still reported
        # `divergence_reproduced_on_raw: false` -- which reads as the raw layer
        # REFUTING AC01 when in fact nothing had been compared. A sensitivity
        # analysis that can fail silently in the direction of its own
        # conclusion is worse than none.
        if seen == 0:
            raise RawSensitivityError(
                f"{sample}: the barcode join matched none of {len(want)} "
                "epithelial cells; refusing to report a comparison of nothing"
            )
        if seen < 0.99 * len(want):
            raise RawSensitivityError(
                f"{sample}: only {seen} of {len(want)} epithelial cells joined "
                "to the filtered matrix; the two files of this accession "
                "disagree by more than a rounding error"
            )

    cells = N.Cells(
        genes=GENES,
        by_unit={k: np.asarray(v, dtype=np.float64) for k, v in by_unit.items()},
        depth_by_unit={
            k: np.asarray(v, dtype=np.float64) for k, v in depth_by_unit.items()
        },
        units=units,
        absent_features=(),
        n_cells_object=total_cells,
        label_counts=label_counts,
    )
    return cells, {
        "cells_joined": total_cells,
        "cells_in_object_not_in_matrix": unmatched,
    }


def compare(cells: N.Cells) -> dict[str, object]:
    """Apply the frozen movement rule to the raw layer, per donor.

    `node_support`'s own `unit_statistics` and `gene_movement` are called, not
    reimplemented, so the raw and corrected results differ only in the numbers
    that went in.
    """
    ordered = sorted(cells.by_unit)
    stats = {
        unit_id: N.unit_statistics(cells, unit_id, ordinal)
        for ordinal, unit_id in enumerate(ordered)
    }
    result: dict[str, object] = {}
    for gene in GENES:
        per_donor = {
            donor: N.gene_movement(gene, donor, COMPARTMENT, stats)
            for donor in C.DONORS
        }
        detail = {}
        for donor in C.DONORS:
            cnt = stats.get(N.Unit(donor, "CNT", COMPARTMENT).unit_id)
            ht = stats.get(N.Unit(donor, "HT", COMPARTMENT).unit_id)
            if cnt is None or ht is None:
                continue
            key = f"gene:{gene}"
            pseudo_c = (cnt.f[key] * cnt.exposure + 1) / (cnt.exposure + 1)
            pseudo_h = (ht.f[key] * ht.exposure + 1) / (ht.exposure + 1)
            detail[donor] = {
                "f_cnt": cnt.f[key],
                "f_ht": ht.f[key],
                "f_cnt_ci": list(cnt.f_ci[key]),
                "f_ht_ci": list(ht.f_ci[key]),
                "d_cnt": cnt.d[key],
                "d_ht": ht.d[key],
                "log2_fold": math.log2(pseudo_h / pseudo_c),
                "intervals_separate": bool(
                    cnt.f_ci[key][1] < ht.f_ci[key][0]
                    or ht.f_ci[key][1] < cnt.f_ci[key][0]
                ),
                "n_cnt": cnt.n_cells,
                "n_ht": ht.n_cells,
            }
        result[gene] = {"per_donor": per_donor, "detail": detail}
    return result


def verdict(comparison: dict[str, object]) -> dict[str, object]:
    """Does the raw layer reproduce AC01's divergence?

    The corrected layer gave `E_PAEP` `moves_up` in 3/3 and `E_HBEGF`
    `no_material_move` in 3/3. Reproduction means the same two patterns under
    the same rule. Anything else is reported as what it is; this function makes
    no new decision rule and licenses nothing on its own.
    """
    paep = comparison["PAEP"]["per_donor"]  # type: ignore[index]
    hbegf = comparison["HBEGF"]["per_donor"]  # type: ignore[index]
    paep_up = sum(1 for call in paep.values() if call == "moves_up")
    hbegf_flat = sum(1 for call in hbegf.values() if call == "no_material_move")
    uninformative = [
        donor
        for calls in (paep, hbegf)
        for donor, call in calls.items()
        if call == "uninformative"
    ]
    if uninformative:
        # Never report "not reproduced" when the comparison did not happen.
        return {
            "corrected_layer": {
                "PAEP": "moves_up 3/3",
                "HBEGF": "no_material_move 3/3",
            },
            "raw_layer": {"PAEP": dict(paep), "HBEGF": dict(hbegf)},
            "divergence_reproduced_on_raw": None,
            "status": "not_evaluated",
            "uninformative_donors": sorted(set(uninformative)),
        }
    reproduced = paep_up == len(C.DONORS) and hbegf_flat == len(C.DONORS)
    return {
        "corrected_layer": {"PAEP": "moves_up 3/3", "HBEGF": "no_material_move 3/3"},
        "raw_layer": {"PAEP": dict(paep), "HBEGF": dict(hbegf)},
        "paep_moves_up_donors": paep_up,
        "hbegf_no_material_move_donors": hbegf_flat,
        "divergence_reproduced_on_raw": reproduced,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reduce", action="store_true", help="stream and reduce the matrices"
    )
    parser.add_argument("--rds", type=Path, help="extract the object's cell names")
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument(
        "--work",
        type=Path,
        default=Path.home() / "ext/dt_adoc_node_support/raw",
        help="where reduced tables live; outside the repository",
    )
    parser.add_argument("--cells", type=Path)
    parser.add_argument("--root", type=Path, default=N.REPO)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    args.work.mkdir(parents=True, exist_ok=True)

    if args.rds is not None:
        destination = args.cells or (args.work / "cells.tsv")
        extract_cells(args.rds, destination, rscript=args.rscript)
        args.cells = destination

    if args.reduce:
        for sample in SAMPLES:
            reduce_sample(sample, args.work)

    if args.cells is None:
        args.cells = args.work / "cells.tsv"
    if not args.cells.is_file():
        raise RawSensitivityError(f"{args.cells} is missing; run --rds first")

    # Read back from disk rather than from whatever this invocation happened to
    # do, so a re-derivation records the same digests as the run that fetched.
    provenance = gather_provenance(args.work, args.cells, root=args.root)
    cells, join = build_cells(args.cells, args.work)
    comparison = compare(cells)
    payload = {
        "layer": "raw filtered_feature_bc_matrix UMIs",
        "question": (
            "Does AC01's E_PAEP / E_HBEGF divergence survive on raw counts, or is "
            "it a decontX artifact? Section 3.2 of the registered "
            "pre-registration says the correction is condition-entangled and "
            "that the caveat applies to presence as well as absence."
        ),
        "rule": {
            "log2_fold_min": C.LOG2_FOLD_MIN,
            "bootstrap_b": C.BOOTSTRAP_B,
            "bootstrap_seed": C.BOOTSTRAP_SEED,
            "bootstrap_alpha": C.BOOTSTRAP_ALPHA,
            "note": (
                "the frozen rule, applied by node_support's own functions; no "
                "new genes, no re-clustering, no new threshold"
            ),
        },
        "join": join,
        "comparison": comparison,
        "verdict": verdict(comparison),
        "provenance": provenance,
    }
    if args.no_write:
        print(json.dumps(payload, indent=1, sort_keys=True, default=str))
        return 0
    target = args.root / "docs/scrna/node_support_raw_sensitivity.json"
    target.write_text(
        json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {target.relative_to(args.root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
