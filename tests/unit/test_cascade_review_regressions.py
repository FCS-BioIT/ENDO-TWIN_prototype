"""Regression tests for the first independent review of the cascade tool.

- Order is counted only when identifiable from the occupancies: a hidden
  out-and-back pair can make a node's reconstructed first switch later than
  another's that happened after it.
- The control is called stationary only when nothing switched and every rule is
  known and agrees at the horizon.
- A bundle is written only to a plain-named directory inside the output root,
  never over anything else.
"""

from __future__ import annotations

import itertools
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.cascade.events import node_events
from dt_adoc.cascade.run import (
    BUNDLE_FILES,
    begin_staging,
    bundle_directory,
    commit_staging,
    run_diagnostics,
    run_warnings,
)
from dt_adoc.cascade.summary import pairwise_precedence


def occupancy(initial, switch_times, tick, horizon):
    n = round(horizon / tick)
    starts = np.arange(n) * tick
    out = np.zeros(n)
    edges = [0.0, *sorted(switch_times), horizon]
    state = initial
    for a, b in itertools.pairwise(edges):
        if state == 1:
            for j in range(n):
                lo, hi = starts[j], starts[j] + tick
                out[j] += max(0.0, min(hi, b) - max(lo, a)) / tick
        state = 1 - state
    return out, starts


def events_table(
    paths: dict[str, list[float]], tick: float, horizon: float
) -> pd.DataFrame:
    rows = []
    for node, times in paths.items():
        x, starts = occupancy(1, times, tick, horizon)
        e = node_events(x, starts, tick, 1)
        rows.append(
            {
                "trajectory": 0,
                "node": node,
                "seed": 1,
                "initial": e.initial,
                "final": e.final,
                "n_switches_min": e.n_min,
                "first_switch_time": e.first_time,
                "first_switch_lower": e.first_lower,
                "first_switch_upper": e.first_upper,
                "first_switch_resolved": e.first_resolved,
                "category": e.category,
                "rule_disagrees_at_horizon": False,
            }
        )
    return pd.DataFrame(rows)


class IdentifiableOrderTests(unittest.TestCase):
    def test_hidden_switches_never_reverse_the_reported_order(self):
        # The reviewer's counterexample: A truly switches first (0.1), but two
        # hidden switches in the same window push its reconstruction to 0.8,
        # after B's exact 0.5.
        ev = events_table({"A": [0.1, 0.2, 0.9], "B": [0.5]}, tick=1.0, horizon=2.0)
        a = ev.set_index("node").loc["A"]
        self.assertAlmostEqual(a.first_switch_time, 0.8)
        self.assertLessEqual(a.first_switch_lower, 0.1)
        pr = pairwise_precedence(ev).set_index(["node_a", "node_b"])
        r = pr.loc[("B", "A")]
        self.assertEqual((r.n_a_first, r.n_b_first, r.n_order_unresolved), (0, 0, 1))
        self.assertTrue(np.isnan(r.p_a_first))

    def test_different_windows_are_ordered_even_with_hidden_switches(self):
        ev = events_table({"A": [0.1, 0.2, 0.9], "B": [1.5]}, tick=1.0, horizon=3.0)
        r = pairwise_precedence(ev).set_index(["node_a", "node_b"]).loc[("A", "B")]
        self.assertEqual((r.n_a_first, r.n_order_unresolved, r.p_a_first), (1, 0, 1.0))

    def test_point_events_without_intervals_still_work(self):
        ev = events_table({"A": [0.3], "B": [0.6]}, tick=0.1, horizon=1.0)
        ev = ev.drop(columns=["first_switch_lower", "first_switch_upper"])
        r = pairwise_precedence(ev).set_index(["node_a", "node_b"]).loc[("A", "B")]
        self.assertEqual(r.p_a_first, 1.0)


def diag_events(rule_values, switches=0):
    return pd.DataFrame(
        {
            "trajectory": list(range(len(rule_values))),
            "node": "A",
            "n_switches_min": switches,
            "first_switch_resolved": None,
            "final": 1,
            "rule_disagrees_at_horizon": rule_values,
        }
    )


