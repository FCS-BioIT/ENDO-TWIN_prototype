"""Quantitative inventory of the research foundation, computed from committed files.

Every number in the README dashboard and in docs/RESEARCH_FOUNDATION_AUDIT.md
comes from :func:`compute` and is written to
``docs/research_foundation_metrics.json`` by ``pixi run endotwin-metrics``. The
output is deterministic (no timestamps) so a test can require the committed JSON
to equal a fresh computation.

Counting rules that matter for interpretation are stated next to each metric:
papers screened are not papers used; declared dependencies are not effective
dependencies; named nodes are not distinct Boolean functions; software tests are
not biological validation.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import yaml

from dt_adoc.model.topology import parse_bnd_rules
from endotwin.model import dependencies, load_model
from endotwin.paths import ROOT
from endotwin.protocols import load_protocols
from endotwin.structure import summarize

OUT = ROOT / "docs" / "research_foundation_metrics.json"
SUITE_RECORDS = ROOT / "docs" / "verification" / "endotwin_suite_records.json"
REVIEW_PREFIXES = {"REF-001", "REF-002", "REF-003", "REF-004", "REF-005", "REF-045"}

LEGACY_VERSIONS = {
    "adoc-core-v0.1.0": "models/baseline/adoc-core-v0.1.0",
    "adoc-literature-v0.2.0": "models/extended/adoc-literature-v0.2.0",
    "adoc-literature-superset-v0.3.0": "models/superset/adoc-literature-superset-v0.3.0",
    "adoc-literature-superset-v0.4.0": "models/superset/adoc-literature-superset-v0.4.0",
    "adoc-literature-superset-v0.5.0": "models/superset/adoc-literature-superset-v0.5.0",
    "adoc-literature-superset-v0.5.1": "models/superset/adoc-literature-superset-v0.5.1",
    "adoc-literature-superset-v0.5.2": "models/superset/adoc-literature-superset-v0.5.2",
    "adoc-literature-superset-v0.6.0": "models/superset/adoc-literature-superset-v0.6.0",
}

#: Completed prototype analyses with the committed file holding each result.
COMPLETED_ANALYSES = [
    (
        "U5 structural, identifiability and design audit",
        "adoc-literature-superset-v0.5.0",
        "docs/u5_structural_audit/u5_audit_summary.json",
    ),
    (
        "U5b readout repair with paired transient comparison",
        "adoc-literature-superset-v0.5.1",
        "docs/v05_u5b_readout_repair.md",
    ),
    (
        "v0.5.2 HAND2-relay and PAEP-readout paired transient comparison",
        "adoc-literature-superset-v0.5.2",
        "docs/v052_paep_hand2/transient_comparison.tsv",
    ),
    (
        "v0.6.0 markerless-intervention gate G8 and structure recount",
        "adoc-literature-superset-v0.6.0",
        "docs/intervention_layer_stage3/structure_counts.json",
    ),
    (
        "Functional-endpoint replicates on disjoint seed blocks",
        "adoc-literature-superset-v0.5.0",
        "docs/endpoint/endpoint_replicates.tsv",
    ),
    (
        "MaBoSS seed-structure probe",
        "adoc-literature-superset-v0.5.0",
        "docs/endpoint/seed_structure_probe.json",
    ),
    (
        "Endpoint convergence finding",
        "adoc-literature-superset-v0.4.0",
        "docs/endpoint_convergence_finding.md",
    ),
    (
        "Model-data concordance (60 curated result rows)",
        "adoc-literature-superset-v0.4.0",
        "docs/concordance/concordance_table.tsv",
    ),
    (
        "C3a pre-registered kinetic readouts",
        "adoc-literature-superset-v0.5.2",
        "docs/c3_kinetic_readouts/classification.tsv",
    ),
    (
        "Progesterone-withdrawal perturbation cascade (historical)",
        "adoc-literature-superset-v0.5.1",
        "docs/perturbation_cascade/historical_v051/aggregate_timecourse.tsv",
    ),
    (
        "Perturbation cascade, two-seed reproducibility (stage C)",
        "adoc-literature-superset-v0.6.0",
        "docs/perturbation_cascade/stage_c/historical_comparison.tsv",
    ),
    (
        "Phase 1B closure and sensitivity inventory",
        "adoc-literature-superset-v0.5.1",
        "docs/phase1b_closure/phase1b_closure_summary.json",
    ),
    (
        "Stage 3 experiment selection (112 candidate fifth arms)",
        "adoc-literature-superset-v0.4.0",
        "docs/experiments/stage3_experiment_design.tsv",
    ),
    (
        "U8 Stage-3 rerank",
        "adoc-literature-superset-v0.5.1",
        "docs/experiments/u8_stage3_rerank/u8_rerank_summary.json",
    ),
    (
        "Experimental identifiability",
        "adoc-literature-superset-v0.4.0",
        "docs/identifiability_analysis.md",
    ),
    (
        "Identifiability-driven experimental design",
        "adoc-literature-superset-v0.6.0",
        "docs/identifiability_design/alias_pairs.tsv",
    ),
    (
        "Design-alias analysis of planned arms",
        "adoc-literature-superset-v0.4.0",
        "docs/design_alias_note.md",
    ),
    (
        "Gate 3a rule-variant discrimination",
        "adoc-literature-superset-v0.4.0",
        "docs/experiments/variant_discrimination.tsv",
    ),
    (
        "U6b MUC1 rule-family evaluation",
        "adoc-literature-superset-v0.5.1",
        "docs/u6b_muc1_reconciliation/family_members.tsv",
    ),
    (
        "Stage 4b veto expressivity (exact)",
        "adoc-literature-superset-v0.6.0",
        "docs/stage4b/v060_veto_expressivity.tsv",
    ),
    (
        "scRNA node-support audit (pre-registered)",
        "adoc-literature-superset-v0.4.0",
        "docs/scrna/node_support_findings.json",
    ),
    (
        "KLF12 prior battery and conditioning sweep",
        "adoc-literature-superset-v0.4.0",
        "docs/scrna/klf12_prior_finding.md",
    ),
    (
        "RNA versus MaBoSS endpoint concordance",
        "adoc-literature-superset-v0.5.1",
        "docs/rna_endpoint_concordance/concordance.tsv",
    ),
    (
        "Observation compartment attribution (C2)",
        "adoc-literature-superset-v0.5.1",
        "docs/c2_observation_compartments/attribution_report.md",
    ),
    (
        "Phase 2B external reference qualification (closed NO_SUITABLE_REFERENCE)",
        "adoc-literature-superset-v0.5.1",
        "docs/phase2b_c4/PHASE2B_CLOSED.md",
    ),
]


def _tsv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def literature() -> dict[str, object]:
    seed = _tsv("context/literature/searches/adhesion_routes_seed.tsv")
    refs = _tsv("context/literature/references.tsv")
    verification = _tsv("context/literature/citation_verification.tsv")
    pdfs = _tsv("context/literature/pdf_manifest.tsv")
    active = _tsv("context/literature/active_evidence_manifest.tsv")

    screen_text = (
        ROOT / "context/literature/reviews/adoc_2026-10-21_147_paper_screen.md"
    ).read_text("utf-8")
    screen_rows = re.findall(
        r"^\| \d+ \| \d+ \| .*? \| ([ABC]) — ", screen_text, re.MULTILINE
    )
    reaudit = (
        ROOT / "context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md"
    ).read_text("utf-8")
    stated = re.search(r"\*\*Corpus:\*\* (\d+) PDFs", reaudit)
    section15 = reaudit[reaudit.index("## 15.") :]
    pack = [
        int(n)
        for n in re.findall(r"^### 15\.[1-4] .*\((\d+)\)\s*$", section15, re.MULTILINE)
    ]
    active_keys = {(r["doi"].lower() or r["label"].lower()) for r in active}
    return {
        "seed_search_candidates": len(seed),
        "seed_search_unique_dois": len({r["doi"].lower() for r in seed if r["doi"]}),
        "bundle_screen_2026_10_21_papers": len(screen_rows),
        "bundle_screen_tiers": dict(sorted(Counter(screen_rows).items())),
        "reaudit_2026_09_28_stated_corpus_pdfs": int(stated.group(1))
        if stated
        else None,
        "reaudit_2026_09_28_enumerated_active_pack": sum(pack),
        "reaudit_2026_09_28_active_pack_breakdown": {
            "core": pack[0],
            "rule_variant": pack[1],
            "boundary": pack[2],
            "reviews": pack[3],
        }
        if len(pack) == 4
        else pack,
        "registered_references": len(refs),
        "registered_unique_dois": len({r["doi"].lower() for r in refs if r["doi"]}),
        "registered_crossref_resolved": sum(
            1 for r in verification if r["resolved"] == "true"
        ),
        "pdf_manifest_entries": len(pdfs),
        "pdf_manifest_full_text_inspected": sum(
            1 for r in pdfs if r["full_text_inspected"] == "yes"
        ),
        "active_evidence_manifest_rows": len(active),
        "active_evidence_unique_papers": len(active_keys),
        "note": (
            "The 163-PDF re-audit corpus is stated in the report but not enumerated in "
            "the repository; the 147-paper screen is of a different 2026-10-21 bundle; "
            "the corpora were never deduplicated against each other, so these counts "
            "must not be added."
        ),
    }


def evidence() -> dict[str, object]:
    rows = _tsv("context/evidence/edge_experimental_evidence.tsv")
    active = [r for r in rows if r["edge_status"] == "active"]
    graded = [r for r in active if r["source_verification"] == "full_text_verified"]
    primary_edges = {
        r["edge_id"]
        for r in active
        if r["reference_id"] and r["reference_id"] not in REVIEW_PREFIXES
    }
    edge_ev = _tsv("models/superset/adoc-literature-superset-v0.6.0/edge_evidence.tsv")
    topo = _tsv("models/superset/adoc-literature-superset-v0.6.0/topology.tsv")
    live = {r["edge_id"] for r in topo if r.get("provenance_status") == "declared"}
    adjudications = _tsv("config/edge_citation_adjudications.tsv")
    post = _tsv("context/evidence/post_closure_citation_adjudications_2026-11-18.tsv")
    best: dict[str, str] = {}
    rank = {"direct": 3, "partial": 2, "not_demonstrated": 1}
    for r in graded:
        if rank.get(r["edge_support"], 0) > rank.get(best.get(r["edge_id"], ""), 0):
            best[r["edge_id"]] = r["edge_support"]
    return {
        "experimental_evidence_rows": len(rows),
        "active_rows": len(active),
        "active_edges_with_rows": len({r["edge_id"] for r in active}),
        "active_unique_references": len(
            {r["reference_id"] for r in active if r["reference_id"]}
        ),
        "full_text_graded_rows": len(graded),
        "full_text_graded_edges": len({r["edge_id"] for r in graded}),
        "full_text_graded_references": len({r["reference_id"] for r in graded}),
        "graded_best_edge_support": dict(sorted(Counter(best.values()).items())),
        "v060_declared_edges": len(live),
        "v060_declared_edges_with_primary_reference": len(live & primary_edges),
        "v060_edge_confidence": dict(
            sorted(
                Counter(
                    r["confidence"] for r in edge_ev if r["edge_id"] in live
                ).items()
            )
        ),
        "citation_adjudications": len(adjudications) + len(post),
        "citation_adjudications_by_action": dict(
            sorted(Counter(r["action"] for r in adjudications + post).items())
        ),
    }


def network_versions() -> dict[str, object]:
    out: dict[str, object] = {}
    for version, path in LEGACY_VERSIONS.items():
        bnd = ROOT / path / "network.bnd"
        if not bnd.is_file():
            continue
        rules = parse_bnd_rules(bnd)
        deps = dependencies(rules)
        entry: dict[str, object] = {
            "nodes": len(rules),
            "dependencies": len(deps),
            "activations": sum(1 for s in deps.values() if s == "activation"),
            "inhibitions": sum(1 for s in deps.values() if s == "inhibition"),
            "cross_compartment_dependencies": sum(
                1
                for s, t in deps
                if s[:2] in {"E_", "S_"} and t[:2] in {"E_", "S_"} and s[:2] != t[:2]
            ),
        }
        if version.startswith("adoc-literature-superset"):
            outputs = tuple(n for n in rules if n.startswith("OUT_"))
            summary = summarize(rules, outputs)
            entry.update(
                {
                    "free_variables": len(summary.free_variables),
                    "distinct_boolean_functions": summary.distinct_functions,
                    "alias_classes": len(summary.alias_classes),
                    "absorbed_or_never_binding": len(
                        set(summary.absorbed_dependencies)
                        | set(summary.never_binding_inhibitions)
                    ),
                    "phenotype_inert_nodes": len(summary.phenotype_inert_nodes),
                    "unread_inputs": list(summary.unread_inputs),
                }
            )
        out[version] = entry
    return out


def alternatives_and_adjudication() -> dict[str, object]:
    gate3 = _tsv("context/literature/reviews/gate3_candidate_variants_2026-09-16.tsv")
    u6b = _tsv("docs/u6b_muc1_reconciliation/family_members.tsv")
    discrimination = _tsv("docs/experiments/variant_discrimination.tsv")
    deferred = _tsv("docs/deferred_topology_register.tsv")
    dispositions = _tsv(
        "context/literature/reviews/deep_research_adhesion_model_2026-09-11.candidate-node-dispositions.tsv"
    )
    unresolved = _tsv(
        "models/superset/adoc-literature-superset-v0.6.0/unresolved_mechanisms.tsv"
    )
    v060_variants = _tsv(
        "models/superset/adoc-literature-superset-v0.6.0/rule_variants.tsv"
    )
    return {
        "gate3_candidate_rule_variants": len(gate3),
        "u6b_muc1_family_members": len(u6b),
        "variant_discrimination_pairs": len(discrimination),
        "v060_rule_variant_ids": len({r["variant_id"] for r in v060_variants}),
        "rules_changed_after_literature_reaudit": 2,
        "rules_changed_after_literature_reaudit_ids": [
            "v0.5.2 C1 (PAEP readout)",
            "v0.5.2 C5 (HAND2 stromal relay)",
        ],
        "deferred_topology_register_rows": len(deferred),
        "candidate_node_dispositions": len(dispositions),
        "candidate_node_disposition_counts": dict(
            sorted(Counter(r["final_disposition"] for r in dispositions).items())
        ),
        "unresolved_mechanisms_v060": len(unresolved),
    }


def experimental_data() -> dict[str, object]:
    proteins = _tsv("input_tables/adoc_secreted_proteins.tsv")
    states = Counter((r["protein"], r["measurement_state"]) for r in proteins)
    calibration = yaml.safe_load((ROOT / "config/calibration.yaml").read_text("utf-8"))
    adhesion = {}
    for row in calibration.get("adhesion_objective", {}).get("readouts", []) or []:
        adhesion[row["protocol_id"]] = f"{row['successes']}/{row['trials']}"
    scrna = json.loads(
        (ROOT / "docs/phase2a/scrna_metadata_extraction.json").read_text("utf-8")
    )
    by_sample: Counter[str] = Counter()
    by_type: Counter[str] = Counter()
    for group in scrna["groups"]:
        by_sample[group["sample_id"]] += int(group["n_cells"])
        by_type[group["celltype_v2"]] += int(group["n_cells"])
    epithelial = sum(n for t, n in by_type.items() if "pitheli" in t)
    obs_map = _tsv("config/observation_model_map.tsv")
    return {
        "secreted_protein_rows": len(proteins),
        "secreted_protein_states": {
            f"{p}:{s}": n for (p, s), n in sorted(states.items())
        },
        "secreted_protein_observed_values": sum(
            1 for r in proteins if r["measurement_state"] == "observed"
        ),
        "adhesion_counts": adhesion,
        "adhesion_embryos": sum(int(v.split("/")[1]) for v in adhesion.values()),
        "scrna_accession": "E-MTAB-15842",
        "scrna_cells": int(scrna["n_cells"]),
        "scrna_samples": len(by_sample),
        "scrna_donors": len({s.split("TE_")[0] for s in by_sample}),
        "scrna_cell_state_labels": len(by_type),
        "scrna_epithelial_cells": epithelial,
        "scrna_stromal_cells": int(scrna["n_cells"]) - epithelial,
        "observation_map_rows_v060": len(obs_map),
        "observation_map_status_counts": dict(
            sorted(Counter(r["activation_status"] for r in obs_map).items())
        ),
    }


def analyses() -> list[dict[str, object]]:
    return [
        {
            "analysis": name,
            "model_version": version,
            "result_file": path,
            "exists": (ROOT / path).is_file(),
        }
        for name, version, path in COMPLETED_ANALYSES
    ]


def mainline() -> dict[str, object]:
    model = load_model()
    protocols = load_protocols(model)
    summary = summarize(model.rules, model.outputs, model.readout_nodes)
    edges = [e for e in model.edges if e["in_default_network"] == "true"]
    return {
        "model_version": model.version,
        "structure": summary.as_dict(),
        "cross_compartment_dependencies": sum(
            1
            for e in edges
            if e["crossing"] in {"epithelium_to_stroma", "stroma_to_epithelium"}
        ),
        "edge_evidence_classes": dict(
            sorted(Counter(e["evidence_class"] for e in edges).items())
        ),
        "variant_only_edges": sum(
            1 for e in model.edges if e["in_default_network"] == "false"
        ),
        "rule_variant_families": {
            f: list(v) for f, v in sorted(model.families().items())
        },
        "rule_variant_scenarios": len(model.scenarios()),
        "references": len(_tsv("endotwin/evidence/references.tsv")),
        "protocol_conditions": len(protocols.conditions),
        "matched_comparisons": len(protocols.comparisons),
        "interventions": len(protocols.interventions),
    }


def software_verification() -> dict[str, object]:
    if not SUITE_RECORDS.is_file():
        return {"status": "no suite record committed"}
    return json.loads(SUITE_RECORDS.read_text("utf-8"))


def compute() -> dict[str, object]:
    return {
        "generated_by": "endotwin.foundation_metrics (pixi run endotwin-metrics)",
        "prototype_source_commit": "b1de5f90582f02291789eb72753fa5ab1f2d8c88",
        "literature": literature(),
        "evidence": evidence(),
        "network_versions": network_versions(),
        "alternatives_and_adjudication": alternatives_and_adjudication(),
        "experimental_data": experimental_data(),
        "completed_analyses": analyses(),
        "endotwin_mainline": mainline(),
        "software_verification": software_verification(),
    }


def write(path: Path = OUT) -> dict[str, object]:
    payload = compute()
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return payload


if __name__ == "__main__":  # pragma: no cover
    write()
