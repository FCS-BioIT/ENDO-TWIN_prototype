"""T-H -- v0.4 is frozen, and cannot be edited into agreement with its own record.

U1 of `docs/v05_mechanistic_integration_plan.md`. v0.5 is developed beside v0.4,
not on top of it, so every claim, figure, ranking and digest already published
against v0.4 has to keep resolving to the same bytes.

The obvious test -- check each file against the hash `provenance.toml` records --
catches a careless edit and misses a deliberate one, because an editor who
changes `network.bnd` can restate `network_bnd_sha256` in the same commit and
the check still passes. So `provenance.toml` is itself pinned here, to a literal
written into this file. Changing a v0.4 artifact now requires changing its hash
in provenance, which changes provenance's hash, which fails against this
literal.

WHAT THAT DOES AND DOES NOT BUY, stated because an earlier draft of this
docstring overstated it as "there is no edit to v0.4 that this suite accepts".
It is not true and no in-repo test can make it true: an agent willing to edit
`PROVENANCE_SHA256` below can still change v0.4 and get a green suite. What the
pin does is force that tampering INTO THE DIFF, as an edit to a test file whose
only purpose is to prevent it -- which a reviewer can see and a silent
regeneration cannot hide. This is TAMPER-EVIDENT, REVIEW-ENFORCED immutability,
not a cryptographic guarantee. Treat a diff that touches `PROVENANCE_SHA256` as
a claim that v0.4 should stop being immutable, and review it as that claim.

Immutability is asserted over EVERY file in the directory, enumerated from disk
rather than from the record, so a file cannot be ADDED to a frozen model without
failing -- an omission the record alone cannot detect.
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "models" / "superset" / "adoc-literature-superset-v0.4.0"

#: v0.4's own provenance record, pinned. See the module docstring for why a
#: literal is required here and a self-consistency check is not enough.
PROVENANCE_SHA256 = "ec1183e474a6970fe3b5f9f4c2e7d8714ef08bdfd196630c2693aab873582484"

#: Every file in the frozen directory. 18 named artifacts + topology.tsv + 21
#: condition cfgs + provenance.toml. Asserted, so the count cannot drift.
EXPECTED_FILE_COUNT = 41


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class V04ImmutabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = tomllib.loads(
            (V4 / "provenance.toml").read_text(encoding="utf-8")
        )
        cls.files = sorted(p for p in V4.rglob("*") if p.is_file())

    def test_the_provenance_record_itself_is_pinned(self) -> None:
        """Without this, every other assertion here is self-referential."""
        self.assertEqual(
            sha256(V4 / "provenance.toml"),
            PROVENANCE_SHA256,
            "v0.4 provenance.toml changed. v0.4 is an immutable parent: if a "
            "v0.5 change needs different content, it belongs in "
            "models/superset/adoc-literature-superset-v0.5.0/, not here.",
        )

    def test_the_directory_holds_exactly_the_files_it_held(self) -> None:
        """Enumerated from disk: the record cannot report a file nobody added."""
        self.assertEqual(len(self.files), EXPECTED_FILE_COUNT)

    def test_every_named_artifact_matches_its_recorded_digest(self) -> None:
        artifacts = self.payload["artifacts"]
        hashes = self.payload["artifact_hashes"]
        self.assertEqual(len(artifacts), 18)
        for name, rel in sorted(artifacts.items()):
            with self.subTest(artifact=name):
                path = ROOT / rel
                self.assertTrue(path.is_file(), f"{rel} is missing")
                self.assertEqual(sha256(path), hashes[f"{name}_sha256"])

    def test_topology_matches_its_recorded_digest(self) -> None:
        """topology.tsv carries a hash but no [artifacts] row, so it needs its own.

        That asymmetry is v0.4's and is left as found; the file is frozen either
        way and this is what keeps it covered.
        """
        self.assertNotIn("topology", self.payload["artifacts"])
        self.assertEqual(
            sha256(V4 / "topology.tsv"),
            self.payload["artifact_hashes"]["topology_sha256"],
        )

    def test_every_condition_cfg_matches_its_recorded_digest(self) -> None:
        recorded = self.payload["condition_hashes"]
        cfgs = sorted((V4 / "conditions").glob("*.cfg"))
        self.assertEqual(len(cfgs), 21)
        self.assertEqual(len(recorded), 21)
        for cfg in cfgs:
            with self.subTest(condition=cfg.name):
                key = f"{cfg.stem}_cfg_sha256"
                self.assertIn(key, recorded)
                self.assertEqual(sha256(cfg), recorded[key])

    def test_every_file_on_disk_is_covered_by_one_of_the_assertions_above(self) -> None:
        """The count alone would pass if a file were swapped for another.

        This closes that: the set of files is exactly the set the record plus
        the two explicit exceptions account for.
        """
        accounted = {V4 / "provenance.toml", V4 / "topology.tsv"}
        accounted |= {ROOT / rel for rel in self.payload["artifacts"].values()}
        accounted |= set((V4 / "conditions").glob("*.cfg"))
        self.assertEqual(set(self.files), accounted)


if __name__ == "__main__":
    unittest.main()
