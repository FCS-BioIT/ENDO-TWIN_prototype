#!/usr/bin/env python3
"""Validate a DT_ADOC ChatGPT archive after a fresh extraction."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath


ROOT_NAME = "DT_ADOC_chatgpt_bundle"
MANIFEST_NAME = "CHATGPT_BUNDLE_MANIFEST.tsv"
REQUIRED_FILES = {
    "README.md",
    "CHATGPT_BUNDLE_README.md",
    "CHATGPT_BUNDLE_MANIFEST.tsv",
    "SECTION_STATUS.tsv",
}
FORBIDDEN_PARTS = {
    ".git",
    ".pixi",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    "cache",
    "checkpoints",
    "tmp",
}
FORBIDDEN_SUFFIXES = {
    ".rds",
    ".rdata",
    ".rda",
    ".h5ad",
    ".h5",
    ".loom",
    ".pkl",
    ".pickle",
    ".pdf",
    ".docx",
    ".xlsx",
    ".xls",
    ".zip",
    ".tgz",
}
MANIFEST_COLUMNS = {"path", "size_bytes", "sha256", "inclusion_reason"}
PROTEIN_WORKBOOK_PATH = (
    "input_tables/protein_readouts/proteinas secretadas ADOC.xlsx"
)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_files: int = 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative_path(value: str) -> PurePosixPath | None:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        return None
    return path


def forbidden_path(path: PurePosixPath) -> bool:
    if str(path) == PROTEIN_WORKBOOK_PATH:
        return False
    lower_parts = {part.lower() for part in path.parts}
    if lower_parts & FORBIDDEN_PARTS:
        return True
    lower_name = path.name.lower()
    if lower_name.endswith((".tar.gz", ".tsv.gz", ".csv.gz", ".json.gz", ".txt.gz")):
        return lower_name.endswith(".tar.gz")
    return path.suffix.lower() in FORBIDDEN_SUFFIXES


def validate_archive(archive: Path) -> Report:
    report = Report()
    if not archive.is_file():
        report.errors.append(f"archive does not exist: {archive}")
        return report
    if archive.stat().st_size > 60 * 1024 * 1024:
        report.errors.append("archive exceeds 60 MiB")

    try:
        handle = tarfile.open(archive, "r:gz")
    except (OSError, tarfile.TarError) as exc:
        report.errors.append(f"cannot open archive: {exc}")
        return report

    with handle:
        members = handle.getmembers()
        regular_paths: set[str] = set()
        for member in members:
            member_path = safe_relative_path(member.name)
            if member_path is None:
                report.errors.append(f"unsafe archive member path: {member.name!r}")
                continue
            if not member_path.parts or member_path.parts[0] != ROOT_NAME:
                report.errors.append(f"member is outside {ROOT_NAME}/: {member.name}")
            if member.issym() or member.islnk():
                report.errors.append(f"links are not allowed in archive: {member.name}")
            if member.isfile():
                relative = PurePosixPath(*member_path.parts[1:])
                if forbidden_path(relative):
                    report.errors.append(f"forbidden file in archive: {relative}")
                if relative.parts and relative.parts[0] == "data":
                    report.errors.append(f"source data must not be bundled: {relative}")
                regular_paths.add(str(relative))
        if report.errors:
            return report

        with tempfile.TemporaryDirectory() as tmp:
            extraction_root = Path(tmp)
            handle.extractall(extraction_root, filter="data")
            root = extraction_root / ROOT_NAME
            missing_required = sorted(REQUIRED_FILES - regular_paths)
            for missing in missing_required:
                report.errors.append(f"required bundle file missing: {missing}")
            manifest_path = root / MANIFEST_NAME
            if not manifest_path.is_file():
                return report

            with manifest_path.open(newline="", encoding="utf-8") as stream:
                reader = csv.DictReader(stream, delimiter="\t")
                if set(reader.fieldnames or ()) != MANIFEST_COLUMNS:
                    report.errors.append(
                        f"manifest columns are {reader.fieldnames!r}, expected {sorted(MANIFEST_COLUMNS)!r}"
                    )
                    return report
                rows = list(reader)

            seen: set[str] = set()
            for row in rows:
                value = row["path"]
                relative = safe_relative_path(value)
                if relative is None:
                    report.errors.append(f"unsafe manifest path: {value!r}")
                    continue
                if value in seen:
                    report.errors.append(f"duplicate manifest path: {value}")
                    continue
                seen.add(value)
                target = root.joinpath(*relative.parts)
                if not target.is_file():
                    report.errors.append(f"manifest target missing: {value}")
                    continue
                try:
                    expected_size = int(row["size_bytes"])
                except ValueError:
                    report.errors.append(f"invalid size for {value}: {row['size_bytes']!r}")
                    continue
                if target.stat().st_size != expected_size:
                    report.errors.append(f"size mismatch for {value}")
                if sha256(target) != row["sha256"]:
                    report.errors.append(f"SHA-256 mismatch for {value}")
                if not row["inclusion_reason"].strip():
                    report.errors.append(f"missing inclusion reason for {value}")
                report.checked_files += 1

            expected_manifest_paths = regular_paths - {MANIFEST_NAME}
            missing_rows = sorted(expected_manifest_paths - seen)
            extra_rows = sorted(seen - expected_manifest_paths)
            for value in missing_rows:
                report.errors.append(f"archive file absent from manifest: {value}")
            for value in extra_rows:
                report.errors.append(f"manifest row absent from archive: {value}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    report = validate_archive(args.archive.resolve())
    payload = {
        "status": "valid" if not report.errors else "invalid",
        "checked_files": report.checked_files,
        "errors": report.errors,
        "warnings": report.warnings,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
