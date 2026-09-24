"""Phase-1B closure audit and the prospective `dropout_e2` handoff.

Two separate outputs, built by one deterministic generator:

1. **The closure audit.** Every Phase-1B roadmap item and exit-gate criterion
   (`docs/roadmap.md`, "Phase 1B") is given a status from a fixed vocabulary,
   with the artifacts it rests on, what was actually tested, the current claim
   ceiling, the limitation and what would unblock it. The overall status is
   **derived** from the exit-gate rows by :func:`derive_overall_status`, a rule
   fixed in code before the rows are read. It is not chosen.
2. **The handoff.** An execution-facing restatement of the frozen Stage-3
   design (`docs/stage3_experiment_selection.md` §4, §5, §9 and §12, frozen
   2026-09-17). It is joined to the owner's pre-run analysis addendum of
   2026-09-24, which closes eight interpretation gaps found before any
   prospective data exist. The frozen document is read and digest-pinned, and
   never written.

Nothing here simulates or edits a model. The audit's computed premises are
exact Boolean fixed-point expectations on the adopted
`adoc-literature-superset-v0.5.1`, obtained by the same latent-variable
enumeration as `reporting.endpoint_replicates.exact_converged_endpoint`,
widened to more nodes and arms. Each curated status that rests on a computed
premise is tied to it. If a premise moves, the build refuses to run instead of
publishing a status the model no longer supports.

The handoff quotes the frozen design rather than restating it from memory. The
quoted phrases are rendered from the frozen text itself, and the §5 table is
copied cell for cell. `check_handoff_against_frozen` asserts that the handoff's
own dose, day, compartment, assay-outlet and replication statements agree with
those quotes. Doses are cross-checked against `config/protocols.yaml`, and bands
are recomputed from `input_tables/adoc_secreted_proteins.tsv`. Any divergence
stops the build. The remaining bench prose is a restatement governed by the
quotes and the addendum.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path
from typing import Any

from dt_adoc.calibration.adhesion_likelihood import (
    STRUCTURALLY_CONTRADICTED,
    is_rankable,
    structural_verdict,
)
from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting.identifiability import (
    _evaluate,
    _latent_seeds,
    _parse_cfg_inputs,
    load_design,
    parse_cfg_probabilities,
    repo_root,
)
from dt_adoc.reporting.structure import _topological_order

TASK = "build-phase1b-closure"
ADOPTED_VERSION = "adoc-literature-superset-v0.5.1"
ADDENDUM_DATE = "2026-09-24"
FROZEN_DATE = "2026-09-17"

OUT_DIR = Path("docs/phase1b_closure")
OUT_EXIT_GATE = OUT_DIR / "phase1b_exit_gate.tsv"
OUT_CLAIMS = OUT_DIR / "phase1b_claims.tsv"
OUT_SENSITIVITY = OUT_DIR / "sensitivity_inventory.tsv"
OUT_HANDOFF_TSV = OUT_DIR / "prospective_dropout_e2_handoff.tsv"
OUT_ADDENDUM = OUT_DIR / "pre_run_analysis_addendum.tsv"
OUT_HANDOFF_MD = OUT_DIR / "prospective_dropout_e2_handoff.md"
OUT_SUMMARY = OUT_DIR / "phase1b_closure_summary.json"
OUT_ALLOCATION = OUT_DIR / "prospective_allocation_manifest_template.tsv"
OUT_ASSAY_METADATA = OUT_DIR / "prospective_assay_metadata_template.tsv"
OUTPUTS = (
    OUT_EXIT_GATE,
    OUT_CLAIMS,
    OUT_SENSITIVITY,
    OUT_HANDOFF_TSV,
    OUT_ADDENDUM,
    OUT_HANDOFF_MD,
    OUT_SUMMARY,
    OUT_ALLOCATION,
    OUT_ASSAY_METADATA,
)

ROADMAP = Path("docs/roadmap.md")
CALIBRATION = Path("config/calibration.yaml")
OBSERVATION_MAP = Path("config/observation_model_map.tsv")
PROTOCOLS = Path("config/protocols.yaml")
PROTEINS = Path("input_tables/adoc_secreted_proteins.tsv")
FROZEN_SELECTION = Path("docs/stage3_experiment_selection.md")
FROZEN_TABLES = Path("docs/experiments/stage3_decision_tables.md")
FROZEN_DESIGN_TSV = Path("docs/experiments/stage3_experiment_design.tsv")
FROZEN_DESIGN_MD = Path("docs/experiments/stage3_experiment_design.md")
U8_SUMMARY = Path("docs/experiments/u8_stage3_rerank/u8_rerank_summary.json")

#: The four frozen Stage-3 artifacts, pinned to the same literals U8 pins them
#: to (`tests/unit/test_v05_u8_stage3_rerank.py::FROZEN_DIGESTS`). The build
#: refuses to run if any has changed, because every handoff value is read from
#: them.
FROZEN_DIGESTS = {
    str(
        FROZEN_DESIGN_TSV
    ): "987d75644925346fab73e7251067094d04c01883af783a83c3775705b444ee74",
    str(
        FROZEN_DESIGN_MD
    ): "7368b1f85007f677cd16c5f308d9571f9573a83771b3dfdb2bb34b593b068520",
    str(
        FROZEN_TABLES
    ): "a2cc7291adfaf130f79f345201a30556ab16c9391c8598315a5735d6b0c3305b",
    str(
        FROZEN_SELECTION
    ): "e6a5fa558bede27f20b329cfbfe7bd3ec90d4d41c0f5091ed52e3dd4cbdb113c",
}

SATISFIED = "SATISFIED"
PARTIALLY_SATISFIED = "PARTIALLY_SATISFIED"
NOT_SATISFIED = "NOT_SATISFIED"
NOT_APPLICABLE = "NOT_APPLICABLE"
STATUSES = (SATISFIED, PARTIALLY_SATISFIED, NOT_SATISFIED, NOT_APPLICABLE)

#: How an unmet criterion could become met. `NO_SCHEDULED_ROUTE` means no
#: dataset or unit in the current plan can supply what it needs.
IN_REPO_WORK = "IN_REPO_WORK"
PROSPECTIVE_DATA = "PROSPECTIVE_DATA_DROPOUT_E2"
NO_SCHEDULED_ROUTE = "NO_SCHEDULED_ROUTE"
NONE_REQUIRED = "NONE_REQUIRED"

CLOSED = "CLOSED"
PARTIAL = "PARTIAL"
BLOCKED = "BLOCKED"

OVERALL_RULE = (
    "Computed from the exit-gate rows (kind=exit_gate) only; roadmap-item rows "
    "are the work that feeds them and are reported, not gated. CLOSED iff every "
    "exit-gate row is SATISFIED or NOT_APPLICABLE. Otherwise BLOCKED iff at "
    "least one unmet exit-gate row has unblock_route=NO_SCHEDULED_ROUTE, i.e. "
    "nothing in the current plan can supply what it needs. Otherwise PARTIAL "
    "(every unmet row has a scheduled route: in-repository work or the frozen "
    "prospective experiment)."
)

EXIT_GATE_COLUMNS = (
    "criterion_id",
    "kind",
    "criterion_verbatim",
    "audited_scope",
    "status",
    "evidence_artifacts",
    "what_was_tested",
    "current_claim",
    "limitation",
    "unblock_requirement",
    "unblock_route",
    "computed_premises",
)
CLAIM_COLUMNS = ("claim_id", "permission", "statement", "basis", "ceiling_source")
SENSITIVITY_COLUMNS = (
    "kind",
    "status",
    "model_version",
    "artifacts",
    "what_was_run",
    "what_was_not_run",
)
HANDOFF_COLUMNS = (
    "row_id",
    "arm",
    "protocol_timing",
    "reagent_dose",
    "compartment",
    "assay",
    "timepoint",
    "biological_replicate",
    "technical_replicate_policy",
    "integrity_control",
    "interpretation_rule",
    "failure_indeterminate_rule",
    "frozen_source",
)
ADDENDUM_COLUMNS = (
    "gap_id",
    "addendum_round",
    "record_type",
    "decided_on",
    "decided_by",
    "status",
    "gap",
    "decision",
    "frozen_text_it_resolves",
)


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_sha(root: Path, relative: Path) -> str:
    """One digest over every file under a directory: its path and its bytes."""
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


#: The roadmap words each audited criterion quotes. Checked verbatim against the
#: roadmap's Phase-1B section, so a reworded roadmap stops the build rather than
#: leaving the audit answering a question nobody asks any more.
ROADMAP_QUOTES = {
    "R1": "Calibrate only pre-declared initial-state/rate alternatives against untreated and HT molecular/adhesion data.",
    "R2": "Quantify seed and trajectory stability.",
    "R3a": "Perform one-at-a-time and global sensitivity over uncertain thresholds, rates, initial states, and alternative rules.",
    "R3b": "Perform one-at-a-time and global sensitivity over uncertain thresholds, rates, initial states, and alternative rules.",
    "R3c": "Perform one-at-a-time and global sensitivity over uncertain thresholds, rates, initial states, and alternative rules.",
    "R3d": "Perform one-at-a-time and global sensitivity over uncertain thresholds, rates, initial states, and alternative rules.",
    "R3e": "Perform one-at-a-time and global sensitivity over uncertain thresholds, rates, initial states, and alternative rules.",
    "R4a": "Test the frozen mifepristone perturbation as held-out validation if it was not used in construction.",
    "R4b": "Test the frozen mifepristone perturbation as held-out validation if it was not used in construction.",
    "R5": "Report ensembles of acceptable models when parameters are not identifiable.",
    "E1": "the model reproduces qualitative molecular directions",
    "E2": "gives uncertainty-aware adhesion agreement",
    "E3": "predicts the held-out perturbation",
    "E4": "does not depend on one fragile assumption",
}


def roadmap_phase1b(root: Path) -> str:
    text = (root / ROADMAP).read_text(encoding="utf-8")
    return _section(text, "## Phase 1B")


def check_roadmap(root: Path) -> str:
    section = roadmap_phase1b(root)
    for criterion, quote in ROADMAP_QUOTES.items():
        _require(section, quote, f"roadmap Phase 1B ({criterion})")
    return hashlib.sha256(section.encode("utf-8")).hexdigest()


def _check_frozen(root: Path) -> None:
    for relative, expected in FROZEN_DIGESTS.items():
        actual = _sha(root / relative)
        if actual != expected:
            raise RuntimeError(
                f"{relative} is not the frozen Stage-3 artifact "
                f"(sha256 {actual}, frozen {expected}); the handoff is read from "
                "it and must not be built against a different text"
            )


def _section(text: str, heading: str) -> str:
    """The body of one `## ` section, from its heading to the next one."""
    start = text.index(heading)
    following = text.find("\n## ", start + len(heading))
    return text[start : following if following != -1 else len(text)]


def _require(text: str, phrase: str, where: str) -> str:
    """A handoff value is carried only if the frozen text states it verbatim."""
    squashed = re.sub(r"\s+", " ", text)
    if phrase not in squashed:
        raise RuntimeError(f"frozen {where} no longer states {phrase!r}")
    return phrase


def load_calibration(root: Path) -> dict[str, Any]:
    import yaml

    return yaml.safe_load((root / CALIBRATION).read_text(encoding="utf-8"))


def load_observation_map(root: Path) -> list[dict[str, str]]:
    with (root / OBSERVATION_MAP).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _protocol_notes(root: Path) -> dict[str, str]:
    import yaml

    payload = yaml.safe_load((root / PROTOCOLS).read_text(encoding="utf-8"))
    notes: dict[str, str] = {}
    for protocol in payload["protocols"]:
        for step in protocol.get("steps", []):
            notes.setdefault(step["step_id"], step.get("duration_note", ""))
    return notes


# --------------------------------------------------------------------------
# Computed premises on the adopted model
# --------------------------------------------------------------------------


def exact_fixed_point(
    model_version: str, root: Path, arm_ids: tuple[str, ...], nodes: tuple[str, ...]
) -> dict[str, dict[str, float]]:
    """Exact fixed-point expectation of each node in each arm, by enumeration.

    The same computation as `exact_converged_endpoint`. Probabilistic latent
    free variables take their `baseline.cfg` prior and deterministic ones their
    cfg value, and each assignment contributes its unique fixed point.
    """
    spec = resolve_model(model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    free = {n for n in rules if rules[n].strip() == n}
    order = _topological_order(rules, free)
    arms, _controlled, _held_off, latent = load_design(model_version, root)
    by_id = {arm.arm_id: arm for arm in arms}
    priors = parse_cfg_probabilities(spec.baseline_cfg)
    fixed = _parse_cfg_inputs(spec.baseline_cfg)
    seeds, states, mask = _latent_seeds(latent)
    weights = []
    for index in range(states):
        weight = 1.0
        for node_id in latent:
            bit = (seeds[node_id] >> index) & 1
            if node_id in priors:
                weight *= priors[node_id] if bit else 1.0 - priors[node_id]
            elif bit != int(fixed.get(node_id, False)):
                weight = 0.0
                break
        weights.append(weight)
    result: dict[str, dict[str, float]] = {}
    for arm_id in arm_ids:
        columns = _evaluate(rules, order, seeds, mask, by_id[arm_id].inputs)
        result[arm_id] = {
            node: round(
                sum(w for i, w in enumerate(weights) if (columns[node] >> i) & 1), 12
            )
            for node in nodes
        }
    return result


def on_in_any_weighted_assignment(
    model_version: str, root: Path, arm_id: str, node: str
) -> bool:
    """Whether `node` is ON at the fixed point of ANY latent assignment the cfg weights.

    This is the per-assignment statement, as distinct from the expectation that
    `exact_fixed_point` returns.
    """
    spec = resolve_model(model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    free = {n for n in rules if rules[n].strip() == n}
    order = _topological_order(rules, free)
    arms, _controlled, _held_off, latent = load_design(model_version, root)
    by_id = {arm.arm_id: arm for arm in arms}
    priors = parse_cfg_probabilities(spec.baseline_cfg)
    fixed = _parse_cfg_inputs(spec.baseline_cfg)
    seeds, states, mask = _latent_seeds(latent)
    column = _evaluate(rules, order, seeds, mask, by_id[arm_id].inputs)[node]
    for index in range(states):
        weighted = True
        for node_id in latent:
            bit = (seeds[node_id] >> index) & 1
            if node_id in priors:
                if priors[node_id] in (0.0, 1.0) and bit != int(priors[node_id]):
                    weighted = False
            elif bit != int(fixed.get(node_id, False)):
                weighted = False
        if weighted and (column >> index) & 1:
            return True
    return False


def _acyclic_given_free(model_version: str, root: Path) -> dict[str, Any]:
    """Whether every non-free node is ordered by its parents.

    If so, each free-variable assignment has exactly one fixed point, reached
    under any positive transition rates. That is the ground on which the
    fixed-point claims do not depend on rates.
    """
    spec = resolve_model(model_version, root)
    rules = parse_bnd_rules(spec.network_bnd)
    free = {n for n in rules if rules[n].strip() == n}
    order = _topological_order(rules, free)
    return {
        "nodes": len(rules),
        "free_variables": len(free),
        "ordered_non_free_nodes": len(order),
        "acyclic_given_free_variables": len(order) == len(rules) - len(free),
    }


def _rule(model_version: str, root: Path, node: str) -> str:
    spec = resolve_model(model_version, root)
    return " ".join(parse_bnd_rules(spec.network_bnd)[node].split())


ADHESION_ARMS = (
    ("untreated", "adhesion_challenge_basal"),
    ("hormone_treated", "adhesion_challenge_hormone_treated"),
    ("hormone_treated_mifepristone", "adhesion_challenge_hormone_treated_mifepristone"),
)
MATERNAL_ARMS = ("basal_maternal", "e2_primed_maternal", "hormone_treated_maternal")


def compute_premises(root: Path) -> dict[str, Any]:
    """Every computed fact a curated status below rests on."""
    calibration = load_calibration(root)
    objective = calibration["adhesion_objective"]
    readouts = {r["protocol_id"]: r for r in objective["readouts"]}
    om = {row["mapping_id"]: row for row in load_observation_map(root)}

    adhesion = exact_fixed_point(
        ADOPTED_VERSION,
        root,
        tuple(p for _, p in ADHESION_ARMS),
        ("OUT_STABLE_ADHESION",),
    )
    arms = {}
    for label, protocol in ADHESION_ARMS:
        probability = adhesion[protocol]["OUT_STABLE_ADHESION"]
        readout = readouts[protocol]
        arms[label] = {
            "protocol_id": protocol,
            "exact_fixed_point_probability": probability,
            "observed_successes": readout["successes"],
            "observed_trials": readout["trials"],
            "role": readout["role"],
            "structural_verdict": structural_verdict(
                probability=probability,
                successes=readout["successes"],
                trials=readout["trials"],
            ),
            "rankable": is_rankable(
                probability=probability,
                successes=readout["successes"],
                trials=readout["trials"],
            ),
        }
    u, h, m = (arms[k]["exact_fixed_point_probability"] for k, _ in ADHESION_ARMS)

    maternal = exact_fixed_point(
        ADOPTED_VERSION, root, MATERNAL_ARMS, ("E_PAEP", "S_IGFBP1", "S_PRL")
    )
    statuses = {mid: row["activation_status"] for mid, row in om.items()}
    return {
        "model_version": ADOPTED_VERSION,
        "adhesion_arms": arms,
        "ordinal_claim": {
            "statement": objective["retained_ordinal_claim"]["statement"],
            "recorded_status": objective["retained_ordinal_claim"]["status"],
            "holds_on_adopted_model": u < h and h > m,
            "holds_as": "an expectation over the latent priors, not per assignment",
            "untreated_on_in_any_assignment": on_in_any_weighted_assignment(
                ADOPTED_VERSION, root, "adhesion_challenge_basal", "OUT_STABLE_ADHESION"
            ),
            "mifepristone_on_in_any_assignment": on_in_any_weighted_assignment(
                ADOPTED_VERSION,
                root,
                "adhesion_challenge_hormone_treated_mifepristone",
                "OUT_STABLE_ADHESION",
            ),
        },
        "maternal_fixed_point": maternal,
        "om001_direction_holds": maternal["hormone_treated_maternal"]["E_PAEP"]
        > maternal["e2_primed_maternal"]["E_PAEP"],
        "om002_non_inversion_holds": maternal["hormone_treated_maternal"]["S_IGFBP1"]
        >= maternal["basal_maternal"]["S_IGFBP1"],
        "fixed_point_values_binary": all(
            v in (0.0, 1.0) for arm in maternal.values() for v in arm.values()
        ),
        "s_prl_rule_equals_s_igfbp1_rule": _rule(ADOPTED_VERSION, root, "S_PRL")
        == _rule(ADOPTED_VERSION, root, "S_IGFBP1"),
        "structure": _acyclic_given_free(ADOPTED_VERSION, root),
        "contract": {
            "adhesion_role": objective["role"],
            "magnitude_fitted": objective["magnitude_fitted"],
            "no_quantitative_objective": "NO quantitative magnitude-fitted objective"
            in objective["no_replacement_objective"],
            "calibrated_physical_time": calibration["time_units"][
                "calibrated_physical_time"
            ],
            "duration_units": calibration["sequential_execution"]["duration_units"],
            "mifepristone_role": readouts[
                "adhesion_challenge_hormone_treated_mifepristone"
            ]["role"],
            "active_constraints": sorted(
                m for m, s in statuses.items() if s == "active_constraint"
            ),
            "active_diagnostics": sorted(
                m for m, s in statuses.items() if s == "active_diagnostic"
            ),
            "active_constraint_nodes": sorted(
                om[m]["model_nodes"]
                for m, s in statuses.items()
                if s == "active_constraint"
            ),
            "active_diagnostic_nodes": sorted(
                om[m]["model_nodes"]
                for m, s in statuses.items()
                if s == "active_diagnostic"
            ),
            "prl_rows": {
                m: {
                    "activation_status": row["activation_status"],
                    "calibration_role": row["calibration_role"],
                    "objective_treatment": row["objective_treatment"],
                }
                for m, row in om.items()
                if row["protein"].strip() == "PRL"
            },
        },
    }


#: Premises each curated status is conditional on. If one moves, the build
#: stops: the status would otherwise outlive its ground.
EXPECTED_PREMISES = {
    "ordinal_holds": True,
    "no_assignment_inverts": True,
    "mifepristone_verdict": STRUCTURALLY_CONTRADICTED,
    "mifepristone_rankable": False,
    "mifepristone_probability": 0.0,
    "mifepristone_role": "validation_if_held_out",
    "om001": True,
    "om002": True,
    "binary": True,
    "acyclic": True,
    "alias": True,
    "adhesion_role": "diagnostic_ordinal",
    "magnitude_fitted": False,
    "no_quantitative_objective": True,
    "calibrated_physical_time": False,
    "active_constraint_nodes": ["E_PAEP"],
    "active_diagnostic_nodes": ["S_IGFBP1"],
}


def _observed_premises(p: dict[str, Any]) -> dict[str, Any]:
    mife = p["adhesion_arms"]["hormone_treated_mifepristone"]
    c = p["contract"]
    return {
        "ordinal_holds": p["ordinal_claim"]["holds_on_adopted_model"],
        "no_assignment_inverts": not (
            p["ordinal_claim"]["untreated_on_in_any_assignment"]
            or p["ordinal_claim"]["mifepristone_on_in_any_assignment"]
        ),
        "mifepristone_verdict": mife["structural_verdict"],
        "mifepristone_rankable": mife["rankable"],
        "mifepristone_probability": mife["exact_fixed_point_probability"],
        "mifepristone_role": c["mifepristone_role"],
        "om001": p["om001_direction_holds"],
        "om002": p["om002_non_inversion_holds"],
        "binary": p["fixed_point_values_binary"],
        "acyclic": p["structure"]["acyclic_given_free_variables"],
        "alias": p["s_prl_rule_equals_s_igfbp1_rule"],
        "adhesion_role": c["adhesion_role"],
        "magnitude_fitted": c["magnitude_fitted"],
        "no_quantitative_objective": c["no_quantitative_objective"],
        "calibrated_physical_time": c["calibrated_physical_time"],
        "active_constraint_nodes": c["active_constraint_nodes"],
        "active_diagnostic_nodes": c["active_diagnostic_nodes"],
    }


def check_premises(premises: dict[str, Any]) -> None:
    observed = _observed_premises(premises)
    moved = {
        k: (observed[k], v) for k, v in EXPECTED_PREMISES.items() if observed[k] != v
    }
    if moved:
        raise RuntimeError(
            "AUDIT_PREMISE_MOVED: the curated Phase-1B statuses rest on premises "
            f"the adopted model or contract no longer supports: {moved}. "
            "Re-audit; do not edit the expectation to match."
        )


# --------------------------------------------------------------------------
# Bands, read from the canonical table and checked against the frozen text
# --------------------------------------------------------------------------


def _label(row: dict[str, str]) -> str:
    """The verbatim workbook label with its non-breaking spaces collapsed."""
    return " ".join(row["source_label"].split())


def reference_bands(root: Path) -> dict[str, Any]:
    with (root / PROTEINS).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    def values(protein: str, pick) -> list[float]:
        return [
            float(r["reported_concentration_pg_ml"])
            for r in rows
            if r["protein"] == protein
            and r["quality_tier"] == "primary"
            and r["reported_concentration_pg_ml"] != ""
            and pick(r)
        ]

    e2_only = values("PAEP", lambda r: _label(r) == "HT (E2 only)")
    # "HT (E2+P4+XAV939)" is the verbatim workbook label; the actual condition is
    # E2 + MPA + cAMP + XAV939 (SOFIA-COMM-004).
    full = values("PAEP", lambda r: _label(r) == "HT (E2+P4+XAV939)")
    bottom = lambda day: (
        lambda r: (
            r["series_id"].startswith("IGFBP-1_BOTTOM")
            and r["resolved_protocol_day"] == day
        )
    )
    day0 = values("IGFBP-1", bottom("0"))
    day6 = values("IGFBP-1", bottom("6"))
    nz0 = [v for v in day0 if v != 0]
    nz6 = [v for v in day6 if v != 0]
    return {
        "paep_e2_only": {"n": len(e2_only), "min": min(e2_only), "max": max(e2_only)},
        "paep_full_cocktail": {"n": len(full), "min": min(full), "max": max(full)},
        "igfbp1_day0": {
            "n": len(day0),
            "exact_zeros": day0.count(0.0),
            "nonzero_min": min(nz0),
            "nonzero_max": max(nz0),
        },
        "igfbp1_day6": {
            "n": len(day6),
            "exact_zeros": day6.count(0.0),
            "nonzero_min": min(nz6),
            "nonzero_max": max(nz6),
        },
        "paep_rows_carry_a_sampling_day": any(
            r["resolved_protocol_day"] != "" for r in rows if r["protein"] == "PAEP"
        ),
        "source_sha256": _sha(root / PROTEINS),
    }


def _fmt(value: float) -> str:
    return f"{round(value):,}"


def check_bands_against_frozen(bands: dict[str, Any], selection: str) -> None:
    """The frozen text quotes the bands, and those quotes must match the table."""
    paep_e2 = (
        f"{_fmt(bands['paep_e2_only']['min'])}–{_fmt(bands['paep_e2_only']['max'])}"
    )
    paep_full = f"{_fmt(bands['paep_full_cocktail']['min'])}–{_fmt(bands['paep_full_cocktail']['max'])}"
    _require(
        selection,
        f"E2-only {paep_e2} pg/mL and full cocktail {paep_full} pg/mL",
        "§9.1",
    )
    d0 = bands["igfbp1_day0"]
    d6 = bands["igfbp1_day6"]
    _require(
        selection,
        f"{d0['nonzero_min']:.1f}–{d0['nonzero_max']:.1f} at day 0",
        "§4 (ii)",
    )
    frozen_day6 = f"{round(d6['nonzero_min'], -2):,.0f}–{round(d6['nonzero_max'], -2):,.0f} pg/mL at day 6"
    _require(selection, f"roughly {frozen_day6}", "§4 (ii)")
    if not (d0["exact_zeros"] >= 1 and d6["exact_zeros"] >= 1):
        raise RuntimeError("frozen §4 (ii) says both IGFBP-1 bands contain exact zeros")
    if bands["paep_rows_carry_a_sampling_day"]:
        raise RuntimeError(
            "PAEP rows now carry a sampling day; addendum G7 states that they do not"
        )


# --------------------------------------------------------------------------
# The frozen design, as the handoff carries it
# --------------------------------------------------------------------------

#: (field, phrase, frozen section). Each phrase must appear verbatim, after
#: whitespace is collapsed, in the named section of the frozen selection
#: document. The handoff rows below quote these phrases and nothing looser.
FROZEN_PHRASES = (
    (
        "arm",
        "Days 2–6: **MPA 1 µM + cAMP 0.25 mM + XAV939 10 µM, E2 omitted.**",
        "## 12.",
    ),
    (
        "priming",
        "Days 0–2 unchanged: E2-only priming, as the current protocol runs it.",
        "## 12.",
    ),
    (
        "comparator",
        "**Full cocktail** (E2 + MPA + cAMP + XAV939) — the ON reference band.",
        "## 4.",
    ),
    (
        "e2_only_reference",
        "**E2-only, sampled at day 2** — the low reference band",
        "## 4.",
    ),
    ("baseline", "**Pre-cocktail baseline PAEP.**", "## 4."),
    (
        "baseline_timepoint",
        "Existing assay, existing timepoint, one extra aliquot.",
        "## 4.",
    ),
    (
        "imaging",
        "phase-contrast confluence imaging at days 2, 4 and 6 in **both** the epithelial and the stromal channel",
        "## 12.",
    ),
    (
        "outlets",
        "Top outlet for PAEP, bottom outlet for IGFBP-1 and PRL, sampled at the existing day-3 and day-6 windows, with chip identity carried",
        "## 12.",
    ),
    (
        "assays",
        "PAEP, IGFBP-1 and PRL by the three existing ELISAs. **Nothing else.**",
        "## 12.",
    ),
    (
        "no_embryo",
        "No surface CD98, no pSTAT3, no α-DG-N, no GLI1/PTCH1, no embryos, no attachment.",
        "## 12.",
    ),
    (
        "replication",
        "Three donors, one chip per donor per condition, plus a technical duplicate of the minus-E2 arm if capacity permits (§9.2).",
        "## 12.",
    ),
    (
        "unit",
        "Donor is the biological unit; chips are not independent replicates; no patient-level variance, confidence interval, paired-donor test or personalization claim may be derived.",
        "## 12.",
    ),
    ("duplicate_not_n", "It does not raise biological *n*", "## 9."),
    (
        "paep_rule",
        "**ON** — the minus-E2 value lies in or above the full-cocktail band;",
        "## 9.",
    ),
    ("paep_off", "**OFF** — it lies in or below the E2-only band;", "## 9."),
    (
        "paep_indeterminate",
        "**indeterminate** — anything between, which is an admissible verdict and not a tie to be broken.",
        "## 9.",
    ),
    (
        "never_refit",
        "**The rule must never be fitted from the minus-E2 result**",
        "## 9.",
    ),
    (
        "igfbp1_same_rule",
        "(ii) the same three-level rule for IGFBP-1 against its own day-0 and day-6 bands",
        "## 4.",
    ),
    (
        "igfbp1_decides",
        "(iii) **IGFBP-1 is the stromal decision variable and PRL is corroborative, not a substitute.**",
        "## 4.",
    ),
    ("prl_never", "**PRL is corroborative and never decisive**", "## 12."),
    (
        "first_row",
        "`PAEP OFF + IGFBP-1 ON` establishes **sustained E2 dependence of the epithelial secretory programme**, not the mechanism, because `SEC-e` predicts identically on both usable assays.",
        "## 12.",
    ),
)


def check_frozen_phrases(selection: str) -> dict[str, str]:
    carried = {}
    for field, phrase, heading in FROZEN_PHRASES:
        carried[field] = _require(
            _section(selection, heading), phrase, heading.strip("# .")
        )
    return carried


def check_doses(root: Path, selection: str) -> dict[str, str]:
    """The frozen arm's doses equal the cocktail doses the protocol records."""
    notes = _protocol_notes(root)
    cocktail = notes["hormone_treated_maternal"]
    priming = notes["e2_primed_maternal"]
    for dose in ("10 nM E2", "1 uM MPA", "250 uM cAMP", "10 uM XAV939"):
        if dose not in cocktail:
            raise RuntimeError(
                f"config/protocols.yaml cocktail note no longer states {dose!r}"
            )
    if "10 nM E2 alone" not in priming or "protocol days 0-2" not in priming:
        raise RuntimeError("config/protocols.yaml priming note changed")
    # 0.25 mM == 250 uM: the frozen arm and the recorded cocktail agree on cAMP.
    _require(_section(selection, "## 12."), "cAMP 0.25 mM", "12")
    return {"cocktail_note": cocktail, "priming_note": priming}


