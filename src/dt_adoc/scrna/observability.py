"""Build `config/scrna_observation_map.tsv`: measurement reach vs model reach.

WHAT THIS IS FOR. Before any model node is conditioned on the ADOC single-cell
data, two questions have to be answered per node, and they are about two
different systems:

1. **What can the MEASUREMENT see and separate?** A transcript is not an
   activity, a ligand is not a signal, a glycosyltransferase program is not a
   measured surface glycan, and a localisation or cleavage state is not
   observable by RNA at all. `AGENTS.md` requires these distinctions.

2. **What can v0.4 REPRESENT?** Thirty-two of the fifty-nine nodes realise only
   eight distinct Boolean functions of the free variables, so under the current
   rules `S_PRL` and `S_IGFBP1` co-vary exactly.

KEEPING THESE APART IS THE POINT, and an earlier revision of this module
collapsed them. It said an observation "resolves the CLASS, not this node" and
that conditioning one member "conditions the others identically". Both are
wrong, and the error mattered because it blamed the data for a limitation of the
model.

* **The measurement separates them fine.** PRL and IGFBP1 are separately
  quantifiable transcripts. If they disagree experimentally, that does not mean
  the measurement failed to resolve them -- it means **v0.4 cannot represent a
  distinction the data can measure**, which is a model deficiency and a
  falsification of the aliasing.
* **Function equality is not interventional equivalence.** Clamping `S_PRL`
  overrides `S_PRL`'s rule; `S_IGFBP1` keeps its own and is unaffected. This
  repository demonstrates the asymmetry in its own numbers: `E_CD98_CD9` is
  phenotype-inert while `E_GP130_STAT3`, in the same function class, is not.

So the honest headline is not "scRNA can only see nine things". It is: **27
named biological states have some scRNA observability, but the v0.4 rule set
compresses them into 9 native Boolean signatures, so the model cannot
independently represent much of what the data could measure.** That is a
representational deficit in the model, and it is what makes further measurement
and further perturbation worth doing.

DERIVED VERSUS CURATED, kept strictly apart. Function class, class size,
membership, phenotype-inertness and evidence class are **derived** from the
executable model by exhaustive enumeration, and `load_scrna_observation_map`
re-derives and re-checks them. Evidence role is derived too, from whether a
measurement's features were used to construct the model -- partly from the
canonical records directly (`P1-EPI-STATE` and `P1-STR-STATE` carry structured
analyte composites) and partly from a small curated residue for two readouts
that carry no structured membership at all. That split is explicit, and a
fingerprint over the source records trips if they move, because a duplicated
list that cannot notice its sources changing is exactly the drift hole this
module previously had. The observability
judgements are **curated** and carry an explicit claim ceiling.

WHAT THIS MAP DOES NOT DO. It assigns no priors, conditions no node and runs no
simulation. It is the layer that has to exist before any of that is defensible.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from dt_adoc.calibration.observation_map import (
    ACTIVATION_STATUSES,
    CALIBRATION_ROLES,
)

MODEL_VERSION = "adoc-literature-superset-v0.4.0"

#: How a state could be read off single-cell RNA, ordered from strongest to
#: weakest. `not_observable` is a positive finding, not a gap to be filled
#: later: post-translational state, subcellular localisation, extracellular
#: protein concentration and interface mechanics are not RNA-visible, and
#: recording that is what stops a proxy being substituted silently.
OBSERVABLE_VIA: frozenset[str] = frozenset(
    {
        "direct_transcript",
        "gene_program",
        "regulon_activity",
        "pathway_score",
        "proxy_abundance_not_activity",
        "not_observable",
    }
)

#: Evidence role, in the project's sense. `same_dataset_internal` is the one
#: that is easy to get wrong: a second feature of the same 28,212 cells is not
#: circular the way a constructing feature is, but it is not independent
#: validation either.
EVIDENCE_ROLES: frozenset[str] = frozenset(
    {
        "construction",
        "calibration",
        "same_dataset_internal",
        "held_out",
        "external",
        "not_applicable",
    }
)

#: Analyte-name spellings that differ from the gene symbol scRNA uses.
#:
#: Narrow and explicit rather than a general normaliser: the observation map
#: records assay names, this map records gene symbols, and exactly one differs.
#: A fuzzy matcher here would quietly widen construction status.
_ANALYTE_TO_SYMBOL: dict[str, str] = {"IGFBP-1": "IGFBP1"}

#: Construction analytes that no structured record carries, kept as a CURATED
#: snapshot because deriving them would mean parsing prose.
#:
#: `config/evidence_roles.yaml` puts four readouts in the construction role.
#: Two of them, `P1-EPI-STATE` and `P1-STR-STATE`, have mapping rows in
#: `config/observation_model_map.tsv` whose `protein` field is a structured
#: `multi_analyte_composite:` list -- those are DERIVED below and are not
#: repeated here. The other two have **no mapping row at all**, and their
#: `observed_target` in `context/phase1-readouts.tsv` reads only "active in
#: manuscript interpretation". There is nothing structured to derive from, and
#: inferring gene symbols from that prose would be exactly the fragile parser
#: worth avoiding.
#:
#: So these two are curated, from the readout identifiers and the mechanisms
#: they name: `P1-IHH-BMP` is the IHH/COUP-TFII(NR2F2)/BMP2 coupling and
#: `P1-SPP1` the SPP1 adhesion coupling. BMP2 and SPP1 are already derived from
#: the composites, so the residue is two symbols.
#:
#: Kept deliberately narrow. An earlier revision of this module also listed
#: SCGB1D2 and SCGB2A1 as construction analytes because the manuscript mentions
#: "secretoglobins" -- but they are NOT in the registered `P1-EPI-STATE`
#: composite, and construction status must not widen just because an analyte
#: appears somewhere in the same paper.
CURATED_PATHWAY_CONSTRUCTION_FEATURES: frozenset[str] = frozenset({"IHH", "NR2F2"})

#: Fingerprint of the canonical records the construction set depends on.
#:
#: The drift guard. Without it this module could keep a stale membership while
#: the canonical files moved underneath it, and every test would stay green --
#: the failure mode of any duplicated list. `construction_source_fingerprint`
#: recomputes this from the live records and
#: `tests/unit/test_scrna_observability.py` fails if it moves, which forces the
#: curated half to be re-adjudicated rather than silently inherited.
CONSTRUCTION_SOURCE_FINGERPRINT = (
    "5f29affa679c8257f2ef1278f4e743ac50d25c30c8d58e7e91c4507618c20e43"
)


def _construction_readout_ids(root: Path) -> tuple[str, ...]:
    """Readouts the project records as construction-role, from its own file."""
    import yaml

    payload = yaml.safe_load(
        (root / "config" / "evidence_roles.yaml").read_text(encoding="utf-8")
    )
    return tuple(sorted(payload["construction"]["readout_ids"]))


def _composite_analytes(root: Path, readout_ids: tuple[str, ...]) -> dict[str, str]:
    """The structured `multi_analyte_composite:` fields, per readout."""
    path = root / "config" / "observation_model_map.tsv"
    found: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["registered_readout_id"] not in readout_ids:
                continue
            protein = row["protein"]
            if protein.startswith("multi_analyte_composite:"):
                found[row["registered_readout_id"]] = protein
    return found


def _pathway_readout_targets(
    root: Path, readout_ids: tuple[str, ...]
) -> dict[str, str]:
    """The unstructured targets, recorded so the fingerprint covers them."""
    path = root / "context" / "phase1-readouts.tsv"
    found: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["readout_id"] in readout_ids:
                found[row["readout_id"]] = row["observed_target"]
    return found


def derived_construction_features(root: Path) -> frozenset[str]:
    """Construction analytes READ from the structured canonical records."""
    readout_ids = _construction_readout_ids(root)
    symbols: set[str] = set()
    for composite in _composite_analytes(root, readout_ids).values():
        for analyte in composite.split(":", 1)[1].split(";"):
            name = analyte.strip()
            if name:
                symbols.add(_ANALYTE_TO_SYMBOL.get(name, name))
    return frozenset(symbols)


def construction_features(root: Path | None = None) -> frozenset[str]:
    """Features that BUILT the model; an observation using them is construction.

    Derived where the canonical records are structured, curated where they are
    not, and the split is explicit rather than implied. See
    `CURATED_PATHWAY_CONSTRUCTION_FEATURES` for why the residue exists.
    """
    active_root = root or Path(__file__).resolve().parents[3]
    return derived_construction_features(active_root) | (
        CURATED_PATHWAY_CONSTRUCTION_FEATURES
    )


def construction_source_fingerprint(root: Path | None = None) -> str:
    """Digest of every canonical record the construction set depends on.

    Covers the construction readout id list, the structured composites those
    ids resolve to, and the unstructured `observed_target` of the readouts the
    curated residue stands in for -- so a change to ANY of them trips the guard,
    including a change to the prose that the curated half was adjudicated from.
    """
    import hashlib

    active_root = root or Path(__file__).resolve().parents[3]
    readout_ids = _construction_readout_ids(active_root)
    parts: list[str] = list(readout_ids)
    composites = _composite_analytes(active_root, readout_ids)
    parts += [f"{k}={composites[k]}" for k in sorted(composites)]
    targets = _pathway_readout_targets(active_root, readout_ids)
    parts += [f"{k}~{targets[k]}" for k in sorted(targets)]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _evidence_role(observable_via: str, features: str, root: Path | None = None) -> str:
    """Per-measurement, from whether its features constructed the model."""
    if observable_via == _NOT_OBS:
        return "not_applicable"
    used = {f.strip() for f in features.split(";") if f.strip()}
    if used & construction_features(root):
        return "construction"
    return "same_dataset_internal"


#: Whether a measured value can be applied to this node at all, and how.
#:
#: The distinction the map previously blurred. A FREE variable takes an
#: initial-state prior directly. A DERIVED node does not: its value is computed
#: from its rule, so "conditioning" it means overriding that rule -- which is a
#: model edit, and one that decouples the node from its function class rather
#: than moving the class together.
CONDITIONING_COMPATIBILITY: frozenset[str] = frozenset(
    {
        "istate_prior",
        "rule_override_required",
        "not_applicable",
    }
)


FIELDS: tuple[str, ...] = (
    "mapping_id",
    "model_node",
    "compartment",
    "biological_state",
    # --- what the MEASUREMENT can do -------------------------------------
    "measurement_observability",
    "measurement_features",
    "measurement_resolution",
    "aggregation",
    "condition_confounding",
    "evidence_role",
    # --- what the MODEL can do -------------------------------------------
    "v04_function_class",
    "v04_class_size",
    "v04_class_members",
    "v04_representational_resolution",
    "conditioning_compatibility",
    "phenotype_inert",
    "evidence_class",
    # --- disposition ------------------------------------------------------
    "calibration_role",
    "activation_status",
    "confidence",
    "source_table",
    "claim_ceiling",
)


@dataclass(frozen=True)
class Curation:
    """The scientific judgement for one node. Everything else is derived."""

    biological_state: str
    observable_via: str
    observation_features: str
    #: What the MEASUREMENT itself distinguishes -- deliberately separate from
    #: what v0.4 can represent, because conflating them blames the assay for a
    #: limitation of the rules.
    measurement_resolution: str
    aggregation: str
    calibration_role: str
    activation_status: str
    confidence: str
    claim_ceiling: str


_NOT_OBS = "not_observable"
_CELLTYPE_AGG = "donor x condition x celltype_v2"
#: For KLF12 specifically, `celltype_v2` is not an admissible stratifier for a
#: condition contrast: three of the four epithelial labels are ~80% one arm, so
#: stratifying and then contrasting is close to contrasting a variable with
#: itself. The union of the epithelial labels is a condition-independent
#: DEFINITION and is what docs/scrna/klf12_prior_preregistration.md fixed.
_EPITHELIAL_UNION_AGG = "donor x condition x pooled epithelial celltype_v2 labels"
_NONE = "not_applicable"

#: Curated per node. Absent nodes fall back to `_default_curation`, which is
#: deliberately conservative rather than absent: a node nobody has thought about
#: must not read as observable.
CURATION: dict[str, Curation] = {
    # --- AC01, the nine-member epithelial secretory class -------------------
    "E_PAEP": Curation(
        "PAEP transcriptional state in epithelium",
        "direct_transcript",
        "PAEP",
        "separately quantifiable transcript; the measurement distinguishes PAEP "
        "from SPP1, PC6 and every other member of this function class",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "moderate",
        "PAEP transcript is not PAEP secretion. The ADOC secretome table "
        "measures extracellular PAEP protein (OM-001); the two are separate "
        "observations of separate quantities. PAEP is a CONSTRUCTION analyte "
        "(P1-EPI-STATE), so this measurement built the epithelial state and can "
        "never be cited as concordance for it.",
    ),
    "E_SPP1_EXPR": Curation(
        "SPP1 transcriptional state in epithelium",
        "direct_transcript",
        "SPP1",
        "separately quantifiable transcript; the measurement distinguishes it "
        "from every other gene measured here",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "moderate",
        "Transcript only; says nothing about secreted SPP1 reaching the lumen, "
        "which is what X_SPP1_LUMEN_FREE represents. SPP1 is a CONSTRUCTION "
        "analyte (P1-EPI-STATE and P1-SPP1).",
    ),
    "E_PC6": Curation(
        "PCSK6 (PC6) transcriptional state",
        "direct_transcript",
        "PCSK6",
        "separately quantifiable transcript; the measurement distinguishes it "
        "from every other gene measured here",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "low-moderate",
        "Proprotein convertase transcript; enzymatic activity is not observed.",
    ),
    "E_HBEGF": Curation(
        "HBEGF transcriptional state",
        "direct_transcript",
        "HBEGF",
        "separately quantifiable transcript; the measurement distinguishes it "
        "from every other gene measured here",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "low-moderate",
        "Transcript only; HB-EGF is shed and acts extracellularly, which RNA "
        "does not see. Also phenotype-inert in v0.4, so an observation here "
        "cannot reach any OUT_ node through this model.",
    ),
    "E_ITGAVB3_5": Curation(
        "alpha-v beta-3/beta-5 integrin RECEPTOR state",
        "proxy_abundance_not_activity",
        "ITGAV;ITGB3;ITGB5",
        "three subunit transcripts, separately quantifiable; they do NOT "
        "distinguish an engaged receptor from an unengaged one",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "Subunit transcripts support receptor ABUNDANCE at best, and the node is "
        "a ligand-engaged receptor state. AGENTS.md forbids substituting "
        "abundance for activity. A staged literature row proposing the same "
        "substitution for a different integrin was rejected on this ground; "
        "that record is deliberately not cited by id here, because a "
        "quarantined id must not appear in a canonical artifact even in support "
        "of its own rejection.",
    ),
    "E_MUC1_SLEX": Curation(
        "sialyl-Lewis-X decorated MUC1 on the apical surface",
        "gene_program",
        "FUT3;FUT4;FUT6;FUT7;ST3GAL3;ST3GAL4;ST3GAL6;B3GNT2;ST6GALNAC1;MUC1",
        "a biosynthetic-capacity score; it does NOT distinguish a cell that "
        "carries surface sLeX from one that merely could make it",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "A glycosyltransferase program is BIOSYNTHETIC COMPETENCE, never a "
        "measured cell-surface glycan. Surface sLeX requires lectin or antibody "
        "staining this dataset does not contain. Must never be reported as sLeX "
        "measured.",
    ),
    "E_DAG1_CLEAVED": Curation(
        "cleaved (beta-)dystroglycan state",
        _NOT_OBS,
        "",
        "no scRNA feature separates cleaved from intact DAG1: the transcript is "
        "the same for both",
        _NONE,
        "gap",
        "rejected",
        _NONE,
        "Proteolytic cleavage state. Not RNA-observable, and the limitation is "
        "the ASSAY's here -- unlike the aliasing rows, no change to the model "
        "would make this measurable.",
    ),
    "E_ANXA2_ACTIN": Curation(
        "annexin-A2 / cortical actin complex at the apical membrane",
        _NOT_OBS,
        "",
        "protein-complex assembly and localisation; no transcript resolves it",
        _NONE,
        "gap",
        "rejected",
        _NONE,
        "A protein-complex and localisation state. Not RNA-observable.",
    ),
    "E_SECRETORY_STATE": Curation(
        "epithelial secretory differentiation program",
        "gene_program",
        "PAEP;SPP1;CEACAM5;CEACAM6;DPP4;SCGB1D2;SCGB2A1",
        "a multi-gene program score; resolves the program as a whole, and its "
        "components remain separately quantifiable if the program is decomposed",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "moderate",
        "This IS the P1-EPI-STATE construction composite, so it is CONSTRUCTION "
        "evidence and cannot be concordance for the epithelial state it built. "
        "CONFOUND: these markers are close to the features defining the HT "
        "epithelium I/II labels, which are 79-80% HT cells, so an HT-vs-CNT "
        "contrast on this program is close to a contrast on the labels.",
    ),
    # --- AC02, the six-member stromal decidual class ------------------------
    "S_PRL": Curation(
        "PRL transcriptional state in stroma",
        "direct_transcript",
        "PRL",
        "separately quantifiable from IGFBP1 and from every other class member; "
        "the measurement CAN distinguish them",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "moderate",
        "Transcript, not secreted prolactin; the ADOC secretome PRL readout "
        "measures protein and is a separate observation. PRL is a CONSTRUCTION "
        "analyte (P1-STR-STATE, SOFIA-SC-002). NOTE the asymmetry that matters: "
        "PRL and IGFBP1 are separately measurable, and v0.4 makes them the same "
        "Boolean function. If they diverge in the data that is a FALSIFICATION "
        "of the aliasing, not a limit on the assay.",
    ),
    "S_IGFBP1": Curation(
        "IGFBP1 transcriptional state in stroma",
        "direct_transcript",
        "IGFBP1",
        "separately quantifiable from PRL; the measurement CAN distinguish them",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "moderate",
        "As S_PRL: transcript only, CONSTRUCTION analyte (P1-STR-STATE). The "
        "model cannot separate it from S_PRL; the data can.",
    ),
    "S_SPP1": Curation(
        "SPP1 transcriptional state in stroma",
        "direct_transcript",
        "SPP1",
        "separately quantifiable transcript; the measurement distinguishes it "
        "from every other gene measured here",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "low-moderate",
        "Transcript only; compartment assignment depends on the celltype_v2 "
        "stroma labels, which are condition-confounded. Also phenotype-inert in "
        "v0.4.",
    ),
    "S_TAZ_ECM": Curation(
        "TAZ/WWTR1-dependent stromal ECM remodelling state",
        "proxy_abundance_not_activity",
        "WWTR1;CTGF;CYR61;FN1;COL4A1",
        "transcripts and a target-gene readout; neither resolves TAZ nuclear "
        "localisation, which is the mechanistically relevant state",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "WWTR1 transcript is not TAZ nuclear localisation. Target-gene readout "
        "(CTGF/CYR61) is a better proxy but is regulated by other inputs too.",
    ),
    "S_DECIDUALIZED": Curation(
        "stromal decidualization program",
        "gene_program",
        "PRL;IGFBP1;FOXO1;WNT4;LEFTY2",
        "a multi-gene program score whose components are separately quantifiable",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "moderate",
        "Overlaps the P1-STR-STATE construction composite (PRL, IGFBP1), so "
        "CONSTRUCTION. Same confound as E_SECRETORY_STATE: HT stroma is 81.6% "
        "HT cells.",
    ),
    "OUT_STROMAL_DECIDUALIZED": Curation(
        "declared stromal decidualization OUTPUT",
        _NOT_OBS,
        "",
        "a declared model output; nothing measures it directly",
        _NONE,
        "gap",
        "rejected",
        _NONE,
        "A declared model output, not a measurable cell state. Under v0.4 it is "
        "also Boolean-identical to five other class members, so as the model "
        "stands it adds no representational content beyond a single marker.",
    ),
    # --- AC03, the five-member progesterone class ---------------------------
    "E_PGR": Curation(
        "progesterone-receptor ACTIVITY in epithelium",
        "regulon_activity",
        "PGR;GREB1;HOXA10;HOXA11;IHH",
        "a response-gene program, resolved per cell type, so the epithelial and "
        "stromal responses ARE separately measurable",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "PGR TRANSCRIPT IS NOT RECEPTOR ACTIVITY, and in endometrium epithelial "
        "PGR falls exactly when progesterone signalling is highest, so the "
        "transcript can move opposite to the state. Uses IHH, a CONSTRUCTION "
        "analyte (P1-IHH-BMP).",
    ),
    "S_PGR": Curation(
        "progesterone-receptor ACTIVITY in stroma",
        "regulon_activity",
        "PGR;GREB1;HAND2",
        "a response-gene program in a different compartment from E_PGR; the "
        "measurement resolves epithelial and stromal responses separately",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "As E_PGR. v0.4 makes this Boolean-identical to E_PGR, so THE MODEL "
        "cannot separate epithelial from stromal progesterone response. The "
        "measurement can -- these are different cells. An earlier revision "
        "called this 'an identifiability limit, not a measurement limit' and "
        "then described it as scRNA being unable to separate them; only the "
        "first half was right.",
    ),
    "E_IHH": Curation(
        "IHH transcriptional state in epithelium",
        "direct_transcript",
        "IHH",
        "separately quantifiable transcript; the measurement distinguishes it "
        "from every other gene measured here",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "low-moderate",
        "Transcript only, CONSTRUCTION analyte (P1-IHH-BMP), and phenotype-inert "
        "in v0.4: clamping it changes no OUT_ node, so an observation cannot "
        "reach any prediction through it.",
    ),
    "S_NR2F2": Curation(
        "NR2F2 (COUP-TFII) regulatory activity in stroma",
        "regulon_activity",
        "NR2F2",
        "transcript only; no validated NR2F2 target program is registered here, "
        "so regulatory activity is NOT resolved by this measurement",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "TF TRANSCRIPT IS NOT TF ACTIVITY. CONSTRUCTION analyte (P1-IHH-BMP). "
        "Also phenotype-inert in v0.4.",
    ),
    "S_BMP2": Curation(
        "BMP2 ligand expression in stroma",
        "direct_transcript",
        "BMP2",
        "separately quantifiable transcript; the measurement distinguishes it "
        "from every other gene measured here",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "low-moderate",
        "LIGAND EXPRESSION IS NOT SIGNALLING. BMP2 transcript must not set a "
        "BMP-SMAD signalling state ON; that needs a SMAD1/5/8 target program. "
        "CONSTRUCTION analyte (P1-STR-STATE and P1-IHH-BMP).",
    ),
    # --- AC04 / AC05 --------------------------------------------------------
    "E_LIF": Curation(
        "LIF ligand expression in epithelium",
        "direct_transcript",
        "LIF",
        "separately quantifiable, but lowly expressed and dropout-prone, so a "
        "zero is weak evidence of absence",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "low-moderate",
        "Ligand transcript, not signalling.",
    ),
    "E_GP130_STAT3": Curation(
        "GP130/STAT3 pathway ACTIVITY in epithelium",
        "regulon_activity",
        "SOCS3;BCL3;STAT3",
        "a downstream target program; it does NOT resolve which upstream ligand "
        "activated STAT3",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "STAT3 TRANSCRIPT IS A POOR PROXY FOR PHOSPHO-STAT3; only a downstream "
        "target program is defensible. Note this node is NOT phenotype-inert "
        "while E_CD98_CD9, in the same function class, is -- the clearest "
        "in-repo demonstration that identical Boolean function does not mean "
        "identical interventional consequence.",
    ),
    "E_CD98_CD9": Curation(
        "CD98/CD9 tetraspanin-complex surface state",
        "proxy_abundance_not_activity",
        "SLC3A2;CD9",
        "two subunit transcripts; complex formation and surface presentation "
        "are not resolved",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "Transcript abundance of two subunits. Phenotype-inert in v0.4, unlike "
        "E_GP130_STAT3 in the same function class.",
    ),
    "E_PODXL": Curation(
        "podocalyxin anti-adhesive apical coat",
        "proxy_abundance_not_activity",
        "PODXL",
        "transcript only; the node's meaning is spatial (APICAL) and scRNA has "
        "no spatial axis",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "PODXL transcript does not establish an apical anti-adhesive coat.",
    ),
    "E_DAG1_FULL": Curation(
        "intact dystroglycan state",
        "proxy_abundance_not_activity",
        "DAG1",
        "DAG1 transcript cannot distinguish intact from cleaved, so it does not "
        "separate this node from E_DAG1_CLEAVED -- an ASSAY limit, not a rule "
        "limit",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "One of the few rows where the measurement genuinely cannot resolve two "
        "model states. Recorded as such rather than as aliasing.",
    ),
    "E_MUC1_BARRIER": Curation(
        "MUC1 apical anti-adhesive barrier",
        "proxy_abundance_not_activity",
        "MUC1",
        "transcript only; barrier function depends on apical presentation and "
        "glycosylation, neither resolved",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "MUC1 transcript is not an apical barrier.",
    ),
    # --- AC07 ---------------------------------------------------------------
    "E_RECEPTIVE_SURFACE": Curation(
        "composite receptive apical surface state",
        _NOT_OBS,
        "",
        "a model-defined composite; nothing measures it directly",
        _NONE,
        "gap",
        "rejected",
        _NONE,
        "Defined by the model rather than measured.",
    ),
    "OUT_EPITHELIAL_RECEPTIVE": Curation(
        "declared epithelial receptivity OUTPUT",
        _NOT_OBS,
        "",
        "a declared model output; nothing measures it directly",
        _NONE,
        "gap",
        "rejected",
        _NONE,
        "A declared model output. Under v0.4 it adds no representational "
        "content beyond E_RECEPTIVE_SURFACE.",
    ),
    # --- unaliased nodes worth observing ------------------------------------
    "E_KLF12_HIGH": Curation(
        "high KLF12 state in epithelium",
        "direct_transcript",
        "KLF12",
        "detected, but at the floor: 83.2% of epithelial cells carry none and "
        "84.2% of those that do carry under two transcript-equivalents, so the "
        "measurement separates expressing from not-expressing and not high "
        "from low",
        _EPITHELIAL_UNION_AGG,
        "diagnostic",
        "provisional",
        "low-moderate",
        "THE HIGHEST-VALUE ROW IN THIS MAP, for a structural reason, and the "
        "one row that has since been taken to its conclusion. E_KLF12_HIGH is "
        "one of only five hand-set FREE variables in v0.4 and the only one "
        "scRNA can observe -- the other four are interface relays with no "
        "cellular correlate. Being free, it takes an initial-state prior "
        "DIRECTLY, with no rule override. The pre-registered attempt to supply "
        "that prior is docs/scrna/klf12_prior_preregistration.md and its result "
        "is docs/scrna/klf12_prior_finding.md: these data do not establish a "
        "measured prior for E_KLF12_HIGH -- a limit of what the measurement "
        "identifies, NOT a finding that no KLF12-high state exists. A "
        "two-component mixture on the 3,429 detected cells fits, but whether "
        "it passes M1(a) depends on which reading of the frozen sentence is "
        "applied: the implemented rule (exactly one posterior crossing inside "
        "the fitted support, between the means) says no, while the two "
        "readings closer to the pre-registered wording propose boundaries of "
        "1.06 and 1.17 transcript-equivalents and say yes. That rule is "
        "POST-HOC and is labelled as such. F3 is loose in the same way and "
        "pulls the other way, so the pre-registered decision branch is NOT "
        "uniquely determined: crossing the two ambiguities reaches GO, "
        "CONDITIONAL_GO and NO_GO alike, and the artifact commits the whole "
        "grid. Nothing was activated under any cell. What rules a measured "
        "prior out under every cell is specificity, not wording: all three "
        "M1(a) readings, and M1(b), also pass on a population simulated with "
        "no latent state at all, 25 of 25 replicates. That calibration covers "
        "M1(a) and M1(b) only; M1(c) and the falsifiers need per-unit "
        "structure the null does not model. The multimodality the detected "
        "values do have is the integer UMI lattice (modes at 0.97, 1.91, "
        "2.79, 3.77, 4.72, 5.92, 6.88 transcript-equivalents). The "
        "pre-registered raw-UMI sensitivity was run "
        "(docs/scrna/klf12_raw_umi_findings.json) and agrees: on integer "
        "counts 65.5% of detected cells carry exactly one UMI and the median "
        "detected value is one molecule in every one of the six units. No "
        "latent-state model is fitted on the raw layer: an earlier revision "
        "compared a two-component gamma-Poisson mixture against a single-rate "
        "model by BIC, and that analysis was REMOVED because the likelihood is "
        "multimodal, three successive fitters each returned a demonstrable "
        "non-maximum, and the reported gain moved +17.0 to +10.24 to +21.52 as "
        "the search was hardened; it was never load-bearing. Model-free, "
        "thinning to the lowest unit median (14,503 UMIs) and recounting on "
        "the cells that were actually matched -- the scheme the artifact "
        "records as depth_matched_scheme_for_per_unit = matched_cells_only, "
        "because thinning cannot raise a cell already below the target -- cuts "
        "the between-unit spread in KLF12 detection from 0.330 to 0.229 and "
        "reverses the HT-versus-CNT sign within donor SZ25 (+0.102 crude, "
        "-0.118 depth-matched), the same reversal seen by standardisation on "
        "the corrected layer. That scheme is not free and its cost is uneven "
        "in the direction opposite to the intuition: the unmatched (dropped) "
        "share is 4.1% for SZ25TE_HT, which keeps 1,346 of its 1,404 cells, "
        "against 36.3-50.0% for the other five, so the deep unit retains "
        "almost everything and the shallow units pay. Three "
        "POST-HOC findings sit beside that pre-registered one: the pooled 75th "
        "and 80th percentile thresholds are exactly zero and so collapse onto "
        "bare detection; the HT-versus-CNT difference changes sign depending on "
        "whether sequencing depth or epithelial subtype is adjusted for, with "
        "both adjustments putting 20-43% of their weight on strata of 3-38 "
        "cells; and subtype adjustment partly removes the condition itself, "
        "because three of the four epithelial labels are ~80% one arm. "
        "Conditioning was executed anyway, as a declared arbitrary-threshold "
        "sensitivity sweep, and its only finding is structural: at the "
        "converged horizon every tracked quantity is the two-extreme mixture "
        "(1-p)*value(0) + p*value(1) to within 6.0e-4 -- NOT the special case "
        "'unconditioned value scaled by 1 - prior', which is false for "
        "E_KLF12_HIGH itself, for E_ITGAVB3_5 and for OUT_STROMAL_DECIDUALIZED. "
        "So this row stays provisional "
        "and the external asset stays not-integrated. What would lift it is a "
        "reference population for 'high' or a KLF12 assay with dynamic range, "
        "not more analysis of these 28,212 cells.",
    ),
    "S_HAND2": Curation(
        "HAND2 expression state in stroma",
        "direct_transcript",
        "HAND2",
        "separately quantifiable transcript; the measurement distinguishes it "
        "from every other gene measured here",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "low-moderate",
        "Transcript, and HAND2 is a TF, so expression is not regulatory "
        "activity. Relevant because IN_HAND2_LOSS is a declared perturbation "
        "arm: a measured baseline would bound what that arm represents.",
    ),
    "E_ESTROGENIC_PROLIFERATION": Curation(
        "estrogen-driven epithelial proliferation state",
        "gene_program",
        "MKI67;TOP2A;GREB1",
        "a proliferation program, among the better-resolved states here",
        _CELLTYPE_AGG,
        "diagnostic",
        "reported_only",
        "moderate",
        "CONFOUND: the Cycling epithelium label is itself defined by these "
        "genes, so contrasting that label against others is close to "
        "tautological.",
    ),
    "S_FGF_MITOGENIC": Curation(
        "FGF-driven stromal mitogenic state",
        "pathway_score",
        "FGF2;FGF7;FGF9;SPRY2;DUSP6",
        "ligand transcripts plus a negative-feedback target readout; receptor "
        "engagement is not resolved",
        _CELLTYPE_AGG,
        "context_only",
        "reported_only",
        "low",
        "Neither component establishes receptor engagement.",
    ),
}


def _default_curation(node_id: str) -> Curation:
    """Conservative fallback. Never reports a node as observable."""
    if node_id.startswith("IN_"):
        state = "declared protocol input"
        resolution = "an experimental setting, not a cell state"
        ceiling = (
            "A protocol input is an experimental setting, not a cell state. "
            "scRNA cannot observe it and must not be used to infer it."
        )
    elif node_id.startswith("X_"):
        state = "interface / mechanical relay state"
        resolution = "no single-cell transcriptional correlate exists"
        ceiling = (
            "Interface and mechanical states have no single-cell "
            "transcriptional correlate in this dataset. Protein, imaging or "
            "functional assays are required; RNA is not a substitute. This is "
            "an ASSAY limit: no change to the model would make it measurable."
        )
    elif node_id.startswith("OUT_"):
        state = "declared model output"
        resolution = "a declared model output; nothing measures it directly"
        ceiling = "A declared output of the model, not a measured quantity."
    else:
        state = "uncurated"
        resolution = "no observability judgement recorded"
        ceiling = (
            "No observability judgement has been made for this node. Treat as "
            "unobservable until one is recorded; silence is not permission."
        )
    return Curation(
        state,
        _NOT_OBS,
        "",
        resolution,
        _NONE,
        "gap",
        "rejected",
        _NONE,
        ceiling,
    )


def _alias_index(facts) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Stable alias-class ids, ordered largest first then alphabetically."""
    index: dict[str, tuple[str, tuple[str, ...]]] = {}
    ordered = sorted(facts.alias_classes, key=lambda c: (-len(c), min(c)))
    for position, members in enumerate(ordered, start=1):
        class_id = f"AC{position:02d}"
        sorted_members = tuple(sorted(members))
        for member in sorted_members:
            index[member] = (class_id, sorted_members)
    return index


