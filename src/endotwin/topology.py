"""Parse MaBoSS ``.bnd`` rules and derive their signed dependencies.

A copy of the two topology helpers the mainline needs, kept here so that the
ENDO-TWIN package does not depend on the legacy prototype package. The legacy
copy stays unchanged because closed records pin its digest; the two are checked
to agree on every model file in ``tests/unit/test_endotwin_topology_parity.py``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path

_KEYWORDS = {"and", "or", "not"}
_LEXER = re.compile(r"\(|\)|\b\w+\b")
_NODE_BLOCK = re.compile(r"Node\s+(\w+)\s*\{(.*?)\}", re.DOTALL)
_LOGIC = re.compile(r"logic\s*=\s*(.*?);", re.DOTALL)


class TopologyError(RuntimeError):
    """A rule cannot be parsed into a unique signed dependency set."""


def parse_bnd_rules(path: Path) -> dict[str, str]:
    """Return ``{node_id: logic}`` in declaration order for an executable ``.bnd``."""
    rules: dict[str, str] = {}
    for name, body in _NODE_BLOCK.findall(path.read_text(encoding="utf-8")):
        match = _LOGIC.search(body)
        if match is None:
            raise TopologyError(f"node {name} in {path} declares no logic")
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
                raise TopologyError(f"unbalanced parentheses in {tokens!r}")
            take()
            return node
        if peek() is None:
            raise TopologyError(f"truncated expression {tokens!r}")
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
        raise TopologyError(f"trailing tokens in {tokens!r}")
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
