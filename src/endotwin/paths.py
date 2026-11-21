"""Repository locations used by the ENDO-TWIN mainline."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAINLINE = ROOT / "endotwin"
MODELS = MAINLINE / "models"
CONFIG = MAINLINE / "config"
EVIDENCE = MAINLINE / "evidence"
PREDICTIONS = MAINLINE / "predictions"
RESULTS = MAINLINE / "results"
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets" / "endotwin"


def model_dir(version: str) -> Path:
    path = MODELS / version
    if not path.is_dir():
        raise FileNotFoundError(f"unknown ENDO-TWIN model version: {version}")
    return path


def relative(path: Path) -> str:
    """Repository-relative POSIX path, for provenance records."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()