def _representational_resolution(node_id: str, entry) -> str:
    """What v0.4 can REPRESENT here -- never a claim about the measurement.

    The wording matters and an earlier revision got it backwards. Saying an
    observation "resolves the CLASS, not this node" blames the assay for the
    rules. Co-variation under the model's own dynamics is a property of the
    rules, it is falsifiable by separate measurements, and it does NOT mean the
    nodes are interchangeable under intervention -- clamping one overrides only
    its own rule.
    """
    if entry is None:
        return (
            "distinct: v0.4 gives this node a Boolean function no other node "
            "realises, so the model can represent it independently"
        )
    class_id, members = entry
    others = [m for m in members if m != node_id]
    return (
        f"class {class_id}, {len(members)} members: under UNMODIFIED v0.4 rules "
        f"this node co-varies exactly with {';'.join(others)}. The model cannot "
        "represent a difference between them. Separate measurements remain "
        "biologically distinct and a measured divergence would FALSIFY this "
        "aliasing rather than be limited by it."
    )


def _conditioning_compatibility(
    node_id: str, evidence_class: str, observable: bool
) -> str:
    """How, mechanically, a measured value could be applied to this node."""
    if not observable:
        return "not_applicable"
    if evidence_class in {"hand_set_free", "protocol_input"}:
        return "istate_prior"
    return "rule_override_required"


