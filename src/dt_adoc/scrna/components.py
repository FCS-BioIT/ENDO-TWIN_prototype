"""U6: the evidence-state enum, the component combinator and the component map.

WHAT THIS IS. Layer B of `docs/v05_mechanistic_integration_plan.md` §1.3 -- the
one layer that did not exist. `measurement_features` in the observation map is a
flat `;`-list with no grouping, no AND/OR and no role, so it cannot say that a
node needs *these* components together, or that one gene votes on direction while
another only establishes availability. This module adds the smallest schema that
can say those things, and the combinator that evaluates it.

WHAT THIS IS NOT. It computes no gate, writes no `.cfg`, clamps nothing and reads
no expression value. The gate layer is blocked by §0.2 and U7. The one clamp
statement here, `clamp_permitted_by_evidence`, is a NECESSARY condition that a
later gate layer must honour -- never a sufficient one.

THREE THINGS KEPT APART, because each has been conflated before:

1. **Four states, not three.** `NOT_ASSESSABLE` (RNA can never speak about this)
   is not a kind of `INDETERMINATE` (RNA did not resolve it this time). §1.2.
2. **The state and the reason.** The frozen support vocabulary records *why*
   something is indeterminate. `uninformative_integrity` (an integrity control
   was run and FAILED) and `uninformative_no_integrity_control` (no control is
   DEFINED for the compartment, so nothing ran to fail) coarsen to the same
   state and are never merged: the reason travels verbatim beside it. §0.8(e).
3. **The state and its provenance.** `provisional_corrected_layer_only` is
   orthogonal metadata. A provisional absence is still `ABSENT_POWERED`, still
   combines as one, and never authorises a clamp. §6.3(4).

NO BIOLOGY IS DECLARED HERE. §6.2: a component group is admissible only when a
cited source states the requirement structure. None is registered, and the one
the plan calls justified (`E_ITGAVB3_5`) is contradicted by the committed node
dictionary, which reads it as "surface ITGAV or ITGB3 or ITGB5". So every
assessable node is `undeclared` -- a valid state that evaluates to
`INDETERMINATE` -- and `DECLARED_REQUIREMENTS` is empty. The declared-structure
path exists and is tested on synthetic fixtures, so the first real declaration
lands in code that has already been proven.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


class ComponentMapError(ValueError):
    """The component map is malformed. A broken table, never an honest gap."""


# --------------------------------------------------------------------------
# The four-state enum, mapped from the frozen support vocabulary (§1.2)
# --------------------------------------------------------------------------


class EvidenceState(Enum):
    """String-valued on purpose: there is no order to compute with. §1.2."""

    PRESENT = "PRESENT"
    INDETERMINATE = "INDETERMINATE"
    ABSENT_POWERED = "ABSENT_POWERED"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


#: The frozen `node_support` labels that are not `uninformative`.
SUPPORT_LABEL_STATE: dict[str, EvidenceState] = {
    "robustly_detected": EvidenceState.PRESENT,
    "sparse_or_low": EvidenceState.INDETERMINATE,
    "not_detected_with_power": EvidenceState.ABSENT_POWERED,
    "not_RNA_assessable": EvidenceState.NOT_ASSESSABLE,
}

#: Every `uninformative` reason `node_support.py` can emit. All five coarsen to
#: `INDETERMINATE` and each is kept verbatim as the reason. The two integrity
#: reasons are the pair that must not collapse: one is a control that FAILED,
#: the other a control that is NOT DEFINED for the compartment.
UNINFORMATIVE_REASONS: frozenset[str] = frozenset(
    {
        "uninformative_n",
        "uninformative_exposure",
        "uninformative_integrity",
        "uninformative_no_integrity_control",
        "missing_unit",
    }
)

#: The one provenance flag the frozen audit attaches to an absence.
PROVISIONAL_FLAG = "provisional_corrected_layer_only"


@dataclass(frozen=True)
class Evidence:
    """One evidence state, the reason it holds, and its absence provenance.

    `state` and `provisional` are the evidence. `reason` is a TRACE of how the
    value was reached -- a frozen label or reason, or the order-preserving
    expression a combination was evaluated over -- and is outside the algebra:
    two evaluations of equivalent groups can agree on (state, provisional) and
    still differ in `reason`, because the trace records the group as written.
    Compare `evidence_key`, never whole `Evidence` objects, when asking whether
    two results are the same evidence.
    """

    state: EvidenceState
    reason: str
    provisional: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.state, EvidenceState):
            raise ComponentMapError(f"not an evidence state: {self.state!r}")
        if not self.reason:
            raise ComponentMapError("an evidence state must carry its reason")
        if self.provisional and self.state is not EvidenceState.ABSENT_POWERED:
            # The flag qualifies an ABSENCE. On any other state it would be
            # provenance about an observation that was never made.
            raise ComponentMapError(
                f"{PROVISIONAL_FLAG} qualifies an absence only, not {self.state.value}"
            )


def evidence_from_support(
    label: str, reason: str = "", provisional: str = ""
) -> Evidence:
    """Map one frozen support label onto the enum, keeping its reason.

    Total over the committed vocabulary and closed against anything else: an
    unknown label or reason raises rather than falling into a default.
    """
    if label == "uninformative":
        if reason not in UNINFORMATIVE_REASONS:
            raise ComponentMapError(f"unknown uninformative reason {reason!r}")
        if provisional:
            raise ComponentMapError("an uninformative call carries no absence flag")
        return Evidence(EvidenceState.INDETERMINATE, reason)
    if label not in SUPPORT_LABEL_STATE:
        raise ComponentMapError(f"unknown support label {label!r}")
    if reason:
        raise ComponentMapError(f"label {label!r} carries no reason, got {reason!r}")
    state = SUPPORT_LABEL_STATE[label]
    if provisional and provisional != PROVISIONAL_FLAG:
        raise ComponentMapError(f"unknown provenance flag {provisional!r}")
    return Evidence(state, label, provisional == PROVISIONAL_FLAG)


# --------------------------------------------------------------------------
# The combinator -- §6.3, frozen before this was written
# --------------------------------------------------------------------------

AND = "AND"
OR = "OR"

#: First match wins. Each operation is therefore commutative, associative and
#: idempotent by construction ON THE (state, provisional) PROJECTION -- see
#: `evidence_key` -- so any nesting yields the same evidence. The `reason` trace
#: is deliberately not canonicalized: it records the group as written, so it
#: changes with order and nesting and is not part of that contract. `NOT_ASSESSABLE`
#: outranks `INDETERMINATE` in BOTH: the two operators are deliberately not De
#: Morgan duals, because the schema has no negation (§6.3(1)).
PRECEDENCE: dict[str, tuple[EvidenceState, ...]] = {
    AND: (
        EvidenceState.ABSENT_POWERED,
        EvidenceState.NOT_ASSESSABLE,
        EvidenceState.INDETERMINATE,
        EvidenceState.PRESENT,
    ),
    OR: (
        EvidenceState.PRESENT,
        EvidenceState.NOT_ASSESSABLE,
        EvidenceState.INDETERMINATE,
        EvidenceState.ABSENT_POWERED,
    ),
}


def evidence_key(evidence: Evidence) -> tuple[EvidenceState, bool]:
    """The part of an `Evidence` the combination algebra is defined over."""
    return evidence.state, evidence.provisional


def combine(logic: str, components: Sequence[Evidence]) -> Evidence:
    """Combine component evidence under one AND or OR group.

    An empty group raises: the AND identity is `PRESENT` and the OR identity
    `ABSENT_POWERED`, so an empty group would silently assert availability or
    absence (§6.3(3)).

    The absence flag propagates DUALLY (§6.3(4)). Under AND any one absent
    component justifies an absent result, so it is provisional only if EVERY
    absent component is. Under OR every alternative must be absent, so each is
    load-bearing and the result is provisional if ANY is.
    """
    if logic not in PRECEDENCE:
        raise ComponentMapError(f"unknown group logic {logic!r}")
    if not components:
        raise ComponentMapError(f"an empty {logic} group is a schema error")
    present = {c.state for c in components}
    state = next(s for s in PRECEDENCE[logic] if s in present)
    provisional = False
    if state is EvidenceState.ABSENT_POWERED:
        absent = [c for c in components if c.state is EvidenceState.ABSENT_POWERED]
        if logic == AND:
            provisional = all(c.provisional for c in absent)
        else:
            provisional = any(c.provisional for c in absent)
    reason = f"{logic}[{','.join(c.reason for c in components)}]"
    return Evidence(state, reason, provisional)


def clamp_permitted_by_evidence(evidence: Evidence) -> bool:
    """The evidence-side veto on a hard clamp (T-E2). Necessary, not sufficient.

    Only a confirmed powered absence may ever stand behind a clamp; a provisional
    one never does, directly or after combination. This is the pre-registration's
    §3.1(3) -- no structural conclusion rests on a provisional absence -- at the
    point where it would bite. Whether a node may be clamped at all is a
    gate-layer question this module does not answer.
    """
    return evidence.state is EvidenceState.ABSENT_POWERED and not evidence.provisional


# --------------------------------------------------------------------------
# Requirement structures
# --------------------------------------------------------------------------

DECLARED = "declared"
UNDECLARED = "undeclared"
REQUIRES_DEFINITION = "requires_definition"
NOT_APPLICABLE = "not_applicable"

#: `undeclared` and `requires_definition` are VALID states meaning the biology
#: was never established; both evaluate to `INDETERMINATE` and create no
#: constraint (T-J). `not_applicable` is a node RNA cannot assess at all.
REQUIREMENT_STRUCTURES: frozenset[str] = frozenset(
    {DECLARED, UNDECLARED, REQUIRES_DEFINITION, NOT_APPLICABLE}
)


@dataclass(frozen=True)
class Group:
    """One AND/OR requirement group over committed symbols and subgroups."""

    logic: str
    members: tuple[Group | str, ...]


def evaluate(
    requirement: Group | str, evidence_by_symbol: Mapping[str, Evidence]
) -> Evidence:
    """Evaluate a requirement tree, or a structure state, against evidence.

    A symbol with no evidence raises: silence about a component is not
    evidence about it.
    """
    if isinstance(requirement, str):
        if requirement in {UNDECLARED, REQUIRES_DEFINITION}:
            return Evidence(
                EvidenceState.INDETERMINATE, f"requirement_structure_{requirement}"
            )
        if requirement == NOT_APPLICABLE:
            return Evidence(EvidenceState.NOT_ASSESSABLE, "not_RNA_assessable")
        raise ComponentMapError(f"not a requirement structure: {requirement!r}")
    return combine(
        requirement.logic,
        [_member(member, evidence_by_symbol) for member in requirement.members],
    )


def _member(
    member: Group | str, evidence_by_symbol: Mapping[str, Evidence]
) -> Evidence:
    if isinstance(member, Group):
        return evaluate(member, evidence_by_symbol)
    if member not in evidence_by_symbol:
        raise ComponentMapError(f"no evidence supplied for component {member!r}")
    return evidence_by_symbol[member]


#: Requirement structures stated by a cited source, keyed (node, variant_id).
#: EMPTY, and that is the finding: no registered source states one. See the
#: module docstring and `docs/v05_u6_semantics_components.md`.
DECLARED_REQUIREMENTS: dict[tuple[str, str], tuple[Group, str]] = {}

#: Nodes whose requirement structure is not merely unstated but undefined.
#: `E_CD98_CD9` is one node named for two different complexes -- CD98 is
#: SLC3A2 with an SLC7A light chain, CD9 a tetraspanin -- and its own dictionary
#: row reads "CD98 or CD9 route" in the label and "surface CD98 and CD9" in the
#: observation column. `MIN(SLC3A2, CD9)` would invent the structure. §6.2.
REQUIRES_DEFINITION_NODES: dict[str, str] = {
    "E_CD98_CD9": (
        "one node named for two complexes (CD98 = SLC3A2 + SLC7A*, CD9 = "
        "tetraspanin); the committed dictionary reads it as both 'or' and 'and'"
    ),
}


# --------------------------------------------------------------------------
# HGNC previous-symbol resolution -- the U6 owner decision
# --------------------------------------------------------------------------

#: OWNER DECISION, 2026-09-23: explicit, forward-only, per-symbol resolution.
#: Not a general normaliser -- a fuzzy symbol matcher is exactly what the
#: observation map refused (`_ANALYTE_TO_SYMBOL` in `observability.py`), and
#: this table may only name symbols the audit actually recorded as absent.
#:
#: Both are 1:1 renames of the same gene, verified against the HGNC REST service
#: (rest.genenames.org, prev_symbol search and symbol fetch) on 2026-09-23:
#: HGNC records each old symbol as a `prev_symbol` of exactly one approved gene,
#: with `date_symbol_changed` 2018-10-11.
#:
#: What this does NOT say. The frozen audit is untouched: it ran with CTGF and
#: CYR61 absent under the committed symbols and substituted nothing, and stays
#: so. `feature_absent` means the COMMITTED SYMBOL was absent from the audited
#: feature namespace -- not that the gene is. Whether `CCN2`/`CCN1` are in the
#: 78,724-feature object is UNVERIFIED, and no `S_TAZ_ECM` evidence may use an
#: alias-resolved feature until a new, registered extraction checks it.
HGNC_PREVIOUS_SYMBOL_RESOLUTIONS: dict[str, tuple[str, str]] = {
    "CTGF": ("CCN2", "HGNC:2500"),
    "CYR61": ("CCN1", "HGNC:2654"),
}
HGNC_RESOLUTION_VERIFIED_ON = "2026-09-23"

PRESENT_IN_NAMESPACE = "present_in_audited_namespace"
FEATURE_ABSENT = "feature_absent"
COMMITTED_SYMBOL_STATUSES: frozenset[str] = frozenset(
    {PRESENT_IN_NAMESPACE, FEATURE_ABSENT}
)
VERIFIED_RENAME = "verified_rename"
ALIAS_RESOLUTIONS: frozenset[str] = frozenset({NOT_APPLICABLE, VERIFIED_RENAME})
#: `verified` is deliberately not a value yet: only a registered extraction may
#: introduce it, and adding it is how that extraction becomes visible.
UNVERIFIED = "unverified"
CURRENT_SYMBOL_PRESENCE: frozenset[str] = frozenset({NOT_APPLICABLE, UNVERIFIED})


# --------------------------------------------------------------------------
# The component map
# --------------------------------------------------------------------------

#: `support_feature` -- the committed feature list node support uses (§4).
#: `direction_readout` -- a symbol of the committed CNT->HT direction-vote
#:   PROGRAM after R1 and R2. It says the symbol is in the program, not that it
#:   voted: a symbol absent from the audited namespace (`CTGF`, `CYR61`) is in
#:   the program and contributed nothing, and its `committed_symbol_status =
#:   feature_absent` is what records that. It stays unusable until a registered
#:   alias extraction verifies the current symbol.
#: `availability_requirement` -- a component of a DECLARED requirement group.
#: Availability and direction use different gene sets for the same node
#: (`E_GP130_STAT3` votes on SOCS3 and BCL3 and excludes STAT3), so the role is
#: carried or the two get conflated on first reuse. §6.1.
ROLES: frozenset[str] = frozenset(
    {"support_feature", "direction_readout", "availability_requirement"}
)

#: `node_level` requirements carry only what every admissible variant shares;
#: anything variant-specific attaches to a `variant` set naming a `variant_id`
#: of the model's `rule_variants.tsv`. §6.1.
REQUIREMENT_SETS: frozenset[str] = frozenset({"node_level", "variant"})

COMPONENT_FIELDS: tuple[str, ...] = (
    "model_node",
    "requirement_set",
    "variant_id",
    "requirement_structure",
    "role",
    "requirement_group",
    "parent_group",
    "logic",
    "symbol_as_committed",
    "committed_symbol_status",
    "current_hgnc_symbol",
    "hgnc_id",
    "alias_resolution",
    "current_symbol_presence",
    "source",
)

COMPONENT_MAP = Path("docs/u6_semantics/component_map.tsv")

#: The model whose `rule_variants.tsv` defines the admissible variants (§6.1:
#: "the variant set declared there for the model under evaluation"). A
#: `variant` row must name a `(variant_id, node_id)` pair that file declares;
#: moving to a later model version means changing this, visibly.
GOVERNING_MODEL = "adoc-literature-superset-v0.5.1"
RULE_VARIANTS = Path("models/superset") / GOVERNING_MODEL / "rule_variants.tsv"


def declared_variants(root: Path = REPO) -> frozenset[tuple[str, str]]:
    """Every `(variant_id, node_id)` pair the governing model declares."""
    with (root / RULE_VARIANTS).open(newline="", encoding="utf-8") as handle:
        return frozenset(
            (row["variant_id"], row["node_id"])
            for row in csv.DictReader(handle, delimiter="\t")
        )


FINDINGS = Path("docs/scrna/node_support_findings.json")


def absent_features(root: Path = REPO) -> frozenset[str]:
    """Symbols recorded as absent from the object: the frozen audit's, plus any
    gene a post-closure observation-map correction reads that its own extraction
    did not find (`observation_corrections.absent_features`)."""
    from dt_adoc.scrna import observation_corrections as O

    return O.absent_features(root)


def _symbol_fields(symbol: str, absent: frozenset[str]) -> dict[str, str]:
    if symbol not in absent:
        return {
            "committed_symbol_status": PRESENT_IN_NAMESPACE,
            "current_hgnc_symbol": "",
            "hgnc_id": "",
            "alias_resolution": NOT_APPLICABLE,
            "current_symbol_presence": NOT_APPLICABLE,
        }
    if symbol not in HGNC_PREVIOUS_SYMBOL_RESOLUTIONS:
        # T-E: an absent symbol is recorded, never silently resolved.
        return {
            "committed_symbol_status": FEATURE_ABSENT,
            "current_hgnc_symbol": "",
            "hgnc_id": "",
            "alias_resolution": NOT_APPLICABLE,
            "current_symbol_presence": NOT_APPLICABLE,
        }
    current, hgnc_id = HGNC_PREVIOUS_SYMBOL_RESOLUTIONS[symbol]
    return {
        "committed_symbol_status": FEATURE_ABSENT,
        "current_hgnc_symbol": current,
        "hgnc_id": hgnc_id,
        "alias_resolution": VERIFIED_RENAME,
        "current_symbol_presence": UNVERIFIED,
    }


def requirement_structure(node: str, assessable: bool) -> str:
    """A node's node-level requirement structure. Never inferred from its genes."""
    if not assessable:
        return NOT_APPLICABLE
    if (node, "") in DECLARED_REQUIREMENTS:
        return DECLARED
    if node in REQUIRES_DEFINITION_NODES:
        return REQUIRES_DEFINITION
    return UNDECLARED


