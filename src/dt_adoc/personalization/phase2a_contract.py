"""Phase 2A: the donor-contextualization input contract.

WHAT THIS IS. A frozen, machine-readable bridge from the final ADOC single-cell
object (E-MTAB-15842, `EXT-SCRNA-001`) to the adopted
`adoc-literature-superset-v0.5.1`. A later unit can use it to write
donor-specific INITIAL-STATE probabilities. This one writes none: no `.bnd`, no
`.cfg`, no rate modifier, no clamp, no mutation interface, and no numerical
probability while the reference gate is blocked.

TWO STEPS, deliberately separate.

    --rds <object> --rscript <R>   read the object's meta.data ONLY (no
                                   expression layer), aggregate inside R, and
                                   write `scrna_metadata_extraction.json`
    (no arguments)                 build every other artifact from committed
                                   files alone -- no R, no 2.9 GB object

Only per-group cell counts leave R. No barcode or other row-level metadata is
written anywhere.

WHAT IT REUSES RATHER THAN RE-DERIVES. The compartment partition, donors,
conditions, feature lists and absent features are the frozen node-support
contract's (`dt_adoc.scrna.node_support_contract`, `node_support_findings.json`).
The mapping layer each node admits is the observation map's
`conditioning_compatibility`. The per-unit statistics are the committed
`node_support_evidence.tsv` rows, copied and never recomputed.

WHAT IT MUST NOT SEE. No model output, occupancy, adhesion count, concordance
value or other outcome may reach an eligibility, reference or transform choice.
The import boundary is asserted by `tests/unit/test_phase2a_contract.py`.

OWNER DECISIONS OF 2026-09-24, applied here and not re-derived:
Q1 only free variables (`logic = <self>`, `istate_prior`) are eligible for an
initial probability; a derived node's istate is overwritten by its rule. Q2
`E_KLF12_HIGH` is eligible pending an external reference, and the closed prior
finding is not reopened. Q3 `config/personalization.yaml` is left as it is, and
this contract permits the initial-probability layer only. Q4 the CNT arm's
composition is unrecorded, so its condition class is unresolved rather than
assumed. B1 (on review) the mapping is the pre-registered three-step bridge of
`docs/scrna/klf12_prior_preregistration.md`: an EXTERNAL per-cell high-state
definition, the fraction of a unit's cells in that state, and that fraction as
the initial probability. No rank transform.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.scrna import node_support_contract as C
from dt_adoc.scrna import verify_rds

REPO = Path(__file__).resolve().parents[3]
TASK = "build-phase2a-contract"
ADOPTED_VERSION = "adoc-literature-superset-v0.5.1"
ASSET_ID = verify_rds.ASSET_ID
SCHEMA_VERSION = 1

MODEL_DIR = Path("models/superset") / ADOPTED_VERSION
NETWORK = MODEL_DIR / "network.bnd"
NODE_DICTIONARY = MODEL_DIR / "node_dictionary.tsv"
BASELINE_CFG = MODEL_DIR / "baseline.cfg"
OBSERVATION_MAP = Path("config/scrna_observation_map.tsv")
EXTERNAL_MANIFEST = Path("config/external_data_manifest.tsv")
DATA_MANIFEST = Path("config/data_manifest.tsv")
PERSONALIZATION = Path("config/personalization.yaml")
NODE_SUPPORT_FINDINGS = Path("docs/scrna/node_support_findings.json")
NODE_SUPPORT_EVIDENCE = Path("docs/scrna/node_support_evidence.tsv")
NODE_SUPPORT_QC = Path("docs/scrna/node_support_qc.tsv")
PHASE1B_SUMMARY = Path("docs/phase1b_closure/phase1b_closure_summary.json")

OUT_DIR = Path("docs/phase2a")
EXTRACTION = OUT_DIR / "scrna_metadata_extraction.json"
OUT_GRAIN = OUT_DIR / "data_grain_audit.tsv"
OUT_MAP = OUT_DIR / "node_personalization_map.tsv"
OUT_SUMMARIES = OUT_DIR / "donor_unit_summaries.tsv"
OUT_REQUIREMENTS = OUT_DIR / "reference_requirements.tsv"
OUT_GATE = OUT_DIR / "reference_gate.json"
OUT_SPEC = OUT_DIR / "mapping_specification.json"
OUT_PROVENANCE = OUT_DIR / "provenance_contract.tsv"
OUT_STATUS = OUT_DIR / "phase2a_status.json"
OUTPUTS = (
    OUT_GRAIN,
    OUT_MAP,
    OUT_SUMMARIES,
    OUT_REQUIREMENTS,
    OUT_GATE,
    OUT_SPEC,
    OUT_PROVENANCE,
    OUT_STATUS,
)

#: The one layer this contract permits. `personalization.yaml` still lists
#: `clamp` and `rate_modifier`; nothing downstream can execute either, and the
#: owner chose (Q3) to forbid them here rather than edit that file.
PERMITTED_LAYER = "initial_probability"
FORBIDDEN_LAYERS = ("clamp", "rate_modifier", "mutation", "topology")

#: The layer every ADOC per-cell value comes from, as the node-support findings
#: record it. A reference definition must be stated on this layer (RR04).
ADOC_LAYER = "deposited counts layer (decontX-corrected, non-integer)"

# -- eligibility vocabulary -------------------------------------------------

ELIGIBLE = "eligible_initial_probability"
CONTEXT_ONLY = "context_only"
NOT_ASSESSABLE = "not_RNA_assessable"
BLOCKED_REFERENCE = "blocked_missing_reference"
BLOCKED_AMBIGUOUS = "blocked_ambiguous_mapping"
BLOCKED_COMPARTMENT = "blocked_wrong_compartment"
BLOCKED_ABSENT = "blocked_feature_absent"
ELIGIBILITY = (
    ELIGIBLE,
    CONTEXT_ONLY,
    NOT_ASSESSABLE,
    BLOCKED_REFERENCE,
    BLOCKED_AMBIGUOUS,
    BLOCKED_COMPARTMENT,
    BLOCKED_ABSENT,
)

#: The observation map's `conditioning_compatibility` token for the only kind of
#: node an initial probability can personalize: a free variable.
ISTATE_PRIOR = "istate_prior"

#: CNT's composition (unstimulated vs E2-primed only) is recorded nowhere in the
#: repository, so it cannot be matched to a reference condition class (Q4).
CONDITION_CLASS = {
    "CNT": "unresolved_cnt_composition_unrecorded",
    "HT": "hormone_treated",
}
RESOLVED_CONDITION_CLASSES = frozenset({"hormone_treated"})

# -- data grain ---------------------------------------------------------------

_R_META = """
suppressPackageStartupMessages(library(SeuratObject))
obj <- readRDS(commandArgs(trailingOnly = TRUE)[1])
md <- obj@meta.data
emit <- function(...) cat(paste(..., sep = "\\t"), "\\n", sep = "")
emit("cells", nrow(md))
for (c in colnames(md)) {
  x <- md[[c]]
  emit("column", c, class(x)[1], sum(is.na(x)), length(unique(x)))
}
emit("orig_ident_equals_sample_id", sum(as.character(md$orig.ident) == as.character(md$sample_id)))
emit("barcode_prefix_equals_sample_id",
     sum(startsWith(rownames(md), paste0(as.character(md$sample_id), "_"))))
tab <- as.data.frame(table(sample_id = md$sample_id, orig_ident = md$orig.ident,
                           celltype_v2 = md$celltype_v2), stringsAsFactors = FALSE)
tab <- tab[tab$Freq > 0, ]
for (i in seq_len(nrow(tab))) emit("group", tab$sample_id[i], tab$orig_ident[i],
                                   tab$celltype_v2[i], tab$Freq[i])
