"""The biological adjudication of v0.4's rule-induced node merges.

`docs/identifiability/node_classification.tsv` already says *whether* two nodes
are separable and *who* merged them -- `P_global` for the rules, `P_design` for
the arms. It does not say whether a merge is **biologically defensible**, and
that is the question every downstream repair decision turns on. This module
carries the adjudication that answers it.

Three things make it a separate curated file rather than a column somebody types
into the generated table:

* `node_classification.tsv` is **generated**. Editing it directly passes every
  quick check and is silently overwritten by the next
  ``pixi run render-identifiability``. The adjudication is a judgement and has
  to live where a judgement lives.
* An adjudication is **about a specific merge**. `adjudicated_against_rule_class`
  pins the `effective_function_id` the judgement was made against, and loading
  fails if the rules have since moved that node into a different class -- so a
  rule change invalidates the adjudication loudly instead of carrying a stale
  verdict into a model it no longer describes.
* Every row names its **evidence**, checked against
  `context/evidence-register.tsv`, so no verdict rests on an assertion this
  repository cannot trace.

The vocabulary is the draft's trichotomy plus the value it needs to be total.
The trichotomy adjudicates a merge, and 27 of the 59 nodes are not rule-merged
at all; forcing them into one of the three would either overstate (calling a
separable node "biologically collapsed") or understate (calling it
"unidentified" when the rules already separate it). ``NOT_RULE_COLLAPSED`` says
what is true, and its rationale names the *design* collapse where that is the
operative limit -- which is the "model repair versus protocol change"
distinction the identifiability analysis already draws, kept visible rather than
merged into the adjudication.

Scope, stated once so it cannot be read wider: this file adjudicates the
**rule** collapse. A design collapse is a statement about the arms, never about
the biology, and no row here is evidence that two nodes are the same thing
because one experiment cannot tell them apart.
"""

from __future__ import annotations

import csv
from pathlib import Path

from dt_adoc.model.provenance import repo_root

ADJUDICATION_FILE = Path("config") / "coupling_adjudication.tsv"
EVIDENCE_REGISTER = Path("context") / "evidence-register.tsv"
DRUG_TARGET_CATALOG = "drug_target_catalog.tsv"

#: Derived, never curated, and **reported rather than verdict-forcing**: whether
#: a rule-induced merge destroys the ability to tell two of this repository's OWN
#: declared perturbation targets apart. It is a statement about what the model
#: can express, which is orthogonal to whether a collapse is biologically
#: defensible -- see :func:`separability_disagreements`.
#: `drug_target_catalog.tsv` types each executable target -- ligand,
#: pathway_state, protease, adhesive_receptor and so on -- and when two targets
#: of DIFFERENT type are one Boolean function, no arm and no agent can
#: distinguish their perturbations. That is not a judgement about biology, it is
#: a statement about what the model can express, so it is computed from the two
#: committed files rather than written down and allowed to drift.
SEPARABILITY = (
    "MERGES_DISTINCT_TARGET_CLASSES",
    "MERGES_SAME_TARGET_CLASS",
    # Catalogued, and merged only with nodes the catalog does not list. Kept
    # separate from NOT_A_CATALOGUED_TARGET because one value for both meant the
    # column said something false about `E_CDH1_APICAL`, which IS executable in
    # the catalog, and meant a test could assert "not a catalogued target" while
    # proving nothing of the kind.
    "MERGES_NO_CATALOGUED_TARGET",
    "NOT_A_CATALOGUED_TARGET",
    "NOT_RULE_COLLAPSED",
)

COLUMNS = (
    "node_id",
    "adjudicated_against_rule_class",
    "adjudication",
    "rationale",
    "evidence_ids",
    "what_would_change_it",
)