def build_rows(root: Path | None = None) -> list[dict[str, str]]:
    from dt_adoc.concordance.mechanism import node_records
    from dt_adoc.reporting.structure import load_structure

    facts = load_structure(MODEL_VERSION, root)
    records = node_records(facts, model_version=MODEL_VERSION, root=root)
    aliases = _alias_index(facts)
    inert = set(facts.phenotype_inert)

    rows: list[dict[str, str]] = []
    for position, node_id in enumerate(sorted(facts.node_ids), start=1):
        entry = aliases.get(node_id)
        curation = CURATION.get(node_id) or _default_curation(node_id)
        record = records[node_id]
        observable = curation.observable_via != _NOT_OBS
        rows.append(
            {
                "mapping_id": f"SC-{position:03d}",
                "model_node": node_id,
                "compartment": facts.compartment_of.get(node_id, "unknown"),
                "biological_state": curation.biological_state,
                "measurement_observability": curation.observable_via,
                "measurement_features": curation.observation_features,
                "measurement_resolution": curation.measurement_resolution,
                "aggregation": curation.aggregation,
                "condition_confounding": CONDITION_CONFOUNDING,
                "evidence_role": _evidence_role(
                    curation.observable_via, curation.observation_features, root
                ),
                "v04_function_class": entry[0] if entry else "",
                "v04_class_size": str(len(entry[1]) if entry else 1),
                "v04_class_members": ";".join(entry[1]) if entry else node_id,
                "v04_representational_resolution": _representational_resolution(
                    node_id, entry
                ),
                "conditioning_compatibility": _conditioning_compatibility(
                    node_id, record.evidence_class, observable
                ),
                "phenotype_inert": "true" if node_id in inert else "false",
                "evidence_class": record.evidence_class,
                "calibration_role": curation.calibration_role,
                "activation_status": curation.activation_status,
                "confidence": curation.confidence,
                "source_table": SOURCE_TABLE,
                "claim_ceiling": curation.claim_ceiling,
            }
        )
    return rows


