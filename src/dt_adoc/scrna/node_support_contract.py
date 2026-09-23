"""The frozen decision contract of the node-support audit.

WHAT THIS IS. Every threshold, decision rule and gene list that
`docs/scrna/node_support_preregistration.md` fixes before extraction, written
once, here, so that the derivation cannot carry a second copy that drifts from
the document. It is committed in the SAME commit as the pre-registration and
before any audited expression value is read, which is what makes the ordering
checkable in `git log` rather than asserted.

WHAT IT READS. `config/scrna_observation_map.tsv`, and nothing else. No
single-cell object, no per-cell table, no expression value, no model output.
The two exclusion rules are DERIVED from the committed map here rather than
transcribed from the document, so a hand-edit of either is a test failure.

WHY IT IS SEPARATE FROM THE DERIVATION. A constant that lives beside the code
that uses it can be retuned in the same edit that produces the result it
changes. Kept here and pinned by `tests/unit/test_node_support_preregistration.py`,
moving one is a visible diff against a committed document.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MAP = REPO / "config/scrna_observation_map.tsv"

# --------------------------------------------------------------------------
# Section 4.1 -- the four numeric constants
# --------------------------------------------------------------------------

#: Prevalence threshold. The share of a compartment-unit's cells below which a
#: gene is not a compartment-level program even if isolated cells carry it. A
#: STATED CONVENTION, not a measured biological constant, and the only one of
#: the four that is conventional rather than derived.
THETA = 0.01

#: Minimum cells per compartment-unit. DERIVED FROM `THETA`, not chosen: with
#: zero detections in n cells the exact one-sided 95% upper bound on the
#: within-unit cell-level detection rate is 1 - 0.05**(1/n), and n = 299 is the
#: smallest integer putting that bound below `THETA` (0.009969; n = 298 gives
#: 0.010002). 300 is the round number immediately above it, bound 0.009936. It
#: is `THETA`'s inverse image and moves only if `THETA` moves.
N_MIN = 300

#: Minimum exposure in corrected transcript-equivalents per compartment-unit.
#: DERIVED: with zero observed, the 95% bound on the pseudobulk fraction is
#: 3/E, so E_MIN gives 3e-7. The weakest pattern `THETA` admits is 1% of cells
#: carrying one transcript each, f ~ 0.01/15000 ~ 6.7e-7, about 2.2x above that
#: bound -- so at E_MIN, zero detection excludes even the weakest expression the
#: prevalence threshold allows.
E_MIN = 1e7

#: C1, detection integrity. The compartment's high-prevalence transcript must be
#: detected in at least this share of a unit's cells. Committed pooled values
#: are 0.986 (EPCAM, epithelium) and 0.974 (VIM, stroma), so this is a floor
#: with roughly two-fold headroom in both compartments rather than a coin flip.
C1_FLOOR = 0.50

#: C1's gene per compartment. NOT newly curated: both are in the committed
#: context-gene list of `dt_adoc.scrna.klf12_state`.
C1_GENE: dict[str, str] = {"epithelium": "EPCAM", "stroma": "VIM"}

#: C2, compartment specificity. The lineage-DISCRIMINATING transcript must be
#: detected at a strictly higher rate in its own compartment than in the
#: complementary compartment of the same donor and condition. A sign comparison
#: with NO FREE CONSTANT -- there is deliberately no `C2_MARGIN`.
C2_GENE: dict[str, str] = {"epithelium": "EPCAM", "stroma": "COL1A1"}

# --------------------------------------------------------------------------
# Section 4.2 and 5.3 -- label and movement criteria
# --------------------------------------------------------------------------

#: `robustly_detected` requires d >= this in 3/3 donors. A STATED CONVENTION:
#: the level at which a substantial share of the compartment, rather than a
#: minority, carries the transcript.
ROBUST_DETECTION = 0.10

#: Material movement, criterion (b): at least two-fold on the pseudobulk
#: fraction. The conventional minimum effect treated as biologically meaningful
#: in expression analysis, and far above the numerical noise of a ratio over
#: >= E_MIN exposure. Stated as a convention.
LOG2_FOLD_MIN = 1.0

#: Within-donor precision. Cells are resampled with replacement to give a 95%
#: interval on f and d. The interval expresses HOW PRECISELY THIS DONOR'S
#: SAMPLED CELLS MEASURE THAT DONOR and nothing else: it is not a
#: biological-replicate interval, is never pooled across donors, and no
#: across-donor statistic is computed from it.
BOOTSTRAP_B = 2000
BOOTSTRAP_SEED = 20260917
BOOTSTRAP_ALPHA = 0.05

#: Donors. Three, and the biological unit. Cells are within-unit measurement
#: precision and are never biological replicates.
DONORS: tuple[str, ...] = ("SZ09", "SZ10", "SZ25")
CONDITIONS: tuple[str, ...] = ("CNT", "HT")

# --------------------------------------------------------------------------
# Section 1 -- the compartment partition
# --------------------------------------------------------------------------

#: A complete, condition-independent partition of all 28,212 cells, fixed
#: before any value was read. Every individual `celltype_v2` label is 80-99%
#: one condition, so a label-level CNT-vs-HT contrast is close to contrasting a
#: variable with itself; both primary compartments are well populated in both
#: arms. The partition is a DEFINITION and its condition balance is a recorded
#: diagnostic, not an assumption.
COMPARTMENT_OF_LABEL: dict[str, str] = {
    "Luminal-like epithelium": "epithelium",
    "Cycling epithelium": "epithelium",
    "HT epithelium I": "epithelium",
    "HT epithelium II": "epithelium",
    "Stroma": "stroma",
    "HT stroma": "stroma",
    "Myofibroblast": "myofibroblast",
}

#: `myofibroblast` is reported separately and excluded from the stromal
#: primary: 365 cells across six units, and it is not the decidualizing
#: compartment. A declared sensitivity, decided before results.
PRIMARY_COMPARTMENTS: tuple[str, ...] = ("epithelium", "stroma")

#: The map's `compartment` column to the analysis compartment.
COMPARTMENT_OF_NODE: dict[str, str] = {
    "epithelial": "epithelium",
    "stromal": "stroma",
}

# --------------------------------------------------------------------------
# Section 5.5 -- classes
# --------------------------------------------------------------------------

#: Alias classes in the order the audit tests them. AC03 first -- NOT because it
#: is the largest assessable class, which is AC01, but because
#: `config/coupling_adjudication.tsv` already records `E_PGR` and `S_PGR` as
#: UNIDENTIFIED with a `what_would_change_it` this unit can answer.
ALIAS_TEST_ORDER: tuple[str, ...] = ("AC03", "AC02", "AC04", "AC01")

#: Measured for node support, NOT alias-tested: the adjudication records AC05 as
#: deliberately UNIDENTIFIED, and `E_DAG1_FULL` is a genuine assay limit -- the
#: transcript cannot distinguish intact from cleaved DAG1 -- so a divergence
#: test there would be testing the assay, not the model.
NODE_SUPPORT_ONLY_CLASSES: tuple[str, ...] = ("AC05",)

#: Values of `measurement_observability` that mean nothing is measured and
#: nothing is inferred.
NOT_ASSESSABLE = "not_observable"

#: `E_KLF12_HIGH` carries a node-support label like the other twenty-six, but
#: its per-unit values were committed before this design existed, so the row is
#: tagged and licenses nothing on its own. The prior question is closed.
NOT_BLIND_NODES: frozenset[str] = frozenset({"E_KLF12_HIGH"})

#: Section 7's measurement-type axis, one entry per value the map actually
#: uses. `pathway_score` keeps its own name rather than being folded into
#: `gene_program`: it is the map's label for `S_FGF_MITOGENIC`, whose features
#: are ligand transcripts PLUS a negative-feedback target readout, and calling
#: that a gene program would assert a claim ceiling the map does not record.
#: An earlier revision collapsed it, and Appendix A printed a type for that node
#: and for `S_HAND2` that the map contradicts. The type is now DERIVED here and
#: the document is compared against it.
MEASUREMENT_TYPE: dict[str, str] = {
    "direct_transcript": "direct_transcript",
    "gene_program": "gene_program",
    "regulon_activity": "regulon_or_activity_proxy",
    "proxy_abundance_not_activity": "abundance_proxy_only",
    "pathway_score": "pathway_score",
    NOT_ASSESSABLE: "not_RNA_assessable",
}

#: How Appendix A prints each type. Presentation only -- the authority is the
#: committed map, and the test compares the printed column against it.
MEASUREMENT_TYPE_LABEL: dict[str, str] = {
    "direct_transcript": "direct transcript",
    "gene_program": "gene program",
    "regulon_or_activity_proxy": "regulon/activity proxy",
    "abundance_proxy_only": "abundance proxy",
    "pathway_score": "pathway score",
    "not_RNA_assessable": "not RNA-assessable",
}


def measurement_type(row: dict[str, str]) -> str:
    """Section 7's measurement type for a row, from the committed map."""
    return MEASUREMENT_TYPE[row["measurement_observability"]]


