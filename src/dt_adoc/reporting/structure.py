"""Structural facts about an executable MaBoSS network, for static figures.

Every quantity here is a property of ``network.bnd`` alone: no simulation, no
``.cfg``, no protocol duration, no seed, no horizon. That is the point. The
repository's endpoint-readout policy is documented but not implemented
(``docs/endpoint_convergence_finding.md``), so any probabilistic figure would
depend on an unresolved decision and would show a held-out perturbation arm
pointing the wrong way. A structural figure cannot be invalidated by that
decision, which is why it can be published first.

Nothing here reads ``edge_evidence.tsv`` for topology. Evidence records what has
been *cited*; the network records what is *computed*, and for the superset those
differ by four dependencies in one direction and one retired relation in the
other.

The network is a DAG over its free variables, so exhaustive enumeration over
``2 ** len(free)`` assignments is exact rather than sampled. Facts derived that
way -- which nodes can never change a phenotype, which nodes are exact aliases
of one another -- are therefore statements about the model, not estimates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dt_adoc.calibration.observation_map import (
    EVALUABLE_ACTIVATION_STATUSES,
    load_observation_map,
)
from dt_adoc.model.catalog import load_tsv
from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import derive_dependencies, parse_bnd_rules
from dt_adoc.reporting.dynamics import classify_node, load_visualization_config

#: Refuse to enumerate beyond this many states rather than silently sampling.
MAX_ENUMERATION_STATES = 2**22

OUTPUT_PREFIX = "OUT_"
INPUT_PREFIX = "IN_"


@dataclass(frozen=True)
class StructuralFacts:
    """What a static figure is entitled to assert about a model."""

    model_version: str
    node_ids: tuple[str, ...]
    rules: dict[str, str]
    free: tuple[str, ...]
    depth: dict[str, int]
    edges: tuple[tuple[str, str, str], ...]
    outputs: tuple[str, ...]
    #: Nodes whose clamping to 0 and to 1 leaves every OUT_ node unchanged in
    #: every enumerated state. They cannot affect any reported phenotype.
    phenotype_inert: tuple[str, ...]
    #: Free variables that no rule reads, so nothing can depend on them.
    unread_inputs: tuple[str, ...]
    #: Groups of nodes realising the identical Boolean function.
    alias_classes: tuple[tuple[str, ...], ...]
    #: Pairs realising exactly complementary functions.
    complement_pairs: tuple[tuple[str, str], ...]
    #: Dependencies whose target's value never depends on the regulator.
    absorbed_edges: tuple[tuple[str, str], ...]
    #: Inhibitions that never suppress anything: pinning the inhibitor OFF
    #: leaves the target unchanged in every enumerated state, so the veto is
    #: already implied by the rest of the rule.
    never_binding_inhibitions: tuple[tuple[str, str], ...]
    #: Nodes carrying an activated row in config/observation_model_map.tsv.
    measured: tuple[str, ...]
    distinct_function_count: int
    enumerated_states: int
    #: Compartment class per node, from the model's own dictionary.
    compartment_of: dict[str, str]

    @property
    def derived(self) -> tuple[str, ...]:
        free = set(self.free)
        return tuple(n for n in self.node_ids if n not in free)


def _topological_order(rules: dict[str, str], free: set[str]) -> list[str]:
    dependencies = derive_dependencies(rules)
    parents: dict[str, set[str]] = {n: set() for n in rules}
    for source, target in dependencies:
        parents[target].add(source)
    remaining = [n for n in rules if n not in free]
    order: list[str] = []
    resolved = set(free)
    while remaining:
        progressed = False
        for node_id in list(remaining):
            if parents[node_id] <= resolved:
                order.append(node_id)
                resolved.add(node_id)
                remaining.remove(node_id)
                progressed = True
        if not progressed:
            raise ValueError(
                f"network is not a DAG over its free variables; unresolved: "
                f"{sorted(remaining)}"
            )
    return order


def _as_bitwise(logic: str) -> str:
    """Rewrite a Boolean rule into a bitwise expression over state columns.

    Each node's value across every enumerated assignment is one Python int used
    as a bit column, so one whole-network evaluation is a few dozen bigint
    operations rather than a loop over hundreds of thousands of states. The
    substitution is safe because Python's bitwise precedence (``~`` > ``&`` >
    ``|``) mirrors its Boolean precedence (``not`` > ``and`` > ``or``), so the
    parse tree is unchanged. ``~`` yields negative ints, which behave correctly
    under further bitwise operations; the caller masks the final result.
    """
    return logic.replace(" and ", " & ").replace(" or ", " | ").replace("not ", "~")


def _columns(
    rules: dict[str, str],
    order: list[str],
    seeds: dict[str, int],
    mask: int,
) -> dict[str, int]:
    """Evaluate every node's bit column from the given free-variable columns."""
    columns = dict(seeds)
    for node_id in order:
        if node_id in columns:
            continue
        columns[node_id] = eval(_as_bitwise(rules[node_id]), {}, columns) & mask
    return columns


