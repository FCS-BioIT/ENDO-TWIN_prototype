"""U3 -- AC01 stays aliased, and no free Boolean variable was created.

`docs/v05_u3_ac01_no_derivable_rule.md` is the reasoning. U3 looked for a
defensible replacement rule for the nine-member AC01 alias class, found one
candidate that is structurally effective, and rejected it on section 5's
EDGE-promotion criteria -- so the alias stays in place and is flagged, which is
one of the two outputs the plan's section 7.1 allows. The structural result is a
diagnostic and was never the evidence basis.

WHAT THESE ASSERT, AND WHY EACH IS HERE.

The owner decision that U3 must not answer AC01 with free Boolean variables is
the one a future round is most likely to undo, because it is the cheapest way to
make the audit's divergence representable. A free node in MaBoSS is
`logic = <self>` -- a Bernoulli flipped once from a hand-typed istate -- and
`E_ITGAVB3_5` is a required conjunct of `X_ADHESION_ROUTE_SPP1`
(`network.bnd:214`), so a new one lands directly on the adhesion prediction.
`FreeVariableTest` pins the count.

`AliasClassTest` pins the class itself, computed with the repository's own
`load_structure`, which is exhaustive over the free variables rather than
sampled. If AC01 changes, the finding document is stale and must be revised
before the test is.

`DegenerateRuleTest` pins the structural fact the document turns on, because it
is the part most likely to be quietly "fixed": `E_ITGAVB3_5`'s committed rule
absorbs to `E_SECRETORY_STATE`, and so does the one catalog variant aimed at it.
A future round that adds `E_GP130_STAT3` to that disjunction -- a core_extension
edge at confidence 6 -- would believe it had repaired something and would not
have.

WHAT A FAILURE HERE MEANS. Not "loosen the test". U3's blocker is evidence for a
second epithelial determinant that is not a subset of `E_SECRETORY_STATE`. If
that evidence arrives, the finding document changes first and cites it; these
tests follow.
"""

from __future__ import annotations

import itertools
import json
import re
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting.identifiability import parse_bnd_rules, repo_root, resolve_model
from dt_adoc.reporting.structure import load_structure

ROOT = repo_root()

GUARDED_MODELS = (
    "adoc-literature-superset-v0.4.0",
    "adoc-literature-superset-v0.5.0",
)

#: The nine members, as `config/scrna_observation_map.tsv` records them and as
#: the committed network computes them.
AC01 = (
    "E_ANXA2_ACTIN",
    "E_DAG1_CLEAVED",
    "E_HBEGF",
    "E_ITGAVB3_5",
    "E_MUC1_SLEX",
    "E_PAEP",
    "E_PC6",
    "E_SECRETORY_STATE",
    "E_SPP1_EXPR",
)

#: The seven verification rows U3 read in the section-5(1) ledger. Asserted as a
#: SUBSET, not as the whole file: U4 may legitimately append its own genuine
#: TI001/TI002/TI004 rows to the same review-scoped ledger, and that must not
#: fail U3. What must not change is that these seven remain and that REF-059
#: stays absent, since U3's section-5(1) verdict turns on that absence.
U3_BASELINE_LEDGER_ROWS = frozenset(
    {
        "DTR002",
        "DTR002-followup",
        "DTR005",
        "DTR006",
        "DTR011",
        "DTR017",
        "DTR026",
    }
)

#: 19 free variables, of which 5 are not `IN_*`. `identifiability_analysis.md`
#: records those five as the latent space; each addition doubles it.
EXPECTED_FREE = 19
EXPECTED_FREE_NON_INPUT = 5


class FreeVariableTest(unittest.TestCase):
    """The owner decision, pinned as a count rather than as prose."""

    def test_no_free_boolean_variable_was_added(self) -> None:
        for model in GUARDED_MODELS:
            rules = parse_bnd_rules(resolve_model(model, ROOT).network_bnd)
            free = sorted(n for n in rules if rules[n].strip() == n)
            with self.subTest(model=model):
                self.assertEqual(
                    len(free),
                    EXPECTED_FREE,
                    "the free-variable count changed. U3 may not answer AC01 "
                    "with a free Boolean variable: it replaces a false equality "
                    "with unconstrained biology, which is not a smaller error "
                    "(owner decision, plan section 7.1).",
                )
                self.assertEqual(
                    len([n for n in free if not n.startswith("IN_")]),
                    EXPECTED_FREE_NON_INPUT,
                )

    def test_no_ac01_member_became_free(self) -> None:
        """The specific form the forbidden repair would take."""
        for model in GUARDED_MODELS:
            rules = parse_bnd_rules(resolve_model(model, ROOT).network_bnd)
            for node in AC01:
                with self.subTest(model=model, node=node):
                    self.assertNotEqual(rules[node].strip(), node)