# --------------------------------------------------------------------------
# Section 2.1 -- R2, a READING of committed text
# --------------------------------------------------------------------------

#: R2 excludes a gene from a node's DIRECTION VOTE when the map's own
#: `claim_ceiling` records that its transcript direction does not track the
#: node's state. This is a reading of committed prose and not a decidable
#: predicate over it: the map has no machine-readable direction field. The
#: distinction drawn is between a ceiling on LEVEL -- which `S_NR2F2`,
#: `S_HAND2` and `S_TAZ_ECM` each carry IN THEIR OWN WORDS (see
#: `LEVEL_CEILING_QUOTES`; an earlier revision quoted one row's sentence and
#: attributed it to all three), and which does not stop a direction being read
#: -- and a ceiling on DIRECTION. The value
#: is the sentence that licenses the exclusion; the test asserts each is still
#: present verbatim in the committed map, so the reading cannot outlive its
#: grounds.
R2_EXCLUSIONS: dict[tuple[str, str], str] = {
    ("E_PGR", "PGR"): (
        "in endometrium epithelial PGR falls exactly when progesterone "
        "signalling is highest, so the transcript can move opposite to the state"
    ),
    ("S_PGR", "PGR"): "As E_PGR.",
    ("E_GP130_STAT3", "STAT3"): (
        "STAT3 TRANSCRIPT IS A POOR PROXY FOR PHOSPHO-STAT3; only a downstream "
        "target program is defensible"
    ),
}

