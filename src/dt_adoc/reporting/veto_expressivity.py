"""What a full ``activity_veto`` of each eligible target expresses (Stage 4b, §5).

For every node the O8b audit admits as a direct target, and every veto-mode
library intervention of the same version, this computes the exact asymptotic
marginals of every node under the veto and compares them with the unperturbed
rules. It then groups the vetoes into classes that the observed readouts cannot
tell apart, and names the **structural nulls**: vetoes that change no observed
node in any declared condition.

Why the computation is exact. A network whose only cycles are self-loops has,
for fixed inputs and free variables, one fixed point, which MaBoSS reaches with
probability 1; a veto renders the target's rule as ``(...) and not 1`` and so
only fixes that node at 0. The asymptotic marginals are therefore a weighted
sum over the free variables' baseline istates. A network with any other cycle is
refused, because then none of this holds.

What it does not say. Transients differ (an upstream veto reaches a node a step
later), but time is relative and uncalibrated, so they are not read as
distinguishability. The classes are relative to the declared condition set and
to the observation map; adding either can split a class or unmask a null, which
is why the output is regenerated and pinned rather than written down once.

Nothing here runs MaBoSS or writes under ``models/`` or ``config/``. Since the
Stage 4b §10 implementation the direct-row licence reruns it and the run record
carries its classes (``perturbations.adjudication.expressivity_classes``), so
this module and its two tables are in the implementation digest (amendment A1 of
``docs/stage4b_implementation.md``). The pre-registration is
``docs/stage4b_direct_admission.md``.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.adjudication import AUDIT_MODEL_VERSION, target_audit
from dt_adoc.perturbations.engine import (
    _KINETIC_RE,
    _evaluable,
    _node_blocks,
    _value,
    read_library_rows,
)

OUTPUT_PATH = Path("docs/stage4b/v060_veto_expressivity.tsv")
OBSERVATION_MAP_PATH = Path("config/observation_model_map.tsv")

#: Roles of the protocol layer: their values come from each condition cfg.
PROTOCOL_INPUT_ROLES = frozenset(
    {"input", "assay_gate", "external_input", "pathology_input", "boundary_input"}
)
#: Observation-map ``activation_status`` values whose nodes form the observed
#: set O. The column takes exactly five values; these three are O, `reported_only`
#: forms the extended set, and `rejected` is excluded entirely because the
#: repository has adjudicated those rows as carrying no claim. Every value is
#: classified, so no status is silently dropped — `REFUSED_STATUSES` below holds
#: the rest, and a value outside the five is an error rather than an omission.
OBSERVED_STATUSES = frozenset({"active_constraint", "active_diagnostic", "provisional"})
REPORTED_ONLY_STATUS = "reported_only"
REJECTED_STATUS = "rejected"
#: Every value the column may take, so an unrecognised one is refused.
KNOWN_STATUSES = OBSERVED_STATUSES | {REPORTED_ONLY_STATUS, REJECTED_STATUS}
#: The binomial adhesion assay (node dictionary: "binomial assay outcome"). It is
#: not an observation-map row, so it is named here.
ADHESION_ASSAY_NODE = "OUT_STABLE_ADHESION"
NULL_CLASS = "null"
#: Above this many hand-set free variables the 2^k scenario enumeration is
#: refused rather than truncated. v0.6.0 has one.
MAX_HAND_SET_FREE_NODES = 8
TOLERANCE = 1e-12

COLUMNS = (
    "arm",
    "arm_kind",
    "targets",
    "observed_class",
    "observed_class_members",
    "extended_class",
    "structurally_null_on_observed",
    "changes_any_non_target_node",
    "observed_effect_reference_context",
    "adhesion_delta_by_context",
)
#: The two context columns above report scenario 0 — the baseline istates, which
#: for v0.6.0 means ``E_KLF12_HIGH = 0``. They are an illustrative slice, never
#: the basis of a class: the classes come from every scenario and every context.
#: At ``E_KLF12_HIGH = 1`` the epithelial branch is off, baseline adhesion is 0
#: and every delta is 0, which is why a single reported slice must say which.
REPORTED_SCENARIO_INDEX = 0
REFERENCE_CONTEXT = "adhesion_challenge_hormone_treated"

_LOGIC_RE = re.compile(r"logic\s*=\s*([^;]+);")
_POINT_ISTATE_RE = re.compile(
    r"^\s*(\w+)\.istate\s*=\s*(TRUE|FALSE|0|1)\s*;", re.MULTILINE
)
#: Any single-node istate, whatever the value. Anything this matches but
#: ``_POINT_ISTATE_RE`` does not carries a spelling we do not interpret (``1.0``,
#: ``0.5``, ``True``), and is refused rather than ignored: ignoring it would
#: silently leave the node at its baseline value.
_ANY_POINT_ISTATE_RE = re.compile(r"^\s*(\w+)\.istate\s*=\s*([^;]*);", re.MULTILINE)


def _unreadable_istates(text: str) -> list[tuple[str, str]]:
    """Single-node istate declarations whose value we do not interpret."""
    readable = {(n, v) for n, v in _POINT_ISTATE_RE.findall(text)}
    return [
        (n, v.strip())
        for n, v in _ANY_POINT_ISTATE_RE.findall(text)
        if (n, v.strip()) not in readable
    ]


_JOINT_ISTATE_RE = re.compile(
    r"^\s*\[(\w+)\]\.istate\s*=\s*([0-9.]+)\s*\[0\]\s*,\s*([0-9.]+)\s*\[1\]\s*;",
    re.MULTILINE,
)
#: Any bracketed istate, including the multi-node ``[A,B].istate`` form that
#: ``_JOINT_ISTATE_RE`` does not match. A multi-node istate declares a *joint*
#: distribution, which per-node marginals cannot represent, so it is refused
#: rather than parsed; this regex is what finds it.
_BRACKET_ISTATE_RE = re.compile(r"^\s*\[([\w\s,]+)\]\.istate\s*=", re.MULTILINE)


def _bracket_nodes(text: str) -> list[tuple[str, ...]]:
    """The node tuple of every bracketed istate declaration in ``text``."""
    return [
        tuple(part.strip() for part in match.group(1).split(",") if part.strip())
        for match in _BRACKET_ISTATE_RE.finditer(text)
    ]


class ExpressivityError(ValueError):
    """The network or its cfgs fall outside what the exact computation covers."""


@dataclass(frozen=True)
class Network:
    order: tuple[str, ...]  # non-free nodes, in topological order
    rules: dict[str, str]  # node -> evaluable Python Boolean expression
    free: tuple[str, ...]  # self-loop nodes
    nodes: tuple[str, ...]  # every node, in file order


def parse_network(text: str) -> Network:
    """The rules of ``text`` in evaluation order.

    Refuses any non-self-loop cycle, and any node that declares a transition
    rate: the fixed point is where the trajectories end only because every node
    runs at MaBoSS's default rates, so a declared rate puts the network outside
    this argument for every node, not only for a veto target. ``engine``'s
    ``_target_logic`` refuses a rate on the target for the narrower reason that
    it would change what the veto means.
    """
    blocks = _node_blocks(text)
    if not blocks:
        raise ExpressivityError("no Node blocks in the network text")
    rules, reads, free = {}, {}, []
    for node, body in blocks.items():
        if _KINETIC_RE.search(body):
            raise ExpressivityError(
                f"{node} declares a transition rate; the exact fixed-point "
                "computation assumes default rates throughout"
            )
        logic = _LOGIC_RE.findall(body)
        if len(logic) != 1:
            raise ExpressivityError(f"{node} has no single logic line")
        expression, names = _evaluable(logic[0])
        if names == {node} and expression.strip("() ") == node:
            free.append(node)
            continue
        unknown = names - set(blocks)
        if unknown:
            raise ExpressivityError(f"{node} reads unknown nodes {sorted(unknown)}")
        rules[node], reads[node] = expression, names
    order, placed = [], set(free)
    pending = dict(reads)
    while pending:
        ready = sorted(n for n, r in pending.items() if r <= placed)
        if not ready:
            raise ExpressivityError(
                f"cycle other than a self-loop through {sorted(pending)}; "
                "exact fixed-point enumeration does not apply"
            )
        for node in ready:
            order.append(node)
            placed.add(node)
            del pending[node]
    return Network(tuple(order), rules, tuple(free), tuple(blocks))


def fixed_point(
    network: Network, values: dict[str, bool], vetoes: frozenset[str]
) -> dict[str, bool]:
    """The one fixed point under ``vetoes``.

    A veto is only applied to a node this network computes. Vetoing a free
    (self-loop) node would be silently ignored here and would come out as a
    structural null — the most damaging possible wrong answer, since §5.6 reads
    a null as "no observed change under complete engagement". So it is refused.
    Today the O8b audit already refuses every self-loop node mechanically; this
    keeps the generator sound if that ever changes.
    """
    unknown = sorted(v for v in vetoes if v not in network.rules)
    if unknown:
        free = [v for v in unknown if v in network.free]
        detail = (
            f"{free} are free (self-loop) nodes, whose value is a declared "
            "initial condition rather than a computed rule"
            if free
            else f"{unknown} are not nodes of this network"
        )
        raise ExpressivityError(f"cannot veto {unknown}: {detail}")
    state = dict(values)
    for node in network.order:
        state[node] = False if node in vetoes else _value(network.rules[node], state)
    return state


def free_distributions(cfg_text: str, free: tuple[str, ...]) -> dict[str, float]:
    """P(node = 1) for each free node, from the baseline cfg.

    A multi-node ``[A,B].istate`` declares a joint distribution, which per-node
    marginals cannot represent, so it is refused rather than approximated.
    """
    multi = [nodes for nodes in _bracket_nodes(cfg_text) if len(nodes) > 1]
    if multi:
        raise ExpressivityError(
            f"multi-node istate {multi} declares a joint distribution; "
            "per-node marginals cannot represent it"
        )
    unreadable = _unreadable_istates(cfg_text)
    if unreadable:
        raise ExpressivityError(f"baseline istate values not interpreted: {unreadable}")
    p = {
        n: (1.0 if v in ("TRUE", "1") else 0.0)
        for n, v in _POINT_ISTATE_RE.findall(cfg_text)
    }
    for node, p0, p1 in _JOINT_ISTATE_RE.findall(cfg_text):
        if abs(float(p0) + float(p1) - 1.0) > 1e-9:
            raise ExpressivityError(f"{node} istate does not sum to 1")
        p[node] = float(p1)
    missing = [n for n in free if n not in p]
    if missing:
        raise ExpressivityError(f"no istate for free nodes {missing}")
    return {n: p[n] for n in free}


def marginals(
    network: Network,
    inputs: dict[str, bool],
    distribution: dict[str, float],
    vetoes: frozenset[str],
) -> dict[str, float]:
    """Exact asymptotic marginals: a weighted sum over the free nodes' istates."""
    uncertain = [n for n, p in distribution.items() if 0.0 < p < 1.0]
    fixed = {n: p == 1.0 for n, p in distribution.items() if n not in uncertain}
    total = dict.fromkeys(network.nodes, 0.0)
    for bits in itertools.product((False, True), repeat=len(uncertain)):
        weight = 1.0
        for node, bit in zip(uncertain, bits):
            weight *= distribution[node] if bit else 1.0 - distribution[node]
        state = fixed_point(
            network, {**fixed, **inputs, **dict(zip(uncertain, bits))}, vetoes
        )
        for node in network.nodes:
            total[node] += weight * state[node]
    return total