def build_component_rows(root: Path = REPO) -> list[dict[str, str]]:
    """The committed component map, generated from canonical inputs only.

    Feature and direction rows come from `node_support_contract`, read over the
    CORRECTED observation map (`observation_corrections`), so a superseded
    feature such as `E_PC6`'s PCSK6 never reaches this live table; symbol status
    from `absent_features`; and requirement groups from `DECLARED_REQUIREMENTS`,
    which is empty.
    """
    from dt_adoc.scrna import node_support_contract as C
    from dt_adoc.scrna.observation_corrections import corrected_map_path

    map_path = corrected_map_path(root)
    assessable = C.assessable_nodes(map_path)
    direction = C.direction_vote_programs(map_path)
    absent = absent_features(root)
    if HGNC_PREVIOUS_SYMBOL_RESOLUTIONS.keys() - absent:
        raise ComponentMapError(
            "an HGNC resolution names a symbol the audit did not record as "
            "absent; this table is not a general normaliser"
        )
    if DECLARED_REQUIREMENTS:
        raise ComponentMapError(
            "DECLARED_REQUIREMENTS is not empty: emit its group rows, with the "
            "cited source, before committing a declaration"
        )
    rows: list[dict[str, str]] = []
    for node in sorted(assessable):
        structure = requirement_structure(node, True)
        base = {
            "model_node": node,
            "requirement_set": "node_level",
            "variant_id": "",
            "requirement_structure": structure,
            "requirement_group": "",
            "parent_group": "",
            "logic": "",
        }
        for role, symbols, source in (
            (
                "support_feature",
                C.features(assessable[node]),
                (
                    "docs/scrna_corrections/scrna_observation_map_corrected.tsv "
                    "measurement_features"
                ),
            ),
            (
                "direction_readout",
                direction[node],
                (
                    "node_support_contract.direction_vote_programs over the corrected "
                    "map (R1, then R2)"
                ),
            ),
        ):
            for symbol in symbols:
                rows.append(
                    {
                        **base,
                        "role": role,
                        "symbol_as_committed": symbol,
                        **_symbol_fields(symbol, absent),
                        "source": source,
                    }
                )
    return rows


