#!/usr/bin/env python3
"""Validate the DT_ADOC immutable-source manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_COLUMNS = {
    "relative_path",
    "size_bytes",
    "sha256",
    "role",
    "inspection_state",
}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "valid" if not self.errors else "invalid"

    def payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "checked": self.checked,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_repo_path(root: Path, raw_path: str) -> Path:
    relative = Path(raw_path)
    if relative.is_absolute() or any(part == ".." for part in relative.parts):
        raise ValueError("path must be repository-relative and cannot contain '..'")
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("path escapes repository root") from exc
    return target


def validate_manifest(root: Path, manifest: Path, check_hashes: bool) -> Report:
    report = Report()
    try:
        with manifest.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            columns = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - columns
            if missing:
                report.errors.append(
                    f"manifest missing columns: {', '.join(sorted(missing))}"
                )
                return report
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        report.errors.append(f"cannot read manifest: {exc}")
        return report

    if not rows:
        report.errors.append("manifest contains no source rows")
        return report

    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        raw_path = (row.get("relative_path") or "").strip()
        if not raw_path:
            report.errors.append(f"row {index}: empty relative_path")
            continue
        if raw_path in seen:
            report.errors.append(f"row {index}: duplicate path {raw_path!r}")
            continue
        seen.add(raw_path)
        try:
            path = safe_repo_path(root, raw_path)
        except ValueError as exc:
            report.errors.append(f"row {index}: {raw_path!r}: {exc}")
            continue
        if not path.is_file():
            report.errors.append(f"row {index}: missing source file {raw_path}")
            continue
        report.checked.append(raw_path)

        try:
            expected_size = int(row.get("size_bytes") or "")
        except ValueError:
            report.errors.append(f"row {index}: invalid size_bytes")
        else:
            observed_size = path.stat().st_size
            if expected_size != observed_size:
                report.errors.append(
                    f"row {index}: size mismatch for {raw_path}: "
                    f"expected {expected_size}, observed {observed_size}"
                )

        expected_hash = (row.get("sha256") or "").strip().lower()
        if not SHA256_RE.fullmatch(expected_hash):
            report.errors.append(f"row {index}: invalid SHA-256 for {raw_path}")
        elif check_hashes:
            observed_hash = sha256_file(path)
            if expected_hash != observed_hash:
                report.errors.append(
                    f"row {index}: SHA-256 mismatch for {raw_path}: "
                    f"expected {expected_hash}, observed {observed_hash}"
                )

        if not (row.get("role") or "").strip():
            report.errors.append(f"row {index}: empty role for {raw_path}")
        if not (row.get("inspection_state") or "").strip():
            report.errors.append(
                f"row {index}: empty inspection_state for {raw_path}"
            )

    if not check_hashes:
        report.warnings.append("content hashes were not recomputed")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("config/data_manifest.tsv"),
        help="Repository-relative manifest path unless absolute.",
    )
    parser.add_argument("--check-hashes", action="store_true")
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
    report = validate_manifest(root, manifest, args.check_hashes)
    payload = report.payload()
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 0 if report.status == "valid" else 1


if __name__ == "__main__":
    sys.exit(main())
