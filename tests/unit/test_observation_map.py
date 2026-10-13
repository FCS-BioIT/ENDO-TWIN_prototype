"""Contract tests for the observation-to-model mapping table and evaluator.

``config/observation_model_map.tsv`` replaced the inert ``directional_readouts``
stub in ``config/calibration.yaml``. These tests only exercise the loader and
the pure evaluator in ``dt_adoc.calibration.observation_map`` -- no MaBoSS run
is involved.
"""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.calibration.observation_map import (
    ACTIVATION_STATUSES,
    CALIBRATION_ROLES,
    MAPPING_COLUMNS,
    ObservationMapValidationError,
    active_constraints,
    active_diagnostics,
    evaluate_directional_constraints,
    load_observation_map,
)
from dt_adoc.model.catalog import default_paths, load_tsv


class LoadObservationMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_observation_map(ROOT)

    def test_loads_and_has_all_required_columns(self) -> None:
        for row in self.rows:
            self.assertEqual(set(row), set(MAPPING_COLUMNS))

    def test_controlled_vocabularies_enforced(self) -> None:
        for row in self.rows:
            self.assertIn(row["activation_status"], ACTIVATION_STATUSES)
            self.assertIn(row["calibration_role"], CALIBRATION_ROLES)

    def test_rejects_bad_activation_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            _write_mapping_copy(
                tmp_root,
                self.rows,
                mutate=lambda rows: rows[0].__setitem__(
                    "activation_status", "not_a_real_status"
                ),
            )
            with self.assertRaises(ObservationMapValidationError):
                load_observation_map(tmp_root)

    def test_rejects_a_row_with_a_numeric_weight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            _write_mapping_copy(
                tmp_root,
                self.rows,
                mutate=lambda rows: rows[0].__setitem__("weight", "0.5"),
            )
            with self.assertRaises(ObservationMapValidationError):
                load_observation_map(tmp_root)

    def test_rejects_a_rejected_row_missing_exclusion_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)

            def mutate(rows: list[dict[str, str]]) -> None:
                target = next(
                    row for row in rows if row["activation_status"] == "rejected"
                )
                target["exclusion_reason"] = ""

            _write_mapping_copy(tmp_root, self.rows, mutate=mutate)
            with self.assertRaises(ObservationMapValidationError):
                load_observation_map(tmp_root)

    def test_only_paep_is_active_constraint(self) -> None:
        constraint_rows = active_constraints(self.rows)
        self.assertEqual(len(constraint_rows), 1)
        self.assertEqual(constraint_rows[0]["model_nodes"], "E_PAEP")
        self.assertEqual(constraint_rows[0]["protein"], "PAEP")

    def test_only_igfbp1_is_active_diagnostic(self) -> None:
        diagnostic_rows = active_diagnostics(self.rows)
        self.assertEqual(len(diagnostic_rows), 1)
        self.assertEqual(diagnostic_rows[0]["model_nodes"], "S_IGFBP1")
        self.assertEqual(diagnostic_rows[0]["protein"], "IGFBP-1")

    def test_prl_is_provisional_and_never_active(self) -> None:
        prl_rows = [row for row in self.rows if row["protein"] == "PRL"]
        self.assertTrue(prl_rows)
        for row in prl_rows:
            self.assertNotEqual(row["activation_status"], "active_constraint")
            self.assertNotEqual(row["activation_status"], "active_diagnostic")

    def test_every_rejected_row_carries_an_exclusion_reason(self) -> None:
        rejected_rows = [
            row for row in self.rows if row["activation_status"] == "rejected"
        ]
        self.assertTrue(rejected_rows)
        for row in rejected_rows:
            self.assertTrue(row["exclusion_reason"].strip())

    def test_no_row_carries_a_numeric_weight(self) -> None:
        for row in self.rows:
            self.assertEqual(row["weight"], "")

    def test_paep_row_records_both_comparators_and_discrepancy(self) -> None:
        paep_rows = [row for row in self.rows if row["protein"] == "PAEP"]
        self.assertEqual(len(paep_rows), 1)
        row = paep_rows[0]
        self.assertEqual(row["registered_comparator"], "HT versus untreated")
        self.assertIn("E2 only", row["actual_comparator"])
        # The verbatim workbook label must survive as provenance, and the row
        # must simultaneously record that the actual condition is MPA-based.
        self.assertIn("E2+P4+XAV939", row["actual_comparator"])
        self.assertIn("verbatim workbook labels", row["actual_comparator"])
        self.assertIn("E2 + MPA + cAMP + XAV939", row["actual_comparator"])
        self.assertIn("no untreated", row["actual_comparator"].lower())
        self.assertIn("must not", row["claim_ceiling"].lower())

    def test_no_mapping_row_references_an_undefined_node(self) -> None:
        node_dictionary_path = default_paths(ROOT).extended_dir / "node_dictionary.tsv"
        known_nodes = {entry["node_id"] for entry in load_tsv(node_dictionary_path)}
        for row in self.rows:
            for node in row["model_nodes"].split(";"):
                if not node:
                    continue
                self.assertIn(
                    node,
                    known_nodes,
                    msg=f"{row['mapping_id']} references undefined node {node!r}",
                )


