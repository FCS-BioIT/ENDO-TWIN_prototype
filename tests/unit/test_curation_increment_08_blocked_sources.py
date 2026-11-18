"""The 2026-09-18 blocked-source refresh: two papers read, nothing executable moved.

U4b closed the fourteen September-11 candidates with two of its nine references
**access-blocked**: Ma 2023 (`DRREF-006`) and Zhou 2021 (`DRREF-007`). It recorded
both as blocked rather than as negative evidence, named the specific fields each
would unblock, and said in terms that registering the papers later "is legitimate
and changes no U4b conclusion". This increment is that later unit. Both PDFs were
located, hashed, read in full and registered canonically, and the three candidates
that depended on them were re-adjudicated.

**Three things are separate and this module keeps them separate**, because the
whole risk of a literature refresh is that they collapse into one another:

1. **evidence strengthened** — a reference moved from unread to read;
2. **candidate admitted** — a node moved on the §5 ladder;
3. **executable encoding justified** — a rule, edge, input or rate changed.

(3) happened for nothing: no node, edge, rule, threshold, rate, initial condition or
input changed. `NoExecutableChangeTest` below derives **part** of that and says which
part -- the free-variable count from the repository's own enumerator, the absence of
every name these two papers could have introduced from both supersets' rules, and
`E_SPP1_EXPR`'s determinant. Byte-identity between the v0.5 scaffold and v0.4 is a
different invariant and is guarded elsewhere, by
`tests/unit/test_v05_scaffold.py::ScaffoldIdentityTest`, which compares the file sets
and the bytes. This unit changed nothing under `models/`, which `git diff` shows.

The re-adjudications went in **opposite directions on the same evidence**, which is
the strongest sign the unit was not run to a conclusion:

- `E_JAG1_NOTCH3` moved **up** — `EVIDENCE_UNVERIFIED` -> `WAIT_FOR_EXPERIMENT` —
  because Zhou 2021 is a real primary-human-cell result with a pathway-activity
  readout. Its *encoding* did not move at all: the paper perturbs **no** upstream
  input to JAG1, so `DRUNR-005` is confirmed by the source rather than inherited.
- `E_SLEX_SURFACE` moved **up a rung without moving its verdict** — Ma 2023 supplies
  the determinant U4b recorded as missing, so the first failing criterion goes from
  §5(2) to §5(4), while the disposition stays `RETAIN_CATALOG_ONLY` because the
  structural measurement against the replacement is unchanged.
- `E_GLYCOSYLATION_PROGRAM` moved **down** — `RETAIN_CATALOG_ONLY` -> `REJECT` —
  because the same paper that strengthened the glycan-output node falsified the
  enzyme-*programme* node. One paper, two candidates, opposite signs.

The tests that matter most here are the **negative** ones. A newly available paper
is exactly when unsupported edges get imported, so `ForbiddenInferencesTest` pins
each relation the sources were checked for and found **not** to license.
"""

from __future__ import annotations

import collections
import csv
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.reporting.structure import load_structure

REVIEWS = ROOT / "context/literature/reviews"
LEDGER = REVIEWS / "blocked_source_refresh_2026-09-18.primary-verification.tsv"
RELATIONS = REVIEWS / "blocked_source_refresh_2026-09-18.candidate-relations.tsv"
DISPOSITIONS = (
    REVIEWS / "deep_research_adhesion_model_2026-09-11.candidate-node-dispositions.tsv"
)
MANIFEST = ROOT / "context/literature/pdf_manifest.tsv"
REFERENCES = ROOT / "context/literature/references.tsv"
STAGED = ROOT / "context/literature/staging/deep_research_adhesion_model_2026-09-11"

GUARDED_MODELS = ("adoc-literature-superset-v0.4.0", "adoc-literature-superset-v0.5.0")

