"""Generate the Phase 1D literature-superset model family artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import platform
import re
import shutil
import subprocess
import sys
from collections import OrderedDict
from collections.abc import Iterable
from pathlib import Path

import tomllib

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.topology import (
    TOPOLOGY_COLUMNS,
    load_adjudications,
    parse_bnd_rules,
    reconcile,
)

ROOT = repo_root()
#: The version this generator emits. v0.3.0 is frozen as an immutable parent and
#: its committed artifacts are no longer reproduced from here; changing this
#: constant is the only supported way to retarget the generator.
MODEL_VERSION = "adoc-literature-superset-v0.4.0"
MODEL_KEY = "adoc_literature_superset_v040"
SUPERTSET_DIR = ROOT / "models" / "superset" / MODEL_VERSION
CONDITIONS_DIR = SUPERTSET_DIR / "conditions"
EXTENDED_DIR = ROOT / "models" / "extended" / "adoc-literature-v0.2.0"
BASELINE_DIR = ROOT / "models" / "baseline" / "adoc-core-v0.1.0"
PARENT_MODEL_VERSION = "adoc-literature-superset-v0.3.0"
SOURCE_FILES = {
    "candidate_nodes": ROOT / "context" / "literature" / "candidate-nodes.tsv",
    "candidate_edges": ROOT / "context" / "literature" / "candidate-edges.tsv",
    "mechanisms": ROOT / "context" / "literature" / "mechanisms.tsv",
    "evidence_register": ROOT / "context" / "evidence-register.tsv",
    "parent_network": EXTENDED_DIR / "network.bnd",
    "parent_baseline_cfg": EXTENDED_DIR / "baseline.cfg",
    "parent_node_dictionary": EXTENDED_DIR / "node_dictionary.tsv",
    "parent_edge_evidence": EXTENDED_DIR / "edge_evidence.tsv",
    "parent_phenotype_contract": EXTENDED_DIR / "phenotype_contract.tsv",
    "parent_provenance": EXTENDED_DIR / "provenance.toml",
    "topology_adjudications": ROOT / "config" / "topology_parity_exemptions.tsv",
}

NEW_NODE_ROWS = {
    "IN_HAND2_LOSS": {
        "node_id": "IN_HAND2_LOSS",
        "label": "Stromal HAND2 loss-of-function input",
        "compartment": "stroma_external",
        "species": "mouse_plus_human_support",
        "baseline_mapping": "new",
        "state_0_meaning": "Stromal HAND2 intact",
        "state_1_meaning": "Stromal HAND2 ablated",
        "measurement_proxies": "experimental schedule",
        "model_role": "perturbation_input",
        "evidence_ids": "LIT-IHH-001",
        "reference_ids": "REF-028;REF-062",
        "confidence": "medium",
        "uncertainty_or_alternative_interpretation": (
            "Direction only. The magnitude of the epithelial collapse is a hard "
            "Boolean consequence of a veto that has no held-out measurement "
            "behind it, so this must never be read as a calibrated effect size."
        ),
        "notes": (
            "Boundary perturbation input, OFF in every default condition, so the "
            "declared suite is bit-identical to the immutable v0.3.0 parent. "
            "Encodes the loss-of-function layer at which the evidence actually "
            "acted: Hand2-flox x PR-Cre conditional knockout in mouse (REF-028) "
            "and two independent siHAND2 duplexes in human stroma (REF-062). "
            "It adds no activation claim; the (S_BMP2 or S_PGR) ON route is "
            "preserved verbatim so REF-028's finding that HAND2 is "
            "progesterone-induced remains encoded unchanged."
        ),
    },
    "E_KLF12_HIGH": {
        "node_id": "E_KLF12_HIGH",
        "label": "High epithelial KLF12",
        "compartment": "epithelium",
        "species": "human",
        "baseline_mapping": "new",
        "state_0_meaning": "High KLF12 context absent",
        "state_1_meaning": "High KLF12 context present",
        "measurement_proxies": "KLF12 expression",
        "model_role": "anti_receptive_context",
        "evidence_ids": "LIT-LIF-001",
        "reference_ids": "REF-037",
        "confidence": "medium",
        "uncertainty_or_alternative_interpretation": (
            "Context-specific inhibitory state kept OFF in the default condition suite"
        ),
        "notes": (
            "Recurrent-implantation-failure-associated inhibitor retained as an "
            "optional contextual input rather than a default active program."
        ),
    },
    "S_FGF_MITOGENIC": {
        "node_id": "S_FGF_MITOGENIC",
        "label": "Stromal mitogenic FGF output",
        "compartment": "stroma",
        "species": "mouse_plus_human_support",
        "baseline_mapping": "new",
        "state_0_meaning": "Mitogenic stromal FGF output low",
        "state_1_meaning": "Mitogenic stromal FGF output active",
        "measurement_proxies": "FGF family expression or secretion",
        "model_role": "paracrine_inhibitor_of_receptivity",
        "evidence_ids": "LIT-IHH-001",
        "reference_ids": "REF-028",
        "confidence": "medium",
        "uncertainty_or_alternative_interpretation": (
            "Family-level collapse is retained without choosing one dominant FGF"
        ),
        "notes": (
            "Implements the HAND2-sensitive stromal mitogenic restraint described in "
            "the literature candidate table."
        ),
    },
    "E_ESTROGENIC_PROLIFERATION": {
        "node_id": "E_ESTROGENIC_PROLIFERATION",
        "label": "Epithelial estrogenic proliferation",
        "compartment": "epithelium",
        "species": "mouse_plus_human_support",
        "baseline_mapping": "new",
        "state_0_meaning": "Persistent estrogenic epithelial proliferation absent",
        "state_1_meaning": "Persistent estrogenic epithelial proliferation present",
        "measurement_proxies": "Ki67 or ESR target program",
        "model_role": "anti_receptive_state",
        "evidence_ids": "LIT-IHH-001",
        "reference_ids": "REF-025;REF-026;REF-028",
        "confidence": "medium",
        "uncertainty_or_alternative_interpretation": (
            "Collapsed anti-receptive state rather than a calibrated cell-cycle model"
        ),
        "notes": (
            "Represents persistent proliferative nonreceptivity when stromal HAND2 "
            "fails to restrain the estrogenic relay."
        ),
    },
}

NEW_EXECUTABLE_EDGES = [
    {
        "edge_id": "LE096",
        "source": "IN_HAND2_LOSS",
        "target": "S_HAND2",
        "sign": "inhibition",
        "evidence_id": "LIT-IHH-001",
        "confidence": "candidate",
        "variant_id": MODEL_KEY,
        "notes": (
            "Loss-of-function boundary input matching the mouse conditional "
            "knockout and the human siRNA; OFF by default."
        ),
    },
    {
        "edge_id": "LE091",
        "source": "E_KLF12_HIGH",
        "target": "E_LIF",
        "sign": "inhibition",
        "evidence_id": "LIT-LIF-001",
        "confidence": "candidate",
        "variant_id": MODEL_KEY,
        "notes": "Contextual KLF12-high state restrains the epithelial LIF gate.",
    },
    {
        "edge_id": "LE092",
        "source": "S_HAND2",
        "target": "S_FGF_MITOGENIC",
        "sign": "inhibition",
        "evidence_id": "LIT-IHH-001",
        "confidence": "candidate",
        "variant_id": MODEL_KEY,
        "notes": "HAND2 restrains mitogenic stromal FGF output in the expansion branch.",
    },
    {
        "edge_id": "LE093",
        "source": "S_FGF_MITOGENIC",
        "target": "E_ESTROGENIC_PROLIFERATION",
        "sign": "activation",
        "evidence_id": "LIT-IHH-001",
        "confidence": "candidate",
        "variant_id": MODEL_KEY,
        "notes": "Stromal mitogenic relay supports persistent epithelial proliferation.",
    },
    {
        "edge_id": "LE094",
        "source": "S_HAND2",
        "target": "E_ESTROGENIC_PROLIFERATION",
        "sign": "inhibition",
        "evidence_id": "LIT-IHH-001",
        "confidence": "candidate",
        "variant_id": MODEL_KEY,
        "notes": "HAND2 directly suppresses the anti-receptive epithelial proliferation branch.",
    },
    {
        "edge_id": "LE095",
        "source": "E_ESTROGENIC_PROLIFERATION",
        "target": "E_RECEPTIVE_SURFACE",
        "sign": "inhibition",
        "evidence_id": "LIT-IHH-001",
        "confidence": "candidate",
        "variant_id": MODEL_KEY,
        "notes": "Persistent epithelial proliferation opposes the receptive surface.",
    },
]

RULE_VARIANTS = [
    {
        "variant_id": "literature_parity_v020",
        "node_id": "E_LIF",
        "expression": "E_SECRETORY_STATE",
        "status": "reference_only",
        "default_in_family": "false",
        "source_table": "models/extended/adoc-literature-v0.2.0/network.bnd",
        "source_row_id": "E_LIF",
        "evidence_ids": "LIT-LIF-001",
        "notes": "Current literature executable starting point before the KLF12 context input.",
    },
    {
        "variant_id": MODEL_KEY,
        "node_id": "E_LIF",
        "expression": "E_SECRETORY_STATE and not E_KLF12_HIGH",
        "status": "default_executable",
        "default_in_family": "true",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "E_LIF",
        "evidence_ids": "LIT-LIF-001",
        "notes": "Uses the explicit candidate-node logic hint without forcing the context active in the default suite.",
    },
    {
        "variant_id": MODEL_KEY,
        "node_id": "S_FGF_MITOGENIC",
        "expression": "not S_HAND2",
        "status": "default_executable",
        "default_in_family": "true",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "S_FGF_MITOGENIC",
        "evidence_ids": "LIT-IHH-001",
        "notes": "Direct transcriptional inhibition branch from the candidate-node logic hint.",
    },
    {
        "variant_id": MODEL_KEY,
        "node_id": "E_ESTROGENIC_PROLIFERATION",
        "expression": "IN_E2 and S_FGF_MITOGENIC and not S_HAND2",
        "status": "default_executable",
        "default_in_family": "true",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "E_ESTROGENIC_PROLIFERATION",
        "evidence_ids": "LIT-IHH-001",
        "notes": "Implements the explicit candidate-node logic hint for persistent anti-receptive proliferation.",
    },
    {
        "variant_id": MODEL_KEY,
        "node_id": "E_RECEPTIVE_SURFACE",
        "expression": (
            "E_GP130_STAT3 and not E_PODXL and not E_DAG1_FULL and "
            "not E_MUC1_BARRIER and not E_ESTROGENIC_PROLIFERATION and "
            "(E_CD98_CD9 or E_CDH1_APICAL or E_ANXA2_ACTIN or E_HBEGF or "
            "E_DAG1_CLEAVED or E_MUC1_SLEX or E_ITGAVB3_5 or X_SPP1_LUMEN_FREE)"
        ),
        "status": "default_executable",
        "default_in_family": "true",
        "source_table": "context/literature/candidate-edges.tsv",
        "source_row_id": "EDGE-015",
        "evidence_ids": "LIT-IHH-001;LIT-LIF-001;LIT-BARRIER-001",
        "notes": "Adds the anti-receptive proliferation penalty without changing the existing positive routes.",
    },
    {
        "variant_id": "hand2_required_decidual_variant",
        "node_id": "S_DECIDUALIZED",
        "expression": "S_PGR and S_PKA and S_BMP2 and S_HAND2",
        "status": "catalog_only",
        "default_in_family": "false",
        "source_table": "models/extended/adoc-literature-v0.2.0/uncertainty_notes.md",
        "source_row_id": "stricter_hand2_variant",
        "evidence_ids": "LIT-IHH-001",
        "notes": "Documented uncertainty variant retained in the catalog only; not promoted into the default executable superset.",
    },
]

UNRESOLVED_ROWS = [
    {
        "mechanism_id": "UNR-001",
        "kind": "node",
        "module_id": "MOD-02",
        "node_or_edge_id": "S_STAT3",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "S_STAT3",
        "reason": "No bounded upstream maternal cue is specified in the current candidate-edge table.",
        "disposition": "catalog_only",
        "blocking_detail": "Upstream epithelial or stromal IL6-family logic remains unspecified.",
        "notes": "Retained for provenance only.",
    },
    {
        "mechanism_id": "UNR-002",
        "kind": "node",
        "module_id": "MOD-08",
        "node_or_edge_id": "S_DECIDUAL_SENESCENCE_BALANCED",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "S_DECIDUAL_SENESCENCE_BALANCED",
        "reason": "The countervailing persistence or pathology gate is not defined without inventing logic.",
        "disposition": "catalog_only",
        "blocking_detail": "Node logic hint requires an unspecified pathological-persistence term.",
        "notes": "Avoids reducing dynamic decidual senescence to a simplistic Boolean surrogate.",
    },
    {
        "mechanism_id": "UNR-003",
        "kind": "edge",
        "module_id": "MOD-08",
        "node_or_edge_id": "EDGE-041",
        "source_table": "context/literature/candidate-edges.tsv",
        "source_row_id": "EDGE-041",
        "reason": "Target node is unresolved and remains unparameterized.",
        "disposition": "catalog_only",
        "blocking_detail": "Cannot route dynamic matrix contribution without the balanced-senescence state.",
        "notes": "Kept explicit instead of silently dropped.",
    },
    {
        "mechanism_id": "UNR-004",
        "kind": "node",
        "module_id": "MOD-10",
        "node_or_edge_id": "X_LGALS1_3",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "X_LGALS1_3",
        "reason": "No bounded upstream maternal rule is specified.",
        "disposition": "catalog_only",
        "blocking_detail": "Would require inventing a receptive-interface activation rule.",
        "notes": "Computational interface candidate only.",
    },
    {
        "mechanism_id": "UNR-005",
        "kind": "node",
        "module_id": "MOD-10",
        "node_or_edge_id": "X_BSG_ITGB1",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "X_BSG_ITGB1",
        "reason": "No bounded upstream maternal rule is specified.",
        "disposition": "catalog_only",
        "blocking_detail": "Would require inventing a receptive-interface activation rule.",
        "notes": "Computational interface candidate only.",
    },
    {
        "mechanism_id": "UNR-006",
        "kind": "edge",
        "module_id": "MOD-10",
        "node_or_edge_id": "EDGE-049",
        "source_table": "context/literature/candidate-edges.tsv",
        "source_row_id": "EDGE-049",
        "reason": "Source node remains catalog-only.",
        "disposition": "catalog_only",
        "blocking_detail": "LGALS interface branch is not bounded well enough for executable use.",
        "notes": "Non-executable candidate edge retained in the superset catalog.",
    },
    {
        "mechanism_id": "UNR-007",
        "kind": "edge",
        "module_id": "MOD-10",
        "node_or_edge_id": "EDGE-050",
        "source_table": "context/literature/candidate-edges.tsv",
        "source_row_id": "EDGE-050",
        "reason": "Source node remains catalog-only.",
        "disposition": "catalog_only",
        "blocking_detail": "BSG-ITGB1 branch is not bounded well enough for executable use.",
        "notes": "Non-executable candidate edge retained in the superset catalog.",
    },
    {
        "mechanism_id": "UNR-008",
        "kind": "node",
        "module_id": "MOD-12",
        "node_or_edge_id": "IN_UTERINE_WNT_CUE",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "IN_UTERINE_WNT_CUE",
        "reason": "Embryo-side execution remains external to the maternal-only MaBoSS network.",
        "disposition": "external_only",
        "blocking_detail": "Would otherwise internalize trophoblast competence logic that this model does not implement.",
        "notes": "Retained in the interface contract and unresolved catalog only.",
    },
    {
        "mechanism_id": "UNR-009",
        "kind": "edge",
        "module_id": "MOD-12",
        "node_or_edge_id": "EDGE-048",
        "source_table": "context/literature/candidate-edges.tsv",
        "source_row_id": "EDGE-048",
        "reason": "Edge crosses into an explicitly external embryo-competence gate.",
        "disposition": "external_only",
        "blocking_detail": "Embryo execution remains outside the executable maternal network.",
        "notes": "Documented in the interface contract rather than silently executable.",
    },
    {
        "mechanism_id": "UNR-010",
        "kind": "edge",
        "module_id": "MOD-02",
        "node_or_edge_id": "EDGE-007",
        "source_table": "context/literature/candidate-edges.tsv",
        "source_row_id": "EDGE-007",
        "reason": "Current literature inventory does not provide a bounded direct LIF-to-ANXA2 rule.",
        "disposition": "catalog_only",
        "blocking_detail": "Would require promoting a low-confidence candidate pathway as a default executable edge.",
        "notes": "Preserved as an explicit alternate hypothesis only.",
    },
]

INTERFACE_ROWS = [
    {
        "interface_id": "IF-001",
        "node_id": "IN_EMBRYO_PRESENT",
        "boundary_type": "assay_gate",
        "direction": "external_to_maternal",
        "external_system": "embryo_presence",
        "execution_status": "required_external_input",
        "default_condition_state": "challenge_only",
        "source_table": "models/extended/adoc-literature-v0.2.0/node_dictionary.tsv",
        "source_row_id": "IN_EMBRYO_PRESENT",
        "evidence_ids": "SOFIA-ADH-001;SOFIA-ADH-002;SOFIA-ADH-003",
        "notes": "Observed assay outcome remains conditional on an explicit embryo challenge.",
    },
    {
        "interface_id": "IF-002",
        "node_id": "IN_TROPHECTODERM_COMPETENT",
        "boundary_type": "assay_gate",
        "direction": "external_to_maternal",
        "external_system": "embryo_competence",
        "execution_status": "required_external_input",
        "default_condition_state": "challenge_only",
        "source_table": "models/extended/adoc-literature-v0.2.0/node_dictionary.tsv",
        "source_row_id": "IN_TROPHECTODERM_COMPETENT",
        "evidence_ids": "SOFIA-ADH-001;SOFIA-ADH-002;SOFIA-ADH-003",
        "notes": "Embryo-side competence remains outside the maternal executable logic.",
    },
    {
        "interface_id": "IF-003",
        "node_id": "IN_EMBRYO_CONTACT",
        "boundary_type": "first_contact_gate",
        "direction": "external_to_maternal",
        "external_system": "embryo_contact",
        "execution_status": "optional_external_input",
        "default_condition_state": "challenge_only",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "IN_EMBRYO_CONTACT",
        "evidence_ids": "LIT-CDH1-001",
        "notes": "Keeps first-contact cues external instead of inventing trophoblast intracellular logic.",
    },
    {
        "interface_id": "IF-004",
        "node_id": "IN_HCG",
        "boundary_type": "embryo_feedback",
        "direction": "external_to_maternal",
        "external_system": "embryo_conditioned_cue",
        "execution_status": "available_but_off_in_required_suite",
        "default_condition_state": "off",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "IN_HCG",
        "evidence_ids": "LIT-CD98-001",
        "notes": "Available for bounded future testing but kept OFF in the required suite.",
    },
    {
        "interface_id": "IF-005",
        "node_id": "IN_EMBRYO_CONDITIONED_SIGNAL",
        "boundary_type": "embryo_feedback",
        "direction": "external_to_maternal",
        "external_system": "embryo_conditioned_cue",
        "execution_status": "available_but_off_in_required_suite",
        "default_condition_state": "off",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "IN_EMBRYO_CONDITIONED_SIGNAL",
        "evidence_ids": "LIT-CDH1-001",
        "notes": "Generic embryo-conditioned cue remains external.",
    },
    {
        "interface_id": "IF-006",
        "node_id": "IN_UTERINE_WNT_CUE",
        "boundary_type": "maternal_to_embryo_modifier",
        "direction": "maternal_boundary_to_embryo",
        "external_system": "embryo_competence",
        "execution_status": "external_only",
        "default_condition_state": "not_executable",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "IN_UTERINE_WNT_CUE",
        "evidence_ids": "",
        "notes": "Explicitly cataloged as a later embryo-side modifier rather than executable maternal logic.",
    },
    {
        "interface_id": "IF-007",
        "node_id": "IN_ER_STRESS_EXCESS",
        "boundary_type": "pathology_input",
        "direction": "external_to_maternal",
        "external_system": "stroma_pathology",
        "execution_status": "executable_boundary_input",
        "default_condition_state": "off",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "IN_ER_STRESS_EXCESS",
        "evidence_ids": "LIT-MECH-001",
        "notes": "Bounded adverse-mechanics sensitivity input only.",
    },
    {
        "interface_id": "IF-008",
        "node_id": "IN_HIGH_ECM_STIFFNESS",
        "boundary_type": "matrix_input",
        "direction": "external_to_maternal",
        "external_system": "extracellular_matrix",
        "execution_status": "executable_boundary_input",
        "default_condition_state": "off",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "IN_HIGH_ECM_STIFFNESS",
        "evidence_ids": "LIT-MECH-001",
        "notes": "Coarse mechanical sensitivity input only; no physical threshold is claimed.",
    },
    {
        "interface_id": "IF-009",
        "node_id": "IN_MIFEPRISTONE",
        "boundary_type": "assay_perturbation",
        "direction": "external_to_maternal",
        "external_system": "protocol_perturbation",
        "execution_status": "executable_boundary_input",
        "default_condition_state": "off",
        "source_table": "models/extended/adoc-literature-v0.2.0/node_dictionary.tsv",
        "source_row_id": "IN_MIFEPRISTONE",
        "evidence_ids": "SOFIA-HT-002",
        "notes": "Protocol perturbation input only.",
    },
    {
        "interface_id": "IF-010",
        "node_id": "IN_ANTI_SPP1",
        "boundary_type": "assay_perturbation",
        "direction": "external_to_maternal",
        "external_system": "protocol_perturbation",
        "execution_status": "executable_boundary_input",
        "default_condition_state": "off",
        "source_table": "models/extended/adoc-literature-v0.2.0/node_dictionary.tsv",
        "source_row_id": "IN_ANTI_SPP1",
        "evidence_ids": "LIT-SPP1-001",
        "notes": "Neutralizes free ligand only; does not erase maternal expression nodes.",
    },
    {
        "interface_id": "IF-011",
        "node_id": "IN_HAND2_LOSS",
        "boundary_type": "assay_perturbation",
        "direction": "external_to_maternal",
        "external_system": "genetic_perturbation",
        "execution_status": "executable_boundary_input",
        "default_condition_state": "off",
        "source_table": "context/literature/candidate-nodes.tsv",
        "source_row_id": "S_HAND2",
        "evidence_ids": "LIT-IHH-001",
        "notes": (
            "Loss-of-function only. Encodes the mouse conditional knockout "
            "(REF-028) and the human siRNA (REF-062) at the layer they acted "
            "on; adds no activation claim and is OFF in every inherited "
            "condition."
        ),
    },
]

MODEL_MANIFEST_ROWS = [
    {
        "model_key": "baseline_core_reference",
        "model_version": "adoc-core-v0.1.0",
        "artifact_role": "reference_parent",
        "parent_model_key": "",
        "network_bnd": "models/baseline/adoc-core-v0.1.0/network.bnd",
        "baseline_cfg": "models/baseline/adoc-core-v0.1.0/baseline.cfg",
        "condition_family": "phase1_core",
        "rule_variant_set": "adoc_core_v010",
        "modules_included": "MOD-01;MOD-03",
        "validation_label": "structural_only",
        "claim_boundary": "reference_only",
        "executable": "true",
        "disposition": "immutable_parent",
        "notes": "Minimal core reference retained unchanged.",
    },
    {
        "model_key": "literature_parity_reference",
        "model_version": "adoc-literature-v0.2.0",
        "artifact_role": "reference_parent",
        "parent_model_key": "baseline_core_reference",
        "network_bnd": "models/extended/adoc-literature-v0.2.0/network.bnd",
        "baseline_cfg": "models/extended/adoc-literature-v0.2.0/baseline.cfg",
        "condition_family": "challenge_ready",
        "rule_variant_set": "literature_parity_v020",
        "modules_included": "MOD-01;MOD-02;MOD-03;MOD-04;MOD-05;MOD-06;MOD-07;MOD-09;MOD-11;MOD-13",
        "validation_label": "structural_only",
        "claim_boundary": "reference_only",
        "executable": "true",
        "disposition": "immutable_parent",
        "notes": "Current executable literature starting point retained unchanged.",
    },
    {
        "model_key": "superset_hand2_fgf_slice",
        "model_version": MODEL_VERSION,
        "artifact_role": "module_slice",
        "parent_model_key": "literature_parity_reference",
        "network_bnd": f"models/superset/{MODEL_VERSION}/network.bnd",
        "baseline_cfg": f"models/superset/{MODEL_VERSION}/baseline.cfg",
        "condition_family": "challenge_ready",
        "rule_variant_set": MODEL_KEY,
        "modules_included": "MOD-03",
        "validation_label": "structural_only",
        "claim_boundary": "module_slice_only",
        "executable": "true",
        "disposition": "shared_runtime_artifact",
        "notes": "Same runtime artifact, interpreted only for the HAND2-FGF-estrogen expansion branch.",
    },
    {
        "model_key": MODEL_KEY,
        "model_version": MODEL_VERSION,
        "artifact_role": "full_executable_superset",
        "parent_model_key": "literature_parity_reference",
        "network_bnd": f"models/superset/{MODEL_VERSION}/network.bnd",
        "baseline_cfg": f"models/superset/{MODEL_VERSION}/baseline.cfg",
        "condition_family": "challenge_ready",
        "rule_variant_set": MODEL_KEY,
        "modules_included": "MOD-01;MOD-02;MOD-03;MOD-04;MOD-05;MOD-06;MOD-07;MOD-09;MOD-11;MOD-13",
        "validation_label": "structural_only",
        "claim_boundary": "provisional_executable_superset",
        "executable": "true",
        "disposition": "new_runtime_artifact",
        "notes": "Adds only the bounded KLF12 and HAND2-FGF-estrogen extensions supported by explicit candidate rules.",
    },
]

ENSEMBLE_ROWS = [
    {
        "ensemble_id": "structural_reference_panel",
        "model_keys": "baseline_core_reference;literature_parity_reference;"
        + MODEL_KEY,
        "condition_ids": "untreated;hormone_treated;hormone_treated_mifepristone",
        "perturbation_scope": "reference_conditions_only",
        "screening_status": "structural_only",
        "pruning_rule": "retain only immutable parent or default superset artifacts",
        "paired_control": "untreated and hormone_treated within matched model version",
        "notes": "Used to compare core, literature parity, and superset architecture without claim promotion.",
    },
    {
        "ensemble_id": "adhesion_interface_panel",
        "model_keys": MODEL_KEY,
        "condition_ids": (
            "adhesion_challenge_hormone_treated;"
            "adhesion_challenge_hormone_treated_mifepristone;"
            "adhesion_challenge_hormone_treated_anti_spp1"
        ),
        "perturbation_scope": "source-backed challenge conditions only",
        "screening_status": "structural_only",
        "pruning_rule": "exclude any candidate lacking an executable target node",
        "paired_control": "adhesion_challenge_hormone_treated",
        "notes": "Retains only source-backed perturbation contexts already present in the repository.",
    },
    {
        "ensemble_id": "mechanics_sensitivity_panel",
        "model_keys": MODEL_KEY,
        "condition_ids": "excess_er_stress;high_ecm_stiffness",
        "perturbation_scope": "bounded adverse-mechanics sensitivity",
        "screening_status": "structural_only",
        "pruning_rule": "mechanics inputs remain coarse Boolean sensitivity variables",
        "paired_control": "hormone_treated",
        "notes": "Explicitly non-calibrated mechanical sensitivity checks only.",
    },
]

MODULE_ACTIVITY_ROWS = [
    (
        "MOD-01",
        "functionally_active",
        "Hormone and protocol inputs drive executable epithelial and stromal state transitions.",
    ),
    (
        "MOD-02",
        "functionally_active",
        "Epithelial LIF-LIFR/GP130-STAT3 gate is executable with the optional KLF12 inhibitor kept OFF by default.",
    ),
    (
        "MOD-03",
        "functionally_active",
        "Executable HAND2-FGF-estrogen branch is bounded and can suppress receptivity when context inputs are enabled.",
    ),
    (
        "MOD-04",
        "functionally_active",
        "Anti-adhesive barrier removal remains executable.",
    ),
    (
        "MOD-05",
        "functionally_active",
        "Redundant epithelial adhesive effectors remain executable.",
    ),
    ("MOD-06", "functionally_active", "PC6 and DAG1 processing remain executable."),
    (
        "MOD-07",
        "functionally_active",
        "Maternal SPP1 and interface routing remain executable.",
    ),
    (
        "MOD-08",
        "unparameterized",
        "Balanced senescence lacks a bounded counter-persistence rule.",
    ),
    (
        "MOD-09",
        "functionally_active",
        "Bounded TAZ-ECM and adverse-mechanics sensitivity remain executable.",
    ),
    (
        "MOD-10",
        "structurally_disconnected",
        "Interface candidate nodes lack bounded upstream rules.",
    ),
    (
        "MOD-11",
        "contextually_inactive",
        "Embryo-conditioned cues remain available but OFF in the required condition suite.",
    ),
    (
        "MOD-12",
        "spatially_blocked",
        "Embryo-side WNT competence execution remains external by contract.",
    ),
    (
        "MOD-13",
        "functionally_active",
        "Only the bounded stiffness and ER-stress sensitivity subset is executable; other fields remain external.",
    ),
]

MODULE_ACTIVITY_MAP = {
    module_id: (status, note) for module_id, status, note in MODULE_ACTIVITY_ROWS
}

EDGE_DIRECTNESS = {
    "transcriptional": "direct",
    "proteolysis": "direct",
    "ligand_receptor_pathway": "direct",
    "pathway_to_state": "inferred",
    "pathway_to_effector": "inferred",
    "state_to_transcription_factor": "inferred",
    "state_to_dynamic_program": "inferred",
    "state_to_mechanics": "inferred",
    "state_to_ligand": "inferred",
    "state_to_growth_factor": "inferred",
    "state_to_protease": "inferred",
    "state_to_barrier": "inferred",
    "state_to_glycocalyx": "inferred",
    "state_to_glycoform": "inferred",
    "surface_to_state": "inferred",
    "barrier_to_state": "direct",
    "glycocalyx_to_state": "direct",
    "growth_factor_to_state": "inferred",
    "growth_factor_to_effector": "inferred",
    "effector_to_state": "inferred",
    "external_feedback": "externalized",
    "external_embryo_modifier": "externalized",
    "latent_to_phenotype": "aggregated",
    "phenotype_to_assay": "externalized",
    "candidate_interface": "candidate_only",
    "dynamic_matrix": "candidate_only",
    "mechanics": "inferred",
    "paracrine": "inferred",
    "cross_compartment": "inferred",
    "pathological_input": "externalized",
    "physical_input": "externalized",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(
    path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_bnd(path: Path) -> OrderedDict[str, str]:
    pattern_node = re.compile(r"^\s*Node\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{")
    pattern_logic = re.compile(r"^\s*logic\s*=\s*(.+?)\s*;\s*$")
    current: str | None = None
    rules: OrderedDict[str, str] = OrderedDict()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match_node = pattern_node.match(raw_line)
        if match_node:
            current = match_node.group(1)
            continue
        match_logic = pattern_logic.match(raw_line)
        if match_logic and current is not None:
            rules[current] = match_logic.group(1)
    return rules


def parse_cfg_assignments(path: Path, suffix: str) -> dict[str, str]:
    pattern = re.compile(
        rf"^\s*\[?([A-Za-z_][A-Za-z0-9_]*)\]?{suffix}\s*=\s*(.+?)\s*;\s*$"
    )
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(raw_line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def render_condition_with_updates(path: Path, updates: dict[str, str]) -> str:
    pattern = re.compile(
        r"^\s*\[?([A-Za-z_][A-Za-z0-9_]*)\]?\.(istate)\s*=\s*(.+?)\s*;\s*$"
    )
    rendered: list[str] = []
    seen: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(raw_line)
        if not match:
            rendered.append(raw_line)
            continue
        node_id = match.group(1)
        if node_id in updates:
            rendered.append(f"{node_id}.istate = {updates[node_id]};")
            seen.add(node_id)
        else:
            rendered.append(raw_line)
    for node_id, value in updates.items():
        if node_id not in seen:
            rendered.append(f"{node_id}.istate = {value};")
    return "\n".join(rendered).rstrip() + "\n"


def candidate_confidence_label(score: str) -> str:
    numeric = int(score)
    if numeric >= 8:
        return "high"
    if numeric >= 6:
        return "medium"
    return "low"


def build_node_order(existing_rows: list[dict[str, str]]) -> list[str]:
    order = [row["node_id"] for row in existing_rows]
    order.insert(order.index("IN_ER_STRESS_EXCESS"), "IN_HAND2_LOSS")
    order.insert(order.index("E_LIF"), "E_KLF12_HIGH")
    order.insert(order.index("S_DECIDUALIZED"), "S_FGF_MITOGENIC")
    order.insert(order.index("E_PODXL"), "E_ESTROGENIC_PROLIFERATION")
    return order


def build_superset_rules() -> OrderedDict[str, str]:
    rules = parse_bnd(SOURCE_FILES["parent_network"])
    rules["E_LIF"] = "E_SECRETORY_STATE and not E_KLF12_HIGH"
    rules["E_KLF12_HIGH"] = "E_KLF12_HIGH"
    rules["IN_HAND2_LOSS"] = "IN_HAND2_LOSS"
    rules["S_HAND2"] = "(S_BMP2 or S_PGR) and not IN_HAND2_LOSS"
    rules["S_FGF_MITOGENIC"] = "not S_HAND2"
    rules["E_ESTROGENIC_PROLIFERATION"] = "IN_E2 and S_FGF_MITOGENIC and not S_HAND2"
    rules["E_RECEPTIVE_SURFACE"] = (
        "E_GP130_STAT3 and not E_PODXL and not E_DAG1_FULL and "
        "not E_MUC1_BARRIER and not E_ESTROGENIC_PROLIFERATION and "
        "(E_CD98_CD9 or E_CDH1_APICAL or E_ANXA2_ACTIN or E_HBEGF or "
        "E_DAG1_CLEAVED or E_MUC1_SLEX or E_ITGAVB3_5 or X_SPP1_LUMEN_FREE)"
    )
    rules["OUT_MATERNAL_ADHESION_COMPETENCE"] = (
        "OUT_EPITHELIAL_RECEPTIVE and S_DECIDUALIZED and "
        "X_MECHANICAL_PERMISSIVE_ECM and (X_ADHESION_ROUTE_SPP1 or "
        "X_ADHESION_ROUTE_REDUNDANT) and not X_ANTIADHESIVE_ROUTE"
    )
    return rules


def render_network_bnd(node_order: list[str], rules: OrderedDict[str, str]) -> str:
    lines = [
        "// ADOC literature-supported maternal adhesion superset v0.3.0",
        "// Extends adoc-literature-v0.2.0 with only bounded, source-backed executable additions.",
        "// Non-executable candidates remain cataloged separately instead of becoming silent logic.",
        "",
    ]
    for node_id in node_order:
        lines.append(f"Node {node_id} {{")
        lines.append(f"  logic = {rules[node_id]};")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_node_dictionary() -> list[dict[str, str]]:
    current_rows = {
        row["node_id"]: row for row in read_tsv(SOURCE_FILES["parent_node_dictionary"])
    }
    node_order = build_node_order(list(current_rows.values()))
    rows = {**current_rows, **NEW_NODE_ROWS}
    return [rows[node_id] for node_id in node_order]


def build_edge_evidence() -> list[dict[str, str]]:
    rows = read_tsv(SOURCE_FILES["parent_edge_evidence"])
    rows.extend(NEW_EXECUTABLE_EDGES)
    return rows


def build_phenotype_contract() -> list[dict[str, str]]:
    return [
        {
            "phenotype_id": "OUT_EPITHELIAL_RECEPTIVE",
            "category": "primary",
            "executable": "true",
            "expression": "OUT_EPITHELIAL_RECEPTIVE",
            "planned_use": "construction_or_calibration",
            "evidence_ids": "SOFIA-SC-001;LIT-LIF-001;LIT-BARRIER-001;LIT-IHH-001",
            "notes": (
                "Refined epithelial receptivity phenotype requiring both the inherited "
                "secretory program, the receptive surface, and suppression of the "
                "expansion anti-receptive proliferation branch."
            ),
        },
        {
            "phenotype_id": "OUT_STROMAL_DECIDUALIZED",
            "category": "primary",
            "executable": "true",
            "expression": "OUT_STROMAL_DECIDUALIZED",
            "planned_use": "construction_or_calibration",
            "evidence_ids": "SOFIA-SC-002;SOFIA-STR-001;LIT-DECID-001",
            "notes": "Tracks the compact stromal decidual core retained in the executable model.",
        },
        {
            "phenotype_id": "OUT_MATERNAL_ADHESION_COMPETENCE",
            "category": "primary",
            "executable": "true",
            "expression": "OUT_MATERNAL_ADHESION_COMPETENCE",
            "planned_use": "mechanistic_intermediate",
            "evidence_ids": "SOFIA-ADH-002;LIT-SPP1-001;LIT-MECH-001;LIT-IHH-001",
            "notes": (
                "Separates maternal permissiveness from the observed embryo outcome and "
                "includes the bounded anti-receptive proliferation penalty."
            ),
        },
        {
            "phenotype_id": "OUT_STABLE_ADHESION",
            "category": "primary",
            "executable": "true",
            "expression": "OUT_STABLE_ADHESION",
            "planned_use": "calibration_or_validation",
            "evidence_ids": "SOFIA-ADH-001;SOFIA-ADH-002;SOFIA-ADH-003",
            "notes": (
                "Requires explicit embryo-challenge inputs and remains a model-conditional "
                "trajectory frequency rather than a clinical probability."
            ),
        },
    ]


def build_baseline_cfg(node_order: list[str]) -> str:
    parent_cfg = SOURCE_FILES["parent_baseline_cfg"]
    state_values = parse_cfg_assignments(parent_cfg, r"\.istate")
    internal_values = parse_cfg_assignments(parent_cfg, r"\.is_internal")
    state_values["E_KLF12_HIGH"] = "FALSE"
    state_values["S_FGF_MITOGENIC"] = "FALSE"
    state_values["E_ESTROGENIC_PROLIFERATION"] = "FALSE"
    # OFF by default: the loss-of-function arm is opt-in per condition, which is
    # what keeps every inherited condition bit-identical to the v0.3.0 parent.
    state_values["IN_HAND2_LOSS"] = "FALSE"
    internal_values["E_KLF12_HIGH"] = "TRUE"
    internal_values["S_FGF_MITOGENIC"] = "TRUE"
    internal_values["E_ESTROGENIC_PROLIFERATION"] = "TRUE"
    internal_values["IN_HAND2_LOSS"] = "FALSE"
    lines = [
        f"// Structural smoke defaults for {MODEL_VERSION}",
        "// Time remains relative and is not calibrated to experimental hours.",
        "",
        "discrete_time = 0;",
        "use_physrandgen = FALSE;",
        "seed_pseudorandom = 1;",
        "sample_count = 5000;",
        "max_time = 20.0;",
        "time_tick = 0.1;",
        "thread_count = 1;",
        "display_traj = FALSE;",
        "",
    ]
    for node_id in node_order:
        prefix = f"[{node_id}]" if "[" in state_values[node_id] else node_id
        lines.append(f"{prefix}.istate = {state_values[node_id]};")
    lines.append("")
    for node_id in node_order:
        lines.append(f"{node_id}.is_internal = {internal_values[node_id]};")
    return "\n".join(lines).rstrip() + "\n"


def build_complete_nodes(
    executable_node_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    candidate_rows = {
        row["node_id"]: row for row in read_tsv(SOURCE_FILES["candidate_nodes"])
    }
    complete: list[dict[str, str]] = []
    executable_ids = {row["node_id"] for row in executable_node_rows}
    for row in executable_node_rows:
        node_id = row["node_id"]
        candidate = candidate_rows.get(node_id, {})
        complete.append(
            {
                "node_id": node_id,
                "label": candidate.get("label", row["label"]),
                "catalog_origin": "literature_candidate"
                if candidate
                else "inherited_executable",
                "source_table": (
                    "context/literature/candidate-nodes.tsv"
                    if candidate
                    else "models/extended/adoc-literature-v0.2.0/node_dictionary.tsv"
                ),
                "source_row_id": node_id,
                "implementation_node_id": node_id,
                "implementation_status": "executable",
                "implementation_model_version": MODEL_VERSION,
                "disposition": (
                    "candidate_executable_extension"
                    if node_id in NEW_NODE_ROWS
                    else "inherited_executable"
                ),
                "default_module": infer_default_module(node_id),
                "compartment": candidate.get("compartment", row["compartment"]),
                "role": candidate.get("role", row["model_role"]),
                "tier": candidate.get("tier", "existing_executable"),
                "baseline_mapping": candidate.get(
                    "baseline_mapping", row["baseline_mapping"]
                ),
                "sign": candidate.get("sign", sign_from_label(node_id)),
                "confidence": candidate_confidence_label(candidate["confidence"])
                if candidate
                else row["confidence"],
                "measurable": candidate.get("measurable", row["measurement_proxies"]),
                "perturbable": candidate.get("perturbable", infer_perturbable(node_id)),
                "druggability": druggability(node_id, candidate.get("perturbable", "")),
                "logic_hint": candidate.get("logic_hint", ""),
                "uncertainty_status": uncertainty_status(node_id, candidate, row),
                "spatial_dependence_status": spatial_status(
                    node_id, candidate.get("compartment", row["compartment"])
                ),
                "evidence_ids": row.get("evidence_ids", ""),
                "reference_ids": row.get("reference_ids", candidate.get("refs", "")),
                "notes": candidate.get("notes", row["notes"]),
            }
        )
    for node_id, candidate in candidate_rows.items():
        if node_id in executable_ids:
            continue
        complete.append(
            {
                "node_id": node_id,
                "label": candidate["label"],
                "catalog_origin": "literature_candidate",
                "source_table": "context/literature/candidate-nodes.tsv",
                "source_row_id": node_id,
                "implementation_node_id": "",
                "implementation_status": "external_only"
                if node_id == "IN_UTERINE_WNT_CUE"
                else "catalog_only",
                "implementation_model_version": "",
                "disposition": "candidate_catalog_only",
                "default_module": infer_default_module(node_id),
                "compartment": candidate["compartment"],
                "role": candidate["role"],
                "tier": candidate["tier"],
                "baseline_mapping": candidate["baseline_mapping"],
                "sign": candidate["sign"],
                "confidence": candidate_confidence_label(candidate["confidence"]),
                "measurable": candidate["measurable"],
                "perturbable": candidate["perturbable"],
                "druggability": druggability(node_id, candidate["perturbable"]),
                "logic_hint": candidate["logic_hint"],
                "uncertainty_status": "high_uncertainty",
                "spatial_dependence_status": spatial_status(
                    node_id, candidate["compartment"]
                ),
                "evidence_ids": "",
                "reference_ids": candidate["refs"],
                "notes": candidate["notes"],
            }
        )
    return complete


def sign_from_label(node_id: str) -> str:
    if node_id.startswith("IN_"):
        return "contextual"
    if node_id.startswith("OUT_"):
        return "phenotype"
    return "contextual"


def infer_default_module(node_id: str) -> str:
    if node_id in {
        "IN_E2",
        "IN_PROGESTIN",
        "IN_cAMP",
        "IN_XAV939",
        "IN_MIFEPRISTONE",
        "E_PGR",
        "S_PGR",
        "S_PKA",
        "E_SECRETORY_STATE",
        "E_PAEP",
        "S_PRL",
        "S_IGFBP1",
    }:
        return "MOD-01"
    if node_id in {
        "E_LIF",
        "E_KLF12_HIGH",
        "E_GP130_STAT3",
        "OUT_EPITHELIAL_RECEPTIVE",
    }:
        return "MOD-02"
    if node_id in {
        "E_IHH",
        "S_NR2F2",
        "S_BMP2",
        "S_HAND2",
        "S_FGF_MITOGENIC",
        "E_ESTROGENIC_PROLIFERATION",
        "S_DECIDUALIZED",
        "OUT_STROMAL_DECIDUALIZED",
    }:
        return "MOD-03"
    if node_id in {
        "E_PODXL",
        "E_DAG1_FULL",
        "E_MUC1_BARRIER",
        "E_MUC1_SLEX",
        "X_INTERFACE_ANTIADHESIVE_RELAY",
        "X_ANTIADHESIVE_ROUTE",
    }:
        return "MOD-04"
    if node_id in {
        "E_CD98_CD9",
        "E_CDH1_APICAL",
        "E_ANXA2_ACTIN",
        "E_HBEGF",
        "E_RECEPTIVE_SURFACE",
        "X_INTERFACE_REDUNDANT_RELAY",
        "X_ADHESION_ROUTE_REDUNDANT",
    }:
        return "MOD-05"
    if node_id in {"E_PC6", "E_DAG1_CLEAVED"}:
        return "MOD-06"
    if node_id in {
        "IN_ANTI_SPP1",
        "E_SPP1_EXPR",
        "S_SPP1",
        "E_ITGAVB3_5",
        "X_SPP1_LUMEN_FREE",
        "X_INTERFACE_SPP1_RELAY",
        "X_ADHESION_ROUTE_SPP1",
        "OUT_MATERNAL_ADHESION_COMPETENCE",
    }:
        return "MOD-07"
    if node_id in {"S_DECIDUAL_SENESCENCE_BALANCED"}:
        return "MOD-08"
    if node_id in {
        "IN_ER_STRESS_EXCESS",
        "IN_HIGH_ECM_STIFFNESS",
        "S_TAZ_ECM",
        "X_MECHANICAL_STRESS_RELAY",
        "X_MECHANICAL_PERMISSIVE_ECM",
    }:
        return "MOD-09"
    if node_id in {"X_LGALS1_3", "X_BSG_ITGB1"}:
        return "MOD-10"
    if node_id in {
        "IN_HCG",
        "IN_EMBRYO_CONDITIONED_SIGNAL",
        "IN_EMBRYO_CONTACT",
        "OUT_STABLE_ADHESION",
    }:
        return "MOD-11"
    if node_id in {"IN_UTERINE_WNT_CUE", "IN_TROPHECTODERM_COMPETENT"}:
        return "MOD-12"
    if node_id in {"IN_EMBRYO_PRESENT"}:
        return "MOD-11"
    return "MOD-13"


def infer_perturbable(node_id: str) -> str:
    return "yes" if node_id.startswith(("IN_", "E_", "S_", "X_")) else "no"


def druggability(node_id: str, perturbable_value: str) -> str:
    if node_id in {"E_PGR", "S_PGR", "IN_MIFEPRISTONE"}:
        return "source_backed_agent"
    if node_id in {"X_SPP1_LUMEN_FREE", "IN_ANTI_SPP1"}:
        return "source_backed_agent"
    if node_id.startswith("IN_"):
        return "boundary_input_only"
    if perturbable_value == "yes":
        return "plausible_target"
    return "not_cataloged"


def uncertainty_status(
    node_id: str, candidate: dict[str, str], executable_row: dict[str, str]
) -> str:
    if node_id in {
        "X_INTERFACE_SPP1_RELAY",
        "X_INTERFACE_REDUNDANT_RELAY",
        "X_INTERFACE_ANTIADHESIVE_RELAY",
        "X_MECHANICAL_STRESS_RELAY",
    }:
        return "bounded_structural_uncertainty"
    if candidate.get("tier") == "expansion":
        return "candidate_expansion"
    if executable_row.get("confidence") == "verified":
        return "low_uncertainty"
    if executable_row.get("confidence") == "assumption":
        return "bounded_structural_uncertainty"
    return "provisional"


def spatial_status(node_id: str, compartment: str) -> str:
    if node_id == "IN_UTERINE_WNT_CUE":
        return "external_embryo_execution"
    if compartment.startswith("external") or compartment == "input_boundary":
        return "external_boundary"
    if compartment == "interface":
        return "interface_context"
    if compartment == "extracellular":
        return "matrix_context"
    return "none"


def build_complete_edges(
    executable_edges: list[dict[str, str]],
) -> list[dict[str, str]]:
    candidate_edges = read_tsv(SOURCE_FILES["candidate_edges"])
    by_tuple: dict[tuple[str, str, str], list[str]] = {}
    for edge in executable_edges:
        key = (edge["source"], edge["target"], edge["sign"])
        by_tuple.setdefault(key, []).append(edge["edge_id"])
    rows: list[dict[str, str]] = []
    for edge in executable_edges:
        rows.append(
            {
                "edge_id": edge["edge_id"],
                "source": edge["source"],
                "target": edge["target"],
                "catalog_origin": "executable_edge",
                "source_table": f"models/superset/{MODEL_VERSION}/edge_evidence.tsv",
                "source_row_id": edge["edge_id"],
                "implementation_edge_ids": edge["edge_id"],
                "implementation_status": "executable",
                "implementation_model_version": MODEL_VERSION,
                "sign": edge["sign"],
                "directness": "inherited_or_curated",
                "compartment_context": edge_compartment_context(
                    edge["source"], edge["target"]
                ),
                "context_scope": infer_default_module(edge["target"]),
                "evidence_ids": edge["evidence_id"],
                "reference_ids": "",
                "confidence": edge["confidence"],
                "tier": "executable",
                "default_enabled": "true",
                "variant_id": edge["variant_id"],
                "spatial_requirement": spatial_requirement(
                    edge["source"], edge["target"]
                ),
                "uncertainty_note": edge["notes"]
                if edge["confidence"] != "verified"
                else "",
                "notes": edge["notes"],
            }
        )
    for candidate in candidate_edges:
        key = (candidate["source"], candidate["target"], candidate["sign"])
        implementation_ids = ";".join(by_tuple.get(key, []))
        rows.append(
            {
                "edge_id": candidate["edge_id"],
                "source": candidate["source"],
                "target": candidate["target"],
                "catalog_origin": "literature_candidate",
                "source_table": "context/literature/candidate-edges.tsv",
                "source_row_id": candidate["edge_id"],
                "implementation_edge_ids": implementation_ids,
                "implementation_status": (
                    "executable"
                    if implementation_ids
                    else "external_only"
                    if candidate["edge_id"] == "EDGE-048"
                    else "catalog_only"
                ),
                "implementation_model_version": MODEL_VERSION
                if implementation_ids
                else "",
                "sign": candidate["sign"],
                "directness": EDGE_DIRECTNESS.get(candidate["mechanism"], "inferred"),
                "compartment_context": edge_compartment_context(
                    candidate["source"], candidate["target"]
                ),
                "context_scope": infer_default_module(candidate["target"]),
                "evidence_ids": "",
                "reference_ids": candidate["refs"],
                "confidence": candidate_confidence_label(candidate["confidence"]),
                "tier": candidate["tier"],
                "default_enabled": "true" if implementation_ids else "false",
                "variant_id": implementation_ids or "",
                "spatial_requirement": spatial_requirement(
                    candidate["source"], candidate["target"]
                ),
                "uncertainty_note": candidate["notes"],
                "notes": candidate["notes"],
            }
        )
    return rows


def edge_compartment_context(source: str, target: str) -> str:
    source_prefix = source.split("_", 1)[0]
    target_prefix = target.split("_", 1)[0]
    return f"{source_prefix.lower()}_to_{target_prefix.lower()}"


def spatial_requirement(source: str, target: str) -> str:
    if source.startswith("IN_") and "EMBRYO" in source:
        return "external_embryo"
    if target.startswith("IN_"):
        return "external_embryo"
    if source.startswith("X_") or target.startswith("X_"):
        return "interface_or_matrix_context"
    return "none"


def build_modules() -> list[dict[str, str]]:
    rows = []
    for mechanism in read_tsv(SOURCE_FILES["mechanisms"]):
        status, note = MODULE_ACTIVITY_MAP[mechanism["module_id"]]
        rows.append(
            {
                "module_id": mechanism["module_id"],
                "name": mechanism["name"],
                "compartments": mechanism["compartments"],
                "summary": mechanism["summary"],
                "evidence": mechanism["evidence"],
                "reference_ids": mechanism["refs"],
                "confidence": mechanism["confidence"],
                "maboss_guidance": mechanism["maboss"],
                "execution_status": module_execution_disposition(
                    mechanism["module_id"]
                ),
                "activity_status": status,
                "manifest_membership": module_manifest_membership(
                    mechanism["module_id"]
                ),
                "source_table": "context/literature/mechanisms.tsv",
                "source_row_id": mechanism["module_id"],
                "notes": note,
            }
        )
    return rows


def module_execution_disposition(module_id: str) -> str:
    if module_id in {"MOD-08", "MOD-10"}:
        return "catalog_only"
    if module_id == "MOD-12":
        return "external_only"
    if module_id == "MOD-11":
        return "executable_boundary_module"
    return "executable"


def module_manifest_membership(module_id: str) -> str:
    if module_id in {"MOD-08", "MOD-10", "MOD-12"}:
        return ""
    return MODEL_KEY


def build_module_activity_report() -> list[dict[str, str]]:
    rows = []
    for module_id, status, note in MODULE_ACTIVITY_ROWS:
        rows.append(
            {
                "model_key": MODEL_KEY,
                "module_id": module_id,
                "activity_status": status,
                "evidence": "static_structural_classification",
                "notes": note,
            }
        )
    return rows


def build_drug_target_catalog(
    complete_nodes: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows = []
    for row in complete_nodes:
        if row["perturbable"] != "yes":
            continue
        if row["catalog_origin"] == "literature_candidate" or row["node_id"] in {
            "E_PGR",
            "S_PGR",
            "X_SPP1_LUMEN_FREE",
            "IN_MIFEPRISTONE",
            "IN_ANTI_SPP1",
        }:
            rows.append(
                {
                    "target_id": row["node_id"],
                    "target_label": row["label"],
                    "target_class": row["role"],
                    "execution_status": row["implementation_status"],
                    "known_agent_or_context": known_agent(row["node_id"]),
                    "modulation_direction": supported_direction(row["node_id"]),
                    "source_table": row["source_table"],
                    "source_row_id": row["source_row_id"],
                    "evidence_ids": row["evidence_ids"],
                    "screening_readiness": "structural_only"
                    if row["implementation_status"] == "executable"
                    else "catalog_only",
                    "claim_boundary": "No efficacy claim; target listing only.",
                    "notes": row["notes"],
                }
            )
    return rows


def known_agent(node_id: str) -> str:
    if node_id in {"E_PGR", "S_PGR", "IN_MIFEPRISTONE"}:
        return "mifepristone"
    if node_id in {"X_SPP1_LUMEN_FREE", "IN_ANTI_SPP1"}:
        return "anti_SPP1"
    return ""


def supported_direction(node_id: str) -> str:
    if node_id in {"E_PGR", "S_PGR", "X_SPP1_LUMEN_FREE"}:
        return "inhibition"
    if node_id.startswith("IN_"):
        return "context_input"
    return "unspecified_modulation"


def build_conditions() -> dict[str, str]:
    payload: dict[str, str] = {}
    for condition in sorted((EXTENDED_DIR / "conditions").glob("*.cfg")):
        payload[condition.name] = condition.read_text(encoding="utf-8")
    maternal_template = EXTENDED_DIR / "conditions" / "hormone_treated_maternal.cfg"
    basal_template = EXTENDED_DIR / "conditions" / "basal_maternal.cfg"
    payload["untreated.cfg"] = basal_template.read_text(encoding="utf-8")
    payload["hormone_treated.cfg"] = maternal_template.read_text(encoding="utf-8")
    payload["hormone_treated_mifepristone.cfg"] = render_condition_with_updates(
        maternal_template,
        {"IN_MIFEPRISTONE": "TRUE"},
    )
    payload["hormone_treated_anti_spp1.cfg"] = render_condition_with_updates(
        maternal_template,
        {"IN_ANTI_SPP1": "TRUE"},
    )
    # The washout maternal phase. Previously absent, which made `washout`
    # resolve in the protocol graph while being impossible to execute: running
    # it would have failed on a missing condition file.
    #
    # Its INPUT state is byte-identical to hormone_treated_maternal, and that is
    # correct rather than redundant -- the core protocol's own step note says
    # washout "reverts to the matched HT maternal input state". What separates
    # washout from hormone_treated is entirely its CONTINUATION: it is seeded
    # from the anti-SPP1 terminal joint state, not the hormone-treated one.
    #
    # Recorded consequence, because it bounds what this arm can ever show: the
    # network is a DAG over its free variables, so each phase has a unique fixed
    # point under a sustained input assignment, independent of its starting
    # state. At a converged horizon washout must therefore equal
    # hormone_treated. Any difference between them is a finite-horizon
    # transient, and this arm can only be read as one.
    payload["washout.cfg"] = maternal_template.read_text(encoding="utf-8")
    payload["excess_er_stress.cfg"] = render_condition_with_updates(
        maternal_template,
        {"IN_ER_STRESS_EXCESS": "TRUE"},
    )
    payload["high_ecm_stiffness.cfg"] = render_condition_with_updates(
        maternal_template,
        {"IN_HIGH_ECM_STIFFNESS": "TRUE"},
    )
    # The HAND2 loss-of-function arm. Every other condition leaves
    # IN_HAND2_LOSS at its baseline FALSE, which is what keeps the declared
    # suite bit-identical to the v0.3.0 parent on all six endpoints.
    payload["hormone_treated_hand2_loss.cfg"] = render_condition_with_updates(
        maternal_template,
        {"IN_HAND2_LOSS": "TRUE"},
    )
    payload["adhesion_challenge_hormone_treated_hand2_loss.cfg"] = (
        render_condition_with_updates(
            EXTENDED_DIR / "conditions" / "adhesion_challenge_hormone_treated.cfg",
            {"IN_HAND2_LOSS": "TRUE"},
        )
    )
    return payload


def build_mermaid_complete(
    complete_nodes: list[dict[str, str]], complete_edges: list[dict[str, str]]
) -> str:
    lines = ["graph TD"]
    subgraphs = OrderedDict(
        [
            (
                "External",
                [
                    row
                    for row in complete_nodes
                    if row["compartment"].startswith("external")
                    or row["compartment"] == "input_boundary"
                ],
            ),
            (
                "Epithelium",
                [row for row in complete_nodes if row["compartment"] == "epithelium"],
            ),
            (
                "Stroma",
                [row for row in complete_nodes if row["compartment"] == "stroma"],
            ),
            (
                "Interface",
                [
                    row
                    for row in complete_nodes
                    if row["compartment"]
                    in {"interface", "extracellular", "stroma_external"}
                ],
            ),
        ]
    )
    for title, rows in subgraphs.items():
        lines.append(f"  subgraph {title}")
        for row in rows:
            label = (
                row["node_id"]
                if row["implementation_status"] == "executable"
                else f"{row['node_id']}?"
            )
            lines.append(f"    {row['node_id']}[{label}]")
        lines.append("  end")
    seen_edges: set[tuple[str, str]] = set()
    for edge in complete_edges:
        if edge["catalog_origin"] != "literature_candidate":
            continue
        key = (edge["source"], edge["target"])
        if key in seen_edges:
            continue
        seen_edges.add(key)
        arrow = "-->" if edge["implementation_status"] == "executable" else "-.->"
        lines.append(f"  {edge['source']} {arrow} {edge['target']}")
    lines.append("  classDef candidate stroke-dasharray: 5 5;")
    for row in complete_nodes:
        if row["implementation_status"] != "executable":
            lines.append(f"  class {row['node_id']} candidate;")
    return "\n".join(lines) + "\n"


def build_mermaid_executable(
    node_order: list[str], executable_edges: list[dict[str, str]]
) -> str:
    lines = [
        "graph TD",
        "  subgraph Inputs",
    ]
    for node_id in [node for node in node_order if node.startswith("IN_")]:
        lines.append(f"    {node_id}[{node_id}]")
    lines.append("  end")
    for title, prefix in [
        ("Epithelium", "E_"),
        ("Stroma", "S_"),
        ("Interface", "X_"),
        ("Phenotypes", "OUT_"),
    ]:
        lines.append(f"  subgraph {title}")
        for node_id in [node for node in node_order if node.startswith(prefix)]:
            lines.append(f"    {node_id}[{node_id}]")
        lines.append("  end")
    for edge in executable_edges:
        arrow = "-->" if edge["sign"] == "activation" else "-.->"
        lines.append(f"  {edge['source']} {arrow} {edge['target']}")
    return "\n".join(lines) + "\n"


def build_readme(generated_files: dict[str, str]) -> str:
    return f"""# ADOC Literature Superset v0.3.0

