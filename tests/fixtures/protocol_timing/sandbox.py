"""A sandbox repository for the protocol-timing gates.

``build_sandbox`` starts from the O8 sandbox (copies of ``models/``, ``config/``
and the evidence register, with any synthetic compounds appended), then rewrites
the sandbox's ``config/protocols.yaml``. The canonical protocol file is never
edited.

The v0.5.2 superset protocols are not rows in ``config/protocols.yaml``: they are
cloned from the archived families in ``protocols.conditions``. A sandbox row
for v0.5.2 would switch that clone off, so the sandbox first *materialises*
every canonical v0.5.2 protocol as an explicit row (``protocol_row``), and only
then appends the variants. ``MaterialisationTest`` checks that this changes no
canonical definition.

Variants are built from the canonical definitions, never written by hand, so a
variant differs from its canonical protocol only in what it says it changes.

The marker-timed gates need legacy markers, so they stay on v0.5.2. A direct
(``direct_supported_effect``) compound, since Stage 4b, can only run on a
version with an entity map and an expressivity artefact, which is v0.6.0
(``docs/stage4b_direct_admission.md`` §6.6). v0.6.0's protocols are already
explicit rows of ``config/protocols_markerless.yaml``, so they need no
materialising: ``markerless_variants`` are appended to the sandbox's copy of
that file, which is likewise never edited in the repository.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

from dt_adoc.protocols.conditions import protocol_definitions
from dt_adoc.protocols.schema import ProtocolDefinition

ROOT = Path(__file__).resolve().parents[3]
MODEL_VERSION = "adoc-literature-superset-v0.5.2"
PROTOCOLS = Path("config/protocols.yaml")
MARKERLESS_PROTOCOLS = Path("config/protocols_markerless.yaml")

_spec = importlib.util.spec_from_file_location(
    "o8_sandbox", ROOT / "tests/fixtures/o8_markerless/sandbox.py"
)
o8_sandbox = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(o8_sandbox)
#: The version the synthetic direct compounds run on.
MARKERLESS_VERSION = o8_sandbox.MODEL_VERSION


def protocol_row(definition: ProtocolDefinition) -> dict[str, Any]:
    """``definition`` as a ``config/protocols.yaml`` row that parses back to it."""
    row: dict[str, Any] = {
        "protocol_id": definition.protocol_id,
        "protocol_class": definition.protocol_class,
        "model_version": definition.model_version,
        "condition_cfg": definition.condition_cfg,
        "comparator_role": definition.comparator_role,
        "steps": [
            {
                "step_id": step.step_id,
                "relative_order": step.relative_order,
                "relative_duration": step.relative_duration,
                "duration_note": step.duration_note,
                "input_states": dict(step.input_states),
                **(
                    {"interventions": list(step.interventions)}
                    if step.interventions
                    else {}
                ),
            }
            for step in definition.steps
        ],
        "evidence_ids": list(definition.evidence_ids),
        "notes": definition.notes,
    }
    if definition.continuation_from is not None:
        row["continuation_from"] = definition.continuation_from
    if definition.continuation is not None:
        row["continuation"] = {
            "mode": definition.continuation.mode,
            "memory_policy": definition.continuation.memory_policy,
            "memory_nodes": list(definition.continuation.memory_nodes),
            "probability_cutoff": definition.continuation.probability_cutoff,
        }
    return row


def canonical_rows(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    """Every canonical v0.5.2 protocol as an explicit row, keyed by id."""
    return {
        protocol_id: protocol_row(definition)
        for protocol_id, definition in protocol_definitions(
            root, model_version=MODEL_VERSION
        ).items()
    }


def markerless_rows(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    """The committed v0.6.0 protocol rows, keyed by id. Already explicit."""
    payload = json.loads((root / MARKERLESS_PROTOCOLS).read_text(encoding="utf-8"))
    return {
        row["protocol_id"]: row
        for row in payload["protocols"]
        if row["model_version"] == MARKERLESS_VERSION
    }


def renamed(
    base: dict[str, Any],
    protocol_id: str,
    *,
    continuation_from: str | None = None,
    steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """A copy of ``base`` under ``protocol_id``, with the named parts replaced."""
    row = copy.deepcopy(base)
    row["protocol_id"] = protocol_id
    if continuation_from is not None:
        row["continuation_from"] = continuation_from
    if steps is not None:
        row["steps"] = steps
    return row


def step(
    base: dict[str, Any],
    step_id: str,
    order: int,
    *,
    inputs: dict[str, bool] | None = None,
    interventions: list[str] | None = None,
) -> dict[str, Any]:
    """A copy of the step ``base`` with ``inputs`` overriding its input states."""
    new = copy.deepcopy(base)
    new["step_id"] = step_id
    new["relative_order"] = order
    new["input_states"].update(inputs or {})
    new.pop("interventions", None)
    if interventions is not None:
        new["interventions"] = list(interventions)
    return new


def build_sandbox(
    destination: Path,
    variants: list[dict[str, Any]],
    compounds: tuple[str, ...] = (),
    markerless_variants: list[dict[str, Any]] = (),
) -> Path:
    """The O8 sandbox, with canonical v0.5.2 protocols explicit and ``variants``
    added, and ``markerless_variants`` added to the v0.6.0 protocol file."""
    o8_sandbox.build_sandbox(destination, compounds)
    for rows, added, path in (
        (canonical_rows(), variants, PROTOCOLS),
        (markerless_rows(), markerless_variants, MARKERLESS_PROTOCOLS),
    ):
        clashes = sorted(set(rows) & {variant["protocol_id"] for variant in added})
        if clashes:
            raise ValueError(f"a variant reuses a canonical protocol id: {clashes}")
    path = destination / PROTOCOLS
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["protocols"] = [
        *payload["protocols"],
        *canonical_rows().values(),
        *variants,
    ]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if markerless_variants:
        path = destination / MARKERLESS_PROTOCOLS
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["protocols"] = [*payload["protocols"], *markerless_variants]
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return destination
