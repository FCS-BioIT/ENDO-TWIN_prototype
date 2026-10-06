"""Exact identifiability claims the collaborator figure is allowed to assert.

Every number is derived by exhaustive enumeration over the model's free
variables under the arms the repository records observations for, so these are
statements about the model and the design rather than estimates. Unit tests: no
MaBoSS, no simulation, no horizon, no seed.

The tests that matter most are the ones asserting the *derivation*, not the
totals. A total can be reproduced by a broken pipeline that happens to land on
the right number; the design split, the overlay semantics and the measurement
extension each had a defect during development that left the headline counts
looking plausible.
"""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting.identifiability import (
    adhesion_endpoint_decomposition,
    candidate_arms,
    compute_gain,
    identifiability_summary,
    load_identifiability,
)

SUPERSET = "adoc-literature-superset-v0.4.0"


class IdentifiabilityFactsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_identifiability(SUPERSET)
        cls.summary = identifiability_summary(cls.facts)

    def test_only_arms_with_a_recorded_observation_count(self) -> None:
        """An arm earns its place by carrying data, never by having a cfg.

        The superset ships conditions for anti-SPP1, washout, HAND2 loss, ER
        stress and high stiffness. None of them was run: counting them would
        credit the design with excitation it never applied, and would make the
        identifiability problem look solved.
        """
        arm_ids = {arm.arm_id for arm in self.facts.arms}
        self.assertEqual(
            arm_ids,
            {
                "basal_maternal",
                "e2_primed_maternal",
                "hormone_treated_maternal",
                "adhesion_challenge_basal",
                "adhesion_challenge_hormone_treated",
                "adhesion_challenge_hormone_treated_mifepristone",
            },
        )
        for arm in self.facts.arms:
            self.assertTrue(arm.measured, f"{arm.arm_id} carries no observation")

    def test_condition_cfgs_are_overlays_on_baseline(self) -> None:
        """basal_maternal.cfg sets nothing, and still assigns every input OFF.

        Reading a condition cfg alone leaves unmentioned inputs looking
        unassigned; reading baseline.cfg wholesale pins all 59 nodes to their
        initial states and flattens the network to constant zero. Both were
        real defects during development.
        """
        basal = next(a for a in self.facts.arms if a.arm_id == "basal_maternal")
        self.assertEqual(basal.on, ())
        self.assertIn("IN_E2", basal.inputs)
        self.assertFalse(basal.inputs["IN_E2"])
        # Derived nodes must never appear as arm inputs.
        self.assertNotIn("E_PAEP", basal.inputs)
        self.assertNotIn("OUT_STABLE_ADHESION", basal.inputs)

    def test_free_variable_split(self) -> None:
        """Latent means unknown, not merely absent.

        A declared intervention no arm applies is *known* to be off. An internal
        free variable no arm assigns is a property of the biological material and
        is genuinely unknown, whatever initial probability baseline.cfg gives it.
        """
        self.assertEqual(
            set(self.facts.latent),
            {
                "E_KLF12_HIGH",
                "X_MECHANICAL_STRESS_RELAY",
                "X_INTERFACE_SPP1_RELAY",
                "X_INTERFACE_REDUNDANT_RELAY",
                "X_INTERFACE_ANTIADHESIVE_RELAY",
            },
        )
        self.assertEqual(self.facts.latent_states, 32)
        for node_id in self.facts.latent:
            self.assertFalse(node_id.startswith("IN_"))

    def test_two_nested_collapses_are_reported_separately(self) -> None:
        """59 labels -> 35 functions -> 19 separable states, for two reasons.

        The first collapse is caused by the rules and no experiment can undo it;
        the second is caused by bundled dosing and an experiment can. Merging
        them into one number would blame the wrong thing.
        """
        self.assertEqual(self.summary["named_nodes"], 59)
        self.assertEqual(self.summary["global_effective_states"], 35)
        self.assertEqual(self.summary["design_effective_states"], 19)
        self.assertEqual(self.summary["states_lost_to_rule_encoding"], 24)
        self.assertEqual(self.summary["states_lost_to_design_bundling"], 16)

    def test_the_two_molecular_readouts_share_one_design_state(self) -> None:
        """PAEP and IGFBP-1 are one bit under the arms as they are run.

        This is the figure's central claim, so it is pinned rather than left to
        a total. The cocktail moves E2 with the progestin and cAMP, so the
        epithelial secretory program and the stromal decidual program never move
        independently and no measurement can separate them.
        """
        design_of = {n: c for c in self.facts.design_classes for n in c}
        self.assertEqual(design_of["E_PAEP"], design_of["S_IGFBP1"])
        self.assertEqual(len(design_of["E_PAEP"]), 23)
        self.assertIn("S_PRL", design_of["E_PAEP"])
        self.assertIn("OUT_STROMAL_DECIDUALIZED", design_of["E_PAEP"])

    def test_whole_experiment_yields_two_observation_classes(self) -> None:
        """Every measurement in every arm splits 32 internal states into 2."""
        self.assertEqual(len(self.facts.fibers), 2)
        self.assertEqual(sum(len(members) for _key, members in self.facts.fibers), 32)
        self.assertEqual(
            set(self.facts.measured_nodes),
            {"E_PAEP", "S_IGFBP1", "OUT_STABLE_ADHESION"},
        )

    def test_perturbation_split(self) -> None:
        """One input is effect-attributable; one is set alone but unreadable.

        This test previously asserted `{IN_E2, IN_MIFEPRISTONE}`, transcribing a
        classification rule that was itself wrong: it counted an input as
        attributable on the strength of an isolated contrast alone, without
        requiring the two arms to share a measured outcome. `IN_E2`'s only
        single-input pair reads `S_IGFBP1` against `E_PAEP`, so no change is
        attributable to it. The expectation moved because the SPECIFICATION was
        corrected, not to make a failing check pass -- see
        `EffectAttributionNeedsASharedOutcome`, which re-derives the invariant
        from the arms rather than restating this constant.
        """
        self.assertEqual(set(self.facts.independently_perturbed), {"IN_MIFEPRISTONE"})
        self.assertEqual(set(self.facts.set_alone_no_shared_readout), {"IN_E2"})
        self.assertEqual(
            self.facts.bundled_perturbed["IN_XAV939"],
            ("IN_PROGESTIN", "IN_XAV939", "IN_cAMP"),
        )
        self.assertEqual(
            self.facts.bundled_perturbed["IN_EMBRYO_CONTACT"],
            ("IN_EMBRYO_CONTACT", "IN_EMBRYO_PRESENT", "IN_TROPHECTODERM_COMPETENT"),
        )

    def test_relays_are_not_assayable(self) -> None:
        """The dictionary declares them placeholders; the search must honour it.

        Unrestricted, the optimal readout panel is the four interface relays --
        a correct answer to the wrong question, since their only declared proxy
        is "bounded stochastic initialization".
        """
        assayable = set(self.facts.assayable)
        for node_id in (
            "X_INTERFACE_SPP1_RELAY",
            "X_INTERFACE_REDUNDANT_RELAY",
            "X_INTERFACE_ANTIADHESIVE_RELAY",
            "X_MECHANICAL_STRESS_RELAY",
            "X_ADHESION_ROUTE_SPP1",
        ):
            self.assertNotIn(node_id, assayable)
        self.assertIn("E_KLF12_HIGH", assayable)
        self.assertIn("S_PRL", assayable)


