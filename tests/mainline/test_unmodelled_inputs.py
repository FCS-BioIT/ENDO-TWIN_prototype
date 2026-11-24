"""XAV939 is declared, applied in every supplemented arm, and read by nothing.

The published ADOC regimen is E2 + MPA + 8-Br-cAMP + **XAV939**, applied as one
four-component cocktail. ``IN_XAV939`` is therefore part of the experimental
definition and must stay in the network, but no Boolean rule reads it.

That is a curated decision, not an oversight. ``docs/curation_increment_01_xav939.md``
searched for a study testing XAV939, tankyrase inhibition or canonical-WNT
manipulation in human endometrial epithelium or stroma, found none, and
**rejected** every candidate edge -- including the composite
``IN_XAV939 -> E_SECRETORY_STATE`` chain, which no single experiment tests, and
any stromal or global WNT-inhibition edge. The negative result is recorded
there.

These tests exist so that the consequence of that decision cannot be forgotten
or silently reversed:

1. the model is **silent** on XAV939 -- toggling it changes no node, in any
   condition, under any scenario; and
2. silence is not a prediction. "The model says XAV939 does nothing" would be a
   misreading. The model says nothing about XAV939 at all, which is why no
   response under the supplemented regimen may be attributed to the hormones
   alone.

If a future increment ever wires XAV939 in, these tests fail, and whoever
changes them has to justify the edge against the rejection ledger in that
curation increment.
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from endotwin.model import load_model
from endotwin.protocols import load_protocols
from endotwin.simulate import SimulationSettings, simulate_condition

MODEL = load_model()
PROTOCOLS = load_protocols(MODEL)
UNMODELLED = "IN_XAV939"


class XAV939IsDeclaredButUnread(unittest.TestCase):
    def test_the_input_node_exists(self) -> None:
        """It is part of the experimental definition, so it may not be deleted."""
        self.assertIn(UNMODELLED, MODEL.nodes)
        self.assertIn(UNMODELLED, MODEL.inputs)

    def test_no_rule_reads_it_in_any_scenario(self) -> None:
        """Zero out-degree, checked across every rule-variant combination.

        Checking only the default network would miss a variant that introduced
        the edge, which is exactly where an unjustified one would land.
        """
        offenders: list[str] = []
        for selection in MODEL.scenarios():
            for node, logic in MODEL.rules_for(selection).items():
                if node == UNMODELLED:
                    continue
                tokens = logic.replace("(", " ").replace(")", " ").split()
                if UNMODELLED in tokens:
                    offenders.append(f"{node} = {logic}")
        self.assertEqual(
            sorted(set(offenders)),
            [],
            f"{UNMODELLED} is read by a rule. If that edge is intended, it must "
            "first clear the rejection ledger in "
            "docs/curation_increment_01_xav939.md, which refused the direct, the "
            "stromal and the global WNT-inhibition edges on the record that no "
            "study tests them in endometrium.",
        )

    def test_the_protocols_really_do_apply_it(self) -> None:
        """Otherwise the test above would pass for the uninteresting reason."""
        applied = [
            condition_id
            for condition_id, condition in PROTOCOLS.conditions.items()
            for phase in condition.phases
            if phase.inputs.get(UNMODELLED)
        ]
        self.assertNotEqual(applied, [], "no condition applies XAV939")


class SilenceIsNotAPrediction(unittest.TestCase):
    """Toggling XAV939 moves nothing, and that is a limitation, not a result."""

    def test_toggling_it_changes_no_node(self) -> None:
        condition = PROTOCOLS.conditions["reference"]
        self.assertTrue(
            any(phase.inputs.get(UNMODELLED) for phase in condition.phases),
            "the reference condition should carry XAV939",
        )
        settings = SimulationSettings(sample_count=2000, seed=1)
        with_xav = simulate_condition(
            MODEL, condition, PROTOCOLS.interventions, None, settings
        )

        stripped = replace(
            condition,
            phases=tuple(
                replace(
                    phase,
                    inputs={
                        node: value
                        for node, value in phase.inputs.items()
                        if node != UNMODELLED
                    },
                )
                for phase in condition.phases
            ),
        )
        without_xav = simulate_condition(
            MODEL, stripped, PROTOCOLS.interventions, None, settings
        )

        def downstream(result: object) -> dict[str, float]:
            # Every node but the input itself, whose own value is of course the
            # thing being toggled.
            final = result.phases[-1].final  # type: ignore[attr-defined]
            return {n: v for n, v in final.items() if n != UNMODELLED}

        self.assertEqual(
            downstream(with_xav),
            downstream(without_xav),
            "removing XAV939 changed a node value; the model is no longer silent "
            "about it and the documented limitation is stale",
        )
        # Guard the guard: the input really was toggled.
        self.assertEqual(with_xav.phases[-1].final[UNMODELLED], 1.0)
        self.assertEqual(without_xav.phases[-1].final[UNMODELLED], 0.0)

    def test_the_limitation_is_documented_where_a_reader_will_meet_it(self) -> None:
        dictionary = (
            ROOT / "endotwin/models" / MODEL.version / "node_dictionary.tsv"
        ).read_text(encoding="utf-8")
        row = next(
            line
            for line in dictionary.splitlines()
            if line.startswith(UNMODELLED + "\t")
        )
        self.assertIn("Read by no rule", row)


if __name__ == "__main__":
    unittest.main()