def _scenarios(
    distribution: dict[str, float], inputs: set[str]
) -> list[dict[str, float]]:
    """Every combination of the hand-set free variables' values.

    A non-input free node with a point istate (``E_KLF12_HIGH`` in v0.6.0) is a
    hand-set context rather than a measured one, so a class must hold at every
    combination of their values — not merely at each one flipped on its own,
    which would miss a class that only two of them together can split. v0.6.0 has
    exactly one such node, where the two agree; the enumeration is what makes the
    rule right for a version with more.
    """
    base = {n: p for n, p in distribution.items() if n not in inputs}
    hand_set = sorted(n for n, p in base.items() if p in (0.0, 1.0))
    if len(hand_set) > MAX_HAND_SET_FREE_NODES:
        raise ExpressivityError(
            f"{len(hand_set)} hand-set free variables {hand_set} would need "
            f"2^{len(hand_set)} scenarios, above the cap of "
            f"{MAX_HAND_SET_FREE_NODES}; enumerate them deliberately rather than "
            "silently sampling"
        )
    return [
        {**base, **dict(zip(hand_set, values))}
        for values in itertools.product((0.0, 1.0), repeat=len(hand_set))
    ]


def _contexts(
    condition_dir: Path,
    protocol_inputs: tuple[str, ...],
    free: tuple[str, ...],
    baseline: dict[str, float],
) -> dict[str, dict[str, bool]]:
    """One context per distinct input vector, named by its first cfg in sort order.

    A condition cfg is read the way the runner merges it: an input the cfg does
    not name keeps its baseline value, rather than defaulting to off. Only
    protocol inputs may vary, so a cfg that sets a free variable is refused
    instead of being silently ignored, and a protocol input the baseline leaves
    mixed is refused because no single assignment represents it.
    """
    mixed = sorted(n for n in protocol_inputs if 0.0 < baseline[n] < 1.0)
    if mixed:
        raise ExpressivityError(
            f"baseline gives protocol inputs {mixed} a mixed istate"
        )
    seen: dict[tuple[bool, ...], str] = {}
    hand_set = set(free) - set(protocol_inputs)
    for cfg in sorted(condition_dir.glob("*.cfg")):
        text = cfg.read_text(encoding="utf-8")
        bracketed = _bracket_nodes(text)
        multi = [nodes for nodes in bracketed if len(nodes) > 1]
        if multi:
            raise ExpressivityError(
                f"{cfg.name} declares a multi-node istate {multi}; "
                "per-node marginals cannot represent a joint distribution"
            )
        # Every bracketed node, single or multi, counts as named and as mixed:
        # matching only the single-node form would let `[A,B].istate` through.
        bracket_names = {n for nodes in bracketed for n in nodes}
        if bracket_names & set(protocol_inputs):
            raise ExpressivityError(f"{cfg.name} gives a protocol input a mixed istate")
        unreadable = _unreadable_istates(text)
        if unreadable:
            raise ExpressivityError(
                f"{cfg.name} istate values not interpreted: {unreadable}"
            )
        named = {n for n, *_ in _POINT_ISTATE_RE.findall(text)} | bracket_names
        if named & hand_set:
            raise ExpressivityError(
                f"{cfg.name} sets free variables {sorted(named & hand_set)}"
            )
        values = {n: baseline[n] == 1.0 for n in protocol_inputs}
        values.update(
            {
                n: v in ("TRUE", "1")
                for n, v in _POINT_ISTATE_RE.findall(text)
                if n in values
            }
        )
        key = tuple(values[n] for n in protocol_inputs)
        seen.setdefault(key, cfg.stem)
    return {name: dict(zip(protocol_inputs, key)) for key, name in seen.items()}


