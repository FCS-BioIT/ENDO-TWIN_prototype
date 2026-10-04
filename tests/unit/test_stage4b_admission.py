"""G13: admitting real direct interventions (Stage 4b), static half.

``docs/stage4b_direct_admission.md`` §7 pre-registers what is tested here: the
completeness rules C1-C8 against ``config/node_entity_map.tsv``, the approval's
``system_grade`` and declaration digest, a current expressivity artefact, and
the guard that no execution path takes an engagement level. Every compound is
synthetic and lives in a sandbox; the committed declarations and ledger hold no
row.

The runtime half -- a null target and a ``scope_relevant`` target executing with
their claim flags, the N+1 invariant, and the bounded class-agreement check --
is ``tests/integration/test_stage4b_admission_runtime.py``.
"""

from __future__ import annotations

import ast
import csv
import importlib.util
import inspect
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.closure_replay import POST_CLOSURE_FILES
from dt_adoc.concordance.simulate import IMPLEMENTATION_GLOBS
from dt_adoc.perturbations import adjudication, engine
from dt_adoc.perturbations.adjudication import (
    AGGREGATIONS,
    AMBIGUOUS,
    COMPOSITE_ROLES,
    DECLARATION_COLUMNS,
    DECLARATIONS_PATH,
    DERIVED,
    ENTITY_MAP_PATH,
    EXPRESSIVITY_ARTEFACTS,
    MODEL_GAP,
    PROTOCOL_INPUT_ROLES,
    RULE_DERIVED_NODES,
    load_adjudications,
    load_declarations,
    load_entity_map,
)
from dt_adoc.perturbations.engine import InterventionError, load_intervention_library
from dt_adoc.reporting import veto_expressivity


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    # Registered first: a dataclass resolves its annotations through it.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sandbox = _load("o8_sandbox", "tests/fixtures/o8_markerless/sandbox.py")
fixtures = _load("g13_fixtures", "tests/fixtures/stage4b/admission.py")
Compound = fixtures.Compound
V060 = fixtures.V060
ALL = ("epithelium", "stroma", "extracellular")


