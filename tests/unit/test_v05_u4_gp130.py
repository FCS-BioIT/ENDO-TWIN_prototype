"""U4 -- the GP130/CD98 axes stay evaluation-only families, and one arm is refused.

`docs/v05_u4_gp130_axis.md` is the reasoning. U4 read Yap/Dimitriadis 2011 in
full -- the item the section-5(1) ledger called the highest-value unread one,
and the paper that was expected to decide whether TI002's rule family collapses
to a single member. It does not decide it: the paper runs no LIF comparator and
no functional endpoint, so it cannot establish that anything it measures is
IL-11-SPECIFIC, which is the entire content of the second family member.

WHAT THESE ASSERT, AND WHY EACH IS HERE.

`RefusedArmTest` is the one that matters. Yap 2011 names ANXA2, and `ANXA2` is
already the committed node `E_ANXA2_ACTIN` inside the nine-member AC01 class, so
`E_ANXA2_ACTIN = E_SECRETORY_STATE or X_IL11` would write the missing family
member and dent AC01 in a single line. It is also, measured, the largest
structural gain available on this axis -- 35 -> 37 alone and 35 -> 38 with
GP130-b, against 35 -> 37 for GP130-b by itself. A future round looking for a
cheap win will find it. What excludes it is the evidence, not the structure, and
that is exactly the kind of decision a test has to hold, because the structural
number is the visible one.

`StagedFamilyTest` pins `CD98-d` as TI001's LITERAL rule text plus the computed
answer to what its third disjunct buys: `CD98-d` differs from `CD98-b` in exactly
one setting -- embryo-conditioned signal present, hCG absent. That is the
hCG-depleted conditioned-medium control Dominguez 2010 did not run, and the
agreement between the model and the missing experiment is the deliverable.

`VerificationLedgerTest` pins that the read happened, that the rows U4 read are
still present and still say what U4 established, and that nothing was promoted on
this paper. It deliberately does NOT pin the total row count or the absence of a
`ref_id`: appending a later verified claim to this ledger, and registering a
paper that was read in full, are both legitimate and neither touches anything U4
concluded. Registration is provenance; promotion is a modelling decision on
separate criteria; U4's invariant is the second one.

`ClosedVocabularyTest` pins the TI016 re-derivation: total over the catalog,
inside the closed level set, no verdict changed, and the fragility that makes
"no verdict changed" mean something.

WHAT A FAILURE HERE MEANS. Not "loosen the test". U4's blocker is a LIF-versus-
IL11 comparison on ANXA2 or FLOT1, or an attachment endpoint under knockdown of
either, in primary human endometrial epithelium. If that evidence arrives, the
finding document changes first and cites it; these tests follow.
"""

from __future__ import annotations

import csv
import re
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.experiments.variant_discrimination import (
    NOT_STAGED,
    PAIRS,
    VARIANTS,
    discriminate,
)
from dt_adoc.reporting.coupling import (
    CouplingAdjudicationError,
    executable_target_classes,
    perturbation_separability,
)
from dt_adoc.reporting.identifiability import (
    load_identifiability,
    parse_bnd_rules,
    resolve_model,
)
from dt_adoc.reporting.structure import load_structure
from dt_adoc.reporting.target_levels import (
    LEVEL_OF_TARGET,
    LEVEL_OF_TARGET_CLASS,
    LEVELS,
    OUT_MD,
    OUT_TSV,
    build,
    rederive,
    target_levels,
)
from tests.unit.checkout_isolation import regenerate_in_shadow

GUARDED_MODELS = (
    "adoc-literature-superset-v0.4.0",
    "adoc-literature-superset-v0.5.0",
)

LEDGER = (
    ROOT
    / "context/literature/reviews"
    / "deep_research_drug_targets_2026-09-16.primary-verification.tsv"
)

#: The PDF U4 read, recorded so the read is checkable rather than asserted. The
#: library itself is gitignored and is not in this worktree, which is why the
#: digest is the record.
YAP_2011_SHA256 = "307076c46158b12a25f1cd3e103be6d6477bcc8586449b229236ed042b3241da"

