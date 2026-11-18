"""The per-edge evidence summary, on synthetic evidence sets.

The summary describes an edge's evidence; it does not grade it. That boundary
is the thing under test, because the version this replaced *looked* like a
grade: it emitted `contradicted` whenever any examined row carried
`edge_support='contradictory'`, with no regard for the credibility bar in
section 7.1 of docs/evidence_grading.md, no weighing against positive evidence,
no `contested` outcome and no curation-completeness label. Strong positive
evidence beside one weak contradictory observation came out as a contradicted
edge.

Every case below is constructed rather than drawn from the live table. The
table holds 38 graded rows out of 276 and not one contradiction, so a test
written against it would be a test against one thin sample and would pass
whatever the contradiction logic did.
"""

from __future__ import annotations

import unittest

from dt_adoc.evidence.coverage import (
    COVERAGE_STATES,
    CREDIBLE_CONTRADICTION_STRENGTHS,
    FilterRefused,
    edge_evidence_summary,
    refuse_filter_if_premature,
    summarize_rows_by_edge,
)


def piece(
    identifier: str,
    *,
    edge: str = "LE001",
    support: str = "partial",
    confidence: str = "medium",
    strength: str = "moderate",
    relevance: str = "close",
    status: str = "provisional",
    group: str = "REF-001",
) -> dict[str, str]:
    return {
        "evidence_piece_id": identifier,
        "edge_id": edge,
        "edge_support": support,
        "overall_confidence": confidence,
        "experimental_strength": strength,
        "human_ADOC_relevance": relevance,
        "curation_status": status,
        "independence_group": group,
    }


def unreviewed(identifier: str, *, edge: str = "LE001") -> dict[str, str]:
    return piece(
        identifier,
        edge=edge,
        support="unassessed",
        confidence="unassessed",
        strength="unassessed",
        relevance="unassessed",
        status="unreviewed",
    )


def summarize(*rows: dict[str, str]):
    return summarize_rows_by_edge(list(rows))["LE001"]


class NoGradeIsEmitted(unittest.TestCase):
    """The regression this module exists for."""

    def test_the_summary_has_no_field_that_is_a_grade(self) -> None:
        """Pinned as an exact set rather than a blocklist of names. A
        blocklist passes a field called `edge_verdict` holding a grade; this
        fails on any new field at all, which is the point -- adding one to
        this dataclass should be a decision, not a drift."""
        self.assertEqual(
            set(summarize(piece("A")).__dataclass_fields__),
            {
                "edge_id",
                "coverage",
                "curation_completeness",
                "supporting_pieces",
                "best_supporting_confidence",
                "independent_supporting_groups",
                "any_supporting_verified",
                "contradictions",
                "not_demonstrated_pieces",
                "unreviewed_pieces",
            },
        )

    def test_no_field_ever_holds_a_grade_vocabulary_value(self) -> None:
        """`best_supporting_confidence` reports the best *piece* confidence and
        is allowed to be one of these; nothing else may be."""
        grades = {"high", "medium", "low", "unsupported", "contradicted", "contested"}
        result = summarize(
            piece("A", support="direct", confidence="medium", strength="strong"),
            piece(
                "B",
                support="contradictory",
                confidence="unsupported",
                strength="strong",
                group="REF-002",
            ),
        )
        for name in result.__dataclass_fields__:
            if name == "best_supporting_confidence":
                continue
            value = getattr(result, name)
            with self.subTest(field=name):
                self.assertNotIn(value, grades)

    def test_strong_support_with_a_weak_contradiction_is_not_overturned(self) -> None:
        """Case 1. The old implementation called this `contradicted`."""
        result = summarize(
            piece("A", support="direct", confidence="medium", strength="strong"),
            piece(
                "B",
                support="contradictory",
                confidence="unsupported",
                strength="weak",
                group="REF-002",
            ),
        )
        self.assertEqual(result.supporting_pieces, ("A",))
        self.assertEqual(len(result.contradictions), 1)
        self.assertEqual(result.credible_contradictions, ())
        self.assertTrue(result.competing_positive_evidence)
        self.assertEqual(result.best_supporting_confidence, "medium")

    def test_a_credible_contradiction_is_reported_as_credible(self) -> None:
        """Case 2. Medium support, strong credible contradiction. Both are
        reported; which wins is section 7.1's job, not this function's."""
        result = summarize(
            piece("A", support="partial", confidence="medium", strength="moderate"),
            piece(
                "B",
                support="contradictory",
                confidence="unsupported",
                strength="strong",
                relevance="direct",
                group="REF-002",
            ),
        )
        self.assertEqual(len(result.credible_contradictions), 1)
        self.assertEqual(result.credible_contradictions[0].weight, "high")
        self.assertTrue(result.competing_positive_evidence)

    def test_strong_support_and_strong_contradiction_are_both_kept(self) -> None:
        """Case 3. Nothing is discarded to produce a tidy answer."""
        result = summarize(
            piece(
                "A",
                support="direct",
                confidence="medium",
                strength="strong",
                relevance="direct",
            ),
            piece(
                "B",
                support="contradictory",
                confidence="unsupported",
                strength="strong",
                relevance="direct",
                group="REF-002",
            ),
        )
        self.assertEqual(result.supporting_pieces, ("A",))
        self.assertEqual(len(result.credible_contradictions), 1)
        self.assertTrue(result.competing_positive_evidence)

    def test_a_contradiction_with_no_support_has_no_competing_evidence(self) -> None:
        """Case 4."""
        result = summarize(
            piece(
                "B",
                support="contradictory",
                confidence="unsupported",
                strength="strong",
            )
        )
        self.assertEqual(result.supporting_pieces, ())
        self.assertFalse(result.competing_positive_evidence)
        self.assertEqual(len(result.credible_contradictions), 1)
        self.assertEqual(result.best_supporting_confidence, "unassessed")


