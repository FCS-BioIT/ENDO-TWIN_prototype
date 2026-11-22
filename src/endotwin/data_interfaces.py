"""Interfaces for the experimental data ENDO-TWIN will generate.

No ENDO-TWIN data exist yet. These validators define what the planned tables
must look like and enforce the scientific contract before any analysis reads
them:

* measurement states (observed, below detection, missing, excluded) stay
  distinct and consistent with the value column;
* donor identifiers are pseudonymised codes;
* donors used for WP2 prospective evaluation never appear in model development,
  and G3 data never enter WP4 intervention selection;
* deconvolution output is a relative transcriptional-state contribution, never
  an absolute cell fraction.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from endotwin.paths import CONFIG

SCHEMAS = CONFIG / "data_schemas"
PSEUDONYM = re.compile(r"^[A-Z0-9][A-Z0-9_-]{1,31}$")
DEVELOPMENT_ROLES = {"development", "wp3_characterisation", "wp4_selection"}


@dataclass
class ValidationReport:
    table: str
    rows: int
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_schema(name: str) -> dict[str, object]:
    return yaml.safe_load((SCHEMAS / f"{name}.yaml").read_text(encoding="utf-8"))


def read_table(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _check_value(
    column: str, spec: Mapping[str, object], raw: str, readouts: set[str]
) -> str | None:
    if raw == "":
        return f"{column} is required" if spec.get("required") else None
    kind = spec["type"]
    if kind == "float":
        try:
            value = float(raw)
        except ValueError:
            return f"{column}={raw!r} is not a number"
        if "min" in spec and value < float(spec["min"]):
            return f"{column}={value} below {spec['min']}"
        if "max" in spec and value > float(spec["max"]):
            return f"{column}={value} above {spec['max']}"
    elif kind == "bool":
        if raw.lower() not in {"true", "false"}:
            return f"{column}={raw!r} is not true/false"
    elif kind == "pseudonymised_id":
        if not PSEUDONYM.match(raw):
            return f"{column}={raw!r} is not a pseudonymised code (A-Z, 0-9, _ or -)"
    elif kind == "readout":
        if raw not in readouts:
            return f"{column}={raw!r} is not a readout in observation_map.tsv"
    allowed = spec.get("allowed")
    if allowed and raw not in {str(a) for a in allowed}:
        return f"{column}={raw!r} not in {allowed}"
    return None


def validate(
    name: str, rows: list[dict[str, str]], readouts: Iterable[str] = ()
) -> ValidationReport:
    schema = load_schema(name)
    columns: Mapping[str, Mapping[str, object]] = schema["columns"]
    report = ValidationReport(table=name, rows=len(rows))
    readout_set = set(readouts)
    if rows:
        missing = sorted(set(columns) - set(rows[0]))
        if missing:
            report.errors.append(f"missing columns: {missing}")
            return report
    seen: set[tuple[str, ...]] = set()
    for i, row in enumerate(rows, start=2):
        for column, spec in columns.items():
            problem = _check_value(column, spec, row.get(column, ""), readout_set)
            if problem:
                report.errors.append(f"line {i}: {problem}")
        key = tuple(row.get(c, "") for c in schema.get("unique", []))
        if key in seen:
            report.errors.append(f"line {i}: duplicate key {key}")
        seen.add(key)
    if name == "functional_measurements":
        report.errors.extend(_measurement_states(rows))
    if name == "deconvolution_estimates":
        report.errors.extend(_deconvolution_sums(rows))
    report.errors.extend(role_partition_errors(rows))
    return report


def _measurement_states(rows: list[dict[str, str]]) -> list[str]:
    errors = []
    for i, row in enumerate(rows, start=2):
        state, value, lod = row["measurement_state"], row["value"], row.get("lod", "")
        if state == "observed" and value == "":
            errors.append(f"line {i}: observed measurement has no value")
        if state in {"missing", "excluded"} and value != "":
            errors.append(f"line {i}: {state} measurement must have an empty value")
        if state == "below_lod":
            if lod == "":
                errors.append(f"line {i}: below_lod requires the assay lod")
            elif value != "" and float(value) >= float(lod):
                errors.append(f"line {i}: below_lod value is not below the lod")
        if (
            state == "observed"
            and lod != ""
            and value != ""
            and float(value) < float(lod)
        ):
            errors.append(
                f"line {i}: observed value below the lod must be state below_lod"
            )
    return errors


def _deconvolution_sums(
    rows: list[dict[str, str]], tolerance: float = 1e-6
) -> list[str]:
    totals: dict[str, float] = {}
    for row in rows:
        if row["estimate"]:
            totals[row["library_id"]] = totals.get(row["library_id"], 0.0) + float(
                row["estimate"]
            )
    return [
        f"library {lib}: relative contributions sum to {total:.4f} > 1"
        for lib, total in sorted(totals.items())
        if total > 1 + tolerance
    ]


def role_partition_errors(rows: list[dict[str, str]]) -> list[str]:
    """Leakage guards between model development and prospective evaluation."""
    if not rows or "analysis_role" not in rows[0] or "donor_id" not in rows[0]:
        return []
    errors = []
    roles_by_donor: dict[str, set[str]] = {}
    for row in rows:
        roles_by_donor.setdefault(row["donor_id"], set()).add(row["analysis_role"])
        if row["analysis_role"] == "wp4_selection" and row.get("group") == "G3":
            errors.append(
                f"donor {row['donor_id']}: G3 data cannot be used for WP4 intervention selection"
            )
        if row["analysis_role"] == "wp2_evaluation" and row.get("group") not in (
            None,
            "G1",
        ):
            errors.append(
                f"donor {row['donor_id']}: WP2 evaluation uses G1 donors only"
            )
    for donor, roles in sorted(roles_by_donor.items()):
        if "wp2_evaluation" in roles and roles & DEVELOPMENT_ROLES:
            errors.append(
                f"donor {donor}: used both for WP2 prospective evaluation and for "
                f"development ({sorted(roles & DEVELOPMENT_ROLES)})"
            )
    return errors