This directory contains the Phase 1D literature-superset family for the ADOC
maternal adhesion model.

## Scope

- Starts from the immutable executable parent `models/extended/adoc-literature-v0.2.0/`.
- Adds only the bounded executable extensions supported by explicit candidate
  logic hints:
  - `E_KLF12_HIGH` as an optional inhibitory context for epithelial `LIF`;
  - `S_FGF_MITOGENIC` as a HAND2-restrained stromal mitogenic relay;
  - `E_ESTROGENIC_PROLIFERATION` as an anti-receptive epithelial state that
    suppresses the receptive surface.
- Keeps unsupported, spatial, embryo-side, or unparameterized biology explicit
  in the catalogs and unresolved-mechanism tables instead of making it silently
  executable.

## Claim Boundary

- Structural and bounded executable architecture only.
- No patient personalization is encoded here.
- MaBoSS probabilities remain simulated trajectory frequencies, not clinical
  probabilities.
- Drug-target and ensemble catalogs remain `structural_only` and do not imply
  validated efficacy.

## Family Artifacts

- `complete_nodes.tsv`, `complete_edges.tsv`: full provenance-preserving node
  and edge catalogs with candidate-to-implementation crosswalk fields.
- `modules.tsv`, `module_activity_report.tsv`: module catalog and structural
  activity status.