def frozen_table_c(root: Path) -> dict[str, tuple[str, str]]:
    """Table C of the frozen decision tables: each class's predicted pattern."""
    text = (root / FROZEN_TABLES).read_text(encoding="utf-8")
    body = _section(text, "## C.")
    table = {}
    for line in body.splitlines():
        match = re.match(
            r"\| `(SEC-[a-e])` \([^)]*\) \| \*\*(ON|OFF)\*\* \| \*\*(ON|OFF)\*\* \|",
            line,
        )
        if match:
            table[match.group(1)] = (match.group(2), match.group(3))
    if sorted(table) != ["SEC-a", "SEC-b", "SEC-c", "SEC-d", "SEC-e"]:
        raise RuntimeError(f"frozen table C no longer parses: {table}")
    return table


# --------------------------------------------------------------------------
# The pre-run analysis addendum (owner decision, 2026-09-24)
# --------------------------------------------------------------------------

OWNER = "project owner (in session, before any prospective data exist)"
ADDENDUM_TYPE = "OWNER_DECISION / PRE_RUN_ADDENDUM"
ACTIVE = "ACTIVE"

#: First pre-run addendum: (id, gap, decision, frozen text it resolves, status).
#: A later owner decision that replaces part of a row marks it here and keeps
#: the original wording, so the record shows what was decided and when.
ADDENDUM = (
    (
        "G1",
        "'PRL convincingly ON' (frozen §4 (iii) and §12) has no criterion.",
        (
            "PRL is removed from classification entirely. It is reported as corroborative "
            "only, with no numeric weight, and it can never change the stromal call. If "
            "IGFBP-1 is interpretable, the stromal call comes from IGFBP-1 alone. If "
            "IGFBP-1 is uninterpretable, the stromal call is INDETERMINATE whatever PRL "
            "shows. PRL agreement or disagreement is recorded descriptively. No PRL "
            "threshold or 'convincingly ON' band is created. This follows from OM-006 "
            "being context_only / provisional / not_used."
        ),
        "where IGFBP-1 is uninterpretable while PRL is convincingly ON",
        ACTIVE,
    ),
    (
        "G2",
        (
            "A prospective IGFBP-1 value of exactly zero: read literally, zero lies inside "
            "the day-0 band, but §4 (ii) says 'a dropout reads zero in either'."
        ),
        (
            "An exact zero is INDETERMINATE, not OFF, because zero occurs in both the "
            "historical low context and the treated context and cannot serve as a "
            "discriminating band assignment. PRL cannot rescue it. Precedence: (1) "
            "IGFBP-1 == 0 -> INDETERMINATE; (2) otherwise, in the ON band -> ON; (3) "
            "otherwise, in the day-0/low band -> OFF; (4) otherwise -> INDETERMINATE. "
            "The fact that a historical interval numerically contains zero never "
            "overrides rule (1)."
        ),
        "while a dropout reads zero in either",
        "SUPERSEDED_IN_PART_BY_RQ6 (steps 2-4; the exact-zero override stands)",
    ),
    (
        "G3",
        (
            "Confluence imaging is required in both channels, but no integrity pass/fail "
            "criterion is pre-registered."
        ),
        (
            "No numerical confluence threshold is invented. A three-state QC call is "
            "pre-registered: INTACT, COMPROMISED or INDETERMINATE. It is made from the "
            "day-2/day-4/day-6 phase-contrast series, for the epithelial and stromal "
            "channels independently, and where operationally possible before the "
            "corresponding secretion classification is seen. COMPROMISED means clear "
            "monolayer loss, detachment or denudation, enough that a change in secreted "
            "protein could plausibly come from loss of the producing compartment rather "
            "than from a state transition. If integrity is COMPROMISED or INDETERMINATE "
            "in the compartment a molecular call needs, that call is not assigned to a "
            "SEC class and is recorded as integrity_invalid / "
            "biological_interpretation_indeterminate. Nothing is averaged through an "
            "integrity failure. A validated quantitative confluence criterion held by "
            "the experimental team may replace this rule only if it is specified and "
            "locked before the run. No threshold is derived from the prospective data."
        ),
        "Phase-contrast confluence imaging at days 2, 4 and 6, epithelial **and** stromal.",
        "SUPERSEDED_IN_PART_BY_G3R (the locking guard replaces 'where operationally possible')",
    ),
    (
        "G4",
        (
            "No technical duplicate is available (frozen §9.2 fallback: 'pre-register, "
            "before the run, how a technical failure and an uninterpretable unit are "
            "reported')."
        ),
        (
            "A documented technical failure produces MISSING/TECHNICAL_FAILURE, never a "
            "biological ON, OFF or INDETERMINATE. There is no imputation, no averaging "
            "over donors and no inference from PRL, and the donor-condition is reported "
            "as unavailable for class assignment. A replacement measurement or chip is "
            "allowed only under a pre-specified technical-repeat policy and only because "
            "of a documented technical failure, never because the biological result is "
            "inconvenient."
        ),
        "how a technical failure and an uninterpretable unit are reported",
        "SUPERSEDED_IN_PART_BY_G4R (the default when no repeat SOP exists)",
    ),
    (
        "G5",
        "Two technical duplicates of the minus-E2 arm disagree.",
        (
            "Discordant duplicates are never averaged to obtain a band call. For a "
            "duplicated minus-E2 donor-condition: concordant valid duplicate calls -> "
            "that call is retained; one documented technical failure plus one valid "
            "replicate -> the valid replicate is retained and the lost duplicate is noted "
            "explicitly; two valid replicates with different ordinal calls -> "
            "TECHNICAL_DISCORDANCE / INDETERMINATE. Both raw values and both calls are "
            "reported. The technical duplicate never increases biological n."
        ),
        "add a technical duplicate of the minus-E2 arm if material and chip capacity permit",
        ACTIVE,
    ),
    (
        "G6",
        "A contemporaneous control falls outside the historical reference band.",
        (
            "The historical bands are never refitted after prospective results are seen. "
            "For each donor and run, the contemporaneous controls are QC for whether the "
            "frozen ordinal rule transfers. If a required contemporaneous control falls "
            "outside the historical reference band expected for it: flag "
            "CONTROL_OUT_OF_BAND, do not classify that donor's minus-E2 measurement with "
            "the frozen band rule, and record the donor as INDETERMINATE pending "
            "assay/protocol investigation. If this happens systematically across the "
            "run, stop biological interpretation of the run and reopen the transferability "
            "of the assay and the reference bands. No new band is manufactured from the "
            "same run."
        ),
        "The bands are the ones already in hand",
        (
            "SUPERSEDED_BY_RQ5 (symmetric out-of-band gating and the run-level stop are "
            "withdrawn; never refitting the bands stands)"
        ),
    ),
    (
        "G7",
        (
            "The frozen design samples day 3 and day 6 but does not say which one decides. "
            "The historical PAEP rows carry no sampling-day axis."
        ),
        (
            "DAY 6 is the PRIMARY decision timepoint, because the intervention is the "
            "whole days-2-to-6 minus-E2 phase. Day 3 is a pre-specified secondary "
            "observation of trajectory, dropout and technical problems. Day 6 decides the "
            "primary PAEP / IGFBP-1 SEC classification. Day-3/day-6 disagreement is "
            "reported and never silently collapsed, and a day-3 value cannot override a "
            "valid day-6 classification. This is an OWNER pre-run decision. It is not "
            "derived from the historical PAEP table, which has no sampling day."
        ),
        "sampled at the existing day-3 and day-6 windows",
        ACTIVE,
    ),
    (
        "G8",
        (
            "The ON/ON branch (frozen §5) defers to 'the registered E2-only PAEP call', "
            "which does not exist: OM-001 records the E_PAEP threshold as implicit and "
            "unrecorded."
        ),
        (
            "That call is not invented. A prospective ON/ON result narrows the model to "
            "SEC-b OR SEC-c and establishes only what the two share: concurrent E2 "
            "during the days-2-to-6 cocktail phase is not required for the observed "
            "epithelial secretory output under this protocol. It does NOT distinguish "
            "SEC-b from SEC-c. No prospective step depends on a registered binary E2-only "
            "PAEP call. The existing E2-only measurements remain the low reference band "
            "for the ordinal minus-E2 rule, and that does not turn them into a separately "
            "licensed Boolean node call. Any later distinction between SEC-b and SEC-c "
            "needs its own licensed measurement and interpretation, and must not be "
            "inferred post hoc from this experiment."
        ),
        "Which of the two is settled by the registered E2-only PAEP call, not by this arm",
        ACTIVE,
    ),
    (
        "P0",
        "The order in which the rules are applied.",
        (
            "For every donor/condition the levels are applied in this order: (1) technical "
            "validity; (2) compartment integrity; (3) contemporaneous-control validity; "
            "(4) molecular ordinal call; (5) SEC-class mapping. A failure at an earlier "
            "level prevents any later biological classification. Donors are never "
            "averaged to manufacture a class call. The three donor-level outcomes are "
            "reported individually, and disagreement is reported as disagreement."
        ),
        "reported per unit, with disagreement between units reported as disagreement rather than averaged",
        "SUPERSEDED_IN_PART_BY_RQ3 (level 3 renamed to contemporaneous expected-state confirmation)",
    ),
)