def render_component_map(root: Path = REPO) -> str:
    import io

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=list(COMPONENT_FIELDS), delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(build_component_rows(root))
    return buffer.getvalue()


def load_component_map(path: Path) -> list[dict[str, str]]:
    """Read a component map and validate it as a schema, groups included."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != COMPONENT_FIELDS:
            raise ComponentMapError(f"column set drifted: {reader.fieldnames!r}")
        rows = list(reader)
    validate_component_rows(rows, declared_variants())
    return rows


#: Fields that describe a committed symbol, and so are blank on a group row.
_SYMBOL_PROVENANCE_FIELDS: tuple[str, ...] = (
    "committed_symbol_status",
    "current_hgnc_symbol",
    "hgnc_id",
    "alias_resolution",
    "current_symbol_presence",
)


def validate_component_rows(
    rows: Sequence[Mapping[str, str]],
    variants: frozenset[tuple[str, str]] | None = None,
) -> None:
    """Validate rows as a schema. `variants` defaults to the governing model's."""
    known = declared_variants() if variants is None else variants
    for row in rows:
        _validate_row(row)
        if row["variant_id"] and (row["variant_id"], row["model_node"]) not in known:
            # An unknown id, or one declared for a different node, would let a
            # typo carry availability logic that no model variant has.
            raise ComponentMapError(
                f"{row['model_node']}: variant {row['variant_id']!r} is not declared "
                f"for this node in {RULE_VARIANTS}"
            )
    by_set: dict[tuple[str, str], list[Mapping[str, str]]] = {}
    for row in rows:
        by_set.setdefault((row["model_node"], row["variant_id"]), []).append(row)
    for key, members in by_set.items():
        structures = {r["requirement_structure"] for r in members}
        if len(structures) != 1:
            raise ComponentMapError(f"{key}: conflicting structures {structures}")
        availability = [r for r in members if r["role"] == "availability_requirement"]
        if structures == {DECLARED}:
            group_tree(key, availability)
        elif availability:
            raise ComponentMapError(
                f"{key}: availability components on a {structures.pop()} structure"
            )