- `rule_variants.tsv`, `unresolved_mechanisms.tsv`: explicit executable and
  non-executable alternatives.
- `interface_contract.tsv`: external inputs and unsupported biology kept at the
  boundary.
- `drug_target_catalog.tsv`, `ensemble_definition.tsv`: bounded screening-ready
  architecture metadata only.
- `network.bnd`, `baseline.cfg`, `conditions/*.cfg`: executable superset
  runtime artifacts.
- `node_dictionary.tsv`, `edge_evidence.tsv`, `phenotype_contract.tsv`:
  executable model contract tables.

## Validation Commands

Structural generation and validation:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B -m dt_adoc.model.superset_family --write
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B -m dt_adoc.model.superset_family --validate
```

Minimal MaBoSS smoke when the Pixi runtime is available:

```bash
pixi run python - <<'PY'
from pathlib import Path
import json
import maboss

root = Path("models/superset/{MODEL_VERSION}")
condition = root / "conditions" / "hormone_treated.cfg"
sim = maboss.load(str(root / "network.bnd"), str(root / "baseline.cfg"), cmaboss=True)
for raw in condition.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("//"):
        continue
    lhs, rhs = line.rstrip(";").split("=", 1)
    node = lhs.strip().replace(".istate", "")
    sim.network.set_istate(node, [0.0, 1.0] if rhs.strip() == "TRUE" else [1.0, 0.0])