emit("r_version", R.version.string)
emit("seuratobject_version", as.character(packageVersion("SeuratObject")))
"""

GRAIN_COLUMNS = (
    "level",
    "donor",
    "condition",
    "compartment",
    "celltype_v2",
    "sample_id",
    "orig_ident",
    "n_cells",
    "grid_status",
    "node_support_unit_n_cells",
    "independent_unit",
    "replicate_status",
)

MAP_COLUMNS = (
    "model_node",
    "model_compartment",
    "model_logic_is_self",
    "source_gene_or_signature",
    "source_feature_type",
    "absent_features",
    "scrna_compartment",
    "aggregation_unit",
    "conditioning_compatibility",
    "structural_eligibility",
    "mapping_eligibility",
    "preferred_mapping_layer",
    "evidence_provenance",
    "evidence_role",
    "missingness_dropout_semantics",
    "reference_requirement",
    "uncertainty_treatment",
    "leakage_flags",
    "reason",
    "claim_ceiling",
)

SUMMARY_COLUMNS = (
    "unit_id",
    "model_node",
    "donor",
    "condition",
    "condition_class",
    "compartment",
    "source_features",
    "n_cells",
    "exposure",
    "pseudobulk_fraction_f",
    "f_ci_lo",
    "f_ci_hi",
    "detection_fraction_d",
    "d_ci_lo",
    "d_ci_hi",
    "min_nonzero_value",
    "meets_n_min",
    "meets_e_min",
    "c1_pass",
    "c2_pass",
    "missingness_state",
    "absence_call",
    "interval_meaning",
    "raw_value_ref",
    "reference_name",
    "mapping_function",
    "high_state_fraction",
    "initial_on_probability",
    "claim_level",
    "bridge_assumption",
    "leakage_control_status",
)

#: What a valid external reference must supply. Every row is tested by
#: :func:`evaluate_reference`, and every failure it reports starts with its id.
REFERENCE_REQUIREMENTS: tuple[dict[str, str], ...] = (
    {
        "req_id": "RR01",
        "field": "reference_path",
        "requirement": "config/personalization.yaml reference_strategy.reference_path names a reference manifest inside the repository.",
        "why": "Without a declared reference there is no high-state definition; PROFILE's cohort-derived normalization is forbidden here.",
    },
    {
        "req_id": "RR02",
        "field": "source_accession; retrieved_on; donors_path + source_sha256; definition_path + definition_sha256",
        "requirement": "An accession or DOI and retrieval date. donors_path is a repository TSV hashing to source_sha256 with columns donor_id, condition_class, compartment, n_cells and one row per declared donor matching donor_ids, condition_class and compartment. definition_path is a one-row repository TSV hashing to definition_sha256 holding the per-cell high-state definition; the gate reads the definition from that file only.",
        "why": "Every future personalized value must be traceable to an immutable reference whose contents, not only its hash, are checked.",
    },
    {
        "req_id": "RR03",
        "field": "independence: donor_ids; source_accession; source_sha256; derived_from_adoc",
        "requirement": "The reference donors are disjoint from SZ09/SZ10/SZ25; the accession is not E-MTAB-15842; the file is neither EXT-SCRNA-001 nor any data/ object; derived_from_adoc is false.",
        "why": "The high-state definition must be set independently of the three ADOC donors (docs/profile_local_reimplementation.md).",
    },
    {
        "req_id": "RR04",
        "field": "assay; definition layer; definition per_cell_quantity",
        "requirement": "The assay is scRNA-seq or snRNA-seq; the definition is stated on the deposited decontX-corrected counts layer, as count or count_per_10k exactly as mapping_specification.high_state_definition.per_cell_quantity_definitions computes them from the ADOC per-cell values.",
        "why": "A per-cell rule is applicable to ADOC cells only on the quantity and layer it was defined on; a protein or bulk assay has no per-cell rule.",
    },
    {
        "req_id": "RR05",
        "field": "compartment",
        "requirement": "The reference compartment equals the node's analysis compartment (epithelium for E_KLF12_HIGH).",
        "why": "The pre-registered population is the epithelial compartment.",
    },
    {
        "req_id": "RR06",
        "field": "definition feature",
        "requirement": "The definition is on the node's own measurement feature, by the same HGNC symbol.",
        "why": "A partial or aliased feature set is a different state.",
    },
    {
        "req_id": "RR07",
        "field": "definition rule; definition threshold; aggregation_unit",
        "requirement": "The rule is one of >= or >, the threshold is finite and non-negative, and it was derived over reference DONORS (aggregation_unit=donor) numbering at least mapping_specification.parameters.min_reference_donors.",
        "why": "Cells are not replicates; a per-cell rule learnt from one donor's cells is one donor's rule.",
    },
    {
        "req_id": "RR08",
        "field": "condition_class",
        "requirement": "The reference condition class equals the ADOC unit's condition class, which must itself be resolved.",
        "why": "CNT's composition is unrecorded (owner Q4); an unmatched condition applies a treated definition to untreated cells.",
    },
    {
        "req_id": "RR09",
        "field": "outcome_blind; columns of both files",
        "requirement": "outcome_blind is true and neither file carries a column beyond its schema (no adhesion, pregnancy, implantation or fertility outcome, and no model output).",
        "why": "The high-state definition must be independent of the outcomes the model is later compared with.",
    },
    {
        "req_id": "RR10",
        "field": "preregistration_path; preregistration_sha256",
        "requirement": "preregistration_path is a repository file hashing to the declared 64-hex preregistration_sha256, first committed strictly before (a proper git ancestor of) the commits that first add the reference manifest, donors file and definition file, and the first commit whose config/personalization.yaml names the manifest; the later mapping unit must also show that its first mapped value descends from it.",
        "why": "Ordering is the only protection against choosing a definition that makes the donors look a particular way.",
    },
    {
        "req_id": "RR11",
        "field": "mapping_specification.parameters",
        "requirement": "Every load-bearing parameter of the mapping specification has a value and a provenance that is neither pending nor forbidden.",
        "why": "A reference alone must never open the gate while the owner has a parameter still to set.",
    },
    {
        "req_id": "RR12",
        "field": "definition evidence_citation; evidence_kind; owner_accepted_on",
        "requirement": "The definition cites its source (DOI or accession), declares an evidence kind (published_per_cell_definition or reference_state_separation), and records the date the owner accepted that evidence.",
        "why": "The gate can check that a definition is evidenced and accepted, not whether the biology is adequate; that judgement stays with the owner.",
    },
    {
        "req_id": "RR13",
        "field": "bridge_validation_path; bridge_validation_sha256",
        "requirement": "ONLY for a measured_personalization claim: a one-row repository TSV hashing to bridge_validation_sha256, committed to git, whose bridge_statement is the pre-registered bridge verbatim, citing an independent evidence-backed calibration or validation of fraction-high -> MaBoSS initial ensemble frequency (evidence_kind independent_calibration or independent_validation, independent_of_adoc true), with the owner's acceptance date. Without it every value stays assumption_conditioned_scenario.",
        "why": "The bridge has no experimental support in this repository; only independent evidence, accepted before the claim is upgraded, can make a value a measurement rather than a scenario.",
    },
    {
        "req_id": "RR14",
        "field": "definition comparability; comparability_evidence; threshold_derivation; threshold_variants; variant_selection; calibration_path + calibration_sha256",
        "requirement": "Gates EXECUTION of the assumption-conditioned scenarios only. The hashed definition declares comparability (same_pipeline_reprocessed, or cross_dataset_calibration with a hashed, committed calibration artifact) with a cited source covering platform, depth, normalization and batch; cites its threshold derivation (a DOI or accession, or, for a custom method only, a repository-local pre-registration artifact repo:<path>@<commit>#sha256:<digest> whose commit is the earliest holding exactly those bytes, strictly precedes the frozen pre-registration, and whose bytes are unchanged; owner schema change of 2026-09-25; that it is used only for a custom method is the owner's rule and is not machine-checked); lists at least two distinct pre-registered threshold sensitivity variants besides the primary threshold; and declares variant_selection=all_reported_none_selected. The frozen pre-registration (RR10's content-ordered commit) names the definition_path and exactly definition_sha256, and calibration_path and calibration_sha256 when calibrated, so the threshold, variants, comparability and calibration were fixed before selection. Each variant is reported as its own scenario value, and none may be selected using ADOC outcomes. Meeting RR14 does not meet RR13 and upgrades no claim.",
        "why": "A per-cell threshold transferred across datasets can convert platform, depth, preprocessing or an arbitrary cut-off into donor-specific probabilities; variants make that sensitivity visible instead of hidden.",
    },
)

#: Words that must never appear as a field of any emitted artifact.
FORBIDDEN_OUTPUT_FIELDS = (
    "rate_up",
    "rate_down",
    "rate_modifier",
    "clamp",
    "mutation",
    "nb_mutable",
    "is_mutant",
)


class Phase2AError(RuntimeError):
    """A premise the contract rests on does not hold; nothing is written."""


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_sha(root: Path, relative: Path) -> str:
    """The same digest `phase1b_closure._tree_sha` records for `models/`.

    Re-implemented rather than imported: that module imports
    `dt_adoc.calibration`, which this one must not see.
    """
    digest = hashlib.sha256()
    base = root / relative
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        if "__pycache__" in path.parts:
            continue
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(_sha(path).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_sha(root: Path) -> str:
    for row in _tsv(root / EXTERNAL_MANIFEST):
        if row["asset_id"] == ASSET_ID:
            return row["sha256"]
    raise Phase2AError(f"{ASSET_ID} is not in {EXTERNAL_MANIFEST}")


def forbidden_reference_shas(root: Path) -> frozenset[str]:
    """Every ADOC object a reference must not be: EXT-SCRNA-001 and all of data/."""
    shas = {manifest_sha(root)}
    for row in _tsv(root / DATA_MANIFEST):
        value = row.get("sha256", "")
        if value:
            shas.add(value)
    return frozenset(shas)


# --------------------------------------------------------------------------
# Step 1 -- meta.data extraction (needs the object and R)
# --------------------------------------------------------------------------


def parse_extraction(stdout: str) -> dict[str, Any]:
    record: dict[str, Any] = {"columns": [], "groups": []}
    for line in stdout.splitlines():
        parts = line.split("\t")
        kind = parts[0]
        if kind == "cells":
            record["n_cells"] = int(parts[1])
        elif kind == "column":
            record["columns"].append(
                {
                    "name": parts[1],
                    "class": parts[2],
                    "n_na": int(parts[3]),
                    "n_distinct": int(parts[4]),
                }
            )
        elif kind in ("orig_ident_equals_sample_id", "barcode_prefix_equals_sample_id"):
            record[kind] = int(parts[1])
        elif kind == "group":
            record["groups"].append(
                {
                    "sample_id": parts[1],
                    "orig_ident": parts[2],
                    "celltype_v2": parts[3],
                    "n_cells": int(parts[4]),
                }
            )
        elif kind in ("r_version", "seuratobject_version"):
            record[kind] = parts[1]
    record["groups"].sort(
        key=lambda g: (g["sample_id"], g["orig_ident"], g["celltype_v2"])
    )
    return record


def extract(rds: Path, *, rscript: str, root: Path = REPO) -> Path:
    """Read meta.data from the object and commit only aggregate counts."""
    expected = manifest_sha(root)
    observed = _sha(rds)
    if observed != expected:
        raise Phase2AError(f"{rds} hashes to {observed}, not the manifest's {expected}")
    with tempfile.NamedTemporaryFile(
        "w", suffix=".R", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(_R_META)
        script = handle.name
    try:
        done = subprocess.run(
            [rscript, script, str(rds)], capture_output=True, text=True, check=False
        )
    finally:
        Path(script).unlink(missing_ok=True)
    if done.returncode != 0:
        raise Phase2AError(f"R failed: {done.stderr.strip()[:400]}")
    record = {
        "schema_version": SCHEMA_VERSION,
        "asset_id": ASSET_ID,
        "rds_sha256": observed,
        "rds_size_bytes": rds.stat().st_size,
        "extracted": "meta.data only; no expression layer read; aggregated inside R",
        **parse_extraction(done.stdout),
    }
    destination = root / EXTRACTION
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


# --------------------------------------------------------------------------
# Step 2 -- the data-grain audit
# --------------------------------------------------------------------------


def parse_sample(sample_id: str) -> tuple[str, str]:
    """Donor and condition from `sample_id`, the only field that carries them.

    Same rule as `node_support.parse_unit`, restated so a malformed identifier
    is refused here too rather than silently split.
    """
    donor_part, sep, condition = sample_id.partition("_")
    if not sep or not donor_part.endswith("TE"):
        raise Phase2AError(f"unparseable sample_id {sample_id!r}")
    donor = donor_part[: -len("TE")]
    if donor not in C.DONORS or condition not in C.CONDITIONS:
        raise Phase2AError(f"sample_id {sample_id!r} names no frozen donor/condition")
    return donor, condition


def check_extraction(extraction: dict[str, Any], root: Path) -> None:
    """Refuse an extraction that is not the pinned object or disagrees with it."""
    findings = _json(root / NODE_SUPPORT_FINDINGS)
    expected = manifest_sha(root)
    for label, value in (
        ("extraction", extraction["rds_sha256"]),
        ("node_support_findings", findings["provenance"]["rds_sha256"]),
    ):
        if value != expected:
            raise Phase2AError(
                f"{label} is bound to {value}, not {ASSET_ID} {expected}"
            )
    columns = tuple(c["name"] for c in extraction["columns"])
    if columns != verify_rds.EXPECTED_META_COLUMNS:
        raise Phase2AError(
            f"meta.data columns {columns} != {verify_rds.EXPECTED_META_COLUMNS}"
        )
    if extraction["n_cells"] != verify_rds.EXPECTED_CELLS:
        raise Phase2AError(
            f"{extraction['n_cells']} cells != {verify_rds.EXPECTED_CELLS}"
        )
    by_sample: dict[str, int] = {}
    by_label: dict[str, int] = {}
    for group in extraction["groups"]:
        by_sample[group["sample_id"]] = (
            by_sample.get(group["sample_id"], 0) + group["n_cells"]
        )
        by_label[group["celltype_v2"]] = (
            by_label.get(group["celltype_v2"], 0) + group["n_cells"]
        )
        if group["celltype_v2"] not in C.COMPARTMENT_OF_LABEL:
            raise Phase2AError(
                f"celltype_v2 {group['celltype_v2']!r} is outside the partition"
            )
    if by_sample != verify_rds.EXPECTED_SAMPLES:
        raise Phase2AError(
            f"per-sample counts {by_sample} != {verify_rds.EXPECTED_SAMPLES}"
        )
    if by_label != verify_rds.EXPECTED_POPULATIONS:
        raise Phase2AError(
            f"per-label counts {by_label} != {verify_rds.EXPECTED_POPULATIONS}"
        )


def grain_rows(extraction: dict[str, Any], root: Path) -> list[dict[str, object]]:
    """Every donor x condition x label, and every donor x condition x compartment.

    Zero-count combinations are rows, not omissions: an empty grid cell is a
    finding. The compartment roll-up must equal the node-support unit counts.
    """
    check_extraction(extraction, root)
    unit_counts: dict[str, int] = _json(root / NODE_SUPPORT_FINDINGS)[
        "unit_cell_counts"
    ]
    counts: dict[tuple[str, str, str], tuple[str, str, int]] = {}
    for group in extraction["groups"]:
        donor, condition = parse_sample(group["sample_id"])
        counts[(donor, condition, group["celltype_v2"])] = (
            group["sample_id"],
            group["orig_ident"],
            group["n_cells"],
        )
    common = {
        "independent_unit": "donor",
        "replicate_status": "cells_are_within_unit_measurement_precision_not_replicates",
    }
    rows: list[dict[str, object]] = []
    rollup: dict[str, int] = {}
    for donor in C.DONORS:
        for condition in C.CONDITIONS:
            sample = f"{donor}TE_{condition}"
            for label in sorted(C.COMPARTMENT_OF_LABEL):
                compartment = C.COMPARTMENT_OF_LABEL[label]
                sample_id, orig, n = counts.get(
                    (donor, condition, label), (sample, "", 0)
                )
                unit = f"{donor}_{condition}_{compartment}"
                rollup[unit] = rollup.get(unit, 0) + n
                rows.append(
                    {
                        "level": "celltype_v2",
                        "donor": donor,
                        "condition": condition,
                        "compartment": compartment,
                        "celltype_v2": label,
                        "sample_id": sample_id,
                        "orig_ident": orig or "-",
                        "n_cells": n,
                        "grid_status": "populated" if n else "empty_combination",
                        "node_support_unit_n_cells": "-",
                        **common,
                    }
                )
    for donor in C.DONORS:
        for condition in C.CONDITIONS:
            for compartment in sorted(set(C.COMPARTMENT_OF_LABEL.values())):
                unit = f"{donor}_{condition}_{compartment}"
                n = rollup[unit]
                recorded = unit_counts.get(unit, 0)
                if recorded != n:
                    raise Phase2AError(
                        f"{unit}: {n} cells here, {recorded} in node support"
                    )
                rows.append(
                    {
                        "level": "compartment_unit",
                        "donor": donor,
                        "condition": condition,
                        "compartment": compartment,
                        "celltype_v2": "-",
                        "sample_id": f"{donor}TE_{condition}",
                        "orig_ident": f"{donor}TE_{condition}" if n else "-",
                        "n_cells": n,
                        "grid_status": "populated" if n else "empty_grid_cell",
                        "node_support_unit_n_cells": recorded,
                        **common,
                    }
                )
    return rows


# --------------------------------------------------------------------------
# Step 3 -- the node personalization map
# --------------------------------------------------------------------------


def model_nodes(root: Path) -> list[dict[str, str]]:
    """The v0.5.1 node dictionary, refused unless it equals `network.bnd`."""
    dictionary = _tsv(root / NODE_DICTIONARY)
    rules = parse_bnd_rules(root / NETWORK)
    if sorted(r["node_id"] for r in dictionary) != sorted(rules):
        raise Phase2AError("node_dictionary.tsv and network.bnd name different nodes")
    for row in dictionary:
        row["logic_is_self"] = (
            "true" if rules[row["node_id"]].strip() == row["node_id"] else "false"
        )
    return dictionary


def classify(
    obs: dict[str, str],
    node: dict[str, str],
    absent: frozenset[str],
) -> dict[str, str]:
    """One node's eligibility, from frozen columns only. Pure; order matters.

    1. not observable -> not_RNA_assessable
    2. the map's analysis compartment is not the model's compartment, or not a
       primary analysis compartment -> blocked_wrong_compartment
    3. every measurement feature is absent from the object -> blocked_feature_absent
    4. the map's mapping mechanics and the model's rule disagree about whether
       the node is free -> blocked_ambiguous_mapping
    5. a derived node (rule_override_required) -> context_only (owner Q1: an
       istate on a derived node is overwritten by its rule)
    6. a free variable (istate_prior) -> eligible_initial_probability, which is
       blocked_missing_reference until the reference gate passes
    """
    observability = obs["measurement_observability"]
    compatibility = obs["conditioning_compatibility"]
    features = C.features(obs)
    missing = tuple(f for f in features if f in absent)
    if observability == C.NOT_ASSESSABLE:
        return {
            "structural": NOT_ASSESSABLE,
            "reason": "measurement_observability=not_observable in the frozen observation map",
        }
    analysis = C.COMPARTMENT_OF_NODE.get(obs["compartment"])
    if analysis != node["compartment"] or analysis not in C.PRIMARY_COMPARTMENTS:
        return {
            "structural": BLOCKED_COMPARTMENT,
            "reason": f"observation-map compartment {obs['compartment']!r} (analysis {analysis!r}) vs model compartment {node['compartment']!r}",
        }
    if features and len(missing) == len(features):
        return {
            "structural": BLOCKED_ABSENT,
            "reason": f"every feature absent from the object: {';'.join(missing)}",
        }
    free = node["logic_is_self"] == "true"
    if (compatibility == ISTATE_PRIOR) != free:
        return {
            "structural": BLOCKED_AMBIGUOUS,
            "reason": f"conditioning_compatibility={compatibility} but model_logic_is_self={node['logic_is_self']}",
        }
    if compatibility != ISTATE_PRIOR:
        return {
            "structural": CONTEXT_ONLY,
            "reason": "derived node: its istate is an initial condition MaBoSS overwrites from the rule within a few ticks, not a constraint (v05 plan section 0.2(c); owner Q1)",
        }
    return {
        "structural": ELIGIBLE,
        "reason": "free variable (logic = self; conditioning_compatibility=istate_prior): an initial probability is the whole of its personalization",
    }


def map_rows(root: Path, *, reference_ready: bool) -> list[dict[str, object]]:
    observations = {
        row["model_node"]: row for row in C.observation_rows(root / OBSERVATION_MAP)
    }
    nodes = model_nodes(root)
    names = [n["node_id"] for n in nodes]
    if sorted(observations) != sorted(names):
        raise Phase2AError("the observation map and v0.5.1 name different nodes")
    absent = frozenset(_json(root / NODE_SUPPORT_FINDINGS)["absent_features"])
    rows: list[dict[str, object]] = []
    for node in sorted(nodes, key=lambda n: n["node_id"]):
        obs = observations[node["node_id"]]
        verdict = classify(obs, node, absent)
        structural = verdict["structural"]
        current = structural
        if structural == ELIGIBLE and not reference_ready:
            current = BLOCKED_REFERENCE
        features = C.features(obs)
        missing = [f for f in features if f in absent]
        assessable = structural not in (
            NOT_ASSESSABLE,
            BLOCKED_COMPARTMENT,
            BLOCKED_ABSENT,
        )
        flags = []
        if obs["evidence_role"] == "construction":
            flags.append("construction_feature_not_citable_as_independent_validation")
        if node["node_id"] in C.NOT_BLIND_NODES:
            flags.append("not_blind_per_unit_values_committed_before_this_contract")
        if missing:
            flags.append("feature_partially_absent_no_alias_substituted")
        if assessable:
            flags.append("same_cells_may_not_both_set_and_score")
        rows.append(
            {
                "model_node": node["node_id"],
                "model_compartment": node["compartment"],
                "model_logic_is_self": node["logic_is_self"],
                "source_gene_or_signature": ";".join(features) or "-",
                "source_feature_type": C.measurement_type(obs),
                "absent_features": ";".join(missing) or "-",
                "scrna_compartment": C.COMPARTMENT_OF_NODE.get(obs["compartment"], "-")
                if assessable
                else "-",
                "aggregation_unit": "donor x condition x compartment"
                if assessable
                else "not_applicable",
                "conditioning_compatibility": obs["conditioning_compatibility"],
                "structural_eligibility": structural,
                "mapping_eligibility": current,
                "preferred_mapping_layer": PERMITTED_LAYER
                if structural == ELIGIBLE
                else "none",
                "evidence_provenance": f"{OBSERVATION_MAP}:{obs['mapping_id']}; {NODE_SUPPORT_EVIDENCE}"
                if assessable
                else f"{OBSERVATION_MAP}:{obs['mapping_id']}",
                "evidence_role": obs["evidence_role"],
                "missingness_dropout_semantics": _missingness(structural),
                "reference_requirement": "external per-cell high-state definition satisfying RR01-RR12 and RR14"
                if structural == ELIGIBLE
                else "not_applicable",
                "uncertainty_treatment": _uncertainty(structural),
                "leakage_flags": ";".join(flags) or "-",
                "reason": verdict["reason"],
                "claim_ceiling": obs["claim_ceiling"],
            }
        )
    return rows


def _missingness(structural: str) -> str:
    if structural == NOT_ASSESSABLE:
        return "not measured: no value exists and none is inferred"
    if structural in (BLOCKED_COMPARTMENT, BLOCKED_ABSENT, BLOCKED_AMBIGUOUS):
        return "no mappable value: the node keeps the shared baseline istate"
    return (
        "zero or low detection is provisional_corrected_layer_only (decontX layer; raw "
        "invariance shown for KLF12 epithelium only) and is never OFF, never a clamp, "
        "never 0; a missing or below-minimum unit is unresolved and keeps the shared baseline istate"
    )


def _uncertainty(structural: str) -> str:
    if structural != ELIGIBLE:
        return "not_applicable"
    return (
        "within-donor cell bootstrap of the high-state fraction: cell-sampling "
        "uncertainty only, never donor or population inference, never pooled"
    )


# --------------------------------------------------------------------------
# Step 4 -- donor x condition x compartment summaries
# --------------------------------------------------------------------------


def summary_rows(
    root: Path, mapping: list[dict[str, object]]
) -> list[dict[str, object]]:
    """Copy the committed node-support per-unit statistics for eligible nodes.

    Only the node's own compartment. Every grid cell of that compartment is a
    row, including an empty one. Values are copied as committed, never
    recomputed and never zero-filled.
    """
    evidence = {
        (row["unit_id"], row["name"]): row
        for row in _tsv(root / NODE_SUPPORT_EVIDENCE)
        if row["level"] == "node"
    }
    qc = {row["unit_id"]: row for row in _tsv(root / NODE_SUPPORT_QC)}
    unit_cells: dict[str, int] = _json(root / NODE_SUPPORT_FINDINGS)["unit_cell_counts"]
    rows: list[dict[str, object]] = []
    for node in mapping:
        if node["structural_eligibility"] != ELIGIBLE:
            continue
        compartment = str(node["scrna_compartment"])
        for donor in C.DONORS:
            for condition in C.CONDITIONS:
                unit = f"{donor}_{condition}_{compartment}"
                source = evidence.get((unit, str(node["model_node"])))
                unit_qc = qc.get(unit)
                blank = "-"
                if source is None or unit_qc is None:
                    # An empty unit and a populated unit whose statistics are
                    # missing are different states; neither is zero-filled.
                    n = unit_cells.get(unit, 0)
                    state = "unit_empty" if n == 0 else "unit_statistics_missing"
                    stats = dict.fromkeys(
                        (
                            "n_cells",
                            "exposure",
                            "f",
                            "f_ci_lo",
                            "f_ci_hi",
                            "d",
                            "d_ci_lo",
                            "d_ci_hi",
                            "min_nonzero_value",
                        ),
                        blank,
                    )
                    stats["n_cells"] = str(n)
                    flags = dict.fromkeys(
                        ("meets_n_min", "meets_e_min", "c1_pass", "c2_pass"), blank
                    )
                else:
                    stats = source
                    flags = unit_qc
                    state = (
                        "measured"
                        if unit_qc["meets_n_min"] == "true"
                        and unit_qc["meets_e_min"] == "true"
                        else "unit_below_minimum"
                    )
                condition_class = CONDITION_CLASS[condition]
                resolved = condition_class in RESOLVED_CONDITION_CLASSES
                rows.append(
                    {
                        "unit_id": unit,
                        "model_node": node["model_node"],
                        "donor": donor,
                        "condition": condition,
                        "condition_class": condition_class,
                        "compartment": compartment,
                        "source_features": node["source_gene_or_signature"],
                        "n_cells": stats["n_cells"],
                        "exposure": stats["exposure"],
                        "pseudobulk_fraction_f": stats["f"],
                        "f_ci_lo": stats["f_ci_lo"],
                        "f_ci_hi": stats["f_ci_hi"],
                        "detection_fraction_d": stats["d"],
                        "d_ci_lo": stats["d_ci_lo"],
                        "d_ci_hi": stats["d_ci_hi"],
                        "min_nonzero_value": stats["min_nonzero_value"],
                        "meets_n_min": flags["meets_n_min"],
                        "meets_e_min": flags["meets_e_min"],
                        "c1_pass": flags["c1_pass"],
                        "c2_pass": flags["c2_pass"],
                        "missingness_state": state,
                        "absence_call": "provisional_corrected_layer_only"
                        if state == "measured"
                        else "not_applicable",
                        "interval_meaning": "within-donor cell bootstrap: precision of this donor's sampled cells, not a replicate interval"
                        if state == "measured"
                        else "not_applicable",
                        "raw_value_ref": f"{NODE_SUPPORT_EVIDENCE}:{unit}:{node['model_node']}"
                        if source
                        else "-",
                        "reference_name": "null",
                        "mapping_function": "unresolved_no_external_high_state_definition"
                        if resolved
                        else "unresolved_condition_class_and_no_external_high_state_definition",
                        "high_state_fraction": "unresolved",
                        "initial_on_probability": "unresolved",
                        "claim_level": CLAIM_LEVEL,
                        "bridge_assumption": BRIDGE_ASSUMPTION,
                        "leakage_control_status": "not_mapped",
                    }
                )
    return rows


# --------------------------------------------------------------------------
# Step 5 -- the mapping specification and the reference gate
# --------------------------------------------------------------------------

#: The bridge from step 2 to step 3, quoted from the frozen pre-registration
#: (`docs/scrna/klf12_prior_preregistration.md`, "The assumption that bridges
#: step 2 to step 3"). Quoted rather than restated so it cannot drift.
BRIDGE_SOURCE = Path("docs/scrna/klf12_prior_preregistration.md")
BRIDGE_ASSUMPTION = (
    "the ensemble frequency with which the modelled epithelial compartment is "
    "initialised in the KLF12-high state equals the estimated fraction of "
    "epithelial cells in that state."
)
PER_CELL_QUANTITIES = ("count", "count_per_10k")
RULES = (">=", ">")
ASSAYS = ("scRNA-seq", "snRNA-seq")
DONORS_COLUMNS = ("donor_id", "condition_class", "compartment", "n_cells")
DEFINITION_COLUMNS = (
    "feature",
    "layer",
    "per_cell_quantity",
    "rule",
    "threshold",
    "evidence_citation",
    "evidence_kind",
    "owner_accepted_on",
    "comparability",
    "comparability_evidence",
    "threshold_derivation",
    "threshold_variants",
    "variant_selection",
)
#: How a reference's per-cell values are made comparable with ADOC's (RR14).
#: `cross_dataset_calibration` needs its own hashed, committed artifact.
COMPARABILITY = ("same_pipeline_reprocessed", "cross_dataset_calibration")
#: Every variant is reported as its own scenario; none is chosen (RR14).
VARIANT_SELECTION = "all_reported_none_selected"
#: What may back a per-cell high-state definition. Machine-checkable only as a
#: declared kind with a citation; whether the evidence is biologically adequate
#: is the owner's call, recorded as `owner_accepted_on` (RR12).
EVIDENCE_KINDS = ("published_per_cell_definition", "reference_state_separation")
#: Definition fields that cite a source; none may be the ADOC accession (RR03).
CITATION_FIELDS = (
    "evidence_citation",
    "comparability_evidence",
    "threshold_derivation",
)

#: Every value this contract can ever license is conditioned on the bridge
#: assumption, which has no experimental support (owner decision on B1).
CLAIM_LEVEL = "assumption_conditioned_scenario"
MEASURED_CLAIM_LEVEL = "measured_personalization"
BRIDGE_VALIDATION_COLUMNS = (
    "bridge_statement",
    "evidence_citation",
    "evidence_kind",
    "independent_of_adoc",
    "owner_accepted_on",
)
BRIDGE_EVIDENCE_KINDS = ("independent_calibration", "independent_validation")
PENDING = "owner_decision_pending"
PERMITTED_PROVENANCE = ("owner_decided",)
PARAMETER_PROVENANCE_FORBIDDEN = (
    PENDING,
    "fitted",
    "tuned_on_outcome",
    "estimated_from_adoc_donors",
)


def mapping_specification() -> dict[str, Any]:
    """The frozen three-step form (owner decision on review finding B1).

    The high-state definition comes from the external reference. The only owner
    parameter, `min_reference_donors`, was set to 3 by the owner on 2026-09-25
    (Phase 2B decision D2), before any candidate reference value was read.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "permitted_layer": PERMITTED_LAYER,
        "forbidden_layers": list(FORBIDDEN_LAYERS),
        "output_field": "initial_on_probability",
        "applies_to": "nodes with structural_eligibility=eligible_initial_probability only (free variables)",
        "source": f"{BRIDGE_SOURCE}, three steps that must not be collapsed",
        "steps": {
            "1_measurement": "the node's feature per cell, on the deposited decontX-corrected counts layer, for every cell of one donor x condition x epithelium unit",
            "2_latent_state": "each cell is classified high or not by the EXTERNAL reference's per-cell high-state definition (feature, per-cell quantity, rule, threshold); the unit's estimate is the fraction of its cells classified high",
            "3_conditioning": "initial_on_probability = that fraction, under the bridge assumption",
        },
        "claim_level": CLAIM_LEVEL,
        "claim_rule": "every generated value carries the bridge assumption and claim_level=assumption_conditioned_scenario; it may not be described as measured personalization unless RR13 is met and the owner has accepted it before the claim is upgraded",
        "bridge_assumption": {
            "text": BRIDGE_ASSUMPTION,
            "source": str(BRIDGE_SOURCE),
            "status": "interpretive assumption with no experimental support in this repository; every conditioned result must carry it",
        },
        "high_state_definition": {
            "supplied_by": "the external reference only (RR01-RR12 and RR14)",
            "per_cell_quantity_vocabulary": list(PER_CELL_QUANTITIES),
            "per_cell_quantity_definitions": {
                "count": "the feature's value in the deposited counts layer (node_support per-cell column counts_<gene>)",
                "count_per_10k": "count / depth_counts * 10^4, where depth_counts is the cell's column sum of the deposited counts layer (node_support per-cell column depth_counts)",
            },
            "file_columns": list(DEFINITION_COLUMNS),
            "evidence_kinds": list(EVIDENCE_KINDS),
            "rule_vocabulary": list(RULES),
            "never_from": "the ADOC donors, their per-unit statistics, or any outcome",
        },
        "uncertainty": {
            "interval": "within-donor cell bootstrap of the fraction (node-support B and seed)",
            "meaning": "cell-sampling uncertainty of this donor's unit only; not donor or population inference, never pooled across donors",
            "variants_reported": [
                "point",
                "cell_bootstrap_lo",
                "cell_bootstrap_hi",
                "shared_baseline",
            ],
            "shared_baseline": "the unpersonalized v0.5.1 baseline.cfg istate, the matched comparator for any personalized run",
        },
        "sensitivity": {
            "rule": "the primary threshold and every pre-registered variant (RR14, at least two) each yield their own scenario value, reported side by side",
            "selection": "none: no variant is preferred, and none may be selected using ADOC outcomes or model output",
            "claim": "sensitivity variants widen the scenario set; they never satisfy RR13 or upgrade the claim",
        },
        "boundary": {
            "rule": "a point estimate or interval bound of exactly 0 or 1 is unresolved and is not written",
            "why": "E_KLF12_HIGH has logic = E_KLF12_HIGH, so an initial probability of 0 or 1 fixes it in every trajectory: a clamp in effect, which scRNA zeros and dropout may never create",
        },
        "clipping": "none: no value is moved into range; an out-of-range or boundary value is refused (config/personalization.yaml clipping [0, 1] is not used)",
        "missing": {
            "rule": "a missing, empty, below-minimum or condition-unresolved unit yields initial_on_probability=unresolved and keeps the shared baseline istate",
            "default_0_5": "never applied implicitly; only as an explicitly declared model assumption with its own provenance, which this contract does not declare",
            "zero_detection": "a measured zero count is a cell not classified high by the external rule; it is never OFF for the node and never a clamp",
        },
        "parameters": {
            "min_reference_donors": {"value": 3, "provenance": "owner_decided"},
        },
        "parameter_domains": {"min_reference_donors": "integer >= 1"},
        "parameter_provenance_permitted": list(PERMITTED_PROVENANCE),
        "parameter_provenance_forbidden": list(PARAMETER_PROVENANCE_FORBIDDEN),
        "outcome_independence": "no adhesion, pregnancy, secretion, model output or phenotype value is an input to any parameter or to the high-state definition",
    }


