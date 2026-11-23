"""Run records: a committed record must cover exactly the code under review.

`src/scripts/run_record.py` is exercised on throwaway git repositories, never on
this checkout: the parser on fixed unittest output, the writer's refusal of a
dirty tree, and the checker on each way a record can fail to cover HEAD.
"""

from __future__ import annotations

import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "run_record", ROOT / "src" / "scripts" / "run_record.py"
)
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)

ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=ENV,
    ).stdout.strip()


class Parser(unittest.TestCase):
    def test_a_passing_run_with_a_skip(self) -> None:
        out = "x ... skipped '8 cited PDF(s) not in this checkout'\n\n----\nRan 2455 tests in 1955.279s\n\nOK (skipped=1)\n"
        parsed = R.parse_unittest(out)
        self.assertEqual(parsed["tests"], 2455)
        self.assertEqual(parsed["verdict"], "OK")
        self.assertEqual(parsed["skipped"], 1)
        self.assertEqual(
            parsed["skip_reasons"], ["8 cited PDF(s) not in this checkout"]
        )

    def test_a_failing_run(self) -> None:
        parsed = R.parse_unittest(
            "Ran 10 tests in 1.0s\n\nFAILED (failures=2, errors=1)\n"
        )
        self.assertEqual(
            (parsed["verdict"], parsed["failures"], parsed["errors"]), ("FAILED", 2, 1)
        )

    def test_the_tool_verdict_is_recorded_not_pixis_banner(self) -> None:
        output = (
            "All checks passed!\n"
            "\N{SPARKLES} Pixi task (lint): ruff check src tests: (Run static lint checks)\n"
        )
        self.assertEqual(R.tool_verdict(output), "All checks passed!")

    def test_no_summary_is_not_a_pass(self) -> None:
        parsed = R.parse_unittest("Traceback (most recent call last):\n")
        self.assertIsNone(parsed["tests"])
        self.assertIsNone(parsed["verdict"])


class Repo(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(self.enterContext(tempfile.TemporaryDirectory()))
        git(self.repo, "init", "-q")
        (self.repo / "code.py").write_text("x = 1\n", encoding="utf-8")
        git(self.repo, "add", "code.py")
        git(self.repo, "commit", "-q", "-m", "code")
        self.tested = git(self.repo, "rev-parse", "HEAD")

    def commit_record(
        self, *, passed: bool = True, log: bytes = b"Ran 1 test\n", tamper: bool = False
    ) -> None:
        runs = self.repo / R.RUNS
        runs.mkdir(parents=True, exist_ok=True)
        short = self.tested[:12]
        log_gz = gzip.compress(log, mtime=0)
        (runs / f"{short}.test.log.gz").write_bytes(log_gz + (b"x" if tamper else b""))
        record = {
            "schema": R.SCHEMA,
            "tested_commit": self.tested,
            "suite": "serial",
            "checks": [{"task": "test", "exit_code": 0 if passed else 1, "result": {}}],
            "passed": passed,
            "log": {
                "path": (R.RUNS / f"{short}.test.log.gz").as_posix(),
                "sha256": hashlib.sha256(log_gz).hexdigest(),
            },
        }
        (runs / f"{short}.json").write_text(json.dumps(record), encoding="utf-8")
        git(self.repo, "add", R.RUNS.as_posix())
        git(self.repo, "commit", "-q", "-m", "record")

    def check(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = R.check(self.repo)
        return code, out.getvalue()


class Checker(Repo):
    def test_a_passing_record_of_the_code_at_head_covers_it(self) -> None:
        self.commit_record()
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_no_record_fails(self) -> None:
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("no committed record covers", out)

    def test_a_code_change_after_the_record_fails(self) -> None:
        self.commit_record()
        (self.repo / "code.py").write_text("x = 2\n", encoding="utf-8")
        git(self.repo, "commit", "-q", "-am", "later change")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("changed since its commit", out)

    def test_a_failed_record_does_not_cover(self) -> None:
        self.commit_record(passed=False)
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("did not exit 0", out)

    def test_a_log_that_does_not_match_its_digest_fails(self) -> None:
        self.commit_record(tamper=True)
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("does not match", out)

    def test_a_record_of_another_line_of_history_is_ignored(self) -> None:
        self.commit_record()
        git(self.repo, "checkout", "-q", "--orphan", "other")
        (self.repo / "code.py").write_text("x = 3\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "unrelated")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("not an ancestor", out)


class Writer(Repo):
    def test_a_dirty_tree_is_refused_before_anything_runs(self) -> None:
        (self.repo / "code.py").write_text("x = 9\n", encoding="utf-8")
        out = io.StringIO()
        with (
            contextlib.redirect_stdout(out),
            unittest.mock.patch.object(
                R, "run_task", side_effect=AssertionError("must not run")
            ),
        ):
            code = R.write_record(self.repo, "serial")
        self.assertEqual(code, 1)
        self.assertIn("not clean", out.getvalue())
        self.assertFalse((self.repo / R.RUNS).exists())

    def test_a_clean_run_writes_a_record_the_checker_accepts(self) -> None:
        def fake(root, task):
            out = "Ran 3 tests in 0.1s\n\nOK\n" if task == "test" else f"{task} ok\n"
            return {"task": task, "exit_code": 0, "seconds": 0.0}, out

        with (
            contextlib.redirect_stdout(io.StringIO()),
            unittest.mock.patch.object(R, "run_task", fake),
            unittest.mock.patch.object(R, "environment", lambda root: {}),
        ):
            self.assertEqual(R.write_record(self.repo, "serial"), 0)
        record = json.loads(
            (self.repo / R.RUNS / f"{self.tested[:12]}.json").read_text()
        )
        self.assertEqual(record["tested_commit"], self.tested)
        self.assertTrue(record["passed"])
        self.assertEqual([c["task"] for c in record["checks"]], [*R.CHECKS, "test"])
        git(self.repo, "add", R.RUNS.as_posix())
        git(self.repo, "commit", "-q", "-m", "record")
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_a_failing_check_is_recorded_as_failed(self) -> None:
        def fake(root, task):
            code = 1 if task == "lint" else 0
            return {
                "task": task,
                "exit_code": code,
                "seconds": 0.0,
            }, "Ran 1 test in 0.1s\n\nOK\n"

        with (
            contextlib.redirect_stdout(io.StringIO()),
            unittest.mock.patch.object(R, "run_task", fake),
            unittest.mock.patch.object(R, "environment", lambda root: {}),
        ):
            self.assertEqual(R.write_record(self.repo, "serial"), 1)
        record = json.loads(
            (self.repo / R.RUNS / f"{self.tested[:12]}.json").read_text()
        )
        self.assertFalse(record["passed"])


if __name__ == "__main__":
    unittest.main()
