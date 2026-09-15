"""The pre-registered raw-UMI sensitivity for the KLF12 state question.

WHY THIS EXISTS. `klf12_state.py` runs the primary analysis on the deposited
`counts` layer, which is decontX-corrected and therefore neither integer nor
raw. The pre-registration allows one fallback, and only one:

    Sensitivity, only if the primary analysis is not already decisive: the raw
    per-sample `filtered_feature_bc_matrix` UMIs from the same accession,
    joined by barcode.

The primary analysis is NOT decisive, and this module exists because of the
specific way it fails. Its M1(a) verdict depends on which of three defensible
readings of one frozen sentence is applied, and `klf12_state` shows that all
three of them certify a population simulated with no latent state at all. A
criterion with no specificity cannot settle the question in either direction,
so the question is re-asked on the integer counts the correction was applied
to, where "how many molecules were captured" is not a matter of interpretation.

WHAT IS PRESERVED. Every constraint the pre-registration binds the primary
analysis with is binding here and is re-imposed from `klf12_state` rather than
restated: the epithelial population is the same four pre-declared `celltype_v2`
labels, the unit is donor x condition, nothing is re-clustered, no population is
defined by condition, cells are not replicates, and no model output may reach
any choice made here.

WHAT IS DIFFERENT, AND KEPT SEPARATE. The layer, and therefore the provenance.
Raw counts come from per-sample matrices with their own digests; the decontX
layer comes from the deposited RDS with its own. The two analyses write two
artifacts and neither inherits the other's binding.

WHAT THIS MODULE DELIBERATELY DOES NOT DO. It fits no latent-state model. It
reports counts, order statistics and a cross-layer cross-tab, and stops. An
earlier revision fitted a two-component gamma-Poisson mixture and compared it
to a single-rate model by BIC; that analysis has been removed, for reasons set
out beside `downsample` below. The short version: the likelihood is multimodal,
the reported statistic moved every time the search was hardened, and it was
never what the conclusion rested on. Nothing here needs an optimiser, which is
the property that makes the remaining numbers checkable by inspection.

LEAKAGE. As in `klf12_state`: this module imports nothing from
`dt_adoc.simulation`, `dt_adoc.concordance`, `dt_adoc.calibration`,
`dt_adoc.scoring` or `dt_adoc.perturbations`, and reads no model output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from dt_adoc.scrna.klf12_state import (
    EPITHELIAL_LABELS,
    GENE,
    Klf12StateError,
    _median,
    _quantile,
    parse_unit,
)

ASSET_ID = "EXT-SCRNA-001"
ACCESSION = "E-MTAB-15842"

#: The six per-sample matrices the pre-registration names. `filtered`, not
#: `raw`: the accession also deposits the unfiltered droplet matrices, and
#: those are not the cells the paper analysed.
SAMPLES: tuple[str, ...] = (
    "SZ09TE_CNT",
    "SZ09TE_HT",
    "SZ10TE_CNT",
    "SZ10TE_HT",
    "SZ25TE_CNT",
    "SZ25TE_HT",
)

#: Monte Carlo is pinned so a committed artifact does not move with a seed.
#: The only remaining random step is the binomial thinning used for depth
#: matching; nothing here is fitted or optimised.
SEED = 20260914
#: Thinning replicates per scheme. Cheap now that each one is a count rather
#: than a model fit.
DOWNSAMPLE_REPLICATES = 5


@dataclass(frozen=True)
class RawCell:
    """One epithelial cell's raw counts. Never an independent replicate."""

    sample_id: str
    celltype_v2: str
    barcode: str
    klf12: int
    depth: int
    nfeature: int
    corrected: float | None