res = sim.run()
print(json.dumps(res.get_last_nodes_probtraj().iloc[-1][[
    "X_MECHANICAL_STRESS_RELAY",
    "X_INTERFACE_SPP1_RELAY",
    "X_INTERFACE_REDUNDANT_RELAY",
    "X_INTERFACE_ANTIADHESIVE_RELAY",
    "OUT_EPITHELIAL_RECEPTIVE",
    "OUT_STROMAL_DECIDUALIZED",
    "OUT_MATERNAL_ADHESION_COMPETENCE",
    "OUT_STABLE_ADHESION",
]].to_dict(), sort_keys=True))
PY
```

## Generated File Hashes

{generated_files["hash_lines"]}
"""


def build_provenance(
    generated: dict[str, str], condition_hashes: dict[str, str]
) -> str:
    maboss_version = "unavailable"
    try:
        maboss_version = importlib.metadata.version("maboss")
    except importlib.metadata.PackageNotFoundError:
        pass
    pixi_python = "unavailable"
    pixi_maboss_version = "unavailable"
    pixi = shutil.which("pixi")
    if pixi is not None:
        result = subprocess.run(
            [
                pixi,
                "run",
                "python",
                "-c",
                (
                    "import importlib.metadata, platform; "
                    "print(platform.python_version()); "
                    "print(importlib.metadata.version('maboss'))"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        if result.returncode == 0:
            lines = [
                line.strip() for line in result.stdout.splitlines() if line.strip()
            ]
            if len(lines) >= 2:
                pixi_python, pixi_maboss_version = lines[:2]
    source_hashes = "\n".join(
        f'{name}_sha256 = "{sha256(path)}"' for name, path in SOURCE_FILES.items()
    )
    artifact_hashes = "\n".join(
        f'{key} = "{value}"'
        for key, value in generated.items()
        if key.endswith("_sha256")
    )
    condition_lines = "\n".join(
        f'  "conditions/{name}",' for name in sorted(condition_hashes)
    )
    condition_hash_lines = "\n".join(
        f'{name.replace(".", "_")}_sha256 = "{digest}"'
        for name, digest in condition_hashes.items()
    )
    return f"""schema_version = "1.0"
family_id = "{MODEL_KEY}"
model_version = "{MODEL_VERSION}"
generated_on = "2026-07-26"
generator_module = "dt_adoc.model.superset_family"

[claim_boundary]
validation_label = "structural_only"
claim_ceiling = "Provisional executable literature superset with bounded structural validation only; not a calibrated, patient-specific, or biologically validated digital twin."

[baseline_policy]
immutable_parent = true
shared_topology_across_conditions = true
patient_variants_required_for_personalization = true

[personalization_contract]
applied = false
independent_biological_unit = "not_applicable_condition_level_model"
cohort_inclusion = "not_applicable_condition_level_model"
notes = "This family encodes condition-level maternal mechanisms only. Patient variants must be versioned separately and must not overwrite this baseline."

[time_semantics]
maboss_time_units = "relative_only"
notes = "No physical time calibration is claimed for this superset family."

[simulation_defaults]
discrete_time = 0
use_physrandgen = false
seed_pseudorandom = 1
sample_count = 5000
max_time = 20.0
time_tick = 0.1
thread_count = 1

[software]
python = "{platform.python_version()}"
maboss_python_package = "{maboss_version}"
pixi_python = "{pixi_python}"
pixi_maboss_python_package = "{pixi_maboss_version}"
standalone_maboss_binary_on_path = {str(shutil.which("MaBoSS") is not None).lower()}

[sources]
candidate_nodes = "context/literature/candidate-nodes.tsv"
candidate_edges = "context/literature/candidate-edges.tsv"
mechanisms = "context/literature/mechanisms.tsv"
evidence_register = "context/evidence-register.tsv"
parent_network = "models/extended/adoc-literature-v0.2.0/network.bnd"
parent_baseline_cfg = "models/extended/adoc-literature-v0.2.0/baseline.cfg"
parent_node_dictionary = "models/extended/adoc-literature-v0.2.0/node_dictionary.tsv"
parent_edge_evidence = "models/extended/adoc-literature-v0.2.0/edge_evidence.tsv"
parent_phenotype_contract = "models/extended/adoc-literature-v0.2.0/phenotype_contract.tsv"
parent_provenance = "models/extended/adoc-literature-v0.2.0/provenance.toml"

[source_hashes]
{source_hashes}

[evidence_scope]
executable_extensions = [
  "E_KLF12_HIGH inhibitory LIF context",
  "S_FGF_MITOGENIC HAND2-restrained stromal relay",
  "E_ESTROGENIC_PROLIFERATION anti-receptive branch",
]
catalog_only_or_external = [
  "S_STAT3",
  "S_DECIDUAL_SENESCENCE_BALANCED",
  "X_LGALS1_3",
  "X_BSG_ITGB1",
  "IN_UTERINE_WNT_CUE",
]

[condition_suite]
default_condition_family = "challenge_ready"
conditions = [
{condition_lines}
]
perturbations = [
  "mifepristone",
  "anti_spp1",
  "embryo_absent",
  "embryo_incompetent",
  "excess_er_stress",
  "high_ecm_stiffness",
]

[artifacts]
complete_nodes = "models/superset/{MODEL_VERSION}/complete_nodes.tsv"
complete_edges = "models/superset/{MODEL_VERSION}/complete_edges.tsv"
modules = "models/superset/{MODEL_VERSION}/modules.tsv"
module_activity_report = "models/superset/{MODEL_VERSION}/module_activity_report.tsv"
rule_variants = "models/superset/{MODEL_VERSION}/rule_variants.tsv"
interface_contract = "models/superset/{MODEL_VERSION}/interface_contract.tsv"
drug_target_catalog = "models/superset/{MODEL_VERSION}/drug_target_catalog.tsv"
executable_model_manifest = "models/superset/{MODEL_VERSION}/executable_model_manifest.tsv"
ensemble_definition = "models/superset/{MODEL_VERSION}/ensemble_definition.tsv"
unresolved_mechanisms = "models/superset/{MODEL_VERSION}/unresolved_mechanisms.tsv"
literature_superset_network = "models/superset/{MODEL_VERSION}/literature_superset_network.mmd"
executable_modules_network = "models/superset/{MODEL_VERSION}/executable_modules_network.mmd"
network_bnd = "models/superset/{MODEL_VERSION}/network.bnd"
baseline_cfg = "models/superset/{MODEL_VERSION}/baseline.cfg"
node_dictionary = "models/superset/{MODEL_VERSION}/node_dictionary.tsv"
edge_evidence = "models/superset/{MODEL_VERSION}/edge_evidence.tsv"
phenotype_contract = "models/superset/{MODEL_VERSION}/phenotype_contract.tsv"
readme = "models/superset/{MODEL_VERSION}/README.md"

[artifact_hashes]
{artifact_hashes}

[condition_hashes]
{condition_hash_lines}
"""


def validate_written(output_dir: Path) -> None:
    # Re-derive parity from what was actually written, not from what was computed
    # in memory. This is the check that would have caught the original defect:
    # every validator in the repo read the relation table, none parsed the network.
    reconcile(
        parse_bnd_rules(output_dir / "network.bnd"),
        read_tsv(output_dir / "edge_evidence.tsv"),
        load_adjudications(SOURCE_FILES["topology_adjudications"]),
    )
    tomllib.loads((output_dir / "provenance.toml").read_text(encoding="utf-8"))
    complete_nodes = read_tsv(output_dir / "complete_nodes.tsv")
    complete_edges = read_tsv(output_dir / "complete_edges.tsv")
    candidate_nodes = {
        row["node_id"] for row in read_tsv(SOURCE_FILES["candidate_nodes"])
    }
    candidate_edges = {
        row["edge_id"] for row in read_tsv(SOURCE_FILES["candidate_edges"])
    }
    complete_node_ids = {row["node_id"] for row in complete_nodes}
    complete_edge_ids = {row["edge_id"] for row in complete_edges}
    missing_nodes = sorted(candidate_nodes - complete_node_ids)
    missing_edges = sorted(candidate_edges - complete_edge_ids)
    if missing_nodes:
        raise ValueError(
            f"missing candidate nodes in complete_nodes.tsv: {missing_nodes}"
        )
    if missing_edges:
        raise ValueError(
            f"missing candidate edges in complete_edges.tsv: {missing_edges}"
        )
    node_dictionary = read_tsv(output_dir / "node_dictionary.tsv")
    executable_ids = [row["node_id"] for row in node_dictionary]
    rule_nodes = list(parse_bnd(output_dir / "network.bnd"))
    if executable_ids != rule_nodes:
        raise ValueError(
            "node_dictionary.tsv order does not match network.bnd node order"
        )
    edge_rows = read_tsv(output_dir / "edge_evidence.tsv")
    for edge in edge_rows:
        if edge["source"] not in executable_ids or edge["target"] not in executable_ids:
            raise ValueError(
                f"edge_evidence.tsv references unknown executable nodes: {edge}"
            )
    phenotype_rows = read_tsv(output_dir / "phenotype_contract.tsv")
    for row in phenotype_rows:
        expression = row["expression"]
        if expression and expression not in executable_ids:
            raise ValueError(
                f"phenotype expression {expression!r} is not an executable node id"
            )
    for path in sorted((output_dir / "conditions").glob("*.cfg")):
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("//"):
                continue
            left = line.split("=", 1)[0].strip().replace(".istate", "")
            if left not in executable_ids:
                raise ValueError(f"{path} references unknown node {left}")


def write_family(output_dir: Path = SUPERTSET_DIR) -> None:
    # Reconcile before anything is created or unlinked. The rules are the only
    # authority on what the model computes; if a dependency executes without a
    # curated relation, or a curated relation stopped executing, and no dated
    # adjudication covers it, generation must abort with nothing written rather
    # than emit a family whose provenance silently disagrees with its network.
    rules = build_superset_rules()
    topology = reconcile(
        rules,
        build_edge_evidence(),
        load_adjudications(SOURCE_FILES["topology_adjudications"]),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    conditions_dir = output_dir / "conditions"
    conditions_dir.mkdir(parents=True, exist_ok=True)
    for stale_cfg in conditions_dir.glob("*.cfg"):
        stale_cfg.unlink()

    node_dictionary = build_node_dictionary()
    node_order = [row["node_id"] for row in node_dictionary]
    executable_edges = build_edge_evidence()
    complete_nodes = build_complete_nodes(node_dictionary)
    complete_edges = build_complete_edges(executable_edges)
    modules = build_modules()
    module_activity = build_module_activity_report()
    baseline_cfg = build_baseline_cfg(node_order)
    conditions = build_conditions()
    network_bnd = render_network_bnd(node_order, rules)
    phenotype_contract = build_phenotype_contract()
    generated_files: dict[str, str] = {}

    write_tsv(
        output_dir / "node_dictionary.tsv", node_dictionary, list(node_dictionary[0])
    )
    write_tsv(
        output_dir / "edge_evidence.tsv", executable_edges, list(executable_edges[0])
    )
    write_tsv(output_dir / "topology.tsv", topology, list(TOPOLOGY_COLUMNS))
    write_tsv(
        output_dir / "phenotype_contract.tsv",
        phenotype_contract,
        list(phenotype_contract[0]),
    )
    write_tsv(
        output_dir / "complete_nodes.tsv",
        complete_nodes,
        [
            "node_id",
            "label",
            "catalog_origin",
            "source_table",
            "source_row_id",
            "implementation_node_id",
            "implementation_status",
            "implementation_model_version",
            "disposition",
            "default_module",
            "compartment",
            "role",
            "tier",
            "baseline_mapping",
            "sign",
            "confidence",
            "measurable",
            "perturbable",
            "druggability",
            "logic_hint",
            "uncertainty_status",
            "spatial_dependence_status",
            "evidence_ids",
            "reference_ids",
            "notes",
        ],
    )
    write_tsv(
        output_dir / "complete_edges.tsv",
        complete_edges,
        [
            "edge_id",
            "source",
            "target",
            "catalog_origin",
            "source_table",
            "source_row_id",
            "implementation_edge_ids",
            "implementation_status",
            "implementation_model_version",
            "sign",
            "directness",
            "compartment_context",
            "context_scope",
            "evidence_ids",
            "reference_ids",
            "confidence",
            "tier",
            "default_enabled",
            "variant_id",
            "spatial_requirement",
            "uncertainty_note",
            "notes",
        ],
    )
    write_tsv(output_dir / "modules.tsv", modules, list(modules[0]))
    write_tsv(
        output_dir / "module_activity_report.tsv",
        module_activity,
        list(module_activity[0]),
    )
    write_tsv(output_dir / "rule_variants.tsv", RULE_VARIANTS, list(RULE_VARIANTS[0]))
    write_tsv(
        output_dir / "interface_contract.tsv", INTERFACE_ROWS, list(INTERFACE_ROWS[0])
    )
    write_tsv(
        output_dir / "drug_target_catalog.tsv",
        build_drug_target_catalog(complete_nodes),
        [
            "target_id",
            "target_label",
            "target_class",
            "execution_status",
            "known_agent_or_context",
            "modulation_direction",
            "source_table",
            "source_row_id",
            "evidence_ids",
            "screening_readiness",
            "claim_boundary",
            "notes",
        ],
    )
    write_tsv(
        output_dir / "executable_model_manifest.tsv",
        MODEL_MANIFEST_ROWS,
        list(MODEL_MANIFEST_ROWS[0]),
    )
    write_tsv(
        output_dir / "ensemble_definition.tsv", ENSEMBLE_ROWS, list(ENSEMBLE_ROWS[0])
    )
    write_tsv(
        output_dir / "unresolved_mechanisms.tsv",
        UNRESOLVED_ROWS,
        list(UNRESOLVED_ROWS[0]),
    )
    (output_dir / "network.bnd").write_text(network_bnd, encoding="utf-8")
    (output_dir / "baseline.cfg").write_text(baseline_cfg, encoding="utf-8")
    for name, contents in conditions.items():
        (output_dir / "conditions" / name).write_text(contents, encoding="utf-8")
    (output_dir / "literature_superset_network.mmd").write_text(
        build_mermaid_complete(complete_nodes, complete_edges), encoding="utf-8"
    )
    (output_dir / "executable_modules_network.mmd").write_text(
        build_mermaid_executable(node_order, executable_edges), encoding="utf-8"
    )

    condition_hashes = {
        name: sha256(output_dir / "conditions" / name) for name in sorted(conditions)
    }
    hash_targets = {
        "complete_nodes": output_dir / "complete_nodes.tsv",
        "complete_edges": output_dir / "complete_edges.tsv",
        "modules": output_dir / "modules.tsv",
        "module_activity_report": output_dir / "module_activity_report.tsv",
        "rule_variants": output_dir / "rule_variants.tsv",
        "interface_contract": output_dir / "interface_contract.tsv",
        "drug_target_catalog": output_dir / "drug_target_catalog.tsv",
        "executable_model_manifest": output_dir / "executable_model_manifest.tsv",
        "ensemble_definition": output_dir / "ensemble_definition.tsv",
        "unresolved_mechanisms": output_dir / "unresolved_mechanisms.tsv",
        "literature_superset_network": output_dir / "literature_superset_network.mmd",
        "executable_modules_network": output_dir / "executable_modules_network.mmd",
        "network_bnd": output_dir / "network.bnd",
        "baseline_cfg": output_dir / "baseline.cfg",
        "node_dictionary": output_dir / "node_dictionary.tsv",
        "edge_evidence": output_dir / "edge_evidence.tsv",
        "topology": output_dir / "topology.tsv",
        "phenotype_contract": output_dir / "phenotype_contract.tsv",
    }
    for key, path in hash_targets.items():
        generated_files[f"{key}_sha256"] = sha256(path)
    hash_lines = "\n".join(
        f"- `{path.relative_to(ROOT)}`: `{generated_files[f'{key}_sha256']}`"
        for key, path in hash_targets.items()
    )
    readme_text = build_readme({"hash_lines": hash_lines})
    (output_dir / "README.md").write_text(readme_text, encoding="utf-8")
    generated_files["readme_sha256"] = sha256(output_dir / "README.md")
    (output_dir / "provenance.toml").write_text(
        build_provenance(generated_files, condition_hashes), encoding="utf-8"
    )
    validate_written(output_dir)


def validate_family(output_dir: Path = SUPERTSET_DIR) -> None:
    validate_written(output_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true", help="Generate the superset family."
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the existing family artifacts.",
    )
    args = parser.parse_args(argv)
    if args.write:
        write_family()
    if args.validate:
        validate_family()
    if not args.write and not args.validate:
        parser.error("at least one of --write or --validate is required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