def _observed_sets(
    root: Path, nodes: set[str]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """O and the extended set, from ``activation_status`` alone.

    Membership of O means the row is *measured and not rejected*; it does not
    mean the row carries a term in any objective. Those are different columns:
    `S_PRL` enters O through OM-006, whose `objective_treatment` is `not_used`.
    Reading `objective_treatment` here instead would make screenability depend on
    the calibration objective, which is a different question from what the assays
    can see.
    """
    observed, reported = set(), set()
    with (root / OBSERVATION_MAP_PATH).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            targets = {n for n in row["model_nodes"].split(";") if n}
            status = row["activation_status"]
            if status not in KNOWN_STATUSES:
                raise ExpressivityError(
                    f"{row['mapping_id']} has unknown activation_status {status!r}; "
                    f"the known values are {sorted(KNOWN_STATUSES)}"
                )
            if status in OBSERVED_STATUSES:
                observed |= targets
            elif status == REPORTED_ONLY_STATUS:
                reported |= targets
    observed.add(ADHESION_ASSAY_NODE)
    observed &= nodes
    return tuple(sorted(observed)), tuple(sorted((reported - observed) & nodes))


def _arms(model_version: str, root: Path) -> list[tuple[str, str, frozenset[str]]]:
    arms = [
        (row["node_id"], "eligible_node", frozenset({row["node_id"]}))
        for row in target_audit(model_version, root)
        if row["direct_target"] == "yes"
    ]
    library: dict[str, set[str]] = {}
    for effect in read_library_rows(root):
        if effect.model_version == model_version and effect.mode == "activity_veto":
            library.setdefault(effect.intervention_id, set()).add(effect.target_node)
    arms.extend(
        (name, "library_intervention", frozenset(targets))
        for name, targets in sorted(library.items())
    )
    return arms


def _classes(signatures: dict[str, tuple]) -> dict[str, str]:
    """Each arm's class, named by its first member; all-zero signatures are null."""
    first: dict[tuple, str] = {}
    out = {}
    for arm, sig in signatures.items():
        if all(abs(x) < TOLERANCE for x in sig):
            out[arm] = NULL_CLASS
        else:
            out[arm] = first.setdefault(sig, arm)
    return out


def _fmt(x: float) -> str:
    return f"{x:+.4f}"


def expressivity(
    model_version: str = AUDIT_MODEL_VERSION, root: Path | None = None
) -> list[dict[str, str]]:
    root = root or repo_root()
    spec = resolve_model(model_version, root)
    network = parse_network(spec.network_bnd.read_text(encoding="utf-8"))
    with spec.node_dictionary.open(encoding="utf-8", newline="") as handle:
        roles = {
            r["node_id"]: r["model_role"]
            for r in csv.DictReader(handle, delimiter="\t")
        }
    protocol_inputs = tuple(
        n for n in network.free if roles.get(n) in PROTOCOL_INPUT_ROLES
    )
    distribution = free_distributions(
        spec.baseline_cfg.read_text(encoding="utf-8"), network.free
    )
    contexts = _contexts(
        spec.condition_dir, protocol_inputs, network.free, distribution
    )
    scenarios = _scenarios(distribution, set(protocol_inputs))
    if REFERENCE_CONTEXT not in contexts:
        # Contexts are keyed by input vector and named after the first cfg that
        # carries it, so the reference disappears either when its cfg is gone or
        # when an earlier-sorting cfg shares its inputs. Both would silently
        # empty a reported column, so neither is allowed to pass.
        raise ExpressivityError(
            f"reference context {REFERENCE_CONTEXT!r} is not a distinct context of "
            f"{model_version}; the contexts are {sorted(contexts)}"
        )
    observed, reported = _observed_sets(root, set(network.nodes))
    arms = _arms(model_version, root)

    deltas: dict[tuple[str, str, int], dict[str, float]] = {}
    for c_name, inputs in contexts.items():
        for s_index, scenario in enumerate(scenarios):
            base = marginals(network, inputs, scenario, frozenset())
            for arm, _, targets in arms:
                m = marginals(network, inputs, scenario, targets)
                deltas[(arm, c_name, s_index)] = {
                    n: m[n] - base[n] for n in network.nodes
                }

    keys = [(c, s) for c in sorted(contexts) for s in range(len(scenarios))]

    def signature(arm: str, nodes: tuple[str, ...]) -> tuple:
        return tuple(round(deltas[(arm, c, s)][n], 9) for c, s in keys for n in nodes)

    observed_class = _classes({arm: signature(arm, observed) for arm, *_ in arms})
    extended_class = _classes(
        {arm: signature(arm, observed + reported) for arm, *_ in arms}
    )
    rows = []
    for arm, kind, targets in arms:
        members = sorted(
            a for a, *_ in arms if observed_class[a] == observed_class[arm]
        )
        others = any(
            abs(x) > TOLERANCE
            for (a, _, _), d in deltas.items()
            if a == arm
            for n, x in d.items()
            if n not in targets
        )
        reference = deltas[(arm, REFERENCE_CONTEXT, REPORTED_SCENARIO_INDEX)]
        rows.append(
            {
                "arm": arm,
                "arm_kind": kind,
                "targets": ";".join(sorted(targets)),
                "observed_class": observed_class[arm],
                "observed_class_members": ";".join(members),
                "extended_class": extended_class[arm],
                "structurally_null_on_observed": "yes"
                if observed_class[arm] == NULL_CLASS
                else "no",
                "changes_any_non_target_node": "yes" if others else "no",
                "observed_effect_reference_context": ";".join(
                    f"{n}:{_fmt(reference[n])}"
                    for n in observed
                    if abs(reference.get(n, 0.0)) > TOLERANCE
                ),
                "adhesion_delta_by_context": ";".join(
                    f"{c}:{_fmt(deltas[(arm, c, REPORTED_SCENARIO_INDEX)][ADHESION_ASSAY_NODE])}"
                    for c in sorted(contexts)
                    if abs(
                        deltas[(arm, c, REPORTED_SCENARIO_INDEX)][ADHESION_ASSAY_NODE]
                    )
                    > TOLERANCE
                ),
            }
        )
    return rows


def baseline_marginal(
    node: str,
    context: str,
    model_version: str = AUDIT_MODEL_VERSION,
    root: Path | None = None,
) -> float:
    """The unperturbed asymptotic marginal of ``node`` in a named context cfg."""
    root = root or repo_root()
    spec = resolve_model(model_version, root)
    network = parse_network(spec.network_bnd.read_text(encoding="utf-8"))
    with spec.node_dictionary.open(encoding="utf-8", newline="") as handle:
        roles = {
            r["node_id"]: r["model_role"]
            for r in csv.DictReader(handle, delimiter="\t")
        }
    protocol_inputs = tuple(
        n for n in network.free if roles.get(n) in PROTOCOL_INPUT_ROLES
    )
    distribution = free_distributions(
        spec.baseline_cfg.read_text(encoding="utf-8"), network.free
    )
    scenario = _scenarios(distribution, set(protocol_inputs))[0]
    contexts = _contexts(
        spec.condition_dir, protocol_inputs, network.free, distribution
    )
    if context not in contexts:
        # Several cfgs can share an input vector; the context takes the first name.
        raise ExpressivityError(
            f"{context} is not a distinct context; it is one of {sorted(contexts)}"
        )
    return marginals(network, contexts[context], scenario, frozenset())[node]


def render(rows: list[dict[str, str]]) -> str:
    lines = ["\t".join(COLUMNS)]
    lines.extend("\t".join(row[c] for c in COLUMNS) for row in rows)
    return "\n".join(lines) + "\n"


# --- Exhaustive invariance over every free-variable assignment (§5.4.1) -------
#
# The per-condition computation above answers "what do the declared arms show?".
# This answers the stronger question the pre-registration actually claims: "is
# the classification a property of the rules, or of the arms we happened to
# declare?". It evaluates *every* assignment of *every* free variable at once,
# by representing each node's value across all 2^k assignments as one Python
# integer used as a bit vector. The network is feed-forward, so one pass in
# topological order evaluates all assignments simultaneously, and `and`/`or`/
# `not` become `&`/`|`/`~`. That is why an exhaustive check is cheap enough to
# be a test rather than a design-time note.

INVARIANCE_PATH = Path("docs/stage4b/v060_veto_invariance.tsv")
INVARIANCE_COLUMNS = (
    "arm",
    "targets",
    "null_under_every_assignment",
    "class_under_every_assignment",
    "class_members_under_every_assignment",
    "agrees_with_declared_condition_class",
)
#: Refuse an enumeration too large to hold as bit vectors.
MAX_FREE_NODES_FOR_EXHAUSTIVE = 24

_BITWISE = {"and": "&", "or": "|", "not": "~"}


def _bitwise_expression(expression: str, full_name: str) -> str:
    """``expression`` with Boolean operators rewritten as bitwise ones.

    ``not`` becomes ``~``, which binds more tightly than ``&`` and ``|`` just as
    ``not`` binds more tightly than ``and`` and ``or``, so the parse is
    unchanged. ``~`` on a Python int yields a negative value, which is why every
    node's result is masked back to the enumeration width.
    """

    def replace(match: re.Match[str]) -> str:
        word = match.group(0)
        if word in _BITWISE:
            return _BITWISE[word]
        if word == "1":
            return full_name
        return word

    return re.sub(r"\b\w+\b", replace, expression)


def exhaustive_signatures(
    network: Network,
    observed: tuple[str, ...],
    arms: list[tuple[str, str, frozenset[str]]],
) -> tuple[dict[str, tuple[int, ...]], tuple[int, ...], int]:
    """Each arm's O-signature over every assignment of every free variable.

    Returns the per-arm signatures, the unperturbed signature, and how many
    assignments were enumerated. A signature is one bit vector per observed
    node, so two arms are indistinguishable on O under *every* assignment
    exactly when their signatures are equal.
    """
    free = network.free
    if len(free) > MAX_FREE_NODES_FOR_EXHAUSTIVE:
        raise ExpressivityError(
            f"{len(free)} free variables would need 2^{len(free)} assignments, "
            f"above the cap of {MAX_FREE_NODES_FOR_EXHAUSTIVE}"
        )
    width = 1 << len(free)
    full = (1 << width) - 1
    columns: dict[str, int] = {}
    for index, node in enumerate(free):
        ones = (1 << (1 << index)) - 1
        block = ones << (1 << index)
        period = 1 << (index + 1)
        pattern = 0
        for start in range(0, width, period):
            pattern |= block << start
        columns[node] = pattern & full
    compiled = {
        node: compile(
            _bitwise_expression(network.rules[node], "_FULL"), "<bits>", "eval"
        )
        for node in network.order
    }

    def evaluate(vetoes: frozenset[str]) -> dict[str, int]:
        state = dict(columns)
        scope = {"_FULL": full}
        for node in network.order:
            state[node] = (
                0
                if node in vetoes
                else eval(compiled[node], {"__builtins__": {}}, {**state, **scope})
                & full
            )
        return state

    base = evaluate(frozenset())
    baseline = tuple(base[node] for node in observed)
    signatures = {}
    for arm, _, targets in arms:
        state = evaluate(targets)
        signatures[arm] = tuple(state[node] for node in observed)
    return signatures, baseline, width


def invariance(
    model_version: str = AUDIT_MODEL_VERSION, root: Path | None = None
) -> list[dict[str, str]]:
    """§5.4.1: the classification under every free-variable assignment."""
    root = root or repo_root()
    spec = resolve_model(model_version, root)
    network = parse_network(spec.network_bnd.read_text(encoding="utf-8"))
    observed, _ = _observed_sets(root, set(network.nodes))
    arms = _arms(model_version, root)
    signatures, baseline, _ = exhaustive_signatures(network, observed, arms)
    declared = {row["arm"]: row for row in expressivity(model_version, root)}
    classes: dict[tuple[int, ...], str] = {}
    names = {}
    for arm, _, _ in arms:
        names[arm] = (
            NULL_CLASS
            if signatures[arm] == baseline
            else classes.setdefault(signatures[arm], arm)
        )
    rows = []
    for arm, _, targets in arms:
        members = sorted(a for a, *_ in arms if names[a] == names[arm])
        rows.append(
            {
                "arm": arm,
                "targets": ";".join(sorted(targets)),
                "null_under_every_assignment": "yes"
                if names[arm] == NULL_CLASS
                else "no",
                "class_under_every_assignment": names[arm],
                "class_members_under_every_assignment": ";".join(members),
                "agrees_with_declared_condition_class": "yes"
                if members == declared[arm]["observed_class_members"].split(";")
                else "no",
            }
        )
    return rows


def render_invariance(rows: list[dict[str, str]]) -> str:
    lines = ["\t".join(INVARIANCE_COLUMNS)]
    lines.extend("\t".join(row[c] for c in INVARIANCE_COLUMNS) for row in rows)
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("write", "check"))
    args = parser.parse_args(argv)
    root = repo_root()
    outputs = (
        (OUTPUT_PATH, render(expressivity(root=root))),
        (INVARIANCE_PATH, render_invariance(invariance(root=root))),
    )
    if args.command == "write":
        for path, text in outputs:
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text(text, encoding="utf-8")
        return 0
    for path, text in outputs:
        if (
            not (root / path).exists()
            or (root / path).read_text(encoding="utf-8") != text
        ):
            print(f"{path} is stale; run write", file=sys.stderr)
            return 1
    print(f"ok: {OUTPUT_PATH} and {INVARIANCE_PATH} current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
