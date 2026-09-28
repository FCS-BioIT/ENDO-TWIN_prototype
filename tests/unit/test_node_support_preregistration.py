"""Pin the node-support pre-registration to what the repository actually says.

Section 10.5 of `docs/scrna/node_support_preregistration.md` requires that every
constant and rule it fixes be pinned by a test, so that changing one is a visible
diff rather than a silent retune. That is what this file is for, and it is
deliberately committed in the SAME commit as the document and the expectation
generator, before any audited expression value is read.

The tests are written to fail in both directions. A constant that moves fails
because the number is pinned; a document that drifts from the code fails because
the pre-registration's own tables are re-parsed out of the Markdown and compared
against what the code derives from the committed observation map.
"""

from __future__ import annotations

import ast
import math
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.scrna import node_support_contract as C
from dt_adoc.scrna import node_support_expectations as X
from dt_adoc.scrna.klf12_state import CONTEXT_GENES

PREREG = ROOT / "docs/scrna/node_support_preregistration.md"
DEVIATIONS = ROOT / "docs/scrna/node_support_deviations.md"

#: The registered document's sha256, as committed at `491b337`. The document is
#: the pre-registration; errors in it are corrected in `DEVIATIONS`, never in
#: place. It WAS once amended in place -- 212 lines, in the results commit --
#: which destroyed the one ordering guarantee git could give. This pin is what
#: makes a second such edit impossible to make quietly.
REGISTERED_SHA256 = "77f353359913c970784bc9aa15d9f3a075bd4e8db1d358b2ca3cfa61e6b8186a"


class RegisteredDocumentTest(unittest.TestCase):
    def test_the_pre_registration_is_byte_identical_to_its_commit(self) -> None:
        import hashlib

        digest = hashlib.sha256(PREREG.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            REGISTERED_SHA256,
            "the registered pre-registration has been edited. Corrections belong "
            "in docs/scrna/node_support_deviations.md; if this change is "
            "deliberate, the design is being re-registered and the new digest "
            "must be recorded with the reason.",
        )

    def test_the_deviations_document_exists_and_pins_the_same_digest(self) -> None:
        self.assertIn(REGISTERED_SHA256, DEVIATIONS.read_text())


class FrozenConstantsTest(unittest.TestCase):
    """The four numeric constants of Section 4.1 and the criteria of 5.3."""

    def test_the_four_constants_are_what_was_registered(self) -> None:
        self.assertEqual(C.THETA, 0.01)
        self.assertEqual(C.N_MIN, 300)
        self.assertEqual(C.E_MIN, 1e7)
        self.assertEqual(C.C1_FLOOR, 0.50)

    def test_n_min_is_thetas_inverse_image_and_not_a_choice(self) -> None:
        """`N_MIN` is derived from `THETA`; recompute the derivation, do not trust it."""

        def bound(n: int) -> float:
            return 1 - 0.05 ** (1 / n)

        smallest = next(n for n in range(2, 10_000) if bound(n) < C.THETA)
        self.assertEqual(smallest, 299)
        self.assertAlmostEqual(bound(298), 0.010002, places=6)
        self.assertAlmostEqual(bound(299), 0.009969, places=6)
        self.assertAlmostEqual(bound(300), 0.009936, places=6)
        # N_MIN is the round number immediately above the smallest that works,
        # so it satisfies the derivation with a little room and never less.
        self.assertGreaterEqual(C.N_MIN, smallest)
        self.assertLess(bound(C.N_MIN), C.THETA)

    def test_e_min_excludes_the_weakest_expression_theta_admits(self) -> None:
        """At `E_MIN`, zero detection rules out even the weakest pattern `THETA` allows."""
        zero_detection_bound = 3 / C.E_MIN
        weakest_theta_admits = C.THETA / 15_000
        self.assertAlmostEqual(zero_detection_bound, 3e-7)
        self.assertAlmostEqual(weakest_theta_admits, 6.667e-7, places=9)
        self.assertGreater(weakest_theta_admits / zero_detection_bound, 2.0)

    def test_movement_and_precision_criteria(self) -> None:
        self.assertEqual(C.ROBUST_DETECTION, 0.10)
        self.assertEqual(C.LOG2_FOLD_MIN, 1.0)  # two-fold
        self.assertEqual(C.BOOTSTRAP_B, 2000)
        self.assertEqual(C.BOOTSTRAP_SEED, 20260917)
        self.assertEqual(C.BOOTSTRAP_ALPHA, 0.05)
        self.assertEqual(C.MIN_VOTING_GENES, 2)


