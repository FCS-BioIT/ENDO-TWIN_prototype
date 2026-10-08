"""Intervention library and perturbation rendering.

An intervention (a reagent or a genetic manipulation) is not a network node
here. It is a set of effects on biological nodes, listed in
``config/intervention_library.tsv``, which this module renders into an
executable ``.bnd`` text. The rendered text goes through the same
``render_network_with_logic_overrides`` the runner uses for rule variants, so it
can be hashed and diffed like any other model file.

Stage 1 added the library and ``intervention_logic_overrides``. Stage 2 added
``legacy_route_overrides``, which the runner uses for every model version the
library covers. Stage 4a lets ``intervention_logic_overrides`` compose several
interventions, so a multi-target compound or a combination is a set of effects
rather than another network node.

A row has one of three mapping bases, and they are licensed differently:

- ``executable_legacy_behaviour`` re-describes a veto the ``.bnd`` already
  encodes through a legacy ``IN_*`` input. Its licence is the Stage 2 check in
  ``legacy_route_overrides``: the rendering must reproduce the legacy rule
  exhaustively. That route keeps the legacy ``IN_*`` nodes but makes no rule
  read them: the protocol still sets them, which marks when an intervention is
  active, and the engine alone carries the effect.
- ``direct_supported_effect`` (O8) states an effect on a biological node that no
  ``IN_*`` node encodes, so there is no legacy rule to reproduce. Its licence is
  checked when the library is loaded (``_license_direct_effects``): no marker,
  the one authorised mode, a target the primitive can mean and that the O8c
  target policy admits, evidence that resolves in the evidence register, and an
  approved effect-level adjudication bound to the row (O8b,
  ``perturbations/adjudication.py``). It is a modelling claim the row makes and
  a reviewer approves, never something the engine infers.
- ``migrated_legacy_behaviour`` (Stage 3) is a legacy row carried to a model
  version that deleted its marker. Its licence is checked when the library is
  loaded (``_license_migrated_effects``): the parent version, read from the
  model's own ``provenance.toml [increment]``, has an
  ``executable_legacy_behaviour`` row for the same intervention, and the child's
  rule, vetoed or not, equals the parent's legacy rule with the marker ON or OFF,
  exhaustively. Gate G8 adds the dynamic proof. See
  ``docs/intervention_layer_stage3.md``.

One intervention id may have rows for several model versions; every lookup
selects the rows of the version being rendered (``library_for_version``).

The two converge only after their licence, as ``(target, mode)`` effects that
compose and render the same way. See ``docs/intervention_layer_refactor_plan.md``
and ``docs/o8_markerless_interventions.md``.
"""

from __future__ import annotations

import csv
import functools
import itertools
import re
import types
from dataclasses import dataclass, replace
from pathlib import Path

import tomllib

from dt_adoc.maboss_adapter import (
    LOGIC_LINE_RE,
    NODE_BLOCK_RE,
    render_network_with_logic_overrides,
)
from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import resolve_model

LIBRARY_PATH = Path("config/intervention_library.tsv")
LIBRARY_COLUMNS = (
    "intervention_id",
    "intervention_label",
    "intervention_class",
    "model_version",
    "legacy_input_node",
    "legacy_perturbation_ids",
    "target_node",
    "mode",
    "mapping_basis",
    "model_abstraction",
    "abstraction_sources",
    "evidence_ids",
    "claim_boundary",
)

#: The target loses its activating rule while the intervention is active. Under
#: MaBoSS default rates it cannot switch on, and an active target switches off
#: at the model's default down-rate. It is not an instantaneous clamp.
ACTIVITY_VETO = "activity_veto"
#: The model version encodes no effect for this intervention. A statement about
#: the model's rules, not about the reagent.
NO_EXECUTABLE_EFFECT = "no_executable_effect"
MODES = (ACTIVITY_VETO, NO_EXECUTABLE_EFFECT)
#: Modes that render an effect on a target node. A mode outside this set is
#: refused rather than rendered, so adding one to ``MODES`` cannot silently make
#: it behave like a veto. Patched by the tests that exercise a second mode.
TARGETED_MODES = (ACTIVITY_VETO,)

#: Any kinetic declaration, wherever it sits in a node block.
_KINETIC_RE = re.compile(r"\b(?:rate_up|rate_down|max_rate)\s*=")
#: The row reproduces a veto the ``.bnd`` already encodes through a legacy input,
#: and the Stage 2 check proves it.
LEGACY_BASIS = "executable_legacy_behaviour"
#: The row states an effect on a biological node that no ``IN_*`` node encodes.
#: It makes no equivalence claim, so its licence is evidence and the checks in
#: ``_license_direct_effects`` instead.
DIRECT_BASIS = "direct_supported_effect"
#: A legacy row carried to a version whose marker was removed. It names no
#: marker; its licence is exhaustive equivalence with the parent version's
#: legacy row of the same intervention (``_license_migrated_effects``).
MIGRATED_BASIS = "migrated_legacy_behaviour"
MAPPING_BASES = (LEGACY_BASIS, DIRECT_BASIS, MIGRATED_BASIS)
#: The only mode a migrated row may carry: the vetoes are what Stage 3 migrates.
MIGRATED_MODES = (ACTIVITY_VETO,)
#: The only mode a direct row may carry. Deliberately narrower than ``MODES``:
#: ``no_executable_effect`` records a model's silence about a reagent it already
#: names, which a row with no legacy input has no reason to say.
DIRECT_MODES = (ACTIVITY_VETO,)
EVIDENCE_REGISTER_PATH = Path("context/evidence-register.tsv")