class _Sandbox(unittest.TestCase):
    """A fresh sandbox per test, copied from one built per class."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._base_tmp = tempfile.TemporaryDirectory()
        cls.base = sandbox.build_sandbox(Path(cls._base_tmp.name) / "root")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._base_tmp.cleanup()

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "root"
        shutil.copytree(self.base, self.root)
        # Each test reads its own sandbox; a shared cache would let one test's
        # verdict on identical content stand in for another's generator patch.
        adjudication._EXPRESSIVITY_CACHE.clear()

    def add(self, compound: Compound, parts: tuple[str, ...] = ()) -> None:
        fixtures.add(sandbox, self.root, compound, parts)

    def load(self):
        return load_intervention_library(self.root)

    def refused(self, pattern: str) -> None:
        with self.assertRaisesRegex(InterventionError, pattern):
            self.load()

    def edit(self, path: Path, old: str, new: str) -> None:
        text = (self.root / path).read_text(encoding="utf-8")
        self.assertIn(old, text)
        (self.root / path).write_text(text.replace(old, new), encoding="utf-8")


#: The O8-fixture shape: one eligible target, hit through one all_of member.
def lifr(known: tuple[str, ...] = ("LIFR@activity",), **kwargs) -> Compound:
    return Compound("g13_lifr", ("E_GP130_STAT3",), known, **kwargs)


class MustRefuseTest(_Sandbox):
    """§7 "G13 must refuse", one rule at a time."""

    def test_c1_a_direct_intervention_with_no_declaration(self) -> None:
        self.add(lifr(), ("evidence", "adjudication", "library"))
        self.refused(r"no declaration in .* \(C1\)")

    def test_c1_two_declarations_of_one_intervention(self) -> None:
        self.add(lifr())
        self.add(lifr(declaration_id="DTD-901"), ("declaration",))
        self.refused(r"already declares .* \(C1\)")

    def test_c2_a_mismatched_target_set(self) -> None:
        self.add(lifr(declaration={"declared_targets": "E_GP130_STAT3;E_LIF"}))
        self.refused(r"declared_targets .* are not the library's targets .* \(C2\)")

    def test_c2_a_stale_library_rows_sha256(self) -> None:
        self.add(lifr(declaration={"library_rows_sha256": "0" * 64}))
        self.refused(r"library rows changed since the declaration .* \(C2\)")

    def test_c3_a_pgr_like_entity_declared_on_s_pgr_only_bath_applied(self) -> None:
        """Bath-applied, so both compartments are reached and E_PGR is omitted."""
        self.add(Compound("g13_pgr", ("S_PGR",), ("PGR@activity",)))
        self.refused(
            r"PGR@activity is carried by E_PGR in the reached epithelium.*\(C3\)"
        )

    def test_c3_entities_on_policy_refused_nodes_cannot_be_represented(self) -> None:
        """A role refusal (a readout) and two node refusals. Each would pass
        unnoticed under a blanket ``derived``: see the next test."""
        cases = {
            "E_PAEP": "PAEP@expression",
            "E_MUC1_BARRIER": "MUC1@activity",
            "E_DAG1_CLEAVED": "DAG1@activity",
        }
        for node, entity in cases.items():
            with self.subTest(node=node):
                self.setUp()
                self.add(lifr(known=("LIFR@activity", entity)))
                self.refused(
                    r"lands on E_\w+, which a veto may not mean.*cannot be represented \(C3\)"
                )

    def test_c3_the_aggregation_rule_does_work(self) -> None:
        """With the three refused nodes re-read as ``derived`` -- the blanket
        reading §3.2 forbids -- the same agents load once their entity is
        classified as unrepresented. So C3 refuses them only because the map
        writes down what those nodes stand for."""
        cases = {
            "E_PAEP": "PAEP@expression",
            "E_MUC1_BARRIER": "MUC1@activity",
            "E_DAG1_CLEAVED": "DAG1@activity",
        }
        for node, entity in cases.items():
            with self.subTest(node=node):
                self.setUp()
                self._blanket_derived(entity)
                self.add(
                    lifr(
                        known=("LIFR@activity", entity),
                        unrepresented=f"{entity}|out_of_scope|none|{fixtures.README}",
                    )
                )
                self.load()

    def _blanket_derived(self, entity: str) -> None:
        name, level = entity.split("@")
        path = self.root / ENTITY_MAP_PATH
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        out = []
        for line in lines:
            cells = line.rstrip("\n").split("\t")
            if cells[2:4] == [name, level] and cells[1]:
                cells[2:6] = ["", "", "", DERIVED]
                line = "\t".join(cells) + "\n"
            out.append(line)
        path.write_text("".join(out), encoding="utf-8")

    def test_c4_a_narrowed_compartment_with_no_source(self) -> None:
        self.add(lifr(reached=("epithelium",)))
        self.refused(r"narrowed to \['epithelium'\] with no source:<source> \(C4\)")

    def test_c4_a_narrowed_compartment_whose_source_does_not_resolve(self) -> None:
        self.add(lifr(reached=("epithelium", "source:docs/no_such_file.md#x")))
        self.refused(r"source docs/no_such_file.md#x does not resolve")

    def test_a_source_outside_the_repository_does_not_resolve(self) -> None:
        """An absolute path and a root-escaping path, each to a real file."""
        for source in ("/etc/passwd", "../../../../../../../../etc/passwd"):
            with self.subTest(source=source):
                self.setUp()
                self.add(lifr(declaration={"target_profile_sources": source}))
                self.refused(rf"source {source} does not resolve")
        self.assertFalse(adjudication._resolves(ROOT, "/etc/passwd", set()))
        self.assertFalse(
            adjudication._resolves(ROOT, "../../../../../../etc/passwd", set())
        )
        self.assertTrue(adjudication._resolves(ROOT, "README.md#x", set()))

    def test_c5_a_subset_of_an_any_of_node(self) -> None:
        self.add(Compound("g13_cd98", ("E_CD98_CD9",), ("SLC3A2@activity",)))
        self.refused(
            r"E_CD98_CD9 is any_of, and the agent leaves \['CD9@activity'\] unhit.*\(C5\)"
        )

    def test_c5_an_ambiguous_target(self) -> None:
        self.add(Compound("g13_pka", ("S_PKA",), ("PRKACA@activity",)))
        self.refused(r"S_PKA is ambiguous .* \(C5\)")

    def test_c5_a_derived_target(self) -> None:
        """No eligible node is ``derived`` in v0.6.0 (the O8c policy refuses those
        roles first), so the map is re-read here to reach C5 on its own."""
        self._blanket_derived("HBEGF@expression")
        self.add(Compound("g13_hbegf", ("E_HBEGF",), ("HBEGF@expression",)))
        self.refused(r"E_HBEGF is derived .* \(C5\)")

    def test_c5_the_integrin_under_an_anti_alpha_v_declaration(self) -> None:
        """Owner decision 7: unapprovable until TI-03, anti-αv included."""
        for known in (
            ("ITGAV@activity",),
            ("ITGB3@activity",),
            (
                "ITGAV@activity",
                "ITGB3@activity",
                "ITGB5@activity",
            ),
        ):
            with self.subTest(known=known):
                self.setUp()
                self.add(Compound("g13_itg", ("E_ITGAVB3_5",), known))
                self.refused(r"E_ITGAVB3_5 is ambiguous .* \(C5\)")

    def test_c5_e_anxa2_actin_stays_ambiguous(self) -> None:
        """§11.2: not resolved here, by implementation or by an approval."""
        self.add(Compound("g13_anxa2", ("E_ANXA2_ACTIN",), ("ANXA2@activity",)))
        self.refused(r"E_ANXA2_ACTIN is ambiguous .* \(C5\)")

    def test_c6_an_unclassified_unrepresented_target(self) -> None:
        """STAT3, bath-applied, reaches the stromal gap S_STAT3."""
        self.add(lifr(known=("LIFR@activity", "STAT3@activity")))
        self.refused(r"STAT3@activity is not represented .* not classified \(C6\)")

    def test_c6_an_entity_with_no_node_at_all_is_unclassified(self) -> None:
        self.add(lifr(known=("LIFR@activity", "IL11@expression")))
        self.refused(r"IL11@expression is not represented .* not classified \(C6\)")

    def test_c6_a_catalog_only_entity_called_out_of_scope(self) -> None:
        for floor in ("floor:S_STAT3", "none"):
            with self.subTest(floor=floor):
                self.setUp()
                self.add(
                    lifr(
                        known=("LIFR@activity", "STAT3@activity"),
                        unrepresented=f"STAT3@activity|out_of_scope|{floor}|{fixtures.README}",
                    )
                )
                self.refused(r"\(C6\)")

    def test_c6_a_model_gap_must_name_its_floor_item(self) -> None:
        self.add(
            lifr(
                known=("LIFR@activity", "STAT3@activity"),
                unrepresented=f"STAT3@activity|scope_relevant|none|{fixtures.README}",
            )
        )
        self.refused(r"is the model gap \['S_STAT3'\] and must name it .*\(C6\)")

    def test_c6_a_staged_candidate_called_out_of_scope(self) -> None:
        self.add(
            lifr(
                known=("LIFR@activity", "IL11@expression"),
                unrepresented=f"IL11@expression|out_of_scope|floor:X_IL11|{fixtures.README}",
            )
        )
        self.refused(
            r"on the §3.5.1 floor \(X_IL11\) and may not be out_of_scope \(C6\)"
        )

    def test_c6_an_unlinked_floor_entity_called_out_of_scope(self) -> None:
        """Amendment A2: the floor is recognised by entity, so omitting the
        floor id cannot turn a staged-candidate entity out_of_scope."""
        # FOXO1@expression and SOX17@expression name floor entities at a level
        # their gap rows do not carry: the floor is matched by entity.
        for entity in (
            "IL11@expression",
            "MAPK3@activity",
            "FOXO1@activity",
            "FOXO1@expression",
            "SOX17@expression",
        ):
            with self.subTest(entity=entity):
                self.setUp()
                self.add(
                    lifr(
                        known=("LIFR@activity", entity),
                        unrepresented=f"{entity}|out_of_scope|none|{fixtures.README}",
                    )
                )
                self.refused(rf"{entity} is the model gap .* and must name it .*\(C6\)")

    def test_c6_an_unknown_floor_item(self) -> None:
        self.add(
            lifr(
                known=("LIFR@activity", "IL11@expression"),
                unrepresented=f"IL11@expression|scope_relevant|floor:X_NOTHING|{fixtures.README}",
            )
        )
        self.refused(r"floor:X_NOTHING, which is not a §3.5.1 floor item \(C6\)")

    def test_c6_classifying_a_represented_entity(self) -> None:
        self.add(
            lifr(unrepresented=f"LIFR@activity|out_of_scope|none|{fixtures.README}")
        )
        self.refused(r"not an unrepresented known target \(C6\)")

    def test_c7_a_declared_target_with_no_named_entity(self) -> None:
        self.add(Compound("g13_two", ("E_GP130_STAT3", "E_LIF"), ("LIFR@activity",)))
        self.refused(r"no known target entity is one E_LIF represents .*\(C7\)")

    def test_c8_a_mismatched_target_declaration_sha256(self) -> None:
        self.add(lifr(approval={"target_declaration_sha256": "f" * 64}))
        self.refused(r"names declaration f{64}, not DTD-900 .*\(C8\)")

    def test_c8_an_approval_naming_no_declaration(self) -> None:
        self.add(lifr(approval={"target_declaration_sha256": ""}))
        self.refused(r"an approval needs target_declaration_sha256 \(C8\)")

    def test_a_non_approvable_system_grade(self) -> None:
        for grade in (
            "immortalised_endometrial_line",
            "endometrial_carcinoma_line",
            "non_endometrial_human",
            "non_human",
        ):
            with self.subTest(grade=grade):
                self.setUp()
                self.add(lifr(real_shape=True, system_grade=grade))
                self.refused(r"an approval needs system_grade .* it has " + grade)

    def test_a_line_only_approval_is_refused_however_many_lines_agree(self) -> None:
        """Both cited ids are lines, so the E2 grade is a line (§6.3)."""
        self.add(lifr(real_shape=True, system_grade="endometrial_carcinoma_line"))
        self.refused(r"line-based E2 measurement is refused")

    def test_the_synthetic_real_split_extends_to_system_grade(self) -> None:
        # A synthetic grade on a real-shape approval, and a real grade on a
        # synthetic one: each is refused.
        self.add(lifr(real_shape=True, system_grade="synthetic_fixture"))
        self.refused(r"an approval needs system_grade")
        self.setUp()
        self.add(lifr(system_grade="primary_human_endometrial"))
        self.refused(r"an approval needs system_grade")

    def test_an_unknown_system_grade(self) -> None:
        self.add(lifr(approval={"decision": "candidate", "system_grade": "primary"}))
        self.refused(r"unknown system_grade 'primary'")

    def test_a_declaration_naming_a_migrated_intervention(self) -> None:
        compound = Compound("mifepristone", ("E_PGR", "S_PGR"), ("PGR@activity",))
        self.add(compound, ("declaration",))
        self.refused(
            r"mifepristone is migrated_legacy_behaviour .* only direct_supported_effect"
        )

    def test_a_stale_expressivity_artefact(self) -> None:
        self.add(lifr())
        path = self.root / EXPRESSIVITY_ARTEFACTS[V060][0]
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self.refused(r"artefact .*v060_veto_expressivity.tsv is stale")

    def test_a_stale_invariance_artefact(self) -> None:
        self.add(lifr())
        path = self.root / EXPRESSIVITY_ARTEFACTS[V060][1]
        path.write_text(
            path.read_text(encoding="utf-8").replace("\tyes\n", "\tno\n", 1)
        )
        self.refused(r"artefact .*v060_veto_invariance.tsv is stale")

    def test_a_missing_expressivity_artefact(self) -> None:
        self.add(lifr())
        (self.root / EXPRESSIVITY_ARTEFACTS[V060][0]).unlink()
        self.refused(r"v060_veto_expressivity.tsv is missing")

    def test_a_version_with_no_artefact(self) -> None:
        """v0.5.2 has no entity map rows and no artefact, so no direct row there."""
        self.add(lifr(model_version="adoc-literature-superset-v0.5.2"))
        self.refused(
            r"has no adoc-literature-superset-v0.5.2 rows|has no expressivity artefact"
        )

    def test_each_generator_refusal_refuses_the_licence(self) -> None:
        """§6.6: where the §5.2 argument does not hold, no approval can stand.

        Each case is triggered in the sandbox's own model or observation map, so
        the licence reaches the generator rather than a mock. The generator-level
        refusals, including the scenario cap and a veto of a free node, are
        pinned one by one in ``tests/unit/test_veto_expressivity.py``
        (``RefusalTest``).
        """
        model = Path("models/superset") / V060
        cases = {
            "a declared transition rate": (
                model / "network.bnd",
                "Node S_NR2F2 {",
                "Node S_NR2F2 {\n  rate_up = 2.0;",
            ),
            "a cyclic network": (
                model / "network.bnd",
                "Node E_IHH {\n  logic = E_PGR;",
                "Node E_IHH {\n  logic = E_PGR or S_NR2F2;",
            ),
            "a free-variable-setting cfg": (
                model / "conditions/basal_maternal.cfg",
                "IN_E2.istate",
                "E_KLF12_HIGH.istate = TRUE;\nIN_E2.istate",
            ),
            "a mixed protocol istate": (
                model / "conditions/basal_maternal.cfg",
                "IN_E2.istate",
                "[IN_PROGESTIN].istate = 0.5[0], 0.5[1];\nIN_E2.istate",
            ),
            "a multi-node istate": (
                model / "conditions/basal_maternal.cfg",
                "IN_E2.istate",
                "[IN_PROGESTIN,IN_cAMP].istate = 0.5[0,0], 0.5[1,1];\nIN_E2.istate",
            ),
            "an uninterpreted istate value": (
                model / "conditions/basal_maternal.cfg",
                "IN_E2.istate = FALSE;",
                "IN_E2.istate = 0.0;",
            ),
            "an unknown activation_status": (
                Path("config/observation_model_map.tsv"),
                "\trejected\t",
                "\tretired\t",
            ),
        }
        for name, (path, old, new) in cases.items():
            with self.subTest(case=name):
                self.setUp()
                self.add(lifr())
                self.edit(path, old, new)
                self.refused(
                    r"the §5.2 generator refuses|cannot hold an approval|cycle"
                )

    def test_a_missing_reference_context_refuses_the_licence(self) -> None:
        self.add(lifr())
        cfg = self.root / "models/superset" / V060 / "conditions"
        (cfg / f"{veto_expressivity.REFERENCE_CONTEXT}.cfg").unlink()
        self.refused(r"the §5.2 generator refuses .*reference context")


class MustAcceptTest(_Sandbox):
    """§7 "G13 must accept"."""

    def test_a_declaration_forcing_two_compartments_with_both_declared(self) -> None:
        self.add(Compound("g13_pgr", ("E_PGR", "S_PGR"), ("PGR@activity",)))
        (effect, other) = self.load()["g13_pgr"]
        self.assertEqual({effect.target_node, other.target_node}, {"E_PGR", "S_PGR"})

    def test_a_narrowed_declaration_with_a_source_needs_only_what_it_reaches(
        self,
    ) -> None:
        """The other side of C3/C4: epithelium only, sourced, so S_PGR is not forced."""
        self.add(
            Compound(
                "g13_pgr",
                ("E_PGR",),
                ("PGR@activity",),
                reached=("epithelium", f"source:{fixtures.README}"),
            )
        )
        self.load()

    def test_an_all_of_node_hit_through_one_member(self) -> None:
        self.add(lifr())
        (effect,) = self.load()["g13_lifr"]
        self.assertTrue(effect.adjudication_id)

    def test_an_any_of_node_hit_through_every_member(self) -> None:
        self.add(
            Compound("g13_cd98", ("E_CD98_CD9",), ("SLC3A2@activity", "CD9@activity"))
        )
        self.load()

    def test_a_line_corroborated_approval_whose_qualifying_evidence_is_primary(
        self,
    ) -> None:
        """Two cited ids, one primary E2 measurement and one line; graded by the E2."""
        self.add(lifr(real_shape=True, system_grade="primary_human_endometrial"))
        (effect,) = self.load()["g13_lifr"]
        self.assertEqual(len(effect.evidence_ids), 2)

    def test_every_approvable_grade(self) -> None:
        for grade in adjudication.APPROVABLE_SYSTEM_GRADES:
            with self.subTest(grade=grade):
                self.setUp()
                self.add(lifr(real_shape=True, system_grade=grade))
                self.load()

    def test_an_approved_null_target_licenses(self) -> None:
        """§5.6: null is a reporting condition, never a refusal. Its execution and
        ``phenotype_claim_blocked`` are checked at runtime."""
        self.add(Compound("g13_hbegf", ("E_HBEGF",), ("HBEGF@expression",)))
        (effect,) = self.load()["g13_hbegf"]
        self.assertTrue(effect.adjudication_id)

    def test_a_scope_relevant_unrepresented_target_licenses(self) -> None:
        """Owner decision 4: it blocks the compound claim, not the licence."""
        self.add(
            lifr(
                known=("LIFR@activity", "STAT3@activity"),
                unrepresented=f"STAT3@activity|scope_relevant|floor:S_STAT3|{fixtures.README}",
            )
        )
        self.load()

    def test_an_unlinked_out_of_scope_entity_is_judgement_not_refusal(self) -> None:
        """An entry naming no floor item, for an entity no gap row carries, is J2
        reviewer judgement (owner choice: floor items are cited by id)."""
        self.add(
            lifr(
                known=("LIFR@activity", "CYP3A4@activity"),
                unrepresented=f"CYP3A4@activity|out_of_scope|none|{fixtures.README}",
            )
        )
        self.load()

    def test_a_declaration_without_rows_licenses_nothing(self) -> None:
        self.add(lifr(), ("evidence", "declaration"))
        self.assertNotIn("g13_lifr", self.load())


class EntityMapTest(unittest.TestCase):
    """§3.2: the committed reading of v0.6.0."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.map = load_entity_map(ROOT)
        cls.rows = cls.map[V060]
        cls.by_node: dict[str, list] = {}
        for row in cls.rows:
            if row.node_id:
                cls.by_node.setdefault(row.node_id, []).append(row)
        with (ROOT / "models/superset" / V060 / "node_dictionary.tsv").open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.roles = {
                r["node_id"]: r["model_role"]
                for r in csv.DictReader(handle, delimiter="\t")
            }

    def aggregation(self, node: str) -> str:
        return self.by_node[node][0].aggregation

    def test_it_covers_exactly_the_45_non_input_nodes(self) -> None:
        expected = {n for n, r in self.roles.items() if r not in PROTOCOL_INPUT_ROLES}
        self.assertEqual(set(self.by_node), expected)
        self.assertEqual(len(expected), 45)
        adjudication.check_entity_map_coverage(self.rows, V060, ROOT)

    def test_only_v060_is_mapped(self) -> None:
        self.assertEqual(set(self.map), {V060})

    def test_a_node_the_map_does_not_mention_is_refused(self) -> None:
        with self.assertRaisesRegex(InterventionError, r"missing \['E_PGR'\]"):
            adjudication.check_entity_map_coverage(
                tuple(r for r in self.rows if r.node_id != "E_PGR"), V060, ROOT
            )

    def test_derived_is_exactly_the_composites_and_two_abstractions(self) -> None:
        derived = {n for n in self.by_node if self.aggregation(n) == DERIVED}
        expected = {
            n for n, r in self.roles.items() if r in COMPOSITE_ROLES
        } | RULE_DERIVED_NODES
        self.assertEqual(derived, expected)

    def test_refused_nodes_that_stand_for_entities_keep_their_aggregation(self) -> None:
        """§3.2: the reason C3 can see a PAEP-, MUC1- or DAG1-directed agent."""
        expected = {
            "E_PAEP": ("single", {("PAEP", "expression")}),
            "S_PRL": ("single", {("PRL", "expression")}),
            "S_IGFBP1": ("single", {("IGFBP1", "expression")}),
            "E_MUC1_BARRIER": ("single", {("MUC1", "activity")}),
            "E_MUC1_SLEX": ("single", {("MUC1", "activity")}),
            "E_DAG1_FULL": ("single", {("DAG1", "activity")}),
            "E_DAG1_CLEAVED": ("single", {("DAG1", "activity")}),
            "S_BMP2": (AMBIGUOUS, None),
        }
        for node, (aggregation, entities) in expected.items():
            with self.subTest(node=node):
                self.assertEqual(self.aggregation(node), aggregation)
                if entities is not None:
                    self.assertEqual(
                        {(r.entity, r.level) for r in self.by_node[node]}, entities
                    )

    def test_the_ambiguous_nodes_are_exactly_the_four_the_preregistration_names(
        self,
    ) -> None:
        """E_ITGAVB3_5 (decision 7), E_ANXA2_ACTIN and S_PKA (§11.2, open) and
        S_BMP2 (§3.2). None is resolved here."""
        ambiguous = {n for n in self.by_node if self.aggregation(n) == AMBIGUOUS}
        self.assertEqual(ambiguous, {"E_ITGAVB3_5", "E_ANXA2_ACTIN", "S_PKA", "S_BMP2"})

    def test_the_model_gaps_are_exactly_the_floor(self) -> None:
        """Amendment A2: every §3.5.1 floor item has an entity reading, the four
        catalog_only targets of §3.2 among them."""
        gaps = {r.gap_id for r in self.rows if r.aggregation == MODEL_GAP}
        self.assertEqual(gaps, set(adjudication.scope_floor(V060, ROOT)))
        self.assertTrue(
            {"S_STAT3", "S_DECIDUAL_SENESCENCE_BALANCED", "X_LGALS1_3", "X_BSG_ITGB1"}
            <= gaps
        )
        adjudication.check_floor_coverage(self.rows, V060, ROOT)

    def test_a_root_without_the_floor_table_is_refused_by_name(self) -> None:
        """Only where a direct row needs the floor; a named refusal, not a crash."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "models", root / "models")
            with self.assertRaisesRegex(InterventionError, r"floor needs .*missing"):
                adjudication.scope_floor(V060, root)

    def test_a_floor_item_without_a_reading_is_refused(self) -> None:
        rows = tuple(r for r in self.rows if r.gap_id != "X_IL11")
        with self.assertRaisesRegex(InterventionError, r"unread \['X_IL11'\]"):
            adjudication.check_floor_coverage(rows, V060, ROOT)

    def test_the_floor(self) -> None:
        """§3.5.1: 5 non-executable catalogue targets and 14 staged candidates."""
        floor = adjudication.scope_floor(V060, ROOT)
        self.assertEqual(len(floor), 19)
        self.assertIn("IN_UTERINE_WNT_CUE", floor)
        self.assertIn("X_IL11", floor)

    def test_the_vocabulary(self) -> None:
        self.assertEqual({r.aggregation for r in self.rows}, set(AGGREGATIONS))

    def test_every_basis_exists(self) -> None:
        for row in self.rows:
            for basis in row.basis.split(";"):
                with self.subTest(row=row.node_id or row.gap_id, basis=basis):
                    self.assertTrue((ROOT / basis.split("#", 1)[0]).is_file())


class ConstructionOverlapTest(unittest.TestCase):
    """§6.5: generated, recorded, never refused."""

    def test_the_pc6_example(self) -> None:
        """§6.5 names REF-011: the knockdown source (LIT-PC6-002) is also a source
        of the PC6 -> DAG1 -> receptive-surface edges (LE011, LE012, LE027,
        LE033). The rule -- every edge on a path from the target to O -- also
        finds LE069 and LE073 (LIT-PC6-001) and LE086 (LIT-BARRIER-001, which
        cites REF-011), so the example names a subset of what the rule flags."""
        overlap = adjudication.construction_overlap(
            V060, {"E_PC6"}, {"LIT-PC6-002"}, ROOT
        )
        self.assertEqual(overlap, "REF-011:LE011,LE012,LE027,LE033,LE069,LE073,LE086")

    def test_no_overlap_reads_none(self) -> None:
        self.assertEqual(
            adjudication.construction_overlap(V060, {"E_LIF"}, {"LIT-PC6-002"}, ROOT),
            "none",
        )

    def test_a_hand_written_overlap_is_refused(self) -> None:
        """It is generated, so a declaration cannot understate it."""
        case = MustRefuseTest("test_c1_a_direct_intervention_with_no_declaration")
        case.setUpClass()
        try:
            case.setUp()
            case.add(lifr(declaration={"construction_overlap": "REF-999:LE001"}))
            case.refused(r"construction_overlap is generated and reads 'none'")
        finally:
            case.doCleanups()
            case.tearDownClass()


class CommittedAdmissionTest(unittest.TestCase):
    """The committed state: no declaration, no approval, no direct row."""

    def test_the_committed_declarations_and_ledger_hold_no_row(self) -> None:
        self.assertEqual(load_declarations(ROOT), {})
        self.assertEqual(load_adjudications(ROOT), {})
        header = (ROOT / DECLARATIONS_PATH).read_text(encoding="utf-8")
        self.assertEqual(header, "\t".join(DECLARATION_COLUMNS) + "\n")

    def test_the_ledger_grew_by_the_two_preregistered_columns(self) -> None:
        """§6.2: 15 to 17 columns."""
        self.assertEqual(len(adjudication.ADJUDICATION_COLUMNS), 17)
        self.assertEqual(
            adjudication.ADJUDICATION_COLUMNS[-2:],
            ("system_grade", "target_declaration_sha256"),
        )

    def test_the_committed_artefacts_are_current(self) -> None:
        adjudication._EXPRESSIVITY_CACHE.clear()
        adjudication.expressivity_classes(V060, ROOT)

    def test_artefact_paths_agree_with_the_generator(self) -> None:
        self.assertEqual(
            EXPRESSIVITY_ARTEFACTS[V060],
            (veto_expressivity.OUTPUT_PATH, veto_expressivity.INVARIANCE_PATH),
        )
        self.assertEqual(PROTOCOL_INPUT_ROLES, veto_expressivity.PROTOCOL_INPUT_ROLES)

    def test_the_new_config_files_are_wired_as_preregistered(self) -> None:
        """§10 item 3: closure replay and the implementation digest."""
        for path in (ENTITY_MAP_PATH, DECLARATIONS_PATH):
            with self.subTest(path=path):
                self.assertIn(str(path), POST_CLOSURE_FILES)
                self.assertIn(str(path), IMPLEMENTATION_GLOBS)
        # Amendment A1: the licence reads the generator, the observation map
        # and both tables, so the digest covers them (§9 had kept them out on
        # the premise that no execution path read them).
        for path in (
            *EXPRESSIVITY_ARTEFACTS[V060],
            Path("src/dt_adoc/reporting/veto_expressivity.py"),
            veto_expressivity.OBSERVATION_MAP_PATH,
        ):
            with self.subTest(path=path):
                self.assertIn(str(path), IMPLEMENTATION_GLOBS)


#: The modules that build engagement grids (§4.5). Only the CLI and the PROFILE
#: parity tests may reach them.
ENGAGEMENT_MODULES = {
    "dt_adoc.perturbations.target_engagement",
    "dt_adoc.perturbations.single",
    "dt_adoc.perturbations.combinations",
    "dt_adoc.perturbations.synergy",
}
#: Every module an execution of a library intervention passes through.
EXECUTION_ROOTS = (
    "dt_adoc.simulation.runner",
    "dt_adoc.perturbations.engine",
    "dt_adoc.perturbations.adjudication",
    "dt_adoc.protocols.runner",
    "dt_adoc.protocols.conditions",
    "dt_adoc.concordance.simulate",
)


def _imports(module: str) -> set[str]:
    path = SRC / (module.replace(".", "/") + ".py")
    if not path.is_file():
        path = SRC / module.replace(".", "/") / "__init__.py"
    if not path.is_file():
        return set()
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return {name for name in found if name.startswith("dt_adoc")}


class EngagementGuardTest(unittest.TestCase):
    """§4.5: no execution path accepts an engagement level, and the
    engagement-grid helpers are reachable from no runner or engine path."""

    def test_the_grid_helpers_are_unreachable_from_execution(self) -> None:
        seen, todo = set(), list(EXECUTION_ROOTS)
        while todo:
            module = todo.pop()
            if module in seen:
                continue
            seen.add(module)
            todo.extend(_imports(module))
        self.assertEqual(seen & ENGAGEMENT_MODULES, set())

    def test_no_execution_entry_point_takes_an_engagement_argument(self) -> None:
        from dt_adoc.simulation import runner

        functions = (
            runner.run_cmaboss_condition,
            runner.run_protocol,
            engine.intervention_logic_overrides,
            engine.render_interventions,
            engine.load_intervention_library,
            adjudication.license_effect,
            adjudication.check_admission,
        )
        for function in functions:
            with self.subTest(function=function.__qualname__):
                names = set(inspect.signature(function).parameters)
                self.assertFalse(
                    {n for n in names if "engag" in n or "dose" in n or "fraction" in n}
                )

    def test_a_library_row_has_no_engagement_column(self) -> None:
        self.assertFalse([c for c in engine.LIBRARY_COLUMNS if "engag" in c])
        self.assertEqual(engine.DIRECT_MODES, ("activity_veto",))


if __name__ == "__main__":
    unittest.main()
