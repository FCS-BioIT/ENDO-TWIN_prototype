"""U6b -- the ``E_MUC1_BARRIER`` rule family, evaluated and not adopted.

Defined in ``docs/v05_mechanistic_integration_plan.md`` §17 (U6b) and register
row ``TI-02``. **Evaluation only**: this module writes no ``network.bnd``, creates
no model version and edits nothing under ``models/``. Every family member is an
in-memory edit of ``adoc-literature-superset-v0.5.1``, materialised only inside a
temporary copy of ``models/`` and ``config/`` so that the repository's own
unmodified loaders -- ``structure.load_structure``,
``identifiability.load_identifiability`` / ``compute_gain`` and
``design_alias.load_design_alias`` -- measure it exactly as they measure a
committed model. That is the pattern ``test_v05_u4_gp130`` already uses for
unadopted variants; no parallel enumerator is introduced.

What is computed, per member, against v0.5.1:

* the exact rule delta, and which nodes' **composed** Boolean functions change
  (the measured blast radius, over every assignment of the free variables);
* distinct functions, alias classes broken/formed, free variables, absorbed and
  never-binding dependencies, phenotype-inert nodes, unsatisfiable nodes;
* whether ``E_MUC1_BARRIER`` can bind on ``OUT_STABLE_ADHESION`` and on
  ``OUT_MATERNAL_ADHESION_COMPETENCE`` at all;
* the fixed-point value of every reported output under each committed
  condition cfg, weighted by ``baseline.cfg``'s own latent priors -- the value
  ``docs/endpoint_convergence_finding.md`` shows converged MaBoSS reproduces;
* identifiability and design-alias under the recorded and the declared design,
  with the matched-unit caveat carried as a field (§13.12).

Two axes are kept apart throughout and must not be merged by a reader:
**structural effect** is measured here; **biological licensing** is read from the
registered evidence and recorded per rule element. A member can move the
numbers and remain unlicensed, and several do.

The clearance placeholder of member family ``C`` has no prior in any cfg, and
none is invented: its endpoints are reported at clearance OFF and ON separately
and never marginalised.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import parse_bnd_rules

MODEL = "adoc-literature-superset-v0.5.1"
OUTPUT_DIR = Path("docs/u6b_muc1_reconciliation")
SUMMARY_JSON = OUTPUT_DIR / "u6b_summary.json"
MEMBERS_TSV = OUTPUT_DIR / "family_members.tsv"
RULE_VARIANTS_TSV = OUTPUT_DIR / "rule_variants.tsv"
ELEMENTS_TSV = OUTPUT_DIR / "rule_elements.tsv"
ENDPOINTS_TSV = OUTPUT_DIR / "endpoints.tsv"

BARRIER = "E_MUC1_BARRIER"
ABUNDANCE = "E_MUC1_ABUNDANCE"
CLEARANCE = "E_MUC1_LOCAL_CLEARANCE"
RECEPTIVE = "E_RECEPTIVE_SURFACE"
ROUTE = "X_ANTIADHESIVE_ROUTE"
STABLE = "OUT_STABLE_ADHESION"
COMPETENCE = "OUT_MATERNAL_ADHESION_COMPETENCE"

#: The committed conjunct the owner's placement decision (2026-09-23) removes.
PLACEMENT_CONJUNCT = f" and not {BARRIER}"

#: The committed rule the family replaces. Asserted on load: if v0.5.1 ever
#: stopped carrying it, every number below would describe a different model.
COMMITTED_BARRIER_RULE = "not E_SECRETORY_STATE"

MATCHED_UNIT_CAVEAT = (
    "MATCHED-UNIT CONDITIONAL. Design-equivalence classes, observation classes, "
    "information statuses and design-state counts assume one biological unit "
    "carries a single latent assignment through every arm and assay. ADOC does "
    "not provide that (config/adoc_chip_donor_provenance.tsv). These numbers "
    "describe what a matched-unit design of this shape could identify, NOT what "
    "the current data identify."
)

#: The frozen prospective arm (docs/stage3_experiment_selection.md §12), as an
#: input vector only: the hormone-treated maternal overlay with E2 omitted. It is
#: EVALUATED here, never edited; its assays are the three existing ELISAs.
FROZEN_ARM_BASE_CFG = "hormone_treated_maternal"
FROZEN_ARM_OVERRIDE = {"IN_E2": False}
FROZEN_ARM_ASSAYS = ("E_PAEP", "S_IGFBP1", "S_PRL")
FROZEN_ARM_ID = "FROZEN_minus_E2_maternal"


# --------------------------------------------------------------------------
# Rule elements and their evidence status -- the licensing axis
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RuleElement:
    element_id: str
    rule_text: str
    evidence_ids: str
    evidence_status: str
    supports: str
    does_not_support: str


#: Every edge or rule component any member writes, with the registered evidence
#: wording it rests on. Statuses are a closed vocabulary; see ``EVIDENCE_STATUSES``.
RULE_ELEMENTS: tuple[RuleElement, ...] = (
    RuleElement(
        "RE-01",
        f"remove `{PLACEMENT_CONJUNCT.strip()}` from {RECEPTIVE} (edge LE028 retired); "
        f"the barrier acts only through {ROUTE} (edge LE074, already committed)",
        "owner decision 2026-09-23 (plan §17 U6b); PIF-008",
        "OWNER_DECISION_PLACEMENT",
        "Placement is an owner decision about where a state acts: maternal "
        "epithelial receptivity must stay definable without embryo contact, and "
        "PIF-008 reports high bulk MUC1 together with strictly local clearance at "
        "apposition.",
        "It says nothing about what causes clearance, and it does not keep "
        f"{COMPETENCE} embryo-independent: that node reads {ROUTE}.",
    ),
    RuleElement(
        "RE-02",
        f"{ABUNDANCE} = E_SECRETORY_STATE",
        "PIF-008 (REF-085); GAP-011 context REF-068 (cell lines)",
        "SUPPORTED_DIRECTION_ONLY",
        "PIF-008: twofold MUC1 mRNA increase Day 21 vs Day 13 in vivo (p<0.05) "
        "after estrogen then progesterone, protein a continuous apical array "
        "after 6 d of progesterone. The sign of the progestin dependence.",
        "A Boolean ON/OFF for a twofold graded change is a binarisation the "
        "source does not state; MUC1 is present on Day 13 too.",
    ),
    RuleElement(
        "RE-03",
        f"{ABUNDANCE} = E_PGR",
        "PIF-008 (REF-085)",
        "NOT_DISTINGUISHED_BY_SOURCE",
        "Same direction as RE-02.",
        "PIF-008 compares estrogen alone against estrogen followed by "
        "progesterone and runs no progesterone-alone arm, so it cannot choose "
        "between RE-02 and RE-03. Both are carried; neither is selected.",
    ),
    RuleElement(
        "RE-04",
        f"{BARRIER} = {ABUNDANCE} and not {CLEARANCE}",
        "GAP-004; GAP-011; PIF-008; PIF-009 (REF-086)",
        "SUPPORTED_AS_SEPARATION_CONSEQUENCE_WEAKENED",
        "GAP-004/GAP-011 prescribe keeping abundance, glycoform and local "
        "clearance apart; PIF-008 measures them as three different things and "
        "shows high bulk MUC1 coexisting with local absence.",
        "That the resulting barrier is anti-adhesive is not established for "
        "MUC1: PIF-009 finds MUC1 knockdown at matched efficiency gives no "
        "statistical difference in trophoblast adhesion (cell line on cell "
        "line, 1 h) -- a non-significant result, not a demonstrated absence of "
        "effect, and not a licence to remove the edge either.",
    ),
    RuleElement(
        "RE-05",
        f"{CLEARANCE} = IN_EMBRYO_CONTACT",
        "PIF-008 (REF-085)",
        "UNLICENSED_SPATIAL_ASSOCIATION",
        "PIF-008: MUC1 absent from epithelium subjacent and adjacent to the "
        "attached embryo, rising with distance, epithelium intact by cytokeratin.",
        "Spatial association only: n=3 implantation sites, descriptive, no "
        "perturbation; the mechanism of local removal is undetermined and the "
        "authors concede embryo-induced epithelial apoptosis would look the "
        "same. A causal contact -> clearance edge is not licensed.",
    ),
    RuleElement(
        "RE-06",
        f"{CLEARANCE} = IN_EMBRYO_CONTACT and IN_TROPHECTODERM_COMPETENT",
        "PIF-008 (REF-085)",
        "UNLICENSED_STRESS_TEST",
        "Nothing beyond RE-05.",
        "PIF-008 licenses no embryo-competence conjunct: arrested embryos were "
        "compared only in the APPOSITION coculture, where their effect was "
        "intermediate, and were not tested at attachment. Carried only to show "
        "what the conjunct would change.",
    ),
    RuleElement(
        "RE-07",
        f"{CLEARANCE} = {CLEARANCE} (free placeholder, no prior)",
        "PIF-008 (REF-085)",
        "REPRESENTS_IGNORANCE",
        "Asserts no determinant, which is what PIF-008 supports.",
        "Adds a latent variable no arm sets and no cfg gives a probability; its "
        "endpoints are bounds, not estimates.",
    ),
    RuleElement(
        "RE-08",
        f"{BARRIER} = E_SECRETORY_STATE (naive sign flip, no clearance term)",
        "PIF-008 (REF-085); GAP-004",
        "REFUSED_BY_SOURCE",
        "Fixes the sign of abundance only.",
        "PIF-008 row: 'DOES NOT LICENSE A SIGN FLIP'. It re-collapses abundance "
        "and barrier into one label, which GAP-004 forbids.",
    ),
)

EVIDENCE_STATUSES = frozenset(e.evidence_status for e in RULE_ELEMENTS)


# --------------------------------------------------------------------------
# The family
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Member:
    member_id: str
    role: str
    description: str
    placement: str  # "receptive_surface_and_interface" | "interface_only"
    #: Replacement rules for committed nodes ("<placement>" is resolved on load).
    overrides: dict[str, str] = field(default_factory=dict)
    #: Nodes the member introduces, with their rules.
    additions: dict[str, str] = field(default_factory=dict)
    elements: tuple[str, ...] = ()
    licensing: str = ""


def _split(
    member_id: str,
    abundance: str,
    clearance: str,
    elements: tuple[str, ...],
    licensing: str,
    description: str,
) -> Member:
    return Member(
        member_id=member_id,
        role="family_member",
        description=description,
        placement="interface_only",
        overrides={
            BARRIER: f"{ABUNDANCE} and not {CLEARANCE}",
            RECEPTIVE: "<placement>",
        },
        additions={ABUNDANCE: abundance, CLEARANCE: clearance},
        elements=("RE-01",) + elements,
        licensing=licensing,
    )


_A = ("RE-04", "RE-05")
_B = ("RE-04", "RE-06")
_C = ("RE-04", "RE-07")

#: Pre-registered before any number below was generated, and fixed in this
#: tuple so a later edit shows up in the diff: the three clearance determinants
#: the plan requires (contact-driven; contact-plus-competence, unlicensed;
#: unresolved), crossed with the two abundance drivers the source cannot tell
#: apart, plus the two naive flips the plan says must be measured before they are
#: refused, the committed rule, and a placement-only control that attributes the
#: effect of moving the conjunct separately from the effect of changing the rule.
MEMBERS: tuple[Member, ...] = (
    Member(
        "V0",
        "reference",
        "committed v0.5.1 rule, unchanged",
        "receptive_surface_and_interface",
        licensing="CONTRADICTED_BY_PIF-008",
    ),
    Member(
        "P0",
        "control",
        "placement only: conjunct removed, committed rule kept",
        "interface_only",
        overrides={RECEPTIVE: "<placement>"},
        elements=("RE-01",),
        licensing="CONTROL_NOT_A_CANDIDATE",
    ),
    Member(
        "N1",
        "naive_flip",
        "sign flip in place, both readers kept",
        "receptive_surface_and_interface",
        overrides={BARRIER: "E_SECRETORY_STATE"},
        elements=("RE-08",),
        licensing="REFUSED",
    ),
    Member(
        "N2",
        "naive_flip",
        "sign flip with the interface placement",
        "interface_only",
        overrides={BARRIER: "E_SECRETORY_STATE", RECEPTIVE: "<placement>"},
        elements=("RE-01", "RE-08"),
        licensing="REFUSED",
    ),
    _split(
        "A-SEC",
        "E_SECRETORY_STATE",
        "IN_EMBRYO_CONTACT",
        ("RE-02",) + _A,
        "UNLICENSED",
        "clearance driven by embryo contact; abundance = secretory",
    ),
    _split(
        "A-PGR",
        "E_PGR",
        "IN_EMBRYO_CONTACT",
        ("RE-03",) + _A,
        "UNLICENSED",
        "clearance driven by embryo contact; abundance = PGR",
    ),
    _split(
        "B-SEC",
        "E_SECRETORY_STATE",
        "IN_EMBRYO_CONTACT and IN_TROPHECTODERM_COMPETENT",
        ("RE-02",) + _B,
        "UNLICENSED_STRESS_TEST",
        "clearance needs contact and embryo competence; abundance = secretory",
    ),
    _split(
        "B-PGR",
        "E_PGR",
        "IN_EMBRYO_CONTACT and IN_TROPHECTODERM_COMPETENT",
        ("RE-03",) + _B,
        "UNLICENSED_STRESS_TEST",
        "clearance needs contact and embryo competence; abundance = PGR",
    ),
    _split(
        "C-SEC",
        "E_SECRETORY_STATE",
        CLEARANCE,
        ("RE-02",) + _C,
        "NO_DETERMINANT_ASSERTED",
        "clearance unresolved (free placeholder); abundance = secretory",
    ),
    _split(
        "C-PGR",
        "E_PGR",
        CLEARANCE,
        ("RE-03",) + _C,
        "NO_DETERMINANT_ASSERTED",
        "clearance unresolved (free placeholder); abundance = PGR",
    ),
)


#: Pairs whose fixed-point contrast is reported: each abundance-driver pair (the
#: source cannot choose between them), A against B (what the unlicensed
#: competence conjunct changes), and every member against the committed rule.
CONTRASTS: tuple[tuple[str, str], ...] = (
    ("A-SEC", "A-PGR"),
    ("B-SEC", "B-PGR"),
    ("C-SEC", "C-PGR"),
    ("A-SEC", "B-SEC"),
    ("A-SEC", "C-SEC"),
) + tuple(("V0", m.member_id) for m in MEMBERS if m.member_id != "V0")


def member_rules(member: Member, base: dict[str, str]) -> dict[str, str]:
    """The member's full rule set, committed rules overridden in memory."""
    if base[BARRIER] != COMMITTED_BARRIER_RULE:
        raise ValueError(
            f"{MODEL} no longer carries {BARRIER} = {COMMITTED_BARRIER_RULE}"
        )
    if base[RECEPTIVE].count(PLACEMENT_CONJUNCT) != 1:
        raise ValueError(
            f"{RECEPTIVE} does not carry exactly one `{PLACEMENT_CONJUNCT}`"
        )
    rules = dict(base)
    for node_id, body in member.overrides.items():
        if node_id not in base:
            raise ValueError(f"override of undeclared node {node_id}")
        rules[node_id] = (
            base[RECEPTIVE].replace(PLACEMENT_CONJUNCT, "")
            if body == "<placement>"
            else body
        )
    for node_id, body in member.additions.items():
        if node_id in base:
            raise ValueError(f"addition {node_id} already exists in {MODEL}")
        rules[node_id] = body
    return rules