class InterventionError(ValueError):
    """The library or a rendering request is outside what the engine supports."""


@dataclass(frozen=True)
class InterventionEffect:
    intervention_id: str
    intervention_label: str
    intervention_class: str
    model_version: str
    legacy_input_node: str
    legacy_perturbation_ids: tuple[str, ...]
    target_node: str
    mode: str
    mapping_basis: str
    model_abstraction: str
    abstraction_sources: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    claim_boundary: str
    #: For a ``migrated_legacy_behaviour`` row only: the version whose legacy row
    #: licenses it, read from the model's provenance when the row is licensed.
    parent_model_version: str = ""
    #: For a ``direct_supported_effect`` row only: the approval that licenses it
    #: and the sha256 of that ledger row, filled in when the row is licensed.
    adjudication_id: str = ""
    adjudication_sha256: str = ""


def _split(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(";") if part.strip())


def read_library_rows(root: Path | None = None) -> list[InterventionEffect]:
    """The library's rows, each checked on its own, and no licence.

    ``load_intervention_library`` is the only reader that executes anything. This
    one exists so a direct row's digest can be printed before it is approved.
    """
    path = (root or repo_root()) / LIBRARY_PATH
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != LIBRARY_COLUMNS:
            raise InterventionError(f"{LIBRARY_PATH} columns are {reader.fieldnames}")
        rows = list(reader)
    effects: list[InterventionEffect] = []
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise InterventionError(f"{LIBRARY_PATH} has a ragged row: {row}")
        effect = InterventionEffect(
            intervention_id=row["intervention_id"],
            intervention_label=row["intervention_label"],
            intervention_class=row["intervention_class"],
            model_version=row["model_version"],
            legacy_input_node=row["legacy_input_node"],
            legacy_perturbation_ids=_split(row["legacy_perturbation_ids"]),
            target_node=row["target_node"],
            mode=row["mode"],
            mapping_basis=row["mapping_basis"],
            model_abstraction=row["model_abstraction"],
            abstraction_sources=_split(row["abstraction_sources"]),
            evidence_ids=_split(row["evidence_ids"]),
            claim_boundary=row["claim_boundary"],
        )
        if effect.mapping_basis not in MAPPING_BASES:
            raise InterventionError(f"unknown mapping basis {effect.mapping_basis!r}")
        if effect.mode not in MODES:
            raise InterventionError(f"unknown mode {effect.mode!r}")
        if (effect.mode == NO_EXECUTABLE_EFFECT) != (effect.target_node == ""):
            raise InterventionError(
                f"{effect.intervention_id}: a target is required for "
                f"{ACTIVITY_VETO} and forbidden for {NO_EXECUTABLE_EFFECT}"
            )
        if effect.mapping_basis == LEGACY_BASIS:
            if effect.mode == ACTIVITY_VETO and not effect.legacy_perturbation_ids:
                raise InterventionError(
                    f"{effect.intervention_id}: a veto row names no declared "
                    "perturbation"
                )
            if not effect.legacy_input_node:
                raise InterventionError(f"incomplete library row: {row}")
        elif effect.mapping_basis == MIGRATED_BASIS:
            # Its marker is gone from this version; the parent's row names it.
            if effect.legacy_input_node or effect.legacy_perturbation_ids:
                raise InterventionError(
                    f"{effect.intervention_id}: a {MIGRATED_BASIS} row names no "
                    "legacy input and no legacy perturbation"
                )
            if effect.mode not in MIGRATED_MODES:
                raise InterventionError(
                    f"{effect.intervention_id}: a {MIGRATED_BASIS} row takes mode "
                    f"{' or '.join(MIGRATED_MODES)}, not {effect.mode!r}"
                )
        else:
            # A marker or a declared perturbation would make the row a legacy
            # one in all but name, and escape the check that licenses those.
            if effect.legacy_input_node or effect.legacy_perturbation_ids:
                raise InterventionError(
                    f"{effect.intervention_id}: a {DIRECT_BASIS} row names no "
                    "legacy input and no legacy perturbation"
                )
            if effect.mode not in DIRECT_MODES:
                raise InterventionError(
                    f"{effect.intervention_id}: a {DIRECT_BASIS} row takes mode "
                    f"{' or '.join(DIRECT_MODES)}, not {effect.mode!r}"
                )
        if not (effect.intervention_id and effect.model_version):
            raise InterventionError(f"incomplete library row: {row}")
        if not (
            effect.evidence_ids
            and effect.abstraction_sources
            and effect.model_abstraction
            and effect.claim_boundary
        ):
            raise InterventionError(
                f"{effect.intervention_id}: row carries no provenance"
            )
        effects.append(effect)
    return effects