def reduce_matrix(
    lines: Iterable[str], row: int, columns: int
) -> list[tuple[int, int, int]]:
    """Reduce a MatrixMarket coordinate stream to one row plus column totals.

    The six matrices are 200-540 MB each and only one of 78,724 rows is
    wanted, so they are streamed and discarded rather than landed. Returns one
    `(gene_count, total_umi, genes_detected)` triple per column, in column
    order, including the columns the stream never mentions.
    """
    gene: dict[int, int] = {}
    total: dict[int, int] = {}
    detected: dict[int, int] = {}
    header_seen = False
    declared = 0
    for line in lines:
        if not line or line.startswith("%"):
            continue
        fields = line.split()
        if not header_seen:
            header_seen = True
            declared = int(fields[1])
            if declared != columns:
                raise Klf12StateError(
                    f"matrix declares {declared} columns, barcodes file has {columns}"
                )
            continue
        r, c, value = int(fields[0]), int(fields[1]), int(fields[2])
        total[c] = total.get(c, 0) + value
        detected[c] = detected.get(c, 0) + 1
        if r == row:
            gene[c] = value
    if not header_seen:
        raise Klf12StateError("no MatrixMarket header found in the stream")
    return [
        (gene.get(c, 0), total.get(c, 0), detected.get(c, 0))
        for c in range(1, columns + 1)
    ]


def feature_row(features: Path, gene: str) -> int:
    """One-based row index of ``gene`` in the accession's feature list."""
    with features.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            if line.strip() == gene:
                return index
    raise Klf12StateError(f"{gene} is not in {features}")


_R_EXTRACT_CELLS = """
suppressPackageStartupMessages(library(SeuratObject))
args <- commandArgs(trailingOnly = TRUE)
obj <- readRDS(args[1])
md <- obj@meta.data
cm <- SeuratObject::LayerData(obj[["RNA"]], layer = "counts")
df <- data.frame(
  cell = colnames(obj),
  sample_id = as.character(md$sample_id),
  celltype_v2 = as.character(md$celltype_v2),
  depth_counts = as.numeric(Matrix::colSums(cm)),
  counts_KLF12 = as.numeric(cm["KLF12", ]),
  stringsAsFactors = FALSE
)
write.table(df, args[2], sep = "\\t", quote = FALSE, row.names = FALSE)
cat(sprintf("r_version\\t%s\\n", R.version.string), file = stderr())
cat(sprintf("seuratobject_version\\t%s\\n",
            as.character(packageVersion("SeuratObject"))), file = stderr())
"""