#: The draft's trichotomy, plus the value that makes it total. See the module
#: docstring for why the fourth is not a softening of the other three.
ADJUDICATIONS = frozenset(
    {
        # The rules force an identity the evidence contradicts, or one that
        # makes a distinction the model must be able to draw unreachable.
        "ARTIFICIALLY_COUPLED",
        # The rules make them one function and that is a defensible abstraction
        # at this level of description.
        "BIOLOGICALLY_COLLAPSED",
        # The rules make them one function and nothing available decides whether
        # they really are. Asserted neither way.
        "UNIDENTIFIED",
        # The rules already give this node its own function. Any remaining merge
        # is design-induced and is a protocol question.
        "NOT_RULE_COLLAPSED",
    }
)

#: A rationale shorter than this is a label, not an adjudication. Chosen to be
#: obviously below every real row rather than tuned to them.
MINIMUM_RATIONALE_CHARS = 80


class CouplingAdjudicationError(ValueError):
    """Raised when the adjudication file disagrees with the model or itself."""


def executable_target_classes(
    model_version: str, root: Path | None = None
) -> dict[str, str]:
    """`target_id` -> `target_class`, for the executable catalog rows only.

    Split out of :func:`perturbation_separability` so that a re-derivation
    against a different typing of the same targets reads the catalog the same
    way the criterion does, rather than growing a second reader that can drift.
    """
    active_root = root or repo_root()
    catalog = active_root / "models" / "superset" / model_version / DRUG_TARGET_CATALOG
    with catalog.open(newline="", encoding="utf-8") as handle:
        return {
            row["target_id"]: row["target_class"]
            for row in csv.DictReader(handle, delimiter="\t")
            if row["execution_status"] == "executable"
        }


