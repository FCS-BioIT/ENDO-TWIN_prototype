"""The mainline's copy of the topology helpers agrees with the legacy package.

``src/endotwin/topology.py`` copies ``parse_bnd_rules`` and
``derive_dependencies`` so that the ENDO-TWIN package does not import the
legacy one. This test keeps the two copies equivalent on every executable
network in the repository.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from dt_adoc.model import topology as legacy
from endotwin import topology as mainline

NETWORKS = sorted(
    p
    for p in ROOT.glob("**/network.bnd")
    if ".pixi" not in p.parts and "output" not in p.parts
)


class TopologyParity(unittest.TestCase):
    def test_there_are_networks_to_compare(self):
        self.assertGreaterEqual(len(NETWORKS), 8)

    def test_both_copies_parse_and_sign_every_network_identically(self):
        for path in NETWORKS:
            with self.subTest(network=str(path.relative_to(ROOT))):
                rules = mainline.parse_bnd_rules(path)
                self.assertEqual(rules, legacy.parse_bnd_rules(path))
                self.assertEqual(
                    mainline.derive_dependencies(rules),
                    legacy.derive_dependencies(rules),
                )


if __name__ == "__main__":
    unittest.main()
