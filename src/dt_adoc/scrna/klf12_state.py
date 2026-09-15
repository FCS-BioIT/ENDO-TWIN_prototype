"""Estimate -- or fail to estimate -- a KLF12-high state from the deposited object.

`E_KLF12_HIGH` is the only v0.4 state that can take a measured initial-state
prior without editing a Boolean rule, which is why it is the first candidate for
single-cell conditioning (`docs/scrna_observability.md`). This module executes
the analysis pre-registered in `docs/scrna/klf12_prior_preregistration.md` and
writes its result, whatever that result is, into two tracked artifacts.

THREE STEPS, KEPT APART. Measurement is the KLF12 value in a named layer. State
inference is a declared model taking that value to a per-unit probability.
Conditioning is that probability entering a `.istate`. This module does the
first two and stops; `klf12_conditioning.py` does the third, and only under the
tier the decision rule allows.

WHAT IT NEEDS AND WHAT IT DOES NOT. Like `verify_rds`, the extraction needs a
local copy of the 2.9 GB deposited object and an R with SeuratObject, and it
never downloads. The per-cell table it extracts carries row-level sample
metadata and is deliberately written outside the repository's tracked tree; only
per-unit aggregates are committed. The derivation half runs on that table alone,
so `--from-per-cell` re-derives every committed number with no R and no RDS,
which is what makes the artifacts checkable.

LEAKAGE. This module imports nothing from `dt_adoc.simulation`,
`dt_adoc.concordance`, `dt_adoc.calibration`, `dt_adoc.scoring` or
`dt_adoc.perturbations`, and reads no model output. Nothing here may be chosen
by what it does to an adhesion endpoint, and `tests/unit/test_klf12_state.py`
asserts the import boundary rather than trusting this paragraph.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ASSET_ID = "EXT-SCRNA-001"
GENE = "KLF12"

#: The population, fixed in the pre-registration before any KLF12 value was
#: read: every `celltype_v2` label that names an epithelium. Three of the seven
#: labels are named for the treatment and are ~80% one condition, so no single
#: label may be used as a stratifier for a condition contrast. The union is a
#: condition-independent *definition*; whether it is condition-balanced in
#: *composition* is measured below, not assumed.
EPITHELIAL_LABELS: tuple[str, ...] = (
    "Luminal-like epithelium",
    "Cycling epithelium",
    "HT epithelium I",
    "HT epithelium II",
)

#: Pre-registered sensitivity parameters for M2. Not biological boundaries.
QUANTILES: tuple[float, ...] = (0.75, 0.80, 0.85, 0.90, 0.95)

#: Genes pulled alongside KLF12 to describe the population the pre-declared
#: definition selects. They may not be used to redefine it.
CONTEXT_GENES: tuple[str, ...] = (
    "LIF",
    "EPCAM",
    "PTPRC",
    "COL1A1",
    "VIM",
    "PGR",
    "PAEP",
)

#: F1's pre-registered trigger: a within-unit top-vs-bottom depth-quartile
#: detection ratio above this, in a majority of units.
F1_RATIO = 2.0

#: Descriptive only. An earlier revision used this pair AS the F2 test, which
#: was wrong: the pre-registered F2 is a statement about the SHAPE of the
#: distribution ("a zero spike plus a monotone decreasing tail with no valley"),
#: and "most detected values are small" is a different proposition that a
#: genuinely bimodal distribution could also satisfy. F2 is now decided by
#: `fit_two_component_mixture` -- the criterion that was actually declared --
#: and these two numbers survive as the summary they always were.
FLOOR_VALUE = 2.0

#: Histogram resolution for the committed density of the detected values. The
#: report claims there is no interior mode, and a claim about a density needs a
#: density behind it rather than six order statistics.
HISTOGRAM_BINS = 40

#: The committed histogram is binned over this central range of log(detected),
#: and the count outside it is reported. Not cosmetic: the smallest "detected"
#: KLF12 value in this object is 4.5e-15, which is not an abundance. That cell
#: captured ONE raw UMI at a depth of 9,095 -- committed as
#: `cross_layer_corrected_vs_raw.minimum_corrected_cell` in
#: `docs/scrna/klf12_raw_umi_findings.json`, which is the module that can see
#: both layers -- and decontX
#: attributed essentially all of it to ambient contamination, so the value
#: records how hard the correction pushed rather than how much KLF12 was there.
#: A single such point stretches an equal-width binning over forty orders of
#: magnitude, leaving one occupied bin at each end and manufacturing a "valley"
#: between them. Trimming is declared here rather than applied silently, and
#: M1(a) does not depend on it.
HISTOGRAM_TRIM = 0.005

#: One transcript-equivalent. M1(a) requires the fitted boundary to sit at or
#: above it, which is this module's reading of the pre-registration's "a genuine
#: density valley, **not inside the zero spike**". A boundary BELOW the quantum
#: of the measurement cannot separate a high state from a low one, because one
#: molecule is the smallest difference the assay can report. Not a tunable
#: constant -- it is set by the assay, not by this analysis.
#:
#: AN EARLIER REVISION JUSTIFIED THIS CONSTANT WITH A CLAIM THE RAW LAYER
#: FALSIFIES, and the claim is recorded here rather than quietly deleted. It
#: said the sub-one values are "the correction's residue of cells that carried
#: no molecule". They are not. Joining these cells to the accession's raw
#: per-sample matrices by barcode (`klf12_raw_umi.py`) shows that all 2,251
#: epithelial cells with a corrected value strictly between 0 and 1 carried at
#: least one raw KLF12 UMI, and 2,247 of them carried exactly one; NONE carried
#: zero. decontX never zeroes a detected gene and never creates one -- the two
#: layers report the identical zero fraction -- so a sub-one value is a cell
#: that captured one molecule and had ambient signal subtracted from it, not a
#: cell that captured nothing. The constant survives the correction; the reason
#: given for it did not.
ONE_TRANSCRIPT = 1.0

#: M1(b): the high component must exclude at least this share of the cells M0
#: would call high, or it is the detection split wearing a mixture's name.
#: **Introduced after the data existed.** The pre-registration said "a
#: substantial share" and named no number, so this constant is post-hoc and is
#: labelled as such wherever it is reported. The decision does not turn on it:
#: M1(a) is a threshold-free shape criterion and is evaluated first.
M1_B_MIN_EXCLUDED_SHARE = 0.5

#: M1(c): the high and low components' median sequencing depths must not differ
#: by more than this ratio, or the split is reading library size. Also post-hoc,
#: also not decisive for the same reason.
M1_C_MAX_DEPTH_RATIO = 1.5

_R_EXTRACT = """
suppressPackageStartupMessages(library(SeuratObject))
args <- commandArgs(trailingOnly = TRUE)
obj <- readRDS(args[1])
md <- obj@meta.data
cm <- SeuratObject::LayerData(obj[["RNA"]], layer = "counts")
dm <- SeuratObject::LayerData(obj[["RNA"]], layer = "data")
genes <- strsplit(args[3], ",")[[1]]
present <- genes[genes %in% rownames(cm)]
missing <- setdiff(genes, present)
if (length(missing) > 0) stop(paste("absent features:", paste(missing, collapse = ",")))
df <- data.frame(
  sample_id = as.character(md$sample_id),
  celltype_v2 = as.character(md$celltype_v2),
  depth_counts = as.numeric(Matrix::colSums(cm)),
  nfeature_counts = as.integer(Matrix::colSums(cm > 0)),
  stringsAsFactors = FALSE
)
for (g in present) {
  df[[paste0("counts_", g)]] <- as.numeric(cm[g, ])
  df[[paste0("data_", g)]] <- as.numeric(dm[g, ])
}
write.table(df, args[2], sep = "\\t", quote = FALSE, row.names = FALSE)
cat(sprintf("r_version\\t%s\\n", R.version.string), file = stderr())
cat(sprintf("seuratobject_version\\t%s\\n",
            as.character(packageVersion("SeuratObject"))), file = stderr())
"""


class Klf12StateError(RuntimeError):
    """The derivation cannot proceed on the evidence it was given."""


@dataclass(frozen=True)
class Cell:
    """One epithelial cell's contribution. Never an independent replicate."""

    sample_id: str
    celltype_v2: str
    depth: float
    nfeature: int
    value: float


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    """Linear-interpolation quantile, so the artifact needs no numpy to check."""
    if not sorted_values:
        raise Klf12StateError("quantile of an empty sample")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = q * (len(sorted_values) - 1)
    low = int(position)
    high = min(low + 1, len(sorted_values) - 1)
    weight = position - low
    return float(sorted_values[low] * (1 - weight) + sorted_values[high] * weight)


