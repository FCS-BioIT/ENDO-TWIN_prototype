"""The concordance figure: what the twin predicts, and the mechanism behind it.

Four panels, each answering one question a reader asks in order:

* **A. Does it reproduce the functional endpoint?** Observed adhesion with its
  Wilson interval against the simulated value at both horizons, with each arm's
  evidence role on the axis. This is the only panel where a number is compared
  to a number, and it is the only place a magnitude failure can be seen.
* **B. Does it reproduce the molecular readouts?** A direction-only scorecard.
  Deliberately not a heatmap of values: a pg/mL concentration and a Boolean
  trajectory frequency have no common scale, and no validated observation model
  exists to give them one. Plotting them on a shared axis would manufacture the
  comparison the repository forbids.
* **C. What generates the predictions?** The reduced mechanism, drawn only from
  nodes on the carrying paths of the panel A and B readouts, with alias classes
  collapsed into one box because they are one Boolean function.
* **D. How much of the evidence can the model touch at all?** Coverage of all
  60 curated rows, so panels A-C are read against the right denominator.

Colour follows the dataviz contract: the categorical slots are taken in fixed
order from the validated reference palette and were re-validated for the exact
subsets used here (panel A all-pairs, panel D adjacent). Three slots sit below
3:1 against the surface, so every segment and marker carries a visible direct
label as the required relief rather than relying on hue.

Panel C uses two hues plus neutrals and adds shape and texture, because a
network laid out in two dimensions is an all-pairs case where more hues would
not clear the colour-vision floor. Node identity there is carried by the printed
node name, never by colour alone.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from dt_adoc.concordance.simulate import ArmRun
    from dt_adoc.reporting.structure import StructuralFacts

from dt_adoc.concordance.table import ConcordanceRow

# Validated categorical slots (light mode) from the dataviz reference palette.
SERIES_OBSERVED = "#2a78d6"
SERIES_CONVERGED = "#eb6834"
SERIES_DECLARED = "#1baf7a"

COVERAGE_COLORS = {
    "not_expressible_by_model_class": "#2a78d6",
    "not_assessable_with_current_data": "#eb6834",
    "calibration_circular_agreement": "#1baf7a",
    "directional_agreement": "#eda100",
    "partial_agreement": "#e87ba4",
    "disagreement": "#008300",
    "structural_falsification": "#4a3aa7",
}

TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"
GRID = "#d9d8d4"

#: Observed adhesion, verbatim from `config/calibration.yaml`. Per-embryo binary
#: outcomes; the denominator is embryos, never donors.
OBSERVED_ADHESION: dict[str, tuple[int, int, str]] = {
    "untreated": (0, 12, "calibration"),
    "hormone_treated": (9, 19, "calibration"),
    "mifepristone": (1, 8, "held out"),
}

ARM_LABELS = {
    "untreated": "Untreated",
    "hormone_treated": "Hormone-treated",
    "mifepristone": "HT + mifepristone",
}


@dataclass(frozen=True)
class ScorecardEntry:
    """One molecular readout's direction-only verdict.

    ``status`` is derived from the concordance table's ``concordance_class``,
    never written by hand. An earlier revision of this panel hand-wrote PRL as a
    directional agreement while the curated matrix recorded it as **not
    assessable** -- its mappings (OM-006/014/015) are provisional or
    context_only, so no directional verdict is licensed at all. Deriving the
    status makes that class of drift impossible rather than merely discouraged.
    """

    label: str
    node_id: str
    result_id: str
    status: str
    observed_direction: str
    magnitude_comparable: str
    evidence_role: str
    footnote: str


#: How a concordance class reads on the scorecard. Deliberately none of these is
#: a bare tick: three of the four rows are either circular or unassessable, and a
#: pass mark would misreport all three.
SCORECARD_STATUS = {
    "calibration_circular_agreement": "direction agrees - but circular",
    "directional_agreement": "direction agrees",
    "partial_agreement": "direction agrees, magnitude fails",
    "disagreement": "disagrees",
    "structural_falsification": "structurally falsified",
    "not_assessable_with_current_data": "NOT ASSESSABLE",
    "not_expressible_by_model_class": "outside the model class",
}


def wilson_interval(
    successes: int, trials: int, z: float = 1.96
) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Wilson rather than Wald because three of these counts are at or next to a
    boundary (0/12, 1/8), where a Wald interval is degenerate or crosses zero.
    The interval describes sampling error in a per-embryo assay outcome and is
    not a donor-level or clinical interval.
    """
    if trials == 0:
        return (0.0, 0.0)
    phat = successes / trials
    denominator = 1 + z * z / trials
    center = (phat + z * z / (2 * trials)) / denominator
    margin = (
        z
        * sqrt(phat * (1 - phat) / trials + z * z / (4 * trials * trials))
        / denominator
    )
    return (max(0.0, center - margin), min(1.0, center + margin))