def _validate_row(row: Mapping[str, str]) -> None:
    node = row["model_node"]
    checks = (
        ("requirement_set", REQUIREMENT_SETS),
        ("requirement_structure", REQUIREMENT_STRUCTURES),
        ("role", ROLES),
    )
    for field, allowed in checks:
        if row[field] not in allowed:
            raise ComponentMapError(f"{node}: invalid {field} {row[field]!r}")
    if (row["requirement_set"] == "variant") != bool(row["variant_id"]):
        raise ComponentMapError(f"{node}: a variant set needs a variant_id, only it")
    if not row["source"].strip():
        # A declaration without its cited basis is exactly what §6.2 forbids,
        # and a derived row without one cannot be traced to its input.
        raise ComponentMapError(f"{node}: every row must name its source")
    is_group_row = not row["symbol_as_committed"]
    if is_group_row:
        if row["role"] != "availability_requirement" or not row["logic"]:
            raise ComponentMapError(f"{node}: a group row needs role and logic")
        if any(row[f] for f in _SYMBOL_PROVENANCE_FIELDS):
            raise ComponentMapError(f"{node}: a group row carries no symbol status")
        return
    # A component row sits IN a group; hierarchy and logic belong to group rows,
    # so a value here would be silently ignored rather than honoured.
    if row["parent_group"] or row["logic"]:
        raise ComponentMapError(
            f"{node}: parent_group and logic belong on group rows, not components"
        )
    if row["role"] != "availability_requirement" and row["requirement_group"]:
        raise ComponentMapError(f"{node}: only availability rows sit in a group")
    if row["committed_symbol_status"] not in COMMITTED_SYMBOL_STATUSES:
        raise ComponentMapError(f"{node}: invalid committed_symbol_status")
    if row["alias_resolution"] not in ALIAS_RESOLUTIONS:
        raise ComponentMapError(f"{node}: invalid alias_resolution")
    if row["current_symbol_presence"] not in CURRENT_SYMBOL_PRESENCE:
        raise ComponentMapError(f"{node}: invalid current_symbol_presence")
    renamed = row["alias_resolution"] == VERIFIED_RENAME
    if not renamed == bool(row["current_hgnc_symbol"]) == bool(row["hgnc_id"]):
        # Both, or neither: an id with no symbol (or the reverse) is an
        # identifier whose provenance nobody can read.
        raise ComponentMapError(
            f"{node}: current_hgnc_symbol and hgnc_id appear together, on a rename"
        )
    if renamed and row["committed_symbol_status"] != FEATURE_ABSENT:
        raise ComponentMapError(f"{node}: only an absent symbol is ever resolved")
    if renamed != (row["current_symbol_presence"] == UNVERIFIED):
        raise ComponentMapError(f"{node}: a rename's presence is unverified")