def load_intervention_library(
    root: Path | None = None,
) -> dict[str, tuple[InterventionEffect, ...]]:
    """Read and validate the library, keyed by intervention id."""
    library: dict[str, list[InterventionEffect]] = {}
    for effect in read_library_rows(root):
        library.setdefault(effect.intervention_id, []).append(effect)

    seen_inputs: dict[str, str] = {}
    for intervention_id, all_effects in library.items():
        # The same reagent across versions: its identity must not drift.
        if (
            len({(e.intervention_label, e.intervention_class) for e in all_effects})
            != 1
        ):
            raise InterventionError(
                f"{intervention_id}: rows disagree on the label or class across "
                "model versions"
            )
        for version in sorted({e.model_version for e in all_effects}):
            effects = [e for e in all_effects if e.model_version == version]
            _check_intervention(intervention_id, effects, seen_inputs)
    licensed = {
        **_license_direct_effects(library, root=root or repo_root()),
        **_license_migrated_effects(library, root=root or repo_root()),
    }
    return {
        key: tuple(licensed.get(e, e) for e in value) for key, value in library.items()
    }


def library_for_version(
    library: dict[str, tuple[InterventionEffect, ...]], model_version: str
) -> dict[str, tuple[InterventionEffect, ...]]:
    """The rows of ``model_version`` only, keyed by intervention id.

    Ids with no row for that version are absent, so a function given this view
    can read intervention-level fields off any one row.
    """
    view = {}
    for intervention_id, effects in library.items():
        selected = tuple(e for e in effects if e.model_version == model_version)
        if selected:
            view[intervention_id] = selected
    return view


def _check_intervention(
    intervention_id: str,
    effects: list[InterventionEffect],
    seen_inputs: dict[str, str],
) -> None:
    """The per-(intervention, version) invariants."""
    shared = {
        (
            e.intervention_label,
            e.intervention_class,
            e.model_version,
            e.legacy_input_node,
            e.legacy_perturbation_ids,
            e.mode,
            e.mapping_basis,
        )
        for e in effects
    }
    if len(shared) != 1:
        raise InterventionError(
            f"{intervention_id}: rows disagree on an intervention-level field"
        )
    targets = [e.target_node for e in effects]
    if len(set(targets)) != len(targets):
        raise InterventionError(f"{intervention_id}: a target is listed twice")
    if effects[0].mode == NO_EXECUTABLE_EFFECT and len(effects) != 1:
        raise InterventionError(
            f"{intervention_id}: {NO_EXECUTABLE_EFFECT} takes one row"
        )
    if effects[0].mapping_basis != LEGACY_BASIS:
        return
    key = f"{effects[0].model_version}:{effects[0].legacy_input_node}"
    if key in seen_inputs:
        raise InterventionError(
            f"{intervention_id} and {seen_inputs[key]} share the legacy input {key}"
        )
    seen_inputs[key] = intervention_id


