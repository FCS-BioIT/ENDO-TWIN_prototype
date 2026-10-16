from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


run_manifest = load_module(
    "dt_adoc_run_manifest_validator",
    ROOT / ".codex/skills/adoc-result-validator/scripts/validate_run_manifest.py",
)

from dt_adoc.model.provenance import describe_file
from dt_adoc.simulation.manifests import SimulationSettings, build_run_manifest


class ManifestTest(unittest.TestCase):
    def test_build_run_manifest_is_validator_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output" / "table.tsv"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("phenotype\tprobability\nA\t1.0\n", encoding="utf-8")
            source_manifest = root / "config" / "data.tsv"
            source_manifest.parent.mkdir(parents=True, exist_ok=True)
            source_manifest.write_text("path\thash\n", encoding="utf-8")
            mapping = root / "config" / "mapping.tsv"
            mapping.write_text("field\trole\n", encoding="utf-8")
            bnd = root / "models" / "network.bnd"
            cfg = root / "models" / "baseline.cfg"
            bnd.parent.mkdir(parents=True, exist_ok=True)
            bnd.write_text("Node A {\n  logic = A;\n}\n", encoding="utf-8")
            cfg.write_text(
                "sample_count = 10;\nmax_time = 1;\ntime_tick = 0.5;\n",
                encoding="utf-8",
            )

            payload = build_run_manifest(
                run_id="synthetic",
                command="python -m dt_adoc.cli smoke --run-id synthetic",
                baseline_bnd=bnd,
                baseline_cfg=cfg,
                source_manifest=source_manifest,
                mapping=mapping,
                outputs=[
                    {**describe_file(output, root=root).__dict__, "kind": "table"}
                ],
                phenotypes={"A": "A"},
                included_units=["fixture"],
                exclusions=[],
                leakage_controls="synthetic test",
                software={"maboss_python_package": "0.8.15"},
                protocols=["synthetic"],
                simulation=SimulationSettings(
                    seeds=[1, 2],
                    trajectory_count=10,
                    max_time=1.0,
                    time_tick=0.5,
                    thread_count=1,
                    perturbation="none",
                ),
                simulation_extras={
                    "stability": {"seeds": [1, 2, 3], "trajectory_count": 500}
                },
                validation_levels=["structural"],
                root=root,
            )
            self.assertEqual(payload["simulation"]["stability"]["seeds"], [1, 2, 3])
            report = run_manifest.validate_manifest(payload, root)
            self.assertEqual(report.errors, [], report.payload())


if __name__ == "__main__":
    unittest.main()
