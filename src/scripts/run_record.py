"""Machine-readable records of the required checks, committed with each PR.

`pixi run run-record` runs the required checks on the committed HEAD of a clean
tree and writes ``docs/verification/runs/<commit>.json`` with the gzipped test
log beside it. Commit both on the PR branch. `pixi run check-run-record` then
passes only if a committed record covers the code at HEAD:

* the record's tested commit is HEAD or an ancestor of it, and nothing outside
  ``docs/verification/runs/`` changed since, so the record describes exactly
  the code under review (re-run after any later code commit);
* every recorded check exited 0;
* the committed log is the one the record names (SHA-256).

The record is produced on the author's machine, so it attests what was run
there; it is not an independent CI result. It is meant for PR branches: on
``main`` after a merge, other PRs' changes sit between a record and HEAD.

Checks, in order: ``lint``, ``format-check``, ``test-guards`` and the complete
serial ``test`` (``--suite parallel`` runs ``test-parallel`` instead and records
that it did; ``test`` stays the required pre-merge check).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = Path("docs/verification/runs")
SCHEMA = "dt_adoc.run_record/1"
CHECKS = ("lint", "format-check", "test-guards")
SUITES = {"serial": "test", "parallel": "test-parallel"}


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def git_ok(root: Path, *args: str) -> bool:
    """Whether a git command succeeds (for the yes/no queries)."""
    return (
        subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, check=False
        ).returncode
        == 0
    )


def dirty(root: Path) -> list[str]:
    status = git(root, "status", "--porcelain", "--untracked-files=all")
    return [line for line in status.splitlines() if line.strip()]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_unittest(output: str) -> dict:
    """Counts from a unittest run's closing lines (``Ran N tests`` and the verdict)."""
    ran = re.findall(r"^Ran (\d+) tests? in ([\d.]+)s$", output, re.MULTILINE)
    verdict = re.findall(r"^(OK|FAILED)(?: \(([^)]*)\))?$", output, re.MULTILINE)
    counts = {"failures": 0, "errors": 0, "skipped": 0, "expected_failures": 0}
    if verdict:
        for part in (verdict[-1][1] or "").split(","):
            key, _, value = part.strip().partition("=")
            key = {"expected failures": "expected_failures"}.get(key, key)
            if key in counts and value.isdigit():
                counts[key] = int(value)
    skips = sorted(set(re.findall(r"\.\.\. skipped '([^']*)'", output)))
    return {
        "tests": int(ran[-1][0]) if ran else None,
        "unittest_seconds": float(ran[-1][1]) if ran else None,
        "verdict": verdict[-1][0] if verdict else None,
        **counts,
        "skip_reasons": skips,
    }


def summary_line(output: str, prefix: str) -> str | None:
    lines = [line for line in output.splitlines() if line.startswith(prefix)]
    return lines[-1] if lines else None


#: Pixi prints this banner (on stderr) for every task it runs.
PIXI_BANNER = "\N{SPARKLES} Pixi task"


def tool_verdict(output: str) -> str:
    """The tool's own last line (``All checks passed!``), not pixi's banner."""
    lines = [
        line.strip()
        for line in output.splitlines()
        if line.strip() and not line.lstrip().startswith(PIXI_BANNER)
    ]
    return lines[-1] if lines else ""


