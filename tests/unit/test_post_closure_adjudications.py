"""Citation directives decided after the Phase 2B closure froze the registry.

`config/edge_citation_adjudications.tsv` is frozen twice over: `closure_replay`
reports any byte change to it, and the historical v0.3.0 generator in
`dt_adoc.evidence.assertions` replays against it. Appending CIT-038 and CIT-039
to it broke both -- it tripped the closure guard, and it silently changed what
the *historical* migration is recorded as producing, because that generator
reads the same file.

Later directives therefore live in dated addenda that only the current pipeline
reads. These tests hold that boundary from both sides: the new citations must
really be in the canonical table, and the historical path must not know they
exist.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from dt_adoc.evidence import experimental as ex
from dt_adoc.evidence.citation_adjudications import (
    ADJUDICATION_COLUMNS,
    CitationAdjudicationError,
    load_citation_adjudications,
    load_with_addenda,
)

ROOT = ex.repo_root()
FROZEN = ROOT / ex.CITATION_ADJUDICATIONS_PATH
ADDENDA = [ROOT / p for p in ex.POST_CLOSURE_ADJUDICATION_PATHS]
#: The commit that closed Phase 2B, from dt_adoc.closure_replay.
CLOSURE_COMMIT = "97f88f55ce62e2adca23f631de3ad8e1270ad3e6"

from tests.unit.source_history import skip_module_unless_available

skip_module_unless_available(CLOSURE_COMMIT)


def _git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, check=True
    ).stdout


def _edges_and_refs() -> tuple[list[str], list[str]]:
    edge_rows = ex.read_tsv(
        ex.model_dir(ex.DEFAULT_MODEL_VERSION, ROOT) / "edge_evidence.tsv"
    )
    references = [r["ref_id"] for r in ex.read_tsv(ROOT / ex.REFERENCES_PATH)]
    return [r["edge_id"] for r in edge_rows], references


class TheFrozenRegistryIsUntouched(unittest.TestCase):
    def test_it_is_byte_identical_to_the_phase2b_closure_commit(self) -> None:
        """The whole point of the addendum. If this fails the addendum was
        pointless and the closure guarantee is gone."""
        frozen = _git("show", f"{CLOSURE_COMMIT}:{ex.CITATION_ADJUDICATIONS_PATH}")
        self.assertEqual(FROZEN.read_bytes(), frozen)

    def test_the_new_directives_are_not_in_it(self) -> None:
        text = FROZEN.read_text(encoding="utf-8")
        for identifier in ("CIT-038", "CIT-039"):
            self.assertNotIn(identifier, text)

    def test_the_historical_generator_reads_only_the_frozen_registry(self) -> None:
        """`assertions.py` must not learn about post-closure directives: a
        citation decided in 2026 is not part of what the v0.3.0 migration did."""
        source = (ROOT / "src/dt_adoc/evidence/assertions.py").read_text("utf-8")
        self.assertIn("load_citation_adjudications", source)
        self.assertNotIn("load_with_addenda", source)
        self.assertNotIn("POST_CLOSURE_ADJUDICATION_PATHS", source)

    def test_no_unrelated_historical_directive_moved(self) -> None:
        """Every id in the closure commit is still in the frozen file, and the
        frozen file has gained none."""
        frozen_then = _git(
            "show", f"{CLOSURE_COMMIT}:{ex.CITATION_ADJUDICATIONS_PATH}"
        ).decode("utf-8")
        then = {line.split("\t")[0] for line in frozen_then.splitlines()[1:]}
        edges, references = _edges_and_refs()
        now = {
            r["adjudication_id"]
            for r in load_citation_adjudications(FROZEN, edges, references)
        }
        self.assertEqual(then, now)


class TheAddendumCarriesTheNewDirectives(unittest.TestCase):
    def setUp(self) -> None:
        self.edges, self.refs = _edges_and_refs()

    def test_the_addendum_file_exists_and_is_outside_the_frozen_paths(self) -> None:
        from dt_adoc.closure_replay import CLOSURE_FROZEN_PATHS

        for path in ADDENDA:
            self.assertTrue(path.is_file(), f"{path} is missing")
            relative = path.relative_to(ROOT).as_posix()
            for frozen in CLOSURE_FROZEN_PATHS:
                self.assertFalse(
                    relative.startswith(str(frozen).rstrip("/") + "/"),
                    f"{relative} is inside the frozen path {frozen}",
                )

    def test_it_has_the_registry_schema(self) -> None:
        for path in ADDENDA:
            header = path.read_text(encoding="utf-8").splitlines()[0].split("\t")
            self.assertEqual(tuple(header), ADJUDICATION_COLUMNS)

    def test_both_new_directives_are_present_exactly_once(self) -> None:
        combined = load_with_addenda(FROZEN, ADDENDA, self.edges, self.refs)
        for identifier, edge, reference in (
            ("CIT-038", "LE018", "REF-042"),
            ("CIT-039", "LE049", "REF-016"),
        ):
            matching = [r for r in combined if r["adjudication_id"] == identifier]
            with self.subTest(identifier=identifier):
                self.assertEqual(len(matching), 1)
                self.assertEqual(matching[0]["edge_id"], edge)
                self.assertEqual(matching[0]["reference_id"], reference)
                self.assertEqual(matching[0]["action"], "attach")

    def test_their_rationale_and_provenance_survived_the_move(self) -> None:
        combined = {
            r["adjudication_id"]: r
            for r in load_with_addenda(FROZEN, ADDENDA, self.edges, self.refs)
        }
        for identifier, needle in (
            ("CIT-038", "beta3 integrin subunit"),
            ("CIT-039", "8-bromo-cAMP"),
        ):
            row = combined[identifier]
            with self.subTest(identifier=identifier):
                self.assertIn(needle, row["rationale"])
                self.assertEqual(row["dated"], "2026-11-18")
                self.assertTrue(row["claim"].strip())
                self.assertTrue(row["action_required"].strip())


class TheCombinedRegistryReachesTheTable(unittest.TestCase):
    def test_both_citations_seed_exactly_one_row_each(self) -> None:
        seeds = ex.migration_seeds()
        for edge, reference in (("LE018", "REF-042"), ("LE049", "REF-016")):
            matching = [
                s for s in seeds if s.edge_id == edge and s.reference_id == reference
            ]
            with self.subTest(edge=edge):
                self.assertEqual(len(matching), 1)

    def test_the_canonical_rows_exist_with_their_curation(self) -> None:
        rows = {r["evidence_piece_id"]: r for r in ex.load_table()}
        for piece in ("EVP-LE018-REF042-01", "EVP-LE049-REF016-01"):
            with self.subTest(piece=piece):
                self.assertIn(piece, rows)
                self.assertEqual(rows[piece]["curation_status"], "provisional")
                self.assertEqual(rows[piece]["edge_support"], "partial")

    def test_rebuilding_preserves_their_provenance(self) -> None:
        """Regeneration must not reset the lineage of a row that only exists
        because of an addendum."""
        rebuilt = {r["evidence_piece_id"]: r for r in ex.build_table(ex.load_table())}
        for piece in ("EVP-LE018-REF042-01", "EVP-LE049-REF016-01"):
            with self.subTest(piece=piece):
                self.assertEqual(
                    rebuilt[piece]["migrated_from"],
                    f"seeded:{ex.DEFAULT_MODEL_VERSION}",
                )
                self.assertEqual(rebuilt[piece]["curation_status"], "provisional")

    def test_the_in_house_seed_for_le049_survives(self) -> None:
        seeds = [s for s in ex.migration_seeds() if s.edge_id == "LE049"]
        self.assertIn("SOFIA-STR-001", {s.source_observation_id for s in seeds})
        rows = {r["evidence_piece_id"] for r in ex.load_table()}
        self.assertIn("EVP-LE049-SOFIASTR001-01", rows)

    def test_regeneration_is_deterministic(self) -> None:
        once = ex.build_table(ex.load_table())
        twice = ex.build_table(ex.load_table())
        self.assertEqual(
            ex.render_tsv(once, ex.COLUMNS), ex.render_tsv(twice, ex.COLUMNS)
        )

    def test_no_curated_row_is_lost_by_regeneration(self) -> None:
        before = {
            r["evidence_piece_id"]
            for r in ex.load_table()
            if r["curation_status"] != "unreviewed"
        }
        after = {
            r["evidence_piece_id"]
            for r in ex.build_table(ex.load_table())
            if r["curation_status"] != "unreviewed"
        }
        self.assertEqual(before, after)


class TheCombinedLoaderRefusesBadCombinations(unittest.TestCase):
    """Per-file validation cannot see across files; these are the gaps."""

    def setUp(self) -> None:
        self.edges, self.refs = _edges_and_refs()
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def _write(self, name: str, rows: list[tuple[str, ...]]) -> Path:
        path = self.tmp / name
        body = "\t".join(ADJUDICATION_COLUMNS) + "\n"
        body += "".join("\t".join(r) + "\n" for r in rows)
        path.write_text(body, encoding="utf-8")
        return path

    def _row(
        self, identifier: str, edge: str, ref: str, action: str
    ) -> tuple[str, ...]:
        basis = (
            "reference_not_in_topic_set" if action == "attach" else "full_text_absence"
        )
        return (
            identifier,
            edge,
            ref,
            action,
            basis,
            "a claim",
            "a rationale",
            "none",
            "2026-11-18",
        )

    def test_an_id_reused_across_files_is_refused(self) -> None:
        a = self._write("a.tsv", [self._row("CIT-900", "LE018", "REF-042", "attach")])
        b = self._write("b.tsv", [self._row("CIT-900", "LE049", "REF-016", "attach")])
        with self.assertRaises(CitationAdjudicationError) as caught:
            load_with_addenda(a, [b], self.edges, self.refs)
        self.assertIn("ids are global", str(caught.exception))

    def test_the_same_citation_registered_twice_is_refused(self) -> None:
        a = self._write("a.tsv", [self._row("CIT-900", "LE018", "REF-042", "attach")])
        b = self._write("b.tsv", [self._row("CIT-901", "LE018", "REF-042", "attach")])
        with self.assertRaises(CitationAdjudicationError) as caught:
            load_with_addenda(a, [b], self.edges, self.refs)
        self.assertIn("again", str(caught.exception))

    def test_attaching_and_retracting_the_same_pair_is_refused(self) -> None:
        """Within one file applicability makes this impossible; across files
        nothing checked it, and the two would have raced in `partition`."""
        a = self._write("a.tsv", [self._row("CIT-900", "LE018", "REF-042", "retract")])
        b = self._write("b.tsv", [self._row("CIT-901", "LE018", "REF-042", "attach")])
        with self.assertRaises(CitationAdjudicationError) as caught:
            load_with_addenda(a, [b], self.edges, self.refs)
        self.assertIn("cannot be", str(caught.exception))

    def test_an_unknown_edge_in_an_addendum_is_refused(self) -> None:
        a = self._write("a.tsv", [])
        b = self._write("b.tsv", [self._row("CIT-900", "LE999", "REF-042", "attach")])
        with self.assertRaises(CitationAdjudicationError):
            load_with_addenda(a, [b], self.edges, self.refs)

    def test_an_unknown_reference_in_an_addendum_is_refused(self) -> None:
        a = self._write("a.tsv", [])
        b = self._write("b.tsv", [self._row("CIT-900", "LE018", "REF-999", "attach")])
        with self.assertRaises(CitationAdjudicationError):
            load_with_addenda(a, [b], self.edges, self.refs)

    def test_a_missing_addendum_is_not_an_error(self) -> None:
        """A dated addendum that does not exist yet must not break the build."""
        a = self._write("a.tsv", [self._row("CIT-900", "LE018", "REF-042", "attach")])
        rows = load_with_addenda(a, [self.tmp / "absent.tsv"], self.edges, self.refs)
        self.assertEqual(len(rows), 1)

    def test_the_frozen_registry_alone_still_loads_unchanged(self) -> None:
        """Passing no addenda must behave exactly like the old loader, or the
        historical path and this one would have diverged."""
        self.assertEqual(
            load_with_addenda(FROZEN, [], self.edges, self.refs),
            load_citation_adjudications(FROZEN, self.edges, self.refs),
        )


if __name__ == "__main__":
    unittest.main()