# Operational labels. Every rule below and every handoff row speaks these.
TECHNICAL_FAILURE = "MISSING/TECHNICAL_FAILURE"
MISSING = "MISSING"
INDETERMINATE_BELOW_DETECTION = "INDETERMINATE_BELOW_DETECTION"
#: Recorded measurement states (round-3 decision MS1). Only `observed` may enter
#: an ordinal classifier.
OBSERVED = "observed"
NO_DETECTABLE_SECRETION = "no_detectable_secretion"
BELOW_DETECTION = "below_detection"
STATE_MISSING = "missing"
STATE_TECHNICAL_FAILURE = "technical_failure"
MEASUREMENT_STATES = (
    OBSERVED,
    NO_DETECTABLE_SECRETION,
    BELOW_DETECTION,
    STATE_MISSING,
    STATE_TECHNICAL_FAILURE,
)
INTEGRITY_INVALID = "integrity_invalid"
NOT_CONFIRMED = "CONTROL_STATE_NOT_CONFIRMED"
ON_CONFIRMED = "CONTROL_ON_CONFIRMED"
LOW_CONFIRMED = "CONTROL_LOW_CONFIRMED"
INDETERMINATE_ZERO = "INDETERMINATE_ZERO"
TECHNICAL_DISCORDANCE = "TECHNICAL_DISCORDANCE"
GRADED = "graded_not_boolean"
ON = "ON"
OFF = "OFF"
INTACT = "INTACT"
NO_CLASS = "NO_CLASS_ASSIGNMENT"
#: QC or measurement indeterminacies. None of them carries a SEC-class inference.
QC_INDETERMINATE = (
    TECHNICAL_FAILURE,
    MISSING,
    INDETERMINATE_BELOW_DETECTION,
    INTEGRITY_INVALID,
    NOT_CONFIRMED,
    INDETERMINATE_ZERO,
    TECHNICAL_DISCORDANCE,
)

PRECEDENCE = (
    "technical validity",
    "compartment integrity",
    "contemporaneous expected-state confirmation",
    "molecular ordinal call",
    "SEC-class mapping",
)


def boundaries(bands: dict[str, Any]) -> dict[str, float]:
    """The four frozen boundaries, read from the canonical table, never refitted."""
    return {
        "PAEP_ON_LOWER": bands["paep_full_cocktail"]["min"],
        "PAEP_LOW_UPPER": bands["paep_e2_only"]["max"],
        "IGFBP1_OFF_UPPER": bands["igfbp1_day0"]["nonzero_max"],
        "IGFBP1_ON_LOWER": bands["igfbp1_day6"]["nonzero_min"],
    }


def paep_on_control(x: float, b: dict[str, float]) -> str:
    """Full-cocktail PAEP, day 6: one-sided; above the old maximum is still ON."""
    return ON_CONFIRMED if x >= b["PAEP_ON_LOWER"] else NOT_CONFIRMED


def paep_low_control(x: float, b: dict[str, float]) -> str:
    """E2-only PAEP, day 2: one-sided; below the old minimum is still LOW."""
    return LOW_CONFIRMED if x <= b["PAEP_LOW_UPPER"] else NOT_CONFIRMED


def igfbp1_on_control(x: float, b: dict[str, float]) -> str:
    """Full-cocktail IGFBP-1, day 6 (RQ1, RQ5). An exact zero is not confirmed."""
    if x == 0:
        return NOT_CONFIRMED
    return ON_CONFIRMED if x >= b["IGFBP1_ON_LOWER"] else NOT_CONFIRMED


def paep_call(x: float, b: dict[str, float]) -> str:
    """Frozen §9.1 three-band rule for the minus-E2 day-6 PAEP value."""
    if x >= b["PAEP_ON_LOWER"]:
        return ON
    if x <= b["PAEP_LOW_UPPER"]:
        return OFF
    return GRADED


def igfbp1_call(x: float, b: dict[str, float]) -> str:
    """RQ6: frozen 'in or above / in or below / between' plus the exact-zero override."""
    if x == 0:
        return INDETERMINATE_ZERO
    if x <= b["IGFBP1_OFF_UPPER"]:
        return OFF
    if x < b["IGFBP1_ON_LOWER"]:
        return GRADED
    return ON


class AssayLimitUndocumented(RuntimeError):
    """No documented prospective assay detection limit: nothing may be classified."""


class InconsistentRecord(ValueError):
    """A record whose state and value contradict each other is rejected, not classified."""


def measured(
    state: str, value: float | None, detection_limit: float | None
) -> float | str:
    """MS1: turn a recorded measurement into a classifiable number or a non-class state.

    Zero, below-detection, missing and technical failure stay distinct. Nothing is
    imputed (no LOD/2), and a censored value never becomes OFF.
    """
    if (
        detection_limit is None
        or not math.isfinite(detection_limit)
        or not detection_limit > 0
    ):
        raise AssayLimitUndocumented(
            "a documented prospective assay detection limit is required before classification"
        )
    if state not in MEASUREMENT_STATES:
        raise InconsistentRecord(f"unknown measurement state {state!r}")
    if state == STATE_TECHNICAL_FAILURE:
        return TECHNICAL_FAILURE
    if state == STATE_MISSING:
        return MISSING
    if state == NO_DETECTABLE_SECRETION:
        return INDETERMINATE_ZERO
    if state == BELOW_DETECTION:
        return INDETERMINATE_BELOW_DETECTION
    if value is None or not math.isfinite(value):
        raise InconsistentRecord(f"state 'observed' with a non-finite value {value!r}")
    if value < detection_limit:
        raise InconsistentRecord(
            f"state 'observed' with value {value!r} below the documented limit {detection_limit}"
        )
    return float(value)


def confirm_control(
    state: str,
    value: float | None,
    detection_limit: float | None,
    rule,
    b: dict[str, float],
) -> str:
    """A reference confirms its expected state only from an observed value."""
    m = measured(state, value, detection_limit)
    if m in (TECHNICAL_FAILURE, MISSING):
        return m
    if isinstance(m, str):
        return NOT_CONFIRMED
    return rule(m, b)


def channel_outcome(
    *,
    technical_ok: bool,
    day6_integrity: str,
    controls: tuple[str, ...],
    state: str,
    value: float | None,
    detection_limit: float | None,
    caller,
    b: dict[str, float],
) -> str:
    """Levels 1-4 of the precedence for one source-pair block and one channel, at day 6.

    Only day-6 inputs are read: a day-3 value or image cannot rescue a day-6
    failure (G7, G3R).
    """
    if (
        detection_limit is None
        or not math.isfinite(detection_limit)
        or not detection_limit > 0
    ):
        raise AssayLimitUndocumented(
            "a documented prospective assay detection limit is required before classification"
        )
    if not technical_ok or state == STATE_TECHNICAL_FAILURE:
        return TECHNICAL_FAILURE
    if state == STATE_MISSING:
        return MISSING
    if day6_integrity != INTACT:
        return INTEGRITY_INVALID
    if any(c not in (ON_CONFIRMED, LOW_CONFIRMED) for c in controls):
        return NOT_CONFIRMED
    m = measured(state, value, detection_limit)
    return m if isinstance(m, str) else caller(m, b)


# --- the pre-run allocation manifest and assay metadata (round 3, AL1/MS1) ---

PLACEHOLDER = "REQUIRED_PRE_RUN_MANIFEST"
ALLOCATION_COLUMNS = (
    "source_pair_block_id",
    "epithelial_source_id",
    "stromal_source_id",
    "chip_id",
    "condition",
    "technical_duplicate_of",
    "physical_position",
    "processing_order",
    "allocation_method",
    "position_allocation_method",
    "order_allocation_method",
    "rng_seed_or_randomisation_record",
    "allocated_at",
    "allocated_by",
)
ASSAY_METADATA_COLUMNS = (
    "analyte",
    "assay_run_id",
    "detection_limit_pg_ml",
    "limit_source",
    "recorded_at",
    "recorded_by",
)
PLANNED_BLOCKS = ("SPB-1", "SPB-2", "SPB-3")
#: Every chip row must carry these, filled.
REQUIRED_MANIFEST_FIELDS = (
    "source_pair_block_id",
    "epithelial_source_id",
    "stromal_source_id",
    "chip_id",
    "physical_position",
    "processing_order",
    "allocation_method",
    "position_allocation_method",
    "order_allocation_method",
    "rng_seed_or_randomisation_record",
    "allocated_at",
    "allocated_by",
)
REQUIRED_ANALYTES = ("PAEP", "IGFBP-1", "PRL")
REQUIRED_ASSAY_FIELDS = (
    "assay_run_id",
    "detection_limit_pg_ml",
    "limit_source",
    "recorded_at",
    "recorded_by",
)
#: AL1: condition assignment within a block is always randomised.
RANDOMIZED = "randomized"
#: AL1: only position and processing order may be counterbalanced, and only when
#: hardware prevents randomising them.
COUNTERBALANCED = "counterbalanced_hardware_constraint"
LAYOUT_METHODS = (RANDOMIZED, COUNTERBALANCED)
CONDITIONS = ("full_cocktail", "minus_E2")


def allocation_template() -> list[dict[str, str]]:
    rows = []
    for block in PLANNED_BLOCKS:
        for condition, duplicate in (
            ("full_cocktail", ""),
            ("minus_E2", ""),
            (
                "minus_E2",
                PLACEHOLDER,
            ),  # optional duplicate: the block's minus_E2 chip_id
        ):
            row = {c: PLACEHOLDER for c in ALLOCATION_COLUMNS}
            row.update(
                source_pair_block_id=block,
                condition=condition,
                technical_duplicate_of=duplicate or "",
            )
            rows.append(row)
    return rows


def assay_metadata_template() -> list[dict[str, str]]:
    return [
        dict({c: PLACEHOLDER for c in ASSAY_METADATA_COLUMNS}, analyte=analyte)
        for analyte in REQUIRED_ANALYTES
    ]