#: The two papers, by the identifiers a later unit would search on. The sha256 is
#: the reproducible part: the PDFs stay in the gitignored library and are never
#: committed, so the digest is what makes "this is the file that was read"
#: checkable by anyone holding the same file.
PAPERS = {
    "REF-076": {
        "pdf": "PDF-048",
        "doi": "10.1096/fj.202100590R",
        "pmid": "34252231",
        "sha256": "17c81107f6a5224045eeefba4b7f95146fdcd0d15a878b1486b33c83fce33e9c",
        "pages": "28",
        "finding": "BSR-DRREF-007",
    },
    "REF-077": {
        "pdf": "PDF-049",
        "doi": "10.1093/biolre/ioad007",
        "pmid": "36648484",
        "sha256": "13a1e0352fafad24f666a2112fd6108dea2b3a685645a20d14bad51c283a7f97",
        "pages": "11",
        "finding": "BSR-DRREF-006",
    },
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class ProvenanceTest(unittest.TestCase):
    """Registration is consistent across all four artifacts, or it is not done."""

    def test_both_papers_are_registered_end_to_end(self) -> None:
        refs = {r["ref_id"]: r for r in _rows(REFERENCES)}
        manifest = {r["ref_id"]: r for r in _rows(MANIFEST) if r["ref_id"]}
        ledger = {r["finding_id"]: r for r in _rows(LEDGER)}
        for ref_id, facts in PAPERS.items():
            with self.subTest(ref=ref_id):
                self.assertIn(ref_id, refs)
                self.assertEqual(refs[ref_id]["doi"], facts["doi"])
                self.assertEqual(refs[ref_id]["pmid"], facts["pmid"])
                row = manifest[ref_id]
                self.assertEqual(row["manifest_id"], facts["pdf"])
                self.assertEqual(row["sha256"], facts["sha256"])
                self.assertEqual(row["pages"], facts["pages"])
                self.assertEqual(row["full_text_inspected"], "yes")
                self.assertEqual(row["registration_decision"], "registered")
                self.assertIn(
                    facts["sha256"], ledger[facts["finding"]]["verification_route"]
                )

    def test_no_pdf_was_committed_by_this_increment(self) -> None:
        """Source PDFs stay in the gitignored library; only the digest is tracked.

        Checked by author-and-year against the tracked `*.pdf` list rather than by
        the manifest's `batch` tag, because the manifest is exactly the artifact
        that would be consistent with itself if a PDF had been committed.
        """
        tracked = subprocess.run(
            ["git", "ls-files", "*.pdf"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        for path in tracked:
            self.assertNotIn("Zhou et al. - 2021", path)
            self.assertNotIn("Ma et al. - 2023", path)

    def test_the_manuscript_version_caveat_is_machine_readable(self) -> None:
        """Zhou 2021 was read from the accepted author manuscript, not the version
        of record, and every figure reference in that ledger row is to it.

        **The first revision of this increment recorded that in prose only**, and
        the review caught it: `publication_status` was the sole machine-readable
        field and it read `published`, so `REF-076` was indistinguishable from a
        version-of-record citation at every point of use and the corpus-wide count
        of files that are not versions of record was short by one.

        The repair was to stop making one column carry two facts.
        `publication_status` describes the **article** -- Zhou 2021 is published,
        so the `REF-*` id is correctly minted and `accepted_unedited`, which means
        "not yet through production", would have been simply false. `rendering_read`
        describes the **file**, and that is where `author_manuscript` belongs. The
        corpus-wide census lives in
        `test_pdf_manifest.test_files_that_are_not_versions_of_record_stay_countable`;
        this asserts the pairing for the row that forced the column.
        """
        row = {r["finding_id"]: r for r in _rows(LEDGER)}["BSR-DRREF-007"]
        self.assertIn("ACCEPTED AUTHOR MANUSCRIPT", row["verification_route"].upper())
        self.assertIn("NOT the publisher version of record", row["verification_route"])
        manifest = {r["manifest_id"]: r for r in _rows(MANIFEST)}
        self.assertEqual(manifest["PDF-048"]["publication_status"], "published")
        self.assertEqual(manifest["PDF-048"]["rendering_read"], "author_manuscript")
        self.assertIn(
            "accepted author manuscript", manifest["PDF-048"]["key_finding_for_adoc"]
        )
        # Ma is the control: same batch, same registration route, no divergence.
        self.assertEqual(manifest["PDF-049"]["rendering_read"], "version_of_record")


class ReadjudicationTest(unittest.TestCase):
    """The three candidates, and the direction each moved."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.by_id = {r["candidate_id"]: r for r in _rows(DISPOSITIONS)}

    def test_jag1_moved_off_unverified_but_its_encoding_did_not_move(self) -> None:
        row = self.by_id["E_JAG1_NOTCH3"]
        self.assertEqual(row["final_disposition"], "WAIT_FOR_EXPERIMENT")
        self.assertEqual(row["node_verdict"], "JUSTIFIED_SYSTEM_LIMITED")
        self.assertEqual(row["first_failing_criterion"], "5(2)_determinant")
        self.assertEqual(row["unblock_locus"], "ADOC_RUNNABLE")
        # The encoding is the half that did NOT move, and DRUNR-005 is why.
        self.assertEqual(row["encoding_verdict"], "REJECT_AS_STAGED")
        self.assertIn("DRUNR-005", row["decisive_reason"])

    def test_the_jag1_experiment_is_named_and_its_scope_is_bound(self) -> None:
        """`ADOC_RUNNABLE` obliges the row to name the experiment -- and, because
        the deposited design bundles its inputs, to say what that experiment
        CANNOT conclude. `config/protocols.yaml` records no single-agent arm, so a
        control-versus-cocktail difference is a CONTEXT-level determinant and can
        never name a hormone. Without this clause the row would read as licensing
        exactly the `IN_P4 -> JAG1` invention DRUNR-005 forbids.
        """
        condition = self.by_id["E_JAG1_NOTCH3"]["unblock_condition"]
        self.assertIn("NOTCH3 NICD", condition)
        self.assertIn("NO SINGLE-AGENT ARM", condition.upper())
        self.assertIn("CONTEXT-LEVEL", condition.upper())
        for forbidden in ("IN_P4 -> JAG1", "IN_E2 -> JAG1"):
            self.assertIn(forbidden, condition)

    def test_slex_moved_a_rung_without_moving_its_verdict(self) -> None:
        """Ma supplies the determinant, so §5(2) passes and §5(4) becomes the
        first failure -- evidence strengthened, node admission advanced,
        disposition unchanged. Three different things, one row.
        """
        row = self.by_id["E_SLEX_SURFACE"]
        self.assertEqual(row["final_disposition"], "RETAIN_CATALOG_ONLY")
        self.assertEqual(row["first_failing_criterion"], "5(4)_delta_and_alias")
        self.assertEqual(row["evidence_state"], "BOTH_REFERENCES_VERIFIED")
        self.assertEqual(row["unblock_locus"], "EXTERNAL")
        self.assertNotIn("ACCESS BLOCKED", row["decisive_references"])

    def test_the_determinant_that_was_accepted_is_of_the_right_variable(self) -> None:
        """Why §5(2) passes here and failed for `S_FOXO1`, `E_SOX17` and
        `E_ITGA2B1`: those three were offered a determinant of their namesake's
        mRNA or total protein against a node defined as an activity state. Ma
        measures surface sLeX **as surface sLeX**, by flow cytometry, which is the
        node's own variable. The distinction is the entire content of the §5(2)
        repair, so it is pinned rather than left to prose.
        """
        row = {r["finding_id"]: r for r in _rows(LEDGER)}["BSR-DRREF-006"]
        self.assertIn("flow cytometry", row["proximal_measurement"])
        self.assertIn("not a transcript proxy", row["proximal_measurement"])
        self.assertIn("does NOT fire", row["what_is_supported"])

    def test_the_glycosylation_reject_is_scoped_and_leaves_slex_alive(self) -> None:
        glyco = self.by_id["E_GLYCOSYLATION_PROGRAM"]
        self.assertEqual(glyco["final_disposition"], "REJECT")
        self.assertEqual(glyco["node_verdict"], "SEMANTICS_REFUTED")
        self.assertEqual(
            glyco["first_failing_criterion"], "5(0-refuted)_definition_falsified"
        )
        # Scoped: the functional glycan state survives as the other candidate.
        self.assertNotEqual(self.by_id["E_SLEX_SURFACE"]["final_disposition"], "REJECT")
        self.assertIn("E_SLEX_SURFACE", glyco["unblock_condition"])

    def test_the_disposition_tally_is_derived_and_the_documents_match_it(
        self,
    ) -> None:
        """The tally, actually derived -- which the prose claimed before it was.

        `docs/v05_u4b_candidate_node_closure.md` says its two tallies are
        "re-derived from the table ... rather than quoted". The broad sweep caught
        that as a claim about a guard that did not exist: the SPLIT-verdict count
        of seven is derived (`test_node_and_encoding_verdicts_are_recorded_
        separately`), but nothing tallied `final_disposition`, so the live counts
        and the U4b-era counts were unguarded prose in a document that told the
        reader they were not.

        Closing it by deriving the tally rather than by softening the sentence,
        because the numbers are worth guarding: they are the first thing a reader
        of either document takes away, and the last commit had to repair three
        sites where exactly these numbers had gone stale.
        """
        tally = collections.Counter(
            row["final_disposition"] for row in _rows(DISPOSITIONS)
        )
        self.assertEqual(
            dict(tally),
            {
                "RULE_VARIANT_ONLY": 1,
                "WAIT_FOR_EXPERIMENT": 2,
                "RETAIN_CATALOG_ONLY": 7,
                "EVIDENCE_UNVERIFIED": 3,
                "REJECT": 1,
            },
        )
        self.assertEqual(sum(tally.values()), 14)
        # PROMOTE stays the number this whole line of units has produced.
        self.assertEqual(tally["PROMOTE"], 0)
        self.assertEqual(tally["MERGE_WITH_EXISTING"], 0)

        # The documents that quote it must quote THIS, in the order they write it.
        # Moved 1/3/5/4 -> 1/2/6/4 on 2026-09-22 by the PRL/IGFBP1/FOXO1 unit:
        # `S_FOXO1` cleared section 5(2) on Labied 2006 and now fails at 5(4),
        # so it moves WAIT_FOR_EXPERIMENT -> RETAIN_CATALOG_ONLY. The total stays
        # 14 and PROMOTE stays 0; no candidate entered or left the table.
        # Moved 1/2/6/4 -> 1/2/7/3 on 2026-09-23 by U5b: `S_AKT_EXCESS` cleared
        # section 5(1) on Kang 2022 (`U5B-001`) and fails at 5(2), EXTERNAL, so
        # it moves EVIDENCE_UNVERIFIED -> RETAIN_CATALOG_ONLY. Again no promotion.
        live = "1 / 2 / 7 / 3"
        plan = (ROOT / "docs/v05_mechanistic_integration_plan.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(live, plan)
        closure = (ROOT / "docs/v05_u4b_candidate_node_closure.md").read_text(
            encoding="utf-8"
        )
        for fragment in (
            "**2** `WAIT_FOR_EXPERIMENT`",
            "**7** `RETAIN_CATALOG_ONLY`",
            "**3** `EVIDENCE_UNVERIFIED`",
            "**1 `REJECT`**",
        ):
            self.assertIn(fragment, closure)

    def test_the_two_papers_stay_mechanistically_independent(self) -> None:
        """They were curated together because they were the two remaining blocked
        sources, not because they describe one pathway. A row that cited the wrong
        paper for the wrong candidate would be invisible in prose review.
        """
        ledger = {r["finding_id"]: r for r in _rows(LEDGER)}
        self.assertEqual(
            ledger["BSR-DRREF-006"]["candidate_ids"],
            "E_SLEX_SURFACE;E_GLYCOSYLATION_PROGRAM",
        )
        self.assertEqual(ledger["BSR-DRREF-007"]["candidate_ids"], "E_JAG1_NOTCH3")
        self.assertNotIn("JAG1", ledger["BSR-DRREF-006"]["what_is_supported"])
        for token in ("IL1B", "IL-1beta", "FUT3", "sLeX"):
            self.assertNotIn(token, ledger["BSR-DRREF-007"]["what_is_supported"])


class SppRelationTest(unittest.TestCase):
    """The one new candidate relation, and the specificity it is held to."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.row = _rows(RELATIONS)[0]

    def test_it_is_recorded_at_canonical_notch_and_never_at_notch3(self) -> None:
        """MAML1 is shared by all four Notch receptors, so its knockdown cannot
        assign SPP1 to NOTCH3 -- and in this very paper JAG1 knockdown pushed
        NOTCH1/2 NICD the OTHER way, so the assignment is actively undermined.
        Recording it as an `E_JAG1_NOTCH3 -> E_SPP1_EXPR` edge would claim a
        receptor the experiment never tested.
        """
        self.assertEqual(self.row["target_node"], "E_SPP1_EXPR")
        self.assertIn("CANONICAL-NOTCH LEVEL ONLY", self.row["specificity_supported"])
        self.assertIn("MAML1", self.row["source_state"])
        self.assertNotIn("NOTCH3", self.row["source_state"])
        self.assertIn("NOT NOTCH3-SPECIFIC", self.row["specificity_NOT_supported"])

    def test_it_records_that_it_is_carcinoma_line_only(self) -> None:
        self.assertIn("Ishikawa", self.row["system"])
        self.assertIn("ONLY", self.row["system"])
        self.assertIn("No primary human", self.row["system"])

    def test_it_is_not_executable_and_says_what_promotion_would_need(self) -> None:
        self.assertIn("NOT EXECUTABLE", self.row["executable_verdict"])
        self.assertEqual(self.row["registered_in_candidate_edges_tsv"], "no")
        self.assertTrue(len(self.row["why_not_registered_there"]) > 200)


class ForbiddenInferencesTest(unittest.TestCase):
    """Relations the sources were checked for and found NOT to license.

    This is the class that earns the module. A newly available paper is precisely
    when an unsupported edge gets imported under a citation that looks right, and
    every entry below is a relation someone could plausibly have drawn from these
    two PDFs. Each is refused for a stated reason, and the reason is in the ledger
    so a later unit re-deriving it lands in the same place.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = {r["finding_id"]: r for r in _rows(LEDGER)}

    def test_no_hormone_to_jag1_rule_is_licensed(self) -> None:
        """U4b's blocking field (d) -- the one it called the one that matters most
        -- answers negatively: Zhou perturbs no hormonal, steroidal, cAMP or
        cytokine input to JAG1 anywhere.
        """
        row = self.ledger["BSR-DRREF-007"]
        self.assertIn(
            "NO HORMONAL OR CONTEXTUAL INPUT TO JAG1 IS PERTURBED",
            row["what_is_NOT_supported"],
        )
        for forbidden in (
            "IN_P4 -> JAG1",
            "IN_E2 -> JAG1",
            "E_SECRETORY_STATE -> JAG1",
        ):
            self.assertIn(forbidden, row["what_is_NOT_supported"])

    def test_notch_independent_markers_do_not_become_downstream_edges(self) -> None:
        """Four of the five JAG1-regulated markers survive MAML1 knockdown, so
        JAG1-dependent does not mean `E_JAG1_NOTCH3`-downstream. `ITGB3` and
        `IGFBP1` are the tempting ones, being model-relevant already.
        """
        row = self.ledger["BSR-DRREF-007"]["what_is_NOT_supported"]
        self.assertIn("SURVIVE MAML1 knockdown", row)
        for marker in ("LIFR", "ITGB3", "MAOA", "IGFBP1"):
            self.assertIn(marker, row)

    def test_no_jag1_to_pgr_or_esr1_edge_and_no_mouse_import(self) -> None:
        """PGR and ESR1 are explicitly unchanged in the human models. Mouse `Esr1`
        DOES fall, and mouse tight junctions fall while the human ones explicitly
        do not -- a species difference the authors call out themselves.
        """
        row = self.ledger["BSR-DRREF-007"]["what_is_NOT_supported"]
        self.assertIn("ANY JAG1 -> PGR OR JAG1 -> ESR1 EDGE", row)
        self.assertIn("TIGHT-JUNCTION EDGES IN HUMAN", row)
        self.assertIn("NO MOUSE-ONLY FINDING MAY BECOME A HUMAN EPITHELIAL EDGE", row)

    def test_no_il1b_input_is_created_from_an_experimental_treatment(self) -> None:
        """A perturbation existing in a paper is not a state the model varies. The
        deposited ADOC contrast bundles its inputs and has no IL1B arm at all.
        """
        row = self.ledger["BSR-DRREF-006"]["what_is_NOT_supported"]
        self.assertIn("NO X_IL1B AND NO IN_IL1B INPUT IS CREATED", row)
        self.assertIn("exogenous experimental treatment", row)

    def test_no_threshold_is_taken_from_a_single_dose(self) -> None:
        row = self.ledger["BSR-DRREF-006"]["what_is_NOT_supported"]
        self.assertIn("ANY THRESHOLD, DOSE-RESPONSE OR SUFFICIENCY CLAIM", row)
        self.assertIn("one concentration, 20 ng/mL", row)

    def test_bulk_tissue_correlation_is_not_epithelial_causality(self) -> None:
        row = self.ledger["BSR-DRREF-006"]["what_is_NOT_supported"]
        self.assertIn("CORRELATIONAL BULK TISSUE", row)
        self.assertIn("cannot localise IL1B to the epithelium", row)

    def test_the_absent_viability_control_is_recorded_not_assumed_away(self) -> None:
        """DRUNR-010 exists to stop an anti-adhesion effect caused by toxicity
        being scored as mechanism. Ma has NO viability control of any kind, and Yu
        -- same cell line -- measured one and found a real proliferation effect,
        so the concern is inherited unmeasured rather than resolved. Zhou is the
        contrast: its adhesion effect is temporally separated from its
        proliferation effect, which is why its row may say so.
        """
        ma = self.ledger["BSR-DRREF-006"]["what_is_NOT_supported"]
        self.assertIn("NO viability or proliferation control ANYWHERE", ma)
        self.assertIn("INHERIT that concern UNMEASURED", ma)
        self.assertIn("DRUNR-010", ma)
        zhou = self.ledger["BSR-DRREF-007"]["what_is_supported"]
        self.assertIn("UNIMPAIRED UP TO 60 h", zhou)

    def test_the_overstated_primary_cell_notch3_result_is_recorded(self) -> None:
        """Zhou's Results text and Abstract call the HEEC NOTCH3 NICD reduction
        "confirmed"; the Figure 3B legend gives P = 0.073 at n = 3. The legend
        governs. Recorded because a later unit reading only the abstract would
        inherit a significance the data do not carry.
        """
        row = self.ledger["BSR-DRREF-007"]["what_is_NOT_supported"]
        self.assertIn("P = 0.073", row)
        self.assertIn("NON-SIGNIFICANT TREND", row)
        self.assertIn("THE LEGEND GOVERNS", row)


class NoExecutableChangeTest(unittest.TestCase):
    """What this class derives, stated as narrowly as the methods below actually go.

    Derived here: the free-variable count in both supersets, from
    `load_structure`; the absence of all ten names these two papers could have
    introduced, from both supersets' `.bnd` rules; `E_SPP1_EXPR`'s determinant; and
    where this increment's records were written.

    **NOT derived here, and an earlier docstring claimed otherwise:** byte-identity
    between the v0.5 scaffold and v0.4, which
    `tests/unit/test_v05_scaffold.py::ScaffoldIdentityTest` guards by comparing file
    sets and bytes; and transition rates, initial conditions and inputs, which no
    method below reads. This unit changed nothing under `models/` -- that is visible
    in `git diff` and is not re-derived here. A later unit relying on this class to
    catch an executable change should know its actual reach.
    """

    def test_the_committed_structure_is_unchanged(self) -> None:
        for model in GUARDED_MODELS:
            with self.subTest(model=model):
                facts = load_structure(model, ROOT)
                self.assertEqual(len(facts.free), 19)

    def test_no_candidate_or_source_entity_entered_any_committed_model(self) -> None:
        """Every name these two papers could have introduced, refused at once."""
        forbidden = (
            "JAG1",
            "NOTCH3",
            "HEY1",
            "HES1",
            "MAML1",
            "IL1B",
            "FUT3",
            "ST3GAL3",
            "SLEX_SURFACE",
            "GLYCOSYLATION_PROGRAM",
        )
        for model in GUARDED_MODELS:
            rules = parse_bnd_rules(resolve_model(model, ROOT).network_bnd)
            body = " ".join(rules) + " " + " ".join(rules.values())
            for name in forbidden:
                with self.subTest(model=model, name=name):
                    self.assertNotIn(name, body.upper())

    def test_this_increments_records_went_beside_the_staged_bundle_not_into_it(
        self,
    ) -> None:
        """The staged bundle is the reviewed delta an external reviewer sent. A
        re-adjudication records a NEW verdict against it; it never rewrites it.

        **This replaces a `git status --porcelain` check that the review correctly
        called vacuous**: in a committed state that is empty whether or not the
        bundle was edited and committed, so it asserted nothing about the
        invariant its docstring claimed. The content invariant -- each staged
        file's sha256 against the bundle manifest -- is already enforced by
        `test_literature_staging_quarantine`, and duplicating it here would add no
        coverage.

        What belongs here is the shape of THIS increment: its new records live in
        `reviews/`, beside the bundle, and it wrote nothing into `staging/` at all.
        """
        for artifact in (LEDGER, RELATIONS):
            with self.subTest(artifact=artifact.name):
                self.assertTrue(artifact.is_file())
                self.assertEqual(artifact.parent, REVIEWS)
                self.assertNotIn("staging", artifact.parts)
        tracked = subprocess.run(
            ["git", "ls-files", str(STAGED.relative_to(ROOT))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        self.assertTrue(tracked, "the staged bundle must still be tracked")
        for path in tracked:
            self.assertNotIn("blocked_source_refresh", path)

    def test_the_committed_spp1_determinant_is_untouched(self) -> None:
        """The SPP1 relation is catalogued, not wired. `E_SPP1_EXPR` keeps the
        determinant it had (`E_SECRETORY_STATE`, LE016) in both supersets.
        """
        for model in GUARDED_MODELS:
            evidence = (
                resolve_model(model, ROOT).network_bnd.parent / "edge_evidence.tsv"
            )
            rows = _rows(evidence)
            into_spp1 = {r["source"] for r in rows if r["target"] == "E_SPP1_EXPR"}
            with self.subTest(model=model):
                self.assertEqual(into_spp1, {"E_SECRETORY_STATE"})


if __name__ == "__main__":
    unittest.main()
