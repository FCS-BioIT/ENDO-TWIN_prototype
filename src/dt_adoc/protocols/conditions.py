"""Load protocol and perturbation definitions for model execution."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

import yaml

from dt_adoc.model.catalog import load_jsonish, load_perturbations, load_protocols
from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.engine import (
    LEGACY_BASIS,
    LIBRARY_PATH,
    InterventionEffect,
    InterventionError,
    library_for_version,
    load_intervention_library,
)
from dt_adoc.protocols.schema import (
    ContinuationDefinition,
    ProtocolDefinition,
    ProtocolStep,
)

#: The maternal phase each embryo challenge must be seeded from, for the
#: superset families only.
#:
#: WHY THIS EXISTS. The superset clone layer builds its protocol suite from two
#: parent families. It takes the ``adoc-literature-v0.2.0`` rows wholesale and
#: additionally imports three ``adoc-core-v0.1.0`` maternal rows, rewiring those
#: onto the maternal lineage. It did not rewire the embryo challenges to consume
#: them, so every named perturbation challenge was seeded from
#: ``hormone_treated_maternal`` -- the UNPERTURBED hormone-treated terminal joint
#: state -- and the perturbation switched on simultaneously with the embryo.
#:
#: That is not the recorded experimental regimen. ``SOFIA-HT-002`` records 10 uM
#: mifepristone for 24 h AFTER the six-day hormone protocol and BEFORE the
#: adhesion assay, acting on maternal tissue while no embryo is present. The
#: intended execution semantics are:
#:
#:     hormone-conditioned maternal terminal distribution
#:         -> maternal perturbation/exposure
#:         -> terminal joint state after that exposure
#:         -> embryo challenge
#:
#: This mapping is applied ONLY to ``adoc-literature-superset-v*``. The
#: ``adoc-core-v0.1.0`` and ``adoc-literature-v0.2.0`` families are archived and
#: keep the lineage they were published with; repairing them would silently
#: change what an archived model version simulates.
#:
#: ``adhesion_challenge_hormone_treated`` is deliberately ABSENT: it is the
#: unperturbed comparator and ``hormone_treated_maternal`` is genuinely its
#: parent. The HAND2-loss challenge is rewired in ``_hand2_loss_protocols``
#: instead, because that arm is synthesised rather than cloned from config.
SUPERSET_CHALLENGE_PARENTS: dict[str, str] = {
    "adhesion_challenge_hormone_treated_mifepristone": "hormone_treated_mifepristone",
    "adhesion_challenge_hormone_treated_anti_spp1": "hormone_treated_anti_spp1",
    "adhesion_challenge_washout": "washout",
}

#: The first superset version that receives the wiring repair.
#:
#: SCOPE, and why it is a version floor rather than "all supersets". The clone
#: layer below deliberately serves EVERY ``adoc-literature-superset-v*`` so that
#: archived supersets stay resolvable. Applying the repair there too would edit
#: what an archived model version simulates, which is the thing this repair is
#: careful not to do for ``adoc-core-v0.1.0`` and ``adoc-literature-v0.2.0``.
#:
#: For ``v0.3.0`` it would also be an outright regression rather than a change
#: of interpretation: that family ships no ``washout.cfg``, so rewiring
#: ``adhesion_challenge_washout`` onto ``washout`` would take an arm that runs
#: today and make it fail on a missing condition file. An archived model keeps
#: the lineage it was published with, defects included.
#:
#: A floor rather than an equality so that ``v0.5.0`` and later inherit the
#: repair automatically instead of silently reverting to the bypass.
REPAIRED_FROM_SUPERSET_VERSION: tuple[int, ...] = (0, 4, 0)

#: The first superset version without intervention-marker nodes (Stage 3,
#: ``docs/intervention_layer_stage3.md``). Its protocols cannot be cloned from
#: the archived families, whose every row sets the markers in ``input_states``,
#: so it and every later superset version must have explicit rows in
#: ``MARKERLESS_PROTOCOLS_PATH``, and a version without them is refused.
MARKERLESS_FROM_SUPERSET_VERSION: tuple[int, ...] = (0, 6, 0)
#: Protocol rows for those versions. A file of its own because
#: ``config/protocols.yaml`` is a closed input (``closure_replay``); generated
#: by ``dt_adoc.reporting.v060_increment``.
MARKERLESS_PROTOCOLS_PATH = Path("config/protocols_markerless.yaml")


def _superset_version(model_version: str) -> tuple[int, ...]:
    """Parse ``adoc-literature-superset-vX.Y.Z`` into a comparable tuple."""
    raw = model_version.rsplit("-v", 1)[-1]
    parts: list[int] = []
    for chunk in raw.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


#: Continuation policy for a challenge seeded from a maternal perturbation
#: phase. Matches the policy the maternal phases themselves use, so the whole
#: maternal chain carries the same memory semantics before the embryo enters.
_CHALLENGE_CONTINUATION: dict[str, Any] = {
    "mode": "joint",
    "memory_policy": "minimal_stable_joint",
    "probability_cutoff": 1e-06,
}


def _duration_fallbacks(root: Path | None = None) -> dict[str, float]:
    active_root = root or Path(__file__).resolve().parents[3]
    payload: dict[str, Any] = yaml.safe_load(
        (active_root / "config" / "calibration.yaml").read_text()
    )
    durations = payload.get("sequential_execution", {}).get(
        "relative_phase_durations", {}
    )
    return {str(key): float(value) for key, value in durations.items()}


def step_interventions(
    raw: Any,
    *,
    protocol_id: str,
    step_id: str,
    model_version: str,
    input_states: dict[str, bool],
    library: dict[str, tuple[InterventionEffect, ...]] | None,
) -> tuple[str, ...]:
    """Validate a step's ``interventions`` field and return it in canonical order.

    Absent (``None``) and ``[]`` both mean that the step names no intervention.
    Otherwise it is a list of distinct library ids, each defined for this
    protocol's model version. A legacy-basis intervention may not be named while
    the same step sets its marker ``ON`` in ``input_states``: that would declare
    it twice, and is refused here rather than resolved by precedence. Whether the
    marker is ``ON`` through the condition cfg or a continuation is only known
    when the step runs, and ``legacy_route_overrides`` refuses that case then
    for a veto marker. A ``no_executable_effect`` row (XAV939) applies nothing,
    so its marker plus its name is not refused at run time; Stage 4a accepts it
    as an inert member.

    The order is not semantic, since composition is an idempotent union; sorting
    makes two spellings of one schedule one definition. Nothing here says what an
    intervention does. That stays in the library.
    """
    where = f"protocol {protocol_id} step {step_id}"
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(
        isinstance(item, str) and item for item in raw
    ):
        raise InterventionError(
            f"{where}: interventions is a list of intervention ids, not {raw!r}"
        )
    if len(set(raw)) != len(raw):
        raise InterventionError(f"{where}: an intervention is named twice: {raw}")
    if raw and library is None:
        raise InterventionError(f"{where}: no intervention library at {LIBRARY_PATH}")
    view = library_for_version(library or {}, model_version)
    for intervention_id in raw:
        if intervention_id not in (library or {}):
            raise InterventionError(
                f"{where}: unknown intervention {intervention_id!r}"
            )
        effects = view.get(intervention_id)
        if effects is None:
            versions = ", ".join(
                sorted({e.model_version for e in (library or {})[intervention_id]})
            )
            raise InterventionError(
                f"{where}: {intervention_id} is defined for {versions}, "
                f"not {model_version}"
            )
        marker = effects[0].legacy_input_node
        if effects[0].mapping_basis == LEGACY_BASIS and input_states.get(marker):
            raise InterventionError(
                f"{where}: {intervention_id} is named and its marker {marker} is "
                "ON; declare its timing one way, not both"
            )
    return tuple(sorted(raw))


def default_model_version(root: Path | None = None) -> str:
    payload = load_protocols(root)
    return str(payload.get("baseline_model_version", "adoc-core-v0.1.0"))


def _hand2_loss_protocols(
    cloned_rows: list[dict[str, Any]],
    superset_root: str,
    root: Path,
    *,
    repaired_wiring: bool,
) -> list[dict[str, Any]]:
    """Derive the HAND2 loss-of-function arms from the hormone-treated pair.

    Only supersets that actually carry the input get them; earlier supersets
    have no IN_HAND2_LOSS node, so synthesising the protocol there would name a
    condition file that does not exist.
    """
    by_id = {row["protocol_id"]: row for row in cloned_rows}
    derived: list[dict[str, Any]] = []
    parents = {
        "hormone_treated_maternal": "hormone_treated_hand2_loss",
        "adhesion_challenge_hormone_treated": (
            "adhesion_challenge_hormone_treated_hand2_loss"
        ),
    }
    for parent_id, new_id in parents.items():
        parent = by_id.get(parent_id)
        if parent is None:
            continue
        cfg = f"{superset_root}{new_id}.cfg"
        if not (root / cfg).is_file():
            continue
        row = copy.deepcopy(parent)
        row["protocol_id"] = new_id
        row["condition_cfg"] = cfg
        row["comparator_role"] = "hand2_loss_of_function_arm"
        # The MATERNAL arm inherits its parent's continuation: it branches from
        # e2_primed_maternal exactly as hormone_treated_maternal does, so HAND2
        # loss is present throughout hormone treatment rather than applied
        # after it. That is already correct and is left alone.
        #
        # The CHALLENGE arm is not: inheriting the parent's continuation seeds
        # it from hormone_treated_maternal, i.e. from tissue that never lost
        # HAND2, so the loss would switch on at the same instant as the embryo.
        # Seed it from the HAND2-loss maternal phase instead, matching every
        # other named perturbation challenge.
        if (
            repaired_wiring
            and new_id == "adhesion_challenge_hormone_treated_hand2_loss"
        ):
            row["continuation_from"] = "hormone_treated_hand2_loss"
            row["continuation"] = dict(_CHALLENGE_CONTINUATION)
        for step in row["steps"]:
            step["input_states"] = dict(step["input_states"])
            step["input_states"]["IN_HAND2_LOSS"] = True
        derived.append(row)
    return derived


def markerless_protocol_rows(root: Path | None = None) -> list[dict[str, Any]]:
    """The rows of ``MARKERLESS_PROTOCOLS_PATH``, or none when the file is absent.

    Each must name a superset version at or after
    ``MARKERLESS_FROM_SUPERSET_VERSION``, so no archived version can pick up a
    row from here.
    """
    path = (root or repo_root()) / MARKERLESS_PROTOCOLS_PATH
    if not path.is_file():
        return []
    rows = list(load_jsonish(path)["protocols"])
    for row in rows:
        version = str(row["model_version"])
        if not (
            version.startswith("adoc-literature-superset-v")
            and _superset_version(version) >= MARKERLESS_FROM_SUPERSET_VERSION
        ):
            raise ValueError(
                f"{MARKERLESS_PROTOCOLS_PATH} row {row['protocol_id']!r} names "
                f"{version}, which predates the markerless superset versions"
            )
    return rows


def protocol_file(model_version: str, root: Path | None = None) -> Path:
    """The file, relative to the root, that defines ``model_version``'s protocols."""
    if any(row["model_version"] == model_version for row in markerless_protocol_rows(root)):
        return MARKERLESS_PROTOCOLS_PATH
    return Path("config/protocols.yaml")