def _license_direct_effects(
    library: dict[str, list[InterventionEffect]], *, root: Path
) -> dict[InterventionEffect, InterventionEffect]:
    """License every ``direct_supported_effect`` row, or refuse the library.

    Returns each such row with its approval attached. A direct row has no legacy
    rule to reproduce, so what licenses it is checked here, against the model it
    names and the repository it is loaded from. The mechanical checks (O8) come
    first:

    - its target is a node the veto can mean (``_target_logic``: one logic line,
      not an input, no declared rate), reads no legacy input, and has a
      ``node_dictionary.tsv`` row;
    - the O8c target policy admits the node (``adjudication.policy_refusal``);
    - each evidence id resolves in the evidence register;
    - each abstraction source names a file that exists.

    Then the scientific licence (O8b, ``adjudication.license_effect``): exactly
    one approved ledger row under the row's own key, citing the same evidence
    and bound to the row's digest. Register status is not read as a licence.
    Then the intervention-level admission (Stage 4b,
    ``adjudication.check_admission``): one declaration per intervention and
    version that C1-C8 hold to ``config/node_entity_map.tsv``, an approvable
    ``system_grade``, approvals naming that declaration's digest, and a current
    expressivity artefact for the version.

    The ledger is validated whenever it exists, direct rows or not, so a ledger
    row can never name a legacy or migrated intervention. Nothing here infers a
    target or an effect. See ``docs/o8b_direct_effect_governance.md``.
    """
    from dt_adoc.perturbations import adjudication

    ledger = adjudication.load_adjudications(root)
    if ledger is not None:
        adjudication.validate_ledger(ledger, library, root)
    direct = [
        effect
        for effects in library.values()
        for effect in effects
        if effect.mapping_basis == DIRECT_BASIS
    ]
    if not direct:
        # Still read: a declaration naming no direct row, or a malformed entity
        # map, refuses the library (Stage 4b, C1).
        adjudication.check_admission(library, ledger, root)
        return {}
    register = root / EVIDENCE_REGISTER_PATH
    if not register.is_file():
        raise InterventionError(
            f"{DIRECT_BASIS} rows need the evidence register at {EVIDENCE_REGISTER_PATH}"
        )
    with register.open(encoding="utf-8", newline="") as handle:
        register_status = {
            row["evidence_id"]: row["status"]
            for row in csv.DictReader(handle, delimiter="\t")
        }
    policy = adjudication.load_target_policy(root)
    legacy_inputs: dict[str, set[str]] = {}
    for effects in library.values():
        for effect in effects:
            if effect.mapping_basis == LEGACY_BASIS:
                legacy_inputs.setdefault(effect.model_version, set()).add(
                    effect.legacy_input_node
                )
    models: dict[str, tuple[dict[str, str], dict[str, str]]] = {}
    licensed: dict[InterventionEffect, InterventionEffect] = {}
    for effect in direct:
        where = f"{effect.intervention_id} -> {effect.target_node}"
        if effect.model_version not in models:
            try:
                spec = resolve_model(effect.model_version, root)
            except ValueError as error:
                raise InterventionError(f"{where}: {error}") from error
            with spec.node_dictionary.open(encoding="utf-8", newline="") as handle:
                roles = {
                    row["node_id"]: row["model_role"]
                    for row in csv.DictReader(handle, delimiter="\t")
                }
            models[effect.model_version] = (
                _node_blocks(spec.network_bnd.read_text(encoding="utf-8")),
                roles,
            )
        blocks, roles = models[effect.model_version]
        try:
            logic = _target_logic(blocks, effect.target_node)
        except InterventionError as error:
            raise InterventionError(f"{where}: {error}") from error
        read = _evaluable(logic)[1] & legacy_inputs.get(effect.model_version, set())
        if read:
            # Its rule is one the legacy route rewrites only if a legacy row
            # targets it too, so the veto would not be over the rule that runs.
            targeted = {
                e.target_node
                for effects in library.values()
                for e in effects
                if e.mapping_basis == LEGACY_BASIS
                and e.model_version == effect.model_version
            }
            if effect.target_node not in targeted:
                raise InterventionError(
                    f"{where}: the target reads legacy inputs {sorted(read)} that "
                    "no legacy row routes"
                )
        role = roles.get(effect.target_node)
        if role is None:
            raise InterventionError(f"{where}: the target has no node_dictionary row")
        refusal = adjudication.policy_refusal(policy, effect.target_node, role)
        if refusal:
            raise InterventionError(f"{where}: {refusal}")
        unknown = sorted(set(effect.evidence_ids) - set(register_status))
        if unknown:
            raise InterventionError(
                f"{where}: evidence {unknown} is not in {EVIDENCE_REGISTER_PATH}"
            )
        for source in effect.abstraction_sources:
            if not (root / source.split("#", 1)[0]).is_file():
                raise InterventionError(f"{where}: source {source} does not exist")
        licensed[effect] = adjudication.license_effect(effect, ledger, register_status)
    # Stage 4b: the intervention-level admission (C1-C8, the declaration digest
    # and a current expressivity artefact), once every effect is approved.
    adjudication.check_admission(library, ledger, root)
    return licensed


