"""Derive the node-support audit from the deposited single-cell object.

WHAT THIS IS. The implementation of `docs/scrna/node_support_preregistration.md`,
which was committed before this module read any audited expression value. Every
threshold and rule it applies comes from `node_support_contract`, which was
frozen in that same commit; this module contains no criterion of its own.

WHAT IT PRODUCES. Per compartment-unit QC (C1 integrity, C2 specificity, n, E),
per-gene and per-node pseudobulk fractions and detection fractions with
within-donor bootstrap intervals, node support labels, and the within-class
alias verdicts. Committed artifacts carry per-unit aggregates only.

TWO WAYS TO RUN IT.

    --rds <object> --rscript <R>   extract, then derive
    --from-per-cell <table>        re-derive every committed number, no R and
                                   no 2.9 GB object

The second is what makes the artifacts checkable by a reviewer, and it is
required to reproduce the first exactly: the bootstrap is seeded per unit from
the frozen seed and the unit's position in a sorted list, so it does not depend
on iteration order, machine or run.

WHAT IT MUST NOT SEE. Section 10.1 forbids this module from importing
`dt_adoc.simulation`, `dt_adoc.concordance`, `dt_adoc.calibration`,
`dt_adoc.scoring` or `dt_adoc.perturbations`, or reading `docs/concordance/`.
No model output, node occupancy or concordance value may reach the choice of
compartment, layer, gene, threshold or criterion -- all of which were fixed
before extraction anyway. `tests/unit/test_node_support_preregistration.py`
asserts the import boundary rather than trusting this paragraph.

ROW-LEVEL METADATA. The per-cell table carries sample-level metadata and is
written OUTSIDE the repository. Only per-unit aggregates are committed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from dt_adoc.scrna import node_support_contract as C
from dt_adoc.scrna import node_support_expectations as X

ASSET_ID = "EXT-SCRNA-001"
REPO = Path(__file__).resolve().parents[3]
EXTRACTION_SIDECAR_SUFFIX = ".extraction.json"
SCHEMA_VERSION = 1

#: The three context genes. `EPCAM`/`VIM` are C1, `EPCAM`/`COL1A1` are C2.
#: None is a measurement feature of any node (the test asserts it), so
#: extracting them adds no audited value to the table.
CONTEXT_GENES: tuple[str, ...] = ("EPCAM", "VIM", "COL1A1")

_R_EXTRACT = """
suppressPackageStartupMessages(library(SeuratObject))
args <- commandArgs(trailingOnly = TRUE)
obj <- readRDS(args[1])
md <- obj@meta.data
cm <- SeuratObject::LayerData(obj[["RNA"]], layer = "counts")
genes <- strsplit(args[3], ",")[[1]]
present <- genes[genes %in% rownames(cm)]
missing <- setdiff(genes, present)
df <- data.frame(
  sample_id = as.character(md$sample_id),
  celltype_v2 = as.character(md$celltype_v2),
  depth_counts = as.numeric(Matrix::colSums(cm)),
  nfeature_counts = as.integer(Matrix::colSums(cm > 0)),
  stringsAsFactors = FALSE
)
for (g in present) {
  df[[paste0("counts_", g)]] <- as.numeric(cm[g, ])
}
write.table(df, args[2], sep = "\\t", quote = FALSE, row.names = FALSE)
# Absent features are REPORTED, never substituted by an alias. The
# pre-registration forbids adding, substituting or curating a feature, so a
# symbol the object does not carry becomes a recorded gap in that node's
# program rather than a silent swap for a synonym.
cat(sprintf("absent_features\\t%s\\n", paste(missing, collapse = ",")), file = stderr())
cat(sprintf("n_features_total\\t%d\\n", nrow(cm)), file = stderr())
cat(sprintf("r_version\\t%s\\n", R.version.string), file = stderr())
cat(sprintf("seuratobject_version\\t%s\\n",
            as.character(packageVersion("SeuratObject"))), file = stderr())
"""


class NodeSupportError(RuntimeError):
    """The derivation cannot proceed on the evidence it was given."""


@dataclass(frozen=True)
class Unit:
    """One donor x condition x compartment cell group. Never a replicate."""

    donor: str
    condition: str
    compartment: str

    @property
    def unit_id(self) -> str:
        return f"{self.donor}_{self.condition}_{self.compartment}"

    @property
    def sample_id(self) -> str:
        return f"{self.donor}TE_{self.condition}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_unit(sample_id: str) -> tuple[str, str]:
    """Donor and condition, recoverable only from `sample_id`.

    The deposited `meta.data` carries no `patient_id` or `group` column, so this
    parse is the whole of the donor structure available.
    """
    donor, _, condition = sample_id.partition("_")
    if not donor.endswith("TE") or condition not in C.CONDITIONS:
        raise NodeSupportError(f"unparseable sample_id {sample_id!r}")
    return donor[:-2], condition


# --------------------------------------------------------------------------
# Reading the extracted table
# --------------------------------------------------------------------------


@dataclass
class Cells:
    """The extracted cells, grouped by unit, as dense arrays per unit.

    `values` is cells x genes of corrected values; `depth` is each cell's total
    corrected depth over the WHOLE matrix, which is the denominator of `f`.
    """

    genes: tuple[str, ...]
    by_unit: dict[str, np.ndarray]
    depth_by_unit: dict[str, np.ndarray]
    units: dict[str, Unit]
    absent_features: tuple[str, ...]
    n_cells_object: int
    label_counts: dict[str, int]


def read_per_cell(path: Path, absent: tuple[str, ...] = ()) -> Cells:
    """Read the extracted per-cell table into per-unit arrays.

    Cells whose `celltype_v2` is not in the frozen partition would be a silent
    hole in a partition the pre-registration calls complete, so an unknown label
    raises rather than being dropped.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = tuple(reader.fieldnames or ())
        genes = tuple(f[len("counts_") :] for f in fields if f.startswith("counts_"))
        if not genes:
            raise NodeSupportError(f"{path} carries no counts_<gene> column")
        rows_by_unit: dict[str, list[list[float]]] = {}
        depth_by_unit: dict[str, list[float]] = {}
        units: dict[str, Unit] = {}
        label_counts: dict[str, int] = {}
        n_cells = 0
        for row in reader:
            n_cells += 1
            label = row["celltype_v2"]
            label_counts[label] = label_counts.get(label, 0) + 1
            compartment = C.COMPARTMENT_OF_LABEL.get(label)
            if compartment is None:
                raise NodeSupportError(
                    f"{label!r} is not in the frozen compartment partition; the "
                    "pre-registration calls that partition complete over all "
                    "28,212 cells, so this is a contradiction, not a cell to drop"
                )
            donor, condition = parse_unit(row["sample_id"])
            unit = Unit(donor, condition, compartment)
            units.setdefault(unit.unit_id, unit)
            rows_by_unit.setdefault(unit.unit_id, []).append(
                [float(row[f"counts_{g}"]) for g in genes]
            )
            depth_by_unit.setdefault(unit.unit_id, []).append(
                float(row["depth_counts"])
            )
    return Cells(
        genes=genes,
        by_unit={k: np.asarray(v, dtype=np.float64) for k, v in rows_by_unit.items()},
        depth_by_unit={
            k: np.asarray(v, dtype=np.float64) for k, v in depth_by_unit.items()
        },
        units=units,
        absent_features=absent,
        n_cells_object=n_cells,
        label_counts=label_counts,
    )