def _write_mapping_copy(
    tmp_root: Path,
    rows: list[dict[str, str]],
    *,
    mutate,
) -> None:
    """Write a mutated copy of the mapping table under a temp root.

    ``load_observation_map`` only ever reads
    ``<root>/config/observation_model_map.tsv``, so pointing it at a
    scratch root with a deliberately broken copy exercises the loader's
    validation without touching the real, canonical table.
    """
    mutable_rows = [dict(row) for row in rows]
    mutate(mutable_rows)
    config_dir = tmp_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    out_path = config_dir / "observation_model_map.tsv"
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(MAPPING_COLUMNS), delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(mutable_rows)


class EvaluateDirectionalConstraintsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_observation_map(ROOT)

    def test_satisfied_when_simulated_respects_directions(self) -> None:
        simulated = {
            "e2_primed_maternal": {"E_PAEP": 0.1},
            "hormone_treated_maternal": {"E_PAEP": 0.9, "S_IGFBP1": 0.5},
            "basal_maternal": {"S_IGFBP1": 0.0},
        }
        checks = evaluate_directional_constraints(simulated, self.rows)
        self.assertEqual(len(checks), 2)
        for check in checks:
            self.assertTrue(check.satisfied)
            self.assertFalse(check.excludes_candidate)

    def test_violated_when_simulated_inverts_directions(self) -> None:
        simulated = {
            "e2_primed_maternal": {"E_PAEP": 0.9},
            "hormone_treated_maternal": {"E_PAEP": 0.1, "S_IGFBP1": 0.0},
            "basal_maternal": {"S_IGFBP1": 0.5},
        }
        checks = evaluate_directional_constraints(simulated, self.rows)
        by_node = {check.model_node: check for check in checks}
        self.assertFalse(by_node["E_PAEP"].satisfied)
        self.assertFalse(by_node["S_IGFBP1"].satisfied)

    def test_paep_inversion_excludes_candidate_igfbp1_inversion_does_not(
        self,
    ) -> None:
        simulated = {
            "e2_primed_maternal": {"E_PAEP": 0.9},
            "hormone_treated_maternal": {"E_PAEP": 0.1, "S_IGFBP1": 0.0},
            "basal_maternal": {"S_IGFBP1": 0.5},
        }
        checks = evaluate_directional_constraints(simulated, self.rows)
        by_node = {check.model_node: check for check in checks}

        paep_check = by_node["E_PAEP"]
        self.assertEqual(paep_check.activation_status, "active_constraint")
        self.assertFalse(paep_check.satisfied)
        self.assertTrue(paep_check.excludes_candidate)

        igfbp1_check = by_node["S_IGFBP1"]
        self.assertEqual(igfbp1_check.activation_status, "active_diagnostic")
        self.assertFalse(igfbp1_check.satisfied)
        self.assertFalse(igfbp1_check.excludes_candidate)


if __name__ == "__main__":
    unittest.main()


