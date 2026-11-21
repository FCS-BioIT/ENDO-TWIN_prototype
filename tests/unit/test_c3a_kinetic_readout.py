"""C3a runner: the code implements the frozen pre-registration, and spends no seed.

Nothing here runs MaBoSS. The tests hold five things in place:

1. every constant equals the value the pre-registration freezes;
2. the phase plan is section 3's, with 25.0 applied to challenge phases only,
   and never through ``run_arm(horizon_class="converged")``. This is pinned
   at the call sites ``run_block`` uses, with MaBoSS mocked;
3. the construction check accepts the committed pairs and refuses a mismatch;
4. the binding refuses a bound file that differs from the pre-registration
   commit;
5. bands, labels, classes and the count-sensitivity record follow sections
   7-10, on synthetic block values.
"""

from __future__ import annotations

import contextlib
import os
import random
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting import c3a_kinetic_readout as M

PREREG = (ROOT / M.PREREGISTRATION).read_text(encoding="utf-8")
ADDENDUM = (ROOT / M.ADDENDUM).read_text(encoding="utf-8")


# History-bound classes read the pre-registration commits or HEAD~1 of the
# DT-ADOC history, which ENDO-TWIN does not carry (tests/unit/source_history.py).
from tests.unit.source_history import (
    skip_unless_available,
    skip_unless_parent_commit,
)

_HISTORY_PREREG = skip_unless_available(M.PREREG_COMMIT, M.ADDENDUM_COMMIT)
_HISTORY_PARENT = skip_unless_parent_commit()


