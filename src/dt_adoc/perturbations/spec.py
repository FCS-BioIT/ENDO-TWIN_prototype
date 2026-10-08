"""A declared perturbation of an established protocol state.

A ``PerturbationSpec`` names a starting protocol and the effects applied at the
end of it. It is a *selection* among mechanisms the repository already executes,
never a second way to write model biology:

- ``input_changes`` sets declared model inputs (``IN_*`` nodes whose rule is
  their own value) differently from the starting protocol's last step, the way
  a protocol step does. Provenance class ``protocol_input_change``.
- ``interventions`` names rows of ``config/intervention_library.tsv``, executed
  by the intervention engine and licensed by it (``registered_intervention``).
- ``rule_variants`` selects registered rule-variant families of the model
  (``registered_rule_variant``).

Nothing else is accepted. In particular there is no free activity veto, no
forced-ON clamp and no rule text: a node-level knockout named without a reagent
is the model-only target-ablation unit that ``docs/stage4b_direct_admission.md``
(owner decision 1) reserves as separate work, and a rule replacement would be a
second modelling language. The spec loader refuses those keys by name so that
the refusal is explicit rather than an "unknown key".

Every result made from a spec is a conditional model-internal prediction under
the declared semantics, not evidence about the named reagent.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import available_models, resolve_model, resolve_rule_variants
from dt_adoc.perturbations.engine import (
    InterventionError,
    library_for_version,
    load_intervention_library,
)
from dt_adoc.protocols.conditions import get_protocol

SPEC_SCHEMA = "dt_adoc.perturbation_spec/1"
SPEC_DIR = Path("perturbations")

INPUT_CHANGE = "protocol_input_change"
REGISTERED_INTERVENTION = "registered_intervention"
REGISTERED_RULE_VARIANT = "registered_rule_variant"
PROVENANCE_CLASSES = (INPUT_CHANGE, REGISTERED_INTERVENTION, REGISTERED_RULE_VARIANT)

_ALLOWED_KEYS = {
    "schema",
    "name",
    "description",
    "model_version",
    "start",
    "input_changes",
    "interventions",
    "rule_variants",
}
#: Keys a reader might expect and that are refused on purpose, with the reason.
_RESERVED_KEYS = {
    "effects": "free per-node effects are not executable here; name a library "
    "intervention, an input change or a registered rule variant",
    "veto": "a reagent-free node veto is the model-only target-ablation unit "
    "reserved by Stage 4b owner decision 1",
    "hypothetical_vetoes": "a reagent-free node veto is the model-only "
    "target-ablation unit reserved by Stage 4b owner decision 1",
    "force_on": "the intervention engine has no ON rendering; adding one is a "
    "model-semantics decision, not a spec option",
    "rule_replace": "free rule text would be a second modelling language; "
    "register a rule variant instead",
}
_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,63}")


class PerturbationSpecError(ValueError):
    """A perturbation specification that cannot be executed as declared."""


@dataclass(frozen=True)
class PerturbationSpec:
    name: str
    model_version: str
    start: str
    input_changes: dict[str, bool] = field(default_factory=dict)
    interventions: tuple[str, ...] = ()
    rule_variants: dict[str, str] = field(default_factory=dict)
    description: str = ""

    @property
    def is_empty(self) -> bool:
        return not (self.input_changes or self.interventions or self.rule_variants)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SPEC_SCHEMA,
            "name": self.name,
            "description": self.description,
            "model_version": self.model_version,
            "start": self.start,
            "input_changes": dict(sorted(self.input_changes.items())),
            "interventions": list(self.interventions),
            "rule_variants": dict(sorted(self.rule_variants.items())),
        }

    def control(self) -> PerturbationSpec:
        """The matched unperturbed twin: same start, no effects."""
        return PerturbationSpec(
            name=f"{self.name}__control",
            model_version=self.model_version,
            start=self.start,
            description=f"matched unperturbed control of {self.name}",
        )


def input_nodes(model_version: str, root: Path | None = None) -> tuple[str, ...]:
    """The model's declared inputs: ``IN_*`` nodes whose rule is their own value.

    Other self-rule nodes (the latched ``X_*_RELAY`` placeholders,
    ``E_KLF12_HIGH``) are latent memory states, not protocol inputs, and cannot
    be set by a spec. The ``IN_`` prefix is the convention the runner already
    uses to exclude inputs from state tracking.
    """
    text = resolve_model(model_version, root).network_bnd.read_text(encoding="utf-8")
    logic = dict(re.findall(r"Node\s+(\w+)\s*\{\s*logic\s*=\s*([^;]+);", text))
    return tuple(
        sorted(
            n
            for n, e in logic.items()
            if n.startswith("IN_") and re.fullmatch(rf"[\s(]*{n}[\s)]*", e)
        )
    )


def _bool(value: Any, where: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1) and not isinstance(value, float):
        return bool(value)
    raise PerturbationSpecError(f"{where} must be true/false or 0/1, got {value!r}")


def parse_spec(payload: dict[str, Any], *, source: str = "<dict>") -> PerturbationSpec:
    if not isinstance(payload, dict):
        raise PerturbationSpecError(f"{source}: a spec is a mapping")
    for key, reason in _RESERVED_KEYS.items():
        if key in payload:
            raise PerturbationSpecError(f"{source}: {key!r} is refused: {reason}")
    unknown = sorted(set(payload) - _ALLOWED_KEYS)
    if unknown:
        raise PerturbationSpecError(f"{source}: unknown keys {unknown}")
    schema = payload.get("schema", SPEC_SCHEMA)
    if schema != SPEC_SCHEMA:
        raise PerturbationSpecError(f"{source}: schema must be {SPEC_SCHEMA}")
    for required in ("name", "model_version", "start"):
        if not isinstance(payload.get(required), str) or not payload[required]:
            raise PerturbationSpecError(f"{source}: {required!r} is required")
    if not _NAME_RE.fullmatch(payload["name"]):
        raise PerturbationSpecError(
            f"{source}: name must match {_NAME_RE.pattern}, got {payload['name']!r}"
        )
    changes = payload.get("input_changes") or {}
    interventions = payload.get("interventions") or []
    variants = payload.get("rule_variants") or {}
    if not isinstance(changes, dict) or not isinstance(variants, dict):
        raise PerturbationSpecError(f"{source}: input_changes/rule_variants are maps")
    if isinstance(interventions, str) or not isinstance(interventions, list):
        raise PerturbationSpecError(f"{source}: interventions is a list of ids")
    return PerturbationSpec(
        name=payload["name"],
        model_version=payload["model_version"],
        start=payload["start"],
        input_changes={
            str(k): _bool(v, f"input_changes.{k}") for k, v in changes.items()
        },
        interventions=tuple(str(i) for i in interventions),
        rule_variants={str(k): str(v) for k, v in variants.items()},
        description=str(payload.get("description") or ""),
    )


def load_spec(path: Path) -> PerturbationSpec:
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    return parse_spec(payload, source=str(path))


def start_step(spec: PerturbationSpec, root: Path | None = None):
    """The starting protocol and its last step: the state the perturbation acts on."""
    protocol = get_protocol(spec.start, root, model_version=spec.model_version)
    return protocol, protocol.steps[-1]


def validate_spec(spec: PerturbationSpec, root: Path | None = None) -> None:
    """Refuse anything the runner could not execute exactly as declared."""
    active_root = root or repo_root()
    if spec.model_version not in available_models(active_root):
        raise PerturbationSpecError(f"unknown model_version {spec.model_version!r}")
    try:
        _, step = start_step(spec, active_root)
    except (KeyError, ValueError) as exc:
        raise PerturbationSpecError(f"start protocol {spec.start!r}: {exc}") from exc
    if spec.is_empty:
        raise PerturbationSpecError(f"{spec.name}: the spec declares no effect")
    inputs = set(input_nodes(spec.model_version, active_root))
    for node, value in spec.input_changes.items():
        if node not in inputs:
            raise PerturbationSpecError(
                f"{node} is not a declared input of {spec.model_version}; only "
                "input nodes can be changed, and a node knockout is not offered"
            )
        if node not in step.input_states:
            raise PerturbationSpecError(
                f"{node} is not declared by the last step of {spec.start}, so its value "
                "at the perturbation boundary is not a declared protocol setting; "
                "only declared inputs can be changed"
            )
        if step.input_states[node] == value:
            raise PerturbationSpecError(
                f"{node} is already {value} at the end of {spec.start}; the change "
                "would change nothing"
            )
    if len(set(spec.interventions)) != len(spec.interventions):
        raise PerturbationSpecError("an intervention is named twice")
    already = sorted(set(spec.interventions) & set(step.interventions))
    if already:
        raise PerturbationSpecError(
            f"{', '.join(already)} is already active in {spec.start}"
        )
    if spec.interventions:
        library = load_intervention_library(active_root)
        view = library_for_version(library, spec.model_version)
        for iv in spec.interventions:
            if iv not in view:
                raise PerturbationSpecError(
                    f"{iv!r} has no library row for {spec.model_version}"
                )
    if spec.rule_variants:
        try:
            resolve_rule_variants(
                model_version=spec.model_version,
                variant_selection=spec.rule_variants,
                root=active_root,
            )
        except ValueError as exc:
            raise PerturbationSpecError(str(exc)) from exc


def effect_provenance(
    spec: PerturbationSpec, root: Path | None = None
) -> list[dict[str, Any]]:
    """One machine-readable record per declared effect, with its provenance class."""
    active_root = root or repo_root()
    _, step = start_step(spec, active_root)
    records: list[dict[str, Any]] = []
    for node, value in sorted(spec.input_changes.items()):
        records.append(
            {
                "provenance_class": INPUT_CHANGE,
                "node": node,
                "from": step.input_states.get(node),
                "to": value,
                "semantics": "the input is set at the perturbation boundary and "
                "held for the whole perturbed phase, as a protocol step would",
            }
        )
    if spec.interventions:
        library = load_intervention_library(active_root)
        view = library_for_version(library, spec.model_version)
        for iv in spec.interventions:
            try:
                effects = view[iv]
            except KeyError as exc:  # pragma: no cover - validate_spec refuses first
                raise InterventionError(iv) from exc
            records.append(
                {
                    "provenance_class": REGISTERED_INTERVENTION,
                    "intervention_id": iv,
                    "intervention_class": effects[0].intervention_class,
                    "effects": [
                        {
                            "target_node": e.target_node,
                            "mode": e.mode,
                            "mapping_basis": e.mapping_basis,
                            "evidence_ids": list(e.evidence_ids),
                            "claim_boundary": e.claim_boundary,
                        }
                        for e in effects
                    ],
                }
            )
    for family, variant in sorted(spec.rule_variants.items()):
        records.append(
            {
                "provenance_class": REGISTERED_RULE_VARIANT,
                "family": family,
                "variant": variant,
            }
        )
    return records