def run_task(root: Path, task: str) -> tuple[dict, str]:
    started = time.perf_counter()
    result = subprocess.run(
        ["pixi", "run", task],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    return {
        "task": task,
        "exit_code": result.returncode,
        "seconds": round(time.perf_counter() - started, 1),
    }, output


def environment(root: Path) -> dict:
    def first_line(*command: str) -> str:
        try:
            return (
                subprocess.run(
                    command, cwd=root, capture_output=True, text=True, check=False
                )
                .stdout.strip()
                .splitlines()[0]
            )
        except (OSError, IndexError):
            return "unavailable"

    lock = root / "pixi.lock"
    return {
        "pixi": first_line("pixi", "--version"),
        "python": first_line("pixi", "run", "-q", "python", "--version"),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "pixi_lock_sha256": sha256_bytes(lock.read_bytes()) if lock.is_file() else None,
    }


def write_record(root: Path, suite: str) -> int:
    if dirty(root):
        print("run-record: refused -- the tree is not clean; commit first:")
        print("\n".join(f"  {line}" for line in dirty(root)[:20]))
        return 1
    commit = git(root, "rev-parse", "HEAD")
    tree = git(root, "rev-parse", "HEAD^{tree}")
    started = time.time()
    checks, logs = [], {}
    for task in (*CHECKS, SUITES[suite]):
        record, output = run_task(root, task)
        if task in ("test", "test-parallel"):
            record["result"] = (
                parse_unittest(output)
                if task == "test"
                else {"summary": summary_line(output, "test-parallel:")}
            )
        elif task == "test-guards":
            record["summary"] = summary_line(output, "test-guards:")
        else:
            record["summary"] = tool_verdict(output)
        checks.append(record)
        logs[task] = output
        print(
            f"run-record: {task} exited {record['exit_code']} in {record['seconds']}s",
            flush=True,
        )
    if git(root, "rev-parse", "HEAD") != commit or dirty(root):
        print("run-record: refused -- HEAD or the tree changed during the run")
        return 1
    suite_task = SUITES[suite]
    log_bytes = gzip.compress(logs[suite_task].encode("utf-8"), mtime=0)
    short = commit[:12]
    out_dir = root / RUNS
    out_dir.mkdir(parents=True, exist_ok=True)
    log_name = f"{short}.{suite_task}.log.gz"
    (out_dir / log_name).write_bytes(log_bytes)
    payload = {
        "schema": SCHEMA,
        "tested_commit": commit,
        "tested_tree": tree,
        "suite": suite,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "wall_seconds": round(time.time() - started, 1),
        "environment": environment(root),
        "checks": checks,
        "passed": all(c["exit_code"] == 0 for c in checks),
        "log": {
            "path": (RUNS / log_name).as_posix(),
            "sha256": sha256_bytes(log_bytes),
        },
        "attestation": "run on the author's machine by src/scripts/run_record.py; not an independent CI result",
    }
    (out_dir / f"{short}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"run-record: wrote {RUNS / (short + '.json')} ({'passed' if payload['passed'] else 'FAILED'}); "
        "commit it and the log on this branch"
    )
    return 0 if payload["passed"] else 1


def covering_records(root: Path, head: str = "HEAD") -> tuple[list[dict], list[str]]:
    """Records committed at ``head`` that cover its code, and why others do not."""
    notes, covering = [], []
    head_sha = git(root, "rev-parse", head)
    runs = f"{head_sha}:{RUNS.as_posix()}"
    listed = (
        git(root, "ls-tree", "--name-only", runs)
        if git_ok(root, "cat-file", "-e", runs)
        else ""
    )
    for name in sorted(n for n in listed.splitlines() if n.endswith(".json")):
        record = json.loads(git(root, "show", f"{head_sha}:{RUNS.as_posix()}/{name}"))
        tested = record.get("tested_commit", "")
        ancestor = git_ok(root, "merge-base", "--is-ancestor", tested, head_sha)
        if not ancestor:
            notes.append(
                f"{name}: tested commit {tested[:12]} is not an ancestor of HEAD"
            )
            continue
        changed = [
            p
            for p in git(root, "diff", "--name-only", tested, head_sha).splitlines()
            if not p.startswith(RUNS.as_posix() + "/")
        ]
        if changed:
            notes.append(
                f"{name}: {len(changed)} file(s) changed since its commit, e.g. {changed[0]}"
            )
            continue
        record["_name"] = name
        covering.append(record)
    return covering, notes


def check(root: Path, head: str = "HEAD") -> int:
    covering, notes = covering_records(root, head)
    if not covering:
        print("check-run-record: FAILED -- no committed record covers the code at HEAD")
        for note in notes:
            print(f"  - {note}")
        return 1
    head_sha = git(root, "rev-parse", head)
    problems = []
    for record in covering:
        name = record["_name"]
        if not record.get("passed") or any(
            c["exit_code"] != 0 for c in record.get("checks", [])
        ):
            problems.append(f"{name}: a recorded check did not exit 0")
        log = record.get("log", {})
        try:
            data = subprocess.run(
                ["git", "-C", str(root), "show", f"{head_sha}:{log['path']}"],
                capture_output=True,
                check=True,
            ).stdout
        except (KeyError, subprocess.CalledProcessError):
            problems.append(f"{name}: its log is not committed")
            continue
        if sha256_bytes(data) != log.get("sha256"):
            problems.append(
                f"{name}: the committed log does not match the recorded SHA-256"
            )
    if problems:
        print("check-run-record: FAILED")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    best = covering[-1]
    suite = next((c for c in best["checks"] if c["task"] in SUITES.values()), {})
    print(
        f"check-run-record: OK -- {best['_name']} covers HEAD (tested {best['tested_commit'][:12]}, "
        f"{best['suite']} suite: {suite.get('result', {})})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    write = sub.add_parser("write", help="run the checks and write a record")
    write.add_argument("--suite", choices=sorted(SUITES), default="serial")
    sub.add_parser("check", help="verify a committed record covers HEAD")
    args = parser.parse_args(argv)
    if args.command == "write":
        return write_record(ROOT, args.suite)
    return check(ROOT)


if __name__ == "__main__":
    sys.exit(main())
