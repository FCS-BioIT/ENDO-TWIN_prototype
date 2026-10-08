"""Unit contracts for the MaBoSS pathway-dynamics view model.

These tests exercise ``dt_adoc.reporting.dynamics`` only. They import no
plotting library, launch no MaBoSS runtime, and use a small synthetic pandas
frame wherever a "timeline frame" shape is needed. The rendering runtime
(matplotlib, GIF output, a real simulated timeline) is covered separately in
``tests/integration/test_dynamic_visualization_runtime.py``.
"""

from __future__ import annotations

import copy
import inspect
import sys
import tempfile
import unittest
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd
import yaml

from dt_adoc.model.catalog import load_tsv
from dt_adoc.model.runtime import resolve_model
from dt_adoc.reporting.dynamics import (
    BIOLOGICAL_FIELDS,
    VIEW_FULL,
    VIEW_OVERVIEW,
    build_network_view,
    classify_node,
    frame_values,
    load_visualization_config,
    probability_to_color,
    sample_frame_indices,
)

CORE = "adoc-core-v0.1.0"
LITERATURE = "adoc-literature-v0.2.0"
BANNED_SUBSTRINGS = (
    "concentration",
    "conc_",
    "_mm",
    "_um",
    "_nm",
    "ng_ml",
    "metabolite",
    "abundance",
)


class ColorRampTest(unittest.TestCase):
    """``probability_to_color`` is the only place a value becomes a pixel."""

    pale = "#000000"
    saturated = "#FFFFFF"

    def color(self, probability: float) -> str:
        return probability_to_color(
            probability, pale=self.pale, saturated=self.saturated
        )

    def channel(self, hex_color: str) -> int:
        return int(hex_color.lstrip("#")[0:2], 16)

    def test_zero_returns_exactly_pale(self) -> None:
        self.assertEqual(self.color(0.0), self.pale)

    def test_one_returns_exactly_saturated(self) -> None:
        self.assertEqual(self.color(1.0), self.saturated)

    def test_intermediate_probability_matches_neither_endpoint(self) -> None:
        mid = self.color(0.5)
        self.assertNotEqual(mid, self.pale)
        self.assertNotEqual(mid, self.saturated)

    def test_out_of_range_probabilities_are_clamped(self) -> None:
        self.assertEqual(self.color(-5.0), self.color(0.0))
        self.assertEqual(self.color(2.5), self.color(1.0))

    def test_increasing_probability_is_never_less_saturated(self) -> None:
        sequence = [0.0, 0.15, 0.4, 0.6, 0.85, 1.0]
        distances = [self.channel(self.color(p)) for p in sequence]
        for earlier, later in pairwise(distances):
            self.assertLessEqual(earlier, later)

    def test_non_finite_probability_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            probability_to_color(float("nan"), pale=self.pale, saturated=self.saturated)


class FixedPositionsTest(unittest.TestCase):
    """Node coordinates are fixed geometry, not a function of simulated time."""

    def test_rebuilding_the_same_view_yields_identical_positions(self) -> None:
        first = build_network_view(
            model_version=LITERATURE, view=VIEW_OVERVIEW, root=ROOT
        )
        second = build_network_view(
            model_version=LITERATURE, view=VIEW_OVERVIEW, root=ROOT
        )
        self.assertEqual(first.positions, second.positions)

    def test_the_api_takes_no_frame_or_time_argument(self) -> None:
        parameters = set(inspect.signature(build_network_view).parameters)
        frame_like = {"frame", "row", "row_index", "time", "timeline", "step"}
        self.assertEqual(parameters & frame_like, set())


