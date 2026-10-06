"""Stage 3: the experiment-selection computation, and the claims that rest on it.

`docs/stage3_experiment_selection.md` recommends one prospective arm and demotes
several candidates that earlier documents ranked higher. Each of those moves is a
computed fact about the committed network, not a judgement, so each is pinned
here -- including the exact set of class pairs each arm reaches, which is what a
prose claim about "this arm cannot test X" actually rests on. If one of these
ever passes trivially -- because a fork stopped being evaluated, or an experiment
was dropped from the catalogue -- the recommendation has quietly lost its support.

Two of these tests exist because the first version of the artifact stated the
complement of what the shipped pair index said, and no assertion covered it.
"""

from __future__ import annotations

import csv
import re
import unittest

from dt_adoc.experiments.stage3_design import (
    ADOPTABLE,
    COMMITTED,
    CONFOUNDER_ONLY,
    EXPERIMENTS,
    FORKS,
    OUT_MD,
    OUT_TABLES,
    OUT_TSV,
    RECOMMENDED,
    RECOMMENDED_FORK,
    SCRNA_OBSERVABLE,
    TSV_COLUMNS,
    USABLE_ASSAY,
    _propagation_cell,
    _rows,
    _scrna_assessment,
    _scrna_can_alter_a_readout_tier,
    _scrna_conditions,
    evaluate,
    render,
    render_tables,
)
from dt_adoc.reporting.identifiability import repo_root

ROOT = repo_root()


