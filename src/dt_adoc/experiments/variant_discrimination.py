"""Gate 3a: which maternal observation separates each candidate rule variant.

With `adhesion_objective` demoted to `diagnostic_ordinal` there is no fitted
score left in this repository, so a candidate rule can no longer be preferred
because it fits better. It can only be preferred because **an observation
distinguishes it**. This module computes that, for every competing pair in
`gate3_candidate_variants_*.tsv`, by applying each variant's rule change in
memory and comparing the two models' predictions node by node and arm by arm.

The distinction it exists to enforce is the one the repository keeps having to
relearn: **structural distinguishability is not experimental
distinguishability.** A variant can add a distinct Boolean function to the
partition -- the 35 -> 36 that `gate3_candidate_variants` records -- and still
be indistinguishable from v0.4 in every arm anyone can run, because the input it
newly reads is off in all of them. `CD98-b` is exactly that case, and only this
computation shows it.

Everything here is derived. The curated table supplies the rule text and the
scientific commentary; which observation separates what is computed from the
committed network, and whether that observation is measurable is read from the
observation layer.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from dt_adoc.reporting.identifiability import (
    _evaluate,
    _latent_seeds,
    _topological_order,
    load_identifiability,
    parse_bnd_rules,
    repo_root,
    resolve_model,
)

MODEL_VERSION = "adoc-literature-superset-v0.4.0"
OUT_MD = Path("docs/experiments/variant_discrimination.md")
OUT_TSV = Path("docs/experiments/variant_discrimination.tsv")


#: The maternal node universe, used for BOTH the discrimination comparison and
#: the measurability lookup. Mixing the two -- comparing only `E_*`/`S_*` while
#: counting a mapped `OUT_*` composite as measurable -- lets the header claim a
#: readout that can never appear as a separating node.
#:
#: `OUT_EPITHELIAL_RECEPTIVE` and `OUT_STROMAL_DECIDUALIZED` are in: they are
#: maternal composites and the observation map does assay them, as multi-analyte
#: composites. `OUT_MATERNAL_ADHESION_COMPETENCE` and `OUT_STABLE_ADHESION` are
#: out: those are the terminal interface, not the maternal model.
MATERNAL_OUT_NODES = ("OUT_EPITHELIAL_RECEPTIVE", "OUT_STROMAL_DECIDUALIZED")


def _is_maternal(node: str) -> bool:
    return node.startswith(("E_", "S_")) or node in MATERNAL_OUT_NODES


#: Arms with no embryo. A discrimination available in one of these is worth far
#: more than one that needs the attachment assay, whose noise the project has
#: decided not to calibrate on.
def _is_embryo_free(arm) -> bool:
    return not arm.inputs.get("IN_EMBRYO_PRESENT", False)


@dataclass(frozen=True)
class Variant:
    """A candidate rule change, as an in-memory edit of the committed network."""

    variant_id: str
    axis: str
    overrides: dict[str, str]
    #: Nodes the variant introduces that an EXPERIMENTER CONTROLS -- a supplied
    #: ligand, a transfected construct. They are never marginalised: averaging
    #: over "IL-11 supplied" and "IL-11 not supplied" produces a number no
    #: experiment can produce. Each setting is evaluated as its own arm.
    required_inputs: tuple[str, ...] = ()

    @property
    def is_baseline(self) -> bool:
        return not self.overrides and not self.required_inputs


#: The executable reading of `gate3_candidate_variants_2026-09-16.tsv`, plus the
#: one variant U4 staged from TI001's literal rule text (`CD98-d`; the curated
#: commentary is in `docs/v05_u4_gp130_axis.md`, not backdated into the Sept-16
#: table). Only the variants whose rule change is expressible as a DAG edit
#: appear: `IGFBP1-fb` introduces a 14-node cycle the enumerator refuses, and
#: `EPAC` and `HH-reception` are pass-throughs recorded there as structurally
#: inert. Those three are reported as excluded rather than silently dropped, and
#: :data:`NOT_STAGED` reports the family member U4 refused to write at all.
VARIANTS: tuple[Variant, ...] = (
    Variant("CD98-a", "CD98", {}),
    Variant("CD98-b", "CD98", {"E_CD98_CD9": "E_GP130_STAT3 or IN_HCG"}),
    Variant("CD98-c", "CD98", {"E_CD98_CD9": "E_GP130_STAT3 or IN_HCG or IN_E2"}),
    # TI001's rule text as written, third disjunct included. Staged in U4 to
    # ask what that disjunct buys, not because it is supported: DTR005 records
    # that no source names a generic embryo-conditioned inducer, and Dominguez
    # 2010 read in full attributes the conditioned-medium induction of CD98 to
    # the hCG the spheroids secrete -- so the disjunct is a second encoding of
    # `IN_HCG` rather than an independent one, on data the paper does not show.
    Variant(
        "CD98-d",
        "CD98",
        {"E_CD98_CD9": ("E_GP130_STAT3 or IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL")},
    ),
    Variant("CDH1-a", "CDH1", {}),
    Variant(
        "CDH1-b", "CDH1", {"E_CDH1_APICAL": "IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL"}
    ),
    Variant(
        "CDH1-c",
        "CDH1",
        {
            "E_CDH1_APICAL": "IN_EMBRYO_CONTACT or IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL"
        },
    ),
    Variant("GP130-a", "GP130/STAT3", {}),
    Variant(
        "GP130-b", "GP130/STAT3", {"E_GP130_STAT3": "E_LIF or X_IL11"}, ("X_IL11",)
    ),
    Variant("PC6-a", "PC6/DAG1", {}),
    Variant(
        "PC6-b",
        "PC6/DAG1",
        {
            "E_DAG1_CLEAVED": "E_PC6 and E_DAG1_CLEAVABLE",
            "E_DAG1_FULL": "not E_DAG1_CLEAVED",
        },
        ("E_DAG1_CLEAVABLE",),
    ),
)

#: Pairs the Gate-3 table treats as competing readings of the same evidence.
#: A pair against its own axis baseline asks "can this variant be told from
#: v0.4 at all"; a pair of two non-baseline variants asks "can they be told
#: apart from each other".
PAIRS: tuple[tuple[str, str], ...] = (
    ("CD98-a", "CD98-b"),
    ("CD98-a", "CD98-c"),
    ("CD98-b", "CD98-c"),
    # U4: does TI001's third disjunct buy an observation that `IN_HCG` alone
    # does not? Against the baseline and against the two-disjunct form.
    ("CD98-a", "CD98-d"),
    ("CD98-b", "CD98-d"),
    ("CDH1-a", "CDH1-b"),
    ("CDH1-b", "CDH1-c"),
    ("GP130-a", "GP130-b"),
    ("PC6-a", "PC6-b"),
)

#: What each controlled input is in the CURRENT design, before any new
#: experiment. Not uniformly False: a supplied ligand is absent by default, but
#: a substrate that already exists in the tissue is present by default, and the
#: experiment is the construct that removes it. Getting this backwards makes the
#: wild-type condition look like the intervention.
INPUT_DEFAULTS: dict[str, bool] = {
    # Recombinant IL-11 is not in any current medium.
    "X_IL11": False,
    # Endogenous alpha-dystroglycan IS cleavable; the experiment is the
    # cleavage-resistant mutant, i.e. setting this to False.
    "E_DAG1_CLEAVABLE": True,
}


def _unexercised_inputs(facts, base_rules: dict[str, str]) -> tuple[str, ...]:
    """Declared `IN_*` nodes that are off in EVERY recorded arm.

    These are controllable and they already exist -- turning one on needs a new
    arm, not a new node. Treating them as fixed was the error that made
    `CD98-a vs CD98-b` look impossible to separate: `CD98-b`'s only new disjunct
    is `IN_HCG`, and an hCG-on arm separates the two readings in six arms.
    """
    return tuple(
        sorted(
            node
            for node in base_rules
            if node.startswith("IN_")
            and not any(arm.inputs.get(node) for arm in facts.arms)
        )
    )


def _inputs_read_by(variant: Variant, candidates: tuple[str, ...]) -> tuple[str, ...]:
    """Which of ``candidates`` this variant's rule text actually reads."""
    return tuple(
        node
        for node in candidates
        if any(
            re.search(rf"\b{re.escape(node)}\b", body)
            for body in variant.overrides.values()
        )
    )


