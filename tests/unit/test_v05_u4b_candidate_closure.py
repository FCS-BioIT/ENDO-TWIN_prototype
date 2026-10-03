"""U4b -- the fourteen Sept-11 candidate nodes are closed, and nothing is promoted.

`docs/v05_u4b_candidate_node_closure.md` is the reasoning. U4b gave every
candidate node in the 2026-09-11 deep-research bundle a final admission decision
under section 5 of `docs/v05_mechanistic_integration_plan.md`, having first
repaired section 5, which defined a disposition for only one of its five possible
failure modes.

WHAT THESE ASSERT, AND WHY EACH IS HERE.

`RefusedGainTest` is the one that matters, and it is the U4 pattern repeated
because the situation repeated. Three encodings in this unit gain structure and
are refused, and each refusal is on evidence that a later round will not see in
the number. The largest is `S_WNT4_CTNNB1 = S_BMP_SMAD and not IN_XAV939`:
`IN_XAV939` is a DECLARED v0.4 input that NO RULE READS, so wiring it costs no
new free variable and reaches 35 -> 37 with the FOXO1 conjunct. DRUNR-003
forbids it in terms, because a global maternal WNT inhibitor does not establish
stromal compartment exposure. The second is `S_FOXO1 = S_WNT4_CTNNB1 or S_PKA`,
which gains where the conjunctive form does not -- and which Li 2013 CONTRADICTS,
having applied WNT4 siRNA with cAMP present and still seen FOXO1 fall. The third
is the `X_ECM_FN1_COL4` package, whose whole +1 comes from `E_ITGA2B1`, an edge
this repository has rejected twice.

`AliasEnlargementTest` pins the two corrections U4b made to asserted structural
claims. Section 4.1 called the staged `E_SOX17` "a pass-through inside AC01,
hence inert" and TI013 predicted the glycosylation pair would break no alias.
Measured, both ENLARGE AC01 -- 9 -> 10 and 9 -> 11. "Inert" and "inert and
alias-enlarging" are different verdicts and only one of them is accurate. These
stay DIAGNOSTICS: after external review B2 neither candidate's disposition reads
from the structural screen, because both fail an earlier criterion.

FOUR TESTS RECORD CORRECTIONS MADE UNDER EXTERNAL REVIEW, and they are the ones
most worth reading, because each pins a place where U4b's first draft was wrong
in a way the numbers did not show. `test_no_node_is_merged_on_boolean_equality_alone`
(B1) -- a rejected rule's function equality is not node identity.
`test_an_activity_node_is_not_given_a_determinant_by_abundance` (B2) -- the
DRE009 failure mode arriving one step upstream, on two candidates at once.
*(`S_FOXO1` left that set on 2026-09-22 by SATISFYING B2: Labied 2006 supplies a
determinant of FOXO1 localisation measured as localisation. The sweep now runs
over `E_SOX17` and `E_ITGA2B1`, and
`test_the_candidate_that_left_the_b2_set_cleared_it_on_a_localisation_read` holds
the positive half, so leaving the set stays something that has to be earned.)*
`test_definition_insufficiency_is_not_recorded_as_refutation` (B3) -- U4b issued
one REJECT and it did not survive scrutiny; there are now none.
`test_formalism_never_overrides_an_earlier_admission_failure` (B4) -- two rules
in section 5 gave different answers for the same row.

`DispositionTableTest` pins the closure itself: all fourteen candidates present,
a closed vocabulary, nothing promoted, and -- the repair that motivated the unit
-- no candidate may hold RETAIN_CATALOG_ONLY while its evidence state says its
primary verification never happened. That is the exact drift U4b found in four
rows.

`LedgerScopeTest` pins that the Sept-11 reads went into a Sept-11-scoped ledger
and that the Sept-16 drug-target ledger was not written into. Backdating a later
unit's reads into an earlier review's file is the provenance error U4 refused to
make with `CD98-d`, and it is just as available here.

`NoMechanismChangeTest` pins that U4b changed nothing executable.

WHAT A FAILURE HERE MEANS. Not "loosen the test". Each blocker is named in the
disposition table's `unblock_condition` column. If that evidence arrives, the
finding document changes first and cites it; these tests follow.
"""

from __future__ import annotations

import csv
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting.structure import load_structure

GUARDED_MODELS = (
    "adoc-literature-superset-v0.4.0",
    "adoc-literature-superset-v0.5.0",
)

REVIEWS = ROOT / "context/literature/reviews"
DISPOSITIONS = (
    REVIEWS / "deep_research_adhesion_model_2026-09-11.candidate-node-dispositions.tsv"
)
U4B_LEDGER = (
    REVIEWS / "deep_research_adhesion_model_2026-09-11.primary-verification.tsv"
)
U4_LEDGER = REVIEWS / "deep_research_drug_targets_2026-09-16.primary-verification.tsv"
#: The 2026-09-18 blocked-source refresh, which read the two papers U4b recorded
#: as access-blocked and therefore SUPERSEDES two of U4b's nine ledger rows. It
#: is a separate dated file rather than an edit to the U4b ledger, for the reason
#: U4 gave when it refused to backdate `CD98-d` into the Sept-16 review: appending
#: a later curation event to an earlier review's file misattributes the curation.
BSR_LEDGER = REVIEWS / "blocked_source_refresh_2026-09-18.primary-verification.tsv"
#: The 2026-09-22 PRL/IGFBP1/FOXO1 evidence-registration unit, which read
#: Labied 2006 in full and therefore re-adjudicates `S_FOXO1`. Same reason as
#: `BSR_LEDGER` for being its own dated file rather than an edit to the U4b one.
PIF_LEDGER = REVIEWS / "prl_igfbp1_foxo1_2026-09-22.primary-verification.tsv"
#: U5b (2026-09-23), which re-adjudicates `S_AKT_EXCESS` on Kang 2022 -- a paper
#: `PIF-007` registered and deliberately did not adjudicate. Same reason again for
#: being its own dated file: writing the verdict into `PIF-007` would backdate it.
U5B_LEDGER = REVIEWS / "u5b_s_akt_excess_2026-09-23.primary-verification.tsv"
#: Ledger order, oldest first. The verdict-agreement loops below read this
#: rather than a hand-written tuple, so a prefix cannot be admitted to
#: `LEDGER_PREFIXES` without its file also entering those loops -- the drift
#: the previous hard-coded pair invited each time a ledger was added.
LEDGERS = (
    ("U4B-", U4B_LEDGER),
    ("BSR-", BSR_LEDGER),
    ("PIF-", PIF_LEDGER),
    ("U5B-", U5B_LEDGER),
)
#: finding_id in the U4b ledger -> finding_id that supersedes it. A superseded row
#: keeps its verbatim finding and is exempt from the verdict comparison below, but
#: it must SAY SO -- see `test_superseded_rows_declare_their_successor`.
SUPERSEDED_BY = {
    "U4B-DRREF-006": "BSR-DRREF-006",
    "U4B-DRREF-007": "BSR-DRREF-007",
}