def _median(values: Sequence[float]) -> float:
    return _quantile(sorted(values), 0.5)


def parse_unit(sample_id: str) -> tuple[str, str]:
    """Donor and condition, which are recoverable only from ``sample_id``.

    The deposited `meta.data` carries no `patient_id` or `group` column, so this
    parse is the whole of the donor structure available.
    """
    donor, _, condition = sample_id.partition("_")
    if not donor.endswith("TE") or condition not in {"CNT", "HT"}:
        raise Klf12StateError(f"unparseable sample_id {sample_id!r}")
    return donor[:-2], condition


def read_per_cell(path: Path) -> tuple[list[Cell], dict[str, int], dict[str, float]]:
    """Read the extracted per-cell table.

    Returns the epithelial cells, the whole-object cell count per sample, and
    per-gene detection inside and outside the pre-declared population.
    """
    column = f"counts_{GENE}"
    epithelial: list[Cell] = []
    per_sample_total: dict[str, int] = {}
    marker_hits: dict[str, float] = {}
    marker_in: dict[str, list[int]] = {gene: [0, 0] for gene in CONTEXT_GENES}
    marker_out: dict[str, list[int]] = {gene: [0, 0] for gene in CONTEXT_GENES}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if column not in (reader.fieldnames or ()):
            raise Klf12StateError(f"{path} carries no {column!r} column")
        for row in reader:
            sample_id = row["sample_id"]
            per_sample_total[sample_id] = per_sample_total.get(sample_id, 0) + 1
            inside = row["celltype_v2"] in EPITHELIAL_LABELS
            for gene in CONTEXT_GENES:
                key = f"counts_{gene}"
                if key not in row:
                    continue
                bucket = marker_in[gene] if inside else marker_out[gene]
                bucket[0] += 1
                bucket[1] += 1 if float(row[key]) > 0 else 0
            if not inside:
                continue
            epithelial.append(
                Cell(
                    sample_id=sample_id,
                    celltype_v2=row["celltype_v2"],
                    depth=float(row["depth_counts"]),
                    nfeature=int(row["nfeature_counts"]),
                    value=float(row[column]),
                )
            )
    if not epithelial:
        raise Klf12StateError("the pre-declared population selected no cells")
    for gene in CONTEXT_GENES:
        for label, bucket_map in (("epithelial", marker_in), ("other", marker_out)):
            total, hits = bucket_map[gene]
            if total:
                marker_hits[f"{gene}_{label}"] = hits / total
    return epithelial, per_sample_total, marker_hits


def _standardise(
    cells: Sequence[Cell],
    stratum: dict[int, str],
    threshold: float,
) -> tuple[dict[str, float | None], dict[str, int], dict[str, float]]:
    """Direct standardisation of the detection fraction to a common stratum mix.

    ``None`` where a unit does not populate every stratum: a standardised rate
    over a partial stratum set is not the same estimand, and silently dropping
    the missing strata would hide exactly the non-overlap that makes the
    adjustment unreliable.

    Two numbers are returned beside the estimate, and the second matters more.
    The thinnest stratum's CELL COUNT says how little data the weakest term
    rests on; the WEIGHT that stratum carries says how much of the answer it
    decides. They come apart badly here: a stratum of fourteen cells reads as
    one small term among many until you see that the common mix gives it 43% of
    the estimate. Reporting the count alone understates the thinness, so both
    are written into the artifact.
    """
    strata = sorted({stratum[id(cell)] for cell in cells})
    weight = {
        name: sum(1 for cell in cells if stratum[id(cell)] == name) / len(cells)
        for name in strata
    }
    out: dict[str, float | None] = {}
    thinnest: dict[str, int] = {}
    thinnest_weight: dict[str, float] = {}
    for unit in sorted({cell.sample_id for cell in cells}):
        total = 0.0
        complete = True
        smallest = None
        smallest_weight = 0.0
        for name in strata:
            members = [
                cell
                for cell in cells
                if cell.sample_id == unit and stratum[id(cell)] == name
            ]
            if smallest is None or len(members) < smallest:
                smallest = len(members)
                smallest_weight = weight[name]
            if not members:
                complete = False
                continue
            hits = sum(1 for cell in members if cell.value > threshold)
            total += weight[name] * hits / len(members)
        out[unit] = total if complete else None
        thinnest[unit] = smallest or 0
        thinnest_weight[unit] = smallest_weight
    return out, thinnest, thinnest_weight


def _depth_strata(cells: Sequence[Cell], count: int = 5) -> dict[int, str]:
    ordered = sorted(cell.depth for cell in cells)
    edges = [_quantile(ordered, index / count) for index in range(1, count)]
    labels: dict[int, str] = {}
    for cell in cells:
        position = sum(1 for edge in edges if cell.depth >= edge)
        labels[id(cell)] = f"D{position + 1}"
    return labels


def _histogram(
    values: Sequence[float], bins: int, trim: float = 0.0
) -> dict[str, object]:
    """Equal-width bin counts, so a claim about the density has one behind it.

    ``trim`` bins over the central range and reports how many values fell
    outside, rather than letting one numerical-residue point set the axis.
    """
    ordered = sorted(values)
    low = _quantile(ordered, trim)
    high = _quantile(ordered, 1.0 - trim)
    outside = sum(1 for value in values if value < low or value > high)
    if not high > low:
        raise Klf12StateError("cannot bin a degenerate sample")
    width = (high - low) / bins
    counts = [0] * bins
    for value in values:
        if value < low or value > high:
            continue
        index = min(bins - 1, int((value - low) / width))
        counts[index] += 1
    return {
        "edges": [low + width * index for index in range(bins + 1)],
        "counts": [float(count) for count in counts],
        "trim": trim,
        "values_outside_trimmed_range": outside,
        "modes": _local_maxima([float(count) for count in counts]),
    }


def _local_maxima(values: Sequence[float]) -> int:
    """Count interior local maxima of a sampled curve.

    Bimodality is "two modes", and the honest test for it is two local maxima --
    not "some interior point is lower than the endpoints", which an earlier
    revision used and which a narrow component nested inside a broad one
    satisfies trivially. That mistake would have reported this distribution as
    separable, so the weaker test is recorded here as rejected rather than
    quietly replaced.
    """
    count = 0
    for index in range(1, len(values) - 1):
        if values[index] > values[index - 1] and values[index] >= values[index + 1]:
            count += 1
    return count


def _mode_positions(histogram: dict[str, object]) -> list[float]:
    """Bin centres of the histogram's interior local maxima."""
    counts: list[float] = list(histogram["counts"])  # type: ignore[arg-type]
    edges: list[float] = list(histogram["edges"])  # type: ignore[arg-type]
    return [
        (edges[index] + edges[index + 1]) / 2
        for index in range(1, len(counts) - 1)
        if counts[index] > counts[index - 1] and counts[index] >= counts[index + 1]
    ]


def _component_crossings(
    mu0: float, var0: float, mu1: float, var1: float, weight: float
) -> list[float]:
    """Every point where the two weighted components have equal density.

    `(1 - w) N(x; mu0, var0) = w N(x; mu1, var1)`, logged, is
    `A x^2 + B x + C = 0`. Unequal variances give `A != 0` and up to two real
    roots -- the narrow-inside-broad case this data exhibits, where the broad
    component owns both tails. Equal variances degenerate to a line with one
    root. Returned sorted, so "is there exactly one, and does it lie between
    the means" is decidable without reference to any scan window.
    """
    low_weight = 1.0 - weight
    if low_weight <= 0.0 or weight <= 0.0:
        return []
    sd0, sd1 = math.sqrt(var0), math.sqrt(var1)
    a = 1.0 / (2.0 * var1) - 1.0 / (2.0 * var0)
    b = -mu1 / var1 + mu0 / var0
    c = (
        mu1 * mu1 / (2.0 * var1)
        - mu0 * mu0 / (2.0 * var0)
        - (math.log(weight / sd1) - math.log(low_weight / sd0))
    )
    # Only an EXACTLY zero quadratic term is linear. Treating a merely small
    # one as linear drops a real root: for var1 = var0 * (1 + 1e-15) the roots
    # are 0.5 and -1.8e15, and discarding the second reports a single interior
    # crossing -- a false ordered separation, the failure direction that
    # certifies a measured state which does not exist.
    if a == 0.0:
        if b == 0.0:
            return []
        return [-c / b]
    disc = b * b - 4.0 * a * c
    if disc < 0.0:
        return []
    if disc == 0.0:
        return [-b / (2.0 * a)]
    # Stable roots: the naive formula loses the small root to cancellation when
    # |4ac| << b^2, which is exactly the near-equal-variance regime above.
    root = math.sqrt(disc)
    q = -0.5 * (b + math.copysign(root, b))
    if q == 0.0:
        return sorted({(-b - root) / (2.0 * a), (-b + root) / (2.0 * a)})
    return sorted({q / a, c / q})