def high_state_fraction(per_cell: list[float], *, rule: str, threshold: float) -> float:
    """Step 2: the fraction of a unit's cells the external rule calls high."""
    if rule not in RULES:
        raise ValueError(f"rule {rule!r} is not one of {RULES}")
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError("threshold must be finite and non-negative")
    if not per_cell:
        raise ValueError("an empty unit has no fraction")
    if any(not math.isfinite(v) or v < 0 for v in per_cell):
        raise ValueError("per-cell values must be finite and non-negative")
    high = sum((v >= threshold) if rule == ">=" else (v > threshold) for v in per_cell)
    return high / len(per_cell)


def initial_probability(
    point: float | None, lo: float | None, hi: float | None
) -> float | str:
    """Step 3: the fraction itself, or `unresolved`. Never 0, never 1."""
    values = (point, lo, hi)
    if any(v is None or not math.isfinite(v) for v in values):
        return "unresolved"
    if not lo <= point <= hi or lo < 0 or hi > 1:
        raise ValueError(f"incoherent estimate {values}")
    if lo <= 0.0 or hi >= 1.0:
        return "unresolved_boundary"
    return point


def load_reference_manifest(
    root: Path, policy: dict[str, Any]
) -> dict[str, Any] | None:
    path = policy["reference_strategy"].get("reference_path")
    if path is None:
        return None
    resolved = _inside(root, path)
    if resolved is None:
        return {"__unreadable__": str(path)}
    manifest = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    return {**manifest, "__path__": str(path)}


