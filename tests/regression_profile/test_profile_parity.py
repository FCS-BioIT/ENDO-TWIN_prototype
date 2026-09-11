from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.personalization.soft_nv import (
    SoftMappingConfig,
    score_to_initial_probability,
    score_to_rate_modifiers,
)


class ProfileParityFixtureTest(unittest.TestCase):
    def test_profile_soft_mapping_fixture(self) -> None:
        fixture = json.loads(
            (
                ROOT
                / "references"
                / "fixtures"
                / "profile"
                / "profile_parity_fixture.json"
            ).read_text(encoding="utf-8")
        )
        config = SoftMappingConfig(alpha=float(fixture["alpha"]))
        for row in fixture["scores"]:
            probability = score_to_initial_probability(float(row["score"]))
            rate_up, rate_down = score_to_rate_modifiers(
                float(row["score"]),
                config,
            )
            self.assertAlmostEqual(
                probability,
                float(row["expected_initial_probability"]),
            )
            self.assertTrue(math.isclose(rate_up, float(row["expected_rate_up"])))
            self.assertTrue(math.isclose(rate_down, float(row["expected_rate_down"])))


if __name__ == "__main__":
    unittest.main()
