"""The KLF12 state derivation must stay honest about what it did and did not do.

The scientific risk in this increment is not an arithmetic slip. It is that a
number derived as *the fraction of epithelial cells in which one transcript was
seen* is later read, cited or reused as *the probability that the epithelium is
in the KLF12-high state*. Nothing in a TSV of six rows prevents that on its own,
so the invariants are enforced here:

* the derivation cannot see a model output, so a threshold cannot be chosen by
  what it does to the adhesion endpoint;
* the artifact records the state model that produced each number, including the
  two quantile thresholds that collapse onto the bare detection rule;
* every committed number is re-derivable from the extracted per-cell table with
  no R and no 2.9 GB object, which is what makes it checkable at all;
* availability is still not integration -- the object being on a disk activates
  nothing.
"""

from __future__ import annotations

import csv
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.scrna import klf12_state

EVIDENCE = ROOT / "docs" / "scrna" / "klf12_state_evidence.tsv"
FINDINGS = ROOT / "docs" / "scrna" / "klf12_state_findings.json"
PREREGISTRATION = ROOT / "docs" / "scrna" / "klf12_prior_preregistration.md"


def _evidence() -> list[dict[str, str]]:
    with EVIDENCE.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _findings() -> dict:
    return json.loads(FINDINGS.read_text(encoding="utf-8"))


class TheDerivationCannotSeeAnOutcome(unittest.TestCase):
    """Leakage control 1, enforced on the source rather than promised in prose."""

    FORBIDDEN = (
        "dt_adoc.simulation",
        "dt_adoc.concordance",
        "dt_adoc.calibration",
        "dt_adoc.scoring",
        "dt_adoc.perturbations",
        "docs/concordance",
        "OUT_STABLE_ADHESION",
        "OUT_MATERNAL_ADHESION_COMPETENCE",
    )

    def test_the_state_module_imports_and_reads_no_model_output(self) -> None:
        source = Path(klf12_state.__file__).read_text(encoding="utf-8")
        # The module's own leakage paragraph names these, so exclude the
        # docstring from the scan rather than exempting the strings globally.
        body = source.split('"""', 2)[-1]
        for token in self.FORBIDDEN:
            with self.subTest(token=token):
                self.assertNotIn(token, body)

    def test_the_evidence_table_carries_no_model_quantity(self) -> None:
        for column in klf12_state.EVIDENCE_COLUMNS:
            with self.subTest(column=column):
                self.assertFalse(column.startswith(("OUT_", "E_", "S_", "X_")))


class CellsAreNotReplicates(unittest.TestCase):
    """The unit is the donor. 20,441 cells are not 20,441 observations.

    `config/preprocessing_contract.yaml` already declares the independent unit,
    and this repository has withdrawn a cell-count-based standard error once
    before. A column whose name promises a sampling error over cells would
    reintroduce exactly that, so the names are constrained.
    """

    def test_no_column_promises_an_interval_over_cells(self) -> None:
        for column in klf12_state.EVIDENCE_COLUMNS:
            with self.subTest(column=column):
                self.assertFalse(column.endswith(("_se", "_ci", "_p_value", "_pval")))

    def test_one_row_per_donor_condition_unit(self) -> None:
        rows = _evidence()
        self.assertEqual(len(rows), 6)
        self.assertEqual({row["donor"] for row in rows}, {"SZ09", "SZ10", "SZ25"})
        self.assertEqual({row["condition"] for row in rows}, {"CNT", "HT"})
        self.assertEqual(len({row["unit_id"] for row in rows}), 6)


class DetectionIsNotTheStateModel(unittest.TestCase):
    """A threshold that equals "non-zero" must be visible as such.

    Two of the five pre-registered quantile thresholds land on zero because 83%
    of epithelial cells carry no KLF12 at all. At those values M2 is not a
    threshold model, it IS the detection rule the pre-registration declared
    inadmissible on its own, and the artifact has to say so.
    """

    def test_zero_thresholds_are_recorded_as_degenerate(self) -> None:
        findings = _findings()
        zero = {
            key
            for key, value in findings["pooled_thresholds"].items()
            if float(value) <= 0.0
        }
        self.assertEqual(zero, set(findings["degenerate_thresholds"]))
        self.assertTrue(zero, "expected the detection-boundary degeneracy")

    def test_a_degenerate_quantile_equals_the_detection_fraction(self) -> None:
        for row in _evidence():
            for key in _findings()["degenerate_thresholds"]:
                with self.subTest(unit=row["unit_id"], q=key):
                    self.assertAlmostEqual(
                        float(row[f"p_{key}"]),
                        float(row["detection_fraction"]),
                        places=9,
                    )


