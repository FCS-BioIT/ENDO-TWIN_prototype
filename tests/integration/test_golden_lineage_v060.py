"""Golden-lineage regression for the adopted v0.6.0 model.

A computational regression reference, not biological validation. The
reference (tests/fixtures/golden_lineage/v060_continuation_reference.json) holds
the exact node probabilities that the committed implementation produced at the
end of four seeded, multi-phase joint-continuation lineages. Three run at the
declared horizon and one, an intervention lineage, at the converged horizon.
This test re-runs the same lineages through the production chain
(`concordance.simulate.run_arm`: protocol lineage, `run_protocol` per phase,
joint continuation between phases) and requires the same numbers, exactly.

Why exact: with `thread_count = 1`, fixed seeds and the pinned environment,
repeated runs in separate processes are bit-identical, which was verified
before freezing. Any tolerance would be a choice about which changes to
ignore. Audit mutation M6c moved the carried joint state by 1 % and shifted
42 of 45 node means by up to 1.9 percentage points in these lineages, and it
passed every other test of this model.

Expected values come only from the frozen file. Nothing here recomputes them
from the current implementation. If the inputs or the environment differ from
the ones recorded, the preconditions below fail and say so: the comparison is
only meaningful against the inputs it was frozen from. An intended change to
the simulation means re-freezing with `src/scripts/freeze_golden_lineage.py`, as a
reviewed change in its own right.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import unittest
from importlib import metadata
from pathlib import Path

from dt_adoc.concordance.simulate import run_arm

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "tests/fixtures/golden_lineage/v060_continuation_reference.json"


def _reference() -> dict:
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


class TheReferenceIsComparable(unittest.TestCase):
    """The preconditions under which an exact comparison means anything."""

    def setUp(self) -> None:
        self.reference = _reference()

    def test_the_environment_is_the_one_the_reference_was_frozen_in(self) -> None:
        recorded = self.reference["environment"]
        current = {
            "maboss": metadata.version("maboss"),
            "python": platform.python_version(),
            "machine": platform.machine(),
        }
        self.assertEqual(
            current,
            recorded,
            "the golden lineage was frozen in a different environment, where "
            "bit-identity was established; re-establish it there before "
            "re-freezing",
        )

    def test_the_model_inputs_are_the_ones_the_reference_was_frozen_from(self) -> None:
        recorded = self.reference["inputs_sha256"]
        model_dir = f"models/superset/{self.reference['model_version']}"
        tracked = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z", "--", model_dir],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split("\0")
        current_paths = {p for p in tracked if p} | {
            p for p in recorded if not p.startswith(model_dir + "/")
        }
        current = {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in sorted(current_paths)
            if (ROOT / p).is_file()
        }
        changed = sorted(
            p for p in set(recorded) | set(current) if recorded.get(p) != current.get(p)
        )
        self.assertEqual(
            changed,
            [],
            "model inputs changed since the golden lineage was frozen; if the "
            "change is intended, re-freeze with src/scripts/freeze_golden_lineage.py "
            "as a reviewed change",
        )

    def test_the_reference_is_not_degenerate(self) -> None:
        # A reference made only of 0s and 1s would hide continuation errors that
        # move intermediate mass. Every declared-horizon case must carry many
        # intermediate probabilities.
        for case in self.reference["cases"]:
            if case["horizon_class"] != "declared":
                continue
            with self.subTest(protocol=case["protocol_id"]):
                intermediate = [
                    v for v in case["node_mean"].values() if 0.02 < v < 0.98
                ]
                self.assertGreaterEqual(len(intermediate), 20)
                self.assertGreaterEqual(len(case["lineage"]), 4)

    def test_every_case_crosses_several_joint_continuations(self) -> None:
        for case in self.reference["cases"]:
            with self.subTest(
                protocol=case["protocol_id"], horizon=case["horizon_class"]
            ):
                self.assertEqual(case["lineage"][0], "basal_maternal")
                self.assertEqual(case["lineage"][-1], case["protocol_id"])
                self.assertGreaterEqual(len(case["lineage"]) - 1, 3)


class TheAdoptedModelReproducesItsGoldenLineages(unittest.TestCase):
    def test_every_case_reproduces_exactly(self) -> None:
        reference = _reference()
        for case in reference["cases"]:
            with self.subTest(
                protocol=case["protocol_id"], horizon=case["horizon_class"]
            ):
                run = run_arm(
                    case["protocol_id"],
                    case["protocol_id"],
                    horizon_class=case["horizon_class"],
                    model_version=reference["model_version"],
                    root=ROOT,
                    trajectory_count=reference["trajectory_count"],
                    seeds=tuple(reference["seeds"]),
                )
                self.assertEqual(list(run.lineage), case["lineage"])
                self.assertEqual(run.phase_horizon, case["phase_horizon"])
                expected = case["node_mean"]
                self.assertEqual(sorted(run.node_mean), sorted(expected))
                moved = {
                    node: (expected[node], run.node_mean[node])
                    for node in expected
                    if run.node_mean[node] != expected[node]
                }
                worst = sorted(
                    moved.items(), key=lambda item: -abs(item[1][1] - item[1][0])
                )[:5]
                self.assertEqual(
                    moved,
                    {},
                    f"{len(moved)} node(s) moved from the frozen reference; largest: "
                    + ", ".join(f"{n} {a!r} -> {b!r}" for n, (a, b) in worst),
                )


if __name__ == "__main__":
    unittest.main()
