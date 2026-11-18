"""The register of outstanding topology obligations, guarded.

Why this file exists, stated plainly, because a guard nobody understands gets
deleted: between 2026-09-22 and 2026-09-23 five topology increments were ordered
in `docs/prl_igfbp1_foxo1_evidence_registration_2026-09-22.md` section 6 -- four
of them rule-level -- and three of those appeared in no scheduled unit of
`docs/v05_mechanistic_integration_plan.md` section 17. They had not been decided
against; they had been recorded in a dated evidence document and then not picked
up. Prose cannot notice that happening. This can.

What is asserted here is deliberately structural rather than scientific. The
register may not silently lose a row; a row may not claim a unit that does not
exist; a deferred row may not sit there with no stated way out; and each row's
`source_claim` must still be present, once markdown emphasis is stripped, in the
document it cites. None of that adjudicates any biology, and none of it should
ever be a reason to change a disposition.

Not every row is an obligation. `TI-03`, `TI-04` and `TI-06` are outstanding work;
`TI-01` was outstanding and is `DISCHARGED` by U5b, and `TI-02` by U6b (an
evaluation, which is why its executable half `TI-06` is still owed); `TI-05` is a scoped closure
record that owes nothing and is carried so a later unit can see what the closure
did and did not settle. `state` carries those distinctions and the
plan and roadmap use the same vocabulary, so a phase gate reading this register
can tell unfinished work from retained history.

Two limits, stated so nobody reads more assurance into this module than it gives.
`forcing_evidence` is free prose and is **not** checked against its source -- only
`source_claim` is -- so a row can still describe its evidence loosely and pass.
And `test_every_cited_derivation_artifact_exists` checks that a cited artifact
exists, not that it contains the number the row quotes; that gap is why the
count-bearing rows are constrained separately below.
"""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path
from types import MappingProxyType

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs" / "deferred_topology_register.tsv"
PLAN = ROOT / "docs" / "v05_mechanistic_integration_plan.md"
ROADMAP = ROOT / "docs" / "roadmap.md"
DISPOSITIONS = (
    ROOT
    / "context"
    / "literature"
    / "reviews"
    / "deep_research_adhesion_model_2026-09-11.candidate-node-dispositions.tsv"
)

#: Every row the register carries, pinned as a set so that deleting one fails
#: here rather than passing quietly -- which is the whole point. Two kinds live
#: in this set and must not be read alike: OUTSTANDING obligations, and scoped
#: CLOSURE records that owe no work and are kept for what they did not settle.
#: `state` is what tells them apart.
EXPECTED_IDS = {"TI-01", "TI-02", "TI-03", "TI-04", "TI-05", "TI-06"}

#: Outstanding: work is owed, either scheduled to a unit or deferred behind
#: conditions.
OUTSTANDING_STATES = {"SCHEDULED", "DEFERRED"}

#: Closed: the row is a scope record, not an obligation.
CLOSURE_STATES = {"CLOSED_ON_CURRENT_EVIDENCE"}

#: Discharged: the work WAS owed and has been done, by the unit the row names.
#: Kept apart from `CLOSURE_STATES` on purpose. A closure record never owed
#: anything, whereas a discharged row is an obligation that ended, and a later
#: unit needs to know which increment carried it out and where the result is.
#: First used by U5b for `TI-01`.
DISCHARGED_STATES = {"DISCHARGED"}

STATES = OUTSTANDING_STATES | CLOSURE_STATES | DISCHARGED_STATES

COLUMNS = (
    "increment_id",
    "what_changes",
    "state",
    "scheduled_unit",
    "forcing_evidence",
    "structural_effect",
    "structural_effect_source",
    "unblock_conditions",
    "unblock_locus",
    "source_document",
    "source_claim",
    "first_deferred",
)


def _rows() -> list[dict[str, str]]:
    with REGISTER.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _plain(text: str) -> str:
    """Markdown emphasis removed, so a claim can be quoted without its markup.

    Backticks and asterisks only. Underscores are left alone deliberately: they
    are inside identifiers here -- `CLOSED_ON_CURRENT_EVIDENCE`,
    `E_MUC1_BARRIER` -- and stripping them would make this helper compare
    mangled names and pass on strings nobody wrote.
    """
    return re.sub(r"[`*]", "", text)


