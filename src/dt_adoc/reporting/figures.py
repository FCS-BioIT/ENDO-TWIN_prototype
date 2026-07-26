"""Figure-spec helpers for smoke reports."""

from __future__ import annotations


def line_figure_spec(title: str, x_label: str, y_label: str) -> dict[str, str]:
    return {
        "type": "line",
        "title": title,
        "x_label": x_label,
        "y_label": y_label,
    }
