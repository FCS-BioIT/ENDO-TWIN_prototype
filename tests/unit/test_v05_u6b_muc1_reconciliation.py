"""U6b guards: the E_MUC1_BARRIER rule family is evaluated, measured, and NOT adopted.

`docs/v05_mechanistic_integration_plan.md` §17 U6b and register row `TI-02` ask
for the family over the clearance determinant, each member's structural,
endpoint and identifiability consequences, the naive sign flip measured before it
is refused, and the evidence record -- with no `network.bnd` written. `TI-06`,
the executable correction, stays deferred on conditions this unit does not move.

What these tests hold, and why each exists:

* the committed artifacts regenerate byte for byte, so no number in the record
  is hand-typed;
* the model is untouched and no version was created, which is the unit's whole
  boundary;
* the family is the one the plan pre-registered, and no member is labelled as
  licensed -- structural gain and biological licensing are separate axes;
* each headline claim in the record follows from the recomputation rather than
  being asserted beside it.

None of this adjudicates biology. The licensing statuses are copied from the
registered evidence wording (`PIF-008`, `PIF-009`, `GAP-004`, `GAP-011`) and the
tests only check they were not upgraded.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting.u6b_muc1_family import (
    CATALOG_STATUSES,
    ELEMENTS_TSV,
    ENDPOINTS_TSV,
    FROZEN_ARM_ID,
    MEMBERS,
    MEMBERS_TSV,
    MODEL,
    OUTPUT_DIR,
    RULE_ELEMENTS,
    RULE_VARIANTS_TSV,
    SUMMARY_JSON,
    build,
    member_rules,
)

RECORD = ROOT / "docs/v05_u6b_muc1_reconciliation.md"
REGISTER = ROOT / "docs/deferred_topology_register.tsv"
NETWORK = ROOT / "models/superset" / MODEL / "network.bnd"

#: sha256 of TI-06's `unblock_conditions` as the register held it before U6b
#: (main @ 8bc581d). U6b meets condition (1) and moves none of the three; a change
#: to this text is a TI-06 decision, not a U6b one.
TI06_CONDITIONS_SHA256 = (
    "278464c82e96f996646d0858e0975f67b6d03d11fe94ffb67c4f44dc8bf1c513"
)

#: Statuses that would mean the evidence chose a member. None may appear.
LICENSED_WORDS = re.compile(r"\b(?:LICENSED|ADOPTED|CANONICAL|PROMOTE)\b")


def _tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class U6bFamilyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.outputs = build(ROOT)
        cls.summary = json.loads(cls.outputs[SUMMARY_JSON])
        cls.members = {r["member_id"]: r for r in _tsv(ROOT / MEMBERS_TSV)}
        cls.endpoints = _tsv(ROOT / ENDPOINTS_TSV)
        cls.catalog = _tsv(ROOT / RULE_VARIANTS_TSV)

    def _endpoint(self, member: str, condition: str, node: str) -> set[float]:
        return {
            float(r[node])
            for r in self.endpoints
            if r["member_id"] == member and r["condition"] == condition
        }

    # ---- provenance ------------------------------------------------------

    def test_committed_outputs_regenerate_byte_for_byte(self) -> None:
        for path, text in self.outputs.items():
            with self.subTest(path=str(path)):
                self.assertEqual((ROOT / path).read_text(encoding="utf-8"), text)

    def test_every_output_lives_under_the_unit_directory(self) -> None:
        for path in self.outputs:
            self.assertEqual(path.parent, OUTPUT_DIR)

    # ---- the unit's boundary ---------------------------------------------

    def test_v051_still_carries_the_committed_rule_and_conjunct(self) -> None:
        text = NETWORK.read_text(encoding="utf-8")
        self.assertIn(
            "Node E_MUC1_BARRIER {\n  logic = not E_SECRETORY_STATE;\n}", text
        )
        self.assertIn("and not E_MUC1_BARRIER and", text)
        for added in ("E_MUC1_ABUNDANCE", "E_MUC1_LOCAL_CLEARANCE"):
            self.assertNotIn(added, text)

    def test_no_model_version_was_created(self) -> None:
        """U6b is evaluation only: no model version was emitted by it.

        Later versions are allowed (dt_adoc.closure_replay). Each must name a
        generator other than U6b's in its own provenance.
        """
        import tomllib

        versions = sorted(p.name for p in (ROOT / "models/superset").iterdir())
        self.assertIn(MODEL, versions)
        for later in versions[versions.index(MODEL) + 1 :]:
            with self.subTest(version=later):
                record = tomllib.loads(
                    (ROOT / "models/superset" / later / "provenance.toml").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertNotIn("u6b", record["generator_module"])

    def test_the_input_digest_matches_the_committed_network(self) -> None:
        recorded = self.summary["inputs"][f"models/superset/{MODEL}/network.bnd"]
        self.assertEqual(recorded, hashlib.sha256(NETWORK.read_bytes()).hexdigest())

    # ---- the family is the one pre-registered ---------------------------

    def test_the_family_carries_every_determinant_the_plan_requires(self) -> None:
        clearance = {
            m.member_id: m.additions.get("E_MUC1_LOCAL_CLEARANCE") for m in MEMBERS
        }
        self.assertEqual(clearance["A-SEC"], "IN_EMBRYO_CONTACT")
        self.assertEqual(
            clearance["B-SEC"], "IN_EMBRYO_CONTACT and IN_TROPHECTODERM_COMPETENT"
        )
        self.assertEqual(clearance["C-SEC"], "E_MUC1_LOCAL_CLEARANCE")
        self.assertEqual(
            {m.member_id for m in MEMBERS},
            {"V0", "P0", "N1", "N2"}
            | {f"{f}-{d}" for f in "ABC" for d in ("SEC", "PGR")},
        )

    def test_no_member_and_no_element_is_labelled_as_licensed(self) -> None:
        for member in MEMBERS:
            with self.subTest(member=member.member_id):
                self.assertIsNone(
                    LICENSED_WORDS.search(member.licensing.replace("UNLICENSED", ""))
                )
        for element in RULE_ELEMENTS:
            with self.subTest(element=element.element_id):
                self.assertIsNone(
                    LICENSED_WORDS.search(
                        element.evidence_status.replace("UNLICENSED", "")
                    )
                )

    def test_the_catalog_uses_the_model_rule_variants_schema(self) -> None:
        """Plan §17 U6b: the unlicensed family "goes to rule_variants.tsv".

        For an evaluation-only unit that is the U6b catalog, in the exact schema
        of the model file (read, never written), so a later TI-06 version can
        transcribe rows without reshaping them.
        """
        model_catalog = ROOT / "models/superset" / MODEL / "rule_variants.tsv"
        with model_catalog.open(encoding="utf-8") as handle:
            model_header = handle.readline().rstrip("\n").split("\t")
        with (ROOT / RULE_VARIANTS_TSV).open(encoding="utf-8") as handle:
            header = handle.readline().rstrip("\n").split("\t")
        self.assertEqual(header, model_header)

    def test_no_catalog_row_can_be_read_as_an_adopted_rule(self) -> None:
        self.assertEqual(CATALOG_STATUSES, {"reference_only", "catalog_only"})
        for row in self.catalog:
            with self.subTest(variant=row["variant_id"], node=row["node_id"]):
                self.assertIn(row["status"], CATALOG_STATUSES)
                self.assertEqual(row["default_in_family"], "false")
                self.assertTrue(row["evidence_ids"])
                self.assertTrue(row["notes"].startswith("EVALUATION ONLY"))
                self.assertEqual(row["source_table"], str(MEMBERS_TSV))

    def test_the_catalog_holds_exactly_each_members_rules(self) -> None:
        base = parse_bnd_rules(NETWORK)
        seen = set()
        for member in MEMBERS:
            rules = member_rules(member, base)
            expected = {
                n: rules[n]
                for n in (
                    "E_RECEPTIVE_SURFACE",
                    "E_MUC1_BARRIER",
                    "E_MUC1_ABUNDANCE",
                    "E_MUC1_LOCAL_CLEARANCE",
                )
                if n in rules
            }
            rows = [r for r in self.catalog if r["source_row_id"] == member.member_id]
            with self.subTest(member=member.member_id):
                self.assertEqual(
                    {r["node_id"]: r["expression"] for r in rows}, expected
                )
                self.assertEqual(len({r["variant_id"] for r in rows}), 1)
                status = (
                    "reference_only"
                    if member.role in ("reference", "control")
                    else "catalog_only"
                )
                self.assertEqual({r["status"] for r in rows}, {status})
            seen.update((r["variant_id"], r["node_id"]) for r in rows)
        self.assertEqual(len(seen), len(self.catalog))

    def test_member_rules_are_tabulated_in_one_file_only(self) -> None:
        """The owner asked for no duplicated representation of the family."""
        header = (ROOT / MEMBERS_TSV).read_text(encoding="utf-8").splitlines()[0]
        for column in header.split("\t"):
            self.assertFalse(column.startswith("rule_E_"), column)
        self.assertNotIn("\texpression\t", header)

    def test_added_nodes_are_not_classified_through_the_missing_row_default(
        self,
    ) -> None:
        """Added under review: with no dictionary row, the unresolved clearance
        state fell through to the empty proxy and was counted as an interface
        placeholder. It must carry explicit metadata and be latent_biological."""
        for member in ("C-SEC", "C-PGR"):
            block = self.summary["members"][member]
            with self.subTest(member=member):
                self.assertEqual(
                    block["design_alias"]["as_declared"]["category_of_added_nodes"][
                        "E_MUC1_LOCAL_CLEARANCE"
                    ],
                    "latent_biological",
                )
                self.assertEqual(
                    block["design_alias"]["as_declared"]["categories"][
                        "interface_placeholder"
                    ],
                    self.summary["members"]["V0"]["design_alias"]["as_declared"][
                        "categories"
                    ]["interface_placeholder"],
                )
        for member in MEMBERS:
            if member.additions:
                self.assertEqual(
                    self.summary["members"][member.member_id]["identifiability"][
                        "assayable_added_nodes"
                    ],
                    sorted(member.additions),
                )

    def test_every_recorded_input_digest_matches_the_tree(self) -> None:
        for path, digest in self.summary["inputs"].items():
            with self.subTest(path=path):
                self.assertEqual(
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest
                )
        self.assertIn(
            f"models/superset/{MODEL}/node_dictionary.tsv", self.summary["inputs"]
        )

    def test_the_input_digests_cover_the_condition_cfgs(self) -> None:
        inputs = self.summary["inputs"]
        for cfg in (ROOT / "models/superset" / MODEL / "conditions").glob("*.cfg"):
            self.assertIn(str(cfg.relative_to(ROOT)), inputs)

    def test_the_contact_and_competence_elements_stay_unlicensed(self) -> None:
        status = {e.element_id: e.evidence_status for e in RULE_ELEMENTS}
        self.assertEqual(status["RE-05"], "UNLICENSED_SPATIAL_ASSOCIATION")
        self.assertEqual(status["RE-06"], "UNLICENSED_STRESS_TEST")
        self.assertEqual(status["RE-08"], "REFUSED_BY_SOURCE")

    def test_every_member_element_is_defined_and_tabulated(self) -> None:
        defined = {e.element_id for e in RULE_ELEMENTS}
        tabulated = {r["element_id"] for r in _tsv(ROOT / ELEMENTS_TSV)}
        self.assertEqual(defined, tabulated)
        for member in MEMBERS:
            self.assertTrue(set(member.elements) <= defined)

    # ---- the committed graph --------------------------------------------

    def test_the_barrier_has_exactly_two_readers(self) -> None:
        self.assertEqual(
            self.summary["readers_of_barrier_in_model"],
            ["E_RECEPTIVE_SURFACE", "X_ANTIADHESIVE_ROUTE"],
        )

    def test_placement_alone_is_a_boolean_identity(self) -> None:
        p0 = self.summary["members"]["P0"]
        self.assertEqual(p0["blast_radius"], [])
        self.assertEqual(self.summary["contrasts"]["V0|P0"]["conditions_differing"], [])

    def test_the_reference_is_the_35_function_baseline(self) -> None:
        self.assertEqual(self.members["V0"]["distinct_functions"], "35")
        self.assertEqual(
            self.members["V0"]["barrier_alias_class_after"],
            "E_DAG1_FULL;E_MUC1_BARRIER;E_PODXL",
        )

    # ---- the naive flip, measured before refusal ------------------------

    def test_the_flip_in_place_makes_the_epithelial_phenotype_unsatisfiable(
        self,
    ) -> None:
        unsat = set(self.members["N1"]["unsatisfiable_nodes"].split(";"))
        self.assertTrue(
            {"E_RECEPTIVE_SURFACE", "OUT_EPITHELIAL_RECEPTIVE", "OUT_STABLE_ADHESION"}
            <= unsat
        )

    def test_the_interface_flip_turns_the_route_into_its_placeholder(self) -> None:
        self.assertEqual(self.members["N2"]["unsatisfiable_nodes"], "")
        self.assertIn(
            "X_ANTIADHESIVE_ROUTE;X_INTERFACE_ANTIADHESIVE_RELAY",
            self.members["N2"]["alias_classes_formed"],
        )
        # The endpoint drops by exactly the hand-set relay prior.
        self.assertEqual(
            self._endpoint(
                "N2", "adhesion_challenge_hormone_treated", "OUT_STABLE_ADHESION"
            ),
            {round(0.82 * (1 - 0.20), 6)},
        )

    # ---- endpoints -------------------------------------------------------

    def test_contact_bearing_members_leave_the_adhesion_endpoint_untouched(
        self,
    ) -> None:
        for member in ("A-SEC", "A-PGR", "B-SEC", "B-PGR"):
            row = self.members[member]
            with self.subTest(member=member):
                self.assertEqual(
                    row["barrier_on_when_stable_adhesion_is_evaluable"], "false"
                )
                self.assertNotIn(
                    "OUT_STABLE_ADHESION", row["composed_function_changed_nodes"]
                )
                watched = self.summary["contrasts"].get(f"V0|{member}", {})
                self.assertEqual(watched["watched_nodes_differing_by_condition"], {})

    def test_contact_bearing_members_make_maternal_competence_contact_dependent(
        self,
    ) -> None:
        self.assertEqual(
            self._endpoint(
                "V0", "hormone_treated_maternal", "OUT_MATERNAL_ADHESION_COMPETENCE"
            ),
            {0.82},
        )
        self.assertEqual(
            self._endpoint(
                "A-SEC", "hormone_treated_maternal", "OUT_MATERNAL_ADHESION_COMPETENCE"
            ),
            {0.656},
        )
        self.assertEqual(
            self._endpoint(
                "A-SEC",
                "adhesion_challenge_hormone_treated",
                "OUT_MATERNAL_ADHESION_COMPETENCE",
            ),
            {0.82},
        )

    def test_the_competence_conjunct_is_invisible_to_every_readout(self) -> None:
        contrast = self.summary["contrasts"]["A-SEC|B-SEC"]
        self.assertEqual(contrast["conditions_differing"], ["embryo_incompetent"])
        self.assertEqual(contrast["watched_nodes_differing_by_condition"], {})

    def test_no_measurement_separates_the_abundance_drivers(self) -> None:
        for family in "ABC":
            contrast = self.summary["contrasts"][f"{family}-SEC|{family}-PGR"]
            with self.subTest(family=family):
                self.assertEqual(contrast["conditions_differing"], [FROZEN_ARM_ID])
                self.assertEqual(contrast["watched_nodes_differing_by_condition"], {})

    def test_only_the_unresolved_member_is_separated_on_a_measured_node(self) -> None:
        """The record's separability claim, checked against every contrast.

        Added under review, which found the record claiming that no arm
        separates ANY two members while the artifact showed `C` at clearance
        OFF moving `OUT_STABLE_ADHESION`. Every reported pair is checked: a pair
        involving a `C` member may differ on a watched node, and then only on
        the adhesion endpoint; every other pair may not differ on one at all.
        """
        for pair, contrast in self.summary["contrasts"].items():
            hits = contrast["watched_nodes_differing_by_condition"]
            involves_c = any(m.startswith("C-") for m in pair.split("|"))
            naive = any(m in ("N1", "N2") for m in pair.split("|"))
            with self.subTest(pair=pair):
                if naive:
                    continue
                if involves_c and not pair.startswith("C-SEC|C-PGR"):
                    self.assertTrue(hits)
                    self.assertEqual(
                        {n for nodes in hits.values() for n in nodes},
                        {"OUT_STABLE_ADHESION"},
                    )
                else:
                    self.assertEqual(hits, {})
        # At clearance ON, C cannot be told from A in any condition.
        for condition in {r["condition"] for r in self.endpoints}:
            on = [
                r
                for r in self.endpoints
                if r["member_id"] == "C-SEC"
                and r["condition"] == condition
                and r["unprioritised_setting"] == "E_MUC1_LOCAL_CLEARANCE=1"
            ]
            a = [
                r
                for r in self.endpoints
                if r["member_id"] == "A-SEC" and r["condition"] == condition
            ]
            with self.subTest(condition=condition):
                self.assertEqual(
                    on[0]["OUT_STABLE_ADHESION"], a[0]["OUT_STABLE_ADHESION"]
                )

    def test_the_frozen_arm_moves_abundance_and_barrier_but_not_the_route(
        self,
    ) -> None:
        for family in "ABC":
            contrast = self.summary["contrasts"][f"{family}-SEC|{family}-PGR"]
            with self.subTest(family=family):
                self.assertEqual(
                    contrast["shared_nodes_differing_by_condition"][FROZEN_ARM_ID],
                    ["E_MUC1_ABUNDANCE", "E_MUC1_BARRIER"],
                )

    def test_the_unresolved_placeholder_is_reported_as_bounds_not_averaged(
        self,
    ) -> None:
        settings = {
            r["unprioritised_setting"]
            for r in self.endpoints
            if r["member_id"] == "C-SEC"
        }
        self.assertEqual(
            settings, {"E_MUC1_LOCAL_CLEARANCE=0", "E_MUC1_LOCAL_CLEARANCE=1"}
        )
        self.assertEqual(
            self._endpoint(
                "C-SEC", "adhesion_challenge_hormone_treated", "OUT_STABLE_ADHESION"
            ),
            {0.656, 0.82},
        )

    # ---- structural costs reported with the gains -----------------------

    def test_every_split_separates_the_barrier_and_enlarges_an_alias(self) -> None:
        for family in "ABC":
            for driver in ("SEC", "PGR"):
                row = self.members[f"{family}-{driver}"]
                with self.subTest(member=f"{family}-{driver}"):
                    self.assertEqual(
                        row["barrier_alias_verdict"], "SEPARATED_TO_SINGLETON"
                    )
                    self.assertIn(
                        "E_MUC1_ABUNDANCE:", row["alias_enlarged_by_new_nodes"]
                    )

    def test_the_naive_flips_only_move_the_alias(self) -> None:
        for member in ("N1", "N2"):
            self.assertEqual(
                self.members[member]["barrier_alias_verdict"], "MOVED_TO_ANOTHER_ALIAS"
            )

    def test_every_interface_candidate_wakes_the_antiadhesive_placeholder(self) -> None:
        for member in MEMBERS:
            if member.member_id in ("V0", "P0", "N1"):
                continue
            with self.subTest(member=member.member_id):
                self.assertIn(
                    "X_INTERFACE_ANTIADHESIVE_RELAY",
                    self.members[member.member_id]["inert_lost"],
                )

    def test_design_blocks_carry_the_matched_unit_caveat(self) -> None:
        for member_id, block in self.summary["members"].items():
            with self.subTest(member=member_id):
                self.assertIn(
                    "MATCHED-UNIT", block["identifiability"]["matched_unit_caveat"]
                )
                self.assertIn(
                    "MATCHED-UNIT", block["design_alias"]["matched_unit_caveat"]
                )

    # ---- the record agrees with the artifact ----------------------------

    def test_the_record_structure_table_matches_the_artifact(self) -> None:
        text = RECORD.read_text(encoding="utf-8")
        section = text.split("### 5.1 Structure")[1].split("\n\n", 2)[1]
        rows = [ln for ln in section.splitlines() if ln.startswith("| `")]
        self.assertEqual(len(rows), len(MEMBERS))
        for line in rows:
            cells = [c.strip() for c in line.strip("|").split("|")]
            member = self.members[cells[0].strip("`")]
            with self.subTest(member=cells[0]):
                self.assertEqual(cells[1], member["licensing"])
                self.assertEqual(cells[2], member["nodes"])
                self.assertEqual(cells[3], member["free_variables"])
                delta = int(member["delta_distinct_functions_vs_v051"])
                self.assertEqual(
                    cells[4], f"{member['distinct_functions']} ({delta:+d})"
                )
                self.assertEqual(cells[5], member["barrier_alias_verdict"])
                self.assertEqual(cells[6], member["phenotype_inert_nodes"])
                changed = member["composed_function_changed_nodes"]
                self.assertEqual(
                    int(cells[7]), len(changed.split(";")) if changed else 0
                )
                self.assertEqual(
                    cells[8],
                    " / ".join(
                        member[k]
                        for k in (
                            "design_effective_states_recorded",
                            "design_effective_states_as_declared_plan",
                            "design_effective_states_maternal_phase_only",
                        )
                    ),
                )

    def test_the_record_states_that_no_rule_is_licensed(self) -> None:
        text = " ".join(RECORD.read_text(encoding="utf-8").replace("*", "").split())
        self.assertIn("No canonical executable rule is licensed.", text)


class U6bRegisterTest(unittest.TestCase):
    def _row(self, increment: str) -> dict[str, str]:
        return next(r for r in _tsv(REGISTER) if r["increment_id"] == increment)

    def test_ti_02_is_discharged_by_u6b(self) -> None:
        row = self._row("TI-02")
        self.assertEqual(row["state"], "DISCHARGED")
        self.assertEqual(row["scheduled_unit"], "U6b")
        self.assertIn(
            "docs/v05_u6b_muc1_reconciliation.md", row["structural_effect_source"]
        )

    def test_ti_06_stays_deferred_on_unchanged_conditions(self) -> None:
        row = self._row("TI-06")
        self.assertEqual(row["state"], "DEFERRED")
        self.assertEqual(row["scheduled_unit"], "")
        self.assertEqual(
            hashlib.sha256(row["unblock_conditions"].encode("utf-8")).hexdigest(),
            TI06_CONDITIONS_SHA256,
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
