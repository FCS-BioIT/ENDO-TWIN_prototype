"""The implementation digest covers the MaBoSS adapter, and only what it lists.

`maboss_adapter.py` renders the executed network and projects the joint state
carried between protocol phases, so an edit to it changes simulated numbers. It
was outside `IMPLEMENTATION_GLOBS`, and an audit mutation of the joint
continuation passed every provenance digest. These tests work on a copy of the
digested files, so nothing in the checkout is touched.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.concordance.simulate import (
    IMPLEMENTATION_GLOBS,
    implementation_digest,
    implementation_files,
)

ADAPTER = "src/dt_adoc/maboss_adapter.py"
#: Files that must stay outside the digest: an unrelated module the suite
#: already asserts is not globbed (test_compartment_attribution), and prose.
UNRELATED = ("src/dt_adoc/observations/compartment_attribution.py", "docs/README.md")


class AdapterIsDigested(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.copy = Path(self._tmp.name)
        # The adapter is copied explicitly, so a digest that stopped listing it
        # fails the mutations below instead of erroring on a missing file.
        for relative in {*implementation_files(ROOT), ADAPTER, *UNRELATED}:
            target = self.copy / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.baseline = implementation_digest(self.copy)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_the_adapter_is_in_the_inventory(self) -> None:
        self.assertIn(ADAPTER, IMPLEMENTATION_GLOBS)
        self.assertIn(ADAPTER, implementation_files(ROOT))

    def test_the_copy_reproduces_the_live_digest(self) -> None:
        # Otherwise the mutations below would be measured against the wrong thing.
        self.assertEqual(implementation_files(self.copy), implementation_files(ROOT))
        self.assertEqual(self.baseline, implementation_digest(ROOT))

    def test_appending_to_the_adapter_changes_the_digest(self) -> None:
        adapter = self.copy / ADAPTER
        adapter.write_bytes(adapter.read_bytes() + b"\n# probe\n")
        self.assertNotEqual(implementation_digest(self.copy), self.baseline)

    def test_editing_the_joint_projection_changes_the_digest(self) -> None:
        adapter = self.copy / ADAPTER
        text = adapter.read_text(encoding="utf-8")
        body = re.search(
            r"\ndef project_joint_distribution\(.*?(?=\ndef )", text, re.DOTALL
        )
        self.assertIsNotNone(body, "project_joint_distribution moved")
        edited = body.group(0).replace(
            "probability_cutoff", "probability_cutoff * 1.0", 1
        )
        self.assertNotEqual(edited, body.group(0), "no cutoff reference to edit")
        adapter.write_text(text.replace(body.group(0), edited), encoding="utf-8")
        self.assertNotEqual(implementation_digest(self.copy), self.baseline)

    def test_removing_the_adapter_changes_the_digest(self) -> None:
        (self.copy / ADAPTER).unlink()
        self.assertNotEqual(implementation_digest(self.copy), self.baseline)

    def test_unrelated_files_do_not_change_the_digest(self) -> None:
        for relative in UNRELATED:
            with self.subTest(path=relative):
                self.assertNotIn(relative, implementation_files(ROOT))
                path = self.copy / relative
                path.write_bytes(path.read_bytes() + b"\n# probe\n")
                self.assertEqual(implementation_digest(self.copy), self.baseline)
        added = self.copy / "src/dt_adoc/_digest_probe.py"
        added.write_text("x = 1\n", encoding="utf-8")
        self.assertEqual(implementation_digest(self.copy), self.baseline)


if __name__ == "__main__":
    unittest.main()
