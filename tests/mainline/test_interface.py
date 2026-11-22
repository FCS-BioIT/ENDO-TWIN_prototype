"""Epithelial-stromal interface and the per-cell regulatory-unit API."""

from __future__ import annotations

import itertools
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from endotwin.model import load_model, scenario_label, split_compartments
from endotwin.regulatory_unit import RegulatoryUnit
from endotwin.structure import fixed_point

MODEL = load_model()


def _compose(selection, inputs):
    """Fixed point of the two compartment networks coupled through RX_ inputs."""
    nets = split_compartments(MODEL, selection)
    received = {rx: 0 for net in nets.values() for rx in net.received_inputs}
    states: dict[str, int] = {}
    for _ in range(12):  # acyclic coupling: settles after one pass per hop
        previous = dict(received)
        states = {}
        for net in nets.values():
            free = {n: inputs.get(n, 0) for n in net.medium_inputs}
            free.update({rx: received[rx] for rx in net.received_inputs})
            states.update(fixed_point(net.rules, free))
        for net in nets.values():
            for rx, source in net.received_inputs.items():
                received[rx] = states[source]
        if received == previous:
            break
    return states


class CompartmentSplit(unittest.TestCase):
    def test_default_split_exposes_exactly_the_declared_interface(self):
        nets = split_compartments(MODEL)
        self.assertEqual(
            nets["stroma"].received_inputs,
            {"RX_X_IHH": "X_IHH", "RX_X_BMP2": "X_BMP2"},
        )
        self.assertEqual(
            nets["epithelium"].received_inputs,
            {"RX_X_PARACRINE_MITOGEN": "X_PARACRINE_MITOGEN"},
        )
        self.assertEqual(
            set(nets["extracellular"].received_inputs.values()),
            {
                "E_IHH",
                "OUT_EPITHELIAL_SECRETORY",
                "S_BMP2",
                "S_PARACRINE_MITOGEN",
                "S_PRL",
                "S_IGFBP1",
            },
        )
        # Cells never read each other directly: every crossing goes through the
        # shared extracellular space.
        for cell in ("epithelium", "stroma"):
            for source in nets[cell].received_inputs.values():
                self.assertEqual(MODEL.compartment(source), "extracellular")
        declared = {(i["signal_node"], i["receiving_node"]) for i in MODEL.interface}
        crossing = {
            (s, t)
            for t, logic in MODEL.rules.items()
            for s in MODEL.rules
            if s != t
            and MODEL.compartment(s) in {"epithelium", "extracellular", "stroma"}
            and MODEL.compartment(t) in {"epithelium", "extracellular", "stroma"}
            and MODEL.compartment(s) != MODEL.compartment(t)
            and s in logic.replace("(", " ").replace(")", " ").split()
        }
        self.assertEqual(crossing, declared)

    def test_every_node_belongs_to_exactly_one_compartment_network(self):
        nets = split_compartments(MODEL)
        own = [
            n
            for net in nets.values()
            for n in net.rules
            if not n.startswith(("RX_", "IN_"))
        ]
        self.assertEqual(
            sorted(own), sorted(n for n in MODEL.rules if not n.startswith("IN_"))
        )

    def test_coupled_compartments_reproduce_the_integrated_network(self):
        for selection in MODEL.scenarios():
            rules = MODEL.rules_for(selection)
            for values in itertools.product((0, 1), repeat=len(MODEL.inputs)):
                inputs = dict(zip(MODEL.inputs, values, strict=True))
                integrated = fixed_point(rules, inputs)
                coupled = _compose(selection, inputs)
                for node in rules:
                    if not node.startswith("IN_"):
                        self.assertEqual(
                            coupled[node],
                            integrated[node],
                            (scenario_label(selection), inputs, node),
                        )

    def test_alternative_rules_change_the_interface_only_where_declared(self):
        autonomous = split_compartments(
            MODEL, MODEL.selection_from_ids(["Q2_epithelial_autonomous"])
        )
        # The receptor still reads the ligand, but proliferation no longer reads it.
        self.assertNotIn(
            "E_FGFR_ERK", autonomous["epithelium"].rules["OUT_EPITHELIAL_PROLIFERATION"]
        )
        direct = split_compartments(
            MODEL, MODEL.selection_from_ids(["Q2_relay_plus_direct_v051"])
        )
        self.assertEqual(
            direct["epithelium"].received_inputs,
            {"RX_S_HAND2": "S_HAND2", "RX_X_PARACRINE_MITOGEN": "X_PARACRINE_MITOGEN"},
        )


class RegulatoryUnitApi(unittest.TestCase):
    def test_stromal_unit_runs_on_its_own(self):
        unit = RegulatoryUnit(MODEL, compartment="stroma", sample_count=300, seed=2)
        self.assertIn("RX_X_IHH", unit.input_nodes)
        self.assertIn("RX_X_BMP2", unit.input_nodes)
        unit.set_inputs(
            {"IN_PROGESTIN": 1, "IN_cAMP": 1, "RX_X_IHH": 1, "RX_X_BMP2": 1}
        )
        probs = unit.step(20.0)
        self.assertEqual(probs["OUT_STROMAL_DECIDUALIZATION"], 1.0)
        self.assertEqual(unit.outputs()["S_PARACRINE_MITOGEN"], 0.0)

    def test_state_is_carried_between_steps_and_can_be_sampled(self):
        unit = RegulatoryUnit(MODEL, compartment="epithelium", sample_count=300, seed=5)
        unit.set_inputs({"IN_E2": 1, "RX_X_PARACRINE_MITOGEN": 1})
        unit.step(20.0)
        self.assertEqual(unit.probabilities()["OUT_EPITHELIAL_PROLIFERATION"], 1.0)
        unit.set_inputs({"RX_X_PARACRINE_MITOGEN": 0})
        early = unit.step(0.3)["OUT_EPITHELIAL_PROLIFERATION"]
        self.assertGreater(early, 0.5)  # decays from ON; no restart
        state = unit.sample_state(random.Random(0))
        self.assertEqual(set(state), set(unit.state_nodes))

    def test_initialise_from_a_cell_state(self):
        unit = RegulatoryUnit(MODEL, compartment="stroma", sample_count=200, seed=7)
        unit.initialize({"S_HAND2": 1})
        self.assertEqual(unit.probabilities()["S_HAND2"], 1.0)
        with self.assertRaises(KeyError):
            unit.initialize({"NOT_A_NODE": 1})
        with self.assertRaises(KeyError):
            unit.set_inputs({"S_HAND2": 1})


if __name__ == "__main__":
    unittest.main()
