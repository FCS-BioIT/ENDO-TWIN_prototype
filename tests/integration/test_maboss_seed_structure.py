"""How MaBoSS seeds trajectories, measured on the installed binary.

`docs/maboss_estimator_semantics.md` (addendum 2026-09-23): trajectory ``k`` of
a run with seed ``s`` is seeded ``s + k``, so runs with seeds closer together
than the trajectory count share trajectories. The functional-endpoint replicates
use disjoint seed blocks because of this. If a MaBoSS upgrade changes the
seeding, this test fails and the replicate design must be re-derived -- it does
not become wrong silently.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting.endpoint_replicates import seed_structure_probe
from dt_adoc.reporting.seed_structure import OUTPUT, shift_probe


class SeedStructureTest(unittest.TestCase):
    def test_a_run_is_the_union_of_consecutive_single_seed_runs(self) -> None:
        probe = seed_structure_probe(root=ROOT, block=20)
        self.assertTrue(
            probe["run_equals_union_of_consecutive_single_seed_runs"], probe
        )
        for test in probe["union_tests"]:
            # The test is on dynamic trajectories, not on nodes that never move.
            self.assertGreater(test["transient_node_tick_cells"], 0)
        # ... and it can fail: runs on non-overlapping seed ranges differ.
        self.assertGreater(probe["disjoint_control"]["max_abs_diff_node_table"], 0.01)

    def test_the_committed_run_settings_record_the_same_measurement(self) -> None:
        import json

        settings = json.loads(
            (ROOT / "docs/endpoint/endpoint_run_settings.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(
            settings["seed_structure_probe"][
                "run_equals_union_of_consecutive_single_seed_runs"
            ]
        )

    def test_the_difference_of_two_pooled_runs_is_carried_by_named_trajectories(
        self,
    ) -> None:
        probe = shift_probe(ROOT, trajectories=12, offsets=(1, 4))
        self.assertTrue(probe["consistent_with_per_trajectory_seed_s_plus_k"], probe)

    def test_the_committed_shift_probe_is_pinned_to_its_generator(self) -> None:
        import hashlib
        import json

        recorded = json.loads((ROOT / OUTPUT).read_text(encoding="utf-8"))
        self.assertTrue(recorded["consistent_with_per_trajectory_seed_s_plus_k"])
        self.assertEqual(
            recorded["generator_sha256"],
            hashlib.sha256(
                (ROOT / "src/dt_adoc/reporting/seed_structure.py").read_bytes()
            ).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