class RegisterShapeTest(unittest.TestCase):
    def test_the_register_exists_with_the_declared_columns(self) -> None:
        self.assertTrue(REGISTER.is_file(), f"missing register: {REGISTER}")
        with REGISTER.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle, delimiter="\t"))
        self.assertEqual(tuple(header), COLUMNS)

    def test_no_obligation_disappears(self) -> None:
        """The assertion this module is named for."""
        self.assertEqual({row["increment_id"] for row in _rows()}, EXPECTED_IDS)

    def test_every_state_is_from_the_closed_vocabulary(self) -> None:
        for row in _rows():
            with self.subTest(row=row["increment_id"]):
                self.assertIn(row["state"], STATES)

    def test_every_row_says_what_changes_and_what_forces_it(self) -> None:
        for row in _rows():
            with self.subTest(row=row["increment_id"]):
                self.assertTrue(row["what_changes"].strip())
                self.assertTrue(row["forcing_evidence"].strip())
                self.assertTrue(row["first_deferred"].strip())


class StructuralClaimLineageTest(unittest.TestCase):
    """A published structural count must be reconstructable from a committed object.

    Added under external review, which found this register publishing exact node,
    function and alias-class counts for a variant that existed nowhere in the
    repository -- and which the plan itself described as unadopted. The numbers
    were additionally stale: computed for a two-node sketch while the plan
    proposed three nodes. Nothing could have caught that, because nothing tied a
    number to the thing that generates it.

    The rule enforced here is narrow and mechanical: any row whose
    `structural_effect` states a count must cite artifacts that exist, and a row
    for an unadopted variant must not state one at all.
    """

    #: A number followed by a word this project uses for a structural quantity, or
    #: an arrow between two counts. Deliberately crude -- it should over-match
    #: rather than let a bare number through. **Spelled-out numerals are included
    #: because the first version of this pattern matched digits only, and the
    #: defect it failed to catch was the word "Six".**
    WORD_NUMBER = (
        r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
        r"thirteen|fourteen"
    )
    COUNT = re.compile(
        r"\b\d+\s*(?:->|→)\s*\d+\b"
        rf"|\b(?:\d+|{WORD_NUMBER})\s+(?:nodes?|distinct|functions?|free)\b",
        re.IGNORECASE,
    )

    #: A claim of the form "<number> of the fourteen candidates ...", which is the
    #: shape that went wrong: a count asserted about the dispositions table rather
    #: than read from it.
    CANDIDATE_COUNT = re.compile(
        rf"\b(?:\d+|{WORD_NUMBER})\s+of\s+the\s+(?:\d+|{WORD_NUMBER})\b",
        re.IGNORECASE,
    )

    def test_every_cited_derivation_artifact_exists(self) -> None:
        for row in _rows():
            sources = row["structural_effect_source"]
            with self.subTest(row=row["increment_id"]):
                self.assertTrue(sources.strip(), "a structural claim needs a source")
                paths = re.findall(r"[\w./-]+\.(?:md|tsv|json|bnd|yaml)", sources)
                self.assertTrue(paths, f"no artifact named in: {sources}")
                for path in paths:
                    self.assertTrue(
                        (ROOT / path).exists(), f"cited artifact missing: {path}"
                    )

    def test_an_unadopted_variant_publishes_no_count(self) -> None:
        """TI-02's rules are proposed, so TI-02 may not carry derived counts."""
        row = next(r for r in _rows() if r["increment_id"] == "TI-02")
        found = self.COUNT.findall(row["structural_effect"])
        self.assertEqual(
            found, [], f"TI-02 publishes counts for an unadopted variant: {found}"
        )

    def test_the_candidate_closure_row_asserts_no_tally_of_its_own(self) -> None:
        """TI-05 may characterise the dispositions table; it may not count it.

        Added under external review, which found TI-05 claiming "six of the
        fourteen" enlarge an alias class. The cited `structural_result` column
        supports no such figure -- at least seven candidates record an
        enlargement, the boundary depends on which form counts as staged, and the
        "six" in the cited closure document counts a different set entirely
        (candidates with a defensible node and a rejected encoding, a tally its
        own section 7 has since moved to seven). A number that is an
        interpretation must not be published as a measurement.
        """
        row = next(r for r in _rows() if r["increment_id"] == "TI-05")
        found = self.CANDIDATE_COUNT.findall(row["structural_effect"])
        self.assertEqual(found, [], f"TI-05 publishes a candidate tally: {found}")

    def test_the_qualitative_enlargement_claim_is_not_vacuous(self) -> None:
        """Removing the count must not leave a claim with nothing behind it."""
        with DISPOSITIONS.open(newline="", encoding="utf-8") as handle:
            results = [
                row["structural_result"]
                for row in csv.DictReader(handle, delimiter="\t")
            ]
        pairs = re.compile(r"\b(\d+)\s*(?:->|→)\s*(\d+)\b")
        enlarging = [
            text
            for text in results
            # 35 is the distinct-function baseline, not an alias-class size.
            if any(
                int(b) > int(a) and "35" not in (a, b) for a, b in pairs.findall(text)
            )
        ]
        self.assertGreaterEqual(len(enlarging), 2)

    def test_the_plan_does_not_publish_counts_for_the_unadopted_split(self) -> None:
        plan = PLAN.read_text(encoding="utf-8")
        block = plan.split("**U6b — ")[-1].split("\n**U7 — ")[0]
        self.assertEqual(
            self.COUNT.findall(block),
            [],
            "the U6b block publishes a structural count for an unadopted variant",
        )


