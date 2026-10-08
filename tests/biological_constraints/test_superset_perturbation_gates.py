"""Biological regression gates for adoc-literature-superset-v0.3.0 perturbations.

These gates run at a **converged readout horizon**, not at the durations
declared in `config/protocols.yaml`. At the declared duration the adhesion
endpoints are sampled roughly 4000x before they reach their logical fixed
point, so every perturbation contrast measured there compares two transients
and is uninterpretable. See `docs/endpoint_convergence_finding.md` for the
evidence.

Running the gates at a converged horizon therefore tests the property that is
actually being asserted -- that the Boolean logic produces the expected
qualitative ordering -- rather than the artifact. It deliberately does NOT
assert calibrated magnitudes: the converged reference value (~0.82) is far from
the observed adhesion frequency (9/19), and the model remains uncalibrated.

Uncertainty handling: each gate requires the direction to hold on **every**
seed in `SEEDS`, and requires the mean effect to exceed `MIN_EFFECT_SD_RATIO`
times the across-seed standard deviation of the per-seed differences. A single
seed point estimate is never sufficient. Observed effect sizes here are three
to four orders of magnitude above the seed noise, so the criterion is
comfortable rather than marginal.
"""

from __future__ import annotations

import statistics
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.simulation.runner import (
    _input_override_text,
    _timing_override_text,
    protocol_continuation,
    run_cmaboss_condition,
    run_protocol,
)

MODEL_VERSION = "adoc-literature-superset-v0.4.0"

#: Relative time the challenge phase needs to reach its fixed point. The
#: endpoint is flat between 20 and 60 relative units; 20 is the cheapest
#: horizon that is unambiguously converged.
CONVERGED_DURATION = 20.0

#: Bounded on purpose. Effect sizes at a converged horizon are 0.24-0.82 with
#: seed SD <= 0.0007, so a small budget resolves them with enormous margin.
TRAJECTORY_COUNT = 2000
SEEDS = (1, 2, 3)
MIN_EFFECT_SD_RATIO = 3.0

COMPETENCE = "OUT_MATERNAL_ADHESION_COMPETENCE"
STABLE = "OUT_STABLE_ADHESION"


def _maternal_lineage(terminal_protocol: str) -> tuple[str, ...]:
    """Every phase before the challenge, READ from the resolved graph.

    This used to be a hardcoded three-phase tuple (basal -> E2 -> HT), which was
    correct only while every challenge was seeded from `hormone_treated_maternal`.
    Once each named perturbation challenge is seeded from its own maternal phase,
    a fixed list either omits that phase or silently runs the wrong arm -- the
    first is a KeyError, the second would be worse. Deriving it means these gates
    always exercise the lineage the model actually declares.
    """
    from dt_adoc.concordance.simulate import protocol_lineage

    return protocol_lineage(terminal_protocol, model_version=MODEL_VERSION, root=ROOT)[
        :-1
    ]


def _challenge_at_converged_horizon(
    terminal_protocol: str, seed: int
) -> dict[str, float]:
    """Run the real maternal lineage, then the challenge to convergence."""
    upstream: dict[str, object] = {}
    for protocol_id in _maternal_lineage(terminal_protocol):
        protocol = get_protocol(protocol_id, ROOT, model_version=MODEL_VERSION)
        continuation = None
        if protocol.continuation_from is not None:
            continuation = protocol_continuation(
                protocol_id,
                upstream[protocol.continuation_from],
                model_version=MODEL_VERSION,
                root=ROOT,
            )
        upstream[protocol_id] = run_protocol(
            protocol_id,
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=continuation,
            seed=seed,
            sample_count=TRAJECTORY_COUNT,
        )

    protocol = get_protocol(terminal_protocol, ROOT, model_version=MODEL_VERSION)
    step = protocol.steps[0]
    continuation = protocol_continuation(
        terminal_protocol,
        upstream[protocol.continuation_from],
        model_version=MODEL_VERSION,
        root=ROOT,
    )
    result = run_cmaboss_condition(
        model_version=MODEL_VERSION,
        condition_cfg=ROOT / protocol.condition_cfg,
        root=ROOT,
        override_texts=[
            _input_override_text(step.input_states),
            _timing_override_text(relative_duration=CONVERGED_DURATION, root=ROOT),
        ],
        continuation=continuation,
        seed=seed,
        sample_count=TRAJECTORY_COUNT,
    )
    return result.last


