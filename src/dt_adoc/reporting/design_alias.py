"""Which nodes a *given* experimental design cannot tell apart, and why.

``identifiability.py`` answers this for the design the repository has already
run: the arms it holds an observation for. This module answers it for an
arbitrary declared arm set -- in particular the practical four-arm plan in
``config/planned_design.yaml``, which is neither a subset nor a superset of the
recorded design -- and asks what a fifth arm would add to it.

The partition vocabulary is inherited unchanged, because the distinction it
draws is the whole point of the figure this module feeds:

``P_global``
    nodes implementing the identical Boolean function over all free variables.
    Merged by the *rules*. No arm separates them; only a rule change does.
``P_design``
    nodes taking identical values across the arms of the design under
    evaluation. A class here that is not a class in ``P_global`` is merged by
    the *design*, and another arm can split it.

A third category sits outside both and must not be read as either. Five free
variables are *latent*: no arm assigns them, so their per-unit value is unknown.
Four of those are the ``X_*_RELAY`` interface placeholders. They are separated
here not by their name but by the property that makes them placeholders --
``identifiability.NON_ASSAYABLE_PROXIES``, the node dictionary saying in its own
words that they have no physical assay target. Colouring them like an ordinary
aliased molecular node would tell a reader to go and measure the one thing the
model declined to model.

NOTHING HERE SIMULATES. Every number is an exhaustive enumeration over the
model's free variables, read from ``network.bnd`` and the condition cfgs, so no
claim depends on the unresolved endpoint horizon
(``docs/endpoint_convergence_finding.md``).

ONE ENUMERATOR. The four private helpers imported below are the canonical ones
``identifiability.py`` uses. They are imported rather than reimplemented on
purpose: a second copy of the evaluator could drift from the model and still
produce a plausible-looking figure, which is exactly the failure this module
exists to make visible. ``tests/unit/test_design_alias.py`` pins the reuse by
asserting that this module, handed the recorded six arms, reproduces
``load_identifiability(...).design_classes`` exactly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting.identifiability import (
    DesignArm,
    IdentifiabilityFacts,
    _classes,
    _evaluate,
    _latent_seeds,
    _observed_arms,
    _parse_cfg_inputs,
    _topological_order,
    load_identifiability,
    perturbation_split,
)

#: Node categories the figure is allowed to draw, in precedence order. The first
#: two are properties of the *rules*, the third of the *design*, the last two of
#: the free-variable split. A node gets exactly one.
CATEGORY_ORDER = (
    "interface_placeholder",
    "latent_biological",
    "structural_alias",
    "design_alias",
    "resolved_singleton",
)


@dataclass(frozen=True)
class PlannedArm:
    """One condition of a declared plan, in both phases the repository runs."""

    arm_id: str
    label: str
    #: ``(phase, cfg_stem)`` pairs; both phases unless the variant restricts it.
    cfgs: tuple[tuple[str, str], ...]
    interpretation: str
    #: True when some cfg of this arm carries an observation the repository
    #: records. Derived from calibration.yaml and observation_model_map.tsv --
    #: never declared in config/planned_design.yaml.
    has_recorded_observation: bool
    #: Which of this arm's cfgs carry one, and what records it.
    recorded_sources: tuple[str, ...]


@dataclass(frozen=True)
class DesignAliasFacts:
    """The partitions a declared design induces, and how they differ from P_global."""

    model_version: str
    plan_id: str
    plan_label: str
    arms: tuple[PlannedArm, ...]
    #: Condition cfg stems entering the partition, in evaluation order.
    cfg_stems: tuple[str, ...]
    node_ids: tuple[str, ...]
    latent: tuple[str, ...]
    global_classes: tuple[tuple[str, ...], ...]
    design_classes: tuple[tuple[str, ...], ...]
    #: node -> one of ``CATEGORY_ORDER``.
    category: dict[str, str]
    #: node -> compartment band used by the biological layout.
    compartment_of: dict[str, str]
    label_of: dict[str, str]
    #: Nodes the repository records an observation for, carried through from
    #: identifiability.py so that "does this arm separate two things we actually
    #: measure?" is answered from the observation tables, never from a name.
    measured_nodes: tuple[str, ...]
    #: Arms declared by the plan that carry no recorded observation.
    planned_not_recorded: tuple[str, ...]
    #: Arms the recorded design has that the plan drops.
    recorded_not_planned: tuple[str, ...]
    #: Inputs the plan isolates AND whose arms share a measured readout. A plan
    #: carries no recorded observation, so under the plan as declared this is
    #: empty: isolating an input is not the same as being able to read its
    #: effect, and the two must not be reported as one.
    independently_perturbed: tuple[str, ...]
    #: Inputs the plan isolates but for which no readout is attached yet.
    set_alone_no_shared_readout: tuple[str, ...]
    bundled_perturbed: dict[str, tuple[str, ...]]
    unexcited_inputs: tuple[str, ...]

    @property
    def design_class_of(self) -> dict[str, tuple[str, ...]]:
        return {n: members for members in self.design_classes for n in members}

    @property
    def global_class_of(self) -> dict[str, tuple[str, ...]]:
        return {n: members for members in self.global_classes for n in members}


#: The one role `config/planned_design.yaml` may declare. Named rather than
#: implied so that repurposing the file is a loud failure: a config that listed
#: a chosen prospective arm would be a different artifact with different
#: provenance requirements, and it must not inherit this one's readers.
PLAN_ROLE = "as_declared_plan_baseline_not_a_prospective_selection"


def load_plan(
    root: Path | None = None,
    variant: str | None = None,
    *,
    model_version: str | None = None,
) -> tuple[dict[str, Any], tuple[PlannedArm, ...]]:
    """Read ``config/planned_design.yaml`` and resolve it against the model.

    ``variant`` selects a ``sensitivity_variants`` entry; ``None`` is the plan as
    declared. A variant may restrict which phases count, never which conditions:
    dropping a condition would be a different plan, not a sensitivity.

    ``model_version`` resolves the same declared plan against another model --
    the U5 audit re-runs it on the v0.5 scaffold -- and is returned in the
    document's ``model_version`` so everything downstream reads one value. The
    plan itself is unchanged, and every arm must still name a condition cfg the
    chosen model carries.
    """
    active_root = root or repo_root()
    document = yaml.safe_load(
        (active_root / "config" / "planned_design.yaml").read_text(encoding="utf-8")
    )
    # The file is the AS-DECLARED plan and is the baseline candidates are scored
    # against. It is not, and may not become, a selection of the prospective
    # arm: the plan's fourth arm is anti-SPP1, that arm carries no recorded
    # observation, and by both scoring currencies the design analysis points
    # elsewhere. Checking the declared role on load means a later edit that
    # repurposes the file fails here rather than being read as a recommendation
    # by code that never asked what it was.
    if document.get("role") != PLAN_ROLE:
        raise ValueError(
            "config/planned_design.yaml must declare "
            f"role: {PLAN_ROLE!r}; found {document.get('role')!r}. This file is "
            "the declared-plan baseline, never a prospective-arm selection -- "
            "that decision belongs to the design analysis, not to a config."
        )
    phases = ("maternal", "challenge")
    if variant is not None:
        variants = document.get("sensitivity_variants", {})
        if variant not in variants:
            raise ValueError(
                f"config/planned_design.yaml declares no sensitivity variant "
                f"'{variant}'; known: {sorted(variants)}"
            )
        phases = tuple(variants[variant].get("use_phases", phases))

    if model_version is not None:
        document = {**document, "model_version": model_version}
    spec = resolve_model(document["model_version"], active_root)
    observed = _observed_arms(active_root, spec.condition_dir)

    arms: list[PlannedArm] = []
    for entry in document["arms"]:
        selected: list[tuple[str, str]] = []
        for phase in phases:
            stem = entry.get(f"{phase}_cfg")
            if stem is None:
                continue
            if not (spec.condition_dir / f"{stem}.cfg").exists():
                raise ValueError(
                    f"config/planned_design.yaml arm '{entry['arm_id']}' names "
                    f"condition cfg '{stem}', which {document['model_version']} "
                    "does not carry. A plan may not invent a condition."
                )
            selected.append((phase, stem))
        if not selected:
            raise ValueError(
                f"config/planned_design.yaml arm '{entry['arm_id']}' selects no "
                f"cfg for phases {phases}."
            )
        sources = tuple(
            sorted(
                {
                    source
                    for _phase, stem in selected
                    for _node, source in observed.get(stem, [])
                }
            )
        )
        arms.append(
            PlannedArm(
                arm_id=entry["arm_id"],
                label=entry["label"],
                cfgs=tuple(selected),
                interpretation=entry.get("interpretation", ""),
                has_recorded_observation=bool(sources),
                recorded_sources=sources,
            )
        )
    return document, tuple(arms)


class _Enumerator:
    """The model's free-variable enumeration, built once and reused.

    Holds the rules, the topological order and the latent seed columns, so that
    evaluating fifty candidate arms costs fifty network evaluations rather than
    fifty rebuilds of the model.
    """

    def __init__(self, model_version: str, root: Path | None = None) -> None:
        self.root = root or repo_root()
        self.spec = resolve_model(model_version, self.root)
        self.rules = parse_bnd_rules(self.spec.network_bnd)
        self.free = {n for n in self.rules if self.rules[n].strip() == n}
        self.order = _topological_order(self.rules, self.free)
        self.inputs = tuple(sorted(n for n in self.free if n.startswith("IN_")))
        self.latent = tuple(n for n in self.free if not n.startswith("IN_"))
        self.seeds, self.states, self.mask = _latent_seeds(self.latent)
        self.baseline = _parse_cfg_inputs(self.spec.baseline_cfg)
        self._columns: dict[str, dict[str, int]] = {}

    def inputs_for(self, stem: str) -> dict[str, bool]:
        """A condition cfg read as an overlay on ``baseline.cfg``, inputs only.

        The same overlay semantics ``identifiability.load_design`` uses: a
        condition cfg lists only what the condition changes, so reading it alone
        would leave every unmentioned input looking unassigned.
        """
        overlay = {
            k: v
            for k, v in _parse_cfg_inputs(
                self.spec.condition_dir / f"{stem}.cfg"
            ).items()
            if k in self.free
        }
        assignment = {n: self.baseline.get(n, False) for n in self.inputs}
        assignment.update(overlay)
        return assignment

    def columns(self, inputs: dict[str, bool]) -> dict[str, int]:
        # Keyed over EVERY free variable, not over `self.inputs`. `inputs_for`
        # admits any free variable a condition cfg assigns, so a cfg that seeded
        # `E_KLF12_HIGH` or an interface relay would produce two assignments the
        # `IN_`-only key could not tell apart -- a silent cache collision
        # returning one arm's columns for another, and a wrong partition with no
        # error. No committed cfg does that today; the key should not be the
        # only reason it stays true.
        key = ";".join(f"{k}={int(inputs.get(k, False))}" for k in sorted(self.free))
        if key not in self._columns:
            self._columns[key] = _evaluate(
                self.rules, self.order, self.seeds, self.mask, inputs
            )
        return self._columns[key]

    def partition(
        self, assignments: list[dict[str, bool]]
    ) -> tuple[tuple[str, ...], ...]:
        """P_design for an arbitrary arm set: nodes equal across every arm."""
        evaluated = [self.columns(a) for a in assignments]
        return _classes({n: tuple(c[n] for c in evaluated) for n in self.rules})


def _categorise(
    node_id: str,
    *,
    global_class: tuple[str, ...],
    design_class: tuple[str, ...],
    latent: frozenset[str],
    assayable: frozenset[str],
) -> str:
    """One category per node, in ``CATEGORY_ORDER`` precedence.

    Precedence matters and is not arbitrary. A latent relay is *also* a design
    singleton, and drawing it as "resolved" would be the single most misleading
    thing this figure could say: its value is unknown in every arm, which is the
    opposite of resolved. So the free-variable split is tested first.

    Below that, the rules outrank the design. A node merged by ``P_global`` is
    reported as a structural alias even though it is necessarily also merged by
    ``P_design``, because a reader deciding what to do next needs to know that
    another arm will not help.
    """
    if node_id in latent:
        return (
            "interface_placeholder" if node_id not in assayable else "latent_biological"
        )
    if len(global_class) > 1:
        return "structural_alias"
    if len(design_class) > 1:
        return "design_alias"
    return "resolved_singleton"


def load_design_alias(
    root: Path | None = None,
    variant: str | None = None,
    *,
    facts: IdentifiabilityFacts | None = None,
    model_version: str | None = None,
) -> DesignAliasFacts:
    """Everything Figure A is entitled to draw, computed from the model.

    ``model_version`` overrides the plan's declared model; see ``load_plan``.
    """
    active_root = root or repo_root()
    document, arms = load_plan(active_root, variant, model_version=model_version)
    model_version = document["model_version"]
    recorded = facts or load_identifiability(model_version, active_root)
    enumerator = _Enumerator(model_version, active_root)

    stems = tuple(stem for arm in arms for _phase, stem in arm.cfgs)
    assignments = [enumerator.inputs_for(stem) for stem in stems]
    design_classes = enumerator.partition(assignments)

    latent = frozenset(recorded.latent)
    assayable = frozenset(recorded.assayable)
    global_of = {n: members for members in recorded.global_classes for n in members}
    design_of = {n: members for members in design_classes for n in members}

    category = {
        node_id: _categorise(
            node_id,
            global_class=global_of[node_id],
            design_class=design_of[node_id],
            latent=latent,
            assayable=assayable,
        )
        for node_id in recorded.node_ids
    }

    # The plan's own perturbation structure, by the same rule the recorded
    # design is split with. A DesignArm is built here only to reuse that rule.
    #
    # `measured` carries the observations the repository actually records for
    # each planned cfg, read from the same `_observed_arms` the recorded design
    # uses. Passing an empty set instead would have made `independently_
    # perturbed` empty for every conceivable plan, which is not a computed
    # finding but an artefact of the construction -- and it would have been
    # wrong here: two of this plan's own cfgs, `adhesion_challenge_hormone_
    # treated` and `adhesion_challenge_hormone_treated_mifepristone`, differ in
    # IN_MIFEPRISTONE alone and both carry a recorded OUT_STABLE_ADHESION
    # readout, so that contrast IS effect-attributable.
    observed = _observed_arms(active_root, enumerator.spec.condition_dir)
    as_arms = tuple(
        DesignArm(
            arm_id=stem,
            cfg=stem,
            inputs=assignment,
            measured=tuple(sorted(set(observed.get(stem, [])))),
        )
        for stem, assignment in zip(stems, assignments, strict=True)
    )
    controlled = tuple(
        n for n in enumerator.inputs if any(n in a.inputs for a in as_arms)
    )
    unexcited = tuple(
        n for n in controlled if len({a.inputs[n] for a in as_arms}) == 1
    ) + tuple(n for n in enumerator.inputs if n not in set(controlled))
    independently, set_alone_unreadable, bundles = perturbation_split(
        as_arms, controlled, unexcited
    )

    recorded_stems = {arm.arm_id for arm in recorded.arms}
    return DesignAliasFacts(
        model_version=model_version,
        plan_id=document["plan_id"],
        plan_label=document["plan_label"],
        arms=arms,
        cfg_stems=stems,
        node_ids=recorded.node_ids,
        latent=recorded.latent,
        global_classes=recorded.global_classes,
        design_classes=design_classes,
        category=category,
        compartment_of=recorded.compartment_of,
        label_of=recorded.label_of,
        measured_nodes=recorded.measured_nodes,
        planned_not_recorded=tuple(
            arm.arm_id for arm in arms if not arm.has_recorded_observation
        ),
        recorded_not_planned=tuple(sorted(recorded_stems - set(stems))),
        independently_perturbed=independently,
        set_alone_no_shared_readout=set_alone_unreadable,
        bundled_perturbed=bundles,
        unexcited_inputs=unexcited,
    )


# --------------------------------------------------------------------------
# Candidate fifth arms
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FifthArm:
    """A candidate addition to the plan, and what it would separate."""

    candidate_id: str
    label: str
    family: str
    rationale: str
    inputs: dict[str, bool]
    #: Committed condition cfg with exactly these input assignments, if one
    #: exists. Empty means the arm would need a new cfg before it could be run.
    committed_cfg: str
    baseline_classes: int
    classes_after: int
    #: Design classes the candidate splits, each as ``(before, parts)``.
    splits: tuple[tuple[tuple[str, ...], tuple[tuple[str, ...], ...]], ...]
    #: Pairs of *measured* nodes this arm pulls into different classes.
    #:
    #: The currency that decides whether an arm is worth running, and it is not
    #: the same as ``gain``. An arm can add five classes and separate no two
    #: quantities the experiment actually reads, in which case everything it
    #: resolves is resolved only in the model. Computed from the repository's
    #: recorded observations, so it cannot be aimed at a favoured answer.
    separated_measured_pairs: tuple[tuple[str, str], ...]

    @property
    def gain(self) -> int:
        return self.classes_after - self.baseline_classes

    @property
    def newly_separable(self) -> tuple[str, ...]:
        """Nodes that leave a class they currently share with another node.

        Every member of every class the candidate splits. ``splits`` only
        retains classes the candidate breaks into two or more parts, so every
        node in one of them ends up in a strictly smaller class than it started
        in, and every one of them has become separable from something.
        """
        return tuple(sorted(n for before, _parts in self.splits for n in before))


def candidate_fifth_arms(
    facts: DesignAliasFacts,
    root: Path | None = None,
    *,
    enumerator: _Enumerator | None = None,
) -> tuple[FifthArm, ...]:
    """Every arm that could be added to the plan, scored against the plan itself.

    Two families, constructed mechanically so the ranking cannot quietly favour
    a preferred answer:

    *excitation* -- every declared input the plan never moves, turned on against
    each of the plan's own backgrounds. This is where HAND2 loss, ER stress,
    high ECM stiffness and hCG come from.

    *de-bundling* -- every input the plan moves only inside a bundle, both alone
    and as the bundle minus that input. This is where "MPA alone" and "cocktail
    minus cAMP" come from.

    Scored against *this plan*, not against the recorded design. The two give
    different answers, because the plan excites IN_ANTI_SPP1, which no recorded
    arm moves, and drops the E2-priming arm, which is the only recorded arm that
    separates E2 from the progestin cocktail.

    ``committed_cfg`` is matched by input assignment, not by name: it is the
    check that a candidate this analysis recommends is an experiment the model
    can already express, rather than one that would need a new cfg written first.
    """
    active_root = root or repo_root()
    enumerate_ = enumerator or _Enumerator(facts.model_version, active_root)
    assignments = [enumerate_.inputs_for(stem) for stem in facts.cfg_stems]
    baseline = enumerate_.partition(assignments)
    baseline_count = len(baseline)

    committed = {
        stem: enumerate_.inputs_for(stem)
        for stem in sorted(p.stem for p in enumerate_.spec.condition_dir.glob("*.cfg"))
    }

    def match(inputs: dict[str, bool]) -> str:
        for stem, reference in committed.items():
            if all(
                inputs.get(k, False) == reference.get(k, False)
                for k in enumerate_.inputs
            ):
                return stem
        return ""

    # Backgrounds: the plan's own arms, split by whether they stage an embryo.
    # A new input excited on an embryo-free background cannot move anything that
    # needs contact, and one excited on the mifepristone background is measured
    # in the condition where the network cannot respond -- the same trap
    # `identifiability.candidate_arms` documents.
    backgrounds = {stem: enumerate_.inputs_for(stem) for stem in facts.cfg_stems}

    proposals: list[tuple[str, str, str, str, dict[str, bool]]] = []
    already_moved = set(facts.independently_perturbed) | set(
        facts.set_alone_no_shared_readout
    )
    for node_id in sorted(set(facts.unexcited_inputs) - already_moved):
        for stem, background in backgrounds.items():
            assignment = dict(background)
            assignment[node_id] = True
            proposals.append(
                (
                    f"{stem}__{node_id}",
                    f"{node_id.removeprefix('IN_')} on {stem}",
                    "excitation",
                    (f"turn on {node_id}, which the plan never moves, against {stem}."),
                    assignment,
                )
            )

    for node_id, bundle in sorted(facts.bundled_perturbed.items()):
        for stem, background in backgrounds.items():
            if not background.get(node_id, False):
                continue
            solo = dict(background)
            for partner in bundle:
                solo[partner] = partner == node_id
            partners = ", ".join(b for b in bundle if b != node_id)
            proposals.append(
                (
                    f"solo_{node_id}__{stem}",
                    f"{node_id.removeprefix('IN_')} alone on {stem}",
                    "de-bundling",
                    (
                        f"{node_id} alone on the {stem} background; the plan "
                        f"moves it only bundled with {partners}."
                    ),
                    solo,
                )
            )
            held = dict(background)
            held[node_id] = False
            proposals.append(
                (
                    f"dropout_{node_id}__{stem}",
                    f"{stem} minus {node_id.removeprefix('IN_')}",
                    "de-bundling",
                    (
                        f"the {stem} condition minus {node_id}; isolates its "
                        "contribution by subtraction rather than by addition."
                    ),
                    held,
                )
            )

    results: list[FifthArm] = []
    seen: set[str] = set()
    for candidate_id, label, family, rationale, assignment in proposals:
        key = ";".join(
            f"{k}={int(assignment.get(k, False))}" for k in enumerate_.inputs
        )
        if key in seen:
            continue
        seen.add(key)
        extended = enumerate_.partition(assignments + [assignment])
        splits = tuple(
            (before, tuple(p for p in extended if set(p) <= set(before)))
            for before in baseline
            if len([p for p in extended if set(p) <= set(before)]) > 1
        )
        measured = set(facts.measured_nodes)
        pairs = tuple(
            sorted(
                (left, right)
                for before, parts in splits
                for index, part in enumerate(parts)
                for raw_left in sorted(measured & set(part))
                for other in parts[index + 1 :]
                for raw_right in sorted(measured & set(other))
                # Sorted within the pair: the same separation must not appear
                # as both (A, B) and (B, A) in the published table.
                for left, right in [tuple(sorted((raw_left, raw_right)))]
            )
        )
        results.append(
            FifthArm(
                candidate_id=candidate_id,
                label=label,
                family=family,
                rationale=rationale,
                inputs=assignment,
                committed_cfg=match(assignment),
                baseline_classes=baseline_count,
                classes_after=len(extended),
                splits=splits,
                separated_measured_pairs=pairs,
            )
        )
    return tuple(
        sorted(results, key=lambda c: (-c.gain, c.committed_cfg == "", c.candidate_id))
    )


def design_alias_summary(
    facts: DesignAliasFacts, candidates: tuple[FifthArm, ...]
) -> dict[str, Any]:
    """The counts the figure captions and the note are allowed to state."""
    sizes = [len(c) for c in facts.design_classes]
    categories = {
        name: sum(1 for value in facts.category.values() if value == name)
        for name in CATEGORY_ORDER
    }
    best = max((c.gain for c in candidates), default=0)
    separating = [c for c in candidates if c.separated_measured_pairs]
    return {
        "model_version": facts.model_version,
        "plan_id": facts.plan_id,
        "named_nodes": len(facts.node_ids),
        "global_effective_states": len(facts.global_classes),
        "design_effective_states": len(facts.design_classes),
        "planned_conditions": len(facts.arms),
        "planned_cfgs": len(facts.cfg_stems),
        "largest_design_class": max(sizes),
        "design_classes_larger_than_one": sum(1 for s in sizes if s > 1),
        "planned_not_recorded": list(facts.planned_not_recorded),
        "inputs_isolated_without_a_shared_readout": list(
            facts.set_alone_no_shared_readout
        ),
        "recorded_not_planned": list(facts.recorded_not_planned),
        "categories": categories,
        "candidates_evaluated": len(candidates),
        "best_fifth_arm_gain": best,
        "best_fifth_arms": [c.candidate_id for c in candidates if c.gain == best],
        "measured_nodes": list(facts.measured_nodes),
        "candidates_separating_two_measured_nodes": len(separating),
        "best_gain_among_arms_separating_measured_nodes": max(
            (c.gain for c in separating), default=0
        ),
        "arms_separating_measured_nodes": [
            c.candidate_id
            for c in separating
            if c.gain == max((x.gain for x in separating), default=0)
        ],
    }
