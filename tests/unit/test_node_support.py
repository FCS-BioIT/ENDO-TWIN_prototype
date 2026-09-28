"""Behavioural tests for the node-support derivation.

These drive `dt_adoc.scrna.node_support` on small synthetic per-cell tables, so
they need no R, no 2.9 GB object and no network. What they pin is the behaviour
the pre-registration specifies and that a reader of the artifacts has to be able
to rely on: which units can support an absence, how a member is
direction-called, and which of the two controls gates which conclusion.
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.scrna import node_support as N
from dt_adoc.scrna import node_support_contract as C

EPI = "Luminal-like epithelium"
STR = "Stroma"


def write_per_cell(path: Path, rows: list[dict[str, object]], genes: list[str]) -> None:
    header = ["sample_id", "celltype_v2", "depth_counts", "nfeature_counts"] + [
        f"counts_{g}" for g in genes
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, header, delimiter="\t")
        writer.writeheader()
        # A gene a row does not mention is zero, not blank: the real extraction
        # writes a value for every requested feature in every cell.
        writer.writerows(
            [{**{f"counts_{g}": 0.0 for g in genes}, **row} for row in rows]
        )


def make_rows(
    sample: str, label: str, n: int, values: dict[str, float], depth: float = 10_000.0
) -> list[dict[str, object]]:
    return [
        {
            "sample_id": sample,
            "celltype_v2": label,
            "depth_counts": depth,
            "nfeature_counts": 100,
            **{f"counts_{g}": v for g, v in values.items()},
        }
        for _ in range(n)
    ]


class PartitionTest(unittest.TestCase):
    def test_an_unknown_label_is_a_contradiction_not_a_cell_to_drop(self) -> None:
        """The pre-registration calls the partition complete over all cells."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            write_per_cell(
                path,
                make_rows("SZ09TE_CNT", "Neutrophil", 3, {"EPCAM": 1.0}),
                ["EPCAM"],
            )
            with self.assertRaises(N.NodeSupportError) as caught:
                N.read_per_cell(path)
        self.assertIn("frozen compartment partition", str(caught.exception))

    def test_sample_id_is_the_whole_of_the_donor_structure(self) -> None:
        self.assertEqual(N.parse_unit("SZ09TE_CNT"), ("SZ09", "CNT"))
        with self.assertRaises(N.NodeSupportError):
            N.parse_unit("SZ09_CNT")
        with self.assertRaises(N.NodeSupportError):
            N.parse_unit("SZ09TE_OTHER")