class MappingGroundTruthTest(unittest.TestCase):
    """Guards that would catch a silent edit to the mapping's factual claims.

    The loader already enforces schema and vocabulary, so tests that merely
    re-assert those can never fail independently. These recompute the mapping's
    empirical claims from the canonical source table instead.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_observation_map(ROOT)
        cls.observations = load_tsv(
            ROOT / "input_tables" / "adoc_secreted_proteins.tsv"
        )

    def _row(self, mapping_id: str) -> dict[str, str]:
        return next(r for r in self.rows if r["mapping_id"] == mapping_id)

    def test_every_mapping_series_id_resolves_and_agrees_with_its_cells(
        self,
    ) -> None:
        """The guard that makes a series rename safe.

        `PRL_BOTTOM_1..3` used to denote workbook columns E,F,G and now denote
        B,C,D. Nothing previously resolved `source_series_id` against the table,
        so a rename could silently re-point a mapping at different cells while
        every other check still passed. This resolves both directions: the
        series must exist, and the row's `source_cells` must be exactly the cells
        those series occupy.
        """
        by_series: dict[str, set[str]] = {}
        outlet_of: dict[str, set[str]] = {}
        for row in self.observations:
            by_series.setdefault(row["series_id"], set()).add(row["source_cell"])
            outlet_of.setdefault(row["series_id"], set()).add(row["outlet"])
        for row in self.rows:
            if row["source_table"] != "input_tables/adoc_secreted_proteins.tsv":
                continue
            series = [s for s in row["source_series_id"].split(";") if s]
            if not series:
                continue
            unknown = [s for s in series if s not in by_series]
            self.assertEqual(
                unknown,
                [],
                f"{row['mapping_id']} names series absent from the source "
                f"table: {unknown}",
            )
            cell_list = [c for c in row["source_cells"].split(",") if c]
            recorded_cells = set(cell_list)
            if recorded_cells:
                # A mapping may select a SUBSET of its series' cells -- OM-002
                # deliberately compares day 0 against day 6 and omits day 3. What
                # must never happen is a cell that the named series do not
                # occupy: that is the signature of a stale series reference.
                occupied = set().union(*(by_series[s] for s in series))
                stray = sorted(recorded_cells - occupied)
                self.assertEqual(
                    stray,
                    [],
                    f"{row['mapping_id']}: source_cells {stray} are not occupied "
                    f"by its source_series_id -- the series reference is stale",
                )
                # Counted with duplicates: `source_cells` carries no sheet, so a
                # cross-sheet row such as OM-016 legitimately lists the same
                # address twice (G3 exists on both IGFBP-1 and PRL). That
                # ambiguity is why source_cells must always be read together
                # with source_series_id.
                self.assertEqual(
                    int(row["source_rows_n"]),
                    len(cell_list),
                    f"{row['mapping_id']}: source_rows_n does not match the "
                    "number of source_cells",
                )
            # The row's declared outlet must match what those series really are.
            outlets = set().union(*(outlet_of[s] for s in series))
            if row["outlet"] in {"top", "bottom"}:
                self.assertEqual(
                    outlets,
                    {row["outlet"]},
                    f"{row['mapping_id']} declares outlet {row['outlet']!r} but "
                    f"its series span {sorted(outlets)}",
                )

    def test_prl_detection_fractions_match_the_source_table(self) -> None:
        """Converts OM-014's detection series from transcribed prose into a
        recomputed claim. Under the corrected all-BOTTOM reading the
        denominators are 6, not 3.
        """
        limit = 10.0  # PRL detection limit, SOFIA-STR-001
        per_day: dict[str, list[float]] = {}
        for row in self.observations:
            if row["protein"] == "PRL":
                self.assertEqual(row["outlet"], "bottom")
                per_day.setdefault(row["resolved_protocol_day"], []).append(
                    float(row["reported_concentration_pg_ml"])
                )
        detected = {
            day: sum(1 for v in values if v >= limit) for day, values in per_day.items()
        }
        totals = {day: len(values) for day, values in per_day.items()}
        self.assertEqual(totals, {"0": 6, "3": 6, "6": 6})
        self.assertEqual(detected, {"0": 0, "3": 1, "6": 3})
        fraction = self._row("OM-014")["supporting_fraction"]
        for token in ("0/6", "1/6", "3/6"):
            self.assertIn(token, fraction)
        # The complete-separation claim is retracted: day 6 overlaps earlier days.
        day6_min = min(per_day["6"])
        earlier_max = max(per_day["0"] + per_day["3"])
        self.assertLess(day6_min, earlier_max)
        self.assertIn("RETRACTED", self._row("OM-014")["censoring_note"])

    def test_no_mapping_row_asserts_an_apical_prl_series(self) -> None:
        for row in self.rows:
            joined = " ".join(row.values())
            self.assertNotIn("PRL_TOP", joined, row["mapping_id"])
            if row["protein"] == "PRL":
                self.assertNotEqual(row["outlet"], "top", row["mapping_id"])

    def _bottom_igfbp1(self) -> dict[str, dict[str, float]]:
        series: dict[str, dict[str, float]] = {}
        for row in self.observations:
            if row["protein"] == "IGFBP-1" and row["outlet"] == "bottom":
                series.setdefault(row["series_id"], {})[
                    row["resolved_protocol_day"]
                ] = float(row["reported_concentration_pg_ml"])
        return series

    def test_paep_supporting_fraction_matches_the_source_table(self) -> None:
        by_series: dict[str, dict[str, float]] = {}
        for row in self.observations:
            if row["protein"] == "PAEP" and row["measurement_state"] == "observed":
                by_series.setdefault(row["series_id"], {})[row["condition"]] = float(
                    row["reported_concentration_pg_ml"]
                )
        # Indexed by the verbatim workbook condition label, which `condition`
        # preserves unchanged; the corrected identifier lives in
        # `condition_normalized`.
        cocktail = "HT (E2+P4+XAV939)"  # verbatim workbook label
        supporting = sum(
            1
            for values in by_series.values()
            if values[cocktail] > values["HT (E2 only)"]
        )
        # The ceiling is READ from the contract, never restated as a literal.
        # Both numbers were hardcoded as "<=4 donor groups" here while
        # test_secreted_proteins.py asserted the tightened value from the same
        # contract, so the suite pinned two contradictory ceilings and stayed
        # green. SOFIA-ANNO-007 tightened it when the annotation workbook
        # arrived; see REL-003 in config/adoc_chip_donor_provenance.tsv.
        contract = yaml.safe_load(
            (ROOT / "config" / "secreted_protein_contract.yaml").read_text(
                encoding="utf-8"
            )
        )["biological_independence_contract"]
        units = contract["max_independent_units_paep_observed"]
        groups = contract["max_independent_epithelial_source_groups_paep"]
        self.assertEqual(
            self._row("OM-001")["supporting_fraction"],
            f"{supporting}/{len(by_series)} chips "
            f"(<={units} independent units; <={groups} epithelial source groups)",
        )

    def test_igfbp1_diagnostic_fraction_matches_the_source_table(self) -> None:
        series = self._bottom_igfbp1()
        supporting = sum(1 for v in series.values() if v["6"] > v["0"])
        self.assertEqual(
            self._row("OM-002")["supporting_fraction"],
            f"{supporting}/{len(series)}",
        )

    def test_rejected_monotone_fraction_matches_the_source_table(self) -> None:
        series = self._bottom_igfbp1()
        supporting = sum(1 for v in series.values() if v["0"] < v["3"] < v["6"])
        self.assertTrue(
            self._row("OM-003")["supporting_fraction"].startswith(
                f"{supporting}/{len(series)}"
            )
        )

    def test_every_mapping_protocol_resolves_for_both_models(self) -> None:
        """A renamed protocol must fail here, not at first real evaluation."""
        from dt_adoc.protocols.conditions import get_protocol

        for model_version in (
            "adoc-literature-v0.2.0",
            "adoc-literature-superset-v0.3.0",
        ):
            for row in self.rows:
                for protocol_id in filter(None, row["protocol_ids"].split(";")):
                    protocol = get_protocol(
                        protocol_id, ROOT, model_version=model_version
                    )
                    self.assertEqual(protocol.protocol_id, protocol_id)

    def test_every_mapping_node_exists_in_both_models(self) -> None:
        """A node valid in only one model is a latent bug, not a passing test."""
        for model_dictionary in (
            ROOT / "models/extended/adoc-literature-v0.2.0/node_dictionary.tsv",
            ROOT
            / "models/superset/adoc-literature-superset-v0.3.0/node_dictionary.tsv",
        ):
            known = {row["node_id"] for row in load_tsv(model_dictionary)}
            for row in self.rows:
                for node in filter(None, row["model_nodes"].split(";")):
                    self.assertIn(
                        node, known, f"{node} missing from {model_dictionary}"
                    )

    def test_loader_rejects_a_corrupted_activation_status(self) -> None:
        """The schema guards are real: prove they raise rather than pass through."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            rows = [dict(r) for r in self.rows]
            rows[0]["activation_status"] = "definitely_not_a_status"
            with (root / "config/observation_model_map.tsv").open(
                "w", newline="", encoding="utf-8"
            ) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=list(MAPPING_COLUMNS), delimiter="\t"
                )
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(ObservationMapValidationError):
                load_observation_map(root)