EXCLUDED = {
    "IGFBP1-fb": (
        "introduces a cycle among 14 nodes, which the structural enumerator "
        "refuses to evaluate; separately blocked on calibration leakage because "
        "S_IGFBP1 carries an observation-map role"
    ),
    "EPAC": (
        "recorded in the candidate table as a pass-through that leaves the "
        "partition at 35 -> 35; Kusama 2013 shows graded potentiation, which a "
        "rate-free Boolean model cannot express at all"
    ),
    "HH-reception": (
        "pass-through, 35 -> 35, and blocked on GAP-014: no free stromal "
        "competence determinant exists that is not invented"
    ),
}

#: Family members that were PROPOSED and are deliberately NOT WRITTEN. Distinct
#: from :data:`EXCLUDED`, which holds variants that exist in the curated table
#: and cannot be computed. A rule absent from both dictionaries looks like a
#: rule nobody thought of.
NOT_STAGED = {
    "GP130-d (convergent-plus-an-IL11-specific-arm)": (
        "TI002 asks for the GP130 family to be carried as convergent-only "
        "VERSUS convergent-plus-an-IL11-specific-arm, because Marwood 2009 "
        "shows the two ligands dissociate DOWNSTREAM of STAT3 -- IL-11 "
        "stimulates trophoblast attachment where LIF does not, and alpha2beta1 "
        "blockade reduces the LIF but not the IL-11 collagen-IV response. U4 "
        "read the paper named as most likely to supply the missing executor, "
        "Yap/Dimitriadis 2011 (PMID 21619711), in full. It identifies ANXA2 and "
        "FLOT1 as IL-11-regulated plasma-membrane proteins, and ANXA2 is "
        "already a committed node -- so the arm could be written in one line "
        "as `E_ANXA2_ACTIN = E_SECRETORY_STATE or X_IL11`, which would also "
        "break it out of the nine-member AC01 class. It is not written, because "
        "that paper runs NO LIF COMPARATOR and NO ADHESION OR ATTACHMENT "
        "ENDPOINT: it cannot establish that either protein is IL-11-SPECIFIC, "
        "which is the entire content of the second family member, and it "
        "measures membrane ABUNDANCE where the node is an actin-remodelling "
        "state. Writing it would invent the functional link, which is what "
        "GP130-b's own limitation column already says must not be done. So the "
        "family is single-membered for want of a representable alternative, "
        "NOT because the evidence chose between the two. See "
        "docs/v05_u4_gp130_axis.md."
    ),
}