class NotDemonstratedIsNotContradiction(unittest.TestCase):
    """The distinction the brief insists must never be conflated."""

    def test_not_demonstrated_is_kept_apart_from_contradiction(self) -> None:
        """Case 5. A citation that does not test the edge is not evidence
        against it."""
        result = summarize(
            piece(
                "A",
                support="not_demonstrated",
                confidence="unsupported",
                strength="insufficient",
            )
        )
        self.assertEqual(result.not_demonstrated_pieces, ("A",))
        self.assertEqual(result.contradictions, ())
        self.assertEqual(result.credible_contradictions, ())
        self.assertEqual(result.supporting_pieces, ())

    def test_the_four_categories_stay_distinct(self) -> None:
        """An unsupported citation, an unassessed interaction, a citation that
        does not test the edge, and a contradiction are four states."""
        result = summarize(
            piece(
                "A",
                support="not_demonstrated",
                confidence="unsupported",
                strength="insufficient",
            ),
            piece(
                "B",
                support="contradictory",
                confidence="unsupported",
                strength="moderate",
                group="REF-002",
            ),
            piece(
                "C",
                support="partial",
                confidence="low",
                strength="weak",
                group="REF-003",
            ),
            unreviewed("D"),
        )
        self.assertEqual(result.not_demonstrated_pieces, ("A",))
        self.assertEqual(
            tuple(c.evidence_piece_id for c in result.contradictions), ("B",)
        )
        self.assertEqual(result.supporting_pieces, ("C",))
        self.assertEqual(result.unreviewed_pieces, ("D",))
        self.assertEqual(result.coverage, "partially_examined")