def group_tree(key: tuple[str, str], rows: Sequence[Mapping[str, str]]) -> Group:
    """Assemble one declared requirement set into a single rooted tree.

    Group rows (no symbol) declare `requirement_group`, its `logic` and its
    `parent_group`; component rows name the group they sit in. Empty groups,
    unknown parents, cycles and more than one root all raise.
    """
    logic: dict[str, str] = {}
    parent: dict[str, str] = {}
    symbols: dict[str, list[str]] = {}
    for row in rows:
        group = row["requirement_group"]
        if not group:
            raise ComponentMapError(f"{key}: an availability row names no group")
        if row["symbol_as_committed"]:
            symbols.setdefault(group, []).append(row["symbol_as_committed"])
            continue
        if group in logic:
            raise ComponentMapError(f"{key}: group {group!r} declared twice")
        if row["logic"] not in PRECEDENCE:
            raise ComponentMapError(f"{key}: invalid logic {row['logic']!r}")
        logic[group] = row["logic"]
        parent[group] = row["parent_group"]
    if not logic:
        raise ComponentMapError(f"{key}: a declared structure with no group")
    for group in symbols.keys() | {p for p in parent.values() if p}:
        if group not in logic:
            raise ComponentMapError(f"{key}: undeclared group {group!r}")
    roots = [g for g, p in parent.items() if not p]
    if len(roots) != 1:
        raise ComponentMapError(f"{key}: expected one root group, found {roots}")

    def build(group: str, seen: frozenset[str]) -> Group:
        if group in seen:
            raise ComponentMapError(f"{key}: group cycle through {group!r}")
        children = [g for g, p in parent.items() if p == group]
        members: tuple[Group | str, ...] = tuple(symbols.get(group, [])) + tuple(
            build(child, seen | {group}) for child in sorted(children)
        )
        if not members:
            raise ComponentMapError(f"{key}: empty group {group!r} is a schema error")
        return Group(logic[group], members)

    tree = build(roots[0], frozenset())
    reached: set[str] = set()

    def walk(group: str) -> None:
        reached.add(group)
        for child in (g for g, p in parent.items() if p == group):
            walk(child)

    walk(roots[0])
    if reached != set(logic):
        raise ComponentMapError(f"{key}: groups unreachable from the root")
    return tree


def usable_feature_symbols(
    rows: Sequence[Mapping[str, str]], node: str, role: str = "support_feature"
) -> tuple[str, ...]:
    """The symbols evidence may use for a node: present under the committed name.

    An alias-resolved symbol is excluded while its presence is unverified, which
    is every one of them: the owner decision records the rename and forbids its
    use until a registered extraction confirms the current symbol is present.
    """
    return tuple(
        r["symbol_as_committed"]
        for r in rows
        if r["model_node"] == node
        and r["role"] == role
        and r["committed_symbol_status"] == PRESENT_IN_NAMESPACE
    )