class CompartmentAssignmentTest(unittest.TestCase):
    """Prefix wins for inputs/outputs; the model's own compartment otherwise."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.view = build_network_view(
            model_version=LITERATURE, view=VIEW_FULL, root=ROOT
        )

    def test_epithelial_stromal_input_output_prefixes(self) -> None:
        for node in self.view.nodes:
            if node.node_id.startswith("IN_"):
                self.assertEqual(node.compartment_class, "input", node.node_id)
            elif node.node_id.startswith("OUT_"):
                self.assertEqual(node.compartment_class, "output", node.node_id)
            elif node.node_id.startswith("E_"):
                self.assertEqual(node.compartment_class, "epithelial", node.node_id)
            elif node.node_id.startswith("S_"):
                self.assertEqual(node.compartment_class, "stromal", node.node_id)

    def test_ecm_and_interface_nodes_are_extracellular_at_centre(self) -> None:
        for node_id in ("X_SPP1_LUMEN_FREE", "X_MECHANICAL_PERMISSIVE_ECM"):
            node = self.view.node(node_id)
            self.assertEqual(node.compartment_class, "extracellular")
            self.assertEqual(node.region, "centre")

    def test_no_x_prefixed_node_is_classified_stromal(self) -> None:
        for node in self.view.nodes:
            if node.node_id.startswith("X_"):
                self.assertNotEqual(node.compartment_class, "stromal", node.node_id)

    def test_output_placement_ignores_its_node_dictionary_compartment(self) -> None:
        node = self.view.node("OUT_STROMAL_DECIDUALIZED")
        self.assertEqual(node.source_compartment, "stroma")
        self.assertEqual(node.compartment_class, "output")

    def test_core_model_agrees_on_the_same_prefix_rules(self) -> None:
        view = build_network_view(model_version=CORE, view=VIEW_FULL, root=ROOT)
        node = view.node("OUT_STROMAL_DECIDUALIZED")
        self.assertEqual(node.source_compartment, "stroma")
        self.assertEqual(node.compartment_class, "output")
        for node in view.nodes:
            if node.node_id.startswith("X_"):
                self.assertNotEqual(node.compartment_class, "stromal", node.node_id)


class ClassifyNodeUnitTest(unittest.TestCase):
    """Direct unit coverage of the classification function itself."""

    def setUp(self) -> None:
        self.config = load_visualization_config(ROOT)

    def test_prefix_beats_compartment_mapping(self) -> None:
        self.assertEqual(
            classify_node("OUT_STROMAL_DECIDUALIZED", "stroma", self.config),
            "output",
        )
        self.assertEqual(
            classify_node("IN_E2", "shared", self.config),
            "input",
        )

    def test_unmapped_compartment_raises(self) -> None:
        with self.assertRaises(ValueError):
            classify_node("Z_MYSTERY", "not_a_real_compartment", self.config)


class EdgeStylingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_visualization_config(ROOT)
        cls.view = build_network_view(
            model_version=LITERATURE, view=VIEW_FULL, root=ROOT
        )

    def test_at_least_one_activation_and_one_inhibition_edge_are_styled(self) -> None:
        activation = [e for e in self.view.edges if e.sign == "activation"]
        inhibition = [e for e in self.view.edges if e.sign == "inhibition"]
        self.assertTrue(activation)
        self.assertTrue(inhibition)
        for edge in activation:
            self.assertEqual(edge.color, self.config["edges"]["activation_color"])
        for edge in inhibition:
            self.assertEqual(edge.color, self.config["edges"]["inhibition_color"])

    def test_edge_signs_only_come_from_the_models_own_edge_evidence(self) -> None:
        spec = resolve_model(LITERATURE, ROOT)
        known_signs = {row["sign"] for row in load_tsv(spec.edge_evidence)}
        observed_signs = {edge.sign for edge in self.view.edges}
        self.assertTrue(observed_signs <= known_signs)

    def test_uncertain_confidence_edges_are_dashed_others_solid(self) -> None:
        uncertain = set(self.config["edges"]["uncertain_confidences"])
        for edge in self.view.edges:
            expected = "dashed" if edge.confidence in uncertain else "solid"
            self.assertEqual(edge.style, expected, edge)


class NodeUncertaintyTest(unittest.TestCase):
    def test_uncertain_flag_matches_the_configured_roles_and_confidences(self) -> None:
        config = load_visualization_config(ROOT)
        roles = set(config["uncertainty"]["roles"])
        confidences = set(config["uncertainty"]["confidences"])
        view = build_network_view(model_version=LITERATURE, view=VIEW_FULL, root=ROOT)
        for node in view.nodes:
            expected = node.model_role in roles or node.confidence in confidences
            self.assertEqual(node.uncertain, expected, node.node_id)


class FrameSamplingTest(unittest.TestCase):
    def test_final_index_is_always_included(self) -> None:
        indices = sample_frame_indices(37, 5)
        self.assertEqual(indices[-1], 36)

    def test_indices_are_strictly_increasing(self) -> None:
        indices = sample_frame_indices(50, 7)
        for earlier, later in pairwise(indices):
            self.assertLess(earlier, later)

    def test_stride_is_respected_between_interior_samples(self) -> None:
        indices = sample_frame_indices(21, 4)
        self.assertEqual(indices, [0, 4, 8, 12, 16, 20])

    def test_non_positive_stride_is_clamped_to_one(self) -> None:
        self.assertEqual(sample_frame_indices(5, 0), [0, 1, 2, 3, 4])
        self.assertEqual(sample_frame_indices(5, -3), [0, 1, 2, 3, 4])

    def test_zero_rows_yields_no_frames(self) -> None:
        self.assertEqual(sample_frame_indices(0, 3), [])


class FrameValuesTest(unittest.TestCase):
    def synthetic_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "global_time": [0.0, 1.0, 2.0],
                "E_PGR": [0.1, 0.5, 0.9],
                "S_DECIDUALIZED": [0.0, 0.2, 0.4],
            }
        )

    def test_reads_the_requested_row_exactly(self) -> None:
        frame = self.synthetic_frame()
        values = frame_values(frame, 1, ("E_PGR", "S_DECIDUALIZED"))
        self.assertEqual(values, {"E_PGR": 0.5, "S_DECIDUALIZED": 0.2})

    def test_silently_skips_node_ids_absent_from_the_frame(self) -> None:
        frame = self.synthetic_frame()
        values = frame_values(frame, 0, ("E_PGR", "NOT_A_REAL_NODE"))
        self.assertEqual(values, {"E_PGR": 0.1})
        self.assertNotIn("NOT_A_REAL_NODE", values)


class OptionalNodeAbsenceTest(unittest.TestCase):
    """The core model must build cleanly without the literature-only nodes."""

    optional_nodes = ("E_LIF", "E_HBEGF", "E_PODXL", "S_HAND2", "S_SPP1")

    def test_core_model_has_none_of_the_optional_nodes(self) -> None:
        core_dictionary = load_tsv(resolve_model(CORE, ROOT).node_dictionary)
        core_ids = {row["node_id"] for row in core_dictionary}
        for node_id in self.optional_nodes:
            self.assertNotIn(node_id, core_ids)

    def test_core_view_builds_and_its_panels_omit_the_optional_nodes(self) -> None:
        view = build_network_view(model_version=CORE, view=VIEW_FULL, root=ROOT)
        self.assertGreater(len(view.nodes), 0)
        panel_members = {member for panel in view.panels for member in panel.members}
        for node_id in self.optional_nodes:
            self.assertNotIn(node_id, panel_members)

    def test_literature_view_panels_include_the_nodes_it_actually_has(self) -> None:
        view = build_network_view(model_version=LITERATURE, view=VIEW_FULL, root=ROOT)
        panel_members = {member for panel in view.panels for member in panel.members}
        for node_id in self.optional_nodes:
            self.assertIn(node_id, panel_members)


class PanelObservableTest(unittest.TestCase):
    """Panels may only surface real node ids; nothing invented, nothing chemical."""

    def test_every_panel_member_is_a_real_node_of_that_model(self) -> None:
        for model_version in (CORE, LITERATURE):
            dictionary = load_tsv(resolve_model(model_version, ROOT).node_dictionary)
            known_ids = {row["node_id"] for row in dictionary}
            view = build_network_view(
                model_version=model_version, view=VIEW_FULL, root=ROOT
            )
            for panel in view.panels:
                for member in panel.members:
                    self.assertIn(member, known_ids, f"{model_version}: {member}")

    def test_no_metabolite_or_concentration_style_naming_leaks_in(self) -> None:
        config = load_visualization_config(ROOT)
        haystacks: list[str] = []
        for panel in config.get("panels", []):
            haystacks.extend(panel.get("members", []))
        haystacks.extend(config.get("short_labels", {}).values())
        for text in haystacks:
            lowered = str(text).lower()
            for banned in BANNED_SUBSTRINGS:
                self.assertNotIn(banned, lowered, f"{text!r} leaks {banned!r}")


class ConfigCarriesNoBiologyTest(unittest.TestCase):
    def test_top_level_keys_exclude_biological_fields_except_edges(self) -> None:
        raw = yaml.safe_load(
            (ROOT / "config" / "visualization.yaml").read_text(encoding="utf-8")
        )
        intruders = (set(raw) & BIOLOGICAL_FIELDS) - {"edges"}
        self.assertEqual(intruders, set())

    def test_loader_rejects_a_config_carrying_a_biological_key(self) -> None:
        raw = yaml.safe_load(
            (ROOT / "config" / "visualization.yaml").read_text(encoding="utf-8")
        )
        tainted = dict(raw)
        tainted["nodes"] = {"IN_E2": {"compartment": "shared"}}
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            config_dir = tmp_root / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "visualization.yaml").write_text(
                yaml.safe_dump(tainted), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                load_visualization_config(tmp_root)


class ConfigNodeCoverageTest(unittest.TestCase):
    def test_overview_nodes_exist_in_their_models_dictionary(self) -> None:
        config = load_visualization_config(ROOT)
        for model_version in (CORE, LITERATURE):
            dictionary = load_tsv(resolve_model(model_version, ROOT).node_dictionary)
            known_ids = {row["node_id"] for row in dictionary}
            requested = config["overview_nodes"].get(model_version, [])
            unknown = [node_id for node_id in requested if node_id not in known_ids]
            self.assertEqual(unknown, [], f"{model_version}: {unknown}")

    def test_an_unknown_overview_node_is_rejected(self) -> None:
        config = copy.deepcopy(load_visualization_config(ROOT))
        config["overview_nodes"][LITERATURE] = [
            *config["overview_nodes"][LITERATURE],
            "NOT_A_REAL_NODE",
        ]
        with self.assertRaises(ValueError):
            build_network_view(
                model_version=LITERATURE,
                view=VIEW_OVERVIEW,
                root=ROOT,
                config=config,
            )


class NoForeignSimulatorReferenceTest(unittest.TestCase):
    """Guard against a spatial/ABM simulator quietly entering the reporting code.

    ``network_figure.py`` and ``render_dynamics.py`` legitimately mention
    "PhysiBoSS" -- but only to disclaim it ("not a PhysiBoSS ... output").
    That negated mention is intentional documentation, not a dependency, so
    this test allows a banned term to appear solely when the word "not"
    appears somewhere earlier in the same disclaiming clause; any other
    occurrence (an import, a call, an unguarded mention) still fails the
    test. The other banned terms
    (implant_twin, abm, blastoid, trophoblast, chip_geometry, diffusion) are
    not expected to appear at all, negated or otherwise.
    """

    files = (
        Path("src/dt_adoc/reporting/dynamics.py"),
        Path("src/dt_adoc/reporting/network_figure.py"),
        Path("src/dt_adoc/reporting/render_dynamics.py"),
    )
    banned_terms = (
        "physiboss",
        "implant_twin",
        "abm",
        "blastoid",
        "trophoblast",
        "chip_geometry",
        "diffusion",
    )

    def test_banned_terms_are_absent_or_strictly_negated(self) -> None:
        for relative in self.files:
            text = (ROOT / relative).read_text(encoding="utf-8").lower()
            for term in self.banned_terms:
                start = 0
                while True:
                    index = text.find(term, start)
                    if index == -1:
                        break
                    window = text[max(0, index - 200) : index]
                    self.assertIn(
                        "not",
                        window,
                        f"{relative}: unguarded {term!r} near {window!r}",
                    )
                    start = index + len(term)


class BothModelsBuildBothViewsTest(unittest.TestCase):
    def test_every_model_and_view_combination_builds_with_content(self) -> None:
        for model_version in (CORE, LITERATURE):
            for view_name in (VIEW_OVERVIEW, VIEW_FULL):
                view = build_network_view(
                    model_version=model_version, view=view_name, root=ROOT
                )
                self.assertGreater(len(view.nodes), 0, f"{model_version}/{view_name}")
                self.assertGreater(len(view.edges), 0, f"{model_version}/{view_name}")


if __name__ == "__main__":
    unittest.main()
