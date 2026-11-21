"""Run the integrity and provenance guards listed in `scripts/test_guards.txt`.

This is the fast check behind `pixi run test-guards`. It is an integrity and
provenance guard, not a substitute for `pixi run test`: the complete suite is
still the required pre-merge check.

Running these classes alone could pass while checking nothing, so the runner
refuses several shapes of that:

* a listed class that does not resolve, or resolves to no tests, is an error,
  never a silently smaller run, and so is an exclusion (`!` line) that matches no
  test;
* a skipped test is a failure, because a guard that did not run guards nothing;
* a failure inside a ``subTest`` fails the run, as unittest already does;
* the checkout must be byte-for-byte the same afterwards. Every tracked file's
  size and mtime is recorded before and after, and so is `git status`, so a
  test that rewrites a tracked file and restores it in ``finally`` is caught
  too. A snapshot cannot see a file that was created and deleted again, so an
  audit hook, installed before any guard module is imported, also records every
  write-mode open, removal, rename (both endpoints), link, symlink, truncate
  and mkdir that the test process makes inside the checkout. Subprocess writes
  are visible only to the snapshot.

Execution contract. The tests must never modify the checkout. The environment
manager is a separate matter and may need somewhere writable to install:

* in a writable isolated checkout (including the disposable checkout used for
  AIH deterministic checks), the entry point is `pixi run test-guards`;
* in a read-only snapshot, `pixi run test-guards` works if Pixi's
  environments are detached to a writable location outside the checkout
  (`detached-environments` in `$PIXI_HOME/config.toml`, as shown in
  docs/verification/README.md). Otherwise, run this file directly with an
  existing, pinned interpreter:
  `PYTHONDONTWRITEBYTECODE=1 <pixi env>/bin/python -B scripts/run_test_guards.py`.

The exact number of tests and subtests executed is printed on the last line.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

#: Reason prefix of the declared history-bound skips (tests/unit/source_history.py).
HISTORY_SKIP_PREFIX = "requires the prototype's source Git history"
#: Guard classes whose module skipped at import for that reason.
HISTORY_SKIPPED_GUARDS: list[str] = []
ROOT = Path(__file__).resolve().parents[1]
GUARDS = ROOT / "scripts" / "test_guards.txt"


def _entries(path: Path) -> list[str]:
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            entries.append(entry)
    if len(set(entries)) != len(entries):
        raise SystemExit(f"{path}: an entry is listed twice")
    return entries


def guard_names(path: Path = GUARDS) -> list[str]:
    """The listed TestCase names, in file order, without comments or blanks."""
    return [entry for entry in _entries(path) if not entry.startswith("!")]


def excluded_tests(path: Path = GUARDS) -> list[str]:
    """Individual test ids (``!`` lines) dropped from the listed classes."""
    return [entry[1:].strip() for entry in _entries(path) if entry.startswith("!")]


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, check=True
    ).stdout


def checkout_state() -> tuple[dict[str, tuple[int, int]], bytes]:
    """(size, mtime_ns) of every tracked file, and the full porcelain status."""
    stamps = {}
    for raw in _git("ls-files", "-z").split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8", "surrogateescape")
        path = ROOT / relative
        if path.is_file():
            stat = path.stat()
            stamps[relative] = (stat.st_size, stat.st_mtime_ns)
    status = _git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    return stamps, status


WRITES: list[str] = []
#: Audit events that change the tree. Each names the (path, dir_fd) argument
#: positions of every path it changes, and whether it acts through a symlink
#: (``True``: the target is written) or on the link itself (``False``: the
#: closure and shadow views are trees of links into this checkout, and removing
#: them must not count). A rename changes both of its endpoints.
_WRITE_EVENTS: dict[str, tuple[tuple[tuple[int, int | None], ...], bool]] = {
    "os.remove": (((0, 1),), False),
    "os.rmdir": (((0, 1),), False),
    "os.mkdir": (((0, 2),), False),
    "os.rename": (((0, 2), (1, 3)), False),
    "os.link": (((1, 3),), False),
    "os.symlink": (((1, 2),), False),
    "os.truncate": (((0, None),), True),
    "shutil.rmtree": (((0, 1),), False),
}


def _resolve(path: object, dir_fd: object, follow: bool) -> Path | None:
    if not isinstance(path, (str, bytes, os.PathLike)):
        return None
    try:
        target = Path(os.fsdecode(path))
        if isinstance(dir_fd, int) and not target.is_absolute():
            target = Path(os.readlink(f"/proc/self/fd/{dir_fd}")) / target
        if follow:
            return target.resolve()
        return target.absolute().parent.resolve() / target.name
    except (OSError, ValueError):
        return None


def _record_writes(event: str, args: tuple) -> None:
    """Audit hook: note any in-process write inside the checkout."""
    if event == "open":
        mode = args[1] if len(args) > 1 else "r"
        flags = args[2] if len(args) > 2 else None
        writing = isinstance(mode, str) and any(c in mode for c in "wax+")
        if not writing and isinstance(flags, int):
            writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
        if not writing:
            return
        # Writing through a symlink writes its target, so follow it.
        targets = [_resolve(args[0], None, follow=True)]
    elif event in _WRITE_EVENTS:
        positions, follow = _WRITE_EVENTS[event]
        targets = [
            _resolve(
                args[p] if len(args) > p else None,
                args[f] if f is not None and len(args) > f else None,
                follow,
            )
            for p, f in positions
        ]
    else:
        return
    for resolved in targets:
        if resolved is not None and resolved.is_relative_to(ROOT):
            WRITES.append(f"{event} {resolved.relative_to(ROOT)}")


class _CountingResult(unittest.TextTestResult):
    subtests = 0

    def addSubTest(self, test, subtest, err):
        self.subtests += 1
        super().addSubTest(test, subtest, err)


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def load(names: list[str], excluded: list[str] = ()) -> unittest.TestSuite:
    """The listed classes, minus the excluded test ids; refuses anything stale."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    unmatched = set(excluded)
    for name in names:
        try:
            loaded = loader.loadTestsFromName(name)
        except unittest.SkipTest as skip:
            # A whole guard module that reads the DT-ADOC Git history skips at
            # import in the history-free ENDO-TWIN repository. That is declared
            # and reported; any other skip still refuses the run.
            if not str(skip).startswith(HISTORY_SKIP_PREFIX):
                raise SystemExit(f"guard {name!r} skipped at import: {skip}") from None
            HISTORY_SKIPPED_GUARDS.append(name)
            module = name.rsplit(".", 1)[0]
            unmatched -= {t for t in unmatched if t.startswith(module + ".")}
            continue
        if loader.errors or loaded.countTestCases() == 0:
            detail = "\n".join(loader.errors) or "it contains no tests"
            raise SystemExit(f"guard {name!r} did not load: {detail}")
        for test in _flatten(loaded):
            if test.id() in unmatched:
                unmatched.discard(test.id())
            else:
                suite.addTest(test)
    if unmatched:
        raise SystemExit(
            "excluded test(s) not found in any listed class: "
            + ", ".join(sorted(unmatched))
        )
    return suite


