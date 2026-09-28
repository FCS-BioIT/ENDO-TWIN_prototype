"""What the conditioning layer may do to v0.4, and what it may never claim.

Three separate risks, and none of them is caught by the simulation agreeing with
itself:

1. **The prior lands on the wrong thing.** MaBoSS takes a probabilistic initial
   state only in a bracketed form that does not share a merge key with the plain
   `E_KLF12_HIGH.istate = FALSE;` in `baseline.cfg`, so the natural
   implementation leaves both lines in the configuration. The engine rejects
   that outright rather than picking one, which is the good case; the bad case
   is a future edit that silences it by touching a different node's line
   instead.
2. **v0.4 changes underneath.** The increment is allowed to add an overlay and
   nothing else. The canonical rule and the canonical initial state are
   fingerprinted here so an "improvement" to either has to be deliberate.
3. **The sensitivity analysis is promoted in the retelling.** The state
   derivation found no KLF12-high boundary, so whatever the sweep produces is a
   response curve over an arbitrary threshold. The artifact has to keep saying
   that even when the prose around it is rewritten.
"""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.scrna import klf12_conditioning as conditioning

MODEL = ROOT / "models" / "superset" / "adoc-literature-superset-v0.4.0"
RESPONSE = ROOT / "docs" / "scrna" / "klf12_conditioning_response.tsv"
SETTINGS = ROOT / "docs" / "scrna" / "klf12_conditioning_settings.json"
FINDINGS = ROOT / "docs" / "scrna" / "klf12_state_findings.json"


class ThePriorIsWrittenWhereItIsMeantTo(unittest.TestCase):
    def test_the_override_is_the_bracketed_form_for_exactly_one_node(self) -> None:
        text = conditioning.istate_override_text(0.25)
        self.assertEqual(text, "[E_KLF12_HIGH].istate = 0.75[0], 0.25[1];\n")
        self.assertEqual(text.count("istate"), 1)
        self.assertEqual(text.count("E_KLF12_HIGH"), 1)

    def test_a_non_probability_is_refused(self) -> None:
        for value in (-0.01, 1.01, 2.0):
            with (
                self.subTest(value=value),
                self.assertRaises(conditioning.Klf12ConditioningError),
            ):
                conditioning.istate_override_text(value)

    def test_substitution_replaces_the_line_and_adds_none(self) -> None:
        cfg = "A.istate = FALSE;\nE_KLF12_HIGH.istate = FALSE;\nB.istate = TRUE;\n"
        out = conditioning._substitute_istate(cfg, 0.4)
        self.assertEqual(out.count("E_KLF12_HIGH"), 1)
        self.assertIn("[E_KLF12_HIGH].istate = 0.6[0], 0.4[1];", out)
        self.assertIn("A.istate = FALSE;", out)
        self.assertIn("B.istate = TRUE;", out)
        self.assertEqual(len(out.splitlines()), len(cfg.splitlines()))

    def test_a_configuration_without_exactly_one_line_is_refused(self) -> None:
        for cfg in (
            "A.istate = FALSE;\n",
            "E_KLF12_HIGH.istate = FALSE;\nE_KLF12_HIGH.istate = TRUE;\n",
        ):
            with (
                self.subTest(cfg=cfg),
                self.assertRaises(conditioning.Klf12ConditioningError),
            ):
                conditioning._substitute_istate(cfg, 0.4)

    def test_the_mixture_law_the_run_has_to_reproduce(self) -> None:
        self.assertAlmostEqual(conditioning.mixture_prediction(0.82, 0.0, 0.0), 0.82)
        self.assertAlmostEqual(conditioning.mixture_prediction(0.82, 0.0, 1.0), 0.0)
        self.assertAlmostEqual(conditioning.mixture_prediction(0.82, 0.0, 0.25), 0.615)
        # The cases the withdrawn scaling law got wrong: a node the conditioned
        # state cannot reach, and the conditioned node itself.
        self.assertAlmostEqual(conditioning.mixture_prediction(1.0, 1.0, 0.4), 1.0)
        self.assertAlmostEqual(conditioning.mixture_prediction(0.0, 1.0, 0.4), 0.4)


class TheCanonicalModelIsUnchanged(unittest.TestCase):
    """Out of scope in this increment: every Boolean rule, and the baseline."""

    def test_the_klf12_rule_is_still_the_free_variable_v04_declared(self) -> None:
        network = (MODEL / "network.bnd").read_text(encoding="utf-8")
        self.assertIn("Node E_KLF12_HIGH {\n  logic = E_KLF12_HIGH;\n}", network)
        self.assertIn(
            "Node E_LIF {\n  logic = E_SECRETORY_STATE and not E_KLF12_HIGH;\n}",
            network,
        )

    def test_the_canonical_initial_state_is_still_a_bare_false(self) -> None:
        baseline = (MODEL / "baseline.cfg").read_text(encoding="utf-8")
        self.assertIn("E_KLF12_HIGH.istate = FALSE;", baseline)
        self.assertNotIn("[E_KLF12_HIGH].istate", baseline)

    def test_no_condition_configuration_carries_a_prior(self) -> None:
        for path in sorted((MODEL / "conditions").glob("*.cfg")):
            with self.subTest(cfg=path.name):
                self.assertNotIn(
                    "[E_KLF12_HIGH].istate", path.read_text(encoding="utf-8")
                )