#: Rows whose own READ is superseded by nothing, but whose stated VERDICT for some
#: candidate was later re-adjudicated on a different paper. They carry a forward
#: reference in `canonical_promotion_decision` rather than a supersession pointer
#: in `verification_route`, because nothing about the read changed.
#:
#: Split out because the column differs: the Yu 2018 pointer went unguarded while
#: the increment document claimed all three were enforced.
FORWARD_REFERENCED = {
    "U4B-DRREF-005": "BSR-DRREF-006",
    # Both U4b rows that stated `S_FOXO1=WAIT_FOR_EXPERIMENT`. Their reads --
    # Li 2013 and Vasquez 2015 -- stand; what moved on 2026-09-22 is the
    # verdict, on a paper (Labied 2006) that neither row had.
    "U4B-DRREF-001": "PIF-001",
    "U4B-DRREF-002": "PIF-001",
}
#: Verification-ledger id prefixes a disposition row may cite. Checked as a set
#: rather than by `startswith` on the joined field, which passed only because the
#: U4b ids happened to sort first. DERIVED from `LEDGERS` rather than written out,
#: so admitting a prefix requires supplying the file that backs it.
LEDGER_PREFIXES = tuple(prefix for prefix, _ in LEDGERS)
STAGED_NODES = (
    ROOT
    / "context/literature/staging/deep_research_adhesion_model_2026-09-11/candidate_nodes.tsv"
)

#: The disposition values section 5 permits after the U4b repair. Two are new
#: (EVIDENCE_UNVERIFIED, MERGE_WITH_EXISTING) and MERGE_WITH_EXISTING is a
#: restoration of the repository's own earlier vocabulary, not an invention --
#: `...2026-09-11.next-stage.md` already lists it.
DISPOSITIONS_ALLOWED = {
    "PROMOTE",
    "RULE_VARIANT_ONLY",
    "WAIT_FOR_EXPERIMENT",
    "RETAIN_CATALOG_ONLY",
    "MERGE_WITH_EXISTING",
    "EVIDENCE_UNVERIFIED",
    "REJECT",
}
NODE_VERDICTS_ALLOWED = {
    "JUSTIFIED",
    "JUSTIFIED_SYSTEM_LIMITED",
    "DUPLICATES_COMMITTED_NODE",
    "SEMANTICS_REFUTED",
    "DEFINITION_INSUFFICIENT",
    "UNVERIFIED",
    "UNVERIFIED_MISCITED",
}
ENCODING_VERDICTS_ALLOWED = {
    "ADMITTED",
    "EVALUATION_ONLY_FAMILY",
    "REJECT_AS_STAGED",
    "REJECT",
    "NONE_PROPOSED",
}
FORMALISM_VERDICTS_ALLOWED = {"REPRESENTABLE", "OUTSIDE_FORMALISM", "NOT_ASSESSED"}