def render_bnd(base_text: str, base: dict[str, str], rules: dict[str, str]) -> str:
    """The member as network.bnd text: committed text with rules substituted."""
    text = base_text
    for node_id, committed in base.items():
        body = rules[node_id]
        if body == committed:
            continue
        pattern = re.compile(rf"(Node {node_id} \{{\n  logic = )(.*?)(;\n)", re.DOTALL)
        text, n = pattern.subn(
            lambda m, body=body: m.group(1) + body + m.group(3), text
        )
        if n != 1:
            raise ValueError(f"could not locate the rule of {node_id}")
    for node_id, body in rules.items():
        if node_id not in base:
            text += f"\nNode {node_id} {{\n  logic = {body};\n}}\n"
    return text


# --------------------------------------------------------------------------
# Exhaustive evaluation helpers (read-only use of the committed enumerator)
# --------------------------------------------------------------------------


def _truth_table(
    rules: dict[str, str], free: tuple[str, ...]
) -> tuple[dict[str, int], int]:
    from dt_adoc.reporting.structure import _columns, _topological_order

    states = 2 ** len(free)
    mask = (1 << states) - 1
    seeds: dict[str, int] = {}
    for index, node_id in enumerate(free):
        block = 1 << index
        column = 0
        for start in range(block, states, block * 2):
            column |= ((1 << block) - 1) << start
        seeds[node_id] = column
    order = _topological_order(rules, set(free))
    return _columns(rules, order, seeds, mask), mask