CATALOG = Path(
    "models/superset/adoc-literature-superset-v0.4.0/drug_target_catalog.tsv"
)


def _measure(overrides: dict[str, str], extra_free: tuple[str, ...] = ()) -> tuple:
    """Distinct Boolean functions and AC01 size under an in-memory rule edit.

    Uses the repository's OWN exhaustive enumerator on a throwaway copy of the
    model tree, rather than a reimplementation, so the numbers the finding quotes
    are the numbers `load_structure` produces. Nothing is written to the repo.
    """
    model = GUARDED_MODELS[0]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        shutil.copytree(ROOT / "models", tmp_root / "models")
        shutil.copytree(ROOT / "config", tmp_root / "config")
        bnd = tmp_root / "models" / "superset" / model / "network.bnd"
        text = bnd.read_text(encoding="utf-8")
        for node, logic in overrides.items():
            pattern = re.compile(rf"(Node {node} \{{\n  logic = )[^;]+(;)")
            text, count = pattern.subn(
                lambda m, body=logic: m.group(1) + body + m.group(2), text
            )
            assert count == 1, f"{node} rule not found exactly once ({count})"
        for node in extra_free:
            text += f"\nNode {node} {{\n  logic = {node};\n}}\n"
        bnd.write_text(text, encoding="utf-8")
        facts = load_structure(model, tmp_root)
        distinct = len(facts.node_ids) - sum(len(c) - 1 for c in facts.alias_classes)
        ac01 = next(
            (len(c) for c in facts.alias_classes if "E_PAEP" in c and len(c) > 1), 1
        )
        return distinct, ac01


class RefusedArmTest(unittest.TestCase):
    """The IL-11-specific downstream arm is not written, in either model."""

    def test_anxa2_did_not_acquire_an_il11_arm(self) -> None:
        for model in GUARDED_MODELS:
            rules = parse_bnd_rules(resolve_model(model, ROOT).network_bnd)
            with self.subTest(model=model):
                self.assertEqual(
                    rules["E_ANXA2_ACTIN"].strip(),
                    "E_SECRETORY_STATE",
                    "E_ANXA2_ACTIN gained a determinant. Yap 2011 runs no LIF "
                    "comparator and no functional endpoint, so it cannot make "
                    "ANXA2 an IL-11-SPECIFIC executor -- which is the whole "
                    "content of TI002's second family member. Revise "
                    "docs/v05_u4_gp130_axis.md first, citing the new evidence.",
                )

    def test_no_committed_model_declares_x_il11(self) -> None:
        """`X_IL11` is an evaluation-only input and must stay out of the network."""
        for model in GUARDED_MODELS:
            rules = parse_bnd_rules(resolve_model(model, ROOT).network_bnd)
            with self.subTest(model=model):
                self.assertNotIn("X_IL11", rules)
                self.assertFalse(
                    any("X_IL11" in body for body in rules.values()),
                    "a committed rule reads X_IL11",
                )

    def test_the_refusal_is_recorded_with_its_two_reasons(self) -> None:
        """Dropped silently, this reads as a variant nobody proposed."""
        key = next(k for k in NOT_STAGED if k.startswith("GP130-d"))
        reason = NOT_STAGED[key]
        self.assertIn("NO LIF COMPARATOR", reason)
        self.assertIn("NO ADHESION OR ATTACHMENT", reason)
        self.assertIn("E_ANXA2_ACTIN", reason)
        self.assertIn("docs/v05_u4_gp130_axis.md", reason)

    def test_the_refused_arm_is_the_biggest_structural_gain_on_this_axis(self) -> None:
        """Why the refusal needs a test: the structural number favours it.

        Recomputed rather than quoted. If these move, the finding's framing --
        that the evidence, not the structure, is what excludes the arm -- is
        stale and must be revised before the numbers here are.
        """
        baseline = _measure({})
        self.assertEqual(baseline, (35, 9))
        gp130b = _measure({"E_GP130_STAT3": "E_LIF or X_IL11"}, ("X_IL11",))
        self.assertEqual(gp130b, (37, 9))
        anxa2 = _measure({"E_ANXA2_ACTIN": "E_SECRETORY_STATE or X_IL11"}, ("X_IL11",))
        self.assertEqual(anxa2, (37, 8))
        both = _measure(
            {
                "E_GP130_STAT3": "E_LIF or X_IL11",
                "E_ANXA2_ACTIN": "E_SECRETORY_STATE or X_IL11",
            },
            ("X_IL11",),
        )
        self.assertEqual(both, (38, 8))

    def test_the_staged_il11_form_dtr003_rejected_is_still_worse(self) -> None:
        """DTR003 re-measured: the staged hint enlarges the decidual class."""
        # X_IL11 = S_DECIDUALIZED, i.e. not a free input.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            shutil.copytree(ROOT / "models", tmp_root / "models")
            shutil.copytree(ROOT / "config", tmp_root / "config")
            model = GUARDED_MODELS[0]
            bnd = tmp_root / "models" / "superset" / model / "network.bnd"
            text = bnd.read_text(encoding="utf-8")
            text = re.sub(
                r"(Node E_GP130_STAT3 \{\n  logic = )[^;]+(;)",
                r"\1E_LIF or X_IL11\2",
                text,
            )
            text += "\nNode X_IL11 {\n  logic = S_DECIDUALIZED;\n}\n"
            bnd.write_text(text, encoding="utf-8")
            facts = load_structure(model, tmp_root)
            staged = len(facts.node_ids) - sum(len(c) - 1 for c in facts.alias_classes)
            decidual = next(c for c in facts.alias_classes if "S_DECIDUALIZED" in c)
        self.assertEqual(staged, 36)
        self.assertIn("X_IL11", decidual)
        self.assertEqual(len(decidual), 7)


