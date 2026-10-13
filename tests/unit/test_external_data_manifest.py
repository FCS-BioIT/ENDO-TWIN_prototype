"""`config/external_data_manifest.tsv` records assets NOT held in this repository.

`config/data_manifest.tsv` has a hard invariant: every row names a file that is
present, and its validator fails otherwise. That invariant is worth keeping, so
an asset this repository deliberately does NOT hold cannot live there. This
second manifest is the place for those, and its invariants are the mirror image:
a row must carry a fetchable URL and a verified digest, and must NOT claim the
file is local or that anything has been built on it.

The distinction these tests enforce is the one that matters scientifically:
`structurally_verified` is a statement about availability and contents;
it is NOT a statement that any model constraint has been derived from the asset.
Conflating the two is how "we have the data" becomes "the model uses the data".
"""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "config" / "external_data_manifest.tsv"

FIELDS = (
    "asset_id",
    "source_accession",
    "source_url",
    "filename",
    "size_bytes",
    "sha256",
    "verified_on",
    "verification_method",
    "role",
    "inspection_state",
    "local_policy",
    "notes",
)

#: An external asset is either verified-and-not-integrated, or integrated as an
#: active constraint. There is no third state, and the second requires a
#: corresponding activated row elsewhere -- see the last test.
INSPECTION_STATES = frozenset(
    {
        "declared_not_fetched",
        "fetched_digest_verified",
        "structurally_verified_not_integrated",
        "integrated_as_active_constraint",
    }
)


def _rows() -> list[dict[str, str]]:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        assert tuple(reader.fieldnames or ()) == FIELDS, reader.fieldnames
        return list(reader)


class Schema(unittest.TestCase):
    def test_every_row_is_complete_and_fetchable(self) -> None:
        for row in _rows():
            with self.subTest(asset=row["asset_id"]):
                self.assertTrue(row["source_url"].startswith("https://"))
                self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(int(row["size_bytes"]), 0)
                self.assertIn(row["inspection_state"], INSPECTION_STATES)
                self.assertTrue(row["notes"].strip())

    def test_asset_ids_are_unique(self) -> None:
        ids = [row["asset_id"] for row in _rows()]
        self.assertEqual(len(ids), len(set(ids)))


class TheTwoManifestsStayDisjoint(unittest.TestCase):
    """An asset is local or external, never recorded as both."""

    def test_no_external_asset_is_also_in_the_local_manifest(self) -> None:
        local = ROOT / "config" / "data_manifest.tsv"
        with local.open(newline="", encoding="utf-8") as handle:
            local_names = {
                Path(row["relative_path"]).name
                for row in csv.DictReader(handle, delimiter="\t")
            }
        for row in _rows():
            with self.subTest(asset=row["asset_id"]):
                self.assertNotIn(row["filename"], local_names)

    def test_no_external_asset_is_committed_to_the_repository(self) -> None:
        """The point of this manifest is that the bytes are NOT here."""
        for row in _rows():
            with self.subTest(asset=row["asset_id"]):
                matches = list(ROOT.rglob(row["filename"]))
                inside = [m for m in matches if ".pixi" not in m.parts]
                self.assertEqual(
                    inside,
                    [],
                    f"{row['filename']} is present in the repository, so it is "
                    "a local asset and belongs in config/data_manifest.tsv",
                )


class AvailabilityIsNotIntegration(unittest.TestCase):
    """The distinction this manifest exists to keep.

    Verifying that a public object exists, hashes correctly and contains what
    the paper says is a provenance fact. It licenses NO model claim by itself.
    Promotion to `integrated_as_active_constraint` requires a row somewhere that
    actually activates it, and until such a row exists the state must not be
    claimed.
    """

    def test_nothing_claims_integration_without_an_activated_constraint(
        self,
    ) -> None:
        scrna_map = ROOT / "config" / "scrna_observation_map.tsv"
        with scrna_map.open(newline="", encoding="utf-8") as handle:
            activated = [
                row
                for row in csv.DictReader(handle, delimiter="\t")
                if row["activation_status"]
                in {"active_constraint", "active_diagnostic"}
            ]
        for row in _rows():
            if row["inspection_state"] == "integrated_as_active_constraint":
                with self.subTest(asset=row["asset_id"]):
                    self.assertTrue(
                        activated,
                        f"{row['asset_id']} claims integration but no row in "
                        "config/scrna_observation_map.tsv is an active "
                        "constraint or diagnostic",
                    )

    def test_the_scrna_object_is_verified_but_not_integrated(self) -> None:
        """Pins today's honest state, so a later edit cannot quietly upgrade it."""
        rows = {row["asset_id"]: row for row in _rows()}
        self.assertEqual(
            rows["EXT-SCRNA-001"]["inspection_state"],
            "structurally_verified_not_integrated",
        )


if __name__ == "__main__":
    unittest.main()
