"""v0.5.2: which single-node clamps separate v0.5.2 from v0.5.1 at steady state.

``v052_increment.structural_identity`` shows that no node's composed function
changes over the free variables. That covers every protocol and condition,
because conditions act only through free inputs. A perturbation that clamps an
*internal* node can still break the absorption the identity rests on. This
module enumerates every such clamp exhaustively:

* every non-free node, forced ON and forced OFF, in both versions;
* the composed function of every node, over all 2**19 free-variable
  assignments.

It reports the clamps under which any node's function differs. U5b did the same
for its marker gates, as "phenotype-inert" changes.

The result is a statement about the model's answer to an intervention, not
about biology. A clamp listed here is one under which the two versions make
different steady-state predictions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting.structure import _columns, _topological_order
from dt_adoc.reporting.v052_increment import MODEL_DIR, PARENT_DIR

#: Constant rules in the repository's own rule grammar; no literal is assumed.
_CONSTANT = {0: "(IN_E2 and not IN_E2)", 1: "(IN_E2 or not IN_E2)"}


def _composed(rules: dict[str, str], free: tuple[str, ...]) -> dict[str, int]:
    states = 2 ** len(free)
    mask = (1 << states) - 1
    seeds: dict[str, int] = {}
    for index, node_id in enumerate(free):
        block = 1 << index
        column = 0
        for start in range(block, states, block * 2):
            column |= ((1 << block) - 1) << start
        seeds[node_id] = column
    return _columns(rules, _topological_order(rules, set(free)), seeds, mask)


def separating_clamps(root: Path) -> list[dict[str, Any]]:
    """Every single-node clamp under which some node's composed function differs."""
    parent = parse_bnd_rules(root / PARENT_DIR / "network.bnd")
    child = parse_bnd_rules(root / MODEL_DIR / "network.bnd")
    free = tuple(n for n in parent if parent[n].strip() == n)
    if free != tuple(n for n in child if child[n].strip() == n):
        raise ValueError("the two versions have different free variables")
    found = []
    for node in (n for n in parent if n not in free):
        for value, constant in _CONSTANT.items():
            a = _composed({**parent, node: constant}, free)
            b = _composed({**child, node: constant}, free)
            differing = sorted(n for n in a if a[n] != b[n])
            if differing:
                found.append(
                    {
                        "clamped_node": node,
                        "value": value,
                        "nodes_whose_function_differs": differing,
                        "phenotypes_that_differ": [
                            n for n in differing if n.startswith("OUT_")
                        ],
                    }
                )
    return found


OUTPUT = Path("docs/v052_paep_hand2/separating_clamps.json")


def write(root: Path) -> Path:
    """Write the exhaustive result; the unit test re-verifies each listed clamp."""
    import hashlib
    import json

    payload = {
        "artifact": "v052_separating_single_node_clamps",
        "claim_boundary": (
            "Exhaustive over every non-free node of adoc-literature-superset-v0.5.1 "
            "clamped ON and OFF, comparing each node's composed Boolean function "
            "over all free-variable assignments between v0.5.1 and v0.5.2. A listed "
            "clamp is one under which the two versions' steady-state predictions "
            "differ. It is a property of the models, not biological evidence."
        ),
        "parent_network_bnd_sha256": hashlib.sha256(
            (root / PARENT_DIR / "network.bnd").read_bytes()
        ).hexdigest(),
        "network_bnd_sha256": hashlib.sha256(
            (root / MODEL_DIR / "network.bnd").read_bytes()
        ).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "separating_clamps": separating_clamps(root),
    }
    path = root / OUTPUT
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


if __name__ == "__main__":  # pragma: no cover
    from dt_adoc.model.provenance import repo_root

    print(write(repo_root()))
