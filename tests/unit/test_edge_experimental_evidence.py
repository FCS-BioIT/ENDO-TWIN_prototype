"""The canonical per-experiment evidence table and its validator.

``context/evidence/edge_experimental_evidence.tsv`` is the one place a curator's
claim-level judgement about an experiment will live, and
``dt_adoc.evidence.experimental`` is the only writer. Three failure modes would
be silent and are therefore tested directly:

* a rebuild losing or renaming curation, which would make curating a paper
  pointless (the defect the v0.3.0 table's merge contract exists to prevent);
* a grade exceeding what its own axes record -- in particular non-human or
  cell-line evidence passing as human primary evidence;
* a generated column drifting from the model, the roles or the bibliography it
  is derived from, so the table describes an edge the network does not compute.

Every assertion here is about behaviour, not about how many rows happen to be
curated. Curation is arriving in batches, so no test encodes a count; what is
asserted is the invariant that survives every batch -- an unreviewed row
carries no assessment, and an examined one carries a complete, internally
consistent set.
"""

from __future__ import annotations

import copy
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.evidence import experimental as ex

#: A fully specified examined row, used as the base for the grading tests. It is
#: deliberately the strongest shape the rubric allows, so each test weakens one
#: axis and nothing else.
EXAMINED = {
    "source_location": "Fig. 1a",
    "source_verification": "full_text_verified",
    "species": "human",
    "experimental_model": "primary_culture",
    "cell_source": "donor_derived_primary",
    "cell_line": "not_applicable",
    "cell_type": "endometrial stromal",
    "experiment_type": "knockdown",
    "perturbation": "siRNA against the regulator",
    "perturbation_direction": "decrease",
    "measured_effect": "target transcript moves as the edge claims",
    "response_direction": "decrease",
    "readout_quantitation": "quantitative",
    "functional_endpoint": "protein expression",
    "controls": "scrambled siRNA",
    "rescue_experiment": "rescue",
    "biological_replicates": "3",
    "experimental_limitations": "one donor pool",
    "experimental_strength": "strong",
    "human_ADOC_relevance": "direct",
    "edge_support": "direct",
    "overall_confidence": "high",
    "confidence_rationale": "siRNA of the regulator lowers the encoded target.",
    "limitations_rationale": "Single laboratory; no independent replication.",
    "curation_status": "verified",
    "curated_on": "2026-11-16",
}


def built() -> list[dict[str, str]]:
    return ex.build_table([])


def examined(
    rows: list[dict[str, str]], index: int = 0, **overrides: str
) -> list[dict[str, str]]:
    """Copy ``rows`` with one row turned into an examined row.

    ``perturbation_target`` defaults to whatever a direct perturbation of that
    row's own edge source would have to name, so a test that is not about the
    target does not have to think about it.
    """
    rows = copy.deepcopy(rows)
    rows[index].update(EXAMINED)
    rows[index]["perturbation_target"] = default_target(rows[index])
    # Consistent with whatever sign this row's edge carries, so a test about
    # something else is not accidentally a direction test.
    rows[index]["response_direction"] = (
        "decrease" if rows[index]["sign"] == "activation" else "increase"
    )
    rows[index].update(overrides)
    return rows


def default_target(row: dict[str, str]) -> str:
    """What a direct perturbation of this edge's source would have to name."""
    role = ex.load_roles().get(row["edge_id"], {}).get("edge_role", "")
    if role == "external_input":
        return row["source"]
    declared = sorted(ex.node_entities().get(row["source"], set()))
    return declared[0] if declared else ""


def row_index(rows: list[dict[str, str]], edge_id: str) -> int:
    return next(i for i, row in enumerate(rows) if row["edge_id"] == edge_id)


def errors_for(rows: list[dict[str, str]]) -> list[str]:
    return ex.validate_rows(rows).errors


