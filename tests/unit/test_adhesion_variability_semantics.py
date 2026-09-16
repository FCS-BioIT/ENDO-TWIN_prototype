"""Pins the structural facts behind `docs/adhesion_variability_semantics.md`.

These are claims about the *model as committed*, not about a proposed change.
Each one is the reason a documented conclusion holds, so if a future edit moves
any of them the document becomes wrong silently -- which is the defect class
this repository keeps finding.

Nothing here asserts that the current model is correct. The opposite: several
of these assertions record a limitation, and they fail if the limitation is
repaired, at which point the document must be updated rather than the test
loosened.
"""

from __future__ import annotations

import math
import unittest

from dt_adoc.calibration.adhesion_likelihood import binomial_log_likelihood
from dt_adoc.reporting.identifiability import (
    _evaluate,
    _latent_seeds,
    _topological_order,
    load_identifiability,
    parse_bnd_rules,
    resolve_model,
)

MODEL = "adoc-literature-superset-v0.4.0"
SPP1 = "X_INTERFACE_SPP1_RELAY"
REDUNDANT = "X_INTERFACE_REDUNDANT_RELAY"
ENDPOINT = "OUT_STABLE_ADHESION"


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
        cls.latent = list(cls.facts.latent)

    def _column(self, inputs: dict[str, bool]) -> int:
        return _evaluate(self.rules, self.order, self.seeds, self.mask, inputs)[
            ENDPOINT
        ]

    def _arm(self, arm_id: str):
        return next(a for a in self.facts.arms if a.arm_id == arm_id)

    def _relay_table(self, inputs: dict[str, bool]) -> dict[tuple[int, int], int]:
        """Endpoint at each (SPP1, REDUNDANT) corner, other free variables off."""
        column = self._column(inputs)
        table: dict[tuple[int, int], int] = {}
        si, ri = self.latent.index(SPP1), self.latent.index(REDUNDANT)
        for i in range(self.states):
            bits = [(self.seeds[n] >> i) & 1 for n in self.latent]
            if any(b for j, b in enumerate(bits) if j not in (si, ri)):
                continue
            table[(bits[si], bits[ri])] = (column >> i) & 1
        return table


class DeterministicArmsTest(_Structure):
    """Two of the three challenge arms cannot produce adhesion at all."""

    def test_the_basal_and_mifepristone_arms_are_zero_in_every_assignment(self) -> None:
        for arm_id in (
            "adhesion_challenge_basal",
            "adhesion_challenge_hormone_treated_mifepristone",
        ):
            column = self._column(self._arm(arm_id).inputs) & self.mask
            self.assertEqual(
                column.bit_count(),
                0,
                f"{arm_id} can now reach adhesion in some assignment; "
                "docs/adhesion_variability_semantics.md §4 says it cannot",
            )

    def test_only_the_hormone_treated_arm_varies(self) -> None:
        column = self._column(self._arm("adhesion_challenge_hormone_treated").inputs)
        count = (column & self.mask).bit_count()
        self.assertGreater(count, 0)
        self.assertLess(count, self.states)


class RelayRidgeTest(_Structure):
    """The two carrier relays enter the endpoint only through their OR."""

    def test_the_endpoint_is_the_disjunction_of_the_two_carrier_relays(self) -> None:
        table = self._relay_table(
            self._arm("adhesion_challenge_hormone_treated").inputs
        )
        self.assertEqual(table, {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 1})

    def test_opposite_relay_attributions_are_likelihood_identical(self) -> None:
        """'All SPP1' and 'no SPP1' are the same point on the objective."""
        combined = [1 - (1 - p1) * (1 - p2) for p1, p2 in ((0.82, 0.0), (0.0, 0.82))]
        self.assertAlmostEqual(combined[0], combined[1], places=12)
        values = [
            binomial_log_likelihood(probability=p, successes=9, trials=19)
            for p in combined
        ]
        self.assertEqual(values[0], values[1])

    def test_the_committed_istates_are_not_the_maximum_likelihood_values(self) -> None:
        typed = binomial_log_likelihood(probability=0.82, successes=9, trials=19)
        mle = binomial_log_likelihood(probability=9 / 19, successes=9, trials=19)
        self.assertLess(typed, mle)
        self.assertGreater(mle - typed, 5.0)


class AntiSpp1SeparatesTheRelaysTest(_Structure):
    """The already-declared anti-SPP1 input breaks the ridge.

    The model-identification claim in §2 of the document, and the sole reason
    that arm is called out there. It is not a claim about SPP1 as a target.
    """

    def test_anti_spp1_is_a_declared_input_of_the_committed_model(self) -> None:
        self.assertIn("IN_ANTI_SPP1", self.facts.node_ids)

    def test_under_anti_spp1_the_endpoint_ignores_the_spp1_relay(self) -> None:
        inputs = dict(self._arm("adhesion_challenge_hormone_treated").inputs)
        inputs["IN_ANTI_SPP1"] = True
        table = self._relay_table(inputs)
        self.assertEqual(table, {(0, 0): 0, (0, 1): 1, (1, 0): 0, (1, 1): 1})
        for redundant in (0, 1):
            self.assertEqual(table[(0, redundant)], table[(1, redundant)])


