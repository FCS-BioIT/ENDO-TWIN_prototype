from __future__ import annotations

import sys
import unittest
from pathlib import Path

import maboss

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.simulation.runner import (
    build_condition_cfg,
    protocol_continuation,
    run_protocol,
)


class CMaBoSSRuntimeTest(unittest.TestCase):
    def test_toy_network_runs(self) -> None:
        # Read the committed fixtures; the test used to rewrite them in place.
        fixtures = ROOT / "tests" / "fixtures"
        bnd = fixtures / "toy_runtime.bnd"
        cfg = fixtures / "toy_runtime.cfg"
        sim = maboss.load(str(bnd), str(cfg), cmaboss=True)
        result = sim.run()
        self.assertEqual(result.get_last_nodes_probtraj().iloc[-1]["A"], 1.0)

    def test_hormone_treated_condition_loads_and_activates_outputs(self) -> None:
        merged_cfg = build_condition_cfg(
            condition_cfg=ROOT
            / "models"
            / "baseline"
            / "adoc-core-v0.1.0"
            / "conditions"
            / "hormone_treated.cfg",
            root=ROOT,
            seed=1,
            sample_count=200,
        )
        sim = maboss.load(
            str(ROOT / "models" / "baseline" / "adoc-core-v0.1.0" / "network.bnd"),
            str(merged_cfg),
            cmaboss=True,
        )
        result = sim.run()
        last = result.get_last_nodes_probtraj().iloc[-1]
        self.assertGreater(last["OUT_EPITHELIAL_RECEPTIVE"], 0.7)
        self.assertLess(last["OUT_EPITHELIAL_RECEPTIVE"], 1.0)
        self.assertGreater(last["OUT_STROMAL_DECIDUALIZED"], 0.4)
        self.assertLess(last["OUT_STROMAL_DECIDUALIZED"], 1.0)

    def test_adhesion_challenge_outputs_intermediate_probability(self) -> None:
        maternal = run_protocol("hormone_treated", root=ROOT, sample_count=300)
        challenge = run_protocol(
            "adhesion_challenge_hormone_treated",
            root=ROOT,
            continuation=protocol_continuation(
                "adhesion_challenge_hormone_treated",
                maternal,
                root=ROOT,
            ),
            sample_count=300,
        )
        probability = challenge.final_result.last["OUT_STABLE_ADHESION"]
        self.assertGreater(probability, 0.0)
        self.assertLess(probability, 1.0)


if __name__ == "__main__":
    unittest.main()
