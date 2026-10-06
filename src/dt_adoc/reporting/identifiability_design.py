"""Which readouts split the Stage 4b veto classes, and what each one buys.

This is the analysis layer for the identifiability-driven experimental-design
unit. It answers one question mechanically: given that the current observed set
``O`` collapses several single-node vetoes into one class
(``docs/stage4b/v060_veto_expressivity.tsv``), **which additional measurement
would separate which of them**, and which separations no measurement can buy.

Seven tables are produced.

``alias_pairs.tsv``
    Every pair of distinct targets that share an observed class, with the nodes
    that separate them and a *reason* for the collapse. The reason is derived,
    not asserted, and it is the taxonomy the unit turns on:

    ``rule_identical_everywhere``
        No node of the network separates the pair under any declared context or
        scenario. No measurement can ever split them; only a rule change can.
    ``separable_only_at_targets``
        The only separating nodes are the perturbed nodes themselves, so the two
        vetoes have *no distinct downstream consequence*. Splitting them means
        measuring engagement, which identifies the agent rather than the
        mechanism.
    ``separable_downstream``
        Separating nodes exist that neither veto targets. These are the genuine
        "``O`` is too small" cases, and the ones an experiment can fix.

``readout_value.tsv``
    For each candidate readout, the number of classes before and after adding it
    to ``O``, and which alias pairs it breaks. ``assayable`` is carried over from
    ``docs/identifiability/candidate_readouts.tsv`` rather than re-decided here.

``perturbation_readout_matrix.tsv``
    The long-form matrix: one row per (perturbation, readout) pair that does
    useful work, naming the distinction it provides.

``minimal_identifying_panel.tsv``
    The smallest assayable readout set identifying each target within its class,
    searched exhaustively so a reported panel is minimal and not merely
    sufficient. Structural, like the two tables above it.

``panel_structural_value.tsv``
    The nested-panel frontier. **Every number in it is a STRUCTURAL capability,
    not an experimental yield**: it says how much of the veto degeneracy would
    become resolvable *if* ``O`` were enlarged, which is a prerequisite for an
    experiment and not a result of one.

``design_yield.tsv``
    What a *named design* — a set of veto arms actually run, with a set of
    readouts actually measured — resolves. This is the experimental quantity,
    and it is deliberately separate from the structural one above, because
    conflating them is the error this repository keeps having to relearn.
    ``experiments.variant_discrimination`` states it exactly: "structural
    distinguishability is not experimental distinguishability." An alias pair is
    counted resolved only when the design **runs BOTH of its vetoes** and
    measures a node that separates them: the pair is a claim about two
    interventions, so refuting it needs both signatures rather than one
    signature and a prediction for the other. A panel added to arms that run no
    new veto resolves no alias pair, however many it would make resolvable, and
    no single-perturbation design resolves one at all.

    The two variant columns **partition** the variants a design touches, and
    both count distinct ``variant_id``s.
    ``variants_discriminated_within_design`` holds those exposed under the
    design's own controlled-input settings;
    ``variants_needing_an_extra_input_arm`` holds only the rest. A variant
    already discriminated within the design does **not** appear in the second
    column, however many further input settings would also expose it — saying
    otherwise made "needing an extra arm" false for it and double-counted it
    across the pair. ``tests/unit/test_identifiability_design.py`` pins the
    disjointness.

``variant_arm_discrimination.tsv``
    For each **registered** competing rule variant and each perturbation arm
    *separately*, which readouts tell the variant from its baseline. STAT3 and
    LIF are never collapsed into one arm: under the registered ``GP130-b``
    (``E_GP130_STAT3 = E_LIF or X_IL11``) they make opposite predictions, so a
    row naming both at once would be false for one of them.

No variant is invented here. They are read from two registered sources: the
model's own ``rule_variants.tsv`` and the Gate-3 ``VARIANTS`` tuple in
``experiments.variant_discrimination``. A rule family the repository has
deliberately declined to write — notably the IL-11/ANXA2 executor, which
``deep_research_adhesion_model_2026-09-11.candidate-node-dispositions.tsv``
refuses because writing it "would invent the functional link" — is **not**
reconstructed here in order to score it.

Why the computation is exact, and what it does not say, are the same as for
``veto_expressivity``, whose parser, context enumeration and marginal
computation this module reuses rather than reimplements. In particular the
classes are relative to the declared conditions and to the observation map, and
transients are not read as distinguishability.

**Nothing here is a model, observation-map or admission change.** It writes only
under ``docs/identifiability_design/``, runs no MaBoSS, and is deliberately
outside ``concordance.simulate.IMPLEMENTATION_GLOBS``: it produces no simulation
result, so it must not trigger the four-artifact regeneration.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import re
import sys
from pathlib import Path

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.adjudication import AUDIT_MODEL_VERSION
from dt_adoc.reporting import veto_expressivity as vx


class ExpressivityConfigError(RuntimeError):
    """A required input to this analysis is missing or unusable.

    Raised rather than degraded: every table here is provenance for an
    experimental recommendation, so incomplete coverage must stop the write.
    """


OUTPUT_DIR = Path("docs/identifiability_design")
ALIAS_PATH = OUTPUT_DIR / "alias_pairs.tsv"
READOUT_PATH = OUTPUT_DIR / "readout_value.tsv"
MATRIX_PATH = OUTPUT_DIR / "perturbation_readout_matrix.tsv"
PANEL_PATH = OUTPUT_DIR / "panel_structural_value.tsv"
YIELD_PATH = OUTPUT_DIR / "design_yield.tsv"
VARIANT_PATH = OUTPUT_DIR / "variant_arm_discrimination.tsv"
MINIMAL_PATH = OUTPUT_DIR / "minimal_identifying_panel.tsv"

#: Assayability is a property of the assay estate, not of the rules, so it is
#: read from the committed identifiability layer rather than re-decided here.
#: That table is keyed on v0.4.0 node ids; a node it does not mention is
#: reported as ``unknown`` rather than silently assumed assayable.
ASSAYABLE_SOURCE = Path("docs/identifiability/candidate_readouts.tsv")

#: Assayability overrides, each with the provenance that justifies it.
#:
#: ``candidate_readouts.tsv`` answers "is there an assay target for this node",
#: and for ``E_KLF12_HIGH`` the honest answer to that narrower question is yes:
#: the KLF12 transcript is measurable and present in the deposited object. But
#: this analysis needs a different question answered — can a *present*
#: measurement be mapped onto the node's Boolean high/low state — and for this
#: node the repository has already tested that and failed.
#: ``docs/scrna/klf12_prior_finding.md`` records that the existing scRNA
#: establishes no interpretable boundary and no measured prior: 83.2% of
#: epithelial cells carry no KLF12, of the 3,429 that do 65.5% carry exactly one
#: raw UMI, and the multimodality the detected values have is the integer UMI
#: lattice. The pre-registered criterion also fired on a population simulated
#: with no latent state at all, 25 times out of 25.
#:
#: So the node is REPRESENTED but its observation mapping is unresolved, which
#: is neither "assayable" nor "no assay target". It is recorded as a third
#: value, and a node carrying it is excluded from every measurement panel and
#: from the minimal-panel search. The override is deliberately explicit rather
#: than a change to ``candidate_readouts.tsv``: that artefact belongs to the
#: Gate-3 identifiability unit and answers its own question correctly.
BLOCKED_NO_VALIDATED_MAPPING = "blocked_no_validated_mapping"
ASSAYABILITY_OVERRIDES: dict[str, tuple[str, str]] = {
    "E_KLF12_HIGH": (
        BLOCKED_NO_VALIDATED_MAPPING,
        "docs/scrna/klf12_prior_finding.md",
    ),
}

ALIAS_COLUMNS = (
    "observed_class",
    "target_a",
    "target_b",
    "collapse_reason",
    "separating_nodes",
    "separating_nodes_assayable",
    "separating_nodes_beyond_targets",
)
READOUT_COLUMNS = (
    "node_id",
    "assayable",
    "classes_with_node_added",
    "null_arms_with_node_added",
    "alias_pairs_broken",
    "pairs_broken_detail",
)
MATRIX_COLUMNS = (
    "perturbation",
    "readout",
    "readout_moves_under_perturbation",
    "rivals_separated",
    "distinction",
)
PANEL_COLUMNS = (
    "panel",
    "added_readouts",
    "new_assay_classes",
    "non_null_classes_structural",
    "null_arms_structural",
    "alias_pairs_made_resolvable_structural",
)
YIELD_COLUMNS = (
    "design",
    "execution_context",
    "latent_scenario",
    "veto_arms_run",
    "readouts_measured",
    "new_assay_classes",
    "alias_pairs_resolved",
    "alias_pairs_resolved_detail",
    "variants_discriminated_within_design",
    "variants_within_design_detail",
    "variants_needing_an_extra_input_arm",
    "variants_needing_extra_arm_detail",
)
MINIMAL_COLUMNS = (
    "target",
    "rivals_in_class",
    "minimal_panel",
    "panel_size",
    "panel_all_assayable",
)
VARIANT_COLUMNS = (
    "variant_id",
    "axis",
    "baseline_id",
    "rule_change",
    "extra_free_inputs",
    "setting_is_current_design",
    "perturbation_arm",
    "context",
    "scenario",
    "separating_readouts",
    "separating_readouts_assayable",
)

#: ``E_KLF12_HIGH`` is deliberately NOT a panel readout. It is a hand-set
#: Boolean latent, and ``docs/scrna/klf12_prior_finding.md`` records that the
#: existing scRNA establishes no interpretable high/low boundary and no measured
#: prior for it, so listing the KLF12 transcript as an observation of that node
#: would claim a mapping the repository has tested and not obtained. It stays a
#: labelled latent SCENARIO instead; see ``scenario_label``.
#:
#: Panels are named here so the frontier is reproducible rather than retyped
#: into prose. ``new_assay_classes`` counts capabilities the platform does not
#: have, not analytes: the outlet immunoassay format already exists, so a new
#: analyte in it is not a new class, while surface staining is.
PANELS: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    ("current_O", 0, ()),
    (
        "A_scrna_expression",
        0,
        ("E_LIF", "E_HBEGF", "E_IHH", "E_SPP1_EXPR", "S_SPP1"),
    ),
    (
        "B_A_plus_free_spp1",
        0,
        (
            "E_LIF",
            "E_HBEGF",
            "E_IHH",
            "E_SPP1_EXPR",
            "S_SPP1",
            "X_SPP1_LUMEN_FREE",
        ),
    ),
    ("C_B_plus_cd98", 1, ()),
    ("D_C_plus_dag1_cleaved", 2, ()),
    ("E_D_plus_proliferation", 3, ()),
    ("F_E_plus_taz", 4, ()),
)
#: The incremental readout each panel adds beyond its predecessor, kept apart
#: from ``PANELS`` so the nesting is explicit and a typo cannot silently make a
#: panel non-nested.
PANEL_INCREMENTS: dict[str, str] = {
    "C_B_plus_cd98": "E_CD98_CD9",
    "D_C_plus_dag1_cleaved": "E_DAG1_CLEAVED",
    "E_D_plus_proliferation": "E_ESTROGENIC_PROLIFERATION",
    "F_E_plus_taz": "S_TAZ_ECM",
}

#: The named designs §7 of the companion document ranks. ``veto_arms`` is what
#: the design actually perturbs — the empty tuple is the whole point of
#: ``design_yield.tsv``, because a design that runs no new veto resolves no
#: alias pair.
#: The condition a one-shot ADOC experiment would actually be run in. A yield is
#: reported FOR a condition; a yield unioned over every declared condition would
#: promise information from arms nobody runs.
EXECUTION_CONTEXT = "adhesion_challenge_hormone_treated"

DESIGNS: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("1_readout_only_existing_arms", (), "B_A_plus_free_spp1", EXECUTION_CONTEXT),
    ("2_pc6_veto", ("E_PC6",), "D_C_plus_dag1_cleaved", EXECUTION_CONTEXT),
    ("3_hand2_veto", ("S_HAND2",), "B_A_plus_free_spp1", EXECUTION_CONTEXT),
    (
        "3b_hand2_veto_with_proliferation",
        ("S_HAND2",),
        "E_D_plus_proliferation",
        EXECUTION_CONTEXT,
    ),
    ("4_stat3_veto", ("E_GP130_STAT3",), "C_B_plus_cd98", EXECUTION_CONTEXT),
    ("5_lif_veto", ("E_LIF",), "C_B_plus_cd98", EXECUTION_CONTEXT),
    # Two arms, shown so the cost of actually de-aliasing is visible rather than
    # implied: an alias pair is a claim about two INTERVENTIONS, so resolving it
    # experimentally needs both of their signatures, not one plus a prediction.
    (
        "6_two_arm_stat3_and_lif",
        ("E_GP130_STAT3", "E_LIF"),
        "C_B_plus_cd98",
        EXECUTION_CONTEXT,
    ),
)


def _same_target(arms: list[tuple[str, str, frozenset[str]]]) -> dict[str, str]:
    """Map each arm to a canonical name for arms that veto the identical set.

    ``hand2_loss`` and ``S_HAND2`` are not two mechanisms that happen to look
    alike; they are the same veto reached through the library and through the
    node. Counting them as an alias pair would overstate the ambiguity, so they
    are collapsed before any pair is formed.
    """
    by_targets: dict[frozenset[str], list[str]] = {}
    for arm, kind, targets in arms:
        by_targets.setdefault(targets, []).append(arm)
    canon = {}
    for targets, names in by_targets.items():
        # Prefer the eligible-node name over a library id, so the canonical
        # label names the model element rather than the reagent.
        nodes = [n for n in names if n in targets]
        head = min(nodes) if nodes else min(names)
        for n in names:
            canon[n] = head
    return canon


class Analysis:
    """Everything the three tables are derived from, computed once."""

    def __init__(self, model_version: str, root: Path) -> None:
        self.root = root
        self.model_version = model_version
        spec = resolve_model(model_version, root)
        self.network = vx.parse_network(spec.network_bnd.read_text(encoding="utf-8"))
        with spec.node_dictionary.open(encoding="utf-8", newline="") as handle:
            roles = {
                r["node_id"]: r["model_role"]
                for r in csv.DictReader(handle, delimiter="\t")
            }
        protocol_inputs = tuple(
            n for n in self.network.free if roles.get(n) in vx.PROTOCOL_INPUT_ROLES
        )
        self.protocol_inputs = protocol_inputs
        distribution = vx.free_distributions(
            spec.baseline_cfg.read_text(encoding="utf-8"), self.network.free
        )
        self.distribution = distribution
        self.contexts = vx._contexts(
            spec.condition_dir, protocol_inputs, self.network.free, distribution
        )
        self.scenarios = vx._scenarios(distribution, set(protocol_inputs))
        self.observed, _ = vx._observed_sets(root, set(self.network.nodes))
        self.arms = vx._arms(model_version, root)
        self.canon = _same_target(self.arms)
        self.targets = {arm: t for arm, _, t in self.arms}

        self.deltas: dict[tuple[str, str, int], dict[str, float]] = {}
        for name, inputs in self.contexts.items():
            for index, scenario in enumerate(self.scenarios):
                base = vx.marginals(self.network, inputs, scenario, frozenset())
                for arm, _, targets in self.arms:
                    m = vx.marginals(self.network, inputs, scenario, targets)
                    self.deltas[(arm, name, index)] = {
                        n: m[n] - base[n] for n in self.network.nodes
                    }
        self.keys = [
            (c, s) for c in sorted(self.contexts) for s in range(len(self.scenarios))
        ]
        self.assayable = self._read_assayable()

    def _read_assayable(self) -> dict[str, str]:
        path = self.root / ASSAYABLE_SOURCE
        if not path.exists():
            raise FileNotFoundError(f"{ASSAYABLE_SOURCE} is required for assayability")
        with path.open(encoding="utf-8", newline="") as handle:
            table = {
                r["node_id"]: r["assayable"]
                for r in csv.DictReader(handle, delimiter="\t")
            }
        resolved = {n: table.get(n, "unknown") for n in self.network.nodes}
        for node, (value, _basis) in ASSAYABILITY_OVERRIDES.items():
            if node in resolved:
                resolved[node] = value
        return resolved

    # -- primitives ----------------------------------------------------------

    def moves(self, arm: str, node: str) -> bool:
        return any(
            abs(self.deltas[(arm, c, s)][node]) > vx.TOLERANCE for c, s in self.keys
        )

    def separates_in(
        self, a: str, b: str, node: str, context: str, s_index: int
    ) -> bool:
        """Whether ``node`` tells ``a`` from ``b`` IN ONE condition and scenario."""
        return (
            abs(
                self.deltas[(a, context, s_index)][node]
                - self.deltas[(b, context, s_index)][node]
            )
            > vx.TOLERANCE
        )

    def separates(self, a: str, b: str, node: str) -> bool:
        """Whether ``node`` tells ``a`` from ``b`` in ANY declared condition.

        Existential, and therefore a STRUCTURAL property. Use
        :meth:`separates_in` for anything an experiment is said to deliver.
        """
        return any(
            abs(self.deltas[(a, c, s)][node] - self.deltas[(b, c, s)][node])
            > vx.TOLERANCE
            for c, s in self.keys
        )

    def classes(self, nodes: tuple[str, ...]) -> dict[str, str]:
        signatures = {
            arm: tuple(
                round(self.deltas[(arm, c, s)][n], 9)
                for c, s in self.keys
                for n in nodes
            )
            for arm, _, _ in self.arms
        }
        return vx._classes(signatures)

    def groups(self, nodes: tuple[str, ...]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for arm, cls in self.classes(nodes).items():
            out.setdefault(cls, []).append(arm)
        return {k: sorted(v) for k, v in out.items()}

    # -- derived tables ------------------------------------------------------

    def alias_pairs(self) -> list[dict[str, str]]:
        rows = []
        for cls, members in sorted(self.groups(self.observed).items()):
            distinct = sorted({self.canon[m] for m in members})
            for a, b in itertools.combinations(distinct, 2):
                sep = [n for n in self.network.nodes if self.separates(a, b, n)]
                both = self.targets[a] | self.targets[b]
                beyond = [n for n in sep if n not in both]
                if not sep:
                    reason = "rule_identical_everywhere"
                elif not beyond:
                    reason = "separable_only_at_targets"
                else:
                    reason = "separable_downstream"
                rows.append(
                    {
                        "observed_class": cls,
                        "target_a": a,
                        "target_b": b,
                        "collapse_reason": reason,
                        "separating_nodes": ";".join(sep),
                        "separating_nodes_assayable": ";".join(
                            n for n in sep if self.assayable.get(n) == "true"
                        ),
                        "separating_nodes_beyond_targets": ";".join(beyond),
                    }
                )
        return rows

    def readout_value(self, pairs: list[dict[str, str]]) -> list[dict[str, str]]:
        rows = []
        for node in self.network.nodes:
            if node in self.observed:
                continue
            groups = self.groups(tuple(self.observed) + (node,))
            broken = [
                p for p in pairs if self.separates(p["target_a"], p["target_b"], node)
            ]
            rows.append(
                {
                    "node_id": node,
                    "assayable": self.assayable.get(node, "unknown"),
                    "classes_with_node_added": str(
                        len([k for k in groups if k != vx.NULL_CLASS])
                    ),
                    "null_arms_with_node_added": str(
                        len(groups.get(vx.NULL_CLASS, []))
                    ),
                    "alias_pairs_broken": str(len(broken)),
                    "pairs_broken_detail": ";".join(
                        f"{p['target_a']}|{p['target_b']}" for p in broken
                    ),
                }
            )
        rows.sort(
            key=lambda r: (
                -int(r["alias_pairs_broken"]),
                -int(r["classes_with_node_added"]),
                r["node_id"],
            )
        )
        return rows

    def matrix(self, pairs: list[dict[str, str]]) -> list[dict[str, str]]:
        """One row per (perturbation, readout) that separates at least one rival."""
        rivals: dict[str, set[str]] = {}
        for p in pairs:
            rivals.setdefault(p["target_a"], set()).add(p["target_b"])
            rivals.setdefault(p["target_b"], set()).add(p["target_a"])
        rows = []
        for arm in sorted(rivals):
            for node in self.network.nodes:
                if node in self.observed:
                    continue
                split = sorted(r for r in rivals[arm] if self.separates(arm, r, node))
                if not split:
                    continue
                moves = self.moves(arm, node)
                rows.append(
                    {
                        "perturbation": f"veto:{arm}",
                        "readout": node,
                        "readout_moves_under_perturbation": "yes" if moves else "no",
                        "rivals_separated": ";".join(split),
                        "distinction": (
                            f"separates {arm} from {', '.join(split)}"
                            if moves
                            else (
                                f"separates {arm} from {', '.join(split)} only as a "
                                "negative result: this readout does not move under "
                                f"{arm}, so the discrimination is carried by the rival arms"
                            )
                        ),
                    }
                )
        return rows

    # -- structural capability, kept apart from experimental yield -----------

    def panel_structural_value(
        self, pairs: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """How much veto degeneracy each panel would make RESOLVABLE.

        Every column here is a property of the model plus the observed set. It
        is what an experiment needs in place beforehand, never what one returns.
        """
        rows = []
        for name, cost, _ in PANELS:
            added = _panel_readouts(name)
            groups = self.groups(tuple(self.observed) + added)
            resolvable = [
                p
                for p in pairs
                if any(self.separates(p["target_a"], p["target_b"], n) for n in added)
            ]
            rows.append(
                {
                    "panel": name,
                    "added_readouts": ";".join(added),
                    "new_assay_classes": str(cost),
                    "non_null_classes_structural": str(
                        len([k for k in groups if k != vx.NULL_CLASS])
                    ),
                    "null_arms_structural": str(len(groups.get(vx.NULL_CLASS, []))),
                    "alias_pairs_made_resolvable_structural": str(len(resolvable)),
                }
            )
        return rows

    def design_yield(self, pairs: list[dict[str, str]]) -> list[dict[str, str]]:
        """What each named design resolves, IN A STATED CONDITION AND SCENARIO.

        Two rules, both of which an earlier revision of this module broke.

        **An alias pair needs both of its vetoes run.** An alias pair is a claim
        that two *interventions* are observationally equivalent. Refuting it
        experimentally requires observing both signatures. Running one arm and
        comparing the result against the model's prediction for the other
        substitutes a prediction for the observation it is supposed to be
        tested against, so it is reported as variant discrimination — which is
        what it actually is — and never as alias resolution.

        **Nothing is unioned over conditions or scenarios.** A yield is reported
        for the condition the design states and for each declared latent
        scenario separately. `E_KLF12_HIGH` is hand-set and was never measurable
        (`docs/scrna/klf12_prior_finding.md`), so a design's yield under each of
        its values is reported rather than averaged or silently fixed at one.
        """
        variants = self.variant_arm_discrimination()
        rows = []
        for name, veto_arms, panel, context in DESIGNS:
            readouts = _panel_readouts(panel)
            cost = next(c for p_name, c, _ in PANELS if p_name == panel)
            measured = set(readouts) | set(self.observed)
            runnable = {f"veto:{a}" for a in veto_arms} | {"unperturbed_arms"}
            for s_index in range(len(self.scenarios)):
                scenario = self.scenario_label(s_index)
                resolved = [
                    pair
                    for pair in pairs
                    if pair["target_a"] in veto_arms
                    and pair["target_b"] in veto_arms
                    and any(
                        self.separates_in(
                            pair["target_a"], pair["target_b"], n, context, s_index
                        )
                        for n in readouts
                    )
                ]
                # Grouped BY VARIANT, not by (variant, arm). One variant read
                # under two arms is one variant discriminated; counting the
                # labels inflated every design running more than one arm, and
                # the ranking was built on that number.
                within: dict[str, set[str]] = {}
                needs_extra: dict[str, set[str]] = {}
                for v in variants:
                    if v["perturbation_arm"] not in runnable:
                        continue
                    if v["context"] != context or v["scenario"] != scenario:
                        continue
                    if not set(v["separating_readouts"].split(";")) & measured:
                        continue
                    if v["setting_is_current_design"] == "yes":
                        within.setdefault(v["variant_id"], set()).add(
                            v["perturbation_arm"]
                        )
                    else:
                        # Keyed by VARIANT, like `within`. One variant that
                        # needs three different input settings is still one
                        # variant needing an extra arm; the settings ride on
                        # the arm label so none of that detail is lost.
                        needs_extra.setdefault(v["variant_id"], set()).add(
                            f"{v['perturbation_arm']}[{v['extra_free_inputs']}]"
                        )
                # A variant already discriminated under the design's own input
                # settings does NOT need an extra arm, however many further
                # settings would also expose it. Leaving it in both columns made
                # "needing an extra input arm" false for it and double-counted
                # it across the two columns; the extra settings are reported in
                # the within-design detail's arms instead.
                needs_extra = {
                    variant: arms
                    for variant, arms in needs_extra.items()
                    if variant not in within
                }

                rows.append(
                    {
                        "design": name,
                        "execution_context": context,
                        "latent_scenario": scenario,
                        "veto_arms_run": ";".join(veto_arms) or "(none)",
                        "readouts_measured": ";".join(readouts) or "(current O only)",
                        "new_assay_classes": str(cost),
                        "alias_pairs_resolved": str(len(resolved)),
                        "alias_pairs_resolved_detail": ";".join(
                            f"{p['target_a']}|{p['target_b']}" for p in resolved
                        )
                        or "(none)",
                        "variants_discriminated_within_design": str(len(within)),
                        "variants_within_design_detail": _variant_detail(within),
                        "variants_needing_an_extra_input_arm": str(len(needs_extra)),
                        "variants_needing_extra_arm_detail": _variant_detail(
                            needs_extra
                        ),
                    }
                )
        return rows

    def _input_settings(self, extra: tuple[str, ...]) -> list[dict[str, bool]]:
        """Every combination of the controlled inputs a variant reads.

        Each setting is its own arm and they are never averaged: a marginal
        over "IL-11 supplied" and "IL-11 not supplied" is a number no
        experiment can produce.
        """
        if not extra:
            return [{}]
        return [
            dict(zip(extra, values))
            for values in itertools.product((False, True), repeat=len(extra))
        ]

    def scenario_label(self, index: int) -> str:
        """A readable name for a declared latent scenario.

        The scenarios are the combinations of the hand-set free variables; for
        v0.6.0 that is ``E_KLF12_HIGH`` alone. Labelling them is what makes a
        reported yield conditional rather than existential.
        """
        base = self.scenarios[index]
        hand_set = {
            n: v
            for n, v in sorted(base.items())
            if n not in self.protocol_inputs and v in (0.0, 1.0)
        }
        if not hand_set:
            return f"scenario_{index}"
        return ";".join(
            f"{n}={'high' if v == 1.0 else 'low'}" for n, v in hand_set.items()
        )

    def minimal_identifying_panel(
        self, pairs: list[dict[str, str]], max_size: int = 4
    ) -> list[dict[str, str]]:
        """The smallest readout set that tells each target from its class-mates.

        Searched exhaustively up to ``max_size`` over the assayable nodes, so a
        reported panel is minimal rather than merely sufficient. This is a
        STRUCTURAL quantity: it uses :meth:`separates`, so it says what could
        identify the target somewhere in the declared conditions, not what one
        executed arm delivers.
        """
        rivals: dict[str, set[str]] = {}
        for pair in pairs:
            rivals.setdefault(pair["target_a"], set()).add(pair["target_b"])
            rivals.setdefault(pair["target_b"], set()).add(pair["target_a"])
        candidates = [
            n
            for n in self.network.nodes
            if n not in self.observed and self.assayable.get(n) == "true"
        ]
        rows = []
        for target in sorted(rivals):
            best: tuple[str, ...] | None = None
            for size in range(1, max_size + 1):
                for combo in itertools.combinations(candidates, size):
                    if all(
                        any(self.separates(target, rival, n) for n in combo)
                        for rival in rivals[target]
                    ):
                        best = combo
                        break
                if best:
                    break
            rows.append(
                {
                    "target": target,
                    "rivals_in_class": ";".join(sorted(rivals[target])),
                    "minimal_panel": ";".join(best)
                    if best
                    else f"(none within {max_size} assayable readouts)",
                    "panel_size": str(len(best)) if best else "",
                    "panel_all_assayable": "yes" if best else "n/a",
                }
            )
        return rows

    def variant_arm_discrimination(self) -> list[dict[str, str]]:
        """Registered variants against the committed rules, ONE ARM AT A TIME.

        Memoised: it rebuilds and re-evaluates a network per variant, arm,
        input setting and context, and both ``design_yield`` and the tests call
        it repeatedly.

        The arms are enumerated separately and never merged. Under the
        registered ``GP130-b`` a LIF veto and a STAT3 veto make opposite
        predictions, so a single row naming both would be false for one.
        """
        from dt_adoc.reporting.veto_expressivity import marginals, parse_network

        cached = getattr(self, "_variant_rows", None)
        if cached is not None:
            return cached
        spec = resolve_model(self.model_version, self.root)
        text = spec.network_bnd.read_text(encoding="utf-8")
        rows = []
        for variant in _registered_variants(
            self.root, set(self.network.nodes), self.model_version
        ):
            mutated = text
            for node, expression in variant["rules"].items():
                pattern = re.compile(
                    rf"(Node\s+{re.escape(node)}\s*\{{\s*logic\s*=\s*)([^;]+)(;)"
                )
                if not pattern.search(mutated):
                    raise vx.ExpressivityError(
                        f"{variant['variant_id']} names {node}, absent from "
                        f"{self.model_version}"
                    )
                mutated = pattern.sub(
                    lambda m, e=expression: m.group(1) + e + m.group(3),
                    mutated,
                    count=1,
                )
            extra = variant["extra"]
            # A controlled input the network ALREADY declares (IN_HCG,
            # IN_EMBRYO_CONDITIONED_SIGNAL) is set by overriding the context's
            # input vector. Putting it in the scenario instead would be silently
            # overwritten by the context, which is why CD98-b, CD98-d and
            # CDH1-c produced no rows at all. Only a node the variant
            # introduces (X_IL11, E_DAG1_CLEAVABLE) is declared and seeded here.
            introduced = tuple(n for n in extra if n not in set(self.network.nodes))
            existing = tuple(n for n in extra if n not in introduced)
            declarations = "".join(
                f"Node {n} {{\n  logic = {n};\n}}\n" for n in introduced
            )
            network = parse_network(declarations + mutated)
            for arm_label, vetoes in [("unperturbed_arms", frozenset())] + [
                (f"veto:{a}", frozenset(self.targets[a])) for a in sorted(self.targets)
            ]:
                # Each controlled-input setting is its own arm, never averaged:
                # a marginal over "IL-11 supplied" and "IL-11 not supplied" is a
                # number no experiment can produce.
                for setting in self._input_settings(extra):
                    # Every declared latent scenario, labelled. Fixing
                    # scenarios[0] silently asserted E_KLF12_HIGH = 0, under
                    # which a different variant set is exposed.
                    for s_index, base_scenario in enumerate(self.scenarios):
                        for context, inputs in sorted(self.contexts.items()):
                            scenario = dict(base_scenario)
                            for node in introduced:
                                scenario[node] = 1.0 if setting[node] else 0.0
                            arm_inputs = dict(inputs)
                            for node in existing:
                                arm_inputs[node] = setting[node]
                            committed = {
                                k: v for k, v in scenario.items() if k not in introduced
                            }
                            variant_m = marginals(network, arm_inputs, scenario, vetoes)
                            base_m = marginals(
                                self.network, arm_inputs, committed, vetoes
                            )
                            differing = [
                                n
                                for n in self.network.nodes
                                if abs(variant_m[n] - base_m[n]) > vx.TOLERANCE
                            ]
                            if not differing:
                                continue
                            rows.append(
                                {
                                    "variant_id": variant["variant_id"],
                                    "axis": str(variant["axis"]),
                                    "baseline_id": str(variant["baseline_id"]),
                                    "rule_change": ";".join(
                                        f"{k} := {v}"
                                        for k, v in variant["rules"].items()
                                    ),
                                    "extra_free_inputs": _setting_label(setting),
                                    "setting_is_current_design": "yes"
                                    if _is_current_design(setting, variant)
                                    else "no",
                                    "perturbation_arm": arm_label,
                                    "context": context,
                                    "scenario": self.scenario_label(s_index),
                                    "separating_readouts": ";".join(differing),
                                    "separating_readouts_assayable": ";".join(
                                        n
                                        for n in differing
                                        if self.assayable.get(n) == "true"
                                    ),
                                }
                            )
        self._variant_rows = rows
        return rows


def _variant_detail(grouped: dict[str, set[str]]) -> str:
    """``variant@arm1,arm2`` per DISTINCT variant, so the detail matches the count."""
    if not grouped:
        return "(none)"
    return ";".join(
        f"{variant}@{','.join(sorted(arms))}"
        for variant, arms in sorted(grouped.items())
    )


def _setting_label(setting: dict[str, bool]) -> str:
    if not setting:
        return "(none)"
    # '+' inside a setting, because ';' separates entries and ',' separates arms
    # in the detail columns; reusing either here made the detail unparseable.
    return "+".join(f"{n}={'on' if v else 'off'}" for n, v in sorted(setting.items()))


def _is_current_design(setting: dict[str, bool], variant: dict[str, object]) -> bool:
    """Whether this input setting is what the CURRENT design already does.

    Against each input's **registered default**, never against ``off``.
    ``INPUT_DEFAULTS`` records ``E_DAG1_CLEAVABLE = True`` because endogenous
    alpha-dystroglycan IS cleavable and the experiment is the cleavage-resistant
    construct, i.e. setting it False. Treating every ``off`` as current makes
    the wild-type condition look like the intervention, which is the error
    ``experiments.variant_discrimination`` warns about in the same words.
    """
    defaults = variant.get("defaults") or {}
    return all(value == defaults.get(node, False) for node, value in setting.items())


def _panel_readouts(name: str) -> tuple[str, ...]:
    """The readouts of a named panel, resolving the nested increments."""
    out: list[str] = []
    for panel, _, explicit in PANELS:
        if explicit:
            out = list(explicit)
        elif panel in PANEL_INCREMENTS:
            out = out + [PANEL_INCREMENTS[panel]]
        if panel == name:
            return tuple(out)
    raise KeyError(f"unknown panel {name!r}; known are {[p for p, _, _ in PANELS]}")


def _registered_variants(
    root: Path, nodes: set[str], model_version: str = AUDIT_MODEL_VERSION
) -> list[dict[str, object]]:
    """Competing rule variants, read from the two registered sources.

    Nothing is invented. A variant whose substitution names a node this model
    version does not have is skipped with its reason recorded, rather than
    being silently adapted until it applies.

    **Fails closed.** The Gate-3 module is a required source, not an optional
    one: if it cannot be imported the tables would silently lose every variant
    it registers and the documented regeneration command would overwrite the
    committed artefacts with incomplete coverage. Only the module's own absence
    is tolerated, and a transitive import failure (a missing dependency of its
    dependencies) is re-raised.

    **Controlled inputs.** A variant is exposed only under the input settings
    its rule text actually reads. Two kinds are carried, mirroring
    ``experiments.variant_discrimination``: the variant's own
    ``required_inputs`` (nodes it introduces), and the *already declared*
    ``IN_*`` nodes that no recorded arm turns on. Omitting the second is what
    made ``CD98-b``, ``CD98-d`` and ``CDH1-c`` invisible, since their only new
    disjuncts are ``IN_HCG`` and ``IN_EMBRYO_CONDITIONED_SIGNAL``.
    """
    found: list[dict[str, object]] = []
    try:
        from dt_adoc.experiments import variant_discrimination as gate3
    except ModuleNotFoundError as error:
        if error.name != "dt_adoc.experiments.variant_discrimination":
            raise
        gate3 = None
    if gate3 is None:  # pragma: no cover - the module is present in this repo
        raise ExpressivityConfigError(
            "experiments.variant_discrimination is a required variant source; "
            "refusing to write tables with incomplete variant coverage"
        )
    unexercised = _unexercised_declared_inputs(root, nodes)
    # --- transport guard, fail-closed ------------------------------------
    # The Gate-3 tuple is registered against its own MODEL_VERSION (v0.4.0),
    # and this analysis evaluates a later one. A variant is only a statement
    # about "the committed rule versus this alternative", so transporting it
    # is sound ONLY where the committed rule it departs from is the same rule
    # in both models. Where the baseline has since changed, the v0.4 variant
    # is an alternative to a rule that no longer exists and carrying it over
    # would silently compare against the wrong baseline.
    source_rules = vx.parse_network(
        resolve_model(gate3.MODEL_VERSION, root).network_bnd.read_text(encoding="utf-8")
    ).rules
    current_rules = vx.parse_network(
        resolve_model(model_version, root).network_bnd.read_text(encoding="utf-8")
    ).rules
    for variant in gate3.VARIANTS:
        for node in variant.overrides or {}:
            if node not in source_rules or node not in current_rules:
                raise ExpressivityConfigError(
                    f"{variant.variant_id} overrides {node}, which is not a "
                    f"computed node of both {gate3.MODEL_VERSION} and "
                    f"{model_version}; transport refused"
                )
            if source_rules[node] != current_rules[node]:
                raise ExpressivityConfigError(
                    f"{variant.variant_id} cannot be transported from "
                    f"{gate3.MODEL_VERSION} to {model_version}: the committed "
                    f"rule for {node} differs between them "
                    f"({source_rules[node]!r} vs {current_rules[node]!r}), so "
                    "the variant would be compared against the wrong baseline"
                )
    for variant in gate3.VARIANTS:
        rules = dict(variant.overrides or {})
        if not rules or not set(rules) <= nodes:
            continue
        reads = tuple(
            node
            for node in unexercised
            if any(
                re.search(rf"\b{re.escape(node)}\b", body) for body in rules.values()
            )
        )
        found.append(
            {
                "variant_id": variant.variant_id,
                "axis": variant.axis,
                "baseline_id": f"{variant.variant_id.rsplit('-', 1)[0]}-a",
                "rules": rules,
                "extra": tuple(variant.required_inputs or ()) + reads,
                "defaults": dict(gate3.INPUT_DEFAULTS),
                "source": "experiments.variant_discrimination",
            }
        )
    # The model's own variant catalogue. Only non-default rows compete with the
    # committed rules; `default_executable` IS the committed rule, so including
    # it would manufacture a variant that differs from the model by nothing.
    spec = resolve_model(model_version, root)
    catalogue = spec.network_bnd.parent / "rule_variants.tsv"
    if catalogue.exists():
        with catalogue.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["status"] == "default_executable":
                    continue
                if row["node_id"] not in nodes:
                    continue
                found.append(
                    {
                        "variant_id": row["variant_id"],
                        "axis": row["node_id"],
                        "baseline_id": "committed",
                        "rules": {row["node_id"]: row["expression"]},
                        "extra": (),
                        "defaults": {},
                        "source": "rule_variants.tsv",
                    }
                )
    return found


def _unexercised_declared_inputs(root: Path, nodes: set[str]) -> tuple[str, ...]:
    """Declared ``IN_*`` nodes that no condition cfg turns on.

    These are controllable and already exist, so exposing a variant that reads
    one needs a new *arm*, not a new node.
    """
    spec = resolve_model(AUDIT_MODEL_VERSION, root)
    on: set[str] = set()
    for cfg in sorted(spec.condition_dir.glob("*.cfg")):
        text = cfg.read_text(encoding="utf-8")
        on |= {
            name
            for name, value in vx._POINT_ISTATE_RE.findall(text)
            if value in ("TRUE", "1")
        }
    return tuple(sorted(n for n in nodes if n.startswith("IN_") and n not in on))


def render(rows: list[dict[str, str]], columns: tuple[str, ...]) -> str:
    lines = ["\t".join(columns)]
    lines.extend("\t".join(row[c] for c in columns) for row in rows)
    return "\n".join(lines) + "\n"


def build(
    model_version: str = AUDIT_MODEL_VERSION, root: Path | None = None
) -> list[tuple[Path, str]]:
    root = root or repo_root()
    analysis = Analysis(model_version, root)
    pairs = analysis.alias_pairs()
    return [
        (ALIAS_PATH, render(pairs, ALIAS_COLUMNS)),
        (READOUT_PATH, render(analysis.readout_value(pairs), READOUT_COLUMNS)),
        (MATRIX_PATH, render(analysis.matrix(pairs), MATRIX_COLUMNS)),
        (
            PANEL_PATH,
            render(analysis.panel_structural_value(pairs), PANEL_COLUMNS),
        ),
        (VARIANT_PATH, render(analysis.variant_arm_discrimination(), VARIANT_COLUMNS)),
        (
            MINIMAL_PATH,
            render(analysis.minimal_identifying_panel(pairs), MINIMAL_COLUMNS),
        ),
        (YIELD_PATH, render(analysis.design_yield(pairs), YIELD_COLUMNS)),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("write", "check"))
    args = parser.parse_args(argv)
    root = repo_root()
    outputs = build(root=root)
    if args.command == "write":
        for path, text in outputs:
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text(text, encoding="utf-8")
        return 0
    stale = [
        str(path)
        for path, text in outputs
        if not (root / path).exists()
        or (root / path).read_text(encoding="utf-8") != text
    ]
    if stale:
        print(f"stale: {', '.join(stale)}; run write", file=sys.stderr)
        return 1
    print(f"ok: {len(outputs)} identifiability-design tables current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