class ScheduledRowsTest(unittest.TestCase):
    def test_a_scheduled_row_names_a_unit_that_section_17_actually_defines(
        self,
    ) -> None:
        plan = PLAN.read_text(encoding="utf-8")
        for row in _rows():
            if row["state"] != "SCHEDULED":
                continue
            unit = row["scheduled_unit"]
            with self.subTest(row=row["increment_id"]):
                self.assertTrue(unit, "a scheduled row must name its unit")
                self.assertIsNotNone(
                    re.search(rf"^\*\*{re.escape(unit)} — ", plan, re.MULTILINE),
                    msg=f"section 17 defines no unit block for {unit}",
                )

    def test_only_scheduled_rows_claim_a_unit(self) -> None:
        for row in _rows():
            if row["state"] == "DEFERRED":
                with self.subTest(row=row["increment_id"]):
                    self.assertEqual(row["scheduled_unit"], "")


class DeferredRowsTest(unittest.TestCase):
    def test_a_deferred_row_states_how_it_could_ever_be_unblocked(self) -> None:
        """A deferral with no stated exit is indistinguishable from a silent drop."""
        for row in _rows():
            if row["state"] != "DEFERRED":
                continue
            with self.subTest(row=row["increment_id"]):
                conditions = row["unblock_conditions"].strip()
                self.assertTrue(conditions)
                self.assertTrue(row["unblock_locus"].strip())
                # Numbered, because "more evidence" is not an unblock condition.
                self.assertRegex(conditions, r"\(1\)")

    def test_the_de_aliasing_row_still_depends_on_the_leakage_repair(self) -> None:
        """The sequencing constraint the 2026-09-22 registration section 6 sets."""
        row = next(r for r in _rows() if r["increment_id"] == "TI-04")
        self.assertIn("TI-01", row["unblock_conditions"])