#: The rows that carry a ceiling on LEVEL and are deliberately NOT excluded by
#: R2. They are quoted and checked exactly as the exclusions are, because the
#: argument that R2 is an honest reading rests on the contrast between these
#: sentences and the two that do exclude -- and a contrast whose other half is
#: unverified is not a contrast.
LEVEL_CEILING_QUOTES: dict[str, str] = {
    "S_NR2F2": "TF TRANSCRIPT IS NOT TF ACTIVITY",
    "S_HAND2": "HAND2 is a TF, so expression is not regulatory activity",
    "S_TAZ_ECM": "WWTR1 transcript is not TAZ nuclear localisation",
}

#: A program reduced below this many voting genes by R1/R2 cannot be
#: direction-called and is recorded `uninformative`. At exactly 2 both must
#: agree; above 2 a strict majority must agree.
MIN_VOTING_GENES = 2


class ContractError(RuntimeError):
    """The frozen contract disagrees with the committed observation map."""


def observation_rows(map_path: Path = MAP) -> list[dict[str, str]]:
    """Every row of the committed map, verbatim."""
    with map_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        raise ContractError(f"{map_path} carries no rows")
    return rows


def features(row: dict[str, str]) -> tuple[str, ...]:
    """A node's measurement features, verbatim from the committed map.

    No feature is added, substituted, dropped for convenience, or newly curated
    in this unit. That list was fixed before this analysis existed, and treating
    it as frozen input is what keeps the audit from becoming a gene hunt.
    """
    raw = row["measurement_features"].strip()
    return tuple(g for g in raw.split(";") if g) if raw else ()


def assessable_nodes(map_path: Path = MAP) -> dict[str, dict[str, str]]:
    """The RNA-assessable rows, keyed by node. Twenty-seven of them."""
    return {
        r["model_node"]: r
        for r in observation_rows(map_path)
        if r["measurement_observability"] != NOT_ASSESSABLE
    }