# --------------------------------------------------------------------------
# Per-unit quantities, with the within-donor bootstrap
# --------------------------------------------------------------------------


@dataclass
class UnitStats:
    """Everything measured on one compartment-unit."""

    unit: Unit
    n_cells: int
    exposure: float
    f: dict[str, float]
    d: dict[str, float]
    f_ci: dict[str, tuple[float, float]]
    d_ci: dict[str, tuple[float, float]]
    min_nonzero: dict[str, float]


def _columns_for(cells: Cells) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Column keys, plus selectors mapping genes to node-level aggregates.

    Gene columns come first and node columns after, because the bootstrap has to
    resample cells ONCE and score every quantity on that same resample. Scoring
    them in separate passes would give each its own resample and make the
    intervals mutually inconsistent.
    """
    gene_index = {g: i for i, g in enumerate(cells.genes)}
    nodes = sorted(C.assessable_nodes())
    keys = [f"gene:{g}" for g in cells.genes] + [f"node:{n}" for n in nodes]
    rows = C.assessable_nodes()
    membership = np.zeros((len(cells.genes), len(nodes)), dtype=np.float64)
    for j, node in enumerate(nodes):
        for gene in C.features(rows[node]):
            if gene in gene_index:
                membership[gene_index[gene], j] = 1.0
    return keys, membership, np.asarray([], dtype=np.float64)


def unit_statistics(cells: Cells, unit_id: str, ordinal: int) -> UnitStats:
    """`f` and `d` for every gene and node, with 95% within-donor intervals.

    THE INTERVAL IS NOT A BIOLOGICAL-REPLICATE INTERVAL. It expresses how
    precisely this donor's sampled cells measure this donor, and nothing else:
    it is never pooled across donors and no across-donor statistic is computed
    from it. Section 5.3 is binding on that.

    The generator is seeded from the frozen seed and the unit's ORDINAL in a
    sorted list, not from iteration order, so `--from-per-cell` reproduces
    `--rds` exactly.
    """
    values = cells.by_unit[unit_id]
    depth = cells.depth_by_unit[unit_id]
    n_cells = int(values.shape[0])
    keys, membership, _ = _columns_for(cells)

    gene_values = values
    node_values = values @ membership
    observed = np.hstack([gene_values, node_values])
    # Node detection is the UNION over the node's features (Section 4.0): a
    # cell detects the node if it carries at least one member. Summing values
    # and then testing > 0 gives the same set, because corrected values are
    # non-negative.
    positive = observed > 0

    exposure = float(depth.sum())
    totals = observed.sum(axis=0)
    f = totals / exposure if exposure > 0 else np.zeros_like(totals)
    d = positive.sum(axis=0) / n_cells if n_cells else np.zeros_like(totals)

    rng = np.random.default_rng([C.BOOTSTRAP_SEED, ordinal])
    f_draws = np.empty((C.BOOTSTRAP_B, observed.shape[1]), dtype=np.float64)
    d_draws = np.empty_like(f_draws)
    positive_f = positive.astype(np.float64)
    chunk = max(1, min(200, C.BOOTSTRAP_B))
    for start in range(0, C.BOOTSTRAP_B, chunk):
        width = min(chunk, C.BOOTSTRAP_B - start)
        idx = rng.integers(0, n_cells, size=(width, n_cells))
        # Resample as cell MULTIPLICITIES: gathering cells x genes per replicate
        # would allocate width x n x columns and buy nothing.
        counts = np.empty((width, n_cells), dtype=np.float64)
        for r in range(width):
            counts[r] = np.bincount(idx[r], minlength=n_cells)
        denominator = counts @ depth
        f_draws[start : start + width] = (counts @ observed) / denominator[:, None]
        d_draws[start : start + width] = (counts @ positive_f) / n_cells

    lo, hi = 100 * C.BOOTSTRAP_ALPHA / 2, 100 * (1 - C.BOOTSTRAP_ALPHA / 2)
    f_lo, f_hi = np.percentile(f_draws, [lo, hi], axis=0)
    d_lo, d_hi = np.percentile(d_draws, [lo, hi], axis=0)
    masked = np.where(observed > 0, observed, np.inf)
    smallest = masked.min(axis=0)

    return UnitStats(
        unit=cells.units[unit_id],
        n_cells=n_cells,
        exposure=exposure,
        f={k: float(v) for k, v in zip(keys, f)},
        d={k: float(v) for k, v in zip(keys, d)},
        f_ci={k: (float(a), float(b)) for k, a, b in zip(keys, f_lo, f_hi)},
        d_ci={k: (float(a), float(b)) for k, a, b in zip(keys, d_lo, d_hi)},
        min_nonzero={
            k: (float(v) if math.isfinite(v) else 0.0) for k, v in zip(keys, smallest)
        },
    )


# --------------------------------------------------------------------------
# QC: C1 integrity and C2 specificity, kept apart
# --------------------------------------------------------------------------


@dataclass
class UnitQC:
    """The two controls, with two failure modes that are never collapsed."""

    unit: Unit
    n_cells: int
    exposure: float
    c1_gene: str
    c1_detection: float
    c1_pass: bool
    c1_evaluated: bool
    c2_gene: str
    c2_own: float
    c2_other: float
    c2_pass: bool
    c2_evaluated: bool
    meets_n_min: bool
    meets_e_min: bool

    @property
    def absence_informative(self) -> bool:
        """C1 gates absence POWER. C2 does not, and must not be folded in.

        A compartment with no C1 gene has no integrity control, so it cannot
        support an absence either -- but for a different reason from failing
        one, which `uninformative_reason` keeps separate.
        """
        return (
            self.c1_evaluated and self.c1_pass and self.meets_n_min and self.meets_e_min
        )

    @property
    def uninformative_reason(self) -> str:
        if not self.meets_n_min:
            return "uninformative_n"
        if not self.meets_e_min:
            return "uninformative_exposure"
        if not self.c1_evaluated:
            # Distinct from failing C1: no integrity control is DEFINED for this
            # compartment, so nothing was measured to fail. Only `myofibroblast`
            # is in this position and it fails `n_min` first in every unit, so
            # this branch does not fire on the committed data -- it is here so
            # the vocabulary cannot quietly conflate "not run" with "failed".
            return "uninformative_no_integrity_control"
        if not self.c1_pass:
            return "uninformative_integrity"
        return ""

    @property
    def attribution(self) -> str:
        """C2 gates compartment ATTRIBUTION only.

        A compartment with no complement in the primary partition -- which is
        `myofibroblast`, and only that -- has no C2 to pass or fail. Reporting
        it as `compartment_attribution_unsafe` would be an accusation the test
        was never run to make, so it is `not_applicable`.
        """
        if not self.c2_evaluated:
            return "not_applicable"
        return "compartment_attribution_unsafe" if not self.c2_pass else "ok"


def unit_qc(stats: dict[str, UnitStats], unit_id: str) -> UnitQC:
    """C1 and C2 for one compartment-unit.

    C2 compares the unit against the COMPLEMENTARY PRIMARY COMPARTMENT of the
    same donor and condition, which is what "the same donor and condition" in
    the pre-registration means. `myofibroblast` has no complement in the primary
    partition, so C2 is not evaluated there and the unit is reported with C2
    recorded as not applicable rather than as a pass.
    """
    this = stats[unit_id]
    unit = this.unit
    # C1 IS DEFINED ONLY FOR THE PRIMARY COMPARTMENTS. `myofibroblast` has no
    # entry in `C1_GENE`, so an earlier revision computed `bool("") and ...` and
    # shipped `c1_pass: false` beside `c1_detection: not_applicable` -- a
    # reported failure for a check that was never run, which is the same defect
    # already corrected for C2. Evaluation is explicit on both controls now.
    c1_gene = C.C1_GENE.get(unit.compartment, "")
    c1_evaluated = bool(c1_gene)
    c1_detection = (
        this.d.get(f"gene:{c1_gene}", float("nan")) if c1_evaluated else float("nan")
    )

    c2_gene = C.C2_GENE.get(unit.compartment, "")
    other = [c for c in C.PRIMARY_COMPARTMENTS if c != unit.compartment]
    complement = Unit(unit.donor, unit.condition, other[0]).unit_id if other else ""
    evaluated = bool(c2_gene) and complement in stats
    if evaluated:
        c2_own = this.d.get(f"gene:{c2_gene}", float("nan"))
        c2_other = stats[complement].d.get(f"gene:{c2_gene}", float("nan"))
        c2_pass = bool(c2_own > c2_other)
    else:
        c2_own = c2_other = float("nan")
        c2_pass = False

    return UnitQC(
        unit=unit,
        n_cells=this.n_cells,
        exposure=this.exposure,
        c1_gene=c1_gene,
        c1_detection=c1_detection,
        c1_pass=c1_evaluated and c1_detection >= C.C1_FLOOR,
        c1_evaluated=c1_evaluated,
        c2_gene=c2_gene,
        c2_own=c2_own,
        c2_other=c2_other,
        c2_pass=c2_pass,
        c2_evaluated=evaluated,
        meets_n_min=this.n_cells >= C.N_MIN,
        meets_e_min=this.exposure >= C.E_MIN,
    )


# --------------------------------------------------------------------------
# Section 4.2 -- support labels
# --------------------------------------------------------------------------


def support_label(
    node: str,
    condition: str,
    stats: dict[str, UnitStats],
    qc: dict[str, UnitQC],
    compartment: str,
) -> dict[str, object]:
    """One node's support label in one condition arm, over the three donors."""
    key = f"node:{node}"
    per_donor = []
    for donor in C.DONORS:
        unit_id = Unit(donor, condition, compartment).unit_id
        if unit_id not in stats:
            per_donor.append({"donor": donor, "present": False})
            continue
        control = qc[unit_id]
        per_donor.append(
            {
                "donor": donor,
                "present": True,
                "d": stats[unit_id].d[key],
                "f": stats[unit_id].f[key],
                "n_cells": stats[unit_id].n_cells,
                "exposure": stats[unit_id].exposure,
                "absence_informative": control.absence_informative,
                "uninformative_reason": control.uninformative_reason,
                "attribution": control.attribution,
            }
        )
    seen = [row for row in per_donor if row.get("present")]
    if len(seen) < len(C.DONORS):
        return {
            "label": "uninformative",
            "reason": "missing_unit",
            "per_donor": per_donor,
        }

    detections = [row["d"] for row in seen]
    if all(value == 0 for value in detections):
        if all(row["absence_informative"] for row in seen):
            label, reason = "not_detected_with_power", ""
        else:
            label = "uninformative"
            reason = next(
                row["uninformative_reason"]
                for row in seen
                if row["uninformative_reason"]
            )
    elif all(value >= C.ROBUST_DETECTION for value in detections):
        label, reason = "robustly_detected", ""
    else:
        label, reason = "sparse_or_low", ""

    record: dict[str, object] = {
        "label": label,
        "reason": reason,
        "per_donor": per_donor,
    }
    if label == "not_detected_with_power":
        # Section 3.1(2): every absence call on the corrected layer alone.
        record["provisional"] = "provisional_corrected_layer_only"
    unsafe = [row["donor"] for row in seen if row["attribution"] != "ok"]
    if unsafe:
        record["attribution"] = "compartment_attribution_unsafe"
        record["attribution_donors"] = unsafe
    # Registered Section 4.1: "Detection values in that unit are still reported
    # and tagged `integrity_failed`, because a depressed `d` in a degraded unit
    # is not evidence of sparseness." Emitted here rather than only promised in
    # the document. No unit fails C1 on this dataset.
    degraded = [
        row["donor"]
        for row in seen
        if row["uninformative_reason"] == "uninformative_integrity"
    ]
    if degraded:
        record["integrity_failed"] = degraded
    return record


