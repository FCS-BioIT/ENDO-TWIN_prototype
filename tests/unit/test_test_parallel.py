"""`pixi run test-parallel`: the split is exact and a partial run never passes.

Exercises the runner's partition, its reconciliation of the two worker reports,
its structured outcome recording, its environment check and how it launches
workers. Nothing here starts the real suite or writes to the checkout.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "src" / "scripts" / "run_test_parallel.py"

_spec = importlib.util.spec_from_file_location("run_test_parallel", SCRIPT)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

A_IDS = [
    "unit.test_phase2b_contract.Amendments.test_one",
    "unit.test_phase2b_contract.Derivation.test_two",
]
B_IDS = [
    "integration.test_x.Case.test_three",
    "unit.test_phase2b_contract_helpers.Case.test_four",
    "unit.test_y.Case.test_five",
]
PDF_SKIP = next(iter(P.ENVIRONMENT_SKIPS))


def _reports(a_ids=A_IDS, b_ids=B_IDS, discovered=None):
    full = discovered if discovered is not None else sorted(a_ids + b_ids)

    def report(worker, ids):
        return {
            "worker": worker,
            "environment_problems": [],
            "discovered": list(full),
            "assigned": list(ids),
            "outcomes": {t: {"status": "success", "detail": ""} for t in ids},
            "fixture_errors": [],
            "loader_errors": [],
            "writes": [],
        }

    return {"A": report("A", a_ids), "B": report("B", b_ids)}


OK_EXITS = {"A": 0, "B": 0}


class Partition(unittest.TestCase):
    def test_only_the_phase2b_contract_module_goes_to_worker_a(self) -> None:
        for test_id in A_IDS:
            self.assertEqual(P.worker_of(test_id), "A", test_id)
        # A module whose name merely starts with the A module's name stays in B.
        for test_id in B_IDS:
            self.assertEqual(P.worker_of(test_id), "B", test_id)

    def test_the_worker_a_module_exists(self) -> None:
        for module in P.WORKER_A_MODULES:
            self.assertTrue(
                (ROOT / "tests" / (module.replace(".", "/") + ".py")).is_file()
            )


class ModuleSearchPath(unittest.TestCase):
    def test_the_worker_path_is_the_one_python_dash_m_gives(self) -> None:
        script_path = [
            str(ROOT / "src" / "scripts"),
            "/env/lib/python3.12",
            "/env/site",
        ]
        self.assertEqual(
            P.unittest_module_path(script_path),
            [str(ROOT), "/env/lib/python3.12", "/env/site"],
        )


class IndexOfALinkedWorktree(unittest.TestCase):
    """The index compared is the one git uses, also in a linked worktree."""

    def _git(self, *args, cwd):
        subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull},
        )

    def test_a_status_neutral_index_rewrite_in_a_linked_worktree_is_seen(self) -> None:
        base = Path(self.enterContext(tempfile.TemporaryDirectory()))
        main, linked = base / "main", base / "linked"
        main.mkdir()
        self._git("init", "-q", cwd=main)
        (main / "f.txt").write_text("x\n", encoding="utf-8")
        self._git("add", "f.txt", cwd=main)
        self._git(
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "-m",
            "c",
            cwd=main,
        )
        self._git("worktree", "add", "-q", "--detach", str(linked), cwd=main)
        self.assertTrue((linked / ".git").is_file())
        index = P.git_index(linked)
        self.assertNotEqual(index, linked / ".git" / "index")
        self.assertTrue(index.is_file())
        before = P.index_bytes(linked)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=linked,
            capture_output=True,
            check=True,
        ).stdout
        # Rewrite only the index's cached stat data: git status is unchanged.
        os.utime(linked / "f.txt", ns=(1, 1))
        self._git("update-index", "--really-refresh", cwd=linked)
        self.assertEqual(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=linked,
                capture_output=True,
                check=True,
            ).stdout,
            status,
        )
        self.assertNotEqual(P.index_bytes(linked), before)

    def test_a_missing_index_is_an_error_not_an_empty_index(self) -> None:
        missing = Path("/nonexistent/index")
        with (
            mock.patch.object(P, "git_index", return_value=missing),
            self.assertRaises(OSError),
        ):
            P.index_bytes()


class Reconcile(unittest.TestCase):
    def test_a_complete_clean_run_passes(self) -> None:
        self.assertEqual(P.reconcile(_reports(), OK_EXITS), ([], []))

    def test_an_omitted_test_fails(self) -> None:
        reports = _reports(b_ids=B_IDS[:-1], discovered=sorted(A_IDS + B_IDS))
        problems, _ = P.reconcile(reports, OK_EXITS)
        self.assertTrue(any("assigned to no worker" in p for p in problems), problems)

    def test_a_test_run_by_both_workers_fails(self) -> None:
        reports = _reports(b_ids=[*B_IDS, A_IDS[0]])
        problems, _ = P.reconcile(reports, OK_EXITS)
        self.assertTrue(
            any("assigned to both workers" in p for p in problems), problems
        )

    def test_a_test_discovered_twice_fails(self) -> None:
        reports = _reports(discovered=sorted(A_IDS + B_IDS) + [B_IDS[0]])
        problems, _ = P.reconcile(reports, OK_EXITS)
        self.assertTrue(any("discovered twice" in p for p in problems), problems)

    def test_workers_that_discovered_different_suites_fail(self) -> None:
        reports = _reports()
        reports["B"]["discovered"] = reports["B"]["discovered"][:-1]
        problems, _ = P.reconcile(reports, OK_EXITS)
        self.assertTrue(any("different suites" in p for p in problems), problems)

    def test_a_test_without_an_outcome_fails(self) -> None:
        reports = _reports()
        del reports["B"]["outcomes"][B_IDS[1]]
        problems, _ = P.reconcile(reports, OK_EXITS)
        self.assertTrue(any("without an outcome" in p for p in problems), problems)

    def test_failures_errors_and_unexpected_successes_fail(self) -> None:
        for status in ("failure", "error", "unexpected_success"):
            with self.subTest(status=status):
                reports = _reports()
                reports["A"]["outcomes"][A_IDS[0]] = {"status": status, "detail": "x"}
                problems, _ = P.reconcile(reports, OK_EXITS)
                self.assertTrue(any(A_IDS[0] in p for p in problems), problems)

    def test_an_expected_failure_passes_as_in_the_serial_suite_and_is_named(
        self,
    ) -> None:
        reports = _reports()
        reports["A"]["outcomes"][A_IDS[0]] = {
            "status": "expected_failure",
            "detail": "",
        }
        problems, accepted = P.reconcile(reports, OK_EXITS)
        self.assertEqual(problems, [])
        self.assertEqual(accepted, [f"{A_IDS[0]} (expected failure)"])

    def test_an_undeclared_skip_fails(self) -> None:
        reports = _reports()
        reports["B"]["outcomes"][B_IDS[0]] = {"status": "skip", "detail": "no reason"}
        problems, accepted = P.reconcile(reports, OK_EXITS)
        self.assertTrue(any("skip" in p for p in problems), problems)
        self.assertEqual(accepted, [])

    def test_the_declared_environment_skip_is_accepted_and_named(self) -> None:
        b_ids = [*B_IDS, PDF_SKIP]
        reports = _reports(b_ids=b_ids)
        reason = f"8 {P.ENVIRONMENT_SKIPS[PDF_SKIP]}"
        reports["B"]["outcomes"][PDF_SKIP] = {"status": "skip", "detail": reason}
        problems, accepted = P.reconcile(reports, OK_EXITS)
        self.assertEqual(problems, [])
        self.assertEqual(len(accepted), 1)
        self.assertIn(PDF_SKIP, accepted[0])

    def test_the_declared_skip_with_another_reason_fails(self) -> None:
        reports = _reports(b_ids=[*B_IDS, PDF_SKIP])
        reports["B"]["outcomes"][PDF_SKIP] = {
            "status": "skip",
            "detail": "something else",
        }
        problems, accepted = P.reconcile(reports, OK_EXITS)
        self.assertTrue(problems)
        self.assertEqual(accepted, [])

    def test_a_crashed_worker_fails_even_if_the_other_passed(self) -> None:
        reports = _reports()
        reports["B"] = None
        problems, _ = P.reconcile(reports, {"A": 0, "B": -9})
        self.assertTrue(
            any("worker B wrote no report" in p for p in problems), problems
        )

    def test_exit_1_fails_even_with_a_complete_all_passing_report(self) -> None:
        problems, _ = P.reconcile(_reports(), {"A": 0, "B": 1})
        self.assertEqual(problems, ["worker B exited 1, not 0"])

    def test_exit_1_with_failures_reports_both(self) -> None:
        reports = _reports()
        reports["B"]["outcomes"][B_IDS[0]] = {"status": "failure", "detail": "x"}
        problems, _ = P.reconcile(reports, {"A": 0, "B": 1})
        self.assertIn("worker B exited 1, not 0", problems)
        self.assertTrue(any(B_IDS[0] in p for p in problems), problems)

    def test_an_abnormal_exit_fails_even_with_a_complete_report(self) -> None:
        problems, _ = P.reconcile(_reports(), {"A": 0, "B": 3})
        self.assertTrue(any("worker B exited 3" in p for p in problems), problems)

    def test_a_worker_outside_the_pixi_environment_fails(self) -> None:
        reports = _reports()
        reports["A"] = {
            "worker": "A",
            "environment_problems": ["`python` on PATH is /usr/bin/python"],
        }
        problems, _ = P.reconcile(reports, {"A": 2, "B": 0})
        self.assertTrue(
            any("not in the Pixi environment" in p for p in problems), problems
        )

    def test_fixture_and_loader_errors_and_checkout_writes_fail(self) -> None:
        for key, value in (
            ("fixture_errors", ["error: setUpClass (unit.test_y.Case)"]),
            ("loader_errors", ["ImportError: unit.test_z"]),
            ("writes", ["open src/dt_adoc/x.py"]),
        ):
            with self.subTest(key=key):
                reports = _reports()
                reports["B"][key] = value
                problems, _ = P.reconcile(reports, OK_EXITS)
                self.assertTrue(problems, key)

    def test_an_empty_worker_a_fails(self) -> None:
        problems, _ = P.reconcile(_reports(a_ids=[]), OK_EXITS)
        self.assertTrue(
            any("worker A was assigned no test" in p for p in problems), problems
        )


class StructuredOutcomes(unittest.TestCase):
    def test_every_kind_of_outcome_is_recorded_per_test(self) -> None:
        class Sample(unittest.TestCase):
            def test_pass(self):
                pass

            def test_fail(self):
                self.fail("no")

            def test_error(self):
                raise RuntimeError("boom")

            @unittest.skip("not here")
            def test_skip(self):
                pass

            def test_subtest_fails_then_passes(self):
                for i in range(2):
                    with self.subTest(i=i):
                        self.assertEqual(i, 1)

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Sample)
        runner = unittest.TextTestRunner(
            resultclass=P._RecordingResult, stream=io.StringIO(), verbosity=0
        )
        result = runner.run(suite)
        status = {k.rsplit(".", 1)[1]: v["status"] for k, v in result.outcomes.items()}
        self.assertEqual(
            status,
            {
                "test_pass": "success",
                "test_fail": "failure",
                "test_error": "error",
                "test_skip": "skip",
                "test_subtest_fails_then_passes": "failure",
            },
        )
        self.assertEqual(result.fixture_errors, [])

    def test_a_class_fixture_error_is_recorded_as_such(self) -> None:
        class Broken(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError("fixture")

            def test_never_runs(self):
                pass

        result = unittest.TextTestRunner(
            resultclass=P._RecordingResult, stream=io.StringIO(), verbosity=0
        ).run(unittest.defaultTestLoader.loadTestsFromTestCase(Broken))
        self.assertEqual(len(result.fixture_errors), 1)
        self.assertEqual(result.outcomes, {})  # so reconcile reports it unaccounted


class EnvironmentActivation(unittest.TestCase):
    def _env(self, **overrides):
        env = {
            "PIXI_PROJECT_ROOT": str(ROOT),
            "CONDA_PREFIX": sys.prefix,
            "PATH": str(Path(sys.prefix) / "bin"),
        }
        env.update(overrides)
        return env

    def test_this_checkouts_environment_is_accepted(self) -> None:
        self.assertEqual(P.environment_problems(self._env(), sys.prefix), [])

    def test_a_system_python_on_path_is_refused(self) -> None:
        problems = P.environment_problems(self._env(PATH="/usr/bin:/bin"), sys.prefix)
        self.assertTrue(any("on PATH" in p for p in problems), problems)

    def test_another_project_or_prefix_is_refused(self) -> None:
        self.assertTrue(
            P.environment_problems(
                self._env(PIXI_PROJECT_ROOT="/elsewhere"), sys.prefix
            )
        )
        self.assertTrue(
            P.environment_problems(self._env(CONDA_PREFIX="/elsewhere"), sys.prefix)
        )
        env = self._env()
        del env["PIXI_PROJECT_ROOT"]
        self.assertTrue(P.environment_problems(env, sys.prefix))

    def test_workers_are_started_through_pixi_without_inherited_activation(
        self,
    ) -> None:
        launched = []

        class FakeProcess:
            pid = 0

            def __init__(self, argv, cwd, env, stdout, stderr, start_new_session):
                launched.append(
                    {"argv": argv, "cwd": cwd, "env": env, "session": start_new_session}
                )

            def wait(self, timeout=None):
                return 0

            def poll(self):
                return 0

        scratch = self.enterContext(tempfile.TemporaryDirectory())
        inherited = {
            "CONDA_PREFIX": sys.prefix,
            "PIXI_PROJECT_ROOT": str(ROOT),
            "PATH": f"{sys.prefix}/bin:/usr/bin",
            "PIXI_EXE": "/opt/pixi/bin/pixi",
        }
        with (
            mock.patch.dict(os.environ, inherited),
            mock.patch.object(P.subprocess, "Popen", FakeProcess),
            mock.patch.object(P, "checkout_state", return_value=("same",)),
            mock.patch.object(P.tempfile, "mkdtemp", return_value=scratch),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            code = P.orchestrate(memory_cap=False)
        self.assertEqual(code, 1)  # the fake workers wrote no report
        self.assertIn("wrote no report", out.getvalue())
        self.assertEqual(len(launched), 2)
        tmpdirs = set()
        for launch in launched:
            self.assertEqual(launch["argv"][:2], ["/opt/pixi/bin/pixi", "run"])
            self.assertEqual(Path(launch["cwd"]), ROOT)
            self.assertNotIn("CONDA_PREFIX", launch["env"])
            self.assertNotIn("PIXI_PROJECT_ROOT", launch["env"])
            self.assertNotIn(sys.prefix, launch["env"]["PATH"])
            self.assertFalse(Path(launch["env"]["TMPDIR"]).is_relative_to(ROOT))
            tmpdirs.add(launch["env"]["TMPDIR"])
        self.assertEqual(len(tmpdirs), 2)


if __name__ == "__main__":
    unittest.main()


class WorkerLifecycle(unittest.TestCase):
    """No worker outlives a run: timeouts and launch failures stop them all."""

    class Fake:
        def __init__(self, pid, *, hangs=False):
            self.pid, self.hangs, self.stopped = pid, hangs, False

        def wait(self, timeout=None):
            if self.hangs and not self.stopped:
                raise subprocess.TimeoutExpired("worker", timeout)
            return 0

        def poll(self):
            return 0 if self.stopped or not self.hangs else None

    def test_a_worker_running_past_the_deadline_is_reported(self) -> None:
        processes = {"A": self.Fake(1), "B": self.Fake(2, hangs=True)}
        exits, problems = P.wait_for_workers(processes, deadline=0.0)
        self.assertEqual(exits, {"A": 0, "B": None})
        self.assertEqual(problems, ["worker B was still running at the timeout"])

    def test_stop_worker_signals_the_whole_process_group(self) -> None:
        sent = []
        fake = self.Fake(4242, hangs=True)

        def killpg(pid, sig):
            sent.append((pid, sig))
            fake.stopped = True

        with mock.patch.object(P.os, "killpg", killpg):
            P.stop_worker(fake)
        self.assertEqual(sent, [(4242, P.signal.SIGTERM)])

    def test_stop_worker_kills_a_real_worker_and_its_children(self) -> None:
        # A shell that starts a child and waits: stopping the worker must stop both.
        process = subprocess.Popen(
            ["sh", "-c", "sleep 60 & wait"], start_new_session=True
        )
        P.stop_worker(process)
        self.assertIsNotNone(process.poll())
        with self.assertRaises(ProcessLookupError):
            os.killpg(process.pid, 0)  # no process of the group is left

    def test_a_failed_second_launch_stops_the_first_worker(self) -> None:
        started = []

        class Launch:
            def __init__(self, *args, **kwargs):
                if started:
                    raise OSError("cannot start worker B")
                self.pid, self.stopped = 777, False
                started.append(self)

            def wait(self, timeout=None):
                return 0

            def poll(self):
                return None if not self.stopped else 0

        stopped = []
        scratch = self.enterContext(tempfile.TemporaryDirectory())
        with (
            mock.patch.object(P.subprocess, "Popen", Launch),
            mock.patch.object(P, "stop_worker", stopped.append),
            mock.patch.object(P, "checkout_state", return_value=("same",)),
            mock.patch.object(P.tempfile, "mkdtemp", return_value=scratch),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            code = P.orchestrate(memory_cap=False)
        self.assertEqual(code, 1)
        self.assertIn("could not run the workers", out.getvalue())
        self.assertEqual(stopped, started)  # the worker that did start was stopped


class ByteExactCheckoutState(unittest.TestCase):
    def test_a_same_size_rewrite_with_its_mtime_restored_is_a_change(self) -> None:
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull}
        for command in (
            ["git", "init", "-q"],
            ["git", "add", "f.txt"],
            [
                "git",
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@t",
                "commit",
                "-q",
                "-m",
                "c",
            ],
        ):
            if command[1] == "add":
                (root / "f.txt").write_text("abcdef\n", encoding="utf-8")
            subprocess.run(command, cwd=root, check=True, capture_output=True, env=env)
        before = P.tree_state(root)
        stat = (root / "f.txt").stat()
        (root / "f.txt").write_text("ABCDEF\n", encoding="utf-8")  # same size
        os.utime(root / "f.txt", ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertEqual((root / "f.txt").stat().st_mtime_ns, stat.st_mtime_ns)
        self.assertNotEqual(P.tree_state(root)["f.txt"], before["f.txt"])
