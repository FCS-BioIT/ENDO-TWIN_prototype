"""Loader and pure evaluator for the observation-to-model mapping table.

``config/observation_model_map.tsv`` is the machine-readable audit trail that
replaced the inert ``directional_readouts`` stub in ``config/calibration.yaml``
(the stub named one ``protocol_id`` per readout with no comparator arm, so it
could not express a contrast). This module only loads and validates that
table and evaluates already-simulated node probabilities against it -- it
never runs MaBoSS itself, and it never converts a secreted-protein
concentration into a probability. The observed side of every row contributes
a direction only.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dt_adoc.model.provenance import repo_root

MAPPING_COLUMNS: tuple[str, ...] = (
    "mapping_id",
    "source_table",
    "source_series_id",
    "source_cells",
    "source_rows_n",
    "protein",
    "outlet",
    "registered_readout_id",
    "registered_comparator",
    "actual_comparator",
    "protocol_ids",
    "model_nodes",
    "target_type",
    "comparison",
    "supporting_fraction",
    "calibration_role",
    "activation_status",
    "confidence",
    "weight",
    "objective_treatment",
    "evidence_ids",
    "censoring_note",
    "exclusion_reason",
    "claim_ceiling",
)

ACTIVATION_STATUSES: frozenset[str] = frozenset(
    {
        "active_constraint",
        "active_diagnostic",
        "reported_only",
        "provisional",
        "rejected",
    }
)

# Rows evaluable by evaluate_directional_constraints(): both name exactly two
# protocol_ids (low, high) and one model_node, and both are read at the
# converged logical fixed point per docs/endpoint_convergence_finding.md
# ("Horizon decision"). They differ only in what a violation means:
#   active_constraint  -- a feasibility gate; a violation excludes the
#                         candidate from the retained ensemble.
#   active_diagnostic  -- reported every run, flags an inversion only, and
#                         never excludes a candidate.
EVALUABLE_ACTIVATION_STATUSES: frozenset[str] = frozenset(
    {"active_constraint", "active_diagnostic"}
)

CALIBRATION_ROLES: frozenset[str] = frozenset(
    {"calibration_constraint", "context_only", "diagnostic", "gap", "rejected"}
)

TARGET_TYPES: frozenset[str] = frozenset(
    {
        "directional",
        "directional_and_censored",
        "directional_state",
        "compartment_sanity_check",
        "protocol_coverage_gap",
    }
)

DEFAULT_MAPPING_PATH = "config/observation_model_map.tsv"


class ObservationMapValidationError(ValueError):
    """Raised when a mapping row violates a controlled vocabulary or invariant."""


@dataclass(frozen=True)
class ConstraintCheck:
    """Result of evaluating one active directional constraint or diagnostic.

    ``satisfied`` is always ``value_high > value_low``. ``excludes_candidate``
    is ``True`` only when ``activation_status == "active_constraint"`` and the
    check failed -- an ``active_diagnostic`` failure (e.g. the S_IGFBP1
    inversion diagnostic) is reported here but never excludes a candidate.
    """

    mapping_id: str
    activation_status: str
    model_node: str
    protocol_high: str
    protocol_low: str
    value_high: float
    value_low: float
    satisfied: bool

    @property
    def excludes_candidate(self) -> bool:
        return self.activation_status == "active_constraint" and not self.satisfied


def _mapping_path(root: Path | None = None) -> Path:
    active_root = root or repo_root()
    return active_root / DEFAULT_MAPPING_PATH


def load_observation_map(root: Path | None = None) -> list[dict[str, str]]:
    """Load and validate ``config/observation_model_map.tsv``.

    Validation is limited to structural/controlled-vocabulary checks: column
    set, ``activation_status``/``calibration_role`` vocabularies, the
    "no numeric weight on a directional row" invariant, and the "every
    rejected row carries an exclusion_reason" invariant. It does not touch
    the model catalog or run MaBoSS.
    """
    path = _mapping_path(root)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = tuple(reader.fieldnames or ())
        if fieldnames != MAPPING_COLUMNS:
            missing = set(MAPPING_COLUMNS) - set(fieldnames)
            extra = set(fieldnames) - set(MAPPING_COLUMNS)
            raise ObservationMapValidationError(
                f"unexpected column set: missing={sorted(missing)} "
                f"extra={sorted(extra)}"
            )
        rows = list(reader)

    if not rows:
        raise ObservationMapValidationError("observation map has no rows")

    seen_ids: set[str] = set()
    for row in rows:
        mapping_id = row["mapping_id"]
        if not mapping_id:
            raise ObservationMapValidationError("row missing mapping_id")
        if mapping_id in seen_ids:
            raise ObservationMapValidationError(f"duplicate mapping_id {mapping_id!r}")
        seen_ids.add(mapping_id)

        activation_status = row["activation_status"]
        if activation_status not in ACTIVATION_STATUSES:
            raise ObservationMapValidationError(
                f"{mapping_id}: invalid activation_status {activation_status!r}"
            )

        calibration_role = row["calibration_role"]
        if calibration_role not in CALIBRATION_ROLES:
            raise ObservationMapValidationError(
                f"{mapping_id}: invalid calibration_role {calibration_role!r}"
            )

        target_type = row["target_type"]
        if target_type not in TARGET_TYPES:
            raise ObservationMapValidationError(
                f"{mapping_id}: invalid target_type {target_type!r}"
            )

        if activation_status == "rejected" and not row["exclusion_reason"].strip():
            raise ObservationMapValidationError(
                f"{mapping_id}: rejected row has no exclusion_reason"
            )

        if row["weight"].strip():
            raise ObservationMapValidationError(
                f"{mapping_id}: no row in this table may carry a numeric weight "
                "-- this repository has NO magnitude-fitted term at all since "
                "adhesion_objective was demoted to diagnostic_ordinal on "
                "2026-09-16 (see docs/gate3_scope_adjudication.md); every row "
                "here is a pass/fail constraint or a "
                "reported/provisional/rejected diagnostic, and a weight would "
                "reintroduce a fitted score by the back door"
            )

        if (
            activation_status == "provisional"
            and row["protein"] == "PRL"
            and calibration_role == "calibration_constraint"
        ):
            raise ObservationMapValidationError(
                f"{mapping_id}: PRL row must not be a calibration_constraint"
            )

    return rows


def active_constraints(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Rows whose violation excludes a candidate from the retained ensemble."""
    return [row for row in rows if row["activation_status"] == "active_constraint"]