# --------------------------------------------------------------------------
# Section 5 -- movement, and the alias test
# --------------------------------------------------------------------------


def gene_movement(
    gene: str, donor: str, compartment: str, stats: dict[str, UnitStats]
) -> str:
    """Whether one gene moves in one donor: separation AND material size."""
    key = f"gene:{gene}"
    cnt_id = Unit(donor, "CNT", compartment).unit_id
    ht_id = Unit(donor, "HT", compartment).unit_id
    if cnt_id not in stats or ht_id not in stats:
        return "uninformative"
    cnt, ht = stats[cnt_id], stats[ht_id]
    lo_c, hi_c = cnt.f_ci[key]
    lo_h, hi_h = ht.f_ci[key]
    separated = hi_c < lo_h or hi_h < lo_c
    # One transcript-equivalent on numerator and denominator, so a zero arm is
    # capped rather than infinite.
    pseudo_c = (cnt.f[key] * cnt.exposure + 1) / (cnt.exposure + 1)
    pseudo_h = (ht.f[key] * ht.exposure + 1) / (ht.exposure + 1)
    fold = math.log2(pseudo_h / pseudo_c) if pseudo_c > 0 else 0.0
    if not separated or abs(fold) < C.LOG2_FOLD_MIN:
        return "no_material_move"
    return "moves_up" if fold > 0 else "moves_down"


