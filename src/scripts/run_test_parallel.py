"""Run the complete suite as two workers: `pixi run test-parallel`.

An optional, faster way to run exactly the tests `pixi run test` runs. It does
not replace `pixi run test`, which stays the required serial pre-merge check.

The split is the one benchmarked on 2026-10-19 (docs/verification/README.md):
worker A runs `unit.test_phase2b_contract`, the longest module, and worker B
runs every other module. Whole modules stay together, in discovery order, so
module and class fixtures run as they do serially.

A run passes only when all of these hold, and never on partial output:

* each worker was started through `pixi run` with an environment cleared of any
  inherited activation, and reports that its interpreter, `python` on PATH and
  the Pixi project root are this checkout's environment;
* both workers discovered the same suite, exactly as `unittest discover -s
  tests` does, and each ran its own disjoint share: the union is the whole
  suite, with no duplicate and no omission;
* every discovered test has a recorded outcome, from a structured result, and
  every outcome is a pass. As in `pixi run test`, an expected failure counts
  as passing, and is reported by name. A skip fails the run unless it is a
  declared environment skip (`ENVIRONMENT_SKIPS`), also reported by name;
* both workers exited 0 (a complete, all-passing report does not excuse any
  other exit status), none crashed or failed a fixture, and both finished
  before the timeout (``--timeout``, default 7,200 s); on a timeout, a launch
  failure or any other exit, every started worker and everything it started
  is stopped;
* the checkout is unchanged: every tracked file has the same content (SHA-256),
  every other file outside `.git/` and `.pixi/` (untracked and ignored ones
  included) has the same size and mtime afterwards, `git status` and the index (resolved with `git rev-parse --git-path index`, so a linked
  worktree's own index) are unchanged, and an audit hook in each worker recorded no
  write inside the checkout. Writes made by subprocesses are visible only to
  the snapshot.

Both workers run inside one systemd user scope capped at MemoryMax=40G with no
swap, the benchmarked limit; `--no-memory-cap` runs without it, and says so.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"
WORKER_A_MODULES = frozenset({"unit.test_phase2b_contract"})
WORKERS = ("A", "B")
MEMORY_CAP = ("-p", "MemoryMax=40G", "-p", "MemorySwapMax=0")
SCOPE_MARKER = "DT_ADOC_TEST_PARALLEL_SCOPE"
#: Wall-clock limit for the whole run; the measured run takes about 1,100 s.
DEFAULT_TIMEOUT_S = 7200
#: How long a stopped worker gets to exit after SIGTERM before SIGKILL.
STOP_GRACE_S = 10
#: Skips that depend only on what this checkout holds, never on code. Each is
#: accepted only with its exact reason, and is named in the summary.
#: Declared skips of checks that read the DT-ADOC Git history, which the
#: history-free ENDO-TWIN repository does not carry (tests/unit/source_history.py).
HISTORY_SKIP_PREFIX = "requires the prototype's source Git history"
ENVIRONMENT_SKIPS = {
    "unit.test_v052_paep_hand2.EvidenceRecordTest.test_every_cited_pdf_is_the_one_hashed": (
        "cited PDF(s) not in this checkout"
    ),
}

_spec = importlib.util.spec_from_file_location(
    "run_test_guards", ROOT / "src" / "scripts" / "run_test_guards.py"
)
GUARDS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GUARDS)


# --- worker -----------------------------------------------------------------


def worker_of(test_id: str) -> str:
    module = test_id.rsplit(".", 2)[0]
    return "A" if module in WORKER_A_MODULES else "B"


def environment_problems(environ: dict[str, str], prefix: str) -> list[str]:
    """Why this process is not running in this checkout's Pixi environment."""
    problems = []
    project = environ.get("PIXI_PROJECT_ROOT")
    if project is None or Path(project).resolve() != ROOT:
        problems.append(f"PIXI_PROJECT_ROOT is {project!r}, not {ROOT}")
    conda = environ.get("CONDA_PREFIX")
    if conda is None or Path(conda).resolve() != Path(prefix).resolve():
        problems.append(
            f"CONDA_PREFIX {conda!r} is not the interpreter prefix {prefix}"
        )
    # Tests start `python` from PATH (test_chatgpt_bundle), so PATH must
    # resolve to this environment too, not to a system interpreter.
    on_path = shutil.which("python", path=environ.get("PATH", ""))
    if on_path is None or not Path(on_path).resolve().is_relative_to(
        Path(prefix).resolve()
    ):
        problems.append(f"`python` on PATH is {on_path!r}, outside {prefix}")
    return problems