def _normal_pdf(value: float, mu: float, sd: float) -> float:
    var = max(sd * sd, 1e-12)
    return math.exp(-((value - mu) ** 2) / (2 * var)) / math.sqrt(2 * math.pi * var)


def fit_two_component_mixture(
    values: Sequence[float], *, iterations: int = 500
) -> dict[str, float]:
    """M1: a two-component Gaussian mixture on log(detected KLF12).

    Fitted on the DETECTED values only. Including the zeros would hand one
    component to the dropout spike and return a "boundary" at the detection
    limit -- which is precisely what M1(a) forbids and what M0 already is.

    Deterministic: initialised by splitting at the median, so the committed
    artifact is reproducible without a seed.
    """
    data = sorted(math.log(value) for value in values if value > 0)
    if len(data) < 20:
        raise Klf12StateError("too few detected cells to fit a mixture")
    midpoint = len(data) // 2
    low, high = data[:midpoint], data[midpoint:]

    def _moments(sample: Sequence[float]) -> tuple[float, float]:
        mean = sum(sample) / len(sample)
        var = sum((value - mean) ** 2 for value in sample) / max(1, len(sample) - 1)
        return mean, max(var, 1e-12)

    mu0, var0 = _moments(low)
    mu1, var1 = _moments(high)
    weight = 0.5

    def _normal(value: float, mu: float, var: float) -> float:
        return math.exp(-((value - mu) ** 2) / (2 * var)) / math.sqrt(2 * math.pi * var)

    responsibilities = [0.0] * len(data)
    for _ in range(iterations):
        for index, value in enumerate(data):
            a = (1 - weight) * _normal(value, mu0, var0)
            b = weight * _normal(value, mu1, var1)
            responsibilities[index] = b / (a + b) if (a + b) > 0 else 0.5
        mass = sum(responsibilities)
        if mass <= 0 or mass >= len(data):
            break
        weight = mass / len(data)
        mu1 = sum(r * v for r, v in zip(responsibilities, data)) / mass
        mu0 = sum((1 - r) * v for r, v in zip(responsibilities, data)) / (
            len(data) - mass
        )
        var1 = max(
            sum(r * (v - mu1) ** 2 for r, v in zip(responsibilities, data)) / mass,
            1e-12,
        )
        var0 = max(
            sum((1 - r) * (v - mu0) ** 2 for r, v in zip(responsibilities, data))
            / (len(data) - mass),
            1e-12,
        )
    if mu1 < mu0:
        mu0, mu1 = mu1, mu0
        var0, var1 = var1, var0
        weight = 1 - weight
        responsibilities = [1 - r for r in responsibilities]

    # M1(a), threshold-free: is the FITTED density actually bimodal? Sampled
    # across both components' support rather than only between their means,
    # because a mixture can put its second mode outside that interval and a
    # narrow-inside-broad pair can dip inside it without having two modes at all.
    span_low = mu0 - 4 * var0**0.5
    span_high = mu1 + 4 * var1**0.5
    grid = [span_low + (span_high - span_low) * index / 2000 for index in range(2001)]
    density = [
        (1 - weight) * _normal(value, mu0, var0) + weight * _normal(value, mu1, var1)
        for value in grid
    ]
    modes = _local_maxima(density)
    analytic_bimodal = modes >= 2

    # M1(a) names "a genuine density valley", and judging that needs two
    # quantities the fit supplies, so both are reported rather than one.
    #
    # (1) The posterior-0.5 set: EVERY crossing of the two weighted components,
    #     not merely the first one a left-to-right scan meets. When the
    #     components have very different variances the narrow one sits INSIDE
    #     the broad one, the set has two points, and the broad component owns
    #     both tails -- so a cell is assigned "high" below the lower crossing as
    #     well as above the upper one. There is then no ordered low/high split
    #     to read off the fit at all, and reporting either crossing as "the"
    #     boundary is an artefact of scan direction rather than a measurement.
    #     An earlier revision broke at the first crossing and reported it.
    # (2) The density minimum between the two modes, which is the valley the
    #     pre-registration actually names.
    # Solved, not scanned. Setting the two weighted normals equal and taking
    # logs gives a quadratic, so the posterior-0.5 set is exactly its real
    # roots. An earlier revision swept a finite grid spanning
    # [mu0 - 4*sd0, mu1 + 4*sd1] and reported the sign changes it happened to
    # bracket: a crossing OUTSIDE that window was silently missed, and the fit
    # was then reported as an ordered separation when it is not -- the failure
    # direction that certifies a measured state which does not exist.
    crossings = _component_crossings(mu0, var0, mu1, var1, weight)

    # Only crossings INSIDE the fitted data's support can partition any
    # observed cell, so only those count. The quadratic of two unequal-variance
    # normals always has a second root somewhere; for a well-separated fit
    # (mu 0 and 5, sd 1 and 1.2) it sits at -25, far below anything observed,
    # and counting it would reject a textbook separation. For THIS fit both
    # roots lie inside the observed range, so the wraparound is real rather
    # than an artefact of the algebra -- which is why the conclusion below
    # survives the correction.
    support_low, support_high = data[0], data[-1]
    in_support = [value for value in crossings if support_low <= value <= support_high]

    # An ordered separation needs exactly one in-support crossing, and it must
    # lie between the component means. Two means the assignment is not monotone
    # in expression and no single boundary separates low from high.
    interior = [value for value in in_support if mu0 < value < mu1]
    ordered_separation = len(in_support) == 1 and len(interior) == 1
    boundary = interior[0] if ordered_separation else None

    # The valley itself, between the two component means, when the fitted
    # density is bimodal at all.
    valley = None
    if analytic_bimodal:
        lo = min(range(len(grid)), key=lambda i: abs(grid[i] - mu0))
        hi = min(range(len(grid)), key=lambda i: abs(grid[i] - mu1))
        if lo < hi:
            valley = grid[min(range(lo, hi + 1), key=lambda i: density[i])]

    high_share = sum(1 for r in responsibilities if r >= 0.5) / len(data)
    return {
        "log_mean_low": mu0,
        "log_mean_high": mu1,
        "log_sd_low": var0**0.5,
        "log_sd_high": var1**0.5,
        "high_component_weight": weight,
        "high_component_share_of_detected": high_share,
        # `null`, not NaN: NaN is not JSON and a strict parser rejects the
        # shipped artifact. "No ordered boundary exists" is an explicit state
        # and is encoded as one.
        "boundary_log": None if boundary is None else boundary,
        "boundary_value": None if boundary is None else math.exp(boundary),
        "posterior_crossings_log": list(crossings),
        "posterior_crossings_value": [math.exp(value) for value in crossings],
        "posterior_crossings_in_support_log": list(in_support),
        "detected_log_support": [support_low, support_high],
        "ordered_separation": ordered_separation,
        #: What an interior-only rule -- "one crossing between the means",
        #: ignoring how many lie outside them -- would have returned for this
        #: fit. Recorded because it is NOT the rule applied, and because for
        #: this data it would have yielded a boundary above one transcript and
        #: so passed M1(a). The conclusion therefore depends on counting the
        #: lower crossing, and a reader is entitled to see that stated.
        "interior_only_rule_boundary_log": (interior[0] if interior else None),
        "interior_only_rule_boundary_value": (
            math.exp(interior[0]) if interior else None
        ),
        "density_minimum_log": None if valley is None else valley,
        "density_minimum_value": None if valley is None else math.exp(valley),
        "analytic_density_modes": modes,
        "analytic_bimodal": analytic_bimodal,
        "n_detected": len(data),
    }