def member_verdict(
    node: str, compartment: str, stats: dict[str, UnitStats], qc: dict[str, UnitQC]
) -> dict[str, object]:
    """One class member's arm-level verdict against its Appendix-A direction."""
    programs = C.direction_vote_programs()
    registered = programs[node]
    committed = C.features(C.assessable_nodes()[node])
    if not stats:
        # A bare `StopIteration` from inside a function is a bad failure: it can
        # be swallowed by an enclosing generator and read as "no more results".
        raise NodeSupportError(
            f"member_verdict({node!r}) was given no unit statistics at all"
        )
    measured = next(iter(stats.values())).f
    available = tuple(g for g in registered if f"gene:{g}" in measured)

    # THE GUARD IS ABOUT REDUCTION, NOT ABOUT SIZE. The pre-registration says a
    # program "reduced below 2 voting genes BY R1/R2" cannot be direction-called,
    # and its own table enumerates eleven programs with one voting gene --
    # `E_PAEP`, `S_PRL`, `S_IGFBP1`, `E_IHH` and the rest. Those were never
    # reduced; they measure one gene by construction, and that gene decides.
    # Reading the guard as "fewer than two genes" instead would make eleven of
    # the twenty alias members permanently undecidable and would contradict the
    # observation map, which records that a `S_PRL`/`S_IGFBP1` divergence "is a
    # FALSIFICATION of the aliasing, not a limit on the assay". An earlier
    # revision of this module read it that way and returned `uninformative` for
    # every single-gene member.
    if len(committed) >= C.MIN_VOTING_GENES and len(registered) < C.MIN_VOTING_GENES:
        return {
            "verdict": "uninformative",
            "reason": "program_reduced_below_two_by_r1_r2",
            "program": list(registered),
        }
    if not available:
        return {
            "verdict": "uninformative",
            "reason": "all_features_absent_from_object",
            "program": [],
            "absent": list(registered),
        }
    # A feature the object does not carry is a recorded gap, never a substituted
    # synonym (Section 2). If that gap takes a multi-gene program below two, the
    # agreement rule has nothing to apply.
    if len(registered) >= C.MIN_VOTING_GENES and len(available) < C.MIN_VOTING_GENES:
        return {
            "verdict": "uninformative",
            "reason": "features_absent_from_object",
            "program": list(available),
            "absent": [g for g in registered if g not in available],
        }
    program = available

    per_donor: dict[str, str] = {}
    votes: dict[str, dict[str, str]] = {}
    for donor in C.DONORS:
        moves = {
            gene: gene_movement(gene, donor, compartment, stats) for gene in program
        }
        votes[donor] = moves
        # A DONOR WHOSE COMPARTMENT-UNIT WAS NEVER MEASURED SUPPLIES NOTHING.
        # `gene_movement` returns `uninformative` for a missing unit, and an
        # earlier revision folded that into `no_material_move` along with every
        # other non-call, so an unmeasured donor became evidence of NON-MOVEMENT
        # and could carry a `divergent` verdict by itself. Section 5.3 lists
        # `uninformative` as a per-donor outcome in its own right. Latent on this
        # dataset -- all twelve primary units exist -- but a zero-cell
        # compartment-unit is real here (`SZ09_HT_myofibroblast`), so the guard
        # is not hypothetical.
        if any(value == "uninformative" for value in moves.values()):
            per_donor[donor] = "uninformative"
            continue
        up = sum(v == "moves_up" for v in moves.values())
        down = sum(v == "moves_down" for v in moves.values())
        if len(program) == 1:
            # One voting gene: that gene decides. Eleven of the twenty members
            # are in this case, by the frozen table in Section 2.1.
            called = next(iter(moves.values()))
            called = called if called in {"moves_up", "moves_down"} else None
        elif len(program) == C.MIN_VOTING_GENES:
            # At exactly two, both must agree.
            called = "moves_up" if up == 2 else "moves_down" if down == 2 else None
        else:
            # Above two, a strict majority must agree.
            called = (
                "moves_up"
                if up * 2 > len(program)
                else "moves_down"
                if down * 2 > len(program)
                else None
            )
        per_donor[donor] = called or "no_material_move"

    expected = next(
        r["expected_cnt_to_ht"]
        for r in X.expectation_table()
        if r["model_node"] == node
    )
    wanted = "moves_up" if expected == "OFF -> ON" else "moves_down"
    against = "moves_down" if wanted == "moves_up" else "moves_up"
    calls = list(per_donor.values())
    if any(call == "uninformative" for call in calls):
        # Both evidential verdicts require 3/3, so an arm missing a donor can
        # reach neither.
        verdict = "uninformative"
    elif all(call == wanted for call in calls):
        verdict = "concordant_with_alias"
    elif all(call == "no_material_move" for call in calls) or all(
        call == against for call in calls
    ):
        verdict = "divergent"
    else:
        verdict = "inconsistent"

    # Registered Section 4.1: a C1 failure tags a unit's detection values, and a
    # C2 failure makes its compartment attribution unsafe. `qc` is consulted here
    # so the alias test records those rather than accepting the parameter and
    # ignoring it. Neither tag fires on this dataset: all twelve primary units
    # pass both controls.
    def _donors_failing(predicate) -> list[str]:
        return sorted(
            {
                stats[unit].unit.donor
                for unit in stats
                if stats[unit].unit.compartment == compartment
                and unit in qc
                and predicate(qc[unit])
            }
        )

    record: dict[str, object] = {
        "verdict": verdict,
        "expected_cnt_to_ht": expected,
        "per_donor": per_donor,
        "votes": votes,
        "program": list(program),
        "absent_from_object": [g for g in registered if g not in available],
    }
    degraded = _donors_failing(
        lambda control: control.c1_evaluated and not control.c1_pass
    )
    if degraded:
        record["integrity_failed"] = degraded
    unsafe = _donors_failing(
        lambda control: control.c2_evaluated and not control.c2_pass
    )
    if unsafe:
        record["compartment_attribution_unsafe"] = unsafe
    return record


