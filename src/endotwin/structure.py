"""Exact structural facts about a Boolean network, by exhaustive enumeration.

The ENDO-TWIN network is acyclic over its free variables (the experimental
inputs), so every assignment of the inputs has exactly one fixed point, and
enumerating all ``2**k`` input assignments is exact rather than sampled. Facts
derived here -- which nodes are exact aliases, which dependencies can never
change their target, which nodes cannot affect any functional output, and what
each condition's fixed point is -- are statements about the model, not estimates,
and they do not depend on transition rates (any positive rates converge to the
same fixed point).
"""

from __future__ import annotations

import functools
from collections.abc import Mapping
from dataclasses import dataclass

from endotwin.model import dependencies, referenced_nodes

#: Refuse rather than silently sample.
MAX_FREE_VARIABLES = 22


class NotAcyclicError(ValueError):
    pass


def free_variables(rules: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(n for n, logic in rules.items() if logic.strip() == n)


def _parents(rules: Mapping[str, str]) -> dict[str, set[str]]:
    known = set(rules)
    return {
        n: {r for r in referenced_nodes(logic) if r in known and r != n}
        for n, logic in rules.items()
    }


def topological_order(
    rules: Mapping[str, str], fixed: set[str] | frozenset[str] = frozenset()
) -> list[str]:
    """Order of evaluation for the non-free, non-fixed nodes."""
    parents = _parents(rules)
    resolved = set(free_variables(rules)) | set(fixed)
    remaining = [n for n in rules if n not in resolved]
    order: list[str] = []
    while remaining:
        progressed = False
        for node in list(remaining):
            if parents[node] <= resolved:
                order.append(node)
                resolved.add(node)
                remaining.remove(node)
                progressed = True
        if not progressed:
            raise NotAcyclicError(f"network has a cycle among {sorted(remaining)}")
    return order


def _bitwise(logic: str) -> str:
    # Python's ~ > & > | precedence mirrors not > and > or.
    return (
        f" {logic} ".replace(" and ", " & ").replace(" or ", " | ").replace("not ", "~")
    )


def fixed_point(
    rules: Mapping[str, str],
    inputs: Mapping[str, int],
    forced: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """The unique fixed point for given input values and pinned nodes.

    Free variables not named in ``inputs`` are 0. ``forced`` pins nodes (a
    knockdown is 0), which is the asymptotic effect of
    :func:`endotwin.model.render_bnd` interventions.
    """
    forced = dict(forced or {})
    state = {n: int(bool(inputs.get(n, 0))) for n in free_variables(rules)}
    unknown = set(inputs) - set(state)
    if unknown:
        raise KeyError(f"not free variables of this network: {sorted(unknown)}")
    state.update(forced)
    for node in topological_order(rules, set(forced)):
        state[node] = int(eval(_bitwise(rules[node]), {"__builtins__": {}}, state)) & 1
    return state


@functools.lru_cache(maxsize=8)
def _input_columns(k: int) -> tuple[int, ...]:
    """Bit columns of the k free variables: bit j of column i is bit i of j.

    Built in closed form (a block of 2**i zeros then 2**i ones, repeated) so the
    cost does not grow with the 2**k assignments.
    """
    count = 1 << k
    total = (1 << count) - 1
    out = []
    for i in range(k):
        half = 1 << i
        block = ((1 << half) - 1) << half
        period = (1 << (2 * half)) - 1
        out.append(block * (total // period))
    return tuple(out)


@dataclass(frozen=True)
class Columns:
    free: tuple[str, ...]
    mask: int
    values: dict[str, int]


def columns(
    rules: Mapping[str, str], forced: Mapping[str, int] | None = None
) -> Columns:
    """Each node's value across all ``2**k`` free-variable assignments, as bits."""
    free = free_variables(rules)
    if len(free) > MAX_FREE_VARIABLES:
        raise ValueError(f"{len(free)} free variables exceed the enumeration cap")
    count = 1 << len(free)
    mask = (1 << count) - 1
    values: dict[str, int] = {
        n: c for n, c in zip(free, _input_columns(len(free)), strict=True)
    }
    forced = dict(forced or {})
    for node, state in forced.items():
        values[node] = mask if state else 0
    for node in topological_order(rules, set(forced)):
        values[node] = eval(_bitwise(rules[node]), {"__builtins__": {}}, values) & mask
    return Columns(free=free, mask=mask, values=values)


@dataclass(frozen=True)
class StructuralSummary:
    nodes: int
    free_variables: tuple[str, ...]
    dependencies: int
    activations: int
    inhibitions: int
    distinct_functions: int
    alias_classes: tuple[tuple[str, ...], ...]
    absorbed_dependencies: tuple[tuple[str, str], ...]
    never_binding_inhibitions: tuple[tuple[str, str], ...]
    phenotype_inert_nodes: tuple[str, ...]
    #: Nodes that cannot change any functional output or any other node with a
    #: planned readout (for example S_BMP_SMAD, read as pSMAD1/5/8).
    readout_inert_nodes: tuple[str, ...]
    unread_inputs: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "nodes": self.nodes,
            "free_variables": list(self.free_variables),
            "dependencies": self.dependencies,
            "activations": self.activations,
            "inhibitions": self.inhibitions,
            "distinct_functions": self.distinct_functions,
            "alias_classes": [list(c) for c in self.alias_classes],
            "absorbed_dependencies": [list(d) for d in self.absorbed_dependencies],
            "never_binding_inhibitions": [
                list(d) for d in self.never_binding_inhibitions
            ],
            "absorbed_or_never_binding": len(
                set(self.absorbed_dependencies) | set(self.never_binding_inhibitions)
            ),
            "phenotype_inert_nodes": list(self.phenotype_inert_nodes),
            "readout_inert_nodes": list(self.readout_inert_nodes),
            "unread_inputs": list(self.unread_inputs),
        }


def _inert(
    rules: Mapping[str, str], cols: Columns, targets: tuple[str, ...]
) -> list[str]:
    inert: list[str] = []
    for node in rules:
        if node in targets:
            continue
        if all(
            all(
                columns(rules, {node: state}).values[t] == cols.values[t]
                for t in targets
            )
            for state in (0, 1)
        ):
            inert.append(node)
    return inert


def summarize(
    rules: Mapping[str, str],
    outputs: tuple[str, ...],
    readouts: tuple[str, ...] = (),
) -> StructuralSummary:
    cols = columns(rules)
    deps = dependencies(rules)
    groups: dict[int, list[str]] = {}
    for node in rules:
        groups.setdefault(cols.values[node], []).append(node)
    aliases = tuple(tuple(g) for g in groups.values() if len(g) > 1)

    # Definitions shared with the prototype's structural report, so counts
    # are comparable across the two projects. A dependency is *absorbed* when
    # pinning its source to 0 and to 1 (propagated through every path) leaves
    # the target identical over all input assignments. An inhibition *never
    # binds* when pinning the inhibitor OFF leaves the target unchanged.
    absorbed: list[tuple[str, str]] = []
    never_binding: list[tuple[str, str]] = []
    for (source, target), sign in sorted(deps.items()):
        pinned = [columns(rules, {source: state}).values[target] for state in (0, 1)]
        if pinned[0] == pinned[1]:
            absorbed.append((source, target))
        if sign == "inhibition" and pinned[0] == cols.values[target]:
            never_binding.append((source, target))

    inert = _inert(rules, cols, outputs)
    readout_inert = _inert(rules, cols, tuple(dict.fromkeys(outputs + readouts)))

    read = {source for source, _ in deps}
    return StructuralSummary(
        nodes=len(rules),
        free_variables=cols.free,
        dependencies=len(deps),
        activations=sum(1 for s in deps.values() if s == "activation"),
        inhibitions=sum(1 for s in deps.values() if s == "inhibition"),
        distinct_functions=len(groups),
        alias_classes=aliases,
        absorbed_dependencies=tuple(absorbed),
        never_binding_inhibitions=tuple(never_binding),
        phenotype_inert_nodes=tuple(inert),
        readout_inert_nodes=tuple(readout_inert),
        unread_inputs=tuple(n for n in cols.free if n not in read),
    )
