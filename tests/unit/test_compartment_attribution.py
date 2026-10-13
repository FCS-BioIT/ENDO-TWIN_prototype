"""C2 -- the compartment attribution overlay reinterprets; it never recomputes.

``context/observation_compartment_attribution.tsv`` states which tissue
compartment each ADOC outlet measurement can be attributed to (SRC-006, C2).
Three things must stay true:

1. the frozen ``config/observation_model_map.tsv`` is unchanged, so OM-002 is
   still an ``active_diagnostic`` on ``S_IGFBP1`` with the same calculation;
2. nothing but the C2 builder reads the overlay, so no closed unit (Phase 1B,
   2A, 2B, U8) sees it, and none of its inputs or outputs moves;
3. every artifact that consumes the overlay records its sha256.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.calibration.observation_map import (
    evaluate_directional_constraints,
    load_observation_map,
)
from dt_adoc.concordance.simulate import implementation_files
from dt_adoc.observations import compartment_attribution as C
from dt_adoc.personalization.phase2b.audit import FROZEN_PREFIXES

#: The digest Phase 1B froze for the observation map
#: (tests/unit/test_phase1b_closure.py) and U8 recorded (u8_rerank_report.md).
FROZEN_MAP_SHA256 = "74f0d5d0896beba57a0a03960239ad2fc039f315fa42a2209a65e228bfa3aff5"


def _rows() -> list[dict[str, str]]:
    with (ROOT / C.ATTRIBUTION_PATH).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _problems(rows: list[dict[str, str]]) -> list[str]:
    return C.validate(rows, load_observation_map(ROOT), C._known_evidence_ids(ROOT))


def _by_id() -> dict[str, C.Attribution]:
    return {a.attribution_id: a for a in C.load_attributions(ROOT)}


class TheTable(unittest.TestCase):
    def test_it_loads_and_validates(self) -> None:
        self.assertEqual(len(C.load_attributions(ROOT)), 5)

    def test_it_states_the_minimum_c2_attributions(self) -> None:
        a = _by_id()
        self.assertEqual(
            (a["CA-001"].analyte, a["CA-001"].compartment_attribution),
            ("PRL", "stromal_attributed"),
        )
        self.assertIn("OM-002", a["CA-002"].mapping_ids)
        self.assertEqual(
            a["CA-002"].compartment_attribution, "epithelial_and_stromal_ambiguous"
        )
        self.assertEqual(set(a["CA-003"].mapping_ids), {"OM-008", "OM-012", "OM-013"})
        self.assertEqual(
            a["CA-003"].compartment_attribution, "epithelial_and_stromal_ambiguous"
        )
        self.assertEqual(a["CA-003"].supersedes_in_rendering, "for a stromal readout")
        self.assertEqual(
            (a["CA-004"].mapping_ids, a["CA-004"].compartment_attribution),
            (("OM-001",), "secretory_epithelial_compartment_uncertain"),
        )
        self.assertEqual(
            (
                a["CA-005"].analyte,
                a["CA-005"].mapping_ids,
                a["CA-005"].compartment_attribution,
            ),
            ("SPP1", (), "mixed_source_free_ligand_pool"),
        )

    def test_only_measured_single_analyte_rows_are_attributed(self) -> None:
        summary = C.compute_summary(ROOT)
        self.assertEqual(
            summary["unattributed_map_rows"], ["OM-009", "OM-010", "OM-011", "OM-017"]
        )
        self.assertEqual(summary["unattributed_measured_rows"], [])
        self.assertEqual(summary["attributed_map_rows"], 13)
        for row in load_observation_map(ROOT):
            if row["mapping_id"] in summary["unattributed_map_rows"]:
                self.assertEqual(C.map_analytes(row), ())

    def test_every_single_analyte_map_row_of_an_attributed_analyte_is_covered_once(
        self,
    ) -> None:
        covered = [
            (m, a.analyte) for a in C.load_attributions(ROOT) for m in a.mapping_ids
        ]
        self.assertEqual(len(covered), len(set(covered)))
        for row in load_observation_map(ROOT):
            for analyte in C.map_analytes(row):
                self.assertIn((row["mapping_id"], analyte), covered)


class ValidationRefuses(unittest.TestCase):
    def _mutated(self, attribution_id: str, **changes: str) -> list[str]:
        rows = copy.deepcopy(_rows())
        for row in rows:
            if row["attribution_id"] == attribution_id:
                row.update(changes)
        return _problems(rows)

    def test_the_committed_table_has_no_problems(self) -> None:
        self.assertEqual(_problems(_rows()), [])

    def test_an_unknown_attribution(self) -> None:
        self.assertTrue(self._mutated("CA-002", compartment_attribution="stromal"))

    def test_a_map_row_left_uncovered(self) -> None:
        self.assertTrue(
            self._mutated("CA-002", mapping_ids="OM-003;OM-004;OM-005;OM-011;OM-016")
        )

    def test_a_map_row_covered_twice(self) -> None:
        self.assertTrue(
            self._mutated("CA-003", mapping_ids="OM-002;OM-008;OM-012;OM-013")
        )

    def test_a_row_naming_a_map_row_of_another_analyte(self) -> None:
        self.assertTrue(self._mutated("CA-004", mapping_ids="OM-001;OM-002"))

    def test_an_evidence_id_that_does_not_resolve(self) -> None:
        self.assertTrue(self._mutated("CA-001", evidence_ids="REF-999"))

    def test_an_analyte_level_row_for_an_analyte_with_map_rows(self) -> None:
        self.assertTrue(
            self._mutated("CA-004", mapping_ids="", outlet=C.OUTLET_NOT_REGISTERED)
        )

    def test_a_map_row_whose_outlet_is_not_declared(self) -> None:
        self.assertTrue(self._mutated("CA-004", outlet="bottom"))

    def test_an_analyte_level_row_without_the_not_registered_outlet(self) -> None:
        self.assertTrue(self._mutated("CA-005", outlet="top"))

    def test_a_record_with_no_measured_rows(self) -> None:
        # OM-011 is a protocol-coverage gap with source_rows_n = 0: no outlet
        # measurement exists for an attribution to qualify.
        self.assertTrue(
            self._mutated(
                "CA-002", mapping_ids="OM-002;OM-003;OM-004;OM-005;OM-011;OM-016"
            )
        )

    def test_a_superseded_phrase_absent_from_the_named_rows(self) -> None:
        self.assertTrue(
            self._mutated("CA-003", supersedes_in_rendering="for an epithelial readout")
        )


class Om002IsUnchanged(unittest.TestCase):
    def test_the_observation_map_is_the_frozen_bytes(self) -> None:
        digest = hashlib.sha256(
            (ROOT / C.OBSERVATION_MAP_PATH).read_bytes()
        ).hexdigest()
        self.assertEqual(digest, FROZEN_MAP_SHA256)

    def test_the_module_records_the_same_frozen_digest(self) -> None:
        self.assertEqual(C.PHASE1B_FROZEN_MAP_SHA256, FROZEN_MAP_SHA256)

    def test_om002_is_still_the_same_active_diagnostic(self) -> None:
        om002 = next(
            r for r in load_observation_map(ROOT) if r["mapping_id"] == "OM-002"
        )
        self.assertEqual(om002["activation_status"], "active_diagnostic")
        self.assertEqual(om002["model_nodes"], "S_IGFBP1")
        self.assertEqual(
            om002["objective_treatment"], "non_inversion_diagnostic_secondary_ranking"
        )

    def test_the_evaluation_is_identical_after_the_overlay_is_loaded(self) -> None:
        rows = [r for r in load_observation_map(ROOT) if r["mapping_id"] == "OM-002"]
        low, high = rows[0]["protocol_ids"].split(";")
        for values in ((0.0, 1.0), (1.0, 0.0), (0.5, 0.5)):
            simulated = {low: {"S_IGFBP1": values[0]}, high: {"S_IGFBP1": values[1]}}
            before = evaluate_directional_constraints(simulated, rows)
            C.load_attributions(ROOT)
            C.interpretation_rows(ROOT)
            reloaded = [
                r for r in load_observation_map(ROOT) if r["mapping_id"] == "OM-002"
            ]
            after = evaluate_directional_constraints(simulated, reloaded)
            self.assertEqual(before, after)
            self.assertFalse(before[0].excludes_candidate)


class ActiveInterpretationPath(unittest.TestCase):
    """OM-002 carries CA-002 in current outputs; its numbers never change."""

    def _om002_check(self, high: float, low: float):
        rows = [r for r in load_observation_map(ROOT) if r["mapping_id"] == "OM-002"]
        lo, hi = rows[0]["protocol_ids"].split(";")
        (check,) = evaluate_directional_constraints(
            {lo: {"S_IGFBP1": low}, hi: {"S_IGFBP1": high}}, rows
        )
        return check

    def test_annotation_passes_every_numerical_field_through_unchanged(self) -> None:
        import dataclasses

        for high, low in ((1.0, 0.0), (0.0, 1.0), (0.5, 0.5)):
            check = self._om002_check(high, low)
            annotated = C.annotate_check(check, ROOT)
            for field in dataclasses.fields(check):
                self.assertEqual(annotated[field.name], getattr(check, field.name))
            self.assertEqual(annotated["excludes_candidate"], check.excludes_candidate)
            self.assertFalse(
                annotated["excludes_candidate"]
            )  # a diagnostic never excludes

    def test_a_current_om002_rendering_carries_ca002(self) -> None:
        annotated = C.annotate_check(self._om002_check(1.0, 0.0), ROOT)
        self.assertEqual(annotated["attribution_id"], "CA-002")
        self.assertEqual(
            annotated["compartment_attribution"], "epithelial_and_stromal_ambiguous"
        )
        self.assertIn("computational proxy", annotated["model_interpretation"])
        self.assertIn("stromal-specific", annotated["prohibited_interpretation"])
        text = C.describe_check(annotated)
        self.assertIn("CA-002", text)
        self.assertIn("epithelial_and_stromal_ambiguous", text)
        self.assertIn("computational proxy S_IGFBP1", text)
        self.assertIn("never excludes a candidate", text)

    def test_a_stromal_specific_statement_is_refused(self) -> None:
        annotated = C.annotate_check(self._om002_check(1.0, 0.0), ROOT)
        for claim in (
            "OM-002 is stromal-specific evidence for S_IGFBP1",
            "basal IGFBP-1 is specific to the stromal state",
            "IGFBP-1 here is an exclusively stromal readout",
            "a stroma-specific readout",
        ):
            with self.subTest(claim=claim), self.assertRaises(C.InterpretationRefused):
                C.check_statement(annotated, claim)
        self.assertTrue(C.check_statement(annotated, "S_IGFBP1 did not invert"))

    def test_a_stromal_attributed_measurement_may_be_called_stromal(self) -> None:
        prl = {
            "mapping_id": "OM-006",
            "attribution_id": "CA-001",
            "compartment_attribution": "stromal_attributed",
        }
        self.assertTrue(C.check_statement(prl, "a stromal-specific readout"))

    def test_the_cli_output_is_annotated_and_hashes_the_overlay(self) -> None:
        import io
        import json
        from contextlib import redirect_stdout

        from dt_adoc import cli
        from dt_adoc.calibration import observation_map

        rows = load_observation_map(ROOT)
        protocols = {
            p
            for r in rows
            if r["activation_status"] in ("active_constraint", "active_diagnostic")
            for p in r["protocol_ids"].split(";")
        }
        simulated = {p: {"E_PAEP": 0.5, "S_IGFBP1": 0.5} for p in protocols}
        for mode in (["--json"], []):
            buffer = io.StringIO()
            with (
                mock.patch.object(
                    observation_map,
                    "simulate_constraint_protocols",
                    return_value=simulated,
                ),
                redirect_stdout(buffer),
            ):
                self.assertEqual(cli.main(["evaluate-constraints", *mode]), 0)
            out = buffer.getvalue()
            if mode:
                payload = json.loads(out)
                om002 = next(
                    c for c in payload["checks"] if c["mapping_id"] == "OM-002"
                )
                self.assertEqual(om002["attribution_id"], "CA-002")
                self.assertFalse(om002["excludes_candidate"])
                self.assertEqual(
                    payload["observation_compartment_attribution"]["sha256"],
                    hashlib.sha256(
                        (ROOT / C.ATTRIBUTION_PATH).read_bytes()
                    ).hexdigest(),
                )
            else:
                line = next(x for x in out.splitlines() if "OM-002" in x)
                self.assertIn("CA-002", line)
                self.assertNotRegex(line, r"(?i)strom\w*[- ]specific")


class ClosedUnitsNeverSeeIt(unittest.TestCase):
    NEEDLES = (
        "observation_compartment_attribution",
        "observations.compartment_attribution",
        "observations import compartment_attribution",
    )

    #: The only approved current consumer of the overlay (owner decision
    #: 2026-09-29): the live evaluate-constraints command.
    APPROVED_READERS = ("src/dt_adoc/cli.py",)

    def test_only_the_approved_current_consumer_reads_the_overlay(self) -> None:
        own = (SRC / "dt_adoc/observations/compartment_attribution.py").resolve()
        readers = [
            path.relative_to(ROOT).as_posix()
            for path in sorted(SRC.rglob("*.py"))
            if path.resolve() != own
            and any(n in path.read_text(encoding="utf-8") for n in self.NEEDLES)
        ]
        self.assertEqual(readers, list(self.APPROVED_READERS))

    def test_no_closed_unit_or_the_evaluator_reads_the_overlay(self) -> None:
        closed = [
            "src/dt_adoc/calibration/observation_map.py",
            "src/dt_adoc/experiments/phase1b_closure.py",
            "src/dt_adoc/experiments/u8_stage3_rerank.py",
            "src/dt_adoc/experiments/stage3_design.py",
            "src/dt_adoc/personalization/phase2a_contract.py",
            *sorted(
                p.relative_to(ROOT).as_posix()
                for p in (SRC / "dt_adoc/personalization/phase2b").glob("*.py")
            ),
            *sorted(
                p.relative_to(ROOT).as_posix()
                for p in (SRC / "dt_adoc/concordance").glob("*.py")
            ),
        ]
        for path in closed:
            text = (ROOT / path).read_text(encoding="utf-8")
            self.assertFalse(any(n in text for n in self.NEEDLES), path)

    def test_the_overlay_and_its_outputs_are_outside_every_closed_phase_guard(
        self,
    ) -> None:
        for path in (C.ATTRIBUTION_PATH, *C.OUTPUTS):
            self.assertFalse(path.as_posix().startswith(FROZEN_PREFIXES), path)

    def test_the_module_is_outside_the_implementation_digest(self) -> None:
        globbed = set(implementation_files(ROOT))
        # The digest's own file list, so the guard can fail: it must see the
        # observation-map loader, which is under calibration/.
        self.assertIn("src/dt_adoc/calibration/observation_map.py", globbed)
        self.assertNotIn("src/dt_adoc/observations/compartment_attribution.py", globbed)


class Outputs(unittest.TestCase):
    def test_regenerating_reproduces_the_committed_files_byte_for_byte(self) -> None:
        for relative, text in C.render_outputs(ROOT).items():
            self.assertEqual(
                (ROOT / relative).read_text(encoding="utf-8"), text, relative
            )

    def test_the_summary_hashes_the_overlay_and_the_map(self) -> None:
        summary = json.loads((ROOT / C.SUMMARY).read_text(encoding="utf-8"))
        hashes = summary["inputs_sha256"]
        self.assertIs(summary["observation_map_is_phase1b_frozen_bytes"], True)
        for path in (C.ATTRIBUTION_PATH, C.OBSERVATION_MAP_PATH):
            self.assertEqual(
                hashes[path.as_posix()],
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            )

    def test_the_superseded_phrase_is_never_rendered_unmarked(self) -> None:
        report = (ROOT / C.REPORT).read_text(encoding="utf-8")
        table = report[report.index("## Map rows as interpreted") :]
        om008 = next(
            line for line in table.splitlines() if line.startswith("| OM-008 ")
        )
        self.assertIn('[superseded by CA-003: "for a stromal readout"', om008)
        self.assertEqual(om008.count("for a stromal readout"), 1)


if __name__ == "__main__":
    unittest.main()