class TheCandidatePriorsAreWhatTheyAreSaidToBe(unittest.TestCase):
    """The upper end of the swept range is the detection rule, not a threshold.

    `candidate_priors` reads all five quantile columns, and two of them are
    degenerate -- the pooled 75th and 80th percentiles of KLF12 are exactly
    zero. So the largest candidate is a *detection fraction*, which the
    pre-registration declared the upper bound on any threshold-based estimate
    rather than an estimate in its own right. The report says so; this makes it
    checkable, and makes a future edit that quietly drops the degenerate columns
    -- narrowing the reported range without saying so -- fail here.
    """

    def test_the_largest_candidate_is_a_detection_fraction(self) -> None:
        candidates = conditioning.candidate_priors(ROOT)
        self.assertEqual(len(candidates), 30)
        with (ROOT / "docs" / "scrna" / "klf12_state_evidence.tsv").open(
            newline="", encoding="utf-8"
        ) as handle:
            detection = [
                float(row["detection_fraction"])
                for row in csv.DictReader(handle, delimiter="\t")
            ]
        self.assertAlmostEqual(max(candidates.values()), max(detection), places=9)

    def test_the_degenerate_quantiles_are_still_in_the_swept_range(self) -> None:
        findings = json.loads(FINDINGS.read_text(encoding="utf-8"))
        degenerate = set(findings["degenerate_thresholds"])
        self.assertTrue(degenerate)
        swept = {key.split(":")[1] for key in conditioning.candidate_priors(ROOT)}
        self.assertTrue(degenerate <= {key.removeprefix("p_") for key in swept})


