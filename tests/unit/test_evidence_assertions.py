from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.evidence.assertions import (
    ASSERTION_COLUMNS,
    CURATION_STATUS_VALUES,
    _paths,
    load_assertions,
    migrate_edge_evidence,
    validate_assertions,
)
from dt_adoc.evidence.citation_adjudications import (
    ADJUDICATION_COLUMNS,
    CitationAdjudicationError,
    check_applicability,
    load_citation_adjudications,
    partition,
)
from dt_adoc.model import superset_family
from dt_adoc.model.catalog import load_tsv
from dt_adoc.model.superset_family import write_family

MODEL_DIR = ROOT / "models" / "superset" / "adoc-literature-superset-v0.3.0"
EDGE_EVIDENCE_TSV = MODEL_DIR / "edge_evidence.tsv"
ASSERTIONS_TSV = MODEL_DIR / "edge_evidence_assertions.tsv"
REGISTER_TSV = ROOT / "context" / "evidence-register.tsv"
REFERENCES_TSV = ROOT / "context" / "literature" / "references.tsv"


def _write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _copy_real_sources(tmp_root: Path) -> None:
    """Mirror the real edge_evidence/register/references files into a
    tempdir tree so a test can corrupt a copy without touching the repo."""
    (tmp_root / EDGE_EVIDENCE_TSV.relative_to(ROOT)).parent.mkdir(
        parents=True, exist_ok=True
    )
    _write_tsv(
        tmp_root / EDGE_EVIDENCE_TSV.relative_to(ROOT), load_tsv(EDGE_EVIDENCE_TSV)
    )
    (tmp_root / REGISTER_TSV.relative_to(ROOT)).parent.mkdir(
        parents=True, exist_ok=True
    )
    _write_tsv(tmp_root / REGISTER_TSV.relative_to(ROOT), load_tsv(REGISTER_TSV))
    (tmp_root / REFERENCES_TSV.relative_to(ROOT)).parent.mkdir(
        parents=True, exist_ok=True
    )
    _write_tsv(tmp_root / REFERENCES_TSV.relative_to(ROOT), load_tsv(REFERENCES_TSV))


def _copy_migration_inputs(tmp_root: Path) -> None:
    """Copy, byte for byte, every file `migrate_edge_evidence` reads -- the
    committed assertions table included, since the migration merges its
    curator-owned fields back."""
    for source in _paths(ROOT).values():
        if source.exists():
            target = tmp_root / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)