def _license_migrated_effects(
    library: dict[str, list[InterventionEffect]], *, root: Path
) -> dict[InterventionEffect, InterventionEffect]:
    """License every ``migrated_legacy_behaviour`` row, or refuse the library.

    Returns each such row with ``parent_model_version`` filled in. A row is
    licensed when, for its own model version (the child):

    - the child's ``provenance.toml [increment]`` names a parent version;
    - the parent has ``executable_legacy_behaviour`` rows for the same
      intervention, with the same mode, the same target set, and per target the
      same evidence and abstraction;
    - the parent's marker is not a node of the child;
    - per target, exhaustively over every assignment, the child's rule equals the
      parent's with every removed marker OFF, and the parent's rule with this
      marker ON (the others OFF) is false -- which is what ``activity_veto`` of
      the child's rule renders. So the child, vetoed or not, executes the
      parent's legacy rule with the marker ON or OFF;
    - every abstraction source exists.

    This is the Stage 2 check carried across one version step. It says nothing
    about dynamics; gate G8 is the test of that.
    """
    groups: dict[tuple[str, str], list[InterventionEffect]] = {}
    for effects in library.values():
        for effect in effects:
            if effect.mapping_basis == MIGRATED_BASIS:
                groups.setdefault(
                    (effect.intervention_id, effect.model_version), []
                ).append(effect)
    licensed: dict[InterventionEffect, InterventionEffect] = {}
    for (intervention_id, version), effects in sorted(groups.items()):
        where = f"{intervention_id} ({version})"
        try:
            spec = resolve_model(version, root)
        except ValueError as error:
            raise InterventionError(f"{where}: {error}") from error
        increment = tomllib.loads(spec.provenance.read_text(encoding="utf-8")).get(
            "increment", {}
        )
        parent = increment.get("parent_model_version")
        if not parent:
            raise InterventionError(
                f"{where}: the model's provenance [increment] names no parent version"
            )
        parent_rows = [
            e for e in library.get(intervention_id, ()) if e.model_version == parent
        ]
        if not parent_rows or any(e.mapping_basis != LEGACY_BASIS for e in parent_rows):
            raise InterventionError(
                f"{where}: {parent} has no {LEGACY_BASIS} row for {intervention_id}"
            )
        if {e.mode for e in parent_rows} != {effects[0].mode}:
            raise InterventionError(f"{where}: the mode differs from {parent}'s row")
        by_target = {e.target_node: e for e in parent_rows}
        if set(by_target) != {e.target_node for e in effects}:
            raise InterventionError(f"{where}: the targets differ from {parent}'s row")
        try:
            parent_spec = resolve_model(parent, root)
        except ValueError as error:
            raise InterventionError(f"{where}: {error}") from error
        child_blocks = _node_blocks(spec.network_bnd.read_text(encoding="utf-8"))
        parent_blocks = _node_blocks(
            parent_spec.network_bnd.read_text(encoding="utf-8")
        )
        marker = parent_rows[0].legacy_input_node
        if marker in child_blocks:
            raise InterventionError(
                f"{where}: {marker} is still a node of {version}; a row whose marker "
                f"exists is {LEGACY_BASIS}"
            )
        removed = {
            e.legacy_input_node
            for effects_ in library.values()
            for e in effects_
            if e.model_version == parent
            and e.mapping_basis == LEGACY_BASIS
            and e.legacy_input_node not in child_blocks
        }
        for effect in effects:
            target = f"{where} -> {effect.target_node}"
            origin = by_target[effect.target_node]
            if (
                effect.evidence_ids != origin.evidence_ids
                or effect.model_abstraction != origin.model_abstraction
            ):
                raise InterventionError(
                    f"{target}: the evidence or abstraction differs from {parent}'s row"
                )
            try:
                child_logic = _target_logic(child_blocks, effect.target_node)
                parent_logic = _target_logic(parent_blocks, effect.target_node)
            except InterventionError as error:
                raise InterventionError(f"{target}: {error}") from error
            _check_migrated_rule(target, child_logic, parent_logic, marker, removed)
            for source in effect.abstraction_sources:
                if not (root / source.split("#", 1)[0]).is_file():
                    raise InterventionError(f"{target}: source {source} does not exist")
            licensed[effect] = replace(effect, parent_model_version=parent)
    return licensed


def _check_migrated_rule(
    where: str, child_logic: str, parent_logic: str, marker: str, removed: set[str]
) -> None:
    child_expression, child_names = _evaluable(child_logic)
    parent_expression, parent_names = _evaluable(parent_logic)
    if child_names & removed:
        raise InterventionError(
            f"{where}: the rule still reads {sorted(child_names & removed)}"
        )
    off = dict.fromkeys(removed, False)
    free = sorted((child_names | parent_names) - removed)
    for values in itertools.product((False, True), repeat=len(free)):
        point = dict(zip(free, values))
        if _value(child_expression, point) != _value(
            parent_expression, {**point, **off}
        ):
            raise InterventionError(
                f"{where}: the rule is not the parent's with {sorted(removed)} OFF"
            )
        if _value(parent_expression, {**point, **off, marker: True}):
            raise InterventionError(
                f"{where}: the parent's rule with {marker} ON is not a veto"
            )


def named_effect_records(
    intervention_ids: list[str] | tuple[str, ...],
    library: dict[str, tuple[InterventionEffect, ...]],
    model_version: str | None = None,
) -> list[dict[str, object]]:
    """One provenance record per library row of each named intervention.

    With the library's sha256, this says which licence each executed effect
    rests on: a legacy marker it reproduces, the evidence a direct row cites and
    the approval that licenses it, or the parent version a migrated row
    reproduces. ``model_version`` selects that
    version's rows; without it every row of each id is listed.
    """
    if model_version is not None:
        library = library_for_version(library, model_version)
    records = []
    for intervention_id in intervention_ids:
        for effect in library.get(intervention_id, ()):
            record: dict[str, object] = {
                "intervention_id": effect.intervention_id,
                "mapping_basis": effect.mapping_basis,
                "legacy_input_node": effect.legacy_input_node,
                "target_node": effect.target_node,
                "mode": effect.mode,
                "evidence_ids": list(effect.evidence_ids),
                "abstraction_sources": list(effect.abstraction_sources),
                "claim_boundary": effect.claim_boundary,
            }
            if effect.mapping_basis == MIGRATED_BASIS:
                record["model_version"] = effect.model_version
                record["parent_model_version"] = effect.parent_model_version
            elif effect.mapping_basis == DIRECT_BASIS:
                from dt_adoc.perturbations.adjudication import library_row_digest

                record["model_version"] = effect.model_version
                record["adjudication_id"] = effect.adjudication_id
                record["adjudication_sha256"] = effect.adjudication_sha256
                record["library_row_sha256"] = library_row_digest(effect)
            records.append(record)
    return records