def _without_single_gene_members(members: dict[str, dict[str, object]]) -> str:
    """The class verdict under the REJECTED reading of the Section 2.1 guard.

    Deviation D1 re-read "a program reduced below 2 voting genes by R1/R2" as a
    reduction test rather than a size test. This recomputes the verdict as if
    the rejected reading held -- every single-gene member `uninformative` -- so
    the artifact carries the counterfactual rather than only the claim.
    """
    programs = C.direction_vote_programs()
    rejected = {
        node: (
            {"verdict": "uninformative"}
            if len(programs.get(node, ())) < C.MIN_VOTING_GENES
            else {"verdict": row["verdict"]}
        )
        for node, row in members.items()
    }
    return class_verdict(rejected)


def class_verdict(members: dict[str, dict[str, object]]) -> str:
    """Section 5.4, and the distinction that must not be collapsed.

    SECTION 5.4 DOES NOT PARTITION THE POSSIBLE PATTERNS, and this returns a
    distinct value rather than pretending it does. Its four verdicts are
    `alias_challenged` (>=1 concordant AND >=1 divergent), `rule_challenged`
    (all callable members divergent TOGETHER), `consistent_with_alias` (all
    concordant) and `uninformative`, whose stated condition is "fewer than two
    direction-callable members". A class whose callable members are a mix of
    `divergent` and `inconsistent`, or all `inconsistent`, meets none of them:
    it has plenty of callable members, so calling it `uninformative` would
    assert something false about the evidence.

    That gap was found after extraction, so it is NOT closed by inventing a
    fifth verdict with consequences. `unclassified_by_section_5_4` licenses
    nothing, carries the member census with it, and is reported to the owner as
    a gap in the frozen vocabulary.
    """
    callable_ = {
        node: row["verdict"]
        for node, row in members.items()
        if row["verdict"] != "uninformative"
    }
    if len(callable_) < 2:
        return "uninformative"
    verdicts = set(callable_.values())
    if "concordant_with_alias" in verdicts and "divergent" in verdicts:
        return "alias_challenged"
    if verdicts == {"divergent"}:
        return "rule_challenged"
    if verdicts == {"concordant_with_alias"}:
        return "consistent_with_alias"
    return "unclassified_by_section_5_4"


