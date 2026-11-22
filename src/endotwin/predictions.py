"""Prediction freezing and prospective evaluation (WP2, WP4).

``freeze`` writes an immutable record before any evaluation data exist: the spec,
a byte copy of the model, protocols, interventions and observation map, the
exact and stochastic predictions, their sensitivity to the other rule variants
and to transition rates, and provenance (repository commit, engine version, UTC
time). Every file is listed with its SHA-256 in ``MANIFEST.sha256``, whose own
digest identifies the record.

``evaluate`` refuses to run unless the record is intact, the evaluation donors
are disjoint from the development donors named in the spec, and (for WP4) the
intervention-selection record was built without G3 data. It writes a separate
evaluation file and never modifies the frozen record.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path

import yaml

from endotwin.analysis import (
    comparison_directions,
    exact_predictions,
    initial_condition_sensitivity,
    rate_sensitivity,
    readout_nodes,
)
from endotwin.model import Model, load_model, scenario_label
from endotwin.observations import (
    AgreementCriteria,
    classify,
    donor_effect,
    load_observation_map,
)
from endotwin.paths import CONFIG, PREDICTIONS, ROOT
from endotwin.protocols import load_protocols
from endotwin.simulate import SimulationSettings, engine_report, replicate

MANIFEST = "MANIFEST.sha256"
PURPOSES = {
    "WP2_prospective_G1",
    "WP4_selection_G2",
    "WP4_evaluation_G2",
    "WP4_evaluation_G3",
}


class FreezeError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_state(root: Path = ROOT) -> dict[str, object]:
    def run(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=root, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""

    commit = run("rev-parse", "HEAD")
    dirty = bool(run("status", "--porcelain", "--untracked-files=no"))
    return {"commit": commit or "uncommitted", "dirty": dirty}


def load_spec(path: Path) -> dict[str, object]:
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = {
        "prediction_id",
        "purpose",
        "model_version",
        "comparison",
        "primary_readout",
        "agreement_criteria",
        "simulation",
        "sensitivity",
        "donor_policy",
    }
    missing = sorted(required - set(spec))
    if missing:
        raise FreezeError(f"spec is missing {missing}")
    if spec["purpose"] not in PURPOSES:
        raise FreezeError(f"purpose must be one of {sorted(PURPOSES)}")
    AgreementCriteria.from_mapping(spec["agreement_criteria"])
    if spec["purpose"] == "WP4_selection_G2":
        groups = set(spec.get("selection_dataset_groups") or [])
        if not groups or "G3" in groups:
            raise FreezeError(
                "a WP4 selection record must name its selection data groups and must "
                "not include G3"
            )
    if spec["purpose"] == "WP4_evaluation_G3" and not spec.get("selection_record"):
        raise FreezeError(
            "a G3 evaluation must reference the frozen WP4 selection record"
        )
    return spec


def _manifest(directory: Path) -> str:
    lines = []
    for path in sorted(
        p for p in directory.rglob("*") if p.is_file() and p.name != MANIFEST
    ):
        lines.append(f"{_sha256(path)}  {path.relative_to(directory).as_posix()}")
    return "\n".join(lines) + "\n"


def record_digest(directory: Path) -> str:
    return _sha256(directory / MANIFEST)


def freeze(
    spec_path: Path,
    *,
    out_root: Path = PREDICTIONS / "frozen",
    allow_dirty: bool = False,
    model: Model | None = None,
    check_only: bool = False,
) -> Path:
    spec = load_spec(spec_path)
    donors = (spec.get("donor_policy") or {}).get("development_donors") or []
    if spec["purpose"] == "WP2_prospective_G1" and not donors and not check_only:
        raise FreezeError(
            "a WP2 record must list every WP1 development donor (pseudonymised) so "
            "that evaluation can refuse them; use the check mode until they are known"
        )
    model = model or load_model(spec["model_version"])
    if model.version != spec["model_version"]:
        raise FreezeError("model version does not match the spec")
    git = git_state()
    if git["dirty"] and not allow_dirty:
        raise FreezeError(
            "refusing to freeze from a working tree with uncommitted changes"
        )
    target = out_root / spec["prediction_id"]
    if target.exists():
        raise FreezeError(
            f"{target} already exists; frozen records are never overwritten"
        )

    protocols = load_protocols(model)
    observations = load_observation_map(model)
    comp_id = spec["comparison"]
    if comp_id not in protocols.comparisons:
        raise FreezeError(f"unknown comparison {comp_id}")
    comparison = protocols.comparisons[comp_id]
    readouts = [spec["primary_readout"], *spec.get("secondary_readouts", [])]
    for readout in readouts:
        if readout not in observations or not observations[readout]["model_node"]:
            raise FreezeError(f"{readout} is not a mapped readout")
    selection = model.resolve_selection(spec.get("rule_variants") or {})
    label = scenario_label(selection)

    exact_rows = exact_predictions(model, protocols)
    directions = comparison_directions(model, protocols, exact_rows)
    predicted: dict[str, object] = {}
    rule_sensitivity: dict[str, dict[str, str]] = {}
    for readout in readouts:
        node = observations[readout]["model_node"]
        mine = [
            d
            for d in directions
            if d["comparison"] == comp_id and d["readout_node"] == node
        ]
        chosen = next(d for d in mine if d["scenario"] == label)
        predicted[readout] = {"model_node": node, "direction": chosen["direction"]}
        rule_sensitivity[readout] = {d["scenario"]: d["direction"] for d in mine}

    sim = spec["simulation"]
    settings = SimulationSettings(
        sample_count=int(sim["sample_count"]), seed=int(sim["seed"])
    )
    stochastic: dict[str, dict[str, float]] = {}
    for role, cid, phase_id in (
        ("perturbed", comparison.perturbed, comparison.phase_perturbed),
        ("control", comparison.control, comparison.phase),
    ):
        runs = replicate(
            model,
            protocols.conditions[cid],
            protocols.interventions,
            replicates=int(sim["replicates"]),
            selection=selection,
            base=settings,
        )
        values = {n: [r.final(phase_id)[n] for r in runs] for n in readout_nodes(model)}
        stochastic[role] = {n: round(sum(v) / len(v), 6) for n, v in values.items()}

    sens = spec["sensitivity"]
    primary_node = predicted[spec["primary_readout"]]["model_node"]
    primary_dir = predicted[spec["primary_readout"]]["direction"]
    families_to_vary = set(sens.get("vary_rule_families") or [])
    stable_rules = all(
        direction == primary_dir
        for scenario, direction in rule_sensitivity[spec["primary_readout"]].items()
        if all(
            selection[f] in scenario.split("+")
            for f in selection
            if f not in families_to_vary
        )
    )
    rate_rows, rate_summary = rate_sensitivity(
        model,
        protocols,
        directions,
        samples=int(sens.get("rate_samples", 10)),
        sample_count=int(sens.get("rate_sample_count", 1000)),
        seed=int(sens.get("rate_seed", 7)),
    )
    primary_rate = [
        r
        for r in rate_rows
        if r["comparison"] == comp_id and r["readout_node"] == primary_node
    ]
    stable_rates = all(r["agrees"] for r in primary_rate if r["both_converged"])
    init_rows, init_summary = initial_condition_sensitivity(
        model,
        protocols,
        comp_id,
        selection,
        primary_node,
        primary_dir,
        samples=int(sens.get("initial_condition_samples", 5)),
        sample_count=int(sens.get("rate_sample_count", 1000)),
        seed=int(sens.get("initial_condition_seed", 11)),
    )
    stable_initial = bool(init_summary["stable"])
    eligible = stable_rules and stable_rates and stable_initial
    if sens.get("require_stable", True) and not eligible:
        raise FreezeError(
            "primary prediction is not stable under the declared sensitivity analysis "
            f"(rules stable: {stable_rules}, rates stable: {stable_rates}, "
            f"initial conditions stable: {stable_initial}); not eligible"
        )

    staging = target.with_name(target.name + ".partial")
    if staging.exists():
        shutil.rmtree(staging)
    (staging / "model").mkdir(parents=True)
    (staging / "config").mkdir()
    shutil.copy2(spec_path, staging / "spec.yaml")
    for path in sorted(model.root.iterdir()):
        if path.is_file():
            shutil.copy2(path, staging / "model" / path.name)
    for name in ("protocols.yaml", "interventions.tsv", "observation_map.tsv"):
        shutil.copy2(CONFIG / name, staging / "config" / name)
    payload = {
        "prediction_id": spec["prediction_id"],
        "purpose": spec["purpose"],
        "model_version": model.version,
        "rule_variants": selection,
        "comparison": {
            "id": comp_id,
            "perturbed": comparison.perturbed,
            "control": comparison.control,
            "phase_control": comparison.phase,
            "phase_perturbed": comparison.phase_perturbed,
        },
        "predictions": predicted,
        "primary_readout": spec["primary_readout"],
        "stochastic_end_of_phase_means": stochastic,
        "sensitivity": {
            "rule_variant_directions": rule_sensitivity,
            "varied_rule_families": sorted(families_to_vary),
            "stable_under_rule_variants": stable_rules,
            "rate_summary": rate_summary,
            "stable_under_rates": stable_rates,
            "initial_condition_summary": init_summary,
            "initial_condition_samples": init_rows,
            "stable_under_initial_conditions": stable_initial,
            "eligible": eligible,
        },
        "agreement_criteria": spec["agreement_criteria"],
        "semantics": (
            "Directions of fixed-point node states between matched conditions. "
            "MaBoSS probabilities are not concentrations; MaBoSS time is not "
            "experimental time."
        ),
    }
    (staging / "predictions.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    provenance = {
        "frozen_at_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "repository": git,
        "engine": engine_report(),
        "python": platform.python_version(),
    }
    (staging / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    )
    (staging / MANIFEST).write_text(_manifest(staging))
    staging.rename(target)
    return target


def verify(record: Path) -> dict[str, object]:
    manifest = record / MANIFEST
    if not manifest.is_file():
        return {"intact": False, "problems": ["missing manifest"]}
    problems = []
    listed = set()
    for line in manifest.read_text().splitlines():
        digest, name = line.split("  ", 1)
        listed.add(name)
        path = record / name
        if not path.is_file():
            problems.append(f"missing: {name}")
        elif _sha256(path) != digest:
            problems.append(f"modified: {name}")
    for path in record.rglob("*"):
        if (
            path.is_file()
            and path.name != MANIFEST
            and not path.name.startswith("evaluation")
            and path.relative_to(record).as_posix() not in listed
        ):
            problems.append(f"unlisted: {path.relative_to(record).as_posix()}")
    return {
        "intact": not problems,
        "problems": problems,
        "record_sha256": record_digest(record),
    }


def _read_observations(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def evaluate(
    record: Path, observations_path: Path, *, out_name: str = "evaluation.json"
) -> Path:
    """Classify each frozen prediction against donor-level observations.

    The observation table has one row per donor and readout with columns
    ``donor_id, group, readout_id, perturbed_value, control_value, evaluable``.
    Non-evaluable rows (failed viability, integrity or target engagement) are
    excluded by the pre-declared quality gate, independently of the prediction.
    """
    check = verify(record)
    if not check["intact"]:
        raise FreezeError(f"frozen record is not intact: {check['problems']}")
    out = record / out_name
    if out.exists():
        raise FreezeError(f"{out} exists; an evaluation is written once")
    spec = yaml.safe_load((record / "spec.yaml").read_text())
    payload = json.loads((record / "predictions.json").read_text())
    rows = _read_observations(observations_path)
    policy = spec["donor_policy"]
    excluded = set(policy.get("development_donors") or [])
    used = {r["donor_id"] for r in rows}
    overlap = sorted(used & excluded)
    if overlap:
        raise FreezeError(f"evaluation donors overlap development donors: {overlap}")
    allowed_groups = set(policy.get("evaluation_groups") or [])
    bad_groups = (
        sorted({r["group"] for r in rows} - allowed_groups) if allowed_groups else []
    )
    if bad_groups:
        raise FreezeError(
            f"observations from groups not declared for evaluation: {bad_groups}"
        )
    if spec["purpose"] == "WP4_evaluation_G3":
        selection_record = (record.parent / spec["selection_record"]).resolve()
        sel_check = verify(selection_record)
        if not sel_check["intact"]:
            raise FreezeError("the referenced WP4 selection record is not intact")
        sel_spec = yaml.safe_load((selection_record / "spec.yaml").read_text())
        if "G3" in set(sel_spec.get("selection_dataset_groups") or []):
            raise FreezeError("the intervention was selected using G3 data")

    criteria = AgreementCriteria.from_mapping(payload["agreement_criteria"])
    results = {}
    for readout, prediction in payload["predictions"].items():
        effects = []
        for row in rows:
            if row["readout_id"] != readout or row["evaluable"].lower() != "true":
                continue
            effects.append(
                donor_effect(float(row["perturbed_value"]), float(row["control_value"]))
            )
        verdict, reason = classify(prediction["direction"], effects, criteria)
        results[readout] = {
            "predicted_direction": prediction["direction"],
            "evaluable_donors": len(effects),
            "donor_log2_effects": [round(e, 6) for e in effects],
            "verdict": verdict,
            "reason": reason,
        }
    evaluation = {
        "frozen_record_sha256": check["record_sha256"],
        "observations_sha256": _sha256(observations_path),
        "evaluated_at_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "primary_readout": payload["primary_readout"],
        "results": results,
        "note": (
            "The frozen record is not modified by evaluation. Discrepancies are "
            "reported, never used to revise the frozen prediction."
        ),
    }
    out.write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n")
    return out
