"""Regenerate Appendix A of the node-support pre-registration from `network.bnd`.

WHAT THIS IS FOR. The pre-registration claims a v0.4 expected CNT->HT direction
for every RNA-assessable node, fixed before any expression value was read. A
claim like that is only worth something if a reviewer can recompute it, so this
module does, from the committed network and the committed observation map and
nothing else.

WHAT IT READS. `network.bnd` and `config/scrna_observation_map.tsv`. No single-
cell object, no per-cell table, no expression value of any kind, and no model
output -- the leakage boundary of `docs/scrna/node_support_preregistration.md`
Section 10 applies here too and the test suite asserts it.

THE RELAY SETTING. Appendix A holds the four interface relays FALSE. That is a
declared evaluation choice and NOT their `baseline.cfg` value -- the file gives
them mixed initial probabilities, which a deterministic fixed point cannot
represent. `relay_invariance()` recomputes the table under all sixteen settings
and `expectation_table()` refuses to emit one if any audited node moves.

THE CNT AMBIGUITY. The repository does not record whether the scRNA control arm
is unstimulated or E2-primed-only. Both encodings are computed and compared
rather than one being guessed; among the 45 non-input nodes they differ for
exactly one, `E_ESTROGENIC_PROLIFERATION`, which is in no alias class. That
invariance is the reason the audit's calls do not depend on resolving it, and
`disagreements()` recomputes it rather than restating it.
"""

from __future__ import annotations

import csv
import re
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BND = REPO / "models/superset/adoc-literature-superset-v0.4.0/network.bnd"
MAP = REPO / "config/scrna_observation_map.tsv"

#: `E_KLF12_HIGH` held FALSE. This one IS its `baseline.cfg` value
#: (`E_KLF12_HIGH.istate = FALSE;`), and the KLF12 unit established that these
#: data do not justify replacing it with a measured prior.
KLF12_FREE_VARIABLE: dict[str, bool] = {"E_KLF12_HIGH": False}

#: The four interface relays, held FALSE as a DECLARED EVALUATION CHOICE and
#: NOT as their `baseline.cfg` values. `baseline.cfg` gives them mixed initial
#: probabilities -- SPP1 0.70 ON, REDUNDANT 0.40, MECHANICAL_STRESS 0.30,
#: ANTIADHESIVE 0.20 -- which a deterministic fixed point cannot represent. An
#: earlier revision of this module and of Appendix A called them FALSE in
#: `baseline.cfg`; that was false about the file. The choice is harmless, and
#: `relay_invariance()` PROVES it over all 2**4 settings rather than asserting
#: it, because no rule of any audited node names a relay.
RELAYS: tuple[str, ...] = (
    "X_MECHANICAL_STRESS_RELAY",
    "X_INTERFACE_SPP1_RELAY",
    "X_INTERFACE_REDUNDANT_RELAY",
    "X_INTERFACE_ANTIADHESIVE_RELAY",
)

#: The declared setting the committed table is computed under.
FREE_VARIABLES: dict[str, bool] = KLF12_FREE_VARIABLE | dict.fromkeys(RELAYS, False)

#: The deposited HT arm, from `conditions/hormone_treated_maternal.cfg`. The
#: four agents are set together and the design has no single-agent arm, so no
#: effect may be attributed to any one of them (`config/protocols.yaml`).
HT_INPUTS: tuple[str, ...] = ("IN_E2", "IN_PROGESTIN", "IN_cAMP", "IN_XAV939")

#: The two candidate encodings of the CNT arm. Not a choice -- both are carried.
CNT_ENCODINGS: dict[str, tuple[str, ...]] = {
    "unstimulated": (),
    "e2_primed_only": ("IN_E2",),
}

#: The alias classes, in the order the audit tests them. AC05 is measured for
#: node support but not alias-tested; see the pre-registration Section 5.5.
CLASS_ORDER: tuple[str, ...] = ("AC03", "AC02", "AC04", "AC01", "AC05")


class ExpectationError(RuntimeError):
    """The expectation table cannot be computed from what was given."""


def load_rules(bnd: Path = BND) -> dict[str, str]:
    rules = dict(
        re.findall(
            r"Node\s+(\w+)\s*\{\s*logic\s*=\s*(.*?);\s*\}", bnd.read_text(), re.DOTALL
        )
    )
    if not rules:
        raise ExpectationError(f"no node declarations parsed from {bnd}")
    return rules


def _evaluate(expression: str, state: dict[str, bool]) -> bool:
    """Evaluate one MaBoSS Boolean logic expression under `state`.

    MaBoSS `and`/`or`/`not` are Python's, so the expression evaluates directly
    once the tokens are spaced. Nothing but node names is bound, and there are
    no builtins, so a malformed rule raises rather than reaching anything.
    """
    spaced = re.sub(r"\b(and|or|not)\b", r" \1 ", expression)
    return bool(eval(spaced, {"__builtins__": {}}, dict(state)))


def fixed_point(rules: dict[str, str], pinned: dict[str, bool]) -> dict[str, bool]:
    """Iterate synchronously from all-OFF with `pinned` held fixed.

    v0.4's dependency graph is acyclic apart from the `logic = self` free
    variables, which are pinned, so this converges to the unique attractor and
    the iteration cap is a guard rather than a truncation.
    """
    state = {node: False for node in rules} | pinned
    for _ in range(200):
        nxt = {
            n: (pinned[n] if n in pinned else _evaluate(rules[n], state)) for n in rules
        }
        if nxt == state:
            return state
        state = nxt
    raise ExpectationError("no fixed point within 200 synchronous rounds")