#: M1(a) admits more than one operationalisation, and which one is applied
#: decides whether this fit proposes a boundary. The frozen pre-registration
#: says only: "the implied boundary falls in a genuine density valley, not
#: inside the zero spike". It names no crossing, no crossing count and no
#: ordering, so NONE of the three rules below is entailed by it -- each is a
#: post-hoc reading, and they are evaluated side by side rather than one being
#: promoted into the pre-registration after the fact.
#:
#: - `implemented`     -- exactly one posterior crossing inside the fitted
#:                        data's support, and that crossing between the means.
#:                        The most conservative reading; the one the decision
#:                        follows.
#: - `interior_only`   -- one crossing between the means, ignoring how many lie
#:                        outside them.
#: - `density_valley`  -- the literal sentence: the boundary IS the density
#:                        minimum between the two modes. The most permissive
#:                        reading, and the closest to the frozen wording.
#:
#: All three additionally require the boundary to clear `ONE_TRANSCRIPT`, which
#: is this module's reading of "not inside the zero spike".
M1_A_READINGS: tuple[str, ...] = ("implemented", "interior_only", "density_valley")


def m1_a_readings(mixture: dict[str, object]) -> dict[str, dict[str, object]]:
    """Evaluate M1(a) under every defensible reading of the frozen sentence.

    Returns one entry per reading with the boundary it proposes and whether it
    passes. Reported for the real fit AND for the null calibration below, which
    is what makes the two comparable: a reading that passes on data generated
    with no latent state is not evidence of a state whatever it says here.
    """
    bimodal = bool(mixture["analytic_bimodal"])
    proposals: dict[str, float | None] = {
        "implemented": (
            float(mixture["boundary_value"])
            if mixture["boundary_value"] is not None
            else None
        ),
        "interior_only": (
            float(mixture["interior_only_rule_boundary_value"])
            if mixture["interior_only_rule_boundary_value"] is not None
            else None
        ),
        "density_valley": (
            float(mixture["density_minimum_value"])
            if mixture["density_minimum_value"] is not None
            else None
        ),
    }
    out: dict[str, dict[str, object]] = {}
    for name in M1_A_READINGS:
        boundary = proposals[name]
        clears = boundary is not None and boundary >= ONE_TRANSCRIPT
        out[name] = {
            "boundary_value": boundary,
            "boundary_at_or_above_one_transcript": bool(clears),
            "passes": bool(bimodal and clears),
        }
    return out


#: The null calibration is Monte Carlo, so it is pinned rather than left to
#: chance: a committed artifact must not change because a seed moved.
NULL_CALIBRATION_SEED = 20260914
NULL_CALIBRATION_REPLICATES = 25
#: Multiples of the observed shrinkage noise at which the null is re-run, to
#: bound how far the specificity failure extends rather than assert it.
NULL_CALIBRATION_SMEAR_MULTIPLIERS: tuple[float, ...] = (1.0, 1.5, 2.0)


def _poisson(rate: float, rng: random.Random) -> int:
    """Knuth's method. Small rates only, which is the whole regime here."""
    if rate <= 0.0:
        return 0
    limit = math.exp(-rate)
    count, product = 0, 1.0
    while True:
        product *= rng.random()
        if product <= limit:
            return count
        count += 1


