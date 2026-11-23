from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.perturbations.combinations import pair_scenarios
from dt_adoc.perturbations.single import single_scenarios
from dt_adoc.perturbations.target_engagement import build_target_engagement_grid


class ProfileV2ParityFixtureTest(unittest.TestCase):
    def test_gradient_inhibition_fixture(self) -> None:
        fixture = json.loads(
            (
                ROOT
                / "context"
                / "upstream"
                / "fixtures"
                / "profile_v2"
                / "profile_v2_gradient_inhibition_fixture.json"
            ).read_text(encoding="utf-8")
        )
        levels = build_target_engagement_grid(list(fixture["levels"]))
        self.assertEqual(levels, fixture["expected_grid"])
        singles = single_scenarios(
            fixture["target_a"],
            levels,
            mode=fixture["mode"],
        )
        pairs = pair_scenarios(
            fixture["target_a"],
            fixture["target_b"],
            levels,
            mode=fixture["mode"],
        )
        self.assertEqual(len(singles), int(fixture["expected_single_count"]))
        self.assertEqual(len(pairs), int(fixture["expected_pair_count"]))


if __name__ == "__main__":
    unittest.main()