class CoverageIsAboutReadingNotFindings(unittest.TestCase):
    def test_all_rows_unreviewed_is_unassessed(self) -> None:
        """Case 6."""
        result = summarize(unreviewed("A"), unreviewed("B"))
        self.assertEqual(result.coverage, "unassessed")
        self.assertEqual(result.curation_completeness, "partial")
        self.assertEqual(result.best_supporting_confidence, "unassessed")
        self.assertEqual(result.supporting_pieces, ())

    def test_one_provisional_positive_experiment(self) -> None:
        """Case 7."""
        result = summarize(piece("A"))
        self.assertEqual(result.coverage, "examined")
        self.assertEqual(result.curation_completeness, "complete")
        self.assertEqual(result.supporting_pieces, ("A",))
        self.assertEqual(result.best_supporting_confidence, "medium")
        self.assertFalse(result.any_supporting_verified)

    def test_mixed_examined_and_unreviewed_is_partial(self) -> None:
        """Case 10. The grade may not be final because more reading could move
        it in either direction, and the label has to say so."""
        result = summarize(piece("A"), unreviewed("B"), unreviewed("C"))
        self.assertEqual(result.coverage, "partially_examined")
        self.assertEqual(result.curation_completeness, "partial")
        self.assertEqual(result.unreviewed_pieces, ("B", "C"))

    def test_an_edge_with_no_rows_at_all_is_no_evidence(self) -> None:
        summaries = summarize_rows_by_edge([], edges={"LE001": None})
        self.assertEqual(summaries["LE001"].coverage, "no_evidence")
        self.assertEqual(summaries["LE001"].curation_completeness, "none")

    def test_every_coverage_value_is_in_the_declared_vocabulary(self) -> None:
        for summary in edge_evidence_summary().values():
            with self.subTest(edge=summary.edge_id):
                self.assertIn(summary.coverage, COVERAGE_STATES)

    def test_a_verified_supporting_record_is_reported(self) -> None:
        result = summarize(piece("A", status="verified"))
        self.assertTrue(result.any_supporting_verified)


class IndependenceIsCountedByStudy(unittest.TestCase):
    def test_two_experiments_from_one_publication_are_one_group(self) -> None:
        """Case 8. Two rows, one study: a paper cannot replicate itself."""
        result = summarize(piece("A", group="REF-001"), piece("B", group="REF-001"))
        self.assertEqual(len(result.supporting_pieces), 2)
        self.assertEqual(result.independent_supporting_groups, 1)

    def test_two_genuinely_independent_studies_are_two_groups(self) -> None:
        """Case 9."""
        result = summarize(piece("A", group="REF-001"), piece("B", group="REF-002"))
        self.assertEqual(result.independent_supporting_groups, 2)

    def test_contradictions_do_not_inflate_supporting_groups(self) -> None:
        result = summarize(
            piece("A", group="REF-001"),
            piece(
                "B",
                support="contradictory",
                confidence="unsupported",
                strength="strong",
                group="REF-002",
            ),
        )
        self.assertEqual(result.independent_supporting_groups, 1)


class TheCredibilityBarIsTheRubrics(unittest.TestCase):
    def test_only_strong_and_moderate_contradictions_are_credible(self) -> None:
        self.assertEqual(CREDIBLE_CONTRADICTION_STRENGTHS, ("strong", "moderate"))
        for strength, expected in (
            ("strong", True),
            ("moderate", True),
            ("weak", False),
            ("insufficient", False),
            ("unassessed", False),
        ):
            result = summarize(
                piece(
                    "B",
                    support="contradictory",
                    confidence="unsupported",
                    strength=strength,
                )
            )
            with self.subTest(strength=strength):
                self.assertEqual(result.contradictions[0].credible, expected)

    def test_a_contradictions_weight_is_what_it_would_have_supported(self) -> None:
        """Section 7.1 step 3: weight is the ceiling its strength and relevance
        would have given a supporting piece."""
        from dt_adoc.evidence import experimental as ex

        for strength, relevance in (
            ("strong", "direct"),
            ("moderate", "close"),
            ("weak", "poor"),
        ):
            result = summarize(
                piece(
                    "B",
                    support="contradictory",
                    confidence="unsupported",
                    strength=strength,
                    relevance=relevance,
                )
            )
            with self.subTest(strength=strength):
                self.assertEqual(
                    result.contradictions[0].weight,
                    ex.contradiction_weight(strength, relevance),
                )