@_HISTORY_PREREG
class ConstantsMatchThePreregistration(unittest.TestCase):
    def test_quantiles_are_the_frozen_values_and_recompute(self) -> None:
        from scipy.stats import norm, t

        alpha = M.FAMILY_ALPHA / M.INTERVALS_PER_FAMILY
        self.assertAlmostEqual(t.ppf(1 - alpha / 2, M.REPLICATES - 1), M.T19, places=6)
        self.assertAlmostEqual(norm.ppf(1 - alpha / 2), M.Q, places=6)
        # Addendum 01 governs the multiplier: 2 pairs x 2 estimands = 4 bands.
        self.assertEqual(M.INTERVALS_PER_FAMILY, 4)
        self.assertIn("**4 bands**", ADDENDUM)
        self.assertIn(f"`t₁₉ = {M.T19}`", ADDENDUM)
        self.assertIn(f"`q = {M.Q}`", ADDENDUM)

    def test_margin_counts_and_seeds(self) -> None:
        self.assertIn("**Margin `δ = 0.005`**", PREREG)
        self.assertEqual(M.DELTA, 0.005)
        self.assertIn("`R = 20` disjoint seed blocks", PREREG)
        self.assertEqual(
            (M.replicate_seed(0, 20_000), M.replicate_seed(19, 20_000) + 19_999),
            (2_000_001, 2_400_000),
        )
        self.assertEqual(
            (M.replicate_seed(0, 2_000), M.replicate_seed(19, 2_000) + 1_999),
            (2_400_001, 2_440_000),
        )
        self.assertIn("seeds 2,000,001 to\n  2,400,000", PREREG)
        for bad in ((20, 20_000), (0, 5_000)):
            with self.assertRaises(ValueError):
                M.replicate_seed(*bad)

    def test_converged_horizon(self) -> None:
        from dt_adoc.concordance.simulate import CONVERGED_PHASE_HORIZON

        self.assertEqual(M.CONVERGED_PHASE_HORIZON, CONVERGED_PHASE_HORIZON)

    def test_the_binding_commit_contains_this_preregistration(self) -> None:
        import subprocess

        addendum = subprocess.run(
            ["git", "show", f"{M.ADDENDUM_COMMIT}:{M.ADDENDUM}"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        self.assertEqual(addendum.decode("utf-8"), ADDENDUM)
        self.assertEqual(
            M.GOVERNING_SPECIFICATION, [str(M.PREREGISTRATION), str(M.ADDENDUM)]
        )
        frozen = subprocess.run(
            ["git", "show", f"{M.PREREG_COMMIT}:{M.PREREGISTRATION}"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        self.assertEqual(frozen.decode("utf-8"), PREREG)


class ThePhasePlan(unittest.TestCase):
    def test_task_counts(self) -> None:
        self.assertEqual(len(M.plan_for(20_000)), 14)
        self.assertEqual(len(M.plan_for(2_000)), 14)
        dry = M.dry_run(ROOT)
        self.assertEqual(dry["maboss_tasks_total"], 560)
        self.assertEqual(dry["worker_jobs"], 40)
        self.assertIn("**Total: 560 MaBoSS tasks** in 40 worker jobs", ADDENDUM)

    def test_25_is_applied_to_challenge_phases_only(self) -> None:
        durations = M.dry_run(ROOT)["phase_durations"]
        for phase in M.phase_plan():
            if phase.horizon == "converged":
                self.assertTrue(phase.key.endswith("@converged"))
                self.assertIn(phase.protocol_id, {p for p, _ in M.CHALLENGES.values()})
                self.assertEqual(durations[phase.key], 25.0)
            else:
                self.assertLess(durations[phase.key], 25.0)
        self.assertEqual(durations["ht_extension"], 2.0)

    def test_run_arm_is_never_used(self) -> None:
        # Section 4: run_arm(horizon_class="converged") sets every phase to 25.
        # The module may name it only in its docstring and comments.
        source = (ROOT / "src/dt_adoc/reporting/c3a_kinetic_readout.py").read_text(
            encoding="utf-8"
        )
        body = source.split('"""', 2)[2]
        code = [line for line in body.splitlines() if not line.lstrip().startswith("#")]
        self.assertEqual([line for line in code if "run_arm" in line], [])

    def test_anti_spp1_and_washout_are_out_of_scope(self) -> None:
        # Addendum 01: removed from C3a scope, not from the model or protocols.
        keys = {p.key for p in M.phase_plan()}
        protocols = {p.protocol_id for p in M.phase_plan()}
        self.assertFalse({k for k in keys if "anti_spp1" in k or "washout" in k})
        self.assertFalse({p for p in protocols if "anti_spp1" in p or "washout" in p})
        self.assertEqual(set(M.PAIRS), {"mifepristone", "hand2_loss"})
        self.assertEqual(set(M.UNMATCHED), {"mifepristone_vs_declared_twin"})
        self.assertTrue(
            (ROOT / M.MODEL_DIR / "conditions/hormone_treated_anti_spp1.cfg").is_file()
        )

    def test_the_perturbed_lineages_are_the_declared_ones(self) -> None:
        record = M.check_construction(ROOT)
        self.assertEqual(
            record["mifepristone"]["perturbed"][-2:],
            [
                "hormone_treated_mifepristone",
                "adhesion_challenge_hormone_treated_mifepristone",
            ],
        )
        self.assertEqual(
            record["mifepristone"]["control"][-2:],
            ["hormone_treated_maternal", "adhesion_challenge_hormone_treated"],
        )
        self.assertEqual(record["mifepristone"]["durations"], [1.0, 2.0, 4.0, 2.0, 1.0])
        self.assertEqual(record["hand2_loss"]["differing_phases"], [2, 3])


class TheSeedSpendingPathIsWiredAsPreregistered(unittest.TestCase):
    """Section 4 at the call sites run_block actually uses, with MaBoSS mocked.

    Pins, for every phase of a block: the protocol, the parent result the
    continuation is built from, seed_r, the trajectory count, and the horizon
    override (25.0 for converged challenges only, 2.0 for the HT extension,
    None, i.e. declared, for everything else).
    """

    def _run(self, count: int, replicate: int, drop_column: str | None = None):
        import pandas as pd

        from dt_adoc.simulation import runner

        runs: list[dict] = []
        continuations: list[dict] = []

        class Result:
            def __init__(self, protocol_id: str) -> None:
                self.protocol_id = protocol_id
                columns = {r: [0.0, 0.5] for r in M.READOUTS if r != drop_column}
                self.final_result = type(
                    "F", (), {"nodes_probtraj": pd.DataFrame(columns, index=[0.0, 0.1])}
                )()

        def fake_continuation(protocol_id, parent_result, *, model_version, root):
            token = ("continuation", protocol_id, id(parent_result))
            continuations.append(
                {
                    "protocol_id": protocol_id,
                    "parent": parent_result,
                    "model_version": model_version,
                    "token": token,
                }
            )
            return token

        def fake_run(
            protocol_id,
            *,
            model_version,
            root,
            continuation,
            seed,
            sample_count,
            phase_horizon,
        ):
            result = Result(protocol_id)
            runs.append(
                {
                    "protocol_id": protocol_id,
                    "continuation": continuation,
                    "seed": seed,
                    "sample_count": sample_count,
                    "phase_horizon": phase_horizon,
                    "model_version": model_version,
                    "result": result,
                }
            )
            return result

        with (
            mock.patch.object(runner, "run_protocol", side_effect=fake_run),
            mock.patch.object(
                runner, "protocol_continuation", side_effect=fake_continuation
            ),
        ):
            out = M.run_block(M.Task(count, replicate, str(ROOT)))
        return out, runs, continuations

    def test_every_phase_call_at_both_counts(self) -> None:
        for count, replicate in ((20_000, 0), (20_000, 19), (2_000, 7)):
            with self.subTest(count=count, replicate=replicate):
                out, runs, _ = self._run(count, replicate)
                plan = M.plan_for(count)
                self.assertEqual(len(runs), 14)
                self.assertEqual(
                    [r["protocol_id"] for r in runs], [p.protocol_id for p in plan]
                )
                result_of = {}
                for phase, call in zip(plan, runs, strict=True):
                    self.assertEqual(call["seed"], M.replicate_seed(replicate, count))
                    self.assertEqual(call["sample_count"], count)
                    self.assertEqual(call["model_version"], M.MODEL_VERSION)
                    if phase.horizon == "converged":
                        self.assertEqual(call["phase_horizon"], 25.0, phase.key)
                    elif phase.key == "ht_extension":
                        self.assertEqual(call["phase_horizon"], 2.0)
                    else:
                        self.assertIsNone(call["phase_horizon"], phase.key)
                    if phase.parent is None:
                        self.assertIsNone(call["continuation"])
                    else:
                        parent = result_of[phase.parent]
                        self.assertEqual(
                            call["continuation"],
                            ("continuation", phase.protocol_id, id(parent)),
                        )
                    result_of[phase.key] = call["result"]
                self.assertEqual(out["seed"], M.replicate_seed(replicate, count))
                self.assertEqual(set(out["series"]), {p.key for p in plan})

    def test_the_declared_and_converged_challenge_share_one_parent_state(self) -> None:
        _, _runs, continuations = self._run(20_000, 3)
        by_protocol = {}
        for c in continuations:
            by_protocol.setdefault(c["protocol_id"], []).append(id(c["parent"]))
        for protocol_id, _ in M.CHALLENGES.values():
            parents = by_protocol[protocol_id]
            # twin and control_ext share a protocol but not a parent; each arm
            # runs twice (declared, converged) from the same parent object.
            for parent in set(parents):
                self.assertEqual(parents.count(parent), 2, protocol_id)

    def test_only_25_and_the_extension_ever_override_a_declared_duration(self) -> None:
        _, runs, _ = self._run(2_000, 0)
        overrides = sorted(
            {r["phase_horizon"] for r in runs if r["phase_horizon"] is not None}
        )
        self.assertEqual(overrides, [2.0, 25.0])
        self.assertEqual(sum(r["phase_horizon"] == 25.0 for r in runs), 4)
        self.assertEqual(sum(r["phase_horizon"] == 2.0 for r in runs), 1)

    def test_a_missing_readout_column_fails_loudly_never_as_a_zero(self) -> None:
        with self.assertRaises(KeyError):
            self._run(20_000, 0, drop_column=M.PRIMARY_READOUT)


class TheConstructionCheckRefuses(unittest.TestCase):
    def test_a_wrong_differing_input(self) -> None:
        wrong = {
            **M.PAIRS,
            "mifepristone": ("control_ext", "mifepristone", "IN_HAND2_LOSS"),
        }
        with mock.patch.dict(M.PAIRS, wrong), self.assertRaises(ValueError):
            M.check_construction(ROOT)

    def test_an_unmatched_control(self) -> None:
        wrong = {**M.PAIRS, "mifepristone": ("twin", "mifepristone", "IN_MIFEPRISTONE")}
        with mock.patch.dict(M.PAIRS, wrong), self.assertRaises(ValueError):
            M.check_construction(ROOT)

    def test_condition_files_that_differ_in_another_line(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp, "a.cfg"), Path(tmp, "b.cfg")
            a.write_text(
                "IN_X.istate = FALSE;\nIN_Y.istate = FALSE;\n", encoding="utf-8"
            )
            b.write_text("IN_X.istate = TRUE;\nIN_Y.istate = TRUE;\n", encoding="utf-8")
            removed, added = M._changed_cfg_lines(a, b)
            self.assertEqual(len(added), 2)
            self.assertFalse(all("IN_X" in line for line in (*removed, *added)))


@_HISTORY_PREREG
class TheBindingRefuses(unittest.TestCase):
    def test_bound_paths_cover_the_model_protocols_and_preregistration(self) -> None:
        paths = M.bound_paths(ROOT)
        for p in (
            "config/protocols.yaml",
            "models/specs/parameter_scenarios.yaml",
            str(M.PREREGISTRATION),
            str(M.ADDENDUM),
            f"{M.MODEL_DIR}/network.bnd",
            f"{M.MODEL_DIR}/baseline.cfg",
            f"{M.MODEL_DIR}/conditions/adhesion_challenge_hormone_treated_anti_spp1.cfg",
        ):
            self.assertIn(p, paths)

    def test_a_bound_file_that_differs_from_the_preregistration_commit(self) -> None:
        import subprocess

        real = subprocess.run

        def fake(args, **kwargs):
            if args[:2] == ["git", "show"] and args[2].endswith(
                "config/protocols.yaml"
            ):
                return subprocess.CompletedProcess(
                    args, 0, stdout=b"changed", stderr=b""
                )
            return real(args, **kwargs)

        with (
            mock.patch.object(M.subprocess, "run", side_effect=fake),
            self.assertRaisesRegex(RuntimeError, "protocols.yaml differs"),
        ):
            M.bind_inputs(ROOT)


def _band(low: float, high: float) -> dict[str, float]:
    return {
        "mean": (low + high) / 2,
        "sd": 0.0,
        "se": (high - low) / 2 / M.T19,
        "low": low,
        "high": high,
    }


class Classification(unittest.TestCase):
    def test_labels_at_the_boundaries(self) -> None:
        self.assertEqual(M.label(_band(-0.02, -0.0051)), M.SUPPRESSED)
        self.assertEqual(M.label(_band(-0.02, -0.005)), M.NEITHER)
        self.assertEqual(M.label(_band(-0.005, 0.005)), M.EQUIVALENT)
        self.assertEqual(M.label(_band(0.0051, 0.02)), M.INCREASED)
        self.assertEqual(M.label(M.band([0.0] * 20)), M.EQUIVALENT)

    def test_the_table(self) -> None:
        S, E, I, N = M.SUPPRESSED, M.EQUIVALENT, M.INCREASED, M.NEITHER
        self.assertEqual(M.kinetic_class(S, E), (M.PERSISTENT, []))
        self.assertEqual(M.kinetic_class(S, I), (M.PERSISTENT, []))
        self.assertEqual(M.kinetic_class(E, S), (M.TRANSIENT, []))
        self.assertEqual(M.kinetic_class(E, E), (M.NO_DIFFERENCE, []))
        self.assertEqual(M.kinetic_class(E, N), (M.INDETERMINATE, []))
        self.assertEqual(
            M.kinetic_class(I, E), (M.INDETERMINATE, ["material increase"])
        )
        self.assertEqual(M.kinetic_class(N, S), (M.INDETERMINATE, []))

    def test_band_formula(self) -> None:
        b = M.band([1.0, 2.0, 3.0])
        self.assertAlmostEqual(b["high"] - b["mean"], M.T19 * 1.0 / 3**0.5)

    def test_count_records(self) -> None:
        governing = {"mean": -0.010, "se": 0.0005, "low": -0.0115, "high": -0.0085}
        same = {"mean": -0.010, "se": 0.0010, "low": -0.0130, "high": -0.0070}
        wider = {"mean": -0.009, "se": 0.0020, "low": -0.0150, "high": -0.0030}
        shifted = {"mean": 0.010, "se": 0.0010, "low": 0.0070, "high": 0.0130}
        self.assertEqual(M.count_record(governing, same), M.STABLE)
        self.assertEqual(M.count_record(governing, wider), M.LOW_COUNT)
        self.assertEqual(M.count_record(governing, shifted), M.COUNT_SENSITIVE)


class LabelsFollowThePreregistration(unittest.TestCase):
    """B10: section 10 compares three labels; section 9 makes an increase a
    descriptive direction, never a label of its own."""

    def test_the_section_10_wording_names_three_labels(self) -> None:
        self.assertIn(
            "- The labels compared are materially suppressed, equivalent or neither\n"
            "  (section 9).",
            PREREG,
        )
        self.assertIn('descriptive sub-label ("material increase")', PREREG)

    def test_a_governing_increase_with_a_compatible_check_neither_is_stable(
        self,
    ) -> None:
        governing = {"mean": 0.013, "se": 0.0020, "low": 0.006, "high": 0.020}
        check = {"mean": 0.012, "se": 0.0027, "low": 0.004, "high": 0.020}
        self.assertEqual(M.label(governing), M.INCREASED)
        self.assertEqual(M.label(check), M.NEITHER)
        self.assertEqual(M.count_record(governing, check), M.STABLE)

    def test_every_label_value_maps_to_a_section_10_label(self) -> None:
        bands = {
            M.SUPPRESSED: _band(-0.02, -0.01),
            M.EQUIVALENT: _band(-0.001, 0.001),
            M.INCREASED: _band(0.01, 0.02),
            M.NEITHER: _band(-0.01, 0.01),
        }
        self.assertEqual({M.label(b) for b in bands.values()}, set(bands))
        section_10 = {M.SUPPRESSED, M.EQUIVALENT, M.NEITHER}
        for value, b in bands.items():
            with self.subTest(label=value):
                self.assertIn(M.count_label(b), section_10)
                expected = M.NEITHER if value == M.INCREASED else value
                self.assertEqual(M.count_label(b), expected)

    def test_an_increase_is_never_a_class_of_its_own(self) -> None:
        for fixed_point in (M.SUPPRESSED, M.EQUIVALENT, M.INCREASED, M.NEITHER):
            for window in (M.SUPPRESSED, M.EQUIVALENT, M.INCREASED, M.NEITHER):
                cls, sub = M.kinetic_class(fixed_point, window)
                with self.subTest(fixed_point=fixed_point, window=window):
                    self.assertIn(
                        cls,
                        {M.PERSISTENT, M.TRANSIENT, M.NO_DIFFERENCE, M.INDETERMINATE},
                    )
                    if (
                        M.INCREASED in (fixed_point, window)
                        and fixed_point != M.SUPPRESSED
                    ):
                        self.assertEqual(
                            (cls, sub), (M.INDETERMINATE, ["material increase"])
                        )


def _fake_results(effect: dict[str, tuple[float, float]]) -> list[dict]:
    """Blocks where each perturbed arm is its control plus (declared, converged) shifts."""
    rng = random.Random(0)
    durations = {p.key: round(M.phase_duration(ROOT, p) * 10) for p in M.phase_plan()}
    results = []
    for count in M.TRAJECTORY_COUNTS:
        for r in range(M.REPLICATES):
            series = {}
            for phase in M.plan_for(count):
                # Exclusive endpoint, as the v0.5.2 runner records it: 0.0 .. duration - tick.
                n = durations[phase.key]
                base = [0.5] * n
                series[phase.key] = {
                    "times": [i / 10 for i in range(n)],
                    **{x: list(base) for x in M.READOUTS},
                }
            for pair, (control, perturbed, _) in M.PAIRS.items():
                declared, converged = effect.get(pair, (0.0, 0.0))
                noise = rng.gauss(0, 0.0002)
                for x in M.READOUTS:
                    series[f"{perturbed}@declared"][x] = [0.5 + declared + noise] * 10
                    series[f"{perturbed}@converged"][x] = [
                        0.5 + converged + noise
                    ] * 250
            results.append(
                {
                    "trajectory_count": count,
                    "replicate": r,
                    "seed": M.replicate_seed(r, count),
                    "series": series,
                }
            )
    return results


class Compare(unittest.TestCase):
    def test_synthetic_classes(self) -> None:
        out = M.compare(
            _fake_results({"mifepristone": (-0.05, 0.0), "hand2_loss": (-0.3, -0.5)})
        )
        classes = {(r["pair"], r["readout"]): r for r in out["classes"]}
        self.assertEqual(
            classes[("mifepristone", M.PRIMARY_READOUT)]["class"], M.TRANSIENT
        )
        self.assertEqual(
            classes[("hand2_loss", M.PRIMARY_READOUT)]["class"], M.PERSISTENT
        )
        self.assertIn(
            M.SOME_OCCUPANCY, classes[("hand2_loss", M.PRIMARY_READOUT)]["sub_labels"]
        )
        self.assertEqual(len(out["classes"]), 4)
        none = M.compare(_fake_results({}))
        self.assertEqual({r["class"] for r in none["classes"]}, {M.NO_DIFFERENCE})
        kinds = {r["kind"] for r in out["bands"]}
        self.assertEqual(kinds, {"classified", "schedule_unmatched_descriptive"})
        self.assertTrue(
            all(
                r["label"] == "not_classified"
                for r in out["bands"]
                if r["kind"] != "classified"
            )
        )

    def test_zero_occupancy_sub_label(self) -> None:
        results = _fake_results({"mifepristone": (-0.5, -0.5)})
        out = M.compare(results)
        row = next(
            r
            for r in out["classes"]
            if r["pair"] == "mifepristone" and r["readout"] == M.PRIMARY_READOUT
        )
        self.assertIn(M.SOME_OCCUPANCY, row["sub_labels"])
        governing = [
            b for b in results if b["trajectory_count"] == M.GOVERNING_TRAJECTORIES
        ]
        for b in governing:
            b["series"]["mifepristone@converged"][M.PRIMARY_READOUT] = [0.0] * 250
        self.assertEqual(
            M.zero_occupancy(governing, "mifepristone", M.PRIMARY_READOUT),
            M.ZERO_OCCUPANCY,
        )

    def test_a_missing_block_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            M.compare(_fake_results({})[1:])


# ---------------------------------------------------------------------------
# Review repairs: B1 (attempt journal), B2 (complete binding), manifest.


def _tasks() -> list:
    return M.task_list(ROOT)


def _sequential(fn, tasks):
    return [fn(t) for t in tasks]


def _accept(status):
    """A validator stub for journal-mechanics tests; the real one is tested below."""
    return []


def _ok(task):
    return {"trajectory_count": task.trajectory_count, "replicate": task.replicate}


class AttemptJournal(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _journals(self) -> list[dict]:
        import json

        return [
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((self.root / M.JOURNAL_DIR).glob("*.json"))
        ]

    def test_a_worker_failure_is_journaled_with_every_dispatched_seed_as_spent(
        self,
    ) -> None:
        calls = []

        def failing(task):
            calls.append(task)
            if len(calls) == 3:
                raise RuntimeError("injected MaBoSS failure")
            return _ok(task)

        with self.assertRaisesRegex(RuntimeError, "injected MaBoSS failure"):
            M.execute_attempt(
                self.root,
                _tasks(),
                {"start_head": "x"},
                failing,
                _sequential,
                lambda results, journal: {},
                _accept,
            )
        (record,) = self._journals()
        self.assertEqual(record["status"], "FAILED")
        self.assertEqual(record["error"]["message"], "injected MaBoSS failure")
        self.assertIn("Traceback", record["error"]["traceback"])
        self.assertEqual(record["provenance_at_start"], {"start_head": "x"})
        self.assertEqual(len(record["spent_seed_ranges"]), 40)
        self.assertIn(
            {"trajectory_count": 20000, "replicate": 0, "seeds": [2000001, 2020000]},
            record["spent_seed_ranges"],
        )

    def test_a_retry_after_a_failure_refuses_to_reuse_the_seeds(self) -> None:
        def failing(task):
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            M.execute_attempt(
                self.root, _tasks(), {}, failing, _sequential, lambda r, j: {}, _accept
            )
        with self.assertRaisesRegex(M.SeedReuseError, "dated addendum"):
            M.execute_attempt(
                self.root, _tasks(), {}, failing, _sequential, lambda r, j: {}, _accept
            )
        self.assertEqual(len(self._journals()), 1)

    def test_a_finalisation_failure_is_journaled_too(self) -> None:
        def bad_finalize(results, journal):
            raise RuntimeError(
                "C3a run invalid: a bound or generator file changed during the run"
            )

        with self.assertRaises(RuntimeError):
            M.execute_attempt(
                self.root, _tasks(), {}, _ok, _sequential, bad_finalize, _accept
            )
        (record,) = self._journals()
        self.assertEqual(record["status"], "FAILED")
        self.assertEqual(len(record["completed_blocks"]), 40)

    def test_a_completed_attempt_also_reserves_its_seeds(self) -> None:
        M.execute_attempt(
            self.root,
            _tasks(),
            {},
            _ok,
            _sequential,
            lambda r, j: {"outputs_sha256": {"a": "b"}},
            _accept,
        )
        self.assertEqual(self._journals()[0]["status"], "COMPLETED")
        with self.assertRaises(M.SeedReuseError):
            M.execute_attempt(
                self.root, _tasks(), {}, _ok, _sequential, lambda r, j: {}, _accept
            )


class DurableJournal(unittest.TestCase):
    def test_the_rename_is_followed_by_a_directory_fsync(self) -> None:
        import os
        import stat
        import tempfile

        synced: list[str] = []
        real = os.fsync

        def recording(fd):
            synced.append("dir" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
            return real(fd)

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(os, "fsync", recording),
            mock.patch.object(os, "replace", wraps=os.replace) as replace,
        ):
            path = Path(tmp) / "attempts" / "attempt_x.json"
            M._write_json_durably(path, {"a": 1})
            self.assertEqual(replace.call_count, 1)
        # The parent created (its parent synced), the file synced, then after the
        # rename the directory holding the journal synced.
        self.assertEqual(synced, ["dir", "file", "dir"])

    def test_an_existing_directory_still_gets_the_post_rename_fsync(self) -> None:
        import os
        import stat
        import tempfile

        synced: list[str] = []
        real = os.fsync

        def recording(fd):
            synced.append("dir" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
            return real(fd)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "attempt_x.json"
            with mock.patch.object(os, "fsync", recording):
                M._write_json_durably(path, {"a": 1})
        self.assertEqual(synced, ["file", "dir"])


class DurableReservationPath(unittest.TestCase):
    """B6: the real reserve_attempt path, starting with no journal directory."""

    def _record(self, synced):
        import os
        import stat

        real = os.fsync

        def recording(fd):
            kind = "dir" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file"
            synced.append((Path(os.readlink(f"/proc/self/fd/{fd}")), kind))
            return real(fd)

        return recording

    def test_every_created_level_is_fsynced_in_its_container_before_the_reservation_returns(
        self,
    ) -> None:
        import os
        import tempfile

        synced: list[tuple[Path, str]] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            journal_dir = root / M.JOURNAL_DIR
            self.assertFalse(journal_dir.exists())
            with mock.patch.object(os, "fsync", self._record(synced)):
                path = M.reserve_attempt(root, _tasks(), {})
            self.assertTrue(path.is_file())
        # docs/, docs/c3_kinetic_readouts/ and attempts/ are created, each followed
        # by an fsync of the directory containing it; then the journal file; then
        # the attempts/ directory holding the renamed journal.
        self.assertEqual(
            synced,
            [
                (root, "dir"),
                (root / "docs", "dir"),
                (root / "docs" / "c3_kinetic_readouts", "dir"),
                (path.with_suffix(".tmp"), "file"),
                (journal_dir, "dir"),
            ],
        )
        # The container of the newly created journal directory is flushed before
        # the journal itself is written.
        container = synced.index((journal_dir.parent, "dir"))
        self.assertLess(container, synced.index((path.with_suffix(".tmp"), "file")))

    def test_an_existing_journal_directory_needs_no_creation_fsync(self) -> None:
        import os
        import tempfile

        synced: list[tuple[Path, str]] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / M.JOURNAL_DIR).mkdir(parents=True)
            with mock.patch.object(os, "fsync", self._record(synced)):
                path = M.reserve_attempt(root, _tasks(), {})
        self.assertEqual(
            synced, [(path.with_suffix(".tmp"), "file"), (root / M.JOURNAL_DIR, "dir")]
        )

    def test_a_concurrently_created_level_still_fsyncs_its_container(self) -> None:
        import os
        import tempfile

        synced: list[tuple[Path, str]] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            target = root / "a" / "b"
            real_mkdir = Path.mkdir

            def racing_mkdir(self_path, *args, **kwargs):
                real_mkdir(self_path, *args, **kwargs)  # another process wins
                raise FileExistsError(str(self_path))

            with (
                mock.patch.object(Path, "mkdir", racing_mkdir),
                mock.patch.object(os, "fsync", self._record(synced)),
            ):
                M.ensure_durable_directory(target)
            self.assertTrue(target.is_dir())
        self.assertEqual(synced, [(root, "dir"), (root / "a", "dir")])


@_HISTORY_PREREG
class CompleteBinding(unittest.TestCase):
    INDIRECT = "src/dt_adoc/maboss_adapter.py"

    def test_indirect_numerical_dependencies_are_bound(self) -> None:
        deps = M.execution_dependencies(ROOT)
        for path in (
            self.INDIRECT,
            "src/dt_adoc/model/runtime.py",
            "src/dt_adoc/simulation/runner.py",
            "src/dt_adoc/simulation/manifests.py",
            "src/dt_adoc/reporting/c3a_kinetic_readout.py",
            "src/dt_adoc/calibration/observation_map.py",
        ):
            self.assertIn(path, deps)
        self.assertEqual(set(M.input_hashes(ROOT)["generator"]), set(deps))

    def test_mutating_an_indirect_dependency_invalidates_the_binding(self) -> None:
        with _disposable_clone() as clone:
            target = clone / self.INDIRECT
            before = M.input_hashes(clone)["generator"][self.INDIRECT]
            self.assertEqual(
                before, M.input_hashes(ROOT, "HEAD")["generator"][self.INDIRECT]
            )
            M.bind_inputs(
                clone
            )  # the unmutated clone binds, so the refusal below is the probe's
            target.write_bytes(target.read_bytes() + b"\n# c3a binding probe\n")
            self.assertNotEqual(
                M.input_hashes(clone)["generator"][self.INDIRECT], before
            )
            with self.assertRaisesRegex(RuntimeError, "maboss_adapter.py"):
                M.bind_inputs(clone)


class ConcurrentReservation(unittest.TestCase):
    """Two attempts that race must not both reserve the same seeds."""

    def test_only_one_of_two_racing_attempts_reserves(self) -> None:
        import tempfile
        import threading
        import time

        real = M.reserved_ranges

        def slow_read(root):
            # Widen the window between reading reservations and writing one:
            # without the lock both racers would read "none" here.
            found = real(root)
            time.sleep(0.3)
            return found

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outcomes: list[str] = []

            def attempt() -> None:
                try:
                    M.reserve_attempt(root, _tasks(), {})
                    outcomes.append("reserved")
                except M.SeedReuseError:
                    outcomes.append("refused")

            with mock.patch.object(M, "reserved_ranges", side_effect=slow_read):
                racers = [threading.Thread(target=attempt) for _ in range(3)]
                for t in racers:
                    t.start()
                for t in racers:
                    t.join()
            self.assertEqual(sorted(outcomes), ["refused", "refused", "reserved"])
            self.assertEqual(
                len(list((root / M.JOURNAL_DIR).glob("attempt_*.json"))), 1
            )

    def test_the_lock_is_what_serialises_them(self) -> None:
        # Regression guard: with the lock disabled the same race double-reserves,
        # so the test above is not passing by luck.
        import tempfile
        import threading
        import time

        real = M.reserved_ranges

        def slow_read(root):
            found = real(root)
            time.sleep(0.3)
            return found

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            import fcntl

            with (
                mock.patch.object(M, "reserved_ranges", side_effect=slow_read),
                mock.patch.object(fcntl, "flock", lambda *args: None),
            ):
                racers = [
                    threading.Thread(
                        target=M.reserve_attempt, args=(root, _tasks(), {})
                    )
                    for _ in range(2)
                ]
                for t in racers:
                    t.start()
                for t in racers:
                    t.join()
            self.assertEqual(
                len(list((root / M.JOURNAL_DIR).glob("attempt_*.json"))), 2
            )


# ---------------------------------------------------------------------------
# B7-B9: one canonical fixture built by the real finalisation path, from real
# git objects, a real journal and real output files. Only MaBoSS is replaced:
# the blocks are synthetic, and the end-of-run hash check reads HEAD, so the
# fixture does not depend on the developer's working tree being clean.


def _git_out(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


@contextlib.contextmanager
def _disposable_clone() -> Iterator[Path]:
    """A throwaway checkout of HEAD that shares this repository's objects.

    For the probes that must mutate a package file: mutating ROOT exposes the
    probe to anything reading the checkout meanwhile (a concurrent session, an
    AIH snapshot, a generator stamping an implementation digest), and a killed
    run leaves it behind. ``bind_inputs`` is driven by git, so a copy without a
    repository would not exercise it. The pre-registration commits stay
    reachable through the shared object store.
    """
    head = _git_out("rev-parse", "HEAD")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "clone"
        for command in (
            [
                "git",
                "clone",
                "--quiet",
                "--shared",
                "--no-checkout",
                str(ROOT),
                str(clone),
            ],
            ["git", "-C", str(clone), "checkout", "--quiet", "--detach", head],
        ):
            subprocess.run(command, check=True, capture_output=True, env=env)
        yield clone


def _build_canonical(root: Path) -> None:
    import functools
    import time

    head = _git_out("rev-parse", "HEAD")
    binding = {
        "prereg_commit": M.PREREG_COMMIT,
        "addendum_commit": M.ADDENDUM_COMMIT,
        "start_head": head,
        "start_tree": _git_out("rev-parse", "HEAD^{tree}"),
        "start_dirty_paths": [],
        "input_sha256_at_start": M.input_hashes(ROOT, head),
    }
    # P(ON) must stay within [0, 1] under the noise, so the effect is -0.45.
    results = _fake_results({"mifepristone": (-0.05, 0.0), "hand2_loss": (-0.3, -0.45)})
    for r in results:
        r["warnings"] = ["DeprecationWarning: synthetic"]
    real = M.input_hashes
    with mock.patch.object(
        M, "input_hashes", side_effect=lambda r, commit=None: real(r, commit or head)
    ):
        M.execute_attempt(
            root,
            M.task_list(ROOT),
            binding,
            None,
            lambda fn, tasks: results,
            M._finalize(root, ROOT, binding, 3, time.time()),
            functools.partial(M.validate_manifest, root, ROOT),
        )


@_HISTORY_PREREG
class _Canonical(unittest.TestCase):
    """Each test gets a fresh copy of one canonical result built once."""

    @classmethod
    def setUpClass(cls) -> None:
        import tempfile

        cls._master = tempfile.TemporaryDirectory()
        _build_canonical(Path(cls._master.name))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._master.cleanup()

    def setUp(self) -> None:
        import shutil
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "r"
        shutil.copytree(self._master.name, self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def manifest(self) -> dict:
        import json

        return json.loads((self.root / M.SETTINGS_JSON).read_text(encoding="utf-8"))

    def journal_path(self) -> Path:
        return self.root / M.JOURNAL_DIR / f"{self.manifest()['attempt_id']}.json"

    def journal(self) -> dict:
        import json

        return json.loads(self.journal_path().read_text(encoding="utf-8"))

    def write_journal(self, record: dict) -> None:
        import json

        self.journal_path().write_text(json.dumps(record), encoding="utf-8")

    def problems(self, manifest: dict | None = None) -> list[str]:
        return M.manifest_problems(
            self.manifest() if manifest is None else manifest, self.root, ROOT
        )


class CanonicalResult(_Canonical):
    def test_the_real_finalisation_path_produces_a_valid_completed_result(self) -> None:
        self.assertEqual(M.validate_manifest(self.root, ROOT), [])
        self.assertEqual(self.journal()["status"], M.COMPLETED)
        self.assertEqual(set(self.manifest()), M.MANIFEST_FIELDS)
        self.assertEqual(self.manifest()["environment"]["maboss"], "0.8.15")

    def test_the_schema_is_closed_and_partitioned(self) -> None:
        self.assertFalse(M.RECONSTRUCTED_FIELDS & M.RUN_VARYING_FIELDS)
        extra = {**self.manifest(), "unlisted_field": 1}
        self.assertTrue(self.problems(extra))
        missing = {k: v for k, v in self.manifest().items() if k != "delta"}
        self.assertTrue(self.problems(missing))


def _perturb(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value + 1
    if isinstance(value, str):
        return value + "x"
    if isinstance(value, list):
        return [*value, "mutated"]
    if isinstance(value, dict):
        return {**value, "mutated": 1}
    raise TypeError(type(value))


class EveryFieldIsValidated(_Canonical):
    #: One invalid value per run-varying field; each has its own rule.
    RUN_VARYING_INVALID: ClassVar[dict[str, object]] = {
        "attempt_id": "attempt_20990101T000000000000Z",
        "binding": "replace start_head with a nonexistent commit",
        "input_sha256_at_end": {"bound": {"x": "0"}, "generator": {"y": "0"}},
        "workers": 0,
        "environment": "drop python",
        "warnings": {"UserWarning: x": 0},
        "errors": ["worker died"],
        "elapsed_seconds": -1.0,
    }

    def test_every_reconstructed_field_rejects_a_mutation(self) -> None:
        for field in sorted(M.RECONSTRUCTED_FIELDS):
            with self.subTest(field=field):
                manifest = self.manifest()
                manifest[field] = _perturb(manifest[field])
                self.assertTrue(self.problems(manifest), field)

    def test_the_class_summary_is_checked_against_classification_tsv(self) -> None:
        manifest = self.manifest()
        key = next(iter(manifest["classes"]))
        manifest["classes"][key] = (
            M.NO_DIFFERENCE
            if manifest["classes"][key] != M.NO_DIFFERENCE
            else M.PERSISTENT
        )
        self.assertIn(
            "classes does not match its reconstruction", self.problems(manifest)
        )

    def test_every_run_varying_field_has_a_rule_that_rejects_an_invalid_value(
        self,
    ) -> None:
        self.assertEqual(set(self.RUN_VARYING_INVALID), M.RUN_VARYING_FIELDS)
        for field, invalid in self.RUN_VARYING_INVALID.items():
            with self.subTest(field=field):
                manifest = self.manifest()
                if field == "binding":
                    manifest["binding"] = {
                        **manifest["binding"],
                        "start_head": "0" * 40,
                    }
                elif field == "environment":
                    manifest["environment"] = {
                        k: v
                        for k, v in manifest["environment"].items()
                        if k != "python"
                    }
                else:
                    manifest[field] = invalid
                self.assertTrue(self.problems(manifest), field)


@_HISTORY_PREREG
@_HISTORY_PARENT
class BindingResolvesThroughGit(_Canonical):
    def _with_binding(self, **changes) -> list[str]:
        manifest = self.manifest()
        manifest["binding"] = {**manifest["binding"], **changes}
        return self.problems(manifest)

    def test_nonexistent_but_well_formed_ids_fail(self) -> None:
        problems = self._with_binding(start_head="1" * 40, start_tree="2" * 40)
        self.assertTrue(any("does not resolve to a commit" in p for p in problems))

    def test_a_real_commit_with_the_wrong_tree_fails(self) -> None:
        other = _git_out("rev-parse", "HEAD~1^{tree}")
        problems = self._with_binding(start_tree=other)
        self.assertTrue(
            any("start_tree is not the tree of start_head" in p for p in problems)
        )

    def test_a_real_commit_with_fabricated_self_consistent_hashes_fails(self) -> None:
        fake = {
            "bound": {"config/protocols.yaml": "0" * 64},
            "generator": {"x.py": "1" * 64},
        }
        manifest = self.manifest()
        manifest["binding"] = {**manifest["binding"], "input_sha256_at_start": fake}
        manifest["input_sha256_at_end"] = fake
        problems = self.problems(manifest)
        self.assertTrue(
            any(
                "do not match the files at start_head" in p
                or "does not match the files at start_head" in p
                for p in problems
            )
        )

    def test_a_real_commit_that_predates_the_addendum_fails_cleanly(self) -> None:
        # 0c7da9c is real, but it lacks addendum 01, a bound file: a problem, not a crash.
        old = M.PREREG_COMMIT
        problems = self._with_binding(
            start_head=old, start_tree=_git_out("rev-parse", f"{old}^{{tree}}")
        )
        self.assertTrue(any("malformed" in p or "start_head" in p for p in problems))

    def test_a_dirty_bound_file_at_start_fails(self) -> None:
        problems = self._with_binding(start_dirty_paths=[" M config/protocols.yaml"])
        self.assertTrue(any("dirty at start" in p for p in problems))


class JournalIsPartOfTheResult(_Canonical):
    def _journal_with(self, **changes) -> list[str]:
        record = self.journal()
        record.update(changes)
        self.write_journal(record)
        return self.problems()

    def test_a_result_without_its_journal_fails(self) -> None:
        self.journal_path().unlink()
        self.assertTrue(any("is missing" in p for p in self.problems()))

    def test_a_non_terminal_status_fails(self) -> None:
        self.assertTrue(self._journal_with(status=M.FINALIZING))

    def test_altered_ranges_and_blocks_fail(self) -> None:
        record = self.journal()
        for field in ("reserved_seed_ranges", "spent_seed_ranges", "completed_blocks"):
            with self.subTest(field=field):
                self.write_journal({**record, field: record[field][:-1]})
                self.assertTrue(self.problems(), field)
        self.write_journal(record)
        self.assertEqual(self.problems(), [])

    def test_journal_output_hashes_must_match(self) -> None:
        record = self.journal()
        outputs = {**record["outputs_sha256"], str(M.CLASSES_TSV): "0" * 64}
        self.assertTrue(self._journal_with(outputs_sha256=outputs))

    def test_a_malformed_journal_is_a_problem_not_a_crash(self) -> None:
        record = self.journal()
        self.write_journal({**record, "reserved_seed_ranges": ["not a range"]})
        self.assertTrue(
            any("malformed" in p or "reserved" in p for p in self.problems())
        )
        self.journal_path().write_text("{not json", encoding="utf-8")
        self.assertTrue(any("malformed" in p for p in self.problems()))

    def test_journal_provenance_must_be_the_manifest_binding(self) -> None:
        self.assertTrue(self._journal_with(provenance_at_start={"start_head": "x"}))


class OutputsAreOneDerivation(_Canonical):
    """An edited table with every hash updated to match must still fail."""

    def _rehash_everything(self) -> None:
        import json

        outputs = {str(p): M._sha((self.root / p).read_bytes()) for p in M.OUTPUTS}
        manifest = {
            **self.manifest(),
            "outputs_sha256": outputs,
            "classes": M._classes_from_tsv(self.root),
        }
        (self.root / M.SETTINGS_JSON).write_text(json.dumps(manifest), encoding="utf-8")
        self.write_journal({**self.journal(), "outputs_sha256": outputs})

    def _edit(self, path: Path, old: str, new: str) -> None:
        text = (self.root / path).read_text(encoding="utf-8")
        self.assertIn(old, text)
        (self.root / path).write_text(text.replace(old, new, 1), encoding="utf-8")

    def test_an_edited_class_with_consistent_hashes_fails(self) -> None:
        self._edit(M.CLASSES_TSV, M.TRANSIENT, M.PERSISTENT)
        self._rehash_everything()
        self.assertIn(
            "classification.tsv is not the derivation of blocks.tsv and curves.tsv",
            self.problems(),
        )

    def test_an_edited_band_with_consistent_hashes_fails(self) -> None:
        self._edit(M.BANDS_TSV, "\tequivalent", "\tmaterially_suppressed")
        self._rehash_everything()
        self.assertIn("bands.tsv is not the derivation of blocks.tsv", self.problems())

    def test_an_edited_block_value_with_consistent_hashes_fails(self) -> None:
        rows = (self.root / M.BLOCKS_TSV).read_text(encoding="utf-8").splitlines()
        cells = rows[1].split("\t")
        cells[-1] = repr(float(cells[-1]) - 0.5)
        rows[1] = "\t".join(cells)
        (self.root / M.BLOCKS_TSV).write_text("\n".join(rows) + "\n", encoding="utf-8")
        self._rehash_everything()
        self.assertTrue(any("derivation" in p for p in self.problems()))

    def test_a_dropped_block_fails(self) -> None:
        rows = (self.root / M.BLOCKS_TSV).read_text(encoding="utf-8").splitlines()
        (self.root / M.BLOCKS_TSV).write_text(
            "\n".join(rows[:-1]) + "\n", encoding="utf-8"
        )
        self._rehash_everything()
        self.assertTrue(any("pre-registered contrasts" in p for p in self.problems()))

    def test_zero_occupancy_from_curves_agrees_with_the_raw_definition(self) -> None:
        results = _fake_results({})
        governing = [
            b for b in results if b["trajectory_count"] == M.GOVERNING_TRAJECTORIES
        ]
        for b in governing:
            b["series"]["mifepristone@converged"][M.PRIMARY_READOUT] = [0.0] * 250
        _, curves = M._blocks_and_curves(results)
        for arm in ("mifepristone", "hand2_loss"):
            self.assertEqual(
                M._zero_occupancy_from_curves(curves, arm, M.PRIMARY_READOUT),
                M.zero_occupancy(governing, arm, M.PRIMARY_READOUT),
            )


class StageOneSchemasAreClosed(_Canonical):
    """B12: every metadata column of blocks.tsv and curves.tsv is checked."""

    def _rehash_everything(self) -> None:
        OutputsAreOneDerivation._rehash_everything(self)

    def _mutate_cell(
        self, path: Path, column: str, value: str, row: int = 1
    ) -> list[str]:
        lines = (self.root / path).read_text(encoding="utf-8").splitlines()
        header = lines[0].split("\t")
        cells = lines[row].split("\t")
        cells[header.index(column)] = value
        lines[row] = "\t".join(cells)
        (self.root / path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        self._rehash_everything()
        return self.problems()

    def test_every_blocks_metadata_column_is_checked(self) -> None:
        replacements = {
            "contrast": "hand2_loss",
            "kind": "schedule_unmatched_descriptive",
            "readout": M.SECONDARY_READOUT,
            "trajectory_count": "2000",
            "replicate": "7",
            "seed": "2000002",
            "estimand": "fixed_point",
        }
        self.assertEqual(set(replacements), set(M.BLOCK_COLUMNS[:-1]))
        original = (self.root / M.BLOCKS_TSV).read_text(encoding="utf-8")
        for column, value in replacements.items():
            with self.subTest(column=column):
                (self.root / M.BLOCKS_TSV).write_text(original, encoding="utf-8")
                problems = self._mutate_cell(M.BLOCKS_TSV, column, value)
                self.assertTrue(any("blocks.tsv" in p for p in problems), column)

    def test_every_curves_metadata_column_is_checked(self) -> None:
        replacements = {
            "phase": "twin@declared",
            "protocol_id": "e2_primed_maternal",
            "horizon": "converged",
            "readout": M.SECONDARY_READOUT,
            "time": "0.05",
        }
        self.assertEqual(set(replacements), set(M.CURVE_COLUMNS[:5]))
        original = (self.root / M.CURVES_TSV).read_text(encoding="utf-8")
        for column, value in replacements.items():
            with self.subTest(column=column):
                (self.root / M.CURVES_TSV).write_text(original, encoding="utf-8")
                problems = self._mutate_cell(M.CURVES_TSV, column, value, row=2)
                self.assertTrue(any("curves.tsv" in p for p in problems), column)

    def test_out_of_range_curve_values_are_refused(self) -> None:
        self.assertTrue(
            any(
                "out-of-range" in p
                for p in self._mutate_cell(M.CURVES_TSV, "mean_p_on", "1.5")
            )
        )

    def test_a_truncated_curve_prefix_fails(self) -> None:
        # B13: keep only the first two ticks of a 25.0 converged phase.
        lines = (self.root / M.CURVES_TSV).read_text(encoding="utf-8").splitlines()
        header, rows = lines[0], lines[1:]
        target = "hand2_loss@converged\t"
        kept, seen = [], {}
        for line in rows:
            if line.startswith(target):
                readout = line.split("\t")[3]
                seen[readout] = seen.get(readout, 0) + 1
                if seen[readout] > 2:
                    continue
            kept.append(line)
        self.assertLess(len(kept), len(rows))
        (self.root / M.CURVES_TSV).write_text(
            "\n".join([header, *kept]) + "\n", encoding="utf-8"
        )
        self._rehash_everything()
        self.assertTrue(any("reaching the phase horizon" in p for p in self.problems()))

    def test_both_endpoint_conventions_are_accepted(self) -> None:
        from dt_adoc.simulation.runner import _default_time_tick

        tick = _default_time_tick(ROOT)
        curves = []
        for phase in M.phase_plan():
            duration = M.phase_duration(ROOT, phase)
            n = round(duration / tick) + (
                1 if phase.key == "basal" else 0
            )  # inclusive for basal
            for readout in M.READOUTS:
                curves += [
                    {
                        "phase": phase.key,
                        "protocol_id": phase.protocol_id,
                        "horizon": phase.horizon,
                        "readout": readout,
                        "time": i * tick,
                        "mean_p_on": 0.5,
                        "sd_p_on": 0.1,
                    }
                    for i in range(n)
                ]
        self.assertEqual(M._curve_problems(curves, ROOT), [])

    def test_a_nan_time_and_an_infinite_sd_fail(self) -> None:
        original = (self.root / M.CURVES_TSV).read_text(encoding="utf-8")
        problems = self._mutate_cell(M.CURVES_TSV, "time", "nan", row=3)
        self.assertTrue(any("time grid" in p for p in problems))
        (self.root / M.CURVES_TSV).write_text(original, encoding="utf-8")
        problems = self._mutate_cell(M.CURVES_TSV, "sd_p_on", "inf")
        self.assertTrue(any("non-finite" in p for p in problems))
        (self.root / M.CURVES_TSV).write_text(original, encoding="utf-8")
        problems = self._mutate_cell(M.CURVES_TSV, "mean_p_on", "nan")
        self.assertTrue(any("non-finite" in p for p in problems))

    def test_a_block_difference_outside_minus_one_to_one_fails(self) -> None:
        problems = self._mutate_cell(M.BLOCKS_TSV, "difference", "1.5")
        self.assertTrue(any("out-of-range difference" in p for p in problems))

    def test_headers_duplicates_and_order(self) -> None:
        for path in (M.BLOCKS_TSV, M.CURVES_TSV):
            with self.subTest(path=path, case="header"):
                original = (self.root / path).read_text(encoding="utf-8")
                lines = original.splitlines()
                lines[0] = lines[0].replace("\t", "\textra\t", 1)
                (self.root / path).write_text("\n".join(lines) + "\n", encoding="utf-8")
                self._rehash_everything()
                self.assertTrue(any("header" in p for p in self.problems()))
                (self.root / path).write_text(original, encoding="utf-8")
            with self.subTest(path=path, case="duplicate"):
                lines = original.splitlines()
                (self.root / path).write_text(
                    "\n".join([*lines, lines[1]]) + "\n", encoding="utf-8"
                )
                self._rehash_everything()
                self.assertTrue(self.problems())
                (self.root / path).write_text(original, encoding="utf-8")
            with self.subTest(path=path, case="order"):
                lines = original.splitlines()
                lines[1], lines[2] = lines[2], lines[1]
                (self.root / path).write_text("\n".join(lines) + "\n", encoding="utf-8")
                self._rehash_everything()
                self.assertTrue(self.problems())
                (self.root / path).write_text(original, encoding="utf-8")


@_HISTORY_PREREG
@_HISTORY_PARENT
class GeneratorInventoryIsImmutable(unittest.TestCase):
    """B11: validating an old run uses nothing from the current checkout."""

    def test_the_inventory_at_a_commit_is_that_commits_package_listing(self) -> None:
        head = _git_out("rev-parse", "HEAD")
        listing = [
            f
            for f in _git_out("ls-tree", "-r", "--name-only", head).split("\n")
            if f.startswith("src/dt_adoc/") and f.endswith(".py")
        ]
        self.assertEqual(list(M.execution_dependencies(ROOT, head)), sorted(listing))
        self.assertIn("src/dt_adoc/maboss_adapter.py", listing)

    def test_changing_the_current_inventory_definitions_changes_nothing_at_a_commit(
        self,
    ) -> None:
        from dt_adoc.concordance import simulate

        head = _git_out("rev-parse", "HEAD")
        before = M.input_hashes(ROOT, head)
        with (
            mock.patch.object(simulate, "IMPLEMENTATION_GLOBS", ()),
            mock.patch.object(simulate, "implementation_files", lambda root: ()),
        ):
            self.assertEqual(M.input_hashes(ROOT, head), before)
            self.assertEqual(
                M.execution_dependencies(ROOT, head),
                M.execution_dependencies(ROOT, head),
            )

    def test_an_older_commit_is_reconstructed_from_its_own_listing(self) -> None:
        older = _git_out("rev-parse", "HEAD~1")
        listing = sorted(
            f
            for f in _git_out("ls-tree", "-r", "--name-only", older).split("\n")
            if f.startswith("src/dt_adoc/") and f.endswith(".py")
        )
        self.assertEqual(list(M.execution_dependencies(ROOT, older)), listing)

    def test_an_untracked_package_file_blocks_the_binding(self) -> None:
        with _disposable_clone() as clone:
            M.bind_inputs(
                clone
            )  # the clean clone binds, so the refusal below is the probe's
            (clone / "src/dt_adoc/_c3a_untracked_probe.py").write_text(
                "x = 1\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "_c3a_untracked_probe"):
                M.bind_inputs(clone)


class ReuseAfterACanonicalResult(_Canonical):
    def test_reserving_again_after_a_valid_result_is_refused(self) -> None:
        with self.assertRaisesRegex(M.SeedReuseError, "consistent with its ledger"):
            M.reserve_attempt(self.root, _tasks(), {})

    def test_a_result_whose_ledger_is_missing_still_refuses(self) -> None:
        self.journal_path().unlink()
        with self.assertRaisesRegex(
            M.SeedReuseError, "without a matching COMPLETED ledger"
        ):
            M.reserve_attempt(self.root, _tasks(), {})

    def test_outputs_without_a_manifest_still_refuse(self) -> None:
        import shutil

        (self.root / M.SETTINGS_JSON).unlink()
        shutil.rmtree(self.root / M.JOURNAL_DIR)
        with self.assertRaisesRegex(M.SeedReuseError, "without a manifest"):
            M.reserve_attempt(self.root, _tasks(), {})


class FinalisationOrder(unittest.TestCase):
    def test_completed_is_never_written_before_validation_accepts(self) -> None:
        import tempfile

        statuses: list[str] = []
        real = M._update

        def recording(path, **fields):
            if "status" in fields:
                statuses.append(fields["status"])
            return real(path, **fields)

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(M, "_update", side_effect=recording),
            self.assertRaisesRegex(RuntimeError, "does not validate"),
        ):
            M.execute_attempt(
                Path(tmp),
                _tasks(),
                {},
                _ok,
                _sequential,
                lambda r, j: {"outputs_sha256": {}},
                lambda status: ["rejected by validation"],
            )
        self.assertEqual(statuses, ["DISPATCHED", "SIMULATED", M.FINALIZING, "FAILED"])

    def test_the_accepted_sequence(self) -> None:
        import tempfile

        statuses: list[str] = []
        real = M._update

        def recording(path, **fields):
            if "status" in fields:
                statuses.append(fields["status"])
            return real(path, **fields)

        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(M, "_update", side_effect=recording),
        ):
            M.execute_attempt(
                Path(tmp),
                _tasks(),
                {},
                _ok,
                _sequential,
                lambda r, j: {"outputs_sha256": {}},
                _accept,
            )
        self.assertEqual(
            statuses, ["DISPATCHED", "SIMULATED", M.FINALIZING, M.COMPLETED]
        )


if __name__ == "__main__":
    unittest.main()