class ControlContractTest(unittest.TestCase):
    """C1 and C2: two controls, two jobs, two failure modes."""

    def test_c1_and_c2_genes_are_registered(self) -> None:
        self.assertEqual(C.C1_GENE, {"epithelium": "EPCAM", "stroma": "VIM"})
        self.assertEqual(C.C2_GENE, {"epithelium": "EPCAM", "stroma": "COL1A1"})

    def test_no_control_gene_is_newly_curated(self) -> None:
        """Both controls come from the context-gene list committed by the KLF12 unit."""
        for gene in {*C.C1_GENE.values(), *C.C2_GENE.values()}:
            self.assertIn(gene, CONTEXT_GENES)

    def test_no_control_gene_is_an_audited_measurement_feature(self) -> None:
        """A control must not also be evidence for a node it gates."""
        audited = set(C.audited_genes())
        for gene in {*C.C1_GENE.values(), *C.C2_GENE.values()}:
            self.assertNotIn(gene, audited)

    def test_c2_has_no_free_constant(self) -> None:
        """C2 is a sign comparison. A margin constant would make it tunable."""
        self.assertFalse(hasattr(C, "C2_MARGIN"))
        self.assertFalse(hasattr(C, "C2_FLOOR"))
        self.assertFalse(hasattr(C, "C2_MIN_RATIO"))

    def test_c1_is_a_floor_with_headroom_on_committed_numbers(self) -> None:
        """The correction's whole point: 50% is headroom for C1's genes, not a coin flip.

        These are the pooled values committed by the KLF12 unit before this unit
        began, and they are why `COL1A1` was moved off the absolute floor.
        """
        import json

        marker = json.loads(
            (ROOT / "docs/scrna/klf12_state_findings.json").read_text()
        )["marker_detection"]
        # C1's genes sit at nearly twice the floor: it is a floor, not a
        # threshold the biology has to clear.
        self.assertGreater(marker["EPCAM_epithelial"] / C.C1_FLOOR, 1.9)
        self.assertGreater(marker["VIM_other"] / C.C1_FLOOR, 1.9)
        # COL1A1 sits ON the floor, which is the defect this design corrects:
        # a control it can fail by a coin flip is not a control.
        self.assertLess(marker["COL1A1_other"] / C.C1_FLOOR, 1.05)
        # But it does discriminate the compartments, which is C2's job.
        self.assertGreater(marker["COL1A1_other"], marker["COL1A1_epithelial"])
        self.assertGreater(marker["EPCAM_epithelial"], marker["EPCAM_other"])


