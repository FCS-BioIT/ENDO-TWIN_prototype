"""What the ADOC experiment can and cannot determine about the executable model.

``structure.py`` asks what the *model* distinguishes. This module asks what the
*experiment* distinguishes, which is a strictly harder question and a much
smaller number.

The framing is structural identifiability of a Boolean model under a finite
experimental design, expressed as three nested partitions of the node labels:

``P_label``
    one class per named node -- how the network is drawn.
``P_global``
    one class per distinct Boolean function over all free variables. Labels that
    merge here are merged by the *rules*; no experiment can separate them while
    the rules say what they say. This is ``structure.py``'s alias analysis.
``P_design``
    one class per distinct behaviour over the region of state space the run arms
    actually visit. Labels that merge here but not in ``P_global`` are merged by
    the *design*; de-bundling the arms separates them.

Keeping those two collapses apart is the point of the module. Reporting only the
label count overstates what the model resolves; reporting only ``P_global``
blames the rules for degeneracy the experiment caused; reporting only
``P_design`` blames the experiment for degeneracy the rules caused. A measurement
proposed to break a ``P_global`` merge is asking for a model repair, and a
measurement proposed to break a ``P_design`` merge is asking for a protocol
change. They are not interchangeable and they do not cost the same.

On top of the partitions sits the measurement layer. The free variables split
into inputs some arm assigns (*controlled*) and internal free variables no arm
assigns (*latent*) -- here ``E_KLF12_HIGH`` and the four interface relays, whose
per-unit values are unknown. Each latent assignment yields one observation
vector; the fibres of that map are the observationally equivalent states, and a
node is identified exactly when its value is constant on every fibre.

Nothing here simulates. Every quantity is a property of ``network.bnd``, the
condition ``.cfg`` files, and the two tables that record which observations
exist. That is deliberate: the endpoint-horizon decision
(``docs/endpoint_convergence_finding.md``) is unresolved, and a claim about what
an experiment can identify must not depend on it. The one place a ``.cfg``
initial probability is read is ``adhesion_endpoint_decomposition``, which exists
to show that the headline 0.82 is arithmetic rather than inference, and it is
reported separately from every partition count.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dt_adoc.calibration.observation_map import (
    EVALUABLE_ACTIVATION_STATUSES,
    load_observation_map,
)
from dt_adoc.model.catalog import load_tsv
from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting.structure import (
    INPUT_PREFIX,
    _columns,
    _topological_order,
    load_structure,
)

#: Refuse to enumerate beyond this many latent assignments rather than sampling.
MAX_LATENT_STATES = 2**20

#: ``measurement_proxies`` values in the node dictionary that name no physical
#: assay target. The four ``structural_uncertainty`` relays declare "bounded
#: stochastic initialization" and the three interface routes declare "derived
#: route state": the dictionary is saying, in its own words, that these are
#: modelling placeholders. An optimiser that is allowed to "measure" them will
#: propose the one panel no laboratory can run, so they are excluded from every
#: candidate readout search and the exclusion is reported, not silent.
NON_ASSAYABLE_PROXIES = frozenset(
    {
        "bounded stochastic initialization",
        "derived route state",
        "experimental schedule",
        "assay design",
        "upstream model state",
        "",
    }
)

_ISTATE_BOOL = re.compile(r"^\s*(\w+)\.istate\s*=\s*(TRUE|FALSE)\s*;", re.MULTILINE)
_ISTATE_PROB = re.compile(
    r"^\s*\[(\w+)\]\.istate\s*=\s*([\d.]+)\s*\[0\]\s*,\s*([\d.]+)\s*\[1\]\s*;",
    re.MULTILINE,
)


@dataclass(frozen=True)
class DesignArm:
    """One experimental condition the repository records an observation for."""

    arm_id: str
    cfg: str
    inputs: dict[str, bool]
    #: Nodes measured in this arm, with the artifact that records the observation.
    measured: tuple[tuple[str, str], ...]

    @property
    def on(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, v in self.inputs.items() if v))


@dataclass(frozen=True)
class IdentifiabilityFacts:
    """What the current design can and cannot determine, exactly."""

    model_version: str
    node_ids: tuple[str, ...]
    arms: tuple[DesignArm, ...]
    #: Free variables some arm assigns.
    controlled: tuple[str, ...]
    #: Free variables no arm assigns: unknown per biological unit.
    latent: tuple[str, ...]
    #: Inputs the design never moves: assigned at one level, or never assigned.
    unexcited_inputs: tuple[str, ...]
    #: Declared interventions no arm assigns at all.
    held_off_inputs: tuple[str, ...]
    #: Inputs with an effect-attributable contrast: two arms differ in that
    #: input alone AND share a measured node, so a change in that node is
    #: attributable to it.
    independently_perturbed: tuple[str, ...]
    #: Inputs two arms differ in alone, but whose arms share no measured node.
    #: The design isolates the input; the measurement cannot read its effect, so
    #: this is a statement about input assignment and not about attribution.
    set_alone_no_shared_readout: tuple[str, ...]
    #: Inputs that move only together with others; the bundles they move in.
    bundled_perturbed: dict[str, tuple[str, ...]]
    #: P_global: node labels grouped by identical Boolean function everywhere.
    global_classes: tuple[tuple[str, ...], ...]
    #: P_design: node labels grouped by identical value over the visited region.
    design_classes: tuple[tuple[str, ...], ...]
    #: Observation vector -> latent assignments producing it.
    fibers: tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]
    #: Per node: the A-E information status defined in ``classify_information``.
    information_status: dict[str, str]
    #: Per node: perturbation status.
    perturbation_status: dict[str, str]
    #: Nodes whose dictionary entry names a physical assay target.
    assayable: tuple[str, ...]
    #: From ``structure.py``; carried through so one figure has one source.
    phenotype_inert: tuple[str, ...]
    unread_inputs: tuple[str, ...]
    measured_nodes: tuple[str, ...]
    compartment_of: dict[str, str]
    label_of: dict[str, str]
    latent_states: int


def _parse_cfg_inputs(path: Path) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {m.group(1): m.group(2) == "TRUE" for m in _ISTATE_BOOL.finditer(text)}


def parse_cfg_probabilities(path: Path) -> dict[str, float]:
    """Free variables the cfg initialises to a probability rather than a Boolean."""
    text = path.read_text(encoding="utf-8")
    return {m.group(1): float(m.group(3)) for m in _ISTATE_PROB.finditer(text)}


def _observed_arms(root: Path, condition_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """Which conditions the repository records a real observation for.

    An arm earns its place in the current design by carrying an observation,
    never by having a ``.cfg``. Most conditions in the superset are in-silico
    probes -- anti-SPP1, washout, HAND2 loss, ER stress, high stiffness -- and
    counting them as run arms would credit the design with excitation it never
    applied. Two artifacts record observations: ``calibration.yaml``'s adhesion
    objective names the protocols whose embryo-attachment counts exist, and
    ``observation_model_map.tsv`` names the nodes whose molecular readouts are
    active, with the protocols they are compared across.
    """
    observed: dict[str, list[tuple[str, str]]] = {}

    calibration = yaml.safe_load(
        (root / "config" / "calibration.yaml").read_text(encoding="utf-8")
    )
    for readout in calibration["adhesion_objective"]["readouts"]:
        protocol = readout["protocol_id"]
        observed.setdefault(protocol, []).append(
            ("OUT_STABLE_ADHESION", "config/calibration.yaml adhesion_objective")
        )

    for row in load_observation_map(root):
        if row["activation_status"] not in EVALUABLE_ACTIVATION_STATUSES:
            continue
        nodes = [n for n in row["model_nodes"].split(";") if n]
        for protocol in row["protocol_ids"].split(";"):
            protocol = protocol.strip()
            if not protocol or not (condition_dir / f"{protocol}.cfg").exists():
                continue
            for node_id in nodes:
                observed.setdefault(protocol, []).append(
                    (node_id, f"config/observation_model_map.tsv {row['mapping_id']}")
                )
    return observed


def load_design(
    model_version: str, root: Path | None = None
) -> tuple[tuple[DesignArm, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """The arms the repository records observations for, and the free-variable split.

    Returns ``(arms, controlled, held_off, latent)``.

    A condition cfg is an *overlay* on ``baseline.cfg``, and it lists only what
    the condition changes: ``basal_maternal.cfg`` sets nothing at all. Reading a
    condition cfg alone would leave every unmentioned input looking unassigned;
    reading ``baseline.cfg`` wholesale would pin all 59 nodes, derived ones
    included, to their initial states and flatten the network to zero. So the
    overlay is applied over the free variables only, with ``baseline.cfg`` as the
    default for those the condition does not mention.

    The free variables then split three ways, and the split is what the whole
    analysis rests on:

    ``controlled``
        some arm assigns it. Whether it also *varies* is a separate question.
    ``held_off``
        a declared ``IN_`` intervention no arm ever assigns. Its value is known
        to be off -- the drug was not added -- so it is not an unknown. It is,
        however, a mechanism the design never excites.
    ``latent``
        an internal free variable no arm assigns. This is a property of the
        biological material, not of the protocol, so its per-unit value is
        genuinely unknown. ``baseline.cfg`` gives these an initial probability,
        but a configured assumption is not an observation and must not be
        counted as one, so they stay unknown here.
    """
    active_root = root or repo_root()
    spec = resolve_model(model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    free = tuple(n for n in rules if rules[n].strip() == n)
    observed = _observed_arms(active_root, spec.condition_dir)

    baseline = _parse_cfg_inputs(spec.baseline_cfg)
    overlays: dict[str, dict[str, bool]] = {}
    for protocol in sorted(observed):
        cfg = spec.condition_dir / f"{protocol}.cfg"
        if not cfg.exists():
            continue
        overlays[protocol] = {
            k: v for k, v in _parse_cfg_inputs(cfg).items() if k in set(free)
        }
    if not overlays:
        raise ValueError(f"{model_version} has no arm carrying a recorded observation")

    controlled = tuple(n for n in free if any(n in o for o in overlays.values()))
    rest = [n for n in free if n not in set(controlled)]
    held_off = tuple(n for n in rest if n.startswith(INPUT_PREFIX))
    latent = tuple(n for n in rest if not n.startswith(INPUT_PREFIX))

    arms = tuple(
        DesignArm(
            arm_id=protocol,
            cfg=str((spec.condition_dir / f"{protocol}.cfg").relative_to(active_root)),
            inputs={
                **{n: baseline.get(n, False) for n in controlled + held_off},
                **overlay,
            },
            measured=tuple(sorted(set(observed[protocol]))),
        )
        for protocol, overlay in sorted(overlays.items())
    )
    return arms, controlled, held_off, latent


def _latent_seeds(latent: tuple[str, ...]) -> tuple[dict[str, int], int, int]:
    states = 2 ** len(latent)
    mask = (1 << states) - 1
    seeds: dict[str, int] = {}
    for index, node_id in enumerate(latent):
        block = 1 << index
        column = 0
        for start in range(block, states, block * 2):
            column |= ((1 << block) - 1) << start
        seeds[node_id] = column
    return seeds, states, mask


def _classes(signature: dict[str, tuple[int, ...]]) -> tuple[tuple[str, ...], ...]:
    grouped: dict[tuple[int, ...], list[str]] = {}
    for node_id, sig in signature.items():
        grouped.setdefault(sig, []).append(node_id)
    return tuple(sorted(tuple(members) for members in grouped.values()))


def _global_partition(
    node_ids: tuple[str, ...], alias_classes: tuple[tuple[str, ...], ...]
) -> tuple[tuple[str, ...], ...]:
    """P_global as a full partition, not only its non-trivial classes.

    ``structure.alias_classes`` reports only groups of size >1, which is what an
    alias *finding* needs. A partition count needs the singletons too, or the
    class total is 8 rather than 35.
    """
    grouped = {n: tuple(sorted(members)) for members in alias_classes for n in members}
    return tuple(sorted({grouped.get(node_id, (node_id,)) for node_id in node_ids}))


def classify_information(
    node_id: str,
    *,
    measured: set[str],
    design_class: tuple[str, ...],
    latent_dependent: bool,
    observation_determined: bool,
) -> str:
    """One of five mutually exclusive statuses, in precedence order.

    ``directly_measured``
        an active observation maps to this node.
    ``design_aliased_to_measured``
        its value equals a measured node's everywhere the design goes. Its state
        is inferred, but only as the class: measuring it separately under the
        current arms adds nothing. This is *not* a claim that the biology is the
        same, only that this design cannot tell the two apart.
    ``indirectly_constrained``
        it depends on a latent variable, is not aliased to a measured node, and
        its value is nonetheless a function of the observation.
    ``model_asserted_untested``
        the arm alone fixes its value, and nothing observes it. The model
        predicts it; the experiment neither confirms nor refutes it.
    ``latent_unresolved``
        it depends on a latent variable and is not a function of the
        observation. Its biological state may matter; this design cannot infer it.
    """
    if node_id in measured:
        return "directly_measured"
    if measured.intersection(design_class):
        return "design_aliased_to_measured"
    if latent_dependent:
        return (
            "indirectly_constrained" if observation_determined else "latent_unresolved"
        )
    return "model_asserted_untested"


def perturbation_split(
    arms: tuple[DesignArm, ...],
    controlled: tuple[str, ...],
    unexcited_inputs: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, tuple[str, ...]]]:
    """How each controlled input moves, and whether its effect is attributable.

    Returns ``(independently_perturbed, set_alone_no_shared_readout,
    bundled_perturbed)``.

    The smallest set of inputs that changes together with this one between two
    arms. Anything larger than one is the bundle the effect is confounded
    within, and reporting the union over all arm pairs instead would make every
    bundle look like the whole protocol.

    Differing in this input ALONE is necessary for attribution and not
    sufficient. A contrast also needs a COMMON MEASURED OUTCOME: if the two arms
    read different nodes, there is no quantity whose change could be attributed
    to the input, and the pair establishes nothing about its effect. ``IN_E2``
    is exactly that case -- its only single-input contrast is ``basal_maternal``
    (reading ``S_IGFBP1``) against ``e2_primed_maternal`` (reading ``E_PAEP``),
    which share no readout -- while ``IN_MIFEPRISTONE`` has a genuine one, both
    of its arms reading ``OUT_STABLE_ADHESION``. Counting the two alike would
    report a design property as an experimental one.

    Factored out of ``load_identifiability`` so that a *proposed* design -- an
    arm set the repository has not run -- is split by the identical rule rather
    than by a second copy of it. ``design_alias.py`` is the other caller, and
    the distinction matters there rather than vanishing: a planned arm carries
    no recorded observation, so an input a plan isolates is
    ``set_alone_no_shared_readout`` until a readout is attached to it. Note that
    ``bundled_perturbed`` does not depend on the readout test -- an input is
    bundled exactly when no single-input contrast exists at all -- so a caller
    reasoning about de-bundling is unaffected by whether the arms are measured.
    """
    unexcited = set(unexcited_inputs)
    differing_sets = {
        (
            tuple(
                sorted(
                    k
                    for k in controlled
                    if left.inputs.get(k, False) != right.inputs.get(k, False)
                )
            ),
            bool({n for n, _ in left.measured} & {n for n, _ in right.measured}),
        )
        for left in arms
        for right in arms
    }
    independently: list[str] = []
    set_alone_unreadable: list[str] = []
    bundles: dict[str, tuple[str, ...]] = {}
    for node_id in controlled:
        if node_id in unexcited:
            continue
        containing = [(d, shared) for d, shared in differing_sets if node_id in d]
        if not containing:
            continue
        attributable = [d for d, shared in containing if len(d) == 1 and shared]
        alone = [d for d, _ in containing if len(d) == 1]
        if attributable:
            independently.append(node_id)
        elif alone:
            set_alone_unreadable.append(node_id)
        else:
            bundles[node_id] = min((d for d, _ in containing), key=len)
    return tuple(independently), tuple(set_alone_unreadable), bundles


def load_identifiability(
    model_version: str, root: Path | None = None
) -> IdentifiabilityFacts:
    """Everything the figure and the tables are entitled to assert."""
    spec = resolve_model(model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    node_ids = tuple(rules)
    free = tuple(n for n in node_ids if rules[n].strip() == n)
    order = _topological_order(rules, set(free))
    arms, controlled, held_off, latent = load_design(model_version, root)
    states = 2 ** len(latent)
    if states > MAX_LATENT_STATES:
        raise ValueError(
            f"{model_version} leaves {len(latent)} free variables latent under the "
            f"recorded design ({states} states), above the {MAX_LATENT_STATES} "
            "exhaustive limit. A sampled identifiability claim must not be published."
        )
    seeds_latent, states, mask = _latent_seeds(latent)

    # One evaluation of the whole network per arm, over every latent assignment.
    value: dict[str, dict[str, int]] = {}
    for arm in arms:
        seeds = dict(seeds_latent)
        for node_id, is_on in arm.inputs.items():
            seeds[node_id] = mask if is_on else 0
        value[arm.arm_id] = _columns(rules, order, seeds, mask)

    # Never excited: assigned by the arms but at one level only, plus the
    # declared interventions no arm assigns at all. Both are mechanisms the
    # design leaves switched off; neither is an unknown.
    unexcited_inputs = (
        tuple(n for n in controlled if len({arm.inputs[n] for arm in arms}) == 1)
        + held_off
    )
    independently, set_alone_unreadable, bundles = perturbation_split(
        arms, controlled, unexcited_inputs
    )

    design_signature = {
        n: tuple(value[arm.arm_id][n] for arm in arms) for n in node_ids
    }
    design_classes = _classes(design_signature)
    structure = load_structure(model_version, root)
    global_classes = _global_partition(structure.node_ids, structure.alias_classes)

    measurements = tuple(
        (arm.arm_id, node_id)
        for arm in arms
        for node_id, _ in arm.measured
        if node_id in rules
    )
    measured_nodes = tuple(sorted({n for _, n in measurements}))

    # MATCHED-UNIT ASSUMPTION, and it is load-bearing for everything below.
    # One latent index is applied across EVERY (arm, node) pair at once, so a
    # fibre is the set of latent assignments that a single biological unit,
    # carrying one latent draw, could not be told apart by if it were observed
    # under every arm and assay.
    #
    # The current data are not that design. Adhesion is an aggregate count over
    # embryos rather than a per-unit readout; the secretion mappings are
    # explicitly unpaired, and the unit mapping is not recoverable from what is
    # recorded. Under independent per-arm latent draws a joint observation
    # constrains no single shared assignment, so these fibres -- and the
    # observation-class, information-status and proposed-panel counts derived
    # from them -- describe what a MATCHED-UNIT design of this shape could
    # identify. They are not a statement about what the current data identify,
    # and `summary["unit_assumption"]` records that so no reader has to infer it.
    fiber_map: dict[tuple[int, ...], list[int]] = {}
    for index in range(states):
        key = tuple((value[a][n] >> index) & 1 for a, n in measurements)
        fiber_map.setdefault(key, []).append(index)
    fibers = tuple((key, tuple(members)) for key, members in sorted(fiber_map.items()))

    class_of = {n: c for c in design_classes for n in c}
    measured_set = set(measured_nodes)
    information: dict[str, str] = {}
    for node_id in node_ids:
        latent_dependent = any(value[a.arm_id][node_id] not in (0, mask) for a in arms)
        determined = all(
            len({(value[a.arm_id][node_id] >> i) & 1 for i in members}) == 1
            for a in arms
            for _, members in fibers
        )
        information[node_id] = classify_information(
            node_id,
            measured=measured_set,
            design_class=class_of[node_id],
            latent_dependent=latent_dependent,
            observation_determined=determined,
        )

    perturbation: dict[str, str] = {}
    for node_id in node_ids:
        if node_id not in free:
            perturbation[node_id] = "not_an_input"
        elif node_id in set(latent):
            perturbation[node_id] = "latent_not_settable"
        elif node_id in set(independently):
            perturbation[node_id] = "independently_perturbed"
        elif node_id in set(set_alone_unreadable):
            perturbation[node_id] = "set_alone_no_shared_readout"
        elif node_id in bundles:
            perturbation[node_id] = "bundled_perturbed"
        else:
            perturbation[node_id] = "never_perturbed"

    dictionary = {
        row["node_id"]: row
        for row in load_tsv(spec.node_dictionary)
        if row["node_id"] in rules
    }
    assayable = tuple(
        n
        for n in node_ids
        if dictionary.get(n, {}).get("measurement_proxies", "")
        not in NON_ASSAYABLE_PROXIES
    )

    return IdentifiabilityFacts(
        model_version=spec.model_version,
        node_ids=node_ids,
        arms=arms,
        controlled=controlled,
        latent=latent,
        unexcited_inputs=unexcited_inputs,
        held_off_inputs=held_off,
        independently_perturbed=tuple(independently),
        set_alone_no_shared_readout=tuple(set_alone_unreadable),
        bundled_perturbed=bundles,
        global_classes=global_classes,
        design_classes=design_classes,
        fibers=fibers,
        information_status=information,
        perturbation_status=perturbation,
        assayable=assayable,
        phenotype_inert=structure.phenotype_inert,
        unread_inputs=structure.unread_inputs,
        measured_nodes=measured_nodes,
        compartment_of=structure.compartment_of,
        label_of={n: dictionary.get(n, {}).get("label", n) for n in node_ids},
        latent_states=states,
    )


# --------------------------------------------------------------------------
# Marginal information gain
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CandidateArm:
    """A proposed additional experimental condition."""

    arm_id: str
    inputs: dict[str, bool]
    rationale: str


def candidate_arms(
    facts: IdentifiabilityFacts, root: Path | None = None
) -> tuple[CandidateArm, ...]:
    """Proposed arms, each one a de-bundling or an unexcited input turned on.

    The construction is mechanical rather than curated, so it cannot quietly
    favour a preferred answer. Two families:

    *De-bundling.* Every input that moves only inside a bundle gets two arms: the
    input alone, and the cocktail minus that input. Either attributes an effect
    to a component rather than to the mixture; both together also test additivity.

    *Excitation.* Every input the design never moves gets an arm turning it on
    against a permissive background.

    A background is chosen as the arm, within its family, that leaves the most
    derived nodes reachable -- not the arm with the most inputs switched on. The
    two differ, and the difference matters: the mifepristone challenge arm has
    the most inputs ON of any arm in the design, and it is also the arm in which
    PGR is blocked and almost nothing downstream can move. Exciting a new input
    against that background would measure it in the one condition where the
    network cannot respond, and would score every proposal at zero.
    """
    spec = resolve_model(facts.model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    order = _topological_order(rules, {n for n in rules if rules[n].strip() == n})
    seeds_latent, _states, mask = _latent_seeds(facts.latent)
    derived = [n for n in rules if rules[n].strip() != n]

    def permissiveness(arm: DesignArm) -> tuple[int, str]:
        columns = _evaluate(rules, order, seeds_latent, mask, arm.inputs)
        return (sum(1 for n in derived if columns[n] != 0), arm.arm_id)

    challenge = [a for a in facts.arms if any("EMBRYO" in n for n in a.on)]
    maternal_arms = [a for a in facts.arms if a not in challenge]
    maternal = max(maternal_arms or facts.arms, key=permissiveness)
    reference = max(challenge or facts.arms, key=permissiveness)

    proposals: list[CandidateArm] = []
    for node_id, bundle in sorted(facts.bundled_perturbed.items()):
        background = reference if any("EMBRYO" in b for b in bundle) else maternal
        base = dict(background.inputs)
        for partner in bundle:
            base[partner] = partner == node_id
        proposals.append(
            CandidateArm(
                arm_id=f"solo_{node_id}",
                inputs=base,
                rationale=(
                    f"{node_id} alone on the {background.arm_id} background; it "
                    f"currently moves only bundled with "
                    f"{', '.join(b for b in bundle if b != node_id)}."
                ),
            )
        )
        held = dict(background.inputs)
        held[node_id] = False
        proposals.append(
            CandidateArm(
                arm_id=f"dropout_{node_id}",
                inputs=held,
                rationale=(
                    f"the {background.arm_id} condition minus {node_id}; isolates "
                    "its contribution by subtraction rather than by addition."
                ),
            )
        )

    for node_id in sorted(facts.unexcited_inputs):
        for background in {
            maternal.arm_id: maternal,
            reference.arm_id: reference,
        }.values():
            base = dict(background.inputs)
            base[node_id] = True
            proposals.append(
                CandidateArm(
                    arm_id=f"{background.arm_id}__{node_id}",
                    inputs=base,
                    rationale=(
                        f"turn on {node_id}, which no run arm ever moves, against "
                        f"{background.arm_id}."
                    ),
                )
            )
    return tuple(sorted(proposals, key=lambda c: c.arm_id))


def _evaluate(
    rules: dict[str, str],
    order: list[str],
    seeds_latent: dict[str, int],
    mask: int,
    inputs: dict[str, bool],
) -> dict[str, int]:
    seeds = dict(seeds_latent)
    for node_id, is_on in inputs.items():
        seeds[node_id] = mask if is_on else 0
    return _columns(rules, order, seeds, mask)


@dataclass(frozen=True)
class GainTable:
    """Marginal gain of each candidate, both currencies reported separately."""

    #: arm_id -> design classes resolved when that arm is added alone.
    arm_structural: tuple[tuple[str, int, str], ...]
    #: node -> observation fibres when that readout is added alone, current arms.
    readout_current: tuple[tuple[str, int, bool], ...]
    #: node -> observation fibres when added on top of every candidate arm.
    readout_extended: tuple[tuple[str, int, bool], ...]
    baseline_design_classes: int
    baseline_fibers: int
    global_ceiling: int
    #: One fibre per latent assignment: full identification of the internal state.
    latent_ceiling: int
    #: Fibres reachable with every proposed arm and every *assayable* readout.
    #: The gap to ``latent_ceiling`` is the part of the internal state no
    #: experiment can resolve while the rules encode it as unobservable.
    assayable_latent_ceiling: int
    #: Fibres reachable if the unobservable placeholders could also be measured.
    unrestricted_latent_ceiling: int
    #: Greedy panel over assayable readouts and proposed arms.
    greedy_arms: tuple[tuple[str, int, int], ...]
    greedy_readouts: tuple[tuple[str, int], ...]
    #: Exact best k-subset of assayable readouts under the greedy arm set.
    exact_readout_panels: tuple[tuple[tuple[str, ...], int], ...]


def compute_gain(
    facts: IdentifiabilityFacts,
    root: Path | None = None,
    *,
    max_exact_panel: int = 3,
) -> GainTable:
    """Marginal information gain, in the two currencies that are not exchangeable.

    A perturbation buys *structural resolution*: how many of the model's distinct
    Boolean functions the design can tell apart at all, bounded above by
    ``P_global``. A readout buys *latent resolution*: how finely the observation
    splits the unknown internal state, bounded above by one fibre per latent
    assignment. Adding them into a single score would let a cheap arm launder
    itself as a measurement, so they stay in separate columns.

    Readout candidates are restricted to assayable nodes. The unrestricted
    optimum is dominated by the four interface relays, which is a correct answer
    to the wrong question: they are declared ``structural_uncertainty`` with
    "bounded stochastic initialization" as their only proxy, so proposing to
    measure them is proposing to measure the thing the model declined to model.
    """
    spec = resolve_model(facts.model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    order = _topological_order(rules, {n for n in rules if rules[n].strip() == n})
    seeds_latent, states, mask = _latent_seeds(facts.latent)

    value = {
        arm.arm_id: _evaluate(rules, order, seeds_latent, mask, arm.inputs)
        for arm in facts.arms
    }
    proposals = candidate_arms(facts, root)
    for candidate in proposals:
        value[candidate.arm_id] = _evaluate(
            rules, order, seeds_latent, mask, candidate.inputs
        )

    current = [arm.arm_id for arm in facts.arms]
    inputs_of = {arm.arm_id: arm.inputs for arm in facts.arms}
    inputs_of.update({c.arm_id: c.inputs for c in proposals})

    def has_embryo(arm_id: str) -> bool:
        return any(
            value
            for node_id, value in inputs_of[arm_id].items()
            if "EMBRYO" in node_id or "TROPHECTODERM" in node_id
        )

    # Which arms each current readout is taken in. A readout added to the panel,
    # or an arm added to the design, is assumed to be measured wherever that
    # readout is already taken -- an embryo-attachment count needs an embryo, and
    # the design only ever samples the secreted proteins from maternal-phase
    # arms. Without this, adding an arm would score zero information gain no
    # matter what it excites, because nothing would be read out in it: the
    # earlier version of this function made exactly that error and scored every
    # interface perturbation at zero.
    families: dict[str, set[bool]] = {}
    for arm in facts.arms:
        for node_id, _ in arm.measured:
            if node_id in rules:
                families.setdefault(node_id, set()).add(has_embryo(arm.arm_id))

    def pairs_for(arm_ids: list[str], extra: list[str]) -> list[tuple[str, str]]:
        pairs = [
            (a, n)
            for n, allowed in families.items()
            for a in arm_ids
            if has_embryo(a) in allowed
        ]
        pairs += [(a, n) for n in extra for a in arm_ids]
        return sorted(set(pairs))

    def design_classes(arm_ids: list[str]) -> int:
        return len(_classes({n: tuple(value[a][n] for a in arm_ids) for n in rules}))

    def fiber_count(arm_ids: list[str], extra: list[str]) -> int:
        pairs = pairs_for(arm_ids, extra)
        seen = {tuple((value[a][n] >> i) & 1 for a, n in pairs) for i in range(states)}
        return len(seen)

    baseline_classes = design_classes(current)
    baseline_fibers = fiber_count(current, [])
    assayable = [n for n in facts.assayable if n not in set(facts.measured_nodes)]
    is_assayable = set(facts.assayable)

    arm_structural = tuple(
        (c.arm_id, design_classes(current + [c.arm_id]), c.rationale) for c in proposals
    )
    all_arms = current + [c.arm_id for c in proposals]
    readout_current = tuple(
        (n, fiber_count(current, [n]), n in is_assayable)
        for n in rules
        if n not in set(facts.measured_nodes)
    )
    readout_extended = tuple(
        (n, fiber_count(all_arms, [n]), n in is_assayable)
        for n in rules
        if n not in set(facts.measured_nodes)
    )

    # Greedy: arms first (they set the ceiling a readout can reach), then
    # assayable readouts. Ties break on arm_id so the panel is deterministic.
    greedy_arms: list[tuple[str, int, int]] = []
    selected = list(current)
    remaining = {c.arm_id for c in proposals}
    while remaining:
        best = max(
            remaining,
            key=lambda a: (
                design_classes(selected + [a]),
                fiber_count(selected + [a], []),
                a,
            ),
        )
        gained = design_classes(selected + [best])
        gained_fibers = fiber_count(selected + [best], [])
        if gained <= design_classes(selected) and gained_fibers <= fiber_count(
            selected, []
        ):
            break
        selected.append(best)
        remaining.discard(best)
        greedy_arms.append((best, gained, gained_fibers))

    greedy_readouts: list[tuple[str, int]] = []
    panel: list[str] = []
    while True:
        best = max(
            (n for n in assayable if n not in panel),
            key=lambda n: (fiber_count(selected, panel + [n]), n),
            default=None,
        )
        if best is None or fiber_count(selected, panel + [best]) <= fiber_count(
            selected, panel
        ):
            break
        panel.append(best)
        greedy_readouts.append((best, fiber_count(selected, panel)))

    # Exact best panel for small k: greedy on a submodular-looking objective is
    # not guaranteed optimal, and the claim "near-minimal panel" has to be
    # checked rather than asserted.
    from itertools import combinations

    exact: list[tuple[tuple[str, ...], int]] = []
    for size in range(1, max_exact_panel + 1):
        best_panel = max(
            combinations(sorted(assayable), size),
            key=lambda c: (fiber_count(selected, list(c)), tuple(reversed(c))),
        )
        exact.append((tuple(best_panel), fiber_count(selected, list(best_panel))))

    return GainTable(
        arm_structural=arm_structural,
        readout_current=readout_current,
        readout_extended=readout_extended,
        baseline_design_classes=baseline_classes,
        baseline_fibers=baseline_fibers,
        global_ceiling=len(facts.global_classes),
        latent_ceiling=states,
        assayable_latent_ceiling=fiber_count(all_arms, assayable),
        unrestricted_latent_ceiling=fiber_count(all_arms, list(rules)),
        greedy_arms=tuple(greedy_arms),
        greedy_readouts=tuple(greedy_readouts),
        exact_readout_panels=tuple(exact),
    )


def adhesion_endpoint_decomposition(
    facts: IdentifiabilityFacts, root: Path | None = None
) -> dict[str, Any]:
    """Why the headline 0.82 is arithmetic on two typed-in numbers.

    The only ``.cfg`` probabilities this module reads. In the hormone-treated
    challenge arm every conjunct of ``OUT_STABLE_ADHESION`` except the two
    positive-route relays is satisfied for every latent assignment with
    ``E_KLF12_HIGH`` off -- which ``baseline.cfg`` sets deterministically -- so
    the endpoint reduces to the disjunction of two independent hand-set draws and
    its converged value is ``1 - (1-p1)(1-p2)`` exactly. An endpoint whose graded
    content is two typed-in numbers cannot localise the mechanism that produced
    it, and that is the claim the figure needs to support.
    """
    spec = resolve_model(facts.model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    order = _topological_order(rules, {n for n in rules if rules[n].strip() == n})
    seeds_latent, states, mask = _latent_seeds(facts.latent)
    priors = parse_cfg_probabilities(spec.baseline_cfg)

    # The arm whose endpoint actually varies with the latent state. The
    # mifepristone challenge arm has more inputs ON but a constant-zero endpoint,
    # so "most inputs" would decompose the one arm that carries no information.
    candidates = [
        a for a in facts.arms if "OUT_STABLE_ADHESION" in {n for n, _ in a.measured}
    ]
    graded = [
        a
        for a in candidates
        if _evaluate(rules, order, seeds_latent, mask, a.inputs)["OUT_STABLE_ADHESION"]
        not in (0, mask)
    ]
    if not graded:
        raise ValueError("no arm leaves OUT_STABLE_ADHESION dependent on latent state")
    arm = max(graded, key=lambda a: (len(a.on), a.arm_id))
    columns = _evaluate(rules, order, seeds_latent, mask, arm.inputs)

    # Restrict to the latent assignments the cfg actually gives weight to: the
    # deterministic latent variables are pinned, the probabilistic ones are free.
    pinned = {n: False for n in facts.latent if n not in priors}
    keep = [
        i
        for i in range(states)
        if all(((seeds_latent[n] >> i) & 1) == int(v) for n, v in pinned.items())
    ]
    positive = [n for n in facts.latent if n in priors and "INTERFACE" in n]
    endpoint_matches = all(
        ((columns["OUT_STABLE_ADHESION"] >> i) & 1)
        == max(
            ((seeds_latent[n] >> i) & 1) for n in positive if "ANTIADHESIVE" not in n
        )
        for i in keep
    )
    carriers = tuple(n for n in positive if "ANTIADHESIVE" not in n)
    product = 1.0
    for node_id in carriers:
        product *= 1.0 - priors[node_id]
    return {
        "arm": arm.arm_id,
        "pinned_latent": pinned,
        "carrier_relays": carriers,
        "carrier_priors": {n: priors[n] for n in carriers},
        "endpoint_equals_disjunction_of_carriers": endpoint_matches,
        "analytic_value": round(1.0 - product, 6),
        "baseline_cfg": str(spec.baseline_cfg.relative_to(root or repo_root())),
    }


def identifiability_summary(facts: IdentifiabilityFacts) -> dict[str, Any]:
    """The caption numbers, in one auditable place."""
    counts: dict[str, int] = {}
    for status in facts.information_status.values():
        counts[status] = counts.get(status, 0) + 1
    return {
        "model_version": facts.model_version,
        "named_nodes": len(facts.node_ids),
        "global_effective_states": len(facts.global_classes),
        "design_effective_states": len(facts.design_classes),
        "states_lost_to_rule_encoding": len(facts.node_ids) - len(facts.global_classes),
        "states_lost_to_design_bundling": (
            len(facts.global_classes) - len(facts.design_classes)
        ),
        "run_arms": len(facts.arms),
        "declared_inputs": len([n for n in facts.node_ids if n.startswith("IN_")]),
        "unit_assumption": (
            "MATCHED-UNIT (hypothetical). Every fibre, observation class, "
            "information status and proposed-panel count assumes one biological "
            "unit carries a single latent assignment through every arm and "
            "assay. The current data do not provide that: adhesion is an "
            "aggregate per-embryo count, the secretion mappings are explicitly "
            "unpaired, and the unit mapping is not recoverable. These counts "
            "therefore describe what a matched-unit design of this shape could "
            "identify, and are NOT claims about what the current data identify."
        ),
        "independently_perturbed_inputs": len(facts.independently_perturbed),
        "set_alone_no_shared_readout_inputs": len(facts.set_alone_no_shared_readout),
        "bundled_perturbed_inputs": len(facts.bundled_perturbed),
        "never_perturbed_inputs": len(facts.unexcited_inputs),
        "latent_variables": len(facts.latent),
        "latent_assignments": facts.latent_states,
        "observation_classes": len(facts.fibers),
        "measured_nodes": len(facts.measured_nodes),
        "assayable_nodes": len(facts.assayable),
        "phenotype_inert_nodes": len(facts.phenotype_inert),
        "unread_inputs": len(facts.unread_inputs),
        **{f"status_{k}": v for k, v in sorted(counts.items())},
    }
