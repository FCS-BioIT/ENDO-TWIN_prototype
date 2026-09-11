from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


data_manifest = load_module(
    "dt_adoc_data_manifest",
    ROOT / ".codex/skills/adoc-data-audit/scripts/check_data_manifest.py",
)
run_manifest = load_module(
    "dt_adoc_run_manifest",
    ROOT / ".codex/skills/adoc-result-validator/scripts/validate_run_manifest.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DataManifestValidatorTest(unittest.TestCase):
    def test_data_manifest_without_hashes(self) -> None:
        report = data_manifest.validate_manifest(
            ROOT, ROOT / "config/data_manifest.tsv", check_hashes=False
        )
        self.assertEqual(report.errors, [])
        self.assertIn("content hashes were not recomputed", report.warnings)


class RunManifestValidatorTest(unittest.TestCase):
    def test_valid_synthetic_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {}
            for name, content in {
                "models/base.bnd": "node A { logic = A; }\n",
                "models/base.cfg": "sample_count = 10;\n",
                "config/data.tsv": "path\\thash\n",
                "mapping.tsv": "feature\\tnode\n",
                "output/result.csv": "phenotype,probability\nA,1.0\n",
            }.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                files[name] = {
                    "path": name,
                    "sha256": sha256(path),
                    "size_bytes": path.stat().st_size,
                }
            payload = {
                "schema_version": "1.0",
                "run_id": "synthetic-smoke",
                "created_at": "2026-07-25T00:00:00Z",
                "software": {"maboss": "test"},
                "model": {
                    "baseline_bnd": files["models/base.bnd"],
                    "baseline_cfg": files["models/base.cfg"],
                },
                "data": {"source_manifest": files["config/data.tsv"]},
                "cohort": {
                    "independent_unit": "synthetic",
                    "included_units": ["fixture"],
                    "exclusions": [],
                },
                "personalization": {
                    "mapping": files["mapping.tsv"],
                    "leakage_controls": "synthetic fixture",
                },
                "simulation": {
                    "seeds": [1, 2],
                    "trajectory_count": 100,
                    "max_time": 10,
                    "time_tick": 1,
                },
                "phenotypes": {"A": "A"},
                "outputs": [{**files["output/result.csv"], "kind": "probability"}],
                "validation": {"completed_levels": ["structural"]},
                "warnings": [],
            }
            report = run_manifest.validate_manifest(payload, root)
            self.assertEqual(report.errors, [])

    def test_path_escape_rejected(self) -> None:
        report = run_manifest.Report()
        run_manifest.validate_file_ref(
            "bad",
            {"path": "../outside", "sha256": "0" * 64},
            ROOT,
            report,
            False,
        )
        self.assertTrue(any("cannot contain '..'" in error for error in report.errors))

    def test_missing_simulation_evidence_rejected(self) -> None:
        payload = {key: {} for key in run_manifest.REQUIRED_TOP_LEVEL}
        payload.update(
            {
                "schema_version": "1",
                "run_id": "bad",
                "created_at": "now",
                "software": {"maboss": "unknown"},
                "model": {},
                "data": {},
                "cohort": {},
                "personalization": {},
                "simulation": {},
                "phenotypes": {},
                "outputs": [],
                "validation": {},
                "warnings": [],
            }
        )
        report = run_manifest.validate_manifest(payload, ROOT, check_hashes=False)
        self.assertTrue(any("simulation.seeds" in error for error in report.errors))
        self.assertTrue(
            any("simulation.trajectory_count" in error for error in report.errors)
        )


if __name__ == "__main__":
    unittest.main()
