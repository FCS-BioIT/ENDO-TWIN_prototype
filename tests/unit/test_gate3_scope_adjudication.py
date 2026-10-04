"""Pins the structural claims in `docs/gate3_scope_adjudication.md`.

Same contract as `test_adhesion_variability_semantics`: each assertion is the
reason a documented conclusion holds, and each fails if the limitation it
records is repaired, at which point the document must be revised rather than
the test loosened.

What is pinned is structural only. The scope decisions the document makes --
that adhesion should be diagnostic, that three relays belong outside the core
DT, that anti-SPP1 is de-prioritised -- are judgements from these facts and are
deliberately not asserted here.
"""

from __future__ import annotations

import unittest

from dt_adoc.reporting.identifiability import (
    _evaluate,
    _latent_seeds,
    _topological_order,
    load_identifiability,
    parse_bnd_rules,
    resolve_model,
)

MODEL = "adoc-literature-superset-v0.4.0"
COMPETENCE = "OUT_MATERNAL_ADHESION_COMPETENCE"
ENDPOINT = "OUT_STABLE_ADHESION"
EMBRYO_INPUTS = ("IN_EMBRYO_PRESENT", "IN_TROPHECTODERM_COMPETENT", "IN_EMBRYO_CONTACT")
INTERFACE_RELAYS = {
    "X_INTERFACE_SPP1_RELAY": True,
    "X_INTERFACE_REDUNDANT_RELAY": True,
    "X_INTERFACE_ANTIADHESIVE_RELAY": False,
}


class _Structure(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_identifiability(MODEL)
        spec = resolve_model(cls.facts.model_version)
        cls.rules = parse_bnd_rules(spec.network_bnd)
        cls.order = _topological_order(
            cls.rules, {n for n in cls.rules if cls.rules[n].strip() == n}
        )
        cls.seeds, cls.states, cls.mask = _latent_seeds(cls.facts.latent)

    def _arm(self, arm_id: str):
        return next(a for a in self.facts.arms if a.arm_id == arm_id)

    def _count(self, inputs: dict[str, bool], node: str) -> int:
        column = _evaluate(self.rules, self.order, self.seeds, self.mask, inputs)[node]
        return (column & self.mask).bit_count()


class EmbryoCompetenceCannotRescueMifepristoneTest(_Structure):
    """§1: the endpoint is a conjunction, so a structural zero absorbs everything."""

    ARM = "adhesion_challenge_hormone_treated_mifepristone"

    def test_maternal_competence_is_zero_under_mifepristone(self) -> None:
        self.assertEqual(self._count(self._arm(self.ARM).inputs, COMPETENCE), 0)

    def test_forcing_every_embryo_input_still_gives_no_adhesion(self) -> None:
        inputs = dict(self._arm(self.ARM).inputs)
        inputs.update(dict.fromkeys(EMBRYO_INPUTS, True))
        self.assertEqual(
            self._count(inputs, ENDPOINT),
            0,
            "embryo competence now rescues the mifepristone arm; "
            "docs/gate3_scope_adjudication.md §1 says it cannot",
        )

    def test_the_embryo_inputs_are_conjuncts_of_the_endpoint(self) -> None:
        """The reason the above holds, rather than a coincidence of this arm."""
        rule = self.rules[ENDPOINT]
        self.assertNotIn(" or ", rule)
        for node in (COMPETENCE, *EMBRYO_INPUTS):
            self.assertIn(node, rule)


class MaternalNetworkIsUpstreamOfTheRelaysTest(_Structure):
    """§2: removing the interface relays disturbs no maternal readout."""

    @property
    def maternal(self) -> list[str]:
        return sorted(
            n
            for n in self.facts.node_ids
            if n.startswith(("E_", "S_"))
            or n in ("OUT_EPITHELIAL_RECEPTIVE", "OUT_STROMAL_DECIDUALIZED")
        )

    def test_we_are_actually_checking_a_nonempty_set(self) -> None:
        self.assertGreater(len(self.maternal), 25)

    def test_no_maternal_readout_changes_in_any_arm(self) -> None:
        changed = []
        for arm in self.facts.arms:
            pinned = {**arm.inputs, **INTERFACE_RELAYS}
            for node in self.maternal:
                if self._count(arm.inputs, node) != self._count(pinned, node):
                    changed.append(f"{arm.arm_id}:{node}")
        self.assertEqual(
            changed,
            [],
            "maternal readouts now depend on the interface relays, so the "
            "variability question can reach maternal topology; "
            "docs/gate3_scope_adjudication.md §2 says it cannot",
        )

    def test_the_endpoint_does_change_so_the_probe_is_not_inert(self) -> None:
        arm = self._arm("adhesion_challenge_hormone_treated")
        self.assertNotEqual(
            self._count(arm.inputs, ENDPOINT),
            self._count({**arm.inputs, **INTERFACE_RELAYS}, ENDPOINT),
        )


class MechanicalRelayIsNotAPenetranceCoinTest(_Structure):
    """§4: the fourth relay is categorically different from the other three."""

    def test_it_gates_an_upstream_node_not_a_terminal_route(self) -> None:
        rule = self.rules["X_MECHANICAL_PERMISSIVE_ECM"]
        self.assertIn("X_MECHANICAL_STRESS_RELAY", rule)
        for route in ("X_ADHESION_ROUTE_SPP1", "X_ADHESION_ROUTE_REDUNDANT"):
            self.assertNotIn("X_MECHANICAL_STRESS_RELAY", self.rules[route])

    def test_its_stress_inputs_are_off_in_every_recorded_arm(self) -> None:
        """Why it is endpoint-inert: the arms that would excite it never ran."""
        for arm in self.facts.arms:
            for node in ("IN_ER_STRESS_EXCESS", "IN_HIGH_ECM_STIFFNESS"):
                self.assertNotEqual(
                    arm.inputs.get(node),
                    True,
                    f"{arm.arm_id} now excites {node}; the relay is no longer "
                    "inert for the reason §4 gives",
                )


class E2PrimingDiscriminatesTheCd98VariantsTest(_Structure):
    """§9: the top-ranked experiment, and it needs no new arm."""

    def test_the_arm_exists_and_primes_with_e2_alone(self) -> None:
        arm = self._arm("e2_primed_maternal")
        self.assertIs(arm.inputs.get("IN_E2"), True)
        self.assertNotEqual(arm.inputs.get("IN_PROGESTIN"), True)

    def test_stat3_is_off_there_which_is_what_splits_the_variants(self) -> None:
        """CD98-b then predicts OFF and CD98-c predicts ON, oppositely."""
        arm = self._arm("e2_primed_maternal")
        self.assertEqual(self._count(arm.inputs, "E_GP130_STAT3"), 0)
        self.assertEqual(self._count(arm.inputs, "E_PGR"), 0)
        self.assertNotEqual(arm.inputs.get("IN_HCG"), True)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