def active_diagnostics(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Rows that are evaluated and reported but never exclude a candidate."""
    return [row for row in rows if row["activation_status"] == "active_diagnostic"]


def evaluate_directional_constraints(
    simulated: dict[str, dict[str, float]],
    rows: list[dict[str, str]],
) -> list[ConstraintCheck]:
    """Evaluate every ``active_constraint``/``active_diagnostic`` row.

    ``simulated`` maps ``protocol_id -> {node_id: probability}`` and is
    expected to have been produced at the converged logical fixed-point
    horizon (see docs/endpoint_convergence_finding.md, "Horizon decision") --
    this function only compares two already-simulated values, it never runs
    MaBoSS and never chooses a horizon itself. Only the two
    semicolon-separated ``protocol_ids`` (low, high) and the single
    ``model_nodes`` entry are used per row -- every currently evaluable row is
    a single-node, two-protocol comparison. Use ``ConstraintCheck.
    excludes_candidate`` to gate on ``active_constraint`` failures alone while
    still recording ``active_diagnostic`` outcomes.
    """
    checks: list[ConstraintCheck] = []
    for row in rows:
        activation_status = row["activation_status"]
        if activation_status not in EVALUABLE_ACTIVATION_STATUSES:
            continue
        protocol_ids = [p for p in row["protocol_ids"].split(";") if p]
        model_nodes = [n for n in row["model_nodes"].split(";") if n]
        if len(protocol_ids) != 2 or len(model_nodes) != 1:
            raise ObservationMapValidationError(
                f"{row['mapping_id']}: {activation_status} rows must name "
                "exactly two protocol_ids (low, high) and one model_node"
            )
        protocol_low, protocol_high = protocol_ids
        node = model_nodes[0]
        try:
            value_low = simulated[protocol_low][node]
            value_high = simulated[protocol_high][node]
        except KeyError as exc:
            raise ObservationMapValidationError(
                f"{row['mapping_id']}: simulated values missing for {exc}"
            ) from exc
        checks.append(
            ConstraintCheck(
                mapping_id=row["mapping_id"],
                activation_status=activation_status,
                model_node=node,
                protocol_high=protocol_high,
                protocol_low=protocol_low,
                value_high=value_high,
                value_low=value_low,
                satisfied=value_high > value_low,
            )
        )
    return checks


def simulate_constraint_protocols(
    *,
    model_version: str = "adoc-literature-superset-v0.3.0",
    root: Path | None = None,
    seed: int = 1,
    trajectory_count: int = 2000,
    converged_duration: float = 30.0,
) -> dict[str, dict[str, float]]:
    """Run the maternal lineage and return final node values per protocol.

    Deliberately separate from the fitted adhesion likelihood: this runs only
    the protocols the directional mapping references, and reads them at the
    converged logical fixed point chosen in
    ``docs/endpoint_convergence_finding.md``. Nothing here feeds
    ``adhesion_objective``.

    Imported lazily so the mapping loader stays usable without a MaBoSS runtime.
    """
    from dt_adoc.protocols.conditions import get_protocol
    from dt_adoc.simulation.runner import (
        _input_override_text,
        _timing_override_text,
        protocol_continuation,
        run_cmaboss_condition,
        run_protocol,
    )

    active_root = root or repo_root()
    lineage = ("basal_maternal", "e2_primed_maternal", "hormone_treated_maternal")
    runs: dict[str, Any] = {}
    simulated: dict[str, dict[str, float]] = {}

    for protocol_id in lineage:
        protocol = get_protocol(protocol_id, active_root, model_version=model_version)
        continuation = None
        if protocol.continuation_from is not None:
            continuation = protocol_continuation(
                protocol_id,
                runs[protocol.continuation_from],
                model_version=model_version,
                root=active_root,
            )
        runs[protocol_id] = run_protocol(
            protocol_id,
            model_version=model_version,
            root=active_root,
            continuation=continuation,
            seed=seed,
            sample_count=trajectory_count,
        )
        step = protocol.steps[0]
        # Re-read the terminal protocol at the converged horizon; the earlier
        # phases only supply the transferred state, so their declared duration
        # is what defines the state being handed on.
        if protocol_id == lineage[-1]:
            simulated[protocol_id] = run_cmaboss_condition(
                model_version=model_version,
                condition_cfg=active_root / protocol.condition_cfg,
                root=active_root,
                override_texts=[
                    _input_override_text(step.input_states),
                    _timing_override_text(
                        relative_duration=converged_duration, root=active_root
                    ),
                ],
                continuation=continuation,
                # The re-read must run what ``run_protocol`` ran for this step.
                interventions=step.interventions,
                seed=seed,
                sample_count=trajectory_count,
            ).last
        else:
            simulated[protocol_id] = runs[protocol_id].final_result.last
    return simulated