class ExclusionRuleTest(unittest.TestCase):
    """R1 is mechanical and recomputed; R2 is a reading and its grounds are checked."""

    def test_r2_grounds_are_still_in_the_committed_map(self) -> None:
        C.verify_r2_grounds()

    def test_r2_excludes_exactly_the_registered_pairs(self) -> None:
        self.assertEqual(
            set(C.R2_EXCLUSIONS),
            {("E_PGR", "PGR"), ("S_PGR", "PGR"), ("E_GP130_STAT3", "STAT3")},
        )

    def test_r2_is_not_applied_to_level_ceilings(self) -> None:
        """Rows carrying a ceiling on LEVEL keep their direction vote.

        This is the distinction R2 rests on, and it is the one a future reader is
        most likely to erase by "tidying" the rule into `transcript is not
        activity`, which would silently delete three more programs.
        """
        programs = C.direction_vote_programs()
        self.assertIn("NR2F2", programs["S_NR2F2"])
        self.assertIn("HAND2", programs["S_HAND2"])
        self.assertIn("WWTR1", programs["S_TAZ_ECM"])

    def test_r1_removes_only_same_class_whole_measurements(self) -> None:
        programs = C.r1_programs()
        # IHH is all of E_IHH, same class as E_PGR.
        self.assertNotIn("IHH", programs["E_PGR"])
        # HAND2 stays in S_PGR: S_HAND2 is its own class, not AC03.
        self.assertIn("HAND2", programs["S_PGR"])
        # MUC1 stays in E_MUC1_SLEX: E_MUC1_BARRIER is AC05, not AC01.
        self.assertIn("MUC1", programs["E_MUC1_SLEX"])
        # A singleton member is never reduced to nothing by R1.
        self.assertEqual(programs["E_IHH"], ("IHH",))

    def test_a_classless_composite_keeps_a_classless_singletons_gene(self) -> None:
        """R1 must not treat every classless row as one shared class.

        The map leaves `v04_function_class` empty for the rows it records as
        classes of one. Grouping on that raw value made `KLF12` and `HAND2`
        count as siblings' whole measurements for the two classless composites.
        It deletes nothing on the committed map, because neither gene appears in
        those programs -- so this drives a map where it would.
        """
        import csv as _csv
        import tempfile

        rows = C.observation_rows()
        header = list(rows[0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.tsv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = _csv.DictWriter(handle, header, delimiter="\t")
                writer.writeheader()
                for row in rows:
                    row = dict(row)
                    # A classless composite that DOES carry a classless
                    # singleton's whole measurement.
                    if row["model_node"] == "S_FGF_MITOGENIC":
                        row["measurement_features"] = "FGF2;FGF7;HAND2"
                    writer.writerow(row)
            programs = C.r1_programs(path)
        self.assertEqual(programs["S_FGF_MITOGENIC"], ("FGF2", "FGF7", "HAND2"))
        self.assertEqual(programs["S_HAND2"], ("HAND2",))

    def test_r1_still_removes_within_a_real_class(self) -> None:
        """The classless fix must not disarm R1 where a class is named."""
        self.assertNotIn("PRL", C.r1_programs()["S_DECIDUALIZED"])
        self.assertNotIn("IGFBP1", C.r1_programs()["S_DECIDUALIZED"])

    def test_level_ceiling_quotes_are_grounded_like_the_exclusions(self) -> None:
        """The rows R2 deliberately does NOT exclude are quoted and checked too."""
        self.assertEqual(
            set(C.LEVEL_CEILING_QUOTES), {"S_NR2F2", "S_HAND2", "S_TAZ_ECM"}
        )
        self.assertFalse(set(C.LEVEL_CEILING_QUOTES) & {n for n, _ in C.R2_EXCLUSIONS})
        rows = C.assessable_nodes()
        for node, sentence in C.LEVEL_CEILING_QUOTES.items():
            self.assertIn(sentence, rows[node]["claim_ceiling"], node)

    def test_direction_vote_programs_match_the_document(self) -> None:
        """Re-parse Section 2.1's table out of the Markdown and compare.

        The document and the code must not be able to disagree about which genes
        vote. Both are derived from the same committed map; this asserts the
        document was not hand-edited away from it.
        """
        text = PREREG.read_text()
        block = text.split("**Resulting direction-vote programs**")[1]
        block = block.split("A program reduced below")[0]
        documented: dict[str, int] = {}
        for line in block.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # The size cell is a bare integer, or "1 each" where one row groups
            # several singleton nodes.
            size = re.match(r"(\d+)", cells[2]) if len(cells) == 3 else None
            if size is None:
                continue
            for node in re.findall(r"`([A-Z0-9_]+)`", cells[0]):
                documented[node] = int(size.group(1))
        self.assertEqual(len(documented), 20)
        derived = C.direction_vote_programs()
        for node, size in documented.items():
            self.assertEqual(len(derived[node]), size, node)


class ScopeTest(unittest.TestCase):
    """What is audited, and what is deliberately not."""

    def test_twenty_seven_assessable_nodes(self) -> None:
        rows = C.observation_rows()
        assessable = C.assessable_nodes()
        self.assertEqual(len(assessable), 27)
        self.assertEqual(len(rows) - len(assessable), 32)

    def test_klf12_is_in_node_support_but_flagged_not_blind(self) -> None:
        self.assertIn("E_KLF12_HIGH", C.assessable_nodes())
        self.assertIn("E_KLF12_HIGH", C.NOT_BLIND_NODES)

    def test_ac05_is_measured_but_never_alias_tested(self) -> None:
        self.assertNotIn("AC05", C.ALIAS_TEST_ORDER)
        self.assertIn("AC05", C.NODE_SUPPORT_ONLY_CLASSES)

    def test_ac03_is_first_and_is_not_the_largest_class(self) -> None:
        """The pre-registration used to justify the order by size. It was wrong."""
        self.assertEqual(C.ALIAS_TEST_ORDER[0], "AC03")
        sizes: dict[str, int] = {}
        for row in C.assessable_nodes().values():
            sizes[row["v04_function_class"]] = (
                sizes.get(row["v04_function_class"], 0) + 1
            )
        self.assertEqual(sizes["AC03"], 5)
        self.assertEqual(sizes["AC01"], 7)
        self.assertGreater(sizes["AC01"], sizes["AC03"])

    def test_every_measurement_observability_value_has_a_phase_a_type(self) -> None:
        for row in C.observation_rows():
            self.assertIn(row["measurement_observability"], C.MEASUREMENT_TYPE)

    def test_compartment_partition_is_complete_and_disjoint(self) -> None:
        """Every one of the object's seven labels lands in exactly one compartment."""
        self.assertEqual(len(C.COMPARTMENT_OF_LABEL), 7)
        self.assertEqual(
            set(C.COMPARTMENT_OF_LABEL.values()),
            {"epithelium", "stroma", "myofibroblast"},
        )
        self.assertNotIn("myofibroblast", C.PRIMARY_COMPARTMENTS)


class ExpectationTableTest(unittest.TestCase):
    """Appendix A is recomputed, and its two stated invariances are proved."""

    def setUp(self) -> None:
        self.rules = X.load_rules()

    def test_only_one_node_depends_on_the_cnt_encoding(self) -> None:
        self.assertEqual(X.disagreements(self.rules), ["E_ESTROGENIC_PROLIFERATION"])

    def test_no_audited_node_depends_on_the_relay_setting(self) -> None:
        """The relays are pinned FALSE by choice, not by `baseline.cfg`.

        The setting is not globally vacuous -- four nodes move with it -- so the
        claim that matters is the intersection with what is audited.
        """
        moved = X.relay_invariance(self.rules)
        self.assertEqual(
            set(moved),
            {
                "X_ADHESION_ROUTE_SPP1",
                "X_ADHESION_ROUTE_REDUNDANT",
                "X_ANTIADHESIVE_ROUTE",
                "OUT_MATERNAL_ADHESION_COMPETENCE",
            },
        )
        self.assertFalse(set(moved) & set(C.assessable_nodes()))

    def test_klf12_is_the_only_free_variable_taking_its_baseline_value(self) -> None:
        """Guard the correction: `baseline.cfg` does NOT set the relays FALSE."""
        cfg = (
            ROOT / "models/superset/adoc-literature-superset-v0.4.0/baseline.cfg"
        ).read_text()
        self.assertIn("E_KLF12_HIGH.istate = FALSE;", cfg)
        for relay in X.RELAYS:
            self.assertNotIn(f"{relay}.istate = FALSE;", cfg)
            self.assertRegex(cfg, rf"\[{relay}\]\.istate = 0\.\d+\[0\], 0\.\d+\[1\];")

    def test_expectations_match_the_documents_appendix(self) -> None:
        """Re-parse Appendix A out of the Markdown and compare to the computation."""
        text = PREREG.read_text()
        documented: dict[str, str] = {}
        for line in text.split("## Appendix A")[1].splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 5:
                continue
            node = re.fullmatch(r"`([A-Z0-9_]+)`", cells[1])
            if node:
                documented[node.group(1)] = cells[4].strip("*")
        computed = {
            r["model_node"]: r["expected_cnt_to_ht"] for r in X.expectation_table()
        }
        self.assertEqual(len(documented), 27)
        self.assertEqual(set(documented), set(computed))
        for node, arrow in documented.items():
            if arrow == "encoding-dependent":
                self.assertEqual(node, "E_ESTROGENIC_PROLIFERATION")
                continue
            self.assertEqual(computed[node], arrow, node)

    def test_appendix_type_errata_match_the_map(self) -> None:
        """Erratum E2: exactly two Appendix A rows disagree with the map.

        The registered document cannot be edited, so what is checked is that the
        deviations document names *precisely* the rows that disagree -- no more,
        so an erratum cannot be invented, and no fewer, so one cannot be missed.
        """
        rows = C.assessable_nodes()
        printed: dict[str, str] = {}
        for line in PREREG.read_text().split("## Appendix A")[1].splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 5:
                continue
            node = re.fullmatch(r"`([A-Z0-9_]+)`", cells[1])
            if node:
                printed[node.group(1)] = cells[3]
        self.assertEqual(len(printed), 27)
        disagreeing = {
            node: C.MEASUREMENT_TYPE_LABEL[C.measurement_type(rows[node])]
            for node, label in printed.items()
            if label != C.MEASUREMENT_TYPE_LABEL[C.measurement_type(rows[node])]
        }
        self.assertEqual(
            disagreeing,
            {"S_HAND2": "direct transcript", "S_FGF_MITOGENIC": "pathway score"},
        )
        errata = DEVIATIONS.read_text()
        section = errata.split("### E2")[1].split("### E3")[0]
        for node, corrected in disagreeing.items():
            self.assertIn(node, section)
            self.assertIn(corrected, section)

    def test_every_map_observability_value_keeps_its_own_type(self) -> None:
        """`pathway_score` is not folded into `gene_program`."""
        self.assertEqual(C.MEASUREMENT_TYPE["pathway_score"], "pathway_score")
        self.assertEqual(
            len(set(C.MEASUREMENT_TYPE.values())), len(set(C.MEASUREMENT_TYPE))
        )

    def test_twenty_switch_on_together_and_three_switch_off(self) -> None:
        """The proposition the audit tests, counted rather than asserted."""
        classed = [
            r
            for r in X.expectation_table()
            if r["v04_function_class"]
            in (*C.ALIAS_TEST_ORDER, *C.NODE_SUPPORT_ONLY_CLASSES)
        ]
        self.assertEqual(len(classed), 23)
        self.assertEqual(
            sum(r["expected_cnt_to_ht"] == "OFF -> ON" for r in classed), 20
        )
        self.assertEqual(
            sum(r["expected_cnt_to_ht"] == "ON -> OFF" for r in classed), 3
        )


class LeakageBoundaryTest(unittest.TestCase):
    """Section 10.1: the audit may not see the model's own outputs."""

    FORBIDDEN = (
        "dt_adoc.simulation",
        "dt_adoc.concordance",
        "dt_adoc.calibration",
        "dt_adoc.scoring",
        "dt_adoc.perturbations",
    )

    def _imports(self, module: Path) -> set[str]:
        tree = ast.parse(module.read_text())
        found: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module)
        return found

    def test_no_audit_module_imports_a_model_output_module(self) -> None:
        for name in (
            "node_support_contract.py",
            "node_support_expectations.py",
            "node_support.py",
        ):
            module = SRC / "dt_adoc/scrna" / name
            if not module.exists():
                continue
            imported = self._imports(module)
            for forbidden in self.FORBIDDEN:
                self.assertFalse(
                    any(
                        i == forbidden or i.startswith(forbidden + ".")
                        for i in imported
                    ),
                    f"{name} imports {forbidden}",
                )

    def test_the_expectation_generator_reads_no_expression_data(self) -> None:
        source = (SRC / "dt_adoc/scrna/node_support_expectations.py").read_text()
        identifiers = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", source))
        for token in ("rds", "per_cell", "Rscript", "subprocess", "LayerData"):
            self.assertNotIn(token, identifiers)
        self.assertNotIn("counts_", source)


class ArithmeticSanityTest(unittest.TestCase):
    """The committed exposure argument, recomputed from the committed table."""

    def test_every_epithelial_unit_clears_e_min_with_margin(self) -> None:
        import csv as _csv

        path = ROOT / "docs/scrna/klf12_state_evidence.tsv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(_csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(rows), 6)
        exposures = {
            r["unit_id"]: int(r["n_cells_epithelial"]) * float(r["median_depth_counts"])
            for r in rows
        }
        for unit, exposure in exposures.items():
            self.assertGreater(exposure, 3 * C.E_MIN, unit)
        # The smallest unit by CELL COUNT is not the smallest by exposure; the
        # pre-registration used to conflate the two.
        smallest_by_cells = min(rows, key=lambda r: int(r["n_cells_epithelial"]))
        self.assertEqual(smallest_by_cells["unit_id"], "SZ25TE_HT")
        self.assertNotEqual(min(exposures, key=exposures.get), "SZ25TE_HT")
        self.assertEqual(min(exposures, key=exposures.get), "SZ10TE_HT")

    def test_three_donors_and_two_conditions(self) -> None:
        self.assertEqual(len(C.DONORS), 3)
        self.assertEqual(len(C.CONDITIONS), 2)
        self.assertEqual(
            len(C.DONORS) * len(C.CONDITIONS) * len(C.PRIMARY_COMPARTMENTS), 12
        )

    def test_sign_agreement_alone_is_weak(self) -> None:
        """Section 5.3's reason for requiring effect size as well as sign."""
        self.assertAlmostEqual(2 * 0.5 ** len(C.DONORS), 0.25)
        self.assertGreater(2 * 0.5 ** len(C.DONORS), 0.05)
        self.assertTrue(math.isclose(0.5 ** len(C.DONORS), 0.125))


if __name__ == "__main__":
    unittest.main()