def audited_genes(map_path: Path = MAP) -> tuple[str, ...]:
    """Every gene any assessable node measures, sorted, deduplicated."""
    seen: set[str] = set()
    for row in assessable_nodes(map_path).values():
        seen.update(features(row))
    return tuple(sorted(seen))


def r1_programs(map_path: Path = MAP) -> dict[str, tuple[str, ...]]:
    """R1 -- same-class self-measurement, applied mechanically to the map.

    In a within-class test, a composite member's program excludes every gene
    that is the ENTIRE measurement of another member of the same class.
    Otherwise the test asks whether a member agrees with itself.

    This is computed from the committed map, never transcribed: if the map
    changes, the programs change with it and the test that compares them to the
    pre-registration's table fails loudly.
    """
    rows = assessable_nodes(map_path)
    # A BLANK `v04_function_class` IS NOT A CLASS. The map leaves it empty for
    # the rows it records as classes of one -- `E_ESTROGENIC_PROLIFERATION`,
    # `E_KLF12_HIGH`, `S_FGF_MITOGENIC`, `S_HAND2`. Keying on the raw value put
    # all four in one bucket and made KLF12 and HAND2 "siblings' whole
    # measurements" for the other two, which is the opposite of what R1 says and
    # of what the pre-registration argues at `S_HAND2`. It deleted nothing only
    # because neither gene appears in the other two programs; a later map edit
    # would have removed a voting gene silently. Each classless row is its own
    # class, so it has no siblings.
    by_class: dict[str, list[str]] = {}
    for node, row in rows.items():
        key = row["v04_function_class"].strip() or f"\0classless:{node}"
        by_class.setdefault(key, []).append(node)
    class_key = {
        node: (row["v04_function_class"].strip() or f"\0classless:{node}")
        for node, row in rows.items()
    }

    programs: dict[str, tuple[str, ...]] = {}
    for node, row in rows.items():
        own = features(row)
        siblings = [s for s in by_class[class_key[node]] if s != node]
        singletons = {
            features(rows[s])[0] for s in siblings if len(features(rows[s])) == 1
        }
        # A member measured by a single gene is not composite; R1 cannot reduce
        # it, and reducing it would delete the measurement rather than a
        # self-comparison.
        programs[node] = (
            own if len(own) == 1 else tuple(g for g in own if g not in singletons)
        )
    return programs


def direction_vote_programs(map_path: Path = MAP) -> dict[str, tuple[str, ...]]:
    """The genes that vote on a node's CNT->HT direction: R1, then R2.

    Node support (Section 4) uses the full committed feature list; only the
    within-class concordance test (Section 5) uses this.
    """
    after_r1 = r1_programs(map_path)
    return {
        node: tuple(g for g in program if (node, g) not in R2_EXCLUSIONS)
        for node, program in after_r1.items()
    }


def verify_r2_grounds(map_path: Path = MAP) -> None:
    """Every R2 exclusion still quotes text the committed map actually carries.

    R2 is a reading, so what can be checked is not the reading but its grounds.
    If the sentence licensing an exclusion is edited out of the map, the
    exclusion loses its footing and this raises rather than continuing on a
    rule no longer written down anywhere.
    """
    rows = assessable_nodes(map_path)
    for (node, gene), sentence in R2_EXCLUSIONS.items():
        if node not in rows:
            raise ContractError(
                f"R2 excludes {gene} from {node}, which is not assessable"
            )
        if gene not in features(rows[node]):
            raise ContractError(
                f"R2 excludes {gene} from {node}, which does not measure it"
            )
        if sentence not in rows[node]["claim_ceiling"]:
            raise ContractError(
                f"the map no longer carries the sentence licensing the R2 "
                f"exclusion of {gene} from {node}: {sentence!r}"
            )
    for node, sentence in LEVEL_CEILING_QUOTES.items():
        if sentence not in rows[node]["claim_ceiling"]:
            raise ContractError(
                f"the map no longer carries the level-ceiling sentence quoted "
                f"for {node}, which R2 deliberately does NOT exclude: {sentence!r}"
            )
