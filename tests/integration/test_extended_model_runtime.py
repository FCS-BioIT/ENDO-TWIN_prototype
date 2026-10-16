from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import maboss

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


MODEL_DIR = ROOT / "models" / "extended" / "adoc-literature-v0.2.0"


def _parse_cfg(text: str) -> tuple[list[str], dict[str, str], list[str]]:
    passthrough: list[str] = []
    assignments: dict[str, str] = {}
    order: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("//") or "=" not in raw_line:
            passthrough.append(raw_line)
            continue
        key = raw_line.split("=", 1)[0].strip()
        assignments[key] = raw_line
        if key not in order:
            order.append(key)
    return passthrough, assignments, order


def _merged_cfg_text(condition_name: str) -> str:
    baseline = (MODEL_DIR / "baseline.cfg").read_text(encoding="utf-8")
    condition = (MODEL_DIR / "conditions" / f"{condition_name}.cfg").read_text(
        encoding="utf-8"
    )
    passthrough, assignments, order = _parse_cfg(baseline)
    for override_text in [
        condition,
        (
            "seed_pseudorandom = 7;\n"
            "sample_count = 5000;\n"
            "max_time = 20.0;\n"
            "time_tick = 0.1;"
        ),
    ]:
        _, override_assignments, override_order = _parse_cfg(override_text)
        for key in override_order:
            assignments[key] = override_assignments[key]
            if key not in order:
                order.append(key)
    lines = [line for line in passthrough if line.strip()]
    lines.append("")
    lines.extend(assignments[key] for key in order)
    return "\n".join(lines).rstrip() + "\n"


def _run_condition(condition_name: str):
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / f"{condition_name}.cfg"
        cfg.write_text(_merged_cfg_text(condition_name), encoding="utf-8")
        sim = maboss.load(str(MODEL_DIR / "network.bnd"), str(cfg), cmaboss=True)
        result = sim.run()
        return result.get_last_nodes_probtraj().iloc[-1]


class ExtendedModelRuntimeTest(unittest.TestCase):
    def test_extended_model_loads(self) -> None:
        last = _run_condition("hormone_treated")
        self.assertIn("OUT_STABLE_ADHESION", last.index)

    def test_smoke_conditions_preserve_expected_directions(self) -> None:
        untreated = _run_condition("untreated")
        hormone = _run_condition("hormone_treated")
        mife = _run_condition("hormone_treated_mifepristone")
        anti = _run_condition("hormone_treated_anti_spp1")
        embryo_absent = _run_condition("embryo_absent")
        embryo_incompetent = _run_condition("embryo_incompetent")
        er_stress = _run_condition("excess_er_stress")
        stiffness = _run_condition("high_ecm_stiffness")

        self.assertLess(
            untreated["OUT_STABLE_ADHESION"], hormone["OUT_STABLE_ADHESION"]
        )
        self.assertGreater(hormone["OUT_STROMAL_DECIDUALIZED"], 0.0)
        self.assertGreater(hormone["OUT_EPITHELIAL_RECEPTIVE"], 0.0)
        self.assertLess(mife["OUT_STABLE_ADHESION"], hormone["OUT_STABLE_ADHESION"])
        self.assertLess(anti["OUT_STABLE_ADHESION"], hormone["OUT_STABLE_ADHESION"])
        self.assertGreater(anti["OUT_STABLE_ADHESION"], 0.0)
        self.assertEqual(embryo_absent["OUT_STABLE_ADHESION"], 0.0)
        self.assertEqual(embryo_incompetent["OUT_STABLE_ADHESION"], 0.0)
        self.assertLess(
            er_stress["X_MECHANICAL_PERMISSIVE_ECM"],
            hormone["X_MECHANICAL_PERMISSIVE_ECM"],
        )
        self.assertLess(
            stiffness["X_MECHANICAL_PERMISSIVE_ECM"],
            hormone["X_MECHANICAL_PERMISSIVE_ECM"],
        )
        self.assertLess(
            er_stress["OUT_STABLE_ADHESION"], hormone["OUT_STABLE_ADHESION"]
        )
        self.assertLess(
            stiffness["OUT_STABLE_ADHESION"], hormone["OUT_STABLE_ADHESION"]
        )


if __name__ == "__main__":
    unittest.main()