def _predictions(
    variant: Variant,
    facts,
    base_rules: dict[str, str],
    setting: dict[str, bool],
) -> dict[str, dict[str, float]]:
    """Marginals over the LATENT variables only, conditioned on ``setting``.

    ``setting`` fixes every experimenter-controlled input the pair introduces.
    Latent nodes -- the cfg-weighted free variables the model already had -- are
    still marginalised, because those are genuine uncertainty. A supplied
    ligand is not.
    """
    rules = dict(base_rules)
    rules.update(variant.overrides)
    for node in setting:
        rules.setdefault(node, node)
    order = _topological_order(rules, {n for n in rules if rules[n].strip() == n})
    seeds, states, mask = _latent_seeds(facts.latent)
    out: dict[str, dict[str, float]] = {}
    for arm in facts.arms:
        column = _evaluate(rules, order, seeds, mask, {**arm.inputs, **setting})
        out[arm.arm_id] = {
            node: (column[node] & mask).bit_count() / states for node in rules
        }
    return out


#: Readout tiers, strongest first. Derived from the observation map, never
#: curated. "Measurable today" was one flat label and it was wrong: it counted
#: `OUT_EPITHELIAL_RECEPTIVE` as measurable although its own OM-009 row is
#: `reported_only`, `confidence=low`, `source_rows_n=0`, `objective_treatment=
#: not_used`, and its `claim_ceiling` says in as many words "Not usable to
#: validate OUT_EPITHELIAL_RECEPTIVE behavior".
USABLE_ASSAY = "usable_assay"
MAPPED_COMPOSITE = "mapped_composite_not_validating"
NO_ASSAY = "no_assay"
READOUT_TIERS = (USABLE_ASSAY, MAPPED_COMPOSITE, NO_ASSAY)

#: Statuses whose rows the calibration layer actually acts on.
_ACTIVE_STATUSES = {"active_constraint", "active_diagnostic"}


