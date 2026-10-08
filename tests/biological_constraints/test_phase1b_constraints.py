from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.simulation.runner import protocol_continuation, run_protocol


def _run(protocol_id: str, upstream: dict[str, object]) -> dict[str, float]:
    continuation = None
    if protocol_id.startswith("adhesion_challenge_"):
        source_protocol = protocol_id.removeprefix("adhesion_challenge_")
        continuation = protocol_continuation(
            protocol_id,
            upstream[source_protocol],
            root=ROOT,
        )
    elif protocol_id in {
        "e2_priming",
        "hormone_treated",
        "hormone_treated_mifepristone",
        "hormone_treated_anti_spp1",
        "washout",
    }:
        source_map = {
            "e2_priming": "basal",
            "hormone_treated": "e2_priming",
            "hormone_treated_mifepristone": "hormone_treated",
            "hormone_treated_anti_spp1": "hormone_treated",
            "washout": "hormone_treated_anti_spp1",
        }
        continuation = protocol_continuation(
            protocol_id, upstream[source_map[protocol_id]], root=ROOT
        )
    run = run_protocol(
        protocol_id,
        root=ROOT,
        continuation=continuation,
        sample_count=2000,
    )
    upstream[protocol_id] = run
    return run.final_result.last


class Phase1BConstraintTest(unittest.TestCase):
    def test_phase1b_biological_constraints(self) -> None:
        upstream: dict[str, object] = {}
        basal = _run("basal", upstream)
        e2 = _run("e2_priming", upstream)
        ht = _run("hormone_treated", upstream)
        mife = _run("hormone_treated_mifepristone", upstream)
        anti = _run("hormone_treated_anti_spp1", upstream)
        washout = _run("washout", upstream)
        basal_challenge = _run("adhesion_challenge_basal", upstream)
        ht_challenge = _run("adhesion_challenge_hormone_treated", upstream)
        mife_challenge = _run(
            "adhesion_challenge_hormone_treated_mifepristone", upstream
        )
        anti_challenge = _run("adhesion_challenge_hormone_treated_anti_spp1", upstream)
        washout_challenge = _run("adhesion_challenge_washout", upstream)

        self.assertLessEqual(
            basal["OUT_MATERNAL_ADHESION_COMPETENCE"],
            e2["OUT_MATERNAL_ADHESION_COMPETENCE"],
        )
        self.assertGreater(
            ht["OUT_MATERNAL_ADHESION_COMPETENCE"],
            basal["OUT_MATERNAL_ADHESION_COMPETENCE"],
        )
        self.assertLess(
            mife["OUT_EPITHELIAL_RECEPTIVE"], ht["OUT_EPITHELIAL_RECEPTIVE"]
        )
        self.assertLess(
            mife["OUT_MATERNAL_ADHESION_COMPETENCE"],
            ht["OUT_MATERNAL_ADHESION_COMPETENCE"],
        )
        self.assertLess(anti["X_SPP1_LUMEN_FREE"], ht["X_SPP1_LUMEN_FREE"])
        self.assertGreater(anti["OUT_MATERNAL_ADHESION_COMPETENCE"], 0.0)
        self.assertEqual(basal_challenge["OUT_STABLE_ADHESION"], 0.0)
        self.assertGreater(
            ht_challenge["OUT_STABLE_ADHESION"], basal_challenge["OUT_STABLE_ADHESION"]
        )
        self.assertLess(
            mife_challenge["OUT_STABLE_ADHESION"],
            ht_challenge["OUT_STABLE_ADHESION"],
        )
        self.assertLess(
            anti_challenge["OUT_STABLE_ADHESION"],
            ht_challenge["OUT_STABLE_ADHESION"],
        )
        self.assertGreater(anti_challenge["OUT_STABLE_ADHESION"], 0.0)
        self.assertGreaterEqual(
            washout["OUT_MATERNAL_ADHESION_COMPETENCE"],
            anti["OUT_MATERNAL_ADHESION_COMPETENCE"],
        )
        self.assertGreaterEqual(
            washout_challenge["OUT_STABLE_ADHESION"],
            anti_challenge["OUT_STABLE_ADHESION"],
        )


if __name__ == "__main__":
    unittest.main()
