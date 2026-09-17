from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.model.compile import render_bnd, render_condition_cfg
from dt_adoc.model.validate import validate


class ModelContractTest(unittest.TestCase):
    def test_static_model_contract_validates(self) -> None:
        report = validate(ROOT)
        self.assertEqual(report.errors, [], report.payload())

    def test_render_bnd_matches_committed_network(self) -> None:
        compiled = render_bnd(ROOT)
        committed = (
            ROOT / "models" / "baseline" / "adoc-core-v0.1.0" / "network.bnd"
        ).read_text(encoding="utf-8")
        self.assertEqual(compiled, committed)

    def test_render_condition_cfg(self) -> None:
        rendered = render_condition_cfg("hormone_treated", ROOT)
        self.assertIn("IN_PROGESTIN.istate = TRUE;", rendered)


if __name__ == "__main__":
    unittest.main()
