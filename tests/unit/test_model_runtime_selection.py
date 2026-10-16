from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from dt_adoc.model.runtime import (
    resolve_memory_policy,
    resolve_model,
    validate_manifest_model_version,
    validate_model_runtime_spec,
)
from dt_adoc.protocols.conditions import get_protocol


class ModelRuntimeSelectionTest(unittest.TestCase):
    def test_known_models_resolve(self) -> None:
        baseline = resolve_model("adoc-core-v0.1.0", ROOT)
        literature = resolve_model("adoc-literature-v0.2.0", ROOT)
        self.assertEqual(baseline.model_version, "adoc-core-v0.1.0")
        self.assertEqual(literature.model_version, "adoc-literature-v0.2.0")
        self.assertTrue(literature.network_bnd.is_file())

    def test_unknown_model_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown model_version"):
            resolve_model("adoc-missing-v9.9.9", ROOT)

    def test_metadata_files_disagreement_raises(self) -> None:
        literature = resolve_model("adoc-literature-v0.2.0", ROOT)
        mismatched = replace(literature, model_version="adoc-literature-v0.9.9")
        with self.assertRaisesRegex(ValueError, "metadata/files disagreement"):
            validate_model_runtime_spec(mismatched, root=ROOT)

    def test_silent_baseline_node_catalog_reuse_is_rejected(self) -> None:
        literature = resolve_model("adoc-literature-v0.2.0", ROOT)
        baseline = resolve_model("adoc-core-v0.1.0", ROOT)
        reused = replace(literature, node_dictionary=baseline.node_dictionary)
        with self.assertRaisesRegex(ValueError, "silent baseline-node-catalog reuse"):
            validate_model_runtime_spec(reused, root=ROOT)

    def test_wrong_manifest_model_version_is_rejected(self) -> None:
        payload = {"model": {"model_version": "adoc-core-v0.1.0"}}
        with self.assertRaisesRegex(ValueError, "wrong manifest model version"):
            validate_manifest_model_version(
                payload,
                expected_model_version="adoc-literature-v0.2.0",
            )

    def test_default_protocol_lookup_remains_baseline(self) -> None:
        protocol = get_protocol("adhesion_challenge_hormone_treated", ROOT)
        self.assertEqual(protocol.model_version, "adoc-core-v0.1.0")

    def test_literature_memory_policy_excludes_outputs_and_route_nodes(self) -> None:
        policy = resolve_memory_policy(
            model_version="adoc-literature-v0.2.0",
            policy_id="minimal_stable_joint",
            root=ROOT,
        )
        self.assertNotIn("OUT_STABLE_ADHESION", policy.node_ids)
        self.assertNotIn("E_PAEP", policy.node_ids)
        self.assertNotIn("S_PRL", policy.node_ids)
        self.assertNotIn("S_IGFBP1", policy.node_ids)
        self.assertNotIn("X_ADHESION_ROUTE_SPP1", policy.node_ids)
        self.assertNotIn("X_ADHESION_ROUTE_REDUNDANT", policy.node_ids)
        self.assertNotIn("IN_EMBRYO_PRESENT", policy.node_ids)


if __name__ == "__main__":
    unittest.main()
