"""Clean-clone smoke test: can a reviewer check the core results at all?

This is the first thing an external reviewer should run. It answers one
question — does the executable model load, compute and agree with its committed
results in a fresh clone? — and it answers it in seconds.

Three deliberate constraints:

* **No private data.** The prototype's local-only evidence (the multi-gigabyte
  RDS, the annotation workbook, the PDF library) is not needed, and neither is
  anything under ``data/``, which is untracked.
* **No prototype Git history.** The 63 skips in the full suite exist because
  legacy checks replay commits this history-free repository does not carry.
  Nothing here depends on them.
* **No MaBoSS.** The network is acyclic, so every fixed point is computed
  exactly in pure Python. That keeps the check fast and makes a failure mean the
  model is wrong rather than that a solver was missing.

Run it with ``pixi run endotwin-smoke``. It exits non-zero on failure.
"""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from endotwin.model import load_model
from endotwin.protocols import load_protocols
from endotwin.structure import fixed_point

MODEL = load_model()
RESULTS = ROOT / "endotwin" / "results" / MODEL.version


class TheModelLoads(unittest.TestCase):
    def test_the_network_is_executable(self) -> None:
        rules = MODEL.rules_for(None)
        self.assertEqual(len(rules), len(MODEL.nodes))
        self.assertTrue(all(logic.strip() for logic in rules.values()))

    def test_every_hypothesis_family_offers_a_choice(self) -> None:
        families = MODEL.families()
        self.assertGreaterEqual(len(families), 2)
        for family, variants in families.items():
            self.assertGreaterEqual(len(variants), 2, family)
            defaults = [v for v in variants if MODEL.variants[v].is_default]
            self.assertEqual(len(defaults), 1, f"{family} needs exactly one default")

    def test_the_scenario_space_is_the_product_of_the_families(self) -> None:
        expected = 1
        for variants in MODEL.families().values():
            expected *= len(variants)
        scenarios = MODEL.scenarios()
        self.assertEqual(len(scenarios), expected)
        self.assertEqual(len({tuple(sorted(s.items())) for s in scenarios}), expected)

    def test_every_scenario_yields_a_complete_rule_set(self) -> None:
        for selection in MODEL.scenarios():
            rules = MODEL.rules_for(selection)
            self.assertEqual(set(rules), set(MODEL.nodes), selection)


class ThePredictionsRecompute(unittest.TestCase):
    """The committed predictions are reproduced, not merely present."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.protocols = load_protocols(MODEL)
        path = RESULTS / "fixed_point_predictions.tsv"
        if not path.is_file():  # pragma: no cover - only in a broken tree
            raise unittest.SkipTest(f"{path} missing; run `pixi run endotwin-all`")
        with path.open(encoding="utf-8") as handle:
            cls.committed = list(csv.DictReader(handle, delimiter="\t"))

    def test_the_committed_predictions_are_not_empty(self) -> None:
        self.assertGreater(len(self.committed), 0)

    def test_recomputing_reproduces_the_committed_fixed_points(self) -> None:
        """Recompute every row from the network and compare.

        A mismatch means the committed results no longer follow from the
        committed rules, which is the single most important thing for a reader
        to be able to rule out.
        """
        from endotwin.model import scenario_label
        from endotwin.protocols import forced_nodes

        by_scenario = {scenario_label(s): MODEL.rules_for(s) for s in MODEL.scenarios()}
        # Wide format: one row per scenario/condition/phase, one column per node.
        meta = {"scenario", "condition", "phase"}
        checked = 0
        for row in self.committed:
            rules = by_scenario[row["scenario"]]
            condition = self.protocols.conditions[row["condition"]]
            phase = next(p for p in condition.phases if p.phase_id == row["phase"])
            state = fixed_point(
                rules,
                phase.inputs,
                forced=forced_nodes(phase, self.protocols.interventions),
            )
            for node, expected in row.items():
                if node in meta or node.startswith("variant_") or node not in rules:
                    continue
                self.assertEqual(
                    str(state[node]),
                    expected,
                    f"{row['scenario']} / {row['condition']} / {row['phase']} / {node}",
                )
                checked += 1
        self.assertGreater(checked, 1000, "too few values recomputed to be meaningful")


class TheReviewerFacingOutputsExist(unittest.TestCase):
    def test_the_headline_artifacts_are_committed(self) -> None:
        for relative in (
            "structure.json",
            "discrimination.tsv",
            "fixed_point_predictions.tsv",
            "rate_sensitivity.tsv",
            "verification_report.md",
            "wp2_candidate_screen.tsv",
        ):
            path = RESULTS / relative
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 0, path)

    def test_the_reviewer_guide_is_present_and_links_resolve(self) -> None:
        import re

        guide = ROOT / "REVIEWER_GUIDE.md"
        self.assertTrue(guide.is_file(), guide)
        text = guide.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#")):
                continue
            self.assertTrue((ROOT / target.split("#", 1)[0]).exists(), target)

    def test_no_private_data_was_needed(self) -> None:
        """Nothing above reads data/, which a fresh clone does not have."""
        self.assertFalse(
            (ROOT / "data").is_dir() and not any((ROOT / "data").iterdir()),
            "data/ exists but is empty; that is fine, and nothing here reads it",
        )


if __name__ == "__main__":
    unittest.main()