def _free(rules: dict[str, str]) -> tuple[str, ...]:
    return tuple(n for n in rules if rules[n].strip() == n)


def blast_radius(base: dict[str, str], rules: dict[str, str]) -> list[str]:
    """Committed nodes whose composed function differs, over the union space."""
    free = tuple(dict.fromkeys(_free(rules) + _free(base)))
    padded = {**base, **{n: n for n in free if n not in base}}
    left, _ = _truth_table(padded, free)
    right, _ = _truth_table(rules, free)
    return [n for n in base if left[n] != right[n]]


def barrier_binding(rules: dict[str, str]) -> dict[str, Any]:
    """Can the barrier change each adhesion output at all, and when is it ON?"""
    from dt_adoc.reporting.structure import _columns, _topological_order

    free = _free(rules)
    table, mask = _truth_table(rules, free)
    order = _topological_order(rules, set(free))
    seeds = {n: table[n] for n in free}
    pinned = []
    for value in (0, mask):
        columns = _columns(rules, order, {**seeds, BARRIER: value}, mask)
        pinned.append(columns)
    evaluable = (
        table["IN_EMBRYO_PRESENT"]
        & table["IN_TROPHECTODERM_COMPETENT"]
        & table["IN_EMBRYO_CONTACT"]
    )
    return {
        "clamping_barrier_changes_stable_adhesion": pinned[0][STABLE]
        != pinned[1][STABLE],
        "clamping_barrier_changes_maternal_competence": (
            pinned[0][COMPETENCE] != pinned[1][COMPETENCE]
        ),
        "barrier_on_when_stable_adhesion_is_evaluable": bool(
            table[BARRIER] & evaluable
        ),
        "barrier_satisfiable": table[BARRIER] != 0,
        "unsatisfiable_nodes": sorted(
            n for n in rules if n not in free and table[n] == 0
        ),
    }