class TheDecisionFollowsTheFalsifiers(unittest.TestCase):
    """The pre-registered rule, re-evaluated rather than trusted."""

    def test_decision_matches_the_pre_registered_conjunction(self) -> None:
        """GO needs M1 to PASS, not merely the falsifiers to stay silent.

        This test used to re-encode the implementation's rule -- falsifiers
        only -- so the code and the test agreed with each other and both
        disagreed with `klf12_prior_preregistration.md`, which requires
        "M1 passes (a), (b) and (c), and F1, F2, F3 do not fire". It never bit,
        because F2 fired and the GO branch was unreachable, but a guard that
        restates the thing it is guarding catches nothing. It now reads the
        pre-registration's conjunction.
        """
        findings = _findings()
        checks = findings["falsifiers"]
        fired = (
            checks["F1_depth_confounding"],
            checks["F2_no_separation"],
            checks["F3_threshold_dominance"],
        )
        m1 = findings["state_model_m1"]
        if m1["m1_passes"] and not any(fired):
            expected = "GO"
        elif (
            not checks["F1_depth_confounding"] and not checks["F3_threshold_dominance"]
        ):
            expected = "CONDITIONAL_GO"
        else:
            expected = "NO_GO"
        self.assertEqual(findings["decision"], expected)

    def test_m1_is_actually_fitted_rather_than_assumed_to_fail(self) -> None:
        """A verdict of "no state" has to come from a fit that was attempted."""
        m1 = _findings()["state_model_m1"]
        self.assertGreater(m1["n_detected"], 100)
        for key in (
            "log_mean_low",
            "log_mean_high",
            "log_sd_low",
            "log_sd_high",
            "boundary_value",
            "posterior_crossings_value",
            "ordered_separation",
            "density_minimum_value",
            "analytic_bimodal",
            "m1_a_density_valley",
            "m1_b_passes",
            "m1_c_passes",
            "m1_passes",
        ):
            self.assertIn(key, m1)
        self.assertEqual(
            m1["m1_passes"],
            bool(m1["m1_a_density_valley"] and m1["m1_b_passes"] and m1["m1_c_passes"]),
        )
        # F2 is NOT M1(a) negated. The pre-registered F2 is a shape claim --
        # "a zero spike plus a monotone decreasing tail with no valley" -- and a
        # density can have a valley (so F2 stays silent) while the boundary it
        # implies is still inadmissible (so M1(a) fails). Asserting the two are
        # each other's negation is what previously let F2 be recorded as fired
        # on a fit whose own `analytic_bimodal` was True.
        self.assertEqual(
            _findings()["falsifiers"]["F2_no_separation"],
            not m1["analytic_bimodal"],
        )

    def test_a_boundary_below_one_transcript_cannot_pass_m1a(self) -> None:
        """The pre-registration's "not inside the zero spike", made checkable.

        On a decontX layer the sub-one values are the correction's residue, so a
        split there separates residue from "about one molecule" -- the detection
        rule again. This is why M1(a) is not satisfied by bimodality alone.
        """
        m1 = _findings()["state_model_m1"]
        if not m1["boundary_at_or_above_one_transcript"]:
            self.assertFalse(m1["m1_a_density_valley"])
        self.assertEqual(
            m1["boundary_at_or_above_one_transcript"],
            bool(m1["ordered_separation"])
            and float(m1["boundary_value"]) >= klf12_state.ONE_TRANSCRIPT,
        )

    def test_an_unbound_or_mismatched_table_is_refused(self) -> None:
        """`--from-per-cell` must not accept just any TSV.

        The artifact stamps EXT-SCRNA-001's digest. If nothing binds the table
        actually read to that object, unrelated data can be published as a
        result from the deposited accession. Three states are distinguished:
        no binding recorded, a binding to a different object, and a table
        edited since extraction.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            table = Path(tmp) / "per_cell.tsv"
            table.write_text("sample_id\n", encoding="utf-8")
            digest = klf12_state._sha256(table)
            declared = klf12_state.source_digest(ROOT)

            with self.assertRaises(klf12_state.Klf12StateError) as unbound:
                klf12_state.verify_source_binding(
                    table,
                    {"rds_sha256": "", "per_cell_sha256": ""},
                    root=ROOT,
                )
            self.assertIn("not bound", str(unbound.exception))

            with self.assertRaises(klf12_state.Klf12StateError) as wrong_object:
                klf12_state.verify_source_binding(
                    table,
                    {"rds_sha256": "0" * 64, "per_cell_sha256": digest},
                    root=ROOT,
                )
            self.assertIn("not the", str(wrong_object.exception))

            with self.assertRaises(klf12_state.Klf12StateError) as edited:
                klf12_state.verify_source_binding(
                    table,
                    {"rds_sha256": declared, "per_cell_sha256": "1" * 64},
                    root=ROOT,
                )
            self.assertIn("changed since extraction", str(edited.exception))

            bound = klf12_state.verify_source_binding(
                table,
                {"rds_sha256": declared, "per_cell_sha256": digest},
                root=ROOT,
            )
            self.assertEqual(bound["source_binding"], "verified")

    def test_the_committed_artifact_declares_a_verified_binding(self) -> None:
        """The shipped provenance must show the binding was checked, not assumed."""
        provenance = _findings()["provenance"]
        self.assertEqual(provenance["source_binding"], "verified")
        self.assertEqual(
            provenance["source_sha256_observed"],
            provenance["source_sha256"],
            "the object read is not the object the manifest declares",
        )
        self.assertEqual(provenance["source_sha256"], klf12_state.source_digest(ROOT))

    def test_a_crossing_outside_the_old_scan_window_is_still_found(self) -> None:
        """The regression case: a root the finite grid scan silently missed.

        An earlier revision swept [mu0 - 4*sd0, mu1 + 4*sd1] and reported the
        sign changes it bracketed. For a narrow component nested in a broad one
        the LOWER crossing can fall outside that window, so the scan returned a
        single interior crossing and the fit was reported as an ordered
        separation -- certifying a measured high state that does not exist.
        The crossings are now the quadratic's roots, so no window can hide one.
        """
        mu0, sd0 = 0.0, 0.05
        mu1, sd1 = 0.6, 0.10
        weight = 0.5
        crossings = klf12_state._component_crossings(mu0, sd0**2, mu1, sd1**2, weight)
        self.assertEqual(len(crossings), 2, crossings)

        window_low, window_high = mu0 - 4 * sd0, mu1 + 4 * sd1
        outside = [x for x in crossings if not window_low <= x <= window_high]
        self.assertEqual(len(outside), 1, "fixture must exercise the missed root")

        # What the old scan would have concluded, and why it was wrong.
        scanned = [x for x in crossings if window_low <= x <= window_high]
        interior_scanned = [x for x in scanned if mu0 < x < mu1]
        self.assertEqual(len(scanned), 1)
        self.assertTrue(
            len(scanned) == 1 and len(interior_scanned) == 1,
            "the old window would have reported a FALSE ordered separation",
        )
        # And what the solved crossings conclude instead.
        interior = [x for x in crossings if mu0 < x < mu1]
        self.assertFalse(len(crossings) == 1 and len(interior) == 1)

    def test_a_nearly_linear_quadratic_still_yields_both_roots(self) -> None:
        """Only an exactly zero quadratic term is linear.

        An earlier revision treated `abs(a) < 1e-15` as linear and returned one
        root. For variances differing by one part in 1e15 the quadratic is tiny
        but nonzero and its roots are 0.5 and -1.8e15; dropping the second
        leaves a single interior crossing, which reads as an ordered separation
        that is not there.
        """
        crossings = klf12_state._component_crossings(0.0, 1.0, 1.0, 1.0 + 1e-15, 0.5)
        self.assertEqual(len(crossings), 2, crossings)
        self.assertAlmostEqual(crossings[1], 0.5, places=9)
        self.assertLess(crossings[0], -1e14)
        # Both roots satisfy the equal-density equation they were solved from.
        for x in crossings:
            low = 0.5 * klf12_state._normal_pdf(x, 0.0, 1.0)
            high = 0.5 * klf12_state._normal_pdf(x, 1.0, math.sqrt(1.0 + 1e-15))
            self.assertAlmostEqual(low, high, places=12)
        # Exactly equal variances really are linear: one root, not two.
        self.assertEqual(
            len(klf12_state._component_crossings(0.0, 1.0, 1.0, 1.0, 0.5)), 1
        )

    def test_a_well_separated_mixture_can_still_be_ordered(self) -> None:
        """The criterion must be satisfiable, or it is not a test but a verdict.

        Two unequal-variance normals always cross twice somewhere. For a
        textbook separation (mu 0 and 5, sd 1 and 1.2) the second root is at
        -25, far outside anything observed. Counting it would reject a genuine
        two-state fit, so only crossings inside the fitted data's support count.
        """
        roots = klf12_state._component_crossings(0.0, 1.0, 5.0, 1.2**2, 0.5)
        self.assertEqual(len(roots), 2, roots)
        support_low, support_high = -4.0, 9.0
        in_support = [x for x in roots if support_low <= x <= support_high]
        self.assertEqual(len(in_support), 1, in_support)
        self.assertTrue(0.0 < in_support[0] < 5.0)
        # The out-of-support root is what an unrestricted rule would have
        # counted, turning a clean separation into a false "not ordered".
        self.assertLess(min(roots), support_low)

    def test_the_conclusion_depends_on_the_in_support_conjunction(self) -> None:
        """State plainly what the weaker rule would have concluded.

        Both of this fit's crossings lie inside the observed data, so the
        wraparound is real. Had only the between-means crossing been required,
        a boundary ABOVE one transcript would have been returned and M1(a)
        would have passed -- so the artifact must record that counterfactual
        rather than leave the dependence implicit.
        """
        m1 = _findings()["state_model_m1"]
        low, high = m1["detected_log_support"]
        for crossing in m1["posterior_crossings_log"]:
            self.assertTrue(low <= crossing <= high, "expected the both-tails case")
        self.assertEqual(
            len(m1["posterior_crossings_in_support_log"]),
            len(m1["posterior_crossings_log"]),
        )
        self.assertFalse(m1["ordered_separation"])
        # The counterfactual the document states, pinned.
        self.assertIsNotNone(m1["interior_only_rule_boundary_value"])
        self.assertGreater(
            float(m1["interior_only_rule_boundary_value"]),
            klf12_state.ONE_TRANSCRIPT,
        )

    def test_the_recorded_derivation_digest_is_this_module(self) -> None:
        """Presence pins nothing; every published hash is recomputed."""
        provenance = _findings()["provenance"]
        module = Path(klf12_state.__file__).resolve()
        self.assertEqual(
            provenance["derivation_module_sha256"],
            klf12_state._sha256(module),
            "the recorded derivation digest is not this module's",
        )

    def test_findings_artifact_is_standards_compliant_json(self) -> None:
        """A shipped artifact a strict parser cannot load is not shipped.

        `json.dump` emits bare `NaN` for a float NaN, which is a Python
        extension and not JSON. An earlier revision of this repair encoded
        "no ordered boundary exists" that way, so every standards-compliant
        consumer failed on the file. Absence is `null`.
        """

        def reject(token: str) -> float:
            raise ValueError(f"non-standard JSON token: {token}")

        with FINDINGS.open(encoding="utf-8") as handle:
            json.load(handle, parse_constant=reject)
        self.assertNotIn("NaN", FINDINGS.read_text(encoding="utf-8"))

    def test_m1c_uses_posterior_assignment_not_a_cut_on_expression(self) -> None:
        """M1(c) asks whether the fit's OWN assignment tracks depth.

        With a narrow component nested inside a broad one the assignment is not
        monotone in expression: the broad "high" component owns both tails, so
        cells BELOW the lower crossing are assigned high. No threshold
        reproduces that, and an earlier revision of this repair cut at the
        valley -- which silently measured a different partition than the one
        M1(c) names.
        """
        m1 = _findings()["state_model_m1"]
        self.assertEqual(m1["m1_c_split_basis"], "posterior_component_assignment")
        # A valley cut must not be reported as the basis, nor survive as a key.
        self.assertNotIn("m1_c_split_value", m1)

        mu_low = float(m1["log_mean_low"])
        sd_low = float(m1["log_sd_low"])
        mu_high = float(m1["log_mean_high"])
        sd_high = float(m1["log_sd_high"])
        w_high = float(m1["high_component_weight"])

        def assigned_high(point: float) -> bool:
            return w_high * klf12_state._normal_pdf(point, mu_high, sd_high) >= (
                1 - w_high
            ) * klf12_state._normal_pdf(point, mu_low, sd_low)

        crossings = sorted(float(v) for v in m1["posterior_crossings_log"])
        if m1["ordered_separation"]:
            self.skipTest("fit has an ordered boundary; both-tail case not present")
        self.assertGreaterEqual(len(crossings), 2)
        lower, upper = crossings[0], crossings[-1]
        # The defining property: high on BOTH sides, low strictly between.
        self.assertTrue(assigned_high(lower - 0.5))
        self.assertTrue(assigned_high(upper + 0.5))
        self.assertFalse(assigned_high((lower + upper) / 2))
        # Therefore no cut on expression reproduces the assignment.
        valley = float(m1["density_minimum_log"])
        self.assertTrue(
            assigned_high(lower - 0.5) and (lower - 0.5) < valley,
            "a valley cut would call this cell low; the fit calls it high",
        )

    def test_every_posterior_crossing_is_reported_not_just_the_first(self) -> None:
        """The defect this guards: a left-to-right scan that broke at the first.

        With a narrow component inside a broad one the posterior-0.5 set has two
        points and the broad component owns BOTH tails, so no single crossing
        separates low from high. Reporting the first one found made a scan
        direction look like a measurement.
        """
        m1 = _findings()["state_model_m1"]
        crossings = list(m1["posterior_crossings_value"])
        self.assertTrue(crossings)
        interior = [
            value
            for value in m1["posterior_crossings_log"]
            if m1["log_mean_low"] < value < m1["log_mean_high"]
        ]
        self.assertEqual(
            bool(m1["ordered_separation"]),
            len(crossings) == 1 and len(interior) == 1,
        )
        if not m1["ordered_separation"]:
            # No ordered boundary exists, so none may be reported as one --
            # and "absent" is encoded as JSON null, never as a NaN token.
            self.assertIsNone(m1["boundary_value"])
            self.assertIsNone(m1["boundary_log"])

    def test_the_multimodality_present_is_the_integer_molecule_lattice(self) -> None:
        """The reason a two-component fit finds "modes" that are not states.

        The detected-value modes must sit on log(1), log(2), log(3)... If they
        ever stop doing so, the claim in the report that the structure is a
        count lattice rather than a biological state is no longer true and has
        to be re-derived.
        """
        findings = _findings()
        modes = findings["detected_log_mode_positions"]
        integers = findings["integer_transcript_log_positions"]
        self.assertGreaterEqual(len(modes), 3)
        matched = 0
        for target in integers:
            if any(abs(mode - target) < 0.12 for mode in modes):
                matched += 1
        self.assertGreaterEqual(
            matched, 4, f"modes {modes} do not sit on the integer lattice {integers}"
        )

    def test_both_readings_of_f3_are_recorded(self) -> None:
        """The one loose sentence in the pre-registration, disclosed not hidden.

        The permissive reading is the one that licenses running the sweep, so
        the strict reading's verdict has to be in the artifact beside it.
        """
        checks = _findings()["falsifiers"]
        self.assertIn("F3_threshold_dominance_strict_reading", checks)
        self.assertIn("F3_reading", checks)
        self.assertLessEqual(
            checks["F3_smallest_across_unit_spread"],
            checks["F3_largest_across_unit_spread"],
        )

    def test_standardised_rates_carry_the_weight_of_their_thinnest_stratum(
        self,
    ) -> None:
        """A cell count alone understates how much one thin stratum decides."""
        for row in _evidence():
            with self.subTest(unit=row["unit_id"]):
                for prefix in ("depth", "subtype"):
                    self.assertTrue(row[f"{prefix}_stratum_min_cells"])
                    weight = float(row[f"{prefix}_stratum_min_weight"])
                    self.assertGreater(weight, 0.0)
                    self.assertLessEqual(weight, 1.0)

    def test_no_measured_prior_is_claimed_while_f2_stands(self) -> None:
        findings = _findings()
        if findings["falsifiers"]["F2_no_separation"]:
            self.assertNotEqual(findings["decision"], "GO")
            self.assertEqual(
                findings["provenance"]["claim_level"],
                "conditioning_candidate_not_validation",
            )

    def test_f4_holds_because_no_donor_carries_a_reference_label(self) -> None:
        """REF-037 defines high KLF12 against fertile controls. There are none."""
        policy = (ROOT / "config" / "personalization.yaml").read_text(encoding="utf-8")
        self.assertIn("external_reference_required", policy)
        self.assertIn("reference_path: null", policy)
        self.assertTrue(_findings()["falsifiers"]["F4_no_reference_for_high"])


class TheArtifactPinsItsOwnProvenance(unittest.TestCase):
    def test_source_digest_agrees_with_the_external_manifest(self) -> None:
        self.assertEqual(
            _findings()["provenance"]["source_sha256"],
            klf12_state.source_digest(ROOT),
        )

    def test_the_preregistration_is_pinned_by_content(self) -> None:
        import hashlib

        self.assertEqual(
            _findings()["provenance"]["preregistration_sha256"],
            hashlib.sha256(PREREGISTRATION.read_bytes()).hexdigest(),
        )

    def test_the_population_is_the_pre_declared_one(self) -> None:
        self.assertEqual(
            tuple(_findings()["population_definition"]),
            klf12_state.EPITHELIAL_LABELS,
        )
        for label in klf12_state.EPITHELIAL_LABELS:
            with self.subTest(label=label):
                self.assertIn(label, PREREGISTRATION.read_text(encoding="utf-8"))


class AvailabilityIsStillNotIntegration(unittest.TestCase):
    """Having fetched the object activates nothing. Leakage control 4."""

    def test_the_external_asset_is_not_marked_integrated(self) -> None:
        manifest = ROOT / "config" / "external_data_manifest.tsv"
        with manifest.open(newline="", encoding="utf-8") as handle:
            rows = {
                row["asset_id"]: row for row in csv.DictReader(handle, delimiter="\t")
            }
        self.assertEqual(
            rows[klf12_state.ASSET_ID]["inspection_state"],
            "structurally_verified_not_integrated",
        )

    def test_the_klf12_row_is_not_an_active_constraint(self) -> None:
        map_path = ROOT / "config" / "scrna_observation_map.tsv"
        with map_path.open(newline="", encoding="utf-8") as handle:
            row = next(
                item
                for item in csv.DictReader(handle, delimiter="\t")
                if item["model_node"] == "E_KLF12_HIGH"
            )
        self.assertNotIn(
            row["activation_status"], {"active_constraint", "active_diagnostic"}
        )
        self.assertEqual(row["evidence_role"], "same_dataset_internal")


class TheArithmeticIsCheckedOnDataTheTestOwns(unittest.TestCase):
    """The committed artifact cannot prove the derivation; a fixture can."""

    def _table(self, rows: list[tuple[str, str, float, int, float]]) -> Path:
        import tempfile

        path = Path(tempfile.mkdtemp(prefix="klf12_test_")) / "per_cell.tsv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(
                [
                    "sample_id",
                    "celltype_v2",
                    "depth_counts",
                    "nfeature_counts",
                    "counts_KLF12",
                ]
            )
            for row in rows:
                writer.writerow(list(row))
        return path

    def test_only_the_pre_declared_population_contributes(self) -> None:
        rows = []
        for index in range(40):
            rows.append(
                ("SZ09TE_CNT", "Luminal-like epithelium", 1000 + index, 100, 0.0)
            )
            rows.append(
                (
                    "SZ09TE_HT",
                    "Cycling epithelium",
                    1000 + index,
                    100,
                    1.0 + index * 0.1,
                )
            )
        # Stroma carries KLF12 in every cell and must change nothing.
        rows += [("SZ09TE_CNT", "Stroma", 1000 + i, 100, 9.0) for i in range(20)]
        path = self._table(rows)
        try:
            findings = klf12_state.derive(path)
        finally:
            path.unlink()
        self.assertEqual(findings["n_cells_epithelial"], 80)
        self.assertEqual(findings["n_cells_object"], 100)
        by_unit = {row["unit_id"]: row for row in findings["per_unit"]}
        self.assertAlmostEqual(by_unit["SZ09TE_CNT"]["detection_fraction"], 0.0)
        self.assertAlmostEqual(by_unit["SZ09TE_HT"]["detection_fraction"], 1.0)
        self.assertEqual(by_unit["SZ09TE_CNT"]["n_cells_sample_total"], 60)

    def test_a_unit_that_misses_a_stratum_gets_no_standardised_rate(self) -> None:
        """Non-overlap must surface as absence, never as a partial-mix average."""
        rows = [
            (
                "SZ09TE_CNT",
                "Luminal-like epithelium",
                1000 + index,
                100,
                1.0 + index * 0.1,
            )
            for index in range(40)
        ]
        rows += [
            (
                "SZ09TE_HT",
                "Luminal-like epithelium",
                90000 + index,
                100,
                2.0 + index * 0.1,
            )
            for index in range(40)
        ]
        path = self._table(rows)
        try:
            findings = klf12_state.derive(path)
        finally:
            path.unlink()
        by_unit = {row["unit_id"]: row for row in findings["per_unit"]}
        self.assertIsNone(by_unit["SZ09TE_CNT"]["detection_depth_standardised"])
        self.assertIsNone(by_unit["SZ09TE_HT"]["detection_depth_standardised"])

    def test_an_undetected_gene_is_an_error_not_a_zero_prior(self) -> None:
        rows = [
            ("SZ09TE_CNT", "Luminal-like epithelium", 1000 + index, 100, 0.0)
            for index in range(10)
        ]
        path = self._table(rows)
        try:
            with self.assertRaises(klf12_state.Klf12StateError):
                klf12_state.derive(path)
        finally:
            path.unlink()


class APostHocRuleIsNotAPreRegisteredOne(unittest.TestCase):
    """The distinction this increment exists to keep, enforced not asserted.

    The frozen pre-registration is one sentence about M1(a). Everything the
    implementation does beyond it -- counting crossings, requiring an ordering,
    requiring a support -- was chosen after the data existed. Promoting any of
    it into the pre-registration would be retroactive pre-registration, which
    is the failure mode the whole document exists to prevent, so the labelling
    is a test rather than a comment.
    """

    def test_the_frozen_sentence_names_no_crossing_ordering_or_support(self) -> None:
        text = PREREGISTRATION.read_text(encoding="utf-8").lower()
        self.assertIn("genuine density valley", text)
        # "support" appears in the frozen text, but only as "support an
        # estimate" and "no experimental support" -- never as the support of a
        # distribution, which is the sense the implemented rule needs.
        self.assertNotIn("fitted data", text)
        for invented in ("posterior", "crossing", "ordered separation"):
            self.assertNotIn(
                invented,
                text,
                f"the frozen pre-registration does not say {invented!r}; a rule "
                "built on it may not be described as pre-registered",
            )

    def test_the_artifact_labels_the_applied_rule_post_hoc(self) -> None:
        m1 = _findings()["state_model_m1"]
        self.assertEqual(m1["m1_a_rule_provenance"], "post_hoc_operationalisation")
        self.assertEqual(
            m1["m1_a_frozen_wording"],
            "the implied boundary falls in a genuine density valley, not "
            "inside the zero spike",
        )
        self.assertIn("exactly one posterior crossing", m1["m1_a_rule_applied"])

    def test_every_defensible_reading_is_recorded_with_its_own_verdict(self) -> None:
        """Ambiguity is part of the result, so it is committed, not resolved."""
        readings = _findings()["state_model_m1"]["m1_a_under_each_reading"]
        self.assertEqual(
            set(readings), set(klf12_state.M1_A_READINGS), "a reading went missing"
        )
        verdicts = {name: bool(body["passes"]) for name, body in readings.items()}
        # The whole point: on THIS fit the readings disagree. If they ever stop
        # disagreeing the report's framing has to be re-derived rather than
        # silently kept.
        self.assertEqual(
            len(set(verdicts.values())),
            2,
            f"the readings no longer disagree ({verdicts}); the reported "
            "ambiguity is stale",
        )
        self.assertFalse(verdicts["implemented"])
        self.assertTrue(verdicts["interior_only"])
        self.assertTrue(verdicts["density_valley"])

    def test_the_conclusion_does_not_rest_on_which_reading_is_chosen(self) -> None:
        """The specificity failure, which is what actually settles it.

        Each reading is run over a population simulated with NO latent state.
        A reading that certifies that population cannot be evidence of a state
        here, whichever way it votes on the real fit -- so if any reading ever
        stops passing the null, the argument in the report changes and this
        test must fail rather than pass quietly.
        """
        calibration = _findings()["state_model_m1"]["m1_a_specificity_calibration"]
        self.assertGreaterEqual(calibration["replicates"], 20)
        for name in klf12_state.M1_A_READINGS:
            self.assertEqual(
                calibration["m1_a_false_pass_rate"][name],
                1.0,
                f"{name} no longer certifies the no-state null; the report's "
                "claim that no reading can settle this is no longer supported",
            )

    def test_the_null_is_a_no_state_population_not_a_relabelled_one(self) -> None:
        """Guard the null itself: a null with a state in it proves nothing."""
        calibration = _findings()["state_model_m1"]["m1_a_specificity_calibration"]
        self.assertIn("no latent", str(calibration["null_model"]))
        self.assertIn("one homogeneous Poisson rate", str(calibration["null_model"]))
        self.assertGreater(float(calibration["calibrated_rate_at_mean_depth"]), 0.0)

    def test_the_specificity_claim_is_scoped_to_this_lattice_resolution(self) -> None:
        """Do not let "the rule is broken" grow into more than was shown."""
        calibration = _findings()["state_model_m1"]["m1_a_specificity_calibration"]
        self.assertIn("not a universal property", str(calibration["scope"]))
        widened = calibration["false_pass_under_widened_shrinkage_noise"]
        self.assertTrue(widened, "no widened-noise arm was recorded")
        cheapest = min(
            (body for body in widened.values()),
            key=lambda body: sum(body[name] for name in klf12_state.M1_A_READINGS),
        )
        self.assertLess(
            sum(cheapest[name] for name in klf12_state.M1_A_READINGS),
            3 * int(cheapest["replicates"]),
            "smearing the lattice did not reduce the false passes at all, so "
            "the failure is not attributable to the lattice as claimed",
        )


class TheSupportDefinitionIsNotTheEvidence(unittest.TestCase):
    """4.5e-15 is decontX residue, not a measurement, and may not decide M1(a)."""

    def test_the_numeric_support_floor_is_one_cell_of_residue(self) -> None:
        m1 = _findings()["state_model_m1"]
        full_low, _ = m1["detected_log_support"]
        trimmed_low, _ = m1["detected_log_support_trimmed_98"]
        self.assertLess(
            full_low,
            -20.0,
            "the raw support floor is expected to be numerical residue",
        )
        self.assertGreater(trimmed_low, -3.0)

    def test_trimming_the_residue_does_not_change_the_verdict(self) -> None:
        m1 = _findings()["state_model_m1"]
        self.assertFalse(
            m1["support_definition_changes_m1_a"],
            "M1(a) now turns on where the support floor is put, so a decontX "
            "residue value is deciding a biological question",
        )
        self.assertEqual(
            len(m1["posterior_crossings_in_trimmed_support_log"]),
            2,
            "both crossings should survive trimming to the central 98%",
        )


class TheFalsifierIsTheFrozenSentence(unittest.TestCase):
    """F2 must be evaluated on what was written, with the proxy kept visible."""

    def test_f2_is_decided_on_the_empirical_histogram(self) -> None:
        falsifiers = _findings()["falsifiers"]
        self.assertEqual(
            falsifiers["F2_basis"], "empirical_histogram_of_detected_values"
        )
        self.assertFalse(falsifiers["F2_tail_is_monotone_decreasing"])
        self.assertGreaterEqual(int(falsifiers["F2_tail_interior_modes"]), 2)
        self.assertFalse(falsifiers["F2_no_separation"])

    def test_the_fitted_density_proxy_is_recorded_as_a_proxy(self) -> None:
        falsifiers = _findings()["falsifiers"]
        self.assertIn("F2_fitted_density_proxy", falsifiers)
        self.assertIn("proxy", str(falsifiers["F2_proxy_note"]))


class TheDepthCheckIsStratifiedAndItsBarIsPostHoc(unittest.TestCase):
    """M1(c) as a within-unit claim, which is the claim it actually makes."""

    def test_the_depth_ratio_is_reported_per_unit(self) -> None:
        m1 = _findings()["state_model_m1"]
        per_unit = m1["m1_c_depth_ratio_per_unit"]
        self.assertEqual(len(per_unit), 6)
        self.assertEqual(m1["m1_c_units_evaluated"], 6)

    def test_the_bar_is_not_what_carries_the_conclusion(self) -> None:
        """Direction disagreeing is the evidence; the 1.5 bar is post-hoc."""
        m1 = _findings()["state_model_m1"]
        self.assertEqual(
            m1["m1_c_bar_provenance"], "post_hoc_threshold_not_pre_registered"
        )
        self.assertFalse(
            m1["m1_c_ratio_direction_is_consistent"],
            "the within-unit depth ratios now agree in direction, which would "
            "be a depth signal the report says is absent",
        )

    def test_the_high_component_is_not_simply_more_klf12(self) -> None:
        """The fact the whole report turns on, pinned as a number."""
        m1 = _findings()["state_model_m1"]
        below = int(m1["high_component_below_lower_crossing"])
        above = int(m1["high_component_above_upper_crossing"])
        self.assertGreater(
            below,
            0,
            "cells BELOW the lower crossing must still be assigned high, or "
            "the component is ordered after all",
        )
        self.assertGreater(above, below)


class TheDecisionItselfDependsOnThePostHocRule(unittest.TestCase):
    """The strongest form of the finding, and the reason for the revision.

    M1(b) and M1(c) pass and F1, F2 and F3 are all silent, so M1(a) alone picks
    the branch -- and M1(a) is decided by a rule chosen after the data existed.
    Under either reading closer to the frozen wording the pre-registered rule
    awards **GO**, which is the branch that would license promoting
    `EXT-SCRNA-001` to an active constraint. Nothing was promoted, and the point
    of committing this is that the dependence cannot become invisible again.
    """

    def test_the_branch_would_differ_under_a_defensible_reading(self) -> None:
        findings = _findings()
        by_reading = findings["decision_under_each_m1_a_reading"]
        self.assertTrue(findings["decision_depends_on_the_post_hoc_m1_a_rule"])
        self.assertEqual(by_reading["implemented"], findings["decision"])
        self.assertEqual(by_reading["implemented"], "CONDITIONAL_GO")
        self.assertEqual(by_reading["interior_only"], "GO")
        self.assertEqual(by_reading["density_valley"], "GO")

    def test_the_preregistration_does_not_determine_one_branch(self) -> None:
        """Two loose sentences, pulling opposite ways, and all three branches
        reachable. Recording a single branch as "the" pre-registered outcome
        would hide that, which is what an earlier revision did."""
        findings = _findings()
        grid = findings["decision_under_each_reading_pair"]
        self.assertEqual(len(grid), 6, "3 M1(a) readings x 2 F3 readings")
        self.assertEqual(
            sorted(findings["decision_branches_reachable"]),
            ["CONDITIONAL_GO", "GO", "NO_GO"],
        )
        self.assertFalse(
            findings["decision_is_uniquely_determined_by_the_preregistration"]
        )
        # The shipped decision must be a cell of the grid, not a seventh answer.
        self.assertIn(findings["decision"], set(grid.values()))
        self.assertEqual(grid["implemented+f3_permissive"], findings["decision"])
        # Under the strict F3 reading, F3 overrides M1(a) entirely.
        for reading in klf12_state.M1_A_READINGS:
            self.assertEqual(grid[f"{reading}+f3_strict"], "NO_GO")

    def test_the_calibration_states_what_it_does_not_cover(self) -> None:
        """The scope limit, enforced. M1(c) and the falsifiers are NOT run on
        the null, so the artifact may not imply the whole battery was."""
        calibration = _findings()["state_model_m1"]["m1_a_specificity_calibration"]
        self.assertIn("M1(b)", calibration["covers"])
        for uncovered in ("M1(c)", "F1", "F2", "F3", "the decision branch"):
            self.assertIn(uncovered, calibration["does_not_cover"])
        # (b) is cheap to evaluate on the null and is, so it is reported.
        self.assertGreaterEqual(calibration["m1_b_false_pass_count"], 0)
        self.assertLessEqual(
            calibration["m1_b_false_pass_count"], calibration["replicates"]
        )

    def test_nothing_was_promoted_on_the_go_branch_anyway(self) -> None:
        """A GO under some reading may not leak into the shipped claim level."""
        provenance = _findings()["provenance"]
        self.assertEqual(provenance["evidence_role"], "same_dataset_internal")
        self.assertEqual(
            provenance["claim_level"], "conditioning_candidate_not_validation"
        )


if __name__ == "__main__":
    unittest.main()
