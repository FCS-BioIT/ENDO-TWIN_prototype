"""The closure-time snapshot the closed Phase 1B / 2A / 2B analyses replay against.

Adding a model version must not imply that a closed analysis changed. These
tests pin both halves of that statement:

1. Every historical version is byte-identical. The snapshot, copied from the
   live tree, has exactly the digest Phase 1B recorded at closure.
2. New versions are outside the snapshot by construction, not by exception.
   The closure set names only the versions that existed at closure, and neither
   the snapshot's files nor its git index contains anything later.
3. Phase 2B's other frozen paths are the closure commit's, file for file and
   index entry for index entry. The live tree may differ from them only by what
   ``closure_replay`` declares, and the declaration is enforced.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc import closure_replay as R
from dt_adoc.experiments import phase1b_closure as p1b
from dt_adoc.personalization.phase2b import audit as p2b

#: Recorded by the Phase 1B closure (docs/phase1b_closure/phase1b_closure_summary.json).
CLOSURE_MODELS_TREE_SHA256 = (
    "de1bddba2be91e837fefbd784c21790531790ec0ee85c5babd7d4dd2844657b5"
)
VERSIONED = re.compile(r"^adoc-literature-superset-v\d+\.\d+\.\d+$")


class ClosureSnapshotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(prefix="closure-replay-test-")
        cls.view, cls.index = R.build_view(ROOT, Path(cls.tmp.name))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_the_snapshot_is_the_tree_the_closure_recorded(self) -> None:
        self.assertEqual(
            p1b._tree_sha(self.view, Path("models")), CLOSURE_MODELS_TREE_SHA256
        )

    def test_the_recorded_digest_is_the_one_in_the_frozen_summary(self) -> None:
        import json

        summary = json.loads((ROOT / p1b.OUT_SUMMARY).read_text(encoding="utf-8"))
        self.assertEqual(
            summary["lineage"]["models_tree_sha256"], CLOSURE_MODELS_TREE_SHA256
        )

    def test_every_historical_version_is_still_on_the_live_tree(self) -> None:
        live = {p.name for p in (ROOT / R.SUPERSET).iterdir() if p.is_dir()}
        self.assertTrue(R.CLOSURE_SUPERSET_VERSIONS <= live)

    def test_later_versions_are_excluded_by_construction_not_by_name(self) -> None:
        later = R.post_closure_versions(ROOT)
        for name in later:
            with self.subTest(version=name):
                self.assertRegex(name, VERSIONED)
                self.assertFalse((self.view / R.SUPERSET / name).exists())
        source = (SRC / "dt_adoc/closure_replay.py").read_text(encoding="utf-8")
        for name in later:
            self.assertNotIn(name, source, "the replay layer names no later version")

    def test_the_snapshot_models_are_copies_not_links(self) -> None:
        models = self.view / "models"
        self.assertFalse(models.is_symlink())
        self.assertFalse(any(p.is_symlink() for p in models.rglob("*")))

    def test_the_snapshot_index_has_no_post_closure_path(self) -> None:
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--cached", "--", "models/superset"],
            env={"GIT_INDEX_FILE": str(self.index), "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        versions = {Path(line).parts[2] for line in listed}
        self.assertTrue(versions <= R.CLOSURE_SUPERSET_VERSIONS, versions)

    def test_no_closed_phase_builder_writes_under_models(self) -> None:
        import importlib

        for task, module_name in R.CLOSED_PHASE_BUILDERS.items():
            with self.subTest(task=task):
                outputs = R.outputs_of(importlib.import_module(module_name))
                self.assertFalse(any(p.is_relative_to("models") for p in outputs))


class ClosureFrozenPathsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(prefix="closure-frozen-test-")
        cls.view, cls.index = R.build_view(ROOT, Path(cls.tmp.name))
        cls.entries = R._closure_entries(ROOT)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_the_frozen_paths_are_phase2b_s(self) -> None:
        self.assertEqual(
            set(R.CLOSURE_FROZEN_PATHS) | {"models/"}, set(p2b.FROZEN_PREFIXES)
        )

    def test_the_closure_commit_is_the_one_that_closed_phase2b(self) -> None:
        subject = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "log",
                "-1",
                "--format=%s",
                R.PHASE2B_CLOSURE_COMMIT,
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(
            subject, "docs(phase2b): close Phase 2B as NO_SUITABLE_REFERENCE"
        )

    def test_the_closure_commit_is_reachable_from_the_reviewed_tree(self) -> None:
        # Reachability is a property of commits, and the independent review's
        # snapshot HEAD is a parentless `git commit-tree` copy of the reviewed
        # tree, so asserting ancestry of HEAD itself fails there. Resolve the
        # reviewed tree to the commit(s) that carry it, as
        # tests/unit/test_endpoint_figure.py does, which ties the claim to the
        # exact bytes under review rather than to this checkout's history.
        def git(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                ["git", "-C", str(ROOT), *args],
                capture_output=True,
                text=True,
                check=False,
            )

        tree = git("rev-parse", "HEAD^{tree}").stdout.strip()
        self.assertTrue(tree, "HEAD has no tree")
        carriers = ["HEAD"] + [
            line.split()[0]
            for line in git("log", "--all", "--format=%H %T").stdout.splitlines()
            if line and line.split()[1] == tree
        ]
        reachable = [
            carrier
            for carrier in carriers
            if git(
                "merge-base", "--is-ancestor", R.PHASE2B_CLOSURE_COMMIT, carrier
            ).returncode
            == 0
        ]
        self.assertTrue(
            reachable,
            f"{R.PHASE2B_CLOSURE_COMMIT} is not an ancestor of any commit "
            f"carrying tree {tree}: checked {carriers}",
        )

    def test_the_snapshot_holds_exactly_the_closure_files_as_real_copies(self) -> None:
        self.assertTrue(self.entries)
        expected = {path for _, _, path in self.entries}
        present = set()
        for prefix in R.CLOSURE_FROZEN_PATHS:
            base = self.view / prefix
            if base.is_file():
                present.add(prefix)
                continue
            self.assertFalse(base.is_symlink(), prefix)
            for path in base.rglob("*"):
                self.assertFalse(path.is_symlink(), path)
                if path.is_file():
                    present.add(path.relative_to(self.view).as_posix())
        self.assertEqual(present, expected)
        for _, sha, path in self.entries:
            blob = subprocess.run(
                ["git", "-C", str(ROOT), "cat-file", "blob", sha],
                capture_output=True,
                check=True,
            ).stdout
            self.assertEqual((self.view / path).read_bytes(), blob, path)

    def test_post_closure_files_are_absent_from_the_snapshot_and_its_index(
        self,
    ) -> None:
        listed = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "ls-files",
                "--cached",
                "-s",
                "--",
                *R.CLOSURE_FROZEN_PATHS,
            ],
            env={"GIT_INDEX_FILE": str(self.index), "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        indexed = {}
        for line in listed:
            meta, path = line.split("\t", 1)
            mode, sha, _ = meta.split()
            indexed[path] = (mode, sha)
        self.assertEqual(
            indexed, {path: (mode, sha) for mode, sha, path in self.entries}
        )
        for path in R.POST_CLOSURE_FILES:
            self.assertFalse((self.view / path).exists(), path)
            self.assertNotIn(path, indexed)

    def test_builder_outputs_under_frozen_paths_stay_carved(self) -> None:
        carved = (Path("docs/phase2a/phase2a_status.json"),)
        with tempfile.TemporaryDirectory() as tmp:
            view, _ = R.build_view(ROOT, Path(tmp), carved)
            self.assertFalse((view / carved[0]).exists())
            self.assertTrue((view / "docs/phase2a/reference_gate.json").is_file())


class LiveDriftTest(unittest.TestCase):
    """The snapshot must not hide a later edit to a closed input."""

    def test_the_live_tree_differs_from_closure_only_as_declared(self) -> None:
        self.assertEqual(R.undeclared_drift(ROOT), [])

    def _sandbox(self, tmp: Path) -> Path:
        """A copy of the frozen paths in a throwaway git work tree that shares this
        repository's objects, so ``undeclared_drift`` can be run on edits."""
        root = tmp / "repo"
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        alternates = root / ".git/objects/info/alternates"
        common = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        alternates.write_text(str((ROOT / common / "objects").resolve()) + "\n")
        for _, sha, path in R._closure_entries(ROOT):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            source = ROOT / path
            if path in R.PROVENANCE_ONLY_REGENERATIONS:
                shutil.copyfile(source, target)
            else:
                target.write_bytes(
                    subprocess.run(
                        ["git", "-C", str(ROOT), "cat-file", "blob", sha],
                        capture_output=True,
                        check=True,
                    ).stdout
                )
        for path in R.POST_CLOSURE_FILES:
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, root / path)
        return root

    def test_the_sandbox_starts_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(R.undeclared_drift(self._sandbox(Path(tmp))), [])

    def test_an_undeclared_new_file_is_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._sandbox(Path(tmp))
            (root / "config/new_table.tsv").write_text("x\n")
            self.assertEqual(R.undeclared_drift(root), ["added: config/new_table.tsv"])

    def test_an_edit_to_a_closed_input_is_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._sandbox(Path(tmp))
            target = root / "config/protocols.yaml"
            target.write_text(target.read_text() + "\n")
            self.assertEqual(
                R.undeclared_drift(root), ["changed: config/protocols.yaml"]
            )

    def test_a_deleted_closed_input_is_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._sandbox(Path(tmp))
            (root / "docs/scrna/klf12_state_findings.json").unlink()
            self.assertEqual(
                R.undeclared_drift(root),
                ["missing or linked: docs/scrna/klf12_state_findings.json"],
            )

    def test_a_regeneration_may_change_only_its_named_fields(self) -> None:
        path = "docs/scrna/klf12_conditioning_settings.json"
        with tempfile.TemporaryDirectory() as tmp:
            root = self._sandbox(Path(tmp))
            payload = json.loads((root / path).read_text())
            payload["provenance"]["git_commit"] = "0" * 40
            (root / path).write_text(json.dumps(payload))
            self.assertEqual(R.undeclared_drift(root), [])
            payload["provenance"]["model_version"] = "something else"
            (root / path).write_text(json.dumps(payload))
            self.assertEqual(
                R.undeclared_drift(root), [f"changed beyond provenance: {path}"]
            )

    def test_a_declared_file_reached_through_a_link_is_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._sandbox(Path(tmp))
            path = "config/intervention_library.tsv"
            (root / path).unlink()
            (root / path).symlink_to(ROOT / path)
            self.assertEqual(R.undeclared_drift(root), [f"added: {path}"])


if __name__ == "__main__":
    unittest.main()
