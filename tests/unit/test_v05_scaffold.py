"""U1 -- the v0.5 scaffold is a scaffold, and is pinned to be one.

`docs/v05_mechanistic_integration_plan.md` orders v0.5 as U1 (scaffold) before
U2 (Gate 3a) and forbids U1 from changing any mechanism. A directory that is
"supposed to be" a copy is worth nothing; a directory that is ASSERTED to be a
copy is worth a great deal, because it makes U2's first real change visible as
exactly that change and nothing else. Reviewers get a one-line diff instead of a
new model to re-read.

Three files are allowed to differ, and only because a model directory has to
name itself: `provenance.toml`, `README.md`, `executable_model_manifest.tsv`.
Each is checked to name v0.5.0 rather than merely to differ, so the allowance
cannot be spent on content.

WHEN U2 CHANGES A RULE, THIS SUITE FAILS. That is correct and intended. U2
should replace the identity assertions with the specific, justified differences
it introduces -- not delete them, and not widen the allowed-to-differ set to
make room.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import available_models, resolve_model
from dt_adoc.model.superset_family import MODEL_VERSION as GENERATOR_TARGET

V4_ID = "adoc-literature-superset-v0.4.0"
V5_ID = "adoc-literature-superset-v0.5.0"
V4 = ROOT / "models" / "superset" / V4_ID
V5 = ROOT / "models" / "superset" / V5_ID

#: The only files a scaffold may differ in. Every one of them is separately
#: asserted below to name v0.5.0, so this is a self-naming allowance and not a
#: content allowance.
SELF_NAMING_FILES = frozenset(
    {"provenance.toml", "README.md", "executable_model_manifest.tsv"}
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


class ScaffoldIdentityTest(unittest.TestCase):
    def test_the_two_directories_hold_the_same_file_set(self) -> None:
        self.assertEqual(relative_files(V5), relative_files(V4))

    def test_every_file_but_the_self_naming_three_is_byte_identical(self) -> None:
        """The core invariant. Byte-identical, not 'equivalent'."""
        checked = 0
        for rel in sorted(relative_files(V4)):
            if rel in SELF_NAMING_FILES:
                continue
            with self.subTest(file=rel):
                self.assertEqual(
                    (V5 / rel).read_bytes(),
                    (V4 / rel).read_bytes(),
                    f"{rel} differs between v0.4.0 and the v0.5 scaffold. U1 "
                    f"changes no mechanism; if U2 needs this file to differ, "
                    f"assert the specific difference rather than removing this "
                    f"check.",
                )
            checked += 1
        self.assertEqual(checked, 38)

    def test_no_rule_node_or_condition_differs(self) -> None:
        """Stated separately from the byte check, because it is the claim.

        The byte check would still pass if `network.bnd` were excluded by a
        careless edit to SELF_NAMING_FILES. This names the mechanism-bearing
        files explicitly so that cannot happen quietly.
        """
        for rel in (
            "network.bnd",
            "baseline.cfg",
            "node_dictionary.tsv",
            "edge_evidence.tsv",
            "phenotype_contract.tsv",
            "topology.tsv",
            "rule_variants.tsv",
        ):
            with self.subTest(file=rel):
                self.assertNotIn(rel, SELF_NAMING_FILES)
                self.assertEqual(sha256(V5 / rel), sha256(V4 / rel))

    def test_the_condition_suite_is_byte_identical_pre_u7_invariant(self) -> None:
        """Plan section 12: byte-identity of generated cfgs against v0.4.

        This is a legitimate invariant BEFORE U7 and is retired there, not
        weakened: once the mutation interface lands, every v0.5 cfg necessarily
        carries `$nb_mutable` and the `$Low_*`/`$High_*` pairs that v0.4 has
        none of, so textual identity becomes impossible by construction and T-B
        (trajectory equivalence) takes over. Until U7 this holds exactly.
        """
        v4_cfgs = sorted((V4 / "conditions").glob("*.cfg"))
        self.assertEqual(len(v4_cfgs), 21)
        for cfg in v4_cfgs:
            with self.subTest(condition=cfg.name):
                self.assertEqual(
                    (V5 / "conditions" / cfg.name).read_bytes(), cfg.read_bytes()
                )

    def test_no_cfg_declares_a_mutation_interface_yet(self) -> None:
        """U7 has not landed. If this fails, U7 landed without retiring the above."""
        for cfg in sorted((V5 / "conditions").glob("*.cfg")) + [V5 / "baseline.cfg"]:
            text = cfg.read_text(encoding="utf-8")
            with self.subTest(cfg=cfg.name):
                self.assertNotIn("$nb_mutable", text)
                self.assertNotIn("$High_", text)
                self.assertNotIn("$Low_", text)


class ScaffoldSelfNamingTest(unittest.TestCase):
    def test_each_allowed_difference_is_actually_a_difference(self) -> None:
        """An unused allowance should be removed, not carried."""
        for rel in sorted(SELF_NAMING_FILES):
            with self.subTest(file=rel):
                self.assertNotEqual(sha256(V5 / rel), sha256(V4 / rel))

    def test_provenance_names_this_version_and_records_the_copy(self) -> None:
        payload = tomllib.loads((V5 / "provenance.toml").read_text(encoding="utf-8"))
        self.assertEqual(payload["model_version"], V5_ID)
        self.assertEqual(payload["family_id"], "adoc_literature_superset_v050")
        scaffold = payload["scaffold"]
        self.assertEqual(scaffold["role"], "scaffold")
        self.assertEqual(scaffold["claim_boundary"], "scaffold_only_no_new_claim")
        self.assertEqual(scaffold["copied_from_model_version"], V4_ID)
        self.assertEqual(scaffold["mechanism_changes"], 0)
        self.assertEqual(
            sorted(scaffold["files_differing_from_parent"]), sorted(SELF_NAMING_FILES)
        )
        self.assertEqual(scaffold["files_copied"], len(relative_files(V4)))

    def test_provenance_does_not_claim_the_generator_emitted_this(self) -> None:
        """It did not, and saying so would be the easiest false claim to make here."""
        payload = tomllib.loads((V5 / "provenance.toml").read_text(encoding="utf-8"))
        self.assertEqual(payload["generator_module"], "none_copied_from_parent")
        self.assertEqual(GENERATOR_TARGET, V4_ID)

    @unittest.skipUnless(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        ).stdout.strip()
        == str(ROOT),
        "requires this repository's git work tree",
    )
    def test_the_recorded_parent_subtree_object_is_the_one_on_disk(self) -> None:
        """`copied_from_tree_sha1` should be enforced, not just recorded.

        The per-file digests below already cover the three artifacts they name.
        This covers the parent directory as a whole -- all 41 files, their names
        and their modes -- in one object, and is the field that makes the copy
        reproducible without depending on which commit is cited.
        """
        payload = tomllib.loads((V5 / "provenance.toml").read_text(encoding="utf-8"))
        recorded = payload["scaffold"]["copied_from_tree_sha1"]
        observed = subprocess.run(
            ["git", "rev-parse", f"HEAD:models/superset/{V4_ID}"],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(recorded, observed)

    def test_provenance_pins_the_parent_it_was_copied_from(self) -> None:
        payload = tomllib.loads((V5 / "provenance.toml").read_text(encoding="utf-8"))
        scaffold = payload["scaffold"]
        self.assertEqual(
            scaffold["parent_provenance_sha256"], sha256(V4 / "provenance.toml")
        )
        self.assertEqual(
            scaffold["parent_network_bnd_sha256"], sha256(V4 / "network.bnd")
        )
        self.assertEqual(
            scaffold["parent_baseline_cfg_sha256"], sha256(V4 / "baseline.cfg")
        )

    def test_artifact_paths_point_inside_this_directory(self) -> None:
        payload = tomllib.loads((V5 / "provenance.toml").read_text(encoding="utf-8"))
        for name, rel in payload["artifacts"].items():
            with self.subTest(artifact=name):
                self.assertTrue(rel.startswith(f"models/superset/{V5_ID}/"), rel)
                self.assertTrue((ROOT / rel).is_file(), rel)

    def test_recorded_artifact_digests_match_this_directory(self) -> None:
        payload = tomllib.loads((V5 / "provenance.toml").read_text(encoding="utf-8"))
        hashes = payload["artifact_hashes"]
        for name, rel in payload["artifacts"].items():
            with self.subTest(artifact=name):
                self.assertEqual(sha256(ROOT / rel), hashes[f"{name}_sha256"])

    def test_the_manifest_declares_v05_and_demotes_v04_to_immutable_parent(
        self,
    ) -> None:
        with (V5 / "executable_model_manifest.tsv").open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        by_version: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            by_version.setdefault(row["model_version"], []).append(row)
        self.assertIn(V5_ID, by_version)
        v5_rows = by_version[V5_ID]
        self.assertEqual(len(v5_rows), 1)
        self.assertEqual(v5_rows[0]["artifact_role"], "full_executable_superset")
        self.assertEqual(
            v5_rows[0]["parent_model_key"], "adoc_literature_superset_v040"
        )
        self.assertEqual(v5_rows[0]["disposition"], "scaffold_copy_of_v040")
        self.assertEqual(v5_rows[0]["claim_boundary"], "scaffold_only_no_new_claim")
        for row in by_version[V4_ID]:
            self.assertEqual(row["disposition"], "immutable_parent")

    def test_the_readme_says_scaffold_and_names_this_version(self) -> None:
        text = (V5 / "README.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# ADOC Literature Superset v0.5.0"))
        self.assertIn("scaffold", text.lower())
        self.assertIn(V4_ID, text)


class ScaffoldRuntimeTest(unittest.TestCase):
    def test_both_versions_resolve_and_v04_stays_resolvable(self) -> None:
        registry = available_models(ROOT)
        self.assertIn(V4_ID, registry)
        self.assertIn(V5_ID, registry)
        self.assertEqual(resolve_model(V5_ID, ROOT).model_version, V5_ID)
        self.assertEqual(resolve_model(V4_ID, ROOT).model_version, V4_ID)

    def test_v05_writes_to_its_own_output_root(self) -> None:
        """Separate v0.5 artifact versioning: v0.5 runs cannot land on v0.4's."""
        v4 = resolve_model(V4_ID, ROOT)
        v5 = resolve_model(V5_ID, ROOT)
        self.assertNotEqual(v5.output_root, v4.output_root)
        self.assertEqual(v5.output_root.name, V5_ID)

    def test_the_default_model_is_still_the_baseline(self) -> None:
        """Adding v0.5 must not silently become anyone's default."""
        self.assertEqual(resolve_model(None, ROOT).model_version, "adoc-core-v0.1.0")


if __name__ == "__main__":
    unittest.main()
