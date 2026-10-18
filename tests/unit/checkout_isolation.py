"""Regenerate committed outputs without writing into the checkout.

A test that calls ``build(ROOT)`` and then compares the file with what it read
before rewrites the committed file when they differ: the first run fails, the
file is now regenerated, and every later run passes. Building into a shadow root
keeps a stale committed output failing until somebody regenerates and commits
it, and keeps the test from writing tracked files under a concurrent session, an
AIH review snapshot or a parallel worker.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _stamp(path: Path) -> tuple[bytes, int]:
    """Content and last-write time, so a rewrite with identical bytes shows up."""
    return path.read_bytes(), path.stat().st_mtime_ns


def regenerate_in_shadow(
    build: Callable[[Path], object], outputs: Iterable[Path | str]
) -> dict[Path, bytes]:
    """Run ``build`` on a shadow of the checkout; return the bytes it wrote.

    Inputs are symlinked and every output is carved out as a real, absent path
    (``test_generated_date_determinism._mirror``), so the generator reads the
    committed inputs and cannot write through to a tracked file. Raises if a
    committed output was touched anyway.
    """
    from tests.unit.test_generated_date_determinism import _mirror

    carved = tuple(Path(output) for output in outputs)
    before = {relative: _stamp(ROOT / relative) for relative in carved}
    with tempfile.TemporaryDirectory() as tmp:
        shadow = Path(tmp) / "shadow"
        _mirror(ROOT, shadow, carved)
        for relative in carved:
            if os.path.lexists(shadow / relative):
                raise AssertionError(
                    f"{relative} exists in the shadow root before the build; "
                    "a symlinked output would be written through to the checkout"
                )
        build(shadow)
        produced = {relative: (shadow / relative).read_bytes() for relative in carved}
    for relative, stamp in before.items():
        if _stamp(ROOT / relative) != stamp:
            raise AssertionError(
                f"{relative} was written in the checkout; the shadow root did not "
                "isolate the build"
            )
    return produced


def working_tree_copy(destination: Path) -> Path:
    """Copy the working tree's source files into ``destination``; return it.

    For runs that record their inputs and outputs relative to the root they are
    given (``provenance.describe_file`` resolves symlinks first, so a symlinked
    shadow root does not work): giving them a copy as their root keeps every
    output out of the checkout. The copy holds every tracked and every
    untracked, unignored file as it is on disk now, uncommitted edits
    included; ignored files and ``.git`` are left out, so its git provenance
    reads ``unavailable``.
    """
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    for relative in filter(None, listed.split("\0")):
        source = ROOT / relative
        if source.is_file():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return destination
