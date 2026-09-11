"""Which nodes actually generate each prediction, and what licenses them.

A concordance row that names one model node hides the thing a reader most needs:
the prediction is produced by a *path*, and the path's weakest link bounds the
claim. This module derives that path from ``network.bnd`` alone -- no simulation,
no seed, no horizon -- so its statements are properties of the model rather than
estimates from a run.

Three derivations, in increasing usefulness:

* **The backward cone** is every ancestor of a node in the dependency graph. It
  is the honest upper bound on "what feeds this readout", and it is
  uninformative on its own: the cone of ``OUT_STABLE_ADHESION`` is almost the
  whole network.
* **The essential free variables** are the free variables whose flipping changes
  the node's value in at least one of the 2^19 enumerated assignments. This is
  exact, not sampled, because the network is a DAG over its free variables. It
  is the *functional* dependence, and it is much smaller than the cone -- which
  is the finding, not a convenience.
* **The carrying path** is the subset of the cone whose value actually differs
  between two compared arms. That is the mechanism the comparison rests on;
  every other node in the cone is inert with respect to that contrast.

The gap between cone and essential set is the model's structural degeneracy, and
naming it is the point. A node can sit in the cone, carry a literature citation,
and still be unable to move any reported output -- ``structure.load_structure``
already computes that set as ``phenotype_inert``. Reporting a mechanism without
that distinction would credit the model with explanatory structure it does not
execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dt_adoc.model.catalog import load_tsv
from dt_adoc.model.runtime import resolve_model
from dt_adoc.reporting.structure import (
    StructuralFacts,
    _columns,
    _topological_order,
)

#: Evidence classes for the mechanism figure's node encoding. Ordered from the
#: strongest licence to the weakest, because a node belongs to exactly one class
#: and the strongest applicable one wins.
EVIDENCE_CLASSES = (
    # An activated row in config/observation_model_map.tsv: an ADOC measurement
    # is mapped onto this node and evaluated every run.
    "adoc_measured",
    # A declared OUT_ phenotype: a composite of other nodes, never measured
    # directly, so its agreement is the agreement of its parts.
    "composite_output",
    # A protocol input: set by the experimental schedule, not predicted.
    "protocol_input",
    # A free variable that is NOT a protocol input: a hand-set number or an
    # unmodelled state. These are the model's free assumptions.
    "hand_set_free",
    # Everything else: a derived node whose rule came from curated literature.
    "literature_derived",
)

#: Free variables that the ADOC protocol suite sets as part of the experimental
#: schedule. Every other free variable is a modelling assumption rather than a
#: condition, which is why the two are separated here rather than both being
#: called "inputs".
PROTOCOL_INPUT_PREFIX = "IN_"


@dataclass(frozen=True)
class NodeMechanismRecord:
    """Everything a mechanism figure may assert about one node."""

    node_id: str
    label: str
    compartment: str
    evidence_class: str
    #: ``confidence`` verbatim from the model's own node_dictionary.tsv.
    declared_confidence: str
    #: True when clamping this node changes no OUT_ node in any enumerated
    #: state. Such a node cannot generate any reported prediction.
    phenotype_inert: bool
    #: Other nodes implementing the identical Boolean function. A non-empty
    #: roster means this node's agreement is not independent of theirs.
    alias_of: tuple[str, ...]


@dataclass(frozen=True)
class PredictionMechanism:
    """The mechanism behind one readout node, for one arm contrast."""

    node_id: str
    #: Every ancestor in the dependency graph.
    backward_cone: tuple[str, ...]
    #: Free variables whose flipping can change this node, exhaustively.
    essential_free: tuple[str, ...]
    #: Essential free variables that are NOT protocol inputs: the free
    #: assumptions this prediction rests on.
    essential_assumptions: tuple[str, ...]
    #: Cone members that are phenotype-inert, i.e. present but unable to act.
    inert_in_cone: tuple[str, ...]
    #: Longest dependency chain from a free variable to this node.
    depth: int


def _seed_columns(free: tuple[str, ...], states: int) -> dict[str, int]:
    """Standard truth-table bit columns, one per free variable.

    Identical construction to ``reporting.structure.load_structure``; duplicated
    rather than imported because that function builds them inline and returning
    them would change its public shape.
    """
    seeds: dict[str, int] = {}
    for index, node_id in enumerate(free):
        block = 1 << index
        column = 0
        for start in range(block, states, block * 2):
            column |= ((1 << block) - 1) << start
        seeds[node_id] = column
    return seeds


def essential_free_variables(facts: StructuralFacts) -> dict[str, tuple[str, ...]]:
    """Per node, the free variables it actually depends on.

    Exhaustive over every assignment of the free variables. For free variable
    ``k``, the assignments that differ only in bit ``k`` are the positions where
    ``k``'s own column is 0 and those positions shifted up by ``2**k``; the node
    depends on ``k`` exactly when its column differs between the two. That makes
    this a handful of bigint comparisons per pair rather than a loop over states.

    A node's essential set can be far smaller than its backward cone. That is
    the model's degeneracy made numeric, and callers are expected to report it.
    """
    free = facts.free
    states = facts.enumerated_states
    mask = (1 << states) - 1
    order = _topological_order(facts.rules, set(free))
    columns = _columns(facts.rules, order, _seed_columns(free, states), mask)

    essential: dict[str, tuple[str, ...]] = {}
    for node_id in facts.node_ids:
        column = columns[node_id]
        depends: list[str] = []
        for index, candidate in enumerate(free):
            low = (~columns[candidate]) & mask
            if (column & low) != ((column >> (1 << index)) & low):
                depends.append(candidate)
        essential[node_id] = tuple(depends)
    return essential


def backward_cone(facts: StructuralFacts, node_id: str) -> tuple[str, ...]:
    """Every ancestor of ``node_id`` in the dependency graph, sorted.

    Absorbed dependencies are kept. An absorbed edge is one whose regulator
    never changes its target's value, so dropping it would produce a smaller and
    more flattering cone; the cone is meant to state what the rule set *reads*,
    and the inert subset is reported separately instead.
    """
    parents: dict[str, set[str]] = {n: set() for n in facts.node_ids}
    for regulator, target, _polarity in facts.edges:
        parents.setdefault(target, set()).add(regulator)

    seen: set[str] = set()
    stack = list(parents.get(node_id, ()))
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(parents.get(current, ()))
    return tuple(sorted(seen))


def node_records(
    facts: StructuralFacts,
    *,
    model_version: str,
    root: Path | None = None,
) -> dict[str, NodeMechanismRecord]:
    """Classify every node by what licenses it, for the mechanism figure.

    ``declared_confidence`` is copied verbatim from the model's own
    ``node_dictionary.tsv`` rather than re-derived, so the figure cannot assert a
    stronger licence than the curation recorded. A node the dictionary calls an
    ``assumption`` stays an assumption on the figure even when it sits on the
    only path to the endpoint -- which is exactly the case the figure exists to
    expose.
    """
    model = resolve_model(model_version, root)
    dictionary = {row["node_id"]: row for row in load_tsv(model.node_dictionary)}
    measured = set(facts.measured)
    outputs = set(facts.outputs)
    free = set(facts.free)
    inert = set(facts.phenotype_inert)

    alias_of: dict[str, tuple[str, ...]] = {}
    for members in facts.alias_classes:
        for member in members:
            alias_of[member] = tuple(m for m in members if m != member)

    records: dict[str, NodeMechanismRecord] = {}
    for node_id in facts.node_ids:
        row = dictionary.get(node_id, {})
        if node_id in measured:
            evidence_class = "adoc_measured"
        elif node_id in outputs:
            evidence_class = "composite_output"
        elif node_id in free and node_id.startswith(PROTOCOL_INPUT_PREFIX):
            evidence_class = "protocol_input"
        elif node_id in free:
            evidence_class = "hand_set_free"
        else:
            evidence_class = "literature_derived"
        records[node_id] = NodeMechanismRecord(
            node_id=node_id,
            label=row.get("label", node_id),
            compartment=facts.compartment_of.get(node_id, "unknown"),
            evidence_class=evidence_class,
            declared_confidence=row.get("confidence", "unrecorded"),
            phenotype_inert=node_id in inert,
            alias_of=alias_of.get(node_id, ()),
        )
    return records


def prediction_mechanism(
    facts: StructuralFacts,
    node_id: str,
    *,
    essential: dict[str, tuple[str, ...]],
) -> PredictionMechanism:
    """Assemble the mechanism record for one readout node."""
    cone = backward_cone(facts, node_id)
    inert = set(facts.phenotype_inert)
    essential_free = essential[node_id]
    return PredictionMechanism(
        node_id=node_id,
        backward_cone=cone,
        essential_free=essential_free,
        essential_assumptions=tuple(
            name
            for name in essential_free
            if not name.startswith(PROTOCOL_INPUT_PREFIX)
        ),
        inert_in_cone=tuple(name for name in cone if name in inert),
        depth=facts.depth[node_id],
    )


def carrying_path(
    facts: StructuralFacts,
    node_id: str,
    arm_a: dict[str, float],
    arm_b: dict[str, float],
    *,
    tolerance: float = 1e-9,
) -> tuple[str, ...]:
    """Cone members whose simulated value differs between two arms.

    This is the mechanism the contrast actually rests on. Nodes in the cone that
    hold the same value in both arms contribute nothing to the difference, no
    matter how well cited they are, and a figure that draws them as part of the
    explanation overstates the model's engaged structure.

    Values come from a simulation, so unlike everything else in this module the
    result depends on seed, horizon and trajectory count. Callers must carry
    those settings alongside it.
    """
    cone = set(backward_cone(facts, node_id)) | {node_id}
    differing = [
        name
        for name in sorted(cone)
        if name in arm_a
        and name in arm_b
        and abs(arm_a[name] - arm_b[name]) > tolerance
    ]
    return tuple(differing)