class DerivedEnumerationTest(unittest.TestCase):
    """Lists the register restates by hand are checked against their source.

    Three review rounds found the same defect in three places: a list in this
    register or in plan section 18 that restates something enumerable -- the
    readers of a node, the items of a source section -- and restates it
    incompletely. The earlier guards check that a cited artifact *exists*; they
    cannot check that the row *accounts for all of it*. These two do, for the two
    lists where the defect actually occurred.

    Both are consistency checks and nothing more. Neither asserts anything about
    biology, modelling, experiments or when an obligation may be lifted: they
    compare text in the register against text derived from a committed artifact,
    and they fail when the register omits an item the artifact contains.
    """

    NETWORK = (
        ROOT / "models" / "superset" / "adoc-literature-superset-v0.5.0" / "network.bnd"
    )
    GATE3A = ROOT / "docs" / "v05_u2_gate3a_blocked.md"
    SPLIT_NODE = "E_ITGAVB3_5"

    @staticmethod
    def _rules(path: Path) -> dict[str, str]:
        text = path.read_text(encoding="utf-8")
        found = {}
        for match in re.finditer(r"Node\s+(\w+)\s*\{(.*?)\}", text, re.DOTALL):
            logic = re.search(r"logic\s*=\s*(.*?);", match.group(2), re.DOTALL)
            if logic:
                found[match.group(1)] = " ".join(logic.group(1).split())
        return found

    def _readers_of(self, node: str) -> set[str]:
        return {
            name
            for name, logic in self._rules(self.NETWORK).items()
            if name != node and re.search(rf"\b{re.escape(node)}\b", logic)
        }

    def _section_4a_items(self) -> list[str]:
        section = self.GATE3A.read_text(encoding="utf-8")
        section = section.split("### 4a.")[1].split("### 4b.")[0]
        return re.split(r"^\d+\.\s+", section, flags=re.MULTILINE)[1:]

    @staticmethod
    def _content_tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9][a-z0-9-]{5,}", _plain(text).lower()))

    def test_ti_03_accounts_for_every_reader_of_the_node_it_would_split(self) -> None:
        readers = self._readers_of(self.SPLIT_NODE)
        self.assertGreaterEqual(len(readers), 2, "derivation found too few readers")
        row = next(r for r in _rows() if r["increment_id"] == "TI-03")
        conditions = row["unblock_conditions"]
        for reader in sorted(readers):
            with self.subTest(reader=reader):
                self.assertIn(
                    reader,
                    conditions,
                    f"TI-03 does not account for {reader}, which reads "
                    f"{self.SPLIT_NODE} in the committed network",
                )

    def test_the_plan_accounts_for_every_reader_too(self) -> None:
        """Section 18 restates TI-03, so the same omission can happen there."""
        plan = PLAN.read_text(encoding="utf-8")
        block = plan.split("### TI-03 — ")[1].split("\n### ")[0]
        for reader in sorted(self._readers_of(self.SPLIT_NODE)):
            with self.subTest(reader=reader):
                self.assertIn(reader, block)

    def test_ti_04_preserves_every_numbered_item_of_section_4a(self) -> None:
        """Each source item must leave a trace that is unique to it.

        The limit, stated so the guard is not read as more than it is: a token
        unique to one item proves that item is *represented*, not that it is
        represented faithfully. What it does catch is the defect that occurred --
        an item dropped entirely, which leaves none of its tokens behind.
        """
        items = self._section_4a_items()
        self.assertEqual(len(items), 3, "section 4a no longer has three items")
        tokens = [self._content_tokens(item) for item in items]
        conditions = next(r for r in _rows() if r["increment_id"] == "TI-04")[
            "unblock_conditions"
        ].lower()
        for index, item in enumerate(items):
            others = set().union(*[t for j, t in enumerate(tokens) if j != index])
            unique = tokens[index] - others
            self.assertTrue(unique, f"item {index + 1} has no distinctive token")
            with self.subTest(item=index + 1, lead=item.strip()[:48]):
                self.assertTrue(
                    unique & set(re.findall(r"[a-z0-9][a-z0-9-]{5,}", conditions)),
                    f"TI-04 carries no trace of section 4a item {index + 1}",
                )

    def test_ti_04_lists_as_many_measurement_items_as_the_source_does(self) -> None:
        row = next(r for r in _rows() if r["increment_id"] == "TI-04")
        listed = re.findall(r"\((i{1,3}|iv)\)", row["unblock_conditions"])
        self.assertEqual(len(listed), len(self._section_4a_items()))


class SourceClaimTest(unittest.TestCase):
    def test_every_cited_document_exists_and_still_carries_its_claim(self) -> None:
        for row in _rows():
            document = ROOT / row["source_document"]
            with self.subTest(row=row["increment_id"]):
                self.assertTrue(document.is_file(), f"missing: {document}")
                self.assertIn(
                    _plain(row["source_claim"]),
                    _plain(document.read_text(encoding="utf-8")),
                )


class PlanAndRoadmapAgreeTest(unittest.TestCase):
    def test_section_18_lists_exactly_the_registered_ids(self) -> None:
        plan = PLAN.read_text(encoding="utf-8")
        section = plan.split("## 18. Outstanding topology obligations")[-1]
        self.assertEqual(set(re.findall(r"TI-\d{2}", section)), EXPECTED_IDS)

    def test_section_18_states_the_same_state_for_each_row(self) -> None:
        plan = PLAN.read_text(encoding="utf-8")
        section = plan.split("## 18. Outstanding topology obligations")[-1]
        for row in _rows():
            with self.subTest(row=row["increment_id"]):
                # The table row, not any prose that happens to name the id --
                # an earlier version took the first matching line and started
                # reading a paragraph once section 18 gained explanatory text.
                line = next(
                    ln
                    for ln in section.splitlines()
                    if ln.lstrip().startswith("|") and row["increment_id"] in ln
                )
                self.assertIn(row["state"], _plain(line))

    def test_the_roadmap_points_at_the_register(self) -> None:
        self.assertIn(
            "docs/deferred_topology_register.tsv",
            ROADMAP.read_text(encoding="utf-8"),
        )