def extract_cells(rds: Path, destination: Path, *, rscript: str) -> dict[str, str]:
    """Extract the annotation parent AND record what it was extracted from.

    `klf12_state` extracts a per-cell table without cell names, because its own
    analysis never needs to join anything. This one does: the barcode join the
    pre-registration names requires `colnames(obj)`, and the cross-layer table
    requires the corrected value beside it.

    The sidecar is the point. An earlier revision built this table with an
    ad-hoc R script and no sidecar, and the binding check then refused it --
    correctly, and only after forty minutes of model fitting had already been
    spent. A table nothing binds could have come from any object, and the
    population it defines decides which cells every number here is computed
    over.
    """
    import subprocess
    import tempfile

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
        raise Klf12StateError(f"R extraction failed: {completed.stderr.strip()[:600]}")
    versions: dict[str, str] = {}
    for line in completed.stderr.splitlines():
        key, _, value = line.partition("\t")
        if key in {"r_version", "seuratobject_version"}:
            versions[key] = value.strip()
    record = dict(versions)
    record["rds_sha256"] = _sha256(rds)
    record["per_cell_sha256"] = _sha256(destination)
    from dt_adoc.scrna import klf12_state

    destination.with_name(
        destination.name + klf12_state.EXTRACTION_SIDECAR_SUFFIX
    ).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def read_cells(path: Path) -> dict[str, tuple[str, str, float | None]]:
    """Barcode -> (sample_id, celltype_v2, corrected KLF12) for every cell.

    The join key the pre-registration names. Cell names in the deposited
    object are `{sample_id}_{barcode}`, so the barcode is recoverable and the
    join needs nothing the object does not carry.

    The decontX-corrected value is carried too when the table has a
    `counts_KLF12` column, so the cross-layer comparison in the report is
    computed HERE, from the same hash-bound table the population comes from,
    rather than asserted from an ad-hoc check nothing pins.
    """
    out: dict[str, tuple[str, str, float | None]] = {}
    with path.open(encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        need = {"cell", "sample_id", "celltype_v2"}
        if not need.issubset(header):
            raise Klf12StateError(f"{path} lacks {sorted(need - set(header))}")
        index = {name: header.index(name) for name in header}
        corrected_at = index.get(f"counts_{GENE}")
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            cell = fields[index["cell"]]
            sample = fields[index["sample_id"]]
            if not cell.startswith(sample + "_"):
                raise Klf12StateError(
                    f"cell {cell!r} does not carry its sample prefix; the "
                    "barcode join the pre-registration names is not available"
                )
            corrected = (
                float(fields[corrected_at]) if corrected_at is not None else None
            )
            out[cell] = (sample, fields[index["celltype_v2"]], corrected)
    return out


# --- depth matching -------------------------------------------------------
#
# WHAT THIS MODULE NO LONGER DOES, and why it is recorded rather than deleted
# silently. Earlier revisions fitted a gamma-Poisson mixture to these counts
# and compared it against a single-rate model by BIC, to ask whether the raw
# layer showed structure beyond one homogeneous rate. That comparison has been
# REMOVED, and nothing in this module or in the report now depends on it.
#
# The reason is not that a reviewer objected to an implementation detail. It is
# that a two-component negative-binomial likelihood is multimodal, and three
# successive fitters -- plain EM, EM with coordinate ascent, EM with a diagonal
# pattern search -- were each demonstrated to return a non-maximum on some
# case, each time by an explicit better point. The reported BIC gain moved from
# +17.0 to +10.24 to +21.52 as the search was hardened, with no sign of having
# converged. A model-selection statistic whose value tracks how hard you looked
# is not evidence, and this one was never load-bearing: the conclusion rests on
# counts and order statistics that need no optimiser at all.
#
# Removing an unstable statistic is not the same as weakening a criterion to
# make a check pass. Nothing else moved to accommodate it, and the conclusion
# is unchanged and now rests only on what the counts directly show.


def downsample(
    counts: Sequence[int],
    depths: Sequence[float],
    target: float,
    rng: random.Random,
) -> tuple[list[int], list[float], int]:
    """Binomial thinning towards a common depth, with the depths it achieved.

    Returns `(thinned counts, EFFECTIVE depths, cells left unthinned)`.

    THE EFFECTIVE DEPTHS ARE THE POINT. A cell already at or below ``target``
    cannot be thinned up to it, so it keeps its own depth; an earlier revision
    thinned that way and then treated EVERY cell as sitting at the target,
    which misstated the depth of 8,401 of 20,441 epithelial cells (41.1%) in
    the one comparison whose purpose was to hold depth constant. The caller now
    receives `min(depth, target)` per cell and how many were never matched, and
    reports both.
    """
    out: list[int] = []
    effective: list[float] = []
    unmatched = 0
    for count, depth in zip(counts, depths):
        if depth <= target:
            unmatched += 1
            out.append(count)
            effective.append(depth)
            continue
        keep = target / depth
        out.append(sum(1 for _ in range(count) if rng.random() < keep))
        effective.append(target)
    return out, effective, unmatched


def read_reduced(directory: Path, sample: str) -> list[tuple[str, int, int, int]]:
    """One `(barcode, klf12, depth, nfeature)` row per cellranger-filtered cell."""
    barcodes = [
        line.strip()
        for line in (directory / f"{sample}.barcodes.tsv")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    rows: list[tuple[str, int, int, int]] = []
    for line in (
        (directory / f"{sample}.klf12.tsv").read_text(encoding="utf-8").splitlines()
    ):
        if not line.strip():
            continue
        column, klf12, depth, nfeature = (int(field) for field in line.split())
        rows.append((barcodes[column - 1], klf12, depth, nfeature))
    if len(rows) != len(barcodes):
        raise Klf12StateError(
            f"{sample}: {len(rows)} reduced columns against {len(barcodes)} barcodes"
        )
    return rows


def join(
    directory: Path, cells: dict[str, tuple[str, str, float | None]]
) -> list[RawCell]:
    """Join the raw matrices to the object's cells, by barcode, per sample.

    Every cell the object keeps must be present in its sample's filtered
    matrix. A cell that is not means the two are not the same processing run,
    and the sensitivity is refused rather than run on a partial join -- which
    would silently drop exactly the cells that differ.
    """
    by_sample: dict[str, dict[str, tuple[str, str, float | None]]] = {}
    for cell, (sample, label, corrected) in cells.items():
        by_sample.setdefault(sample, {})[cell[len(sample) + 1 :]] = (
            sample,
            label,
            corrected,
        )
    out: list[RawCell] = []
    for sample in SAMPLES:
        wanted = by_sample.get(sample, {})
        if not wanted:
            raise Klf12StateError(f"the object carries no cells for {sample}")
        reduced = {row[0]: row for row in read_reduced(directory, sample)}
        missing = [barcode for barcode in wanted if barcode not in reduced]
        if missing:
            raise Klf12StateError(
                f"{sample}: {len(missing)} of {len(wanted)} object cells are "
                f"absent from the deposited filtered matrix (e.g. {missing[0]}). "
                "The object and the matrices are not the same run; the raw "
                "sensitivity is refused rather than computed on a partial join."
            )
        for barcode, (_, label, corrected) in wanted.items():
            _, klf12, depth, nfeature = reduced[barcode]
            out.append(
                RawCell(sample, label, barcode, klf12, depth, nfeature, corrected)
            )
    return out


def cross_layer_table(cells: Sequence[RawCell]) -> dict[str, object]:
    """Corrected value against raw UMI, for the same cells, in one table.

    The report makes a claim that spans BOTH layers -- that a decontX value
    strictly between 0 and 1 is a cell which captured a molecule, not residue
    of a cell which captured none -- and that claim corrected a statement an
    earlier revision shipped as fact. A cross-layer claim needs a cross-layer
    artifact: computed here, from the same hash-bound per-cell table the
    population comes from and the same hash-bound matrices the counts come
    from, rather than left resting on a check nothing pins.
    """
    known = [cell for cell in cells if cell.corrected is not None]
    if not known:
        return {
            "available": False,
            "reason": "the per-cell table carries no corrected value",
        }
    sub_one = [cell for cell in known if 0.0 < float(cell.corrected or 0.0) < 1.0]
    positive = [cell for cell in known if float(cell.corrected or 0.0) > 0.0]
    raw_of_sub_one: dict[str, int] = {}
    for cell in sub_one:
        key = str(cell.klf12) if cell.klf12 <= 4 else "5+"
        raw_of_sub_one[key] = raw_of_sub_one.get(key, 0) + 1
    both_zero = sum(
        1 for cell in known if cell.klf12 == 0 and float(cell.corrected or 0.0) == 0.0
    )
    corrected_only = sum(
        1 for cell in known if cell.klf12 == 0 and float(cell.corrected or 0.0) > 0.0
    )
    raw_only = sum(
        1 for cell in known if cell.klf12 > 0 and float(cell.corrected or 0.0) == 0.0
    )
    both_positive = sum(
        1 for cell in known if cell.klf12 > 0 and float(cell.corrected or 0.0) > 0.0
    )
    ratios = [
        float(cell.corrected or 0.0) / cell.klf12 for cell in known if cell.klf12 > 0
    ]
    return {
        "available": True,
        "n_cells": len(known),
        "detection_agreement": {
            "both_zero": both_zero,
            "both_positive": both_positive,
            "corrected_positive_raw_zero": corrected_only,
            "raw_positive_corrected_zero": raw_only,
        },
        "decontx_never_creates_or_destroys_a_detection": (
            corrected_only == 0 and raw_only == 0
        ),
        # The single smallest corrected value in the object, with what it
        # actually captured. §1 uses this cell to argue that the support floor
        # of the decontX layer is set by how hard the correction pushed rather
        # than by an abundance, and that claim spans both layers, so the cell is
        # committed here instead of being quoted from an ad-hoc check.
        "minimum_corrected_cell": (
            {
                "corrected_value": min(float(c.corrected or 0.0) for c in positive),
                "raw_umi": next(
                    c.klf12
                    for c in positive
                    if float(c.corrected or 0.0)
                    == min(float(d.corrected or 0.0) for d in positive)
                ),
                "raw_depth": next(
                    c.depth
                    for c in positive
                    if float(c.corrected or 0.0)
                    == min(float(d.corrected or 0.0) for d in positive)
                ),
            }
            if positive
            else None
        ),
        "sub_one_corrected_cells": len(sub_one),
        "sub_one_corrected_by_raw_umi": raw_of_sub_one,
        "sub_one_corrected_cells_with_zero_raw_umi": raw_of_sub_one.get("0", 0),
        "corrected_over_raw_mean": (sum(ratios) / len(ratios)) if ratios else None,
    }


def derive(directory: Path, cells_table: Path) -> dict[str, object]:
    """The raw-UMI sensitivity, under the pre-registration's own constraints."""
    cells = read_cells(cells_table)
    joined = join(directory, cells)
    epithelial = [cell for cell in joined if cell.celltype_v2 in EPITHELIAL_LABELS]
    if not epithelial:
        raise Klf12StateError("the pre-declared population selects no cell")
    counts = [cell.klf12 for cell in epithelial]
    depths = [float(cell.depth) for cell in epithelial]
    detected = sorted(count for count in counts if count > 0)
    zero_fraction = 1.0 - len(detected) / len(counts)

    histogram = {
        str(value): sum(1 for count in counts if count == value) for value in range(11)
    }
    histogram[">10"] = sum(1 for count in counts if count > 10)

    per_unit: list[dict[str, object]] = []
    for unit in SAMPLES:
        members = [cell for cell in epithelial if cell.sample_id == unit]
        donor, condition = parse_unit(unit)
        unit_detected = [cell.klf12 for cell in members if cell.klf12 > 0]
        per_unit.append(
            {
                "unit_id": unit,
                "donor": donor,
                "condition": condition,
                "n_cells_epithelial": len(members),
                "median_raw_depth": _median([float(c.depth) for c in members]),
                "detection_fraction": len(unit_detected) / len(members),
                "median_detected_umi": (
                    _median([float(v) for v in unit_detected])
                    if unit_detected
                    else None
                ),
                "share_of_detected_at_one_umi": (
                    sum(1 for v in unit_detected if v == 1) / len(unit_detected)
                    if unit_detected
                    else None
                ),
            }
        )

    cross_layer = cross_layer_table(epithelial)

    # Depth matching, reported as COUNTS.
    #
    # THE PER-UNIT COMPARISON MUST USE THE MATCHED-ONLY SCHEME, and an earlier
    # revision of this function got that wrong in a way that mattered. Thinning
    # to a common target cannot raise a cell already below it, so the
    # "all cells at their effective depth" scheme leaves an unthinned
    # remainder -- and that remainder is wildly uneven between units. At this
    # target it is 50.0% of `SZ25TE_CNT` against 4.1% of `SZ25TE_HT`, because
    # the target IS `SZ25TE_CNT`'s median depth. Comparing units under that
    # scheme thins the deep unit almost completely and barely touches the
    # shallow one, which is the opposite of holding depth constant, and it was
    # used to publish a between-unit spread and a within-donor sign reversal as
    # though they were common-depth results.
    #
    # So the per-unit table is now built from `matched_cells_only` -- every
    # cell in it was above the target and was genuinely thinned to it -- and
    # the per-unit unmatched share is reported beside it so a reader can see
    # what each unit gave up to get there.
    rng = random.Random(SEED)
    target = min(float(row["median_raw_depth"]) for row in per_unit)
    matched: list[dict[str, object]] = []
    for _ in range(DOWNSAMPLE_REPLICATES):
        thinned, _effective, unmatched = downsample(counts, depths, target, rng)
        matched.append(
            {
                "scheme": "all_cells_at_their_effective_depth",
                "n_cells": len(thinned),
                "cells_left_unmatched": unmatched,
                "detection_fraction": sum(1 for v in thinned if v > 0) / len(thinned),
            }
        )

    eligible = [cell for cell in epithelial if float(cell.depth) > target]
    rng = random.Random(SEED + 1)
    by_unit: dict[str, list[float]] = {unit: [] for unit in SAMPLES}
    for _ in range(DOWNSAMPLE_REPLICATES):
        thinned, _effective, unmatched = downsample(
            [c.klf12 for c in eligible], [float(c.depth) for c in eligible], target, rng
        )
        matched.append(
            {
                "scheme": "matched_cells_only",
                "n_cells": len(thinned),
                "cells_left_unmatched": unmatched,
                "detection_fraction": sum(1 for v in thinned if v > 0) / len(thinned),
            }
        )
        for unit in SAMPLES:
            members = [
                value
                for value, cell in zip(thinned, eligible)
                if cell.sample_id == unit
            ]
            if members:
                by_unit[unit].append(sum(1 for v in members if v > 0) / len(members))

    depth_matched_detection = {
        unit: (_median(values) if values else None) for unit, values in by_unit.items()
    }
    unmatched_share = {}
    matched_cells = {}
    for unit in SAMPLES:
        members = [cell for cell in epithelial if cell.sample_id == unit]
        below = sum(1 for cell in members if float(cell.depth) <= target)
        unmatched_share[unit] = below / len(members) if members else None
        matched_cells[unit] = len(members) - below
    crude = {str(row["unit_id"]): float(row["detection_fraction"]) for row in per_unit}
    crude_spread = max(crude.values()) - min(crude.values())
    matched_values = [v for v in depth_matched_detection.values() if v is not None]
    matched_spread = (
        max(matched_values) - min(matched_values) if matched_values else None
    )

    return {
        "gene": GENE,
        "layer": "raw_filtered_feature_bc_matrix",
        "layer_note": (
            "integer UMIs from the per-sample cellranger-filtered matrices of "
            f"{ACCESSION}, joined to the deposited object by barcode. Not "
            "decontX-corrected; this is the sensitivity the pre-registration "
            "allows, not the primary analysis"
        ),
        "population_definition": list(EPITHELIAL_LABELS),
        "n_cells_joined": len(joined),
        "n_cells_epithelial": len(epithelial),
        "zero_fraction": zero_fraction,
        "detected_umi_histogram": histogram,
        "detected_umi_quantiles": {
            f"q{int(q * 100)}": _quantile([float(v) for v in detected], q)
            for q in (0.0, 0.25, 0.5, 0.75, 0.95, 1.0)
        },
        "share_of_detected_at_one_umi": (
            sum(1 for v in detected if v == 1) / len(detected) if detected else None
        ),
        "share_of_detected_at_or_below_two_umi": (
            sum(1 for v in detected if v <= 2) / len(detected) if detected else None
        ),
        "per_unit": per_unit,
        "cross_layer_corrected_vs_raw": cross_layer,
        "latent_state_model": (
            "NONE FITTED. An earlier revision compared a two-component "
            "gamma-Poisson mixture against a single-rate model by BIC. That "
            "comparison is removed: the likelihood is multimodal, three "
            "successive fitters each returned a demonstrable non-maximum, and "
            "the reported gain moved from +17.0 to +10.24 to +21.52 as the "
            "search was hardened without sign of converging. A model-selection "
            "statistic that tracks how hard one looked is not evidence. It was "
            "never load-bearing: every claim below is a count or an order "
            "statistic"
        ),
        "depth_matched_target_umi": target,
        "depth_matched_cells_below_target": sum(1 for d in depths if d <= target),
        "depth_matched_replicates": matched,
        "detection_fraction_crude_by_unit": crude,
        "detection_fraction_depth_matched_by_unit": depth_matched_detection,
        "detection_fraction_spread_crude": crude_spread,
        "detection_fraction_spread_depth_matched": matched_spread,
        "depth_matched_scheme_for_per_unit": "matched_cells_only",
        "depth_matched_cells_per_unit": matched_cells,
        "depth_matched_unmatched_share_per_unit": unmatched_share,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


#: Where the accession's per-sample matrices are served. Recorded rather than
#: inlined at the call site so the artifact names the exact origin of its bytes.
ACCESSION_FILES_URL = (
    "https://ftp.ebi.ac.uk/pub/databases/biostudies/E-MTAB-/842/E-MTAB-15842/Files"
)

REDUCTION_SIDECAR = ".reduction.json"


def reduce_sample(
    sample: str,
    directory: Path,
    *,
    base_url: str = ACCESSION_FILES_URL,
    gene: str = GENE,
) -> dict[str, object]:
    """Stream one sample's matrix, reduce it, and record what it read.

    The matrices are 200-540 MB each and only one of 78,724 rows is wanted, so
    they are streamed and discarded. What must NOT be discarded is the evidence
    of which bytes were read: the digest is computed over the stream as it goes,
    so the reduced table is bound to the source file it came from without ever
    landing 2.4 GB on disk. An earlier revision hashed only the reduced tables,
    which pinned this module's own output and nothing upstream of it.
    """
    import urllib.request

    directory.mkdir(parents=True, exist_ok=True)
    features = directory / "all_feature_bc_matrix_features.tsv"
    if not features.is_file():
        with urllib.request.urlopen(
            f"{base_url}/all_feature_bc_matrix_features.tsv"
        ) as response:
            features.write_bytes(response.read())
    row = feature_row(features, gene)

    barcodes_name = f"{sample}_filtered_feature_bc_matrix_barcodes.tsv"
    barcodes_path = directory / f"{sample}.barcodes.tsv"
    barcode_digest = hashlib.sha256()
    with urllib.request.urlopen(f"{base_url}/{barcodes_name}") as response:
        payload = response.read()
    barcode_digest.update(payload)
    barcodes_path.write_bytes(payload)
    barcodes = [line for line in payload.decode("utf-8").splitlines() if line.strip()]

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

    reduced = reduce_matrix(_lines(), row, len(barcodes))
    target = directory / f"{sample}.klf12.tsv"
    target.write_text(
        "".join(
            f"{index + 1}\t{gene_count}\t{total}\t{detected}\n"
            for index, (gene_count, total, detected) in enumerate(reduced)
        ),
        encoding="utf-8",
    )
    record = {
        "sample": sample,
        "gene": gene,
        "feature_row_one_based": row,
        "matrix_file": matrix_name,
        "matrix_bytes": read_bytes,
        "matrix_sha256": matrix_digest.hexdigest(),
        "barcodes_file": barcodes_name,
        "barcodes_bytes": len(payload),
        "barcodes_sha256": barcode_digest.hexdigest(),
        "features_sha256": _sha256(features),
        "reduced_sha256": _sha256(target),
        "base_url": base_url,
    }
    (directory / f"{sample}{REDUCTION_SIDECAR}").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


def reduction_provenance(
    directory: Path, cells_table: Path, *, root: Path
) -> dict[str, object]:
    """Bind BOTH parents of this artifact, and refuse if either is unbound.

    This analysis has two inputs and an earlier revision recorded only one. The
    raw COUNTS come from the accession's per-sample matrices; the POPULATION
    ASSIGNMENT -- which cell is epithelial, which donor and condition it belongs
    to -- comes from the deposited RDS by way of an extracted per-cell table.
    Recording digests of the reduced matrices alone left the half of the input
    that decides which cells are analysed entirely unbound, and identified the
    source matrices only by a wildcard.

    So: every source matrix is named with its byte count and the sha256 computed
    over the stream that produced the reduction, and the per-cell table is
    verified against `EXT-SCRNA-001`'s manifest digest through the same binding
    the decontX analysis uses.
    """
    reductions: dict[str, object] = {}
    for sample in SAMPLES:
        sidecar = directory / f"{sample}{REDUCTION_SIDECAR}"
        if not sidecar.is_file():
            raise Klf12StateError(
                f"{sample} has no reduction sidecar in {directory}: the reduced "
                "table is not bound to the accession file it came from. Re-run "
                "`--reduce` so the source digest is recorded, rather than "
                "publishing a reduction of unknown provenance."
            )
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        observed = _sha256(directory / f"{sample}.klf12.tsv")
        if observed != record.get("reduced_sha256"):
            raise Klf12StateError(
                f"{sample}.klf12.tsv has changed since it was reduced: it "
                f"hashes to {observed}, but its sidecar records "
                f"{record.get('reduced_sha256')}."
            )
        reductions[sample] = record

    # The annotation parent, bound exactly as klf12_state binds it.
    from dt_adoc.scrna import klf12_state

    recorded = klf12_state.extraction_provenance(cells_table)
    binding = klf12_state.verify_source_binding(cells_table, recorded, root=root)
    return {
        "accession": ACCESSION,
        "asset_id": ASSET_ID,
        "count_parent": {
            "source": f"{ACCESSION} per-sample filtered_feature_bc_matrix",
            "reduction_module_sha256": _sha256(Path(__file__)),
            "per_sample": reductions,
        },
        "annotation_parent": {
            "source": f"{ACCESSION} seurat_object.rds",
            "rds_sha256": binding["source_sha256_observed"],
            "per_cell_sha256": binding["per_cell_sha256"],
            "source_binding": binding["source_binding"],
            "r_version": recorded.get("r_version", ""),
            "seuratobject_version": recorded.get("seuratobject_version", ""),
            "note": (
                "the epithelial population, donor and condition come from this "
                "object; the counts come from the matrices above. Both are "
                "required to reconstruct any number in this artifact"
            ),
        },
    }


def write_findings(
    findings: dict[str, object], destination: Path, *, root: Path
) -> Path:
    reduced_dir = Path(str(findings.pop("_reduced_dir")))
    cells_table = Path(str(findings.pop("_cells_table")))
    payload = {
        "schema_version": "1.1",
        **findings,
        "provenance": {
            **reduction_provenance(reduced_dir, cells_table, root=root),
            "evidence_role": "same_dataset_internal",
            "claim_level": "sensitivity_not_primary_not_validation",
            "derivation_module_sha256": _sha256(Path(__file__)),
            "preregistration_sha256": _sha256(
                root / "docs" / "scrna" / "klf12_prior_preregistration.md"
            ),
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


RAW_EVIDENCE_COLUMNS: tuple[str, ...] = (
    "unit_id",
    "donor",
    "condition",
    "n_cells_epithelial",
    "median_raw_depth",
    "detection_fraction",
    "median_detected_umi",
    "share_of_detected_at_one_umi",
)


def write_evidence(findings: dict[str, object], destination: Path) -> Path:
    rows = list(findings["per_unit"])  # type: ignore[arg-type]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\t".join(RAW_EVIDENCE_COLUMNS) + "\n")
        for row in rows:
            handle.write(
                "\t".join(
                    "" if row.get(name) is None else str(row.get(name))
                    for name in RAW_EVIDENCE_COLUMNS
                )
                + "\n"
            )
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reduce",
        action="store_true",
        help="stream the accession's six per-sample matrices and write reduced "
        "per-barcode tables with a sidecar binding each to its source digest; "
        "~2.4 GB is read and discarded, nothing but the reduction is kept",
    )
    parser.add_argument(
        "--reduced",
        type=Path,
        required=True,
        help="directory of per-sample reduced tables (*.klf12.tsv, "
        "*.barcodes.tsv, *.reduction.json)",
    )
    parser.add_argument(
        "--cells",
        type=Path,
        help="per-cell table carrying `cell`, `sample_id` and `celltype_v2`; "
        "row-level metadata, so it must stay outside the tracked tree. "
        "Required unless --reduce is the only action",
    )
    parser.add_argument(
        "--extract-cells",
        type=Path,
        help="local copy of the deposited seurat_object.rds; extracts the "
        "annotation parent to --cells and records its binding sidecar",
    )
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args(argv)

    if args.reduce:
        for sample in SAMPLES:
            record = reduce_sample(sample, args.reduced)
            print(
                f"{sample}: {record['matrix_bytes']} bytes "
                f"sha256 {record['matrix_sha256'][:16]}..."
            )

    if args.extract_cells is not None:
        record = extract_cells(args.extract_cells, args.cells, rscript=args.rscript)
        print(f"extracted {args.cells} from RDS sha256 {record['rds_sha256'][:16]}...")

    if args.cells is None:
        if args.reduce:
            return 0
        parser.error("--cells is required to derive")

    # VALIDATE BOTH PARENTS BEFORE FITTING ANYTHING. The model fits take tens
    # of minutes; an unbound input is a property of the inputs and is knowable
    # in milliseconds. An earlier revision checked the binding only when
    # writing the artifact, so a refusal arrived after the whole computation
    # had been spent -- the check was right and its placement wasted the run.
    reduction_provenance(args.reduced, args.cells, root=args.root)

    findings = derive(args.reduced, args.cells)
    findings["_reduced_dir"] = str(args.reduced)
    findings["_cells_table"] = str(args.cells)
    evidence = write_evidence(
        findings, args.root / "docs" / "scrna" / "klf12_raw_umi_evidence.tsv"
    )
    report = write_findings(
        findings,
        args.root / "docs" / "scrna" / "klf12_raw_umi_findings.json",
        root=args.root,
    )
    print(f"wrote {evidence.relative_to(args.root)}")
    print(f"wrote {report.relative_to(args.root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