class StationarityTests(unittest.TestCase):
    def test_clean_control_is_stationary(self):
        d = run_diagnostics(diag_events([False, False]), diag_events([False, False]))
        self.assertTrue(d["control_stationary"])

    def test_a_disagreeing_rule_without_a_switch_is_not_stationary(self):
        d = run_diagnostics(diag_events([False]), diag_events([False, True]))
        self.assertFalse(d["control_stationary"])
        self.assertEqual(d["control"]["cells_no_switch_rule_disagrees_at_horizon"], 1)

    def test_an_unevaluable_rule_is_not_stationary(self):
        d = run_diagnostics(diag_events([False]), diag_events([False, None]))
        self.assertFalse(d["control_stationary"])
        self.assertEqual(d["control"]["cells_rule_unknown_at_horizon"], 1)

    def test_strings_read_back_from_tsv_are_understood(self):
        d = run_diagnostics(diag_events(["False"]), diag_events(["False", "True"]))
        self.assertFalse(d["control_stationary"])

    def test_a_control_switch_is_not_stationary(self):
        d = run_diagnostics(diag_events([False]), diag_events([False], switches=1))
        self.assertFalse(d["control_stationary"])


class BundleDirectoryTests(unittest.TestCase):
    def test_unsafe_run_ids_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "out"
            for bad in ("../data", "..", "/tmp/x", "a/b", "", ".hidden", "x/../y"):
                with self.subTest(run_id=bad), self.assertRaises(ValueError):
                    bundle_directory(root, bad)
            self.assertFalse((Path(tmp) / "data").exists())

    def test_a_symlink_escaping_the_root_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "out"
            root.mkdir()
            (root / "link").symlink_to(Path(tmp))
            with self.assertRaises(ValueError):
                bundle_directory(root, "link")

    def test_an_existing_bundle_is_not_replaced_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = bundle_directory(root, "run1")
            out.mkdir()
            (out / "events.tsv").write_text("x")
            with self.assertRaises(FileExistsError):
                bundle_directory(root, "run1")
            self.assertEqual(bundle_directory(root, "run1", overwrite=True), out)

    def test_overwrite_never_mixes_with_foreign_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "run1").mkdir()
            (root / "run1" / "evidence.xlsx").write_text("x")
            with self.assertRaises(FileExistsError):
                bundle_directory(root, "run1", overwrite=True)

    def test_bundle_files_are_the_declared_set(self):
        self.assertIn("metadata.json", BUNDLE_FILES)
        self.assertEqual(len(set(BUNDLE_FILES)), 8)


if __name__ == "__main__":
    unittest.main()


class UnknownInitialStateTests(unittest.TestCase):
    def test_a_switching_node_with_unknown_initial_state_is_refused(self):
        from dt_adoc.cascade.summary import UnknownInitialStateError, node_summary

        x, starts = occupancy(1, [0.04], 0.1, 1.0)
        e = node_events(x, starts, 0.1, None)  # switch inside the first window
        self.assertIsNone(e.initial)
        self.assertGreaterEqual(e.n_min, 1)  # not a non-switcher at the event level
        ev = pd.DataFrame(
            [
                {
                    "trajectory": 0,
                    "node": "A",
                    "seed": 1,
                    "initial": e.initial,
                    "final": e.final,
                    "n_switches_min": e.n_min,
                    "first_switch_time": e.first_time,
                    "first_switch_lower": e.first_lower,
                    "first_switch_upper": e.first_upper,
                    "first_switch_resolved": e.first_resolved,
                    "category": e.category,
                    "rule_disagrees_at_horizon": None,
                }
            ]
        )
        with self.assertRaisesRegex(UnknownInitialStateError, "A \\(1 trajectories\\)"):
            node_summary(ev)

    def test_known_initial_states_pass(self):
        from dt_adoc.cascade.summary import require_known_initial_states

        require_known_initial_states(events_table({"A": [0.5]}, tick=0.1, horizon=1.0))


