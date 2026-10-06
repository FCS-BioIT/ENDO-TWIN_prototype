"""What the design-alias figure is allowed to colour, and why it is not hand-drawn.

The figure's whole claim is that a colour is *computed*. A palette assigned by
hand would look identical and mean nothing, so the tests that matter here are
not the ones checking a total -- a broken pipeline can land on 19 -- but the ones
checking the derivation:

* the partition comes from the same enumerator ``identifiability.py`` uses, and
  is pinned by reproducing its result exactly on the recorded arms;
* the categories come from model properties, not from node-name prefixes;
* the colours come from the partition, in an order the partition fixes;
* the committed artifacts still match the model they were drawn from.

Unit tests: no MaBoSS, no simulation, no horizon, no seed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting.design_alias import (
    CATEGORY_ORDER,
    _Enumerator,
    candidate_fifth_arms,
    design_alias_summary,
    load_design_alias,
    load_plan,
)
from dt_adoc.reporting.design_alias_figure import (
    CLASS_HUES,
    NEUTRAL_FILL,
    assign_class_colors,
)
from dt_adoc.reporting.identifiability import (
    load_identifiability,
)

SUPERSET = "adoc-literature-superset-v0.4.0"
TABLES = ROOT / "docs" / "design_alias"
METADATA = TABLES / "design_alias_metadata.json"
NODE_TABLE = TABLES / "node_design_classes.tsv"
CANDIDATE_TABLE = TABLES / "candidate_fifth_arms.tsv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class PartitionDerivationTest(unittest.TestCase):
    """The partition is the canonical one, not a second implementation of it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.recorded = load_identifiability(SUPERSET, ROOT)
        cls.facts = load_design_alias(ROOT, facts=cls.recorded)
        cls.enumerator = _Enumerator(SUPERSET, ROOT)

    def test_the_enumerator_reproduces_identifiability_on_the_recorded_arms(
        self,
    ) -> None:
        """The pin on reuse.

        Handed the six arms ``identifiability.py`` reconstructs from the
        observation tables, this module's enumerator must return that module's
        ``design_classes`` exactly. If the two ever diverge, one of them has
        drifted from the model, and the figure would still render.
        """
        assignments = [
            self.enumerator.inputs_for(arm.arm_id) for arm in self.recorded.arms
        ]
        self.assertEqual(
            set(self.enumerator.partition(assignments)),
            set(self.recorded.design_classes),
        )

    def test_the_plan_is_not_the_recorded_design(self) -> None:
        """The reason this module exists, asserted rather than assumed.

        The plan adds an anti-SPP1 arm the repository has never run and drops
        the E2-priming arm it has, so the two partitions have the same *count*
        and different *members*. A test on the count alone would pass while the
        figure described the wrong design.
        """
        self.assertEqual(
            len(self.facts.design_classes), len(self.recorded.design_classes)
        )
        self.assertNotEqual(
            set(self.facts.design_classes), set(self.recorded.design_classes)
        )
        self.assertEqual(self.facts.recorded_not_planned, ("e2_primed_maternal",))

    def test_every_design_class_is_a_union_of_global_classes(self) -> None:
        """P_global refines P_design; the figure's two encodings must nest.

        If a design class ever cut across a global class, "heavy border = the
        rules merged it" would be false for some node inside a fill colour, and
        the border and the fill would be telling contradictory stories.
        """
        for members in self.facts.design_classes:
            for node_id in members:
                self.assertLessEqual(
                    set(self.facts.global_class_of[node_id]),
                    set(members),
                    f"{node_id}'s Boolean-function class escapes its design class",
                )

    def test_the_partition_responds_to_the_arm_set(self) -> None:
        """A partition that ignored its arms would still colour the figure.

        Dropping the mifepristone arm must coarsen the partition. This is the
        cheapest possible falsification of "the classes are hard-coded".
        """
        stems = [s for s in self.facts.cfg_stems if "mifepristone" not in s]
        coarser = self.enumerator.partition(
            [self.enumerator.inputs_for(s) for s in stems]
        )
        self.assertLess(len(coarser), len(self.facts.design_classes))


class CategoryDerivationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.recorded = load_identifiability(SUPERSET, ROOT)
        cls.facts = load_design_alias(ROOT, facts=cls.recorded)

    def test_placeholders_are_not_selected_by_their_name(self) -> None:
        """``X_`` is a naming convention, not the property being drawn.

        Several ``X_`` nodes are ordinary derived nodes -- the interface routes,
        the permissive-ECM state, free lumen SPP1. Selecting placeholders by
        prefix would hatch them and tell the reader that quantities the design
        does determine are unknowable.

        The difference is asserted against the property that actually defines a
        placeholder -- being a latent free variable -- rather than against a
        list of names, so renaming a node cannot make this test pass wrongly.
        """
        placeholders = {
            n for n, c in self.facts.category.items() if c == "interface_placeholder"
        }
        prefixed = {n for n in self.facts.node_ids if n.startswith("X_")}
        self.assertTrue(placeholders < prefixed, "prefix and category coincide")
        self.assertEqual(
            prefixed - placeholders,
            prefixed - set(self.recorded.latent),
            "an X_-prefixed node is categorised on something other than latency",
        )
        self.assertGreaterEqual(len(prefixed - placeholders), 2)

    def test_placeholders_are_exactly_the_latent_nodes_with_no_assay_target(
        self,
    ) -> None:
        assayable = set(self.recorded.assayable)
        self.assertEqual(
            {n for n, c in self.facts.category.items() if c == "interface_placeholder"},
            {n for n in self.recorded.latent if n not in assayable},
        )

    def test_every_latent_variable_is_categorised_as_latent(self) -> None:
        """A latent node must never be drawn as resolved.

        Its value is unknown in every arm, so a neutral "already separated"
        fill would invert the finding. Precedence in ``_categorise`` is what
        prevents it, and this is the test of that precedence.
        """
        for node_id in self.recorded.latent:
            self.assertIn(
                self.facts.category[node_id],
                {"interface_placeholder", "latent_biological"},
            )

    def test_every_node_gets_exactly_one_known_category(self) -> None:
        self.assertEqual(set(self.facts.category), set(self.facts.node_ids))
        self.assertTrue(set(self.facts.category.values()) <= set(CATEGORY_ORDER))


class ColorDerivationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_design_alias(ROOT)

    def test_colors_are_assigned_from_the_partition_in_a_fixed_order(self) -> None:
        fills, borders = assign_class_colors(self.facts)
        ranked = sorted(
            (c for c in self.facts.design_classes if len(c) > 1),
            key=lambda c: (-len(c), min(c)),
        )
        self.assertEqual(list(fills), ranked)
        for index, members in enumerate(ranked):
            self.assertEqual(borders[members], CLASS_HUES[index])

    def test_only_multi_member_classes_are_coloured(self) -> None:
        """A singleton is not a finding and must stay neutral."""
        fills, _borders = assign_class_colors(self.facts)
        for members in self.facts.design_classes:
            if len(members) == 1:
                self.assertNotIn(members, fills)

    def test_no_node_identifier_is_hard_coded_in_the_figure_module(self) -> None:
        """The strongest available check that the drawing is not hand-made.

        Every class membership must arrive from the analysis. A model node id
        appearing as a literal in the figure module would mean some part of the
        picture was decided before the model was read. The analysis module is
        held to the same rule; only the two files' own doc prose is exempt,
        which is why the check runs on code lines rather than on the whole file.
        """
        node_ids = set(self.facts.node_ids)
        for relative in (
            "src/dt_adoc/reporting/design_alias_figure.py",
            "src/dt_adoc/reporting/design_alias.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            # Strip docstrings and comments: the prose names nodes on purpose.
            code = "\n".join(
                line.split("#")[0]
                for line in source.splitlines()
                if not line.lstrip().startswith("#")
            )
            for chunk in code.split('"""')[::2]:
                for node_id in node_ids:
                    self.assertNotIn(
                        f'"{node_id}"',
                        chunk,
                        f"{relative} hard-codes the model node {node_id}",
                    )


class PlanIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, cls.arms = load_plan(ROOT)
        cls.facts = load_design_alias(ROOT)

    def test_every_planned_cfg_exists_in_the_model(self) -> None:
        conditions = (
            ROOT / "models" / "superset" / self.document["model_version"] / "conditions"
        )
        for arm in self.arms:
            for _phase, stem in arm.cfgs:
                self.assertTrue((conditions / f"{stem}.cfg").exists(), stem)

    def test_the_anti_spp1_arm_is_planned_but_carries_no_recorded_observation(
        self,
    ) -> None:
        """The flag the brief asked for, asserted so it cannot quietly lapse.

        The plan's fourth arm exists in the model as a condition cfg and has
        never been run: no artifact in the repository records an observation in
        it. Counting it as data in hand would credit the design with excitation
        it never applied.
        """
        planned = {arm.arm_id: arm for arm in self.arms}
        self.assertFalse(planned["hormone_treated_anti_spp1"].has_recorded_observation)
        self.assertIn("hormone_treated_anti_spp1", self.facts.planned_not_recorded)
        for arm_id in ("untreated_control", "hormone_treated"):
            self.assertTrue(planned[arm_id].has_recorded_observation, arm_id)

    def test_the_plan_cannot_be_read_as_a_prospective_selection(self) -> None:
        """The plan names anti-SPP1. Naming it must confer nothing.

        Gate 6 chooses the embryo-challenge arm AFTER the maternal-phase panel,
        with no molecule privileged in advance. A config that lists anti-SPP1 as
        arm four is the easiest thing in this repository to misread as that
        choice already made, so the file declares its role and the loader
        refuses any other.
        """
        from dt_adoc.reporting.design_alias import PLAN_ROLE

        self.assertEqual(self.document["role"], PLAN_ROLE)
        self.assertIn("not_a_prospective_selection", PLAN_ROLE)

    def test_a_repurposed_plan_file_is_refused(self) -> None:
        """The role check must bite, or it is a comment with a colon in it."""
        import shutil
        import tempfile

        import yaml as _yaml

        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "repo"
            sandbox.mkdir()
            for relative in ("models", "config"):
                shutil.copytree(ROOT / relative, sandbox / relative)
            target = sandbox / "config" / "planned_design.yaml"
            document = _yaml.safe_load(target.read_text(encoding="utf-8"))
            document["role"] = "prospective_arm_selection"
            target.write_text(_yaml.safe_dump(document), encoding="utf-8")
            with self.assertRaises(ValueError) as caught:
                load_plan(sandbox)
            self.assertIn("never a prospective-arm selection", str(caught.exception))

    def test_the_named_fourth_arm_is_flagged_where_it_is_declared(self) -> None:
        """Belt and braces on the one arm most likely to be misquoted."""
        import yaml as _yaml

        document = _yaml.safe_load(
            (ROOT / "config" / "planned_design.yaml").read_text(encoding="utf-8")
        )
        entry = next(
            a for a in document["arms"] if a["arm_id"] == "hormone_treated_anti_spp1"
        )
        self.assertTrue(entry.get("not_a_prospective_selection"))

    def test_recorded_observation_is_derived_and_not_declared(self) -> None:
        """The config may declare the plan; it may not declare the evidence."""
        text = (ROOT / "config" / "planned_design.yaml").read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.split("#")[0].strip()
            self.assertFalse(
                stripped.startswith("has_recorded_observation"),
                "planned_design.yaml must not declare what the observation "
                "tables decide",
            )


class CandidateArmTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_design_alias(ROOT)
        cls.enumerator = _Enumerator(SUPERSET, ROOT)
        cls.candidates = candidate_fifth_arms(
            cls.facts, ROOT, enumerator=cls.enumerator
        )
        cls.summary = design_alias_summary(cls.facts, cls.candidates)

    def test_a_matched_committed_cfg_has_the_identical_input_assignment(self) -> None:
        """``committed_cfg`` must mean the cfg, not a cfg with a similar name."""
        for candidate in self.candidates:
            if not candidate.committed_cfg:
                continue
            reference = self.enumerator.inputs_for(candidate.committed_cfg)
            for node_id in self.enumerator.inputs:
                self.assertEqual(
                    candidate.inputs.get(node_id, False),
                    reference.get(node_id, False),
                    f"{candidate.candidate_id} claims {candidate.committed_cfg}",
                )

    def test_the_anti_spp1_arm_is_not_offered_as_a_fifth_arm(self) -> None:
        """It is already the plan's fourth arm; proposing it again is a bug.

        The plan *isolates* ``IN_ANTI_SPP1`` -- the one resolution it buys over
        the recorded design, which never moves that input at all. A candidate
        generator scored against the recorded design would still offer it.

        It is isolated and not attributable: neither anti-SPP1 cfg carries a
        recorded observation, so no measured quantity exists whose change could
        be attributed to the input. ``AttributionTest`` holds that distinction;
        what matters here is only that an input the plan already moves is not
        offered again as something to add.
        """
        self.assertIn("IN_ANTI_SPP1", self.facts.set_alone_no_shared_readout)
        self.assertNotIn("IN_ANTI_SPP1", self.facts.unexcited_inputs)
        self.assertEqual(
            [c for c in self.candidates if "ANTI_SPP1" in c.candidate_id], []
        )

    def test_gain_is_the_difference_the_partition_actually_makes(self) -> None:
        baseline = len(self.facts.design_classes)
        for candidate in self.candidates:
            self.assertEqual(candidate.baseline_classes, baseline)
            recomputed = self.enumerator.partition(
                [self.enumerator.inputs_for(s) for s in self.facts.cfg_stems]
                + [candidate.inputs]
            )
            self.assertEqual(candidate.classes_after, len(recomputed))
            self.assertEqual(candidate.gain, len(recomputed) - baseline)

    def test_the_largest_gain_separates_no_two_measured_analytes(self) -> None:
        """The finding the brief did not expect, pinned so a re-run must restate it.

        HAND2 loss is the best fifth arm by design-class gain and it is the
        wrong answer to "which arm helps the measurements": it leaves E_PAEP and
        S_IGFBP1 in one class. Only de-bundling the hormone cocktail separates
        them, and no committed cfg expresses that arm.
        """
        best = [
            c for c in self.candidates if c.gain == self.summary["best_fifth_arm_gain"]
        ]
        self.assertTrue(all("HAND2_LOSS" in c.candidate_id for c in best))
        for candidate in best:
            self.assertEqual(candidate.separated_measured_pairs, ())

        separating = [c for c in self.candidates if c.separated_measured_pairs]
        self.assertTrue(separating)
        self.assertTrue(
            all(
                c.candidate_id.startswith(("dropout_IN_E2", "dropout_IN_cAMP"))
                for c in separating
            )
        )
        self.assertTrue(
            all(not c.committed_cfg for c in separating),
            "an arm that separates the measured analytes now has a cfg; "
            "re-read docs/design_alias_note.md before trusting its recommendation",
        )

    def test_measured_pairs_are_read_from_the_observation_tables(self) -> None:
        recorded = load_identifiability(SUPERSET, ROOT)
        self.assertEqual(self.facts.measured_nodes, recorded.measured_nodes)
        for candidate in self.candidates:
            for left, right in candidate.separated_measured_pairs:
                self.assertIn(left, recorded.measured_nodes)
                self.assertIn(right, recorded.measured_nodes)


class AttributionTest(unittest.TestCase):
    """Isolating an input is not the same as being able to read its effect."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_design_alias(ROOT)

    def test_mifepristone_is_attributable_and_anti_spp1_is_not(self) -> None:
        """The distinction a hardcoded empty readout set would have erased.

        An earlier version built the plan's arms with ``measured=()``, which
        made ``independently_perturbed`` empty for every conceivable plan and
        published the false claim that no pair of planned arms shares a readout.
        Two of this plan's own cfgs differ in ``IN_MIFEPRISTONE`` alone and both
        carry a recorded ``OUT_STABLE_ADHESION`` observation, so that contrast
        is attributable; the anti-SPP1 arm carries no observation at all, so its
        input is isolated and unreadable. The test asserts the difference, not
        either half, because a construction artefact would flatten it.
        """
        self.assertEqual(self.facts.independently_perturbed, ("IN_MIFEPRISTONE",))
        self.assertEqual(self.facts.set_alone_no_shared_readout, ("IN_ANTI_SPP1",))

    def test_the_planned_arms_carry_the_observations_the_repository_records(
        self,
    ) -> None:
        """The readouts must come from the observation tables, not from nothing."""
        recorded = load_identifiability(SUPERSET, ROOT)
        by_arm = {arm.arm_id: arm for arm in recorded.arms}
        for arm in self.facts.arms:
            for _phase, stem in arm.cfgs:
                if stem in by_arm:
                    self.assertTrue(
                        arm.has_recorded_observation,
                        f"{stem} carries a recorded observation but the plan "
                        "reports the arm as unobserved",
                    )


class VariantTest(unittest.TestCase):
    """A non-default variant must be checkable without corrupting the default."""

    def test_the_variant_writes_its_own_artifacts(self) -> None:
        """The silent-staleness failure this repository has already had once.

        An earlier version applied the variant suffix to the figures and the
        metadata but not to the tables, so rendering the documented
        ``--variant`` run replaced the as-declared tables with
        maternal-phase-only content while leaving the as-declared figures and
        their recorded hashes in place.
        """
        for stem in (
            "node_design_classes",
            "planned_arms",
            "candidate_fifth_arms",
        ):
            self.assertTrue((TABLES / f"{stem}.tsv").exists(), stem)
            self.assertTrue((TABLES / f"{stem}_maternal_phase_only.tsv").exists(), stem)
            self.assertNotEqual(
                (TABLES / f"{stem}.tsv").read_bytes(),
                (TABLES / f"{stem}_maternal_phase_only.tsv").read_bytes(),
                f"{stem}: the variant table is identical to the default one",
            )

    def test_the_variant_reproduces_the_numbers_the_note_states(self) -> None:
        facts = load_design_alias(ROOT, variant="maternal_phase_only")
        enumerator = _Enumerator(SUPERSET, ROOT)
        candidates = candidate_fifth_arms(facts, ROOT, enumerator=enumerator)
        summary = design_alias_summary(facts, candidates)
        self.assertEqual(summary["design_effective_states"], 17)
        self.assertEqual(summary["best_fifth_arm_gain"], 5)
        self.assertTrue(
            all("HAND2_LOSS" in a for a in summary["best_fifth_arms"]),
        )
        self.assertEqual(summary["best_gain_among_arms_separating_measured_nodes"], 3)

    def test_the_variant_uses_fewer_cfgs_and_resolves_no_more(self) -> None:
        """Dropping the challenge phase may only coarsen the partition."""
        declared = load_design_alias(ROOT)
        variant = load_design_alias(ROOT, variant="maternal_phase_only")
        self.assertLess(len(variant.cfg_stems), len(declared.cfg_stems))
        self.assertLessEqual(len(variant.design_classes), len(declared.design_classes))


class ShortlistTest(unittest.TestCase):
    """Figure B draws one bar per distinct experiment, not per distinct name."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = load_design_alias(ROOT)
        cls.candidates = candidate_fifth_arms(
            cls.facts, ROOT, enumerator=_Enumerator(SUPERSET, ROOT)
        )

    def test_candidates_sharing_a_bar_produce_the_identical_refinement(
        self,
    ) -> None:
        """De-duplication must not merge arms that do different things.

        Keying on the set of classes *touched* was tried and is wrong: six of
        the eight such keys collapse candidates that refine those classes
        differently, and the measured-analyte verdict is not constant within
        such a key -- so a bar could carry its representative's "separates two
        measured analytes" marker while a sibling folded into it separates
        nothing.
        """
        from dt_adoc.reporting.design_alias_figure import _shortlist

        def refinement(candidate) -> tuple:
            return tuple(
                sorted(
                    tuple(sorted(part))
                    for _before, parts in candidate.splits
                    for part in parts
                )
            )

        shortlist = _shortlist(self.candidates)
        by_refinement: dict[tuple, list] = {}
        for candidate in self.candidates:
            if candidate.gain > 0:
                by_refinement.setdefault(refinement(candidate), []).append(candidate)

        for group in by_refinement.values():
            verdicts = {bool(c.separated_measured_pairs) for c in group}
            self.assertEqual(len(verdicts), 1)
            self.assertEqual(len({c.gain for c in group}), 1)

        self.assertEqual(
            len({refinement(c) for c in shortlist}),
            len(shortlist),
            "two bars in Figure B draw the same refinement",
        )

    def test_the_shortlist_prefers_an_arm_the_model_can_already_express(
        self,
    ) -> None:
        """Among arms doing the identical thing, draw the runnable one.

        A sibling is an arm producing the *same refinement*, which is the
        de-duplication key. Arms that touch the same classes but refine them
        differently are different experiments and get their own bars, so they
        are not siblings and one may legitimately need a new cfg while the
        other does not.
        """
        from dt_adoc.reporting.design_alias_figure import _shortlist

        def refinement(candidate) -> tuple:
            return tuple(
                sorted(
                    tuple(sorted(part))
                    for _before, parts in candidate.splits
                    for part in parts
                )
            )

        for drawn in _shortlist(self.candidates):
            siblings = [
                c for c in self.candidates if refinement(c) == refinement(drawn)
            ]
            if any(c.committed_cfg for c in siblings):
                self.assertTrue(
                    drawn.committed_cfg,
                    f"{drawn.candidate_id} is drawn though a committed-cfg "
                    "arm producing the same refinement exists",
                )


class CommittedArtifactTest(unittest.TestCase):
    """The staleness guard: the artifacts must match the model on disk.

    ``tests/unit/test_concordance.py`` exists because a figure and its source
    data disagreed through a merge and a green suite. The same guard is applied
    here rather than trusted not to be needed.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = json.loads(METADATA.read_text(encoding="utf-8"))
        cls.provenance = cls.metadata["provenance"]

    def test_the_model_has_not_moved_since_the_figures_were_drawn(self) -> None:
        model = ROOT / "models" / "superset" / self.provenance["model_version"]
        for key, path in (
            ("network_bnd_sha256", model / "network.bnd"),
            ("baseline_cfg_sha256", model / "baseline.cfg"),
            ("node_dictionary_sha256", model / "node_dictionary.tsv"),
            ("planned_design_yaml_sha256", ROOT / "config" / "planned_design.yaml"),
            ("visualization_yaml_sha256", ROOT / "config" / "visualization.yaml"),
        ):
            self.assertEqual(
                self.provenance[key],
                hashlib.sha256(path.read_bytes()).hexdigest(),
                f"{path.name} changed since the design-alias figures were drawn; "
                "run `pixi run render-design-alias` and commit the result",
            )

    def test_the_condition_set_recorded_is_the_condition_set_on_disk(self) -> None:
        """A condition added later changes what a candidate ranking means."""
        conditions = (
            ROOT
            / "models"
            / "superset"
            / self.provenance["model_version"]
            / "conditions"
        )
        recorded = self.provenance["condition_cfg_sha256"]
        self.assertEqual(set(recorded), {p.name for p in conditions.glob("*.cfg")})
        for name, digest in recorded.items():
            self.assertEqual(
                digest, hashlib.sha256((conditions / name).read_bytes()).hexdigest()
            )

    def test_the_implementation_digest_recomputes(self) -> None:
        digest = hashlib.sha256()
        for relative in self.provenance["implementation_files"]:
            digest.update(relative.encode("utf-8"))
            path = ROOT / relative
            digest.update(
                hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii")
                if path.is_file()
                else b"absent"
            )
        self.assertEqual(self.provenance["implementation_digest"], digest.hexdigest())

    def test_every_recorded_artifact_hash_matches_the_committed_file(self) -> None:
        for entry in self.metadata["figures"] + self.metadata["tables"]:
            path = ROOT / entry["path"]
            self.assertTrue(path.exists(), entry["path"])
            self.assertEqual(
                entry["sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
                f"{entry['path']} has changed since the metadata was written",
            )

    def test_the_node_table_agrees_with_a_fresh_computation(self) -> None:
        """The table is the figure in text; the two must not drift apart."""
        facts = load_design_alias(ROOT)
        rows = {row["node_id"]: row for row in _rows(NODE_TABLE)}
        self.assertEqual(set(rows), set(facts.node_ids))
        for node_id, row in rows.items():
            self.assertEqual(row["category"], facts.category[node_id])
            self.assertEqual(
                row["design_class_members"],
                ";".join(sorted(facts.design_class_of[node_id])),
            )
            self.assertEqual(
                row["global_class_members"],
                ";".join(sorted(facts.global_class_of[node_id])),
            )
            self.assertEqual(
                row["structurally_aliased"],
                "true" if len(facts.global_class_of[node_id]) > 1 else "false",
            )

    def test_the_node_table_colour_column_matches_the_palette(self) -> None:
        """A reader recolouring the figure from the TSV must get the figure."""
        facts = load_design_alias(ROOT)
        fills, _borders = assign_class_colors(facts)
        for row in _rows(NODE_TABLE):
            expected = fills.get(facts.design_class_of[row["node_id"]], NEUTRAL_FILL)
            self.assertEqual(row["fill_color"], expected, row["node_id"])

    def test_the_candidate_table_carries_the_measured_pair_verdict(self) -> None:
        rows = _rows(CANDIDATE_TABLE)
        self.assertTrue(rows)
        self.assertIn("separates_measured_nodes", rows[0])
        flagged = [r for r in rows if r["separates_measured_nodes"] == "true"]
        self.assertTrue(flagged)
        for row in flagged:
            self.assertNotEqual(row["measured_pairs_separated"], "(none)")
            for pair in row["measured_pairs_separated"].split(";"):
                left, right = pair.split("|")
                self.assertLess(
                    left,
                    right,
                    "measured pairs must be sorted within the pair, or the "
                    "same separation appears twice under two spellings",
                )


class ReproducibilityTest(unittest.TestCase):
    def test_rendering_twice_produces_byte_identical_artifacts(self) -> None:
        """A hash that changes on every run certifies nothing.

        Rendered into a scratch copy of the repository rather than over the
        committed artifacts, so a failing run cannot leave the working tree
        holding half-written figures.
        """
        from dt_adoc.reporting.design_alias_figure import (
            render_design_alias_artifact,
        )

        with tempfile.TemporaryDirectory() as scratch:
            sandbox = Path(scratch) / "repo"
            sandbox.mkdir()
            for relative in ("models", "config", "src"):
                shutil.copytree(ROOT / relative, sandbox / relative)
            (sandbox / "docs" / "assets").mkdir(parents=True)

            first = render_design_alias_artifact(root=sandbox)
            digests = {
                entry["path"]: entry["sha256"]
                for entry in first["figures"] + first["tables"]
            }
            second = render_design_alias_artifact(root=sandbox)
            for entry in second["figures"] + second["tables"]:
                self.assertEqual(
                    digests[entry["path"]],
                    entry["sha256"],
                    f"{entry['path']} is not reproducible across runs",
                )

    # REACHABILITY OF THE RECORDED COMMIT IS DELIBERATELY NOT ASSERTED.
    #
    # An earlier revision of this module required
    # `git merge-base --is-ancestor <recorded commit> HEAD`. That invariant was
    # removed from `tests/unit/test_concordance.py` for a reason that applies
    # here unchanged and is restated rather than rediscovered: ancestry is a
    # property of whichever checkout happens to be looking, not of the artifact.
    # Strict judging fails wherever history is absent; skipping lets an orphaned
    # stamp pass; and a repository gate cannot pass in a reviewing checkout whose
    # HEAD is a synthetic commit of the tree, which is exactly how this
    # repository's independent review runs. The error was the invariant, not its
    # implementation.
    #
    # What carries the reconstructability the lineage contract asks for is
    # CONTENT: `implementation_digest` over the code that drew these figures,
    # plus the `network.bnd`, `baseline.cfg`, node-dictionary, per-condition,
    # `planned_design.yaml` and `visualization.yaml` hashes, and the sha256 of
    # every emitted artifact. All of those are verified above, and they hold in
    # any environment. The commit is still recorded; it is simply not judged
    # against a tree it was never generated from.

    def test_the_recorded_commit_is_present_and_well_formed(self) -> None:
        """Recorded, and recorded properly -- but not judged for reachability.

        A blank or truncated field would mean the provenance block was written
        without one, which is a defect in the renderer. Whether the commit is
        reachable from the reader's HEAD is not a question about this artifact.
        """
        metadata = json.loads(METADATA.read_text(encoding="utf-8"))
        commit = metadata["provenance"]["git_commit"]
        if not commit:
            self.skipTest("no git commit recorded; rendered outside a work tree")
        self.assertRegex(commit, r"\A[0-9a-f]{40}\Z")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
