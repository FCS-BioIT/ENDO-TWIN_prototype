"""Run-manifest helpers matching the repository validator contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from dt_adoc.model.provenance import describe_file, repo_root


@dataclass(frozen=True)
class SimulationSettings:
    seeds: list[int]
    trajectory_count: int
    max_time: float
    time_tick: float
    thread_count: int
    perturbation: str


def _now_iso8601() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_run_manifest(
    *,
    run_id: str,
    command: str,
    baseline_bnd: str | Path,
    baseline_cfg: str | Path,
    source_manifest: str | Path,
    mapping: str | Path,
    outputs: list[dict[str, Any]],
    phenotypes: dict[str, str],
    included_units: list[str],
    exclusions: list[dict[str, Any]],
    leakage_controls: str,
    software: dict[str, str],
    protocols: list[str],
    simulation: SimulationSettings,
    simulation_extras: dict[str, Any] | None = None,
    validation_levels: list[str],
    patient_cfg: str | Path | None = None,
    warnings: list[str] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    active_root = root or repo_root()
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": run_id,
        "created_at": _now_iso8601(),
        "command": command,
        "software": dict(software),
        "protocols": list(protocols),
        "model": {
            "baseline_bnd": describe_file(baseline_bnd, root=active_root).__dict__,
            "baseline_cfg": describe_file(baseline_cfg, root=active_root).__dict__,
        },
        "data": {
            "source_manifest": describe_file(
                source_manifest, root=active_root
            ).__dict__,
        },
        "cohort": {
            "independent_unit": "published phase-1 assay observation",
            "included_units": included_units,
            "exclusions": exclusions,
        },
        "personalization": {
            "mapping": describe_file(mapping, root=active_root).__dict__,
            "leakage_controls": leakage_controls,
        },
        "simulation": {
            "seeds": simulation.seeds,
            "trajectory_count": simulation.trajectory_count,
            "max_time": simulation.max_time,
            "time_tick": simulation.time_tick,
            "thread_count": simulation.thread_count,
            "perturbation": simulation.perturbation,
            **(simulation_extras or {}),
        },
        "phenotypes": phenotypes,
        "outputs": outputs,
        "validation": {
            "completed_levels": validation_levels,
        },
        "warnings": warnings or [],
    }
    if patient_cfg is not None:
        payload["model"]["patient_cfg"] = describe_file(
            patient_cfg, root=active_root
        ).__dict__
    return payload


def write_run_manifest(
    path: str | Path, payload: dict[str, Any], *, root: Path | None = None
) -> Path:
    active_root = root or repo_root()
    target = Path(path)
    if not target.is_absolute():
        target = active_root / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target