class MemoryPolicyTests(unittest.TestCase):
    MV = "adoc-literature-superset-v0.6.0"

    def test_an_unknown_policy_is_refused(self):
        from dt_adoc.cascade.simulate import validate_memory_policy

        for bad in ("all_non_input", "extended_maternal", "explicit", ""):
            with self.subTest(policy=bad), self.assertRaises(ValueError):
                validate_memory_policy(self.MV, bad)

    def test_supported_policies_pass(self):
        from dt_adoc.cascade.simulate import validate_memory_policy

        for good in (
            "all_non_inputs",
            "relay_only",
            "extended_maternal_joint",
            "minimal_stable_joint",
        ):
            with self.subTest(policy=good):
                validate_memory_policy(self.MV, good)

    def test_the_cascade_refuses_before_simulating(self):
        from unittest import mock

        from dt_adoc.cascade import run as run_module
        from dt_adoc.cascade.simulate import StartSettings
        from dt_adoc.perturbations.spec import parse_spec

        spec = parse_spec(
            {
                "name": "t",
                "model_version": self.MV,
                "start": "hormone_treated_maternal",
                "input_changes": {"IN_PROGESTIN": False},
            }
        )
        req = run_module.CascadeRequest(
            spec, n_trajectories=2, start=StartSettings(memory_policy="typo")
        )
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(run_module, "build_starting_ensemble") as built,
        ):
            with self.assertRaises(ValueError):
                run_module.run_cascade(req, out_root=Path(tmp))
            built.assert_not_called()
            self.assertEqual(list(Path(tmp).iterdir()), [])