def perturbation_separability(
    node_ids: tuple[str, ...],
    rule_class_members: dict[str, tuple[str, ...]],
    model_version: str,
    root: Path | None = None,
    target_class: dict[str, str] | None = None,
) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Per node: the separability verdict and the targets it is merged with.

    The criterion the Gate 2 review turned on. `E_LIF` (a **ligand**) and
    `E_GP130_STAT3` (a **pathway_state**) are separate executable rows of the
    drug-target catalog and one Boolean function, so LIF neutralisation and
    STAT3 inhibition -- two perturbations `docs/v05_plan_review.md` lists on the
    same candidate axis -- are the same intervention in the model. They are not
    the same experiment: STAT3 inhibition blocks the pathway whichever ligand
    drives it, and IL11 is the staged candidate that makes that difference real.
    A merge like that is recorded here rather than left to be noticed.

    Same-class merges are reported and are NOT treated the same way. The three
    barrier nodes are all `anti_adhesive_surface`: three molecules the catalog
    types as performing one declared function, whose separation is a question
    for Gate 3b rather than a defect on its face.

    ``NOT_A_CATALOGUED_TARGET`` means exactly what it says -- this node is not an
    executable row of the catalog. A node that IS catalogued but shares its
    Boolean function only with nodes that are not gets
    ``MERGES_NO_CATALOGUED_TARGET`` instead. One value for both would make the
    column state something the catalog contradicts (`E_CDH1_APICAL` is
    executable in it), and would let a test assert "not a catalogued target"
    while proving nothing about catalog membership.

    ``target_class`` overrides the typing without touching the catalog. It exists
    for the U4 re-derivation of TI016, which asks what this criterion reports
    when the free-text ``target_class`` is replaced by a closed vocabulary of
    biological LEVELS. Passing the mapping in, rather than rewriting the frozen
    catalog to see the answer, keeps the question separable from the file it is
    asked about. The catalog is still what decides **membership**: an override
    whose keys are not exactly the executable catalog rows raises, rather than
    letting an unmapped target fall through to a silent
    ``NOT_A_CATALOGUED_TARGET`` that would understate the merge.
    """
    catalogued = executable_target_classes(model_version, root)
    if target_class is None:
        target_class = catalogued
    elif set(target_class) != set(catalogued):
        missing = sorted(set(catalogued) - set(target_class))
        extra = sorted(set(target_class) - set(catalogued))
        raise CouplingAdjudicationError(
            "a target_class override must type exactly the executable catalog "
            f"rows; unmapped: {missing}; not in the catalog: {extra}"
        )

    verdicts: dict[str, tuple[str, tuple[str, ...]]] = {}
    for node_id in node_ids:
        members = rule_class_members[node_id]
        if len(members) == 1:
            verdicts[node_id] = ("NOT_RULE_COLLAPSED", ())
            continue
        if node_id not in target_class:
            verdicts[node_id] = ("NOT_A_CATALOGUED_TARGET", ())
            continue
        partners = tuple(
            sorted(m for m in members if m != node_id and m in target_class)
        )
        if not partners:
            verdicts[node_id] = ("MERGES_NO_CATALOGUED_TARGET", ())
            continue
        distinct = tuple(
            m for m in partners if target_class[m] != target_class[node_id]
        )
        if distinct:
            verdicts[node_id] = ("MERGES_DISTINCT_TARGET_CLASSES", distinct)
        else:
            verdicts[node_id] = ("MERGES_SAME_TARGET_CLASS", partners)
    return verdicts


def _evidence_ids(root: Path) -> set[str]:
    with (root / EVIDENCE_REGISTER).open(newline="", encoding="utf-8") as handle:
        return {
            row["evidence_id"]
            for row in csv.DictReader(handle, delimiter="\t")
            if row["evidence_id"]
        }


def load_coupling_adjudication(root: Path | None = None) -> dict[str, dict[str, str]]:
    """Load the adjudication, keyed by node id. Structural checks only.

    Deliberately does NOT read `network.bnd`: the class pin is verified against
    the identifiability facts by :func:`adjudication_for`, so this function stays
    usable in contexts that have no model loaded.
    """
    active_root = root or repo_root()
    path = active_root / ADJUDICATION_FILE
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = tuple(reader.fieldnames or ())
        if fieldnames != COLUMNS:
            missing = sorted(set(COLUMNS) - set(fieldnames))
            extra = sorted(set(fieldnames) - set(COLUMNS))
            raise CouplingAdjudicationError(
                f"unexpected column set: missing={missing} extra={extra}"
            )
        rows = list(reader)

    if not rows:
        raise CouplingAdjudicationError("adjudication file has no rows")

    known_evidence = _evidence_ids(active_root)
    by_node: dict[str, dict[str, str]] = {}
    for row in rows:
        node_id = (row["node_id"] or "").strip()
        if not node_id:
            raise CouplingAdjudicationError("row missing node_id")
        if node_id in by_node:
            raise CouplingAdjudicationError(f"{node_id}: duplicate row")
        verdict = row["adjudication"]
        if verdict not in ADJUDICATIONS:
            raise CouplingAdjudicationError(
                f"{node_id}: unknown adjudication {verdict!r}"
            )
        if len(row["rationale"].strip()) < MINIMUM_RATIONALE_CHARS:
            raise CouplingAdjudicationError(
                f"{node_id}: rationale is {len(row['rationale'].strip())} "
                f"characters, under the {MINIMUM_RATIONALE_CHARS} required. An "
                "adjudication without a reason is a label."
            )
        if not row["what_would_change_it"].strip():
            raise CouplingAdjudicationError(
                f"{node_id}: no reopening condition. A verdict nothing could "
                "overturn is not a finding."
            )
        cited = [e for e in row["evidence_ids"].split(";") if e]
        if not cited:
            raise CouplingAdjudicationError(f"{node_id}: cites no evidence")
        for evidence_id in cited:
            if evidence_id not in known_evidence:
                raise CouplingAdjudicationError(
                    f"{node_id}: evidence id {evidence_id!r} is not in "
                    f"{EVIDENCE_REGISTER}"
                )
        by_node[node_id] = row
    return by_node


def adjudication_for(
    node_ids: tuple[str, ...],
    rule_class_of: dict[str, str],
    root: Path | None = None,
    *,
    rule_class_members: dict[str, tuple[str, ...]] | None = None,
    model_version: str | None = None,
) -> dict[str, dict[str, str]]:
    """The adjudication for exactly these nodes, with the class pin verified.

    ``rule_class_of`` maps node id to the `effective_function_id` the model
    currently computes for it. Every node must be adjudicated and every
    adjudication must still be about the class it was written against: a rule
    edit that re-partitions the nodes has to be re-adjudicated, not silently
    inherited.
    """
    rows = load_coupling_adjudication(root)
    missing = sorted(set(node_ids) - set(rows))
    if missing:
        raise CouplingAdjudicationError(
            f"nodes with no adjudication: {missing}. Every node in the model "
            "carries one, so a new node cannot enter unadjudicated."
        )
    stale = sorted(set(rows) - set(node_ids))
    if stale:
        raise CouplingAdjudicationError(
            f"adjudications for nodes the model does not have: {stale}"
        )
    for node_id in node_ids:
        pinned = rows[node_id]["adjudicated_against_rule_class"]
        current = rule_class_of[node_id]
        if pinned != current:
            raise CouplingAdjudicationError(
                f"{node_id}: adjudicated against rule class {pinned!r}, which "
                f"the model now computes as {current!r}. The merge this verdict "
                "describes no longer exists; re-adjudicate rather than carry it."
            )

    # Separability is REPORTED, never verdict-forcing. This function used to
    # refuse any node whose signal was MERGES_DISTINCT_TARGET_CLASSES unless it
    # was adjudicated ARTIFICIALLY_COUPLED; see `separability_disagreements` for
    # why that was withdrawn, and for the tripwire that keeps the reported
    # disagreement set from changing silently.
    return rows


def separability_disagreements(
    node_ids: tuple[str, ...],
    rule_class_members: dict[str, tuple[str, ...]],
    model_version: str,
    root: Path | None = None,
) -> dict[str, tuple[str, str]]:
    """Nodes whose separability signal and adjudication point different ways.

    Reported, deliberately, rather than enforced. An earlier version of this
    module raised on load whenever a node with
    ``MERGES_DISTINCT_TARGET_CLASSES`` was adjudicated anything other than
    ``ARTIFICIALLY_COUPLED``, on the reasoning that a merge the model cannot
    express is artificial "by definition". **That conflated two orthogonal
    questions** and is withdrawn:

    * ``perturbation_separability`` asks what the *model can express* -- whether
      two declared interventions collapse to one Boolean function;
    * ``adjudication`` asks whether the *biological collapse is defensible*.

    A merge can be biologically defensible and still destroy a perturbation
    distinction; those are different facts and neither implies the other. The
    repository's own DTR020 reached the same conclusion from a different
    direction, and rates it the most important catalog defect found:
    ``target_class`` is free text with 24 distinct values across 34 rows, 17 of
    them unique, so which merges tripped the invariant depended on naming
    granularity rather than on biology.

    The barrier trio is the demonstration. ``E_PODXL``, ``E_DAG1_FULL`` and
    ``E_MUC1_BARRIER`` are three separately druggable molecules sharing one
    Boolean function -- exactly the condition the old invariant called artificial
    by definition -- and they are adjudicated ``UNIDENTIFIED`` after
    consideration. What exempted them was that somebody happened to give all
    three the same coarse label. Applied consistently the invariant would have
    overridden a curated judgement on the strength of a naming accident.

    Dropping the forcing changes **no** adjudication: every node that currently
    reports ``MERGES_DISTINCT_TARGET_CLASSES`` is independently adjudicated
    ``ARTIFICIALLY_COUPLED`` on its own rationale and evidence, and 11 of the 22
    ``ARTIFICIALLY_COUPLED`` verdicts rest on nodes the catalog does not even
    list. What is removed is an unsound assertion, not a verdict.

    Returns ``{node_id: (separability, adjudication)}`` for each disagreement,
    so the pair can be surfaced and re-adjudicated by a person.
    """
    active_root = root or repo_root()
    rows = load_coupling_adjudication(active_root)
    separability = perturbation_separability(
        node_ids, rule_class_members, model_version, active_root
    )
    return {
        node_id: (verdict, rows[node_id]["adjudication"])
        for node_id, (verdict, _partners) in separability.items()
        if node_id in rows
        and verdict == "MERGES_DISTINCT_TARGET_CLASSES"
        and rows[node_id]["adjudication"] != "ARTIFICIALLY_COUPLED"
    }