#: The deposited object, pinned by the checksum recomputed from a local copy.
SOURCE_TABLE = (
    "ArrayExpress E-MTAB-15842 seurat_object.rds "
    "(28212 cells; sha256 "
    "504a674db978779b03d02a73224ee425ec46efbf411c148b0903ceef15389a1a)"
)

#: Carried on every row because it applies to every row, and because it is the
#: single fact most likely to be forgotten when a contrast is designed.
CONDITION_CONFOUNDING = (
    "celltype_v2 labels are near-deterministic in condition: Luminal-like "
    "epithelium 0.8% HT, Stroma 0.8% HT, versus HT epithelium I 79.1%, HT "
    "epithelium II 79.9%, HT stroma 81.6% (Cycling epithelium 14.0%, "
    "Myofibroblast 22.7%). Stratifying by celltype_v2 and then contrasting HT "
    "against CNT is close to contrasting a variable with itself."
)


def write_map(root: Path | None = None, destination: Path | None = None) -> Path:
    active_root = root or Path(__file__).resolve().parents[3]
    target = destination or active_root / "config" / "scrna_observation_map.tsv"
    rows = build_rows(active_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(FIELDS), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    return target


class ScrnaObservationMapError(ValueError):
    """Raised when the committed map disagrees with the executable model."""


def load_scrna_observation_map(root: Path | None = None) -> list[dict[str, str]]:
    """Load the map and re-derive every derived column against the model.

    The curated columns are read as written. The derived ones -- function class,
    size, membership, representational resolution, inertness, evidence class,
    evidence role and conditioning compatibility -- are recomputed here, so a
    model change that silently invalidates a claim fails loudly instead of
    leaving a stale statement in a scientific artifact.
    """
    active_root = root or Path(__file__).resolve().parents[3]
    path = active_root / "config" / "scrna_observation_map.tsv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ScrnaObservationMapError(
                f"column set drifted: {reader.fieldnames!r} != {FIELDS!r}"
            )
        rows = list(reader)

    # Trip before anything else if the canonical records moved: a stale
    # construction membership would otherwise validate cleanly against itself.
    actual = construction_source_fingerprint(active_root)
    if actual != CONSTRUCTION_SOURCE_FINGERPRINT:
        raise ScrnaObservationMapError(
            "the canonical construction records changed "
            f"(fingerprint {actual} != pinned {CONSTRUCTION_SOURCE_FINGERPRINT}). "
            "Re-adjudicate CURATED_PATHWAY_CONSTRUCTION_FEATURES against the new "
            "records and update the pin; do not update the pin alone."
        )
    built = construction_features(active_root)
    derived = {row["model_node"]: row for row in build_rows(active_root)}
    if set(derived) != {row["model_node"] for row in rows}:
        raise ScrnaObservationMapError(
            "the committed map does not cover exactly the model's nodes; "
            "regenerate it with dt_adoc.scrna.observability.write_map"
        )
    for row in rows:
        node_id = row["model_node"]
        expected = derived[node_id]
        for field in (
            "v04_function_class",
            "v04_class_size",
            "v04_class_members",
            "v04_representational_resolution",
            "conditioning_compatibility",
            "phenotype_inert",
            "evidence_class",
            "evidence_role",
            "compartment",
        ):
            if row[field] != expected[field]:
                raise ScrnaObservationMapError(
                    f"{node_id}: derived field {field!r} is stale "
                    f"({row[field]!r} != {expected[field]!r})"
                )
        if row["measurement_observability"] not in OBSERVABLE_VIA:
            raise ScrnaObservationMapError(
                f"{node_id}: invalid measurement_observability "
                f"{row['measurement_observability']!r}"
            )
        if row["evidence_role"] not in EVIDENCE_ROLES:
            raise ScrnaObservationMapError(
                f"{node_id}: invalid evidence_role {row['evidence_role']!r}"
            )
        if row["conditioning_compatibility"] not in CONDITIONING_COMPATIBILITY:
            raise ScrnaObservationMapError(
                f"{node_id}: invalid conditioning_compatibility "
                f"{row['conditioning_compatibility']!r}"
            )
        if row["calibration_role"] not in CALIBRATION_ROLES:
            raise ScrnaObservationMapError(
                f"{node_id}: invalid calibration_role {row['calibration_role']!r}"
            )
        if row["activation_status"] not in ACTIVATION_STATUSES:
            raise ScrnaObservationMapError(
                f"{node_id}: invalid activation_status {row['activation_status']!r}"
            )
        observable = row["measurement_observability"] != "not_observable"
        if not observable and row["measurement_features"]:
            raise ScrnaObservationMapError(
                f"{node_id}: not_observable rows must name no features"
            )
        if observable and not row["claim_ceiling"]:
            raise ScrnaObservationMapError(
                f"{node_id}: an observable row must carry a claim_ceiling"
            )
        if not row["measurement_resolution"]:
            raise ScrnaObservationMapError(
                f"{node_id}: every row must state what the measurement resolves"
            )
        # The invariant the review existed to enforce: a measurement whose
        # features built the model can never be same-dataset concordance.
        used = {f.strip() for f in row["measurement_features"].split(";") if f.strip()}
        if used & built and row["evidence_role"] != "construction":
            raise ScrnaObservationMapError(
                f"{node_id}: uses construction features "
                f"{sorted(used & built)} but claims evidence_role "
                f"{row['evidence_role']!r}"
            )
    return rows