class RealMigrationTests(unittest.TestCase):
    """Tests against the real, already-migrated repository file.

    Nothing here migrates the real file. That used to happen in setUpClass,
    which rewrote a stale committed table before any assertion read it, so the
    class passed on a table it had just repaired. Currency is checked on a copy
    instead (`test_committed_table_is_what_the_migration_produces`).
    """

    def test_all_93_edges_covered_with_at_least_93_assertions(self) -> None:
        edge_ids = {row["edge_id"] for row in load_tsv(EDGE_EVIDENCE_TSV)}
        self.assertEqual(len(edge_ids), 93)
        assertions = load_assertions(ROOT)
        self.assertGreaterEqual(len(assertions), 93)
        covered = {row["edge_id"] for row in assertions}
        self.assertEqual(covered, edge_ids)

    def test_multi_reference_lit_id_produces_one_assertion_per_reference(self) -> None:
        register = {row["evidence_id"]: row for row in load_tsv(REGISTER_TSV)}
        ref_ids = [
            token
            for token in register["LIT-SPP1-001"]["location"].split(";")
            if token.startswith("REF-")
        ]
        self.assertEqual(len(ref_ids), 5)

        edges_citing_spp1 = [
            row["edge_id"]
            for row in load_tsv(EDGE_EVIDENCE_TSV)
            if row["evidence_id"] == "LIT-SPP1-001"
        ]
        self.assertTrue(edges_citing_spp1)

        assertions = load_assertions(ROOT)
        by_edge: dict[str, list[dict[str, str]]] = {}
        for row in assertions:
            by_edge.setdefault(row["edge_id"], []).append(row)

        # The fan-out is the topic list minus retractions plus attachments. An
        # unadjudicated edge still gets all five; LE017 keeps only REF-038,
        # because the other four were retracted after full-text review.
        adjudications = load_citation_adjudications(
            ROOT / "config/edge_citation_adjudications.tsv",
            list(by_edge),
            [row["ref_id"] for row in load_tsv(REFERENCES_TSV)],
        )
        retracted, attachments = partition(adjudications)
        for edge_id in edges_citing_spp1:
            expected = [r for r in ref_ids if (edge_id, r) not in retracted]
            expected += [r for r in attachments.get(edge_id, ()) if r not in expected]
            self.assertEqual(
                sorted(r["reference_id"] for r in by_edge[edge_id]),
                sorted(expected),
                edge_id,
            )

    def test_expression_only_references_support_no_relation(self) -> None:
        """Registered-but-uncited is a decision here, not an oversight.

        REF-058 (Somkuti 1997) and REF-059 (Jin 2025) were both read in full and
        deliberately attached to no edge, because neither reaches the claim its
        nearest relation encodes:

        * Somkuti measures the **beta3 subunit** by beta3-directed antibodies and a
          beta3 probe -- ITGAV and ITGB5 are never measured -- with an expression
          readout and no adhesion assay of any kind. It also never tested HB-EGF,
          EREG or AREG, so it cannot support ``LE018`` (``E_HBEGF ->
          E_ITGAVB3_5``). Attaching it there would repeat exactly the
          ligand-substitution defect ``CIT-005``/``CIT-006`` closed on ``LE015``.
        * Jin never tested its own chain end to end (no hCG arm under PGF2a
          blockade), never perturbed ADAM17, and never identified a receptor for
          hCG, so it supports no epithelial-to-stromal edge as encoded.

        Attaching either one is legal -- it needs a row in
        ``config/edge_citation_adjudications.tsv`` -- but it must be deliberate,
        and updating this test is the point at which that becomes visible.
        """
        cited = {row["reference_id"] for row in load_assertions(ROOT)}
        for ref_id in ("REF-058", "REF-059"):
            self.assertNotIn(ref_id, cited, f"{ref_id} acquired edge-level support")

    def test_confirmed_misattributions_are_repaired(self) -> None:
        """The four full-text-verified defects this increment closes.

        Each was a topic fan-out: an evidence id's whole reference list landed
        on every citing edge, so papers that never mention the source or target
        node were asserted as supporting the relation.
        """
        by_edge: dict[str, set[str]] = {}
        for row in load_assertions(ROOT):
            by_edge.setdefault(row["edge_id"], set()).add(row["reference_id"])

        # Apparao 2001 and Fazleabas 1997 contain no occurrence of "LIF".
        self.assertEqual(by_edge["LE017"], {"REF-038"})
        # Apparao applies HB-EGF as a treatment and never measures its
        # regulation; Lessey 2002 is the regulation study.
        self.assertEqual(by_edge["LE015"], {"REF-006", "REF-042"})
        # None of LE091's eight inherited references concerns KLF12.
        self.assertEqual(by_edge["LE091"], {"REF-037"})
        # REF-011 is alpha-dystroglycan: wrong for the PODXL and MUC1 edges,
        # but right for the two that aggregate the E_DAG1_FULL disjunct.
        carrying = {e for e, refs in by_edge.items() if "REF-011" in refs}
        self.assertEqual(
            carrying,
            {
                "LE010",
                "LE011",
                "LE012",
                "LE027",
                "LE033",
                "LE069",
                "LE073",
                "LE075",
                "LE086",
            },
        )

    def test_a_retraction_cannot_rest_on_metadata(self) -> None:
        """Suspicion may annotate a citation; only full text may delete one."""
        with self.assertRaises(CitationAdjudicationError):
            self._load_directives_with(
                action="retract", basis="reference_not_in_topic_set"
            )

    def _load_directives_with(self, *, action: str, basis: str) -> None:
        import csv as _csv

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "adjudications.tsv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = _csv.DictWriter(
                    handle, fieldnames=list(ADJUDICATION_COLUMNS), delimiter="\t"
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "adjudication_id": "CIT-999",
                        "edge_id": "LE017",
                        "reference_id": "REF-007",
                        "action": action,
                        "basis": basis,
                        "claim": "c",
                        "rationale": "r",
                        "action_required": "none",
                        "dated": "2026-07-29",
                    }
                )
            load_citation_adjudications(path, ["LE017"], ["REF-007"])

    def test_stale_directives_fail_in_both_directions(self) -> None:
        """A directive that stops matching a real defect must not outlive it."""
        retract_gone = [
            {
                "adjudication_id": "CIT-998",
                "edge_id": "LE017",
                "reference_id": "REF-099",
                "action": "retract",
                "basis": "full_text_absence",
                "claim": "c",
                "rationale": "r",
                "action_required": "none",
                "dated": "2026-07-29",
            }
        ]
        with self.assertRaises(CitationAdjudicationError):
            check_applicability(retract_gone, {"LE017": ["REF-038"]})

        attach_present = [
            dict(
                retract_gone[0],
                action="attach",
                basis="reference_not_in_topic_set",
                reference_id="REF-038",
            )
        ]
        with self.assertRaises(CitationAdjudicationError):
            check_applicability(attach_present, {"LE017": ["REF-038"]})

    def test_migration_preserves_curator_authored_fields(self) -> None:
        """Regression: the migration used to rebuild from placeholders.

        Curation lives in this file and nowhere else, and the suite runs the
        migration against the real repository root, so a rebuild silently
        erased every claim-level judgement a curator had written.
        """
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _copy_real_sources(tmp)
            migrate_edge_evidence(tmp)
            path = tmp / ASSERTIONS_TSV.relative_to(ROOT)

            rows = load_tsv(path)
            rows[0]["curation_status"] = "curated"
            rows[0]["evidence_grade"] = "B"
            rows[0]["support_rationale"] = "curator judgement"
            rows[0]["directness"] = "direct"
            _write_tsv(path, rows)

            migrate_edge_evidence(tmp)
            after = load_tsv(path)[0]
            self.assertEqual(after["curation_status"], "curated")
            self.assertEqual(after["evidence_grade"], "B")
            self.assertEqual(after["support_rationale"], "curator judgement")
            self.assertEqual(after["directness"], "direct")

            # Still idempotent once curated.
            before_bytes = path.read_bytes()
            migrate_edge_evidence(tmp)
            self.assertEqual(path.read_bytes(), before_bytes)

    def test_curation_does_not_migrate_when_a_reference_is_inserted(self) -> None:
        """Regression: assertion ids used to be positional.

        Ids were ``ASRT-<edge>-<n>`` indexing the register's location list, and
        the merge keys on the id -- so inserting a reference renumbered the rows
        and carried a curator's judgement about one paper onto a different one.
        Correcting a defective citation requires exactly such an insertion.
        """
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _copy_real_sources(tmp)
            migrate_edge_evidence(tmp)
            path = tmp / ASSERTIONS_TSV.relative_to(ROOT)

            rows = load_tsv(path)
            target = next(
                r
                for r in rows
                if r["edge_id"] == "LE018" and r["reference_id"] == "REF-007"
            )
            target["curation_status"] = "curated"
            target["support_rationale"] = "grades REF-007 specifically"
            target["directness"] = "direct"
            target["support_type"] = "functional"
            _write_tsv(path, rows)

            register_path = tmp / REGISTER_TSV.relative_to(ROOT)
            register = load_tsv(register_path)
            for row in register:
                if row["evidence_id"] == "LIT-HBEGF-001":
                    row["location"] = "REF-042;" + row["location"]
            _write_tsv(register_path, register)

            migrate_edge_evidence(tmp)
            after = {
                r["reference_id"]: r for r in load_tsv(path) if r["edge_id"] == "LE018"
            }
            self.assertEqual(after["REF-007"]["curation_status"], "curated")
            self.assertEqual(
                after["REF-007"]["support_rationale"], "grades REF-007 specifically"
            )
            for ref_id in ("REF-006", "REF-042"):
                self.assertEqual(after[ref_id]["curation_status"], "not_yet_curated")
                self.assertEqual(after[ref_id]["support_rationale"], "")

    def test_assertion_ids_are_content_addressed(self) -> None:
        """An id must name the claim it describes, not a list position."""
        for row in load_assertions(ROOT):
            source = row["reference_id"] or row["source_observation_id"]
            self.assertTrue(source, row["assertion_id"])
            self.assertEqual(row["assertion_id"], f"ASRT-{row['edge_id']}-{source}")

    def test_migration_still_refreshes_uncurated_fields(self) -> None:
        """The merge must not freeze the file: a placeholder value is still
        regenerated, so corrected source tables propagate."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _copy_real_sources(tmp)
            migrate_edge_evidence(tmp)
            path = tmp / ASSERTIONS_TSV.relative_to(ROOT)

            rows = load_tsv(path)
            reference_row = next(r for r in rows if r["reference_id"])
            reference_row["species_evidence"] = ""
            _write_tsv(path, rows)

            migrate_edge_evidence(tmp)
            restored = next(
                r
                for r in load_tsv(path)
                if r["assertion_id"] == reference_row["assertion_id"]
            )
            self.assertTrue(restored["species_evidence"].strip())

    def test_committed_table_is_what_the_migration_produces(self) -> None:
        committed = ASSERTIONS_TSV.read_bytes()
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _copy_migration_inputs(tmp)
            path = tmp / ASSERTIONS_TSV.relative_to(ROOT)
            migrate_edge_evidence(tmp)
            first = path.read_bytes()
            migrate_edge_evidence(tmp)
            second = path.read_bytes()
        self.assertEqual(
            committed,
            first,
            "the committed edge_evidence_assertions.tsv is not what "
            "migrate_edge_evidence produces from the committed sources; migrate "
            "and commit it",
        )
        self.assertEqual(first, second, "migrate_edge_evidence is not idempotent")
        self.assertEqual(committed, ASSERTIONS_TSV.read_bytes())

    def test_real_assertions_validate_cleanly(self) -> None:
        report = validate_assertions(ROOT)
        self.assertEqual(report.errors, [], report.errors)

    def test_curation_progress_is_reported_not_mandated_to_be_zero(self) -> None:
        """Every assertion is accounted for by some curation status.

        This previously asserted `not_yet_curated_count == len(assertions)`,
        which made curating a single paper fail the suite. The invariant that
        actually matters is that no assertion falls outside the vocabulary.
        """
        assertions = load_assertions(ROOT)
        counted = sum(
            report_count
            for key, report_count in validate_assertions(ROOT).summary.items()
            if key.endswith("_count")
            and key[: -len("_count")] in CURATION_STATUS_VALUES
        )
        self.assertEqual(counted, len(assertions))

    def test_write_family_does_not_touch_assertions_file(self) -> None:
        before = ASSERTIONS_TSV.read_bytes()
        # write_family lists its outputs in the README `relative_to(ROOT)`, which
        # used to force the scratch dir into the checkout. Re-rooting ROOT at the
        # scratch dir keeps it out. Its inputs are module constants bound at
        # import, so they still come from the checkout; the only other use,
        # build_provenance's `pixi run` version probe (cwd=ROOT), then finds no
        # manifest and records `unavailable`, which no assertion here reads.
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(superset_family, "ROOT", Path(tmp)),
        ):
            write_family(output_dir=Path(tmp) / "generated_family")
            after = ASSERTIONS_TSV.read_bytes()
            self.assertEqual(before, after)
            # write_family regenerates its own edge_evidence.tsv in the
            # scratch dir; the companion assertions table is not part of
            # that generator and must not appear there either.
            self.assertFalse(
                (
                    Path(tmp) / "generated_family" / "edge_evidence_assertions.tsv"
                ).exists()
            )


class SyntheticCorruptionTests(unittest.TestCase):
    """Build corrupted copies in tempdirs to prove the validator actually
    fails on violations, not just passes on clean data."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_root = Path(self._tmp.name)
        _copy_real_sources(self.tmp_root)
        migrate_edge_evidence(self.tmp_root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _assertions_path(self) -> Path:
        return self.tmp_root / ASSERTIONS_TSV.relative_to(ROOT)

    def _load(self) -> list[dict[str, str]]:
        return load_tsv(self._assertions_path())

    def _write(self, rows: list[dict[str, str]]) -> None:
        _write_tsv(self._assertions_path(), rows)

    def test_clean_migration_validates(self) -> None:
        report = validate_assertions(self.tmp_root)
        self.assertEqual(report.errors, [])

    def test_multiple_assertions_per_edge_preserved_by_load(self) -> None:
        rows = self._load()
        by_edge: dict[str, int] = {}
        for row in rows:
            by_edge[row["edge_id"]] = by_edge.get(row["edge_id"], 0) + 1
        multi_edges = [edge for edge, count in by_edge.items() if count > 1]
        self.assertTrue(multi_edges, "expected at least one multi-assertion edge")

    def test_contradictory_second_assertion_loads_and_is_reported_not_overwritten(
        self,
    ) -> None:
        rows = self._load()
        target_edge = rows[0]["edge_id"]
        original_count = sum(1 for r in rows if r["edge_id"] == target_edge)

        contradiction = dict(rows[0])
        contradiction["assertion_id"] = f"{rows[0]['assertion_id']}-CONTRA"
        contradiction["direction_supported"] = "contradicted"
        contradiction["curation_status"] = "disputed"
        rows.append(contradiction)
        self._write(rows)

        loaded = load_assertions(self.tmp_root)
        edge_rows = [r for r in loaded if r["edge_id"] == target_edge]
        self.assertEqual(len(edge_rows), original_count + 1)
        directions = {r["direction_supported"] for r in edge_rows}
        self.assertIn("contradicted", directions)

        report = validate_assertions(self.tmp_root)
        self.assertEqual(
            report.summary["by_direction_supported"].get("contradicted"), 1
        )

    def test_bibliographic_assertion_with_unknown_reference_is_an_error(self) -> None:
        rows = self._load()
        rows[0] = dict(rows[0])
        rows[0]["evidence_origin"] = "bibliographic"
        rows[0]["reference_id"] = "REF-999-DOES-NOT-EXIST"
        rows[0]["source_observation_id"] = ""
        self._write(rows)

        report = validate_assertions(self.tmp_root)
        self.assertTrue(
            any("REF-999-DOES-NOT-EXIST" in e for e in report.errors), report.errors
        )

    def test_in_house_assertion_with_unknown_observation_is_an_error(self) -> None:
        rows = self._load()
        rows[0] = dict(rows[0])
        rows[0]["evidence_origin"] = "in_house_experiment"
        rows[0]["reference_id"] = ""
        rows[0]["source_observation_id"] = "SOFIA-DOES-NOT-EXIST"
        self._write(rows)

        report = validate_assertions(self.tmp_root)
        self.assertTrue(
            any("SOFIA-DOES-NOT-EXIST" in e for e in report.errors), report.errors
        )

    def test_mouse_species_with_human_target_and_transfer_not_required_is_an_error(
        self,
    ) -> None:
        rows = self._load()
        rows[0] = dict(rows[0])
        rows[0]["species_evidence"] = "mouse"
        rows[0]["target_species"] = "human"
        rows[0]["species_transfer_required"] = "false"
        self._write(rows)

        report = validate_assertions(self.tmp_root)
        self.assertTrue(
            any(
                rows[0]["assertion_id"] in e and "species_transfer_required" in e
                for e in report.errors
            ),
            report.errors,
        )

    def test_curated_with_unknown_directness_is_an_error(self) -> None:
        rows = self._load()
        rows[0] = dict(rows[0])
        rows[0]["curation_status"] = "curated"
        rows[0]["directness"] = "unknown"
        rows[0]["support_type"] = "functional"
        self._write(rows)

        report = validate_assertions(self.tmp_root)
        self.assertTrue(
            any(
                rows[0]["assertion_id"] in e and "directness" in e
                for e in report.errors
            ),
            report.errors,
        )

    def test_not_yet_curated_count_appears_in_report(self) -> None:
        report = validate_assertions(self.tmp_root)
        rows = self._load()
        expected = sum(1 for r in rows if r["curation_status"] == "not_yet_curated")
        self.assertEqual(report.summary["not_yet_curated_count"], expected)
        self.assertGreater(report.summary["not_yet_curated_count"], 0)

    def test_assertion_columns_match_declared_schema(self) -> None:
        rows = self._load()
        self.assertEqual(list(rows[0]), list(ASSERTION_COLUMNS))


if __name__ == "__main__":
    unittest.main()
