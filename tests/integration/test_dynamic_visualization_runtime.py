"""Runtime contracts for the MaBoSS pathway-dynamics animation.

Bounded on purpose: a small trajectory count and a large frame stride over the
default protocol lineage. The point is to exercise the real render pipeline
(a real MaBoSS timeline, real matplotlib rendering, a real GIF on disk) at the
smallest scale that still proves the contract -- not to reproduce the
README-quality animation. Every artifact is written into a throwaway
directory that is removed at the end of the run.

The matching pure-logic assertions (colour mapping, compartment placement,
frame sampling, etc.), which need no MaBoSS runtime, live in
``tests/unit/test_dynamic_visualization.py``.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PIL import Image

from dt_adoc.reporting.dynamics import VIEW_OVERVIEW, build_network_view, frame_values
from dt_adoc.reporting.network_figure import (
    CLAIM_FOOTER,
    RenderSettings,
    render_animation,
)
from dt_adoc.reporting.render_dynamics import RenderRequest, render_pathway_dynamics
from dt_adoc.simulation.timeline import build_sequential_timeline
from tests.unit.checkout_isolation import working_tree_copy

LITERATURE = "adoc-literature-v0.2.0"
CORE = "adoc-core-v0.1.0"
TRAJECTORY_COUNT = 150
FRAME_STRIDE = 12
SEED = 1


class RenderAnimationRuntimeTest(unittest.TestCase):
    """One bounded real render, reused by every assertion in this class."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.tmp_path = Path(cls.tmp_dir.name)
        cls.timeline = build_sequential_timeline(
            model_version=LITERATURE,
            root=ROOT,
            seed=SEED,
            trajectory_count=TRAJECTORY_COUNT,
        )
        # Snapshot before rendering so a later test can prove render_animation
        # never mutates the simulated trajectory it draws from.
        cls.frame_before_render = cls.timeline.frame.copy()
        cls.view = build_network_view(
            model_version=LITERATURE, view=VIEW_OVERVIEW, root=ROOT
        )
        cls.gif_path = cls.tmp_path / "pathway_dynamics.gif"
        cls.preview_path = cls.tmp_path / "pathway_dynamics_preview.png"
        cls.settings = RenderSettings(frame_stride=FRAME_STRIDE)
        cls.animation_metadata = render_animation(
            view=cls.view,
            timeline=cls.timeline,
            output_path=cls.gif_path,
            settings=cls.settings,
            preview_path=cls.preview_path,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp_dir.cleanup()

    def test_gif_file_exists_and_is_non_empty(self) -> None:
        self.assertTrue(self.gif_path.exists())
        self.assertGreater(self.gif_path.stat().st_size, 0)

    def test_gif_has_more_than_one_frame_with_positive_dimensions(self) -> None:
        with Image.open(self.gif_path) as image:
            self.assertGreater(image.n_frames, 1)
            self.assertGreater(image.width, 0)
            self.assertGreater(image.height, 0)

    def test_metadata_frame_count_matches_the_actual_gif(self) -> None:
        with Image.open(self.gif_path) as image:
            actual_frame_count = image.n_frames
        self.assertEqual(self.animation_metadata["frame_count"], actual_frame_count)

    def test_preview_png_exists_and_matches_the_gif_frame_size(self) -> None:
        self.assertTrue(self.preview_path.exists())
        with (
            Image.open(self.gif_path) as gif_image,
            Image.open(self.preview_path) as preview_image,
        ):
            self.assertEqual(preview_image.size, gif_image.size)

    def test_displayed_values_equal_the_raw_timeline_values(self) -> None:
        sampled_index = self.animation_metadata["frame_row_indices"][-1]
        displayed = frame_values(self.timeline.frame, sampled_index, self.view.node_ids)
        raw_row = self.timeline.frame.iloc[sampled_index]
        self.assertTrue(displayed)
        for node_id, value in displayed.items():
            self.assertEqual(value, float(raw_row[node_id]), node_id)

    def test_rendering_did_not_mutate_the_simulation_results(self) -> None:
        self.assertTrue(self.frame_before_render.equals(self.timeline.frame))


class CrossModelRenderRuntimeTest(unittest.TestCase):
    """Both registered models must render a GIF, not just the literature one."""

    def render_minimal_gif(self, model_version: str, tmp_path: Path) -> Path:
        timeline = build_sequential_timeline(
            model_version=model_version,
            root=ROOT,
            seed=SEED,
            trajectory_count=TRAJECTORY_COUNT,
        )
        view = build_network_view(
            model_version=model_version, view=VIEW_OVERVIEW, root=ROOT
        )
        gif_path = tmp_path / f"{model_version}.gif"
        # A stride far larger than the row count still yields the mandatory
        # first-and-last pair of frames (see sample_frame_indices), which is
        # all this test needs to prove the model renders at all.
        render_animation(
            view=view,
            timeline=timeline,
            output_path=gif_path,
            settings=RenderSettings(frame_stride=100_000),
        )
        return gif_path

    def test_both_models_render_a_gif_successfully(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for model_version in (CORE, LITERATURE):
                gif_path = self.render_minimal_gif(model_version, tmp_path)
                self.assertTrue(gif_path.exists(), model_version)
                with Image.open(gif_path) as image:
                    self.assertGreaterEqual(image.n_frames, 2, model_version)


class RenderPathwayDynamicsMetadataTest(unittest.TestCase):
    """``render_pathway_dynamics`` must record full reproducibility metadata.

    ``render_pathway_dynamics`` always writes its raw trajectories and full
    metadata under ``output/visualization/<model>/<run_id>`` relative to
    ``root`` -- that location is not configurable via ``RenderRequest`` -- and
    ``describe_file`` records every path ``relative_to(root)``. So the render
    runs with a disposable copy of the working tree as its root, never the
    checkout, and ``output``/``preview``/``metadata`` point inside that copy's
    per-run directory. The copy is removed in ``tearDownClass``.
    """

    run_id = "test-run"

    @classmethod
    def setUpClass(cls) -> None:
        cls._scratch = tempfile.TemporaryDirectory()
        work = working_tree_copy(Path(cls._scratch.name))
        cls.run_dir = work / "output" / "visualization" / LITERATURE / cls.run_id
        request = RenderRequest(
            model_version=LITERATURE,
            seed=SEED,
            trajectory_count=TRAJECTORY_COUNT,
            frame_stride=FRAME_STRIDE,
            run_id=cls.run_id,
            output=cls.run_dir.relative_to(work) / "readme.gif",
            preview=cls.run_dir.relative_to(work) / "preview.png",
            metadata=cls.run_dir.relative_to(work) / "metadata.json",
            write_full_resolution=False,
        )
        cls.metadata = render_pathway_dynamics(request, root=work)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._scratch.cleanup()

    def test_metadata_records_the_model_identity(self) -> None:
        self.assertEqual(self.metadata["model"]["model_version"], LITERATURE)
        self.assertTrue(self.metadata["model"]["model_id"])

    def test_metadata_records_seed_and_trajectory_count(self) -> None:
        self.assertEqual(self.metadata["simulation"]["seed"], SEED)
        self.assertEqual(
            self.metadata["simulation"]["trajectory_count"], TRAJECTORY_COUNT
        )

    def test_metadata_records_the_protocol_sequence(self) -> None:
        sequence = self.metadata["protocol"]["sequence"]
        self.assertTrue(sequence)
        phase_protocol_ids = [
            phase["protocol_id"] for phase in self.metadata["protocol"]["phases"]
        ]
        self.assertEqual(set(sequence), set(phase_protocol_ids))

    def test_metadata_records_a_non_empty_trajectory_sources_list_with_sha256(
        self,
    ) -> None:
        sources = self.metadata["trajectory_sources"]
        self.assertTrue(sources)
        for source in sources:
            self.assertIn("sha256", source)
            self.assertTrue(source["sha256"])


class ClaimFooterDisclaimerTest(unittest.TestCase):
    """The footer burned into every frame must carry its disclaimers."""

    def test_footer_states_the_value_and_time_semantics(self) -> None:
        self.assertIn("P(node = ON)", CLAIM_FOOTER)
        self.assertIn("relative time", CLAIM_FOOTER)

    def test_footer_disclaims_causal_and_spatial_readings(self) -> None:
        self.assertIn("not causal flux", CLAIM_FOOTER)
        self.assertIn("not spatial", CLAIM_FOOTER)


if __name__ == "__main__":
    unittest.main()
