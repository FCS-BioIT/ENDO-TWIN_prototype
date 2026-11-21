"""`pixi run test-guards`: the guard list stays loadable and its write check is sound.

The guards are only as good as the list they run and the checks that stop a
"successful" run from meaning nothing. This keeps the list resolvable from the
complete suite (a renamed class would otherwise drop out of the guards), keeps
the two documented exclusions out, and pins the write detector's handling of
the two shapes that first produced false positives: symlink trees that point
into the checkout, and `dir_fd`-relative removals. The detector is exercised on
a temporary root and never on this checkout.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_test_guards.py"

_spec = importlib.util.spec_from_file_location("run_test_guards", SCRIPT)
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


class TheGuardListResolves(unittest.TestCase):
    def test_every_listed_guard_is_a_test_case_with_tests(self) -> None:
        loader = unittest.TestLoader()
        for name in G.guard_names():
            with self.subTest(guard=name):
                suite = loader.loadTestsFromName(name)
                self.assertEqual(loader.errors, [])
                self.assertGreater(suite.countTestCases(), 0)

    def test_the_documented_exclusions_stay_out(self) -> None:
        names = set(G.guard_names())
        self.assertNotIn(
            "unit.test_c3a_kinetic_readout.GeneratorInventoryIsImmutable", names
        )
        self.assertNotIn("test_project_validators.DataManifestValidatorTest", names)

    def test_comments_blanks_and_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / "guards.txt"
            listing.write_text(
                "# heading\n\na.B  # why\n  c.D\n!a.B.test_x  # dropped\n",
                encoding="utf-8",
            )
            self.assertEqual(G.guard_names(listing), ["a.B", "c.D"])
            self.assertEqual(G.excluded_tests(listing), ["a.B.test_x"])
            listing.write_text("a.B\na.B\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                G.guard_names(listing)

    def test_the_committed_exclusions_each_drop_exactly_one_listed_test(self) -> None:
        excluded = G.excluded_tests()
        self.assertEqual(
            sorted(excluded),
            [
                (
                    "unit.test_closure_replay.ClosureFrozenPathsTest."
                    "test_the_closure_commit_is_reachable_from_the_reviewed_tree"
                ),
                (
                    "unit.test_endpoint_figure.EndpointFigureTest."
                    "test_recorded_commit_is_reachable_from_the_reviewed_tree"
                ),
            ],
        )
        full = G.load(G.guard_names()).countTestCases()
        # Without the DT-ADOC Git history the closure-replay module skips at
        # import (tests/unit/source_history.py), so its exclusion drops nothing.
        from tests.unit.source_history import missing

        dropped = 1 if missing("97f88f55ce62e2adca23f631de3ad8e1270ad3e6") else 2
        self.assertEqual(
            G.load(G.guard_names(), excluded).countTestCases(), full - dropped
        )

    def test_a_stale_exclusion_is_refused(self) -> None:
        name = "unit.test_test_guards.TheGuardListResolves"
        with self.assertRaisesRegex(SystemExit, "not found in any listed class"):
            G.load([name], [name + ".test_that_does_not_exist"])


class TheWriteDetector(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "checkout"
        self.outside = base / "elsewhere"
        (self.root / "src").mkdir(parents=True)
        self.outside.mkdir()
        self.tracked = self.root / "src" / "module.py"
        self.tracked.write_text("x = 1\n", encoding="utf-8")
        self.link = self.outside / "module.py"
        self.link.symlink_to(self.tracked)
        patcher = mock.patch.object(G, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)
        G.WRITES.clear()
        self.addCleanup(G.WRITES.clear)

    def test_a_write_inside_the_checkout_is_recorded(self) -> None:
        G._record_writes("open", (str(self.tracked), "w", 0))
        self.assertEqual(G.WRITES, ["open src/module.py"])

    def test_a_read_is_not_recorded(self) -> None:
        G._record_writes("open", (str(self.tracked), "r", 0))
        G._record_writes("open", (str(self.tracked), None, os.O_RDONLY))
        self.assertEqual(G.WRITES, [])

    def test_a_low_level_write_open_is_recorded(self) -> None:
        G._record_writes("open", (str(self.tracked), None, os.O_WRONLY | os.O_TRUNC))
        self.assertEqual(G.WRITES, ["open src/module.py"])

    def test_writing_through_a_symlink_records_its_target(self) -> None:
        G._record_writes("open", (str(self.link), "w", 0))
        self.assertEqual(G.WRITES, ["open src/module.py"])

    def test_removing_a_symlink_that_points_in_is_not_a_write_in(self) -> None:
        # The closure and shadow views are trees of such links; deleting the view
        # deletes the links, not the checkout.
        G._record_writes("os.remove", (str(self.link), None))
        self.assertEqual(G.WRITES, [])

    def test_a_dir_fd_relative_removal_resolves_against_its_directory(self) -> None:
        outside_fd = os.open(self.outside, os.O_RDONLY)
        inside_fd = os.open(self.root / "src", os.O_RDONLY)
        try:
            G._record_writes("os.remove", ("module.py", outside_fd))
            self.assertEqual(G.WRITES, [])
            G._record_writes("os.remove", ("module.py", inside_fd))
            self.assertEqual(G.WRITES, ["os.remove src/module.py"])
        finally:
            os.close(outside_fd)
            os.close(inside_fd)

    def test_a_write_outside_the_checkout_is_not_recorded(self) -> None:
        G._record_writes("open", (str(self.outside / "new.txt"), "w", 0))
        G._record_writes("os.mkdir", (str(self.outside / "d"), 0o777, None))
        self.assertEqual(G.WRITES, [])

    def test_a_rename_into_the_checkout_is_recorded_at_its_destination(self) -> None:
        G._record_writes(
            "os.rename",
            (str(self.outside / "new.py"), str(self.root / "src" / "x.py"), None, None),
        )
        self.assertEqual(G.WRITES, ["os.rename src/x.py"])

    def test_a_rename_out_of_the_checkout_is_recorded_at_its_source(self) -> None:
        G._record_writes(
            "os.rename", (str(self.tracked), str(self.outside / "moved.py"), None, None)
        )
        self.assertEqual(G.WRITES, ["os.rename src/module.py"])

    def test_a_dir_fd_relative_rename_destination_is_resolved(self) -> None:
        outside_fd = os.open(self.outside, os.O_RDONLY)
        inside_fd = os.open(self.root / "src", os.O_RDONLY)
        try:
            G._record_writes("os.rename", ("a.py", "b.py", outside_fd, inside_fd))
            self.assertEqual(G.WRITES, ["os.rename src/b.py"])
        finally:
            os.close(outside_fd)
            os.close(inside_fd)

    def test_link_symlink_and_truncate_inside_are_recorded(self) -> None:
        G._record_writes(
            "os.symlink", (str(self.outside), str(self.root / "src" / "l"), None)
        )
        G._record_writes(
            "os.link",
            (str(self.outside / "f"), str(self.root / "src" / "h"), None, None),
        )
        G._record_writes("os.truncate", (str(self.link), 0))
        self.assertEqual(
            G.WRITES,
            ["os.symlink src/l", "os.link src/h", "os.truncate src/module.py"],
        )


class TheRunnerSeesImportTimeWrites(unittest.TestCase):
    """A guard module that writes while it is imported must fail the run.

    Run in a subprocess against a throwaway git repository: an audit hook cannot
    be removed, so it must never be installed in this test process.
    """

    MODULE = textwrap.dedent(
        """
        import unittest
        from pathlib import Path
        {body}

        class Fake(unittest.TestCase):
            def test_nothing(self):
                pass
        """
    )

    def _run(self, body: str) -> subprocess.CompletedProcess:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name).resolve()
        (root / "tests").mkdir()
        (root / "src").mkdir()
        (root / "tests" / "fake_guard.py").write_text(
            self.MODULE.format(body=body), encoding="utf-8"
        )
        (root / "guards.txt").write_text("fake_guard.Fake\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        driver = textwrap.dedent(
            f"""
            import importlib.util, sys
            from pathlib import Path
            spec = importlib.util.spec_from_file_location("g", {str(SCRIPT)!r})
            G = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(G)
            G.ROOT = Path({str(root)!r})
            raise SystemExit(G.main(G.ROOT / "guards.txt"))
            """
        )
        return subprocess.run(
            [sys.executable, "-B", "-c", driver],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_a_clean_module_passes(self) -> None:
        result = self._run("")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 tests executed", result.stdout)

    def test_an_import_time_create_and_delete_fails_the_run(self) -> None:
        body = (
            "_probe = Path(__file__).resolve().parents[1] / 'src' / 'probe.py'\n"
            "_probe.write_text('x = 1\\n')\n"
            "_probe.unlink()"
        )
        result = self._run(body)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("write(s) inside the checkout", result.stdout)
        self.assertIn("src/probe.py", result.stdout)


if __name__ == "__main__":
    unittest.main()
