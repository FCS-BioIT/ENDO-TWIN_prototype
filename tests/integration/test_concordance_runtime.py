"""Runtime evidence for the concordance analysis's mifepristone-arm argument.

HISTORY, kept because the reasoning drifted three times and each correction is
instructive. The resolved superset protocol graph HAD a defect. A first revision
of this docstring said the maternal suite "has no mifepristone phase" -- false,
``hormone_treated_mifepristone`` was always declared and executable. A second
blamed `config/protocols.yaml` as a whole, a third blamed the clone layer and
exonerated the YAML; both were too broad and each would have sent a maintainer to
half the cause. The real defect was that the phase was **orphaned**: nothing
declared ``continuation_from: hormone_treated_mifepristone``, so the challenge
was seeded from the unperturbed hormone-treated state and mifepristone switched
on at the same instant as the embryo, while `SOFIA-HT-002` records 10 uM for 24 h
**after** the six-day protocol.

**That defect is REPAIRED, and this module now pins the repair.** The executed
chain is ``basal_maternal -> e2_primed_maternal -> hormone_treated_maternal ->
hormone_treated_mifepristone -> adhesion_challenge_hormone_treated_mifepristone``,
so the recorded phase ORDERING is simulated. The regimen-mismatch explanation for
R43a is withdrawn and must not be reintroduced.

Scope of the repair, pinned by ``TheRepairIsScopedByModelVersion``: it applies
from ``v0.4.0`` onward. The archived ``adoc-core-v0.1.0`` and
``adoc-literature-v0.2.0`` families keep the wiring they were published with, and
so does the archived ``v0.3.0`` superset -- where applying it would not merely
reinterpret an archived model but break a runnable arm, since that family ships
no ``washout.cfg``.

WHAT THESE TESTS ESTABLISH, and at what strength.

* **Asymptotically**, by enumeration rather than sampling: each phase runs to its
  logical fixed point and the network is a DAG over its free variables, so the
  fixed point under a sustained input assignment is unique and independent of the
  state the phase started from.
* **At a finite horizon**, only what was run. That argument does NOT carry:
  the same arm on the same lineage reads a nonzero
  ``OUT_STABLE_ADHESION = 0.000050`` at the declared horizon, so a finite-horizon
  probability here is not identically zero.
  ``test_the_repair_leaves_the_converged_endpoint_unmoved`` compares the repaired
  chain against an explicitly reconstructed pre-repair chain at
  ``CONVERGED_PHASE_HORIZON``, and finds them equal at ``0.0`` across
  ``INVARIANCE_SEEDS``. Bounded to those runs: fixed seeds give reproducibility,
  not Monte Carlo stability, and three seeds characterise nothing.

Note the direction, because it inverted with the repair: the maternal phase is
now IN the lineage, so it is the PRE-REPAIR chain that has to be reconstructed as
a counterfactual, not the repaired one.

R43a's classification rests on horizon instability -- at the declared horizon the
arm has no stable value, its across-seed spread being the size of the value
itself -- never on the size of any near-zero difference. This repository has no
validated characterisation of these estimates' sampling behaviour, so a claim
that such a difference is or is not resolvable would be unfounded.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MODEL_VERSION = "adoc-literature-superset-v0.4.0"
TARGET = "adhesion_challenge_hormone_treated_mifepristone"
TRAJECTORIES = 2000
SEED = 1

#: Seeds for the converged regimen-invariance checks. A single seed shows
#: reproducibility, never Monte Carlo stability -- `AGENTS.md` says so explicitly
#: -- and R43b's retention rests on those checks, so they run across seeds. Three
#: is not a stability characterisation either; it is enough to catch an endpoint
#: that moves with the random stream, and the generated R43b text is bounded to
#: exactly what these runs show rather than claiming invariance in general.
INVARIANCE_SEEDS = (1, 2, 3)


def _run_from(lineage: tuple[str, ...], seed: int = SEED) -> float:
    from dt_adoc.concordance.simulate import CONVERGED_PHASE_HORIZON
    from dt_adoc.simulation.runner import protocol_continuation, run_protocol

    result = None
    continuation = None
    for index, protocol_id in enumerate(lineage):
        result = run_protocol(
            protocol_id,
            model_version=MODEL_VERSION,
            continuation=continuation,
            seed=seed,
            sample_count=TRAJECTORIES,
            phase_horizon=CONVERGED_PHASE_HORIZON,
        )
        if index + 1 < len(lineage):
            continuation = protocol_continuation(
                lineage[index + 1], result, model_version=MODEL_VERSION
            )
    assert result is not None
    return float(result.final_result.last["OUT_STABLE_ADHESION"])


def _run_counterfactual_with_maternal_mifepristone() -> float:
    """The phase ORDERING the evidence records, built at run time.

    `SOFIA-HT-002`: 10 uM mifepristone for 24 h **after** the six-day hormone
    protocol, before the adhesion assay. This builds a phase in that position by
    re-running the hormone-treated maternal condition with ``IN_MIFEPRISTONE``
    forced on, then continuing into the embryo challenge. It reproduces the
    ordering and the perturbation, NOT the 24 h regimen: the phase runs at
    ``CONVERGED_PHASE_HORIZON``, dimensionless MaBoSS relative time that
    `simulate.py` calls "never a day count".

    Kept alongside `test_the_orphaned_maternal_phase_gives_the_same_converged_value`,
    which runs the *committed* ``hormone_treated_mifepristone`` protocol instead
    of synthesising an equivalent. The two reach the same endpoint by different
    routes, so neither rests on the other being built correctly.

    Nothing is written: the committed protocol suite is untouched, and this exists
    only to run the counterfactual the concordance analysis's argument depends on.
    Asserting that argument while never executing the arm it is about would be
    citing a test for something the test does not exercise.
    """
    from dt_adoc.concordance.simulate import CONVERGED_PHASE_HORIZON
    from dt_adoc.protocols.conditions import get_protocol
    from dt_adoc.simulation.runner import (
        _input_override_text,
        _timing_override_text,
        build_continuation,
        protocol_continuation,
        run_cmaboss_condition,
        run_protocol,
    )

    maternal = "hormone_treated_maternal"
    result = None
    continuation = None
    for index, protocol_id in enumerate(
        ("basal_maternal", "e2_primed_maternal", maternal)
    ):
        result = run_protocol(
            protocol_id,
            model_version=MODEL_VERSION,
            continuation=continuation,
            seed=SEED,
            sample_count=TRAJECTORIES,
            phase_horizon=CONVERGED_PHASE_HORIZON,
        )
        if index < 2:
            nxt = ("e2_primed_maternal", maternal)[index]
            continuation = protocol_continuation(
                nxt, result, model_version=MODEL_VERSION
            )
    assert result is not None

    # The bypassed phase: the maternal condition again, with mifepristone on.
    maternal_protocol = get_protocol(maternal, None, model_version=MODEL_VERSION)
    step = maternal_protocol.steps[-1]
    inputs = dict(step.input_states)
    inputs["IN_MIFEPRISTONE"] = True
    mifepristone_phase = run_cmaboss_condition(
        model_version=MODEL_VERSION,
        condition_cfg=ROOT / maternal_protocol.condition_cfg,
        override_texts=[
            _input_override_text(inputs),
            _timing_override_text(relative_duration=CONVERGED_PHASE_HORIZON),
        ],
        continuation=build_continuation(
            previous_condition=result.final_result,
            target_protocol_id=maternal,
            model_version=MODEL_VERSION,
            forced_nodes=inputs,
            source_protocol=maternal,
        ),
        seed=SEED,
        sample_count=TRAJECTORIES,
    )

    challenge = get_protocol(TARGET, None, model_version=MODEL_VERSION)
    final = run_protocol(
        TARGET,
        model_version=MODEL_VERSION,
        continuation=build_continuation(
            previous_condition=mifepristone_phase,
            target_protocol_id=TARGET,
            model_version=MODEL_VERSION,
            forced_nodes=challenge.steps[0].input_states,
            source_protocol=maternal,
        ),
        seed=SEED,
        sample_count=TRAJECTORIES,
        phase_horizon=CONVERGED_PHASE_HORIZON,
    )
    return float(final.final_result.last["OUT_STABLE_ADHESION"])


class ConvergedMifepristoneWasUnmovedByLineage(unittest.TestCase):
    """R43b's comparison was unmoved by the missing mifepristone phase.

    Deliberately not "cannot be changed". What is proved is asymptotic: the
    network is a DAG and the fixed point under sustained ``IN_MIFEPRISTONE`` is
    0 from any starting state. These are FINITE-horizon runs, where that does
    not imply an exact 0 -- the same arm records 0.000050 at the declared
    horizon -- so what the checks below establish is that the converged value
    did not move across the lineages and seeds actually run.
    """

    def test_the_converged_endpoint_was_unmoved_across_the_lineages_run(
        self,
    ) -> None:
        """Three different histories, one converged value in each run performed.

        Named and stated for what it is. An earlier revision named this method
        for lineage-independence as a property, and opened "Three different
        histories, one converged value" -- both of which assert the finite-horizon
        absolute this analysis does not have. ``_run_from`` pins the finite
        ``CONVERGED_PHASE_HORIZON``, so three histories agreeing is evidence
        about those three, not a demonstration that no history could differ.

        If this ever stops holding, the concordance analysis's reason for
        retaining R43b while discarding R43a is void and both rows must be
        reclassified -- which is why it is asserted rather than asserted about.
        """
        from dt_adoc.concordance.simulate import protocol_lineage

        declared = protocol_lineage(TARGET, model_version=MODEL_VERSION)
        values = {
            "declared lineage": _run_from(declared),
            "target alone": _run_from((TARGET,)),
            "basal then target": _run_from(("basal_maternal", TARGET)),
        }
        self.assertEqual(
            set(values.values()),
            {0.0},
            f"converged mifepristone endpoint varies with lineage: {values}",
        )

    def test_the_recorded_phase_ordering_gives_the_same_converged_value(
        self,
    ) -> None:
        """The counterfactual itself, not an argument about it.

        Applies mifepristone to maternal tissue for a phase BEFORE the embryo
        challenge -- the phase ORDERING `SOFIA-HT-002` records -- and checks the
        converged endpoint is unchanged. This is what licenses retaining R43b
        while discarding R43a; without it the licence would rest on the
        fixed-point argument alone.

        What it reproduces is that ORDERING and the perturbation, **not the
        experimental regimen**, and an earlier revision of this docstring
        overstated it. The inserted phase runs at `CONVERGED_PHASE_HORIZON`,
        which `simulate.py` defines as dimensionless MaBoSS relative time and
        expressly "never a day count", so nothing here represents 24 h and this
        model carries no mapping from simulated to physical time.

        Nor does `config/protocols.yaml` simply *omit* that ordering, as the same
        revision said. It declares this challenge TWICE and disagrees with
        itself, and the executed superset family inherits the row that bypasses
        the maternal phase -- see
        `test_the_bypassing_wiring_is_inherited_not_synthesised`, which pins that
        rather than arguing it.
        """
        from dt_adoc.concordance.simulate import protocol_lineage

        declared = _run_from(protocol_lineage(TARGET, model_version=MODEL_VERSION))
        recorded_ordering = _run_counterfactual_with_maternal_mifepristone()
        self.assertEqual(
            declared,
            recorded_ordering,
            "the converged mifepristone endpoint changes under the recorded "
            "phase ordering, so R43b cannot be retained as a comparison",
        )

    def test_the_declared_horizon_reads_far_from_the_fixed_point(self) -> None:
        """Why R43a is not assessable -- stated as what can actually be shown.

        An earlier revision asserted that the declared horizon is *demonstrably*
        lineage-sensitive on one-trajectory grounds, and later revisions asserted
        the opposite -- that the chained-versus-unchained difference was too small
        to matter -- once via a binomial standard error and once via a
        1/trajectory_count resolution limit. All three are withdrawn.

        A fourth revision committed a probe that measured that difference and
        drew a mechanism from the continuation support and mass it recorded; that
        too is withdrawn, because the recorded mass was `1.0` by construction and
        support cardinality cannot establish that a distribution is mixed. No
        committed check measures the difference, and this repository has no
        validated characterisation of these estimates' sampling behaviour, so no
        claim about it is made in either direction. This test deliberately does
        not measure it.

        What this test checks, and what the classification actually rests on, is
        that the declared horizon reads the endpoint far from its fixed point:
        for the unperturbed arm it gives 0.000 where the converged value is
        ~0.82. A pre-convergence readout is a transient rather than a converged value,
        and the bypassed maternal mifepristone phase is what would set the state
        such a transient is read from -- but whether the transient's VALUE
        actually depends on that starting state is exactly the claim this
        repository records as WITHDRAWN and not demonstrated, and nothing here
        reinstates it. The converged endpoint, separately, was unmoved by that
        phase in every run above. That is why the
        converged row survives the regimen mismatch and the declared one does
        not: the asymmetry is in the evidence, not in a proof -- the fixed-point
        argument is asymptotic, and what separates the rows is that the
        converged comparison was actually run and held, while the declared one
        has no such demonstration.
        """
        from dt_adoc.concordance.simulate import (
            CONVERGED_PHASE_HORIZON,
            protocol_lineage,
        )
        from dt_adoc.simulation.runner import protocol_continuation, run_protocol

        unperturbed = "adhesion_challenge_hormone_treated"

        def endpoint(horizon: float | None) -> float:
            result = None
            continuation = None
            lineage = protocol_lineage(unperturbed, model_version=MODEL_VERSION)
            for index, protocol_id in enumerate(lineage):
                result = run_protocol(
                    protocol_id,
                    model_version=MODEL_VERSION,
                    continuation=continuation,
                    seed=SEED,
                    sample_count=TRAJECTORIES,
                    phase_horizon=horizon,
                )
                if index + 1 < len(lineage):
                    continuation = protocol_continuation(
                        lineage[index + 1], result, model_version=MODEL_VERSION
                    )
            assert result is not None
            return float(result.final_result.last["OUT_STABLE_ADHESION"])

        declared = endpoint(None)
        converged = endpoint(CONVERGED_PHASE_HORIZON)
        # Not an exact zero, which is the point -- the declared readout is a
        # transient, not a converged value. Deliberately NOT described as some
        # number of trajectories: this repository has no validated
        # characterisation of these estimates' sampling behaviour, and a count
        # reading is the interpretation `simulate.py` and the R43a note record as
        # unestablished. Asserted as orders of magnitude apart rather than as an
        # equality, so the test says what it means.
        self.assertLess(declared, 0.01)
        self.assertGreater(converged, 0.5)
        self.assertGreater(converged / max(declared, 1e-9), 100.0)


class MifepristoneArmLineageIsPinned(unittest.TestCase):
    """What is actually executed for the mifepristone arm, asserted not narrated.

    Every claim the concordance analysis makes about the mifepristone regimen
    rests on one fact -- which protocols run, in which order -- so that fact is
    pinned here rather than described in prose.

    History. This class was written to pin a DEFECT: the executed chain bypassed
    the maternal mifepristone phase, seeding the embryo challenge from the
    unperturbed hormone-treated state, so mifepristone switched on at the same
    instant as the embryo. `SOFIA-HT-002` records the opposite -- 10 uM
    mifepristone for 24 h AFTER the six-day protocol and BEFORE the adhesion
    assay. The defect is now repaired and this class pins the repair, keeping
    the regression guards that made the original diagnosis checkable.
    """

    def test_the_executed_chain_runs_the_maternal_mifepristone_phase(self) -> None:
        """The exact chain, and the state the challenge is seeded from."""
        from dt_adoc.concordance.build import (
            ARMS,
            MATERNAL_MIFEPRISTONE_PROTOCOL,
        )
        from dt_adoc.concordance.build import (
            MODEL_VERSION as BUILD_MODEL_VERSION,
        )
        from dt_adoc.concordance.simulate import protocol_lineage

        self.assertEqual(BUILD_MODEL_VERSION, MODEL_VERSION)
        self.assertEqual(ARMS["mifepristone"], TARGET)
        lineage = protocol_lineage(TARGET, model_version=MODEL_VERSION)
        self.assertEqual(
            lineage,
            (
                "basal_maternal",
                "e2_primed_maternal",
                "hormone_treated_maternal",
                MATERNAL_MIFEPRISTONE_PROTOCOL,
                TARGET,
            ),
        )
        # The phase immediately before the challenge supplies its initial joint
        # distribution. It must be the maternal mifepristone phase, so the drug
        # has acted on maternal tissue before any embryo is present.
        self.assertEqual(lineage[-2], MATERNAL_MIFEPRISTONE_PROTOCOL)
        self.assertNotEqual(
            lineage[-2],
            "hormone_treated_maternal",
            "the challenge is seeded from the unperturbed hormone-treated state "
            "again, which is the bypass this repair removed",
        )

    def test_the_maternal_mifepristone_phase_exists_and_is_consumed(self) -> None:
        """Present, executable, and now actually continued from."""
        from dt_adoc.concordance.build import MATERNAL_MIFEPRISTONE_PROTOCOL
        from dt_adoc.protocols.conditions import protocol_definitions

        definitions = protocol_definitions(model_version=MODEL_VERSION)
        self.assertIn(MATERNAL_MIFEPRISTONE_PROTOCOL, definitions)
        maternal = definitions[MATERNAL_MIFEPRISTONE_PROTOCOL]

        # It is a genuine maternal phase: mifepristone on, no embryo.
        inputs: dict[str, bool] = {}
        for step in maternal.steps:
            inputs.update(step.input_states)
        self.assertTrue(inputs["IN_MIFEPRISTONE"])
        self.assertFalse(inputs["IN_EMBRYO_PRESENT"])
        self.assertFalse(inputs.get("IN_EMBRYO_CONTACT", False))

        # And it is runnable: it sits on the maternal lineage and its cfg exists.
        self.assertEqual(maternal.continuation_from, "hormone_treated_maternal")
        self.assertTrue(
            (ROOT / maternal.condition_cfg).is_file(),
            f"{maternal.condition_cfg} is missing, so the phase is not executable",
        )

        # No longer orphaned: its own challenge continues from it.
        continuing = sorted(
            protocol_id
            for protocol_id, definition in definitions.items()
            if definition.continuation_from == MATERNAL_MIFEPRISTONE_PROTOCOL
        )
        self.assertEqual(continuing, [TARGET])

    def test_the_repair_is_scoped_to_the_superset_and_archives_are_untouched(
        self,
    ) -> None:
        """Where the repair lives, pinned so its scope cannot drift.

        The archived `adoc-core-v0.1.0` and `adoc-literature-v0.2.0` rows in
        `config/protocols.yaml` are deliberately NOT edited: changing them would
        silently alter what a published model version simulates. Core already
        chained the challenge onto the maternal phase; v0.2.0 did not, and the
        superset used to inherit v0.2.0's value wholesale. The repair lives in
        the superset clone layer, which now overrides that inherited value.

        So the superset must agree with CORE here and differ from v0.2.0 -- the
        exact inverse of the pre-repair assertion, and checked mechanically
        rather than asserted, because two earlier revisions named the wrong
        culprit for the original defect.
        """
        from dt_adoc.concordance.build import MATERNAL_MIFEPRISTONE_PROTOCOL
        from dt_adoc.model.catalog import load_protocols
        from dt_adoc.protocols.conditions import protocol_definitions

        rows = {
            row["model_version"]: row
            for row in load_protocols(ROOT)["protocols"]
            if row["protocol_id"] == TARGET
        }
        self.assertEqual(
            rows["adoc-core-v0.1.0"]["continuation_from"],
            MATERNAL_MIFEPRISTONE_PROTOCOL,
            "the archived core row changed; archives must not be edited",
        )
        self.assertEqual(
            rows["adoc-literature-v0.2.0"]["continuation_from"],
            "hormone_treated_maternal",
            "the archived v0.2.0 row changed; archives must not be edited",
        )

        # The resolved superset now overrides the inherited v0.2.0 value and
        # lands on core's, which is the one the recorded regimen supports.
        resolved = protocol_definitions(model_version=MODEL_VERSION)[TARGET]
        self.assertEqual(
            resolved.continuation_from,
            rows["adoc-core-v0.1.0"]["continuation_from"],
        )
        self.assertNotEqual(
            resolved.continuation_from,
            rows["adoc-literature-v0.2.0"]["continuation_from"],
        )

    def test_the_repair_leaves_the_converged_endpoint_unmoved(self) -> None:
        """What the repair did NOT change, measured rather than predicted.

        R43b is read at the converged horizon and is the only genuinely held-out
        comparison in the matrix, so whether the rewiring moves it decides
        whether R43b survives the repair. It is measured here against the
        pre-repair chain, constructed explicitly, rather than assumed from the
        DAG argument.

        This is bounded to these runs: fixed seeds give reproducibility, not
        Monte Carlo stability, and three seeds is not a stability
        characterisation. It is enough to catch an endpoint that moves with the
        random stream.
        """
        from dt_adoc.concordance.simulate import protocol_lineage

        repaired = protocol_lineage(TARGET, model_version=MODEL_VERSION)
        # The chain as it ran before the repair: the maternal phase removed, so
        # the challenge is seeded from hormone_treated_maternal.
        legacy = tuple(p for p in repaired if p != "hormone_treated_mifepristone")
        self.assertEqual(
            legacy,
            (
                "basal_maternal",
                "e2_primed_maternal",
                "hormone_treated_maternal",
                TARGET,
            ),
        )
        for seed in INVARIANCE_SEEDS:
            with self.subTest(seed=seed):
                before = _run_from(legacy, seed)
                after = _run_from(repaired, seed)
                self.assertEqual(
                    before,
                    after,
                    "the converged mifepristone endpoint moved with the repair, "
                    "so R43b's retention must be re-derived rather than carried "
                    "over from the pre-repair evidence",
                )
                # The VALUE, not just the equality. Several surfaces cite this
                # test for "0.0 in every run performed". Asserting equality
                # alone would leave that citation true of seed 1 only.
                self.assertEqual(
                    after,
                    0.0,
                    "the repaired converged endpoint is not 0.0 at this seed, so "
                    "the R43b surfaces citing this test overstate it",
                )


class AllMaternalPerturbationWiringIsPinned(unittest.TestCase):
    """The whole maternal-perturbation wiring table, now asserting the REPAIR.

    History, kept because both errors are instructive. Three shipped texts once
    said `hormone_treated_anti_spp1` was "orphaned the same way" as the
    mifepristone phase. It was not: `washout` continued from it. That claim was
    written from the mifepristone case and generalised without being checked.
    This class was then written to pin the defect so it could not drift, and it
    distinguished two things the loose wording had merged -- being ORPHANED
    (nothing continues from this phase) and being BYPASSED (the matching
    adhesion challenge is seeded from `hormone_treated_maternal` instead of from
    this phase).

    The defect is now REPAIRED, and this class pins the repair. It keeps the
    orphaned/bypassed distinction, because the distinction is what made the
    original diagnosis checkable, and asserting only "nothing is orphaned" would
    let a future edit reintroduce a bypass while every phase still had a
    consumer. Both properties are therefore asserted separately, per arm.

    What the repair does NOT establish is any claim about the numbers. Each
    phase runs to a unique fixed point because the network is a DAG over its
    free variables, so at a converged horizon several of these arms are expected
    to be unchanged by the rewiring. The repair makes the executed regimen match
    the recorded one; it is not evidence that any value moved.
    """

    #: phase -> (orphaned, condition cfg exists). Every maternal perturbation
    #: phase must now have a consumer and be runnable.
    EXPECTED_MATERNAL_WIRING: ClassVar[dict[str, tuple[bool, bool]]] = {
        "hormone_treated_mifepristone": (False, True),
        "hormone_treated_anti_spp1": (False, True),
        "hormone_treated_hand2_loss": (False, True),
        # Was orphaned AND unrunnable: it resolved, but the superset generator
        # emitted no washout.cfg. It is now emitted and consumed.
        "washout": (False, True),
    }

    def test_which_maternal_phases_are_orphaned_and_which_are_runnable(self) -> None:
        from dt_adoc.protocols.conditions import protocol_definitions

        definitions = protocol_definitions(model_version=MODEL_VERSION)
        continued_from = {
            definition.continuation_from
            for definition in definitions.values()
            if definition.continuation_from
        }
        actual = {
            phase: (
                phase not in continued_from,
                (ROOT / definitions[phase].condition_cfg).is_file(),
            )
            for phase in self.EXPECTED_MATERNAL_WIRING
            if phase in definitions
        }
        self.assertEqual(actual, self.EXPECTED_MATERNAL_WIRING)

    def test_anti_spp1_is_continued_from_and_so_is_not_orphaned(self) -> None:
        """The specific claim that was once wrong, asserted on its own.

        It now has two consumers rather than one: `washout` continued from it
        before the repair, and its own adhesion challenge does too.
        """
        from dt_adoc.protocols.conditions import protocol_definitions

        definitions = protocol_definitions(model_version=MODEL_VERSION)
        continuing = sorted(
            protocol_id
            for protocol_id, definition in definitions.items()
            if definition.continuation_from == "hormone_treated_anti_spp1"
        )
        self.assertEqual(
            continuing,
            ["adhesion_challenge_hormone_treated_anti_spp1", "washout"],
        )

    def test_each_named_perturbation_challenge_is_seeded_from_its_own_phase(
        self,
    ) -> None:
        """The repaired property, and the regression guard against the bypass.

        Each challenge must be seeded from the perturbation phase whose name it
        carries, so that the perturbation acts on maternal tissue BEFORE the
        embryo is introduced -- which is the regimen `SOFIA-HT-002` records.
        Being seeded from `hormone_treated_maternal` is asserted against
        explicitly, because that is the exact state this repair moved away from
        and a re-clone from the archived parents would silently restore it.

        Scope is exactly the challenges of the form
        ``adhesion_challenge_hormone_treated_<phase>``. ``washout`` is NOT one
        of them and is covered separately below.
        """
        from dt_adoc.protocols.conditions import protocol_definitions

        definitions = protocol_definitions(model_version=MODEL_VERSION)
        named = sorted(
            protocol_id
            for protocol_id in definitions
            if protocol_id.startswith("adhesion_challenge_hormone_treated_")
        )
        self.assertEqual(
            named,
            [
                "adhesion_challenge_hormone_treated_anti_spp1",
                "adhesion_challenge_hormone_treated_hand2_loss",
                "adhesion_challenge_hormone_treated_mifepristone",
            ],
            "the set of named perturbation challenges changed, so this class's "
            "scope statement and the tables that cite it must be re-derived",
        )
        for challenge in named:
            maternal = challenge.replace("adhesion_challenge_", "", 1)
            with self.subTest(arm=challenge):
                self.assertIn(maternal, definitions)
                self.assertEqual(definitions[challenge].continuation_from, maternal)
                self.assertNotEqual(
                    definitions[challenge].continuation_from,
                    "hormone_treated_maternal",
                )

    def test_the_unperturbed_comparator_still_continues_from_the_shared_state(
        self,
    ) -> None:
        """The arm that must NOT be rewired.

        `adhesion_challenge_hormone_treated` is the unperturbed comparator, and
        `hormone_treated_maternal` is genuinely its parent. A repair that
        rewired every challenge uniformly would have broken the comparator the
        other arms are read against.
        """
        from dt_adoc.protocols.conditions import protocol_definitions

        definitions = protocol_definitions(model_version=MODEL_VERSION)
        self.assertEqual(
            definitions["adhesion_challenge_hormone_treated"].continuation_from,
            "hormone_treated_maternal",
        )

    def test_washout_is_now_runnable_and_seeds_its_own_challenge(self) -> None:
        """Washout had a different defect, and it had two parts.

        Before the repair `adhesion_challenge_washout` continued from the
        anti-SPP1 *challenge* -- a challenge seeded from a challenge, so the
        embryo was already present when the washout was applied -- and `washout`
        itself had no emitted condition .cfg, which made it unrunnable rather
        than merely unused. Both are asserted here.
        """
        from dt_adoc.protocols.conditions import protocol_definitions

        definitions = protocol_definitions(model_version=MODEL_VERSION)
        self.assertNotIn("adhesion_challenge_hormone_treated_washout", definitions)
        self.assertEqual(
            definitions["adhesion_challenge_washout"].continuation_from,
            "washout",
        )
        self.assertTrue((ROOT / definitions["washout"].condition_cfg).is_file())

    def test_no_embryo_challenge_is_seeded_from_another_embryo_challenge(
        self,
    ) -> None:
        """The general form of the washout defect, asserted across the suite.

        A challenge seeded from another challenge means the perturbation is
        applied to tissue that is already in contact with an embryo, which no
        arm in this study records. `adhesion_challenge_washout` was the only
        instance; this asserts none is reintroduced anywhere.
        """
        from dt_adoc.protocols.conditions import protocol_definitions

        definitions = protocol_definitions(model_version=MODEL_VERSION)
        offenders = sorted(
            protocol_id
            for protocol_id, definition in definitions.items()
            if definition.protocol_class == "embryo_challenge"
            and definition.continuation_from is not None
            and definitions[definition.continuation_from].protocol_class
            == "embryo_challenge"
        )
        self.assertEqual(offenders, [])


class TheRepairIsScopedByModelVersion(unittest.TestCase):
    """Which model versions receive the maternal-perturbation wiring repair.

    The superset clone layer serves EVERY `adoc-literature-superset-v*` so that
    archived supersets stay resolvable. That makes the repair's scope a decision
    rather than an accident, and getting it wrong is silent: applying it to an
    archived family changes what a published model version simulates, and for
    `v0.3.0` it would be an outright regression, because that family ships no
    `washout.cfg` and the rewired `adhesion_challenge_washout` would fail on a
    missing file.

    The floor is a comparison rather than an equality so that v0.5.0 and later
    inherit the repair instead of silently reverting to the bypass.
    """

    def test_the_archived_v030_superset_keeps_its_published_wiring(self) -> None:
        from dt_adoc.protocols.conditions import protocol_definitions

        definitions = protocol_definitions(
            model_version="adoc-literature-superset-v0.3.0"
        )
        self.assertEqual(
            definitions[
                "adhesion_challenge_hormone_treated_mifepristone"
            ].continuation_from,
            "hormone_treated_maternal",
        )
        self.assertEqual(
            definitions["adhesion_challenge_washout"].continuation_from,
            "adhesion_challenge_hormone_treated_anti_spp1",
        )

    def test_applying_the_repair_to_v030_would_break_a_runnable_arm(self) -> None:
        """The concrete harm, asserted rather than asserted-about.

        `washout` has no condition file in the archived family, so a rewired
        `adhesion_challenge_washout` would resolve onto an unrunnable parent.
        """
        from dt_adoc.protocols.conditions import protocol_definitions

        definitions = protocol_definitions(
            model_version="adoc-literature-superset-v0.3.0"
        )
        self.assertFalse(
            (ROOT / definitions["washout"].condition_cfg).is_file(),
            "v0.3.0 now ships a washout.cfg, so the regression this floor "
            "avoids no longer exists and the scope decision can be revisited",
        )

    def test_the_floor_admits_future_versions(self) -> None:
        from dt_adoc.protocols.conditions import (
            REPAIRED_FROM_SUPERSET_VERSION,
            _superset_version,
        )

        self.assertLess(
            _superset_version("adoc-literature-superset-v0.3.0"),
            REPAIRED_FROM_SUPERSET_VERSION,
        )
        for future in (
            "adoc-literature-superset-v0.4.0",
            "adoc-literature-superset-v0.5.0",
        ):
            with self.subTest(model_version=future):
                self.assertGreaterEqual(
                    _superset_version(future), REPAIRED_FROM_SUPERSET_VERSION
                )


class RegeneratedSourceDataRenders(unittest.TestCase):
    """The figure source data must stay renderable by the figure that reads it.

    `write_figure_source_data` packs panel C's evidence class and box kind into
    one `unit` column as ``"<cls>; box_kind=<kind>"``, and `_panel_c` splits them
    back apart before the class reaches `NODE_FACE`. Nothing but a render
    exercises that split, so a regression to using the packed string as the
    class raises `KeyError` only when someone redraws the figure -- after
    `build-concordance` has already reported success. These tests render the
    tracked source data end to end so that failure surfaces in the suite.
    """

    def test_every_panel_c_class_resolves_in_the_palette(self) -> None:
        """The precise regression: the packed `unit` value is not a palette key."""
        from dt_adoc.concordance.build import FIGURE_SOURCE_DATA
        from dt_adoc.concordance.render import NODE_FACE, _panel_c, _read_source_data

        records = _read_source_data(ROOT / FIGURE_SOURCE_DATA)
        panel_c = [
            row
            for row in records
            if row["panel"] == "C" and row["quantity"] == "mechanism_node"
        ]
        self.assertTrue(panel_c, "tracked source data has no panel C mechanism nodes")
        for row in panel_c:
            packed = row["unit"]
            self.assertIn("box_kind=", packed)
            # The whole packed value must NOT be a key, and the split half must.
            self.assertNotIn(packed, NODE_FACE)
            self.assertIn(packed.split(";")[0].strip(), NODE_FACE)
        del _panel_c  # imported to assert it exists at its documented name

    def test_regenerated_source_data_renders_to_completion(self) -> None:
        """The round trip that matters: writer -> file -> parser -> render.

        `write_figure_source_data` is what packs the `unit` column, so reading
        only the tracked file would leave the writer's format and the parser's
        split free to drift apart. This regenerates panel C through the real
        writer and renders the result, so the two must agree.

        No simulation runs: panel C's boxes come from `PANEL_C_NODES`, and the
        writer reaches `runs` only through `runs.get(...)`, which returns None
        for an empty mapping and skips the simulated panel-A rows. `facts` is
        touched only for `model_version`. So the mechanism under test is
        exercised in full without a MaBoSS execution.
        """
        import tempfile
        from types import SimpleNamespace

        import matplotlib

        matplotlib.use("Agg")

        from dt_adoc.concordance.figure import write_figure_source_data
        from dt_adoc.concordance.render import (
            NODE_FACE,
            PANEL_C_NODES,
            _read_source_data,
            render,
        )
        from dt_adoc.concordance.table import build_rows_from_table

        rows = build_rows_from_table(ROOT)

        with tempfile.TemporaryDirectory() as tmp:
            regenerated = Path(tmp) / "figure_source_data.tsv"
            write_figure_source_data(
                rows=rows,
                runs={},
                facts=SimpleNamespace(model_version="adoc-literature-superset-v0.4.0"),
                destination=regenerated,
            )

            # The writer's own output must parse to palette keys.
            panel_c = [
                row
                for row in _read_source_data(regenerated)
                if row["panel"] == "C" and row["quantity"] == "mechanism_node"
            ]
            self.assertEqual(len(panel_c), len(PANEL_C_NODES))
            for row in panel_c:
                self.assertIn(row["unit"].split(";")[0].strip(), NODE_FACE)

            destination = Path(tmp) / "regenerated.png"
            written = render(
                source_data=regenerated,
                destination=destination,
                provenance={
                    "model_version": "adoc-literature-superset-v0.4.0",
                    "trajectory_count": 20000,
                    "seeds": [1, 2, 3],
                },
                rows=rows,
            )
            self.assertTrue(written.exists())
            self.assertGreater(written.stat().st_size, 0)

    def test_the_tracked_source_data_renders_to_completion(self) -> None:
        """A full render of the committed source data, to a scratch destination.

        Writes nowhere near `docs/assets`: the committed figure is a build
        artifact and a test must not overwrite it.
        """
        import json
        import tempfile

        import matplotlib

        matplotlib.use("Agg")

        from dt_adoc.concordance.build import FIGURE_SOURCE_DATA, RUN_SETTINGS
        from dt_adoc.concordance.render import render
        from dt_adoc.concordance.table import build_rows_from_table

        provenance = json.loads((ROOT / RUN_SETTINGS).read_text(encoding="utf-8"))[
            "provenance"
        ]

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "concordance_test.png"
            written = render(
                source_data=ROOT / FIGURE_SOURCE_DATA,
                destination=destination,
                provenance=provenance,
                rows=build_rows_from_table(ROOT),
            )
            self.assertTrue(written.exists())
            self.assertGreater(written.stat().st_size, 0)
            sidecar = destination.with_name(destination.stem + "_metadata.json")
            self.assertTrue(sidecar.exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
