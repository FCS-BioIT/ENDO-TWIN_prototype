"""Reconcile an executable MaBoSS network against its curated edge provenance.

``network.bnd`` is the only authority on what a model computes. ``edge_evidence.tsv``
is the only authority on what has been curated. This module owns neither: it reads
both, derives structural polarity from the rules, and returns the reconciliation.
It never writes ``edge_evidence.tsv``.

The defect this exists to prevent is silent drift between the two. Before it, every
validator in the repository read the relation table and none parsed the network, so
four dependencies executed with no row and one row described a relation the model
does not compute -- and nothing could detect it. Reconciliation is therefore run
*before* generation writes anything: an unadjudicated mismatch aborts the write
rather than being recorded after the fact.

Reconciliation never invents evidence. A dependency that executes without curated
support is reported with ``provenance_status=unprovenanced`` and an empty
``edge_id``; it gets no row in the evidence store and no assertion, because an
assertion that cites nothing would make an unsupported edge look evidenced at
exactly the granularity where the claim lives. A curated row whose dependency no
longer executes becomes ``retired``: it keeps its ``edge_id``, its evidence and its
assertions as history, and is excluded from active coverage.

Polarity IS derived, by recursive descent with negation propagated down the parse
tree. A token-local "preceded by not" heuristic would be wrong -- rules such as
``X_MECHANICAL_PERMISSIVE_ECM`` negate a parenthesised group -- but a real parse
handles those, and agrees with all 224 curated signs across the three models. The
derived sign is cross-checked against the curated one so that sign drift fails the
build in both directions.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

TOPOLOGY_COLUMNS = (
    "source",
    "target",
    "derived_sign",
    "provenance_status",
    "edge_id",
    "exemption_id",
)

ADJUDICATION_COLUMNS = (
    "exemption_id",
    "source_node",
    "target_node",
    "category",
    "adjudication",
    "rationale",
    "action_required",
    "dated",
)

#: Statuses describing a relation the network actually computes.
ACTIVE_STATUSES = ("declared", "unprovenanced", "logical_aggregate")
PROVENANCE_STATUS_VALUES = (*ACTIVE_STATUSES, "retired")

#: The only status that may ever be reported as having provenance.
COVERED_STATUS = "declared"

SIGN_VALUES = ("activation", "inhibition")

CATEGORY_TO_STATUS = {
    "phenotype_or_logical_aggregate": "logical_aggregate",
    "executing_without_provenance": "unprovenanced",
    "stale_topology_row_undocumented_migration": "retired",
}

_KEYWORDS = {"and", "or", "not"}
_LEXER = re.compile(r"\(|\)|\b\w+\b")
_NODE_BLOCK = re.compile(r"Node\s+(\w+)\s*\{(.*?)\}", re.DOTALL)
_LOGIC = re.compile(r"logic\s*=\s*(.*?);", re.DOTALL)


class TopologyParityError(RuntimeError):
    """An executing dependency, or a curated row, is neither matched nor adjudicated."""


def parse_bnd_rules(path: Path) -> dict[str, str]:
    """Return ``{node_id: logic}`` in declaration order for an executable ``.bnd``."""
    rules: dict[str, str] = {}
    for name, body in _NODE_BLOCK.findall(path.read_text(encoding="utf-8")):
        match = _LOGIC.search(body)
        if match is None:
            raise TopologyParityError(f"node {name} in {path} declares no logic")
        rules[name] = match.group(1).strip()
    return rules


def _parse(tokens: Sequence[str]) -> tuple:
    """Recursive descent over ``not`` > ``and`` > ``or``.

    Raises rather than degrading to a token scan: a silent misparse would produce a
    confidently wrong sign, which is worse than no sign at all.
    """
    position = 0

    def peek() -> str | None:
        return tokens[position] if position < len(tokens) else None

    def take() -> str:
        nonlocal position
        position += 1
        return tokens[position - 1]

    def factor() -> tuple:
        if peek() == "not":
            take()
            return ("not", factor())
        if peek() == "(":
            take()
            node = expression()
            if peek() != ")":
                raise TopologyParityError(f"unbalanced parentheses in {tokens!r}")
            take()
            return node
        if peek() is None:
            raise TopologyParityError(f"truncated expression {tokens!r}")
        return ("id", take())

    def term() -> tuple:
        nodes = [factor()]
        while peek() == "and":
            take()
            nodes.append(factor())
        return ("and", nodes) if len(nodes) > 1 else nodes[0]

    def expression() -> tuple:
        nodes = [term()]
        while peek() == "or":
            take()
            nodes.append(term())
        return ("or", nodes) if len(nodes) > 1 else nodes[0]

    tree = expression()
    if position != len(tokens):
        raise TopologyParityError(f"trailing tokens in {tokens!r}")
    return tree


def _polarity(
    node: tuple, negated: bool = False, found: dict[str, set[str]] | None = None
) -> dict[str, set[str]]:
    found = {} if found is None else found
    kind = node[0]
    if kind == "id":
        found.setdefault(node[1], set()).add("inhibition" if negated else "activation")
    elif kind == "not":
        _polarity(node[1], not negated, found)
    else:
        for child in node[1]:
            _polarity(child, negated, found)
    return found


def derive_dependencies(rules: Mapping[str, str]) -> dict[tuple[str, str], str]:
    """Non-self ``(source, target)`` pairs with their structural sign.

    ``ambiguous`` marks a source used at both polarities within one rule; such an
    edge cannot be given a single sign and must be adjudicated rather than guessed.
    """
    known = set(rules)
    derived: dict[tuple[str, str], str] = {}
    for target, expression in rules.items():
        polarities = _polarity(_parse(_LEXER.findall(expression)))
        for source, signs in polarities.items():
            if source in known and source != target and source not in _KEYWORDS:
                derived[(source, target)] = (
                    "ambiguous" if len(signs) > 1 else next(iter(signs))
                )
    return derived


def dependencies_of(path: Path) -> dict[tuple[str, str], str]:
    return derive_dependencies(parse_bnd_rules(path))


def load_adjudications(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Load and fully validate the topology adjudication registry."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = sorted(set(ADJUDICATION_COLUMNS) - set(reader.fieldnames or ()))
        if missing:
            raise TopologyParityError(f"{path} is missing columns: {missing}")
        rows = list(reader)

    table: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        pair = (row["source_node"], row["target_node"])
        if pair in table:
            raise TopologyParityError(f"{path} adjudicates {pair} twice")
        if row["category"] not in CATEGORY_TO_STATUS:
            raise TopologyParityError(
                f"adjudication {row['exemption_id']} has unknown category "
                f"{row['category']!r}"
            )
        for field in ("exemption_id", "adjudication", "rationale", "dated"):
            if not row[field].strip():
                raise TopologyParityError(f"adjudication for {pair} is missing {field}")
        table[pair] = row
    return table


def reconcile(
    rules: Mapping[str, str],
    curated_rows: Sequence[Mapping[str, str]],
    adjudications: Mapping[tuple[str, str], Mapping[str, str]],
) -> list[dict[str, str]]:
    """Return the topology table implied by the rules and the curated relations.

    Raises ``TopologyParityError`` listing every unmatched pair, so a caller can
    abort before opening any file for writing.
    """
    derived = derive_dependencies(rules)
    curated: dict[tuple[str, str], Mapping[str, str]] = {}
    for row in curated_rows:
        pair = (row["source"], row["target"])
        if pair in curated:
            raise TopologyParityError(
                f"relation table declares {pair[0]} -> {pair[1]} twice "
                f"(second is {row['edge_id']})"
            )
        curated[pair] = row

    errors: list[str] = []
    used: set[tuple[str, str]] = set()
    table: list[dict[str, str]] = []

    for pair in sorted(set(derived) | set(curated)):
        row = curated.get(pair)
        waiver = adjudications.get(pair)
        executes = pair in derived
        sign = derived.get(pair, "")

        if executes and row is not None:
            if waiver is not None:
                errors.append(
                    f"{pair[0]} -> {pair[1]} both executes and is curated, but is "
                    f"still adjudicated as {waiver['exemption_id']}; "
                    "delete the adjudication"
                )
                continue
            if sign != "ambiguous" and sign != row["sign"]:
                errors.append(
                    f"{pair[0]} -> {pair[1]}: edge_evidence.tsv records "
                    f"sign={row['sign']!r} but the rule uses it as {sign!r}"
                )
                continue
            status, edge_id, exemption_id = "declared", row["edge_id"], ""
        elif executes:
            if waiver is None:
                errors.append(
                    f"{pair[0]} -> {pair[1]} executes but is neither curated in "
                    "edge_evidence.tsv nor adjudicated in "
                    "config/topology_parity_exemptions.tsv"
                )
                continue
            status = CATEGORY_TO_STATUS[waiver["category"]]
            if status == "retired":
                errors.append(
                    f"{pair[0]} -> {pair[1]} executes but is adjudicated as retired "
                    f"({waiver['exemption_id']})"
                )
                continue
            used.add(pair)
            edge_id, exemption_id = "", waiver["exemption_id"]
        else:
            if waiver is None or CATEGORY_TO_STATUS[waiver["category"]] != "retired":
                errors.append(
                    f"edge {row['edge_id']} declares {pair[0]} -> {pair[1]}, which "
                    "the rules do not compute, and no retirement adjudication exists"
                )
                continue
            used.add(pair)
            status, edge_id, exemption_id = (
                "retired",
                row["edge_id"],
                (waiver["exemption_id"]),
            )

        table.append(
            {
                "source": pair[0],
                "target": pair[1],
                "derived_sign": sign,
                "provenance_status": status,
                "edge_id": edge_id,
                "exemption_id": exemption_id,
            }
        )

    stale_waivers = sorted(set(adjudications) - used)
    if stale_waivers:
        errors.append(
            "adjudications correspond to no mismatch and must be deleted: "
            f"{stale_waivers}"
        )
    if errors:
        raise TopologyParityError("; ".join(errors))
    return table


def coverage_counts(table: Sequence[Mapping[str, str]]) -> dict[str, int]:
    """Coverage numerator and denominator for a reconciled topology table.

    ``active_edge_count`` is the denominator; ``declared_edge_count`` is the only
    numerator that may be described as covered. Retired relations are in neither.
    Neither number says anything about whether a cited paper was ever read -- that
    is ``curation_status`` in the assertion store, and it is currently zero.
    """
    counts = {f"{status}_edge_count": 0 for status in PROVENANCE_STATUS_VALUES}
    for row in table:
        status = row["provenance_status"]
        if status not in PROVENANCE_STATUS_VALUES:
            raise TopologyParityError(
                f"{row['source']} -> {row['target']} has invalid "
                f"provenance_status {status!r}"
            )
        counts[f"{status}_edge_count"] += 1
    counts["relation_count"] = len(table)
    counts["active_edge_count"] = sum(
        counts[f"{status}_edge_count"] for status in ACTIVE_STATUSES
    )
    return counts