class Stage3DesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = evaluate(ROOT)
        cls.by_experiment = {r["experiment"]: r for r in cls.report["results"]}

    # -- the observation layer ------------------------------------------------

    def test_only_two_maternal_nodes_carry_a_usable_assay(self) -> None:
        """The premise the whole ranking rests on.

        Every candidate is scored by whether its separation lands on a node the
        observation layer can validate. If that set ever grows silently, the
        ranking is stale rather than wrong, and nothing else here would notice.
        """
        usable = {
            node
            for node, (tier, _note) in self.report["readout_tiers"].items()
            if tier == USABLE_ASSAY
        }
        self.assertEqual(usable, {"E_PAEP", "S_IGFBP1"})

    # -- the recommendation ---------------------------------------------------

    def test_dropout_e2_is_the_only_arm_separating_both_usable_assays(self) -> None:
        both = []
        for result in self.report["results"]:
            nodes = {
                hit["node"]
                for fork in result["forks"]
                for pair in fork["pairs"]
                for hit in pair["usable"]
            }
            if {"E_PAEP", "S_IGFBP1"} <= nodes:
                both.append(result["experiment"])
        self.assertEqual(both, ["dropout_e2"])

    def test_dropout_e2_separates_the_committed_class_from_every_other(self) -> None:
        """Opposite predictions, on a usable assay, against all three rivals.

        `SEC-a` is the committed rule. An experiment that separated only the
        alternatives from each other could not falsify v0.4, which is the point
        of running it.
        """
        fork = next(
            f for f in self.by_experiment["dropout_e2"]["forks"] if f["fork"] == "SEC"
        )
        against_committed = {
            pair["right"]: pair
            for pair in fork["pairs"]
            if pair["left"] == "SEC-a" and pair["usable_opposite"]
        }
        self.assertEqual(set(against_committed), {"SEC-b", "SEC-c", "SEC-d"})
        self.assertEqual(
            {h["node"] for h in against_committed["SEC-b"]["usable_opposite"]},
            {"E_PAEP"},
        )
        # The stromal outlet is what excludes the confounder; an epithelium-only
        # readout cannot tell SEC-a from SEC-d at all.
        self.assertEqual(
            {h["node"] for h in against_committed["SEC-d"]["usable_opposite"]},
            {"S_IGFBP1"},
        )

    def _pairs_separated_by(self, experiment_id: str, fork_id: str) -> set[str]:
        fork = next(
            f
            for f in self.by_experiment[experiment_id]["forks"]
            if f["fork"] == fork_id
        )
        return {f"{p['left']} vs {p['right']}" for p in fork["pairs"] if p["hits"]}

    def test_the_e2_only_arms_resolve_only_whether_sec_c_survives(self) -> None:
        """The pin that two wrong prose claims got past.

        An earlier draft of `stage3_experiment_selection.md` said the E2-only
        observation and its hCG variant separate `SEC-a` from nothing. They
        separate it from `SEC-c`, and the shipped pair index said so. What is
        true -- and what the recommendation actually rests on -- is narrower:
        EVERY pair these arms reach has `SEC-c` on one side, so they decide
        whether `SEC-c` survives and cannot tell `SEC-a` from `SEC-b` or from
        `SEC-d`. Assert the exact set, not its consequences, so that neither the
        claim nor its negation can drift again.
        """
        for experiment_id in ("observe_e2_primed", "add_hcg_on_e2"):
            reached = self._pairs_separated_by(experiment_id, "SEC")
            self.assertTrue(reached, experiment_id)
            # The invariant, not a literal set: adding a class to the fork
            # enlarges the set without changing what these arms decide.
            self.assertTrue(
                all("SEC-c" in pair for pair in reached),
                f"{experiment_id}: every reachable pair must involve SEC-c",
            )
            for unreachable in ("SEC-a vs SEC-b", "SEC-a vs SEC-e"):
                self.assertNotIn(unreachable, reached, experiment_id)
        # The complement is what makes `dropout_e2` necessary rather than merely
        # better: it reaches every pair these arms cannot.
        reached = self._pairs_separated_by("dropout_e2", "SEC")
        for pair in ("SEC-a vs SEC-b", "SEC-a vs SEC-c", "SEC-a vs SEC-d"):
            self.assertIn(pair, reached)
        self.assertNotIn("SEC-b vs SEC-c", reached)

    def test_both_hcg_arms_reach_the_cd98_pair_that_needs_hcg(self) -> None:
        """`CD98-a vs CD98-b` is reachable from either hCG background.

        Pinned because a draft claimed the E2-only background was the only one
        that reaches it, which would have made an E2-only arm look necessary for
        the CD98 axis when it is not.
        """
        reaching = {
            result["experiment"]
            for result in self.report["results"]
            for fork in result["forks"]
            if fork["fork"] == "CD98"
            for pair in fork["pairs"]
            if (pair["left"], pair["right"]) == ("CD98-a", "CD98-b") and pair["hits"]
        }
        self.assertEqual(reaching, {"add_hcg_on_e2", "add_hcg_on_hormone_treated"})

    def test_the_four_outcome_decision_table_is_what_the_model_predicts(self) -> None:
        """Each cell of the §5 table, read back off the computation."""
        fork = next(
            f for f in self.by_experiment["dropout_e2"]["forks"] if f["fork"] == "SEC"
        )
        expected = {
            "SEC-a": (0.0, 1.0),
            "SEC-b": (1.0, 1.0),
            "SEC-c": (1.0, 1.0),
            "SEC-d": (0.0, 0.0),
        }
        for class_id, (paep, igfbp1) in expected.items():
            predicted = fork["predictions"][class_id]
            self.assertEqual(predicted["E_PAEP"], paep, class_id)
            self.assertEqual(predicted["S_IGFBP1"], igfbp1, class_id)

    # -- the demotions --------------------------------------------------------

    def test_anti_lif_alone_separates_no_gp130_class(self) -> None:
        """Neutralising LIF cannot test `E_GP130_STAT3 = E_LIF`.

        Both readings agree wherever IL-11 is not supplied, so the separation
        needs a supplied ligand -- and an opposite separation needs anti-LIF and
        IL-11 together, which is two perturbations.
        """
        fork = next(
            f for f in self.by_experiment["anti_lif"]["forks"] if f["fork"] == "GP130"
        )
        self.assertEqual([p["hits"] for p in fork["pairs"]], [[]])
        supplied = next(
            f for f in self.by_experiment["add_il11"]["forks"] if f["fork"] == "GP130"
        )
        self.assertTrue(any(p["hits"] for p in supplied["pairs"]))

    def test_the_constitutive_cd98_reading_survives_the_e2_only_arm(self) -> None:
        """Why the earlier top-ranked CD98 measurement was demoted.

        `CD98-c` (E2 induces CD98) and `CD98-x` (CD98 is constitutive) predict
        the same thing under E2-only priming, with or without hCG. A
        presence/absence surface readout in that arm therefore cannot exclude
        the most likely explanation of a positive result.
        """
        separating = [
            result["experiment"]
            for result in self.report["results"]
            for fork in result["forks"]
            if fork["fork"] == "CD98"
            for pair in fork["pairs"]
            if (pair["left"], pair["right"]) == ("CD98-c", "CD98-x") and pair["hits"]
        ]
        self.assertEqual(separating, ["dropout_e2"])

    def test_interventions_that_separate_nothing(self) -> None:
        """Five candidates that would cost a donor and buy no discrimination.

        The CD98 fork is excluded from the count on purpose. Its confounder
        class `CD98-x` is a constant, so it differs from the committed rule in
        almost every arm; counting that would make every intervention look
        informative. What matters for CD98 is which PAIR an arm separates, and
        that is pinned separately above.
        """
        for experiment_id in (
            "bmpr_inhibitor",
            "pc6_knockdown",
            "anti_spp1",
            "hand2_loss",
            "dropout_xav939",
        ):
            result = self.by_experiment[experiment_id]
            informative = [
                fork["fork"]
                for fork in result["forks"]
                if fork["fork"] != "CD98" and any(p["hits"] for p in fork["pairs"])
            ]
            self.assertEqual(informative, [], experiment_id)

    def test_xav939_and_smo_propagate_nowhere_in_the_committed_model(self) -> None:
        """The two arms whose null is confounded with failed engagement.

        `IN_XAV939` is read by no rule, and Hedgehog reception is subsumed by the
        direct PGR route, so the committed model predicts that neither
        intervention reaches any maternal node. That is a design requirement for
        the runner-up -- it must buy its own engagement control -- and it is the
        computed reason XAV939 dropout is not an experiment.
        """
        for experiment_id in ("dropout_xav939", "smo_antagonist"):
            result = self.by_experiment[experiment_id]
            # Both DO apply something, so an empty set is a fact about the
            # network rather than arithmetic -- unlike the observation arms.
            self.assertFalse(result["applies_nothing"], experiment_id)
            self.assertEqual(result["committed_model_changes"], [], experiment_id)
        # ...and the recommendation is not in that position.
        self.assertTrue(self.by_experiment["dropout_e2"]["committed_model_changes"])

    def test_anti_spp1_reaches_no_maternal_node(self) -> None:
        self.assertEqual(self.by_experiment["anti_spp1"]["committed_model_changes"], [])

    # -- contracts on the declarations ----------------------------------------

    def test_confounder_classes_are_never_presented_as_adoptable(self) -> None:
        """A class carried to be excluded must not read as a proposed repair.

        `SEC-d` and `CAMP-b` encode rules no repository evidence row supports.
        They exist so the experiment can be required to rule them out; marking
        either adoptable would be exactly the intuition-filling the evidence
        standards forbid.
        """
        roles = {klass.class_id: klass.role for fork in FORKS for klass in fork.classes}
        for class_id in ("SEC-d", "CAMP-b", "CD98-x"):
            self.assertEqual(roles[class_id], CONFOUNDER_ONLY, class_id)
        for fork in FORKS:
            committed = [k for k in fork.classes if k.role == COMMITTED]
            self.assertEqual(len(committed), 1, fork.fork_id)
            self.assertEqual(committed[0].overrides, {}, fork.fork_id)
            # A fork whose only alternative is confounder-only is legitimate --
            # `CAMP` is one -- but then every confounder must say what an outcome
            # favouring it LICENSES, since that is what the role means. A bare
            # support argument there reintroduces the criterion R2 removed, and
            # a blanket exemption for the fork would hide it.
            self.assertTrue(
                any(k.role in (ADOPTABLE, CONFOUNDER_ONLY) for k in fork.classes),
                fork.fork_id,
            )
        for fork in FORKS:
            for klass in fork.classes:
                if klass.role != CONFOUNDER_ONLY:
                    continue
                # `licen` and nothing else. An earlier version of this
                # assertion also accepted "carried", which made it pass on the
                # exact bare-support string it was added to reject -- so the
                # invariant was weakened to fit three classes that did not state
                # a licensing consequence, instead of those classes being fixed.
                # They are fixed now. Verified by mutation: the pre-repair
                # `CAMP-b` evidence fails this.
                self.assertIn(
                    "licen",
                    klass.evidence.lower(),
                    f"{klass.class_id}: a confounder must say what an outcome "
                    "favouring it LICENSES, not only how well supported it is",
                )

    def test_role_is_about_what_an_outcome_licenses_not_about_support(self) -> None:
        """The distinction two earlier versions of this module got wrong.

        `role` is not a ranking of evidential support. `SEC-b` is ADOPTABLE with
        no prior support at all -- nothing recorded tells it from the committed
        rule, which is the reason to run the arm -- while `SEC-d` has exactly as
        little and is CONFOUNDER_ONLY, because a favourable outcome would point
        at a PGR rule and license opening a gap rather than an edit. If those two
        ever agree on role, or if `SEC-b` quietly acquires a support claim it
        does not have, the distinction has collapsed again.
        """
        by_id = {k.class_id: k for fork in FORKS for k in fork.classes}
        self.assertEqual(by_id["SEC-b"].role, ADOPTABLE)
        self.assertEqual(by_id["SEC-d"].role, CONFOUNDER_ONLY)
        for class_id in ("SEC-b", "SEC-d", "CAMP-b", "CD98-x"):
            self.assertTrue(
                by_id[class_id].prior_support.lower().startswith("none"),
                f"{class_id}: prior support must still be none",
            )
        # ...and the observation that DOES support a class supports only that
        # one. SEC-b's entry may name OM-001 -- it has to, in order to say the
        # measurement cannot discriminate it -- so assert the claim, not the
        # token: the two classes must disagree about what OM-001 establishes.
        self.assertIn("OM-001", by_id["SEC-c"].prior_support)
        self.assertIn("cannot tell them apart", by_id["SEC-b"].prior_support)
        self.assertEqual(
            self._pairs_separated_by("observe_e2_primed", "SEC") & {"SEC-a vs SEC-b"},
            set(),
            "no arm carrying OM-001's data may separate SEC-a from SEC-b",
        )

    def test_every_class_declares_prior_support_separately(self) -> None:
        for fork in FORKS:
            for klass in fork.classes:
                self.assertTrue(klass.prior_support.strip(), klass.class_id)

    def test_an_arm_that_applies_nothing_gets_no_propagation_verdict(self) -> None:
        """An empty downstream set is arithmetic when nothing is applied.

        With no overrides and no clamps the two marginal evaluations receive
        identical inputs, so the set is empty for any network whatever. Printing
        the same **no** there as for an intervention would charge the zero-cost
        observation arms with a design demerit the computation never tested.
        """
        for experiment_id in ("observe_e2_primed", "observe_hormone_treated"):
            result = self.by_experiment[experiment_id]
            self.assertTrue(result["applies_nothing"], experiment_id)
            self.assertEqual(result["committed_model_changes"], [], experiment_id)
            self.assertEqual(_propagation_cell(result), "n/a", experiment_id)
        # The interventions whose null IS informative keep their verdict.
        self.assertEqual(
            _propagation_cell(self.by_experiment["dropout_xav939"]), "**no**"
        )
        self.assertEqual(_propagation_cell(self.by_experiment["dropout_e2"]), "yes")

    def test_the_tier_columns_partition_the_forks_an_arm_separates(self) -> None:
        """Every separated fork lands in exactly one tier column.

        The §2 table of `stage3_experiment_selection.md` lists only forks
        separated on a readout that EXISTS, and two earlier versions of its
        stated rule did not cover what the table actually omitted. The rule is
        only checkable if the three tier sets are a partition, so assert that
        they are.
        """
        for result in self.report["results"]:
            usable = set(result["forks_separated_usable_assay"])
            composite = set(result["forks_separated_mapped_composite"])
            no_assay = set(result["forks_separated_no_assay_only"])
            self.assertEqual(
                usable | composite | no_assay,
                set(result["forks_separated_any"]),
                result["experiment"],
            )
            self.assertEqual(
                len(usable) + len(composite) + len(no_assay),
                len(usable | composite | no_assay),
                result["experiment"],
            )

    def test_the_cd98_axis_is_unmeasurable_in_every_arm(self) -> None:
        """Separable in many arms, decidable in none — including both hCG arms.

        This is the fact that justifies leaving CD98 out of the selection doc's
        "classes separated" column for every row, and it is stronger than either
        rationale that column carried before: it does not depend on `CD98-x`
        being a constant, and it covers `CD98-a/b`, which the two hCG arms do
        reach and which an earlier draft therefore listed as though it counted.
        """
        reached_anywhere = False
        for result in self.report["results"]:
            self.assertNotIn(
                "CD98", result["forks_separated_usable_assay"], result["experiment"]
            )
            self.assertNotIn(
                "CD98",
                result["forks_separated_mapped_composite"],
                result["experiment"],
            )
            if "CD98" in result["forks_separated_any"]:
                reached_anywhere = True
                self.assertIn(
                    "CD98",
                    result["forks_separated_no_assay_only"],
                    result["experiment"],
                )
        self.assertTrue(reached_anywhere, "CD98 must still be separable somewhere")

    def test_every_experiment_declares_its_own_costs(self) -> None:
        for experiment in EXPERIMENTS:
            self.assertTrue(experiment.assay_note, experiment.experiment_id)
            self.assertTrue(experiment.feasibility, experiment.experiment_id)
            self.assertIn(
                experiment.protocol_status,
                {
                    "existing_recorded_state",
                    "existing_phase_new_sampling",
                    "new_arm",
                },
                experiment.experiment_id,
            )

    def test_the_committed_artifacts_match_a_fresh_computation(self) -> None:
        """Both artifacts, compared in memory rather than by rebuilding in place.

        The MD is checked as well as the TSV: the pair index lives only in the
        MD, both documents cite it, and leaving it unpinned is how two prose
        claims contradicting it shipped green.

        Nothing is written. Calling `build()` against the checked-out tree and
        restoring afterwards leaves a window in which an interrupted or
        concurrent run abandons modified artifacts, and this repository is
        worked on from more than one checkout.
        """
        report = evaluate(ROOT)
        self.assertEqual(
            (ROOT / OUT_TSV).read_text(encoding="utf-8").splitlines(),
            ["\t".join(TSV_COLUMNS)] + ["\t".join(row) for row in _rows(report)],
            "regenerate with `pixi run build-stage3-design`",
        )
        self.assertEqual(
            (ROOT / OUT_MD).read_text(encoding="utf-8").splitlines(),
            render(report).splitlines(),
            "regenerate with `pixi run build-stage3-design`",
        )

    def test_the_selection_document_does_not_restate_the_generated_tables(
        self,
    ) -> None:
        """The structural fix, asserted rather than intended.

        Four review rounds on `stage3_experiment_selection.md` found one class of
        defect and nothing else: a hand-written sentence about a computed cell
        that the artifact contradicted. The repair was to generate the tables and
        cite them. If a future edit pastes one back in, the drift site returns
        and this is the only thing that would notice.
        """
        doc = (ROOT / "docs/stage3_experiment_selection.md").read_text(encoding="utf-8")
        for header in (
            "| Experiment | Axis separated on a readout that exists |",
            "| Size | Class | Contains a usable assay? |",
            "| Experiment | Mechanism tested |",
        ):
            self.assertNotIn(header, doc, f"table restated: {header}")
        self.assertIn("stage3_decision_tables.md", doc, "the tables must be cited")
        # No class row survives in the document at all. The four that did were
        # the last drift site, and the test guarding them compared only the
        # class ids and `none` against non-`none` -- so a non-`none` support
        # entry could have drifted to a different non-`none` claim unnoticed.
        # Generating them removes the question rather than strengthening the
        # comparison.
        self.assertEqual(
            re.findall(r"^\| `([A-Z0-9]+-[a-z])` \| ", doc, re.MULTILINE),
            [],
            "class rows must live in table D, not here",
        )

    def test_the_document_never_enumerates_computed_pair_sets(self) -> None:
        """The enumeration that went stale twice, forbidden rather than updated.

        Listing which class pairs an arm separates is a computed fact, and every
        time it was written out by hand it went stale the moment the fork gained
        a class. It belongs in the generated pair index. The structural
        statements the document does keep -- every pair the E2-only arms reach
        has `SEC-c` on one side, and exactly one pair is unreachable -- survive a
        fork that grows, and are pinned elsewhere.
        """
        doc = (ROOT / "docs/stage3_experiment_selection.md").read_text(encoding="utf-8")
        enumerations = re.findall(r"`SEC-[a-z]/[a-z]`(?:,| and| or)\s+`SEC-", doc)
        self.assertEqual(
            enumerations, [], "pair lists belong in the generated pair index"
        )
        # A bare COUNT is the same defect wearing different clothes, and this
        # test did not catch it: removing the list and leaving the number is how
        # "separate three pairs" survived a fix and was reported a third time.
        # Plural only -- "exactly one pair is unreachable" is the structural
        # statement the design rests on, is stable, and is pinned elsewhere.
        counts = re.findall(
            r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+pairs\b",
            doc,
            re.IGNORECASE,
        )
        self.assertEqual(
            counts, [], "pair counts belong in the generated pair index too"
        )

    def test_the_decision_tree_inverts_the_generated_predictions(self) -> None:
        """§5 maps observation -> class; table C maps class -> prediction.

        §5 has to stay hand-written: which model action a result licenses is a
        judgement, not a computation. But its first three columns are the
        INVERSE of table C, and an inverse can drift from what it inverts. So
        parse the table out of the document and check the mapping both ways.
        """
        doc = (ROOT / "docs/stage3_experiment_selection.md").read_text(encoding="utf-8")
        block = re.search(r"^\| PAEP \(top\).*?\n\n", doc, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(block, "§5 decision table not found")
        claimed: dict[tuple[str, str], set[str]] = {}
        for line in block.group(0).splitlines()[2:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 3 or "indeterminate" in cells[0]:
                continue
            key = (cells[0].strip("*"), cells[1].strip("*"))
            claimed[key] = set(re.findall(r"`(SEC-[a-z])`", cells[2]))

        fork = next(
            f
            for f in self.by_experiment[RECOMMENDED]["forks"]
            if f["fork"] == RECOMMENDED_FORK
        )
        computed: dict[tuple[str, str], set[str]] = {}
        for class_id, values in fork["predictions"].items():
            key = (
                "ON" if values["E_PAEP"] == 1.0 else "OFF",
                "ON" if values["S_IGFBP1"] == 1.0 else "OFF",
            )
            computed.setdefault(key, set()).add(class_id)

        self.assertEqual(
            {k: v for k, v in claimed.items() if v},
            computed,
            "§5's observation -> class mapping must invert table C",
        )
        # ...and the pattern no class predicts must be listed as supporting none.
        unpredicted = {
            ("ON", "OFF"),
            ("OFF", "ON"),
            ("ON", "ON"),
            ("OFF", "OFF"),
        } - set(computed)
        for key in unpredicted:
            self.assertIn(key, claimed, f"{key} must appear, as supporting nothing")
            self.assertEqual(claimed[key], set(), key)

    def test_the_arm_cannot_say_where_e2_acts(self) -> None:
        """`SEC-a` and `SEC-e` predict the same thing where it can be measured.

        This is what stops a `PAEP OFF + IGFBP-1 ON` result licensing the
        committed conjunction specifically. `SEC-e` -- E2 acting only by
        maintaining EPITHELIAL PGR -- gives the identical pattern on both usable
        assays, and the two separate only at nodes nothing can assay. An
        external review raised this in prose; the computation states it exactly,
        and §5 may not claim more than this test allows.
        """
        fork = next(
            f
            for f in self.by_experiment[RECOMMENDED]["forks"]
            if f["fork"] == RECOMMENDED_FORK
        )
        pair = next(
            p for p in fork["pairs"] if {p["left"], p["right"]} == {"SEC-a", "SEC-e"}
        )
        self.assertEqual(pair["usable"], [], "SEC-a/SEC-e must be unmeasurable here")
        self.assertTrue(pair["hits"], "they must still differ, just not measurably")
        self.assertTrue(
            all(h["readout_tier"] == "no_assay" for h in pair["hits"]),
            "every SEC-a/SEC-e difference must sit at no_assay",
        )
        predictions = fork["predictions"]
        for node in ("E_PAEP", "S_IGFBP1"):
            self.assertEqual(
                predictions["SEC-a"][node], predictions["SEC-e"][node], node
            )
        # And it is not this arm's failing: no arm in the catalogue reaches the
        # pair on a readout that exists, which is what §3 and §7 now claim.
        unreached = [
            (p["left"], p["right"])
            for p in fork["pairs"]
            if not any(
                q["usable"]
                for result in self.report["results"]
                for f in result["forks"]
                if f["fork"] == RECOMMENDED_FORK
                for q in f["pairs"]
                if (q["left"], q["right"]) == (p["left"], p["right"])
            )
        ]
        self.assertEqual(unreached, [("SEC-a", "SEC-e")])

    def test_the_ranking_is_invariant_under_any_scrna_result(self) -> None:
        """The load-bearing step of the closure argument in §3a and table F.

        `dropout_e2` is preferred for separating a fork on a readout that
        EXISTS, and that tier is computed from `config/observation_model_map.tsv`
        alone. If the scRNA layer ever activated a row, it could promote a node
        to `usable_assay`, a fork decided at `no_assay` could become decidable,
        and the invariance argument would have to be rerun rather than restated.
        Nothing else in the suite would notice.
        """
        activated, statuses = _scrna_can_alter_a_readout_tier(ROOT)
        self.assertFalse(
            activated, f"an scRNA row became active ({statuses}); rerun table F"
        )
        # The forks an AC04 result bears on are not decided at the deciding tier,
        # so neither extreme can move them into the candidate set.
        assessment = {a["fork"]: a for a in _scrna_assessment(evaluate(ROOT), ROOT)}
        for fork in ("GP130", "CD98"):
            self.assertNotEqual(assessment[fork]["decided_at"], USABLE_ASSAY, fork)
        deciding = {
            result["experiment"]
            for result in self.report["results"]
            if result["forks_separated_usable_assay"]
        }
        self.assertIn(RECOMMENDED, deciding)
        self.assertFalse(
            {"GP130", "CD98"}
            & {
                f
                for result in self.report["results"]
                for f in result["forks_separated_usable_assay"]
            },
            "no arm decides GP130 or CD98 on a usable assay",
        )

    def test_the_scrna_design_lacks_the_contrast_the_sec_fork_needs(self) -> None:
        """Two conditions, bundled. The design reason, not the evidence-role one.

        `HT` moves E2, MPA, cAMP and XAV939 together and there is no E2-dropout
        condition, so the contrast separating `SEC-a` from `SEC-b` is absent from
        that dataset however well its genes are detected.
        """
        conditions, donors = _scrna_conditions(ROOT)
        self.assertEqual(conditions, ["CNT", "HT"])
        self.assertEqual(len(donors), 3)

    def test_the_scrna_verdict_depends_only_on_the_separating_quantities(
        self,
    ) -> None:
        """Identical separators must give identical verdicts.

        The invariant a real logic bug broke: `_scrna_verdict` also took the
        arm's INTERVENTIONS, so `GP130` -- whose only separator is unobservable,
        exactly like `PC6`'s -- was diverted into `PROXY_LEVEL_ONLY` because its
        arm perturbs the observable `E_LIF`. That verdict's own definition was
        false of it. Being able to see what you perturb constrains nothing if
        you cannot see the consequence that separates the classes.
        """
        report = evaluate(ROOT)
        assessment = _scrna_assessment(report, ROOT)
        by_signature: dict[tuple, set[str]] = {}
        for entry in assessment:
            signature = tuple(
                sorted((level, role) for _node, level, role in entry["separating"])
            )
            by_signature.setdefault(signature, set()).add(entry["verdict"])
        for signature, verdicts in by_signature.items():
            self.assertEqual(len(verdicts), 1, f"{signature} -> {verdicts}")
        # The two the bug separated, named so the regression is legible.
        verdicts = {e["fork"]: e["verdict"] for e in assessment}
        self.assertEqual(verdicts["GP130"], verdicts["PC6"])
        self.assertEqual(verdicts["GP130"], "NOT_OBSERVABLE")
        # ...and each verdict must be true of its own separators.
        levels = {
            e["fork"]: {level for _n, level, _r in e["separating"]} for e in assessment
        }
        for fork, verdict in verdicts.items():
            if verdict == "PROXY_LEVEL_ONLY":
                self.assertIn("proxy_abundance_not_activity", levels[fork], fork)
            if verdict == "NOT_OBSERVABLE":
                self.assertFalse(levels[fork] & SCRNA_OBSERVABLE, fork)
                self.assertNotIn("proxy_abundance_not_activity", levels[fork], fork)

    def test_the_scrna_layer_cannot_move_the_fork_that_decides_the_ranking(
        self,
    ) -> None:
        """Evidence in hand is checked before new material is spent.

        The `SEC` fork is decided on `E_PAEP` and `S_IGFBP1`, and the scRNA map
        gives both `evidence_role = construction`: they helped build v0.4, so
        judging v0.4 by them is leakage. Its discriminating input is not
        observable in RNA at all. If either ever changed, the recommendation
        would have to be re-derived rather than re-stated.
        """
        report = evaluate(ROOT)
        assessment = {a["fork"]: a for a in _scrna_assessment(report, ROOT)}
        sec = assessment["SEC"]
        self.assertEqual(sec["decided_at"], USABLE_ASSAY)
        self.assertEqual(sec["verdict"], "CONSTRUCTION_ROLE_ONLY")
        self.assertEqual(
            {node for node, _level, _role in sec["separating"]},
            {"E_PAEP", "S_IGFBP1"},
        )
        self.assertTrue(
            all(role == "construction" for _n, _l, role in sec["separating"])
        )
        self.assertIn(("IN_E2", "not_observable"), sec["interventions"])
        # No fork the ranking turns on is constrainable from evidence in hand.
        self.assertNotIn(
            "IN_PRINCIPLE_CONSTRAINABLE",
            {a["verdict"] for a in assessment.values()},
        )

    def test_every_compartment_the_arm_reads_has_a_declared_control(self) -> None:
        """The invariant behind a defect that took two rounds to surface.

        `feasibility` is prose in the module that renders verbatim into both
        generated artifacts, and §4 of the selection document is prose about the
        same design. Two prose sources for one fact drift, and they did: §4 was
        widened to require confluence imaging in both channels while the
        declaration still named only the epithelial one, so the table a reader
        is sent to for feasibility described the control §4 had just called
        insufficient.

        The checkable invariant is that a compartment the arm READS must be a
        compartment whose viability the arm CONTROLS. Derive the compartments
        from the usable-assay nodes the arm actually separates on, and require
        each to be named in both places.
        """
        compartments = {"E_": "epithelial", "S_": "stromal"}
        read = {
            compartments[hit["node"][:2]]
            for fork in self.by_experiment[RECOMMENDED]["forks"]
            for pair in fork["pairs"]
            for hit in pair["usable"]
            if hit["node"][:2] in compartments
        }
        self.assertEqual(read, {"epithelial", "stromal"}, "the arm reads both outlets")
        declared = next(
            e for e in EXPERIMENTS if e.experiment_id == RECOMMENDED
        ).feasibility.lower()
        doc = (ROOT / "docs/stage3_experiment_selection.md").read_text(encoding="utf-8")
        design = re.search(r"^## 4\..*?^---", doc, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(design, "§4 not found")
        for compartment in sorted(read):
            self.assertIn(
                compartment,
                declared,
                f"{RECOMMENDED}'s feasibility must name the {compartment} control",
            )
            self.assertIn(
                compartment,
                design.group(0).lower(),
                f"§4 must name the {compartment} control",
            )

    def test_recommended_matches_the_arm_the_document_recommends(self) -> None:
        """Nothing otherwise ties the constant to the recommendation.

        Table C is generated for whatever `RECOMMENDED` names. If §3 ever
        recommended a different arm, the table would keep generating for
        `dropout_e2` and the document would cite predictions for an arm it no
        longer proposes.
        """
        doc = (ROOT / "docs/stage3_experiment_selection.md").read_text(encoding="utf-8")
        recommendation = re.search(r"^## 3\..*?^---", doc, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(recommendation, "§3 not found")
        named = set(re.findall(r"`([a-z0-9_]+)`", recommendation.group(0))) & {
            e.experiment_id for e in EXPERIMENTS
        }
        self.assertIn(RECOMMENDED, named, "§3 must name the recommended arm")
        # ...and the headline blockquote must describe that same arm, so a
        # change of recommendation cannot leave table C generating for the old
        # one. Matched on the intervention in words, because the constant is an
        # identifier and the blockquote is prose.
        quote = " ".join(
            line[2:]
            for line in recommendation.group(0).splitlines()
            if line.startswith("> ")
        )
        self.assertTrue(quote, "§3 must open with a recommendation blockquote")
        self.assertIn("minus E2", quote, f"§3's headline must describe {RECOMMENDED}")

    def test_the_decision_tables_are_generated_for_the_recommended_arm(self) -> None:
        report = evaluate(ROOT)
        text = render_tables(report, ROOT)
        self.assertIn(f"## C. `{RECOMMENDED}`: predictions by mechanism class", text)
        # Table C must carry the usable-assay readouts and nothing weaker.
        for node in ("E_PAEP", "S_IGFBP1"):
            self.assertIn(node, text)
        committed = (ROOT / OUT_TABLES).read_text(encoding="utf-8")

        def strip(blob: str) -> list[str]:
            return [
                line
                for line in blob.splitlines()
                if not line.startswith("> **Generated file")
            ]

        self.assertEqual(
            strip(committed),
            strip(text),
            "regenerate with `pixi run build-stage3-design`",
        )

    def test_tsv_header_is_the_declared_contract(self) -> None:
        with (ROOT / OUT_TSV).open(encoding="utf-8") as fh:
            header = next(csv.reader(fh, delimiter="\t"))
        self.assertEqual(tuple(header), TSV_COLUMNS)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
