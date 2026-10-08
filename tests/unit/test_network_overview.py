"""The principal network figure is derived from the executable model, not drawn.

Guards that the committed overview and its sidecar still describe the committed
``network.bnd``: the counts, the alias rosters, the measurement tiers and the
executable-identity statement are recomputed here, and a fresh render must
reproduce the committed PNG byte-for-byte.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import resolve_model
from dt_adoc.reporting.network_overview import (
    TIER_ACTIVE,
    TIER_ASSAYED,
    TIER_COMPOSITE,
    TIER_ENDPOINT,
    measurement_tiers,
    overview_positions,
    render_network_overview_artifact,
)
from dt_adoc.reporting.structure import load_structure, structural_summary

MODEL = "adoc-literature-superset-v0.5.0"
PARENT = "adoc-literature-superset-v0.4.0"
FIGURE = ROOT / "docs/assets/adoc_network_overview_v0.5.0.png"
SIDECAR = ROOT / "docs/assets/adoc_network_overview_v0.5.0_metadata.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NetworkOverviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_structure(MODEL, ROOT)
        cls.meta = json.loads(SIDECAR.read_text(encoding="utf-8"))

    def test_sidecar_counts_recompute_from_network_bnd(self) -> None:
        summary = structural_summary(self.facts)
        for key, value in summary.items():
            self.assertEqual(self.meta["summary"][key], value, key)
        self.assertEqual(
            self.meta["alias_classes"],
            sorted(sorted(m) for m in self.facts.alias_classes),
        )
        self.assertEqual(self.meta["unread_inputs"], sorted(self.facts.unread_inputs))
        self.assertEqual(
            self.meta["summary"]["absorbed_or_never_binding_dependencies"],
            len(
                set(self.facts.absorbed_edges)
                | set(self.facts.never_binding_inhibitions)
            ),
        )

    def test_every_node_and_edge_is_placed(self) -> None:
        positions, _extents = overview_positions(self.facts)
        self.assertEqual(set(positions), set(self.facts.node_ids))
        self.assertEqual(len(self.facts.edges), self.meta["summary"]["dependencies"])

    def test_identity_statement_is_computed_not_asserted(self) -> None:
        same = (
            resolve_model(MODEL, ROOT).network_bnd.read_bytes()
            == resolve_model(PARENT, ROOT).network_bnd.read_bytes()
        )
        identity = self.meta["executable_identity"]
        self.assertEqual(identity["parent_model_version"], PARENT)
        self.assertEqual(identity["network_bnd_byte_identical_to_parent"], same)

    def test_measurement_tiers_are_derived_from_the_mapping_tables(self) -> None:
        tiers = measurement_tiers(self.facts, ROOT)
        self.assertEqual(
            sorted(n for n, t in tiers.items() if t == TIER_ACTIVE),
            sorted(self.facts.measured),
        )
        self.assertEqual(tiers.get("OUT_STABLE_ADHESION"), TIER_ENDPOINT)
        # PRL is assayed by ADOC but its mapping is provisional; it must never be
        # drawn as a measured node of the same standing as PAEP or IGFBP-1.
        self.assertEqual(tiers.get("S_PRL"), TIER_ASSAYED)
        # The composite outputs have reported mappings with ZERO source rows;
        # they must not carry the marker of an assayed analyte.
        for node in ("OUT_EPITHELIAL_RECEPTIVE", "OUT_STROMAL_DECIDUALIZED"):
            self.assertEqual(tiers.get(node), TIER_COMPOSITE, node)
        self.assertEqual(
            self.meta["summary"]["measurement_tiers"],
            {
                t: sorted(n for n, v in tiers.items() if v == t)
                for t in (TIER_ACTIVE, TIER_ENDPOINT, TIER_ASSAYED, TIER_COMPOSITE)
            },
        )

    def test_committed_figure_is_the_one_the_sidecar_pins(self) -> None:
        self.assertEqual(_sha(FIGURE), self.meta["figure"]["sha256"])
        for relative, digest in self.meta["generator_files"].items():
            self.assertEqual(_sha(ROOT / relative), digest, relative)
        for name, record in self.meta["inputs"].items():
            self.assertEqual(_sha(ROOT / record["path"]), record["sha256"], name)

    def test_a_fresh_render_reproduces_the_committed_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = render_network_overview_artifact(
                root=ROOT, output_path=Path(tmp) / "overview.png"
            )
            self.assertEqual(metadata["figure"]["sha256"], _sha(FIGURE))


CURRENT_MODEL = "adoc-literature-superset-v0.6.0"
CURRENT_FIGURE = ROOT / "docs/assets/adoc_network_overview_v0.6.0.png"
CURRENT_SIDECAR = ROOT / "docs/assets/adoc_network_overview_v0.6.0_metadata.json"
STRUCTURE_COUNTS = ROOT / "docs/intervention_layer_stage3/structure_counts.json"
RETIRED_MARKERS = ("IN_MIFEPRISTONE", "IN_ANTI_SPP1", "IN_HAND2_LOSS")


class CurrentNetworkOverviewTest(unittest.TestCase):
    """The README's current network figure: the markerless v0.6.0 render.

    Rendered by ``pixi run render-network`` with no parent-identity statement,
    since v0.6.0 is a real increment over v0.5.2 rather than a byte copy.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_structure(CURRENT_MODEL, ROOT)
        cls.meta = json.loads(CURRENT_SIDECAR.read_text(encoding="utf-8"))
        cls.counts = json.loads(STRUCTURE_COUNTS.read_text(encoding="utf-8"))[
            "versions"
        ][CURRENT_MODEL]

    def test_sidecar_counts_recompute_from_network_bnd(self) -> None:
        self.assertEqual(self.meta["model_version"], CURRENT_MODEL)
        self.assertIsNone(self.meta["executable_identity"])
        summary = structural_summary(self.facts)
        for key, value in summary.items():
            self.assertEqual(self.meta["summary"][key], value, key)
        self.assertEqual(
            self.meta["alias_classes"],
            sorted(sorted(m) for m in self.facts.alias_classes),
        )
        self.assertEqual(
            self.meta["summary"]["absorbed_or_never_binding_dependencies"],
            len(
                set(self.facts.absorbed_edges)
                | set(self.facts.never_binding_inhibitions)
            ),
        )

    def test_sidecar_agrees_with_the_stage3_structure_counts(self) -> None:
        summary = self.meta["summary"]
        counts = self.counts
        self.assertEqual(summary["nodes"], counts["nodes"])
        self.assertEqual(summary["dependencies"], counts["dependencies"])
        self.assertEqual(summary["free_variables"], counts["free_variables"])
        self.assertEqual(summary["enumerated_states"], counts["enumerated_assignments"])
        self.assertEqual(
            summary["distinct_functions"], counts["distinct_composed_functions"]
        )
        self.assertEqual(summary["alias_classes"], counts["alias_class_count"])
        self.assertEqual(self.meta["alias_classes"], sorted(counts["alias_classes"]))
        self.assertEqual(
            self.meta["phenotype_inert_nodes"], counts["phenotype_inert_nodes"]
        )
        self.assertEqual(self.meta["unread_inputs"], counts["unread_inputs"])

    def test_no_retired_intervention_marker_appears(self) -> None:
        text = CURRENT_SIDECAR.read_text(encoding="utf-8")
        for marker in RETIRED_MARKERS:
            self.assertNotIn(marker, self.facts.node_ids, marker)
            self.assertNotIn(marker, text, marker)

    def test_committed_figure_is_the_one_the_sidecar_pins(self) -> None:
        self.assertEqual(_sha(CURRENT_FIGURE), self.meta["figure"]["sha256"])
        self.assertNotIn("dirty", self.meta["source_commit"])
        for relative, digest in self.meta["generator_files"].items():
            self.assertEqual(_sha(ROOT / relative), digest, relative)
        for name, record in self.meta["inputs"].items():
            self.assertEqual(_sha(ROOT / record["path"]), record["sha256"], name)
        self.assertEqual(
            self.meta["inputs"]["network_bnd"]["path"],
            f"models/superset/{CURRENT_MODEL}/network.bnd",
        )

    def test_a_fresh_render_reproduces_the_committed_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = render_network_overview_artifact(
                CURRENT_MODEL,
                None,
                root=ROOT,
                output_path=Path(tmp) / "overview.png",
            )
            self.assertEqual(metadata["figure"]["sha256"], _sha(CURRENT_FIGURE))


if __name__ == "__main__":
    unittest.main()
