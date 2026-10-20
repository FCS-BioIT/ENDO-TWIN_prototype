"""Machine-checkable guards on the ADOC reproducibility matrix.

`docs/results_reproducibility_matrix.tsv` compares published ADOC results against
`adoc-literature-superset-v0.3.0`. A prose table cannot be asserted against a
claim boundary; a fielded one can, which is the whole reason the matrix is a TSV.

The guards fall into three groups:

* **claim boundary** -- the matrix may never claim quantitative reproduction,
  calibrated time, validation, or causality. `AGENTS.md` and
  `config/calibration.yaml` (`calibrated_physical_time: false`) make those
  claims unavailable, and `test_quantitatively_reproduced_count_is_zero` turns
  that into a number under test rather than a promise in prose.
* **horizon discipline** -- every simulated value carries its horizon class and
  stochastic settings, and a declared value can never be merged with a converged
  one. The declared horizon reads endpoints ~4000x early
  (`docs/endpoint_convergence_finding.md`), so an unlabelled probability is
  actively misleading here.
* **leakage control** -- rows compared against construction- or
  calibration-role evidence are labelled circular, and the single held-out
  observation stays held out. The circular set is DERIVED from
  `config/evidence_roles.yaml`, so curating that file updates the guard.
"""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MATRIX = ROOT / "docs" / "results_reproducibility_matrix.tsv"
NARRATIVE = ROOT / "docs" / "results_reproducibility_matrix.md"

#: The only verdicts the matrix may express. There is deliberately no
#: "quantitatively_reproduced" member -- see the module docstring.
VERDICTS = frozenset(
    {
        "qualitatively_reproduced_direction_only",
        "partial_direction_only",
        "disagreement",
        "not_assessable",
        "circular_by_construction",
        "analytically_reproduced_model_internal",
    }
)

#: Closed vocabulary for the binding limitation. Every result must name at least
#: one, so "not assessable" can never stand unexplained.
LIMITATIONS = frozenset(
    {
        "topology",
        "timing",
        "calibration",
        "assay_design",
        "missing_provenance",
        "continuous_spatial",
    }
)

HORIZON_CLASSES = frozenset({"declared", "converged"})

#: Phrases that would overstate what a MaBoSS trajectory frequency supports.
FORBIDDEN_PHRASES = (
    "quantitativ",
    "calibrated time",
    "calibrated physical time",
    "reproduces the observed value",
    "clinically",
    "proves",
    "validated the model",
    "predicts that the patient",
)

#: Fields that must accompany any simulated number (AGENTS.md reporting rules).
STOCHASTIC_FIELDS = (
    "horizon_class",
    "max_time",
    "time_tick",
    "trajectory_count",
    "seeds",
    "mc_sd_across_seeds",
)


def _rows() -> list[dict[str, str]]:
    with MATRIX.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _base_result_id(result_id: str) -> str:
    """`R12a` and `R12b` are two horizons of one published result."""
    return result_id[:-1] if result_id[-1].isalpha() else result_id


class MatrixSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = _rows()

    def test_the_matrix_has_rows(self) -> None:
        self.assertGreater(len(self.rows), 40)

    def test_result_ids_are_unique(self) -> None:
        ids = [row["result_id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_row_carries_a_known_verdict(self) -> None:
        for row in self.rows:
            self.assertIn(row["verdict"], VERDICTS, row["result_id"])

    def test_every_row_names_a_binding_limitation(self) -> None:
        """A "not assessable" cell must say WHY, from a closed vocabulary."""
        for row in self.rows:
            tokens = [t for t in row["binding_limitation"].split(";") if t]
            self.assertNotEqual(tokens, [], row["result_id"])
            for token in tokens:
                self.assertIn(token, LIMITATIONS, f"{row['result_id']}: {token}")

    def test_every_row_carries_a_figure_anchor_and_an_observation(self) -> None:
        for row in self.rows:
            self.assertNotEqual(row["figure_anchor"].strip(), "", row["result_id"])
            self.assertNotEqual(row["observed_result"].strip(), "", row["result_id"])

    def test_outlet_status_is_explicit(self) -> None:
        """PAEP's outlet is uncertain and must stay visibly so."""
        allowed = {"confirmed", "uncertain", "not_applicable"}
        for row in self.rows:
            self.assertIn(row["outlet_status"], allowed, row["result_id"])
        paep = [
            r for r in self.rows if r["readout_id"] == "P1-PAEP" and r["mapping_id"]
        ]
        self.assertTrue(paep)
        for row in paep:
            self.assertEqual(row["outlet_status"], "uncertain", row["result_id"])


class ClaimBoundaryTest(unittest.TestCase):
    """The guards that stop the matrix overstating what the twin supports."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = _rows()

    def test_no_row_claims_quantitative_reproduction(self) -> None:
        offenders: list[str] = []
        for row in self.rows:
            haystack = " ".join(row.values()).lower()
            for phrase in FORBIDDEN_PHRASES:
                if phrase in haystack:
                    # A row may say the claim is FORBIDDEN or IMPOSSIBLE.
                    negated = any(
                        marker in haystack
                        for marker in ("not ", "never", "no ", "cannot", "forbid")
                    )
                    if not negated:
                        offenders.append(f"{row['result_id']}: {phrase}")
        self.assertEqual(offenders, [], offenders)

    def test_quantitatively_reproduced_count_is_zero(self) -> None:
        """A number under test, not a promise in prose.

        Five independent blockers make quantitative reproduction unavailable:
        no calibrated time (`config/calibration.yaml`), **no** magnitude-fitted
        term at all since the 2026-09-16 demotion of `adhesion_objective`,
        binary saturation at the decided horizon, the only graded magnitude
        being two hand-set relay probabilities, and that magnitude disagreeing
        with the observation where it exists.
        """
        self.assertNotIn("quantitatively_reproduced", VERDICTS)
        quantitative = [
            row for row in self.rows if "quantitativ" in row["verdict"].lower()
        ]
        self.assertEqual(quantitative, [])
        self.assertIn(
            "Quantitatively reproduced** | **0**", NARRATIVE.read_text(encoding="utf-8")
        )

    def test_no_row_asserts_validation(self) -> None:
        text = NARRATIVE.read_text(encoding="utf-8")
        self.assertIn("No row in this matrix constitutes validation.", text)


class HorizonDisciplineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = _rows()
        cls.simulated = [row for row in cls.rows if row["simulated_value"].strip()]

    def test_there_are_simulated_rows_to_check(self) -> None:
        self.assertGreater(len(self.simulated), 5)

    def test_every_simulated_value_carries_its_horizon_and_settings(self) -> None:
        """An unlabelled probability is actively misleading in this repository:
        the declared horizon reads endpoints ~4000x before their fixed point.
        """
        for row in self.simulated:
            for field in STOCHASTIC_FIELDS:
                self.assertNotEqual(
                    row[field].strip(), "", f"{row['result_id']} missing {field}"
                )
            self.assertIn(row["horizon_class"], HORIZON_CLASSES, row["result_id"])

    def test_no_row_merges_the_two_horizons(self) -> None:
        for row in self.rows:
            self.assertNotIn("/", row["horizon_class"])
            self.assertNotIn(";", row["horizon_class"])

    def test_a_result_reported_at_both_horizons_uses_two_rows(self) -> None:
        by_result: dict[str, set[str]] = {}
        for row in self.simulated:
            by_result.setdefault(_base_result_id(row["result_id"]), set()).add(
                row["horizon_class"]
            )
        both = {k for k, v in by_result.items() if v == HORIZON_CLASSES}
        self.assertTrue(both, "expected at least one result reported at both horizons")
        for result in both:
            rows = [
                row
                for row in self.simulated
                if _base_result_id(row["result_id"]) == result
            ]
            self.assertGreaterEqual(len(rows), 2, result)

    def test_the_narrative_states_the_horizon_gap(self) -> None:
        text = NARRATIVE.read_text(encoding="utf-8")
        self.assertIn("4000", text)
        self.assertIn("dimensionless", text)
        self.assertIn("superseded", text)


class LeakageControlTest(unittest.TestCase):
    """Circularity is derived from evidence_roles.yaml, not hard-coded."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = _rows()
        roles = yaml.safe_load(
            (ROOT / "config" / "evidence_roles.yaml").read_text(encoding="utf-8")
        )
        cls.fitted_or_construction = set(roles["construction"]["evidence_ids"]) | set(
            roles["calibration"]["evidence_ids"]
        )
        cls.held_out = set(roles["validation"]["evidence_ids"])

    def test_the_held_out_arm_is_still_held_out(self) -> None:
        """SOFIA-ADH-003 is the repository's only held-out observation and the
        hold-out is enforced in code. Citing it from an observation mapping
        would spend it, so no mapping row may reference it.
        """
        self.assertIn("SOFIA-ADH-003", self.held_out)
        from dt_adoc.calibration.observation_map import load_observation_map

        for row in load_observation_map(ROOT):
            self.assertNotIn(
                "SOFIA-ADH-003",
                row["evidence_ids"],
                f"{row['mapping_id']} would spend the only held-out arm",
            )

    def test_rows_citing_fitted_evidence_declare_their_circularity(self) -> None:
        offenders: list[str] = []
        for row in self.rows:
            cited = {e for e in row["evidence_id"].split(";") if e}
            if not cited & self.fitted_or_construction:
                continue
            if not row["simulated_value"].strip():
                continue  # nothing was compared, so nothing is circular
            if row["verdict"] != "circular_by_construction" and not row["circularity"]:
                offenders.append(row["result_id"])
        self.assertEqual(offenders, [], offenders)

    def test_the_held_out_row_is_labelled_as_such(self) -> None:
        held = [r for r in self.rows if "SOFIA-ADH-003" in r["evidence_id"]]
        self.assertTrue(held)
        for row in held:
            self.assertIn("HELD OUT", row["circularity"], row["result_id"])


class MatrixResolvesAgainstTheModelTest(unittest.TestCase):
    """A renamed node or protocol must fail here, not at interpretation time."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = _rows()

    def test_every_named_node_exists_in_the_superset(self) -> None:
        from dt_adoc.model.catalog import load_tsv

        nodes = {
            entry["node_id"]
            for entry in load_tsv(
                ROOT
                / "models"
                / "superset"
                / "adoc-literature-superset-v0.3.0"
                / "node_dictionary.tsv"
            )
        }
        for row in self.rows:
            field = row["dt_node_or_proxy"]
            if not field or field == "none":
                continue
            for token in field.replace(";", " ").split():
                candidate = token.strip("()")
                if candidate.startswith(("E_", "S_", "X_", "OUT_", "IN_")):
                    self.assertIn(candidate, nodes, f"{row['result_id']}: {candidate}")

    def test_every_named_readout_exists(self) -> None:
        from dt_adoc.model.catalog import load_tsv

        readouts = {
            entry["readout_id"]
            for entry in load_tsv(ROOT / "context" / "phase1-readouts.tsv")
        }
        for row in self.rows:
            for token in (t for t in row["readout_id"].split(";") if t):
                self.assertIn(token, readouts, f"{row['result_id']}: {token}")

    def test_every_named_mapping_exists(self) -> None:
        from dt_adoc.calibration.observation_map import load_observation_map

        known = {row["mapping_id"] for row in load_observation_map(ROOT)}
        for row in self.rows:
            for token in (t for t in row["mapping_id"].split(";") if t):
                self.assertIn(token, known, f"{row['result_id']}: {token}")

    def test_every_named_evidence_id_exists(self) -> None:
        from dt_adoc.model.catalog import load_tsv

        known = {
            entry["evidence_id"]
            for entry in load_tsv(ROOT / "context" / "evidence-register.tsv")
        }
        for row in self.rows:
            for token in (t for t in row["evidence_id"].split(";") if t):
                self.assertIn(token, known, f"{row['result_id']}: {token}")


class SummaryCountsTest(unittest.TestCase):
    """The narrative's headline counts are recomputed from the TSV."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = _rows()
        cls.text = NARRATIVE.read_text(encoding="utf-8")

    def test_distinct_result_count_matches_the_narrative(self) -> None:
        distinct = {_base_result_id(row["result_id"]) for row in self.rows}
        self.assertIn(f"**{len(distinct)}**", self.text)

    def test_matrix_row_count_matches_the_narrative(self) -> None:
        self.assertIn(f"**{len(self.rows)} rows", self.text)

    def test_the_reproduced_counts_match_the_rows(self) -> None:
        qual = sum(
            1
            for r in self.rows
            if r["verdict"] == "qualitatively_reproduced_direction_only"
        )
        partial = sum(1 for r in self.rows if r["verdict"] == "partial_direction_only")
        self.assertEqual(qual, 3)
        self.assertEqual(partial, 1)
        self.assertIn(f"**{qual}** | R41b, R42, R44", self.text)

    def test_newly_assessable_is_zero_and_said_so(self) -> None:
        """The corrected metadata changed comparisons and enabled none. Saying
        otherwise would present provenance work as new reproduction.
        """
        self.assertIn(
            "Newly assessable because of the new metadata** | **0**", self.text
        )
        changed = sum(1 for r in self.rows if r["metadata_effect"] == "changed")
        self.assertEqual(changed, 5)


if __name__ == "__main__":
    unittest.main()