def validate_manifest(rows: list[dict[str, str]]) -> dict[str, Any]:
    """Whether treatment may start, and what the manifest says about independence."""
    errors: list[str] = []
    unfilled = sorted(
        {c for r in rows for c in ALLOCATION_COLUMNS if r.get(c, "") == PLACEHOLDER}
    )
    # Every identity and provenance field is filled for every chip.
    for index, row in enumerate(rows):
        for field in REQUIRED_MANIFEST_FIELDS:
            if not row.get(field, "").strip():
                errors.append(f"row {index + 1}: {field} is empty")
    chip_ids = [
        r.get("chip_id", "").strip() for r in rows if r.get("chip_id", "").strip()
    ]
    duplicate_chips = sorted({c for c in chip_ids if chip_ids.count(c) > 1})
    if duplicate_chips:
        errors.append(f"chip_id: duplicate values {duplicate_chips}")
    blocks: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        blocks.setdefault(row.get("source_pair_block_id", "").strip(), []).append(row)
    if sorted(blocks) != sorted(PLANNED_BLOCKS):
        errors.append(
            f"source-pair blocks {sorted(blocks)} differ from the planned {list(PLANNED_BLOCKS)}"
        )
    pairs: dict[str, tuple[str, str]] = {}
    for block, chips in sorted(blocks.items()):
        sources = {(c["epithelial_source_id"], c["stromal_source_id"]) for c in chips}
        if len(sources) != 1:
            errors.append(
                f"{block}: condition chips do not share one source pair {sorted(sources)}"
            )
        else:
            pairs[block] = next(iter(sources))
        primary_rows = [
            c for c in chips if not c.get("technical_duplicate_of", "").strip()
        ]
        primaries = [c["condition"] for c in primary_rows]
        if sorted(primaries) != sorted(CONDITIONS):
            errors.append(
                f"{block}: needs exactly one full_cocktail and one minus_E2 chip"
            )
        minus_ids = [c["chip_id"] for c in primary_rows if c["condition"] == "minus_E2"]
        duplicates = [c for c in chips if c.get("technical_duplicate_of", "").strip()]
        if len(duplicates) > 1:
            errors.append(f"{block}: at most one technical duplicate is allowed")
        for chip in duplicates:
            if chip["condition"] != "minus_E2":
                errors.append(f"{block}: only the minus_E2 arm may be duplicated")
            if (
                len(minus_ids) != 1
                or chip["technical_duplicate_of"].strip() != minus_ids[0]
            ):
                errors.append(
                    f"{block}: technical_duplicate_of must name this block's primary "
                    "minus_E2 chip_id"
                )
    # AL1: condition assignment is always randomised, with a real record.
    for row in rows:
        chip = row.get("chip_id", "?")
        if row.get("allocation_method") != RANDOMIZED:
            errors.append(f"{chip}: condition assignment must be {RANDOMIZED!r}")
        record = row.get("rng_seed_or_randomisation_record", "").strip()
        if not record or record == PLACEHOLDER:
            errors.append(f"{chip}: no randomisation record")
        for field in ("position_allocation_method", "order_allocation_method"):
            if row.get(field) not in LAYOUT_METHODS:
                errors.append(f"{chip}: {field} must be one of {LAYOUT_METHODS}")
    # Physical positions and processing-order slots are unique in the run.
    for field in ("physical_position", "processing_order"):
        values = [r.get(field, "").strip() for r in rows]
        if any(v in ("", PLACEHOLDER) for v in values) and PLACEHOLDER not in values:
            errors.append(f"{field}: empty value")
        filled = [v for v in values if v not in ("", PLACEHOLDER)]
        if len(filled) != len(set(filled)):
            errors.append(
                f"{field}: duplicate values {sorted(v for v in set(filled) if filled.count(v) > 1)}"
            )
    if any(
        r.get("processing_order", "") not in ("", PLACEHOLDER)
        and not r["processing_order"].strip().isdigit()
        for r in rows
    ):
        errors.append("processing_order: must be a positive integer")
    # Counterbalancing must actually vary the within-block layout across blocks.
    for field, method in (
        ("physical_position", "position_allocation_method"),
        ("processing_order", "order_allocation_method"),
    ):
        if not any(r.get(method) == COUNTERBALANCED for r in rows):
            continue
        layouts = set()
        for block, chips in sorted(blocks.items()):
            primaries = [c for c in chips if not c.get("technical_duplicate_of")]
            try:
                ranked = sorted(primaries, key=lambda c: _sort_key(c[field]))
            except (KeyError, ValueError):
                errors.append(f"{block}: {field} cannot be ordered")
                continue
            layouts.add(tuple(c["condition"] for c in ranked))
        if len(layouts) < 2:
            errors.append(
                f"{field}: counterbalanced but identical within-block layout in every block"
            )
    reused = {
        kind: sorted(
            {
                src
                for src in (p[index] for p in pairs.values())
                if [p[index] for p in pairs.values()].count(src) > 1
                and src != PLACEHOLDER
            }
        )
        for kind, index in (("epithelial", 0), ("stromal", 1))
    }
    return {
        "errors": errors,
        "unfilled_fields": unfilled,
        "reused_sources": reused,
        "independent_blocks_claimable": not any(reused.values()),
        "treatment_may_start": not errors and not unfilled,
    }


def _sort_key(value: str) -> tuple[int, float | str]:
    value = value.strip()
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)


def assay_limits(rows: list[dict[str, str]]) -> dict[str, float]:
    """The documented prospective detection limit per analyte, or refuse.

    A limit must be a finite positive number; anything else is refused here,
    at metadata-validation time, not discovered later at classification.
    """
    analytes = [row.get("analyte", "").strip() for row in rows]
    if sorted(analytes) != sorted(REQUIRED_ANALYTES):
        raise AssayLimitUndocumented(
            f"assay metadata analytes {sorted(analytes)} must be exactly one row each of "
            f"{list(REQUIRED_ANALYTES)}"
        )
    for row in rows:
        for field in REQUIRED_ASSAY_FIELDS:
            value = row.get(field, "").strip()
            if not value or value == PLACEHOLDER:
                raise AssayLimitUndocumented(
                    f"{row['analyte']}: {field} is not documented"
                )
    limits = {}
    for row in rows:
        raw = row.get("detection_limit_pg_ml", "").strip()
        if raw in ("", PLACEHOLDER):
            raise AssayLimitUndocumented(
                f"{row['analyte']}: no documented detection limit"
            )
        try:
            limit = float(raw)
        except ValueError as exc:
            raise AssayLimitUndocumented(
                f"{row['analyte']}: limit {raw!r} is not a number"
            ) from exc
        if not math.isfinite(limit) or limit <= 0:
            raise AssayLimitUndocumented(
                f"{row['analyte']}: limit {raw!r} is not finite and positive"
            )
        limits[row["analyte"]] = limit
    return limits


def sec_mapping(paep: str, igfbp1: str, table_c: dict[str, tuple[str, str]]) -> str:
    """Level 5. QC indeterminacies never map to a class; only valid calls do."""
    if paep in QC_INDETERMINATE or igfbp1 in QC_INDETERMINATE:
        return NO_CLASS
    if GRADED in (paep, igfbp1):
        return GRADED
    classes = sorted(c for c, v in table_c.items() if v == (paep, igfbp1))
    return " or ".join(classes) if classes else "none (the fork as posed is wrong)"


def second_addendum(
    bands: dict[str, Any],
) -> tuple[tuple[str, str, str, str, str], ...]:
    """Owner decisions RQ1-RQ6 and the G3/G4 strengthening, 2026-09-24, pre-run."""
    b = boundaries(bands)
    return (
        (
            "RQ1",
            "An exact-zero day-6 IGFBP-1 in the contemporaneous full-cocktail control.",
            (
                f"The raw zero is retained and reported, and the reference is "
                f"{NOT_CONFIRMED}. That donor's minus-E2 stromal result is not classified, "
                "and PRL cannot rescue the reference. It is not called a technical failure "
                "unless independent assay/QC evidence says it was one. This records that the "
                "expected reference state was not demonstrated; it does not say why the zero "
                "occurred. The historical treated zeros explain why the rule is needed; they "
                "do not turn a prospective zero into a valid ON control."
            ),
            "while a dropout reads zero in either",
            ACTIVE,
        ),
        (
            "RQ2",
            "The day of the pre-cocktail PAEP aliquot.",
            (
                "DAY 0, before E2 priming. It is the missing PAEP baseline that corresponds "
                "to the existing day-0 IGFBP-1/PRL baselines, and it is descriptive: a "
                "measured referent for E_PAEP = 0, not a gating band. The separate day-2 "
                "E2-only PAEP sample remains the LOW/OFF reference. This timing is an OWNER "
                "pre-run clarification, because the frozen text called it an 'existing "
                "timepoint' without naming the day."
            ),
            "Existing assay, existing timepoint, one extra aliquot.",
            ACTIVE,
        ),
        (
            "RQ3",
            "What `graded_not_boolean` means once QC can produce indeterminate results.",
            (
                f"`{GRADED}` is used ONLY when all upstream QC has passed and a valid "
                "molecular measurement lies in the pre-registered intermediate region "
                f"between OFF and ON. These are NOT `{GRADED}`: {TECHNICAL_FAILURE}; "
                f"integrity COMPROMISED or INDETERMINATE ({INTEGRITY_INVALID}); a required "
                f"contemporaneous reference state not confirmed ({NOT_CONFIRMED}); an "
                f"exact-zero IGFBP-1 ({INDETERMINATE_ZERO}, G2/RQ1); and "
                f"{TECHNICAL_DISCORDANCE} between valid duplicates. Those are QC/measurement "
                "indeterminacies and carry no SEC-class inference. Precedence: (1) technical "
                "validity; (2) compartment integrity; (3) contemporaneous expected-state "
                "confirmation; (4) molecular ordinal call; (5) SEC-class mapping. Only level-4 "
                f"intermediate values can produce `{GRADED}`."
            ),
            "Record as `graded_not_boolean`.",
            ACTIVE,
        ),
        (
            "RQ4",
            "Whether the day-0 IGFBP-1 baseline gates a call.",
            (
                "Prospective day-0 IGFBP-1 stays DESCRIPTIVE. It is collected, chip and donor "
                "identity are retained, and unexpected values are reported, but no donor is "
                "invalidated because its day-0 value lies outside the historical day-0 range. "
                "The frozen control list did not designate it as a transferability gate, and "
                "adding one would be a new experimental criterion, not a clarification."
            ),
            "same collection windows",
            ACTIVE,
        ),
        (
            "RQ5",
            "Symmetric historical-band gating of controls (G6).",
            (
                "Replaced by one-sided EXPECTED-STATE confirmation, consistent with the "
                "frozen ordinal semantics. Full-cocktail PAEP at day 6: >= PAEP_ON_LOWER "
                f"({b['PAEP_ON_LOWER']:.3f} pg/mL) -> {ON_CONFIRMED}, otherwise "
                f"{NOT_CONFIRMED}; a value above the old maximum remains valid ON evidence. "
                f"E2-only PAEP at day 2: <= PAEP_LOW_UPPER ({b['PAEP_LOW_UPPER']:.4f} pg/mL) "
                f"-> {LOW_CONFIRMED}, otherwise {NOT_CONFIRMED}; a value below the old "
                "minimum remains valid LOW evidence. Full-cocktail IGFBP-1 at day 6: exact "
                f"zero -> {NOT_CONFIRMED}; >= IGFBP1_ON_LOWER ({b['IGFBP1_ON_LOWER']:.3f} "
                f"pg/mL) -> {ON_CONFIRMED}; 0 < x < IGFBP1_ON_LOWER -> {NOT_CONFIRMED}. A "
                "required reference that fails confirmation invalidates the corresponding "
                "minus-E2 molecular classification FOR THAT DONOR. There is no majority "
                "rule, no 2-of-3 donor rule, no run-level average and no systematic-failure "
                "threshold: each donor is individually classifiable, biologically "
                "indeterminate, or unavailable because a required QC or reference state was "
                "not established. No boundary is refitted. Rationale: the historical minima "
                "and maxima are descriptive reference extrema, not validated two-sided "
                "acceptance intervals, so they are not used for symmetric control exclusion "
                "(rationale corrected by RAT1)."
            ),
            "The bands are the ones already in hand",
            "ACTIVE (rationale corrected by RAT1)",
        ),
        (
            "RQ6",
            "The final IGFBP-1 ordinal rule.",
            (
                "After technical validity, integrity and required control-state confirmation "
                "have all passed, with IGFBP1_OFF_UPPER = the maximum NON-ZERO day-0 value "
                f"({b['IGFBP1_OFF_UPPER']:.4f} pg/mL) and IGFBP1_ON_LOWER = the minimum "
                f"NON-ZERO day-6 value ({b['IGFBP1_ON_LOWER']:.3f} pg/mL), the primary day-6 "
                f"minus-E2 value x is: (1) x == 0 -> {INDETERMINATE_ZERO}, not {GRADED}; (2) "
                f"0 < x <= IGFBP1_OFF_UPPER -> {OFF}; (3) IGFBP1_OFF_UPPER < x < "
                f"IGFBP1_ON_LOWER -> {GRADED}; (4) x >= IGFBP1_ON_LOWER -> {ON}. So a "
                "positive value below the historical non-zero day-0 minimum is OFF, and a "
                "value above the historical day-6 maximum is ON. The historical ranges are "
                "not symmetric acceptance bands, exact zero is the special override because "
                "zero occurred in both historical contexts, and PRL never alters the call. "
                "This is the frozen 'in or above / in or below / between' logic plus the "
                "pre-run exact-zero exception."
            ),
            "(ii) the same three-level rule for IGFBP-1 against its own day-0 and day-6 bands",
            ACTIVE,
        ),
        (
            "G3R",
            "Integrity adjudication must not be influenced by secretion results.",
            (
                "The INTACT / COMPROMISED / INDETERMINATE calls stay, and no numeric "
                "confluence cutoff is invented. The integrity calls from the day-2/day-4/day-6 "
                "images are LOCKED before the PAEP/IGFBP-1/PRL assay VALUES are revealed to "
                "the person assigning biological calls. Condition identity need not be "
                "blinded if that is operationally impossible; what is required is that "
                "secretion results cannot influence the image-integrity judgement. Recorded "
                "per call: image identifier, channel, day, integrity call, adjudicator, "
                "timestamp/version. If the relevant compartment is COMPROMISED or "
                "INDETERMINATE at primary day 6, the primary molecular call is invalid and "
                "day 3 cannot rescue it. A validated quantitative confluence SOP may replace "
                "the categorical rule only through another documented PRE-RUN addendum "
                "before assay values are unblinded."
            ),
            "Phase-contrast confluence imaging at days 2, 4 and 6, epithelial **and** stromal.",
            ACTIVE,
        ),
        (
            "G4R",
            "Technical repeats when no repeat SOP exists.",
            (
                "No laboratory repeat SOP is invented. Without an already documented pre-run "
                f"technical-repeat SOP, a documented failed assay or chip remains "
                f"{TECHNICAL_FAILURE}. A measurement is never repeated because its biological "
                "value is inconvenient. If a legitimate technical repeat occurs, both the "
                "original record and the reason the repeat was authorised are retained. The "
                "planned technical duplicate follows G5 and does not increase biological n."
            ),
            "how a technical failure and an uninterpretable unit are reported",
            ACTIVE,
        ),
    )


THIRD_ADDENDUM = (
    (
        "MS1",
        "Measurement states and detection limits for the prospective run.",
        (
            "The prospective ELISA/run metadata must carry a documented assay detection "
            "limit before any biological classification; the historical 5 pg/mL IGFBP-1 "
            "figure is manuscript prose, not a canonical limit, and is not used. The "
            "classifier consumes measurement_state, the numeric value when one exists and "
            "the documented limit. States stay distinct: `observed` (a valid value at or "
            "above the documented limit; the only state that enters the ordinal "
            f"classifier); `no_detectable_secretion` (measured non-detect) -> {INDETERMINATE_ZERO}; "
            f"`below_detection` (censored below the documented limit) -> "
            f"{INDETERMINATE_BELOW_DETECTION}, never OFF; `missing` -> {MISSING}; a documented "
            f"technical failure -> {TECHNICAL_FAILURE}. None of them carries a SEC-class "
            "inference. An `observed` record below the documented limit is rejected as "
            "inconsistent, not classified. No LOD/2 or other imputed value is used. Without a "
            "documented limit the handoff is not execution-ready for classification."
        ),
        "while a dropout reads zero in either",
        ACTIVE,
    ),
    (
        "SPB1",
        (
            "The frozen design's joint unit is 'donor', but a chip can pair epithelium and "
            "stroma from different people (config/secreted_protein_contract.yaml)."
        ),
        (
            "The joint unit is the SOURCE-PAIR BLOCK: one identified epithelial source and "
            "one identified stromal source. In each planned block the full-cocktail and "
            "minus-E2 chips MUST use the same epithelial and the same stromal source, and "
            "the condition comparison is paired at block level. source_pair_block_id, "
            "epithelial_source_id, stromal_source_id, chip_id and condition are recorded "
            "separately. The pair is never called a patient or donor. Three source-pair "
            "blocks are planned; n = 3 independent biological donors is NOT asserted. Any "
            "source reused across blocks is recorded and no independence claim is made. "
            "The technical duplicate belongs to the same block and never increases "
            "biological n. Patient-level variance, confidence intervals, personalization "
            "and paired-patient claims stay prohibited."
        ),
        "Donor is the biological unit; chips are not independent replicates",
        ACTIVE,
    ),
    (
        "AL1",
        "No treatment-allocation procedure was pre-registered.",
        (
            "Within each source-pair block: prepare the condition chips from the same "
            "sources; randomly assign full cocktail versus minus-E2 to physical chip "
            "IDs/positions, including the optional minus-E2 duplicate in the same step; "
            "randomise processing order independently where operationally possible, or, "
            "where hardware prevents it, counterbalance position and order across blocks; "
            "record the realised allocation before treatment starts, in the pre-run "
            "allocation manifest (prospective_allocation_manifest_template.tsv). No "
            "treatment begins until the manifest is complete. Until real IDs exist the "
            f"manifest reads {PLACEHOLDER}: an operational prerequisite, not an open "
            "interpretation question."
        ),
        "So, on the same donors and the same run:",
        ACTIVE,
    ),
    (
        "RAT1",
        (
            "The RQ5 rationale counted IGFBP-1 'chips' and applied an exchangeability rate, "
            "but the column-to-chip mapping for IGFBP-1 is lost."
        ),
        (
            "The unsupported historical chip count and every exchangeability-rate "
            "calculation are removed. The retained rationale: historical minima and maxima "
            "are descriptive reference extrema, not validated two-sided acceptance "
            "intervals, so they are not used for symmetric control exclusion. The one-sided "
            "expected-state rule of RQ5 is unchanged."
        ),
        "The bands are the ones already in hand",
        ACTIVE,
    ),
    (
        "SPP1X",
        "The frozen design left an optional SPP1 ELISA with no registered call rule.",
        (
            "The optional SPP1 possibility is NOT EXERCISED in this run, and no SPP1 "
            "threshold or call rule is registered. The executable assay set is exactly "
            "PAEP, IGFBP-1 and PRL, plus phase-contrast integrity imaging, which agrees with "
            "frozen §12 ('PAEP, IGFBP-1 and PRL ... Nothing else.')."
        ),
        "A single top-outlet SPP1 ELISA.",
        ACTIVE,
    ),
)