def _network_nodes(model_version: str, root: Path | None) -> set[str]:
    text = resolve_model(model_version, root).network_bnd.read_text(encoding="utf-8")
    return set(re.findall(r"^Node\s+(\w+)\s*\{", text, re.MULTILINE))


def protocol_definitions(
    root: Path | None = None,
    *,
    model_version: str | None = None,
) -> dict[str, ProtocolDefinition]:
    payload = load_protocols(root)["protocols"]
    markerless = markerless_protocol_rows(root)
    duration_fallbacks = _duration_fallbacks(root)
    selected_model_version = model_version or default_model_version(root)
    resolve_model(selected_model_version, root)
    selected_rows = [
        row for row in payload if row["model_version"] == selected_model_version
    ]
    markerless_rows = [
        row for row in markerless if row["model_version"] == selected_model_version
    ]
    if selected_rows and markerless_rows:
        raise ValueError(
            f"{selected_model_version} has rows in both config/protocols.yaml and "
            f"{MARKERLESS_PROTOCOLS_PATH}"
        )
    selected_rows = selected_rows or markerless_rows
    if (
        not selected_rows
        and selected_model_version.startswith("adoc-literature-superset-v")
        and _superset_version(selected_model_version)
        >= MARKERLESS_FROM_SUPERSET_VERSION
    ):
        # Cloning would copy marker-bearing input states into a version that
        # has no markers; refuse rather than guess its schedule.
        raise ValueError(
            f"{selected_model_version} has no intervention-marker nodes, so its "
            f"protocols cannot be cloned; give it rows in {MARKERLESS_PROTOCOLS_PATH}"
        )
    # Superset protocols are cloned from the parent families rather than
    # duplicated in config. Match ANY superset version, not just the one the
    # generator currently emits, so archived supersets stay resolvable.
    if not selected_rows and selected_model_version.startswith(
        "adoc-literature-superset-v"
    ):
        repaired_wiring = (
            _superset_version(selected_model_version) >= REPAIRED_FROM_SUPERSET_VERSION
        )
        literature_root = "models/extended/adoc-literature-v0.2.0/conditions/"
        superset_root = f"models/superset/{selected_model_version}/conditions/"
        selected_rows = []
        for row in payload:
            if row["model_version"] not in {
                "adoc-literature-v0.2.0",
                "adoc-core-v0.1.0",
            }:
                continue
            if row["model_version"] == "adoc-core-v0.1.0" and row[
                "protocol_id"
            ] not in {
                "hormone_treated_mifepristone",
                "hormone_treated_anti_spp1",
                "washout",
            }:
                continue
            cloned = dict(row)
            cloned["model_version"] = selected_model_version
            cloned["condition_cfg"] = (
                str(row["condition_cfg"])
                .replace(literature_root, superset_root)
                .replace("models/baseline/adoc-core-v0.1.0/conditions/", superset_root)
            )
            if cloned["protocol_id"] in {
                "hormone_treated_mifepristone",
                "hormone_treated_anti_spp1",
            }:
                cloned["continuation_from"] = "hormone_treated_maternal"
                cloned["continuation"] = {
                    "mode": "joint",
                    "memory_policy": "extended_maternal_joint",
                    "probability_cutoff": 1e-06,
                }
            if cloned["protocol_id"] == "washout":
                cloned["continuation_from"] = "hormone_treated_anti_spp1"
                cloned["continuation"] = {
                    "mode": "joint",
                    "memory_policy": "extended_maternal_joint",
                    "probability_cutoff": 1e-06,
                }
            # Seed each named perturbation challenge from the maternal phase
            # whose name it carries, rather than from the unperturbed
            # hormone-treated state. See SUPERSET_CHALLENGE_PARENTS, and
            # REPAIRED_FROM_SUPERSET_VERSION for why archived supersets keep the
            # bypass they were published with.
            challenge_parent = (
                SUPERSET_CHALLENGE_PARENTS.get(cloned["protocol_id"])
                if repaired_wiring
                else None
            )
            if challenge_parent is not None:
                cloned["continuation_from"] = challenge_parent
                cloned["continuation"] = dict(_CHALLENGE_CONTINUATION)
            cloned_steps: list[dict[str, Any]] = []
            protocol_class = row.get(
                "protocol_class",
                "embryo_challenge"
                if str(row["protocol_id"]).startswith("adhesion_challenge_")
                else "maternal_state",
            )
            for step in row["steps"]:
                cloned_step = dict(step)
                input_states = dict(step["input_states"])
                input_states.setdefault(
                    "IN_EMBRYO_CONTACT", protocol_class == "embryo_challenge"
                )
                cloned_step["input_states"] = input_states
                cloned_steps.append(cloned_step)
            cloned["steps"] = cloned_steps
            selected_rows.append(cloned)
        selected_rows.extend(
            _hand2_loss_protocols(
                selected_rows,
                superset_root,
                root or repo_root(),
                repaired_wiring=repaired_wiring,
            )
        )
    library: dict[str, tuple[InterventionEffect, ...]] | None = None
    if any(step.get("interventions") for row in selected_rows for step in row["steps"]):
        # Loaded only when a step names one, so a protocol file that names none
        # resolves exactly as it did before the field existed.
        library_root = root or repo_root()
        if (library_root / LIBRARY_PATH).is_file():
            library = load_intervention_library(library_root)
    nodes = _network_nodes(selected_model_version, root)
    definitions: dict[str, ProtocolDefinition] = {}
    for row in selected_rows:
        protocol_id = row["protocol_id"]
        for step in row["steps"]:
            # Otherwise a stale name reaches MaBoSS as an istate for an
            # undefined node, or a forced node it cannot set.
            unknown = sorted(set(step["input_states"]) - nodes)
            if unknown:
                raise ValueError(
                    f"protocol {protocol_id} step {step['step_id']} sets "
                    f"{', '.join(unknown)}, which {selected_model_version} does not have"
                )
        continuation_payload = row.get("continuation")
        if protocol_id in definitions:
            raise ValueError(
                f"duplicate protocol_id {protocol_id!r} for model_version {selected_model_version!r}"
            )
        definitions[row["protocol_id"]] = ProtocolDefinition(
            protocol_id=protocol_id,
            protocol_class=row.get(
                "protocol_class",
                "embryo_challenge"
                if protocol_id.startswith("adhesion_challenge_")
                else "maternal_state",
            ),
            model_version=row["model_version"],
            condition_cfg=row["condition_cfg"],
            comparator_role=row["comparator_role"],
            continuation_from=row.get("continuation_from"),
            steps=tuple(
                ProtocolStep(
                    step_id=step["step_id"],
                    relative_order=int(step["relative_order"]),
                    relative_duration=float(
                        step.get(
                            "relative_duration",
                            duration_fallbacks.get(step["step_id"], 1.0),
                        )
                    ),
                    duration_note=step["duration_note"],
                    input_states={k: bool(v) for k, v in step["input_states"].items()},
                    interventions=step_interventions(
                        step.get("interventions"),
                        protocol_id=protocol_id,
                        step_id=step["step_id"],
                        model_version=row["model_version"],
                        input_states={
                            k: bool(v) for k, v in step["input_states"].items()
                        },
                        library=library,
                    ),
                )
                for step in row["steps"]
            ),
            evidence_ids=tuple(row["evidence_ids"]),
            notes=row["notes"],
            continuation=(
                ContinuationDefinition(
                    mode=str(continuation_payload["mode"]),
                    memory_policy=str(continuation_payload["memory_policy"]),
                    memory_nodes=tuple(continuation_payload.get("memory_nodes", [])),
                    probability_cutoff=float(
                        continuation_payload.get("probability_cutoff", 0.0)
                    ),
                )
                if continuation_payload is not None
                else None
            ),
        )
    return definitions


def get_protocol(
    protocol_id: str,
    root: Path | None = None,
    *,
    model_version: str | None = None,
) -> ProtocolDefinition:
    definitions = protocol_definitions(root, model_version=model_version)
    return definitions[protocol_id]


def perturbation_catalog(root: Path | None = None) -> list[dict[str, object]]:
    return load_perturbations(root)["perturbations"]