def _inside(root: Path, relative: object) -> Path | None:
    """A file inside the repository, or None."""
    if not isinstance(relative, str) or not relative:
        return None
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        return None
    return resolved


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return done.stdout.strip() if done.returncode == 0 else ""


def first_commit(root: Path, path: Path) -> str:
    """The commit that first added `path`, or '' if it was never committed."""
    relative = str(path.relative_to(root.resolve()))
    added = _git(root, "log", "--diff-filter=A", "--format=%H", "--", relative)
    return added.splitlines()[-1] if added else ""


def activation_commit(root: Path, manifest: str) -> str:
    """The first commit whose `config/personalization.yaml` names `manifest`.

    That commit is what activates a reference; until it exists the reference
    is inert, whatever files are present.
    """
    commits = _git(root, "log", "--reverse", "--format=%H", "--", str(PERSONALIZATION))
    for commit in commits.splitlines():
        text = _git(root, "show", f"{commit}:{PERSONALIZATION}")
        try:
            strategy = (yaml.safe_load(text) or {}).get("reference_strategy") or {}
        except yaml.YAMLError:
            continue
        if strategy.get("reference_path") == manifest:
            return commit
    return ""


def digest_commit(root: Path, path: Path, digest: str) -> str:
    """The earliest commit in which `path` holds bytes hashing to `digest`.

    Ordering the PATH is not enough: an early placeholder rewritten after the
    reference was chosen would pass. What must precede selection is the
    declared content itself.
    """
    relative = str(path.relative_to(root.resolve()))
    commits = _git(root, "log", "--reverse", "--format=%H", "--", relative)
    for commit in commits.splitlines():
        done = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{relative}"],
            capture_output=True,
            check=False,
        )
        if done.returncode == 0 and hashlib.sha256(done.stdout).hexdigest() == digest:
            return commit
    return ""