class AliasClassTest(unittest.TestCase):
    """AC01 is unchanged, computed exhaustively by the repository's own code."""

    def test_ac01_is_still_the_same_nine_members(self) -> None:
        for model in GUARDED_MODELS:
            facts = load_structure(model, ROOT)
            classes = [c for c in facts.alias_classes if "E_PAEP" in c]
            with self.subTest(model=model):
                self.assertEqual(len(classes), 1)
                self.assertEqual(tuple(sorted(classes[0])), AC01)

    def test_the_distinct_function_count_is_unchanged(self) -> None:
        """35 is the baseline every measured delta in the plan is quoted against."""
        for model in GUARDED_MODELS:
            facts = load_structure(model, ROOT)
            distinct = len(facts.node_ids) - sum(
                len(c) - 1 for c in facts.alias_classes
            )
            with self.subTest(model=model):
                self.assertEqual(distinct, 35)


class DegenerateRuleTest(unittest.TestCase):
    """`E_ITGAVB3_5`'s rule absorbs, and so does the catalog variant aimed at it.

    Enumerated over the four variables the class depends on, which is exhaustive
    rather than sampled.

    The claim is NOT that the nine members share a syntactic upstream closure --
    `E_ITGAVB3_5` reaches `E_KLF12_HIGH` through `E_LIF` and the other eight do
    not. It is that all nine compute the same EFFECTIVE Boolean function, whose
    SUPPORT is `{IN_E2, IN_PROGESTIN, IN_MIFEPRISTONE}`. `E_KLF12_HIGH` is in
    `E_ITGAVB3_5`'s closure but not in its function's support, because the arm
    carrying it is absorbed -- which is precisely what enumerating both of its
    values below demonstrates.
    """

    INPUTS = ("IN_E2", "IN_PROGESTIN", "IN_MIFEPRISTONE", "E_KLF12_HIGH")

    def _worlds(self):
        for values in itertools.product([False, True], repeat=len(self.INPUTS)):
            v = dict(zip(self.INPUTS, values, strict=True))
            pgr = v["IN_PROGESTIN"] and not v["IN_MIFEPRISTONE"]
            sec = v["IN_E2"] and pgr
            lif = sec and not v["E_KLF12_HIGH"]
            yield sec, lif, sec  # E_SECRETORY_STATE, E_LIF, E_HBEGF

    def test_the_committed_rules_are_the_ones_this_reasoning_assumes(self) -> None:
        """Guard the premise, so the enumeration cannot silently describe nothing."""
        rules = parse_bnd_rules(resolve_model(GUARDED_MODELS[1], ROOT).network_bnd)
        self.assertEqual(rules["E_SECRETORY_STATE"].strip(), "IN_E2 and E_PGR")
        self.assertEqual(rules["E_PGR"].strip(), "IN_PROGESTIN and not IN_MIFEPRISTONE")
        self.assertEqual(
            rules["E_LIF"].strip(), "E_SECRETORY_STATE and not E_KLF12_HIGH"
        )
        self.assertEqual(rules["E_HBEGF"].strip(), "E_SECRETORY_STATE")
        self.assertEqual(
            rules["E_ITGAVB3_5"].strip(), "E_LIF or E_HBEGF or E_SECRETORY_STATE"
        )

    def test_the_committed_itgav_rule_reduces_to_the_secretory_state(self) -> None:
        for sec, lif, hbegf in self._worlds():
            self.assertEqual(bool(lif or hbegf or sec), bool(sec))

    def test_the_catalog_variant_also_absorbs(self) -> None:
        """`dr20260911_itgav_no_secretory_absorption` is a prerequisite, not a repair."""
        for sec, lif, hbegf in self._worlds():
            self.assertEqual(bool(lif or hbegf), bool(sec))

    def test_adding_the_unimplemented_core_edge_would_also_absorb(self) -> None:
        """EDGE-006 (`E_GP130_STAT3` -> `E_ITGAVB3_5`), confidence 6, core_extension.

        The most-supported edge touching this class that v0.4 does not implement.
        `E_GP130_STAT3 = E_LIF`, so it changes nothing.
        """
        rules = parse_bnd_rules(resolve_model(GUARDED_MODELS[1], ROOT).network_bnd)
        self.assertEqual(rules["E_GP130_STAT3"].strip(), "E_LIF")
        for sec, lif, hbegf in self._worlds():
            gp130 = lif
            self.assertEqual(bool(lif or hbegf or sec or gp130), bool(sec))


