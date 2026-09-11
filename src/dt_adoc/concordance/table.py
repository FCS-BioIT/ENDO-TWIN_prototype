"""Assemble the canonical concordance table from curated and derived parts.

Three sources, joined on ``result_id``, each owned by exactly one party:

* `docs/results_reproducibility_matrix.tsv` is **hand-curated** and stays that
  way. It is the observation record: what the paper reported, in which figure,
  under which condition, with which denominator, and which evidence role that
  observation plays. No code writes it.
* The simulated side is **regenerated** here from the committed model, so every
  simulated number in the output traces to `run_settings.json` rather than to a
  paste.
* The mechanism side is **derived** from `network.bnd` by
  `concordance.mechanism`, so the path behind each prediction is computed rather
  than drawn by hand.

The output adds a `concordance_class` that is *finer* than the curated
``verdict``, because the curated vocabulary cannot express two distinctions the
analysis needs. ``structural_falsification`` separates a prediction that is
refuted and cannot be repaired by any parameter change from one that merely
misses a magnitude, and ``not_expressible_by_model_class`` separates a Boolean
model's permanent inability to represent geometry or flux from a shortage of
data. The curated ``verdict`` is carried through unchanged alongside it, so the
refinement is auditable and reversible rather than a silent recode.

Why the classes are not collapsed into a score: the rows mix a per-embryo
binomial outcome, a concentration ratio with no validated observation model, a
qualitative figure panel and a result that no Boolean model can express. A mean
over those is not a measure of anything.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from dt_adoc.concordance.mechanism import (
    PredictionMechanism,
    carrying_path,
    essential_free_variables,
    prediction_mechanism,
)
from dt_adoc.concordance.simulate import ArmRun
from dt_adoc.model.provenance import repo_root
from dt_adoc.reporting.structure import StructuralFacts

CURATED_MATRIX = Path("docs") / "results_reproducibility_matrix.tsv"
CONCORDANCE_TABLE = Path("docs") / "concordance" / "concordance_table.tsv"

#: The concordance vocabulary. Wider than the curated ``verdict`` set, and every
#: member must be reachable from a curated verdict plus a derived fact -- a class
#: nothing can produce would be a promise, not a category.
CONCORDANCE_CLASSES = (
    # Simulated magnitude agrees with the observation inside its stated
    # uncertainty, under a validated observation model. Nothing in this
    # repository can reach this class; it exists so its emptiness is visible.
    "quantitative_agreement",
    # Direction or ordering agrees; magnitude is not compared, or has no image
    # in {0, 1}.
    "directional_agreement",
    # Direction agrees and magnitude disagrees, repairably.
    "partial_agreement",
    # Simulated and observed point in opposite directions.
    "disagreement",
    # The observation has zero likelihood under the committed model and no
    # parameter setting can change that. Scoped to the committed encoding.
    "structural_falsification",
    # Agreement with evidence that was used to build, fit or filter the model.
    # Not validation.
    "calibration_circular_agreement",
    # No model node, or no defensible mapping, or the source data cannot
    # support the comparison.
    "not_assessable_with_current_data",
    # A Boolean, non-spatial, non-quantitative model class cannot express the
    # observation at all. Permanent, not pending.
    "not_expressible_by_model_class",
)

#: Curated ``binding_limitation`` values that mean the model *class* forecloses
#: the comparison, as opposed to data or calibration being short.
_CLASS_BOUND_LIMITATIONS = frozenset({"continuous_spatial"})


@dataclass(frozen=True)
class ConcordanceRow:
    """One joined row. Field names become the output header verbatim."""

    result_id: str
    figure_anchor: str
    result_block: str
    condition: str
    observed_result: str
    observed_numbers: str
    biological_unit: str
    dt_node_or_proxy: str
    horizon_class: str
    simulated_value_curated: str
    simulated_value_regenerated: str
    simulated_sd_across_seeds: str
    regimen_fidelity: str
    simulated_artifact: str
    evidence_role: str
    circularity: str
    curated_verdict: str
    concordance_class: str
    mechanism_essential_free: str
    mechanism_free_assumptions: str
    mechanism_cone_size: str
    mechanism_inert_in_cone: str
    mechanism_alias_collapse: str
    mechanism_carrying_path: str
    binding_limitation: str
    non_assessability_reason: str
    note: str


def load_curated(root: Path | None = None) -> list[dict[str, str]]:
    """Read the hand-curated matrix verbatim."""
    path = (root or repo_root()) / CURATED_MATRIX
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _biological_unit(row: dict[str, str]) -> str:
    """State the denominator's unit, because it is never the patient.

    ADOC counts embryos for adhesion and chips or column positions for
    secretion, and chips are not independent biological replicates. A row that
    reported a fraction without naming its unit would invite a donor-level
    reading the data cannot support.
    """
    block = row.get("result_block", "")
    if block == "F_human_embryo":
        return "embryo (per-embryo binary outcome; not donor)"
    if row.get("dt_node_or_proxy", "") in {"E_PAEP"}:
        return "chip (<=3 independent units, <=2 epithelial source groups; chips share sources)"
    if row.get("dt_node_or_proxy", "") in {"S_IGFBP1", "S_PRL"}:
        return "workbook column position (chip and donor mapping LOST)"
    if block == "C_single_cell":
        return "cell (3 donors; cells are not biological replicates)"
    return "not applicable"


def _concordance_class(
    row: dict[str, str],
    *,
    structural_ids: set[str],
    unassessable_result_ids: dict[str, str] | None = None,
) -> str:
    """Refine the curated verdict into the analysis vocabulary.

    Deliberately mechanical. ``structural_ids`` is passed in rather than
    inferred, so promoting a row to ``structural_falsification`` is an explicit,
    reviewable decision recorded by the caller with its justification, never a
    heuristic that could silently reclassify a future row.
    """
    verdict = row.get("verdict", "")
    if row["result_id"] in (unassessable_result_ids or {}):
        # This row is forced to not_assessable, and the caller records WHY in
        # `UNASSESSABLE_RESULT_IDS`. The reason is deliberately NOT restated
        # here: an earlier revision named one inline ("the simulated arm does
        # not implement the recorded regimen"), that reason was later repaired
        # away, and the comment went on asserting it.
        #
        # The curated matrix must already say so. An earlier revision let this
        # layer quietly override a curated `disagreement`, which left the matrix
        # narrative counting a contradiction the generated table did not: the
        # two records disagreed and neither said so. A reclassification belongs
        # in the curated file, where it is reviewable; this is only a
        # cross-check that it happened.
        if verdict != "not_assessable":
            raise ValueError(
                f"{row['result_id']} is listed as regimen-unassessable but the "
                f"curated matrix still records verdict={verdict!r}. Correct the "
                "curated verdict rather than overriding it here."
            )
        return "not_assessable_with_current_data"
    if row["result_id"] in structural_ids:
        return "structural_falsification"
    if verdict == "circular_by_construction":
        return "calibration_circular_agreement"
    if verdict == "qualitatively_reproduced_direction_only":
        return "directional_agreement"
    if verdict == "partial_direction_only":
        return "partial_agreement"
    if verdict == "disagreement":
        return "disagreement"
    if verdict == "not_assessable":
        limitations = set(filter(None, row.get("binding_limitation", "").split(";")))
        if limitations & _CLASS_BOUND_LIMITATIONS:
            return "not_expressible_by_model_class"
        return "not_assessable_with_current_data"
    raise ValueError(f"unmapped curated verdict {verdict!r} in {row['result_id']}")


def _alias_collapse(facts: StructuralFacts, node_ids: list[str]) -> str:
    """Name the alias class of each node, or say it is distinct.

    A node sharing its Boolean function with others cannot agree with an
    observation independently of them, so a scorecard that lists PAEP, IGFBP-1
    and PRL as three successes when two are one function overcounts.
    """
    out: list[str] = []
    for node_id in node_ids:
        members = next((cls for cls in facts.alias_classes if node_id in cls), ())
        if members:
            others = ";".join(m for m in members if m != node_id)
            out.append(f"{node_id}=alias_of[{others}]")
        else:
            out.append(f"{node_id}=distinct_function")
    return " | ".join(out)


def _mechanism_fields(
    facts: StructuralFacts,
    node_ids: list[str],
    *,
    essential: dict[str, tuple[str, ...]],
) -> dict[str, str]:
    if not node_ids:
        return {
            "mechanism_essential_free": "",
            "mechanism_free_assumptions": "",
            "mechanism_cone_size": "",
            "mechanism_inert_in_cone": "",
            "mechanism_alias_collapse": "",
        }
    mechanisms: list[PredictionMechanism] = [
        prediction_mechanism(facts, node_id, essential=essential)
        for node_id in node_ids
    ]
    return {
        "mechanism_essential_free": " | ".join(
            f"{m.node_id}:{';'.join(m.essential_free)}" for m in mechanisms
        ),
        "mechanism_free_assumptions": " | ".join(
            f"{m.node_id}:{';'.join(m.essential_assumptions) or 'none'}"
            for m in mechanisms
        ),
        "mechanism_cone_size": " | ".join(
            f"{m.node_id}:{len(m.backward_cone)}" for m in mechanisms
        ),
        "mechanism_inert_in_cone": " | ".join(
            f"{m.node_id}:{len(m.inert_in_cone)}" for m in mechanisms
        ),
        "mechanism_alias_collapse": _alias_collapse(facts, node_ids),
    }


def build_rows(
    *,
    facts: StructuralFacts,
    runs: dict[tuple[str, str], ArmRun],
    arm_of_result: dict[str, str],
    contrast_of_result: dict[str, tuple[str, str]],
    structural_ids: set[str],
    regimen_mismatch: dict[str, str],
    unassessable_result_ids: dict[str, str],
    artifact_pointer: str,
    root: Path | None = None,
) -> list[ConcordanceRow]:
    """Join the curated, regenerated and derived sides into output rows.

    ``runs`` is keyed by ``(arm_id, horizon_class)``. ``arm_of_result`` says
    which arm supplies a row's regenerated value; a row with no entry keeps an
    empty regenerated column rather than borrowing a number from a neighbouring
    arm. ``contrast_of_result`` names the two arms whose difference a row's
    carrying path describes.
    """
    essential = essential_free_variables(facts)
    known_nodes = set(facts.node_ids)
    rows: list[ConcordanceRow] = []

    for curated in load_curated(root):
        result_id = curated["result_id"]
        node_field = curated.get("dt_node_or_proxy", "") or ""
        node_ids = [
            part.strip()
            for part in node_field.replace("(composite)", "").split(";")
            if part.strip() in known_nodes
        ]

        horizon = curated.get("horizon_class", "")
        arm_id = arm_of_result.get(result_id, "")
        run = runs.get((arm_id, horizon)) if arm_id and horizon else None
        regenerated = ""
        regenerated_sd = ""
        if run is not None and len(node_ids) == 1:
            node_id = node_ids[0]
            if node_id in run.node_mean:
                regenerated = f"{run.node_mean[node_id]:.6f}"
                regenerated_sd = f"{run.node_sd[node_id]:.6f}"

        carrying = ""
        contrast = contrast_of_result.get(result_id)
        if contrast and len(node_ids) == 1 and horizon:
            left = runs.get((contrast[0], horizon))
            right = runs.get((contrast[1], horizon))
            if left is not None and right is not None:
                path = carrying_path(
                    facts, node_ids[0], left.node_mean, right.node_mean
                )
                carrying = (
                    f"{contrast[0]}->{contrast[1]}: " + ";".join(path)
                    if path
                    else f"{contrast[0]}->{contrast[1]}: no node differs"
                )

        mechanism = _mechanism_fields(facts, node_ids, essential=essential)
        rows.append(
            ConcordanceRow(
                result_id=result_id,
                figure_anchor=curated.get("figure_anchor", ""),
                result_block=curated.get("result_block", ""),
                condition=curated.get("condition", ""),
                observed_result=curated.get("observed_result", ""),
                observed_numbers=curated.get("observed_numbers", ""),
                biological_unit=_biological_unit(curated),
                dt_node_or_proxy=node_field,
                horizon_class=horizon,
                simulated_value_curated=curated.get("simulated_value", ""),
                simulated_value_regenerated=regenerated,
                simulated_sd_across_seeds=regenerated_sd,
                regimen_fidelity=regimen_mismatch.get(
                    result_id, "matches the recorded regimen" if regenerated else ""
                ),
                simulated_artifact=artifact_pointer if regenerated else "",
                evidence_role=curated.get("evidence_id", ""),
                circularity=curated.get("circularity", ""),
                mechanism_carrying_path=carrying,
                curated_verdict=curated.get("verdict", ""),
                concordance_class=_concordance_class(
                    curated,
                    structural_ids=structural_ids,
                    unassessable_result_ids=unassessable_result_ids,
                ),
                binding_limitation=curated.get("binding_limitation", ""),
                non_assessability_reason=(
                    curated.get("note", "")
                    if curated.get("verdict") == "not_assessable"
                    else ""
                ),
                note=curated.get("note", ""),
                **mechanism,
            )
        )
    return rows


def write_table(rows: list[ConcordanceRow], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(ConcordanceRow.__dataclass_fields__)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({name: getattr(row, name) for name in fieldnames})
    return destination


def build_rows_from_table(root: Path | None = None) -> list[ConcordanceRow]:
    """Re-read the generated concordance table back into rows.

    Lets the figure be redrawn from tracked artifacts alone, with no simulation
    and no re-derivation. A redraw must not be able to produce a figure the
    committed table does not support, so it reads the table rather than
    recomputing anything.
    """
    path = (root or repo_root()) / CONCORDANCE_TABLE
    fields = set(ConcordanceRow.__dataclass_fields__)
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            ConcordanceRow(**{k: v for k, v in row.items() if k in fields})
            for row in csv.DictReader(handle, delimiter="\t")
        ]