def calibrate_m1a_specificity(
    depths: Sequence[float],
    detection_fraction: float,
    shrinkage: float,
    shrinkage_sd: float,
    *,
    replicates: int = NULL_CALIBRATION_REPLICATES,
    seed: int = NULL_CALIBRATION_SEED,
    smear_multipliers: Sequence[float] = NULL_CALIBRATION_SMEAR_MULTIPLIERS,
) -> dict[str, object]:
    """Does M1(a) certify a population that has no latent state at all?

    THE POINT. M1 is a state-estimation model, and a state-estimation model
    that fires on data containing no state is not measuring a state. This
    builds exactly that null -- ONE homogeneous Poisson rate per unit of
    sequencing depth, no high sub-population, no biology whatsoever -- pushes
    it through the same integer lattice and the same decontX-like multiplicative
    shrinkage the real layer carries, and runs the identical mixture fit and the
    identical M1(a) readings over it.

    A reading that passes here is certifying molecule counts, not states. This
    is a specificity check on the estimator, not a test of the data, and it is
    the reason the conclusion in the report does not rest on which reading of
    M1(a) is adopted: the two permissive readings both pass the null.

    Calibrated, not guessed: the rate reproduces the observed detection
    fraction at the observed per-cell depths, and the shrinkage reproduces the
    observed ratio of corrected value to nearest integer.
    """
    rng = random.Random(seed)
    if not depths:
        raise Klf12StateError("no depths to calibrate a null against")
    mean_depth = sum(depths) / len(depths)

    def _detection_at(rate: float, draw: random.Random) -> float:
        hits = sum(1 for d in depths if _poisson(rate * d / mean_depth, draw) > 0)
        return hits / len(depths)

    low, high = 1e-6, 5.0
    for _ in range(40):
        middle = (low + high) / 2
        if _detection_at(middle, random.Random(seed)) < detection_fraction:
            low = middle
        else:
            high = middle
    rate = (low + high) / 2

    # HOW FAR THE FAILURE EXTENDS, which is a claim that has to be bounded
    # rather than asserted. The rule is fooled by a lattice it can SEE: smear
    # the lattice by widening the shrinkage noise and the false passes stop.
    # Reported so the finding is scoped to this measurement's resolution --
    # "the rule has no specificity at the lattice resolution these data sit
    # at" -- and not overstated into a claim about the rule everywhere.
    smear: dict[str, dict[str, int]] = {}
    for multiplier in smear_multipliers:
        if multiplier == 1.0:
            continue
        counts_at = {name: 0 for name in M1_A_READINGS}
        draw = random.Random(seed + 1)
        done = 0
        for _ in range(max(1, replicates // 2)):
            trial: list[float] = []
            for depth in depths:
                drawn = _poisson(rate * depth / mean_depth, draw)
                if drawn > 0:
                    trial.append(
                        drawn
                        * max(1e-12, draw.gauss(shrinkage, shrinkage_sd * multiplier))
                    )
            if len(trial) < 20:
                continue
            done += 1
            for name, verdict in m1_a_readings(
                fit_two_component_mixture(trial)
            ).items():
                if verdict["passes"]:
                    counts_at[name] += 1
        smear[f"x{multiplier:g}"] = {**counts_at, "replicates": done}

    tallies = {name: 0 for name in M1_A_READINGS}
    boundaries: dict[str, list[float]] = {name: [] for name in M1_A_READINGS}
    m1_b_passes_on_null = 0
    fitted = 0
    for _ in range(replicates):
        sample: list[float] = []
        for depth in depths:
            drawn = _poisson(rate * depth / mean_depth, rng)
            if drawn > 0:
                sample.append(drawn * max(1e-12, rng.gauss(shrinkage, shrinkage_sd)))
        if len(sample) < 20:
            continue
        fitted += 1
        null_fit = fit_two_component_mixture(sample)
        # (b) costs nothing extra: it is a function of the fit alone. (c) and
        # the falsifiers are NOT evaluated here -- see `covers` below.
        if (
            1.0 - float(null_fit["high_component_share_of_detected"])
            >= M1_B_MIN_EXCLUDED_SHARE
        ):
            m1_b_passes_on_null += 1
        readings = m1_a_readings(null_fit)
        for name, verdict in readings.items():
            if verdict["passes"]:
                tallies[name] += 1
            if verdict["boundary_value"] is not None:
                boundaries[name].append(float(verdict["boundary_value"]))
    return {
        "null_model": (
            "one homogeneous Poisson rate per unit of sequencing depth -- no "
            "latent KLF12-high sub-population -- pushed through the integer "
            "lattice and a decontX-like multiplicative shrinkage"
        ),
        "calibrated_rate_at_mean_depth": rate,
        "shrinkage_mean": shrinkage,
        "shrinkage_sd": shrinkage_sd,
        "seed": seed,
        "replicates": fitted,
        "m1_a_false_pass_count": dict(tallies),
        "m1_a_false_pass_rate": {
            name: (tallies[name] / fitted if fitted else None) for name in M1_A_READINGS
        },
        "m1_b_false_pass_count": m1_b_passes_on_null,
        # WHAT THIS DOES AND DOES NOT CALIBRATE, stated so the result is not
        # read as more than it is. M1(a) and M1(b) are functions of the fit and
        # are evaluated on every null replicate. M1(c) needs per-cell depths
        # tied to the SIMULATED assignment and the falsifiers need per-unit
        # structure -- donors, conditions, subtype composition -- that this null
        # does not model, so neither is evaluated. The claim this supports is
        # therefore "the M1(a) criterion has no specificity here", NOT "the
        # whole pre-registered battery would pass on stateless data".
        "covers": ["M1(a) under every reading", "M1(b)"],
        "does_not_cover": ["M1(c)", "F1", "F2", "F3", "the decision branch"],
        "false_pass_under_widened_shrinkage_noise": smear,
        "scope": (
            "a specificity failure at THIS measurement's lattice resolution, "
            "not a universal property of the rule: widening the shrinkage "
            "noise until the integer lattice is no longer visible stops the "
            "false passes"
        ),
        "median_null_boundary_value": {
            name: (_median(values) if values else None)
            for name, values in boundaries.items()
        },
    }


def _condition_contrasts(
    units: Sequence[str],
    table: dict[str, float | None],
) -> dict[str, float | None]:
    per_donor: dict[str, float | None] = {}
    for donor in sorted({parse_unit(unit)[0] for unit in units}):
        high = table.get(f"{donor}TE_HT")
        low = table.get(f"{donor}TE_CNT")
        per_donor[donor] = (
            None if high is None or low is None else float(high) - float(low)
        )
    return per_donor


def derive(path: Path) -> dict[str, object]:
    """Run the pre-registered battery and return every number it produced."""
    cells, per_sample_total, markers = read_per_cell(path)
    units = sorted({cell.sample_id for cell in cells})
    values = sorted(cell.value for cell in cells)
    detected = sorted(value for value in values if value > 0)
    if not detected:
        raise Klf12StateError(f"{GENE} is not detected in the pre-declared population")
    zero_fraction = 1.0 - len(detected) / len(values)

    thresholds = {f"q{int(q * 100)}": _quantile(values, q) for q in QUANTILES}
    degenerate = sorted(key for key, value in thresholds.items() if value <= 0.0)

    per_unit: list[dict[str, object]] = []
    for unit in units:
        members = [cell for cell in cells if cell.sample_id == unit]
        donor, condition = parse_unit(unit)
        by_depth = sorted(members, key=lambda cell: cell.depth)
        quartiles = [
            by_depth[index * len(by_depth) // 4 : (index + 1) * len(by_depth) // 4]
            for index in range(4)
        ]
        rates = [
            sum(1 for cell in part if cell.value > 0) / len(part) if part else 0.0
            for part in quartiles
        ]
        row: dict[str, object] = {
            "unit_id": unit,
            "donor": donor,
            "condition": condition,
            "n_cells_epithelial": len(members),
            "n_cells_sample_total": per_sample_total[unit],
            "epithelial_share": len(members) / per_sample_total[unit],
            "median_depth_counts": _median([cell.depth for cell in members]),
            "median_nfeature_counts": _median(
                [float(cell.nfeature) for cell in members]
            ),
            "detection_fraction": sum(1 for cell in members if cell.value > 0)
            / len(members),
            "depth_quartile_detection": rates,
            "depth_q4_over_q1": (rates[3] / rates[0]) if rates[0] > 0 else None,
        }
        for key, threshold in thresholds.items():
            # A threshold at or below zero IS the detection boundary, which M0
            # declares inadmissible on its own. Recorded at its degenerate value
            # rather than quietly skipped, because the degeneracy is a finding.
            row[f"p_{key}"] = sum(
                1 for cell in members if cell.value > threshold
            ) / len(members)
        spread = [float(row[f"p_{key}"]) for key in thresholds]
        row["p_across_q_width"] = max(spread) - min(spread)
        per_unit.append(row)

    depth_standardised, depth_thinnest, depth_thin_weight = _standardise(
        cells, _depth_strata(cells), 0.0
    )
    subtype_standardised, subtype_thinnest, subtype_thin_weight = _standardise(
        cells, {id(cell): cell.celltype_v2 for cell in cells}, 0.0
    )
    for row in per_unit:
        unit = str(row["unit_id"])
        row["detection_depth_standardised"] = depth_standardised[unit]
        row["detection_subtype_standardised"] = subtype_standardised[unit]
        row["depth_stratum_min_cells"] = depth_thinnest[unit]
        row["depth_stratum_min_weight"] = depth_thin_weight[unit]
        row["subtype_stratum_min_cells"] = subtype_thinnest[unit]
        row["subtype_stratum_min_weight"] = subtype_thin_weight[unit]

    # --- the pre-registered falsifiers -------------------------------------
    ratios = [row["depth_q4_over_q1"] for row in per_unit]
    f1_hits = sum(
        1 for ratio in ratios if ratio is not None and float(ratio) > F1_RATIO
    )
    f1 = f1_hits > len(per_unit) / 2

    near_floor = sum(1 for value in detected if value < FLOOR_VALUE) / len(detected)

    # M1, fitted rather than asserted. F2 is a separate, weaker claim about the
    # shape of the density -- no interior valley -- and is not M1(a) negated.
    mixture = fit_two_component_mixture(detected)
    log_histogram = _histogram(
        [math.log(value) for value in detected], HISTOGRAM_BINS, HISTOGRAM_TRIM
    )
    # M1(a). THE FROZEN SENTENCE IS "the implied boundary falls in a genuine
    # density valley, not inside the zero spike", and that is ALL it says. It
    # names no posterior crossing, no crossing count and no ordering
    # requirement, so the conjunction applied below -- exactly one crossing
    # inside the fitted data's support, and that crossing between the means --
    # is a POST-HOC operationalisation chosen after the data existed. It is a
    # defensible and deliberately conservative one, and it is not the only
    # defensible one: `m1_a_readings` evaluates the two more permissive
    # readings beside it, and on this fit they DISAGREE with it. That
    # disagreement is recorded rather than resolved by assertion.
    #
    # What resolves it is not a reading of the sentence but a property of the
    # estimator: `calibrate_m1a_specificity` below shows that both permissive
    # readings certify a population simulated with NO latent state at all. A
    # criterion that passes the null is not evidence of a state under any
    # reading, which is why the negative conclusion does not depend on the
    # choice made here.
    ordered = bool(mixture["ordered_separation"])
    boundary_above_quantum = ordered and (
        mixture["boundary_value"] is not None
        and float(mixture["boundary_value"]) >= ONE_TRANSCRIPT
    )
    mixture["boundary_at_or_above_one_transcript"] = boundary_above_quantum
    m1_a = bool(mixture["analytic_bimodal"]) and ordered and boundary_above_quantum
    mixture["m1_a_rule_provenance"] = "post_hoc_operationalisation"
    mixture["m1_a_frozen_wording"] = (
        "the implied boundary falls in a genuine density valley, not inside "
        "the zero spike"
    )
    mixture["m1_a_rule_applied"] = (
        "exactly one posterior crossing inside the fitted data's support, AND "
        "that crossing lying between the component means, AND at or above one "
        "transcript-equivalent"
    )
    mixture["m1_a_under_each_reading"] = m1_a_readings(mixture)
    # The support that "in-support" is computed over is the observed MINIMUM of
    # the detected values, and that minimum is 4.5e-15 -- one cell out of 3,429,
    # which captured one raw UMI that the correction assigned almost entirely to
    # ambient signal. That is a property of the correction, not a measurement of
    # abundance, and a biological verdict may not turn on it. So the same test
    # is recomputed over a support trimmed to the central 98% of the detected
    # values and the two answers are reported together. They agree here, which
    # is the only reason the numeric definition is allowed to stand.
    trimmed_low = math.log(_quantile(detected, 0.01))
    trimmed_high = math.log(_quantile(detected, 0.99))
    trimmed = [
        value
        for value in mixture["posterior_crossings_log"]  # type: ignore[union-attr]
        if trimmed_low <= float(value) <= trimmed_high
    ]
    mixture["detected_log_support_trimmed_98"] = [trimmed_low, trimmed_high]
    mixture["posterior_crossings_in_trimmed_support_log"] = list(trimmed)
    mixture["ordered_separation_on_trimmed_support"] = len(trimmed) == 1
    mixture["support_definition_changes_m1_a"] = bool((len(trimmed) == 1) != ordered)

    excluded = 1.0 - float(mixture["high_component_share_of_detected"])
    m1_b = excluded >= M1_B_MIN_EXCLUDED_SHARE

    # (c) as pre-registered: "component assignment is not explained by
    # sequencing depth". The test is over the fit's OWN assignment, so it is
    # computed from the posterior and not from a cut on expression. That
    # distinction is load-bearing here rather than pedantic: the broad
    # component owns both tails, so NO threshold on value reproduces the
    # assignment -- a cut would put the sub-0.78 cells, which the fit calls
    # high, on the low side and silently measure a different partition.
    mu_low = float(mixture["log_mean_low"])
    sd_low = float(mixture["log_sd_low"])
    mu_high = float(mixture["log_mean_high"])
    sd_high = float(mixture["log_sd_high"])
    w_high = float(mixture["high_component_weight"])

    def _assigned_high(value: float) -> bool:
        point = math.log(value)
        return w_high * _normal_pdf(point, mu_high, sd_high) >= (
            1 - w_high
        ) * _normal_pdf(point, mu_low, sd_low)

    mixture["m1_c_split_basis"] = "posterior_component_assignment"
    detected_cells = [cell for cell in cells if cell.value > 0]
    above = [cell for cell in detected_cells if _assigned_high(cell.value)]
    below = [cell for cell in detected_cells if not _assigned_high(cell.value)]
    if above and below:
        depth_ratio = _median([cell.depth for cell in above]) / _median(
            [cell.depth for cell in below]
        )
        m1_c = 1 / M1_C_MAX_DEPTH_RATIO <= depth_ratio <= M1_C_MAX_DEPTH_RATIO
    else:
        depth_ratio = float("nan")
        m1_c = False
    # M1(c) POOLED IS THE WRONG STRATUM, and the pooled number hides it.
    # Median depth differs 5x BETWEEN units in this object (`SZ25TE_HT` at
    # ~62,000 against ~12,000 elsewhere), so a pooled high-vs-low depth ratio
    # is partly a comparison of samples rather than of components. The claim
    # M1(c) makes -- "component assignment is not explained by sequencing
    # depth" -- is a within-unit claim, so it is computed within each unit too
    # and both are reported. The post-hoc 1.5 bar is not what carries it: what
    # carries it is that the within-unit ratios do not even agree in DIRECTION.
    per_unit_depth_ratio: dict[str, float | None] = {}
    for unit in units:
        members = [cell for cell in detected_cells if cell.sample_id == unit]
        hi = [cell.depth for cell in members if _assigned_high(cell.value)]
        lo = [cell.depth for cell in members if not _assigned_high(cell.value)]
        per_unit_depth_ratio[unit] = (
            _median(hi) / _median(lo) if hi and lo and _median(lo) > 0 else None
        )
    stratified = [v for v in per_unit_depth_ratio.values() if v is not None]
    mixture["m1_c_depth_ratio_per_unit"] = per_unit_depth_ratio
    mixture["m1_c_units_within_post_hoc_bar"] = sum(
        1 for v in stratified if 1 / M1_C_MAX_DEPTH_RATIO <= v <= M1_C_MAX_DEPTH_RATIO
    )
    mixture["m1_c_units_evaluated"] = len(stratified)
    # Directionally inconsistent means no monotone depth signal to explain the
    # assignment, which is a stronger statement than any single ratio clearing
    # a bar chosen after the fact.
    mixture["m1_c_ratio_direction_is_consistent"] = bool(
        stratified
        and (all(v > 1 for v in stratified) or all(v < 1 for v in stratified))
    )
    mixture["m1_c_bar_provenance"] = "post_hoc_threshold_not_pre_registered"

    # What the two components actually hold, which is the fact the report rests
    # on. The "high" component is not "more KLF12": it is everything that is
    # not sitting on the one-molecule lattice point, sub-molecule residue
    # included.
    crossing_values = [float(v) for v in mixture["posterior_crossings_value"]]
    if len(crossing_values) == 2:
        mixture["high_component_below_lower_crossing"] = sum(
            1 for cell in detected_cells if cell.value < crossing_values[0]
        )
        mixture["high_component_above_upper_crossing"] = sum(
            1 for cell in detected_cells if cell.value > crossing_values[1]
        )

    # SPECIFICITY. Everything above asks what the fit says about these cells.
    # This asks the prior question -- whether the fit says anything at all --
    # by running the identical battery over a population simulated with no
    # latent state. Calibrated to this object: the observed detection fraction
    # at the observed per-cell depths, and the observed ratio of corrected
    # value to nearest integer.
    ratios = [value / round(value) for value in detected if value > 0.5]
    shrink_mean = sum(ratios) / len(ratios)
    shrink_sd = (
        sum((r - shrink_mean) ** 2 for r in ratios) / max(1, len(ratios) - 1)
    ) ** 0.5
    mixture["decontx_value_over_nearest_integer_mean"] = shrink_mean
    mixture["decontx_value_over_nearest_integer_sd"] = shrink_sd
    mixture["m1_a_specificity_calibration"] = calibrate_m1a_specificity(
        [cell.depth for cell in cells],
        1.0 - zero_fraction,
        shrink_mean,
        shrink_sd,
    )

    mixture["empirical_histogram_modes"] = log_histogram["modes"]
    mixture["component_depth_ratio"] = depth_ratio
    mixture["m1_a_density_valley"] = m1_a
    mixture["m1_b_excludes_detected_share"] = excluded
    mixture["m1_b_passes"] = m1_b
    mixture["m1_c_passes"] = m1_c
    mixture["m1_passes"] = bool(m1_a and m1_b and m1_c)

    # F2 as pre-registered: "a zero spike plus a monotone decreasing tail with
    # no valley". That is a statement about the shape of the OBSERVED
    # distribution, and it is NOT the negation of M1(a): a distribution can
    # have a valley -- so F2 does not fire -- while the boundary a mixture
    # implies is still inadmissible, so M1(a) fails. An earlier revision set
    # `f2 = not m1_a`, which reported F2 as fired on a fit whose own
    # `analytic_bimodal` was True.
    #
    # THE FITTED DENSITY IS NOT THE DISTRIBUTION, so the frozen sentence is now
    # evaluated on the empirical histogram of the detected values, which is
    # what it is about, and the fitted-density test is kept beside it as the
    # proxy it always was. TWO things separate them, and the proxy tests
    # neither: the frozen sentence requires the tail to be MONOTONE DECREASING,
    # which "has fewer than two modes" does not test; and a two-component
    # Gaussian can be unimodal over a histogram that plainly is not. A third
    # difference is NOT claimed, because this reading does not deliver it --
    # the frozen sentence speaks of the distribution including the zero spike,
    # and the histogram below is built from the detected values alone, so it
    # cannot see that spike either. What the zeros contribute is reported
    # separately as `zero_fraction`, and F2 is read on the tail. The decision
    # follows the empirical reading. Both agree
    # here -- the tail rises to the one-molecule mode, so it is not monotone
    # decreasing and F2 is silent either way -- and the pre-registered rule
    # routes neither CONDITIONAL-GO nor NO-GO through F2 in any case.
    # The tail is the committed histogram of the detected values -- the same
    # one the report cites, at its declared trim, so F2 and the published
    # density are the same object rather than two differently binned ones.
    tail_counts = [float(count) for count in log_histogram["counts"]]  # type: ignore[index]
    tail_monotone = all(
        tail_counts[index] >= tail_counts[index + 1]
        for index in range(len(tail_counts) - 1)
    )
    tail_modes = _local_maxima(tail_counts)
    f2_empirical = tail_monotone and tail_modes < 2
    f2_fitted_proxy = not bool(mixture["analytic_bimodal"])
    f2 = f2_empirical

    # F3 is the one pre-registered sentence loose enough to admit two readings:
    # "the width of the across-q interval exceeds THE LARGEST across-unit
    # difference AT ANY FIXED q". Read as max-over-q it is a permissive bar; read
    # as "exceeds, at any fixed q, the across-unit difference" it is the minimum
    # over q and a strict one. Both are computed and both are recorded, because
    # the permissive reading is the one that licenses running the sweep and a
    # reader is entitled to see what the strict one would have said. The
    # decision follows the max reading, which is the more natural parse of the
    # sentence as written; under the strict reading F3 fires and the decision
    # would be NO_GO. Nothing was activated under either.
    widths = [float(row["p_across_q_width"]) for row in per_unit]
    spreads = {
        key: max(float(row[f"p_{key}"]) for row in per_unit)
        - min(float(row[f"p_{key}"]) for row in per_unit)
        for key in thresholds
    }
    across_unit = max(spreads.values())
    across_unit_strict = min(spreads.values())
    f3 = any(width > across_unit for width in widths)
    f3_strict = any(width > across_unit_strict for width in widths)

    # The pre-registered rule, and the whole conjunction it actually states:
    # GO needs M1 to PASS (a), (b) and (c) -- not merely the falsifiers to stay
    # silent. An earlier revision tested the falsifiers alone, which would have
    # awarded GO, and with it the promotion of EXT-SCRNA-001, without ever
    # fitting M1. It never bit, because F2 fired; it was still the rule bent in
    # the permissive direction, and the test that should have caught it encoded
    # the same mistake.
    if mixture["m1_passes"] and not f1 and not f2 and not f3:
        decision = "GO"
    elif not f1 and not f3:
        decision = "CONDITIONAL_GO"
    else:
        decision = "NO_GO"

    # THE COUNTERFACTUAL THE WHOLE REPORT TURNS ON, committed as a value rather
    # than left in prose. M1(b) and M1(c) both pass, and F1, F2 and F3 are all
    # silent, so M1(a) alone decides the branch -- and M1(a) is decided by a
    # POST-HOC reading. Under either reading closer to the frozen wording the
    # branch is GO, which would have made EXT-SCRNA-001 eligible for promotion
    # to an active constraint on a fit whose "low" component is a single lattice
    # point. Recording the decision under every reading is what stops that
    # dependence from being invisible to a reader who only sees the verdict.
    decision_by_reading: dict[str, str] = {}
    for name, verdict in mixture["m1_a_under_each_reading"].items():  # type: ignore[union-attr]
        passes_m1 = bool(verdict["passes"]) and m1_b and m1_c
        if passes_m1 and not f1 and not f2 and not f3:
            decision_by_reading[name] = "GO"
        elif not f1 and not f3:
            decision_by_reading[name] = "CONDITIONAL_GO"
        else:
            decision_by_reading[name] = "NO_GO"

    # TWO INDEPENDENT AMBIGUITIES, not one, and they pull in opposite
    # directions. M1(a)'s reading moves the branch towards GO; F3's reading --
    # the other loose pre-registered sentence, already recorded above -- moves
    # it to NO_GO, since F3 firing overrides everything. Crossing the two is the
    # honest statement of what the frozen document determines, which is: not a
    # single branch. The shipped `decision` remains the one that actually
    # governed what was done, and nothing was activated under any cell of this
    # grid.
    branch_grid: dict[str, str] = {}
    for name, verdict in mixture["m1_a_under_each_reading"].items():  # type: ignore[union-attr]
        for f3_name, f3_fired in (("f3_permissive", f3), ("f3_strict", f3_strict)):
            passes_m1 = bool(verdict["passes"]) and m1_b and m1_c
            if f1 or f3_fired:
                branch_grid[f"{name}+{f3_name}"] = "NO_GO"
            elif passes_m1 and not f2:
                branch_grid[f"{name}+{f3_name}"] = "GO"
            else:
                branch_grid[f"{name}+{f3_name}"] = "CONDITIONAL_GO"

    # Composition, which the pre-registration named as the leakage risk but did
    # not enumerate as a falsifier. Reported because the two admissible
    # adjustments can disagree, which is a stronger statement than either alone.
    subtypes = sorted({cell.celltype_v2 for cell in cells})
    composition = {
        unit: {
            label: sum(
                1
                for cell in cells
                if cell.sample_id == unit and cell.celltype_v2 == label
            )
            / sum(1 for cell in cells if cell.sample_id == unit)
            for label in subtypes
        }
        for unit in units
    }
    subtype_detection: dict[str, dict[str, float | None]] = {}
    for label in subtypes:
        subtype_detection[label] = {}
        for condition in ("CNT", "HT"):
            members = [
                cell
                for cell in cells
                if cell.celltype_v2 == label
                and parse_unit(cell.sample_id)[1] == condition
            ]
            subtype_detection[label][condition] = (
                sum(1 for cell in members if cell.value > 0) / len(members)
                if members
                else None
            )

    crude: dict[str, float | None] = {
        str(row["unit_id"]): float(row["detection_fraction"]) for row in per_unit
    }
    contrasts = {
        "crude": _condition_contrasts(units, crude),
        "depth_standardised": _condition_contrasts(units, depth_standardised),
        "subtype_standardised": _condition_contrasts(units, subtype_standardised),
    }
    signs = {
        key: sorted(
            {
                (0 if value == 0 else (1 if value > 0 else -1))
                for value in per_donor.values()
                if value is not None
            }
        )
        for key, per_donor in contrasts.items()
    }

    return {
        "gene": GENE,
        "layer": "counts",
        "layer_caveat": (
            "decontX-corrected and non-integer; not raw UMIs. Raw per-sample "
            "matrices exist separately in the same accession."
        ),
        "population_definition": list(EPITHELIAL_LABELS),
        "n_cells_epithelial": len(cells),
        "n_cells_object": sum(per_sample_total.values()),
        "zero_fraction": zero_fraction,
        "detected_below_two_fraction": near_floor,
        "state_model_m1": mixture,
        "detected_log_histogram": log_histogram,
        # Where the empirical modes SIT is the finding the mixture obscures.
        # If they line up with log(1), log(2), log(3)... the multimodality is
        # the integer molecule lattice showing through the decontX correction,
        # not two biological states -- and a two-component fit will happily
        # report "bimodal" for it.
        "detected_log_mode_positions": _mode_positions(log_histogram),
        "integer_transcript_log_positions": [
            math.log(count) for count in (1, 2, 3, 4, 5)
        ],
        "detected_value_quantiles": {
            f"q{int(q * 100)}": _quantile(detected, q)
            for q in (0.0, 0.25, 0.5, 0.75, 0.95, 1.0)
        },
        "pooled_thresholds": thresholds,
        "degenerate_thresholds": degenerate,
        "per_unit": per_unit,
        "subtype_composition": composition,
        "subtype_detection_by_condition": subtype_detection,
        "condition_contrasts": contrasts,
        "condition_contrast_sign_sets": signs,
        "marker_detection": markers,
        "falsifiers": {
            "F1_depth_confounding": f1,
            "F1_units_above_ratio": f1_hits,
            "F2_no_separation": f2,
            "F2_criterion": "the frozen wording, evaluated on the EMPIRICAL "
            "histogram of the detected values: a monotone decreasing tail with "
            "no interior mode. Not the negation of M1(a), and not the fitted "
            "density -- the tail rises to the one-molecule mode, so it is "
            "neither monotone nor valley-free and F2 is silent",
            "F2_basis": "empirical_histogram_of_detected_values",
            "F2_tail_is_monotone_decreasing": tail_monotone,
            "F2_tail_interior_modes": tail_modes,
            "F2_fitted_density_proxy": f2_fitted_proxy,
            "F2_proxy_note": "an earlier revision decided F2 from the fitted "
            "two-component density, which can be unimodal over a histogram "
            "that is not, cannot see the zero spike the frozen sentence names, "
            "and never tests monotonicity. Kept beside the empirical reading "
            "as the proxy it was; both agree here",
            "F3_threshold_dominance": f3,
            "F3_reading": "across-q width vs the MAXIMUM across-unit spread "
            "over q; the strict reading uses the minimum and is reported beside "
            "it because the pre-registered sentence admits both",
            "F3_largest_across_unit_spread": across_unit,
            "F3_smallest_across_unit_spread": across_unit_strict,
            "F3_threshold_dominance_strict_reading": f3_strict,
            "F3_decision_under_strict_reading": ("NO_GO" if f3_strict else "unchanged"),
            "F4_no_reference_for_high": True,
        },
        "decision": decision,
        "decision_under_each_m1_a_reading": decision_by_reading,
        "decision_depends_on_the_post_hoc_m1_a_rule": (
            len(set(decision_by_reading.values())) > 1
        ),
        "decision_under_each_reading_pair": branch_grid,
        "decision_branches_reachable": sorted(set(branch_grid.values())),
        "decision_is_uniquely_determined_by_the_preregistration": (
            len(set(branch_grid.values())) == 1
        ),
        "shipped_decision_basis": (
            "the implemented post-hoc M1(a) rule with the permissive F3 "
            "reading -- the combination that actually governed what was done. "
            "It is reported as one cell of decision_under_each_reading_pair, "
            "not as the branch the pre-registration determines, because the "
            "pre-registration does not determine one. Nothing was activated "
            "under any cell."
        ),
    }


EVIDENCE_COLUMNS: tuple[str, ...] = (
    "unit_id",
    "donor",
    "condition",
    "n_cells_epithelial",
    "n_cells_sample_total",
    "epithelial_share",
    "median_depth_counts",
    "median_nfeature_counts",
    "detection_fraction",
    "detection_depth_standardised",
    "detection_subtype_standardised",
    "depth_stratum_min_cells",
    "depth_stratum_min_weight",
    "subtype_stratum_min_cells",
    "subtype_stratum_min_weight",
    "depth_q1_detection",
    "depth_q2_detection",
    "depth_q3_detection",
    "depth_q4_detection",
    "depth_q4_over_q1",
    "p_q75",
    "p_q80",
    "p_q85",
    "p_q90",
    "p_q95",
    "p_across_q_width",
)


def _format(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_evidence(findings: dict[str, object], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = findings["per_unit"]  # type: ignore[assignment]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(EVIDENCE_COLUMNS)
        for row in rows:
            flat = dict(row)
            quartiles: list[float] = row["depth_quartile_detection"]  # type: ignore[assignment]
            for index in range(4):
                flat[f"depth_q{index + 1}_detection"] = quartiles[index]
            writer.writerow([_format(flat.get(name)) for name in EVIDENCE_COLUMNS])
    return destination


def source_digest(root: Path) -> str:
    path = root / "config" / "external_data_manifest.tsv"
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["asset_id"] == ASSET_ID:
                return row["sha256"]
    raise Klf12StateError(f"{ASSET_ID} is not in {path}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_findings(
    findings: dict[str, object],
    destination: Path,
    *,
    root: Path,
    r_versions: dict[str, str],
) -> Path:
    payload = dict(findings)
    payload["schema_version"] = "1.0"
    payload["provenance"] = {
        "asset_id": ASSET_ID,
        "source_accession": "E-MTAB-15842",
        "source_filename": "seurat_object.rds",
        "source_sha256": source_digest(root),
        "source_binding_checked_against": "config/external_data_manifest.tsv",
        "evidence_role": "same_dataset_internal",
        "claim_level": "conditioning_candidate_not_validation",
        "derivation_module_sha256": _sha256(Path(__file__).resolve()),
        "preregistration_sha256": _sha256(
            root / "docs" / "scrna" / "klf12_prior_preregistration.md"
        ),
        **r_versions,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


#: Written beside the per-cell table so a later `--from-per-cell` re-derivation
#: can still say which R produced the numbers. Without it the artifact records
#: `r_version: not_used`, which is true of that invocation and misleading about
#: the evidence: the values still came out of an R session, just an earlier one.
EXTRACTION_SIDECAR_SUFFIX = ".extraction.json"


def _sidecar(per_cell: Path) -> Path:
    return per_cell.with_name(per_cell.name + EXTRACTION_SIDECAR_SUFFIX)


def extraction_provenance(per_cell: Path) -> dict[str, str]:
    """R versions recorded when this per-cell table was extracted.

    An absent sidecar is reported as unknown rather than as absence of R. A
    per-cell table that this module did not write could have come from
    anywhere, and saying so is the point.
    """
    path = _sidecar(per_cell)
    unknown = "unknown_extraction_environment"
    if not path.is_file():
        return {
            "r_version": unknown,
            "seuratobject_version": unknown,
            "rds_sha256": "",
            "per_cell_sha256": "",
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "r_version": str(payload.get("r_version", unknown)),
        "seuratobject_version": str(payload.get("seuratobject_version", unknown)),
        "rds_sha256": str(payload.get("rds_sha256", "")),
        "per_cell_sha256": str(payload.get("per_cell_sha256", "")),
    }


def verify_source_binding(
    per_cell: Path, recorded: dict[str, str], *, root: Path
) -> dict[str, str]:
    """Refuse to derive from a table not bound to the declared source.

    Two independent things are checked, and neither alone is enough. The
    sidecar's `rds_sha256` must be the digest `external_data_manifest.tsv`
    declares for EXT-SCRNA-001, so the table came from the deposited object and
    not some other one; and the table on disk must still hash to the
    `per_cell_sha256` written beside it, so it has not been edited or swapped
    since. `--from-per-cell` otherwise accepts any TSV, which is how unrelated
    data could be published under this accession.
    """
    declared = source_digest(root)
    observed_rds = recorded.get("rds_sha256", "")
    observed_table = recorded.get("per_cell_sha256", "")
    if not observed_rds or not observed_table:
        raise Klf12StateError(
            f"{per_cell} is not bound to {ASSET_ID}: its sidecar records no "
            "rds_sha256/per_cell_sha256. Re-extract with --rds so the binding "
            "is recorded, rather than stamping the manifest digest on an "
            "unverified table."
        )
    if observed_rds != declared:
        raise Klf12StateError(
            f"{per_cell} was extracted from an object whose sha256 is "
            f"{observed_rds}, not the {declared} that {ASSET_ID} declares."
        )
    actual = _sha256(per_cell)
    if actual != observed_table:
        raise Klf12StateError(
            f"{per_cell} has changed since extraction: it hashes to {actual}, "
            f"but its sidecar records {observed_table}."
        )
    return {
        "source_sha256_observed": observed_rds,
        "per_cell_sha256": actual,
        "source_binding": "verified",
    }


def extract(rds: Path, destination: Path, *, rscript: str) -> dict[str, str]:
    """Pull the per-cell table out of the deposited object with R."""
    genes = ",".join((GENE, *CONTEXT_GENES))
    with tempfile.NamedTemporaryFile(
        "w", suffix=".R", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(_R_EXTRACT)
        script = handle.name
    try:
        completed = subprocess.run(
            [rscript, script, str(rds), str(destination), genes],
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
    # Bind the table to the object it came from. Without these two digests the
    # sidecar records only which R ran, and a later `--from-per-cell` cannot
    # tell the deposited object's table from any other TSV.
    record = dict(versions)
    record["rds_sha256"] = _sha256(rds)
    record["per_cell_sha256"] = _sha256(destination)
    _sidecar(destination).write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rds", type=Path, help="local copy of the deposited seurat_object.rds"
    )
    parser.add_argument(
        "--from-per-cell",
        type=Path,
        help="re-derive from an already extracted per-cell table; needs no R",
    )
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument(
        "--per-cell-out",
        type=Path,
        help="where to write the extracted per-cell table; it carries row-level "
        "sample metadata and must stay outside the tracked tree",
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args(argv)

    if (args.rds is None) == (args.from_per_cell is None):
        parser.error("give exactly one of --rds or --from-per-cell")

    if args.rds is not None:
        destination = args.per_cell_out or (args.root / "tmp" / "klf12_per_cell.tsv")
        destination.parent.mkdir(parents=True, exist_ok=True)
        versions = extract(args.rds, destination, rscript=args.rscript)
        per_cell = destination
    else:
        per_cell = args.from_per_cell
        # NOT "not_used": the numbers came out of an R session even when this
        # invocation did not open one, so the committed artifact carries the
        # extraction's environment rather than this run's.
        versions = extraction_provenance(per_cell)

    # Bind before deriving. An unbound or mismatched table is refused rather
    # than silently stamped with the manifest digest.
    versions = {**versions, **verify_source_binding(per_cell, versions, root=args.root)}

    findings = derive(per_cell)
    evidence = write_evidence(
        findings, args.root / "docs" / "scrna" / "klf12_state_evidence.tsv"
    )
    report = write_findings(
        findings,
        args.root / "docs" / "scrna" / "klf12_state_findings.json",
        root=args.root,
        r_versions=versions,
    )
    print(f"decision: {findings['decision']}")
    print(f"wrote {evidence.relative_to(args.root)}")
    print(f"wrote {report.relative_to(args.root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