def strictly_precedes(root: Path, earlier: str, later: str) -> bool:
    """`earlier` is a proper ancestor of `later` in the repository history."""
    if not earlier or not later or earlier == later:
        return False
    done = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", earlier, later],
        capture_output=True,
        check=False,
    )
    return done.returncode == 0


def _hashed_tsv(
    root: Path, relative: object, digest: object
) -> tuple[list[str], list[dict[str, str]]] | None:
    """A repository TSV whose bytes hash to `digest`, read; else None."""
    path = _inside(root, relative)
    if path is None or not isinstance(digest, str) or _sha(path) != digest:
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def per_cell_quantity(count: float, depth: float, quantity: str) -> float:
    """The per-cell quantity a definition is stated on, from ADOC per-cell values.

    `count` is the feature's value in the deposited counts layer and `depth` the
    cell's column sum of that layer, exactly as `node_support`'s per-cell table
    records them (`counts_<gene>`, `depth_counts`).
    """
    if quantity == "count":
        return count
    if quantity == "count_per_10k":
        if not depth > 0:
            raise ValueError("count_per_10k needs a positive depth")
        return count / depth * 1e4
    raise ValueError(
        f"per-cell quantity {quantity!r} is not one of {PER_CELL_QUANTITIES}"
    )


#: A DOI (optionally `doi:`-prefixed) or an archive accession such as
#: E-MTAB-15842, GSE123456 or PRJNA123456.
_CITATION = re.compile(
    r"^(?:doi:)?10\.\d{4,9}/\S+$|^[A-Z]{1,6}(?:-[A-Z]{1,6})?-?\d{3,}$"
)


def _normalised(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value).upper())


def is_adoc_donor(value: object) -> bool:
    """Any spelling that names an ADOC donor: case, spacing and prefixes aside."""
    text = _normalised(value)
    return any(donor in text for donor in C.DONORS)


def is_adoc_citation(value: object) -> bool:
    """The ADOC accession under any spelling; it can never be independent evidence."""
    return "EMTAB15842" in _normalised(value)


def _is_citation(value: object) -> bool:
    return isinstance(value, str) and bool(_CITATION.match(value))


def _is_date(value: object) -> bool:
    if isinstance(value, datetime.date):
        return True
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _not_before(later: object, earlier: object) -> bool:
    """Both ISO dates and `later` is not before `earlier`; no clock is read."""
    if not (_is_date(later) and _is_date(earlier)):
        return False
    return str(later) >= str(earlier)


def _positive_int(value: str) -> bool:
    return bool(re.fullmatch(r"[1-9]\d*", value or ""))


#: A custom threshold method may cite the repository artifact that froze it
#: (owner schema change of 2026-09-25, Phase-2B amendment 03), never a minted
#: DOI. Bound by commit, path and content, and only for threshold_derivation.
_REPO_CITATION = re.compile(
    r"^repo:(?P<path>[A-Za-z0-9_][A-Za-z0-9_./-]*)@(?P<commit>[0-9a-f]{40})"
    r"#sha256:(?P<sha>[0-9a-f]{64})$"
)


