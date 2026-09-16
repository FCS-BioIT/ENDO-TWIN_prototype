"""Guards on the biological adjudication of v0.4's rule-induced merges.

`config/coupling_adjudication.tsv` is the one thing the three identifiability
partitions do not carry: whether a merge the rules force is biologically
defensible. It is a judgement, so what can be machine-checked about it is
narrow, and this module checks exactly that and nothing it cannot:

* **totality and pinning** -- every node in the executable model is adjudicated,
  no node the model does not have is, and every verdict still names the rule
  class it was written against. A rule edit must invalidate the verdict rather
  than inherit it.
* **traceability** -- every row cites evidence that exists in
  `context/evidence-register.tsv`, and every row says what would overturn it.
* **the structural facts the verdicts rest on** -- four of the
  `ARTIFICIALLY_COUPLED` rows assert that a conjunct in a published rule is
  absorbed and therefore vacuous. That is not an opinion, it is a property of
  `network.bnd` over all 2^19 free-variable assignments, and it is enumerated
  here. If a future rule change makes one of those conjuncts live, the
  adjudication resting on it must fail rather than stand on a fact that has
  stopped being true.

What is NOT checked, deliberately: whether a verdict is the *right* one. No test
can settle that, and a test that pinned the current counts would turn a
scientific judgement into a regression fixture.
"""

from __future__ import annotations

import csv
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting.coupling import (
    ADJUDICATIONS,
    SEPARABILITY,
    CouplingAdjudicationError,
    adjudication_for,
    load_coupling_adjudication,
    perturbation_separability,
    separability_disagreements,
)
from dt_adoc.reporting.identifiability import load_identifiability

SUPERSET = "adoc-literature-superset-v0.4.0"
CLASSIFICATION = ROOT / "docs" / "identifiability" / "node_classification.tsv"
TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _facts():
    return load_identifiability(SUPERSET)


def _evaluate_directly(expression: str, values: dict[str, bool]) -> bool:
    """The obvious evaluator, kept as the reference the bit-parallel one is
    checked against."""
    return bool(
        eval(  # the expression comes from the committed model, not from input
            TOKEN.sub(
                lambda m: (
                    str(values[m.group(0)]) if m.group(0) in values else m.group(0)
                ),
                expression,
            )
        )
    )


def _rule_class_of(facts) -> dict[str, str]:
    global_of = {n: members for members in facts.global_classes for n in members}
    return {n: min(global_of[n]) for n in facts.node_ids}


class TotalityAndPinningTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = _facts()
        cls.rule_class = _rule_class_of(cls.facts)

    def test_every_node_is_adjudicated_and_none_is_stale(self) -> None:
        rows = adjudication_for(self.facts.node_ids, self.rule_class, ROOT)
        self.assertEqual(set(rows), set(self.facts.node_ids))

    def test_every_verdict_is_in_the_vocabulary(self) -> None:
        for node_id, row in load_coupling_adjudication(ROOT).items():
            self.assertIn(row["adjudication"], ADJUDICATIONS, node_id)

    def test_a_moved_rule_class_invalidates_the_verdict(self) -> None:
        """The pin must bite, or it is decoration."""
        moved = dict(self.rule_class)
        moved["S_PRL"] = "SOMETHING_ELSE"
        with self.assertRaises(CouplingAdjudicationError) as caught:
            adjudication_for(self.facts.node_ids, moved, ROOT)
        self.assertIn("S_PRL", str(caught.exception))

    def test_a_node_with_no_adjudication_is_refused(self) -> None:
        extended = self.facts.node_ids + ("S_A_NEW_NODE",)
        classes = dict(self.rule_class)
        classes["S_A_NEW_NODE"] = "S_A_NEW_NODE"
        with self.assertRaises(CouplingAdjudicationError):
            adjudication_for(extended, classes, ROOT)

    def test_not_rule_collapsed_is_exactly_the_singleton_classes(self) -> None:
        """The one verdict that is a fact rather than a judgement.

        `NOT_RULE_COLLAPSED` says the rules already give this node its own
        Boolean function, which is computable. Only the other three are
        judgements, and only they are left unchecked.
        """
        global_of = {
            n: members for members in self.facts.global_classes for n in members
        }
        rows = load_coupling_adjudication(ROOT)
        for node_id in self.facts.node_ids:
            alone = len(global_of[node_id]) == 1
            verdict = rows[node_id]["adjudication"]
            with self.subTest(node=node_id):
                self.assertEqual(
                    verdict == "NOT_RULE_COLLAPSED",
                    alone,
                    f"{node_id} is in a rule class of {len(global_of[node_id])} "
                    f"and is adjudicated {verdict}",
                )