def activity_veto_logic(logic: str) -> str:
    """The vetoed rule: false everywhere, with the original rule left readable.

    ``1`` rather than ``TRUE``, because MaBoSS reads ``TRUE`` as an undefined node.
    """
    return f"({logic}) and not 1"


def _node_blocks(network_text: str) -> dict[str, str]:
    return {
        match.group(2): match.group(3) for match in NODE_BLOCK_RE.finditer(network_text)
    }


def _target_logic(blocks: dict[str, str], target: str) -> str:
    """The target's single logic expression, refusing anything the veto cannot mean."""
    body = blocks.get(target)
    if body is None:
        raise InterventionError(f"target {target} is not a network node")
    logic_lines = LOGIC_LINE_RE.findall(body)
    if len(logic_lines) != 1:
        raise InterventionError(f"target {target} has no single logic line")
    logic = logic_lines[0][1].strip()
    if ";" in logic:
        raise InterventionError(
            f"target {target} has another statement on its logic line"
        )
    if re.fullmatch(rf"[\s(]*{re.escape(target)}[\s)]*", logic):
        raise InterventionError(f"target {target} is an input node")
    if _KINETIC_RE.search(body):
        # The veto's meaning rests on MaBoSS default rates; with a declared
        # rate it would be something else, so refuse rather than guess.
        raise InterventionError(f"target {target} declares a rate")
    return logic


def intervention_logic_overrides(
    network_text: str,
    intervention_ids: list[str] | tuple[str, ...],
    *,
    model_version: str,
    library: dict[str, tuple[InterventionEffect, ...]],
) -> dict[str, str]:
    """The ``{node: logic}`` overrides that the active interventions of one phase imply.

    In the shape ``render_network_with_logic_overrides`` takes, so a caller can
    hand them to the runner's existing rendering path unchanged.

    **Composition** (Stage 4a). Several interventions compose as the union of
    their effects, which is what applying them together means here and adds no
    node to the network:

    - a compound with several targets vetoes each of them;
    - two interventions that veto the same target leave one veto. The veto makes
      the rule false whatever else holds, so a second one changes nothing. This
      is an algebraic consequence of the primitive, not a potency assumption:
      the model carries no dose, so "both hit this node" and "one hits it" are
      the same executable state;
    - two interventions claiming one target under *different* modes are refused,
      because nothing says which should win. Only ``activity_veto`` has a target
      today, so this cannot yet fire; it is here so that adding a mode cannot
      silently resolve a conflict.

    Composition is an executable statement about this model, never a claim that
    the compounds interact. Anything read off a combination is a conditional
    model-internal prediction, like any other perturbation here.
    """
    blocks = _node_blocks(network_text)
    overrides: dict[str, str] = {}
    for target, (_, mode) in _composed_effects(
        intervention_ids, model_version=model_version, library=library
    ).items():
        overrides[target] = _render_mode(mode, _target_logic(blocks, target))
    return overrides


def _render_mode(mode: str, logic: str) -> str:
    """``logic`` under ``mode``. Only the veto renders; anything else is refused.

    Dispatching on the mode, rather than vetoing whatever reaches this point,
    is what keeps a mode added to ``TARGETED_MODES`` without a renderer from
    silently behaving as a veto.
    """
    if mode == ACTIVITY_VETO:
        return activity_veto_logic(logic)
    raise InterventionError(f"no rendering for mode {mode!r}")