class _RecordingResult(unittest.TextTestResult):
    """Keeps one structured outcome per test id, plus fixture errors."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.outcomes: dict[str, dict[str, str]] = {}
        self.fixture_errors: list[str] = []

    def _set(self, test, status: str, detail: str = "") -> None:
        if isinstance(test, unittest.case._SubTest):
            test = test.test_case
        if (
            not isinstance(test, unittest.TestCase)
            or type(test).__name__ == "_ErrorHolder"
        ):
            self.fixture_errors.append(f"{status}: {test} {detail}".strip())
            return
        previous = self.outcomes.get(test.id(), {}).get("status")
        if previous in ("failure", "error"):
            return  # a failed subtest stays failed whatever follows
        self.outcomes[test.id()] = {"status": status, "detail": detail}

    def addSuccess(self, test):
        super().addSuccess(test)
        self._set(test, "success")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._set(test, "failure", self._exc_info_to_string(err, test)[-2000:])

    def addError(self, test, err):
        super().addError(test, err)
        self._set(test, "error", self._exc_info_to_string(err, test)[-2000:])

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._set(test, "skip", reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._set(test, "expected_failure")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._set(test, "unexpected_success")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            status = "failure" if issubclass(err[0], test.failureException) else "error"
            self._set(test, status, f"subtest {subtest}: {err[1]}"[-2000:])


def _flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def unittest_module_path(path: list[str]) -> list[str]:
    """``sys.path`` as `python -m unittest` would have it, from this script's.

    Run as a script, Python puts the script's directory first; run as `-m`, it
    puts the working directory (the repository root) there, and the suite
    relies on it (`from tests.unit import ...`). Nothing else is added: the
    tests put `src/` on the path themselves, as they do under `pixi run test`.
    """
    return [str(ROOT), *path[1:]]


def run_worker(worker: str, report: Path) -> int:
    os.chdir(ROOT)
    payload: dict = {"worker": worker, "environment_problems": []}
    problems = environment_problems(dict(os.environ), sys.prefix)
    if problems:
        payload["environment_problems"] = problems
        report.write_text(json.dumps(payload), encoding="utf-8")
        return 2
    sys.path[:] = unittest_module_path(sys.path)
    # Installed before any test module is imported: a module can write at import.
    sys.addaudithook(GUARDS._record_writes)
    loader = unittest.TestLoader()
    # Same start and top-level directory as `python -m unittest discover -s tests`.
    suite = loader.discover(start_dir=str(TESTS), top_level_dir=str(TESTS))
    discovered = [test.id() for test in _flatten(suite)]
    mine = [test for test in _flatten(suite) if worker_of(test.id()) == worker]
    started = time.perf_counter()
    result = unittest.TextTestRunner(resultclass=_RecordingResult, verbosity=2).run(
        unittest.TestSuite(mine)
    )
    payload.update(
        discovered=discovered,
        assigned=[test.id() for test in mine],
        outcomes=result.outcomes,
        fixture_errors=result.fixture_errors,
        loader_errors=list(loader.errors),
        writes=sorted(set(GUARDS.WRITES)),
        seconds=time.perf_counter() - started,
    )
    report.write_text(json.dumps(payload), encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


# --- orchestrator -----------------------------------------------------------


def reconcile(
    reports: dict[str, dict | None], exits: dict[str, int]
) -> tuple[list[str], list[str]]:
    """(problems, accepted environment skips) for two worker reports."""
    problems: list[str] = []
    accepted: list[str] = []
    for worker in WORKERS:
        report = reports.get(worker)
        if report is None:
            problems.append(
                f"worker {worker} wrote no report (exit {exits.get(worker)})"
            )
        elif report.get("environment_problems"):
            problems.append(
                f"worker {worker} is not in the Pixi environment: "
                + "; ".join(report["environment_problems"])
            )
        elif exits.get(worker) not in (0, 1):
            problems.append(f"worker {worker} exited {exits.get(worker)}")
    if problems:
        return problems, accepted
    for worker in WORKERS:
        # A complete report does not excuse a non-zero exit: success is exit 0.
        # (1 is unittest's "something failed"; the failures are listed below.)
        if exits.get(worker) != 0:
            problems.append(f"worker {worker} exited {exits.get(worker)}, not 0")
    full = reports["A"]["discovered"]
    if reports["B"]["discovered"] != full:
        problems.append("the two workers discovered different suites")
    duplicated = sorted({t for t in full if full.count(t) > 1})
    if duplicated:
        problems.append(
            f"{len(duplicated)} test id(s) discovered twice: {duplicated[:5]}"
        )
    assigned_a, assigned_b = reports["A"]["assigned"], reports["B"]["assigned"]
    if not assigned_a:
        problems.append(
            f"worker A was assigned no test: {sorted(WORKER_A_MODULES)} not discovered"
        )
    both = sorted(set(assigned_a) & set(assigned_b))
    if both:
        problems.append(f"{len(both)} test(s) assigned to both workers: {both[:5]}")
    union = assigned_a + assigned_b
    missing = sorted(set(full) - set(union))
    extra = sorted(set(union) - set(full))
    if missing:
        problems.append(
            f"{len(missing)} discovered test(s) assigned to no worker: {missing[:5]}"
        )
    if extra:
        problems.append(
            f"{len(extra)} assigned test(s) were not discovered: {extra[:5]}"
        )
    for worker in WORKERS:
        report = reports[worker]
        for error in report.get("loader_errors", []):
            problems.append(f"worker {worker} failed to load tests: {error[:300]}")
        for error in report.get("fixture_errors", []):
            problems.append(f"worker {worker} fixture error: {error[:300]}")
        outcomes = report["outcomes"]
        unaccounted = [t for t in report["assigned"] if t not in outcomes]
        if unaccounted:
            problems.append(
                f"worker {worker}: {len(unaccounted)} test(s) without an outcome: {unaccounted[:5]}"
            )
        for test_id, outcome in sorted(outcomes.items()):
            status, detail = outcome["status"], outcome.get("detail", "")
            if status == "success":
                continue
            if status == "expected_failure":
                # `pixi run test` counts these as passing; so does this run, by name.
                accepted.append(f"{test_id} (expected failure)")
                continue
            if (
                status == "skip"
                and ENVIRONMENT_SKIPS.get(test_id)
                and ENVIRONMENT_SKIPS[test_id] in detail
            ) or (status == "skip" and HISTORY_SKIP_PREFIX in detail):
                accepted.append(f"{test_id} ({detail})")
                continue
            problems.append(f"worker {worker}: {test_id} {status}: {detail[:300]}")
        for write in report.get("writes", []):
            problems.append(f"worker {worker} wrote inside the checkout: {write}")
    return problems, accepted


def tree_state(root: Path = ROOT) -> dict[str, tuple]:
    """Every path outside .git/ and .pixi/, ignored ones included.

    Each path maps to (size, mtime_ns), and a tracked file also carries its
    SHA-256, so a tracked file rewritten with the same size and its timestamp
    restored is still a change. Untracked and ignored files are compared by
    size and mtime only (the multi-gigabyte data objects are not hashed).
    """
    tracked = set(
        subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=True,
        )
        .stdout.decode("utf-8", "surrogateescape")
        .split("\0")
    )
    state = {}
    for directory, dirs, files in os.walk(root):
        if directory == str(root):
            dirs[:] = [d for d in dirs if d not in (".git", ".pixi")]
        for name in dirs + files:
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, root)
            stat = os.lstat(path)
            entry: tuple = (stat.st_size, stat.st_mtime_ns)
            if (
                relative in tracked
                and os.path.isfile(path)
                and not os.path.islink(path)
            ):
                with open(path, "rb") as handle:
                    entry += (hashlib.file_digest(handle, "sha256").hexdigest(),)
            state[relative] = entry
    return state


def git_index(root: Path = ROOT) -> Path:
    """The index git uses for ``root``: in a linked worktree `.git` is a file and
    the index lives under the common directory's `worktrees/<name>/`."""
    raw = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-path", "index"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()
    return (root / raw).resolve()