class ClosureScopeTest(unittest.TestCase):
    """TI-05 is closed for one adjudication, not for all future admission."""

    def test_the_candidate_closure_row_records_zero_promotions(self) -> None:
        with DISPOSITIONS.open(newline="", encoding="utf-8") as handle:
            dispositions = [
                row["final_disposition"]
                for row in csv.DictReader(handle, delimiter="\t")
            ]
        self.assertEqual(len(dispositions), 14)
        self.assertNotIn("PROMOTE", dispositions)
        row = next(r for r in _rows() if r["increment_id"] == "TI-05")
        self.assertEqual(row["state"], "CLOSED_ON_CURRENT_EVIDENCE")

    def test_the_closure_is_scoped_rather_than_standing(self) -> None:
        row = next(r for r in _rows() if r["increment_id"] == "TI-05")
        conditions = row["unblock_conditions"]
        self.assertIn("re-adjudication", conditions)
        self.assertIn("not a standing bar", conditions)


class NoExecutableChangeTest(unittest.TestCase):
    """This planning change touches no model file.

    Narrow by design: it reads the two committed supersets' rules and asserts the
    obligations registered here have NOT been carried out, because carrying them
    out is a separate reviewed unit. U5b has landed: it emitted v0.5.1 and the
    assertion is re-pointed below, so the repaired version is held to TI-01 and
    nothing else. The v0.4.0 and v0.5.0 rules are audited objects and are
    expected to keep failing to change forever.
    """

    AUDITED = (
        "models/superset/adoc-literature-superset-v0.4.0",
        "models/superset/adoc-literature-superset-v0.5.0",
    )

    #: The version U5b emitted to discharge TI-01. The re-point the docstring
    #: promised: the audited versions keep their assertions unchanged, and the
    #: repaired version is held to carrying out TI-01 and nothing else.
    REPAIRED = "models/superset/adoc-literature-superset-v0.5.1"

    #: Discharged rows and the unit that discharged each. TI-01 by an executable
    #: repair (U5b, v0.5.1); TI-02 by an evaluation that changed no model file
    #: (U6b), so its executable half stays outstanding as TI-06.
    DISCHARGED_BY = MappingProxyType({"TI-01": "U5b", "TI-02": "U6b"})

    def test_the_audited_versions_still_carry_the_unrepaired_rules(self) -> None:
        for model in self.AUDITED:
            text = (ROOT / model / "network.bnd").read_text(encoding="utf-8")
            with self.subTest(model=model):
                self.assertIn("logic = S_DECIDUALIZED and S_PRL and S_IGFBP1;", text)
                self.assertIn("logic = not E_SECRETORY_STATE;", text)
                self.assertIn("logic = E_LIF or E_HBEGF or E_SECRETORY_STATE;", text)

    def test_the_repaired_version_discharges_ti_01_and_only_ti_01(self) -> None:
        text = (ROOT / self.REPAIRED / "network.bnd").read_text(encoding="utf-8")
        self.assertIn(
            "Node OUT_STROMAL_DECIDUALIZED {\n  logic = S_DECIDUALIZED;\n}", text
        )
        self.assertNotIn("S_DECIDUALIZED and S_PRL and S_IGFBP1", text)
        # TI-02/TI-06 (MUC1), TI-03 (integrin) and TI-04 (marker de-aliasing)
        # are NOT carried out by it.
        self.assertIn("logic = not E_SECRETORY_STATE;", text)
        self.assertIn("logic = E_LIF or E_HBEGF or E_SECRETORY_STATE;", text)
        self.assertIn("Node S_PRL {\n  logic = S_DECIDUALIZED;\n}", text)
        self.assertIn("Node S_IGFBP1 {\n  logic = S_DECIDUALIZED;\n}", text)
        row = next(r for r in _rows() if r["increment_id"] == "TI-01")
        self.assertEqual(row["state"], "DISCHARGED")
        self.assertEqual(row["scheduled_unit"], "U5b")
        for row in _rows():
            if row["increment_id"] not in self.DISCHARGED_BY:
                with self.subTest(row=row["increment_id"]):
                    self.assertNotIn(row["state"], DISCHARGED_STATES)

    def test_every_discharged_row_names_the_unit_that_discharged_it(self) -> None:
        """TI-02 is discharged by U6b as an EVALUATION: nothing executable moved.

        That is why the MUC1 assertions above are unchanged for v0.5.1 -- the
        committed rule is still `not E_SECRETORY_STATE` -- and why TI-06, the
        executable half, must still be outstanding.
        """
        for increment, unit in self.DISCHARGED_BY.items():
            row = next(r for r in _rows() if r["increment_id"] == increment)
            with self.subTest(row=increment):
                self.assertEqual(row["state"], "DISCHARGED")
                self.assertEqual(row["scheduled_unit"], unit)
        ti06 = next(r for r in _rows() if r["increment_id"] == "TI-06")
        self.assertIn(ti06["state"], OUTSTANDING_STATES)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
