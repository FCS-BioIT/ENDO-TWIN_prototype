"""The README dashboard quotes exactly the numbers the committed files produce."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from endotwin.foundation_metrics import OUT, SUITE_RECORDS, compute

README = (ROOT / "README.md").read_text(encoding="utf-8")
DASHBOARD = README.split("<!-- dashboard:start -->", 1)[1].split(
    "<!-- dashboard:end -->", 1
)[0]
METRICS = json.loads(OUT.read_text(encoding="utf-8"))
RESULTS = ROOT / "endotwin/results/endotwin-v0.1.0"


def n(value: int) -> str:
    return f"{value:,}"


class MetricsAreCurrent(unittest.TestCase):
    def test_committed_metrics_equal_a_fresh_computation(self):
        self.assertEqual(METRICS, json.loads(json.dumps(compute())))

    def test_every_listed_analysis_has_its_result_file(self):
        missing = [
            a["result_file"] for a in METRICS["completed_analyses"] if not a["exists"]
        ]
        self.assertEqual(missing, [])


class DashboardMatchesMetrics(unittest.TestCase):
    def assertQuoted(self, phrase: str) -> None:
        self.assertIn(phrase, DASHBOARD)

    def test_literature(self):
        lit = METRICS["literature"]
        tiers = lit["bundle_screen_tiers"]
        for phrase in (
            (
                f"{lit['bundle_screen_2026_10_21_papers']} papers screened "
                f"(tiers A {tiers['A']} / B {tiers['B']} / C {tiers['C']})"
            ),
            (
                f"{lit['registered_references']} registered references, "
                f"all {lit['registered_crossref_resolved']} checked against Crossref"
            ),
            f"{lit['pdf_manifest_full_text_inspected']} read in full text",
            (
                f"a stated {lit['reaudit_2026_09_28_stated_corpus_pdfs']}-PDF corpus, with "
                f"{lit['reaudit_2026_09_28_enumerated_active_pack']} papers listed in it"
            ),
        ):
            self.assertQuoted(phrase)

    def test_evidence(self):
        ev = METRICS["evidence"]
        actions = ev["citation_adjudications_by_action"]
        for phrase in (
            f"{ev['experimental_evidence_rows']} edge-level evidence rows",
            (
                f"{ev['full_text_graded_rows']} rows graded from full text on "
                f"{ev['full_text_graded_edges']} edges"
            ),
            (
                f"{ev['citation_adjudications']} citation adjudications "
                f"({actions['retract']} retracted, {actions['attach']} attached)"
            ),
        ):
            self.assertQuoted(phrase)

    def test_network_and_history(self):
        v060 = METRICS["network_versions"]["adoc-literature-superset-v0.6.0"]
        for phrase in (
            (
                f"{v060['nodes']} nodes, {v060['dependencies']} dependencies "
                f"({v060['activations']} activating, {v060['inhibitions']} inhibitory)"
            ),
            (
                f"{v060['distinct_boolean_functions']} distinct Boolean functions in "
                f"{v060['alias_classes']} alias classes"
            ),
            f"{v060['phenotype_inert_nodes']} phenotype-inert nodes",
            (
                f"{len(METRICS['network_versions'])} model versions; "
                f"{len(METRICS['completed_analyses'])} completed analyses"
            ),
        ):
            self.assertQuoted(phrase)

    def test_experimental_data(self):
        x = METRICS["experimental_data"]
        self.assertQuoted(
            f"{x['secreted_protein_rows']} secreted-protein rows, "
            f"{x['secreted_protein_observed_values']} observed values"
        )
        self.assertQuoted(
            f"scRNA-seq with {n(x['scrna_cells'])} cells from {x['scrna_donors']} donors"
        )

    def test_embryo_adhesion_is_not_presented_as_endotwin_evidence(self):
        # prototype-only endpoint; scope decision in docs/experimental_data.md, section 3.
        self.assertNotRegex(DASHBOARD.lower(), r"adhesion|embryo")

    def test_mainline_and_robustness(self):
        main = METRICS["endotwin_mainline"]
        structure = main["structure"]
        families = main["rule_variant_families"]
        self.assertQuoted(
            f"{structure['nodes']} nodes, {structure['dependencies']} dependencies, "
            f"{structure['distinct_functions']} distinct Boolean functions; "
            f"{len(families)} hypothesis families, "
            f"{sum(len(v) for v in families.values())} rule variants, "
            f"{main['rule_variant_scenarios']} scenarios; "
            f"{main['protocol_conditions']} protocol conditions, "
            f"{main['matched_comparisons']} comparisons"
        )
        rates = json.loads((RESULTS / "rate_sensitivity_summary.json").read_text())
        self.assertQuoted(
            f"{rates['records_converged']} of {rates['records']} steady-state predictions "
            f"unchanged under {rates['samples']} random rate sets"
        )
        confirm = json.loads((RESULTS / "maboss_confirmation_summary.json").read_text())
        self.assertEqual(confirm["unconverged_phases"], 0)
        self.assertQuoted(
            f"all {confirm['records']} simulated phases reach their exact fixed points"
        )

    def test_software_verification(self):
        records = json.loads(SUITE_RECORDS.read_text())
        run = records["endotwin_full_suite"]
        self.assertQuoted(
            f"{n(run['ran'])} automated tests in this repository ({n(run['passed'])} passed, "
            f"{run['failed']} failed, {run['skipped']} skipped)"
        )
        mainline = records["endotwin_mainline_tests"]
        for phrase in (
            (
                f"| This repository, `pixi run test` | {n(run['ran'])} | "
                f"{n(run['passed'])} passed, {run['failed']} failed, {run['skipped']} skipped |"
            ),
            (
                f"| of which mainline, `pixi run endotwin-test` | {mainline['ran']} | "
                f"{mainline['result_line']} |"
            ),
            f"| Prototype at the source commit | {n(records['source_baseline']['ran'])} |",
            (
                f"| Prototype benchmark, {records['historical_benchmark']['date']} | "
                f"{n(records['historical_benchmark']['ran'])} |"
            ),
        ):
            self.assertIn(phrase, README)


class ReadmeHygiene(unittest.TestCase):
    def test_no_unfilled_placeholders(self):
        self.assertNotIn("{{", README)

    def test_relative_links_resolve(self):
        for target in re.findall(r"\]\(([^)]+)\)", README):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = target.split("#", 1)[0]
            self.assertTrue((ROOT / path).exists(), target)

    def test_claims_stay_conservative(self):
        self.assertIn("No calibration and no independent validation", README)
        self.assertIn("Software correctness ≠ biological validation", README)
        self.assertNotRegex(README.lower(), r"\bvalidated (digital )?twin\b")


if __name__ == "__main__":
    unittest.main()