class AdhesionEndpointTest(unittest.TestCase):
    def test_endpoint_is_arithmetic_on_two_typed_in_numbers(self) -> None:
        """0.82 is 1-(1-0.70)(1-0.40), not an inference.

        The decomposition must land on the hormone-treated challenge arm. The
        mifepristone challenge arm has more inputs ON and a constant-zero
        endpoint, so "most inputs on" picks the one arm carrying no information.
        """
        facts = load_identifiability(SUPERSET)
        endpoint = adhesion_endpoint_decomposition(facts)
        self.assertEqual(endpoint["arm"], "adhesion_challenge_hormone_treated")
        self.assertTrue(endpoint["endpoint_equals_disjunction_of_carriers"])
        self.assertEqual(
            endpoint["carrier_relays"],
            ("X_INTERFACE_SPP1_RELAY", "X_INTERFACE_REDUNDANT_RELAY"),
        )
        self.assertAlmostEqual(endpoint["analytic_value"], 0.82, places=6)
        self.assertEqual(endpoint["pinned_latent"], {"E_KLF12_HIGH": False})


class GainTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_identifiability(SUPERSET)
        cls.gain = compute_gain(cls.facts)

    def test_adding_an_arm_also_measures_the_existing_readouts_in_it(self) -> None:
        """An anti-SPP1 challenge is scored with its attachment count.

        Without this the marginal gain of every interface perturbation is zero,
        because nothing would be read out in the new arm -- a defect that made
        the analysis recommend no perturbations at all.
        """
        antispp1 = next(
            value
            for arm_id, value, _rationale in self.gain.arm_structural
            if arm_id == "adhesion_challenge_hormone_treated__IN_ANTI_SPP1"
        )
        self.assertGreater(antispp1, self.gain.baseline_design_classes)

    def test_most_candidate_readouts_add_nothing_under_the_current_arms(self) -> None:
        """The finding that has to survive: extra assays buy no information.

        They report states the design already covers, because the arms never
        make those states vary independently.
        """
        assayable = [(n, v) for n, v, ok in self.gain.readout_current if ok]
        zero = [n for n, v in assayable if v <= self.gain.baseline_fibers]
        self.assertGreater(len(zero), 0.75 * len(assayable))
        for node_id in ("S_PRL", "S_SPP1", "E_HBEGF", "E_ITGAVB3_5", "S_TAZ_ECM"):
            self.assertIn(node_id, zero)

    def test_perturbations_recover_structure_and_readouts_do_not(self) -> None:
        """The two currencies are not interchangeable, and the numbers show it.

        Arms alone take separable mechanism from 19 to nearly the 35 ceiling.
        Assayable readouts take internal-state resolution from 2 only to 8 of
        32; the rest is carried by placeholders no assay can reach, so it is a
        model repair, not an experiment.
        """
        self.assertEqual(self.gain.baseline_design_classes, 19)
        self.assertEqual(self.gain.global_ceiling, 35)
        self.assertGreaterEqual(self.gain.greedy_arms[-1][1], 34)
        self.assertEqual(self.gain.baseline_fibers, 2)
        self.assertEqual(self.gain.latent_ceiling, 32)
        self.assertEqual(self.gain.assayable_latent_ceiling, 8)
        self.assertEqual(self.gain.unrestricted_latent_ceiling, 32)

    def test_greedy_panel_is_not_beaten_by_an_exact_small_subset(self) -> None:
        """ "Near-minimal" is checked rather than asserted."""
        for panel, value in self.gain.exact_readout_panels:
            greedy_prefix = [n for n, _v in self.gain.greedy_readouts][: len(panel)]
            if len(greedy_prefix) == len(panel):
                greedy_value = self.gain.greedy_readouts[len(panel) - 1][1]
                self.assertLessEqual(value - greedy_value, 1, f"greedy lost on {panel}")

    def test_candidate_arms_use_a_permissive_background(self) -> None:
        """Not the arm with the most inputs on -- that one blocks PGR."""
        arm_ids = {c.arm_id for c in candidate_arms(self.facts)}
        self.assertIn("adhesion_challenge_hormone_treated__IN_ANTI_SPP1", arm_ids)
        self.assertNotIn(
            "adhesion_challenge_hormone_treated_mifepristone__IN_ANTI_SPP1", arm_ids
        )