def _repository_citation(
    value: object, root: Path, frozen: str, forbidden_shas: frozenset[str]
) -> bool:
    """A repository-local citation whose bytes, commit and ordering all check out.

    The commit must be the EARLIEST one holding exactly those bytes at that path
    (so the citation names when the method was frozen, not a later copy), it
    must strictly precede the frozen pre-registration of the definition, and
    the working tree must still hold the same bytes.

    "For a custom method only" is the owner's rule and is NOT checked here:
    whether a published per-cell definition exists (D3 prefers one) is a
    judgement about the literature that no field of the definition can carry.
    """
    match = _REPO_CITATION.match(value) if isinstance(value, str) else None
    if match is None or not frozen:
        return False
    relative = Path(match["path"])
    if ".." in relative.parts or relative.parts[0] == "data":
        return False
    # Bound to the NAMED path: no component of it below the root may be a
    # symlink (checked before anything is resolved), and the resolved file must
    # lie inside the repository and outside data/.
    base = root.resolve()
    probe = base / relative
    while probe != base:
        if probe.is_symlink():
            return False
        probe = probe.parent
    path = (base / relative).resolve()
    if (
        not path.is_file()
        or not path.is_relative_to(base)
        or path.is_relative_to(base / "data")
    ):
        return False
    declared = match["sha"]
    if declared in forbidden_shas or _sha(path) != declared:
        return False
    return digest_commit(root, path, declared) == match["commit"] and strictly_precedes(
        root, match["commit"], frozen
    )


def _rr14(
    definition: dict[str, str],
    reference: dict[str, Any],
    threshold: float,
    root: Path,
    forbidden_shas: frozenset[str],
) -> list[str]:
    """RR14: gates EXECUTION of the scenarios only; it upgrades no claim."""
    try:
        variants = [
            float(v) for v in definition.get("threshold_variants", "").split(";")
        ]
    except ValueError:
        variants = []
    distinct = {v for v in variants if math.isfinite(v) and v >= 0 and v != threshold}
    comparability = definition.get("comparability")
    calibrated = True
    if comparability == "cross_dataset_calibration":
        path = _inside(root, reference.get("calibration_path"))
        declared = str(reference.get("calibration_sha256") or "")
        calibrated = (
            path is not None
            and _sha(path) == declared
            and declared not in forbidden_shas
            and bool(digest_commit(root, path, declared))
        )
    if (
        comparability not in COMPARABILITY
        or not _is_citation(definition.get("comparability_evidence"))
        or not calibrated
    ):
        return [
            "RR14: no demonstrated comparability of the reference per-cell values with ADOC's"
        ]
    prereg = _inside(root, reference.get("preregistration_path"))
    digest = str(reference.get("preregistration_sha256") or "")
    frozen = digest_commit(root, prereg, digest) if prereg else ""
    method = definition.get("threshold_derivation")
    if not (
        _is_citation(method)
        or _repository_citation(method, root, frozen, forbidden_shas)
    ):
        return ["RR14: the threshold derivation is not cited"]
    if len(distinct) < 2 or len(distinct) != len(variants):
        return ["RR14: fewer than two distinct, valid threshold sensitivity variants"]
    if definition.get("variant_selection") != VARIANT_SELECTION:
        return ["RR14: every variant must be reported, none selected"]
    # The variants, threshold and comparability are PRE-registered only if the
    # pre-registration, as frozen (RR10's content-ordered commit), names the
    # exact definition bytes that carry them.
    named = str(reference.get("definition_sha256") or "")
    text = (
        _git(root, "show", f"{frozen}:{prereg.relative_to(root.resolve())}")
        if frozen
        else ""
    )
    # Exactly the chosen artifacts may be pre-registered -- the definition, and
    # the calibration when comparability rests on one. Extra candidate digests
    # would let one be chosen after ADOC was seen.
    # The binding is by FIELD, not by mention: `key: value` lines, each key at
    # most once, equal to the active reference. Extra 64-hex digests anywhere
    # would let a candidate be chosen after ADOC was seen.
    expected = {
        "definition_path": str(reference.get("definition_path") or ""),
        "definition_sha256": named,
    }
    if comparability == "cross_dataset_calibration":
        expected["calibration_path"] = str(reference.get("calibration_path") or "")
        expected["calibration_sha256"] = str(reference.get("calibration_sha256") or "")
    fields: dict[str, list[str]] = {}
    for key, value in re.findall(
        r"(?m)^\s*(definition_path|definition_sha256|calibration_path|calibration_sha256):[ \t]*(\S+)[ \t]*$",
        text,
    ):
        fields.setdefault(key, []).append(value)
    bound = {key: values[0] for key, values in fields.items() if len(values) == 1}
    tokens = re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", text)
    if (
        not frozen
        or bound != expected
        or len(bound) != len(fields)
        or sorted(tokens)
        != sorted(v for k, v in expected.items() if k.endswith("_sha256"))
    ):
        return [
            "RR14: the frozen pre-registration does not bind exactly the definition (and, when calibrated, the calibration) as path and sha256 fields, so they were not pre-registered"
        ]
    return []


def parameter_set(parameter: dict[str, Any]) -> bool:
    """A value in the parameter's domain, set by a recorded owner decision.

    The provenance vocabulary is closed: only `owner_decided` sets a value, so
    an outcome-tuned value cannot pass under a new name.
    """
    value = parameter["value"]
    return (
        parameter["provenance"] in PERMITTED_PROVENANCE
        and isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 1
    )


def parameter_failures(spec: dict[str, Any]) -> list[str]:
    """RR11: every parameter set, in its domain, by an owner decision."""
    return [
        f"RR11: parameter {name} is unset, outside its domain or has provenance {p['provenance']!r}"
        for name, p in sorted(spec["parameters"].items())
        if not parameter_set(p)
    ]


def evaluate_reference(
    reference: dict[str, Any] | None,
    *,
    node: dict[str, object],
    spec: dict[str, Any],
    forbidden_shas: frozenset[str],
    root: Path,
) -> list[str]:
    """Every unmet requirement for one eligible node; empty means usable.

    Every value the gate accepts is read from a hashed file, never from the
    manifest alone. RR11 is evaluated whether or not a reference exists, so a
    reference can never open the gate while a parameter is pending.
    """
    unset = parameter_failures(spec)
    if reference is None:
        return ["RR01: reference_strategy.reference_path is null", *unset]
    if "__unreadable__" in reference:
        return [
            f"RR01: reference manifest {reference['__unreadable__']!r} is not a file inside the repository",
            *unset,
        ]
    failures: list[str] = []
    declared_donors = [str(d) for d in reference.get("donor_ids") or []]
    condition = reference.get("condition_class")
    compartment = reference.get("compartment")

    # RR02 -- both files hashed, and their CONTENTS agree with the manifest.
    if not _is_citation(reference.get("source_accession")) or not _is_date(
        reference.get("retrieved_on")
    ):
        failures.append(
            "RR02: source_accession must be a DOI or accession and retrieved_on an ISO date"
        )
    donors = _hashed_tsv(
        root, reference.get("donors_path"), reference.get("source_sha256")
    )
    header: list[str] = []
    if donors is None:
        failures.append(
            "RR02: donors_path is not a repository file hashing to source_sha256"
        )
    else:
        header, rows = donors
        if set(DONORS_COLUMNS) - set(header):
            failures.append(
                f"RR02: donors file lacks columns {sorted(set(DONORS_COLUMNS) - set(header))}"
            )
        elif (
            sorted(r["donor_id"] for r in rows) != sorted(declared_donors)
            or len(set(declared_donors)) != len(declared_donors)
            or any(
                r["condition_class"] != condition or r["compartment"] != compartment
                for r in rows
            )
        ):
            failures.append(
                "RR02: donors file rows disagree with donor_ids, condition_class or compartment"
            )
        elif not all(_positive_int(r["n_cells"]) for r in rows):
            failures.append(
                "RR02: every reference donor needs a positive integer n_cells"
            )
    definition_file = _hashed_tsv(
        root, reference.get("definition_path"), reference.get("definition_sha256")
    )
    definition: dict[str, str] = {}
    definition_header: list[str] = []
    if definition_file is None or len(definition_file[1]) != 1:
        failures.append(
            "RR02: definition_path is not a one-row repository file hashing to definition_sha256"
        )
    else:
        definition_header, (definition,) = definition_file[0], definition_file[1]

    # RR03 -- independence from ADOC.
    file_donors = [r.get("donor_id", "") for r in donors[1]] if donors else []
    if any(is_adoc_donor(d) for d in [*declared_donors, *file_donors]):
        failures.append("RR03: reference donors overlap the ADOC donors")
    cited = [reference.get("source_accession")]
    if definition_file:
        cited += [row.get(f) for row in definition_file[1] for f in CITATION_FIELDS]
    if any(is_adoc_citation(c) for c in cited):
        failures.append(
            "RR03: the ADOC accession is cited as the reference or its evidence"
        )
    if {
        reference.get("source_sha256"),
        reference.get("definition_sha256"),
    } & forbidden_shas:
        failures.append("RR03: a reference file is an ADOC object")
    if reference.get("derived_from_adoc") is not False:
        failures.append("RR03: derived_from_adoc must be declared false")

    if definition:
        # RR04 -- assay, layer, quantity.
        if (
            reference.get("assay") not in ASSAYS
            or definition.get("layer") != ADOC_LAYER
            or definition.get("per_cell_quantity") not in PER_CELL_QUANTITIES
        ):
            failures.append(
                "RR04: assay, layer or per-cell quantity is not applicable to the ADOC per-cell values"
            )
        # RR06 -- feature.
        if [definition.get("feature")] != str(node["source_gene_or_signature"]).split(
            ";"
        ):
            failures.append("RR06: the definition is not on the node's own feature")
        # RR07 -- rule, threshold, donors as the unit.
        try:
            threshold = float(definition.get("threshold", "nan"))
        except ValueError:
            threshold = math.nan
        minimum = spec["parameters"]["min_reference_donors"]["value"]
        if (
            definition.get("rule") not in RULES
            or not math.isfinite(threshold)
            or threshold < 0
            or reference.get("aggregation_unit") != "donor"
        ):
            failures.append("RR07: rule, threshold or aggregation unit is invalid")
        elif (
            parameter_set(spec["parameters"]["min_reference_donors"])
            and len(declared_donors) < minimum
        ):
            failures.append("RR07: fewer reference donors than min_reference_donors")
        # RR14 -- comparability, threshold derivation, sensitivity variants.
        failures.extend(_rr14(definition, reference, threshold, root, forbidden_shas))
        # RR12 -- the definition's evidence, and the owner's acceptance of it.
        if (
            not _is_citation(definition.get("evidence_citation"))
            or definition.get("evidence_kind") not in EVIDENCE_KINDS
            or not _is_date(definition.get("owner_accepted_on"))
            or not _not_before(
                definition.get("owner_accepted_on"), reference.get("retrieved_on")
            )
        ):
            failures.append(
                "RR12: the definition carries no citation, no admissible evidence kind, or no owner acceptance"
            )
    # RR05 -- compartment.
    if compartment != node["scrna_compartment"]:
        failures.append(
            f"RR05: reference compartment {compartment!r} != {node['scrna_compartment']!r}"
        )
    # RR08 -- condition class.
    if condition not in RESOLVED_CONDITION_CLASSES:
        failures.append(
            "RR08: reference condition class is not a resolved ADOC condition class"
        )
    # RR09 -- outcome blindness, checked on both files themselves.
    extra = [c for c in header if c not in DONORS_COLUMNS] + [
        c for c in definition_header if c not in DEFINITION_COLUMNS
    ]
    if reference.get("outcome_blind") is not True or extra:
        failures.append(
            f"RR09: outcome_blind must be true and no file may carry a column beyond its schema {extra}"
        )
    # RR10 -- a committed pre-registration, by content hash, committed strictly
    # before every commit that selects or activates the reference: the one that
    # first adds each reference file, and the one whose personalization.yaml
    # first names the manifest.
    prereg = _inside(root, reference.get("preregistration_path"))
    digest = str(reference.get("preregistration_sha256") or "")
    selected = [
        _inside(root, reference.get(key))
        for key in ("__path__", "donors_path", "definition_path")
    ]
    later = [first_commit(root, p) if p else "" for p in selected]
    later.append(activation_commit(root, str(reference.get("__path__", ""))))
    frozen = digest_commit(root, prereg, digest) if prereg else ""
    if (
        prereg is None
        or len(digest) != 64
        or any(c not in "0123456789abcdef" for c in digest)
        or _sha(prereg) != digest
        or not all(strictly_precedes(root, frozen, commit) for commit in later)
    ):
        failures.append(
            "RR10: no pre-registration matching preregistration_sha256 committed strictly before the reference files and its activation in personalization.yaml"
        )
    return failures + unset