class TheSweepStaysASensitivityAnalysis(unittest.TestCase):
    def setUp(self) -> None:
        if not SETTINGS.is_file():
            self.skipTest("the conditioning sweep has not been run in this tree")

    def test_the_run_records_reconstructable_lineage(self) -> None:
        """A simulation artifact whose inputs are not pinned cannot show drift.

        The executable surface is the rule set, the initial-condition/rate file
        and the protocol schedule; the candidate priors come from the state
        derivation, so that artifact is an input of this run too. Without these
        a later number that differs has no diagnosable cause.
        """
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        provenance = settings["provenance"]
        for key in (
            "network_bnd_sha256",
            "baseline_cfg_sha256",
            "protocols_yaml_sha256",
            "condition_cfg_sha256",
            "implementation_digest",
            "source_evidence_sha256",
            "source_findings_sha256",
            "time_tick",
            "trajectory_count",
            "seeds",
            "converged_phase_horizon",
        ):
            self.assertIn(key, provenance, f"provenance is missing {key}")
        # Presence pins nothing. EVERY recorded hash is recomputed from this
        # tree, so a recorded value that has drifted from the file it names
        # fails here rather than silently certifying a stale lineage.
        import hashlib

        from dt_adoc.concordance.simulate import (
            implementation_digest,
            implementation_files,
        )
        from dt_adoc.model.runtime import resolve_model

        def sha256(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()

        model = resolve_model(provenance["model_version"], ROOT)
        for key, path in (
            ("source_evidence_sha256", ROOT / "docs/scrna/klf12_state_evidence.tsv"),
            ("source_findings_sha256", FINDINGS),
            ("network_bnd_sha256", Path(model.network_bnd)),
            ("baseline_cfg_sha256", Path(model.baseline_cfg)),
            ("protocols_yaml_sha256", ROOT / "config" / "protocols.yaml"),
        ):
            self.assertEqual(
                provenance[key],
                sha256(path),
                f"{key} does not match the file it names",
            )

        expected_conditions = {
            path.name: sha256(path)
            for path in sorted(Path(model.condition_dir).glob("*.cfg"))
        }
        self.assertEqual(provenance["condition_cfg_sha256"], expected_conditions)

        files = implementation_files(ROOT)
        self.assertEqual(
            provenance["implementation_digest"],
            implementation_digest(ROOT, files),
            "the recorded implementation digest is not this tree's",
        )
        self.assertEqual(list(provenance["implementation_files"]), list(files))

        # The generator itself decides the grid, the istate substitution and the
        # aggregation, and is not covered by the shared digest above. A change
        # to it can move every number while every other hash stays identical,
        # so it is pinned separately and recomputed here.
        generator_files = tuple(provenance["generator_files"])
        self.assertIn("src/dt_adoc/scrna/klf12_conditioning.py", generator_files)
        self.assertEqual(
            provenance["generator_digest"],
            implementation_digest(ROOT, generator_files),
            "the recorded generator digest is not this tree's",
        )

    def test_reported_spread_is_recomputable_from_its_parents(self) -> None:
        """An sd with no per-seed parents is a summary nobody can check."""
        from statistics import pstdev

        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        checked = 0
        for run in settings["runs"]:
            self.assertIn("node_by_seed", run)
            for node_id, sd in run["node_sd"].items():
                values = run["node_by_seed"][node_id]
                self.assertEqual(len(values), len(run["seeds"]))
                expected = pstdev(values) if len(values) > 1 else 0.0
                self.assertAlmostEqual(sd, expected, places=12)
                checked += 1
        self.assertGreater(checked, 0)

    def test_the_claim_level_matches_the_state_decision(self) -> None:
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        decision = json.loads(FINDINGS.read_text(encoding="utf-8"))["decision"]
        if decision != "GO":
            self.assertEqual(
                settings["claim_level"], "arbitrary_threshold_sensitivity_analysis"
            )

    def test_the_unconditioned_row_is_the_canonical_model(self) -> None:
        """p = 0 must reproduce the tracked concordance value, not approach it."""
        concordance = json.loads(
            (ROOT / "docs" / "concordance" / "run_settings.json").read_text(
                encoding="utf-8"
            )
        )
        reference = {
            arm["arm_id"]: arm["node_mean"]
            for arm in concordance["arms"]
            if arm["horizon_class"] == "converged"
        }
        with RESPONSE.open(newline="", encoding="utf-8") as handle:
            rows = [
                row
                for row in csv.DictReader(handle, delimiter="\t")
                if float(row["prior"]) == 0.0
            ]
        self.assertTrue(rows)
        for row in rows:
            expected = reference.get(row["arm_id"], {}).get(row["node_id"])
            if expected is None:
                continue
            with self.subTest(arm=row["arm_id"], node=row["node_id"]):
                self.assertAlmostEqual(float(row["node_mean"]), expected, places=2)

    def test_every_row_obeys_the_mixture_law(self) -> None:
        """The check that the prior reached `E_KLF12_HIGH` and nothing else.

        Every tracked node, every arm, every prior -- no node is exempted. An
        exemption is where a law applied outside its domain hides. The law does
        have a domain, and it is worth stating exactly: within ONE phase the
        conditioned node never moves, so the ensemble is two sub-ensembles that
        never mix. Across a chain the prior is re-drawn at each phase, so the
        endpoint is a priori a polynomial in the prior rather than a line -- it
        is the CONVERGED horizon that collapses it back to the final phase's
        draw, as `klf12_conditioning.mixture_prediction` sets out. So the law
        holds here as an observed property of converged readings, not as a
        theorem about the chain, and every row is checked against it.
        """
        with RESPONSE.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(
                arm=row["arm_id"], node=row["node_id"], prior=row["prior"]
            ):
                # 2e-3, not the 1e-2 an earlier revision used. The observed
                # maximum is 6.0e-4, so a 1e-2 bar was seventeen times looser
                # than anything the data could fail -- a check that could not
                # have caught the prior landing on the wrong node.
                self.assertLess(float(row["abs_deviation_from_prediction"]), 2e-3)

    def test_the_law_is_checked_where_it_has_content(self) -> None:
        """Most rows satisfy the law trivially; the count has to be visible.

        Rows at prior 0 or 1 are the anchors the prediction is built from, so
        their deviation is zero by construction, and rows whose two anchors
        coincide are satisfied by any prior at all. Reporting "286 rows checked"
        without this would overstate the check by a factor of four.
        """
        with RESPONSE.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        content = [
            row
            for row in rows
            if 0.0 < float(row["prior"]) < 1.0
            and row["mean_at_prior_0"] != row["mean_at_prior_1"]
        ]
        self.assertGreater(len(content), 20)
        self.assertLess(len(content), len(rows))

    def test_the_conditioned_node_reads_back_at_its_own_prior(self) -> None:
        with RESPONSE.open(newline="", encoding="utf-8") as handle:
            rows = [
                row
                for row in csv.DictReader(handle, delimiter="\t")
                if row["node_id"] == "E_KLF12_HIGH"
            ]
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(arm=row["arm_id"], prior=row["prior"]):
                self.assertAlmostEqual(
                    float(row["node_mean"]), float(row["prior"]), places=2
                )

    def test_what_does_not_move_is_recorded_as_not_moving(self) -> None:
        """Which quantities did not move has to be an entry, not a silence."""
        with RESPONSE.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        stromal = [row for row in rows if row["node_id"] == "OUT_STROMAL_DECIDUALIZED"]
        self.assertTrue(stromal)
        for row in stromal:
            with self.subTest(arm=row["arm_id"], prior=row["prior"]):
                self.assertEqual(row["moves_with_prior"], "false")
        # The integrin node is the interesting non-mover: its rule keeps an
        # `E_SECRETORY_STATE` disjunct, so shutting the LIF gate leaves it on.
        integrin = [row for row in rows if row["node_id"] == "E_ITGAVB3_5"]
        self.assertTrue(integrin)
        for row in integrin:
            with self.subTest(arm=row["arm_id"], prior=row["prior"]):
                self.assertEqual(row["moves_with_prior"], "false")
        self.assertTrue(
            any(row["moves_with_prior"] == "true" for row in rows),
            "a sweep in which nothing moves has not conditioned anything",
        )


if __name__ == "__main__":
    unittest.main()