def index_bytes(root: Path = ROOT) -> bytes:
    """The index content; raises rather than compare a missing index as empty."""
    return git_index(root).read_bytes()


def checkout_state() -> tuple:
    return (tree_state(), GUARDS.checkout_state(), index_bytes())


def clean_environment(tmpdir: Path) -> dict[str, str]:
    """No inherited activation: `pixi run` must provide the whole environment."""
    # Pixi's own configuration (where it keeps environments and caches) is kept;
    # its activation (PATH, CONDA_PREFIX, PIXI_PROJECT_*) is not.
    keep = (
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "LC_ALL",
        "TERM",
        "XDG_RUNTIME_DIR",
        "DBUS_SESSION_BUS_ADDRESS",
        "PIXI_HOME",
        "PIXI_CACHE_DIR",
        "RATTLER_CACHE_DIR",
    )
    env = {k: os.environ[k] for k in keep if k in os.environ}
    env.update(PATH="/usr/bin:/bin", TMPDIR=str(tmpdir), PYTHONDONTWRITEBYTECODE="1")
    return env


def pixi_executable() -> str | None:
    return os.environ.get("PIXI_EXE") or shutil.which("pixi")


def stop_worker(process: subprocess.Popen) -> None:
    """Stop a worker and everything it started (its own process group)."""
    if process.poll() is not None:
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=STOP_GRACE_S)
            return
        except subprocess.TimeoutExpired:
            continue