def scorecard_entries(rows: list[ConcordanceRow]) -> tuple[ScorecardEntry, ...]:
    """The molecular readouts, with what each comparison can and cannot say.

    The status comes from the row's ``concordance_class``; only the explanatory
    text, which the table has no column for, is written here.

    PAEP and IGFBP-1 are circular: OM-001 is the feasibility gate on the retained
    ensemble and OM-002 the reported diagnostic, so agreeing with either is
    agreeing with the filter. PRL is not assessable at all. The scRNA states have
    no mapping because the repository holds no annotated object.
    """
    by_id = {row.result_id: row for row in rows}
    spec = (
        (
            "PAEP (secreted)",
            "E_PAEP",
            "R15b",
            "up, full cocktail vs E2-only (5/5 chips, 9.5-57.6x)",
            "no: a 57.6x ratio has no image in {0,1}",
            "calibration (OM-001 feasibility gate)",
            "agreement here is agreement with the filter, not validation",
        ),
        (
            "IGFBP-1 (secreted)",
            "S_IGFBP1",
            "R12b",
            "up day 0 to day 6 in 3/5 column positions",
            "no: saturates to 1.0 at the converged horizon",
            "calibration (OM-002 diagnostic)",
            "chip and donor mapping LOST; not a within-unit trajectory",
        ),
        (
            "PRL (secreted)",
            "S_PRL",
            "R12c",
            "heterogeneous LATE onset: 0/6 day 0, 1/6 day 3, 3/6 day 6",
            "not compared: no directional verdict is licensed",
            "OM-006/014/015 provisional or context_only",
            "same Boolean function as S_IGFBP1, so not an independent readout",
        ),
        (
            "scRNA epithelial / stromal states",
            "(none)",
            "R23",
            "paper reports 7 populations over 28,212 cells",
            "no mapping exists",
            "not assessable",
            "the local object is pre-annotation; see scrna_object_audit.json",
        ),
    )
    entries = []
    for label, node_id, result_id, observed, magnitude, role, footnote in spec:
        row = by_id[result_id]
        entries.append(
            ScorecardEntry(
                label=label,
                node_id=node_id,
                result_id=result_id,
                status=SCORECARD_STATUS[row.concordance_class],
                observed_direction=observed,
                magnitude_comparable=magnitude,
                evidence_role=role,
                footnote=footnote,
            )
        )
    return tuple(entries)


