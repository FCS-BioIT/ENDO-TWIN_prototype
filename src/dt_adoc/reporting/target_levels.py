"""U4 / TI016: the Gate 2 separability criterion re-derived on a CLOSED vocabulary.

`drug_target_catalog.tsv` types every executable target with a free-text
`target_class`: 24 distinct values across 34 rows, 17 of them appearing exactly
once. DTR020 rates that this repository's single most important catalog defect,
because *which* rule-induced merges trip the separability criterion then follows
naming granularity rather than biology. Its `what_would_change_it` asks for "a
closed, documented `target_class` vocabulary defined by biological LEVEL (ligand
/ receptor / pathway / protease / glycan / TF / ECM / mechanical / state /
readout), with the Gate 2 invariant re-derived against it and every changed
verdict surfaced individually."

This module is that re-derivation, and three things about how it is done are
deliberate.

**The catalog is not rewritten.** The question "what does the criterion report
under a different typing" is answered by passing the typing in, not by editing
the frozen file the question is about. `drug_target_catalog.tsv` is byte-pinned
in v0.4 (T-H) and in the v0.5 scaffold, and DTR021 records separately that some
rows' `execution_status` is wrong -- a change that removes catalog ground for
real coupling verdicts and is not U4's to make. Editing the catalog to see the
answer would also be the "move the rule rather than the code" failure mode.

**One implementation of the verdict rule.** The level verdicts come from
`coupling.perturbation_separability` with a `target_class` override, not from a
second copy of the same logic. A re-derivation that reimplemented the criterion
could differ from the criterion it claims to re-derive, and nothing would say so.

**The answer is reported with its own fragility.** A level assignment is a
judgement, so "no verdict changed" is worth little on its own: what matters is
how many assignments would have to move to change it. :func:`rederive` reports,
per node, the minimum number of catalogued class-members that would have to be
relabelled to flip its verdict. That converts a judgement-dependent result into
a stated dependency, and it is what makes DTR020's own demonstration -- the
barrier trio -- legible rather than rhetorical.

**What this does NOT do.** It does not force, change or propose any coupling
adjudication. The invariant `MERGES_DISTINCT_TARGET_CLASSES` => `ARTIFICIALLY_
COUPLED` was withdrawn on 2026-09-16 (`docs/coupling_adjudication.md` 2.1) and
is reported rather than enforced, so even a flipped signal moves a reported
column and nothing else. `separability_disagreements` remains the tripwire.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from dt_adoc.reporting.coupling import (
    executable_target_classes,
    perturbation_separability,
)
from dt_adoc.reporting.identifiability import load_identifiability, repo_root

MODEL_VERSION = "adoc-literature-superset-v0.4.0"
OUT_MD = Path("docs/gate2_target_level_rederivation.md")
OUT_TSV = Path("docs/gate2_target_level_rederivation.tsv")

#: The closed vocabulary: DTR020's ten levels, plus three additions, each
#: recorded here rather than slipped in. A level is kept even when no executable
#: row uses it, because a vocabulary only as large as today's catalog closes
#: nothing.
#:
#: The additions:
#:
#: * ``input`` -- DTR020's list types model-internal targets and has no level for
#:   an exogenous agent or boundary condition. Four free-text values are exactly
#:   that (`perturbation_input`, `input`, `boundary_input`, `external_input`) and
#:   collapsing them into `ligand` would type mifepristone as a ligand of the
#:   model, which it is not.
#: * ``surface_molecule`` -- a cell-surface protein or protein complex whose
#:   abundance or localisation IS the modelled state. DTR020's list has
#:   `receptor` and `glycan` but no level for a mucin, a sialomucin, a
#:   tetraspanin complex or a junction protein.
#: * ``cytoskeleton`` -- intracellular structural remodelling, which is neither
#:   a pathway nor a surface molecule.
#:
#: `readout` is declared and unused: no executable row is a pure readout. That is
#: correct and is asserted, because `E_PAEP`, the repository's canonical readout,
#: is deliberately NOT in the catalog.
LEVELS: tuple[str, ...] = (
    "input",
    "ligand",
    "receptor",
    "pathway",
    "transcription_factor",
    "protease",
    "glycan",
    "surface_molecule",
    "cytoskeleton",
    "ecm",
    "mechanical",
    "state",
    "readout",
)

#: Every one of the 24 free-text `target_class` values, mapped to exactly one
#: level, with the reason. Curated once, here rather than in the catalog, and
#: total over the file: :func:`target_levels` raises on a value it has never
#: seen, so a catalog edit cannot quietly acquire an untyped class.
#:
#: The two assignments that carry the result are stated as such:
#:
#: * `anti_adhesive_surface` -> ``surface_molecule``. PODXL, full-length
#:   alpha-dystroglycan and the MUC1 glycocalyx are three different molecules
#:   performing one declared function, and at the LEVEL axis all three are
#:   cell-surface molecules whose abundance is what an agent would act on. This
#:   is the assignment DTR020 predicted would be doing the work, and it is.
#: * `adhesive_effector` -> split is NOT available: the value covers
#:   `E_MUC1_SLEX` (a carbohydrate epitope), `E_CD98_CD9` (a transmembrane
#:   complex) and `E_CDH1_APICAL` (a junction protein), which is precisely the
#:   lumping DTR020 objects to. A free-text value maps to ONE level, so the
#:   split is made where the level genuinely differs -- see
#:   :data:`LEVEL_OF_TARGET`, which overrides per target for exactly this case
#:   and records why.
LEVEL_OF_TARGET_CLASS: dict[str, tuple[str, str]] = {
    "perturbation_input": ("input", "an agent the experimenter adds or withholds"),
    "input": ("input", "an exogenous signal supplied to the culture"),
    "boundary_input": ("input", "a boundary condition set by the platform"),
    "external_input": (
        "input",
        "an exogenous cue declared outside the executable model",
    ),
    "regulator": (
        "receptor",
        (
            "PGR activity: a ligand-activated nuclear receptor, and the level a "
            "receptor antagonist acts on (mifepristone is catalogued separately as "
            "the agent)"
        ),
    ),
    "negative_regulator": (
        "transcription_factor",
        (
            "KLF12 is a Kruppel-like transcription factor; the node is its "
            "transcriptional state"
        ),
    ),
    "transcription_factor": (
        "transcription_factor",
        "stromal HAND2: the free-text value already names the level",
    ),
    "ligand": ("ligand", "a secreted protein acting on a receptor"),
    "growth_factor_effector": (
        "ligand",
        (
            "HB-EGF is shed and acts extracellularly on ERBB receptors; it is a "
            "ligand at this axis whatever the node's own claim ceiling says about "
            "transcript-versus-protein"
        ),
    ),
    "decidual_effector": (
        "ligand",
        "stromal SPP1/osteopontin is a secreted matricellular ligand",
    ),
    "extracellular_bridge": (
        "ligand",
        "the free maternal SPP1 pool is the same secreted ligand as a pool",
    ),
    "paracrine_inhibitor_of_receptivity": (
        "ligand",
        "stromal mitogenic FGF output is secreted FGF",
    ),
    "pathway_state": ("pathway", "intracellular signalling-pathway activity"),
    "protease": ("protease", "PC6/PCSK5 enzymatic activity"),
    "adhesive_receptor": (
        "receptor",
        "alphaVbeta3/alphaVbeta5 integrin engagement state",
    ),
    "anti_adhesive_surface": (
        "surface_molecule",
        (
            "PODXL, full-length alpha-dystroglycan and the MUC1 glycocalyx: three "
            "cell-surface molecules whose abundance is the barrier"
        ),
    ),
    "adhesive_surface_release": (
        "surface_molecule",
        (
            "the PC6-cleaved alpha-dystroglycan product is a surface molecule in a "
            "second state; the ENZYME is typed protease separately, which is the "
            "dissociation Heng 2015 established"
        ),
    ),
    "adhesive_effector": (
        "surface_molecule",
        (
            "default for the value; overridden per target for E_MUC1_SLEX, which is "
            "a glycan epitope rather than the protein carrying it"
        ),
    ),
    "cytoskeletal_effector": (
        "cytoskeleton",
        (
            "ANXA2-RHOA-F-actin remodelling is intracellular structure, not a "
            "surface molecule and not a pathway"
        ),
    ),
    "mechanical_regulator": (
        "ecm",
        (
            "stromal TAZ/WWTR1 ECM remodelling acts on matrix composition; the "
            "PHYSICAL permissiveness it produces is typed mechanical separately"
        ),
    ),
    "dynamic_matrix_regulator": (
        "ecm",
        "balanced decidual senescence/remodelling, same axis as the above",
    ),
    "latent_state": (
        "mechanical",
        (
            "mechanical and dynamic ECM permissiveness is the physical state, not "
            "the matrix composition that sets it"
        ),
    ),
    "anti_receptive_state": (
        "state",
        "a derived proliferative cell state with no single molecular target",
    ),
    "candidate_effector": (
        "surface_molecule",
        "LGALS1/3 and BSG-ITGB1 interface states are surface interactions",
    ),
}

#: Per-target overrides, for the one case where a free-text value spans two
#: levels. `adhesive_effector` covers a glycan epitope and two proteins, and
#: DTR020 names that lumping explicitly; typing `E_MUC1_SLEX` by its class would
#: reproduce the defect the re-derivation exists to test for.
#:
#: The MUC1 pair is the reason this override cannot be avoided by choosing a
#: coarser level. `E_MUC1_SLEX` and `E_MUC1_BARRIER` are the SAME molecule in two
#: glycosylation states (plan section 3.3: one feature, two nodes, exact logical
#: complements), and they are targeted at different levels -- the sLeX epitope
#: through glycosyltransferases, the barrier through MUC1 abundance or shedding.
LEVEL_OF_TARGET: dict[str, tuple[str, str]] = {
    "E_MUC1_SLEX": (
        "glycan",
        (
            "a carbohydrate epitope, targeted through glycosyltransferases; the "
            "MUC1 protein that carries it is typed surface_molecule as "
            "E_MUC1_BARRIER"
        ),
    ),
}


class TargetLevelError(ValueError):
    """Raised when the catalog carries a `target_class` this vocabulary misses."""


def target_levels(
    model_version: str = MODEL_VERSION, root: Path | None = None
) -> dict[str, str]:
    """Executable `target_id` -> closed level. Total, or it raises."""
    classes = executable_target_classes(model_version, root)
    unknown = sorted({v for v in classes.values() if v not in LEVEL_OF_TARGET_CLASS})
    if unknown:
        raise TargetLevelError(
            f"target_class values with no level assignment: {unknown}. Assign "
            "each one in LEVEL_OF_TARGET_CLASS with its reason; do not widen an "
            "existing level to absorb it silently."
        )
    levels = {
        target: LEVEL_OF_TARGET_CLASS[value][0] for target, value in classes.items()
    }
    for target, (level, _why) in LEVEL_OF_TARGET.items():
        if target in levels:
            levels[target] = level
    bad = sorted({v for v in levels.values() if v not in LEVELS})
    if bad:  # pragma: no cover - guarded by the test, kept so it cannot pass
        raise TargetLevelError(f"levels outside the closed vocabulary: {bad}")
    return levels


def _flip_distance(members: tuple[str, ...], labels: dict[str, str]) -> int:
    """Minimum relabellings that would flip this node's verdict.

    ``members`` are the catalogued members of the node's Boolean-function class,
    the node included. If they all carry one label the verdict is
    ``MERGES_SAME_TARGET_CLASS`` and moving any single member flips it. If they
    do not, flipping the other way means collapsing every member onto one label,
    which costs the class size minus its largest existing group.
    """
    counts = Counter(labels[m] for m in members)
    if len(counts) == 1:
        return 1
    return len(members) - max(counts.values())


def rederive(model_version: str = MODEL_VERSION, root: Path | None = None) -> dict:
    """Both separability passes over the same classes, plus their fragility."""
    active = root or repo_root()
    facts = load_identifiability(model_version, active)
    classes = {n: members for members in facts.global_classes for n in members}

    free_text = executable_target_classes(model_version, active)
    levels = target_levels(model_version, active)

    before = perturbation_separability(facts.node_ids, classes, model_version, active)
    after = perturbation_separability(
        facts.node_ids, classes, model_version, active, target_class=levels
    )

    rows = []
    for node_id in facts.node_ids:
        free_verdict, free_partners = before[node_id]
        level_verdict, level_partners = after[node_id]
        catalogued_members = tuple(sorted(m for m in classes[node_id] if m in levels))
        fragility = (
            _flip_distance(catalogued_members, levels)
            if len(catalogued_members) > 1 and node_id in levels
            else None
        )
        rows.append(
            {
                "node_id": node_id,
                "target_class_free_text": free_text.get(node_id, ""),
                "target_level_closed": levels.get(node_id, ""),
                "separability_free_text": free_verdict,
                "separability_closed_vocabulary": level_verdict,
                "changed": free_verdict != level_verdict,
                "catalogued_class_members": catalogued_members,
                "merged_with_free_text": free_partners,
                "merged_with_closed": level_partners,
                "relabellings_to_flip": fragility,
            }
        )

    changed = [r for r in rows if r["changed"]]
    # One row per Boolean-function class that has at least two catalogued
    # members: these are the only places any typing can matter at all.
    class_rows = []
    seen: set[tuple[str, ...]] = set()
    for members in facts.global_classes:
        catalogued = tuple(sorted(m for m in members if m in levels))
        if len(catalogued) < 2 or catalogued in seen:
            continue
        seen.add(catalogued)
        counts = Counter(levels[m] for m in catalogued)
        class_rows.append(
            {
                "members": catalogued,
                "levels": {m: levels[m] for m in catalogued},
                "verdict": (
                    "MERGES_SAME_TARGET_CLASS"
                    if len(counts) == 1
                    else "MERGES_DISTINCT_TARGET_CLASSES"
                ),
                "relabellings_to_flip": _flip_distance(catalogued, levels),
            }
        )
    class_rows.sort(key=lambda r: (r["relabellings_to_flip"], r["members"]))

    return {
        "model_version": model_version,
        "rows": rows,
        "changed": changed,
        "classes": class_rows,
        "levels": levels,
        "free_text_values": sorted(set(free_text.values())),
        "executable_targets": len(free_text),
        "levels_used": sorted(set(levels.values())),
    }


def render(report: dict) -> str:
    lines: list[str] = []
    a = lines.append
    # The banner carries no generation date. A wall-clock stamp made an
    # unchanged report rewrite itself on a new day, so a clean checkout went
    # dirty for nothing; pinned by
    # test_generated_date_determinism.ClockFrozenRegenerationTest.
    a("# Gate 2 separability, re-derived against a closed target-level vocabulary")
    a("")
    a(
        "> **Generated file — do not edit.** Regenerate with "
        "`pixi run build-target-level-rederivation`. Computed by running "
        "`coupling.perturbation_separability` twice over the same "
        f"Boolean-function classes of `{report['model_version']}` — once with the "
        "catalog's free-text `target_class`, once with a closed vocabulary of "
        "biological levels."
    )
    a("")
    a(
        f"`drug_target_catalog.tsv` types **{report['executable_targets']}** "
        f"executable targets with **{len(report['free_text_values'])}** distinct "
        "free-text values. DTR020 rates the free text this repository's most "
        "important catalog defect, because which merges trip the criterion then "
        "follows naming granularity. This re-derives the criterion on "
        f"**{len(report['levels_used'])}** of the {len(LEVELS)} declared "
        "biological levels and surfaces every changed verdict."
    )
    a("")
    a(
        f"**A smaller exposure than the catalog defect.** DTR020 and the plan's "
        "section 4.2 both count **34 rows, 24 distinct values**, which is the "
        "whole catalog. The criterion reads only rows with "
        "`execution_status = executable`, so what it can actually see is "
        f"**{report['executable_targets']} rows, "
        f"{len(report['free_text_values'])} values**: the "
        f"{34 - report['executable_targets']} non-executable rows carry "
        "`dynamic_matrix_regulator`, `candidate_effector` and `external_input`, "
        "three values no separability verdict has ever depended on. The defect "
        "is real; its reach through this criterion is narrower than the headline "
        "count implies."
    )
    a("")
    a("## Result")
    a("")
    if report["changed"]:
        a(
            f"**{len(report['changed'])} node(s) change verdict** under the closed "
            "vocabulary:"
        )
        a("")
        a("| Node | free-text class | level | free-text verdict | closed verdict |")
        a("|---|---|---|---|---|")
        for r in report["changed"]:
            a(
                f"| `{r['node_id']}` | `{r['target_class_free_text']}` | "
                f"`{r['target_level_closed']}` | `{r['separability_free_text']}` | "
                f"`{r['separability_closed_vocabulary']}` |"
            )
    else:
        a(
            "**No node changes verdict.** Every separability signal the "
            "criterion reports is the same under the closed vocabulary as under "
            "the free text."
        )
    a("")
    a(
        "That is a weak result on its own — a vocabulary is a judgement, and one "
        "chosen after seeing the answer could reproduce it. What follows is the "
        "part that is not a judgement: **how far each signal is from flipping**, "
        "computed as the minimum number of catalogued class members that would "
        "have to be relabelled."
    )
    a("")
    a("## Where the typing is load-bearing")
    a("")
    a(
        "Only a Boolean-function class with at least two catalogued members can "
        "be affected by any typing at all. There are "
        f"**{len(report['classes'])}** of them."
    )
    a("")
    a("| Class members | levels | verdict | relabellings to flip |")
    a("|---|---|---|---|")
    for c in report["classes"]:
        members = ", ".join(f"`{m}`" for m in c["members"])
        levels = ", ".join(f"`{c['levels'][m]}`" for m in c["members"])
        a(
            f"| {members} | {levels} | `{c['verdict']}` | **{c['relabellings_to_flip']}** |"
        )
    a("")
    a(
        "> **Nothing here forces an adjudication.** The invariant "
        "`MERGES_DISTINCT_TARGET_CLASSES` ⇒ `ARTIFICIALLY_COUPLED` was withdrawn "
        "on 2026-09-16 (`docs/coupling_adjudication.md` §2.1) and is reported "
        "rather than enforced, so a flipped signal would move a reported column "
        "and no verdict. `config/coupling_adjudication.tsv` is untouched by this "
        "computation."
    )
    a("")
    a("## The vocabulary")
    a("")
    a(
        "Closed set: "
        + ", ".join(f"`{level}`" for level in LEVELS)
        + ". Levels with no executable target today are kept, because a "
        "vocabulary only as large as the current catalog closes nothing."
    )
    a("")
    a("| free-text `target_class` | level | why |")
    a("|---|---|---|")
    for value in sorted(LEVEL_OF_TARGET_CLASS):
        level, why = LEVEL_OF_TARGET_CLASS[value]
        a(f"| `{value}` | `{level}` | {why} |")
    a("")
    a("Per-target overrides, where one free-text value spans two levels:")
    a("")
    a("| target | level | why |")
    a("|---|---|---|")
    for target in sorted(LEVEL_OF_TARGET):
        level, why = LEVEL_OF_TARGET[target]
        a(f"| `{target}` | `{level}` | {why} |")
    a("")
    return "\n".join(lines) + "\n"


def build(root: Path | None = None) -> tuple[Path, Path]:
    active = root or repo_root()
    report = rederive(MODEL_VERSION, active)
    md = active / OUT_MD
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(render(report), encoding="utf-8")
    tsv = active / OUT_TSV
    with tsv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "node_id",
                "target_class_free_text",
                "target_level_closed",
                "separability_free_text",
                "separability_closed_vocabulary",
                "changed",
                "catalogued_class_members",
                "relabellings_to_flip",
            ]
        )
        for row in report["rows"]:
            writer.writerow(
                [
                    row["node_id"],
                    row["target_class_free_text"],
                    row["target_level_closed"],
                    row["separability_free_text"],
                    row["separability_closed_vocabulary"],
                    row["changed"],
                    ";".join(row["catalogued_class_members"]),
                    ""
                    if row["relabellings_to_flip"] is None
                    else row["relabellings_to_flip"],
                ]
            )
    return md, tsv


if __name__ == "__main__":  # pragma: no cover
    md, tsv = build()
    print(f"wrote {md}")
    print(f"wrote {tsv}")
