#!/usr/bin/env python3
"""Export every worksheet cell from the ADOC protein workbook to TSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import date, datetime, time
from pathlib import Path

from openpyxl import load_workbook


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_sheet_slug(name: str) -> str:
    stripped = name.strip()
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", stripped)
    return slug.strip("._-") or "sheet"


def serialize_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return str(value)


def export_workbook(source: Path, output_dir: Path) -> list[dict[str, object]]:
    source = source.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    sheets_dir = output_dir / "sheets"
    sheets_dir.mkdir(exist_ok=True)
    workbook = load_workbook(source, read_only=True, data_only=False)
    rows: list[dict[str, object]] = []

    try:
        for index, worksheet in enumerate(workbook.worksheets, start=1):
            filename = f"sheet_{index:02d}_{safe_sheet_slug(worksheet.title)}.tsv"
            target = sheets_dir / filename
            nonempty_cells = 0
            formula_cells = 0
            with target.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
                for source_row in worksheet.iter_rows(
                    min_row=1,
                    max_row=worksheet.max_row,
                    min_col=1,
                    max_col=worksheet.max_column,
                    values_only=True,
                ):
                    values = [serialize_cell(value) for value in source_row]
                    nonempty_cells += sum(value != "" for value in values)
                    formula_cells += sum(value.startswith("=") for value in values)
                    writer.writerow(values)
            rows.append(
                {
                    "sheet_index": index,
                    "sheet_name": worksheet.title,
                    "sheet_name_json": json.dumps(
                        worksheet.title, ensure_ascii=False
                    ),
                    "exported_path": f"sheets/{filename}",
                    "max_row": worksheet.max_row,
                    "max_column": worksheet.max_column,
                    "nonempty_cells": nonempty_cells,
                    "formula_cells": formula_cells,
                }
            )
    finally:
        workbook.close()

    manifest = output_dir / "WORKBOOK_SHEETS.tsv"
    fieldnames = [
        "sheet_index",
        "sheet_name",
        "sheet_name_json",
        "exported_path",
        "max_row",
        "max_column",
        "nonempty_cells",
        "formula_cells",
    ]
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    readme = output_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# ADOC protein-readout tables",
                "",
                "These TSV files are cell-value exports of every worksheet in",
                f"`{source.name}`. No values were normalized, imputed, pooled,",
                "or mapped to model states.",
                "",
                f"- Source size: {source.stat().st_size} bytes",
                f"- Source SHA-256: `{sha256(source)}`",
                f"- Worksheets exported: {len(rows)}",
                "- Blank cells are empty TSV fields; numeric zero remains `0`.",
                "- Formula cells retain their formula text rather than cached values.",
                "- `WORKBOOK_SHEETS.tsv` preserves original sheet names, including",
                "  leading or trailing whitespace.",
                "- Units, sample mapping, replicate structure, and detection-limit",
                "  semantics remain unresolved unless documented elsewhere.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    rows = export_workbook(args.input, args.output_dir)
    print(
        json.dumps(
            {
                "status": "exported",
                "source": str(args.input),
                "output_dir": str(args.output_dir),
                "worksheets": len(rows),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