class TheFilterGuard(unittest.TestCase):
    def setUp(self) -> None:
        self.summaries = edge_evidence_summary()

    def test_all_is_permitted_because_it_asserts_nothing(self) -> None:
        self.assertIsNone(refuse_filter_if_premature(self.summaries, "all"))

    def test_high_and_high_medium_are_refused(self) -> None:
        for level in ("high", "high_medium"):
            with self.subTest(level=level), self.assertRaises(FilterRefused) as caught:
                refuse_filter_if_premature(self.summaries, level)
            self.assertIn("no edge-level grade exists", str(caught.exception))

    def test_an_unknown_level_is_refused_rather_than_ignored(self) -> None:
        with self.assertRaises(FilterRefused):
            refuse_filter_if_premature(self.summaries, "medium_ish")

    def test_the_refusal_counts_what_it_refuses_on(self) -> None:
        with self.assertRaises(FilterRefused) as caught:
            refuse_filter_if_premature(self.summaries, "high")
        unassessed = sum(
            1 for s in self.summaries.values() if s.coverage == "unassessed"
        )
        self.assertIn(str(unassessed), str(caught.exception))

    def test_the_refusal_does_not_depend_on_todays_table(self) -> None:
        """Even a table where every edge were fully examined and supported
        still has no edge-level grade to filter on, because 7.1 is not
        implemented."""
        synthetic = summarize_rows_by_edge(
            [piece("A", edge="LE001", status="verified")]
        )
        with self.assertRaises(FilterRefused):
            refuse_filter_if_premature(synthetic, "high")


if __name__ == "__main__":
    unittest.main()


class BothHalvesOfTheSupportDefinition(unittest.TestCase):
    """Section 7.1 step 3 defines a supporting piece by support AND confidence.

    Filtering on `edge_support` alone counted a row the rubric does not: a
    `direct` perturbation whose `experimental_strength` is `insufficient` has a
    confidence ceiling of `unsupported`, which is validator-legal, and it came
    back as support with a "best supporting confidence" of `unsupported`.
    """

    def test_direct_support_at_unsupported_confidence_is_not_support(self) -> None:
        result = summarize(
            piece(
                "A",
                support="direct",
                confidence="unsupported",
                strength="insufficient",
            )
        )
        self.assertEqual(result.supporting_pieces, ())
        self.assertEqual(result.best_supporting_confidence, "unassessed")
        self.assertFalse(result.competing_positive_evidence)
        self.assertEqual(result.independent_supporting_groups, 0)

    def test_that_row_is_legal_for_the_validator(self) -> None:
        """If the schema forbade the combination the filter would not matter.
        It does not forbid it: the ceiling for direct/insufficient is exactly
        `unsupported`."""
        from dt_adoc.evidence import experimental as ex

        self.assertEqual(
            ex.confidence_ceiling("insufficient", "direct", "direct"), "unsupported"
        )

    def test_a_contradiction_still_outweighs_nothing(self) -> None:
        """With the only positive row disqualified, a credible contradiction
        must not find competing evidence to be weighed against."""
        result = summarize(
            piece(
                "A", support="direct", confidence="unsupported", strength="insufficient"
            ),
            piece(
                "B",
                support="contradictory",
                confidence="unsupported",
                strength="strong",
                group="REF-002",
            ),
        )
        self.assertFalse(result.competing_positive_evidence)
        self.assertEqual(len(result.credible_contradictions), 1)

    def test_low_still_counts_as_support(self) -> None:
        """The bar is `unsupported`, not `medium`: `low` is in the rubric's
        list and must not be swept out with it."""
        result = summarize(
            piece("A", support="partial", confidence="low", strength="weak")
        )
        self.assertEqual(result.supporting_pieces, ("A",))
        self.assertEqual(result.best_supporting_confidence, "low")

    def test_the_declared_vocabulary_is_the_rubrics(self) -> None:
        from dt_adoc.evidence.coverage import SUPPORTING_CONFIDENCES

        self.assertEqual(SUPPORTING_CONFIDENCES, ("high", "medium", "low"))