# --------------------------------------------------------------------------
# U6: the three semantic axes for all fifty-nine nodes
# --------------------------------------------------------------------------
#
# A VIEW, NOT A FOURTH TABLE. The axes are already derived, for the 27
# RNA-assessable nodes, by `node_support.interpretability_rows` from the map
# above, and frozen at the evidence root as `node_rna_interpretability.tsv`.
# This extends that derivation to every node by calling it -- never by
# re-deriving it -- and adds the rows the frozen table has no reason to carry:
# the 32 nodes RNA can never assess, as `not_RNA_assessable` rather than absent.
#
# The map itself is not touched: it is pinned at the evidence root and
# `write_map` must keep reproducing it byte for byte, so the new columns live in
# their own generated file.
#
# Only MEASUREMENT semantics are carried. Function class and phenotype
# inertness are properties of a model version (U5b changed inertness in v0.5.1),
# and a table keyed to no version must not carry them.

SEMANTICS = Path("docs/u6_semantics/node_semantics.tsv")

SEMANTICS_FIELDS: tuple[str, ...] = (
    "model_node",
    "compartment",
    "measurement_observability",
    "measurement_type",
    "presence_can_establish",
    "convincing_absence_can_establish",
    "not_blind",
    "requirement_structure",
    "axes_source",
)