class TransactionalOverwriteTests(unittest.TestCase):
    def test_a_completed_staging_replaces_the_old_bundle_whole(self):
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            final.mkdir()
            (final / "metadata.json").write_text("old")
            (final / "cascade.png").write_text("old figure")
            staging = begin_staging(final)
            (staging / "metadata.json").write_text("new")
            commit_staging(staging, final, overwrite=True)
            self.assertEqual((final / "metadata.json").read_text(), "new")
            self.assertFalse((final / "cascade.png").exists())  # nothing old survives
            self.assertEqual(
                sorted(p.name for p in Path(tmp).iterdir()), [".trash", "run1"]
            )
            # The replaced bundle is kept whole in the trash, not deleted.
            (kept,) = (Path(tmp) / ".trash").iterdir()
            self.assertEqual((kept / "metadata.json").read_text(), "old")
            self.assertEqual((kept / "cascade.png").read_text(), "old figure")

    def test_a_failed_run_leaves_the_old_bundle_untouched(self):
        from unittest import mock

        from dt_adoc.cascade import run as run_module
        from dt_adoc.perturbations.spec import parse_spec

        spec = parse_spec(
            {
                "name": "t",
                "model_version": "adoc-literature-superset-v0.6.0",
                "start": "hormone_treated_maternal",
                "input_changes": {"IN_PROGESTIN": False},
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            final.mkdir()
            (final / "metadata.json").write_text("old provenance")
            (final / "events.tsv").write_text("old events")
            req = run_module.CascadeRequest(
                spec, n_trajectories=2, run_id="run1", overwrite=True
            )
            boom = RuntimeError("injected failure after the tables would be written")
            with (
                mock.patch.object(
                    run_module, "build_starting_ensemble", side_effect=boom
                ),
                self.assertRaises(RuntimeError),
            ):
                run_module.run_cascade(req, out_root=Path(tmp))
            self.assertEqual((final / "metadata.json").read_text(), "old provenance")
            self.assertEqual((final / "events.tsv").read_text(), "old events")
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["run1"])

    def test_failure_while_rendering_also_leaves_nothing_mixed(self):
        # A real (tiny) run whose figure rendering fails after every table has
        # been written into the staging directory.
        from unittest import mock

        from dt_adoc.cascade import run as run_module
        from dt_adoc.cascade.simulate import StartSettings
        from dt_adoc.perturbations.spec import parse_spec

        spec = parse_spec(
            {
                "name": "t",
                "model_version": "adoc-literature-superset-v0.6.0",
                "start": "hormone_treated_maternal",
                "input_changes": {"IN_PROGESTIN": False},
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            final.mkdir()
            (final / "metadata.json").write_text("old provenance")
            req = run_module.CascadeRequest(
                spec,
                n_trajectories=2,
                run_id="run1",
                overwrite=True,
                workers=1,
                start=StartSettings(lineage_trajectories=200),
            )
            with (
                mock.patch.object(
                    run_module, "render_cascade", side_effect=RuntimeError("render")
                ),
                self.assertRaisesRegex(RuntimeError, "render"),
            ):
                run_module.run_cascade(req, out_root=Path(tmp))
            self.assertEqual(sorted(p.name for p in final.iterdir()), ["metadata.json"])
            self.assertEqual((final / "metadata.json").read_text(), "old provenance")
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["run1"])


def summary_events(spec):
    """``{trajectory: {node: (initial, time or None)}}`` -> events (single switches)."""
    rows = []
    for k, nodes in spec.items():
        for node, (initial, t) in nodes.items():
            sw = t is not None
            rows.append(
                {
                    "trajectory": k,
                    "node": node,
                    "seed": 100 + k,
                    "initial": initial,
                    "final": (1 - initial) if sw else initial,
                    "n_switches_min": int(sw),
                    "first_switch_time": t if sw else np.nan,
                    "first_switch_resolved": True if sw else None,
                    "category": "net_change_n_switches_min_1" if sw else "no_switch",
                    "rule_disagrees_at_horizon": False,
                }
            )
    return pd.DataFrame(rows)


class DirectionCompletenessTests(unittest.TestCase):
    def test_sub_threshold_switching_in_both_directions_is_kept(self):
        from dt_adoc.cascade.summary import node_summary

        spec = {}
        for k in range(100):
            initial = 1 if k < 50 else 0
            t = 1.0 if (k < 4 or 50 <= k < 54) else None  # 4 % each way
            spec[k] = {"A": (initial, t), "Z": (1, 2.0)}
        s = node_summary(summary_events(spec)).query("node == 'A'")
        self.assertEqual(sorted(s.direction), ["off_to_on", "on_to_off"])
        self.assertNotIn("none", set(s.direction))
        self.assertEqual(s.n_contributing.sum(), 8)
        self.assertFalse(s.shown_in_figure.any())
        self.assertAlmostEqual(s.p_switch.iloc[0], 0.08)

    def test_none_occurs_exactly_when_the_node_never_switches(self):
        from dt_adoc.cascade.summary import node_summary

        s = node_summary(
            summary_events({k: {"A": (1, None), "B": (1, 1.0 + k)} for k in range(5)})
        )
        for row in s.itertuples():
            self.assertEqual(row.direction == "none", row.p_switch == 0)


class FigureListTests(unittest.TestCase):
    def test_never_switched_is_read_from_p_switch(self):
        from dt_adoc.cascade.figure import figure_rows
        from dt_adoc.cascade.summary import node_summary

        # B switches only in a trajectory where nothing else does, so its
        # normalised position is undefined everywhere: it switched, but cannot
        # be drawn on a normalised axis.
        spec = {
            0: {"A": (1, 1.0), "B": (1, None), "C": (1, 2.0), "N": (1, None)},
            1: {"A": (1, None), "B": (1, 1.5), "C": (1, None), "N": (1, None)},
        }
        s = node_summary(summary_events(spec))
        rows, never, not_drawn = figure_rows(s, "normalized_time")
        self.assertEqual(never, ["N"])
        self.assertEqual(not_drawn, ["B"])
        self.assertEqual(sorted(rows.node), ["A", "C"])
        rows_abs, never_abs, not_drawn_abs = figure_rows(s, "absolute_time")
        self.assertEqual((never_abs, not_drawn_abs), (["N"], []))
        self.assertIn("B", set(rows_abs.node))


class SweepTwoRegressionTests(unittest.TestCase):
    def test_overwrite_refuses_a_directory_or_symlink_with_a_bundle_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "run1"
            (out / "events.tsv").mkdir(parents=True)
            (out / "events.tsv" / "precious.dat").write_text("x")
            with self.assertRaisesRegex(FileExistsError, "not regular files"):
                bundle_directory(root, "run1", overwrite=True)
            self.assertTrue((out / "events.tsv" / "precious.dat").exists())
            other = root / "run2"
            other.mkdir()
            (other / "metadata.json").symlink_to(
                root / "run1" / "events.tsv" / "precious.dat"
            )
            with self.assertRaisesRegex(FileExistsError, "not regular files"):
                bundle_directory(root, "run2", overwrite=True)

    def test_unknown_finals_are_missing_not_unchanged(self):
        from dt_adoc.cascade.summary import compare_arms, node_summary

        rows = []
        for arm, final in (("perturbed", None), ("control", 1)):
            for k in range(20):
                rows.append(
                    {
                        "arm": arm,
                        "trajectory": k,
                        "node": "A",
                        "seed": k,
                        "initial": 1,
                        "final": final,
                        "n_switches_min": 1 if final is None else 0,
                        "first_switch_time": 24.99 if final is None else np.nan,
                        "first_switch_resolved": None,
                        "category": "unresolved_end",
                        "rule_disagrees_at_horizon": None,
                    }
                )
        ev = pd.DataFrame(rows)
        p, c = ev[ev.arm == "perturbed"], ev[ev.arm == "control"]
        r = compare_arms(p, c).iloc[0]
        self.assertEqual(r.n_pairs_final_known, 0)
        self.assertTrue(np.isnan(r.delta_p_net_change))
        self.assertTrue(np.isnan(r.delta_p_net_change_ci_low))
        s = node_summary(p).iloc[0]
        self.assertEqual(s.n_final_known, 0)
        self.assertTrue(np.isnan(s.p_net_change))
        self.assertEqual(s.p_final_unknown, 1.0)

    def test_the_logic_cache_follows_the_network_not_the_version_string(self):
        from types import SimpleNamespace
        from unittest import mock

        from dt_adoc.cascade import simulate

        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.bnd", Path(tmp) / "b.bnd"
            a.write_text("Node X { logic = Y; }\nNode Y { logic = Y; }\n")
            b.write_text("Node X { logic = not Y; }\nNode Y { logic = Y; }\n")
            specs = {
                Path(tmp) / "ra": SimpleNamespace(network_bnd=a),
                Path(tmp) / "rb": SimpleNamespace(network_bnd=b),
            }
            with mock.patch.object(
                simulate, "resolve_model", side_effect=lambda v, r: specs[r]
            ):
                la = simulate._logic("same-version", {}, Path(tmp) / "ra")
                lb = simulate._logic("same-version", {}, Path(tmp) / "rb")
            ya = simulate._value(la["X"][0], {"Y": True})
            yb = simulate._value(lb["X"][0], {"Y": True})
            self.assertNotEqual(ya, yb)


class PhaseHorizonTests(unittest.TestCase):
    """MaBoSS stops at the last whole tick, so the recorded horizon must be one."""

    def test_a_horizon_that_is_not_a_whole_number_of_ticks_is_refused(self):
        from dt_adoc.cascade.simulate import PhaseSettings

        # 0.3 and 0.7 are decimal multiples of 0.1, but their float ratios are
        # 2.9999999999999996 and 6.999999999999999 and MaBoSS (installed
        # cmaboss) returns 2 and 6 windows; 1.00000000001 returns 10.
        for horizon in (1.05, 0.05, 0.95, 1.00000000001, 0.99999999999, 0.3, 0.7):
            with self.assertRaisesRegex(ValueError, "whole number of ticks"):
                PhaseSettings(horizon=horizon, tick=0.1)

    def test_non_positive_or_non_finite_settings_are_refused(self):
        from dt_adoc.cascade.simulate import PhaseSettings

        for horizon, tick in ((0.0, 0.1), (1.0, 0.0), (-1.0, 0.1), (float("nan"), 0.1)):
            with self.assertRaises(ValueError):
                PhaseSettings(horizon=horizon, tick=tick)

    def test_whole_tick_horizons_are_accepted(self):
        from dt_adoc.cascade.simulate import PhaseSettings

        # Each ratio is an exact float integer, and MaBoSS returns that many
        # windows (25/0.01: 2500, 1.0/0.1: 10, 0.9/0.3: 3, 2.5/0.5: 5).
        for horizon, tick in ((25.0, 0.01), (1.0, 0.1), (0.9, 0.3), (2.5, 0.5)):
            self.assertEqual(
                PhaseSettings(horizon=horizon, tick=tick).n_windows,
                round(horizon / tick),
            )


class WarningsArePersisted(unittest.TestCase):
    """B (run.py): a non-stationary control is a warning in metadata, not only stderr."""

    def test_a_stationary_control_gives_no_warning(self):
        self.assertEqual(run_warnings({"control_stationary": True}), [])

    def test_a_switching_control_gives_the_warning(self):
        warnings = run_warnings({"control_stationary": False})
        self.assertEqual(len(warnings), 1)
        self.assertIn("matched control switched", warnings[0])


class SwitchCountClaimsAreLowerBounds(unittest.TestCase):
    """A (events.py): n_switches_min is a lower bound, so no category or claim may
    say that a node switched exactly once or never more than once."""

    def test_no_category_claims_a_single_switch(self):
        from dt_adoc.cascade.events import CATEGORIES

        for category in CATEGORIES:
            self.assertNotIn("single", category)

    def test_the_stage_c_record_does_not_claim_no_repeated_switch(self):
        stage = ROOT / "docs" / "perturbation_cascade"
        for path in (
            stage / "README.md",
            stage / "stage_c" / "compare_historical.py",
            stage / "stage_c" / "historical_comparison_summary.json",
        ):
            text = path.read_text(encoding="utf-8").lower()
            for phrase in (
                "switched more than once",
                "switching more than once",
                "no repeated switch",
            ):
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertNotIn(phrase, text)


class EveryInputIsContentPinned(unittest.TestCase):
    """B (run.py:440): the bundle's implementation record covers every module and
    file the simulation depends on, not only the cascade package."""

    def test_the_shared_simulation_code_is_recorded(self):
        from dt_adoc.cascade.run import implementation_files

        recorded = {p.relative_to(ROOT).as_posix() for p in implementation_files(ROOT)}
        for path in (
            "src/dt_adoc/maboss_adapter.py",
            "src/dt_adoc/simulation/runner.py",
            "src/dt_adoc/model/runtime.py",
            "src/dt_adoc/protocols/conditions.py",
            "src/dt_adoc/perturbations/engine.py",
            "config/intervention_library.tsv",
            "src/dt_adoc/perturbations/spec.py",
            "src/dt_adoc/cascade/simulate.py",
        ):
            self.assertIn(path, recorded)

    def test_every_imported_dt_adoc_module_is_recorded(self):
        import subprocess

        probe = (
            "import sys; from pathlib import Path; "
            "import dt_adoc.cascade.run as R, dt_adoc.cascade.cli; "
            "root = Path.cwd(); rec = {p.resolve() for p in R.implementation_files(root)}; "
            "mods = {Path(m.__file__).resolve() for n, m in list(sys.modules.items()) "
            "if n.split('.')[0] == 'dt_adoc' and getattr(m, '__file__', None)}; "
            "print('\\n'.join(sorted(str(m) for m in mods - rec)))"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", probe],
            cwd=ROOT,
            env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "", "imported but not recorded")

    def test_a_change_to_any_dependency_class_changes_the_record(self):
        """One representative per class: the cascade, shared simulation code, the
        intervention library, calibration and protocol settings, the model
        registry, a model network and a lineage phase's condition cfg."""
        from dt_adoc.cascade.run import configuration_files, implementation_files
        from dt_adoc.model.provenance import describe_file

        def record(root):
            return {
                describe_file(p, root=root).path: describe_file(p, root=root).sha256
                for p in (*implementation_files(root), *configuration_files(root))
            }

        v060 = "models/superset/adoc-literature-superset-v0.6.0"
        probes = (
            "src/dt_adoc/cascade/events.py",
            "src/dt_adoc/maboss_adapter.py",
            "src/dt_adoc/simulation/runner.py",
            "config/intervention_library.tsv",
            "config/calibration.yaml",
            "config/protocols_markerless.yaml",
            f"{v060}/provenance.toml",
            "models/superset/adoc-literature-superset-v0.5.2/network.bnd",
            f"{v060}/conditions/hormone_treated.cfg",
        )
        with tempfile.TemporaryDirectory() as raw:
            copy = Path(raw)
            for path in (*implementation_files(ROOT), *configuration_files(ROOT)):
                target = copy / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
            baseline = record(copy)
            for relative in probes:
                with self.subTest(path=relative):
                    self.assertIn(relative, baseline)
                    target = copy / relative
                    original = target.read_bytes()
                    target.write_bytes(original + b"\n")
                    changed = record(copy)
                    target.write_bytes(original)
                    self.assertNotEqual(changed[relative], baseline[relative])


class CommitRechecksTheTarget(unittest.TestCase):
    """B (run.py:433): the preflight runs before the simulation, so the commit
    must recheck the target: a bundle committed meanwhile by another run is not
    replaced without overwrite, and a late foreign entry is never deleted."""

    def _staged(self, final, text):
        staging = begin_staging(final)
        (staging / "metadata.json").write_text(text)
        return staging

    def test_a_competing_bundle_is_not_replaced_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            bundle_directory(Path(tmp), "run1")  # both runs pass the preflight
            first, second = self._staged(final, "first"), self._staged(final, "second")
            commit_staging(first, final)
            with self.assertRaises(FileExistsError):
                commit_staging(second, final)
            self.assertEqual((final / "metadata.json").read_text(), "first")

    def test_a_late_foreign_entry_is_refused_and_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            final.mkdir()
            (final / "metadata.json").write_text("old")
            bundle_directory(Path(tmp), "run1", overwrite=True)  # preflight passes
            staging = self._staged(final, "new")
            (final / "notes.txt").write_text("not a bundle file")  # arrives late
            with self.assertRaises(FileExistsError):
                commit_staging(staging, final, overwrite=True)
            self.assertEqual((final / "notes.txt").read_text(), "not a bundle file")
            self.assertEqual((final / "metadata.json").read_text(), "old")

    def test_an_entry_reaching_the_set_aside_bundle_restores_it(self):
        from unittest import mock

        from dt_adoc.cascade import run as run_module

        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            final.mkdir()
            (final / "metadata.json").write_text("old")
            staging = self._staged(final, "new")
            real = run_module._refuse_unless_replaceable
            calls = []

            def foreign_after_first_check(path, *, overwrite):
                calls.append(path)
                if len(calls) == 2:  # the set-aside copy, checked before removal
                    (path / "notes.txt").write_text("late")
                return real(path, overwrite=overwrite)

            with (
                mock.patch.object(
                    run_module, "_refuse_unless_replaceable", foreign_after_first_check
                ),
                self.assertRaises(FileExistsError),
            ):
                commit_staging(staging, final, overwrite=True)
            self.assertEqual((final / "notes.txt").read_text(), "late")
            self.assertEqual((final / "metadata.json").read_text(), "old")

    def test_commits_into_one_directory_are_serialised(self):
        import fcntl
        import os
        import threading

        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            staging = self._staged(final, "new")
            held = os.open(tmp, os.O_RDONLY)
            fcntl.flock(held, fcntl.LOCK_EX)  # another run is committing
            done = threading.Event()
            worker = threading.Thread(
                target=lambda: (commit_staging(staging, final), done.set())
            )
            worker.start()
            self.assertFalse(done.wait(0.3), "commit did not wait for the lock")
            fcntl.flock(held, fcntl.LOCK_UN)
            os.close(held)
            worker.join(5)
            self.assertTrue(done.is_set())
            self.assertEqual((final / "metadata.json").read_text(), "new")

    def test_an_entry_arriving_after_the_last_check_is_never_deleted(self):
        from unittest import mock

        from dt_adoc.cascade import run as run_module

        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            final.mkdir()
            (final / "metadata.json").write_text("old")
            (final / "cascade.png").write_text("old figure")
            staging = self._staged(final, "new")
            real = run_module._refuse_unless_replaceable
            calls = []

            def foreign_after_the_last_check(path, *, overwrite):
                result = real(path, overwrite=overwrite)
                calls.append(path)
                if len(calls) == 2:  # passed its last check; a file arrives now
                    (path / "notes.txt").write_text("late")
                return result

            with mock.patch.object(
                run_module, "_refuse_unless_replaceable", foreign_after_the_last_check
            ):
                commit_staging(staging, final, overwrite=True)
            self.assertEqual((final / "metadata.json").read_text(), "new")
            kept = list((Path(tmp) / ".trash").iterdir())
            self.assertEqual(len(kept), 1)
            self.assertEqual((kept[0] / "notes.txt").read_text(), "late")
            self.assertEqual(
                sorted(p.name for p in kept[0].iterdir()),
                ["cascade.png", "metadata.json", "notes.txt"],
            )

    def test_a_late_directory_under_a_bundle_file_name_neither_fails_nor_is_lost(self):
        from unittest import mock

        from dt_adoc.cascade import run as run_module

        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            final.mkdir()
            (final / "metadata.json").write_text("old")
            staging = self._staged(final, "new")
            real = run_module._refuse_unless_replaceable
            calls = []

            def late_directory(path, *, overwrite):
                result = real(path, overwrite=overwrite)
                calls.append(path)
                if len(calls) == 2:  # after the set-aside copy's last check
                    (path / "metadata.json").unlink()
                    (path / "metadata.json").mkdir()
                    (path / "metadata.json" / "inner.txt").write_text("late")
                return result

            with mock.patch.object(
                run_module, "_refuse_unless_replaceable", late_directory
            ):
                commit_staging(staging, final, overwrite=True)  # does not raise
            self.assertEqual((final / "metadata.json").read_text(), "new")
            kept = list((Path(tmp) / ".trash").iterdir())
            self.assertEqual(
                (kept[0] / "metadata.json" / "inner.txt").read_text(), "late"
            )

    def test_a_target_swapped_for_a_symlink_is_refused_and_its_target_untouched(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            tempfile.TemporaryDirectory() as away,
        ):
            final = Path(tmp) / "run1"
            bundle_directory(Path(tmp), "run1", overwrite=True)  # preflight: absent
            staging = self._staged(final, "new")
            (Path(away) / "events.tsv").write_text("someone else's")
            final.symlink_to(away, target_is_directory=True)  # swapped in late
            with self.assertRaises(FileExistsError):
                commit_staging(staging, final, overwrite=True)
            self.assertEqual((Path(away) / "events.tsv").read_text(), "someone else's")
            self.assertTrue(final.is_symlink())

    def test_a_regular_file_replacing_a_bundle_file_late_is_kept(self):
        """Sweep 4: a regular file put under a bundle file's name after the last
        check must survive; the replaced bundle is moved, never deleted."""
        from unittest import mock

        from dt_adoc.cascade import run as run_module

        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "run1"
            final.mkdir()
            (final / "metadata.json").write_text("old")
            staging = self._staged(final, "new")
            real = run_module._refuse_unless_replaceable
            calls = []

            def replaced_after_the_last_check(path, *, overwrite):
                result = real(path, overwrite=overwrite)
                calls.append(path)
                if len(calls) == 2:
                    (path / "metadata.json").write_text("someone else's file")
                return result

            with mock.patch.object(
                run_module, "_refuse_unless_replaceable", replaced_after_the_last_check
            ):
                commit_staging(staging, final, overwrite=True)
            self.assertEqual((final / "metadata.json").read_text(), "new")
            (kept,) = (Path(tmp) / ".trash").iterdir()
            self.assertEqual(
                (kept / "metadata.json").read_text(), "someone else's file"
            )

    def test_a_symlinked_trash_is_refused_and_the_bundle_stays(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            tempfile.TemporaryDirectory() as away,
        ):
            final = Path(tmp) / "run1"
            final.mkdir()
            (final / "metadata.json").write_text("old")
            staging = self._staged(final, "new")
            (Path(tmp) / ".trash").symlink_to(away, target_is_directory=True)
            with self.assertRaises(FileExistsError):
                commit_staging(staging, final, overwrite=True)
            self.assertEqual((final / "metadata.json").read_text(), "old")
            self.assertEqual(list(Path(away).iterdir()), [])