def evaluate_bridge_validation(
    reference: dict[str, Any] | None,
    *,
    root: Path,
    forbidden_shas: frozenset[str] | None = None,
) -> list[str]:
    """RR13, the only route from a scenario to a measured-personalization claim."""
    if reference is None or "__unreadable__" in reference:
        return ["RR13: no bridge-validation artifact (no reference)"]
    table = _hashed_tsv(
        root,
        reference.get("bridge_validation_path"),
        reference.get("bridge_validation_sha256"),
    )
    if (
        table is None
        or len(table[1]) != 1
        or list(table[0]) != list(BRIDGE_VALIDATION_COLUMNS)
    ):
        return [
            "RR13: bridge_validation_path is not a one-row, schema-exact repository file hashing to bridge_validation_sha256"
        ]
    (row,) = table[1]
    path = _inside(root, reference.get("bridge_validation_path"))
    declared = str(reference.get("bridge_validation_sha256") or "")
    forbidden = (
        forbidden_reference_shas(REPO) if forbidden_shas is None else forbidden_shas
    )
    if (
        declared in forbidden
        or is_adoc_citation(row["evidence_citation"])
        or not digest_commit(root, path, declared)
    ):
        return [
            "RR13: the bridge validation is an ADOC object, cites the ADOC accession, or its declared content was never committed"
        ]
    if (
        " ".join(row["bridge_statement"].split()) != BRIDGE_ASSUMPTION
        or not _is_citation(row["evidence_citation"])
        or row["evidence_kind"] not in BRIDGE_EVIDENCE_KINDS
        or row["independent_of_adoc"] != "true"
        or not _is_date(row["owner_accepted_on"])
    ):
        return [
            "RR13: the bridge validation is not the pre-registered bridge, not independent, not evidenced, not owner-accepted or not committed"
        ]
    return []


def reference_gate(
    root: Path, mapping: list[dict[str, object]], spec: dict[str, Any]
) -> dict[str, Any]:
    policy = yaml.safe_load((root / PERSONALIZATION).read_text(encoding="utf-8"))
    strategy = policy["reference_strategy"]
    if strategy["mode"] != "external_reference_required":
        raise Phase2AError(
            f"reference mode {strategy['mode']!r} is not external_reference_required"
        )
    reference = load_reference_manifest(root, policy)
    forbidden = forbidden_reference_shas(root)
    per_node = {}
    for node in mapping:
        if node["structural_eligibility"] == ELIGIBLE:
            per_node[str(node["model_node"])] = evaluate_reference(
                reference, node=node, spec=spec, forbidden_shas=forbidden, root=root
            )
    ready = [n for n, failures in per_node.items() if not failures]
    measured = {
        n: failures
        + evaluate_bridge_validation(reference, root=root, forbidden_shas=forbidden)
        for n, failures in per_node.items()
    }
    measured_ready = [n for n, failures in measured.items() if not failures]
    return {
        "schema_version": SCHEMA_VERSION,
        "rule": "READY_FOR_MAPPING (of assumption-conditioned scenario values only) iff at least one structurally eligible node has zero unmet RR01-RR12 and RR14 requirements; otherwise BLOCKED_REFERENCE_REQUIRED",
        "policy_source": str(PERSONALIZATION),
        "policy_mode": strategy["mode"],
        "policy_reference_path": strategy.get("reference_path"),
        "verdict": "READY_FOR_MAPPING" if ready else "BLOCKED_REFERENCE_REQUIRED",
        "eligible_nodes": sorted(per_node),
        "ready_nodes": ready,
        "unmet_requirements": per_node,
        "claim_level_if_ready": CLAIM_LEVEL,
        "measured_personalization_rule": "READY_FOR_MEASURED_PERSONALIZATION iff a node meets every applicable requirement of RR01-RR14 (the ordinary reference gate, RR14 included) AND RR13, the bridge-validation requirement that alone can upgrade the claim; otherwise BLOCKED_BRIDGE_UNVALIDATED",
        "measured_personalization_verdict": "READY_FOR_MEASURED_PERSONALIZATION"
        if measured_ready
        else "BLOCKED_BRIDGE_UNVALIDATED",
        "measured_unmet_requirements": measured,
        "adoc_donors_forbidden_as_reference": list(C.DONORS),
        "forbidden_reference_sha256": sorted(forbidden),
    }


# --------------------------------------------------------------------------
# Step 6 -- provenance contract and status
# --------------------------------------------------------------------------

PROVENANCE_COLUMNS = ("stage", "lineage_stage", "artifact", "identity", "rule")


def provenance_rows(root: Path, gate: dict[str, Any]) -> list[dict[str, str]]:
    sha = manifest_sha(root)
    active = gate["policy_reference_path"]
    reference_identity = (
        "reference_path null"
        if active is None
        else f"{active} sha256 {_sha(root / active) if _inside(root, active) else 'unreadable'}; verdict {gate['verdict']}"
    )
    return [
        {
            "stage": "1_scrna_source",
            "lineage_stage": "source",
            "artifact": f"{EXTERNAL_MANIFEST}:{ASSET_ID}",
            "identity": f"sha256 {sha}",
            "rule": "the object is fetched on demand and never committed; every derived value names this hash",
        },
        {
            "stage": "2_donor_sample",
            "lineage_stage": "audited",
            "artifact": str(OUT_GRAIN),
            "identity": f"{EXTRACTION} sha256 {_sha(root / EXTRACTION)}",
            "rule": "donor and condition are parsed from sample_id, the only field that carries them; the donor is the independent unit",
        },
        {
            "stage": "3_compartment",
            "lineage_stage": "audited",
            "artifact": "dt_adoc.scrna.node_support_contract.COMPARTMENT_OF_LABEL",
            "identity": "frozen in the node-support pre-registration",
            "rule": "celltype_v2 -> epithelium/stroma/myofibroblast; only epithelium and stroma are primary",
        },
        {
            "stage": "4_feature",
            "lineage_stage": "model_mapping",
            "artifact": str(OBSERVATION_MAP),
            "identity": f"sha256 {_sha(root / OBSERVATION_MAP)}",
            "rule": "the frozen measurement_features only; absent features are recorded, never aliased",
        },
        {
            "stage": "5_aggregation",
            "lineage_stage": "analysis_ready",
            "artifact": str(NODE_SUPPORT_EVIDENCE),
            "identity": f"sha256 {_sha(root / NODE_SUPPORT_EVIDENCE)}",
            "rule": "donor x condition x compartment pseudobulk f and detection d with within-donor bootstrap intervals; cells are never replicates",
        },
        {
            "stage": "6_external_reference",
            "lineage_stage": "model_mapping",
            "artifact": str(OUT_GATE),
            "identity": reference_identity,
            "rule": "RR01-RR12 and RR14; the ADOC donors can never define the high state",
        },
        {
            "stage": "7_transform",
            "lineage_stage": "model_mapping",
            "artifact": str(OUT_SPEC),
            "identity": "three-step bridge of docs/scrna/klf12_prior_preregistration.md",
            "rule": "external per-cell high-state definition -> fraction of the unit's cells in that state -> initial probability under the declared ensemble-frequency bridge; a 0 or 1 is unresolved, never written",
        },
        {
            "stage": "8_initial_probability",
            "lineage_stage": "model",
            "artifact": "none written by Phase 2A",
            "identity": "-",
            "rule": "a later unit writes `<node>.istate` only, on a shared v0.5.1 topology, and records every value's stage 1-7 identities",
        },
        {
            "stage": "leakage_outcomes",
            "lineage_stage": "claim",
            "artifact": str(OUT_SPEC),
            "identity": "outcome_independence",
            "rule": "no outcome label (adhesion, pregnancy, secretion, model output) selects a reference, statistic or threshold",
        },
        {
            "stage": "leakage_topology",
            "lineage_stage": "model",
            "artifact": str(NETWORK),
            "identity": f"sha256 {_sha(root / NETWORK)}",
            "rule": "one topology shared by every donor; Phase 2A writes no .bnd or .cfg",
        },
        {
            "stage": "leakage_reuse",
            "lineage_stage": "claim",
            "artifact": str(OUT_MAP),
            "identity": "leakage_flags",
            "rule": "a feature used to personalize a donor cannot later be cited as independent validation of that donor's model on the same feature without a declared validation design",
        },
    ]


