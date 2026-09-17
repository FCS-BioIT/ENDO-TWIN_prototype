from __future__ import annotations

import csv
import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model import superset_family
from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.superset_family import MODEL_KEY, MODEL_VERSION, write_family

# The contract suite tracks whatever the generator currently emits. v0.3.0 is an
# immutable parent and is covered separately by the archived-model test below.
MODEL_DIR = ROOT / "models" / "superset" / MODEL_VERSION
ARCHIVED_SUPERSET = "adoc-literature-superset-v0.3.0"
NODE_RE = re.compile(r"^\s*Node\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{")
LOGIC_RE = re.compile(r"^\s*logic\s*=\s*(.+?)\s*;\s*$")


def _load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _bnd_nodes_and_logic(path: Path) -> tuple[list[str], dict[str, str]]:
    ordered: list[str] = []
    logic_map: dict[str, str] = {}
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        node_match = NODE_RE.match(line)
        if node_match:
            current = node_match.group(1)
            ordered.append(current)
            continue
        logic_match = LOGIC_RE.match(line)
        if logic_match and current is not None:
            logic_map[current] = logic_match.group(1)
    return ordered, logic_map


def _cfg_nodes(path: Path) -> set[str]:
    nodes: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("//", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key.startswith("[") and key.endswith("].istate"):
            key = key[1:-8]
        elif key.endswith((".istate", ".is_internal")):
            key = key.rsplit(".", 1)[0]
        else:
            continue
        nodes.add(key)
    return nodes


class SupersetModelContractTest(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        expected = {
            "README.md",
            "provenance.toml",
            "network.bnd",
            "baseline.cfg",
            "node_dictionary.tsv",
            "edge_evidence.tsv",
            "phenotype_contract.tsv",
            "complete_nodes.tsv",
            "complete_edges.tsv",
            "modules.tsv",
            "rule_variants.tsv",
            "interface_contract.tsv",
            "drug_target_catalog.tsv",
            "executable_model_manifest.tsv",
            "ensemble_definition.tsv",
            "unresolved_mechanisms.tsv",
            "literature_superset_network.mmd",
            "executable_modules_network.mmd",
            "conditions/basal_maternal.cfg",
            "conditions/e2_primed_maternal.cfg",
            "conditions/hormone_treated_maternal.cfg",
            "conditions/adhesion_challenge_basal.cfg",
            "conditions/adhesion_challenge_hormone_treated.cfg",
            "conditions/adhesion_challenge_hormone_treated_mifepristone.cfg",
            "conditions/adhesion_challenge_hormone_treated_anti_spp1.cfg",
            "conditions/adhesion_challenge_excess_er_stress.cfg",
            "conditions/adhesion_challenge_high_ecm_stiffness.cfg",
            "conditions/adhesion_challenge_washout.cfg",
        }
        for relative in expected:
            self.assertTrue((MODEL_DIR / relative).is_file(), relative)

    def test_the_derived_slices_exist_for_the_archived_parent_only(self) -> None:
        """The three derived reference slices have NO generator anywhere in
        `src/`; they exist only under v0.3.0, where they were produced by a
        step that was never committed. They are asserted against the archived
        parent so their loss would still be caught, and their absence under the
        active model is a recorded gap rather than a silently dropped contract.
        Hand-authoring them would put unprovenanced model artifacts in
        `models/`, which is worse than the gap."""
        archived = ROOT / "models" / "superset" / ARCHIVED_SUPERSET
        for slice_name in (
            "minimal_core",
            "literature_parity",
            "module_expansion_proliferative_feedback",
        ):
            self.assertTrue(
                (archived / "generated" / slice_name / "network.bnd").is_file(),
                slice_name,
            )
        self.assertFalse(
            (MODEL_DIR / "generated").exists(),
            "if a slice generator is ever written, fold this back into "
            "test_required_files_exist and delete this test",
        )

    def test_candidate_nodes_and_edges_are_retained(self) -> None:
        complete_nodes = _load_tsv(MODEL_DIR / "complete_nodes.tsv")
        complete_edges = _load_tsv(MODEL_DIR / "complete_edges.tsv")
        candidate_nodes = {
            row["node_id"]
            for row in _load_tsv(
                ROOT / "context" / "literature" / "candidate-nodes.tsv"
            )
        }
        candidate_edges = {
            row["edge_id"]
            for row in _load_tsv(
                ROOT / "context" / "literature" / "candidate-edges.tsv"
            )
        }
        complete_node_ids = {row["node_id"] for row in complete_nodes}
        complete_candidate_edges = {
            row["edge_id"]
            for row in complete_edges
            if row["catalog_origin"] == "literature_candidate"
        }
        self.assertEqual(candidate_nodes - complete_node_ids, set())
        self.assertEqual(candidate_edges - complete_candidate_edges, set())

    def test_runtime_nodes_and_conditions_are_consistent(self) -> None:
        node_rows = _load_tsv(MODEL_DIR / "node_dictionary.tsv")
        edge_rows = _load_tsv(MODEL_DIR / "edge_evidence.tsv")
        node_ids = [row["node_id"] for row in node_rows]
        self.assertEqual(len(node_ids), len(set(node_ids)))
        edge_ids = [row["edge_id"] for row in edge_rows]
        self.assertEqual(len(edge_ids), len(set(edge_ids)))
        bnd_nodes, logic_map = _bnd_nodes_and_logic(MODEL_DIR / "network.bnd")
        self.assertEqual(bnd_nodes, node_ids)
        for node_id in node_ids:
            self.assertIn(node_id, logic_map)
        known_node_ids = set(node_ids)
        for relative in [
            "baseline.cfg",
            "conditions/basal_maternal.cfg",
            "conditions/e2_primed_maternal.cfg",
            "conditions/hormone_treated_maternal.cfg",
            "conditions/adhesion_challenge_basal.cfg",
            "conditions/adhesion_challenge_hormone_treated.cfg",
            "conditions/adhesion_challenge_hormone_treated_mifepristone.cfg",
            "conditions/adhesion_challenge_hormone_treated_anti_spp1.cfg",
            "conditions/adhesion_challenge_excess_er_stress.cfg",
            "conditions/adhesion_challenge_high_ecm_stiffness.cfg",
            "conditions/adhesion_challenge_washout.cfg",
        ]:
            self.assertEqual(
                sorted(_cfg_nodes(MODEL_DIR / relative) - known_node_ids), [], relative
            )

    def test_generated_model_manifest_paths_exist(self) -> None:
        rows = _load_tsv(MODEL_DIR / "executable_model_manifest.tsv")
        self.assertGreaterEqual(len(rows), 4)
        for row in rows:
            for key in ["network_bnd", "baseline_cfg"]:
                self.assertTrue((ROOT / row[key]).is_file(), row[key])

    def test_rule_variants_ledger_preserves_required_rows(self) -> None:
        rows = _load_tsv(MODEL_DIR / "rule_variants.tsv")
        observed = {
            (row["variant_id"], row["node_id"], row["expression"], row["status"])
            for row in rows
        }
        self.assertTrue(
            {
                (
                    "literature_parity_v020",
                    "E_LIF",
                    "E_SECRETORY_STATE",
                    "reference_only",
                ),
                (
                    MODEL_KEY,
                    "E_LIF",
                    "E_SECRETORY_STATE and not E_KLF12_HIGH",
                    "default_executable",
                ),
                (
                    MODEL_KEY,
                    "S_FGF_MITOGENIC",
                    "not S_HAND2",
                    "default_executable",
                ),
                (
                    MODEL_KEY,
                    "E_ESTROGENIC_PROLIFERATION",
                    "IN_E2 and S_FGF_MITOGENIC and not S_HAND2",
                    "default_executable",
                ),
                (
                    "hand2_required_decidual_variant",
                    "S_DECIDUALIZED",
                    "S_PGR and S_PKA and S_BMP2 and S_HAND2",
                    "catalog_only",
                ),
            }.issubset(observed)
        )

    def test_direct_condition_suite_separates_maternal_and_challenge_contexts(
        self,
    ) -> None:
        maternal_only = {
            "untreated.cfg",
            "hormone_treated.cfg",
            "hormone_treated_mifepristone.cfg",
            "hormone_treated_anti_spp1.cfg",
            "excess_er_stress.cfg",
            "high_ecm_stiffness.cfg",
        }
        embryo_required = {
            "adhesion_challenge_hormone_treated.cfg",
            "adhesion_challenge_hormone_treated_mifepristone.cfg",
            "adhesion_challenge_hormone_treated_anti_spp1.cfg",
        }
        for name in maternal_only:
            assignments = (MODEL_DIR / "conditions" / name).read_text(encoding="utf-8")
            self.assertIn("IN_EMBRYO_PRESENT.istate = FALSE;", assignments, name)
            self.assertIn(
                "IN_TROPHECTODERM_COMPETENT.istate = FALSE;", assignments, name
            )
            self.assertIn("IN_EMBRYO_CONTACT.istate = FALSE;", assignments, name)
        for name in embryo_required:
            assignments = (MODEL_DIR / "conditions" / name).read_text(encoding="utf-8")
            self.assertIn("IN_EMBRYO_PRESENT.istate = TRUE;", assignments, name)
            self.assertIn(
                "IN_TROPHECTODERM_COMPETENT.istate = TRUE;", assignments, name
            )
            self.assertIn("IN_EMBRYO_CONTACT.istate = TRUE;", assignments, name)

    def test_write_family_to_alternate_dir_does_not_touch_real_conditions(
        self,
    ) -> None:
        real_conditions = MODEL_DIR / "conditions"
        before_names = sorted(p.name for p in real_conditions.glob("*.cfg"))
        before_hashes = {
            name: hashlib.sha256((real_conditions / name).read_bytes()).hexdigest()
            for name in before_names
        }
        self.assertTrue(before_names, "expected existing .cfg files in real model dir")

        # write_family lists its outputs in the README `relative_to(ROOT)`, which
        # used to force the scratch dir into the checkout. Re-rooting ROOT at the
        # scratch dir keeps it out. Its inputs are module constants bound at
        # import, so they still come from the checkout; the only other use,
        # build_provenance's `pixi run` version probe (cwd=ROOT), then finds no
        # manifest and records `unavailable`, which no assertion here reads.
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(superset_family, "ROOT", Path(tmp)),
        ):
            tmp_output_dir = Path(tmp) / "generated_family"
            write_family(output_dir=tmp_output_dir)

            after_names = sorted(p.name for p in real_conditions.glob("*.cfg"))
            after_hashes = {
                name: hashlib.sha256((real_conditions / name).read_bytes()).hexdigest()
                for name in after_names
            }
            self.assertEqual(before_names, after_names)
            self.assertEqual(before_hashes, after_hashes)

            generated_names = sorted(
                p.name for p in (tmp_output_dir / "conditions").glob("*.cfg")
            )
            self.assertEqual(generated_names, before_names)

    def test_runtime_registry_resolves_superset(self) -> None:
        model = resolve_model(MODEL_VERSION, ROOT)
        self.assertEqual(model.model_version, MODEL_VERSION)
        self.assertTrue(model.network_bnd.is_file())
        self.assertEqual(model.default_memory_policy, "minimal_stable_joint")
        self.assertEqual(model.default_rule_variants, {})

    def test_the_archived_superset_parent_stays_resolvable(self) -> None:
        """v0.3.0 is frozen, not deleted. Committed figures and their sidecars
        name it, so dropping it from the registry would orphan them."""
        self.assertNotEqual(MODEL_VERSION, ARCHIVED_SUPERSET)
        model = resolve_model(ARCHIVED_SUPERSET, ROOT)
        self.assertEqual(model.model_version, ARCHIVED_SUPERSET)
        self.assertTrue(model.network_bnd.is_file())
        # The parent must not have acquired the loss input.
        self.assertNotIn("IN_HAND2_LOSS", model.network_bnd.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