class UnconstrainedRelaysTest(_Structure):
    """Two relays carry istates that no recorded arm can constrain."""

    INERT = ("X_INTERFACE_ANTIADHESIVE_RELAY", "X_MECHANICAL_STRESS_RELAY")

    def test_the_inert_relays_are_still_free_variables(self) -> None:
        for node in self.INERT:
            self.assertIn(node, self.facts.latent)

    def test_they_change_the_endpoint_in_no_recorded_arm(self) -> None:
        for node in self.INERT:
            index = self.latent.index(node)
            for arm in self.facts.arms:
                if ENDPOINT not in {n for n, _ in arm.measured}:
                    continue
                column = self._column(arm.inputs)
                for i in range(self.states):
                    flipped = i ^ (1 << index)
                    if flipped >= self.states:
                        continue
                    bits_i = [(self.seeds[n] >> i) & 1 for n in self.latent]
                    bits_f = [(self.seeds[n] >> flipped) & 1 for n in self.latent]
                    if bits_i[index] == bits_f[index]:
                        continue
                    if any(
                        bits_i[j] != bits_f[j]
                        for j in range(len(self.latent))
                        if j != index
                    ):
                        continue
                    self.assertEqual(
                        (column >> i) & 1,
                        (column >> flipped) & 1,
                        f"{node} now changes {ENDPOINT} in {arm.arm_id}; "
                        "docs/adhesion_variability_semantics.md §4 says no arm "
                        "constrains it",
                    )


class VariabilityAttributionTest(_Structure):
    """§6: the model asserts every embryo is competent.

    The premise of the referred consultation. If a future edit makes the
    embryo-side inputs vary per arm, or de-bundles them so they become
    independently controllable, §6's argument stops holding and the note must
    be revised rather than left standing.
    """

    EMBRYO_INPUTS = (
        "IN_EMBRYO_PRESENT",
        "IN_TROPHECTODERM_COMPETENT",
        "IN_EMBRYO_CONTACT",
    )

    def test_every_challenge_arm_asserts_a_competent_embryo(self) -> None:
        arms = [a for a in self.facts.arms if a.arm_id.startswith("adhesion_challenge")]
        self.assertEqual(len(arms), 3, "the three recorded challenge arms")
        for arm in arms:
            for node in self.EMBRYO_INPUTS:
                self.assertIs(
                    arm.inputs.get(node),
                    True,
                    f"{arm.arm_id} no longer asserts {node}; "
                    "docs/adhesion_variability_semantics.md §6 assumes it does",
                )

    def test_the_embryo_side_inputs_are_not_independently_controllable(self) -> None:
        for node in self.EMBRYO_INPUTS:
            self.assertEqual(
                self.facts.perturbation_status[node],
                "bundled_perturbed",
                f"{node} is no longer bundled_perturbed; §6 rests on the embryo "
                "side carrying no independent determinant",
            )

    def test_no_embryo_side_input_is_a_free_stochastic_variable(self) -> None:
        """The note explicitly declines to promote one; this pins that it has not."""
        for node in self.EMBRYO_INPUTS:
            self.assertNotIn(node, self.facts.latent)


class ClipDominatedLikelihoodTest(unittest.TestCase):
    """The reported log-likelihood is partly a function of the clip constant.

    Recorded, not repaired: how to score a model that assigns an observed event
    probability zero is a methodological fork, and these assertions exist so
    that whichever way it is resolved, the resolution is deliberate.
    """

    def test_a_structural_zero_is_scored_by_the_clip_not_by_the_model(self) -> None:
        value = binomial_log_likelihood(probability=0.0, successes=1, trials=8)
        self.assertAlmostEqual(value, math.log(1e-9), places=6)

    def test_the_held_out_score_moves_with_the_clip_constant_alone(self) -> None:
        """Three decades of clip is ~6.9 nats, with model and data fixed."""
        at = {eps: 1 * math.log(eps) + 7 * math.log(1 - eps) for eps in (1e-6, 1e-12)}
        self.assertAlmostEqual(at[1e-6] - at[1e-12], 6 * math.log(10), places=4)

    def test_a_structural_zero_against_zero_successes_is_unpenalised(self) -> None:
        """The basal arm is matched trivially, so it ranks nothing."""
        value = binomial_log_likelihood(probability=0.0, successes=0, trials=12)
        self.assertAlmostEqual(value, 0.0, places=6)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