class PerturbationSeparabilityTest(unittest.TestCase):
    """The criterion the Gate 2 review turned on, as an enforced invariant.

    A `BIOLOGICALLY_COLLAPSED` verdict says a merge is a defensible abstraction.
    It cannot be, if the merge means two perturbations THIS REPOSITORY declares
    as separate targets are one intervention. `drug_target_catalog.tsv` types
    each executable target, so the question is computable rather than a matter
    of taste, and it is computed rather than curated.

    `E_LIF` (a **ligand**) and `E_GP130_STAT3` (a **pathway_state**) are the case
    that prompted this: `docs/v05_plan_review.md` lists LIF neutralisation and
    STAT3 inhibition as two candidate perturbations on one axis and notes that
    both nodes are present, while the rules make them one Boolean function. They
    are not one experiment -- STAT3 inhibition blocks the pathway whichever
    ligand drives it, and `X_IL11` is the staged candidate that makes the
    difference real. Four of the only six class-gaining readouts sit on that
    axis.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.facts = _facts()
        cls.members = {
            n: members for members in cls.facts.global_classes for n in members
        }
        cls.separability = perturbation_separability(
            cls.facts.node_ids, cls.members, SUPERSET, ROOT
        )
        cls.rows = load_coupling_adjudication(ROOT)

    def test_the_verdicts_are_in_the_vocabulary(self) -> None:
        for node_id, (verdict, _partners) in self.separability.items():
            self.assertIn(verdict, SEPARABILITY, node_id)

    #: Nodes where the separability signal and the adjudication currently point
    #: different ways. Empty today. This is a TRIPWIRE on a derived signal, not
    #: a definition: separability says what the model can express, adjudication
    #: says whether a collapse is defensible, and neither implies the other (see
    #: `separability_disagreements`). A new entry means a person should look,
    #: not that the adjudication is wrong.
    EXPECTED_DISAGREEMENTS: ClassVar[dict[str, tuple[str, str]]] = {}

    def test_the_separability_adjudication_disagreements_are_the_expected_set(
        self,
    ) -> None:
        """Reported, not enforced. Withdrawn as an invariant on 2026-09-16.

        The old assertion was that `MERGES_DISTINCT_TARGET_CLASSES` forces
        `ARTIFICIALLY_COUPLED` "by definition". DTR020 -- this repository's own
        high-confidence finding -- shows why that was unsound: `target_class` is
        free text with 24 values across 34 rows, 17 unique, so which merges
        tripped it followed naming granularity. The barrier trio escaped only
        because all three happened to carry one coarse label, and applied
        consistently the rule would have overridden their curated `UNIDENTIFIED`
        verdict on a naming accident.

        Dropping the forcing changed no adjudication, which is the point: the
        expected set below is empty because every node that reports the signal
        is independently adjudicated `ARTIFICIALLY_COUPLED` on its own evidence.
        """
        found = {
            node_id: (verdict, self.rows[node_id]["adjudication"])
            for node_id, (verdict, _) in self.separability.items()
            if verdict == "MERGES_DISTINCT_TARGET_CLASSES"
            and self.rows[node_id]["adjudication"] != "ARTIFICIALLY_COUPLED"
        }
        self.assertEqual(
            found,
            self.EXPECTED_DISAGREEMENTS,
            "the separability/adjudication disagreement set changed; this is a "
            "prompt to re-adjudicate those nodes by hand, NOT a rule that the "
            "adjudication must follow the target taxonomy",
        )

    def test_the_module_helper_reports_the_same_set(self) -> None:
        self.assertEqual(
            separability_disagreements(
                self.facts.node_ids, self.members, SUPERSET, ROOT
            ),
            self.EXPECTED_DISAGREEMENTS,
        )

    def test_no_defensible_collapse_hides_a_lost_perturbation(self) -> None:
        """The reviewer's question, stated as the property it asks about.

        After the 2026-09-16 revision no node adjudicated
        `BIOLOGICALLY_COLLAPSED` is a catalogued executable target at all, which
        is a stronger statement than the invariant above and is therefore
        asserted separately: if a future verdict called a target-merging
        collapse defensible, this fails even if the two targets happened to
        share a class.

        CATALOG MEMBERSHIP IS READ DIRECTLY, not inferred from the separability
        column. An earlier revision asserted
        `separability == "NOT_A_CATALOGUED_TARGET"`, which at the time meant
        both "absent from the catalog" and "present but merged with nobody
        else in it" -- so a catalogued target could have passed. The column has
        since been split, and this reads the catalog anyway: a guard for a
        property about the catalog should not depend on a derived column
        continuing to encode it.
        """
        catalog = ROOT / "models" / "superset" / SUPERSET / "drug_target_catalog.tsv"
        with catalog.open(newline="", encoding="utf-8") as handle:
            executable = {
                row["target_id"]
                for row in csv.DictReader(handle, delimiter="\t")
                if row["execution_status"] == "executable"
            }
        self.assertIn("E_CDH1_APICAL", executable, "catalog read is wrong")
        for node_id, row in self.rows.items():
            if row["adjudication"] != "BIOLOGICALLY_COLLAPSED":
                continue
            with self.subTest(node=node_id):
                self.assertNotIn(
                    node_id,
                    executable,
                    f"{node_id} is adjudicated a defensible collapse while "
                    "being an executable drug-target-catalog entry",
                )
                self.assertEqual(
                    self.separability[node_id][0], "NOT_A_CATALOGUED_TARGET"
                )

    def test_a_catalogued_node_is_never_called_uncatalogued(self) -> None:
        """The split the review asked for, checked in both directions.

        `E_CDH1_APICAL` is executable in the catalog and is merged only with
        `IN_EMBRYO_CONTACT`, which is not. It must read
        `MERGES_NO_CATALOGUED_TARGET`, never `NOT_A_CATALOGUED_TARGET`, or the
        shipped column states something the catalog contradicts.
        """
        catalog = ROOT / "models" / "superset" / SUPERSET / "drug_target_catalog.tsv"
        with catalog.open(newline="", encoding="utf-8") as handle:
            executable = {
                row["target_id"]
                for row in csv.DictReader(handle, delimiter="\t")
                if row["execution_status"] == "executable"
            }
        for node_id, (verdict, _partners) in self.separability.items():
            with self.subTest(node=node_id):
                if verdict == "NOT_A_CATALOGUED_TARGET":
                    self.assertNotIn(node_id, executable)
                if verdict in {
                    "MERGES_NO_CATALOGUED_TARGET",
                    "MERGES_SAME_TARGET_CLASS",
                    "MERGES_DISTINCT_TARGET_CLASSES",
                }:
                    self.assertIn(node_id, executable)
        self.assertEqual(
            self.separability["E_CDH1_APICAL"][0], "MERGES_NO_CATALOGUED_TARGET"
        )

    def test_the_lif_gp130_case_is_caught_by_name(self) -> None:
        """Named, because a general invariant that silently stopped covering
        the case it was written for would look healthy."""
        for node_id in ("E_LIF", "E_GP130_STAT3", "E_CD98_CD9"):
            verdict = self.separability[node_id][0]
            with self.subTest(node=node_id):
                self.assertEqual(verdict, "MERGES_DISTINCT_TARGET_CLASSES")
                self.assertEqual(
                    self.rows[node_id]["adjudication"], "ARTIFICIALLY_COUPLED"
                )
        self.assertIn("E_GP130_STAT3", self.separability["E_LIF"][1])
        self.assertIn("E_LIF", self.separability["E_GP130_STAT3"][1])

    def test_same_class_merges_are_reported_and_not_forced(self) -> None:
        """The barrier trio must stay reportable without being pre-judged.

        `E_PODXL`, `E_DAG1_FULL` and `E_MUC1_BARRIER` are three executable
        targets the catalog types identically -- `anti_adhesive_surface`. The
        merge is recorded, and whether it is a defect is Gate 3b's question, so
        the invariant must NOT force a verdict on them.
        """
        for node_id in ("E_PODXL", "E_DAG1_FULL", "E_MUC1_BARRIER"):
            self.assertEqual(
                self.separability[node_id][0], "MERGES_SAME_TARGET_CLASS", node_id
            )
            self.assertEqual(self.rows[node_id]["adjudication"], "UNIDENTIFIED")

    def test_a_collapse_verdict_on_a_distinct_class_merge_is_reported_not_refused(
        self,
    ) -> None:
        """The behaviour that replaced the invariant, exercised end to end.

        Previously this asserted that flipping `E_LIF` to
        `BIOLOGICALLY_COLLAPSED` made the file refuse to load. It no longer
        does, and that is the decision: the taxonomy reports, it does not
        adjudicate. What must still happen is that the disagreement becomes
        VISIBLE -- a silent acceptance would be the actual regression.
        """
        rule_class_of = _rule_class_of(self.facts)
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "repo"
            sandbox.mkdir()
            for relative in ("models", "config", "context"):
                shutil.copytree(ROOT / relative, sandbox / relative)
            target = sandbox / "config" / "coupling_adjudication.tsv"
            text = target.read_text(encoding="utf-8").replace(
                "E_LIF\tE_CD98_CD9\tARTIFICIALLY_COUPLED",
                "E_LIF\tE_CD98_CD9\tBIOLOGICALLY_COLLAPSED",
            )
            self.assertIn("E_LIF\tE_CD98_CD9\tBIOLOGICALLY_COLLAPSED", text)
            target.write_text(text, encoding="utf-8")

            # It loads. That is the change.
            rows = adjudication_for(
                self.facts.node_ids,
                rule_class_of,
                sandbox,
                rule_class_members=self.members,
                model_version=SUPERSET,
            )
            self.assertEqual(rows["E_LIF"]["adjudication"], "BIOLOGICALLY_COLLAPSED")
            self.assertEqual(len(rows), 59)

            # And it is reported, so the disagreement cannot pass unnoticed.
            found = separability_disagreements(
                self.facts.node_ids, self.members, SUPERSET, sandbox
            )
            self.assertIn("E_LIF", found)
            self.assertEqual(
                found["E_LIF"],
                ("MERGES_DISTINCT_TARGET_CLASSES", "BIOLOGICALLY_COLLAPSED"),
            )

    def test_the_real_file_still_adjudicates_the_lif_merge_artificial(self) -> None:
        """Removing the forcing must not have weakened the actual verdict.

        The reviewer's explicit condition: do not delete valid adjudications to
        make the invariant disappear. `E_LIF` is `ARTIFICIALLY_COUPLED` on its
        own rationale and evidence, not because a rule compelled it.
        """
        self.assertEqual(self.rows["E_LIF"]["adjudication"], "ARTIFICIALLY_COUPLED")
        self.assertGreater(len(self.rows["E_LIF"]["rationale"]), 80)
        self.assertTrue(self.rows["E_LIF"]["evidence_ids"].strip())


class TraceabilityTest(unittest.TestCase):
    def test_every_row_cites_registered_evidence(self) -> None:
        """Enforced by the loader; asserted here so the guard is visible."""
        rows = load_coupling_adjudication(ROOT)
        with (ROOT / "context" / "evidence-register.tsv").open(
            newline="", encoding="utf-8"
        ) as handle:
            known = {r["evidence_id"] for r in csv.DictReader(handle, delimiter="\t")}
        for node_id, row in rows.items():
            cited = [e for e in row["evidence_ids"].split(";") if e]
            self.assertTrue(cited, node_id)
            for evidence_id in cited:
                self.assertIn(evidence_id, known, node_id)

    def test_every_row_states_what_would_overturn_it(self) -> None:
        for node_id, row in load_coupling_adjudication(ROOT).items():
            self.assertTrue(row["what_would_change_it"].strip(), node_id)

    def test_the_generated_table_carries_the_adjudication(self) -> None:
        with CLASSIFICATION.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        curated = load_coupling_adjudication(ROOT)
        self.assertEqual(len(rows), 59)
        for row in rows:
            self.assertEqual(
                row["coupling_adjudication"],
                curated[row["node_id"]]["adjudication"],
                row["node_id"],
            )


class AbsorbedConjunctTest(unittest.TestCase):
    """The structural facts four ARTIFICIALLY_COUPLED verdicts rest on.

    Each names a conjunct of a published rule that contributes nothing because
    the rest of the conjunction already implies it. Checked over every one of the
    2^19 free-variable assignments rather than argued, because "vacuous" is a
    claim about all assignments and a spot check is not one.

    Evaluated BIT-PARALLEL: each node becomes one 524,288-bit integer whose bit
    *i* is that node's value under assignment *i*, and the rules are applied with
    bitwise operators. One pass over 40 rules replaces 21 million per-state
    evaluations, which is the difference between this guard costing two minutes
    of the suite and costing none. `not` maps to `~` under a wrapper that
    re-masks, and the two agree on precedence for every form the rules use --
    `not A and B` and `~A & B` both bind the negation tightest.
    """

    class _Bits:
        __slots__ = ("v",)

        def __init__(self, v: int) -> None:
            self.v = v

        def __and__(self, other: AbsorbedConjunctTest._Bits):
            return AbsorbedConjunctTest._Bits(self.v & other.v)

        def __or__(self, other: AbsorbedConjunctTest._Bits):
            return AbsorbedConjunctTest._Bits(self.v | other.v)

        def __invert__(self):
            return AbsorbedConjunctTest._Bits(~self.v & AbsorbedConjunctTest.ALL)

    ALL = 0

    @classmethod
    def setUpClass(cls) -> None:
        rules = {
            node: expression.replace(";", "").strip()
            for node, expression in parse_bnd_rules(
                resolve_model(SUPERSET).network_bnd
            ).items()
        }
        free = [n for n, r in rules.items() if r == n]
        cls.free = free
        width = 1 << len(free)
        cls.width = width
        AbsorbedConjunctTest.ALL = (1 << width) - 1

        # Column i of the truth table: bit j is set when assignment j has free
        # variable i true. Built by tiling a run of 2^i zeros and 2^i ones.
        env: dict[str, AbsorbedConjunctTest._Bits] = {}
        for index, node in enumerate(free):
            block = 1 << index
            pattern = 0
            for start in range(block, width, 2 * block):
                pattern |= ((1 << block) - 1) << start
            env[node] = cls._Bits(pattern)

        deps = {
            n: {t for t in TOKEN.findall(rules[n]) if t in rules and t != n}
            for n in rules
        }
        pending = [n for n in rules if n not in env]
        while pending:
            progressed = False
            for node in list(pending):
                if deps[node] <= set(env):
                    expression = (
                        rules[node]
                        .replace(" and ", " & ")
                        .replace(" or ", " | ")
                        .replace("not ", "~")
                    )
                    env[node] = eval(
                        TOKEN.sub(
                            lambda m: (
                                f"env[{m.group(0)!r}]"
                                if m.group(0) in env
                                else m.group(0)
                            ),
                            expression,
                        ),
                        {"env": env},
                    )
                    pending.remove(node)
                    progressed = True
            assert progressed, pending
        cls.env = {k: v.v for k, v in env.items()}

    def _assert_absorbed(self, rest: int, conjunct: int, what: str) -> None:
        """`rest` already implies `conjunct`, so adding it changes nothing."""
        self.assertEqual(
            rest & ~conjunct & self.ALL,
            0,
            f"{what} is no longer absorbed: the conjunct is false in "
            f"{(rest & ~conjunct & self.ALL).bit_count()} of the "
            f"{self.width} assignments where the rest of the rule holds",
        )

    def test_the_enumeration_is_the_whole_space(self) -> None:
        self.assertEqual(len(self.free), 19)
        self.assertEqual(self.width, 2**19)

    def test_the_integrin_conjunct_in_the_spp1_route_is_vacuous(self) -> None:
        """E_ITGAVB3_5 -- the receptor of the model's headline adhesion route."""
        env = self.env
        rest = (
            env["E_RECEPTIVE_SURFACE"]
            & env["X_SPP1_LUMEN_FREE"]
            & env["X_INTERFACE_SPP1_RELAY"]
        )
        self._assert_absorbed(rest, env["E_ITGAVB3_5"], "E_ITGAVB3_5")

    def test_the_paep_conjunct_in_epithelial_receptivity_is_vacuous(self) -> None:
        env = self.env
        self._assert_absorbed(env["E_RECEPTIVE_SURFACE"], env["E_PAEP"], "E_PAEP")

    def test_the_marker_conjuncts_in_stromal_decidualization_are_vacuous(self) -> None:
        env = self.env
        self._assert_absorbed(env["S_DECIDUALIZED"], env["S_PRL"], "S_PRL")
        self._assert_absorbed(env["S_DECIDUALIZED"], env["S_IGFBP1"], "S_IGFBP1")

    def test_the_taz_conjunct_in_mechanical_permissiveness_is_vacuous(self) -> None:
        env = self.env
        rest = env["S_DECIDUALIZED"] & ~(
            (env["IN_ER_STRESS_EXCESS"] | env["IN_HIGH_ECM_STIFFNESS"])
            & env["X_MECHANICAL_STRESS_RELAY"]
        )
        self._assert_absorbed(rest & self.ALL, env["S_TAZ_ECM"], "S_TAZ_ECM")

    def test_the_fgf_conjunct_in_epithelial_proliferation_is_vacuous(self) -> None:
        """The fifth, and a DIFFERENT SHAPE from the other four.

        The four above are alias members: two nodes realise one function, and a
        conjunct naming one of them adds nothing. `S_FGF_MITOGENIC` is not in an
        alias class at all -- it has its own Boolean function, the complement of
        `S_HAND2` -- and its *use* is still vacuous, because
        `S_FGF_MITOGENIC = not S_HAND2` makes
        `S_FGF_MITOGENIC and not S_HAND2` reduce to `not S_HAND2`.

        So absorption is not only a property of alias classes, and a node can be
        structurally distinct while doing no work where it is read. The
        consequence is the one that matters for design: HAND2 loss and an
        FGF-level perturbation have **no distinct image** in this model, so the
        stroma-to-epithelium relay's own intermediate cannot be probed
        separately from its upstream regulator.

        Found while testing whether NR2F2's documented repression of epithelial
        proliferation was an unwired edge; it is wired, through exactly this
        vacuous intermediate. Recorded 2026-09-16.
        """
        env = self.env
        rest = env["IN_E2"] & ~env["S_HAND2"] & self.ALL
        self._assert_absorbed(rest, env["S_FGF_MITOGENIC"], "S_FGF_MITOGENIC")

    def test_epithelial_proliferation_reduces_to_e2_and_not_hand2(self) -> None:
        """The consequence stated positively, so deleting the guard above is
        not enough to hide it."""
        env = self.env
        self.assertEqual(
            env["E_ESTROGENIC_PROLIFERATION"],
            env["IN_E2"] & ~env["S_HAND2"] & self.ALL,
            "E_ESTROGENIC_PROLIFERATION no longer reduces to IN_E2 and not "
            "S_HAND2; the FGF intermediate may have become load-bearing, which "
            "would be a repair worth recording rather than a regression",
        )

    def test_the_bit_parallel_evaluation_agrees_with_direct_evaluation(self) -> None:
        """The optimisation is only trustworthy if it is checked against the
        obvious implementation. Sampled rather than exhaustive, because the
        exhaustive version is precisely what is too slow to keep.
        """
        import random

        rules = {
            node: expression.replace(";", "").strip()
            for node, expression in parse_bnd_rules(
                resolve_model(SUPERSET).network_bnd
            ).items()
        }
        deps = {
            n: {t for t in TOKEN.findall(rules[n]) if t in rules and t != n}
            for n in rules
        }
        order: list[str] = []
        seen = set(self.free)
        pending = [n for n in rules if n not in seen]
        while pending:
            for node in list(pending):
                if deps[node] <= seen:
                    order.append(node)
                    seen.add(node)
                    pending.remove(node)

        rng = random.Random(20260915)
        for _ in range(64):
            index = rng.randrange(self.width)
            direct = {
                node: bool(index >> position & 1)
                for position, node in enumerate(self.free)
            }
            for node in order:
                direct[node] = _evaluate_directly(rules[node], direct)
            for node, bits in self.env.items():
                with self.subTest(assignment=index, node=node):
                    self.assertEqual(bool(bits >> index & 1), direct[node])


class ZeroDegreeInputTest(unittest.TestCase):
    """Three declared inputs that no rule reads, named by three adjudications.

    `IN_HCG` and `IN_EMBRYO_CONDITIONED_SIGNAL` are the inducers
    `LIT-CD98-001` and `LIT-CDH1-001` name for the epithelial adhesive
    response, and they are wired nowhere; `IN_XAV939` is a cocktail agent whose
    de-bundling would move nothing. If one of them ever gains a reader, the
    rationale that calls it unused has to be rewritten.
    """

    def test_the_three_named_inputs_are_read_by_no_rule(self) -> None:
        rules = parse_bnd_rules(resolve_model(SUPERSET).network_bnd)
        for node in ("IN_HCG", "IN_EMBRYO_CONDITIONED_SIGNAL", "IN_XAV939"):
            readers = [
                other
                for other, expression in rules.items()
                if other != node and node in TOKEN.findall(expression)
            ]
            with self.subTest(node=node):
                self.assertEqual(readers, [], f"{node} is now read by {readers}")


if __name__ == "__main__":
    unittest.main()