# --------------------------------------------------------------------------
# Fixed-point endpoints under the committed conditions
# --------------------------------------------------------------------------

REPORTED = (
    BARRIER,
    ROUTE,
    "OUT_EPITHELIAL_RECEPTIVE",
    COMPETENCE,
    STABLE,
)


def _cfg_inputs(path: Path) -> dict[str, bool]:
    from dt_adoc.reporting.identifiability import _parse_cfg_inputs

    return _parse_cfg_inputs(path)


def condition_values(
    rules: dict[str, str], root: Path
) -> dict[tuple[str, str], dict[str, float]]:
    """Exact fixed-point probability of every node, per condition and setting.

    The network is a DAG over its free variables, so each assignment has one
    fixed point; probabilistic latent variables are weighted by the priors
    ``baseline.cfg`` declares, deterministic ones take their declared istate. A
    free variable with NO prior -- the clearance placeholder -- is evaluated at
    each value separately and never averaged. Keys are ``(condition, setting)``.
    """
    from dt_adoc.reporting.identifiability import parse_cfg_probabilities
    from dt_adoc.reporting.structure import _columns, _topological_order

    spec = resolve_model(MODEL, root)
    priors = parse_cfg_probabilities(spec.baseline_cfg)
    baseline = _cfg_inputs(spec.baseline_cfg)
    free = _free(rules)
    weighted = tuple(n for n in free if n in priors)
    unprioritised = tuple(
        n
        for n in free
        if n not in priors and n not in baseline and not n.startswith("IN_")
    )
    order = _topological_order(rules, set(free))
    states = 2 ** len(weighted)
    full = (1 << states) - 1
    seeds_w: dict[str, int] = {}
    for index, node_id in enumerate(weighted):
        block = 1 << index
        column = 0
        for start in range(block, states, block * 2):
            column |= ((1 << block) - 1) << start
        seeds_w[node_id] = column
    weights = []
    for i in range(states):
        w = 1.0
        for node_id in weighted:
            w *= (
                priors[node_id]
                if (seeds_w[node_id] >> i) & 1
                else 1.0 - priors[node_id]
            )
        weights.append(w)

    settings = (
        [{}]
        if not unprioritised
        else [{n: bool(v) for n in unprioritised} for v in (0, 1)]
    )
    stems = sorted(p.stem for p in spec.condition_dir.glob("*.cfg"))
    arms = [(stem, spec.condition_dir / f"{stem}.cfg", {}) for stem in stems]
    arms.append(
        (
            FROZEN_ARM_ID,
            spec.condition_dir / f"{FROZEN_ARM_BASE_CFG}.cfg",
            FROZEN_ARM_OVERRIDE,
        )
    )
    out: dict[tuple[str, str], dict[str, float]] = {}
    for stem, cfg, override in arms:
        overlay = {**_cfg_inputs(cfg), **override}
        for setting in settings:
            seeds = dict(seeds_w)
            for node_id in free:
                if node_id in seeds:
                    continue
                if node_id in setting:
                    value = setting[node_id]
                else:
                    value = overlay.get(node_id, baseline.get(node_id, False))
                seeds[node_id] = full if value else 0
            columns = _columns(rules, order, seeds, full)
            label = ";".join(f"{k}={int(v)}" for k, v in setting.items()) or "none"
            out[(stem, label)] = {
                n: round(
                    sum(w for i, w in enumerate(weights) if (columns[n] >> i) & 1), 6
                )
                for n in rules
            }
    return out


def endpoint_rows(
    member: Member, values: dict[tuple[str, str], dict[str, float]]
) -> list[dict[str, Any]]:
    rows = []
    for (stem, setting), nodes in values.items():
        row: dict[str, Any] = {
            "member_id": member.member_id,
            "condition": stem,
            "unprioritised_setting": setting,
        }
        for node_id in REPORTED:
            row[node_id] = f"{nodes[node_id]:.6f}" if node_id in nodes else ""
        rows.append(row)
    return rows


def contrast(left: dict, right: dict, watched: tuple[str, ...]) -> dict[str, Any]:
    """Where two members' fixed points differ, over the conditions they share.

    A condition is compared only under a setting both members carry; a member
    with an unprioritised placeholder is compared at each of its settings
    against the other's single value, so a difference at EITHER bound counts.
    """
    differing: dict[str, list[str]] = {}
    for (stem, s_left), a in left.items():
        for (stem_r, s_right), b in right.items():
            if stem_r != stem or (
                s_left != "none" and s_right != "none" and s_left != s_right
            ):
                continue
            nodes = sorted(n for n in set(a) & set(b) if a[n] != b[n])
            if nodes:
                differing.setdefault(stem, [])
                differing[stem] = sorted(set(differing[stem]) | set(nodes))
    watched_hits = {
        stem: [n for n in nodes if n in watched] for stem, nodes in differing.items()
    }
    return {
        "conditions_differing": sorted(differing),
        "shared_nodes_differing_by_condition": differing,
        "watched_nodes_differing_by_condition": {
            k: v for k, v in watched_hits.items() if v
        },
    }


