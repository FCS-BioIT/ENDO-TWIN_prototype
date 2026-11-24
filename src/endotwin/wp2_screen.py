"""Exhaustive single-perturbation screen for WP2 candidate selection.

The point is to stop the candidate set being whatever was thought of first. It
enumerates **every** single-node perturbation the network can express — each
internal node pinned ON and pinned OFF — under each regimen, across **every**
rule-variant scenario, and reports what each one does to the functional
readouts the funded plan measures.

It is exact, not simulated. The network is acyclic, so each input assignment has
one fixed point, computed by :func:`endotwin.structure.fixed_point`. Fixed
points are therefore independent of transition rates and of initial conditions
by construction, which is why this screen can speak to two of v10's three
robustness requirements without sampling anything. The third — robustness to
uncertain **rules** — is what enumerating all scenarios covers.

What the screen does NOT do, deliberately:

* it does not rank candidates or select one. Feasibility, cost, donor logistics
  and whether a perturbation is genuinely withheld are not in the model;
* it does not consider timing. Every row is a steady state, and MaBoSS time is
  not experimental time;
* it does not know which perturbations are reagent-accessible. A node being
  pinnable in a Boolean model says nothing about there being an inhibitor for
  it.

Its output is an input to the selection workflow in
``docs/wp2_prediction_selection.md``, not a decision.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from endotwin import DEFAULT_MODEL_VERSION
from endotwin.model import load_model
from endotwin.protocols import load_protocols
from endotwin.structure import fixed_point

ROOT = Path(__file__).resolve().parents[2]

#: Tissue-level readouts: what the chip can be asked to report as a FUNCTION,
#: as opposed to pathway activity or target engagement. v10 Task 2.1 requires
#: the WP2 primary prediction to be one of these.
FUNCTIONAL = (
    "OUT_STROMAL_DECIDUALIZATION",
    "OUT_EPITHELIAL_PROLIFERATION",
    "OUT_EPITHELIAL_SECRETORY",
    "X_PRL",
    "X_IGFBP1",
    "X_PAEP",
)

#: Regimens a WP2 arm could plausibly run in. Task 1.1 decides which.
REGIMENS = ("reference", "hormone_only_reference")


def _direction(control: int, perturbed: int) -> str:
    if perturbed == control:
        return "no_change"
    return "down" if perturbed < control else "up"


def screen(version: str = DEFAULT_MODEL_VERSION) -> list[dict[str, Any]]:
    model = load_model(version)
    protocols = load_protocols(model)
    scenarios = model.scenarios()
    internal = [n for n in model.nodes if n not in model.inputs]

    rows: list[dict[str, Any]] = []
    for regimen in REGIMENS:
        condition = protocols.conditions[regimen]
        inputs = condition.phases[-1].inputs
        # {(node, state, readout): {direction, ...}} over all scenarios, plus the
        # per-family split so a non-robust effect can be read as discrimination
        # rather than as noise.
        seen: dict[tuple[str, int, str], set[str]] = {}
        families: dict[tuple[str, int, str], set[str]] = {}
        for selection in scenarios:
            rules = model.rules_for(selection)
            control = fixed_point(rules, inputs)
            for node in internal:
                for state in (0, 1):
                    if control[node] == state:
                        continue  # pinning a node to the value it already has
                    perturbed = fixed_point(rules, inputs, forced={node: state})
                    for readout in FUNCTIONAL:
                        key = (node, state, readout)
                        d = _direction(control[readout], perturbed[readout])
                        seen.setdefault(key, set()).add(d)
                        if d != "no_change":
                            families.setdefault(key, set()).update(
                                f"{f}={v}" for f, v in selection.items()
                            )
        for (node, state, readout), directions in sorted(seen.items()):
            if directions == {"no_change"}:
                continue
            robust = len(directions) == 1
            rows.append(
                {
                    "regimen": regimen,
                    "perturbation": f"{node}={state}",
                    "node": node,
                    "forced_state": state,
                    "readout": readout,
                    "directions": ";".join(sorted(directions)),
                    "robust_across_scenarios": "true" if robust else "false",
                    "scenarios": len(scenarios),
                }
            )
    return rows


def write(version: str = DEFAULT_MODEL_VERSION) -> Path:
    import csv

    rows = screen(version)
    path = ROOT / "endotwin" / "results" / version / "wp2_candidate_screen.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    return path