def _inputs(
    rules: dict[str, str],
    active: tuple[str, ...],
    free: dict[str, bool] | None = None,
) -> dict[str, bool]:
    pinned = {n: False for n in rules if n.startswith("IN_")} | dict(
        FREE_VARIABLES if free is None else free
    )
    for node in active:
        if node not in pinned:
            raise ExpectationError(f"{node} is not an input of this model")
        pinned[node] = True
    return pinned


def states(
    rules: dict[str, str], free: dict[str, bool] | None = None
) -> dict[str, dict[str, bool]]:
    """The attractor under HT and under each candidate CNT encoding."""
    resolved = {"HT": fixed_point(rules, _inputs(rules, HT_INPUTS, free))}
    for name, active in CNT_ENCODINGS.items():
        resolved[name] = fixed_point(rules, _inputs(rules, active, free))
    return resolved


def _directions(rules: dict[str, str], free: dict[str, bool]) -> dict[str, str]:
    """Every non-input node's expected CNT->HT direction under one free setting.

    The CNT arm is taken as `e2_primed_only`, which is what the committed table
    reports; `disagreements()` separately establishes which nodes that choice
    can reach at all.
    """
    resolved = states(rules, free)
    ht = resolved["HT"]
    return {
        node: direction(resolved["e2_primed_only"][node], ht[node])
        for node in rules
        if not node.startswith("IN_")
    }


def relay_invariance(rules: dict[str, str]) -> dict[str, set[str]]:
    """Non-input nodes whose expected direction depends on the relay setting.

    Appendix A pins the four interface relays FALSE, which is NOT what
    `baseline.cfg` says (it gives them mixed initial probabilities). That is a
    declared choice, and a declared choice that changed an expectation would be
    a hidden assumption. So the whole table is recomputed under all sixteen
    settings and the nodes that move are returned.

    The result is NOT empty, which is why this is computed. Four nodes move --
    the three adhesion-route nodes and `OUT_MATERNAL_ADHESION_COMPETENCE` -- and
    all four are `not_observable`, so none is audited. `expectation_table()`
    checks the intersection with the assessable set rather than emptiness.
    """
    seen: dict[str, set[str]] = {}
    for bits in product((False, True), repeat=len(RELAYS)):
        free = KLF12_FREE_VARIABLE | dict(zip(RELAYS, bits))
        for node, arrow in _directions(rules, free).items():
            seen.setdefault(node, set()).add(arrow)
    return {node: arrows for node, arrows in seen.items() if len(arrows) > 1}


def direction(before: bool, after: bool) -> str:
    if before == after:
        return "no change"
    return "OFF -> ON" if after else "ON -> OFF"


def disagreements(rules: dict[str, str]) -> list[str]:
    """Non-input nodes whose expected direction depends on the CNT encoding.

    Recomputed rather than asserted: the pre-registration's claim that the audit
    does not depend on resolving the CNT arm is only as good as this list.
    """
    resolved = states(rules)
    ht = resolved["HT"]
    names = list(CNT_ENCODINGS)
    return [
        node
        for node in rules
        if not node.startswith("IN_")
        and len({direction(resolved[n][node], ht[node]) for n in names}) > 1
    ]


def rna_assessable_rows(map_path: Path = MAP) -> list[dict[str, str]]:
    with map_path.open(newline="") as handle:
        rows = [
            r
            for r in csv.DictReader(handle, delimiter="\t")
            if r["measurement_observability"] != "not_observable"
        ]
    rows.sort(
        key=lambda r: (
            CLASS_ORDER.index(r["v04_function_class"])
            if r["v04_function_class"] in CLASS_ORDER
            else len(CLASS_ORDER),
            r["model_node"],
        )
    )
    return rows


def expectation_table() -> list[dict[str, str]]:
    rules = load_rules()
    moved = relay_invariance(rules)
    assessable = {r["model_node"] for r in rna_assessable_rows()}
    if moved.keys() & assessable:
        raise ExpectationError(
            "the committed relay setting changes an audited expectation: "
            f"{sorted(moved.keys() & assessable)}. Appendix A pins the relays "
            "FALSE as a declared choice, which is only admissible while no "
            "audited node depends on it."
        )
    resolved = states(rules)
    ht = resolved["HT"]
    table = []
    for row in rna_assessable_rows():
        node = row["model_node"]
        if node not in rules:
            raise ExpectationError(
                f"{node} is in the observation map but not in network.bnd"
            )
        per_encoding = {
            n: direction(resolved[n][node], ht[node]) for n in CNT_ENCODINGS
        }
        table.append(
            {
                "model_node": node,
                "v04_function_class": row["v04_function_class"],
                "compartment": row["compartment"],
                "measurement_observability": row["measurement_observability"],
                "expected_cnt_to_ht": per_encoding["e2_primed_only"],
                "encoding_dependent": str(len(set(per_encoding.values())) > 1).lower(),
            }
        )
    return table


def main() -> None:
    rules = load_rules()
    dependent = disagreements(rules)
    print(
        f"non-input nodes whose direction depends on the CNT encoding: {dependent or 'none'}"
    )
    moved = relay_invariance(rules)
    print(
        "non-input nodes whose direction depends on the interface-relay setting "
        f"(all 2**{len(RELAYS)} checked): {sorted(moved) or 'none'}"
    )
    print()
    header = (
        f"{'class':<7}{'node':<22}{'compartment':<13}{'expected CNT->HT':<18}enc-dep"
    )
    print(header)
    print("-" * len(header))
    for row in expectation_table():
        print(
            f"{row['v04_function_class']:<7}{row['model_node']:<22}"
            f"{row['compartment']:<13}{row['expected_cnt_to_ht']:<18}"
            f"{row['encoding_dependent']}"
        )


if __name__ == "__main__":
    main()