# --------------------------------------------------------------------------
# Whole-member evaluation
# --------------------------------------------------------------------------


#: Node-dictionary rows for the nodes a member ADDS, written only into the
#: temporary copy. The identifiability and design-alias loaders read
#: `measurement_proxies` to decide assayability; a node with no row would fall
#: through to the empty-proxy default and be classed as a modelling placeholder,
#: which would misreport the unresolved clearance state as an interface relay.
#: The proxies are PIF-008's own proximal measurements, not an assay proposal:
#: MUC1 abundance by Northern blot and core-protein antibodies, and local apical
#: loss by confocal localisation next to the attached embryo. Proposed, not
#: adopted -- these rows exist nowhere in the repository's models.
ADDED_NODE_METADATA: dict[str, dict[str, str]] = {
    ABUNDANCE: {
        "label": "Bulk epithelial MUC1 abundance (proposed, U6b evaluation)",
        "compartment": "epithelium",
        "species": "human",
        "baseline_mapping": "new",
        "state_0_meaning": "MUC1 at non-receptive abundance",
        "state_1_meaning": "MUC1 raised by the progestin-driven state",
        "measurement_proxies": "MUC1 core protein or mRNA abundance",
        "model_role": "state",
        "evidence_ids": "PIF-008",
        "reference_ids": "REF-085",
        "confidence": "assumption",
        "uncertainty_or_alternative_interpretation": (
            "Driver not distinguished by the source (E_SECRETORY_STATE vs E_PGR)"
        ),
        "notes": "U6b in-memory evaluation only; not in any model.",
    },
    CLEARANCE: {
        "label": "Local apical MUC1 clearance (proposed, U6b evaluation)",
        "compartment": "epithelium",
        "species": "human",
        "baseline_mapping": "new",
        "state_0_meaning": "No local MUC1 loss",
        "state_1_meaning": "MUC1 locally absent at the embryo site, epithelium intact",
        "measurement_proxies": "local apical MUC1 loss by confocal localisation",
        "model_role": "state",
        "evidence_ids": "PIF-008",
        "reference_ids": "REF-085",
        "confidence": "assumption",
        "uncertainty_or_alternative_interpretation": (
            "Determinant undetermined; embryo-induced apoptosis not excluded"
        ),
        "notes": "U6b in-memory evaluation only; not in any model.",
    },
}


