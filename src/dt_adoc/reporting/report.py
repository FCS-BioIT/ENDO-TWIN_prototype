"""Markdown report helpers."""

from __future__ import annotations

from pathlib import Path


def write_markdown_report(
    path: Path, *, title: str, sections: list[tuple[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(body.rstrip())
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