def addendum_rows(selection: str, bands: dict[str, Any]) -> list[dict[str, str]]:
    squashed = re.sub(r"\s+", " ", selection)
    rows = []
    for round_, entries in (
        ("1", ADDENDUM),
        ("2", second_addendum(bands)),
        ("3", THIRD_ADDENDUM),
    ):
        for gap_id, gap, decision, resolves, status in entries:
            if resolves not in squashed:
                raise RuntimeError(
                    f"addendum {gap_id} cites frozen text that is absent: {resolves!r}"
                )
            rows.append(
                {
                    "gap_id": gap_id,
                    "addendum_round": round_,
                    "record_type": ADDENDUM_TYPE,
                    "decided_on": ADDENDUM_DATE,
                    "decided_by": OWNER,
                    "status": status,
                    "gap": gap,
                    "decision": decision,
                    "frozen_text_it_resolves": resolves,
                }
            )
    return rows


#: Pre-run questions the owner has not yet answered. It must stay empty for the
#: handoff to be execution-ready; a test fails if an entry is added.
RESIDUAL_QUESTIONS: tuple[tuple[str, str], ...] = ()


def residual_questions(bands: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return RESIDUAL_QUESTIONS


# --------------------------------------------------------------------------
# The handoff rows
# --------------------------------------------------------------------------


def handoff_rows(
    carried: dict[str, str], bands: dict[str, Any]
) -> list[dict[str, str]]:
    b = boundaries(bands)
    paep_rule = (
        f"Frozen §9.1 three-band rule at day 6 (G7): ON if >= PAEP_ON_LOWER "
        f"({b['PAEP_ON_LOWER']:.3f} pg/mL); OFF if <= PAEP_LOW_UPPER "
        f"({b['PAEP_LOW_UPPER']:.4f} pg/mL); strictly between -> {GRADED}. Boundaries are "
        "the historical ones in hand and are never refitted."
    )
    igfbp1_rule = (
        "IGFBP-1 is the stromal decision variable (RQ6), at day 6 (G7): exact zero -> "
        f"{INDETERMINATE_ZERO} (not {GRADED}); 0 < x <= IGFBP1_OFF_UPPER "
        f"({b['IGFBP1_OFF_UPPER']:.4f} pg/mL) -> {OFF}; IGFBP1_OFF_UPPER < x < "
        f"IGFBP1_ON_LOWER ({b['IGFBP1_ON_LOWER']:.3f} pg/mL) -> {GRADED}; x >= "
        f"IGFBP1_ON_LOWER -> {ON}. PRL never alters the call."
    )
    prl_rule = (
        "Reported and corroborative only (G1; OM-006 context_only/provisional/not_used). "
        "No numeric weight, no band, and it never changes the stromal call. Agreement or "
        "disagreement with IGFBP-1 is recorded descriptively."
    )
    integrity = (
        "Phase-contrast confluence imaging on days 2, 4 and 6 in BOTH channels. Each "
        "channel gets its own INTACT / COMPROMISED / INDETERMINATE call, LOCKED before "
        "assay values are revealed to the person assigning biological calls (G3R); record "
        "image id, channel, day, call, adjudicator, timestamp/version."
    )
    fail_common = (
        f"Levels are applied in the P0/RQ3 order. Measurement states stay distinct (MS1): "
        f"only an `observed` value at or above the documented prospective assay limit "
        f"is classified; no_detectable_secretion -> {INDETERMINATE_ZERO}; below_detection "
        f"-> {INDETERMINATE_BELOW_DETECTION} (never OFF); missing -> {MISSING}; an "
        "`observed` record below the limit is rejected as inconsistent; nothing is "
        f"imputed. A documented technical failure is {TECHNICAL_FAILURE} (G4R). COMPROMISED or INDETERMINATE day-6 integrity in the "
        f"producing compartment gives {INTEGRITY_INVALID} / "
        "biological_interpretation_indeterminate (G3R), never biological OFF; day 3 cannot "
        "rescue it. No QC indeterminacy maps to a SEC class (RQ3)."
    )
    bio = (
        "source-pair block (3 planned blocks; one epithelial + one stromal source, the "
        "same pair for every condition chip of the block; not a patient or donor; no "
        "independence claim if a source is reused; SPB1)"
    )
    minus_e2_dup = (
        "one chip per source-pair block; plus a technical duplicate of this arm in the "
        "same block if capacity permits (§9.2). The duplicate never raises biological "
        "n, and disagreeing duplicates follow G5."
    )
    one_chip = "one chip per source-pair block; no technical duplicate planned (§9.2)"
    dose_minus = "MPA 1 uM + cAMP 250 uM (0.25 mM) + XAV939 10 uM; E2 omitted"
    dose_full = "E2 10 nM + MPA 1 uM + cAMP 250 uM + XAV939 10 uM"
    priming = "days 0-2 E2-only priming (10 nM E2, config/protocols.yaml) as the current protocol runs it"
    paep_controls = (
        f"Requires the block's full-cocktail day-6 PAEP = {ON_CONFIRMED} (H06) and this "
        f"chip's own day-2 PAEP = {LOW_CONFIRMED} (H08); otherwise {NOT_CONFIRMED} and "
        "this block's minus-E2 PAEP is not classified (RQ5)."
    )
    igfbp1_controls = (
        f"Requires the block's full-cocktail day-6 IGFBP-1 = {ON_CONFIRMED} (H07); "
        f"otherwise {NOT_CONFIRMED} and this block's minus-E2 stromal result is not "
        "classified (RQ1, RQ5). PRL cannot rescue it (G1)."
    )
    rows = [
        # --- experimental arm ---
        (
            "H01",
            "minus_E2",
            f"{priming}; days 2-6 minus-E2 cocktail",
            dose_minus,
            "epithelial (top outlet)",
            "PAEP ELISA",
            "day 6 (primary, G7)",
            bio,
            minus_e2_dup,
            integrity,
            paep_rule,
            fail_common + " " + paep_controls,
            "§12 Arm; §9.1; addendum G7, RQ3, RQ5",
        ),
        (
            "H02",
            "minus_E2",
            f"{priming}; days 2-6 minus-E2 cocktail",
            dose_minus,
            "epithelial (top outlet)",
            "PAEP ELISA",
            "day 3 (secondary, G7)",
            bio,
            minus_e2_dup,
            integrity,
            "Secondary trajectory/QC observation only (G7). It cannot override or rescue a day-6 call, and day-3/day-6 disagreement is reported.",
            fail_common,
            "§12 Compartment and timing; addendum G7",
        ),
        (
            "H03",
            "minus_E2",
            f"{priming}; days 2-6 minus-E2 cocktail",
            dose_minus,
            "stromal (bottom outlet)",
            "IGFBP-1 ELISA",
            "day 6 (primary, G7)",
            bio,
            minus_e2_dup,
            integrity,
            igfbp1_rule,
            fail_common
            + " PRL cannot rescue an uninterpretable IGFBP-1 (G1, G2). "
            + igfbp1_controls,
            "§4 (ii)-(iii); §12 Decision semantics; addendum G1, G2, G7, RQ1, RQ5, RQ6",
        ),
        (
            "H04",
            "minus_E2",
            f"{priming}; days 2-6 minus-E2 cocktail",
            dose_minus,
            "stromal (bottom outlet)",
            "IGFBP-1 ELISA",
            "day 3 (secondary, G7)",
            bio,
            minus_e2_dup,
            integrity,
            "Secondary trajectory/QC observation only (G7). The day-3/day-6 comparison is paired by chip identity (§12).",
            fail_common,
            "§12 Compartment and timing; addendum G7",
        ),
        (
            "H05",
            "minus_E2",
            f"{priming}; days 2-6 minus-E2 cocktail",
            dose_minus,
            "stromal (bottom outlet)",
            "PRL ELISA",
            "day 3 and day 6",
            bio,
            minus_e2_dup,
            integrity,
            prl_rule,
            "PRL is never used to decide a call; a missing PRL value affects no call.",
            "§12 Decision semantics; addendum G1",
        ),
        # --- contemporaneous comparator ---
        (
            "H06",
            "full_cocktail",
            f"{priming}; days 2-6 full cocktail",
            dose_full,
            "epithelial (top outlet)",
            "PAEP ELISA",
            "day 6 (and day 3)",
            bio,
            one_chip,
            integrity,
            f"Contemporaneous ON-reference control (§4 control 1). Day 6, one-sided (RQ5): >= PAEP_ON_LOWER ({b['PAEP_ON_LOWER']:.3f} pg/mL) -> {ON_CONFIRMED}, otherwise {NOT_CONFIRMED}. A value above the old historical maximum remains valid ON evidence. The day-3 value is descriptive only (G7).",
            f"Day-6 {NOT_CONFIRMED} -> this block's minus-E2 PAEP is not classified (RQ5). A day-3 value never gates (G7).",
            "§4 Controls 1; addendum RQ5",
        ),
        (
            "H07",
            "full_cocktail",
            f"{priming}; days 2-6 full cocktail",
            dose_full,
            "stromal (bottom outlet)",
            "IGFBP-1 and PRL ELISA",
            "day 3 and day 6",
            bio,
            one_chip,
            integrity,
            f"Contemporaneous stromal ON reference. Day-6 IGFBP-1, one-sided (RQ1, RQ5): exact zero -> {NOT_CONFIRMED} (raw zero retained; not a technical failure without independent QC evidence); >= IGFBP1_ON_LOWER ({b['IGFBP1_ON_LOWER']:.3f} pg/mL) -> {ON_CONFIRMED}; 0 < x < IGFBP1_ON_LOWER -> {NOT_CONFIRMED}. Above the old maximum remains valid ON evidence. Day-3 values and PRL are descriptive only (G7, G1).",
            f"Day-6 {NOT_CONFIRMED} -> this block's minus-E2 stromal result is not classified; PRL cannot rescue the reference (RQ1). A day-3 value never gates (G7).",
            "§4 Controls; addendum G1, RQ1, RQ5",
        ),
        # --- within-chip references, every chip ---
        (
            "H08",
            "all_chips",
            "end of days 0-2 E2-only priming, before the cocktail",
            "E2 10 nM (priming)",
            "epithelial (top outlet)",
            "PAEP ELISA",
            "day 2",
            bio,
            "every chip, both arms",
            integrity,
            f"The contemporaneous LOW/OFF reference (§4 control 2). One-sided (RQ5): <= PAEP_LOW_UPPER ({b['PAEP_LOW_UPPER']:.4f} pg/mL) -> {LOW_CONFIRMED}, otherwise {NOT_CONFIRMED}. A value below the old historical minimum remains valid LOW evidence.",
            f"A minus-E2 chip's own day-2 {NOT_CONFIRMED} -> that chip's minus-E2 PAEP is not classified (RQ5). The full-cocktail chip's day-2 value is reported descriptively.",
            "§4 Controls 2; addendum RQ5",
        ),
        (
            "H09",
            "all_chips",
            "day 0, before E2 priming (one extra aliquot)",
            "none added",
            "epithelial (top outlet)",
            "PAEP ELISA",
            "day 0",
            bio,
            "every chip, both arms",
            integrity,
            "The pre-cocktail PAEP baseline (§4 control 3), fixed at day 0 by owner pre-run clarification (RQ2). A measured referent for the model's E_PAEP = 0; descriptive, not a band, and it gates no call.",
            "Missing -> reported missing; it decides no call.",
            "§4 Controls 3; addendum RQ2",
        ),
        (
            "H10",
            "all_chips",
            "existing day-0 collection window (unchanged: 'same collection windows')",
            "none added",
            "stromal (bottom outlet)",
            "IGFBP-1 and PRL ELISA",
            "day 0",
            bio,
            "every chip, both arms",
            integrity,
            "Existing baseline collection. DESCRIPTIVE (RQ4): chip and source identity retained and unexpected values reported, but no source-pair block is invalidated by its day-0 value. PRL is descriptive (G1).",
            "Missing -> reported missing; it decides no call.",
            "§4 Intervention ('same collection windows'); addendum RQ4",
        ),
    ]
    return [dict(zip(HANDOFF_COLUMNS, row, strict=True)) for row in rows]


# --------------------------------------------------------------------------
# The audit rows
# --------------------------------------------------------------------------


def exit_gate_rows(p: dict[str, Any]) -> list[dict[str, str]]:
    a = p["adhesion_arms"]
    mife = a["hormone_treated_mifepristone"]
    ordinal = (
        f"exact fixed point {ADOPTED_VERSION}: untreated "
        f"{a['untreated']['exact_fixed_point_probability']}, HT "
        f"{a['hormone_treated']['exact_fixed_point_probability']}, HT+mifepristone "
        f"{mife['exact_fixed_point_probability']}; ordinal claim holds = "
        f"{p['ordinal_claim']['holds_on_adopted_model']}"
    )
    mife_premise = (
        f"HT+mifepristone exact P = {mife['exact_fixed_point_probability']} against "
        f"observed {mife['observed_successes']}/{mife['observed_trials']} -> "
        f"{mife['structural_verdict']}, rankable = {mife['rankable']}; role = {mife['role']}"
    )
    mat = p["maternal_fixed_point"]
    om = (
        f"exact fixed point {ADOPTED_VERSION}: E_PAEP HT {mat['hormone_treated_maternal']['E_PAEP']} "
        f"vs E2-primed {mat['e2_primed_maternal']['E_PAEP']}; S_IGFBP1 HT "
        f"{mat['hormone_treated_maternal']['S_IGFBP1']} vs basal "
        f"{mat['basal_maternal']['S_IGFBP1']}; all maternal values binary = "
        f"{p['fixed_point_values_binary']}"
    )
    acyclic = (
        f"{p['structure']['ordered_non_free_nodes']} non-free nodes topologically ordered "
        f"given {p['structure']['free_variables']} free variables (acyclic = "
        f"{p['structure']['acyclic_given_free_variables']})"
    )
    alias = f"S_PRL rule == S_IGFBP1 rule in {ADOPTED_VERSION}: {p['s_prl_rule_equals_s_igfbp1_rule']}"
    rows = [
        (
            "R1",
            "roadmap_item",
            "Calibrate only pre-declared initial-state/rate alternatives against untreated and HT molecular/adhesion data.",
            PARTIALLY_SATISFIED,
            "config/calibration.yaml; config/observation_model_map.tsv; docs/gate3_scope_adjudication.md §3, §3a; docs/stage3_experiment_selection.md §3; docs/experiments/stage3_decision_tables.md tables C-D",
            "No fitting was run, by policy. Nothing ranks scenarios: the runner takes scenario [0] unconditionally, and tests/unit/test_structural_contradiction.py pins this. Selection became structural and evidence-based discrimination (Gate 3a). The only data-based filter is OM-001 (pass/fail). The pre-declared SEC alternatives were evaluated against the in-hand data exactly.",
            "OM-001 passes and OM-002 does not invert on the adopted model. The in-hand data cannot separate SEC-a, SEC-b, SEC-d or SEC-e; only SEC-c is predicted differently on E2-only PAEP, and that call rests on an unrecorded threshold.",
            "There is no quantitative objective, and none may be manufactured. models/specs/parameter_scenarios.yaml still names baseline adoc-core-v0.1.0, and its relay initial-state block is read by nothing. No declared rate exists.",
            "The frozen dropout_e2 data, interpreted by the frozen decision tree and the pre-run addendum.",
            PROSPECTIVE_DATA,
            om,
        ),
        (
            "R2",
            "roadmap_item",
            "Quantify seed and trajectory stability.",
            PARTIALLY_SATISFIED,
            "docs/endpoint/endpoint_run_settings.json; docs/endpoint/README.md; docs/maboss_estimator_semantics.md; docs/u5b_readout_repair/transient_run_settings.json; docs/endpoint_convergence_finding.md",
            "50 disjoint-seed replicates x 20,000 trajectories of the adhesion endpoint at the declared and converged horizons (v0.5.0, executable-identical to v0.4.0), with a seed-structure probe. Trajectory-count dependence at the declared horizon. U5b paired block-reproducibility on v0.5.1 against v0.5.0 (transient).",
            "The across-replicate SD is run-to-run reproducibility of the estimator. It is not a Monte Carlo SE and not biological uncertainty. Fixed seeds give reproducibility, not stability.",
            "The endpoint replicates were not re-run on v0.5.1. The sampling behaviour of the estimator is recorded as not validated (stratified, not i.i.d.). The retained claims are exact enumerations, so this gap does not bind them.",
            "A v0.5.1 replicate run (capped systemd unit), needed only if a finite-horizon or MaBoSS-estimated claim is ever made.",
            IN_REPO_WORK,
            "",
        ),
        (
            "R3a",
            "roadmap_item",
            "One-at-a-time and global sensitivity over uncertain thresholds.",
            NOT_SATISFIED,
            "config/observation_model_map.tsv OM-001, OM-002 claim_ceiling; docs/prl_igfbp1_temporal_axis.md §5",
            "Nothing. The E_PAEP and IGFBP-1 ON/OFF thresholds are implicit and unrecorded.",
            "None.",
            "No threshold may be chosen from the observations that also serve as the feasibility gate or diagnostic. The three-band rule avoids a threshold instead of varying one.",
            "Independent threshold evidence. dropout_e2 avoids a threshold for one arm by reading bands, but that does not supply a threshold to vary, so this row keeps NO_SCHEDULED_ROUTE.",
            NO_SCHEDULED_ROUTE,
            "",
        ),
        (
            "R3b",
            "roadmap_item",
            "One-at-a-time and global sensitivity over uncertain rates.",
            NOT_APPLICABLE,
            "models/superset/adoc-literature-superset-v0.5.1/network.bnd; src/dt_adoc/reporting/endpoint_replicates.py (exact_converged_endpoint); config/calibration.yaml horizon_note",
            "No rate is declared anywhere, and MaBoSS runs on default rates. The network is acyclic given its free variables, so each assignment has a unique fixed point under any positive rates.",
            "Every retained claim is a fixed-point claim, and so does not depend on rates.",
            "NOT_APPLICABLE under the current claim contract only; the roadmap item is not thereby met. It becomes APPLICABLE the moment any transient, finite-horizon, graded or time-course claim is made (U5b measured transient moves of +0.085 to +0.467 occupancy).",
            "Needed only together with a rate layer, which would need calibrated physical time. This project disclaims calibrated time.",
            NONE_REQUIRED,
            acyclic,
        ),
        (
            "R3c",
            "roadmap_item",
            "One-at-a-time and global sensitivity over uncertain initial states.",
            PARTIALLY_SATISFIED,
            "docs/gate3_scope_adjudication.md §1; docs/scrna/klf12_prior_finding.md; docs/scrna/klf12_conditioning_response.tsv; docs/endpoint_convergence_finding.md",
            "An exhaustive enumeration over all 32 cfg-weighted latent assignments for the adhesion arms (v0.4): basal and mifepristone are 0/32 even with the embryo inputs forced true. The E_KLF12_HIGH prior sweep (v0.4), labelled an arbitrary-threshold sensitivity analysis.",
            "No latent assignment inverts the ordinal adhesion claim. Untreated and mifepristone are OFF at the fixed point of every weighted latent assignment (computed on v0.5.1). The strict ordering untreated < HT > HT+mifepristone holds only in expectation, because HT is ON in some assignments and not others.",
            "The relay priors (0.7/0.4/0.2) are hand-set and were never swept. The HT magnitude is a closed-form function of them, 1-(1-p_spp1)(1-p_redundant). The KLF12 sweep is v0.4 and activated nothing.",
            "A v0.5.1 exact sweep of the latent priors. It is cheap, but it informs no retained claim, because none is a magnitude.",
            IN_REPO_WORK,
            ordinal,
        ),
        (
            "R3d",
            "roadmap_item",
            "One-at-a-time and global sensitivity over alternative rules.",
            PARTIALLY_SATISFIED,
            "docs/experiments/stage3_decision_tables.md (table D); docs/experiments/variant_discrimination.md; docs/u6b_muc1_reconciliation/u6b_summary.json; docs/experiments/u8_stage3_rerank/u8_rerank_report.md",
            "Structural evaluation of pre-declared rule classes (SEC, CAMP, HH, GP130, CD98, PC6) and of the U6b E_MUC1_BARRIER family, by exact Boolean marginals. U8 showed v0.5.1 is identical to v0.4 on every quantity Stage 3 reads.",
            "Which rule classes a usable assay can separate, and which it cannot (SEC-a vs SEC-e).",
            "No alternative was propagated into an ensemble or a phenotype distribution. The alternatives are carried as hypotheses, not as an acceptable-model set.",
            "The prospective dropout_e2 data (SEC fork); the TI-03/TI-04/TI-06 unblock conditions in docs/deferred_topology_register.tsv.",
            PROSPECTIVE_DATA,
            "",
        ),
        (
            "R3e",
            "roadmap_item",
            "Global (joint) sensitivity and uncertainty-ensemble propagation.",
            NOT_SATISFIED,
            "models/superset/adoc-literature-superset-v0.5.1/ensemble_definition.tsv; config/calibration.yaml search.retain_acceptable_ensemble",
            "Nothing. Every ensemble panel is structural_only and still names v0.4.0 model keys. Nothing retains an acceptable-model set.",
            "None.",
            "A joint analysis needs a declared uncertainty set over the thresholds, priors and rules above. Only the rule classes exist as declared sets.",
            "Declared uncertainty sets (see R3a-R3d). This is not needed by any retained claim. The threshold set depends on R3a, which has no scheduled route, so this row carries the same route.",
            NO_SCHEDULED_ROUTE,
            "",
        ),
        (
            "R4a",
            "roadmap_item",
            "Test the frozen mifepristone perturbation as held-out validation if it was not used in construction: DIRECTION.",
            NOT_APPLICABLE,
            "docs/results_reproducibility_matrix.md ('Circularity, and the one held-out comparison'); docs/concordance_analysis.md ('An honest weakening of the hold-out claim'); config/perturbations.yaml",
            "Construction provenance. IN_MIFEPRISTONE -| E_PGR (LE002) and -| S_PGR (LE038) both cite SOFIA-HT-002, the same study's methods.",
            "The reduction under mifepristone is guaranteed by construction. It is not a held-out prediction.",
            "The roadmap precondition ('if it was not used in construction') is false for the direction. SOFIA-HT-002 still has no config/evidence_roles.yaml entry.",
            "An independent mifepristone (or other PGR-antagonist) dataset not used to encode the antagonism.",
            NONE_REQUIRED,
            "",
        ),
        (
            "R4b",
            "roadmap_item",
            "Test the frozen mifepristone perturbation as held-out validation: MAGNITUDE.",
            NOT_SATISFIED,
            "config/calibration.yaml structural_contradiction_policy; src/dt_adoc/calibration/adhesion_likelihood.py; docs/gate3_scope_adjudication.md §1, §7",
            "Held out and enforced in code (objectives.py sums only roles=('calibration',)). Scored from the unclipped model probability.",
            "structurally_contradicted AND quantitatively_unscorable_for_ranking. The 1/8 event cannot identify or justify a maternal-rule change with the available data. No maternal rule is altered to accommodate it.",
            "Held-out validation did not succeed. Nor does it falsify the maternal model: the contradiction sits in the complete-antagonism encoding and the embryo/penetrance boundary (Gate 3b, quarantined), which no per-embryo covariate can separate.",
            "Per-embryo metadata (grading, euploidy, chip/donor assignment) or an explicit observation model, both under Gate 3b, which the owner has not opened.",
            NO_SCHEDULED_ROUTE,
            mife_premise,
        ),
        (
            "R5",
            "roadmap_item",
            "Report ensembles of acceptable models when parameters are not identifiable.",
            PARTIALLY_SATISFIED,
            "docs/identifiability_analysis.md; docs/design_alias_note.md; docs/experiments/stage3_decision_tables.md tables A, C; docs/coupling_adjudication.md; models/superset/adoc-literature-superset-v0.5.1/ensemble_definition.tsv",
            "Non-identifiability is reported exhaustively: alias classes, design classes, SEC-a/SEC-e indistinguishable on every usable assay, S_PRL = S_IGFBP1.",
            "What cannot be identified is stated. No ensemble of acceptable executable models is reported.",
            "calibration.yaml sets retain_acceptable_ensemble: true, but nothing retains one (pinned). The committed model is one member reported as the model.",
            "An acceptable-model set defined by the frozen SEC decision tree after the dropout_e2 data, carried as an explicit ensemble.",
            PROSPECTIVE_DATA,
            alias,
        ),
        (
            "E1",
            "exit_gate",
            "the model reproduces qualitative molecular directions",
            PARTIALLY_SATISFIED,
            "config/observation_model_map.tsv (OM-001, OM-002, OM-003-OM-016); docs/calibration_observation_audit.md; docs/results_reproducibility_matrix.md",
            "OM-001 (full cocktail > E2-only on E_PAEP) and OM-002 (no S_IGFBP1 inversion, basal vs HT) at the exact fixed point on v0.5.1.",
            "Two directions hold: OM-001 and OM-002. Both are circular, because they are the model's only two measured nodes and are the filter. Both are binary at the fixed point.",
            "OM-001 is not the registered HT-vs-untreated claim, which has no untreated PAEP arm. The IGFBP-1 day-3 and monotone claims are rejected, PRL is not evaluable, and the IGFBP-1-before-PRL onset order cannot be expressed (S_PRL = S_IGFBP1). There is no graded direction.",
            "Three sources, all needed. (1) The dropout_e2 data, which give one prospective molecular direction on both usable assays. (2) S_PRL/S_IGFBP1 de-aliasing (TI-04), which stays deferred with unmet unblock conditions. (3) An untreated PAEP arm, for the registered claim. Sources (2) and (3) have no scheduled route, so the row carries the most restrictive route.",
            NO_SCHEDULED_ROUTE,
            om + "; " + alias,
        ),
        (
            "E2",
            "exit_gate",
            "gives uncertainty-aware adhesion agreement",
            NOT_SATISFIED,
            "config/calibration.yaml adhesion_objective; docs/gate3_scope_adjudication.md §1-§3, §5, §7-§8; docs/endpoint/endpoint_run_settings.json",
            "The ordinal claim at the exact fixed point on v0.5.1, and the structural verdict per arm.",
            "Only the ordinal claim untreated < HT > HT+mifepristone. Adhesion is diagnostic_ordinal and not magnitude-fitted.",
            "The HT magnitude (0.82) is set entirely by hand-set relay priors and is not maternal biology. The mifepristone arm is structurally_contradicted. No per-embryo covariate exists, so embryo variability cannot be separated from maternal mechanism. Gate 3b is quarantined.",
            "Per-embryo metadata or an explicit observation model (Gate 3b), which is not scheduled.",
            NO_SCHEDULED_ROUTE,
            ordinal + "; " + mife_premise,
        ),
        (
            "E3",
            "exit_gate",
            "predicts the held-out perturbation",
            NOT_SATISFIED,
            "see R4a and R4b",
            "The mifepristone direction (not held out) and its magnitude (held out).",
            "No held-out perturbation is predicted. The direction was constructed, and the magnitude is structurally_contradicted and unscorable.",
            "The dropout_e2 result will re-adjudicate the SEC fork, which is model construction. Under AGENTS.md ('do not tune ... on the same held-out outcomes used for validation') it cannot also serve as this criterion's held-out validation.",
            "A held-out perturbation dataset that is not used in construction and is not scheduled for any fork adjudication.",
            NO_SCHEDULED_ROUTE,
            mife_premise,
        ),
        (
            "E4",
            "exit_gate",
            "does not depend on one fragile assumption",
            NOT_SATISFIED,
            "docs/stage3_experiment_selection.md §1, §7; docs/v05_u8_stage3_rerank.md §1; docs/deferred_topology_register.tsv; docs/gate3_scope_adjudication.md §3a; this audit's sensitivity_inventory.tsv",
            "Whether the retained claims survive the declared alternatives. No latent assignment inverts the ordinal adhesion claim: untreated and mifepristone are OFF in every weighted assignment, and the strict ordering holds in expectation. The molecular claims were not tested under the alternative SEC classes as an ensemble.",
            "Not demonstrated. The retained molecular behaviour rests on the committed SEC-a rule, an open fork that is the reason the prospective experiment exists.",
            "Single points of dependence: SEC-a; the complete-antagonism mifepristone encoding; the implicit E_PAEP threshold; the hand-set relay priors (adhesion magnitude); the AC01 alias verdict, which depends on the post-extraction D1 call. There is no OAT or global sensitivity (R3a, R3e).",
            "Three routes, all needed. (1) The dropout_e2 data, for the SEC fork. (2) Declared uncertainty sets and their propagation, which is in-repo work. (3) Independent threshold evidence (R3a) and an alternative to the complete-antagonism encoding (R4b). Route (3) has no scheduled source, so the row carries the most restrictive of the three routes.",
            NO_SCHEDULED_ROUTE,
            ordinal,
        ),
    ]
    columns = tuple(c for c in EXIT_GATE_COLUMNS if c != "criterion_verbatim")
    out = []
    for row in rows:
        record = dict(zip(columns, row, strict=True))
        record["criterion_verbatim"] = ROADMAP_QUOTES[record["criterion_id"]]
        assert record["status"] in STATUSES, record
        out.append({c: record[c] for c in EXIT_GATE_COLUMNS})
    return out


def derive_overall_status(rows: list[dict[str, str]]) -> str:
    gate = [r for r in rows if r["kind"] == "exit_gate"]
    unmet = [r for r in gate if r["status"] not in (SATISFIED, NOT_APPLICABLE)]
    if not unmet:
        return CLOSED
    if any(r["unblock_route"] == NO_SCHEDULED_ROUTE for r in unmet):
        return BLOCKED
    return PARTIAL


def claim_rows(p: dict[str, Any]) -> list[dict[str, str]]:
    ceilings = "config/calibration.yaml; config/observation_model_map.tsv"
    rows = [
        (
            "C01",
            "MAY",
            "The adopted model's prior-weighted expected fixed-point occupancy of adhesion orders untreated < hormone_treated > hormone_treated_mifepristone. This holds in expectation, not assignment by assignment; no latent assignment inverts it.",
            "computed premise (exact enumeration, v0.5.1)",
            "config/calibration.yaml retained_ordinal_claim",
        ),
        (
            "C02",
            "MAY",
            "Full cocktail (E2 + MPA + cAMP + XAV939) > E2-only priming on E_PAEP (OM-001), as a binary feasibility gate at the fixed point.",
            "computed premise; OM-001 active_constraint",
            "OM-001 claim_ceiling",
        ),
        (
            "C03",
            "MAY",
            "S_IGFBP1 does not invert between basal and hormone-treated maternal states (OM-002, non-exclusionary diagnostic).",
            "computed premise; OM-002 active_diagnostic",
            "OM-002 claim_ceiling",
        ),
        (
            "C04",
            "MAY",
            "The held-out mifepristone magnitude is structurally_contradicted (observed 1/8, model P exactly 0 at the fixed point) and quantitatively_unscorable_for_ranking. It cannot identify or justify a maternal-rule change.",
            "computed premise; structural_verdict",
            "config/calibration.yaml structural_contradiction_policy",
        ),
        (
            "C05",
            "MAY",
            "What cannot be identified is stated: SEC-a vs SEC-e on every usable assay; S_PRL = S_IGFBP1; the recorded alias classes.",
            "docs/experiments/stage3_decision_tables.md; computed premise",
            "docs/stage3_experiment_selection.md §7",
        ),
        (
            "C06",
            "MAY",
            "dropout_e2 remains the first-ranked prospective experiment on v0.5.1, conditional on the frozen Stage-3 criteria and on the D1 call.",
            "docs/experiments/u8_stage3_rerank/u8_rerank_summary.json",
            "docs/v05_u8_stage3_rerank.md §1, §4",
        ),
        (
            "N01",
            "MAY_NOT",
            "Any quantitative or magnitude-fitted calibration, or any fitted objective, including a replacement for the demoted adhesion likelihood.",
            "config/calibration.yaml no_replacement_objective",
            ceilings,
        ),
        (
            "N02",
            "MAY_NOT",
            "That mifepristone is a successful validation, or that the model predicts the held-out perturbation.",
            "R4b, E3",
            "config/calibration.yaml structural_contradiction_policy",
        ),
        (
            "N03",
            "MAY_NOT",
            "That the mifepristone direction is an independent prediction.",
            "R4a (LE002/LE038 cite SOFIA-HT-002)",
            "docs/results_reproducibility_matrix.md",
        ),
        (
            "N04",
            "MAY_NOT",
            "That the maternal model is falsified by, or correct at, the mifepristone arm.",
            "R4b",
            "config/calibration.yaml structural_contradiction_policy",
        ),
        (
            "N05",
            "MAY_NOT",
            "Any physical time, day count, delay or transition rate. MaBoSS time is dimensionless and the fixed-point horizon is not a day.",
            "calibrated_physical_time = false; duration_units = relative_only",
            "config/calibration.yaml time_units",
        ),
        (
            "N06",
            "MAY_NOT",
            "Graded molecular agreement or ranking power at the fixed point: E_PAEP and S_IGFBP1 are binary there.",
            "computed premise",
            "config/calibration.yaml horizon_note",
        ),
        (
            "N07",
            "MAY_NOT",
            "The registered P1-PAEP 'HT versus untreated' claim; no untreated PAEP arm exists.",
            "OM-001",
            "OM-001 claim_ceiling",
        ),
        (
            "N08",
            "MAY_NOT",
            "PRL as a calibration or validation term, or the IGFBP-1-before-PRL onset order as model behaviour.",
            "OM-006/OM-014/OM-016; S_PRL = S_IGFBP1",
            "OM-006 exclusion_reason ('No numeric weight, ever.')",
        ),
        (
            "N09",
            "MAY_NOT",
            "Any patient-level variance, standard error, confidence interval, paired-donor test or personalization claim.",
            "chips are not independent units",
            "config/adoc_chip_donor_provenance.tsv; SOFIA-COMM-005",
        ),
        (
            "N10",
            "MAY_NOT",
            "Attribution of any effect to MPA, cAMP or XAV939 individually.",
            "OM-017",
            "OM-017",
        ),
        (
            "N11",
            "MAY_NOT",
            "That the model is robust to its uncertain assumptions, or has been through one-at-a-time or global sensitivity analysis.",
            "R3a, R3e, E4",
            "this audit",
        ),
        (
            "N12",
            "MAY_NOT",
            "That simulated adhesion probabilities are experimental or clinical attachment probabilities, or that the model is a validated patient replica.",
            "AGENTS.md model and claim boundaries",
            "docs/endpoint/README.md",
        ),
        (
            "N13",
            "MAY_NOT",
            "That a future dropout_e2 result validates the model. It is construction and discrimination evidence for the SEC fork.",
            "E3",
            "AGENTS.md leakage control",
        ),
        (
            "N14",
            "MAY_NOT",
            "That Phase 1B is closed.",
            "derive_overall_status",
            "this audit",
        ),
    ]
    return [dict(zip(CLAIM_COLUMNS, row, strict=True)) for row in rows]


def sensitivity_rows() -> list[dict[str, str]]:
    rows = [
        (
            "simulator_seed_trajectory_reproducibility",
            "RUN",
            "adoc-literature-superset-v0.5.0",
            "docs/endpoint/endpoint_run_settings.json; docs/endpoint/endpoint_replicates.tsv",
            "50 disjoint seed blocks x 20,000 trajectories, declared and converged horizons, seed-structure probe",
            "a v0.5.1 re-run; an i.i.d. Monte Carlo SE (not established for this estimator)",
        ),
        (
            "simulator_seed_trajectory_reproducibility",
            "RUN",
            "adoc-literature-superset-v0.5.1 vs v0.5.0",
            "docs/u5b_readout_repair/transient_run_settings.json; docs/u5b_readout_repair/transient_comparison.tsv",
            "pre-registered paired block-reproducibility screen of the U5b transient (R = 20)",
            "a coverage or confidence claim (withdrawn in U5b)",
        ),
        (
            "endpoint_horizon_stability",
            "RUN",
            "adoc-literature-superset-v0.3.0/v0.4.0",
            "docs/endpoint_convergence_finding.md; docs/calibration_observation_audit.md (horizon table)",
            "max_time sweep to the fixed point; trajectory count at the declared horizon; E_PAEP/S_IGFBP1 saturation curves",
            "a v0.5.1 horizon sweep (fixed-point values are computed exactly instead)",
        ),
        (
            "parameter_rate_sensitivity",
            "NOT_RUN",
            "none",
            "models/superset/adoc-literature-superset-v0.5.1/network.bnd",
            "nothing: no rate is declared",
            "one-at-a-time or global rate variation. Fixed-point claims do not depend on rates (acyclic given free variables)",
        ),
        (
            "threshold_sensitivity",
            "NOT_RUN",
            "none",
            "config/observation_model_map.tsv OM-001/OM-002",
            "nothing: the thresholds are implicit, and choosing them from the same data is forbidden",
            "any threshold variation",
        ),
        (
            "initial_state_sensitivity",
            "PARTIAL",
            "adoc-literature-superset-v0.4.0",
            "docs/gate3_scope_adjudication.md §1; docs/scrna/klf12_conditioning_response.tsv",
            "exhaustive 32-assignment enumeration of the latent Boolean states for the adhesion arms; E_KLF12_HIGH prior sweep (arbitrary-threshold sensitivity)",
            "a sweep of the relay priors; any v0.5.1 re-run",
        ),
        (
            "alternative_rule_sensitivity",
            "PARTIAL",
            "adoc-literature-superset-v0.4.0 and v0.5.1",
            "docs/experiments/stage3_decision_tables.md; docs/experiments/variant_discrimination.md; docs/experiments/u8_stage3_rerank/u8_rerank_report.md",
            "pre-declared rule classes per fork, evaluated by exact Boolean marginals across candidate arms",
            "propagating the classes into phenotype or adhesion distributions",
        ),
        (
            "structural_rule_family_evaluation",
            "RUN",
            "adoc-literature-superset-v0.5.1 (in-memory variants)",
            "docs/v05_u6b_muc1_reconciliation.md; docs/u6b_muc1_reconciliation/u6b_summary.json",
            "E_MUC1_BARRIER family: structural and endpoint consequences, evaluation only",
            "adoption (TI-06 deferred)",
        ),
        (
            "uncertainty_ensemble_propagation",
            "NOT_RUN",
            "none",
            "models/superset/adoc-literature-superset-v0.5.1/ensemble_definition.tsv",
            "nothing: every panel is structural_only",
            "any acceptable-model ensemble or joint propagation",
        ),
    ]
    return [dict(zip(SENSITIVITY_COLUMNS, row, strict=True)) for row in rows]


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _tsv(columns: tuple[str, ...], rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=columns, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def frozen_decision_tree(selection: str) -> list[dict[str, str]]:
    """Frozen §5, row by row and verbatim: PAEP, IGFBP-1, supported, model action."""
    rows = []
    for line in _section(selection, "## 5.").splitlines():
        if not line.startswith("| **"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            raise RuntimeError(f"frozen §5 row no longer has four cells: {line!r}")
        rows.append(
            dict(
                zip(("paep", "igfbp1", "supported", "model_action"), cells, strict=True)
            )
        )
    if len(rows) != 5:
        raise RuntimeError(f"frozen §5 has {len(rows)} outcome rows, expected 5")
    return rows


#: What the pre-run addendum adds to a frozen §5 row. It adds to the row and
#: rewrites nothing in it.
TREE_AMENDMENTS = {
    ("**ON**", "**ON**"): (
        "G8: the registered E2-only PAEP call this row defers to does not exist. The "
        "result narrows to SEC-b OR SEC-c and establishes only what they share: "
        "concurrent E2 during days 2-6 is not required for the observed epithelial "
        "secretory output under this protocol. It does NOT distinguish SEC-b from SEC-c."
    ),
    ("**indeterminate** in either channel", "—"): (
        "RQ3: `graded_not_boolean` applies ONLY to a valid level-4 value that lies "
        "between OFF and ON after every upstream QC level has passed. QC and measurement "
        "indeterminacies are NOT graded and carry no SEC-class inference: "
        "MISSING/TECHNICAL_FAILURE, integrity_invalid, CONTROL_STATE_NOT_CONFIRMED, "
        "INDETERMINATE_ZERO and TECHNICAL_DISCORDANCE. Each is recorded as "
        "NO_CLASS_ASSIGNMENT with its reason."
    ),
}


def _tree_rows(
    selection: str, table_c: dict[str, tuple[str, str]]
) -> list[dict[str, str]]:
    tree = frozen_decision_tree(selection)
    for row in tree:
        key = (
            row["paep"].replace("**", "").split()[0],
            row["igfbp1"].replace("**", ""),
        )
        if key[0] in ("ON", "OFF") and key[1] in ("ON", "OFF"):
            predicted = sorted(c for c, v in table_c.items() if v == key)
            named = sorted(re.findall(r"SEC-[a-e]", row["supported"]))
            if predicted != named:
                raise RuntimeError(
                    f"frozen §5 row {key} names {named}; frozen table C predicts {predicted}"
                )
        row["addendum"] = TREE_AMENDMENTS.get((row["paep"], row["igfbp1"]), "")
    return tree


_UNIT_TO_UM = {"nM": 1e-3, "uM": 1.0, "mM": 1e3}
_AGENTS = ("E2", "MPA", "cAMP", "XAV939")


def parse_doses(text: str, *, agent_first: bool) -> dict[str, float]:
    """Agent -> concentration in µM, from 'MPA 1 uM' or '1 uM MPA' phrasing."""
    text = text.replace("µ", "u")
    if agent_first:
        pattern = r"\b(E2|MPA|cAMP|XAV939) ([0-9.]+) (nM|uM|mM)\b"
        found = [(a, v, u) for a, v, u in re.findall(pattern, text)]
    else:
        pattern = r"\b([0-9.]+) (nM|uM|mM) (E2|MPA|cAMP|XAV939)\b"
        found = [(a, v, u) for v, u, a in re.findall(pattern, text)]
    doses: dict[str, float] = {}
    for agent, value, unit in found:
        if agent in doses:
            raise RuntimeError(f"dose text names {agent} twice: {text!r}")
        doses[agent] = round(float(value) * _UNIT_TO_UM[unit], 9)
    return doses


def expected_doses(protocol_notes: dict[str, str]) -> dict[str, dict[str, float]]:
    """The canonical dose sets, from config/protocols.yaml."""
    full = parse_doses(protocol_notes["cocktail_note"], agent_first=False)
    priming = parse_doses(protocol_notes["priming_note"], agent_first=False)
    if sorted(full) != sorted(_AGENTS) or sorted(priming) != ["E2"]:
        raise RuntimeError(
            f"config/protocols.yaml doses no longer parse: {full}, {priming}"
        )
    return {
        "full_cocktail": full,
        "minus_E2": {a: v for a, v in full.items() if a != "E2"},
        "priming": priming,
        "none": {},
    }


def _row_dose_kind(row: dict[str, str]) -> str:
    if row["reagent_dose"] == "none added":
        return "none"
    if row["arm"] == "all_chips":
        return "priming"
    return row["arm"]


def check_handoff_against_frozen(
    rows: list[dict[str, str]],
    md: str,
    carried: dict[str, str],
    protocol_notes: dict[str, str],
) -> None:
    """The handoff's own statements must agree with the frozen quotes and the protocol."""
    unmark = lambda text: " ".join(text.replace("**", "").replace("µ", "u").split())
    by_id = {r["row_id"]: r for r in rows}
    canonical = expected_doses(protocol_notes)
    for row in rows:
        kind = _row_dose_kind(row)
        got = parse_doses(row["reagent_dose"], agent_first=True)
        if got != canonical[kind]:
            raise RuntimeError(
                f"handoff {row['row_id']} doses {got} differ from config/protocols.yaml "
                f"{kind} doses {canonical[kind]}"
            )
        if kind == "minus_E2" and "E2 omitted" not in row["reagent_dose"]:
            raise RuntimeError(
                f"handoff {row['row_id']} does not state that E2 is omitted"
            )
    if parse_doses(unmark(carried["arm"]), agent_first=True) != canonical["minus_E2"]:
        raise RuntimeError("the frozen arm's doses differ from config/protocols.yaml")
    if "E2 omitted" not in unmark(carried["arm"]):
        raise RuntimeError("frozen arm no longer omits E2")
    if "E2 omitted" not in by_id["H01"]["reagent_dose"]:
        raise RuntimeError("handoff H01 does not carry the frozen E2 omission")
    arm = carried["arm"].split("Days 2–6: ")[1].replace("**", "").rstrip(".")
    if f"**{arm}**" not in md:
        raise RuntimeError(
            "handoff protocol table does not carry the frozen arm verbatim"
        )
    if "days 2, 4 and 6" not in unmark(carried["imaging"]):
        raise RuntimeError("frozen imaging days changed")
    for row in rows:
        if "days 2, 4 and 6 in BOTH channels" not in row["integrity_control"]:
            raise RuntimeError(
                f"handoff {row['row_id']} imaging differs from the frozen days"
            )
        if "source-pair block (3 planned blocks" not in row["biological_replicate"]:
            raise RuntimeError(
                f"handoff {row['row_id']} unit is not the SPB1 source-pair block"
            )
    # Frozen §12 plans three donors; SPB1 keeps the count of three and replaces the unit.
    if "Three donors" not in carried["replication"]:
        raise RuntimeError("frozen replication changed")
    outlets = unmark(carried["outlets"])
    if "Top outlet for PAEP, bottom outlet for IGFBP-1 and PRL" not in outlets:
        raise RuntimeError("frozen outlets changed")
    for row in rows:
        if row["assay"].startswith("PAEP") and "top outlet" not in row["compartment"]:
            raise RuntimeError(
                f"handoff {row['row_id']} puts PAEP outside the top outlet"
            )
        if (
            "IGFBP-1" in row["assay"] or row["assay"].startswith("PRL")
        ) and "bottom outlet" not in row["compartment"]:
            raise RuntimeError(
                f"handoff {row['row_id']} puts a stromal analyte outside the bottom outlet"
            )
    if "day-3 and day-6 windows" not in outlets:
        raise RuntimeError("frozen sampling days changed")
    for day in ("day 3", "day 6"):
        if not any(day in r["timepoint"] for r in rows if r["arm"] == "minus_E2"):
            raise RuntimeError(f"handoff minus-E2 arm does not sample {day}")
    full_cell = md.split("| **Full cocktail (comparator)** |", 1)[1].split("\n", 1)[0]
    if parse_doses(full_cell, agent_first=True) != canonical["full_cocktail"]:
        raise RuntimeError(
            "handoff protocol table's full-cocktail doses differ from the protocol"
        )
    if any("SPP1" in r["assay"] for r in rows):
        raise RuntimeError("SPP1 is not exercised in this run (SPP1X)")


def render_handoff_md(
    handoff: list[dict[str, str]],
    bands: dict[str, Any],
    tree: list[dict[str, str]],
    overall: str,
) -> str:
    bd = boundaries(bands)
    full_dose = next(r for r in handoff if r["row_id"] == "H06")["reagent_dose"]
    lines = [
        "# Prospective `dropout_e2` experiment — handoff to the experimental team",
        "",
        (
            f"> **Generated file — do not edit.** Regenerate with `pixi run {TASK}`. "
            "The frozen text quoted in the next section is rendered from "
            "`docs/stage3_experiment_selection.md` itself, and the §5 decision table is "
            "copied cell for cell. The doses are cross-checked against "
            "`config/protocols.yaml`, and the band limits are recomputed from the "
            "canonical protein table. The handoff's own dose, day, compartment and "
            "replication statements are asserted to agree with the frozen quotes. The "
            "build fails if any of these diverge. The remaining prose is a restatement "
            "for the bench, and where it differs, the quotes and the addendum "
            "(`pre_run_analysis_addendum.tsv`) govern."
        ),
        "",
        (
            f"Frozen design: {FROZEN_DATE}. Pre-run analysis addendum: {ADDENDUM_DATE}, recorded "
            "before any prospective data exist. The frozen text is unchanged. The addendum "
            "only closes ambiguities in it."
        ),
        "",
        "## The frozen design, verbatim",
        "",
        (
            "Quoted from `docs/stage3_experiment_selection.md` by the generator. This is "
            "the frozen wording. Where the pre-run addenda say so it is superseded: the "
            "joint unit is now the source-pair block (SPB1), and the optional SPP1 assay "
            "is not exercised (SPP1X)."
        ),
        "",
    ]
    lines += [
        f"- ({heading.strip('# .')}) {phrase}"
        for _field, phrase, heading in FROZEN_PHRASES
    ]
    lines += [
        "",
        "## What is being tested",
        "",
        (
            "Whether the epithelial secretory programme still needs E2 once the progestin "
            "cocktail is running. The model's competing rule classes predict different "
            "PAEP (top) × IGFBP-1 (bottom) patterns when E2 is omitted on days 2–6. "
            "**No embryo is needed.** This is a discrimination experiment. It is not a "
            "validation of the model, and it is not a clinical or patient-level test."
        ),
        "",
        "## Protocol",
        "",
        "| | Days 0–2 | Days 2–6 |",
        "|---|---|---|",
        "| **Minus-E2 arm** | E2-only priming (10 nM E2), unchanged | **MPA 1 µM + cAMP 0.25 mM + XAV939 10 µM, E2 omitted** |",
        f"| **Full cocktail (comparator)** | E2-only priming (10 nM E2), unchanged | {full_dose} |",
        "",
        (
            "Nothing else changes: same chip, same flow rate, same medium base, same "
            "collection windows. Both arms run on the same source-pair blocks in the same "
            "run. Historical chips are never the comparator."
        ),
        "",
        "## Unit and replication",
        "",
        (
            "- **3 planned source-pair blocks.** A block is one identified epithelial source "
            "plus one identified stromal source. The full-cocktail and minus-E2 chips of a "
            "block MUST use the same epithelial and the same stromal source (SPB1)."
        ),
        (
            "- A block is **not** a patient or donor, and n = 3 independent biological "
            "donors is not asserted. A source reused across blocks is recorded, and then no "
            "independence claim is made."
        ),
        (
            "- **A technical duplicate of the minus-E2 arm, in the same block, if material "
            "and chip capacity permit.** It never increases biological n and is never "
            "reported as if it did."
        ),
        (
            "- **No patient-level variance, standard error, confidence interval, "
            "personalization or paired-patient claim** may be derived. Results are "
            "reported per source-pair block."
        ),
        "",
        "## Allocation (required before treatment)",
        "",
        (
            "Within each source-pair block, conditions are **randomly assigned** to "
            "physical chip IDs and positions, with the optional minus-E2 duplicate included "
            "in the same step. Processing order is randomised independently where "
            "operationally possible, or, where hardware prevents it, counterbalanced "
            "across blocks. The realised allocation is recorded in "
            "`prospective_allocation_manifest_template.tsv` **before treatment starts**, "
            "and no treatment begins until it is complete (AL1). The manifest records the "
            "block, epithelial source, stromal source, chip, condition, duplicate link, "
            "position, processing order, randomisation record, time and person, and three "
            f"methods. `allocation_method` must be `{RANDOMIZED}`: condition assignment is "
            "always randomised. `position_allocation_method` and `order_allocation_method` "
            f"are `{RANDOMIZED}`, or `{COUNTERBALANCED}` only when hardware prevents "
            "randomising them, and counterbalancing must vary the within-block layout "
            "across blocks. Positions and processing-order slots are unique in the run. "
            "Until real IDs exist it reads `REQUIRED_PRE_RUN_MANIFEST`, which is an "
            "operational prerequisite, not an open interpretation question."
        ),
        "",
        (
            "**Assay metadata (required before classification).** "
            "`prospective_assay_metadata_template.tsv` must carry a documented detection "
            "limit for each of PAEP, IGFBP-1 and PRL on this run. Without one, nothing is "
            "classified (MS1). The historical 5 pg/mL IGFBP-1 figure is manuscript prose "
            "and is not used."
        ),
        "",
        "## Sampling",
        "",
        "| Sample | Compartment | Assay | When | Role |",
        "|---|---|---|---|---|",
        "| every chip | top outlet | PAEP | **day 0**, before E2 priming (one extra aliquot; RQ2) | referent for the model's E_PAEP = 0; descriptive, gates no call |",
        "| every chip | bottom outlet | IGFBP-1, PRL | day 0 (existing window) | baseline; descriptive, gates no call (RQ4) |",
        "| every chip | top outlet | PAEP | day 2 (end of E2-only priming) | contemporaneous E2-only (low) reference |",
        "| every chip | top outlet | PAEP | day 3, **day 6** | day 6 decides, day 3 is secondary |",
        "| every chip | bottom outlet | IGFBP-1, PRL | day 3, **day 6** | day 6 decides, day 3 is secondary; carry chip identity so day 3/day 6 are paired |",
        "| every chip | both channels | phase-contrast confluence imaging | days 2, 4, 6 | compartment integrity, epithelial **and** stromal |",
        "",
        (
            "**Assays: PAEP, IGFBP-1, PRL by the existing ELISAs, plus phase-contrast "
            "integrity imaging. Nothing else.** The optional SPP1 assay is not exercised in "
            "this run (SPP1X). No CD98, pSTAT3, α-DG-N, GLI1/PTCH1, embryos or attachment."
        ),
        "",
        "## Pre-registered interpretation (fixed before the run)",
        "",
        "Applied per source-pair block, **in this order**. A failure at an earlier step stops every later step.",
        "",
    ]
    lines += [f"{i}. {step}" for i, step in enumerate(PRECEDENCE, start=1)]
    lines += [
        "",
        (
            f"**1. Technical validity and measurement state (MS1).** Only an `observed` "
            "value at or above the documented prospective assay limit is classified. "
            f"`no_detectable_secretion` → `{INDETERMINATE_ZERO}`; `below_detection` → "
            f"`{INDETERMINATE_BELOW_DETECTION}`, **never OFF**; `missing` → `{MISSING}`; an "
            "`observed` record below the limit is rejected as inconsistent. No LOD/2 or "
            f"other value is imputed. A documented technical failure is `{TECHNICAL_FAILURE}`, "
            "never ON, OFF or indeterminate. There is no averaging over blocks and no "
            "inference from PRL. Without an already documented pre-run "
            "technical-repeat SOP, a failed assay or chip stays failed. A measurement is "
            "never repeated because its value is inconvenient; if a legitimate repeat "
            "happens, the original record and the reason for the repeat are both kept "
            "(G4R). With duplicates: concordant calls are kept; one failure plus one "
            "valid replicate keeps the valid one (the loss is noted); two valid but "
            f"different calls give `{TECHNICAL_DISCORDANCE}`. Duplicates are never "
            "averaged and never raise biological n."
        ),
        "",
        (
            "**2. Compartment integrity.** From the day-2/4/6 images, each channel "
            "independently gets `INTACT`, `COMPROMISED` or `INDETERMINATE`. **These calls "
            "are locked before any PAEP/IGFBP-1/PRL value is revealed to the person "
            "assigning biological calls** (G3R). Condition identity need not be blinded if "
            "that is impossible, but secretion results must not influence the integrity "
            "judgement. Record the image id, channel, day, call, adjudicator and "
            "timestamp/version. `COMPROMISED` means clear monolayer loss, detachment or "
            "denudation, enough that a change in secretion could come from losing the "
            "producing cells. If the relevant channel is COMPROMISED or INDETERMINATE at "
            f"day 6, its molecular result is `{INTEGRITY_INVALID}` and day 3 cannot rescue "
            "it. **Loss of epithelium mimics PAEP OFF, and loss of stroma mimics IGFBP-1 "
            "OFF; neither is ever read as biological OFF.** A validated quantitative "
            "confluence SOP may replace this only through another documented pre-run "
            "addendum, before assay values are unblinded."
        ),
        "",
        (
            "**3. Contemporaneous expected-state confirmation (one-sided, RQ5).** Each "
            "required reference must show the state it exists to show. **Boundaries are "
            "never refitted, and a value beyond the old historical extreme on the expected "
            "side still confirms.**"
        ),
        "",
        (
            f"- Full-cocktail PAEP, day 6: ≥ {bd['PAEP_ON_LOWER']:,.3f} pg/mL → `{ON_CONFIRMED}`; "
            f"otherwise `{NOT_CONFIRMED}`."
        ),
        (
            f"- E2-only PAEP, day 2 (the minus-E2 chip's own sample): ≤ "
            f"{bd['PAEP_LOW_UPPER']:,.4f} pg/mL → `{LOW_CONFIRMED}`; otherwise `{NOT_CONFIRMED}`."
        ),
        (
            f"- Full-cocktail IGFBP-1, day 6: exact zero → `{NOT_CONFIRMED}` (raw zero "
            "kept; not a technical failure without independent QC evidence; PRL cannot "
            f"rescue it); ≥ {bd['IGFBP1_ON_LOWER']:,.3f} pg/mL → `{ON_CONFIRMED}`; "
            f"0 < x < {bd['IGFBP1_ON_LOWER']:,.3f} → `{NOT_CONFIRMED}`."
        ),
        "",
        (
            "A reference that is not confirmed invalidates the corresponding minus-E2 call "
            "**for that source-pair block only**: the PAEP references gate PAEP, and the IGFBP-1 "
            "reference gates the stromal call. There is no majority rule, no 2-of-3 block "
            "rule, no run-level average and no systematic-failure threshold. Day-0 IGFBP-1 "
            "and the day-0 PAEP baseline are descriptive and never gate (RQ2, RQ4). Day-3 "
            "control values never gate (G7)."
        ),
        "",
        "**4. Molecular calls (day 6).**",
        "",
        (
            f"- **PAEP (top):** ≥ {bd['PAEP_ON_LOWER']:,.3f} → ON; ≤ {bd['PAEP_LOW_UPPER']:,.4f} "
            f"→ OFF; strictly between → `{GRADED}`. The intermediate result is admissible, "
            "not a tie to be broken."
        ),
        (
            f"- **IGFBP-1 (bottom), the stromal decision variable (RQ6):** exact zero → "
            f"`{INDETERMINATE_ZERO}` (not graded); 0 < x ≤ {bd['IGFBP1_OFF_UPPER']:,.4f} "
            f"(IGFBP1_OFF_UPPER, the largest non-zero day-0 value) → OFF; between → "
            f"`{GRADED}`; ≥ {bd['IGFBP1_ON_LOWER']:,.3f} (IGFBP1_ON_LOWER, the smallest "
            "non-zero day-6 value) → ON. So a positive value below the historical day-0 "
            "minimum is OFF, and a value above the historical day-6 maximum is ON: the "
            "historical ranges are not symmetric acceptance bands."
        ),
        (
            "- **PRL:** reported alongside, **never decisive**. It has no band and no "
            "weight, and it cannot rescue an uninterpretable IGFBP-1 or an unconfirmed "
            "reference. PRL/IGFBP-1 disagreement is recorded as a finding."
        ),
        (
            "- **Day 3** is secondary. It cannot override or rescue a day-6 call, and "
            "disagreement between day 3 and day 6 is reported."
        ),
        "",
        (
            f"`{GRADED}` arises only from a valid level-4 intermediate value. Every QC "
            f"indeterminacy ({', '.join(f'`{q}`' for q in QC_INDETERMINATE)}) is "
            f"`{NO_CLASS}` with its reason and never maps to a SEC class (RQ3)."
        ),
        "",
        (
            "**5. What each source-pair block's day-6 pattern supports.** The predictions are frozen "
            "decision table C, and the build checks that each row's classes match it."
        ),
        "",
        (
            "The first four columns are frozen §5, verbatim. The last column is what the "
            "pre-run addendum adds; it rewrites nothing."
        ),
        "",
        "| PAEP (top) | IGFBP-1 (bottom) | Supported | Model action (frozen) | Pre-run addendum |",
        "|---|---|---|---|---|",
    ]
    for row in tree:
        lines.append(
            f"| {row['paep']} | {row['igfbp1']} | {row['supported']} | "
            f"{row['model_action']} | {row['addendum']} |"
        )
    lines += [
        "",
        (
            "The first row is the one to read carefully: **`PAEP OFF + IGFBP-1 ON` establishes "
            "sustained E2 dependence of the epithelial secretory programme, not the "
            "mechanism.** SEC-a (E2 as a direct conjunct) and SEC-e (E2 maintaining "
            "epithelial PGR) cannot be told apart on any usable assay."
        ),
        "",
        (
            "The three source-pair blocks are reported **individually**. Disagreement between "
            "blocks is reported as disagreement and is never averaged into a class call."
        ),
        "",
        "## Pre-run decisions",
        "",
        (
            "Every interpretation gap found before the run has been decided by the owner "
            "(`pre_run_analysis_addendum.tsv`, rounds 1-3, all dated "
            f"{ADDENDUM_DATE}). No pre-run question is open."
        ),
        "",
        "## After the data arrive",
        "",
        (
            "1. Ingest the raw values into a new, declared derived table. Nothing under "
            "`data/` is edited. **No band, rule or threshold is changed.**"
        ),
        (
            "2. Apply the five-step order per source-pair block and record every intermediate call, "
            "including every QC indeterminacy (technical failure, integrity_invalid, "
            "CONTROL_STATE_NOT_CONFIRMED, INDETERMINATE_ZERO, TECHNICAL_DISCORDANCE) and "
            "every graded_not_boolean result, with its reason."
        ),
        (
            "3. Map each valid source-pair-block pattern to the table above. Record "
            "disagreement between blocks, and between day 3 and day 6, explicitly."
        ),
        (
            "4. Re-evaluate the SEC fork and AC01 against those per-block outcomes, in a "
            "new unit."
        ),
        (
            "5. Only then decide whether a new executable model version is licensed. This "
            "handoff does not prescribe which rule the data must produce."
        ),
        "",
        (
            f"Phase-1B status from the companion audit: **{overall}**. This experiment "
            "does not close Phase 1B on its own: it is construction and discrimination "
            "evidence, and it cannot also serve as the held-out validation."
        ),
        "",
    ]
    return "\n".join(lines)


def compute(root: Path) -> dict[str, Any]:
    _check_frozen(root)
    roadmap_sha = check_roadmap(root)
    selection = (root / FROZEN_SELECTION).read_text(encoding="utf-8")
    carried = check_frozen_phrases(selection)
    doses = check_doses(root, selection)
    bands = reference_bands(root)
    check_bands_against_frozen(bands, selection)
    table_c = frozen_table_c(root)
    premises = compute_premises(root)
    check_premises(premises)
    gate = exit_gate_rows(premises)
    overall = derive_overall_status(gate)
    return {
        "carried": carried,
        "doses": doses,
        "bands": bands,
        "table_c": table_c,
        "tree": _tree_rows(selection, table_c),
        "premises": premises,
        "exit_gate": gate,
        "overall": overall,
        "claims": claim_rows(premises),
        "sensitivity": sensitivity_rows(),
        "handoff": handoff_rows(carried, bands),
        "addendum": addendum_rows(selection, bands),
        "lineage": {
            "frozen_stage3_sha256": dict(FROZEN_DIGESTS),
            "models_tree_sha256": _tree_sha(root, Path("models")),
            "roadmap_phase1b_section_sha256": roadmap_sha,
            "inputs_sha256": {
                str(p): _sha(root / p)
                for p in (CALIBRATION, OBSERVATION_MAP, PROTOCOLS, PROTEINS, U8_SUMMARY)
            },
        },
    }


def render_outputs(result: dict[str, Any]) -> dict[Path, str]:
    gate = result["exit_gate"]
    handoff_md = render_handoff_md(
        result["handoff"], result["bands"], result["tree"], result["overall"]
    )
    check_handoff_against_frozen(
        result["handoff"], handoff_md, result["carried"], result["doses"]
    )
    summary = {
        "task": TASK,
        "model_version": ADOPTED_VERSION,
        "phase1b_overall_status": result["overall"],
        "overall_status_rule": OVERALL_RULE,
        "exit_gate": {
            r["criterion_id"]: r["status"] for r in gate if r["kind"] == "exit_gate"
        },
        "roadmap_items": {
            r["criterion_id"]: r["status"] for r in gate if r["kind"] == "roadmap_item"
        },
        "unmet_exit_criteria_without_scheduled_route": [
            r["criterion_id"]
            for r in gate
            if r["kind"] == "exit_gate"
            and r["status"] not in (SATISFIED, NOT_APPLICABLE)
            and r["unblock_route"] == NO_SCHEDULED_ROUTE
        ],
        "mifepristone": {
            "direction": "NOT_APPLICABLE: constructed from SOFIA-HT-002 (LE002, LE038); not held out",
            "magnitude": result["premises"]["adhesion_arms"][
                "hormone_treated_mifepristone"
            ],
            "validation_claim": "none: structurally_contradicted and quantitatively_unscorable_for_ranking; cannot identify or justify a maternal-rule change",
        },
        "premises": result["premises"],
        "reference_bands": result["bands"],
        "frozen_boundaries": boundaries(result["bands"]),
        "operational_prerequisites": {
            "allocation_manifest": str(OUT_ALLOCATION),
            "assay_metadata": str(OUT_ASSAY_METADATA),
            "treatment_may_start": validate_manifest(allocation_template())[
                "treatment_may_start"
            ],
            "classification_ready": False,
        },
        "frozen_table_c": {k: list(v) for k, v in sorted(result["table_c"].items())},
        "addendum": {
            "record_type": ADDENDUM_TYPE,
            "decided_on": ADDENDUM_DATE,
            "gaps": [r["gap_id"] for r in result["addendum"]],
            "precedence": list(PRECEDENCE),
        },
        "residual_pre_run_questions": sorted(
            rq for rq, _ in residual_questions(result["bands"])
        ),
        "lineage": result["lineage"],
    }
    return {
        OUT_EXIT_GATE: _tsv(EXIT_GATE_COLUMNS, gate),
        OUT_CLAIMS: _tsv(CLAIM_COLUMNS, result["claims"]),
        OUT_SENSITIVITY: _tsv(SENSITIVITY_COLUMNS, result["sensitivity"]),
        OUT_HANDOFF_TSV: _tsv(HANDOFF_COLUMNS, result["handoff"]),
        OUT_ADDENDUM: _tsv(ADDENDUM_COLUMNS, result["addendum"]),
        OUT_HANDOFF_MD: handoff_md,
        OUT_SUMMARY: json.dumps(summary, indent=2, sort_keys=True) + "\n",
        OUT_ALLOCATION: _tsv(ALLOCATION_COLUMNS, allocation_template()),
        OUT_ASSAY_METADATA: _tsv(ASSAY_METADATA_COLUMNS, assay_metadata_template()),
    }


def build(root: Path | None = None) -> tuple[Path, ...]:
    active = root or repo_root()
    outputs = render_outputs(compute(active))
    assert tuple(outputs) == OUTPUTS
    (active / OUT_DIR).mkdir(parents=True, exist_ok=True)
    for relative, text in outputs.items():
        (active / relative).write_text(text, encoding="utf-8")
    return tuple(active / p for p in OUTPUTS)


if __name__ == "__main__":  # pragma: no cover
    for written in build():
        print(f"wrote {written}")