_FROZEN_AXES_SOURCE = (
    "node_support.interpretability_rows (frozen as "
    "docs/scrna/node_rna_interpretability.tsv at 91f79ed)"
)
_NOT_ASSESSABLE_SOURCE = "scrna_observation_map measurement_observability"


def semantics_rows(root: Path | None = None) -> list[dict[str, str]]:
    """The three axes for every node in the committed map, sorted by model_node."""
    from dt_adoc.scrna import node_support_contract as C
    from dt_adoc.scrna.components import requirement_structure
    from dt_adoc.scrna.node_support import interpretability_rows

    active_root = root or Path(__file__).resolve().parents[3]
    map_path = active_root / "config" / "scrna_observation_map.tsv"
    if map_path != C.MAP:
        # `interpretability_rows` reads the contract's MAP, so a view built over
        # any other root would silently describe this repository instead.
        raise ScrnaObservationMapError(
            f"semantics are derived from {C.MAP}, not {map_path}"
        )
    axes = {row["model_node"]: row for row in interpretability_rows()}
    rows: list[dict[str, str]] = []
    for row in sorted(C.observation_rows(map_path), key=lambda r: r["model_node"]):
        node = row["model_node"]
        assessable = row["measurement_observability"] != C.NOT_ASSESSABLE
        if assessable != (node in axes):
            raise ScrnaObservationMapError(
                f"{node}: assessability disagrees with the frozen axes"
            )
        if assessable:
            presence = axes[node]["presence_can_establish"]
            absence = axes[node]["convincing_absence_can_establish"]
            source = _FROZEN_AXES_SOURCE
        else:
            presence = absence = "not_applicable"
            source = _NOT_ASSESSABLE_SOURCE
        rows.append(
            {
                "model_node": node,
                "compartment": row["compartment"],
                "measurement_observability": row["measurement_observability"],
                "measurement_type": C.measurement_type(row),
                "presence_can_establish": presence,
                "convincing_absence_can_establish": absence,
                "not_blind": str(node in C.NOT_BLIND_NODES).lower(),
                "requirement_structure": requirement_structure(node, assessable),
                "axes_source": source,
            }
        )
    return rows


