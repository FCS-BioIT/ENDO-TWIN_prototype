"""Effect-level scientific licensing of ``direct_supported_effect`` rows (O8b/O8c).

O8 licenses a direct row mechanically: a legal target, evidence ids that
resolve, sources that exist. That establishes that a source is *registered*, not
that it supports the executed claim. This module adds the two things a
production direct row also needs, both read from data:

- an approved **effect adjudication** in ``config/direct_effect_adjudications.tsv``,
  keyed exactly by ``(intervention_id, model_version, target_node, mode)`` and
  bound to the library row's evidence set and content digest (O8b);
- a **target policy** in ``config/direct_effect_target_policy.tsv`` that refuses
  nodes whose veto would set a derived readout, state or route rather than act
  on a biological entity (O8c).

Evidence-register ``status`` is not read as a licence: it answers whether a
source exists, which is a different question. Legacy and migrated rows are never
read against the ledger; the ledger may not name them.

The design, vocabularies and definition of "approved" are pre-registered in
``docs/o8b_direct_effect_governance.md``. ``engine._license_direct_effects`` calls
this module after its own mechanical checks.

Stage 4b (``docs/stage4b_direct_admission.md``) adds the intervention-level half:
a declaration per intervention and version in
``config/direct_effect_target_declarations.tsv``, the completeness rules C1-C8
read against ``config/node_entity_map.tsv``, the approval's ``system_grade`` and
``target_declaration_sha256``, a current expressivity artefact, and the run-record
fields of §6.5. See ``check_admission`` and ``admission_record``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.engine import (
    DIRECT_BASIS,
    DIRECT_MODES,
    EVIDENCE_REGISTER_PATH,
    LEGACY_BASIS,
    LIBRARY_COLUMNS,
    LIBRARY_PATH,
    InterventionEffect,
    InterventionError,
    _evaluable,
    _node_blocks,
    _target_logic,
    load_intervention_library,
    read_library_rows,
)

ADJUDICATIONS_PATH = Path("config/direct_effect_adjudications.tsv")
TARGET_POLICY_PATH = Path("config/direct_effect_target_policy.tsv")
AUDIT_PATH = Path("docs/o8b_direct_effect_governance/v060_target_audit.tsv")
AUDIT_MODEL_VERSION = "adoc-literature-superset-v0.6.0"

ADJUDICATION_COLUMNS = (
    "adjudication_id",
    "intervention_id",
    "model_version",
    "target_node",
    "mode",
    "decision",
    "evidence_ids",
    "effect_evidence",
    "system_match",
    "biological_system",
    "library_row_sha256",
    "basis_record",
    "rationale",
    "adjudicator",
    "dated",
    # Stage 4b (docs/stage4b_direct_admission.md §6.2): the grade of the system
    # that produced the E2 measurement, and the declaration the approval rests on.
    "system_grade",
    "target_declaration_sha256",
)
APPROVED = "approved_for_model_execution"
DECISIONS = (APPROVED, "candidate", "rejected")
#: Test fixtures only. Approvable solely together with synthetic evidence.
SYNTHETIC = "synthetic_fixture"
#: What the cited evidence shows about this intervention acting on this target.
#: ``target_activity_reduced`` is the one approvable value and is deliberately
#: narrow: the executable mode is a *full* ``activity_veto``, and graded
#: engagement is open (O4, engagement fixed at 1), so evidence of a partial or
#: graded reduction -- a knockdown that leaves half the activity, a potentiator
#: -- is ``target_activity_partially_reduced`` and does not license the full
#: veto. The distinction is about the abstraction the model would execute, not
#: about how good the experiment is.
EFFECT_EVIDENCE = (
    "target_activity_reduced",
    "target_activity_partially_reduced",
    "target_abundance_reduced",
    "target_necessity_only",
    "adjacent_level_only",
    "phenotype_only",
    "inferred_from_class",
    SYNTHETIC,
)
#: How the evidence's biological system relates to the target node.
SYSTEM_MATCH = (
    "matches_model_compartment",
    "other_human_endometrial_compartment",
    "human_non_endometrial",
    "non_human",
    SYNTHETIC,
)
#: The only values an approval may carry. Widening either is a policy change
#: made here and in its test, never by a single approval.
APPROVABLE_EFFECT_EVIDENCE = ("target_activity_reduced",)
APPROVABLE_SYSTEM_MATCH = ("matches_model_compartment",)
#: Stage 4b §6.3: the system that produced the **E2 measurement** -- the one
#: cited measurement establishing that the node's activity is abolished -- not
#: the paper and not an average over the cited ids. A line may corroborate a
#: qualifying E2 id; it never raises the grade.
SYSTEM_GRADES = (
    "human_endometrium_in_vivo",
    "primary_human_endometrial",
    "primary_derived_other",
    "immortalised_endometrial_line",
    "endometrial_carcinoma_line",
    "non_endometrial_human",
    "non_human",
    SYNTHETIC,
)
#: ``primary_derived_other`` needs its equivalence reason in ``basis_record``;
#: that is reviewer judgement (§6.4), recorded and not loader-checked.
APPROVABLE_SYSTEM_GRADES = (
    "human_endometrium_in_vivo",
    "primary_human_endometrial",
    "primary_derived_other",
)

POLICY_COLUMNS = ("scope", "key", "policy", "basis", "rationale")
POLICY_SCOPES = ("role", "node")
ELIGIBLE = "eligible"
REFUSED = "refused"

AUDIT_COLUMNS = (
    "node_id",
    "model_role",
    "mechanical",
    "policy",
    "policy_scope",
    "direct_target",
    "basis",
)

_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-]*")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

Key = tuple[str, str, str, str]


@dataclass(frozen=True)
class Adjudication:
    adjudication_id: str
    intervention_id: str
    model_version: str
    target_node: str
    mode: str
    decision: str
    evidence_ids: tuple[str, ...]
    effect_evidence: str
    system_match: str
    biological_system: str
    library_row_sha256: str
    basis_record: str
    rationale: str
    adjudicator: str
    dated: str
    system_grade: str
    target_declaration_sha256: str
    #: sha256 of the ledger row as written, so two approvals that differ in any
    #: field never produce the same run record.
    row_sha256: str

    @property
    def key(self) -> Key:
        return (self.intervention_id, self.model_version, self.target_node, self.mode)


@dataclass(frozen=True)
class TargetPolicy:
    roles: dict[str, tuple[str, str]]
    node_refusals: dict[str, str]


def _split(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(";") if part.strip())


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def library_row_digest(effect: InterventionEffect) -> str:
    """sha256 of the row's 13 library columns, in ``LIBRARY_COLUMNS`` order.

    List columns enter as their parsed ``;``-joined form, so the digest is that
    of what the loader read. Any change to identity, target, mode, evidence,
    abstraction, sources or claim boundary changes it.
    """
    values = []
    for column in LIBRARY_COLUMNS:
        value = getattr(effect, column)
        values.append(";".join(value) if isinstance(value, tuple) else value)
    return _sha256("\t".join(values))


def _read_tsv(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != columns:
            raise InterventionError(f"{path.name} columns are {reader.fieldnames}")
        rows = list(reader)
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise InterventionError(f"{path.name} has a ragged row: {row}")
    return rows


def _check_sources(root: Path, sources: tuple[str, ...], where: str) -> None:
    if not sources:
        raise InterventionError(f"{where}: no basis is recorded")
    for source in sources:
        if not (root / source.split("#", 1)[0]).is_file():
            raise InterventionError(f"{where}: basis {source} does not exist")


def load_adjudications(root: Path) -> dict[Key, Adjudication] | None:
    """The ledger keyed by effect, or ``None`` when the file does not exist.

    Validates what needs no model: columns, vocabularies, one row per key, a
    single-node target, and approvable values on an approved row.
    """
    path = root / ADJUDICATIONS_PATH
    if not path.is_file():
        return None
    ledger: dict[Key, Adjudication] = {}
    ids: set[str] = set()
    for row in _read_tsv(path, ADJUDICATION_COLUMNS):
        where = f"{ADJUDICATIONS_PATH} {row['adjudication_id'] or '<no id>'}"
        entry = Adjudication(
            **{c: row[c] for c in ADJUDICATION_COLUMNS if c != "evidence_ids"},
            evidence_ids=_split(row["evidence_ids"]),
            row_sha256=_sha256("\t".join(row[c] for c in ADJUDICATION_COLUMNS)),
        )
        if not entry.adjudication_id or entry.adjudication_id in ids:
            raise InterventionError(f"{where}: a missing or repeated adjudication_id")
        ids.add(entry.adjudication_id)
        if not _TOKEN_RE.fullmatch(entry.intervention_id) or not _TOKEN_RE.fullmatch(
            entry.model_version
        ):
            raise InterventionError(
                f"{where}: intervention_id and model_version must each name one item"
            )
        if not _IDENTIFIER_RE.fullmatch(entry.target_node):
            # A list, a pattern or a class would be target inference.
            raise InterventionError(
                f"{where}: target_node {entry.target_node!r} is not one node id"
            )
        if entry.mode not in DIRECT_MODES:
            raise InterventionError(
                f"{where}: mode {entry.mode!r} is not a direct mode "
                f"({', '.join(DIRECT_MODES)})"
            )
        if entry.decision not in DECISIONS:
            raise InterventionError(f"{where}: unknown decision {entry.decision!r}")
        if entry.effect_evidence not in EFFECT_EVIDENCE:
            raise InterventionError(
                f"{where}: unknown effect_evidence {entry.effect_evidence!r}"
            )
        if entry.system_match not in SYSTEM_MATCH:
            raise InterventionError(
                f"{where}: unknown system_match {entry.system_match!r}"
            )
        if not entry.evidence_ids:
            raise InterventionError(f"{where}: no evidence ids")
        if not _SHA256_RE.fullmatch(entry.library_row_sha256):
            raise InterventionError(f"{where}: library_row_sha256 is not a sha256")
        if entry.system_grade not in SYSTEM_GRADES:
            raise InterventionError(
                f"{where}: unknown system_grade {entry.system_grade!r}"
            )
        if entry.target_declaration_sha256 and not _SHA256_RE.fullmatch(
            entry.target_declaration_sha256
        ):
            raise InterventionError(
                f"{where}: target_declaration_sha256 is not a sha256"
            )
        if entry.decision == APPROVED and not entry.target_declaration_sha256:
            # C8: an approval names the declaration it rests on.
            raise InterventionError(
                f"{where}: an approval needs target_declaration_sha256 (C8)"
            )
        if not _DATE_RE.fullmatch(entry.dated):
            raise InterventionError(f"{where}: dated is not an ISO date")
        if not (entry.biological_system and entry.rationale and entry.adjudicator):
            raise InterventionError(
                f"{where}: biological_system, rationale and adjudicator are required"
            )
        if entry.decision == APPROVED and not _approvable(entry):
            raise InterventionError(
                f"{where}: an approval needs effect_evidence "
                f"{'/'.join(APPROVABLE_EFFECT_EVIDENCE)} and system_match "
                f"{'/'.join(APPROVABLE_SYSTEM_MATCH)} (or both {SYNTHETIC}); it has "
                f"{entry.effect_evidence} and {entry.system_match}"
            )
        if entry.decision == APPROVED and not _grade_approvable(entry):
            raise InterventionError(
                f"{where}: an approval needs system_grade "
                f"{'/'.join(APPROVABLE_SYSTEM_GRADES)} (or {SYNTHETIC} with synthetic "
                f"effect evidence); it has {entry.system_grade}. A line-based E2 "
                "measurement is refused however many lines agree (§6.3)"
            )
        if entry.key in ledger:
            raise InterventionError(
                f"{where}: {ledger[entry.key].adjudication_id} already adjudicates "
                f"{entry.key}"
            )
        ledger[entry.key] = entry
    return ledger


def _approvable(entry: Adjudication) -> bool:
    if SYNTHETIC in (entry.effect_evidence, entry.system_match):
        return entry.effect_evidence == entry.system_match == SYNTHETIC
    return (
        entry.effect_evidence in APPROVABLE_EFFECT_EVIDENCE
        and entry.system_match in APPROVABLE_SYSTEM_MATCH
    )


def _grade_approvable(entry: Adjudication) -> bool:
    """§6.3, with the O8b synthetic/real split extended to the new column."""
    if SYNTHETIC in (entry.system_grade, entry.effect_evidence):
        return entry.system_grade == entry.effect_evidence == SYNTHETIC
    return entry.system_grade in APPROVABLE_SYSTEM_GRADES


def validate_ledger(
    ledger: dict[Key, Adjudication],
    library: dict[str, list[InterventionEffect]],
    root: Path,
) -> None:
    """What needs the models and the library: every target is a node of its
    version, every basis exists, and no row names a non-direct intervention."""
    nodes: dict[str, set[str]] = {}
    for entry in ledger.values():
        where = f"{ADJUDICATIONS_PATH} {entry.adjudication_id}"
        if entry.model_version not in nodes:
            try:
                spec = resolve_model(entry.model_version, root)
            except ValueError as error:
                raise InterventionError(f"{where}: {error}") from error
            nodes[entry.model_version] = set(
                _node_blocks(spec.network_bnd.read_text(encoding="utf-8"))
            )
        if entry.target_node not in nodes[entry.model_version]:
            raise InterventionError(
                f"{where}: {entry.target_node} is not a node of {entry.model_version}"
            )
        _check_sources(root, _split(entry.basis_record), where)
        bases = {
            e.mapping_basis
            for e in library.get(entry.intervention_id, ())
            if e.model_version == entry.model_version
        }
        if bases - {DIRECT_BASIS}:
            # An adjudication cannot turn a legacy or migrated row into a direct
            # one; the three bases stay distinct.
            raise InterventionError(
                f"{where}: {entry.intervention_id} is {', '.join(sorted(bases))} on "
                f"{entry.model_version}; only {DIRECT_BASIS} rows are adjudicated here"
            )


def load_target_policy(root: Path) -> TargetPolicy:
    path = root / TARGET_POLICY_PATH
    if not path.is_file():
        raise InterventionError(
            f"{DIRECT_BASIS} rows need the target policy at {TARGET_POLICY_PATH}"
        )
    roles: dict[str, tuple[str, str]] = {}
    node_refusals: dict[str, str] = {}
    for row in _read_tsv(path, POLICY_COLUMNS):
        where = f"{TARGET_POLICY_PATH} {row['scope']}:{row['key']}"
        if row["scope"] not in POLICY_SCOPES:
            raise InterventionError(f"{where}: unknown scope")
        if row["policy"] not in (ELIGIBLE, REFUSED):
            raise InterventionError(f"{where}: unknown policy {row['policy']!r}")
        if not (row["key"] and row["rationale"] and _split(row["basis"])):
            raise InterventionError(f"{where}: key, basis and rationale are required")
        if row["scope"] == "node":
            if row["policy"] != REFUSED:
                # A node row narrows a role; it never admits a refused one.
                raise InterventionError(f"{where}: a node row may only refuse")
            if row["key"] in node_refusals:
                raise InterventionError(f"{where}: listed twice")
            node_refusals[row["key"]] = row["basis"]
        else:
            if row["key"] in roles:
                raise InterventionError(f"{where}: listed twice")
            roles[row["key"]] = (row["policy"], row["basis"])
    return TargetPolicy(roles=roles, node_refusals=node_refusals)


def check_policy_basis(root: Path) -> None:
    """Every policy row's basis names a file that exists.

    Static, not checked on load: the basis is the record a reviewer reads, and a
    sandbox root need not carry the review records to execute.
    """
    for row in _read_tsv(root / TARGET_POLICY_PATH, POLICY_COLUMNS):
        where = f"{TARGET_POLICY_PATH} {row['scope']}:{row['key']}"
        _check_sources(root, _split(row["basis"]), where)


def policy_decision(policy: TargetPolicy, node: str, role: str) -> tuple[str, str, str]:
    """``(policy, scope, basis)`` for a node. An unlisted role is refused."""
    if role not in policy.roles:
        return REFUSED, "unlisted", ""
    role_policy, role_basis = policy.roles[role]
    if role_policy == ELIGIBLE and node in policy.node_refusals:
        return REFUSED, "node", policy.node_refusals[node]
    return role_policy, "role", role_basis


def policy_refusal(policy: TargetPolicy, node: str, role: str) -> str | None:
    """Why the policy refuses a direct effect on ``node``, or ``None``."""
    decision, scope, basis = policy_decision(policy, node, role)
    if decision == ELIGIBLE:
        return None
    if scope == "unlisted":
        return (
            f"role {role!r} is not in {TARGET_POLICY_PATH}, and an unlisted role "
            "is refused"
        )
    if scope == "node":
        return f"{node} is refused by node policy ({basis})"
    return f"a direct effect may not target a {role} node"


def license_effect(
    effect: InterventionEffect,
    ledger: dict[Key, Adjudication] | None,
    register_status: dict[str, str],
) -> InterventionEffect:
    """``effect`` with its approval attached, or refuse it.

    The row must have exactly one ledger row under its own key, approved, citing
    the same evidence set, with the row's current digest. Synthetic approvals
    must cite only synthetic evidence, and real ones none.
    """
    where = f"{effect.intervention_id} -> {effect.target_node} ({effect.model_version})"
    if ledger is None:
        raise InterventionError(
            f"{where}: {DIRECT_BASIS} rows need the adjudication ledger at "
            f"{ADJUDICATIONS_PATH}"
        )
    key: Key = (
        effect.intervention_id,
        effect.model_version,
        effect.target_node,
        effect.mode,
    )
    entry = ledger.get(key)
    if entry is None:
        others = sorted(
            f"{k[2]}/{k[3]}" for k in ledger if k[:2] == key[:2] and k != key
        )
        hint = f" (this intervention and version are adjudicated for {others})"
        raise InterventionError(
            f"{where}: no adjudication in {ADJUDICATIONS_PATH} for mode "
            f"{effect.mode}{hint if others else ''}"
        )
    if entry.decision != APPROVED:
        raise InterventionError(
            f"{where}: {entry.adjudication_id} is {entry.decision}, not {APPROVED}"
        )
    if set(entry.evidence_ids) != set(effect.evidence_ids):
        raise InterventionError(
            f"{where}: the row cites evidence {sorted(effect.evidence_ids)} but "
            f"{entry.adjudication_id} approved {sorted(entry.evidence_ids)}"
        )
    digest = library_row_digest(effect)
    if digest != entry.library_row_sha256:
        raise InterventionError(
            f"{where}: the library row changed since {entry.adjudication_id} "
            f"approved it (row sha256 {digest}, approved "
            f"{entry.library_row_sha256})"
        )
    synthetic = {
        evidence_id
        for evidence_id in effect.evidence_ids
        if register_status.get(evidence_id) == SYNTHETIC
    }
    if entry.effect_evidence == SYNTHETIC:
        if synthetic != set(effect.evidence_ids):
            raise InterventionError(
                f"{where}: {entry.adjudication_id} is a {SYNTHETIC} approval citing "
                f"real evidence {sorted(set(effect.evidence_ids) - synthetic)}"
            )
    elif synthetic:
        raise InterventionError(
            f"{where}: {entry.adjudication_id} approves on synthetic evidence "
            f"{sorted(synthetic)}"
        )
    return replace(
        effect,
        adjudication_id=entry.adjudication_id,
        adjudication_sha256=entry.row_sha256,
    )


def target_audit(
    model_version: str = AUDIT_MODEL_VERSION, root: Path | None = None
) -> list[dict[str, str]]:
    """Every node of ``model_version`` under the mechanical checks and the policy.

    ``direct_target`` is ``yes`` only when both admit the node. That is
    necessary for a direct effect and never sufficient: each effect still needs
    its own approval.
    """
    root = root or repo_root()
    spec = resolve_model(model_version, root)
    blocks = _node_blocks(spec.network_bnd.read_text(encoding="utf-8"))
    policy = load_target_policy(root)
    # Rows, not the licensed library: the Stage 4b licence regenerates the
    # expressivity artefact, which reads this audit, so licensing here would
    # recurse. Only the legacy rows' inputs are read.
    legacy_inputs = {
        e.legacy_input_node
        for e in read_library_rows(root)
        if e.mapping_basis == LEGACY_BASIS and e.model_version == model_version
    }
    with spec.node_dictionary.open(encoding="utf-8", newline="") as handle:
        dictionary = list(csv.DictReader(handle, delimiter="\t"))
    rows = []
    for entry in dictionary:
        node, role = entry["node_id"], entry["model_role"]
        try:
            logic = _target_logic(blocks, node)
            read = sorted(_evaluable(logic)[1] & legacy_inputs)
            mechanical = f"refused: reads legacy inputs {read}" if read else "eligible"
        except InterventionError as error:
            mechanical = f"refused: {error}"
        decision, scope, basis = policy_decision(policy, node, role)
        rows.append(
            {
                "node_id": node,
                "model_role": role,
                "mechanical": mechanical,
                "policy": decision,
                "policy_scope": scope,
                "direct_target": "yes"
                if mechanical == "eligible" and decision == ELIGIBLE
                else "no",
                "basis": basis,
            }
        )
    return rows


def render_audit(rows: list[dict[str, str]]) -> str:
    lines = ["\t".join(AUDIT_COLUMNS)]
    lines.extend("\t".join(row[c] for c in AUDIT_COLUMNS) for row in rows)
    return "\n".join(lines) + "\n"


def direct_row_digests(root: Path | None = None) -> list[str]:
    """``key<TAB>digest`` for every direct row, to draft an approval from."""
    return [
        "\t".join(
            (
                e.intervention_id,
                e.model_version,
                e.target_node,
                e.mode,
                library_row_digest(e),
            )
        )
        for e in read_library_rows(root or repo_root())
        if e.mapping_basis == DIRECT_BASIS
    ]


# --- Stage 4b: admitting real direct interventions ----------------------------
#
# docs/stage4b_direct_admission.md is the pre-registration. O8b approves each
# listed *effect*; nothing above knows what an intervention omits. This section
# adds the intervention-level declaration and the checks C1-C8 (§3.4) that hold
# it to a reading of the model version (the entity map), plus the §6.1 licence
# conditions that need it: the declaration digest, and a current expressivity
# artefact. Every failure refuses the whole library and names the rule.
#
# Kept apart, as §2a requires: the licence (L1) is decided here; expressivity
# (L2) is read from the committed artefact and only *reported*; a null or an
# aliased target is never refused for being one (§5.6).

ENTITY_MAP_PATH = Path("config/node_entity_map.tsv")
DECLARATIONS_PATH = Path("config/direct_effect_target_declarations.tsv")
#: §3.5.1: the staged candidates that were not admitted, one half of the
#: mechanical floor for ``scope_relevant``.
FLOOR_CANDIDATES_PATH = Path(
    "context/literature/staging/deep_research_adhesion_model_2026-09-11/"
    "candidate_nodes.tsv"
)
#: The committed expressivity artefacts per model version (§5). A version with
#: none may not hold an approved executable row (§6.6). The paths are those of
#: ``reporting.veto_expressivity``; a test holds the two equal.
EXPRESSIVITY_ARTEFACTS = {
    AUDIT_MODEL_VERSION: (
        Path("docs/stage4b/v060_veto_expressivity.tsv"),
        Path("docs/stage4b/v060_veto_invariance.tsv"),
    )
}
ADMISSION_PREREGISTRATION = "docs/stage4b_direct_admission.md"

ENTITY_MAP_COLUMNS = (
    "model_version",
    "node_id",
    "entity",
    "level",
    "compartment",
    "aggregation",
    "basis",
)
LEVELS = ("expression", "activity", "extracellular")
COMPARTMENTS = ("epithelium", "stroma", "extracellular")
SINGLE = "single"
#: A full veto must hit every member.
ANY_OF = "any_of"
#: Hitting one member suffices.
ALL_OF = "all_of"
#: The dictionary does not decide what the node stands for. Never approvable;
#: resolved only by a recorded decision, never by an approval (§3.2, §11.2).
AMBIGUOUS = "ambiguous"
#: The node stands for no entity of its own. Not "policy-refused": a refused
#: node that stands for entities keeps its real aggregation, which is what lets
#: C3 see a PAEP-, MUC1- or DAG1-directed agent.
DERIVED = "derived"
#: A known entity the version does not represent (``node_id`` empty): the
#: entity reading of one §3.5.1 floor item, named by its basis anchor.
MODEL_GAP = "model_gap"
AGGREGATIONS = (SINGLE, ANY_OF, ALL_OF, AMBIGUOUS, DERIVED, MODEL_GAP)
#: The roles that have no map row: their values come from the protocol.
PROTOCOL_INPUT_ROLES = frozenset(
    {"input", "assay_gate", "external_input", "pathology_input", "boundary_input"}
)
#: §3.2: the composite roles, and the two rule-derived abstractions, are
#: ``derived``; every other mapped node carries entities.
COMPOSITE_ROLES = frozenset(
    {"state", "latent_state", "interface_route", "phenotype", "structural_uncertainty"}
)
RULE_DERIVED_NODES = frozenset({"E_ESTROGENIC_PROLIFERATION", "S_FGF_MITOGENIC"})

DECLARATION_COLUMNS = (
    "declaration_id",
    "intervention_id",
    "model_version",
    "agent_class",
    "agent_specification",
    "reached_compartments",
    "known_target_entities",
    "declared_targets",
    "unrepresented_known_targets",
    "target_profile_sources",
    "profile_searched_on",
    "construction_overlap",
    "library_rows_sha256",
    "adjudicator",
    "dated",
)
AGENT_CLASSES = (
    "small_molecule",
    "biologic",
    "antibody",
    "genetic_knockdown",
    "genetic_knockout",
)
SCOPE_RELEVANT = "scope_relevant"
OUT_OF_SCOPE = "out_of_scope"
SCOPE_CLASSES = (SCOPE_RELEVANT, OUT_OF_SCOPE)
#: ``reached_compartments`` item citing why a narrowed set is narrowed (C4).
SOURCE_PREFIX = "source:"
#: ``unrepresented_known_targets`` item naming the §3.5.1 floor item it falls
#: under, or ``none``.
FLOOR_PREFIX = "floor:"
NO_FLOOR = "none"
NO_OVERLAP = "none"

_ENTITY_RE = re.compile(r"[A-Z][A-Z0-9-]*|process:[a-z0-9_]+")
_DECLARATION_ID_RE = re.compile(r"DTD-\d{3,}")
_REFERENCE_RE = re.compile(r"REF-\d+")
_LOGIC_RE = re.compile(r"logic\s*=\s*([^;]+);")

Entity = tuple[str, str]


@dataclass(frozen=True)
class EntityRow:
    model_version: str
    node_id: str
    entity: str
    level: str
    compartment: str
    aggregation: str
    basis: str

    @property
    def gap_id(self) -> str:
        """For a ``model_gap`` row, the catalogue target it stands for."""
        return self.basis.rsplit("#", 1)[-1]


@dataclass(frozen=True)
class Unrepresented:
    entity: str
    level: str
    scope: str
    floor: str
    basis: tuple[str, ...]


@dataclass(frozen=True)
class Declaration:
    declaration_id: str
    intervention_id: str
    model_version: str
    agent_class: str
    agent_specification: str
    reached_compartments: str
    known_target_entities: str
    declared_targets: str
    unrepresented_known_targets: str
    target_profile_sources: str
    profile_searched_on: str
    construction_overlap: str
    library_rows_sha256: str
    adjudicator: str
    dated: str
    reached: frozenset[str]
    reached_sources: tuple[str, ...]
    known: frozenset[Entity]
    declared: frozenset[str]
    unrepresented: tuple[Unrepresented, ...]
    sources: tuple[str, ...]
    #: sha256 of the declaration row as written: what ``target_declaration_sha256``
    #: binds (C8, §6.1 item 4).
    row_sha256: str


@dataclass(frozen=True)
class Admission:
    """What the licence established about one direct intervention on one version."""

    declaration: Declaration
    #: An unrepresented known target is ``scope_relevant`` (§3.5, owner decision 4).
    compound_claim_blocked: bool
    construction_overlap: str


def _entity(token: str, where: str) -> Entity:
    entity, sep, level = token.partition("@")
    if not sep or not _ENTITY_RE.fullmatch(entity) or level not in LEVELS:
        raise InterventionError(
            f"{where}: {token!r} is not ENTITY@level (an HGNC symbol or "
            f"process:<name>, at {'/'.join(LEVELS)})"
        )
    return entity, level


def load_entity_map(root: Path) -> dict[str, tuple[EntityRow, ...]] | None:
    """``config/node_entity_map.tsv`` by model version, or ``None`` if absent.

    Validates the vocabulary and the per-node shape. Coverage of the version's
    nodes is ``check_entity_map_coverage``, which needs the model.
    """
    path = root / ENTITY_MAP_PATH
    if not path.is_file():
        return None
    by_version: dict[str, list[EntityRow]] = {}
    seen: set[tuple[str, str, str, str]] = set()
    for raw in _read_tsv(path, ENTITY_MAP_COLUMNS):
        row = EntityRow(**raw)
        where = f"{ENTITY_MAP_PATH} {row.model_version}:{row.node_id or '<gap>'}"
        if row.aggregation not in AGGREGATIONS:
            raise InterventionError(f"{where}: unknown aggregation {row.aggregation!r}")
        if not _TOKEN_RE.fullmatch(row.model_version) or not _split(row.basis):
            raise InterventionError(f"{where}: model_version and basis are required")
        if row.aggregation == DERIVED:
            # It stands for nothing, so it names nothing.
            if not row.node_id or row.entity or row.level or row.compartment:
                raise InterventionError(
                    f"{where}: a {DERIVED} row names a node and no entity, level "
                    "or compartment"
                )
        else:
            _entity(f"{row.entity}@{row.level}", where)
            if row.aggregation == MODEL_GAP:
                if row.node_id:
                    raise InterventionError(f"{where}: a {MODEL_GAP} row names no node")
                if row.compartment and row.compartment not in COMPARTMENTS:
                    raise InterventionError(f"{where}: unknown compartment")
                if "#" not in row.basis or not row.gap_id:
                    raise InterventionError(
                        f"{where}: a {MODEL_GAP} basis names its catalogue row as "
                        "<path>#<target_id>"
                    )
            elif not _IDENTIFIER_RE.fullmatch(row.node_id) or (
                row.compartment not in COMPARTMENTS
            ):
                raise InterventionError(
                    f"{where}: needs one node id and a compartment in "
                    f"{'/'.join(COMPARTMENTS)}"
                )
        key = (row.model_version, row.node_id, row.entity, row.level)
        if key in seen and row.aggregation != MODEL_GAP:
            raise InterventionError(f"{where}: {row.entity}@{row.level} listed twice")
        seen.add(key)
        by_version.setdefault(row.model_version, []).append(row)
    for version, rows in by_version.items():
        nodes: dict[str, list[EntityRow]] = {}
        for row in rows:
            if row.node_id:
                nodes.setdefault(row.node_id, []).append(row)
        for node, node_rows in nodes.items():
            where = f"{ENTITY_MAP_PATH} {version}:{node}"
            aggregations = {r.aggregation for r in node_rows}
            if len(aggregations) != 1:
                raise InterventionError(f"{where}: rows disagree on the aggregation")
            (aggregation,) = aggregations
            if aggregation in (SINGLE, DERIVED) and len(node_rows) != 1:
                raise InterventionError(f"{where}: {aggregation} takes one row")
            if aggregation in (ANY_OF, ALL_OF) and len(node_rows) < 2:
                raise InterventionError(f"{where}: {aggregation} needs two members")
            if len({r.compartment for r in node_rows}) != 1:
                raise InterventionError(f"{where}: rows disagree on the compartment")
    return {version: tuple(rows) for version, rows in by_version.items()}


def check_entity_map_coverage(
    rows: tuple[EntityRow, ...], model_version: str, root: Path
) -> None:
    """The map covers exactly the version's non-input nodes (§3.2), so a model
    version cannot gain a node the map does not mention."""
    spec = resolve_model(model_version, root)
    with spec.node_dictionary.open(encoding="utf-8", newline="") as handle:
        dictionary = list(csv.DictReader(handle, delimiter="\t"))
    expected = {
        r["node_id"] for r in dictionary if r["model_role"] not in PROTOCOL_INPUT_ROLES
    }
    mapped = {r.node_id for r in rows if r.node_id}
    if mapped != expected:
        raise InterventionError(
            f"{ENTITY_MAP_PATH} does not cover {model_version} exactly: missing "
            f"{sorted(expected - mapped)}, not nodes {sorted(mapped - expected)}"
        )


def check_floor_coverage(
    rows: tuple[EntityRow, ...], model_version: str, root: Path
) -> None:
    """Every §3.5.1 floor item has its entity reading as model-gap rows, and no
    gap row names anything else, so an entity on the floor is recognised whether
    or not a declaration links it (amendment A2, docs/stage4b_implementation.md).

    Checked for every version that holds a direct row, and by
    ``validate-direct-effects``; a root with no direct row need not carry the
    staged floor table.
    """
    floor = set(scope_floor(model_version, root))
    gaps = {r.gap_id for r in rows if r.aggregation == MODEL_GAP}
    if gaps != floor:
        raise InterventionError(
            f"{ENTITY_MAP_PATH} model gaps for {model_version} are not the §3.5.1 "
            f"floor: unread {sorted(floor - gaps)}, not floor items "
            f"{sorted(gaps - floor)}"
        )


def _parse_unrepresented(value: str, where: str) -> tuple[Unrepresented, ...]:
    entries = []
    for item in _split(value):
        parts = item.split("|")
        if len(parts) != 4:
            raise InterventionError(
                f"{where}: unrepresented entry {item!r} is not "
                "ENTITY@level|class|floor:<id> or none|basis[,basis]"
            )
        token, scope, floor, basis = (p.strip() for p in parts)
        entity, level = _entity(token, where)
        if scope not in SCOPE_CLASSES:
            raise InterventionError(
                f"{where}: {token} has class {scope!r}, not one of {SCOPE_CLASSES}"
            )
        if floor != NO_FLOOR and not (
            floor.startswith(FLOOR_PREFIX) and floor[len(FLOOR_PREFIX) :]
        ):
            raise InterventionError(
                f"{where}: {token} names floor {floor!r}, not floor:<id> or none"
            )
        bases = tuple(b.strip() for b in basis.split(",") if b.strip())
        if not bases:
            raise InterventionError(f"{where}: {token} is classified with no basis")
        entries.append(Unrepresented(entity, level, scope, floor, bases))
    if len({(e.entity, e.level) for e in entries}) != len(entries):
        raise InterventionError(f"{where}: an unrepresented entity is listed twice")
    return tuple(entries)


def load_declarations(root: Path) -> dict[tuple[str, str], Declaration] | None:
    """The declarations by ``(intervention_id, model_version)``, or ``None``."""
    path = root / DECLARATIONS_PATH
    if not path.is_file():
        return None
    declarations: dict[tuple[str, str], Declaration] = {}
    ids: set[str] = set()
    for row in _read_tsv(path, DECLARATION_COLUMNS):
        where = f"{DECLARATIONS_PATH} {row['declaration_id'] or '<no id>'}"
        if not _DECLARATION_ID_RE.fullmatch(row["declaration_id"]) or (
            row["declaration_id"] in ids
        ):
            raise InterventionError(f"{where}: a missing, malformed or repeated id")
        ids.add(row["declaration_id"])
        if not _TOKEN_RE.fullmatch(row["intervention_id"]) or not _TOKEN_RE.fullmatch(
            row["model_version"]
        ):
            raise InterventionError(
                f"{where}: intervention_id and model_version must each name one item"
            )
        if row["agent_class"] not in AGENT_CLASSES:
            raise InterventionError(
                f"{where}: unknown agent_class {row['agent_class']!r}"
            )
        for column in ("agent_specification", "adjudicator", "construction_overlap"):
            if not row[column]:
                raise InterventionError(f"{where}: {column} is required")
        for column in ("profile_searched_on", "dated"):
            if not _DATE_RE.fullmatch(row[column]):
                raise InterventionError(f"{where}: {column} is not an ISO date")
        if not _SHA256_RE.fullmatch(row["library_rows_sha256"]):
            raise InterventionError(f"{where}: library_rows_sha256 is not a sha256")
        reached, reached_sources = set(), []
        for item in _split(row["reached_compartments"]):
            if item.startswith(SOURCE_PREFIX) and item[len(SOURCE_PREFIX) :]:
                reached_sources.append(item[len(SOURCE_PREFIX) :])
            elif item in COMPARTMENTS:
                reached.add(item)
            else:
                raise InterventionError(
                    f"{where}: reached_compartments item {item!r} is neither a "
                    f"compartment nor {SOURCE_PREFIX}<source>"
                )
        if not reached:
            raise InterventionError(f"{where}: no reached compartment")
        known = [
            _entity(token, where) for token in _split(row["known_target_entities"])
        ]
        if not known or len(set(known)) != len(known):
            raise InterventionError(
                f"{where}: known_target_entities is empty or lists an entity twice"
            )
        declared = _split(row["declared_targets"])
        if (
            not declared
            or len(set(declared)) != len(declared)
            or not all(_IDENTIFIER_RE.fullmatch(node) for node in declared)
        ):
            raise InterventionError(
                f"{where}: declared_targets must be distinct node ids"
            )
        sources = _split(row["target_profile_sources"])
        if not sources:
            raise InterventionError(f"{where}: no target_profile_sources")
        declaration = Declaration(
            **row,
            reached=frozenset(reached),
            reached_sources=tuple(reached_sources),
            known=frozenset(known),
            declared=frozenset(declared),
            unrepresented=_parse_unrepresented(
                row["unrepresented_known_targets"], where
            ),
            sources=sources,
            row_sha256=_sha256("\t".join(row[c] for c in DECLARATION_COLUMNS)),
        )
        key = (declaration.intervention_id, declaration.model_version)
        if key in declarations:
            # C1: exactly one declaration per intervention and version.
            raise InterventionError(
                f"{where}: {declarations[key].declaration_id} already declares {key} (C1)"
            )
        declarations[key] = declaration
    return declarations


def library_rows_digest(effects: list[InterventionEffect] | tuple) -> str:
    """sha256 of an intervention's rows for one version, in library order, each
    digested as O8b digests one row (``library_row_digest``), newline-joined."""
    return _sha256("\n".join(library_row_digest(e) for e in effects))


def scope_floor(model_version: str, root: Path) -> dict[str, str]:
    """§3.5.1: the floor items, ``{id: where it is recorded}``.

    The version's catalogue targets whose ``execution_status`` is not
    ``executable``, and the staged candidate nodes. A declaration may name one
    in an unrepresented entry (``floor:<id>``); naming one ``out_of_scope`` is
    refused.
    """
    spec = resolve_model(model_version, root)
    catalog = spec.model_root / "drug_target_catalog.tsv"
    floor: dict[str, str] = {}
    if not (root / FLOOR_CANDIDATES_PATH).is_file():
        raise InterventionError(
            f"the §3.5.1 floor needs {FLOOR_CANDIDATES_PATH}, which is missing"
        )
    with catalog.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["execution_status"] != "executable":
                floor[row["target_id"]] = (
                    f"{catalog.relative_to(root)}#{row['target_id']}"
                )
    with (root / FLOOR_CANDIDATES_PATH).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            floor.setdefault(
                row["node_id"], f"{FLOOR_CANDIDATES_PATH}#{row['node_id']}"
            )
    return floor


def _register_references(root: Path) -> dict[str, tuple[str, ...]]:
    with (root / EVIDENCE_REGISTER_PATH).open(encoding="utf-8", newline="") as handle:
        return {
            row["evidence_id"]: tuple(_REFERENCE_RE.findall(row["location"]))
            for row in csv.DictReader(handle, delimiter="\t")
        }


def construction_overlap(
    model_version: str,
    targets: frozenset[str] | set[str],
    evidence_ids: set[str],
    root: Path,
) -> str:
    """§6.5: the reference ids cited by the approval that also support an edge on
    a path from a target to the observed set O.

    ``REF:edge,edge;REF:edge`` sorted, or ``none``. An edge is on such a path when
    its source is reachable from a target and its target reaches O, along the
    executed rules (self-loops excluded). Its support is the ``reference_ids`` of
    its executable ``complete_edges.tsv`` rows and the references of their
    evidence ids. A source in this set cannot validate the prediction: it is
    circular by construction. Recorded, never refused.
    """
    from dt_adoc.reporting.veto_expressivity import ExpressivityError, _observed_sets

    spec = resolve_model(model_version, root)
    blocks = _node_blocks(spec.network_bnd.read_text(encoding="utf-8"))
    parents: dict[str, set[str]] = {}
    for node, block in blocks.items():
        match = _LOGIC_RE.search(block)
        read = _evaluable(match.group(1))[1] if match else frozenset()
        parents[node] = {p for p in read if p != node and p in blocks}
    children: dict[str, set[str]] = {node: set() for node in blocks}
    for node, read in parents.items():
        for parent in read:
            children[parent].add(node)
    try:
        observed, _ = _observed_sets(root, set(blocks))
    except ExpressivityError as error:
        raise InterventionError(
            f"the §5.2 generator refuses {model_version} ({error}); O is undefined"
        ) from error

    def closure(start: set[str], step: dict[str, set[str]]) -> set[str]:
        seen, todo = set(start), list(start)
        while todo:
            for nxt in step[todo.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        return seen

    downstream = closure(set(targets), children)
    upstream = closure(set(observed), parents)
    on_path = {
        (source, node)
        for node in upstream
        for source in parents[node]
        if source in downstream
    }
    references = _register_references(root)
    cited = {ref for eid in evidence_ids for ref in references.get(eid, ())}
    support: dict[str, set[str]] = {}
    with (spec.model_root / "complete_edges.tsv").open(
        encoding="utf-8", newline=""
    ) as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["catalog_origin"] != "executable_edge":
                continue
            if (row["source"], row["target"]) not in on_path:
                continue
            refs = set(_REFERENCE_RE.findall(row["reference_ids"]))
            for eid in _split(row["evidence_ids"]):
                refs.update(references.get(eid, ()))
            for ref in refs & cited:
                support.setdefault(ref, set()).add(row["edge_id"])
    if not support:
        return NO_OVERLAP
    return ";".join(
        f"{ref}:{','.join(sorted(edges))}" for ref, edges in sorted(support.items())
    )


_EXPRESSIVITY_CACHE: dict[str, dict[str, dict[str, str]]] = {}


def expressivity_classes(model_version: str, root: Path) -> dict[str, dict[str, str]]:
    """The committed per-condition artefact's rows by arm, after checking that
    both committed artefacts equal what the generator writes now (§6.1 item 5).

    Refuses a version with no artefact, a missing or stale one, and a version the
    §5.2 generator refuses: in each case the run record could not carry the
    class. Cached on the paths and bytes of everything the generator reads.
    """
    from dt_adoc.reporting import veto_expressivity as generator

    paths = EXPRESSIVITY_ARTEFACTS.get(model_version)
    if paths is None:
        raise InterventionError(
            f"{model_version} has no expressivity artefact, so it may not hold an "
            f"approved executable direct row ({ADMISSION_PREREGISTRATION} §6.6)"
        )
    for path in paths:
        if not (root / path).is_file():
            raise InterventionError(
                f"the expressivity artefact {path} is missing; run "
                "`pixi run veto-expressivity write` (§6.1 item 5)"
            )
    spec = resolve_model(model_version, root)
    inputs = [
        spec.model_root / "provenance.toml",
        spec.network_bnd,
        spec.node_dictionary,
        spec.baseline_cfg,
        *sorted(spec.condition_dir.glob("*.cfg")),
        root / generator.OBSERVATION_MAP_PATH,
        root / LIBRARY_PATH,
        root / TARGET_POLICY_PATH,
        *(root / path for path in paths),
    ]
    # Keyed on content, not on the root, so identical sandboxes share a check.
    digest = hashlib.sha256(model_version.encode() + b"\0")
    for path in inputs:
        digest.update(
            str(path.relative_to(root)).encode() + b"\0" + path.read_bytes() + b"\0"
        )
    key = digest.hexdigest()
    if key not in _EXPRESSIVITY_CACHE:
        try:
            expected = (
                generator.render(generator.expressivity(model_version, root)),
                generator.render_invariance(generator.invariance(model_version, root)),
            )
        except generator.ExpressivityError as error:
            raise InterventionError(
                f"the §5.2 generator refuses {model_version} ({error}); such a "
                "version cannot hold an approval until a substitute method is "
                "pre-registered"
            ) from error
        for path, text in zip(paths, expected):
            if (root / path).read_text(encoding="utf-8") != text:
                raise InterventionError(
                    f"the expressivity artefact {path} is stale for {model_version}; "
                    "run `pixi run veto-expressivity write` (§6.1 item 5)"
                )
        with (root / paths[0]).open(encoding="utf-8", newline="") as handle:
            _EXPRESSIVITY_CACHE[key] = {
                row["arm"]: row for row in csv.DictReader(handle, delimiter="\t")
            }
    return _EXPRESSIVITY_CACHE[key]


def _resolves(root: Path, reference: str, register: set[str]) -> bool:
    """An evidence id in the register, or a file inside the repository root.

    An absolute path or one that escapes the root through ``..`` never resolves:
    an admission may rest only on evidence the repository carries.
    """
    if reference in register:
        return True
    relative = Path(reference.split("#", 1)[0])
    if not relative.parts or relative.is_absolute():
        return False
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        return False
    return target.is_file()


def check_admission(
    library: dict[str, list[InterventionEffect]] | dict,
    ledger: dict[Key, Adjudication] | None,
    root: Path,
) -> dict[tuple[str, str], Admission]:
    """C1-C8 and §6.1 items 4-5 for every direct intervention, or refuse.

    Called by ``engine._license_direct_effects`` once every effect has its O8b
    approval. The entity map and the declarations are validated whenever they
    exist, so a declaration can never name a legacy or migrated intervention; one
    whose rows do not exist yet licenses nothing, as an approval does. Returns what the run record needs (§6.5).
    """
    entity_map = load_entity_map(root)
    declarations = load_declarations(root)
    direct: dict[tuple[str, str], list[InterventionEffect]] = {}
    for effects in library.values():
        for effect in effects:
            if effect.mapping_basis == DIRECT_BASIS:
                direct.setdefault(
                    (effect.intervention_id, effect.model_version), []
                ).append(effect)
    for (intervention_id, version), declaration in (declarations or {}).items():
        bases = {
            e.mapping_basis
            for e in library.get(intervention_id, ())
            if e.model_version == version
        }
        if bases - {DIRECT_BASIS}:
            # As for the ledger: a declaration cannot make a legacy or migrated
            # row a direct one. One with no rows yet licenses nothing.
            raise InterventionError(
                f"{DECLARATIONS_PATH} {declaration.declaration_id}: "
                f"{intervention_id} is {', '.join(sorted(bases))} on {version}; "
                f"only {DIRECT_BASIS} interventions are declared here"
            )
    if entity_map is not None:
        for version, rows in entity_map.items():
            check_entity_map_coverage(rows, version, root)
    if not direct:
        return {}
    if declarations is None or entity_map is None:
        raise InterventionError(
            f"{DIRECT_BASIS} rows need {DECLARATIONS_PATH} and {ENTITY_MAP_PATH}"
        )
    register = set(_register_references(root))
    policy = load_target_policy(root)
    admissions: dict[tuple[str, str], Admission] = {}
    for (intervention_id, version), effects in direct.items():
        where = f"{intervention_id} ({version})"
        declaration = declarations.get((intervention_id, version))
        if declaration is None:
            raise InterventionError(
                f"{where}: no declaration in {DECLARATIONS_PATH} (C1)"
            )
        where = f"{where} {declaration.declaration_id}"
        rows = entity_map.get(version)
        if rows is None:
            raise InterventionError(f"{where}: {ENTITY_MAP_PATH} has no {version} rows")
        check_floor_coverage(rows, version, root)
        spec = resolve_model(version, root)
        with spec.node_dictionary.open(encoding="utf-8", newline="") as handle:
            roles = {
                r["node_id"]: r["model_role"]
                for r in csv.DictReader(handle, delimiter="\t")
            }
        targets = {effect.target_node for effect in effects}
        # C2: the declaration is of exactly these rows.
        if declaration.declared != targets:
            raise InterventionError(
                f"{where}: declared_targets {sorted(declaration.declared)} are not "
                f"the library's targets {sorted(targets)} (C2)"
            )
        digest = library_rows_digest(effects)
        if digest != declaration.library_rows_sha256:
            raise InterventionError(
                f"{where}: the library rows changed since the declaration "
                f"(rows sha256 {digest}, declared {declaration.library_rows_sha256}) (C2)"
            )
        # C4: a narrowed set of compartments cites a source that resolves.
        if declaration.reached != set(COMPARTMENTS) and not declaration.reached_sources:
            raise InterventionError(
                f"{where}: reached_compartments is narrowed to "
                f"{sorted(declaration.reached)} with no {SOURCE_PREFIX}<source> (C4)"
            )
        for source in declaration.reached_sources + declaration.sources:
            if not _resolves(root, source, register):
                raise InterventionError(f"{where}: source {source} does not resolve")
        by_node: dict[str, list[EntityRow]] = {}
        for row in rows:
            if row.node_id:
                by_node.setdefault(row.node_id, []).append(row)
        # C5, then C7: each declared target's coverage by the known entities.
        for node in sorted(targets):
            node_rows = by_node.get(node)
            if not node_rows:
                raise InterventionError(
                    f"{where}: {node} has no {ENTITY_MAP_PATH} row (C5)"
                )
            aggregation = node_rows[0].aggregation
            members = {(r.entity, r.level) for r in node_rows}
            hit = members & declaration.known
            if aggregation in (AMBIGUOUS, DERIVED):
                raise InterventionError(
                    f"{where}: {node} is {aggregation} in {ENTITY_MAP_PATH}, so no "
                    "veto of it can be approved (C5)"
                )
            if not hit:
                raise InterventionError(
                    f"{where}: no known target entity is one {node} represents "
                    f"({sorted(f'{e}@{lvl}' for e, lvl in members)}) (C7)"
                )
            if aggregation == ANY_OF and hit != members:
                missing = sorted(f"{e}@{lvl}" for e, lvl in members - hit)
                raise InterventionError(
                    f"{where}: {node} is {ANY_OF}, and the agent leaves {missing} "
                    "unhit: partial engagement of the node (C5)"
                )
        # C3: every node carrying a known entity at its level, in a reached
        # compartment, is declared -- or the intervention cannot be represented.
        for entity, level in sorted(declaration.known):
            for row in rows:
                if not row.node_id or (row.entity, row.level) != (entity, level):
                    continue
                if row.compartment not in declaration.reached:
                    continue
                if row.node_id in targets:
                    continue
                refusal = policy_refusal(
                    policy, row.node_id, roles.get(row.node_id, "")
                )
                if refusal:
                    raise InterventionError(
                        f"{where}: {entity}@{level} lands on {row.node_id}, which a "
                        f"veto may not mean ({refusal}); the intervention cannot be "
                        "represented (C3)"
                    )
                raise InterventionError(
                    f"{where}: {entity}@{level} is carried by {row.node_id} in the "
                    f"reached {row.compartment}, which is not declared (C3)"
                )
        # C6: every known entity the version does not represent is classified.
        # Unrepresented means no node carries it at that level, or a model gap
        # carries it in a reached compartment.
        gaps: dict[Entity, set[str]] = {}
        for row in rows:
            if row.aggregation == MODEL_GAP and (
                not row.compartment or row.compartment in declaration.reached
            ):
                gaps.setdefault((row.entity, row.level), set()).add(row.gap_id)
        # The floor is recognised by entity, at any level: a floor item read at
        # activity still names FOXO1 when a declaration says FOXO1@expression
        # (amendment A2).
        floor_gaps: dict[str, set[str]] = {}
        for (gap_entity, _), ids in gaps.items():
            floor_gaps.setdefault(gap_entity, set()).update(ids)
        carried = {(r.entity, r.level) for r in rows if r.node_id}
        unrepresented = {e for e in declaration.known if e not in carried or e in gaps}
        classified = {(u.entity, u.level): u for u in declaration.unrepresented}
        for entity, level in sorted(unrepresented - set(classified)):
            raise InterventionError(
                f"{where}: known target {entity}@{level} is not represented in "
                f"{version} and is not classified (C6)"
            )
        for entity, level in sorted(set(classified) - unrepresented):
            raise InterventionError(
                f"{where}: {entity}@{level} is classified as unrepresented but is "
                "not an unrepresented known target (C6)"
            )
        floor = scope_floor(version, root)
        for (entity, level), entry in sorted(classified.items()):
            linked = entry.floor[len(FLOOR_PREFIX) :] if entry.floor != NO_FLOOR else ""
            if linked and linked not in floor:
                raise InterventionError(
                    f"{where}: {entity}@{level} names {entry.floor}, which is not a "
                    "§3.5.1 floor item (C6)"
                )
            if entity in floor_gaps and linked not in floor_gaps[entity]:
                raise InterventionError(
                    f"{where}: {entity}@{level} is the model gap "
                    f"{sorted(floor_gaps[entity])} and must name it as "
                    f"{FLOOR_PREFIX}<id> (C6)"
                )
            if linked and entry.scope == OUT_OF_SCOPE:
                raise InterventionError(
                    f"{where}: {entity}@{level} is on the §3.5.1 floor "
                    f"({linked}) and may not be {OUT_OF_SCOPE} (C6)"
                )
            for basis in entry.basis:
                if not _resolves(root, basis, register):
                    raise InterventionError(
                        f"{where}: {entity}@{level} basis {basis} does not resolve (C6)"
                    )
        # C8 and §6.1 item 4: every approval names this declaration.
        evidence: set[str] = set()
        for effect in effects:
            entry = (ledger or {})[
                (
                    effect.intervention_id,
                    effect.model_version,
                    effect.target_node,
                    effect.mode,
                )
            ]
            evidence.update(entry.evidence_ids)
            if entry.target_declaration_sha256 != declaration.row_sha256:
                raise InterventionError(
                    f"{where}: {entry.adjudication_id} names declaration "
                    f"{entry.target_declaration_sha256 or '<none>'}, not "
                    f"{declaration.declaration_id} ({declaration.row_sha256}) (C8)"
                )
        overlap = construction_overlap(version, targets, evidence, root)
        if declaration.construction_overlap != overlap:
            raise InterventionError(
                f"{where}: construction_overlap is generated and reads {overlap!r}, "
                f"not {declaration.construction_overlap!r} (§6.5)"
            )
        # §6.1 item 5: the class the run record will carry must be current.
        expressivity_classes(version, root)
        admissions[(intervention_id, version)] = Admission(
            declaration=declaration,
            compound_claim_blocked=any(
                u.scope == SCOPE_RELEVANT for u in declaration.unrepresented
            ),
            construction_overlap=overlap,
        )
    return admissions


def admission_record(
    intervention_ids: list[str] | tuple[str, ...],
    library: dict[str, tuple[InterventionEffect, ...]],
    model_version: str,
    root: Path,
) -> dict[str, object] | None:
    """§6.5: the run-record fields for the direct interventions a run names.

    ``None`` when it names none. The flags are run-level: any null target sets
    ``phenotype_claim_blocked`` and any ``scope_relevant`` unrepresented target
    sets ``compound_claim_blocked``. Neither withholds execution (§5.6, owner
    decision 4); both bound what the result may be reported as.
    """
    from dt_adoc.model.provenance import describe_file

    named = [
        effect
        for intervention_id in intervention_ids
        for effect in library.get(intervention_id, ())
        if effect.model_version == model_version
        and effect.mapping_basis == DIRECT_BASIS
    ]
    if not named:
        return None
    admissions = check_admission(library, load_adjudications(root), root)
    classes = expressivity_classes(model_version, root)
    interventions, effects = [], []
    out_of_scope: list[str] = []
    phenotype_blocked = False
    for intervention_id in dict.fromkeys(e.intervention_id for e in named):
        admission = admissions[(intervention_id, model_version)]
        declaration = admission.declaration
        arm = classes[intervention_id]
        interventions.append(
            {
                "intervention_id": intervention_id,
                "declaration_id": declaration.declaration_id,
                "declaration_sha256": declaration.row_sha256,
                "library_rows_sha256": declaration.library_rows_sha256,
                "unrepresented_known_targets": [
                    {
                        "entity": f"{u.entity}@{u.level}",
                        "class": u.scope,
                        "floor": u.floor,
                        "basis": list(u.basis),
                    }
                    for u in declaration.unrepresented
                ],
                "construction_overlap": admission.construction_overlap,
                "expressivity_class": arm["observed_class"],
                "extended_class": arm["extended_class"],
                "class_members": arm["observed_class_members"].split(";"),
                "compound_claim_blocked": admission.compound_claim_blocked,
            }
        )
        out_of_scope.extend(
            f"{intervention_id}: {u.entity}@{u.level}"
            for u in declaration.unrepresented
            if u.scope == OUT_OF_SCOPE
        )
    for effect in named:
        row = classes.get(effect.target_node)
        if row is None or row["arm_kind"] != "eligible_node":
            raise InterventionError(
                f"{effect.intervention_id} -> {effect.target_node}: the expressivity "
                "artefact has no class for this target"
            )
        null = row["structurally_null_on_observed"] == "yes"
        phenotype_blocked |= null
        effects.append(
            {
                "intervention_id": effect.intervention_id,
                "target_node": effect.target_node,
                "expressivity_class": row["observed_class"],
                "extended_class": row["extended_class"],
                "class_members": row["observed_class_members"].split(";"),
                "structurally_null_on_observed": null,
            }
        )
    expressivity, invariance = EXPRESSIVITY_ARTEFACTS[model_version]
    return {
        "pre_registration": ADMISSION_PREREGISTRATION,
        "node_entity_map": describe_file(root / ENTITY_MAP_PATH, root=root).__dict__,
        "target_declarations": describe_file(
            root / DECLARATIONS_PATH, root=root
        ).__dict__,
        "expressivity_artefact": describe_file(root / expressivity, root=root).__dict__,
        "expressivity_invariance": describe_file(root / invariance, root=root).__dict__,
        "interventions": interventions,
        "effects": effects,
        "phenotype_claim_blocked": phenotype_blocked,
        "compound_claim_blocked": any(
            i["compound_claim_blocked"] for i in interventions
        ),
        "claim_boundary": {
            "engagement": "complete-engagement counterfactual; no partial engagement",
            "magnitude": "direction-only: adhesion magnitudes are relay priors",
            "resolution": "class-level: no discrimination within an expressivity class",
            "out_of_scope_unrepresented_targets": out_of_scope,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "validate",
        help="load the library (all licences) and require the committed audit to match",
    )
    sub.add_parser("write-audit", help=f"regenerate {AUDIT_PATH}")
    sub.add_parser("digests", help="print each direct row's key and digest")
    args = parser.parse_args(argv)
    root = repo_root()
    if args.command == "digests":
        for line in direct_row_digests(root):
            print(line)
        return 0
    text = render_audit(target_audit(root=root))
    if args.command == "write-audit":
        (root / AUDIT_PATH).parent.mkdir(parents=True, exist_ok=True)
        (root / AUDIT_PATH).write_text(text, encoding="utf-8")
        return 0
    library = load_intervention_library(root)
    ledger = load_adjudications(root) or {}
    check_policy_basis(root)
    if (root / AUDIT_PATH).read_text(encoding="utf-8") != text:
        print(f"{AUDIT_PATH} is stale; run write-audit", file=sys.stderr)
        return 1
    # §6.6: a missing or stale expressivity artefact fails here too, rows or not.
    try:
        for version in EXPRESSIVITY_ARTEFACTS:
            expressivity_classes(version, root)
    except InterventionError as error:
        print(error, file=sys.stderr)
        return 1
    entity_map = load_entity_map(root) or {}
    try:
        for version, rows in entity_map.items():
            check_floor_coverage(rows, version, root)
    except InterventionError as error:
        print(error, file=sys.stderr)
        return 1
    declarations = load_declarations(root) or {}
    direct = sum(
        e.mapping_basis == DIRECT_BASIS for effects in library.values() for e in effects
    )
    print(
        f"ok: {len(ledger)} adjudication rows, {len(declarations)} target "
        f"declarations, {direct} licensed direct rows, entity map covers "
        f"{', '.join(sorted(entity_map)) or 'no version'}, audit and expressivity "
        "artefacts current"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
