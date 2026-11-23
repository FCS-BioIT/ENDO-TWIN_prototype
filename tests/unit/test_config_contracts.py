from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.personalization.reference import load_reference_policy


class ConfigContractTest(unittest.TestCase):
    def test_reference_policy_loads(self) -> None:
        policy = load_reference_policy(ROOT / "config" / "personalization.yaml")
        self.assertTrue(policy.requires_external_reference)
        self.assertIsNone(policy.reference_path)

    def test_core_yaml_contracts_parse(self) -> None:
        for relative in [
            "config/source_contract.yaml",
            "config/preprocessing_contract.yaml",
            "config/evidence_roles.yaml",
            "config/personalization.yaml",
            "config/calibration.yaml",
            "config/candidate_score.yaml",
            "context/upstream/upstream_versions.yaml",
        ]:
            payload = yaml.safe_load((ROOT / relative).read_text())
            self.assertIsInstance(payload, dict, relative)


if __name__ == "__main__":
    unittest.main()