class ScrnaReconciliationTest(unittest.TestCase):
    """Hold this analysis and `config/scrna_observation_map.tsv` to each other.

    The claim the document makes is that the scRNA route moves the latent
    frontier by exactly one class and then stops, so the numbers on both sides
    are pinned here and a change to either has to face the other.

    SCOPE, because the two sides are independent about one node and not about
    the rest. `E_KLF12_HIGH` is a curated map entry naming a transcript, an
    aggregation grain and an evidence role, owing nothing to this analysis. The
    four relays are NOT curated: they fall to `_default_curation`, which marks
    every `X_`-prefixed node unobservable by naming convention. The relay
    agreement therefore restates a shared convention rather than corroborating
    anything, and these tests assert that the convention holds -- not that two
    measurements agreed.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_identifiability(SUPERSET)
        with (ROOT / "config" / "scrna_observation_map.tsv").open(
            encoding="utf-8"
        ) as handle:
            cls.scrna = {
                row["model_node"]: row for row in csv.DictReader(handle, delimiter="\t")
            }

    def test_the_map_covers_every_latent_variable(self) -> None:
        """A silent gap would make every claim below vacuous."""
        for node_id in self.facts.latent:
            self.assertIn(
                node_id,
                self.scrna,
                f"{node_id} is latent here but absent from the scRNA map",
            )

    def test_only_klf12_is_observable_and_the_four_relays_are_not(self) -> None:
        """Stated as an equality rather than a count, so a new relay cannot hide.

        The relays declare `bounded stochastic initialization` as their proxy in
        this repository's node dictionary and the map marks the same four
        `not_observable` -- by the `X_` naming default, not by a data judgement,
        so this asserts the convention and not a corroboration. What it protects
        is real: if a latent variable ever appears that is neither a relay nor
        observable, the document's account of the wall is incomplete.
        """
        observable = {
            node_id
            for node_id in self.facts.latent
            if self.scrna[node_id]["measurement_observability"] != "not_observable"
        }
        self.assertEqual(observable, {"E_KLF12_HIGH"})
        for node_id in set(self.facts.latent) - observable:
            self.assertTrue(
                node_id.startswith("X_"),
                f"{node_id} is unobservable but is not a relay placeholder",
            )

    def test_klf12_is_the_only_istate_compatible_node_in_the_whole_map(self) -> None:
        """Not merely the only latent one -- the only one at all, of 59.

        Every other observable node is derived, so conditioning on its measured
        value needs a rule change and not a config edit. That is what makes the
        single gain below a hard ceiling on this route.
        """
        compatible = {
            node_id
            for node_id, row in self.scrna.items()
            if row["conditioning_compatibility"] == "istate_prior"
        }
        self.assertEqual(compatible, {"E_KLF12_HIGH"})

    def _refine_by_klf12(self) -> list[list[int]]:
        position = self.facts.latent.index("E_KLF12_HIGH")
        refined = []
        for _key, members in self.facts.fibers:
            for bit in (0, 1):
                part = [m for m in members if (m >> position) & 1 == bit]
                if part:
                    refined.append(part)
        return refined

    def test_conditioning_klf12_gives_three_classes_not_four(self) -> None:
        """Three, because the 12-member class already resolves `E_KLF12_HIGH`.

        Asserting four would be the arithmetic guess and would be wrong, so the
        count is pinned against the enumeration rather than against intuition.
        """
        self.assertEqual(len(self.facts.fibers), 2, "the baseline moved")
        self.assertEqual(len(self._refine_by_klf12()), 3)

    def test_conditioning_klf12_pins_two_relays_only_where_adhesion_fails(
        self,
    ) -> None:
        """A real gain, and precisely as far as it goes.

        With `E_KLF12_HIGH` off the endpoint reduces to
        `X_INTERFACE_SPP1_RELAY or X_INTERFACE_REDUNDANT_RELAY`, so observing no
        attachment in that branch pins both off. That is a genuine consequence
        of combining an scRNA prior with the attachment count -- and it holds in
        4 of the 32 internal configurations, in the branch where attachment
        FAILS, which is not the case the experiment is about.
        """
        latent = self.facts.latent
        relays = [n for n in latent if n.startswith("X_")]
        resolved_by_size = {
            len(part): {
                relay
                for relay in relays
                if len({(m >> latent.index(relay)) & 1 for m in part}) == 1
            }
            for part in self._refine_by_klf12()
        }
        self.assertEqual(
            resolved_by_size,
            {
                4: {"X_INTERFACE_SPP1_RELAY", "X_INTERFACE_REDUNDANT_RELAY"},
                16: set(),
                12: set(),
            },
        )

    def test_two_relays_are_resolved_in_no_branch_at_all(self) -> None:
        """The wall. Conditioning does not move it, and no assay reaches it.

        These two are unresolved before and after an scRNA prior. Identifying
        the interface is a model repair -- replace the relays with mechanism --
        and only then a measurement; the map's own default ceiling calls the
        same thing an assay limit, and the document keeps that difference
        visible rather than resolving it by assertion. If this ever passes with
        a smaller set, that conclusion has to be rewritten.
        """
        latent = self.facts.latent
        relays = [n for n in latent if n.startswith("X_")]
        never = set(relays)
        for part in self._refine_by_klf12():
            never -= {
                relay
                for relay in relays
                if len({(m >> latent.index(relay)) & 1 for m in part}) == 1
            }
        self.assertEqual(
            never,
            {"X_MECHANICAL_STRESS_RELAY", "X_INTERFACE_ANTIADHESIVE_RELAY"},
        )

    def test_no_observable_state_carries_held_out_evidence(self) -> None:
        """Conditioning on construction evidence is not validation.

        The map records 11 `construction` and 16 `same_dataset_internal` roles
        across the 27 observable states, and nothing held out or external. The
        document may therefore never call an scRNA-conditioned run validated.
        """
        roles = {
            row["evidence_role"]
            for row in self.scrna.values()
            if row["measurement_observability"] != "not_observable"
        }
        self.assertEqual(roles, {"construction", "same_dataset_internal"})
        self.assertEqual(
            self.scrna["E_KLF12_HIGH"]["evidence_role"], "same_dataset_internal"
        )

    def test_the_document_states_the_deficit_as_the_models_not_the_assays(
        self,
    ) -> None:
        """The framing this reconciliation exists to prevent regressing.

        27 observable states falling into 9 v0.4 signatures is a representational
        deficit of v0.4. A measured divergence inside an alias class FALSIFIES
        the aliasing; it is not an observation the assay was unable to make.
        """
        observable = [
            row
            for row in self.scrna.values()
            if row["measurement_observability"] != "not_observable"
        ]
        self.assertEqual(len(observable), 27)
        # An empty `v04_function_class` means the node realises a Boolean
        # function no other node does, so it is its own signature rather than a
        # shared one; collapsing the blanks together would undercount to 6.
        signatures = {
            row["v04_function_class"] or "distinct:" + row["model_node"]
            for row in observable
        }
        self.assertEqual(len(signatures), 9)

        text = (ROOT / "docs" / "identifiability_analysis.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("representational deficit of the model", text)
        self.assertIn("falsifies the aliasing", text.lower())
        for obsolete in (
            "scRNA can only observe nine",
            "resolves the alias class rather than the node",
            "conditioning one class member conditions the whole class",
        ):
            self.assertNotIn(obsolete, text, f"obsolete framing returned: {obsolete}")


class EffectAttributionNeedsASharedOutcome(unittest.TestCase):
    """`independently_perturbed` must mean attributable, not merely isolated.

    An earlier revision classified an input as independently perturbed as soon as
    two arms differed in it alone, and said in so many words that "its effect is
    attributable to it". Differing alone is necessary and not sufficient. If the
    two arms measure different nodes there is no common outcome whose change
    could be attributed to the input, so the contrast establishes nothing about
    its effect, and counting it alongside a real contrast reports a property of
    the input assignment as a property of the experiment.

    `IN_E2` is that case and `IN_MIFEPRISTONE` is not, which is what makes this
    checkable rather than a matter of wording: both are set alone by some arm
    pair, and only one of those pairs shares a readout.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_identifiability(SUPERSET)

    def _arms_by_id(self) -> dict[str, object]:
        return {arm.arm_id: arm for arm in self.facts.arms}

    def test_every_attributable_input_has_a_pair_sharing_a_readout(self) -> None:
        """The invariant itself, re-derived from the arms rather than trusted."""
        arms = list(self.facts.arms)
        for node_id in self.facts.independently_perturbed:
            found = False
            for left in arms:
                for right in arms:
                    differing = {
                        k
                        for k in self.facts.controlled
                        if left.inputs.get(k, False) != right.inputs.get(k, False)
                    }
                    if differing != {node_id}:
                        continue
                    shared = {n for n, _ in left.measured} & {
                        n for n, _ in right.measured
                    }
                    if shared:
                        found = True
            self.assertTrue(
                found,
                f"{node_id} is reported effect-attributable, but no arm pair "
                "differs in it alone while sharing a measured node",
            )

    def test_in_e2_is_isolated_but_not_attributable(self) -> None:
        """The concrete case, pinned so the classes cannot quietly re-merge."""
        self.assertIn("IN_E2", self.facts.set_alone_no_shared_readout)
        self.assertNotIn("IN_E2", self.facts.independently_perturbed)

        by_id = self._arms_by_id()
        left, right = by_id["basal_maternal"], by_id["e2_primed_maternal"]
        differing = {
            k
            for k in self.facts.controlled
            if left.inputs.get(k, False) != right.inputs.get(k, False)
        }
        self.assertEqual(differing, {"IN_E2"}, "the sole IN_E2 contrast moved")
        self.assertEqual(
            {n for n, _ in left.measured} & {n for n, _ in right.measured},
            set(),
            "the IN_E2 arms now share a readout; re-derive the classification",
        )

    def test_in_mifepristone_stays_attributable(self) -> None:
        """The companion direction, so the rule is not vacuously strict."""
        self.assertIn("IN_MIFEPRISTONE", self.facts.independently_perturbed)
        by_id = self._arms_by_id()
        left = by_id["adhesion_challenge_hormone_treated"]
        right = by_id["adhesion_challenge_hormone_treated_mifepristone"]
        self.assertIn(
            "OUT_STABLE_ADHESION",
            {n for n, _ in left.measured} & {n for n, _ in right.measured},
        )

    def test_the_two_classes_are_disjoint_and_reported_separately(self) -> None:
        independent = set(self.facts.independently_perturbed)
        isolated = set(self.facts.set_alone_no_shared_readout)
        self.assertEqual(independent & isolated, set())

        text = (ROOT / "docs" / "identifiability_analysis.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("no shared readout", text)
        self.assertNotIn(
            "2 (`IN_E2`, `IN_MIFEPRISTONE`)",
            text,
            "the merged count returned; IN_E2 is not effect-attributable",
        )


class TheEndpointFigureKeepsItsCondition(unittest.TestCase):
    """The relay-only reduction holds under a pinned latent value, so say so.

    The derivation filters to `E_KLF12_HIGH` false and the metadata records that
    pin, but the rendered text said the conditions hold "for every internal
    configuration" full stop -- claiming the mechanism across the very
    assignments the derivation excludes, in the one artifact a collaborator reads
    without the analysis beside it. Checked in every emitted format, because the
    figure is published as three and a caption fixed in one proves nothing about
    the others.
    """

    def test_the_caption_is_built_from_the_pin_and_cannot_omit_it(self) -> None:
        """Source-level, because that is what makes it true of EVERY format.

        All three figures are written from one caption string in one render
        call, so the qualification is either interpolated into that string or
        missing everywhere. Pinning the construction is a stronger statement
        than grepping one output, and it is the only one that holds for the PDF
        and PNG, whose text is compressed and rasterised respectively.
        """
        source = (
            ROOT / "src" / "dt_adoc" / "reporting" / "identifiability_figure.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'endpoint["pinned_latent"]',
            source,
            "the endpoint caption no longer reads the pinned latent value, so "
            "the condition is not derived from the derivation",
        )
        self.assertNotIn(
            "condition for attachment holds for every internal",
            source,
            "the unconditional wording returned: it claims the reduction across "
            "the latent assignments the derivation excludes",
        )

    def test_the_text_format_actually_shows_it(self) -> None:
        """And the claim is checked against a real emitted artifact, not only source."""
        import json

        meta = json.loads(
            (
                ROOT / "docs" / "identifiability" / "identifiability_metadata.json"
            ).read_text(encoding="utf-8")
        )
        pinned = meta["adhesion_endpoint"]["pinned_latent"]
        self.assertEqual(pinned, {"E_KLF12_HIGH": False}, "the pin moved")

        svg = next(
            ROOT / e["path"] for e in meta["figures"] if e["path"].endswith(".svg")
        )
        text = svg.read_text(encoding="utf-8", errors="ignore")
        self.assertIn(
            "E_KLF12_HIGH",
            text,
            "the rendered figure states the reduction without naming the latent "
            "value it is conditional on",
        )

    def test_the_recorded_hashes_match_the_emitted_figures(self) -> None:
        """So a caption fix cannot be claimed without regenerating the artifact."""
        import hashlib
        import json

        meta = json.loads(
            (
                ROOT / "docs" / "identifiability" / "identifiability_metadata.json"
            ).read_text(encoding="utf-8")
        )
        for entry in meta["figures"]:
            path = ROOT / entry["path"]
            with self.subTest(figure=path.name):
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(
                    digest,
                    entry["sha256"],
                    f"{path.name} differs from the hash the metadata records",
                )


class TheFibresDeclareTheirMatchedUnitAssumption(unittest.TestCase):
    """Fibres assume one unit carries one latent draw through the whole design.

    The construction applies a single latent index across every (arm, node) pair
    at once. That is a matched-unit design, and the current data are not one:
    adhesion is an aggregate count over embryos, the secretion mappings are
    explicitly unpaired, and the unit mapping is not recoverable. Under
    independent per-arm draws a joint observation constrains no shared
    assignment, so every count derived from these fibres describes a
    hypothetical design.

    The counts themselves are not wrong and are not changed here -- what was
    wrong was presenting them as current-data identifiability. This pins the
    withdrawal so the stronger reading cannot quietly return, in the metadata a
    tool reads and in the prose a person reads.
    """

    def test_the_metadata_records_the_assumption_beside_the_numbers(self) -> None:
        import json

        meta = json.loads(
            (
                ROOT / "docs" / "identifiability" / "identifiability_metadata.json"
            ).read_text(encoding="utf-8")
        )
        assumption = meta["summary"].get("unit_assumption", "")
        self.assertIn("MATCHED-UNIT", assumption)
        self.assertIn("NOT claims about what the current data identify", assumption)

    def test_the_analysis_withdraws_the_current_data_reading(self) -> None:
        text = (ROOT / "docs" / "identifiability_analysis.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("matched-unit", text.lower())
        self.assertIn("that reading is withdrawn", text)
        self.assertNotIn(
            "# What the current ADOC experiment can identify",
            text,
            "the title claiming current-data identifiability returned",
        )

    def test_the_structural_half_is_not_withdrawn(self) -> None:
        """The scoping must not be read as retracting what never needed pairing."""
        facts = load_identifiability(SUPERSET)
        self.assertEqual(len(facts.node_ids), 59)
        self.assertEqual(len(facts.global_classes), 35)


class PanelScopeTest(unittest.TestCase):
    """B1: panel B may not assert the reading its own document withdraws.

    The panel was titled "What the current experiment can determine" while
    `docs/identifiability_analysis.md` opens by withdrawing exactly that: every
    information status assumes one biological unit carries a single latent
    assignment through every arm and assay, which the current data do not
    provide. The string is baked into the committed SVG, PNG and PDF, so a
    caption fixed in one proves nothing about the others -- this pins the one
    construction all three are written from.
    """

    SOURCE = ROOT / "src" / "dt_adoc" / "reporting" / "identifiability_figure.py"

    def test_panel_b_does_not_claim_the_current_experiment(self) -> None:
        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertNotIn(
            "B  What the current experiment can determine",
            source,
            "the withdrawn current-data reading returned to the panel title",
        )

    def test_panel_b_is_scoped_to_the_matched_unit_assumption(self) -> None:
        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertIn(
            "B  What a matched-unit design of this shape could determine",
            source,
            "panel B no longer names the assumption its colours depend on",
        )
        self.assertIn(
            "MATCHED-UNIT ASSUMPTION: every colour below assumes one biological unit",
            source,
            "panel B's subtitle no longer states the assumption in the panel "
            "itself, so the figure can be read apart from its document",
        )


class PerturbationMarkerCoverageTest(unittest.TestCase):
    """B2: the figure may not silently drop a perturbation status it computes.

    `identifiability.py` writes six values into `perturbation_status`. The
    figure's marker table held two, so `set_alone_no_shared_readout` -- carried
    by exactly one node, `IN_E2`, and defended at length in
    `docs/identifiability_analysis.md` -- was drawn as though the input were
    never perturbed. The legend is derived from the same table, so a status
    that gains a marker gains a legend entry with it.
    """

    def test_the_set_alone_status_has_a_marker(self) -> None:
        from dt_adoc.reporting.identifiability_figure import PERTURBATION_MARKER

        self.assertIn(
            "set_alone_no_shared_readout",
            PERTURBATION_MARKER,
            "the status IN_E2 alone carries is drawn as if it were absent",
        )

    def test_every_drawable_status_is_reachable_and_legended(self) -> None:
        """A marker nothing selects, or a status nothing draws, is a silent gap."""
        from dt_adoc.reporting.identifiability_figure import (
            _PERTURBATION_PRECEDENCE,
            PERTURBATION_MARKER,
        )

        self.assertEqual(
            set(_PERTURBATION_PRECEDENCE),
            set(PERTURBATION_MARKER),
            "the precedence order and the marker table disagree, so a status "
            "is either undrawn or unreachable",
        )
        for status, (marker, colour, label) in PERTURBATION_MARKER.items():
            self.assertTrue(marker and colour and label, status)
        self.assertEqual(
            len({colour for _, colour, _ in PERTURBATION_MARKER.values()}),
            len(PERTURBATION_MARKER),
            "two perturbation statuses share a colour",
        )
        self.assertEqual(
            len({marker for marker, _, _ in PERTURBATION_MARKER.values()}),
            len(PERTURBATION_MARKER),
            "two perturbation statuses share a marker glyph",
        )

    def test_the_marked_statuses_are_exactly_the_attributable_ones(self) -> None:
        """The three drawn statuses are the three where an arm moves the input.

        `not_an_input`, `never_perturbed` and `latent_not_settable` describe
        inputs no arm moves, so they have nothing to mark. If the classifier
        ever emits a fourth moved-input status, this fails rather than letting
        the figure quietly omit it.
        """
        from dt_adoc.reporting.identifiability_figure import PERTURBATION_MARKER

        facts = load_identifiability(SUPERSET)
        moved = {
            status
            for status in facts.perturbation_status.values()
            if status not in {"not_an_input", "never_perturbed", "latent_not_settable"}
        }
        self.assertEqual(moved, set(PERTURBATION_MARKER))

    def test_in_e2_is_the_node_the_marker_exists_for(self) -> None:
        facts = load_identifiability(SUPERSET)
        carriers = {
            node
            for node, status in facts.perturbation_status.items()
            if status == "set_alone_no_shared_readout"
        }
        self.assertEqual(carriers, {"IN_E2"})


if __name__ == "__main__":
    unittest.main()