class StagedFamilyTest(unittest.TestCase):
    """`CD98-d` is TI001's literal rule, and the computed answer it produces."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = discriminate(ROOT)
        cls.by_pair = {r["pair"]: r for r in cls.report["results"]}

    def test_cd98_d_carries_ti001s_rule_text_verbatim(self) -> None:
        variant = next(v for v in VARIANTS if v.variant_id == "CD98-d")
        self.assertEqual(
            variant.overrides["E_CD98_CD9"],
            "E_GP130_STAT3 or IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL",
        )
        self.assertEqual(variant.required_inputs, ())
        self.assertIn(("CD98-a", "CD98-d"), PAIRS)
        self.assertIn(("CD98-b", "CD98-d"), PAIRS)

    def test_the_third_disjunct_buys_exactly_one_experiment(self) -> None:
        """And it is the control the primary source did not run.

        `CD98-d` differs from `CD98-b` only where an embryo-conditioned signal is
        supplied WITHOUT hCG. Dominguez 2010 reports conditioned-medium induction
        of CD98 as data-not-shown and attributes it to the hCG the spheroids
        secrete, without testing an hCG-depleted medium -- so the one setting
        that separates the rules is the one experiment the evidence lacks.
        """
        result = self.by_pair["CD98-b vs CD98-d"]
        self.assertEqual(result["verdict"], "REQUIRES_A_NEW_CONTROLLED_INPUT")
        separating = [s for s in result["per_setting"] if s["hits"]]
        self.assertEqual(len(separating), 1)
        self.assertEqual(
            separating[0]["setting"],
            {"IN_EMBRYO_CONDITIONED_SIGNAL": True, "IN_HCG": False},
        )
        self.assertEqual({h["node"] for h in separating[0]["hits"]}, {"E_CD98_CD9"})

    def test_cd98_d_is_no_more_visible_than_v04_in_the_current_design(self) -> None:
        result = self.by_pair["CD98-a vs CD98-d"]
        current = next(s for s in result["per_setting"] if s["is_current_design"])
        self.assertEqual(current["hits"], [])
        self.assertEqual(result["verdict"], "REQUIRES_A_NEW_CONTROLLED_INPUT")

    def test_staging_a_family_member_changed_no_executable_model(self) -> None:
        """The families are evaluation-only; `rule_variants.tsv` is untouched."""
        for model in GUARDED_MODELS:
            path = ROOT / "models" / "superset" / model / "rule_variants.tsv"
            with path.open(newline="", encoding="utf-8") as handle:
                ids = {
                    row["variant_id"] for row in csv.DictReader(handle, delimiter="\t")
                }
            with self.subTest(model=model):
                self.assertNotIn("CD98-d", ids)
                self.assertNotIn("GP130-b", ids)


class PrerequisiteTest(unittest.TestCase):
    """The one standing prerequisite that names U4, checked rather than assumed."""

    #: Plan section 17: the owner question -- is the CNT arm unstimulated or
    #: E2-primed-only -- gates any v0.5 CLAIM about this node, and is still
    #: unanswered. U4 proceeds because it makes none. The single occurrence
    #: across everything U4 generates is a typing row: what the catalog calls the
    #: node and that it has its own Boolean function. No answer to the owner
    #: question could move either.
    GATED_NODE = "E_ESTROGENIC_PROLIFERATION"

    #: Everything U4 GENERATES. The finding document is deliberately not in
    #: this list: it discusses the prerequisite by name, which is the opposite
    #: of making a claim gated by it.
    GENERATED = (
        "docs/gate2_target_level_rederivation.md",
        "docs/experiments/variant_discrimination.md",
        "docs/experiments/variant_discrimination.tsv",
    )

    def test_u4_generates_no_claim_about_the_gated_node(self) -> None:
        for relative in self.GENERATED:
            with self.subTest(file=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertFalse(
                    self.GATED_NODE in text,
                    f"{relative} now mentions {self.GATED_NODE}. The owner "
                    "question that gates any claim about it is still "
                    "unanswered (plan section 17), so a new mention has to be "
                    "shown not to be a claim before this guard is relaxed.",
                )

    def test_the_one_permitted_occurrence_is_a_typing_row(self) -> None:
        with (ROOT / "docs/gate2_target_level_rederivation.tsv").open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = {r["node_id"]: r for r in csv.DictReader(handle, delimiter="\t")}
        row = rows[self.GATED_NODE]
        self.assertEqual(row["separability_free_text"], "NOT_RULE_COLLAPSED")
        self.assertEqual(row["separability_closed_vocabulary"], "NOT_RULE_COLLAPSED")
        self.assertEqual(row["changed"], "False")


class VerificationLedgerTest(unittest.TestCase):
    """The section-5(1) ledger records the read, and not a promotion."""

    #: The rows present when U4 concluded, all of which its section-5(1)
    #: reasoning reads. U4 revised the last two and appended none.
    #:
    #: This is a FLOOR, not a census. An earlier revision asserted the total row
    #: count instead, which made U4 fail on an event that says nothing about
    #: U4: a later literature-adjudication unit appending its own verified claim
    #: to this review-scoped ledger. U4 depends on these rows being present and
    #: saying what they say, not on nothing else ever being verified.
    RELIED_UPON = (
        "DTR002",
        "DTR006",
        "DTR011",
        "DTR017",
        "DTR026",
        "DTR005",
        "DTR002-followup",
    )

    @classmethod
    def setUpClass(cls) -> None:
        with LEDGER.open(newline="", encoding="utf-8") as handle:
            cls.raw = list(csv.DictReader(handle, delimiter="\t"))
        cls.rows = {row["finding_id"]: row for row in cls.raw}

    def test_every_row_u4_relied_upon_is_still_present(self) -> None:
        """Removing or re-keying one of these silently changes what U4 read."""
        missing = [f for f in self.RELIED_UPON if f not in self.rows]
        self.assertEqual(
            missing,
            [],
            f"the ledger no longer holds {missing}, which U4's section-5(1) "
            "reasoning reads. A row may be REVISED -- the assertions below say "
            "what has to survive a revision -- but a row U4 read cannot "
            "disappear without U4's record being re-derived.",
        )

    def test_finding_ids_are_unique(self) -> None:
        """`setUpClass` keys by `finding_id`. A duplicate id would silently
        replace a row U4 read and every other assertion here would still pass,
        which is the failure the old total-count assertion caught by accident.
        """
        duplicates = [
            f for f, n in Counter(r["finding_id"] for r in self.raw).items() if n > 1
        ]
        self.assertEqual(duplicates, [], f"duplicate finding_id: {duplicates}")

    def test_yap_2011_is_recorded_as_read_with_a_checkable_digest(self) -> None:
        row = self.rows["DTR002-followup"]
        self.assertNotIn("NOT YET READ", row["what_is_supported"])
        self.assertIn("FULL TEXT READ 2026-09-17", row["what_is_supported"])
        self.assertIn(YAP_2011_SHA256, row["verification_route"])

    def test_reading_it_did_not_promote_it(self) -> None:
        """The invariant is the MODELLING decision, not the curation state.

        An earlier revision also asserted that Yap 2011 stays unregistered, on
        the rationale that registration accompanies a promotion. That is not an
        invariant and must not be encoded as one: registering a reference or a
        PDF is provenance and curation, and promoting an edge, rule or node into
        canonical topology is a separate decision on separate criteria. A later
        unit may legitimately register this paper -- it was read in full, and
        recording that is good practice -- while still refusing every
        mechanistic use of it. U4 is unharmed by that and must not fail on it.

        What U4 actually established, and what has to survive, is that this
        paper does not make either candidate an IL-11-specific functional
        executor, and that nothing was promoted on it.
        """
        decision = self.rows["DTR002-followup"]["canonical_promotion_decision"]
        self.assertIn("NO PROMOTION", decision)
        self.assertIn("NOT COLLAPSED", decision.upper())
        self.assertIn("neither is shown to be IL-11-specific or functional", decision)

    def test_u4_claims_no_il11_specific_executor_anywhere_it_speaks(self) -> None:
        """The finding document is the place a specificity claim would appear
        first, so the refusal is pinned there and not only in the ledger.
        """
        finding = (ROOT / "docs/v05_u4_gp130_axis.md").read_text(encoding="utf-8")
        # Reflowed, so a line re-wrap cannot fail this for a reason that is not
        # about the claim.
        flat = " ".join(finding.split())
        self.assertIn("nothing in the paper makes either protein IL-11-specific", flat)

    def test_the_negative_is_recorded_as_a_missing_comparison(self) -> None:
        """Not as a weak result. A study with one cytokine cannot be evidence
        against ligand specificity; it is silent on it, and the difference is
        what stops a later round reading this as 'IL-11 is not specific'.
        """
        text = self.rows["DTR002-followup"]["what_is_NOT_supported"]
        self.assertIn("NO LIF COMPARATOR", text)
        self.assertIn("NO FUNCTIONAL ENDPOINT", text)

    def test_dominguez_2010_is_now_a_full_text_read(self) -> None:
        row = self.rows["DTR005"]
        self.assertIn("FULL TEXT READ 2026-09-17", row["what_is_supported"])
        self.assertIn("2026-09-17", row["confidence"])

    def test_the_embryo_conditioned_finding_is_refined_not_deleted(self) -> None:
        """DTR005 said no source names a generic embryo-conditioned inducer. The
        full text DOES report conditioned-medium induction, attributes it to hCG
        and shows no data. Both halves must survive: the route exists, and a
        generic inducer DISTINCT FROM hCG still has no support.
        """
        text = self.rows["DTR005"]["what_is_NOT_supported"]
        self.assertIn("CONDITIONED MEDIUM", text.upper())
        self.assertIn("DATA NOT SHOWN", text.upper())
        self.assertIn("DISTINCT FROM hCG", text)

    def test_ref_059_is_still_absent(self) -> None:
        """U3's section-5(1) verdict turns on the absence; U4 must not tidy it."""
        self.assertNotIn(
            "REF-059", " ".join(row["ref_id"] for row in self.rows.values())
        )