def wait_for_workers(
    processes: dict[str, subprocess.Popen], deadline: float
) -> tuple[dict[str, int | None], list[str]]:
    """Exit codes, or None for a worker still running at ``deadline``."""
    exits: dict[str, int | None] = {}
    problems = []
    for worker, process in processes.items():
        try:
            exits[worker] = process.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            exits[worker] = None
            problems.append(f"worker {worker} was still running at the timeout")
    return exits, problems


def orchestrate(memory_cap: bool, timeout: float = DEFAULT_TIMEOUT_S) -> int:
    pixi = pixi_executable()
    if pixi is None:
        print(
            "test-parallel: FAILED -- pixi not found; workers are only ever started through `pixi run`"
        )
        return 1
    if memory_cap and os.environ.get(SCOPE_MARKER) != "1":
        systemd_run = shutil.which("systemd-run")
        if systemd_run is None:
            print(
                "test-parallel: FAILED -- systemd-run not found for the memory cap; "
                "rerun with --no-memory-cap to run uncapped"
            )
            return 1
        os.environ[SCOPE_MARKER] = "1"
        return subprocess.run(
            [
                systemd_run,
                "--user",
                "--scope",
                "-q",
                *MEMORY_CAP,
                sys.executable,
                "-B",
                __file__,
                *sys.argv[1:],
            ],
            check=False,
        ).returncode
    before = checkout_state()
    started = time.perf_counter()
    scratch = Path(tempfile.mkdtemp(prefix="dt_adoc_test_parallel_"))
    processes, logs, report_paths = {}, {}, {}
    deadline = time.monotonic() + timeout
    launch_problems: list[str] = []
    try:
        for worker in WORKERS:
            tmpdir = scratch / f"tmp{worker}"
            tmpdir.mkdir()
            report_paths[worker] = scratch / f"report_{worker}.json"
            logs[worker] = scratch / f"worker_{worker}.log"
            with logs[worker].open("w") as log:
                processes[worker] = subprocess.Popen(
                    [
                        pixi,
                        "run",
                        "--manifest-path",
                        str(ROOT / "pixi.toml"),
                        "-q",
                        "python",
                        "-B",
                        __file__,
                        "--worker",
                        worker,
                        str(report_paths[worker]),
                    ],
                    cwd=ROOT,
                    env=clean_environment(tmpdir),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,  # its own process group, for stop_worker
                )
        exits, launch_problems = wait_for_workers(processes, deadline)
    except (OSError, ValueError, subprocess.SubprocessError) as error:  # not started
        exits = {worker: None for worker in WORKERS}
        launch_problems = [f"could not run the workers: {error!r}"]
    finally:
        # Whatever happened above, no worker outlives this run.
        for process in processes.values():
            stop_worker(process)
    elapsed = time.perf_counter() - started
    reports = {}
    for worker, path in report_paths.items():
        try:
            reports[worker] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            reports[worker] = None
    problems, accepted = reconcile(reports, exits)
    problems = launch_problems + problems
    after = checkout_state()
    if after != before:
        changed = sorted(
            p
            for p in set(before[0]) | set(after[0])
            if before[0].get(p) != after[0].get(p)
        )
        detail = ", ".join(changed[:10]) or "git status or the index changed"
        problems.append(f"the checkout was modified by the run: {detail}")
    counts = {
        w: len(r["assigned"]) for w, r in reports.items() if r and "assigned" in r
    }
    summary = (
        f"test-parallel: {sum(counts.values())} tests "
        f"(A {counts.get('A', '?')}, B {counts.get('B', '?')}) in {elapsed:.1f}s, "
        f"logs in {scratch}"
    )
    if not memory_cap:
        summary += ", WITHOUT the memory cap"
    if problems:
        print(f"{summary} -- FAILED:")
        for problem in problems[:50]:
            print(f"  - {problem}")
        return 1
    if accepted:
        summary += f" -- {len(accepted)} accepted non-pass outcome(s): " + "; ".join(
            accepted
        )
        if any(t in a for a in accepted for t in ENVIRONMENT_SKIPS):
            summary += " -- not equivalent to a run with the skipped inputs present"
    print(f"{summary} -- OK, every test accounted for, checkout unchanged")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--worker", choices=WORKERS)
    parser.add_argument("report", nargs="?", type=Path)
    parser.add_argument("--no-memory-cap", action="store_true")
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(
            os.environ.get("DT_ADOC_TEST_PARALLEL_TIMEOUT", DEFAULT_TIMEOUT_S)
        ),
        help="seconds before the run is stopped and failed (default %(default)s)",
    )
    args = parser.parse_args(argv)
    if args.worker:
        return run_worker(args.worker, args.report)
    return orchestrate(memory_cap=not args.no_memory_cap, timeout=args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