def load_structure(model_version: str, root: Path | None = None) -> StructuralFacts:
    """Derive every structural fact a static figure may assert.

    Exhaustive over all assignments of the free variables, so the inert set and
    the alias classes are exact. Raises rather than sampling if the space is too
    large -- a sampled claim must not be presented in a figure that reads as
    definitive.
    """
    spec = resolve_model(model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    node_ids = tuple(rules)
    free = tuple(n for n in node_ids if rules[n].strip() == n)
    states = 2 ** len(free)
    if states > MAX_ENUMERATION_STATES:
        raise ValueError(
            f"{model_version} has {len(free)} free variables ({states} states), "
            f"above the {MAX_ENUMERATION_STATES} exhaustive limit. A sampled "
            "result must not be published as a structural fact."
        )

    order = _topological_order(rules, set(free))
    dependencies = derive_dependencies(rules)
    outputs = tuple(n for n in node_ids if n.startswith(OUTPUT_PREFIX))
    mask = (1 << states) - 1

    # Column i of free variable k alternates every 2**k states, so the seeds are
    # the standard truth-table columns.
    seeds: dict[str, int] = {}
    for index, node_id in enumerate(free):
        block = 1 << index
        column = 0
        for start in range(block, states, block * 2):
            column |= ((1 << block) - 1) << start
        seeds[node_id] = column

    baseline = _columns(rules, order, seeds, mask)
    out_signature = tuple(baseline[out] for out in outputs)

    phenotype_inert: list[str] = []
    for node_id in node_ids:
        if node_id in outputs:
            continue
        unchanged = True
        for value in (0, mask):
            pinned = dict(seeds)
            pinned[node_id] = value
            columns = _columns(rules, order, pinned, mask)
            if tuple(columns[out] for out in outputs) != out_signature:
                unchanged = False
                break
        if unchanged:
            phenotype_inert.append(node_id)

    absorbed: list[tuple[str, str]] = []
    never_binding: list[tuple[str, str]] = []
    for (source, target), sign in sorted(dependencies.items()):
        pinned_targets = []
        for value in (0, mask):
            pinned = dict(seeds)
            pinned[source] = value
            pinned_targets.append(_columns(rules, order, pinned, mask)[target])
        if pinned_targets[0] == pinned_targets[1]:
            absorbed.append((source, target))
        # An inhibition that suppresses nothing: removing it (pinning the
        # inhibitor OFF) leaves the target identical everywhere, so the rest of
        # the rule already implies the veto. X_ANTIADHESIVE_ROUTE inhibiting
        # OUT_MATERNAL_ADHESION_COMPETENCE is the clearest case -- competence
        # requires E_RECEPTIVE_SURFACE, which already requires the negation of
        # every disjunct of that route.
        if sign == "inhibition" and pinned_targets[0] == baseline[target]:
            never_binding.append((source, target))

    regulators = {source for source, _ in dependencies}
    unread_inputs = tuple(n for n in free if n not in regulators)

    by_signature: dict[int, list[str]] = {}
    for node_id in node_ids:
        by_signature.setdefault(baseline[node_id], []).append(node_id)
    alias_classes = tuple(
        tuple(members) for members in by_signature.values() if len(members) > 1
    )
    complement_pairs = tuple(
        sorted(
            {
                tuple(sorted((node_id, by_signature[inverted][0])))
                for node_id in node_ids
                if (inverted := baseline[node_id] ^ mask) in by_signature
            }
        )
    )

    observation_rows = load_observation_map(root)
    measured = tuple(
        node_id
        for row in observation_rows
        if row["activation_status"] in EVALUABLE_ACTIVATION_STATUSES
        for node_id in row["model_nodes"].split(";")
        if node_id in rules
    )

    visualization = load_visualization_config(root)
    compartment_of = {
        row["node_id"]: classify_node(
            row["node_id"], row.get("compartment", ""), visualization
        )
        for row in load_tsv(spec.node_dictionary)
        if row["node_id"] in rules
    }

    parents: dict[str, set[str]] = {n: set() for n in rules}
    for source, target in dependencies:
        parents[target].add(source)
    depth: dict[str, int] = dict.fromkeys(free, 0)
    for node_id in order:
        depth[node_id] = 1 + max((depth[p] for p in parents[node_id]), default=-1)

    return StructuralFacts(
        model_version=spec.model_version,
        node_ids=node_ids,
        rules=dict(rules),
        free=free,
        depth=depth,
        edges=tuple(
            (source, target, sign)
            for (source, target), sign in sorted(dependencies.items())
        ),
        outputs=outputs,
        phenotype_inert=tuple(phenotype_inert),
        unread_inputs=unread_inputs,
        alias_classes=alias_classes,
        complement_pairs=complement_pairs,
        absorbed_edges=tuple(absorbed),
        never_binding_inhibitions=tuple(never_binding),
        measured=measured,
        distinct_function_count=len(by_signature),
        enumerated_states=states,
        compartment_of=compartment_of,
    )


def structural_summary(facts: StructuralFacts) -> dict[str, Any]:
    """The figures' caption numbers, in one auditable place."""
    return {
        "model_version": facts.model_version,
        "nodes": len(facts.node_ids),
        "dependencies": len(facts.edges),
        "free_variables": len(facts.free),
        "derived_nodes": len(facts.derived),
        "max_depth": max(facts.depth.values()),
        "distinct_functions": facts.distinct_function_count,
        "phenotype_inert_nodes": len(facts.phenotype_inert),
        "unread_inputs": len(facts.unread_inputs),
        "alias_classes": len(facts.alias_classes),
        "absorbed_dependencies": len(facts.absorbed_edges),
        "never_binding_inhibitions": len(facts.never_binding_inhibitions),
        "measured_nodes": len(facts.measured),
        "enumerated_states": facts.enumerated_states,
    }
