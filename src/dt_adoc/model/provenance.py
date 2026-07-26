"""Repository-safe hashing helpers for DT_ADOC model artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class FileRef:
    path: str
    sha256: str
    size_bytes: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def to_repo_relative(path: Path, *, root: Path | None = None) -> str:
    active_root = root or repo_root()
    return str(path.resolve().relative_to(active_root.resolve()))


def describe_file(path: str | Path, *, root: Path | None = None) -> FileRef:
    active_root = root or repo_root()
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = active_root / resolved
    resolved = resolved.resolve()
    return FileRef(
        path=to_repo_relative(resolved, root=active_root),
        sha256=sha256_file(resolved),
        size_bytes=resolved.stat().st_size,
    )


def source_commit(root: Path | None = None) -> str:
    """Short git commit of the working tree, with a ``-dirty`` suffix if needed.

    A clean sha reported from a dirty tree is a false provenance claim, so the
    suffix is not optional. Returns ``"unavailable"`` outside a work tree rather
    than raising: a figure should still render without git.
    """
    import subprocess

    active_root = root or repo_root()
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=active_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=active_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        return "unavailable"
    if not sha:
        return "unavailable"
    return f"{sha}-dirty" if dirty else sha
