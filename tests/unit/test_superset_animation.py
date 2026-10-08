"""Contracts for the superset README animation and the archived v0.2 assets.

The README's primary figure changed on 2026-07-29 from a horizon-independent
structural PNG to a horizon-DEPENDENT simulated animation of
`adoc-literature-superset-v0.3.0`. That trade is deliberate and is argued in
README, but it means the figure now carries claims that need guarding:

* the declared readout horizon reads the adhesion endpoints ~4000x before their
  fixed point, so the animation must run converged AND mark the declared
  duration in-frame -- neither alone is honest;
* `S_IGFBP1` and `S_PRL` share one Boolean rule with no declared rate, so the
  analyte panel shows two curves that coincide *by construction*. A panel that
  did not say so would present an assumption as a result;
* the archived v0.2 assets are historical evidence and must never be overwritten.

`test_render_output_paths.py` protects the v0.2 names only along the
`resolve_output_paths` code path. This module pins the bytes, which also catches
a stray `cp` or `savefig`.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

ASSETS = ROOT / "docs" / "assets"
SUPERSET_STEM = "adoc_superset_pathway_dynamics_v0.6.0"
SUPERSET_MODEL = "adoc-literature-superset-v0.6.0"
#: Retired v0.5.2 marker inputs; v0.6.0 times interventions in the protocol layer.
RETIRED_MARKERS = ("IN_MIFEPRISTONE", "IN_ANTI_SPP1", "IN_HAND2_LOSS")
SUPERSET_GIF = ASSETS / f"{SUPERSET_STEM}.gif"
SUPERSET_PREVIEW = ASSETS / f"{SUPERSET_STEM}_preview.png"
SUPERSET_METADATA = ASSETS / f"{SUPERSET_STEM}_metadata.json"

#: Byte-exact digests of the archived v0.2.0 animation. The model it depicts is
#: immutable, so these can never legitimately change.
ARCHIVED_V0_2 = {
    "adoc_maboss_pathway_dynamics.gif": (
        3594831,
        "2ebc896d43bdcda0",
    ),
    "adoc_maboss_pathway_dynamics_preview.png": (
        928188,
        "63037a0037eb6814",
    ),
    "adoc_maboss_pathway_dynamics_metadata.json": (
        10188,
        "483be5c9d66ac890",
    ),
}


#: Byte-exact digests of the v0.3.0 superset assets. v0.3.0 became an immutable
#: parent when v0.4.0 was minted, so these can no longer legitimately change
#: either -- pinned the same way the v0.2.0 set is.
ARCHIVED_V0_3 = {
    "adoc_superset_pathway_dynamics_v0.3.0.gif": (
        1778056,
        "84a184432d0d09ff",
    ),
    "adoc_superset_pathway_dynamics_v0.3.0_preview.png": (
        1051791,
        "c54c9b0bd56cf568",
    ),
    "adoc_superset_pathway_dynamics_v0.3.0_metadata.json": (
        9141,
        "e63e3566842c2a2c",
    ),
    "adoc_superset_structure_v0.3.0.png": (
        412230,
        "17fbccc825ab80f2",
    ),
    "adoc_superset_structure_v0.3.0_metadata.json": (
        3526,
        "eae8909d21e5c08d",
    ),
}


#: Byte-exact digests of the v0.4.0 superset animation. It was the README figure
#: until v0.6.0 replaced it and is kept as a reproducibility artifact.
ARCHIVED_V0_4 = {
    "adoc_superset_pathway_dynamics_v0.4.0.gif": (
        1779050,
        "1cce23bb57d7bb4a",
    ),
    "adoc_superset_pathway_dynamics_v0.4.0_preview.png": (
        1059619,
        "018e085f7e093c10",
    ),
    "adoc_superset_pathway_dynamics_v0.4.0_metadata.json": (
        9141,
        "5406adf7a0b2b759",
    ),
}


def _digest(path: Path) -> tuple[int, str]:
    payload = path.read_bytes()
    return len(payload), hashlib.sha256(payload).hexdigest()[:16]


class ArchivedAnimationIsImmutableTest(unittest.TestCase):
    def test_the_archived_v0_2_assets_are_byte_unchanged(self) -> None:
        for name, (size, prefix) in ARCHIVED_V0_2.items():
            path = ASSETS / name
            self.assertTrue(path.is_file(), name)
            observed_size, observed_prefix = _digest(path)
            self.assertEqual(observed_size, size, f"{name} size changed")
            self.assertEqual(observed_prefix, prefix, f"{name} content changed")

    def test_the_superset_render_does_not_target_the_archived_names(self) -> None:
        from dt_adoc.reporting.render_dynamics import README_ARTIFACTS

        archived = {ASSETS / name for name in ARCHIVED_V0_2}
        self.assertTrue(archived <= {ROOT / p for p in README_ARTIFACTS})
        self.assertNotIn(SUPERSET_GIF, {ROOT / p for p in README_ARTIFACTS})

    def test_the_demo_task_still_owns_the_archive(self) -> None:
        """`render-dynamics-demo` stays pointed at v0.2.0 and is the only writer
        of the archived paths.
        """
        pixi = (ROOT / "pixi.toml").read_text(encoding="utf-8")
        self.assertIn("render-dynamics-demo", pixi)
        self.assertIn("adoc_maboss_pathway_dynamics.gif", pixi)
        self.assertIn("ARCHIVED v0.2.0", pixi)


class SupersetAnimationAssetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = json.loads(SUPERSET_METADATA.read_text(encoding="utf-8"))

    def test_the_three_assets_exist(self) -> None:
        for path in (SUPERSET_GIF, SUPERSET_PREVIEW, SUPERSET_METADATA):
            self.assertTrue(path.is_file(), str(path))

    def test_the_gif_is_readme_sized(self) -> None:
        size = SUPERSET_GIF.stat().st_size
        self.assertLess(size, 4_000_000, "too large for a README figure")
        self.assertGreater(size, 200_000, "suspiciously small for 68 frames")

    def test_the_metadata_artifact_follows_the_output_stem(self) -> None:
        """Regression: the artifact name used to be a hardcoded literal, so the
        superset sidecar declared itself to be the v0.2 artifact.
        """
        self.assertEqual(self.metadata["artifact"], SUPERSET_STEM)
        self.assertNotEqual(self.metadata["artifact"], "adoc_maboss_pathway_dynamics")

    def test_the_metadata_records_the_model_and_the_commit(self) -> None:
        self.assertEqual(self.metadata["model"]["model_version"], SUPERSET_MODEL)
        self.assertEqual(
            self.metadata["model"]["network_bnd"]["path"],
            f"models/superset/{SUPERSET_MODEL}/network.bnd",
        )
        commit = self.metadata["source_commit"]
        self.assertNotEqual(commit, "")
        self.assertNotEqual(commit, "unavailable")

    def test_the_metadata_declares_a_converged_horizon(self) -> None:
        """An unlabelled horizon is actively misleading in this repository."""
        self.assertEqual(self.metadata["horizon_class"], "converged")
        self.assertEqual(float(self.metadata["phase_horizon"]), 25.0)
        declared = self.metadata["declared_phase_durations"]
        self.assertTrue(declared)
        for label, duration in declared.items():
            self.assertLess(
                float(duration),
                float(self.metadata["phase_horizon"]),
                f"{label}: the declared duration must be shorter than the "
                "converged horizon, or the in-frame marker is meaningless",
            )

    def test_the_claim_boundary_names_the_horizon_semantics(self) -> None:
        boundary = self.metadata["claim_boundary"]
        for token in ("dimensionless", "never a day", "fixed point"):
            self.assertIn(token, boundary)

    def test_every_declared_source_resolves_with_its_hash(self) -> None:
        """The figure's lineage must be checkable from the repository alone:
        the trajectory tables, the condition cfgs and the merged cfgs MaBoSS
        executed are all committed and match the recorded digests.
        """
        refs = list(self.metadata["trajectory_sources"])
        for phase in self.metadata["protocol"]["phases"]:
            execution = phase["execution"]
            refs += [execution["condition_cfg"], execution["executed_cfg"]]
            self.assertEqual(execution["max_time"], 25.0)
            self.assertEqual(execution["time_tick"], 0.1)
            self.assertEqual(
                execution["executed_network"]["source_network"],
                self.metadata["model"]["network_bnd"],
            )
        self.assertEqual(len(refs), 12)
        for ref in refs:
            path = ROOT / ref["path"]
            self.assertTrue(path.is_file(), ref["path"])
            self.assertFalse(ref["path"].startswith("output/"), ref["path"])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, ref["sha256"], ref["path"])

    def test_the_runtime_and_commit_are_recorded(self) -> None:
        self.assertFalse(self.metadata["source_commit"].endswith("-dirty"))
        runtime = self.metadata["simulation"]["runtime"]
        for package in ("python", "maboss", "matplotlib"):
            self.assertNotEqual(runtime.get(package, "unavailable"), "unavailable")
        request = self.metadata["render_request"]
        self.assertEqual(request["model_version"], SUPERSET_MODEL)
        self.assertEqual(request["trajectory_count"], 20000)

    def test_the_animation_covers_the_whole_superset(self) -> None:
        visualization = self.metadata["visualization"]
        self.assertEqual(visualization["view"], "full")
        self.assertEqual(visualization["node_count"], 56)  # v0.5.2 minus 3 markers
        self.assertEqual(visualization["edge_count"], 89)
        self.assertIn("secreted_analytes", visualization["panels"])

    def test_the_protocols_come_from_the_markerless_file(self) -> None:
        protocol = self.metadata["protocol"]
        self.assertEqual(
            protocol["definition"]["path"], "config/protocols_markerless.yaml"
        )
        self.assertEqual(
            protocol["sequence"],
            [
                "basal_maternal",
                "e2_primed_maternal",
                "hormone_treated_maternal",
                "adhesion_challenge_hormone_treated",
            ],
        )

    def test_no_retired_marker_node_is_rendered_or_simulated(self) -> None:
        for phase in self.metadata["protocol"]["phases"]:
            for marker in RETIRED_MARKERS:
                self.assertNotIn(marker, phase["input_states"], phase["step_id"])
        text = SUPERSET_METADATA.read_text(encoding="utf-8")
        for marker in RETIRED_MARKERS:
            self.assertNotIn(marker, text)
        for stale in ("v0.4.0", "v0.5.0", "v0.5.1", "v0.5.2"):
            self.assertNotIn(stale, text)


class AnalytePanelHonestyTest(unittest.TestCase):
    """The panel the user asked for, and the caveat that keeps it honest."""

    @classmethod
    def setUpClass(cls) -> None:
        from dt_adoc.reporting.dynamics import build_network_view

        cls.view = build_network_view(
            model_version="adoc-literature-superset-v0.3.0", view="full", root=ROOT
        )
        cls.panels = {panel.key: panel for panel in cls.view.panels}

    def test_the_analyte_panel_holds_exactly_the_three_adoc_analytes(self) -> None:
        panel = self.panels["secreted_analytes"]
        self.assertEqual(set(panel.members), {"E_PAEP", "S_IGFBP1", "S_PRL"})

    def test_no_node_is_plotted_in_two_panels(self) -> None:
        seen: dict[str, list[str]] = {}
        for panel in self.view.panels:
            for member in panel.members:
                seen.setdefault(member, []).append(panel.key)
        duplicated = {k: v for k, v in seen.items() if len(v) > 1}
        self.assertEqual(duplicated, {}, duplicated)

    def test_every_measured_node_is_in_the_analyte_panel(self) -> None:
        from dt_adoc.reporting.structure import load_structure

        measured = set(load_structure("adoc-literature-superset-v0.3.0", ROOT).measured)
        self.assertEqual(measured, {"E_PAEP", "S_IGFBP1"})
        self.assertTrue(measured <= set(self.panels["secreted_analytes"].members))

    def test_no_panel_titled_readouts_contains_an_unmeasured_node(self) -> None:
        """The archived v0.2 GIF has panels titled "readouts" holding nodes with
        no ADOC measurement -- a defect README confesses. The superset animation
        must not inherit it.
        """
        from dt_adoc.reporting.structure import load_structure

        measured = set(load_structure("adoc-literature-superset-v0.3.0", ROOT).measured)
        for panel in self.view.panels:
            if "readout" not in panel.title.lower():
                continue
            for member in panel.members:
                self.assertIn(member, measured, f"{panel.key}: {member}")

    def test_the_unmeasured_panels_say_so_in_their_titles(self) -> None:
        for key in ("epithelial_model_states", "stromal_model_states"):
            self.assertIn("not ADOC-measured", self.panels[key].title)

    def test_igfbp1_and_prl_are_exact_aliases(self) -> None:
        """The test that keeps the caption honest.

        If someone later gives the two markers distinct rules, this fails and
        forces the caption's "coincide by construction" claim to be revisited.
        """
        from dt_adoc.reporting.structure import load_structure

        facts = load_structure("adoc-literature-superset-v0.3.0", ROOT)
        classes = [set(members) for members in facts.alias_classes]
        self.assertTrue(
            any({"S_IGFBP1", "S_PRL"} <= cls for cls in classes),
            "S_IGFBP1 and S_PRL are no longer exact aliases -- revisit the "
            "analyte-panel caption and docs/results_reproducibility_matrix.md",
        )

    def test_the_model_declares_no_transition_rates(self) -> None:
        """Onset order is DAG depth alone, which is why the two curves coincide."""
        network = (
            ROOT
            / "models"
            / "superset"
            / "adoc-literature-superset-v0.3.0"
            / "network.bnd"
        ).read_text(encoding="utf-8")
        self.assertNotIn("rate_up", network)
        self.assertNotIn("rate_down", network)

    def test_the_panel_avoids_concentration_style_naming(self) -> None:
        """The user said "metabolites"; the repository's own guard bans
        concentration-style naming for Boolean node states, correctly.
        """
        panel = self.panels["secreted_analytes"]
        lowered = f"{panel.key} {panel.title} {panel.axis_label}".lower()
        for banned in ("metabolite", "abundance", "concentration", "ng_ml"):
            self.assertNotIn(banned, lowered)


class HorizonPlumbingTest(unittest.TestCase):
    """The C2 defect: an override must reach BOTH the metadata and the run."""

    def test_declared_durations_survive_a_horizon_override(self) -> None:
        from dt_adoc.simulation.timeline import TimelinePhase

        phase = TimelinePhase(
            phase_index=0,
            protocol_id="p",
            step_id="s",
            label="l",
            relative_duration=25.0,
            declared_duration=4.0,
            phase_start=0.0,
            phase_end=25.0,
            continuation_from=None,
            continuation_applied=False,
        )
        self.assertEqual(phase.relative_duration, 25.0)
        self.assertEqual(phase.declared_duration, 4.0)
        self.assertLess(phase.declared_duration, phase.relative_duration)

    def test_the_render_request_exposes_a_phase_horizon(self) -> None:
        from dt_adoc.reporting.render_dynamics import RenderRequest

        self.assertIsNone(RenderRequest().phase_horizon)
        self.assertEqual(RenderRequest(phase_horizon=25.0).phase_horizon, 25.0)

    def test_the_footer_does_not_claim_a_fitted_calibration(self) -> None:
        """calibration.yaml demoted adhesion to an ordinal diagnostic
        (magnitude_fitted: false), so no frame may say it was fitted.
        """
        from dt_adoc.reporting.network_figure import CLAIM_FOOTER

        calibration = yaml.safe_load(
            (ROOT / "config" / "calibration.yaml").read_text(encoding="utf-8")
        )
        self.assertIs(calibration["adhesion_objective"]["magnitude_fitted"], False)
        flat = " ".join(CLAIM_FOOTER.split())
        self.assertNotIn("was fitted", flat)
        self.assertIn("No magnitude is fitted", flat)
        self.assertIn("ordinal diagnostic", flat)

    def test_the_footer_states_the_horizon_and_the_relay_arithmetic(self) -> None:
        from dt_adoc.reporting.network_figure import CLAIM_FOOTER

        for token in (
            "dimensionless",
            "4000x",
            "0.82",
            "9/19",
            "EXPLORATORY",
            "coincide by construction",
        ):
            self.assertIn(token, CLAIM_FOOTER)


class VisualizationConfigTest(unittest.TestCase):
    def test_the_assumed_non_spp1_relay_label_is_present(self) -> None:
        config = yaml.safe_load(
            (ROOT / "config" / "visualization.yaml").read_text(encoding="utf-8")
        )
        labels = config["short_labels"]
        self.assertEqual(
            labels["X_INTERFACE_REDUNDANT_RELAY"], "Assumed non-SPP1 relay"
        )

    def test_short_labels_all_target_a_real_node(self) -> None:
        """A typo'd short_labels key currently fails silently."""
        from dt_adoc.model.catalog import load_tsv

        config = yaml.safe_load(
            (ROOT / "config" / "visualization.yaml").read_text(encoding="utf-8")
        )
        known: set[str] = set()
        for model_dir in (
            ROOT / "models" / "superset" / "adoc-literature-superset-v0.3.0",
            ROOT / "models" / "extended" / "adoc-literature-v0.2.0",
            ROOT / "models" / "baseline" / "adoc-core-v0.1.0",
        ):
            known |= {
                entry["node_id"]
                for entry in load_tsv(model_dir / "node_dictionary.tsv")
            }
        unknown = sorted(set(config["short_labels"]) - known)
        self.assertEqual(unknown, [], unknown)


if __name__ == "__main__":
    unittest.main()


class ArchivedSupersetV04IsImmutableTest(unittest.TestCase):
    """The v0.4.0 README animation is superseded, not deleted."""

    def test_the_v0_4_assets_are_byte_identical(self) -> None:
        for name, expected in ARCHIVED_V0_4.items():
            path = ASSETS / name
            self.assertTrue(path.is_file(), name)
            self.assertEqual(_digest(path), expected, name)


class ArchivedSupersetV03IsImmutableTest(unittest.TestCase):
    """v0.3.0 is frozen, not deleted. Its committed assets must stay byte-exact
    now that v0.4.0 is the active model, exactly as the v0.2.0 set is."""

    def test_the_v0_3_assets_are_byte_identical(self) -> None:
        for name, expected in ARCHIVED_V0_3.items():
            path = ASSETS / name
            self.assertTrue(path.is_file(), name)
            self.assertEqual(_digest(path), expected, name)