# --------------------------------------------------------------------------
# Phase A -- interpretability, derived from the map before any value is read
# --------------------------------------------------------------------------


def interpretability_rows() -> list[dict[str, str]]:
    """Section 7's three axes, from the committed map, with no expression data."""
    rows = []
    for node, row in sorted(C.assessable_nodes().items()):
        measurement = C.measurement_type(row)
        ceiling = row["claim_ceiling"]
        resolution = row["measurement_resolution"]
        haystack = f"{ceiling} {resolution}".lower()
        if measurement == "direct_transcript":
            presence = "direct_biological_availability"
        elif measurement in {
            "gene_program",
            "pathway_score",
            "regulon_or_activity_proxy",
        }:
            # A program or regulon readout supports PROGRAM ACTIVITY and never
            # the node's Boolean state: Section 6 forbids upgrading any of these
            # to "node confirmed".
            presence = "supports_program_activity"
        else:
            presence = "availability_only"
        # A node whose meaning is post-translational, spatial or complex-level
        # cannot be informed by absence, whatever the measurement shows.
        if any(
            token in haystack
            for token in (
                "apical",
                "spatial",
                "surface",
                "secret",
                "nuclear localisation",
                "phospho",
                "complex formation",
                "engaged",
                "cleaved",
            )
        ):
            absence = "cannot_inform_functional_state"
        elif measurement == "direct_transcript":
            absence = "challenges_contemporaneous_expression"
        else:
            absence = "challenges_constitutive_or_active_use"
        rows.append(
            {
                "model_node": node,
                "compartment": row["compartment"],
                "v04_function_class": row["v04_function_class"] or "-",
                "measurement_type": measurement,
                "presence_can_establish": presence,
                "convincing_absence_can_establish": absence,
                "phenotype_inert": row["phenotype_inert"],
                "not_blind": str(node in C.NOT_BLIND_NODES).lower(),
                "measurement_features": row["measurement_features"],
            }
        )
    return rows


# --------------------------------------------------------------------------
# Extraction and provenance
# --------------------------------------------------------------------------


def source_digest(root: Path) -> str:
    path = root / "config/external_data_manifest.tsv"
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["asset_id"] == ASSET_ID:
                return row["sha256"]
    raise NodeSupportError(f"{ASSET_ID} is not in {path}")


def _sidecar(per_cell: Path) -> Path:
    return per_cell.with_name(per_cell.name + EXTRACTION_SIDECAR_SUFFIX)