def write_figure_source_data(
    *,
    rows: list[ConcordanceRow],
    runs: dict[tuple[str, str], ArmRun],
    facts: StructuralFacts,
    destination: Path,
) -> Path:
    """Emit exactly the numbers the figure draws, one row per plotted quantity.

    Written before the figure is rendered and read back by it, so a reader can
    check every mark against a tracked table and the figure cannot silently plot
    something the table does not contain.
    """
    records: list[dict[str, str]] = []

    for arm_id, (successes, trials, role) in OBSERVED_ADHESION.items():
        low, high = wilson_interval(successes, trials)
        records.append(
            {
                "panel": "A",
                "arm": arm_id,
                "quantity": "observed_proportion",
                "value": f"{successes / trials:.6f}",
                "ci_low": f"{low:.6f}",
                "ci_high": f"{high:.6f}",
                "n": f"{successes}/{trials}",
                "unit": "embryo (per-embryo binary outcome)",
                "evidence_role": role,
                "source": "config/calibration.yaml adhesion_objective",
            }
        )
        for horizon, series in (
            ("converged", "simulated_converged"),
            ("declared", "simulated_declared"),
        ):
            run = runs.get((arm_id, horizon))
            if run is None:
                continue
            mean = run.node_mean.get("OUT_STABLE_ADHESION")
            if mean is None:
                continue
            # No interval is emitted for a simulated point, and panel A draws
            # none. The across-seed spread is recorded in `n` as a labelled
            # diagnostic; writing it into ci_low/ci_high would put an interval on
            # the figure's source data that nothing here can justify, and it is
            # exactly zero for the near-zero arms in any case. The binomial
            # plug-in that used to sit beside it is WITHDRAWN, not merely
            # unused: it is the wrong variance family for a time-averaged
            # occupancy (docs/maboss_estimator_semantics.md section 3d). The
            # Wilson interval drawn for the OBSERVED counts above is unaffected.
            spread = run.node_sd.get("OUT_STABLE_ADHESION", 0.0)
            records.append(
                {
                    "panel": "A",
                    "arm": arm_id,
                    "quantity": series,
                    "value": f"{mean:.6f}",
                    "ci_low": "",
                    "ci_high": "",
                    "n": (
                        f"{run.trajectory_count} trajectories x "
                        f"{len(run.seeds)} seeds; across-seed spread {spread:.6f} "
                        "(DIAGNOSTIC ONLY, not a validated uncertainty)"
                    ),
                    "unit": (
                        "MaBoSS trajectory frequency (dimensionless); NO interval "
                        "is given, because this repository has no validated "
                        "characterisation of this estimator"
                    ),
                    "evidence_role": role,
                    "source": "docs/concordance/run_settings.json",
                }
            )

    for entry in scorecard_entries(rows):
        records.append(
            {
                "panel": "B",
                "arm": entry.node_id,
                "quantity": f"direction_only_scorecard ({entry.result_id})",
                "value": entry.status,
                "ci_low": "",
                "ci_high": "",
                "n": "",
                "unit": "direction only; no validated observation model",
                "evidence_role": entry.evidence_role,
                "source": "docs/concordance/concordance_table.tsv",
            }
        )

    from dt_adoc.concordance.render import PANEL_C_EDGES, PANEL_C_NODES

    for key, spec in PANEL_C_NODES.items():
        records.append(
            {
                "panel": "C",
                "arm": key,
                "quantity": "mechanism_node",
                # TSV cannot hold a raw newline, so the box's line breaks are
                # escaped here and restored by the renderer. Flattening them
                # instead would make multi-line labels overflow their boxes.
                "value": spec["label"].replace("\n", "\\n"),
                "ci_low": "",
                "ci_high": "",
                "n": str(spec["n"]),
                "unit": f"{spec['cls']}; box_kind={spec['kind']}",
                "evidence_role": ";".join(spec["members"]),
                "source": "docs/concordance/mechanism_nodes.tsv",
            }
        )
    for edge_from, edge_to, kind in PANEL_C_EDGES:
        records.append(
            {
                "panel": "C",
                "arm": f"{edge_from}->{edge_to}",
                "quantity": "mechanism_edge",
                "value": kind,
                "ci_low": "",
                "ci_high": "",
                "n": "",
                "unit": "dependency",
                "evidence_role": "",
                "source": f"models/superset/{facts.model_version}/network.bnd",
            }
        )

    counts: dict[str, int] = {}
    for row in rows:
        counts[row.concordance_class] = counts.get(row.concordance_class, 0) + 1
    for concordance_class, count in sorted(counts.items()):
        records.append(
            {
                "panel": "D",
                "arm": concordance_class,
                "quantity": "curated_row_count",
                "value": str(count),
                "ci_low": "",
                "ci_high": "",
                "n": f"{len(rows)} rows total",
                "unit": "matrix row",
                "evidence_role": "",
                "source": "docs/concordance/concordance_table.tsv",
            }
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "panel",
        "arm",
        "quantity",
        "value",
        "ci_low",
        "ci_high",
        "n",
        "unit",
        "evidence_role",
        "source",
    ]
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(records)
    return destination