def _readout_tier(root: Path) -> dict[str, tuple[str, str]]:
    """Per model node: ``(tier, provenance)``, from the observation map.

    A row earns :data:`USABLE_ASSAY` only if the layer actually acts on it
    (`active_constraint` or `active_diagnostic`) **and** it has real source rows.
    A row that maps a node but is `reported_only`/`provisional`, or that has
    `source_rows_n = 0`, is a :data:`MAPPED_COMPOSITE`: the propagation is
    preserved and reported, but it does not make the node validatable. Anything
    the map does not mention is :data:`NO_ASSAY`.
    """
    found: dict[str, tuple[str, str]] = {}
    with (root / "config/observation_model_map.tsv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            status = row.get("activation_status", "").strip()
            if status in {"rejected", ""}:
                continue
            try:
                rows_n = int(row.get("source_rows_n", "0") or 0)
            except ValueError:
                rows_n = 0
            tier = (
                USABLE_ASSAY
                if status in _ACTIVE_STATUSES and rows_n > 0
                else MAPPED_COMPOSITE
            )
            label = (
                f"{row['protein'].strip()} [{status}, "
                f"confidence={row.get('confidence', '').strip() or 'unstated'}, "
                f"source_rows_n={rows_n}]"
            )
            for node in row.get("model_nodes", "").split(";"):
                node = node.strip()
                if not node:
                    continue
                # Strongest tier wins if a node is mapped more than once.
                if node not in found or (
                    found[node][0] == MAPPED_COMPOSITE and tier == USABLE_ASSAY
                ):
                    found[node] = (tier, label)
    return found


def discriminate(root: Path | None = None) -> dict:
    active = root or repo_root()
    facts = load_identifiability(MODEL_VERSION, active)
    base_rules = parse_bnd_rules(resolve_model(MODEL_VERSION, active).network_bnd)
    maternal = sorted(n for n in base_rules if _is_maternal(n))
    # Same universe for the readout tiers, so the two can never disagree.
    tiers = {
        node: value
        for node, value in _readout_tier(active).items()
        if _is_maternal(node)
    }
    embryo_free = {a.arm_id for a in facts.arms if _is_embryo_free(a)}
    by_id = {v.variant_id: v for v in VARIANTS}

    results = []
    for left, right in PAIRS:
        unexercised = _unexercised_inputs(facts, base_rules)
        required = tuple(
            sorted(
                set(by_id[left].required_inputs)
                | set(by_id[right].required_inputs)
                | set(_inputs_read_by(by_id[left], unexercised))
                | set(_inputs_read_by(by_id[right], unexercised))
            )
        )
        # Every setting of the controlled inputs is its own experiment. The
        # all-off setting is the one runnable in the CURRENT design.
        settings: list[dict[str, bool]] = [{}]
        for node in required:
            settings = [{**s, node: value} for s in settings for value in (False, True)]

        per_setting = []
        for setting in settings:
            ml = _predictions(by_id[left], facts, base_rules, setting)
            mr = _predictions(by_id[right], facts, base_rules, setting)
            hits = []
            for arm_id in sorted(ml):
                for node in maternal:
                    if node not in ml[arm_id] or node not in mr[arm_id]:
                        continue
                    a, b = ml[arm_id][node], mr[arm_id][node]
                    if abs(a - b) > 1e-12:
                        hits.append(
                            {
                                "arm": arm_id,
                                "node": node,
                                "left": round(a, 4),
                                "right": round(b, 4),
                                "embryo_free": arm_id in embryo_free,
                                "opposite": {a, b} == {0.0, 1.0},
                                "readout_tier": tiers.get(node, (NO_ASSAY, ""))[0],
                                "readout_note": tiers.get(node, (NO_ASSAY, ""))[1],
                            }
                        )
            per_setting.append(
                {
                    "setting": setting,
                    "label": ", ".join(
                        f"{k}={'present' if v else 'absent'}"
                        + (
                            " [current design]"
                            if v == INPUT_DEFAULTS.get(k, False)
                            else " [INTERVENTION]"
                        )
                        for k, v in sorted(setting.items())
                    )
                    or "current design (no new input)",
                    "is_current_design": all(
                        value == INPUT_DEFAULTS.get(node, False)
                        for node, value in setting.items()
                    ),
                    "hits": hits,
                }
            )

        current = next(s for s in per_setting if s["is_current_design"])
        any_hit = [s for s in per_setting if s["hits"]]
        if not any_hit:
            verdict = "NOT_DISCRIMINABLE_UNDER_ANY_SETTING"
        elif current["hits"]:
            free = [h for h in current["hits"] if h["embryo_free"]]
            if any(h["opposite"] for h in free):
                verdict = "DISCRIMINABLE_IN_CURRENT_ARMS_EMBRYO_FREE_OPPOSITE"
            elif free:
                verdict = "DISCRIMINABLE_IN_CURRENT_ARMS_EMBRYO_FREE"
            else:
                verdict = "DISCRIMINABLE_IN_CURRENT_ARMS_ONLY_WITH_EMBRYOS"
        else:
            verdict = "REQUIRES_A_NEW_CONTROLLED_INPUT"

        all_hits = [h for s in per_setting for h in s["hits"]]
        results.append(
            {
                "pair": f"{left} vs {right}",
                "left": left,
                "right": right,
                "axis": by_id[left].axis,
                "verdict": verdict,
                "controlled_inputs_varied": list(required),
                "per_setting": per_setting,
                "separating_nodes": sorted({h["node"] for h in all_hits}),
                "usable_assay_nodes": sorted(
                    {h["node"] for h in all_hits if h["readout_tier"] == USABLE_ASSAY}
                ),
                "mapped_composite_nodes": sorted(
                    {
                        h["node"]
                        for h in all_hits
                        if h["readout_tier"] == MAPPED_COMPOSITE
                    }
                ),
            }
        )
    return {
        "results": results,
        "excluded": EXCLUDED,
        "not_staged": NOT_STAGED,
        "embryo_free_arms": sorted(embryo_free),
        "readout_tiers": tiers,
    }


def render(report: dict) -> str:
    lines: list[str] = []
    a = lines.append
    # The banner carries no generation date. A wall-clock stamp made an
    # unchanged report rewrite itself on a new day, so a clean checkout went
    # dirty for nothing; pinned by
    # test_generated_date_determinism.ClockFrozenRegenerationTest.
    a("# Gate 3a — which maternal observation separates each candidate variant")
    a("")
    a(
        "> **Generated file — do not edit.** Regenerate with "
        "`pixi run build-variant-discrimination`. Computed by applying each "
        "variant's rule change to the committed "
        f"`{MODEL_VERSION}` network in memory and comparing predictions across "
        "every recorded arm."
    )
    a("")
    a(
        "`adhesion_objective` is `diagnostic_ordinal`, so **no fitted score "
        "exists**. A candidate can only be preferred because an observation "
        "distinguishes it, and this table is that test."
    )
    a("")
    a(
        "Three distinctions are kept separate, because collapsing any of them overstates a candidate:"
    )
    a("")
    a(
        "1. **Structural vs experimental.** A variant can add a distinct Boolean "
        "function to the partition and still be unseparable from v0.4 in every "
        "arm anyone can run, because the input it newly reads is off in all of "
        "them. `CD98-b` is exactly that."
    )
    a(
        "2. **Current arms vs a new controlled input.** A variant that introduces "
        "a supplied ligand or a construct is *not* discriminable today; it is "
        "discriminable in an experiment that does not yet exist. Those inputs are "
        '**conditioned on, never marginalised** — averaging over "IL-11 supplied" '
        'and "IL-11 absent" yields a number no experiment can produce.'
    )
    a(
        "3. **Model state vs readout, in three tiers, not two.** A difference in "
        "a node nothing can assay is a difference between two model states. But "
        '"measurable" is not one thing: a node can be mapped by the observation '
        "layer and still not be usable to validate it. The tiers are derived from "
        "the map, never asserted:"
    )
    a("")
    a(
        "| Pair | Axis | Verdict | Separating nodes | Usable assay | "
        "Mapped composite | Controlled inputs varied |"
    )
    a("|---|---|---|---|---|---|---|")
    for r in report["results"]:
        nodes = ", ".join(f"`{n}`" for n in r["separating_nodes"]) or "—"
        usable = ", ".join(f"`{n}`" for n in r["usable_assay_nodes"]) or "**none**"
        composite = ", ".join(f"`{n}`" for n in r["mapped_composite_nodes"]) or "—"
        varied = ", ".join(f"`{n}`" for n in r["controlled_inputs_varied"]) or "—"
        a(
            f"| {r['pair']} | {r['axis']} | **{r['verdict']}** | {nodes} | "
            f"{usable} | {composite} | {varied} |"
        )
    a("")

    for r in report["results"]:
        a(f"## {r['pair']}")
        a("")
        a(f"**Verdict:** `{r['verdict']}`")
        a("")
        if r["controlled_inputs_varied"]:
            a(
                "**Controlled inputs varied:** "
                + ", ".join(f"`{n}`" for n in r["controlled_inputs_varied"])
                + ". Each setting below is a distinct experiment. The setting "
                "marked *current design* is the one the existing arms already "
                "run; a verdict of `REQUIRES_A_NEW_CONTROLLED_INPUT` means only "
                "the other settings separate the pair."
            )
            a("")
        if r["separating_nodes"] and not r["usable_assay_nodes"]:
            if r["mapped_composite_nodes"]:
                a(
                    "> **No separating node has a usable assay.** "
                    + ", ".join(f"`{n}`" for n in r["mapped_composite_nodes"])
                    + " is mapped by the observation layer, but at a tier the map "
                    "itself says cannot validate the node, so it does not make "
                    "this discrimination runnable today."
                )
            else:
                a(
                    "> **No separating node is in the observation layer at all.** "
                    "Every discrimination below needs a readout ADOC has never "
                    "measured, so the experiment must be costed as a new assay."
                )
            a("")
        for setting in r["per_setting"]:
            a(f"### Setting: {setting['label']}")
            a("")
            if not setting["hits"]:
                a("No maternal node differs in any recorded arm under this setting.")
                a("")
                continue
            a(
                f"| Arm | Node | {r['left']} | {r['right']} | embryo-free | "
                "opposite | readout tier |"
            )
            a("|---|---|---|---|---|---|---|")
            for h in setting["hits"]:
                a(
                    f"| `{h['arm']}` | `{h['node']}` | {h['left']} | {h['right']} | "
                    f"{'yes' if h['embryo_free'] else 'no'} | "
                    f"{'**yes**' if h['opposite'] else 'no'} | "
                    f"`{h['readout_tier']}`"
                    + (f" — {h['readout_note']}" if h["readout_note"] else "")
                    + " |"
                )
            a("")

    a("## Variants excluded from this computation")
    a("")
    for variant_id, reason in sorted(report["excluded"].items()):
        a(f"* **{variant_id}** — {reason}")
    a("")
    a(
        "> **Excluding `IGFBP1-fb` does NOT close the PRL/IGFBP1 Gate-3a task.** "
        "What is excluded is one proposed *repair* — adding `S_IGFBP1` as an input "
        "to `S_DECIDUALIZED` — because it creates a 14-node cycle the enumerator "
        "cannot evaluate and because `S_IGFBP1` carries an observation-map role, so "
        "an outgoing causal edge would make the model that interprets that "
        "measurement depend on it. The underlying problem is untouched and is live: "
        "`S_PRL = S_IGFBP1 = S_DECIDUALIZED` share one rule, one initial state and "
        "one default rate, so their onset distributions are identical by "
        "construction, and the recorded IGFBP-1-before-PRL onset order is something "
        "the model cannot express at all. That axis is also the **only** one whose "
        "nodes the observation layer actually measures."
    )
    a("")
    a("## Family members proposed and deliberately not written")
    a("")
    for variant_id, reason in sorted(report["not_staged"].items()):
        a(f"* **{variant_id}** — {reason}")
    a("")
    a("## Embryo-free arms")
    a("")
    a(
        "A discrimination available in one of these avoids the attachment assay "
        "entirely: " + ", ".join(f"`{x}`" for x in report["embryo_free_arms"])
    )
    a("")
    return "\n".join(lines) + "\n"


def build(root: Path | None = None) -> tuple[Path, Path]:
    active = root or repo_root()
    report = discriminate(active)
    md = active / OUT_MD
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(render(report), encoding="utf-8")
    tsv = active / OUT_TSV
    with tsv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(
            [
                "pair",
                "axis",
                "verdict",
                "controlled_inputs_varied",
                "separating_nodes",
                "usable_assay_nodes",
                "mapped_composite_nodes",
                "discriminable_in_current_arms",
                "embryo_free_separation",
                "opposite_prediction",
            ]
        )
        for r in report["results"]:
            current = next(s for s in r["per_setting"] if s["is_current_design"])
            all_hits = [h for s in r["per_setting"] for h in s["hits"]]
            w.writerow(
                [
                    r["pair"],
                    r["axis"],
                    r["verdict"],
                    ";".join(r["controlled_inputs_varied"]),
                    ";".join(r["separating_nodes"]),
                    ";".join(r["usable_assay_nodes"]),
                    ";".join(r["mapped_composite_nodes"]),
                    bool(current["hits"]),
                    any(h["embryo_free"] for h in all_hits),
                    any(h["opposite"] for h in all_hits),
                ]
            )
    return md, tsv


if __name__ == "__main__":  # pragma: no cover
    md, tsv = build()
    print(f"wrote {md}")
    print(f"wrote {tsv}")