def _composed_effects(
    intervention_ids: list[str] | tuple[str, ...],
    *,
    model_version: str,
    library: dict[str, tuple[InterventionEffect, ...]],
    claimed: dict[str, tuple[str, str]] | None = None,
) -> dict[str, tuple[str, str]]:
    """The named interventions as ``{target: (intervention_id, mode)}``.

    The point where legacy-backed and direct rows converge. Both have been
    licensed by then (the legacy ones by the Stage 2 check, the direct ones when
    the library was loaded), and from here on a row's basis does not matter.

    ``claimed`` seeds targets already under an effect, such as the ones a legacy
    marker vetoes in this phase, so that a conflicting mode is refused against
    them too. Only the named interventions' targets are returned.
    """
    if isinstance(intervention_ids, str):
        raise InterventionError("intervention_ids is a sequence of ids, not one id")
    ids = list(intervention_ids)
    if len(set(ids)) != len(ids):
        raise InterventionError(f"an intervention is named twice: {sorted(ids)}")
    claimed = dict(claimed or {})
    composed: dict[str, tuple[str, str]] = {}
    view = library_for_version(library, model_version)
    for intervention_id in ids:
        if intervention_id not in library:
            raise InterventionError(f"unknown intervention {intervention_id!r}")
        effects = view.get(intervention_id)
        if effects is None:
            versions = ", ".join(
                sorted({e.model_version for e in library[intervention_id]})
            )
            raise InterventionError(
                f"{intervention_id} is defined for {versions}, not {model_version}"
            )
        for effect in effects:
            if effect.mode == NO_EXECUTABLE_EFFECT:
                continue
            if effect.mode not in TARGETED_MODES:
                # Without this a new mode would be rendered as a veto, which is
                # worse than the conflict the ``claimed`` check below refuses.
                raise InterventionError(f"unsupported mode {effect.mode!r}")
            target = effect.target_node
            previous = claimed.get(target)
            if previous is not None and previous[1] != effect.mode:
                raise InterventionError(
                    f"{previous[0]} and {intervention_id} claim {target} under "
                    f"different modes ({previous[1]}, {effect.mode})"
                )
            claimed[target] = (intervention_id, effect.mode)
            composed.setdefault(target, (intervention_id, effect.mode))
    return composed


def render_interventions(
    network_text: str,
    intervention_ids: list[str] | tuple[str, ...],
    *,
    model_version: str,
    library: dict[str, tuple[InterventionEffect, ...]],
) -> str:
    """Render the active interventions of one phase into ``network_text``."""
    overrides = intervention_logic_overrides(
        network_text, intervention_ids, model_version=model_version, library=library
    )
    return render_network_with_logic_overrides(network_text, logic_overrides=overrides)


_TOKEN_RE = re.compile(r"\s*(?:(\()|(\))|([A-Za-z_][A-Za-z0-9_]*)|([01]))")
_OPERATORS = {"and", "or", "not"}


def _evaluable(logic: str) -> tuple[str, frozenset[str]]:
    """``logic`` as a Python Boolean expression, and the node names it reads.

    Only parentheses, ``and``/``or``/``not``, node names and the literals 0 and 1
    are accepted, so evaluating it cannot do anything but Boolean arithmetic.
    """
    position, names = 0, set()
    text = logic.strip()
    while position < len(text):
        match = _TOKEN_RE.match(text, position)
        if match is None or match.end() == position:
            raise InterventionError(f"cannot check rule {logic!r}")
        word = match.group(3)
        if word is not None and word not in _OPERATORS:
            names.add(word)
        position = match.end()
    return text, frozenset(names)


@functools.lru_cache(maxsize=4096)
def _compiled(expression: str) -> types.CodeType:
    """``expression`` compiled exactly as ``eval`` of the string compiles it.

    ``eval`` of a string first strips leading spaces and tabs and names the
    source ``"<string>"``, so both are reproduced: every result and every
    refusal stay what string ``eval`` gives. The key is the whole expression
    and nothing else, so a changed rule is a new entry rather than a stale one.
    """
    return compile(expression.lstrip(" \t"), "<string>", "eval")


def _value(expression: str, assignment: dict[str, bool]) -> bool:
    # Only a ``str`` is cached; anything else goes to ``eval`` as before, so it
    # is accepted or refused exactly as it always was.
    code = _compiled(expression) if type(expression) is str else expression
    return bool(eval(code, {"__builtins__": {}}, assignment))