class ControlsTest(unittest.TestCase):
    """C1 gates absence POWER; C2 gates compartment ATTRIBUTION. Never merged."""

    @staticmethod
    def _unit(
        sample: str, label: str, n: int, shares: dict[str, float], genes: list[str]
    ):
        """A unit of exactly `n` cells with the given per-gene detection shares.

        Depth is set so the unit clears `E_MIN` comfortably: these fixtures are
        for the CONTROLS, and a unit that failed the exposure floor first would
        test nothing about them.
        """
        rows = []
        cuts = {g: round(shares.get(g, 0.0) * n) for g in genes}
        for i in range(n):
            rows.append(
                {
                    "sample_id": sample,
                    "celltype_v2": label,
                    "depth_counts": 30_000.0,
                    "nfeature_counts": 100,
                    **{f"counts_{g}": (1.0 if i < cuts[g] else 0.0) for g in genes},
                }
            )
        return rows

    def _qc(self, epcam_epi: float, col1a1_str: float, col1a1_epi: float, vim: float):
        genes = ["EPCAM", "VIM", "COL1A1"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            rows = self._unit(
                "SZ09TE_CNT",
                EPI,
                500,
                {"EPCAM": epcam_epi, "COL1A1": col1a1_epi},
                genes,
            ) + self._unit(
                "SZ09TE_CNT", STR, 500, {"VIM": vim, "COL1A1": col1a1_str}, genes
            )
            write_per_cell(path, rows, genes)
            cells = N.read_per_cell(path)
            order = sorted(cells.by_unit)
            stats = {u: N.unit_statistics(cells, u, i) for i, u in enumerate(order)}
            return {u: N.unit_qc(stats, u) for u in order}

    def test_c1_failure_removes_absence_power(self) -> None:
        qc = self._qc(epcam_epi=0.2, col1a1_str=0.9, col1a1_epi=0.0, vim=0.9)
        epi = qc["SZ09_CNT_epithelium"]
        self.assertFalse(epi.c1_pass)
        self.assertFalse(epi.absence_informative)
        self.assertEqual(epi.uninformative_reason, "uninformative_integrity")

    def test_c2_failure_leaves_power_untouched(self) -> None:
        """A specificity failure is an attribution finding, never a power one."""
        # COL1A1 higher in epithelium than in stroma: the assignment is suspect,
        # but both units are large, deep and pass C1.
        qc = self._qc(epcam_epi=0.99, col1a1_str=0.10, col1a1_epi=0.90, vim=0.99)
        stroma = qc["SZ09_CNT_stroma"]
        self.assertFalse(stroma.c2_pass)
        self.assertEqual(stroma.attribution, "compartment_attribution_unsafe")
        self.assertTrue(stroma.c1_pass)
        self.assertTrue(stroma.absence_informative)
        self.assertEqual(stroma.uninformative_reason, "")

    def test_both_controls_pass_on_a_healthy_unit(self) -> None:
        qc = self._qc(epcam_epi=0.99, col1a1_str=0.60, col1a1_epi=0.10, vim=0.99)
        for unit in ("SZ09_CNT_epithelium", "SZ09_CNT_stroma"):
            self.assertTrue(qc[unit].c1_pass, unit)
            self.assertTrue(qc[unit].c2_pass, unit)
            self.assertTrue(qc[unit].absence_informative, unit)

    def test_the_committed_run_keeps_the_two_failures_distinct(self) -> None:
        """No unit in the shipped artifact may carry a merged QC reason."""
        path = ROOT / "docs/scrna/node_support_qc.tsv"
        if not path.is_file():
            self.skipTest("artifact not generated in this checkout")
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["c2_pass"] == "false" and row["c1_pass"] == "true":
                    # C2 alone must never make a unit absence-uninformative.
                    self.assertNotEqual(
                        row["uninformative_reason"], "uninformative_integrity"
                    )


class VotingRuleTest(unittest.TestCase):
    """Section 2.1's guard is about REDUCTION by R1/R2, not about program size."""

    def test_eleven_members_vote_with_a_single_gene(self) -> None:
        """The frozen table lists these with `n = 1` under "genes voting"."""
        programs = C.direction_vote_programs()
        singletons = [
            node
            for node in (
                "E_IHH",
                "S_NR2F2",
                "S_BMP2",
                "S_PRL",
                "S_IGFBP1",
                "S_SPP1",
                "E_LIF",
                "E_PAEP",
                "E_PC6",
                "E_HBEGF",
                "E_SPP1_EXPR",
            )
        ]
        self.assertEqual(len(singletons), 11)
        for node in singletons:
            self.assertEqual(len(programs[node]), 1, node)
            committed = C.features(C.assessable_nodes()[node])
            # Never REDUCED below two -- there was only ever one.
            self.assertEqual(len(committed), 1, node)

    def test_a_single_gene_member_is_direction_callable(self) -> None:
        """Reading the guard as "fewer than two genes" made eleven of twenty
        members permanently undecidable, and contradicted the observation map's
        own statement that a `S_PRL`/`S_IGFBP1` divergence is a falsification."""
        stats = self._two_arm_stats({"PRL": (1.0, 64.0)})
        verdict = N.member_verdict("S_PRL", "stroma", stats, {})
        self.assertNotEqual(verdict["verdict"], "uninformative")
        self.assertEqual(verdict["program"], ["PRL"])
        self.assertEqual(set(verdict["per_donor"].values()), {"moves_up"})

    def _two_arm_stats(self, genes: dict[str, tuple[float, float]]):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            names = sorted(genes)
            rows = []
            for donor in C.DONORS:
                for arm, which in (("CNT", 0), ("HT", 1)):
                    rows += make_rows(
                        f"{donor}TE_{arm}",
                        STR,
                        400,
                        {g: genes[g][which] for g in names},
                    )
            write_per_cell(path, rows, names)
            cells = N.read_per_cell(path)
            order = sorted(cells.by_unit)
            return {u: N.unit_statistics(cells, u, i) for i, u in enumerate(order)}

    def test_an_unmeasured_donor_is_not_evidence_of_non_movement(self) -> None:
        """A donor whose compartment-unit does not exist supplies nothing.

        `gene_movement` returns `uninformative` for a missing unit. An earlier
        revision folded that into `no_material_move` with every other non-call,
        so a donor that was never measured became evidence of NON-movement and
        could carry a `divergent` verdict by itself. A zero-cell
        compartment-unit is real in this dataset -- `SZ09_HT_myofibroblast` --
        so the guard is not hypothetical.
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            rows = []
            for donor in C.DONORS:
                for arm in C.CONDITIONS:
                    if donor == "SZ25" and arm == "HT":
                        continue  # the unit never existed
                    rows += make_rows(f"{donor}TE_{arm}", STR, 400, {"PRL": 4.0})
            write_per_cell(path, rows, ["PRL"])
            cells = N.read_per_cell(path)
            order = sorted(cells.by_unit)
            stats = {u: N.unit_statistics(cells, u, i) for i, u in enumerate(order)}
            verdict = N.member_verdict("S_PRL", "stroma", stats, {})
        self.assertEqual(verdict["per_donor"]["SZ25"], "uninformative")
        self.assertEqual(verdict["verdict"], "uninformative")
        self.assertNotEqual(verdict["verdict"], "divergent")

    def test_a_present_donor_still_calls_normally_beside_a_missing_one(self) -> None:
        """The guard must not silence donors that were measured."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            rows = []
            for donor in C.DONORS:
                for arm in C.CONDITIONS:
                    if donor == "SZ25" and arm == "HT":
                        continue
                    rows += make_rows(
                        f"{donor}TE_{arm}",
                        STR,
                        400,
                        {"PRL": 1.0 if arm == "CNT" else 64.0},
                    )
            write_per_cell(path, rows, ["PRL"])
            cells = N.read_per_cell(path)
            order = sorted(cells.by_unit)
            stats = {u: N.unit_statistics(cells, u, i) for i, u in enumerate(order)}
            verdict = N.member_verdict("S_PRL", "stroma", stats, {})
        self.assertEqual(verdict["per_donor"]["SZ09"], "moves_up")
        self.assertEqual(verdict["per_donor"]["SZ10"], "moves_up")
        self.assertEqual(verdict["per_donor"]["SZ25"], "uninformative")
        self.assertEqual(verdict["verdict"], "uninformative")

    def test_movement_needs_both_separation_and_two_fold(self) -> None:
        """Criterion (a) alone passes on cell count; (b) alone passes on noise."""
        # Identical in both arms: no separation, no fold.
        flat = self._two_arm_stats({"PRL": (4.0, 4.0)})
        self.assertEqual(
            N.gene_movement("PRL", "SZ09", "stroma", flat), "no_material_move"
        )
        # A large, separated change clears both.
        big = self._two_arm_stats({"PRL": (1.0, 64.0)})
        self.assertEqual(N.gene_movement("PRL", "SZ09", "stroma", big), "moves_up")
        self.assertEqual(
            N.gene_movement(
                "PRL", "SZ09", "stroma", self._two_arm_stats({"PRL": (64.0, 1.0)})
            ),
            "moves_down",
        )

    def test_a_small_but_perfectly_separated_change_does_not_move(self) -> None:
        """Constant-per-cell values give a zero-width interval; only (b) can stop it."""
        small = self._two_arm_stats({"PRL": (4.0, 5.0)})
        self.assertEqual(
            N.gene_movement("PRL", "SZ09", "stroma", small), "no_material_move"
        )


class ClassVerdictTest(unittest.TestCase):
    """Section 5.4's four verdicts, and the pattern it does not name."""

    @staticmethod
    def _members(*verdicts: str) -> dict[str, dict[str, object]]:
        return {f"N{i}": {"verdict": v} for i, v in enumerate(verdicts)}

    def test_alias_challenged_needs_a_concordant_and_a_divergent(self) -> None:
        self.assertEqual(
            N.class_verdict(self._members("concordant_with_alias", "divergent")),
            "alias_challenged",
        )

    def test_rule_challenged_is_all_divergent_together(self) -> None:
        self.assertEqual(
            N.class_verdict(self._members("divergent", "divergent", "divergent")),
            "rule_challenged",
        )

    def test_consistent_with_alias_confirms_nothing_but_is_its_own_verdict(
        self,
    ) -> None:
        self.assertEqual(
            N.class_verdict(
                self._members("concordant_with_alias", "concordant_with_alias")
            ),
            "consistent_with_alias",
        )

    def test_uninformative_means_what_it_says(self) -> None:
        """Its stated condition is FEWER THAN TWO direction-callable members."""
        self.assertEqual(
            N.class_verdict(
                self._members("divergent", "uninformative", "uninformative")
            ),
            "uninformative",
        )

    def test_a_pattern_section_5_4_does_not_name_is_not_called_uninformative(
        self,
    ) -> None:
        """Divergent + inconsistent, and all-inconsistent, meet no stated condition.

        Reporting either as `uninformative` would assert that fewer than two
        members were direction-callable, which is false.
        """
        for members in (
            self._members("divergent", "inconsistent", "inconsistent"),
            self._members("inconsistent", "inconsistent"),
        ):
            self.assertEqual(N.class_verdict(members), "unclassified_by_section_5_4")


class DeterminismTest(unittest.TestCase):
    def test_a_units_draw_is_fixed_by_its_ordinal_and_nothing_else(self) -> None:
        """Same ordinal reproduces; a different ordinal is a different unit.

        Named for what it checks. The property that the ordinal comes from a
        SORTED unit list, which is what actually makes `--from-per-cell`
        independent of dict iteration order, is checked separately below.
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            rows = make_rows("SZ09TE_CNT", EPI, 50, {"PAEP": 1.0})
            rows += make_rows("SZ09TE_CNT", EPI, 50, {"PAEP": 0.0})
            write_per_cell(path, rows, ["PAEP"])
            cells = N.read_per_cell(path)
            first = N.unit_statistics(cells, "SZ09_CNT_epithelium", 0)
            second = N.unit_statistics(cells, "SZ09_CNT_epithelium", 0)
            other = N.unit_statistics(cells, "SZ09_CNT_epithelium", 1)
        self.assertEqual(first.f_ci["gene:PAEP"], second.f_ci["gene:PAEP"])
        # A different ordinal is a different unit and must draw differently.
        self.assertNotEqual(first.f_ci["gene:PAEP"], other.f_ci["gene:PAEP"])

    def test_the_ordinal_comes_from_a_sorted_unit_list(self) -> None:
        """This is what makes the seeding independent of iteration order.

        `derive` must not hand out ordinals in whatever order the units happened
        to be inserted, or two runs over the same table could seed differently.
        """
        import ast
        import inspect

        source = inspect.getsource(N.derive)
        tree = ast.parse(source.lstrip())
        sorted_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "sorted"
        ]
        self.assertTrue(sorted_calls, "derive does not sort the units")
        self.assertIn("enumerate(ordered)", source)
        self.assertIn("sorted(cells.by_unit)", source)


class NodeAggregationTest(unittest.TestCase):
    """Section 4.0: `d_node` is the union over the node's features."""

    def test_node_detection_is_the_union_of_its_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            genes = sorted(C.features(C.assessable_nodes()["E_CD98_CD9"]))
            self.assertEqual(genes, ["CD9", "SLC3A2"])
            # Disjoint carriers: 40 cells carry only CD9, 40 only SLC3A2.
            rows = make_rows("SZ09TE_CNT", EPI, 40, {"CD9": 1.0, "SLC3A2": 0.0})
            rows += make_rows("SZ09TE_CNT", EPI, 40, {"CD9": 0.0, "SLC3A2": 1.0})
            rows += make_rows("SZ09TE_CNT", EPI, 20, {"CD9": 0.0, "SLC3A2": 0.0})
            write_per_cell(path, rows, genes)
            cells = N.read_per_cell(path)
            stats = N.unit_statistics(cells, "SZ09_CNT_epithelium", 0)
        self.assertAlmostEqual(stats.d["gene:CD9"], 0.40)
        self.assertAlmostEqual(stats.d["gene:SLC3A2"], 0.40)
        # Union, not mean (0.40) and not intersection (0.0).
        self.assertAlmostEqual(stats.d["node:E_CD98_CD9"], 0.80)

    def test_a_node_is_undetected_only_when_every_feature_is(self) -> None:
        """The label that licenses a structural change is invariant to Section 4.0."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            genes = ["CD9", "SLC3A2"]
            rows = make_rows("SZ09TE_CNT", EPI, 100, {"CD9": 0.0, "SLC3A2": 0.0})
            write_per_cell(path, rows, genes)
            cells = N.read_per_cell(path)
            stats = N.unit_statistics(cells, "SZ09_CNT_epithelium", 0)
        self.assertEqual(stats.d["node:E_CD98_CD9"], 0.0)


class QcArtifactSemanticsTest(unittest.TestCase):
    """C2 is not evaluated for a compartment with no complement."""

    def _qc_for(self, compartment_label: str):
        genes = ["EPCAM", "VIM", "COL1A1"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            rows = ControlsTest._unit(
                "SZ09TE_CNT", EPI, 500, {"EPCAM": 0.99}, genes
            ) + ControlsTest._unit(
                "SZ09TE_CNT",
                compartment_label,
                500,
                {"VIM": 0.99, "COL1A1": 0.6},
                genes,
            )
            write_per_cell(path, rows, genes)
            cells = N.read_per_cell(path)
            order = sorted(cells.by_unit)
            stats = {u: N.unit_statistics(cells, u, i) for i, u in enumerate(order)}
            return {u: N.unit_qc(stats, u) for u in order}

    def test_myofibroblast_c2_is_not_applicable_not_a_failure(self) -> None:
        """It has no complement in the primary partition, so there is no test.

        Reporting `compartment_attribution_unsafe` would be an accusation the
        test was never run to make.
        """
        qc = self._qc_for("Myofibroblast")
        myo = qc["SZ09_CNT_myofibroblast"]
        self.assertFalse(myo.c2_evaluated)
        self.assertEqual(myo.attribution, "not_applicable")

    def test_a_primary_compartment_does_evaluate_c2(self) -> None:
        qc = self._qc_for(STR)
        self.assertTrue(qc["SZ09_CNT_stroma"].c2_evaluated)
        self.assertIn(
            qc["SZ09_CNT_stroma"].attribution, {"ok", "compartment_attribution_unsafe"}
        )

    def test_not_evaluated_never_becomes_an_unsafe_tag_on_a_member(self) -> None:
        """`member_verdict` must gate its attribution tag on `c2_evaluated`.

        `c2_pass` is False for `myofibroblast` because C2 was never run, so a
        member scored on that compartment must not pick up an
        `compartment_attribution_unsafe` tag from it.
        """
        genes = ["PRL", "EPCAM", "VIM", "COL1A1"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.tsv"
            rows = []
            for donor in C.DONORS:
                for arm in C.CONDITIONS:
                    rows += ControlsTest._unit(
                        f"{donor}TE_{arm}",
                        "Myofibroblast",
                        500,
                        {"PRL": 0.5, "VIM": 0.99},
                        genes,
                    )
            write_per_cell(path, rows, genes)
            cells = N.read_per_cell(path)
            order = sorted(cells.by_unit)
            stats = {u: N.unit_statistics(cells, u, i) for i, u in enumerate(order)}
            qc = {u: N.unit_qc(stats, u) for u in order}
        self.assertFalse(next(iter(qc.values())).c2_evaluated)
        record = N.member_verdict("S_PRL", "myofibroblast", stats, qc)
        self.assertNotIn("compartment_attribution_unsafe", record)

    def test_member_verdict_refuses_an_empty_statistics_map(self) -> None:
        with self.assertRaises(N.NodeSupportError):
            N.member_verdict("S_PRL", "stroma", {}, {})

    def test_myofibroblast_c1_is_not_applicable_not_a_failure(self) -> None:
        """C1 is defined only for the primary compartments.

        `myofibroblast` has no `C1_GENE` entry, so an earlier revision computed
        `bool("") and ...` and shipped `c1_pass: false` beside
        `c1_detection: not_applicable` -- a reported failure for a check that
        was never run. Same defect as the C2 one above, left in place on C1.
        """
        qc = self._qc_for("Myofibroblast")
        myo = qc["SZ09_CNT_myofibroblast"]
        self.assertFalse(myo.c1_evaluated)
        self.assertEqual(myo.c1_gene, "")
        self.assertFalse(myo.absence_informative)

    def test_no_integrity_control_is_distinct_from_failing_one(self) -> None:
        """ "Not run" and "failed" license different readings, so they differ."""
        qc = self._qc_for("Myofibroblast")
        myo = qc["SZ09_CNT_myofibroblast"]
        # n_min is checked first and myofibroblast units are small, so the
        # committed data never reaches the integrity branch; drive it directly.
        self.assertNotEqual(myo.uninformative_reason, "uninformative_integrity")

    def test_a_primary_compartment_does_evaluate_c1(self) -> None:
        qc = self._qc_for(STR)
        stroma = qc["SZ09_CNT_stroma"]
        self.assertTrue(stroma.c1_evaluated)
        self.assertEqual(stroma.c1_gene, C.C1_GENE["stroma"])

    def test_the_committed_qc_table_reports_no_unevaluated_failure(self) -> None:
        """B5: a pass/fail column must not report a failure for an unrun check."""
        path = ROOT / "docs/scrna/node_support_qc.tsv"
        if not path.is_file():
            self.skipTest("artifact not generated in this checkout")
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        for row in rows:
            for control in ("c1", "c2"):
                if row[f"{control}_detection" if control == "c1" else "c2_own"] == (
                    "not_applicable"
                ):
                    self.assertEqual(
                        row[f"{control}_pass"],
                        "not_applicable",
                        (row["unit_id"], control),
                    )

    def test_the_committed_findings_null_an_unevaluated_control(self) -> None:
        path = ROOT / "docs/scrna/node_support_findings.json"
        if not path.is_file():
            self.skipTest("artifact not generated in this checkout")
        units = json.loads(path.read_text())["units"]
        for unit_id, unit in units.items():
            for control in ("c1", "c2"):
                if not unit[f"{control}_evaluated"]:
                    self.assertIsNone(unit[f"{control}_pass"], (unit_id, control))

    def test_the_committed_qc_table_says_not_applicable(self) -> None:
        path = ROOT / "docs/scrna/node_support_qc.tsv"
        if not path.is_file():
            self.skipTest("artifact not generated in this checkout")
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        myo = [r for r in rows if r["compartment"] == "myofibroblast"]
        self.assertTrue(myo)
        for row in myo:
            self.assertEqual(row["c2_pass"], "not_applicable")
            self.assertEqual(row["attribution"], "not_applicable")


class StrictJsonTest(unittest.TestCase):
    """The artifact is read by tools that are not Python."""

    def test_finite_maps_nan_to_none(self) -> None:
        self.assertIsNone(N._finite(float("nan")))
        self.assertEqual(N._finite(0.25), 0.25)
        self.assertEqual(N._finite(0.0), 0.0)

    def test_the_committed_findings_carry_no_nan(self) -> None:
        path = ROOT / "docs/scrna/node_support_findings.json"
        if not path.is_file():
            self.skipTest("artifact not generated in this checkout")
        text = path.read_text()
        for token in ("NaN", "Infinity", "-Infinity"):
            self.assertNotIn(token, text)
        json.loads(text)  # strict by default


class DecisionProvenanceTest(unittest.TestCase):
    """A future unit may ingest the JSON and never read the prose."""

    def test_the_counterfactual_is_computed_not_asserted(self) -> None:
        """Under the rejected reading of the guard, single-gene members vote nothing."""
        members = {
            "E_PAEP": {"verdict": "concordant_with_alias"},  # single-gene
            "E_MUC1_SLEX": {"verdict": "divergent"},  # ten genes
            "E_SECRETORY_STATE": {"verdict": "inconsistent"},  # five genes
        }
        self.assertEqual(N.class_verdict(members), "alias_challenged")
        self.assertEqual(
            N._without_single_gene_members(members), "unclassified_by_section_5_4"
        )

    def test_a_class_with_no_single_gene_dependence_is_unchanged(self) -> None:
        members = {
            "E_GP130_STAT3": {"verdict": "divergent"},
            "E_CD98_CD9": {"verdict": "divergent"},
        }
        self.assertEqual(
            N._without_single_gene_members(members), N.class_verdict(members)
        )

    def test_the_committed_artifact_flags_ac01_and_only_ac01(self) -> None:
        path = ROOT / "docs/scrna/node_support_findings.json"
        if not path.is_file():
            self.skipTest("artifact not generated in this checkout")
        classes = json.loads(path.read_text())["alias_classes"]
        depends = {
            name: payload["decision_provenance"]["depends_on_deviations"]
            for name, payload in classes.items()
        }
        self.assertEqual(depends["AC01"], ["D1"])
        for name in ("AC02", "AC03", "AC04"):
            self.assertEqual(depends[name], [], name)
        ac01 = classes["AC01"]["decision_provenance"]
        self.assertEqual(ac01["registration_status"], "post_extraction_semantic_repair")
        self.assertEqual(
            ac01["counterfactual_verdict_without_D1"], "unclassified_by_section_5_4"
        )
        self.assertTrue(ac01["licenses_structural_change"])


class NetworkClaimTest(unittest.TestCase):
    """Only LITERAL rules and the COMPUTED inertness result are asserted.

    Two successive drafts of the finding document made claims about paths
    through v0.4's graph and both were false: the first said the route from
    `E_PAEP`/`E_HBEGF` to an `OUT_` node runs through `E_ITGAVB3_5`; the second
    said the SPP1 route does not carry `E_HBEGF`, while `E_ITGAVB3_5`'s own rule
    takes `E_HBEGF` as a direct input. A test named for a route property but
    checking only token membership in one rule string let the second through.

    So these assert exactly two kinds of fact -- that a quoted rule is the rule
    `network.bnd` carries, and that the map's `phenotype_inert` column says what
    the document says it says -- and nothing transitive.
    """

    BND = ROOT / "models/superset/adoc-literature-superset-v0.4.0/network.bnd"
    FINDING = ROOT / "docs/scrna/node_support_finding.md"

    #: Line numbers are what the document cites, so they are checked too.
    QUOTED_RULES: ClassVar[dict[int, tuple[str, str]]] = {
        126: ("E_ITGAVB3_5", "E_LIF or E_HBEGF or E_SECRETORY_STATE"),
        214: (
            "X_ADHESION_ROUTE_SPP1",
            (
                "E_RECEPTIVE_SURFACE and X_SPP1_LUMEN_FREE and E_ITGAVB3_5"
                " and X_INTERFACE_SPP1_RELAY"
            ),
        ),
        218: (
            "X_ADHESION_ROUTE_REDUNDANT",
            (
                "E_RECEPTIVE_SURFACE and (E_CD98_CD9 or E_CDH1_APICAL"
                " or E_ANXA2_ACTIN or E_HBEGF or E_DAG1_CLEAVED or E_MUC1_SLEX)"
                " and X_INTERFACE_REDUNDANT_RELAY"
            ),
        ),
        226: ("OUT_EPITHELIAL_RECEPTIVE", "E_RECEPTIVE_SURFACE and E_PAEP"),
    }

    def setUp(self) -> None:
        self.lines = self.BND.read_text().splitlines()

    def test_each_quoted_rule_is_the_rule_at_the_cited_line(self) -> None:
        for line_number, (node, logic) in self.QUOTED_RULES.items():
            rule = self.lines[line_number - 1].strip()
            self.assertEqual(rule, f"logic = {logic};", f"{node} at line {line_number}")
            declaration = self.lines[line_number - 2].strip()
            self.assertEqual(declaration, "Node " + node + " {")

    def test_every_quoted_rule_appears_in_the_finding_verbatim(self) -> None:
        finding = self.FINDING.read_text()
        for node, logic in self.QUOTED_RULES.values():
            self.assertIn(f"{node} = {logic}", finding.replace("\n", " "))

    def test_the_computed_inertness_is_what_the_document_reports(self) -> None:
        """Not read off the rules: the map's column, from a 524,288-state sweep."""
        rows = C.assessable_nodes()
        self.assertEqual(rows["E_PAEP"]["phenotype_inert"], "false")
        self.assertEqual(rows["E_HBEGF"]["phenotype_inert"], "true")
        self.assertEqual(rows["E_ITGAVB3_5"]["phenotype_inert"], "false")

    def test_the_finding_makes_no_transitive_route_claim(self) -> None:
        """The error class both earlier drafts fell into, blocked by shape."""
        finding = self.FINDING.read_text().replace("\n", " ")
        for phrase in (
            "runs through",
            "does **not** carry",
            "does not carry",
            "route to an `OUT_` node",
        ):
            self.assertNotIn(phrase, finding, f"transitive route claim: {phrase!r}")


class LeakageTest(unittest.TestCase):
    def test_the_derivation_reads_no_model_output(self) -> None:
        import ast

        path = SRC / "dt_adoc/scrna/node_support.py"
        source = path.read_text()
        # Strip the module docstring first: it NAMES the forbidden paths in
        # order to state the boundary, and a test that cannot tell a prohibition
        # from a violation would force the boundary to go undocumented.
        tree = ast.parse(source)
        docstring = ast.get_docstring(tree, clean=False) or ""
        body = source.replace(docstring, "", 1)
        self.assertIn("docs/concordance", docstring)
        self.assertNotIn("docs/concordance", body)
        for forbidden in (
            "dt_adoc.simulation",
            "dt_adoc.concordance",
            "dt_adoc.calibration",
            "dt_adoc.scoring",
            "dt_adoc.perturbations",
        ):
            self.assertNotIn(f"import {forbidden}", body)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertFalse(
            {i for i in imported if i.startswith("dt_adoc.")} - {"dt_adoc.scrna"},
            imported,
        )


if __name__ == "__main__":
    unittest.main()
