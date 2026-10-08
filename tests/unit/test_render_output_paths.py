"""Path-resolution contracts for the pathway-dynamics renderer.

Pure path logic: nothing here runs MaBoSS, renders a frame, or writes to
docs/assets. It exists because the previous behaviour resolved ``--preview`` and
``--metadata`` independently of ``--output``, so rendering any other model with
only ``--output`` set silently overwrote the committed
``adoc-literature-v0.2.0`` preview PNG and metadata JSON that README.md
references.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting.render_dynamics import (
    DEFAULT_METADATA,
    DEFAULT_PREVIEW_PNG,
    DEFAULT_README_GIF,
    README_ARTIFACT_OWNER,
    RenderRequest,
    resolve_output_paths,
)

SUPERSET = "adoc-literature-superset-v0.3.0"
SCRATCH = Path("output/visualization/scratch")


class DerivedPathTest(unittest.TestCase):
    def test_the_committed_output_derives_the_committed_siblings(self) -> None:
        """This is what keeps `pixi run render-dynamics-demo`, which passes only
        --output, producing exactly the three committed filenames."""
        paths = resolve_output_paths(
            RenderRequest(model_version=README_ARTIFACT_OWNER), root=ROOT
        )
        self.assertEqual(paths.gif, DEFAULT_README_GIF)
        self.assertEqual(paths.preview, DEFAULT_PREVIEW_PNG)
        self.assertEqual(paths.metadata, DEFAULT_METADATA)

    def test_a_new_output_derives_new_siblings_not_the_committed_ones(self) -> None:
        paths = resolve_output_paths(
            RenderRequest(model_version=SUPERSET, output=SCRATCH / "superset.gif"),
            root=ROOT,
        )
        self.assertEqual(paths.preview, SCRATCH / "superset_preview.png")
        self.assertEqual(paths.metadata, SCRATCH / "superset_metadata.json")
        self.assertNotIn(DEFAULT_PREVIEW_PNG, (paths.preview, paths.metadata))
        self.assertNotIn(DEFAULT_METADATA, (paths.preview, paths.metadata))

    def test_explicit_paths_still_win_over_derivation(self) -> None:
        paths = resolve_output_paths(
            RenderRequest(
                model_version=SUPERSET,
                output=SCRATCH / "a.gif",
                preview=SCRATCH / "b.png",
                metadata=SCRATCH / "c.json",
            ),
            root=ROOT,
        )
        self.assertEqual(paths.preview, SCRATCH / "b.png")
        self.assertEqual(paths.metadata, SCRATCH / "c.json")


class CommittedArtifactProtectionTest(unittest.TestCase):
    def test_a_foreign_model_may_not_write_the_committed_gif(self) -> None:
        with self.assertRaises(ValueError) as caught:
            resolve_output_paths(
                RenderRequest(model_version=SUPERSET, output=DEFAULT_README_GIF),
                root=ROOT,
            )
        self.assertIn(README_ARTIFACT_OWNER, str(caught.exception))

    def test_a_foreign_model_may_not_name_the_committed_preview(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_paths(
                RenderRequest(
                    model_version=SUPERSET,
                    output=SCRATCH / "superset.gif",
                    preview=DEFAULT_PREVIEW_PNG,
                ),
                root=ROOT,
            )

    def test_a_foreign_model_may_not_name_the_committed_metadata(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_paths(
                RenderRequest(
                    model_version=SUPERSET,
                    output=SCRATCH / "superset.gif",
                    metadata=DEFAULT_METADATA,
                ),
                root=ROOT,
            )

    def test_the_owning_model_may_still_rewrite_them(self) -> None:
        paths = resolve_output_paths(
            RenderRequest(
                model_version=README_ARTIFACT_OWNER, output=DEFAULT_README_GIF
            ),
            root=ROOT,
        )
        self.assertEqual(paths.gif, DEFAULT_README_GIF)


class OutsideRootTest(unittest.TestCase):
    def test_a_destination_outside_the_repository_is_refused_up_front(self) -> None:
        """Previously this failed only after the whole animation had rendered."""
        with self.assertRaises(ValueError):
            resolve_output_paths(
                RenderRequest(model_version=SUPERSET, output=Path("/tmp/nope.gif")),
                root=ROOT,
            )

    def test_a_trajectory_dir_outside_the_repository_is_refused_up_front(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_paths(
                RenderRequest(
                    model_version=SUPERSET,
                    output=Path("output/x.gif"),
                    trajectory_dir=Path("/tmp/nope"),
                ),
                root=ROOT,
            )

    def test_no_trajectory_dir_keeps_the_run_directory(self) -> None:
        paths = resolve_output_paths(
            RenderRequest(model_version=SUPERSET, output=Path("output/x.gif")),
            root=ROOT,
        )
        self.assertIsNone(paths.trajectories)


if __name__ == "__main__":
    unittest.main()