class ConvergedPerturbationGateTest(unittest.TestCase):
    """Direction gates for the perturbation arms, at a converged horizon."""

    results: dict[str, list[dict[str, float]]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.results = {}
        for label in (
            "adhesion_challenge_hormone_treated",
            "adhesion_challenge_hormone_treated_mifepristone",
            "adhesion_challenge_hormone_treated_anti_spp1",
            "adhesion_challenge_excess_er_stress",
            "adhesion_challenge_high_ecm_stiffness",
            "adhesion_challenge_hormone_treated_hand2_loss",
        ):
            cls.results[label] = [
                _challenge_at_converged_horizon(label, seed) for seed in SEEDS
            ]

    def assert_decreases(self, arm: str, endpoint: str) -> None:
        """Require a decrease vs hormone-treated on every seed, above noise."""
        reference = [
            row[endpoint] for row in self.results["adhesion_challenge_hormone_treated"]
        ]
        treated = [row[endpoint] for row in self.results[arm]]
        differences = [t - r for t, r in zip(treated, reference, strict=True)]

        self.assertTrue(
            all(difference < 0 for difference in differences),
            f"{arm}: {endpoint} must decrease vs hormone-treated on every seed; "
            f"got {differences}",
        )
        spread = statistics.stdev(differences) if len(differences) > 1 else 0.0
        if spread > 0.0:
            ratio = abs(statistics.mean(differences)) / spread
            self.assertGreater(
                ratio,
                MIN_EFFECT_SD_RATIO,
                f"{arm}: {endpoint} effect {statistics.mean(differences):.6f} is "
                f"only {ratio:.2f}x the across-seed SD {spread:.6f}",
            )

    # --- Evidence-backed gates -------------------------------------------
    # Mifepristone is the one perturbation arm with held-out manuscript counts
    # (1/8 versus 9/19 hormone-treated), so its direction is a genuine
    # falsification criterion rather than a mechanistic expectation.

    def test_mifepristone_reduces_adhesion_competence(self) -> None:
        self.assert_decreases(
            "adhesion_challenge_hormone_treated_mifepristone", COMPETENCE
        )

    def test_mifepristone_reduces_stable_adhesion(self) -> None:
        self.assert_decreases("adhesion_challenge_hormone_treated_mifepristone", STABLE)

    # --- Mechanistic-expectation gates -----------------------------------
    # No held-out adhesion counts exist for these arms. They are gated on
    # direction only, never on magnitude, and must not be read as validation.

    def test_anti_spp1_reduces_adhesion_competence(self) -> None:
        self.assert_decreases(
            "adhesion_challenge_hormone_treated_anti_spp1", COMPETENCE
        )

    def test_excess_er_stress_reduces_adhesion_competence(self) -> None:
        self.assert_decreases("adhesion_challenge_excess_er_stress", COMPETENCE)

    def test_high_ecm_stiffness_reduces_adhesion_competence(self) -> None:
        self.assert_decreases("adhesion_challenge_high_ecm_stiffness", COMPETENCE)

    # --- Known structural defect -----------------------------------------

    def test_hand2_loss_reduces_epithelial_receptivity(self) -> None:
        """DIRECTION ONLY. Li 2011 (REF-028) reports implantation failure in the
        Hand2 conditional knockout with the stromal progesterone response
        intact; Murata 2019 (REF-062) supplies the human siHAND2 half. The
        MAGNITUDE here is a hard Boolean consequence of a veto that has no
        held-out measurement behind it, so this must never become a magnitude
        assertion."""
        self.assert_decreases(
            "adhesion_challenge_hormone_treated_hand2_loss",
            "OUT_EPITHELIAL_RECEPTIVE",
        )

    def test_hand2_loss_reduces_stable_adhesion(self) -> None:
        self.assert_decreases(
            "adhesion_challenge_hormone_treated_hand2_loss",
            "OUT_STABLE_ADHESION",
        )

    def test_hand2_loss_spares_stromal_decidualization(self) -> None:
        """The dissociation IS the claim. If HAND2 loss also suppressed the
        decidual arm the node would just be another switch on the shared
        progesterone variable, which is precisely the degeneracy this version
        exists to break."""
        reference = [
            row["OUT_STROMAL_DECIDUALIZED"]
            for row in self.results["adhesion_challenge_hormone_treated"]
        ]
        treated = [
            row["OUT_STROMAL_DECIDUALIZED"]
            for row in self.results["adhesion_challenge_hormone_treated_hand2_loss"]
        ]
        for observed, expected in zip(treated, reference, strict=True):
            self.assertAlmostEqual(observed, expected, delta=0.01)

    def test_er_stress_and_ecm_stiffness_are_currently_indistinguishable(
        self,
    ) -> None:
        """Documents a real model defect rather than asserting correct biology.

        IN_ER_STRESS_EXCESS and IN_HIGH_ECM_STIFFNESS occur only inside one
        symmetric disjunction in X_MECHANICAL_PERMISSIVE_ECM's logic and
        nowhere else, so the two challenge conditions are the same executable
        network. This test pins that identity so it cannot change silently; it
        should be inverted into a non-identity requirement once the two inputs
        are given distinct mechanisms.
        """
        for endpoint in (COMPETENCE, STABLE):
            er_stress = [
                row[endpoint]
                for row in self.results["adhesion_challenge_excess_er_stress"]
            ]
            stiffness = [
                row[endpoint]
                for row in self.results["adhesion_challenge_high_ecm_stiffness"]
            ]
            self.assertEqual(
                er_stress,
                stiffness,
                f"{endpoint}: ER stress and ECM stiffness diverged. If this is "
                "intentional, invert this test into a non-identity gate and "
                "update docs/endpoint_convergence_finding.md.",
            )


class ConvergenceHorizonTest(unittest.TestCase):
    """Pins the convergence finding itself, so a regression is visible."""

    def test_declared_duration_does_not_reach_the_fixed_point(self) -> None:
        """At the declared 1.0 duration the endpoint is still in transit.

        This is the defect documented in docs/endpoint_convergence_finding.md.
        When the readout horizon is eventually corrected this test should be
        deleted, not relaxed.
        """
        protocol = get_protocol(
            "adhesion_challenge_hormone_treated", ROOT, model_version=MODEL_VERSION
        )
        self.assertEqual(protocol.steps[0].relative_duration, 1.0)

        converged = _challenge_at_converged_horizon(
            "adhesion_challenge_hormone_treated", seed=1
        )[COMPETENCE]
        self.assertGreater(
            converged,
            0.5,
            "converged adhesion competence should approach the analytic 0.82",
        )


if __name__ == "__main__":
    unittest.main()