def main(guards: Path | None = None) -> int:
    sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "src")]
    os.chdir(ROOT)
    listing = guards or GUARDS
    names = guard_names(listing)
    excluded = excluded_tests(listing)
    before = checkout_state()
    # Installed before any guard module is imported: a module can write at import.
    sys.addaudithook(_record_writes)
    suite = load(names, excluded)
    started = time.perf_counter()
    result = unittest.TextTestRunner(resultclass=_CountingResult, verbosity=1).run(
        suite
    )
    elapsed = time.perf_counter() - started
    writes = sorted(set(WRITES))
    after = checkout_state()

    problems = []
    if not result.wasSuccessful():
        problems.append(
            f"{len(result.failures)} failure(s), {len(result.errors)} error(s)"
        )
    # A guard that reads the DT-ADOC Git history is skipped, with this exact
    # reason prefix, in the history-free ENDO-TWIN repository
    # (tests/unit/source_history.py). That skip is declared and reported; any
    # other skip is still a failure.
    history_skips = [t.id() for t, why in result.skipped if why.startswith(HISTORY_SKIP_PREFIX)]
    other_skips = [t.id() for t, why in result.skipped if not why.startswith(HISTORY_SKIP_PREFIX)]
    if other_skips:
        problems.append(f"{len(other_skips)} guard(s) skipped: " + ", ".join(other_skips))
    history_skips = HISTORY_SKIPPED_GUARDS + history_skips
    if history_skips:
        print(
            f"{len(history_skips)} history-bound guard(s) skipped by declaration "
            "(no DT-ADOC source history in this repository): " + ", ".join(history_skips)
        )
    if after != before:
        changed = sorted(
            path
            for path in set(before[0]) | set(after[0])
            if before[0].get(path) != after[0].get(path)
        )
        detail = ", ".join(changed[:10]) or "git status changed"
        problems.append(f"the checkout was modified by the run: {detail}")
    if writes:
        problems.append(
            f"{len(writes)} write(s) inside the checkout during the run: "
            + ", ".join(writes[:10])
        )

    summary = (
        f"test-guards: {result.testsRun} tests executed "
        f"({result.subtests} subtests) from {len(names)} classes, "
        f"{len(excluded)} excluded, in {elapsed:.1f}s"
    )
    if problems:
        print(f"{summary} -- FAILED: " + "; ".join(problems))
        return 1
    print(f"{summary} -- OK, checkout unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