def _append_dictionary_rows(path: Path, added: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    header = text.splitlines()[0].split("\t")
    if not text.endswith("\n"):
        text += "\n"
    for node_id in added:
        row = {"node_id": node_id, **ADDED_NODE_METADATA[node_id]}
        missing = set(header) - set(row)
        if missing:
            raise ValueError(f"no metadata for {node_id}: {sorted(missing)}")
        text += "\t".join(row[c] for c in header) + "\n"
    path.write_text(text, encoding="utf-8")


def _with_member(root: Path, bnd_text: str, added: list[str], fn):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        shutil.copytree(root / "models", tmp_root / "models")
        shutil.copytree(root / "config", tmp_root / "config")
        model_dir = tmp_root / "models" / "superset" / MODEL
        (model_dir / "network.bnd").write_text(bnd_text, encoding="utf-8")
        if added:
            _append_dictionary_rows(model_dir / "node_dictionary.tsv", added)
        return fn(tmp_root)


def _measure(tmp_root: Path) -> dict[str, Any]:
    from dt_adoc.reporting.design_alias import (
        _Enumerator,
        candidate_fifth_arms,
        design_alias_summary,
        load_design_alias,
    )
    from dt_adoc.reporting.identifiability import (
        compute_gain,
        identifiability_summary,
        load_identifiability,
    )
    from dt_adoc.reporting.structure import load_structure, structural_summary

    facts = load_structure(MODEL, tmp_root)
    ident = load_identifiability(MODEL, tmp_root)
    gain = compute_gain(ident, tmp_root)
    design = {}
    for variant in (None, "maternal_phase_only"):
        alias = load_design_alias(tmp_root, variant, facts=ident, model_version=MODEL)
        candidates = candidate_fifth_arms(
            alias, tmp_root, enumerator=_Enumerator(MODEL, tmp_root)
        )
        summary = design_alias_summary(alias, candidates)
        design[variant or "as_declared"] = {
            "design_effective_states": summary["design_effective_states"],
            "largest_design_class": summary["largest_design_class"],
            "best_fifth_arm_gain": summary["best_fifth_arm_gain"],
            "categories": summary["categories"],
            "category_of_added_nodes": {
                n: alias.category[n]
                for n in (ABUNDANCE, CLEARANCE)
                if n in alias.category
            },
            "design_class_of": {
                n: sorted(m)
                for m in alias.design_classes
                for n in m
                if n in (BARRIER, ABUNDANCE, CLEARANCE, ROUTE, COMPETENCE)
            },
        }
    return {
        "structural": structural_summary(facts),
        "alias_classes": sorted(sorted(m) for m in facts.alias_classes),
        "phenotype_inert": sorted(facts.phenotype_inert),
        "absorbed": sorted(list(e) for e in facts.absorbed_edges),
        "never_binding": sorted(list(e) for e in facts.never_binding_inhibitions),
        "edges": sorted([s, t, sign] for s, t, sign in facts.edges),
        "free": sorted(facts.free),
        "identifiability": {
            "matched_unit_caveat": MATCHED_UNIT_CAVEAT,
            **{
                k: identifiability_summary(ident)[k]
                for k in (
                    "global_effective_states",
                    "design_effective_states",
                    "latent_variables",
                    "observation_classes",
                    "measured_nodes",
                )
            },
            "design_states_ceiling": gain.global_ceiling,
            "observation_classes_ceiling": gain.latent_ceiling,
            "information_status": {
                n: s
                for n, s in sorted(ident.information_status.items())
                if n
                in (
                    BARRIER,
                    ABUNDANCE,
                    CLEARANCE,
                    ROUTE,
                    COMPETENCE,
                    STABLE,
                    "X_INTERFACE_ANTIADHESIVE_RELAY",
                )
            },
            "latent": list(ident.latent),
            "measured": list(ident.measured_nodes),
            "assayable_added_nodes": sorted(
                n for n in ident.assayable if n in (ABUNDANCE, CLEARANCE)
            ),
        },
        "design_alias": {"matched_unit_caveat": MATCHED_UNIT_CAVEAT, **design},
    }


def _alias_moves(
    reference: list[list[str]], mine: list[list[str]], member: Member
) -> dict:
    ref = {tuple(m) for m in reference}
    new = {tuple(m) for m in mine}
    class_of = {n: m for m in mine for n in m}
    ref_of = {n: m for m in reference for n in m}
    enlarged = []
    for node_id in member.additions:
        if node_id in class_of:
            grown = class_of[node_id]
            previous = [n for n in grown if n != node_id]
            prior = ref_of.get(previous[0], [previous[0]]) if previous else []
            enlarged.append(
                {
                    "node": node_id,
                    "joins": previous,
                    "size_before": len(prior),
                    "size_after": len(grown),
                }
            )
    barrier_before = ref_of.get(BARRIER, [BARRIER])
    barrier_after = class_of.get(BARRIER, [BARRIER])
    if barrier_after == [BARRIER]:
        barrier_verdict = "SEPARATED_TO_SINGLETON"
    elif sorted(barrier_after) == sorted(barrier_before):
        barrier_verdict = "UNCHANGED_ALIAS"
    else:
        barrier_verdict = "MOVED_TO_ANOTHER_ALIAS"
    return {
        "broken": sorted(list(m) for m in ref - new),
        "formed": sorted(list(m) for m in new - ref),
        "enlarged_by_new_nodes": enlarged,
        "barrier_class_before": sorted(barrier_before),
        "barrier_class_after": sorted(barrier_after),
        "barrier_verdict": barrier_verdict,
    }


def evaluate(root: Path | None = None) -> dict[str, Any]:
    active = root or repo_root()
    spec = resolve_model(MODEL, active)
    base_text = spec.network_bnd.read_text(encoding="utf-8")
    base = parse_bnd_rules(spec.network_bnd)
    readers = sorted(
        n
        for n, body in base.items()
        if n != BARRIER and re.search(rf"\b{BARRIER}\b", body)
    )

    results: dict[str, Any] = {}
    endpoints: list[dict[str, Any]] = []
    values: dict[str, dict] = {}
    for member in MEMBERS:
        rules = member_rules(member, base)
        measured = _with_member(
            active,
            render_bnd(base_text, base, rules),
            [n for n in rules if n not in base],
            _measure,
        )
        measured["rules"] = {
            n: rules[n]
            for n in (BARRIER, ABUNDANCE, CLEARANCE, RECEPTIVE)
            if n in rules
        }
        measured["rule_delta"] = {
            n: {"from": base.get(n, "<absent>"), "to": rules[n]}
            for n in rules
            if base.get(n) != rules[n]
        }
        measured["blast_radius"] = blast_radius(base, rules)
        measured["binding"] = barrier_binding(rules)
        results[member.member_id] = measured
        values[member.member_id] = condition_values(rules, active)
        endpoints.extend(endpoint_rows(member, values[member.member_id]))

    reference = results["V0"]
    for member in MEMBERS:
        r = results[member.member_id]
        r["alias"] = _alias_moves(
            reference["alias_classes"], r["alias_classes"], member
        )
        r["delta_distinct_functions"] = (
            r["structural"]["distinct_functions"]
            - reference["structural"]["distinct_functions"]
        )
        ref_edges = {tuple(e[:2]) for e in reference["edges"]}
        my_edges = {tuple(e[:2]) for e in r["edges"]}
        absorbed = {tuple(e) for e in r["absorbed"]}
        r["edges_added"] = sorted(
            [s, t, "absorbed" if (s, t) in absorbed else "effective"]
            for s, t in my_edges - ref_edges
        )
        r["edges_removed"] = sorted(list(e) for e in ref_edges - my_edges)
        r["inert_gained"] = sorted(
            set(r["phenotype_inert"]) - set(reference["phenotype_inert"])
        )
        r["inert_lost"] = sorted(
            set(reference["phenotype_inert"]) - set(r["phenotype_inert"])
        )

    # What any readout could see. The recorded design's measured nodes plus the
    # frozen arm's three assays; every other node is invisible to data in hand.
    watched = tuple(
        sorted(set(reference["identifiability"]["measured"]) | set(FROZEN_ARM_ASSAYS))
    )
    contrasts = {
        f"{a}|{b}": contrast(values[a], values[b], watched) for a, b in CONTRASTS
    }
    return {
        "readers_of_barrier_in_model": readers,
        "members": results,
        "endpoints": endpoints,
        "watched_nodes": list(watched),
        "contrasts": contrasts,
    }


# --------------------------------------------------------------------------
# Serialisation
# --------------------------------------------------------------------------


def _tsv(rows: list[dict[str, Any]], columns: tuple[str, ...]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=columns, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


MEMBER_COLUMNS = (
    "member_id",
    "role",
    "description",
    "placement",
    "rule_elements",
    "licensing",
    "nodes",
    "dependencies",
    "free_variables",
    "distinct_functions",
    "delta_distinct_functions_vs_v051",
    "alias_classes",
    "barrier_alias_verdict",
    "barrier_alias_class_after",
    "alias_classes_broken",
    "alias_classes_formed",
    "alias_enlarged_by_new_nodes",
    "phenotype_inert_nodes",
    "inert_gained",
    "inert_lost",
    "absorbed_dependencies",
    "never_binding_inhibitions",
    "edges_added",
    "edges_removed",
    "unsatisfiable_nodes",
    "composed_function_changed_nodes",
    "clamping_barrier_changes_stable_adhesion",
    "clamping_barrier_changes_maternal_competence",
    "barrier_on_when_stable_adhesion_is_evaluable",
    "global_effective_states",
    "design_effective_states_recorded",
    "observation_classes",
    "latent_variables",
    "design_effective_states_as_declared_plan",
    "design_effective_states_maternal_phase_only",
    "matched_unit_conditional",
)


def _join(items) -> str:
    return ";".join(items) if items else ""


#: The U6b rule-variant catalog (plan §17 U6b: an unlicensed family "goes to
#: rule_variants.tsv"). v0.5.1's own rule_variants.tsv is part of an audited model
#: and may not change, and U6b creates no version, so the family is written to
#: RULE_VARIANTS_TSV in that file's exact schema. It is the ONLY place the member
#: rules are tabulated; family_members.tsv carries metrics and licensing and
#: joins on `source_row_id`. `status` takes only the schema's non-executable
#: values and `default_in_family` is false on every row, so no row can be read as
#: an adopted rule; the finer class (refused, stress test, unresolved) is in
#: `notes` and in family_members.tsv `licensing`. The runtime reads only
#: model-local catalogs; a later TI-06 version may transcribe rows into its own.
RULE_VARIANT_COLUMNS = (
    "variant_id",
    "node_id",
    "expression",
    "status",
    "default_in_family",
    "source_table",
    "source_row_id",
    "evidence_ids",
    "notes",
)
CATALOG_NODES = (RECEPTIVE, BARRIER, ABUNDANCE, CLEARANCE)
CATALOG_STATUSES = frozenset({"reference_only", "catalog_only"})


def catalog_status(member: Member) -> str:
    return (
        "reference_only" if member.role in ("reference", "control") else "catalog_only"
    )


def evidence_ids(member: Member) -> list[str]:
    by_id = {e.element_id: e for e in RULE_ELEMENTS}
    found: set[str] = set()
    for element_id in member.elements:
        found.update(
            re.findall(r"\b(?:PIF|GAP|REF)-\d+", by_id[element_id].evidence_ids)
        )
    if member.member_id == "V0":
        # The committed rule's own citation (edge LE013) and the source that
        # contradicts it.
        found.update({"LIT-BARRIER-001", "PIF-008"})
    return sorted(found)


def variant_id(member: Member) -> str:
    return "u6b_muc1_" + member.member_id.lower().replace("-", "_")


def rule_variant_rows(
    result: dict[str, Any], base: dict[str, str]
) -> list[dict[str, Any]]:
    """One row per member and per MUC1-locus node the member defines."""
    rows = []
    for member in MEMBERS:
        rules = result["members"][member.member_id]["rules"]
        for node_id in CATALOG_NODES:
            if node_id not in rules:
                continue
            if node_id not in base:
                change = "node proposed by this member, absent from v0.5.1"
            elif rules[node_id] == base[node_id]:
                change = "unchanged committed v0.5.1 rule"
            else:
                change = "replaces the committed v0.5.1 rule in memory"
            rows.append(
                {
                    "variant_id": variant_id(member),
                    "node_id": node_id,
                    "expression": rules[node_id],
                    "status": catalog_status(member),
                    "default_in_family": "false",
                    "source_table": str(MEMBERS_TSV),
                    "source_row_id": member.member_id,
                    "evidence_ids": _join(evidence_ids(member)),
                    "notes": (
                        f"EVALUATION ONLY, not adopted and not executable (U6b, TI-02). "
                        f"{member.role}: {member.description}. Licensing "
                        f"{member.licensing}; rule elements "
                        f"{_join(member.elements) or 'none'} "
                        f"(docs/u6b_muc1_reconciliation/rule_elements.tsv). {change}."
                    ),
                }
            )
    return rows


def member_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for member in MEMBERS:
        r = result["members"][member.member_id]
        s = r["structural"]
        rows.append(
            {
                "member_id": member.member_id,
                "role": member.role,
                "description": member.description,
                "placement": member.placement,
                "rule_elements": _join(member.elements),
                "licensing": member.licensing,
                "nodes": s["nodes"],
                "dependencies": s["dependencies"],
                "free_variables": s["free_variables"],
                "distinct_functions": s["distinct_functions"],
                "delta_distinct_functions_vs_v051": r["delta_distinct_functions"],
                "alias_classes": s["alias_classes"],
                "barrier_alias_verdict": r["alias"]["barrier_verdict"],
                "barrier_alias_class_after": _join(r["alias"]["barrier_class_after"]),
                "alias_classes_broken": " | ".join(
                    _join(m) for m in r["alias"]["broken"]
                ),
                "alias_classes_formed": " | ".join(
                    _join(m) for m in r["alias"]["formed"]
                ),
                "alias_enlarged_by_new_nodes": _join(
                    f"{e['node']}:{e['size_before']}->{e['size_after']}"
                    for e in r["alias"]["enlarged_by_new_nodes"]
                ),
                "phenotype_inert_nodes": s["phenotype_inert_nodes"],
                "inert_gained": _join(r["inert_gained"]),
                "inert_lost": _join(r["inert_lost"]),
                "absorbed_dependencies": s["absorbed_dependencies"],
                "never_binding_inhibitions": s["never_binding_inhibitions"],
                "edges_added": _join(f"{a}->{b}[{k}]" for a, b, k in r["edges_added"]),
                "edges_removed": _join(f"{a}->{b}" for a, b in r["edges_removed"]),
                "unsatisfiable_nodes": _join(r["binding"]["unsatisfiable_nodes"]),
                "composed_function_changed_nodes": _join(r["blast_radius"]),
                "clamping_barrier_changes_stable_adhesion": str(
                    r["binding"]["clamping_barrier_changes_stable_adhesion"]
                ).lower(),
                "clamping_barrier_changes_maternal_competence": str(
                    r["binding"]["clamping_barrier_changes_maternal_competence"]
                ).lower(),
                "barrier_on_when_stable_adhesion_is_evaluable": str(
                    r["binding"]["barrier_on_when_stable_adhesion_is_evaluable"]
                ).lower(),
                "global_effective_states": r["identifiability"][
                    "global_effective_states"
                ],
                "design_effective_states_recorded": r["identifiability"][
                    "design_effective_states"
                ],
                "observation_classes": r["identifiability"]["observation_classes"],
                "latent_variables": r["identifiability"]["latent_variables"],
                "design_effective_states_as_declared_plan": (
                    r["design_alias"]["as_declared"]["design_effective_states"]
                ),
                "design_effective_states_maternal_phase_only": (
                    r["design_alias"]["maternal_phase_only"]["design_effective_states"]
                ),
                "matched_unit_conditional": (
                    "design_effective_states_recorded;observation_classes;"
                    "design_effective_states_as_declared_plan;"
                    "design_effective_states_maternal_phase_only"
                ),
            }
        )
    return rows


ELEMENT_COLUMNS = (
    "element_id",
    "rule_text",
    "evidence_ids",
    "evidence_status",
    "members",
    "supports",
    "does_not_support",
)


def element_rows() -> list[dict[str, Any]]:
    return [
        {
            "element_id": e.element_id,
            "rule_text": e.rule_text,
            "evidence_ids": e.evidence_ids,
            "evidence_status": e.evidence_status,
            "members": _join(
                m.member_id for m in MEMBERS if e.element_id in m.elements
            ),
            "supports": e.supports,
            "does_not_support": e.does_not_support,
        }
        for e in RULE_ELEMENTS
    ]


ENDPOINT_COLUMNS = ("member_id", "condition", "unprioritised_setting") + REPORTED


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


GENERATOR_FILES = (
    "src/dt_adoc/reporting/u6b_muc1_family.py",
    "src/dt_adoc/reporting/structure.py",
    "src/dt_adoc/reporting/identifiability.py",
    "src/dt_adoc/reporting/design_alias.py",
)
INPUT_FILES = (
    f"models/superset/{MODEL}/network.bnd",
    f"models/superset/{MODEL}/baseline.cfg",
    f"models/superset/{MODEL}/node_dictionary.tsv",
    "config/planned_design.yaml",
    "config/observation_model_map.tsv",
    "config/calibration.yaml",
)


def input_files(root: Path) -> tuple[str, ...]:
    """Every file the numbers read, the condition cfgs included."""
    conditions = sorted(
        str(p.relative_to(root))
        for p in (root / "models/superset" / MODEL / "conditions").glob("*.cfg")
    )
    return INPUT_FILES + tuple(conditions)


def build(root: Path | None = None) -> dict[Path, str]:
    """The exact bytes of every tracked output."""
    active = root or repo_root()
    result = evaluate(active)
    members = {}
    for member_id, r in result["members"].items():
        members[member_id] = {k: v for k, v in r.items() if k not in ("edges",)}
    payload = {
        "schema_version": "1.0",
        "unit": "U6b",
        "plan": "docs/v05_mechanistic_integration_plan.md §17 U6b; register TI-02",
        "model": MODEL,
        "claim_boundary": (
            "EVALUATION ONLY. No member is adopted, none is written to any "
            "network.bnd, and no model version is created. Structural and design "
            "facts are exhaustive enumerations; endpoints are exact fixed-point "
            "values weighted by baseline.cfg priors, which converged MaBoSS "
            "reproduces (docs/endpoint_convergence_finding.md). No transient, "
            "declared-horizon value, rate or simulation enters. Structural effect "
            "and biological licensing are separate axes."
        ),
        "matched_unit_caveat": MATCHED_UNIT_CAVEAT,
        "readers_of_barrier_in_model": result["readers_of_barrier_in_model"],
        "added_node_metadata": ADDED_NODE_METADATA,
        "frozen_arm": {
            "source": "docs/stage3_experiment_selection.md §12",
            "evaluated_as": f"{FROZEN_ARM_BASE_CFG} overlay with {FROZEN_ARM_OVERRIDE}",
            "assays": list(FROZEN_ARM_ASSAYS),
            "edited": False,
        },
        "members": members,
        "watched_nodes": result["watched_nodes"],
        "contrasts": result["contrasts"],
        "inputs": {p: _sha256(active / p) for p in input_files(active)},
        "generator_files": {p: _sha256(active / p) for p in GENERATOR_FILES},
    }
    return {
        SUMMARY_JSON: json.dumps(payload, indent=2, sort_keys=True) + "\n",
        MEMBERS_TSV: _tsv(member_rows(result), MEMBER_COLUMNS),
        RULE_VARIANTS_TSV: _tsv(
            rule_variant_rows(
                result, parse_bnd_rules(resolve_model(MODEL, active).network_bnd)
            ),
            RULE_VARIANT_COLUMNS,
        ),
        ELEMENTS_TSV: _tsv(element_rows(), ELEMENT_COLUMNS),
        ENDPOINTS_TSV: _tsv(result["endpoints"], ENDPOINT_COLUMNS),
    }


def write(root: Path | None = None) -> dict[Path, str]:
    active = root or repo_root()
    outputs = build(active)
    (active / OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    for path, text in outputs.items():
        (active / path).write_text(text, encoding="utf-8")
    return outputs


def main() -> int:
    write()
    for path in (
        SUMMARY_JSON,
        MEMBERS_TSV,
        RULE_VARIANTS_TSV,
        ELEMENTS_TSV,
        ENDPOINTS_TSV,
    ):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