def render_semantics(root: Path | None = None) -> str:
    import io

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=list(SEMANTICS_FIELDS), delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(semantics_rows(root))
    return buffer.getvalue()


def write_semantics(root: Path | None = None) -> tuple[Path, Path]:
    """Regenerate both U6 artifacts: node semantics and the component map."""
    from dt_adoc.scrna.components import COMPONENT_MAP, render_component_map

    active_root = root or Path(__file__).resolve().parents[3]
    written = []
    for relative, text in (
        (SEMANTICS, render_semantics(active_root)),
        (COMPONENT_MAP, render_component_map(active_root)),
    ):
        target = active_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="")
        written.append(target)
    return written[0], written[1]


def main(argv: list[str] | None = None) -> int:
    """No arguments: regenerate the observation map, as this always has.

    `--u6-semantics`: regenerate the U6 artifacts instead. Anything else exits
    non-zero -- a mistyped flag must not fall through to rewriting the map.
    `allow_abbrev=False` because a prefix such as `--u6-semantic` would
    otherwise be accepted as the flag.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m dt_adoc.scrna.observability",
        description=(
            "Regenerate config/scrna_observation_map.tsv, or with --u6-semantics "
            "the two docs/u6_semantics/ artifacts."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "--u6-semantics",
        action="store_true",
        help="write node_semantics.tsv and component_map.tsv instead of the map",
    )
    args = parser.parse_args(argv)
    if args.u6_semantics:
        for target in write_semantics():
            print(f"wrote {target}")
        return 0
    target = write_map()
    rows = load_scrna_observation_map()
    print(f"wrote {target} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
