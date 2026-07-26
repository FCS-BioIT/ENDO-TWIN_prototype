#!/usr/bin/env python3
"""Validate a DT_ADOC MaBoSS run manifest and referenced artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "run_id",
    "created_at",
    "software",
    "model",
    "data",
    "cohort",
    "personalization",
    "simulation",
    "phenotypes",
    "outputs",
    "validation",
    "warnings",
}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_files: list[str] = field(default_factory=list)

    def payload(self) -> dict[str, object]:
        return {
            "status": "valid" if not self.errors else "invalid",
            "errors": self.errors,
            "warnings": self.warnings,
            "checked_files": self.checked_files,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(root: Path, raw_path: str) -> Path:
    relative = Path(raw_path)
    if relative.is_absolute() or any(part == ".." for part in relative.parts):
        raise ValueError("path must be repository-relative and cannot contain '..'")
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("path escapes repository root") from exc
    return target


def validate_file_ref(
    label: str,
    value: Any,
    root: Path,
    report: Report,
    check_hashes: bool,
) -> None:
    if not isinstance(value, dict):
        report.errors.append(f"{label} must be an object")
        return
    raw_path = value.get("path")
    expected_hash = str(value.get("sha256", "")).lower()
    if not isinstance(raw_path, str) or not raw_path:
        report.errors.append(f"{label}.path must be a non-empty string")
        return
    try:
        path = resolve_path(root, raw_path)
    except ValueError as exc:
        report.errors.append(f"{label}.path: {exc}")
        return
    if not path.is_file():
        report.errors.append(f"{label}: missing file {raw_path}")
        return
    if path.stat().st_size == 0:
        report.errors.append(f"{label}: empty file {raw_path}")
    report.checked_files.append(raw_path)

    if not SHA256_RE.fullmatch(expected_hash):
        report.errors.append(f"{label}.sha256 must be 64 lowercase hex characters")
    elif check_hashes:
        observed = sha256_file(path)
        if observed != expected_hash:
            report.errors.append(
                f"{label}: SHA-256 mismatch for {raw_path}: "
                f"expected {expected_hash}, observed {observed}"
            )
    expected_size = value.get("size_bytes")
    if expected_size is not None:
        if not isinstance(expected_size, int) or expected_size < 0:
            report.errors.append(f"{label}.size_bytes must be a non-negative integer")
        elif path.stat().st_size != expected_size:
            report.errors.append(
                f"{label}: size mismatch for {raw_path}: "
                f"expected {expected_size}, observed {path.stat().st_size}"
            )


def positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def validate_manifest(
    payload: Any, root: Path, *, check_hashes: bool = True
) -> Report:
    report = Report()
    if not isinstance(payload, dict):
        report.errors.append("manifest root must be a JSON object")
        return report

    missing = REQUIRED_TOP_LEVEL - set(payload)
    if missing:
        report.errors.append(
            f"manifest missing keys: {', '.join(sorted(missing))}"
        )
        return report

    for key in ("schema_version", "run_id", "created_at"):
        if not isinstance(payload[key], str) or not payload[key].strip():
            report.errors.append(f"{key} must be a non-empty string")

    software = payload["software"]
    if not isinstance(software, dict) or not software:
        report.errors.append("software must be a non-empty object")

    model = payload["model"]
    if not isinstance(model, dict):
        report.errors.append("model must be an object")
    else:
        for key in ("baseline_bnd", "baseline_cfg"):
            if key not in model:
                report.errors.append(f"model missing {key}")
            else:
                validate_file_ref(
                    f"model.{key}", model[key], root, report, check_hashes
                )
        if "patient_cfg" in model:
            validate_file_ref(
                "model.patient_cfg", model["patient_cfg"], root, report, check_hashes
            )

    data = payload["data"]
    if not isinstance(data, dict) or "source_manifest" not in data:
        report.errors.append("data.source_manifest is required")
    else:
        validate_file_ref(
            "data.source_manifest",
            data["source_manifest"],
            root,
            report,
            check_hashes,
        )

    cohort = payload["cohort"]
    if not isinstance(cohort, dict):
        report.errors.append("cohort must be an object")
    else:
        if not isinstance(cohort.get("independent_unit"), str):
            report.errors.append("cohort.independent_unit must be a string")
        if not isinstance(cohort.get("included_units"), list):
            report.errors.append("cohort.included_units must be a list")
        if not isinstance(cohort.get("exclusions"), list):
            report.errors.append("cohort.exclusions must be a list")

    personalization = payload["personalization"]
    if not isinstance(personalization, dict):
        report.errors.append("personalization must be an object")
    else:
        if "mapping" not in personalization:
            report.errors.append("personalization.mapping is required")
        else:
            validate_file_ref(
                "personalization.mapping",
                personalization["mapping"],
                root,
                report,
                check_hashes,
            )
        if not isinstance(personalization.get("leakage_controls"), str):
            report.errors.append(
                "personalization.leakage_controls must be a string"
            )

    simulation = payload["simulation"]
    if not isinstance(simulation, dict):
        report.errors.append("simulation must be an object")
    else:
        seeds = simulation.get("seeds")
        if (
            not isinstance(seeds, list)
            or not seeds
            or any(not isinstance(seed, int) for seed in seeds)
        ):
            report.errors.append("simulation.seeds must be a non-empty integer list")
        for key in ("trajectory_count", "max_time", "time_tick"):
            if not positive_number(simulation.get(key)):
                report.errors.append(f"simulation.{key} must be positive")

    phenotypes = payload["phenotypes"]
    if not isinstance(phenotypes, (list, dict)) or not phenotypes:
        report.errors.append("phenotypes must be a non-empty list or object")

    outputs = payload["outputs"]
    if not isinstance(outputs, list) or not outputs:
        report.errors.append("outputs must be a non-empty list")
    else:
        for index, output in enumerate(outputs):
            validate_file_ref(
                f"outputs[{index}]", output, root, report, check_hashes
            )
            if isinstance(output, dict) and not isinstance(output.get("kind"), str):
                report.errors.append(f"outputs[{index}].kind must be a string")

    validation = payload["validation"]
    if not isinstance(validation, dict):
        report.errors.append("validation must be an object")
    elif not isinstance(validation.get("completed_levels"), list):
        report.errors.append("validation.completed_levels must be a list")

    if not isinstance(payload["warnings"], list):
        report.errors.append("warnings must be a list")

    if not check_hashes:
        report.warnings.append("referenced file hashes were not recomputed")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--skip-hashes", action="store_true")
    parser.add_argument("--json-report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: unreadable repository root: {root}")
        return 2
    manifest = args.manifest
    if not manifest.is_absolute():
        manifest = root / manifest
    try:
        payload = json.loads(manifest.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read JSON manifest: {exc}")
        return 2
    report = validate_manifest(payload, root, check_hashes=not args.skip_hashes)
    output = report.payload()
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    return 0 if not report.errors else 1


if __name__ == "__main__":
    sys.exit(main())