class EvidenceTraceTest(unittest.TestCase):
    """The document's load-bearing citations resolve, so it cannot rot silently."""

    def test_d1_still_carries_ac01(self) -> None:
        payload = json.loads(
            (ROOT / "docs/scrna/node_support_findings.json").read_text(encoding="utf-8")
        )
        ac01 = payload["alias_classes"]["AC01"]
        self.assertEqual(ac01["class_verdict"], "alias_challenged")
        provenance = ac01["decision_provenance"]
        self.assertEqual(provenance["depends_on_deviations"], ["D1"])
        self.assertEqual(
            provenance["counterfactual_verdict_without_D1"],
            "unclassified_by_section_5_4",
        )
        self.assertEqual(
            provenance["raw_layer_sensitivity"]["condition_entanglement_status"],
            "resolved_for_PAEP_HBEGF_only",
        )

    def test_the_two_unread_epithelial_inputs_are_still_unread(self) -> None:
        """They are what a real repair would use, and why it would cost no node."""
        rules = parse_bnd_rules(resolve_model(GUARDED_MODELS[1], ROOT).network_bnd)
        for target in ("IN_HCG", "IN_EMBRYO_CONDITIONED_SIGNAL"):
            readers = [
                node
                for node, logic in rules.items()
                if node != target and re.search(rf"\b{target}\b", logic)
            ]
            with self.subTest(input=target):
                self.assertEqual(readers, [])

    def test_the_verification_ledger_exists_and_does_not_hold_ref_059(self) -> None:
        """U3's section 4a, pinned, because both halves are load-bearing.

        The ledger section 5(1) names is real and review-scoped; REF-059 has no
        row in it, which is why section 5(1) is NOT satisfied for the hCG
        candidate. A future round that adds a REF-059 row to make U3's paperwork
        tidy would be fabricating the provenance section 5(1) exists to require,
        so the absence is asserted rather than left implicit.
        """
        import csv

        ledger = (
            ROOT
            / "context/literature/reviews"
            / "deep_research_drug_targets_2026-09-16.primary-verification.tsv"
        )
        self.assertTrue(ledger.is_file(), "the ledger section 5(1) names is missing")
        with ledger.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))

        # The seven rows U3 read. They must stay; the ledger is NOT frozen at
        # seven, because U4 is told it may append its own genuine verification
        # rows to this same file. A legitimate append must not fail U3.
        present = {r["finding_id"] for r in rows}
        self.assertLessEqual(U3_BASELINE_LEDGER_ROWS, present)
        self.assertNotIn(
            "REF-059",
            " ".join(r["ref_id"] for r in rows),
            "REF-059 acquired a verification row. If that verification is "
            "genuine, the U3 finding must be revised first -- its section 5(1) "
            "verdict turns on the absence. If it was added to tidy U3's "
            "paperwork, it fabricates the provenance the criterion exists to "
            "require.",
        )
        self.assertFalse(
            (ROOT / "context/literature/primary-verification.tsv").exists()
        )

    def test_paep_is_part_of_the_construction_composite_it_would_be_tuned_against(
        self,
    ) -> None:
        """Section 5 of the finding: why E_PAEP cannot take a derived determinant."""
        import csv

        with (ROOT / "config/scrna_observation_map.tsv").open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = {r["model_node"]: r for r in csv.DictReader(handle, delimiter="\t")}
        features = rows["E_SECRETORY_STATE"]["measurement_features"].split(";")
        self.assertIn("PAEP", features)
        self.assertIn(
            "construction", rows["E_SECRETORY_STATE"]["claim_ceiling"].lower()
        )


if __name__ == "__main__":
    unittest.main()