#: Everything the committed rule of `E_RECEPTIVE_SURFACE` is, with a hook for the
#: candidate disjuncts U4b measured. `BaselineTest.test_the_constant_still_matches_the_
#: committed_rule` compares it to `network.bnd`, so a drift in the committed rule fails
#: HERE rather than silently making `_measure` substitute a stale rule. (The docstring
#: previously claimed that guarantee without any assertion behind it; external review
#: caught the overclaim and the assertion was added rather than the claim softened.)
RECEPTIVE_SURFACE = (
    "E_GP130_STAT3 and not E_PODXL and not E_DAG1_FULL and not E_MUC1_BARRIER "
    "and not E_ESTROGENIC_PROLIFERATION and (E_CD98_CD9 or E_CDH1_APICAL or "
    "E_ANXA2_ACTIN or E_HBEGF or E_DAG1_CLEAVED or E_MUC1_SLEX or E_ITGAVB3_5 "
    "or X_SPP1_LUMEN_FREE{extra})"
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _measure(
    overrides: dict[str, str], new_nodes: tuple[tuple[str, str], ...] = ()
) -> tuple[int, int, int, int]:
    """Distinct Boolean functions, free variables, AC01 size, decidual size.

    Uses the repository's OWN exhaustive enumerator on a throwaway copy of the
    model tree, exactly as U4's guard does, so the numbers the finding quotes are
    the numbers `load_structure` produces. Nothing is written to the repo.
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
        for node, logic in new_nodes:
            text += f"\nNode {node} {{\n  logic = {logic};\n}}\n"
        bnd.write_text(text, encoding="utf-8")
        facts = load_structure(model, tmp_root)
    distinct = len(facts.node_ids) - sum(len(c) - 1 for c in facts.alias_classes)
    ac01 = next((c for c in facts.alias_classes if "E_PAEP" in c), ())
    decidual = next((c for c in facts.alias_classes if "S_DECIDUALIZED" in c), ())
    return distinct, len(facts.free), len(ac01), len(decidual)


class BaselineTest(unittest.TestCase):
    """Every number below is a delta against these, so pin them first."""

    def test_the_committed_baseline_is_unchanged(self) -> None:
        self.assertEqual(_measure({}), (35, 19, 9, 6))

    def test_the_constant_still_matches_the_committed_rule(self) -> None:
        """`RECEPTIVE_SURFACE` is a copy, and a copy can go stale silently.

        Without this, a change to `E_RECEPTIVE_SURFACE` in `network.bnd` would
        leave `_measure` substituting the OLD rule and every candidate delta in
        this file would be measured against a model that no longer exists. Only
        `BaselineTest` would notice, and only if the drift moved a count.
        """
        rules = parse_bnd_rules(resolve_model(GUARDED_MODELS[0], ROOT).network_bnd)
        self.assertEqual(
            rules["E_RECEPTIVE_SURFACE"].strip(),
            RECEPTIVE_SURFACE.format(extra=""),
            "the committed receptive-surface rule moved; every delta measured "
            "with RECEPTIVE_SURFACE in this file is stale until it is updated",
        )

    def test_xav939_is_declared_and_read_by_nothing(self) -> None:
        """The premise of the refusal in `RefusedGainTest`.

        If a later unit wires `IN_XAV939` for some other reason, the "costs no
        new free variable" argument changes and the refusal must be re-reasoned.
        """
        facts = load_structure(GUARDED_MODELS[0], ROOT)
        self.assertIn("IN_XAV939", facts.free)
        self.assertEqual(
            set(facts.unread_inputs),
            {"IN_XAV939", "IN_HCG", "IN_EMBRYO_CONDITIONED_SIGNAL"},
        )


class RefusedGainTest(unittest.TestCase):
    """Three encodings gain structure in U4b and all three are refused.

    Recomputed rather than quoted. If these move, the finding's framing -- that
    the evidence, not the structure, is what excludes each one -- is stale and
    must be revised before the numbers here are.
    """

    def test_the_xav939_arm_is_the_largest_gain_and_costs_no_free_variable(
        self,
    ) -> None:
        chain = (("S_BMP_SMAD", "S_BMP2"), ("S_WNT4_CTNNB1", "S_BMP_SMAD"))
        staged = _measure({}, chain)
        self.assertEqual(staged, (35, 19, 9, 6), "the staged chain is inert")

        xav = (
            ("S_BMP_SMAD", "S_BMP2"),
            ("S_WNT4_CTNNB1", "S_BMP_SMAD and not IN_XAV939"),
        )
        self.assertEqual(_measure({}, xav), (36, 19, 9, 6))

        xav_foxo = xav + (("S_FOXO1", "S_WNT4_CTNNB1 and S_PKA"),)
        self.assertEqual(
            _measure({}, xav_foxo),
            (37, 19, 9, 6),
            "35 -> 37 with NINETEEN free variables and no alias class enlarged. "
            "It is refused because DRUNR-003 forbids connecting XAV939 to "
            "S_WNT4_CTNNB1 without compartment-specific exposure evidence, which "
            "does not exist. Li 2013 inhibits WNT with DKK1 on isolated stromal "
            "cells, which is not evidence that a tankyrase inhibitor reaches the "
            "stroma in a two-compartment chip. Revise "
            "docs/v05_u4b_candidate_node_closure.md first, citing the new evidence.",
        )

    def test_the_foxo1_rule_that_gains_is_the_one_the_evidence_refutes(self) -> None:
        """The unit's sharpest structure-versus-evidence conflict."""
        chain = (("S_BMP_SMAD", "S_BMP2"), ("S_WNT4_CTNNB1", "S_BMP_SMAD"))
        conjunctive = _measure({}, chain + (("S_FOXO1", "S_WNT4_CTNNB1 and S_PKA"),))
        disjunctive = _measure({}, chain + (("S_FOXO1", "S_WNT4_CTNNB1 or S_PKA"),))

        self.assertEqual(
            conjunctive,
            (35, 19, 9, 7),
            "the SUPPORTED rule is inert and enlarges the decidual class to seven",
        )
        self.assertEqual(
            disjunctive,
            (36, 19, 9, 6),
            "the rule that GAINS is the one Li 2013 contradicts: WNT4 siRNA was "
            "applied WITH 8-bromo-cAMP present and FOXO1 still fell, which 'or' "
            "cannot produce.",
        )
        self.assertGreater(
            disjunctive[0],
            conjunctive[0],
            "if this ever ceases to hold, the finding's whole point is stale",
        )

    def test_the_ecm_package_gain_belongs_to_a_rejected_edge(self) -> None:
        package = _measure(
            {"E_RECEPTIVE_SURFACE": RECEPTIVE_SURFACE.format(extra=" or E_ITGA2B1")},
            (
                ("X_ECM_FN1_COL4", "S_DECIDUALIZED"),
                ("E_ITGA2B1", "E_GP130_STAT3 and X_ECM_FN1_COL4"),
            ),
        )
        node_alone = _measure({}, (("X_ECM_FN1_COL4", "S_DECIDUALIZED"),))

        self.assertEqual(package, (36, 19, 9, 7))
        self.assertEqual(
            node_alone,
            (35, 19, 9, 7),
            "the ECM node alone buys nothing and still enlarges the decidual "
            "class, so the package's +1 is entirely E_ITGA2B1's -- an edge "
            "rejected by DRE009 and sustained by DTR002/DTR018.",
        )


class XavAttributionTest(unittest.TestCase):
    """The one number in this unit that has drifted twice, and why no prose guard
    is shipped for it.

    `S_WNT4_CTNNB1 = S_BMP_SMAD and not IN_XAV939` measures 35 -> 36; it reaches
    35 -> 37 only with `S_FOXO1 = S_WNT4_CTNNB1 and S_PKA` alongside it. The
    plan's header and flow diagram credited 37 to the rule alone (round 2), and
    after that was fixed the closure record's section 6 summary still did
    (round 5) -- the same defect, in the paragraph a later unit looking for a
    cheap structural win is most likely to read.

    A PROSE GUARD WAS WRITTEN FOR THIS AND DELIBERATELY NOT SHIPPED. It asserted
    that no paragraph mentioning `IN_XAV939` and "37" may omit "FOXO1" or "36".
    Injecting the exact round-5 defect did NOT fail it: the same paragraph lists
    two other candidates' 35 -> 36 results, so the escape clause was satisfied by
    unrelated text. Every narrower phrasing either missed a correct sentence or
    overfitted to one wording. Shipping it would have been a guard that passes by
    checking nothing -- which is itself a defect this unit has already been caught
    with twice, and the reason every new guard here is injection-tested.

    What IS asserted is the measurement, below and in `RefusedGainTest`. That was
    never wrong; the documents drifted away from a correct number. The structural
    fix is to derive the quoted deltas from a machine-readable claim rather than
    to police prose, which is recorded as a follow-up and is out of U4b's scope.
    """

    def test_the_measurement_the_prose_has_twice_drifted_from(self) -> None:
        xav = (
            ("S_BMP_SMAD", "S_BMP2"),
            ("S_WNT4_CTNNB1", "S_BMP_SMAD and not IN_XAV939"),
        )
        self.assertEqual(_measure({}, xav)[0], 36, "the XAV939 rule ALONE")
        self.assertEqual(
            _measure({}, xav + (("S_FOXO1", "S_WNT4_CTNNB1 and S_PKA"),))[0],
            37,
            "37 requires the S_FOXO1 conjunct",
        )


class AliasEnlargementTest(unittest.TestCase):
    """Two asserted 'inert' claims that are measurably worse than inert."""

    def test_staged_sox17_enlarges_ac01(self) -> None:
        staged = _measure(
            {"E_RECEPTIVE_SURFACE": RECEPTIVE_SURFACE.format(extra=" or E_SOX17")},
            (("E_SOX17", "E_SECRETORY_STATE"),),
        )
        self.assertEqual(
            staged,
            (35, 19, 10, 6),
            "section 4.1 called this 'a pass-through inside AC01, hence inert'. "
            "It is inert AND it grows AC01 from nine to ten.",
        )

    def test_the_staged_glycosylation_pair_enlarges_ac01_by_two(self) -> None:
        replaced = RECEPTIVE_SURFACE.format(extra="").replace(
            "E_MUC1_SLEX", "E_SLEX_SURFACE"
        )
        staged = _measure(
            {
                "E_RECEPTIVE_SURFACE": replaced,
                "X_ADHESION_ROUTE_REDUNDANT": (
                    "E_RECEPTIVE_SURFACE and (E_CD98_CD9 or E_CDH1_APICAL or "
                    "E_ANXA2_ACTIN or E_HBEGF or E_DAG1_CLEAVED or E_SLEX_SURFACE) "
                    "and X_INTERFACE_REDUNDANT_RELAY"
                ),
            },
            (
                ("E_GLYCOSYLATION_PROGRAM", "E_SECRETORY_STATE"),
                ("E_SLEX_SURFACE", "E_GLYCOSYLATION_PROGRAM"),
            ),
        )
        self.assertEqual(
            staged,
            (35, 19, 11, 6),
            "TI013 expected 'no alias broken'. Measured, the pair ADDS TWO "
            "members to AC01, so replacing a committed node is refused on "
            "measurement as well as on evidence.",
        )

    def test_staged_esr1_decomposition_is_inert_as_section_4_1_asserted(self) -> None:
        """Section 4.1 asserted 35 -> 35 without measuring it. It holds."""
        self.assertEqual(
            _measure(
                {"E_SECRETORY_STATE": "E_ESR1_ACTIVITY and E_PGR"},
                (("E_ESR1_ACTIVITY", "IN_E2"),),
            ),
            (35, 19, 9, 6),
        )


class DispositionTableTest(unittest.TestCase):
    """The closure itself: fourteen candidates, closed vocabulary, none promoted."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = _rows(DISPOSITIONS)
        cls.by_id = {r["candidate_id"]: r for r in cls.rows}

    def test_every_staged_candidate_node_has_exactly_one_disposition(self) -> None:
        staged = {r["node_id"] for r in _rows(STAGED_NODES)}
        self.assertEqual(len(staged), 14)
        self.assertEqual(set(self.by_id), staged)
        self.assertEqual(len(self.rows), 14, "one row per candidate, no duplicates")

    def test_the_vocabulary_is_closed(self) -> None:
        for row in self.rows:
            with self.subTest(candidate=row["candidate_id"]):
                self.assertIn(row["final_disposition"], DISPOSITIONS_ALLOWED)
                self.assertIn(row["node_verdict"], NODE_VERDICTS_ALLOWED)
                self.assertIn(row["encoding_verdict"], ENCODING_VERDICTS_ALLOWED)
                self.assertIn(row["formalism_verdict"], FORMALISM_VERDICTS_ALLOWED)

    def test_nothing_is_promoted(self) -> None:
        promoted = [
            r["candidate_id"]
            for r in self.rows
            if r["final_disposition"] == "PROMOTE"
            or r["encoding_verdict"] == "ADMITTED"
        ]
        self.assertEqual(promoted, [], "U4b promotes nothing; see section 6")

    def test_retain_catalog_only_requires_that_verification_happened(self) -> None:
        """The section 5 repair, asserted rather than described.

        RETAIN_CATALOG_ONLY is section 5's disposition for a candidate that
        PASSED primary verification and failed the structural screen. Four rows
        held it while their evidence step had never been assessed at all. Nothing
        may drift back into that state.
        """
        for row in self.rows:
            if row["final_disposition"] != "RETAIN_CATALOG_ONLY":
                continue
            with self.subTest(candidate=row["candidate_id"]):
                self.assertNotIn(
                    row["node_verdict"],
                    {"UNVERIFIED", "UNVERIFIED_MISCITED"},
                    "an unverified node may not hold the disposition reserved "
                    "for one whose evidence was weighed",
                )
                cited = [f for f in row["verification_finding_ids"].split(";") if f]
                self.assertTrue(
                    cited and all(f.startswith(LEDGER_PREFIXES) for f in cited),
                    "RETAIN_CATALOG_ONLY must cite verification ledger rows, and "
                    "every id it cites must belong to a known ledger",
                )

    def test_unverified_candidates_are_not_rejected_for_being_unverified(self) -> None:
        """A paywall blocks promotion; it never produces a REJECT."""
        for row in self.rows:
            if row["node_verdict"] not in {"UNVERIFIED", "UNVERIFIED_MISCITED"}:
                continue
            with self.subTest(candidate=row["candidate_id"]):
                self.assertNotEqual(row["final_disposition"], "REJECT")
                self.assertEqual(row["final_disposition"], "EVIDENCE_UNVERIFIED")

    def test_definition_insufficiency_is_not_recorded_as_refutation(self) -> None:
        """External review B3: U4b's first draft over-rejected, twice.

        A node whose definition is merely UNESTABLISHED -- a named component with
        no evidence either way, or a reference bearing on it left unread -- takes
        RETAIN_CATALOG_ONLY. `REJECT` is reserved for a definition the evidence
        positively falsifies, and the burden is on the rejecting unit. Falsifying
        transcript co-regulation among selected enzymes is not falsifying the
        existence of a functional state.
        """
        for row in self.rows:
            if row["node_verdict"] != "DEFINITION_INSUFFICIENT":
                continue
            with self.subTest(candidate=row["candidate_id"]):
                self.assertEqual(row["final_disposition"], "RETAIN_CATALOG_ONLY")
                self.assertEqual(
                    row["first_failing_criterion"],
                    "5(0-insufficient)_definition_not_established",
                )

    def test_a_refutation_discharges_the_burden_section_5_carries(self) -> None:
        """The other half of B3, and why `E_GLYCOSYLATION_PROGRAM` may now refute.

        B3 withdrew U4b's first `REJECT` on two grounds. The LOGICAL one --
        falsifying transcript co-regulation among selected enzymes is not
        falsifying the existence of a functional state -- is permanent, and the
        test above still enforces it for every `DEFINITION_INSUFFICIENT` row. The
        EVIDENTIARY one was specific and dischargeable: "DRREF-006 (Ma 2023), the
        reference bearing on the FUT3 half of the definition, is ACCESS BLOCKED
        and unread. A refutation cannot rest on silence about a component whose
        evidence was never obtained."

        The 2026-09-18 blocked-source refresh obtained and read it, and it
        contradicts the definition rather than being silent on it: FUT3 and
        ST3GAL3 -- the two enzymes the node's label conjoins and its measurables
        column names -- move SIGNIFICANTLY IN OPPOSITE DIRECTIONS in the same
        cells under the same stimulus. So the row may now carry `SEMANTICS_REFUTED`,
        and this pins the conditions under which it may: the definition's own
        named components must be the falsified ones, a verified reference must be
        cited, and the logical scope B3 insisted on must be preserved in the row
        -- the REJECT is of the transcriptional programme, and the functional
        glycan state survives elsewhere.
        """
        for row in self.rows:
            if row["node_verdict"] != "SEMANTICS_REFUTED":
                continue
            with self.subTest(candidate=row["candidate_id"]):
                self.assertEqual(row["final_disposition"], "REJECT")
                self.assertEqual(
                    row["first_failing_criterion"], "5(0-refuted)_definition_falsified"
                )
                self.assertNotIn(
                    "ACCESS BLOCKED",
                    row["decisive_references"],
                    "a refutation may not rest on a reference that was never read",
                )
                self.assertIn("VERIFIED", row["decisive_references"])

        glyco = self.by_id["E_GLYCOSYLATION_PROGRAM"]
        self.assertEqual(glyco["node_verdict"], "SEMANTICS_REFUTED")
        # The falsified components are the ones the DEFINITION names, which is
        # what section 5(0-refuted)'s entailment burden asks the rejecting unit
        # to show. A REJECT citing some other enzyme pair would not discharge it.
        for named in ("FUT3", "ST3GAL3"):
            self.assertIn(named, glyco["semantic_verdict"])
        # B3's logical scope, preserved: the functional glycan state is NOT
        # rejected, and the row must say where it survives.
        self.assertIn("E_SLEX_SURFACE", glyco["unblock_condition"])
        self.assertIn("BSR-DRREF-006", glyco["verification_finding_ids"])
        # ...and the candidate it points at must still be alive, or the scoping
        # is a form of words.
        self.assertNotEqual(self.by_id["E_SLEX_SURFACE"]["final_disposition"], "REJECT")

    def test_no_node_is_merged_on_boolean_equality_alone(self) -> None:
        """External review B1, and the reason §5(0b) was rewritten.

        `X_ECM_FN1_COL4`'s staged rule equals `S_TAZ_ECM`'s committed rule, and
        U4b first read that as identity. It is not: the equality is a property of
        a rule that is itself rejected, and the node dictionary puts the two in
        different compartments with different model roles. The alias is recorded
        against any future encoding; the merge is withdrawn.
        """
        merged = [
            r for r in self.rows if r["final_disposition"] == "MERGE_WITH_EXISTING"
        ]
        self.assertEqual(merged, [], "no Sept-11 candidate meets §5(0b)")

        row = self.by_id["X_ECM_FN1_COL4"]
        self.assertEqual(row["final_disposition"], "RETAIN_CATALOG_ONLY")
        self.assertEqual(row["duplicates"], "")
        self.assertIn(
            "S_TAZ_ECM", row["decisive_reason"], "the alias is still recorded"
        )

        dictionary = {
            r["node_id"]: r
            for r in _rows(
                ROOT
                / "models/superset/adoc-literature-superset-v0.4.0/node_dictionary.tsv"
            )
        }
        taz = dictionary["S_TAZ_ECM"]
        self.assertEqual(taz["compartment"], "stroma")
        self.assertEqual(taz["model_role"], "mechanical_regulator")
        self.assertNotIn("FN1", taz["measurement_proxies"])
        self.assertNotIn("COL4A1", taz["measurement_proxies"])

    def test_an_activity_node_is_not_given_a_determinant_by_abundance(self) -> None:
        """External review B2, swept across the justified activity-state rows.

        A node defined as an activity, localisation or engagement state is not
        given a determinant by evidence that something moves its namesake's mRNA
        or total protein.

        `S_FOXO1` and `E_SOX17` were first recorded as failing at the structural
        screen, which is later and reads as a much weaker objection; the sweep
        external review asked for moved both. `E_ITGA2B1` is here for a different
        reason -- it always failed on activity-versus-abundance (that is DRE009's
        whole content), but revision 1 labelled it `edge_criteria_...` under the
        pre-repair rubric and never re-derived it.

        **`S_FOXO1` LEFT THIS SET ON 2026-09-22, AND B2 IS NOT RELAXED BY THAT.**
        Labied 2006 (`PIF-001`) measures FOXO1 nuclear versus cytoplasmic
        localisation AS LOCALISATION, which is the variable the node names, so
        B2's rule is SATISFIED rather than bypassed and the row legitimately
        moves to `5(4)_delta_and_alias`. A list of names cannot tell that apart
        from someone quietly putting the row back to (4) on abundance evidence,
        which is the exact drift B2 caught -- so the row is not simply dropped.
        It is checked positively below against the ledger row that moved it, and
        against that row's own measurement text.
        """
        for candidate in ("E_SOX17", "E_ITGA2B1"):
            with self.subTest(candidate=candidate):
                self.assertEqual(
                    self.by_id[candidate]["first_failing_criterion"],
                    "5(2)_determinant_activity_vs_abundance",
                )

    def test_the_candidate_that_left_the_b2_set_cleared_it_on_a_localisation_read(
        self,
    ) -> None:
        """The other half of B2: leaving the set has to be earned, in the ledger.

        `S_FOXO1` no longer fails at 5(2). That is only legitimate if the paper
        that cleared it measured the node's own variable, so this asserts the
        ledger row's `proximal_measurement` says so -- the same shape as the
        `E_SLEX_SURFACE` check in
        `test_curation_increment_08_blocked_sources.py`, which pins "flow
        cytometry" and "not a transcript proxy" rather than trusting the verdict.
        """
        row = self.by_id["S_FOXO1"]
        self.assertEqual(row["first_failing_criterion"], "5(4)_delta_and_alias")
        self.assertEqual(row["final_disposition"], "RETAIN_CATALOG_ONLY")
        self.assertIn("PIF-001", row["verification_finding_ids"])

        pif = {r["finding_id"]: r for r in _rows(PIF_LEDGER)}
        self.assertIn("PIF-001", pif)
        measured = pif["PIF-001"]["proximal_measurement"].lower()
        self.assertIn("localisation", measured)
        self.assertIn("immunofluorescence", measured)
        self.assertIn("fractions", measured)
        # ...and it is a localisation read, not an abundance one dressed up: the
        # row must say the abundance readouts are reported separately.
        self.assertIn("separately", measured)

    def test_formalism_never_overrides_an_earlier_admission_failure(self) -> None:
        """External review B4: the two rules contradicted each other.

        `formalism_verdict` is orthogonal and SUBORDINATE. An earlier failure
        governs the disposition; `outside_formalism` only caps it once (0)-(3)
        are satisfied, and it never produces a REJECT in either position.
        """
        tgfb = self.by_id["S_TGFB_CONTEXT"]
        self.assertEqual(tgfb["formalism_verdict"], "OUTSIDE_FORMALISM")
        self.assertEqual(
            tgfb["final_disposition"],
            "EVIDENCE_UNVERIFIED",
            "the step-(1) failure governs; the formalism block is recorded beside it",
        )
        for row in self.rows:
            if row["formalism_verdict"] != "OUTSIDE_FORMALISM":
                continue
            with self.subTest(candidate=row["candidate_id"]):
                self.assertNotEqual(row["final_disposition"], "REJECT")

    def test_every_unresolved_candidate_names_what_would_resolve_it(self) -> None:
        unresolved = {
            "RULE_VARIANT_ONLY",
            "WAIT_FOR_EXPERIMENT",
            "RETAIN_CATALOG_ONLY",
            "EVIDENCE_UNVERIFIED",
        }
        for row in self.rows:
            if row["final_disposition"] not in unresolved:
                continue
            with self.subTest(candidate=row["candidate_id"]):
                self.assertGreater(len(row["unblock_condition"]), 60)

    def test_node_and_encoding_verdicts_are_recorded_separately(self) -> None:
        """Seven candidates have a defensible node and a rejected encoding.

        Collapsing the two columns would erase the distinction this unit exists
        to preserve. `E_JAG1_NOTCH3` is the seventh as of 2026-09-18 and is the
        cleanest example in the table: reading Zhou 2021 moved its NODE off
        UNVERIFIED on primary-human-cell evidence with a pathway-activity readout,
        and left its ENCODING exactly where DRUNR-005 had it, because the paper
        perturbs no upstream input to JAG1 at all.
        """
        split = [
            r["candidate_id"]
            for r in self.rows
            if r["node_verdict"] in {"JUSTIFIED", "JUSTIFIED_SYSTEM_LIMITED"}
            and r["encoding_verdict"] in {"REJECT", "REJECT_AS_STAGED"}
        ]
        self.assertEqual(
            sorted(split),
            [
                "E_ITGA2B1",
                "E_JAG1_NOTCH3",
                "E_SLEX_SURFACE",
                "E_SOX17",
                "S_BMP_SMAD",
                "S_FOXO1",
                "S_WNT4_CTNNB1",
            ],
        )


class LedgerScopeTest(unittest.TestCase):
    """Sept-11 reads belong in a Sept-11 ledger."""

    def test_no_u4b_curation_event_was_backdated_into_the_september_16_ledger(
        self,
    ) -> None:
        """Guard U4b's CURATION EVENT, not the identity of a source document.

        Three versions of this guard, each too broad in a subtler way, and the
        progression is the point. (1) `len(rows) == 7` froze a file U4b has no
        authority over. (2) Forbidding "Europe PMC full-text XML" banned a generic
        verification ROUTE. (3) Forbidding the four sha256 digests banned SOURCE
        DOCUMENT identity -- but a later Sept-16 follow-up may legitimately read
        the same paper, in which case the digest correctly recurs, and this guard
        would have failed honest work.

        What is actually U4b's is the curation EVENT: its finding ids and the
        stamp it writes on a read it performed. Those may not appear in another
        review's ledger; the papers, the routes and the digests may.
        """
        rows = _rows(U4_LEDGER)
        blob = "\n".join("\t".join(r.values()) for r in rows)

        self.assertEqual(
            {r["finding_id"] for r in rows if r["finding_id"].startswith("U4B-")},
            set(),
            "U4b's findings belong in the Sept-11 ledger",
        )
        for marker in ("U4B-DRREF", "(U4b)"):
            with self.subTest(marker=marker):
                self.assertNotIn(
                    marker,
                    blob,
                    "a U4b curation event recorded in the Sept-16 review's ledger",
                )

        # The U4 findings U4b actually leans on, with the claims it leans on.
        by_id = {r["finding_id"]: r for r in rows}
        self.assertIn("DTR002", by_id, "Marwood 2009, reused for X_IL11/E_ITGA2B1")
        self.assertIn("PMID 19213836", by_id["DTR002"]["primary_paper"])
        self.assertIn("LIF but not IL-11", by_id["DTR002"]["what_is_NOT_supported"])
        self.assertIn(
            "DTR005", by_id, "Dominguez 2010, the only verified TGF-beta datum"
        )
        self.assertIn(
            "TGF-beta significantly REDUCES", by_id["DTR005"]["what_is_supported"]
        )

    def test_the_ledger_and_the_dispositions_table_agree_field_by_field(self) -> None:
        """A STRUCTURED agreement check, because the prose one did not hold.

        The previous version checked a handful of withdrawn strings plus candidate
        membership and called itself a verdict-agreement guard. It was not: a
        withdrawn refutation survived it in `U4B-DRREF-005`'s prose, which is
        exactly the class of drift it claimed to cover. The ledger now carries a
        machine-comparable `final_dispositions` field, and this compares it to the
        table candidate by candidate.
        """
        table = {r["candidate_id"]: r["final_disposition"] for r in _rows(DISPOSITIONS)}

        # SUPERSESSION IS PER CANDIDATE, NOT PER ROW, and getting that wrong was
        # this guard's first failure after the refresh. `U4B-DRREF-005` is the Yu
        # 2018 row: its READ is not superseded by anything and its findings still
        # stand, but it also states a verdict for `E_GLYCOSYLATION_PROGRAM`, and
        # that verdict was re-adjudicated on 2026-09-18 on a DIFFERENT paper. So
        # the governing row for a candidate is the LAST one, in ledger order, that
        # names it; earlier rows hold the verdict of their own moment and are
        # historical. Making this row-scoped would have forced either a backdated
        # edit to Yu's row or a permanently red test.
        governing: dict[str, str] = {}
        seen: set[str] = set()
        for _, ledger in LEDGERS:
            for row in _rows(ledger):
                named = [c for c in row["candidate_ids"].split(";") if c]
                pairs = [p for p in row["final_dispositions"].split(";") if p]
                with self.subTest(finding=row["finding_id"]):
                    self.assertEqual(
                        [p.split("=")[0] for p in pairs],
                        named,
                        "every candidate the row names must carry a disposition",
                    )
                for pair in pairs:
                    candidate, disposition = pair.split("=", 1)
                    self.assertIn(candidate, table)
                    governing[candidate] = disposition
                    seen.add(candidate)

        for candidate, disposition in sorted(governing.items()):
            with self.subTest(candidate=candidate):
                self.assertEqual(
                    disposition,
                    table[candidate],
                    f"{candidate}: the governing ledger row and the dispositions "
                    "table state different verdicts",
                )

        # Only the three candidates with no verifiable reference may be absent:
        # `S_ERK` and `S_TGFB_CONTEXT` name none, and `E_ESR1_ACTIVITY`'s one
        # reference does not support it. `S_AKT_EXCESS` left this set in U5b,
        # when `U5B-001` adjudicated it on Kang 2022 (`PIF-007`); until then the
        # comment here called it a candidate with no verifiable reference, which
        # had been untrue since 2026-09-22 while the assertion still passed.
        self.assertEqual(
            set(table) - seen,
            {"S_ERK", "S_TGFB_CONTEXT", "E_ESR1_ACTIVITY"},
        )
        self.assertNotIn("MERGE_WITH_EXISTING", set(table.values()))

    def test_a_stale_ledger_verdict_is_always_covered_by_a_later_one(self) -> None:
        """The price of making supersession per candidate, charged explicitly.

        Exempting earlier rows from the verdict comparison is safe only while
        every disagreement is EXPLAINED by a later row that re-adjudicated the
        same candidate. Without this, the test above would quietly tolerate any
        ledger row drifting away from the table -- which is the drift it exists
        to catch. So: for every (row, candidate) pair whose stated verdict differs
        from the live table, a LATER ledger row must name that candidate.
        """
        table = {r["candidate_id"]: r["final_disposition"] for r in _rows(DISPOSITIONS)}
        ordered = [(ledger, _rows(ledger)) for _, ledger in LEDGERS]
        for index, (ledger, rows) in enumerate(ordered):
            later = {
                c
                for _, following in ordered[index + 1 :]
                for row in following
                for c in row["candidate_ids"].split(";")
                if c
            }
            for row in rows:
                for pair in (p for p in row["final_dispositions"].split(";") if p):
                    candidate, disposition = pair.split("=", 1)
                    if disposition == table[candidate]:
                        continue
                    with self.subTest(finding=row["finding_id"], c=candidate):
                        self.assertIn(
                            candidate,
                            later,
                            f"{ledger.name}:{row['finding_id']} states "
                            f"{candidate}={disposition} but the table says "
                            f"{table[candidate]}, and no later ledger row "
                            "re-adjudicated it -- that is drift, not supersession",
                        )

    def test_every_candidate_a_superseded_row_named_is_readjudicated(self) -> None:
        """Supersession must be total, or the table silently keeps a stale verdict.

        The loop above SKIPS superseded rows, and a skip is exactly how an
        artifact goes stale: if `BSR-DRREF-006` had re-adjudicated only
        `E_SLEX_SURFACE` and quietly dropped `E_GLYCOSYLATION_PROGRAM`, the
        glycosylation verdict would be governed by nothing and compared against
        nothing. So every candidate named by a superseded row must be named by
        its successor too.
        """
        u4b = {r["finding_id"]: r for r in _rows(U4B_LEDGER)}
        bsr = {r["finding_id"]: r for r in _rows(BSR_LEDGER)}
        for old_id, new_id in SUPERSEDED_BY.items():
            with self.subTest(superseded=old_id):
                self.assertIn(new_id, bsr, "the successor row must exist")
                before = {c for c in u4b[old_id]["candidate_ids"].split(";") if c}
                after = {c for c in bsr[new_id]["candidate_ids"].split(";") if c}
                self.assertTrue(
                    before <= after,
                    f"{new_id} drops {sorted(before - after)}, which {old_id} "
                    "adjudicated -- those candidates would be governed by nothing",
                )

    def test_superseded_rows_declare_their_successor(self) -> None:
        """A verbatim row is a record, not a trap.

        U4b's two access-blocked rows are left byte-for-byte on their findings
        because backdating them would misattribute a 2026-09-18 curation to a
        2026-09-17 review. But a reader who lands on `U4B-DRREF-007` and takes
        "no full text available" at face value would be reading a fact that
        stopped being true -- the failure mode this repository has already been
        bitten by. The pointer is the difference between preserved and stale, so
        it is enforced rather than trusted.
        """
        u4b = {r["finding_id"]: r for r in _rows(U4B_LEDGER)}
        for old_id, new_id in SUPERSEDED_BY.items():
            with self.subTest(superseded=old_id):
                route = u4b[old_id]["verification_route"]
                self.assertIn("SUPERSEDED", route)
                self.assertIn(new_id, route)
                self.assertIn(BSR_LEDGER.name, route)

        # A row whose READ stands but whose VERDICT moved points forward from a
        # different column, and is checked in the one it actually uses.
        for old_id, new_id in FORWARD_REFERENCED.items():
            with self.subTest(forward_referenced=old_id):
                note = u4b[old_id]["canonical_promotion_decision"]
                self.assertIn("FORWARD REFERENCE", note)
                self.assertIn(new_id, note)
                self.assertNotIn(
                    "SUPERSEDED",
                    u4b[old_id]["verification_route"],
                    "this row's read is superseded by nothing; only a verdict moved",
                )

    def test_the_refresh_ledger_registers_what_u4b_deliberately_did_not(
        self,
    ) -> None:
        """U4b allocated no `REF-*` id because it was an adjudication unit and
        said so in terms, adding that registering the papers later "is legitimate
        and changes no U4b conclusion". This increment IS that later unit, so its
        ledger rows must carry the canonical ids -- otherwise the digests in the
        prose are again the only record, which is what U4b settled for and this
        unit was asked not to.
        """
        bsr = {r["finding_id"]: r for r in _rows(BSR_LEDGER)}
        for finding, ref, pdf in (
            ("BSR-DRREF-006", "REF-077", "PDF-049"),
            ("BSR-DRREF-007", "REF-076", "PDF-048"),
        ):
            with self.subTest(finding=finding):
                self.assertIn(ref, bsr[finding]["ref_id"])
                self.assertIn(pdf, bsr[finding]["ref_id"])
                self.assertNotIn("not registered", bsr[finding]["ref_id"].lower())
                self.assertNotIn("NOT VERIFIED", bsr[finding]["what_is_supported"])

    def test_the_section_5_2_discriminator_is_applied_consistently(self) -> None:
        """External review B5: the discriminator was real but implicit.

        The rule, in the owner's ratified wording (2026-09-18):
        `WAIT_FOR_EXPERIMENT` when the missing evidence can be obtained by a named
        experiment feasible within the current or planned ADOC programme;
        otherwise `RETAIN_CATALOG_ONLY`. Revision 2 applied the author's earlier
        phrasing of it to `S_BMP_SMAD` and `S_FOXO1` and left `E_ITGA2B1` on an
        inherited label, with nothing to catch the inconsistency. `unblock_locus`
        makes the rule checkable per row; the ratified wording changed no row.
        """
        allowed = {
            "ADOC_RUNNABLE",
            "EXTERNAL",
            "ACCESS_BLOCKED",
            "EXTERNAL_AND_ACCESS_BLOCKED",
        }
        for row in _rows(DISPOSITIONS):
            with self.subTest(candidate=row["candidate_id"]):
                self.assertIn(row["unblock_locus"], allowed)
            if not row["first_failing_criterion"].startswith("5(2)"):
                continue
            if row["final_disposition"] not in {
                "WAIT_FOR_EXPERIMENT",
                "RETAIN_CATALOG_ONLY",
            }:
                continue  # RULE_VARIANT_ONLY is §5's orthogonal route
            expected = (
                "WAIT_FOR_EXPERIMENT"
                if row["unblock_locus"] == "ADOC_RUNNABLE"
                else "RETAIN_CATALOG_ONLY"
            )
            with self.subTest(candidate=row["candidate_id"], rule="5(2)"):
                self.assertEqual(row["final_disposition"], expected)

    def test_the_two_blocked_papers_are_recorded_as_blocked_not_as_negative(
        self,
    ) -> None:
        by_id = {r["finding_id"]: r for r in _rows(U4B_LEDGER)}
        for finding in ("U4B-DRREF-006", "U4B-DRREF-007"):
            with self.subTest(finding=finding):
                row = by_id[finding]
                self.assertIn("ACCESS BLOCKED", row["verification_route"])
                self.assertIn("NOT", row["what_is_supported"])
                self.assertIn(
                    "NOT NEGATIVE EVIDENCE", row["what_is_NOT_supported"].upper()
                )
                # Left verbatim on 2026-09-18: the supersession is recorded in
                # `verification_route` only, so what U4b FOUND is untouched.
                self.assertIn("NOTHING IS VERIFIED", row["what_is_supported"])


class NoMechanismChangeTest(unittest.TestCase):
    """U4b changed nothing executable, in either superset."""

    def test_no_candidate_node_entered_any_committed_model(self) -> None:
        staged = {r["node_id"] for r in _rows(STAGED_NODES)}
        for model in GUARDED_MODELS:
            rules = parse_bnd_rules(resolve_model(model, ROOT).network_bnd)
            body = " ".join(rules.values())
            for node in staged:
                with self.subTest(model=model, node=node):
                    self.assertNotIn(node, rules)
                    self.assertNotIn(node, body)

    def test_both_supersets_still_measure_the_committed_baseline(self) -> None:
        for model in GUARDED_MODELS:
            facts = load_structure(model, ROOT)
            distinct = len(facts.node_ids) - sum(
                len(c) - 1 for c in facts.alias_classes
            )
            with self.subTest(model=model):
                self.assertEqual(distinct, 35)
                self.assertEqual(len(facts.free), 19)
                self.assertEqual(
                    len(next(c for c in facts.alias_classes if "E_PAEP" in c)), 9
                )

    def test_the_staged_bundle_is_not_edited(self) -> None:
        """U4b adjudicates the delta; it does not rewrite it.

        The three reference-less candidates are load-bearing for section 5 of the
        finding, so an edit that quietly supplied them a `refs` value would
        invalidate the argument without touching any file this test names.
        """
        by_id = {r["node_id"]: r for r in _rows(STAGED_NODES)}
        for node in ("S_AKT_EXCESS", "S_ERK", "S_TGFB_CONTEXT"):
            with self.subTest(node=node):
                self.assertEqual(by_id[node]["refs"].strip(), "")


if __name__ == "__main__":
    unittest.main()