class ClosedVocabularyTest(unittest.TestCase):
    """TI016: the separability criterion re-derived on biological levels."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = rederive(GUARDED_MODELS[0], ROOT)

    def test_the_vocabulary_is_total_over_the_whole_catalog(self) -> None:
        """Not only over the executable rows the criterion reads. A catalog_only
        row promoted to executable later must not arrive untyped.
        """
        with (ROOT / CATALOG).open(newline="", encoding="utf-8") as handle:
            values = {
                row["target_class"] for row in csv.DictReader(handle, delimiter="\t")
            }
        self.assertEqual(len(values), 24)
        self.assertEqual(values - set(LEVEL_OF_TARGET_CLASS), set())

    def test_every_assignment_is_inside_the_closed_set(self) -> None:
        for level, _why in LEVEL_OF_TARGET_CLASS.values():
            self.assertIn(level, LEVELS)
        for level, _why in LEVEL_OF_TARGET.values():
            self.assertIn(level, LEVELS)
        self.assertEqual(
            set(target_levels(GUARDED_MODELS[0], ROOT).values()) - set(LEVELS), set()
        )

    def test_every_assignment_carries_a_reason(self) -> None:
        """A one-word mapping table is a relabelling, not a vocabulary."""
        for value, (_level, why) in LEVEL_OF_TARGET_CLASS.items():
            self.assertGreater(len(why), 20, value)

    def test_no_verdict_changes_under_the_closed_vocabulary(self) -> None:
        self.assertEqual(
            [r["node_id"] for r in self.report["changed"]],
            [],
            "a separability verdict moved. That is a reportable result, not a "
            "test to update: docs/gate2_target_level_rederivation.md and "
            "docs/v05_u4_gp130_axis.md section 4 both state that none does.",
        )

    def test_the_result_is_reported_with_its_fragility(self) -> None:
        """Without this, 'no verdict changed' is only as good as the mapping."""
        by_members = {c["members"]: c for c in self.report["classes"]}
        self.assertEqual(len(by_members), 5)
        barrier = by_members[("E_DAG1_FULL", "E_MUC1_BARRIER", "E_PODXL")]
        self.assertEqual(barrier["verdict"], "MERGES_SAME_TARGET_CLASS")
        self.assertEqual(barrier["relabellings_to_flip"], 1)
        gp130 = by_members[("E_CD98_CD9", "E_GP130_STAT3", "E_LIF")]
        self.assertEqual(gp130["verdict"], "MERGES_DISTINCT_TARGET_CLASSES")
        self.assertEqual(gp130["relabellings_to_flip"], 2)
        ac01 = max(by_members, key=len)
        self.assertEqual(len(ac01), 6)
        self.assertEqual(by_members[ac01]["relabellings_to_flip"], 5)

    def test_the_criterion_reads_fewer_rows_than_the_catalog_defect_counts(
        self,
    ) -> None:
        """DTR020's 34/24 is a catalog statement; 29/21 is the exposure."""
        self.assertEqual(self.report["executable_targets"], 29)
        self.assertEqual(len(self.report["free_text_values"]), 21)

    def test_an_incomplete_override_raises_rather_than_understating_a_merge(
        self,
    ) -> None:
        """A target dropped from the override would read NOT_A_CATALOGUED_TARGET,
        which understates the merge instead of failing.
        """
        facts = load_identifiability(GUARDED_MODELS[0], ROOT)
        classes = {n: members for members in facts.global_classes for n in members}
        partial = dict(target_levels(GUARDED_MODELS[0], ROOT))
        partial.pop("E_LIF")
        with self.assertRaises(CouplingAdjudicationError):
            perturbation_separability(
                facts.node_ids,
                classes,
                GUARDED_MODELS[0],
                ROOT,
                target_class=partial,
            )

    def test_the_catalog_itself_was_not_rewritten_to_get_this_answer(self) -> None:
        """The free-text typing is still what the committed catalog says."""
        classes = executable_target_classes(GUARDED_MODELS[0], ROOT)
        self.assertEqual(classes["E_LIF"], "ligand")
        self.assertEqual(classes["E_GP130_STAT3"], "pathway_state")
        self.assertEqual(
            Counter(classes.values())["anti_adhesive_surface"],
            3,
            "the barrier trio's shared free-text label is the demonstration "
            "DTR020 rests on; it must stay in the catalog, not be repaired here",
        )

    def test_regenerating_reproduces_the_committed_outputs(self) -> None:
        produced = regenerate_in_shadow(build, (OUT_MD, OUT_TSV))
        for relative, content in produced.items():
            self.assertEqual((ROOT / relative).read_bytes(), content, str(relative))


if __name__ == "__main__":
    unittest.main()
