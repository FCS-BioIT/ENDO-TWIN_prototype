"""Verify the 2026-11-18 audit's fixed-point Boolean identities against the model.

The audit reported seven identities and shipped a SymPy script that proves each
one by showing ``XOR(rule, identity)`` is unsatisfiable. Reproducing a result
with the tool that produced it checks arithmetic, not the claim, so this module
re-derives the same seven from the repository's own network parser by a
different method: exhaustive enumeration.

The network is a DAG over its free variables, so every node's value across all
``2 ** len(free)`` assignments can be computed exactly -- ``structure._columns``
evaluates the whole network as a few dozen bigint operations, one bit per
assignment. Two Boolean functions over the same free variables are equal if and
only if their bit columns are equal integers. That is a decision procedure, not
a sample, and it never calls SymPy.

What an identity here does and does not mean
--------------------------------------------
Each identity is a statement about the *substituted logical function* of one
node: unroll every deterministic rule until only free variables remain, and the
node's apparent molecular detail cancels. It says nothing whatever about

* asynchronous MaBoSS trajectories, transition rates or hitting times,
* transient behaviour before a fixed point,
* a node clamped by an intervention -- clamping breaks the substitution the
  identity depends on, which is exactly why interventions can still separate
  models these identities call equal,
* whether any of the biology is true.

Algebraic redundancy is an identifiability warning: it says baseline terminal
readouts cannot distinguish these mechanisms, so an experiment that only reads
them cannot calibrate them. It is not evidence that a protein does nothing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting.structure import (
    MAX_ENUMERATION_STATES,
    _as_bitwise,
    _columns,
    _topological_order,
)

DEFAULT_MODEL_VERSION = "adoc-literature-superset-v0.6.0"

#: The seven identities as the audit stated them, transcribed verbatim into the
#: model's own rule syntax. The left side names the node; the right side is the
#: claimed substituted function. Nothing here is derived -- these are the
#: claims under test, and a transcription error must show up as a failure
#: rather than be quietly corrected.
IDENTITIES: tuple[tuple[str, str], ...] = (
    ("S_DECIDUALIZED", "IN_PROGESTIN and IN_cAMP"),
    ("S_TAZ_ECM", "IN_PROGESTIN and IN_cAMP"),
    (
        "E_RECEPTIVE_SURFACE",
        "IN_E2 and IN_PROGESTIN and not E_KLF12_HIGH",
    ),
    (
        "X_MECHANICAL_PERMISSIVE_ECM",
        (
            "IN_PROGESTIN and IN_cAMP and not (X_MECHANICAL_STRESS_RELAY and "
            "(IN_ER_STRESS_EXCESS or IN_HIGH_ECM_STIFFNESS))"
        ),
    ),
    (
        "X_ADHESION_ROUTE_SPP1",
        "IN_E2 and IN_PROGESTIN and not E_KLF12_HIGH and X_INTERFACE_SPP1_RELAY",
    ),
    (
        "X_ADHESION_ROUTE_REDUNDANT",
        "IN_E2 and IN_PROGESTIN and not E_KLF12_HIGH and X_INTERFACE_REDUNDANT_RELAY",
    ),
    (
        "OUT_STABLE_ADHESION",
        (
            "IN_E2 and IN_PROGESTIN and IN_cAMP and not E_KLF12_HIGH and "
            "IN_EMBRYO_PRESENT and IN_TROPHECTODERM_COMPETENT and "
            "IN_EMBRYO_CONTACT and (X_INTERFACE_REDUNDANT_RELAY or "
            "X_INTERFACE_SPP1_RELAY) and not (X_MECHANICAL_STRESS_RELAY and "
            "(IN_ER_STRESS_EXCESS or IN_HIGH_ECM_STIFFNESS))"
        ),
    ),
)


class IdentityError(RuntimeError):
    """An identity names something the network does not have."""


@dataclass(frozen=True)
class IdentityResult:
    node: str
    claimed: str
    holds: bool
    #: Number of free-variable assignments where node and claim disagree. Zero
    #: iff the identity holds; reported so a failure is quantified rather than
    #: merely announced.
    counterexamples: int
    #: One disagreeing assignment, as ``{free_variable: bool}``, or ``None``.
    witness: dict[str, bool] | None


@dataclass(frozen=True)
class IdentityReport:
    model_version: str
    network_sha256: str
    free: tuple[str, ...]
    enumerated_states: int
    results: tuple[IdentityResult, ...]

    @property
    def all_hold(self) -> bool:
        return all(r.holds for r in self.results)


def _network_path(model_version: str, root: Path | None = None) -> Path:
    return Path(resolve_model(model_version, root).network_bnd)


def verify_identities(
    model_version: str = DEFAULT_MODEL_VERSION,
    root: Path | None = None,
    identities: tuple[tuple[str, str], ...] = IDENTITIES,
) -> IdentityReport:
    """Decide each identity by exhaustive enumeration over the free variables."""
    import hashlib

    path = _network_path(model_version, root)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rules = parse_bnd_rules(path)

    # A free variable is a node whose rule is itself: the external inputs and
    # the structural relays. This is `structure.load_structure`'s own test,
    # reused verbatim rather than re-derived, so the two analyses cannot
    # disagree about what is being held free -- which would otherwise be a
    # silent way for this check to prove something about a different model.
    free = tuple(node for node in rules if rules[node].strip() == node)
    states = 2 ** len(free)
    if states > MAX_ENUMERATION_STATES:
        raise IdentityError(
            f"{states} states exceeds the enumeration ceiling "
            f"{MAX_ENUMERATION_STATES}; refusing to sample"
        )
    # One bit per enumerated state, so the mask is `states` bits wide -- not
    # `states - 1`, which is the width of a state *index* and would silently
    # truncate every column to its lowest few assignments. Taken from
    # `structure.load_structure` rather than rederived, for the same reason the
    # free set is.
    mask = (1 << states) - 1

    # Column i of free variable k alternates every 2**k states, so the seeds
    # are the standard truth-table columns.
    seeds: dict[str, int] = {}
    for index, node in enumerate(free):
        block = 1 << index
        column = 0
        for start in range(block, states, block * 2):
            column |= ((1 << block) - 1) << start
        seeds[node] = column

    order = _topological_order(rules, set(free))
    columns = _columns(rules, order, seeds, mask)

    results: list[IdentityResult] = []
    for node, claimed in identities:
        if node not in rules:
            raise IdentityError(f"identity names {node!r}, which the network lacks")
        try:
            claim_column = eval(_as_bitwise(claimed), {}, dict(columns)) & mask
        except NameError as exc:  # pragma: no cover - guarded by the test
            raise IdentityError(
                f"identity for {node} names an unknown node: {exc}"
            ) from exc
        disagree = (columns[node] ^ claim_column) & mask
        count = disagree.bit_count()
        witness = None
        if count:
            state = (disagree & -disagree).bit_length() - 1
            witness = {v: bool(state >> i & 1) for i, v in enumerate(free)}
        results.append(IdentityResult(node, claimed, count == 0, count, witness))

    return IdentityReport(
        model_version=model_version,
        network_sha256=digest,
        free=free,
        enumerated_states=states,
        results=tuple(results),
    )


@dataclass(frozen=True)
class ClampResult:
    """What clamping one node does to every reported output, exhaustively."""

    node: str
    mode: str
    #: ``{output: states_changed}`` over all free-variable assignments.
    changed: dict[str, int]
    #: Nodes realising the identical Boolean function as this one, which no
    #: baseline readout can tell it apart from.
    aliases: tuple[str, ...]

    @property
    def discriminating_outputs(self) -> tuple[str, ...]:
        return tuple(sorted(o for o, n in self.changed.items() if n))

    @property
    def observationally_silent(self) -> bool:
        return not self.discriminating_outputs


def clamp_discrimination(
    targets: tuple[str, ...],
    model_version: str = DEFAULT_MODEL_VERSION,
    root: Path | None = None,
) -> tuple[ClampResult, ...]:
    """Clamp each target OFF and ON; count output changes over every state.

    This is the structural half of an identifiability question: if clamping a
    node leaves every ``OUT_`` node identical in all ``2 ** len(free)``
    assignments, then no experiment that reads only those outputs at a fixed
    point can detect the intervention -- a complete answer, not a sample.

    It is emphatically not the dynamical half. Two interventions that agree on
    every fixed point may still differ in transient order, in hitting time or
    in the probability mass MaBoSS assigns en route, and this function says
    nothing about any of those. A node reported silent here is unobservable at
    steady state, not biologically idle.
    """
    path = _network_path(model_version, root)
    rules = parse_bnd_rules(path)
    free = tuple(node for node in rules if rules[node].strip() == node)
    states = 2 ** len(free)
    if states > MAX_ENUMERATION_STATES:
        raise IdentityError(f"{states} states exceeds the enumeration ceiling")
    mask = (1 << states) - 1

    seeds: dict[str, int] = {}
    for index, node in enumerate(free):
        block = 1 << index
        column = 0
        for start in range(block, states, block * 2):
            column |= ((1 << block) - 1) << start
        seeds[node] = column

    order = _topological_order(rules, set(free))
    outputs = tuple(n for n in rules if n.startswith("OUT_"))
    baseline = _columns(rules, order, seeds, mask)

    # Nodes with the same bit column compute the same function of the inputs.
    by_column: dict[int, list[str]] = {}
    for node, column in baseline.items():
        by_column.setdefault(column, []).append(node)

    results: list[ClampResult] = []
    for target in targets:
        if target not in rules:
            raise IdentityError(f"{target!r} is not a node of {model_version}")
        aliases = tuple(sorted(n for n in by_column[baseline[target]] if n != target))
        for mode, value in (("loss_of_function", 0), ("gain_of_function", mask)):
            # Clamping replaces the node's rule, so every rule downstream is
            # re-evaluated against the clamped column rather than its own.
            clamped = dict(rules)
            clamped[target] = "False" if value == 0 else "True"
            forced = dict(seeds)
            forced[target] = value
            order_c = _topological_order(clamped, set(free) | {target})
            columns = _columns(clamped, order_c, forced, mask)
            changed = {
                out: ((columns[out] ^ baseline[out]) & mask).bit_count()
                for out in outputs
            }
            results.append(ClampResult(target, mode, changed, aliases))
    return tuple(results)


def report_json(report: IdentityReport) -> str:
    return json.dumps(
        {
            "model_version": report.model_version,
            "network_sha256": report.network_sha256,
            "free_variables": list(report.free),
            "enumerated_states": report.enumerated_states,
            "method": "exhaustive bit-column enumeration over free variables",
            "all_hold": report.all_hold,
            "identities": [
                {
                    "node": r.node,
                    "claimed": r.claimed,
                    "holds": r.holds,
                    "counterexamples": r.counterexamples,
                    "witness": r.witness,
                }
                for r in report.results
            ],
        },
        indent=2,
        sort_keys=False,
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-version", default=DEFAULT_MODEL_VERSION)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = verify_identities(args.model_version)
    if args.json:
        print(report_json(report))
    else:
        print(f"{report.model_version}  sha256 {report.network_sha256[:16]}")
        print(f"{len(report.free)} free variables, {report.enumerated_states} states")
        for result in report.results:
            mark = "HOLDS     " if result.holds else "FAILS     "
            print(f"{mark} {result.node}")
            if not result.holds:
                print(f"           {result.counterexamples} disagreeing assignments")
                print(f"           witness: {result.witness}")
    return 0 if report.all_hold else 1


if __name__ == "__main__":
    raise SystemExit(main())
