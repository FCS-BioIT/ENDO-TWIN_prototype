"""U5 -- structural audit and identifiability rerun on the v0.5 development line.

Defined in ``docs/v05_mechanistic_integration_plan.md`` §17 (U5):

* recompute Δ (distinct Boolean functions against the v0.4 baseline) and confirm
  which alias classes actually broke;
* rerun identifiability and design-alias, carrying the matched-unit caveat onto
  every number (§13.12).

Everything is **recomputed** from each model directory through the same
resolvers the rest of the repository uses (``structure.load_structure``,
``identifiability.load_identifiability`` / ``compute_gain``,
``design_alias.load_design_alias`` with the plan resolved against the audited
model) and then **compared**, never copied. File-level byte identity is recorded
beside the recomputation because the two answer different questions: identity
says the inputs cannot differ; recomputation says the v0.5 path is actually the
one read, so a resolver that silently fell back to v0.4 would not pass as an
audit.

No rule, node, edge, threshold, rate, condition or phenotype is changed here.
The audit writes only under ``docs/u5_structural_audit/``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from dt_adoc.model.provenance import repo_root

AUDITED = "adoc-literature-superset-v0.5.0"
BASELINE = "adoc-literature-superset-v0.4.0"
OUTPUT_DIR = Path("docs/u5_structural_audit")
SUMMARY_JSON = OUTPUT_DIR / "u5_audit_summary.json"
NODE_TSV = OUTPUT_DIR / "u5_node_audit.tsv"

#: Carried verbatim onto every design-dependent block (plan §13.12). The
#: structural half -- nodes, dependencies, free variables, distinct functions,
#: exact aliases, absorbed edges, inert nodes, unread inputs -- is a property of
#: network.bnd alone and does not need it; everything that depends on which arms
#: exist does.
MATCHED_UNIT_CAVEAT = (
    "MATCHED-UNIT CONDITIONAL. Design-equivalence classes, observation classes, "
    "information statuses and proposed-panel counts assume one biological unit "
    "carries a single latent assignment through every arm and assay. ADOC does "
    "not provide that: adhesion is an aggregate per-embryo count, the secreted-"
    "protein mappings are unpaired, chips can share donors and epithelial and "
    "stromal cells in one chip may come from different donors, and the "
    "column-to-chip mapping for IGFBP-1 and PRL was lost "
    "(config/adoc_chip_donor_provenance.tsv). These numbers describe what a "
    "matched-unit design of this shape could identify, NOT what the current "
    "data identify."
)


#: The files U1 was allowed to change. Anything else differing is a finding.
SCAFFOLD_METADATA_FILES = frozenset(
    {"provenance.toml", "README.md", "executable_model_manifest.tsv"}
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_identity(root: Path) -> dict[str, Any]:
    """Per-file byte comparison of the two model directories."""
    from dt_adoc.model.runtime import resolve_model

    audited = resolve_model(AUDITED, root)
    baseline = resolve_model(BASELINE, root)
    left = audited.network_bnd.parent
    right = baseline.network_bnd.parent
    names = sorted(
        {str(p.relative_to(left)) for p in left.rglob("*") if p.is_file()}
        | {str(p.relative_to(right)) for p in right.rglob("*") if p.is_file()}
    )
    differing, identical, only_one = [], [], []
    for name in names:
        a, b = left / name, right / name
        if not (a.is_file() and b.is_file()):
            only_one.append(name)
        elif a.read_bytes() == b.read_bytes():
            identical.append(name)
        else:
            differing.append(name)
    unexpected = [n for n in differing + only_one if n not in SCAFFOLD_METADATA_FILES]
    return {
        "audited_dir": str(left.relative_to(root)),
        "baseline_dir": str(right.relative_to(root)),
        "files_compared": len(names),
        "identical": len(identical),
        "differing": differing,
        "present_in_one_only": only_one,
        "unexpected_differences": unexpected,
        "executable_byte_identical": not unexpected,
        "network_bnd_sha256": _sha256(audited.network_bnd),
    }


def _structural(model_version: str, root: Path) -> dict[str, Any]:
    from dt_adoc.reporting.network_overview import measurement_tiers
    from dt_adoc.reporting.structure import load_structure, structural_summary

    facts = load_structure(model_version, root)
    summary = structural_summary(facts)
    dead = set(facts.absorbed_edges) | set(facts.never_binding_inhibitions)
    return {
        "summary": summary,
        "absorbed_or_never_binding_dependencies": len(dead),
        "alias_classes": sorted(sorted(m) for m in facts.alias_classes),
        "complement_pairs": sorted(list(p) for p in facts.complement_pairs),
        "absorbed_dependencies": sorted(list(p) for p in facts.absorbed_edges),
        "never_binding_inhibitions": sorted(
            list(p) for p in facts.never_binding_inhibitions
        ),
        "phenotype_inert_nodes": sorted(facts.phenotype_inert),
        "unread_inputs": sorted(facts.unread_inputs),
        "free_variables": sorted(facts.free),
        "measurement_tiers": dict(sorted(measurement_tiers(facts, root).items())),
        "_facts": facts,
    }


def _identifiability(model_version: str, root: Path) -> dict[str, Any]:
    from dt_adoc.reporting.identifiability import (
        adhesion_endpoint_decomposition,
        compute_gain,
        identifiability_summary,
        load_identifiability,
    )

    facts = load_identifiability(model_version, root)
    gain = compute_gain(facts, root)
    endpoint = adhesion_endpoint_decomposition(facts, root)
    endpoint.pop("baseline_cfg", None)
    return {
        "matched_unit_caveat": MATCHED_UNIT_CAVEAT,
        "summary": identifiability_summary(facts),
        "ceilings": {
            "design_states_now": gain.baseline_design_classes,
            "design_states_with_proposed_arms": gain.greedy_arms[-1][1],
            "design_states_ceiling": gain.global_ceiling,
            "observation_classes_now": gain.baseline_fibers,
            "observation_classes_assayable_ceiling": gain.assayable_latent_ceiling,
            "observation_classes_ceiling": gain.latent_ceiling,
        },
        "greedy_arms": [list(a) for a in gain.greedy_arms],
        "greedy_readouts": [list(r) for r in gain.greedy_readouts],
        "design_classes": sorted(sorted(m) for m in facts.design_classes),
        "information_status": dict(sorted(facts.information_status.items())),
        "perturbation_status": dict(sorted(facts.perturbation_status.items())),
        "latent": list(facts.latent),
        "independently_perturbed": list(facts.independently_perturbed),
        "set_alone_no_shared_readout": list(facts.set_alone_no_shared_readout),
        "adhesion_endpoint": endpoint,
        "_facts": facts,
    }


def _design_alias(
    model_version: str, root: Path, variant: str | None
) -> dict[str, Any]:
    from dt_adoc.reporting.design_alias import (
        _Enumerator,
        candidate_fifth_arms,
        design_alias_summary,
        load_design_alias,
    )
    from dt_adoc.reporting.identifiability import load_identifiability

    recorded = load_identifiability(model_version, root)
    facts = load_design_alias(
        root, variant, facts=recorded, model_version=model_version
    )
    enumerator = _Enumerator(model_version, root)
    candidates = candidate_fifth_arms(facts, root, enumerator=enumerator)
    return {
        "matched_unit_caveat": MATCHED_UNIT_CAVEAT,
        "variant": variant or "as_declared",
        "summary": design_alias_summary(facts, candidates),
        "design_classes": sorted(sorted(m) for m in facts.design_classes),
        "category": dict(sorted(facts.category.items())),
        "candidate_gains": sorted(
            [c.candidate_id, c.gain, sorted(map(list, c.separated_measured_pairs))]
            for c in candidates
        ),
        "_facts": facts,
    }


def _strip(block: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in block.items() if not k.startswith("_")}


def _comparable(block: dict[str, Any]) -> Any:
    """A block with model-version labels removed, for equality testing."""
    text = json.dumps(_strip(block), sort_keys=True)
    return json.loads(text.replace(AUDITED, "<model>").replace(BASELINE, "<model>"))


def audit_model(model_version: str, root: Path) -> dict[str, Any]:
    return {
        "structural": _structural(model_version, root),
        "identifiability": _identifiability(model_version, root),
        "design_alias": {
            variant or "as_declared": _design_alias(model_version, root, variant)
            for variant in (None, "maternal_phase_only")
        },
    }


def measured_node_implications(audit: dict[str, Any]) -> list[dict[str, Any]]:
    """For each ADOC-touched node: what else its reading stands for.

    ``structural_alias_class`` is design-independent -- reading the node reads
    every member, under any experiment. ``design_class`` is matched-unit
    conditional and depends on the declared four-arm plan.
    """
    structural = audit["structural"]
    tiers = structural["measurement_tiers"]
    alias_of = {n: m for m in structural["alias_classes"] for n in m}
    design = audit["design_alias"]["as_declared"]
    design_of = {n: m for m in design["design_classes"] for n in m}
    status = audit["identifiability"]["information_status"]
    return [
        {
            "node_id": node_id,
            "measurement_tier": tier,
            "structural_alias_class": alias_of.get(node_id, [node_id]),
            "design_class_as_declared_plan": design_of.get(node_id, [node_id]),
            "information_status": status.get(node_id, ""),
            "matched_unit_conditional_fields": [
                "design_class_as_declared_plan",
                "information_status",
            ],
        }
        for node_id, tier in sorted(tiers.items())
    ]


def compare(audited: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    """Δ and alias breakage, plus a block-by-block equality verdict."""
    a_struct, b_struct = audited["structural"], baseline["structural"]
    a_classes = {tuple(m) for m in a_struct["alias_classes"]}
    b_classes = {tuple(m) for m in b_struct["alias_classes"]}
    blocks = {
        "structural": (a_struct, b_struct),
        "identifiability": (audited["identifiability"], baseline["identifiability"]),
        **{
            f"design_alias.{k}": (
                audited["design_alias"][k],
                baseline["design_alias"][k],
            )
            for k in audited["design_alias"]
        },
    }
    return {
        "delta_distinct_boolean_functions": (
            a_struct["summary"]["distinct_functions"]
            - b_struct["summary"]["distinct_functions"]
        ),
        "baseline_distinct_boolean_functions": b_struct["summary"][
            "distinct_functions"
        ],
        "alias_classes_broken": sorted(list(m) for m in b_classes - a_classes),
        "alias_classes_new": sorted(list(m) for m in a_classes - b_classes),
        "recomputed_blocks_identical": {
            name: _comparable(a) == _comparable(b) for name, (a, b) in blocks.items()
        },
    }


def build_audit(root: Path | None = None) -> tuple[dict[str, Any], str, str]:
    """The summary payload and the exact bytes of both tracked outputs."""
    active_root = root or repo_root()
    audited = audit_model(AUDITED, active_root)
    baseline = audit_model(BASELINE, active_root)
    comparison = compare(audited, baseline)
    identity = file_identity(active_root)

    payload = {
        "schema_version": "1.0",
        "unit": "U5",
        "plan": "docs/v05_mechanistic_integration_plan.md §17 U5",
        "audited_model": AUDITED,
        "baseline_model": BASELINE,
        "claim_boundary": (
            "Structural and design-identifiability facts computed by exhaustive "
            "enumeration over the model's free variables. No simulation, rate, "
            "horizon or fitted parameter enters. Design and identifiability blocks "
            "carry the matched-unit caveat; the structural block does not need it."
        ),
        "matched_unit_caveat": MATCHED_UNIT_CAVEAT,
        "file_identity": identity,
        "comparison": comparison,
        "audited": {
            "structural": _strip(audited["structural"]),
            "identifiability": _strip(audited["identifiability"]),
            "design_alias": {k: _strip(v) for k, v in audited["design_alias"].items()},
        },
        "measured_node_implications": measured_node_implications(audited),
        "inputs": {
            relative: _sha256(active_root / relative)
            for relative in (
                "config/planned_design.yaml",
                "config/observation_model_map.tsv",
                "config/calibration.yaml",
                "config/visualization.yaml",
            )
        },
        "generator_files": {
            relative: _sha256(active_root / relative)
            for relative in (
                "src/dt_adoc/reporting/u5_structural_audit.py",
                "src/dt_adoc/reporting/structure.py",
                "src/dt_adoc/reporting/identifiability.py",
                "src/dt_adoc/reporting/design_alias.py",
                "src/dt_adoc/reporting/network_overview.py",
            )
        },
    }
    return (
        payload,
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        node_table_text(audited),
    )


def run_audit(root: Path | None = None) -> dict[str, Any]:
    active_root = root or repo_root()
    payload, summary_text, node_text = build_audit(active_root)
    (active_root / OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    (active_root / SUMMARY_JSON).write_text(summary_text, encoding="utf-8")
    (active_root / NODE_TSV).write_text(node_text, encoding="utf-8")
    return payload


NODE_COLUMNS = (
    "node_id",
    "compartment",
    "free_variable",
    "depth",
    "structural_alias_class",
    "phenotype_inert",
    "unread_input",
    "measurement_tier",
    "design_class_as_declared",
    "design_category_as_declared",
    "information_status",
    "perturbation_status",
    "matched_unit_conditional",
)


def node_table_text(audited: dict[str, Any]) -> str:
    facts = audited["structural"]["_facts"]
    structural = audited["structural"]
    identifiability = audited["identifiability"]
    design = audited["design_alias"]["as_declared"]
    alias_of = {n: m for m in structural["alias_classes"] for n in m}
    design_of = {n: m for m in design["design_classes"] for n in m}
    rows = [
        {
            "node_id": node_id,
            "compartment": facts.compartment_of.get(node_id, ""),
            "free_variable": str(node_id in facts.free).lower(),
            "depth": facts.depth[node_id],
            "structural_alias_class": ";".join(alias_of.get(node_id, [node_id])),
            "phenotype_inert": str(node_id in facts.phenotype_inert).lower(),
            "unread_input": str(node_id in facts.unread_inputs).lower(),
            "measurement_tier": structural["measurement_tiers"].get(
                node_id, "unmeasured"
            ),
            "design_class_as_declared": ";".join(design_of.get(node_id, [node_id])),
            "design_category_as_declared": design["category"].get(node_id, ""),
            "information_status": identifiability["information_status"].get(
                node_id, ""
            ),
            "perturbation_status": identifiability["perturbation_status"].get(
                node_id, ""
            ),
            "matched_unit_conditional": (
                "design_class_as_declared;design_category_as_declared;"
                "information_status;perturbation_status"
            ),
        }
        for node_id in facts.node_ids
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=NODE_COLUMNS, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main() -> int:
    payload = run_audit()
    comparison = payload["comparison"]
    print(
        json.dumps(
            {
                "executable_byte_identical": payload["file_identity"][
                    "executable_byte_identical"
                ],
                "delta": comparison["delta_distinct_boolean_functions"],
                "alias_classes_broken": comparison["alias_classes_broken"],
                "recomputed_blocks_identical": comparison[
                    "recomputed_blocks_identical"
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