class CommittedTable(unittest.TestCase):
    def test_the_committed_table_is_current_and_valid(self) -> None:
        self.assertEqual(ex.check(), [])

    def test_an_unreviewed_row_carries_no_grade(self) -> None:
        # A grade requires an examined row, and the two states are visibly
        # distinct in the committed table: `unreviewed` everywhere means
        # `unassessed`, so no row can look graded without having been read.
        rows = ex.load_table()
        self.assertTrue(rows)
        for row in rows:
            if row["curation_status"] == "unreviewed":
                self.assertEqual(
                    {row[column] for column in ex.ASSESSMENT_COLUMNS},
                    {"unassessed"},
                    f"{row['evidence_piece_id']} is unreviewed but carries an assessment",
                )

    def test_the_table_is_lf_and_has_the_declared_columns(self) -> None:
        for path in (ex.EVIDENCE_TABLE_PATH, ex.EDGE_ROLES_PATH):
            raw = (ROOT / path).read_bytes()
            self.assertNotIn(b"\r", raw, f"{path} must stay LF")
        self.assertEqual(list(ex.load_table()[0]), list(ex.COLUMNS))

    def test_the_commands_the_guide_documents_exist(self) -> None:
        pixi = (ROOT / "pixi.toml").read_text(encoding="utf-8")
        doc = (ROOT / "docs/evidence_grading.md").read_text(encoding="utf-8")
        for task in ("build-edge-evidence", "check-edge-evidence"):
            self.assertIn(f"[tasks.{task}]", pixi)
            self.assertIn(f"pixi run {task}", doc)

    def test_check_runs_as_a_module_and_writes_nothing(self) -> None:
        before = (ROOT / ex.EVIDENCE_TABLE_PATH).read_bytes()
        completed = subprocess.run(
            [sys.executable, "-B", "-m", "dt_adoc.evidence.experimental", "check"],
            cwd=ROOT,
            env={
                "PYTHONPATH": "src",
                "PATH": "/usr/bin:/bin",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual((ROOT / ex.EVIDENCE_TABLE_PATH).read_bytes(), before)


class RebuildPreservesCuration(unittest.TestCase):
    def test_rebuilding_is_idempotent(self) -> None:
        once = built()
        twice = ex.build_table(once)
        self.assertEqual(
            ex.render_tsv(once, ex.COLUMNS),
            ex.render_tsv(twice, ex.COLUMNS),
            "a second build changed the table",
        )

    def test_a_rebuild_keeps_every_curated_cell(self) -> None:
        curated = examined(built(), 0)
        expected = {column: curated[0][column] for column in ex.CURATED_COLUMNS}
        rebuilt = ex.build_table(curated)
        row = next(
            r
            for r in rebuilt
            if r["evidence_piece_id"] == expected["evidence_piece_id"]
        )
        self.assertEqual(
            {column: row[column] for column in ex.CURATED_COLUMNS}, expected
        )

    def test_a_rebuild_drops_no_row_and_adds_the_missing_seeds(self) -> None:
        full = built()
        rebuilt = ex.build_table(full[5:])
        self.assertEqual(
            {row["evidence_piece_id"] for row in rebuilt},
            {row["evidence_piece_id"] for row in full},
            "seeds are not restored, or rows were dropped",
        )

    def test_a_second_experiment_from_one_paper_survives_a_rebuild(self) -> None:
        rows = built()
        first = next(row for row in rows if row["reference_id"])
        extra = dict(first)
        extra["evidence_piece_id"] = ex.piece_id(
            first["edge_id"], first["reference_id"], 2
        )
        extra["migrated_from"] = ""
        extra["source_location"] = "Fig. 4c"
        rebuilt = ex.build_table([*rows, extra])
        self.assertIn(
            extra["evidence_piece_id"], {row["evidence_piece_id"] for row in rebuilt}
        )
        # Both rows of one paper stay one study, and the table still validates.
        self.assertEqual(errors_for(rebuilt), [])

    def test_rows_are_written_in_canonical_order(self) -> None:
        rows = built()
        self.assertEqual(errors_for(rows), [])
        swapped = [rows[1], rows[0], *rows[2:]]
        self.assertTrue(
            any("canonical order" in error for error in errors_for(swapped))
        )


class Lineage(unittest.TestCase):
    def test_every_migrated_parent_resolves(self) -> None:
        parents = ex.v030_assertion_ids()
        self.assertTrue(parents)
        for row in ex.load_table():
            value = row["migrated_from"]
            if value.startswith("ASRT-"):
                self.assertIn(
                    value, parents, f"{row['evidence_piece_id']} names a missing parent"
                )

    def test_an_edge_absent_from_v030_is_seeded_not_invented(self) -> None:
        # LE096 entered the family at v0.4.0, so the v0.3.0 paper-level table
        # has no assertion for it; its rows must say so rather than name one.
        rows = [row for row in ex.load_table() if row["edge_id"] == "LE096"]
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row["migrated_from"], f"seeded:{ex.DEFAULT_MODEL_VERSION}")

    def test_every_seed_is_present_with_its_own_lineage(self) -> None:
        rows = {row["evidence_piece_id"]: row for row in ex.load_table()}
        seeds = ex.migration_seeds()
        self.assertTrue(seeds)
        for seed in seeds:
            self.assertIn(seed.piece_id, rows)
            self.assertEqual(rows[seed.piece_id]["migrated_from"], seed.migrated_from)

    def test_a_lineage_that_is_not_this_seeds_own_is_rejected(self) -> None:
        for corrupt in (
            "ASRT-LE999-REF-001",  # no such assertion
            "seeded:adoc-literature-superset-v0.6.0",  # a real parent exists
            "migrated by hand",  # not a lineage at all
        ):
            with self.subTest(migrated_from=corrupt):
                rows = copy.deepcopy(built())
                row = next(r for r in rows if r["migrated_from"].startswith("ASRT-"))
                row["migrated_from"] = corrupt
                self.assertTrue(
                    any(
                        "is not the lineage of this seed" in error
                        for error in errors_for(rows)
                    )
                )

    def test_a_parent_from_another_edge_is_rejected(self) -> None:
        rows = copy.deepcopy(built())
        other = next(
            r
            for r in rows
            if r["edge_id"] != rows[0]["edge_id"]
            and r["migrated_from"].startswith("ASRT-")
        )
        rows[0]["migrated_from"] = other["migrated_from"]
        self.assertTrue(
            any(
                "is not the lineage of this seed" in error for error in errors_for(rows)
            )
        )

    def test_a_row_that_is_not_a_seed_may_not_claim_lineage(self) -> None:
        # REF-070 is in the bibliography but is in no edge's fan-out, so a row
        # citing it on LE001 is a curator's addition and was never migrated.
        rows = copy.deepcopy(built())
        fabricated = dict(rows[0])
        fabricated.update(
            {
                "edge_id": "LE001",
                "evidence_piece_id": ex.piece_id("LE001", "REF-070", 1),
                "reference_id": "REF-070",
                "source_observation_id": "",
                "independence_group": "REF-070",
                "migrated_from": f"seeded:{ex.DEFAULT_MODEL_VERSION}",
            }
        )
        rows = ex.build_table([*rows, fabricated])
        self.assertTrue(
            any("is not a migration seed" in error for error in errors_for(rows))
        )

    def test_a_missing_seed_is_restored_even_beside_a_curator_row(self) -> None:
        # A second row for the same paper must not stand in for the seed: the
        # seed carries the lineage, and keying restoration on (edge, source)
        # silently dropped it.
        full = built()
        seed = ex.migration_seeds()[0]
        extra = dict(next(r for r in full if r["evidence_piece_id"] == seed.piece_id))
        extra["evidence_piece_id"] = ex.piece_id(seed.edge_id, seed.source_id, 2)
        extra["migrated_from"] = ""
        without_seed = [r for r in full if r["evidence_piece_id"] != seed.piece_id]
        rebuilt = ex.build_table([*without_seed, extra])
        restored = next(r for r in rebuilt if r["evidence_piece_id"] == seed.piece_id)
        self.assertEqual(restored["migrated_from"], seed.migrated_from)
        self.assertEqual(errors_for(rebuilt), [])

    def test_a_missing_seed_is_reported_by_validation(self) -> None:
        rows = built()
        seed = ex.migration_seeds()[0]
        self.assertTrue(
            any(
                "is missing; rebuild the table" in error
                for error in errors_for(
                    [r for r in rows if r["evidence_piece_id"] != seed.piece_id]
                )
            )
        )


class TheCeilingHoldsAcrossTheWholeTable(unittest.TestCase):
    """No graded row may claim more confidence than its three axes allow.

    The per-row rule is tested elsewhere on constructed values; this applies it
    to every row actually committed, which is what an import round can break.
    """

    def test_no_row_exceeds_its_own_ceiling(self) -> None:
        for row in ex.load_table():
            if row["curation_status"] == "unreviewed":
                continue
            ceiling = ex.confidence_ceiling(
                row["experimental_strength"],
                row["human_ADOC_relevance"],
                row["edge_support"],
            )
            with self.subTest(piece=row["evidence_piece_id"]):
                self.assertLessEqual(
                    ex.CONFIDENCE_RANK[row["overall_confidence"]],
                    ex.CONFIDENCE_RANK[ceiling],
                    f"{row['evidence_piece_id']} claims "
                    f"{row['overall_confidence']} above its ceiling {ceiling}",
                )

    def test_no_row_in_the_table_is_high(self) -> None:
        """As of the 2026-11-18 review no evidence piece anywhere reaches
        `high`. If one ever does it is a reviewed decision, not a drift."""
        high = [
            r["evidence_piece_id"]
            for r in ex.load_table()
            if r["overall_confidence"] == "high"
        ]
        self.assertEqual(high, [])

    def test_a_derived_source_node_cannot_carry_direct_support(self) -> None:
        """Support through a proxy is `partial`. LE049's source is a derived
        state with no entity, so no evidence on it can ever be `direct`."""
        entities = ex.node_entities()
        contexts = ex.edge_context()
        for row in ex.load_table():
            if row["edge_support"] != "direct":
                continue
            source = contexts[row["edge_id"]].source
            role = ex.load_roles().get(row["edge_id"], {}).get("edge_role", "")
            if role == "external_input":
                continue
            with self.subTest(piece=row["evidence_piece_id"]):
                self.assertTrue(
                    entities.get(source),
                    f"{row['evidence_piece_id']} claims direct support for the "
                    f"derived source {source}, which has no entity",
                )


class AnAttachmentToAnInHouseSeededEdge(unittest.TestCase):
    """An `attach` directive must reach an edge whose seed is a SOFIA record.

    `migration_seeds` used to `continue` as soon as an edge's evidence id was a
    SOFIA in-house observation, which ended the edge before the citation
    adjudications were read. An `attach` naming such an edge was therefore
    discarded in silence -- and `check_applicability` had already accepted the
    same directive as valid and needed, because the register genuinely does not
    fan that reference out. The generator contradicted its own validator and
    the only symptom was a row that never appeared.

    LE049 is the live instance: its only seed is SOFIA-STR-001, and CIT-039
    attaches REF-016 to it.
    """

    def test_the_attachment_produces_a_seed(self) -> None:
        seeds = ex.migration_seeds()
        self.assertIn(
            ("LE049", "REF-016"),
            {(s.edge_id, s.reference_id) for s in seeds},
            "an attach to a SOFIA-seeded edge must still seed a row",
        )

    def test_the_in_house_seed_survives_beside_it(self) -> None:
        """The attachment adds to the edge, it does not displace the
        observation the edge was seeded from."""
        seeds = [s for s in ex.migration_seeds() if s.edge_id == "LE049"]
        self.assertIn("SOFIA-STR-001", {s.source_observation_id for s in seeds})
        self.assertIn("REF-016", {s.reference_id for s in seeds})

    def test_the_attached_row_exists_in_the_canonical_table(self) -> None:
        rows = {r["evidence_piece_id"] for r in ex.load_table()}
        self.assertIn("EVP-LE049-REF016-01", rows)

    def test_the_attached_row_is_seeded_not_migrated(self) -> None:
        """It has no v0.3.0 ancestor, so it must say `seeded:` rather than
        claim a parent assertion that never existed."""
        row = next(
            r
            for r in ex.load_table()
            if r["evidence_piece_id"] == "EVP-LE049-REF016-01"
        )
        self.assertEqual(row["migrated_from"], f"seeded:{ex.DEFAULT_MODEL_VERSION}")

    def test_a_retraction_still_applies_to_such_an_edge(self) -> None:
        """The same code path honours retractions; if it did not, a retracted
        citation could come back through an in-house-seeded edge."""
        import dt_adoc.evidence.experimental as module

        original = module.partition
        retracted = {("LE049", "REF-016")}

        def only_retract(adjudications):
            _, attachments = original(adjudications)
            return retracted, attachments

        module.partition = only_retract
        try:
            pairs = {(s.edge_id, s.reference_id) for s in ex.migration_seeds()}
        finally:
            module.partition = original
        self.assertNotIn(("LE049", "REF-016"), pairs)


class IndependenceGroups(unittest.TestCase):
    def test_one_publication_carries_one_group(self) -> None:
        self.assertEqual(ex.independence_errors(ex.load_table()), [])

    def test_two_groups_for_one_reference_are_rejected(self) -> None:
        rows = copy.deepcopy(built())
        same = [r for r in rows if r["reference_id"] == "REF-002"]
        self.assertGreaterEqual(len(same), 2)
        same[0]["independence_group"] = "AN-INDEPENDENT-STUDY"
        self.assertTrue(
            any(
                "one publication or observation is one study" in error
                for error in errors_for(rows)
            )
        )

    def test_two_groups_for_one_in_house_observation_are_rejected(self) -> None:
        # SOFIA-HT-001 appears on several edges. One observation is one study,
        # exactly as one paper is; keying the check on reference_id alone let
        # the in-house half through.
        rows = copy.deepcopy(built())
        same = [r for r in rows if r["source_observation_id"] == "SOFIA-HT-001"]
        self.assertGreaterEqual(len(same), 2)
        same[0]["independence_group"] = "AN-INDEPENDENT-OBSERVATION"
        self.assertTrue(
            any(
                "one publication or observation is one study" in error
                for error in errors_for(rows)
            )
        )

    def test_an_observation_is_checked_even_beside_a_reference_id(self) -> None:
        # Called directly, as the edge-level aggregation will call it. A row
        # carrying both ids is rejected elsewhere, so this function must not
        # rely on that: it counts every id present, not the first one.
        base = dict(ex.load_table()[0])
        rows = [
            {
                **base,
                "reference_id": "REF-023",
                "source_observation_id": "SOFIA-HT-001",
                "independence_group": "REF-023",
            },
            {
                **base,
                "reference_id": "REF-024",
                "source_observation_id": "SOFIA-HT-001",
                "independence_group": "REF-024",
            },
        ]
        messages = ex.independence_errors(rows)
        self.assertTrue(
            any("SOFIA-HT-001" in error for error in messages),
            f"the shared observation was not checked: {messages}",
        )

    def test_two_references_may_share_a_group(self) -> None:
        # The column exists so that one cohort reported in two papers counts
        # once; that direction stays allowed.
        rows = copy.deepcopy(built())
        for row in rows:
            if row["reference_id"] in ("REF-023", "REF-024"):
                row["independence_group"] = "SHARED-COHORT"
        self.assertEqual(ex.independence_errors(rows), [])

    def test_a_blank_group_is_rejected(self) -> None:
        rows = copy.deepcopy(built())
        rows[0]["independence_group"] = "   "
        self.assertTrue(
            any("independence_group is empty" in error for error in errors_for(rows))
        )

    def test_a_retracted_citation_cannot_bear_on_its_edge_either_way(self) -> None:
        # CIT-001 retracts REF-007 from LE017 on full-text absence: LIF occurs
        # nowhere in Apparao 2001. A paper that cannot support the relation
        # cannot contradict it either, and a contradiction weighs as much as
        # support in the edge-level rule.
        rows = copy.deepcopy(built())
        row = dict(rows[0])
        row.update(
            {
                "edge_id": "LE017",
                "evidence_piece_id": ex.piece_id("LE017", "REF-007", 1),
                "reference_id": "REF-007",
                "source_observation_id": "",
                "independence_group": "REF-007",
                "migrated_from": "",
            }
        )
        rows = ex.build_table([*rows, row])
        index = next(
            i
            for i, r in enumerate(rows)
            if r["evidence_piece_id"] == row["evidence_piece_id"]
        )
        for support, confidence in (
            ("direct", "high"),
            ("partial", "medium"),
            ("contradictory", "unsupported"),
        ):
            with self.subTest(edge_support=support):
                messages = errors_for(
                    examined(
                        rows,
                        index,
                        edge_support=support,
                        overall_confidence=confidence,
                    )
                )
                self.assertTrue(
                    any("is retracted from" in error for error in messages), messages
                )

    def test_a_retracted_citation_may_still_be_recorded_as_not_demonstrated(
        self,
    ) -> None:
        rows = copy.deepcopy(built())
        row = dict(rows[0])
        row.update(
            {
                "edge_id": "LE017",
                "evidence_piece_id": ex.piece_id("LE017", "REF-007", 1),
                "reference_id": "REF-007",
                "source_observation_id": "",
                "independence_group": "REF-007",
                "migrated_from": "",
            }
        )
        rows = ex.build_table([*rows, row])
        index = next(
            i
            for i, r in enumerate(rows)
            if r["evidence_piece_id"] == row["evidence_piece_id"]
        )
        self.assertEqual(
            errors_for(
                examined(
                    rows,
                    index,
                    edge_support="not_demonstrated",
                    overall_confidence="unsupported",
                    experimental_strength="insufficient",
                    rescue_experiment="not_applicable",
                    limitations_rationale="LIF is absent from the full text (CIT-001).",
                )
            ),
            [],
        )


class GeneratedColumnsFollowTheModel(unittest.TestCase):
    def test_the_active_edges_are_the_ones_the_network_computes(self) -> None:
        contexts = ex.edge_context()
        active = {c.edge_id for c in ex.active_edges(contexts)}
        rules = ex.parse_bnd_rules(
            ex.model_dir(ex.DEFAULT_MODEL_VERSION, ex.repo_root()) / "network.bnd"
        )
        self.assertEqual(len(active), len(ex.derive_dependencies(rules)))
        # The retired intervention-marker edges stay as history, unfiltered.
        retired = {c.edge_id for c in contexts.values() if c.edge_status == "retired"}
        self.assertLessEqual({"LE002", "LE038", "LE059", "LE096"}, retired)

    def test_every_active_edge_has_exactly_one_role_with_a_rationale(self) -> None:
        contexts = ex.edge_context()
        self.assertEqual(ex.validate_roles(ex.load_roles(), contexts), [])
        roles = ex.load_roles()
        self.assertEqual(set(roles), {c.edge_id for c in ex.active_edges(contexts)})

    def test_a_role_for_an_edge_the_model_does_not_compute_is_rejected(self) -> None:
        contexts = ex.edge_context()
        roles = dict(ex.load_roles())
        roles["LE999"] = {
            "edge_id": "LE999",
            "source": "A",
            "target": "B",
            "edge_role": "biological_regulatory",
            "rationale": "x",
        }
        self.assertTrue(
            any(
                "not an active edge" in error
                for error in ex.validate_roles(roles, contexts)
            )
        )

    def test_each_generated_column_is_checked_against_its_derivation(self) -> None:
        for column, corrupt in (
            ("source", "E_WRONG"),
            ("target", "E_WRONG"),
            (
                "sign",
                "inhibition" if built()[0]["sign"] == "activation" else "activation",
            ),
            ("boolean_rule", "A and B"),
            ("compartment", "nowhere"),
            ("edge_status", "retired"),
            ("edge_role", "structural_relay"),
            ("model_version", "adoc-literature-superset-v0.3.0"),
            ("publication", "Nobody 1999"),
            ("doi", "10.0000/fake"),
        ):
            with self.subTest(column=column):
                rows = copy.deepcopy(built())
                rows[0][column] = corrupt
                self.assertTrue(
                    any(
                        f"generated column {column}=" in error
                        for error in errors_for(rows)
                    ),
                    f"corrupting {column} was not detected",
                )

    def test_a_stale_committed_table_fails_the_currentness_check(self) -> None:
        rows = copy.deepcopy(built())
        rows[0]["publication"] = "Nobody 1999"
        self.assertNotEqual(
            ex.render_tsv(rows, ex.COLUMNS),
            ex.render_tsv(ex.build_table(rows), ex.COLUMNS),
            "a rebuild did not repair a corrupted generated column",
        )


class GradingCeilings(unittest.TestCase):
    def test_the_ceiling_table_matches_the_rubric(self) -> None:
        self.assertEqual(ex.confidence_ceiling("strong", "direct", "direct"), "high")
        self.assertEqual(
            ex.confidence_ceiling("strong", "indirect", "direct"), "medium"
        )
        self.assertEqual(ex.confidence_ceiling("strong", "direct", "partial"), "medium")
        self.assertEqual(ex.confidence_ceiling("weak", "direct", "direct"), "low")
        self.assertEqual(ex.confidence_ceiling("strong", "poor", "direct"), "low")
        self.assertEqual(
            ex.confidence_ceiling("insufficient", "direct", "direct"), "unsupported"
        )
        self.assertEqual(
            ex.confidence_ceiling("strong", "direct", "contradictory"), "unsupported"
        )
        self.assertEqual(
            ex.confidence_ceiling("strong", "direct", "not_demonstrated"), "unsupported"
        )

    def test_a_well_formed_examined_row_validates(self) -> None:
        self.assertEqual(errors_for(examined(built())), [])

    def test_a_grade_above_its_ceiling_is_rejected(self) -> None:
        rows = examined(
            built(),
            human_ADOC_relevance="indirect",
            species="mouse",
            cell_source="animal_in_vivo",
        )
        self.assertTrue(
            any("exceeds the ceiling" in error for error in errors_for(rows))
        )

    def test_mouse_in_vivo_evidence_tops_out_at_medium(self) -> None:
        rows = examined(
            built(),
            species="mouse",
            cell_source="animal_in_vivo",
            experimental_model="in_vivo",
            human_ADOC_relevance="indirect",
            overall_confidence="medium",
        )
        self.assertEqual(errors_for(rows), [])

    def test_an_unlisted_organism_is_rejected_rather_than_read_as_human(self) -> None:
        rows = examined(
            built(),
            species="rabbit",
            cell_source="animal_in_vivo",
            experimental_model="in_vivo",
        )
        messages = errors_for(rows)
        self.assertTrue(
            any(
                "requires every compartment to be human" in error for error in messages
            ),
            messages,
        )

    def test_an_organism_outside_the_vocabulary_is_an_error(self) -> None:
        rows = examined(built(), species="axolotl")
        self.assertTrue(
            any("is not '<organism>'" in error for error in errors_for(rows))
        )

    def test_a_heterologous_system_cannot_be_direct(self) -> None:
        rows = examined(built(), species="maternal: human; embryo: mouse")
        self.assertTrue(
            any(
                "requires every compartment to be human" in error
                for error in errors_for(rows)
            )
        )

    def test_a_heterologous_system_may_be_close(self) -> None:
        # Dominguez 2010's shape: human endometrial cells, mouse blastocysts.
        rows = examined(
            built(),
            species="maternal: human; embryo: mouse",
            human_ADOC_relevance="close",
            overall_confidence="medium",
        )
        self.assertEqual(errors_for(rows), [])

    def test_a_non_human_only_system_cannot_be_close(self) -> None:
        rows = examined(
            built(),
            species="baboon",
            cell_source="animal_in_vivo",
            experimental_model="in_vivo",
            human_ADOC_relevance="close",
            overall_confidence="medium",
        )
        self.assertTrue(
            any("requires a human compartment" in error for error in errors_for(rows))
        )

    def test_cancer_and_immortalized_lines_cannot_be_human_primary(self) -> None:
        for cell_source, relevance in (
            ("cancer_derived", "close"),
            ("immortalized_primary_like", "direct"),
        ):
            with self.subTest(cell_source=cell_source):
                rows = examined(
                    built(),
                    cell_source=cell_source,
                    experimental_model="cell_line",
                    cell_line="Ishikawa",
                    human_ADOC_relevance=relevance,
                    overall_confidence="medium",
                )
                self.assertTrue(
                    any("cannot have relevance" in error for error in errors_for(rows))
                )

    def test_a_contradiction_cannot_carry_a_positive_grade(self) -> None:
        rows = examined(built(), edge_support="contradictory", overall_confidence="low")
        self.assertTrue(
            any(
                "requires overall_confidence=unsupported" in error
                for error in errors_for(rows)
            )
        )


class ExaminationIsNotAssumed(unittest.TestCase):
    def test_an_unreviewed_row_may_not_carry_an_assessment(self) -> None:
        rows = copy.deepcopy(built())
        rows[0]["overall_confidence"] = "high"
        self.assertTrue(
            any("must leave every assessment" in error for error in errors_for(rows))
        )

    def test_an_examined_row_needs_both_rationales_and_a_location(self) -> None:
        for column in (
            "confidence_rationale",
            "limitations_rationale",
            "source_location",
            "curated_on",
        ):
            with self.subTest(column=column):
                rows = examined(built(), **{column: ""})
                self.assertTrue(
                    any(f"empty {column}" in error for error in errors_for(rows))
                )

    def test_a_grade_read_off_an_abstract_is_capped_at_low(self) -> None:
        rows = examined(
            built(), source_verification="abstract_only", curation_status="provisional"
        )
        messages = errors_for(rows)
        self.assertTrue(any("capped at 'low'" in error for error in messages), messages)

    def test_verified_requires_the_full_text(self) -> None:
        rows = examined(
            built(), source_verification="full_text_partial", overall_confidence="low"
        )
        self.assertTrue(
            any(
                "requires source_verification=full_text_verified" in error
                for error in errors_for(rows)
            )
        )

    def test_an_unavailable_source_cannot_be_graded(self) -> None:
        rows = examined(built(), source_verification="unavailable")
        self.assertTrue(
            any(
                "cannot have source_verification" in error for error in errors_for(rows)
            )
        )

    def test_an_examined_row_may_not_leave_the_experiment_blank(self) -> None:
        # The reviewer's counterexample: a verified, strong, direct, high row
        # describing no perturbation, no effect, no endpoint, no controls and
        # no replicate count.
        empty = dict.fromkeys(ex.DESCRIPTIVE_COLUMNS, "")
        messages = errors_for(examined(built(), **empty))
        for column in ex.DESCRIPTIVE_COLUMNS:
            self.assertTrue(
                any(f"leaves {column} blank" in error for error in messages),
                f"{column} was allowed to be blank",
            )

    def test_missingness_may_be_written_but_not_omitted(self) -> None:
        # A paper that does not state its replicate count can still be graded,
        # just not as `strong`, which requires reported replication.
        rows = examined(
            built(),
            experimental_strength="moderate",
            overall_confidence="medium",
            rescue_experiment="none",
            biological_replicates="not_reported",
            experimental_limitations="not_reported",
            limitations_rationale="Replicate count not stated; no specificity check.",
        )
        self.assertEqual(errors_for(rows), [])

    def test_strong_requires_every_documented_prerequisite(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        for overrides, expected in (
            ({"rescue_experiment": "none"}, "requires one of the specificity routes"),
            (
                {"rescue_experiment": "not_applicable"},
                "requires one of the specificity routes",
            ),
            ({"controls": "not_reported"}, "requires reported controls"),
            ({"controls": "none"}, "requires reported controls"),
            ({"controls": "N/A"}, "requires reported controls"),
            (
                {"readout_quantitation": "qualitative"},
                "requires a quantitative readout",
            ),
            (
                {"readout_quantitation": "not_reported"},
                "requires a quantitative readout",
            ),
            (
                {"biological_replicates": "not_reported"},
                "requires reported biological replication",
            ),
            (
                {"biological_replicates": "1"},
                "requires reported biological replication",
            ),
            (
                {"experiment_type": "immunostaining"},
                "requires a perturbation of the regulator",
            ),
        ):
            with self.subTest(**overrides):
                messages = errors_for(examined(rows, index, **overrides))
                self.assertTrue(any(expected in error for error in messages), messages)

    def test_every_documented_specificity_route_is_accepted(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        for route in ex.SPECIFICITY_ROUTES:
            with self.subTest(route=route):
                self.assertEqual(
                    errors_for(examined(rows, index, rescue_experiment=route)), []
                )

    def test_two_independent_reagents_need_no_rescue(self) -> None:
        # docs/evidence_grading.md section 3.1 lists this as a specificity
        # check in its own right; requiring a rescue on top downgraded it.
        rows = built()
        index = row_index(rows, "LE091")
        self.assertEqual(
            errors_for(
                examined(
                    rows,
                    index,
                    rescue_experiment="two_independent_reagents",
                    perturbation="two non-overlapping siRNAs against the regulator",
                    limitations_rationale="No rescue; two reagents instead.",
                )
            ),
            [],
        )

    def test_a_replicate_count_must_be_a_count(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            examined(rows, index, biological_replicates="three independent experiments")
        )
        self.assertTrue(
            any("is neither a count nor" in error for error in messages), messages
        )

    def test_direct_support_names_an_entity_of_the_edge_source(self) -> None:
        # LE091 is E_KLF12_HIGH -> E_LIF; the source stands for KLF12.
        rows = built()
        index = row_index(rows, "LE091")
        self.assertEqual(errors_for(examined(rows, index)), [])

    def test_a_proxy_perturbation_is_not_direct_support(self) -> None:
        # LE003 is E_PGR -> E_IHH. Treating cells with progesterone perturbs
        # the ligand, not the receptor node: the rubric calls that partial.
        rows = built()
        index = row_index(rows, "LE003")
        messages = errors_for(
            examined(
                rows,
                index,
                experiment_type="hormone_treatment",
                perturbation="progesterone 10 nM for 48 h",
                perturbation_target="progesterone",
            )
        )
        self.assertTrue(
            any("is not an entity of the edge source" in e for e in messages), messages
        )

    def test_perturbing_an_unrelated_gene_is_not_direct_support(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(examined(rows, index, perturbation_target="FOXO1"))
        self.assertTrue(
            any("is not an entity of the edge source" in e for e in messages), messages
        )

    def test_a_derived_source_cannot_carry_direct_support(self) -> None:
        # LE006 is E_SECRETORY_STATE -> E_PAEP. The source is a composite
        # state, so nothing in a laboratory is that node.
        rows = built()
        index = row_index(rows, "LE006")
        messages = errors_for(examined(rows, index, perturbation_target="PGR"))
        self.assertTrue(
            any("is not available for E_SECRETORY_STATE" in e for e in messages),
            messages,
        )

    def test_naming_the_derived_node_itself_is_also_refused(self) -> None:
        rows = built()
        index = row_index(rows, "LE006")
        messages = errors_for(
            examined(rows, index, perturbation_target="E_SECRETORY_STATE")
        )
        self.assertTrue(
            any("names the model node rather than a molecule" in e for e in messages),
            messages,
        )

    def test_an_input_edge_may_name_its_own_node(self) -> None:
        # LE001 is IN_PROGESTIN -> E_PGR: the input node is the manipulation.
        rows = built()
        index = row_index(rows, "LE001")
        self.assertEqual(
            errors_for(examined(rows, index, perturbation_target="IN_PROGESTIN")), []
        )

    def test_a_regulatory_node_may_not_be_named_as_its_own_perturbation(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(examined(rows, index, perturbation_target="E_KLF12_HIGH"))
        self.assertTrue(
            any("names the model node rather than a molecule" in e for e in messages),
            messages,
        )

    def test_a_missing_perturbation_target_blocks_direct_support(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        for value in ("", "not_reported"):
            with self.subTest(perturbation_target=value):
                messages = errors_for(examined(rows, index, perturbation_target=value))
                self.assertTrue(
                    any("requires perturbation_target to name" in e for e in messages),
                    messages,
                )

    def test_direct_support_requires_the_regulator_to_be_perturbed(self) -> None:
        messages = errors_for(
            examined(
                built(),
                experiment_type="expression_profiling",
                experimental_strength="weak",
                overall_confidence="low",
            )
        )
        self.assertTrue(
            any("requires the regulator itself to be perturbed" in e for e in messages),
            messages,
        )

    def test_an_observational_study_can_still_be_recorded_as_partial(self) -> None:
        rows = examined(
            built(),
            experiment_type="expression_profiling",
            experimental_strength="weak",
            edge_support="partial",
            overall_confidence="low",
            rescue_experiment="not_applicable",
        )
        self.assertEqual(errors_for(rows), [])

    def test_evidence_pointing_the_wrong_way_cannot_support_an_edge(self) -> None:
        # LE091 is E_KLF12_HIGH -| E_LIF. Knocking the inhibitor down must
        # RAISE LIF; a fall is evidence against the edge, not for it.
        rows = built()
        index = row_index(rows, "LE091")
        self.assertEqual(rows[index]["sign"], "inhibition")
        messages = errors_for(
            examined(
                rows,
                index,
                perturbation_direction="decrease",
                response_direction="decrease",
            )
        )
        self.assertTrue(
            any("recorded directions contradict the edge" in e for e in messages),
            messages,
        )

    def test_the_same_experiment_the_right_way_round_is_accepted(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        self.assertEqual(
            errors_for(
                examined(
                    rows,
                    index,
                    perturbation_direction="decrease",
                    response_direction="increase",
                )
            ),
            [],
        )

    def test_an_activation_edge_wants_the_directions_together(self) -> None:
        rows = built()
        index = row_index(rows, "LE001")
        self.assertEqual(rows[index]["sign"], "activation")
        messages = errors_for(
            examined(
                rows,
                index,
                perturbation_direction="increase",
                response_direction="decrease",
            )
        )
        self.assertTrue(
            any("recorded directions contradict the edge" in e for e in messages),
            messages,
        )

    def test_a_target_that_did_not_move_supports_nothing(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(examined(rows, index, response_direction="no_change"))
        self.assertTrue(any("supports no direction" in e for e in messages), messages)

    def test_a_contradiction_may_not_agree_with_the_edge(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            examined(
                rows,
                index,
                edge_support="contradictory",
                overall_confidence="unsupported",
                perturbation_direction="decrease",
                response_direction="increase",
            )
        )
        self.assertTrue(
            any("is not a contradiction of it" in e for e in messages), messages
        )

    def test_a_recorded_perturbation_must_say_which_way_it_went(self) -> None:
        # Both ways of recording "no direction" are refused. Excusing only
        # `not_examined` left `not_applicable` as a way out of the sign check,
        # because direction_errors reads both as nothing recorded.
        rows = built()
        index = row_index(rows, "LE091")
        for column in ("perturbation_direction", "response_direction"):
            for value in ("not_examined", "not_applicable"):
                with self.subTest(column=column, value=value):
                    messages = errors_for(examined(rows, index, **{column: value}))
                    self.assertTrue(
                        any(f"{column} must be one of" in e for e in messages),
                        messages,
                    )

    def test_a_knockdown_cannot_opt_out_of_the_direction_check(self) -> None:
        # The whole counterexample: verified, direct, strong, high, a real
        # KLF12 knockdown, and both directions declared inapplicable.
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            examined(
                rows,
                index,
                perturbation_direction="not_applicable",
                response_direction="not_applicable",
            )
        )
        self.assertTrue(
            any("must be one of" in e for e in messages),
            f"a perturbational direct-support row escaped the check: {messages}",
        )

    def test_strong_must_perturb_the_regulator_even_when_support_is_partial(
        self,
    ) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            examined(
                rows,
                index,
                edge_support="partial",
                overall_confidence="medium",
                perturbation_target="FOXO1",
            )
        )
        self.assertTrue(
            any("is not an entity of the edge source" in e for e in messages), messages
        )

    def test_observation_only_evidence_cannot_be_moderate_or_strong(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        for strength in ("moderate", "strong"):
            with self.subTest(strength=strength):
                messages = errors_for(
                    examined(
                        rows,
                        index,
                        experiment_type="expression_profiling",
                        experimental_strength=strength,
                        edge_support="partial",
                        overall_confidence="medium",
                        perturbation_direction="not_applicable",
                        response_direction="not_applicable",
                        rescue_experiment="not_applicable",
                    )
                )
                self.assertTrue(any("only observes" in e for e in messages), messages)

    def test_a_controlled_molecular_experiment_may_still_be_moderate(self) -> None:
        # The rubric allows ChIP, reporter and binding assays at `moderate`
        # without a functional perturbation; only association is capped.
        rows = built()
        index = row_index(rows, "LE091")
        self.assertEqual(
            errors_for(
                examined(
                    rows,
                    index,
                    experiment_type="chip",
                    experimental_strength="moderate",
                    edge_support="partial",
                    overall_confidence="medium",
                    perturbation_direction="not_applicable",
                    response_direction="not_applicable",
                    rescue_experiment="not_applicable",
                )
            ),
            [],
        )

    def test_an_incoherent_system_is_rejected(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            examined(
                rows,
                index,
                experimental_model="cell_line",
                cell_source="donor_derived_primary",
                cell_line="Ishikawa",
            )
        )
        self.assertTrue(
            any("is not donor-derived primary material" in e for e in messages),
            messages,
        )

    def test_direct_relevance_requires_a_donor_derived_system(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            examined(
                rows,
                index,
                experimental_model="cell_line",
                cell_source="immortalized_primary_like",
                cell_line="hTERT-EEC",
                human_ADOC_relevance="direct",
            )
        )
        self.assertTrue(
            any("requires a donor-derived system" in e for e in messages), messages
        )

    def test_mandatory_text_may_not_be_a_null_in_disguise(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        for column, value in (
            ("source_location", "not_reported"),
            ("confidence_rationale", "none"),
            ("limitations_rationale", "N/A"),
        ):
            with self.subTest(column=column):
                messages = errors_for(examined(rows, index, **{column: value}))
                self.assertTrue(
                    any(f"{column}=" in e and "asserts nothing" in e for e in messages),
                    messages,
                )

    def test_an_examined_row_may_not_leave_its_system_unexamined(self) -> None:
        rows = examined(built(), experiment_type="not_examined")
        self.assertTrue(
            any(
                "still has experiment_type=not_examined" in error
                for error in errors_for(rows)
            )
        )


class ACitationThatDoesNotTestItsEdge(unittest.TestCase):
    """``not_demonstrated`` is the one support value with no direction to state.

    The commonest audit finding is a paper that perturbs the regulator properly
    and never measures this edge's target: Chung 2016 raises LIF and assays
    integrins but never GP130 or phospho-STAT3; Heng 2011 silences PC5/6 and
    never assays dystroglycan. Those rows record a real perturbation, so the
    concreteness rule applied to them, and the only way to pass was to write a
    response direction for a measurement that was never made.
    """

    def _not_demonstrated(self, rows: list[dict[str, str]], index: int, **over: str):
        axes = {
            "edge_support": "not_demonstrated",
            "overall_confidence": "unsupported",
            "experimental_strength": "insufficient",
        }
        return examined(rows, index, **{**axes, **over})

    def test_an_untested_target_may_be_recorded_as_unmeasured(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        self.assertEqual(
            errors_for(
                self._not_demonstrated(
                    rows,
                    index,
                    perturbation_direction="decrease",
                    response_direction="not_examined",
                )
            ),
            [],
        )

    def test_an_unperturbed_regulator_may_be_recorded_as_inapplicable(self) -> None:
        # The mirror case: the paper perturbs something, but not this edge's
        # regulator, so neither direction describes anything.
        rows = built()
        index = row_index(rows, "LE091")
        self.assertEqual(
            errors_for(
                self._not_demonstrated(
                    rows,
                    index,
                    perturbation_direction="not_applicable",
                    response_direction="not_applicable",
                )
            ),
            [],
        )

    def test_the_exemption_reaches_no_grade(self) -> None:
        # Nothing can be bought with it: `not_demonstrated` is pinned to
        # `unsupported` whatever the other axes say.
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            self._not_demonstrated(
                rows,
                index,
                overall_confidence="medium",
                perturbation_direction="decrease",
                response_direction="not_examined",
            )
        )
        self.assertTrue(
            any("requires overall_confidence=unsupported" in e for e in messages),
            messages,
        )

    def test_supporting_grades_keep_the_requirement(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        for support, confidence in (("direct", "high"), ("partial", "medium")):
            with self.subTest(support=support):
                messages = errors_for(
                    examined(
                        rows,
                        index,
                        edge_support=support,
                        overall_confidence=confidence,
                        response_direction="not_examined",
                    )
                )
                self.assertTrue(
                    any("response_direction must be one of" in e for e in messages),
                    messages,
                )

    def test_a_contradiction_still_states_both_directions(self) -> None:
        # The case where direction carries the whole claim is deliberately not
        # exempt: "it went the other way" is unverifiable without saying which.
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            examined(
                rows,
                index,
                edge_support="contradictory",
                overall_confidence="unsupported",
                response_direction="not_examined",
            )
        )
        self.assertTrue(
            any("response_direction must be one of" in e for e in messages), messages
        )


class ASystemWithMoreThanOnePart(unittest.TestCase):
    """A co-culture and a two-experiment paper are not mislabelled cell lines.

    ``experimental_model`` and ``cell_source`` are multi-valued because the
    systems in this literature have several parts: a cancer line co-cultured
    with primary trophoblast spheroids, or immunostaining of donor tissue
    followed by an adhesion assay in Ishikawa cells. Rejecting every
    ``cell_line`` beside ``donor_derived_primary`` forced the primary half of
    those systems out of the record.
    """

    def test_a_coculture_may_name_a_line_and_primary_material(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        self.assertEqual(
            errors_for(
                examined(
                    rows,
                    index,
                    experimental_model="cell_line;assembloid_or_coculture",
                    cell_source="cancer_derived;donor_derived_primary",
                    cell_line="Ishikawa",
                    human_ADOC_relevance="indirect",
                    overall_confidence="medium",
                )
            ),
            [],
        )

    def test_a_single_line_still_cannot_be_donor_derived_primary(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            examined(
                rows,
                index,
                experimental_model="cell_line",
                cell_source="donor_derived_primary",
                cell_line="Ishikawa",
            )
        )
        self.assertTrue(
            any("is not donor-derived primary material" in e for e in messages),
            messages,
        )

    def test_a_multi_part_system_containing_a_line_still_cannot_climb(self) -> None:
        # The exemption must not become a route to human-primary relevance.
        rows = built()
        index = row_index(rows, "LE091")
        for relevance in ("direct", "close"):
            with self.subTest(relevance=relevance):
                messages = errors_for(
                    examined(
                        rows,
                        index,
                        experimental_model="cell_line;assembloid_or_coculture",
                        cell_source="cancer_derived;donor_derived_primary",
                        cell_line="Ishikawa",
                        human_ADOC_relevance=relevance,
                        overall_confidence="medium",
                    )
                )
                self.assertTrue(
                    any("cannot have relevance" in e for e in messages), messages
                )

    def test_a_line_source_still_has_to_name_the_line(self) -> None:
        rows = built()
        index = row_index(rows, "LE091")
        messages = errors_for(
            examined(
                rows,
                index,
                experimental_model="assembloid_or_coculture;primary_culture",
                cell_source="cancer_derived;donor_derived_primary",
                cell_line="Ishikawa",
                human_ADOC_relevance="indirect",
                overall_confidence="medium",
            )
        )
        self.assertTrue(
            any("requires experimental_model 'cell_line'" in e for e in messages),
            messages,
        )


if __name__ == "__main__":
    unittest.main()
