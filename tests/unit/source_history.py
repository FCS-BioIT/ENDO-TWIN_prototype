"""Guard for legacy checks that read the prototype repository's Git history.

ENDO-TWIN was created from the private prototype repository at commit
b1de5f90582f02291789eb72753fa5ab1f2d8c88 without its Git history
(docs/ORIGIN.md). A few legacy checks read frozen commits of that history:
closed-phase replays, pre-registration bindings and the ancestry of recorded
commits. In a checkout without those commits they are skipped, always with a
reason that starts with ``REASON_PREFIX``, and both test runners accept exactly
that reason as a declared environment skip. In any checkout that has the
commits (the source repository, or a verification clone that borrows the
source objects) they run unchanged.

Their last complete pass at the source commit is recorded in
docs/verification/source_baseline_b1de5f9.json; docs/software_verification.md
lists every guarded module and test.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_COMMIT = "b1de5f90582f02291789eb72753fa5ab1f2d8c88"
REASON_PREFIX = "requires the prototype's source Git history"


def _git_ok(*args: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
        )
    except OSError:
        return False
    return result.returncode == 0


def commit_available(sha: str) -> bool:
    return _git_ok("cat-file", "-e", f"{sha}^{{commit}}")


def is_ancestor(sha: str) -> bool:
    return commit_available(sha) and _git_ok("merge-base", "--is-ancestor", sha, "HEAD")


def missing(*shas: str) -> list[str]:
    return [sha for sha in shas if not commit_available(sha)]


def reason(*shas: str) -> str:
    return (
        f"{REASON_PREFIX}: commit(s) {', '.join(s[:12] for s in shas)} absent from this "
        "history-free repository (docs/ORIGIN.md); passed at the source commit "
        "(docs/verification/source_baseline_b1de5f9.json)"
    )


def skip_module_unless_available(*shas: str) -> None:
    """Call at module top, before any code that reads the commits."""
    absent = missing(*shas)
    if absent:
        raise unittest.SkipTest(reason(*absent))


def skip_unless_available(*shas: str):
    absent = missing(*shas)
    return unittest.skipIf(bool(absent), reason(*absent) if absent else "")


def skip_unless_ancestor(sha: str):
    ok = is_ancestor(sha)
    return unittest.skipIf(
        not ok,
        f"{REASON_PREFIX}: {sha[:12]} is not an ancestor of HEAD in this history-free repository",
    )


def skip_unless_parent_commit():
    """For checks that compare HEAD with HEAD~1."""
    ok = _git_ok("rev-parse", "--verify", "--quiet", "HEAD~1")
    return unittest.skipIf(
        not ok, f"{REASON_PREFIX}: HEAD has no parent in this history-free repository"
    )