def forbidden_emission(texts: dict[Path, str]) -> list[str]:
    """Any output that is a model file or names a forbidden layer as a field."""
    problems = []
    for path, text in texts.items():
        if path.suffix in (".bnd", ".cfg"):
            problems.append(f"{path} is a model file")
        header = text.splitlines()[0] if path.suffix == ".tsv" else ""
        fields = (
            header.split("\t")
            if header
            else _json_keys(text)
            if path.suffix == ".json"
            else []
        )
        for field in fields:
            if any(bad in field for bad in FORBIDDEN_OUTPUT_FIELDS):
                problems.append(f"{path} has forbidden field {field!r}")
    return problems


def _json_keys(text: str) -> list[str]:
    keys: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, inner in value.items():
                keys.append(str(key))
                walk(inner)
        elif isinstance(value, list):
            for inner in value:
                walk(inner)

    walk(json.loads(text))
    return keys


def status(
    root: Path,
    *,
    grain: list[dict[str, object]],
    mapping: list[dict[str, object]],
    summaries: list[dict[str, object]],
    gate: dict[str, Any],
    spec: dict[str, Any],
    emitted: dict[Path, str],
) -> dict[str, Any]:
    extraction = _json(root / EXTRACTION)
    phase1b = _json(root / PHASE1B_SUMMARY)["lineage"]
    frozen_ok = all(
        _sha(root / p) == d for p, d in phase1b["frozen_stage3_sha256"].items()
    )
    models_tree = _tree_sha(root, Path("models"))
    units = [g for g in grain if g["level"] == "compartment_unit"]
    eligible = [m for m in mapping if m["structural_eligibility"] == ELIGIBLE]
    expected_summaries = len(eligible) * len(C.DONORS) * len(C.CONDITIONS)
    # G6: every parameter is either still the owner's to set (null, pending) or
    # set with a provenance that is neither pending nor forbidden. A value with
    # no recorded decision, or a fitted one, would be a choice this unit made.
    forbidden = set(spec["parameter_provenance_forbidden"])
    parameters_owner_controlled = all(
        (v["value"] is None and v["provenance"] == PENDING)
        or (parameter_set(v) and v["provenance"] not in forbidden)
        for v in spec["parameters"].values()
    )
    gates = {
        "G1_source_identity_pinned": extraction["rds_sha256"] == manifest_sha(root),
        "G2_grain_accounted": len(units) == 18
        and sum(int(u["n_cells"]) for u in units) == verify_rds.EXPECTED_CELLS
        and all(u["n_cells"] == u["node_support_unit_n_cells"] for u in units),
        "G3_one_row_per_v051_node": len(mapping) == len(model_nodes(root)),
        "G4_summaries_for_every_eligible_unit": len(summaries) == expected_summaries,
        "G5_reference_gate": gate["verdict"],
        "G6_spec_parameters_owner_controlled": parameters_owner_controlled,
        "G7_models_and_frozen_artifacts_unchanged": models_tree
        == phase1b["models_tree_sha256"]
        and frozen_ok,
        "G8_no_forbidden_emission": not forbidden_emission(emitted),
    }
    structural = all(v is True for k, v in gates.items() if k != "G5_reference_gate")
    if not structural:
        raise Phase2AError(f"a structural gate failed: {gates}")
    counts = {
        e: sum(m["mapping_eligibility"] == e for m in mapping) for e in ELIGIBILITY
    }
    structural_counts = {
        e: sum(m["structural_eligibility"] == e for m in mapping) for e in ELIGIBILITY
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "adopted_model": ADOPTED_VERSION,
        "status": "STRUCTURAL_MAPPING_READY_BUT_REFERENCE_BLOCKED"
        if gate["verdict"] != "READY_FOR_MAPPING"
        else "STRUCTURAL_MAPPING_READY_REFERENCE_AVAILABLE",
        "rule": "G1-G4 and G6-G8 must all hold or nothing is written; the status then follows G5 alone",
        "phase2_complete": False,
        "numerical_personalization": "BLOCKED"
        if gate["verdict"] != "READY_FOR_MAPPING"
        else "NOT_RUN_BY_PHASE_2A",
        "claim_level": CLAIM_LEVEL,
        "measured_personalization": "BLOCKED"
        if gate["measured_personalization_verdict"]
        != "READY_FOR_MEASURED_PERSONALIZATION"
        else "NOT_RUN_BY_PHASE_2A",
        "gates": gates,
        "mapping_eligibility_counts": counts,
        "structural_eligibility_counts": structural_counts,
        "owner_decisions_applied": {
            "Q1": "only free variables are eligible for an initial probability",
            "Q2": "E_KLF12_HIGH eligible pending an external reference; the closed prior finding is not reopened",
            "Q3": "config/personalization.yaml unchanged; only the initial-probability layer is permitted here",
            "Q4": "CNT condition class unresolved (composition unrecorded)",
            "B1": "the pre-registered three-step bridge replaces a rank transform: external per-cell high-state definition, unit fraction of high cells, that fraction as the initial probability",
            "B1_claim": "every value is an assumption_conditioned_scenario carrying the bridge assumption; RR13 (independent evidence-backed calibration/validation of fraction-high -> initial ensemble frequency, owner-accepted before the claim is upgraded) is the only route to measured personalization",
            "B13": "RR14 (comparability, cited threshold derivation, at least two pre-registered threshold variants, all reported, none selected by ADOC outcomes) gates execution of the scenarios only; it does not satisfy RR13 or upgrade the claim",
            "RR12_vocabulary": "published_per_cell_definition and reference_state_separation are accepted as a Phase-2A-local controlled vocabulary; they do not replace or modify the repository-wide evidence-schema vocabularies",
            "D2_min_reference_donors": "min_reference_donors = 3 (owner, 2026-09-25, before any candidate reference value was read): a minimum for assumption-conditioned scenario generation only, not a claim of population adequacy; the donors must be identifiable independent biological donors, and clones or technical replicates do not count",
            "boundary_rule": "for E_KLF12_HIGH a mapped point estimate or uncertainty bound of exactly 0 or 1 stays unresolved and is not written, because the self-loop node would otherwise be functionally hard-clamped; a conservative personalization-interface rule, not evidence that the biological state cannot be all-low or all-high",
        },
        "owner_decisions_open": [
            "which external population and per-cell high-state definition qualify biologically (tissue vs organoid, cycle phase, hormone exposure)",
            "CNT arm composition, from the depositors",
        ],
        "lineage": {
            "rds_sha256": extraction["rds_sha256"],
            "extraction_sha256": _sha(root / EXTRACTION),
            "node_support_findings_sha256": _sha(root / NODE_SUPPORT_FINDINGS),
            "node_support_evidence_sha256": _sha(root / NODE_SUPPORT_EVIDENCE),
            "node_support_qc_sha256": _sha(root / NODE_SUPPORT_QC),
            "observation_map_sha256": _sha(root / OBSERVATION_MAP),
            "personalization_yaml_sha256": _sha(root / PERSONALIZATION),
            "network_bnd_sha256": _sha(root / NETWORK),
            "baseline_cfg_sha256": _sha(root / BASELINE_CFG),
            "models_tree_sha256": models_tree,
            "frozen_stage3_sha256": phase1b["frozen_stage3_sha256"],
        },
    }


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _render_tsv(columns: tuple[str, ...], rows: list[dict[str, object]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=columns, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row[k] for k in columns})
    return buffer.getvalue()


def _render_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def compute(root: Path = REPO) -> dict[Path, str]:
    extraction = _json(root / EXTRACTION)
    if _json(root / NODE_SUPPORT_FINDINGS)["layer"] != ADOC_LAYER:
        raise Phase2AError("the node-support layer is not the one RR04 names")
    grain = grain_rows(extraction, root)
    spec = mapping_specification()
    structural_map = map_rows(root, reference_ready=False)
    gate = reference_gate(root, structural_map, spec)
    mapping = map_rows(root, reference_ready=gate["verdict"] == "READY_FOR_MAPPING")
    summaries = summary_rows(root, mapping)
    outputs = {
        OUT_GRAIN: _render_tsv(GRAIN_COLUMNS, grain),
        OUT_MAP: _render_tsv(MAP_COLUMNS, mapping),
        OUT_SUMMARIES: _render_tsv(SUMMARY_COLUMNS, summaries),
        OUT_REQUIREMENTS: _render_tsv(
            ("req_id", "field", "requirement", "why"), list(REFERENCE_REQUIREMENTS)
        ),
        OUT_GATE: _render_json(gate),
        OUT_SPEC: _render_json(spec),
        OUT_PROVENANCE: _render_tsv(PROVENANCE_COLUMNS, provenance_rows(root, gate)),
    }
    outputs[OUT_STATUS] = _render_json(
        status(
            root,
            grain=grain,
            mapping=mapping,
            summaries=summaries,
            gate=gate,
            spec=spec,
            emitted=dict(outputs),
        )
    )
    return {p: outputs[p] for p in OUTPUTS}


def build(root: Path | None = None) -> tuple[Path, ...]:
    active = root or REPO
    outputs = compute(active)
    (active / OUT_DIR).mkdir(parents=True, exist_ok=True)
    for relative, text in outputs.items():
        (active / relative).write_text(text, encoding="utf-8")
    return tuple(active / p for p in OUTPUTS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--rds", type=Path, help="local copy of seurat_object.rds; re-extract meta.data"
    )
    parser.add_argument("--rscript", default="Rscript")
    args = parser.parse_args(argv)
    if args.rds is not None:
        print(f"wrote {extract(args.rds, rscript=args.rscript)}")
    for written in build():
        print(f"wrote {written}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