def legacy_route_overrides(
    network_text: str,
    input_values: dict[str, bool],
    *,
    model_version: str,
    library: dict[str, tuple[InterventionEffect, ...]],
    also_active: list[str] | tuple[str, ...] = (),
) -> dict[str, str]:
    """Overrides that move every library intervention of ``model_version`` into the engine.

    ``input_values`` gives the value each legacy input takes in this phase, as the
    protocol sets it. Every rule that the library targets has its legacy inputs
    replaced by ``0``, so no rule reads them any more, and is vetoed when one of
    the interventions acting on it is active.

    Before anything is rendered, each targeted rule is checked exhaustively: for
    every combination of legacy-input values, not only this phase's, the rendering
    that combination would get must equal the legacy rule. A library row that is
    not a pure veto of its target (an input that activates a rule, say) is
    therefore refused in every phase, never rendered.

    ``also_active`` names interventions to apply on top, which is how a
    combination is executed. Their vetoes are added *after* that check, so the
    check keeps its meaning: it establishes that the phase's legacy-driven
    rendering reproduces the legacy model, and ``also_active`` is then a declared
    departure from it. An intervention whose own legacy input is already active
    in this phase is refused rather than applied twice.

    Every member must be a library row. A legacy-backed member can only
    re-describe a veto this ``.bnd`` already contains, because the check above
    covers it. A ``direct_supported_effect`` member is how a compound the model
    does not encode is executed: the check above does not cover it, since it has
    no legacy rule to reproduce, and the loader's licence does instead. Its
    target is vetoed directly, with no ``IN_*`` node. See
    ``docs/o8_markerless_interventions.md``.
    """
    view = library_for_version(library, model_version)
    vetoing = {
        intervention_id: effects
        for intervention_id, effects in view.items()
        if effects[0].mode == ACTIVITY_VETO and effects[0].mapping_basis == LEGACY_BASIS
    }
    legacy_inputs = {effects[0].legacy_input_node for effects in vetoing.values()}
    missing = sorted(legacy_inputs - set(input_values))
    if missing:
        raise InterventionError(f"no value given for legacy inputs {missing}")
    acting: dict[str, set[str]] = {}
    modes: dict[str, str] = {}
    for effects in vetoing.values():
        for effect in effects:
            acting.setdefault(effect.target_node, set()).add(effect.legacy_input_node)
            modes[effect.target_node] = effect.mode
    blocks = _node_blocks(network_text)
    for name in sorted(legacy_inputs):
        # Disconnecting an input is only safe if it is constant within a phase:
        # a free input with no kinetics, changed by the protocol alone.
        body = blocks.get(name)
        logic_lines = LOGIC_LINE_RE.findall(body or "")
        if (
            body is None
            or len(logic_lines) != 1
            or logic_lines[0][1].strip() != name
            or _KINETIC_RE.search(body)
        ):
            raise InterventionError(f"legacy input {name} is not a constant input node")
    overrides: dict[str, str] = {}
    vetoed: set[str] = set()
    for target in sorted(acting):
        legacy_logic = _target_logic(blocks, target)
        disconnected = legacy_logic
        for name in sorted(legacy_inputs):
            disconnected = re.sub(rf"\b{re.escape(name)}\b", "0", disconnected)

        def rendering(values: dict[str, bool], target=target, text=disconnected) -> str:
            if any(values[name] for name in acting[target]):
                return activity_veto_logic(text)
            return text

        old_expression, old_names = _evaluable(legacy_logic)
        _, new_names = _evaluable(rendering(dict.fromkeys(legacy_inputs, True)))
        if new_names & legacy_inputs or _evaluable(disconnected)[1] & legacy_inputs:
            raise InterventionError(f"{target} still reads a legacy input")
        relevant = sorted((old_names & legacy_inputs) | acting[target])
        free = sorted((old_names | new_names) - legacy_inputs)
        for combination in itertools.product((False, True), repeat=len(relevant)):
            fixed = dict(zip(relevant, combination))
            new_expression = rendering({**dict.fromkeys(legacy_inputs, False), **fixed})
            for values in itertools.product((False, True), repeat=len(free)):
                point = {**dict(zip(free, values)), **fixed}
                if _value(new_expression, point) != _value(old_expression, point):
                    raise InterventionError(
                        f"{target}: the engine rendering is not equivalent to the legacy rule"
                    )
        phase = {name: bool(input_values[name]) for name in legacy_inputs}
        overrides[target] = rendering(phase)
        if any(phase[name] for name in acting[target]):
            vetoed.add(target)

    if isinstance(also_active, str):
        raise InterventionError("also_active is a sequence of ids, not one id")
    extra = list(also_active)
    for intervention_id in extra:
        effects = view.get(intervention_id)
        if effects is None or effects[0].mapping_basis != LEGACY_BASIS:
            continue
        legacy = effects[0].legacy_input_node
        if input_values.get(legacy, False):
            raise InterventionError(
                f"{intervention_id} is already active in this phase through "
                f"{legacy}; naming it again would apply it twice"
            )
    # The marker-driven vetoes of this phase are claims too, so a named effect
    # under another mode is refused against them rather than layered on top.
    marked = {target: (f"the marker on {target}", modes[target]) for target in vetoed}
    for target, (_, mode) in _composed_effects(
        extra, model_version=model_version, library=library, claimed=marked
    ).items():
        # Idempotent: a target another member already vetoes stays vetoed
        # once. Tracked rather than read back off the rendered text, so the
        # rule cannot turn on how a rendering happens to be spelled.
        if target in vetoed:
            continue
        if target in overrides:
            base = overrides[target]
        else:
            # A direct target no legacy row routes. Its rule reads no legacy
            # input (the loader refuses one that does), so it runs as written.
            base = _target_logic(blocks, target)
            if _evaluable(base)[1] & legacy_inputs:
                raise InterventionError(f"{target} still reads a legacy input")
        overrides[target] = _render_mode(mode, base)
        vetoed.add(target)
    return overrides