def extraction_provenance(per_cell: Path) -> dict[str, str]:
    path = _sidecar(per_cell)
    unknown = "unknown_extraction_environment"
    if not path.is_file():
        return {
            "r_version": unknown,
            "seuratobject_version": unknown,
            "rds_sha256": "",
            "per_cell_sha256": "",
            "absent_features": "",
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {key: str(payload.get(key, "")) for key in payload}


def verify_source_binding(
    per_cell: Path, recorded: dict[str, str], *, root: Path
) -> dict[str, str]:
    """Refuse to derive from a table not bound to the declared source."""
    declared = source_digest(root)
    observed_rds = recorded.get("rds_sha256", "")
    observed_table = recorded.get("per_cell_sha256", "")
    if not observed_rds or not observed_table:
        raise NodeSupportError(
            f"{per_cell} is not bound to {ASSET_ID}: its sidecar records no "
            "rds_sha256/per_cell_sha256. Re-extract with --rds."
        )
    if observed_rds != declared:
        raise NodeSupportError(
            f"{per_cell} was extracted from an object whose sha256 is "
            f"{observed_rds}, not the {declared} that {ASSET_ID} declares."
        )
    actual = _sha256(per_cell)
    if actual != observed_table:
        raise NodeSupportError(
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
    genes = ",".join(sorted({*C.audited_genes(), *CONTEXT_GENES}))
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
        raise NodeSupportError(f"R extraction failed: {completed.stderr.strip()[:800]}")
    record: dict[str, str] = {}
    for line in completed.stderr.splitlines():
        key, _, value = line.partition("\t")
        if key in {
            "r_version",
            "seuratobject_version",
            "absent_features",
            "n_features_total",
        }:
            record[key] = value.strip()
    record["rds_sha256"] = _sha256(rds)
    record["per_cell_sha256"] = _sha256(destination)
    _sidecar(destination).write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


# --------------------------------------------------------------------------
# Derivation and artifacts
# --------------------------------------------------------------------------


#: The classes the raw-layer sensitivity speaks to, and the genes it read.
#: `AC01` is the only finding licensing mechanistic reconsideration, and
#: registered Section 3.2 binds presence as well as absence, so its two
#: load-bearing genes were re-derived on raw UMIs.
RAW_SENSITIVITY = REPO / "docs/scrna/node_support_raw_sensitivity.json"
RAW_SENSITIVITY_CLASS = "AC01"


def raw_sensitivity_link(root: Path) -> dict[str, object]:
    """The raw-layer result, linked by path and digest rather than by prose.

    A future unit is likely to read this JSON and never open
    `node_support_finding.md`, so the answer to "has the condition-entanglement
    caveat been discharged for this verdict, and on what evidence" has to be in
    the file. An absent sensitivity is reported as `not_assessed`, never as
    resolved.
    """
    path = root / RAW_SENSITIVITY.relative_to(REPO)
    if not path.is_file():
        return {
            "condition_entanglement_status": "not_assessed",
            "artifact": str(RAW_SENSITIVITY.relative_to(REPO)),
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    verdict = payload.get("verdict", {})
    reproduced = verdict.get("divergence_reproduced_on_raw")
    genes = ",".join(payload.get("provenance", {}).get("genes", []))
    return {
        "artifact": str(RAW_SENSITIVITY.relative_to(REPO)),
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "divergence_reproduced_on_raw": reproduced,
        "genes_re_derived": payload.get("provenance", {}).get("genes", []),
        # Scoped deliberately. The sensitivity read two genes, so it discharges
        # Section 3.2 for those two and for nothing else in this audit.
        "condition_entanglement_status": (
            f"resolved_for_{genes.replace(',', '_')}_only"
            if reproduced
            else "not_resolved"
            if reproduced is False
            else "not_assessed"
        ),
    }


def derive(cells: Cells, *, root: Path = REPO) -> dict[str, object]:
    """Everything the audit computes, from the extracted cells."""
    ordered = sorted(cells.by_unit)
    stats = {
        unit_id: unit_statistics(cells, unit_id, ordinal)
        for ordinal, unit_id in enumerate(ordered)
    }
    qc = {unit_id: unit_qc(stats, unit_id) for unit_id in ordered}

    rows = C.assessable_nodes()
    support: dict[str, dict[str, object]] = {}
    for node, row in sorted(rows.items()):
        compartment = C.COMPARTMENT_OF_NODE.get(row["compartment"])
        if compartment is None:
            continue
        support[node] = {
            arm: support_label(node, arm, stats, qc, compartment)
            for arm in C.CONDITIONS
        }

    classes: dict[str, object] = {}
    for name in C.ALIAS_TEST_ORDER:
        members = {
            node: member_verdict(
                node, C.COMPARTMENT_OF_NODE[row["compartment"]], stats, qc
            )
            for node, row in sorted(rows.items())
            if row["v04_function_class"] == name
            and row["compartment"] in C.COMPARTMENT_OF_NODE
        }
        census: dict[str, int] = {}
        for row in members.values():
            key = str(row["verdict"])
            census[key] = census.get(key, 0) + 1
        resolved = class_verdict(members)
        # A FUTURE READER OF THIS FILE MAY NEVER OPEN THE DEVIATIONS DOCUMENT.
        # `AC01`'s verdict depends entirely on deviation D1, a post-extraction
        # re-reading of the direction-vote guard, and under the rejected reading
        # it is `unclassified_by_section_5_4` and licenses nothing. That
        # dependence was recorded only in prose, so the next unit -- which is
        # likely to ingest this JSON rather than the prose -- could have taken
        # the stronger claim without its condition. It is machine-readable here.
        counterfactual = _without_single_gene_members(members)
        provenance = {
            "depends_on_deviations": (["D1"] if counterfactual != resolved else []),
            "registration_status": (
                "post_extraction_semantic_repair"
                if counterfactual != resolved
                else "as_registered"
            ),
            "counterfactual_verdict_without_D1": counterfactual,
            "licenses_structural_change": resolved
            in {"alias_challenged", "rule_challenged"},
            "see": "docs/scrna/node_support_deviations.md",
        }
        if name == RAW_SENSITIVITY_CLASS:
            provenance["raw_layer_sensitivity"] = raw_sensitivity_link(root)
        classes[name] = {
            "members": members,
            "class_verdict": resolved,
            "decision_provenance": provenance,
            "member_census": census,
            "direction_callable_members": sum(
                1 for row in members.values() if row["verdict"] != "uninformative"
            ),
        }

    # The grid has 3 x 2 x 3 = 18 cells, but a cell containing no cells writes
    # no row, and one does: `SZ09` has no `myofibroblast` cells in the HT arm.
    # Recorded rather than left to be noticed, so a reader reconciling the grid
    # against the artifact can tell "never existed" from "dropped".
    expected = [
        Unit(donor, condition, compartment).unit_id
        for donor in C.DONORS
        for condition in C.CONDITIONS
        for compartment in sorted(set(C.COMPARTMENT_OF_LABEL.values()))
    ]
    empty = [unit_id for unit_id in expected if unit_id not in stats]

    return {
        "schema_version": SCHEMA_VERSION,
        "stats": stats,
        "qc": qc,
        "grid_cells_expected": len(expected),
        "units_written": len(stats),
        "empty_units": empty,
        "support": support,
        "classes": classes,
        "absent_features": list(cells.absent_features),
        "n_cells_object": cells.n_cells_object,
        "label_counts": cells.label_counts,
    }


def _write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise NodeSupportError(f"refusing to write an empty table to {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_artifacts(findings: dict[str, object], *, root: Path) -> list[Path]:
    """Per-unit aggregates only. The per-cell table stays outside the repo."""
    out = root / "docs/scrna"
    written: list[Path] = []

    _write_tsv(out / "node_rna_interpretability.tsv", interpretability_rows())
    written.append(out / "node_rna_interpretability.tsv")

    qc: dict[str, UnitQC] = findings["qc"]  # type: ignore[assignment]
    _write_tsv(
        out / "node_support_qc.tsv",
        [
            {
                "unit_id": control.unit.unit_id,
                "donor": control.unit.donor,
                "condition": control.unit.condition,
                "compartment": control.unit.compartment,
                "primary": str(
                    control.unit.compartment in C.PRIMARY_COMPARTMENTS
                ).lower(),
                "n_cells": control.n_cells,
                "exposure": f"{control.exposure:.6g}",
                "meets_n_min": str(control.meets_n_min).lower(),
                "meets_e_min": str(control.meets_e_min).lower(),
                "c1_gene": control.c1_gene or "-",
                "c1_detection": (
                    f"{control.c1_detection:.6f}"
                    if control.c1_evaluated
                    else "not_applicable"
                ),
                "c1_pass": (
                    str(control.c1_pass).lower()
                    if control.c1_evaluated
                    else "not_applicable"
                ),
                "c1_evaluated": str(control.c1_evaluated).lower(),
                "c2_gene": control.c2_gene or "-",
                "c2_own": (
                    f"{control.c2_own:.6f}"
                    if control.c2_evaluated
                    else "not_applicable"
                ),
                "c2_complement": (
                    f"{control.c2_other:.6f}"
                    if control.c2_evaluated
                    else "not_applicable"
                ),
                "c2_pass": (
                    str(control.c2_pass).lower()
                    if control.c2_evaluated
                    else "not_applicable"
                ),
                "absence_informative": str(control.absence_informative).lower(),
                "uninformative_reason": control.uninformative_reason or "-",
                "attribution": control.attribution,
            }
            for _, control in sorted(qc.items())
        ],
    )
    written.append(out / "node_support_qc.tsv")

    stats: dict[str, UnitStats] = findings["stats"]  # type: ignore[assignment]
    evidence: list[dict[str, object]] = []
    for unit_id, row in sorted(stats.items()):
        for key in sorted(row.f):
            kind, _, name = key.partition(":")
            evidence.append(
                {
                    "unit_id": unit_id,
                    "donor": row.unit.donor,
                    "condition": row.unit.condition,
                    "compartment": row.unit.compartment,
                    "level": kind,
                    "name": name,
                    "n_cells": row.n_cells,
                    "exposure": f"{row.exposure:.6g}",
                    "f": f"{row.f[key]:.6e}",
                    "f_ci_lo": f"{row.f_ci[key][0]:.6e}",
                    "f_ci_hi": f"{row.f_ci[key][1]:.6e}",
                    "d": f"{row.d[key]:.6f}",
                    "d_ci_lo": f"{row.d_ci[key][0]:.6f}",
                    "d_ci_hi": f"{row.d_ci[key][1]:.6f}",
                    "min_nonzero_value": f"{row.min_nonzero[key]:.6e}",
                }
            )
    _write_tsv(out / "node_support_evidence.tsv", evidence)
    written.append(out / "node_support_evidence.tsv")
    return written


def _finite(value: float) -> float | None:
    """`None` for a quantity that was never computed.

    The artifact is read by tools outside Python. `json.dumps` emits a bare
    `NaN` for a float NaN, which is not JSON at all and which strict parsers
    reject -- and it reads as "this was measured and came out undefined" rather
    than "this was not evaluated". `null` beside an explicit status says the
    second, which is what is true of `myofibroblast`'s C2.
    """
    return None if math.isnan(value) else float(value)


def _jsonable(findings: dict[str, object]) -> dict[str, object]:
    qc: dict[str, UnitQC] = findings["qc"]  # type: ignore[assignment]
    stats: dict[str, UnitStats] = findings["stats"]  # type: ignore[assignment]
    return {
        "schema_version": findings["schema_version"],
        "layer": "deposited counts layer (decontX-corrected, non-integer)",
        "layer_caveat": (
            "Every absence call here is provisional_corrected_layer_only: the raw "
            "per-sample matrices are not on local disk and detection invariance "
            "was established for KLF12 only, in the epithelium only."
        ),
        "n_cells_object": findings["n_cells_object"],
        "label_counts": findings["label_counts"],
        "grid_cells_expected": findings["grid_cells_expected"],
        "units_written": findings["units_written"],
        "empty_units": findings["empty_units"],
        "absent_features": findings["absent_features"],
        "units": {
            unit_id: {
                "n_cells": control.n_cells,
                "exposure": control.exposure,
                "c1_gene": control.c1_gene or None,
                "c1_detection": _finite(control.c1_detection),
                "c1_pass": control.c1_pass if control.c1_evaluated else None,
                "c1_evaluated": control.c1_evaluated,
                "c2_gene": control.c2_gene or None,
                "c2_own": _finite(control.c2_own),
                "c2_complement": _finite(control.c2_other),
                "c2_pass": control.c2_pass if control.c2_evaluated else None,
                "c2_evaluated": control.c2_evaluated,
                "meets_n_min": control.meets_n_min,
                "meets_e_min": control.meets_e_min,
                "absence_informative": control.absence_informative,
                "uninformative_reason": control.uninformative_reason,
                "attribution": control.attribution,
            }
            for unit_id, control in sorted(qc.items())
        },
        "node_support": findings["support"],
        "alias_classes": findings["classes"],
        "unit_cell_counts": {k: v.n_cells for k, v in sorted(stats.items())},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rds", type=Path)
    parser.add_argument("--from-per-cell", type=Path)
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--per-cell-out", type=Path)
    parser.add_argument("--root", type=Path, default=REPO)
    parser.add_argument(
        "--no-write", action="store_true", help="derive and print, commit nothing"
    )
    args = parser.parse_args(argv)

    if (args.rds is None) == (args.from_per_cell is None):
        parser.error("pass exactly one of --rds or --from-per-cell")

    if args.rds is not None:
        destination = args.per_cell_out or (
            Path.home() / "ext/dt_adoc_node_support/node_support_per_cell.tsv"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        versions = extract(args.rds, destination, rscript=args.rscript)
        per_cell = destination
    else:
        per_cell = args.from_per_cell
        versions = extraction_provenance(per_cell)

    versions = {**versions, **verify_source_binding(per_cell, versions, root=args.root)}
    absent = tuple(f for f in versions.get("absent_features", "").split(",") if f)
    cells = read_per_cell(per_cell, absent)
    findings = derive(cells, root=args.root)

    payload = _jsonable(findings)
    payload["provenance"] = {
        "asset_id": ASSET_ID,
        **{k: v for k, v in versions.items() if k != "absent_features"},
        "bootstrap_b": C.BOOTSTRAP_B,
        "bootstrap_seed": C.BOOTSTRAP_SEED,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
    }
    if not args.no_write:
        written = write_artifacts(findings, root=args.root)
        target = args.root / "docs/scrna/node_support_findings.json"
        target.write_text(
            json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        written.append(target)
        for path in written:
            print(f"wrote {path.relative_to(args.root)}")
    else:
        print(json.dumps(payload, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
